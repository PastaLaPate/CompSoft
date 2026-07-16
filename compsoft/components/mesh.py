from OpenGL.GL import (
    glGenVertexArrays,
    glBindVertexArray,
    GL_DYNAMIC_DRAW,
    GL_STATIC_DRAW,
    glGenBuffers,
    glBindBuffer,
    GL_ARRAY_BUFFER,
    glBufferData,
    GLfloat,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    GL_FLOAT,
    GL_FALSE,
    glBufferSubData,
    glDrawArrays,
    GL_TRIANGLES,
    glDeleteBuffers,
    glDeleteVertexArrays,
)
import random
from typing import cast
from pyglm.glm import mat4, vec3
import pyglm.glm as glm

from compsoft.component import RenderableComponent
from compsoft.material import Material


class SimpleMeshComponent(RenderableComponent):
    def __init__(
        self,
        triangles: list[tuple[vec3, vec3, vec3]],
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
        self.dynamic = dynamic
        self._mat = material

        # Generate random colors for each vertex (matching your original logic)
        self.colors: list[vec3] = [
            vec3(
                random.uniform(0, 1),
                random.uniform(0, 1),
                random.uniform(0, 1),
            )
            for _ in range(len(triangles) * 3)
        ]

        self._position = vec3(0, 0, 0)
        self._scale = vec3(1, 1, 1)
        self._rotation = vec3(0, 0, 0)

        self.dirty_matrix = True
        self.t_matrix = None

        # OpenGL IDs
        self.vao = 0
        self.vbo_vertices = 0
        self.vbo_colors = 0

    @property
    def triangles(self) -> list[tuple[vec3, vec3, vec3]]:
        return self._triangles

    @triangles.setter
    def triangles(self, triangles: list[tuple[vec3, vec3, vec3]]):
        self._triangles = triangles

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
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        usage = GL_DYNAMIC_DRAW if self.dynamic else GL_STATIC_DRAW

        # Vertex Buffer
        vertex_buffer_data = [
            val for t in self._triangles for c in t for val in (c.x, c.y, c.z)
        ]
        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(vertex_buffer_data) * 4,  # 4 bytes per float
            (GLfloat * len(vertex_buffer_data))(*vertex_buffer_data),
            usage,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # Color Buffer
        color_buffer_data = [
            val for c in self.colors for val in (c.x, c.y, c.z)
        ]
        self.vbo_colors = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(color_buffer_data) * 4,
            (GLfloat * len(color_buffer_data))(*color_buffer_data),
            usage,
        )
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBindVertexArray(0)

    def update(self):
        """Updates VRAM with new triangle or color data."""
        if not self.dynamic:
            print("Warning: Attempted to update a static mesh.")
            return

        # Update Vertices
        vertex_buffer_data = [
            val for t in self._triangles for c in t for val in (c.x, c.y, c.z)
        ]
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferSubData(
            GL_ARRAY_BUFFER,
            0,
            len(vertex_buffer_data) * 4,
            (GLfloat * len(vertex_buffer_data))(*vertex_buffer_data),
        )

        # Update Colors
        color_buffer_data = [
            val for c in self.colors for val in (c.x, c.y, c.z)
        ]
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glBufferSubData(
            GL_ARRAY_BUFFER,
            0,
            len(color_buffer_data) * 4,
            (GLfloat * len(color_buffer_data))(*color_buffer_data),
        )
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw(self, aspect_ratio: float, mvp: mat4):
        """Draws the mesh using its attached Material."""
        if self.vao == 0:
            return  # Prevent drawing before load() is called

        final_mvp = cast(mat4, mvp * self.get_transform_matrix())

        self._mat.use(final_mvp)

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
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])

        self.vbo_vertices = 0
        self.vbo_colors = 0
        self.vao = 0
