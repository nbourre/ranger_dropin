# Ranger drop-in: BEAPER Nano carrier for ESP32-S3

Goal: replace the Arduino-based **Makeblock Auriga** controller of an mBot Ranger with a custom carrier board for an **ESP32-S3-DevKitC-1-N16R8**, based on the mirobo.tech **BEAPER Nano** schematic converted to SMD parts (JLCPCB/LCSC, Basic parts where possible).

Project files: KiCad 10 (`BEAPER-Nano.kicad_sch`, `BEAPER-Nano.kicad_pcb`), custom footprint library `BEAPER-Nano.pretty`, custom symbol library `ESP32S3.kicad_sym`. Reference: `auriga/Me Auriga Schematic.pdf`.

> **Status:** schematic is updated (ERC: 0 errors). The PCB has the new outline (65.5 × 100 mm, R2) and the three guide holes; components are **not** placed yet (the old footprints are still on the board).

---

## 1. Makeblock Auriga (original controller)

Source: `auriga/Me Auriga Schematic.pdf` (one page, read as text). Items marked *(memory)* are not visible in that PDF and come from general knowledge of the mBot Ranger. The full pin-by-pin map is in [AURIGA_PINMAP.md](AURIGA_PINMAP.md).

**Board size (measured): 65.5 × 100 mm, corner radius 2 mm** (target outline for the drop-in PCB). The original has no mounting holes (clipped in).

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
- Piezo buzzer (LS1), 4 status LEDs (D2 to D5), reset button (SW1).

### GPIO mapping (Arduino-style net name → ESP32-S3 GPIO)

| Net | GPIO | Net | GPIO |
|---|---|---|---|
| PA_S1 (RJ25 A) | 1 | D5 | 17 |
| A1 | 2 | D6 | 18 |
| A2 (LIGHT2) | 4 | D7 | 21 |
| A3 (LIGHT1) | 5 | D8 (buzzer) | 47 |
| A6 | 6 | D9 (J3, RJ25 C) | 38 |
| A7 | 7 | D10 (J3, RJ25 C) | 10 |
| A4/SDA | 8 | D11/COPI | 11 |
| A5/SCL | 9 | D12/CIPO | 13 |
| PB_S2 (RJ25 B) | 44 | D13/SCK | 12 |
| PB_S1 (RJ25 B) | 43 | ~{RST} (SW1) | EN |
| KEY_GPIO | 14 | Encoders | 39, 40, 41, 42 |
| PA_S2 (RJ25 A) | 15 | RGB_3V3 (ring data) | 48 |
| D4 | 16 | VOL_BAT | 3 |

No free GPIO is left. **45, 46, 0** are strapping pins (unused, usable with care). **19, 20** are USB D−/D+. **35, 36, 37** are used by the octal PSRAM and must stay unused. GPIO 43/44 are the UART0 pins of the DevKitC-1 USB-UART bridge: a module on RJ25 port B may conflict while that USB port is connected.

### Panel module, RJ25, Qwiic and expansion connectors
- **J12** PRGB (female 1x7, left to right): V-BAT (`VCC`), KEY, A2/LIGHT2, A3/LIGHT1, RGB, GND, 5 V. **J13, J14**: female 1x2 GND supports.
- **KEY** is active high: the module button ties KEY to V-BAT (measured with a multimeter). R38 15k / R37 10k to GND divide it to under 3.4 V on GPIO 14. Configure GPIO 14 as input with no internal pull-up.
- **RGB ring data:** GPIO 48 → U7 74AHCT1G125 (3.3 V → 5 V buffer) → R39 220 Ω → J12.5.
- **J5, J6, J7** RJ25 (6P6C), low-power side only: 1 SCL, 2 SDA, 3 GND, 4 +5 V, 5 S1, 6 S2. I2C is 3.3 V logic (5 V on the Auriga); a module with 5 V pull-ups may be a problem. Port C shares D9/D10 with the SPI header J3.
- **J8, J9** extra Qwiic (JST-SH 4-pin: GND, 3V3, SDA, SCL), same as J4.
- **J10** VL53L1X module (Amazon board, silkscreen order): 1 VIN (3.3 V), 2 GND, 3 SCL, 4 SDA, 5 GPIO1 (not connected), 6 XSHUT (not connected). On placement it must point the same way as the Auriga motor connectors.
- **J11** OLED I2C socket, assumed order GND, 3V3, SCL, SDA (module not yet chosen, to confirm).

---

## 3. Comparison

### On the Auriga but missing on the new board
- 12-LED ring itself and the light sensors: the Auriga **panel module is reused** through J12 to J14 (the ring data line is level-shifted from GPIO 48).
- Microphone and amplifier.
- Power switch.
- RJ25 ports: only 3 low-power ports (J5 to J7) are provided, no motor-power side.
- Dedicated Bluetooth / 2.4 G socket. Wi-Fi and BLE are built into the ESP32-S3.

### On the new board but not on the Auriga
- SPI / TFT connector (J3).
- Qwiic / JST-SH I2C connectors (J4, J8, J9).
- VL53L1X module socket (J10) and OLED I2C socket (J11).
- Headers H1 to H4 (3.3 V analog/digital or sonar) and H5 to H8 (5 V outputs).
- Onboard user buttons were removed; the user button is planned on the panel module `KEY` pin (see TODO).
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
- ERC: 0 errors, 58 warnings (library symbol mismatches, missing `Conn_01x03_Male`, `ARPS` and `UBMP4.1-rescue` libraries, same local/global label names, one U6 SDO pin type conflict). Leftover wires, orphan power symbols and floating labels were cleaned.

---

## 5. TODO
- [x] **Distance sensor** VL53L1X: socket J10 on the I2C bus (Amazon module, order VIN, GND, SCL, SDA, GPIO1, XSHUT; last two not connected). Must face the same way as the Auriga motor connectors at placement.
- [x] **Auriga panel module** (RGB ring + light sensors): J12 (1x7 female), J13/J14 (1x2 GND supports), level-shifted data (U7). See `AURIGA_PINMAP.md` for the geometry to reproduce at placement (module 36.1 × 50 mm, GND headers 31.75 mm apart).
- [x] Panel KEY used as the general button (active high, divider to GPIO 14). Board buttons SW2 to SW5 removed.
- [x] 3 RJ25 ports (low-power side) and 2 extra Qwiic connectors.
- [x] PCB outline (65.5 × 100 mm, R2) and the three Ø 2 mm guide holes.
- [ ] Component placement on the PCB, then `update_pcb_from_schematic` (waiting for the remaining parts).
- [ ] Confirm the OLED module pinout (J11 is an assumed order).
- [ ] LCSC references for the new parts (connectors, U7, R37 to R39, C12).
- [ ] Line-follower I2C module (home-made, Adafruit ATtiny1616 with seesaw, address 0x49) on a Qwiic connector. Source: `nbourre/LyneTracker` (target ATmega2560; porting only needs the I2C pins GPIO 8/9, 3.3 V). Check pull-ups and supply at 3.3 V.
- [ ] **Makeblock mounting holes:** nominally 8 mm pitch, M4; measure on a real beam.
