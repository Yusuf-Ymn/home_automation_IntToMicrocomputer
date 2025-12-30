"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/api/curtain_control.py
DESCRIPTION:
    High-level API for the Curtain Control System (Board #2).
    This class manages the communication logic, sensor reading, and curtain setting.
    
    Refers to Requirement: [R2.3-1] API Class Structure

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .common import HomeAutomationSystemConnection
from ..protocol import board2


@dataclass
class CurtainControlSystemConnection:
    """
    Manages the connection and state of the Curtain Control System (Board #2).
    Requirement: [R2.3-1]
    """
    connection: HomeAutomationSystemConnection

    # Local cache of the board variables
    curtainStatus: float = 0.0
    outdoorTemperature: float = 0.0
    outdoorPressure: float = 0.0
    lightIntensity: float = 0.0

    # Configuration for protocol flexibility
    light_high_cmd: int = board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT
    curtain_set_mode: str = "scaled_0_63"  # "scaled_0_63" or "raw_0_63"

    def update(self) -> None:
        """
        Reads the latest data from Board #2 via UART.
        It sends GET commands and updates the local variables.
        """
        st = board2.CurtainState()

        # Helper function to send command and read 1 byte response
        def req(cmd: int) -> int:
            self.connection.write(cmd)
            return self.connection.read()

        # --- 1. Get Curtain Position ---
        low = req(board2.GET_DESIRED_CURTAIN_LOW)
        board2.decode_get_response(board2.GET_DESIRED_CURTAIN_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_DESIRED_CURTAIN_HIGH)
        board2.decode_get_response(board2.GET_DESIRED_CURTAIN_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # --- 2. Get Outdoor Temperature ---
        low = req(board2.GET_OUTDOOR_TEMP_LOW)
        board2.decode_get_response(board2.GET_OUTDOOR_TEMP_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_OUTDOOR_TEMP_HIGH)
        board2.decode_get_response(board2.GET_OUTDOOR_TEMP_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # --- 3. Get Outdoor Pressure ---
        low = req(board2.GET_OUTDOOR_PRESS_LOW)
        board2.decode_get_response(board2.GET_OUTDOOR_PRESS_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_OUTDOOR_PRESS_HIGH)
        board2.decode_get_response(board2.GET_OUTDOOR_PRESS_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # --- 4. Get Light Intensity ---
        low = req(board2.GET_LIGHT_INTENSITY_LOW)
        board2.decode_get_response(board2.GET_LIGHT_INTENSITY_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(self.light_high_cmd)
        board2.decode_get_response(self.light_high_cmd, high, st, light_high_cmd=self.light_high_cmd)

        # --- Update Local Cache ---
        raw = st.desired_curtain.to_float()
        
        # Convert raw PIC value (0-63) back to Percentage (0-100) if needed
        if self.curtain_set_mode == "scaled_0_63":
            self.curtainStatus = round((raw / 63.0) * 100.0, 1)
        else:
            self.curtainStatus = round(raw, 1)

        self.outdoorTemperature = st.outdoor_temp.to_float()
        self.outdoorPressure = st.outdoor_press.to_float()
        self.lightIntensity = st.light_intensity.to_float()

    def setCurtainStatus(self, value: float) -> bool:
        """
        Sets the desired curtain position on Board #2.
        
        Args:
            value: Target position (0-100% usually).
            
        Returns:
            True if successful, False if error.
        """
        try:
            v = float(value)

            # Validate input range based on mode
            if self.curtain_set_mode == "scaled_0_63":
                if not (0.0 <= v <= 100.0):
                    raise ValueError("Curtain percent must be 0..100 in scaled_0_63 mode")
            else:  # raw_0_63
                if not (0.0 <= v <= 63.0):
                    raise ValueError("Curtain raw value must be 0..63 in raw_0_63 mode")

            # Convert to UART commands
            low_cmd, high_cmd = board2.encode_set_desired_curtain(v, mode=self.curtain_set_mode)
            
            # Send commands
            self.connection.write(low_cmd)
            self.connection.write(high_cmd)

            # Update local cache immediately
            self.curtainStatus = round(v, 1)
            return True
        except Exception as e:
            # In a real app, logging would be better than print
            print("setCurtainStatus error:", repr(e))
            return False

    def getOutdoorTemp(self) -> float:
        """Returns the last read outdoor temperature."""
        return float(self.outdoorTemperature)

    def getOutdoorPress(self) -> float:
        """Returns the last read outdoor pressure."""
        return float(self.outdoorPressure)

    def getLightIntensity(self) -> float:
        """Returns the last read light intensity."""
        return float(self.lightIntensity)