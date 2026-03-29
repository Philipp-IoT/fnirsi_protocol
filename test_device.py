#!/usr/bin/env python3
"""Manual integration test against a live DPS-150 on /dev/ttyACM1.

Run: python test_device.py

Sequence
--------
1. Connect
2. Query device name, HW version, FW version
3. Get full status (Vin, Vset, Iset, output state)
4. Set voltage to 5.0 V, current limit to 0.5 A
5. Enable output
6. Read three periodic measurement pushes (CMD 0xc3)
7. Disable output
8. Disconnect
"""

from __future__ import annotations

import sys
import time

import serial

from fnirsi_ps_control import protocol
from fnirsi_ps_control.protocol import (
    Cmd,
    Frame,
    START_QUERY,
    START_WRITE,
    encode_connect,
    encode_disconnect,
    encode_output_disable,
    encode_output_enable,
    encode_query,
    encode_set_current,
    encode_set_voltage,
    decode_f32,
    decode_string,
)

PORT = "/dev/ttyACM1"
BAUD = 9600
TIMEOUT = 5.0

# Raw start-session magic (sent by manufacturer tool after READY handshake)
_START_SESSION_MAGIC = b"\xb0\x00\x01\x01\x01"


# ---------------------------------------------------------------------------
# Serial helpers
# ---------------------------------------------------------------------------

def read_frame(ser: serial.Serial) -> Frame | None:
    """Read one frame, consuming the 0xf0 RX direction prefix."""
    header = ser.read(4)          # DIR(0xf0) + START + CMD + LEN
    if len(header) < 4:
        return None
    # header[0] is the direction prefix 0xf0 – strip it
    length = header[3]
    rest = ser.read(length + 1)   # DATA bytes + CHKSUM
    if len(rest) < length + 1:
        return None
    return Frame.decode(header[1:] + rest)


def send(ser: serial.Serial, frame: Frame) -> None:
    raw = b"\xf1" + frame.encode()   # prepend 0xf1 TX direction prefix
    ser.write(raw)
    ser.flush()
    print(f"  TX: {raw.hex(' ')}")


def send_raw(ser: serial.Serial, raw: bytes, label: str = "") -> None:
    wire = b"\xf1" + raw             # prepend 0xf1 TX direction prefix
    ser.write(wire)
    ser.flush()
    print(f"  TX raw{' (' + label + ')' if label else ''}: {wire.hex(' ')}")


def recv(ser: serial.Serial, expect_cmd: int | None = None) -> Frame | None:
    frame = read_frame(ser)
    if frame is None:
        print("  RX: <timeout>")
        return None
    print(f"  RX: {frame.start:02x} {frame.cmd:02x} {len(frame.data):02x}"
          f" {frame.data.hex(' ')} | cmd=0x{frame.cmd:02x}")
    if expect_cmd is not None and frame.cmd != expect_cmd:
        print(f"  WARNING: expected cmd=0x{expect_cmd:02x}, got 0x{frame.cmd:02x}")
    return frame


# ---------------------------------------------------------------------------
# Main test sequence
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Opening {PORT} @ {BAUD} baud (DTR=off, RTS=on) \u2026")
    ser = serial.Serial()
    ser.port = PORT
    ser.baudrate = BAUD
    ser.timeout = TIMEOUT
    ser.dtr = False
    ser.rts = True
    ser.open()
    ser.reset_input_buffer()
    time.sleep(0.5)

    # ── Sniff: see if device is already pushing anything ─────────────────
    print("\n[0] SNIFF 2 s (raw bytes from device before any TX) …")
    raw_sniff = ser.read(512)
    if raw_sniff:
        print(f"     got {len(raw_sniff)} bytes: {raw_sniff.hex(' ')}")
    else:
        print("     (nothing received)")

    try:
        # ── 1. Connect ────────────────────────────────────────────────────
        print("\n[1] CONNECT")
        send(ser, encode_connect())
        time.sleep(0.1)

        print("\n[1b] GET_READY")
        send(ser, encode_query(Cmd.GET_READY))
        time.sleep(0.05)
        f = recv(ser, Cmd.GET_READY)
        if f:
            print(f"     ready = {f.data[0]:#04x}  ({'ready' if f.data[0] == 0x01 else 'NOT ready'})")

        print("\n[1c] START_SESSION magic (b0 00 01 01 01)")
        send_raw(ser, _START_SESSION_MAGIC, "start-session")
        time.sleep(0.05)

        # ── 2. Device info ────────────────────────────────────────────────
        print("\n[2a] GET_DEVICE_NAME")
        send(ser, encode_query(Cmd.GET_DEVICE_NAME))
        f = recv(ser, Cmd.GET_DEVICE_NAME)
        if f:
            print(f"     name = {decode_string(f.data)!r}")

        print("\n[2b] GET_HW_VERSION")
        send(ser, encode_query(Cmd.GET_HW_VERSION))
        f = recv(ser, Cmd.GET_HW_VERSION)
        if f:
            print(f"     hw   = {decode_string(f.data)!r}")

        print("\n[2c] GET_FW_VERSION")
        send(ser, encode_query(Cmd.GET_FW_VERSION))
        f = recv(ser, Cmd.GET_FW_VERSION)
        if f:
            print(f"     fw   = {decode_string(f.data)!r}")

        # ── 3. Full status ────────────────────────────────────────────────
        print("\n[3] GET_FULL_STATUS")
        send(ser, encode_query(Cmd.GET_FULL_STATUS))
        f = recv(ser, Cmd.GET_FULL_STATUS)
        if f and len(f.data) >= 24:
            import struct
            vin, vset, iset, vout, iout, pout = struct.unpack_from("<ffffff", f.data)
            print(f"     Vin={vin:.3f}V  Vset={vset:.3f}V  Iset={iset:.3f}A")
            print(f"     Vout={vout:.3f}V  Iout={iout:.3f}A  Pout={pout:.3f}W")
            if len(f.data) >= 112:
                out_state = f.data[109]
                print(f"     output_state byte[109] = {out_state:#04x}")

        # ── 4. Set voltage and current ────────────────────────────────────
        print("\n[4a] SET_VOLTAGE 5.0 V")
        send(ser, encode_set_voltage(5.0))
        time.sleep(0.05)

        print("\n[4b] SET_CURRENT 0.5 A")
        send(ser, encode_set_current(0.5))
        time.sleep(0.05)

        # ── 5. Enable output ──────────────────────────────────────────────
        print("\n[5] ENABLE OUTPUT")
        send(ser, encode_output_enable())
        f = recv(ser, Cmd.SET_OUTPUT)   # device echoes back
        if f:
            print(f"     echo data = {f.data.hex()}  ({'enabled' if f.data[0] == 0x01 else '???'})")

        # ── 6. Read 3 periodic measurement pushes ─────────────────────────
        print("\n[6] Reading 3 × PUSH_OUTPUT (CMD 0xc3)  [~600 ms each] …")
        pushes_seen = 0
        deadline = time.monotonic() + 5.0
        while pushes_seen < 3 and time.monotonic() < deadline:
            frame = read_frame(ser)
            if frame is None:
                continue
            if frame.cmd == Cmd.PUSH_OUTPUT and len(frame.data) >= 12:
                import struct
                vout, iout, pout = struct.unpack_from("<fff", frame.data)
                pushes_seen += 1
                print(f"     push #{pushes_seen}: Vout={vout:.3f}V  Iout={iout:.4f}A  Pout={pout:.4f}W")
            else:
                print(f"     (skip cmd=0x{frame.cmd:02x} len={len(frame.data)})")

        if pushes_seen < 3:
            print(f"     WARNING: only saw {pushes_seen}/3 pushes within timeout")

        # ── 7. Disable output ─────────────────────────────────────────────
        print("\n[7] DISABLE OUTPUT")
        send(ser, encode_output_disable())
        f = recv(ser, Cmd.SET_OUTPUT)
        if f:
            print(f"     echo data = {f.data.hex()}  ({'disabled' if f.data[0] == 0x00 else '???'})")

        # ── 8. Disconnect ─────────────────────────────────────────────────
        print("\n[8] DISCONNECT")
        send(ser, encode_disconnect())
        time.sleep(0.1)

        print("\n✓ Test complete.")

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise
    finally:
        ser.close()
        print(f"Closed {PORT}")


if __name__ == "__main__":
    main()
