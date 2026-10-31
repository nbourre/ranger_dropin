"""Lecture (lecture seule) d'un fichier .kicad_pcb vers un modèle Python simple.

Le fichier n'est JAMAIS modifié : l'outil lit, simule, puis exporte un plan JSON
que l'on applique ensuite avec Konnect (set_component_placements).

Conventions KiCad (repère PCB, y vers le bas) :
  - la rotation d'une empreinte est en degrés, sens horaire à l'écran ;
  - un point local (x, y) d'une empreinte tournée de `a` degrés devient
        x' = x cos a + y sin a ,   y' = -x sin a + y cos a
  - l'angle d'une pastille est ABSOLU dans le fichier (il inclut la rotation de l'empreinte).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------- s-expression
_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


def parse_sexpr(text: str):
    """Analyse une s-expression KiCad en listes imbriquées (chaînes, listes)."""
    stack, cur, pos, n = [], [], 0, len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done, cur = cur, stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(("s", m.group(3)))
        else:
            cur.append(m.group(4))
    root = cur[0] if cur else []
    return _untag(root)


def _untag(node):
    if isinstance(node, tuple):
        return node[1]
    if isinstance(node, list):
        return [_untag(c) for c in node]
    return node


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    r = kids(node, name)
    return r[0] if r else None


def rot_pt(x: float, y: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c


# ----------------------------------------------------------------- modèle
@dataclass
class Pad:
    """Pastille, en coordonnées LOCALES de l'empreinte (position non tournée)."""
    number: str
    ptype: str          # smd, thru_hole, np_thru_hole, connect
    shape: str          # rect, circle, oval, roundrect, custom...
    x: float            # position locale
    y: float
    w: float            # taille locale (avant rotation de l'empreinte)
    h: float
    net: str = ""
    drill: float = 0.0
    layers: tuple = ()


@dataclass
class Footprint:
    """Un composant tel qu'il est dans le fichier (état d'origine, immuable ensuite)."""
    ref: str
    value: str
    lib_id: str
    layer: str
    x: float
    y: float
    rot: float
    locked: bool
    attr: str                                   # "smd", "through_hole" ou ""
    uuid: str
    path: str
    props: dict = field(default_factory=dict)   # toutes les propriétés (Reference, Value, LCSC...)
    pads: list = field(default_factory=list)
    court: tuple | None = None                  # (xmin, ymin, xmax, ymax) local, courtyard
    silk: list = field(default_factory=list)    # segments locaux ((x1,y1),(x2,y2))
    text_off: tuple | None = None               # (x, y, angle, taille) du texte de référence, local
    text_hidden: bool = False
    height: float = 0.0                         # hauteur 3D connue (mm), 0 = inconnue


@dataclass
class Board:
    path: str
    footprints: list
    outline: list                                # segments ((x1,y1),(x2,y2)) d'Edge.Cuts
    bbox: tuple | None                           # (xmin, ymin, xmax, ymax) du contour
    texts: list = field(default_factory=list)    # textes libres : (texte, x, y, angle, taille, couche)


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _segments(g, layer_ok):
    """Segments d'un graphique fp_/gr_ line/rect/circle/arc/poly (arcs et cercles approximés)."""
    t = g[0].split("_", 1)[1]
    ly = kid(g, "layer")
    if not ly or not layer_ok(ly[1]):
        return []
    out = []
    if t == "line":
        s, e = kid(g, "start"), kid(g, "end")
        out.append(((_f(s[1]), _f(s[2])), (_f(e[1]), _f(e[2]))))
    elif t == "rect":
        s, e = kid(g, "start"), kid(g, "end")
        x1, y1, x2, y2 = _f(s[1]), _f(s[2]), _f(e[1]), _f(e[2])
        pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
        out += list(zip(pts[:-1], pts[1:]))
    elif t == "circle":
        c, e = kid(g, "center"), kid(g, "end")
        cx, cy = _f(c[1]), _f(c[2])
        r = math.hypot(_f(e[1]) - cx, _f(e[2]) - cy)
        pts = [(cx + r * math.cos(a * math.pi / 12), cy + r * math.sin(a * math.pi / 12)) for a in range(25)]
        out += list(zip(pts[:-1], pts[1:]))
    elif t == "arc":
        s, m, e = kid(g, "start"), kid(g, "mid"), kid(g, "end")
        if s and m and e:
            pts = [(_f(s[1]), _f(s[2])), (_f(m[1]), _f(m[2])), (_f(e[1]), _f(e[2]))]
            out += list(zip(pts[:-1], pts[1:]))  # approximation grossière suffisante pour l'affichage
    elif t == "poly":
        pl = kid(g, "pts")
        if pl:
            pts = [(_f(p[1]), _f(p[2])) for p in kids(pl, "xy")]
            if pts:
                out += list(zip(pts, pts[1:] + pts[:1]))
    return out


def _parse_footprint(fp) -> Footprint:
    at = kid(fp, "at")
    props = {p[1]: p[2] for p in kids(fp, "property") if len(p) > 2}
    ref = props.get("Reference", "?")
    lk = kid(fp, "locked")
    attr_node = kid(fp, "attr")
    attr = ""
    if attr_node:
        for a in attr_node[1:]:
            if a in ("smd", "through_hole"):
                attr = a
    pads = []
    for pd in kids(fp, "pad"):
        pa, sz = kid(pd, "at"), kid(pd, "size")
        nn = kid(pd, "net")
        net = nn[-1] if nn and len(nn) > 1 else ""
        dr = kid(pd, "drill")
        ly = kid(pd, "layers")
        pads.append(Pad(
            number=str(pd[1]), ptype=pd[2] if len(pd) > 2 else "", shape=pd[3] if len(pd) > 3 else "",
            x=_f(pa[1]) if pa else 0.0, y=_f(pa[2]) if pa else 0.0,
            w=_f(sz[1]) if sz else 0.0, h=_f(sz[2]) if sz else 0.0,
            net=net, drill=_f(dr[1]) if dr and len(dr) > 1 and dr[1] not in ("oval",) else 0.0,
            layers=tuple(ly[1:]) if ly else ()))
    # courtyard puis repli sur les pastilles
    segs = []
    for g in fp:
        if isinstance(g, list) and g and g[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
            segs += _segments(g, lambda l: l in ("F.CrtYd", "B.CrtYd"))
    court = None
    if segs:
        xs = [p[0] for s in segs for p in s]
        ys = [p[1] for s in segs for p in s]
        court = (min(xs), min(ys), max(xs), max(ys))
    elif pads:
        xs = [p.x - p.w / 2 for p in pads] + [p.x + p.w / 2 for p in pads]
        ys = [p.y - p.h / 2 for p in pads] + [p.y + p.h / 2 for p in pads]
        court = (min(xs) - 0.25, min(ys) - 0.25, max(xs) + 0.25, max(ys) + 0.25)
    silk = []
    for g in fp:
        if isinstance(g, list) and g and g[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
            silk += _segments(g, lambda l: l in ("F.SilkS", "B.SilkS"))
    # texte de référence
    text_off, hidden = None, False
    for p in kids(fp, "property"):
        if p[1] == "Reference":
            pa = kid(p, "at")
            font = kid(kid(p, "effects") or [], "font") if kid(p, "effects") else None
            sz = kid(font, "size") if font else None
            hd = kid(p, "hide")
            hidden = bool(hd and len(hd) > 1 and hd[1] == "yes")
            if pa:
                text_off = (_f(pa[1]), _f(pa[2]), _f(pa[3]) if len(pa) > 3 else 0.0, _f(sz[1], 1.0) if sz else 1.0)
    uuid_n = kid(fp, "uuid")
    path_n = kid(fp, "path")
    return Footprint(
        ref=ref, value=props.get("Value", ""), lib_id=fp[1], layer=(kid(fp, "layer") or ["", "F.Cu"])[1],
        x=_f(at[1]), y=_f(at[2]), rot=_f(at[3]) if len(at) > 3 else 0.0,
        locked=bool(lk and len(lk) > 1 and lk[1] == "yes"), attr=attr,
        uuid=uuid_n[1] if uuid_n else "", path=path_n[1] if path_n else "",
        props=props, pads=pads, court=court, silk=silk, text_off=text_off, text_hidden=hidden)


def load_board(path: str) -> Board:
    """Lit un .kicad_pcb et renvoie un Board (empreintes, contour, textes libres)."""
    with open(path, encoding="utf-8") as fh:
        root = parse_sexpr(fh.read())
    fps = [_parse_footprint(fp) for fp in kids(root, "footprint")]
    outline = []
    for g in root:
        if isinstance(g, list) and g and g[0] in ("gr_line", "gr_rect", "gr_circle", "gr_arc", "gr_poly"):
            outline += _segments(g, lambda l: l == "Edge.Cuts")
    bbox = None
    if outline:
        xs = [p[0] for s in outline for p in s]
        ys = [p[1] for s in outline for p in s]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    texts = []
    for t in kids(root, "gr_text"):
        at, ly = kid(t, "at"), kid(t, "layer")
        font = kid(kid(t, "effects") or [], "font") if kid(t, "effects") else None
        sz = kid(font, "size") if font else None
        if at and ly:
            texts.append((t[1], _f(at[1]), _f(at[2]), _f(at[3]) if len(at) > 3 else 0.0,
                          _f(sz[1], 1.0) if sz else 1.0, ly[1]))
    return Board(path=path, footprints=fps, outline=outline, bbox=bbox, texts=texts)
