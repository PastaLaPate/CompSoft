from pathlib import Path
from typing import NamedTuple


class ShaderPair(NamedTuple):
    vertex: Path
    fragment: Path


class ResourceManager:
    def __init__(self, root_dir: Path | None = None) -> None:
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = Path(root_dir).resolve()

        self.assets_dir = self.root_dir / "assets"
        if not self.assets_dir.exists() or not self.assets_dir.is_dir():
            self.assets_dir.unlink(True)
            self.assets_dir.mkdir()

        self.models_dir = self.assets_dir / "models"
        self.shaders_dir = self.assets_dir / "shaders"
        self.textures_dir = self.assets_dir / "textures"

    def get_model_path(self, path: str | Path) -> Path:
        path = (self.models_dir / path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        return path

    def get_texture_path(self, path: str | Path) -> Path:
        path = (self.textures_dir / path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Texture file not found: {path}")
        return path

    def get_shader_path(self, folder: str) -> ShaderPair:
        shaders_folder = self.shaders_dir / folder
        vert_path = shaders_folder / "vertex.glsl"
        frag_path = shaders_folder / "fragment.glsl"

        if not vert_path.exists():
            raise FileNotFoundError(f"Vertex shader not found: {vert_path}")
        if not frag_path.exists():
            raise FileNotFoundError(f"Fragment shader not found: {frag_path}")

        return ShaderPair(vertex=vert_path, fragment=frag_path)


resources = ResourceManager()
