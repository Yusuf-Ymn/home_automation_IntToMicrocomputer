"""Simülasyon amaçlı sahte UART transport.

Gerçek donanım olmadan geliştirme ve test yapabilmek için her iki board'ı
bellek içinde simüle eder.

Özellikler:
- GET komutları: Hemen yanıt kuyruğuna ekler
- SET komutları: İç state'ı günceller
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .base import Transport, TransportError
from ..protocol import board1, board2
from ..protocol.common import PAYLOAD_MASK_6BIT, join_1dp


@dataclass
class FakeTransport(Transport):
    """Tek board için sahte transport.
    
    Her board için ayrı FakeTransport instance'ı oluşturulur.
    """

    board: str  # "board1" veya "board2"
    light_high_cmd: int = board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT

    _open: bool = False
    _rx_queue: List[int] = field(default_factory=list)

    # Simüle edilen board state'leri
    air_state: board1.AirState = field(default_factory=board1.AirState)
    curtain_state: board2.CurtainState = field(default_factory=board2.CurtainState)

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False
        self._rx_queue.clear()

    def is_open(self) -> bool:
        return self._open

    def write_byte(self, b: int) -> None:
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
        if not self._open:
            raise TransportError("FakeTransport not open")
        if not self._rx_queue:
            raise TransportError("No data available (fake)")
        return self._rx_queue.pop(0)

    def _handle_board1(self, cmd: int) -> None:
        """Board #1 komutlarını işler (klima sistemi)."""
        """Board #1 komutlarını işler (klima sistemi)."""
        # GET komutlarına yanıt ver
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

        elif (cmd & 0b1100_0000) == 0b1000_0000:
            self.air_state.desired_temp.frac_digit = cmd & PAYLOAD_MASK_6BIT

        elif (cmd & 0b1100_0000) == 0b1100_0000:
            self.air_state.desired_temp.integral = cmd & PAYLOAD_MASK_6BIT

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
        """Board #2 komutlarını işler (perde kontrol sistemi)."""
        cs = self.curtain_state
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

        # SET komutları
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            cs.desired_curtain.frac_digit = cmd & PAYLOAD_MASK_6BIT
        elif (cmd & 0b1100_0000) == 0b1100_0000:
            cs.desired_curtain.integral = cmd & PAYLOAD_MASK_6BIT
        else:
            pass

    def __post_init__(self) -> None:
        """Simülasyon için varsayılan değerleri ayarlar."""
        cs = self.curtain_state

        # Perde: 0-63 aralığında (50% = 32)
        cs.desired_curtain.integral = 32
        cs.desired_curtain.frac_digit = 0

        # Dış sıcaklık: 20.0 C
        cs.outdoor_temp.integral = 20
        cs.outdoor_temp.frac_digit = 0

        # Dış basınç: Tek byte'a sığacak değer (101.3 hPa)
        cs.outdoor_press.integral = 101
        cs.outdoor_press.frac_digit = 3

        # Işık yoğunluğu: 0-255 aralığında (200.0 Lux)
        cs.light_intensity.integral = 200
        cs.light_intensity.frac_digit = 0
