from compsoft.actor import Actor
import uuid
from compsoft.camera import Camera


class Scene:
    def __init__(self, camera: Camera) -> None:
        self.camera = camera
        self.root_actors: list = []
        self.registry: dict[uuid.UUID, Actor] = {}

    def add_actor(self, actor: Actor) -> None:
        if actor.parent is None:
            self.root_actors.append(actor)
        actor.set_scene(self)

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
        pass
