from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from glm import mat4x4
from pyglm.glm import mat4

from compsoft.graphics.infrastructure.render_pass import RenderPass

if TYPE_CHECKING:
    from compsoft.scene.actor import Actor
    from compsoft.scene.scene import Scene


class Component:
    def __init__(self):
        self._parent: Actor | None = None

    @property
    def parent(self) -> Actor | None:
        return self._parent

    @parent.setter
    def parent(self, parent: Actor | None):
        self._parent = parent

    def on_enter_scene(self, scene: Scene):
        """Triggered when the parent actor enters a scene."""

    def on_exit_scene(self):
        """Triggered when the parent actor leaves a scene."""


class RenderableComponent(ABC, Component):
    RENDER_PASS: RenderPass = RenderPass.DEFERRED

    @abstractmethod
    def load(self): ...

    @abstractmethod
    def unload(self): ...

    @abstractmethod
    def update(self): ...

    @abstractmethod
    def draw(self, aspect_ratio: float, world_model_matrix: mat4): ...

    @abstractmethod
    def draw_depth(
        self, light_view_projection: mat4x4, world_model_matrix: mat4x4
    ): ...
