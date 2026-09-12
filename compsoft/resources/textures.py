from pathlib import Path
from typing import ClassVar

from OpenGL.GL import (
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_NEAREST,
    GL_RGB,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBindTexture,
    glDeleteTextures,
    glGenerateMipmap,
    glGenTextures,
    glTexImage2D,
    glTexParameteri,
)
from PIL import Image
from PIL.Image import Transpose
from pyglm.glm import vec3, vec4


class TextureRegistry:
    _cache: ClassVar[dict[str, int]] = {}  # texture_path: texture_id
    _solid_cache: ClassVar[
        dict[tuple[int, int, int, int], int]
    ] = {}  # tuple(r, g, b, a): texture_id
    _default_normal: int = -1

    @classmethod
    def get_texture(cls, txt: Path) -> int:

        key = str(txt.resolve())

        if key in cls._cache:
            return cls._cache[key]

        print(f"Registering textures, txt: {key}")
        txt_id = cls._load_from_file(txt)
        cls._cache[key] = txt_id
        return txt_id

    @classmethod
    def get_default_normal(cls) -> int:
        if cls._default_normal == -1:
            id = cls._generate_normal_texture()
            cls._default_normal = id
        return cls._default_normal

    @classmethod
    def get_solid_color(
        cls,
        color: vec3
        | vec4
        | tuple[int, int, int]
        | tuple[int, int, int, int]
        | tuple[float, float, float]
        | tuple[float, float, float, float],
    ):
        if isinstance(color, (vec3, vec4)):
            raw_vals = [color.x, color.y, color.z]
            if isinstance(color, vec4):
                raw_vals.append(color.w)
        else:
            raw_vals = list(color)

        if isinstance(raw_vals[0], float):
            r, g, b = [int(x * 255) for x in raw_vals[:3]]
            a = int(raw_vals[3] * 255) if len(raw_vals) == 4 else 255
        else:
            r, g, b = [int(x) for x in raw_vals[:3]]
            a = int(raw_vals[3]) if len(raw_vals) == 4 else 255

        key: tuple[int, int, int, int] = (r, g, b, a)
        if key in cls._solid_cache:
            return cls._solid_cache[key]
        else:
            id = cls._generate_solid_texture(vec4(r, g, b, a))
            cls._solid_cache[key] = id
            return id

    @classmethod
    def _generate_normal_texture(cls) -> int:
        return cls._generate_solid_texture(vec4(128, 128, 255, 255))

    @classmethod
    def _generate_solid_texture(cls, color: vec3 | vec4) -> int:
        r, g, b = int(color.x), int(color.y), int(color.z)
        a = int(color.w) if isinstance(color, vec4) else 255

        pixel_data = bytes([r, g, b, a])

        txt_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, txt_id)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            1,
            1,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            pixel_data,
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)
        return txt_id

    @classmethod
    def _load_from_file(cls, txt: Path) -> int:
        if not txt.exists():
            raise FileNotFoundError(f"Texture file missing at: {txt}")

        img = Image.open(txt)
        img = img.transpose(Transpose.FLIP_TOP_BOTTOM)

        img_data = img.convert("RGB").tobytes()
        width, height = img.size

        txt_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, txt_id)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,  # Mipmap level
            GL_RGB,  # GPU Repr
            width,
            height,
            0,  # border
            GL_RGB,  # Source
            GL_UNSIGNED_BYTE,
            img_data,
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)
        return txt_id

    @classmethod
    def clear_cache(cls):
        """Useful when reloading a scene or shutting down the engine."""
        for txt_id in cls._cache.values():
            glDeleteTextures(1, [txt_id])
        cls._cache.clear()
