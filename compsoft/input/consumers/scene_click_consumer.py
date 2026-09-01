from __future__ import annotations

from typing import TYPE_CHECKING

from compsoft.input.binding import Binding
from compsoft.input.consumer import InputConsumer
from compsoft.input.inputs import Inputs, TriggerMode
from compsoft.input.state import PointerState
from compsoft.input.window_bridge import WindowInputBridge

if TYPE_CHECKING:
    from compsoft.scene.scene import Scene

BINDING_SCENE_LMB_CLICK = Binding(
    "scene_click_consumer.lmb_click",
    Inputs.LMB,
    trigger_mode=TriggerMode.RELEASED,
)


class SceneClickConsumer(InputConsumer):
    def __init__(self, scene: Scene):
        super().__init__()
        self.scene = scene

    def on_action(
        self,
        action_id: str,
        dt: float,
        value: float,
        pointer: PointerState,
        window: WindowInputBridge,
    ) -> bool:
        if action_id == BINDING_SCENE_LMB_CLICK:
            return self.scene.on_click(*window.get_size(), pointer.current_pos)

        return False
