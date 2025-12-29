"""UART protokolü için ortak yardımcı fonksiyonlar.

Sayıları encode/decode etmek için kullanılır:
- Tam kısım ve ondalık kısım ayrı byte'larda saklanır
- SET komutları 6-bit payload kullanır (10xxxxxx ve 11xxxxxx formatı)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


# SET komutları için prefix bitleri
SET_LOW_PREFIX  = 0b10 << 6   # 0x80
SET_HIGH_PREFIX = 0b11 << 6   # 0xC0

PAYLOAD_MASK_6BIT = 0b0011_1111


def split_1dp(value: float) -> Tuple[int, int]:
    """Ondalıklı sayıyı tam ve kesirli kısımlara ayırır.
    
    Örnek: 29.5 -> (29, 5)
    """
    if value < 0:
        raise ValueError("value must be >= 0")

    rounded = round(float(value), 1)
    integral = int(rounded)
    frac_digit = int(round((rounded - integral) * 10))

    # Yuvarlama sonucu 10 olursa, integral'i artır
    if frac_digit == 10:
        integral += 1
        frac_digit = 0

    return integral, frac_digit


def join_1dp(integral: int, frac_digit: int) -> float:
    """Tam ve kesirli kısımları birleştirerek ondalıklı sayı oluşturur."""
    return float(integral) + float(frac_digit) / 10.0


def make_set_low(frac_digit: int) -> int:
    """Kesirli kısım için SET LOW komutu oluşturur (10xxxxxx formatı)."""
    if not (0 <= frac_digit <= 63):
        raise ValueError("frac_digit must be 0..63 for 6-bit payload")
    return SET_LOW_PREFIX | (frac_digit & PAYLOAD_MASK_6BIT)


def make_set_high(integral: int) -> int:
    """Tam kısım için SET HIGH komutu oluşturur (11xxxxxx formatı)."""
    if not (0 <= integral <= 63):
        raise ValueError("integral must be 0..63 for 6-bit payload")
    return SET_HIGH_PREFIX | (integral & PAYLOAD_MASK_6BIT)


@dataclass
class Fixed1dp:
    """1 ondalık basamağa sahip sabit noktayı sayı temsili."""
    integral: int
    frac_digit: int

    @classmethod
    def from_float(cls, value: float) -> "Fixed1dp":
        i, f = split_1dp(value)
        return cls(i, f)

    def to_float(self) -> float:
        return join_1dp(self.integral, self.frac_digit)
