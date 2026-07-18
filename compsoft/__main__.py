from collections import deque

import glfw
from glm import vec3

from compsoft.actor import Actor
from compsoft.camera import Camera
from compsoft.camera_controls import CameraControls
from compsoft.components.cube import SimpleCubeComponent
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

    actor = scene.add_actor(Actor())
    cube = actor.add_component(
        SimpleCubeComponent(
            Material(ROOT / "textures" / "mc_dirt.png"),
        )
    )
    cube.load()

    suzanne = scene.add_actor(Actor())
    suzanne.position = vec3(10, 10, 10)
    suzanne_mesh = actor.add_component(
        ModelMeshComponent(
            ROOT / "models" / "suzanne.obj",
            Material(ROOT / "textures" / "mc_dirt.png"),
        )
    )
    suzanne_mesh.load()

    controls = CameraControls(cam, window)
    frame_times = deque(maxlen=60)

    print("\n")  # Create initial line space

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

        # Go up and clear
        print("\033[A")
        print("\033[K")
        print(f"{avg_ms:6.2f} ms | {fps:7.1f} FPS", end="\r")

        controls.update(window.dt)
        scene.render(window.aspect_ratio)
        window.swap_buffers()
        window.poll_events()
