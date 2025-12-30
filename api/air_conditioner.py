"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/api/air_conditioner.py
DESCRIPTION:
    High-level API for the Air Conditioner System (Board #1).
    This class manages the communication logic and keeps track of sensor values.
    
    Refers to Requirement: [R2.3-1] API Class Structure

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .common import HomeAutomationSystemConnection
from ..protocol import board1


@dataclass
class AirConditionerSystemConnection:
    """
    Manages the connection and state of the Air Conditioner System (Board #1).
    Requirement: [R2.3-1]
    """
    connection: HomeAutomationSystemConnection

    # Local cache of the board variables
    desiredTemperature: float = 0.0
    ambientTemperature: float = 0.0
    fanSpeed: int = 0

    def update(self) -> None:
        """
        Reads the latest data from Board #1 via UART.
        It sends GET commands and updates the local variables.
        """
        # Create a temporary state object to hold received bytes
        st = board1.AirState()

        # --- 1. Get Desired Temperature ---
        # Send command for Low Byte (Fractional)
        self.connection.write(board1.GET_DESIRED_TEMP_LOW)
        low = self.connection.read()
        board1.decode_get_response(board1.GET_DESIRED_TEMP_LOW, low, st)

        # Send command for High Byte (Integral)
        self.connection.write(board1.GET_DESIRED_TEMP_HIGH)
        high = self.connection.read()
        board1.decode_get_response(board1.GET_DESIRED_TEMP_HIGH, high, st)

        # --- 2. Get Ambient Temperature ---
        # Send command for Low Byte
        self.connection.write(board1.GET_AMBIENT_TEMP_LOW)
        low = self.connection.read()
        board1.decode_get_response(board1.GET_AMBIENT_TEMP_LOW, low, st)

        # Send command for High Byte
        self.connection.write(board1.GET_AMBIENT_TEMP_HIGH)
        high = self.connection.read()
        board1.decode_get_response(board1.GET_AMBIENT_TEMP_HIGH, high, st)

        # --- 3. Get Fan Speed ---
        self.connection.write(board1.GET_FAN_SPEED_RPS)
        fs = self.connection.read()
        board1.decode_get_response(board1.GET_FAN_SPEED_RPS, fs, st)

        # Update class members with the decoded values
        self.desiredTemperature = st.desired_temp.to_float()
        self.ambientTemperature = st.ambient_temp.to_float()
        self.fanSpeed = int(st.fan_speed_rps)

    def setDesiredTemp(self, temp: float) -> bool:
        """
        Sets the desired temperature on Board #1.
        The value must be between 10.0 and 50.0 degrees [R2.1.2-3].
        
        Args:
            temp: New temperature value (e.g. 24.5)
            
        Returns:
            True if successful, False if invalid or error.
        """
        try:
            # Convert float to UART command bytes
            low_cmd, high_cmd = board1.encode_set_desired_temp(temp)
            
            # Send commands to the board
            self.connection.write(low_cmd)
            self.connection.write(high_cmd)

            # Update local cache immediately
            self.desiredTemperature = round(float(temp), 1)
            return True
        except Exception:
            return False

    def getAmbientTemp(self) -> float:
        """Returns the last read ambient temperature."""
        return float(self.ambientTemperature)

    def getFanSpeed(self) -> int:
        """Returns the last read fan speed."""
        return int(self.fanSpeed)

    def getDesiredTemp(self) -> float:
        """Returns the last read desired temperature."""
        return float(self.desiredTemperature)