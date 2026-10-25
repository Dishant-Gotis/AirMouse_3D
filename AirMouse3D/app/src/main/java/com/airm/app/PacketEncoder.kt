package com.airm.app

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * PacketEncoder — builds the 52-byte binary SENSOR packet (Section 8.3, QA-1).
 *
 * Layout (little-endian):
 *   0-1   uint16  magic       = 0x3D4D
 *   2     uint8   version     = 1
 *   3     uint8   type        = 1 (SENSOR)
 *   4-5   uint16  seq
 *   6-7   uint16  buttons
 *   8-11  uint32  timestamp_ms
 *   12-27 float32 qw,qx,qy,qz
 *   28-39 float32 gx,gy,gz
 *   40-51 float32 ax,ay,az
 *
 * Rules: COM-1 (52-byte UDP datagram), COM-6 (reuse buffer).
 */
class PacketEncoder {

    companion object {
        const val MAGIC: Short   = 0x3D4D.toShort()
        const val VERSION: Byte  = 1
        const val TYPE_SENSOR: Byte = 1
        const val PACKET_SIZE    = 52

        // Button bitmask constants (Section 8.4)
        const val BTN_LEFT     = 0x0001
        const val BTN_RIGHT    = 0x0002
        const val BTN_ZOOM_IN  = 0x0004
        const val BTN_ZOOM_OUT = 0x0008
        const val BTN_ROTATE   = 0x0010
        const val BTN_RECENTER = 0x0020
    }

    // COM-6: pre-allocated buffer, reused every packet — zero GC pressure
    private val buffer = ByteBuffer.allocate(PACKET_SIZE).order(ByteOrder.LITTLE_ENDIAN)
    val bytes: ByteArray = buffer.array()   // expose backing array for DatagramPacket

    /**
     * Fill the buffer with a new SENSOR packet. Call this before sending.
     *
     * @param seq          packet sequence number (wraps at 65535, COM-5)
     * @param buttons      bitmask of currently pressed buttons (Section 8.4)
     * @param timestampMs  ms since app start (uint32 range, COM-3)
     * @param qw,qx,qy,qz unit quaternion — game rotation vector (SEN-2, SEN-3)
     * @param gx,gy,gz     gyroscope in rad/s                    (SEN-3)
     * @param ax,ay,az     linear acceleration in m/s²           (SEN-3)
     */
    fun encode(
        seq: Int,
        buttons: Int,
        timestampMs: Long,
        qw: Float, qx: Float, qy: Float, qz: Float,
        gx: Float, gy: Float, gz: Float,
        ax: Float, ay: Float, az: Float,
    ) {
        buffer.rewind()
        buffer.putShort(MAGIC)
        buffer.put(VERSION)
        buffer.put(TYPE_SENSOR)
        buffer.putShort((seq and 0xFFFF).toShort())
        buffer.putShort((buttons and 0xFFFF).toShort())
        buffer.putInt((timestampMs and 0xFFFFFFFFL).toInt())
        buffer.putFloat(qw); buffer.putFloat(qx); buffer.putFloat(qy); buffer.putFloat(qz)
        buffer.putFloat(gx); buffer.putFloat(gy); buffer.putFloat(gz)
        buffer.putFloat(ax); buffer.putFloat(ay); buffer.putFloat(az)
    }
}
