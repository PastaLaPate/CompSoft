import math
import os

import OpenGL.GL as GL
from glm import vec3
from OpenGL.GL.glget import glGetString

from compsoft.core.engine import Engine
from compsoft.graphics.material import Material
from compsoft.resources.manager import resources
from compsoft.scene.actor import Actor
from compsoft.scene.components.cube import SimpleCubeComponent
from compsoft.scene.components.light import PointLight
from compsoft.scene.components.model_mesh import ModelMeshComponent

# NVIDIA PRIME Offload
os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"

# AMD / Mesa PRIME
os.environ["DRI_PRIME"] = "1"


class COLORS:
    RED = vec3(1, 0, 0)
    GREEN = vec3(0, 1, 0)
    BLUE = vec3(0, 0, 1)

    WHITE = vec3(1, 1, 1)
    BLACK = vec3(0, 0, 0)


def main():
    print("Welcome...")

    engine = Engine()

    vendor = glGetString(GL.GL_VENDOR)
    renderer = glGetString(GL.GL_RENDERER)
    if isinstance(vendor, bytes) and isinstance(renderer, bytes):
        print(f"Vendor:   {vendor.decode('utf-8')}")
        print(f"Renderer: {renderer.decode('utf-8')}")

    scene = engine.scene
    scene.load()

    mat = Material(resources.get_texture_path("mc_dirt.png"))

    actor = scene.add_actor(Actor())
    cube = actor.add_component(SimpleCubeComponent(mat))
    cube.load()
    cube.scale = vec3(100, 1, 100)

    suzanne = scene.add_actor(Actor())
    suzanne.position = vec3(10, 10, 10)
    suzanne_mesh = suzanne.add_component(
        ModelMeshComponent(resources.get_model_path("suzanne.obj"), mat)
    )
    suzanne_mesh.load()

    light_actor = scene.add_actor(Actor())
    light_cube = light_actor.add_component(SimpleCubeComponent(mat))
    light_actor.add_component(PointLight()).intensity = 5
    light_cube.load()

    hq_mat = Material(
        resources.get_texture_path(
            "Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_High_4K_albedo.jpeg"
        ),
        resources.get_texture_path(
            "Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_High_4K_normal.jpeg"
        ),
    )

    hq_actor = scene.add_actor(Actor())
    hq_actor.position = vec3(0, 5, 0)
    hq_mesh = hq_actor.add_component(
        ModelMeshComponent(
            resources.get_model_path(
                "Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_High.gltf"
            ),
            hq_mat,
        )
    )
    # hq_mesh.scale = vec3(0.0001, 0.0001, 0.0001)
    hq_mesh.load()

    def tick(t: float, dt: float):
        mat.light_pos = vec3(
            math.cos(math.radians(t)) * 10, 10, math.sin(math.radians(t)) * 10
        )
        light_actor.position = mat.light_pos

    engine._add_prerender_listener(tick)
    engine.start()
    engine.exit()
