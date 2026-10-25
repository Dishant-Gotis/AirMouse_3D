package com.airm.app

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.airm.app.databinding.ActivityConnectionBinding

/**
 * ConnectionActivity — Screen 1 (Section 9.2)
 *
 * Fields: Simulator IP, Port
 * Buttons: Connect
 * Persists last-used IP/port (COM-13: no hardcoded address).
 */
class ConnectionActivity : AppCompatActivity() {

    private lateinit var binding: ActivityConnectionBinding
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityConnectionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = getSharedPreferences("airm_prefs", Context.MODE_PRIVATE)

        // Restore last values (COM-13)
        binding.etIp.setText(prefs.getString("host", "192.168.1.100"))
        binding.etPort.setText(prefs.getString("port", "9000"))
        binding.etRate.setText(prefs.getString("rate", "60"))

        binding.btnConnect.setOnClickListener {
            val host = binding.etIp.text.toString().trim()
            val port = binding.etPort.text.toString().toIntOrNull()
            val rate = binding.etRate.text.toString().toIntOrNull()

            when {
                host.isEmpty()       -> toast("Enter simulator IP address")
                port == null || port !in 1..65535 -> toast("Enter a valid port (1–65535)")
                rate == null || rate !in 10..100  -> toast("Rate must be 10–100 Hz")
                else -> {
                    // Save for next time
                    prefs.edit()
                        .putString("host", host)
                        .putString("port", port.toString())
                        .putString("rate", rate.toString())
                        .apply()

                    val intent = Intent(this, ControllerActivity::class.java).apply {
                        putExtra(ControllerActivity.EXTRA_HOST, host)
                        putExtra(ControllerActivity.EXTRA_PORT, port)
                        putExtra(ControllerActivity.EXTRA_RATE, rate)
                    }
                    startActivity(intent)
                }
            }
        }
    }

    private fun toast(msg: String) = Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
}
