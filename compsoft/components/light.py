import math
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np
from pyglm.glm import vec3

from compsoft.components.component import Component

if TYPE_CHECKING:
    from compsoft.scene import Scene


class LightType(IntEnum):
    DIRECTIONAL = 0
    POINT = 1
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
            ("color", np.float32, 3),  # 12 bytes
            ("intensity", np.float32),  # 4 bytes
            ("cutoff", np.float32),  # 4 bytes
            (
                "_pad3",
                np.float32,
                2,
            ),  # 8 bytes of trailing padding to round out to 80 bytes total
        ]
    )

    BLOCK_DTYPE = np.dtype(
        [
            ("u_lights", LIGHT_DTYPE, 8),
            ("u_active_light_count", np.int32),
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


class PointLight(LightComponent):
    def __init__(
        self,
        color: vec3 = vec3(1, 1, 1),
        intensity: float = 1,
        position: vec3 = vec3(0, 0, 0),
    ):
        super().__init__()
        self.color = color
        self.intensity = intensity
        self.position = position

    def get_data(self) -> LightData:
        return LightData(
            LightType.POINT,
            self.position,
            vec3(0, 0, 0),
            self.color,
            self.intensity,
            0,
        )


class DirectionalLight(LightComponent):
    def __init__(
        self,
        direction: vec3 = vec3(0, 90, 0),
        color: vec3 = vec3(1, 1, 1),
        intensity: float = 1,
        position: vec3 = vec3(0, 0, 0),
    ):
        """Initiates a directional light

        Args:
            direction (vec3, optional): direction of light, in order: roll, pitch, yaw. Defaults to vec3(0, 90, 0).
            color (vec3, optional): color of the light. Defaults to vec3(1, 1, 1).
            intensity (float, optional): intensity of the light. Defaults to 1.
            position (vec3, optional): position relative to parent actor. Defaults to vec3(0, 0, 0).
        """
        super().__init__()
        self.direction = direction
        self.color = color
        self.intensity = intensity
        self.position = position

    def get_data(self) -> LightData:
        return LightData(
            LightType.DIRECTIONAL,
            self.position,
            self.direction,
            self.color,
            self.intensity,
            0,
        )


class SpotLight(LightComponent):
    def __init__(
        self,
        direction: vec3 = vec3(0, 90, 0),
        angle: float = 30,
        color: vec3 = vec3(1, 1, 1),
        intensity: float = 1,
        position: vec3 = vec3(0, 0, 0),
    ):
        super().__init__()
        self.direction = direction
        self.color = color
        self.intensity = intensity
        self.position = position
        self.cutoff = math.cos(math.radians(angle))

    def get_data(self) -> LightData:
        return LightData(
            LightType.SPOT,
            self.position,
            self.direction,
            self.color,
            self.intensity,
            self.cutoff,
        )
