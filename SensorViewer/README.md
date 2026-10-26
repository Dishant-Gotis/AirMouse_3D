# AirMouse 3D — Laptop Sensor Hub & Visualizer

A real-time telemetry dashboard and UDP receiver for the **AirMouse3D** Android controller application.

---

## 🚀 Quick Start

### 1. Launch the Server
Double-click `run.bat` or run:
```powershell
python server.py
```
This will:
- Start the UDP listener on **`0.0.0.0:9000`**
- Start the Web Dashboard server on **`http://localhost:8080`**
- Automatically open your default web browser to the dashboard

### 2. Connect Your Android Phone
1. Ensure your laptop and Android phone are connected to the **same Wi-Fi network**.
2. Open the **AirMouse 3D** app on your phone.
3. On the connection screen:
   - **Host IP**: Enter the IP displayed at the top of the laptop dashboard (e.g., `192.168.1.44`).
   - **Port**: `9000`
   - **Rate**: `60 Hz`
4. Tap **CONNECT**.
5. Sensor motion (Delta X, Y, Z), button states (Left, Orbit, Zoom, Calibrate), and real-time 3D rotation will appear immediately on your laptop screen!

---

## 🧪 Testing Without a Phone
You can test the UI at any time:
- Click the **Test Simulation** button in the top right of the dashboard.
- Or run: `python server.py --mock`

This feeds simulated 60 Hz orbital motion, button presses, and calibration events into the dashboard.

---

## 📊 Features
- **Real-time 3D Device Visualization**: Realistic 3D phone model tilts, rolls, and rotates with phone movements.
- **2D Cursor Motion Trail**: Trajectory canvas plotting continuous $(X, Y)$ movement.
- **Bidirectional Delta Meters**: High-precision indicators for Delta X, Y, and Z.
- **Button Telemetry Matrix**: Glowing LED state indicators for Left Click, Orbit Mode, Zoom, and Calibrate.
- **Calibration Frame**: Live orthogonal basis vectors (`forward`, `up`, `right`) when calibration is triggered.
- **Packet Telemetry**: Exact Hz rate meter, sequence check, and packet drop counter.
- **Live JSON Inspector**: View and copy incoming raw UDP JSON datagrams.
