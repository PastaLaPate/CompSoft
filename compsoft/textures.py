from pathlib import Path

from OpenGL.GL import (
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_RGB,
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


class TextureRegistry:
    _cache: dict[str, int] = {}  # texture_path: texture_id

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
        glTexParameteri(
            GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR
        )
        glGenerateMipmap(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)
        return txt_id

    @classmethod
    def clear_cache(cls):
        """Useful when reloading a scene or shutting down the engine."""
        for txt_id in cls._cache.values():
            glDeleteTextures(1, [txt_id])
        cls._cache.clear()
