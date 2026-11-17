from __future__ import annotations

import ctypes
import re
from collections import defaultdict
from collections.abc import Callable
from typing import Final

from OpenGL.error import Error as OpenGLError
from OpenGL.GL import (
    GL_EXTENSIONS,
    GL_NO_ERROR,
    GL_NUM_EXTENSIONS,
    GL_QUERY_RESULT,
    GL_QUERY_RESULT_AVAILABLE,
    GL_TIME_ELAPSED,
    GL_VERSION,
    glBeginQuery,
    glDeleteQueries,
    glEndQuery,
    glGenQueries,
    glGetError,
    glGetIntegerv,
    glGetQueryObjectiv,
    glGetQueryObjectui64v,
    glGetQueryObjectuiv,
    glGetString,
    glGetStringi,
)

# Extension-only constant, not exported by OpenGL.GL.
GL_GPU_DISJOINT_EXT: Final = 0x8FBB

# Driver/PyOpenGL failures that mean "this query is not usable here".
_GL_ERRORS: Final = (OpenGLError, ctypes.ArgumentError, TypeError)

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)")


def _gl_version() -> tuple[int, int]:
    raw = glGetString(GL_VERSION)
    if not raw:
        return (0, 0)
    match = _VERSION_RE.match(raw.decode("ascii", "replace"))
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def _extensions() -> set[bytes]:
    try:
        count = int(glGetIntegerv(GL_NUM_EXTENSIONS))
    except _GL_ERRORS:
        return set()
    return {
        ext for i in range(count) if (ext := glGetStringi(GL_EXTENSIONS, i)) is not None
    }


def _drain_errors() -> None:
    while glGetError() != GL_NO_ERROR:
        pass


def _supports_timer_queries(extensions: set[bytes]) -> bool:
    # GL_TIME_ELAPSED and glGetQueryObjectui64v are core in 3.3; on 3.x
    # contexts ARB_timer_query provides the same entry points.
    return _gl_version() >= (3, 3) or b"GL_ARB_timer_query" in extensions


def _probe_timer_queries(extensions: set[bytes]) -> bool:
    """Reject drivers that advertise the version but not the query targets."""
    if not _supports_timer_queries(extensions):
        return False
    _drain_errors()
    try:
        query = _first_int(glGenQueries(1))
        glBeginQuery(GL_TIME_ELAPSED, query)
        glEndQuery(GL_TIME_ELAPSED)
        ok = glGetError() == GL_NO_ERROR
        glDeleteQueries(1, [query])
        return ok
    except _GL_ERRORS:
        return False


def _first_int(value) -> int:
    """PyOpenGL returns single-value GL queries as 1-element arrays."""
    try:
        return int(value[0])
    except (TypeError, IndexError):
        return int(value)


def _gpu_disjoint() -> bool:
    out = (ctypes.c_int * 1)()
    glGetIntegerv(GL_GPU_DISJOINT_EXT, out)
    return out[0] != 0


class GpuTimerQueries:
    """A small per-pass pool of timer queries.

    Query objects are allocated once per pass name and recycled, so steady
    state does no allocation and never calls glFinish/glGetQueryObject(..,
    GL_QUERY_RESULT) before the result is actually available.
    """

    POOL_SIZE: Final = 4
    MAX_LATENCY_FRAMES: Final = 8

    def __init__(self) -> None:
        extensions = _extensions()
        self.supported = _probe_timer_queries(extensions)
        self._disjoint_ext = b"GL_EXT_disjoint_timer_query" in extensions
        self._free: dict[str, list[int]] = defaultdict(list)
        self._created: dict[str, int] = defaultdict(int)
        self._all_ids: list[int] = []
        self._in_flight: list[tuple[str, int, int]] = []
        self._frame = 0
        # Reused output buffers: no ctypes allocation per query read.
        self._avail_buf = (ctypes.c_int * 1)()
        self._result_buf = (ctypes.c_uint64 * 1)()
        self._result32_buf = (ctypes.c_uint * 1)()

    def _available(self, query: int) -> bool:
        glGetQueryObjectiv(query, GL_QUERY_RESULT_AVAILABLE, self._avail_buf)
        return self._avail_buf[0] != 0

    def _result_ns(self, query: int) -> int:
        try:
            glGetQueryObjectui64v(query, GL_QUERY_RESULT, self._result_buf)
            return int(self._result_buf[0])
        except _GL_ERRORS:
            # Some PyOpenGL builds do not wrap the 64-bit variant.
            try:
                glGetQueryObjectuiv(query, GL_QUERY_RESULT, self._result32_buf)
                return int(self._result32_buf[0])
            except _GL_ERRORS:
                return -1

    def acquire(self, name: str) -> int:
        """Begin a timed region. Returns 0 when no query is available."""
        if not self.supported:
            return 0

        pool = self._free[name]
        if not pool:
            if self._created[name] >= self.POOL_SIZE:
                return 0
            query = _first_int(glGenQueries(1))
            self._created[name] += 1
            self._all_ids.append(query)
            pool.append(query)

        query = pool.pop()
        try:
            glBeginQuery(GL_TIME_ELAPSED, query)
        except _GL_ERRORS:
            pool.append(query)
            return 0
        return query

    def release(self, name: str, query: int) -> None:
        """End a timed region started by :meth:`acquire`."""
        if not query:
            return
        try:
            glEndQuery(GL_TIME_ELAPSED)
        except _GL_ERRORS:
            self._free[name].append(query)
            return
        self._in_flight.append((name, query, self._frame))

    def harvest(self, record: Callable[[str, float], None]) -> None:
        """Collect finished queries and hand timings to ``record`` in ms.

        Queries complete in submission order, so the scan stops at the first
        one that is not ready: steady state is a single availability check.
        """
        self._frame += 1
        if not self._in_flight:
            return

        if self._disjoint_ext and _gpu_disjoint():
            for name, query, _ in self._in_flight:
                self._free[name].append(query)
            self._in_flight.clear()
            return

        consumed = 0
        for name, query, frame in self._in_flight:
            if self._available(query):
                elapsed_ns = self._result_ns(query)
                if elapsed_ns >= 0:
                    record(name, elapsed_ns / 1_000_000.0)
                self._free[name].append(query)
            elif self._frame - frame > self.MAX_LATENCY_FRAMES:
                # Driver never resolved it; reclaim rather than starve the pool.
                self._free[name].append(query)
            else:
                break
            consumed += 1

        if consumed:
            del self._in_flight[:consumed]

    def destroy(self) -> None:
        if self._all_ids:
            glDeleteQueries(len(self._all_ids), self._all_ids)
            self._all_ids.clear()
        self._free.clear()
        self._created.clear()
        self._in_flight.clear()
