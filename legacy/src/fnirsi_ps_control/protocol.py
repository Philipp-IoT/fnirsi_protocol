"""Protocol encode / decode layer for the FNIRSI DPS-150.

Wire format (CONFIRMED 2026-03-29 from Windows USBPcap capture):

.. code-block:: text

    [DIR] [START] [CMD] [LEN] [DATA × LEN] [CHKSUM]

    DIR    : 0xf1 host→device  |  0xf0 device→host
    START  : 0xa1 query/response  |  0xb1 write  |  0xc1 connect/disconnect
    CHKSUM : (CMD + LEN + Σ DATA bytes) mod 256  (DIR and START excluded)
    Values : IEEE 754 32-bit little-endian float for voltage and current

The DIR byte is a direction prefix that is part of the serial data stream.
It is NOT a USB-layer artefact (confirmed: USBPcap captures raw bulk
payloads; every TX frame in the pcapng starts with ``0xf1``, every RX
with ``0xf0``).

See ``docs/protocol/`` for full command catalogue and RE notes.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from fnirsi_ps_control.exceptions import ChecksumError, ProtocolError

# ---------------------------------------------------------------------------
# Direction prefixes (part of the wire protocol, NOT USB-layer artefacts)
# ---------------------------------------------------------------------------
DIR_TX: int = 0xF1    # host → device  (prepended to every TX frame)
DIR_RX: int = 0xF0    # device → host  (first byte of every RX frame)

# ---------------------------------------------------------------------------
# Start bytes
# ---------------------------------------------------------------------------
START_QUERY: int = 0xA1    # read / query from host; ALL device responses
START_WRITE: int = 0xB1    # write / set command from host
START_CTRL:  int = 0xC1    # connect / disconnect

# Opaque 5-byte magic sent by the manufacturer tool after the READY handshake
# in every captured session.  START=0xb0, but checksum does NOT follow the
# standard algorithm (expected 0x02, observed 0x01).  Sent as raw bytes
# (the DIR_TX prefix is added by the transport layer).
START_SESSION_MAGIC: bytes = b"\xb0\x00\x01\x01\x01"

# ---------------------------------------------------------------------------
# Command IDs  (confirmed from capture unless noted)
# ---------------------------------------------------------------------------


class Cmd:
    """Known command identifiers (all confirmed from 2026-03-29 capture)."""

    # Connection control
    CONNECT_CTRL:    int = 0x00   # START=0xc1; DATA=01 connect, 00 disconnect

    # Host reads (query + response, START=0xa1 both directions)
    GET_READY:       int = 0xE1   # response: uint8 (0x01 = ready)
    GET_DEVICE_NAME: int = 0xDE   # response: ASCII "DPS-150"
    GET_HW_VERSION:  int = 0xE0   # response: ASCII "V1.2"
    GET_FW_VERSION:  int = 0xDF   # response: ASCII "V1.0"
    GET_FULL_STATUS: int = 0xFF   # response: 139-byte blob

    # Host writes (START=0xb1)
    SET_VOLTAGE:     int = 0xC1   # DATA: float32 LE [V]
    SET_CURRENT:     int = 0xC2   # DATA: float32 LE [A]
    SET_OUTPUT:      int = 0xDB   # DATA: uint8  0x01=enable 0x00=disable; device echoes back

    # Periodic device push (~600 ms, unsolicited, START=0xa1)
    PUSH_OUTPUT:     int = 0xC3   # 3 × float32: Vout[V], Iout[A], Pout[W]
    PUSH_VIN_A:      int = 0xC0   # float32: Vin channel A [V] (~20.1 V)
    PUSH_VIN_B:      int = 0xE2   # float32: Vin channel B [V] (~19.9 V)
    PUSH_MAX_I_REF:  int = 0xE3   # float32: always 5.1 A (max current constant)
    PUSH_VIN_C:      int = 0xC4   # float32: ~23.67 V (TBD – Vin2 or boost rail)


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------

def _checksum(cmd: int, length: int, data: bytes) -> int:
    """Compute frame checksum: (CMD + LEN + Σ DATA) mod 256."""
    return (cmd + length + sum(data)) & 0xFF


# ---------------------------------------------------------------------------
# Generic Frame
# ---------------------------------------------------------------------------

@dataclass
class Frame:
    """One application-layer frame."""

    start: int
    cmd: int
    data: bytes = field(default=b"")

    # ------------------------------------------------------------------
    # Encode
    # ------------------------------------------------------------------

    def encode(self) -> bytes:
        """Serialise this frame to bytes ready for transmission."""
        length = len(self.data)
        chk = _checksum(self.cmd, length, self.data)
        return struct.pack(
            f"BBB{length}sB",
            self.start,
            self.cmd,
            length,
            self.data,
            chk,
        )

    # ------------------------------------------------------------------
    # Decode
    # ------------------------------------------------------------------

    @classmethod
    def decode(cls, raw: bytes) -> Frame:
        """Parse *raw* bytes into a :class:`Frame`.

        Raises
        ------
        ProtocolError
            Frame too short or length field inconsistent.
        ChecksumError
            Checksum does not match.
        """
        if len(raw) < 4:
            raise ProtocolError(f"Frame too short: {len(raw)} bytes (min 4)")

        start  = raw[0]
        cmd    = raw[1]
        length = raw[2]

        expected_total = 4 + length   # start + cmd + len + data + chk
        if len(raw) < expected_total:
            raise ProtocolError(
                f"Frame truncated: have {len(raw)} bytes, need {expected_total}"
            )

        data    = raw[3 : 3 + length]
        got_chk = raw[3 + length]
        exp_chk = _checksum(cmd, length, data)

        if got_chk != exp_chk:
            raise ChecksumError(
                f"Checksum mismatch: got 0x{got_chk:02X}, expected 0x{exp_chk:02X}"
            )

        return cls(start=start, cmd=cmd, data=data)


# ---------------------------------------------------------------------------
# TX frame builders
# ---------------------------------------------------------------------------

def encode_connect() -> Frame:
    """Build a CONNECT request frame."""
    return Frame(start=START_CTRL, cmd=Cmd.CONNECT_CTRL, data=b"\x01")


def encode_disconnect() -> Frame:
    """Build a DISCONNECT request frame."""
    return Frame(start=START_CTRL, cmd=Cmd.CONNECT_CTRL, data=b"\x00")


def encode_set_voltage(volts: float) -> Frame:
    """Build a SET_VOLTAGE frame.

    Parameters
    ----------
    volts:
        Target voltage in **volts** (e.g. ``10.0``). Sent as float32 LE.
    """
    return Frame(start=START_WRITE, cmd=Cmd.SET_VOLTAGE, data=struct.pack("<f", volts))


def encode_set_current(amps: float) -> Frame:
    """Build a SET_CURRENT frame.

    Parameters
    ----------
    amps:
        Current limit in **amps** (e.g. ``1.0``). Sent as float32 LE.
    """
    return Frame(start=START_WRITE, cmd=Cmd.SET_CURRENT, data=struct.pack("<f", amps))


def encode_output_enable() -> Frame:
    """Build a SET_OUTPUT frame that enables output.

    TX: ``b1 db 01 01 dd``  (CHKSUM = (0xdb+0x01+0x01) mod 256 = 0xdd).
    Device echoes back with START=0xa1.
    """
    return Frame(start=START_WRITE, cmd=Cmd.SET_OUTPUT, data=b"\x01")


def encode_output_disable() -> Frame:
    """Build a SET_OUTPUT frame that disables output.

    TX: ``b1 db 01 00 dc``  (CHKSUM = (0xdb+0x01+0x00) mod 256 = 0xdc).
    Device echoes back with START=0xa1.
    """
    return Frame(start=START_WRITE, cmd=Cmd.SET_OUTPUT, data=b"\x00")


def encode_set_output(enabled: bool) -> Frame:
    """Build a SET_OUTPUT frame.

    Convenience wrapper for :func:`encode_output_enable` /
    :func:`encode_output_disable`.
    """
    return encode_output_enable() if enabled else encode_output_disable()


def encode_get_status() -> Frame:
    """Build a GET_FULL_STATUS query frame (CMD 0xff).

    The device responds with a 139-byte blob (CMD 0xff, START 0xa1).
    """
    return encode_query(Cmd.GET_FULL_STATUS)


def encode_query(cmd: int) -> Frame:
    """Build a generic read-request frame (DATA = 0x00)."""
    return Frame(start=START_QUERY, cmd=cmd, data=b"\x00")


# ---------------------------------------------------------------------------
# RX payload parsers
# ---------------------------------------------------------------------------

def decode_f32(data: bytes) -> float:
    """Decode a 4-byte little-endian float32 payload."""
    if len(data) < 4:
        raise ProtocolError(f"Expected 4 bytes for float32, got {len(data)}")
    return float(struct.unpack_from("<f", data)[0])


def decode_string(data: bytes) -> str:
    """Decode an ASCII string payload (no NUL terminator)."""
    return data.decode("ascii")


def decode_push_output(data: bytes) -> tuple[float, float, float]:
    """Decode CMD 0xc3 periodic output measurement.

    Returns
    -------
    tuple
        ``(vout_V, iout_A, pout_W)`` — all 0.0 when output is disabled.

    Pout is confirmed from capture
    ``dps150_connect_enable_out_set_v_set_i_disable_disconnect.txt`` row 12827:
    Vout≈8.45 V, Iout≈0.0077 A → third float ≈0.065 W ≈ 8.45×0.0077.
    """
    if len(data) < 12:
        raise ProtocolError(f"CMD_PUSH_OUTPUT: expected 12 bytes, got {len(data)}")
    vout, iout, pout = struct.unpack_from("<fff", data)
    return float(vout), float(iout), float(pout)
