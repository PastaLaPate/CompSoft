import math
import os
import time

from glm import vec3
from OpenGL import GL
from OpenGL.GL.glget import glGetString
from pyglm.glm import normalize

from compsoft.core.engine import Engine
from compsoft.graphics.infrastructure.render_pass import RenderPass
from compsoft.graphics.materials.light_material import LightMaterial
from compsoft.graphics.materials.material import Material
from compsoft.resources.manager import resources
from compsoft.scene.actor import Actor
from compsoft.scene.components.cone import SimpleConeComponent
from compsoft.scene.components.cube import SimpleCubeComponent
from compsoft.scene.components.cylinder import SimpleCylinderComponent
from compsoft.scene.components.light import SpotLight
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


def smooth_noise(t: float, seed: float) -> float:
    """Combines sines at different frequencies for natural, organic motion."""
    return (
        math.sin(t * 0.8 + seed) * 0.5
        + math.sin(t * 1.9 + seed * 1.3) * 0.3
        + math.sin(t * 3.7 + seed * 2.1) * 0.2
    )


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
    # scene.debug.add_flag(DebugFlags.DEBUG_SELECTION_RAYCAST)
    scene.camera.pos = vec3(0, 7, 0)
    scene.camera.look_at(vec3(5, 10, 5))

    mat = Material(resources.get_texture_path("mc_dirt.png"))

    actor = scene.add_actor(Actor())
    cube = actor.add_component(SimpleCubeComponent(mat))
    # actor.add_component(DirectionalLight(vec3(0, -1, 0), intensity=0.15))
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
        SimpleCubeComponent(LightMaterial(resources.get_texture_path("mc_dirt.png")))
    )
    light_actor.position = vec3(0, 10, 0)
    light_cube.RENDER_PASS = RenderPass.FORWARD
    light_comp = light_actor.add_component(SpotLight())
    light_comp.intensity = 5
    light_comp.color = vec3(1, 0, 0)
    light_cube.load()

    light_actor2 = scene.add_actor(Actor())
    light_cube2 = light_actor2.add_component(
        SimpleCubeComponent(LightMaterial(resources.get_texture_path("mc_dirt.png")))
    )
    light_cube2.RENDER_PASS = RenderPass.FORWARD
    light_comp2 = light_actor2.add_component(SpotLight())
    light_comp2.intensity = 5
    light_comp2.color = vec3(0, 0, 1)
    light_cube2.load()

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
    hq_actor.rotation = vec3(0, 180, 0)
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
        light_actor.rotation = vec3(
            smooth_noise(t / 100, 1.0) * 180,
            smooth_noise(t / 100, 10.0) * 180,
            smooth_noise(t / 100, 20.0) * 180,
        )
        light_comp.direction = normalize(-light_actor.position)

        light_actor2.position = vec3(
            -math.cos(math.radians(t / 10)) * 10,
            10,
            -math.sin(math.radians(t / 10)) * 10,
        )
        light_actor2.rotation = vec3(
            smooth_noise(t / 100, 1.0) * 180,
            smooth_noise(t / 100, 10.0) * 180,
            smooth_noise(t / 100, 20.0) * 180,
        )
        light_comp2.direction = normalize(-light_actor2.position)

    engine._add_prerender_listener(tick)

    print(f"Started in {round((time.time_ns() - t) / 1e6)}ms")

    engine.start()
    engine.exit()


if __name__ == "__main__":
    main()
