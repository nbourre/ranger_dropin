# Ranger drop-in: BEAPER Nano carrier for ESP32-S3

Goal: replace the Arduino-based **Makeblock Auriga** controller of an mBot Ranger with a custom carrier board for an **ESP32-S3-DevKitC-1-N16R8**, based on the mirobo.tech **BEAPER Nano** schematic converted to SMD parts (JLCPCB/LCSC, Basic parts where possible).

Project files: KiCad 10 (`BEAPER-Nano.kicad_sch`, `BEAPER-Nano.kicad_pcb`), custom footprint library `BEAPER-Nano.pretty`, custom symbol library `ESP32S3.kicad_sym`. Reference: `Me Auriga Schematic.pdf`.

> **Status:** schematic is updated (ERC: 0 errors). The PCB has **not** been updated yet. It still contains the old footprints and is waiting for the board dimensions.

---

## 1. Makeblock Auriga (original controller)

Source: `Me Auriga Schematic.pdf` (one page, read as text). Items marked *(memory)* are not visible in that PDF and come from general knowledge of the mBot Ranger. The full pin-by-pin map is in [AURIGA_PINMAP.md](AURIGA_PINMAP.md).

| Function | Details |
|---|---|
| MCU | ATmega2560 *(memory)*, with ICSP header |
| USB-serial | CH340G |
| Motor driver | TB6612 (1.2 A continuous per channel), two motor ports with encoders (`ENC` signals, 51 Ω series resistors) |
| Motor power protection | Fuses (1 A per motor, 3.5 A main), SS54 diode, SMAJ TVS, 470 µF / 16 V on the motor rail |
| Regulators | 5 V LDO and 3.3 V XC6206 |
| IMU | MPU6050 gyroscope + accelerometer (I2C, INT and AD0 pins) |
| RGB LED ring | 12 RGB LEDs, one data line (`D44/RGB`) |
| Ambient light sensors | LIGHT1 and LIGHT2 |
| Sound sensor | Microphone with LM2904 amplifier |
| Temperature sensor | Present (`TEMP`) |
| Buzzer | Present |
| User button | One (`KEY`) |
| Status LEDs | LED_RED, LED_BLUE |
| RJ25 ports | 10 ports for Makeblock modules (line follower, ultrasonic, etc.) |
| Servo header | `P_SERVO`, powered from the motor rail (V-M) |
| Wireless | Bluetooth / 2.4 G module socket *(memory)* |

---

## 2. BEAPER Nano on ESP32-S3 (this project)

Carrier board for the ESP32-S3-DevKitC-1-N16R8 (U5, two 22-pin headers, 22.86 mm apart).

### Power
- Battery input on **CON1** (screw terminal), 7.2 V NiMH RC pack.
- Protection: fuse F1 (3.5 A), SS54 diode D8, SMAJ13A TVS D9, 470 µF bulk capacitor C8.
- **U1 (LM2940-5.0)** makes the +5 V rail. The DevKitC-1 has no VIN pin, so it is powered through its 5V pin. U1 is therefore **required**.
- 3.3 V comes from the DevKitC-1.
- No on-board USB charger (external charger for the pack).

### Motors
- **U3 TB6612FNG** (SSOP-24, LCSC C141517, Extended part). Replaces the SN754410 of the original design.
- CON1 pins 3 to 6 carry the motor outputs.
- **M1 and M2** (1x6 headers, same idea as the Auriga MHDR1X6): pin 6 motor+, 5 motor−, 4 GND, 3 +3V3, 2 encoder A, 1 encoder B.
- Encoder signals go through 51 Ω resistors (R31 to R34) to GPIO 39 to 42. Encoders are powered at **3.3 V** (the Auriga uses 5 V). To be tested with the real motors.
- Difference from the old driver: with both inputs low, the TB6612 coasts (the SN754410 braked). Maximum supply: 13.5 V.

### Sensors and I/O
- **U6 LSM6DS3TR-C** (LCSC C967633): 6-axis IMU on I2C (address 0x6A), interrupts not connected.
- **Battery voltage monitor** (`VOL_BAT`, like the Auriga's A4/VOL_BAT): R35 100 kΩ / R36 51 kΩ divider + C11 1 µF on **GPIO 3** (ADC1_CH2). Ratio 0.338, so a 9 V pack reads about 3.0 V. It is tapped after D8, so it reads about 0.4 V low: calibrate in firmware. GPIO 3 is a strapping pin, which only matters at reset.
- Ambient light sensor (TEPT4400) removed; the Auriga's light module will be reused instead (see TODO).
- Temperature sensor (MCP9700A, on A1), wired directly (no selection jumpers).
- Line / floor sensors and potentiometers were **removed** to free GPIO. As on the Auriga, line-following is done by an external I2C module (home-made: Adafruit ATtiny1616 with seesaw firmware, sensors wired to the ATtiny) on the Qwiic connector (J4) or H1/H4.
- Headers H1 to H4: analog or digital I/O at 3.3 V, or a 4-pin sonar (HC-SR04) through the bridging jumpers.
- Headers H5 to H8: 5 V outputs through the **74HCT541** level shifter (U2), for servos or modules.
- Qwiic / JST-SH I2C connector (J4), SPI / TFT connector (J3).
- Piezo buzzer (LS1), 4 push buttons (SW2 to SW5), 4 status LEDs (D2 to D5), reset button (SW1).

### GPIO mapping (Arduino-style net name → ESP32-S3 GPIO)

| Net | GPIO | Net | GPIO |
|---|---|---|---|
| A0 (free) | 1 | D5 | 17 |
| A1 | 2 | D6 | 18 |
| A2 (free) | 4 | D7 | 21 |
| A3 (free) | 5 | D8 (buzzer) | 47 |
| A6 | 6 | D9 | 38 |
| A7 | 7 | D10 | 10 |
| A4/SDA | 8 | D11/COPI | 11 |
| A5/SCL | 9 | D12/CIPO | 13 |
| D0/RX0 (SW2) | 44 | D13/SCK | 12 |
| D1/TX0 (SW3) | 43 | ~{RST} (SW1) | EN |
| D2 (SW4) | 14 | Encoders | 39, 40, 41, 42 |
| D3 (SW5) | 15 | | |
| D4 | 16 | VOL_BAT | 3 |

Remaining GPIO: **1, 4, 5** (ex A0/A2/A3, no connect) and **48** are free (also drives the on-board RGB LED, suitable for a WS2812 chain). **45, 46, 0** are strapping pins (usable with care). **19, 20** are USB D−/D+. **35, 36, 37** are used by the octal PSRAM and must stay unused.

---

## 3. Comparison

### On the Auriga but missing on the new board
- 12-LED RGB ring (only the DevKit's single RGB LED, GPIO 48, is available).
- Microphone and amplifier.
- A second ambient light sensor.
- RJ25 ports (headers 2.54 mm and Qwiic are used instead).
- Power switch.
- Dedicated Bluetooth / 2.4 G socket. Wi-Fi and BLE are built into the ESP32-S3.

### On the new board but not on the Auriga
- SPI / TFT connector (J3).
- Qwiic / JST-SH I2C connector (J4).
- Headers H1 to H4 (3.3 V analog/digital or sonar) and H5 to H8 (5 V outputs).
- Four user buttons (the Auriga has one).
- Four simple status LEDs.
- Wi-Fi and BLE through the ESP32-S3, with native USB.

### In both
Buzzer, temperature sensor, IMU, battery voltage sensing, motors with encoders, battery protection, reset button, servo outputs.

---

## 4. Open items
- **5 V supply:** the LM2940 (1 A, TO-220) is not enough for pan/tilt with two servos plus the ESP32-S3. Plan: replace it with a 5 V / 3 A buck converter, add about 470 µF near the servo headers, use 5 V servos, and generate the servo signals with LEDC.
- Update the PCB from the schematic once the board dimensions are known. The DevKitC-1 footprint outline is approximate (pad envelope only).
- Missing LCSC references: F1, D8, D9, C8 (470 µF probably not stocked), R31 to R36, C9 to C11, M1/M2. The 5.62 kΩ and 1.37 kΩ resistors are Extended only.
- Possible back-feed of the LM2940 output when USB and battery are connected at the same time (not checked).
- CON1 motor pins 3 to 6 duplicate M1/M2. Decide whether to keep them.
- Optional additions to match the Auriga: RGB LED ring on GPIO 48, power switch.
- The title block comment 3 still says "for Arduino Nano ESP32".
- The schematic page was enlarged from B to C to make room for the IMU.
- ERC: 0 errors, 83 warnings that were already there (library symbol mismatches, missing `Conn_01x03_Male` and `ARPS` libraries, a dangling wire end).

---

## 5. TODO
- [ ] **Distance sensor** such as the VL53L1X (I2C, 3.3 V): add a connector or an on-board footprint on the I2C bus (A4/SDA = GPIO 8, A5/SCL = GPIO 9). XSHUT and GPIO1 (interrupt) can use free GPIO (4, 5).
- [ ] **Reuse the Auriga's RGB LED ring module** (12 LEDs, `D44/RGB` on the Auriga). Put the connector at the correct physical position and pinout so the module is plug and play. Drive it from a free GPIO (GPIO 48 or 4/5) through a 3.3 V → 5 V level shifter if required.
- [ ] **Reuse the Auriga's ambient light module** (LIGHT1/LIGHT2). Same requirement: matching connector position and pinout, on an ADC-capable GPIO (A0/GPIO 1 is now free for this).
- [ ] Line-follower I2C module connector (replaces the removed floor/line sensors). The home-made line sensor is a 5-sensor reflectance array on an Adafruit ATtiny1616 board running seesaw firmware (analog reads on seesaw pins 0 to 4, I2C address 0x49 by default, which does not clash with the LSM6DS3 at 0x6A). Source: the private repo `nbourre/LyneTracker` (PlatformIO library with calibration, 0..4000 line position and PID, built on `Adafruit seesaw Library`). Its current target is an ATmega2560 (Auriga), so porting to the ESP32-S3 only needs the I2C pins (SDA GPIO 8, SCL GPIO 9, 3.3 V) in `Wire.begin()`. Qwiic J4 is a good fit. Check that the module's pull-ups and supply voltage work at 3.3 V.
- [ ] Update the PCB from the schematic once the board dimensions are known.
