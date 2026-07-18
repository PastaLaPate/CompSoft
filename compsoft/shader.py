from pathlib import Path

from glm import value_ptr
from OpenGL.GL import (
    GL_FALSE,
    glGetUniformLocation,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
)
from pyglm.glm import vec3

from compsoft.shaders import ShaderRegistry


class Shader:
    def __init__(self, vert_path: Path, frag_path: Path):
        self.program_id = ShaderRegistry.get_program(vert_path, frag_path)

        self._uniform_locations: dict[str, int] = {}

    def get_uniform_location(self, name: str) -> int:
        if name not in self._uniform_locations:
            location = glGetUniformLocation(self.program_id, name)
            self._uniform_locations[name] = location
        return self._uniform_locations[name]

    def set_uniform_matrix(self, name: str, matrix) -> None:
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniformMatrix4fv(loc, 1, GL_FALSE, value_ptr(matrix))

    def set_uniform_float(self, name: str, val: float) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1f(loc, val)

    def set_uniform_i(self, name: str, val: int) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1i(loc, val)

    def set_uniform_vec3(self, name: str, val: vec3) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform3f(loc, val.x, val.y, val.z)

    def use(self):
        glUseProgram(self.program_id)
