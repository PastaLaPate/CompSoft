import uuid
from typing import Optional

from glm import mat4

from compsoft.actor import Actor
from compsoft.camera import Camera
from compsoft.components.light import LightComponent


class Scene:
    def __init__(self, camera: Camera) -> None:
        self.camera = camera

        self.root_actors: list[Actor] = []
        self.registry: dict[uuid.UUID, Actor] = {}
        self.active_lights: list[LightComponent] = []

    def add_actor(self, actor: Actor, parent: Optional[Actor] = None) -> Actor:
        if parent:
            parent.add_child(actor)
        else:
            # Prevent duplicates if it was previously root
            if actor not in self.root_actors:
                self.root_actors.append(actor)
            actor.set_scene(self)
        return actor

    def remove_actor(self, actor: Actor):
        if actor in self.root_actors:
            self.root_actors.remove(actor)
        actor.set_scene(None)

    def register_actor(self, actor: Actor):
        """Internal callback to register an actor when added to the scene."""
        if actor.id is None:
            actor.id = uuid.uuid4()  # Assign an id
        self.registry[actor.id] = actor
        print(f"Registered {actor.name} (ID: {actor.id})")

    def unregister_actor(self, actor: Actor):
        """Internal callback to unregister an actor."""
        if actor.id and actor.id in self.registry:
            del self.registry[actor.id]
            print(f"Unregistered {actor.name} (ID: {actor.id})")

    def register_light(self, light: LightComponent):
        if light not in self.active_lights:
            self.active_lights.append(light)

    def unregister_light(self, light: LightComponent):
        if light in self.active_lights:
            self.active_lights.remove(light)

    def get_lights(self):
        """O(1) fetch for the shader loop. No tree traversal required."""
        return [light.get_data() for light in self.active_lights]

    def render(self, aspect_ratio: float):
        for actor in self.root_actors:
            actor.render(aspect_ratio, mat4())  # pass identity
