import math

from glm import vec2
from pyglm.glm import vec3

from compsoft.graphics.materials.material import Material
from compsoft.scene.components.mesh import SimpleMeshComponent


class SimpleSphereComponent(SimpleMeshComponent):
    def __init__(
        self,
        material: Material,
        radius: float = 0.5,
        stacks: int = 16,
        slices: int = 32,
    ) -> None:
        positions: list[tuple[vec3, vec3, vec3]] = []
        uvs: list[tuple[vec2, vec2, vec2]] = []

        grid_pos: list[list[vec3]] = []
        grid_uv: list[list[vec2]] = []

        for i in range(stacks + 1):
            v = i / stacks
            phi = v * math.pi

            row_pos: list[vec3] = []
            row_uv: list[vec2] = []

            for j in range(slices + 1):
                u = j / slices
                theta = u * 2.0 * math.pi  # longitude angle, 0 to 2*pi

                # spherical to cartesian coordinates conversion
                x = radius * math.sin(phi) * math.cos(theta)
                y = radius * math.cos(phi)
                z = radius * math.sin(phi) * math.sin(theta)

                row_pos.append(vec3(x, y, z))
                row_uv.append(vec2(u, 1.0 - v))

            grid_pos.append(row_pos)
            grid_uv.append(row_uv)

        for i in range(stacks):
            for j in range(slices):
                p00 = grid_pos[i][j]
                p10 = grid_pos[i + 1][j]
                p11 = grid_pos[i + 1][j + 1]
                p01 = grid_pos[i][j + 1]

                uv00 = grid_uv[i][j]
                uv10 = grid_uv[i + 1][j]
                uv11 = grid_uv[i + 1][j + 1]
                uv01 = grid_uv[i][j + 1]

                positions.append((p00, p11, p10))
                uvs.append((uv00, uv11, uv10))

                positions.append((p00, p01, p11))
                uvs.append((uv00, uv01, uv11))

        super().__init__(positions, uvs, material, False)
