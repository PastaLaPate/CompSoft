import math

from glm import vec2
from pyglm.glm import vec3

from compsoft.graphics.material import Material
from compsoft.scene.components.mesh import SimpleMeshComponent


class SimpleConeComponent(SimpleMeshComponent):
    def __init__(
        self,
        material: Material,
        radius: float = 0.5,
        height: float = 1.0,
        segments: int = 32,
    ) -> None:
        vertices = []
        uvs = []

        half_h = height / 2.0
        apex = vec3(0.0, half_h, 0.0)
        bot_center = vec3(0.0, -half_h, 0.0)

        for i in range(segments):
            theta0 = 2.0 * math.pi * i / segments
            theta1 = 2.0 * math.pi * (i + 1) / segments

            x0, z0 = radius * math.cos(theta0), radius * math.sin(theta0)
            x1, z1 = radius * math.cos(theta1), radius * math.sin(theta1)

            p0_bot = vec3(x0, -half_h, z0)
            p1_bot = vec3(x1, -half_h, z1)

            u0 = i / segments
            u1 = (i + 1) / segments
            uv0_bot = vec2(u0, 0.0)
            uv1_bot = vec2(u1, 0.0)
            uv_apex = vec2((u0 + u1) / 2.0, 1.0)

            vertices.append((p0_bot, apex, p1_bot))
            uvs.append((uv0_bot, uv_apex, uv1_bot))

            uv_center = vec2(0.5, 0.5)
            uv_p0 = vec2(
                0.5 + 0.5 * math.cos(theta0), 0.5 + 0.5 * math.sin(theta0)
            )
            uv_p1 = vec2(
                0.5 + 0.5 * math.cos(theta1), 0.5 + 0.5 * math.sin(theta1)
            )

            vertices.append(
                (
                    bot_center,
                    p0_bot,
                    p1_bot,
                )
            )
            uvs.append(
                (
                    uv_center,
                    uv_p0,
                    uv_p1,
                )
            )

        super().__init__(vertices, uvs, material, False)
