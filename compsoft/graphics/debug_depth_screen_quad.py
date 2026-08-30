from glm import vec3
from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_TEXTURE0,
    GL_TEXTURE_2D_ARRAY,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBindVertexArray,
    glDisable,
    glDrawArrays,
    glEnable,
)

from compsoft.graphics.screen_quad import ScreenQuad
from compsoft.resources.manager import resources


class DebugDepthScreenQuad(ScreenQuad):
    def __init__(self):
        sq_shader_pair = resources.get_shader_path("debug_depth")
        super().__init__(sq_shader_pair.vertex, sq_shader_pair.fragment)

    def bind_shader(self):
        glDisable(GL_DEPTH_TEST)
        self.shader.use()

    def render(
        self,
        screen_width: int,
        screen_height: int,
        position_tex: int = 0,
        normal_tex: int | None = None,
        color_tex: int | None = None,
        selected_tex: int | None = None,
        shadows_tex: int = 0,
        camera_pos: vec3 | None = None,
    ):

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, shadows_tex)

        self.shader.set_uniform_i("shadowMapArray", 0)
        self.shader.set_uniform_i("debugLayer", position_tex)

        glBindVertexArray(self.vxt)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)
