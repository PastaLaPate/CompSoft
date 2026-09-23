# Engine optimization audit and next-step plan

## Current measurements

The current profile is substantially better than the earlier sample, but the
remaining work is concentrated in scene rendering:

| Region     |     Min |     Avg |     P95 | Interpretation                                              |
| ---------- | ------: | ------: | ------: | ----------------------------------------------------------- |
| Frame time | 2.45 ms | 2.81 ms | 3.60 ms | Includes work outside the stage sum and timing/swap effects |
| Input      | 0.02 ms | 0.04 ms | 0.10 ms | Not worth prioritizing                                      |
| Deferred   | 0.40 ms | 0.50 ms | 0.62 ms | Highest repeatable scene traversal cost                     |
| Shadow     | 0.50 ms | 0.57 ms | 0.67 ms | Highest render-pass cost                                    |
| Lighting   | 0.09 ms | 0.11 ms | 0.15 ms | Small screen-quad/driver cost                               |
| Forward    | 0.41 ms | 0.50 ms | 0.74 ms | Comparable to deferred and more variable                    |
| Volumetric | 0.08 ms | 0.09 ms | 0.13 ms | Low priority                                                |
| Blur       | 0.05 ms | 0.07 ms | 0.09 ms | Low priority                                                |

The measured stage average is about 1.84 ms, leaving roughly 0.97 ms in
`Random`, listener work, framebuffer transitions, timing, and buffer swap or
driver scheduling. The first task is to make that accounting explicit rather
than optimizing based on the incomplete stage sum.

## Audit of implemented optimizations

### Implemented and useful

- [shader.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/graphics/shader.py)
  now caches uniform locations, avoiding repeated `glGetUniformLocation`.
- [screen_quad.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/graphics/infrastructure/quads/screen_quad.py)
  caches the lighting uniform-block index.
- [engine.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/core/engine.py)
  has stage timing output and throttled logging, which made the current profile
  possible.
- The volumetric shader reduced its sampling workload; this is a GPU-side
  optimization and likely explains part of the lower volumetric time.
- The post-process shader was simplified; this is also a GPU-side optimization.

### Not implemented despite the earlier plan

- [actor.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/actor.py)
  still recursively visits every actor for every pass and filters components
  with `get_components_by_type`.
- [manager.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/input/manager.py)
  still filters and sorts bindings on every event and for every held key.
  This remains low priority because input averages 0.04 ms.
- [camera.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/camera.py)
  caches only the view matrix; projection and inverse view-projection are
  rebuilt.
- [scene.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/scene.py)
  allocates a NumPy UBO buffer and rebuilds every light's dtype data each frame.
- [shadows_frame_buffer.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/graphics/infrastructure/frame_buffers/shadows_frame_buffer.py)
  recomputes every light matrix and redraws every shadow map every frame.
- Screen-quad sampler uniforms and texture/state transitions are still issued
  every pass; this is lower priority than scene traversal.
- The profiler still computes `sum(frame_times)` every frame, does not report
  p95 internally, and does not time `swap_buffers` separately.

## CPU track: prioritized implementation

### 1. Correct the profiler before optimizing

In [engine.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/core/engine.py):

- Maintain a rolling sum instead of calling `sum(frame_times)` every frame.
- Add explicit timings for prerender listeners, framebuffer bind/unbind work,
  and `swap_buffers`.
- Store bounded per-stage samples and report min/average/p95 from the same
  window as frame time.
- Add counters for actor visits, renderable checks, matrix calculations,
  shadow redraws, and draw calls.

This will explain the missing ~0.97 ms and prevent optimizing the wrong region.

### 2. Share scene traversal data between deferred, shadow, and forward

In [actor.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/actor.py)
and [scene.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/scene.py):

- Maintain ordered scene-level lists of deferred renderables, forward
  renderables, and shadow casters, updated on actor/component scene changes.
- Preserve parent-before-child ordering when rebuilding these lists.
- Cache actor world matrices and invalidate descendants when local transforms or
  parenting changes.
- Compute each renderable's complete world matrix once per invalidated update,
  then reuse it for deferred, shadow, and forward passes.
- Keep gizmos and selection behavior separate so the optimization does not
  accidentally make editor-only geometry cast shadows.

This directly targets the 0.50 ms deferred, 0.57 ms shadow, and 0.50 ms
forward averages without changing rendering semantics.

### 3. Add explicit shadow invalidation

In [shadows_frame_buffer.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/graphics/infrastructure/frame_buffers/shadows_frame_buffer.py):

- Cache each light's view-projection matrix based on light type, direction,
  position, angle, and parent transform version.
- Track a dirty bit per shadow layer.
- Invalidate a layer when its light changes or a shadow-casting renderable's
  world transform/topology changes.
- Skip the shadow framebuffer clear and draw calls for clean layers.
- Keep all current culling, depth settings, layer assignment, and shadow-map
  sampling behavior unchanged.

This is the highest-value structural optimization, but must follow the
profiler and scene-list work so stale shadows cannot be introduced.

### 4. Cache camera and light data

In [camera.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/camera.py):

- Cache projection matrices by aspect and projection parameters.
- Cache inverse view-projection for ray casting and volumetric rendering.

In [scene.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/scene.py):

- Reuse one packed `LightData.BLOCK_DTYPE` buffer.
- Upload it only when light membership, light properties, or relevant actor
  transforms change.
- Preserve the current eight-light limit and ordering.

### 5. Defer low-value CPU work

- Input binding indexing is correctness-safe but should be done only after the
  scene work because it can save at most a few hundredths of a millisecond in
  the current profile.
- Sampler-uniform setup and redundant texture/state binding reduction should be
  measured after lighting reaches the top-level bottleneck.

## GPU track: separate follow-up

These changes affect GPU cost or visual quality and should be benchmarked
separately from CPU changes:

- Evaluate shadow-map resolution and number of shadow-casting lights; shadow
  rendering is currently the largest pass.
- Replace repeated fullscreen passes with a combined blur or lower-resolution
  volumetric buffer if quality permits.
- Profile the deferred lighting shader's per-pixel light loop and PCF samples.
- Consider batching/instancing for repeated meshes only after CPU draw-call
  counts are known.

No GPU-track change should be mixed into the CPU benchmark without recording
the quality/resolution trade-off.

## Validation

- Benchmark the same scene and camera path before and after each CPU phase.
- Require improvement in frame p95 or a measured hotspot, not only a lower
  instantaneous minimum.
- Verify static scenes do zero shadow redraws after the first frame, while
  moving a light or caster redraws exactly the affected layers.
- Verify camera movement invalidates camera caches but does not invalidate
  static shadow maps.
- Run existing repository checks (`ruff`, `ty`, and available tests); do not
  add new tooling solely for profiling.
