import glfw
from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_COMPARE_REF_TO_TEXTURE,
    GL_LEQUAL,
    GL_LINEAR,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE3,
    GL_TEXTURE4,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    GL_TEXTURE_COMPARE_FUNC,
    GL_TEXTURE_COMPARE_MODE,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    glActiveTexture,
    glBindSampler,
    glBindTexture,
    glDeleteSamplers,
    glGenSamplers,
    glSamplerParameteri,
    glViewport,
)
from pyglm.glm import vec2, vec3

from compsoft.graphics.infrastructure.quads.screen_quad import (
    LitScreenQuad,
)
from compsoft.resources.manager import ShaderPair

SHADOW_TEXTURE_UNIT = 4


class SceneRenderScreenQuad(LitScreenQuad):
    """Deferred lighting pass: samples the G-buffer and the shadow array."""

    def __init__(self, path_pair: ShaderPair) -> None:
        super().__init__(path_pair)
        # Hardware depth comparison for this pass only. The shadow array itself
        # stays a plain depth array (NEAREST, no compare) because the volumetric
        # pass reads the same texture for its raw depth; filter and compare state
        # are per texture unit, so a sampler object gives the lighting shader a
        # filtered compare (the GL_LINEAR 2x2 comparison is a free PCF kernel)
        # without changing what the other passes see.
        self.shadow_sampler = glGenSamplers(1)
        glSamplerParameteri(self.shadow_sampler, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glSamplerParameteri(self.shadow_sampler, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glSamplerParameteri(self.shadow_sampler, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glSamplerParameteri(self.shadow_sampler, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glSamplerParameteri(
            self.shadow_sampler,
            GL_TEXTURE_COMPARE_MODE,
            GL_COMPARE_REF_TO_TEXTURE,
        )
        glSamplerParameteri(self.shadow_sampler, GL_TEXTURE_COMPARE_FUNC, GL_LEQUAL)

    def render(
        self,
        screen_width: int,
        screen_height: int,
        position_tex: int | None = 0,
        normal_tex: int | None = 0,
        color_tex: int | None = 0,
        selected_tex: int | None = 0,
        shadows_tex: int | None = 0,
        camera_pos: vec3 | None = None,
        **kwargs,
    ):
        camera_pos = camera_pos or vec3(0, 0, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, position_tex)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, normal_tex)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, color_tex)
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, selected_tex)
        glActiveTexture(GL_TEXTURE4)
        glBindTexture(GL_TEXTURE_2D_ARRAY, shadows_tex)
        glBindSampler(SHADOW_TEXTURE_UNIT, self.shadow_sampler)

        glViewport(0, 0, screen_width, screen_height)

        self.shader.set_uniform_i("uPosition", 0)
        self.shader.set_uniform_i("uNormal", 1)
        self.shader.set_uniform_i("uColor", 2)
        self.shader.set_uniform_i("uSelection", 3)
        self.shader.set_uniform_i("uShadowMapArray", SHADOW_TEXTURE_UNIT)

        self.shader.set_uniform_vec2(
            "uTexelSize", vec2(1.0 / screen_width, 1.0 / screen_height)
        )

        self.shader.set_uniform_vec3("uCameraPos", camera_pos)
        self.shader.set_uniform_float("uTime", float(glfw.get_time() * 10.0))

        self.draw()

    def destroy(self) -> None:
        if getattr(self, "shadow_sampler", 0):
            glBindSampler(SHADOW_TEXTURE_UNIT, 0)
            glDeleteSamplers(1, [self.shadow_sampler])
            self.shadow_sampler = 0
        super().destroy()
