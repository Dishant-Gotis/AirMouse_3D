"""
processor.py — Converts raw SensorSample data into scene commands.

All filtering/smoothing/calibration lives HERE, not on the phone (SEN-4).
Implements Section 6.4 calibration, Section 6.5 filtering, Section 10.5 math.
"""
import time
import numpy as np
from simulator.config import Config
from simulator.math_utils import (
    quat_normalize, quat_conjugate, quat_multiply,
    quat_to_yaw_pitch,
)
from simulator.net.protocol import SensorSample, BTN_ROTATE, BTN_RECENTER, BTN_ZOOM_IN, BTN_ZOOM_OUT


class InputProcessor:
    """
    Stateful processor:  SensorSample → updates to a mutable SceneState dict.

    Call  process(sample, scene_state, dt)  each time a new packet arrives.
    Call  recenter(q)  to manually reset the reference orientation.
    """

    def __init__(self, config: Config):
        self.cfg = config
        # Reference quaternion — set on first packet or on Recenter press
        self._q_ref = np.array([1.0, 0.0, 0.0, 0.0])
        self._calibrated = False

        # Rotate-mode bookkeeping
        self._was_rotating = False
        self._q_prev_rotate = np.array([1.0, 0.0, 0.0, 0.0])

        # Previous button state for edge detection
        self._prev_buttons: int = 0

        # Smoothed cursor output (EMA state)
        self._smooth_x: float = config.grid_w / 2.0
        self._smooth_y: float = config.grid_h / 2.0

    # ── Public API ─────────────────────────────────────────────────────────────

    def recenter(self, q: np.ndarray):
        """Store `q` as the new reference orientation (Section 6.4)."""
        self._q_ref = quat_normalize(q.copy())

    def process(self, sample: SensorSample, scene_state: dict, dt: float):
        """
        Apply the sample to `scene_state` in-place.

        scene_state keys (managed here):
          cursor_x, cursor_y   – smoothed grid-space cursor position
          cam_dist             – camera distance (zoom)
          object_q             – object's rotation quaternion (np.ndarray)
          buttons              – current bitmask
          btn_left_click       – True for one frame on rising edge
          btn_right_click      – True for one frame on rising edge
        """
        q   = quat_normalize(sample.q)
        btn = sample.buttons

        # ── Auto-calibrate on first valid packet ──────────────────────────────
        if not self._calibrated:
            self._q_ref = q.copy()
            self._calibrated = True

        # ── Recenter (rising edge of Recenter bit) ────────────────────────────
        if (btn & BTN_RECENTER) and not (self._prev_buttons & BTN_RECENTER):
            self.recenter(q)

        # ── Click edge detection ──────────────────────────────────────────────
        scene_state["btn_left_click"]  = bool((btn & 0x0001) and not (self._prev_buttons & 0x0001))
        scene_state["btn_right_click"] = bool((btn & 0x0002) and not (self._prev_buttons & 0x0002))
        scene_state["buttons"]         = btn

        # ── Relative orientation ───────────────────────────────────────────────
        # q_rel = q_ref† * q_now   (Section 10.5)
        q_rel = quat_normalize(quat_multiply(quat_conjugate(self._q_ref), q))

        # ── Rotate mode ────────────────────────────────────────────────────────
        if btn & BTN_ROTATE:
            if not self._was_rotating:
                # Just entered rotate mode — record starting orientation
                self._q_prev_rotate = q.copy()
                self._was_rotating = True
            else:
                # Incremental rotation: delta = q_now * q_prev†
                delta_q = quat_normalize(
                    quat_multiply(q, quat_conjugate(self._q_prev_rotate))
                )
                obj_q = scene_state.get("object_q", np.array([1.0, 0.0, 0.0, 0.0]))
                scene_state["object_q"] = quat_normalize(quat_multiply(delta_q, obj_q))
                self._q_prev_rotate = q.copy()
        else:
            self._was_rotating = False

            # ── Cursor mode ────────────────────────────────────────────────────
            yaw_deg, pitch_deg = quat_to_yaw_pitch(q_rel)

            # Dead zone (Section 6.5)
            if abs(yaw_deg)   < self.cfg.dead_zone_deg: yaw_deg   = 0.0
            if abs(pitch_deg) < self.cfg.dead_zone_deg: pitch_deg = 0.0

            # Map to grid coordinates (Section 10.5)
            target_x = (self.cfg.grid_w / 2.0
                        + (yaw_deg   / self.cfg.fov_yaw)   * (self.cfg.grid_w / 2.0))
            target_y = (self.cfg.grid_h / 2.0
                        - (pitch_deg / self.cfg.fov_pitch) * (self.cfg.grid_h / 2.0))

            # Clamp to grid
            target_x = max(0.0, min(self.cfg.grid_w  - 1.0, target_x))
            target_y = max(0.0, min(self.cfg.grid_h - 1.0, target_y))

            # EMA smoothing (Section 6.5)
            a = self.cfg.smoothing_alpha
            self._smooth_x = a * target_x + (1.0 - a) * self._smooth_x
            self._smooth_y = a * target_y + (1.0 - a) * self._smooth_y

            scene_state["cursor_x"] = self._smooth_x
            scene_state["cursor_y"] = self._smooth_y

        # ── Zoom ───────────────────────────────────────────────────────────────
        dist = scene_state.get("cam_dist", self.cfg.cam_dist_default)
        if btn & BTN_ZOOM_IN:
            dist -= self.cfg.zoom_speed * dt
        if btn & BTN_ZOOM_OUT:
            dist += self.cfg.zoom_speed * dt
        dist = max(self.cfg.cam_dist_min, min(self.cfg.cam_dist_max, dist))
        scene_state["cam_dist"] = dist

        self._prev_buttons = btn
