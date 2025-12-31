"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/transport/serial_transport.py
DESCRIPTION:
    This file implements the real UART communication using the PySerial library.
    It handles the physical connection to the PIC microcontroller via USB-TTL.
    
    Configuration: 9600 Baud, 8 Data bits, No Parity, 1 Stop bit (8N1).

REQUIREMENTS MET:
    [R2.1.4] UART Module (PC Side implementation)
    [R2.3-1] Connection Class implementation (Open/Close logic)
    [R2.3-2] Support for testing API functions via serial

AUTHORS:
    1. Yusuf Yaman 152120221075
    2. Yigit Ata 152120221106 
    3. Nihan Cardak 151220212067
    4. Anil Cetin 151220212097
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import serial  # type: ignore

from .base import Transport, TransportError


@dataclass
class SerialTransport(Transport):
    """
    Real implementation of Transport using PySerial.
    This class manages the actual serial port (COMx or /dev/ttyUSBx).
    """
    port: str
    baudrate: int = 9600

    _ser: Optional[serial.Serial] = None

    def open(self) -> None:
        """
        [R2.3-1] Initiate a connection to the Board via UART port.
        Configures the port with 8N1 settings as required by the project.
        """
        if self._ser and self._ser.is_open:
            return
        try:
            # [R2.1.4] Configure Serial Port: 8N1 Format
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,      # 8 data bits
                parity=serial.PARITY_NONE,      # No parity
                stopbits=serial.STOPBITS_ONE,   # 1 stop bit
                timeout=2.0,                    # Read timeout (2 seconds)
            )
            
            # Clear buffers to remove any old data
            if self._ser:
                import time
                time.sleep(2)  # Wait for PIC/Arduino to reset and stabilize
                
                # Reset buffers multiple times to ensure clean state
                for _ in range(3):
                    self._ser.reset_input_buffer()
                    self._ser.reset_output_buffer()
                    time.sleep(0.1)
                
                # Final flush
                self._ser.flushInput()
                self._ser.flushOutput()
                
        except Exception as e:
            raise TransportError(f"Failed to open serial port {self.port}: {e}") from e

    def close(self) -> None:
        """
        [R2.3-1] Closes the connection to the board.
        Releases the serial port resource.
        """
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass

    def is_open(self) -> bool:
        """
        Checks if the serial connection is currently active.
        """
        return bool(self._ser and self._ser.is_open)

    def write_byte(self, b: int) -> None:
        """
        Sends a single byte to the PIC microcontroller.
        Used for sending commands (e.g., GET/SET requests).
        """
        if not self._ser or not self._ser.is_open:
            raise TransportError("Serial port is not open")
        
        # Clear input buffer before writing to avoid reading our own echo (if any)
        self._ser.reset_input_buffer()
        
        # Write the byte (mask with 0xFF to ensure 8-bit)
        self._ser.write(bytes([int(b) & 0xFF]))
        
        # [Wait] Give PIC some time to process the interrupt
        import time
        time.sleep(0.1)  # 100ms delay for stability

    def read_byte(self, timeout_s: float = 1.0) -> int:
        """
        Receives a single byte from the PIC microcontroller.
        Used for reading sensor data or status codes.
        
        Args:
            timeout_s: Custom timeout for this specific read operation.
        """
        if not self._ser or not self._ser.is_open:
            raise TransportError("Serial port is not open")
        
        # Temporarily change the timeout for this read
        old_timeout = self._ser.timeout
        self._ser.timeout = timeout_s
        
        try:
            # Read exactly 1 byte
            data = self._ser.read(1)
            if data and len(data) == 1:
                return int(data[0])
            else:
                raise TransportError(f"Timeout while reading byte from {self.port}")
        finally:
            # Restore the original timeout setting
            self._ser.timeout = old_timeout