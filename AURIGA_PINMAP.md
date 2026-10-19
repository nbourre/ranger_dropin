# Makeblock Auriga: pin map

Reference so that the schematic (`Me Auriga Schematic.pdf`) does not need to be read again.
Source: manual reading of the PDF (ATmega2560, `MCU1`). Items marked **(?)** are not certain.
Arduino names are the ones used by the Makeblock library (`D0`..`D53`, `A0`..`A15`).

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

### RGB LED ring + light sensor board (RGB1, "RGB_SCREEN")

The module replaces PG1 / PG2 / PRGB in the BOM. Connector pinout:

| Pin | Signal |
|---|---|
| 1 | 5 V |
| 2 | GND |
| 3 | `D44/RGB` (LED data) |
| 4 | `A3/LIGHT1` |
| 5 | `A2/LIGHT2` |
| 6 | `KEY` (power-key signal, **(?)** probably not an MCU pin) |
| 7 | V-BAT |
| 8 to 11 | GND |

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
| RGB ring, light sensors | D44, A2, A3 | not yet (TODO) |
| Microphone | A1 | not on the board |
| RJ25 ports | | not on the board (2.54 mm headers + Qwiic) |
