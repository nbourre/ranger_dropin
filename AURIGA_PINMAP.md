# Makeblock Auriga: pin map

Reference so that the schematic (`auriga/Me Auriga Schematic.pdf`, plus the picture `auriga/Pinout-Auriga.svg`) does not need to be read again.
Source: manual reading of the PDF (ATmega2560, `MCU1`). Items marked **(?)** are not certain.
Arduino names are the ones used by the Makeblock library (`D0`..`D53`, `A0`..`A15`).

**Board size (measured): 65.5 × 100 mm, corner radius 2 mm.** This is the target outline for the drop-in PCB. The original has no mounting holes (it is clipped in), only guide-pin holes.

**Guide-pin holes (all Ø 2 mm).** Orientation as in Pinout-Auriga.svg: portrait, USB/reset edge at the top, RJ25 ports 1-5 on the left and 6-10 on the right. Origin = top-left corner, X to the right, Y downward, board 65.5 (X) × 100 (Y) mm:

| Hole | X (mm) | Y (mm) | Description |
|---|---|---|---|
| GH1 | 38.75 | 6 | 26.75 mm from the right edge, 6 mm from the top edge, just below the reset button |
| GH2 | 55.5 | 83.5 | 10 mm from the right edge, 16.5 mm from the bottom, between ports 6 and 7 |
| GH3 | 10 | 83.5 | mirror of GH2 on the left, between ports 4 and 5 |

## 1. Arduino pin → function

### Digital

| Pin | MCU pin | Function on the Auriga |
|---|---|---|
| D0 / RX0 | 2 | USB serial (CH340G), BLE module TX; blue LED (D6) |
| D1 / TX0 | 3 | USB serial (CH340G), BLE module RX; red LED (D9) |
| D2 | 6 | RJ25 **J2** S2 |
| D3 | 7 | RJ25 **J2** S1 |
| D4 | 1 | RJ25 **J1** S2 |
| D5 | 5 | RJ25 **J1** S1 |
| D6 | 15 | RJ25 **J3** S2 |
| D7 | 16 | RJ25 **J3** S1 |
| D8 | 17 | RJ25 **J4** S2 |
| D9 | 18 | RJ25 **J4** S1 |
| D10 | 23 | TB6612 **PWMB** (motor 2 speed) |
| D11 | 24 | TB6612 **PWMA** (motor 1 speed) |
| D12 | 25 | not connected |
| D13 | 26 | on-board LED (D14, blue) |
| D14 / TX3 | 64 | 2.4 GHz / Bluetooth header **P1** (via 51 Ω) |
| D15 / RX3 | 63 | header **P1** (via 51 Ω) |
| D16 / TX2 | 13 | RJ25 **J5** S1, **P_SERVO** pin 2, P_PWM pin 5 (via 51 Ω) |
| D17 / RX2 | 12 | RJ25 **J5** S2, **P_SERVO** pin 1, P_PWM pin 6 (via 51 Ω) |
| D18 / TX1 | 46 | **Motor 2 encoder**, signal ENB_A |
| D19 / RX1 | 45 | **Motor 1 encoder**, signal ENA_A |
| D20 / SDA | 44 | I2C: RJ25 SDA pin on every port, MPU-6050 (via 51 Ω) |
| D21 / SCL | 43 | I2C: RJ25 SCL pin on every port, MPU-6050 (via 51 Ω) |
| D22, D23, D24 | 78, 77, 76 | not connected |
| D25 to D29, D39 | 75 to 71, 70 | not connected (labels only) |
| D30 to D37 | 60 to 53 | header **P_DIGITAL** (EXTENSION3) |
| D38 | 50 | not connected |
| D40, D41 | 52, 51 | header **P_DIGITAL** (EXTENSION3) |
| D42 | 42 | **Motor 1 encoder**, signal ENA_B |
| D43 | 41 | **Motor 2 encoder**, signal ENB_B |
| D44 | 40 | **RGB LED ring** data (`D44/RGB`, RGB1 pin 3) |
| D45 | 39 | **Buzzer** (via R13 → Q1 S9013) |
| D46 | 38 | TB6612 **BIN2** (EN_DIRB2) |
| D47 | 37 | TB6612 **BIN1** (EN_DIRB1) |
| D48 | 36 | TB6612 **AIN1** (EN_DIRA1) |
| D49 | 35 | TB6612 **AIN2** (EN_DIRA2) |
| D50 / MISO | 22 | ICSP header |
| D51 / MOSI | 21 | ICSP header |
| D52 / SCK | 20 | ICSP header |
| D53 / SS | 19 | not connected |

### Analog

| Pin | MCU pin | Function on the Auriga |
|---|---|---|
| A0 | 97 | **Temperature**: NTC RT1 (NCP18XH103F03RB, 10 k) with R12 10 k to 5 V |
| A1 | 96 | **Sound**: electret mic MK1 → LM2904 (U1A, U1B) |
| A2 | 95 | **LIGHT2** (RGB board connector pin 5) |
| A3 | 94 | **LIGHT1** (RGB board connector pin 4) |
| A4 | 93 | **Battery voltage**: R58 100 k / R59 51 k from V-BAT, C48 1 µF (`A4/VOL_BAT`) |
| A5 | 92 | not connected (label `A5/RJ` only) |
| A6 | 91 | RJ25 **J10** S1 |
| A7 | 90 | RJ25 **J9** S1 |
| A8 | 89 | RJ25 **J8** S1 |
| A9 | 88 | RJ25 **J7** S1 |
| A10 | 87 | RJ25 **J6** S1 |
| A11 | 86 | RJ25 **J10** S2 |
| A12 | 85 | RJ25 **J9** S2 |
| A13 | 84 | RJ25 **J8** S2 |
| A14 | 83 | RJ25 **J7** S2 |
| A15 | 82 | RJ25 **J6** S2 |

## 2. RJ25 ports

All ports: pin 1 SCL (D21), pin 2 SDA (D20). Pins 5 and 6 are S1 and S2.

| Port | Type | Pin 3 / Pin 4 | S1 (pin 5) | S2 (pin 6) |
|---|---|---|---|---|
| J1 | RJ25/RED | V-M / GND | D5 | D4 |
| J2 | RJ25/RED | V-M / GND | D3 | D2 |
| J3 | RJ25/RED | V-M / GND | D7 | D6 |
| J4 | RJ25/RED | V-M / GND | D9 | D8 |
| J5 | RJ25 | GND / 5 V | D16 / TX2 | D17 / RX2 (pins 1 and 2 not connected) |
| J6 | RJ25 | GND / 5 V | A10 | A15 |
| J7 | RJ25 | GND / 5 V | A9 | A14 |
| J8 | RJ25 | GND / 5 V | A8 | A13 |
| J9 | RJ25 | GND / 5 V | A7 | A12 |
| J10 | RJ25 | GND / 5 V | A6 | A11 |

- "RED" ports (J1 to J4) carry **V-M** (battery after fuse F02 3.5 A and diode D06) for motors or servos, and have 1 kΩ series resistors on S1 and S2.
- Ports J5 to J10 carry 5 V.
- J1/J2 and J3/J4 are the pairs of the 4 "smart" motor/servo ports.

## 3. Modules and connectors

### RGB LED ring + light sensor board ("Panel Module", RGB1)

Sources: schematic (`auriga/Me Auriga Schematic.pdf`) and the module picture in `auriga/Pinout-Auriga.svg`.

The module has 12 RGB LEDs (WS2812-type, one data line `D44`), a POWER push button in the centre, and two round photoresistors in the top corners (labelled 1 and 2 on the picture: LIGHT SENSOR 1 → A3, LIGHT SENSOR 2 → A2). It plugs into standard 2.54 mm (100 mil) **female** headers on the Auriga: one 1×7 for the signals (PRGB) and two 1×2 for GND (PG1, PG2). The GND headers are also the mechanical support of the module.

**Signal header, left to right as drawn on both the Auriga and the module** (the module faces the same way as the Auriga board in the picture, header along the top edge):

| Position | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Signal | V-BAT | KEY | A2 / LIGHT2 | A3 / LIGHT1 | D44 / RGB | GND | 5 V |

- `KEY` is the module's POWER button, connected to the Auriga power-latch circuit (through D5 / S2). It is not an MCU pin.
- V-BAT is the raw battery voltage; 5 V powers the LEDs.
- GND headers: two vertical 1×2 headers, one near each bottom corner of the module.

**Module geometry (module size and GND spacing measured with a caliper; signal-header offsets measured on the SVG, about ±0.3 mm):**

| Item | Value |
|---|---|
| Module size | 36.1 × 50 mm (caliper, rounded corners), header at the top edge |
| Signal header | 7 pins, centred horizontally on the module |
| Left / right GND headers | 15.875 mm left / right of the centre line (31.75 mm centre to centre; caliper: 34 mm over the male plastic outside − 2.54 = 31.46, 29.2 mm inside + 2.54 = 31.74) |
| Vertical offset, signal header → upper pin of the GND headers | about 42.5 mm |
| Vertical offset, signal header → lower pin of the GND headers | about 45.1 mm (pitch 2.54 mm) |
| Light sensors | top corners, about 16 mm left and right of the centre line, just above the signal header |

The Auriga board holds these same female headers at a fixed position; the footprint on our PCB must reproduce the same relative positions of the 1×7 and the two 1×2.
### Motors (TB6612, U4)

| TB6612 pin | Signal | MCU |
|---|---|---|
| PWMA | EN_PWMA | D11 |
| AIN1 | EN_DIRA1 | D48 |
| AIN2 | EN_DIRA2 | D49 |
| PWMB | EN_PWMB | D10 |
| BIN1 | EN_DIRB1 | D47 |
| BIN2 | EN_DIRB2 | D46 |
| STBY | tied high (5 V) | none |
| AO1/AO2 | M1+ / M1− (to M1 header through ferrite beads and 1 A fuses) | |
| BO1/BO2 | M2+ / M2− (to M2 header) | |

Motor supply: VM = V-M (battery after F02 / D06). Logic VCC = 5 V.

### Motor headers M1 / M2 (MHDR1X6)

| Pin | Signal |
|---|---|
| 6 | Motor + |
| 5 | Motor − |
| 4 | GND |
| 3 | 5 V (encoder supply) |
| 2 | Encoder A |
| 1 | Encoder B |

| Header | Encoder A | Encoder B | MCU pins |
|---|---|---|---|
| M1 (TB6612 channel A) | ENA_A | ENA_B | D19, D42 |
| M2 (TB6612 channel B) | ENB_A | ENB_B | D18, D43 |

Each encoder signal has a 51 Ω series resistor (R36, R37, R41, R42).

### Expansion headers

| Header | Pins |
|---|---|
| **P_DIGITAL** (EXTENSION3, 2×5) | 1 D31, 2 D30, 3 D33, 4 D32, 5 D35, 6 D34, 7 D37, 8 D36, 9 D41, 10 D40 |
| **P_PWM** (EXTENSION1, 1×10) | 10 D4, 9 D5, 8 D2, 7 D3, 6 D17, 5 D16, 4 D6, 3 D7, 2 D8, 1 D9 |
| **P_ANALOG** (EXTENSION2, 1×10) | 10 A10, 9 A15, 8 A9, 7 A14, 6 A8, 5 A13, 4 A7, 3 A12, 2 A6, 1 A11 |
| **P_SERVO** (1×4) | 4 V-M, 3 GND, 2 D16 / TX2, 1 D17 / RX2 |
| **P1** (Header 4, 2.4 GHz / BT) | 1 5 V **(?)**, 2 GND **(?)**, 3 D14 / TX3, 4 D15 / RX3 (5.1 kΩ pull-ups on 3 and 4) |
| **ICSP1** (2×3) | MISO D50, 5 V, SCK D52, MOSI D51, RESET, GND |
| PRT (4 pins) / PPower (3 pins) | replace the BLE module U2 in the BOM |

### On-board functions

| Function | Parts | Connection |
|---|---|---|
| USB / programming | CH340G (U3), USB-B, 16 MHz crystal | D0 / D1 serial, DTR → RESET through 100 nF |
| BLE | U2 module (not in BOM; PRT / PPower headers instead) | D0 / D1 through 51 Ω, reset from DTR (Q3 S8550) |
| Buzzer | LS1, Q1 S9013, D2 1N4148 | D45 |
| Gyro / accelerometer | MPU-6050 (UM9) | I2C D20 / D21; INT and AD0 not connected to the MCU **(?)** |
| Microphone | MK1 + LM2904 | A1 |
| Temperature | NTC RT1 | A0 |
| Battery voltage | R58 / R59 divider | A4 |
| Status LEDs | D6 blue (D0), D9 red (D1), D14 blue (D13), D12 / D13 / D15 / D16 motor LEDs | |
| Reset button | S1 | RESET |
| Power button | S2 + Q2 (P-MOS AOD4185), Q4, Q5 | latches the power; not an MCU input |

### Power

- Battery input: JP1 (DC jack) → V-BAT. Protection: D17 SMAJ13A TVS, D8 1N4148, Q2 reverse protection, F1 1.5 A.
- 5 V: **TPS54331** buck converter (U5), L3 6.8 µH, D10 SS34, D7 SMAJ5.0A.
- V-M: battery through D06 SS54 and F02 3.5 A (motors and RJ25 red ports).
- USB 5 V (VBUS) is OR-ed into 5 V through F2 0.5 A and Q6 CJ3401.
- 3.3 V (UM1 XC6206P332MR) supplies only the MPU-6050.

## 4. Where each Auriga feature lands on the ESP32-S3 board

| Auriga feature | Auriga pin | ESP32-S3 board |
|---|---|---|
| Buzzer | D45 | D8 net → GPIO 47 (LS1) |
| Motor 1 / 2 control | D11, D48, D49 / D10, D47, D46 | TB6612 U3 (see the GPIO table in `README.md`) |
| Encoders | D19, D42 / D18, D43 | GPIO 39, 40, 41, 42 via M1 / M2 |
| I2C | D20 / D21 | GPIO 8 / 9 (A4/SDA, A5/SCL) |
| Battery voltage | A4 | GPIO 3 (`VOL_BAT`) |
| IMU | MPU-6050 (I2C) | LSM6DS3TR-C (I2C 0x6A) |
| Temperature | A0 | GPIO 2 (A1 net) |
| RGB ring | D44 | J12 pin 5 (`RGB`) ← R39 220 Ω ← U7 74AHCT1G125 (3.3 → 5 V) ← GPIO 48 |
| Light sensors | A2 (LIGHT2), A3 (LIGHT1) | J12 pins 3 / 4 → GPIO 4 / GPIO 5 (nets `A2`, `A3`) |
| Panel KEY button | KEY | J12 pin 2 → R38 15k + R37 10k divider → GPIO 14 (active high, ties to V-BAT) |
| Panel V-BAT / 5 V / GND | | J12 pins 1 / 7 / 6; J13, J14 = GND supports |
| RJ25 port A (low-power side) | | J5: SCL, SDA, GND, 5 V, S1 = GPIO 1, S2 = GPIO 15 |
| RJ25 port B | | J6: S1 = GPIO 43, S2 = GPIO 44 (UART0 pins) |
| RJ25 port C | | J7: S1 = D9 (GPIO 38), S2 = D10 (GPIO 10), shared with SPI header J3 |
| Microphone | A1 | not on the board |

RJ25 I2C pins are 3.3 V logic on the new board (5 V on the Auriga). The panel connector J12 is a female 1x7 header and J13 / J14 are female 1x2 headers.
