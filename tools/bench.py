"""Fixed-frame benchmark for the demo scene.

Runs `compsoft.__main__.main()` for a fixed number of frames at a configurable
window size / shadow resolution and prints the profiler table to stdout, so
changes can be compared without eyeballing the live table. Optionally freezes the
scene animation and writes a PNG of the final frame, which makes it possible to
diff two builds pixel by pixel and prove an optimisation is visually neutral.

    uv run python tools/bench.py
    BENCH_W=1280 BENCH_H=720 BENCH_FRAMES=300 uv run python tools/bench.py
    BENCH_SHADOW_RES=2 uv run python tools/bench.py
    BENCH_FREEZE=1 BENCH_SHOT=/tmp/after.png uv run python tools/bench.py

Env knobs:
    BENCH_W, BENCH_H     render size, default 1920x1080
    BENCH_FRAMES         frames to render, default 200
    BENCH_SHADOW_RES     ShadowFrameBuffer resolution multiplier, default 5
    BENCH_FREEZE         1 to skip prerender listeners (static scene, for diffs)
    BENCH_SHOT           path of a PNG to write for the final frame
    BENCH_NO_DEBUG       1 to enable no debug flags (no timers, no wireframes)
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, cast

WIDTH = int(os.environ.get("BENCH_W") or "1920")
HEIGHT = int(os.environ.get("BENCH_H") or "1080")
FRAMES = int(os.environ.get("BENCH_FRAMES") or "200")
SHADOW_RES = float(os.environ.get("BENCH_SHADOW_RES") or "5")
FREEZE = os.environ.get("BENCH_FREEZE") == "1"
NO_DEBUG = os.environ.get("BENCH_NO_DEBUG") == "1"
SHOT = os.environ.get("BENCH_SHOT")

import compsoft.core.debug as debug_mod
import compsoft.core.engine as engine_mod
import compsoft.core.window as window_mod
from compsoft.core.debug import Profiler
from compsoft.graphics.infrastructure.frame_buffers.shadows_frame_buffer import (
    ShadowFrameBuffer,
)


def _capture_on_last_frame(window_cls: type[Any]) -> None:
    import numpy as np
    from OpenGL.GL import GL_PACK_ALIGNMENT, glPixelStorei, glReadPixels
    from PIL import Image

    shot_path = SHOT or "bench_frame.png"
    original_swap = window_cls.swap_buffers

    def swap_buffers(self):
        self._bench_frame = getattr(self, "_bench_frame", 0) + 1
        if self._bench_frame == FRAMES:
            glPixelStorei(GL_PACK_ALIGNMENT, 1)
            # GL_RGB / GL_UNSIGNED_BYTE
            raw = bytes(glReadPixels(0, 0, WIDTH, HEIGHT, 0x1907, 0x1401))
            pixels = np.frombuffer(raw, np.uint8).reshape(HEIGHT, WIDTH, 3)
            Image.fromarray(pixels[::-1]).save(shot_path)
            print(f"# wrote {shot_path}", flush=True)
        return original_swap(self)

    window_cls.swap_buffers = swap_buffers


def _patch() -> None:
    window_init = window_mod.Window.__init__

    def bench_window_init(self, w, h, title):
        window_init(self, WIDTH, HEIGHT, title)
        self.size = (WIDTH, HEIGHT)  # the render targets are sized from this

    window_mod.Window.__init__ = bench_window_init

    class BenchShadowFrameBuffer(ShadowFrameBuffer):
        def __init__(self, resolution=1):
            super().__init__(SHADOW_RES)

    engine_mod.ShadowFrameBuffer = cast(Any, BenchShadowFrameBuffer)

    if FREEZE:
        # Static scene: two runs then produce identical pixels.
        engine_mod.Engine._add_prerender_listener = lambda self, listener: None

    if NO_DEBUG:
        debug_mod.Debug.add_flag = lambda self, flag: None

    if SHOT:
        _capture_on_last_frame(window_mod.Window)

    # Keep the live table off stdout: the table is printed once at the end.
    Profiler.summary = lambda self: None

    original_start = engine_mod.Engine.start

    def bench_start(self, max_frames=None):
        started = time.perf_counter()
        original_start(self, max_frames=FRAMES)
        elapsed = time.perf_counter() - started
        print(
            f"# loop {elapsed * 1000:.0f}ms / {FRAMES} frames = "
            f"{FRAMES / elapsed:.1f} fps ({elapsed / FRAMES * 1000:.2f} ms/frame)",
            flush=True,
        )

    engine_mod.Engine.start = bench_start


def main() -> None:
    _patch()
    import compsoft.__main__ as app

    print(
        f"# bench {WIDTH}x{HEIGHT} frames={FRAMES} shadow_res={SHADOW_RES} "
        f"freeze={FREEZE} debug={not NO_DEBUG}",
        flush=True,
    )
    app.main()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
