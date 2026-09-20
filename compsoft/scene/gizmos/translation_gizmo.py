from pyglm.glm import vec3

from compsoft.scene.actor import Actor
from compsoft.scene.components.cone import SimpleConeComponent
from compsoft.scene.components.cylinder import SimpleCylinderComponent
from compsoft.scene.components.sphere import SimpleSphereComponent
from compsoft.scene.gizmos.axes import Axis
from compsoft.scene.gizmos.gizmo_materials import GizmoMaterials


class TranslationGizmo(Actor):
    def __init__(self, name="Gizmo.Translation") -> None:
        super().__init__(name)

        self.selected_actor: Actor | None = None

        self.scale = vec3(0.5, 0.5, 0.5)

        central_point = self.add_component(
            SimpleSphereComponent(GizmoMaterials.CENTER_POINT_MAT, radius=0.1)
        )
        central_point.load()
        central_point.position = vec3(0, 0, 0)

        x_axis_cylinder = self.add_component(
            SimpleCylinderComponent(
                GizmoMaterials.X_AXIS_MAT, radius=0.05, height=1
            )
        )
        x_axis_cylinder.load()
        x_axis_cylinder.position = vec3(0.5, 0, 0)
        x_axis_cylinder.rotation = vec3(0, 0, 90)
        self.x_axis_cylinder = x_axis_cylinder

        x_axis_arrow_head = self.add_component(
            SimpleConeComponent(
                GizmoMaterials.X_AXIS_MAT, radius=0.08, height=0.2
            )
        )
        x_axis_arrow_head.load()
        x_axis_arrow_head.position = vec3(1.1, 0, 0)
        x_axis_arrow_head.rotation = vec3(180, 0, 90)
        self.x_axis_arrow_head = x_axis_arrow_head

        y_axis_cylinder = self.add_component(
            SimpleCylinderComponent(
                GizmoMaterials.Y_AXIS_MAT, radius=0.05, height=1
            )
        )
        y_axis_cylinder.load()
        y_axis_cylinder.position = vec3(0, 0.5, 0)
        self.y_axis_cylinder = y_axis_cylinder

        y_axis_arrow_head = self.add_component(
            SimpleConeComponent(
                GizmoMaterials.Y_AXIS_MAT, radius=0.08, height=0.2
            )
        )
        y_axis_arrow_head.load()
        y_axis_arrow_head.position = vec3(0, 1.1, 0)
        y_axis_arrow_head.rotation = vec3(0, 0, 0)
        self.y_axis_arrow_head = y_axis_arrow_head

        z_axis_cylinder = self.add_component(
            SimpleCylinderComponent(
                GizmoMaterials.Z_AXIS_MAT, radius=0.05, height=1
            )
        )
        z_axis_cylinder.load()
        z_axis_cylinder.position = vec3(0, 0, 0.5)
        z_axis_cylinder.rotation = vec3(90, 0, 0)
        self.z_axis_cylinder = z_axis_cylinder

        z_axis_arrow_head = self.add_component(
            SimpleConeComponent(
                GizmoMaterials.Z_AXIS_MAT, radius=0.08, height=0.2
            )
        )
        z_axis_arrow_head.load()
        z_axis_arrow_head.position = vec3(0, 0, 1.1)
        z_axis_arrow_head.rotation = vec3(90, 0, 180)
        self.z_axis_arrow_head = z_axis_arrow_head

    @Actor.position.setter
    def position(self, pos: vec3):
        Actor.position.fset(self, pos)
        if self.selected_actor is not None:
            self.selected_actor.position = pos

    def select_axis(self, axis: Axis):
        self.unselect_axes()
        thickness_factor = 1.4
        components = self.get_axis_components(axis)
        for comp in components:
            comp.material = GizmoMaterials.SELECTED_AXIS_MAT
            comp.scale = vec3(thickness_factor, 1, thickness_factor)

    def unselect_axes(self):
        for axis, mat in [
            (Axis.X, GizmoMaterials.X_AXIS_MAT),
            (Axis.Y, GizmoMaterials.Y_AXIS_MAT),
            (Axis.Z, GizmoMaterials.Z_AXIS_MAT),
        ]:
            for comp in self.get_axis_components(axis):
                comp.material = mat
                comp.scale = vec3(1, 1, 1)

    def get_axis_components(
        self, axis: Axis
    ) -> list[SimpleCylinderComponent | SimpleConeComponent]:
        mapping = {
            Axis.X: [self.x_axis_cylinder, self.x_axis_arrow_head],
            Axis.Y: [self.y_axis_cylinder, self.y_axis_arrow_head],
            Axis.Z: [self.z_axis_cylinder, self.z_axis_arrow_head],
        }
        return mapping[axis]
