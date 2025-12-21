"""Klima sistemi (Board #1) için yüksek seviye API.

Bu modül klimayı kontrol etmek için basit fonksiyonlar sağlar:
- Sıcaklık okuma ve ayarlama
- Fan hızını kontrol etme
- Ortam sıcaklığını ölçme
"""

from __future__ import annotations

from dataclasses import dataclass

from .common import HomeAutomationSystemConnection
from ..protocol import board1


@dataclass
class AirConditionerSystemConnection:
    connection: HomeAutomationSystemConnection

    desiredTemperature: float = 0.0
    ambientTemperature: float = 0.0
    fanSpeed: int = 0

    def update(self) -> None:
        """Board'dan güncel verileri okur (sıcaklık, fan hızı vb.)"""
        st = board1.AirState()

        # İstenen sıcaklığı oku
        self.connection.write(board1.GET_DESIRED_TEMP_LOW)
        low = self.connection.read()
        board1.decode_get_response(board1.GET_DESIRED_TEMP_LOW, low, st)

        self.connection.write(board1.GET_DESIRED_TEMP_HIGH)
        high = self.connection.read()
        board1.decode_get_response(board1.GET_DESIRED_TEMP_HIGH, high, st)

        # Ortam sıcaklığını oku
        self.connection.write(board1.GET_AMBIENT_TEMP_LOW)
        low = self.connection.read()
        board1.decode_get_response(board1.GET_AMBIENT_TEMP_LOW, low, st)

        self.connection.write(board1.GET_AMBIENT_TEMP_HIGH)
        high = self.connection.read()
        board1.decode_get_response(board1.GET_AMBIENT_TEMP_HIGH, high, st)

        # Fan hızını oku
        self.connection.write(board1.GET_FAN_SPEED_RPS)
        fs = self.connection.read()
        board1.decode_get_response(board1.GET_FAN_SPEED_RPS, fs, st)

        self.desiredTemperature = st.desired_temp.to_float()
        self.ambientTemperature = st.ambient_temp.to_float()
        self.fanSpeed = int(st.fan_speed_rps)

    def setDesiredTemp(self, temp: float) -> bool:
        """İstenen sıcaklığı ayarlar (10.0-50.0°C arası)."""
        try:
            low_cmd, high_cmd = board1.encode_set_desired_temp(temp)
            self.connection.write(low_cmd)
            self.connection.write(high_cmd)

            # Değeri hemen local cache'e kaydet
            self.desiredTemperature = round(float(temp), 1)
            return True
        except Exception:
            return False

    def getAmbientTemp(self) -> float:
        return float(self.ambientTemperature)

    def getFanSpeed(self) -> int:
        return int(self.fanSpeed)

    def getDesiredTemp(self) -> float:
        return float(self.desiredTemperature)
