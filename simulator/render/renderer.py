"""
renderer.py — Projects the 3D voxel scene to a terminal frame.

Technique (Section 10.4):
  1. Apply object rotation (already done by SceneEngine — voxels are in world space).
  2. Perspective-project each voxel onto the 2D pixel grid.
  3. Use a depth buffer so closer voxels occlude farther ones.
  4. Render using half-block characters (▀) with 24-bit fg/bg ANSI colour:
       upper pixel = foreground;  lower pixel = background.
     This doubles the effective vertical resolution.
  5. Draw cursor crosshair on top.
  6. Overlay a HUD (connection status, FPS, packet rate, latency).
  7. Use differential updates: only rewrite cells that changed.
"""
import os
import sys
import time
import numpy as np
from typing import Dict, Tuple

from simulator.config import Config

HALF_BLOCK = "▀"

# ANSI escape helpers
def _rgb_fg(r, g, b): return f"\033[38;2;{r};{g};{b}m"
def _rgb_bg(r, g, b): return f"\033[48;2;{r};{g};{b}m"
_RESET   = "\033[0m"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"
_CLEAR   = "\033[2J\033[H"
def _goto(row, col): return f"\033[{row};{col}H"


class Renderer:
    """
    Stateful renderer.  Call render() once per frame.
    Keeps a previous-frame buffer for differential updates.
    """

    def __init__(self, config: Config):
        self.cfg = config
        self._prev_cells: Dict[Tuple[int,int], str] = {}   # (row,col) → ANSI cell string
        self._frame_count = 0
        self._fps_timer   = time.monotonic()
        self._fps_display = 0.0
        self._initialized = False

    # ── Public API ─────────────────────────────────────────────────────────────

    def setup(self):
        """Call once before the render loop starts."""
        sys.stdout.write(_HIDE_CURSOR + _CLEAR)
        sys.stdout.flush()
        self._initialized = True

    def teardown(self):
        """Call on exit to restore the terminal."""
        sys.stdout.write(_SHOW_CURSOR + _RESET + "\n")
        sys.stdout.flush()

    def render(self, scene_engine, protocol_stats: dict):
        """
        Full render call.  Run at ~cfg.fps.

        `scene_engine`   – SceneEngine instance (reads .voxels and .state)
        `protocol_stats` – dict with keys: connected, packet_rate, packet_loss_pct
        """
        tw, th = _term_size()
        if tw < 20 or th < 6:
            return                           # terminal too small, skip

        # Effective pixel grid (half-blocks double vertical res)
        px_w = tw
        px_h = th * 2

        # ── Build pixel buffer ─────────────────────────────────────────────────
        buf    = np.zeros((px_h, px_w, 3), dtype=np.uint8)
        depth  = np.full((px_h, px_w), np.inf)

        with scene_engine.lock:
            voxels   = scene_engine.voxels
            state    = scene_engine.state
            cam_dist = state["cam_dist"]
            cx_g     = state["cursor_x"]
            cy_g     = state["cursor_y"]
            cz_g     = float(self.cfg.grid_d) / 2.0

        # focal length: chosen so the full grid fits in the pixel area
        f = min(px_w, px_h) * 0.65

        # Pixel-space centre
        cx_px = px_w / 2.0
        cy_px = px_h / 2.0

        half_w = self.cfg.grid_w / 2.0
        half_h = self.cfg.grid_h / 2.0
        half_d = self.cfg.grid_d / 2.0

        # ── Draw voxels ────────────────────────────────────────────────────────
        for (gx, gy, gz), (r, g, b) in voxels.items():
            X = gx - half_w
            Y = gy - half_h
            Z = gz - half_d

            denom = Z + cam_dist
            if denom <= 0.5:
                continue

            sx = int(cx_px + f * X / denom)
            sy = int(cy_px - f * Y / denom)

            if 0 <= sx < px_w and 0 <= sy < px_h:
                if denom < depth[sy, sx]:
                    depth[sy, sx] = denom
                    buf[sy, sx]   = (r, g, b)

        # ── Draw bounding-box wireframe (very dim) ─────────────────────────────
        _draw_grid_box(buf, depth, f, cx_px, cy_px, cam_dist,
                       half_w, half_h, half_d, self.cfg.grid_wire_color)

        # ── Draw cursor crosshair ──────────────────────────────────────────────
        X = cx_g - half_w
        Y = cy_g - half_h
        Z = cz_g - half_d
        denom = Z + cam_dist
        if denom > 0.5:
            sx = int(cx_px + f * X / denom)
            sy = int(cy_px - f * Y / denom)
            cr, cg, cb = self.cfg.cursor_color
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(0,0)]:
                px, py = sx + dx, sy + dy
                if 0 <= px < px_w and 0 <= py < px_h:
                    # Pulsing brightness
                    pulse = 0.75 + 0.25 * np.sin(time.monotonic() * 6.0)
                    buf[py, px] = (int(cr*pulse), int(cg*pulse), int(cb*pulse))

        # ── Convert pixel buffer → terminal cells ──────────────────────────────
        new_cells: Dict[Tuple[int,int], str] = {}
        for row in range(th):
            for col in range(px_w):
                upper = buf[row * 2,     col]
                lower = buf[row * 2 + 1, col] if row * 2 + 1 < px_h else np.zeros(3, dtype=np.uint8)

                ur, ug, ub = int(upper[0]), int(upper[1]), int(upper[2])
                lr, lg, lb = int(lower[0]), int(lower[1]), int(lower[2])

                if ur == 0 and ug == 0 and ub == 0 and lr == 0 and lg == 0 and lb == 0:
                    cell = " "
                else:
                    cell = (
                        _rgb_fg(ur, ug, ub) +
                        _rgb_bg(lr, lg, lb) +
                        HALF_BLOCK +
                        _RESET
                    )
                new_cells[(row + 1, col + 1)] = cell   # 1-indexed for ANSI goto

        # ── Differential update (only changed cells) ───────────────────────────
        out_parts = []
        for pos, cell in new_cells.items():
            if self._prev_cells.get(pos) != cell:
                row, col = pos
                out_parts.append(_goto(row, col) + cell)

        # ── HUD overlay ────────────────────────────────────────────────────────
        hud = _build_hud(state, protocol_stats, self._fps_display,
                         self.cfg.grid_w, self.cfg.grid_h, self.cfg.grid_d)
        # Write HUD at bottom rows (last 3 lines)
        for i, line in enumerate(hud):
            out_parts.append(_goto(th - len(hud) + i + 1, 1) + _RESET + line[:tw])

        if out_parts:
            sys.stdout.write("".join(out_parts))
            sys.stdout.flush()

        self._prev_cells = new_cells

        # FPS counter
        self._frame_count += 1
        now = time.monotonic()
        if now - self._fps_timer >= 1.0:
            self._fps_display = self._frame_count / (now - self._fps_timer)
            self._frame_count = 0
            self._fps_timer   = now


# ── Internal helpers ──────────────────────────────────────────────────────────

def _term_size() -> Tuple[int, int]:
    """Return (cols, rows) of the current terminal."""
    try:
        sz = os.get_terminal_size()
        return sz.columns, sz.lines
    except OSError:
        return 80, 24


def _project(X, Y, Z, cam_dist, f, cx_px, cy_px):
    denom = Z + cam_dist
    if denom <= 0.5:
        return None, None
    return int(cx_px + f * X / denom), int(cy_px - f * Y / denom)


def _draw_grid_box(buf, depth, f, cx_px, cy_px, cam_dist,
                   hw, hh, hd, color):
    """Draw a very dim wireframe bounding box from the 8 corners of the grid."""
    cr, cg, cb = color
    corners = [
        (-hw, -hh, -hd), (hw, -hh, -hd), (-hw, hh, -hd), (hw, hh, -hd),
        (-hw, -hh,  hd), (hw, -hh,  hd), (-hw, hh,  hd), (hw, hh,  hd),
    ]
    edges = [
        (0,1),(2,3),(4,5),(6,7),   # top/bottom face parallels
        (0,2),(1,3),(4,6),(5,7),
        (0,4),(1,5),(2,6),(3,7),   # depth edges
    ]
    px_h, px_w = buf.shape[:2]

    for i, j in edges:
        x0, y0, z0 = corners[i]
        x1, y1, z1 = corners[j]
        steps = 20
        for s in range(steps + 1):
            t = s / steps
            X = x0 + t * (x1 - x0)
            Y = y0 + t * (y1 - y0)
            Z = z0 + t * (z1 - z0)
            sx, sy = _project(X, Y, Z, cam_dist, f, cx_px, cy_px)
            if sx is None:
                continue
            if 0 <= sx < px_w and 0 <= sy < px_h:
                d = Z + cam_dist
                if d < depth[sy, sx]:
                    depth[sy, sx] = d
                    buf[sy, sx]   = (cr, cg, cb)


def _build_hud(state: dict, proto: dict, fps: float, gw, gh, gd) -> list:
    """Return list of plain strings for the HUD overlay."""
    connected   = proto.get("connected", False)
    pkt_rate    = proto.get("packet_rate", 0.0)
    pkt_loss    = proto.get("packet_loss_pct", 0.0)
    cam_dist    = state.get("cam_dist", 0.0)
    buttons     = state.get("buttons", 0)

    btn_str = ""
    if buttons & 0x0001: btn_str += "L "
    if buttons & 0x0002: btn_str += "R "
    if buttons & 0x0004: btn_str += "Z+ "
    if buttons & 0x0008: btn_str += "Z- "
    if buttons & 0x0010: btn_str += "ROT "
    if not btn_str:      btn_str  = "—"

    conn_str = (
        "\033[1;32m● CONNECTED\033[0m" if connected
        else "\033[1;31m○ WAITING FOR DEVICE\033[0m"
    )
    lines = [
        (f"  {conn_str}   "
         f"\033[36mpkt/s:\033[0m{pkt_rate:.0f}  "
         f"\033[36mloss:\033[0m{pkt_loss:.1f}%  "
         f"\033[36mfps:\033[0m{fps:.0f}  "
         f"\033[36mcam:\033[0m{cam_dist:.1f}  "
         f"\033[36mbtn:\033[0m{btn_str}"),
        (f"  \033[2mGrid {gw}×{gh}×{gd}  "
         "Keys: W/A/S/D=cursor  +/-=zoom  R=rotate  C=recenter  O=obj  Q=quit\033[0m"),
    ]
    return lines
