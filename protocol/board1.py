"""Board #1 (Klima Sistemi) için UART protokol tanımları.

GET ve SET komutlarını encode/decode eder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .common import Fixed1dp, PAYLOAD_MASK_6BIT, make_set_high, make_set_low


# GET komutları (board'dan veri okuma)
GET_DESIRED_TEMP_LOW = 0x01
GET_DESIRED_TEMP_HIGH = 0x02
GET_AMBIENT_TEMP_LOW = 0x03
GET_AMBIENT_TEMP_HIGH = 0x04
GET_FAN_SPEED_RPS = 0x05

# SET komutları (board'a değer yazma)
# Low:  10xxxxxx formatında (kesirli kısım)
# High: 11xxxxxx formatında (tam kısım)

# Document rule (keypad): 10.0 .. 50.0 inclusive, 1 decimal digit
MIN_DESIRED_TEMP_C = 10.0
MAX_DESIRED_TEMP_C = 50.0


@dataclass
class AirState:
    desired_temp: Fixed1dp = field(default_factory=lambda: Fixed1dp(25, 0))
    ambient_temp: Fixed1dp = field(default_factory=lambda: Fixed1dp(24, 0))
    fan_speed_rps: int = 0


def encode_set_desired_temp(temp_c: float) -> Tuple[int, int]:
    """İstenen sıcaklığı LOW ve HIGH komutlarına dönüştürür.
    
    Sıcaklık 10.0-50.0°C aralığında olmalıdır.
    """
    temp_c = round(float(temp_c), 1)

    if not (10.0 <= temp_c <= 50.0):
        raise ValueError("Desired temperature must be between 10.0 and 50.0")

    fixed = Fixed1dp.from_float(temp_c)
    low_cmd = make_set_low(fixed.frac_digit)
    high_cmd = make_set_high(fixed.integral)
    return low_cmd, high_cmd


def decode_get_response(cmd: int, data_byte: int, state: AirState) -> AirState:
    """GET komutu yanıtını parse edip state nesnesini günceller."""
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
        # Fan hızı tam byte olarak gelir (0-255)
        state.fan_speed_rps = b

    return state
