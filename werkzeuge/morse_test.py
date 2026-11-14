#!/usr/bin/env python3
"""Test und Prüfstand «Morse-Modus» (MoveEye Teil 639zzz) – ohne echte Kamera, ohne echte Lampe.

  A) Zeichen und Zeitplan: Tabelle eindeutig, Umlaute / ß / CH, Prosigns (SOS als EIN Zeichen), unbekannte Zeichen werden
     ausgelassen und gemeldet, dit = 1 / dah = 3 / Pausen 1 / 3 / 7, Farnsworth, Tempo-Grenzen pro Ausgang (kein Weg
     schneller als die Grenze), Länge.
  B) Entschlüsseln aus Zeiten (ohne Bild): alle Tempi, Handtastung ±20 % / ±40 %, Farnsworth, gleichmässiges Blinken ist
     kein Text.
  C) Synthetische Kamera -> MorseRx: ein blinkender Fleck (Grösse, Helligkeit, Hintergrund, Rauschen, Bild-Zittern,
     verlorene Bilder, Belichtungszeit, Nachregeln der Belichtung, Wandern der Hand), dazu ein Dauerlicht und ein Blinker
     mit 1.5 Hz (darf nicht als Text gelesen werden).
  D) Rundlauf: MoveEyes eigener Sender (morse_encode -> morse_timeline) -> synthetische Kamera -> MorseRx für ALLE Zeichen
     der Tabelle und alle Prosigns.
  E) Feindliche Eingabe: zufällige Lichtmuster, Rauschen, springende Uhr, Bildgrösse wechselt, leere Bilder - kein Absturz,
     Speicher bleibt begrenzt, der Text enthält nur Zeichen der Tabelle und ist gekürzt.
  F) MoveEye mit der Demo-Kamera: Rechte (Familie / Kind / ohne Anmeldung / fremde Webseite), PIN, Modus pausiert den Schutz und endet
     von selbst (nie länger als 30 min), Senden mit Tempo-Grenze pro Ausgang (am GPIO gemessen), Stopp, eine Sendung auf einmal,
     Empfang einer Lampe im Demo-Bild (Live, Verlauf, Push ohne Ort), «Strom weg» im Modus. G) --browser: Seite 390 px / PC, 5 Sprachen.
     Schritt 2: Ton am «Mikrofon» (ab Werk aus; gewählt: gelesen, nichts gespeichert), Testsignal der Gegenstelle, kein eigenes Echo.
  I) Ton: synthetisches Mikrofon -> MorseAudio (Tempo, Rauschen, Pfiff, Funkkanal, Dauerton, Pieper, Unsinn), Rundlauf eigener Ton.
  H) Nachgebaute Hardware (PCA9685 ohne Bus, GPIO): Status-LED und IR am PCA9685 getastet; Programm mitten in einem Strich
     abgeschossen (kill -9) - die Ausgänge stehen an - nach dem Neustart sind alle wieder im Zustand der Regeln.
  --messen-ton / --messen-ir: die Tabellen Ton (Tempo × Rauschen, Funkkanal) und IR zwischen zwei MoveEye (docs/Morse_Messung_*.md).
  --messen: die Tabelle Bildrate × Tempo × Fleckgrösse -> Zeichenfehler (dauert einige Minuten), --tabelle DATEI schreibt sie.

  python3 werkzeuge/morse_test.py [--datei X.py | --quelle] [--messen] [--tabelle DATEI] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import http.server
import json
import math
import os
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

import numpy as np
import cv2

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}


def ok(cond, what):
    if cond:
        N["ok"] += 1
        print("  ✓ " + what, flush=True)
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def lade_kern():
    """nur der Kern aus quelle/639zzz_morse.py (zwischen den Marken) - für die Entwicklung und die Messung"""
    src = open(os.path.join(REPO, "quelle", "639zzz_morse.py"), encoding="utf-8").read()
    a, e = src.index("# ==== MORSE-KERN ANFANG"), src.index("# ==== MORSE-KERN ENDE")
    ns = {"math": math, "time": time, "np": np, "cv2": cv2}
    exec(compile(src[a:e], "639zzz_morse.py(kern)", "exec"), ns)
    return ns


def lev(a, b):
    """Levenshtein-Abstand"""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(soll, ist):
    """Zeichenfehler-Rate ohne Leerzeichen (0 = alles richtig, 1 = nichts)"""
    s, i = soll.replace(" ", ""), ist.replace(" ", "")
    return min(1.0, lev(s, i) / float(max(1, len(s))))


# ---------------------------------------------------------------------------------------------- die synthetische Kamera
class Kamera:
    """Bilder 640 × 360 (so gross wie das Arbeitsbild von MoveEye) mit einem blinkenden Fleck.
    fps Bilder/s · groesse = Radius des Flecks in Pixeln · hell = Helligkeit des Flecks über dem Hintergrund (linear, darf
    überlaufen) · hg = Hintergrund (0..255) · rausch = Sigma des Bildrauschens · zittern = so viel später (Teil der Bildperiode,
    gestreut) meldet MoveEye das Bild · verlust = Anteil verlorener Bilder · belichtung = Belichtungszeit (Teil der Bildperiode) · regel = die
    Kamera regelt die Helligkeit nach (True) · wandern = Pixel, um die der Fleck wandert (Hand) · dauerlicht / blinker =
    ein zweites Licht, das immer leuchtet / mit 1.5 Hz blinkt."""
    W, H = 640, 360
    UNSCHARF = 0.7                      # Pixel (Sigma) Unschärfe der Optik im Arbeitsbild

    def __init__(self, fps=15.0, groesse=3.0, hell=400.0, hg=25.0, rausch=3.0, zittern=0.1, verlust=0.0, belichtung=0.5, regel=True,
                 wandern=3.0, dauerlicht=False, blinker=False, laeufer=False, seed=1):
        self.fps, self.T = float(fps), 1.0 / float(fps)
        self.rng = np.random.default_rng(seed)
        self.rnd = random.Random(seed)
        self.zittern, self.verlust, self.E, self.regel, self.wandern = zittern, verlust, belichtung, regel, wandern
        tex = cv2.resize(self.rng.uniform(-0.3, 0.3, (9, 16)).astype(np.float32), (self.W, self.H), interpolation=cv2.INTER_CUBIC)
        base = np.clip(hg * (1.0 + tex), 0, 255)
        self.pool = [np.clip(base + self.rng.normal(0, rausch, base.shape), 0, 255).astype(np.float32) for _ in range(6)]
        self.fleck = self._blob(groesse, hell)
        self.pos = (self.rng.uniform(0.25, 0.75) * self.W, self.rng.uniform(0.25, 0.75) * self.H)
        self.extra = []
        if dauerlicht:
            self.extra.append((self._blob(4.0, 500.0), (0.12 * self.W, 0.2 * self.H), None))
        if blinker:
            self.extra.append((self._blob(4.0, 450.0), (0.88 * self.W, 0.8 * self.H), 1.5))
        self.laeufer = laeufer
        self.gain = 1.0
        self.ph = self.rng.uniform(0, 6.28, 4)

    @staticmethod
    def _blob(r, amp):
        s0 = max(0.2, r / 1.5)
        s = math.sqrt(s0 * s0 + Kamera.UNSCHARF ** 2)         # die Optik verschmiert: ein kleiner Fleck wird breiter und dunkler
        n = int(max(3, math.ceil(s * 5))) | 1
        ax = np.arange(n) - n // 2
        g = np.exp(-(ax[:, None] ** 2 + ax[None, :] ** 2) / (2.0 * s * s))
        return (g * amp * (s0 * s0) / (s * s)).astype(np.float32)

    def _add(self, img, blob, pos, k):
        if k <= 0.0:
            return
        n = blob.shape[0]
        x0, y0 = int(round(pos[0])) - n // 2, int(round(pos[1])) - n // 2
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(self.W, x0 + n), min(self.H, y0 + n)
        if xb > xa and yb > ya:
            img[ya:yb, xa:xb] += blob[ya - y0:yb - y0, xa - x0:xb - x0] * k

    @staticmethod
    def _anteil(a, b, zeiten):
        """Anteil von [a, b], in dem das Licht an ist; zeiten = [(von, bis)]"""
        if b <= a:
            return 0.0
        s = 0.0
        for v, bis in zeiten:
            if bis <= a:
                continue
            if v >= b:
                break
            s += min(b, bis) - max(a, v)
        return s / (b - a)

    def lauf(self, zeiten, dauer):
        """liefert (Graubild uint8, Zeit) für `dauer` Sekunden"""
        i = 0
        while True:
            t = i * self.T
            i += 1
            if t > dauer:
                return
            if self.verlust and self.rnd.random() < self.verlust:
                continue
            tt = t                                            # die Aufnahme ist im Takt, nur die gemeldete Zeit streut (kommt später an)
            tm = max(getattr(self, "_tm", -1.0) + 1e-4, t + (abs(self.rnd.gauss(0, self.zittern * self.T)) if self.zittern else 0.0))
            self._tm = tm
            img = self.pool[self.rnd.randrange(len(self.pool))].copy()
            a = tt - self.E * self.T
            w = self.wandern
            pos = (self.pos[0] + w * (math.sin(2 * math.pi * 1.3 * tt + self.ph[0]) * 0.4 + math.sin(2 * math.pi * 0.21 * tt + self.ph[1])),
                   self.pos[1] + w * (math.sin(2 * math.pi * 1.1 * tt + self.ph[2]) * 0.4 + math.sin(2 * math.pi * 0.17 * tt + self.ph[3])))
            self._add(img, self.fleck, pos, self._anteil(a, tt, zeiten))
            for blob, p, hz in self.extra:
                if hz is None:
                    k = 1.0
                else:
                    per = 1.0 / hz
                    n0 = int(a / per) - 1
                    k = self._anteil(a, tt, [((n0 + j) * per, (n0 + j) * per + per / 2) for j in range(4)])
                self._add(img, blob, p, k)
            if self.laeufer:                                  # jemand in heller Kleidung geht knapp unter der Lampe durch (30 × 100 Pixel)
                lx, ly = int(self.pos[0] - 150 + 70.0 * tt), int(self.pos[1] + 60)
                img[max(0, ly):min(self.H, ly + 100), max(0, lx):min(self.W, lx + 30)] += 150.0
            if self.regel:                                    # die Kamera regelt nach: träge, auf mittlere Helligkeit
                img *= self.gain
                m = float(np.minimum(img, 255.0).mean())
                ziel = 60.0 if self.pool[0].mean() > 60 else max(25.0, float(self.pool[0].mean()))
                self.gain = min(4.0, max(0.2, self.gain * (1.0 + 0.2 * (ziel - m) / max(ziel, 1.0))))
            yield np.clip(img, 0, 255).astype(np.uint8), tm


def zeiten_aus(tl, start=1.0, hand=0.0, rnd=None):
    """Zeitplan [(s, an)] -> [(von, bis)] der AN-Zeiten; hand = ±Anteil, um den jede Länge von Hand streut"""
    out, t = [], start
    for d, on in tl:
        if hand and rnd is not None:
            d *= 1.0 + rnd.uniform(-hand, hand)
        if on:
            out.append((t, t + d))
        t += d
    return out, t


def senden_empfangen(ns, text, wpm, kam, farnsworth=0, hand=0.0, seed=1):
    """MoveEyes Sender -> Kamera -> MorseRx. Liefert (empfangener Text, Statistik)"""
    signs, _skip = ns["morse_encode"](text)
    tl = ns["morse_timeline"](signs, wpm, farnsworth)
    zeiten, ende = zeiten_aus(tl, 1.0, hand, random.Random(seed))
    got = []
    rx = ns["MorseRx"](lambda txt, info: got.append(txt))
    u = ns["morse_unit"](farnsworth or wpm)
    for g, t in kam.lauf(zeiten, ende + max(4.5, 17.0 * u) + 1.0):
        rx.feed(g, t)
    return " ".join(got), rx.stats


SOLL = "PARIS QTH BERN 59"


def zelle(ns, fps, wpm, groesse, n=3, **kw):
    """mittlere Zeichenfehler-Rate über n Läufe"""
    s = 0.0
    hand = kw.pop("hand", 0.0)
    fw = kw.pop("farnsworth", 0)
    for seed in range(1, n + 1):
        kam = Kamera(fps=fps, groesse=groesse, seed=seed * 7 + int(fps) + int(wpm * 3), **kw)
        got, _st = senden_empfangen(ns, SOLL, wpm, kam, farnsworth=fw, hand=hand, seed=seed)
        s += cer(SOLL, got)
    return s / n


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(ns):
    print("A) Zeichen und Zeitplan", flush=True)
    code, pro = ns["MORSE_CODE"], ns["MORSE_PROSIGNS"]
    ok(len(set(code.values())) == len(code), f"{len(code)} Zeichen, jedes Morsezeichen nur einmal")
    ok(all(set(v) <= set(".-") and 1 <= len(v) <= 9 for v in list(code.values()) + list(pro.values())), "nur Punkt und Strich, höchstens 9 Elemente")
    enc, tl_ = ns["morse_encode"], ns["morse_timeline"]
    s, skip = enc("Grüße aus Zürich, ä ö ü ch ß!")
    shown = "".join(x[1] for x in s)
    ok("Ü" in shown and "ß" in shown and "CH" in shown and "Ä" in shown and "Ö" in shown and not skip, f"Umlaute, ß, CH: «{shown}»")
    ok(dict((x[1], x[0]) for x in s)["CH"] == "----" and dict((x[1], x[0]) for x in s)["ß"] == "...--..", "CH = ---- und ß = ...--..")
    s, skip = enc("a€b 😀 c{")
    ok([x[1] for x in s] == ["A", "B", " ", "C"] and skip == ["€", "😀", "{"], f"unbekannte Zeichen ausgelassen und gemeldet: {skip}")
    s, skip = enc("<SOS> <sos> <XX>")
    ok(s[0] == ("...---...", "<SOS>") and s[2][0] == "...---..." and "<" in skip, "SOS als EIN Zeichen (auch klein geschrieben), <XX> ist keines")
    tl = tl_(enc("<SOS>")[0], 5)
    ok(len(tl) == 17 and all(abs(d - (0.24 if i % 2 or (i // 2) not in (3, 4, 5) else 0.72)) < 1e-9 for i, (d, _on) in enumerate(tl)),
       "SOS: 9 Elemente, dazwischen nur 1 Einheit Pause")
    u = ns["morse_unit"](12)
    tl = tl_(enc("PARIS PARIS")[0], 12)
    tot = sum(d for d, _ in tl) + 7 * u
    ok(abs(tot - 100 * u) < 1e-6 and abs(u - 0.1) < 1e-9, f"PARIS = 50 Einheiten ({tot / u:.1f} für zwei), dit bei 12 WPM = {u * 1000:.0f} ms")
    tl = tl_(enc("EE E")[0], 10)
    ok([round(d / ns["morse_unit"](10), 3) for d, _ in tl] == [1, 3, 1, 7, 1], "Pausen 3 (Zeichen) und 7 (Wort) Einheiten")
    tf = tl_(enc("EE E")[0], 18, 5)
    ok(abs(tf[0][0] - 1.2 / 18) < 1e-9 and tf[1][0] > 3 * 1.2 / 18 * 3 and abs(tf[3][0] / tf[1][0] - 7 / 3.0) < 1e-6,
       f"Farnsworth 18 / 5: dit bleibt {tf[0][0] * 1000:.0f} ms, Zeichenpause {tf[1][0]:.2f} s, Wortpause {tf[3][0]:.2f} s")
    ok(tl_(enc("E")[0], 10, 10) == tl_(enc("E")[0], 10) and tl_(enc("EE")[0], 10, 15) == tl_(enc("EE")[0], 10), "Farnsworth schneller als das Tempo = aus")
    ts, total = ns["morse_edges"](tl_(enc("AB")[0], 6))
    on = ns["morse_on_at"]
    ok(on(ts, total, 0.0) and not on(ts, total, 0.2 + 1e-6) and on(ts, total, 0.4 + 1e-6) and not on(ts, total, total) and not on(ts, total, -1)
       and not on(ts, total, 1e9), "morse_on_at: Taste nach der Zeit, vor dem Start und nach dem Ende aus")
    ok(len(enc("E" * 5000)[0]) <= ns["MORSE_TEXT_MAX"] * 2 and len(enc("E " * 5000)[0]) <= ns["MORSE_TEXT_MAX"] * 2, "sehr langer Text wird gekürzt")
    ok(ns["morse_upper"]("straße é ç") == "STRAßE É C", "Grossschreibung: ß bleibt, é bleibt (in der Tabelle), ç -> C")


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(ns):
    print("B) Entschlüsseln aus Zeiten", flush=True)
    enc, tl_, dec = ns["morse_encode"], ns["morse_timeline"], ns["morse_decode"]

    def run(text, wpm, hand=0.0, fw=0, seed=3):
        tl = tl_(enc(text)[0], wpm, fw)
        rnd = random.Random(seed)
        d = [x * (1.0 + rnd.uniform(-hand, hand)) for x, _on in tl]
        ons, gaps = d[0::2], d[1::2] + [None]
        return dec(ons, gaps)
    txt = "CQ CQ DE HB9 MOVEEYE K"
    bad = [w for w in (3, 5, 8, 12, 18, 25) if run(txt, w)["text"] != txt]
    ok(not bad, f"sauber getastet: 3 bis 25 WPM richtig (falsch bei {bad})")
    r = run(txt, 12)
    ok(abs(r["wpm"] - 12) < 0.3 and r["q"] == 1.0 and not r["periodic"], f"Tempo aus dem Signal geschätzt: {r['wpm']} WPM")
    e20 = sum(cer(txt, run(txt, 8, 0.2, seed=s)["text"]) for s in range(40)) / 40
    e40 = sum(cer(txt, run(txt, 8, 0.4, seed=s)["text"]) for s in range(40)) / 40
    ok(e20 <= 0.01, f"Handtastung ±20 %: Zeichenfehler {e20 * 100:.1f} %")
    ok(e40 <= 0.12, f"Handtastung ±40 %: Zeichenfehler {e40 * 100:.1f} % (die Grenze: Pausen 1.4 und 1.8 Einheiten liegen dicht)")
    N["hand20"], N["hand40"] = e20, e40
    ok(run(txt, 18, 0.0, 6)["text"] == txt and run(txt, 15, 0.15, 5)["text"].replace(" ", "") == txt.replace(" ", ""), "Farnsworth 18 / 6 und 15 / 5 (mit ±15 %)")
    ok(run("SOS", 6)["text"] == "SOS" and run("<SOS>", 6)["text"] == "<SOS>" and run("OOO", 6)["text"] == "OOO" and run("EEE", 6)["text"] == "EEE",
       "nur Punkte / nur Striche: die Pausen entscheiden (SOS, <SOS>, OOO, EEE)")
    per = dec([0.33] * 12, [0.33] * 11 + [None])
    ok(per["periodic"], "gleichmässiges Blinken (1.5 Hz) = «periodic», kein Text")
    ok(not run("SOS SOS", 6)["periodic"] and not run("HHH", 6)["periodic"], "SOS und HHH sind NICHT gleichmässig")
    ok(dec([], [])["text"] == "" and dec([0.1], [None])["text"] == "E" and dec([1e-9, 1e9], [0, None])["n"] == 2, "leer, ein Element, unsinnige Zeiten: kein Fehler")
    r = dec([0.1, 0.1, 0.3, 0.3, 0.1, 0.1, 0.3, 0.1, 0.3], [0.1] * 8 + [None])
    ok(r["text"] == ns["MORSE_UNKNOWN"] and r["unknown"] == 1, "ein Zeichen, das es nicht gibt, wird «#»")


# ---------------------------------------------------------------------------------------------------------------------- C
def teil_c(ns):
    print("C) Synthetische Kamera -> MorseRx", flush=True)
    for fps, wpm, gr in ((30, 10, 3.0), (15, 5, 1.0), (10, 4, 6.0)):
        e = zelle(ns, fps, wpm, gr, n=2)
        ok(e <= 0.03, f"{fps} Bilder/s, {wpm} WPM, Fleck {gr:g} px: Zeichenfehler {e * 100:.0f} %")
    e = zelle(ns, 15, 5, 3.0, n=2, hg=140.0, hell=110.0, rausch=4.0)
    ok(e <= 0.05, f"Tageslicht (Hintergrund 140, Fleck nur 110 heller): Zeichenfehler {e * 100:.0f} %")
    e = zelle(ns, 15, 5, 3.0, n=2, wandern=14.0)
    ok(e <= 0.05, f"Hand wandert ±14 Pixel: Zeichenfehler {e * 100:.0f} %")
    e = zelle(ns, 15, 5, 3.0, n=2, verlust=0.05, zittern=0.25)
    ok(e <= 0.1, f"5 % verlorene Bilder, Bildzeit streut 25 %: Zeichenfehler {e * 100:.0f} %")
    e = zelle(ns, 15, 5, 3.0, n=2, dauerlicht=True, blinker=True)
    ok(e <= 0.03, f"mit Dauerlicht und Blinker 1.5 Hz daneben: Zeichenfehler {e * 100:.0f} %")
    e = zelle(ns, 15, 5, 3.0, n=3, laeufer=True)
    ok(e <= 0.03, f"jemand in heller Kleidung geht beim ersten Zeichen knapp unter der Lampe durch: Zeichenfehler {e * 100:.0f} %")
    # nur Dauerlicht + Blinker, kein Morse: nichts darf als Text gemeldet werden
    kam = Kamera(fps=15, dauerlicht=True, blinker=True, seed=5)
    got = []
    rx = ns["MorseRx"](lambda txt, info: got.append(txt))
    live = 0
    for g, t in kam.lauf([], 40.0):
        if rx.feed(g, t):
            live += 1
    ok(not got and not live and rx.stats["periodic"] >= 1, f"Blinker 1.5 Hz allein, 40 s: kein Text, als gleichmässig erkannt ({rx.stats['periodic']}×)")
    kam = Kamera(fps=15, dauerlicht=True, seed=6)
    rx = ns["MorseRx"](lambda txt, info: got.append(txt))
    for g, t in kam.lauf([], 15.0):
        rx.feed(g, t)
    ok(not got and rx.stats["tracks"] == 0, "Dauerlicht allein: keine Spur, kein Text")
    ok(rx.stats["ms"] < 10.0, f"Rechenzeit pro Bild {rx.stats['ms']:.2f} ms (dieser Rechner)")
    N["ms"] = rx.stats["ms"]


# ---------------------------------------------------------------------------------------------------------------------- D
def teil_d(ns):
    print("D) Rundlauf Sender -> Kamera -> Empfänger, alle Zeichen", flush=True)
    code, pro = ns["MORSE_CODE"], ns["MORSE_PROSIGNS"]
    zeichen = [k for k in code]
    gruppen = [zeichen[i:i + 6] for i in range(0, len(zeichen), 6)]
    falsch = []
    for gi, grp in enumerate(gruppen):
        text = " ".join("".join(grp[i:i + 3]) for i in range(0, len(grp), 3))
        soll = "".join(x[1] for x in ns["morse_encode"](text)[0])
        got, _st = senden_empfangen(ns, text, 6, Kamera(fps=15, groesse=3.0, seed=40 + gi))
        if got != soll:
            falsch.append((soll, got))
    ok(not falsch, f"alle {len(zeichen)} Zeichen der Tabelle kommen gleich zurück (6 WPM, 15 Bilder/s)" + (f" - falsch: {falsch[:3]}" if falsch else ""))
    gleich = {"AR": "+", "BT": "=", "KN": "("}
    falsch = []
    for gi, names in enumerate((["SOS", "AR", "SK", "KA"], ["BT", "HH", "SN", "KN"])):
        text = " ".join("<" + n + ">" for n in names)
        soll = " ".join(gleich.get(n, "<" + n + ">") for n in names)
        got, _st = senden_empfangen(ns, text, 6, Kamera(fps=15, groesse=3.0, seed=60 + gi))
        if got != soll:
            falsch.append((soll, got))
    ok(not falsch, "alle Prosigns (<SOS> <SK> <KA> <HH> <SN>; <AR> = +, <BT> = =, <KN> = ( )" + (f" - falsch: {falsch}" if falsch else ""))
    got, _st = senden_empfangen(ns, "Grüße aus Zürich", 6, Kamera(fps=15, seed=77))
    ok(got == "GRÜßE AUS ZÜRICH".replace("ICH", "ICH"), f"«Grüße aus Zürich» -> «{got}»")
    got, _st = senden_empfangen(ns, "MOVEEYE RUFT", 15, Kamera(fps=30, seed=78), farnsworth=6)
    ok(got == "MOVEEYE RUFT", f"Farnsworth 15 / 6 bei 30 Bildern/s -> «{got}»")


# ---------------------------------------------------------------------------------------------------------------------- E
def teil_e(ns):
    print("E) Feindliche Eingabe", flush=True)
    erlaubt = set("".join(ns["MORSE_DECODE"].values())) | set(" " + ns["MORSE_UNKNOWN"])
    rnd = random.Random(11)
    rng = np.random.default_rng(11)
    got = []
    rx = ns["MorseRx"](lambda txt, info: got.append(txt))
    t = 0.0
    worst = 0
    flecken = [(rnd.randrange(20, 620), rnd.randrange(20, 340)) for _ in range(12)]
    zust = [False] * 12
    t0 = time.time()
    for i in range(6000):
        t += rnd.choice((0.01, 0.033, 0.066, 0.1, 0.3))
        img = rng.integers(0, 40, (360, 640), dtype=np.uint8)
        for k, (x, y) in enumerate(flecken):
            if rnd.random() < 0.3:
                zust[k] = not zust[k]
            if zust[k]:
                img[y - 3:y + 3, x - 3:x + 3] = 255
        if i % 500 == 499:
            img[:] = 255 if (i // 500) % 2 else 0           # das ganze Bild blitzt
        live = rx.feed(img, t)
        if live:
            worst = max(worst, len(live["text"]))
            if not set(live["text"]) <= erlaubt:
                FEHLER.append("fremdes Zeichen im Live-Text")
        if len(rx.tracks) > rx.TRACKS or any(len(q["key"].ons) > q["key"].EL_MAX or len(q["key"].v) > 401 for q in rx.tracks):
            FEHLER.append("Speicher wächst"); break
    dt = time.time() - t0
    ok(all(set(m) <= erlaubt and len(m) <= ns["MORSE_RX_TEXT_MAX"] for m in got) and worst <= ns["MORSE_RX_TEXT_MAX"],
       f"6000 Bilder zufälliges Geflacker an 12 Stellen: kein Absturz, {len(got)} «Texte», alle nur Zeichen der Tabelle, höchstens {ns['MORSE_RX_TEXT_MAX']} lang")
    ok(len(rx.tracks) <= rx.TRACKS and len(rx.ignore) <= 8 and rx.buf.shape[0] == rx.BUF, f"Speicher begrenzt: {len(rx.tracks)} Spuren, Puffer {rx.buf.nbytes // 1024} KB")
    ok(dt / 6000 * 1000 < 20.0, f"{dt / 6000 * 1000:.2f} ms pro Bild im schlimmsten Fall (Grenze 20 ms: auch auf einem vollen Rechner)")
    # die Uhr springt, die Grösse wechselt, leere / winzige Bilder
    rx = ns["MorseRx"](None)
    try:
        for g, tt in ((np.zeros((360, 640), np.uint8), 5.0), (np.zeros((360, 640), np.uint8), 1.0), (np.zeros((90, 160), np.uint8), 1.1),
                      (np.zeros((2, 3), np.uint8), 1.2), (np.full((720, 1280), 255, np.uint8), 1.3), (np.zeros((360, 640), np.uint8), 1e12),
                      (np.zeros((360, 640), np.uint8), -5.0), (np.zeros((360, 640), np.uint8), float("nan"))):
            rx.feed(g, tt)
        heil = True
    except Exception as e:
        heil = False
        print("    ", type(e).__name__, e)
    ok(heil, "Uhr springt zurück / weit vor / NaN, Bildgrösse wechselt, 2 × 3 Pixel: kein Fehler")
    # ein Sender, der nie aufhört: die Nachricht wird nach EL_MAX Elementen geschlossen
    got = []
    rx = ns["MorseRx"](lambda txt, info: got.append(txt))
    key = ns["MorseKey"]()
    tt = 0.0
    for i in range(3000):
        key.edge(True, tt); tt += 0.1 if i % 3 else 0.3
        key.edge(False, tt); tt += 0.1 if i % 7 else 0.3
    ok(len(key.ons) == key.EL_MAX and len(key.gaps) == key.EL_MAX, f"MorseKey nimmt höchstens {key.EL_MAX} Elemente")
    r = ns["morse_decode"](key.ons, key.gaps)
    ok(len(r["text"]) <= ns["MORSE_RX_TEXT_MAX"], f"Text einer endlosen Sendung auf {len(r['text'])} Zeichen gekürzt")


# ---------------------------------------------------------------------------------------------------------------------- F
WRAP = r"""
import json, os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = '''
_mt_read = DemoSource.read
def _mt_read_blink(self):                                 # a lamp in the demo picture, on by the plan in the file MW_MORSE_PLAN
    ok_, img_ = _mt_read(self)
    try:
        if ok_ and os.path.exists(os.environ["MW_MORSE_PLAN"]):
            P_ = json.load(open(os.environ["MW_MORSE_PLAN"]))
            n_ = time.time() - P_["t0"]
            if any(a_ <= n_ < b_ for a_, b_ in P_["zeiten"]):
                img_ = img_.copy(); cv2.circle(img_, (P_["x"], P_["y"]), 7, (255, 255, 255), -1)
    except Exception:
        pass
    return ok_, img_
DemoSource.read = _mt_read_blink
_mt_hwl = Hardware._lights
_MT = {"last": {}}
def _mt_hw_lights(self, wanted):                          # every switch of a GPIO the hardware loop would write, with its time
    _mt_hwl(self, wanted)
    try:
        for g_, (on_, al_) in wanted.items():
            if _MT["last"].get(g_) != on_:
                _MT["last"][g_] = on_
                open(os.environ["MW_MORSE_OUT"], "a").write(json.dumps([time.time(), g_, bool(on_)]) + chr(10))
        fr_ = LED.get("frame") or {}
        k_ = fr_.get("layer") == "morse" and fr_.get("br", 0) > 0
        if _MT["last"].get("led") != k_:
            _MT["last"]["led"] = k_
            open(os.environ["MW_MORSE_OUT"], "a").write(json.dumps([time.time(), "led", bool(k_)]) + chr(10))
    except Exception:
        pass
Hardware._lights = _mt_hw_lights
def _mt_ton():                                            # a «microphone»: the sound of the file MW_MORSE_TON, in real time
    while True:
        time.sleep(0.2)
        try:
            p_ = os.environ.get("MW_MORSE_TON", "")
            if p_ and os.path.exists(p_) and AUDIO is not None:
                d_ = open(p_, "rb").read(); os.remove(p_)
                for i_ in range(0, len(d_), 3200):
                    AUDIO._chunk(d_[i_:i_ + 3200]); time.sleep(0.097)
        except Exception as e_:
            print("mt_ton", e_, flush=True)
threading.Thread(target=_mt_ton, daemon=True).start()
'''
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
"""
PW = "Morse-" + "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))
PIN = "4821"


class Hook(http.server.BaseHTTPRequestHandler):
    got = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        Hook.got.append(self.rfile.read(n) + b" | " + json.dumps(dict(self.headers)).encode())
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def teil_f(datei, ns, browser, bilder):
    print("F) MoveEye mit Demo-Kamera: Modus, Rechte, Ausgänge, Empfang", flush=True)
    hook = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Hook)
    threading.Thread(target=hook.serve_forever, daemon=True).start()
    tmp = tempfile.mkdtemp(prefix="mw_morse_f_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    plan_f, out_f = os.path.join(tmp, "plan.json"), os.path.join(tmp, "out.txt")
    rec = os.path.join(tmp, "aufnahmen")
    st = {"source": "demo", "thermal_source": "", "thermal_on": False, "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False,
          "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "news_popup": False, "tours_auto": False, "notify_type": "webhook",
          "notify_url": f"http://127.0.0.1:{hook.server_address[1]}/hook", "notify_on": True, "light_white_out": "gpio:17", "light_ir_out": "gpio:27",
          "armed": True, "protect_level": "watch", "arm_delay": 0, "record_dir": rec, "tamper_on": True, "ai_enabled": False,
          "latitude": 46.95, "longitude": 7.44, "eco_on": False}
    json.dump({"cfg": st, "relays": [{"name": "Scheinwerfer", "gpio": 22, "mode": "off", "trigger": "person", "hold": 5.0, "active_low": False}]},
              open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    ton_f = os.path.join(tmp, "ton.raw")
    env = dict(os.environ, MW_MORSE_PLAN=plan_f, MW_MORSE_OUT=out_f, MW_MORSE_TON=ton_f)
    P = {"p": None}

    def start():
        P["p"] = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                                   "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    start()
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    A = ("admin", PW)

    def req(path, data=None, user=A, pin=None, origin=None):
        h = {"Authorization": "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode()} if user else {}
        h["Content-Type"] = "application/json"
        if pin:
            h["X-MW-PIN"] = pin
        if origin:
            h["Origin"] = origin
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
        try:
            with op.open(r, timeout=60) as x:
                b = x.read()
                return x.status, (json.loads(b) if x.headers.get_content_type() == "application/json" else b)
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                return e.code, json.loads(b)
            except ValueError:
                return e.code, b

    def mstate():
        return req("/api/morse?lang=de")[1]["state"]

    def warte(was, s=30.0):
        ende = time.time() + s
        while time.time() < ende:
            try:
                if was():
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def log_text(q="Morse"):
        return json.dumps(req("/api/log?limit=3000&q=" + q)[1].get("lines", []), ensure_ascii=False)

    def kanten(g):
        out = []
        if os.path.exists(out_f):
            for ln in open(out_f):
                t, gg, on = json.loads(ln)
                if gg == g:
                    out.append((t, on))
        return out

    def gesendet(g):
        """was der Ausgang wirklich getastet hat: (Text, kürzeste AN-Zeit, höchste Zahl Schaltspiele pro Sekunde)"""
        k = kanten(g)
        while k and not k[0][1]:
            k.pop(0)
        ons, gaps = [], []
        for i in range(0, len(k) - 1, 2):
            ons.append(k[i + 1][0] - k[i][0]); gaps.append(k[i + 2][0] - k[i + 1][0] if i + 2 < len(k) else None)
        r = ns["morse_decode"](ons, gaps)
        per = [k[i + 2][0] - k[i][0] for i in range(0, len(k) - 2, 2)]
        return r["text"], (min(ons) if ons else 0.0), (1.0 / min(per) if per else 0.0)

    def blinken(text, wpm, vor=1.5):
        try:                                                          # nie schneller, als diese Kamera jetzt liest (0.4 × Bilder/s):
            wpm = max(3, min(wpm, int(mstate()["rx"]["limit"])))      # auf einem vollen Rechner liefert die Demo-Kamera weniger Bilder
        except Exception:
            pass
        zeiten, ende = zeiten_aus(ns["morse_timeline"](ns["morse_encode"](text)[0], wpm), vor)
        json.dump({"t0": time.time(), "zeiten": zeiten, "x": 420, "y": 250}, open(plan_f + ".tmp", "w")); os.replace(plan_f + ".tmp", plan_f)
        return ende
    try:
        ok(warte(lambda: req("/api/state")[0] == 200, 90), "MoveEye läuft (Demo-Kamera)")
        for n_, r_ in {"Anna": "family", "Kim": "kid"}.items():
            req("/api/users", {"action": "add", "name": n_, "password": n_.lower() + "-pass-1", "role": r_})
        warte(lambda: req("/api/state")[1]["state"].get("arm_state") == "armed", 30)
        print("F) Rechte", flush=True)
        for wer in (("Anna", "anna-pass-1"), ("Kim", "kim-pass-1")):
            c = [req("/api/morse", user=wer)[0], req("/morse", user=wer)[0], req("/api/morse", {"action": "start", "minutes": 5}, user=wer)[0],
                 req("/api/morse", {"action": "send", "text": "SOS", "outs": ["white"], "wpm": 5}, user=wer)[0],
                 req("/api/morse", {"action": "prefs", "rx_push": True}, user=wer)[0], req("/api/set", {"key": "morse_rx_push", "value": True}, user=wer)[0]]
            ok(all(x == 403 for x in c), f"{wer[0]}: Seite, Zustand, Start, Senden, Einstellungen = 403 {c}")
        ok(req("/api/morse", user=None)[0] == 401 and req("/api/morse", {"action": "start", "minutes": 5}, user=None)[0] == 401, "ohne Anmeldung: 401")
        c, j = req("/api/morse", {"action": "start", "minutes": 5}, origin="https://boese.example")
        ok(c == 403 and not mstate()["on"], f"POST von einer fremden Webseite (Origin): 403, Modus bleibt aus ({c})")
        c, j = req("/api/morse", {"action": "send", "text": "SOS", "outs": ["white"], "wpm": 5})
        ok(c == 409 and not j["ok"], f"Senden ohne Modus: abgelehnt ({c}, {j.get('error')})")
        ok(req("/api/morse", {"action": "start", "minutes": 0})[0] == 409 and req("/api/morse", {"action": "start", "minutes": 31})[0] == 409
           and req("/api/morse", {"action": "start", "minutes": "x"})[0] == 409 and req("/api/morse", {"action": "more", "minutes": 5})[0] == 409,
           "Minuten 0 / 31 / «x», «länger» ohne Modus: abgelehnt")
        c, html = req("/morse")
        ok(c == 200 and b"mo-back" in html and b'href="/more"' in html, "Seite /morse für den Administrator, mit Weg zurück")
        c, more = req("/more")
        c2, more2 = req("/more", user=("Anna", "anna-pass-1"))
        ok(b'href="/morse"' in more and b'href="/morse"' not in (more2 if isinstance(more2, bytes) else b""), "Eintrag unter «Mehr» nur für den Administrator")
        print("F) PIN und Start", flush=True)
        ok(req("/api/protect", {"action": "pin", "new": PIN})[0] == 200, "PIN für «Aus» gesetzt")
        c, j = req("/api/morse", {"action": "start", "minutes": 5})
        ok(c == 403 and j.get("need_pin") and not mstate()["on"], f"Start ohne PIN: 403 «PIN nötig», Modus bleibt aus ({c})")
        c, j = req("/api/morse", {"action": "start", "minutes": 5}, pin="0000")
        ok(c == 403 and j.get("need_pin") and not mstate()["on"], "Start mit falscher PIN: 403")
        ok(req("/api/state")[1]["state"].get("arm_state") == "armed", "vorher: Schutz «Wachsam»")
        c, j = req("/api/morse", {"action": "start", "minutes": 2}, pin=PIN)
        s = mstate()
        ok(c == 200 and s["on"] and 100 < s["rest"] <= 120 and s["by"] == "admin", f"Start mit PIN: Modus läuft, endet in {s['rest']} s, gestartet von «{s['by']}»")
        pr = req("/api/protect?lang=de")[1]
        ok(pr.get("morse") and pr.get("level") == "watch", "Schutz-Zustand der Seiten: «Morse-Modus» (die Stufe in den Einstellungen bleibt «Wachsam»)")
        ok(json.load(open(os.path.join(cfg, "motionwatch_settings.json")))["cfg"].get("armed") is True, "in der Einstellungs-Datei bleibt der Schutz EIN")
        ok("Morse mode on (admin)" in log_text() and "PAUSED" in log_text(), "Protokoll: «Morse mode on (admin) … PAUSED»")
        c, j = req("/api/morse", {"action": "more", "minutes": 5})
        ok(c == 403 and j.get("need_pin"), "«länger» ohne PIN: 403")
        for _i in range(12):
            req("/api/morse", {"action": "more", "minutes": 30}, pin=PIN)
        s = mstate()
        ok(s["rest"] <= 30 * 60 and not s["more"] and req("/api/morse", {"action": "more", "minutes": 1}, pin=PIN)[0] == 409,
           f"12-mal «+30 min»: nie länger als 30 Minuten ab Start ({s['rest']} s), danach abgelehnt")
        r0 = mstate()["rest"]; time.sleep(2.5)
        for _i in range(5):
            req("/api/morse?lang=de"); req("/morse")
        ok(mstate()["rest"] < r0, "Abfragen der Seite verlängert den Modus nicht")
        print("F) Senden", flush=True)
        s = mstate()
        outs = {o["id"]: o for o in s["outs"]}
        ok(outs["white"]["wpm"] == 7 and outs["ir"]["wpm"] == 20 and outs["relay:22"]["wpm"] == 4 and outs["led"]["wpm"] == 10 and outs["beep"]["wpm"] == 25,
           "Grenzen: weiss 7, IR 20, Relais 4 (mechanisch), LED 10, Ton 25 WPM")
        c, j = req("/api/morse", {"action": "plan", "text": "SOS ä€", "outs": ["white", "ir"], "wpm": 25, "lang": "de"})
        ok(c == 200 and j["plan"]["wpm"] == 7 and j["plan"]["slow"] == "Weisses Licht" and j["plan"]["skipped"] == ["€"] and j["plan"]["shown"] == "SOS Ä",
           f"Vorschau: 25 WPM gewünscht -> 7 WPM, gebremst durch «{j['plan']['slow']}», ausgelassen {j['plan']['skipped']}")
        c, j = req("/api/morse", {"action": "plan", "text": "E", "outs": ["relay:22", "ir"], "wpm": 25})
        ok(j["plan"]["wpm"] == 4, "mechanisches Relais + IR: 4 WPM")
        req("/api/morse", {"action": "prefs", "ssr": [22]})
        c, j = req("/api/morse", {"action": "plan", "text": "E", "outs": ["relay:22", "ir"], "wpm": 25})
        ok(j["plan"]["wpm"] == 7, "als Halbleiter-Relais: 7 WPM (sichtbares Licht)")
        req("/api/morse", {"action": "prefs", "ssr": []})
        for bad in ({"text": "", "outs": ["white"], "wpm": 5}, {"text": "SOS", "outs": [], "wpm": 5}, {"text": "SOS", "outs": ["relay:99"], "wpm": 5},
                    {"text": "S" * 201, "outs": ["white"], "wpm": 5}, {"text": ["SOS"], "outs": ["white"], "wpm": 5}, {"text": "SOS", "outs": "white", "wpm": "x"},
                    {"text": "€€", "outs": ["white"], "wpm": 5}, {"text": "SOS", "outs": ["beep"], "wpm": 5}):
            c, j = req("/api/morse", dict(bad, action="send"))
            ok(c == 400 and not j["ok"] and not mstate()["tx"], f"abgelehnt: {str(bad)[:60]} -> {j.get('error')}")
        open(out_f, "w").close()
        c, j = req("/api/morse", {"action": "send", "text": "SOS ok", "outs": ["white", "ir", "relay:22"] + (["led"] if outs["led"]["ok"] else []), "wpm": 25, "lang": "de"})
        ok(c == 200 and j["plan"]["wpm"] == 4 and j["state"]["tx"] and j["state"]["tx"]["shown"] == "SOS OK",
           f"Senden auf mehreren Ausgängen zugleich: {(j.get('plan') or {}).get('wpm')} WPM (das Relais bremst) {j.get('error') or ''}")
        c2, j2 = req("/api/morse", {"action": "send", "text": "E", "outs": ["ir"], "wpm": 5})
        ok(c2 == 409, "eine zweite Sendung gleichzeitig: abgelehnt")
        ok(warte(lambda: not mstate()["tx"], (j.get("plan") or {}).get("secs", 0) + 15), "die Sendung endet von selbst")
        time.sleep(0.5)
        for g, name in ((17, "weisses Licht"), (27, "IR-Licht"), (22, "Relais"), ("led", "Status-LED")):
            txt, kurz, hz = gesendet(g)
            if g == "led" and not kanten(g):
                print("  – Status-LED: ohne PCA9685 hier nicht getastet", flush=True); continue
            ok(txt == "SOS OK" and kurz >= 0.3 * 0.8 and hz <= 2.0 * 1.15, f"{name}: getastet «{txt}», kürzeste AN-Zeit {kurz * 1000:.0f} ms, höchstens {hz:.2f} Schaltspiele/s")
            ok(kanten(g) and kanten(g)[-1][1] is False, f"{name}: nach dem Ende aus (wie vorher)")
        ok("White light ON" not in log_text("light") and "GPIO22) ON" not in log_text("GPIO22"), "kein «Licht EIN / AUS» pro Zeichen im Protokoll")
        open(out_f, "w").close()
        c, j = req("/api/morse", {"action": "send", "text": "PARIS PARIS PARIS", "outs": ["ir"], "wpm": 20})
        ok(c == 200 and j["plan"]["wpm"] == 20, "IR allein: 20 WPM")
        time.sleep(2.5)
        c, j = req("/api/morse", {"action": "tx_stop"})
        time.sleep(0.4)
        k = kanten(27)
        ok(c == 200 and not j["state"]["tx"] and k and k[-1][1] is False, "Stopp mitten in der Sendung: IR-Licht aus")
        n0 = len(k); time.sleep(1.5)
        ok(len(kanten(27)) == n0, "nach dem Stopp schaltet nichts mehr")
        per = [k[i + 2][0] - k[i][0] for i in range(0, len(k) - 2, 2)]
        ok(per and 1.0 / min(per) <= 8.34 * 1.6, f"IR bei 20 WPM: höchstens {1.0 / min(per):.1f} Schaltspiele/s (Soll 8.3; die Hardware-Schleife taktet mit 20 ms)")
        for _i in range(8):
            c, j = req("/api/morse", {"action": "send", "text": "E", "outs": ["ir"], "wpm": 20}); time.sleep(0.25); req("/api/morse", {"action": "tx_stop"})
        ok(c == 429, f"mehr als 6 Sendungen pro Minute: abgelehnt ({c})")
        print("F) Empfangen", flush=True)
        req("/api/morse", {"action": "prefs", "rx": True, "rx_live": True, "rx_hist": True, "rx_push": True, "rx_say": False})
        ok(warte(lambda: mstate()["rx"]["fps"] > 5, 20), f"der Empfänger bekommt Bilder: {mstate()['rx']['fps']} pro Sekunde, Anzeige «bis etwa {mstate()['rx']['limit']} WPM»")
        Hook.got.clear()
        ende = blinken("SOS MOVEEYE", 4)
        live = []
        ende_t = time.time() + ende + 8
        while time.time() < ende_t:
            r = mstate()["rx"]
            if r["live"]:
                live.append(r["live"])
            if r["msgs"]:
                break
            time.sleep(0.5)
        r = mstate()["rx"]
        ok(r["msgs"] and r["msgs"][0]["text"] == "SOS MOVEEYE", f"Lampe im Kamerabild, 3 bis 4 WPM: gelesen «{r['msgs'][0]['text'] if r['msgs'] else ''}»")
        ok(any(x.startswith("SOS") for x in live), f"die Zeichen erscheinen laufend ({len(live)} Zwischenstände, z. B. «{live[len(live) // 2] if live else ''}»)")
        ok(warte(lambda: any(b"SOS MOVEEYE" in g for g in Hook.got), 15), "Push mit dem Text (Webhook)")
        blob = b" ".join(Hook.got)
        ok(len(Hook.got) == 1 and b"46.95" not in blob and b"7.44" not in blob and b"maps" not in blob.lower() and b"image" not in blob.lower() and b"jpeg" not in blob.lower(),
           f"genau 1 Push, ohne Ort, ohne Bild ({len(Hook.got)})")
        def fotos():
            return [x for x in req("/api/recordings?kind=image&limit=100")[1].get("items", []) if x["name"].startswith("morse_")]
        if shutil.disk_usage(tmp).free < 500 * 1024 ** 2:               # unter 400 MB frei räumt MoveEye alte Aufnahmen weg (410)
            print("  – Bild im Verlauf nicht geprüft: weniger als 500 MB frei", flush=True)
        else:
            ok(warte(lambda: len(fotos()) >= 1, 10), "Bild im Verlauf → Aufnahmen")
            f_ = fotos()
            ok(f_ and f_[0].get("source") == "Morse" and "SOS MOVEEYE" in (f_[0].get("note") or ""), f"Notiz am Bild: Quelle «Morse», der Text ({(f_ or [{}])[0].get('note')})")
        ok("Morse received (camera" in log_text() and "SOS MOVEEYE" in log_text(), "Protokoll: «Morse received … SOS MOVEEYE»")
        ok("SABOTAGE" not in log_text("SABOTAGE") and "Pre-alarm" not in log_text("alarm") and "Low-light mode" not in log_text("Low-light"),
           "während des Modus: keine Sabotage-Meldung, kein Voralarm, kein Wechsel Tag / Nacht")
        c, jpg = req("/snapshot.jpg")
        if bilder and isinstance(jpg, bytes) and c == 200:
            os.makedirs(bilder, exist_ok=True); open(os.path.join(bilder, "morse_livebild.jpg"), "wb").write(jpg)
        ende = blinken("OK", 4, 1.0)                               # gleich danach: die zweite Push wird zurückgehalten (eine pro 20 s)
        ok(warte(lambda: len(mstate()["rx"]["msgs"]) >= 2, ende + 10) and mstate()["rx"]["msgs"][0]["text"] == "OK", "zweite Nachricht «OK» gelesen")
        time.sleep(1.5)
        ok(len(Hook.got) == 1 and mstate()["rx"]["msgs"][0]["push"] == "held", "zweite Push innerhalb von 20 s: zurückgehalten")
        print("F) Schritt 2: Ton über das Mikrofon, Gegenstelle, eigenes Licht", flush=True)

        def spielen(text, wpm, snr=15.0):
            x = ton(ns, text, wpm, snr, seed=7)
            open(ton_f + ".tmp", "wb").write(np.clip(x, -32768, 32767).astype("<i2").tobytes()); os.replace(ton_f + ".tmp", ton_f)
            return len(x) / float(TON_RATE)
        vorher = {os.path.join(d_, f) for d_, _s, fs in os.walk(tmp) for f in fs}
        n0 = len(mstate()["rx"]["msgs"])
        dauer = spielen("CQ MOVEEYE", 12)
        time.sleep(dauer + 2.0)
        ok(len(mstate()["rx"]["msgs"]) == n0 and not mstate()["rx"]["sound"]["on"], "Ton ab Werk aus: ein Morse-Ton am Mikrofon wird nicht gelesen")
        req("/api/morse", {"action": "prefs", "rx_sound": True})
        dauer = spielen("CQ MOVEEYE", 12)
        ok(warte(lambda: mstate()["rx"]["sound"]["run"], 10), "«mit dem Mikrofon» gewählt: der Empfänger bekommt Ton")
        ok(warte(lambda: len(mstate()["rx"]["msgs"]) > n0, dauer + 12) and mstate()["rx"]["msgs"][0]["text"] == "CQ MOVEEYE" and mstate()["rx"]["msgs"][0]["src"] == "sound",
           f"Ton 12 WPM am Mikrofon: gelesen «{mstate()['rx']['msgs'][0]['text']}» (Quelle {mstate()['rx']['msgs'][0]['src']})")
        ok("Morse received (sound" in log_text(), "Protokoll: «Morse received (sound …»")
        time.sleep(1.0)
        neu = {os.path.join(d_, f) for d_, _s, fs in os.walk(tmp) for f in fs} - vorher
        ok(not [f for f in neu if f.lower().endswith((".wav", ".raw", ".pcm", ".mp3", ".ogg", ".flac"))], f"kein Ton gespeichert (neue Dateien: {sorted(os.path.basename(f) for f in neu)[:6]})")
        req("/api/morse", {"action": "prefs", "rx_sound": False})
        hooks0 = len(Hook.got)
        for versuch in (1, 2, 3):                                   # (im Demo-Bild läuft manchmal etwas Helles vorbei: wie der Bediener nochmals)
            ende = blinken(ns["MORSE_TEST_TEXT"], 4, 1.5)
            if warte(lambda: (mstate()["rx"].get("peer") or {}).get("full"), ende + 14):
                break
        ok((mstate()["rx"].get("peer") or {}).get("full"),
           f"Testsignal der Gegenstelle im Bild: «gelesen» im {versuch}. Versuch ({mstate()['rx'].get('peer')}, zuletzt «{mstate()['rx']['msgs'][0]['text']}»)")
        N["peer_versuche"] = versuch
        time.sleep(1.0)
        ok(mstate()["rx"]["msgs"][0]["test"] and len(Hook.got) == hooks0, "das Testsignal steht in der Liste, löst aber keine Push aus")
        ende_t = time.time() + 75
        while True:                                                 # (höchstens 6 Sendungen pro Minute: von vorher)
            c, j = req("/api/morse", {"action": "test", "wpm": 25})
            if c != 429 or time.time() > ende_t:
                break
            time.sleep(3)
        ok(c == 200 and j["plan"]["shown"] == ns["MORSE_TEST_TEXT"] and j["plan"]["wpm"] == 20 and j["state"]["tx"]["outs"] == ["ir"], f"«Testsignal per Infrarot senden»: nur IR, 20 WPM ({c})")
        req("/api/morse", {"action": "tx_stop"})
        n1 = len(mstate()["rx"]["msgs"])
        c, j = req("/api/morse", {"action": "send", "text": "PARIS PARIS PARIS PARIS PARIS", "outs": ["ir"], "wpm": 10})
        ende = blinken("OK", 4, 0.5)
        ok(c == 200 and warte(lambda: not mstate()["tx"], 60), "eigene Sendung mit Licht läuft und endet")
        time.sleep(4.5)
        ok(len(mstate()["rx"]["msgs"]) == n1, "solange MoveEye selbst mit Licht sendet, wird eine Lampe im Bild nicht gelesen (kein eigenes Echo)")
        ende = blinken("OK", 4, 1.0)
        ok(warte(lambda: len(mstate()["rx"]["msgs"]) > n1, ende + 12) and mstate()["rx"]["msgs"][0]["text"] == "OK", "danach wird wieder gelesen")
        if browser:
            teil_g(base, bilder, blinken, lambda lg: req("/api/set", {"key": "lang", "value": lg}))
        print("F) Ende des Modus", flush=True)
        c, j = req("/api/morse", {"action": "stop"})
        ok(c == 200 and not j["state"]["on"] and not req("/api/protect")[1].get("morse"), "Beenden: Modus aus")
        ok(warte(lambda: req("/api/state")[1]["state"].get("arm_state") == "armed", 10), "Schutz wieder «Wachsam» (wie vorher)")
        ok("Morse mode off (button, admin)" in log_text(), "Protokoll: «Morse mode off (button, admin)»")
        time.sleep(14)
        ok("SABOTAGE" not in log_text("SABOTAGE"), "nach dem Ende: keine Sabotage-Meldung (der Wächter lernt neu)")
        print("F) «Strom weg» mitten im Modus", flush=True)
        req("/api/morse", {"action": "start", "minutes": 30}, pin=PIN)
        ok(mstate()["on"], "Modus läuft (30 min)")
        time.sleep(1.0)
        P["p"].send_signal(signal.SIGKILL); P["p"].wait(timeout=10)
        ok(json.load(open(os.path.join(cfg, "motionwatch_settings.json")))["cfg"].get("armed") is True, "Einstellungs-Datei nach dem harten Ende: Schutz EIN")
        start()
        ok(warte(lambda: req("/api/state")[0] == 200, 90), "neu gestartet")
        ok(warte(lambda: req("/api/state")[1]["state"].get("arm_state") == "armed", 30) and not mstate()["on"] and not req("/api/protect")[1].get("morse"),
           "nach dem Neustart: Modus aus, Schutz «Wachsam» - nichts bleibt hängen")
    finally:
        try:
            P["p"].send_signal(signal.SIGKILL); P["p"].wait(timeout=10)
        except Exception:
            pass
        logf.close()
        hook.shutdown()
        if FEHLER:
            try:
                print("  --- Ende von log.txt ---\n" + "".join(open(os.path.join(tmp, "log.txt"), errors="replace").readlines()[-25:]))
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)


def teil_g(base, bilder, blinken, sprache):
    from playwright.sync_api import sync_playwright
    print("G) Browser", flush=True)
    if bilder:
        os.makedirs(bilder, exist_ok=True)

    def shot(pg, n, **k):
        if bilder:
            pg.evaluate("() => document.querySelectorAll('#gd-card, .gd-card, #g2-ov').forEach(x => x.remove())")
            pg.screenshot(path=os.path.join(bilder, n), **k)
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for name, vp, mob, lang in (("iphone", {"width": 390, "height": 844}, True, "de"), ("pc", {"width": 1366, "height": 900}, False, "de"),
                                    ("iphone_fr", {"width": 390, "height": 844}, True, "fr"), ("iphone_it", {"width": 390, "height": 844}, True, "it"),
                                    ("iphone_rm", {"width": 390, "height": 844}, True, "rm"), ("iphone_en", {"width": 390, "height": 844}, True, "en")):
            ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                 http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','%s');localStorage.setItem('mw-theme','dark');"
                                "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"settings\"]')}catch(e){}" % lang)
            sprache(lang)                                     # eine Sprache für das Gerät (639zb): die Seite folgt der Einstellung
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            if lang != "de":                                  # die Sprache wie der Bediener wählen (langSet)
                pg.goto(base + "/more", wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
                with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                    pg.evaluate("k => { langSet(k); }", lang)
                pg.wait_for_timeout(800)
            pg.goto(base + "/morse", wait_until="domcontentloaded")
            pg.wait_for_selector("#mo-outs .mo-o", timeout=20000)
            pg.wait_for_selector("#mo-st.on", timeout=10000)
            titel = {"de": "Morse-Modus", "en": "Morse mode", "fr": "Mode morse", "it": "Modalità Morse", "rm": "Modus da morse"}[lang]
            ok(titel in pg.inner_text("h2") and pg.locator("#mo-st .mo-cd").count() == 1, f"{name}: Seite «{titel}», Modus läuft, Restzeit sichtbar")
            ok(pg.locator("#mo-back").is_visible() and pg.get_attribute("#mo-back", "href") == "/more", f"{name}: Weg zurück sichtbar")
            pg.fill("#mo-text", "Grüße <script>alert(1)</script> €")
            pg.locator("#mo-outs input[data-o='white']").check()
            pg.wait_for_function("() => document.getElementById('mo-plan').textContent.length > 5", timeout=8000)
            pl = pg.inner_text("#mo-plan")
            ok("WPM" in pl and "€" in pl and pg.locator("#mo-plan script").count() == 0 and not pg.locator("#mo-flash").is_hidden(),
               f"{name}: Vorschau als Text, Hinweis Blinklicht: {pl[:70]!r}")
            pg.evaluate("() => { document.getElementById('mo-peer').open = true; }")
            ok(pg.locator("#mo-chk input[data-k='rx_sound']").count() == 1 and pg.locator("#mo-peer-go").is_visible() and pg.locator("#mo-peer-how li").count() == 4,
               f"{name}: Schalter «mit dem Mikrofon» und Karte «Gegenstelle testen»")
            sw = pg.evaluate("() => document.documentElement.scrollWidth")
            ok(sw <= vp["width"] + 1, f"{name}: kein waagrechtes Scrollen ({sw} px)")
            raus = pg.evaluate("""() => Array.from(document.querySelectorAll('main button, main select, main label, main .mo-o, main .mo-live, main .mo-hint, main .mo-warn'))
              .filter(e => e.offsetParent && (e.getBoundingClientRect().right > innerWidth + 1 || e.scrollWidth > e.clientWidth + 2)).map(e => (e.id || e.className) + ':' + e.textContent.slice(0, 30))""")
            ok(not raus, f"{name}: nichts ragt aus Knopf / Feld {raus[:3]}")
            eng = pg.evaluate("""() => Array.from(document.querySelectorAll('main *')).filter(e => e.children.length === 0 && e.id !== 'mo-text'
              && /\\b(the|Morse mode|Send|Receive|Start the|flashes|pictures)\\b/.test(e.textContent)).map(e => e.textContent.slice(0, 40))""")
            ok(lang == "en" or not eng, f"{name}: keine englisch gebliebenen Texte {eng[:3]}")
            if lang == "de":
                ok("ß" not in pg.evaluate("() => { const m = document.querySelector('main').cloneNode(true); m.querySelector('#mo-plan').remove(); return m.innerText; }"),
                   f"{name}: kein «ß» in den deutschen Texten (ausser im eingegebenen Text)")
            shot(pg, f"morse_{name}.png", full_page=True)
            if name == "iphone":
                ende = blinken("HALLO", 4, 0.5)
                try:
                    pg.wait_for_function("() => Array.from(document.querySelectorAll('#mo-msgs b')).some(b => b.textContent === 'HALLO')", timeout=int((ende + 40) * 1000))   # Luft für langsame Rechner
                    da = True
                except Exception:
                    da = False
                if not da:
                    st_ = pg.evaluate("() => fetch('/api/morse?lang=de').then(r => r.json()).then(j => j.state)")
                    print("    Zustand:", json.dumps({k: st_.get(k) for k in ("on", "rest", "tx")}), json.dumps({k: (st_.get("rx") or {}).get(k) for k in ("on", "fps", "limit", "live", "fast", "blink", "msgs")}, ensure_ascii=False)[:900], flush=True)
                ok(da, "iphone: die empfangene Nachricht «HALLO» erscheint in der Liste")
                shot(pg, "morse_iphone_empfangen.png", full_page=True)
                pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_timeout(4000)
                ok(pg.evaluate("() => document.body.innerText.includes('Morse-Modus')"), "iphone: die Hauptseite zeigt «Morse-Modus» als Schutz-Zustand")
                shot(pg, "morse_iphone_live.png")
            ok(not errs, f"{name}: keine JavaScript-Fehler {errs}")
            ctx.close()
        sprache("de")
        br.close()


# ---------------------------------------------------------------------------------------------------------------------- H
WRAP_HW = r"""
import json, os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = '''
def _mt_note(name_, lit_):                                # what the «hardware» holds now (the file survives kill -9, like a real chip)
    try:
        p_ = os.environ["MW_MORSE_PINS"]
        try:
            d_ = json.load(open(p_))
        except (OSError, ValueError):
            d_ = {}
        if d_.get(name_) != lit_:
            d_[name_] = lit_
            open(p_ + ".tmp", "w").write(json.dumps(d_)); os.replace(p_ + ".tmp", p_)
            open(os.environ["MW_MORSE_OUT"], "a").write(json.dumps([time.time(), name_, lit_]) + chr(10))
    except Exception:
        pass
class _MtPca:                                             # a PCA9685 without a bus: the channels keep their state in the file
    def __init__(self, addr, bus=1, freq=50.0):
        self.addr, self.freq, self.pre = addr, float(freq), 121
    def _w(self, reg, val):
        pass
    def _r(self, reg):
        return 0
    def healthy(self):
        return True
    def _set(self, ch, on, off):
        _mt_note("pca:%d" % ch, bool(on & 0x1000) or (not (off & 0x1000) and off > 0))
    def pulse_us(self, ch, us):
        pass
    def switch(self, ch, on):
        self._set(ch, 0x1000, 0) if on else self._set(ch, 0, 0x1000)
    def close(self):
        pass
PCA9685 = _MtPca
pca_present = lambda addr, bus=1: True
_mt_write = Hardware._write
def _mt_hw_write(self, gpio, on, al):                     # a GPIO the hardware loop writes (relay, light on a GPIO)
    _mt_write(self, gpio, on, al)
    _mt_note("gpio:%d" % gpio, bool(on))
Hardware._write = _mt_hw_write
'''
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
"""


def teil_h(datei):
    print("H) Nachgebaute Hardware (PCA9685 + GPIO): hartes Ende mitten in einem Strich, Neustart", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_morse_h_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    pins_f, out_f = os.path.join(tmp, "pins.json"), os.path.join(tmp, "out.txt")
    st = {"source": "demo", "thermal_source": "", "thermal_on": False, "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False,
          "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "news_popup": False, "tours_auto": False, "notify_on": False,
          "servo_driver": "pca9685", "mover_mode": "off", "light_white_out": "gpio:17", "light_ir_out": "pca:3", "led_on": True,
          "armed": False, "ai_enabled": False, "eco_on": False, "record_dir": os.path.join(tmp, "aufnahmen")}
    json.dump({"cfg": st, "relays": [{"name": "Scheinwerfer", "gpio": 22, "mode": "off", "trigger": "person", "hold": 5.0, "active_low": False}]},
              open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP_HW)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = dict(os.environ, MW_MORSE_PINS=pins_f, MW_MORSE_OUT=out_f)
    P = {"p": None, "t": 0.0}

    def start():
        P["t"] = time.time()
        P["p"] = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                                   "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None):
        h = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode(), "Content-Type": "application/json"}
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
        try:
            with op.open(r, timeout=60) as x:
                return x.status, json.loads(x.read())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            except ValueError:
                return e.code, {}
        except OSError:
            return 0, {}

    def pins():
        try:
            return json.load(open(pins_f))
        except (OSError, ValueError):
            return {}

    def warte(was, s=30.0, schritt=0.3):
        ende = time.time() + s
        while time.time() < ende:
            try:
                if was():
                    return True
            except Exception:
                pass
            time.sleep(schritt)
        return False

    def kanten(name, ab=0.0):
        return [(t, on) for t, n, on in (json.loads(ln) for ln in open(out_f)) if n == name and t >= ab] if os.path.exists(out_f) else []
    AUS = ("gpio:17", "gpio:22", "pca:3", "pca:7")                    # weiss, Relais, IR-Licht, Status-LED (Kanal Blau: nur beim Morsen an)
    try:
        start()
        ok(warte(lambda: req("/api/state")[0] == 200, 90), "MoveEye läuft mit nachgebautem PCA9685")
        ok(warte(lambda: all(k in pins() for k in ("pca:3", "pca:5", "pca:6", "pca:7")), 20) and not pins().get("pca:3") and not pins().get("pca:7"),
           f"Start: IR-Kanal aus, Status-LED in der Farbe des Zustands {dict((k, v) for k, v in pins().items() if k.startswith('pca'))}")
        c, j = req("/api/morse", {"action": "start", "minutes": 5})
        ok(c == 200 and j["state"]["on"], "Morse-Modus läuft")
        outs = {o["id"]: o for o in j["state"]["outs"]}
        ok(outs["led"]["ok"] and outs["ir"]["ok"], "Status-LED und IR-Licht (PCA9685) sind wählbar")
        t1 = time.time()
        c, j = req("/api/morse", {"action": "send", "text": "E T E T", "outs": ["led", "ir"], "wpm": 10})
        ok(c == 200 and j["plan"]["wpm"] == 10, "Status-LED + IR: 10 WPM (die LED bremst)")
        ok(warte(lambda: not req("/api/morse")[1]["state"]["tx"], 30), "Sendung fertig")
        time.sleep(0.3)
        for name, was in (("pca:7", "Status-LED"), ("pca:3", "IR-Licht am PCA9685")):
            k = kanten(name, t1)
            while k and not k[0][1]:
                k.pop(0)
            ons = [k[i + 1][0] - k[i][0] for i in range(0, len(k) - 1, 2)]
            ok(len(ons) == 4 and ons[0] < 0.2 < ons[1] and ons[2] < 0.2 < ons[3] and k[-1][1] is False,
               f"{was}: getastet kurz / lang / kurz / lang ({' '.join('%.0f' % (x * 1000) for x in ons)} ms), danach aus")
        ok(pins().get("pca:5") or pins().get("pca:6"), "Status-LED nach der Sendung wieder in der Farbe des Zustands")
        c, j = req("/api/morse", {"action": "send", "text": "TTTTTT", "outs": ["white", "ir", "relay:22", "led"], "wpm": 4})
        ok(c == 200, "lange Striche auf allen vier Ausgängen")
        ok(warte(lambda: all(pins().get(k) for k in AUS), 15, 0.02), "mitten im Strich: alle vier an")
        P["p"].send_signal(signal.SIGKILL); P["p"].wait(timeout=10)
        ok(all(pins().get(k) for k in AUS), f"«Programm abgestürzt» (kill -9): die Ausgänge stehen noch AN {[k for k in AUS if pins().get(k)]}")
        start()
        heil = warte(lambda: not any(pins().get(k) for k in AUS), 90, 0.05)
        dt = time.time() - P["t"]
        ok(heil, f"Neustart: alle vier wieder aus, {dt:.1f} s nach dem Programmstart {pins()}")
        N["heil"] = dt
        ok(warte(lambda: req("/api/state")[0] == 200, 90) and not req("/api/morse")[1]["state"]["on"], "nach dem Neustart: Modus aus")
        time.sleep(2.0)
        ok(not any(pins().get(k) for k in AUS) and (pins().get("pca:5") or pins().get("pca:6")), "und es bleibt so (Status-LED zeigt wieder den Zustand)")
    finally:
        try:
            P["p"].send_signal(signal.SIGKILL); P["p"].wait(timeout=10)
        except Exception:
            pass
        logf.close()
        if FEHLER:
            try:
                print("  --- Ende von log.txt ---\n" + "".join(open(os.path.join(tmp, "log.txt"), errors="replace").readlines()[-25:]))
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- I
TON_RATE = 16000


def ton(ns, text, wpm, snr=20.0, f=660.0, hand=0.0, seed=1, pfeif=False, vor=1.0, fw=0, funk="", stoer="", dauer=0.0):
    """synthetischer Ton: der Text als getasteter Ton (oder Pfiff) mit Rauschen. snr = Ton zu Rauschen im Band 300-3000 Hz (dB).
    funk: "" = direkt, "ton" = über ein FM-Sprechfunkgerät, Träger bleibt, der Ton wird getastet, "traeger" = der Träger wird
    getastet (die Rauschsperre schneidet den Anfang ab und rauscht am Ende nach). stoer: "dauerton" / "pieper" daneben."""
    rng = np.random.default_rng(seed); rnd = random.Random(seed)
    tl = ns["morse_timeline"](ns["morse_encode"](text)[0], wpm, fw) if text else []
    zeiten, ende = zeiten_aus(tl, vor, hand, rnd)
    u = ns["morse_unit"](fw or wpm)
    n = int(max(dauer, ende + max(4.5, 17 * u) + 1.0) * TON_RATE)
    t = np.arange(n) / TON_RATE
    env = np.zeros(n, np.float32)
    for a, b in zeiten:
        env[int(a * TON_RATE):int(b * TON_RATE)] = 1.0
    k = int(0.004 * TON_RATE)
    envs = np.convolve(env, np.ones(k) / k, mode="same")
    A = 3000.0
    if pfeif:                                                 # ein Pfiff: die Tonhöhe wandert, die Lautstärke schwankt, ein Oberton
        fr = f * (1.0 + 0.04 * np.sin(2 * np.pi * 0.7 * t + 1.0) + 0.02 * np.sin(2 * np.pi * 3.1 * t))
        ph = 2 * np.pi * np.cumsum(fr) / TON_RATE
        x = (np.sin(ph) + 0.15 * np.sin(2 * ph)) * envs * (1.0 + 0.3 * np.sin(2 * np.pi * 1.3 * t))
    else:
        x = np.sin(2 * np.pi * f * t) * envs
    x = x * A
    if funk:
        x = funkkanal(x, env, funk, rng, A)
    if stoer == "dauerton":
        x = x + 0.8 * A * np.sin(2 * np.pi * 1850.0 * t)
    elif stoer == "pieper":                                   # ein Rückfahr-Warner: 1250 Hz, 2 × pro Sekunde
        x = x + A * np.sin(2 * np.pi * 1250.0 * t) * ((t * 2.0) % 1.0 < 0.5)
    rausch = rng.normal(0, 1, n) * math.sqrt((A * A / 2.0) / (10 ** (snr / 10.0)) * 8000.0 / 2700.0)
    return (x + rausch).astype(np.float32)


def funkkanal(x, env, art, rng, A):
    """ein FM-Handfunkgerät, vereinfacht: Bandpass 300-3000 Hz, Regelung der Lautstärke (hebt in den Pausen das Rauschen an),
    bei getastetem Träger die Rauschsperre: 40 ms zu spät offen, 120 ms Rauschen nach dem Ende, dazwischen still."""
    from scipy import signal as sg
    n = x.size
    sos = sg.butter(4, [300.0, 3000.0], btype="band", fs=TON_RATE, output="sos")
    kanal = rng.normal(0, 1, n) * A * 0.03                  # Rauschen des Empfängers bei gutem Signal
    if art == "traeger":
        auf = np.zeros(n, np.float32)
        d_auf, d_zu = int(0.040 * TON_RATE), int(0.120 * TON_RATE)
        kanten = np.flatnonzero(np.diff(np.concatenate(([0.0], env, [0.0]))))
        y = np.zeros(n, np.float64)
        for a, b in zip(kanten[0::2], kanten[1::2]):
            auf[min(n, a + d_auf):b] = 1.0
            y[b:min(n, b + d_zu)] += rng.normal(0, 1, max(0, min(n, b + d_zu) - b)) * A * 0.5      # der Rauschschwanz
        y += (x + kanal) * auf
    else:
        y = x + kanal
    y = sg.sosfilt(sos, y)
    blk = int(0.005 * TON_RATE)                               # Regelung: schnell leiser, langsam (0.5 s) lauter
    g, out = 1.0, np.empty(n, np.float64)
    ziel = A * 0.7
    for i in range(0, n, blk):
        seg = y[i:i + blk]
        r = float(np.sqrt(np.mean(seg * seg))) + 1.0
        want = min(20.0, ziel / r)
        g = want if want < g else g + (want - g) * (0.005 / 0.5)
        out[i:i + blk] = seg * g
    return out if art != "traeger" else np.where(np.abs(out) > 0, out, 0.0)


def hoeren(ns, x):
    got = []
    rx = ns["MorseAudio"](lambda txt, info: got.append(txt))
    live = 0
    for i in range(0, len(x), 1600):
        lv = rx.feed(x[i:i + 1600])
        if lv and lv["valid"]:
            live += 1
    return " ".join(got), rx, live


def zelle_ton(ns, wpm, snr, n=2, **kw):
    s = 0.0
    for seed in range(1, n + 1):
        got, _rx, _l = hoeren(ns, ton(ns, SOLL, wpm, snr, seed=seed * 5 + int(wpm), **kw))
        s += cer(SOLL, got)
    return s / n


def teil_i(ns):
    print("I) Ton: synthetisches Mikrofon -> MorseAudio", flush=True)
    for wpm, snr in ((5, 20), (12, 10), (20, 6)):
        e = zelle_ton(ns, wpm, snr)
        ok(e <= 0.02, f"Ton 660 Hz, {wpm} WPM, {snr} dB über dem Rauschen: Zeichenfehler {e * 100:.0f} %")
    e = zelle_ton(ns, 8, 10, pfeif=True, f=1500.0)
    ok(e <= 0.05, f"Pfiff (Tonhöhe wandert ±6 %, Lautstärke schwankt), 8 WPM: Zeichenfehler {e * 100:.0f} %")
    e = zelle_ton(ns, 8, 10, hand=0.3)
    ok(e <= 0.05, f"Handtastung ±30 %, 8 WPM: Zeichenfehler {e * 100:.0f} %")
    e = zelle_ton(ns, 12, 10, funk="ton", f=800.0)
    ok(e <= 0.03, f"über das Funkgerät (Träger bleibt, Ton getastet), 12 WPM: Zeichenfehler {e * 100:.0f} %")
    e = zelle_ton(ns, 8, 10, funk="traeger", f=800.0)
    ok(e <= 0.05, f"über das Funkgerät (Träger getastet, Rauschsperre), 8 WPM: Zeichenfehler {e * 100:.0f} %")
    e = zelle_ton(ns, 10, 10, stoer="dauerton")
    ok(e <= 0.03, f"mit einem Dauerton (1850 Hz) daneben: Zeichenfehler {e * 100:.0f} %")
    e = zelle_ton(ns, 10, 10, stoer="pieper")
    ok(e <= 0.03, f"mit einem Pieper (1250 Hz, 2 × pro Sekunde) daneben: Zeichenfehler {e * 100:.0f} %")
    got, rx, live = hoeren(ns, ton(ns, "", 5, 10, stoer="pieper", seed=3, dauer=40.0))
    ok(not got and not live and rx.stats["periodic"] >= 1, f"Pieper allein, 40 s: kein Text, als gleichmässig erkannt ({rx.stats['periodic']}×)")
    got, rx, live = hoeren(ns, ton(ns, "", 5, 10, stoer="dauerton", seed=4, dauer=20.0))
    ok(not got and not live and rx.key is None, "Dauerton allein: kein Text, keine Spur")
    rng = np.random.default_rng(9)
    got, rx, live = hoeren(ns, (rng.normal(0, 1, TON_RATE * 30) * 4000 * (1 + np.sin(np.arange(TON_RATE * 30) / 900.0))).astype(np.float32))
    ok(not got, f"30 s Rauschen, das an- und abschwillt (Wind): kein Text ({rx.stats['dropped']} verworfen)")
    ok(rx.stats["ms"] < 20.0, f"Rechenzeit {rx.stats['ms']:.2f} ms pro 0.1 s Ton (dieser Rechner)")
    N["ton_ms"] = rx.stats["ms"]
    # Rundlauf: der Ton, den MoveEye selbst spielt (morse_beep_chunks, 22050 Hz) -> wie das Mikrofon ihn hört (16 kHz) -> MorseAudio
    if "morse_beep_chunks" in ns:
        from scipy import signal as sg
        tl = ns["morse_timeline"](ns["morse_encode"]("MOVEEYE <SOS> ÄÖÜ 73")[0], 15)
        y = np.concatenate(list(ns["morse_beep_chunks"](tl, 22050, 0.6)) + [np.zeros(22050 * 5, np.float32)])
        x = sg.resample_poly(y, 320, 441).astype(np.float32) * 2500.0
        x += np.random.default_rng(2).normal(0, 300, x.size).astype(np.float32)
        got, rx, live = hoeren(ns, x)
        ok(got == "MOVEEYE <SOS> ÄÖÜ 73" and abs(rx.stats["hz"] - 660) <= 70, f"Rundlauf eigener Ton (15 WPM) -> «{got}», Ton bei {rx.stats['hz']} Hz")
    # feindliche Eingabe
    rnd = random.Random(5)
    rx = ns["MorseAudio"](None)
    erlaubt = set("".join(ns["MORSE_DECODE"].values())) | set(" " + ns["MORSE_UNKNOWN"])
    heil, fremd = True, False
    try:
        t = np.arange(1600) / TON_RATE
        for i in range(3000):
            art = rnd.randrange(6)
            if art == 0:
                x = rng.normal(0, rnd.choice((1, 100, 30000)), rnd.choice((0, 1, 7, 1600, 5000)))
            elif art == 1:
                x = np.sin(2 * np.pi * rnd.choice((440, 660, 1000, 2500, 7000)) * t) * 8000 * (rnd.random() < 0.5)
            elif art == 2:
                x = np.full(1600, rnd.choice((0.0, 32767.0, -32768.0)))
            elif art == 3:
                x = np.sin(2 * np.pi * 900 * t) * 8000 * (np.arange(1600) % rnd.choice((97, 400, 801)) < 200)
            elif art == 4:
                x = np.array([float("nan"), float("inf")] * 50)
            else:
                x = rng.integers(-32768, 32767, 1600).astype(np.int16)
            lv = rx.feed(x)
            if lv and not set(lv["text"]) <= erlaubt:
                fremd = True
        rx.feed(np.zeros(TON_RATE * 60, np.float32))
    except Exception as e:
        heil = False
        print("    ", type(e).__name__, e)
    ok(heil and not fremd and rx.hist.shape[0] == rx.N and rx.tail.size <= rx.WIN and len(rx.ignore) <= 8 and (rx.key is None or len(rx.key.ons) <= rx.key.EL_MAX),
       f"3000 Stücke Unsinn (Rauschen, Vollausschlag, NaN, leere / riesige Stücke, zerhackte Töne): kein Fehler, Speicher fest ({rx.hist.nbytes // 1024} KB)")


def messen_ton(ns, pfad=None, n=2):
    zeilen = []
    out = zeilen.append
    out("# Morse-Empfang mit Ton: gemessene Grenzen (synthetisches Mikrofon)")
    out("")
    out("Erzeugt mit `python3 werkzeuge/morse_test.py --quelle --messen-ton --tabelle docs/Morse_Messung_Ton.md`. Text «%s», %d Läufe pro Feld." % (SOLL, n))
    out("Ton 660 Hz (der Ton von MoveEye) als 16-kHz-Signal, weisses Rauschen. «dB» = Ton zu Rauschen im Band 300–3000 Hz.")
    out("Zahl = Zeichenfehler in % (0 = alles richtig, 100 = nichts gelesen).")
    out("")
    out("**Nicht gemessen: echtes Mikrofon, echter Raum (Hall), echter Wind, echte Stimmen, echtes Funkgerät.**")
    ws = (5, 8, 12, 15, 20, 25, 30)
    snrs = (20, 10, 6, 3, 0, -3, -6)
    t0 = time.time()

    def tab(titel, kw, snrs_=snrs):
        out(""); out("## " + titel); out("")
        out("| Ton zu Rauschen | " + " | ".join("%d WPM" % w for w in ws) + " |")
        out("|---|" + "---|" * len(ws))
        res = {}
        for s in snrs_:
            row = [zelle_ton(ns, w, s, n=n, **dict(kw)) for w in ws]
            res[s] = row
            out("| %+d dB | " % s + " | ".join("%d" % round(e * 100) for e in row) + " |")
            print("   ", zeilen[-1], f"({time.time() - t0:.0f} s)", flush=True)
        return res
    direkt = tab("Direkt (Ton nahe am Mikrofon)", {})
    tab("Pfiff (1500 Hz, Tonhöhe wandert ±6 %, Lautstärke schwankt ±30 %)", dict(pfeif=True, f=1500.0), (20, 10, 6, 3, 0))
    tab("Handtastung ±30 %", dict(hand=0.3), (20, 10, 6, 3))
    funk1 = tab("Über ein FM-Handfunkgerät, Träger bleibt, der Ton (800 Hz) wird getastet", dict(funk="ton", f=800.0), (20, 10, 6, 3, 0))
    funk2 = tab("Über ein FM-Handfunkgerät, der Träger wird getastet (Rauschsperre: 40 ms zu spät offen, 120 ms Rauschschwanz)", dict(funk="traeger", f=800.0), (20, 10, 6, 3, 0))
    tab("Mit einem Pieper daneben (1250 Hz, 2 × pro Sekunde)", dict(stoer="pieper"), (20, 10, 6))
    out("")
    out("Funkkanal im Test: Bandpass 300–3000 Hz, die Lautstärke-Regelung hebt in den Pausen das Rauschen an, etwas Empfänger-Rauschen.")
    out("Bei getastetem Träger fehlen jedem Zeichen-Element die ersten 40 ms: bei 15 WPM ist ein dit nur 80 ms lang - darum ist dort früher Schluss.")
    out("")
    out("## Daraus: die Grenze für die Anzeige")
    out("")

    def bis(res, s):
        best = 0
        for w, e in zip(ws, res[s]):
            if e > 0.02:
                break
            best = w
        return best
    out("| | liest fehlerfrei bis |")
    out("|---|---|")
    out("| direkt, +6 dB | %d WPM |" % bis(direkt, 6))
    out("| direkt, 0 dB | %d WPM |" % bis(direkt, 0))
    out("| Funkgerät, Ton getastet, +6 dB | %d WPM |" % bis(funk1, 6))
    out("| Funkgerät, Träger getastet, +6 dB | %d WPM |" % bis(funk2, 6))
    passt = bis(direkt, 6) >= TON_WPM and bis(funk1, 6) >= TON_WPM
    out("")
    out("Die Seite verspricht «liest bis etwa **%d WPM**», wenn der Ton deutlich lauter ist als die Umgebung (ab etwa +6 dB). " % TON_WPM
        + ("Die Messung hält das ein (direkt und über das Funkgerät mit getastetem Ton)." if passt else "ACHTUNG: die Messung hält das NICHT ein."))
    out("Mit getastetem Träger geht es langsamer (siehe Tabelle): Seite und Hilfe nennen dafür «nur bis etwa 12 WPM» (gemessen, nicht mit einem echten Funkgerät).")
    txt = "\n".join(zeilen) + "\n"
    if pfad:
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)
    return passt


TON_WPM = 20            # die Grenze der Seite für Ton (MORSE_SOUND_WPM)


def messen_ir(ns, pfad=None, n=2):
    """IR zwischen zwei MoveEye: das IR-Licht der Gegenstelle ist nachts ein heller Punkt; das eigene IR-Licht hellt das Bild auf"""
    zeilen = []
    out = zeilen.append
    out("# Morse mit Infrarot zwischen zwei MoveEye: gemessen (synthetische Kamera) und gerechnet")
    out("")
    out("Erzeugt mit `python3 werkzeuge/morse_test.py --quelle --messen-ir --tabelle docs/Morse_Messung_IR.md`. Text «%s», %d Läufe pro Feld." % (SOLL, n))
    out("Nacht, das eigene IR-Licht ist an (Hintergrund 45 statt 25, Rauschen σ 5), die Gegenstelle ist ein Punkt, der überstrahlt.")
    out("Zahl = Zeichenfehler in %.")
    out("")
    out("**Nicht gemessen: zwei echte Geräte, echte IR-LEDs, echte Entfernung, Regen / Nebel, die Bildrate der Pi-Kamera in der Nacht.**")
    ws = (3, 4, 5, 6, 8, 10, 12, 15, 20)
    for gr, name in ((0.4, "Punkt (weit weg, Radius 0.4 Pixel)"), (1.5, "klein (Radius 1.5 Pixel)"), (6.0, "nah, überstrahlt (Radius 6 Pixel)")):
        out(""); out("## Gegenstelle: " + name); out("")
        out("| Bilder/s | " + " | ".join("%d WPM" % w for w in ws) + " | Anzeige 0.4 × Bilder/s |")
        out("|---|" + "---|" * (len(ws) + 1))
        for fps in (8, 10, 15, 20, 30):
            row = ["%d" % round(zelle(ns, fps, w, gr, n=n, hg=45.0, hell=600.0, rausch=5.0, wandern=0.5) * 100) for w in ws]
            out("| %d | " % fps + " | ".join(row) + " | %d |" % int(GRENZE_K * fps))
            print("   ", zeilen[-1], flush=True)
    out("")
    out("## Entfernung (gerechnet, nicht gemessen)")
    out("")
    out("Das IR-Licht der Gegenstelle direkt zu sehen ist viel heller als eine davon beleuchtete Szene: sein Licht fällt auf einen")
    out("Bildpunkt (Winkel eines Bildpunkts bei 66° Bildwinkel und 1280 Bildpunkten: 0.9 mrad, Raumwinkel 8 × 10⁻⁷ sr), während eine")
    out("matte Fläche (30 % Rückstrahlung) das Licht in den ganzen Halbraum streut. Verhältnis direkt (Abstand D) zu beleuchteter")
    out("Fläche (Abstand d): (d / D)² × π / (0.3 × 8 × 10⁻⁷) ≈ (d / D)² × 1.3 × 10⁷.")
    out("Reicht das IR-Licht, um eine Szene in d = 5 m gut auszuleuchten, ist es als Punkt rechnerisch noch in mehreren Kilometern")
    out("so hell - die Helligkeit begrenzt die Strecke also nicht. Es begrenzen: die freie Sicht, der Abstrahlwinkel der LEDs")
    out("(beide müssen im Lichtkegel UND im Bild des anderen sein), Dunst, und dass der Punkt mindestens ~50 Graustufen über dem")
    out("Hintergrund liegt (nachts erfüllt, am Tag nicht). Ehrliche Erwartung ohne Messung: einige zehn bis wenige hundert Meter.")
    out("")
    out("## Tempo")
    out("")
    out("Senden kann das IR-Licht bis 20 WPM; lesen kann die Gegenstelle bis etwa 0.4 × ihre Bilder pro Sekunde:")
    out("bei 15 Bildern/s 6 WPM, bei 30 Bildern/s 12 WPM. Massgebend ist die Zahl auf der Seite der Gegenstelle.")
    txt = "\n".join(zeilen) + "\n"
    if pfad:
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)
    return True


# ---------------------------------------------------------------------------------------------------------------- messen
FPS_LISTE = (5, 8, 10, 15, 20, 30)
WPM_LISTE = (3, 4, 5, 6, 8, 10, 12, 15, 18, 20)
GR_LISTE = (0.6, 1.5, 4.0)
GRENZE_K = 0.4          # WPM pro (Bild/s) für die Anzeige: ein dit ist dann 3 Bilder lang (gemessen geht es bis etwa 1.8 Bilder)
LICHT = (("Nacht (Hintergrund 25, Lampe +400)", dict(hg=25.0, hell=400.0)),
         ("Dämmerung (Hintergrund 80, Lampe +200)", dict(hg=80.0, hell=200.0)),
         ("Tag (Hintergrund 140, Lampe +110)", dict(hg=140.0, hell=110.0, rausch=4.0)),
         ("Tag, schwache Lampe (Hintergrund 140, Lampe +60)", dict(hg=140.0, hell=60.0, rausch=4.0)))


def grenze_wpm(fps):
    """die Grenze für die Anzeige: bis zu diesem Tempo liest die Kamera bei dieser Bildrate sicher"""
    return GRENZE_K * fps


def messen(ns, pfad=None, n=2):
    zeilen = []
    out = zeilen.append
    out("# Morse-Empfang: gemessene Grenzen (synthetische Kamera)")
    out("")
    out("Erzeugt mit `python3 werkzeuge/morse_test.py --quelle --messen --tabelle docs/Morse_Messung.md`. Text «%s», %d Läufe pro Feld." % (SOLL, n))
    out("Kamera: 640 × 360 (Arbeitsbild von MoveEye), Rauschen σ 3, Belichtung = halbe Bildperiode, die Bildzeit kommt bis 10 % der")
    out("Bildperiode später an, die Kamera regelt die Helligkeit nach, die Optik verschmiert um 0.7 Pixel, der Fleck wandert ±3 Pixel.")
    out("Zahl = Zeichenfehler in % (0 = alles richtig, 100 = nichts gelesen).")
    out("")
    out("**Nicht gemessen: echte Kamera, echte Lampe, echte Entfernung, echtes Tageslicht, die Bildrate von MoveEye auf dem Pi.**")
    t0 = time.time()
    beste = {}
    for gr in GR_LISTE:
        out("")
        out("## Bildrate × Tempo, Fleck Radius %g Pixel, Nacht" % gr)
        out("")
        out("(Radius im Arbeitsbild 640 breit; im Kamerabild 1280 das Doppelte)")
        out("")
        out("| Bilder/s | " + " | ".join("%d WPM" % w for w in WPM_LISTE) + " | liest bis |")
        out("|---|" + "---|" * (len(WPM_LISTE) + 1))
        for fps in FPS_LISTE:
            row, best = [], 0
            hole = False
            for w in WPM_LISTE:
                e = zelle(ns, fps, w, gr, n=n)
                row.append("%d" % round(e * 100))
                if e <= 0.02 and not hole:
                    best = w
                else:
                    hole = True
            beste[(gr, fps)] = best
            out("| %d | " % fps + " | ".join(row) + " | **%d WPM** |" % best)
            print("   ", zeilen[-1], f"({time.time() - t0:.0f} s)", flush=True)
    out("")
    out("## Fleckgrösse × Licht (15 Bilder/s, 5 WPM)")
    out("")
    gl = (0.4, 0.6, 1.0, 1.5, 2.5, 4.0, 10.0)
    out("| Licht | " + " | ".join("Radius %g" % g for g in gl) + " |")
    out("|---|" + "---|" * len(gl))
    for name, kw in LICHT:
        out("| %s | " % name + " | ".join("%d" % round(zelle(ns, 15, 5, g, n=n, **dict(kw)) * 100) for g in gl) + " |")
        print("   ", zeilen[-1], flush=True)
    out("")
    out("Ein kleiner Fleck ist nach der Optik dunkler: entscheidend ist, dass sein hellster Bildpunkt rund 50 Graustufen")
    out("(von 255) über dem Hintergrund liegt. Nachts reicht dafür ein Punkt, am Tag braucht es eine helle oder nahe Lampe.")
    out("")
    out("## Erschwerte Bedingungen (15 Bilder/s, Fleck 3 Pixel, Nacht)")
    out("")
    ws = (3, 5, 6, 8, 10)
    out("| Bedingung | " + " | ".join("%d WPM" % w for w in ws) + " |")
    out("|---|" + "---|" * len(ws))
    for name, kw in (("wie oben", {}),
                     ("Handtastung ±20 %", dict(hand=0.2)),
                     ("Handtastung ±30 %", dict(hand=0.3)),
                     ("Handtastung ±40 %", dict(hand=0.4)),
                     ("Hand wandert ±14 Pixel", dict(wandern=14.0)),
                     ("Hand wandert ±25 Pixel", dict(wandern=25.0)),
                     ("jemand geht knapp unter der Lampe durch", dict(laeufer=True)),
                     ("Hand wandert ±40 Pixel", dict(wandern=40.0)),
                     ("5 % verlorene Bilder, Bildzeit bis 25 % später", dict(verlust=0.05, zittern=0.25)),
                     ("15 % verlorene Bilder, Bildzeit bis 50 % später", dict(verlust=0.15, zittern=0.5)),
                     ("kurze Belichtung (1/10 Bildperiode)", dict(belichtung=0.1)),
                     ("lange Belichtung (ganze Bildperiode)", dict(belichtung=1.0)),
                     ("Dauerlicht + Blinker 1.5 Hz daneben", dict(dauerlicht=True, blinker=True)),
                     ("starkes Rauschen σ 10", dict(rausch=10.0)),
                     ("Farnsworth (Pausen wie 3 WPM)", dict(farnsworth=3))):
        row = ["%d" % round(zelle(ns, 15, w, 3.0, n=max(n, 3), **dict(kw)) * 100) for w in ws]
        out("| %s | " % name + " | ".join(row) + " |")
        print("   ", zeilen[-1], flush=True)
    out("")
    out("## Daraus: die Grenze für die Anzeige")
    out("")
    out("| Bilder/s | " + " | ".join("Fleck %g" % g for g in GR_LISTE) + " | Anzeige: %.1f × Bilder/s |" % GRENZE_K)
    out("|---|" + "---|" * (len(GR_LISTE) + 1))
    passt = True
    for fps in FPS_LISTE:
        lim = grenze_wpm(fps)
        out("| %d | " % fps + " | ".join("%d" % beste[(g, fps)] for g in GR_LISTE) + " | %.0f |" % lim)
        passt = passt and all(beste[(g, fps)] >= min(int(lim), WPM_LISTE[-1]) for g in GR_LISTE)
    out("")
    out("In der Simulation liest der Empfänger, bis ein dit etwa 1.8 Bilder lang ist (rund 0.65 × Bilder pro Sekunde). Die Seite")
    out("verspricht weniger: «bis etwa **%.1f × Bilder pro Sekunde** WPM» - ein dit ist dann 3 Bilder lang. Die Reserve ist für das," % GRENZE_K)
    out("was die Simulation nicht kennt (echte Kamera, ungleichmässige Bildzeiten auf dem Pi). "
        + ("Die Messung hält die Grenze überall ein." if passt else "ACHTUNG: die Messung hält die Grenze NICHT überall ein."))
    txt = "\n".join(zeilen) + "\n"
    if pfad:
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)
    return passt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei")
    ap.add_argument("--quelle", action="store_true", help="nur der Kern aus quelle/ (ohne die gebaute Datei)")
    ap.add_argument("--messen", action="store_true")
    ap.add_argument("--messen-ton", action="store_true", help="die Tabelle Ton: Tempo × Rauschen, Funkkanal")
    ap.add_argument("--messen-ir", action="store_true", help="die Tabelle IR zwischen zwei MoveEye")
    ap.add_argument("--tabelle")
    ap.add_argument("--laeufe", type=int, default=2)
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder")
    ap.add_argument("--nur-h", action="store_true", help="nur Teil H (nachgebaute Hardware)")
    a = ap.parse_args()
    datei = None if a.quelle else (a.datei or neueste())
    home = None
    if a.messen or a.messen_ton or a.messen_ir or a.quelle:
        ns = lade_kern()
    else:
        home = tempfile.mkdtemp(prefix="mw_morse_a_")
        os.environ["MOTIONWATCH_HOME"] = home
        ns = {"__name__": "mw_morse_test", "__file__": os.path.abspath(datei)}
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    if a.messen:
        return 0 if messen(ns, a.tabelle, a.laeufe) else 1
    if a.messen_ton:
        return 0 if messen_ton(ns, a.tabelle, a.laeufe) else 1
    if a.messen_ir:
        return 0 if messen_ir(ns, a.tabelle, a.laeufe) else 1
    t0 = time.time()
    try:
        if a.nur_h and home:
            teil_h(datei)
            return 1 if FEHLER else 0
        teil_a(ns); teil_b(ns); teil_c(ns); teil_d(ns); teil_e(ns); teil_i(ns)
        if home:
            ok(ns["morse_selftest"]().startswith("table"), "Selbsttest morse_selftest (Modus, Grenzen, Licht wie vorher, Text gereinigt)")
            ok(abs(ns["MORSE_LIMIT_K"] - GRENZE_K) < 1e-9, "die Grenze der Seite (MORSE_LIMIT_K) ist die der Messung")
            teil_f(datei, ns, a.browser, a.bilder)
            teil_h(datei)
    finally:
        if home:
            shutil.rmtree(home, ignore_errors=True)
    print(f"\n{N['ok']} Prüfungen bestanden, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    for f in FEHLER:
        print("  ✗ " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
