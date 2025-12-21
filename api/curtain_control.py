"""Perde kontrol sistemi (Board #2) için yüksek seviye API.

Bu modül perdeleri kontrol etmek için basit fonksiyonlar sağlar:
- Perde açıklık oranını ayarlama
- Dış ortam verilerini okuma (sıcaklık, basınç, ışık)
"""

from __future__ import annotations

from dataclasses import dataclass

from .common import HomeAutomationSystemConnection
from ..protocol import board2


@dataclass
class CurtainControlSystemConnection:
    connection: HomeAutomationSystemConnection

    curtainStatus: float = 0.0
    outdoorTemperature: float = 0.0
    outdoorPressure: float = 0.0
    lightIntensity: float = 0.0

    # Protokol belirsizliği için ayarlanabilir parametreler
    light_high_cmd: int = board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT
    curtain_set_mode: str = "scaled_0_63"  # "scaled_0_63" or "raw_0_63"

    def update(self) -> None:
        """Board'dan güncel verileri okur (perde durumu, dış ortam verileri vb.)"""
        st = board2.CurtainState()

        def req(cmd: int) -> int:
            self.connection.write(cmd)
            return self.connection.read()

        # Perde pozisyonunu oku
        low = req(board2.GET_DESIRED_CURTAIN_LOW)
        board2.decode_get_response(board2.GET_DESIRED_CURTAIN_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_DESIRED_CURTAIN_HIGH)
        board2.decode_get_response(board2.GET_DESIRED_CURTAIN_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # Dış sıcaklığı oku
        low = req(board2.GET_OUTDOOR_TEMP_LOW)
        board2.decode_get_response(board2.GET_OUTDOOR_TEMP_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_OUTDOOR_TEMP_HIGH)
        board2.decode_get_response(board2.GET_OUTDOOR_TEMP_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # Dış basıncı oku
        low = req(board2.GET_OUTDOOR_PRESS_LOW)
        board2.decode_get_response(board2.GET_OUTDOOR_PRESS_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(board2.GET_OUTDOOR_PRESS_HIGH)
        board2.decode_get_response(board2.GET_OUTDOOR_PRESS_HIGH, high, st, light_high_cmd=self.light_high_cmd)

        # Işık yoğunluğunu oku
        low = req(board2.GET_LIGHT_INTENSITY_LOW)
        board2.decode_get_response(board2.GET_LIGHT_INTENSITY_LOW, low, st, light_high_cmd=self.light_high_cmd)

        high = req(self.light_high_cmd)
        board2.decode_get_response(self.light_high_cmd, high, st, light_high_cmd=self.light_high_cmd)

        # Okunan değerleri kaydet
        raw = st.desired_curtain.to_float()
        if self.curtain_set_mode == "scaled_0_63":
            self.curtainStatus = round((raw / 63.0) * 100.0, 1)
        else:
            self.curtainStatus = round(raw, 1)

        self.outdoorTemperature = st.outdoor_temp.to_float()
        self.outdoorPressure = st.outdoor_press.to_float()
        self.lightIntensity = st.light_intensity.to_float()

    def setCurtainStatus(self, value: float) -> bool:
        """Perde açıklık oranını ayarlar (0-100% arası)."""
        try:
            v = float(value)

            # Geçerli değer aralığını kontrol et
            if self.curtain_set_mode == "scaled_0_63":
                if not (0.0 <= v <= 100.0):
                    raise ValueError("Curtain percent must be 0..100 in scaled_0_63 mode")
            else:  # raw_0_63
                if not (0.0 <= v <= 63.0):
                    raise ValueError("Curtain raw value must be 0..63 in raw_0_63 mode")

            low_cmd, high_cmd = board2.encode_set_desired_curtain(v, mode=self.curtain_set_mode)
            self.connection.write(low_cmd)
            self.connection.write(high_cmd)

            self.curtainStatus = round(v, 1)
            return True
        except Exception as e:
            print("setCurtainStatus error:", repr(e))
            return False

    def getOutdoorTemp(self) -> float:
        return float(self.outdoorTemperature)

    def getOutdoorPress(self) -> float:
        return float(self.outdoorPressure)

    def getLightIntensity(self) -> float:
        return float(self.lightIntensity)
