#!/usr/bin/env python3
"""MoveEye Kiosk - Fenster «Controller koppeln» (ohne Tippen): Controller per Bluetooth koppeln, Liste der gekoppelten
Controller mit Akku, «Trennen» und «Vergessen». Bedienbar mit Maus / Finger, Tastatur (Pfeile, Enter, Esc) und - sobald
einer da ist - mit dem Controller selbst (Steuerkreuz oder linker Stick, untere Taste ✕ / A = wählen, rechte ○ / B = zurück).
Das Fenster hat selbst keine Rechte: es legt nur leere Wunsch-Dateien an (der Dienst moveeye-controller-koppeln erledigt sie
als root, controller_koppeln.sh) und zeigt, was der Dienst als Daten meldet (status.json, liste.json).
Gestartet vom Knopf «Controller koppeln» im Testbild (testbild.py), vom Knopf in der Ecke des Kiosks (--ecke, erscheint
nur, solange kein Controller angeschlossen ist) und mit Ctrl+Alt+B (kiosk_sitzung.sh koppeln).

  python3 -I controller_fenster.py [--start auto|koppeln|liste] [--wunsch /run/moveeye-spiel/controller_koppeln]
                                   [--status /run/moveeye-controller/status.json] [--fenster 900x560]
  python3 -I controller_fenster.py --ecke unten-rechts [--pause /run/moveeye-test/kiosk_pause]

--start auto (Standard): ist schon ein Controller verbunden, zuerst die Liste; sonst beginnt gleich die Suche (60 s).
Nur Daten: Wunsch-Dateien sind leer (es zählt der Name), Status und Liste werden geprüft gelesen (Grösse, keine
Verknüpfung, nur bekannte Felder und Werte, Texte gekürzt). Solange das Fenster offen ist, schreibt es die Marke
«fenster_offen» neben die Wunsch-Dateien: hp_wache.py zählt Tasten am Controller dann nicht als Spielen (das Bedienen
dieses Fensters ist kein Spielen).
"""
import argparse
import glob
import json
import os
import re
import stat
import struct
import subprocess
import sys
import time

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:                                   # python3-tk fehlt: main() endet mit Code 3 (die Daten-Teile gehen)
    tk = tkfont = None

BG, PANEL, KACHEL, FG, GRAU, LINIE = "#0f1624", "#172134", "#1f2c44", "#e6ebf4", "#9a9ea3", "#3a4763"
ORANGE, GRUEN, ROT = "#f59a4a", "#3ecf8e", "#ef5b5b"
LAEUFT = ("start", "suche", "koppeln")
SCHRITTE = LAEUFT + ("fertig", "kein_adapter", "nicht_gefunden", "abgebrochen", "fehler")
ARTEN = ("DualSense", "DualSense Edge", "DualShock 4", "Xbox-Controller")
ID_RE = re.compile(r"^[0-9a-f]{10}$")
OHNE_DIENST_S = 15           # so lange ohne Antwort des Dienstes: Koppeln ist (noch) nicht eingerichtet
LISTE_S = 5                  # so oft die Liste neu holen, solange das Fenster offen ist
MAX_ZEILEN = 4
HALTEN = "PS-Taste und Create-Taste gedrückt halten, bis die Leiste schnell blau blinkt"
KEIN_ADAPTER = "Kein Bluetooth-Adapter gefunden – USB-Bluetooth-Stick einstecken oder Controller per USB-C-Kabel anschliessen"
ECKEN = ("unten-rechts", "unten-links", "oben-rechts", "oben-links")


# ------------------------------------------------------------------ Daten (geprüft lesen, leere Wünsche schreiben)
def _json_lesen(p, max_bytes=4096):
    """normale Datei (keine Verknüpfung), höchstens max_bytes, gültiges JSON-Objekt -> dict oder None"""
    try:
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > max_bytes:
            return None
        d = json.loads(os.read(fd, max_bytes + 1).decode("utf-8", "replace"))
    except (OSError, ValueError):
        return None
    finally:
        os.close(fd)
    return d if isinstance(d, dict) else None


def _zahl(x):
    return x if isinstance(x, int) and not isinstance(x, bool) else 0


def status_lesen(p):
    """Status des Dienstes -> dict mit geprüften Feldern oder {}"""
    d = _json_lesen(p)
    if d is None or d.get("schritt") not in SCHRITTE:
        return {}
    text = d.get("text") if isinstance(d.get("text"), str) else ""
    text = "".join(c for c in text if c.isprintable())[:160]
    ok = d.get("ok") if isinstance(d.get("ok"), bool) else None
    return {"schritt": d["schritt"], "t": _zahl(d.get("t")), "rest_s": max(0, min(600, _zahl(d.get("rest_s")))),
            "text": text, "ok": ok}


def liste_lesen(p):
    """Liste der gekoppelten Controller -> {"t", "adapter", "liste": [{"id", "art", "verbunden", "akku"}]} oder {}.
    Nur bekannte Arten und Kürzel aus 10 Hex-Zeichen; alles andere fällt weg."""
    d = _json_lesen(p, 8192)
    if d is None or not isinstance(d.get("liste"), list):
        return {}
    aus = []
    for e in d["liste"][:8]:
        if not isinstance(e, dict) or e.get("art") not in ARTEN or not isinstance(e.get("id"), str) or not ID_RE.match(e["id"]):
            continue
        a = e.get("akku")
        a = a if isinstance(a, int) and not isinstance(a, bool) and 0 <= a <= 100 else None
        if any(x["id"] == e["id"] for x in aus):
            continue
        aus.append({"id": e["id"], "art": e["art"], "verbunden": e.get("verbunden") is True, "akku": a})
    return {"t": _zahl(d.get("t")), "adapter": d.get("adapter") is True, "liste": aus}


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


def wunsch(ordner, was, kuerzel=None):
    """Wunsch an den Dienst: koppeln, abbrechen, liste, trennen / vergessen (mit Kürzel aus der Liste)"""
    if was in ("koppeln", "abbrechen", "liste") and kuerzel is None:
        name = "controller_" + was
    elif was in ("trennen", "vergessen") and isinstance(kuerzel, str) and ID_RE.match(kuerzel):
        name = "controller_%s.%s" % (was, kuerzel)
    else:
        return False
    return wunsch_schreiben(os.path.join(ordner, name))


def marke_setzen(p, an=True):
    """Marke «Fenster offen» für hp_wache.py (Änderungsdatum = jetzt) bzw. wegnehmen"""
    try:
        if an:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o644)
            os.close(fd)
            os.utime(p, None)
        else:
            os.unlink(p)
    except OSError:
        pass


def pads_da(quelle="/dev/input"):
    """Zahl der Controller, die Linux gerade kennt (Kabel oder Bluetooth): Joystick-Geräte js*"""
    return len(glob.glob(os.path.join(quelle, "js[0-9]*")))


# ------------------------------------------------------------------ Bedienung (ohne Tk: Knöpfe, Fokus, Auswahl)
class Bedienung:
    """Welche Knöpfe es gerade gibt, wo der Fokus steht und was eine Auswahl auslöst. «Vergessen» braucht zwei Mal
    Drücken innert FRAGE_S (kein Versehen mit dem Controller)."""
    FRAGE_S = 6.0

    def __init__(self):
        self.fokus = ("koppeln",)
        self.frage = None
        self.frage_t = 0.0

    def knoepfe(self, liste, laeuft):
        k = []
        for e in liste[:MAX_ZEILEN]:
            if e["verbunden"]:
                k.append(("trennen", e["id"]))
            k.append(("vergessen", e["id"]))
        k.append(("abbrechen",) if laeuft else ("koppeln",))
        k.append(("zu",))
        if self.fokus not in k:                        # Knopf weg (Liste geändert, Suche begonnen / beendet): Hauptknopf
            self.fokus = k[-2]
        return k

    def text(self, key, jetzt, zahl=0):
        if key[0] == "trennen":
            return "Trennen"
        if key[0] == "vergessen":
            return "Wirklich vergessen?" if self.frage == key and jetzt - self.frage_t < self.FRAGE_S else "Vergessen"
        if key[0] == "abbrechen":
            return "Suche abbrechen"
        if key[0] == "koppeln":
            return "Weiteren Controller koppeln" if zahl else "Controller koppeln"
        return "Schliessen"

    def bewegen(self, k, d):
        i = k.index(self.fokus) if self.fokus in k else len(k) - 2
        self.fokus = k[(i + d) % len(k)]

    def waehlen(self, key, jetzt):
        """-> ("wunsch", was, kürzel) | ("zu",) | None (nichts oder erst die Rückfrage)"""
        self.fokus = key
        if key[0] == "vergessen":
            if self.frage == key and jetzt - self.frage_t < self.FRAGE_S:
                self.frage = None
                return ("wunsch", "vergessen", key[1])
            self.frage, self.frage_t = key, jetzt
            return None
        self.frage = None
        if key[0] == "trennen":
            return ("wunsch", "trennen", key[1])
        if key[0] in ("koppeln", "abbrechen"):
            return ("wunsch", key[0], None)
        return ("zu",)


class PadLeser:
    """Controller als Bedienung des Fensters: /dev/input/js* (Steuerkreuz, linker Stick, Taste 0 = wählen, Taste 1 = zurück)"""
    JS = struct.Struct("IhBB")
    WAAGRECHT, SENKRECHT = (0, 6), (1, 7)

    def __init__(self, quelle="/dev/input"):
        self.quelle = quelle
        self.fds = {}                                  # Pfad -> fd
        self.rest = {}
        self.lage = {}                                 # (fd, Achse) -> -1 / 0 / 1
        self.t_scan = 0.0

    def scan(self, jetzt):
        if jetzt - self.t_scan < 2.0:
            return
        self.t_scan = jetzt
        da = set(glob.glob(os.path.join(self.quelle, "js[0-9]*")))
        for p in da - set(self.fds):
            try:
                fd = os.open(p, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
            except OSError:
                continue
            self.fds[p], self.rest[fd] = fd, b""
        for p in set(self.fds) - da:
            self._zu(p)

    def _zu(self, p):
        fd = self.fds.pop(p, None)
        if fd is None:
            return
        self.rest.pop(fd, None)
        for k in [k for k in self.lage if k[0] == fd]:
            del self.lage[k]
        try:
            os.close(fd)
        except OSError:
            pass

    def lesen(self, jetzt=None):
        """-> Liste von «auf», «ab», «ok», «zurueck»"""
        self.scan(time.time() if jetzt is None else jetzt)
        aus = []
        for p, fd in list(self.fds.items()):
            try:
                roh = os.read(fd, 4096)
            except BlockingIOError:
                continue
            except OSError:
                roh = b""
            if not roh:
                self._zu(p)
                continue
            daten = self.rest[fd] + roh
            n = len(daten) // self.JS.size
            self.rest[fd] = daten[n * self.JS.size:]
            for i in range(n):
                _, wert, typ, nr = self.JS.unpack_from(daten, i * self.JS.size)
                if typ & 0x80:                         # Startwerte beim Öffnen
                    continue
                if typ == 1 and wert == 1 and nr in (0, 1):
                    aus.append("ok" if nr == 0 else "zurueck")
                elif typ == 2 and nr in self.WAAGRECHT + self.SENKRECHT:
                    alt = self.lage.get((fd, nr), 0)
                    neu = (1 if wert > 0 else -1) if abs(wert) > 20000 else (0 if abs(wert) < 8000 else alt)
                    self.lage[(fd, nr)] = neu
                    if neu != 0 and neu != alt:
                        aus.append("ab" if neu > 0 else "auf")
        return aus


def gamepad_zeichnen(c, cx, cy, s, farbe, loch):
    """Symbol Spielkonsole (gezeichnet - Farb-Emoji kann Tk unter X11 nicht sicher zeigen)"""
    w, h = s * 1.6, s * 0.9
    c.create_oval(cx - w / 2, cy - h / 2, cx - w / 2 + h, cy + h / 2, fill=farbe, outline="")
    c.create_oval(cx + w / 2 - h, cy - h / 2, cx + w / 2, cy + h / 2, fill=farbe, outline="")
    c.create_rectangle(cx - w / 2 + h / 2, cy - h / 2, cx + w / 2 - h / 2, cy + h / 2, fill=farbe, outline="")
    k = s * 0.13
    x0 = cx - w * 0.27
    c.create_rectangle(x0 - k * 2.2, cy - k * 0.7, x0 + k * 2.2, cy + k * 0.7, fill=loch, outline="")
    c.create_rectangle(x0 - k * 0.7, cy - k * 2.2, x0 + k * 0.7, cy + k * 2.2, fill=loch, outline="")
    for dx, dy in ((0.2, -0.1), (0.32, 0.1)):
        x1, y1 = cx + w * dx, cy + h * dy
        c.create_oval(x1 - k, y1 - k, x1 + k, y1 + k, fill=loch, outline="")


# ------------------------------------------------------------------ Fenster
class Fenster:
    def __init__(self, a):
        self.a = a
        self.ordner = os.path.dirname(a.wunsch)
        self.liste_datei = os.path.join(os.path.dirname(a.status), "liste.json")
        self.marke = os.path.join(self.ordner, "fenster_offen")
        self.t0 = time.time()
        self.t_bedient = self.t0
        self.root = tk.Tk(className="moveeye-controller")
        self.root.title("MoveEye – Controller koppeln")
        self.root.configure(bg=BG)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        if a.fenster:
            w, h = (int(x) for x in a.fenster.split("x"))
        else:
            w, h = min(sw - 40, max(760, int(sh * 1.2))), min(sh - 40, max(420, int(sh * 0.72)))
        self.root.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 2))
        self.root.attributes("-topmost", True)
        self.w, self.h = w, h
        self.c = tk.Canvas(self.root, width=w, height=h, bg=PANEL, highlightthickness=3, highlightbackground=ORANGE)
        self.c.pack(fill="both", expand=True)
        fam = "DejaVu Sans" if "DejaVu Sans" in tkfont.families(self.root) else "Helvetica"
        self.f_titel = tkfont.Font(family=fam, size=-max(14, int(h * 0.062)), weight="bold")
        self.f_gross = tkfont.Font(family=fam, size=-max(13, int(h * 0.054)), weight="bold")
        self.f_text = tkfont.Font(family=fam, size=-max(11, int(h * 0.040)))
        self.f_knopf = tkfont.Font(family=fam, size=-max(11, int(h * 0.038)), weight="bold")
        self.f_klein = tkfont.Font(family=fam, size=-max(10, int(h * 0.030)))
        self.bed = Bedienung()
        self.pad = PadLeser(a.pad_quelle) if a.pad_quelle else None
        self.boxen = {}
        self.knoepfe = []
        self.liste = {}
        self.gewollt = None                            # Zeit des letzten Wunsches «koppeln» aus diesem Fenster
        self.auto_offen = a.start == "auto"
        self.t_liste = 0.0
        self.ende_t = None
        self.wunsch_ok = os.path.isdir(self.ordner)
        aktuell = status_lesen(a.status)
        if aktuell.get("schritt") in LAEUFT and time.time() - aktuell.get("t", 0) < 30:
            self.gewollt = aktuell.get("t", self.t0)   # läuft schon: nicht noch einmal anstossen
            self.auto_offen = False
        elif a.start == "koppeln":
            self.koppeln()
        self.liste_holen()
        self.root.bind_all("<Key>", self.taste)
        self.root.bind_all("<Button-1>", self.klick)
        self.root.protocol("WM_DELETE_WINDOW", self.zu)
        self.root.after(200, self.root.focus_force)
        self.tick()
        self.pad_tick()

    # ---------------------------------------------- Wünsche
    def koppeln(self):
        self.gewollt = time.time()
        self.ende_t = None
        self.wunsch_ok = wunsch(self.ordner, "koppeln") and self.wunsch_ok

    def liste_holen(self):
        self.t_liste = time.time()
        wunsch(self.ordner, "liste")

    def zu(self):
        marke_setzen(self.marke, False)
        self.root.destroy()

    def ausfuehren(self, tat):
        self.t_bedient = time.time()
        if tat is None:
            return
        if tat[0] == "zu":
            self.zu()
            return
        _, was, kuerzel = tat
        if was == "koppeln":
            self.koppeln()
        else:
            wunsch(self.ordner, was, kuerzel)
            if was != "abbrechen":
                self.gewollt = self.ende_t = None      # zurück zur Liste (das Ergebnis des letzten Koppelns ist erledigt)
            self.t_liste = time.time() - LISTE_S + 1.5  # die Liste kommt gleich vom Dienst; sonst bald nachfragen
        self.auto_offen = False

    # ---------------------------------------------- Eingaben
    def taste(self, e):
        self.t_bedient = time.time()
        k = (e.keysym or "").lower()
        if k == "escape":
            self.zu()
        elif k in ("up", "left", "iso_left_tab"):
            self.bed.bewegen(self.knoepfe, -1)
        elif k in ("down", "right", "tab"):
            self.bed.bewegen(self.knoepfe, 1)
        elif k in ("return", "kp_enter", "space"):
            self.ausfuehren(self.bed.waehlen(self.bed.fokus, time.time()))
        else:
            return
        if self.root.winfo_exists():
            self.zeichnen()

    def klick(self, e):
        self.t_bedient = time.time()
        x, y = e.x_root - self.root.winfo_rootx(), e.y_root - self.root.winfo_rooty()
        for key, (x0, y0, x1, y1) in self.boxen.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.ausfuehren(self.bed.waehlen(key, time.time()))
                break
        if self.root.winfo_exists():
            self.zeichnen()

    def pad_tick(self):
        if self.pad is not None:
            try:
                befehle = self.pad.lesen()
            except OSError:
                befehle = []
            for b in befehle:
                if time.time() - self.t0 < 1.0:        # was beim Öffnen noch gedrückt war, zählt nicht
                    continue
                self.t_bedient = time.time()
                if b == "zurueck":
                    self.zu()
                    return
                if b == "ok":
                    self.ausfuehren(self.bed.waehlen(self.bed.fokus, time.time()))
                    if not self.root.winfo_exists():
                        return
                else:
                    self.bed.bewegen(self.knoepfe, 1 if b == "ab" else -1)
            if befehle:
                self.zeichnen()
        self.root.after(50, self.pad_tick)

    # ---------------------------------------------- Bild
    def lage(self, jetzt):
        """-> (Farbe, Zeile gross, Zeile darunter, läuft die Suche?)"""
        s = status_lesen(self.a.status)
        if self.gewollt is None or (s and s["t"] < self.gewollt - 2):
            s = {}                                     # alter Stand (voriges Koppeln) oder hier noch nichts gewollt
        if s.get("schritt") in LAEUFT and jetzt - s["t"] > s["rest_s"] + 60:
            s = {"schritt": "fehler", "ok": False, "text": "Koppeln abgebrochen – noch einmal versuchen", "t": 0, "rest_s": 0}
        if not self.wunsch_ok:
            return (ROT, "Koppeln geht hier nicht (Ordner /run/moveeye-spiel fehlt)",
                    "Controller per USB-C-Kabel anschliessen – das geht immer", False)
        if self.gewollt is not None and not s:
            if jetzt - self.gewollt > OHNE_DIENST_S:
                return (ROT, "Koppeln ist auf diesem PC noch nicht eingerichtet (kommt mit dem HP-Update)",
                        "Controller per USB-C-Kabel anschliessen – das geht immer", False)
            return ORANGE, HALTEN, "Bluetooth wird vorbereitet …", True
        if not s or s["schritt"] == "abgebrochen":
            L = self.liste
            if L and not L["adapter"]:
                return ROT, KEIN_ADAPTER, "", False
            if L and not L["liste"]:
                return FG, "Noch kein Controller gekoppelt", "«Controller koppeln» wählen, dann: " + HALTEN, False
            return FG, "Gekoppelte Controller", "Ein gekoppelter Controller verbindet sich mit der PS-Taste von selbst.", False
        if s["schritt"] in ("start", "suche"):
            rest = "Suche Controller … noch %d s" % s["rest_s"] if s["schritt"] == "suche" else "Bluetooth wird vorbereitet …"
            return ORANGE, HALTEN, rest, True
        if s["schritt"] == "koppeln":
            return ORANGE, s["text"] or "Controller gefunden – wird gekoppelt …", "Bitte warten …", True
        if s.get("ok") is True:
            self.ende_t = self.ende_t or jetzt
            return (GRUEN, s["text"] or "Verbunden ✔",
                    "Zum Spielen: dieses Fenster schliessen, dann eine Taste am Controller drücken. Nächstes Mal genügt die PS-Taste.", False)
        if s["schritt"] == "kein_adapter":
            return ROT, s["text"] or KEIN_ADAPTER, "", False
        if s["schritt"] == "nicht_gefunden":
            return ROT, s["text"] or "Kein Controller gefunden", HALTEN + " – dann noch einmal «Controller koppeln»", False
        return ROT, s["text"] or "Nicht geklappt", "Ohne Bluetooth: Controller per USB-C-Kabel anschliessen", False

    def knopf(self, key, x0, y0, x1, y1, text, wichtig=False):
        c = self.c
        fokus = self.bed.fokus == key
        c.create_rectangle(x0, y0, x1, y1, fill=ORANGE if fokus else KACHEL, outline=ORANGE if (fokus or wichtig) else LINIE,
                           width=3 if fokus else 2)
        c.create_text((x0 + x1) // 2, (y0 + y1) // 2, text=text, fill=BG if fokus else FG, font=self.f_knopf, anchor="center")
        self.boxen[key] = (x0, y0, x1, y1)

    def zeichnen(self):
        jetzt = time.time()
        c, w, h = self.c, self.w, self.h
        farbe, gross, klein, laeuft = self.lage(jetzt)
        eintraege = self.liste.get("liste", []) if self.liste else []
        self.knoepfe = self.bed.knoepfe(eintraege, laeuft)
        self.boxen = {}
        c.delete("all")
        m = int(w * 0.04)
        gamepad_zeichnen(c, m + int(h * 0.07), int(h * 0.075), int(h * 0.075), farbe if laeuft else ORANGE, PANEL)
        c.create_text(m + int(h * 0.16), int(h * 0.075), text="Controller", fill=FG, font=self.f_titel, anchor="w")
        da = pads_da(self.a.pad_quelle) if self.a.pad_quelle else 0
        c.create_text(w - m, int(h * 0.075), text="Am HP erkannt: %d Controller" % da if da else "Am HP ist noch kein Controller erkannt",
                      fill=GRUEN if da else GRAU, font=self.f_klein, anchor="e")
        c.create_text(w // 2, int(h * 0.235), text=gross, fill=farbe, font=self.f_gross, anchor="center", width=w - 2 * m)
        c.create_text(w // 2, int(h * 0.375), text=klein, fill=FG, font=self.f_text, anchor="center", width=w - 2 * m)
        # Liste der gekoppelten Controller
        zh = int(h * 0.088)
        y = int(h * 0.455)
        bw = int(w * 0.17)
        for e in eintraege[:MAX_ZEILEN]:
            c.create_rectangle(m, y, w - m, y + zh - 6, fill=BG, outline=LINIE)
            c.create_oval(m + 14, y + zh // 2 - 10, m + 28, y + zh // 2 + 4, fill=GRUEN if e["verbunden"] else GRAU, outline="")
            t = e["art"] + ("  ·  verbunden" if e["verbunden"] else "  ·  nicht verbunden (PS-Taste drücken)")
            if e["akku"] is not None:
                t += "  ·  Akku %d %%" % e["akku"]
            c.create_text(m + 42, y + zh // 2 - 3, text=t, fill=FG, font=self.f_text, anchor="w")
            x1 = w - m - 8
            kv = ("vergessen", e["id"])
            self.knopf(kv, x1 - bw - int(w * 0.04), y + 5, x1, y + zh - 11, self.bed.text(kv, jetzt))
            if e["verbunden"]:
                kt = ("trennen", e["id"])
                x2 = x1 - bw - int(w * 0.04) - 10
                self.knopf(kt, x2 - bw + int(w * 0.03), y + 5, x2, y + zh - 11, self.bed.text(kt, jetzt))
            y += zh
        if len(eintraege) > MAX_ZEILEN:
            c.create_text(w // 2, y + 4, text="… und %d weitere" % (len(eintraege) - MAX_ZEILEN), fill=GRAU, font=self.f_klein)
        # unten: Hauptknopf und Schliessen
        y0, y1 = int(h * 0.83), int(h * 0.925)
        haupt = self.knoepfe[-2]
        self.knopf(haupt, m, y0, int(w * 0.60), y1, self.bed.text(haupt, jetzt, len(eintraege)), wichtig=True)
        self.knopf(("zu",), int(w * 0.64), y0, w - m, y1, self.bed.text(("zu",), jetzt))
        c.create_text(w // 2, int(h * 0.965), fill=GRAU, font=self.f_klein, anchor="center", width=w - 2 * m,
                      text="Antippen oder Klick  ·  Controller: Steuerkreuz, ✕ / A = wählen, ○ / B = zurück  ·  Tastatur: Pfeile, Enter, Esc")

    def tick(self):
        jetzt = time.time()
        marke_setzen(self.marke)
        self.liste = liste_lesen(self.liste_datei)
        if self.liste and self.liste["t"] < self.t0 - 2:
            self.liste = {}                            # alter Stand von früher: erst die neue Liste zeigen
        if self.auto_offen and (self.liste or jetzt - self.t0 > 2.5):
            self.auto_offen = False                    # --start auto: schon einer verbunden -> Liste; sonst gleich suchen
            if not any(e["verbunden"] for e in self.liste.get("liste", [])):
                self.koppeln()
        self.zeichnen()
        laeuft = self.lage(jetzt)[3]
        if not laeuft and jetzt - self.t_liste >= LISTE_S:
            self.liste_holen()
        ruhe = jetzt - self.t_bedient
        if (self.ende_t is not None and jetzt - self.ende_t > 15 and ruhe > 15) or (not laeuft and ruhe > 180) or jetzt - self.t0 > 900:
            self.zu()                                  # nach Erfolg bald zu; sonst nach 3 Min. ohne Bedienung
            return
        self.root.after(400, self.tick)


class Ecke:
    """Kleiner Knopf in einer Ecke des Kiosks: nur sichtbar, solange kein Controller angeschlossen ist und kein Test läuft.
    Antippen öffnet das Fenster «Controller koppeln» (ohne Tastatur erreichbar, während der Simulator läuft)."""
    def __init__(self, a):
        self.a = a
        self.root = tk.Tk(className="moveeye-controller-ecke")
        self.root.overrideredirect(True)               # ohne Rahmen, der Fenstermanager fasst es nicht an (nimmt nie den Fokus)
        self.root.attributes("-topmost", True)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        s = max(44, int(sh * 0.055))
        rand = max(8, int(sh * 0.012))
        x = rand if a.ecke.endswith("links") else sw - s - rand
        y = rand if a.ecke.startswith("oben") else sh - s - rand
        self.root.geometry("%dx%d+%d+%d" % (s, s, x, y))
        c = tk.Canvas(self.root, width=s, height=s, bg=PANEL, highlightthickness=2, highlightbackground=ORANGE, cursor="hand2")
        c.pack(fill="both", expand=True)
        gamepad_zeichnen(c, s // 2, s // 2, int(s * 0.42), ORANGE, PANEL)
        c.bind("<Button-1>", self.auf)
        self.sichtbar = True
        self.tick()

    def auf(self, _e=None):
        try:
            subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "--start", "auto", "--wunsch", self.a.wunsch,
                              "--status", self.a.status], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as e:
            print("controller_fenster:", e, file=sys.stderr)

    def tick(self):
        soll = pads_da(self.a.pad_quelle or "/dev/input") == 0 and not (self.a.pause and os.path.exists(self.a.pause))
        if soll and not self.sichtbar:
            self.root.deiconify()
        elif not soll and self.sichtbar:
            self.root.withdraw()
        self.sichtbar = soll
        if soll:
            self.root.lift()
        self.root.after(2500, self.tick)


def main():
    ap = argparse.ArgumentParser(description="MoveEye Kiosk: Controller per Bluetooth koppeln und verwalten (Fenster)")
    ap.add_argument("--wunsch", default="/run/moveeye-spiel/controller_koppeln")
    ap.add_argument("--status", default="/run/moveeye-controller/status.json")
    ap.add_argument("--start", choices=("auto", "koppeln", "liste"), default="auto")
    ap.add_argument("--ecke", choices=ECKEN, default=None, help="statt des Fensters: kleiner Knopf in dieser Ecke")
    ap.add_argument("--pause", default="", help="--ecke: Pause-Datei der Testläufe (dann kein Knopf)")
    ap.add_argument("--pad-quelle", default="/dev/input", help="Ordner mit js* (Controller als Bedienung); leer = aus")
    ap.add_argument("--fenster", default="", help="BxH (zum Prüfen)")
    a = ap.parse_args()
    if a.fenster and not all(x.isdigit() for x in a.fenster.split("x")):
        ap.error("--fenster BxH")
    if tk is None:
        print("controller_fenster: python3-tk fehlt", file=sys.stderr)
        return 3
    art = "ecke" if a.ecke else "fenster"
    sperre = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", "moveeye-controller-%s-%d.lock" % (art, os.getuid()))
    try:
        import fcntl
        lf = open(sperre, "a")
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)  # schon offen: nicht ein zweites Fenster
    except OSError:
        return 0
    try:
        (Ecke(a) if a.ecke else Fenster(a)).root.mainloop()
    except tk.TclError as e:
        print("controller_fenster:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
