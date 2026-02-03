# Home Automation System

**ESOGU – Introduction to Microcomputers (Term Project)**

This is the PC Control Software for our Home Automation Project. It communicates with two **PIC16F877A** boards using the **UART** protocol.

For a complete overview of the system architecture, implementation details, and project documentation, please refer to the "Report_Home_Automation.docx" file included in this repository.

---

## About the Project

In this project, we designed a system with two main modules. This software runs on the computer and allows the user to monitor and control these modules.

### Board #1: Air Conditioner System

* **Set Desired Temperature:** User can set a value between **10.0°C** and **50.0°C**.
* **Read Ambient Temperature:** Displays the current room temperature.
* **Fan Speed:** Shows the fan speed (**rps**) based on the heating needs.

### Board #2: Curtain Control System

* **Set Curtain Position:** User can open/close the curtain (**0–100%**).
* **Read Light Intensity:** Displays the light level (**Lux**) from the sensor.

---

## Requirements

* Python **3.7** or higher
* **PySerial** library (for real hardware communication)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Yusuf-Ymn/home_automation_IntToMicrocomputer.git
cd home_automation_IntToMicrocomputer
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## How to Run

### 1) Simulation Mode (No Hardware)

You can test the interface without connecting any boards. This uses the `FakeTransport` layer.

```bash
python -m home_automation.app.console --fake
```

### 2) Real Hardware Mode

If you have the PIC boards connected to your computer via USB-TTL converters, use this command. Replace `COM3` and `COM5` with your actual ports.

```bash
python -m home_automation.app.console --port1 COM3 --port2 COM5 --baud 9600
```

* `--port1`: COM port for Air Conditioner (Board 1)
* `--port2`: COM port for Curtain Control (Board 2)
* `--baud`: Baud rate (Default: **9600**)

### 3) Board Simulator (PC-to-PC Test)

If you want to test the serial logic using virtual ports (like **com0com**) instead of real PICs:

```bash
python -m home_automation.tools.serial_board_sim --b1 COM11 --b2 COM13
```

---

## Project Structure

```text
home_automation/
├── api/                   # High-Level API Layer
│   ├── air_conditioner.py  # Logic for Board 1
│   ├── curtain_control.py  # Logic for Board 2
│   └── common.py           # Shared connection logic
├── app/                   # User Interface
│   └── console.py          # Main console menu application
├── protocol/              # UART Protocol Layer (Bit manipulation)
│   ├── board1.py           # Command definitions for Board 1
│   ├── board2.py           # Command definitions for Board 2
│   └── common.py           # Encoding/Decoding helpers
├── transport/             # Communication Layer
│   ├── base.py             # Abstract base class
│   ├── fake_transport.py   # For testing without hardware
│   └── serial_transport.py # Real PySerial implementation
├── tests/                 # Unit Tests
│   ├── api_test_program.py
│   └── test_protocol_ranges.py
└── tools/                 # Helper Tools
    └── serial_board_sim.py # Python-based board simulator
```

---

## Testing

To run the unit tests for protocol logic:

```bash
python -m unittest tests.test_protocol_ranges
```

To run the API functionality test:

```bash
python home_automation/tests/api_test_program.py
```
