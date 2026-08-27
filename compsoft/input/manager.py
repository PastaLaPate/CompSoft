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

    def _update_modifiers(self) -> None:
        mods = InputModifier.NONE
        modifiers_map = {
            Inputs.LEFT_CONTROL: InputModifier.LEFT_CONTROL,
            Inputs.RIGHT_CONTROL: InputModifier.RIGHT_CONTROL,
            Inputs.LEFT_SHIFT: InputModifier.LEFT_SHIFT,
            Inputs.RIGHT_SHIFT: InputModifier.RIGHT_SHIFT,
            Inputs.LEFT_ALT: InputModifier.ALT,
            Inputs.RIGHT_ALT: InputModifier.ALT,
            Inputs.LEFT_SUPER: InputModifier.SUPER,
            Inputs.RIGHT_SUPER: InputModifier.SUPER,
        }
        for key in self.active_keys:
            if key in modifiers_map:
                mods |= modifiers_map[key]

        self.current_modifiers = mods

    def handle_input_event(
        self, input_code: Inputs, mode: TriggerMode
    ) -> None:
        if mode == TriggerMode.PRESSED:
            self.active_keys.add(input_code)
        elif mode == TriggerMode.RELEASED:
            self.active_keys.discard(input_code)

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

    def update(self) -> None:
        for key in list(self.active_keys):
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
