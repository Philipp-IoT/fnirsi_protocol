"""Custom exception hierarchy for fnirsi_ps_control."""

from __future__ import annotations


class FnirsiError(Exception):
    """Base exception for all fnirsi_ps_control errors."""


class ConnectionError(FnirsiError):  # noqa: A001
    """Raised when the serial connection cannot be established or is lost."""


class ProtocolError(FnirsiError):
    """Raised when a received frame violates the expected protocol."""


class ChecksumError(ProtocolError):
    """Raised when a frame checksum does not match."""


class TimeoutError(FnirsiError):  # noqa: A001
    """Raised when a command response is not received within the timeout."""


class InvalidParameterError(FnirsiError):
    """Raised when a parameter value is outside the device's accepted range."""
