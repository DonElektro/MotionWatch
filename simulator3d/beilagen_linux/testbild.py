#!/usr/bin/env python3
"""MoveEye Kiosk - Testbild: solange auf dem Simulator-PC ein Test läuft (Pause-Datei des Test-Runners), zeigt die
Kiosk-Sitzung statt eines dunklen Bildschirms dieses Bild im Vollbild, wie ein Dashboard: Logo, «Test läuft – bitte nicht
ausschalten», das Bild, das MoveEye gerade auswertet (mit MoveEyes Rahmen), «Soll / Ist» des laufenden Falls, Fortschritt
(Plan, Fall N/M, Start, Dauer, Rest) und die Bilanz bisher (Personen erkannt, Tiere / Autos ignoriert, Leerlauf ruhig,
Pushes). Nach dem Test bleibt 2 Min. eine Zusammenfassung stehen, dann startet kiosk_sitzung.sh den Simulator wieder.
Ab 3.55.0 (Dauerrechnen): oben steht, welche Arbeit läuft («Erkennung messen», «KI-Trainingsbilder», «Langzeittest»), andere
Arbeiten zeigen eigene Kacheln (Feld «kacheln»). Knopf «Spielen» unten rechts (Maus); jede Taste / Mausbewegung zeigt ihn
gross in der Mitte (Enter oder Klick = Spielen, Esc = weiter rechnen). Spielen schreibt die Spielen-Datei (wie hp_wache.py),
der Test-Runner hält an und gibt den Bildschirm frei – dann kommt keine Zusammenfassung, der Simulator startet gleich.
Daneben der Knopf «Controller koppeln» (oder Taste K): öffnet controller_fenster.py (Controller per Bluetooth koppeln,
Liste mit Akku, Trennen, Vergessen; der Dienst moveeye-controller-koppeln macht das als root, das Fenster legt nur leere
Wunsch-Dateien an).
Nach 10 Min. ohne Maus / Taste schläft das Bild (schwarz, nichts wird mehr gezeichnet; den Bildschirm schaltet DPMS aus,
kiosk_sitzung.sh); eine Taste oder die Maus weckt es sofort. «ende»: false im Fortschritt (z. B. HP-Diagnose) = keine
Zusammenfassung.

  python3 -I testbild.py --pause /run/moveeye-test/kiosk_pause --fortschritt /run/moveeye-test/fortschritt.json \
      --logo /usr/local/lib/moveeye-kiosk/moveeye.png [--fenster 1366x768] [--ende-s 120] \
      [--spiel-datei /run/moveeye-spiel/spielen] [--schlaf-s 600]

Die Fortschritt-Datei und bild.png / bild_klein.png daneben schreibt der Test (werkzeuge/erkennungstest/fortschritt.py,
Haken job_start.sh). Sie gelten nur als Daten: JSON bzw. PNG lesen (Grösse begrenzt, keine Verknüpfungen), nur bekannte
Felder, Texte gekürzt, nichts wird ausgeführt. Ist etwas älter als die Pause-Datei (voriger Lauf), fehlt es oder ist es
kaputt, bleibt der Teil leer (Logo, Text und Dauer gibt es immer). Wenig Rechenzeit: Daten und Bild alle 5 s, dazwischen
nur der pulsierende «LIVE»-Punkt und die Uhr.
"""
import argparse
import base64
import json
import os
import stat
import subprocess
import sys
import time

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:                                   # python3-tk fehlt: kiosk_sitzung.sh zeigt dann nur den dunklen Hintergrund
    sys.exit(3)

BG, PANEL, KACHEL, LINIE = "#0f1624", "#172134", "#1d2940", "#27324a"
FG, GRAU, ORANGE, GRUEN, ROT = "#e6ebf4", "#9a9ea3", "#f59a4a", "#3ecf8e", "#ef5b5b"
DATEN_S = 5
SPIEL_RUHE_S = 900                                    # wie hp_wache.py --ruhe-s: so lange gilt ein Spielen-Wunsch
ARBEITEN = {"Erkennung messen", "KI-Trainingsbilder", "Langzeittest"}
MAX_JSON, MAX_BILD = 65536, 4_000_000


# ------------------------------------------------------------------ Daten (nur lesen, alles prüfen)
def text(v, n):
    """nur Text, ohne Steuerzeichen, höchstens n Zeichen"""
    if not isinstance(v, str):
        return ""
    v = "".join(c for c in v if c.isprintable()).strip()
    return v if len(v) <= n else v[:n - 1].rstrip() + "…"


def zahl(v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v if lo <= v <= hi else None


def mtime(p):
    try:
        return os.stat(p).st_mtime
    except OSError:
        return None


def roh_lesen(p, seit, max_bytes, max_alter):
    """Datei sicher lesen: normale Datei (keine Verknüpfung), nicht zu gross, nicht älter als die Pause / max_alter"""
    try:
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > max_bytes:
            return None
        if (seit is not None and st.st_mtime < seit - 2) or time.time() - st.st_mtime > max_alter:
            return None
        return os.read(fd, max_bytes + 1)[:max_bytes]
    except OSError:
        return None
    finally:
        os.close(fd)


def paar(v):
    if isinstance(v, list) and len(v) == 2:
        a, b = zahl(v[0], 0, 100000), zahl(v[1], 0, 100000)
        if a is not None and b is not None and a <= b:
            return [int(a), int(b)]
    return None


def lesen(p, seit):
    """Fortschritt -> dict mit geprüften Feldern, oder {}"""
    roh = roh_lesen(p, seit, MAX_JSON, 6 * 3600) if p else None
    if not roh:
        return {}
    try:
        d = json.loads(roh.decode("utf-8", "replace"))
    except ValueError:
        return {}
    if not isinstance(d, dict):
        return {}
    jetzt = time.time()
    out = {"titel": text(d.get("titel"), 40), "plan": text(d.get("plan"), 24), "plan_text": text(d.get("plan_text"), 90),
           "arbeit": text(d.get("arbeit"), 30), "ende": d.get("ende") is not False, "fall_name": text(d.get("fall_name"), 14),
           "name": text(d.get("name"), 60), "fall": zahl(d.get("fall"), 0, 100000), "faelle": zahl(d.get("faelle"), 1, 100000),
           "start": zahl(d.get("start"), jetzt - 2 * 86400, jetzt + 120), "status": text(d.get("status"), 20),
           "soll": text(d.get("soll"), 20), "bild_t": zahl(d.get("bild_t"), jetzt - 86400, jetzt + 120)}
    if out["fall"] is not None and out["faelle"] is not None:
        out["faelle"] = max(out["faelle"], out["fall"])
    ist = d.get("ist") if isinstance(d.get("ist"), dict) else {}
    out["ist"] = {"art": text(ist.get("art"), 12), "text": text(ist.get("text"), 30)} if ist else {}
    b = d.get("bilanz") if isinstance(d.get("bilanz"), dict) else {}
    out["bilanz"] = {k: paar(b.get(k)) for k in ("personen", "ignoriert", "leer")}
    pu = zahl(b.get("pushes"), 0, 100000)
    out["bilanz"]["pushes"] = int(pu) if pu is not None else None
    le = d.get("letzter") if isinstance(d.get("letzter"), dict) else {}
    out["letzter"] = {"name": text(le.get("name"), 60), "text": text(le.get("text"), 60),
                      "ok": le.get("ok") if isinstance(le.get("ok"), bool) else None} if le else {}
    ka = []                                             # andere Arbeiten (KI-Bilder, Langzeittest): [Name, Wert, Farbe]
    for k in (d.get("kacheln") if isinstance(d.get("kacheln"), list) else [])[:4]:
        if isinstance(k, list) and len(k) >= 2:
            ka.append((text(k[0], 30), text(k[1], 20), text(k[2], 8) if len(k) > 2 else ""))
    out["kacheln"] = ka
    return out


def spiel_alter(p):
    """Alter der Spielen-Datei in s (normale Datei, keine Verknüpfung), None = fehlt"""
    if not p:
        return None
    try:
        st = os.lstat(p)
    except OSError:
        return None
    return max(0.0, time.time() - st.st_mtime) if stat.S_ISREG(st.st_mode) else None


def spielt(p):
    al = spiel_alter(p)
    return al is not None and al < SPIEL_RUHE_S


def spielen_schreiben(p, grund):
    """Spielen-Wunsch (wie hp_wache.spielen_schreiben): JSON {"grund", "seit"}, atomar, lesbar für den Test-Runner"""
    if not p:
        return False
    try:
        if spielt(p):
            os.utime(p, None)
            return True
        tmp = p + ".neu"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"grund": grund[:20], "seit": int(time.time())}, f)
        os.chmod(tmp, 0o644)
        os.replace(tmp, p)
        return True
    except OSError as e:
        print("testbild: Spielen-Datei:", e, file=sys.stderr)
        return False


def dauer(s, kurz=False):
    m = max(0, int(s // 60))
    if m < 1:
        return "< 1 Min."
    if m < 60:
        return "%d Min." % m
    return ("%d:%02d Std." if kurz else "%d Std. %d Min.") % (m // 60, m % 60)


# ------------------------------------------------------------------ Bild
class Testbild:
    def __init__(self, a):
        self.a = a
        self.root = tk.Tk(className="moveeye-testbild")
        self.root.title("MoveEye – Test läuft")
        self.root.configure(bg=BG, cursor="none")
        if a.fenster:
            w, h = (int(x) for x in a.fenster.split("x"))
            self.root.geometry("%dx%d+0+0" % (w, h))
        else:
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.attributes("-fullscreen", True)
        self.w, self.h = w, h
        self.c = tk.Canvas(self.root, width=w, height=h, bg=BG, highlightthickness=0, cursor="none")
        self.c.pack(fill="both", expand=True)
        fam = self._familie()
        F = lambda f, fett=False: tkfont.Font(family=fam, size=-max(10, int(h * f)), weight="bold" if fett else "normal")
        self.f = {"marke": F(0.040, True), "titel": F(0.050, True), "gross": F(0.058, True), "mittel": F(0.032, True),
                  "text": F(0.025), "klein": F(0.020), "klein_fett": F(0.020, True), "riesig": F(0.085, True)}
        self.logo_klein = self._logo(a.logo, int(h * 0.075))
        self.logo_gross = self._logo(a.logo, int(h * 0.20))
        self.bild = None
        self.bild_quelle = ("", 0.0)
        self.d = {}
        self.seit = None
        self.ende_ab = None                           # Zeitpunkt, ab dem die Zusammenfassung steht (Pause-Datei weg)
        self.modus = ""
        self.puls = 0
        self.n_tick = 0
        self.root.bind("<Escape>", lambda e: None)    # Kiosk: nichts schliesst das Bild ausser dem Ende des Tests
        self.eingabe_t = time.time()                  # letzte Maus / Taste (Schlaf nach --schlaf-s)
        self.schlaeft = False
        self.hinweis_bis = 0.0                        # bis wann der grosse Spielen-Knopf in der Mitte steht
        self.spiel_ab = None                          # Spielen gewünscht (hier oder über MoveEye / hp_wache)
        self.maus = None
        self.root.bind_all("<Key>", self._taste)
        self.root.bind_all("<Motion>", self._bewegung)
        self.root.bind_all("<Button>", self._klick)
        self.tick()

    # ---------------------------------------------- Eingaben: wecken, Spielen
    def _aufwachen(self):
        self.eingabe_t = time.time()
        if self.schlaeft:
            self.schlaeft = False
            self.modus = ""                           # beim nächsten Takt neu aufbauen
            self.n_tick = DATEN_S - 1
            return True
        return False

    def _taste(self, e):
        geweckt = self._aufwachen()
        if self.modus != "live" or self.spiel_ab is not None:
            return
        k = (e.keysym or "").lower()
        if k == "k" and not geweckt:
            self.koppeln()
            return
        if self.hinweis_bis > time.time() and not geweckt and k in ("return", "kp_enter", "space"):
            self.spielen("taste")
        elif k == "escape":
            self.hinweis_bis = 0.0
        else:
            self.hinweis_bis = time.time() + 20
        self.zeichne_spielknopf()

    def _bewegung(self, e):
        if self.maus is not None and abs(e.x_root - self.maus[0]) + abs(e.y_root - self.maus[1]) < 12:
            return                                    # kleines Zittern der Maus zählt nicht
        self.maus = (e.x_root, e.y_root)
        geweckt = self._aufwachen()
        if self.modus == "live" and self.spiel_ab is None and not geweckt:
            neu = self.hinweis_bis < time.time()
            self.hinweis_bis = time.time() + 20
            if neu:
                self.zeichne_spielknopf()

    def _klick(self, e):
        geweckt = self._aufwachen()
        if geweckt or self.modus != "live" or self.spiel_ab is not None:
            return
        x, y = e.x_root - self.root.winfo_rootx(), e.y_root - self.root.winfo_rooty()
        kb = getattr(self, "koppeln_box", None)
        if kb and kb[0] <= x <= kb[2] and kb[1] <= y <= kb[3] and self.hinweis_bis <= time.time():
            self.koppeln()
            return
        for box in (getattr(self, "knopf_box", None), getattr(self, "gross_box", None) if self.hinweis_bis > time.time() else None):
            if box and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                self.spielen("knopf")
                return
        self.hinweis_bis = time.time() + 20
        self.zeichne_spielknopf()

    def koppeln(self):
        """Fenster «Controller koppeln» (controller_fenster.py daneben) öffnen - es legt die Wunsch-Datei an"""
        if not self.a.spiel_datei:
            return
        prog = os.path.join(os.path.dirname(os.path.abspath(__file__)), "controller_fenster.py")
        if not os.path.isfile(prog):
            print("testbild: controller_fenster.py fehlt", file=sys.stderr)
            return
        try:
            subprocess.Popen([sys.executable, "-I", prog, "--wunsch",
                              os.path.join(os.path.dirname(self.a.spiel_datei), "controller_koppeln")],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except OSError as e:
            print("testbild: Controller koppeln:", e, file=sys.stderr)

    def spielen(self, grund):
        if spielen_schreiben(self.a.spiel_datei, grund):
            self.spiel_ab = time.time()
        self.hinweis_bis = 0.0
        self.zeichne_spielknopf()

    def gamepad(self, cx, cy, s, farbe, tag):
        """Symbol Spielkonsole (gezeichnet - Farb-Emoji kann Tk unter X11 nicht sicher zeigen)"""
        c = self.c
        w, h = s * 1.6, s * 0.9
        self.rund(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, s * 0.4, fill=farbe, outline="", tags=(tag,))
        k = s * 0.13
        x0 = cx - w * 0.27
        c.create_rectangle(x0 - k * 2.2, cy - k * 0.7, x0 + k * 2.2, cy + k * 0.7, fill=BG, outline="", tags=(tag,))
        c.create_rectangle(x0 - k * 0.7, cy - k * 2.2, x0 + k * 0.7, cy + k * 2.2, fill=BG, outline="", tags=(tag,))
        for dx, dy in ((0.2, -0.1), (0.32, 0.1)):
            x1, y1 = cx + w * dx, cy + h * dy
            c.create_oval(x1 - k, y1 - k, x1 + k, y1 + k, fill=BG, outline="", tags=(tag,))

    def zeichne_spielknopf(self):
        """unten rechts immer der Knopf «Spielen»; nach einer Eingabe gross in der Mitte; nach dem Wunsch: Hinweis"""
        c, w, h = self.c, self.w, self.h
        c.delete("spiel")
        self.knopf_box = self.gross_box = self.koppeln_box = None
        if self.modus != "live" or self.schlaeft or not self.a.spiel_datei:
            return
        m = int(h * 0.035)
        f = self.f["mittel"]
        if self.spiel_ab is None and spielt(self.a.spiel_datei):
            self.spiel_ab = time.time()                  # Wunsch kam von MoveEye / einem Handy (hp_wache.py)
        if self.spiel_ab is not None:
            lange = self.spiel_ab is not None and time.time() - self.spiel_ab > 90
            t1 = "Spielen – das Rechnen wird angehalten"
            t2 = ("Dieser Test kann nicht anhalten – der Simulator startet, sobald er fertig ist." if lange
                  else "Der Stand wird gesichert, der Simulator startet in wenigen Sekunden.")
            bw = max(f.measure(t1), self.f["text"].measure(t2)) + int(h * 0.12)
            bh = int(h * 0.20)
            x0, y0 = w // 2 - bw // 2, h // 2 - bh // 2
            self.rund(x0, y0, x0 + bw, y0 + bh, int(h * 0.02), fill=PANEL, outline=ORANGE, width=3, tags=("spiel",))
            self.gamepad(w // 2, y0 + int(bh * 0.28), int(h * 0.05), ORANGE, "spiel")
            c.create_text(w // 2, y0 + int(bh * 0.58), text=t1, fill=FG, font=f, anchor="center", tags=("spiel",))
            c.create_text(w // 2, y0 + int(bh * 0.82), text=t2, fill=GRAU, font=self.f["text"], anchor="center", tags=("spiel",))
            self.knopf_box = self.gross_box = None
            return
        # kleiner Knopf unten rechts
        t = "Spielen"
        bh = int(h * 0.055)
        bw = int(bh * 1.3) + self.f["klein_fett"].measure(t) + int(h * 0.03)
        x1, y1 = w - m, h - int(h * 0.012)
        x0, y0 = x1 - bw, y1 - bh
        self.rund(x0, y0, x1, y1, int(bh * 0.3), fill=KACHEL, outline=ORANGE, width=2, tags=("spiel",))
        self.gamepad(x0 + int(bh * 0.7), (y0 + y1) // 2, int(bh * 0.42), ORANGE, "spiel")
        c.create_text(x0 + int(bh * 1.3), (y0 + y1) // 2, text=t, fill=FG, font=self.f["klein_fett"], anchor="w", tags=("spiel",))
        self.knopf_box = (x0, y0, x1, y1)
        self.gross_box = None
        # links daneben: «Controller koppeln» (PS5-Controller per Bluetooth)
        t = "Controller koppeln"
        kx1 = x0 - int(h * 0.02)
        kx0 = kx1 - self.f["klein_fett"].measure(t) - int(bh * 1.3) - int(h * 0.03)
        self.rund(kx0, y0, kx1, y1, int(bh * 0.3), fill=KACHEL, outline=LINIE, width=2, tags=("spiel",))
        self.gamepad(kx0 + int(bh * 0.7), (y0 + y1) // 2, int(bh * 0.42), GRAU, "spiel")       # Symbol wie beim Knopf «Spielen»
        c.create_text(kx0 + int(bh * 1.3), (y0 + y1) // 2, text=t, fill=FG, font=self.f["klein_fett"], anchor="w", tags=("spiel",))
        self.koppeln_box = (kx0, y0, kx1, y1)
        if self.hinweis_bis <= time.time():
            return
        # gross in der Mitte (nach Taste / Maus)
        t1 = "Spielen?"
        t2 = "Das Rechnen hält an (der Stand wird gesichert), der Simulator startet."
        t3 = "Enter oder Klick: spielen  ·  Esc: weiter rechnen"
        bw = max(self.f["text"].measure(t2), self.f["klein"].measure(t3)) + int(h * 0.14)
        bh = int(h * 0.34)
        x0, y0 = w // 2 - bw // 2, h // 2 - bh // 2
        c.create_rectangle(0, 0, w, h, fill=BG, stipple="gray50", outline="", tags=("spiel",))
        self.rund(x0, y0, x0 + bw, y0 + bh, int(h * 0.025), fill=PANEL, outline=ORANGE, width=3, tags=("spiel",))
        self.gamepad(w // 2, y0 + int(bh * 0.25), int(h * 0.075), ORANGE, "spiel")
        c.create_text(w // 2, y0 + int(bh * 0.52), text=t1, fill=FG, font=self.f["titel"], anchor="center", tags=("spiel",))
        c.create_text(w // 2, y0 + int(bh * 0.71), text=t2, fill=FG, font=self.f["text"], anchor="center", tags=("spiel",))
        c.create_text(w // 2, y0 + int(bh * 0.87), text=t3, fill=GRAU, font=self.f["klein"], anchor="center", tags=("spiel",))
        self.gross_box = (x0, y0, x0 + bw, y0 + bh)

    def _familie(self):
        da = {f.lower(): f for f in tkfont.families(self.root)}
        for f in ("DejaVu Sans", "Noto Sans", "Liberation Sans", "Ubuntu", "FreeSans"):
            if f.lower() in da:
                return da[f.lower()]
        return "Helvetica"

    def _skalieren(self, img, ziel_b, ziel_h, nur_kleiner=True):
        """ganzzahliger Zoom / Unterabtastung, damit das Bild in ziel_b × ziel_h passt (Tk kann nur das)"""
        bw, bh = max(1, img.width()), max(1, img.height())
        best, wert = (1, 16), -1.0                   # passt nichts: so klein wie möglich
        for z in range(1, 4):
            for s in range(1, 17):
                f = z / s
                if (nur_kleiner and f > 1) or bw * f > ziel_b or bh * f > ziel_h:
                    continue
                if f > wert:
                    best, wert = (z, s), f
        z, s = best
        if z > 1:
            img = img.zoom(z)
        if s > 1:
            img = img.subsample(s)
        return img

    def _logo(self, p, ziel):
        try:
            img = tk.PhotoImage(master=self.root, file=p)
        except (tk.TclError, OSError):
            return None
        return self._skalieren(img, ziel, ziel, nur_kleiner=False)

    def passend(self, t, f, breite):
        """Text auf eine Zeile kürzen (mit «…»), damit nichts überlappt"""
        f = self.f[f]
        if f.measure(t) <= breite:
            return t
        while t and f.measure(t + "…") > breite:
            t = t[:-1]
        return t.rstrip(" ·") + "…"

    def rund(self, x0, y0, x1, y1, r, **kw):
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r,
               x0, y0 + r, x0, y0]
        return self.c.create_polygon(pts, smooth=True, **kw)

    def txt(self, x, y, t, f, farbe=FG, anker="nw", breite=None, tag="daten"):
        if breite:
            t = self.passend(t, f, breite)
        return self.c.create_text(x, y, text=t, fill=farbe, font=self.f[f], anchor=anker, tags=(tag,))

    # ---------------------------------------------- Daten holen
    def daten(self):
        neu = mtime(self.a.pause) if self.a.pause else time.time()
        if neu is not None:
            if self.seit is not None and abs(neu - self.seit) > 1 and self.ende_ab is not None:
                self.d, self.bild = {}, None           # neuer Test während der Zusammenfassung
            self.seit, self.ende_ab = neu, None
            d = lesen(self.a.fortschritt, self.seit)
            if d or self.seit is None:
                self.d = d
            self._bild_laden()
        elif self.ende_ab is None:
            self.ende_ab = time.time()                 # Test fertig: Zusammenfassung (Daten vom letzten Stand)
            if spielt(self.a.spiel_datei) or self.d.get("ende") is False or self.a.ende_s == 0:
                self.ende_ab = -1e9                    # gespielt wird / ohne Zusammenfassung (HP-Diagnose): gleich zu

    def _bild_laden(self):
        self.bild_ok = False
        if not self.a.fortschritt:
            return
        ordner = os.path.dirname(self.a.fortschritt)
        b, hh = self.bildbox
        for name in ("bild.png", "bild_klein.png"):
            p = os.path.join(ordner, name)
            m = mtime(p)
            if m is None or m < (self.seit or 0) - 2 or time.time() - m > 120:
                continue
            if self.bild is not None and self.bild_quelle == (p, m):
                self.bild_ok = True
                return
            roh = roh_lesen(p, self.seit, MAX_BILD, 120)
            if not roh or not roh.startswith(b"\x89PNG\r\n\x1a\n"):
                continue
            try:
                img = tk.PhotoImage(master=self.root, data=base64.b64encode(roh).decode("ascii"))
            except tk.TclError:
                continue
            if img.width() > b * 1.01 or img.height() > hh * 1.01:
                if name == "bild.png":
                    continue                           # das kleinere versuchen
                img = self._skalieren(img, b, hh)
            self.bild, self.bild_quelle, self.bild_ok = img, (p, m), True
            return

    # ---------------------------------------------- Takt
    def tick(self):
        self.n_tick += 1
        if not self.schlaeft and self.a.schlaf_s and time.time() - self.eingabe_t >= self.a.schlaf_s and self.spiel_ab is None:
            self.schlaeft = True                       # schlafen: schwarz, nichts mehr zeichnen (DPMS schaltet ab)
            self.c.delete("all")
            self.modus = "schlaf"
            self.c.configure(bg="#000000")
        if self.schlaeft:
            if self.n_tick % DATEN_S == 0:
                self.daten()                           # nur: ist der Test fertig? (dann zu, ohne Zusammenfassung zu zeichnen)
                if self.ende_ab is not None and time.time() - self.ende_ab >= self.a.ende_s:
                    self.root.destroy()
                    return
            self.root.after(1000, self.tick)
            return
        self.c.configure(bg=BG)
        if self.n_tick == 1 or self.n_tick % DATEN_S == 0:
            if not self.modus:
                self.aufbau_live()
            self.daten()
            if self.ende_ab is not None and time.time() - self.ende_ab >= self.a.ende_s:
                self.root.destroy()                    # kiosk_sitzung.sh startet den Simulator wieder
                return
            fertig = self.ende_ab is not None or self.d.get("status") in ("fertig", "fehler")
            if fertig and self.modus != "ende":
                self.aufbau_ende()
            elif not fertig and (self.modus != "live" or getattr(self, "kopf_arbeit", "") != self.arbeit_name()):
                self.aufbau_live()                     # (auch wenn die Arbeit wechselt: Kopfzeile neu)
            (self.zeichne_ende if self.modus == "ende" else self.zeichne_live)()
            self.zeichne_spielknopf()
        elif self.modus == "live" and self.hinweis_bis and self.hinweis_bis <= time.time():
            self.hinweis_bis = 0.0
            self.zeichne_spielknopf()
        self.animieren()
        self.root.after(1000, self.tick)

    def animieren(self):
        self.puls = (self.puls + 1) % 2
        jetzt = time.localtime()
        self.c.itemconfigure("uhr", text=time.strftime("%H:%M", jetzt))
        if self.modus == "live":
            self.c.itemconfigure("puls", fill=ORANGE if self.puls else "#7a4d25")
            self.c.itemconfigure("puls_ring", outline=ORANGE if self.puls else BG)
        elif self.modus == "ende" and self.ende_ab is not None:
            rest = max(0, int(self.a.ende_s - (time.time() - self.ende_ab)))
            self.c.itemconfigure("countdown", text="Der Simulator startet in %d:%02d wieder." % (rest // 60, rest % 60))

    def arbeit_name(self):
        return self.d.get("arbeit") if self.d.get("arbeit") in ARBEITEN else "Erkennungstest" if self.d.get("plan") else "Test"

    # ---------------------------------------------- Kopf (beide Ansichten)
    def kopf(self, rechts_text, rechts_farbe, puls):
        c, w, h = self.c, self.w, self.h
        m = int(h * 0.035)
        y = m
        x = m
        if self.logo_klein is not None:
            c.create_image(x, y, image=self.logo_klein, anchor="nw")
            x += self.logo_klein.width() + int(h * 0.018)
        lh = self.logo_klein.height() if self.logo_klein is not None else int(h * 0.075)
        wm = self.f["marke"].measure("Move")
        ym = y + lh // 2
        c.create_text(x, ym, text="Move", fill=FG, font=self.f["marke"], anchor="w")
        c.create_text(x + wm, ym, text="Eye", fill=ORANGE, font=self.f["marke"], anchor="w")
        x += wm + self.f["marke"].measure("Eye") + int(h * 0.02)
        arbeit = self.arbeit_name()
        self.kopf_arbeit = arbeit
        c.create_text(x, ym, text="Simulator-PC · " + arbeit, fill=GRAU, font=self.f["text"], anchor="w")
        # rechts: Uhr, Zustand mit pulsierendem Punkt
        xr = w - m
        c.create_text(xr, ym, text="", fill=GRAU, font=self.f["mittel"], anchor="e", tags=("uhr",))
        xr -= self.f["mittel"].measure("00:00") + int(h * 0.035)
        c.create_text(xr, ym, text=rechts_text, fill=rechts_farbe, font=self.f["klein_fett"], anchor="e")
        xr -= self.f["klein_fett"].measure(rechts_text) + int(h * 0.016)
        r = int(h * 0.009)
        if puls:
            c.create_oval(xr - 2 * r - 4, ym - r - 4, xr + 4, ym + r + 4, outline=ORANGE, width=1, tags=("puls_ring",))
            c.create_oval(xr - 2 * r, ym - r, xr, ym + r, fill=ORANGE, outline="", tags=("puls",))
        else:
            c.create_oval(xr - 2 * r, ym - r, xr, ym + r, fill=rechts_farbe, outline="")
        return y + lh + int(h * 0.03)

    # ---------------------------------------------- Ansicht «läuft»
    def aufbau_live(self):
        c, w, h = self.c, self.w, self.h
        c.delete("all")
        self.modus = "live"
        m = int(h * 0.035)
        y = self.kopf("LIVE", ORANGE, True)
        c.create_text(m, y, text="Test läuft – bitte nicht ausschalten", fill=FG, font=self.f["titel"], anchor="nw")
        y += self.f["titel"].metrics("linespace") + int(h * 0.006)
        c.create_rectangle(m, y, m + int(h * 0.12), y + max(3, int(h * 0.005)), fill=ORANGE, outline="")
        y += int(h * 0.03)
        unten = h - int(h * 0.06)
        # links: Live-Bild
        lb = int(w * 0.58) - m
        p = int(h * 0.022)
        self.rund(m, y, m + lb, unten, int(h * 0.018), fill=PANEL, outline=LINIE, width=2)
        sim_bild = self.d.get("arbeit") == "KI-Trainingsbilder"          # Bild des Simulators, nicht von MoveEye
        c.create_text(m + p, y + p, text="LIVE-BILD · SIMULATOR" if sim_bild else "LIVE-BILD · SO SIEHT ES MOVEEYE", fill=GRAU,
                      font=self.f["klein_fett"], anchor="nw")
        iy = y + p + self.f["klein_fett"].metrics("linespace") + int(h * 0.012)
        zeile = self.f["mittel"].metrics("linespace") + int(h * 0.03)
        bh = unten - p - zeile - iy
        bb = lb - 2 * p
        bh = min(bh, int(bb * 9 / 16))
        self.bildbox = (bb, bh)
        self.bild_ort = (m + lb // 2, iy, bb, bh)
        self.soll_ort = (m + p, iy + bh + int(h * 0.02), bb)
        # rechts: Fortschritt und Bilanz
        rx0, rx1 = m + lb + m, w - m
        self.r = (rx0, rx1)
        ph = int((unten - y) * 0.42)
        self.rund(rx0, y, rx1, y + ph, int(h * 0.018), fill=PANEL, outline=LINIE, width=2)
        self.fort_ort = (rx0 + p, y + p, rx1 - p, y + ph - p)
        y2 = y + ph + int(h * 0.022)
        self.rund(rx0, y2, rx1, unten, int(h * 0.018), fill=PANEL, outline=LINIE, width=2)
        self.bilanz_ort = (rx0 + p, y2 + p, rx1 - p, unten - p)
        c.create_text(m, h - int(h * 0.03), text="Spielen: Taste, Klick oder Controller  ·  K: Controller koppeln" if self.a.spiel_datei else "Der Simulator startet nach dem Test von selbst wieder.",
                      fill=GRAU, font=self.f["klein"], anchor="w")

    def zeichne_live(self):
        c, h, d = self.c, self.h, self.d
        c.delete("daten")
        jetzt = time.time()
        # Bild oder Platzhalter
        mx, iy, bb, bh = self.bild_ort
        if self.bild is not None and getattr(self, "bild_ok", False):
            c.create_image(mx, iy, image=self.bild, anchor="n", tags=("daten",))
            bw, bhh = self.bild.width(), self.bild.height()
            c.create_rectangle(mx - bw // 2 - 1, iy - 1, mx + bw // 2 + 1, iy + bhh + 1, outline=LINIE, tags=("daten",))
        else:
            c.create_rectangle(mx - bb // 2, iy, mx + bb // 2, iy + bh, fill=KACHEL, outline="", tags=("daten",))
            if self.logo_gross is not None:
                c.create_image(mx, iy + bh // 2 - int(h * 0.03), image=self.logo_gross, anchor="center", tags=("daten",))
            self.txt(mx, iy + bh // 2 + int(h * 0.10), "Noch kein Bild – es kommt mit dem ersten Fall" if d.get("plan") or d.get("arbeit")
                     else "Für diesen Test gibt es kein Live-Bild", "text", GRAU, "n")
        # Soll / Ist (gleich unter dem Bild)
        sx, sy, sb = self.soll_ort
        if self.bild is not None and getattr(self, "bild_ok", False):
            sy = iy + self.bild.height() + int(h * 0.025)
        soll, ist = d.get("soll"), d.get("ist") or {}
        if soll and ist.get("text"):
            person_soll, person_ist = soll == "Person", ist.get("art") == "person"
            if person_soll:
                farbe, zeichen = (GRUEN, " ✓") if person_ist else (ORANGE, " · sucht …")
            else:
                farbe, zeichen = (ROT, " ✗ Fehlalarm?") if person_ist else (GRUEN, " ✓")
            x = sx
            for teil, f, fb in (("Soll: ", "mittel", GRAU), (soll, "mittel", FG), ("   Ist: ", "mittel", GRAU),
                                (ist["text"] + zeichen, "mittel", farbe)):
                t = self.passend(teil, f, sb - (x - sx))
                self.txt(x, sy, t, f, fb)
                x += self.f[f].measure(t)
        elif soll:
            self.txt(sx, sy, "Soll: " + soll, "mittel", GRAU, breite=sb)
        if self.bild is not None and getattr(self, "bild_ok", False) and d.get("arbeit") != "KI-Trainingsbilder":   # Legende: MoveEyes Farben
            ly = sy + self.f["mittel"].metrics("linespace") + int(h * 0.016)
            x, q = sx, int(h * 0.016)
            for farbe, name in (("#ff2020", "Person (MoveEye)"), ("#50c878", "KI-Objekt mit Sicherheit"),
                                ("#ffffff", "Bewegung / Tier / Fahrzeug")):
                if x + q + self.f["klein"].measure(name) > sx + sb:
                    break
                c.create_rectangle(x, ly + 3, x + q, ly + 3 + q, outline=farbe, width=2, tags=("daten",))
                t = self.txt(x + q + int(h * 0.008), ly, name, "klein", GRAU)
                x = c.bbox(t)[2] + int(h * 0.03)
        # Fortschritt
        x0, y0, x1, y1 = self.fort_ort
        b = x1 - x0
        y = y0
        if d.get("plan"):
            plan = "PLAN " + d["plan"].upper() + ("  ·  " + d["plan_text"] if d.get("plan_text") else "")
        elif d.get("plan_text"):
            plan = d["plan_text"].upper()
        else:
            plan = (d.get("titel") or "Test auf diesem PC").upper()
        if d.get("arbeit") in ARBEITEN:
            plan = d["arbeit"].upper() + "  ·  " + plan
        self.txt(x0, y, plan, "klein_fett", GRAU, breite=b)
        y += self.f["klein_fett"].metrics("linespace") + int(h * 0.01)
        n, mm = d.get("fall"), d.get("faelle")
        start = d.get("start") or self.seit or jetzt
        anteil = None
        if n and mm:
            t1 = self.txt(x0, y, "%s %d" % (d.get("fall_name") or "Fall", n), "gross", ORANGE)
            xx = c.bbox(t1)[2] + int(h * 0.012)
            self.txt(xx, y + self.f["gross"].metrics("ascent") - self.f["mittel"].metrics("ascent"), "/ %d" % mm, "mittel", GRAU)
            anteil = max(0.0, min(1.0, (n - 1) / float(mm)))
            self.txt(x1, y + self.f["gross"].metrics("ascent") - self.f["mittel"].metrics("ascent"), "%d %%" % round(anteil * 100),
                     "mittel", FG, "ne")
        else:
            self.txt(x0, y, "Vorbereitung …" if d.get("plan") or d.get("arbeit") else "läuft", "gross", ORANGE)
        y += self.f["gross"].metrics("linespace")
        self.txt(x0, y, d.get("name") or "", "text", FG, breite=b)
        y += self.f["text"].metrics("linespace") + int(h * 0.016)
        bar = max(8, int(h * 0.014))
        c.create_rectangle(x0, y, x1, y + bar, fill=LINIE, outline="", tags=("daten",))
        if anteil:
            c.create_rectangle(x0, y, x0 + int(b * anteil), y + bar, fill=ORANGE, outline="", tags=("daten",))
        y += bar + int(h * 0.016)
        zeit = "Start %s · seit %s" % (time.strftime("%H:%M", time.localtime(start)), dauer(jetzt - start, True))
        if anteil and anteil > 0.02 and n and n > 2:
            zeit += " · Rest ~%s" % dauer((jetzt - start) / (n - 1) * (mm - n + 1), True)
        self.txt(x0, y, zeit, "text", GRAU, breite=b)
        # Bilanz
        self.bilanz(*self.bilanz_ort, d, "BILANZ BISHER")

    def bilanz(self, x0, y0, x1, y1, d, titel, gross=False):
        c, h = self.c, self.h
        bi = d.get("bilanz") or {}
        self.txt(x0, y0, titel, "klein_fett", GRAU)
        y = y0 + self.f["klein_fett"].metrics("linespace") + int(h * 0.012)
        le = d.get("letzter") or {}
        unten = y1
        if le.get("name") and not gross:
            unten = y1 - self.f["text"].metrics("linespace") * 2 - int(h * 0.006)
        g = int(h * 0.016)
        kw, kh = (x1 - x0 - g) // 2, (unten - y - g) // 2
        kacheln = [("Personen erkannt", bi.get("personen")), ("Tiere / Autos ignoriert", bi.get("ignoriert")),
                   ("Leerlauf ruhig", bi.get("leer")), ("Pushes", bi.get("pushes"))]
        if d.get("kacheln"):                           # andere Arbeit: ihre eigenen Kacheln (Text, schon fertig)
            kacheln = [(n, ("text", v, f)) for n, v, f in d["kacheln"]] + [("", None)] * (4 - len(d["kacheln"]))
        for i, (name, wert) in enumerate(kacheln):
            if not name:
                continue
            kx, ky = x0 + (i % 2) * (kw + g), y + (i // 2) * (kh + g)
            self.rund(kx, ky, kx + kw, ky + kh, int(h * 0.012), fill=KACHEL, outline="", tags=("daten",))
            p = int(h * 0.016)
            self.txt(kx + p, ky + p, name, "klein", GRAU, breite=kw - 2 * p)
            if isinstance(wert, tuple):
                farbe = {"gruen": GRUEN, "orange": ORANGE, "rot": ROT}.get(wert[2], FG)
                s, zus = wert[1] or "–", ""
            elif isinstance(wert, list):
                a, b = wert
                farbe = GRAU if b == 0 else (GRUEN if a == b else (ORANGE if a >= 0.8 * b else ROT))
                s, zus = ("%d" % a, " / %d" % b) if b else ("–", "")
            elif isinstance(wert, int):
                farbe, s, zus = FG, "%d" % wert, ""
            else:
                farbe, s, zus = GRAU, "–", ""
            f = "riesig" if gross else "gross"
            if isinstance(wert, tuple) and self.f[f].measure(s) > kw - 2 * p:
                f = "mittel"
            vy = ky + kh - p
            if gross and isinstance(wert, list) and wert[1]:      # Zusammenfassung: Anteil gross rechts und als Balken
                a, b = wert
                self.txt(kx + kw - p, ky + p, "%d %%" % round(100.0 * a / b), "titel", farbe, "ne")
                bar = max(6, int(h * 0.01))
                c.create_rectangle(kx + p, vy - bar, kx + kw - p, vy, fill=LINIE, outline="", tags=("daten",))
                c.create_rectangle(kx + p, vy - bar, kx + p + int((kw - 2 * p) * a / b), vy, fill=farbe, outline="", tags=("daten",))
                vy -= bar + int(h * 0.015)
            t = self.txt(kx + p, vy, s, f, farbe, "sw")
            if zus:
                self.txt(c.bbox(t)[2] + int(h * 0.006), vy - int(h * 0.006), zus, "mittel", GRAU, "sw")
        if le.get("name") and not gross:
            ok = le.get("ok")
            farbe = GRUEN if ok else (ROT if ok is False else GRAU)
            yy = unten + int(h * 0.01)
            self.txt(x0, yy, "Letzter Fall: " + le["name"], "klein", GRAU, breite=x1 - x0)
            self.txt(x0, yy + self.f["klein"].metrics("linespace"), (le.get("text") or "") + (" ✓" if ok else (" ✗" if ok is False else "")),
                     "text", farbe, breite=x1 - x0)

    # ---------------------------------------------- Ansicht «fertig»
    def aufbau_ende(self):
        c, w, h = self.c, self.w, self.h
        c.delete("all")
        self.modus = "ende"
        y = self.kopf("FERTIG", GRUEN, False)
        m = int(h * 0.035)
        fehler = self.d.get("status") == "fehler"
        c.create_text(w // 2, y + int(h * 0.02), text="Test mit Fehler beendet" if fehler else "Test fertig", fill=ROT if fehler else GRUEN,
                      font=self.f["titel"], anchor="n")
        self.ende_y = y + int(h * 0.02) + self.f["titel"].metrics("linespace") + int(h * 0.01)
        kb = min(w - 2 * m, int(h * 1.5))
        self.ende_box = (w // 2 - kb // 2, w // 2 + kb // 2)
        c.create_text(w // 2, h - int(h * 0.075), text="", fill=FG, font=self.f["mittel"], anchor="center", tags=("countdown",))
        c.create_text(w // 2, h - int(h * 0.03), text="Ergebnisse: GitHub → Actions → " + (
                      "Dauerrechnen (HP)" if self.d.get("arbeit") in ARBEITEN else "Erkennung (HP)") + " → Artefakt", fill=GRAU,
                      font=self.f["klein"], anchor="center")

    def zeichne_ende(self):
        c, w, h, d = self.c, self.w, self.h, self.d
        c.delete("daten")
        x0, x1 = self.ende_box
        y = self.ende_y
        start = d.get("start") or self.seit or time.time()
        bis = self.ende_ab or time.time()
        n, mm = d.get("fall"), d.get("faelle")
        zeile = ("Plan %s" % d["plan"]) if d.get("plan") else (d.get("titel") or "Test")
        zeile += " · %s" % dauer(bis - start)
        if n and mm:
            zeile += " · %d von %d Fällen" % (n, mm)
        self.txt(w // 2, y, zeile, "text", GRAU, "n", breite=x1 - x0)
        y += self.f["text"].metrics("linespace") + int(h * 0.03)
        if self.ende_ab is None:
            c.itemconfigure("countdown", text="Ergebnisse werden gespeichert …")
        unten = h - int(h * 0.13)
        if d.get("kacheln") or any(v is not None for v in (d.get("bilanz") or {}).values()):
            self.bilanz(x0, y, x1, unten, d, "ERGEBNIS", gross=True)
        elif self.logo_gross is not None:
            c.create_image(w // 2, (y + unten) // 2, image=self.logo_gross, anchor="center", tags=("daten",))


def main():
    ap = argparse.ArgumentParser(description="MoveEye Kiosk: Testbild während eines Tests")
    ap.add_argument("--pause", default="", help="Pause-Datei des Test-Runners (danach Zusammenfassung, dann Ende)")
    ap.add_argument("--fortschritt", default="", help="Fortschritt als JSON (nur Daten), daneben bild.png")
    ap.add_argument("--logo", default="", help="Logo (PNG)")
    ap.add_argument("--ende-s", type=int, default=120, help="so lange bleibt die Zusammenfassung nach dem Test (s)")
    ap.add_argument("--fenster", default="", help="BxH statt Vollbild (zum Prüfen)")
    ap.add_argument("--spiel-datei", default="", help="Spielen-Wunsch (JSON, wie hp_wache.py); leer = ohne Knopf «Spielen»")
    ap.add_argument("--schlaf-s", type=int, default=600, help="nach so vielen s ohne Maus / Taste schläft das Bild (0 = nie)")
    a = ap.parse_args()
    if a.fenster and not all(x.isdigit() for x in a.fenster.split("x")):
        ap.error("--fenster BxH, z. B. 1366x768")
    a.ende_s = max(0, min(600, a.ende_s))
    a.schlaf_s = max(0, min(86400, a.schlaf_s))
    try:
        Testbild(a).root.mainloop()
    except tk.TclError as e:                          # kein Display
        print("testbild:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
