"""Board #2 (Perde Kontrol Sistemi) için UART protokol tanımları.

GET ve SET komutlarını encode/decode eder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .common import Fixed1dp, make_set_high, make_set_low


# GET komutları (board'dan veri okuma)
GET_DESIRED_CURTAIN_LOW   = 0x01
GET_DESIRED_CURTAIN_HIGH  = 0x02
GET_OUTDOOR_TEMP_LOW      = 0x03
GET_OUTDOOR_TEMP_HIGH     = 0x04
GET_OUTDOOR_PRESS_LOW     = 0x05
GET_OUTDOOR_PRESS_HIGH    = 0x06
GET_LIGHT_INTENSITY_LOW   = 0x07

# Işık yoğunluğu high byte için varsayılan değer
# (Protokol belirsizliği: 0x08 veya 0x10 olabilir)
GET_LIGHT_INTENSITY_HIGH_DEFAULT = 0x08


# SET komutları (board'a değer yazma)
# Low:  10xxxxxx formatında (kesirli kısım)
# High: 11xxxxxx formatında (tam kısım)

@dataclass
class CurtainState:
    desired_curtain: Fixed1dp = field(default_factory=lambda: Fixed1dp(50, 0))   # percent (approx)
    outdoor_temp: Fixed1dp = field(default_factory=lambda: Fixed1dp(20, 0))      # °C
    outdoor_press: Fixed1dp = field(default_factory=lambda: Fixed1dp(1013, 0))   # hPa
    light_intensity: Fixed1dp = field(default_factory=lambda: Fixed1dp(300, 0))  # Lux



def encode_set_desired_curtain(percent: float, mode: str = "scaled_0_63") -> Tuple[int, int]:
    """Perde açıklık oranını LOW ve HIGH komutlarına dönüştürür.
    
    İki mod desteklenir:
    - 'scaled_0_63' (varsayılan): 0-100% değeri 0-63 aralığına ölçeklenir
    - 'raw_0_63': 0-63 arası ham değer direkt gönderilir
    """
    if mode not in ("raw_0_63", "scaled_0_63"):
        raise ValueError("mode must be 'raw_0_63' or 'scaled_0_63'")

    if mode == "raw_0_63":
        v = round(float(percent), 1)
        if not (0.0 <= v <= 63.0):
            raise ValueError("raw_0_63 mode requires 0.0 <= value <= 63.0")
        fixed = Fixed1dp.from_float(v)
        low_cmd = make_set_low(fixed.frac_digit)
        high_cmd = make_set_high(fixed.integral)
        return low_cmd, high_cmd


    # scaled_0_63 modu: 0-100% değerini 0-63 aralığına ölçekle
    if percent < 0 or percent > 100:
        raise ValueError("Curtain percent must be 0..100 in scaled_0_63 mode")

    # Yüzdeyi 0-63 aralığına çevir (1 ondalık basamağı koruyarak)
    scaled = round((percent / 100.0) * 63.0, 1)
    fixed = Fixed1dp.from_float(scaled)
    low_cmd = make_set_low(fixed.frac_digit)
    high_cmd = make_set_high(fixed.integral)
    return low_cmd, high_cmd


def decode_get_response(cmd: int, data_byte: int, state: CurtainState, *, light_high_cmd: int) -> CurtainState:
    b = int(data_byte) & 0xFF
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
    elif cmd == light_high_cmd:
        state.light_intensity.integral = b
    return state
