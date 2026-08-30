from OpenGL.GL import (
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    GL_NEAREST,
    GL_NONE,
    GL_REPEAT,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    glBindFramebuffer,
    glBindTexture,
    glClear,
    glDrawBuffer,
    glEnable,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenTextures,
    glReadBuffer,
    glTexImage2D,
    glTexParameteri,
    glViewport,
)
from pyglm import glm
from pyglm.glm import vec3

from compsoft.scene.components.light import LightComponent
from compsoft.scene.scene import Scene


class ShadowFrameBuffer:
    def __init__(self, resolution: float = 1):
        self.width = 1024 * resolution
        self.height = 1024 * resolution

        self.lights_depth_map: dict[LightComponent, tuple[int, int]] = {}

    def new_light(self, light: LightComponent):
        # Build a new frame buffer
        fbo = glGenFramebuffers(1)

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_DEPTH_COMPONENT,
            self.width,
            self.height,
            0,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
            None,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, texture, 0
        )
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        self.lights_depth_map[light] = (fbo, texture)

    def render_light(self, light: LightComponent, scene: Scene):
        fbo, texture = self.lights_depth_map[light]
        glViewport(0, 0, self.width, self.height)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_DEPTH_BUFFER_BIT)
        near, far = 1, 50
        light_projection = glm.ortho(-10, 10, -10, 10, near, far)
        light_view = glm.lookAt(
            light.get_data().position, vec3(0, 0, 0), vec3(0, 1, 0)
        )
        scene.render_shadow_map(light_projection * light_view)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
