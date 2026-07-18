from typing import cast

import numpy as np
import pyglm.glm as glm
from OpenGL.constant import Constant
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_FALSE,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glBufferSubData,
    glDeleteBuffers,
    glDeleteVertexArrays,
    glDrawArrays,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glVertexAttribPointer,
)
from pyglm.glm import mat4, vec2, vec3

from compsoft.components.component import RenderableComponent
from compsoft.material import Material


class SimpleMeshComponent(RenderableComponent):
    DIRTY_NONE = 0b0000
    DIRTY_VERTICES = 0b0001
    DIRTY_COLORS = 0b0010
    DIRTY_UVS = 0b0100
    DIRTY_NORMALS = 0b1000
    DIRTY_ALL = 0b1111

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
        self.vbo_vertices = 0
        self.vbo_colors = 0
        self.vbo_uvs = 0
        self.vbo_normals = 0

        self.usage: Constant = (
            GL_DYNAMIC_DRAW if self.dynamic else GL_STATIC_DRAW
        )

        self.compute_normals()

    @property
    def triangles(self) -> list[tuple[vec3, vec3, vec3]]:
        return self._triangles

    @triangles.setter
    def triangles(self, triangles: list[tuple[vec3, vec3, vec3]]):
        self._triangles = triangles
        self._dirty_flags |= self.DIRTY_VERTICES
        self.compute_normals()

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

    def compute_normals(self):
        # For each triangle, calculate its normal, for each vertex, accumulate it in a map, after all triangles, normalize

        vertex_normal_map = {}
        for triangle in self.triangles:
            v1, v2, v3 = triangle
            edge_1 = v2 - v1
            edge_2 = v3 - v1
            face_normal = glm.cross(edge_1, edge_2)
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

                if glm.length(accumulated_normal) > 0.0001:
                    smoothed_normal = glm.normalize(accumulated_normal)
                else:
                    smoothed_normal = glm.vec3(
                        0.0, 1.0, 0.0
                    )  # Fallback up-vector

                self._normals.append(smoothed_normal)

        self._dirty_flags |= self.DIRTY_NORMALS

    def get_transform_matrix(self) -> glm.mat4x4:
        if self.t_matrix and not self.dirty_matrix:
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
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Vertex Buffer
        vertex_buffer_data = np.array(
            [[c.x, c.y, c.z] for t in self._triangles for c in t],
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
            [[c.x, c.y, c.z] for c in self._colors],
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
            [[vertex.x, vertex.y] for t in self.uvs for vertex in t],
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
            [[n.x, n.y, n.z] for n in self._normals],
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

        glBindVertexArray(0)

    def update(self):
        """Updates VRAM with new triangle or color data."""
        if not self.dynamic:
            print(
                "Warning: Attempted to update a static mesh. This can cause significant performance drop if done too frequently."
            )
        if self._dirty_flags == self.DIRTY_NONE:
            return

        if self._dirty_flags & self.DIRTY_VERTICES:
            vertex_buffer_data = np.array(
                [[c.x, c.y, c.z] for t in self._triangles for c in t],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
            # Orphanage
            glBufferData(
                GL_ARRAY_BUFFER, vertex_buffer_data.nbytes, None, self.usage
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                vertex_buffer_data.nbytes,
                vertex_buffer_data,
            )

        if self._dirty_flags & self.DIRTY_COLORS:
            color_buffer_data = np.array(
                [[c.x, c.y, c.z] for c in self._colors],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
            # Orphanage
            glBufferData(
                GL_ARRAY_BUFFER, color_buffer_data.nbytes, None, self.usage
            )
            glBufferSubData(
                GL_ARRAY_BUFFER, 0, color_buffer_data.nbytes, color_buffer_data
            )

        if self._dirty_flags & self.DIRTY_UVS:
            uv_buffer_data = np.array(
                [[vertex.x, vertex.y] for t in self.uvs for vertex in t],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_uvs)
            # Orphanage
            glBufferData(
                GL_ARRAY_BUFFER, uv_buffer_data.nbytes, None, self.usage
            )
            glBufferSubData(
                GL_ARRAY_BUFFER, 0, uv_buffer_data.nbytes, uv_buffer_data
            )

        # Update Normals
        if self._dirty_flags & self.DIRTY_NORMALS:
            normals_buffer_data = np.array(
                [[n.x, n.y, n.z] for n in self._normals],
                dtype=np.float32,
            ).ravel()
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
            # Orphanage
            glBufferData(
                GL_ARRAY_BUFFER, normals_buffer_data.nbytes, None, self.usage
            )
            glBufferSubData(
                GL_ARRAY_BUFFER,
                0,
                normals_buffer_data.nbytes,
                normals_buffer_data,
            )

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        self._dirty_flags = self.DIRTY_NONE

    def draw(self, aspect_ratio: float, mvp: mat4):
        """Draws the mesh using its attached Material. MVP is projection * view * each_parent_transform_matrix"""
        if self.vao == 0 or not self.parent or not self.parent.scene:
            return  # Prevent drawing before load() is called

        final_mvp = cast(mat4, mvp * self.get_transform_matrix())
        normal_matrix = cast(
            mat4,
            glm.mat4(
                glm.transpose(
                    glm.inverse(glm.mat3(self.get_transform_matrix()))
                )
            ),
        )

        self._mat.use(
            final_mvp,
            self.get_transform_matrix(),
            self.parent.scene.camera.get_view_matrix(),
            normal_matrix,
        )

        # draw the geometry
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 3 * len(self._triangles))
        glBindVertexArray(0)

    def unload(self):
        """Frees GPU resources when the component is destroyed."""
        if self.vbo_vertices:
            glDeleteBuffers(1, [self.vbo_vertices])
        if self.vbo_colors:
            glDeleteBuffers(1, [self.vbo_colors])
        if self.vbo_uvs:
            glDeleteBuffers(1, [self.vbo_uvs])
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])

        self.vbo_vertices = 0
        self.vbo_colors = 0
        self.vbo_uvs = 0
        self.vao = 0
