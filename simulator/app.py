"""
app.py — Main entry point for the 3D Monitor Simulator.

Runs two concurrent asyncio tasks:
  1. UDP receive loop  — receives packets, updates scene state (SIM-1)
  2. Render loop       — reads scene state, writes terminal frame at cfg.fps

A non-blocking keyboard poller provides a fallback control interface
when no phone is connected (Phase 2 requirement).

Usage:
    python simulator/app.py [--port 9000] [--fps 30]
"""
import asyncio
import sys
import os
import json
import time
import signal
import argparse
import threading
import numpy as np

# ── Adjust sys.path so the package is importable when run directly ─────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.config import Config
from simulator.net.receiver import start_receiver
from simulator.net.protocol import SensorSample
from simulator.input.processor import InputProcessor
from simulator.scene.engine import SceneEngine
from simulator.render.renderer import Renderer
from simulator.math_utils import euler_to_quat


# ── Keyboard helper (non-blocking, cross-platform) ────────────────────────────
if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

class KeyboardPoller:
    """Non-blocking single-character keyboard reader."""

    def __init__(self):
        self._old_settings = None

    def start(self):
        if os.name != "nt":
            fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

    def stop(self):
        if os.name != "nt" and self._old_settings:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._old_settings)

    def read_char(self) -> str:
        """Return a char if one is waiting, else empty string."""
        if os.name == "nt":
            if msvcrt.kbhit():
                return msvcrt.getwch()
        elif select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return ""


# ── App ───────────────────────────────────────────────────────────────────────

class App:
    def __init__(self, cfg: Config):
        self.cfg       = cfg
        self.scene     = SceneEngine(cfg)
        self.processor = InputProcessor(cfg)
        self.renderer  = Renderer(cfg)
        self.keyboard  = KeyboardPoller()
        self._running  = True
        self._protocol = None   # set after receiver starts

        # Keyboard-driven virtual sample state (for fallback control)
        self._kb_yaw: float   = 0.0
        self._kb_pitch: float = 0.0
        self._kb_rotate       = False

    # ── Packet callback ────────────────────────────────────────────────────────

    def _on_sample(self, sample: SensorSample):
        """Called from asyncio event loop — must be fast (SIM-1)."""
        dt = 1.0 / self.cfg.fps   # approximate; good enough for input
        with self.scene.lock:
            self.processor.process(sample, self.scene.state, dt)

    # ── Render task ───────────────────────────────────────────────────────────

    async def _render_loop(self):
        frame_duration = 1.0 / self.cfg.fps
        while self._running:
            t0 = asyncio.get_event_loop().time()

            self.scene.tick()

            proto_stats = {
                "connected":       False,
                "packet_rate":     0.0,
                "packet_loss_pct": 0.0,
            }
            if self._protocol:
                proto_stats["connected"]       = self._protocol.connected
                proto_stats["packet_rate"]     = self._protocol.packet_rate
                proto_stats["packet_loss_pct"] = self._protocol.packet_loss_pct

                # Update scene state connectivity flag
                with self.scene.lock:
                    self.scene.state["connected"] = self._protocol.connected

            self.renderer.render(self.scene, proto_stats)

            elapsed = asyncio.get_event_loop().time() - t0
            sleep   = max(0.0, frame_duration - elapsed)
            await asyncio.sleep(sleep)

    # ── Keyboard task ─────────────────────────────────────────────────────────

    async def _keyboard_loop(self):
        """Poll keyboard ~60 Hz and synthesise virtual SensorSamples."""
        _seq    = 0
        _start  = time.monotonic()

        while self._running:
            ch = self.keyboard.read_char()

            if ch:
                ch_lower = ch.lower()

                if ch_lower == 'q':
                    self._running = False
                    break
                elif ch_lower == 'c':
                    # Recenter
                    q = euler_to_quat(self._kb_yaw, self._kb_pitch)
                    self.processor.recenter(q)
                elif ch_lower == 'o':
                    self.scene.cycle_object()
                elif ch_lower == 'r':
                    self._kb_rotate = not self._kb_rotate
                elif ch_lower == 'w':
                    self._kb_pitch = min(self.cfg.fov_pitch, self._kb_pitch + 2.0)
                elif ch_lower == 's':
                    self._kb_pitch = max(-self.cfg.fov_pitch, self._kb_pitch - 2.0)
                elif ch_lower == 'a':
                    self._kb_yaw = max(-self.cfg.fov_yaw, self._kb_yaw - 2.0)
                elif ch_lower == 'd':
                    self._kb_yaw = min(self.cfg.fov_yaw, self._kb_yaw + 2.0)
                elif ch in ('+', '='):
                    with self.scene.lock:
                        self.scene.state["cam_dist"] = max(
                            self.cfg.cam_dist_min,
                            self.scene.state["cam_dist"] - 3.0)
                elif ch == '-':
                    with self.scene.lock:
                        self.scene.state["cam_dist"] = min(
                            self.cfg.cam_dist_max,
                            self.scene.state["cam_dist"] + 3.0)

                # Build and inject a synthetic sample from keyboard state
                if not self._kb_rotate:
                    q = euler_to_quat(self._kb_yaw, self._kb_pitch)
                    buttons = 0
                else:
                    # In rotate mode, simulate small incremental yaw
                    q = euler_to_quat(self._kb_yaw, self._kb_pitch)
                    buttons = 0x0010  # ROTATE held

                ts = int((time.monotonic() - _start) * 1000)
                sample = SensorSample(
                    seq          = _seq & 0xFFFF,
                    timestamp_ms = ts,
                    buttons      = buttons,
                    q            = q,
                    gyro         = np.zeros(3),
                    acc          = np.zeros(3),
                )
                _seq += 1
                self._on_sample(sample)

            await asyncio.sleep(1.0 / 60)

    # ── Main ──────────────────────────────────────────────────────────────────

    async def run(self):
        self.renderer.setup()
        self.keyboard.start()

        try:
            self._protocol = await start_receiver(
                on_sample  = self._on_sample,
                host       = self.cfg.host,
                port       = self.cfg.port,
                timeout_ms = self.cfg.timeout_ms,
            )

            await asyncio.gather(
                self._render_loop(),
                self._keyboard_loop(),
            )
        finally:
            self.keyboard.stop()
            self.renderer.teardown()


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> Config:
    p = argparse.ArgumentParser(
        description="3D Monitor Simulator — receive phone sensor data and render a 3D LED grid."
    )
    p.add_argument("--port", type=int,   default=9000,  help="UDP listen port (default 9000)")
    p.add_argument("--fps",  type=int,   default=30,    help="Render framerate (default 30)")
    p.add_argument("--grid", type=int,   default=32,    help="Voxel grid size N (N×N×N, default 32)")
    p.add_argument("--host", type=str,   default="0.0.0.0", help="Bind host (default 0.0.0.0)")
    args = p.parse_args()

    cfg           = Config()
    cfg.port      = args.port
    cfg.fps       = args.fps
    cfg.grid_w    = args.grid
    cfg.grid_h    = args.grid
    cfg.grid_d    = args.grid
    cfg.host      = args.host
    return cfg


def main():
    cfg = parse_args()
    app = App(cfg)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _sigint(sig, frame):
        app._running = False

    signal.signal(signal.SIGINT, _sigint)
    signal.signal(signal.SIGTERM, _sigint)

    try:
        loop.run_until_complete(app.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
