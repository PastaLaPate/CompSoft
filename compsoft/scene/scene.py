import uuid

import numpy as np
from glm import mat4
from OpenGL.GL import (
    GL_DYNAMIC_DRAW,
    GL_UNIFORM_BUFFER,
    glBindBuffer,
    glBindBufferBase,
    glBufferData,
    glBufferSubData,
    glGenBuffers,
)

from compsoft.graphics.render_pass import RenderPass
from compsoft.scene.actor import Actor
from compsoft.scene.camera import Camera
from compsoft.scene.components.light import LightComponent, LightData


class Scene:
    def __init__(self, camera: Camera) -> None:
        self.camera = camera

        self.root_actors: list[Actor] = []
        self.registry: dict[uuid.UUID, Actor] = {}
        self.active_lights: list[LightComponent] = []
        self.lights_ubo_id = -1

    def load(self):
        self.lights_ubo_id = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.lights_ubo_id)

        glBufferData(
            GL_UNIFORM_BUFFER,
            LightData.BLOCK_DTYPE.itemsize,
            None,
            GL_DYNAMIC_DRAW,
        )
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

        glBindBufferBase(GL_UNIFORM_BUFFER, 0, self.lights_ubo_id)

    def upload_light_ubo(self, lights: list[LightData]):
        upload_data = np.zeros(1, dtype=LightData.BLOCK_DTYPE)

        light_count = min(len(lights), 8)
        upload_data["u_active_light_count"] = light_count

        for i in range(light_count):
            light_comp = lights[i]

            upload_data["u_lights"][0][i] = light_comp.to_dtype()

        glBindBuffer(GL_UNIFORM_BUFFER, self.lights_ubo_id)
        glBufferSubData(
            GL_UNIFORM_BUFFER, 0, LightData.BLOCK_DTYPE.itemsize, upload_data
        )
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    def add_actor(self, actor: Actor, parent: Actor | None = None) -> Actor:
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
        self.upload_light_ubo(self.get_lights())

    def unregister_light(self, light: LightComponent):
        if light in self.active_lights:
            self.active_lights.remove(light)

        self.upload_light_ubo(self.get_lights())

    def get_lights(self):
        """O(1) fetch for the shader loop. No tree traversal required."""
        return [light.get_data() for light in self.active_lights]

    def render(self, aspect_ratio: float, render_pass: RenderPass):
        for actor in self.root_actors:
            actor.render(aspect_ratio, mat4(), render_pass)  # pass identity
