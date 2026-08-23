from enum import Enum, auto
from typing import NamedTuple

from pyglm import glm
from pyglm.glm import epsilon, vec3


class RayTrace(NamedTuple):
    origin: vec3
    direction: vec3


class IntersectResult(Enum):
    REJECT = auto()
    INTERSECT = auto()


# Based on Realtime Rendering 4th edition (22.8.2)


def ray_tri_intersect(
    raytrace: RayTrace, triangle: tuple[vec3, vec3, vec3]
) -> tuple[IntersectResult, float, float, float]:
    return ray_tri_intersect_raw(
        raytrace.origin,
        raytrace.direction,
        triangle[0],
        triangle[1],
        triangle[2],
    )


def ray_tri_intersect_raw(
    origin: vec3, dir: vec3, p0: vec3, p1: vec3, p2: vec3
) -> tuple[IntersectResult, float, float, float]:
    edge_1 = p1 - p0
    edge_2 = p2 - p0

    q = glm.cross(dir, edge_2)
    a = glm.dot(edge_1, q)
    if a < epsilon():
        return IntersectResult.REJECT, 0, 0, 0

    f = 1 / a
    s = origin - p0
    u = f * glm.dot(s, q)
    if u < 0.0:
        return IntersectResult.REJECT, 0, 0, 0

    r = glm.dot(s, edge_1)
    v = f * glm.dot(dir, r)
    if v < 0.0 or u + v > 1.0:
        return IntersectResult.REJECT, 0, 0, 0

    t = f * glm.dot(edge_2, r)
    if t < 0:  # Behind ray dir
        return IntersectResult.REJECT, 0, 0, 0

    return IntersectResult.INTERSECT, u, v, t
