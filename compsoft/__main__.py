from compsoft.material import Material
from compsoft.components.cube import SimpleCubeComponent
from compsoft.actor import Actor
from compsoft.camera_controls import CameraControls
from compsoft.camera import Camera
from compsoft.scene import Scene
from compsoft.window import Window
import random
import math
from typing import cast
from glm import vec3
import glfw
from pathlib import Path


class COLORS:
    RED = vec3(1, 0, 0)
    GREEN = vec3(0, 1, 0)
    BLUE = vec3(0, 0, 1)

    WHITE = vec3(1, 1, 1)
    BLACK = vec3(0, 0, 0)


ROOT = Path(__file__).resolve().parent.parent


def main():
    print("Welcome...")
    window = Window(800, 600, "CompSoft")
    cam = Camera(vec3(4, 4, 3))
    cam.look_at(vec3(0, 0, 0))
    scene = Scene(cam)

    actor = scene.add_actor(Actor())
    cube = actor.add_component(
        SimpleCubeComponent(
            Material(
                Path(ROOT / "shaders" / "vertex.glsl"),
                Path(ROOT / "shaders" / "fragment.glsl"),
            )
        )
    )
    cube.load()

    controls = CameraControls(cam, window)
    while not window.key_pressed(glfw.KEY_ESCAPE):
        window.clear()
        controls.update(window.dt)
        scene.render(window.aspect_ratio)
        window.swap_buffers()
        window.poll_events()
