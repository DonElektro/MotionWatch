#!/usr/bin/env python3
"""Test «Eigenes Protokoll (2 Töne)» und «Handy-Funkgerät» (MoveEye Teil 639zzzf) - die Verträglichkeit mit der Seite des Besitzers.

  A) Die Seite: sein Decoder (/*DECODER-START*/ … /*DECODER-END*/), seine Funktionen prepTx und transmit stehen UNVERÄNDERT in
     funk/index.html und in FUNK_PAGE (Prüfsummen seiner Datei); funk/ passt zu quelle/; keine Anfragen nach aussen, kein
     innerHTML; alle Texte in fünf Sprachen.
  B) Gleich gerechnet: Schlüsselstrom (Python = seine Seite in node), Text -> Zeitplan (MoveEye = sein transmit, auf die Mikrosekunde).
  C) Verträglichkeit, beide Richtungen, ohne / mit Schlüssel, direkt und über den nachgebauten Funkkanal (Bandpass 300-3000 Hz,
     Rauschsperre, Lautstärke-Regelung), Rauschen, Tempo:
       MoveEye -> Seite: der Ton aus MoveEyes Lautsprecher-Code (morse_beep_chunks) -> SEIN Decoder in node (48 kHz, Blöcke 512)
       Seite -> MoveEye: der Ton nach SEINEM transmit -> MoveEyes Empfänger (FunkRx, 16 kHz, Stücke von 0.1 s wie das Mikrofon)
  D) Fremde Eingabe: Rauschen, Dauerton A / B, Pieper, Morse ohne Start-Ton, Unsinn - keine Nachricht, kein Absturz.
  E) MoveEye mit der Demo (--server, auch mit --browser): Format, Töne, Schlüssel (nur setzen / löschen; nie im Zustand, im
     Protokoll, im Verlauf), Rechte, Senden über den Lautsprecher, Empfang über das «Mikrofon», die Seiten bei 390 px in 5 Sprachen.

  python3 werkzeuge/funk_test.py [--datei X.py] [--server] [--browser] [--messen [--tabelle docs/Funk_Protokoll.md]]
Braucht node (die Seite des Besitzers läuft darin); ohne node: Fehler (in CI ist node da).
"""
import argparse
import glob
import hashlib
import http.server
import importlib.util
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

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE_JS = os.path.join(REPO, "werkzeuge", "funk_node.js")
SEITE = os.path.join(REPO, "funk", "index.html")
# die Prüfsummen aus SEINER Datei «Morse-Funk» (14.11.2026): Decoder-Block, prepTx, transmit - so laufen die Tests mit seinem Code
SHA_DECODER = "cc94f04635d226ed73891a567c63a2c82637ee59e3d54d10ce925bc3cdaebf31"
SHA_PREPTX = "eac9274705512a8311aeaea1b6e28832de78f52e0abe54f1183c6e1dc0c963f5"
SHA_TRANSMIT = "c83ccbc8dae4d7aa82b6cd71b90bf13e505041157fb0e12180fdc1deadf87bff"
RATE = 16000                                                   # MoveEyes Mikrofon; die Seite läuft mit 48000 (iPhone)
FUNK_NOTIZEN = """## Was das heisst

* **Direkt** (Handy-Lautsprecher am Mikrofon): beide Richtungen, mit und ohne Schlüssel, 8–25 WPM bis 0 dB fehlerfrei.
* **Tempo gleich einstellen.** Seine Seite (und MoveEye, das genau so liest) schätzt den Anfang nach dem eingestellten Tempo und lernt
  das wirkliche Tempo erst aus den ersten Zeichen. Ist der Sender viel schneller als eingestellt, sind die ersten Zeichen falsch, und
  MoveEye erkennt den Start-Ton nicht (siehe Tabelle «Tempo nicht gleich»). Auf beiden Seiten dasselbe Tempo wählen.
* **Über das Funkgerät** (nachgebaut, mit einer Lautstärke-Regelung, die das Rauschen in den Pausen anhebt – eher schlechter als ein echtes
  Gerät): 15–25 WPM fast immer fehlerfrei; bei 8–12 WPM einzelne falsche Zeichen (lange Pausen: das angehobene Rauschen liegt nahe bei
  einem der Töne und täuscht seinen Ton-Erkenner). Das ist sein Decoder – MoveEye liest absichtlich gleich.
* **Mit Schlüssel geht ein verlorenes Zeichen weiter:** der Schlüsselstrom zählt die Zeichen; fehlt eines (oder kommt eines dazu), ist der
  Rest der Nachricht Unsinn. Ohne Schlüssel bleibt es ein einzelner Fehler. Für eine spätere Fassung: Zeichen nummerieren oder neu
  ansetzen.
* **Später: echte Verschlüsselung.** Platz dafür, ohne das jetzige Protokoll zu brechen: das erste Zeichen einer Nachricht mit dem Code
  `.-.-` (kommt in den 39 Zeichen nicht vor) heisst «neueres Format, danach ein Versionsbyte». Seine Seite zeigt dann «□» und Unsinn (kein
  Absturz), MoveEye zeigt «neueres Format – dieses MoveEye kann es nicht lesen».
* Der Schlüssel **verschleiert** nur (jede Nachricht nutzt dieselbe Folge) – keine starke Verschlüsselung. Im Amateurfunk ist
  Verschlüsselung verboten (ITU-Vollzugsordnung Funk Nr. 25.2A; BAKOM: digitale Übertragungen nur unverschlüsselt).
"""
TEXT = "TREFFEN UM 15 UHR BEI DER BRUECKE?"
FEHLER = []
N = {}


def ok(cond, what):
    if cond:
        print("  ✓ " + what, flush=True)
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def morse_test_modul():
    """funkkanal() und das Rauschen wie im Morse-Test (Teil 639zzz Schritt 2)"""
    spec = importlib.util.spec_from_file_location("morse_test_mod", os.path.join(REPO, "werkzeuge", "morse_test.py"))
    m = importlib.util.module_from_spec(spec)
    argv = sys.argv; sys.argv = [argv[0]]
    try:
        spec.loader.exec_module(m)
    finally:
        sys.argv = argv
    return m


def node(tmp, *args, timeout=300):
    r = subprocess.run(["node", NODE_JS, SEITE] + [str(a) for a in args], capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError("node: " + r.stderr[-400:])
    return json.loads(r.stdout or "null")


def fn(src, head):
    i = src.index(head)
    return src[i:src.index("\n}\n", i) + 3]


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(ns):
    print("A) Die Seite", flush=True)
    src = open(SEITE, encoding="utf-8").read()
    a, e = src.index("/*DECODER-START*/"), src.index("/*DECODER-END*/") + len("/*DECODER-END*/")
    for name, txt, soll in (("Decoder", src[a:e], SHA_DECODER), ("prepTx", fn(src, "function prepTx("), SHA_PREPTX),
                            ("transmit", fn(src, "async function transmit("), SHA_TRANSMIT)):
        ok(hashlib.sha256(txt.encode("utf-8")).hexdigest() == soll, f"{name} unverändert aus seiner Seite (Prüfsumme)")
    ok(src == ns["FUNK_PAGE"], "funk/index.html = FUNK_PAGE in quelle/639zzzf_funk.py")
    r = subprocess.run([sys.executable, os.path.join(REPO, "werkzeuge", "funk_pwa.py"), "--pruefen"], capture_output=True, text=True, timeout=120)
    ok(r.returncode == 0, "funk/ passt zu quelle/ (werkzeuge/funk_pwa.py --pruefen): " + r.stdout.strip())
    aussen = re.findall(r"""(?:src|href|action)\s*=\s*["']?(?:https?:)?//(?!'\+location\.hostname)""", src)   # (der eigene Rechner: die sichere Seite von MoveEye) + re.findall(r"""(?:fetch|import|XMLHttpRequest|WebSocket|EventSource)\s*\(""", src)
    ok(not aussen, f"keine Anfragen nach aussen ({aussen[:3]})")
    ok("innerHTML" not in src and "eval(" not in src and "document.write" not in src, "kein innerHTML / eval / document.write")
    ok("morsefunk.key" not in src.replace("'morsefunk.'+k", "") and "store.set('key'" in src, "der Schlüssel nur im Speicher des Handys (wie seine Seite)")
    ok("based on" in src or "beruht auf der Seite «Morse-Funk»" in src, "Hinweis im Kopf: beruht auf seiner Seite «Morse-Funk»")
    sp = json.loads(subprocess.run(["node", "-e", "const s=require('fs').readFileSync(process.argv[1],'utf8');const i=s.indexOf('const TXT='),j=s.indexOf('};',i);"
                                    "const TXT=eval('('+s.slice(i+10,j+1)+')');const ks=Object.keys(TXT.de);"
                                    "console.log(JSON.stringify(Object.fromEntries(Object.keys(TXT).map(l=>[l,ks.filter(k=>!TXT[l][k]).concat(Object.keys(TXT[l]).filter(k=>!(k in TXT.de)))]))))",
                                    SEITE], capture_output=True, text=True, timeout=60).stdout or "{}")
    ok(sorted(sp) == ["de", "en", "fr", "it", "rm"] and not any(sp.values()), f"Texte der Seite in 5 Sprachen vollständig ({ {k: v[:3] for k, v in sp.items() if v} })")
    de = re.search(r"\nde:\{(.*?)\},\n", src, re.S).group(1)
    ok("ß" not in de, "kein «ß» im Deutsch der Seite")
    for v in ("mw", "file", "pwa"):
        p = ns["funk_page"](v, "fr", 5001)
        ok(("window.MW_FUNK=" in p) == (v == "mw") and ("manifest.webmanifest" in p) == (v == "pwa"), f"Fassung «{v}»: MoveEye-Teil / Manifest wie gedacht")


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(ns, tmp):
    print("B) Gleich gerechnet wie seine Seite", flush=True)
    for k in ("geheim", "Zürich 2026!", "x", "ein sehr langer Schlüssel mit Leerzeichen und ÄÖÜ äöü ß € 😀"):
        ok(node(tmp, "keystream", k, 600) == ns["funk_keystream"](k, 600), f"Schlüsselstrom «{k[:20]}»: gleich (600 Werte)")
    cfg = {"mode": "prot", "fA": 800, "fB": 1400, "wpm": 12, "auto": True, "sens": 10, "vol": 0.8}
    for key, txt, wpm in (("", "Grüsse aus Zürich – ÄÖÜ ß, 100%?", 12), ("geheim", TEXT, 20), ("k", "  zwei  Leer  ", 5), ("", "?.", 35)):
        cfg["wpm"] = wpm
        bs = node(tmp, "transmit", json.dumps(cfg), key, txt)
        _p, codes = ns["funk_prep"](txt, ns["funk_keystream"](key))
        t, mine = 0.15, []
        for d, f in ns["funk_timeline"](codes, wpm, 800, 1400):
            if f:
                mine.append((t, f, d))
            t += d
        same = len(mine) == len(bs) and all(abs(m[0] - b[0]) < 1e-6 and m[1] == b[1] and abs(m[2] - b[2]) < 1e-6 for m, b in zip(mine, bs))
        ok(same, f"Zeitplan «{txt[:18]}» {wpm} WPM, Schlüssel {'ja' if key else 'nein'}: MoveEye = sein transmit ({len(bs)} Töne)")
    cfg["mode"] = "morse"
    bs = node(tmp, "transmit", json.dumps(cfg), "", "SOS 73")
    _p, codes = ns["funk_prep"]("SOS 73", None, "morse")
    ok(len(bs) == sum(len(c) for c in codes if c != " "), "auch sein Modus «Morse»: gleich viele Töne")


# ---------------------------------------------------------------------------------------------------------------------- C
def me_ton(ns, text, key, wpm, rate):
    """der Ton, wie MoveEye ihn aus dem Lautsprecher gibt (der echte Code: morse_plan -> morse_beep_chunks), float -1..1"""
    ks = ns["funk_keystream"](key)
    _p, codes = ns["funk_prep"](text, ks)
    tl = ns["funk_timeline"](codes, wpm, 800, 1400)
    from scipy.signal import resample_poly
    y = np.concatenate(list(ns["morse_beep_chunks"](tl, 22050, 0.4)) + [np.zeros(int(1.5 * 22050), np.float32)]).astype(np.float64)
    return y if rate == 22050 else resample_poly(y, rate // 50, 441)        # (MoveEyes Lautsprecher: 22050 Hz)


def seite_ton(tmp, text, key, wpm, rate, mode="prot"):
    """der Ton nach SEINER Funktion transmit (Oszillator + Lautstärke-Rampen 5 ms)"""
    bs = node(tmp, "transmit", json.dumps({"mode": mode, "fA": 800, "fB": 1400, "wpm": wpm, "auto": True, "sens": 10, "vol": 0.8}), key, text)
    end = max(t + l for t, _f, l, _v in bs) + 1.5
    x = np.zeros(int(end * rate) + 1)
    for t, f, l, v in bs:
        i0, n = int(round(t * rate)), int(round(l * rate))
        y = np.sin(2 * np.pi * f * np.arange(n) / rate) * v
        r = int(0.005 * rate)
        y[:r] *= np.linspace(0, 1, r); y[-r:] *= np.linspace(1, 0, r)
        x[i0:i0 + n] += y
    return x


def strecke(mt, x, art, snr, seed):
    """x (16 kHz, -1..1) -> über das Funkgerät / direkt, mit Rauschen. art: "" direkt, "ton" (Träger bleibt, Ton getastet),
    "ptt" (Sendetaste für die ganze Nachricht gedrückt: die Rauschsperre öffnet 40 ms zu spät und rauscht am Ende 120 ms nach)"""
    rng = np.random.default_rng(seed)
    A = 3000.0
    y = x * A / 0.8
    if art:
        on = np.flatnonzero(np.abs(x) > 1e-4)
        env = np.zeros(x.size, np.float32)
        if on.size:
            env[on[0]:on[-1] + 1] = 1.0
        y = mt.funkkanal(y, env, "traeger" if art == "ptt" else "ton", rng, A)
    rausch = rng.normal(0, 1, x.size) * math.sqrt((A * A / 2.0) / (10 ** (snr / 10.0)) * 8000.0 / 2700.0)
    return np.clip(y + rausch, -32767, 32767)


def seite_hoert(tmp, x16, key, wpm=12):
    """SEIN Decoder in node: 48 kHz (aus 16 kHz hochgerechnet), Blöcke 512 - wie im iPhone"""
    from scipy.signal import resample_poly
    y = resample_poly(x16 / 32768.0, 3, 1).astype(np.float32)
    f = os.path.join(tmp, "ton.raw"); y.tofile(f)
    got = node(tmp, "decode", json.dumps({"mode": "prot", "fA": 800, "fB": 1400, "wpm": wpm, "auto": True, "sens": 10}), key, f, 48000)
    return [t for t, _m in got]


def me_hoert(ns, x16, key, wpm=12):
    got = []
    rx = ns["FunkRx"](RATE, lambda: {"mode": "prot", "fA": 800, "fB": 1400, "wpm": wpm, "auto": True, "sens": 10},
                      lambda t, i: got.append(t), strict=True)
    rx.ks = ns["funk_keystream"](key)
    pcm = x16.astype(np.int16)
    for i in range(0, pcm.size, 1600):
        rx.feed(pcm[i:i + 1600])
    return got


def zelle(ns, mt, tmp, richtung, key, wpm, art, snr, n=2, rwpm=None):
    """Anteil richtig gelesener Nachrichten (0..1). rwpm: das Tempo, auf das der Empfänger eingestellt ist (sonst = Sender:
    beide Seiten stellen dasselbe Tempo ein - seine Seite schätzt den Anfang nach dem eingestellten Tempo)"""
    rw = rwpm or wpm
    gut = 0
    for s in range(n):
        if richtung == "me>seite":
            x = me_ton(ns, TEXT, key, wpm, RATE)
            got = seite_hoert(tmp, strecke(mt, x, art, snr, 100 + s), key, rw)
        else:
            x = seite_ton(tmp, TEXT, key, wpm, RATE)
            got = me_hoert(ns, strecke(mt, x, art, snr, 200 + s), key, rw)
        gut += got == [TEXT]
    return gut / float(n)


def teil_c(ns, mt, tmp):
    print("C) Verträglichkeit mit seiner Seite (beide Richtungen, Schlüssel, Funkkanal)", flush=True)
    for richtung in ("me>seite", "seite>me"):
        for key in ("", "geheim"):
            # (über den Funkkanal nur, was die Messung sicher fehlerfrei zeigt: docs/Funk_Protokoll.md)
            for art, snr, wpms in (("", 20, (8, 12, 20, 25)), ("ton", 10, (15, 20)), ("ptt", 10, (15,))):
                res = {w: zelle(ns, mt, tmp, richtung, key, w, art, snr, 1) for w in wpms}
                name = {"": "direkt", "ton": "Funkgerät, Träger bleibt", "ptt": "Funkgerät, Sendetaste für die Nachricht"}[art]
                ok(all(v == 1.0 for v in res.values()),
                   f"{'MoveEye -> seine Seite' if richtung == 'me>seite' else 'seine Seite -> MoveEye'}, Schlüssel {'ja' if key else 'nein'}, {name}, "
                   f"+{snr} dB: {', '.join(f'{w} WPM ' + ('ok' if v == 1 else 'FALSCH') for w, v in res.items())}")
    # ohne den richtigen Schlüssel: Unsinn (aber kein Absturz) - und MoveEye <-> MoveEye
    got = seite_hoert(tmp, strecke(mt, me_ton(ns, TEXT, "geheim", 12, RATE), "", 20, 5), "falsch", 12)
    ok(got and got != [TEXT], f"falscher Schlüssel: nicht lesbar ({got[:1]})")
    got = me_hoert(ns, strecke(mt, me_ton(ns, TEXT, "geheim", 15, RATE), "ptt", 10, 6), "geheim", 15)
    ok(got == [TEXT], "MoveEye -> MoveEye über das Funkgerät, mit Schlüssel")


def messen(ns, mt, tmp, pfad=None, n=2):
    """die Tabelle: Tempo × Rauschen × Strecke, beide Richtungen (dauert einige Minuten)"""
    zeilen = []
    out = zeilen.append
    out("# Eigenes Protokoll (2 Töne): Verträglichkeit mit der Seite «Morse-Funk» des Besitzers - gemessen")
    out("")
    out(f"Erzeugt mit `python3 werkzeuge/funk_test.py --messen --tabelle docs/Funk_Protokoll.md`. Text «{TEXT}» (34 Zeichen), {n} Läufe pro Feld,")
    out("mit Schlüssel «geheim». Zahl = Anteil fehlerfrei gelesener Nachrichten (1 = alle, 0 = keine). «dB» = Ton zu Rauschen im Band 300–3000 Hz.")
    out("MoveEye → Seite: Ton aus MoveEyes Lautsprecher-Code → **sein Decoder** (node, 48 kHz). Seite → MoveEye: Ton nach **seiner Funktion transmit** → MoveEye (16 kHz).")
    out("")
    out("**Nicht gemessen: echte Handys, echte Lautsprecher und Mikrofone, echtes Funkgerät, Raum, Wind.**")
    wpms = (8, 12, 15, 20, 25)
    for art, titel in (("", "Direkt (Handy-Lautsprecher nahe am Mikrofon)"), ("ton", "Über ein FM-Handfunkgerät, Träger bleibt (Ton getastet)"),
                       ("ptt", "Über ein FM-Handfunkgerät, Sendetaste für die ganze Nachricht (Rauschsperre 40 ms spät, 120 ms Rauschschwanz)")):
        for richtung in ("me>seite", "seite>me"):
            out("")
            out(f"## {titel} – {'MoveEye → seine Seite' if richtung == 'me>seite' else 'seine Seite → MoveEye'}")
            out("")
            out("| Ton zu Rauschen | " + " | ".join(f"{w} WPM" for w in wpms) + " |")
            out("|---|" + "---|" * len(wpms))
            for snr in (20, 10, 6, 3, 0):
                row = [zelle(ns, mt, tmp, richtung, "geheim", w, art, snr, n) for w in wpms]
                out(f"| +{snr} dB | " + " | ".join(f"{v:.1g}" if v not in (0, 1) else str(int(v)) for v in row) + " |")
                print(zeilen[-1], flush=True)
    out("")
    out("## Tempo nicht gleich eingestellt (Empfänger steht auf 12 WPM, direkt, +20 dB)")
    out("")
    out("| Sender | " + " | ".join(f"{w} WPM" for w in wpms) + " |")
    out("|---|" + "---|" * len(wpms))
    for richtung in ("me>seite", "seite>me"):
        row = [zelle(ns, mt, tmp, richtung, "geheim", w, "", 20, n, rwpm=12) for w in wpms]
        out(f"| {'MoveEye → Seite' if richtung == 'me>seite' else 'Seite → MoveEye'} | " + " | ".join(f"{v:.1g}" if v not in (0, 1) else str(int(v)) for v in row) + " |")
        print(zeilen[-1], flush=True)
    out("")
    out(FUNK_NOTIZEN)
    txt = "\n".join(zeilen) + "\n"
    if pfad:
        open(pfad, "w", encoding="utf-8").write(txt)
    print(txt)


# ---------------------------------------------------------------------------------------------------------------------- D
def teil_d(ns, mt, tmp):
    print("D) Fremde Eingabe", flush=True)
    rng = np.random.default_rng(9)
    t = np.arange(RATE * 20) / RATE
    faelle = {"Rauschen 20 s": rng.normal(0, 3000, t.size),
              "Dauerton A (800 Hz)": 3000 * np.sin(2 * np.pi * 800 * t) + rng.normal(0, 300, t.size),
              "Dauerton B (1400 Hz)": 3000 * np.sin(2 * np.pi * 1400 * t),
              "Pieper A, 2 × pro Sekunde": 3000 * np.sin(2 * np.pi * 800 * t) * ((t * 2) % 1 < 0.3),
              "Pieper B, 2 × pro Sekunde": 3000 * np.sin(2 * np.pi * 1400 * t) * ((t * 2) % 1 < 0.3),
              "A und B abwechselnd, zufällig": 3000 * np.sin(2 * np.pi * np.where(rng.random(t.size // 800).repeat(800) < 0.5, 800, 1400) * t) * (rng.random(t.size // 800).repeat(800) < 0.6)}
    tl = ns["funk_timeline"](ns["funk_prep"]("SOS SOS", None, "morse")[1], 12, 800, 1400, "morse")
    faelle["Morse SOS auf Ton A (ohne Start-Ton)"] = np.concatenate([np.sin(2 * np.pi * 800 * np.arange(int(d * RATE)) / RATE) * 3000 if f else np.zeros(int(d * RATE)) for d, f in tl] + [np.zeros(RATE * 10)])
    for name, x in faelle.items():
        got = me_hoert(ns, np.clip(x, -32767, 32767), "")
        if name.startswith("A und B"):                       # (zwei reine Töne, zufällig: das sieht aus wie das Protokoll - nur Bruchstücke)
            ok(len(got) <= 2 and all(len(g) <= 8 for g in got), f"{name}: höchstens kurze Bruchstücke ({got[:3]})")
        else:
            ok(not got, f"{name}: keine Nachricht ({got[:2]})")
    rx = ns["FunkRx"](RATE, None, None)
    for bad in (np.full(1600, np.nan), np.full(1600, np.inf), np.zeros(0), np.ones(RATE * 700), rng.normal(0, 1e9, 1600)):
        rx.feed(bad)
    ok(rx.tail.size < rx.N, "NaN, unendlich, leer, riesig, übersteuert: kein Absturz, Speicher klein")
    long_ = [ns["FUNK_PCODE"][c] for c in (ns["FUNK_ALPHA"] * 11)[:400]]
    x = np.concatenate([np.zeros(RATE // 2)] + [np.sin(2 * np.pi * f * np.arange(int(d * RATE)) / RATE) * 3000 if f else np.zeros(int(d * RATE))
                                                for d, f in ns["funk_timeline"](long_, 20, 800, 1400)] + [np.zeros(RATE * 2)])
    got = me_hoert(ns, x, "", 20)
    ok(got and all(len(g) <= 240 for g in got), f"400 Zeichen am Stück: in Stücken zu höchstens 240 ({[len(g) for g in got]})")
    nv = []
    rx = ns["FunkRx"](RATE, None, lambda t_, i: nv.append(i))
    codes = [ns["FUNK_VERSION_CODE"]] + ns["funk_prep"]("NEUES FORMAT", None)[1]
    rx.feed((np.concatenate([np.zeros(RATE // 2)] + [np.sin(2 * np.pi * f * np.arange(int(d * RATE)) / RATE) * 3000 if f else np.zeros(int(d * RATE))
                                                     for d, f in ns["funk_timeline"](codes, 12, 800, 1400)] + [np.zeros(RATE)])).astype(np.int16))
    ok(nv and nv[0]["newer"], "das reservierte erste Zeichen: «neueres Format» statt Unsinn")
    f = os.path.join(tmp, "v.raw")
    (np.concatenate([np.zeros(24000)] + [np.sin(2 * np.pi * f_ * np.arange(int(d * 48000)) / 48000) * 0.5 if f_ else np.zeros(int(d * 48000))
                                         for d, f_ in ns["funk_timeline"](codes, 12, 800, 1400)] + [np.zeros(48000)])).astype(np.float32).tofile(f)
    got = node(tmp, "decode", json.dumps({"mode": "prot", "fA": 800, "fB": 1400, "wpm": 12, "auto": True, "sens": 10}), "", f, 48000)
    ok(got and got[0][0].startswith("□"), f"seine Seite und das neuere Format: «□» und weiter, kein Absturz ({got[:1]})")


WRAP = r"""
import os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = '''
def out_cmd(rate, connect=True):                          # (Test) der Lautsprecher = eine Datei: was MoveEye wirklich ausgibt
    return [sys.executable, "-c", "import sys,shutil;shutil.copyfileobj(sys.stdin.buffer,open(sys.argv[1],'ab'))", os.environ["MW_FUNK_SPK"]], ""
def _ft_mic():                                            # (Test) das «Mikrofon»: der Ton der Datei MW_FUNK_TON in Echtzeit
    while True:
        time.sleep(0.2)
        try:
            p_ = os.environ.get("MW_FUNK_TON", "")
            if p_ and os.path.exists(p_) and AUDIO is not None:
                d_ = open(p_, "rb").read(); os.remove(p_)
                for i_ in range(0, len(d_), 3200):
                    AUDIO._chunk(d_[i_:i_ + 3200]); time.sleep(0.097)
        except Exception as e_:
            print("ft_mic", e_, flush=True)
threading.Thread(target=_ft_mic, daemon=True).start()
'''
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
"""
PW = "Funk-" + "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))
GEHEIM = "Mein-Geheimnis-" + "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(6))


def teil_e(datei, ns, browser):
    import base64
    import urllib.error
    import urllib.request
    from scipy.signal import resample_poly
    print("E) MoveEye mit der Demo: Format, Schlüssel, Rechte, Senden, Empfangen" + (", Seiten im Browser" if browser else ""), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_funk_e_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    rec = os.path.join(tmp, "aufnahmen")
    st = {"source": "demo", "thermal_source": "", "thermal_on": False, "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False,
          "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "news_popup": False, "tours_auto": False, "audio_out": "default", "armed": True,
          "protect_level": "watch", "arm_delay": 0, "record_dir": rec, "ai_enabled": False, "eco_on": False, "tamper_on": False}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    spk, ton = os.path.join(tmp, "lautsprecher.raw"), os.path.join(tmp, "mikrofon.raw")
    env = dict(os.environ, MW_FUNK_SPK=spk, MW_FUNK_TON=ton)
    P = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    A = ("admin", PW)

    def req(path, data=None, user=A, raw=False):
        h = {"Authorization": "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode(), "Content-Type": "application/json"} if user else {}
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
        try:
            with op.open(r, timeout=60) as x:
                b = x.read()
                if raw:
                    return x.status, b, dict(x.headers)
                return x.status, (json.loads(b) if x.headers.get_content_type() == "application/json" else b)
        except urllib.error.HTTPError as e:
            b = e.read()
            if raw:
                return e.code, b, dict(e.headers)
            try:
                return e.code, json.loads(b)
            except ValueError:
                return e.code, b

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

    def mst():
        return req("/api/morse?lang=de")[1]["state"]
    try:
        ok(warte(lambda: req("/api/state")[0] == 200, 120), "MoveEye läuft (Demo)")
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        AN = ("Anna", "anna-pass-1")
        r = [req("/morse/funk", user=AN)[0], req("/morse/funk.html", user=AN)[0], req("/api/morse", {"action": "key", "key": "x"}, user=AN)[0],
             req("/api/morse", {"action": "funk", "fmt": "prot"}, user=AN)[0], req("/morse/funk", user=None)[0]]
        ok(r[:4] == [403] * 4 and r[4] in (401, 302, 303, 403), f"Familie / ohne Anmeldung: Seite, Datei, Schlüssel, Format verboten {r}")
        c, b, h = req("/morse/funk?lang=fr", raw=True)
        page = b.decode("utf-8", "replace")
        ok(c == 200 and "window.MW_FUNK=" in page and '"lang": "fr"' in page and "manifest.webmanifest" not in page and "/*DECODER-START*/" in page,
           "Administrator: /morse/funk = seine Seite in MoveEye (Sprache, Weg zurück, ohne Manifest)")
        c, b, h = req("/morse/funk.html", raw=True)
        ok(c == 200 and "attachment" in h.get("Content-Disposition", "") and "window.MW_FUNK=" not in b.decode("utf-8", "replace"),
           "«Als Datei herunterladen»: /morse/funk.html als Anhang, ohne MoveEye-Teil")
        c, j = req("/api/morse", {"action": "funk", "fa": 900, "fb": 1000, "lang": "de"})
        ok(c == 400 and "200 Hz" in (j.get("error") or ""), f"Töne zu nah beieinander: abgelehnt ({j.get('error')})")
        c, j = req("/api/morse", {"action": "funk", "fmt": "kaputt"})
        ok(c == 400, "unbekanntes Format: abgelehnt")
        c, j = req("/api/morse", {"action": "key", "key": "a" * 201})
        ok(c == 400 and not j["state"]["funk"]["key"], "Schlüssel zu lang: abgelehnt")
        c, j = req("/api/morse", {"action": "funk", "fmt": "prot", "fa": 800, "fb": 1400})
        ok(c == 200 and j["state"]["funk"]["fmt"] == "prot", "Format «Eigenes Protokoll (2 Töne)», Ton A 800 Hz, Ton B 1400 Hz")
        c, j = req("/api/morse", {"action": "key", "key": GEHEIM})
        alles = json.dumps(j)
        ok(c == 200 and j["state"]["funk"]["key"] is True and GEHEIM not in alles, "Schlüssel gesetzt - die Antwort sagt nur «gesetzt», nie den Schlüssel")
        c, j = req("/api/morse", {"action": "start", "minutes": 10})
        ok(c == 200 and j["state"]["on"], "Morse-Modus läuft")
        req("/api/morse", {"action": "prefs", "rx_sound": True, "wpm": 15})
        # senden: was MoveEye wirklich auf den Lautsprecher gibt -> SEIN Decoder
        c, j = req("/api/morse", {"action": "plan", "text": "Treffen um 15 Uhr!", "outs": ["white", "beep"], "wpm": 15})
        ok(c == 200 and j["plan"]["shown"] == "TREFFEN UM 15 UHR" and j["plan"]["wpm"] == 15 and j["plan"]["skipped"] == ["!"],
           f"Plan im Protokoll: «{(j.get('plan') or {}).get('shown')}», ausgelassen {(j.get('plan') or {}).get('skipped')}")
        c, j = req("/api/morse", {"action": "send", "text": "Treffen um 15 Uhr!", "outs": ["beep"], "wpm": 15})
        ok(c == 200 and j["state"]["tx"] and j["state"]["tx"]["outs"] == ["beep"], "Senden über den Lautsprecher")
        ok(warte(lambda: not mst()["tx"], 90), "Sendung fertig")
        time.sleep(1.0)
        pcm = np.fromfile(spk, dtype="<i2").astype(np.float64) if os.path.exists(spk) else np.zeros(0)
        # (nach dem Lautsprecher kommt Stille - sie beendet den letzten langen Ton B; die Datei hört einfach auf)
        y48 = resample_poly(np.concatenate([pcm, np.zeros(2 * 22050)]) / 32768.0, 320, 147).astype(np.float32)   # 22050 -> 48000
        f = os.path.join(tmp, "spk48.raw"); y48.tofile(f)
        cf = json.dumps({"mode": "prot", "fA": 800, "fB": 1400, "wpm": 15, "auto": True, "sens": 10})
        got = node(tmp, "decode", cf, GEHEIM, f, 48000)
        sp_ = np.abs(np.fft.rfft(pcm)) if pcm.size > 100 else np.zeros(2)
        fq_ = sorted(int(round(v)) for v in np.fft.rfftfreq(max(pcm.size, 2), 1 / 22050.0)[np.argsort(sp_)[-2:]]) if pcm.size > 100 else []
        ok([t for t, _m in got] == ["TREFFEN UM 15 UHR"],
           f"MoveEyes Lautsprecher -> SEIN Decoder mit Schlüssel: {got} ({pcm.size / 22050.0:.1f} s Ton, Spitzen {fq_} Hz, Pegel {np.sqrt(np.mean(pcm * pcm)) if pcm.size else 0:.0f})")
        got = node(tmp, "decode", cf, "", f, 48000)
        ok(got and got[0][0] != "TREFFEN UM 15 UHR", f"... ohne Schlüssel: nicht lesbar ({got[:1]})")
        # empfangen: SEIN transmit -> das «Mikrofon» -> MoveEye
        x = seite_ton(tmp, "Gruss an MoveEye 73", GEHEIM, 15, RATE)
        n0 = len(mst()["rx"]["msgs"])
        time.sleep(2.0)                                       # (nach der eigenen Sendung hört MoveEye kurz nicht zu - kein Echo)
        (np.clip(x * 3000 / 0.8 + np.random.default_rng(1).normal(0, 60, x.size), -32767, 32767)).astype("<i2").tofile(ton + ".tmp"); os.replace(ton + ".tmp", ton)
        ok(warte(lambda: len(mst()["rx"]["msgs"]) > n0, x.size / RATE + 20), "eine Nachricht ist angekommen")
        m = mst()["rx"]["msgs"][0]
        ok(m["text"] == "GRUSS AN MOVEEYE 73" and m["fmt"] == "prot" and m["key"] is True,
           f"SEIN transmit -> MoveEyes Mikrofon: «{m['text']}», Format {m['fmt']}, «entschlüsselt mit Schlüssel» {m['key']}")
        time.sleep(1.5)
        logt = json.dumps(req("/api/log?limit=3000")[1], ensure_ascii=False)
        fotos = [x_ for x_ in (req("/api/recordings?kind=image&limit=100")[1] or {}).get("items", []) if x_.get("name", "").startswith("morse_")]
        side = json.dumps(fotos, ensure_ascii=False)
        ok(GEHEIM not in logt and "key set" in logt and "GRUSS AN MOVEEYE 73" in logt, "Protokoll: «key set», die Nachricht - nie der Schlüssel")
        if shutil.disk_usage(tmp).free < 500 * 1024 ** 2:      # (unter 400 MB frei räumt MoveEye alte Aufnahmen weg)
            print("  – Verlauf nicht geprüft: weniger als 500 MB frei", flush=True)
        else:
            ok(GEHEIM not in side and "entschlüsselt mit Schlüssel" in side and "GRUSS AN MOVEEYE 73" in side,
               f"Verlauf: Bild mit «… · 🔑 entschlüsselt mit Schlüssel», nie der Schlüssel ({[x_.get('note') for x_ in fotos][:2]})")
        ok(GEHEIM not in json.dumps(mst()) and GEHEIM not in page, "Zustand und Seite: nie der Schlüssel")
        ok(req("/api/settings/export", user=AN)[0] == 403, "Einstellungen exportieren (enthält ihn wie die PIN): nur der Administrator")
        c, j = req("/api/morse", {"action": "key", "clear": True})
        ok(c == 200 and j["state"]["funk"]["key"] is False, "Schlüssel löschen")
        # Morse bleibt wie vorher
        req("/api/morse", {"action": "funk", "fmt": "morse"})
        if os.path.exists(spk):
            os.remove(spk)
        time.sleep(6.0)                                       # (höchstens 6 Sendungen pro Minute)
        c, j = req("/api/morse", {"action": "send", "text": "SOS", "outs": ["beep"], "wpm": 12})
        ok(c == 200 and warte(lambda: not mst()["tx"], 60), f"Format Morse: senden wie vorher ({c} {j.get('error')})")
        time.sleep(1.0)
        pcm = np.fromfile(spk, dtype="<i2").astype(np.float64) if os.path.exists(spk) else np.zeros(1)
        sp = np.abs(np.fft.rfft(pcm)); fpk = np.fft.rfftfreq(pcm.size, 1 / 22050.0)[int(np.argmax(sp))] if pcm.size > 100 else 0
        ok(abs(fpk - 660) < 5, f"Morse auf dem Lautsprecher: weiterhin 660 Hz ({fpk:.0f} Hz)")
        if browser:
            teil_g(base, PW, tmp, ns)
    finally:
        try:
            P.send_signal(signal.SIGKILL); P.wait(timeout=10)
        except Exception:
            pass
        logf.close()
        if FEHLER:
            try:
                print("  --- Ende von log.txt ---\n" + "".join(open(os.path.join(tmp, "log.txt"), errors="replace").readlines()[-20:]))
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)


def teil_g(base, pw, tmp, ns):
    """die Seiten bei 390 px in 5 Sprachen (mit den Schriften, die FONTCONFIG_FILE wählt), Weg zurück, kein waagrechtes Scrollen;
    seine Seite als PWA (funk/) und mit einem «Mikrofon» (Chromium spielt eine WAV-Datei als Mikrofon): sie liest MoveEyes Ton"""
    from playwright.sync_api import sync_playwright
    import wave
    print("G) Browser", flush=True)
    wav = os.path.join(tmp, "mic.wav")
    x = np.concatenate([np.zeros(RATE), me_ton(ns, "HALLO HANDY", "", 12, RATE), np.zeros(RATE * 30)])
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes((x * 0.6 * 32767).astype("<i2").tobytes())
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), lambda *a: http.server.SimpleHTTPRequestHandler(*a, directory=os.path.join(REPO, "funk")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    pwa = f"http://127.0.0.1:{srv.server_address[1]}/"
    titel = {"de": "Handy-Funkgerät", "en": "Phone radio", "fr": "Radio du téléphone", "it": "Radio del telefono", "rm": "Radio dal telefonin"}
    with sync_playwright() as pw_:
        br = pw_.chromium.launch(args=["--no-proxy-server", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                       "--use-file-for-fake-audio-capture=" + wav, "--autoplay-policy=no-user-gesture-required"])
        for lang in ("de", "en", "fr", "it", "rm"):
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": pw}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','%s');localStorage.setItem('morsefunk.lang',JSON.stringify('%s'));"
                                "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"settings\"]')}catch(e){}" % (lang, lang))
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            if lang != "de":                                  # die Sprache wie der Bediener wählen (langSet)
                pg.goto(base + "/more", wait_until="domcontentloaded"); pg.wait_for_timeout(1200)
                try:
                    with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                        pg.evaluate("k => { langSet(k); }", lang)
                except Exception:
                    pass
            pg.goto(base + "/morse", wait_until="domcontentloaded"); pg.wait_for_selector("#mo-fmt-seg button", timeout=20000)
            pg.wait_for_function("() => document.getElementById('mo-key-st').textContent.length > 3", timeout=20000)
            pg.locator("#mo-f-prot").click(); pg.wait_for_function("() => !document.getElementById('mo-prot').hidden", timeout=10000)
            pg.wait_for_timeout(300)
            sw = pg.evaluate("() => document.documentElement.scrollWidth")
            raus = pg.evaluate("""() => Array.from(document.querySelectorAll('#mo-fmt button, #mo-fmt a, #mo-fmt input, #mo-fmt .mo-hint, #mo-fmt .mo-warn'))
              .filter(e => e.offsetParent && (e.getBoundingClientRect().right > innerWidth + 1 || e.scrollWidth > e.clientWidth + 2)).map(e => (e.id || e.className) + ':' + e.textContent.slice(0, 30))""")
            eng = pg.evaluate("""() => Array.from(document.querySelectorAll('#mo-fmt *')).filter(e => e.children.length === 0
              && /\\b(the|Own protocol|Tone A|Set the key|Phone radio|Download)\\b/.test(e.textContent)).map(e => e.textContent.slice(0, 40))""")
            ok(sw <= 391 and not raus and (lang == "en" or not eng),
               f"Morse-Seite {lang}, 390 px: Karte «Format» passt ({sw} px, {raus[:2]}, Englisch übrig: {eng[:2]})")
            pg.locator("#mo-f-morse").click(); pg.wait_for_function("() => document.getElementById('mo-prot').hidden", timeout=10000)
            pg.goto(base + "/morse/funk", wait_until="domcontentloaded"); pg.wait_for_timeout(600)
            tt = pg.inner_text("#ttl")
            back = pg.locator("#mw-back")
            ok(tt == titel[lang] and back.is_visible() and back.get_attribute("href") == "/morse", f"Handy-Funkgerät {lang}: «{tt}», Weg zurück zum Morse-Modus")
            for b_, sh in (("#sendBtn", "#shSend"), ("#keyBtn", "#shKey"), ("#setBtn", "#shSet"), ("#histBtn", "#shHist")):
                pg.locator(b_).click(); pg.wait_for_timeout(250)
                vis = pg.locator(sh).is_visible()
                sw = pg.evaluate("() => document.documentElement.scrollWidth")
                wid = pg.evaluate("s => Array.from(document.querySelectorAll(s + ' *')).filter(e => e.offsetParent && e.getBoundingClientRect().right > innerWidth + 1)"
                                  ".map(e => e.tagName + ':' + e.textContent.slice(0, 20))", sh)
                pg.locator(sh + " [data-close]").click(); pg.wait_for_timeout(200)
                ok(vis and not pg.locator(sh).is_visible() and sw <= 391 and not wid, f"  {lang}: Blatt {sh} auf, passt ({sw} px {wid[:2]}), «Schliessen» führt zurück")
            ok(not errs, f"  {lang}: keine JavaScript-Fehler {errs[:2]}")
            ctx.close()
        # seine Seite als PWA (127.0.0.1 = sichere Umgebung): Mikrofon = MoveEyes Ton aus der WAV-Datei
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="de-CH")
        ctx.grant_permissions(["microphone"])
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(pwa, wait_until="domcontentloaded"); pg.wait_for_timeout(800)
        ok(not pg.locator("#mw-back").is_visible() and pg.evaluate("() => !!document.querySelector('link[rel=manifest]')"), "PWA: ohne «zurück» (eigene App), mit Manifest")
        pg.locator("#listen").click()
        try:
            pg.wait_for_function("() => JSON.parse(localStorage.getItem('morsefunk.hist')||'[]').some(h => h.text === 'HALLO HANDY')", timeout=60000)
            gehoert = True
        except Exception:
            gehoert = False
        ok(gehoert, "seine Seite im Browser hört MoveEyes Ton über das «Mikrofon»: «HALLO HANDY» im Verlauf (" + pg.inner_text("#live")[:40] + ")")
        ok(not errs, f"PWA: keine JavaScript-Fehler {errs[:2]}")
        ctx.close(); br.close()
    srv.shutdown()


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_funk_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei")
    ap.add_argument("--server", action="store_true")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--messen", action="store_true")
    ap.add_argument("--tabelle")
    ap.add_argument("--laeufe", type=int, default=2)
    a = ap.parse_args()
    if not shutil.which("node"):
        print("node fehlt"); return 1
    datei = a.datei or neueste()
    home = tempfile.mkdtemp(prefix="mw_funk_a_"); tmp = tempfile.mkdtemp(prefix="mw_funk_t_")
    t0 = time.time()
    try:
        ns = lade(datei, home)
        mt = morse_test_modul()
        if a.messen:
            messen(ns, mt, tmp, a.tabelle, a.laeufe); return 0
        teil_a(ns); teil_b(ns, tmp); teil_c(ns, mt, tmp); teil_d(ns, mt, tmp)
        if a.server or a.browser:
            teil_e(datei, ns, a.browser)
    finally:
        shutil.rmtree(home, ignore_errors=True); shutil.rmtree(tmp, ignore_errors=True)
    print(("FEHLER: " + str(len(FEHLER))) if FEHLER else "alles ok", f"({time.time() - t0:.0f} s)")
    for f in FEHLER:
        print("  ✗ " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
