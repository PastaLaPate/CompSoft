from pathlib import Path
from typing import overload

from glm import value_ptr
from OpenGL.GL import (
    GL_FALSE,
    GL_TRUE,
    glDeleteProgram,
    glGetUniformLocation,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUniform3f,
    glUniformMatrix3fv,
    glUniformMatrix4fv,
    glUseProgram,
)
from pyglm.glm import mat3, mat4, vec2, vec3

from compsoft.resources.manager import ShaderPair
from compsoft.resources.shaders import ShaderRegistry


class Shader:
    @overload
    def __init__(self, pair: ShaderPair, /) -> None: ...

    @overload
    def __init__(self, vert_path: Path, frag_path: Path, /): ...

    def __init__(
        self,
        vert_path_or_pair: Path | ShaderPair,
        frag_path: Path | None = None,
    ):
        if isinstance(vert_path_or_pair, ShaderPair):
            vert, frag = vert_path_or_pair
        elif frag_path is not None:
            vert, frag = vert_path_or_pair, frag_path
        else:
            raise TypeError("Invalid arguments provided.")
        self.program_id = ShaderRegistry.get_program(vert, frag)

        self._uniform_locations: dict[str, int] = {}

    def get_uniform_location(self, name: str) -> int:
        if name not in self._uniform_locations:
            location = glGetUniformLocation(self.program_id, name)
            self._uniform_locations[name] = location
        return self._uniform_locations[name]

    def set_uniform_matrix(self, name: str, matrix: mat4) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            if isinstance(matrix, mat4):
                glUniformMatrix4fv(loc, 1, GL_FALSE, value_ptr(matrix))
            elif isinstance(matrix, mat3):
                glUniformMatrix3fv(loc, 1, GL_FALSE, value_ptr(matrix))

    def set_uniform_float(self, name: str, val: float) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1f(loc, val)

    def set_uniform_i(self, name: str, val: int) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1i(loc, val)

    def set_uniform_bool(self, name: str, val: bool) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1i(loc, GL_TRUE if val else GL_FALSE)

    def set_uniform_vec2(self, name: str, val: vec2) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform2f(loc, val.x, val.y)

    def set_uniform_vec3(self, name: str, val: vec3) -> None:
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform3f(loc, val.x, val.y, val.z)

    def use(self):
        glUseProgram(self.program_id)

    def destroy(self):
        glDeleteProgram(self.program_id)
        ShaderRegistry.remove_cache_for_program(self.program_id)
