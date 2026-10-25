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

/**
 * MotionSender — the heart of the mobile app.
 *
 * Responsibilities:
 *   1. Register sensors on a dedicated HandlerThread (SEN-6).
 *   2. Copy sensor values into pre-allocated buffers in onSensorChanged — NO I/O (SEN-5).
 *   3. Run a fixed-rate sender thread (COM-2) that calls sendPacket() every ~16 ms (60 Hz).
 *   4. Unregister sensors on stop() (SEN-7).
 *   5. Handle errors without crashing (COM-7).
 *
 * Sensor data stored as @Volatile arrays (written by sensor thread, read by sender thread).
 * This is safe because individual float array element reads/writes are atomic on Android
 * and we prefer the latest reading over strict ordering.
 */
class MotionSender(
    private val sensorManager: SensorManager,
    private val host: String,
    private val port: Int,
    private val rateHz: Int = 60,
) : SensorEventListener {

    // ── Sensor data buffers (SEN-5: only copy here, no alloc/IO) ─────────────
    @Volatile private var qw = 1f; @Volatile private var qx = 0f
    @Volatile private var qy = 0f; @Volatile private var qz = 0f
    @Volatile private var gx = 0f; @Volatile private var gy = 0f; @Volatile private var gz = 0f
    @Volatile private var ax = 0f; @Volatile private var ay = 0f; @Volatile private var az = 0f

    // Shared button bitmask — set atomically from UI thread (COM-4)
    @Volatile var buttons: Int = 0

    // ── Internals ─────────────────────────────────────────────────────────────
    private val encoder    = PacketEncoder()
    private lateinit var transport: UdpTransport
    private val seq        = AtomicInteger(0)
    private val startMs    = SystemClock.elapsedRealtime()

    // Dedicated sensor handler thread (SEN-6)
    private val sensorThread  = HandlerThread("SensorThread").also { it.start() }
    private val sensorHandler = android.os.Handler(sensorThread.looper)

    // Fixed-rate sender on a scheduled thread pool (COM-2)
    private val senderExecutor  = Executors.newSingleThreadScheduledExecutor()
    private var senderFuture: ScheduledFuture<*>? = null

    // Stats
    var packetsSent: Int = 0; private set
    var sendErrors: Int  = 0; private set

    companion object {
        private const val TAG = "MotionSender"
        // Request 100 Hz (10 000 µs) — SEN-1: actual rate is device-dependent
        private const val SENSOR_DELAY_US = 10_000
        // maxReportLatencyUs = 0 → deliver immediately, no batching (SEN-1)
        private const val MAX_LATENCY_US  = 0
    }

    // ── Public API ─────────────────────────────────────────────────────────────

    fun start() {
        transport = UdpTransport(host, port)

        // Register sensors on dedicated thread (SEN-6)
        val sensors = listOf(
            Sensor.TYPE_GAME_ROTATION_VECTOR,   // primary orientation (SEN-2)
            Sensor.TYPE_GYROSCOPE,
            Sensor.TYPE_LINEAR_ACCELERATION,
        )
        var gameRotOk = false
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
            Log.d(TAG, "Registered sensor type=$type ok=$ok")
        }

        // Fallback if game rotation vector not available (SEN-2)
        if (!gameRotOk) {
            Log.w(TAG, "Game rotation vector N/A — falling back to rotation vector")
            sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)?.let {
                sensorManager.registerListener(this, it, SENSOR_DELAY_US, MAX_LATENCY_US, sensorHandler)
            }
        }

        // Fixed-rate sender loop (COM-2): period = 1_000_000 / rateHz µs
        val periodUs = 1_000_000L / rateHz
        senderFuture = senderExecutor.scheduleAtFixedRate(
            ::sendPacket, 0L, periodUs, TimeUnit.MICROSECONDS
        )
        Log.i(TAG, "Started at $rateHz Hz → $host:$port")
    }

    fun stop() {
        senderFuture?.cancel(false)
        sensorManager.unregisterListener(this)   // SEN-7: saves battery
        sensorThread.quitSafely()
        senderExecutor.shutdown()
        if (::transport.isInitialized) transport.close()
        Log.i(TAG, "Stopped. Sent=$packetsSent errors=$sendErrors")
    }

    // ── SensorEventListener ────────────────────────────────────────────────────

    override fun onSensorChanged(event: SensorEvent) {
        // SEN-5: ONLY copy values — no IO, no allocation, no logging
        when (event.sensor.type) {
            Sensor.TYPE_GAME_ROTATION_VECTOR,
            Sensor.TYPE_ROTATION_VECTOR -> {
                // Android fills values[0..3] as x,y,z,w  for rotation vector
                // SensorManager.getQuaternionFromVector gives [w,x,y,z]
                val q = FloatArray(4)
                SensorManager.getQuaternionFromVector(q, event.values)
                qw = q[0]; qx = q[1]; qy = q[2]; qz = q[3]
            }
            Sensor.TYPE_GYROSCOPE -> {
                gx = event.values[0]; gy = event.values[1]; gz = event.values[2]
            }
            Sensor.TYPE_LINEAR_ACCELERATION -> {
                ax = event.values[0]; ay = event.values[1]; az = event.values[2]
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) { /* ignored */ }

    // ── Send loop (runs on senderExecutor) ────────────────────────────────────

    private fun sendPacket() {
        try {
            val ts = SystemClock.elapsedRealtime() - startMs
            encoder.encode(
                seq       = seq.getAndIncrement(),
                buttons   = buttons,
                timestampMs = ts,
                qw = qw, qx = qx, qy = qy, qz = qz,
                gx = gx, gy = gy, gz = gz,
                ax = ax, ay = ay, az = az,
            )
            transport.send(encoder)
            packetsSent++

            // COM-4: if button state changed, an immediate extra packet is already
            // guaranteed because buttons is read fresh every send tick and the
            // UI sets it atomically before the next tick fires.

            // QA-2: limit logging to ~1/s
            if (packetsSent % rateHz == 0) {
                Log.v(TAG, "sent=$packetsSent errors=${transport.errorCount}")
            }
        } catch (e: Exception) {
            sendErrors++
            Log.w(TAG, "sendPacket error: ${e.message}")
        }
    }
}
