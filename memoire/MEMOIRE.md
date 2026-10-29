# Mémoire du projet (contexte pour reprendre le travail)

Résumé de l'état du projet Beaper-Esp32s3 (anciennement BEAPER Nano) → carrier ESP32-S3 pour remplacer l'Auriga du mBot Ranger.
Détails historiques : voir `checkpoints/` (001 à 005). Documentation technique : `../README.md` (anglais) et `../AURIGA_PINMAP.md` (anglais). Liste des tâches et état détaillé : `notes-a-faire.md`. Photos de l'Auriga : `../auriga/photos/`. Modèles 3D ajoutés : `../3dmodels/`.

## Conventions de travail
- L'utilisateur écrit en français : répondre en français, concisément. README et PINMAP restent en anglais.
- Le schéma et le PCB sont modifiés avec les outils MCP Konnect (`.mcp.json`). Le paramètre du fichier PCB s'appelle `board`, celui du schéma `schematic`. Jamais d'édition directe des fichiers `.kicad_*`.
- Pièces préférées : SMD, catalogue Basic de JLCPCB/LCSC.
- **Tout est sur la face du dessus (F.Cu)** : rien sous le PCB, pour que la carte s'enclenche dans le robot.
- L'utilisateur place et déplace beaucoup de pièces à la main dans KiCad entre deux sessions : relire les positions (`get_component_list`) avant de supposer quoi que ce soit.

## Décisions de conception
- Carte : ESP32-S3-DevKitC-1-N16R8 (U5, sur supports), alimentée par sa broche 5V via le rail +5V du buck U1 (TPS54331, 3 A, remplace le LM2940) et la diode D11. Le TB6612FNG (U3) remplace le SN754410.
- Alimentation : jack DC J1 (centre = VBAT, 7,2 V NiMH). VBAT → TVS D9 → F1 (moteurs, VCC) et F2 → D13 → buck U1. Sorties moteur protégées (TVS, perle, PTC) comme l'Auriga. Détails dans `notes-a-faire.md`.
- Boutons de la carte supprimés, sauf RESET (SW1, bouton latéral Alps SKRTLAE010). Capteurs de ligne, potentiomètres et TEPT4400 supprimés.
- Bouton général = broche KEY du module panneau Auriga. **Mesuré : le bouton relie KEY au V-BAT (actif haut).** Diviseur R38 15k (série) / R37 10k (vers GND) vers GPIO14, entrée sans pull-up interne.
- Anneau RGB : GPIO48 → U7 (74AHCT1G125, 3,3 V → 5 V) → R39 220 Ω → J12.
- Connecteurs : J12 PRGB (femelle 1x7), J13/J14 supports GND (femelle 1x2), J5 à J7 RJ25 (côté basse puissance, **5 V comme l'Auriga via décalage de niveau BSS138**, Amphenol 54601-906WPLF 6p6c), J4 et J8 Qwiic (JST SH), J9/J15/J16 headers I2C 1x04 génériques (GND, 3V3, SCL, SDA), J10 VL53L1X, J11 OLED I2C, J3 TFT/SPI, **M1/M2 JST PH 6 broches 2,0 mm entrée latérale** (comme l'Auriga), H1/H4 (I2C 3,3 V) et H7/H8 (servos 5 V).
- JP1 = cavalier 1x03 qui choisit la tension des pull-ups du bus I2C des RJ25 (3,3 V ou 5 V).
- VL53L1X (module Amazon, ordre sérigraphié) : 1 VIN, 2 GND, 3 SCL, 4 SDA, 5 GPIO1, 6 XSHUT (5 et 6 non connectés). Doit rester centré sur les moteurs.
- OLED : ordre supposé GND, 3V3, SCL, SDA (modèle pas encore choisi).
- Aucun GPIO libre : voir le tableau dans `../README.md`. GPIO 43/44 (RJ25 B) sont l'UART0 du pont USB. Le port RJ25 C partage D9/D10 avec le connecteur SPI J3.
- Contraintes de l'utilisateur sur le placement : M1/M2 et J10 fixes, module RGB (J12) centré en x, tout le reste déplaçable.

## Géométrie (origine en haut à gauche de l'Auriga)
- Carte 65,5 × 100 mm, coins R2. Sur le PCB : (50, 30) à (115,5, 130).
- Trous de guidage Ø 2 mm : GH1 (38,75, 6), GH2 (55,5, 83,5), GH3 (10, 83,5) dans le repère Auriga → PCB (88,75, 36), (105,5, 113,5), (60, 113,5).
- Module panneau : 36,1 × 50 mm, entraxe des headers GND 31,75 mm. Hauteur disponible sous le DevKit et sous le module : ≈ 8,5 mm.
- Trous de fixation Makeblock : pas encore mesurés (nominal 8 mm, M4).
- Sur l'Auriga, tous les connecteurs sont sur la face du dessus. Ses RJ25 ont les contacts en bas, les nôtres en haut (câble à tordre, sans conséquence électrique).

## État (2026-10-28, fin de soirée)
- Schéma et PCB synchronisés (127 empreintes, 0 écart de parité), **placement terminé et validé** (candidat commité), **routage pas commencé**, pas de zones de masse. DRC enregistré : 304 non routés, 13 erreurs de clearance toutes sur U6 (pastilles du LSM6, propres au composant), 29 courtyards (U5 voulus + H1/H4/H7/H8 + J12/GH1), 19 avertissements d'empreintes (les 19 que Konnect ne rafraîchit pas).
- **U5 (DevKit)** : footprint `BEAPER-Nano:ESP32-S3-DevKitC-1-2x22` (88 pastilles : rangées intérieures sur les broches du DevKit, rangées d'accès **à l'extérieur**, même numéro de pastille, `duplicate_pad_numbers_are_jumpers yes`). **Tourné de 180°** (rotation −90°, origine (113,87 ; 84,42), broche 1 à droite) : USB à gauche (x ≈ 52,1), **antenne qui dépasse d'environ 6 mm du bord droit** (voulu, bon pour le Wi-Fi : ne jamais mettre de cuivre/zone de masse sous l'antenne, ni de câble). Rangée L = nord (y 84,42), rangée R = sud (y 107,28). Modèle 3D : STEP de l'utilisateur + 2 supports 2x22 (détails dans `notes-a-faire.md`, tâche 4). Étiquettes de broches (44 textes F.SilkS, y = 87,0 et 104,8) entre les rangées.
- J4 (Qwiic) est en haut à gauche (67,25 ; 33,6), J8 sur le bord gauche (53,25 ; 85,6), loin de l'antenne. SW1 est en haut à droite. L1 et SW1 ont des modèles 3D VRML approximatifs (`3dmodels/*.wrl`, script `tools/make_block_models.py`).
- Voir `notes-a-faire.md` pour la liste des tâches et la disposition.

## Particularités des outils Konnect (pour gagner du temps)
- Découvrir le schéma d'un outil en l'appelant avec un argument manquant. Charger les jeux d'outils avec `load_toolset`.
- PCB en direct (IPC) : lancer pcbnew seul (pas le gestionnaire de projet) avec le bon `.kicad_pcb` ouvert. Le schéma est édité par fichier : il faut fermer l'éditeur de schéma.
- **Les modifications IPC ne vivent que dans la carte ouverte** : si KiCad recharge le fichier ou si l'utilisateur annule (Ctrl+Z), elles disparaissent. Demander d'enregistrer (Ctrl+S) après chaque série de changements, et vérifier l'état réel avant de poursuivre. `run_drc` lit le fichier **enregistré**, pas la carte ouverte.
- `batch_connect_to_net` n'existe pas : utiliser `connect_to_net` (`schematic`, `reference`, `pin_number`, `net`). Noms de nets avec `{slash}` pour « / » (`A4{slash}SDA`) ; les rails (`GND`, `+3V3`) se connectent par étiquettes locales du même nom.
- `delete_schematic_net_label` : `net`, `schematic`, `x`, `y`. `delete_graphics` : `board`, `layer`, `dry_run`. `delete_schematic_wire` : UUID complet. `batch_add_junction` : `positions`.
- `add_board_outline` : `board`, `x1`, `y1`, `x2`, `y2`, `corner_radius` (ajoute, ne remplace pas). `add_mounting_hole` : `board`, `x`, `y`, `drill_diameter`, `reference` (sans diamètre, M3 3,2 mm).
- Changer l'empreinte d'un composant : `edit_schematic_component` (footprint) → `delete_component` sur le PCB → `update_pcb_from_schematic` (dry-run puis apply avec `expected_plan_revision`). Konnect refuse de changer l'empreinte d'une pièce déjà sur le PCB.
- La synchronisation crée les empreintes **sans modèle 3D** (ou avec le chemin de bibliothèque). Voir/ajouter les modèles : `set_placed_footprint_models` (`inspect` d'abord pour obtenir `models_revision`, puis `append` ou `replace`). `update_footprints_from_library` ne les restaure pas. Les modèles de KiCad sont dans `${KICAD10_3DMODEL_DIR}` ; les nôtres sous `${KIPRJMOD}/3dmodels/`. Le STEP de la prise RJ25 Amphenol est « Y vers le haut » : rotation X de −90° et décalage (3,175; −16,77; 0) mm (vérifié par un rendu `kicad-cli pcb render`).
- `set_component_placements` : un seul appel pour plusieurs pièces (x, y, rotation). `score_placement` : les chevauchements avec U5 sont voulus (DevKit sur supports) ; ne regarder que les autres. L'outil `place_decoupling_caps` est bloqué tant que le contour est « non prouvé » : placer à la main.
- Bounding boxes de courtyard : D_SMA ≈ ±3,5 mm en x, condensateurs CP 6,3×7,7 ≈ ±4,2 mm, buzzer = cercle (bbox plus grande que le cercle).
- Netlist : `generate_netlist` avec `output` ; `export_netlist_summary` renvoie un gros JSON (sauvé dans un fichier, à lire avec python). ERC : sortie JSON dans un fichier temporaire.
- Windows : `Remove-Item` d'un dossier utilisé comme répertoire courant échoue (« busy ») : changer de répertoire d'abord.
- **Accès en direct (2026-10-28)** : il faut « Enable KiCad API » (Préférences → Plugins) et **seulement l'éditeur PCB ouvert** ; avec l'éditeur de footprints ou de schéma ouvert en même temps, KiCad répond « BeginCommit … multiple editors are open ». Si le fichier verrou `~*.kicad_pcb.lck` existe et que l'API ne répond pas, Konnect refuse de toucher au fichier (ne jamais le contourner). Un `get_component_pads` sur U5 dépasse la limite de jetons : sauver et lire en python. `check_kicad_ui` dit si l'API répond.
- **Textes de référence** : aucun outil Konnect ne déplace ou ne cache le texte de référence d'un composant (seulement `add_board_text`, qui crée du texte libre). Il faut le faire dans KiCad (taille, masquage).
- **`update_footprints_from_library`** : toujours en simulation d'abord. Refuse 20 empreintes (champ Datasheet « unlocked », `tedit`, `clearance`, et surtout `duplicate_pad_numbers_are_jumpers yes` de U5) ; passer la liste `references` des autres. Pour les refuser, utiliser la fenêtre de KiCad **en décochant « Update/reset 3D models »** (sinon SW1, L1, J5 à J7 perdent leurs modèles personnalisés) et **sans U5**.
- **`update_pcb_from_schematic`** répond « conflict / footprint_id_changed » quand le footprint d'une pièce change : faire F8 dans KiCad (le remplace en gardant position, verrou et nets). KiCad ne recopie pas `duplicate_pad_numbers_are_jumpers` : le régler dans les propriétés du footprint de la carte (onglet « Clearance Overrides & Pad Connections »).
- **Modèles 3D, conventions KiCad 10 (vérifiées par rendu)** : le signe de la rotation en x est **inversé** (un STEP « y vers le haut » se met debout avec rotation x = **−90**, +90 le met à l'envers) ; avec rotation x = −90, la position y de la carte vaut `z_du_modèle − décalage_y` (pour U5 : décalage_y = −29,97 met la broche 1 à y = 0) ; la 2e colonne de `PinSocket_2xNN` est vers les **x négatifs** ; un modèle VRML compte en unités de 0,1 pouce (2,54 mm). Méthode de vérification sans toucher à la vraie carte : `create_project` dans le dossier temporaire, `register_footprint_library` sur une copie de la bibliothèque, `place_component`, `get_board_2d_view` (rendu 3D de dessus, kicad-cli) ; `set_footprint_models` pour itérer. Les modèles du projet sont référencés par `${KIPRJMOD}/3dmodels/...`.
- **`kicad-cli`** : `C:\Users\nicol\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe pcb drc --format json --severity-all --units mm -o out.json carte.kicad_pcb` donne un DRC complet lisible en python (plus léger que `run_drc`, dont la réponse dépasse vite la limite).
- **`tools/repulse_placement.py`** (lecture seule, écrit un plan JSON) : détecte très bien les chevauchements courtyard/texte (`--report-only --margin 0`), mais la simulation de répulsion/attraction **ne réduit pas les conflits** sur cette carte dense (texte de référence rigide, pièces coincées autour des connecteurs verrouillés). Ne l'utiliser que pour lister les conflits.

## À faire
Voir `notes-a-faire.md` et la section TODO de `../README.md`.
