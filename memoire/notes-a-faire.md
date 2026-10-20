# À faire / en suspens (BEAPER Nano -> DevKitC-1)

## Alimentation 5 V (pan/tilt avec 2 servos)
- FAIT (2026-10-19) : le LM2940 est remplacé par un buck TPS54331 (U1, 3 A, même puce que l'Auriga). Bloc à droite de la feuille (x 430-540, y 200-240 mm). Servos : micro 9 g (blocage ~0,7 A chacun), batterie NiMH 7,2 V.
- Circuit repris de l'Auriga : diviseur 10k/1,91k (5,0 V), L1 6,8 µH/4,5 A, SS34, 470 µF de sortie, compensation 30k + 120 pF en série et 68 pF (valeurs de l'Auriga avec condensateur électrolytique ; à revalider avec la fiche technique si la sortie change).
- D11 (SS34) isole la sortie du buck du rail +5V (pas de retour de courant quand l'USB du DevKit est branché ; chute ~0,3 V : le rail +5V vaut ~4,7 V). D12 : TVS SMAJ5.0A sur +5V. C7 (près des headers servo) passé à 470 µF.
- FAIT : fusibles séparés comme l'Auriga. Le net VBAT (batterie après la TVS D9) alimente F1 3,5 A → D8 → VCC (moteurs, VM du TB6612) et F2 3 A (C182445) → D13 SS34 → entrée du buck. FAIT aussi : protection des sorties moteur comme l'Auriga (bloc en bas à droite, x 425-455, y 245-305 mm) : sortie du TB6612 (nets M1A_D, M1B_D, M2A_D, M2B_D) → TVS SMAJ12CA vers GND (D14-D17) → perle 120 Ω/2 A (FB1-FB4) → fusible PTC 1 A (F3-F6) → nets M1A/M1B/M2A/M2B (CON1 et M1/M2). TVS D9 (SMAJ13CA) et D12 (SMAJ5.0CA) passées en bidirectionnelles : le symbole D_TVS est bidirectionnel et l'ancienne SMAJ13A unidirectionnelle aurait eu sa cathode du mauvais côté.
- Datasheets principaux dans `datasheets/` (TPS54331, TB6612FNG, 74HCT541, 74AHCT1G125, MCP9700A, ESP32-S3 + schéma DevKitC-1, VL53L1X). Manque : LSM6DS3TR-C (st.com bloque le téléchargement automatique).
- À faire : le cadre pointillé « Optional 5V LDO » (x 25-86, y 150-193 mm) est vide et son titre est périmé ; D1/R2 (LED Vin) y est resté.
- Signaux servo via 74HCT541 (5 V) : générer le PWM par LEDC.
- Vérifier : EN du TPS54331 laissé flottant (actif par défaut) ; rendre les valeurs R41 1,91 k (Extended) et C13 10 µF/50 V (Basic) ; L1 = HCMA-0630-6R8 (C54431702, Extended). C8, C7 et C17 : LCSC C18221527 (470 µF 8×10,2 mm) à confirmer.

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
- Commentaire 3 de la page de titre mentionne encore « Arduino Nano ESP32 ».
- Firmware : GPIO14 (KEY) en entrée sans pull-up interne, actif haut.
- Optionnel : MCP23017 si plus de GPIO nécessaires.
