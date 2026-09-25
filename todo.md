# CompSoft Optimization Summary

## Scope

This document summarizes the frame-time optimization work performed in this
checkout. The main objective was to reduce CPU-side frame overhead while
preserving the existing OpenGL 3.3 renderer, scene behavior, render ordering,
shadow behavior, and public component APIs.

The work also added infrastructure for measuring GPU cost, but it intentionally
did not introduce aggressive visual-quality reductions. Future quality/performance
trade-offs should remain explicit and configurable.

The optimization effort focused on:

- Python-side scene traversal and dispatch
- Transform and camera matrix recomputation
- Mesh normal-matrix calculation
- Light data preparation and uniform-buffer uploads
- Input binding lookup and sorting
- OpenGL GPU timing
- Low-risk shader arithmetic reduction

It did not attempt to:

- Convert the renderer to C++
- Replace the OpenGL 3.3 backend
- Change mesh topology, batching, or instancing
- Add GPU occlusion culling
- Reduce render resolution by default
- Replace the renderer architecture
- Make significant silent quality reductions

## Performance baselines

### Earlier baseline

The initial supplied profile was:

| Stage               | Min (ms) | Average (ms) | P95 (ms) |
| ------------------- | -------: | -----------: | -------: |
| Frame time          |     3.47 |         5.06 |     6.99 |
| Input               |     0.09 |         0.18 |     0.43 |
| Deferred            |     0.57 |         1.07 |     1.78 |
| Shadow              |     0.54 |         0.79 |     1.14 |
| Lighting            |     0.12 |         0.22 |     0.37 |
| Forward             |     0.61 |         1.13 |     1.95 |
| Volumetric lighting |     0.09 |         0.17 |     0.28 |
| Blur                |     0.07 |         0.10 |     0.16 |

The primary targets were deferred, shadow, and forward rendering because they
had the largest average and percentile costs. Input was already comparatively
small and was treated as a secondary optimization target.

### Current reported profile

After the implemented CPU optimizations, the reported profile became:

| Stage               | Min (ms) | Average (ms) | P95 (ms) |
| ------------------- | -------: | -----------: | -------: |
| Frame time          |     2.50 |         2.85 |     3.38 |
| FPS                 |   193.35 |       356.47 |   396.27 |
| Input               |     0.02 |         0.05 |     0.11 |
| Deferred            |     0.40 |         0.48 |     0.56 |
| Shadow              |     0.48 |         0.53 |     0.59 |
| Lighting            |     0.09 |         0.11 |     0.14 |
| Forward             |     0.41 |         0.53 |     0.72 |
| Volumetric lighting |     0.08 |         0.09 |     0.12 |
| Blur                |     0.05 |         0.06 |     0.08 |

Compared with the initial average values:

- Frame time improved from 5.06 ms to 2.85 ms, approximately a 44% reduction.
- Deferred improved from 1.07 ms to 0.48 ms, approximately a 55% reduction.
- Shadow improved from 0.79 ms to 0.53 ms, approximately a 33% reduction.
- Forward improved from 1.13 ms to 0.53 ms, approximately a 53% reduction.
- Input improved from 0.18 ms to 0.05 ms, approximately a 72% reduction.
- Lighting improved from 0.22 ms to 0.11 ms, approximately a 50% reduction.
- Volumetric lighting improved from 0.17 ms to 0.09 ms, approximately a 47% reduction.
- Blur improved from 0.10 ms to 0.06 ms, approximately a 40% reduction.

These values are reported measurements rather than controlled benchmark results.
They should be rechecked using the same scene, window size, driver, camera
motion, and warm-up period before attributing every improvement to one change.

## CPU optimizations

### Camera matrix caching

File:

- [compsoft/scene/camera.py](compsoft/scene/camera.py)

The camera previously rebuilt projection matrices whenever a caller requested
one. It already cached the view matrix, but projection and combined matrices
were still repeatedly created by several paths.

The camera now caches:

- Projection matrix by aspect ratio
- View-projection matrix
- Inverse view-projection matrix

The caches are invalidated when camera properties change:

- Position
- Rotation
- Field of view
- Near clipping plane
- Far clipping plane

The cached inverse view-projection matrix is reused by:

- Ray construction and selection
- Volumetric lighting setup
- Other paths that need the camera-to-world transform

This avoids repeated `glm.perspective`, matrix multiplication, and
`glm.inverse` work in the same frame.

### Shared actor world-matrix traversal

File:

- [compsoft/scene/actor.py](compsoft/scene/actor.py)

Actor local and world transforms are cached and invalidated only when local
transforms or parent relationships change.

The actor render path was updated so that:

- A parent world matrix can be passed into child traversal.
- A child does not need to walk back up the hierarchy to recompute its parent
  matrix.
- Components in one actor reuse the same world matrix.
- Child traversal receives the already-computed parent world matrix.

This preserves parent-before-child ordering while reducing repeated calls to
`get_world_matrix()`.

The implementation still retains the existing transform invalidation behavior
for position, rotation, scale, parenting, and subtree changes.

### Scene-owned renderable lists

Files:

- [compsoft/scene/scene.py](compsoft/scene/scene.py)
- [compsoft/scene/components/component.py](compsoft/scene/components/component.py)

Before this change, deferred and forward rendering recursively walked the actor
tree and checked every renderable component to determine whether it belonged to
the current pass.

The scene now maintains:

- `deferred_renderables`
- `forward_renderables`
- `shadow_casters`

Renderable components register themselves when entering a scene and unregister
when leaving one. When `RENDER_PASS` changes, the component is removed from its
old list and added to the new list.

The results are:

- Deferred rendering directly iterates deferred renderables.
- Forward rendering directly iterates forward renderables.
- Shadow rendering directly iterates shadow casters.
- Components no longer require a per-frame pass comparison during normal scene
  rendering.
- Scene hierarchy traversal is removed from the hot path for the main render
  passes.

The translation gizmo is intentionally excluded from the normal scene render
lists because it already has a dedicated explicit render path in the forward
pass. This avoids rendering it twice.

Registration order is preserved by appending components as they enter the
scene. The existing explicit gizmo rendering order and debug rendering behavior
remain intact.

### Mesh normal-matrix caching

File:

- [compsoft/scene/components/mesh.py](compsoft/scene/components/mesh.py)

Mesh drawing previously calculated the normal matrix by inverting and
transposing the model matrix for every draw:

```python
glm.transpose(glm.inverse(glm.mat3(world_model_matrix)))
```

The mesh now caches the normal matrix associated with its current world matrix.
It recalculates the normal matrix only when the world matrix changes.

This is particularly useful for static scenes because the same mesh can be
drawn over many frames without repeating a matrix inversion.

Transformed bounding-box invalidation remains tied to world-transform changes,
so selection and debug AABB behavior continue to use current transforms.

### Light UBO upload caching

File:

- [compsoft/scene/scene.py](compsoft/scene/scene.py)

The scene previously rebuilt and uploaded the complete light uniform buffer
whenever the render loop requested light data.

The scene now retains the last uploaded logical light data and packed NumPy
buffer. If the current light data is unchanged, the UBO upload is skipped.

This avoids:

- Allocating a new light buffer payload
- Repacking every light
- Calling `glBufferSubData`
- Binding and unbinding the UBO

The existing immediate update behavior for light registration and
unregistration remains in place.

### Shadow matrix cache improvement

File:

- [compsoft/graphics/infrastructure/frame_buffers/shadows_frame_buffer.py](compsoft/graphics/infrastructure/frame_buffers/shadows_frame_buffer.py)

Shadow matrices were previously cached using `LightData` values as dictionary
keys. That required creating light data and hashing vector-heavy values for
every lookup.

The cache now uses the `LightComponent` as the primary key and stores the last
`LightData` snapshot alongside its matrix:

```text
LightComponent -> (LightData snapshot, view-projection matrix)
```

When a light's data changes, the matrix is recalculated. When it does not
change, the cached matrix is reused.

This reduces unnecessary cache-key construction and makes the ownership of a
shadow matrix clearer.

The following behavior was intentionally preserved:

- Shadow texture-layer allocation
- Shadow framebuffer attachment
- Shadow-map resolution
- Front-face culling during shadow rendering
- Existing directional and spotlight matrix calculations

Full shadow-map dirty tracking, where static maps are skipped entirely when no
caster or light changed, remains future work.

### Input binding indexing

File:

- [compsoft/input/manager.py](compsoft/input/manager.py)

Input bindings were previously filtered and sorted on every input event and
every update for held keys.

The manager now maintains buckets keyed by:

```text
(Inputs, TriggerMode)
```

Each bucket is sorted by descending `chord_weight` when a binding is added.

`handle_input_event()` and `update()` now perform direct bucket lookups instead
of:

- Scanning the complete binding list
- Allocating a filtered list
- Sorting that list every time

The following semantics were preserved:

- Modifier matching
- Pressed-modifier snapshots
- Release-time modifier evaluation
- Consumer priority
- Early action consumption
- Pointer drag handling
- Public `bindings` list
- Stable ordering for equal chord weights

This accounts for the reduction in the input timing shown in the newer profile.

### Cached secondary camera use

Files:

- [compsoft/core/engine.py](compsoft/core/engine.py)
- [compsoft/scene/scene.py](compsoft/scene/scene.py)

Ray casting, debug drawing, and volumetric setup now use the camera cache rather
than independently constructing and inverting the projection-view matrix.

This consolidates camera-dependent CPU work and ensures that those paths share
the same cached matrix representation.

## GPU timing infrastructure

Files:

- [compsoft/core/debug.py](compsoft/core/debug.py)
- [compsoft/core/engine.py](compsoft/core/engine.py)

CPU timings alone cannot show whether a rendering stage is CPU-bound, GPU-bound,
or overlapping with other work. An opt-in GPU profiler was added using OpenGL
timer queries.

### Implementation details

The GPU profiler:

- Uses `GL_TIME_ELAPSED`.
- Uses a three-frame query ring.
- Delays query readback to avoid forcing the CPU to wait for the GPU.
- Checks for `GL_ARB_timer_query`.
- Disables itself if the extension is unavailable.
- Cleans up query objects during shutdown.

Instrumented GPU stages:

- Deferred
- Shadow
- Lighting
- Forward
- Volumetric lighting
- Blur

GPU measurements are recorded through the existing profiler and appear with
names such as:

```text
GPU DEFERRED
GPU SHADOW
GPU LIGHTING
GPU FORWARD
GPU VOL LIGHTNING
GPU BLUR
```

This allows CPU and GPU measurements to be compared without introducing a
mandatory synchronization point in normal rendering.

The timer-query path should still be tested inside a real OpenGL context on the
target hardware. Static source validation confirms that the PyOpenGL symbols
are available, but it does not prove that the runtime context exposes the
extension or that the driver reports useful timing values.

## Shader optimization

Files:

- [assets/shaders/lit/fragment.glsl](assets/shaders/lit/fragment.glsl)
- [assets/shaders/vol_light/fragment.glsl](assets/shaders/vol_light/fragment.glsl)

The shader changes were intentionally conservative.

The CPU-side light preparation already normalizes light directions. The shaders
were adjusted to avoid repeating light-direction normalization inside the
inner loops.

### Deferred lighting

The lighting shader now computes a normalized light direction once per active
light iteration and reuses it for:

- Directional-light direction
- Spotlight cone-angle calculation

### Volumetric lighting

The volumetric shader now computes the normalized spotlight direction once per
light before entering the ray-step loop.

Previously, the spotlight direction was normalized for each ray step. Since the
direction is invariant across all samples for a given light, this was redundant
work.

The following were deliberately left unchanged:

- 28-step ray-marching default
- Shadow lookup behavior
- Dithering
- Henyey-Greenstein phase function
- Attenuation formula
- Reinhard tone mapping
- Gamma correction
- Noise behavior

This optimization should preserve the rendered result within normal floating
point differences while reducing repeated shader arithmetic.

## Validation performed

The following validation commands passed after the implemented changes:

```text
uv run --group dev ruff check compsoft
uv run --group dev ty check
git diff --check
python -m compileall -q compsoft
```

The repository currently has no automated test files, so validation was based
on:

- Ruff linting
- Ty type checking
- Python bytecode compilation
- Git whitespace checking
- Source inspection
- Existing runtime frame-time measurements

Shader compilation and GPU timer behavior still require execution inside an
actual OpenGL context. The installed PyOpenGL package exposes the required
timer-query symbols, but a headless source-only validation cannot verify the
driver's runtime extension support.

## Remaining optimization opportunities

### Explicit shadow-map dirty tracking

The current renderer still redraws shadow maps when the render loop requests
them. A future revision should track invalidation from:

- Shadow-light transform changes
- Shadow-light property changes
- Shadow-caster transform changes
- Mesh membership changes
- Shadow-pass changes
- Scene membership changes

Static shadow maps could then be reused without another shadow draw.

### GPU timing and bottleneck classification

The next profiling run should compare CPU and GPU values for the same stages.
This will determine whether further work should target Python orchestration,
shader arithmetic, framebuffer bandwidth, or driver state changes.

### Volumetric lighting

The volumetric shader is a likely GPU hotspot because it can perform:

- 28 ray steps
- Per-step shadow sampling
- Per-step distance and direction calculations
- Work for every active spotlight
- Work for every screen pixel

Possible future improvements, subject to visual validation:

- Configurable step counts
- A lower-cost volumetric shadow mode
- Half-resolution volumetric rendering
- Depth-aware upsampling
- More invariant calculations outside the inner loop

These should not be enabled blindly. Dithering and temporal stability need to
be checked during camera movement.

### Deferred shadow filtering

The lighting shader currently performs 3x3 PCF filtering, which means nine
shadow-map samples per light and fragment.

Possible explicit quality modes:

- Existing 3x3 PCF reference
- Four-tap approximation
- Single-tap low-cost mode

The default should remain the current quality until GPU measurements and visual
comparisons demonstrate that a cheaper mode is acceptable.

### Blur

The blur shader performs nine texture reads per pixel per pass and runs in two
directions. Potential future tests include:

- Smaller separable kernels
- Linear-filter paired samples
- Lower-resolution blur targets

Brightness, halo size, and edge behavior must be compared against the existing
implementation.

### G-buffer bandwidth

The scene framebuffer uses several floating-point attachments:

- Position
- Normal
- Albedo/specular
- Selection

Possible future investigations include:

- Lower precision for selection
- Packed or normalized normal storage
- More compact color formats
- Precision validation for world position
- `glInvalidateFramebuffer` hints after attachments are no longer needed

These changes can affect both quality and correctness, especially for large
world coordinates, ray casting, outlines, and lighting precision.

## Design principles used

The optimization work followed these rules:

1. Measure larger and more variable stages first.
2. Prefer caching over speculative algorithm changes.
3. Invalidate caches explicitly rather than recomputing everything every frame.
4. Preserve existing scene and render ordering.
5. Keep normal runtime overhead low when profiling is disabled.
6. Avoid blocking GPU queries.
7. Avoid broad OpenGL state caches without explicit invalidation rules.
8. Keep quality-affecting approximations configurable.
9. Validate source, types, formatting, and runtime measurements separately.
10. Do not trade significant visual degradation for small benchmark gains.
