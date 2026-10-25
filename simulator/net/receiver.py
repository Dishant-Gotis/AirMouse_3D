"""
receiver.py — asyncio UDP receiver.

Responsibilities (per SIM-1 to SIM-5):
  SIM-2: bind to 0.0.0.0, print all local IPs + port at startup.
  SIM-3: discard duplicate / older packets using seq with wraparound.
  SIM-4: mark disconnected after timeout_ms of silence; recover automatically.
  SIM-5: track packet rate and sequence gaps (estimated loss).
"""
import asyncio
import socket
import time
import logging
from typing import Callable, Optional

from simulator.net.protocol import decode_sensor_packet, SensorSample

log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _local_ips() -> list[str]:
    """Return all non-loopback IPv4 addresses for this machine."""
    ips = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
    except Exception:
        pass
    return ips or ["127.0.0.1"]


def _seq_is_newer(new: int, last: int) -> bool:
    """Return True if `new` is strictly newer than `last` (handles uint16 wraparound)."""
    diff = (new - last) & 0xFFFF
    return 0 < diff <= 0x8000


# ── Protocol class ────────────────────────────────────────────────────────────
class SensorUDPProtocol(asyncio.DatagramProtocol):
    """
    asyncio DatagramProtocol that receives, validates, and dispatches
    SENSOR packets.  Heavy work MUST NOT be done here (SIM-1).
    """

    def __init__(
        self,
        on_sample: Callable[[SensorSample], None],
        timeout_ms: float = 2000.0,
    ):
        self._on_sample    = on_sample
        self._timeout_ms   = timeout_ms
        self._last_seq: Optional[int] = None

        # Stats
        self._last_packet_time: float = 0.0
        self._connected: bool = False
        self._packet_count: int = 0
        self._loss_count:   int = 0
        self._rate_window_start: float = time.monotonic()
        self.packet_rate: float = 0.0
        self.packet_loss_pct: float = 0.0

    # ── asyncio callbacks ─────────────────────────────────────────────────────
    def connection_made(self, transport):
        self._transport = transport

    def datagram_received(self, data: bytes, addr):
        sample = decode_sensor_packet(data)
        if sample is None:
            return                              # malformed → drop (SIM-3)

        # Sequence ordering check (SIM-3)
        if self._last_seq is not None:
            if not _seq_is_newer(sample.seq, self._last_seq):
                return                          # duplicate / stale → drop
            gap = (sample.seq - self._last_seq - 1) & 0xFFFF
            if gap > 0:
                self._loss_count += gap

        self._last_seq = sample.seq

        # Stats
        now = time.monotonic()
        self._last_packet_time = now
        self._packet_count += 1
        self._connected = True

        elapsed = now - self._rate_window_start
        if elapsed >= 1.0:
            self.packet_rate = self._packet_count / elapsed
            total = self._packet_count + self._loss_count
            self.packet_loss_pct = (self._loss_count / total * 100.0) if total else 0.0
            self._packet_count  = 0
            self._loss_count    = 0
            self._rate_window_start = now

        # Dispatch (SIM-1: keep this path light)
        self._on_sample(sample)

    def error_received(self, exc: Exception):
        log.warning("UDP error: %s", exc)

    def connection_lost(self, exc):
        log.info("UDP connection lost: %s", exc)

    # ── Public helpers ────────────────────────────────────────────────────────
    @property
    def connected(self) -> bool:
        """True if a packet was received within the last timeout_ms ms."""
        if not self._connected:
            return False
        if (time.monotonic() - self._last_packet_time) * 1000 > self._timeout_ms:
            self._connected = False
        return self._connected


# ── Factory / startup ──────────────────────────────────────────────────────────
async def start_receiver(
    on_sample: Callable[[SensorSample], None],
    host: str = "0.0.0.0",
    port: int = 9000,
    timeout_ms: float = 2000.0,
) -> SensorUDPProtocol:
    """
    Bind the UDP socket and return the running protocol instance.
    Prints local IPs + port to stdout (SIM-2).
    """
    loop = asyncio.get_running_loop()
    _, protocol = await loop.create_datagram_endpoint(
        lambda: SensorUDPProtocol(on_sample, timeout_ms),
        local_addr=(host, port),
    )
    protocol = protocol  # type: SensorUDPProtocol

    ips = _local_ips()
    print("\033[1;32m━━━ 3D Monitor Simulator ━━━\033[0m")
    print(f"\033[1mListening on UDP port {port}\033[0m")
    for ip in ips:
        print(f"  → Enter  \033[1;33m{ip}:{port}\033[0m  in the phone app")
    print("\033[2m(or use 10.0.2.2 from the Android emulator)\033[0m")
    print()

    return protocol
