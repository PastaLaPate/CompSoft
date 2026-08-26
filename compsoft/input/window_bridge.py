import glfw
from glfw import _GLFWwindowPointerT

from compsoft.input.manager import InputManager


class WindowInputBridge:
    def __init__(
        self, glfw_window: _GLFWwindowPointerT, input_manager: InputManager
    ):
        self.window = glfw_window
        self.input_mgr = input_manager
        self.pointer = input_manager.pointer

        glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)
        glfw.set_mouse_button_callback(
            self.window, self._mouse_button_callback
        )
        glfw.set_scroll_callback(self.window, self._scroll_callback)
        glfw.set_key_callback(self.window, self._key_callback)

    def _cursor_pos_callback(
        self, window: _GLFWwindowPointerT, xpos: float, ypos: float
    ) -> None:
        pass

    def _mouse_button_callback(
        self, window: _GLFWwindowPointerT, button: int, action: int, mods: int
    ) -> None:
        pass

    def _scroll_callback(
        self, window: _GLFWwindowPointerT, xoffset: float, yoffset: float
    ) -> None:
        pass

    def _key_callback(
        self,
        window: _GLFWwindowPointerT,
        key: int,
        scancode: int,
        action: int,
        mods: int,
    ) -> None:
        pass
