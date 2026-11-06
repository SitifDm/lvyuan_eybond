"""Base client for LVYUAN Inverter (EyeBond G-ASCII).
Contains base exceptions used by the serial client and coordinator.
"""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# ------------------------------ exceptions ------------------------------

class LvyuanError(Exception):
    """Base exception for Lvyuan errors."""

class LvyuanConnectionError(LvyuanError):
    """Connection-level error (port open, write, etc.)."""

class LvyuanProtocolError(LvyuanError):
    """Protocol-level error (no response, etc.)."""

class LvyuanCommandError(LvyuanProtocolError):
    """Inverter rejected the command (NAK response)."""