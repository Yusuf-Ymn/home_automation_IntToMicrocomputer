"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/api/common.py
DESCRIPTION:
    Common connection class used by all boards (Air Conditioner & Curtain).
    It manages the serial port connection and provides basic read/write operations.
    
    Refers to Requirement: [R2.3-1] API Class Structure (Shared Logic)

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..transport.base import Transport, TransportError


@dataclass
class HomeAutomationSystemConnection:
    """
    A wrapper class for the transport layer.
    It keeps track of the port settings and error states.
    """
    transport: Transport
    comPort: str
    baudRate: int
    last_error: Optional[str] = None 

    def open(self) -> bool:
        """
        Tries to open the serial connection.
        Returns: True if successful, False if it fails.
        """
        try:
            self.transport.open()
            self.last_error = None
            return True
        except TransportError as e:
            self.last_error = str(e)
            return False
        except Exception as e:
            self.last_error = repr(e)
            return False

    def close(self) -> bool:
        """
        Closes the connection safely.
        """
        try:
            self.transport.close()
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = repr(e)
            return False


    def is_open(self) -> bool:
        """Checks if the connection is currently active."""
        return self.transport.is_open()

    def setComPort(self, port: str) -> None:
        """Updates the COM port configuration (e.g. COM3)."""
        self.comPort = port
        # If the transport object supports changing ports, update it.
        if hasattr(self.transport, "port"):
            setattr(self.transport, "port", port)

    def setBaudRate(self, rate: int) -> None:
        """Updates the communication speed (e.g. 9600)."""
        self.baudRate = int(rate)
        if hasattr(self.transport, "baudrate"):
            setattr(self.transport, "baudrate", int(rate))


    def write(self, b: int) -> None:
        """Sends a single byte of data to the board."""
        self.transport.write_byte(b)

    def read(self, timeout_s: float = 1.0) -> int:
        """
        Reads a single byte from the board.
        Waits up to 'timeout_s' seconds.
        """
        return self.transport.read_byte(timeout_s=timeout_s)