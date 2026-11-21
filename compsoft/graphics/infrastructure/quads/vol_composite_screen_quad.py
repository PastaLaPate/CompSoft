from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    glActiveTexture,
    glBindTexture,
    glViewport,
)
from pyglm.glm import vec2, vec3

from compsoft.graphics.infrastructure.quads.screen_quad import ScreenQuad


class VolumetricCompositeScreenQuad(ScreenQuad):
    """Upsamples the half-resolution fog onto the scene, depth-aware.

    Reads the horizontally blurred fog plus the full-resolution position buffer,
    so taps that belong to a different surface than the pixel are rejected
    instead of bleeding across silhouettes. Drawn with additive blending, on top
    of the already lit scene.
    """

    def render(
        self,
        screen_width: int,
        screen_height: int,
        fog_tex: int | None = None,
        fog_width: int = 1,
        fog_height: int = 1,
        position_tex: int | None = None,
        camera_pos: vec3 | None = None,
        **kwargs,
    ):
        camera_pos = camera_pos or vec3(0, 0, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, fog_tex)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, position_tex)

        glViewport(0, 0, screen_width, screen_height)

        self.shader.set_uniform_i("uFog", 0)
        self.shader.set_uniform_i("uPosition", 1)
        self.shader.set_uniform_vec3("uCameraPos", camera_pos)
        self.shader.set_uniform_vec2(
            "uFogTexelSize", vec2(1.0 / fog_width, 1.0 / fog_height)
        )

        self.draw()
