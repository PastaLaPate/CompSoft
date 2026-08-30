from collections import deque
from collections.abc import Callable

import glfw
from OpenGL.GL import GL_BACK, GL_FRONT, glCullFace
from pyglm.glm import vec3

from compsoft.core.debug import DebugFlags
from compsoft.core.window import Window
from compsoft.graphics.debug_depth_screen_quad import DebugDepthScreenQuad
from compsoft.graphics.frame_buffer import FrameBuffer
from compsoft.graphics.render_pass import RenderPass
from compsoft.graphics.screen_quad import ScreenQuad
from compsoft.graphics.shadows_frame_buffer import ShadowFrameBuffer
from compsoft.input.consumers.viewport_consumer import (
    BINDING_BACKWARD,
    BINDING_CAMERA_FOV,
    BINDING_CAMERA_ORBIT,
    BINDING_CAMERA_ORBIT_RELEASE,
    BINDING_CAMERA_PAN,
    BINDING_CAMERA_PAN_RELEASE,
    BINDING_CAMERA_SPEED,
    BINDING_FORWARD,
    BINDING_LEFT,
    BINDING_RIGHT,
    ViewportInputConsumer,
)
from compsoft.input.manager import InputManager
from compsoft.input.state import PointerState
from compsoft.input.window_bridge import WindowInputBridge
from compsoft.resources.manager import resources
from compsoft.scene.camera import Camera
from compsoft.scene.camera_controls import CameraControls
from compsoft.scene.scene import Scene


class Engine:
    def __init__(self) -> None:
        self.prerender_listeners: list[Callable[[float, float], None]] = []

        self.window = Window(800, 600, "CompSoft")

        self.cam = Camera(vec3(0, 0, 0))
        self.cam_controls = CameraControls(self.cam)
        self.shadows_fb = ShadowFrameBuffer(1)
        self.scene = Scene(self.cam, self.shadows_fb)

        self.pointer_state = PointerState()
        self.input_manager = InputManager(self.pointer_state)

        self.input_manager.add_binding(BINDING_CAMERA_PAN)
        self.input_manager.add_binding(BINDING_CAMERA_PAN_RELEASE)
        self.input_manager.add_binding(BINDING_CAMERA_ORBIT)
        self.input_manager.add_binding(BINDING_CAMERA_ORBIT_RELEASE)

        self.input_manager.add_binding(BINDING_FORWARD)
        self.input_manager.add_binding(BINDING_BACKWARD)
        self.input_manager.add_binding(BINDING_LEFT)
        self.input_manager.add_binding(BINDING_RIGHT)

        self.input_manager.add_binding(BINDING_CAMERA_SPEED)
        self.input_manager.add_binding(BINDING_CAMERA_FOV)

        self.input_manager.add_consumer(
            ViewportInputConsumer(self.cam_controls)
        )
        self.window_bridge = WindowInputBridge(
            self.window.window, self.input_manager
        )
        # self.cam_controls.add_lmb_click_listener(
        #    lambda pos: self.scene.select_on_click(
        #        self.window.size[0], self.window.size[1], pos
        #    )
        # )

        self.fb = FrameBuffer(self.window.size[0], self.window.size[1])
        sq_shader_pair = resources.get_shader_path("lit")
        self.sq = ScreenQuad(sq_shader_pair.vertex, sq_shader_pair.fragment)
        self.debug_depth_sq = None
        if self.scene.debug.has_flag(DebugFlags.DEBUG_RENDER_SHADOW_MAP):
            self.construct_debug_depth_sq()
        self.window.add_window_resize_listener(self.fb._on_window_size_changed)

    def construct_debug_depth_sq(self):
        self.debug_depth_sq = DebugDepthScreenQuad()

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
            self.input_manager.begin_frame()
            self.window.poll_events()
            self.input_manager.update(self.window.dt)

            t += self.window.dt * 100
            [
                listener(t, self.window.dt)
                for listener in self.prerender_listeners
            ]

            if self.scene.debug.has_flag(DebugFlags.DEBUG_RENDER_SHADOW_MAP):
                if self.debug_depth_sq is None:
                    self.construct_debug_depth_sq()
                if self.debug_depth_sq:
                    self.shadows_fb.render_light(
                        self.scene.active_lights[0], self.scene
                    )
                    self.debug_depth_sq.bind_shader()
                    self.debug_depth_sq.render(
                        1024,
                        1024,
                        position_tex=0,
                        shadows_tex=self.shadows_fb.shadow_array_tex,
                    )
            else:
                self.fb.bind()
                self.scene.render(
                    self.window.aspect_ratio, RenderPass.DEFERRED
                )
                self.fb.unbind()
                self.scene.upload_light_ubo(self.scene.get_lights())

                glCullFace(GL_FRONT)
                light_space_matrices = {}
                for active_light in self.scene.active_lights:
                    index = self.shadows_fb.get_light_layer(active_light)
                    matrix = self.shadows_fb.render_light(
                        active_light, self.scene
                    )
                    light_space_matrices[index] = matrix

                glCullFace(GL_BACK)
                self.sq.bind_shader(light_space_matrices)
                self.sq.render(
                    self.window.size[0],
                    self.window.size[1],
                    self.fb.position_tex,
                    self.fb.normal_tex,
                    self.fb.color_tex,
                    self.fb.selection_tex,
                    self.shadows_fb.shadow_array_tex,
                    self.scene.camera.pos,
                )
                self.scene.render(self.window.aspect_ratio, RenderPass.FORWARD)

            self.window.swap_buffers()

    def exit(self):
        self.fb.destroy()
        self.sq.destroy()

        self.window.exit()
