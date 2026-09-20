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


class ShadowFrameBuffer:
    def __init__(self, resolution: float = 1):
        self.width = int(1024 * resolution)
        self.height = int(1024 * resolution)
        self.max_layer = MAX_SHADOW_LIGHTS

        self.matrices_cache: dict[LightData, mat4x4] = {}

        self.light_layers: dict[
            LightComponent, int
        ] = {}  # light: texture2d_array layer
        self._available_layers: deque[int] = deque(
            range(MAX_SHADOW_LIGHTS)
        )  # queue of available layers

        self.shadow_array_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.shadow_array_tex)
        glTexImage3D(
            GL_TEXTURE_2D_ARRAY,
            0,  # Mip level
            GL_DEPTH_COMPONENT,  # GPU Format
            self.width,
            self.height,
            self.max_layer,  # depth = layer count
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

        # Build a new frame buffer
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def get_light_layer(self, light: LightComponent, cascade: int = 0) -> int:
        if light not in self.light_layers:
            if len(self._available_layers) == 0:
                raise RuntimeError("No more shadow texture available")
            layer = self._available_layers.popleft()
            self.light_layers[light] = layer
        return self.light_layers[light]  # * CASCADES_N + cascade

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
        if not light_data in self.matrices_cache:
            self.matrices_cache[light_data] = self._compute_vp_matrix(
                light_data, 0.1, 50.0
            )

        scene.render_shadow_map(self.matrices_cache[light_data])

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return self.matrices_cache[light_data]
