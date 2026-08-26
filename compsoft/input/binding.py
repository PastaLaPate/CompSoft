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
