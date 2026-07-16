from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from compsoft.scene import Scene


class Actor:
    def __init__(self, name="Actor") -> None:
        self.name: str = name
        self.id: UUID | None = None
        self.scene: Scene | None = None

        self.parent: Actor | None = None  # Top Level
        self.children: list[Actor] = []

    def add_child(self, child: "Actor") -> None:
        if child.parent is not None:  # Orphan if had already parent
            child.parent.remove_child(child)

        child.parent = self
        self.children.append(child)

        if self.scene is not None:
            child.set_scene(self.scene)

    def remove_child(self, child: "Actor") -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            # Leaving the parent means leaving the scene, orphan it completely
            child.set_scene(None)

    def set_scene(self, scene):
        """Recursively propagates scene registration down the subtree."""
        if self.scene == scene:  # Abandon if same scene
            return

        # Orphan from old scene
        if self.scene is not None and scene is None:
            self.scene.unregister_actor(self)

        self.scene = scene

        # Register on the new scene
        if self.scene is not None:
            self.scene.register_actor(self)

        # Do same for children
        for child in self.children:
            child.set_scene(scene)
