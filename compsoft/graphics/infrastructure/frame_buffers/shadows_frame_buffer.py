import math
from collections import deque
from typing import cast

from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    GL_NEAREST,
    GL_NONE,
    GL_TEXTURE_2D_ARRAY,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    glBindFramebuffer,
    glBindTexture,
    glClear,
    glDeleteFramebuffers,
    glDeleteTextures,
    glDrawBuffer,
    glEnable,
    glFramebufferTextureLayer,
    glGenFramebuffers,
    glGenTextures,
    glReadBuffer,
    glTexImage3D,
    glTexParameteri,
    glViewport,
)
from pyglm import glm
from pyglm.glm import mat4x4, vec3, vec4

from compsoft.scene.components.light import (
    LightComponent,
    LightData,
    LightType,
)
from compsoft.scene.scene import Scene

MAX_SHADOW_LIGHTS = 8
CASCADES_N = 4

FIT_MARGIN = 0.5  # world units of slack kept around the fitted casters
FIT_EXTENT_QUANTUM = 0.5  # fitted extents round up to this many world units
MIN_FIT_EXTENT = 2.0  # sane floor so one tiny caster can't collapse the box
MIN_NEAR = 0.1
DEFAULT_FAR = 50.0  # fallback far plane, and the directional eye distance
MAX_SPOT_HALF_FOV_DEG = 89.0  # acos() guard for degenerate outer cutoffs

# A depth layer costs width * height * 4 bytes. Past roughly half a gigabyte the
# array stops staying resident on a 6GB card that is also driving the desktop, and
# every depth write in the shadow pass goes over PCIe: 420MB/frame at ~7GB/s is
# ~60ms instead of ~0.6ms. Warn instead of silently collapsing to 2 fps.
SHADOW_VRAM_WARN_BYTES = 512 * 1024 * 1024


class ShadowFrameBuffer:
    """Depth-only 2D texture array with one shadow map per light.

    Layers are allocated on demand: the array starts with a single layer and grows
    by doubling when another shadow-casting light registers. Sizing it eagerly for
    MAX_SHADOW_LIGHTS wastes most of the VRAM for scenes that use two or three
    lights - at 5120x5120 the unused layers alone are half a gigabyte.
    """

    def __init__(self, resolution: float = 1, max_layers: int = MAX_SHADOW_LIGHTS):
        self.width = int(1024 * resolution)
        self.height = int(1024 * resolution)
        self.max_layer = max_layers

        # Bound to the light component, not to its current data: moving lights used
        # to insert a fresh entry in the value-keyed dict every frame. The entry
        # also carries the caster AABBs the matrix was fitted to, since the
        # frustum now follows the content.
        self.matrices_cache: dict[
            LightComponent, tuple[LightData, tuple[tuple[vec3, vec3], ...], mat4x4]
        ] = {}

        self.light_layers: dict[
            LightComponent, int
        ] = {}  # light: texture2d_array layer
        self._available_layers: deque[int] = deque()  # queue of available layers

        self.layer_capacity = 0
        self.shadow_array_tex = 0
        self._allocate_layers(1)

        # Build a new frame buffer
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    @property
    def vram_bytes(self) -> int:
        # 4 bytes per depth sample (GL_DEPTH_COMPONENT is uploaded as float)
        return self.width * self.height * 4 * self.layer_capacity

    def _allocate_layers(self, layers: int) -> None:
        layers = max(1, min(layers, self.max_layer))

        if self.shadow_array_tex:
            glDeleteTextures(1, [self.shadow_array_tex])

        self.shadow_array_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.shadow_array_tex)
        glTexImage3D(
            GL_TEXTURE_2D_ARRAY,
            0,  # Mip level
            GL_DEPTH_COMPONENT,  # GPU Format
            self.width,
            self.height,
            layers,  # depth = layer count
            0,  # legacy
            GL_DEPTH_COMPONENT,  # cpu format
            GL_FLOAT,  # type
            None,  # No data
        )
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

        # Existing layer assignments keep their index; their contents are dropped but
        # every shadow map is re-rendered before it is sampled.
        for layer in range(self.layer_capacity, layers):
            self._available_layers.append(layer)
        self.layer_capacity = layers

        if self.vram_bytes > SHADOW_VRAM_WARN_BYTES:
            mib = self.vram_bytes / (1024 * 1024)
            print(
                f"WARNING: shadow map array is {mib:.0f} MiB "
                f"({self.width}x{self.height} x {layers} layers). Above ~512 MiB it "
                "can stop being resident in VRAM and the shadow pass falls back to "
                "PCIe traffic. Lower ShadowFrameBuffer(resolution=...) or use fewer "
                "shadow-casting lights."
            )

    def get_light_layer(self, light: LightComponent, cascade: int = 0) -> int:
        layer = self.light_layers.get(light)
        if layer is None:
            if not self._available_layers:
                if self.layer_capacity >= self.max_layer:
                    raise RuntimeError("No more shadow texture available")
                self._allocate_layers(self.layer_capacity * 2)
            layer = self._available_layers.popleft()
            self.light_layers[light] = layer
        return layer  # * CASCADES_N + cascade

    def _compute_vp_matrix(
        self,
        light_data: LightData,
        caster_boxes: tuple[tuple[vec3, vec3], ...],
    ) -> mat4x4:
        light_dir = light_data.direction
        if glm.length(light_dir) == 0:
            raise ValueError("Shadow-casting light direction must not be zero")
        light_dir = glm.normalize(light_dir)

        if light_data.type == LightType.DIRECTIONAL:
            light_pos = -light_dir * DEFAULT_FAR
            up = vec3(0, 0, 1) if abs(light_dir.y) > 0.9 else vec3(0, 1, 0)
            light_target = vec3(0, 0, 0)
        else:
            light_pos = light_data.position
            up = (
                vec3(0, 0, 1)
                if abs(glm.dot(light_dir, vec3(0, 1, 0))) > 0.99
                else vec3(0, 1, 0)
            )
            light_target = light_pos + light_dir

        light_view = glm.lookAt(light_pos, light_target, up)

        if light_data.type == LightType.DIRECTIONAL:
            light_projection = self._fit_directional_projection(
                light_view, caster_boxes
            )
        else:
            light_projection = self._fit_spot_projection(
                light_view, light_data, caster_boxes
            )

        return cast(mat4x4, light_projection * light_view)

    @staticmethod
    def _box_corners(box: tuple[vec3, vec3]):
        box_min, box_max = box
        for x in (box_min.x, box_max.x):
            for y in (box_min.y, box_max.y):
                for z in (box_min.z, box_max.z):
                    yield vec3(x, y, z)

    def _fit_directional_projection(
        self,
        light_view: mat4x4,
        caster_boxes: tuple[tuple[vec3, vec3], ...],
    ) -> mat4x4:
        """Square ortho box around the whole caster set, snapped to texels."""
        if not caster_boxes:
            return glm.ortho(-10, 10, -10, 10, MIN_NEAR, DEFAULT_FAR)

        lo: vec3 = vec3(math.inf)
        hi: vec3 = vec3(-math.inf)
        for box in caster_boxes:
            for corner in self._box_corners(box):
                ls = vec3(light_view * vec4(corner.x, corner.y, corner.z, 1.0))
                lo = cast(vec3, glm.min(lo, ls))
                hi = cast(vec3, glm.max(hi, ls))

        # Square, padded, quantized extent: the quantum keeps the texel size
        # (extent / resolution) itself stable across small content changes.
        extent = max(hi.x - lo.x, hi.y - lo.y) + 2.0 * FIT_MARGIN
        extent = max(
            MIN_FIT_EXTENT,
            math.ceil(extent / FIT_EXTENT_QUANTUM) * FIT_EXTENT_QUANTUM,
        )

        # Snap the box centre to whole texels. extent/2 is (width/2) texels, so
        # the left/top edges land on the same light-space grid every frame and
        # shadow edges don't crawl when the camera or the light moves.
        texel = extent / self.width
        center_x = round(((lo.x + hi.x) * 0.5) / texel) * texel
        center_y = round(((lo.y + hi.y) * 0.5) / texel) * texel

        # z bounds: keep the near plane between the eye and the nearest caster.
        near = max(MIN_NEAR, -hi.z - FIT_MARGIN)
        far = max(-lo.z + FIT_MARGIN, near + MIN_FIT_EXTENT)

        return glm.ortho(
            center_x - extent * 0.5,
            center_x + extent * 0.5,
            center_y - extent * 0.5,
            center_y + extent * 0.5,
            near,
            far,
        )

    def _fit_spot_projection(
        self,
        light_view: mat4x4,
        light_data: LightData,
        caster_boxes: tuple[tuple[vec3, vec3], ...],
    ) -> mat4x4:
        """Perspective over the light's cone, near/far fitted to its casters."""
        # Cover the outer cone so the intensity falloff band is shadowed too;
        # fall back to the inner angle when the outer cutoff is unset/degenerate.
        cone_cos = light_data.outer_cutoff
        if not (0.0 < cone_cos < light_data.inner_cutoff):
            cone_cos = light_data.inner_cutoff
        half_fov_deg = min(math.degrees(math.acos(cone_cos)), MAX_SPOT_HALF_FOV_DEG)
        fov = glm.radians(half_fov_deg * 2.0)

        if not caster_boxes:
            return glm.perspective(fov, 1.0, MIN_NEAR, DEFAULT_FAR)

        tan_half = math.tan(math.radians(half_fov_deg))
        near_dist = math.inf
        far_dist = 0.0
        for box in caster_boxes:
            corners = [
                vec3(light_view * vec4(corner.x, corner.y, corner.z, 1.0))
                for corner in self._box_corners(box)
            ]
            # A caster counts when any AABB corner is inside the cone. Casters
            # spanning it without touching it (a cone slicing through a huge
            # ground plane) only ever receive, so clipping them is correct.
            in_cone = any(
                ls.z < -MIN_NEAR and math.hypot(ls.x, ls.y) <= tan_half * -ls.z
                for ls in corners
            )
            if not in_cone:
                continue
            near_dist = min(near_dist, -max(ls.z for ls in corners))
            far_dist = max(far_dist, -min(ls.z for ls in corners))

        if near_dist == math.inf:
            return glm.perspective(fov, 1.0, MIN_NEAR, DEFAULT_FAR)

        near = max(MIN_NEAR, near_dist - FIT_MARGIN)
        far = max(far_dist + FIT_MARGIN, near + MIN_FIT_EXTENT)
        return glm.perspective(fov, 1.0, near, far)

    def render_light(self, light: LightComponent, scene: Scene) -> mat4x4:
        if not light.parent:
            return mat4x4()
        layer = self.get_light_layer(light)

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTextureLayer(
            GL_FRAMEBUFFER,
            GL_DEPTH_ATTACHMENT,
            self.shadow_array_tex,
            0,
            layer,
        )
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_DEPTH_BUFFER_BIT)

        light_data = light.get_data()
        # The frustum follows the casters, so the cache key must include their
        # current AABBs, not just the light's own data.
        caster_boxes = scene.get_shadow_caster_boxes()
        cached = self.matrices_cache.get(light)
        if cached is None or cached[0] != light_data or cached[1] != caster_boxes:
            cached = (
                light_data,
                caster_boxes,
                self._compute_vp_matrix(light_data, caster_boxes),
            )
            self.matrices_cache[light] = cached
        matrix: mat4x4 = cached[2]

        scene.render_shadow_map(matrix)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return matrix

    def release_light(self, light: LightComponent) -> None:
        """Gives the light's layer back so a later light can reuse it."""
        layer = self.light_layers.pop(light, None)
        if layer is not None:
            self._available_layers.append(layer)
        self.matrices_cache.pop(light, None)

    def destroy(self) -> None:
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
            self.fbo = 0
        if self.shadow_array_tex:
            glDeleteTextures(1, [self.shadow_array_tex])
            self.shadow_array_tex = 0
