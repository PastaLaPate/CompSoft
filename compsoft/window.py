from OpenGL.GL import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
import glfw


class Window:
    def __init__(self, w: int, h: int, title: str) -> None:
        self.__width = w
        self.__height = h
        self.__title = title
        self.__running = False

        self.dt: int = 0
        self.last_time: int = 0

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

        window = glfw.create_window(w, h, title, None, None)
        self.window = window
        glfw.make_context_current(window)

        glfw.set_input_mode(
            window, glfw.STICKY_KEYS, 0x1
        )  # == GL_TRUE but avoids putting opengl code here.

    @property
    def running(self) -> bool:
        return self.__running

    @property
    def size(self) -> tuple[int, int]:
        return (self.__width, self.__height)

    @size.setter
    def size(self, s: tuple[int, int]) -> None:
        self.__width = s[0]
        self.__height = s[1]
        glfw.set_window_size(self.window, s[0], s[1])

    @property
    def aspect_ratio(self) -> float:
        return self.__width / self.__height

    @property
    def title(self) -> str:
        return self.__title

    @title.setter
    def title(self, t: str):
        self.__title = t
        glfw.set_window_title(self.window, t)

    def exit(self):
        self.__running = False
        # glfw.destroy_window(self.window)

    def clear(self):
        current_time = glfw.get_time()
        self.dt = current_time - self.last_time
        self.last_time = current_time

        glClear(GL_COLOR_BUFFER_BIT)
        glClear(GL_DEPTH_BUFFER_BIT)

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def poll_events(self):
        glfw.poll_events()

    def key_pressed(self, key: int) -> bool:
        return glfw.get_key(self.window, key) == glfw.PRESS

    def rmb_pressed(self) -> bool:
        return (
            glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_RIGHT)
            == glfw.PRESS
        )

    def lmb_pressed(self) -> bool:
        return (
            glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_LEFT)
            == glfw.PRESS
        )

    def mmb_pressed(self) -> bool:
        return (
            glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_MIDDLE)
            == glfw.PRESS
        )
