# À faire / en suspens (BEAPER Nano -> DevKitC-1)

## Alimentation 5 V (pan/tilt avec 2 servos)
- Le LM2940 (U1, 1 A, TO-220) ne suffit pas : 2 servos (pointes 1 à 1,4 A) + ESP32-S3 (~300 mA).
- Remplacer par un buck 5 V / 3 A sur le rail +5V (DevKit, 74HCT541, headers H5-H8, anneau RGB, ports RJ25).
- Ajouter ~470 uF près des headers servo. Servos 5 V seulement.
- Chercher une réf. JLCPCB (Basic si possible, sinon en stock) + passifs, puis remplacer U1.
- Signaux servo via 74HCT541 (5 V) : générer le PWM par LEDC.

## PCB
- Placement des composants (il manque des pièces), puis `update_pcb_from_schematic`.
- Reproduire la géométrie du module panneau (1x7 + 2 x 1x2 GND) et placer les RJ25 / Qwiic sur le bord.
- VL53L1X (J10) orienté comme les connecteurs moteur de l'Auriga.
- Trous de fixation Makeblock : mesurer sur une vraie poutre (nominal 8 mm, M4).
- Enregistrer le PCB dans KiCad (contour et trous de guidage faits par IPC).

## Autres points ouverts
- Confirmer le brochage du module OLED (J11 supposé).
- Refs LCSC manquantes : F1, D8, D9, C8, R31-R39, C9-C12, M1/M2, U7, RJ25, Qwiic, supports.
- Encodeurs moteurs alimentés en 3,3 V (Auriga : 5 V) : à tester ; sinon diviseur sur GPIO 39-42.
- CON1 : broches moteur 3-6 redondantes avec M1/M2.
- Retour d'alimentation possible du LM2940 si USB + batterie en même temps (non vérifié).
- Commentaire 3 de la page de titre mentionne encore « Arduino Nano ESP32 ».
- Firmware : GPIO14 (KEY) en entrée sans pull-up interne, actif haut.
- Optionnel : MCP23017 si plus de GPIO nécessaires.
