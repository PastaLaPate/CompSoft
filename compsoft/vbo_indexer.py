from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from pyglm.glm import vec2, vec3


@dataclass(frozen=True)
class PackedVertex:
    position: vec3
    uv: vec2
    normal: vec3
    color: vec3


def get_similar_vertex_index_fast(
    packed: PackedVertex, vertex_to_out_index: Dict[PackedVertex, int]
) -> Tuple[bool, Optional[int]]:
    """
    Looks up a vertex in the dictionary.
    Returns a tuple: (True, index) if found, or (False, None) if not.
    """
    result = vertex_to_out_index.get(packed)

    if result is None:
        return False, None
    return True, result


def index_vbo(
    vertices: list[vec3],
    uvs: list[vec2],
    normals: list[vec3],
    colors: list[vec3],
    tangents: list[vec3],
    bitangents: list[vec3],
) -> Tuple[
    list[int],
    list[vec3],
    list[vec2],
    list[vec3],
    list[vec3],
    list[vec3],
    list[vec3],
]:  # indices, vertices, uvs, normals, colors, tangents, bitangents
    vertex_to_out_index: Dict[PackedVertex, int] = {}

    indices: list[int] = []
    out_vertices: list[vec3] = []
    out_uvs: list[vec2] = []
    out_normals: list[vec3] = []
    out_colors: list[vec3] = []
    out_tangents: list[vec3] = []
    out_bitangents: list[vec3] = []

    for i in range(len(vertices)):
        packed_vertex = PackedVertex(
            vertices[i], uvs[i], normals[i], colors[i]
        )
        found, index = get_similar_vertex_index_fast(
            packed_vertex, vertex_to_out_index
        )
        if found:
            indices.append(vertex_to_out_index[packed_vertex])

            out_tangents[vertex_to_out_index[packed_vertex]] += tangents[i]
            out_bitangents[vertex_to_out_index[packed_vertex]] += bitangents[i]
        else:
            out_vertices.append(vertices[i])
            out_uvs.append(uvs[i])
            out_normals.append(normals[i])
            out_colors.append(colors[i])
            out_tangents.append(tangents[i])
            out_bitangents.append(bitangents[i])
            new_idx = len(out_vertices) - 1
            indices.append(new_idx)
            vertex_to_out_index[packed_vertex] = new_idx

    return (
        indices,
        out_vertices,
        out_uvs,
        out_normals,
        out_colors,
        out_tangents,
        out_bitangents,
    )
