"""Unit tests for the protocol encode / decode layer.

All expected byte values are derived from the confirmed capture
``dps150_connect_set_10v_set_1A_disconnect.txt`` (2026-03-29).
"""

from __future__ import annotations

import struct

import pytest

from fnirsi_ps_control.exceptions import ChecksumError, ProtocolError
from fnirsi_ps_control import protocol
from fnirsi_ps_control.protocol import (
    Frame,
    _checksum,
    START_CTRL,
    START_QUERY,
    START_WRITE,
    Cmd,
    decode_f32,
    decode_push_output,
    decode_string,
    encode_connect,
    encode_disconnect,
    encode_query,
    encode_set_current,
    encode_set_voltage,
)


# ---------------------------------------------------------------------------
# Checksum helper
# ---------------------------------------------------------------------------

class TestChecksum:
    def test_connect_frame(self) -> None:
        # c1 00 01 01 → CHKSUM = (0x00+0x01+0x01) mod 256 = 0x02
        assert _checksum(0x00, 1, b"\x01") == 0x02

    def test_set_voltage_10v(self) -> None:
        # b1 c1 04 00 00 20 41 → CHKSUM = (0xc1+0x04+0x00+0x00+0x20+0x41) mod 256
        data = bytes([0x00, 0x00, 0x20, 0x41])
        assert _checksum(0xC1, 4, data) == 0x26

    def test_set_current_1a(self) -> None:
        # b1 c2 04 00 00 80 3f → CHKSUM = (0xc2+0x04+0x00+0x00+0x80+0x3f) mod 256
        data = bytes([0x00, 0x00, 0x80, 0x3F])
        assert _checksum(0xC2, 4, data) == 0x85

    def test_wrap_around(self) -> None:
        # Ensure mod 256 wraps correctly
        result = _checksum(0xFF, 0xFF, b"\xFF")
        assert result == (0xFF + 0xFF + 0xFF) % 256


# ---------------------------------------------------------------------------
# Frame.encode
# ---------------------------------------------------------------------------

class TestFrameEncode:
    def test_connect_frame_bytes(self) -> None:
        frame = encode_connect()
        raw = frame.encode()
        assert raw == bytes([0xC1, 0x00, 0x01, 0x01, 0x02])

    def test_disconnect_frame_bytes(self) -> None:
        frame = encode_disconnect()
        raw = frame.encode()
        assert raw == bytes([0xC1, 0x00, 0x01, 0x00, 0x01])

    def test_set_voltage_10v_bytes(self) -> None:
        frame = encode_set_voltage(10.0)
        raw = frame.encode()
        assert raw[0] == START_WRITE
        assert raw[1] == Cmd.SET_VOLTAGE
        assert raw[2] == 4
        assert struct.unpack_from("<f", raw, 3)[0] == pytest.approx(10.0, rel=1e-5)
        assert raw[-1] == 0x26  # confirmed checksum

    def test_set_current_1a_bytes(self) -> None:
        frame = encode_set_current(1.0)
        raw = frame.encode()
        assert raw[0] == START_WRITE
        assert raw[1] == Cmd.SET_CURRENT
        assert raw[2] == 4
        assert struct.unpack_from("<f", raw, 3)[0] == pytest.approx(1.0, rel=1e-5)
        assert raw[-1] == 0x85  # confirmed checksum

    def test_empty_data_frame_length(self) -> None:
        frame = Frame(start=START_QUERY, cmd=0xE1, data=b"\x00")
        raw = frame.encode()
        assert len(raw) == 5  # start + cmd + len(1) + data(1) + chk
        assert raw[2] == 1

    def test_no_stop_byte(self) -> None:
        """Frame must NOT end with 0x55 (old wrong assumption)."""
        frame = encode_connect()
        raw = frame.encode()
        assert len(raw) == 5
        # no trailing 0x55
        assert raw[-1] == 0x02


# ---------------------------------------------------------------------------
# Frame.decode – round-trip
# ---------------------------------------------------------------------------

class TestFrameDecode:
    def test_round_trip_connect(self) -> None:
        tx = encode_connect()
        rx = Frame.decode(tx.encode())
        assert rx.start == START_CTRL
        assert rx.cmd == Cmd.CONNECT_CTRL
        assert rx.data == b"\x01"

    def test_round_trip_set_voltage(self) -> None:
        tx = encode_set_voltage(12.5)
        rx = Frame.decode(tx.encode())
        assert rx.start == START_WRITE
        assert rx.cmd == Cmd.SET_VOLTAGE
        assert struct.unpack("<f", rx.data)[0] == pytest.approx(12.5, rel=1e-5)

    def test_round_trip_set_current(self) -> None:
        tx = encode_set_current(0.5)
        rx = Frame.decode(tx.encode())
        assert rx.cmd == Cmd.SET_CURRENT
        assert struct.unpack("<f", rx.data)[0] == pytest.approx(0.5, rel=1e-5)

    def test_decode_confirmed_response_frame(self) -> None:
        """Decode a literal frame from the 2026-03-29 capture."""
        # a1 de 07 44 50 53 2d 31 35 30 8f  (device name "DPS-150")
        raw = bytes([0xA1, 0xDE, 0x07, 0x44, 0x50, 0x53, 0x2D, 0x31, 0x35, 0x30, 0x8F])
        frame = Frame.decode(raw)
        assert frame.start == START_QUERY
        assert frame.cmd == Cmd.GET_DEVICE_NAME
        assert frame.data == b"DPS-150"


# ---------------------------------------------------------------------------
# Frame.decode – error conditions
# ---------------------------------------------------------------------------

class TestFrameDecodeErrors:
    def test_too_short_raises(self) -> None:
        with pytest.raises(ProtocolError, match="too short"):
            Frame.decode(b"\xA1\xDE\x07")

    def test_truncated_data_raises(self) -> None:
        # LEN says 4 but only 2 data bytes present
        raw = bytes([0xB1, 0xC1, 0x04, 0x00, 0x00])
        with pytest.raises(ProtocolError, match="truncated"):
            Frame.decode(raw)

    def test_bad_checksum_raises(self) -> None:
        raw = bytearray(encode_connect().encode())
        raw[-1] ^= 0xFF  # flip checksum
        with pytest.raises(ChecksumError):
            Frame.decode(bytes(raw))


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

class TestPayloadHelpers:
    def test_decode_f32_vin(self) -> None:
        # From capture: a1 c0 04 b1 6d a0 41 → 20.0537...V
        data = bytes([0xB1, 0x6D, 0xA0, 0x41])
        v = decode_f32(data)
        assert v == pytest.approx(20.05, abs=0.01)

    def test_decode_f32_too_short(self) -> None:
        with pytest.raises(ProtocolError, match="float32"):
            decode_f32(b"\x00\x00")

    def test_decode_string_device_name(self) -> None:
        assert decode_string(b"DPS-150") == "DPS-150"

    def test_decode_push_output_all_zero(self) -> None:
        data = struct.pack("<fff", 0.0, 0.0, 0.0)
        vout, iout, unk = decode_push_output(data)
        assert vout == pytest.approx(0.0)
        assert iout == pytest.approx(0.0)
        assert unk  == pytest.approx(0.0)

    def test_decode_push_output_too_short(self) -> None:
        with pytest.raises(ProtocolError, match="12 bytes"):
            decode_push_output(b"\x00" * 8)

    def test_encode_query_format(self) -> None:
        frame = encode_query(Cmd.GET_FULL_STATUS)
        assert frame.start == START_QUERY
        assert frame.cmd == Cmd.GET_FULL_STATUS
        assert frame.data == b"\x00"
