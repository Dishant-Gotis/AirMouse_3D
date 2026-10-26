package com.airm.app

import android.content.Context
import android.hardware.SensorManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import com.airm.app.PacketEncoder.Companion.BTN_LEFT
import com.airm.app.PacketEncoder.Companion.BTN_RIGHT
import com.airm.app.PacketEncoder.Companion.BTN_ZOOM_IN
import com.airm.app.PacketEncoder.Companion.BTN_ZOOM_OUT
import com.airm.app.PacketEncoder.Companion.BTN_ROTATE
import com.airm.app.PacketEncoder.Companion.BTN_RECENTER
import com.airm.app.databinding.ActivityControllerBinding
import java.util.concurrent.atomic.AtomicInteger

/**
 * ControllerActivity — Screen 2 (Section 9.2, 9.3)
 *
 * Buttons:
 *   LEFT, RIGHT        — click triggers; state sent in every packet
 *   ZOOM IN, ZOOM OUT  — held; maps to protocol "zoom" + delta.z direction
 *   ORBIT (ROTATE)     — held; engages orbit mode in simulator
 *   CALIBRATE          — edge-triggered tap; sends calibrate packet
 *
 * Rules: UI-1 (thin), UI-2 (atomic bitmask, multi-touch), UI-3 (no heavy work),
 *        UI-4 (large buttons), UI-5 (screen locked portrait), UI-6 (status display),
 *        COM-11 (screen stays awake).
 */
class ControllerActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_HOST = "host"
        const val EXTRA_PORT = "port"
        const val EXTRA_RATE = "rate"
    }

    private lateinit var binding: ActivityControllerBinding
    private lateinit var sender: MotionSender
    private val uiHandler = Handler(Looper.getMainLooper())

    // Atomic bitmask — UI thread writes, sender thread reads (UI-2, COM-4)
    private val buttonBits = AtomicInteger(0)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityControllerBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // COM-11: keep screen on while controlling
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val host = intent.getStringExtra(EXTRA_HOST) ?: "127.0.0.1"
        val port = intent.getIntExtra(EXTRA_PORT, 9000)
        val rate = intent.getIntExtra(EXTRA_RATE, 60)

        val sm = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        sender = MotionSender(sm, host, port, rate)

        setupButtons()
        startStatusUpdater()
        
        // Start streaming on a background thread (COM-2 — network off main thread)
        Thread({
            try {
                sender.start()
            } catch (e: Exception) {
                android.util.Log.e("ControllerActivity", "Unable to start sensor sender", e)
                runOnUiThread {
                    binding.tvStatus.text = "Connection failed: ${e.message ?: "unknown error"}"
                }
            }
        }, "SenderStartThread").start()

        binding.tvStatus.text = "Connecting to $host:$port…"
    }

    override fun onDestroy() {
        super.onDestroy()
        uiHandler.removeCallbacksAndMessages(null)
        sender.stop()
    }

    // ── Button wiring (UI-2: multi-touch, atomic bitmask) ──────────────────────

    private fun setupButtons() {
        // Helper: register hold-button touch listener
        fun View.onHold(bit: Int) {
            setOnTouchListener { _, event ->
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN ->
                        buttonBits.updateAndGet { it or bit }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP,
                    MotionEvent.ACTION_CANCEL ->
                        buttonBits.updateAndGet { it and bit.inv() }
                }
                sender.buttons = buttonBits.get()
                performClick()    // accessibility
                true
            }
        }

        binding.btnLeft.onHold(BTN_LEFT)
        binding.btnRight.onHold(BTN_RIGHT)
        binding.btnZoomIn.onHold(BTN_ZOOM_IN)
        binding.btnZoomOut.onHold(BTN_ZOOM_OUT)
        binding.btnRotate.onHold(BTN_ROTATE)

        // Calibrate: edge-triggered tap — calls calibrate() on the sender
        // Also briefly sets BTN_RECENTER so the protocol "calibrate" button
        // is true for one send cycle
        binding.btnCalibrate.setOnClickListener {
            sender.calibrate()
            buttonBits.updateAndGet { it or BTN_RECENTER }
            sender.buttons = buttonBits.get()
            // Clear after one send cycle (~20 ms)
            uiHandler.postDelayed({
                buttonBits.updateAndGet { it and BTN_RECENTER.inv() }
                sender.buttons = buttonBits.get()
            }, 50L)
        }

        // Disconnect button
        binding.btnDisconnect.setOnClickListener { finish() }
    }

    // ── Status HUD (UI-6) ─────────────────────────────────────────────────────

    private fun startStatusUpdater() {
        var tickCount = 0
        val runnable = object : Runnable {
            override fun run() {
                // Real-time sensor snapshot update (~12.5 Hz, every 80 ms)
                val snap = sender.getSnapshot()
                binding.tvSensorRate.text = "${sender.rateHz} Hz"
                binding.tvSensorAngles.text = String.format(
                    java.util.Locale.US,
                    "YAW: %+6.1f°  PITCH: %+6.1f°  ROLL: %+6.1f°",
                    snap.yawDeg, snap.pitchDeg, snap.rollDeg
                )
                binding.tvSensorGyro.text = String.format(
                    java.util.Locale.US,
                    "GYRO (rad/s) : gx:%+5.2f gy:%+5.2f gz:%+5.2f",
                    snap.gx, snap.gy, snap.gz
                )
                binding.tvSensorAccel.text = String.format(
                    java.util.Locale.US,
                    "ACCEL(m/s²)  : ax:%+5.2f ay:%+5.2f az:%+5.2f",
                    snap.ax, snap.ay, snap.az
                )
                binding.tvSensorQuat.text = String.format(
                    java.util.Locale.US,
                    "DELTA  dx:%+.3f  dy:%+.3f  dz:%+.3f",
                    snap.deltaX, snap.deltaY, snap.deltaZ
                )

                // Status text updated every ~480 ms (every 6 ticks)
                if (tickCount++ % 6 == 0) {
                    val sent   = snap.packetsSent
                    val errors = snap.sendErrors
                    val bits   = buttonBits.get()
                    val btnStr = buildString {
                        if (bits and BTN_LEFT     != 0) append("L ")
                        if (bits and BTN_RIGHT    != 0) append("R ")
                        if (bits and BTN_ZOOM_IN  != 0) append("Z+ ")
                        if (bits and BTN_ZOOM_OUT != 0) append("Z- ")
                        if (bits and BTN_ROTATE   != 0) append("ORB ")
                        if (bits and BTN_RECENTER != 0) append("CAL ")
                        if (isEmpty()) append("—")
                    }
                    binding.tvStatus.text =
                        "Sent: $sent  Errors: $errors  Buttons: $btnStr  [${sender.host}:${sender.port}]"
                }

                uiHandler.postDelayed(this, 80L)
            }
        }
        uiHandler.post(runnable)
    }
}
