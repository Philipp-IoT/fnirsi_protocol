"""High-level device interface for the FNIRSI DPS-150."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

from fnirsi_ps_control import protocol
from fnirsi_ps_control.connection import SerialConnection
from fnirsi_ps_control.exceptions import ProtocolError, TimeoutError

log = logging.getLogger(__name__)

MAX_VOLTAGE_V: float = 30.0
MAX_CURRENT_A: float = 5.1

_READY_RETRIES: int = 10
_READY_RETRY_DELAY: float = 0.1


@dataclass
class DeviceStatus:
    """Snapshot of the device state from a GET_FULL_STATUS response."""

    voltage_set_v: float
    current_set_a: float
    voltage_out_v: float
    current_out_a: float
    output_enabled: bool  # TODO: confirm bit in blob tail (offsets 96–138)

    @property
    def power_out_w(self) -> float:
        """Measured output power (Vout × Iout)."""
        return self.voltage_out_v * self.current_out_a


@dataclass
class PushOutput:
    """Periodic output measurement from CMD PUSH_OUTPUT (0xc3)."""

    vout_v: float
    iout_a: float
    pout_w: float


class DPS150:
    """High-level interface to the FNIRSI DPS-150.

    Use as a context manager — :meth:`__enter__` opens the port and performs
    the connect/READY handshake; :meth:`__exit__` disconnects and closes.

    Example
    -------
    ::

        with DPS150("/dev/ttyACM0") as ps:
            ps.set_voltage(12.0)
            ps.enable_output()
            status = ps.get_status()
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
    # Handshake
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        """Perform the connect → READY → start-session handshake.

        Confirmed sequence from pcapng capture 2026-03-29:

        1. TX ``c1 00 01 01 02``  (CTRL CONNECT_CTRL data=0x01)
        2. TX ``a1 e1 01 00 e2``  (QUERY GET_READY)
        3. RX ``a1 e1 01 01 e3``  (device responds ready=1)
        4. TX ``b0 00 01 01 01``  (START_SESSION magic — non-standard checksum)
        """
        self._conn.flush()
        self._send(protocol.encode_connect())
        log.debug("CONNECT sent")
        time.sleep(0.2)

        for attempt in range(_READY_RETRIES):
            self._send(protocol.encode_query(protocol.Cmd.GET_READY))
            parsed = self._recv()
            if parsed.frame.cmd == protocol.Cmd.GET_READY and parsed.frame.payload.ready == 1:
                log.info("Device ready (attempt %d)", attempt + 1)
                break
            log.debug("Not yet ready (attempt %d), retrying…", attempt + 1)
            time.sleep(_READY_RETRY_DELAY)
        else:
            raise TimeoutError(
                f"Device did not become ready after {_READY_RETRIES} GET_READY polls"
            )

        self._conn.write(protocol.START_SESSION_MAGIC)
        log.debug("START_SESSION magic sent")

    def _disconnect(self) -> None:
        self._send(protocol.encode_disconnect())
        log.debug("DISCONNECT sent")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float) -> None:
        """Set the output voltage in volts."""
        from fnirsi_ps_control.exceptions import InvalidParameterError

        if not 0.0 <= volts <= MAX_VOLTAGE_V:
            raise InvalidParameterError(f"Voltage {volts} V out of range (0–{MAX_VOLTAGE_V} V)")
        self._send(protocol.encode_set_voltage(volts))
        log.info("Voltage set to %.3f V", volts)

    def set_current_limit(self, amps: float) -> None:
        """Set the output current limit in amps."""
        from fnirsi_ps_control.exceptions import InvalidParameterError

        if not 0.0 <= amps <= MAX_CURRENT_A:
            raise InvalidParameterError(f"Current {amps} A out of range (0–{MAX_CURRENT_A} A)")
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
        """Query and return the current device status."""
        self._send(protocol.encode_get_status())
        parsed = self._recv()
        return _parse_status(parsed)

    def read_push_output(self) -> PushOutput:
        """Read one unsolicited PUSH_OUTPUT frame (CMD 0xc3).

        The device emits these roughly every 600 ms during an active session.
        Call this in a loop to get a live measurement stream.
        """
        parsed = self._recv()
        if parsed.frame.cmd != protocol.Cmd.PUSH_OUTPUT:
            raise ProtocolError(
                f"Expected PUSH_OUTPUT (0x{protocol.Cmd.PUSH_OUTPUT:02X}), "
                f"got 0x{parsed.frame.cmd:02X}"
            )
        p = parsed.frame.payload
        return PushOutput(vout_v=float(p.vout), iout_a=float(p.iout), pout_w=float(p.pout))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send(self, frame: protocol.Frame) -> None:
        self._conn.write(frame.encode())

    def _recv(self) -> Any:
        """Read one frame and parse it with the Kaitai parser."""
        raw = self._conn.read_frame()
        if not raw:
            raise TimeoutError("No response from device")
        try:
            return protocol.parse_frame(raw)
        except (ProtocolError, ValueError) as exc:
            raise ProtocolError(f"Failed to decode response: {exc}") from exc


def _parse_status(parsed: Any) -> DeviceStatus:
    """Extract DeviceStatus from a GET_FULL_STATUS Kaitai frame object."""
    p = parsed.frame.payload
    return DeviceStatus(
        voltage_set_v=float(p.vset),
        current_set_a=float(p.iset),
        voltage_out_v=float(p.vout),
        current_out_a=float(p.iout),
        output_enabled=False,  # TODO: confirm offset in blob tail (offsets 96–138)
    )
