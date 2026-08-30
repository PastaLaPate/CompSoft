from pyglm.glm import mat4, mat4x4, vec3

from compsoft.graphics.materials.material import Material
from compsoft.graphics.shader import Shader
from compsoft.resources.manager import resources


class DepthMaterial(Material):
    def __init__(self) -> None:
        shader_pair = resources.get_shader_path("depth")
        self.shader = Shader(shader_pair.vertex, shader_pair.fragment)

    def bind_properties(self):
        pass

    def use(
        self,
        mvp_matrix: mat4x4,
        model_matrix: mat4 | None = None,
        view_matrix: mat4 | None = None,
        normal_matrix: mat4 | None = None,
        cam_pos: vec3 | None = None,
        selected: bool = False,
    ):
        self.shader.use()

        self.shader.set_uniform_matrix("uMVP", mvp_matrix)
