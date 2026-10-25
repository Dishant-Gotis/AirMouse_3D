"""
config.py — All tunable parameters for the 3D Monitor Simulator.
Edit this file (or pass CLI args via app.py) to change behaviour.
"""
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class Config:
    # ── Network ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"        # bind to all interfaces (SIM-2)
    port: int = 9000             # default UDP port (open item resolved)
    timeout_ms: float = 2000.0   # mark disconnected after this many ms of silence (SIM-4)

    # ── Voxel grid ─────────────────────────────────────────────────────────────
    grid_w: int = 32
    grid_h: int = 32
    grid_d: int = 32

    # ── Rendering ──────────────────────────────────────────────────────────────
    fps: int = 30                # render loop target framerate (NFR-2)

    # ── Input / mapping ────────────────────────────────────────────────────────
    fov_yaw: float = 30.0        # degrees of yaw that span full grid width   (Section 6.5)
    fov_pitch: float = 30.0      # degrees of pitch that span full grid height
    smoothing_alpha: float = 0.35 # EMA weight for smoothed cursor [0.2–0.6]  (Section 6.5)
    dead_zone_deg: float = 0.25  # ignore orientation changes smaller than this (Section 6.5)
    zoom_speed: float = 8.0      # grid units per second when zoom button held
    cam_dist_default: float = 55.0
    cam_dist_min: float = 18.0
    cam_dist_max: float = 110.0

    # ── Colors (R, G, B) ───────────────────────────────────────────────────────
    cursor_color: Tuple[int, int, int] = (255, 90, 0)    # bright orange crosshair
    grid_wire_color: Tuple[int, int, int] = (25, 25, 50) # dim bounding box
    bg_color: Tuple[int, int, int] = (0, 0, 0)
