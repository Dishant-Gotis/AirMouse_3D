package com.airm.app

import android.util.Log
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

/**
 * UdpTransport — wraps DatagramSocket for the sensor stream.
 *
 * Rules implemented:
 *   COM-1:  UDP, one datagram per packet, never fragmented
 *   COM-6:  pre-allocated DatagramPacket, no per-send allocation
 *   COM-7:  socket errors caught, logged, counted — app never crashes
 *   COM-14: sets SO_TRAFFIC_CLASS to DSCP CS6 (low-delay) — best effort
 */
class UdpTransport(private val host: String, private val port: Int) {

    private val socket      = DatagramSocket()
    private val address     = InetAddress.getByName(host)
    // COM-6: reuse DatagramPacket — no allocation in the hot path
    private val datagram    = DatagramPacket(ByteArray(PacketEncoder.PACKET_SIZE),
                                             PacketEncoder.PACKET_SIZE, address, port)

    var errorCount: Int = 0
        private set

    init {
        // COM-14: request low-delay DSCP (ignored by many networks — not relied upon)
        try { socket.trafficClass = 0x10 } catch (_: Exception) {}
        socket.soTimeout = 0   // non-blocking send is fine; receives are not done here
    }

    /**
     * Send the bytes already encoded in [encoder].
     * Must be called from a background thread (COM-2).
     */
    fun send(encoder: PacketEncoder) {
        try {
            datagram.data    = encoder.bytes   // shares backing array — no copy
            datagram.length  = PacketEncoder.PACKET_SIZE
            datagram.address = address
            datagram.port    = port
            socket.send(datagram)
        } catch (e: Exception) {
            errorCount++
            Log.w(TAG, "UDP send error #$errorCount: ${e.message}")
        }
    }

    fun close() {
        try { socket.close() } catch (_: Exception) {}
    }

    companion object { private const val TAG = "UdpTransport" }
}
