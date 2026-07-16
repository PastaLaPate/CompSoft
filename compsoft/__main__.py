import math
from typing import Tuple, cast
from glm import vec3
import pyglm.glm as glm

from OpenGL.GL.APPLE.vertex_program_evaluators import (
    glDisableVertexAttribAPPLE,
)
from OpenGL.GL import (
    GL_TRUE,
    glClear,
    GL_COLOR_BUFFER_BIT,
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    GL_ARRAY_BUFFER,
    glBufferData,
    GL_STATIC_DRAW,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    GL_FLOAT,
    GL_FALSE,
    glDrawArrays,
    GL_TRIANGLES,
    glDisableVertexAttribArray,
    GLfloat,
    glCreateShader,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    glShaderSource,
    glCompileShader,
    glCreateProgram,
    glLinkProgram,
    glAttachShader,
    glUseProgram,
    glGetUniformLocation,
    glUniformMatrix4fv,
    glEnable,
    GL_LESS,
    GL_DEPTH_TEST,
    glDepthFunc,
    GL_DEPTH_BUFFER_BIT,
)
import glfw
from pathlib import Path


class COLORS:
    RED = vec3(1, 0, 0)
    GREEN = vec3(0, 1, 0)
    BLUE = vec3(0, 0, 1)

    WHITE = vec3(1, 1, 1)
    BLACK = vec3(0, 0, 0)


def load_vertex_shader(path: Path):
    vertex_shader_id = glCreateShader(GL_VERTEX_SHADER)

    with open(path, mode="r") as f:
        lines = f.readlines()
        vertex_shader_content = "\n".join(lines)

    glShaderSource(vertex_shader_id, vertex_shader_content)
    glCompileShader(vertex_shader_id)
    return vertex_shader_id


def load_fragment_shader(path: Path):
    fragment_shader_id = glCreateShader(GL_FRAGMENT_SHADER)

    with open(path, mode="r") as f:
        lines = f.readlines()
        fragment_shader_content = "\n".join(lines)

    glShaderSource(fragment_shader_id, fragment_shader_content)
    glCompileShader(fragment_shader_id)
    return fragment_shader_id


def link_shaders(shaders):
    program_id = glCreateProgram()
    for shader in shaders:
        glAttachShader(program_id, shader)
    glLinkProgram(program_id)

    return program_id


class Camera:
    def __init__(self) -> None:
        self._pos = vec3(0, 0, 0)
        self._rot = vec3(0, 0, 0)

        self.fov = 90  # in degrees

        self.v_matrix = None
        self.dirty_matrix = True

    @classmethod
    def from_pos(cls, pos: vec3):
        i = cls()
        i.pos = pos
        return i

    @classmethod
    def from_rot(cls, rot: vec3):
        i = cls()
        i.rot = rot
        return i

    @classmethod
    def from_pos_rot(cls, pos: vec3, rot: vec3):
        i = cls()
        i.pos = pos
        i.rot = rot
        return i

    @property
    def pos(self) -> vec3:
        return self._pos

    @pos.setter
    def pos(self, pos: vec3):
        if not pos == self._pos:
            self.dirty_matrix = True
        self._pos = pos

    @property
    def rot(self) -> vec3:
        return self._rot

    @rot.setter
    def rot(self, rot: vec3):
        if not rot == self._rot:
            self.dirty_matrix = True
        self._rot = rot

    def look_at(self, target: glm.vec3):
        direction = target - self.pos

        if glm.length(direction) < 0.0001:
            return

        direction = glm.normalize(direction)

        pitch = glm.asin(direction.y)
        yaw = glm.atan(direction.z, direction.x)

        self.rot = glm.vec3(
            glm.degrees(pitch),
            glm.degrees(yaw),
            0.0,  # Roll (Z) is kept at 0 to keep the camera level with the horizon
        )

    def get_lookat_target(self) -> vec3:
        pitch = glm.radians(self.rot.x)
        yaw = glm.radians(self.rot.y)

        forward = vec3()
        # Some trigonometry shit
        forward.x = math.cos(pitch) * math.cos(yaw)
        forward.y = math.sin(pitch)
        forward.z = math.cos(pitch) * math.sin(yaw)

        forward = glm.normalize(forward)
        return self.pos + forward

    def get_view_matrix(self) -> glm.mat4x4:
        if self.v_matrix and not self.dirty_matrix:
            return self.v_matrix

        v = glm.lookAt(self.pos, self.get_lookat_target(), vec3(0, 1, 0))
        return v

    def get_projection_matrix(self) -> glm.mat4x4:
        p = glm.perspective(
            glm.radians(self.fov),
            4.0 / 3.0,  # Aspect Ratio
            0.1,  # Near clipping plane. Keep as big as possible, or you'll get precision issues.
            100,  # Far clipping plane. Keep as little as possible
        )
        return p


class SimpleMesh:
    def __init__(self, triangles: list[tuple[vec3, vec3, vec3]]) -> None:
        self.triangles = triangles
        self.vertex_array = glGenVertexArrays(1)

        self._position = vec3(0, 0, 0)
        self._scale = vec3(1, 1, 1)
        self._rotation = vec3(0, 0, 0)

        self.dirty_matrix = True
        self.t_matrix = None

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

    def load(self):
        glBindVertexArray(self.vertex_array)
        buffer_data = [
            x for t in self.triangles for c in t for x in [c.x, c.y, c.z]
        ]  # triple nested loop WCPGW
        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(buffer_data) * 4,
            (GLfloat * len(buffer_data))(*buffer_data),
            GL_STATIC_DRAW,
        )

    def get_transform_matrix(self) -> glm.mat4x4:
        if self.t_matrix and not self.dirty_matrix:
            return self.t_matrix
        identity = glm.mat4(1.0)

        quat = glm.quat(self.rotation)
        rot: glm.mat4x4 = glm.mat4_cast(quat)
        scale: glm.mat4x4 = glm.scale(identity, self.scale)
        translate: glm.mat4x4 = glm.translate(identity, self.position)
        m = cast(glm.mat4x4, translate * rot * scale)
        self.t_matrix = m
        self.dirty_matrix = False
        return m

    def draw(self, camera: Camera, program_id):

        mvp: glm.mat4x4 = cast(
            glm.mat4x4,
            camera.get_projection_matrix()
            * camera.get_view_matrix()
            * self.get_transform_matrix(),
        )

        matrix_id = glGetUniformLocation(program_id, "MVP")

        glUniformMatrix4fv(matrix_id, 1, GL_FALSE, glm.value_ptr(mvp))

        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glDrawArrays(GL_TRIANGLES, 0, 3 * len(self.triangles))
        glDisableVertexAttribArray(0)


class SimpleCube(SimpleMesh):
    def __init__(self) -> None:
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
            ]
        )


ROOT = Path(__file__).parent.parent


def main():
    print("Welcome...")
    glfw.init()
    glfw.window_hint(glfw.SAMPLES, 4)  # 4x antialiasing
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)  # We want OpenGL 3.3
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(
        glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE
    )  # To make MacOS happy; should not be needed
    glfw.window_hint(
        glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE
    )  # We don't want the old OpenGL

    window = glfw.create_window(1024, 768, "Tutorial 01", None, None)
    glfw.make_context_current(window)

    glfw.set_input_mode(window, glfw.STICKY_KEYS, GL_TRUE)

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)

    shaders = []

    shaders.append(load_vertex_shader(Path(ROOT / "shaders/vertex.glsl")))
    shaders.append(load_fragment_shader(Path(ROOT / "shaders/fragment.glsl")))

    program = link_shaders(shaders)

    cam = Camera.from_pos_rot(vec3(4, 3, -3), vec3(0, 0, 0))
    cam.look_at(vec3(0, 0, 0))

    objects = [SimpleCube()]

    for object in objects:
        object.load()
    while (
        glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS
        and glfw.window_should_close(window) == 0
    ):
        glClear(GL_COLOR_BUFFER_BIT)
        glClear(GL_DEPTH_BUFFER_BIT)

        glUseProgram(program)

        for object in objects:
            object.draw(cam, program)

        glfw.swap_buffers(window)
        glfw.poll_events()
