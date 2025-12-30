"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/tests/api_test_program.py
DESCRIPTION:
    A simple test program to verify the API functions.
    It uses 'FakeTransport' to simulate boards without real hardware.
    Useful for checking if the code logic is working correctly.

AUTHOR:
    1. Yiğit Ata - 152120221106
================================================================================
"""

from home_automation.api import (
    HomeAutomationSystemConnection,
    AirConditionerSystemConnection,
    CurtainControlSystemConnection,
)
from home_automation.transport import FakeTransport


def main():
    # --- Setup Board #1 (Air Conditioner) ---
    # Create a fake connection for testing
    t1 = FakeTransport(board="board1")
    c1 = HomeAutomationSystemConnection(transport=t1, comPort="FAKE1", baudRate=9600)
    c1.open()
    
    # Create the API object
    air = AirConditionerSystemConnection(connection=c1)

    # --- Setup Board #2 (Curtain Control) ---
    # Create a fake connection for testing
    t2 = FakeTransport(board="board2")
    c2 = HomeAutomationSystemConnection(transport=t2, comPort="FAKE2", baudRate=9600)
    c2.open()
    
    # Create the API object
    cur = CurtainControlSystemConnection(connection=c2)

    print("=== API TEST PROGRAM (FAKE) ===")

    # Test Reading from Board 1
    air.update()
    print("[Air] Ambient:", air.getAmbientTemp(), "Desired:", air.getDesiredTemp(), "Fan:", air.getFanSpeed())

    # Test Writing to Board 1
    ok = air.setDesiredTemp(29.5)
    print("[Air] setDesiredTemp(29.5) ->", ok)
    
    # Check if value is updated
    air.update()
    print("[Air] After set -> Desired:", air.getDesiredTemp())

    print("-" * 30)

    # Test Reading from Board 2
    cur.update()
    print("[Curtain] Temp:", cur.getOutdoorTemp(), "Press:", cur.getOutdoorPress(),
          "Curtain:", cur.curtainStatus, "Light:", cur.getLightIntensity())

    # Test Writing to Board 2
    ok = cur.setCurtainStatus(75.0)
    print("[Curtain] setCurtainStatus(75.0) ->", ok)
    
    # Check if value is updated
    cur.update()
    print("[Curtain] After set -> Curtain:", cur.curtainStatus)

    print("=== DONE ===")


if __name__ == "__main__":
    main()