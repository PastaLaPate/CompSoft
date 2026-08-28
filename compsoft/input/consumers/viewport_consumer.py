import math

from pyglm.glm import vec2

from compsoft.input.binding import Binding
from compsoft.input.consumer import InputConsumer
from compsoft.input.cursors import CursorMode, CursorShape
from compsoft.input.inputs import InputModifier, Inputs, TriggerMode
from compsoft.input.state import PointerState
from compsoft.input.window_bridge import WindowInputBridge
from compsoft.scene.camera_controls import CameraControls

BINDING_CAMERA_PAN = Binding(
    "camera.pan",
    Inputs.MMB,
    modifier=InputModifier.SHIFT,
    trigger_mode=TriggerMode.WHILE,
)


BINDING_CAMERA_PAN_RELEASE = Binding(
    "camera.pan.release",
    Inputs.MMB,
    modifier=InputModifier.SHIFT,
    trigger_mode=TriggerMode.RELEASED,
)

BINDING_CAMERA_ORBIT = Binding(
    "camera.orbit", Inputs.LMB, trigger_mode=TriggerMode.WHILE
)

BINDING_CAMERA_ORBIT_RELEASE = Binding(
    "camera.orbit.release", Inputs.LMB, trigger_mode=TriggerMode.RELEASED
)

BINDING_FORWARD = Binding(
    "viewport.forward", Inputs.W, trigger_mode=TriggerMode.WHILE
)
BINDING_BACKWARD = Binding(
    "viewport.backward", Inputs.S, trigger_mode=TriggerMode.WHILE
)
BINDING_LEFT = Binding(
    "viewport.left", Inputs.A, trigger_mode=TriggerMode.WHILE
)
BINDING_RIGHT = Binding(
    "viewport.right", Inputs.D, trigger_mode=TriggerMode.WHILE
)

BINDING_CAMERA_SPEED = Binding(
    "camera.speed", Inputs.MOUSE_WHEEL, trigger_mode=TriggerMode.AXIS_DELTA
)
BINDING_CAMERA_FOV = Binding(
    "camera.fov",
    Inputs.MOUSE_WHEEL,
    modifier=InputModifier.CTRL,
    trigger_mode=TriggerMode.AXIS_DELTA,
)


class ViewportInputConsumer(InputConsumer):
    def __init__(
        self,
        camera_controls: CameraControls,
        priority: int = 100,
        drag_threshold: float = 4.0,
    ):
        super().__init__(priority)
        self.camera_controls = camera_controls
        self.drag_threshold = drag_threshold
        self.is_panning = False
        self.is_lmb_clicking = False
        self.is_orbiting = False
        self.start_click_pos = vec2(0, 0)

    def on_action(
        self,
        action_id: str,
        dt: float,
        value: float,
        pointer: PointerState,
        window: WindowInputBridge,
    ) -> bool:
        if action_id == BINDING_CAMERA_PAN.id and value > 0:
            if not self.is_panning:
                self.is_panning = True
                window.set_cursor_mode(CursorMode.DISABLED)

            if pointer.delta.x != 0 or pointer.delta.y != 0:
                self.camera_controls.pan_camera(pointer.delta)

            return True

        if action_id == BINDING_CAMERA_PAN_RELEASE.id:
            if self.is_panning:
                self.is_panning = False
                window.set_cursor_mode(CursorMode.NORMAL)
                window.set_cursor_shape(CursorShape.ARROW)
            return True

        if action_id == BINDING_CAMERA_ORBIT.id:
            if not self.is_lmb_clicking:
                self.is_lmb_clicking = True
                self.start_click_pos = pointer.current_pos
            elif self.is_lmb_clicking and not self.is_orbiting:
                dist = math.hypot(
                    pointer.current_pos.x - self.start_click_pos.x,
                    pointer.current_pos.y - self.start_click_pos.y,
                )
                if dist > self.drag_threshold:
                    self.is_orbiting = True
                    window.set_cursor_mode(CursorMode.DISABLED)
            elif self.is_orbiting:
                self.camera_controls.orbit_camera(pointer.delta)
            return True

        if action_id == BINDING_CAMERA_ORBIT_RELEASE.id:
            if not self.is_orbiting:
                pass  # Register click for select
            self.is_orbiting = False
            self.is_lmb_clicking = False
            window.set_cursor_mode(CursorMode.NORMAL)
            window.set_cursor_shape(CursorShape.ARROW)
            return True

        if action_id == BINDING_FORWARD.id:
            self.camera_controls.forward(dt)
            return True
        if action_id == BINDING_BACKWARD.id:
            self.camera_controls.backward(dt)
            return True
        if action_id == BINDING_LEFT.id:
            self.camera_controls.left(dt)
            return True
        if action_id == BINDING_RIGHT.id:
            self.camera_controls.right(dt)
            return True

        if action_id == BINDING_CAMERA_SPEED.id:
            self.camera_controls.add_speed(value * 0.5)
            return True
        if action_id == BINDING_CAMERA_FOV.id:
            self.camera_controls.add_fov(int(value * 5))
            return True

        return False
