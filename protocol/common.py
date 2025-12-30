"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/protocol/common.py
DESCRIPTION:
    This file contains common helper functions and data structures used 
    by the UART protocols. It handles splitting numbers into integer 
    and fractional parts, and formatting bits for SET commands.

    Reference: 
    - [R2.1.4-1] Set command bit format (Board 1)
    - [R2.2.6-1] Set command bit format (Board 2)

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


# ------------------------------------------------------------------------------
# BIT MASKS FOR COMMANDS
# The project requires specific bit patterns for SET commands.
# Low Byte starts with '10' -> 10xxxxxx (0x80)
# High Byte starts with '11' -> 11xxxxxx (0xC0)
# ------------------------------------------------------------------------------

SET_LOW_PREFIX  = 0b10 << 6   # 0x80
SET_HIGH_PREFIX = 0b11 << 6   # 0xC0

# We use the lower 6 bits for data (0-63)
PAYLOAD_MASK_6BIT = 0b0011_1111


def split_1dp(value: float) -> Tuple[int, int]:
    """
    Splits a float number into its integer and fractional parts.
    Example: 29.5 -> returns (29, 5)
    
    Args:
        value: The number to split.
        
    Returns:
        Tuple (Integer Part, Fractional Part)
    """
    if value < 0:
        raise ValueError("value must be >= 0")

    # Round to 1 decimal place to avoid errors
    rounded = round(float(value), 1)
    
    # Get the integer part
    integral = int(rounded)
    
    # Get the first decimal digit: (29.5 - 29) * 10 = 0.5 * 10 = 5
    frac_digit = int(round((rounded - integral) * 10))

    # Fix edge case: if rounding makes frac 10, increment integer
    if frac_digit == 10:
        integral += 1
        frac_digit = 0

    return integral, frac_digit


def join_1dp(integral: int, frac_digit: int) -> float:
    """
    Combines integer and fractional parts back into a float.
    Example: (29, 5) -> returns 29.5
    """
    return float(integral) + float(frac_digit) / 10.0


def make_set_low(frac_digit: int) -> int:
    """
    Creates the 'Set Low Byte' command.
    It combines the prefix (10) with the data bits.
    
    Format: 10xxxxxx
    """
    # Data must fit in 6 bits (0-63)
    if not (0 <= frac_digit <= 63):
        raise ValueError("frac_digit must be 0..63 for 6-bit payload")
    
    # Combine prefix and data using OR operation
    return SET_LOW_PREFIX | (frac_digit & PAYLOAD_MASK_6BIT)


def make_set_high(integral: int) -> int:
    """
    Creates the 'Set High Byte' command.
    It combines the prefix (11) with the data bits.
    
    Format: 11xxxxxx
    """
    # Data must fit in 6 bits (0-63)
    if not (0 <= integral <= 63):
        raise ValueError("integral must be 0..63 for 6-bit payload")
    
    # Combine prefix and data using OR operation
    return SET_HIGH_PREFIX | (integral & PAYLOAD_MASK_6BIT)


@dataclass
class Fixed1dp:
    """
    A simple class to store the number in two parts:
    - integral: The main number (e.g. 24)
    - frac_digit: The decimal part (e.g. 5)
    
    This is used because we send these parts separately.
    """
    integral: int
    frac_digit: int

    @classmethod
    def from_float(cls, value: float) -> "Fixed1dp":
        """Helper to create object from a float."""
        i, f = split_1dp(value)
        return cls(i, f)

    def to_float(self) -> float:
        """Helper to get back the float value."""
        return join_1dp(self.integral, self.frac_digit)