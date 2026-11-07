#!/usr/bin/env python3
"""MoveEye Kiosk - Fenster «Controller koppeln»: legt die Wunsch-Datei an (der Dienst moveeye-controller-koppeln koppelt
als root einen PS5-Controller per Bluetooth, controller_koppeln.sh) und zeigt im Vordergrund, wie weit es ist.
Gestartet vom Knopf «Controller koppeln» im Testbild (testbild.py) und mit Ctrl+Alt+B im Kiosk (kiosk_sitzung.sh koppeln).

  python3 -I controller_fenster.py [--wunsch /run/moveeye-spiel/controller_koppeln]
                                   [--status /run/moveeye-controller/status.json] [--fenster 900x420]

Nur Daten: die Wunsch-Datei ist leer, der Status (JSON, vom Dienst geschrieben) wird geprüft gelesen (Grösse, keine
Verknüpfung, nur bekannte Felder, Texte gekürzt). Esc, Klick oder eine Taste schliesst das Fenster (das Koppeln läuft weiter).
"""
import argparse
import json
import os
import stat
import sys
import time

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:                                   # python3-tk fehlt: main() endet mit Code 3 (die Daten-Teile gehen)
    tk = tkfont = None

BG, PANEL, FG, GRAU, ORANGE, GRUEN, ROT = "#0f1624", "#172134", "#e6ebf4", "#9a9ea3", "#f59a4a", "#3ecf8e", "#ef5b5b"
LAEUFT = ("start", "suche", "koppeln")
SCHRITTE = LAEUFT + ("fertig", "kein_adapter", "nicht_gefunden", "fehler")
OHNE_DIENST_S = 15           # so lange ohne Antwort des Dienstes: Koppeln ist (noch) nicht eingerichtet
HINWEIS = "PS-Taste und Create-Taste gleichzeitig halten, bis das Licht schnell blinkt"


def status_lesen(p):
    """Status des Dienstes -> dict mit geprüften Feldern oder {}"""
    try:
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return {}
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > 4096:
            return {}
        d = json.loads(os.read(fd, 4097).decode("utf-8", "replace"))
    except (OSError, ValueError):
        return {}
    finally:
        os.close(fd)
    if not isinstance(d, dict) or d.get("schritt") not in SCHRITTE:
        return {}
    t = d.get("t") if isinstance(d.get("t"), int) and not isinstance(d.get("t"), bool) else 0
    rest = d.get("rest_s") if isinstance(d.get("rest_s"), int) and not isinstance(d.get("rest_s"), bool) else 0
    text = d.get("text") if isinstance(d.get("text"), str) else ""
    text = "".join(c for c in text if c.isprintable())[:120]
    ok = d.get("ok") if isinstance(d.get("ok"), bool) else None
    return {"schritt": d["schritt"], "t": t, "rest_s": max(0, min(600, rest)), "text": text, "ok": ok}


def wunsch_schreiben(p):
    """leere Wunsch-Datei anlegen (der Ordner gehört dem Benutzer des Kiosks); False = geht nicht"""
    if not p or not os.path.isdir(os.path.dirname(p)):
        return False
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o644)
        os.close(fd)
        return True
    except OSError:
        return False


class Fenster:
    def __init__(self, a):
        self.a = a
        self.t0 = time.time()
        self.root = tk.Tk(className="moveeye-controller")
        self.root.title("MoveEye – Controller koppeln")
        self.root.configure(bg=BG)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        if a.fenster:
            w, h = (int(x) for x in a.fenster.split("x"))
        else:
            w, h = min(sw - 40, max(640, int(sh * 1.15))), min(sh - 40, max(300, int(sh * 0.48)))
        self.root.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 2))
        self.root.attributes("-topmost", True)
        self.w, self.h = w, h
        self.c = tk.Canvas(self.root, width=w, height=h, bg=PANEL, highlightthickness=3, highlightbackground=ORANGE)
        self.c.pack(fill="both", expand=True)
        fam = "DejaVu Sans" if "DejaVu Sans" in tkfont.families(self.root) else "Helvetica"
        self.f_titel = tkfont.Font(family=fam, size=-max(14, int(h * 0.10)), weight="bold")
        self.f_text = tkfont.Font(family=fam, size=-max(11, int(h * 0.058)))
        self.f_klein = tkfont.Font(family=fam, size=-max(10, int(h * 0.045)))
        self.ende_t = None
        self.zustand = {}
        aktuell = status_lesen(a.status)
        laeuft = aktuell.get("schritt") in LAEUFT and time.time() - aktuell.get("t", 0) < 30
        self.wunsch_ok = True if laeuft else wunsch_schreiben(a.wunsch)    # läuft schon: nicht noch einmal anstossen
        if laeuft:
            self.t0 = min(self.t0, aktuell.get("t", self.t0))
        for ev in ("<Key>", "<Button>"):
            self.root.bind_all(ev, lambda e: self.zu())
        self.root.after(200, self.root.focus_force)
        self.tick()

    def zu(self):
        if time.time() - self.t0 > 1.0:              # die Taste, die das Fenster geöffnet hat, schliesst es nicht gleich
            self.root.destroy()

    def gamepad(self, cx, cy, s, farbe):
        c = self.c
        w, h = s * 1.6, s * 0.9
        c.create_oval(cx - w / 2, cy - h / 2, cx - w / 2 + h, cy + h / 2, fill=farbe, outline="")
        c.create_oval(cx + w / 2 - h, cy - h / 2, cx + w / 2, cy + h / 2, fill=farbe, outline="")
        c.create_rectangle(cx - w / 2 + h / 2, cy - h / 2, cx + w / 2 - h / 2, cy + h / 2, fill=farbe, outline="")
        k = s * 0.13
        x0 = cx - w * 0.27
        c.create_rectangle(x0 - k * 2.2, cy - k * 0.7, x0 + k * 2.2, cy + k * 0.7, fill=PANEL, outline="")
        c.create_rectangle(x0 - k * 0.7, cy - k * 2.2, x0 + k * 0.7, cy + k * 2.2, fill=PANEL, outline="")
        for dx, dy in ((0.2, -0.1), (0.32, 0.1)):
            x1, y1 = cx + w * dx, cy + h * dy
            c.create_oval(x1 - k, y1 - k, x1 + k, y1 + k, fill=PANEL, outline="")

    def zeichnen(self, farbe, zeile1, zeile2, zeile3):
        c, w, h = self.c, self.w, self.h
        c.delete("all")
        self.gamepad(w // 2, int(h * 0.17), int(h * 0.13), farbe)
        c.create_text(w // 2, int(h * 0.38), text="Controller koppeln", fill=FG, font=self.f_titel, anchor="center")
        c.create_text(w // 2, int(h * 0.56), text=zeile1, fill=farbe, font=self.f_text, anchor="center", width=w - 40)
        c.create_text(w // 2, int(h * 0.74), text=zeile2, fill=FG, font=self.f_text, anchor="center", width=w - 40)
        c.create_text(w // 2, int(h * 0.91), text=zeile3, fill=GRAU, font=self.f_klein, anchor="center", width=w - 40)

    def tick(self):
        jetzt = time.time()
        s = status_lesen(self.a.status)
        if s and s["t"] < self.t0 - 2:
            s = {}                                     # alter Stand (voriges Koppeln)
        if s.get("schritt") in LAEUFT and jetzt - s["t"] > s["rest_s"] + 60:
            s = {"schritt": "fehler", "ok": False, "text": "Koppeln abgebrochen – noch einmal versuchen"}
        zu_text = "Esc oder Klick: Fenster zu (das Koppeln läuft weiter)"
        if not self.wunsch_ok:
            self.zeichnen(ROT, "Koppeln geht hier nicht (Ordner /run/moveeye-spiel fehlt)",
                          "Controller per USB-C-Kabel anschliessen – das geht immer", "Esc oder Klick: zu")
            self.ende_t = self.ende_t or jetzt
        elif not s:
            if jetzt - self.t0 > OHNE_DIENST_S:
                self.zeichnen(ROT, "Koppeln ist auf diesem PC noch nicht eingerichtet (kommt mit dem HP-Update)",
                              "Controller per USB-C-Kabel anschliessen – das geht immer", "Esc oder Klick: zu")
                self.ende_t = self.ende_t or jetzt
            else:
                self.zeichnen(ORANGE, "Bluetooth wird vorbereitet …", HINWEIS, zu_text)
        elif s["schritt"] in LAEUFT:
            rest = " (noch %d s)" % s["rest_s"] if s["schritt"] == "suche" and s["rest_s"] else ""
            self.zeichnen(ORANGE, (s["text"] or "…") + rest, HINWEIS if s["schritt"] != "koppeln" else "Bitte warten …", zu_text)
        else:
            gut = s.get("ok") is True
            self.zeichnen(GRUEN if gut else ROT, s["text"] or ("Fertig" if gut else "Nicht geklappt"),
                          "Eine Taste am Controller drücken = Spielen" if gut else
                          "Ohne Bluetooth: Controller per USB-C-Kabel anschliessen", "Das Fenster geht gleich zu")
            self.ende_t = self.ende_t or jetzt
        if self.ende_t is not None and jetzt - self.ende_t > (8 if s.get("ok") is True else 20):
            self.root.destroy()
            return
        if jetzt - self.t0 > 600:                      # spätestens nach 10 Min. zu
            self.root.destroy()
            return
        self.root.after(500, self.tick)


def main():
    ap = argparse.ArgumentParser(description="MoveEye Kiosk: PS5-Controller per Bluetooth koppeln (Fenster)")
    ap.add_argument("--wunsch", default="/run/moveeye-spiel/controller_koppeln")
    ap.add_argument("--status", default="/run/moveeye-controller/status.json")
    ap.add_argument("--fenster", default="", help="BxH (zum Prüfen)")
    a = ap.parse_args()
    if a.fenster and not all(x.isdigit() for x in a.fenster.split("x")):
        ap.error("--fenster BxH")
    if tk is None:
        print("controller_fenster: python3-tk fehlt", file=sys.stderr)
        return 3
    sperre = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", "moveeye-controller-fenster-%d.lock" % os.getuid())
    try:
        import fcntl
        lf = open(sperre, "a")
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)  # schon offen: nicht ein zweites Fenster
    except OSError:
        return 0
    try:
        Fenster(a).root.mainloop()
    except tk.TclError as e:
        print("controller_fenster:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
