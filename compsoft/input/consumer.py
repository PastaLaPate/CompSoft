from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from compsoft.input.state import PointerState
    from compsoft.input.window_bridge import WindowInputBridge


class InputConsumer(ABC):
    def __init__(self, priority: int = 0) -> None:
        """Constructs an input consumer

        Args:
            priority (int, optional): Priority of the input consumer, higher = evaluated first. Defaults to 0.
        """
        self.priority = priority

    @abstractmethod
    def on_action(
        self,
        action_id: str,
        value: float,
        pointer: PointerState,
        window: WindowInputBridge,
    ) -> bool:
        """Listener for input actions

        Args:
            action_id (str): The binding name of the action.
            value (float): For keys and mouse button: 1.0 when pressed, 0.0 when released, for mouse wheel: 1.0 for scrolling up and 0.0 for down, for mouse movement: pixel distance.
            pointer (PointerState): The state of the pointer.
            window (WindowInputBridge): The window bridge calling.

        Returns:
            bool: If the InputConsumer consumed the input.
        """
        return False
