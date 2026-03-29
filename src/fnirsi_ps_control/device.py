"""High-level device abstraction for the FNIRSI DPS-150."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Self

from fnirsi_ps_control.connection import SerialConnection
from fnirsi_ps_control.exceptions import ProtocolError, TimeoutError
from fnirsi_ps_control import protocol

log = logging.getLogger(__name__)

# Voltage / current limits of the DPS-150 – adjust to real specs
MAX_VOLTAGE_MV: int = 30_000   # 30 V
MAX_CURRENT_MA: int = 5_000    # 5 A


@dataclass
class DeviceStatus:
    """Snapshot of the device state returned by :meth:`DPS150.get_status`."""

    voltage_set_mv: int    # set-point in millivolts
    voltage_meas_mv: int   # measured output voltage in millivolts
    current_set_ma: int    # current limit in milliamps
    current_meas_ma: int   # measured output current in milliamps
    output_enabled: bool

    @property
    def power_mw(self) -> int:
        """Measured output power in milliwatts."""
        return self.voltage_meas_mv * self.current_meas_ma // 1000


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

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self._conn = SerialConnection(port=port, baudrate=baudrate, timeout=timeout)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> Self:
        self._conn.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float) -> None:
        """Set the output voltage.

        Parameters
        ----------
        volts:
            Target voltage in volts (e.g. ``12.0``). Resolution is 1 mV.

        Raises
        ------
        InvalidParameterError
            If *volts* is outside the device range.
        """
        from fnirsi_ps_control.exceptions import InvalidParameterError

        mv = round(volts * 1000)
        if not 0 <= mv <= MAX_VOLTAGE_MV:
            raise InvalidParameterError(
                f"Voltage {volts} V out of range (0 – {MAX_VOLTAGE_MV / 1000} V)"
            )
        frame = protocol.encode_set_voltage(mv)
        self._send(frame)
        log.info("Voltage set to %.3f V", volts)

    def set_current_limit(self, amps: float) -> None:
        """Set the output current limit.

        Parameters
        ----------
        amps:
            Current limit in amps (e.g. ``1.5``). Resolution is 1 mA.
        """
        from fnirsi_ps_control.exceptions import InvalidParameterError

        ma = round(amps * 1000)
        if not 0 <= ma <= MAX_CURRENT_MA:
            raise InvalidParameterError(
                f"Current {amps} A out of range (0 – {MAX_CURRENT_MA / 1000} A)"
            )
        frame = protocol.encode_set_current(ma)
        self._send(frame)
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
        """Read one frame from the device.

        .. todo::
            Replace with proper framing logic once the protocol stop-byte /
            length-field semantics are confirmed.
        """
        # Placeholder: read until FRAME_STOP byte
        raw = self._conn.read_until(bytes([protocol.FRAME_STOP]))
        if not raw:
            raise TimeoutError("No response from device")
        try:
            return protocol.Frame.decode(raw)
        except (ProtocolError, ValueError) as exc:
            raise ProtocolError(f"Failed to decode response: {exc}") from exc


def _parse_status(frame: protocol.Frame) -> DeviceStatus:
    """Parse a GET_STATUS response frame.

    .. note::
        Payload layout is a placeholder – update once RE confirms the format.
    """
    import struct

    if len(frame.data) < 10:
        raise ProtocolError(
            f"GET_STATUS response payload too short: {len(frame.data)} bytes"
        )

    # Hypothetical layout: 5 × uint16, big-endian
    v_set, v_meas, i_set, i_meas, flags = struct.unpack_from(">HHHHH", frame.data)
    return DeviceStatus(
        voltage_set_mv=v_set,
        voltage_meas_mv=v_meas,
        current_set_ma=i_set,
        current_meas_ma=i_meas,
        output_enabled=bool(flags & 0x01),
    )
