"""Ligne de commande : python -m tools.placement_sim CARTE.kicad_pcb [options]"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import Annealer, Config, World, load_board


def csv(s: str):
    return [x.strip() for x in s.split(",") if x.strip()]


def fmt(m: dict) -> str:
    return ("chevauchements %d (%.1f mm2) | HPWL %.0f mm | hors carte %d | déplacées %d (max %.1f mm)"
            % (m["overlaps"], m["overlap_area"], m["hpwl"], m["outside"], m["moved"], m["max_disp"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="placement_sim", description=__doc__)
    ap.add_argument("pcb", help="fichier .kicad_pcb (lu en lecture seule)")
    ap.add_argument("--only", default="", help="préfixes de référence mobiles, ex. R,D,C (défaut : tout)")
    ap.add_argument("--refs", default="", help="références mobiles exactes, ex. D12,D8")
    ap.add_argument("--fix", default="", help="références à figer en plus des pièces verrouillées")
    ap.add_argument("--ghost", default="", help="références « fantômes » (ne repoussent personne), ex. U5")
    ap.add_argument("--keepout", default="", help="références dont les broches forment une zone interdite au repos, ex. U5")
    ap.add_argument("--zone", type=float, default=1.0, help="force des zones de broches (0 = off)")
    ap.add_argument("--no-auto-ghost", action="store_true", help="ne pas détecter les modules sur supports")
    ap.add_argument("--margin", type=float, default=0.2, help="espace mini entre courtyards (mm)")
    ap.add_argument("--text", action="store_true", help="le texte de référence compte comme obstacle")
    ap.add_argument("--repulsion", type=float, default=0.6)
    ap.add_argument("--separation", type=float, default=0.08, help="poids de la séparation de type boids (0 = off)")
    ap.add_argument("--sep-radius", type=float, default=3.0, help="rayon de la séparation (mm)")
    ap.add_argument("--attraction", type=float, default=0.005)
    ap.add_argument("--home", type=float, default=0.0, help="rappel vers la position d'origine (0 = libre)")
    ap.add_argument("--max-move", type=float, default=0.0, help="distance maximale depuis l'origine, mm (0 = illimitée)")
    ap.add_argument("--max-net-pins", type=int, default=6)
    ap.add_argument("--ignore-nets", default=None, help="regex des nets ignorés pour l'attraction et le HPWL")
    ap.add_argument("--headless", action="store_true", help="simule sans fenêtre")
    ap.add_argument("--steps", type=int, default=0, help="pas de physique à exécuter avant (ou sans) fenêtre")
    ap.add_argument("--anneal", type=int, default=0, help="itérations de recuit simulé à exécuter")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default="placement_plan.json", help="fichier du plan exporté (format Konnect)")
    ap.add_argument("--screenshot", default="", help="écrit une capture PNG puis quitte (rendu sans écran)")
    ap.add_argument("--list", action="store_true", help="liste les composants et quitte")
    a = ap.parse_args(argv)

    board = load_board(a.pcb)
    cfg = Config(margin=a.margin, use_text=a.text, repulsion=a.repulsion, attraction=a.attraction, sep_weight=a.separation, zone_weight=a.zone, sep_radius=a.sep_radius,
                 home=a.home, max_move=a.max_move, max_net_pins=a.max_net_pins)
    if a.ignore_nets is not None:
        cfg.ignore_nets = a.ignore_nets
    world = World(board, cfg)
    world.apply_filter(only=csv(a.only), refs=csv(a.refs), fix=csv(a.fix), ghosts=csv(a.ghost))
    if not a.no_auto_ghost:
        auto = [r for r in world.auto_ghost() if r not in csv(a.ghost)]
        if auto:
            print("fantômes détectés (modules sur supports) :", ", ".join(auto))

    world.set_keepout(csv(a.keepout))
    if a.list:
        for e in world.entities:
            print("%-5s %-9s %8.2f %8.2f %5.0f° %-4s %s%s%s | %s" % (
                e.ref, e.value[:9], e.x, e.y, e.rot, e.layer, "L" if e.locked else "-",
                "P" if e.pinned else "-", "G" if e.ghost else "-", e.lib_id))
        return 0

    print("%d composants, %d mobiles, %d verrouillés, %d nets significatifs"
          % (len(world.entities), len(world.movable_entities()), sum(e.locked for e in world.entities),
             len(world.sig_nets)))
    m0 = world.metrics()
    print("avant   :", fmt(m0))

    if a.anneal:  # d'abord l'optimisation globale...
        an = Annealer(world, seed=a.seed)
        an.total = a.anneal
        an.run(a.anneal)
        print("recuit  : %d itérations, %d acceptées" % (an.iter, an.accepted), "->", fmt(world.metrics()))
    if a.steps:   # ...puis la physique pour nettoyer les derniers chevauchements
        n = world.run(a.steps)
        print("physique: %d pas" % n, "->", fmt(world.metrics()))
    if a.steps or a.anneal:
        print("après   :", fmt(world.metrics()))

    plan = world.plan()
    if a.headless and not a.screenshot:
        if a.steps or a.anneal:
            with open(a.out, "w", encoding="utf-8") as fh:
                json.dump(plan, fh, indent=1)
            print("plan exporté : %d pièces -> %s" % (len(plan), a.out))
        return 0

    if a.screenshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from .viewer import App

    app = App(world, out_path=a.out, snap=0.05)
    if a.screenshot:
        app.last_metrics = world.metrics()
        path = app.screenshot(a.screenshot)
        print("capture :", path)
        return 0
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
