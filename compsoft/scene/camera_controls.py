import math
from collections.abc import Callable

import glfw
from pyglm.glm import vec2

from compsoft.core.window import Window
from compsoft.scene.camera import Camera


class CameraControls:
    def __init__(
        self,
        camera: Camera,
        window: Window,
        speed: float = 5,
        mouse_speed: float = 0.05,
        drag_threshold: float = 4.0,
    ) -> None:
        self.camera = camera
        self.window = window

        self.speed = speed
        self.mouse_speed = mouse_speed
        self.drag_threshold = drag_threshold

        self.last_x, self.last_y = glfw.get_cursor_pos(self.window.window)

        self.lmb_click_listeners: list[Callable[[vec2], None]] = []
        self.lmb_was_pressed = False
        self.lmb_press_pos = (0.0, 0.0)
        self.is_dragging = False

        glfw.set_scroll_callback(self.window.window, self.scroll_callback)

    def add_lmb_click_listener(self, listener: Callable[[vec2], None]) -> None:
        self.lmb_click_listeners.append(listener)

    def enable_cursor(self):
        glfw.set_input_mode(
            self.window.window, glfw.CURSOR, glfw.CURSOR_NORMAL
        )

    def disable_cursor(self):
        glfw.set_input_mode(
            self.window.window, glfw.CURSOR, glfw.CURSOR_DISABLED
        )

    def scroll_callback(self, window, x_offset: float, y_offset: float):
        ctrl_pressed = self.window.key_pressed(
            glfw.KEY_LEFT_CONTROL
        ) or self.window.key_pressed(glfw.KEY_RIGHT_CONTROL)

        if ctrl_pressed:
            self.camera.fov = max(
                10, min(140, self.camera.fov - int(y_offset) * 3)
            )

            print(
                f"\r\033[KCamera FOV: {round(self.camera.fov, 1)}°",
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

    def update(self, dt: float):
        current_x, current_y = glfw.get_cursor_pos(self.window.window)

        dx = current_x - self.last_x
        dy = current_y - self.last_y

        self.last_x = current_x
        self.last_y = current_y

        dirty = False

        mmb_pressed = self.window.mmb_pressed()
        lmb_pressed = self.window.lmb_pressed()

        if mmb_pressed:
            self.disable_cursor()
            self.camera.pos += self.camera.right * (dx * self.mouse_speed)
            self.camera.pos -= self.camera.up * (dy * self.mouse_speed)
            dirty = True

        if lmb_pressed and (not mmb_pressed):
            if not self.lmb_was_pressed:
                self.lmb_was_pressed = True
                self.lmb_press_pos = (current_x, current_y)
                self.is_dragging = False

            dist = math.hypot(
                current_x - self.lmb_press_pos[0],
                current_y - self.lmb_press_pos[1],
            )

            if dist > self.drag_threshold:
                self.is_dragging = True

            if self.is_dragging:
                self.disable_cursor()
                self.camera.rot.y += dx * self.mouse_speed
                self.camera.rot.x -= dy * self.mouse_speed
                self.camera.rot.x = max(-89.0, min(89.0, self.camera.rot.x))
                dirty = True
        elif self.lmb_was_pressed:
            # Button was released this frame
            if not self.is_dragging:
                [
                    listener(vec2(self.lmb_press_pos))
                    for listener in self.lmb_click_listeners
                ]

            self.lmb_was_pressed = False
            self.is_dragging = False

        if not lmb_pressed and not mmb_pressed:
            self.enable_cursor()

        if self.window.key_pressed(glfw.KEY_W):
            self.camera.pos += self.camera.forward * dt * self.speed
            dirty = True
        if self.window.key_pressed(glfw.KEY_S):
            self.camera.pos -= self.camera.forward * dt * self.speed
            dirty = True
        if self.window.key_pressed(glfw.KEY_D):
            self.camera.pos += self.camera.right * dt * self.speed
            dirty = True
        if self.window.key_pressed(glfw.KEY_A):
            self.camera.pos -= self.camera.right * dt * self.speed
            dirty = True

        self.camera._dirty_matrix = dirty
