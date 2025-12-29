"""Gerçek COM portlarında çalışan board simülatörü.

Com0com gibi sanal COM port araçlarıyla test için kullanılır.
Varsayılan: Board1=COM11, Board2=COM13
"""

import argparse
import threading
import time

import serial

from home_automation.protocol import board1, board2
from home_automation.protocol.common import PAYLOAD_MASK_6BIT, Fixed1dp


def run_board1(port: str, baud: int):
    """Board #1 (klima) simülatörünü çalıştırır."""
    ser = serial.Serial(port, baudrate=baud, timeout=0.1)
    st = board1.AirState()  # default değer: desired=25.0, ambient=24.0, fan=0

    last_drift = time.time()

    while True:
        # Ortam sıcaklığını istenen sıcaklığa doğru yavaşça kaydır
        now = time.time()
        if now - last_drift >= 0.25: 
            last_drift = now

            amb = st.ambient_temp.to_float()
            des = st.desired_temp.to_float()

            if abs(des - amb) >= 0.05:
                step = 0.1  # °C
                amb = min(des, amb + step) if amb < des else max(des, amb - step)

                # Float'u Fixed1dp'ye güvenli dönüşüm
                st.ambient_temp = Fixed1dp.from_float(round(amb, 1))

            # Fan hızını güncelle
            amb2 = st.ambient_temp.to_float()
            des2 = st.desired_temp.to_float()
            st.fan_speed_rps = 30 if des2 > amb2 else 0

        # UART komutlarını işle
        b = ser.read(1)
        if not b:
            continue
        cmd = b[0] & 0xFF

        # GET
        if cmd == board1.GET_DESIRED_TEMP_LOW:
            ser.write(bytes([st.desired_temp.frac_digit & 0xFF]))
        elif cmd == board1.GET_DESIRED_TEMP_HIGH:
            ser.write(bytes([st.desired_temp.integral & 0xFF]))
        elif cmd == board1.GET_AMBIENT_TEMP_LOW:
            ser.write(bytes([st.ambient_temp.frac_digit & 0xFF]))
        elif cmd == board1.GET_AMBIENT_TEMP_HIGH:
            ser.write(bytes([st.ambient_temp.integral & 0xFF]))
        elif cmd == board1.GET_FAN_SPEED_RPS:
            ser.write(bytes([st.fan_speed_rps & 0xFF]))

        # SET komutları (10xxxxxx ve 11xxxxxx prefixleri)
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            # LOW (fraction digit)
            st.desired_temp.frac_digit = cmd & PAYLOAD_MASK_6BIT

        elif (cmd & 0b1100_0000) == 0b1100_0000:
            # HIGH (integral)
            st.desired_temp.integral = cmd & PAYLOAD_MASK_6BIT

            # Yeni setpoint sonrası fan hızını hemen güncelle
            amb = st.ambient_temp.to_float()
            des = st.desired_temp.to_float()
            st.fan_speed_rps = 30 if des > amb else 0


def run_board2(port: str, baud: int, light_high_cmd: int):
    """Board #2 (perde kontrol) simülatörünü çalıştırır."""
    ser = serial.Serial(port, baudrate=baud, timeout=0.1)
    st = board2.CurtainState()

    # Varsayılan değerler (byte sınırları içinde)
    st.desired_curtain = Fixed1dp(32, 0)    # raw 0..63 -> 50.8%
    st.outdoor_temp = Fixed1dp(20, 0)       # 20.0 C
    st.outdoor_press = Fixed1dp(101, 3)     # 101.3 hPa
    st.light_intensity = Fixed1dp(200, 0)   # 200.0 Lux

    while True:
        b = ser.read(1)
        if not b:
            continue
        cmd = b[0] & 0xFF

        # GET
        if cmd == board2.GET_DESIRED_CURTAIN_LOW:
            ser.write(bytes([st.desired_curtain.frac_digit & 0xFF]))
        elif cmd == board2.GET_DESIRED_CURTAIN_HIGH:
            ser.write(bytes([st.desired_curtain.integral & 0xFF]))
        elif cmd == board2.GET_OUTDOOR_TEMP_LOW:
            ser.write(bytes([st.outdoor_temp.frac_digit & 0xFF]))
        elif cmd == board2.GET_OUTDOOR_TEMP_HIGH:
            ser.write(bytes([st.outdoor_temp.integral & 0xFF]))
        elif cmd == board2.GET_OUTDOOR_PRESS_LOW:
            ser.write(bytes([st.outdoor_press.frac_digit & 0xFF]))
        elif cmd == board2.GET_OUTDOOR_PRESS_HIGH:
            ser.write(bytes([st.outdoor_press.integral & 0xFF]))
        elif cmd == board2.GET_LIGHT_INTENSITY_LOW:
            ser.write(bytes([st.light_intensity.frac_digit & 0xFF]))
        elif cmd == light_high_cmd or cmd == board2.GET_LIGHT_INTENSITY_HIGH:
            ser.write(bytes([st.light_intensity.integral & 0xFF]))

        # SET komutları (0-63 aralığında)
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            st.desired_curtain.frac_digit = cmd & PAYLOAD_MASK_6BIT
        elif (cmd & 0b1100_0000) == 0b1100_0000:
            st.desired_curtain.integral = cmd & PAYLOAD_MASK_6BIT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b1", default="COM11")
    ap.add_argument("--b2", default="COM13")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--light-high-cmd", type=int, default=board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT)
    args = ap.parse_args()

    t1 = threading.Thread(target=run_board1, args=(args.b1, args.baud), daemon=True)
    t2 = threading.Thread(target=run_board2, args=(args.b2, args.baud, args.light_high_cmd), daemon=True)



    #BOARD İLE BAŞARILI BAĞLANTI KURULURSA YORUM SATIRINA ALMALISINIZ!
    t1.start()
    #t2.start()

    print(f"Serial board sim running: Board1={args.b1}, Board2={args.b2}, baud={args.baud}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")


if __name__ == "__main__":
    main()
