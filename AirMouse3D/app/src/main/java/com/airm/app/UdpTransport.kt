package com.airm.app

import android.util.Log
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

/**
 * UdpTransport — wraps DatagramSocket for the sensor stream.
 *
 * Updated for variable-length JSON packets (was fixed 52-byte binary).
 *
 * Rules implemented:
 *   COM-1:  UDP, one datagram per packet, never fragmented
 *   COM-7:  socket errors caught, logged, counted — app never crashes
 *   COM-14: sets SO_TRAFFIC_CLASS to DSCP CS6 (low-delay) — best effort
 */
class UdpTransport(private val host: String, private val port: Int) {

    companion object {
        private const val TAG = "UdpTransport"
        // JSON packets are larger than old 52-byte binary; 1500 stays under MTU
        const val MAX_PACKET_SIZE = 1024
    }

    private val socket  = DatagramSocket()
    private val address = InetAddress.getByName(host)
    // Pre-allocate with max size; actual length set per-send
    private val datagram = DatagramPacket(ByteArray(MAX_PACKET_SIZE),
                                          MAX_PACKET_SIZE, address, port)

    var errorCount: Int = 0
        private set

    init {
        // COM-14: request low-delay DSCP (ignored by many networks — not relied upon)
        try { socket.trafficClass = 0x10 } catch (_: Exception) {}
        socket.soTimeout = 0
    }

    /**
     * Send the bytes already encoded in [encoder].
     * Must be called from a background thread (COM-2).
     */
    fun send(encoder: PacketEncoder): Boolean {
        return send(encoder.bytes, encoder.packetSize)
    }

    /**
     * Send arbitrary bytes.
     * Must be called from a background thread (COM-2).
     */
    fun send(data: ByteArray, length: Int): Boolean {
        try {
            datagram.data    = data
            datagram.length  = length
            datagram.address = address
            datagram.port    = port
            socket.send(datagram)
            return true
        } catch (e: Exception) {
            errorCount++
            Log.w(TAG, "UDP send error #$errorCount: ${e.message}")
            return false
        }
    }

    fun close() {
        try { socket.close() } catch (_: Exception) {}
    }
}
