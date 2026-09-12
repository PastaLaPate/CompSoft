from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_DEPTH_TEST,
    GL_FALSE,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glDeleteBuffers,
    glDeleteVertexArrays,
    glDisable,
    glDrawArrays,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glGetUniformBlockIndex,
    glUniformBlockBinding,
    glVertexAttribPointer,
)
from pyglm.glm import mat4x4

from compsoft.graphics.shader import Shader


class ScreenQuad(ABC):
    def __init__(
        self, passthrough_vert_path: Path, postprocess_frag_path: Path
    ) -> None:
        self.vxt = glGenVertexArrays(1)
        glBindVertexArray(self.vxt)

        quad_vertex_buffer_data = np.array(
            [
                [-1, -1, 0],
                [1, -1, 0],
                [-1, 1, 0],
                [-1, 1, 0],
                [1, -1, 0],
                [1, 1, 0],
            ],
            np.float32,
        ).ravel()

        self.quad_vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vertex_buffer)
        glBufferData(
            GL_ARRAY_BUFFER,
            quad_vertex_buffer_data.nbytes,
            quad_vertex_buffer_data,
            GL_STATIC_DRAW,
        )

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(
            0,  # attribute 0. No particular reason for 0, but must match the layout in the shader.
            3,  # size
            GL_FLOAT,  # type
            GL_FALSE,  # normalized?
            0,  # stride
            None,  # array buffer offset
        )

        glBindVertexArray(0)
        self.shader = Shader(passthrough_vert_path, postprocess_frag_path)

    def bind_shader(self, **kwargs):
        glDisable(GL_DEPTH_TEST)
        self.shader.use()

    @abstractmethod
    def render(self, screen_width: int, screen_height: int, **kwargs):
        pass

    def draw(self):
        glBindVertexArray(self.vxt)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)

    def destroy(self) -> None:
        if self.vxt:
            glDeleteVertexArrays(1, [self.vxt])
        if self.quad_vertex_buffer:
            glDeleteBuffers(1, [self.quad_vertex_buffer])
        if self.shader:
            self.shader.destroy()


class LitScreenQuad(ScreenQuad, ABC):
    def bind_shader(
        self, light_space_matrices: dict[int, mat4x4] | None = None, **kwargs
    ):
        super().bind_shader(**kwargs)
        if light_space_matrices:
            block_index = glGetUniformBlockIndex(
                self.shader.program_id, "LightingBlock"
            )
            glUniformBlockBinding(self.shader.program_id, block_index, 0)
            self.upload_light_space_matrices(light_space_matrices)
        else:
            raise RuntimeError("Light space matrices not set")

    def upload_light_space_matrices(self, matrices: dict[int, mat4x4]):
        for light_i, matrix in matrices.items():
            self.shader.set_uniform_matrix(
                f"uLightSpaceMatrices[{light_i}]", matrix
            )
