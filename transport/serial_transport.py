"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/transport/serial_transport.py
DESCRIPTION:
    Real UART Transport implementation using PySerial library.
    It connects to physical COM ports or virtual ports (com0com).
    
    Configuration: 8N1 (8 Data bits, No Parity, 1 Stop bit).

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import time

import serial  # type: ignore

from .base import Transport, TransportError


@dataclass
class SerialTransport(Transport):
    """
    Transport implementation for real Serial Ports.
    It uses the 'serial' library to talk to hardware.
    """
    port: str
    baudrate: int = 9600

    _ser: Optional[serial.Serial] = None

    def open(self) -> None:
        """
        Opens the serial port with standard UART settings (8N1).
        """
        if self._ser and self._ser.is_open:
            return
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,      # 8 Data bits
                parity=serial.PARITY_NONE,      # No Parity
                stopbits=serial.STOPBITS_ONE,   # 1 Stop bit
                timeout=0.1,                    # Non-blocking read with small timeout
            )
        except Exception as e:
            raise TransportError(f"Failed to open serial port {self.port}: {e}") from e

    def close(self) -> None:
        """Closes the serial port if open."""
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass

    def is_open(self) -> bool:
        """Checks if the port is currently active."""
        return bool(self._ser and self._ser.is_open)

    def write_byte(self, b: int) -> None:
        """Sends a single byte over the serial cable."""
        if not self._ser or not self._ser.is_open:
            raise TransportError("Serial port is not open")
        
        # Write the byte (masked to 8-bit safety)
        self._ser.write(bytes([int(b) & 0xFF]))

    def read_byte(self, timeout_s: float = 1.0) -> int:
        """
        Waits for a single byte to arrive.
        If nothing arrives within 'timeout_s', it raises an error.
        """
        if not self._ser or not self._ser.is_open:
            raise TransportError("Serial port is not open")
        
        # Simple loop to wait for data
        deadline = time.time() + float(timeout_s)
        while time.time() < deadline:
            data = self._ser.read(1)
            if data:
                return int(data[0])
        
        raise TransportError(f"Timeout while reading byte from {self.port}")