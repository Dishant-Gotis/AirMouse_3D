# 3D Monitor Simulator with Smartphone Air Mouse

**Project name:** `<PROJECT_NAME>`
**Version:** 0.3 (Draft)
**Owner / Team:** `<TEAM_NAME>`
**Last updated:** `<DATE>`

---

## 1. Purpose of This Document

This document describes the complete concept, architecture, communication protocol, and implementation plan for the project. Its primary purpose is to serve as a reference for developing the **mobile application** (the "3D mouse"), while also defining the **Linux terminal simulator** that the mobile application communicates with.

---

## 2. Project Overview

The project consists of two software components:

1. **Mobile Application (Air Mouse).** Runs on a smartphone. Reads the phone's motion sensors (gyroscope, accelerometer, rotation vector) and on-screen button states, and streams them to the simulator in real time.
2. **3D Monitor Simulator (Linux Terminal Application).** Receives the sensor stream, converts it into cursor motion and object manipulation, and renders a simulated **3D LED matrix monitor** inside the terminal.

### 2.1 Core Idea

The simulated monitor is a volumetric grid of LEDs (a 3D matrix of width × height × depth voxels). 3D objects are displayed by lighting up LEDs in that grid. The user holds the phone and moves it through the air; the on-screen cursor in the simulation follows that motion. Buttons on the phone provide left click, right click, zoom in, zoom out, and a rotation control that rotates the displayed 3D object.

### 2.2 Important Clarification

This project does **not** implement an operating-system-level mouse driver. The simulator is a standalone Linux terminal application that consumes the phone's data stream directly. No kernel module, `uinput` device, or system pointer integration is required (this may be considered as a future extension; see Section 14).

---

## 3. Goals and Non-Goals

### 3.1 Goals

- Stream IMU sensor data from a phone to a Linux terminal application with low latency (target end-to-end latency below 50 ms).
- Move a cursor inside the simulated 3D monitor in response to phone motion.
- Provide Left Click, Right Click, Zoom In, Zoom Out, and Rotate controls.
- Allow rotation of a displayed 3D object by holding the Rotate control and moving the phone.
- Render a 3D LED-grid monitor in a Linux terminal.
- Provide a documented, versioned communication protocol.
- Treat **seamless, continuous sensor-to-simulator communication** as the highest-priority quality of the system; the mobile UI is secondary (see Section 9.8).

### 3.2 Non-Goals (Version 0.1)

- Real OS-level mouse/pointer control.
- Absolute position tracking in space (see the limitation in Section 6.3).
- Support for multiple phones connected at once.
- Rendering with a GPU or windowed graphics toolkit.
- Bluetooth transport (deferred to a later phase; see Section 5.1).
- iOS support (the protocol is platform-neutral, so an iOS client can be added later).

---

## 4. System Architecture

```
+---------------------------+                 +--------------------------------------+
|     MOBILE APPLICATION    |                 |   LINUX TERMINAL SIMULATOR           |
|                           |                 |                                      |
|  Sensors (IMU)            |                 |  Network Receiver                    |
|   - Rotation vector       |   Wi-Fi (UDP)   |   - Packet parser / validator        |
|   - Gyroscope             | --------------> |  Input Processor                     |
|   - Accelerometer         |   (v0.1 only)   |   - Filtering, calibration           |
|  Buttons / UI             |                 |   - Cursor + rotation mapping        |
|   - L, R, Zoom +/-, Rot.  |                 |  3D Scene Engine                     |
|  Packet Encoder           |                 |   - Voxel grid, objects, camera      |
|  Network Sender           |                 |  Terminal Renderer                   |
+---------------------------+                 |   - Projection, depth, colors        |
                                              +--------------------------------------+
```

### 4.1 Data Flow

1. The phone samples sensors at a fixed rate (target 60 to 100 Hz).
2. The phone packages the latest sensor values and button states into a packet.
3. The packet is transmitted over Wi-Fi using UDP (Bluetooth is deferred to a later phase).
4. The simulator receives and validates the packet.
5. The input processor converts sensor data into cursor movement, zoom, and rotation commands.
6. The scene engine updates the cursor, camera, and object state.
7. The terminal renderer draws the updated 3D LED grid.

### 4.2 Technology Stack (Selected for Version 0.1)

| Layer | Selected Technology | Notes |
|---|---|---|
| Mobile platform | Android (native) | iOS is out of scope for version 0.1 |
| Mobile language | Not mandated | Kotlin is the recommended default for Android Studio productivity; Java or C/C++ (NDK) are equally acceptable provided the rules in Section 9.8 and the protocol in Section 8 are followed |
| Mobile UI | Any (Jetpack Compose or XML Views) | UI is thin: connection fields, status, and buttons only |
| Mobile concurrency | Dedicated background threads | Sensor thread and fixed-rate sender thread (coroutine, `HandlerThread`, or native thread) |
| Mobile sensors | Android `SensorManager` | Game rotation vector, gyroscope, linear acceleration |
| Mobile networking | UDP socket (`DatagramSocket` or native socket) | No external dependencies |
| Mobile tooling | Android Studio | Editor, emulator with virtual sensors, Logcat, and device mirroring (Section 9.9) |
| Transport | Wi-Fi over UDP | Bluetooth is deferred (see Section 5.1) |
| Protocol | Custom 52-byte binary packet | JSON variant for debugging only |
| Simulator language | Python 3 | Prototype; C++ or Rust only if performance requires it |
| Simulator libraries | `asyncio`, `numpy`, `curses` or `rich` | UDP receiver, 3D math, terminal rendering |
| Rendering | Perspective projection, depth buffer, half-block characters, 24-bit color | Terminal-only; no GPU or windowing toolkit |
| Platform | Linux terminal | Phone and simulator on the same local network or hotspot |

---

## 5. Choosing the Transport: Wi-Fi vs. Bluetooth

| Criterion | Wi-Fi (UDP) | Bluetooth LE | Bluetooth Classic (RFCOMM) |
|---|---|---|---|
| Typical latency | Low (about 2 to 10 ms on a local network) | Medium (about 10 to 40 ms, depends on connection interval) | Low to medium |
| Throughput | High | Low to medium | Medium |
| Setup effort | Easy (IP address and port) | Moderate (GATT service design) | Moderate |
| Linux support | Excellent (standard sockets) | Good (BlueZ, requires setup) | Good (BlueZ) |
| Requires shared network | Yes | No | No |
| Mobile platform support | Android and iOS | Android and iOS | Android only (iOS restricts it) |

### 5.1 Decision

**Version 0.1 uses Wi-Fi over UDP only.** Bluetooth is not required for the first release.

- **Latency:** UDP on a local network typically adds only a few milliseconds, which meets the 50 ms target. Bluetooth LE generally adds more and varies more, which can cause cursor jitter.
- **Simplicity:** Wi-Fi requires only an IP address and a port on each side. Bluetooth requires BlueZ configuration, pairing, and a custom service design on Linux.
- **Bandwidth:** The stream is approximately 52 bytes at 60 to 100 Hz (a few KB/s), which is well within Wi-Fi capacity.
- **Packet loss:** Occasional loss is acceptable because the newest sensor sample supersedes older ones.
- **TCP:** Use TCP only for control messages, if required. Do not use it for the sensor stream, since retransmission delays cause visible lag.

**Network requirement and known risk.** The phone and the Linux machine must be on the same network. Many institutional or public Wi-Fi networks enable client isolation, which blocks device-to-device traffic. If this occurs, enable the phone's hotspot and connect the Linux machine to it (no internet access is required), or run a hotspot from the Linux machine. This is also the recommended setup for demonstrations.

**When Bluetooth should be reconsidered.** Add it in a later phase only if the system must operate with no Wi-Fi or hotspot, if one-tap pairing is desired, or if real Bluetooth HID mouse emulation is pursued (see Section 14).

**Design requirement for future transports.** The mobile app shall implement sending behind a small interface (for example, `Transport.send(bytes)`), with `UdpTransport` as the only implementation in version 0.1. The packet format in Section 8 is transport-independent, so a Bluetooth transport can be added later without changing the sensor processing or the simulator logic.

---

## 6. Sensors and Motion Processing

### 6.1 Sensors Used

| Sensor | Android API | iOS API | Purpose |
|---|---|---|---|
| Game Rotation Vector (fused, no magnetometer) | `Sensor.TYPE_GAME_ROTATION_VECTOR` | `CMDeviceMotion.attitude` / `quaternion` | Primary orientation source (quaternion) |
| Gyroscope | `Sensor.TYPE_GYROSCOPE` | `CMDeviceMotion.rotationRate` | Angular velocity, rotation deltas |
| Linear Accelerometer | `Sensor.TYPE_LINEAR_ACCELERATION` | `CMDeviceMotion.userAcceleration` | Gestures, shake detection (optional) |
| Accelerometer | `Sensor.TYPE_ACCELEROMETER` | `CMDeviceMotion.gravity` | Fallback for tilt and gravity |

**Recommendation:** Use the platform's fused orientation (game rotation vector on Android, `CMDeviceMotion` on iOS) as the main signal. Operating-system sensor fusion already combines gyroscope and accelerometer data and handles bias and noise better than raw integration. Also send raw gyroscope and accelerometer values so the simulator can apply its own filtering or fall back to them.

The magnetometer-free variant is preferred, because magnetic interference indoors causes unpredictable heading shifts.

### 6.2 Coordinate Conventions

Define and document one convention and convert on the phone before sending.

- **Phone frame (device coordinates):** X to the right of the screen, Y toward the top of the screen, Z out of the screen.
- **Transmitted quaternion:** `(w, x, y, z)`, unit length, representing device orientation relative to an arbitrary fixed reference frame.
- **Units:** gyroscope in rad/s, accelerometer in m/s², timestamps in milliseconds.

### 6.3 Key Technical Limitation: Position vs. Orientation

Phone sensors measure **orientation** reliably but **position poorly**. Obtaining position by double-integrating accelerometer data produces rapid drift (errors grow with the square of time), so a phone cannot be tracked in 3D space the way a camera-tracked controller can.

**Design decision:** the cursor is controlled by **orientation** (pointing direction), not by physical position.

- Rotating or tilting the phone left/right (yaw) moves the cursor horizontally.
- Tilting the phone up/down (pitch) moves the cursor vertically.
- Depth (the third axis of the 3D monitor) is controlled by the Zoom buttons, or optionally by a push/pull gesture detected from linear acceleration (see Section 7.4).

This approach is stable, drift-free after calibration, and feels similar to a laser pointer or console motion controller.

### 6.4 Calibration and Recentering

- **Recenter button:** pressing it stores the current orientation as the reference orientation. All later motion is measured relative to that reference.
- **Auto-recenter on connect:** the simulator or the app stores the first valid orientation as the reference.
- **Drift handling:** gyroscope-only integration drifts over time. Using the fused quaternion minimizes this, and the Recenter button resets any residual drift.

### 6.5 Filtering and Smoothing

- **Dead zone:** ignore angular changes below a small threshold (for example, 0.2 degrees) to suppress hand tremor.
- **Low-pass smoothing:** apply an exponential moving average to the output cursor position: `smoothed = alpha * new + (1 - alpha) * smoothed`, with `alpha` in the range 0.2 to 0.6 (configurable).
- **Sensitivity:** configurable scaling between phone angle and cursor movement (for example, ±30 degrees of yaw covers the full monitor width).

Filtering is performed on the **simulator** side so it can be tuned without updating the mobile application.

---

## 7. Control Scheme and Functional Requirements

### 7.1 Mobile Application Controls

| Control | Type | Function |
|---|---|---|
| Left Button | Hold / tap | Primary click (select, drag when held) |
| Right Button | Hold / tap | Secondary click (context action, cancel) |
| Zoom In | Hold / tap | Moves the camera closer / enlarges the scene |
| Zoom Out | Hold / tap | Moves the camera away / shrinks the scene |
| Rotate | **Hold** | While held, phone motion rotates the displayed 3D object instead of moving the cursor |
| Recenter | Tap | Resets the reference orientation |
| Connect / Status | UI element | Shows connection state and latency |

### 7.2 Cursor Mode (Default)

When Rotate is not held, the relative orientation of the phone (yaw, pitch) is mapped to the cursor's X and Y position on the monitor's front plane. The cursor is shown as a distinct marker (for example, a crosshair or a bright voxel).

### 7.3 Rotate Mode

When Rotate is held:

1. The simulator records the phone's orientation at the instant Rotate was pressed.
2. For each subsequent sample, it computes the incremental rotation of the phone since the previous sample.
3. That incremental rotation is applied to the displayed 3D object's orientation.
4. The cursor is frozen while Rotate is held.

When Rotate is released, cursor mode resumes. The object retains its new orientation.

### 7.4 Optional Depth Gesture (Future)

A quick forward/backward push detected in the linear acceleration Z axis may be mapped to moving the cursor along the depth axis. This is optional and should be considered only after the core features are stable.

### 7.5 Functional Requirements Summary

| ID | Requirement |
|---|---|
| FR-1 | The mobile app shall stream sensor and button data at a configurable rate (default 60 Hz). |
| FR-2 | The mobile app shall allow entering or discovering the simulator's address. |
| FR-3 | The simulator shall display a 3D LED-grid monitor in the terminal. |
| FR-4 | The cursor shall follow phone orientation changes in real time. |
| FR-5 | Left and Right buttons shall generate click events in the simulation. |
| FR-6 | Zoom In and Zoom Out shall change the scene scale or camera distance. |
| FR-7 | Holding Rotate shall rotate the displayed object according to phone motion. |
| FR-8 | The Recenter control shall reset the reference orientation. |
| FR-9 | Both sides shall detect connection loss and recover automatically. |
| FR-10 | The simulator shall ignore malformed or out-of-order packets. |

### 7.6 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | End-to-end latency below 50 ms on a typical local network. |
| NFR-2 | Simulator terminal rendering at 30 frames per second or higher. |
| NFR-3 | Mobile app battery use acceptable for sessions of 30 minutes or more. |
| NFR-4 | The protocol shall be versioned for backward compatibility. |
| NFR-5 | The mobile app shall maintain a steady send rate with low jitter and shall recover automatically from link interruptions without user action. |

---

## 8. Communication Protocol

### 8.1 Connection Setup (Wi-Fi / UDP)

- The simulator listens on a UDP port, default `<PORT>` (for example, 9000), and displays its IP address on startup.
- The mobile app sends packets to `<SIMULATOR_IP>:<PORT>`.
- The simulator replies to `HELLO` with `HELLO_ACK` so the app can confirm the link is alive.

**Optional discovery:** the simulator may display a QR code (encoding `ip:port`) in the terminal, which the phone scans for one-step pairing. Alternatively, the simulator may broadcast a discovery beacon that the app listens for.

**Network note:** if the phone cannot reach the simulator on a shared Wi-Fi network, use a phone or laptop hotspot (see Section 5.1).

### 8.2 Message Types

| Type ID | Name | Direction | Description |
|---|---|---|---|
| 1 | `SENSOR` | Phone to Simulator | Sensor and button data (sent continuously) |
| 2 | `HELLO` | Phone to Simulator | Connection request with device information |
| 3 | `HELLO_ACK` | Simulator to Phone | Connection accepted |
| 4 | `PING` | Either | Latency measurement request |
| 5 | `PONG` | Either | Latency measurement reply |
| 6 | `BYE` | Either | Graceful disconnect |

### 8.3 Binary `SENSOR` Packet Layout

All multi-byte values are **little-endian**. Total size: **52 bytes**.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 2 | `uint16` | `magic` | Constant `0x3D4D`, identifies the protocol |
| 2 | 1 | `uint8` | `version` | Protocol version (currently 1) |
| 3 | 1 | `uint8` | `type` | Message type (1 for `SENSOR`) |
| 4 | 2 | `uint16` | `seq` | Sequence number, wraps at 65535 |
| 6 | 2 | `uint16` | `buttons` | Button bitmask (see below) |
| 8 | 4 | `uint32` | `timestamp_ms` | Sender time in milliseconds since app start |
| 12 | 4 | `float32` | `qw` | Quaternion W |
| 16 | 4 | `float32` | `qx` | Quaternion X |
| 20 | 4 | `float32` | `qy` | Quaternion Y |
| 24 | 4 | `float32` | `qz` | Quaternion Z |
| 28 | 4 | `float32` | `gx` | Gyroscope X (rad/s) |
| 32 | 4 | `float32` | `gy` | Gyroscope Y (rad/s) |
| 36 | 4 | `float32` | `gz` | Gyroscope Z (rad/s) |
| 40 | 4 | `float32` | `ax` | Linear acceleration X (m/s²) |
| 44 | 4 | `float32` | `ay` | Linear acceleration Y (m/s²) |
| 48 | 4 | `float32` | `az` | Linear acceleration Z (m/s²) |

### 8.4 Button Bitmask

| Bit | Mask | Button |
|---|---|---|
| 0 | `0x0001` | Left |
| 1 | `0x0002` | Right |
| 2 | `0x0004` | Zoom In |
| 3 | `0x0008` | Zoom Out |
| 4 | `0x0010` | Rotate (held) |
| 5 | `0x0020` | Recenter (edge-triggered) |
| 6 to 15 | reserved | Future use (middle button, scroll, etc.) |

A bit set to `1` means the button is currently pressed. Because UDP can drop packets, the **state** is sent in every packet instead of sending only press/release events. This keeps the simulator consistent even if a packet is lost.

### 8.5 Sequence Numbers and Ordering

The simulator discards any packet whose `seq` is older than the most recently accepted one (accounting for wraparound). This prevents stale data from causing cursor jumps.

### 8.6 Debug Format (JSON, Optional)

For development, an equivalent JSON message may be used, which is easier to inspect:

```json
{
  "v": 1,
  "t": "sensor",
  "seq": 1042,
  "ts": 583920,
  "btn": 17,
  "q": [0.9961, 0.0872, 0.0, 0.0],
  "gyro": [0.01, -0.02, 0.00],
  "acc": [0.12, 0.03, -0.05]
}
```

The binary format is recommended for production because it is smaller and faster to parse.

### 8.7 Connection Timeout

If the simulator receives no packet for **2 seconds**, it marks the device as disconnected and shows a "Waiting for device" status. The mobile app, on its side, shows "Disconnected" if no `PONG` or `HELLO_ACK` is received within a similar interval, and retries automatically.

---

## 9. Mobile Application Design

### 9.1 Technology Options

| Option | Advantages | Considerations |
|---|---|---|
| **Android native (Kotlin, Java, or NDK)** | Best sensor access and timing control, simple UDP sockets | Android only |
| **Flutter** | Single codebase for Android and iOS, plugins such as `sensors_plus` | Slightly less control over sensor sampling rate |
| **React Native** | Single codebase, large ecosystem | Sensor timing and UDP need native modules or libraries |

**Decision:** Native Android, developed in Android Studio. The implementation language is **not mandated**. The mobile application is a low-level sensor streamer: its UI only displays connection status and provides button actions, so the choice of language or UI toolkit has no effect on the system as long as the rules in Section 9.8 and the protocol in Section 8 are followed.

- **Kotlin** is the recommended default, because it gives the fastest development in Android Studio and most current Android documentation uses it.
- **Java** is equally acceptable. The sensor and socket APIs are identical.
- **C/C++ through the NDK** is permitted. It is not required initially: the Java and Kotlin `SensorManager` API sits on top of the same underlying sensor services, so end-to-end latency is determined mainly by the sensor rate, the Wi-Fi link, and thread scheduling rather than by the language. Move the sender to native code only if profiling shows jitter caused by the managed runtime (for example, garbage-collection pauses) that cannot be removed by following rule SEN-5 and rule COM-6.

**Alternative:** if iOS support becomes a requirement, a second client can be built (for example, with Flutter or native Swift). The protocol and the simulator remain unchanged.

### 9.2 Screens

1. **Connection Screen.** Fields for simulator IP and port, a Scan QR button, a Connect button, and connection status.
2. **Controller Screen.** Large touch buttons for Left, Right, Zoom In, Zoom Out, Rotate (hold), and Recenter, plus a small status indicator (connected, latency, packet rate).
3. **Settings Screen.** Sampling rate, button layout (left-handed or right-handed), haptic feedback on or off, and screen-stays-on toggle.

### 9.3 Suggested Layout (Controller Screen)

```
+------------------------------------+
|  Status: Connected   Latency: 8 ms |
|                                    |
|            [   ROTATE   ]          |  <- large, hold to rotate object
|                                    |
|   [ LEFT ]            [ RIGHT ]    |
|                                    |
|   [ ZOOM + ]          [ ZOOM - ]   |
|                                    |
|            [ RECENTER ]            |
+------------------------------------+
```

The phone is held like a remote, with the thumb reaching the buttons. Buttons should be large, provide haptic feedback, and support multi-touch (for example, holding Rotate while pressing Zoom).

### 9.4 Mobile Application Internal Structure

```
App
 |-- SensorManager      -> registers sensors, produces a motion snapshot
 |-- ButtonState        -> tracks pressed buttons (bitmask)
 |-- PacketEncoder      -> builds the 52-byte binary packet
 |-- Transport          -> interface: send(bytes), close()
 |    |-- UdpTransport  -> DatagramSocket implementation (version 0.1)
 |-- NetworkClient      -> uses a Transport; send loop, HELLO / PING handling
 |-- UI Layer           -> connection screen, controller screen, settings
 |-- Config Store       -> saves last IP, port, rate, layout
```

### 9.5 Sending Loop

Use a **fixed-rate sender** (for example, every 16 ms for 60 Hz) that reads the **latest** sensor snapshot and button state, rather than sending a packet on every individual sensor callback. This produces a steady stream and avoids flooding the network when sensors report at high rates.

Implement the loop on a dedicated background thread (for example, a coroutine on `Dispatchers.IO`, a `HandlerThread`, or a native thread) using a fixed-rate schedule, so that no network operation runs on the main thread. The complete rules are in Section 9.8.

### 9.6 Reference Snippet: Android (Kotlin)

The following sketch illustrates the core idea in Kotlin. It is not a complete application, and the language is not mandated (Section 9.1). For brevity it registers the sensors on the default thread; production code must follow rule SEN-6 (dedicated sensor thread) and the other rules in Section 9.8.

```kotlin
class MotionSender(
    private val sensorManager: SensorManager,
    private val host: String,
    private val port: Int
) : SensorEventListener {

    private val q = FloatArray(4)           // w, x, y, z
    private val gyro = FloatArray(3)
    private val acc = FloatArray(3)
    @Volatile var buttons: Int = 0
    private var seq = 0
    private val socket = DatagramSocket()
    private val address = InetAddress.getByName(host)
    private val startMs = SystemClock.elapsedRealtime()

    fun start() {
        val samplingUs = 10_000 // about 100 Hz request; actual rate is device dependent
        listOf(
            Sensor.TYPE_GAME_ROTATION_VECTOR,
            Sensor.TYPE_GYROSCOPE,
            Sensor.TYPE_LINEAR_ACCELERATION
        ).forEach { type ->
            sensorManager.getDefaultSensor(type)?.let {
                sensorManager.registerListener(this, it, samplingUs)
            }
        }
        // Start a fixed-rate send loop (for example, a coroutine) calling sendPacket() every ~16 ms.
    }

    override fun onSensorChanged(e: SensorEvent) {
        when (e.sensor.type) {
            Sensor.TYPE_GAME_ROTATION_VECTOR ->
                SensorManager.getQuaternionFromVector(q, e.values) // fills w, x, y, z
            Sensor.TYPE_GYROSCOPE -> e.values.copyInto(gyro, endIndex = 3)
            Sensor.TYPE_LINEAR_ACCELERATION -> e.values.copyInto(acc, endIndex = 3)
        }
    }

    override fun onAccuracyChanged(s: Sensor?, a: Int) {}

    fun sendPacket() {
        val buf = ByteBuffer.allocate(52).order(ByteOrder.LITTLE_ENDIAN)
        buf.putShort(0x3D4D.toShort())
        buf.put(1)                                   // version
        buf.put(1)                                   // type SENSOR
        buf.putShort((seq++ and 0xFFFF).toShort())
        buf.putShort(buttons.toShort())
        buf.putInt((SystemClock.elapsedRealtime() - startMs).toInt())
        q.forEach { buf.putFloat(it) }
        gyro.forEach { buf.putFloat(it) }
        acc.forEach { buf.putFloat(it) }
        socket.send(DatagramPacket(buf.array(), 52, address, port))
    }
}
```

**Notes for implementation:**

- Network operations must run off the main thread.
- Request the `INTERNET` permission. If a Bluetooth transport is added later, also request the relevant Bluetooth permissions for the target Android version.
- Keep the screen awake while the controller screen is active (`FLAG_KEEP_SCREEN_ON`).
- Consider a foreground service if the app must continue streaming while the screen is locked.

### 9.7 iOS Notes (If Supported)

- Use `CMMotionManager.startDeviceMotionUpdates(to:)` with `deviceMotionUpdateInterval` set to about `1/60`.
- Read `attitude.quaternion`, `rotationRate`, and `userAcceleration`.
- Use `NWConnection` (Network framework) with UDP for sending.
- Remember the Local Network permission prompt on iOS 14 and later.

### 9.8 Mobile Application Development Rules

#### 9.8.1 Guiding Principle

The mobile application is a **sensor-streaming client**. It reads the phone's sensors, reads the button states, and delivers both to the simulator with the lowest possible delay and without interruption. All interpretation of the data (filtering, mapping to cursor movement, rotation, zoom) happens in the simulator.

Priorities, in order:

1. **Continuity and low latency** of the sensor-to-simulator stream.
2. **Correctness** of the transmitted data (units, axes, ordering).
3. **Simplicity** of the code.
4. **UI appearance** (the lowest priority; the UI only needs to be clear and usable).

The key words MUST, SHOULD, and MAY in the rules below are to be interpreted as requirements, strong recommendations, and options respectively.

#### 9.8.2 Sensor Acquisition Rules

| ID | Rule |
|---|---|
| SEN-1 | The app MUST register each sensor with an explicit sampling period (request 10,000 µs or less, i.e. 100 Hz) and a **maximum report latency of 0**, so that readings are delivered immediately and not batched. Note: on Android 12 and later, rates above 200 Hz require the `HIGH_SAMPLING_RATE_SENSORS` permission; the default target of 100 Hz does not. |
| SEN-2 | The app MUST use the fused **game rotation vector** as the primary orientation source. If it is unavailable, it SHOULD fall back to the rotation vector, and then to the gyroscope with the accelerometer. The app MUST show the user which source is active. |
| SEN-3 | The app MUST report gyroscope values in rad/s, acceleration in m/s², and orientation as a unit quaternion `(w, x, y, z)`, exactly as defined in Section 6.2. |
| SEN-4 | The app MUST NOT filter, smooth, or scale the data (no sensitivity, dead zone, or drift correction on the phone). Only unit and axis conversion is allowed. These adjustments belong to the simulator (Section 6.5). |
| SEN-5 | Sensor callbacks MUST only copy values into preallocated buffers. No memory allocation, file or network I/O, logging, or UI work may occur inside a sensor callback. |
| SEN-6 | Sensors SHOULD be registered with a dedicated background thread (for example, a `HandlerThread`), so that UI work on the main thread cannot delay sensor delivery. |
| SEN-7 | The app MUST unregister its sensor listeners when streaming stops, to save battery. |

#### 9.8.3 Communication Rules

| ID | Rule |
|---|---|
| COM-1 | The sensor stream MUST use UDP and the exact 52-byte `SENSOR` packet defined in Section 8.3. A packet MUST never exceed one datagram (no fragmentation). |
| COM-2 | Packets MUST be sent by a **fixed-rate sender** running on its own background thread (default 60 Hz, configurable from 30 to 100 Hz). Network operations MUST NOT run on the main thread. |
| COM-3 | **Latest state wins.** Each packet carries the newest available sensor snapshot. The app MUST NOT queue old samples for later delivery; if sending falls behind, old data is dropped. |
| COM-4 | The full button bitmask MUST be included in every packet (Section 8.4). In addition, a **change in button state SHOULD trigger an immediate extra packet**, so that clicks are not delayed until the next send tick. |
| COM-5 | The sequence number MUST increase by one per packet and wrap at 65535. |
| COM-6 | The send path MUST reuse its buffers. No allocation per packet. |
| COM-7 | Socket errors (for example, `IOException`) MUST be handled without crashing the app. The app SHOULD count errors and show them in the status display. |
| COM-8 | **Connection handling.** On connect, the app sends `HELLO` and retries every second until `HELLO_ACK` is received. Once connected, it sends `PING` about once per second to measure latency. If nothing is received for 2 seconds, the app MUST declare the link lost, display "Disconnected", and retry automatically with a short backoff (for example, 1 s, 2 s, 4 s, capped at 5 s). No user action is required to recover. |
| COM-9 | While streaming, the app SHOULD hold a **Wi-Fi lock** in low-latency mode where available (Android 10 / API 29 and later) and in high-performance mode otherwise, and release it when streaming stops. This requires the `WAKE_LOCK` permission. Low-latency mode generally applies only while the app is in the foreground with the screen on. |
| COM-10 | If the phone is connected to a Wi-Fi network without internet access (for example, a laptop hotspot), the app SHOULD bind its socket to that Wi-Fi network (through `ConnectivityManager`), so that traffic is not routed over mobile data. |
| COM-11 | The screen MUST stay awake while the controller screen is active. If streaming must continue with the screen off, the app MUST use a foreground service. |
| COM-12 | The app MUST write the protocol version into every packet and MUST ignore any received message with an unknown version or type. |
| COM-13 | The simulator address and port MUST be configurable and saved between sessions. No address may be hard-coded. |
| COM-14 | The app MAY set the low-delay traffic class on the socket. Many networks ignore it, so correct operation MUST NOT depend on it. |

#### 9.8.4 Simulator-Side Rules for Seamless Communication

| ID | Rule |
|---|---|
| SIM-1 | The simulator MUST receive packets on its own thread or task, independent of the render loop, and MUST NOT perform heavy work inside the receive path. |
| SIM-2 | The simulator MUST bind to all interfaces (`0.0.0.0`) and print every local IP address and the port at startup, so the address can be entered in the app. |
| SIM-3 | The simulator MUST discard duplicate and older packets using the sequence number with wraparound handling (Section 8.5), and ignore packets with a wrong magic value, size, or version. |
| SIM-4 | The simulator MUST mark the device as disconnected after 2 seconds without packets and recover automatically when packets resume. |
| SIM-5 | The simulator SHOULD display the packet rate, estimated packet loss (from sequence gaps), and latency, to make link problems visible. |
| SIM-6 | If the host firewall blocks the port, it MUST be opened for UDP (for example, `sudo ufw allow 9000/udp` on systems using UFW; use your own port). |

#### 9.8.5 User Interface Rules

| ID | Rule |
|---|---|
| UI-1 | The UI MUST stay thin: connection fields, a status display, and the control buttons only. No sensor processing in the UI layer. |
| UI-2 | Button presses MUST update a single shared bitmask atomically, and multi-touch MUST be supported (for example, holding Rotate while pressing Zoom). |
| UI-3 | The UI MUST NOT block, or share a thread with, the sensor or sender threads. Avoid heavy animations. |
| UI-4 | Buttons SHOULD be large and easy to hit without looking, with optional haptic feedback. |
| UI-5 | The screen orientation SHOULD be locked for a stable layout. The fused orientation is reported in the device's own frame, so it does not depend on the display rotation. |
| UI-6 | The status display SHOULD show: connection state, round-trip latency, actual packet rate, and which sensor sources are active. |

#### 9.8.6 Quality and Testing Rules

| ID | Rule |
|---|---|
| QA-1 | The packet encoder MUST have a unit test against a fixed "golden" packet, and the same bytes MUST be decoded correctly by the simulator's parser. |
| QA-2 | Logging inside the sensor and send paths MUST be disabled or limited to about once per second. |
| QA-3 | The app MUST request and handle runtime permissions gracefully, and MUST show a clear message if a required sensor is missing. |
| QA-4 | The app MUST be verified on at least one real phone before a release, since emulator sensors and network timing are not representative (Section 9.9.3). |

#### 9.8.7 Latency Budget (Target)

The end-to-end target in NFR-1 is 50 ms. The following allocation assumes a 100 Hz send rate and a 60 fps render loop.

| Stage | Target |
|---|---|
| Sensor sampling and fixed-rate sender | up to 10 ms |
| Network (local Wi-Fi, UDP) | up to 5 ms typical |
| Parsing and input mapping in the simulator | up to 2 ms |
| Terminal render (60 fps) | up to 16 ms |
| **Typical total** | **about 33 ms (margin to 50 ms)** |

These are targets, not guarantees. Wi-Fi congestion or a slow terminal can exceed them, which is why the system measures and displays latency (rule SIM-5).

### 9.9 Android Studio Setup and Visual Verification

Android Studio is used to build the app, to see how it looks, and to verify that it works, both on an emulator and on a real phone.

#### 9.9.1 Installation and Project Creation

1. Install the latest stable **Android Studio** on the Linux development machine. A JDK is bundled with it. The Android emulator requires hardware virtualization (KVM) on Linux.
2. Create a new project using **Empty Activity** (Jetpack Compose) or **Empty Views Activity** (XML), whichever the team prefers. Use the placeholders `<APP_NAME>`, `<PACKAGE_NAME>`, and `<MIN_SDK>` for the project name, package, and minimum Android version. Choose Kotlin or Java as the language (Section 9.1).
3. Declare the permissions in `AndroidManifest.xml` as needed:

| Permission | Purpose |
|---|---|
| `INTERNET` | UDP communication |
| `ACCESS_NETWORK_STATE` | Binding to the Wi-Fi network (COM-10) |
| `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE` | Wi-Fi lock and network information (COM-9) |
| `WAKE_LOCK` | Wi-Fi lock and keeping the device awake |
| `FOREGROUND_SERVICE` | Only if streaming with the screen off (COM-11) |
| `HIGH_SAMPLING_RATE_SENSORS` | Only if sampling above 200 Hz (SEN-1) |

#### 9.9.2 Checking How the App Looks

- Use the **Preview** pane (Compose Preview) or the **Layout Editor** (XML) to see the screens while editing.
- Run the app on an emulator from **Device Manager** (create a virtual phone with a recent system image) to see the real appearance and behavior at different screen sizes.
- Use **Layout Inspector** to examine the running UI if a layout looks wrong.

#### 9.9.3 Testing on the Emulator

- **Virtual sensors.** In the emulator window, open **Extended controls (the "..." button) and choose Virtual sensors**. The Device Pose controls move and rotate the virtual phone, and the additional sensor controls set accelerometer and gyroscope values. Which sensor types are available depends on the emulator version and system image. In particular, verify whether the game rotation vector is present (the app's status display from rule UI-6 shows this); if it is not, use the fallback in rule SEN-2 and complete the test on a real phone.
- **Reaching the simulator.** Inside the emulator, the host computer is reachable at the special address **`10.0.2.2`**. When the simulator runs on the same Linux machine as the emulator, enter `10.0.2.2` and the simulator's port in the app.
- **What the emulator proves.** The UI layout, button handling, packet format, and the full communication path from app to simulator.
- **What it does not prove.** Real sensor noise, real motion feel, and real Wi-Fi latency.

#### 9.9.4 Testing on a Real Phone

1. Enable **Developer options** and **USB debugging** on the phone, connect it by USB, and run the app from Android Studio.
2. For cable-free testing, use **Wireless debugging** (Android 11 and later) and pair the phone from Device Manager.
3. Recent versions of Android Studio can **mirror the phone screen inside the IDE** (Running Devices window), so the app can be seen and operated from the computer while it runs.
4. In the app, enter the Linux machine's **LAN IP address** (printed by the simulator at startup, rule SIM-2) and the port. Both devices must be on the same network or hotspot (Section 5.1).

#### 9.9.5 Verification Checklist

| Check | How | Expected result |
|---|---|---|
| App appearance | Preview and emulator | Screens and buttons render correctly |
| Packets leave the app | Logcat (limited logging, rule QA-2) | Steady send-rate message about once per second |
| Packets reach the computer | On Linux: `sudo tcpdump -i any -n udp port <PORT>` | About the configured number of packets per second, each 52 bytes of payload |
| Packets decode correctly | Run the Python receiver (Section 10.6) | Quaternion, gyro, acceleration, and buttons change as the phone is moved and buttons are pressed |
| Buttons | Press every button, including combinations | Correct bits change in the received data |
| Connection recovery | Turn Wi-Fi off and on, restart the simulator | Both sides recover automatically (COM-8, SIM-4) |
| Latency and feel | Real phone only | Within the target of Section 9.8.7 |

---

## 10. Linux Terminal Simulator Design

### 10.1 Technology Options

| Option | Notes |
|---|---|
| **Python** (`asyncio`, `numpy`, `curses` or `rich`) | Fastest to prototype, adequate performance for a modest voxel grid |
| **C++ / Rust** (`ncurses` / `crossterm`) | Higher performance for large grids or high frame rates |

**Recommendation:** prototype in Python, and move the rendering core to a faster language only if performance requires it.

### 10.2 Modules

```
simulator/
 |-- net/         UDP receiver, packet parser, connection state
 |-- input/       calibration, filtering, cursor mapper, rotation mapper
 |-- scene/       voxel grid, 3D objects, camera, cursor
 |-- render/      projection, depth buffer, terminal drawing
 |-- config/      sensitivity, grid size, colors, port
 |-- app.py       main loop (receive -> update -> render)
```

### 10.3 The Simulated 3D LED Monitor

- The monitor is a 3D array `grid[W][H][D]` of voxels, each holding an on/off state or an RGB color. Suggested starting size: `32 × 32 × 32`, configurable.
- 3D objects (cube, sphere, pyramid, or imported point sets) are rasterized into the grid by lighting the voxels they occupy.
- The scene has an **object orientation** (a quaternion), a **camera distance** (zoom), and a **cursor**.

### 10.4 Rendering in the Terminal

The terminal is a 2D grid of character cells, so the 3D scene must be projected to 2D.

1. Apply the object's rotation to each lit voxel's coordinates.
2. Project to 2D using perspective projection: `x' = x * f / (z + camera_distance)`, and similarly for `y`.
3. Use a **depth buffer** so closer voxels hide farther ones.
4. Draw to the terminal. To double vertical resolution, use the half-block character (`▀`) with a foreground and background color per cell (24-bit color), which gives two "pixels" per character cell.
5. Draw the cursor last so it is always visible.
6. Optionally, draw the monitor's bounding box wireframe to convey the 3D volume.

Use differential updates (redraw only changed cells) and a double buffer to reduce flicker.

### 10.5 Input Processing (Mapping Math)

**Relative orientation.** Let `q_ref` be the reference quaternion (set at Recenter) and `q_now` the current one:

```
q_rel = inverse(q_ref) * q_now
```

Convert `q_rel` to yaw and pitch angles (in degrees).

**Cursor mapping.**

```
cursor_x = center_x + (yaw   / FOV_YAW)   * (grid_width  / 2)
cursor_y = center_y - (pitch / FOV_PITCH) * (grid_height / 2)
```

where `FOV_YAW` and `FOV_PITCH` are configurable (for example, 30 degrees). Clamp the cursor to the grid, then apply smoothing.

**Object rotation (Rotate held).**

```
delta_q    = q_now * inverse(q_prev)       // incremental phone rotation
object_q   = normalize(delta_q * object_q) // apply to object
q_prev     = q_now
```

**Zoom.**

```
if ZOOM_IN  pressed: camera_distance -= zoom_speed * dt
if ZOOM_OUT pressed: camera_distance += zoom_speed * dt
camera_distance = clamp(camera_distance, MIN, MAX)
```

**Clicks.** Detect the transition from released to pressed (rising edge) to generate a click event, and the held state for drag operations.

### 10.6 Reference Snippet: Python Receiver

```python
import asyncio
import struct

PACKET_FORMAT = "<HBBHHI10f"   # 52 bytes
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)
MAGIC = 0x3D4D

class SensorProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_sample):
        self.on_sample = on_sample
        self.last_seq = None

    def datagram_received(self, data, addr):
        if len(data) != PACKET_SIZE:
            return
        magic, version, mtype, seq, buttons, ts, *f = struct.unpack(PACKET_FORMAT, data)
        if magic != MAGIC or version != 1 or mtype != 1:
            return
        if self.last_seq is not None:
            diff = (seq - self.last_seq) & 0xFFFF
            if diff == 0 or diff > 0x8000:   # duplicate or older packet
                return
        self.last_seq = seq
        sample = {
            "buttons": buttons,
            "ts": ts,
            "q": f[0:4],       # w, x, y, z
            "gyro": f[4:7],
            "acc": f[7:10],
        }
        self.on_sample(sample)

async def main():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: SensorProtocol(lambda s: print(s)),
        local_addr=("0.0.0.0", 9000),
    )
    await asyncio.Event().wait()

asyncio.run(main())
```

### 10.7 Threading Model

Run the network receiver and the render loop independently. The receiver updates a "latest sample" variable; the render loop reads it at its own frame rate. This prevents a slow frame from delaying packet reception.

---

## 11. Development Roadmap

| Phase | Deliverable | Verification |
|---|---|---|
| 1 | **Protocol and mock sender.** A script that sends synthetic packets (for example, a rotating quaternion) to the simulator. | Simulator prints received samples correctly |
| 2 | **Simulator core.** UDP receiver, voxel grid, simple object, terminal renderer with a keyboard fallback. | A static 3D cube renders and rotates using keyboard input |
| 3 | **Mobile app (sensors and UDP).** Connection screen, sensor streaming, button bitmask. | Simulator shows live phone data |
| 4 | **Cursor control.** Orientation-to-cursor mapping, recentering, smoothing. | Cursor follows phone tilt smoothly |
| 5 | **Rotate, zoom, clicks.** Full control scheme. | Object rotates while Rotate is held; zoom and clicks work |
| 6 | **Polish.** Connection recovery, latency display, settings, QR pairing, documentation. | Stable 30-minute session |
| 7 | **Optional extensions.** Bluetooth LE transport, depth gesture, multiple objects. | As defined at that time |

**Tip:** build the **mock sender** and a **keyboard-controlled simulator** first, and use the Android Studio emulator (Section 9.9) to check the mobile UI and packet flow before testing on a real phone. This allows the simulator and the mobile app to be developed and tested independently.

---

## 12. Testing Plan

| Test | Method | Expected Result |
|---|---|---|
| Packet integrity | Unit tests encoding and decoding sample packets on both sides | Values round-trip exactly |
| Sensor accuracy | Rotate the phone by known angles (for example, 90 degrees) and compare with the simulator's reading | Error within a few degrees |
| Latency | Use `PING` / `PONG` and timestamps; optionally record screen and phone motion on video | Below 50 ms |
| Packet loss | Simulate loss using `tc netem` on Linux | Cursor remains stable, no large jumps |
| Drift | Hold the phone still for 5 minutes | Cursor movement stays within tolerance |
| Reconnection | Toggle Wi-Fi off and on | Both sides recover automatically |
| Button handling | Press all buttons, including multi-touch combinations | Correct events in the simulator |
| Performance | Large grids (for example, 64 × 64 × 64) | Frame rate target met or documented limits |

---

## 13. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Position drift if accelerometer position tracking is attempted | Unusable cursor | Use orientation-based control (Section 6.3) |
| Wi-Fi latency spikes or interference | Jittery cursor | Use UDP, smoothing, and a dedicated or hotspot network |
| Different sensor sampling rates across phones | Inconsistent feel | Fixed-rate sender, time-based (not sample-based) processing |
| Terminal resolution limits | Coarse visuals | Half-block characters, adjustable grid size |
| Wi-Fi client isolation on institutional networks | Phone cannot reach the simulator | Use a phone or laptop hotspot (Section 5.1) |
| Magnetic interference | Heading errors | Use game rotation vector (no magnetometer) |
| Hand tremor | Shaky cursor | Dead zone and smoothing |

---

## 14. Future Extensions

- Real OS pointer integration on Linux using `uinput` (a virtual input device), so the phone can control the desktop mouse.
- Bluetooth LE transport and automatic discovery.
- Depth gesture control and a full 3D cursor.
- Additional gestures (flick, shake to reset, pinch for zoom).
- Visual calibration wizard in the mobile app.
- Support for multiple objects, object selection, and moving objects with the cursor.
- Recording and playback of motion sessions for debugging.

---

## 15. Glossary

| Term | Meaning |
|---|---|
| IMU | Inertial Measurement Unit; the group of motion sensors (gyroscope, accelerometer) in a phone |
| Quaternion | A four-number representation of 3D orientation that avoids gimbal lock |
| Yaw / Pitch / Roll | Rotation about the vertical, side-to-side, and front-to-back axes respectively |
| Voxel | A 3D pixel; here, a single LED in the 3D matrix monitor |
| UDP | A lightweight network protocol with low latency and no delivery guarantee |
| BLE | Bluetooth Low Energy |
| Sensor fusion | Combining multiple sensors to obtain a more accurate estimate than any one alone |
| Dead zone | A small input range that is ignored to suppress noise |

---

## 16. Open Items (To Be Decided by the Team)

- [x] Mobile platform: Android native, built in Android Studio; implementation language and UI toolkit not mandated (Section 9.1)
- [ ] Minimum Android version: `<MIN_SDK>`
- [x] Transport for version 0.1: Wi-Fi over UDP only
- [ ] Voxel grid size and color depth: `<W × H × D>`
- [ ] Default UDP port: `<PORT>`
- [ ] Default sensor streaming rate: `<RATE_HZ>`
- [ ] Sensitivity values (`FOV_YAW`, `FOV_PITCH`): `<VALUES>`
- [ ] Whether and when to add Bluetooth LE or iOS support: `<DECISION_DATE>`
- [ ] Repository locations and naming: `<REPOSITORY_LINKS>`

---

## 17. Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | `<DATE>` | `<AUTHOR>` | Initial draft |
| 0.2 | `<DATE>` | `<AUTHOR>` | Added selected technology stack; finalized Wi-Fi/UDP-only transport and Kotlin/Compose for the mobile app; deferred Bluetooth and iOS |
| 0.3 | `<DATE>` | `<AUTHOR>` | Made mobile language and UI toolkit non-mandatory; added mobile development rules (Section 9.8) and Android Studio setup and verification (Section 9.9) |
