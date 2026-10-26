"""
AirMouse 3D - Laptop Sensor Data Receiver & Dashboard Server
Listens for UDP JSON packets from the Android AirMouse3D app (default port 9000),
tracks packet statistics, and streams them in real-time over WebSocket
to a modern dark-theme web dashboard.
"""

import asyncio
import json
import math
import os
import socket
import time
import webbrowser
from typing import Set, Dict, Any, List

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

UDP_PORT = int(os.environ.get("UDP_PORT", 9000))
HTTP_PORT = int(os.environ.get("HTTP_PORT", 8080))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = FastAPI(title="AirMouse3D Sensor Dashboard")
connected_websockets: Set[WebSocket] = set()

# Packet statistics
stats = {
    "total_packets": 0,
    "last_seq": -1,
    "dropped_packets": 0,
    "rate_hz": 0.0,
    "last_packet_time": 0.0,
    "device_id": "none",
    "last_type": "none",
    "mock_running": False
}

# 1-second rolling rate window
recent_timestamps: List[float] = []

def get_local_ips() -> List[str]:
    """Detect local LAN IP addresses to display for the user."""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        ips.append(primary)
        s.close()
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    return ips if ips else ["127.0.0.1"]

async def broadcast_message(message: Dict[str, Any]):
    """Send JSON payload to all active browser dashboard WebSocket clients."""
    if not connected_websockets:
        return
    dead_clients = set()
    for ws in connected_websockets:
        try:
            await ws.send_json(message)
        except Exception:
            dead_clients.add(ws)
    for dead in dead_clients:
        connected_websockets.discard(dead)

def process_sensor_packet(packet: Dict[str, Any], addr: tuple):
    """Processes an incoming JSON sensor packet from Android/UDP or Mock."""
    now = time.time()
    recent_timestamps.append(now)
    # Prune timestamps older than 1.0 second
    while recent_timestamps and (now - recent_timestamps[0] > 1.0):
        recent_timestamps.pop(0)

    stats["rate_hz"] = len(recent_timestamps)
    stats["total_packets"] += 1
    stats["last_packet_time"] = now

    seq = packet.get("seq")
    if isinstance(seq, int):
        if stats["last_seq"] != -1 and seq > stats["last_seq"] + 1:
            stats["dropped_packets"] += (seq - stats["last_seq"] - 1)
        stats["last_seq"] = seq

    if "device_id" in packet:
        stats["device_id"] = str(packet["device_id"])
    if "type" in packet:
        stats["last_type"] = str(packet["type"])

    # Prepare message for web clients
    payload = {
        "event": "sensor_data",
        "source": f"{addr[0]}:{addr[1]}",
        "timestamp": now,
        "stats": {
            "total_packets": stats["total_packets"],
            "rate_hz": stats["rate_hz"],
            "dropped_packets": stats["dropped_packets"],
            "last_seq": stats["last_seq"],
            "device_id": stats["device_id"]
        },
        "data": packet
    }

    # Schedule broadcast onto event loop
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_message(payload))
    except RuntimeError:
        pass


class UdpProtocol(asyncio.DatagramProtocol):
    """Async UDP Receiver Protocol."""
    def __init__(self, callback):
        self.callback = callback
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print(f"[*] UDP Socket bound and listening on 0.0.0.0:{UDP_PORT}")

    def datagram_received(self, data: bytes, addr):
        try:
            text = data.decode("utf-8", errors="ignore")
            packet = json.loads(text)
            self.callback(packet, addr)
        except Exception as e:
            # Not valid json, ignore noise
            pass

    def error_received(self, exc):
        print(f"[!] UDP Error: {exc}")


# Mock generator for testing without physical Android device
mock_task = None

async def mock_sensor_loop():
    """Generates realistic 60Hz sensor packets for demo/testing purposes."""
    seq = 0
    t = 0.0
    print("[*] Mock sensor stream started (60 Hz)")
    try:
        while True:
            t += 1.0 / 60.0
            seq += 1

            # Simulated smooth orbital / figures movement
            dx = math.sin(t * 2.5) * 0.45 + (math.sin(t * 7.1) * 0.05)
            dy = math.cos(t * 2.0) * 0.35 + (math.cos(t * 5.3) * 0.04)
            dz = math.sin(t * 1.2) * 0.15

            # Simulated button presses every few seconds
            left_btn = (int(t) % 4 == 1) and (math.sin(t * 10) > 0.5)
            orbit_btn = (int(t) % 6 == 3)
            zoom_btn = (int(t) % 8 == 5)
            calib_btn = (seq % 600 == 0)

            if calib_btn:
                pkt = {
                    "version": 1,
                    "device_id": "mock-mobile-01",
                    "seq": seq,
                    "type": "calibrate",
                    "reference": {
                        "forward": [0.0, 0.0, 1.0],
                        "up": [0.0, 1.0, 0.0],
                        "right": [1.0, 0.0, 0.0]
                    }
                }
            else:
                pkt = {
                    "version": 1,
                    "device_id": "mock-mobile-01",
                    "seq": seq,
                    "type": "input",
                    "delta": {
                        "x": round(dx, 4),
                        "y": round(dy, 4),
                        "z": round(dz, 4)
                    },
                    "buttons": {
                        "left": left_btn,
                        "orbit": orbit_btn,
                        "zoom": zoom_btn,
                        "calibrate": False
                    }
                }

            process_sensor_packet(pkt, ("127.0.0.1", 54321))
            await asyncio.sleep(1.0 / 60.0)
    except asyncio.CancelledError:
        print("[*] Mock sensor stream stopped.")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_websockets.add(ws)

    # Initial state greeting
    await ws.send_json({
        "event": "server_info",
        "ips": get_local_ips(),
        "udp_port": UDP_PORT,
        "http_port": HTTP_PORT,
        "mock_running": stats["mock_running"],
        "stats": {
            "total_packets": stats["total_packets"],
            "rate_hz": stats["rate_hz"],
            "dropped_packets": stats["dropped_packets"],
            "last_seq": stats["last_seq"],
            "device_id": stats["device_id"]
        }
    })

    try:
        while True:
            text = await ws.receive_text()
            msg = json.loads(text)
            action = msg.get("action")
            if action == "toggle_mock":
                global mock_task
                enable = msg.get("enable", not stats["mock_running"])
                if enable and (mock_task is None or mock_task.done()):
                    stats["mock_running"] = True
                    mock_task = asyncio.create_task(mock_sensor_loop())
                elif not enable and mock_task:
                    stats["mock_running"] = False
                    mock_task.cancel()
                    mock_task = None

                await broadcast_message({
                    "event": "mock_status",
                    "mock_running": stats["mock_running"]
                })
            elif action == "reset_stats":
                stats["total_packets"] = 0
                stats["dropped_packets"] = 0
                stats["last_seq"] = -1
                recent_timestamps.clear()
                await broadcast_message({
                    "event": "stats_reset",
                    "stats": {
                        "total_packets": 0,
                        "rate_hz": 0,
                        "dropped_packets": 0,
                        "last_seq": -1,
                        "device_id": stats["device_id"]
                    }
                })
    except WebSocketDisconnect:
        pass
    finally:
        connected_websockets.discard(ws)


@app.get("/api/info")
async def api_info():
    return {
        "ips": get_local_ips(),
        "udp_port": UDP_PORT,
        "http_port": HTTP_PORT,
        "stats": stats
    }


# Mount static directory for frontend HTML/CSS/JS
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AirMouse3D Server Running. Static files missing."}


async def start_server():
    loop = asyncio.get_running_loop()

    # 1. Start UDP Server
    listen = loop.create_datagram_endpoint(
        lambda: UdpProtocol(process_sensor_packet),
        local_addr=("0.0.0.0", UDP_PORT)
    )
    transport, protocol = await listen

    # 2. Start Uvicorn Web Server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=HTTP_PORT,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)

    local_ips = get_local_ips()
    primary_ip = local_ips[0] if local_ips else "127.0.0.1"

    print("\n" + "=" * 60)
    print("      AirMouse 3D - Laptop Sensor Hub & Visualizer")
    print("=" * 60)
    print(f"[*] UDP Receiver   : 0.0.0.0:{UDP_PORT}")
    print(f"[*] Web Dashboard  : http://localhost:{HTTP_PORT}")
    print("\n>>> CONFIGURATION FOR ANDROID APP <<<")
    for ip in local_ips:
        print(f"    • Server IP : {ip}")
    print(f"    • Port      : {UDP_PORT}")
    print("=" * 60 + "\n")

    # Automatically open web browser
    try:
        webbrowser.open(f"http://localhost:{HTTP_PORT}")
    except Exception:
        pass

    try:
        await server.serve()
    finally:
        transport.close()


def main():
    import sys
    if "--mock" in sys.argv:
        # Auto-enable mock on start
        async def run_with_mock():
            global mock_task
            stats["mock_running"] = True
            mock_task = asyncio.create_task(mock_sensor_loop())
            await start_server()
        asyncio.run(run_with_mock())
    else:
        asyncio.run(start_server())


if __name__ == "__main__":
    main()
