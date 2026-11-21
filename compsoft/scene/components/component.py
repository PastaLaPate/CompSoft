from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pyglm.glm import mat4, vec3

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


class ShadowCasterComponent(RenderableComponent):
    """Renderable that can be rendered into a shadow map."""

    cast_shadow: bool = True

    @abstractmethod
    def draw_depth(self, light_view_projection: mat4, world_model_matrix: mat4): ...

    @abstractmethod
    def get_transformed_bounding_box(self) -> tuple[vec3, vec3] | None:
        """World-space AABB, or None if not drawn yet (no world matrix)."""

    @property
    def casts_shadows(self) -> bool:
        return (
            self.cast_shadow
            and self.RENDER_PASS == RenderPass.DEFERRED
            and self.parent is not None
        )

    def on_enter_scene(self, scene: Scene):
        super().on_enter_scene(scene)
        if self not in scene.shadow_casters:
            scene.shadow_casters.append(self)

    def on_exit_scene(self):
        super().on_exit_scene()
        if self.parent and self.parent.scene:
            casters = self.parent.scene.shadow_casters
            if self in casters:
                casters.remove(self)
