"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/api/common.py
DESCRIPTION:
    This file defines the base connection class for the Home Automation System.
    It manages the transport layer (Serial Port) and provides common functions
    like open, close, and settings configuration.

REQUIREMENTS MET:
    [R2.3-1] Base Class implementation (HomeAutomationSystemConnection)
    [R2.3-1] Common functions: open, close, setComPort, setBaudRate

AUTHORS:
    1. Yusuf Yaman 152120221075
    2. Yigit Ata 152120221106
    3. Dogancan Kucuk 151220212099
    4. Anil Cetin 151220212097
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..transport.base import Transport, TransportError


@dataclass
class HomeAutomationSystemConnection:
    """
    [R2.3-1] Base class for system connections as shown in Figure 17 (UML).
    It encapsulates the Transport object (Serial) and manages connection state.
    """
    transport: Transport
    comPort: str
    baudRate: int
    last_error: Optional[str] = None 

    def open(self) -> bool:
        """
        [R2.3-1] Initiate a connection to the Board via UART port.
        Returns:
            bool: True if connection is successful, False otherwise.
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
        [R2.3-1] Closes the connection to the board.
        Returns:
            bool: True if closed successfully.
        """
        try:
            self.transport.close()
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = repr(e)
            return False

    def is_open(self) -> bool:
        """
        Checks if the physical transport layer is currently open.
        """
        return self.transport.is_open()

    def setComPort(self, port: str) -> None:
        """
        [R2.3-1] Set the communication port number (e.g., COM1, /dev/ttyUSB0).
        """
        self.comPort = port
        if hasattr(self.transport, "port"):
            setattr(self.transport, "port", port)

    def setBaudRate(self, rate: int) -> None:
        """
        [R2.3-1] Set the communication baudrate (e.g., 9600).
        """
        self.baudRate = int(rate)
        if hasattr(self.transport, "baudrate"):
            setattr(self.transport, "baudrate", int(rate))

    def write(self, b: int) -> None:
        """
        Sends a single byte to the hardware.
        Wrapper around the transport layer's write method.
        """
        try:
            self.transport.write_byte(b)
        except TransportError as e:
            self.last_error = str(e)
            raise

    def read(self, timeout_s: float = 1.0) -> int:
        """
        Reads a single byte from the hardware.
        Returns -1 if a timeout occurs.
        """
        try:
            return self.transport.read_byte(timeout_s=timeout_s)
        except TransportError as e:
            self.last_error = str(e)
            return -1  # Return -1 on timeout or error