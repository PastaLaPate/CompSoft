from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pyglm.glm import mat4

if TYPE_CHECKING:
    from compsoft.actor import Actor
    from compsoft.scene import Scene


class Component:
    def __init__(self):
        self._parent: Actor | None = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent: Actor | None):
        self._parent = parent

    def on_enter_scene(self, scene: "Scene"):
        """Triggered when the parent actor enters a scene."""
        pass

    def on_exit_scene(self):
        """Triggered when the parent actor leaves a scene."""
        pass


class RenderableComponent(ABC, Component):
    @abstractmethod
    def load(self): ...

    @abstractmethod
    def unload(self): ...

    @abstractmethod
    def update(self): ...

    @abstractmethod
    def draw(self, aspect_ratio: float, world_model_matrix: mat4): ...
