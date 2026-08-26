from enum import IntEnum, IntFlag, auto


class TriggerMode(IntEnum):
    PRESSED = auto()
    RELEASED = auto()
    CLICKED = auto()
    WHILE = auto()
    AXIS_DELTA = auto()


class InputModifier(IntFlag):
    RIGHT_CONTROL = auto()
    LEFT_CONTROL = auto()
    CTRL = RIGHT_CONTROL | LEFT_CONTROL

    RIGHT_SHIFT = auto()
    LEFT_SHIFT = auto()
    SHIFT = RIGHT_SHIFT | LEFT_SHIFT

    ALT = auto()
    SUPER = auto()

    NONE = 0


# Also makes it easier to switch between backends: glfw, qt etc...
class Inputs(IntEnum):
    # Mouse
    LEFT_MOUSE_BUTTON = auto()
    LMB = LEFT_MOUSE_BUTTON
    MIDDLE_MOUSE_BUTTON = auto()
    MMB = MIDDLE_MOUSE_BUTTON
    RIGHT_MOUSE_BUTTON = auto()
    RMB = RIGHT_MOUSE_BUTTON

    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()
