import math
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np
from pyglm import glm
from pyglm.glm import vec3, vec4

from compsoft.scene.components.component import Component

if TYPE_CHECKING:
    from compsoft.scene.scene import Scene


class LightType(IntEnum):
    # POINT = 0
    DIRECTIONAL = 1
    SPOT = 2


class LightData:
    """Matches shaders/shaded/fragment.glsl Light struct"""

    LIGHT_DTYPE = np.dtype(
        [
            ("type", np.int32),
            (
                "_pad0",
                np.int32,
                3,
            ),  # 12 bytes of padding to push 'position' to byte 16
            ("position", np.float32, 3),  # 12 bytes
            (
                "_pad1",
                np.float32,
                1,
            ),  # 4 bytes of padding to push 'direction' to byte 32
            ("direction", np.float32, 3),  # 12 bytes
            (
                "_pad2",
                np.float32,
                1,
            ),  # 4 bytes of padding to push 'color' to byte 48
            ("color", np.float32, 3),  # 12 bytes, offset = 60 bytes
            ("intensity", np.float32),  # 4 bytes, offset = 64 bytes
            ("cutoff", np.float32),  # 4 bytes, offset = 68 bytes
            (
                "_pad3",
                np.float32,
                3,
            ),  # 12 bytes of trailing padding to round out to 80 bytes total
        ]
    )

    BLOCK_DTYPE = np.dtype(
        [
            ("uLights", LIGHT_DTYPE, 8),
            ("uActiveLightCount", np.int32),
            (
                "_pad_block",
                np.int32,
                3,
            ),  # Pad the final int to a clean 16-byte boundary
        ]
    )

    def __init__(
        self,
        light_type: LightType,
        position: vec3,
        direction: vec3,
        color: vec3,
        intensity: float,
        cutoff: float = 0.0,
    ):
        self.type = light_type
        self.position = position
        self.direction = direction
        self.color = color
        self.intensity = intensity
        self.cutoff = cutoff  # For Spotlights (cosine of angle)

    def to_dtype(self):
        data = np.zeros(1, dtype=self.LIGHT_DTYPE)
        data["type"] = int(self.type)
        data["position"] = self.position
        data["direction"] = self.direction
        data["color"] = self.color
        data["intensity"] = self.intensity
        data["cutoff"] = self.cutoff
        return data

    def __repr__(self):
        return f"Light[type={self.type},pos={self.position}]"


class LightComponent(ABC, Component):
    def on_enter_scene(self, scene: "Scene"):
        self.current_scene = scene
        self.current_scene.register_light(self)

    def on_exit_scene(self):
        if self.current_scene is not None:
            self.current_scene.unregister_light(self)
            self.current_scene = None

    @abstractmethod
    def get_data(self) -> LightData: ...


# TODO: Point light available with https://learnopengl.com/Advanced-Lighting/Shadows/Point-Shadows
"""
class PointLight(LightComponent):
    def __init__(
        self,
        color: vec3 | None = None,
        intensity: float = 1,
        position: vec3 | None = None,
    ):
        super().__init__()
        self.color = color or vec3(1, 1, 1)
        self.intensity = intensity
        self.position = position or vec3(0, 0, 0)

    def get_data(self) -> LightData:
        pos = self.position
        if self.parent:
            wrld_matrix = self.parent.get_world_matrix()
            pos = vec3(wrld_matrix * vec4(pos.x, pos.y, pos.z, 1.0))
        return LightData(
            LightType.POINT,
            pos,
            vec3(0, 0, 0),
            self.color,
            self.intensity,
            0,
        )
        """


class DirectionalLight(LightComponent):
    def __init__(
        self,
        direction: vec3 | None = None,
        color: vec3 | None = None,
        intensity: float = 1,
        position: vec3 | None = None,
    ):
        """Initiates a directional light

        Args:
            direction (vec3, optional): direction of light, in order: roll, pitch, yaw. Defaults to vec3(0, 90, 0).
            color (vec3, optional): color of the light. Defaults to vec3(1, 1, 1).
            intensity (float, optional): intensity of the light. Defaults to 1.
            position (vec3, optional): position relative to parent actor. Defaults to vec3(0, 0, 0).
        """
        super().__init__()
        self.direction = direction or vec3(0, 90, 0)
        self.color = color or vec3(1, 1, 1)
        self.intensity = intensity
        self.position = position or vec3(0, 0, 0)

    def get_data(self) -> LightData:
        pos = self.position
        rotation_quat = glm.quat(glm.radians(self.direction))
        local_forward = rotation_quat * glm.vec3(
            0.0, 0.0, -1.0
        )  # multiply by standard Z- forward
        if self.parent:
            wrld_matrix = self.parent.get_world_matrix()
            pos = vec3(wrld_matrix * vec4(pos.x, pos.y, pos.z, 1.0))
            local_forward = vec3(
                wrld_matrix
                * glm.vec4(local_forward.x, local_forward.y, local_forward.z, 0.0)
            )

        return LightData(
            LightType.DIRECTIONAL,
            pos,
            glm.normalize(vec3(local_forward)),
            self.color,
            self.intensity,
            0,
        )


class SpotLight(LightComponent):
    def __init__(
        self,
        direction: vec3 | None = None,
        angle: float = 30,
        color: vec3 | None = None,
        intensity: float = 1,
        position: vec3 | None = None,
    ):
        super().__init__()
        self.direction = direction or vec3(0, -1, 0)
        self.color = color or vec3(1, 1, 1)
        self.intensity = intensity
        self.position = position or vec3(0, 0, 0)
        self.angle = angle
        self.cutoff = math.cos(math.radians(angle))

    def get_data(self) -> LightData:
        pos = self.position
        dir_vec = self.direction

        if self.parent:
            wrld_matrix = self.parent.get_world_matrix()
            pos = vec3(wrld_matrix * vec4(pos.x, pos.y, pos.z, 1.0))
            dir_vec = vec3(wrld_matrix * vec4(dir_vec.x, dir_vec.y, dir_vec.z, 0.0))
            if glm.length(dir_vec) > 0:
                dir_vec = glm.normalize(dir_vec)

        return LightData(
            LightType.SPOT,
            pos,
            dir_vec,
            self.color,
            self.intensity,
            self.cutoff,
        )
