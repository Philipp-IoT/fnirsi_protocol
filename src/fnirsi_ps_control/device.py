"""High-level device abstraction for the FNIRSI DPS-150."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Self

from fnirsi_ps_control import protocol
from fnirsi_ps_control.connection import SerialConnection
from fnirsi_ps_control.exceptions import ProtocolError, TimeoutError

log = logging.getLogger(__name__)

# Voltage / current limits of the DPS-150
MAX_VOLTAGE_V: float = 30.0    # 30 V
MAX_CURRENT_A: float = 5.1     # 5.1 A (confirmed from PUSH_MAX_I_REF)

# How many times to poll GET_READY after CONNECT before giving up
_READY_RETRIES: int = 10
_READY_RETRY_DELAY: float = 0.1   # seconds


@dataclass
class DeviceStatus:
    """Snapshot of the device state returned by :meth:`DPS150.get_status`."""

    voltage_set_v: float    # set-point in volts
    current_set_a: float    # current limit in amps
    output_enabled: bool

    @property
    def power_w(self) -> float:
        """Estimated output power (set-point only; use PUSH_OUTPUT for measured)."""
        return self.voltage_set_v * self.current_set_a


class DPS150:
    """High-level interface to the FNIRSI DPS-150 power supply.

    Parameters
    ----------
    port:
        Serial port, e.g. ``/dev/ttyACM0``.
    baudrate:
        Baud rate (defaults to :data:`~fnirsi_ps_control.connection.DEFAULT_BAUDRATE`).
    timeout:
        Command response timeout in seconds.

    Examples
    --------
    ::

        with DPS150("/dev/ttyACM0") as ps:
            ps.set_voltage(12.0)
            ps.enable_output()
            status = ps.get_status()
            print(status)
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> None:
        self._conn = SerialConnection(port=port, baudrate=baudrate, timeout=timeout)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> Self:
        self._conn.open()
        self._connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            self._disconnect()
        finally:
            self._conn.close()

    # ------------------------------------------------------------------
    # Application-level connect / disconnect handshake
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        """Send CONNECT frame, wait for READY, and start the session.

        The required handshake (confirmed from captures 2026-03-29):

        1. TX ``c1 00 01 01 02``  (CTRL CONNECT_CTRL data=0x01)
        2. TX ``a1 e1 01 00 e2``  (QUERY GET_READY)
        3. RX ``a1 e1 01 01 e3``  (device responds ready=1)
        4. TX ``b0 00 01 01 01``  (START_SESSION – raw magic; see note)

        Step 4 is a raw 5-byte sequence sent by the manufacturer tool in
        **every** captured session.  Its checksum does not match the normal
        algorithm (expected 0x02, got 0x01), so it is treated as an opaque
        magic sequence rather than a standard protocol frame.

        Raises
        ------
        TimeoutError
            If the device does not become ready within *_READY_RETRIES* polls.
        """
        self._conn.flush()
        self._send(protocol.encode_connect())
        log.debug("CONNECT sent")
        # Give the device a moment to process the CONNECT before polling.
        time.sleep(0.2)

        for attempt in range(_READY_RETRIES):
            self._send(protocol.encode_query(protocol.Cmd.GET_READY))
            frame = self._recv()
            if frame.cmd == protocol.Cmd.GET_READY and frame.data == b"\x01":
                log.info("Device ready (attempt %d)", attempt + 1)
                break
            log.debug("Not yet ready (attempt %d), retrying…", attempt + 1)
            time.sleep(_READY_RETRY_DELAY)
        else:
            raise TimeoutError(
                f"Device did not become ready after {_READY_RETRIES} GET_READY polls"
            )

        # Start-session magic (confirmed in both pcapng captures).
        # Raw bytes because the checksum does not follow the standard algorithm.
        self._conn.write(protocol.START_SESSION_MAGIC)
        log.debug("START_SESSION magic sent")

    def _disconnect(self) -> None:
        """Send DISCONNECT frame."""
        self._send(protocol.encode_disconnect())
        log.debug("DISCONNECT sent")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float) -> None:
        """Set the output voltage.

        Parameters
        ----------
        volts:
            Target voltage in volts (e.g. ``12.0``).

        Raises
        ------
        InvalidParameterError
            If *volts* is outside the device range.
        """
        from fnirsi_ps_control.exceptions import InvalidParameterError

        if not 0.0 <= volts <= MAX_VOLTAGE_V:
            raise InvalidParameterError(
                f"Voltage {volts} V out of range (0 – {MAX_VOLTAGE_V} V)"
            )
        # encode_set_voltage expects float volts directly (float32 LE on the wire)
        self._send(protocol.encode_set_voltage(volts))
        log.info("Voltage set to %.3f V", volts)

    def set_current_limit(self, amps: float) -> None:
        """Set the output current limit.

        Parameters
        ----------
        amps:
            Current limit in amps (e.g. ``1.5``).
        """
        from fnirsi_ps_control.exceptions import InvalidParameterError

        if not 0.0 <= amps <= MAX_CURRENT_A:
            raise InvalidParameterError(
                f"Current {amps} A out of range (0 – {MAX_CURRENT_A} A)"
            )
        # encode_set_current expects float amps directly (float32 LE on the wire)
        self._send(protocol.encode_set_current(amps))
        log.info("Current limit set to %.3f A", amps)

    def enable_output(self) -> None:
        """Enable the power supply output."""
        self._send(protocol.encode_set_output(True))
        log.info("Output enabled")

    def disable_output(self) -> None:
        """Disable the power supply output."""
        self._send(protocol.encode_set_output(False))
        log.info("Output disabled")

    def get_status(self) -> DeviceStatus:
        """Query and return the current device status.

        Raises
        ------
        TimeoutError
            If no response is received within the configured timeout.
        ProtocolError
            If the response frame cannot be parsed.
        """
        self._send(protocol.encode_get_status())
        raw = self._recv()
        return _parse_status(raw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send(self, frame: protocol.Frame) -> None:
        self._conn.write(frame.encode())

    def _recv(self) -> protocol.Frame:
        """Read exactly one length-delimited frame from the device.

        Frame format: ``[START:1] [CMD:1] [LEN:1] [DATA:LEN] [CHKSUM:1]``.
        There is **no** stop byte; :meth:`~SerialConnection.read_frame` uses
        the LEN field to know how many bytes to read.

        Raises
        ------
        TimeoutError
            If no data arrives within the configured timeout.
        ProtocolError
            If the frame fails checksum validation.
        """
        raw = self._conn.read_frame()
        if not raw:
            raise TimeoutError("No response from device")
        try:
            return protocol.Frame.decode(raw)
        except (ProtocolError, ValueError) as exc:
            raise ProtocolError(f"Failed to decode response: {exc}") from exc


def _parse_status(frame: protocol.Frame) -> DeviceStatus:
    """Parse a GET_FULL_STATUS (CMD 0xff) response frame.

    Confirmed offsets from capture ``ps_connect_raw.pcapng`` (2026-03-29):

    * bytes  4– 7: V_set   float32 LE [V]  (e.g. 10.0 V)
    * bytes  8–11: I_set   float32 LE [A]  (e.g.  1.0 A)

    Remaining 139-byte blob layout is still partially TBD
    (see ``docs/protocol/commands.md``).
    """
    import struct

    # 139-byte data blob: first 12 bytes contain Vin_A, V_set, I_set
    if len(frame.data) < 12:
        raise ProtocolError(
            f"GET_FULL_STATUS payload too short: {len(frame.data)} bytes (need ≥12)"
        )

    _vin_a = struct.unpack_from("<f", frame.data, 0)[0]   # Vin channel A [V]
    v_set  = struct.unpack_from("<f", frame.data, 4)[0]   # V_set [V]
    i_set  = struct.unpack_from("<f", frame.data, 8)[0]   # I_set [A]

    # output_enabled: TBD – not yet confirmed in the blob; default False
    return DeviceStatus(
        voltage_set_v=float(v_set),
        current_set_a=float(i_set),
        output_enabled=False,  # TODO: confirm offset once blob tail is RE'd
    )
