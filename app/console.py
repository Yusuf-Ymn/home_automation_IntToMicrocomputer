"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/app/console.py
DESCRIPTION:
    This file implements the Console Application (PC Side) for the project.
    It provides a menu-based interface for the user to interact with the
    Air Conditioner (Board #1) and Curtain Control (Board #2) systems.

USAGE:
    - Simulation Mode: python -m home_automation.app.console --fake
    - Real Mode:       python -m home_automation.app.console --port1 COM3 --port2 COM5

REQUIREMENTS MET:
    [R2.4] Application Requirements (PC Side Program)
    [R2.4-1] Menu Structure (Main Menu, Air Conditioner Menu, Curtain Menu)
    [Figure 18] Matches the specific menu layout defined in the PDF

AUTHORS:
    1. Yusuf Yaman 152120221075
    2. Yigit Ata 152120221106
    3. Dogancan Kucuk 151220212099
================================================================================
"""

from __future__ import annotations

import argparse
import time

from ..api import (
    HomeAutomationSystemConnection,
    AirConditionerSystemConnection,
    CurtainControlSystemConnection,
)
from ..transport import FakeTransport


def fmt_1dp(x: float) -> str:
    """Helper to format float numbers to 1 decimal place."""
    return f"{x:0.1f}"


def parse_float(s: str) -> float:
    """
    Parses decimal numbers from user input.
    Accepts both dot (.) and comma (,) as separators.
    """
    return float(s.strip().replace(",", "."))


def air_conditioner_menu(air: AirConditionerSystemConnection, port: str, baud: int) -> None:
    """
    [R2.4-1] Sub-menu for Air Conditioner System (Board #1).
    Displays temperature/fan data and allows setting desired temperature.
    Matches the layout in Figure 18.
    """
    while True:
        # Update data from the board
        try:
            air.update()
        except Exception:
            pass  # Ignore temporary errors to keep menu alive

        # [Figure 18] Display System Information
        print("\nHome Ambient Temperature:", fmt_1dp(air.getAmbientTemp()), "°C")
        print("Home Desired Temperature:", fmt_1dp(air.getDesiredTemp()), "°C")
        print("Fan Speed:", f"{air.getFanSpeed()} rps")
        print("-" * 48)
        print("Connection Port:", port)
        print("Connection Baudrate:", baud)

        # [Figure 18] Menu Options
        print("\nMENU")
        print("1. Enter the desired temperature")
        print("2. Return")
        choice = input("> ").strip()

        if choice == "1":
            # [Figure 18] "Enter Desired Temp: ...."
            val = input("Enter Desired Temp: ").strip()
            try:
                temp = parse_float(val)
            except ValueError:
                print("Invalid number.")
                continue

            # Check valid range (10.0 - 50.0 C)
            if not (10.0 <= temp <= 50.0):
                print("Rejected. Desired temperature must be between 10.0 and 50.0.")
                continue

            temp = round(temp, 1)
            
            # Send command to Board #1
            ok = air.setDesiredTemp(temp)
            print("OK" if ok else "FAILED")
            
            # Wait briefly to let user see result
            time.sleep(1)
            continue

        elif choice == "2":
            # Return to Main Menu
            return
        else:
            print("Invalid selection.")


def curtain_control_menu(cur: CurtainControlSystemConnection, port: str, baud: int) -> None:
    """
    [R2.4-1] Sub-menu for Curtain Control System (Board #2).
    Displays sensors/curtain data and allows setting curtain openness.
    Matches the layout in Figure 18.
    """
    while True:
        # Update data from the board
        try:
            cur.update()
        except Exception:
            pass

        # [Figure 18] Display System Information
        print("\nOutdoor Temperature:", fmt_1dp(cur.getOutdoorTemp()), "°C")
        print("Outdoor Pressure:", fmt_1dp(cur.getOutdoorPress()), "hPa")
        print("Curtain Status:", fmt_1dp(cur.curtainStatus), "%")
        print("Light Intensity:", fmt_1dp(cur.getLightIntensity()), "Lux")
        print("-" * 48)
        print("Connection Port:", port)
        print("Connection Baudrate:", baud)

        # [Figure 18] Menu Options
        print("\nMENU")
        print("1. Enter the desired curtain status")
        print("2. Return")
        choice = input("> ").strip()

        if choice == "1":
            # [Figure 18] "Enter Desired Curtain: ...."
            val = input("Enter Desired Curtain: ").strip()
            try:
                pct = parse_float(val)
            except ValueError:
                print("Invalid number.")
                continue

            # Check valid range (0% - 100%)
            if not (0.0 <= pct <= 100.0):
                print("Rejected. Curtain status must be between 0 and 100.")
                continue

            pct = round(pct, 1)
            
            # Send command to Board #2
            ok = cur.setCurtainStatus(pct)
            print("OK" if ok else "FAILED")
            
            # Wait for motor movement (Simulation delay)
            print("Waiting for motor to finish...")
            time.sleep(3) 
            continue

        elif choice == "2":
            # Return to Main Menu
            return
        else:
            print("Invalid selection.")


def build_system(args):
    """
    Initializes the system connections based on command line arguments.
    Supports both 'Fake' (Simulation) and 'Real' (Serial) modes.
    """
    if args.fake:
        # Use FakeTransport for testing without hardware
        t1 = FakeTransport(board="board1")
        t2 = FakeTransport(board="board2")
        c1 = HomeAutomationSystemConnection(transport=t1, comPort="FAKE1", baudRate=args.baud)
        c2 = HomeAutomationSystemConnection(transport=t2, comPort="FAKE2", baudRate=args.baud)
    else:
        # Use Real Serial Transport
        if not args.port1 or not args.port2:
            raise SystemExit("Serial mode requires --port1 and --port2")

        # Import SerialTransport only if needed (requires pyserial)
        from ..transport.serial_transport import SerialTransport

        t1 = SerialTransport(port=args.port1, baudrate=args.baud)
        t2 = SerialTransport(port=args.port2, baudrate=args.baud)
        c1 = HomeAutomationSystemConnection(transport=t1, comPort=args.port1, baudRate=args.baud)
        c2 = HomeAutomationSystemConnection(transport=t2, comPort=args.port2, baudRate=args.baud)

    # Initialize High-Level API objects
    air = AirConditionerSystemConnection(connection=c1)
    cur = CurtainControlSystemConnection(connection=c2)

    # Open Connections
    if not c1.open():
        msg = c1.last_error or ""
        print(f"Warning: Could not open connection for Board#1 ({c1.comPort}). {msg}".strip())
    else:
        # Initial sync
        try:
            air.update()
        except Exception:
            pass
            
    if not c2.open():
        msg = c2.last_error or ""
        print(f"Warning: Could not open connection for Board#2 ({c2.comPort}). {msg}".strip())
    else:
        # Initial sync
        try:
            cur.update()
        except Exception:
            pass

    return air, cur, c1, c2


def main(argv=None) -> int:
    """
    Main entry point of the application.
    Parses arguments and runs the Main Menu loop.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="Run without COM ports (FakeTransport)")
    parser.add_argument("--port1", type=str, default="", help="COM port for Board#1 (Air Conditioner)")
    parser.add_argument("--port2", type=str, default="", help="COM port for Board#2 (Curtain Control)")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate")
    args = parser.parse_args(argv)

    # Build system components
    air, cur, c1, c2 = build_system(args)

    # [R2.4-1] Main Menu Loop
    while True:
        print("\nMAIN MENU")
        print("1. Air Conditioner")
        print("2. Curtain Control")
        print("3. Exit")
        choice = input("> ").strip()

        if choice == "1":
            # Go to Air Conditioner Menu
            air_conditioner_menu(air, c1.comPort, c1.baudRate)
        elif choice == "2":
            # Go to Curtain Control Menu
            curtain_control_menu(cur, c2.comPort, c2.baudRate)
        elif choice == "3":
            # Close connections and Exit
            c1.close()
            c2.close()
            return 0
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    raise SystemExit(main())
