# AGENTS.md - CompSoft

## Commands

### Run the engine
```bash
uv run compsoft
# or
uv run python -m compsoft
```

### Benchmark
```bash
# Fixed number of frames, prints the profiler table once to stdout
uv run python tools/bench.py

# Smaller target / shadow map, and a frozen scene for before-after pixel diffs
BENCH_W=1280 BENCH_H=720 BENCH_SHADOW_RES=2 uv run python tools/bench.py
BENCH_FREEZE=1 BENCH_SHOT=/tmp/frame.png uv run python tools/bench.py
```

### Development workflow
```bash
# Install pre-commit hooks
make hooks

# Pre-commit hooks run in order:
# 1. uv-lock (sync dependencies)
# 2. ruff check --fix (lint + auto-fix)
# 3. ruff format (format)
# 4. ty (type check)
```

### CI pipeline order
```bash
uv sync --locked --all-extras
uvx ruff format --check .
uvx ruff check .
uvx ty check .
uv build
```

## Project Paths

```
/home/alex/Documents/CompSoft/

compsoft/
├── __main__.py      # Entry point
├── core/            # Engine, window, debug, profiler
├── graphics/        # Rendering pipeline (shaders, frame buffers, materials)
├── scene/           # Scene graph (actors, components, camera, lights)
├── input/           # Input handling (keyboard, mouse, gizmos)
├── resources/       # Shaders, textures, models
└── assets/          # Static assets
```

## Key Files

| File | Purpose |
|------|---------|
| `compsoft/__main__.py` | Main entry point, sets up OpenGL env vars for PRIME offload |
| `compsoft/core/engine.py` | Engine loop, window management, render pipeline orchestration |
| `compsoft/scene/scene.py` | Scene graph, actor/component hierarchy, raycasting, lights |
| `compsoft/graphics/infrastructure/render_pass.py` | Render pass enumeration (DEFERRED, FORWARD, SHADOW) |

## Environment Quirks

### NVIDIA PRIME Offload
```python
os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
```

### AMD / Mesa PRIME
```python
os.environ["DRI_PRIME"] = "1"
```

**Location:** `compsoft/__main__.py` lines 24-29

## Rendering Pipeline

1. **Deferred Pass** → Color/normal/depth textures
2. **Shadow Map** → Per-light shadow buffers (8 lights max)
3. **Lighting Pass** → Combine lighting with shadows
4. **Forward Pass** → Final geometry rendering
5. **Volumetric Light** → Volume lighting effect
6. **Blur Pass** → Horizontal + vertical blur for volumetric effect
7. **Post-process** → Final tone mapping

## Scene Graph Hierarchy

```
Actor
├── position, rotation, scale (vec3)
├── children (Actor[])
│   └── add_child(actor)
└── components[]
    ├── SimpleCubeComponent
    ├── SimpleConeComponent
    ├── SimpleCylinderComponent
    ├── ModelMeshComponent (for .obj, .gltf models)
    ├── LightComponent (DirectionalLight, SpotLight)
    └── RenderableComponent
```

**Add component:**
```python
actor.add_component(ComponentClass(material))
```

**Add child actor:**
```python
child_actor = actor.add_child(Actor())
```

## Debug Flags

Located in `compsoft/core/debug.py` as `DebugFlags.*`:

| Flag | Purpose |
|------|---------|
| `DEBUG_FRAME_TIME` | Show FPS in profiler |
| `DEBUG_FRAME_TIME_DETAILLED` | Detailed timing breakdown |
| `DEBUG_RENDER_SHADOW_MAP` | Render shadow map pass (1024×1024) |
| `DEBUG_MESH_AABB` | Show bounding boxes |
| `DEBUG_SELECTION_RAYCAST` | Show selection ray |

**Enable in code:**
```python
scene.debug.add_flag(DebugFlags.DEBUG_FRAME_TIME_DETAILLED)
scene.debug.add_flag(DebugFlags.DEBUG_RENDER_SHADOW_MAP)
```

## Shader Paths

All shaders in `compsoft/resources/shaders/`:

| Shader | Path |
|--------|------|
| Lit | `resources.get_shader_path("lit")` |
| Volumetric light | `resources.get_shader_path("vol_light")` |
| Blur | `resources.get_shader_path("blur")` |
| Postprocess | `resources.get_shader_path("postprocess")` |

## Dependencies

- **GLFW** - Window management
- **PyOpenGL** - OpenGL bindings
- **PyGLM** - GLM wrapper for math
- **NumPy** - Numerical operations
- **Pillow** - Image handling
- **trimesh** - 3D model loading
- **rich** - Terminal output

## Input Bindings

Located in `compsoft/input/`:

| Binding | Action |
|---------|--------|
| `BINDING_CAMERA_PAN` / `_RELEASE` | Pan camera |
| `BINDING_CAMERA_ORBIT` / `_RELEASE` | Orbit camera |
| `BINDING_FORWARD` / `BINDING_BACKWARD` | Move forward/back |
| `BINDING_LEFT` / `BINDING_RIGHT` | Strafe |
| `BINDING_CAMERA_SPEED` | Adjust camera speed |
| `BINDING_CAMERA_FOV` | Adjust field of view |
| `BINDING_SCENE_LMB_CLICK` | Raycast selection |
| `BINDING_GIZMO_CLICK` / `_RELEASE` | Manipulate gizmo |

## Utilities

### Prerender listener
```python
def tick(t: float, dt: float):
    # Called each frame before rendering
    pass

engine._add_prerender_listener(tick)
```

### Resources
```python
from compsoft.resources.manager import resources

# Get texture path
path = resources.get_texture_path("texture.png")

# Get model path
path = resources.get_model_path("model.obj")

# Get shader path
path = resources.get_shader_path("shader.glsl")
```

## Testing

No test files currently present. Add tests in `compsoft/tests/` or use pytest convention.

## Build

```bash
uv build  # Creates wheel package
```

## Versioning

Uses `commitizen` with conventional commits:
```bash
cz bump  # Bump version
cz version  # Show current version
```

## Notes

- Python 3.14+ required
- Uses `uv` package manager (not pip)
- Single package, no monorepo
- Scene graph inspired by Unreal/Unity
