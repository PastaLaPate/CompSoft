import math
from collections import deque
from typing import cast

from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    GL_NEAREST,
    GL_NONE,
    GL_TEXTURE_2D_ARRAY,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    glBindFramebuffer,
    glBindTexture,
    glClear,
    glDeleteFramebuffers,
    glDeleteTextures,
    glDrawBuffer,
    glEnable,
    glFramebufferTextureLayer,
    glGenFramebuffers,
    glGenTextures,
    glReadBuffer,
    glTexImage3D,
    glTexParameteri,
    glViewport,
)
from pyglm import glm
from pyglm.glm import mat4x4, vec3

from compsoft.scene.components.light import (
    LightComponent,
    LightData,
    LightType,
)
from compsoft.scene.scene import Scene

MAX_SHADOW_LIGHTS = 8
CASCADES_N = 4

# A depth layer costs width * height * 4 bytes. Past roughly half a gigabyte the
# array stops staying resident on a 6GB card that is also driving the desktop, and
# every depth write in the shadow pass goes over PCIe: 420MB/frame at ~7GB/s is
# ~60ms instead of ~0.6ms. Warn instead of silently collapsing to 2 fps.
SHADOW_VRAM_WARN_BYTES = 512 * 1024 * 1024


class ShadowFrameBuffer:
    """Depth-only 2D texture array with one shadow map per light.

    Layers are allocated on demand: the array starts with a single layer and grows
    by doubling when another shadow-casting light registers. Sizing it eagerly for
    MAX_SHADOW_LIGHTS wastes most of the VRAM for scenes that use two or three
    lights - at 5120x5120 the unused layers alone are half a gigabyte.
    """

    def __init__(self, resolution: float = 1, max_layers: int = MAX_SHADOW_LIGHTS):
        self.width = int(1024 * resolution)
        self.height = int(1024 * resolution)
        self.max_layer = max_layers

        # Bound to the light component, not to its current data: moving lights used
        # to insert a fresh entry in the value-keyed dict every frame.
        self.matrices_cache: dict[LightComponent, tuple[LightData, mat4x4]] = {}

        self.light_layers: dict[
            LightComponent, int
        ] = {}  # light: texture2d_array layer
        self._available_layers: deque[int] = deque()  # queue of available layers

        self.layer_capacity = 0
        self.shadow_array_tex = 0
        self._allocate_layers(1)

        # Build a new frame buffer
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    @property
    def vram_bytes(self) -> int:
        # 4 bytes per depth sample (GL_DEPTH_COMPONENT is uploaded as float)
        return self.width * self.height * 4 * self.layer_capacity

    def _allocate_layers(self, layers: int) -> None:
        layers = max(1, min(layers, self.max_layer))

        if self.shadow_array_tex:
            glDeleteTextures(1, [self.shadow_array_tex])

        self.shadow_array_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.shadow_array_tex)
        glTexImage3D(
            GL_TEXTURE_2D_ARRAY,
            0,  # Mip level
            GL_DEPTH_COMPONENT,  # GPU Format
            self.width,
            self.height,
            layers,  # depth = layer count
            0,  # legacy
            GL_DEPTH_COMPONENT,  # cpu format
            GL_FLOAT,  # type
            None,  # No data
        )
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

        # Existing layer assignments keep their index; their contents are dropped but
        # every shadow map is re-rendered before it is sampled.
        for layer in range(self.layer_capacity, layers):
            self._available_layers.append(layer)
        self.layer_capacity = layers

        if self.vram_bytes > SHADOW_VRAM_WARN_BYTES:
            mib = self.vram_bytes / (1024 * 1024)
            print(
                f"WARNING: shadow map array is {mib:.0f} MiB "
                f"({self.width}x{self.height} x {layers} layers). Above ~512 MiB it "
                "can stop being resident in VRAM and the shadow pass falls back to "
                "PCIe traffic. Lower ShadowFrameBuffer(resolution=...) or use fewer "
                "shadow-casting lights."
            )

    def get_light_layer(self, light: LightComponent, cascade: int = 0) -> int:
        layer = self.light_layers.get(light)
        if layer is None:
            if not self._available_layers:
                if self.layer_capacity >= self.max_layer:
                    raise RuntimeError("No more shadow texture available")
                self._allocate_layers(self.layer_capacity * 2)
            layer = self._available_layers.popleft()
            self.light_layers[light] = layer
        return layer  # * CASCADES_N + cascade

    def _compute_vp_matrix(self, light_data: LightData, near=0.1, far=50.0) -> mat4x4:
        if light_data.type == LightType.DIRECTIONAL:
            light_projection = glm.ortho(-10, 10, -10, 10, near, far)
        else:
            spot_angle = math.degrees(math.acos(light_data.inner_cutoff))
            light_projection = glm.perspective(
                glm.radians(spot_angle * 2.0), 1.0, near, far
            )

        light_dir = light_data.direction
        if glm.length(light_dir) == 0:
            raise ValueError("Shadow-casting light direction must not be zero")
        light_dir = glm.normalize(light_dir)

        if light_data.type == LightType.DIRECTIONAL:
            light_pos = -light_dir * far
            up = vec3(0, 0, 1) if abs(light_dir.y) > 0.9 else vec3(0, 1, 0)
            light_target = vec3(0, 0, 0)
        else:
            light_pos = light_data.position
            up = (
                vec3(0, 0, 1)
                if abs(glm.dot(light_dir, vec3(0, 1, 0))) > 0.99
                else vec3(0, 1, 0)
            )
            light_target = light_pos + light_dir

        light_view = glm.lookAt(
            light_pos,
            light_target,
            up,
        )

        vp_matrix: mat4x4 = cast(mat4x4, light_projection * light_view)
        return vp_matrix

    def render_light(self, light: LightComponent, scene: Scene) -> mat4x4:
        if not light.parent:
            return mat4x4()
        layer = self.get_light_layer(light)

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTextureLayer(
            GL_FRAMEBUFFER,
            GL_DEPTH_ATTACHMENT,
            self.shadow_array_tex,
            0,
            layer,
        )
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_DEPTH_BUFFER_BIT)

        light_data = light.get_data()
        cached = self.matrices_cache.get(light)
        if cached is None or cached[0] != light_data:
            cached = (light_data, self._compute_vp_matrix(light_data, 0.1, 50.0))
            self.matrices_cache[light] = cached
        matrix: mat4x4 = cached[1]

        scene.render_shadow_map(matrix)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return matrix

    def release_light(self, light: LightComponent) -> None:
        """Gives the light's layer back so a later light can reuse it."""
        layer = self.light_layers.pop(light, None)
        if layer is not None:
            self._available_layers.append(layer)
        self.matrices_cache.pop(light, None)

    def destroy(self) -> None:
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
            self.fbo = 0
        if self.shadow_array_tex:
            glDeleteTextures(1, [self.shadow_array_tex])
            self.shadow_array_tex = 0
