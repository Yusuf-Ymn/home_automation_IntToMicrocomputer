"""Konsol tabanlı ev otomasyon kontrol programı.

Kullanım:
- Simülasyon modu:  python -m home_automation.app.console --fake
- Gerçek mod:       python -m home_automation.app.console --port1 COM3 --port2 COM5 --baud 9600
"""

from __future__ import annotations

import argparse

from ..api import (
    HomeAutomationSystemConnection,
    AirConditionerSystemConnection,
    CurtainControlSystemConnection,
)
from ..transport import FakeTransport


def fmt_1dp(x: float) -> str:
    return f"{x:0.1f}"


def parse_float(s: str) -> float:
    """Ondalik sayıyı parse eder (hem '29.5' hem '29,5' kabul eder)."""
    return float(s.strip().replace(",", "."))


def air_conditioner_menu(air: AirConditionerSystemConnection, port: str, baud: int) -> None:
    while True:
        try:
            air.update()
        except Exception:
            pass

        print("\nHome Ambient Temperature:", fmt_1dp(air.getAmbientTemp()), "°C")
        print("Home Desired Temperature:", fmt_1dp(air.getDesiredTemp()), "°C")
        print("Fan Speed:", f"{air.getFanSpeed()} rps")
        print("-" * 48)
        print("Connection Port:", port)
        print("Connection Baudrate:", baud)

        print("\nMENU")
        print("1. Enter the desired temperature")
        print("2. Return")
        choice = input("> ").strip()

        if choice == "1":
            val = input("Enter Desired Temp: ").strip()
            try:
                temp = parse_float(val)
            except ValueError:
                print("Invalid number.")
                continue

            # Sıcaklık aralığını kontrol et (10.0-50.0°C)
            if not (10.0 <= temp <= 50.0):
                print("Rejected. Desired temperature must be between 10.0 and 50.0.")
                continue

            temp = round(temp, 1)
            if not (10.0 <= temp <= 50.0):
                print("FAILED: Desired temperature must be between 10.0 and 50.0")
                continue
            ok = air.setDesiredTemp(temp)
            print("OK" if ok else "FAILED")


        elif choice == "2":
            return
        else:
            print("Invalid selection.")


def curtain_control_menu(cur: CurtainControlSystemConnection, port: str, baud: int) -> None:
    while True:
        try:
            cur.update()
        except Exception as e:
            print(f"DEBUG: update() exception: {e}")
            import traceback
            traceback.print_exc()

        print("\nOutdoor Temperature:", fmt_1dp(cur.getOutdoorTemp()), "°C")
        print("Outdoor Pressure:", fmt_1dp(cur.getOutdoorPress()), "hPa")
        print("Curtain Status:", fmt_1dp(cur.curtainStatus), "%")
        print("Light Intensity:", fmt_1dp(cur.getLightIntensity()), "Lux")
        print("-" * 48)
        print("Connection Port:", port)
        print("Connection Baudrate:", baud)

        print("\nMENU")
        print("1. Enter the desired curtain status")
        print("2. Return")
        choice = input("> ").strip()

        if choice == "1":
            val = input("Enter Desired Curtain: ").strip()
            try:
                pct = parse_float(val)
            except ValueError:
                print("Invalid number.")
                continue

            if not (0.0 <= pct <= 100.0):
                print("Rejected. Curtain status must be between 0 and 100.")
                continue

            pct = round(pct, 1)
            if not (0.0 <= pct <= 100.0):
                print("FAILED: Curtain status must be between 0 and 100 (%)")
                continue

            ok = cur.setCurtainStatus(pct)
            print("OK" if ok else "FAILED")


        elif choice == "2":
            return
        else:
            print("Invalid selection.")


def build_system(args):
    """Komut satırı argümanlarına göre sistemi oluşturur (fake veya gerçek mod)."""
    if args.fake:
        t1 = FakeTransport(board="board1")
        t2 = FakeTransport(board="board2")
        c1 = HomeAutomationSystemConnection(transport=t1, comPort="FAKE1", baudRate=args.baud)
        c2 = HomeAutomationSystemConnection(transport=t2, comPort="FAKE2", baudRate=args.baud)
    else:
        if not args.port1 or not args.port2:
            raise SystemExit("Serial mode requires --port1 and --port2")

        # SerialTransport sadece gerektiğinde import edilir
        from ..transport.serial_transport import SerialTransport

        t1 = SerialTransport(port=args.port1, baudrate=args.baud)
        t2 = SerialTransport(port=args.port2, baudrate=args.baud)
        c1 = HomeAutomationSystemConnection(transport=t1, comPort=args.port1, baudRate=args.baud)
        c2 = HomeAutomationSystemConnection(transport=t2, comPort=args.port2, baudRate=args.baud)

    air = AirConditionerSystemConnection(connection=c1)
    cur = CurtainControlSystemConnection(connection=c2)

    if not c1.open():
        msg = c1.last_error or ""
        print(f"Warning: Could not open connection for Board#1 ({c1.comPort}). {msg}".strip())
    if not c2.open():
        msg = c2.last_error or ""
        print(f"Warning: Could not open connection for Board#2 ({c2.comPort}). {msg}".strip())


    return air, cur, c1, c2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="Run without COM ports (FakeTransport)")
    parser.add_argument("--port1", type=str, default="", help="COM port for Board#1 (Air Conditioner)")
    parser.add_argument("--port2", type=str, default="", help="COM port for Board#2 (Curtain Control)")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate")
    args = parser.parse_args(argv)

    air, cur, c1, c2 = build_system(args)

    while True:
        print("\nMAIN MENU")
        print("1. Air Conditioner")
        print("2. Curtain Control")
        print("3. Exit")
        choice = input("> ").strip()

        if choice == "1":
            air_conditioner_menu(air, c1.comPort, c1.baudRate)
        elif choice == "2":
            curtain_control_menu(cur, c2.comPort, c2.baudRate)
        elif choice == "3":
            c1.close()
            c2.close()
            return 0
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    raise SystemExit(main())
