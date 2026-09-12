import glfw
from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    glActiveTexture,
    glBindTexture,
    glViewport,
)
from pyglm.glm import mat4x4, vec2, vec3

from compsoft.graphics.infrastructure.quads.screen_quad import (
    LitScreenQuad,
)


class VolumetricLightScreenQuad(LitScreenQuad):
    def render(
        self,
        screen_width: int,
        screen_height: int,
        position_tex: int = 0,
        shadows_tex: int = 0,
        camera_pos: vec3 | None = None,
        inv_camera_view: mat4x4 | None = None,
        **kwargs,
    ):
        camera_pos = camera_pos or vec3(0, 0, 0)
        inv_camera_view = inv_camera_view or mat4x4()
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, position_tex)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, shadows_tex)

        glViewport(0, 0, screen_width, screen_height)

        self.shader.set_uniform_i("uPosition", 0)
        self.shader.set_uniform_i("uShadowMapArray", 1)

        self.shader.set_uniform_vec2(
            "uTexelSize", vec2(1.0 / screen_width, 1.0 / screen_height)
        )

        self.shader.set_uniform_vec3("uCameraPos", camera_pos)
        self.shader.set_uniform_matrix("uInvViewProj", inv_camera_view)
        self.shader.set_uniform_float("uTime", float(glfw.get_time() * 10.0))

        self.draw()
