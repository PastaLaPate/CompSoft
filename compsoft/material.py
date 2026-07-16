from OpenGL.GL import (
    glGetUniformLocation,
    glUseProgram,
    glUniformMatrix4fv,
    GL_FALSE,
)
from pathlib import Path
from compsoft.shaders import ShaderRegistry
import pyglm.glm as glm


class Material:
    def __init__(self, vert_path: Path, frag_path: Path):
        self.program_id = ShaderRegistry.get_program(vert_path, frag_path)

        self._uniform_locations: dict[str, int] = {}

    def get_uniform_location(self, name: str) -> int:
        if name not in self._uniform_locations:
            location = glGetUniformLocation(self.program_id, name)
            self._uniform_locations[name] = location
        return self._uniform_locations[name]

    def use(self, mvp_matrix: glm.mat4):
        glUseProgram(self.program_id)

        matrix_loc = self.get_uniform_location("MVP")
        if matrix_loc != -1:
            glUniformMatrix4fv(
                matrix_loc, 1, GL_FALSE, glm.value_ptr(mvp_matrix)
            )
