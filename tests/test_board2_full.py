"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/tests/test_board2_full.py
DESCRIPTION:
    Full test program for Board #2 (Curtain Control) UART Protocol.
    It checks all GET and SET commands to make sure they work correctly.
    
    Refers to Requirement: [R2.2.6-1] UART Module Command Set

AUTHOR:
    1.Yusuf Yaman - 152120221075
================================================================================
"""

from home_automation.api import HomeAutomationSystemConnection, CurtainControlSystemConnection
from home_automation.transport import FakeTransport
from home_automation.protocol import board2


def test_all_get_commands():
    """Tests all GET commands to read data from the board."""
    print("=" * 60)
    print("BOARD #2 GET COMMANDS TEST")
    print("=" * 60)
    
    # Create a fake connection for testing
    t = FakeTransport(board="board2")
    conn = HomeAutomationSystemConnection(transport=t, comPort="TEST", baudRate=9600)
    conn.open()
    api = CurtainControlSystemConnection(connection=conn)
    
    print("\n Testing GET Commands...\n")
    
    try:
        # Read values from the (fake) board
        api.update()
        
        print(f" GET Desired Curtain:")
        print(f"   -> Curtain Status: {api.curtainStatus}%")
        
        print(f"\n GET Outdoor Temperature:")
        print(f"   -> Temperature: {api.getOutdoorTemp()}°C")
        
        print(f"\n GET Outdoor Pressure:")
        print(f"   -> Pressure: {api.getOutdoorPress()} hPa")
        
        print(f"\n GET Light Intensity:")
        print(f"   -> Light: {api.getLightIntensity()} Lux")
        
        print("\n" + "=" * 60)
        print("RESULT: ALL GET COMMANDS SUCCESSFUL ")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_set_commands():
    """Tests all SET commands to control the curtain."""
    print("\n" + "=" * 60)
    print("BOARD #2 SET COMMANDS TEST")
    print("=" * 60)
    
    t = FakeTransport(board="board2")
    conn = HomeAutomationSystemConnection(transport=t, comPort="TEST", baudRate=9600)
    conn.open()
    api = CurtainControlSystemConnection(connection=conn)
    
    print("\n Testing SET Commands...\n")
    
    test_values = [0.0, 25.5, 50.0, 75.3, 100.0]
    
    for val in test_values:
        try:
            # Try to set the curtain position
            success = api.setCurtainStatus(val)
            if success:
                # Read it back to verify
                api.update()
                print(f" SET Curtain {val}% -> Read back: {api.curtainStatus}%")
            else:
                print(f" SET Curtain {val}% FAILED")
                return False
        except Exception as e:
            print(f" SET Curtain {val}% ERROR: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("RESULT: ALL SET COMMANDS SUCCESSFUL ")
    print("=" * 60)
    
    return True


def test_protocol_details():
    """
    Checks if the command byte values match the project requirements.
    Reference: PDF Page 19 [R2.2.6-1]
    """
    print("\n" + "=" * 60)
    print("PROTOCOL DETAIL TEST")
    print("=" * 60)
    
    print("\n UART Command Addresses (Requirement [R2.2.6-1]):\n")
    
    # List of commands to check: (Name, Expected Value, Description)
    commands = [
        ("GET_DESIRED_CURTAIN_LOW", 0x01, "Curtain Low Byte"),
        ("GET_DESIRED_CURTAIN_HIGH", 0x02, "Curtain High Byte"),
        ("GET_OUTDOOR_TEMP_LOW", 0x03, "Temp Low Byte"),
        ("GET_OUTDOOR_TEMP_HIGH", 0x04, "Temp High Byte"),
        ("GET_OUTDOOR_PRESS_LOW", 0x05, "Pressure Low Byte"),
        ("GET_OUTDOOR_PRESS_HIGH", 0x06, "Pressure High Byte"),
        ("GET_LIGHT_INTENSITY_LOW", 0x07, "Light Low Byte"),
        ("GET_LIGHT_INTENSITY_HIGH", 0x08, "Light High Byte"),
    ]
    
    all_ok = True
    for name, expected, desc in commands:
        actual = getattr(board2, name)
        status = "OK" if actual == expected else "FAIL"
        print(f"{status} {name:30} = 0x{actual:02X} (Expected: 0x{expected:02X}) - {desc}")
        if actual != expected:
            all_ok = False
    
    print("\n SET Command Formats:\n")
    
    # Test SET command encoding logic
    from home_automation.protocol.board2 import encode_set_desired_curtain
    
    test_cases = [
        (0.0, "0% (Min)"),
        (50.0, "50% (Mid)"),
        (100.0, "100% (Max)"),
    ]
    
    for percent, desc in test_cases:
        low_cmd, high_cmd = encode_set_desired_curtain(percent, mode="scaled_0_63")
        
        # Check prefix bits (10xxxxxx for low, 11xxxxxx for high)
        low_prefix_ok = (low_cmd & 0b11000000) == 0b10000000
        high_prefix_ok = (high_cmd & 0b11000000) == 0b11000000
        
        status = "OK" if (low_prefix_ok and high_prefix_ok) else "FAIL"
        
        print(f"{status} {desc:20} -> LOW: 0x{low_cmd:02X} (10..), HIGH: 0x{high_cmd:02X} (11..)")
        
        if not (low_prefix_ok and high_prefix_ok):
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("RESULT: PROTOCOL IS FULLY COMPLIANT ")
    else:
        print("RESULT: PROTOCOL HAS ERRORS ")
    print("=" * 60)
    
    return all_ok


def main():
    print("\n")
    print("BOARD #2 COMPREHENSIVE PROTOCOL TEST")
    print("\n")
    
    results = []
    
    # Run tests
    results.append(("GET Commands", test_all_get_commands()))
    results.append(("SET Commands", test_all_set_commands()))
    results.append(("Protocol Details", test_protocol_details()))
    
    # Final Report
    print("\n" + "=" * 60)
    print("FINAL TEST REPORT")
    print("=" * 60 + "\n")
    
    all_passed = True
    for test_name, passed in results:
        status = " PASS" if passed else " FAIL"
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print(" ALL TESTS PASSED! BOARD #2 IS READY! ")
    else:
        print("  SOME TESTS FAILED! PLEASE CHECK! ")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())