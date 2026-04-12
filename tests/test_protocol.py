"""Protocol tests — TX encoding (byte-exact) and Kaitai RX parsing.

TX expected values are derived from confirmed captures 2026-03-29.
"""

from __future__ import annotations

import struct

# Import the Kaitai-generated parser directly for type-level checks
import sys
from io import BytesIO
from pathlib import Path

import pytest
from kaitaistruct import KaitaiStream

from fnirsi_ps_control.exceptions import ChecksumError, ProtocolError
from fnirsi_ps_control.protocol import (
    Cmd,
    _checksum,
    encode_connect,
    encode_disconnect,
    encode_output_disable,
    encode_output_enable,
    encode_query,
    encode_set_current,
    encode_set_voltage,
    parse_frame,
)

sys.path.insert(0, str(Path(__file__).parent.parent / "protocol" / "generated"))
from fnirsi_dps150 import FnirsiDps150  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------


class TestChecksum:
    def test_connect(self) -> None:
        # c1 00 01 01 → CHKSUM = (0x00+0x01+0x01) mod 256 = 0x02
        assert _checksum(0x00, 1, b"\x01") == 0x02

    def test_set_voltage_10v(self) -> None:
        data = bytes([0x00, 0x00, 0x20, 0x41])
        assert _checksum(0xC1, 4, data) == 0x26

    def test_set_current_1a(self) -> None:
        data = bytes([0x00, 0x00, 0x80, 0x3F])
        assert _checksum(0xC2, 4, data) == 0x85

    def test_enable_output(self) -> None:
        assert _checksum(0xDB, 1, b"\x01") == 0xDD

    def test_disable_output(self) -> None:
        assert _checksum(0xDB, 1, b"\x00") == 0xDC

    def test_wrap_around(self) -> None:
        assert _checksum(0xFF, 0xFF, b"\xff") == (0xFF + 0xFF + 0xFF) % 256


# ---------------------------------------------------------------------------
# TX frame encoding
# ---------------------------------------------------------------------------


class TestFrameEncode:
    def test_connect(self) -> None:
        assert encode_connect().encode() == bytes([0xF1, 0xC1, 0x00, 0x01, 0x01, 0x02])

    def test_disconnect(self) -> None:
        assert encode_disconnect().encode() == bytes([0xF1, 0xC1, 0x00, 0x01, 0x00, 0x01])

    def test_set_voltage_10v(self) -> None:
        raw = encode_set_voltage(10.0).encode()
        assert raw[0] == 0xF1  # DIR_TX
        assert raw[1] == 0xB1  # START_WRITE
        assert raw[2] == Cmd.SET_VOLTAGE
        assert raw[3] == 4
        assert struct.unpack_from("<f", raw, 4)[0] == pytest.approx(10.0, rel=1e-5)
        assert raw[-1] == 0x26  # confirmed checksum

    def test_set_current_1a(self) -> None:
        raw = encode_set_current(1.0).encode()
        assert raw[2] == Cmd.SET_CURRENT
        assert struct.unpack_from("<f", raw, 4)[0] == pytest.approx(1.0, rel=1e-5)
        assert raw[-1] == 0x85

    def test_enable_output(self) -> None:
        # Row 12795 from dps150_connect_enable_out_set_v_set_i_disable_disconnect.txt
        assert encode_output_enable().encode() == bytes([0xF1, 0xB1, 0xDB, 0x01, 0x01, 0xDD])

    def test_disable_output(self) -> None:
        # Row 16335
        assert encode_output_disable().encode() == bytes([0xF1, 0xB1, 0xDB, 0x01, 0x00, 0xDC])

    def test_get_full_status_query(self) -> None:
        raw = encode_query(Cmd.GET_FULL_STATUS).encode()
        assert raw[2] == Cmd.GET_FULL_STATUS
        assert raw[3] == 1  # LEN = 1 (data = 0x00)

    def test_frame_encode_has_dir_prefix(self) -> None:
        """Frame.encode() must include the 0xf1 DIR byte as first byte."""
        raw = encode_connect().encode()
        assert raw[0] == 0xF1  # DIR_TX
        assert raw[1] == 0xC1  # START_CTRL


# ---------------------------------------------------------------------------
# Kaitai RX parsing
# ---------------------------------------------------------------------------


class TestKaitaiParse:
    def test_device_name(self) -> None:
        # f0 a1 de 07 44 50 53 2d 31 35 30 8f  → "DPS-150"
        raw = bytes([0xF0, 0xA1, 0xDE, 0x07, 0x44, 0x50, 0x53, 0x2D, 0x31, 0x35, 0x30, 0x8F])
        p = FnirsiDps150(KaitaiStream(BytesIO(raw)))
        assert p.frame.body.payload.value == "DPS-150"

    def test_output_enable_echo(self) -> None:
        # f0 a1 db 01 01 dd — device echoes back after enable
        raw = bytes([0xF0, 0xA1, 0xDB, 0x01, 0x01, 0xDD])
        p = FnirsiDps150(KaitaiStream(BytesIO(raw)))
        assert p.frame.body.payload.state == 1

    def test_output_disable_echo(self) -> None:
        # f0 a1 db 01 00 dc
        raw = bytes([0xF0, 0xA1, 0xDB, 0x01, 0x00, 0xDC])
        p = FnirsiDps150(KaitaiStream(BytesIO(raw)))
        assert p.frame.body.payload.state == 0

    def test_push_output_values(self) -> None:
        # Capture row 12827: Vout≈8.45V Iout≈0.0077A Pout≈0.065W
        raw = bytes(
            [
                0xF0,
                0xA1,
                0xC3,
                0x0C,
                0xB8,
                0x43,
                0x07,
                0x41,  # vout float32 LE
                0x40,
                0xC7,
                0xFD,
                0x3B,  # iout float32 LE
                0x34,
                0x17,
                0x86,
                0x3D,  # pout float32 LE
                0x5F,
            ]
        )
        p = FnirsiDps150(KaitaiStream(BytesIO(raw)))
        assert p.frame.body.payload.vout == pytest.approx(8.45, abs=0.01)
        assert p.frame.body.payload.iout == pytest.approx(0.0077, abs=0.001)
        assert p.frame.body.payload.pout == pytest.approx(
            p.frame.body.payload.vout * p.frame.body.payload.iout, rel=0.02
        )

    def test_parse_frame_helper(self) -> None:
        raw = bytes([0xF0, 0xA1, 0xDE, 0x07, 0x44, 0x50, 0x53, 0x2D, 0x31, 0x35, 0x30, 0x8F])
        p = parse_frame(raw)
        assert p.frame.body.payload.value == "DPS-150"


# ---------------------------------------------------------------------------
# parse_frame error handling
# ---------------------------------------------------------------------------


class TestParseFrameErrors:
    def test_too_short(self) -> None:
        with pytest.raises(ProtocolError, match="too short"):
            parse_frame(b"\xf0\xa1\xde")

    def test_truncated(self) -> None:
        with pytest.raises(ProtocolError, match="truncated"):
            parse_frame(bytes([0xF1, 0xB1, 0xC1, 0x04, 0x00, 0x00]))

    def test_bad_checksum(self) -> None:
        raw = bytearray(encode_connect().encode())
        raw[-1] ^= 0xFF
        with pytest.raises(ChecksumError):
            parse_frame(bytes(raw))

    def test_correct_frame_round_trips(self) -> None:
        tx = encode_connect()
        p = parse_frame(tx.encode())
        assert p.frame.body.cmd == Cmd.CONNECT_CTRL

    def test_set_voltage_round_trip(self) -> None:
        tx = encode_set_voltage(12.5)
        p = parse_frame(tx.encode())
        assert struct.unpack("<f", tx.data)[0] == pytest.approx(12.5, rel=1e-5)
        _ = p  # parsed without error is enough; payload type is float32_payload
