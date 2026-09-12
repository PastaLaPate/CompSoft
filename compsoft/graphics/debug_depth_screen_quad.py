from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_TEXTURE0,
    GL_TEXTURE_2D_ARRAY,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBindVertexArray,
    glDrawArrays,
    glEnable,
)

from compsoft.graphics.infrastructure.quads.screen_quad import ScreenQuad
from compsoft.resources.manager import resources


class DebugDepthScreenQuad(ScreenQuad):
    def __init__(self):
        sq_shader_pair = resources.get_shader_path("debug_depth")
        super().__init__(sq_shader_pair.vertex, sq_shader_pair.fragment)

    def render(
        self,
        screen_width: int,
        screen_height: int,
        position_tex: int = 0,
        shadows_tex: int = 0,
        **kwargs,
    ):

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, shadows_tex)

        self.shader.set_uniform_i("uShadowMapArray", 0)
        self.shader.set_uniform_i("uDebugLayer", position_tex)

        glBindVertexArray(self.vxt)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)
