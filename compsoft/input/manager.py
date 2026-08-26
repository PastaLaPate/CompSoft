from compsoft.input.binding import Binding
from compsoft.input.consumer import InputConsumer
from compsoft.input.inputs import InputModifier, Inputs, TriggerMode
from compsoft.input.state import PointerState


class InputManager:
    def __init__(self, pointer_state: PointerState) -> None:
        self._consumers: list[InputConsumer] = []
        self.bindings: list[Binding] = []
        self.pointer = pointer_state

        self.active_keys: set[Inputs] = set()
        self.current_modifiers = InputModifier.NONE

    def add_consumer(self, consumer: InputConsumer):
        self._consumers.append(consumer)
        self.sort_consumers()

    def sort_consumers(self):
        self._consumers = sorted(
            self._consumers, key=lambda c: c.priority, reverse=True
        )

    def add_binding(self, binding: Binding):
        self.bindings.append(binding)

    def dispatch_action(self, action_id: str, value: float = 1.0) -> bool:
        if self.pointer.active_drag_action:
            self.pointer.active_drag_action.on_action(
                action_id, value, self.pointer
            )
            return True
        for consumer in self._consumers:
            if consumer.on_action(action_id, value, self.pointer):
                return True
        return False

    def handle_input_event(
        self, input_code: Inputs, mode: TriggerMode
    ) -> None:
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
                    1.0
                    if mode in (TriggerMode.PRESSED, TriggerMode.WHILE)
                    else 0.0
                )
                if self.dispatch_action(binding.id, val):
                    break
