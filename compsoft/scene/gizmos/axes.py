from enum import IntEnum, auto

from pyglm.glm import vec3


class Axis(IntEnum):
    X = auto()
    Y = auto()
    Z = auto()


AXIS_DIRS = {
    Axis.X: vec3(1, 0, 0),
    Axis.Y: vec3(0, 1, 0),
    Axis.Z: vec3(0, 0, 1),
}
