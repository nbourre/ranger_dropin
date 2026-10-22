# À faire / en suspens (Beaper-Esp32s3, carrier DevKitC-1)

Dernière mise à jour : 2026-10-22. L'état ci-dessous correspond au PCB enregistré le 2026-10-22 à 07 h 25 (schéma enregistré le 2026-10-21). Historique détaillé : `checkpoints/` (001 à 005, Copilot) et `git log`.

## État du projet
- **Schéma** : à jour (buck, fusibles séparés, protection des sorties moteur, décalage de niveau des RJ25, J1 jack DC, M1/M2 en JST PH, Qwiic J8 et 3 headers I2C J9/J15/J16). Dernier ERC complet : 0 erreur (avant les derniers ajouts, **à relancer**).
- **PCB** : 127 empreintes synchronisées avec le schéma, **tout sur la face du dessus (F.Cu)**, placement fait à la main par l'utilisateur et optimisé (condensateurs et résistances près de leurs broches). **Pas encore routé, pas de zone de masse, DRC non repris sur la version finale.** `score_placement` = 60 (les seuls « échecs durs » restants sont des chevauchements voulus avec le DevKit U5 et quelques courtyards d'en-têtes, voir plus bas).
- Contour 65,5 × 100 mm (R2) de (50, 30) à (115,5, 130), 3 trous de guidage Ø 2 mm (GH1 88,75/36 ; GH2 105,5/113,5 ; GH3 60/113,5).

## Disposition actuelle (positions clés, mm, repère PCB)
- Haut : J1 jack DC (57,75; 41,1), SW1 reset (66,1; 32,15), J12 panneau RGB 1x7 (75,13 à 90,37; 32,6, centré en x), buck U1 (79,65; 47,98) avec L1, C13/C14/C15/C16, compensation C19/C20/R42, diviseur R40/R41 ; U3 TB6612 (69,95; 57,26) ; J5 RJ25 A (110,52; 42,64, ouverture vers le haut).
- Milieu : J13/J14 appuis GND du panneau (66,875 et 98,625; 75,1), colonne de headers H7/H8/H4/H1 (x = 108,17; y 57,7 à 68,2), J9/J15/J16 I2C 1x04 (x = 105,63; y 72,6 à 79,8), LS1 buzzer, J3 TFT (52,25; 47,1), J11 OLED (52,25; 71,1).
- Bas : DevKit U5 (60,53; 107,28, rot 90, sur supports) avec les petits composants dessous (y 84 à 107), J4 et J8 Qwiic (111,25; 100,1 et 91,6, ouverture vers le bord droit, **sous le DevKit**), bande y 109 à 118 : chaînes de protection moteur et résistances d'encodeur, J10 VL53L1X (76,4 à 89,1; 119,6), M1 (70,25; 123,4) et M2 (85,25; 123,4) en JST PH, J6 et J7 RJ25 B et C dans les coins du bas (103,15 et 56,06; 117,71, ouverture vers le bas).
- Fixes (contraintes de l'utilisateur) : connecteurs moteur M1/M2 et capteur de distance J10 (J10 a été remonté de 4,2 mm pour les JST). Le module RGB doit rester centré en x.

## Décisions de conception (rappel)
- **Alimentation** : batterie NiMH 7,2 V sur J1 (centre = VBAT). VBAT → TVS D9 → F1 3,5 A → D8 → VCC (moteurs, VM du TB6612) et F2 3 A → D13 → buck U1 TPS54331 (5,0 V, même circuit que l'Auriga). D11 isole la sortie du buck (5V_P) du rail +5V (≈4,7 V) pour éviter le retour de courant USB. Servos : micro 9 g, 2 sorties (H7 = A6 / GPIO 6, H8 = A7 / GPIO 7) via le 74HCT541 U2 ; générer le PWM par LEDC.
- **Sorties moteur** : TB6612 → TVS bidirectionnelle SMAJ12CA (D14 à D17) → perle 120 Ω/2 A (FB1 à FB4) → PTC 1 A (F3 à F6) → M1/M2. Chaînes placées juste au-dessus de M1/M2.
- **M1/M2** : JST PH 6 broches, pas 2,0 mm, entrée latérale (S6B-PH-K, empreinte `Connector_JST:JST_PH_S6B-PH-K_1x06_P2.00mm_Horizontal`, modèle 3D de KiCad). Photos de l'Auriga dans `auriga/photos/`. Brochage : 1 ENCB, 2 ENCA, 3 +3V3, 4 GND, 5 M−, 6 M+. **Sens de la broche 1 à vérifier au multimètre sur une fiche moteur réelle.** Les encodeurs sont en 3,3 V (Auriga : 5 V) : à tester, sinon diviseur.
- **RJ25 (J5, J6, J7)** identiques à l'Auriga en tension (5 V) : 6 signaux S1/S2 par décalage de niveau BSS138 (Q3 à Q8, pull-ups 10 k R45 à R56), nets côté port `PA_S1_5V` etc., alimentation sur `5V_P` (sortie du buck avant D11). Ordre des broches du RJ : 1 SCL, 2 SDA, 3 GND, 4 5 V, 5 S1, 6 S2. Numérique seulement (pas d'analogique 0-5 V) ; le port B partage GPIO 43/44 (UART0) ; le port C partage D9/D10 avec J3. Prise : Amphenol 54601-906WPLF (6p6c, « tab down », contacts en haut ; l'Auriga est l'inverse, le câble se tord sans problème).
- **JP1** (header 1x03, « I2C EXT 3V3/5V ») : choisit la tension des pull-ups du bus I2C des RJ25 (EXT_SCL/EXT_SDA) : 1-2 = 3,3 V, 2-3 = 5 V (position Makeblock). Sans rapport avec le « JP1 » (jack d'alimentation) de `AURIGA_PINMAP.md`.
- **I2C 3,3 V du carrier** : Qwiic J4 et J8 (JST SH, GND/3V3/SDA/SCL), headers J9/J15/J16 (GND, +3V3, SCL, SDA, comme J11), H1 (SDA) et H4 (SCL), J10, J11, U6. Aucun pull-up ajouté pour les nouveaux connecteurs ; **vérifier que les pull-ups du bus principal (R16/R17 4,7 k) suffisent avec 8 appareils**.
- **74AHCT1G125 (U7)** : tampon 3,3 V → 5 V pour la donnée de l'anneau RGB : GPIO 48 → U7 → R39 220 Ω → J12.5. KEY du panneau : actif haut, R38 15 k / R37 10 k vers GPIO 14, sans pull-up interne.
- **Condensateurs** : replacés près de leur circuit (buck, U3, U2, U7, U4, U6, U5). C11 est collé à la broche VOL_BAT du DevKit. C8 (470 µF, VCC) est resté loin de U3.
- **Remplacements d'empreintes** pour gagner de la place : C7/C8/C17 en CP_Elec_6.3x7.7 (C5354997), C3 en 1206, U2 en TSSOP-20 (C53552921), U4 en SOT-23 (C127949).
- Supprimés : CON1 (bornier), H2/H3 (sonar), H5/H6, R13/R14, R27/R28, SW2 à SW5. Le Qwiic J9 de l'ancien schéma n'existe plus : **J9 est maintenant un header I2C 1x04**.

## À faire (priorité)
1. **Relancer ERC et DRC** sur le fichier enregistré. DRC connu : sérigraphie des références qui se chevauche partout (les masquer ou les réduire), espacement des pastilles du LSM6 (U6, 0,15 mm pour 0,2 mm requis, propre au composant), courtyards du DevKit (à ignorer ou exclure).
2. **Routage** (Freerouting ou à la main) : lignes moteur 1 A longues (U3 en haut, M1/M2 en bas, ~60 mm), I2C, 5V_P, VCC ; **zones de masse** F.Cu/B.Cu.
3. **Vérifications en 3D** (Alt+3) : RJ25 (ouverture qui dépasse du bord de ≈ 4,5 mm pour J5, J6 et J7, l'Auriga dépasse de ≈ 1,8 mm), Qwiic J4/J8 sous le DevKit (câble qui doit entrer sous le module), hauteur sous le DevKit (8,5 mm) et sous le module panneau, J12 contre GH1, buzzer LS1, SW1 (orientation du bouton latéral), J1 (sens d'entrée de la fiche).
4. **Modèles 3D manquants** : L1 (Bourns SRP7028A-6R8M), SW1 (Alps SKRTLAE010), U5 (DevKitC-1, Espressif), G1 (logo). Les autres empreintes ont un modèle de KiCad : si les modèles manquent après un rechargement, faire « Mettre à jour les empreintes depuis la bibliothèque » dans KiCad.
5. **Placement à revoir si le routage coince** : U3 plus près de M1/M2 ; D10 (diode du buck) à 4,8 mm de la broche PH de U1 (acceptable) ; C13 à 6 mm de VIN ; H1/H4/H7/H8 se touchent de 0,3 mm (courtyards) ; F6/LS1 1,2 mm² ; J12/GH1 2,8 mm² (pas de contact cuivre).
6. LCSC / BOM : refs manquantes (F1, D8, D9, C8, R31 à R39, R45 à R56 = 10 k C25804, C9 à C12, M1/M2 S6B-PH-K-S, U7, RJ25 54601-906WPLF, Qwiic, supports). L1 = HCMA-0630-6R8 (C54431702, Extended) à confirmer ; C7/C8/C17 470 µF C18221527 / C5354997 à confirmer.
7. Datasheet du LSM6DS3TR-C absent (st.com bloque le téléchargement automatique). Autres datasheets dans `datasheets/`.
8. Ménage du schéma : cadre pointillé « Optional 5V LDO » vide et périmé (x 25-86, y 150-193 mm) avec D1/R2 (LED Vin) ; commentaire 3 de la page de titre qui dit encore « Arduino Nano ESP32 ».
9. Confirmer le brochage du module OLED (J11 supposé GND, 3V3, SCL, SDA) et l'ordre des broches des modules I2C génériques (J9/J15/J16 sont GND, VCC, SCL, SDA).
10. Mesurer les trous de fixation Makeblock sur une vraie poutre (nominal 8 mm, M4).
11. **Monter le DevKit (U5) sur des headers femelles « doubles » : 2x22 au lieu de 1x22 par côté** (demande de l'utilisateur, 2026-10-22, à faire **avant** la tâche 12). Chaque côté du DevKit aurait donc deux rangées de 22 contacts femelles à 2,54 mm : une rangée reçoit les broches du DevKit, l'autre rangée, reliée broche à broche en parallèle, donne accès à **toutes** les broches (mesure, fils Dupont, autres variantes, GPIO non câblés). Pistes à étudier : (a) une empreinte U5 personnalisée (p. ex. `BEAPER-Nano:ESP32-S3-DevKitC-1-2x22`) avec deux pastilles du même numéro par broche, pour ne pas toucher au schéma, ou deux `PinSocket_2x22_P2.54mm_Vertical` ; (b) rangée supplémentaire **à l'extérieur** (côté bord de la carte), pour ne pas manger la zone entre les rangées où passent les petits composants ; (c) vérifier la largeur : DevKit 22,86 mm + 2 × 2,54 mm de rangée supplémentaire, sur une carte de 65,5 mm, et le chevauchement avec J3/J11 (x ≈ 52 mm) et la colonne H (x ≈ 105-113 mm) ; (d) la hauteur sous le module panneau (limite ≈ 8,5 mm sous le DevKit, à revalider) ; (e) les pastilles de la rangée supplémentaire doivent avoir un net (celui de la broche), même si elles ne vont nulle part ailleurs. Si toutes les broches sont accessibles ainsi, la tâche 12 devient en grande partie inutile.
12. **Ajouter des headers de sortie pour les GPIO 35, 36 et 37** (demande de l'utilisateur, 2026-10-22). Ces trois broches sont réservées par la **PSRAM octale** (« R8 ») : c'est le type de PSRAM qui compte, pas la taille de la mémoire. La taille de la flash (N8 ou N16) ne libère aucune broche.

    | Variante du DevKitC-1 (même empreinte) | Flash | PSRAM | GPIO 35/36/37 |
    |---|---|---|---|
    | N16R8 (celle de la carte) | 16 Mo | 8 Mo octale | réservés |
    | N8R8 | 8 Mo | 8 Mo octale | réservés |
    | N8R2 | 8 Mo | 2 Mo quad | libres |
    | N8 / N4 | 8 ou 4 Mo | aucune | libres |

    Les flash octales (type N32R8V) en réservent encore plus. Tableau tiré de mes connaissances du module : **à confirmer** dans la fiche d'Espressif (WROOM-1, tableau des broches) et `datasheets/U5_ESP32-S3-DevKitC-1_schematic.pdf`. À faire : un header 1x03 (GPIO 35/36/37) avec les nets nommés, non câblés à autre chose, marqué « sans PSRAM octale seulement » en sérigraphie (inutile avec un N16R8 ou un N8R8) ; mettre à jour le tableau GPIO du README si on les utilise.
13. Optionnel : MCP23017 si plus de GPIO ; firmware : GPIO 14 (KEY) en entrée sans pull-up interne, actif haut ; module suiveur de ligne I2C maison (ATtiny1616 seesaw, adresse 0x49) sur un Qwiic.

## Pièges Konnect appris
- Voir `MEMOIRE.md`, section « Particularités des outils Konnect ».
