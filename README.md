# Ranger drop-in: BEAPER Nano carrier for ESP32-S3

Goal: replace the Arduino-based **Makeblock Auriga** controller of an mBot Ranger with a custom carrier board for an **ESP32-S3-DevKitC-1-N16R8**, based on the mirobo.tech **BEAPER Nano** schematic converted to SMD parts (JLCPCB/LCSC, Basic parts where possible).

Project files: KiCad 10 (`Beaper-Esp32s3.kicad_sch`, `Beaper-Esp32s3.kicad_pcb`), custom footprint library `BEAPER-Nano.pretty`, custom symbol library `ESP32S3.kicad_sym`. Reference: `auriga/Me Auriga Schematic.pdf`.

> **Status (2026-10-22):** schematic and PCB are in sync (127 footprints, all on the top side so the board clips into the robot). **Placement is done; routing, ground pours and the final DRC are still to do.** See `memoire/notes-a-faire.md` for the layout, the decisions and the task list, and `memoire/MEMOIRE.md` for the working notes (Konnect MCP tips). Photos of the Auriga are in `auriga/photos/`; extra 3D models are in `3dmodels/`.

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
- Battery input on **J1** (5.5 × 2.1 mm DC barrel jack, centre = VBAT), 7.2 V NiMH RC pack. The old screw terminal CON1 was removed.
- Protection: the battery (net `VBAT`, SMAJ13A TVS D9) splits into two fused branches, as on the Auriga. **Motor branch:** fuse F1 (3.5 A), SS54 diode D8, 470 µF bulk capacitor C8, net `VCC` (TB6612 VM, battery sense, panel V-BAT). **Logic branch:** fuse F2 (3 A, C182445), SS34 diode D13, then the buck U1. A motor stall that blows F1 therefore leaves the logic and servos powered.
- **U1 (TPS54331DDA, 3 A buck, LCSC C90761)** makes the +5 V rail, as on the Auriga (L1 6.8 µH, D10 SS34, 10 k / 1.91 k feedback divider, 470 µF output capacitor). D11 (SS34) isolates the buck from the +5 V rail so that USB power cannot back-feed it (the rail is about 4.7 V), and D12 (SMAJ5.0A) clamps the rail. The DevKitC-1 has no VIN pin, so it is powered through its 5V pin. U1 is therefore **required**.
- 3.3 V comes from the DevKitC-1.
- No on-board USB charger (external charger for the pack).

### Motors
- **U3 TB6612FNG** (SSOP-24, LCSC C141517, Extended part). Replaces the SN754410 of the original design.
- Motor outputs are protected like on the Auriga: TB6612 output → bidirectional TVS SMAJ12CA (D14 to D17) → 120 Ω / 2 A ferrite bead (FB1 to FB4) → 1 A PTC fuse (F3 to F6) → connector.
- **M1 and M2** are **JST PH 6-pin side-entry connectors (2.0 mm pitch, S6B-PH-K)**, as on the Auriga (see `auriga/photos/`): pin 6 motor+, 5 motor−, 4 GND, 3 +3V3, 2 encoder A, 1 encoder B. Pin 1 orientation still has to be checked on a real motor plug.
- Encoder signals go through 51 Ω resistors (R31 to R34) to GPIO 39 to 42. Encoders are powered at **3.3 V** (the Auriga uses 5 V). To be tested with the real motors.
- Difference from the old driver: with both inputs low, the TB6612 coasts (the SN754410 braked). Maximum supply: 13.5 V.

### Sensors and I/O
- **U6 LSM6DS3TR-C** (LCSC C967633): 6-axis IMU on I2C (address 0x6A), interrupts not connected.
- **Battery voltage monitor** (`VOL_BAT`, like the Auriga's A4/VOL_BAT): R35 100 kΩ / R36 51 kΩ divider + C11 1 µF on **GPIO 3** (ADC1_CH2). Ratio 0.338, so a 9 V pack reads about 3.0 V. It is tapped after D8, so it reads about 0.4 V low: calibrate in firmware. GPIO 3 is a strapping pin, which only matters at reset.
- Ambient light sensor (TEPT4400) removed; the Auriga's light module will be reused instead (see TODO).
- Temperature sensor (MCP9700A, on A1), wired directly (no selection jumpers).
- Line / floor sensors and potentiometers were **removed** to free GPIO. As on the Auriga, line-following is done by an external I2C module (home-made: Adafruit ATtiny1616 with seesaw firmware, sensors wired to the ATtiny) on the Qwiic connector (J4) or H1/H4.
- Headers H1 (A4 / SDA) and H4 (A5 / SCL): I2C signals at 3.3 V. The sonar headers H2/H3 were removed.
- Headers H7 (A6 / GPIO 6) and H8 (A7 / GPIO 7): 5 V servo outputs through the **74HCT541** level shifter (U2) for the pan/tilt micro servos (H5/H6 removed). Generate the servo PWM with LEDC.
- I2C expansion on the main 3.3 V bus: two Qwiic / JST-SH connectors (J4, J8) and three generic 4-pin headers (J9, J15, J16: GND, +3V3, SCL, SDA). SPI / TFT connector (J3).
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
- **J5, J6, J7** RJ25 (Amphenol 54601-906WPLF, 6P6C), low-power side only: 1 SCL, 2 SDA, 3 GND, 4 +5 V, 5 S1, 6 S2. They behave like the Auriga ports (**5 V**): the six S1/S2 signals go through BSS138 level shifters (Q3 to Q8, 10 k pull-ups R45 to R56), and the port supply is `5V_P` (buck output before D11). The RJ25 I2C bus (EXT_SCL / EXT_SDA, through Q1/Q2) has its pull-ups on 3.3 V or 5 V, selected with **JP1** (1-2 = 3.3 V, 2-3 = 5 V, Makeblock setting). Digital only (no 0–5 V analog); port B uses GPIO 43/44 (UART0); port C shares D9/D10 with the SPI header J3. The jacks have the contacts on top (the Auriga's are at the bottom): the cable just has to be twisted, the pinout is the same.
- **J4, J8** Qwiic (JST-SH 4-pin: GND, 3V3, SDA, SCL); **J9, J15, J16** generic I2C headers.
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
- Qwiic / JST-SH I2C connectors (J4, J8) and generic I2C headers (J9, J15, J16).
- VL53L1X module socket (J10) and OLED I2C socket (J11).
- I2C headers H1 / H4 (3.3 V) and servo headers H7 / H8 (5 V outputs).
- Onboard user buttons were removed; the user button is planned on the panel module `KEY` pin (see TODO).
- Four simple status LEDs.
- Wi-Fi and BLE through the ESP32-S3, with native USB.

### In both
Buzzer, temperature sensor, IMU, battery voltage sensing, motors with encoders, battery protection, reset button, servo outputs.

---

## 4. Open items
- **5 V supply:** done. The LM2940 was replaced by a TPS54331 3 A buck, and C7 (470 µF) sits near the servo headers. Use 5 V micro servos (9 g) and generate the servo signals with LEDC. The buck has its own fuse F2 and reverse diode D13, separate from the motor fuse F1. The motor outputs have their own TVS, ferrite and 1 A PTC fuse (done).
- The DevKitC-1 footprint outline is approximate (pad envelope only), and it has no 3D model yet.
- Missing LCSC references: F1, D8, D9, C8 (470 µF probably not stocked), R31 to R36, R45 to R56, C9 to C12, M1/M2 (S6B-PH-K-S), U7, RJ25, Qwiic. The 5.62 kΩ and 1.37 kΩ resistors are Extended only.
- Routing, ground pours, silkscreen clean-up and the final DRC are not done. The motor lines are long (U3 near the top, M1/M2 at the bottom edge).
- Missing 3D models: L1 (Bourns SRP7028A), SW1 (Alps SKRTLAE010), U5, G1. The RJ25 model is in `3dmodels/`.
- Optional additions to match the Auriga: power switch.
- The title block comment 3 still says "for Arduino Nano ESP32".
- The schematic page was enlarged from B to C to make room for the IMU.
- ERC: 0 errors, 58 warnings (library symbol mismatches, missing `Conn_01x03_Male`, `ARPS` and `UBMP4.1-rescue` libraries, same local/global label names, one U6 SDO pin type conflict). Leftover wires, orphan power symbols and floating labels were cleaned.

---

## 5. TODO
- [x] **Distance sensor** VL53L1X: socket J10 on the I2C bus (Amazon module, order VIN, GND, SCL, SDA, GPIO1, XSHUT; last two not connected). Must face the same way as the Auriga motor connectors at placement.
- [x] **Auriga panel module** (RGB ring + light sensors): J12 (1x7 female), J13/J14 (1x2 GND supports), level-shifted data (U7). See `AURIGA_PINMAP.md` for the geometry to reproduce at placement (module 36.1 × 50 mm, GND headers 31.75 mm apart).
- [x] Panel KEY used as the general button (active high, divider to GPIO 14). Board buttons SW2 to SW5 removed.
- [x] 3 RJ25 ports (low-power side, 5 V with level shifters), 2 Qwiic connectors and 3 generic I2C headers.
- [x] PCB outline (65.5 × 100 mm, R2) and the three Ø 2 mm guide holes.
- [x] `update_pcb_from_schematic` and component placement (everything on the top side).
- [ ] Routing, ground pours, silkscreen clean-up, final ERC / DRC, 3D check.
- [ ] **Mount the DevKit (U5) on "double" female headers: 2x22 instead of 1x22 per side.** One row receives the DevKit pins, the parallel extra row (wired pin to pin, preferably on the outer side) gives access to every DevKit pin for measurements, jumper wires and other DevKit variants. Likely a custom U5 footprint with two pads per pin number. Check the width (22.86 mm + 2 × 2.54 mm on a 65.5 mm board), the neighbours (J3, J11, the H column) and the height budget under the panel module (about 8.5 mm). Do this first: it makes the next item mostly unnecessary.
- [ ] **Breakout header for GPIO 35, 36 and 37.** These pins are reserved by the **octal PSRAM** ("R8" variants: N16R8, N8R8), whatever the flash size. They are free on variants without octal PSRAM that share the same footprint (N8R2 with quad PSRAM, N8 / N4 without PSRAM), so a 1x03 header would only be useful with one of those (to be confirmed against the Espressif module datasheet). Label it on the silkscreen ("without octal PSRAM only") and update the GPIO table if used.
- [ ] Confirm the OLED module pinout (J11 is an assumed order).
- [ ] LCSC references for the new parts (connectors, U7, R37 to R39, C12).
- [ ] Line-follower I2C module (home-made, Adafruit ATtiny1616 with seesaw, address 0x49) on a Qwiic connector. Source: `nbourre/LyneTracker` (target ATmega2560; porting only needs the I2C pins GPIO 8/9, 3.3 V). Check pull-ups and supply at 3.3 V.
- [ ] **Makeblock mounting holes:** nominally 8 mm pitch, M4; measure on a real beam.
