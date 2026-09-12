from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBindVertexArray,
    glDisable,
    glDrawArrays,
    glEnable,
    glViewport,
)
from pyglm.glm import mat4x4, vec2, vec3

from compsoft.graphics.infrastructure.screen_quad import ScreenQuad


class BlurScreenQuad(ScreenQuad):
    def bind_shader(
        self, light_space_matrices: dict[int, mat4x4] | None = None
    ):
        glDisable(GL_DEPTH_TEST)
        self.shader.use()

    def render(
        self,
        screen_width: int,
        screen_height: int,
        position_tex: int = 0,
        normal_tex: int = 0,
        color_tex: int = 0,
        selected_tex: int = 0,
        shadows_tex: int = 0,
        camera_pos: vec3 | None = None,
        blur_direction: vec2 | None = None,
    ):
        blur_direction = blur_direction or vec2(1, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, position_tex)

        glViewport(0, 0, screen_width, screen_height)

        self.shader.set_uniform_i("uColor", 0)

        self.shader.set_uniform_vec2(
            "uTexelSize", vec2(1.0 / screen_width, 1.0 / screen_height)
        )
        self.shader.set_uniform_vec2("uBlurDirection", blur_direction)

        glBindVertexArray(self.vxt)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)
