"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/protocol/board2.py
DESCRIPTION:
    This file defines the UART communication protocol for Board #2 (Curtain System).
    It includes command definitions and helper functions to encode/decode data
    according to the requirements defined in the project documentation.

    Reference Requirement: [R2.2.6-1] UART Module Command Set

AUTHOR:
    1. Yusuf Yaman - 152120221075
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .common import Fixed1dp, make_set_high, make_set_low


# ------------------------------------------------------------------------------
# UART COMMAND DEFINITIONS [R2.2.6-1]
# These values correspond to the "Message received by Module" column in the
# protocol table defined in Requirement [R2.2.6-1].
# ------------------------------------------------------------------------------

# 00000001B: Get desired curtain status low byte (fractional part)
GET_DESIRED_CURTAIN_LOW   = 0x01

# 00000010B: Get desired curtain status high byte (integral part)
GET_DESIRED_CURTAIN_HIGH  = 0x02

# 00000011B: Get outdoor temperature low byte (fractional part)
GET_OUTDOOR_TEMP_LOW      = 0x03

# 00000100B: Get outdoor temperature high byte (integral part)
GET_OUTDOOR_TEMP_HIGH     = 0x04

# 00000101B: Get outdoor pressure low byte (fractional part)
GET_OUTDOOR_PRESS_LOW     = 0x05

# 00000110B: Get outdoor pressure high byte (integral part)
GET_OUTDOOR_PRESS_HIGH    = 0x06

# 00000111B: Get light intensity low byte (fractional part)
GET_LIGHT_INTENSITY_LOW   = 0x07

# 00001000B: Get light intensity high byte (integral part)
GET_LIGHT_INTENSITY_HIGH  = 0x08

# Default high byte command for light intensity
GET_LIGHT_INTENSITY_HIGH_DEFAULT = 0x08


# ------------------------------------------------------------------------------
# SET COMMAND DEFINITIONS [R2.2.6-1]
# The protocol defines SET commands using specific bit patterns:
# - Low Byte (Fractional): 10xxxxxx
# - High Byte (Integral):  11xxxxxx
# These are handled dynamically in the encode functions.
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# DATA STRUCTURES
# ------------------------------------------------------------------------------
@dataclass
class CurtainState:
    """
    Holds the current state of Board #2 sensors and actuators.
    All values are stored as Fixed Point numbers (Integer + Fraction) to match
    the split-byte protocol structure.
    """
    # [R2.2.1-1] The desired curtain status (in percent).
    desired_curtain: Fixed1dp = field(default_factory=lambda: Fixed1dp(50, 0))   # %

    # [R2.2.3-1] The outdoor temperature.
    outdoor_temp: Fixed1dp = field(default_factory=lambda: Fixed1dp(20, 0))      # C

    # [R2.2.3-2] The outdoor air pressure.
    outdoor_press: Fixed1dp = field(default_factory=lambda: Fixed1dp(1013, 0))   # hPa

    # [R2.2.2-1] The current light intensity.
    light_intensity: Fixed1dp = field(default_factory=lambda: Fixed1dp(300, 0))  # Lux


# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def encode_set_desired_curtain(percent: float, mode: str = "scaled_0_63") -> Tuple[int, int]:
    """
    Prepares the UART commands to set the desired curtain status.
    This function implements the SET command generation defined in [R2.2.6-1].

    Format:
        Low Byte:  10xxxxxx (Binary)
        High Byte: 11xxxxxx (Binary)

    Args:
        percent: The target curtain status (0-100%).
        mode:
            - 'scaled_0_63' (default): Maps 0-100% range to 0-63 range for the PIC logic.
            - 'raw_0_63': Sends the raw value directly (useful for testing).

    Returns:
        Tuple (low_command_byte, high_command_byte) to be sent over serial.
    """
    if mode not in ("raw_0_63", "scaled_0_63"):
        raise ValueError("mode must be 'raw_0_63' or 'scaled_0_63'")

    if mode == "raw_0_63":
        # Direct raw value mode (for debugging specific PIC values)
        v = round(float(percent), 1)
        if not (0.0 <= v <= 63.0):
            raise ValueError("raw_0_63 mode requires 0.0 <= value <= 63.0")
        fixed = Fixed1dp.from_float(v)
        
        # Create command bytes: 10xxxxxx (Low) and 11xxxxxx (High)
        low_cmd = make_set_low(fixed.frac_digit)
        high_cmd = make_set_high(fixed.integral)
        return low_cmd, high_cmd


    # scaled_0_63 mode: Normal Operation
    # Scale the percentage (0-100) to the PIC's internal range (0-63)
    if percent < 0 or percent > 100:
        raise ValueError("Curtain percent must be 0..100 in scaled_0_63 mode")

    # Mapping Formula: (Percent / 100.0) * 63.0
    # This maintains the 1 decimal place precision used in Fixed1dp.
    scaled = round((percent / 100.0) * 63.0, 1)
    
    fixed = Fixed1dp.from_float(scaled)
    
    # Generate the actual command bytes as per protocol [R2.2.6-1]
    low_cmd = make_set_low(fixed.frac_digit)
    high_cmd = make_set_high(fixed.integral)
    
    return low_cmd, high_cmd


def decode_get_response(cmd: int, data_byte: int, state: CurtainState, *, light_high_cmd: int) -> CurtainState:
    """
    Updates the state object based on data received from Board #2.
    It matches the received command ID with the corresponding variable in CurtainState
    and updates either the integral or fractional part.

    Args:
        cmd: The command byte sent to the board (e.g., GET_DESIRED_CURTAIN_LOW).
        data_byte: The data byte received from the board in response.
        state: The current CurtainState object to update.
        light_high_cmd: The specific command used for high byte of light (context dependent).

    Returns:
        The updated CurtainState object.
    """
    b = int(data_byte) & 0xFF  # Ensure byte is treated as unsigned
    
    if cmd == GET_DESIRED_CURTAIN_LOW:
        state.desired_curtain.frac_digit = b
    elif cmd == GET_DESIRED_CURTAIN_HIGH:
        state.desired_curtain.integral = b
        
    elif cmd == GET_OUTDOOR_TEMP_LOW:
        state.outdoor_temp.frac_digit = b
    elif cmd == GET_OUTDOOR_TEMP_HIGH:
        state.outdoor_temp.integral = b
        
    elif cmd == GET_OUTDOOR_PRESS_LOW:
        state.outdoor_press.frac_digit = b
    elif cmd == GET_OUTDOOR_PRESS_HIGH:
        state.outdoor_press.integral = b
        
    elif cmd == GET_LIGHT_INTENSITY_LOW:
        state.light_intensity.frac_digit = b
    elif cmd == light_high_cmd or cmd == GET_LIGHT_INTENSITY_HIGH:
        # Some implementations might use a dynamic command for light high byte
        state.light_intensity.integral = b
        
    return state