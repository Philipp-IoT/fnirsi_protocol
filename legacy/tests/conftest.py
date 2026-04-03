"""Shared pytest fixtures for fnirsi_ps_control tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fnirsi_ps_control.connection import SerialConnection


@pytest.fixture()
def mock_serial_connection() -> SerialConnection:
    """Return a :class:`~fnirsi_ps_control.connection.SerialConnection` with the
    underlying ``serial.Serial`` object replaced by a :class:`~unittest.mock.MagicMock`.
    """
    conn = SerialConnection.__new__(SerialConnection)
    conn._port = "/dev/ttyUSB_FAKE"
    conn._baudrate = 115200
    conn._timeout = 1.0
    conn._serial = MagicMock()
    conn._serial.is_open = True
    return conn
