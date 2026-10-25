"""
engine.py — Scene state: voxel grid, 3D objects, cursor, camera.

The SceneEngine holds the canonical scene_state dict and exposes methods
to rebuild the voxel list when the object orientation changes.
"""
import math
import threading
import time
import numpy as np
from typing import Dict, Tuple

from simulator.config import Config
from simulator.math_utils import quat_rotate, quat_normalize

# RGB color type alias
Color = Tuple[int, int, int]


class SceneEngine:
    """
    Manages the 3D voxel scene.

    scene_state (dict) is the shared mutable state read by the renderer
    and written by InputProcessor + SceneEngine.  Access is protected by
    `self.lock` (threading.Lock).
    """

    def __init__(self, config: Config):
        self.cfg = config
        self.lock = threading.Lock()

        # ── Shared scene state dict ───────────────────────────────────────────
        self.state: dict = {
            # Cursor (grid coords, float)
            "cursor_x":        float(config.grid_w // 2),
            "cursor_y":        float(config.grid_h // 2),
            # Camera
            "cam_dist":        config.cam_dist_default,
            # Object orientation
            "object_q":        np.array([1.0, 0.0, 0.0, 0.0]),
            # Button state
            "buttons":         0,
            "btn_left_click":  False,
            "btn_right_click": False,
            # Connection stats
            "connected":       False,
            "packet_rate":     0.0,
            "packet_loss_pct": 0.0,
            "latency_ms":      0.0,
        }

        # ── Object geometry (unrotated, relative to grid centre) ──────────────
        self._object_name = "cube"
        self._raw_voxels: list = []          # list of (x, y, z, r, g, b)
        self._build_object("cube")

        # ── Rendered voxel cache (world-space, recomputed on orientation change)
        self.voxels: Dict[Tuple[int,int,int], Color] = {}
        self._last_object_q = None
        self._recompute_voxels()

    # ── Object builders ────────────────────────────────────────────────────────

    def _build_object(self, name: str):
        """Populate self._raw_voxels with the chosen object's geometry."""
        self._object_name = name
        self._raw_voxels  = []

        if name == "cube":
            self._raw_voxels = _make_wire_cube(size=12)
        elif name == "sphere":
            self._raw_voxels = _make_wire_sphere(radius=9)
        elif name == "pyramid":
            self._raw_voxels = _make_wire_pyramid(size=12)

    def cycle_object(self):
        """Switch to the next available object."""
        order = ["cube", "sphere", "pyramid"]
        idx   = (order.index(self._object_name) + 1) % len(order)
        self._build_object(order[idx])
        self._recompute_voxels(force=True)

    # ── Voxel cache recomputation ──────────────────────────────────────────────

    def _recompute_voxels(self, force: bool = False):
        """
        Apply the current object_q rotation to all raw voxels and rebuild
        self.voxels.  Only runs when object_q has actually changed.
        """
        obj_q = self.state["object_q"]

        if not force and self._last_object_q is not None:
            if np.allclose(obj_q, self._last_object_q, atol=1e-5):
                return  # nothing to do

        self._last_object_q = obj_q.copy()
        W, H, D = self.cfg.grid_w, self.cfg.grid_h, self.cfg.grid_d
        cx, cy, cz = W // 2, H // 2, D // 2

        new_voxels: Dict[Tuple[int,int,int], Color] = {}
        for (rx, ry, rz, r, g, b) in self._raw_voxels:
            v  = np.array([rx, ry, rz], dtype=float)
            rv = quat_rotate(obj_q, v)
            gx = cx + int(round(rv[0]))
            gy = cy + int(round(rv[1]))
            gz = cz + int(round(rv[2]))
            if 0 <= gx < W and 0 <= gy < H and 0 <= gz < D:
                new_voxels[(gx, gy, gz)] = (r, g, b)

        self.voxels = new_voxels

    # ── Per-frame update ───────────────────────────────────────────────────────

    def tick(self):
        """
        Called every render frame.  Recomputes voxels if the object_q changed
        (rotate mode updates it continuously via InputProcessor).
        """
        with self.lock:
            self._recompute_voxels()


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _make_wire_cube(size: int = 12):
    """Wireframe cube: edges only, centred at origin. Returns [(x,y,z,r,g,b)]."""
    half = size // 2
    voxels = set()

    def edge_x(y, z):
        for x in range(-half, half + 1):
            voxels.add((x, y, z))

    def edge_y(x, z):
        for y in range(-half, half + 1):
            voxels.add((x, y, z))

    def edge_z(x, y):
        for z in range(-half, half + 1):
            voxels.add((x, y, z))

    for y in (-half, half):
        for z in (-half, half):
            edge_x(y, z)
    for x in (-half, half):
        for z in (-half, half):
            edge_y(x, z)
    for x in (-half, half):
        for y in (-half, half):
            edge_z(x, y)

    result = []
    for (x, y, z) in voxels:
        # Colour: gradient along Z axis
        t = (z + half) / (size or 1)
        r = int(30  + t * 60)
        g = int(120 + t * 135)
        b = int(220 - t * 60)
        result.append((x, y, z, r, g, b))
    return result


def _make_wire_sphere(radius: int = 9):
    """Wireframe sphere: voxels on the surface. Returns [(x,y,z,r,g,b)]."""
    voxels = {}
    r2 = radius * radius
    lo = (radius - 1) ** 2

    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                d2 = x*x + y*y + z*z
                if lo <= d2 <= r2:
                    t  = (z + radius) / (2 * radius + 1)
                    rv = int(200 + t * 55)
                    gv = int(80  + t * 100)
                    bv = int(255 - t * 80)
                    voxels[(x, y, z)] = (rv, gv, bv)

    return [(x, y, z, r, g, b) for (x, y, z), (r, g, b) in voxels.items()]


def _make_wire_pyramid(size: int = 12):
    """Wireframe square pyramid. Returns [(x,y,z,r,g,b)]."""
    half  = size // 2
    voxels = set()

    # Base square
    for x in range(-half, half + 1):
        for z in range(-half, half + 1):
            if abs(x) == half or abs(z) == half:
                voxels.add((x, -half, z))

    # Four edges to apex
    apex_y = half
    for t in range(size + 1):
        frac = t / size
        for (bx, bz) in [(-half, -half), (half, -half), (-half, half), (half, half)]:
            x = int(round(bx * (1 - frac)))
            y = int(round(-half + size * frac))
            z = int(round(bz * (1 - frac)))
            voxels.add((x, y, z))

    result = []
    for (x, y, z) in voxels:
        t  = (y + half) / (size or 1)
        r  = int(255 - t * 100)
        g  = int(180 - t * 80)
        b  = int(50  + t * 50)
        result.append((x, y, z, r, g, b))
    return result
