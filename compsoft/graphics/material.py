from pathlib import Path

from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    glActiveTexture,
    glBindTexture,
    glGetUniformBlockIndex,
    glUniformBlockBinding,
    glUseProgram,
)
from pyglm.glm import mat4, vec3

from compsoft.graphics.shader import Shader
from compsoft.resources.manager import resources
from compsoft.resources.textures import TextureRegistry


class Material:
    def __init__(self, albedo: Path, normal: Path | None = None) -> None:
        shader_pair = resources.get_shader_path("shaded")
        self.shader = Shader(shader_pair.vertex, shader_pair.fragment)
        self.light_pos = vec3(10, 10, 10)

        self.albedo = TextureRegistry.get_texture(albedo) or -1
        self.normal = (
            TextureRegistry.get_texture(normal)
            if normal
            else TextureRegistry.get_default_normal() or -1
        )

    def bind_properties(self):
        glUseProgram(self.shader.program_id)

        block_index = glGetUniformBlockIndex(
            self.shader.program_id, "LightingBlock"
        )
        glUniformBlockBinding(self.shader.program_id, block_index, 0)
        self.shader.set_uniform_i("albedo", 0)
        self.shader.set_uniform_i("normal", 1)

    def use(
        self,
        mvp_matrix: mat4,
        model_matrix: mat4,
        view_matrix: mat4,
        normal_matrix: mat4,
        cam_pos: vec3,
    ):
        self.shader.use()

        if self.albedo != -1:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.albedo)
        if self.normal != -1:
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.normal)

        self.shader.set_uniform_matrix("MVP", mvp_matrix)
        self.shader.set_uniform_matrix("M", model_matrix)
        self.shader.set_uniform_matrix("V", view_matrix)
        self.shader.set_uniform_matrix("NormalMatrix", normal_matrix)
        self.shader.set_uniform_vec3("cameraPosition_worldspace", cam_pos)
