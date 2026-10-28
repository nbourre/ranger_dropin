#!/usr/bin/env python3
"""Placement par répulsion (« organique ») pour un .kicad_pcb.

Lit le PCB ENREGISTRÉ en lecture seule, simule des forces de répulsion entre
les pièces (boîte = courtyard + texte de la référence) et écrit un plan JSON.
Le plan est appliqué ensuite par Konnect (set_component_placements) : ce script
ne modifie JAMAIS le fichier .kicad_pcb.

Exemples (depuis la racine du projet) :
    python tools/repulse_placement.py Beaper-Esp32s3.kicad_pcb --only R
    python tools/repulse_placement.py Beaper-Esp32s3.kicad_pcb --only R,D --max-move 2
    python tools/repulse_placement.py Beaper-Esp32s3.kicad_pcb --refs D12,D8 --fix U2
    python tools/repulse_placement.py Beaper-Esp32s3.kicad_pcb --only D --report-only

Règles :
  - Une pièce bouge seulement si elle passe les filtres (--only / --refs) ET n'est
    ni verrouillée dans KiCad (cadenas), ni dans --fix / FIXED_DEFAULT.
  - Les pièces qui ne bougent pas restent des obstacles.
  - Un ressort faible ramène chaque pièce vers sa position d'origine, et le
    déplacement est limité (--max-move) : le placement manuel reste la base.
  - v1 : translation seulement, la rotation n'est pas modifiée.
"""
import argparse
import json
import math
import re
import sys

# Pièces que l'utilisateur veut garder en place (voir memoire/notes-a-faire.md).
FIXED_DEFAULT = {"M1", "M2", "J10", "J12", "U5", "J1", "GH1", "GH2", "GH3"}
# Pièces dont le corps (courtyard) recouvre volontairement les autres.
BODY_IGNORED_DEFAULT = {"U5"}
# Gain minimal de chevauchement (mm²) pour accepter de tourner une pièce.
MIN_ROTATE_GAIN = 0.3


# ---------------------------------------------------------------- s-expression
def tokenize(text):
    pos, n = 0, len(text)
    tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')
    while pos < n:
        m = tok.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            yield "("
        elif m.group(2):
            yield ")"
        elif m.group(3) is not None:
            yield ("s", m.group(3))
        else:
            yield m.group(4)


def parse(text):
    stack, cur = [], []
    for t in tokenize(text):
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done, cur = cur, stack.pop()
            cur.append(done)
        else:
            cur.append(t[1] if isinstance(t, tuple) else t)
    return cur[0] if cur else []


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def child(node, name):
    r = children(node, name)
    return r[0] if r else None


def num(x):
    return float(x)


# ----------------------------------------------------------------- géométrie
def rot(x, y, deg):
    """Rotation KiCad (y vers le bas) : même convention que le fichier."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c


def bbox_of(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


class Unit:
    """Une empreinte : boîte du corps + boîte du texte de la référence."""

    def __init__(self, fp):
        self.ref = ""
        self.locked = False
        self.layer = ""
        for p in children(fp, "property"):
            if p[1] == "Reference":
                self.ref = p[2]
        at = child(fp, "at")
        self.x, self.y = num(at[1]), num(at[2])
        self.rot = num(at[3]) if len(at) > 3 else 0.0
        self.x0, self.y0 = self.x, self.y
        self.layer = child(fp, "layer")[1]
        lk = child(fp, "locked")
        self.locked = bool(lk and len(lk) > 1 and lk[1] == "yes")
        # courtyard local
        pts = []
        for g in fp:
            if not (isinstance(g, list) and g and g[0] in ("fp_line", "fp_rect", "fp_poly", "fp_circle")):
                continue
            ly = child(g, "layer")
            if not ly or ly[1] not in ("F.CrtYd", "B.CrtYd"):
                continue
            for k in ("start", "end", "center"):
                c = child(g, k)
                if c:
                    pts.append((num(c[1]), num(c[2])))
            pl = child(g, "pts")
            if pl:
                for xy in children(pl, "xy"):
                    pts.append((num(xy[1]), num(xy[2])))
        self.pads_local = []
        self.nets = set()
        for pd in children(fp, "pad"):
            nn = child(pd, "net")
            if nn and len(nn) > 1 and not str(nn[-1]).startswith("unconnected-"):
                self.nets.add(nn[-1])
            a, s = child(pd, "at"), child(pd, "size")
            if a and s:
                self.pads_local.append((num(a[1]), num(a[2]), num(s[1]), num(s[2])))
        if not pts:  # repli : pastilles
            for pd in children(fp, "pad"):
                a, s = child(pd, "at"), child(pd, "size")
                px, py = num(a[1]), num(a[2])
                hx, hy = num(s[1]) / 2, num(s[2]) / 2
                pts += [(px - hx, py - hy), (px + hx, py + hy)]
        self.loc = bbox_of(pts) if pts else [-0.5, -0.5, 0.5, 0.5]
        # texte de la référence : décalage dans le repère de la pièce, angle ABSOLU dans le fichier
        self.rot0 = self.rot
        self.text_local = None
        for p in children(fp, "property"):
            if p[1] != "Reference":
                continue
            if child(p, "hide") and child(p, "hide")[1] == "yes":
                break
            pa = child(p, "at")
            tx, ty = num(pa[1]), num(pa[2])  # déjà dans le repère local de la pièce
            tang = num(pa[3]) if len(pa) > 3 else 0.0
            font = child(child(p, "effects"), "font")
            sz = child(font, "size")
            w, h = num(sz[1]), num(sz[2])
            self.text_local = (tx, ty, tang, w, h)
        self.set_rot(self.rot)

    def set_rot(self, deg):
        """Recalcule les boîtes (corps et texte) pour une rotation donnée."""
        self.rot = deg % 360
        loc = self.loc
        corners = [(loc[0], loc[1]), (loc[2], loc[1]), (loc[2], loc[3]), (loc[0], loc[3])]
        self.body_off = bbox_of([rot(cx, cy, self.rot) for cx, cy in corners])
        self.text_off = None
        if self.text_local:
            tx, ty, tang, w, h = self.text_local
            dx, dy = rot(tx, ty, self.rot)
            ang = tang + (self.rot - self.rot0)
            length = len(self.ref) * w * 0.62 + 0.15
            height = h * 1.0 + 0.15
            if int(round(ang)) % 180 == 90:
                length, height = height, length
            self.text_off = [dx - length / 2, dy - height / 2, dx + length / 2, dy + height / 2]

    def body(self, dx=0.0, dy=0.0):
        o = self.body_off
        return [self.x + dx + o[0], self.y + dy + o[1], self.x + dx + o[2], self.y + dy + o[3]]

    def text(self):
        if not self.text_off:
            return None
        o = self.text_off
        return [self.x + o[0], self.y + o[1], self.x + o[2], self.y + o[3]]


def inflate(b, m):
    return [b[0] - m, b[1] - m, b[2] + m, b[3] + m]


def overlap(a, b):
    """Vecteur de pénétration minimal (ox, oy) pour dégager a de b, ou None."""
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    if ox <= 0 or oy <= 0:
        return None
    ca, cb = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2), ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if ox < oy:
        return (ox if ca[0] >= cb[0] else -ox, 0.0)
    return (0.0, oy if ca[1] >= cb[1] else -oy)


# -------------------------------------------------------------------- lecture
def load(path):
    root = parse(open(path, encoding="utf-8").read())
    units = [Unit(fp) for fp in children(root, "footprint")]
    # obstacles fixes : textes libres (étiquettes de broches, etc.) sur la soie
    obstacles = []
    for t in children(root, "gr_text"):
        ly = child(t, "layer")
        if not ly or ly[1] not in ("F.SilkS", "B.SilkS"):
            continue
        at = child(t, "at")
        font = child(child(t, "effects"), "font")
        sz = child(font, "size")
        w, h = num(sz[1]), num(sz[2])
        txt = t[1]
        ang = num(at[3]) if len(at) > 3 else 0.0
        length, height = len(txt) * w * 0.62 + 0.15, h + 0.15
        if int(round(ang)) % 180 == 90:
            length, height = height, length
        cx, cy = num(at[1]), num(at[2])
        obstacles.append((txt, [cx - length / 2, cy - height / 2, cx + length / 2, cy + height / 2]))
    # les pastilles des pièces dont le corps est ignoré (U5) restent des obstacles
    for u in units:
        if u.ref not in BODY_IGNORED_DEFAULT:
            continue
        for px, py, w, h in u.pads_local:
            cx, cy = rot(px, py, u.rot)
            if int(round(u.rot)) % 180 == 90:
                w, h = h, w
            obstacles.append(("pad %s" % u.ref, [u.x + cx - w / 2, u.y + cy - h / 2, u.x + cx + w / 2, u.y + cy + h / 2]))
    # contour de la carte (rectangle Edge.Cuts)
    xs, ys = [], []
    for g in root:
        if isinstance(g, list) and g and g[0] in ("gr_line", "gr_rect", "gr_arc"):
            ly = child(g, "layer")
            if ly and ly[1] == "Edge.Cuts":
                for k in ("start", "end"):
                    c = child(g, k)
                    if c:
                        xs.append(num(c[1]))
                        ys.append(num(c[2]))
    outline = [min(xs), min(ys), max(xs), max(ys)] if xs else None
    return units, obstacles, outline


# ----------------------------------------------------------------- simulation
def conflicts(units, obstacles, margin, body_ignored, dx=None, dy=None):
    """Liste des paires en conflit : (i, j, type)."""
    out = []
    n = len(units)
    for i in range(n):
        a = units[i]
        for j in range(i + 1, n):
            b = units[j]
            if a.layer != b.layer:
                continue
            hit = False
            if a.ref not in body_ignored and b.ref not in body_ignored:
                if overlap(inflate(a.body(), margin / 2), inflate(b.body(), margin / 2)):
                    hit = True
            ta, tb = a.text(), b.text()
            if ta and b.ref not in body_ignored and overlap(inflate(ta, margin / 2), inflate(b.body(), margin / 2)):
                hit = True
            if tb and a.ref not in body_ignored and overlap(inflate(tb, margin / 2), inflate(a.body(), margin / 2)):
                hit = True
            if ta and tb and overlap(inflate(ta, margin / 2), inflate(tb, margin / 2)):
                hit = True
            if hit:
                out.append((a.ref, b.ref))
        for name, ob in obstacles:
            hit = overlap(inflate(a.body(), margin / 2), ob) if a.ref not in body_ignored else None
            ta = a.text()
            if not hit and ta:
                hit = overlap(inflate(ta, margin / 2), ob)
            if hit:
                out.append((a.ref, 'texte "%s"' % name))
    return out


POWER_NETS = re.compile(r"^(GND|VCC|VBAT|\+?[0-9]V[0-9]?|\+?[0-9]+V[0-9]*|5V_P|VM|.*GND.*)$", re.I)


def attraction_pairs(units, max_pads=4):
    """Paires de pièces qui partagent un net à peu de pièces (hors GND et rails)."""
    bynet = {}
    for u in units:
        for n in u.nets:
            if not POWER_NETS.match(n):
                bynet.setdefault(n, []).append(u.ref)
    pairs = {}
    for n, refs in bynet.items():
        if 2 <= len(refs) <= max_pads:
            for i in range(len(refs)):
                for j in range(i + 1, len(refs)):
                    key = tuple(sorted((refs[i], refs[j])))
                    pairs[key] = pairs.get(key, 0) + 1.0 / (len(refs) - 1)
    # découplage : chaque condensateur est attaché au circuit intégré le plus proche (à l'origine)
    # avec lequel il partage un rail
    for u in units:
        if not u.ref.startswith("C"):
            continue
        best, bd = None, 1e9
        for v in units:
            if v is u or not v.ref.startswith("U") or not (u.nets & v.nets - {n for n in v.nets if n.upper().endswith("GND") or n.upper() == "GND"}):
                continue
            d = math.hypot(u.x0 - v.x0, u.y0 - v.y0)
            if d < bd:
                best, bd = v, d
        if best is not None:
            key = tuple(sorted((u.ref, best.ref)))
            pairs[key] = pairs.get(key, 0) + 3.0
    return [(a, b, w) for (a, b), w in pairs.items()]


def simulate(units, movable, obstacles, outline, margin, max_move, spring, iters, edge,
             attract=(), attract_k=0.0):
    byref = {u.ref: u for u in units}
    body_ignored = BODY_IGNORED_DEFAULT
    for it in range(iters):
        force = {r: [0.0, 0.0] for r in movable if r in byref}
        for ra, rb, w in attract:
            if ra not in byref or rb not in byref or (ra not in force and rb not in force):
                continue
            A, B = byref[ra], byref[rb]
            ba, bb = A.body(), B.body()
            gx = max(0.0, max(ba[0], bb[0]) - min(ba[2], bb[2]))
            gy = max(0.0, max(ba[1], bb[1]) - min(ba[3], bb[3]))
            g = math.hypot(gx, gy)
            if g <= 0.5:
                continue
            dx, dy = B.x - A.x, B.y - A.y
            dn = math.hypot(dx, dy) or 1.0
            f = min(w * attract_k * (g - 0.5), 1.0)
            if ra in force:
                force[ra][0] += dx / dn * f
                force[ra][1] += dy / dn * f
            if rb in force:
                force[rb][0] -= dx / dn * f
                force[rb][1] -= dy / dn * f

        def push(a, b, boxa, boxb, share):
            ov = overlap(inflate(boxa, margin / 2), inflate(boxb, margin / 2))
            if not ov:
                return
            if a.ref in force:
                force[a.ref][0] += ov[0] * share
                force[a.ref][1] += ov[1] * share
            if b.ref in force:
                force[b.ref][0] -= ov[0] * share
                force[b.ref][1] -= ov[1] * share

        # recherche par cases : seules les pièces voisines sont comparées
        CELL = 8.0
        n = len(units)
        ext = []
        grid = {}
        for i, u in enumerate(units):
            b, t = u.body(), u.text()
            e = [b[0], b[1], b[2], b[3]]
            if t:
                e = [min(e[0], t[0]), min(e[1], t[1]), max(e[2], t[2]), max(e[3], t[3])]
            e = inflate(e, margin)
            ext.append(e)
            for cx in range(int(e[0] // CELL), int(e[2] // CELL) + 1):
                for cy in range(int(e[1] // CELL), int(e[3] // CELL) + 1):
                    grid.setdefault((cx, cy), []).append(i)
        seen = set()
        for cell in grid.values():
            for p in range(len(cell)):
                for q in range(p + 1, len(cell)):
                    i, j = (cell[p], cell[q]) if cell[p] < cell[q] else (cell[q], cell[p])
                    if (i, j) in seen:
                        continue
                    seen.add((i, j))
                    a, b = units[i], units[j]
                    if a.layer != b.layer or (a.ref not in force and b.ref not in force):
                        continue
                    if not overlap(ext[i], ext[j]):
                        continue
                    share = 0.5 if (a.ref in force and b.ref in force) else 1.0
                    abody_ok = a.ref not in body_ignored
                    bbody_ok = b.ref not in body_ignored
                    if abody_ok and bbody_ok:
                        push(a, b, a.body(), b.body(), share)
                    ta, tb = a.text(), b.text()
                    if ta and bbody_ok:
                        push(a, b, ta, b.body(), share)
                    if tb and abody_ok:
                        push(a, b, a.body(), tb, share)
                    if ta and tb:
                        push(a, b, ta, tb, share)
        for i, a in enumerate(units):
            if a.ref not in force:
                continue
            e = ext[i]
            ta = a.text()
            for _, ob in obstacles:
                if not overlap(e, ob):
                    continue
                if a.ref not in body_ignored:
                    ov = overlap(inflate(a.body(), margin / 2), ob)
                    if ov:
                        force[a.ref][0] += ov[0]
                        force[a.ref][1] += ov[1]
                if ta:
                    ov = overlap(inflate(ta, margin / 2), ob)
                    if ov:
                        force[a.ref][0] += ov[0]
                        force[a.ref][1] += ov[1]
        moved = 0.0
        for r, (fx, fy) in force.items():
            u = byref[r]
            fx += (u.x0 - u.x) * spring
            fy += (u.y0 - u.y) * spring
            step = 0.15 + 0.65 * (1.0 - it / max(1, iters - 1)) ** 2  # refroidissement
            nx, ny = u.x + fx * step, u.y + fy * step
            # limite de déplacement (disque autour de l'origine)
            d = math.hypot(nx - u.x0, ny - u.y0)
            if d > max_move:
                nx = u.x0 + (nx - u.x0) * max_move / d
                ny = u.y0 + (ny - u.y0) * max_move / d
            # reste dans la carte
            if outline:
                b = u.body(nx - u.x, ny - u.y)
                if b[0] < outline[0] + edge:
                    nx += outline[0] + edge - b[0]
                if b[1] < outline[1] + edge:
                    ny += outline[1] + edge - b[1]
                if b[2] > outline[2] - edge:
                    nx -= b[2] - (outline[2] - edge)
                if b[3] > outline[3] - edge:
                    ny -= b[3] - (outline[3] - edge)
            moved += abs(nx - u.x) + abs(ny - u.y)
            u.x, u.y = nx, ny
        if moved < 1e-4:
            break
    return it + 1


def area(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return ox * oy if ox > 0 and oy > 0 else 0.0


def unit_cost(u, units, obstacles, margin, body_ignored):
    """Surface de chevauchement de u (corps + texte) avec tout le reste."""
    m = margin / 2
    cost = 0.0
    ub, ut = inflate(u.body(), m), u.text()
    ut = inflate(ut, m) if ut else None
    for v in units:
        if v is u or v.layer != u.layer:
            continue
        vb, vt = inflate(v.body(), m), v.text()
        vt = inflate(vt, m) if vt else None
        if u.ref not in body_ignored and v.ref not in body_ignored:
            cost += area(ub, vb)
        if ut and v.ref not in body_ignored:
            cost += area(ut, vb)
        if vt and u.ref not in body_ignored:
            cost += area(ub, vt)
        if ut and vt:
            cost += area(ut, vt)
    for _, ob in obstacles:
        if u.ref not in body_ignored:
            cost += area(ub, ob)
        if ut:
            cost += area(ut, ob)
    return cost


def best_rotations(units, movable, obstacles, margin, deltas, body_ignored):
    """Une passe gloutonne : garde pour chaque pièce la rotation au moindre chevauchement."""
    changed = 0
    byref = {u.ref: u for u in units}
    order = sorted(movable, key=lambda r: -unit_cost(byref[r], units, obstacles, margin, body_ignored))
    for r in order:
        u = byref[r]
        base = u.rot
        # une rotation n'est acceptée que si elle réduit vraiment le chevauchement (mm²)
        best, best_cost = base, unit_cost(u, units, obstacles, margin, body_ignored) - MIN_ROTATE_GAIN
        for d in deltas:
            if d % 360 == 0:
                continue
            u.set_rot(u.rot0 + d)
            c = unit_cost(u, units, obstacles, margin, body_ignored)
            if c < best_cost:
                best, best_cost = u.rot, c
        u.set_rot(best)
        changed += best != base
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcb")
    ap.add_argument("--only", default="", help="préfixes de référence à déplacer, ex. R,D (résistances + diodes)")
    ap.add_argument("--refs", default="", help="références exactes à déplacer, ex. D12,D8")
    ap.add_argument("--exclude", default="", help="références à ne jamais déplacer (en plus des verrouillées)")
    ap.add_argument("--fix", default="", help="synonyme de --exclude")
    ap.add_argument("--no-default-fixed", action="store_true", help="ignore la liste FIXED_DEFAULT du script")
    ap.add_argument("--margin", type=float, default=0.3, help="espace mini entre boîtes, mm (défaut 0.3)")
    ap.add_argument("--max-move", type=float, default=2.0, help="déplacement max par pièce, mm (défaut 2)")
    ap.add_argument("--spring", type=float, default=0.05, help="rappel vers la position d'origine (défaut 0.05)")
    ap.add_argument("--settle", action="store_true",
                    help="mode en deux phases : pièces fixes retirées, les autres se placent, puis les fixes reviennent")
    ap.add_argument("--settle-move", type=float, default=12.0, help="déplacement max en mode --settle, mm")
    ap.add_argument("--attract", type=float, default=0.05, help="force d'attraction du netlist (0 = aucune)")
    ap.add_argument("--rotate", default="", help="rotations à essayer en plus de l'actuelle, ex. 90,180,270")
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--edge", type=float, default=0.5, help="marge au bord de la carte, mm")
    ap.add_argument("--min-move", type=float, default=0.3, help="déplacement mini pour garder une pièce dans le plan, mm")
    ap.add_argument("--snap", type=float, default=0.05, help="grille finale, mm")
    ap.add_argument("--out", default="", help="écrit le plan JSON (références, x, y, rotation)")
    ap.add_argument("--report-only", action="store_true", help="liste les conflits sans simuler")
    a = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    units, obstacles, outline = load(a.pcb)
    csv =lambda s: {x.strip() for x in s.split(",") if x.strip()}
    prefixes, refs = csv(a.only), csv(a.refs)
    fixed = csv(a.exclude) | csv(a.fix)
    if not a.no_default_fixed:
        fixed |= FIXED_DEFAULT

    def selected(u):
        if not prefixes and not refs:
            return True
        pref = re.match(r"[A-Za-z]+", u.ref)
        return u.ref in refs or (pref and pref.group(0) in prefixes)

    locked = {u.ref for u in units if u.locked}
    movable = [u.ref for u in units if selected(u) and u.ref not in fixed and u.ref not in locked]
    print("Pièces : %d, verrouillées : %d (%s)" % (len(units), len(locked), ", ".join(sorted(locked)) or "-"))
    print("Déplaçables avec ce filtre : %d" % len(movable))

    mset = set(movable)
    relevant = lambda cs: [p for p in cs if p[0] in mset or p[1] in mset]
    before = relevant(conflicts(units, obstacles, a.margin, BODY_IGNORED_DEFAULT))
    print("Conflits avant (au moins une pièce déplaçable) : %d" % len(before))
    if a.report_only:
        for p in before:
            print("  %s <-> %s" % p)
        return 0

    deltas = [int(x) for x in csv(a.rotate)] if a.rotate else []
    if a.settle:
        # Phase A : les pièces fixes/verrouillées disparaissent, le reste se place « naturellement »
        # (répulsion + attraction par le netlist). Phase B : elles reviennent, le reste s'adapte.
        ghost = fixed | locked
        active = [u for u in units if u.ref not in ghost]
        pairs = attraction_pairs(active)
        print("Attraction : %d paires (nets de 2 à 4 pièces, hors GND et rails)" % len(pairs))
        simulate(active, mset, [], outline, a.margin, a.settle_move, a.spring, a.iters, a.edge, pairs, a.attract)
        for _ in range(2):
            if deltas:
                best_rotations(units, movable, obstacles, a.margin, deltas, BODY_IGNORED_DEFAULT)
            iters = simulate(units, mset, obstacles, outline, a.margin, a.settle_move, a.spring, a.iters,
                             a.edge, pairs, a.attract)
    else:
        rounds = 3 if deltas else 1
        for _ in range(rounds):
            if deltas:
                best_rotations(units, movable, obstacles, a.margin, deltas, BODY_IGNORED_DEFAULT)
            iters = simulate(units, mset, obstacles, outline, a.margin, a.max_move, a.spring, a.iters, a.edge)
    plan = []
    for u in units:
        if u.ref not in movable:
            continue
        u.x = round(u.x / a.snap) * a.snap
        u.y = round(u.y / a.snap) * a.snap
    # écarte les micro-déplacements : la pièce revient à son état d'origine
    for u in units:
        if u.ref in movable and math.hypot(u.x - u.x0, u.y - u.y0) < a.min_move:
            u.x, u.y = u.x0, u.y0
            u.set_rot(u.rot0)
    after = relevant(conflicts(units, obstacles, a.margin, BODY_IGNORED_DEFAULT))
    for u in units:
        turned = round(u.rot - u.rot0) % 360 != 0
        if u.ref in movable and (turned or math.hypot(u.x - u.x0, u.y - u.y0) >= a.snap):
            plan.append({"reference": u.ref, "x": round(u.x, 4), "y": round(u.y, 4), "rotation": u.rot})
            print("  %-5s (%.3f, %.3f, %d°) -> (%.3f, %.3f, %d°)  d=%.2f mm" % (
                u.ref, u.x0, u.y0, round(u.rot0), u.x, u.y, round(u.rot),
                math.hypot(u.x - u.x0, u.y - u.y0)))
    print("Itérations : %d | pièces déplacées : %d | conflits après : %d" % (iters, len(plan), len(after)))
    for p in after:
        print("  restant : %s <-> %s" % p)
    if a.out:
        json.dump(plan, open(a.out, "w"), indent=1)
        print("Plan écrit dans %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
