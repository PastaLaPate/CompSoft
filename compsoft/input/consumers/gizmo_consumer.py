from pyglm import glm
from pyglm.glm import vec2, vec3

from compsoft.input.binding import Binding
from compsoft.input.consumer import InputConsumer
from compsoft.input.cursors import CursorShape
from compsoft.input.inputs import Inputs, TriggerMode
from compsoft.input.state import PointerState
from compsoft.input.window_bridge import WindowInputBridge
from compsoft.scene.gizmos.axes import AXIS_DIRS, Axis
from compsoft.scene.scene import Scene

BINDING_GIZMO_CLICK = Binding(
    "camera.orbit", Inputs.LMB, trigger_mode=TriggerMode.WHILE
)

BINDING_GIZMO_CLICK_RELEASE = Binding(
    "camera.orbit.release", Inputs.LMB, trigger_mode=TriggerMode.RELEASED
)


def closest_point_on_axis(
    origin: vec3, dir: vec3, axis: Axis, axes_origin: vec3
) -> float | None:
    axis_dir = AXIS_DIRS[axis]
    axis_o = axes_origin
    r = origin - axis_o
    a = glm.dot(dir, dir)
    b = glm.dot(dir, axis_dir)
    c = glm.dot(axis_dir, axis_dir)
    d = glm.dot(dir, r)
    e = glm.dot(axis_dir, r)

    denom = a * c - b * b
    if abs(denom) < 1e-6:
        return None

    t_axis = (a * e - b * d) / denom
    return t_axis


class GizmoInputConsumer(InputConsumer):
    def __init__(
        self,
        scene: Scene,
        priority: int = 200,
    ):
        super().__init__(priority)
        self.scene = scene

        self.start_click_pos = vec2(0, 0)
        self.last_pos = vec2(0, 0)
        self.current_axis = Axis.X
        self.moving_gizmo = False

        self.axis_origin = vec3(0, 0, 0)
        self.axis_start_t = 0.0

    def on_hover(
        self, pointer: PointerState, window: WindowInputBridge
    ) -> CursorShape | None:
        if self.moving_gizmo:
            return CursorShape.GRAB

        ray_origin, ray_dir = self.scene.compute_ray(
            window.get_width(), window.get_height(), pointer.current_pos
        )
        if self.scene.is_ray_on_gizmo(ray_origin, ray_dir) is not None:
            return CursorShape.HAND
        return None

    def on_action(
        self,
        action_id: str,
        dt: float,
        value: float,
        pointer: PointerState,
        window: WindowInputBridge,
    ) -> bool:
        if action_id == BINDING_GIZMO_CLICK.id:
            ray_origin, ray_dir = self.scene.compute_ray(
                window.get_width(), window.get_height(), pointer.current_pos
            )
            if self.moving_gizmo == False:
                axis = self.scene.is_ray_on_gizmo(ray_origin, ray_dir)
                if axis is not None:
                    self.current_axis = axis
                    self.moving_gizmo = True
                    self.start_click_pos = pointer.current_pos
                    self.last_pos = pointer.current_pos

                    self.scene.translation_gizmo.select_axis(axis)
                    self.axis_origin = self.scene.translation_gizmo.position
                    t0 = closest_point_on_axis(
                        vec3(ray_origin), vec3(ray_dir), axis, self.axis_origin
                    )

                    self.axis_start_t = t0 if t0 is not None else 0.0
                    window.set_cursor_shape(CursorShape.GRAB)

                    return True
            else:
                t = closest_point_on_axis(
                    vec3(ray_origin),
                    vec3(ray_dir),
                    self.current_axis,
                    self.axis_origin,
                )
                if t is not None:
                    delta = t - self.axis_start_t
                    self.scene.translation_gizmo.position = (
                        self.axis_origin + AXIS_DIRS[self.current_axis] * delta
                    )
                self.last_pos = pointer.current_pos
                return True

            return False

        if action_id == BINDING_GIZMO_CLICK_RELEASE.id and self.moving_gizmo:
            self.moving_gizmo = False
            self.scene.translation_gizmo.unselect_axes()
            window.set_cursor_shape(CursorShape.ARROW)
            return True

        return False
