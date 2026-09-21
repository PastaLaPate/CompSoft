from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, cast
from uuid import UUID

from pyglm import glm
from pyglm.glm import mat4x4, vec3

from compsoft.graphics.infrastructure.render_pass import RenderPass
from compsoft.scene.components.component import Component, RenderableComponent

if TYPE_CHECKING:
    from compsoft.scene.scene import Scene


class Actor:
    def __init__(self, name="Actor") -> None:
        self.name: str = name
        self.id: UUID | None = None
        self.components: list[Component] = []
        self._components_by_type: dict[type[Component], list[Component]] = (
            defaultdict(list)
        )
        self.scene: Scene | None = None

        self.parent: Actor | None = None  # Top Level
        self.children: list[Actor] = []

        self._position = glm.vec3(0.0, 0.0, 0.0)
        self._rotation = glm.vec3(
            0.0, 0.0, 0.0
        )  # Euler angles (pitch, yaw, roll) in degrees
        self._scale = glm.vec3(1.0, 1.0, 1.0)

        self.t_matrix: mat4x4 | None = None
        self.dirty_matrix = True
        self._world_matrix: mat4x4 | None = None
        self._dirty_world = True

    # Children and scene management

    def add_child(self, child: Actor) -> Actor:
        if child.parent is not None:  # Orphan if had already parent
            child.parent.remove_child(child)

        child.parent = self
        self.children.append(child)

        if self.scene is not None:
            child.set_scene(self.scene)
        child._invalidate_world()
        return child

    def remove_child(self, child: Actor) -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            # Leaving the parent means leaving the scene, orphan it completely
            child.set_scene(None)
            child._invalidate_world()

    def clear_children(self) -> None:
        for child in list(self.children):
            self.remove_child(child)

    def set_scene(self, scene):
        """Recursively propagates scene registration down the subtree."""
        if self.scene == scene:  # Abandon if same scene
            return

        # Orphan from old scene
        if self.scene is not None and scene is None:
            for comp in self.components:
                comp.on_exit_scene()
            self.scene.unregister_actor(self)

        self.scene = scene

        # Register on the new scene
        if self.scene is not None:
            self.scene.register_actor(self)
            for comp in self.components:
                comp.on_enter_scene(self.scene)

        # Do same for children
        for child in self.children:
            child.set_scene(scene)

    # Component

    def add_component[T: Component](self, component: T) -> T:
        self.components.append(component)
        component.parent = self
        if self.scene is not None:
            component.on_enter_scene(self.scene)
        for cls in type(component).__mro__:
            if issubclass(cls, Component):
                self._components_by_type[cls].append(component)
        return component

    def remove_component(self, component: Component):
        if component not in self.components:
            return
        if self.scene is not None:
            component.on_exit_scene()
        component.parent = None
        self.components.remove(component)
        for cls in type(component).__mro__:
            if issubclass(cls, Component):
                self._components_by_type[cls].remove(component)

    def clear_components(self):
        for component in list(self.components):
            self.remove_component(component)

    def get_component_by_type[T: Component](
        self, component_cls: type[T]
    ) -> T | None:
        """Gets first component of the type `component_cls`

        Args:
            component_cls (type[T]): The class of component to fetch

        Returns:
            _type_: A T component instance.
        """
        comps = self._components_by_type.get(component_cls)
        return cast(T, comps[0]) if comps else None

    def get_components_by_type[T: Component](
        self, component_cls: type[T]
    ) -> list[T]:
        return cast(list[T], self._components_by_type.get(component_cls, []))

    # Transform

    def _invalidate(self) -> None:
        self.dirty_matrix = True
        self._invalidate_world()

    def _invalidate_world(self) -> None:
        if self._dirty_world:
            return
        self._dirty_world = True
        for child in self.children:
            child._invalidate_world()

    @property
    def position(self) -> vec3:
        return self._position

    @position.setter
    def position(self, x: vec3):
        if x != self._position:
            self._invalidate()
        self._position = x

    @property
    def scale(self) -> vec3:
        return self._scale

    @scale.setter
    def scale(self, x: vec3):
        if x != self._scale:
            self._invalidate()
        self._scale = x

    @property
    def rotation(self) -> vec3:
        return self._rotation

    @rotation.setter
    def rotation(self, x: vec3):
        if x != self._rotation:
            self._invalidate()
        self._rotation = x

    # Rendering

    def compute_transform_matrix(self) -> glm.mat4x4:
        if self.t_matrix is not None and not self.dirty_matrix:
            return self.t_matrix
        identity = glm.mat4(1.0)

        quat = glm.quat(glm.radians(self.rotation))
        rot: glm.mat4x4 = glm.mat4_cast(quat)
        scale: glm.mat4x4 = glm.scale(identity, self.scale)
        translate: glm.mat4x4 = glm.translate(identity, self.position)
        m = cast(glm.mat4x4, translate * rot * scale)
        self.t_matrix = m
        self.dirty_matrix = False
        return m

    # Walk up tree, shouldnt be used during the render itself as it already has parent_matrix
    def get_world_matrix(self) -> glm.mat4x4:
        if not self._dirty_world and self._world_matrix is not None:
            return self._world_matrix
        local_matrix = self.compute_transform_matrix()
        if self.parent is not None:
            self._world_matrix = cast(
                mat4x4, self.parent.get_world_matrix() * local_matrix
            )
        else:
            self._world_matrix = local_matrix
        self._dirty_world = False
        return self._world_matrix

    def render(
        self,
        aspect_ratio: float,
        render_pass: RenderPass,
        light_view_projection: mat4x4 | None = None,
    ):
        for r_comp in self.get_components_by_type(RenderableComponent):
            if render_pass == r_comp.RENDER_PASS:
                r_comp.draw(aspect_ratio, self.get_world_matrix())
            elif (
                render_pass == RenderPass.SHADOW
                and r_comp.RENDER_PASS
                == RenderPass.DEFERRED  # Dont render lights
                and light_view_projection is not None
            ):
                r_comp.draw_depth(
                    light_view_projection, self.get_world_matrix()
                )

        for child in self.children:
            child.render(
                aspect_ratio,
                render_pass,
                light_view_projection=light_view_projection,
            )
