from pathlib import Path

from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    glActiveTexture,
    glBindTexture,
    glUseProgram,
)
from pyglm.glm import mat4

from compsoft.consts import ROOT
from compsoft.shader import Shader
from compsoft.textures import TextureRegistry


class Material:
    def __init__(self, albedo: Path) -> None:
        self.shader = Shader(
            ROOT / "shaders" / "shaded" / "vertex.glsl",
            ROOT / "shaders" / "shaded" / "fragment.glsl",
        )

        self.albedo = TextureRegistry.get_texture(albedo) or -1

    def bind_properties(self):
        glUseProgram(self.shader.program_id)

        if self.albedo != -1:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.albedo)

            # Set sampler location
            self.shader.set_uniform_i("albedo", 0)

    def use(self, mvp_matrix: mat4, model_matrix: mat4, view_matrix: mat4):
        self.shader.use()

        self.shader.set_uniform_matrix("MVP", mvp_matrix)
