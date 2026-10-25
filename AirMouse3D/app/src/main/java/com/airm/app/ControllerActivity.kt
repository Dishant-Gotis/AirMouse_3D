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
 *   LEFT, RIGHT        — COM-4: state sent in every packet; click triggers immediate extra
 *   ZOOM IN, ZOOM OUT  — held
 *   ROTATE             — held; engages rotate mode in simulator
 *   RECENTER           — edge-triggered tap
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
        Thread({ sender.start() }, "SenderStartThread").start()

        binding.tvStatus.text = "Connecting to $host:$port…"
    }

    override fun onDestroy() {
        super.onDestroy()
        uiHandler.removeCallbacksAndMessages(null)
        Thread({ sender.stop() }, "SenderStopThread").start()
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

        // Recenter: edge-triggered tap — set bit briefly then clear (Section 8.4)
        binding.btnRecenter.setOnClickListener {
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
        val runnable = object : Runnable {
            override fun run() {
                val sent   = sender.packetsSent
                val errors = sender.sendErrors
                val bits   = buttonBits.get()
                val btnStr = buildString {
                    if (bits and BTN_LEFT     != 0) append("L ")
                    if (bits and BTN_RIGHT    != 0) append("R ")
                    if (bits and BTN_ZOOM_IN  != 0) append("Z+ ")
                    if (bits and BTN_ZOOM_OUT != 0) append("Z- ")
                    if (bits and BTN_ROTATE   != 0) append("ROT ")
                    if (isEmpty()) append("—")
                }
                binding.tvStatus.text =
                    "Sent: $sent  Errors: $errors  Buttons: $btnStr"

                uiHandler.postDelayed(this, 500L)
            }
        }
        uiHandler.post(runnable)
    }
}
