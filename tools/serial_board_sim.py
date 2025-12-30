"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/tools/serial_board_sim.py
DESCRIPTION:
    A Simulator tool that acts like the real PIC boards.
    It runs on PC using virtual COM ports (like com0com).
    Useful for testing the PC Interface [R2.4-1] without hardware.

    Defaults: Board1=COM11, Board2=COM13

AUTHORS:
    1. Yusuf Yaman - 152120221075
    2. Yiğit Ata - 152120221106
================================================================================
"""

import argparse
import threading
import time

import serial

from home_automation.protocol import board1, board2
from home_automation.protocol.common import PAYLOAD_MASK_6BIT, Fixed1dp


def run_board1(port: str, baud: int):
    """
    Simulates Board #1 (Air Conditioner).
    It manages temperature drifting and fan speed logic.
    """
    # Open Serial Port
    ser = serial.Serial(port, baudrate=baud, timeout=0.1)
    
    # Initial State: Desired=25.0, Ambient=24.0, Fan=0
    st = board1.AirState()

    last_drift = time.time()

    while True:
        # --- Simulate Physics ---
        # Slowly move Ambient Temperature towards Desired Temperature
        now = time.time()
        if now - last_drift >= 0.25: 
            last_drift = now

            amb = st.ambient_temp.to_float()
            des = st.desired_temp.to_float()

            # If there is a difference, change ambient temp slightly
            if abs(des - amb) >= 0.05:
                step = 0.1  # Change by 0.1 degrees
                amb = min(des, amb + step) if amb < des else max(des, amb - step)

                # Convert back to Fixed Point format safely
                st.ambient_temp = Fixed1dp.from_float(round(amb, 1))

            # Update Fan Speed logic [R2.1.1-5]
            # If Desired > Ambient (Heating needed), turn fan on
            amb2 = st.ambient_temp.to_float()
            des2 = st.desired_temp.to_float()
            st.fan_speed_rps = 30 if des2 > amb2 else 0

        # --- Handle UART Communication ---
        b = ser.read(1)
        if not b:
            continue
        
        cmd = b[0] & 0xFF

        # Handle GET Commands [R2.1.4-1]
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

        # Handle SET Commands (10xxxxxx and 11xxxxxx)
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            # Set Low Byte (Fraction)
            st.desired_temp.frac_digit = cmd & PAYLOAD_MASK_6BIT

        elif (cmd & 0b1100_0000) == 0b1100_0000:
            # Set High Byte (Integral)
            st.desired_temp.integral = cmd & PAYLOAD_MASK_6BIT

            # Recalculate fan speed immediately after set point change
            amb = st.ambient_temp.to_float()
            des = st.desired_temp.to_float()
            st.fan_speed_rps = 30 if des > amb else 0


def run_board2(port: str, baud: int, light_high_cmd: int):
    """
    Simulates Board #2 (Curtain Control).
    It holds sensor values and responds to requests.
    """
    ser = serial.Serial(port, baudrate=baud, timeout=0.1)
    st = board2.CurtainState()

    # Default Sensor Values
    # Note: These values are raw bytes to fit into 6-bit or 8-bit limits
    st.desired_curtain = Fixed1dp(32, 0)    # Approx 50% open
    st.outdoor_temp = Fixed1dp(20, 0)       # 20.0 C
    st.outdoor_press = Fixed1dp(101, 3)     # 101.3 hPa
    st.light_intensity = Fixed1dp(200, 0)   # 200.0 Lux

    while True:
        b = ser.read(1)
        if not b:
            continue
        
        cmd = b[0] & 0xFF

        # Handle GET Commands [R2.2.6-1]
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

        # Handle SET Commands (For Curtain Position)
        elif (cmd & 0b1100_0000) == 0b1000_0000:
            st.desired_curtain.frac_digit = cmd & PAYLOAD_MASK_6BIT
        elif (cmd & 0b1100_0000) == 0b1100_0000:
            st.desired_curtain.integral = cmd & PAYLOAD_MASK_6BIT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b1", default="COM11", help="Port for Board 1")
    ap.add_argument("--b2", default="COM13", help="Port for Board 2")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--light-high-cmd", type=int, default=board2.GET_LIGHT_INTENSITY_HIGH_DEFAULT)
    args = ap.parse_args()

    # Create threads for each board simulation
    t1 = threading.Thread(target=run_board1, args=(args.b1, args.baud), daemon=True)
    t2 = threading.Thread(target=run_board2, args=(args.b2, args.baud, args.light_high_cmd), daemon=True)

    # Start Board 1 Simulation
    t1.start()
    
    # IMPORTANT: If you are using real hardware (PIC) or PICSimLab for Board 2,
    # keep the following line COMMENTED OUT. Otherwise, both this script and
    # the real board will try to use the same COM port!
    # t2.start()

    print(f"Serial board sim running: Board1={args.b1}, Board2={args.b2}, baud={args.baud}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping simulation...")


if __name__ == "__main__":
    main()