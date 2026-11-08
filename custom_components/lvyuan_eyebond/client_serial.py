"""Serial client for LVYUAN inverters over USB-to-RS232.
Uses plain pyserial with executor-thread reads for async compatibility.
"""
from __future__ import annotations

import asyncio
import logging
import serial

from .client import (
    LvyuanCommandError,
    LvyuanConnectionError,
    LvyuanProtocolError,
)

_LOGGER = logging.getLogger(__name__)


class LvyuanSerialClient:
    """Serial client for LVYUAN inverters using EyeBond G-ASCII protocol."""

    def __init__(
        self,
        device: str,
        baudrate: int = 9600,
        timeout: int = 3,
    ) -> None:
        self._device = device
        self._baudrate = baudrate
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._port: serial.Serial | None = None

    def _ensure_open(self) -> None:
        if self._port is not None and self._port.is_open:
            return
        try:
            self._port = serial.Serial(
                port=self._device,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=float(self._timeout),
                write_timeout=float(self._timeout),
                rtscts=False,
                dsrdtr=False,
            )
            _LOGGER.debug("Serial port %s opened at %s baud", self._device, self._baudrate)
        except (OSError, serial.SerialException) as err:
            self._port = None
            raise LvyuanConnectionError(f"Unable to open serial port {self._device}") from err

    def _drop(self) -> None:
        """Close the serial port immediately and safely."""
        port, self._port = self._port, None
        if port is not None and port.is_open:
            try:
                port.close()
            except Exception:
                pass

    async def close(self) -> None:
        """Close the serial port."""
        async with self._lock:
            if self._port is not None:
                await asyncio.get_running_loop().run_in_executor(None, self._drop)

    async def send_command(
        self,
        command: str,
        *,
        expect_response: bool = True,
        timeout: int | None = None,
    ) -> str:
        """Send an EyeBond G-ASCII command and return the response string."""
        # EyeBond commands are just the command string + \r (no CRC needed)
        frame = f"{command}\r".encode("ascii")
        effective_timeout = timeout or self._timeout

        async with self._lock:
            try:
                await asyncio.get_running_loop().run_in_executor(None, self._ensure_open)
                
                # Clear buffers to avoid reading stale data from previous failed attempts
                if self._port:
                    self._port.reset_input_buffer()
                    self._port.reset_output_buffer()
                    self._port.write(frame)
                    self._port.flush()

                if not expect_response:
                    return "ACK"

                def read_sync() -> bytes:
                    if not self._port:
                        return b""
                    self._port.timeout = float(effective_timeout)
                    # read_until is built into pyserial and is perfect for \r terminated responses
                    return self._port.read_until(b"\r", size=1024)

                raw = await asyncio.get_running_loop().run_in_executor(None, read_sync)
                
                if not raw:
                    raise LvyuanProtocolError(f"No response from inverter for command {command}")

                response = raw.decode("ascii", errors="replace").strip()
                
                if response.upper() in ("NAK", "NOA", "ERCRC"):
                    raise LvyuanCommandError(f"Inverter rejected command {command}: {response}")

                _LOGGER.debug("TX: %s | RX: %s", command, response)
                return response

            except (OSError, serial.SerialException) as err:
                await asyncio.get_running_loop().run_in_executor(None, self._drop)
                raise LvyuanConnectionError(f"Serial failure while sending {command}") from err