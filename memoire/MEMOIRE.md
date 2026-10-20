# Mémoire du projet (contexte pour reprendre le travail)

Résumé de l'état du projet BEAPER Nano → carrier ESP32-S3 pour remplacer l'Auriga du mBot Ranger.
Détails historiques : voir `checkpoints/` (001 à 005). Documentation technique : `../README.md` (anglais) et `../AURIGA_PINMAP.md` (anglais).

## Conventions de travail
- L'utilisateur écrit en français : répondre en français, concisément. README et PINMAP restent en anglais.
- Le schéma et le PCB sont modifiés avec les outils MCP Konnect (`.mcp.json`). Le paramètre du fichier PCB s'appelle `board`, celui du schéma `schematic`.
- Pièces préférées : SMD, catalogue Basic de JLCPCB/LCSC.

## Décisions de conception
- Carte : ESP32-S3-DevKitC-1-N16R8 (U5), alimentée par sa broche 5V via le rail +5V du buck U1 (TPS54331, 3 A, remplace le LM2940 depuis le 2026-10-19) et la diode D11. Le TB6612FNG (U3) remplace le SN754410.
- Boutons de la carte supprimés (SW2 à SW5, R3 à R6), sauf RESET (SW1). Capteurs de ligne, potentiomètres et TEPT4400 supprimés.
- Bouton général = broche KEY du module panneau Auriga. **Mesuré : le bouton relie KEY au V-BAT (actif haut).** Diviseur R38 15k (série) / R37 10k (vers GND) vers GPIO14, entrée sans pull-up interne.
- Anneau RGB : GPIO48 → U7 (74AHCT1G125, 3,3 V → 5 V) → R39 220 Ω → J12.5.
- Connecteurs : J12 PRGB (femelle 1x7), J13/J14 supports GND (femelle 1x2), J5 à J7 RJ25 (côté basse puissance seulement), J8/J9 Qwiic supplémentaires (J4 existant), J10 VL53L1X, J11 OLED I2C.
- VL53L1X (module Amazon, ordre sérigraphié) : 1 VIN, 2 GND, 3 SCL, 4 SDA, 5 GPIO1, 6 XSHUT (5 et 6 non connectés). Doit pointer dans la même direction que les connecteurs moteur de l'Auriga lors du placement.
- OLED : ordre supposé GND, 3V3, SCL, SDA (modèle pas encore choisi).
- Aucun GPIO libre : voir le tableau dans `../README.md`. GPIO 43/44 (RJ25 B) sont l'UART0 du pont USB. Le port RJ25 C partage D9/D10 avec le connecteur SPI J3.
- I2C du carrier en 3,3 V (5 V sur l'Auriga) : un module avec pull-ups 5 V pourrait poser problème.

## Géométrie (origine en haut à gauche de l'Auriga)
- Carte 65,5 × 100 mm, coins R2. Sur le PCB : (50, 30) à (115,5, 130).
- Trous de guidage Ø 2 mm : GH1 (38,75, 6), GH2 (55,5, 83,5), GH3 (10, 83,5) → PCB (88,75, 36), (105,5, 113,5), (60, 113,5).
- Module panneau : 36,1 × 50 mm, entraxe des headers GND 31,75 mm (mesuré 34 mm extérieur / 29,2 mm intérieur).
- Trous de fixation Makeblock : pas encore mesurés (nominal 8 mm, M4).

## État
- Schéma : ERC 0 erreur (89 avertissements anciens : symboles/bibliothèques, labels locaux/globaux, extrémités de fils).
- PCB : contour et 3 trous faits (non sauvegardés tant que KiCad n'est pas enregistré). Pas de placement, `update_pcb_from_schematic` pas fait. Les anciens footprints restent sur la carte.

## Particularités des outils Konnect (pour gagner du temps)
- Découvrir le schéma d'un outil en l'appelant avec un argument manquant.
- `batch_connect_to_net` : `net_name`, `schematic`, `pins:[{reference, pin_number}]`.
- `delete_schematic_net_label` : `net`, `schematic`, `x`, `y`. `delete_graphics` : `board`, `layer`, `dry_run`.
- `add_board_outline` : `board`, `x1`, `y1`, `x2`, `y2`, `corner_radius` (ajoute, ne remplace pas).
- `add_mounting_hole` : `board`, `x`, `y`, `drill_diameter`, `reference` (2 → MountingHole_2mm). Sans diamètre, il crée un M3 3,2 mm.
- Après suppression de composants, les fils et labels orphelins restent à nettoyer à la main.
- Netlist : `generate_netlist` avec `output`. ERC : sortie JSON dans un fichier temporaire.

## À faire
Voir `notes-a-faire.md` et la section TODO de `../README.md`.
