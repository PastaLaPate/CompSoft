from compsoft.graphics.materials.light_material import LightMaterial
from compsoft.resources.textures import TextureRegistry


class _GizmoMaterialsMeta(type):
    _x_axis_mat = None
    _y_axis_mat = None
    _z_axis_mat = None

    @property
    def X_AXIS_MAT(cls):
        if cls._x_axis_mat is None:
            cls._x_axis_mat = LightMaterial(
                TextureRegistry.get_solid_color((1.0, 0.2, 0.2))
            )
        return cls._x_axis_mat

    @property
    def Y_AXIS_MAT(cls):
        if cls._y_axis_mat is None:
            cls._y_axis_mat = LightMaterial(
                TextureRegistry.get_solid_color((0.2, 1.0, 0.2))
            )
        return cls._y_axis_mat

    @property
    def Z_AXIS_MAT(cls):
        if cls._z_axis_mat is None:
            cls._z_axis_mat = LightMaterial(
                TextureRegistry.get_solid_color((0.2, 0.2, 1.0))
            )
        return cls._z_axis_mat


class GizmoMaterials(metaclass=_GizmoMaterialsMeta):
    pass
