"""Unit tests for the protocol encode / decode layer."""

from __future__ import annotations

import struct

import pytest

from fnirsi_ps_control.exceptions import ChecksumError, ProtocolError
from fnirsi_ps_control import protocol
from fnirsi_ps_control.protocol import Frame, _checksum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_raw_frame(cmd: int, data: bytes) -> bytes:
    """Build a well-formed raw frame byte string."""
    length = len(data)
    chk = _checksum(bytes([cmd, length]) + data)
    return struct.pack(
        f"BBB{length}sBB",
        protocol.FRAME_START,
        cmd,
        length,
        data,
        chk,
        protocol.FRAME_STOP,
    )


# ---------------------------------------------------------------------------
# Frame.encode / Frame.decode round-trip
# ---------------------------------------------------------------------------

class TestFrameRoundTrip:
    def test_empty_payload(self) -> None:
        frame = Frame(cmd=0x01)
        decoded = Frame.decode(frame.encode())
        assert decoded.cmd == frame.cmd
        assert decoded.data == b""

    def test_with_payload(self) -> None:
        frame = Frame(cmd=0x02, data=b"\x00\x03\xE8")
        decoded = Frame.decode(frame.encode())
        assert decoded.cmd == 0x02
        assert decoded.data == b"\x00\x03\xE8"


# ---------------------------------------------------------------------------
# Frame.decode – error conditions
# ---------------------------------------------------------------------------

class TestFrameDecodeErrors:
    def test_too_short_raises(self) -> None:
        with pytest.raises(ProtocolError, match="too short"):
            Frame.decode(b"\xAA")

    def test_bad_start_byte_raises(self) -> None:
        raw = make_raw_frame(0x01, b"")
        raw = b"\xFF" + raw[1:]
        with pytest.raises(ProtocolError, match="start byte"):
            Frame.decode(raw)

    def test_bad_stop_byte_raises(self) -> None:
        raw = make_raw_frame(0x01, b"")
        raw = raw[:-1] + b"\xFF"
        with pytest.raises(ProtocolError, match="stop byte"):
            Frame.decode(raw)

    def test_bad_checksum_raises(self) -> None:
        raw = bytearray(make_raw_frame(0x01, b"\x00"))
        raw[-2] ^= 0xFF  # corrupt checksum
        with pytest.raises(ChecksumError):
            Frame.decode(bytes(raw))

    def test_length_mismatch_raises(self) -> None:
        raw = bytearray(make_raw_frame(0x01, b"\xAB\xCD"))
        raw[2] = 99  # lie about length
        with pytest.raises(ProtocolError, match="Length field"):
            Frame.decode(bytes(raw))


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

class TestPayloadHelpers:
    def test_encode_set_voltage(self) -> None:
        frame = protocol.encode_set_voltage(12_000)
        assert frame.cmd == protocol.Cmd.SET_VOLTAGE
        assert struct.unpack(">I", frame.data)[0] == 12_000

    def test_encode_set_current(self) -> None:
        frame = protocol.encode_set_current(1_500)
        assert frame.cmd == protocol.Cmd.SET_CURRENT
        assert struct.unpack(">I", frame.data)[0] == 1_500

    def test_encode_set_output_on(self) -> None:
        frame = protocol.encode_set_output(True)
        assert frame.data == b"\x01"

    def test_encode_set_output_off(self) -> None:
        frame = protocol.encode_set_output(False)
        assert frame.data == b"\x00"

    def test_encode_get_status(self) -> None:
        frame = protocol.encode_get_status()
        assert frame.cmd == protocol.Cmd.GET_STATUS
        assert frame.data == b""
