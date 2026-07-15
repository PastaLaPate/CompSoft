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
)
import glfw
from pathlib import Path


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

    shaders = []

    shaders.append(load_vertex_shader(Path(ROOT / "shaders/vertex.glsl")))
    shaders.append(load_fragment_shader(Path(ROOT / "shaders/fragment.glsl")))

    program = link_shaders(shaders)

    vertex = glGenVertexArrays(1)
    glBindVertexArray(vertex)

    buffer_data = [
        -1.0,
        -1.0,
        0.0,
        1.0,
        -1.0,
        0.0,
        0.0,
        1.0,
        0.0,
    ]

    vertex_buffer = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
    glBufferData(
        GL_ARRAY_BUFFER,
        len(buffer_data) * 4,
        (GLfloat * len(buffer_data))(*buffer_data),
        GL_STATIC_DRAW,
    )

    while (
        glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS
        and glfw.window_should_close(window) == 0
    ):
        glClear(GL_COLOR_BUFFER_BIT)

        glUseProgram(program)

        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glDisableVertexAttribArray(0)

        glfw.swap_buffers(window)
        glfw.poll_events()
