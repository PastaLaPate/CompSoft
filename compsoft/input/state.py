from pyglm.glm import vec2

from compsoft.input.consumer import InputConsumer


class PointerState:
    def __init__(self) -> None:

        # Positions
        self.current_pos = vec2(0, 0)
        self.last_pos = vec2(0, 0)
        self.delta = vec2(0, 0)

        # Drag
        self.drag_start_pos = vec2(0, 0)
        self.drag_threshold = 1
        self.active_drag_action: InputConsumer | None = None

        # Scroll wheel
        self.scroll_delta = vec2(0, 0)
