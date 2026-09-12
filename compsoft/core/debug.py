import ctypes
from enum import IntFlag, auto

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_DEPTH_TEST,
    GL_DYNAMIC_DRAW,
    GL_FALSE,
    GL_FLOAT,
    GL_LINES,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glBufferSubData,
    glDisable,
    glDrawArrays,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glVertexAttribPointer,
)
from pyglm.glm import mat4, vec3

from compsoft.graphics.shader import Shader
from compsoft.resources.manager import resources


class DebugFlags(IntFlag):
    # Format as veritcal
    # fmt: off
    DEBUG_NONE = 0
    DEBUG_MESH_AABB = auto()
    DEBUG_SELECTION_RAYCAST = auto()
    DEBUG_RENDER_SHADOW_MAP = auto()
    DEBUG_FRAME_TIME = auto()

    DEBUG_ALL = DEBUG_MESH_AABB | DEBUG_SELECTION_RAYCAST
    # fmt: on


class Debug:
    MAX_LINES = 10_000

    def __init__(self) -> None:
        self._debug_vertices: list[tuple[vec3, vec3]] = []
        self._dirty_vertices = False

        # Just a container
        self.flags: DebugFlags = DebugFlags.DEBUG_NONE

        self.vao = 0
        self.vbo = 0

        self.shader = Shader(resources.get_shader_path("debug"))

    def add_flag(self, flag: DebugFlags):
        self.flags |= flag

    def has_flag(self, flag: DebugFlags):
        return bool(self.flags & flag)

    def remove_flag(self, flag: DebugFlags):
        self.flags &= ~flag

    def clear_flags(self):
        self.flags = DebugFlags.DEBUG_NONE

    def load(self):
        # Interleaved data
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER, Debug.MAX_LINES * 2 * 6 * 4, None, GL_DYNAMIC_DRAW
        )  # 2 vertices * (3 position floats + 3 color floats) * 4 bytes per float =

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(
            1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12)
        )  # Start = 3 * 4 bytes
        glEnableVertexAttribArray(1)

    def upload(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        datas = np.array(
            [
                [v[0].x, v[0].y, v[0].z, v[1].x, v[1].y, v[1].z]
                for v in self._debug_vertices
            ],
            dtype=np.float32,
        ).ravel()

        glBufferSubData(GL_ARRAY_BUFFER, 0, datas.nbytes, datas)

    def draw(self, view_proj: mat4):
        if self._dirty_vertices:
            self.upload()
            self._dirty_vertices = False

        self.shader.use()
        self.shader.set_uniform_matrix("uViewProj", view_proj)
        glDisable(GL_DEPTH_TEST)

        glBindVertexArray(self.vao)
        # glLineWidth(
        #    2.0
        # )  # will get ignored because why do a good opengl driver implementation when it can be trash ?
        # ..., 10 minutes later, even puts invalid value lol
        glDrawArrays(GL_LINES, 0, len(self._debug_vertices))
        glEnable(GL_DEPTH_TEST)

    def add_line(self, p0: vec3, p1: vec3, color: vec3 | None = None):
        color = color if color is not None else vec3(1, 1, 1)
        self._debug_vertices.extend([(p0, color), (p1, color)])
        if len(self._debug_vertices) > Debug.MAX_LINES * 2:
            self._debug_vertices = self._debug_vertices[: Debug.MAX_LINES * 2]
        self._dirty_vertices = True

    def add_box(self, mins: vec3, maxs: vec3, color: vec3 | None = None):
        corners = [
            vec3(mins.x, mins.y, mins.z),
            vec3(maxs.x, mins.y, mins.z),
            vec3(maxs.x, maxs.y, mins.z),
            vec3(mins.x, maxs.y, mins.z),
            vec3(mins.x, mins.y, maxs.z),
            vec3(maxs.x, mins.y, maxs.z),
            vec3(maxs.x, maxs.y, maxs.z),
            vec3(mins.x, maxs.y, maxs.z),
        ]
        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),  # bottom
            (4, 5),
            (5, 6),
            (6, 7),
            (7, 4),  # top
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7),
        ]  # verticals
        for a, b in edges:
            self.add_line(corners[a], corners[b], color)

    def add_box_centered(
        self, center: vec3, extent: vec3, color: vec3 | None = None
    ):
        self.add_box(center - extent, center + extent, color)

    def clear(self):
        self._debug_vertices.clear()
        self._dirty_vertices = True
