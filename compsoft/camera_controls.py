import glfw

from compsoft.camera import Camera
from compsoft.window import Window


class CameraControls:
    def __init__(
        self,
        camera: Camera,
        window: Window,
        speed: float = 5,
        mouse_speed: float = 0.05,
    ) -> None:
        self.camera = camera
        self.window = window

        self.speed = speed
        self.mouse_speed = mouse_speed

        self.last_x, self.last_y = glfw.get_cursor_pos(self.window.window)
        glfw.set_scroll_callback(self.window.window, self.scroll_callback)

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
                10, min(120, self.camera.fov - int(y_offset) * 3)
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

        if self.window.mmb_pressed():
            self.disable_cursor()
            self.camera.pos += self.camera.right * (dx * self.mouse_speed)
            self.camera.pos -= self.camera.up * (dy * self.mouse_speed)
            dirty = True
        elif self.window.lmb_pressed() and (not self.window.mmb_pressed()):
            self.disable_cursor()
            self.camera.rot.y += dx * self.mouse_speed
            self.camera.rot.x -= dy * self.mouse_speed
            self.camera.rot.x = max(-89.0, min(89.0, self.camera.rot.x))
            dirty = True
        else:
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
