<overview>
The user is converting a KiCad 10 project (BEAPER Nano, a mirobo.tech educational robot board) from through-hole to SMD parts, using JLCPCB/LCSC Basic parts where possible. The board becomes a carrier for an **ESP32-S3-DevKitC-1-N16R8** that replaces the Makeblock mBot Ranger's Arduino "Auriga" controller. I edit the schematic with the Konnect MCP tools (KiCAD-MCP-Konnect). The user writes in French, so I reply in French and concisely. The README and the pin-map document are in English at the user's request. PCB layout is deferred until the user gives board dimensions.

The latest turn: the user moved the Auriga files into `auriga\` (the PDF and `Pinout-Auriga.svg`) and said the "Panel Module" picture in the SVG shows the module's header layout. I read it and documented the geometry. I had just finished the document edits and had not yet reported back to the user.
</overview>

<history>
1. **Konnect MCP configuration help**, then **through-hole to SMD conversion** (schematic first).
   - Resistors set to 0603, small capacitors to 0402, LEDs to 0603.
   - Replaced the SN754410 with a TB6612FNG (U3).
   - Added battery protection: F1 3.5 A fuse, D8 SS54, D9 SMAJ13A TVS, C8 470 µF. The user chose no USB charger.

2. **Replaced the Nano ESP32 socket with the DevKitC-1.**
   - Custom symbol `ESP32S3:ESP32-S3-DevKitC-1` and custom footprint.
   - Wired as U5. Hit ERC errors on power pins and fixed them with 3 PWR_FLAGs.

3. **Added motor connectors M1/M2** (MHDR1X6, as on the Auriga). Encoders go to GPIO 39 to 42 through 51 Ω resistors R31 to R34.

4. **Q&A (answered in French).**
   - The 5 V LDO (U1) is still required, because the DevKitC-1 has no VIN.
   - A pan/tilt with 2 servos needs a 5 V / 3 A buck. This was saved in the notes.

5. **Auriga vs Beaper feature review**, then an **IMU** and a **battery monitor**.
   - Added the LSM6DS3TR-C (U6, I2C 0x6A, LCSC C967633).
   - The schematic page was enlarged to size C.
   - Added the `VOL_BAT` divider: R35 100k and R36 51k with C11 1 µF, on GPIO3. It is wired and verified.
   - Created `README.md` in English.

6. **The user asked to free pins.** Removed the floor/line sensors, the potentiometers and the jumpers.
   - Removed: Q1 to Q3, D6, D7, R20 to R24, H9 to H12, RV1, RV2, R25, R26, JP1 to JP4.
   - A2/A3 (GPIO4/5) are now free, with no-connects on U5 L4 and L5.
   - The only ERC errors were dangling wires and labels, and I deleted them all. ERC is now 0 errors.

7. **Strapping-pin question.** I explained that GPIO 0, 3, 45 and 46 are read only at reset.

8. **The user asked for a TODO section in the README and for the TEPT4400 light sensor to be removed.**
   - Removed Q4, R18 and the A0 labels; U5 R4 (GPIO1) now has a no-connect. ERC is 0 errors.
   - Added "5. TODO" to the README: a VL53L1X distance sensor, the Auriga RGB ring module, the Auriga light module, a line-follower I2C module, and the PCB update.

9. **Line sensor note.** The user's home-made line sensor is an Adafruit ATtiny1616 with seesaw firmware, read over I2C.
   - The repo `nbourre/LyneTracker` is private. I read it with `gh repo clone` and deleted the clone afterwards.
   - It has 5 sensors on seesaw analog pins 0 to 4, default I2C address 0x49, a PID library, and an ATmega2560 target.
   - Recorded in the README.

10. **The user asked for a pin-mapping document of the Auriga.**
    - Rendered the PDF with PyMuPDF at high DPI and read it visually.
    - Created `AURIGA_PINMAP.md` at the root. It covers: Arduino pin → function tables for D and A pins, the RJ25 ports J1 to J10, the RGB/light module, the motors (TB6612), the M1/M2 headers, the expansion headers, the on-board functions, the power section, and an "Auriga → ESP32-S3 board" table.
    - Added a link to it in the README.

11. **The user said the RGB/light module uses a standard 7-pin 100-mil female header on the Auriga, plus two 2-pin female headers for GND that also act as support.** I recorded this in the pin map and the README TODO.

12. **Latest: the user moved the files into `auriga\` and pointed to the "Panel Module" in `Pinout-Auriga.svg`.**
    - Rendered the SVG with `fitz` (ImageMagick failed because of fonts) and zoomed in on the module and on the board's 7-pin header.
    - Rewrote the RGB module section of `AURIGA_PINMAP.md`.
    - Updated the PDF path references in `README.md` and `AURIGA_PINMAP.md` to `auriga/Me Auriga Schematic.pdf`.
    - The README RGB/light TODO bullets are not yet updated with the new geometry.
</history>

<work_done>
Files created or modified:
- `BEAPER-Nano.kicad_sch`: all schematic changes above. ERC is 0 errors with about 90 old warnings.
- `README.md`: English documentation with four sections plus "5. TODO" (VL53L1X, RGB ring, light module, line-follower, PCB update). PDF paths now point to `auriga/`.
- `AURIGA_PINMAP.md`: the full Auriga pin map, with the new "Panel Module" section (geometry and header order).
- `ESP32S3.kicad_sym`, `sym-lib-table` and `BEAPER-Nano.pretty\ESP32-S3-DevKitC-1.kicad_mod`: custom DevKitC-1 library, created earlier.
- Session `files\notes-a-faire.md` and `after*.net` netlists (the last is `after14.net`).
- Temp files from the SVG/PDF renders (`pin_full.png`, `panel.png`, `hdr.png`) are still in `%TEMP%`; they need cleanup.

Completed:
- [x] Schematic: SMD, TB6612, protection, DevKitC-1, M1/M2, IMU, VOL_BAT.
- [x] Removal of the floor/line sensors, potentiometers, jumpers and the TEPT4400.
- [x] README and pin map.
- [x] Panel module geometry documented.

Not done:
- [ ] Report the SVG findings to the user in French.
- [ ] README TODO bullets for the RGB ring/light module: update with the correct header order and geometry.
- [ ] PCB update.
- [ ] LCSC refs.
- [ ] 5 V / 3 A buck to replace the LM2940.
- [ ] Title block comment 3 still says "for Arduino Nano ESP32".
- [ ] Delete the temp PNGs.
</work_done>

<technical_details>
**Free GPIO now:** 1 (ex A0), 4 (ex A2), 5 (ex A3) and 48 (also the on-board RGB LED). GPIO 45, 46 and 0 are strapping pins. GPIO 3 is used by VOL_BAT. 19/20 are USB. 35/36/37 are used by the PSRAM.

**Current GPIO map:**

| Net | GPIO | Net | GPIO |
|---|---|---|---|
| A1 (MCP9700A temperature) | 2 | D5 | 17 |
| A4/SDA | 8 | D6 | 18 |
| A5/SCL | 9 | D7 | 21 |
| A6 | 6 | D8 (buzzer) | 47 |
| A7 | 7 | D9 | 38 |
| D0/RX0 (SW2) | 44 | D10 | 10 |
| D1/TX0 (SW3) | 43 | D11/COPI | 11 |
| D2 (SW4) | 14 | D12/CIPO | 13 |
| D3 (SW5) | 15 | D13/SCK | 12 |
| D4 | 16 | VOL_BAT | 3 |
| Encoders | 39, 40, 41, 42 | RST | EN |

**DevKitC-1 pinout (symbol):**
- Left row: L1 3V3, L2 3V3, L3 RST, L4 GPIO4, L5 GPIO5, L6 GPIO6, L7 GPIO7, L8 GPIO15, L9 GPIO16, L10 GPIO17, L11 GPIO18, L12 GPIO8, L13 GPIO3, L14 GPIO46, L15 GPIO9, L16 GPIO10, L17 GPIO11, L18 GPIO12, L19 GPIO13, L20 GPIO14, L21 5V, L22 GND.
- Right row: R1 GND, R2 GPIO43, R3 GPIO44, R4 GPIO1, R5 GPIO2, R6 GPIO42, R7 GPIO41, R8 GPIO40, R9 GPIO39, R10 GPIO38, R11 GPIO37, R12 GPIO36, R13 GPIO35, R14 GPIO0, R15 GPIO45, R16 GPIO48, R17 GPIO47, R18 GPIO21, R19 GPIO20, R20 GPIO19, R21 GND, R22 GND.
- U5 is at (60.96, 27.94). Left pins are at x=46.99, right pins at x=74.93.

**Auriga RGB/light "Panel Module" (from the SVG and the schematic):**
- Connector on the Auriga: a 7-pin 2.54 mm female header, plus two 1×2 female GND headers that also give mechanical support.
- Signal order, left to right as drawn: **V-BAT, KEY, A2/LIGHT2, A3/LIGHT1, D44/RGB, GND, 5V**. This is the reverse of the earlier pin numbering (pin1=5V…pin7=VBAT), which was the same sequence read in the other direction.
- KEY is the module's POWER button, wired into the Auriga power-latch circuit through D5 and S2. It is not an MCU pin.
- 12 WS2812-type RGB LEDs on one data line. Two round photoresistors in the top corners (1 = LIGHT1/A3, 2 = LIGHT2/A2).
- Measured on the SVG using the 2.54 mm pitch as scale (about ±0.3 mm, to be confirmed with a caliper or photo):
  - Module size about 36.8 × 50.8 mm.
  - The signal header is on the top edge, centred horizontally.
  - The GND headers are about ±15.9 mm from the centre line (about 31.75 mm apart).
  - Vertical offset from the signal header to the GND headers: about 42.5 mm (upper pin) and 45.1 mm (lower pin).
- Ideas for the ESP32-S3 board:
  - Drive the data line from GPIO 48, or 4/5.
  - A 3.3 V → 5 V level shifter may be needed. The board's 74HCT541 (U2) may have spare channels, but I did not check this.
  - LIGHT1/LIGHT2 need 2 ADC-capable GPIOs. GPIO1 and GPIO4/5 are free, and the ADC1/ADC2 constraint on Wi-Fi has not been checked.
  - V-BAT and KEY would be passed through.

**Auriga key facts:**
- Battery voltage divider on A4 (R58 100k / R59 51k, C48 1 µF).
- Encoders: M1 uses D19 and D42, M2 uses D18 and D43. Encoders are powered at 5 V on the Auriga.
- TB6612: PWMA=D11, AIN1=D48, AIN2=D49, PWMB=D10, BIN1=D47, BIN2=D46.
- Buzzer is on D45, the RGB ring on D44, the temperature NTC on A0, the sound sensor on A1, the MPU-6050 on I2C D20/D21.
- 5 V comes from a TPS54331 buck converter.
- RJ25 ports J1 to J4 are "RED" and carry V-M; J5 to J10 carry 5 V.
- Some items in `AURIGA_PINMAP.md` are marked **(?)**: P1 pin order, MPU INT/AD0 connections, and the exact role of the KEY signal.

**Line sensor:** an Adafruit ATtiny1616 board running seesaw, address 0x49 (no clash with the IMU at 0x6A). The LyneTracker library targets an ATmega2560. For the ESP32-S3 only `Wire.begin()` needs the SDA/SCL pins. 3.3 V pull-ups and supply are to be checked.

**Power:** U1 (LM2940, 1 A) feeds +5V. A 5 V / 3 A buck is needed for the pan/tilt servos. USB + battery back-feed has not been verified. Encoders are at 3.3 V (the Auriga uses 5 V), to be tested.

**Konnect tool quirks:**
- The schema is learned by calling a tool with missing arguments.
- `delete_schematic_net_label` takes `net`, `schematic`, `x`, `y`.
- `batch_connect_to_net` takes top-level `net_name`, `schematic` and `pins:[{reference, pin_number}]`. It adds labels at the pin ends.
- `batch_delete` takes `uuids`. `batch_delete_schematic_components` takes `references`. `batch_add_no_connect` and `batch_delete_no_connect` take `positions:[{x,y}]`.
- Konnect refuses writes while KiCad has the schematic open.
- After deleting components, dangling wires and labels remain. Clean them with ERC → `batch_delete` of the uuids → ERC, repeating until clean.
- ERC output is saved to a temp JSON file; parse it with Python and use the specific file name.
- Netlist parsing in Python: split on `\n\t\t(net\n`, then use the regex `\(ref "([^"]+)"\)\s*\(pin "([^"]+)"`.
- Several tool calls in the same batch run in parallel. Do not chain a file-producing call and a view of its result in the same batch.
- ImageMagick cannot render the SVG (font issue). `fitz` (PyMuPDF) can open and render both SVG and PDF.
- kicad-cli is not in PATH.
- The jlcsearch API (`jlcsearch.tscircuit.com`) replaces the broken `search_jlcpcb_parts`.

**Known ERC warnings (old, ignore):** lib_symbol_mismatch, missing `Conn_01x03_Male` and `ARPS` libraries, same-name local/global labels, one dangling wire end.
</technical_details>

<important_files>
- `D:\_data\projets\_cegep\1sx\ranger_dropin\BEAPER-Nano.kicad_sch`
  - Main schematic, page C.
  - Contains U5, U6, U3, M1/M2, F1, D8, D9, C8 to C11, R31 to R36.
  - U1 and U4 (MCP9700A on A1) are unchanged.
- `D:\_data\projets\_cegep\1sx\ranger_dropin\README.md`
  - English documentation: Auriga features, Beaper features and GPIO table, comparison, open items, and "5. TODO".
  - Still to do: update the RGB/light TODO bullets (lines about the "Reuse the Auriga's RGB LED ring module" and the "light module") with the final header order and geometry.
- `D:\_data\projets\_cegep\1sx\ranger_dropin\AURIGA_PINMAP.md`
  - Pin-by-pin map of the Auriga, so that the schematic does not need to be read again.
  - The RGB module section (`### RGB LED ring + light sensor board ("Panel Module", RGB1)`) was just rewritten.
- `D:\_data\projets\_cegep\1sx\ranger_dropin\auriga\Me Auriga Schematic.pdf` and `auriga\Pinout-Auriga.svg`
  - Moved here by the user.
  - The SVG has the pinout diagram, with the Panel Module image in the top-right area (render crop about Rect(880,185,1090,475), the board header about Rect(430,255,650,330), at 500 dpi).
- `D:\_data\projets\_cegep\1sx\ranger_dropin\ESP32S3.kicad_sym`, `sym-lib-table` and `BEAPER-Nano.pretty\ESP32-S3-DevKitC-1.kicad_mod`
  - The custom DevKitC-1 symbol and footprint.
- `D:\_data\projets\_cegep\1sx\ranger_dropin\BEAPER-Nano.kicad_pcb`
  - Old PCB, not updated. It is open in KiCad with user changes.
- `C:\Users\nicol\.copilot\session-state\41f4b332-d886-444f-8613-d4b14432f684\files\notes-a-faire.md`
  - Open-items notes (buck converter, LCSC refs).
- `C:\Users\nicol\.copilot\instructions\basic_instructions.md.instructions.md`
  - Québécois French punctuation rules for French markdown. They do not apply to the English README.
</important_files>

<next_steps>
Immediate:
1. Update the README TODO bullets for the RGB ring and light module with the verified header order (V-BAT, KEY, A2/LIGHT2, A3/LIGHT1, D44/RGB, GND, 5V, left to right) and the approximate geometry, and point to `AURIGA_PINMAP.md`.
2. Delete the temp renders (`%TEMP%\pin_full.png`, `panel.png`, `hdr.png`).
3. Reply to the user in French, concisely:
   - Summarize what I read in the SVG: the 7-pin order, the two 1×2 GND headers at the bottom corners, the approximate dimensions, and the KEY = POWER button.
   - Say that the measurements are approximate and need confirming with a caliper or a photo.
   - Ask whether to add the footprint and connectors now or wait for the PCB dimensions.
   - Note the open GPIO question: GPIO48 for D44, and 2 ADC pins for LIGHT1/LIGHT2 (GPIO1, 4, 5 are free).

Later or pending the user:
- Add the schematic part: a 1×7 female header (PRGB) plus two 1×2 GND headers (PG1, PG2) with a custom footprint matching the module geometry, and a level shifter for the data line.
- Add a VL53L1X sensor (I2C) and a line-follower I2C connector (Qwiic J4 may be enough).
- Replace U1 (LM2940) with a 5 V / 3 A buck from JLCPCB.
- Update the PCB once the board dimensions are known (`update_pcb_from_schematic`). The DevKitC-1 footprint outline is approximate.
- Add LCSC refs for F1, D8, D9, C8 (probably out of stock), R31 to R36, C9 to C11, M1/M2.
- Decide whether to keep CON1 pins 3 to 6 (now redundant with M1/M2).
- Fix the title block comment 3 ("for Arduino Nano ESP32").
- Optional additions to match the Auriga: power switch, microphone.
</next_steps>