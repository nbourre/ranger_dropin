"""Simulateur générique de placement pour fichiers KiCad (.kicad_pcb), avec visuel PyGame.

    python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb            # fenêtre interactive
    python -m tools.placement_sim Beaper-Esp32s3.kicad_pcb --headless --steps 600 --out plan.json

Voir README.md.
"""
from .kicad_pcb import Board, Footprint, Pad, load_board  # noqa: F401
from .world import Annealer, Config, Entity, World  # noqa: F401
