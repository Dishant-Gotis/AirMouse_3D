"""
protocol.py — 52-byte binary SENSOR packet encoder / decoder.

Packet layout (Section 8.3, all little-endian):
  Offset  Size  Type      Field
  0       2     uint16    magic     = 0x3D4D
  2       1     uint8     version   = 1
  3       1     uint8     type      (1 = SENSOR, 2 = HELLO, 3 = HELLO_ACK, 4 = PING, 5 = PONG, 6 = BYE)
  4       2     uint16    seq
  6       2     uint16    buttons   (bitmask, Section 8.4)
  8       4     uint32    timestamp_ms
  12      4     float32   qw
  16      4     float32   qx
  20      4     float32   qy
  24      4     float32   qz
  28      4     float32   gx  (rad/s)
  32      4     float32   gy
  36      4     float32   gz
  40      4     float32   ax  (m/s²)
  44      4     float32   ay
  48      4     float32   az
Total: 52 bytes

Button bitmask (Section 8.4):
  Bit 0  0x0001  Left
  Bit 1  0x0002  Right
  Bit 2  0x0004  Zoom In
  Bit 3  0x0008  Zoom Out
  Bit 4  0x0010  Rotate (held)
  Bit 5  0x0020  Recenter (edge-triggered)
"""
import struct
from dataclasses import dataclass
from typing import Optional
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────
MAGIC: int   = 0x3D4D
VERSION: int = 1

MSG_SENSOR    = 1
MSG_HELLO     = 2
MSG_HELLO_ACK = 3
MSG_PING      = 4
MSG_PONG      = 5
MSG_BYE       = 6

BTN_LEFT     = 0x0001
BTN_RIGHT    = 0x0002
BTN_ZOOM_IN  = 0x0004
BTN_ZOOM_OUT = 0x0008
BTN_ROTATE   = 0x0010
BTN_RECENTER = 0x0020

_SENSOR_FMT  = "<HBBHHIffffffffff"   # 52 bytes total
SENSOR_SIZE  = struct.calcsize(_SENSOR_FMT)    # must be 52

assert SENSOR_SIZE == 52, f"Packet size mismatch: {SENSOR_SIZE}"


# ── Data class ────────────────────────────────────────────────────────────────
@dataclass
class SensorSample:
    seq: int
    timestamp_ms: int
    buttons: int
    q: np.ndarray       # [w, x, y, z]
    gyro: np.ndarray    # [x, y, z]  rad/s
    acc: np.ndarray     # [x, y, z]  m/s²


# ── Decode ────────────────────────────────────────────────────────────────────
def decode_sensor_packet(data: bytes) -> Optional[SensorSample]:
    """
    Parse a raw UDP payload into a SensorSample.
    Returns None if the packet is invalid (wrong size, magic, version, type).
    Out-of-order / duplicate detection is handled by the receiver (Section 8.5).
    """
    if len(data) != SENSOR_SIZE:
        return None

    fields = struct.unpack(_SENSOR_FMT, data)
    magic, version, mtype, seq, buttons, ts_ms = fields[:6]
    floats = fields[6:]

    if magic != MAGIC or version != VERSION or mtype != MSG_SENSOR:
        return None

    return SensorSample(
        seq          = seq,
        timestamp_ms = ts_ms,
        buttons      = buttons,
        q            = np.array(floats[0:4], dtype=np.float64),   # qw qx qy qz
        gyro         = np.array(floats[4:7], dtype=np.float64),   # gx gy gz
        acc          = np.array(floats[7:10], dtype=np.float64),  # ax ay az
    )


# ── Encode ────────────────────────────────────────────────────────────────────
def encode_sensor_packet(
    seq: int,
    buttons: int,
    timestamp_ms: int,
    q: np.ndarray,
    gyro: np.ndarray,
    acc: np.ndarray,
) -> bytes:
    """
    Build a 52-byte SENSOR packet.  Used by mock_sender.py and QA-1 tests.
    """
    return struct.pack(
        _SENSOR_FMT,
        MAGIC, VERSION, MSG_SENSOR,
        seq & 0xFFFF,
        buttons & 0xFFFF,
        timestamp_ms & 0xFFFFFFFF,
        float(q[0]), float(q[1]), float(q[2]), float(q[3]),
        float(gyro[0]), float(gyro[1]), float(gyro[2]),
        float(acc[0]),  float(acc[1]),  float(acc[2]),
    )
