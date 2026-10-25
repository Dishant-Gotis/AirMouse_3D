"""
math_utils.py — Quaternion and vector math helpers.

All quaternions are numpy arrays of shape (4,) in [w, x, y, z] order.
All operations return new arrays (no in-place mutation).
"""
import math
import numpy as np


# ── Fundamental quaternion operations ─────────────────────────────────────────

def quat_normalize(q: np.ndarray) -> np.ndarray:
    """Return unit quaternion. Handles near-zero gracefully."""
    n = np.linalg.norm(q)
    if n < 1e-10:
        return np.array([1.0, 0.0, 0.0, 0.0])
    return q / n


def quat_conjugate(q: np.ndarray) -> np.ndarray:
    """Conjugate (= inverse for unit quaternion): (w, -x, -y, -z)."""
    return np.array([q[0], -q[1], -q[2], -q[3]])


def quat_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Hamilton product q1 * q2."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ])


def quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate 3-vector v by unit quaternion q using sandwich product q*p*q†."""
    p = np.array([0.0, v[0], v[1], v[2]])
    rotated = quat_multiply(quat_multiply(q, p), quat_conjugate(q))
    return rotated[1:]   # drop w component


# ── Derived helpers ────────────────────────────────────────────────────────────

def quat_to_yaw_pitch(q: np.ndarray):
    """
    Extract yaw and pitch from a unit quaternion (ZYX Euler convention).

    Must be consistent with euler_to_quat so that:
        yaw, pitch = quat_to_yaw_pitch(euler_to_quat(yaw, pitch))
    returns the original angles.

    In ZYX convention:
      - yaw   is rotation about the Z axis (left/right cursor)
      - pitch is rotation about the Y axis (up/down cursor)
    """
    w, x, y, z = q

    # Yaw — Z axis (ZYX: atan2 of the Z-rotation terms)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

    # Pitch — Y axis
    sinp = 2.0 * (w * y - z * x)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.degrees(math.asin(sinp))

    return yaw, pitch


def euler_to_quat(yaw_deg: float, pitch_deg: float, roll_deg: float = 0.0) -> np.ndarray:
    """
    Build a unit quaternion from ZYX Euler angles (degrees).
    Useful for the mock sender.
    """
    y = math.radians(yaw_deg)   / 2.0
    p = math.radians(pitch_deg) / 2.0
    r = math.radians(roll_deg)  / 2.0

    cy, sy = math.cos(y), math.sin(y)
    cp, sp = math.cos(p), math.sin(p)
    cr, sr = math.cos(r), math.sin(r)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y_ = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return quat_normalize(np.array([w, x, y_, z]))
