import math
from collections import deque
from pathlib import Path

import glfw
from glm import vec3

from compsoft.actor import Actor
from compsoft.camera import Camera
from compsoft.camera_controls import CameraControls
from compsoft.components.cube import SimpleCubeComponent
from compsoft.components.light import PointLight
from compsoft.components.model_mesh import ModelMeshComponent
from compsoft.consts import ROOT
from compsoft.material import Material
from compsoft.scene import Scene
from compsoft.window import Window


class COLORS:
    RED = vec3(1, 0, 0)
    GREEN = vec3(0, 1, 0)
    BLUE = vec3(0, 0, 1)

    WHITE = vec3(1, 1, 1)
    BLACK = vec3(0, 0, 0)


def main():
    print("Welcome...")
    window = Window(800, 600, "CompSoft")
    cam = Camera(vec3(4, 4, 3))
    cam.look_at(vec3(0, 0, 0))
    scene = Scene(cam)
    scene.load()

    mat = Material(
        ROOT / "textures" / "mc_dirt.png",
    )

    actor = scene.add_actor(Actor())
    cube = actor.add_component(SimpleCubeComponent(mat))
    cube.load()
    cube.scale = vec3(100, 1, 100)

    suzanne = scene.add_actor(Actor())
    suzanne.position = vec3(10, 10, 10)
    suzanne_mesh = suzanne.add_component(
        ModelMeshComponent(ROOT / "models" / "suzanne.obj", mat)
    )
    suzanne_mesh.load()

    light_actor = scene.add_actor(Actor())
    light_cube = light_actor.add_component(SimpleCubeComponent(mat))
    light_actor.add_component(PointLight()).intensity = 5
    light_cube.load()

    hq_mat = Material(
        Path(
            "/home/alex/Documents/CompositionSoftware/textures/Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_High_4K_albedo.jpeg"
        ),
        Path(
            "/home/alex/Documents/CompositionSoftware/textures/Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_High_4K_normal.jpeg"
        ),
    )

    hq_actor = scene.add_actor(Actor())
    hq_actor.position = vec3(0, 5, 0)
    hq_mesh = hq_actor.add_component(
        ModelMeshComponent(
            Path(
                "/home/alex/Documents/CompositionSoftware/models/Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_High.gltf"
            ),
            hq_mat,
        )
    )
    # hq_mesh.scale = vec3(0.0001, 0.0001, 0.0001)
    hq_mesh.load()

    controls = CameraControls(cam, window)
    frame_times = deque(maxlen=1500)
    t = 0

    while (
        not window.key_pressed(glfw.KEY_ESCAPE) and not window.should_close()
    ):
        window.clear()

        # Track time in ms
        dt_ms = window.dt * 1000
        frame_times.append(dt_ms)

        # Calculate metrics
        avg_ms = sum(frame_times) / len(frame_times)
        fps = 1000.0 / avg_ms

        # Goofy huh
        print(f"\x1b[1K\r{avg_ms:6.2f} ms | {fps:7.1f} FPS", end="")

        controls.update(window.dt)

        t += window.dt * 100
        mat.light_pos = vec3(
            math.cos(math.radians(t)) * 10, 10, math.sin(math.radians(t)) * 10
        )
        light_actor.position = mat.light_pos
        scene.render(window.aspect_ratio)
        window.swap_buffers()
        window.poll_events()
