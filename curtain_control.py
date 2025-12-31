"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/api/curtain_control.py
DESCRIPTION:
    This file implements the High-Level API for Board #2 (Curtain Control System).
    It defines the class 'CurtainControlSystemConnection' as required by the
    project specifications (UML Diagram).

REQUIREMENTS MET:
    [R2.3-1] API Class Structure (Figure 17 - CurtainControlSystemConnection)
    [R2.2.6-1] UART Requests handling for Board #2 (Get/Set commands)
    [R2.3-2] Functions to manage peripherals (Curtain, LDR, BMP180)

AUTHORS:
    1. Yusuf Yaman 152120221075
    2. Yigit Ata 152120221106
    3. Dogancan Kucuk 151220212099
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .common import HomeAutomationSystemConnection
from ..protocol import board2


@dataclass
class CurtainControlSystemConnection:
    """
    [R2.3-1] This class encapsulates the serial communication with Board #2.
    It matches the UML diagram shown in Figure 17 of the project PDF.
    """
    connection: HomeAutomationSystemConnection

    # [R2.3-1] Member variables as defined in UML
    curtainStatus: float = 0.0
    outdoorTemperature: float = 0.0
    outdoorPressure: float = 0.0
    lightIntensity: float = 0.0

    # Configuration for protocol flexibility (Implementation Detail)
    light_high_cmd: int = board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT
    curtain_set_mode: str = "scaled_0_63"  # Options: "scaled_0_63" or "raw_0_63"

    def update(self) -> None:
        """
        [R2.3-1] Updates the member data by communicating with the board.
        It sends GET commands defined in [R2.2.6-1] to retrieve current values.
        """
        st = board2.CurtainState()

        def req(cmd: int, retries: int = 5) -> int:
            """
            Helper function to send a command and wait for a response.
            It includes retry logic to ensure reliable communication.
            """
            for attempt in range(retries):
                self.connection.write(cmd)
                resp = self.connection.read(timeout_s=1.0)  # Use longer timeout for safety
                if resp != -1:  # Success
                    if attempt > 0:
                        print(f"[DEBUG] CMD=0x{cmd:02X} -> RESP=0x{resp:02X} ({resp}) [attempt {attempt+1}]")
                    return resp
                
                # Timeout occurred, wait and retry
                import time
                time.sleep(0.3)
            
            # All attempts failed
            print(f"[DEBUG] CMD=0x{cmd:02X} -> FAILED after {retries} attempts, returning 0")
            return 0  # Return default value

        # [R2.2.6-1] Read Desired Curtain Status (Low and High bytes)
        low = req(board2.GET_DESIRED_CURTAIN_LOW)
        board2.decode_get_response(board2.GET_DESIRED_CURTAIN_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_DESIRED_CURTAIN_HIGH)
        board2.decode_get_response(board2.GET_DESIRED_CURTAIN_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # [R2.2.6-1] Read Outdoor Temperature (Low and High bytes)
        low = req(board2.GET_OUTDOOR_TEMP_LOW)
        board2.decode_get_response(board2.GET_OUTDOOR_TEMP_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_OUTDOOR_TEMP_HIGH)
        board2.decode_get_response(board2.GET_OUTDOOR_TEMP_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # [R2.2.6-1] Read Outdoor Pressure (Low and High bytes)
        low = req(board2.GET_OUTDOOR_PRESS_LOW)
        board2.decode_get_response(board2.GET_OUTDOOR_PRESS_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_OUTDOOR_PRESS_HIGH)
        board2.decode_get_response(board2.GET_OUTDOOR_PRESS_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # [R2.2.6-1] Read Light Intensity (Low and High bytes)
        low = req(board2.GET_LIGHT_INTENSITY_LOW)
        board2.decode_get_response(board2.GET_LIGHT_INTENSITY_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(self.light_high_cmd)
        board2.decode_get_response(self.light_high_cmd, high, st, light_high_cmd=self.light_high_cmd)

        # Update local member variables based on decoded state
        raw = st.desired_curtain.to_float()
        if self.curtain_set_mode == "scaled_0_63":
            # Scale 0-63 raw value to 0-100%
            self.curtainStatus = round((raw / 63.0) * 100.0, 1)
        else:
            self.curtainStatus = round(raw, 1)

        self.outdoorTemperature = st.outdoor_temp.to_float()
        self.outdoorPressure = st.outdoor_press.to_float()
        self.lightIntensity = st.light_intensity.to_float()

    def setCurtainStatus(self, value: float) -> bool:
        """
        [R2.3-1] Sets the desired curtain openness (0-100%).
        It converts the percentage to the protocol format and sends it via UART.
        """
        try:
            v = float(value)

            # Validate input based on mode
            if self.curtain_set_mode == "scaled_0_63":
                if not (0.0 <= v <= 100.0):
                    raise ValueError("Curtain percent must be 0..100 in scaled_0_63 mode")
            else:  # raw_0_63
                if not (0.0 <= v <= 63.0):
                    raise ValueError("Curtain raw value must be 0..63 in raw_0_63 mode")

            # [R2.2.6-1] Encode value into SET commands
            low_cmd, high_cmd = board2.encode_set_desired_curtain(v, mode=self.curtain_set_mode)
            print(f"[DEBUG SET] Sending LOW=0x{low_cmd:02X}, HIGH=0x{high_cmd:02X}")
            
            # Send SET commands (No response expected)
            self.connection.write(low_cmd)
            self.connection.write(high_cmd)

            # Wait for PIC to process
            import time
            time.sleep(0.2)
            
            # Clear input buffer to prevent reading echoes or old data
            if hasattr(self.connection.transport, '_ser') and self.connection.transport._ser:
                ser = self.connection.transport._ser
                ser.reset_input_buffer()
                if ser.in_waiting > 0:
                    garbage = ser.read(ser.in_waiting)
                    print(f"[DEBUG SET] Cleared {len(garbage)} bytes")
                ser.reset_input_buffer()

            # Update local cache immediately
            self.curtainStatus = round(v, 1)
            return True
        except Exception as e:
            print("setCurtainStatus error:", repr(e))
            return False

    def getOutdoorTemp(self) -> float:
        """
        [R2.3-1] Get the outdoor temperature.
        """
        return float(self.outdoorTemperature)

    def getOutdoorPress(self) -> float:
        """
        [R2.3-1] Get the outdoor pressure.
        """
        return float(self.outdoorPressure)

    def getLightIntensity(self) -> float:
        """
        [R2.3-1] Get the light intensity.
        """
        return float(self.lightIntensity)