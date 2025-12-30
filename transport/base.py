"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/transport/base.py
DESCRIPTION:
    This file defines the base "Interface" for communication.
    It acts as a template for both Real Serial Port and Fake Simulator classes.
    It ensures that all transport classes have the same standard functions.

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TransportError(RuntimeError):
    """Custom error class for communication problems."""
    pass


class Transport(ABC):
    """
    Abstract Base Class for Transport.
    This class forces other classes (like SerialTransport) to implement
    specific methods like open, close, read, and write.
    """

    @abstractmethod
    def open(self) -> None:
        """Opens the connection."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Closes the connection."""
        ...

    @abstractmethod
    def is_open(self) -> bool:
        """Checks if the connection is currently open."""
        ...

    @abstractmethod
    def write_byte(self, b: int) -> None:
        """Sends a single byte of data."""
        ...

    @abstractmethod
    def read_byte(self, timeout_s: float = 1.0) -> int:
        """
        Reads a single byte of data.
        If no data arrives within 'timeout_s', it raises an error.
        """
        ...