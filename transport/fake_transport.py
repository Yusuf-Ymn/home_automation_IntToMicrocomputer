"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/transport/fake_transport.py
DESCRIPTION:
    A 'Fake' transport layer for simulation purposes.
    It simulates the behavior of Board #1 and Board #2 in memory.
    This allows testing the PC application without connecting real hardware.

    Features:
    - Responds to GET commands immediately.
    - Updates internal state on SET commands.

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .base import Transport, TransportError
from ..protocol import board1, board2
from ..protocol.common import PAYLOAD_MASK_6BIT, join_1dp


@dataclass
class FakeTransport(Transport):
    """
    Simulates a serial connection to a board.
    Each instance represents one board (either 'board1' or 'board2').
    """

    board: str  # "board1" or "board2"
    light_high_cmd: int = board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT

    _open: bool = False
    _rx_queue: List[int] = field(default_factory=list)

    # Internal state memory for simulation
    air_state: board1.AirState = field(default_factory=board1.AirState)
    curtain_state: board2.CurtainState = field(default_factory=board2.CurtainState)

    def open(self) -> None:
        """Simulates opening the port."""
        self._open = True

    def close(self) -> None:
        """Simulates closing the port."""
        self._open = False
        self._rx_queue.clear()

    def is_open(self) -> bool:
        """Checks if the fake connection is open."""
        return self._open

    def write_byte(self, b: int) -> None:
        """
        Receives a byte from the PC (Simulation of sending data to PIC).
        It processes the command immediately.
        """
        if not self._open:
            raise TransportError("FakeTransport not open")
        
        cmd = int(b) & 0xFF

        if self.board == "board1":
            self._handle_board1(cmd)
        elif self.board == "board2":
            self._handle_board2(cmd)
        else:
            raise TransportError("Unknown board type")

    def read_byte(self, timeout_s: float = 1.0) -> int:
        """
        Sends a byte to the PC (Simulation of receiving data from PIC).
        """
        if not self._open:
            raise TransportError("FakeTransport not open")
        if not self._rx_queue:
            raise TransportError("No data available (fake)")
        
        # Return the first byte from the queue
        return self._rx_queue.pop(0)

    def _handle_board1(self, cmd: int) -> None:
        """
        Processes commands for Board #1 (Air Conditioner).
        Refers to Protocol [R2.1.4-1].
        """
        # --- Handle GET Commands (Read Data) ---
        if cmd == board1.GET_DESIRED_TEMP_LOW:
            self._rx_queue.append(self.air_state.desired_temp.frac_digit & 0xFF)
        elif cmd == board1.GET_DESIRED_TEMP_HIGH:
            self._rx_queue.append(self.air_state.desired_temp.integral & 0xFF)
        elif cmd == board1.GET_AMBIENT_TEMP_LOW:
            self._rx_queue.append(self.air_state.ambient_temp.frac_digit & 0xFF)
        elif cmd == board1.GET_AMBIENT_TEMP_HIGH:
            self._rx_queue.append(self.air_state.ambient_temp.integral & 0xFF)
        elif cmd == board1.GET_FAN_SPEED_RPS:
            self._rx_queue.append(self.air_state.fan_speed_rps & 0xFF)

        # --- Handle SET Commands (Write Data) ---
        # Low Byte (10xxxxxx)
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            self.air_state.desired_temp.frac_digit = cmd & PAYLOAD_MASK_6BIT

        # High Byte (11xxxxxx)
        elif (cmd & 0b1100_0000) == 0b1100_0000:
            self.air_state.desired_temp.integral = cmd & PAYLOAD_MASK_6BIT

            # Update Logic: Turn on fan if heating is needed
            desired = join_1dp(
                self.air_state.desired_temp.integral,
                self.air_state.desired_temp.frac_digit,
            )
            ambient = join_1dp(
                self.air_state.ambient_temp.integral,
                self.air_state.ambient_temp.frac_digit,
            )

            self.air_state.fan_speed_rps = 30 if desired > ambient else 0

    def _handle_board2(self, cmd: int) -> None:
        """
        Processes commands for Board #2 (Curtain Control).
        Refers to Protocol [R2.2.6-1].
        """
        cs = self.curtain_state
        
        # --- Handle GET Commands ---
        if cmd == board2.GET_DESIRED_CURTAIN_LOW:
            self._rx_queue.append(cs.desired_curtain.frac_digit & 0xFF)
        elif cmd == board2.GET_DESIRED_CURTAIN_HIGH:
            self._rx_queue.append(cs.desired_curtain.integral & 0xFF)
        elif cmd == board2.GET_OUTDOOR_TEMP_LOW:
            self._rx_queue.append(cs.outdoor_temp.frac_digit & 0xFF)
        elif cmd == board2.GET_OUTDOOR_TEMP_HIGH:
            self._rx_queue.append(cs.outdoor_temp.integral & 0xFF)
        elif cmd == board2.GET_OUTDOOR_PRESS_LOW:
            self._rx_queue.append(cs.outdoor_press.frac_digit & 0xFF)
        elif cmd == board2.GET_OUTDOOR_PRESS_HIGH:
            self._rx_queue.append(cs.outdoor_press.integral & 0xFF)
        elif cmd == board2.GET_LIGHT_INTENSITY_LOW:
            self._rx_queue.append(cs.light_intensity.frac_digit & 0xFF)
        elif cmd == self.light_high_cmd or cmd == board2.GET_LIGHT_INTENSITY_HIGH:
            self._rx_queue.append(cs.light_intensity.integral & 0xFF)

        # --- Handle SET Commands (Curtain Position) ---
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            cs.desired_curtain.frac_digit = cmd & PAYLOAD_MASK_6BIT
        elif (cmd & 0b1100_0000) == 0b1100_0000:
            cs.desired_curtain.integral = cmd & PAYLOAD_MASK_6BIT
        else:
            pass

    def __post_init__(self) -> None:
        """Sets default values for simulation."""
        cs = self.curtain_state

        # Curtain: 50% approx (Raw value 32 out of 63)
        cs.desired_curtain.integral = 32
        cs.desired_curtain.frac_digit = 0

        # Outdoor Temp: 20.0 C
        cs.outdoor_temp.integral = 20
        cs.outdoor_temp.frac_digit = 0

        # Pressure: 101.3 hPa
        cs.outdoor_press.integral = 101
        cs.outdoor_press.frac_digit = 3

        # Light: 200.0 Lux
        cs.light_intensity.integral = 200
        cs.light_intensity.frac_digit = 0