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

from compsoft.scene.components.light import LightComponent
from compsoft.scene.scene import Scene

MAX_SHADOW_LIGHTS = 8
CASCADES_N = 4


class ShadowFrameBuffer:
    def __init__(self, resolution: float = 1):
        self.width = int(1024 * resolution)
        self.height = int(1024 * resolution)
        self.max_layer = MAX_SHADOW_LIGHTS

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
        glTexParameteri(
            GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE
        )
        glTexParameteri(
            GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE
        )
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
        return self.light_layers[light] * CASCADES_N + cascade

    def render_light(self, light: LightComponent, scene: Scene) -> mat4x4:

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

        near, far = 0.1, 50
        # light_projection = glm.ortho(-10, 10, -10, 10, near, far)
        light_projection = glm.perspective(glm.radians(10), 1, near, far)
        light_view = glm.lookAt(
            light.get_data().position, vec3(0, 0, 0), vec3(0, 1, 0)
        )
        vp_matrix: mat4x4 = cast(mat4x4, light_projection * light_view)

        scene.render_shadow_map(vp_matrix)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return vp_matrix
