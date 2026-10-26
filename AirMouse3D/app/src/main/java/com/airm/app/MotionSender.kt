package com.airm.app

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.HandlerThread
import android.os.SystemClock
import android.util.Log
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.math.atan2
import kotlin.math.asin
import kotlin.math.sqrt

/**
 * MotionSender — the heart of the mobile app.
 *
 * Updated for the new JSON-based UDP protocol:
 *   - Computes tilt-compensated delta (x, y, z) from quaternion changes
 *   - Sends JSON "input" packets at the configured rate
 *   - Supports discrete "calibrate" packets with reference-frame vectors
 *   - Exposes SensorSnapshot for the real-time sensor HUD
 *
 * Sensor data is still read via SensorEventListener on a dedicated thread (SEN-6).
 * The sender loop runs on a ScheduledExecutorService (COM-2).
 */
class MotionSender(
    private val sensorManager: SensorManager,
    val host: String,
    val port: Int,
    val rateHz: Int = 60,
) : SensorEventListener {

    data class SensorSnapshot(
        val qw: Float, val qx: Float, val qy: Float, val qz: Float,
        val gx: Float, val gy: Float, val gz: Float,
        val ax: Float, val ay: Float, val az: Float,
        val yawDeg: Float, val pitchDeg: Float, val rollDeg: Float,
        val deltaX: Float, val deltaY: Float, val deltaZ: Float,
        val packetsSent: Int, val sendErrors: Int,
    )

    // ── Sensor data buffers (SEN-5: only copy here, no alloc/IO) ─────────────
    @Volatile var qw = 1f; @Volatile var qx = 0f
    @Volatile var qy = 0f; @Volatile var qz = 0f
    @Volatile var gx = 0f; @Volatile var gy = 0f; @Volatile var gz = 0f
    @Volatile var ax = 0f; @Volatile var ay = 0f; @Volatile var az = 0f
    private val quaternion = FloatArray(4)

    // Shared button bitmask — set atomically from UI thread (COM-4)
    @Volatile var buttons: Int = 0

    // ── Delta computation state ──────────────────────────────────────────────
    // Reference quaternion (set on calibrate)
    @Volatile private var refQw = 1f; @Volatile private var refQx = 0f
    @Volatile private var refQy = 0f; @Volatile private var refQz = 0f

    // Previous frame euler angles (for computing delta)
    private var prevYaw = 0f
    private var prevPitch = 0f
    private var firstFrame = true

    // Last computed deltas (for snapshot)
    @Volatile private var lastDx = 0f
    @Volatile private var lastDy = 0f
    @Volatile private var lastDz = 0f

    // Calibrate request flag — set from UI thread, consumed by sender thread
    @Volatile var calibrateRequested = false

    // ── Internals ─────────────────────────────────────────────────────────────
    private val encoder    = PacketEncoder()
    private lateinit var transport: UdpTransport
    private val seq        = AtomicInteger(0)

    // Dedicated sensor handler thread (SEN-6)
    private val sensorThread  = HandlerThread("SensorThread").also { it.start() }
    private val sensorHandler = android.os.Handler(sensorThread.looper)

    // Fixed-rate sender on a scheduled thread pool (COM-2)
    private val senderExecutor  = Executors.newSingleThreadScheduledExecutor()
    private var senderFuture: ScheduledFuture<*>? = null

    // Stats
    var packetsSent: Int = 0; private set
    var sendErrors: Int  = 0; private set
    @Volatile private var running = false

    companion object {
        private const val TAG = "MotionSender"
        private const val SENSOR_DELAY_US = 10_000
        private const val MAX_LATENCY_US  = 0
    }

    // ── Public API ─────────────────────────────────────────────────────────────

    /**
     * Calibrate: store current orientation as the reference frame and
     * send a CALIBRATE packet with forward/up/right vectors.
     */
    fun calibrate() {
        // Store current orientation as reference
        refQw = qw; refQx = qx; refQy = qy; refQz = qz
        prevYaw   = 0f
        prevPitch = 0f
        firstFrame = true
        calibrateRequested = true
        Log.i(TAG, "Calibration requested — ref quat: [$refQw, $refQx, $refQy, $refQz]")
    }

    fun getSnapshot(): SensorSnapshot {
        val w = qw; val x = qx; val y = qy; val z = qz

        // Euler angles from raw quaternion (for display)
        val sinrCosp = 2.0 * (w * x + y * z)
        val cosrCosp = 1.0 - 2.0 * (x * x + y * y)
        val roll = Math.toDegrees(atan2(sinrCosp, cosrCosp)).toFloat()

        val sinp = (2.0 * (w * y - z * x)).coerceIn(-1.0, 1.0)
        val pitch = Math.toDegrees(asin(sinp)).toFloat()

        val sinyCosp = 2.0 * (w * z + x * y)
        val cosyCosp = 1.0 - 2.0 * (y * y + z * z)
        val yaw = Math.toDegrees(atan2(sinyCosp, cosyCosp)).toFloat()

        return SensorSnapshot(
            qw = w, qx = x, qy = y, qz = z,
            gx = gx, gy = gy, gz = gz,
            ax = ax, ay = ay, az = az,
            yawDeg = yaw, pitchDeg = pitch, rollDeg = roll,
            deltaX = lastDx, deltaY = lastDy, deltaZ = lastDz,
            packetsSent = packetsSent,
            sendErrors = sendErrors,
        )
    }

    fun start() {
        if (running) return
        running = true
        transport = UdpTransport(host, port)

        // Set initial calibration reference to current orientation
        refQw = qw; refQx = qx; refQy = qy; refQz = qz

        // Register sensors on dedicated thread (SEN-6)
        val sensors = listOf(
            Sensor.TYPE_GAME_ROTATION_VECTOR,
            Sensor.TYPE_GYROSCOPE,
            Sensor.TYPE_LINEAR_ACCELERATION,
        )
        var gameRotOk = false
        var linAccelOk = false
        for (type in sensors) {
            val sensor = sensorManager.getDefaultSensor(type)
            if (sensor == null) {
                Log.w(TAG, "Sensor type $type not available — skipping")
                continue
            }
            val ok = sensorManager.registerListener(
                this, sensor, SENSOR_DELAY_US, MAX_LATENCY_US, sensorHandler
            )
            if (type == Sensor.TYPE_GAME_ROTATION_VECTOR) gameRotOk = ok
            if (type == Sensor.TYPE_LINEAR_ACCELERATION) linAccelOk = ok
            Log.d(TAG, "Registered sensor type=$type ok=$ok")
        }

        // Fallback if game rotation vector not available (SEN-2)
        if (!gameRotOk) {
            Log.w(TAG, "Game rotation vector N/A — falling back to rotation vector")
            sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)?.let {
                sensorManager.registerListener(this, it, SENSOR_DELAY_US, MAX_LATENCY_US, sensorHandler)
            }
        }

        // Fallback for linear acceleration
        if (!linAccelOk) {
            Log.w(TAG, "Linear acceleration N/A — falling back to accelerometer")
            sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.let {
                sensorManager.registerListener(this, it, SENSOR_DELAY_US, MAX_LATENCY_US, sensorHandler)
            }
        }

        // Fixed-rate sender loop (COM-2)
        val periodUs = 1_000_000L / rateHz
        senderFuture = senderExecutor.scheduleAtFixedRate(
            ::sendPacket, 0L, periodUs, TimeUnit.MICROSECONDS
        )
        Log.i(TAG, "Started at $rateHz Hz → $host:$port (JSON protocol v${PacketEncoder.PROTOCOL_VERSION})")
    }

    fun stop() {
        if (!running) return
        running = false
        senderFuture?.cancel(false)
        sensorManager.unregisterListener(this)
        sensorThread.quitSafely()
        senderExecutor.shutdown()
        if (::transport.isInitialized) transport.close()
        Log.i(TAG, "Stopped. Sent=$packetsSent errors=$sendErrors")
    }

    // ── SensorEventListener ────────────────────────────────────────────────────

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_GAME_ROTATION_VECTOR,
            Sensor.TYPE_ROTATION_VECTOR -> {
                SensorManager.getQuaternionFromVector(quaternion, event.values)
                qw = quaternion[0]; qx = quaternion[1]; qy = quaternion[2]; qz = quaternion[3]
            }
            Sensor.TYPE_GYROSCOPE -> {
                gx = event.values[0]; gy = event.values[1]; gz = event.values[2]
            }
            Sensor.TYPE_LINEAR_ACCELERATION -> {
                ax = event.values[0]; ay = event.values[1]; az = event.values[2]
            }
            Sensor.TYPE_ACCELEROMETER -> {
                // Fallback — only use if linear acceleration hasn't provided data
                if (ax == 0f && ay == 0f && az == 0f) {
                    ax = event.values[0]; ay = event.values[1]; az = event.values[2]
                }
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) { /* ignored */ }

    // ── Send loop (runs on senderExecutor) ────────────────────────────────────

    private fun sendPacket() {
        try {
            // Handle calibrate request first
            if (calibrateRequested) {
                calibrateRequested = false
                sendCalibratePacket()
            }

            // Compute delta from quaternion relative to reference
            val delta = computeDelta()
            lastDx = delta[0]; lastDy = delta[1]; lastDz = delta[2]

            // Map UI button bitmask to protocol booleans
            val bits = buttons
            val btnLeft      = (bits and PacketEncoder.BTN_LEFT) != 0
            val btnOrbit     = (bits and PacketEncoder.BTN_ROTATE) != 0
            val btnZoom      = (bits and PacketEncoder.BTN_ZOOM_IN) != 0
                            || (bits and PacketEncoder.BTN_ZOOM_OUT) != 0
            val btnCalibrate = (bits and PacketEncoder.BTN_RECENTER) != 0

            // When zoom is active, encode direction in delta.z
            val dz = if (bits and PacketEncoder.BTN_ZOOM_IN != 0) {
                1.0f
            } else if (bits and PacketEncoder.BTN_ZOOM_OUT != 0) {
                -1.0f
            } else {
                delta[2]
            }

            encoder.encodeInput(
                seq = seq.getAndIncrement(),
                deltaX = delta[0], deltaY = delta[1], deltaZ = dz,
                btnLeft = btnLeft, btnOrbit = btnOrbit,
                btnZoom = btnZoom, btnCalibrate = btnCalibrate,
            )

            if (transport.send(encoder)) {
                packetsSent++
            } else {
                sendErrors++
            }

            // QA-2: limit logging to ~1/s
            if (packetsSent % rateHz == 0) {
                Log.v(TAG, "sent=$packetsSent errors=${transport.errorCount} " +
                        "dx=${delta[0]} dy=${delta[1]} dz=$dz")
            }
        } catch (e: Exception) {
            sendErrors++
            Log.w(TAG, "sendPacket error: ${e.message}")
        }
    }

    private fun sendCalibratePacket() {
        try {
            // Compute forward/up/right from the reference quaternion
            val w = refQw.toDouble(); val x = refQx.toDouble()
            val y = refQy.toDouble(); val z = refQz.toDouble()

            // Rotate unit vectors by the reference quaternion
            // Forward (looking direction) = rotate [0, 0, 1]
            val forward = floatArrayOf(
                (2.0 * (x * z + w * y)).toFloat(),
                (2.0 * (y * z - w * x)).toFloat(),
                (1.0 - 2.0 * (x * x + y * y)).toFloat(),
            )
            // Up = rotate [0, 1, 0]
            val up = floatArrayOf(
                (2.0 * (x * y - w * z)).toFloat(),
                (1.0 - 2.0 * (x * x + z * z)).toFloat(),
                (2.0 * (y * z + w * x)).toFloat(),
            )
            // Right = rotate [1, 0, 0]
            val right = floatArrayOf(
                (1.0 - 2.0 * (y * y + z * z)).toFloat(),
                (2.0 * (x * y + w * z)).toFloat(),
                (2.0 * (x * z - w * y)).toFloat(),
            )

            encoder.encodeCalibrate(
                seq = seq.getAndIncrement(),
                forward = forward, up = up, right = right,
            )

            if (transport.send(encoder)) {
                packetsSent++
                Log.i(TAG, "Calibrate packet sent. forward=${ forward.contentToString()}")
            } else {
                sendErrors++
            }
        } catch (e: Exception) {
            sendErrors++
            Log.w(TAG, "sendCalibratePacket error: ${e.message}")
        }
    }

    // ── Delta computation ────────────────────────────────────────────────────

    /**
     * Compute relative movement delta since the last frame.
     *
     * 1. Compute the relative quaternion: q_rel = conjugate(q_ref) * q_current
     * 2. Extract yaw (horizontal) and pitch (vertical) from q_rel
     * 3. delta = current_angles − previous_angles
     *
     * Returns [dx, dy, dz] where dx=yaw_change, dy=pitch_change, dz=0.
     */
    private fun computeDelta(): FloatArray {
        // Current sensor quaternion
        val cw = qw.toDouble(); val cx = qx.toDouble()
        val cy = qy.toDouble(); val cz = qz.toDouble()

        // Conjugate of reference quaternion
        val rw = refQw.toDouble(); val rx = -refQx.toDouble()
        val ry = -refQy.toDouble(); val rz = -refQz.toDouble()

        // q_rel = conj(ref) * current
        val relW = rw * cw - rx * cx - ry * cy - rz * cz
        val relX = rw * cx + rx * cw + ry * cz - rz * cy
        val relY = rw * cy - rx * cz + ry * cw + rz * cx
        val relZ = rw * cz + rx * cy - ry * cx + rz * cw

        // Normalise (safety)
        val n = sqrt(relW * relW + relX * relX + relY * relY + relZ * relZ)
        val nw = relW / n; val nx = relX / n; val ny = relY / n; val nz = relZ / n

        // Extract yaw and pitch from relative quaternion
        val yaw = Math.toDegrees(
            atan2(2.0 * (nw * nz + nx * ny), 1.0 - 2.0 * (ny * ny + nz * nz))
        ).toFloat()

        val sinp = (2.0 * (nw * ny - nz * nx)).coerceIn(-1.0, 1.0)
        val pitch = Math.toDegrees(asin(sinp)).toFloat()

        if (firstFrame) {
            prevYaw   = yaw
            prevPitch = pitch
            firstFrame = false
            return floatArrayOf(0f, 0f, 0f)
        }

        // Compute delta with wraparound handling for yaw
        var dx = yaw - prevYaw
        if (dx > 180f)  dx -= 360f
        if (dx < -180f) dx += 360f
        val dy = pitch - prevPitch

        prevYaw   = yaw
        prevPitch = pitch

        return floatArrayOf(dx, dy, 0f)
    }
}
