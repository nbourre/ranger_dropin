"""Visualisation interactive PyGame du monde de simulation.

Souris : clic gauche = sélectionner / glisser une pièce ; clic droit ou milieu = déplacer la vue ;
molette = zoom. Touche H dans la fenêtre pour la liste complète des raccourcis.
"""
from __future__ import annotations

import colorsys
import json
import math
import os
import time
import zlib

import pygame

from .world import Annealer, Entity, World

BG = (22, 26, 30)
BOARD = (36, 52, 44)
OUTLINE = (210, 200, 120)
GRID = (40, 46, 50)
TXT = (230, 230, 230)
DIM = (150, 156, 160)
ALERT = (240, 90, 80)
SEL = (80, 200, 255)
FORCE_COLORS = {"overlap": (255, 90, 80), "separation": (230, 120, 255), "zone": (255, 150, 40), "nets": (90, 200, 255), "boundary": (255, 210, 70), "home": (120, 230, 120)}
FORCE_LABELS = {"overlap": "répulsion", "separation": "séparation", "zone": "zone broches", "nets": "attraction nets", "boundary": "rappel bord", "home": "rappel origine"}

HELP = [
    "SOURIS  clic gauche : sélection / glisser   clic droit ou milieu : déplacer la vue   molette : zoom",
    "Espace  physique (répulsion + attraction)    A  recuit simulé (optimiseur)",
    "R / Maj+R  tourner de 90°    L  figer / libérer    V  fantôme (ne repousse pas)    Q  grille aimantée",
    "X  zone de broches (la pièce sélectionnée : les autres ne restent pas sur ses broches)",
    "G  forces (flèches : blanc = total, rouge = répulsion, bleu = nets, jaune = bord, vert = origine)",
    "N  chevelu    C  courtyards    P  pastilles    T  références    S  sérigraphie    I  infos",
    "F  ajuster la vue    Z  tout remettre à l'origine    Ctrl+Z  annuler    E  exporter le plan JSON",
    "K  capture PNG    -/+  zoom    flèches  vue    Échap  quitter",
    "Réglages : boutons - / + du panneau (souris)  ou  F1/F2 répulsion   F3/F4 attraction   F5/F6 marge   ([ ] , . ; ' marchent aussi)",
]


def net_color(net: str):
    if not net:
        return (120, 120, 120)
    h = (zlib.crc32(net.encode()) % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.55, 0.95)
    return (int(r * 255), int(g * 255), int(b * 255))


class App:
    def __init__(self, world: World, size=(1500, 950), out_path: str = "placement_plan.json",
                 snap: float = 0.05, headless: bool = False):
        pygame.init()
        pygame.display.set_caption("Simulation de placement KiCad")
        flags = pygame.RESIZABLE
        self.screen = pygame.display.set_mode(size, flags)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 13)
        self.small = pygame.font.SysFont("consolas", 11)
        self.big = pygame.font.SysFont("consolas", 16, bold=True)
        self.w = world
        self.out_path = out_path
        self.snap_value = snap
        self.snap_on = True
        self.scale = 8.0
        self.ox = self.oy = 0.0
        self.selected: Entity | None = None
        self.hover: Entity | None = None
        self.drag: tuple[Entity, float, float] | None = None
        self.panning = False
        self.pan_last = (0, 0)
        self.running_physics = False
        self.confirm_quit = False
        self.force_cache = ({}, {})
        self.buttons: list = []      # (rect, paramètre, ±1), reconstruits à chaque rendu
        self.panel_rects: list = []
        self.annealer: Annealer | None = None
        self.show = dict(forces=False, ratsnest=True, court=True, pads=True, labels=True, silk=True, info=True, help=False)
        self.undo: list[dict] = []
        self.message = ""
        self.message_t = 0.0
        self.last_metrics = {}
        self.metrics_t = 0.0
        self.fit()

    # ------------------------------------------------------------ vue
    def fit(self):
        W, H = self.screen.get_size()
        b = self.w.bbox or (0, 0, 100, 100)
        pad = 40
        self.scale = max(1.0, min((W - 2 * pad) / (b[2] - b[0]), (H - 2 * pad) / (b[3] - b[1])))
        self.ox = W / 2 - (b[0] + b[2]) / 2 * self.scale
        self.oy = H / 2 - (b[1] + b[3]) / 2 * self.scale

    def s(self, x, y):
        return (x * self.scale + self.ox, y * self.scale + self.oy)

    def inv(self, sx, sy):
        return ((sx - self.ox) / self.scale, (sy - self.oy) / self.scale)

    def zoom_at(self, sx, sy, factor):
        wx, wy = self.inv(sx, sy)
        self.scale = max(1.0, min(200.0, self.scale * factor))
        self.ox = sx - wx * self.scale
        self.oy = sy - wy * self.scale

    def say(self, text):
        self.message, self.message_t = text, time.time()

    # ------------------------------------------------------------ interaction
    def entity_at(self, sx, sy):
        wx, wy = self.inv(sx, sy)
        best, area = None, 1e18
        for e in self.w.entities:
            b = e.court_aabb()
            if b[0] <= wx <= b[2] and b[1] <= wy <= b[3]:
                a = (b[2] - b[0]) * (b[3] - b[1])
                if a < area:
                    best, area = e, a
        return best

    def push_undo(self):
        self.undo.append(self.w.snapshot())
        del self.undo[:-60]

    def handle(self, ev) -> bool:
        if ev.type == pygame.QUIT:
            self.confirm_quit = True
            return True
        if ev.type == pygame.VIDEORESIZE:
            return True
        if self.confirm_quit:  # la boîte de confirmation capte tout le reste
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_o, pygame.K_y):
                    return False
                self.confirm_quit = False
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1 and self.click_panel(ev.pos):
                return True
            if ev.button == 1:
                e = self.entity_at(*ev.pos)
                self.selected = e
                if e and e.movable:
                    self.push_undo()
                    wx, wy = self.inv(*ev.pos)
                    self.drag = (e, wx - e.x, wy - e.y)
                elif e:
                    self.say("%s est verrouillé / figé (L pour libérer un figé)" % e.ref)
            elif ev.button in (2, 3):
                self.panning, self.pan_last = True, ev.pos
            elif ev.button == 4:
                self.zoom_at(*ev.pos, 1.15)
            elif ev.button == 5:
                self.zoom_at(*ev.pos, 1 / 1.15)
        elif ev.type == pygame.MOUSEBUTTONUP:
            if ev.button == 1:
                self.drag = None
            elif ev.button in (2, 3):
                self.panning = False
        elif ev.type == pygame.MOUSEMOTION:
            if self.panning:
                self.ox += ev.pos[0] - self.pan_last[0]
                self.oy += ev.pos[1] - self.pan_last[1]
                self.pan_last = ev.pos
            elif self.drag:
                e, dx, dy = self.drag
                wx, wy = self.inv(*ev.pos)
                x, y = wx - dx, wy - dy
                if self.snap_on and self.snap_value:
                    x, y = round(x / self.snap_value) * self.snap_value, round(y / self.snap_value) * self.snap_value
                e.x, e.y, e.vx, e.vy = x, y, 0.0, 0.0
            else:
                self.hover = self.entity_at(*ev.pos)
        elif ev.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            self.zoom_at(mx, my, 1.15 ** ev.y)
        elif ev.type == pygame.KEYDOWN:
            return self.key(ev)
        return True

    def key(self, ev) -> bool:
        k, mods = ev.key, pygame.key.get_mods()
        if k == pygame.K_ESCAPE:
            self.confirm_quit = True
            return True
        if k == pygame.K_SPACE:
            self.running_physics = not self.running_physics
            self.say("Physique " + ("ACTIVE" if self.running_physics else "en pause"))
        elif k == pygame.K_a:
            if self.annealer:
                self.annealer = None
                self.say("Recuit arrêté")
            else:
                self.push_undo()
                self.annealer = Annealer(self.w)
                self.say("Recuit simulé démarré")
        elif k == pygame.K_r and self.selected and self.selected.movable:
            self.push_undo()
            self.selected.rotate90(-1 if mods & pygame.KMOD_SHIFT else 1)
        elif k == pygame.K_l and self.selected:
            if self.selected.locked:
                self.say("%s : verrou KiCad, non modifiable ici" % self.selected.ref)
            else:
                self.selected.pinned = not self.selected.pinned
                self.say("%s %s" % (self.selected.ref, "figé" if self.selected.pinned else "libéré"))
        elif k == pygame.K_v and self.selected:
            self.selected.ghost = not self.selected.ghost
            self.say("%s %s" % (self.selected.ref, "fantôme" if self.selected.ghost else "solide"))
        elif k == pygame.K_x and self.selected:
            self.selected.keepout = not self.selected.keepout
            self.say("Zone de broches de %s %s" % (self.selected.ref, "ACTIVE" if self.selected.keepout else "retirée"))
        elif k == pygame.K_g:
            self.show["forces"] = not self.show["forces"]
            self.force_cache = self.w.compute_forces()
            self.say("Forces " + ("affichées" if self.show["forces"] else "masquées"))
        elif k == pygame.K_n:
            self.show["ratsnest"] = not self.show["ratsnest"]
        elif k == pygame.K_c:
            self.show["court"] = not self.show["court"]
        elif k == pygame.K_p:
            self.show["pads"] = not self.show["pads"]
        elif k == pygame.K_t:
            self.show["labels"] = not self.show["labels"]
        elif k == pygame.K_s:
            self.show["silk"] = not self.show["silk"]
        elif k == pygame.K_i:
            self.show["info"] = not self.show["info"]
        elif k == pygame.K_h:
            self.show["help"] = not self.show["help"]
        elif k == pygame.K_f:
            self.fit()
        elif k == pygame.K_q:
            self.snap_on = not self.snap_on
            self.say("Grille aimantée " + ("ON (%.2f mm)" % self.snap_value if self.snap_on else "OFF"))
        elif k == pygame.K_z and (mods & pygame.KMOD_CTRL):
            if self.undo:
                self.w.restore(self.undo.pop())
                self.say("Annulé")
        elif k == pygame.K_z:
            self.push_undo()
            self.w.reset()
            self.say("Positions d'origine restaurées")
        elif k == pygame.K_e:
            self.export()
        elif k == pygame.K_k:
            self.screenshot()
        elif k in (pygame.K_LEFTBRACKET, pygame.K_F1):
            self.adjust("repulsion", -1)
        elif k in (pygame.K_RIGHTBRACKET, pygame.K_F2):
            self.adjust("repulsion", 1)
        elif k in (pygame.K_COMMA, pygame.K_F3):
            self.adjust("attraction", -1)
        elif k in (pygame.K_PERIOD, pygame.K_F4):
            self.adjust("attraction", 1)
        elif k in (pygame.K_SEMICOLON, pygame.K_F5):
            self.adjust("margin", -1)
        elif k in (pygame.K_QUOTE, pygame.K_F6):
            self.adjust("margin", 1)
        elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.zoom_at(*[v / 2 for v in self.screen.get_size()], 1 / 1.2)
        elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.zoom_at(*[v / 2 for v in self.screen.get_size()], 1.2)
        elif k == pygame.K_LEFT:
            self.ox += 60
        elif k == pygame.K_RIGHT:
            self.ox -= 60
        elif k == pygame.K_UP:
            self.oy += 60
        elif k == pygame.K_DOWN:
            self.oy -= 60
        return True

    # paramètres réglables : nom -> (libellé, valeur max de la jauge)
    PARAMS = {"repulsion": ("répulsion", 3.0), "sep_weight": ("séparation", 0.3),
              "sep_radius": ("rayon sép. mm", 8.0), "attraction": ("attraction", 0.05),
              "zone_weight": ("zone broches", 3.0), "margin": ("marge (mm)", 2.0), "home": ("rappel origine", 0.05)}

    def adjust(self, name, direction):
        cfg = self.w.cfg
        v = getattr(cfg, name)
        if name in ("margin", "sep_radius"):
            v = max(0.0, round(v + (0.1 if name == "margin" else 0.5) * direction, 2))
        elif direction > 0:
            v = v * 1.25 if v > 0 else {"repulsion": 0.05, "sep_weight": 0.02, "zone_weight": 0.1, "attraction": 0.002, "home": 0.002}[name]
        else:
            v = v / 1.25 if v > 1e-3 else 0.0
        setattr(cfg, name, v)
        self.say("%s = %.3f" % (self.PARAMS[name][0], v))

    def click_panel(self, pos) -> bool:
        for rect, name, d in self.buttons:
            if rect.collidepoint(pos):
                self.adjust(name, d)
                return True
        return any(r.collidepoint(pos) for r in self.panel_rects)

    def export(self):
        plan = self.w.plan()
        with open(self.out_path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=1)
        self.say("Plan exporté : %d pièces -> %s" % (len(plan), self.out_path))

    def screenshot(self, path=None):
        path = path or os.path.splitext(self.out_path)[0] + "_capture.png"
        self.render()
        pygame.image.save(self.screen, path)
        self.say("Capture : " + path)
        return path

    # ------------------------------------------------------------ simulation
    def update(self):
        if self.running_physics:
            for _ in range(2):
                self.w.step()
        if self.annealer:
            self.annealer.run(300)
            if self.annealer.iter >= self.annealer.total:
                self.annealer = None
                self.say("Recuit terminé")
        if (self.show["forces"] and (self.running_physics or self.drag)) or time.time() - self.metrics_t > 0.25:
            self.force_cache = self.w.compute_forces()
        if time.time() - self.metrics_t > 0.25:
            self.last_metrics = self.w.metrics()
            self.metrics_t = time.time()

    # ------------------------------------------------------------ rendu
    def rrect(self, surf, color, x, y, w, h, width=0, radius=0):
        pygame.draw.rect(surf, color, pygame.Rect(x, y, max(1, w), max(1, h)), width, radius)

    def draw_zones(self, surf):
        """Zones de broches (pièces « keepout », touche X) : hachures orangées translucides."""
        for ref, z in self.w.zones():
            x0, y0 = self.s(z[0], z[1])
            r = pygame.Rect(x0, y0, (z[2] - z[0]) * self.scale, (z[3] - z[1]) * self.scale)
            ov = pygame.Surface(r.size, pygame.SRCALPHA)
            ov.fill((255, 150, 40, 45))
            surf.blit(ov, r.topleft)
            pygame.draw.rect(surf, (255, 150, 40), r, 1)

    def draw_forces(self, surf):
        parts, total = self.force_cache
        gain, cap = 10.0, 15.0  # mm affichés par unité de force ; longueur maximale

        def arrow(e, f, col, width):
            n = math.hypot(*f)
            if n < 0.005:
                return
            L = min(n * gain, cap)
            b = e.court_aabb()
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            a = self.s(cx, cy)
            z = self.s(cx + f[0] / n * L, cy + f[1] / n * L)
            pygame.draw.line(surf, col, a, z, width)
            ang = math.atan2(z[1] - a[1], z[0] - a[0])
            for d in (2.6, -2.6):  # pointe de la flèche
                pygame.draw.line(surf, col, z, (z[0] + 7 * math.cos(ang + d), z[1] + 7 * math.sin(ang + d)), width)

        sel = self.selected or self.hover
        for e in self.w.entities:
            if not e.movable or e.ref not in total:
                continue
            if sel is e:  # détail par force pour la pièce courante
                for name, d in parts.items():
                    arrow(e, d[e.ref], FORCE_COLORS.get(name, (170, 170, 170)), 2)
            arrow(e, total[e.ref], (255, 255, 255), 3 if sel is e else 1)

    def draw_ratsnest(self, surf):
        for name, pins in self.w.sig_nets.items():
            pts = [e.world_pads()[i] for e, i in pins]
            ents = {e.ref for e, _ in pins}
            if len(ents) < 2 or len(ents) > 12:
                continue
            col = net_color(name)
            col = (col[0] // 2 + 40, col[1] // 2 + 40, col[2] // 2 + 40)
            # arbre couvrant minimal (Prim) sur les pastilles
            inside, outside = [pts[0]], pts[1:]
            while outside:
                best = min(((a, b) for a in inside for b in outside),
                           key=lambda t: (t[0].x - t[1].x) ** 2 + (t[0].y - t[1].y) ** 2)
                pygame.draw.aaline(surf, col, self.s(best[0].x, best[0].y), self.s(best[1].x, best[1].y))
                inside.append(best[1])
                outside.remove(best[1])

    def draw_entity(self, surf, e: Entity, bad: set):
        sc = self.scale
        b = e.court_aabb()
        x0, y0 = self.s(b[0], b[1])
        w, h = (b[2] - b[0]) * sc, (b[3] - b[1]) * sc
        if self.show["court"]:
            fill = (60, 50, 50) if e.ref in bad else (48, 62, 74)
            if e.ghost:
                fill = (46, 46, 60)
            s2 = pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)
            s2.fill((*fill, 150))
            surf.blit(s2, (x0, y0))
            col = ALERT if e.ref in bad else ((110, 150, 190) if e.movable else (200, 140, 60))
            self.rrect(surf, col, x0, y0, w, h, 1)
        if self.show["silk"]:
            for a, c in e.silk_segments():
                pygame.draw.line(surf, (190, 190, 150), self.s(*a), self.s(*c), 1)
        if self.show["pads"]:
            for p in e.world_pads():
                px, py = self.s(p.x - p.w / 2, p.y - p.h / 2)
                pw, ph = max(2, p.w * sc), max(2, p.h * sc)
                col = net_color(p.net)
                if p.ptype in ("thru_hole", "np_thru_hole"):
                    col = (col[0] * 4 // 5, col[1] * 4 // 5, col[2] * 4 // 5)
                if p.shape in ("circle", "oval"):
                    pygame.draw.ellipse(surf, col, pygame.Rect(px, py, pw, ph))
                else:
                    self.rrect(surf, col, px, py, pw, ph)
        if e is self.selected:
            self.rrect(surf, SEL, x0 - 2, y0 - 2, w + 4, h + 4, 2)
        elif e is self.hover:
            self.rrect(surf, (255, 255, 255), x0 - 1, y0 - 1, w + 2, h + 2, 1)
        if self.show["labels"] and (w > 14 or e is self.selected):
            txt = self.small.render(e.ref, True, TXT if e.movable else (240, 180, 100))
            cx, cy = self.s(e.x, e.y)
            surf.blit(txt, (cx - txt.get_width() / 2, cy - txt.get_height() / 2))

    def render(self):
        surf = self.screen
        W, H = surf.get_size()
        surf.fill(BG)
        bb = self.w.bbox
        if bb:
            x0, y0 = self.s(bb[0], bb[1])
            self.rrect(surf, BOARD, x0, y0, (bb[2] - bb[0]) * self.scale, (bb[3] - bb[1]) * self.scale)
        for a, c in self.w.board.outline:
            pygame.draw.line(surf, OUTLINE, self.s(*a), self.s(*c), 2)
        bad = set()
        for a, c, _, _ in self.w.overlapping_pairs():
            bad.add(a.ref)
            bad.add(c.ref)
        for e in sorted(self.w.entities, key=lambda e: -((e.court_aabb()[2] - e.court_aabb()[0]) * (e.court_aabb()[3] - e.court_aabb()[1]))):
            self.draw_entity(surf, e, bad)
        self.draw_zones(surf)
        if self.show["ratsnest"]:
            self.draw_ratsnest(surf)
        if self.show["forces"]:
            self.draw_forces(surf)
        sel_net = None
        e = self.selected or self.hover
        if e:
            # surligne les liaisons de la pièce courante
            for p in e.world_pads():
                if p.net and p.net in self.w.sig_nets:
                    for o, i in self.w.sig_nets[p.net]:
                        if o is not e:
                            q = o.world_pads()[i]
                            pygame.draw.line(surf, net_color(p.net), self.s(p.x, p.y), self.s(q.x, q.y), 2)
        self.draw_hud(surf, W, H)

    def draw_panel(self, surf, W):
        """Fenêtre en haut à droite : réglages (boutons - / +) et force réellement appliquée."""
        self.buttons, self.panel_rects = [], []
        if not self.show["info"]:
            return
        cfg, parts = self.w.cfg, self.force_cache[0]
        pw, x0, y = 330, W - 336, 6
        rows = len(self.PARAMS) + 1 + len(parts) * 2 + 2
        panel = pygame.Rect(x0, y, pw, rows * 22 + 20)
        self.panel_rects.append(panel)
        bg = pygame.Surface(panel.size, pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        surf.blit(bg, panel.topleft)
        y += 8
        surf.blit(self.big.render("Réglages", True, TXT), (x0 + 8, y))
        surf.blit(self.small.render("boutons ou F1-F6", True, DIM), (x0 + 190, y + 3))
        y += 24
        key_of = {"repulsion": "overlap", "sep_weight": "separation", "sep_radius": "separation", "zone_weight": "zone",
                  "attraction": "nets", "home": "home"}
        for name, (label, vmax) in self.PARAMS.items():
            v = getattr(cfg, name)
            col = FORCE_COLORS.get(key_of.get(name, ""), (170, 170, 170))
            surf.blit(self.font.render("%-15s %6.3f" % (label, v), True, TXT), (x0 + 8, y))
            bar = pygame.Rect(x0 + 172, y + 3, 78, 10)
            pygame.draw.rect(surf, (50, 54, 60), bar)
            pygame.draw.rect(surf, col, (bar.x, bar.y, int(bar.w * min(1.0, v / vmax)), bar.h))
            for i, (sym, d) in enumerate((("-", -1), ("+", 1))):
                r = pygame.Rect(x0 + 268 + i * 28, y, 24, 18)
                pygame.draw.rect(surf, (70, 76, 86), r, border_radius=3)
                t = self.font.render(sym, True, TXT)
                surf.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))
                self.buttons.append((r, name, d))
            y += 22
        y += 6
        surf.blit(self.big.render("Force appliquée", True, TXT), (x0 + 8, y))
        y += 22
        for name, d in parts.items():
            mags = [math.hypot(*f) for f in d.values()]
            act = [m for m in mags if m > 0.005]
            mean = sum(act) / len(act) if act else 0.0
            col = FORCE_COLORS.get(name, (170, 170, 170))
            surf.blit(self.font.render("%-15s" % FORCE_LABELS.get(name, name), True, col), (x0 + 8, y))
            bar = pygame.Rect(x0 + 160, y + 3, 150, 10)
            pygame.draw.rect(surf, (50, 54, 60), bar)
            pygame.draw.rect(surf, col, (bar.x, bar.y, int(bar.w * min(1.0, mean / 0.3)), bar.h))
            y += 18
            surf.blit(self.small.render("  %d pièces touchées, moy %.3f, max %.3f" % (
                len(act), mean, max(mags, default=0.0)), True, DIM), (x0 + 8, y))
            y += 18
        surf.blit(self.small.render("barre pleine = force moyenne 0.3 (pas max %.1f)" % cfg.max_step, True, DIM), (x0 + 8, y))

    def draw_hud(self, surf, W, H):
        m = self.last_metrics or self.w.metrics()
        cfg = self.w.cfg
        lines = []
        if self.show["info"]:
            lines += [
                ("Simulation de placement", self.big, TXT),
                ("physique : %s   recuit : %s" % ("ON" if self.running_physics else "off",
                                                    "%d%% T=%.2f" % (100 * self.annealer.iter // self.annealer.total, self.annealer.t)
                                                    if self.annealer else "off"), self.font, TXT),
                ("chevauchements : %d (%.1f mm2)" % (m["overlaps"], m["overlap_area"]), self.font,
                 ALERT if m["overlaps"] else (120, 220, 130)),
                ("longueur HPWL  : %.0f mm" % m["hpwl"], self.font, TXT),
                ("sur broches    : %d" % m.get("in_zone", 0), self.font, ALERT if m.get("in_zone") else TXT),
                ("hors carte     : %d   déplacées : %d (max %.1f mm)" % (m["outside"], m["moved"], m["max_disp"]), self.font, TXT),
                ("rep %.2f  att %.3f  marge %.1f" % (cfg.repulsion, cfg.attraction, cfg.margin), self.font, DIM),
                ("H : aide", self.font, DIM),
            ]
        y = 8
        if lines:
            wmax = max(f.size(t)[0] for t, f, _ in lines) + 16
            pygame.draw.rect(surf, (0, 0, 0, 120), pygame.Rect(6, 6, wmax, len(lines) * 18 + 8), border_radius=4)
            s2 = pygame.Surface((wmax, len(lines) * 18 + 8), pygame.SRCALPHA)
            s2.fill((0, 0, 0, 150))
            surf.blit(s2, (6, 6))
            for t, f, c in lines:
                surf.blit(f.render(t, True, c), (14, y + 2))
                y += 18
        self.draw_panel(surf, W)
        e = self.selected or self.hover
        if e:
            nets = sorted({p.net for p in e.pads if p.net})
            info = [
                "%s  =  %s" % (e.ref, e.value),
                e.lib_id,
                "x %.3f  y %.3f  rot %.0f°  couche %s  %s" % (e.x, e.y, e.rot % 360, e.layer, e.attr),
                "verrou %s   figé %s   fantôme %s" % ("oui" if e.locked else "non", "oui" if e.pinned else "non",
                                                       "oui" if e.ghost else "non"),
                "%d pastilles ; nets : %s" % (len(e.pads), ", ".join(nets)[:90]),
            ]
            for k in ("LCSC", "Datasheet", "Description"):
                if e.props.get(k):
                    info.append("%s : %s" % (k, e.props[k][:80]))
            if self.show["forces"]:
                parts, total = self.force_cache
                if e.ref in total:
                    info.append("forces (flèche blanche = total ; mm affichés = 10 x force) :")
                    for name, d in parts.items():
                        fx, fy = d[e.ref]
                        info.append("  %-16s fx %+.3f  fy %+.3f  |%.3f|" % (
                            FORCE_LABELS.get(name, name), fx, fy, math.hypot(fx, fy)))
                    fx, fy = total[e.ref]
                    info.append("  %-16s fx %+.3f  fy %+.3f  |%.3f|" % ("TOTAL", fx, fy, math.hypot(fx, fy)))
                else:
                    info.append("forces : aucune (pièce verrouillée ou figée)")
            wmax = max(self.font.size(t)[0] for t in info) + 16
            h = len(info) * 17 + 10
            s2 = pygame.Surface((wmax, h), pygame.SRCALPHA)
            s2.fill((0, 0, 0, 170))
            surf.blit(s2, (6, H - h - 6))
            for i, t in enumerate(info):
                surf.blit(self.font.render(t, True, SEL if i == 0 else TXT), (14, H - h - 2 + i * 17))
        if self.message and time.time() - self.message_t < 4:
            t = self.font.render(self.message, True, (255, 230, 120))
            surf.blit(t, (W - t.get_width() - 12, H - 24))
        if self.show["help"]:
            wmax = max(self.font.size(t)[0] for t in HELP) + 24
            h = len(HELP) * 20 + 16
            s2 = pygame.Surface((wmax, h), pygame.SRCALPHA)
            s2.fill((0, 0, 0, 215))
            surf.blit(s2, (W / 2 - wmax / 2, 60))
            for i, t in enumerate(HELP):
                surf.blit(self.font.render(t, True, TXT), (W / 2 - wmax / 2 + 12, 68 + i * 20))
        if self.confirm_quit:
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 140))
            surf.blit(dim, (0, 0))
            n = sum(1 for e in self.w.entities if e.moved())
            lines = [("Quitter la simulation ?", self.big, TXT),
                     ("%d pièce(s) déplacée(s) ; le plan non exporté (E) sera perdu." % n, self.font, TXT),
                     ("Entrée / O : quitter      toute autre touche : continuer", self.font, DIM)]
            wmax = max(f.size(t)[0] for t, f, _ in lines) + 40
            h = len(lines) * 26 + 24
            box = pygame.Rect(W // 2 - wmax // 2, H // 2 - h // 2, wmax, h)
            pygame.draw.rect(surf, (30, 32, 40), box, border_radius=6)
            pygame.draw.rect(surf, ALERT, box, 2, border_radius=6)
            for i, (t, f, c) in enumerate(lines):
                r = f.render(t, True, c)
                surf.blit(r, (W // 2 - r.get_width() // 2, box.y + 14 + i * 26))

    # ------------------------------------------------------------ boucle
    def run(self):
        alive = True
        while alive:
            for ev in pygame.event.get():
                alive = self.handle(ev) and alive
            self.update()
            self.render()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
