"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/protocol/board1.py
DESCRIPTION:
    This file defines the UART communication protocol for Board #1 
    (Air Conditioner System). It helps to send and receive data 
    according to the project rules.

    Reference Requirement: [R2.1.4-1] UART Module Command Set

AUTHOR:
    1. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .common import Fixed1dp, PAYLOAD_MASK_6BIT, make_set_high, make_set_low


# ------------------------------------------------------------------------------
# UART COMMAND DEFINITIONS [R2.1.4-1]
# These values match the table given in Requirement [R2.1.4-1].
# ------------------------------------------------------------------------------

# Command to get fractional part of desired temperature (0x01)
GET_DESIRED_TEMP_LOW = 0x01

# Command to get integral part of desired temperature (0x02)
GET_DESIRED_TEMP_HIGH = 0x02

# Command to get fractional part of ambient temperature (0x03)
GET_AMBIENT_TEMP_LOW = 0x03

# Command to get integral part of ambient temperature (0x04)
GET_AMBIENT_TEMP_HIGH = 0x04

# Command to get fan speed (0x05)
GET_FAN_SPEED_RPS = 0x05

# ------------------------------------------------------------------------------
# SET COMMAND CONSTANTS
# The protocol uses 6-bit payload for SET commands.
# Low Byte format:  10xxxxxx
# High Byte format: 11xxxxxx
# ------------------------------------------------------------------------------

# Temperature limits defined in requirements [R2.1.2-3]
MIN_DESIRED_TEMP_C = 10.0
MAX_DESIRED_TEMP_C = 50.0


@dataclass
class AirState:
    """
    Holds the current state of Board #1 variables.
    """
    # [R2.1.1-1] Desired temperature value
    desired_temp: Fixed1dp = field(default_factory=lambda: Fixed1dp(25, 0))
    
    # [R2.1.1-4] Ambient temperature value
    ambient_temp: Fixed1dp = field(default_factory=lambda: Fixed1dp(24, 0))
    
    # [R2.1.1-5] Fan speed in rps
    fan_speed_rps: int = 0


def encode_set_desired_temp(temp_c: float) -> Tuple[int, int]:
    """
    Prepares the UART commands to set the desired temperature.
    
    It checks if the temperature is valid (10-50 C) as per [R2.1.2-3].
    Then it converts the value into Low and High command bytes.
    
    Args:
        temp_c: The desired temperature (e.g. 24.5)
        
    Returns:
        Tuple (low_command, high_command)
    """
    temp_c = round(float(temp_c), 1)

    # Check validity [R2.1.2-3]
    if not (10.0 <= temp_c <= 50.0):
        raise ValueError("Desired temperature must be between 10.0 and 50.0")

    fixed = Fixed1dp.from_float(temp_c)
    
    # Create the command bytes using helper functions
    low_cmd = make_set_low(fixed.frac_digit)
    high_cmd = make_set_high(fixed.integral)
    
    return low_cmd, high_cmd


def decode_get_response(cmd: int, data_byte: int, state: AirState) -> AirState:
    """
    Updates the state object with data received from Board #1.
    Matches the command ID with the correct variable.
    """
    b = int(data_byte) & 0xFF

    if cmd == GET_DESIRED_TEMP_LOW:
        state.desired_temp.frac_digit = b & PAYLOAD_MASK_6BIT
    elif cmd == GET_DESIRED_TEMP_HIGH:
        state.desired_temp.integral = b & PAYLOAD_MASK_6BIT
        
    elif cmd == GET_AMBIENT_TEMP_LOW:
        state.ambient_temp.frac_digit = b & PAYLOAD_MASK_6BIT
    elif cmd == GET_AMBIENT_TEMP_HIGH:
        state.ambient_temp.integral = b & PAYLOAD_MASK_6BIT
        
    elif cmd == GET_FAN_SPEED_RPS:
        state.fan_speed_rps = b

    return state