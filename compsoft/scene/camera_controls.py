import math

from pyglm.glm import vec2

from compsoft.scene.camera import Camera


class CameraControls:
    def __init__(
        self,
        camera: Camera,
        base_speed: float = 5.0,
        speed_exponent: float = 0.0,
        mouse_speed: float = 0.05,
        min_exponent: float = -8.0,
        max_exponent: float = 8.0,
    ) -> None:
        self.camera = camera

        self.base_speed = base_speed
        self.speed_exponent = speed_exponent
        self.mouse_speed = mouse_speed
        self.min_exponent = min_exponent
        self.max_exponent = max_exponent

    def add_fov(self, delta: int):
        self.camera.fov = max(10, min(140, self.camera.fov + delta))
        self.camera._dirty_matrix = True

    def set_fov(self, fov: int):
        self.camera.fov = max(10, min(140, fov))
        self.camera._dirty_matrix = True

    @property
    def speed(self) -> float:
        """Calculates dynamic speed exponentially: base_speed * (2 ^ exponent)."""
        return self.base_speed * (2.0**self.speed_exponent)

    def add_speed(self, delta: float):
        """Adjusts the speed exponent linearly, resulting in exponential speed changes."""
        self.speed_exponent = max(
            self.min_exponent,
            min(self.max_exponent, self.speed_exponent + delta),
        )

    def set_speed(self, target_speed: float):
        """Sets explicit speed by computing the required exponent."""
        if target_speed <= 0:
            return
        ratio = target_speed / self.base_speed
        exponent = math.log2(ratio)
        self.speed_exponent = max(self.min_exponent, min(self.max_exponent, exponent))

    def pan_camera(self, delta: vec2):
        self.camera.pos += self.camera.right * (delta.x * self.mouse_speed)
        self.camera.pos -= self.camera.up * (delta.y * self.mouse_speed)
        self.camera._dirty_matrix = True

    def orbit_camera(self, delta: vec2):
        self.camera.rot.y += delta.x * self.mouse_speed
        self.camera.rot.x -= delta.y * self.mouse_speed
        self.camera.rot.x = max(-89.0, min(89.0, self.camera.rot.x))
        self.camera._dirty_matrix = True

    def forward(self, dt: float):
        self.camera.pos += self.camera.forward * dt * self.speed
        self.camera._dirty_matrix = True

    def backward(self, dt: float):
        self.camera.pos -= self.camera.forward * dt * self.speed
        self.camera._dirty_matrix = True

    def left(self, dt: float):
        self.camera.pos -= self.camera.right * dt * self.speed
        self.camera._dirty_matrix = True

    def right(self, dt: float):
        self.camera.pos += self.camera.right * dt * self.speed
        self.camera._dirty_matrix = True
