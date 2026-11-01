#!/usr/bin/env python3
"""Foto-Texturen für den 3D-Simulator (Bergtal) aufbereiten – Texturen aus eigenen Fotos von DonElektro.

Liest die PNG (1024 × 1024, nahtlos kachelbar, nur Farbe) aus einem Ordner und schreibt sie als JPG (Qualität 85) nach
simulator3d/texturen/ (benutzte) bzw. simulator3d/texturen/unbenutzt/ (nicht benutzte; dort mit .gdignore, damit Godot
sie nicht importiert und der Export nicht grösser wird).

Dabei wird die Naht in der Bildmitte geglättet: die gelieferten Kacheln wurden um eine halbe Breite verschoben und überblendet,
in Zeile/Spalte 511|512 bleibt ein harter Sprung (im Spiel ein sichtbares Gitter). Der Sprung wird über ±RAMP Pixel
verteilt (Ausgleich nur der Stufe, das Bild bleibt sonst gleich).

    python3 werkzeuge/texturen_bauen.py /pfad/zu/tex_in
"""
import os
import sys

import numpy as np
from PIL import Image

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "..", "simulator3d", "texturen")

# benutzt im Bergtal (bergtal_boden.gdshader, bergsee.gdshader, bergtal.gd _ribbon)
BENUTZT = ["wiese_alp_01", "wiese_hellgruen_01", "wiese_alp_steinig_01", "geroell_gras_02", "fels_kalk_grau_01",
           "fels_platte_hell_01", "zwergstrauch_alpenrose_01", "wald_von_oben_02", "weg_asphalt_01",
           "wasser_seegrund_flach_01"]
RAMP = 24
QUALITAET = 85


def naht_glaetten(a: np.ndarray) -> np.ndarray:
    """den Sprung zwischen Spalte 511 und 512 (und Zeile 511|512) über ±RAMP Pixel verteilen"""
    a = a.astype(np.float32)
    n = a.shape[0]
    m = n // 2
    w = np.linspace(-1.0, 1.0, 2 * RAMP)                      # -1 … +1 über die Rampe
    ramp = np.clip(1.0 - np.abs(w), 0.0, 1.0)                  # 0 am Rand, 1 an der Naht
    side = np.where(w < 0, 0.5, -0.5)                          # links +halber Sprung, rechts −halber Sprung
    for achse in (1, 0):
        b = a if achse == 1 else a.transpose(1, 0, 2)
        # Stufe = Sprung an der Naht minus der normale Unterschied benachbarter Spalten
        jump = (b[:, m, :] - b[:, m - 1, :]) - 0.5 * ((b[:, m - 1, :] - b[:, m - 2, :]) + (b[:, m + 1, :] - b[:, m, :]))
        # entlang der Naht leicht glätten (keine neuen Streifen)
        k = np.ones(9) / 9.0
        for c in range(jump.shape[1]):
            jump[:, c] = np.convolve(np.pad(jump[:, c], 4, mode="wrap"), k, mode="valid")
        for i, x in enumerate(range(m - RAMP, m + RAMP)):
            b[:, x, :] += jump * (side[i] * ramp[i])
        if achse == 0:
            a = b.transpose(1, 0, 2)
    return np.clip(a, 0, 255).astype(np.uint8)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    quelle = sys.argv[1]
    os.makedirs(os.path.join(ZIEL, "unbenutzt"), exist_ok=True)
    with open(os.path.join(ZIEL, "unbenutzt", ".gdignore"), "w") as f:
        f.write("")
    n = 0
    for fn in sorted(os.listdir(quelle)):
        if not fn.endswith(".png"):
            continue
        name = fn[:-4]
        img = np.asarray(Image.open(os.path.join(quelle, fn)).convert("RGB"))
        img = naht_glaetten(img)
        ordner = ZIEL if name in BENUTZT else os.path.join(ZIEL, "unbenutzt")
        ziel = os.path.join(ordner, name + ".jpg")
        Image.fromarray(img).save(ziel, quality=QUALITAET, optimize=True, subsampling=0 if name.startswith("weg_") else 2)
        n += 1
        print("%-34s → %s (%d kB)" % (fn, os.path.relpath(ziel, os.path.join(HIER, "..")), os.path.getsize(ziel) // 1024))
    print(n, "Texturen")


if __name__ == "__main__":
    main()
