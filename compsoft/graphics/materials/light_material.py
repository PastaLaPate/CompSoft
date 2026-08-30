from pathlib import Path

from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    glActiveTexture,
    glBindTexture,
)
from pyglm.glm import mat4, vec3

from compsoft.graphics.materials.material import Material
from compsoft.graphics.shader import Shader
from compsoft.resources.manager import resources
from compsoft.resources.textures import TextureRegistry


class LightMaterial(Material):
    def __init__(self, albedo: Path | int, normal: Path | None = None) -> None:
        shader_pair = resources.get_shader_path("light")
        self.shader = Shader(shader_pair.vertex, shader_pair.fragment)

        self.albedo = (
            TextureRegistry.get_texture(albedo) or -1
            if isinstance(albedo, Path)
            else albedo
        )
        self.normal = (
            TextureRegistry.get_texture(normal)
            if normal
            else TextureRegistry.get_default_normal() or -1
        )

    def use(
        self,
        mvp_matrix: mat4,
        model_matrix: mat4,
        view_matrix: mat4,
        normal_matrix: mat4,
        cam_pos: vec3,
        selected: bool,
    ):
        self.shader.use()

        if self.albedo != -1:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.albedo)
        if self.normal != -1:
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.normal)

        self.shader.set_uniform_matrix("uMVP", mvp_matrix)
        self.shader.set_uniform_matrix("uModel", model_matrix)
        self.shader.set_uniform_matrix("uV", view_matrix)
        self.shader.set_uniform_matrix("uNormalMatrix", normal_matrix)
        self.shader.set_uniform_vec3("uCameraPosition_W", cam_pos)
        self.shader.set_uniform_bool("uIsSelected", selected)
