"""API fonksiyonlarını test eden örnek program.

Fake transport kullanarak her iki board'ın API'sını test eder.
"""
from home_automation.api import (
    HomeAutomationSystemConnection,
    AirConditionerSystemConnection,
    CurtainControlSystemConnection,
)
from home_automation.transport import FakeTransport


def main():
    # Board#1 fake
    t1 = FakeTransport(board="board1")
    c1 = HomeAutomationSystemConnection(transport=t1, comPort="FAKE1", baudRate=9600)
    c1.open()
    air = AirConditionerSystemConnection(connection=c1)

    # Board#2 fake
    t2 = FakeTransport(board="board2")
    c2 = HomeAutomationSystemConnection(transport=t2, comPort="FAKE2", baudRate=9600)
    c2.open()
    cur = CurtainControlSystemConnection(connection=c2)

    print("=== API TEST PROGRAM (FAKE) ===")

    air.update()
    print("[Air] Ambient:", air.getAmbientTemp(), "Desired:", air.getDesiredTemp(), "Fan:", air.getFanSpeed())

    ok = air.setDesiredTemp(29.5)
    print("[Air] setDesiredTemp(29.5) ->", ok)
    air.update()
    print("[Air] After set -> Desired:", air.getDesiredTemp())

    cur.update()
    print("[Curtain] Temp:", cur.getOutdoorTemp(), "Press:", cur.getOutdoorPress(),
          "Curtain:", cur.curtainStatus, "Light:", cur.getLightIntensity())

    ok = cur.setCurtainStatus(75.0)
    print("[Curtain] setCurtainStatus(75.0) ->", ok)
    cur.update()
    print("[Curtain] After set -> Curtain:", cur.curtainStatus)

    print("=== DONE ===")


if __name__ == "__main__":
    main()
