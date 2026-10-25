"""
mock_sender.py — Phase 1: synthetic UDP packet sender.

Sends valid 52-byte SENSOR packets with a slowly rotating quaternion so
the simulator can be tested end-to-end without a real phone.

Rotation pattern:
  - Yaw sweeps ±30° at `--rotate-speed` deg/s  (cursor moves left/right)
  - Pitch oscillates ±15° at half that speed    (cursor moves up/down)
  - Every `--spin-interval` seconds the Rotate button is briefly held
    to demo object rotation mode.

Usage:
    python mock_sender.py --host 127.0.0.1 --port 9000 --rate 60
    python mock_sender.py --host 192.168.1.42 --port 9000 --rate 60 --rotate-speed 20
"""
import socket
import time
import math
import argparse
import struct
import sys

# We import the encoder directly without needing the full simulator package
_SENSOR_FMT = "<HBBHHIffffffffff"
MAGIC       = 0x3D4D
VERSION     = 1
MSG_SENSOR  = 1


def euler_to_quat(yaw_deg: float, pitch_deg: float, roll_deg: float = 0.0):
    """ZYX Euler angles (degrees) → (w, x, y, z) unit quaternion."""
    y = math.radians(yaw_deg)   / 2.0
    p = math.radians(pitch_deg) / 2.0
    r = math.radians(roll_deg)  / 2.0

    cy, sy = math.cos(y), math.sin(y)
    cp, sp = math.cos(p), math.sin(p)
    cr, sr = math.cos(r), math.sin(r)

    w  =  cr * cp * cy + sr * sp * sy
    x  =  sr * cp * cy - cr * sp * sy
    yq =  cr * sp * cy + sr * cp * sy
    z  =  cr * cp * sy - sr * sp * cy

    # Normalise
    n = math.sqrt(w*w + x*x + yq*yq + z*z)
    return w/n, x/n, yq/n, z/n


def build_packet(seq, buttons, ts_ms, qw, qx, qy, qz,
                 gx=0.0, gy=0.0, gz=0.0,
                 ax=0.0, ay=0.0, az=0.0) -> bytes:
    return struct.pack(
        _SENSOR_FMT,
        MAGIC, VERSION, MSG_SENSOR,
        seq & 0xFFFF,
        buttons & 0xFFFF,
        ts_ms & 0xFFFFFFFF,
        float(qw), float(qx), float(qy), float(qz),
        float(gx), float(gy), float(gz),
        float(ax), float(ay), float(az),
    )


def main():
    parser = argparse.ArgumentParser(description="3D Monitor — mock UDP packet sender")
    parser.add_argument("--host",          default="127.0.0.1", help="Simulator IP (default 127.0.0.1)")
    parser.add_argument("--port",          type=int, default=9000, help="UDP port (default 9000)")
    parser.add_argument("--rate",          type=float, default=60.0, help="Packets per second (default 60)")
    parser.add_argument("--rotate-speed",  type=float, default=15.0, help="Yaw sweep speed deg/s (default 15)")
    parser.add_argument("--spin-interval", type=float, default=8.0,
                        help="Seconds between object-spin demos (default 8)")
    args = parser.parse_args()

    period = 1.0 / args.rate
    sock   = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr   = (args.host, args.port)

    print(f"[mock_sender] Sending {args.rate:.0f} pkt/s → {args.host}:{args.port}")
    print(f"              Yaw sweep ±{args.rotate_speed * 2:.0f}° | Spin demo every {args.spin_interval}s")
    print("              Ctrl+C to stop\n")

    seq      = 0
    start    = time.monotonic()
    next_tx  = start

    try:
        while True:
            now     = time.monotonic()
            elapsed = now - start

            # ── Motion pattern ───────────────────────────────────────────────
            # Yaw: slow sine sweep
            yaw_deg   = math.sin(elapsed * math.radians(args.rotate_speed)) * 30.0
            pitch_deg = math.sin(elapsed * math.radians(args.rotate_speed / 2.0)) * 15.0

            # Simulated gyro (derivative of orientation)
            w_yaw   = args.rotate_speed * math.cos(elapsed * math.radians(args.rotate_speed))
            w_pitch = (args.rotate_speed / 2.0) * math.cos(elapsed * math.radians(args.rotate_speed / 2.0))
            gx = math.radians(w_pitch)
            gy = math.radians(w_yaw)
            gz = 0.0

            # ── Button / mode logic ──────────────────────────────────────────
            # Every spin_interval seconds, hold Rotate for 2 seconds to demo mode
            cycle_t  = elapsed % args.spin_interval
            spinning = cycle_t < 2.0
            buttons  = 0x0010 if spinning else 0     # BTN_ROTATE

            # Quick recenter at the start of each cycle
            if 1.95 < cycle_t < 2.05:
                buttons |= 0x0020   # BTN_RECENTER for one pass

            qw, qx, qy, qz = euler_to_quat(yaw_deg, pitch_deg)
            ts_ms = int(elapsed * 1000) & 0xFFFFFFFF

            pkt = build_packet(seq, buttons, ts_ms, qw, qx, qy, qz, gx, gy, gz)
            sock.sendto(pkt, addr)
            seq += 1

            # ── Stats every second ───────────────────────────────────────────
            if seq % int(args.rate) == 0:
                mode = "ROTATING" if spinning else "CURSOR"
                sys.stdout.write(
                    f"\r  seq={seq:6d}  yaw={yaw_deg:+6.1f}°  pitch={pitch_deg:+5.1f}°  "
                    f"mode={mode:8s}  "
                )
                sys.stdout.flush()

            # ── Fixed-rate sleep ─────────────────────────────────────────────
            next_tx += period
            sleep    = next_tx - time.monotonic()
            if sleep > 0:
                time.sleep(sleep)

    except KeyboardInterrupt:
        print("\n[mock_sender] Stopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
