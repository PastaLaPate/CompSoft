from compsoft.input.binding import Binding
from compsoft.input.inputs import InputModifier, Inputs, TriggerMode

BINDING_CAMERA_PAN = Binding(
    "camera.pan",
    Inputs.MMB,
    modifier=InputModifier.SHIFT,
    trigger_mode=TriggerMode.WHILE,
)
