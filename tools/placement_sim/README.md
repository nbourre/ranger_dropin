# placement_sim : simulateur générique de placement KiCad (PyGame)

Lit un fichier `.kicad_pcb` **en lecture seule**, en fait un monde de composants simulés, et permet
de les déplacer à la main, de lancer une physique (répulsion des courtyards, attraction des nets,
rappel dans le contour) ou un recuit simulé, puis d'**exporter un plan JSON** que l'on applique
ensuite avec Konnect (`set_component_placements`). Le fichier de la carte n'est jamais modifié.

Dépendance : `pip install pygame` (testé avec 2.6.1, Python 3.11). Le mode `--headless` n'en a pas besoin.

## Lancer

Depuis la racine du projet :

```
python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb                       # fenêtre interactive
python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb --only R,D,C          # seules R, D et C bougent
python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb --headless --anneal 8000 --max-move 6 --out plan.json
python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb --screenshot capture.png --anneal 8000   # sans écran
python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb --list                # liste les composants
```

Forces de la physique : **répulsion** (chevauchements), **séparation** à la manière des boids (voisins à moins de `--sep-radius` mm, poids ~1/d, agit avant le contact ; `--separation 0` la désactive), **zone de broches** (les rangées de broches d'une pièce marquée `--keepout U5` ou touche `X` : les autres pièces peuvent la traverser mais pas y rester ; U5 est marquée automatiquement), **attraction** des nets, **rappel** vers le bord et vers l'origine. Le panneau (en haut à droite) règle et mesure chacune.

Options utiles : `--refs D12,D8` (seules ces pièces bougent), `--fix U2` (figer en plus), `--ghost U5`
(ne repousse personne), `--margin 0.2` (espace mini entre courtyards), `--text` (le texte de référence compte
comme obstacle), `--max-move 6` (laisse chaque pièce à 6 mm de son origine au plus), `--home`, `--attraction`,
`--repulsion`, `--ignore-nets REGEX`, `--steps N` (pas de physique), `--anneal N` (itérations de recuit), `--seed`.

## Raccourcis de la fenêtre (touche **H** dans l'outil)

| Action | Touche |
|---|---|
| Sélectionner / glisser une pièce | clic gauche (les pièces verrouillées ne bougent pas) |
| Déplacer la vue / zoom | clic droit ou milieu / molette, flèches, `-` `+`, `F` ajuste |
| Physique ON/OFF | Espace |
| Recuit simulé ON/OFF | `A` |
| Tourner de 90° (Maj = sens inverse) | `R` |
| Figer / libérer, fantôme | `L`, `V` |
| Chevelu, courtyards, pastilles, références, sérigraphie, infos | `N` `C` `P` `T` `S` `I` |
| Tout remettre à l'origine / annuler | `Z` / `Ctrl+Z` |
| Exporter le plan JSON / capture PNG | `E` / `K` |
| Régler répulsion, attraction, marge | `[` `]`, `,` `.`, `;` `'` |
| Grille aimantée (0,05 mm) | `Q` |
| Voir les forces (flèche blanche = total ; rouge répulsion, bleu attraction des nets, jaune bord, vert origine ; le détail chiffré de la pièce survolée/sélectionnée s'affiche en bas) | `G` |
| Quitter (avec confirmation : Entrée ou `O` confirme, toute autre touche annule) | `Esc` ou fermer la fenêtre |

Couleurs : contour orange = pièce verrouillée dans KiCad, bleu = mobile, rouge = en chevauchement,
violet = « fantôme ». Les pastilles ont la couleur de leur net ; passer la souris sur une pièce surligne ses liaisons.

## Architecture (pour le réutiliser)

- `kicad_pcb.py` : lecteur (`load_board`) → `Board` / `Footprint` / `Pad` (propriétés d'origine : référence, valeur,
  empreinte, couche, verrou, `attr`, uuid, toutes les propriétés, pastilles avec nets, courtyard, sérigraphie, texte).
- `world.py` : `Entity` (un composant simulé : mêmes propriétés + position/rotation/vitesse, drapeaux
  `locked`/`pinned`/`ghost`), `World` (forces, métriques, projection de non-pénétration, export du plan),
  `Annealer` (recuit simulé), `Config` (poids). Une **force** est une fonction `f(world, force_dict)` ajoutée à
  `World.forces` : pour une règle de placement nouvelle (aimantation sur un bord, alignement, groupes...), il suffit
  d'en écrire une.
- `viewer.py` : `App` PyGame (aucune logique de placement dedans). `__main__.py` : ligne de commande.

Métriques affichées : nombre et surface des chevauchements de courtyards, longueur de fil HPWL des nets
« significatifs » (sans GND ni rails), pièces hors carte, pièces déplacées.

## Limites connues (à garder en tête avant d'appliquer un plan)

- Aucune connaissance de la **hauteur 3D** : une pièce peut passer sous un module (le DevKit est détecté « fantôme »
  car son courtyard englobe au moins 5 autres pièces) même si elle est trop haute. Aucune règle de routage
  (courant, boucles, antenne) non plus.
- Les courtyards sont des boîtes alignées sur les axes (exact pour des rotations de 90°).
- Le texte de référence est optionnel (`--text`) et rigide ; Konnect ne sait pas le déplacer.
- La physique est surtout utile pour **pousser les voisins** quand on glisse une pièce ; l'optimisation globale se fait
  par le recuit (`--anneal`). Les pièces verrouillées dans KiCad (cadenas) sont toujours fixes ; les paires de pièces
  verrouillées qui se chevauchent comptent dans les métriques sans pouvoir être résolues.
- Résultat type sur Beaper-Esp32s3 (recuit 8000 itérations, `--max-move 6`) : 13 → 2 chevauchements, HPWL −17 %.
  C'est un point de départ à relire dans KiCad, pas un placement fini.
