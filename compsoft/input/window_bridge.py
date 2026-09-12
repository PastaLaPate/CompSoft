from __future__ import annotations

from typing import TYPE_CHECKING

import glfw
from pyglm.glm import vec2

from compsoft.input.cursors import CursorMode, CursorShape
from compsoft.input.inputs import Inputs, TriggerMode
from compsoft.input.manager import InputManager

if TYPE_CHECKING:
    from glfw import (
        _GLFWwindowPointerT,  # Not available at runtime for some reason
    )


class WindowInputBridge:
    def __init__(self, glfw_window: _GLFWwindowPointerT, input_manager: InputManager):
        self.window = glfw_window
        self.input_mgr = input_manager
        self.input_mgr.controller = self
        self.pointer = input_manager.pointer

        glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)
        glfw.set_scroll_callback(self.window, self._scroll_callback)
        glfw.set_key_callback(self.window, self._key_callback)

        self.mouse_map = {
            glfw.MOUSE_BUTTON_LEFT: Inputs.LMB,
            glfw.MOUSE_BUTTON_MIDDLE: Inputs.MMB,
            glfw.MOUSE_BUTTON_RIGHT: Inputs.RMB,
            glfw.MOUSE_BUTTON_4: Inputs.MOUSE_4,
            glfw.MOUSE_BUTTON_5: Inputs.MOUSE_5,
        }

        # Maps GLFW/QT keycodes to standard us layout
        self._cursor_cache = {
            CursorShape.ARROW: glfw.create_standard_cursor(glfw.ARROW_CURSOR),
            CursorShape.IBEAM: glfw.create_standard_cursor(glfw.IBEAM_CURSOR),
            CursorShape.CROSSHAIR: glfw.create_standard_cursor(glfw.CROSSHAIR_CURSOR),
            CursorShape.HAND: glfw.create_standard_cursor(glfw.HAND_CURSOR),
            CursorShape.RESIZE_ALL: glfw.create_standard_cursor(glfw.RESIZE_ALL_CURSOR),
            CursorShape.GRAB: glfw.create_standard_cursor(glfw.HAND_CURSOR),
        }
        self.scancode_map: dict[int, Inputs] = self._build_scancode_map()

    def set_cursor_mode(self, mode: CursorMode):
        match mode:
            case CursorMode.NORMAL:
                glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            case CursorMode.HIDDEN:
                glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)
            case CursorMode.DISABLED:
                # Fixes the cursor not actually being disabled
                glfw.set_cursor(self.window, None)  # ty: ignore[invalid-argument-type]
                glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    def set_cursor_shape(self, shape: CursorShape) -> None:
        cursor = self._cursor_cache.get(shape)
        if cursor:
            glfw.set_cursor(self.window, cursor)

    def get_width(self) -> int:
        return glfw.get_window_size(self.window)[0]

    def get_height(self) -> int:
        return glfw.get_window_size(self.window)[1]

    def get_size(self) -> tuple[int, int]:
        return glfw.get_window_size(self.window)

    def _cursor_pos_callback(
        self, window: _GLFWwindowPointerT, xpos: float, ypos: float
    ) -> None:
        new_pos = vec2(xpos, ypos)

        if self.pointer.current_pos == vec2(0, 0):  # Frame has begun, start state:
            self.pointer.current_pos = new_pos
            self.pointer.last_pos = new_pos
            return

        # Accumulate over the frame...
        self.pointer.delta += new_pos - self.pointer.current_pos
        self.pointer.last_pos = self.pointer.current_pos
        self.pointer.current_pos = new_pos

    def _mouse_button_callback(
        self, window: _GLFWwindowPointerT, button: int, action: int, mods: int
    ) -> None:
        input_code = self.mouse_map.get(button)
        if not input_code:
            return

        trigger = TriggerMode.PRESSED if action == glfw.PRESS else TriggerMode.RELEASED
        self.input_mgr.handle_input_event(input_code, trigger)

    def _scroll_callback(
        self, window: _GLFWwindowPointerT, xoffset: float, yoffset: float
    ) -> None:
        self.pointer.scroll_delta = vec2(xoffset, yoffset)
        self.input_mgr.handle_input_event(
            Inputs.MOUSE_WHEEL, TriggerMode.AXIS_DELTA, yoffset
        )

    def _key_callback(
        self,
        window: _GLFWwindowPointerT,
        key: int,
        scancode: int,
        action: int,
        mods: int,
    ) -> None:
        input_code = self.scancode_map.get(scancode)
        if not input_code:
            return

        if action == glfw.PRESS:
            self.input_mgr.handle_input_event(input_code, TriggerMode.PRESSED)
        elif action == glfw.RELEASE:
            self.input_mgr.handle_input_event(input_code, TriggerMode.RELEASED)

    def _build_scancode_map(self) -> dict[int, Inputs]:
        key_map = {
            # Special Characters
            glfw.KEY_ESCAPE: Inputs.ESC,
            glfw.KEY_DELETE: Inputs.DEL,
            glfw.KEY_HOME: Inputs.HOME,
            glfw.KEY_END: Inputs.END,
            glfw.KEY_PAGE_UP: Inputs.PAGE_UP,
            glfw.KEY_PAGE_DOWN: Inputs.PAGE_DOWN,
            glfw.KEY_INSERT: Inputs.INSERT,
            glfw.KEY_ENTER: Inputs.ENT,
            glfw.KEY_BACKSPACE: Inputs.BCK_SPACE,
            glfw.KEY_SPACE: Inputs.SPACE,
            glfw.KEY_TAB: Inputs.TAB,
            glfw.KEY_CAPS_LOCK: Inputs.CAPS_LOCK,
            glfw.KEY_NUM_LOCK: Inputs.NUM_LOCK,
            glfw.KEY_SCROLL_LOCK: Inputs.SCROLL_LOCK,
            glfw.KEY_PRINT_SCREEN: Inputs.PRINT_SCREEN,
            glfw.KEY_PAUSE: Inputs.PAUSE,
            glfw.KEY_MENU: Inputs.MENU,
            # Modifiers
            glfw.KEY_RIGHT_CONTROL: Inputs.RIGHT_CONTROL,
            glfw.KEY_LEFT_CONTROL: Inputs.LEFT_CONTROL,
            glfw.KEY_RIGHT_SHIFT: Inputs.RIGHT_SHIFT,
            glfw.KEY_LEFT_SHIFT: Inputs.LEFT_SHIFT,
            glfw.KEY_RIGHT_ALT: Inputs.RIGHT_ALT,
            glfw.KEY_LEFT_ALT: Inputs.LEFT_ALT,
            glfw.KEY_LEFT_SUPER: Inputs.LEFT_SUPER,
            glfw.KEY_RIGHT_SUPER: Inputs.RIGHT_SUPER,
            # F keys
            glfw.KEY_F1: Inputs.F1,
            glfw.KEY_F2: Inputs.F2,
            glfw.KEY_F3: Inputs.F3,
            glfw.KEY_F4: Inputs.F4,
            glfw.KEY_F5: Inputs.F5,
            glfw.KEY_F6: Inputs.F6,
            glfw.KEY_F7: Inputs.F7,
            glfw.KEY_F8: Inputs.F8,
            glfw.KEY_F9: Inputs.F9,
            glfw.KEY_F10: Inputs.F10,
            glfw.KEY_F11: Inputs.F11,
            glfw.KEY_F12: Inputs.F12,
            # Arrows
            glfw.KEY_UP: Inputs.ARROW_UP,
            glfw.KEY_DOWN: Inputs.ARROW_DOWN,
            glfw.KEY_LEFT: Inputs.ARROW_LEFT,
            glfw.KEY_RIGHT: Inputs.ARROW_RIGHT,
            # Top Row Numbers
            glfw.KEY_0: Inputs.N_0,
            glfw.KEY_1: Inputs.N_1,
            glfw.KEY_2: Inputs.N_2,
            glfw.KEY_3: Inputs.N_3,
            glfw.KEY_4: Inputs.N_4,
            glfw.KEY_5: Inputs.N_5,
            glfw.KEY_6: Inputs.N_6,
            glfw.KEY_7: Inputs.N_7,
            glfw.KEY_8: Inputs.N_8,
            glfw.KEY_9: Inputs.N_9,
            # Numpad
            glfw.KEY_KP_0: Inputs.KP_0,
            glfw.KEY_KP_1: Inputs.KP_1,
            glfw.KEY_KP_2: Inputs.KP_2,
            glfw.KEY_KP_3: Inputs.KP_3,
            glfw.KEY_KP_4: Inputs.KP_4,
            glfw.KEY_KP_5: Inputs.KP_5,
            glfw.KEY_KP_6: Inputs.KP_6,
            glfw.KEY_KP_7: Inputs.KP_7,
            glfw.KEY_KP_8: Inputs.KP_8,
            glfw.KEY_KP_9: Inputs.KP_9,
            glfw.KEY_KP_DECIMAL: Inputs.KP_DECIMAL,
            glfw.KEY_KP_DIVIDE: Inputs.KP_DIVIDE,
            glfw.KEY_KP_MULTIPLY: Inputs.KP_MULTIPLY,
            glfw.KEY_KP_SUBTRACT: Inputs.KP_SUBTRACT,
            glfw.KEY_KP_ADD: Inputs.KP_ADD,
            glfw.KEY_KP_ENTER: Inputs.KP_ENTER,
            glfw.KEY_KP_EQUAL: Inputs.KP_EQUAL,
            # Symbols
            glfw.KEY_GRAVE_ACCENT: Inputs.GRAVE_ACCENT,
            glfw.KEY_MINUS: Inputs.MINUS,
            glfw.KEY_EQUAL: Inputs.EQUAL,
            glfw.KEY_LEFT_BRACKET: Inputs.LEFT_BRACKET,
            glfw.KEY_RIGHT_BRACKET: Inputs.RIGHT_BRACKET,
            glfw.KEY_SEMICOLON: Inputs.SEMICOLON,
            glfw.KEY_APOSTROPHE: Inputs.APOSTROPHE,
            glfw.KEY_COMMA: Inputs.COMMA,
            glfw.KEY_PERIOD: Inputs.PERIOD,
            glfw.KEY_SLASH: Inputs.SLASH,
            glfw.KEY_BACKSLASH: Inputs.BACK_SLASH,
            # Alphabet
            glfw.KEY_A: Inputs.A,
            glfw.KEY_B: Inputs.B,
            glfw.KEY_C: Inputs.C,
            glfw.KEY_D: Inputs.D,
            glfw.KEY_E: Inputs.E,
            glfw.KEY_F: Inputs.F,
            glfw.KEY_G: Inputs.G,
            glfw.KEY_H: Inputs.H,
            glfw.KEY_I: Inputs.I,
            glfw.KEY_J: Inputs.J,
            glfw.KEY_K: Inputs.K,
            glfw.KEY_L: Inputs.L,
            glfw.KEY_M: Inputs.M,
            glfw.KEY_N: Inputs.N,
            glfw.KEY_O: Inputs.O,
            glfw.KEY_P: Inputs.P,
            glfw.KEY_Q: Inputs.Q,
            glfw.KEY_R: Inputs.R,
            glfw.KEY_S: Inputs.S,
            glfw.KEY_T: Inputs.T,
            glfw.KEY_U: Inputs.U,
            glfw.KEY_V: Inputs.V,
            glfw.KEY_W: Inputs.W,
            glfw.KEY_X: Inputs.X,
            glfw.KEY_Y: Inputs.Y,
            glfw.KEY_Z: Inputs.Z,
        }

        mapping = {}
        for glfw_key, internal_input in key_map.items():
            scancode = glfw.get_key_scancode(glfw_key)
            if scancode != -1:
                mapping[scancode] = internal_input
        return mapping
