# ROADMAP — Rendering performance

Ordered by importance. Each item states the measured problem, the change, what it
buys, and how to verify it. Numbers come from `tools/bench.py` on the demo scene at
1920×1080 (GTX 1660 SUPER, 6 GB) unless marked *(estimate)*.

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

## Done (phase 0)

| Change | Effect |
|---|---|
| Shadow array layers allocated on demand instead of eagerly 8 | 838 MiB → 419 MiB at 5120²; SHADOW 61 ms → 0.36 ms |
| No depth attachment / depth blit on post, vol and blur FBOs | 3 × 1080p depth blits + 25 MB VRAM removed |
| `matrices_cache` keyed by light component, not `LightData` value | stopped unbounded per-frame dict growth |
| `release_light()` / `destroy()` + `Engine.exit()` cleanup | shadow layers are reusable; GPU memory freed |
| Frame clock started at window creation | profiler MIN/AVG no longer polluted by a ~1.5 s first frame |

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

## 1. Fit the shadow frustum to the casters, and snap it to texels

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

**Buys.** 5–10× effective texel density at the same memory *(estimate, depends on
scene spread)*. Shadow pixelation drops without spending a byte, and it makes item 5
(CSM) and item 6 (atlas) much easier to land, because both need a fitted frustum.

**Verify.** Visual: shadow edges must get crisper, no shimmering while orbiting.
Perf must stay flat (SHADOW ≤ 0.5 ms).

---

## 2. Hardware depth comparison instead of manual PCF

**Problem.** `lit/fragment.glsl` does a 3×3 loop of `texture(uShadowMapArray, …).r`
with a hand-rolled bias. Nine dependent texture fetches per light per pixel, and the
result is still blocky because each fetch is NEAREST.

**Change.** Set `GL_TEXTURE_COMPARE_MODE = GL_COMPARE_REF_TO_TEXTURE` (and
`GL_TEXTURE_COMPARE_FUNC = GL_LEQUAL`) on the shadow array, declare the sampler as
`sampler2DArrayShadow`, and use `texture(…, vec4(uv, layer, refDepth))`. The compare
+ 2×2 bilinear filter then happens in the sampler for free. Keep the 3×3 loop if you
want extra softness, or drop to 2×2 with a rotated pattern.

**Buys.** Smoother shadow edges at the *same* resolution, and fewer effective fetches
per pixel. This is the cheapest direct fix for pixelation.

**Verify.** Pixel diff is expected to change (that is the point) — compare against the
reference visually at the shadow boundary only; keep SHADOW and LIGHTING flat.

---

## 3. Half-resolution volumetrics with a depth-aware upsample

**Problem.** The volumetric pass is now the single most expensive pass
(**2.08 ms avg, 3.31 ms p95**) — 28 steps × up to 4 spot lights, i.e. up to 84 shadow
array fetches per pixel at full 1080p. Fog has no high-frequency detail, so most of
that resolution is wasted.

**Change.** Render `vol_fb` at half resolution (960×540), then upsample in the blur
composite using the position buffer to reject samples across depth discontinuities
(bilateral / joint-bilateral filter). The existing blur pass is already a good home
for this.

**Buys.** ~4× fewer marching pixels → **~0.6 ms** *(estimate)*, near-identical output
for fog. Watch for haloing where fog overlaps object silhouettes; that is what the
depth-weighted upsample is for.

**Risk.** Low-moderate. Everything downstream of `vol_fb` (blur, composite) must use
the half-res texel size, not the window size.

---

## 4. Clip the volumetric ray to each light's cone

**Problem.** `vol_light/fragment.glsl` marches all 28 steps from the camera for every
spot light, even when the ray never enters that light's cone. Roughly the intersection
test *is* the frame: `spotFactor` is computed at every step and most are zero, but the
loop still runs and the shadow fetch still happens whenever
`projCoords` happens to be in range.

**Change.** Per light, intersect the ray with the cone/sphere (infinite cone test +
sphere at the light's range) and march only `[t0, t1]`, distributing the same 28
steps over that interval. Skip the light entirely when there is no intersection.

**Buys.** Fewer wasted samples *and* better sample distribution for the same step
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

**Buys.** ~40% less G-buffer bandwidth *(estimate)*, which mostly shows up as headroom
on the fill-heavy `DEFERRED` pass and on the passes that read it.

**Risk.** Moderate: every shader that reads `uPosition` / `uNormal` must change.

---

## 9. Tiled light culling

**Problem.** Both the lighting and volumetric shaders loop over all
`uActiveLightCount` lights for every pixel. Capped at 8 by the UBO layout, so this is
about scaling rather than today's 2 ms.

**Change.** Compute a 16×16 tile → light index list per frame (cheap CPU pass over
light bounding spheres projected to screen, or a compute/`GL_ARB_compute_shader` pass
later), upload as an SSBO, and loop only over the tile's lights. Also lets you drop
the `uLights[8]` cap.

**Buys.** Makes 20+ lights viable; cuts both the lit and volumetric passes
proportionally to how many lights each tile actually needs.

**Risk.** Moderate. Do it when the light count becomes a design constraint.

---

## 10. Fold the postprocess copy into the blur composite

**Problem.** `PostScreenQuad` copies `post_fb.color_tex` to the default framebuffer,
and then the vertical blur draw composites on top with `GL_ONE, GL_ONE`. One of those
two full-screen passes is pure copy.

**Change.** Make the vertical blur pass sample `post_fb.color_tex` as well and write
`sceneColor + blur`, dropping the `postprocess` pass to a single draw.

**Buys.** One full-screen 1080p pass (~0.2 ms *(estimate)*). Trivial change, so it is
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

**Buys.** *(estimate)* 1–2 ms on this scene; the payoff grows with object count.

**Risk.** Low, but measure before and after with `BENCH_NO_DEBUG=1` so the profiler
itself isn't in the number.

---

## 12. VRAM watchdog and budget reporting

**Problem.** The failure mode fixed in phase 0 was silent: a 100× slowdown with no
error, and the profiler attributed it to the shadow *pass* while the volumetric pass
was really being starved by the same allocation.

**Change.** Print total render-target footprint at startup (each `FrameBuffer` knows
its attachments; `ShadowFrameBuffer.vram_bytes` exists) with a budget check, and add a
debug flag that dumps it live. Extend the existing 512 MiB shadow warning to the sum
of all targets.

**Buys.** Any future render target (cascades, atlases, G-buffer formats) can't quietly
push the app over the cliff.

**Risk.** None.

---

## Not worth doing (tested)

- **Lowering the shadow resolution.** Its cost was never the resolution: 5120² costs
  0.36 ms now, and 2048² saves ~0.2 ms while changing only 126 pixels of a 1080p
  reference frame (max channel diff 45, i.e. a few texel-level shade differences on
  soft edges). Keep the resolution and fit the frustum instead (item 1).
- **Removing the window's 4× MSAA.** It looks free (only quads reach the default
  framebuffer) but it antialiases the forward-pass light gizmos and debug wireframes,
  and measured 16.07 vs 16.35 ms — inside the noise. Left on.
