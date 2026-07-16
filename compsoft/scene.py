from typing import cast, Optional
import pyglm.glm as glm
from compsoft.actor import Actor
import uuid
from compsoft.camera import Camera


class Scene:
    def __init__(self, camera: Camera) -> None:
        self.camera = camera
        self.root_actors: list[Actor] = []
        self.registry: dict[uuid.UUID, Actor] = {}

    def add_actor(self, actor: Actor, parent: Optional[Actor] = None) -> Actor:
        if parent:
            parent.add_child(actor)
        else:
            # Prevent duplicates if it was previously root
            if actor not in self.root_actors:
                self.root_actors.append(actor)
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

    def render(self, aspect_ratio: float):
        mvp: glm.mat4x4 = cast(
            glm.mat4x4,
            self.camera.get_projection_matrix(aspect_ratio)
            * self.camera.get_view_matrix(),
        )
        for actor in self.root_actors:
            actor.render(aspect_ratio, mvp)
