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
# Each character represents the scancode of the us layout
class Inputs(IntEnum):
    # Mouse
    LEFT_MOUSE_BUTTON = auto()
    LMB = LEFT_MOUSE_BUTTON
    MIDDLE_MOUSE_BUTTON = auto()
    MMB = MIDDLE_MOUSE_BUTTON
    RIGHT_MOUSE_BUTTON = auto()
    RMB = RIGHT_MOUSE_BUTTON
    MOUSE_4 = auto()
    X1 = MOUSE_4
    MOUSE_5 = auto()
    X2 = MOUSE_5

    # Special characters
    ESCAPE = auto()
    ESC = ESCAPE
    DELETE = auto()
    DEL = DELETE
    HOME = auto()
    END = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    INSERT = auto()
    ENTER = auto()
    ENT = ENTER
    BACK_SPACE = auto()
    BCK_SPACE = BACK_SPACE
    SPACE = auto()
    TAB = auto()
    CAPS_LOCK = auto()
    NUM_LOCK = auto()
    SCROLL_LOCK = auto()
    PRINT_SCREEN = auto()
    PAUSE = auto()
    MENU = auto()

    # Modifiers
    RIGHT_CONTROL = auto()
    LEFT_CONTROL = auto()
    CTRL = LEFT_CONTROL

    RIGHT_SHIFT = auto()
    LEFT_SHIFT = auto()
    SHIFT = LEFT_SHIFT

    RIGHT_ALT = auto()
    LEFT_ALT = auto()
    ALT = LEFT_ALT

    RIGHT_SUPER = auto()
    LEFT_SUPER = auto()
    SUPER = LEFT_SUPER

    # F keys
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()

    # Arrows
    ARROW_UP = auto()
    UP = ARROW_UP
    ARROW_DOWN = auto()
    DOWN = ARROW_DOWN
    ARROW_LEFT = auto()
    LEFT = ARROW_LEFT
    ARROW_RIGHT = auto()
    RIGHT = ARROW_RIGHT

    # Top Row Numbers
    N_0 = auto()
    N_1 = auto()
    N_2 = auto()
    N_3 = auto()
    N_4 = auto()
    N_5 = auto()
    N_6 = auto()
    N_7 = auto()
    N_8 = auto()
    N_9 = auto()

    # Numpad
    KP_0 = auto()
    KP_1 = auto()
    KP_2 = auto()
    KP_3 = auto()
    KP_4 = auto()
    KP_5 = auto()
    KP_6 = auto()
    KP_7 = auto()
    KP_8 = auto()
    KP_9 = auto()
    KP_DECIMAL = auto()
    KP_DIVIDE = auto()
    KP_MULTIPLY = auto()
    KP_SUBTRACT = auto()
    KP_ADD = auto()
    KP_ENTER = auto()
    KP_EQUAL = auto()

    # Symbols
    GRAVE_ACCENT = auto()
    MINUS = auto()
    EQUAL = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    SEMICOLON = auto()
    APOSTROPHE = auto()
    COMMA = auto()
    PERIOD = auto()
    SLASH = auto()
    BACK_SLASH = auto()

    # Alphabet keys
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
