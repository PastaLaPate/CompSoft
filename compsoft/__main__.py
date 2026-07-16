import random
import math
from typing import cast
from glm import vec3
import pyglm.glm as glm

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
    GL_DYNAMIC_DRAW,
    glBufferSubData,
    GL_CULL_FACE,
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

    def get_forward(self) -> vec3:
        pitch = glm.radians(self.rot.x)
        yaw = glm.radians(self.rot.y)

        forward = vec3()
        # Some trigonometry shit
        forward.x = math.cos(pitch) * math.cos(yaw)
        forward.y = math.sin(pitch)
        forward.z = math.cos(pitch) * math.sin(yaw)

        forward = glm.normalize(forward)
        return forward

    def get_right(self) -> vec3:
        return glm.normalize(glm.cross(self.get_forward(), vec3(0, 1, 0)))

    def get_up(self) -> glm.vec3:
        """Returns the camera's local Up vector (perpendicular to both Forward and Right)."""
        # Useful if you want a camera that can pitch up and down relative to its own tilt
        return glm.normalize(glm.cross(self.get_right(), self.get_forward()))

    def get_lookat_target(self) -> vec3:
        return self.pos + self.get_forward()

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


class Controls:
    def __init__(
        self, win, cam: Camera, speed: float = 5, mouse_speed: float = 0.05
    ) -> None:
        self.win = win
        self.cam = cam
        self.speed = speed
        self.mouse_speed = mouse_speed
        self.pan_speed = 0.05

        glfw.set_input_mode(self.win, glfw.CURSOR, glfw.CURSOR_DISABLED)

        self.last_x, self.last_y = glfw.get_cursor_pos(self.win)
        glfw.set_scroll_callback(self.win, self.scroll_callback)

    def scroll_callback(self, window, x_offset: float, y_offset: float):
        ctrl_pressed = (
            glfw.get_key(self.win, glfw.KEY_LEFT_CONTROL) == glfw.PRESS
            or glfw.get_key(self.win, glfw.KEY_RIGHT_CONTROL) == glfw.PRESS
        )

        if ctrl_pressed:
            self.cam.fov = max(10, min(120, self.cam.fov - int(y_offset) * 3))

            print(
                f"\r\033[KCamera FOV: {round(self.cam.fov, 1)}°",
                end="",
                flush=True,
            )
        else:
            self.speed = max(0.5, min(50.0, self.speed + y_offset * 0.5))

            print(
                f"\r\033[KMovement Speed: {round(self.speed, 2)}",
                end="",
                flush=True,
            )

    def control_pass(self, dt: float):
        # Rot
        current_x, current_y = glfw.get_cursor_pos(self.win)

        dx = current_x - self.last_x
        dy = current_y - self.last_y

        self.last_x = current_x
        self.last_y = current_y

        # Pan
        rmb_pressed = (
            glfw.get_mouse_button(self.win, glfw.MOUSE_BUTTON_RIGHT)
            == glfw.PRESS
        )
        mmb_pressed = (
            glfw.get_mouse_button(self.win, glfw.MOUSE_BUTTON_MIDDLE)
            == glfw.PRESS
        )

        if mmb_pressed:
            self.cam.pos += self.cam.get_right() * (dx * self.pan_speed)
            self.cam.pos -= self.cam.get_up() * (dy * self.pan_speed)

        elif rmb_pressed or (not mmb_pressed):
            # Default behavior: Look around if RMB is held or no other mouse buttons are down
            self.cam.rot.y += dx * self.mouse_speed
            self.cam.rot.x -= dy * self.mouse_speed
            self.cam.rot.x = max(-89.0, min(89.0, self.cam.rot.x))

        # Pos

        if glfw.get_key(self.win, glfw.KEY_W) == glfw.PRESS:
            self.cam.pos += self.cam.get_forward() * dt * self.speed
        if glfw.get_key(self.win, glfw.KEY_S) == glfw.PRESS:
            self.cam.pos -= self.cam.get_forward() * dt * self.speed
        if glfw.get_key(self.win, glfw.KEY_D) == glfw.PRESS:
            self.cam.pos += self.cam.get_right() * dt * self.speed
        if glfw.get_key(self.win, glfw.KEY_A) == glfw.PRESS:
            self.cam.pos -= self.cam.get_right() * dt * self.speed


class SimpleMesh:
    def __init__(
        self, triangles: list[tuple[vec3, vec3, vec3]], dynamic=False
    ) -> None:
        """Initialize a mesh of triangles.

        Args:
            triangles (list[tuple[vec3, vec3, vec3]]): List of a tuple of 3 vertices, all of the triangles.
            dynamic (bool, optional): Will the triangles or colors be updated ? Defaults to False.
        """

        self.dynamic = dynamic

        self.triangles = triangles
        self.vertex_array = glGenVertexArrays(1)

        self.colors: list[vec3] = [  # 1 color per vertex
            vec3(
                random.uniform(0, 1),
                random.uniform(0, 1),
                random.uniform(0, 1),
            )
            for i in range(len(triangles * 3))
        ]

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
        """### Loads all of the meshes info into VRAM.
        Note: If the colors for example are changed after loading it wont be taken into account. Needs to use update func.
        """
        glBindVertexArray(self.vertex_array)

        vertex_buffer_data = [
            x for t in self.triangles for c in t for x in [c.x, c.y, c.z]
        ]  # triple nested loop WCPGW
        self.vertex_buffer = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(vertex_buffer_data) * 4,
            (GLfloat * len(vertex_buffer_data))(*vertex_buffer_data),
            GL_STATIC_DRAW if not self.dynamic else GL_DYNAMIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        color_buffer_data = [x for t in self.colors for x in [t.x, t.y, t.z]]
        self.color_buffer = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(color_buffer_data) * 4,
            (GLfloat * len(color_buffer_data))(*color_buffer_data),
            GL_STATIC_DRAW if not self.dynamic else GL_DYNAMIC_DRAW,
        )
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(
            1,  # attribute. No particular reason for 1, but must match the layout in the shader.
            3,  # size
            GL_FLOAT,  # type
            GL_FALSE,  # normalized?
            0,  # stride
            None,  # array buffer offset
        )
        glBindVertexArray(0)

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

        glBindVertexArray(self.vertex_array)
        glDrawArrays(GL_TRIANGLES, 0, 3 * len(self.triangles))
        glBindVertexArray(0)

    def update_triangles(self, triangles: list[tuple[vec3, vec3, vec3]]):
        self.triangles = triangles
        vertex_buffer_data = [
            x for t in self.triangles for c in t for x in [c.x, c.y, c.z]
        ]  # triple nested loop WCPGW

        data_array = (GLfloat * len(vertex_buffer_data))(*vertex_buffer_data)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferSubData(
            GL_ARRAY_BUFFER,
            0,  # Start at 0, replace whole buffer
            len(vertex_buffer_data) * 4,  # Whole buffer size in bytes
            data_array,
        )
        glBindBuffer(GL_ARRAY_BUFFER, 0)  # Unbind

    def update_colors(self, colors: list[vec3]):
        self.colors = colors
        color_buffer_data = [x for t in self.colors for x in [t.x, t.y, t.z]]

        data_array = (GLfloat * len(color_buffer_data))(*color_buffer_data)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glBufferSubData(
            GL_ARRAY_BUFFER,
            0,  # Start at 0, replace whole buffer
            len(color_buffer_data) * 4,  # Whole buffer size in bytes
            data_array,
        )
        glBindBuffer(GL_ARRAY_BUFFER, 0)  # Unbind


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

    glEnable(GL_CULL_FACE)
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

    controls = Controls(window, cam)

    last_time = glfw.get_time()
    nb_frames = 0
    accumulated_time = 0.0

    while (
        glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS
        and glfw.window_should_close(window) == 0
    ):
        current_time = glfw.get_time()
        dt = current_time - last_time
        last_time = current_time

        glClear(GL_COLOR_BUFFER_BIT)
        glClear(GL_DEPTH_BUFFER_BIT)

        controls.control_pass(dt)

        glUseProgram(program)
        for object in objects:
            object.draw(cam, program)

        nb_frames += 1
        accumulated_time += dt
        if nb_frames > 10:
            avg_ms = (accumulated_time / nb_frames) * 1000.0
            print(f"\r\033[Ktook {round(avg_ms, 4)}ms", end="", flush=True)
            nb_frames = 0
            accumulated_time = 0.0
