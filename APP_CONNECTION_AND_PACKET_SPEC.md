# AirMouse 3D — App Connection Lifecycle & Packet Protocol Specification

This document details:
1. **Everything the Android application does step-by-step after the user presses the "CONNECT" button**.
2. **The complete UDP JSON packet format, field meanings, units, and ranges**.
3. **Realistic example packets** for all operation modes (neutral motion, left click, orbit, zoom, and calibration).

---

## 1. What the App Does After Pressing "CONNECT"

```
[ User Taps CONNECT ]
         │
         ▼
 1. Validate Host IP, Port & Rate (10–100 Hz)
 2. Save settings to SharedPreferences ("airm_prefs")
 3. Launch ControllerActivity with Intent extras
         │
         ▼
 4. Acquire Screen WakeLock (FLAG_KEEP_SCREEN_ON)
 5. Initialize UdpTransport(host, port)
 6. Start Dedicated HandlerThread ("SensorThread")
 7. Register Hardware Sensors (Delay: 10,000 µs = 100 Hz):
    ├── TYPE_GAME_ROTATION_VECTOR (fallback: TYPE_ROTATION_VECTOR)
    ├── TYPE_GYROSCOPE
    └── TYPE_LINEAR_ACCELERATION (fallback: TYPE_ACCELEROMETER)
 8. Establish Initial Calibration Reference Quaternion
 9. Start High-Frequency Sender Loop (ScheduledExecutorService @ 60 Hz)
10. Start In-App UI HUD Updater (12.5 Hz refresh)
         │
         ▼
[ Continuous 60 Hz Loop: Compute Delta → Read Buttons → Encode JSON → Send UDP ]
```

### Detailed Step-by-Step Execution:

### Step 1: Input Validation & Persistence (`ConnectionActivity.kt`)
- Validates that the **Host IP** is non-empty, the **Port** is between `1` and `65535`, and the **Rate** is between `10` and `100 Hz`.
- Saves these values into `SharedPreferences` so they auto-populate on subsequent launches.
- Creates an Intent with `EXTRA_HOST`, `EXTRA_PORT`, and `EXTRA_RATE`, then launches `ControllerActivity`.

### Step 2: Screen WakeLock (`ControllerActivity.kt`)
- Calls `window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)` to ensure the mobile display never sleeps while controlling the computer or 3D scene.

### Step 3: Hardware Sensor Registration (`MotionSender.kt`)
- Creates a dedicated background thread named `SensorThread` (with its own `Looper`) so sensor hardware interrupts do not stutter the Android UI.
- Registers listeners for:
  - **Rotation Vector** (`TYPE_GAME_ROTATION_VECTOR`, fallback to `TYPE_ROTATION_VECTOR`): Provides uncalibrated or calibrated orientation quaternions $[q_w, q_x, q_y, q_z]$ immune to compass drift.
  - **Gyroscope** (`TYPE_GYROSCOPE`): Angular velocity $[g_x, g_y, g_z]$ in rad/s.
  - **Linear Acceleration** (`TYPE_LINEAR_ACCELERATION`, fallback to `TYPE_ACCELEROMETER`): Acceleration $[a_x, a_y, a_z]$ excluding gravity.

### Step 4: Network Socket Initialization (`UdpTransport.kt`)
- Allocates an unbonded UDP `DatagramSocket`.
- Resolves the destination hostname or IPv4 address into an `InetAddress` cache to avoid DNS latency during the real-time loop.

### Step 5: Relative Reference Calibration
- Captures the initial phone orientation quaternion at the moment of connection:
  $$\mathbf{q}_{\text{ref}} = [q_w, q_x, q_y, q_z]$$
- All subsequent movements are calculated relative to this frame.

### Step 6: 60 Hz High-Frequency Send Loop (`MotionSender.kt`)
A single-threaded `ScheduledExecutorService` runs on a fixed period:
$$\Delta t = \frac{1\,000\,000\,\mu\text{s}}{\text{rateHz}} \approx 16\,666\,\mu\text{s}\quad(60\text{ Hz})$$

On **each tick**:
1. **Computes Relative Quaternion**:
   $$\mathbf{q}_{\text{rel}} = \mathbf{q}_{\text{ref}}^{*} \otimes \mathbf{q}_{\text{current}}$$
2. **Extracts Relative Euler Angles**:
   - Relative Yaw (horizontal deflection)
   - Relative Pitch (vertical deflection)
3. **Calculates Frame-to-Frame Delta**:
   $$\Delta x = \text{Yaw}_{\text{current}} - \text{Yaw}_{\text{prev}}$$
   $$\Delta y = \text{Pitch}_{\text{current}} - \text{Pitch}_{\text{prev}}$$
   *(Includes $360^\circ$ angular wraparound compensation).*
4. **Inspects Button Bitmask**:
   Atomically reads multi-touch state from `buttonBits`:
   - `left`: `true` if LEFT button touched
   - `orbit`: `true` if ORBIT (ROTATE) button touched
   - `zoom`: `true` if ZOOM IN or ZOOM OUT touched
   - If Zoom In is pressed: $\Delta z = +1.0$
   - If Zoom Out is pressed: $\Delta z = -1.0$
   - Otherwise: $\Delta z = 0.0$
5. **Increments Sequence Counter**:
   `seq = seq.getAndIncrement()` (monotonically increasing integer starting at 0).
6. **Encodes to UTF-8 JSON**:
   Uses `PacketEncoder.encodeInput()` to build the JSON string and converts it to UTF-8 bytes.
7. **Transmits UDP Datagram**:
   Sends the packet over UDP to `host:port`.

### Step 7: In-App Sensor HUD Loop (`ControllerActivity.kt`)
Every 80 ms (~12.5 Hz), the UI reads a `SensorSnapshot` and updates the on-screen display:
- Live Euler Angles: Yaw, Pitch, Roll in degrees
- Gyroscope rates ($g_x, g_y, g_z$ in rad/s)
- Linear Acceleration ($a_x, a_y, a_z$ in $\text{m/s}^2$)
- Current $\Delta x, \Delta y, \Delta z$
- Packets sent counter and transmission errors

### Step 8: Calibration Tap Event
When the user taps the **CALIBRATE** button:
1. `MotionSender.calibrate()` captures the current quaternion as the new $\mathbf{q}_{\text{ref}}$.
2. Rotates standard basis vectors $[0,0,1]$, $[0,1,0]$, $[1,0,0]$ by the new reference quaternion to calculate `forward`, `up`, and `right` 3D direction vectors.
3. Transmits an out-of-band `type: "calibrate"` JSON packet.

---

## 2. Packet Protocol Specifications

The app sends **two distinct packet formats** over UDP:

### A. Periodic Motion Packet (`type: "input"`)
Sent every tick at 60 Hz.

| Field | Type | Description |
| :--- | :--- | :--- |
| `version` | `Integer` | Protocol version (always `1`). |
| `device_id` | `String` | Unique hardware/device identifier (default `"mobile-01"`). |
| `seq` | `Integer` | Monotonically increasing packet sequence number (0, 1, 2, ...). Used by receiver to detect dropped packets and jitter. |
| `type` | `String` | Packet category identifier: `"input"`. |
| `delta` | `Object` | Relative movement vector since the previous update: |
| `delta.x` | `Float` | Relative horizontal rotation (yaw change in degrees, rounded to 4 decimals). Positive = rotated right, Negative = rotated left. |
| `delta.y` | `Float` | Relative vertical rotation (pitch change in degrees, rounded to 4 decimals). Positive = tilted up, Negative = tilted down. |
| `delta.z` | `Float` | Relative depth / zoom movement. `+1.0` during Zoom In, `-1.0` during Zoom Out, `0.0` when idle. |
| `buttons` | `Object` | Current synchronized button states: |
| `buttons.left` | `Boolean` | `true` when Left Click is pressed/held, otherwise `false`. |
| `buttons.orbit` | `Boolean` | `true` when Orbit / Rotate button is held, otherwise `false`. |
| `buttons.zoom` | `Boolean` | `true` when either Zoom In or Zoom Out button is held, otherwise `false`. |
| `buttons.calibrate` | `Boolean` | `true` during the single tick in which calibration was triggered, otherwise `false`. |

---

### B. Discrete Calibration Packet (`type: "calibrate"`)
Sent immediately when the user taps **CALIBRATE**.

| Field | Type | Description |
| :--- | :--- | :--- |
| `version` | `Integer` | Protocol version (always `1`). |
| `device_id` | `String` | Unique hardware/device identifier (e.g. `"mobile-01"`). |
| `seq` | `Integer` | Shares the monotonic sequence counter with input packets. |
| `type` | `String` | Packet category identifier: `"calibrate"`. |
| `reference` | `Object` | Orthogonal 3D basis vectors computed from the phone's orientation: |
| `reference.forward` | `Array[3]` | $[x, y, z]$ unit vector representing the phone's pointing direction. |
| `reference.up` | `Array[3]` | $[x, y, z]$ unit vector representing the phone's top edge pointing direction. |
| `reference.right` | `Array[3]` | $[x, y, z]$ unit vector representing the phone's right edge pointing direction. |

---

## 3. Concrete Example Packets

### Example 1: Neutral / Idle Input Packet
*The phone is resting still or held steady. No buttons pressed.*
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1024,
  "type": "input",
  "delta": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
  },
  "buttons": {
    "left": false,
    "orbit": false,
    "zoom": false,
    "calibrate": false
  }
}
```

---

### Example 2: Active Diagonal Panning Movement
*User turned the phone slightly right ($\Delta x = +0.1425^\circ$) and tilted up ($\Delta y = +0.0812^\circ$).*
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1025,
  "type": "input",
  "delta": {
    "x": 0.1425,
    "y": 0.0812,
    "z": 0.0
  },
  "buttons": {
    "left": false,
    "orbit": false,
    "zoom": false,
    "calibrate": false
  }
}
```

---

### Example 3: Left-Click & Drag Motion
*User is holding the LEFT button while moving downward and left.*
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1026,
  "type": "input",
  "delta": {
    "x": -0.215,
    "y": -0.3418,
    "z": 0.0
  },
  "buttons": {
    "left": true,
    "orbit": false,
    "zoom": false,
    "calibrate": false
  }
}
```

---

### Example 4: 3D Scene Orbiting
*User is holding the ORBIT button while rotating the phone to orbit the 3D model.*
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1027,
  "type": "input",
  "delta": {
    "x": 0.421,
    "y": -0.1105,
    "z": 0.0
  },
  "buttons": {
    "left": false,
    "orbit": true,
    "zoom": false,
    "calibrate": false
  }
}
```

---

### Example 5: Zooming In
*User is holding the ZOOM IN button.*
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1028,
  "type": "input",
  "delta": {
    "x": 0.012,
    "y": -0.005,
    "z": 1.0
  },
  "buttons": {
    "left": false,
    "orbit": false,
    "zoom": true,
    "calibrate": false
  }
}
```

---

### Example 6: Discrete Calibration Packet
*User tapped the CALIBRATE button. The phone captures its current orientation as the reference frame.*
```json
{
  "version": 1,
  "device_id": "mobile-01",
  "seq": 1029,
  "type": "calibrate",
  "reference": {
    "forward": [0.0345, -0.1204, 0.9921],
    "up": [0.0121, 0.9926, 0.1204],
    "right": [0.9993, -0.0079, -0.0358]
  }
}
```

---

## 4. Summary Table of Button Mappings

| In-App Button | Protocol Field | Associated Action |
| :--- | :--- | :--- |
| **LEFT** | `buttons.left` | Left mouse click or object selection. |
| **ROTATE (ORBIT)** | `buttons.orbit` | Activates camera orbit / rotational viewpoint. |
| **ZOOM IN** | `buttons.zoom: true`, `delta.z: +1.0` | Zooms camera closer / moves object forward. |
| **ZOOM OUT** | `buttons.zoom: true`, `delta.z: -1.0` | Zooms camera farther / moves object backward. |
| **CALIBRATE** | `type: "calibrate"` | Resets zero orientation reference frame. |
