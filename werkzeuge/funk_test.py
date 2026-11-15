#!/usr/bin/env python3
"""Test «Eigenes Protokoll (2 Töne)» und «Handy-Funkgerät» (MoveEye Teil 639zzzf) - die Verträglichkeit mit der Seite des Besitzers.

  A) Die Seite: sein Decoder (/*DECODER-START*/ … /*DECODER-END*/), seine Funktionen prepTx und transmit stehen UNVERÄNDERT in
     funk/index.html und in FUNK_PAGE (Prüfsummen seiner Datei); funk/ passt zu quelle/; keine Anfragen nach aussen, kein
     innerHTML; alle Texte in fünf Sprachen.
  B) Gleich gerechnet: V2 (feste Testvektoren: Python = Seite in node; falscher Schlüssel, geändertes Zeichen, jedes Mal neu),
     Text -> Zeitplan (MoveEye = sein transmit, auf die Mikrosekunde, ohne und mit Schlüssel), Audiodatei der Seite = transmit.
  C) Verträglichkeit, beide Richtungen, ohne / mit Schlüssel, direkt und über den nachgebauten Funkkanal (Bandpass 300-3000 Hz,
     Rauschsperre, Lautstärke-Regelung), Rauschen, Tempo:
       MoveEye -> Seite: der Ton aus MoveEyes Lautsprecher-Code (morse_beep_chunks) -> SEIN Decoder in node (48 kHz, Blöcke 512)
       Seite -> MoveEye: der Ton nach SEINEM transmit -> MoveEyes Empfänger (FunkRx, 16 kHz, Stücke von 0.1 s wie das Mikrofon)
  D) Fremde Eingabe: Rauschen, Dauerton A / B, Pieper, Morse ohne Start-Ton, Unsinn - keine Nachricht, kein Absturz.
  E) MoveEye mit der Demo (--server, auch mit --browser): Format, Töne, Schlüssel (nur setzen / löschen; nie im Zustand, im
     Protokoll, im Verlauf), Rechte, Senden über den Lautsprecher, Empfang über das «Mikrofon», Audiodateien (MoveEye-WAV -> Seite,
     Seiten-WAV -> MoveEye, Morse), die Seiten bei 390 px in 5 Sprachen, Audiodatei teilen / einlesen im Browser.

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
* **Mit Schlüssel (V2) zählt jedes Zeichen:** fehlt eines oder ist eines falsch, stimmen die Prüfzeichen nicht – die Nachricht heisst dann
  «falscher Schlüssel oder gestört» (statt Unsinn). Ohne Schlüssel bleibt es ein einzelner falscher Buchstabe. V2 ist 13 Zeichen länger.
* Im Amateurfunk ist Verschlüsselung verboten (ITU-Vollzugsordnung Funk Nr. 25.2A; BAKOM: digitale Übertragungen nur unverschlüsselt).
  Mit Schlüssel nie über Amateurfunk senden.

## V2: Nachrichten mit Schlüssel (Besitzer 14.11.2026: «nur noch V2»)

Ohne Schlüssel ändert sich nichts (Bit für Bit seine Seite «Morse-Funk»). Mit Schlüssel geht **jede** Nachricht so (V1, der feste
SHA-256-Strom seiner Seite, ist weg):

| Teil | Zeichen | Inhalt |
|---|---|---|
| Version | 1 | Code `.-.-` (kommt in den 39 Zeichen nicht vor; seine alte Seite zeigt «□») |
| Nonce | 6 | zufällig aus den 39 Zeichen (Seite: `crypto.getRandomValues`, Bytes < 234 → Byte mod 39; MoveEye: `secrets`) – rund 31.7 Bit |
| Text | n ≤ 200 | Klartext (nur die 39 Zeichen, vorne / hinten ohne Leerzeichen), Zeichen i um s<sub>i</sub> verschoben |
| Prüfung | 6 | aus den 38 Zeichen ohne Leerzeichen (der Empfänger kürzt das Ende) – rund 31.5 Bit |

* Schlüssel: `dk = PBKDF2-HMAC-SHA256(Schlüssel als UTF-8, Salz "MoveEye-Funk-v2", 200 000 Runden, 64 Bytes)`, `kE = dk[0:32]`,
  `kM = dk[32:64]`. Einmal pro Schlüssel gerechnet (Seite: beim Einstellen, MoveEye: im Speicher, nur der SHA-256 als Merkzeichen).
* Strom: für Zähler c = 0, 1, …: `HMAC-SHA256(kE, Nonce als ASCII ‖ c als 4 Bytes big endian)`; jedes Byte b < 234 gibt `b mod 39`.
  Geheimtext-Zeichen i = `ALPHA[(Index(Klar i) + s_i) mod 39]`.
* Prüfung: `h = HMAC-SHA256(kM, 0x02 ‖ Nonce ‖ Geheimtext)` (ASCII); jedes Byte b < 228 gibt `TAG[b mod 38]` (`TAG` = die 39 Zeichen ohne
  Leerzeichen), bis 6 Zeichen da sind (sonst `h = HMAC-SHA256(kM, h)` und weiter).
* Empfang: erstes Zeichen = Versionszeichen → Nonce, Geheimtext, Prüfung trennen; Prüfung falsch → «falscher Schlüssel oder gestört»;
  kein Schlüssel eingestellt → «verschlüsselt – hier ist kein Schlüssel eingestellt». Derselbe Text klingt jedes Mal anders (Nonce).
* Testvektoren (Seite in node = MoveEye, `funk_test.py` Teil B, Selbsttest `FUNK_V2_VEKTOREN`): Schlüssel `geheim`, Nonce `ABC12.`,
  Text `TREFFEN UM 15 UHR` → `ABC12.N?.4R8USIXLEETRJ1VONQ0F` (nach dem Versionszeichen).
* Grenzen: kein geprüftes Verfahren; 6 Prüfzeichen sind rund 32 Bit – genug gegen Störungen und Raten, nicht gegen einen grossen Angriff.
  Die Nonce ist kurz (31.7 Bit): bei vielen tausend Nachrichten mit demselben Schlüssel kann sie sich wiederholen.

## Audiodateien

* **Als Audiodatei:** die Nachricht als WAV (Mono, 16 Bit, 22 050 Hz, 0.5 s Vorlauf, 0.6 s Nachlauf), genau die Töne von transmit
  (Seite: `beepsOf` = transmit, geprüft) bzw. von MoveEyes Lautsprecher (`funk_wav_bytes`). iPhone: Teilen-Blatt (`navigator.share`),
  sonst Herunterladen; in MoveEye der übliche Download (in der App das Teilen-Blatt).
* **Audiodatei einlesen:** Seite: der Browser dekodiert (`decodeAudioData`, auf 48 kHz umgerechnet; Safari: WAV, M4A/AAC, MP3 –
  Ogg/Opus meist nicht), dann sein Decoder schneller als Echtzeit (`decodeSamples`). MoveEye: WAV selbst, M4A/MP3/Ogg mit ffmpeg,
  16 kHz, `FunkRx` bzw. `MorseAudio` wie am Mikrofon. Höchstens 10 Minuten. Im Verlauf mit 📁.

## Mehrton (MFSK): Spezifikation (Besitzer 14.11.2026)

Dritte Art neben Morse und dem 2-Ton-Protokoll, nur über den Ton, auf der Seite (Block `MFSK` in `FUNK_PAGE`) und in MoveEye
(Teil 639zzzi) Bit für Bit gleich (Testvektoren `MFSK_VEKTOREN`, `funk_test.py` Teil M).

| Vorlage | Töne | Frequenzen | Symbol / Schutz | Bit pro Symbol | roh |
|---|---|---|---|---|---|
| 1 | 4 | 800 + i · 250 Hz (800–1550) | 40 ms / 6 ms | 2 | 50 bit/s |
| 2 | 8 | 650 + i · 200 Hz (650–2050) | 50 ms / 8 ms | 3 | 60 bit/s |
| 3 | 16 | 500 + i · 150 Hz (500–2750) | 64 ms / 8 ms | 4 | 62.5 bit/s |
| 0 | Baukasten: 2–32 | Start + Abstand oder Liste, 300–3000 Hz | 10–500 ms (0.5-ms-Schritte) / 0 bis T/2 | floor(log2 n) | |

* **Symbol:** ein Ton für T ms, die Phase läuft durch (keine Klicks); Grenzen bei `round(j · T · Rate)`. Daten nutzen die ersten 2^k Töne,
  Gray-Code (Wert v → Ton `v ^ (v >> 1)`). Der Empfänger misst nur `[Start + Schutz, Start + T)` mit Hann-Fenster (DFT pro Ton).
  Prüfung des Baukastens: Abstand < 1/(T − Schutz) → geht nicht; < 2/(T − Schutz) → Warnung; n keine Zweierpotenz → Warnung.
* **Rahmen:** Vorspann 0.3 s (Ton 0 und Ton n − 1 abwechselnd: öffnet die Rauschsperre, stellt die Lautstärke-Regelung ein) · Sync 12 Symbole
  (Ton `a · n // 16`, a = 0 15 5 10 3 12 8 1 14 6 11 2) · Kopf 5 Bytes `[0x10 | Vorlage, FEC | Schlüssel << 2 | gepackt << 3, Länge,
  Prüfwert Baukasten (CRC-8 von "n|f·10;…|T·10|Schutz·10") oder 0, CRC-8]`, immer Faltungscode 1/2 (92 Bit) · Nutzdaten + CRC-16/CCITT-FALSE
  über Kopf (4 Bytes) und Nutzdaten, mit der gewählten Fehlerkorrektur, verschachtelt (Block: Spalten = ceil(√n), zeilenweise
  geschrieben, spaltenweise gelesen) · auf k Bit mit Nullen aufgefüllt · Nachlauf 3 Symbole Ton 0.
* **Fehlerkorrektur:** aus (roh) · leicht = Faltungscode K = 7 (171, 133 oktal) punktiert auf 3/4 (Muster 110110) · stark = derselbe Code,
  Rate 1/2. 6 Nullbits am Ende, Viterbi mit weichen Entscheidungen: pro Bit (max. Amplitude der Töne mit Bit 1 − mit Bit 0) / max. Amplitude.
* **Text:** nur die 39 Zeichen → gepackt (3 Zeichen in 2 Bytes: `i0·1521 + i1·39 + i2`; 2 Zeichen: `59319 + i0·39 + i1`; 1 Zeichen: 1 Byte),
  sonst UTF-8 (Gross / klein, Umlaute, Emoji). Höchstens 200 Zeichen und 255 Bytes Nutzdaten.
* **Schlüssel (V2 auf Bytes):** dieselben kE / kM (PBKDF2 wie oben); Nonce 4 Bytes zufällig; Strom `HMAC-SHA256(kE, "M" ‖ Nonce ‖ Zähler)`
  XOR; Prüfung `HMAC-SHA256(kM, 0x03 ‖ Kopf 4 Bytes ‖ Nonce ‖ Geheimtext)[0:4]` (32 Bit). Nutzdaten = Nonce ‖ Geheimtext ‖ Prüfung.
* **Empfang:** Energien aller Töne alle T/8; Sync = Mittel über die 12 Symbole von (Energie des Sync-Tons / Energie aller Töne) ≥
  1/n + 0.35 · (1 − 1/n), alle 12 über 1.5 × Rauschboden; das beste von 8 Nachbarn gilt. Takt nachgeführt (früh / spät, ±T/8). Alle
  Vorlagen gleichzeitig (der Kopf sagt, welche), der Baukasten nur, wenn eingestellt. Kopf falsch → weitersuchen; CRC-16 falsch →
  «gestört»; Prüfung falsch → «falscher Schlüssel oder gestört»; anderer Baukasten-Prüfwert → «andere Baukasten-Einstellungen».

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
    for key, nonce, plain, body in ns["FUNK_V2_VEKTOREN"] + (("ein sehr langer Schlüssel mit Leerzeichen und ÄÖÜ äöü ß € 😀", "0.?0.?", "Q" * 200, None),):
        js = node(tmp, "v2seal", key, nonce, plain)
        py = ns["funk_v2_seal"](plain, key, nonce)
        ok(js == py and (body is None or js == body) and node(tmp, "v2open", key, js) == {"text": plain, "err": ""} and ns["funk_v2_open"](js, key) == (plain, ""),
           f"V2 «{key[:12]}» / «{nonce}» / «{plain[:12]}»: Seite = MoveEye = Testvektor ({js[:20]}…)")
    body = ns["FUNK_V2_VEKTOREN"][0][3]
    zu = body[:9] + ("A" if body[9] != "A" else "B") + body[10:]
    r = [node(tmp, "v2open", "falsch", body)["err"], node(tmp, "v2open", "", body)["err"], node(tmp, "v2open", "geheim", zu)["err"],
         ns["funk_v2_open"](zu, "geheim")[1], node(tmp, "v2open", "geheim", body[:12])["err"]]
    ok(r == ["bad", "nokey", "bad", "bad", "short"], f"V2: falscher Schlüssel, kein Schlüssel, ein Zeichen geändert, zu kurz: erkannt {r}")
    a_, b_ = node(tmp, "v2seal", "geheim", "", "SOS"), node(tmp, "v2seal", "geheim", "", "SOS")
    ok(a_ != b_ and a_[6:-6] != b_[6:-6] and ns["funk_v2_seal"]("SOS", "geheim") != ns["funk_v2_seal"]("SOS", "geheim"),
       f"V2: derselbe Text zweimal klingt anders (Seite {a_} / {b_})")
    cfg = {"mode": "prot", "fA": 800, "fB": 1400, "wpm": 12, "auto": True, "sens": 10, "vol": 0.8}
    for key, txt, wpm in (("", "Grüsse aus Zürich – ÄÖÜ ß, 100%?", 12), ("geheim", TEXT, 20), ("k", "  zwei  Leer  ", 5), ("", "?.", 35)):
        cfg["wpm"] = wpm
        bs = node(tmp, "transmit", json.dumps(cfg), key, txt, "N0NCE?")
        _p, codes = ns["funk_tx_codes"](txt, key, "N0NCE?")
        t, mine = 0.15, []
        for d, f in ns["funk_timeline"](codes, wpm, 800, 1400):
            if f:
                mine.append((t, f, d))
            t += d
        same = len(mine) == len(bs) and all(abs(m[0] - b[0]) < 1e-6 and m[1] == b[1] and abs(m[2] - b[2]) < 1e-6 for m, b in zip(mine, bs))
        ok(same, f"Zeitplan «{txt[:18]}» {wpm} WPM, Schlüssel {'ja (V2)' if key else 'nein'}: MoveEye = sein transmit ({len(bs)} Töne)")
        wb = node(tmp, "beeps", json.dumps(cfg), key, txt, "N0NCE?")
        ok(len(wb) == len(bs) and all(abs(w[0] - b[0]) < 1e-9 and w[1] == b[1] and abs(w[2] - b[2]) < 1e-9 for w, b in zip(wb, bs)),
           f"  Audiodatei der Seite (beepsOf) = sein transmit ({len(wb)} Töne)")
    cfg["mode"] = "morse"
    bs = node(tmp, "transmit", json.dumps(cfg), "", "SOS 73")
    _p, codes = ns["funk_prep"]("SOS 73", None, "morse")
    ok(len(bs) == sum(len(c) for c in codes if c != " "), "auch sein Modus «Morse»: gleich viele Töne")


# ---------------------------------------------------------------------------------------------------------------------- C
def me_ton(ns, text, key, wpm, rate):
    """der Ton, wie MoveEye ihn aus dem Lautsprecher gibt (der echte Code: morse_plan -> morse_beep_chunks), float -1..1"""
    _p, codes = ns["funk_tx_codes"](text, key, nonce_fest(wpm))       # (feste Nonce: der Test ist bei jedem Lauf gleich)
    tl = ns["funk_timeline"](codes, wpm, 800, 1400)
    from scipy.signal import resample_poly
    y = np.concatenate(list(ns["morse_beep_chunks"](tl, 22050, 0.4)) + [np.zeros(int(1.5 * 22050), np.float32)]).astype(np.float64)
    return y if rate == 22050 else resample_poly(y, rate // 50, 441)        # (MoveEyes Lautsprecher: 22050 Hz)


def seite_ton(tmp, text, key, wpm, rate, mode="prot"):
    """der Ton nach SEINER Funktion transmit (Oszillator + Lautstärke-Rampen 5 ms)"""
    bs = node(tmp, "transmit", json.dumps({"mode": mode, "fA": 800, "fB": 1400, "wpm": wpm, "auto": True, "sens": 10, "vol": 0.8}), key, text, nonce_fest(wpm))
    end = max(t + l for t, _f, l, _v in bs) + 1.5
    x = np.zeros(int(end * rate) + 1)
    for t, f, l, v in bs:
        i0, n = int(round(t * rate)), int(round(l * rate))
        y = np.sin(2 * np.pi * f * np.arange(n) / rate) * v
        r = int(0.005 * rate)
        y[:r] *= np.linspace(0, 1, r); y[-r:] *= np.linspace(1, 0, r)
        x[i0:i0 + n] += y
    return x


def nonce_fest(wpm):
    """V2: eine feste Nonce pro Tempo - sonst klingt jede Nachricht anders und der Funkkanal-Test wäre bei jedem Lauf ein anderer"""
    return "NONC%02d" % (int(wpm) % 100)


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
    """SEIN Decoder in node: 48 kHz (aus 16 kHz hochgerechnet), Blöcke 512 - wie im iPhone; V2 von der Seite geöffnet"""
    from scipy.signal import resample_poly
    y = resample_poly(x16 / 32768.0, 3, 1).astype(np.float32)
    f = os.path.join(tmp, "ton.raw"); y.tofile(f)
    got = node(tmp, "decode", json.dumps({"mode": "prot", "fA": 800, "fB": 1400, "wpm": wpm, "auto": True, "sens": 10}), key, f, 48000)
    return [t for t, _m in got]


def me_hoert(ns, x16, key, wpm=12):
    got = []
    rx = ns["FunkRx"](RATE, lambda: {"mode": "prot", "fA": 800, "fB": 1400, "wpm": wpm, "auto": True, "sens": 10},
                      lambda t, i: got.append((t, i)), strict=True)
    pcm = x16.astype(np.int16)
    for i in range(0, pcm.size, 1600):
        rx.feed(pcm[i:i + 1600])
    out = []
    for t_, i_ in got:                                          # (V2: opened like MoveEye does - funk_rx_message)
        t, _k, bad = ns["funk_rx_open"](t_, i_["newer"], key)
        out.append("!" + bad if bad else t)
    return out


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
    ok(got == ["!bad"], f"falscher Schlüssel: «falscher Schlüssel oder gestört» statt Unsinn ({got[:1]})")
    got = seite_hoert(tmp, strecke(mt, me_ton(ns, TEXT, "geheim", 12, RATE), "", 20, 5), "", 12)
    ok(got == ["!nokey"], f"kein Schlüssel eingestellt: «verschlüsselt – kein Schlüssel» ({got[:1]})")
    # Rauschen nach der Nachricht (Träger bleibt, die Lautstärke-Regelung hebt es an): sein Decoder las daraus ein «E» als
    # zweite Nachricht (in rund 15 % der Fälle). Die Seite verwirft solche Stücke ohne Start-Ton (rxJunk) - diese Texte zeigten es.
    rr = random.Random(7)
    texte = ["".join(rr.choice(ns["FUNK_ALPHA"]) for _ in range(47)).strip() for _ in range(18)]
    for i in (4, 7, 12, 17):
        _p, codes = ns["funk_tx_codes"](texte[i], "")
        from scipy.signal import resample_poly
        y = np.concatenate(list(ns["morse_beep_chunks"](ns["funk_timeline"](codes, 15, 800, 1400), 22050, 0.4)) + [np.zeros(int(1.5 * 22050), np.float32)])
        got = seite_hoert(tmp, strecke(mt, resample_poly(y.astype(np.float64), 320, 441), "ton", 10, 100), "", 15)
        ok(got == [_p.strip()], f"Rauschen nach der Nachricht (Funkgerät, Träger bleibt): kein «E» danach ({[g[:6] for g in got]})")
    got = me_hoert(ns, strecke(mt, seite_ton(tmp, TEXT, "geheim", 12, RATE), "", 20, 7), "falsch", 12)
    ok(got == ["!bad"], f"MoveEye mit falschem Schlüssel: erkannt ({got[:1]})")
    got = me_hoert(ns, strecke(mt, seite_ton(tmp, TEXT, "", 12, RATE), "", 20, 8), "geheim", 12)
    ok(got == [TEXT], f"mit Schlüssel eingestellt, Nachricht ohne Schlüssel: lesbar wie sie kam ({got[:1]})")
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
    ok(got == [["!nokey", "prot"]], f"das Versionszeichen ohne Schlüssel auf der Seite: «kein Schlüssel», kein Absturz ({got[:1]})")


# ---------------------------------------------------------------------------------------------------------------------- M
MF_KIT = {"n": 6, "f0": 700, "df": 220, "T": 45, "g": 7}


def mf_ton16(ns, text, pid, fec, key="", s=None, seite=None, tmp=None):
    """der Mehrton-Ton bei 16 kHz (-1..1, Amplitude 0.8): von MoveEye (mfsk_render) oder von der Seite (node mfRender)"""
    s = s or ns["MFSK_PRESETS"][pid]
    if seite:
        f = os.path.join(tmp, "mf_s.raw")
        node(tmp, "mfwav", text, pid, fec, key, "", json.dumps(s) if pid == 0 else "", RATE, f)
        y = np.fromfile(f, np.float32).astype(np.float64)
    else:
        sym, _e = ns["mfsk_frame"](text, pid, s, fec, key)
        y = ns["mfsk_render"](sym, s, RATE, 0.8).astype(np.float64)
    return np.concatenate([np.zeros(RATE // 2), y, np.zeros(RATE)])


def mf_me_hoert(ns, x16, key="", custom=None):
    rx = ns["MfskRx"](RATE, custom, None, lambda: key)
    pcm = np.clip(x16, -32767, 32767).astype(np.int16)
    for i in range(0, pcm.size, 1600):
        rx.feed(pcm[i:i + 1600])
    return [(r["text"], r["bad"]) for r in rx.got]


def mf_seite_hoert(tmp, x16, key="", custom=None):
    from scipy.signal import resample_poly
    f = os.path.join(tmp, "mf_in.raw")
    resample_poly(x16 / 32768.0, 3, 1).astype(np.float32).tofile(f)
    return [(r["text"], r["bad"]) for r in node(tmp, "mfdecode", f, 48000, key, json.dumps(custom) if custom else "")]


def teil_m(ns, mt, tmp):
    print("M) Mehrton (MFSK): Seite = MoveEye, beide Richtungen, Funkkanal, Schlüssel, Baukasten", flush=True)
    for text, pid, fec, key, nonce, h in ns["MFSK_VEKTOREN"]:
        js = node(tmp, "mfframe", text, pid, fec, key, nonce, "")
        py, _e = ns["mfsk_frame"](text, pid, ns["MFSK_PRESETS"][pid], fec, key, bytes.fromhex(nonce) if nonce else None)
        hj = hashlib.sha256(",".join(map(str, js)).encode()).hexdigest()[:16]
        ok(js == py and hj == h, f"Testvektor «{text[:14]}» Vorlage {pid}, FEC {fec}, Schlüssel {'ja' if key else 'nein'}: Seite = MoveEye = {h} ({len(js)} Symbole)")
    f = os.path.join(tmp, "mf_r.raw")
    for rate in (16000, 48000):
        node(tmp, "mfwav", "Hallo 73", 0, 1, "geheim", "01020304", json.dumps(MF_KIT), rate, f)
        sym, _e = ns["mfsk_frame"]("Hallo 73", 0, ns["mfsk_check"](MF_KIT)[0], 1, "geheim", bytes.fromhex("01020304"))
        py = ns["mfsk_render"](sym, ns["mfsk_check"](MF_KIT)[0], rate, 0.8); js = np.fromfile(f, np.float32)
        ok(js.size == py.size and float(np.abs(js - py).max()) * 32767 < 1.0, f"Ton der Seite = Ton von MoveEye ({rate} Hz, Baukasten, Abweichung {float(np.abs(js - py).max()) * 32767:.4f} LSB)")
    for kit in (MF_KIT, {"n": 8, "f0": 700, "df": 10, "T": 20, "g": 5}, {"n": 4, "f0": 2900, "df": 300, "T": 40, "g": 5}, {"list": [600, 900, 1250, 1700], "T": 30.5, "g": 4},
                {"n": 40, "f0": 400, "df": 60, "T": 100, "g": 10}, {"n": 8, "f0": 500, "df": 100, "T": 12.25, "g": 3}):
        j = node(tmp, "mfcheck", json.dumps(kit)); c, err, warn, need = ns["mfsk_check"](kit)
        ok(bool(j["s"]) == bool(c) and len(j["err"]) == len(err) and len(j["warn"]) == len(warn) and j["need"] == need,
           f"Baukasten {json.dumps(kit)[:44]}: Prüfung gleich (Fehler {err[:1]}, Warnungen {len(warn)})")
    T2 = "Grüsse aus Zürich, 15 Uhr!"
    for pid in (1, 2, 3):
        for fec in (0, 1, 2):
            key = "geheim" if fec == 1 else ""
            r1 = mf_seite_hoert(tmp, ft_strecke(mt, mf_ton16(ns, T2, pid, fec, key), "", 3, 300 + pid), key)
            r2 = mf_me_hoert(ns, ft_strecke(mt, mf_ton16(ns, T2, pid, fec, key, seite=True, tmp=tmp), "ptt", 10, 400 + pid), key)
            ok(r1 == [(T2, "")] and r2 == [(T2, "")], f"Vorlage {pid} ({1 << (pid + 1)} Töne), FEC {('aus', 'leicht', 'stark')[fec]}{', Schlüssel' if key else ''}: "
               f"MoveEye -> Seite direkt +3 dB {r1[:1]}, Seite -> MoveEye über Funk (Sendetaste) +10 dB {r2[:1]}")
    x = mf_ton16(ns, T2, 2, 2, "geheim") * 3000 / 0.8
    ok(mf_seite_hoert(tmp, x, "falsch") == [("", "bad")] and mf_me_hoert(ns, x, "") == [("", "nokey")],
       "falscher Schlüssel / kein Schlüssel: erkannt, kein Unsinn")
    kit = ns["mfsk_check"](MF_KIT)[0]
    x = mf_ton16(ns, T2, 0, 2, "", s=kit) * 3000 / 0.8
    k2 = dict(MF_KIT, g=7.5)
    r = [mf_seite_hoert(tmp, x, "", MF_KIT), mf_me_hoert(ns, x, "", kit), mf_me_hoert(ns, x, ""), mf_me_hoert(ns, x, "", ns["mfsk_check"](k2)[0])]
    ok(r[0] == [(T2, "")] and r[1] == [(T2, "")] and r[2] == [] and r[3] in ([("", "settings")], []),
       f"Baukasten: beide gleich -> gelesen; ohne Baukasten -> nichts; anderer Baukasten -> «andere Einstellungen» {r[3]}")
    rng = np.random.default_rng(11)
    t = np.arange(RATE * 20) / RATE
    for name, x in (("Rauschen 20 s", rng.normal(0, 3000, t.size)), ("Pieper 800 / 1300 Hz", 3000 * np.sin(2 * np.pi * np.where((t * 4) % 2 < 1, 800, 1300) * t)),
                    ("seine 2 Töne (Protokoll)", seite_ton(tmp, TEXT, "", 15, RATE) * 3000 / 0.8)):
        ok(not mf_me_hoert(ns, x) and not mf_seite_hoert(tmp, x), f"{name}: kein Mehrton-Rahmen")


def ft_strecke(mt, x, art, snr, seed):
    return strecke(mt, x, art, snr, seed)


def mf_messen(ns, mt, tmp, pfad=None, n=3):
    """Mehrton: Zeichen pro Sekunde und Anteil fehlerfrei je Vorlage und FEC, bei 10 / 5 / 0 / -6 / -10 dB und über das Funkgerät,
    neben dem 2-Ton-Protokoll (TEXT, ohne Schlüssel; Empfänger MoveEye 16 kHz)"""
    zeilen = ["<!-- MFSK-MESSUNG -->", "", "## Mehrton (MFSK) – gemessen", "",
              f"Erzeugt mit `python3 werkzeuge/funk_test.py --mfsk-messen --tabelle docs/Funk_Protokoll.md`. Text «{TEXT}» ({len(TEXT)} Zeichen, gepackt),",
              f"{n} Läufe pro Feld, ohne Schlüssel. Zeichen/s = Textlänge durch die ganze Sendung (mit Vorspann, Sync, Kopf, CRC). «dB» wie oben",
              "(Ton zu Rauschen im Band 300–3000 Hz). Funk = nachgebautes FM-Handfunkgerät (Sendetaste für die ganze Nachricht: Rauschsperre 40 ms",
              "spät, 120 ms Rauschschwanz). Empfänger: MoveEye (16 kHz); die Seite liest gleich (Teil M der Tests).", "",
              "| Art | Fehlerkorrektur | Zeichen/s | +10 dB | +5 dB | 0 dB | −6 dB | −10 dB | Funk +10 dB | Funk +3 dB |", "|---|---|---|---|---|---|---|---|---|---|"]
    print("\n".join(zeilen), flush=True)
    cols = (("", 10), ("", 5), ("", 0), ("", -6), ("", -10), ("ptt", 10), ("ptt", 3))
    for pid in (1, 2, 3):
        s = ns["MFSK_PRESETS"][pid]
        for fec in (0, 1, 2):
            sym, _e = ns["mfsk_frame"](TEXT, pid, s, fec, "")
            x = mf_ton16(ns, TEXT, pid, fec)
            row = []
            for art, snr in cols:
                g = sum(mf_me_hoert(ns, strecke(mt, x, art, snr, 900 + k)) == [(TEXT, "")] for k in range(n))
                row.append(g / float(n))
            zeilen.append(f"| {s['n']} Töne, {s['T']:g} ms | {('aus', 'leicht', 'stark')[fec]} | {len(TEXT) / (len(sym) * s['T'] / 1000.0):.1f} | "
                          + " | ".join(f"{v:.2g}" if v not in (0, 1) else str(int(v)) for v in row) + " |")
            print(zeilen[-1], flush=True)
    for wpm in (12, 20):
        x = seite_ton(tmp, TEXT, "", wpm, RATE)
        row = [sum(me_hoert(ns, strecke(mt, x, art, snr, 900 + k), "", wpm) == [TEXT] for k in range(n)) / float(n) for art, snr in cols]
        secs = x.size / RATE - 1.5
        zeilen.append(f"| 2 Töne (Protokoll), {wpm} WPM | – | {len(TEXT) / secs:.1f} | " + " | ".join(f"{v:.2g}" if v not in (0, 1) else str(int(v)) for v in row) + " |")
        print(zeilen[-1], flush=True)
    zeilen += ["", "**Was das heisst** (Messung vom 14.11.2026, je 3 Läufe – kleine Stichprobe):",
               "* Mehrton ist bei gleichem Text 3–6 × schneller als das 2-Ton-Protokoll (3.1–5.7 statt 0.9–1.4 Zeichen/s) und liest noch bei −6 dB,",
               "  wo das 2-Ton-Protokoll nichts mehr liest (jeder Ton liegt in einem schmalen Band; der Empfänger misst nur dort).",
               "* Die Fehlerkorrektur kostet Zeit (leicht × 4/3, stark × 2 der Nutzdaten; Vorspann, Sync und Kopf bleiben gleich) und bringt ihren",
               "  Gewinn nahe an der Grenze: bei −10 dB liest «aus» nichts mehr, «leicht» und «stark» alles. Zwischen leicht und stark zeigt diese",
               "  Messung keinen Unterschied (stark sollte mehr einzelne Aussetzer aushalten – nicht gemessen). Vorgabe: 8 Töne, leicht.",
               "* Über das nachgebaute Funkgerät (Sendetaste, Rauschsperre) bei +10 und +3 dB alles fehlerfrei. Nicht gemessen: echte Geräte, Raum, Wind.",
               "<!-- /MFSK-MESSUNG -->"]
    txt = "\n".join(zeilen) + "\n"
    if pfad:
        d = open(pfad, encoding="utf-8").read()
        a, e = d.find("<!-- MFSK-MESSUNG -->"), d.find("<!-- /MFSK-MESSUNG -->")
        d = (d[:a] + txt.rstrip("\n") + d[e + len("<!-- /MFSK-MESSUNG -->"):]) if a >= 0 and e > a else d.rstrip("\n") + "\n\n" + txt
        open(pfad, "w", encoding="utf-8").write(d)
    print(txt)


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
    import urllib.parse
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
        c, b, h = req("/help", raw=True)
        hp = b.decode("utf-8", "replace")
        ok(c == 200 and "📡 Eigenes Protokoll (2 Töne) und Handy-Funkgerät" in hp and "📶 Mehrton (MFSK)" in hp and "📡 Own protocol (2 tones)" in hp,
           "Anleitung: die Absätze zum Protokoll und zum Mehrton stehen drin (de, en)")
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
        # Audiodateien (Format Protokoll, mit Schlüssel): MoveEyes WAV -> seine Seite; die WAV der Seite -> MoveEye
        import io
        import wave
        c, b, h = req("/morse/audio.wav?text=" + urllib.parse.quote("Treffen um 15 Uhr") + "&wpm=15&lang=de", raw=True)
        ok(c == 200 and h.get("Content-Type", "").startswith("audio/wav") and "attachment" in h.get("Content-Disposition", "") and b[:4] == b"RIFF",
           f"«Als Audiodatei» in MoveEye: WAV als Download ({c}, {h.get('Content-Disposition', '')[:50]})")
        with wave.open(io.BytesIO(b)) as w_:
            sr_, pcm_ = w_.getframerate(), np.frombuffer(w_.readframes(w_.getnframes()), "<i2").astype(np.float64)
        f = os.path.join(tmp, "mw_wav.raw"); resample_poly(pcm_ / 32768.0, 320, 147).astype(np.float32).tofile(f)
        got = node(tmp, "decode", cf, GEHEIM, f, 48000); got0 = node(tmp, "decode", cf, "", f, 48000)
        ok(sr_ == 22050 and [t for t, _m in got] == ["TREFFEN UM 15 UHR"] and [t for t, _m in got0] == ["!nokey"],
           f"  MoveEyes Audiodatei -> «Audiodatei einlesen» der Seite: {got} (ohne Schlüssel {got0})")

        def post_raw(path, data, ctype="audio/wav"):
            r_ = urllib.request.Request(base + path, data=data, headers={"Authorization": "Basic " + base64.b64encode(f"{A[0]}:{A[1]}".encode()).decode(),
                                                                         "Content-Type": ctype})
            try:
                with op.open(r_, timeout=120) as x_:
                    return x_.status, json.loads(x_.read())
            except urllib.error.HTTPError as e_:
                return e_.code, json.loads(e_.read() or b"{}")
        fw_ = os.path.join(tmp, "seite.wav")
        node(tmp, "wav", json.dumps({"mode": "prot", "fA": 800, "fB": 1400, "wpm": 15, "auto": True, "sens": 10, "vol": 0.8}), GEHEIM, "Gruss vom Handy 73", "", fw_)
        c, j = post_raw("/api/morse/audio?lang=de", open(fw_, "rb").read())
        m = (j.get("state") or {}).get("rx", {}).get("msgs", [{}])[0]
        ok(c == 200 and j.get("found") == ["GRUSS VOM HANDY 73"] and m.get("src") == "file" and m.get("key") is True,
           f"Audiodatei der Seite (V2) -> «Audiodatei einlesen» in MoveEye: {j.get('found')} {m.get('src')} key {m.get('key')} ({j.get('error')})")
        c, j = post_raw("/api/morse/audio?lang=de", b"kein Ton" * 100, "application/octet-stream")
        ok(c == 400 and j.get("error"), f"  keine Audiodatei: abgelehnt, kein Absturz ({c} «{(j.get('error') or '')[:60]}»)")
        r_ = urllib.request.Request(base + "/api/morse/audio", data=b"RIFF", headers={"Authorization": "Basic " + base64.b64encode(b"Anna:anna-pass-1").decode()})
        try:
            c = op.open(r_, timeout=30).status
        except urllib.error.HTTPError as e_:
            c = e_.code
        ok(c == 403, f"  Audiodatei einlesen: nur der Administrator ({c})")
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
        c, b, h = req("/morse/audio.wav?text=SOS%20TEST&wpm=12", raw=True)
        c2, j = post_raw("/api/morse/audio?lang=de", b) if c == 200 else (c, {})
        ok(c == 200 and c2 == 200 and j.get("found") == ["SOS TEST"], f"Format Morse: Audiodatei hin und zurück ({c} {c2} {j.get('found')} {j.get('error')})")
        # Mehrton in MoveEye: Format, Baukasten prüfen, Lautsprecher -> Seite, Audiodatei hin und zurück, Mikrofon
        c, j = req("/api/morse", {"action": "funk", "mf": {"pid": 0, "custom": {"n": 8, "f0": 700, "df": 10, "T": 20, "g": 5}}, "lang": "de"})
        ok(c == 400 and "nah" in (j.get("error") or ""), f"Mehrton: unbrauchbarer Baukasten abgelehnt («{j.get('error')}»)")
        c, j = req("/api/morse", {"action": "funk", "fmt": "mfsk", "mf": {"pid": 2, "fec": 2}})
        mf_ = ((j.get("state") or {}).get("funk") or {}).get("mf") or {}
        ok(c == 200 and j["state"]["funk"]["fmt"] == "mfsk" and mf_.get("pid") == 2 and mf_.get("fec") == 2, f"Format «Mehrton», 8 Töne, stark ({c} {j.get('error')})")
        if os.path.exists(spk):
            os.remove(spk)
        time.sleep(6.0)
        c, j = req("/api/morse", {"action": "send", "text": "Grüsse vom Pi 73!", "outs": ["beep"], "wpm": 12})
        ok(c == 200 and j["state"]["tx"] and warte(lambda: not mst()["tx"], 90), f"Mehrton: senden über den Lautsprecher ({c} {j.get('error')})")
        time.sleep(1.0)
        pcm = np.fromfile(spk, dtype="<i2").astype(np.float64) if os.path.exists(spk) else np.zeros(16)
        x16 = resample_poly(pcm, 320, 441)
        r = mf_seite_hoert(tempfile.mkdtemp(prefix="mf_e_", dir=tmp), x16)
        ok(r == [("Grüsse vom Pi 73!", "")], f"  MoveEyes Lautsprecher -> Mehrton der Seite: {r}")
        c, b, h = req("/morse/audio.wav?text=" + urllib.parse.quote("Grüsse vom Pi 73!"), raw=True)
        c2, j = post_raw("/api/morse/audio?lang=de", b) if c == 200 else (c, {})
        m = ((j.get("state") or {}).get("rx") or {}).get("msgs", [{}])[0]
        ok(c == 200 and c2 == 200 and j.get("found") == ["Grüsse vom Pi 73!"] and m.get("fmt") == "mfsk" and m.get("src") == "file",
           f"  Mehrton-Audiodatei hin und zurück ({c} {c2} {j.get('found')} {m.get('fmt')})")
        x = mf_ton16(ns, "Hallo MoveEye, äöü!", 1, 1, "", seite=True, tmp=tmp)
        n0 = len(mst()["rx"]["msgs"])
        (np.clip(x * 3000 / 0.8 + np.random.default_rng(2).normal(0, 60, x.size), -32767, 32767)).astype("<i2").tofile(ton + ".tmp"); os.replace(ton + ".tmp", ton)
        ok(warte(lambda: len(mst()["rx"]["msgs"]) > n0, x.size / RATE + 20) and mst()["rx"]["msgs"][0]["text"] == "Hallo MoveEye, äöü!" and mst()["rx"]["msgs"][0]["fmt"] == "mfsk",
           f"  Seite (4 Töne, leicht) -> MoveEyes Mikrofon: «{mst()['rx']['msgs'][0]['text']}»")
        req("/api/morse", {"action": "funk", "fmt": "morse"})
        if browser:
            teil_g(base, PW, tmp, ns)
            teil_mg(base, PW, tmp, ns)
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


def teil_mg(base, pw, tmp, ns):
    """Mehrton im Browser: Modus-Wahl, Baukasten (Warnung), eine Datei mit Mehrton einlesen; Bilder nach FUNK_MF_SHOTS"""
    from playwright.sync_api import sync_playwright
    import wave
    shots = os.environ.get("FUNK_MF_SHOTS", "")
    if shots:
        os.makedirs(shots, exist_ok=True)
    x = mf_ton16(ns, "Treffen um 15 Uhr – bis gleich!", 2, 2, "", seite=False)
    fw_ = os.path.join(tmp, "mf.wav")
    with wave.open(fw_, "wb") as w_:
        w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(RATE); w_.writeframes((x * 32767).astype("<i2").tobytes())
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), lambda *a: http.server.SimpleHTTPRequestHandler(*a, directory=os.path.join(REPO, "funk")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    pwa = f"http://127.0.0.1:{srv.server_address[1]}/"
    with sync_playwright() as pw_:
        br = pw_.chromium.launch(args=["--no-proxy-server"])
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH")
        ctx.add_init_script("try{localStorage.setItem('morsefunk.lang',JSON.stringify('de'))}catch(e){}")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(pwa, wait_until="domcontentloaded"); pg.wait_for_timeout(800)
        pg.locator("#setBtn").click(); pg.locator("#mMf").click(); pg.wait_for_timeout(300)
        vis = pg.locator("#mfBox").is_visible() and not pg.locator("#twoBox").is_visible()
        sw = pg.evaluate("() => document.documentElement.scrollWidth")
        if shots:
            pg.screenshot(path=os.path.join(shots, "01_modus_mehrton.png"))
        pg.select_option("#sMfP", "0"); pg.wait_for_timeout(200)
        pg.locator("#kDf").fill("10"); pg.locator("#kDf").dispatch_event("change"); pg.wait_for_timeout(200)
        warn = pg.inner_text("#mfWarn") if pg.locator("#mfWarn").is_visible() else ""
        pg.locator("#kDf").fill("200"); pg.locator("#kDf").dispatch_event("change"); pg.wait_for_timeout(200)
        pg.locator("#kN").fill("6"); pg.locator("#kN").dispatch_event("change"); pg.wait_for_timeout(200)
        if shots:
            pg.locator("#kitBox").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(shots, "02_baukasten.png"))
        warn2 = pg.inner_text("#mfWarn") if pg.locator("#mfWarn").is_visible() else ""
        ok(vis and sw <= 391 and "zu nah" in warn and "Zweierpotenz" in warn2, f"Seite: Modus «Mehrton», Baukasten warnt («{warn[:50]}» / «{warn2[:40]}»), {sw} px")
        pg.select_option("#sMfP", "2"); pg.wait_for_timeout(200)
        pg.locator("#shSet [data-close]").first.click(); pg.wait_for_timeout(200)
        pg.set_input_files("#fileIn", fw_)
        try:
            pg.wait_for_function("() => JSON.parse(localStorage.getItem('morsefunk.hist')||'[]').some(h => h.mode === 'mfsk' && h.src === 'file')", timeout=60000)
            h = pg.evaluate("() => JSON.parse(localStorage.getItem('morsefunk.hist'))[0]")
        except Exception:
            h = {}
        ok(h.get("text") == "Treffen um 15 Uhr – bis gleich!", f"Seite: Mehrton-Datei eingelesen: «{h.get('text')}» ({h.get('mf')})")
        if shots:
            pg.screenshot(path=os.path.join(shots, "03_empfangen.png"))
            pg.locator("#histBtn").click(); pg.wait_for_timeout(400); pg.screenshot(path=os.path.join(shots, "04_verlauf.png"))
            pg.locator("#shHist [data-close]").first.click()
        pg.locator("#sendBtn").click(); pg.locator("#txIn").fill("Grüsse aus Zürich!"); pg.wait_for_timeout(1500)
        prev = pg.inner_text("#txPrev")
        ok("s" in prev and "Grüsse aus Zürich!" in prev, f"Seite: Mehrton-Vorschau mit Dauer («{prev}»)")
        if shots:
            pg.screenshot(path=os.path.join(shots, "05_senden.png"))
        ok(not errs, f"Seite Mehrton: keine JavaScript-Fehler {errs[:2]}")
        ctx.close()
        if shots:
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": pw}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"settings\"]')}catch(e){}")
            pg = ctx.new_page(); pg.goto(base + "/morse", wait_until="domcontentloaded"); pg.wait_for_selector("#mo-fmt-seg button", timeout=20000)
            try:
                with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                    pg.evaluate("k => { langSet(k); }", "de")
            except Exception:
                pass
            pg.wait_for_selector("#mo-fmt-seg button", timeout=20000)
            pg.locator("#mo-f-mfsk").click(); pg.wait_for_timeout(1200)
            pg.locator("#mo-fmt").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(shots, "06_moveeye_mehrton.png"))
            pg.select_option("#mo-mf-p", "0"); pg.wait_for_timeout(1200)
            pg.locator("#mo-mf-kit").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(shots, "07_moveeye_baukasten.png"))
            pg.select_option("#mo-mf-p", "2"); pg.wait_for_timeout(600)
            pg.evaluate("() => fetch('/api/morse', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'funk', fmt: 'morse'})})")
            ctx.close()
        br.close()
    srv.shutdown()


def teil_g(base, pw, tmp, ns):
    """die Seiten bei 390 px in 5 Sprachen (mit den Schriften, die FONTCONFIG_FILE wählt), Weg zurück, kein waagrechtes Scrollen;
    seine Seite als PWA (funk/) und mit einem «Mikrofon» (Chromium spielt eine WAV-Datei als Mikrofon): sie liest MoveEyes Ton"""
    from playwright.sync_api import sync_playwright
    from scipy.signal import resample_poly
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
        ctx.close()
        # iPhone: getUserMedia zuerst (vor dem AudioContext), bei TypeError ein zweiter Versuch mit {audio:true}, Fehler mit Name + Meldung
        for art in ("einmal", "immer"):
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="de-CH")
            ctx.grant_permissions(["microphone"])
            ctx.add_init_script("""(() => { const md = navigator.mediaDevices, g = md.getUserMedia.bind(md); window.__gum = [];
              md.getUserMedia = c => { window.__gum.push([JSON.stringify(c), !!window.__ctxDa]);
                if ('%s' === 'immer' || typeof c.audio === 'object') return Promise.reject(new TypeError('Type error')); return g(c); };
              const A = window.AudioContext; window.AudioContext = function(o) { window.__ctxDa = true; return new A(o); }; })();""" % art)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(pwa, wait_until="domcontentloaded"); pg.wait_for_timeout(500)
            pg.locator("#listen").click(); pg.wait_for_timeout(1500)
            gum, live, msg = pg.evaluate("() => window.__gum"), pg.evaluate("() => document.getElementById('listen').classList.contains('live')"), pg.inner_text("#msg")
            if art == "einmal":
                ok(len(gum) == 2 and not gum[0][1] and gum[1][0] == '{"audio":true}' and live and not msg and not errs,
                   f"iPhone: Mikrofon vor dem AudioContext, nach TypeError zweiter Versuch {{audio:true}}: hört ({gum}, «{msg[:40]}»)")
            else:
                ok(len(gum) == 2 and not live and "TypeError: Type error" in msg and "audio:true" in msg and not errs,
                   f"iPhone: geht es gar nicht, steht der Fehler mit Name und Meldung da («{msg[-60:]}»)")
            ctx.close()
        # V2 + Audiodateien im Browser: «Als Audiodatei» (ohne Teilen-Blatt: Herunterladen), «Audiodatei einlesen» (📁 im Verlauf)
        shots = os.environ.get("FUNK_SHOTS", "")
        if shots:
            os.makedirs(shots, exist_ok=True)
        fw_ = os.path.join(tmp, "g_v2.wav")
        node(tmp, "wav", json.dumps({"mode": "prot", "fA": 800, "fB": 1400, "wpm": 12, "auto": True, "sens": 10, "vol": 0.8}), "geheim", "Treffen um 15 Uhr", "", fw_)
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH", accept_downloads=True)
        ctx.add_init_script("try{localStorage.setItem('morsefunk.key',JSON.stringify('geheim'));localStorage.setItem('morsefunk.lang',JSON.stringify('de'))}catch(e){}")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(pwa, wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
        pg.locator("#sendBtn").click(); pg.locator("#txIn").fill("Treffen um 15 Uhr"); pg.wait_for_timeout(1200)
        if shots:
            pg.screenshot(path=os.path.join(shots, "01_senden_als_audiodatei.png"))
        try:
            with pg.expect_download(timeout=20000) as dl:
                pg.locator("#txWav").click()
            d_ = os.path.join(tmp, "g_dl.wav"); dl.value.save_as(d_)
            import wave
            with wave.open(d_) as w_:
                okw = w_.getframerate() == 22050 and w_.getnchannels() == 1 and w_.getsampwidth() == 2
                pcm_ = np.frombuffer(w_.readframes(w_.getnframes()), "<i2").astype(np.float64)
            got = me_hoert(ns, resample_poly(pcm_, 320, 441), "geheim", 12)
            name_ = dl.value.suggested_filename
        except Exception as e_:
            okw, got, name_ = False, [str(e_)[:80]], ""
        ok(okw and got == ["TREFFEN UM 15 UHR"] and name_.endswith(".wav"), f"Seite «Als Audiodatei» (V2): {name_} -> MoveEye liest {got}")
        pg.locator("#shSend [data-close]").first.click(); pg.wait_for_timeout(300)
        pg.set_input_files("#fileIn", fw_)
        try:
            pg.wait_for_function("() => JSON.parse(localStorage.getItem('morsefunk.hist')||'[]').some(h => h.src === 'file' && h.text === 'TREFFEN UM 15 UHR' && h.key)", timeout=60000)
            gel = True
        except Exception:
            gel = False
        msg = pg.inner_text("#msg")
        ok(gel and "TREFFEN UM 15 UHR" in msg, f"Seite «Audiodatei einlesen» (V2, Schlüssel): «{msg[:60]}»")
        if shots:
            pg.screenshot(path=os.path.join(shots, "02_datei_gelesen.png"))
            pg.locator("#histBtn").click(); pg.wait_for_timeout(400); pg.screenshot(path=os.path.join(shots, "03_verlauf_aus_datei.png"))
            pg.locator("#shHist [data-close]").first.click(); pg.wait_for_timeout(200)
        pg.locator("#keyBtn").click(); pg.locator("#keyIn").fill("falsch"); pg.locator("#keySave").click(); pg.wait_for_timeout(1500)   # (der Schlüssel wie der Bediener)
        pg.set_input_files("#fileIn", fw_)
        try:
            pg.wait_for_function("() => JSON.parse(localStorage.getItem('morsefunk.hist')||'[]')[0].bad === 'bad'", timeout=60000)
            fal = True
        except Exception:
            fal = False
        ok(fal and "falscher Schlüssel" in pg.inner_text("#msg"), f"  mit falschem Schlüssel: «{pg.inner_text('#msg')[:60]}»")
        ok(not errs, f"  V2 / Audiodateien: keine JavaScript-Fehler {errs[:2]}")
        ctx.close()
        if shots:                                            # MoveEye: Mehr -> Morse, die Knöpfe für Audiodateien
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": pw}, locale="de-CH")
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"settings\"]')}catch(e){}")
            pg = ctx.new_page(); pg.goto(base + "/morse", wait_until="domcontentloaded"); pg.wait_for_selector("#mo-fmt-seg button", timeout=20000)
            pg.evaluate("""async () => { for (const b of [{action: 'funk', fmt: 'prot'}, {action: 'key', key: 'geheim'}])
              await fetch('/api/morse', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(b)}); }""")
            try:
                with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                    pg.evaluate("k => { langSet(k); }", "de")
            except Exception:
                pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector("#mo-fmt-seg button", timeout=20000); pg.wait_for_timeout(800)
            pg.locator("#mo-text").fill("Treffen um 15 Uhr"); pg.wait_for_timeout(1200)
            pg.locator("#mo-send").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(shots, "04_moveeye_morse_audiodatei.png"))
            pg.set_input_files("#mo-file", fw_)
            try:
                pg.wait_for_function("() => document.getElementById('mo-file-r').textContent.length > 20", timeout=60000)
            except Exception:
                pass
            pg.locator("#mo-file-r").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(shots, "05_moveeye_datei_gelesen.png"))
            ctx.close()
        br.close()
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
    ap.add_argument("--mfsk-messen", action="store_true")
    a = ap.parse_args()
    if not shutil.which("node"):
        print("node fehlt"); return 1
    datei = a.datei or neueste()
    home = tempfile.mkdtemp(prefix="mw_funk_a_"); tmp = tempfile.mkdtemp(prefix="mw_funk_t_")
    t0 = time.time()
    try:
        ns = lade(datei, home)
        mt = morse_test_modul()
        if a.mfsk_messen:
            mf_messen(ns, mt, tmp, a.tabelle, a.laeufe); return 0
        if a.messen:
            messen(ns, mt, tmp, a.tabelle, a.laeufe); return 0
        teil_a(ns); teil_b(ns, tmp); teil_c(ns, mt, tmp); teil_d(ns, mt, tmp); teil_m(ns, mt, tmp)
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
