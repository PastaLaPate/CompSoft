from typing import TYPE_CHECKING

from compsoft.input.binding import Binding
from compsoft.input.consumer import InputConsumer
from compsoft.input.inputs import InputModifier, Inputs, TriggerMode
from compsoft.input.state import PointerState

if TYPE_CHECKING:
    from compsoft.input.window_bridge import WindowInputBridge

MODIFIERS_MAP = {
    Inputs.LEFT_CONTROL: InputModifier.LEFT_CONTROL | InputModifier.CTRL,
    Inputs.RIGHT_CONTROL: InputModifier.RIGHT_CONTROL | InputModifier.CTRL,
    Inputs.LEFT_SHIFT: InputModifier.LEFT_SHIFT | InputModifier.SHIFT,
    Inputs.RIGHT_SHIFT: InputModifier.RIGHT_SHIFT | InputModifier.SHIFT,
    Inputs.LEFT_ALT: InputModifier.LEFT_ALT | InputModifier.ALT,
    Inputs.RIGHT_ALT: InputModifier.RIGHT_ALT | InputModifier.ALT,
    Inputs.LEFT_SUPER: InputModifier.LEFT_SUPER | InputModifier.SUPER,
    Inputs.RIGHT_SUPER: InputModifier.RIGHT_SUPER | InputModifier.SUPER,
}


class InputManager:
    def __init__(self, pointer_state: PointerState) -> None:
        self._consumers: list[InputConsumer] = []
        self.bindings: list[Binding] = []
        self.pointer = pointer_state

        self.active_keys: set[Inputs] = set()
        self.current_modifiers = InputModifier.NONE

        self.controller: WindowInputBridge | None = None

    def add_consumer(self, consumer: InputConsumer):
        self._consumers.append(consumer)
        self.sort_consumers()

    def sort_consumers(self):
        self._consumers = sorted(
            self._consumers, key=lambda c: c.priority, reverse=True
        )

    def add_binding(self, binding: Binding):
        self.bindings.append(binding)

    def _update_modifiers(self) -> None:
        mods = InputModifier.NONE
        for key in self.active_keys:
            if key in MODIFIERS_MAP:
                mods |= MODIFIERS_MAP[key]

        self.current_modifiers = mods

    def handle_input_event(
        self, input_code: Inputs, mode: TriggerMode, value: float | None = None
    ) -> None:
        if mode == TriggerMode.PRESSED:
            self.active_keys.add(input_code)
        elif mode == TriggerMode.RELEASED:
            self.active_keys.discard(input_code)
        self._update_modifiers()

        matching_bindings = [
            b
            for b in self.bindings
            if b.input == input_code and b.trigger_mode == mode
        ]
        matching_bindings.sort(key=lambda b: b.chord_weight, reverse=True)

        for binding in matching_bindings:
            if (
                binding.modifier == InputModifier.NONE
                or (self.current_modifiers & binding.modifier)
                == binding.modifier
            ):
                val = (
                    (
                        1.0
                        if mode in (TriggerMode.PRESSED, TriggerMode.WHILE)
                        else 0.0
                    )
                    if value is None
                    else value
                )
                if self.dispatch_action(binding.id, val):
                    break

    def update(self, dt: float) -> None:
        for key in self.active_keys:
            matching_bindings = [
                b
                for b in self.bindings
                if b.input == key and b.trigger_mode == TriggerMode.WHILE
            ]

            matching_bindings.sort(key=lambda b: b.chord_weight, reverse=True)
            for binding in matching_bindings:
                if (
                    binding.modifier == InputModifier.NONE
                    or (self.current_modifiers & binding.modifier)
                    == binding.modifier
                ) and self.dispatch_action(binding.id, 1.0):
                    break

    def dispatch_action(
        self, action_id: str, dt: float, value: float = 1.0
    ) -> bool:
        if not self.controller:
            return False
        if self.pointer.active_drag_action:
            self.pointer.active_drag_action.on_action(
                action_id, dt, value, self.pointer, self.controller
            )
            return True
        for consumer in self._consumers:
            if consumer.on_action(
                action_id, dt, value, self.pointer, self.controller
            ):
                return True
        return False
