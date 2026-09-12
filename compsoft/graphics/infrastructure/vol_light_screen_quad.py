import glfw
from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE3,
    GL_TEXTURE4,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBindVertexArray,
    glDrawArrays,
    glEnable,
    glViewport,
)
from pyglm.glm import mat4x4, vec2, vec3

from compsoft.graphics.infrastructure.screen_quad import ScreenQuad


class VolumetricLightScreenQuad(ScreenQuad):
    def render(
        self,
        screen_width: int,
        screen_height: int,
        position_tex: int,
        normal_tex: int,
        color_tex: int,
        selected_tex: int,
        shadows_tex: int,
        camera_pos: vec3,
        inv_camera_view: mat4x4 | None = None,
    ):
        inv_camera_view = inv_camera_view or mat4x4()
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
        self.shader.set_uniform_matrix("uInvViewProj", inv_camera_view)
        self.shader.set_uniform_float("uTime", float(glfw.get_time() * 10.0))

        glBindVertexArray(self.vxt)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)
