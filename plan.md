# Engine CPU-overhead optimization plan

## Goal, based on the supplied timings

The measured CPU-side render work is already very small: the two samples total
2.36 ms and 1.31 ms, while the frame-time deque reports 3.02 ms. Input is only
0.03-0.05 ms and should not be optimized first. The priority order is therefore:

1. Shadow pass: 0.80/0.32 ms (largest variable cost).
2. Deferred pass: 0.75/0.38 ms (second-largest variable cost).
3. Forward pass: 0.34/0.26 ms.
4. Lighting: 0.20/0.11 ms.
5. Volumetric and blur: 0.11/0.09 and 0.09/0.07 ms.

The first pass should target shadow/deferred scene traversal and repeated
transform/render dispatch. It should not spend implementation complexity on
input dispatch or micro-optimizing 0.07-0.11 ms post-processing calls until
the larger passes are measured and improved.

The discrepancy between the reported 3.02 ms frame delta and the measured
1.31-2.36 ms render total must also be made explicit: `window.dt` is wall-clock
time between frame starts and includes buffer swap/driver scheduling, while
the debug total starts after `window.clear()` and excludes the swap. These
numbers are not interchangeable.

## Baseline and measurement

1. Add an opt-in `Engine` profiling mode rather than printing timings every frame.
2. Measure these exact regions separately:
   - `InputManager.begin_frame/update`
   - prerender listeners
   - deferred actor traversal/draw dispatch
   - shadow rendering, split into `LightComponent.get_data`, matrix setup, and shadow actor traversal
   - lighting/post/volumetric/blur orchestration
   - forward actor traversal/debug/gizmo work
3. Record counts for root actors, total actors, renderable components, active lights, shadow lights, and draw calls.
4. Fix the existing timing metric: replace `sum(frame_times)` on every frame with a rolling sum, and do not calculate debug-only timings unless profiling is enabled.

## Concrete changes

### 1. Measure the actual target before changing it

In [engine.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/core/engine.py):

- Keep the existing stage timings, but add separate timings for Python traversal
  and the OpenGL draw calls inside deferred and shadow passes.
- Count actor visits, renderable-component checks, matrix computations, shadow
  lights, and draw calls per pass.
- Record min/average/p95 over a window rather than only the instantaneous
  sample, because the supplied deferred/shadow values vary by roughly 2x.
- Add a `swap_buffers` timing boundary so wall-clock frame time can be reconciled
  with the debug total.

### 2. Shadow pass: optimize the dominant variable cost first

In [shadows_frame_buffer.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/graphics/infrastructure/frame_buffers/shadows_frame_buffer.py)
and [scene.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/scene.py):

- [x] Cache each light's view-projection matrix until its position, direction,
      type, angle, or relevant parent transform changes.
- [] Add explicit shadow-caster dirty tracking. A static scene should not redraw
  every shadow layer every frame; moving a caster or shadow light invalidates the
  affected maps.
- [] When a map must be redrawn, traverse a prebuilt list of shadow-casting
  renderables instead of recursively walking every actor and checking every
  component.
- [] Keep the current culling, framebuffer layer, resolution, and visual behavior.
- [] Do not add speculative frustum/visibility culling in this pass; measure first,
  because incorrect culling would trade CPU time for missing shadows.

### 3. Deferred pass: remove repeated scene traversal and matrix work

In [actor.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/actor.py):

- [] Maintain cached renderable lists for `DEFERRED` and `FORWARD`; shadow uses the
  deferred list.
- [x] Cache each actor's world matrix and invalidate only the changed subtree when a
      local transform or parent changes.
- [x] During traversal, compute a changed actor's world matrix once and pass it to
      children. Reuse the cached world matrix in deferred, forward, and shadow
      passes.
- [] Keep the current parent-before-child ordering and draw behavior.

This directly targets the 0.75/0.38 ms deferred and 0.80/0.32 ms shadow
regions, rather than optimizing the already-cheap input path.

### 4. Forward pass and light preparation: only after traversal data is shared

- Use the same cached forward renderable list and world matrices in the forward
  pass; avoid a separate component scan.
- Cache packed light UBO data in [scene.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/scene.py)
  and upload only on light/transform changes.
- Cache camera projection/view/inverse view-projection matrices in
  [camera.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/scene/camera.py)
  for the ray, debug, volumetric, and render paths.

These are follow-up optimizations for the 0.11-0.34 ms regions and should not
precede the shadow/deferred work.

### 5. Defer low-value input and quad micro-optimizations

The input path is 0.03-0.05 ms, so binding indexing is explicitly lower
priority. Implement it only if profiling shows it scales with scene interaction.
Likewise, sampler/uniform/state caching in screen quads should be considered
only after measuring the 0.20 ms lighting and sub-0.11 ms volumetric/blur paths.

In [manager.py](/home/alex/Documents/CompositionSoftware.worktrees/engine-optimization-cpu-reduction/compsoft/input/manager.py):

- Store bindings in a dictionary keyed by `(Inputs, TriggerMode)`.
- Sort each bucket by `chord_weight` only in `add_binding`, not in `handle_input_event` or `update`.
- In `update`, iterate the precomputed bucket for each active key.
- Preserve modifier matching, release-time modifier snapshots, consumer priority, and early consumption exactly.
- Keep `active_keys` as a set; do not introduce per-frame key polling.

Expected result: no list comprehensions or sorts for every held key and input event.

## Validation

- Capture a baseline and post-change profile on the same representative scene.
- Compare average and percentile CPU frame time, plus counts of matrix inversions, `to_dtype` conversions, binding sorts, actor visits, and draw calls.
- Verify static scenes stop rebuilding transforms/lights while moving actors and camera still update correctly.
- Run existing `ruff`, `ty`, and any repository test commands from the Makefile/pyproject.

## Out of scope

Shader instruction count, texture formats, shadow resolution, blur quality, batching/instancing, GPU occlusion culling, and converting the engine to C++ are separate projects. They may improve total frame time but are not part of this CPU-overhead pass.
