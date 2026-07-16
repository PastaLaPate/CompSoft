from pathlib import Path
from OpenGL.GL import (
    shaders,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    glDeleteProgram,
)


class ShaderRegistry:
    _cache: dict[
        tuple[str, str], int
    ] = {}  # (vertex_shader_path, fragment_shader_path): program_id

    @classmethod
    def get_program(cls, vtx_path: Path, fgt_path: Path) -> int:
        key = (str(vtx_path), str(fgt_path))

        if key in cls._cache:
            return cls._cache[key]

        print(f"Compiling new shader prog, v: {vtx_path}, f: {fgt_path}")
        program_id = cls._compile_from_files(vtx_path, fgt_path)
        cls._cache[key] = program_id
        return program_id

    @classmethod
    def _compile_from_files(cls, vert_path: Path, frag_path: Path) -> int:
        if not vert_path.exists():
            raise FileNotFoundError(f"Vertex shader missing: {vert_path}")
        if not frag_path.exists():
            raise FileNotFoundError(f"Fragment shader missing: {frag_path}")

        with open(vert_path, "r") as v_file:
            vert_source = v_file.read()

        with open(frag_path, "r") as f_file:
            frag_source = f_file.read()

        try:
            program = shaders.compileProgram(
                shaders.compileShader(vert_source, GL_VERTEX_SHADER),
                shaders.compileShader(frag_source, GL_FRAGMENT_SHADER),
            )
            return program
        except Exception as e:
            # If you have a syntax error in your GLSL, this will print the exact line
            raise RuntimeError(
                f"Shader compilation failed for {vert_path} / {frag_path}:\n{e}"
            )

    @classmethod
    def clear_cache(cls):
        """Useful when reloading a scene or shutting down the engine."""
        for prog_id in cls._cache.values():
            glDeleteProgram(prog_id)
        cls._cache.clear()
