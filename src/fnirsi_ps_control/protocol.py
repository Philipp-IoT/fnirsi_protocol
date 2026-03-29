"""Protocol encode / decode layer for the FNIRSI DPS-150.

.. note::
    This module will grow as the serial protocol is reverse-engineered.
    See ``docs/protocol/`` for the current state of the RE effort.

Frame structure (hypothesis – update as RE progresses)
-------------------------------------------------------

.. code-block:: text

    +--------+--------+--------+  ...  +--------+----------+
    | START  |  CMD   | LENGTH |  DATA | CHKSUM |  STOP    |
    | 1 byte | 1 byte | 1 byte | N byte| 1 byte | 1 byte   |
    +--------+--------+--------+  ...  +--------+----------+

All multi-byte integers: big-endian unless noted otherwise.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from fnirsi_ps_control.exceptions import ChecksumError, ProtocolError

# ---------------------------------------------------------------------------
# Frame constants – adjust to match real captures
# ---------------------------------------------------------------------------
FRAME_START: int = 0xAA   # TBD
FRAME_STOP: int = 0x55    # TBD
MIN_FRAME_LEN: int = 5    # start + cmd + length + checksum + stop


# ---------------------------------------------------------------------------
# Command IDs – extend as commands are discovered
# ---------------------------------------------------------------------------
class Cmd:
    """Known command identifiers."""

    GET_STATUS: int = 0x01     # TBD
    SET_VOLTAGE: int = 0x02    # TBD
    SET_CURRENT: int = 0x03    # TBD
    SET_OUTPUT: int = 0x04     # TBD


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Frame:
    """Represents a single protocol frame."""

    cmd: int
    data: bytes = field(default=b"")

    def encode(self) -> bytes:
        """Serialise this frame to bytes ready for transmission."""
        length = len(self.data)
        checksum = _checksum(bytes([self.cmd, length]) + self.data)
        return struct.pack(
            f"BBB{length}sBB",
            FRAME_START,
            self.cmd,
            length,
            self.data,
            checksum,
            FRAME_STOP,
        )

    @classmethod
    def decode(cls, raw: bytes) -> "Frame":
        """Parse *raw* bytes into a :class:`Frame`.

        Raises
        ------
        ProtocolError
            If the frame boundaries or length are invalid.
        ChecksumError
            If the checksum does not match.
        """
        if len(raw) < MIN_FRAME_LEN:
            raise ProtocolError(f"Frame too short: {len(raw)} bytes")
        if raw[0] != FRAME_START:
            raise ProtocolError(f"Unexpected start byte: 0x{raw[0]:02X}")
        if raw[-1] != FRAME_STOP:
            raise ProtocolError(f"Unexpected stop byte: 0x{raw[-1]:02X}")

        cmd = raw[1]
        length = raw[2]

        if len(raw) != MIN_FRAME_LEN + length:
            raise ProtocolError(
                f"Length field ({length}) does not match frame size ({len(raw)})"
            )

        data = raw[3 : 3 + length]
        received_chk = raw[3 + length]
        expected_chk = _checksum(bytes([cmd, length]) + data)

        if received_chk != expected_chk:
            raise ChecksumError(
                f"Checksum mismatch: got 0x{received_chk:02X}, expected 0x{expected_chk:02X}"
            )

        return cls(cmd=cmd, data=data)


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------
def encode_set_voltage(millivolts: int) -> Frame:
    """Build a SET_VOLTAGE frame.

    Parameters
    ----------
    millivolts:
        Target voltage in millivolts (e.g. 12000 for 12 V).
    """
    return Frame(cmd=Cmd.SET_VOLTAGE, data=struct.pack(">I", millivolts))


def encode_set_current(milliamps: int) -> Frame:
    """Build a SET_CURRENT frame.

    Parameters
    ----------
    milliamps:
        Current limit in milliamps (e.g. 1000 for 1 A).
    """
    return Frame(cmd=Cmd.SET_CURRENT, data=struct.pack(">I", milliamps))


def encode_set_output(enabled: bool) -> Frame:
    """Build an OUTPUT ON/OFF frame."""
    return Frame(cmd=Cmd.SET_OUTPUT, data=bytes([0x01 if enabled else 0x00]))


def encode_get_status() -> Frame:
    """Build a GET_STATUS request frame."""
    return Frame(cmd=Cmd.GET_STATUS)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _checksum(data: bytes) -> int:
    """Simple XOR checksum – update to match real device checksum algorithm."""
    result = 0
    for byte in data:
        result ^= byte
    return result
