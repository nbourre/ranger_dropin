#!/usr/bin/env python3
"""Génère des modèles 3D VRML volumétriques (APPROXIMATIFS) pour les empreintes dont
KiCad ne fournit pas de modèle : L1 (Bourns SRP7028A) et SW1 (Alps SKRTLAE010).

Ce sont des blocs aux dimensions de l'empreinte (fab/courtyard), pas les modèles du
fabricant. Les remplacer par les vrais STEP si on les obtient.

Unités : le VRML de KiCad compte en 0,1 pouce (2,54 mm) ; le script convertit les mm.
Usage : python tools/make_block_models.py 3dmodels
"""
import os
import sys

U = 2.54  # 1 unité VRML = 2,54 mm


def box(cx, cy, z0, w, d, h, rgb):
    """Boîte centrée en (cx, cy), de la hauteur z0 à z0+h, dimensions en mm."""
    r, g, b = rgb
    return (
        "Transform {\n  translation %.4f %.4f %.4f\n  children Shape {\n"
        "    appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f specularColor 0.4 0.4 0.4 shininess 0.3 } }\n"
        "    geometry Box { size %.4f %.4f %.4f }\n  }\n}\n"
    ) % (cx / U, cy / U, (z0 + h / 2) / U, r, g, b, w / U, d / U, h / U)


def write(path, solids):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#VRML V2.0 utf8\n# Modele approximatif genere par tools/make_block_models.py\n")
        f.write("".join(solids))
    print("écrit", path)


def main(out):
    os.makedirs(out, exist_ok=True)
    silver, ferrite, black = (0.78, 0.78, 0.80), (0.16, 0.16, 0.18), (0.10, 0.10, 0.11)
    # L1 : Bourns SRP7028A, 7,3 x 6,6 x 2,8 mm, bornes aux deux extrémités (x = ±2,725)
    write(os.path.join(out, "L_Bourns_SRP7028A_7.3x6.6mm.wrl"), [
        box(0, 0, 0.0, 7.3, 6.6, 2.8, ferrite),
        box(-3.0, 0, 0.0, 1.3, 6.2, 0.9, silver),
        box(3.0, 0, 0.0, 1.3, 6.2, 0.9, silver),
    ])
    # SW1 : Alps SKRTLAE010, corps 4,5 x 3,39 mm (fab x ±2,25, y -1,35..2,04), hauteur 2,0 mm
    write(os.path.join(out, "SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010.wrl"), [
        box(0, 0.345, 0.0, 4.5, 3.39, 2.0, black),
        box(0, 0.345, 2.0, 3.6, 2.6, 0.1, silver),
    ])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "3dmodels")
