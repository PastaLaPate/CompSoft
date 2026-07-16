from __future__ import annotations
from pyglm.glm import mat4
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from compsoft.actor import Actor


class Component:
    def __init__(self):
        self.parent: Actor | None = None


class RenderableComponent(ABC, Component):
    @abstractmethod
    def load(self): ...

    @abstractmethod
    def unload(self): ...

    @abstractmethod
    def update(self): ...

    @abstractmethod
    def draw(self, aspect_ratio: float, mvp: mat4): ...
