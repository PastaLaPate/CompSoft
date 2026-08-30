from compsoft.input.inputs import InputModifier, Inputs, TriggerMode


class Binding:
    def __init__(
        self,
        id: str,
        input: Inputs,
        modifier=InputModifier.NONE,
        trigger_mode=TriggerMode.PRESSED,
    ) -> None:
        self.id = id
        self.input = input
        self.trigger_mode = trigger_mode
        self.modifier = modifier

    @property
    def chord_weight(self) -> int:
        """Higher modifier count takes priority (eg Shift+MMB over MMB)."""
        return self.modifier.value.bit_count()

    def __eq__(self, other):
        if isinstance(other, Binding):
            return (
                other.id == self.id
                and other.input == self.input
                and other.trigger_mode == self.trigger_mode
                and other.modifier == self.modifier
            )
        elif isinstance(other, str):
            return self.id == other
        else:
            return super().__eq__(other)
