from enum import Enum, auto


class CursorMode(Enum):
    NORMAL = auto()  # Standard visible cursor
    HIDDEN = auto()  # Invisible over window, moves freely
    DISABLED = auto()  # Locked to window center & hidden (FPS / 3D Orbit look)


class CursorShape(Enum):
    ARROW = auto()
    IBEAM = auto()
    CROSSHAIR = auto()
    HAND = auto()
    RESIZE_ALL = auto()
    GRAB = auto()
