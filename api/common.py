"""Tüm board'lar için ortak bağlantı sınıfı.

Seri port bağlantısını yönetir ve temel okuma/yazma işlemlerini sağlar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..transport.base import Transport, TransportError


from dataclasses import dataclass
from typing import Optional

from ..transport.base import Transport, TransportError


@dataclass
class HomeAutomationSystemConnection:
    transport: Transport
    comPort: str
    baudRate: int
    last_error: Optional[str] = None 

    def open(self) -> bool:
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
        try:
            self.transport.close()
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = repr(e)
            return False


    def is_open(self) -> bool:
        return self.transport.is_open()

    def setComPort(self, port: str) -> None:
        self.comPort = port
        if hasattr(self.transport, "port"):
            setattr(self.transport, "port", port)

    def setBaudRate(self, rate: int) -> None:
        self.baudRate = int(rate)
        if hasattr(self.transport, "baudrate"):
            setattr(self.transport, "baudrate", int(rate))


    def write(self, b: int) -> None:
        self.transport.write_byte(b)

    def read(self, timeout_s: float = 1.0) -> int:
        return self.transport.read_byte(timeout_s=timeout_s)
