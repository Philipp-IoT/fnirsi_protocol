"""TX encode layer and Kaitai RX parser wrapper for the FNIRSI DPS-150.

Wire format (confirmed 2026-03-29):

    [DIR:1] [START:1] [CMD:1] [LEN:1] [DATA×LEN] [CHKSUM:1]

    DIR    : 0xf1 host→device  |  0xf0 device→host
    START  : 0xa1 query/response  |  0xb1 write cmd  |  0xc1 connect/disconnect
    CHKSUM : (CMD + LEN + Σ DATA) mod 256  (DIR and START excluded)
    Values : IEEE 754 32-bit little-endian float for voltage and current

Exception: the session-start magic frame (START=0xb0) uses a non-standard
4-byte body without CMD/LEN/CHKSUM — see :func:`encode_session_magic`.

The Kaitai-generated parser (``protocol/generated/fnirsi_dps150.py``) handles
all RX decoding and is the single source of truth for all protocol constants.
This module provides TX encoding plus a thin ``parse_frame()`` wrapper.
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
# Constants derived from Kaitai-generated IntEnums (single source of truth)
# ---------------------------------------------------------------------------
DIR_TX: int = _FnirsiDps150.Direction.host_to_device
DIR_RX: int = _FnirsiDps150.Direction.device_to_host

START_QUERY: int = _FnirsiDps150.StartByte.query_or_response
START_WRITE: int = _FnirsiDps150.StartByte.write_command
START_CTRL: int = _FnirsiDps150.StartByte.connect_ctrl


class Cmd:
    """Known command identifiers — aliased from the Kaitai-generated IntEnum."""

    CONNECT_CTRL: int = _FnirsiDps150.CommandId.connect_ctrl
    GET_READY: int = _FnirsiDps150.CommandId.ready_status
    GET_DEVICE_NAME: int = _FnirsiDps150.CommandId.get_device_name
    GET_HW_VERSION: int = _FnirsiDps150.CommandId.get_hw_version
    GET_FW_VERSION: int = _FnirsiDps150.CommandId.get_fw_version
    GET_FULL_STATUS: int = _FnirsiDps150.CommandId.get_full_status
    SET_VOLTAGE: int = _FnirsiDps150.CommandId.set_voltage
    SET_CURRENT: int = _FnirsiDps150.CommandId.set_current
    SET_OUTPUT: int = _FnirsiDps150.CommandId.set_output
    PUSH_OUTPUT: int = _FnirsiDps150.CommandId.push_output
    PUSH_VIN_A: int = _FnirsiDps150.CommandId.push_vin_a
    PUSH_VIN_B: int = _FnirsiDps150.CommandId.push_vin_b
    PUSH_VIN_C: int = _FnirsiDps150.CommandId.push_vin_c
    PUSH_MAX_CURRENT: int = _FnirsiDps150.CommandId.push_max_current


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
    dir: int = field(default_factory=lambda: DIR_TX)

    def encode(self) -> bytes:
        """Serialise to bytes ready for transmission (includes DIR prefix)."""
        length = len(self.data)
        chk = _checksum(self.cmd, length, self.data)
        return struct.pack(
            f"BBBB{length}sB", self.dir, self.start, self.cmd, length, self.data, chk
        )


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


def encode_session_magic() -> bytes:
    """Build the 6-byte session-start magic frame (DIR + START + 4-byte payload).

    The magic body bytes are defined by ``session_magic_body.magic`` contents
    in ``protocol/fnirsi_dps150.ksy`` — update there if the wire format changes.
    """
    # Magic payload bytes as declared by `session_magic_body.magic` contents in fnirsi_dps150.ksy.
    _magic_payload: bytes = b"\x00\x01\x01\x01"
    return bytes([DIR_TX, _FnirsiDps150.StartByte.start_session_magic]) + _magic_payload


# ---------------------------------------------------------------------------
# RX parser (Kaitai)
# ---------------------------------------------------------------------------
def parse_frame(raw: bytes) -> _Any:
    """Parse a raw wire frame into a FnirsiDps150 object.

    Parameters
    ----------
    raw:
        Full frame bytes with format ``[DIR][START][CMD][LEN][DATA][CHKSUM]``.

    Returns
    -------
    FnirsiDps150
        Kaitai-generated parser object.  Access via ``result.frame.body.cmd``
        and ``result.frame.body.payload``.

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

    if len(raw) < 5:
        raise ProtocolError(f"Frame too short: {len(raw)} bytes (minimum 5)")

    cmd = raw[2]
    length = raw[3]
    expected_total = 5 + length
    if len(raw) < expected_total:
        raise ProtocolError(f"Frame truncated: have {len(raw)} bytes, need {expected_total}")

    data = raw[4 : 4 + length]
    got_chk = raw[4 + length]
    exp_chk = _checksum(cmd, length, data)
    if got_chk != exp_chk:
        raise ChecksumError(f"Checksum mismatch: got 0x{got_chk:02X}, expected 0x{exp_chk:02X}")

    return _FnirsiDps150(KaitaiStream(BytesIO(raw)))
