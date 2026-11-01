#!/usr/bin/env python3
"""Ruhebild (MoveEye 639y): das Startbild des Simulators (simulator3d/ruhebild_start.png, project.godot
application/boot_splash/image) - dunkler Verlauf, zwei Bergketten, ein paar Sterne, das MoveEye-Symbol und «MoveEye Sim
startet …». Gleiches Aussehen wie das Ruhebild von MoveEye (quelle/639y_ruhebild.py) und der Hintergrund des Update-Fensters
(simulator3d/scripts/ruhebild.gd). Still, nichts bewegt sich.

    python3 werkzeuge/ruhebild_start_bauen.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HIER, "..", "simulator3d")
W, H = 1280, 720


def font(size, bold):
    for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF"):
        try:
            return ImageFont.truetype(os.path.join(d, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    top, bot = (11, 18, 32), (20, 30, 44)                      # #0b1220 -> #141e2c
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    glow = Image.new("L", (W, H), 0)                            # a soft glow behind the symbol
    ImageDraw.Draw(glow).ellipse((W * 0.2, H * 0.02, W * 0.8, H * 0.70), fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im = Image.composite(Image.new("RGB", (W, H), (42, 64, 96)), im, glow)
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for _ in range(int(W * H / 9000)):
        x, y = rnd.random() * W, rnd.random() * H * 0.55
        d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(130, 140, 150))
    for base, amp, col, ph in ((0.70, 0.10, (29, 40, 54), 0.0), (0.80, 0.07, (22, 32, 44), 1.7)):
        pts = []
        for k in range(241):
            xs = k / 240
            pts.append((xs * W, H * (base - amp * (0.55 * math.sin(xs * 6.1 + ph) + 0.30 * math.sin(xs * 13.7 + ph * 2.0)
                                                    + 0.15 * math.sin(xs * 29.0 + ph)))))
        d.polygon(pts + [(W, H), (0, H)], fill=col)
    ic = Image.open(os.path.join(SIM, "icon_sim3d.png")).convert("RGBA").resize((150, 150), Image.LANCZOS)
    im.paste(ic, ((W - 150) // 2, int(H * 0.36 - 75)), ic)
    for txt, size, col, bold, y in (("MoveEye Sim startet …", 40, (232, 238, 245), True, H * 0.52),
                                    ("Die Welt wird aufgebaut – einen Moment", 22, (139, 155, 176), False, H * 0.52 + 58)):
        f = font(size, bold)
        d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=col)
    out = os.path.join(SIM, "ruhebild_start.png")
    im.save(out, optimize=True)
    print("geschrieben:", os.path.normpath(out), os.path.getsize(out), "Bytes")


if __name__ == "__main__":
    main()
