"""UART iletişimi için temel transport arayüzü.

Fake ve gerçek seri port implementasyonları bu interface'i kullanır.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TransportError(RuntimeError):
    pass


class Transport(ABC):
    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def is_open(self) -> bool:
        ...

    @abstractmethod
    def write_byte(self, b: int) -> None:
        ...

    @abstractmethod
    def read_byte(self, timeout_s: float = 1.0) -> int:
        ...
