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


class RayType(Enum):
    Ray = auto()
    Line = auto()
    Segment = auto()


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

    r = glm.cross(s, edge_1)
    v = f * glm.dot(dir, r)
    if v < 0.0 or u + v > 1.0:
        return IntersectResult.REJECT, 0, 0, 0

    t = f * glm.dot(edge_2, r)
    if t < 0:  # Behind ray dir
        return IntersectResult.REJECT, 0, 0, 0

    return IntersectResult.INTERSECT, u, v, t


# Based on https://github.com/juj/MathGeoLib/blob/master/src/Geometry/AABB.cpp#L796 (AABB:IntersectLineAABB_CPP)


def is_near_zero(a: float, eps: float = 1e-9) -> bool:
    return abs(a) < eps


AABB_INTERSECT_T_NEAR_MAP = {
    RayType.Ray: 0,
    RayType.Line: -float("inf"),
    RayType.Segment: 0,
}

AABB_INTERSECT_T_FAR_MAP = {
    RayType.Ray: float("inf"),
    RayType.Line: float("inf"),
}


def ray_aabb_intersect(
    ray: RayTrace,
    aabb: tuple[vec3, vec3],
    ray_type: RayType = RayType.Ray,
    len_: float | None = None,
) -> tuple[IntersectResult, float, float]:
    if ray_type == RayType.Segment and (len_ is None or len_ < 0):
        raise ValueError(
            "Len should be specified if Raytype == RayType.Segment."
        )
    t_near = AABB_INTERSECT_T_NEAR_MAP[ray_type]
    t_far = (
        len_ or 1.0
        if ray_type == RayType.Segment
        else AABB_INTERSECT_T_FAR_MAP[ray_type]
    )
    return ray_aabb_intersect_raw(
        ray.origin, ray.direction, aabb[0], aabb[1], t_near, t_far
    )


def ray_aabb_intersect_raw(
    origin: vec3,
    dir: vec3,
    mins: vec3,
    maxs: vec3,
    t_near: float = 0.0,
    t_far: float = float("inf"),
) -> tuple[IntersectResult, float, float]:
    """
    For Line-AABB:
      t_near = -inf
      t_far  = inf
    For Ray-AABB:
      t_near = 0
      t_far = inf
    For Segment-AABB:
      t_near = 0
      t_far = len(segment)
    """
    for d, o, mn, mx in (
        (dir.x, origin.x, mins.x, maxs.x),
        (dir.y, origin.y, mins.y, maxs.y),
        (dir.z, origin.z, mins.z, maxs.z),
    ):
        res, t_near, t_far = check_intersect_axis(d, o, mn, mx, t_near, t_far)
        if res == IntersectResult.REJECT:
            return IntersectResult.REJECT, t_near, t_far

    return IntersectResult.INTERSECT, t_near, t_far


def check_intersect_axis(
    dir: float,
    origin: float,
    min_: float,
    max_: float,
    t_near: float,
    t_far: float,
) -> tuple[IntersectResult, float, float]:
    if not is_near_zero(dir):
        reciprocal_dir = 1 / dir
        t1 = (min_ - origin) * reciprocal_dir
        t2 = (max_ - origin) * reciprocal_dir

        if t1 > t2:
            t1, t2 = t2, t1
        t_near = max(t1, t_near)
        t_far = min(t2, t_far)

        if t_near > t_far:
            return IntersectResult.REJECT, t_near, t_far
    elif origin < min_ or origin > max_:
        return IntersectResult.REJECT, t_near, t_far

    return IntersectResult.INTERSECT, t_near, t_far
