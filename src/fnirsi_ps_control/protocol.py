"""TX encode layer and Kaitai RX parser wrapper for the FNIRSI DPS-150.

Wire format (confirmed 2026-03-29):

    [DIR:1] [START:1] [CMD:1] [LEN:1] [DATA×LEN] [CHKSUM:1]

    DIR    : 0xf1 host→device  |  0xf0 device→host
    START  : 0xa1 query/response  |  0xb1 write cmd  |  0xc1 connect/disconnect
    CHKSUM : (CMD + LEN + Σ DATA) mod 256  (DIR and START excluded)
    Values : IEEE 754 32-bit little-endian float for voltage and current

The Kaitai-generated parser (``protocol/generated/fnirsi_dps150.py``) handles
all RX decoding.  This module provides TX encoding only, plus a thin
``parse_frame()`` wrapper that returns a typed ``FnirsiDps150`` object.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from io import BytesIO
from typing import TYPE_CHECKING

from kaitaistruct import KaitaiStream

from fnirsi_ps_control.exceptions import ChecksumError, ProtocolError

if TYPE_CHECKING:
    pass

# Lazy import of the Kaitai-generated parser.
# The generated module lives outside the package (protocol/generated/),
# so we add it to sys.path at runtime.  mypy sees only `Any` here.
import sys as _sys
from pathlib import Path as _Path
from typing import Any as _Any

_gen_path = str(_Path(__file__).parent.parent.parent / "protocol" / "generated")
if _gen_path not in _sys.path:
    _sys.path.insert(0, _gen_path)

try:
    from fnirsi_dps150 import FnirsiDps150 as _FnirsiDps150

    _parser_available: bool = True
except ImportError:  # pragma: no cover
    _FnirsiDps150 = None
    _parser_available = False

# ---------------------------------------------------------------------------
# Direction / start bytes
# ---------------------------------------------------------------------------
DIR_TX: int = 0xF1
DIR_RX: int = 0xF0

START_QUERY: int = 0xA1
START_WRITE: int = 0xB1
START_CTRL: int = 0xC1

# Opaque 5-byte magic sent after the CONNECT/READY handshake.
# The DIR_TX prefix is prepended by SerialConnection.write().
START_SESSION_MAGIC: bytes = b"\xb0\x00\x01\x01\x01"


# ---------------------------------------------------------------------------
# Command IDs (all confirmed from 2026-03-29 capture)
# ---------------------------------------------------------------------------
class Cmd:
    """Known command identifiers."""

    CONNECT_CTRL: int = 0x00
    GET_READY: int = 0xE1
    GET_DEVICE_NAME: int = 0xDE
    GET_HW_VERSION: int = 0xE0
    GET_FW_VERSION: int = 0xDF
    GET_FULL_STATUS: int = 0xFF
    SET_VOLTAGE: int = 0xC1
    SET_CURRENT: int = 0xC2
    SET_OUTPUT: int = 0xDB
    PUSH_OUTPUT: int = 0xC3
    PUSH_VIN_A: int = 0xC0
    PUSH_VIN_B: int = 0xE2
    PUSH_VIN_C: int = 0xC4
    PUSH_MAX_CURRENT: int = 0xE3


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------
def _checksum(cmd: int, length: int, data: bytes) -> int:
    """Compute (CMD + LEN + Σ DATA) mod 256."""
    return (cmd + length + sum(data)) & 0xFF


# ---------------------------------------------------------------------------
# TX frame (encode-only)
# ---------------------------------------------------------------------------
@dataclass
class Frame:
    """One application-layer TX frame."""

    start: int
    cmd: int
    data: bytes = field(default=b"")

    def encode(self) -> bytes:
        """Serialise to bytes ready for transmission (no DIR prefix)."""
        length = len(self.data)
        chk = _checksum(self.cmd, length, self.data)
        return struct.pack(f"BBB{length}sB", self.start, self.cmd, length, self.data, chk)


# ---------------------------------------------------------------------------
# TX frame builders
# ---------------------------------------------------------------------------
def encode_connect() -> Frame:
    return Frame(start=START_CTRL, cmd=Cmd.CONNECT_CTRL, data=b"\x01")


def encode_disconnect() -> Frame:
    return Frame(start=START_CTRL, cmd=Cmd.CONNECT_CTRL, data=b"\x00")


def encode_set_voltage(volts: float) -> Frame:
    return Frame(start=START_WRITE, cmd=Cmd.SET_VOLTAGE, data=struct.pack("<f", volts))


def encode_set_current(amps: float) -> Frame:
    return Frame(start=START_WRITE, cmd=Cmd.SET_CURRENT, data=struct.pack("<f", amps))


def encode_output_enable() -> Frame:
    return Frame(start=START_WRITE, cmd=Cmd.SET_OUTPUT, data=b"\x01")


def encode_output_disable() -> Frame:
    return Frame(start=START_WRITE, cmd=Cmd.SET_OUTPUT, data=b"\x00")


def encode_set_output(enabled: bool) -> Frame:
    return encode_output_enable() if enabled else encode_output_disable()


def encode_query(cmd: int) -> Frame:
    return Frame(start=START_QUERY, cmd=cmd, data=b"\x00")


def encode_get_status() -> Frame:
    return encode_query(Cmd.GET_FULL_STATUS)


# ---------------------------------------------------------------------------
# RX parser (Kaitai)
# ---------------------------------------------------------------------------
def parse_frame(raw: bytes) -> _Any:
    """Parse a raw RX frame (without DIR prefix) into a FnirsiDps150 object.

    Parameters
    ----------
    raw:
        Frame bytes with format ``[START][CMD][LEN][DATA][CHKSUM]``,
        i.e. the DIR byte must already be stripped by the caller.

    Returns
    -------
    FnirsiDps150
        Kaitai-generated parser object with typed field access.

    Raises
    ------
    ImportError
        If the Kaitai-generated parser is not available.
    ProtocolError
        If the frame is too short or structurally invalid.
    ChecksumError
        If the checksum does not match.
    """
    if not _parser_available:
        raise ImportError("Kaitai-generated parser not found. Run: bash scripts/gen_kaitai.sh")

    if len(raw) < 4:
        raise ProtocolError(f"Frame too short: {len(raw)} bytes (minimum 4)")

    cmd = raw[1]
    length = raw[2]
    expected_total = 4 + length
    if len(raw) < expected_total:
        raise ProtocolError(f"Frame truncated: have {len(raw)} bytes, need {expected_total}")

    data = raw[3 : 3 + length]
    got_chk = raw[3 + length]
    exp_chk = _checksum(cmd, length, data)
    if got_chk != exp_chk:
        raise ChecksumError(f"Checksum mismatch: got 0x{got_chk:02X}, expected 0x{exp_chk:02X}")

    return _FnirsiDps150(KaitaiStream(BytesIO(raw)))
