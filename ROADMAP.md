# ROADMAP — Rendering performance

Two parts:

- **Part 1 — Squeezing the current renderer.** Items in importance order, all about the
  present 1 directional + 3 spot setup. Items 1–12 are numbered by importance.
- **Part 2 — Scaling to many lights.** What it takes to run hundreds to thousands of
  point/spot/directional lights cheaply, and why the 8-light UBO is the last of several
  walls rather than the first. Phases are numbered **L1–L8** in importance order.

Each item states the measured problem, the change, what it buys, and how to verify it.
Numbers come from `tools/bench.py` on the demo scene at 1920×1080 (GTX 1660 SUPER,
6 GB) unless marked _(estimate)_.

Current state after the first pass: **5.68 ms/frame (176 fps) at 1080p with the
shadow map still at 5120²**, from 74.7 ms/frame (≈17 fps). GPU work is now ~4.4 ms
total, so the frame is CPU/present-bound.

Verification rules that apply to every item:

- Anything claiming to be visually neutral must be proven: `BENCH_FREEZE=1
BENCH_SHOT=/tmp/before.png` on the old build, same command on the new build, then
  diff the PNGs (max per-channel diff must be 0).
- Timing: `uv run python tools/bench.py` (add `BENCH_FRAMES=300` for a tight p95).
  Compare p95, not the average — rare stalls dominate the mean.
- Run `uvx ruff check . && uvx ruff format --check . && uvx ty check .`.

---

# Part 1 — Squeezing the current renderer

## Done (phase 0)

| Change                                                           | Effect                                                      |
| ---------------------------------------------------------------- | ----------------------------------------------------------- |
| Shadow array layers allocated on demand instead of eagerly 8     | 838 MiB → 419 MiB at 5120²; SHADOW 61 ms → 0.36 ms          |
| No depth attachment / depth blit on post, vol and blur FBOs      | 3 × 1080p depth blits + 25 MB VRAM removed                  |
| `matrices_cache` keyed by light component, not `LightData` value | stopped unbounded per-frame dict growth                     |
| `release_light()` / `destroy()` + `Engine.exit()` cleanup        | shadow layers are reusable; GPU memory freed                |
| Frame clock started at window creation                           | profiler MIN/AVG no longer polluted by a ~1.5 s first frame |

Measured root cause, for the record — a 5120² per-layer depth array has a hard
residency cliff on a 6 GB card that is also driving the desktop:

```
5 layers  524 MiB  ->  SHADOW 0.68 ms
6 layers  629 MiB  ->  SHADOW 0.65 ms
7 layers  734 MiB  ->  SHADOW 62.0 ms   <- spill to PCIe
8 layers  838 MiB  ->  SHADOW 61.4 ms
```

Standing constraint: **keep total render-target VRAM well under ~600 MiB.** Above it
the shadow pass streams ~420 MB/frame over PCIe and every pass that touches the
array collapses by ~100×. `ShadowFrameBuffer` now warns past 512 MiB; extend that
watchdog to all render targets (item 12).

---

## 1. Fit the shadow frustum to the casters, and snap it to texels (Done)

**Problem.** `_compute_vp_matrix()` hardcodes `glm.ortho(-10, 10, -10, 10, 0.1, 50.0)`.
The shadow map covers a fixed 20×20 world box no matter what is in it. The sandbag
pile is ~1 unit wide, so ~95% of the 26 M texels are spent on empty ground. This —
not resolution — is why shadows look pixelated.

**Change.**

- Compute the light-space AABB of the casters that actually intersect the light
  (`scene.shadow_casters`, already available; use each component's transformed AABB).
- Build a square ortho box from those bounds, padded, with a sane minimum size.
- Snap the box centre to whole texels (`extent / resolution`) so shadow edges don't
  crawl when the camera or light moves.
- Do it per light type: directional fits the whole caster set, spot fits its cone.

**Buys.** 5–10× effective texel density at the same memory _(estimate, depends on
scene spread)_. Shadow pixelation drops without spending a byte, and it makes item 5
(CSM) and item 6 (atlas) much easier to land, because both need a fitted frustum.

**Verify.** Visual: shadow edges must get crisper, no shimmering while orbiting.
Perf must stay flat (SHADOW ≤ 0.5 ms).

---

## 2. Hardware depth comparison instead of manual PCF (Done)

**Problem.** `lit/fragment.glsl` does a 3×3 loop of `texture(uShadowMapArray, …).r`
with a hand-rolled bias. Nine dependent texture fetches per light per pixel, and the
result is still blocky because each fetch is NEAREST.

**Change.** Set `GL_TEXTURE_COMPARE_MODE = GL_COMPARE_REF_TO_TEXTURE` (and
`GL_TEXTURE_COMPARE_FUNC = GL_LEQUAL`) on the shadow array, declare the sampler as
`sampler2DArrayShadow`, and use `texture(…, vec4(uv, layer, refDepth))`. The compare

- 2×2 bilinear filter then happens in the sampler for free. Keep the 3×3 loop if you
  want extra softness, or drop to 2×2 with a rotated pattern.

**Buys.** Smoother shadow edges at the _same_ resolution, and fewer effective fetches
per pixel. This is the cheapest direct fix for pixelation.

**Verify.** Pixel diff is expected to change (that is the point) — compare against the
reference visually at the shadow boundary only; keep SHADOW and LIGHTING flat.

**Landed.** The compare state lives on a **sampler object** bound to the lighting
pass' unit rather than on the shadow array itself: the volumetric and debug-depth
passes read the same texture's raw depth, and compare+`GL_LINEAR` on the texture
object made the volumetric pass **2.09 → 2.52 ms** (bilinear compare fetches at 84
per pixel). With the state per unit instead, the fog pass is untouched and only the
lighting pass pays for filtering. Kernel is now four rotated-grid taps at a ~1-texel
radius; each tap is a 2×2 filtered compare, so it still averages sixteen comparisons
over the old 3×3 footprint. `GL_LEQUAL` means a tap passes when
`refDepth = projCoords.z - bias` is `<=` the stored depth (lit).

Measured (`BENCH_FRAMES=300`, two runs each, 1920×1080, shadow map 5120²):

| Pass     | Before (min/avg/p95) | After (min/avg/p95) |
| -------- | -------------------- | ------------------- |
| LIGHTING | 0.28 / 0.31 / 0.41   | 0.25 / 0.27 / 0.30  |
| VOL      | 1.52 / 1.59 / 1.76   | 1.53 / 1.58 / 1.72  |
| SHADOW   | 0.13 / 0.13 / 0.15   | 0.13 / 0.13 / 0.15  |

Frozen-frame diff (both runs verified bit-identical first): 72 pixels changed at
5120² (max 9/255) and 278 at 1024² (max 18/255), every changed pixel within 5 px of a
shadow edge — no shading change in flat regions, i.e. no new acne. The visual gain is
modest at 5120² because item 1 already made texels sub-pixel; it is the cheap
prerequisite for the coarser maps item 5/6 will use.

---

## 3. Half-resolution volumetrics with a depth-aware upsample (Done)

**Problem.** The volumetric pass is now the single most expensive pass
(**2.08 ms avg, 3.31 ms p95**) — 28 steps × up to 4 spot lights, i.e. up to 84 shadow
array fetches per pixel at full 1080p. Fog has no high-frequency detail, so most of
that resolution is wasted.

**Change.** Render `vol_fb` at half resolution (960×540), then upsample in the blur
composite using the position buffer to reject samples across depth discontinuities
(bilateral / joint-bilateral filter). The existing blur pass is already a good home
for this.

**Buys.** ~4× fewer marching pixels → **~0.6 ms** _(estimate)_, near-identical output
for fog. Watch for haloing where fog overlaps object silhouettes; that is what the
depth-weighted upsample is for.

**Risk.** Low-moderate. Everything downstream of `vol_fb` (blur, composite) must use
the half-res texel size, not the window size.

**Landed.** `FrameBuffer` takes a `scale`, so `vol_fb` and the horizontal blur target
allocate at half size and follow window resizes through the same listener. The
vertical blur moved into a new `vol_composite` pass that runs at full resolution and
weights every tap by |scene distance at the tap − scene distance at the pixel|
(linear falloff squared, tolerance `max(0.05, 2% of distance)`), reading the full-res
position buffer as guidance — that is the joint-bilateral upsample, and it also
rejects fog bleeding across silhouettes in Y. Sky reads 1e6 so it never rejects
against itself. Bilinear in X comes free: the fog texture is `GL_LINEAR`. Buffers are
3 × 4.1 MiB at 1080p instead of 2 × 16.6 MiB, and one full-screen pass went away
(the old chain was vol + 2 blurs + composite).

Measured (`BENCH_FRAMES=300`, two runs each, 1920×992 — see the harness note below):

| Pass                        | Before (min/avg/p95) | After (min/avg/p95) |
| --------------------------- | -------------------- | ------------------- |
| VOL LIGHTNING               | 1.45 / 1.54 / 1.75   | 0.38 / 0.39 / 0.43  |
| BLUR (horizontal, half res) | 0.26 / 0.27 / 0.30   | 0.04 / 0.04 / 0.05  |
| VOL COMPOSITE (new)         | —                    | 0.13 / 0.13 / 0.15  |
| loop                        | 4.90 ms (204 fps)    | 3.64 ms (275 fps)   |

The volumetric chain as a whole: **1.81 → 0.56 ms**, 3.2× cheaper, ~26% off the frame.

Frozen-frame diff against the full-resolution chain (both runs bit-identical first):
max 17/255, mean 1.06, 98% of pixels within 2 levels, no halo band along silhouettes
(per-block mean |diff| stays between 0.0 and 2.1; only 4 px brighter and 21 darker by
more than 4). The residual is the expected half-res sampling difference in fog
distribution, not lost or doubled light.

**Harness note.** `BENCH_W/BENCH_H` is a *request*: this desktop gives a 1920×992
window for a 1920×1080 ask. The bench used to keep rendering and reading 1080 rows
anyway, so every PNG had ~88 rows of stale VRAM at the top and the render targets were
a size nobody displayed. It now prints the achieved size and uses it for the targets,
the viewport and the readback. Item 2's diff is unaffected (the stale band was
identical in both captures).

---

## 4. Clip the volumetric ray to each light's cone

**Problem.** `vol_light/fragment.glsl` marches all 28 steps from the camera for every
spot light, even when the ray never enters that light's cone. Roughly the intersection
test _is_ the frame: `spotFactor` is computed at every step and most are zero, but the
loop still runs and the shadow fetch still happens whenever
`projCoords` happens to be in range.

**Change.** Per light, intersect the ray with the cone/sphere (infinite cone test +
sphere at the light's range) and march only `[t0, t1]`, distributing the same 28
steps over that interval. Skip the light entirely when there is no intersection.

**Buys.** Fewer wasted samples _and_ better sample distribution for the same step
count, so image quality goes **up** while cost goes down. Pairs naturally with item 3
(half-res + clipped interval).

**Risk.** Low. Analytic cone math must match the shader's cutoff convention
(`inner_cutoff` / `outer_cutoff` are cosines).

---

## 5. Cascaded shadow maps for the directional light

**Problem.** One map for the whole scene means either blocky near-field shadows or a
map that has to be enormous. `CASCADES_N = 4` is already declared in
`shadows_frame_buffer.py` and unused (`# * CASCADES_N + cascade` in `get_light_layer`).

**Change.** Split the camera frustum into 4 depth ranges (practical split or log
split), fit and texel-snap one map per cascade (items 1), and select the cascade per
fragment in the lighting shader from view depth, with a cross-fade at the boundaries.
Layer index = `light_layer * CASCADES_N + cascade`; the shader already receives a
`uLightSpaceMatrices[8]` array, which needs to become per-cascade.

**Buys.** Much higher shadow detail where the camera is looking, at **lower** total
memory (4 × 2048² = 64 MiB vs 419 MiB today). This is the structural answer to the
"high resolution to avoid pixelation" problem.

**Risk.** Moderate: cascade fitting, blend bands, and the light-space array layout all
change together. Land items 1 and 2 first — CSM without texel snapping shimmers badly.

---

## 6. Per-light shadow atlas instead of equal-sized array layers

**Problem.** Every light gets the same 5120² layer. Three of the four lights in the
demo are narrow cones that need a fraction of those texels, yet all four pay full
price (419 MiB, and 8 lights would be back over the VRAM cliff).

**Change.** One 4096² atlas (or 2 × 2048²), with each light assigned a tile sized to
its cone/importance: e.g. 2048² for the sun, 1024² for a 30° spot. Pass a UV rect +
depth range per light instead of a layer index; map to tile coordinates in
`ShadowCalculation` and in the volumetric pass.

**Buys.** Same visual quality at ~1/6 the memory, more lights before the cliff, and
one texture binding instead of `glFramebufferTextureLayer` per light.

**Risk.** Moderate. Needs care with tile edge bleeding (add a 1-texel inset) and with
clipping in the shader when a sample falls outside the light's tile.

---

## 7. Cache shadow maps for lights that did not move

**Problem.** Every shadow-casting layer is re-rendered every frame, even when the
light and all its casters are static.

**Change.** Per layer, store a fingerprint (light VP hash + a hash of the casters'
world matrices inside that light's frustum) and skip `render_light` when unchanged.
Needs the "contents were dropped" caveat in `_allocate_layers` to become an explicit
invalidation, since growth currently discards layers.

**Buys.** Static scenes and editor sessions drop to near-zero shadow cost. It does
**not** help the demo, whose lights orbit every frame — hence it is below the
structural items.

**Risk.** Low, but a stale-map bug is subtle. Add a debug flag to force a full
re-render.

---

## 8. Depth prepass and a packed G-buffer

**Problem.** `DEFERRED` costs **1.16 ms** and writes 26 B/px + depth: RGBA16F position,
RGBA16F normal, RGBA16F albedo, R16F selection. Every full-screen pass then reads
those back — the position buffer in particular is the volumetric pass' main input.

**Change.** Two steps, in order of payoff:

1. Reconstruct world position from the depth buffer instead of storing RGBA16F
   (saves 8 B/px; needs the inverse view-projection as a uniform — already computed in
   `engine.py` for the volumetric pass).
2. Pack normals to 2 channels (octahedral) instead of 3 half-floats (saves ~4 B/px).
3. Optional: a depth-only prepass before the deferred pass so hidden fragments never
   run the gbuffer shader (helps here, since the 100×100 ground plane has heavy
   overdraw).

**Buys.** ~40% less G-buffer bandwidth _(estimate)_, which mostly shows up as headroom
on the fill-heavy `DEFERRED` pass and on the passes that read it.

**Risk.** Moderate: every shader that reads `uPosition` / `uNormal` must change.

---

## 9. Tiled light culling

**Superseded by Part 2, L2** (clustered light assignment), which is the same idea done
properly in 3D and with the culling shared by the lighting and volumetric passes. Kept
here only as a note: do not implement 2D-only tiles first, the depth-range
over-inclusion makes it wasted work.

---

## 10. Fold the postprocess copy into the blur composite

**Problem.** `PostScreenQuad` copies `post_fb.color_tex` to the default framebuffer,
and then the vertical blur draw composites on top with `GL_ONE, GL_ONE`. One of those
two full-screen passes is pure copy.

**Change.** Make the vertical blur pass sample `post_fb.color_tex` as well and write
`sceneColor + blur`, dropping the `postprocess` pass to a single draw.

**Buys.** One full-screen 1080p pass (~0.2 ms _(estimate)_). Trivial change, so it is
worth doing opportunistically, but it is not worth its own commit.

---

## 11. Cut per-draw CPU overhead

**Problem.** The frame is now CPU/present-bound: 4.4 ms of GPU work but 5.68 ms
wall-clock. Per mesh per pass the engine calls `material.use()` → `glUseProgram`,
`value_ptr` + `glUniformMatrix4fv` for MVP/model/normal matrix, and a texture bind pair.

**Change.**

- Move camera-derived matrices (view, projection, inverse view-projection) into a
  per-frame uniform block, uploaded once.
- Batch draws by material/shader and sort by VAO to cut state changes.
- Cache `value_ptr` results per matrix instance rather than re-deriving them for
  `gbuffer` and `depth` in the same frame.

**Buys.** _(estimate)_ 1–2 ms on this scene; the payoff grows with object count.

**Risk.** Low, but measure before and after with `BENCH_NO_DEBUG=1` so the profiler
itself isn't in the number.

---

## 12. VRAM watchdog and budget reporting

**Problem.** The failure mode fixed in phase 0 was silent: a 100× slowdown with no
error, and the profiler attributed it to the shadow _pass_ while the volumetric pass
was really being starved by the same allocation.

**Change.** Print total render-target footprint at startup (each `FrameBuffer` knows
its attachments; `ShadowFrameBuffer.vram_bytes` exists) with a budget check, and add a
debug flag that dumps it live. Extend the existing 512 MiB shadow warning to the sum
of all targets.

**Buys.** Any future render target (cascades, atlases, G-buffer formats) can't quietly
push the app over the cliff.

**Risk.** None.

---

# Part 2 — Scaling to many lights (point, spot, directional)

Target: hundreds to thousands of lights on this GPU, with roughly constant cost per
frame. The `uLights[8]` UBO is the _visible_ cap, but it is the cheapest wall to
remove and not the first one that hurts. In the order they actually hit:

| Wall                                                                      | Where                                          | Gives out at                                                   |
| ------------------------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------- |
| Per-pixel loop pays full price for every light                            | `lit/fragment.glsl`, `vol_light/fragment.glsl` | ~16–32 lights                                                  |
| One shadow layer per light (5120² × 4 B = **105 MiB each**)               | `ShadowFrameBuffer.get_light_layer`            | 4–5 shadowed lights before the VRAM cliff                      |
| Volumetric marching: 28 steps × every spot light                          | `vol_light/fragment.glsl`                      | 2–3 spots (already 2.08 ms)                                    |
| `uLights[8]` / `uActiveLightCount`                                        | `LightData.BLOCK_DTYPE`, both shaders          | 8 — extra lights are silently dropped by `min(len(lights), 8)` |
| `uLightSpaceMatrices[8]` + one `set_uniform_matrix` per light per frame   | `screen_quad.py`                               | 8                                                              |
| `upload_light_ubo()`: `np.zeros` + per-light record fill, twice per frame | `scene.py`                                     | ~200–1000 lights (ms of Python)                                |

So: lifting the array size alone buys maybe 16–32 lights before the volumetric pass
collapses. The order below is designed so each phase removes the wall the previous
one exposes.

Order of importance: **L1** (unblock data path) → **L2** (cluster culling: this is the
real enabler) → **L3** (shadow budget) → **L4** (froxel volumetrics) → **L5** (point
lights, cheap once L2 exists) → **L6** (baked lighting for thousands) → **L7**
(housekeeping, needed before any of the scaling numbers are honest) → **L8**
(validation).

---

## L1. Get light data out of the UBO and kill the 8-light cap

**Problem.** `LightData.LIGHT_DTYPE` is 80 B per light in a `std140` block sized for 8,
with the count passed as a UBO member. Two shaders declare `LightData uLights[8]`, and
`LitScreenQuad.upload_light_space_matrices()` does one `glUniformMatrix4fv` per light
per frame.

**Change.**

1. Bump the context to 4.3 core (or 4.6) in `window.py` — the 1660 SUPER is a 4.6 part
   and PyOpenGL exposes everything. This unlocks SSBOs, compute (L2 GPU path), image
   store (L4) and `glCopyImageSubData` (shadow caching). If 3.3 must stay for
   compatibility, use a **texture buffer object** (`samplerBuffer` + `texelFetch`)
   instead — it is core in 3.1 and holds 65 536 lights.
2. Store lights in a plain SSBO/TBO instead of the UBO, with the count in the same
   buffer (or a 1-int uniform — cheap either way).
3. Pack the struct, 80 B → 32 B. One possible layout:

```
struct GpuLight {        // 32 bytes
  vec3  position;        // 12   world space
  float radius;          //  4   influence radius (culling + attenuation cutoff)
  vec3  color;           // 12   HDR linear
  float intensity;       //  4
  uvec2 packedDir;       //  8   octahedral, 2 x int16
  uint  typeShadow;      //  4   type:2b | shadow tile:10b | flags
  uint  cutoffs;         //  4   inner/outer as 2 x uint16 (normalised)
};
```

1000 lights = 32 KB. Upload is one `glBufferSubData`. 4. Move `uLightSpaceMatrices` into a buffer as well (or into the per-light struct as
four `mat4` in a parallel array indexed by shadow tile) so per-light uniform uploads
disappear entirely. 5. Shader loop becomes `GpuLight l = lightAt(i);` with `lightAt` doing a
`texelFetch`/`lightData[i]` — no per-light uniform state.

**Buys.** Removes the hard cap and the per-light CPU submission cost. Prerequisite for
everything else.

**Risk.** Low. Straight port of the existing math; keep the current lighting result
bit-comparable before moving on (freeze-frame diff).

---

## L2. Clustered light assignment (Forward+) — the actual mechanism

**Problem.** `lit/fragment.glsl` loops over all active lights for every pixel. Cost is
`pixels × lightCount`, so "many lights" is impossible regardless of how cheap each
light is.

**Change.** Build a 3D cluster grid over the view frustum each frame, and store the list
of lights intersecting each cluster. The deferred lighting shader then loops only over
its own cluster's lights.

- Grid: **16×16 tiles × 24 depth slices**, with exponential (log) z slicing so near
  clusters stay thin. 1080p → 120×68 pixels per tile. Note this is 3D, not 2D: with
  near 0.1 / far 50 the 2D tile version would pull distant lights into near tiles.
- Culling test: light bounding sphere (radius from L1) vs cluster AABB. The directional
  light is stored once in a "global lights" list instead of in clusters.
- Two implementations, in this order:
  1. **CPU (works on GL 3.3 today).** Vectorised numpy: project each light's sphere to a
     tile range + z-slice range, then scatter into per-cluster lists. 3456 clusters ×
     500 lights is a few numpy passes, _(estimate)_ 1–3 ms — acceptable while the GPU
     path doesn't exist, and it is measurable immediately.
  2. **GPU compute (after L1's context bump).** Per-cluster dispatch: test lights
     against the cluster AABB, `atomicAdd` into a count buffer, second pass writes
     indices into an SSBO at the reserved offsets. _(estimate)_ <0.2 ms for 1000 lights.
     This is the version to land long-term; it also frees the CPU for shadow policy.
- Upload cluster offsets/counts and the index list as one buffer; the shader computes
  its cluster index from `gl_FragCoord` and view-space depth (no extra pass needed).

**Buys.** Per-pixel cost becomes proportional to _overlapping_ lights (typically 2–6 in
a dense scene) instead of total lights. This is what makes hundreds of lights cheap.
The same cluster lists are reused by the volumetric pass in L4 — one culling structure,
two consumers.

**Risk.** Moderate. Tune: tile size (16×16 vs 32×32), z-slice count, and a max-lights-
per-cluster overflow guard (drop the least important light, and log it) so a pathological
cluster can't blow up the fragment loop.

---

## L3. Make shadows a budgeted resource, not a per-light allocation

**Problem.** `get_light_layer()` hands every shadow-casting light a full-size layer.
At 5120² that is 105 MiB per light; four lights already sit at 419 MiB, and the VRAM
cliff is around 600–700 MiB. Many shadowed lights is therefore impossible by
construction, no matter how the light list is stored.

**Change.**

1. Shadow **atlas** with per-light tiles (Part 1, item 6), total VRAM fixed by design —
   e.g. 4096² = 67 MiB for the whole renderer.
2. A **budget policy** in `Scene`/`ShadowFrameBuffer`: at most _K_ shadowed lights
   (start with 8–16). Select per frame by importance = screen-space light size ×
   intensity × a `shadow_priority` field; the sun/directional light is always in. Give
   tiles **hysteresis** (keep the same tile across frames unless the ranking changes by
   a margin) so shadows don't pop or thrash.
3. Explicit `casts_shadows: bool` on `LightComponent` instead of "every light gets a
   layer". Lights that lose a tile this frame are simply unshadowed.
4. Static lights keep their tile content (Part 1, item 7) — a 16-tile atlas then serves
   16 static lights for free plus a few dynamic ones.
5. Cache the shadow matrix per light anyway (already done), and index the atlas per
   light with the tile id packed into `GpuLight.typeShadow` (L1), so the shader needs no
   per-light uniform.

**Buys.** Hundreds of lights with a **constant, known** shadow VRAM cost and a flat
per-frame shadow cost. This is the phase that makes the light count irrelevant to
memory.

**Risk.** Moderate: tile packing, tile-edge insets, and hysteresis tuning. Do it after
L1/L2 — the packing depends on per-light data being in a buffer.

---

## L4. Froxel volumetrics instead of per-pixel marching

**Problem.** `vol_light/fragment.glsl` marches `NUM_STEPS = 28` per _spot light_ per
pixel: at 4 lights that is up to 84 shadow fetches/px, and it is already 2.08 ms avg /
3.31 ms p95. With 50 spots it is unshippable, and the cone-clip trick (Part 1, item 4)
only helps with sparse lights.

**Change.** Compute volumetric scattering in a **3D froxel volume** instead:

1. Volume: 160×90×64 (or the cluster grid) of RGBA16F = 7.4 MB; one 3D texture.
2. **Injection:** for each froxel, loop over its cluster's lights (reuse L2's lists),
   evaluate the phase function + shadow visibility, accumulate in-scattering. This is
   the only per-light term, and it is per _froxel_, not per pixel.
3. **Blur:** separable 3D blur (or a few 3D Kawase-style passes) to remove the low
   froxel resolution.
4. **Composite:** one full-res pass that samples the volume by view depth and adds it to
   the scene color — replaces the current vol + blur + composite chain.

Implementation routes: compute + `imageStore` on 4.3+ (clean); on 3.3, render one quad
per z-slice into the 3D texture layer via an FBO per layer, or layered rendering with a
geometry shader.

**Buys.** Volumetric cost becomes ~independent of light count and of screen resolution:
_(estimate)_ ~1 ms total for 50 spots, vs 2.08 ms today for four. It also decouples
volumetrics from shadow-map resolution, which is what bit you in phase 0.

**Risk.** Moderate-high (new subsystem). Land Part 1 item 4 first to get an interim win
without a rewrite.

---

## L5. Point lights

**Problem.** `LightType.POINT` is commented out (`# POINT = 0`) and the class is stubbed
in `light.py`, so only directional and spot exist.

**Change.** Small once L1/L2 are in place:

- Re-add `POINT = 0`; `PointLight` with `position`, `color`, `intensity`, `radius`,
  `casts_shadows`.
- Deferred shader: inverse-square with a smooth radius cutoff
  (`attenuation = saturate(1 - (d/radius)^4)^2 / (d^2 + eps)`) — no cone test, so it is
  _cheaper_ per light than a spot.
- Clusters cull it by sphere, exactly like a spot.
- Shadows: **not** per point light by default. A cube map is 6 renders and a
  dual-paraboloid 2; only hero lights (L3's budget) get one.

**Buys.** A point light then costs about the same as a spot in the deferred pass, and
nothing extra in the culling structure.

**Risk.** Low.

---

## L6. Baked / probe lighting for mass static lights

**Problem.** Even with clusters, thousands of lights cost _something_ per frame. Most
scene lighting is static, and evaluating it every frame is pure waste.

**Change**, in increasing order of effort:

1. **Irradiance volume** — a 3D grid of spherical-harmonic probes baked offline/on
   demand, sampled in the deferred shader by world position. One texture fetch replaces
   any number of static lights. _(estimate)_ 1000+ static lights, ~0 extra ms.
2. **Lightmaps** — per-mesh UV2 bakes. Best quality for static geometry, needs a UV
   unwrap and a bake tool.
3. **DDGI** — probe volumes with ray-traced updates for dynamic GI feel; heavier and a
   bigger project.

Then classify lights: `static` lights go into the bake, `dynamic` lights (the few that
move) go through L1/L2 at runtime.

**Buys.** The only route that actually reaches "thousands of lights for free". Pairs
naturally with L3's budget: bake everything static, spend the shadow tiles on the
handful of lights that move.

**Risk.** High effort, low risk to the runtime. Do it when scene content demands it.

---

## L7. Light data-path housekeeping (required before you trust any scaling number)

**Problem.** The Python side is fine for 8 lights and dies long before the GPU does:

- `Scene.upload_light_ubo()` allocates `np.zeros(1, BLOCK_DTYPE)` and writes each light's
  record field by field — every frame, and it is called **twice** per frame (once in the
  render loop, once from `register_light`).
- `Scene.get_lights()` allocates a fresh list of fresh `LightData` objects on every call.
- `LightData.to_dtype()` allocates a record array per light.
- `LitScreenQuad.upload_light_space_matrices()` does one uniform call per light per frame.

**Change.**

- One preallocated `(N, ...)` numpy array sized to a capacity that grows by doubling;
  vectorised fill; a `lights_version` counter bumped on any light change; upload only
  when the version changed.
- Cache the packed buffer instead of `LightData` objects: `get_lights()` returns a view
  into it (or is dropped from the hot path entirely).
- Move matrices into a buffer (L1) so there is no per-light uniform traffic.
- Keep the CPU cluster build (L2 path 1) working in the same preallocated buffers.

**Buys.** With 500 lights, this is the difference between a ~1 ms and a ~10 ms frame
before the GPU has done anything.

**Risk.** Low, but do it before L8 so the sweep measures the renderer, not numpy.

---

## L8. Validation

1. Add a stress scene (`compsoft/scenes/stress_lights.py`, or a `BENCH_LIGHTS` knob in
   `tools/bench.py`) that spawns N lights in a grid over the demo scene — mixing
   directional, spot and point — plus a shadowed-count knob.
2. Sweep and record: ms/frame vs N = 8, 32, 128, 512; ms/frame vs shadowed count =
   0, 4, 8, 16; VRAM footprint from the L1/Part-1-item-12 watchdog.
3. Gate targets _(estimates, to be replaced with measured values)_:
   - 500 lights, no shadows: **≤ 1.5 ms added** over the current no-light baseline.
   - 500 lights, 8 shadowed: shadow VRAM constant regardless of N.
   - Volumetrics flat in light count after L4.

---

## Part 2 — expected shape after L1 + L2 + L3 + L4 (+L7)

| Lights | Shadowed          | Added cost _(estimate)_ | Notes                                             |
| ------ | ----------------- | ----------------------- | ------------------------------------------------- |
| 8      | 4                 | 0 — today               | baseline                                          |
| 32     | 8                 | ~+0.3 ms                | clusters already help; shadows still the limit    |
| 128    | 8                 | ~+0.5 ms                | CPU culling fine; GPU path preferable beyond here |
| 512    | 8–16              | ~+0.8–1.5 ms            | needs GPU cluster build and the L7 data path      |
| 1000+  | 0 (all baked, L6) | ~0                      | irradiance volume replaces them at runtime        |

---

## Not worth doing (tested / considered and rejected)

- **Lowering the shadow resolution.** Its cost was never the resolution: 5120² costs
  0.36 ms now, and 2048² saves ~0.2 ms while changing only 126 pixels of a 1080p
  reference frame (max channel diff 45, i.e. a few texel-level shade differences on
  soft edges). Keep the resolution and fit the frustum instead (Part 1, item 1).
- **Removing the window's 4× MSAA.** It looks free (only quads reach the default
  framebuffer) but it antialiases the forward-pass light gizmos and debug wireframes,
  and measured 16.07 vs 16.35 ms — inside the noise. Left on.
- **Just raising `uLights[8]` to 64.** Removes the error but not the cost: the shader
  still evaluates every light per pixel, `uLightSpaceMatrices` still needs 64 per-light
  uniform uploads, and the volumetric pass dies at ~3 spots regardless.
- **Forward light volumes (stencil per light).** Good for a few huge lights, bad for
  many small ones — a small light volume still shades its whole screen-space footprint
  with overdraw, and you lose the G-buffer reuse. Use clusters instead; light volumes
  can still complement them for one or two screen-filling lights.
- **A shadow cube per point light.** Six renders per light per frame; only viable for
  1–2 hero lights, and even then dual-paraboloid (2 renders) is usually enough.
