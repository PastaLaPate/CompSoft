import ast
import re
from pathlib import Path
from typing import ClassVar

from OpenGL.GL import (
    GL_FRAGMENT_SHADER,
    GL_VERTEX_SHADER,
    glDeleteProgram,
    shaders,
)
from OpenGL.GL.shaders import ShaderCompilationError


def _extract_driver_log(raw_error: Exception) -> str:
    """Pull a cleanly decoded driver log out of a GL error, avoiding
    the repr()-induced backslash-escaping that str(exception) causes
    on bytes objects."""
    args = getattr(raw_error, "args", ())
    message = str(args[0]) if args else str(raw_error)

    match = re.search(r"b(['\"]).*?\1", message, re.DOTALL)
    if match:
        try:
            raw_bytes = ast.literal_eval(match.group(0))
            decoded = raw_bytes.decode("utf-8", errors="replace")
            message = message[: match.start()] + decoded + message[match.end() :]
        except (ValueError, SyntaxError):
            pass  # fall back to the raw message if it doesn't parse cleanly

    return message


def _format_shader_error(shader_path: Path, raw_error: Exception, source: str) -> str:
    """Build a compiler-style diagnostic report with line numbers."""
    driver_log = _extract_driver_log(raw_error)

    # Match NVIDIA '0(13)', AMD/Mesa '0:13', or generic 'line 13' line numbers
    match = re.search(r"(?:0[\(\:]|line\s+)(\d+)", driver_log, re.IGNORECASE)
    err_line = int(match.group(1)) if match else None

    # Format source code with line numbers and a pointer on the broken line
    lines = source.splitlines()
    formatted_lines = []
    for idx, line in enumerate(lines, start=1):
        if err_line and idx == err_line:
            formatted_lines.append(f"  > {idx:4d} | {line}")
        else:
            formatted_lines.append(f"    {idx:4d} | {line}")

    source_code_block = "\n".join(formatted_lines)

    return (
        f"\n{'=' * 68}\n"
        f"SHADER COMPILATION FAILED\n"
        f"File: {shader_path}\n"
        f"{'-' * 68}\n"
        f"Driver Output:\n  {driver_log}\n"
        f"{'-' * 68}\n"
        f"Source Code:\n{source_code_block}\n"
        f"{'=' * 68}"
    )


class ShaderRegistry:
    _cache: ClassVar[
        dict[tuple[str, str], int]
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
            vert_shader = shaders.compileShader(vert_source, GL_VERTEX_SHADER)
        except ShaderCompilationError as e:
            raise ShaderCompilationError(
                _format_shader_error(vert_path, e, vert_source)
            ) from None

        try:
            frag_shader = shaders.compileShader(frag_source, GL_FRAGMENT_SHADER)
        except ShaderCompilationError as e:
            raise ShaderCompilationError(
                _format_shader_error(frag_path, e, frag_source)
            ) from None

        try:
            return shaders.compileProgram(vert_shader, frag_shader)
        except ShaderCompilationError as e:
            raise ShaderCompilationError(
                f"\nLink failure ({vert_path.name} + {frag_path.name}):\n{e}"
            ) from None

    @classmethod
    def remove_cache_for_program(cls, program_id: int):
        for i in cls._cache:
            del cls._cache[i]
            break

    @classmethod
    def clear_cache(cls):
        """Useful when reloading a scene or shutting down the engine."""
        for prog_id in cls._cache.values():
            glDeleteProgram(prog_id)
        cls._cache.clear()
