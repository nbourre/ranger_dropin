"""Monde de simulation de placement : entités, forces, métriques, optimiseur.

Chaque composant du PCB devient une `Entity` qui conserve ses propriétés d'origine
(référence, valeur, empreinte, couche, verrou, pastilles avec nets, propriétés...) et
qui a en plus un état dynamique (position, rotation, vitesse).

Le moteur est générique : les forces sont de petites fonctions ajoutées à `World.forces`.
Rien ici ne dépend de PyGame, on peut donc simuler « sans écran » (voir __main__.py).
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field

from .kicad_pcb import Board, Footprint, rot_pt

# Nets que l'on n'essaie pas de rapprocher (rails, masse) : ils relient tout à tout.
DEFAULT_IGNORE_NETS = r"^(GND|.*GND.*|\+?[0-9]V[0-9]?|\+5V|\+3V3|VCC|VBAT|VM|5V_P|unconnected.*|)$"


# ------------------------------------------------------------------ entités
@dataclass
class WPad:
    """Pastille en coordonnées monde (pour l'affichage et les forces)."""
    number: str
    net: str
    x: float
    y: float
    w: float
    h: float
    shape: str
    ptype: str
    angle: float


class Entity:
    """Un composant simulé : propriétés du composant + état dynamique."""

    def __init__(self, fp: Footprint):
        self.fp = fp
        # --- propriétés du composant (identiques à celles du PCB)
        self.ref = fp.ref
        self.value = fp.value
        self.lib_id = fp.lib_id
        self.layer = fp.layer
        self.attr = fp.attr
        self.props = dict(fp.props)
        self.uuid = fp.uuid
        self.locked = fp.locked          # verrou KiCad (cadenas) : jamais déplacé
        self.pads = fp.pads
        # --- état dynamique
        self.x, self.y, self.rot = fp.x, fp.y, fp.rot
        self.x0, self.y0, self.rot0 = fp.x, fp.y, fp.rot
        self.vx = self.vy = 0.0
        # --- drapeaux de simulation
        self.pinned = False              # figé par l'utilisateur dans l'outil
        self.ghost = False               # ne repousse pas les autres (ex. DevKit sur supports)
        self.keepout = False             # ses broches forment une zone où les autres pièces ne restent pas
        self._cache_key = None
        self._wpads: list[WPad] = []

    # ---- état
    @property
    def movable(self) -> bool:
        return not (self.locked or self.pinned)

    def moved(self, tol: float = 0.02) -> bool:
        return (math.hypot(self.x - self.x0, self.y - self.y0) > tol
                or round(self.rot - self.rot0) % 360 != 0)

    def reset(self):
        self.x, self.y, self.rot = self.x0, self.y0, self.rot0
        self.vx = self.vy = 0.0

    def rotate90(self, steps: int = 1):
        self.rot = (self.rot + 90 * steps) % 360

    # ---- géométrie monde
    def to_world(self, lx: float, ly: float) -> tuple[float, float]:
        dx, dy = rot_pt(lx, ly, self.rot)
        return self.x + dx, self.y + dy

    def world_pads(self) -> list[WPad]:
        key = (round(self.x, 6), round(self.y, 6), round(self.rot, 6))
        if key != self._cache_key:
            out = []
            quarter = int(round(self.rot - self.rot0)) % 180 == 90
            for p in self.pads:
                wx, wy = self.to_world(p.x, p.y)
                w, h = (p.h, p.w) if quarter else (p.w, p.h)
                out.append(WPad(p.number, p.net, wx, wy, w, h, p.shape, p.ptype, self.rot))
            self._wpads, self._cache_key = out, key
        return self._wpads

    def court_aabb(self, margin: float = 0.0):
        """Boîte alignée sur les axes du courtyard tourné (exact pour des rotations de 90°)."""
        c = self.fp.court or (-0.5, -0.5, 0.5, 0.5)
        pts = [self.to_world(x, y) for x, y in ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)

    def text_aabb(self):
        """Boîte approximative du texte de référence (None s'il est masqué)."""
        t = self.fp.text_off
        if not t or self.fp.text_hidden:
            return None
        cx, cy = self.to_world(t[0], t[1])
        size = t[3]
        length, height = len(self.ref) * size * 0.62 + 0.15, size + 0.15
        if int(round(t[2])) % 180 == 90:
            length, height = height, length
        return (cx - length / 2, cy - height / 2, cx + length / 2, cy + height / 2)

    def silk_segments(self):
        return [(self.to_world(*a), self.to_world(*b)) for a, b in self.fp.silk]


# ------------------------------------------------------------------ géométrie
def overlap_vec(a, b):
    """(ox, oy) = translation minimale qui dégage `a` de `b`, ou None s'ils ne se touchent pas."""
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    if ox <= 0 or oy <= 0:
        return None
    ca = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
    cb = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if ox < oy:
        return (ox if ca[0] >= cb[0] else -ox, 0.0)
    return (0.0, oy if ca[1] >= cb[1] else -oy)


def overlap_area(a, b) -> float:
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return ox * oy if ox > 0 and oy > 0 else 0.0


# ------------------------------------------------------------------ configuration
@dataclass
class Config:
    margin: float = 0.2           # espace minimal voulu entre courtyards (mm)
    use_text: bool = False        # le texte de référence compte comme obstacle
    repulsion: float = 0.6        # force de répulsion des chevauchements
    attraction: float = 0.005     # force d'attraction des nets
    sep_weight: float = 0.08      # séparation « boids » : poids (0 = désactivée)
    sep_radius: float = 3.0       # séparation : rayon d'influence autour des courtyards (mm)
    sep_max: float = 0.5          # séparation : force totale maximale par pièce
    sep_neighbors: int = 7        # séparation : nombre de voisins pris en compte
    zone_weight: float = 1.0      # zones de broches : poussée hors de la zone (0 = désactivée)
    zone_max: float = 1.5         # zones de broches : force maximale
    zone_margin: float = 0.5      # zones de broches : marge autour des pastilles (mm)
    zone_gap: float = 3.0         # pastilles à moins de cette distance = même zone (mm)
    w_zone: float = 30.0          # recuit : coût par mm2 de pièce posée sur une zone
    attract_max: float = 0.8      # plafond de la force d'attraction par pastille
    max_net_pins: int = 6         # on ignore les nets reliant plus de pièces (rails)
    boundary: float = 0.8         # rappel vers l'intérieur du contour
    edge_margin: float = 0.3      # marge au bord de la carte
    home: float = 0.0             # rappel vers la position d'origine (0 = libre)
    damping: float = 0.82
    max_step: float = 0.6         # déplacement max par pas (mm)
    max_move: float = 0.0         # distance max autorisée depuis l'origine (0 = illimité)
    project_iters: int = 8        # passes de projection de non-pénétration par pas
    ignore_nets: str = DEFAULT_IGNORE_NETS
    # poids de l'optimiseur (recuit simulé)
    w_wire: float = 1.0
    w_overlap: float = 30.0
    w_outside: float = 20.0


# ------------------------------------------------------------------ monde
class World:
    def __init__(self, board: Board, config: Config | None = None):
        self.board = board
        self.cfg = config or Config()
        self.entities: list[Entity] = [Entity(fp) for fp in board.footprints]
        self.by_ref = {e.ref: e for e in self.entities}
        self.bbox = board.bbox
        self.time = 0
        self.forces = [force_overlap, force_zone, force_separation, force_nets, force_boundary, force_home]
        self._rebuild_nets()

    # ---- nets
    def _rebuild_nets(self):
        ig = re.compile(self.cfg.ignore_nets, re.I)
        self.nets: dict[str, list[tuple[Entity, int]]] = {}
        for e in self.entities:
            for i, p in enumerate(e.pads):
                if p.net:
                    self.nets.setdefault(p.net, []).append((e, i))
        self.sig_nets = {n: pins for n, pins in self.nets.items() if not ig.match(n)}

    def set_ignore_nets(self, pattern: str):
        self.cfg.ignore_nets = pattern
        self._rebuild_nets()

    # ---- sélection / filtres
    def apply_filter(self, only=(), refs=(), fix=(), ghosts=()):
        """Fige tout ce qui n'est pas visé par `only` (préfixes) ou `refs`, plus `fix`."""
        only, refs, fix, ghosts = set(only), set(refs), set(fix), set(ghosts)
        for e in self.entities:
            prefix = re.match(r"[A-Za-z]+", e.ref)
            targeted = (not only and not refs) or e.ref in refs or (prefix and prefix.group(0) in only)
            e.pinned = (not targeted) or e.ref in fix
            e.ghost = e.ref in ghosts

    def movable_entities(self):
        return [e for e in self.entities if e.movable]

    def auto_ghost(self, min_inside: int = 5) -> list[str]:
        """Rend « fantôme » toute pièce dont le courtyard englobe au moins `min_inside` autres
        pièces (typiquement un module monté sur supports, comme le DevKit : les composants
        sont dessous par conception). Renvoie les références concernées."""
        found = []
        for e in self.entities:
            b = e.court_aabb()
            n = sum(1 for o in self.entities if o is not e and b[0] <= o.x <= b[2] and b[1] <= o.y <= b[3])
            if n >= min_inside:
                e.ghost = True
                e.keepout = len(e.pads) >= 8
                found.append(e.ref)
        return found

    # ---- zones de broches
    def set_keepout(self, refs):
        for e in self.entities:
            if e.ref in set(refs):
                e.keepout = True

    def zones(self):
        """Rectangles (réf, (x0, y0, x1, y1)) autour des groupes de pastilles des pièces `keepout`.
        Les pastilles voisines (< zone_gap) forment une même zone ; recalculé car la pièce peut bouger."""
        cfg, out = self.cfg, []
        for e in self.entities:
            if not e.keepout:
                continue
            boxes = [(p.x - p.w / 2, p.y - p.h / 2, p.x + p.w / 2, p.y + p.h / 2) for p in e.world_pads()]
            groups: list[list[float]] = []
            for b in boxes:
                hit = [g for g in groups if g[0] - cfg.zone_gap < b[2] and g[2] + cfg.zone_gap > b[0]
                       and g[1] - cfg.zone_gap < b[3] and g[3] + cfg.zone_gap > b[1]]
                merged = [b[0], b[1], b[2], b[3]]
                for g in hit:
                    merged = [min(merged[0], g[0]), min(merged[1], g[1]), max(merged[2], g[2]), max(merged[3], g[3])]
                    groups.remove(g)
                groups.append(merged)
            m = cfg.zone_margin
            out += [(e.ref, (g[0] - m, g[1] - m, g[2] + m, g[3] + m)) for g in groups]
        return out

    def zone_overlap(self, e: Entity, zones=None) -> float:
        """Surface (mm2) du courtyard de `e` posée sur une zone de broches d'une autre pièce."""
        if e.keepout or e.ghost:
            return 0.0
        a = e.court_aabb()
        return sum(overlap_area(a, z) for r, z in (self.zones() if zones is None else zones) if r != e.ref)

    # ---- instantanés (annuler / rétablir)
    def snapshot(self):
        return {e.ref: (e.x, e.y, e.rot) for e in self.entities}

    def restore(self, snap):
        for e in self.entities:
            if e.ref in snap:
                e.x, e.y, e.rot = snap[e.ref]
                e.vx = e.vy = 0.0

    def reset(self):
        for e in self.entities:
            e.reset()

    # ---- paires qui se touchent (grille spatiale)
    def overlapping_pairs(self, margin=None, use_text=None):
        m = self.cfg.margin if margin is None else margin
        ut = self.cfg.use_text if use_text is None else use_text
        cell = 8.0
        boxes = []
        grid: dict[tuple[int, int], list[int]] = {}
        for i, e in enumerate(self.entities):
            b = e.court_aabb(m / 2)
            t = e.text_aabb() if ut else None
            if t:
                b = (min(b[0], t[0]), min(b[1], t[1]), max(b[2], t[2]), max(b[3], t[3]))
            boxes.append(b)
            for cx in range(int(b[0] // cell), int(b[2] // cell) + 1):
                for cy in range(int(b[1] // cell), int(b[3] // cell) + 1):
                    grid.setdefault((cx, cy), []).append(i)
        seen, out = set(), []
        for ids in grid.values():
            for p in range(len(ids)):
                for q in range(p + 1, len(ids)):
                    i, j = (ids[p], ids[q]) if ids[p] < ids[q] else (ids[q], ids[p])
                    if (i, j) in seen:
                        continue
                    seen.add((i, j))
                    a, b = self.entities[i], self.entities[j]
                    if a.layer != b.layer or a.ghost or b.ghost:
                        continue
                    ca, cb = a.court_aabb(m / 2), b.court_aabb(m / 2)
                    ov = overlap_vec(ca, cb)
                    if ov:
                        out.append((a, b, ov, overlap_area(ca, cb)))
                    elif ut:
                        ta, tb = a.text_aabb(), b.text_aabb()
                        for x, y in ((ta, cb), (ca, tb), (ta, tb)):
                            if x and y:
                                ov = overlap_vec(x, y)
                                if ov:
                                    out.append((a, b, ov, overlap_area(x, y)))
                                    break
        return out

    # ---- métriques
    def net_hpwl(self, name: str) -> float:
        pins = self.nets.get(name, [])
        if len(pins) < 2:
            return 0.0
        xs, ys = [], []
        for e, i in pins:
            p = e.world_pads()[i]
            xs.append(p.x)
            ys.append(p.y)
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    def hpwl(self, significant_only: bool = True) -> float:
        nets = self.sig_nets if significant_only else self.nets
        return sum(self.net_hpwl(n) for n in nets)

    def outside_distance(self, e: Entity) -> float:
        if not self.bbox:
            return 0.0
        m = self.cfg.edge_margin
        b = e.court_aabb()
        d = 0.0
        d += max(0.0, self.bbox[0] + m - b[0]) + max(0.0, b[2] - (self.bbox[2] - m))
        d += max(0.0, self.bbox[1] + m - b[1]) + max(0.0, b[3] - (self.bbox[3] - m))
        return d

    def metrics(self) -> dict:
        pairs = self.overlapping_pairs()
        zs = self.zones()
        moved = [e for e in self.entities if e.moved()]
        disp = [math.hypot(e.x - e.x0, e.y - e.y0) for e in moved]
        return {
            "overlaps": len(pairs),
            "overlap_area": round(sum(p[3] for p in pairs), 2),
            "hpwl": round(self.hpwl(), 1),
            "outside": sum(1 for e in self.entities if e.movable and self.outside_distance(e) > 0.01),
            "in_zone": sum(1 for e in self.entities if self.zone_overlap(e, zs) > 0.01),
            "moved": len(moved),
            "max_disp": round(max(disp), 2) if disp else 0.0,
        }

    # ---- forces
    def compute_forces(self):
        """Évalue chaque force séparément (sans bouger personne) :
        renvoie ({nom_de_force: {réf: [fx, fy]}}, {réf: [fx, fy]} total)."""
        parts, total = {}, {e.ref: [0.0, 0.0] for e in self.entities if e.movable}
        for f in self.forces:
            d = {r: [0.0, 0.0] for r in total}
            f(self, d)
            parts[f.__name__.replace("force_", "")] = d
            for r, (fx, fy) in d.items():
                total[r][0] += fx
                total[r][1] += fy
        return parts, total

    # ---- une étape de physique
    def step(self, dt: float = 1.0) -> float:
        """Avance d'un pas ; renvoie l'énergie cinétique (pour détecter la convergence)."""
        cfg = self.cfg
        force = self.compute_forces()[1]
        ke = 0.0
        for e in self.entities:
            if not e.movable:
                e.vx = e.vy = 0.0
                continue
            fx, fy = force[e.ref]
            e.vx = (e.vx + fx * dt) * cfg.damping
            e.vy = (e.vy + fy * dt) * cfg.damping
            sp = math.hypot(e.vx, e.vy)
            if sp > cfg.max_step:
                e.vx, e.vy = e.vx * cfg.max_step / sp, e.vy * cfg.max_step / sp
            e.x += e.vx
            e.y += e.vy
            if cfg.max_move > 0:
                d = math.hypot(e.x - e.x0, e.y - e.y0)
                if d > cfg.max_move:
                    e.x = e.x0 + (e.x - e.x0) * cfg.max_move / d
                    e.y = e.y0 + (e.y - e.y0) * cfg.max_move / d
                    e.vx = e.vy = 0.0  # butée : la vitesse ne doit pas rester accumulée
            ke += e.vx * e.vx + e.vy * e.vy
        self.project()
        self.time += 1
        return ke

    def project(self):
        """Projection de non-pénétration (comme les moteurs physiques de jeux) : après les forces,
        on écarte réellement les courtyards qui se chevauchent, puis on rentre les pièces dans la carte."""
        cfg = self.cfg
        for _ in range(cfg.project_iters):
            pairs = self.overlapping_pairs()
            if not pairs:
                break
            for a, b, (ox, oy), _area in pairs:
                if a.movable and b.movable:
                    sa = sb = 0.5
                elif a.movable:
                    sa, sb = 1.0, 0.0
                elif b.movable:
                    sa, sb = 0.0, 1.0
                else:
                    continue
                a.x += ox * sa
                a.y += oy * sa
                b.x -= ox * sb
                b.y -= oy * sb
        if self.bbox:
            m = cfg.edge_margin
            for e in self.entities:
                if not e.movable:
                    continue
                b = e.court_aabb()
                if b[0] < self.bbox[0] + m:
                    e.x += self.bbox[0] + m - b[0]
                if b[2] > self.bbox[2] - m:
                    e.x -= b[2] - (self.bbox[2] - m)
                if b[1] < self.bbox[1] + m:
                    e.y += self.bbox[1] + m - b[1]
                if b[3] > self.bbox[3] - m:
                    e.y -= b[3] - (self.bbox[3] - m)
        if cfg.max_move > 0:
            for e in self.entities:
                if e.movable:
                    d = math.hypot(e.x - e.x0, e.y - e.y0)
                    if d > cfg.max_move:
                        e.x = e.x0 + (e.x - e.x0) * cfg.max_move / d
                        e.y = e.y0 + (e.y - e.y0) * cfg.max_move / d

    def run(self, steps: int, tol: float = 1e-5) -> int:
        n = 0
        for n in range(1, steps + 1):
            if self.step() < tol:
                break
        return n

    # ---- export d'un plan (format de Konnect : set_component_placements)
    def plan(self, tol: float = 0.02, snap: float = 0.05) -> list[dict]:
        out = []
        for e in self.entities:
            if e.moved(tol):
                x = round(e.x / snap) * snap if snap else e.x
                y = round(e.y / snap) * snap if snap else e.y
                out.append({"reference": e.ref, "x": round(x, 4), "y": round(y, 4), "rotation": round(e.rot % 360, 3)})
        return out


# ------------------------------------------------------------------ forces
def force_overlap(world: World, force: dict):
    """Répulsion entre courtyards qui se chevauchent (plus la marge)."""
    k = world.cfg.repulsion
    for a, b, (ox, oy), _ in world.overlapping_pairs():
        share = 0.5 if (a.movable and b.movable) else 1.0
        if a.movable:
            force[a.ref][0] += k * ox * share
            force[a.ref][1] += k * oy * share
        if b.movable:
            force[b.ref][0] -= k * ox * share
            force[b.ref][1] -= k * oy * share


def force_zone(world: World, force: dict):
    """Zones de broches (ex. U5) : une pièce dont le courtyard est dans une zone est poussée vers
    la sortie la plus proche. C'est une force douce et bornée, pas un mur : une pièce peut la
    traverser (glissée à la souris, attirée fortement par un net) mais n'y reste pas au repos."""
    cfg = world.cfg
    if cfg.zone_weight <= 0:
        return
    zones = world.zones()
    if not zones:
        return
    for e in world.entities:
        if not e.movable or e.keepout or e.ghost:
            continue
        a = e.court_aabb()
        for ref, z in zones:
            if ref == e.ref:
                continue
            ov = overlap_vec(a, z)
            if not ov:
                continue
            depth = math.hypot(*ov)
            f = min(cfg.zone_max, cfg.zone_weight * (0.4 + depth))
            force[e.ref][0] += ov[0] / depth * f
            force[e.ref][1] += ov[1] / depth * f


def force_separation(world: World, force: dict):
    """Séparation à la manière des boids : chaque pièce est repoussée par les voisins proches
    (distance entre courtyards < sep_radius), de plus en plus fort à mesure qu'ils s'approchent
    (poids 1/d, nul au bord du rayon), sur les `sep_neighbors` plus proches, force totale limitée à
    `sep_max`. Elle agit AVANT le contact : les pièces s'écartent et se stabilisent à distance,
    là où l'attraction des nets la compense. Les chevauchements restent traités par force_overlap."""
    cfg = world.cfg
    R = cfg.sep_radius
    if cfg.sep_weight <= 0 or R <= 0:
        return
    ents = [e for e in world.entities if not e.ghost]
    boxes = {e.ref: e.court_aabb() for e in ents}
    for me in ents:
        if not me.movable:
            continue
        a = boxes[me.ref]
        near = []
        for o in ents:
            if o is me or o.layer != me.layer:
                continue
            b = boxes[o.ref]
            gx = max(b[0] - a[2], a[0] - b[2])
            gy = max(b[1] - a[3], a[1] - b[3])
            if gx >= R or gy >= R or (gx <= 0 and gy <= 0):
                continue  # trop loin, ou chevauchement (géré par force_overlap)
            dx, dy = max(gx, 0.0), max(gy, 0.0)
            d = math.hypot(dx, dy)
            if d >= R:
                continue
            # direction qui s'éloigne de `o`, selon l'axe où il y a un écart
            ux = -dx if b[0] > a[0] else dx
            uy = -dy if b[1] > a[1] else dy
            near.append((d, ux / (d or 1e-9), uy / (d or 1e-9)))
        near.sort()
        fx = fy = 0.0
        for d, ux, uy in near[:cfg.sep_neighbors]:
            m = cfg.sep_weight * (1.0 / max(d, 0.05) - 1.0 / R)
            fx += ux * m
            fy += uy * m
        n = math.hypot(fx, fy)
        if n > cfg.sep_max:
            fx, fy = fx * cfg.sep_max / n, fy * cfg.sep_max / n
        force[me.ref][0] += fx
        force[me.ref][1] += fy


def force_nets(world: World, force: dict):
    """Attraction des pastilles d'un même net vers leur barycentre (modèle en étoile)."""
    cfg = world.cfg
    if cfg.attraction <= 0:
        return
    for name, pins in world.sig_nets.items():
        ents = {e.ref for e, _ in pins}
        if len(ents) < 2 or len(ents) > cfg.max_net_pins:
            continue
        pts = [(e, e.world_pads()[i]) for e, i in pins]
        cx = sum(p.x for _, p in pts) / len(pts)
        cy = sum(p.y for _, p in pts) / len(pts)
        w = cfg.attraction / max(1, len(ents) - 1)
        for e, p in pts:
            if not e.movable:
                continue
            dx, dy = cx - p.x, cy - p.y
            d = math.hypot(dx, dy)
            if d < 1e-9:
                continue
            f = min(d * w, cfg.attract_max)
            force[e.ref][0] += dx / d * f
            force[e.ref][1] += dy / d * f


def force_boundary(world: World, force: dict):
    """Rappel vers l'intérieur du contour de la carte."""
    if not world.bbox or world.cfg.boundary <= 0:
        return
    m, k = world.cfg.edge_margin, world.cfg.boundary
    bx0, by0, bx1, by1 = world.bbox
    for e in world.entities:
        if not e.movable:
            continue
        b = e.court_aabb()
        if b[0] < bx0 + m:
            force[e.ref][0] += k * (bx0 + m - b[0])
        if b[2] > bx1 - m:
            force[e.ref][0] -= k * (b[2] - (bx1 - m))
        if b[1] < by0 + m:
            force[e.ref][1] += k * (by0 + m - b[1])
        if b[3] > by1 - m:
            force[e.ref][1] -= k * (b[3] - (by1 - m))


def force_home(world: World, force: dict):
    """Ressort faible vers la position d'origine (garde le placement manuel comme base)."""
    k = world.cfg.home
    if k <= 0:
        return
    for e in world.entities:
        if e.movable:
            force[e.ref][0] += k * (e.x0 - e.x)
            force[e.ref][1] += k * (e.y0 - e.y)


# ------------------------------------------------------------------ recuit simulé
class Annealer:
    """Optimiseur par recuit simulé : déplacements/rotations aléatoires d'une pièce à la fois.

    Le coût local d'une pièce = longueur de fil (HPWL) de ses nets + chevauchements + sortie
    de carte. Un coup n'est accepté que si le coût local diminue (ou avec la probabilité de
    Metropolis, qui décroît avec la température).
    """

    def __init__(self, world: World, seed: int | None = None, t0: float = 2.0, t_end: float = 0.02,
                 allow_rotate: bool = True):
        self.w = world
        self.rng = random.Random(seed)
        self.t0, self.t_end = t0, t_end
        self.t = t0
        self.allow_rotate = allow_rotate
        self.iter = 0
        self.total = 20000
        self.accepted = 0
        self._nets_of: dict[str, list[str]] = {}
        for name, pins in world.sig_nets.items():
            for e, _ in pins:
                lst = self._nets_of.setdefault(e.ref, [])
                if name not in lst:
                    lst.append(name)

    def local_cost(self, e: Entity) -> float:
        w, cfg = self.w, self.w.cfg
        c = cfg.w_wire * sum(w.net_hpwl(n) for n in self._nets_of.get(e.ref, ()))
        if not e.ghost:
            ca = e.court_aabb(cfg.margin / 2)
            for o in w.entities:
                if o is e or o.ghost or o.layer != e.layer:
                    continue
                cb = o.court_aabb(cfg.margin / 2)
                if ca[0] < cb[2] and ca[2] > cb[0] and ca[1] < cb[3] and ca[3] > cb[1]:
                    c += cfg.w_overlap * overlap_area(ca, cb)
        c += cfg.w_outside * w.outside_distance(e)
        if cfg.zone_weight > 0:
            c += cfg.w_zone * w.zone_overlap(e)
        if cfg.max_move > 0:
            c += 10 * max(0.0, math.hypot(e.x - e.x0, e.y - e.y0) - cfg.max_move)
        return c

    def run(self, iterations: int = 2000):
        movable = self.w.movable_entities()
        if not movable:
            return
        cool = (self.t_end / self.t0) ** (1.0 / max(1, self.total))
        for _ in range(iterations):
            e = self.rng.choice(movable)
            before = self.local_cost(e)
            old = (e.x, e.y, e.rot)
            r = self.rng.random()
            if self.allow_rotate and r < 0.12:
                e.rotate90(self.rng.choice((1, 2, 3)))
            else:
                s = max(0.15, 3.0 * self.t)
                e.x += self.rng.gauss(0, s)
                e.y += self.rng.gauss(0, s)
            if self.w.cfg.max_move > 0:
                d = math.hypot(e.x - e.x0, e.y - e.y0)
                if d > self.w.cfg.max_move:
                    e.x = e.x0 + (e.x - e.x0) * self.w.cfg.max_move / d
                    e.y = e.y0 + (e.y - e.y0) * self.w.cfg.max_move / d
            delta = self.local_cost(e) - before
            if delta <= 0 or self.rng.random() < math.exp(-delta / max(self.t, 1e-6)):
                self.accepted += 1
            else:
                e.x, e.y, e.rot = old
            self.iter += 1
            self.t = max(self.t_end, self.t * cool)
