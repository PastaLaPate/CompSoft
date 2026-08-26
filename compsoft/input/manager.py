from compsoft.input.binding import Binding
from compsoft.input.consumer import InputConsumer
from compsoft.input.state import PointerState


class InputManager:
    def __init__(self, pointer_state: PointerState) -> None:
        self._consumers: list[InputConsumer] = []
        self.bindings: list[Binding] = []
        self.pointer = pointer_state

    def add_consumer(self, consumer: InputConsumer):
        self._consumers.append(consumer)

    def sort_consumers(self):
        self._consumers = sorted(
            self._consumers, key=lambda c: c.priority, reverse=True
        )

    def dispatch_action(self, action_id: str, value: float = 1.0) -> None:
        if self.pointer.active_drag_action:
            self.pointer.active_drag_action.on_action(
                action_id, value, self.pointer
            )
            return
        for consumer in self._consumers:
            if consumer.on_action(action_id, value, self.pointer):
                break  # consumed, break
