"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/api/air_conditioner.py
DESCRIPTION:
    This file implements the High-Level API for Board #1 (Air Conditioner).
    It defines the class 'AirConditionerSystemConnection' as required by the
    project specifications (UML Diagram).

REQUIREMENTS MET:
    [R2.3-1] API Class Structure (Figure 17 - AirConditionerSystemConnection)
    [R2.3-2] Functions to manage peripherals (set/get temperature, fan speed)

AUTHORS:
    1. Yusuf Yaman 152120221075
    2. Yigit Ata 152120221106
    3. Nihan Cardak 151220212067
    4. Anil Cetin 151220212097
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .common import HomeAutomationSystemConnection
from ..protocol import board1


@dataclass
class AirConditionerSystemConnection:
    """
    [R2.3-1] This class encapsulates the serial communication with Board #1.
    It matches the UML diagram shown in Figure 17 of the project PDF.
    """
    connection: HomeAutomationSystemConnection

    # [R2.3-1] Member variables as defined in UML
    desiredTemperature: float = 0.0
    ambientTemperature: float = 0.0
    fanSpeed: int = 0

    def update(self) -> None:
        """
        [R2.3-1] Updates the member data by communicating with the board.
        It sends GET commands to retrieve current values.
        """
        st = board1.AirState()
        
        def req(cmd: int, retries: int = 5) -> int:
            """
            Helper function to send a command and wait for a response.
            It retries if communication fails.
            """
            for attempt in range(retries):
                self.connection.write(cmd)
                resp = self.connection.read(timeout_s=1.0)
                if resp != -1:
                    return resp
                import time
                time.sleep(0.3)
            return 0  # Default value if failed

        # [R2.1.4-1] Read Desired Temperature (Low and High bytes)
        low = req(board1.GET_DESIRED_TEMP_LOW)
        board1.decode_get_response(board1.GET_DESIRED_TEMP_LOW, low, st)

        high = req(board1.GET_DESIRED_TEMP_HIGH)
        board1.decode_get_response(board1.GET_DESIRED_TEMP_HIGH, high, st)

        # [R2.1.4-1] Read Ambient Temperature (Low and High bytes)
        low = req(board1.GET_AMBIENT_TEMP_LOW)
        board1.decode_get_response(board1.GET_AMBIENT_TEMP_LOW, low, st)

        high = req(board1.GET_AMBIENT_TEMP_HIGH)
        board1.decode_get_response(board1.GET_AMBIENT_TEMP_HIGH, high, st)

        # [R2.1.4-1] Read Fan Speed
        fs = req(board1.GET_FAN_SPEED_RPS)
        board1.decode_get_response(board1.GET_FAN_SPEED_RPS, fs, st)

        # Update local member variables
        self.desiredTemperature = st.desired_temp.to_float()
        self.ambientTemperature = st.ambient_temp.to_float()
        self.fanSpeed = int(st.fan_speed_rps)

    def setDesiredTemp(self, temp: float) -> bool:
        """
        [R2.3-1] Sets the desired temperature by sending a message to the board.
        Target range: 10.0 - 50.0 Celcius.
        """
        try:
            # Encode float into Low/High byte commands
            low_cmd, high_cmd = board1.encode_set_desired_temp(temp)
            
            # [R2.1.4-1] Send SET commands via UART
            self.connection.write(low_cmd)
            self.connection.write(high_cmd)

            # Wait for PIC to process and clear buffers
            import time
            time.sleep(0.2)
            
            # Clear input buffer to remove potential echoes
            if hasattr(self.connection.transport, '_ser') and self.connection.transport._ser:
                ser = self.connection.transport._ser
                ser.reset_input_buffer()
                if ser.in_waiting > 0:
                    ser.read(ser.in_waiting)
                ser.reset_input_buffer()

            # Update local cache immediately
            self.desiredTemperature = round(float(temp), 1)
            return True
        except Exception:
            return False

    def getAmbientTemp(self) -> float:
        """
        [R2.3-1] Get the ambient temperature.
        """
        return float(self.ambientTemperature)

    def getFanSpeed(self) -> int:
        """
        [R2.3-1] Get the fan speed.
        """
        return int(self.fanSpeed)

    def getDesiredTemp(self) -> float:
        """
        [R2.3-1] Get the desired temperature.
        """
        return float(self.desiredTemperature)
