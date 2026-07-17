from pathlib import Path

import trimesh
from glm import vec2, vec3

from compsoft.components.mesh import SimpleMeshComponent
from compsoft.material import Material


class ModelMeshComponent(SimpleMeshComponent):
    def __init__(self, path: Path, material: Material) -> None:
        mesh = trimesh.load_mesh(path)
        trimesh.repair.fix_normals(mesh)

        uv_array = getattr(mesh.visual, "uv", None)
        has_uvs = uv_array is not None

        triangles_output = []
        uvs_output = []

        for face in mesh.faces:
            v0 = vec3(*mesh.vertices[face[0]])
            v1 = vec3(*mesh.vertices[face[1]])
            v2 = vec3(*mesh.vertices[face[2]])
            triangles_output.append((v0, v1, v2))

            if has_uvs:
                uv0 = vec2(*mesh.visual.uv[face[0]])  # type: ignore
                uv1 = vec2(*mesh.visual.uv[face[1]])  # type: ignore
                uv2 = vec2(*mesh.visual.uv[face[2]])  # type: ignore
                uvs_output.append((uv0, uv1, uv2))
            else:
                # fallback
                uvs_output.append(
                    (vec2(0.0, 0.0), vec2(0.0, 0.0), vec2(0.0, 0.0))
                )

        super().__init__(
            triangles=triangles_output,
            uvs=uvs_output,
            material=material,
            dynamic=False,
        )
