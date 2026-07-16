import math

import pyglm.glm as glm
from pyglm.glm import vec3


class Camera:
    def __init__(
        self, pos: vec3 | None = None, rot: vec3 | None = None
    ) -> None:
        self._pos = pos or vec3(0, 0, 0)
        self._rot = rot or vec3(0, 0, 0)
        self._fov = 90  # in degrees
        self._near_clipping_plane = 0.1
        self._far_clipping_plane = 300.0

        self._cached_view_matrix = None
        self._dirty_matrix = True

    @classmethod
    def from_pos(cls, pos: vec3):
        return cls(pos=pos)

    @classmethod
    def from_rot(cls, rot: vec3):
        return cls(rot=rot)

    @classmethod
    def from_pos_rot(cls, pos: vec3, rot: vec3):
        return cls(pos=pos, rot=rot)

    @property
    def pos(self) -> vec3:
        return self._pos

    @pos.setter
    def pos(self, pos: vec3):
        if pos != self._pos:
            self._dirty_matrix = True
        self._pos = pos

    @property
    def rot(self) -> vec3:
        return self._rot

    @rot.setter
    def rot(self, rot: vec3):
        if rot != self._rot:
            self._dirty_matrix = True
        self._rot = rot

    @property
    def fov(self) -> int:
        return self._fov

    @fov.setter
    def fov(self, fov: int):
        if fov != self.fov:
            self._dirty_matrix = True
        self._fov = fov

    @property
    def near_clipping_plane(self) -> float:
        return self._near_clipping_plane

    @near_clipping_plane.setter
    def near_clipping_plane(self, near_clipping_plane: float):
        if near_clipping_plane != self.near_clipping_plane:
            self._dirty_matrix = True
        self._near_clipping_plane = near_clipping_plane

    @property
    def far_clipping_plane(self) -> float:
        return self._far_clipping_plane

    @far_clipping_plane.setter
    def far_clipping_plane(self, far_clipping_plane: float):
        if far_clipping_plane != self.far_clipping_plane:
            self._dirty_matrix = True
        self._far_clipping_plane = far_clipping_plane

    @property
    def forward(self) -> vec3:
        """Returns the camera's local forward vector, where it is looking at/direction."""
        pitch = glm.radians(self.rot.x)
        yaw = glm.radians(self.rot.y)

        forward = vec3()
        # Some trigonometry shit
        forward.x = math.cos(pitch) * math.cos(yaw)
        forward.y = math.sin(pitch)
        forward.z = math.cos(pitch) * math.sin(yaw)

        return glm.normalize(forward)

    @property
    def right(self) -> vec3:
        """Returns the camera's local Right vector (perpendicular to both Forward and Up)."""
        return glm.normalize(glm.cross(self.forward, vec3(0, 1, 0)))

    @property
    def up(self) -> vec3:
        """Returns the camera's local Up vector (perpendicular to both Forward and Right)."""
        return glm.normalize(glm.cross(self.right, self.forward))

    @property
    def lookat_target(self) -> vec3:
        return self.pos + self.forward

    def look_at(self, target: glm.vec3):
        direction = target - self.pos

        if glm.length(direction) < 0.0001:
            return

        direction = glm.normalize(direction)

        pitch = glm.asin(direction.y)
        yaw = glm.atan(direction.z, direction.x)

        self.rot = glm.vec3(
            glm.degrees(pitch),
            glm.degrees(yaw),
            0.0,  # Roll (Z) is kept at 0 to keep the camera level with the horizon
        )

    def get_view_matrix(self) -> glm.mat4x4:
        if self._cached_view_matrix is not None and not self._dirty_matrix:
            return self._cached_view_matrix

        self._cached_view_matrix = glm.lookAt(
            self.pos,
            self.lookat_target,
            vec3(0, 1, 0),
        )
        self._dirty_matrix = False
        return self._cached_view_matrix

    def get_projection_matrix(self, aspect_ratio: float) -> glm.mat4x4:
        return glm.perspective(
            glm.radians(self.fov),
            aspect_ratio,  # Aspect Ratio
            0.1,  # Near clipping plane. Keep as big as possible, or you'll get precision issues.
            100,  # Far clipping plane. Keep as little as possible
        )
