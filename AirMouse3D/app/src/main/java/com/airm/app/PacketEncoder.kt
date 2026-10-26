package com.airm.app

import org.json.JSONArray
import org.json.JSONObject

/**
 * PacketEncoder — builds JSON UDP packets per the new protocol spec.
 *
 * Two packet types:
 *
 * 1. INPUT — sent every tick (~60 Hz):
 *    { "version":1, "device_id":"mobile-01", "seq":N, "type":"input",
 *      "delta":{"x":0.12,"y":-0.04,"z":0.00},
 *      "buttons":{"left":false,"orbit":true,"zoom":false,"calibrate":false} }
 *
 * 2. CALIBRATE — sent on demand when user taps Calibrate:
 *    { "version":1, "device_id":"mobile-01", "seq":N, "type":"calibrate",
 *      "reference":{"forward":[...],"up":[...],"right":[...]} }
 *
 * Note: JSON inherently allocates strings; we minimise overhead by
 * reusing the JSONObject where possible but cannot achieve zero-GC
 * like the old binary encoder.
 */
class PacketEncoder {

    companion object {
        const val PROTOCOL_VERSION = 1
        const val TYPE_INPUT     = "input"
        const val TYPE_CALIBRATE = "calibrate"

        // UI-side button bitmask constants (used by ControllerActivity)
        const val BTN_LEFT      = 0x0001
        const val BTN_RIGHT     = 0x0002   // kept for UI; not in protocol
        const val BTN_ZOOM_IN   = 0x0004
        const val BTN_ZOOM_OUT  = 0x0008
        const val BTN_ROTATE    = 0x0010   // maps to "orbit"
        const val BTN_RECENTER  = 0x0020   // maps to "calibrate"
    }

    private var deviceId = "mobile-01"

    /** Last-encoded packet bytes, ready for UDP send. */
    var bytes: ByteArray = ByteArray(0)
        private set
    var packetSize: Int = 0
        private set

    fun setDeviceId(id: String) { deviceId = id }

    /**
     * Encode an INPUT packet.
     *
     * @param seq        monotonically increasing sequence number
     * @param deltaX     relative horizontal movement (yaw delta, degrees)
     * @param deltaY     relative vertical movement (pitch delta, degrees)
     * @param deltaZ     relative depth movement (zoom delta or 0)
     * @param btnLeft    left-click held
     * @param btnOrbit   orbit (rotate scene) held
     * @param btnZoom    zoom mode active
     * @param btnCalibrate calibrate button active this tick
     */
    fun encodeInput(
        seq: Int,
        deltaX: Float, deltaY: Float, deltaZ: Float,
        btnLeft: Boolean, btnOrbit: Boolean,
        btnZoom: Boolean, btnCalibrate: Boolean,
    ) {
        val json = JSONObject()
        json.put("version", PROTOCOL_VERSION)
        json.put("device_id", deviceId)
        json.put("seq", seq)
        json.put("type", TYPE_INPUT)

        val delta = JSONObject()
        delta.put("x", roundTo4(deltaX))
        delta.put("y", roundTo4(deltaY))
        delta.put("z", roundTo4(deltaZ))
        json.put("delta", delta)

        val buttons = JSONObject()
        buttons.put("left", btnLeft)
        buttons.put("orbit", btnOrbit)
        buttons.put("zoom", btnZoom)
        buttons.put("calibrate", btnCalibrate)
        json.put("buttons", buttons)

        bytes = json.toString().toByteArray(Charsets.UTF_8)
        packetSize = bytes.size
    }

    /**
     * Encode a CALIBRATE packet with the current reference frame vectors.
     *
     * @param seq      sequence number (shares counter with input packets)
     * @param forward  forward direction vector [x, y, z]
     * @param up       up direction vector [x, y, z]
     * @param right    right direction vector [x, y, z]
     */
    fun encodeCalibrate(
        seq: Int,
        forward: FloatArray,
        up: FloatArray,
        right: FloatArray,
    ) {
        val json = JSONObject()
        json.put("version", PROTOCOL_VERSION)
        json.put("device_id", deviceId)
        json.put("seq", seq)
        json.put("type", TYPE_CALIBRATE)

        val reference = JSONObject()
        reference.put("forward", floatArrayToJson(forward))
        reference.put("up", floatArrayToJson(up))
        reference.put("right", floatArrayToJson(right))
        json.put("reference", reference)

        bytes = json.toString().toByteArray(Charsets.UTF_8)
        packetSize = bytes.size
    }

    // ── Helpers ─────────────────────────────────────────────────────────────
    private fun floatArrayToJson(arr: FloatArray): JSONArray {
        val ja = JSONArray()
        for (v in arr) ja.put(roundTo4(v))
        return ja
    }

    private fun roundTo4(v: Float): Double =
        Math.round(v * 10000.0).toDouble() / 10000.0
}
