from glm import vec2
from pyglm.glm import vec3

from compsoft.components.mesh import SimpleMeshComponent
from compsoft.material import Material


class SimpleCubeComponent(SimpleMeshComponent):
    def __init__(self, material: Material) -> None:
        super().__init__(
            [
                (
                    vec3(0.5, -0.5, -0.5),
                    vec3(0.5, 0.5, -0.5),
                    vec3(0.5, -0.5, 0.5),
                ),  # Right face
                (
                    vec3(0.5, -0.5, 0.5),
                    vec3(0.5, 0.5, -0.5),
                    vec3(0.5, 0.5, 0.5),
                ),
                (
                    vec3(-0.5, -0.5, -0.5),
                    vec3(-0.5, -0.5, 0.5),
                    vec3(-0.5, 0.5, -0.5),
                ),  # Left face
                (
                    vec3(-0.5, -0.5, 0.5),
                    vec3(-0.5, 0.5, 0.5),
                    vec3(-0.5, 0.5, -0.5),
                ),
                (
                    vec3(-0.5, 0.5, -0.5),
                    vec3(0.5, 0.5, 0.5),
                    vec3(0.5, 0.5, -0.5),
                ),  # Top face
                (
                    vec3(-0.5, 0.5, -0.5),
                    vec3(-0.5, 0.5, 0.5),
                    vec3(0.5, 0.5, 0.5),
                ),
                (
                    vec3(-0.5, -0.5, -0.5),
                    vec3(0.5, -0.5, -0.5),
                    vec3(0.5, -0.5, 0.5),
                ),  # Bottom face
                (
                    vec3(-0.5, -0.5, -0.5),
                    vec3(0.5, -0.5, 0.5),
                    vec3(-0.5, -0.5, 0.5),
                ),
                (
                    vec3(-0.5, -0.5, 0.5),
                    vec3(0.5, -0.5, 0.5),
                    vec3(-0.5, 0.5, 0.5),
                ),  # Back face
                (
                    vec3(0.5, -0.5, 0.5),
                    vec3(0.5, 0.5, 0.5),
                    vec3(-0.5, 0.5, 0.5),
                ),
                (
                    vec3(-0.5, -0.5, -0.5),
                    vec3(-0.5, 0.5, -0.5),
                    vec3(0.5, -0.5, -0.5),
                ),  # Front face
                (
                    vec3(0.5, -0.5, -0.5),
                    vec3(-0.5, 0.5, -0.5),
                    vec3(0.5, 0.5, -0.5),
                ),
            ],
            [  # Right face UVs
                (vec2(0.0, 0.0), vec2(0.0, 1.0), vec2(1.0, 0.0)),
                (vec2(1.0, 0.0), vec2(0.0, 1.0), vec2(1.0, 1.0)),
                # Left face UVs
                (vec2(1.0, 0.0), vec2(0.0, 0.0), vec2(1.0, 1.0)),
                (vec2(0.0, 0.0), vec2(0.0, 1.0), vec2(1.0, 1.0)),
                # Top face UVs
                (vec2(0.0, 0.0), vec2(1.0, 1.0), vec2(1.0, 0.0)),
                (vec2(0.0, 0.0), vec2(0.0, 1.0), vec2(1.0, 1.0)),
                # Bottom face UVs
                (vec2(0.0, 1.0), vec2(1.0, 1.0), vec2(1.0, 0.0)),
                (vec2(0.0, 1.0), vec2(1.0, 0.0), vec2(0.0, 0.0)),
                # Back face UVs
                (vec2(0.0, 0.0), vec2(1.0, 0.0), vec2(0.0, 1.0)),
                (vec2(1.0, 0.0), vec2(1.0, 1.0), vec2(0.0, 1.0)),
                # Front face UVs
                (vec2(1.0, 0.0), vec2(1.0, 1.0), vec2(0.0, 0.0)),
                (vec2(0.0, 0.0), vec2(1.0, 1.0), vec2(0.0, 1.0)),
            ],
            material,
            False,
        )
