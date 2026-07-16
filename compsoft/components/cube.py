from pyglm.glm import vec3

from compsoft.components.mesh import SimpleMeshComponent
from compsoft.material import Material


class SimpleCubeComponent(SimpleMeshComponent):
    def __init__(self, material: Material) -> None:
        super().__init__(
            [
                (vec3(1, 0, 0), vec3(1, 1, 0), vec3(1, 0, 1)),  # Right face
                (vec3(1, 0, 1), vec3(1, 1, 0), vec3(1, 1, 1)),
                (vec3(0, 0, 0), vec3(0, 0, 1), vec3(0, 1, 0)),  # Left face
                (vec3(0, 0, 1), vec3(0, 1, 1), vec3(0, 1, 0)),
                (vec3(0, 1, 0), vec3(1, 1, 1), vec3(1, 1, 0)),  # Top face
                (vec3(0, 1, 0), vec3(0, 1, 1), vec3(1, 1, 1)),
                (vec3(0, 0, 0), vec3(1, 0, 0), vec3(1, 0, 1)),  # Bottom face
                (vec3(0, 0, 0), vec3(1, 0, 1), vec3(0, 0, 1)),
                (vec3(0, 0, 1), vec3(1, 0, 1), vec3(0, 1, 1)),  # Back face
                (vec3(1, 0, 1), vec3(1, 1, 1), vec3(0, 1, 1)),
                (vec3(0, 0, 0), vec3(0, 1, 0), vec3(1, 0, 0)),  # Front face
                (vec3(1, 0, 0), vec3(0, 1, 0), vec3(1, 1, 0)),
            ],
            material,
            False,
        )
