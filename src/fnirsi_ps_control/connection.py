"""Low-level serial connection for the FNIRSI DPS-150."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

import serial

from fnirsi_ps_control.exceptions import ConnectionError, TimeoutError

log = logging.getLogger(__name__)

DEFAULT_BAUDRATE: int = 9600
DEFAULT_TIMEOUT: float = 1.0


class SerialConnection:
    """Thin wrapper around :class:`serial.Serial`.

    The DPS-150 requires DTR=False and RTS=True on port open (confirmed
    from pcapng CDC SET_CONTROL_LINE_STATE analysis 2026-03-29).  The Linux
    ``cdc_acm`` driver asserts DTR=True by default, which prevents the device
    from responding.  A two-step open (configure, then open) ensures the driver
    sends the correct SET_CONTROL_LINE_STATE before any data flows.
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
        """Open the serial port with DTR=False, RTS=True."""
        if self._serial and self._serial.is_open:
            return
        try:
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
    # I/O
    # ------------------------------------------------------------------

    def write(self, data: bytes) -> None:
        """Write *data*, prepending the ``0xf1`` TX direction byte.

        Every host→device frame on the wire starts with ``0xf1`` (confirmed
        from USBPcap raw bulk payloads — it is part of the application protocol,
        not a USB-layer artefact).
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
        """Read exactly *n* bytes."""
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Port is not open")
        try:
            data = self._serial.read(n)
            log.debug("RX (%d B): %s", len(data), data.hex(" "))
            return bytes(data)
        except serial.SerialException as exc:
            raise ConnectionError(f"Read error: {exc}") from exc

    def read_frame(self) -> bytes:
        """Read exactly one application-layer frame.

        Wire format: ``[DIR:1][START:1][CMD:1][LEN:1][DATA:LEN][CHKSUM:1]``

        Consumes and discards the ``0xf0`` direction prefix.  Returns
        ``[START][CMD][LEN][DATA][CHKSUM]`` ready for :func:`~protocol.parse_frame`.

        Raises
        ------
        TimeoutError
            If no data arrives within the configured timeout.
        """
        header = self.read(4)  # DIR + START + CMD + LEN
        if len(header) < 4:
            raise TimeoutError("Timeout waiting for frame header")
        dir_byte, _start, _cmd, length = header
        if dir_byte != 0xF0:
            log.warning("Unexpected DIR byte 0x%02X (expected 0xF0)", dir_byte)
        tail = self.read(length + 1)  # DATA + CHKSUM
        if len(tail) < length + 1:
            raise TimeoutError("Timeout reading frame body")
        return header[1:] + tail  # strip DIR, return START..CHKSUM

    def flush(self) -> None:
        """Flush RX and TX buffers."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

    @property
    def is_open(self) -> bool:
        return bool(self._serial and self._serial.is_open)
