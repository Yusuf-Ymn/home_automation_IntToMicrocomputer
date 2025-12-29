"""Board #2 UART Protokol Test Programı

Tüm GET ve SET komutlarını test eder.
"""
from home_automation.api import HomeAutomationSystemConnection, CurtainControlSystemConnection
from home_automation.transport import FakeTransport
from home_automation.protocol import board2


def test_all_get_commands():
    """Tüm GET komutlarını test et"""
    print("=" * 60)
    print("BOARD #2 GET KOMUTLARI TESTİ")
    print("=" * 60)
    
    t = FakeTransport(board="board2")
    conn = HomeAutomationSystemConnection(transport=t, comPort="TEST", baudRate=9600)
    conn.open()
    api = CurtainControlSystemConnection(connection=conn)
    
    # GET komutlarını test et
    print("\n GET Komutları Test Ediliyor...\n")
    
    try:
        api.update()
        
        print(f" GET Desired Curtain:")
        print(f"   → Curtain Status: {api.curtainStatus}%")
        
        print(f"\n GET Outdoor Temperature:")
        print(f"   → Temperature: {api.getOutdoorTemp()}°C")
        
        print(f"\n GET Outdoor Pressure:")
        print(f"   → Pressure: {api.getOutdoorPress()} hPa")
        
        print(f"\n GET Light Intensity:")
        print(f"   → Light: {api.getLightIntensity()} Lux")
        
        print("\n" + "=" * 60)
        print("SONUÇ: TÜM GET KOMUTLARI BAŞARILI ")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n HATA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_set_commands():
    """Tüm SET komutlarını test et"""
    print("\n" + "=" * 60)
    print("BOARD #2 SET KOMUTLARI TESTİ")
    print("=" * 60)
    
    t = FakeTransport(board="board2")
    conn = HomeAutomationSystemConnection(transport=t, comPort="TEST", baudRate=9600)
    conn.open()
    api = CurtainControlSystemConnection(connection=conn)
    
    print("\n SET Komutları Test Ediliyor...\n")
    
    test_values = [0.0, 25.5, 50.0, 75.3, 100.0]
    
    for val in test_values:
        try:
            success = api.setCurtainStatus(val)
            if success:
                api.update()
                print(f" SET Curtain {val}% → Okunan: {api.curtainStatus}%")
            else:
                print(f" SET Curtain {val}% BAŞARISIZ")
                return False
        except Exception as e:
            print(f" SET Curtain {val}% HATA: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("SONUÇ: TÜM SET KOMUTLARI BAŞARILI ")
    print("=" * 60)
    
    return True


def test_protocol_details():
    """Protokol detaylarını test et"""
    print("\n" + "=" * 60)
    print("PROTOKOL DETAY TESTİ")
    print("=" * 60)
    
    print("\n UART Komut Adresleri (PDF Sayfa 19):\n")
    
    commands = [
        ("GET_DESIRED_CURTAIN_LOW", 0x01, "Perde kesirli byte"),
        ("GET_DESIRED_CURTAIN_HIGH", 0x02, "Perde tam byte"),
        ("GET_OUTDOOR_TEMP_LOW", 0x03, "Dış sıcaklık kesirli"),
        ("GET_OUTDOOR_TEMP_HIGH", 0x04, "Dış sıcaklık tam"),
        ("GET_OUTDOOR_PRESS_LOW", 0x05, "Dış basınç kesirli"),
        ("GET_OUTDOOR_PRESS_HIGH", 0x06, "Dış basınç tam"),
        ("GET_LIGHT_INTENSITY_LOW", 0x07, "Işık kesirli"),
        ("GET_LIGHT_INTENSITY_HIGH", 0x08, "Işık tam"),
    ]
    
    all_ok = True
    for name, expected, desc in commands:
        actual = getattr(board2, name)
        status = "✅" if actual == expected else "❌"
        print(f"{status} {name:30} = 0x{actual:02X} (beklenen: 0x{expected:02X}) - {desc}")
        if actual != expected:
            all_ok = False
    
    print("\n SET Komut Formatları:\n")
    
    # Test SET encoding
    from home_automation.protocol.board2 import encode_set_desired_curtain
    
    test_cases = [
        (0.0, "0% (minimum)"),
        (50.0, "50% (orta)"),
        (100.0, "100% (maksimum)"),
    ]
    
    for percent, desc in test_cases:
        low_cmd, high_cmd = encode_set_desired_curtain(percent, mode="scaled_0_63")
        
        # Check prefix bits
        low_prefix_ok = (low_cmd & 0b11000000) == 0b10000000
        high_prefix_ok = (high_cmd & 0b11000000) == 0b11000000
        
        status = "✅" if (low_prefix_ok and high_prefix_ok) else "❌"
        
        print(f"{status} {desc:20} → LOW: 0x{low_cmd:02X} (10xxxxxx), HIGH: 0x{high_cmd:02X} (11xxxxxx)")
        
        if not (low_prefix_ok and high_prefix_ok):
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("SONUÇ: PROTOKOL TAM UYUMLU ")
    else:
        print("SONUÇ: PROTOKOL HATASI VAR ")
    print("=" * 60)
    
    return all_ok


def main():
    print("\n")
    print("BOARD #2 KAPSAMLI PROTOKOL TESTİ")
    print("\n")
    
    results = []
    
    # Test 1: GET komutları
    results.append(("GET Komutları", test_all_get_commands()))
    
    # Test 2: SET komutları
    results.append(("SET Komutları", test_all_set_commands()))
    
    # Test 3: Protokol detayları
    results.append(("Protokol Uyumu", test_protocol_details()))
    
    # Final rapor
    print("\n" + "=" * 60)
    print("FİNAL TEST RAPORU")
    print("=" * 60 + "\n")
    
    all_passed = True
    for test_name, passed in results:
        status = " BAŞARILI" if passed else " BAŞARISIZ"
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print(" TÜM TESTLER BAŞARILI! BOARD #2 TAM ÇALIŞIR DURUMDA! ")
    else:
        print("  BAZI TESTLER BAŞARISIZ! KONTROL EDİN! ")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
