import math
import os
import time

from glm import vec3
from OpenGL import GL
from OpenGL.GL.glget import glGetString

from compsoft.core.engine import Engine
from compsoft.graphics.infrastructure.render_pass import RenderPass
from compsoft.graphics.materials.light_material import LightMaterial
from compsoft.graphics.materials.material import Material
from compsoft.resources.manager import resources
from compsoft.scene.actor import Actor
from compsoft.scene.components.cone import SimpleConeComponent
from compsoft.scene.components.cube import SimpleCubeComponent
from compsoft.scene.components.cylinder import SimpleCylinderComponent
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
    t = time.time_ns()

    engine = Engine()

    vendor = glGetString(GL.GL_VENDOR)
    renderer = glGetString(GL.GL_RENDERER)
    if isinstance(vendor, bytes) and isinstance(renderer, bytes):
        print(f"Vendor:   {vendor.decode('utf-8')}")
        print(f"Renderer: {renderer.decode('utf-8')}")

    scene = engine.scene
    scene.load()
    # scene.debug.add_flag(DebugFlags.DEBUG_MESH_AABB)
    scene.camera.pos = vec3(0, 7, 0)
    scene.camera.look_at(vec3(5, 10, 5))

    mat = Material(resources.get_texture_path("mc_dirt.png"))

    actor = scene.add_actor(Actor())
    cube = actor.add_component(SimpleCubeComponent(mat))
    cube.load()
    cube.scale = vec3(100, 1, 100)

    suzanne = scene.add_actor(Actor())
    suzanne.position = vec3(5, 10, 5)
    suzanne.rotation = vec3(0, 180, 0)
    suzanne_mesh = suzanne.add_component(
        ModelMeshComponent(resources.get_model_path("suzanne.obj"), mat)
    )
    suzanne_mesh.load()

    light_actor = scene.add_actor(Actor())
    light_cube = light_actor.add_component(
        SimpleCubeComponent(
            LightMaterial(resources.get_texture_path("mc_dirt.png"))
        )
    )
    light_actor.position = vec3(0, 10, 0)
    light_cube.RENDER_PASS = RenderPass.FORWARD
    light_actor.add_component(PointLight()).intensity = 5
    light_cube.load()

    cone_actor = scene.add_actor(Actor())
    cone_actor.position = vec3(5, 5, 0)
    cone_actor.add_component(SimpleConeComponent(mat)).load()

    cylinder_actor = scene.add_actor(Actor())
    cylinder_actor.position = vec3(10, 2, 0)
    cylinder_actor.add_component(SimpleCylinderComponent(mat)).load()

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
        light_actor.position = vec3(
            math.cos(math.radians(t / 10)) * 10,
            10,
            math.sin(math.radians(t / 10)) * 10,
        )

    engine._add_prerender_listener(tick)

    print(f"Started in {round((time.time_ns() - t) / 1e6)}ms")

    engine.start()
    engine.exit()


if __name__ == "__main__":
    main()
