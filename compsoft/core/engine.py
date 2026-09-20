import time
from collections.abc import Callable
from typing import cast

import glfw
import glm
from OpenGL.GL import (
    GL_BACK,
    GL_BLEND,
    GL_FALSE,
    GL_FRONT,
    GL_ONE,
    GL_TRUE,
    glBlendFunc,
    glCullFace,
    glDepthMask,
    glDisable,
    glEnable,
)
from pyglm.glm import mat4x4, vec2, vec3

from compsoft.core.debug import DebugFlags, Profiler
from compsoft.core.window import Window
from compsoft.graphics.debug_depth_screen_quad import DebugDepthScreenQuad
from compsoft.graphics.infrastructure.frame_buffers.scene_frame_buffer import (
    SceneFrameBuffer,
)
from compsoft.graphics.infrastructure.frame_buffers.shadows_frame_buffer import (
    ShadowFrameBuffer,
)
from compsoft.graphics.infrastructure.frame_buffers.vol_light_frame_buffer import (
    VolumetricLightFrameBuffer,
)
from compsoft.graphics.infrastructure.quads.blur_screen_quad import (
    BlurScreenQuad,
)
from compsoft.graphics.infrastructure.quads.lit_screen_quad import (
    SceneRenderScreenQuad,
)
from compsoft.graphics.infrastructure.quads.post_screen_quad import (
    PostScreenQuad,
)
from compsoft.graphics.infrastructure.quads.vol_light_screen_quad import (
    VolumetricLightScreenQuad,
)
from compsoft.graphics.infrastructure.render_pass import RenderPass
from compsoft.input.consumers.gizmo_consumer import (
    BINDING_GIZMO_CLICK,
    BINDING_GIZMO_CLICK_RELEASE,
    GizmoInputConsumer,
)
from compsoft.input.consumers.scene_click_consumer import (
    BINDING_SCENE_LMB_CLICK,
    SceneClickConsumer,
)
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
        self.shadows_fb = ShadowFrameBuffer(5)
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

        self.input_manager.add_binding(BINDING_SCENE_LMB_CLICK)

        self.input_manager.add_binding(BINDING_GIZMO_CLICK)
        self.input_manager.add_binding(BINDING_GIZMO_CLICK_RELEASE)

        self.input_manager.add_consumer(
            ViewportInputConsumer(self.cam_controls)
        )
        self.input_manager.add_consumer(SceneClickConsumer(self.scene))
        self.input_manager.add_consumer(GizmoInputConsumer(self.scene))
        self.window_bridge = WindowInputBridge(
            self.window.window, self.input_manager
        )
        # self.cam_controls.add_lmb_click_listener(
        #    lambda pos: self.scene.select_on_click(
        #        self.window.size[0], self.window.size[1], pos
        #    )
        # )

        self.fb = SceneFrameBuffer(*self.window.size)
        self.vol_fb = VolumetricLightFrameBuffer(*self.window.size)
        self.blur_fb = VolumetricLightFrameBuffer(*self.window.size)
        self.post_fb = VolumetricLightFrameBuffer(*self.window.size)

        self.sq = SceneRenderScreenQuad(resources.get_shader_path("lit"))
        self.vol_sq = VolumetricLightScreenQuad(
            resources.get_shader_path("vol_light")
        )
        self.blur_sq = BlurScreenQuad(resources.get_shader_path("blur"))
        self.post_sq = PostScreenQuad(resources.get_shader_path("postprocess"))

        self.profiler = Profiler()
        self.debug_depth_sq = None
        if self.scene.debug.has_flag(DebugFlags.DEBUG_RENDER_SHADOW_MAP):
            self.construct_debug_depth_sq()
        self.window.add_window_resize_listener(self.fb._on_window_size_changed)
        self.window.add_window_resize_listener(
            self.vol_fb._on_window_size_changed
        )
        self.window.add_window_resize_listener(
            self.blur_fb._on_window_size_changed
        )
        self.window.add_window_resize_listener(
            self.post_fb._on_window_size_changed
        )

    def construct_debug_depth_sq(self):
        self.debug_depth_sq = DebugDepthScreenQuad()

    def _add_prerender_listener(
        self, listener: Callable[[float, float], None]
    ):
        self.prerender_listeners.append(listener)

    def start(self) -> None:
        t = 0
        last_print = time.time()
        while (
            not self.window.key_pressed(glfw.KEY_ESCAPE)
            and not self.window.should_close()
        ):
            self.window.clear()

            debug_basic = self.scene.debug.has_flag(
                DebugFlags.DEBUG_FRAME_TIME
            )
            debug_complex = self.scene.debug.has_flag(
                DebugFlags.DEBUG_FRAME_TIME_DETAILLED
            )

            # Track time in ms
            dt_ms = self.window.dt * 1000
            self.profiler.record("frame time (ms)", dt_ms, enabled=debug_basic)
            self.profiler.record("fps", 1000.0 / dt_ms, enabled=debug_basic)

            with self.profiler.time("Inputs", enabled=debug_complex):
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
                with self.profiler.time("Deferred", enabled=debug_complex):
                    with self.fb:
                        self.scene.render(
                            self.window.aspect_ratio, RenderPass.DEFERRED
                        )
                    self.scene.upload_light_ubo(self.scene.get_lights())

                with self.profiler.time("Shadow", enabled=debug_complex):
                    glCullFace(GL_FRONT)
                    light_space_matrices = {}
                    for active_light in self.scene.active_lights:
                        index = self.shadows_fb.get_light_layer(active_light)
                        matrix = self.shadows_fb.render_light(
                            active_light, self.scene
                        )
                        light_space_matrices[index] = matrix

                with self.profiler.time("Lighting", enabled=debug_complex):
                    glCullFace(GL_BACK)
                    with self.post_fb:
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
                    self.post_sq.bind_shader()
                    self.post_sq.render(
                        *self.window.size, self.post_fb.color_tex
                    )

                with self.profiler.time("Forward", enabled=debug_complex):
                    self.fb.unbind()  # Get the scene's depth buffer back
                    self.scene.render(
                        self.window.aspect_ratio, RenderPass.FORWARD
                    )

                with (
                    self.profiler.time("Vol Lightning", enabled=debug_complex),
                    self.vol_fb,
                ):
                    self.vol_sq.bind_shader(light_space_matrices)
                    self.vol_sq.render(
                        *self.window.size,
                        self.fb.position_tex,
                        self.shadows_fb.shadow_array_tex,
                        self.scene.camera.pos,
                        cast(
                            mat4x4,
                            glm.inverse(
                                self.scene.camera.get_projection_matrix(
                                    self.window.aspect_ratio
                                )
                                * self.scene.camera.get_view_matrix()
                            ),
                        ),
                    )

                with self.profiler.time("Blur", enabled=debug_complex):
                    with self.blur_fb:
                        self.blur_sq.bind_shader()
                        self.blur_sq.render(
                            self.window.size[0],
                            self.window.size[1],
                            self.vol_fb.color_tex,
                            blur_direction=vec2(1, 0),
                        )

                    glEnable(GL_BLEND)
                    glBlendFunc(GL_ONE, GL_ONE)
                    glDepthMask(GL_FALSE)
                    self.blur_sq.bind_shader()
                    self.blur_sq.render(
                        self.window.size[0],
                        self.window.size[1],
                        self.blur_fb.color_tex,
                        blur_direction=vec2(0, 1),
                    )
                    glDepthMask(GL_TRUE)
                    glDisable(GL_BLEND)

            # Goofy huh
            now = time.time()
            if now - last_print > 0.75:
                self.profiler.summary()
                self._last_print_time = now

            self.window.swap_buffers()

    def exit(self):
        self.fb.destroy()
        self.sq.destroy()

        self.window.exit()
