# Home Automation System

IntToMicrocomputer Dersi Term Projesi - PC tarafli kontrol yazilimi.

## Proje Hakkinda

Bu proje, UART protokolu uzerinden iki farkli mikroislemci karti ile haberlesmeyi saglayan bir ev otomasyon kontrol sistemidir.

**Board #1 - Klima Sistemi:**
- Istenen sicaklik ayarlama (10.0-50.0°C)
- Ortam sicakligini okuma
- Fan hizini kontrol etme

**Board #2 - Perde Kontrol Sistemi:**
- Perde aciklik oranini ayarlama (0-100%)
- Dis ortam sicakligini okuma
- Dis ortam basincini okuma
- Isik yogunlugunu okuma

## Gereksinimler

- Python 3.7 veya uzeri
- PySerial (sadece gercek donanim ile calisma icin)

## Kurulum

```bash
# Repository'yi klonlayin
git clone https://github.com/Yusuf-Ymn/home_automation_IntToMicrocomputer.git
cd home_automation_IntToMicrocomputer

# Gerekli kutuphaneleri yukleyin
pip install -r requirements.txt
```

## Kullanim

### Simulasyon Modu (Donanim Olmadan)

Gercek donanim gerektirmez, her sey bellekte simule edilir:

```bash
python -m home_automation.app.console --fake
```

### Gercek Donanim ile Kullanim

COM portlarinizi belirterek gercek kartlarla calisabilirsiniz:

```bash
python -m home_automation.app.console --port1 COM3 --port2 COM5 --baud 9600
```

**Parametreler:**
- `--port1`: Board #1 (Klima) icin COM port
- `--port2`: Board #2 (Perde) icin COM port
- `--baud`: Baud rate (varsayilan: 9600)

### Serial Port Simulatoru

Sanal COM portlari (com0com gibi) ile test icin board simulatoru:

```bash
python -m home_automation.tools.serial_board_sim --b1 COM11 --b2 COM13 --baud 9600
```

## Proje Yapisi

```
home_automation/
├── api/                    # Yuksek seviye API
│   ├── air_conditioner.py  # Klima kontrolu
│   ├── curtain_control.py  # Perde kontrolu
│   └── common.py           # Ortak baglanti yonetimi
├── app/                    # Kullanici arayuzu
│   └── console.py          # Konsol tabanli uygulama
├── protocol/               # UART protokol katmani
│   ├── board1.py           # Board #1 protokol tanimlari
│   ├── board2.py           # Board #2 protokol tanimlari
│   └── common.py           # Ortak encoding/decoding
├── transport/              # Iletisim katmani
│   ├── base.py             # Transport interface
│   ├── fake_transport.py   # Simulasyon transport
│   └── serial_transport.py # Gercek seri port transport
├── tests/                  # Test dosyalari
│   ├── api_test_program.py
│   └── test_protocol_ranges.py
└── tools/                  # Yardimci araclar
    └── serial_board_sim.py # Serial board simulatoru
```

## Test

### Unit Testler

```bash
python -m unittest tests.test_protocol_ranges
```

### API Testleri

```bash
python tests/api_test_program.py
```

## Ozellikler

- Katmanli mimari (Transport -> Protocol -> API -> App)
- Donanim olmadan gelistirme (FakeTransport)
- Gercek seri port destegi (PySerial)
- Kapsamli hata yonetimi
- Input validasyon
- Test coverage

## Lisans

Bu proje egitim amacli geliştirilmistir.
