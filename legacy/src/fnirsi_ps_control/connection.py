"""Low-level serial connection management for the FNIRSI DPS-150."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

import serial

from fnirsi_ps_control.exceptions import ConnectionError, TimeoutError

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants – confirmed from pcapng CDC SET_LINE_CODING analysis (2026-03-29)
# ---------------------------------------------------------------------------
DEFAULT_BAUDRATE: int = 9600    # Confirmed: manufacturer tool uses 9600 baud
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
        """Open the serial port.

        Configures DTR=False and RTS=True to match the manufacturer tool's
        CDC SET_CONTROL_LINE_STATE sequence (confirmed from pcapng capture).
        The Linux ``cdc_acm`` driver asserts DTR=True on port open by default,
        which prevents the DPS-150 from responding.
        """
        if self._serial and self._serial.is_open:
            return
        try:
            # Two-step open: configure DTR/RTS *before* open() so the
            # cdc_acm driver sends the correct SET_CONTROL_LINE_STATE.
            s = serial.Serial()
            s.port = self._port
            s.baudrate = self._baudrate
            s.timeout = self._timeout
            s.dtr = False
            s.rts = True
            s.open()
            self._serial = s
            log.info("Opened %s @ %d baud (DTR=off, RTS=on)", self._port, self._baudrate)
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
        """Write *data* to the port, prepending the ``0xf1`` TX direction byte.

        The DPS-150 wire protocol requires a direction prefix before every
        frame: ``0xf1`` for host→device.  This was confirmed from a Windows
        USBPcap capture (USBPcap records raw bulk payloads; every TX frame
        in the pcapng starts with ``0xf1``).

        Raises
        ------
        ConnectionError
            If the port is not open or a serial error occurs.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Port is not open")
        try:
            wire = b"\xf1" + data
            self._serial.write(wire)
            log.debug("TX (%d B): %s", len(wire), wire.hex(" "))
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

    def read_frame(self) -> bytes:
        """Read exactly one application-layer frame from the device.

        Wire format: ``[DIR:1] [START:1] [CMD:1] [LEN:1] [DATA:LEN] [CHKSUM:1]``.

        The ``0xf0`` direction prefix is consumed and discarded.  The returned
        bytes contain ``[START] [CMD] [LEN] [DATA] [CHKSUM]`` (no DIR byte),
        ready for :meth:`~protocol.Frame.decode`.

        Returns
        -------
        bytes
            The frame *without* the direction prefix.

        Raises
        ------
        ConnectionError
            If the port is closed or a serial error occurs.
        TimeoutError
            If no data arrives within the configured read timeout.
        """
        # 1) Read DIR byte (0xf0) + START + CMD + LEN  →  4 bytes total
        header = self.read(4)               # DIR + START + CMD + LEN
        if len(header) < 4:
            raise TimeoutError("Timeout waiting for frame header from device")
        dir_byte = header[0]
        if dir_byte != 0xF0:
            log.warning("Unexpected DIR byte 0x%02X (expected 0xF0)", dir_byte)
        length = header[3]                  # LEN field
        tail   = self.read(length + 1)      # DATA + CHKSUM
        if len(tail) < length + 1:
            raise TimeoutError("Timeout reading frame body from device")
        return header[1:] + tail            # strip DIR, keep START..CHKSUM

    def flush(self) -> None:
        """Flush both input and output buffers."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

    @property
    def is_open(self) -> bool:
        """Return ``True`` if the port is open."""
        return bool(self._serial and self._serial.is_open)
