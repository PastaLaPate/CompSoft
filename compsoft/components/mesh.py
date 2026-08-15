from typing import cast

import numpy as np
import pyglm.glm as glm
from OpenGL.constant import Constant
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FALSE,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glBufferSubData,
    glDeleteBuffers,
    glDeleteVertexArrays,
    glDrawElements,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glVertexAttribPointer,
)
from pyglm.glm import mat4, vec2, vec3

from compsoft.components.component import RenderableComponent
from compsoft.material import Material
from compsoft.vbo_indexer import index_vbo


class SimpleMeshComponent(RenderableComponent):
    # Format as veritcal
    # fmt: off
    DIRTY_NONE     = 0b00000
    DIRTY_VERTICES = 0b10000
    DIRTY_COLORS   = 0b01000
    DIRTY_UVS      = 0b00100
    DIRTY_NORMALS  = 0b00010
    DIRTY_TOPOLOGY = 0b00001
    DIRTY_ALL      = 0b11111
    # fmt: on

    def __init__(
        self,
        triangles: list[tuple[vec3, vec3, vec3]],
        uvs: list[tuple[vec2, vec2, vec2]],
        material: Material,
        dynamic=False,
    ) -> None:
        """Initialize a mesh of triangles.

        Args:
            triangles (list[tuple[vec3, vec3, vec3]]): List of a tuple of 3 vertices.
            material (Material): The shader material bundle.
            dynamic (bool, optional): Will the triangles or colors be updated? Defaults to False.
        """
        self._triangles = triangles
        self._colors: list[vec3] = [  # Default white vertex color
            vec3(1, 1, 1) for _ in range(len(triangles) * 3)
        ]
        self._uvs = uvs
        self._normals = []
        self._tangents = []

        self._mat = material
        self._mat.bind_properties()
        self.dynamic = dynamic

        self._position = vec3(0, 0, 0)
        self._scale = vec3(1, 1, 1)
        self._rotation = vec3(0, 0, 0)

        self._dirty_flags = self.DIRTY_NONE
        self.dirty_matrix = True
        self.t_matrix = None

        # OpenGL IDs
        self.vao = 0
        self.ebo = 0
        self.vbo_vertices = 0
        self.vbo_colors = 0
        self.vbo_uvs = 0
        self.vbo_normals = 0
        self.vbo_tangents = 0

        # VBO Indexed
        self.index_count = 0
        self._indexed_triangles: list[int] = []
        self._indexed_vertices: list[vec3] = []
        self._reverse_vbo_index_lookup: list[
            int
        ] = []  # VBO Index -> idx of first corner of corresponding triangle, get the color of first triangle of index n self._colors[self._reverse_vbo_index_lookup[n]], as its color is the same as the other (bcs it got merged) all vertices who use index n have this color

        self.usage: Constant = (
            GL_DYNAMIC_DRAW if self.dynamic else GL_STATIC_DRAW
        )

        self.compute_normals()
        self.compute_tangent_basis()

    @property
    def triangles(self) -> list[tuple[vec3, vec3, vec3]]:
        return self._triangles

    @triangles.setter
    def triangles(self, triangles: list[tuple[vec3, vec3, vec3]]):
        self._triangles = triangles
        self._dirty_flags |= self.DIRTY_VERTICES
        if self.check_topology_change(
            triangles, self._indexed_triangles, self._indexed_vertices
        ):
            self._dirty_flags |= self.DIRTY_TOPOLOGY
        self.compute_normals()
        self.compute_tangent_basis()

    @property
    def colors(self) -> list[vec3]:
        return self._colors

    @colors.setter
    def colors(self, colors: list[vec3]):
        self._colors = colors
        self._dirty_flags |= self.DIRTY_COLORS

    @property
    def uvs(self) -> list[tuple[vec2, vec2, vec2]]:
        return self._uvs

    @uvs.setter
    def uvs(self, uvs: list[tuple[vec2, vec2, vec2]]):
        self._uvs = uvs
        self._dirty_flags |= self.DIRTY_UVS

    @property
    def material(self) -> Material:
        return self._mat

    @material.setter
    def material(self, mat: Material):
        self._mat = mat

    @property
    def position(self) -> vec3:
        return self._position

    @position.setter
    def position(self, x: vec3):
        if not x == self._position:
            self.dirty_matrix = True
        self._position = x

    @property
    def scale(self) -> vec3:
        return self._scale

    @scale.setter
    def scale(self, x: vec3):
        if not x == self._scale:
            self.dirty_matrix = True
        self._scale = x

    @property
    def rotation(self) -> vec3:
        return self._rotation

    @rotation.setter
    def rotation(self, x: vec3):
        if not x == self._rotation:
            self.dirty_matrix = True
        self._rotation = x

    def update(self):
        pass

    def check_topology_change(
        self,
        new_triangles: list[tuple[vec3, vec3, vec3]],
        indices: list[int],
        vertices: list[vec3],
        eps: float = 1e-6,
    ) -> bool:
        # Pass 1: size change?
        if len(indices) != len(new_triangles) * 3:
            return True

        # Pass 2: check vertex split
        new_vertices: list[None | vec3] = [None] * len(vertices)

        for corner_idx, vertex_idx in enumerate(indices):
            t_idx = corner_idx // 3
            t_vert_idx = corner_idx % 3
            new_vert_pos = new_triangles[t_idx][t_vert_idx]

            if new_vertices[vertex_idx] is None:
                new_vertices[vertex_idx] = new_vert_pos
            elif (
                new_vert_pos != new_vertices[vertex_idx]
            ):  # Two vertices before joined are now split
                return True

        # Pass 3: check if two same positions appear in new vertices, if yes, means two vertices are now merged

        def key(v: vec3):  # For float accuracy
            return (round(v.x / eps), round(v.y / eps), round(v.z / eps))

        seen_pos: set[vec3] = set()
        for pos in new_vertices:
            if pos:
                k = key(pos)
                if k in seen_pos:
                    return True
                seen_pos.add(pos)

        return False

    def compute_normals(self):
        # For each triangle, calculate its normal, for each vertex, accumulate it in a map, after all triangles, normalize

        vertex_normal_map = {}
        for triangle in self.triangles:
            v1, v2, v3 = triangle
            edge_1 = v2 - v1
            edge_2 = v3 - v1
            face_normal = glm.cross(edge_1, edge_2)

            if glm.length(face_normal) > 1e-8:
                face_normal = glm.normalize(face_normal)

            for v in (v1, v2, v3):
                key = (v.x, v.y, v.z)
                if key not in vertex_normal_map:
                    vertex_normal_map[key] = glm.vec3(0.0)
                vertex_normal_map[key] += face_normal

        self._normals = []
        for triangle in self._triangles:
            for v in triangle:
                key = (v.x, v.y, v.z)
                accumulated_normal = vertex_normal_map[key]
                if glm.length(accumulated_normal) > 1e-8:
                    smoothed_normal = glm.normalize(accumulated_normal)
                else:
                    smoothed_normal = glm.vec3(0.0, 1.0, 0.0)
                self._normals.append(smoothed_normal)

        self._dirty_flags |= self.DIRTY_NORMALS

    def compute_tangent_basis(self) -> None:
        if min(len(self.triangles), len(self.uvs), len(self._normals)) == 0:
            return

        tangents = []

        for i in range(len(self.triangles)):
            v0, v1, v2 = self.triangles[i]

            uv0, uv1, uv2 = self.uvs[i]

            delta_pos_1 = v1 - v0
            delta_pos_2 = v2 - v0

            delta_uv_1 = uv1 - uv0
            delta_uv_2 = uv2 - uv0

            det = delta_uv_1.x * delta_uv_2.y - delta_uv_1.y * delta_uv_2.x

            if abs(det) > 1e-6:
                r = 1.0 / det
                tangent = (
                    delta_pos_1 * delta_uv_2.y - delta_pos_2 * delta_uv_1.y
                ) * r
            else:
                tangent = vec3(1.0, 0.0, 0.0)

            for v_idx in [
                i * 3,
                i * 3 + 1,
                i * 3 + 2,
            ]:
                n = self._normals[v_idx]
                tangent = glm.normalize(tangent - glm.dot(tangent, n) * n)

                tangents.append(tangent)

        self._tangents = tangents

    def get_transform_matrix(self) -> glm.mat4x4:
        if self.t_matrix is not None and not self.dirty_matrix:
            return self.t_matrix

        identity = glm.mat4(1.0)

        quat = glm.quat(glm.radians(self.rotation))
        rot: glm.mat4x4 = glm.mat4_cast(quat)
        scale: glm.mat4x4 = glm.scale(identity, self.scale)
        translate: glm.mat4x4 = glm.translate(identity, self.position)

        m = cast(glm.mat4x4, translate * rot * scale)
        self.t_matrix = m
        self.dirty_matrix = False
        return m

    def load(self):
        """Loads all of the meshes info into VRAM."""
        if len(self.triangles) != len(self.uvs) or (
            len(self.triangles) * 3
        ) != len(self._colors):
            raise ValueError(
                f"Mesh data mismatch! Triangles: {len(self.triangles)}, "
                f"UVs: {len(self.uvs)}, Vertex Colors: {len(self._colors)}"
            )

        (
            indices,
            vertices,
            uvs,
            normals,
            colors,
            tangents,
            reverse_vbo_index_lookup,
        ) = index_vbo(
            [vertice for t in self._triangles for vertice in t],
            [uv for t_uv in self._uvs for uv in t_uv],
            self._normals,
            self._colors,
            self._tangents,
        )

        self.index_count = len(indices)
        self._indexed_triangles = indices
        self._indexed_vertices = vertices
        self._reverse_vbo_index_lookup = reverse_vbo_index_lookup

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        index_buffer_data = np.array(indices, dtype=np.uint32)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            index_buffer_data.nbytes,
            index_buffer_data,
            self.usage,
        )

        # Vertex Buffer
        vertex_buffer_data = np.array(
            [[v.x, v.y, v.z] for v in vertices],
            dtype=np.float32,
        ).ravel()

        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)

        glBufferData(
            GL_ARRAY_BUFFER,
            vertex_buffer_data.nbytes,  # 4 bytes per float
            vertex_buffer_data,
            self.usage,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # Color Buffer
        color_buffer_data = np.array(
            [[c.x, c.y, c.z] for c in colors],
            dtype=np.float32,
        ).ravel()
        self.vbo_colors = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glBufferData(
            GL_ARRAY_BUFFER,
            color_buffer_data.nbytes,
            color_buffer_data,
            self.usage,
        )
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

        # UVs Buffer
        uv_buffer_data = np.array(
            [[vertex.x, vertex.y] for vertex in uvs],
            dtype=np.float32,
        ).ravel()
        self.vbo_uvs = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_uvs)
        glBufferData(
            GL_ARRAY_BUFFER,
            uv_buffer_data.nbytes,
            uv_buffer_data,
            self.usage,
        )
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)

        normals_buffer_data = np.array(
            [[n.x, n.y, n.z] for n in normals],
            dtype=np.float32,
        ).ravel()
        self.vbo_normals = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glBufferData(
            GL_ARRAY_BUFFER,
            normals_buffer_data.nbytes,
            normals_buffer_data,
            self.usage,
        )
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 0, None)

        tangents_buffer_data = np.array(
            [[t.x, t.y, t.z] for t in tangents], dtype=np.float32
        ).ravel()
        self.vbo_tangents = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_tangents)
        glBufferData(
            GL_ARRAY_BUFFER,
            tangents_buffer_data.nbytes,
            tangents_buffer_data,
            self.usage,
        )
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBindVertexArray(0)

    def update_mesh(self):
        """Updates VRAM with new triangle or color data."""
        if not self.dynamic:
            print(
                "Warning: Attempted to update a static mesh. This can cause significant performance drop if done too frequently."
            )

        if len(self.triangles) != len(self.uvs) or (
            len(self.triangles) * 3
        ) != len(self._colors):
            raise ValueError(
                f"Mesh data mismatch! Triangles: {len(self.triangles)}, "
                f"UVs: {len(self.uvs)}, Vertex Colors: {len(self._colors)}"
            )

        if self._dirty_flags == self.DIRTY_NONE:
            return

        if self._dirty_flags & self.DIRTY_TOPOLOGY:
            (
                indices,
                vertices,
                uvs,
                normals,
                colors,
                tangents,
                reverse_vbo_index_lookup,
            ) = index_vbo(
                [vertice for t in self._triangles for vertice in t],
                [uv for t_uv in self._uvs for uv in t_uv],
                self._normals,
                self._colors,
                self._tangents,
            )
            self.index_count = len(indices)
            self._indexed_triangles = indices
            self._indexed_vertices = vertices
            self._reverse_vbo_index_lookup = reverse_vbo_index_lookup

            index_buffer_data = np.array(indices, dtype=np.uint32)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(
                GL_ELEMENT_ARRAY_BUFFER,
                index_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ELEMENT_ARRAY_BUFFER,
                0,
                index_buffer_data.nbytes,
                index_buffer_data,
            )

            vertex_buffer_data = np.array(
                [[v.x, v.y, v.z] for v in vertices],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
            glBufferData(
                GL_ARRAY_BUFFER,
                vertex_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                vertex_buffer_data.nbytes,  # 4 bytes per float
                vertex_buffer_data,
            )

            color_buffer_data = np.array(
                [[c.x, c.y, c.z] for c in colors],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
            glBufferData(
                GL_ARRAY_BUFFER,
                color_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER, 0, color_buffer_data.nbytes, color_buffer_data
            )

            uv_buffer_data = np.array(
                [[vertex.x, vertex.y] for vertex in uvs],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_uvs)
            glBufferData(
                GL_ARRAY_BUFFER,
                uv_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER, 0, uv_buffer_data.nbytes, uv_buffer_data
            )

            normals_buffer_data = np.array(
                [[n.x, n.y, n.z] for n in normals],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
            glBufferData(
                GL_ARRAY_BUFFER,
                normals_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                normals_buffer_data.nbytes,
                normals_buffer_data,
            )

            tangents_buffer_data = np.array(
                [[t.x, t.y, t.z] for t in tangents], dtype=np.float32
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_tangents)
            glBufferData(
                GL_ARRAY_BUFFER,
                tangents_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                tangents_buffer_data.nbytes,
                tangents_buffer_data,
            )

            self._dirty_flags = self.DIRTY_NONE  # Because by setting topology we also sent other variables (assuming they must have been changed too)
            return

        if self._dirty_flags & self.DIRTY_VERTICES:
            # No topology change, only update vertices, normals & tangents
            raw_vertices = [vertice for t in self._triangles for vertice in t]
            vertices = [
                raw_vertices[raw_idx]
                for raw_idx in self._reverse_vbo_index_lookup
            ]
            normals = [
                self._normals[raw_idx]
                for raw_idx in self._reverse_vbo_index_lookup
            ]
            tangents = [
                self._tangents[raw_idx]
                for raw_idx in self._reverse_vbo_index_lookup
            ]
            self._indexed_vertices = vertices

            vertex_buffer_data = np.array(
                [[v.x, v.y, v.z] for v in vertices],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
            glBufferData(
                GL_ARRAY_BUFFER,
                vertex_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                vertex_buffer_data.nbytes,  # 4 bytes per float
                vertex_buffer_data,
            )

            normals_buffer_data = np.array(
                [[n.x, n.y, n.z] for n in normals],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
            glBufferData(
                GL_ARRAY_BUFFER,
                normals_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                normals_buffer_data.nbytes,
                normals_buffer_data,
            )

            tangents_buffer_data = np.array(
                [[t.x, t.y, t.z] for t in tangents], dtype=np.float32
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_tangents)
            glBufferData(
                GL_ARRAY_BUFFER,
                tangents_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                tangents_buffer_data.nbytes,
                tangents_buffer_data,
            )

        if self._dirty_flags & self.DIRTY_COLORS:
            colors = [
                self._colors[raw_idx]
                for raw_idx in self._reverse_vbo_index_lookup
            ]

            color_buffer_data = np.array(
                [[c.x, c.y, c.z] for c in colors],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
            glBufferData(
                GL_ARRAY_BUFFER,
                color_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER, 0, color_buffer_data.nbytes, color_buffer_data
            )

        if self._dirty_flags & self.DIRTY_UVS:
            raw_uvs = [uv for uvs in self._uvs for uv in uvs]
            uvs = [
                raw_uvs[raw_idx] for raw_idx in self._reverse_vbo_index_lookup
            ]

            uv_buffer_data = np.array(
                [[vertex.x, vertex.y] for vertex in uvs],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_uvs)
            glBufferData(
                GL_ARRAY_BUFFER,
                uv_buffer_data.nbytes,
                None,
                self.usage,
            )
            glBufferSubData(
                GL_ARRAY_BUFFER, 0, uv_buffer_data.nbytes, uv_buffer_data
            )

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        self._dirty_flags = self.DIRTY_NONE

    def _sync_buffer(self, buffer_id: int, target: Constant, data: np.ndarray):
        glBindBuffer(target, buffer_id)
        glBufferData(buffer_id, data.nbytes, None, self.usage)
        glBufferSubData(buffer_id, 0, data.nbytes, data)

    def draw(self, aspect_ratio: float, world_model_matrix: mat4):
        """Draws the mesh using its attached Material. MVP is projection * view * each_parent_transform_matrix"""
        if (
            self.vao == 0
            or self.ebo == 0
            or not self.parent
            or not self.parent.scene
        ):
            return  # Prevent drawing before load() is called

        world_model_matrix = cast(
            mat4, world_model_matrix * self.get_transform_matrix()
        )
        normal_matrix = cast(
            mat4,
            glm.mat4(glm.transpose(glm.inverse(glm.mat3(world_model_matrix)))),
        )

        P = self.parent.scene.camera.get_projection_matrix(aspect_ratio)
        V = self.parent.scene.camera.get_view_matrix()

        final_mvp = cast(
            mat4,
            P * V * world_model_matrix,
        )

        self._mat.use(
            final_mvp,
            world_model_matrix,
            V,
            normal_matrix,
            self.parent.scene.camera.pos,
        )

        # draw the geometry
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def unload(self):
        """Frees GPU vram when the component is destroyed."""
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])

        to_delete = [
            b
            for b in (
                self.vbo_vertices,
                self.vbo_colors,
                self.vbo_uvs,
                self.vbo_normals,
                self.vbo_tangents,
                self.ebo,
            )
            if b
        ]

        if to_delete:
            glDeleteBuffers(len(to_delete), to_delete)

        self.vbo_vertices = 0
        self.vbo_colors = 0
        self.vbo_uvs = 0
        self.vbo_normals = 0
        self.vbo_tangents = 0
        self.vao = 0
        self.ebo = 0
