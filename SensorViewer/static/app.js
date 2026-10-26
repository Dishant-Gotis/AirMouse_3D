/**
 * AirMouse 3D — Telemetry Hub & Visualizer Client Logic
 */

// State variables
let ws = null;
let reconnectTimer = null;
let lastPacketTime = 0;
let isStreamPaused = false;
let latestPacketJson = "";

// 3D Orientation state
let phonePitch = 15;
let phoneRoll = -20;
let phoneYaw = 0;

// 2D Canvas Trajectory state
let trailPoints = [];
const MAX_TRAIL_POINTS = 60;
let cursorX = 180;
let cursorY = 130;

// DOM Elements
const connectionDot = document.getElementById("connection-dot");
const connectionStatus = document.getElementById("connection-status");
const displayIp = document.getElementById("display-ip");
const footerIp = document.getElementById("footer-ip");
const copyIpBtn = document.getElementById("copy-ip-btn");
const toggleMockBtn = document.getElementById("toggle-mock-btn");
const mockDot = document.getElementById("mock-dot");
const mockBtnText = document.getElementById("mock-btn-text");
const resetStatsBtn = document.getElementById("reset-stats-btn");

// Metrics
const statRate = document.getElementById("stat-rate");
const statRateBar = document.getElementById("stat-rate-bar");
const rateBadge = document.getElementById("rate-badge");
const statPackets = document.getElementById("stat-packets");
const statSeq = document.getElementById("stat-seq");
const statDropped = document.getElementById("stat-dropped");
const lossBadge = document.getElementById("loss-badge");
const statDevice = document.getElementById("stat-device");
const statSourceAddr = document.getElementById("stat-source-addr");
const sourceIpBadge = document.getElementById("source-ip-badge");

// Spatial & Gauges
const virtualPhone = document.getElementById("virtual-phone");
const phoneHudStatus = document.getElementById("phone-hud-status");
const btnRecenterView = document.getElementById("btn-recenter-view");
const btnClearCanvas = document.getElementById("btn-clear-canvas");
const canvas = document.getElementById("trajectory-canvas");
const ctx = canvas.getContext("2d");

const valDeltaX = document.getElementById("val-delta-x");
const valDeltaY = document.getElementById("val-delta-y");
const valDeltaZ = document.getElementById("val-delta-z");
const barDeltaX = document.getElementById("bar-delta-x");
const barDeltaY = document.getElementById("bar-delta-y");
const barDeltaZ = document.getElementById("bar-delta-z");

// Buttons
const btnCardLeft = document.getElementById("btn-state-left");
const txtBtnLeft = document.getElementById("txt-btn-left");
const btnCardOrbit = document.getElementById("btn-state-orbit");
const txtBtnOrbit = document.getElementById("txt-btn-orbit");
const btnCardZoom = document.getElementById("btn-state-zoom");
const txtBtnZoom = document.getElementById("txt-btn-zoom");
const btnCardCalib = document.getElementById("btn-state-calibrate");
const txtBtnCalib = document.getElementById("txt-btn-calib");

// Vectors
const vecForward = document.getElementById("vec-forward");
const vecUp = document.getElementById("vec-up");
const vecRight = document.getElementById("vec-right");
const lastCalibTime = document.getElementById("last-calib-time");

// Inspector
const rawJsonStream = document.getElementById("raw-json-stream");
const btnPauseStream = document.getElementById("btn-pause-stream");
const btnCopyJson = document.getElementById("btn-copy-json");

// =============================================================================
// WebSocket Connection
// =============================================================================
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  updateConnectionStatus("connecting", "Connecting to local hub...");

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    updateConnectionStatus("connected", "Listening on UDP 9000 (Waiting for app)");
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleServerMessage(msg);
    } catch (e) {
      console.error("Failed to parse incoming WS message:", e);
    }
  };

  ws.onclose = () => {
    updateConnectionStatus("offline", "Disconnected from Hub (Retrying...)");
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => {
    ws.close();
  };
}

function updateConnectionStatus(state, message) {
  connectionDot.className = "status-dot";
  if (state === "live") {
    connectionDot.classList.add("active");
  } else if (state === "offline") {
    connectionDot.classList.add("offline");
  }
  connectionStatus.textContent = message;
}

// Watchdog timer to transition from LIVE -> IDLE if no packet received in 1.5s
setInterval(() => {
  const now = Date.now();
  if (lastPacketTime > 0 && now - lastPacketTime > 1500) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      updateConnectionStatus("idle", "UDP Socket Listening (Standby)");
      phoneHudStatus.textContent = "STANDBY";
      phoneHudStatus.style.color = "#F59E0B";
      statRate.textContent = "0.0";
      statRateBar.style.width = "0%";
    }
  }
}, 500);

// =============================================================================
// Message Handling
// =============================================================================
function handleServerMessage(msg) {
  if (msg.event === "server_info") {
    handleServerInfo(msg);
  } else if (msg.event === "sensor_data") {
    handleSensorData(msg);
  } else if (msg.event === "mock_status") {
    updateMockUI(msg.mock_running);
  } else if (msg.event === "stats_reset") {
    statPackets.textContent = "0";
    statDropped.textContent = "0";
    statRate.textContent = "0.0";
    statSeq.textContent = "--";
    lossBadge.textContent = "0.0%";
  }
}

function handleServerInfo(info) {
  const primaryIp = (info.ips && info.ips.length > 0) ? info.ips[0] : "127.0.0.1";
  const port = info.udp_port || 9000;
  displayIp.textContent = `${primaryIp}:${port}`;
  footerIp.textContent = primaryIp;
  updateMockUI(info.mock_running);
}

function handleSensorData(payload) {
  lastPacketTime = Date.now();
  updateConnectionStatus("live", `Live Stream (${payload.stats.rate_hz.toFixed(1)} Hz)`);

  const data = payload.data;
  const pStats = payload.stats;

  // 1. Update Metrics
  statRate.textContent = pStats.rate_hz.toFixed(1);
  const fillPct = Math.min(100, (pStats.rate_hz / 60) * 100);
  statRateBar.style.width = `${fillPct}%`;
  rateBadge.textContent = `${pStats.rate_hz.toFixed(0)} Hz Actual`;

  statPackets.textContent = pStats.total_packets.toLocaleString();
  statSeq.textContent = pStats.last_seq !== -1 ? `#${pStats.last_seq}` : "--";

  statDropped.textContent = pStats.dropped_packets;
  const total = pStats.total_packets + pStats.dropped_packets;
  const lossPct = total > 0 ? ((pStats.dropped_packets / total) * 100).toFixed(2) : "0.00";
  lossBadge.textContent = `${lossPct}%`;
  lossBadge.className = pStats.dropped_packets > 0 ? "metric-badge warning" : "metric-badge accent";

  statDevice.textContent = data.device_id || "mobile";
  statSourceAddr.textContent = `Via ${payload.source}`;
  sourceIpBadge.textContent = payload.source.split(":")[0];

  phoneHudStatus.textContent = "RECEIVING";
  phoneHudStatus.style.color = "#10B981";

  // 2. Handle Packet Types
  if (data.type === "input" && data.delta) {
    updateMotionData(data.delta);
    if (data.buttons) {
      updateButtonStates(data.buttons);
    }
  } else if (data.type === "calibrate") {
    handleCalibrationPacket(data);
  }

  // 3. Raw JSON Inspector
  if (!isStreamPaused) {
    latestPacketJson = JSON.stringify(data, null, 2);
    rawJsonStream.textContent = latestPacketJson;
  }
}

// =============================================================================
// Motion & 3D Visualization
// =============================================================================
function updateMotionData(delta) {
  const dx = delta.x || 0;
  const dy = delta.y || 0;
  const dz = delta.z || 0;

  // Numeric text updates
  valDeltaX.textContent = dx.toFixed(4);
  valDeltaY.textContent = dy.toFixed(4);
  valDeltaZ.textContent = dz.toFixed(4);

  // Meter gauges (-1.0 to +1.0 mapped to 0-100% center gauge)
  updateGaugeBar(barDeltaX, dx);
  updateGaugeBar(barDeltaY, dy);
  updateGaugeBar(barDeltaZ, dz);

  // Update 3D Phone Perspective
  // Mobile delta tilt: Pitch (Y), Roll (X), Yaw (Z)
  phonePitch += dy * 8.0;
  phoneRoll  -= dx * 8.0;
  phoneYaw   += dz * 4.0;

  // Clamp slight perspective for visual stability
  phonePitch = Math.max(-65, Math.min(65, phonePitch));
  phoneRoll  = Math.max(-75, Math.min(75, phoneRoll));

  virtualPhone.style.transform = `rotateX(${phonePitch}deg) rotateY(${phoneRoll}deg) rotateZ(${phoneYaw}deg)`;

  // Update 2D Trajectory Canvas
  cursorX += dx * 70;
  cursorY += dy * 70;

  // Clamp within canvas bounds
  cursorX = Math.max(10, Math.min(canvas.width - 10, cursorX));
  cursorY = Math.max(10, Math.min(canvas.height - 10, cursorY));

  trailPoints.push({ x: cursorX, y: cursorY, alpha: 1.0 });
  if (trailPoints.length > MAX_TRAIL_POINTS) {
    trailPoints.shift();
  }

  drawTrajectoryCanvas();
}

function updateGaugeBar(element, val) {
  // val typically in [-1, 1], clamp
  const clamped = Math.max(-1.0, Math.min(1.0, val));
  if (clamped >= 0) {
    element.style.left = "50%";
    element.style.width = `${(clamped * 50).toFixed(1)}%`;
  } else {
    const width = Math.abs(clamped) * 50;
    element.style.left = `${(50 - width).toFixed(1)}%`;
    element.style.width = `${width.toFixed(1)}%`;
  }
}

function drawTrajectoryCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw subtle grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
  ctx.lineWidth = 1;
  const step = 30;
  for (let x = 0; x < canvas.width; x += step) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += step) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }

  // Draw motion path trail
  if (trailPoints.length > 1) {
    for (let i = 1; i < trailPoints.length; i++) {
      const p1 = trailPoints[i - 1];
      const p2 = trailPoints[i];
      const alpha = (i / trailPoints.length) * 0.8;

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = `rgba(0, 242, 254, ${alpha})`;
      ctx.lineWidth = 2.5;
      ctx.stroke();
    }
  }

  // Draw current cursor head
  if (trailPoints.length > 0) {
    const head = trailPoints[trailPoints.length - 1];
    ctx.beginPath();
    ctx.arc(head.x, head.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = "#00F2FE";
    ctx.shadowColor = "#00F2FE";
    ctx.shadowBlur = 12;
    ctx.fill();
    ctx.shadowBlur = 0;
  }
}

// =============================================================================
// Button States
// =============================================================================
function updateButtonStates(buttons) {
  setButtonActive(btnCardLeft, txtBtnLeft, buttons.left, "PRESSED", "RELEASED");
  setButtonActive(btnCardOrbit, txtBtnOrbit, buttons.orbit, "ACTIVE", "RELEASED");
  setButtonActive(btnCardZoom, txtBtnZoom, buttons.zoom, "ACTIVE", "RELEASED");
  setButtonActive(btnCardCalib, txtBtnCalib, buttons.calibrate, "TRIGGERED", "STANDBY");
}

function setButtonActive(card, textElem, isActive, activeText, inactiveText) {
  if (isActive) {
    card.classList.add("active");
    textElem.textContent = activeText;
  } else {
    card.classList.remove("active");
    textElem.textContent = inactiveText;
  }
}

// =============================================================================
// Calibration Packet
// =============================================================================
function handleCalibrationPacket(packet) {
  // Flash calibrate button
  btnCardCalib.classList.add("active");
  txtBtnCalib.textContent = "CALIBRATED!";
  setTimeout(() => {
    btnCardCalib.classList.remove("active");
    txtBtnCalib.textContent = "STANDBY";
  }, 1200);

  if (packet.reference) {
    const f = packet.reference.forward || [0, 0, 1];
    const u = packet.reference.up || [0, 1, 0];
    const r = packet.reference.right || [1, 0, 0];

    vecForward.textContent = `[${f.map(v => Number(v).toFixed(2)).join(", ")}]`;
    vecUp.textContent = `[${u.map(v => Number(v).toFixed(2)).join(", ")}]`;
    vecRight.textContent = `[${r.map(v => Number(v).toFixed(2)).join(", ")}]`;
  }

  const now = new Date();
  lastCalibTime.textContent = `Calibrated at ${now.toLocaleTimeString()}`;
  lastCalibTime.style.color = "#10B981";

  // Also recenter 3D view on calibration
  recenter3DView();
}

function recenter3DView() {
  phonePitch = 15;
  phoneRoll = -20;
  phoneYaw = 0;
  virtualPhone.style.transform = `rotateX(${phonePitch}deg) rotateY(${phoneRoll}deg) rotateZ(${phoneYaw}deg)`;
}

// =============================================================================
// Controls & UI Listeners
// =============================================================================
btnRecenterView.addEventListener("click", recenter3DView);

btnClearCanvas.addEventListener("click", () => {
  trailPoints = [];
  cursorX = canvas.width / 2;
  cursorY = canvas.height / 2;
  drawTrajectoryCanvas();
});

// Copy IP
copyIpBtn.addEventListener("click", async () => {
  try {
    const textToCopy = displayIp.textContent.trim();
    await navigator.clipboard.writeText(textToCopy);
    const originalText = displayIp.textContent;
    displayIp.textContent = "COPIED!";
    setTimeout(() => {
      displayIp.textContent = originalText;
    }, 1500);
  } catch (err) {
    console.error("Clipboard copy failed:", err);
  }
});

// Mock simulation toggle
toggleMockBtn.addEventListener("click", () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "toggle_mock" }));
  }
});

function updateMockUI(isRunning) {
  if (isRunning) {
    toggleMockBtn.classList.add("active");
    mockBtnText.textContent = "Stop Simulation";
  } else {
    toggleMockBtn.classList.remove("active");
    mockBtnText.textContent = "Test Simulation";
  }
}

// Reset stats
resetStatsBtn.addEventListener("click", () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "reset_stats" }));
  }
});

// Pause stream
btnPauseStream.addEventListener("click", () => {
  isStreamPaused = !isStreamPaused;
  btnPauseStream.textContent = isStreamPaused ? "Resume Stream" : "Pause Stream";
  btnPauseStream.classList.toggle("active", isStreamPaused);
});

// Copy JSON
btnCopyJson.addEventListener("click", async () => {
  if (latestPacketJson) {
    await navigator.clipboard.writeText(latestPacketJson);
    btnCopyJson.textContent = "Copied!";
    setTimeout(() => {
      btnCopyJson.textContent = "Copy JSON";
    }, 1200);
  }
});

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
  drawTrajectoryCanvas();
  connectWebSocket();
});
