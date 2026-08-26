import uuid
from typing import cast

import glm
import numpy as np
from OpenGL.GL import (
    GL_DYNAMIC_DRAW,
    GL_UNIFORM_BUFFER,
    glBindBuffer,
    glBindBufferBase,
    glBufferData,
    glBufferSubData,
    glGenBuffers,
)
from pyglm import glm
from pyglm.glm import mat4, mat4x4, vec2, vec3, vec4

from compsoft.core.debug import Debug
from compsoft.graphics.ray_trace import (
    IntersectResult,
    RayTrace,
    RayType,
    ray_aabb_intersect,
)
from compsoft.graphics.render_pass import RenderPass
from compsoft.scene.actor import Actor
from compsoft.scene.camera import Camera
from compsoft.scene.components.light import LightComponent, LightData
from compsoft.scene.components.mesh import SimpleMeshComponent
from compsoft.scene.gizmos.translation_gizmo import TranslationGizmo


class Scene:
    def __init__(self, camera: Camera) -> None:
        self.camera = camera

        self.root_actors: list[Actor] = []
        self.registry: dict[uuid.UUID, Actor] = {}
        self.active_lights: list[LightComponent] = []
        self.lights_ubo_id = -1

        self.debug = Debug()
        self.debug_rays = []

        self.translation_gizmo = self.add_actor(TranslationGizmo())

    def select_on_click(self, w: int, h: int, pos: vec2):
        ndc_x = (pos.x / w) * 2.0 - 1.0
        ndc_y = (
            1.0 - (pos.y / h) * 2.0
        )  # Y Inverse because opengl decided to render upside down or smth

        ray_start = vec4(ndc_x, ndc_y, -1.0, 1.0)
        ray_end = vec4(ndc_x, ndc_y, 1.0, 1.0)

        inverse_m: mat4x4 = cast(
            mat4x4,
            glm.inverse(
                self.camera.get_projection_matrix(w / h)
                * self.camera.get_view_matrix(),
            ),
        )

        ray_start_world = cast(vec4, inverse_m * ray_start)
        ray_start_world /= ray_start_world.w

        ray_end_world = cast(vec4, inverse_m * ray_end)
        ray_end_world /= ray_end_world.w

        ray_dir = ray_end_world - ray_start_world
        ray_dir = glm.normalize(ray_dir)

        self.debug_rays.append(
            (vec3(ray_start_world), vec3(ray_start_world + 10 * ray_dir))
        )

        all_mesh_components = []

        for actor in self.root_actors:
            all_mesh_components.extend(self.get_mesh_components(actor))

        mesh_components = [
            comp
            for comp in all_mesh_components
            if ray_aabb_intersect(
                RayTrace(vec3(ray_start_world), vec3(ray_dir)),
                comp.get_transformed_bounding_box(),
                RayType.Ray,
            )[0]
            == IntersectResult.INTERSECT
        ]

        # Sort nearest to farthest

        closest_comp: SimpleMeshComponent | None = None
        closest_t = float("inf")
        for comp in mesh_components:
            intersects, t = comp.ray_intersects(
                vec3(ray_start_world), vec3(ray_dir), False
            )
            if intersects and t < closest_t:
                closest_t = t
                closest_comp = comp

        for comp in all_mesh_components:
            comp.selected = False

        if closest_comp and closest_comp.parent:
            print("Selected: ", closest_comp.parent.id)
            closest_comp.selected = True
        else:
            print("Void :/")

    def get_mesh_components(self, actor: Actor) -> list[SimpleMeshComponent]:
        components = []
        components.extend(actor.get_components_by_type(SimpleMeshComponent))

        for child in actor.children:
            components.extend(self.get_mesh_components(child))

        return components

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

        self.debug.load()

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
        if render_pass == RenderPass.FORWARD:
            [self.debug.add_line(*line) for line in self.debug_rays]

            self.debug.draw(
                cast(
                    mat4,
                    self.camera.get_projection_matrix(aspect_ratio)
                    * self.camera.get_view_matrix(),
                )
            )

            self.debug.clear()
