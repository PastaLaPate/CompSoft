from collections import deque
from typing import Callable

import glfw
from pyglm.glm import vec3

from compsoft.core.window import Window
from compsoft.graphics.frame_buffer import FrameBuffer
from compsoft.graphics.screen_quad import ScreenQuad
from compsoft.resources.manager import resources
from compsoft.scene.camera import Camera
from compsoft.scene.camera_controls import CameraControls
from compsoft.scene.scene import Scene


class Engine:
    def __init__(self) -> None:

        self.prerender_listeners: list[Callable[[float, float], None]] = []

        self.window = Window(800, 600, "CompSoft")
        self.cam = Camera(vec3(0, 0, 0))
        self.scene = Scene(self.cam)
        self.cam_controls = CameraControls(self.cam, self.window)
        self.fb = FrameBuffer(self.window.size[0], self.window.size[1])
        sq_shader_pair = resources.get_shader_path("framebuffer")
        self.sq = ScreenQuad(sq_shader_pair.vertex, sq_shader_pair.fragment)
        self.window.add_window_resize_listener(self.fb._on_window_size_changed)

    def _add_prerender_listener(
        self, listener: Callable[[float, float], None]
    ):
        self.prerender_listeners.append(listener)

    def start(self) -> None:
        frame_times = deque(maxlen=1500)
        t = 0
        while (
            not self.window.key_pressed(glfw.KEY_ESCAPE)
            and not self.window.should_close()
        ):
            self.window.clear()

            # Track time in ms
            dt_ms = self.window.dt * 1000
            frame_times.append(dt_ms)

            # Calculate metrics
            avg_ms = sum(frame_times) / len(frame_times)
            fps = 1000.0 / avg_ms

            # Goofy huh
            print(f"\x1b[1K\r{avg_ms:6.2f} ms | {fps:7.1f} FPS", end="")

            self.cam_controls.update(self.window.dt)

            t += self.window.dt * 100
            [
                listener(t, self.window.dt)
                for listener in self.prerender_listeners
            ]
            self.fb.bind()
            self.scene.render(self.window.aspect_ratio)
            self.fb.unbind()
            self.sq.render(
                self.fb.position_tex, self.fb.normal_tex, self.fb.color_tex
            )

            self.window.swap_buffers()
            self.window.poll_events()

    def exit(self):
        self.fb.destroy()
        self.sq.destroy()

        self.window.exit()
