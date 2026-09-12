import glfw
from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE3,
    GL_TEXTURE4,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    glActiveTexture,
    glBindTexture,
    glViewport,
)
from pyglm.glm import vec2, vec3

from compsoft.graphics.infrastructure.quads.screen_quad import (
    LitScreenQuad,
)


class SceneRenderScreenQuad(LitScreenQuad):
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

        glViewport(0, 0, screen_width, screen_height)

        self.shader.set_uniform_i("uPosition", 0)
        self.shader.set_uniform_i("uNormal", 1)
        self.shader.set_uniform_i("uColor", 2)
        self.shader.set_uniform_i("uSelection", 3)
        self.shader.set_uniform_i("uShadowMapArray", 4)

        self.shader.set_uniform_vec2(
            "uTexelSize", vec2(1.0 / screen_width, 1.0 / screen_height)
        )

        self.shader.set_uniform_vec3("uCameraPos", camera_pos)
        self.shader.set_uniform_float("uTime", float(glfw.get_time() * 10.0))

        self.draw()
