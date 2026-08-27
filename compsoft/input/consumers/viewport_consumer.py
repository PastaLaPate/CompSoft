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

        if action_id == "camera.pan_release":
            print("released")
            if self.is_panning:
                self.is_panning = False
                window.set_cursor_mode(CursorMode.NORMAL)
                window.set_cursor_shape(CursorShape.ARROW)
            return True

        """
        dist = math.hypot(
            current_x - self.lmb_press_pos[0],
            current_y - self.lmb_press_pos[1],
        )
        """

        return False
