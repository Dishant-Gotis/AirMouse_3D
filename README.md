# 🛸 AirMouse 3D — Spatial Motion Controller & 3D Telemetry System

[![Kotlin](https://img.shields.io/badge/Kotlin-2.0.0-7F52FF?logo=kotlin&logoColor=white)](https://kotlinlang.org)
[![Android](https://img.shields.io/badge/Android-Min%20SDK%2026%20%7C%20Target%2034-3DDC84?logo=android&logoColor=white)](https://developer.android.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Dashboard-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![UDP 60Hz](https://img.shields.io/badge/Telemetry-UDP%2060Hz%20JSON-00F2FE)](#-communication-protocol)

An end-to-end 6-DOF spatial air mouse and telemetry system that transforms an Android smartphone into a high-precision 3D spatial controller. The mobile application streams IMU sensor deltas and button interactions over low-latency UDP Wi-Fi to a PC, powering real-time 3D spatial manipulation and interactive telemetry dashboards.

---

## 📐 System Architecture

```
┌─────────────────────────────────┐                 ┌──────────────────────────────────────┐
│       ANDROID AIRMOUSE APP      │                 │            LAPTOP / PC               │
│                                 │                 │                                      │
│  Hardware IMU Sensors:          │   Wi-Fi (UDP)   │   1. SensorViewer Telemetry Hub      │
│   • Game Rotation Vector        │  Port 9000      │      • Async UDP socket listener     │
│   • Gyroscope (rad/s)           │ ──────────────> │      • FastAPI + WebSocket server    │
│   • Linear Acceleration (m/s²)  │  60 Hz JSON     │      • 3D Phone Spatial Visualizer   │
│                                 │                 │      • 2D Cursor Trajectory Plotter  │
│  Multi-Touch Controls:          │                 │                                      │
│   • Left Click, Orbit Mode      │                 │   2. 3D Volumetric Simulator         │
│   • Zoom In / Out, Calibrate    │                 │      • 3D LED matrix renderer        │
│                                 │                 │      • 6-DOF object manipulation     │
│  On-Device Real-Time HUD        │                 │      • Spatial raycasting cursor     │
└─────────────────────────────────┘                 └──────────────────────────────────────┘
```

---

## 🗂️ Repository Structure

```
TS_App/
├── AirMouse3D/                     # Native Android Kotlin application
│   ├── app/src/main/
│   │   ├── java/com/airm/app/
│   │   │   ├── ConnectionActivity.kt   # IP, port & rate configuration screen
│   │   │   ├── ControllerActivity.kt   # Multi-touch controller UI + live sensor HUD
│   │   │   ├── MotionSender.kt         # IMU listeners, relative delta & 60Hz send loop
│   │   │   ├── PacketEncoder.kt        # JSON UDP packet serializer (v1)
│   │   │   └── UdpTransport.kt         # Low-latency UDP socket transport
│   │   └── res/layout/                 # Dark-mode Material design layouts
│   └── build.gradle.kts                # Android build configuration
│
├── SensorViewer/                   # Laptop real-time dashboard & telemetry hub
│   ├── server.py                       # UDP receiver + FastAPI WebSocket streamer
│   ├── run.bat                         # 1-click Windows launcher
│   ├── requirements.txt                # Python dependencies
│   └── static/
│       ├── index.html                  # Responsive telemetry dashboard
│       ├── style.css                   # Glassmorphic dark styling & 3D CSS model
│       └── app.js                      # WebSocket client, 3D rotation & canvas trail
│
├── simulator/                      # 3D volumetric terminal / matrix simulator
│   ├── app.py                          # Simulator application entry point
│   ├── config.py                       # Simulation settings & grid dimensions
│   ├── net/                            # UDP protocol decoders & receiver loop
│   ├── render/                         # Voxel projection & terminal rendering
│   └── scene/                          # 3D spatial scene graph & camera models
│
├── APP_CONNECTION_AND_PACKET_SPEC.md   # Exhaustive protocol & lifecycle documentation
├── 3D_MONITOR_AIR_MOUSE_PROJECT_updated.md # Full project engineering specification
└── requirements.txt                # Root Python environment requirements
```

---

## ✨ Key Features

### 📱 Android Controller (`AirMouse3D`)
- **60 Hz Fixed-Rate Streaming**: Smooth, jitter-free transmission via `ScheduledExecutorService`.
- **Tilt-Compensated Deltas**: Relative quaternion delta math ($\mathbf{q}_{\text{rel}} = \mathbf{q}_{\text{ref}}^{*} \otimes \mathbf{q}_{\text{current}}$) prevents gimbal lock and drifting.
- **Dedicated Sensor Threading**: Hardware sensors run on an independent `HandlerThread` to ensure the UI remains fluid.
- **Real-Time On-Device HUD**: Displays live Euler angles (Yaw/Pitch/Roll), gyroscope angular velocities, linear accelerations, deltas, and packet transmission counts directly on the phone.
- **Multi-Touch Gesture Controls**: Dedicated buttons for Left Click, Orbit/Rotate, Zoom In (+Z), Zoom Out (-Z), and 1-tap Calibration.

### 💻 Laptop Telemetry Hub (`SensorViewer`)
- **Auto-IP Detection**: Detects your laptop's local LAN IP and displays it prominently with a 1-click copy button.
- **Interactive 3D Virtual Phone**: A responsive 3D model rotates, rolls, and pitches in real time with phone motion.
- **2D Trajectory Canvas**: Plots continuous $(X, Y)$ cursor movements with a glowing, fading trail.
- **High-Precision Delta Gauges**: Instantaneous bidirectional visual meters for $\Delta X$, $\Delta Y$, and $\Delta Z$.
- **LED Button States**: Instant neon feedback when buttons are clicked, held, or released.
- **Orthogonal Basis Vectors**: Displays live 3D `forward`, `up`, and `right` calibration reference vectors.
- **Datagram Inspector**: Live formatted JSON stream with pause and copy functionality.
- **Built-in Mock Simulator**: Test the entire laptop UI with realistic 60 Hz motion without needing the phone.

---

## 📡 Communication Protocol

All packets are transmitted over **UDP** (Default port `9000`) using UTF-8 JSON.

### 1. Motion Input Packet (`type: "input"`)
Sent every tick at 60 Hz during active control:
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1025,
  "type": "input",
  "delta": {
    "x": 0.1425,
    "y": 0.0812,
    "z": 0.0000
  },
  "buttons": {
    "left": false,
    "orbit": true,
    "zoom": false,
    "calibrate": false
  }
}
```

### 2. Calibration Packet (`type: "calibrate"`)
Sent when the user taps **CALIBRATE** on the mobile screen:
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1026,
  "type": "calibrate",
  "reference": {
    "forward": [0.0345, -0.1204, 0.9921],
    "up": [0.0121, 0.9926, 0.1204],
    "right": [0.9993, -0.0079, -0.0358]
  }
}
```

> 📖 **Full Protocol Specification**: See [`APP_CONNECTION_AND_PACKET_SPEC.md`](APP_CONNECTION_AND_PACKET_SPEC.md) for field definitions, coordinate frames, and math derivations.

---

## 🚀 Getting Started

### Prerequisites
- **Python**: Version `3.10` or newer.
- **Android Studio / Android SDK**: For building or modifying the mobile app (or use pre-built debug APK).
- **Network**: Laptop and smartphone connected to the **same Wi-Fi network**.

---

### Step 1: Launch the Laptop UI (`SensorViewer`)

1. Navigate to `SensorViewer`:
   ```powershell
   cd SensorViewer
   ```
2. Install dependencies (if not already installed):
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the dashboard:
   ```powershell
   python server.py
   ```
   *(Or simply double-click `run.bat` on Windows)*.
4. Your default browser will automatically open to `http://localhost:8080`.
5. Note the **Target IP** displayed in the top banner (e.g., `192.168.1.44:9000`).

---

### Step 2: Build & Install the Android App

Using Gradle in Android Studio or command-line:
```powershell
# Set your Java Home (if needed)
$env:JAVA_HOME = "D:\SYSTEM APPS\android-studio\jbr"

# Build debug APK
.\gradlew.bat assembleDebug
```
The output APK is generated at:
`AirMouse3D/app/build/outputs/apk/debug/app-debug.apk`

Install on your connected phone:
```powershell
adb install -r AirMouse3D/app/build/outputs/apk/debug/app-debug.apk
```

---

### Step 3: Connect & Control

1. Open **AirMouse 3D** on your smartphone.
2. Enter the laptop's Wi-Fi IP in the **Simulator IP** field (e.g. `192.168.1.44`).
3. Set **Port** to `9000` and **Rate** to `60 Hz`.
4. Tap **CONNECT**.
5. Wave the phone in the air! You will immediately see:
   - Live 3D phone model tilting and rotating on your laptop screen.
   - 2D cursor trajectory drawing on the canvas.
   - Live angles, gyro, and delta values updating in the phone's HUD and laptop gauges.
   - Glowing button indicators when you tap **Left Click**, **Orbit**, **Zoom**, or **Calibrate**.

---

## 🎮 Controller Buttons & Gesture Controls

| Control | Mode | Behavior |
| :--- | :--- | :--- |
| **Air Movement** | Continuous | Tilting and waving the phone moves the 3D cursor along $(\Delta X, \Delta Y)$. |
| **LEFT** | Hold / Press | Left-click selection or dragging action. |
| **ROTATE (ORBIT)** | Hold | Engages 3D camera / object orbit mode while moving the phone. |
| **ZOOM IN** | Hold | Sets `zoom: true` and sends $\Delta Z = +1.0$ (moves forward). |
| **ZOOM OUT** | Hold | Sets `zoom: true` and sends $\Delta Z = -1.0$ (moves backward). |
| **CALIBRATE** | Tap | Re-centers orientation zero reference and transmits orthogonal 3D basis vectors. |

---

## 🛠️ Testing & Simulation Without a Phone

To verify your laptop setup without a physical phone:
- Click the **Test Simulation** button in the top-right corner of the web dashboard.
- Or start the server with the mock flag:
  ```powershell
  python server.py --mock
  ```
This generates realistic 60 Hz figure-8 spatial movement, periodic button clicks, and calibration packets directly into the dashboard.

---

## 📄 Documentation & References

- [**Application Connection & Packet Spec**](APP_CONNECTION_AND_PACKET_SPEC.md) — Comprehensive packet breakdowns, units, equations, and connection lifecycle.
- [**System Engineering Document**](3D_MONITOR_AIR_MOUSE_PROJECT_updated.md) — Complete 3D monitor simulator architecture and LED matrix specifications.

---

## 👤 Author
- **Dishant Gotis** — [GitHub Profile](https://github.com/Dishant-Gotis)
