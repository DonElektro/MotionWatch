#!/usr/bin/env python3
"""MoveEye Kiosk - Leiste «‹ Zurück zum Simulator» über dem Browser (HP_FASSUNG 8, Besitzer 12.11.2026).
hp_knoepfe.sh browser startet sie zusammen mit dem Browser und beendet sie danach. Ein schmaler Streifen ganz oben, immer
im Vordergrund (ohne Rahmen, der Fenstermanager fasst ihn nicht an; Openbox lässt maximierten Fenstern oben so viel Platz
frei: <margins> in openbox.xml). Antippen legt nur die leere Datei --zu an - hp_knoepfe.sh schliesst dann den Browser und
lässt den Simulator weiterlaufen. Die Leiste hat keine Rechte und führt nichts aus.

  python3 -I browser_leiste.py --zu /run/moveeye-spiel/browser_zu [--hoehe 40]
"""
import argparse
import os
import sys

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:
    tk = tkfont = None

PANEL, FG, GRAU, ORANGE, BG = "#172134", "#e6ebf4", "#9a9ea3", "#f59a4a", "#0f1624"
HOEHE = 40                                            # = <margins><top> in openbox.xml (kiosk_ein.sh, hp_update.sh)


def zu_schreiben(p):
    """leere Datei «zurück» anlegen (nie über eine Verknüpfung); False = geht nicht"""
    if not p or not os.path.isdir(os.path.dirname(p)):
        return False
    try:
        os.close(os.open(p, os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o644))
        return True
    except OSError:
        return False


class Leiste:
    def __init__(self, a):
        self.a = a
        self.root = tk.Tk(className="moveeye-browser-leiste")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        sw = self.root.winfo_screenwidth()
        h = a.hoehe
        self.root.geometry("%dx%d+0+0" % (sw, h))
        self.root.configure(bg=PANEL)
        fam = "DejaVu Sans" if "DejaVu Sans" in tkfont.families(self.root) else "Helvetica"
        fett = tkfont.Font(family=fam, size=-max(12, int(h * 0.42)), weight="bold")
        klein = tkfont.Font(family=fam, size=-max(10, int(h * 0.32)))
        self.knopf = tk.Label(self.root, text="  ‹ Zurück zum Simulator  ", bg=ORANGE, fg=BG, font=fett, cursor="hand2")
        self.knopf.pack(side="left", fill="y", padx=(6, 12), pady=4)
        self.text = tk.Label(self.root, text="Browser  ·  der Simulator ist angehalten und läuft danach weiter", bg=PANEL, fg=FG, font=klein)
        self.text.pack(side="left", fill="y")
        tk.Label(self.root, text="Ctrl + Alt + Z = zurück   ", bg=PANEL, fg=GRAU, font=klein).pack(side="right", fill="y")
        self.knopf.bind("<Button-1>", self.zurueck)
        self.gedrueckt = False
        self.tick()

    def zurueck(self, _e=None):
        self.gedrueckt = zu_schreiben(self.a.zu) or self.gedrueckt
        self.knopf.configure(text="  Zurück zum Simulator …  ")

    def tick(self):
        self.root.lift()                               # über dem Browser bleiben (auch bei Vollbild-Video)
        self.root.after(1500, self.tick)


def main():
    ap = argparse.ArgumentParser(description="MoveEye Kiosk: Leiste «Zurück zum Simulator» über dem Browser")
    ap.add_argument("--zu", default="/run/moveeye-spiel/browser_zu")
    ap.add_argument("--hoehe", type=int, default=HOEHE)
    a = ap.parse_args()
    a.hoehe = max(24, min(120, a.hoehe))
    if tk is None:
        print("browser_leiste: python3-tk fehlt", file=sys.stderr)
        return 3
    try:
        Leiste(a).root.mainloop()
    except tk.TclError as e:
        print("browser_leiste:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
