from pyglm.glm import vec3

from compsoft.scene.actor import Actor
from compsoft.scene.components.cone import SimpleConeComponent
from compsoft.scene.components.cylinder import SimpleCylinderComponent
from compsoft.scene.gizmos.gizmo_materials import GizmoMaterials


class TranslationGizmo(Actor):
    def __init__(self, name="Gizmo.Translation") -> None:
        super().__init__(name)

        # TODO: Add central point when simple circle component is added
        # central_point

        self.scale = vec3(0.5, 0.5, 0.5)

        x_axis_cylinder = self.add_component(
            SimpleCylinderComponent(
                GizmoMaterials.X_AXIS_MAT, radius=0.05, height=1
            )
        )
        x_axis_cylinder.load()
        x_axis_cylinder.position = vec3(0.5, 0, 0)
        x_axis_cylinder.rotation = vec3(0, 0, 90)

        x_axis_arrow_head = self.add_component(
            SimpleConeComponent(
                GizmoMaterials.X_AXIS_MAT, radius=0.08, height=0.2
            )
        )
        x_axis_arrow_head.load()
        x_axis_arrow_head.position = vec3(1.1, 0, 0)
        x_axis_arrow_head.rotation = vec3(180, 0, 90)

        y_axis_cylinder = self.add_component(
            SimpleCylinderComponent(
                GizmoMaterials.Y_AXIS_MAT, radius=0.05, height=1
            )
        )
        y_axis_cylinder.load()
        y_axis_cylinder.position = vec3(0, 0.5, 0)

        y_axis_arrow_head = self.add_component(
            SimpleConeComponent(
                GizmoMaterials.Y_AXIS_MAT, radius=0.08, height=0.2
            )
        )
        y_axis_arrow_head.load()
        y_axis_arrow_head.position = vec3(0, 1.1, 0)
        y_axis_arrow_head.rotation = vec3(0, 0, 0)

        z_axis_cylinder = self.add_component(
            SimpleCylinderComponent(
                GizmoMaterials.Z_AXIS_MAT, radius=0.05, height=1
            )
        )
        z_axis_cylinder.load()
        z_axis_cylinder.position = vec3(0, 0, 0.5)
        z_axis_cylinder.rotation = vec3(90, 0, 0)

        z_axis_arrow_head = self.add_component(
            SimpleConeComponent(
                GizmoMaterials.Z_AXIS_MAT, radius=0.08, height=0.2
            )
        )
        z_axis_arrow_head.load()
        z_axis_arrow_head.position = vec3(0, 0, 1.1)
        z_axis_arrow_head.rotation = vec3(90, 0, 180)
