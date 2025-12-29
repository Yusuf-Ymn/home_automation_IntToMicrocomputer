"""PySerial kullanarak gerçek UART iletişimi.

UART konfigürasyonu: 8N1 (8 bit data, No parity, 1 stop bit)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import serial  # type: ignore

from .base import Transport, TransportError


@dataclass
class SerialTransport(Transport):
    port: str
    baudrate: int = 9600

    _ser: Optional[serial.Serial] = None

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
            )
        except Exception as e:
            raise TransportError(f"Failed to open serial port {self.port}: {e}") from e

    def close(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass

    def is_open(self) -> bool:
        return bool(self._ser and self._ser.is_open)

    def write_byte(self, b: int) -> None:
        if not self._ser or not self._ser.is_open:
            raise TransportError("Serial port is not open")
        self._ser.write(bytes([int(b) & 0xFF]))

    def read_byte(self, timeout_s: float = 1.0) -> int:
        if not self._ser or not self._ser.is_open:
            raise TransportError("Serial port is not open")
        # Timeout süresince byte beklenir
        import time
        deadline = time.time() + float(timeout_s)
        while time.time() < deadline:
            data = self._ser.read(1)
            if data:
                return int(data[0])
        raise TransportError(f"Timeout while reading byte from {self.port}")
