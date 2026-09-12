from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    glActiveTexture,
    glBindTexture,
    glViewport,
)
from pyglm.glm import vec2

from compsoft.graphics.infrastructure.quads.screen_quad import ScreenQuad


class PostScreenQuad(ScreenQuad):
    def render(
        self,
        screen_width: int,
        screen_height: int,
        color_tex: int | None = None,
        **kwargs,
    ):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, color_tex)

        glViewport(0, 0, screen_width, screen_height)

        self.shader.set_uniform_i("uColor", 0)

        self.shader.set_uniform_vec2(
            "uTexelSize", vec2(1.0 / screen_width, 1.0 / screen_height)
        )

        self.draw()
