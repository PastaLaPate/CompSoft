from pyglm.glm import vec2

from compsoft.scene.camera import Camera


class CameraControls:
    def __init__(
        self,
        camera: Camera,
        speed: float = 5,
        mouse_speed: float = 0.05,
    ) -> None:
        self.camera = camera

        self.speed = speed
        self.mouse_speed = mouse_speed

    def add_fov(self, delta: int):
        self.camera.fov = max(10, min(140, self.camera.fov + delta))
        self.camera._dirty_matrix = True

    def set_fov(self, fov: int):
        self.camera.fov = max(10, min(140, fov))
        self.camera._dirty_matrix = True

    def add_speed(self, delta: float):
        self.speed = max(0.5, min(50.0, self.speed + delta))

    def set_speed(self, speed: float):
        self.speed = max(0.5, min(50.0, speed))

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
