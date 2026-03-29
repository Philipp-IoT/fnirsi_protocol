"""Low-level serial connection management for the FNIRSI DPS-150."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

import serial

from fnirsi_ps_control.exceptions import ConnectionError

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants – update once the protocol is fully characterised
# ---------------------------------------------------------------------------
DEFAULT_BAUDRATE: int = 115200  # TBD – adjust after RE
DEFAULT_TIMEOUT: float = 1.0    # seconds


class SerialConnection:
    """Thin wrapper around :class:`serial.Serial` with context-manager support.

    Parameters
    ----------
    port:
        Serial port path, e.g. ``/dev/ttyACM0`` or ``COM3``.
    baudrate:
        Baud rate (default 115 200 – update once confirmed by RE).
    timeout:
        Read timeout in seconds.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial: serial.Serial | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Open the serial port."""
        if self._serial and self._serial.is_open:
            return
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._timeout,
            )
            log.info("Opened %s @ %d baud", self._port, self._baudrate)
        except serial.SerialException as exc:
            raise ConnectionError(f"Cannot open {self._port}: {exc}") from exc

    def close(self) -> None:
        """Close the serial port if open."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            log.info("Closed %s", self._port)

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def write(self, data: bytes) -> None:
        """Write *data* to the port.

        Raises
        ------
        ConnectionError
            If the port is not open or a serial error occurs.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Port is not open")
        try:
            self._serial.write(data)
            log.debug("TX (%d B): %s", len(data), data.hex(" "))
        except serial.SerialException as exc:
            raise ConnectionError(f"Write error: {exc}") from exc

    def read(self, n: int) -> bytes:
        """Read exactly *n* bytes from the port.

        Raises
        ------
        ConnectionError
            If the port is not open or a serial error occurs.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Port is not open")
        try:
            data = self._serial.read(n)
            log.debug("RX (%d B): %s", len(data), data.hex(" "))
            return data
        except serial.SerialException as exc:
            raise ConnectionError(f"Read error: {exc}") from exc

    def read_until(self, terminator: bytes = b"\n", size: int | None = None) -> bytes:
        """Read until *terminator* is found or *size* bytes have been read."""
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Port is not open")
        try:
            data = self._serial.read_until(terminator, size)
            log.debug("RX (%d B): %s", len(data), data.hex(" "))
            return data
        except serial.SerialException as exc:
            raise ConnectionError(f"Read error: {exc}") from exc

    def flush(self) -> None:
        """Flush both input and output buffers."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

    @property
    def is_open(self) -> bool:
        """Return ``True`` if the port is open."""
        return bool(self._serial and self._serial.is_open)
