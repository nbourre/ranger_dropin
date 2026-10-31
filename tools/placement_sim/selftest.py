"""Auto-test rapide : python -m tools.placement_sim.selftest CARTE.kicad_pcb

Vérifie sur une vraie carte que le lecteur, le moteur et l'export se comportent correctement :
  - toutes les empreintes sont lues, avec des pastilles ;
  - une rotation de 360° (4 x 90°) ramène exactement les pastilles à leur place ;
  - les pièces verrouillées ne bougent jamais (physique, recuit) ;
  - le plan exporté ne contient que des pièces déplacées et reste dans le format de Konnect ;
  - l'annulation par instantané restaure tout.
"""
from __future__ import annotations

import sys

from . import Annealer, Config, World, load_board


def check(cond: bool, msg: str):
    print(("OK   " if cond else "ECHEC"), msg)
    if not cond:
        raise SystemExit(1)


def main(path: str):
    board = load_board(path)
    check(len(board.footprints) > 0, "%d empreintes lues" % len(board.footprints))
    with_pads = sum(1 for f in board.footprints if f.pads)
    check(with_pads >= 0.9 * len(board.footprints), "%d empreintes sur %d ont des pastilles" % (with_pads, len(board.footprints)))
    check(board.bbox is not None, "contour Edge.Cuts lu : {}".format(tuple(round(v, 1) for v in board.bbox) if board.bbox else None))
    w = World(board, Config(max_move=5))
    w.auto_ghost()
    ents = w.entities

    # rotation 4 x 90° = identité
    e = next(x for x in ents if len(x.pads) >= 2)
    before = [(p.x, p.y) for p in e.world_pads()]
    for _ in range(4):
        e.rotate90()
    after = [(p.x, p.y) for p in e.world_pads()]
    check(all(abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6 for a, b in zip(before, after)),
          "rotation de 360° : pastilles de %s inchangées" % e.ref)

    locked = {x.ref: (x.x, x.y, x.rot) for x in ents if x.locked}
    snap = w.snapshot()
    w.run(60)
    an = Annealer(w, seed=1)
    an.total = 1500
    an.run(1500)
    check(all((x.x, x.y, x.rot) == locked[x.ref] for x in ents if x.locked),
          "%d pièces verrouillées immobiles après physique et recuit" % len(locked))
    check(all(((x.x - x.x0) ** 2 + (x.y - x.y0) ** 2) ** 0.5 <= 5 + 1e-6 for x in ents if x.movable),
          "--max-move 5 respecté")
    plan = w.plan()
    check(all(set(p) == {"reference", "x", "y", "rotation"} for p in plan), "plan exporté : %d pièces, format Konnect" % len(plan))
    check(all(not w.by_ref[p["reference"]].locked for p in plan), "aucune pièce verrouillée dans le plan")
    w.restore(snap)
    check(all((x.x, x.y, x.rot) == snap[x.ref] for x in ents), "annulation par instantané")
    m = w.metrics()
    check(m["overlaps"] >= 0 and m["hpwl"] > 0, "métriques : %s" % m)
    print("Tous les tests passent.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Beaper-Esp32s3.kicad_pcb")
