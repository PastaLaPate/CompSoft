from pathlib import Path

import glfw
import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_DEPTH_TEST,
    GL_FALSE,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE3,
    GL_TEXTURE4,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    GL_TRIANGLES,
    glActiveTexture,
    glBindBuffer,
    glBindTexture,
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
    glViewport,
)
from pyglm.glm import mat4x4, vec2, vec3

from compsoft.graphics.shader import Shader


class ScreenQuad:
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

    def bind_shader(self, light_space_matrices: dict[int, mat4x4]):
        glDisable(GL_DEPTH_TEST)
        self.shader.use()
        block_index = glGetUniformBlockIndex(
            self.shader.program_id, "LightingBlock"
        )
        glUniformBlockBinding(self.shader.program_id, block_index, 0)
        self.upload_light_space_matrices(light_space_matrices)

    def upload_light_space_matrices(self, matrices: dict[int, mat4x4]):
        for light_i, matrix in matrices.items():
            self.shader.set_uniform_matrix(
                f"lightSpaceMatrices[{light_i}]", matrix
            )

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
    ):
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

        self.shader.set_uniform_i("positionTexture", 0)
        self.shader.set_uniform_i("normalTexture", 1)
        self.shader.set_uniform_i("colorTexture", 2)
        self.shader.set_uniform_i("selectionTexture", 3)
        self.shader.set_uniform_i("shadowMapArray", 4)

        self.shader.set_uniform_vec2(
            "u_TexelSize", vec2(1.0 / screen_width, 1.0 / screen_height)
        )

        self.shader.set_uniform_vec3("cameraPos", camera_pos)
        self.shader.set_uniform_float("time", float(glfw.get_time() * 10.0))

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
