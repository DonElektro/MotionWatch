#!/usr/bin/env python3
"""Spielton bauen (Daniel 01.11.2026: «Ton in den Spielen»).

Baut die Klänge für Spiele und Geschichten (scripts/klang.gd) aus freien Aufnahmen (alle CC0, Liste in
simulator3d/klang/LIZENZEN.txt, Abschnitt «Spielton») und legt sie als Ogg Vorbis ab:
  simulator3d/klang/sp_<name>.ogg      (nur für den Simulator; der Browser braucht sie nicht)
  simulator3d/klang/spielton.json      Länge, Schleife, Pegel (LUFS, Spitze) und «db» = Ausgleich der Lautheit
  simulator3d/klang/sp_<name>.ogg.import   (importer="keep": Godot liest die Datei roh, wie klang/*.ogg)

  python3 werkzeuge/spielton_bauen.py --quellen /pfad/zu/den/klonen [--nur name,name]

--quellen: derselbe Ordner wie bei klang_bauen.py (dessen QUELLEN) plus «sgossner_VCSL» (Kleine Trommel, Becken).
Zusätzlich gebrauchte Dateien (mit «git checkout HEAD -- <pfad>» in den Klonen holen, die Klone sind «blob:none»):
  sgossner_VSCO-2-CE:   Strings/Harp, Woodwinds/Flute/susvib, Percussion/Marimba, Brass/Trumpet/stac, Brass/Trumpet/sus
  sgossner_VCSL:        Membranophones/Struck Membranophones/Snare Drum, Modern 1, Idiophones/Struck Idiophones/Clash Cymbals 1
  lavenderdotpet_…:     kenney_impactsounds, kenney_interfacesounds, Micro Pack - Record Fuzzies, 100-CC0-wood-metal-SFX
Braucht klang_bauen.py (gleicher Ordner: Hall, Schleifen, Stichproben), numpy, scipy, ffmpeg (libvorbis).
Alle Zufallswerte fest: derselbe Lauf gibt dieselben Klänge.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import klang_bauen as K  # noqa: E402

SR = K.SR
ZIEL = os.path.join(os.path.dirname(HIER), "simulator3d", "klang")
VS = K.VS
LV = K.LV
VC = "sgossner_VCSL/"
KEN_I = LV + "kenney_impactsounds/Audio/"
KEN_UI = LV + "kenney_interfacesounds/Audio/"
KEN_R = K.KEN_R


def P(rel):
    return os.path.join(K.Q, rel)


# ---- saving ----------------------------------------------------------------------------------------------------------------
def speichern(name, x, loop=False, q=None, mono_=False):
    """float (n,) / (n,2) -> klang/sp_<name>.ogg (peak at most -1 dBFS), and the .import file (keep)"""
    x = np.asarray(x, dtype=np.float32)
    if mono_:
        x = K.mono(x)
    ch = 1 if x.ndim == 1 else 2
    pk = np.abs(x).max()
    if pk > 0.891:
        x = x * (0.891 / pk)
    if not loop:
        x = x.copy()
        k = min(len(x), int(0.004 * SR))
        x[-k:] *= np.linspace(1, 0, k)[:, None] if ch == 2 else np.linspace(1, 0, k)
    out = os.path.join(ZIEL, "sp_" + name + ".ogg")
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, "x.f32")
        x.astype(np.float32).tofile(w)
        qq = q if q is not None else (1 if ch == 2 else 2)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-i", w,
                        "-c:a", "libvorbis", "-q:a", str(qq), out], check=True)
    with open(out + ".import", "w") as f:
        f.write('[remap]\n\nimporter="keep"\n')
    return len(x) / SR


# ---- a small sampler on the VSCO-2 CE / VCSL instruments (pitch measured, the name only for the octave) ------------------------
_lib = {}


def _tok(nm):
    for t in nm.replace(".wav", "").split("_"):
        if t[:1] in "ABCDEFG" and any(c.isdigit() for c in t) and len(t) <= 3:
            return t
    return None


def f0_kurz(x):
    """the fundamental from the first 0.5 s (struck / plucked notes decay; K.f0 looks at the middle)"""
    y = K.mono(x)
    on = int(np.argmax(np.abs(y) > 0.1 * np.abs(y).max()))
    s = y[on + int(0.03 * SR): on + int(0.6 * SR)]
    if len(s) < 2048:
        s = y[: int(0.6 * SR)]
    s = s * np.hanning(len(s))
    N = 1 << 18
    X = np.abs(np.fft.rfft(s, N))
    f = np.fft.rfftfreq(N, 1 / SR)
    hps = X.copy()
    for k in (2, 3):
        d = X[::k]
        hps[: len(d)] *= d
    m = (f > 40) & (f < 4500)
    return float(f[m][np.argmax(hps[m])])


INSTR = {"harp": ("Strings/Harp", "*.wav", "kurz"), "flute": ("Woodwinds/Flute/susvib", "*_v1_1.wav", "lang"),
         "marimba": ("Percussion/Marimba", "*.wav", "kurz"), "trp_stac": ("Brass/Trumpet/stac", "*_v3_rr1.wav", "kurz"),
         "trp": ("Brass/Trumpet/sus", "*_v3_rr1.wav", "lang"), "horn_k": ("Brass/F Horn/sus", "*_v3_1.wav", "lang")}


def lib(art):
    if art in _lib:
        return _lib[art]
    if art in ("cello", "viola", "violin", "bass", "horn", "tbn", "tuba"):
        _lib[art] = K.bibliothek(art)
        return _lib[art]
    folder, pat, kind = INSTR[art]
    roh = []
    for p in sorted(glob.glob(os.path.join(K.Q, VS, folder, pat))):
        t = _tok(os.path.basename(p))
        if not t:
            continue
        x = K.lade(p)
        named = K.hz(t)
        meas = f0_kurz(x) if kind == "kurz" else K.f0(x)
        roh.append((named, meas, p, x))
    # the octave of the names is the same for one instrument: the most frequent offset (0 or 12 semitones) counts;
    # a measurement more than 0.7 semitones off the name (an octave error, a sub harmonic) is replaced by the name
    offs = [int(round(12 * np.log2(m / n) / 12.0)) * 12 for n, m, _, _ in roh]
    oct_ = max(set(offs), key=offs.count) if offs else 12
    res = []
    for named, meas, p, x in roh:
        soll = named * 2 ** (oct_ / 12.0)
        f = meas if abs(12 * np.log2(meas / soll)) < 0.7 else soll
        res.append((f, p, x))
    _lib[art] = res
    return res


def note(art, n, max_shift=7.0):
    """sample of instrument art at note n ('C5' or Hz), the nearest recorded note resampled"""
    f = K.hz(n) if isinstance(n, str) else float(n)
    L = lib(art)
    best = min(L, key=lambda e: abs(np.log2(e[0] / f)))
    return K.resample(best[2], f / best[0])


def glock(n):
    gl = {}
    for p in glob.glob(os.path.join(K.Q, VS, "Percussion/Glock/*.wav")):
        nm = os.path.basename(p).split("_")[-1][:-4]
        gl[K.hz(nm) * 2] = p
    f = K.hz(n)
    src = min(gl, key=lambda q: abs(np.log2(q / f)))
    x = K.lade(gl[src])
    meas = K.f0(x[: int(0.6 * SR)])
    ratio = f / (meas if abs(np.log2(meas / src)) < 0.6 else src)
    return K.filt0(K.resample(x, ratio), "high", 300.0)          # (the recordings hum a little below)


def huelle_ar(n, att, rel, total):
    """attack / release envelope over n samples (hold in between); total = length of the note incl. release"""
    e = np.ones(n)
    a = max(1, int(att * SR))
    r = max(1, int(rel * SR))
    e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if r < n:
        e[-r:] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def gestrichen(art, n, dauer, att=0.5, rel=0.9, seed=0):
    """a held string / wind note of any length (grains from the steady part), soft attack and release"""
    s = note(art, n)
    m = int((dauer + rel) * SR)
    h = K.halten(K.st(s), m, seed=seed)
    return h * huelle_ar(m, att, rel, dauer)[:, None]


def kurz(art, n, dauer=None, rel=0.25):
    s = K.st(note(art, n))
    if dauer is not None and len(s) > int(dauer * SR):
        s = K.kuerzen(s, dauer, rel)
    return s


def zirkular_hall(x, rt, wet, seed):
    return K.hall(x, rt, wet, pre=0.02, hf=6000.0, circular=True, breite=1.2, seed=seed)


# ---- music moments ----------------------------------------------------------------------------------------------------------
def fund():
    """Fund: a quick glockenspiel arpeggio up (G5 C6 E6 G6 C7), a light shimmer"""
    out = np.zeros((int(3.2 * SR), 2))
    for k, (nn, at, g, p) in enumerate((("G5", 0.0, 0.75, -0.4), ("C6", 0.075, 0.8, -0.2), ("E6", 0.15, 0.85, 0.0),
                                        ("G6", 0.225, 0.8, 0.2), ("C7", 0.30, 0.9, 0.4))):
        y = K.mono(glock(nn))
        K.setze(out, K.pan(y, p), int(at * SR), g)
    out = K.hall(out, 2.2, 0.45, pre=0.015, hf=9000.0, breite=1.3, seed=21)
    return K.kuerzen(K.auf_spitze(out, -3.0), 3.0, 1.0)


def fanfare():
    """Rätsel gelöst: a small trumpet fanfare (G4 G4 G4 C5 —) with a second voice, a timpani at the end"""
    out = np.zeros((int(3.6 * SR), 2))
    t = [0.0, 0.13, 0.26, 0.42]
    lead = ["G4", "G4", "G4", "C5"]
    zweit = ["E4", "E4", "E4", "G4"]
    for k in range(4):
        last = k == 3
        for voice, g, pn in ((lead, 1.0, -0.15), (zweit, 0.6, 0.2)):
            if last:
                s = gestrichen("trp", voice[k], 1.15, att=0.02, rel=0.55, seed=k + (5 if g < 1 else 0))
            else:
                s = kurz("trp_stac", voice[k], 0.16, 0.06)
            K.setze(out, K.pan(K.mono(s), pn), int(t[k] * SR), g * (1.1 if last else 0.85))
    tp, _ = K.timpani(65.41)                          # C2
    K.setze(out, K.st(K.kuerzen(K.auf_spitze(tp, -8.0), 2.0, 0.8)), int(t[3] * SR), 1.0)
    out = K.filt0(out, "high", 70.0)
    out = K.hall(out, 1.8, 0.35, pre=0.02, hf=7000.0, seed=22)
    return K.kuerzen(K.auf_spitze(out, -3.0), 3.4, 0.9)


def kapitel():
    """Kapitel geschafft: strings, Bb (IV) swells into F (I), a harp glissando up at the start"""
    n = int(6.4 * SR)
    out = np.zeros((n, 2))
    for k, nn in enumerate(["C4", "D4", "E4", "F4", "G4", "A4", "Bb4", "C5", "D5", "E5", "F5"]):
        nn = nn.replace("Bb", "A#")
        s = K.mono(kurz("harp", nn, 1.6, 0.6))
        K.setze(out, K.pan(s, -0.5 + k * 0.09), int(k * 0.045 * SR), 0.55)
    akk1 = [("bass", "A#1"), ("cello", "F2"), ("viola", "D4"), ("violin", "F4"), ("violin", "A#4")]
    akk2 = [("bass", "F1"), ("cello", "C3"), ("viola", "A3"), ("violin", "F4"), ("violin", "C5")]
    for j, (art, nn) in enumerate(akk1):
        s = gestrichen(art, nn, 1.55, att=0.35, rel=0.5, seed=40 + j)
        K.setze(out, s, int(0.35 * SR), 0.5 if art != "bass" else 0.6)
    for j, (art, nn) in enumerate(akk2):
        s = gestrichen(art, nn, 2.6, att=0.25, rel=1.6, seed=50 + j)
        K.setze(out, s, int(1.85 * SR), 0.55 if art != "bass" else 0.65)
    out = K.filt0(out, "high", 40.0)
    out = K.hall(out, 3.0, 0.5, pre=0.03, hf=5500.0, breite=1.2, seed=23)
    return K.kuerzen(K.auf_spitze(out, -3.0), 6.4, 1.6)


def snare(pat):
    fs = sorted(glob.glob(os.path.join(K.Q, VC, "Membranophones/Struck Membranophones/Snare Drum, Modern 1", pat)))
    return K.lade(fs[0])


def tusch():
    """Überraschung: a snare roll grows for 1.3 s, then crash cymbal + brass chord (trumpets C-E-G, horns) + timpani"""
    out = np.zeros((int(4.6 * SR), 2))
    roll = snare("Snare2_rollSN_v4_rr1_Mid.wav")
    rl = K.halten(K.st(roll), int(1.35 * SR), seed=61, grain=0.35)
    cres = np.linspace(0.12, 1.0, len(rl)) ** 1.6
    K.setze(out, rl * cres[:, None], 0, 0.8)
    hit = int(1.32 * SR)
    cr = sorted(glob.glob(os.path.join(K.Q, VC, "Idiophones/Struck Idiophones/Clash Cymbals 1", "cymbal_crash1_ff2.wav")))
    if cr:
        c = K.lade(cr[0])
        K.setze(out, K.kuerzen(K.auf_spitze(c, -6.0), 2.8, 1.4), hit, 0.75)
    for j, (art, nn, g, pn) in enumerate((("trp", "C5", 0.9, -0.2), ("trp", "E5", 0.7, 0.2), ("trp", "G4", 0.75, 0.0),
                                          ("horn_k", "C4", 0.7, -0.3), ("horn_k", "G3", 0.6, 0.3), ("tbn", "C3", 0.55, 0.0))):
        try:
            s = gestrichen(art, nn, 0.9, att=0.015, rel=0.7, seed=70 + j)
        except Exception:
            continue
        K.setze(out, K.pan(K.mono(s), pn), hit, g)
    k = K.lade(VS + "Percussion/BDrumNewhit_v5_rr1_Sum.wav")
    K.setze(out, K.st(K.filt0(K.auf_spitze(k, -6.0), "low", 1500.0)), hit, 0.6)
    out = K.filt0(out, "high", 50.0)
    out = K.hall(out, 2.2, 0.35, pre=0.02, hf=7000.0, seed=24)
    return K.kuerzen(K.auf_spitze(out, -3.0), 4.4, 1.4)


def wirbel(L_s=4.0):
    """Spannung: a soft snare roll as a seamless loop (grains of a real roll)"""
    roll = snare("Snare2_rollSN_v2_rr1_Mid.wav")
    L = int(L_s * SR)
    xf = int(0.4 * SR)
    h = K.halten(K.st(roll), L + xf, seed=62, grain=0.3)
    y = K.schleife(h, L, xf)
    y = K.filt_rund(y, "high", 120.0)
    y = K.filt_rund(y, "low", 7000.0)
    return K.auf_rms(y, -26.0)


def puls(bpm=72.0, takte=2):
    """Spannung: a heartbeat-like pulse (soft bass drum + muted timpani: «lub-dub»), seamless (whole bars)"""
    beat = 60.0 / bpm
    L = int(round(SR * beat * 4 * takte))
    out = np.zeros((L, 2))
    k = K.lade(VS + "Percussion/BDrumNewhit_v3_rr1_Sum.wav")
    k = K.filt0(K.auf_spitze(k, -3.0), "low", 600.0)
    tp, _ = K.timpani(55.0, weich=True)
    tp = K.kuerzen(K.auf_spitze(tp, -6.0), 1.2, 0.6)
    for b in range(4 * takte):
        at = b * beat * SR
        K.setze_rund(out, K.st(k), at, 0.9)
        K.setze_rund(out, K.st(k), at + 0.22 * SR, 0.55)
        if b % 2 == 0:
            K.setze_rund(out, K.st(tp), at, 0.35)
    out = K.filt_rund(out, "low", 900.0)
    out = K.hall(out, 1.2, 0.25, circular=True, seed=63)
    return K.auf_rms(out, -24.0)


# ---- background music (loops, quiet): seasons and the lake -----------------------------------------------------------------
def _musik(name, bpm, akkorde, schichten, seed, takte_je=2, hell=0.5):
    """a seamless loop: chords (each takte_je bars of 4 beats), every layer renders into a circular buffer, circular hall"""
    beat = 60.0 / bpm
    bar = 4 * beat
    L = int(round(SR * bar * takte_je * len(akkorde)))
    out = np.zeros((L, 2))
    r = np.random.default_rng(seed)
    for ci, ak in enumerate(akkorde):
        t0 = ci * bar * takte_je
        for lay in schichten:
            lay(out, t0, bar * takte_je, beat, ak, ci, r)
    out = K.filt_rund(out, "high", 45.0)
    out = K.filt_rund(out, "low", 3500.0 + 5000.0 * hell)
    out = zirkular_hall(out, 2.6, 0.45, seed)
    return K.auf_rms(out, -24.0)


def L_pad(arten, g=0.35, att=0.9, rel=1.4):
    def f(out, t0, dur, beat, ak, ci, r):
        for j, nn in enumerate(ak["pad"]):
            art = arten[min(j, len(arten) - 1)]
            s = gestrichen(art, nn, dur, att=att, rel=rel, seed=ci * 13 + j)
            K.setze_rund(out, s, t0 * SR, g)
    return f


def L_arp(art, muster, g=0.4, schritt=0.5, dauer=1.6, pan=0.3):
    """an arpeggio: muster = indices into ak['arp'] per step (schritt in beats)"""
    def f(out, t0, dur, beat, ak, ci, r):
        n = int(round(dur / (schritt * beat)))
        for i in range(n):
            idx = muster[i % len(muster)]
            if idx is None:
                continue
            nn = ak["arp"][idx % len(ak["arp"])]
            s = K.mono(kurz(art, nn, dauer, 0.5))
            v = g * (1.0 if i % 4 == 0 else 0.75) * r.uniform(0.85, 1.05)
            K.setze_rund(out, K.pan(s, (pan if i % 2 else -pan) * r.uniform(0.5, 1.0)), (t0 + i * schritt * beat) * SR, v)
    return f


def L_mel(art, g=0.3, lang=True):
    """a melody: ak['mel'] = [(beat, note, beats), …] inside the chord's time"""
    def f(out, t0, dur, beat, ak, ci, r):
        for (b, nn, d) in ak.get("mel", []):
            if lang:
                s = gestrichen(art, nn, d * beat, att=0.12, rel=0.6, seed=ci * 7 + int(b * 4))
            else:
                s = kurz(art, nn, max(0.6, d * beat + 0.8), 0.6)
            K.setze_rund(out, K.pan(K.mono(s), 0.15), (t0 + b * beat) * SR, g)
    return f


def L_bass(art, g=0.35):
    def f(out, t0, dur, beat, ak, ci, r):
        for b in (0.0, 4.0):
            s = K.mono(kurz(art, ak["bass"], 3.0, 1.0))
            K.setze_rund(out, K.st(s), (t0 + b * beat) * SR, g)
    return f


def fruehling():
    A = [{"pad": ["F3", "A3", "C4"], "arp": ["F3", "C4", "F4", "A4", "C5", "A4"], "bass": "F2",
          "mel": [(2.0, "A5", 2.0), (4.0, "C6", 3.0)]},
         {"pad": ["D3", "F3", "A3"], "arp": ["D3", "A3", "D4", "F4", "A4", "F4"], "bass": "D2",
          "mel": [(1.0, "A5", 1.0), (2.0, "F5", 2.0), (5.0, "D5", 2.5)]},
         {"pad": ["A#2", "D3", "F3"], "arp": ["A#2", "F3", "A#3", "D4", "F4", "D4"], "bass": "A#1",
          "mel": [(2.0, "D5", 1.0), (3.0, "F5", 1.0), (4.0, "A#5", 3.0)]},
         {"pad": ["C3", "E3", "G3"], "arp": ["C3", "G3", "C4", "E4", "G4", "E4"], "bass": "C2",
          "mel": [(2.0, "G5", 2.0), (4.0, "E5", 3.5)]}]
    return _musik("fruehling", 72.0, A, [L_pad(["cello", "viola", "viola"], 0.22), L_arp("harp", [0, 1, 2, 3, 4, 5, 3, 2], 0.42),
                                          L_mel("flute", 0.28)], seed=101, hell=0.6)


def sommer():
    A = [{"pad": ["C3", "G3", "E4"], "arp": ["C4", "E4", "G4", "C5", "E5"], "bass": "C2",
          "mel": [(0.0, "G5", 1.5), (2.0, "E5", 1.0), (3.0, "G5", 1.0), (4.0, "C6", 3.0)]},
         {"pad": ["A2", "E3", "C4"], "arp": ["A3", "C4", "E4", "A4", "C5"], "bass": "A1",
          "mel": [(0.0, "E5", 2.0), (2.0, "C5", 1.0), (4.0, "A5", 3.0)]},
         {"pad": ["F2", "C3", "A3"], "arp": ["F3", "A3", "C4", "F4", "A4"], "bass": "F1",
          "mel": [(0.0, "A5", 1.5), (2.0, "C6", 1.0), (3.0, "A5", 1.0), (4.0, "F5", 3.0)]},
         {"pad": ["G2", "D3", "B3"], "arp": ["G3", "B3", "D4", "G4", "B4"], "bass": "G1",
          "mel": [(0.0, "D5", 2.0), (2.0, "G5", 2.0), (4.0, "B5", 3.0)]}]
    return _musik("sommer", 80.0, A, [L_pad(["cello", "viola", "violin"], 0.2), L_arp("marimba", [0, 2, 1, 3, 2, 4, 3, 1], 0.38),
                                       L_mel("flute", 0.22), L_bass("harp", 0.3)], seed=102, hell=0.7)


def herbst():
    A = [{"pad": ["A2", "E3", "C4"], "arp": ["A2", "E3", "A3", "C4", "E4"], "bass": "A1",
          "mel": [(0.0, "E4", 2.0), (2.0, "C4", 2.0), (4.0, "A3", 4.0)]},
         {"pad": ["F2", "C3", "A3"], "arp": ["F2", "C3", "F3", "A3", "C4"], "bass": "F1",
          "mel": [(0.0, "C4", 2.0), (2.0, "A3", 2.0), (4.0, "F3", 3.5)]},
         {"pad": ["C3", "G3", "E4"], "arp": ["C3", "G3", "C4", "E4", "G4"], "bass": "C2",
          "mel": [(0.0, "G4", 2.0), (2.0, "E4", 2.0), (4.0, "C4", 3.5)]},
         {"pad": ["E2", "B2", "G#3"], "arp": ["E2", "B2", "E3", "G#3", "B3"], "bass": "E1",
          "mel": [(0.0, "B3", 3.0), (4.0, "G#3", 3.5)]}]
    return _musik("herbst", 66.0, A, [L_pad(["cello", "viola", "viola"], 0.3), L_arp("harp", [0, 1, 2, 3, 4, 3, 2, 1], 0.36, 1.0, 2.2),
                                       L_mel("cello", 0.2)], seed=103, hell=0.35)


def winter():
    A = [{"pad": ["D3", "A3", "F#4"], "arp": ["D6", "A6", "F#6", "E6"], "bass": "D2"},
         {"pad": ["G2", "D3", "B3"], "arp": ["B5", "D6", "G6", "F#6"], "bass": "G1"},
         {"pad": ["B2", "F#3", "D4"], "arp": ["F#6", "D6", "B5", "C#6"], "bass": "B1"},
         {"pad": ["A2", "E3", "C#4"], "arp": ["E6", "C#6", "A5", "E6"], "bass": "A1"}]

    def gl(out, t0, dur, beat, ak, ci, r):
        for i, b in enumerate((0.0, 1.5, 3.0, 5.0, 6.5)):
            nn = ak["arp"][i % 4]
            s = K.mono(glock(nn))
            K.setze_rund(out, K.pan(s, r.uniform(-0.6, 0.6)), (t0 + b * beat) * SR, 0.22 * r.uniform(0.7, 1.0))
    return _musik("winter", 60.0, A, [L_pad(["viola", "violin", "violin"], 0.24, 1.4, 2.0), gl, L_bass("harp", 0.32)],
                  seed=104, hell=0.55)


def see():
    A = [{"pad": ["G2", "D3", "B3"], "arp": ["G3", "B3", "D4", "G4", "B4"], "bass": "G1",
          "mel": [(0.0, "D5", 1.0), (1.0, "G5", 1.0), (2.0, "B5", 2.0), (4.0, "A5", 1.0), (5.0, "G5", 2.0)]},
         {"pad": ["E2", "B2", "G3"], "arp": ["E3", "G3", "B3", "E4", "G4"], "bass": "E1",
          "mel": [(0.0, "G5", 2.0), (2.0, "E5", 2.0), (4.0, "B4", 3.0)]},
         {"pad": ["C3", "G3", "E4"], "arp": ["C4", "E4", "G4", "C5", "E5"], "bass": "C2",
          "mel": [(0.0, "E5", 1.0), (1.0, "G5", 1.0), (2.0, "C6", 2.0), (4.0, "B5", 1.0), (5.0, "A5", 2.0)]},
         {"pad": ["D3", "A3", "F#4"], "arp": ["D4", "F#4", "A4", "D5", "F#5"], "bass": "D2",
          "mel": [(0.0, "F#5", 2.0), (2.0, "A5", 2.0), (4.0, "D5", 3.0)]}]
    return _musik("see", 84.0, A, [L_pad(["cello", "viola", "violin"], 0.16), L_arp("marimba", [0, 2, 4, 2, 1, 3, 4, 3], 0.32),
                                    L_arp("harp", [0, None, None, None, 2, None, None, None], 0.3, 0.5, 2.0, 0.1),
                                    L_mel("flute", 0.2)], seed=105, hell=0.75)


# ---- surroundings --------------------------------------------------------------------------------------------------------
def schritte(art):
    """4 steps in 0.5-s slots (klang.gd plays one slot per step): gras / kies / schnee"""
    slot = int(0.5 * SR)
    out = np.zeros(slot * 4)
    if art == "gras":
        fs = [P(KEN_I + "footstep_grass_%03d.ogg" % i) for i in (0, 1, 2, 4)]
    elif art == "schnee":
        fs = [P(KEN_I + "footstep_snow_%03d.ogg" % i) for i in (0, 1, 2, 3)]
    else:
        fs = [P(KEN_R + "footstep_%d.ogg" % i) for i in (1, 3, 6, 8)]
        if not os.path.exists(fs[0]):
            alt = os.path.join(K.Q, "kenney-rpg-audio-for-godot/src/addons/kenney rpg audio/")
            fs = [alt + "footstep_%d.ogg" % i for i in (1, 3, 6, 8)]
    for k, f in enumerate(fs):
        y = K.lade(f, mono=True)
        on = int(np.argmax(np.abs(y) > 0.05 * np.abs(y).max()))
        y = y[max(0, on - int(0.003 * SR)):][: slot - int(0.02 * SR)]
        y = K.auf_spitze(y, -4.0)
        n = len(y)
        fade = min(n, int(0.05 * SR))
        y[-fade:] *= np.linspace(1, 0, fade)
        out[k * slot: k * slot + n] += y
    out = K.filt0(out, "high", 90.0)
    return out


def feuer(L_s=9.0):
    """crackling camp fire as a loop: low roar with flicker (own synthesis) + crackles (record crackle, CC0) + wood pops"""
    L = int(L_s * SR)
    r = np.random.default_rng(91)
    roar = K.fft_band(L, 60.0, 900.0, tilt=-6.0, seed=92, ch=1)
    fl = 0.65 + 0.2 * K.per_lfo(L, 7, 0.3) + 0.15 * K.per_lfo(L, 17, 1.1)
    out = roar * fl * 0.18
    fz = glob.glob(os.path.join(K.Q, LV, "Micro Pack - Record Fuzzies", "Big Crackle.wav"))
    if fz:
        c = K.lade(fz[0], mono=True)
        c = K.filt0(c, "bp", (700.0, 7000.0))
        # gate: only the loud clicks (the hiss below goes)
        thr = np.percentile(np.abs(c), 99.3)
        g = np.clip((np.abs(c) - thr * 0.5) / (thr + 1e-9), 0, 1)
        g = K.filt0(g, "low", 400.0)
        c = c * np.clip(g * 3.0, 0, 1)
        seg = c[: L] if len(c) >= L else np.tile(c, L // len(c) + 1)[:L]
        out += K.auf_rms(seg, -30.0)
    wc = sorted(glob.glob(os.path.join(K.Q, LV, "100-CC0-wood-metal-SFX", "wood_cracking_0*.ogg")))
    pops = [K.lade(p, mono=True) for p in wc]
    for i in range(int(L_s * 1.6)):
        at = r.uniform(0, L)
        if pops and r.random() < 0.35:
            y = pops[r.integers(len(pops))]
            o = int(r.uniform(0, max(1, len(y) - 0.08 * SR)))
            y = K.resample(y[o:o + int(0.12 * SR)], r.uniform(1.4, 2.2))
            y = y * np.exp(-np.arange(len(y)) / (0.02 * SR))
            K.setze_rund(out, K.auf_spitze(y, -14.0 + r.uniform(-4, 2)), at)
        else:
            n = int(r.uniform(0.002, 0.012) * SR)
            y = r.standard_normal(n) * np.exp(-np.arange(n) / (n * 0.3))
            y = K.filt0(y, "bp", (r.uniform(900, 2000), r.uniform(4000, 9000)))
            K.setze_rund(out, K.auf_spitze(y, -18.0 + r.uniform(-6, 3)), at)
    out = K.filt_rund(out, "high", 50.0)
    return K.auf_rms(out, -24.0)


# ---- menu clicks in the style of MoveEye (sine, soft, short) --------------------------------------------------------------
def _sinus(f0_, f1, dur, att=0.002, tau=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0_ + (f1 - f0_) * np.clip(t / dur, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.clip(t / att, 0, 1) * (np.exp(-t / tau) if tau else np.cos(np.clip(t / dur, 0, 1) * np.pi / 2) ** 2)
    return np.sin(ph) * env


def ui(art):
    if art == "klick":
        y = _sinus(1250.0, 980.0, 0.05, 0.0015, 0.012)
        K.setze(y, _sinus(2500.0, 1960.0, 0.03, 0.001, 0.006), 0, 0.25)
        ck = glob.glob(os.path.join(K.Q, KEN_UI, "click_002.ogg"))
        if ck:
            c = K.lade(ck[0], mono=True)[: int(0.03 * SR)]
            c = K.filt0(c, "low", 3000.0)
            y[: len(c)] += K.auf_spitze(c, -14.0)[: len(y)]
        return K.auf_spitze(y, -12.0)
    if art == "auf":
        y = np.zeros(int(0.13 * SR))
        K.setze(y, _sinus(880.0, 880.0, 0.05, 0.003), 0)
        K.setze(y, _sinus(1175.0, 1175.0, 0.065, 0.003), int(0.055 * SR), 0.9)
        return K.auf_spitze(y, -14.0)
    y = np.zeros(int(0.13 * SR))
    K.setze(y, _sinus(1175.0, 1175.0, 0.05, 0.003), 0, 0.9)
    K.setze(y, _sinus(880.0, 880.0, 0.065, 0.003), int(0.055 * SR))
    return K.auf_spitze(y, -15.0)


# ---- plan ---------------------------------------------------------------------------------------------------------------
# name -> (function, loop, mono, quality, target LUFS as played at 0 dB of klang.gd)
PLAN = {
    "fund": (fund, False, False, 2, -20.0), "fanfare": (fanfare, False, False, 2, -19.0),
    "kapitel": (kapitel, False, False, 2, -20.0), "tusch": (tusch, False, False, 2, -18.0),
    "wirbel": (wirbel, True, True, 2, -26.0), "puls": (puls, True, True, 2, -24.0),
    "musik_fruehling": (fruehling, True, False, 0, -26.0), "musik_sommer": (sommer, True, False, 0, -26.0),
    "musik_herbst": (herbst, True, False, 0, -26.0), "musik_winter": (winter, True, False, 0, -26.0),
    "musik_see": (see, True, False, 0, -26.0),
    "schritt_gras": (lambda: schritte("gras"), False, True, 2, -24.0),
    "schritt_kies": (lambda: schritte("kies"), False, True, 2, -24.0),
    "schritt_schnee": (lambda: schritte("schnee"), False, True, 2, -24.0),
    "feuer": (feuer, True, True, 1, -26.0),
    "ui_klick": (lambda: ui("klick"), False, True, 3, None), "ui_auf": (lambda: ui("auf"), False, True, 3, None),
    "ui_zu": (lambda: ui("zu"), False, True, 3, None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quellen", required=True)
    ap.add_argument("--nur", default="")
    a = ap.parse_args()
    K.Q = a.quellen
    nur = [x for x in a.nur.split(",") if x]
    info_p = os.path.join(ZIEL, "spielton.json")
    info = json.load(open(info_p)) if os.path.exists(info_p) else {}
    for nm, (fn, loop, mo, q, tgt) in PLAN.items():
        if nur and nm not in nur:
            continue
        x = fn()
        s = speichern(nm, x, loop=loop, q=q, mono_=mo)
        i_, tp = K.lufs(os.path.join(ZIEL, "sp_" + nm + ".ogg"))
        d = {"s": round(s, 3), "loop": loop, "lufs": round(i_, 1), "spitze": round(tp, 1)}
        d["db"] = 0.0 if tgt is None else round(min(tgt - i_, -3.0 - tp), 1)
        if nm.startswith("schritt_"):
            d["slots"] = 4
            d["slot_s"] = 0.5
        info[nm] = d
        print("%-16s %5.1f s  %6.1f LUFS  Spitze %5.1f  db %+5.1f  %6.1f kB" % (nm, s, i_, tp, d["db"],
              os.path.getsize(os.path.join(ZIEL, "sp_" + nm + ".ogg")) / 1024))
    json.dump(dict(sorted(info.items())), open(info_p, "w"), indent=1)


if __name__ == "__main__":
    main()
