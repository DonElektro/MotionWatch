#!/usr/bin/env python3
"""Trailer-Klänge bauen (Daniel 01.11.2026: «Musik und Geräusche im Trailer klingen furchtbar»).

Baut aus freien Aufnahmen (CC0, siehe simulator3d/klang/LIZENZEN.txt) und eigener Synthese die Klänge der beiden Trailer
(trailer_ton.gd) und legt sie ab:
  simulator3d/klang/<name>.ogg       Ogg Vorbis, 44.1 kHz – spielt der Simulator (trailer_ton.gd get_snd)
  simulator3d/klang/web/<name>.mp3   dieselben Klänge als MP3 – für den Browser (MoveEye /sim/trailer, iPad: Safari kann
                                     Ogg nicht sicher dekodieren). Schleifen haben vorne und hinten 0.1 s «Umlauf», damit
                                     die Verzögerung des MP3-Dekoders keine Lücke macht (loopStart = 0.1 s, siehe ton_plan).

  python3 werkzeuge/klang_bauen.py --quellen /pfad/zu/den/geklonten/paketen [--alt ALT_WAVS] [--nur name,name]

--quellen: Ordner mit den Klonen (Namen wie unten in QUELLEN; holen mit --holen, braucht nur git und Zugang zu GitHub).
--alt:     die alten, im Code erzeugten Klänge als WAV (Tierstimmen werden daraus bearbeitet, nicht ersetzt) – fehlt der
           Ordner, werden sie mit Godot erzeugt (werkzeuge/klang_alt_export.gd).
Braucht: python3 mit numpy + scipy, ffmpeg (libvorbis, libmp3lame). Keine Zugangsdaten.
Alle Zufallswerte haben feste Startwerte: derselbe Lauf gibt dieselben Klänge.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from scipy import signal

SR = 44100
HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
ZIEL = os.path.join(REPO, "simulator3d", "klang")

# the free sources (all CC0): folder name in --quellen -> (GitHub repository, commit, files actually needed)
QUELLEN = {
    "sgossner_VSCO-2-CE": ("https://github.com/sgossner/VSCO-2-CE", "440300901dfe9275fd84e0b7763af1f8443ae62e",
                           ["Strings/Cello Section/susvib/*", "Strings/Viola Section/susvib/*_v1_*",
                            "Strings/Violin Section/susVib/*_v1.wav", "Strings/Solo Contrabass/SusVib/*_v1_*",
                            "Strings/Cello Section/spic/*_RR1.wav", "Strings/Cello Section/trem/*_v2_*",
                            "Brass/Tuba/sus/*_v3_*", "Brass/Tenor Trombone/sus/*_v3_*", "Brass/F Horn/sus/*_v3_*",
                            "Percussion/Timpani/*_rr1_*", "Percussion/Timpani/Rolls/*", "Percussion/Glock/*",
                            "Percussion/BDrumNewhit_v3_rr1_Sum.wav", "Percussion/BDrumNewhit_v5_rr1_Sum.wav",
                            "Miscellania Raw/Misc 1/cymb_gong.wav", "LICENSE"]),
    "lavenderdotpet_CC0-Public-Domain-Sounds": ("https://github.com/lavenderdotpet/CC0-Public-Domain-Sounds",
                                                "f2b6264f9ab89fabc266914c3654685d68c5a39b",
                                                ["40-cc0-water-splash-slime-sfx/loop_rain.ogg",
                                                 "100-cc0-sfx-2/sfx100v2_loop_water_03.ogg",
                                                 "100-cc0-sfx-2/sfx100v2_thunder_01.ogg",
                                                 "Micro Pack - Organic Wooshes/Gentle Swish.wav",
                                                 "Micro Pack - Organic Wooshes/_README.txt",
                                                 "bb - Books, Paper, Writing (Jan 2021)/Page Turn 1.wav",
                                                 "bb - Books, Paper, Writing (Jan 2021)/Page Turn 2.wav",
                                                 "bb - Books, Paper, Writing (Jan 2021)/_README.txt", "LICENSE"]),
    "stargatedaw_stargate-sample-pack": ("https://github.com/stargatedaw/stargate-sample-pack",
                                         "dbfd6ec52d4ed53b60bdbea5fc6adf295127c027",
                                         ["stargate-sample-pack/fugue-state-audio/found-sounds/thunder.wav",
                                          "stargate-sample-pack/fugue-state-audio/readme.md", "README.md"]),
    "kenney-impact-sounds-for-godot": ("https://github.com/Boyquotes/kenney-impact-sounds-for-godot",
                                       "999dd1684873f8b020a3aa5b26e713da21688924", None),
    "kenney-rpg-audio-for-godot": ("https://github.com/Boyquotes/kenney-rpg-audio-for-godot",
                                   "22eb79bb843bbcadcaa6ed119353a33265ffad11", None),
}
KEN_I = "kenney-impact-sounds-for-godot/addons/kenney impact sounds/"
KEN_R = "kenney-rpg-audio-for-godot/addons/kenney rpg audio/"
VS = "sgossner_VSCO-2-CE/"
LV = "lavenderdotpet_CC0-Public-Domain-Sounds/"

Q = ""          # --quellen
ALT = ""        # --alt
rng = np.random.default_rng(1)


# ---- input / output ---------------------------------------------------------------------------------------------------------
def lade(rel, mono=False):
    """any audio file -> float32 (n, 2) (or (n,) mono) at 44.1 kHz"""
    p = rel if os.path.isabs(rel) else os.path.join(Q, rel)
    if not os.path.exists(p):
        alt = os.path.join(Q, rel.split("/", 1)[0], "src", rel.split("/", 1)[1]) if "/" in rel else p
        p = alt if os.path.exists(alt) else p
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1" if mono else "2", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    return x if mono else x.reshape(-1, 2)


def st(x):
    return x if x.ndim == 2 else np.stack([x, x], 1)


def mono(x):
    return x if x.ndim == 1 else x.mean(1)


def speichern(name, x, loop=False, stereo=None, q=None):
    """x float (n,) or (n,2) -> klang/<name>.ogg and klang/web/<name>.mp3 (loops: web with 0.1 s wrap at both ends)"""
    os.makedirs(os.path.join(ZIEL, "web"), exist_ok=True)
    x = np.asarray(x, dtype=np.float32)
    if stereo is False:
        x = mono(x)
    ch = 1 if x.ndim == 1 else 2
    pk = np.abs(x).max()
    if pk > 0.891:                                          # never above -1 dBFS in the file
        x = x * (0.891 / pk)
    if not loop:
        x = x.copy()
        k = min(len(x), int(0.004 * SR))
        x[-k:] *= np.linspace(1, 0, k)[:, None] if ch == 2 else np.linspace(1, 0, k)
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, "x.f32")
        x.astype(np.float32).tofile(w)
        qq = q if q is not None else (3 if ch == 2 else 4)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-i", w,
                        "-c:a", "libvorbis", "-q:a", str(qq), os.path.join(ZIEL, name + ".ogg")], check=True)
        if loop:                                            # 0.1 s of the end before, 0.1 s of the start after (periodic)
            m = int(0.1 * SR)
            x = np.concatenate([x[-m:], x, x[:m]])
            x.astype(np.float32).tofile(w)
        br = "112k" if ch == 2 else "80k"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-i", w,
                        "-c:a", "libmp3lame", "-b:a", br, os.path.join(ZIEL, "web", name + ".mp3")], check=True)
    return len(x) / SR


# ---- dsp -------------------------------------------------------------------------------------------------------------------
def sos(kind, f, order=2):
    nyq = SR / 2
    if kind == "bp":
        return signal.butter(order, [f[0] / nyq, min(0.99, f[1] / nyq)], "bandpass", output="sos")
    return signal.butter(order, min(0.99, f / nyq), kind, output="sos")


def filt(x, kind, f, order=2):
    return signal.sosfilt(sos(kind, f, order), x, axis=0)


def filt0(x, kind, f, order=2):
    """zero phase (no delay)"""
    return signal.sosfiltfilt(sos(kind, f, order), x, axis=0)


def filt_rund(x, kind, f, order=2):
    """zero phase and circular (for loops: the filter wraps around, stays seamless)"""
    n = len(x)
    w = np.fft.rfftfreq(n, 1 / SR)
    _, h = signal.sosfreqz(sos(kind, f, order), worN=w, fs=SR)
    H = np.abs(h) ** 2
    X = np.fft.rfft(x, axis=0)
    return np.fft.irfft(X * (H[:, None] if x.ndim == 2 else H), n, axis=0)


def fft_band(n, lo, hi, tilt=0.0, seed=0, ch=2):
    """circular (seamless) band-limited noise of exactly n samples, slope tilt dB/octave (pink = -3)"""
    r = np.random.default_rng(seed)
    out = []
    for _ in range(ch):
        X = np.fft.rfft(r.standard_normal(n))
        f = np.fft.rfftfreq(n, 1 / SR)
        g = np.zeros_like(f)
        m = (f >= lo) & (f <= hi)
        g[m] = (np.maximum(f[m], 1.0) / max(lo, 1.0)) ** (tilt / 6.02)
        e = 0.15                                            # soft band edges (1/6 octave)
        g *= np.clip((f / lo - (1 - e)) / e, 0, 1) if lo > 0 else 1
        g *= np.clip(((1 + e) - f / hi) / e, 0, 1)
        y = np.fft.irfft(X * g, n)
        out.append(y / (np.sqrt((y ** 2).mean()) + 1e-12))
    return np.stack(out, 1) if ch == 2 else out[0]


def per_lfo(n, cycles, phase=0.0):
    """a sine with a whole number of cycles over n samples (stays seamless in a loop)"""
    return np.sin(2 * np.pi * cycles * np.arange(n) / n + phase)


def impulsantwort(rt60, pre=0.015, hf=6500.0, lf_rt=None, seed=7, breite=1.0, dichte_ms=12.0):
    """a synthetic stereo hall: early reflections + exponentially decaying noise, highs die faster (like air / walls)"""
    n = int((rt60 * 1.1 + pre) * SR)
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    p0 = int(pre * SR)
    for ch in range(2):
        nz = r.standard_normal(n)
        lo = filt(nz, "low", 900.0)
        hi = nz - lo
        lo_rt = lf_rt or rt60 * 1.1
        env_lo = 10 ** (-3 * t / lo_rt)
        env_hi = 10 ** (-3 * t / (rt60 * 0.55))
        y = lo * env_lo * 1.4 + filt(hi, "low", hf) * env_hi
        y *= np.clip(t / (dichte_ms / 1000.0), 0, 1)        # build-up (no hard start)
        ir[p0:, ch] = y[: n - p0]
        for k in range(10):                                 # early reflections
            d = p0 + int(r.uniform(0.004, 0.06) * SR)
            if d < n:
                ir[d, ch] += r.uniform(0.2, 0.6) * r.choice([-1, 1])
    m = ir.mean(1, keepdims=True)
    ir = m + (ir - m) * breite
    return ir / np.sqrt((ir ** 2).sum(0).mean())


def hall(x, rt60, wet, pre=0.015, hf=6500.0, circular=False, breite=1.0, seed=7):
    """x (n,) or (n,2) -> stereo with hall; circular=True for loops (the tail wraps around: seamless)"""
    x = st(x)
    ir = impulsantwort(rt60, pre, hf, seed=seed, breite=breite)
    n = len(x)
    out = np.zeros_like(x) if circular else np.zeros((n + len(ir) - 1, 2))
    for ch in range(2):
        if circular:
            L = n
            X = np.fft.rfft(x[:, ch], L)
            irr = ir[:, ch]
            if len(irr) > L:
                irr = irr[:L]
            H = np.fft.rfft(irr, L)
            out[:, ch] = np.fft.irfft(X * H, L)
        else:
            out[:, ch] = signal.fftconvolve(x[:, ch], ir[:, ch])
    dry = np.zeros_like(out)
    dry[:n] = x
    return dry * (1 - wet * 0.5) + out * wet


def kuerzen(x, secs, fade=0.3):
    n = int(secs * SR)
    x = x[:n].copy()
    k = min(len(x), int(fade * SR))
    ramp = np.cos(np.linspace(0, np.pi / 2, k)) ** 2
    x[-k:] *= ramp[:, None] if x.ndim == 2 else ramp
    return x


def platz(n, ch=2):
    return np.zeros((n, 2)) if ch == 2 else np.zeros(n)


def setze(dst, src, at, g=1.0):
    """add src into dst at sample index at (clipped)"""
    i0 = int(at)
    if i0 >= len(dst):
        return
    s = src[: len(dst) - i0]
    if dst.ndim == 2 and s.ndim == 1:
        s = st(s)
    dst[i0:i0 + len(s)] += s * g


def setze_rund(dst, src, at, g=1.0):
    """add src into dst at index at, wrapping around the end (for loops)"""
    n = len(dst)
    s = st(src) if dst.ndim == 2 and src.ndim == 1 else src
    idx = (int(at) + np.arange(len(s))) % n
    np.add.at(dst, idx, s * g)


def pan(x, p):
    """mono -> stereo, p -1 (left) .. 1 (right), constant power"""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def schleife(x, L, xf):
    """the first L samples of x as a seamless loop: the xf samples after L fade into the start (needs len(x) >= L + xf)"""
    y = x[:L].copy()
    a = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    if x.ndim == 2:
        a = a[:, None]
    y[:xf] = x[:xf] * np.sqrt(a) + x[L:L + xf] * np.sqrt(1 - a)
    return y


def resample(x, ratio):
    """play x «ratio» times faster (pitch up by ratio)"""
    n = int(round(len(x) / ratio))
    if n < 4:
        return x[:4]
    return signal.resample(x, n, axis=0)


def gleiten(x, r0, r1, curve=2.0):
    """time-varying speed from r0 to r1 (a glide / pitch rise), simple interpolation"""
    n_in = len(x)
    pos = [0.0]
    i = 0
    while pos[-1] < n_in - 2:
        u = pos[-1] / n_in
        pos.append(pos[-1] + r0 + (r1 - r0) * u ** curve)
        i += 1
    pos = np.array(pos[:-1])
    if x.ndim == 2:
        return np.stack([np.interp(pos, np.arange(n_in), x[:, c]) for c in range(2)], 1)
    return np.interp(pos, np.arange(n_in), x)


def soft(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


def rms(x):
    return float(np.sqrt((np.asarray(x) ** 2).mean()) + 1e-12)


def auf_rms(x, db):
    return x * (10 ** (db / 20) / rms(x))


def auf_spitze(x, db):
    return x * (10 ** (db / 20) / (np.abs(x).max() + 1e-12))


def f0(x):
    """the fundamental of a sustained note (harmonic product spectrum over the middle part)"""
    x = mono(x)
    a, b = int(len(x) * 0.3), int(len(x) * 0.7)
    s = x[a:b] * np.hanning(b - a)
    N = 1 << 18
    X = np.abs(np.fft.rfft(s, N))
    f = np.fft.rfftfreq(N, 1 / SR)
    hps = X.copy()
    for k in (2, 3, 4):
        d = X[::k]
        hps[: len(d)] *= d
    m = (f > 25) & (f < 2000)
    return float(f[m][np.argmax(hps[m])])


NOTEN = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(n):
    """'A2' -> 110.0 (scientific pitch: A4 = 440)"""
    nm, o = (n[:2], int(n[2:])) if n[1] == "#" else (n[:1], int(n[1:]))
    return 440.0 * 2 ** ((NOTEN[nm] + 12 * (o + 1) - 69) / 12)


# ---- sample library (VSCO-2 CE strings: the name of a note is one octave below scientific pitch; we measure) ------------------
_lib = {}


def _scan(folder, pat):
    import glob
    out = []
    for p in sorted(glob.glob(os.path.join(Q, VS, folder, pat))):
        out.append(p)
    return out


UNTEN = {"cello": 63, "cello3": 63, "viola": 125, "violin": 190, "bass": 38, "spic": 63, "spic1": 63, "trem": 63,
         "tuba": 28, "tbn": 55, "horn": 60}


def bibliothek(art):
    """[(measured f0, path)] for an instrument: cello / viola / violin / bass / cello_spic / cello_trem / tuba / tbn / horn"""
    if art in _lib:
        return _lib[art]
    pat = {"cello": ("Strings/Cello Section/susvib", "*_v1_1.wav"), "cello3": ("Strings/Cello Section/susvib", "*_v3_1.wav"),
           "viola": ("Strings/Viola Section/susvib", "*_v1_1.wav"), "violin": ("Strings/Violin Section/susVib", "*_v1.wav"),
           "bass": ("Strings/Solo Contrabass/SusVib", "*_v1_rr1.wav"), "spic": ("Strings/Cello Section/spic", "*_v2_RR1.wav"),
           "spic1": ("Strings/Cello Section/spic", "*_v1_RR1.wav"), "trem": ("Strings/Cello Section/trem", "*_v2_1.wav"),
           "tuba": ("Brass/Tuba/sus", "*_v3_*"), "tbn": ("Brass/Tenor Trombone/sus", "*_v3_1.wav"),
           "horn": ("Brass/F Horn/sus", "*_v3_1.wav")}[art]
    res = []
    for p in _scan(*pat):
        nm = os.path.basename(p)
        tok = [t for t in nm.replace(".wav", "").split("_") if t[:1] in "ABCDEFG" and any(c.isdigit() for c in t)]
        if not tok:
            continue
        try:
            named = hz(tok[0]) * 2.0                     # VSCO: one octave lower in the name
        except Exception:
            continue
        while named < UNTEN[art]:                        # (some names are off by an octave: below the instrument's range)
            named *= 2
        x = lade(p)
        meas = f0(x)
        # trust the name (the measurement may jump an octave), fine-tune with the measured value
        for k in (1.0, 2.0, 0.5, 4.0, 0.25):
            if abs(12 * np.log2(meas / (named * k))) < 0.7:
                named = meas / k
                break
        res.append((named, p, x))
    _lib[art] = res
    return res


def note_sample(art, ziel_hz):
    """the sample nearest to the note, shifted to it exactly"""
    lib = bibliothek(art)
    best = min(lib, key=lambda e: abs(np.log2(e[0] / ziel_hz)))
    return resample(best[2], ziel_hz / best[0]), best[1]


def huelle(x, thr=0.5):
    e = signal.sosfiltfilt(sos("low", 8.0), np.abs(mono(x)))
    return e / (e.max() + 1e-12)


def halten(x, n, seed=0, grain=1.6):
    """a sustained note of any length from a sample: grains from the steady middle, crossfaded (like a section that holds)"""
    e = huelle(x)
    on = np.where(e > 0.6)[0]
    a, b = (on[0], on[-1]) if len(on) else (0, len(x))
    a = int(a + 0.15 * SR)
    b = max(a + int(grain * SR) + 1, int(b - 0.1 * SR))
    if b > len(x):
        b = len(x)
        a = max(0, b - int(grain * SR) - 1)
    r = np.random.default_rng(seed)
    g = int(grain * SR)
    hop = g // 4
    w = np.hanning(g)
    out = np.zeros((n + g, 2))
    norm = np.zeros(n + g)
    pos = 0
    while pos < n:
        s0 = int(r.uniform(a, max(a + 1, b - g)))
        seg = x[s0:s0 + g]
        if len(seg) < g:
            seg = np.pad(seg, ((0, g - len(seg)), (0, 0)))
        out[pos:pos + g] += seg * w[:, None]
        norm[pos:pos + g] += w
        pos += hop
    out = out[:n] / np.maximum(norm[:n], 1e-3)[:, None]
    return out


# ---- music --------------------------------------------------------------------------------------------------------------
def pad(noten, L_s, hell, seed):
    """a string pad from real section samples (cello / viola / violin / bass sustain with vibrato), seamless loop, hall"""
    L = int(L_s * SR)
    xf = int(2.0 * SR)
    mix = np.zeros((L + xf, 2))
    for k, n in enumerate(noten):
        f = hz(n)
        arten = ["bass"] if f < 70 else ["cello", "cello3"] if f < 140 else ["cello", "viola"] if f < 220 else \
            ["viola", "violin"] if f < 420 else ["violin"]
        for j, art in enumerate(arten):
            for det in (-3.0, 4.0) if len(arten) == 1 else (0.0,):
                s, _ = note_sample(art, f * 2 ** ((det + (j * 2 - 1) * 2.5) / 1200))
                h = halten(s, L + xf, seed=seed * 31 + k * 7 + j * 3 + int(det))
                # each voice swells on its own (whole cycles over the loop -> seamless)
                sw = 0.78 + 0.22 * per_lfo(L, 1 + (k + j) % 2, phase=k * 1.3 + j)
                sw = np.concatenate([sw, sw[:xf]])
                p = ((k / max(1, len(noten) - 1)) * 1.2 - 0.6) * (1 if j == 0 else -0.6)
                a = (p + 1) * np.pi / 4
                g = (110.0 / f) ** 0.25 * (0.8 if j else 1.0) / (len(arten) ** 0.5)
                hm = mono(h)
                hs = h[:, 0] - h[:, 1]
                mix[:, 0] += (hm * np.cos(a) + hs * 0.25) * sw * g
                mix[:, 1] += (hm * np.sin(a) - hs * 0.25) * sw * g
    mix = schleife(mix, L, xf)
    mix = filt_rund(mix, "high", 45.0)
    mix = filt_rund(mix, "low", 2600.0 + 4500.0 * hell)
    mix = hall(mix, 3.2, 0.55, pre=0.03, hf=5000.0, circular=True, breite=1.2, seed=seed)
    return auf_rms(mix, -20.0)


def spic_note(f, laut=1.0, seed=0):
    s, _ = note_sample("spic" if laut > 0.7 else "spic1", f)
    e = huelle(s)
    on = np.argmax(e > 0.05)
    s = s[max(0, on - int(0.004 * SR)):]
    return s


def puls(bpm, schnell, takte):
    """muted strings in eighths / sixteenths (real cello spiccato) over a soft low drum, seamless (whole bars)"""
    beat = 60.0 / bpm
    L = int(round(SR * beat * 4 * takte))
    out = np.zeros((L, 2))
    steps = 16 if schnell else 8
    seq = [110.0, 164.81, 220.0, 164.81, 110.0, 164.81, 220.0, 246.94, 110.0, 164.81, 220.0, 164.81, 98.0, 146.83, 196.0, 146.83] \
        if schnell else [110.0, 110.0, 164.81, 110.0, 130.81, 110.0, 164.81, 146.83]
    r = np.random.default_rng(5 if schnell else 4)
    stl = beat * 4 / steps
    cache = {}
    for b in range(takte):
        for k in range(steps):
            f = seq[k % len(seq)]
            acc = 1.0 if k % (4 if schnell else 2) == 0 else 0.62
            key = (round(f, 2), acc > 0.7)
            if key not in cache:
                cache[key] = spic_note(f, acc)
            s = cache[key][: int(stl * SR * (1.6 if not schnell else 1.2))].copy()
            fade = int(0.05 * SR)
            s[-fade:] *= np.linspace(1, 0, fade)[:, None]
            at = (b * 4 * beat + k * stl) * SR + r.uniform(-0.004, 0.004) * SR
            setze_rund(out, s, max(0, at), acc * r.uniform(0.9, 1.05))
    out = auf_rms(out, -22.0)
    kick = lade(VS + "Percussion/BDrumNewhit_v3_rr1_Sum.wav")
    kick = filt0(kick, "low", 900.0)[: int(1.2 * SR)]
    kick = auf_spitze(kick, -6.0)
    timp, _ = timpani(55.0, weich=True)
    for b in range(takte):
        for q in range(4):
            at = (b * 4 + q) * beat * SR
            if schnell:
                setze_rund(out, kick, at, 0.55 if q % 2 == 0 else 0.35)
            else:
                setze_rund(out, kick, at, 0.5 if q == 0 else 0.3 if q == 2 else 0.18)
        if not schnell:
            setze_rund(out, timp, b * 4 * beat * SR, 0.35)
    out = hall(out, 1.8, 0.35, pre=0.02, circular=True, seed=11)
    return auf_rms(out, -19.0 if schnell else -20.0)


def timpani(ziel_hz, weich=False):
    """a real timpani hit (VSCO-2 CE), tuned"""
    import glob
    fs = sorted(glob.glob(os.path.join(Q, VS, "Percussion/Timpani/Timpani*_Hit_v%s_rr1_Sum.wav" % ("1" if weich else "4"))))
    best, bf = None, None
    for p in fs:
        x = lade(p)
        y = mono(x)[: int(1.0 * SR)]
        Y = np.abs(np.fft.rfft(y * np.hanning(len(y)), 1 << 17))
        f = np.fft.rfftfreq(1 << 17, 1 / SR)
        m = (f > 40) & (f < 200)
        fm = f[m][np.argmax(Y[m])]
        if best is None or abs(np.log2(fm / ziel_hz)) < abs(np.log2(bf / ziel_hz)):
            best, bf = x, fm
    return resample(best, ziel_hz / bf), bf


def sub(f0_, f1, secs, decay, drop=0.25):
    t = np.arange(int(secs * SR)) / SR
    f = f1 + (f0_ - f1) * np.exp(-t / drop)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / decay) * np.clip(t / 0.004, 0, 1)


def pauke():
    """the big drum: a real timpani (D2), underneath a sub bass with pitch drop, a dull bass drum, hall"""
    t, _ = timpani(73.42)
    t = kuerzen(t, 5.0, 1.5)
    out = np.zeros((int(6.5 * SR), 2))
    setze(out, auf_spitze(t, -3.0), 0)
    setze(out, pan(sub(70.0, 41.0, 2.5, 0.55, 0.12), 0), 0, 0.55)
    k = lade(VS + "Percussion/BDrumNewhit_v5_rr1_Sum.wav")
    setze(out, filt0(auf_spitze(k, -3.0), "low", 1200.0), 0, 0.45)
    out = hall(out, 2.8, 0.45, pre=0.02, hf=4500.0, seed=3)
    return kuerzen(out, 6.0, 1.5)


def boom():
    """the deep cinema hit under the title («braam»): low brass in D (tuba, trombones, horns), cello tremolo, gong,
    bass drum, sub drop – decays over about 6 s"""
    n = int(8.0 * SR)
    out = np.zeros((n, 2))
    for art, notes, g in (("tuba", ["D1", "A1"], 1.0), ("tbn", ["D2", "A2", "F3"], 0.8), ("horn", ["D3", "A3"], 0.5),
                          ("trem", ["D2", "A2"], 0.45)):
        for k, nn in enumerate(notes):
            s, _ = note_sample(art, hz(nn) * 2 ** ((k - 0.5) * 4 / 1200))
            s = halten(s, int(7.0 * SR), seed=k + len(art))
            t = np.arange(len(s)) / SR
            env = np.clip(t / 0.03, 0, 1) * (0.35 + 0.65 * np.exp(-t / 0.5)) * np.exp(-t / 2.6)
            setze(out, s * env[:, None] * g / len(notes) ** 0.5, 0)
    out = soft(auf_spitze(out, -4.0), 1.8)
    out = filt0(out, "low", 3500.0)
    gong = lade(VS + "Miscellania Raw/Misc 1/cymb_gong.wav")
    setze(out, auf_spitze(gong, -8.0), 0)
    k = lade(VS + "Percussion/BDrumNewhit_v5_rr1_Sum.wav")
    setze(out, auf_spitze(k, -2.0), 0)
    setze(out, pan(sub(62.0, 36.7, 5.0, 1.6, 0.3), 0), 0, 0.8)
    out = hall(out, 4.0, 0.5, pre=0.03, hf=4000.0, breite=1.3, seed=5)
    return kuerzen(out, 7.5, 2.5)


def riser(secs=4.0):
    """rising strings (cello tremolo gliding up an octave), timpani roll crescendo, noise sweep – stops dead at the end"""
    n = int(secs * SR)
    s, _ = note_sample("trem", hz("D2"))
    s = halten(s, int(secs * 1.6 * SR), seed=2)
    up = gleiten(s, 1.0, 2.0, 1.6)[:n]
    if len(up) < n:
        up = np.pad(up, ((0, n - len(up)), (0, 0)))
    s2, _ = note_sample("trem", hz("A2"))
    s2 = halten(s2, int(secs * 1.6 * SR), seed=3)
    up2 = gleiten(s2, 1.0, 2.0, 1.6)[:n]
    up2 = np.pad(up2, ((0, n - len(up2)), (0, 0)))
    t = np.arange(n) / n
    env = (0.08 + 0.92 * t ** 2.2)[:, None]
    out = (up + 0.7 * up2) * env
    roll = lade(VS + "Percussion/Timpani/Rolls/Timpani1_Roll_v5_rr1_Sum.wav")
    roll = roll[:n] if len(roll) >= n else np.pad(roll, ((0, n - len(roll)), (0, 0)))
    out += auf_rms(roll, -26.0) * (t ** 1.5)[:, None] * 1.0
    nz = fft_band(n, 200.0, 12000.0, -3.0, seed=9)
    # a band sweeping up: time-varying lowpass done in blocks
    blk = 1024
    y = np.zeros_like(nz)
    zi = None
    for i in range(0, n, blk):
        u = i / n
        so = sos("bp", (300 + 1500 * u ** 2, 900 + 9000 * u ** 2), 1)
        if zi is None:
            zi = np.zeros((so.shape[0], 2, 2))
        y[i:i + blk], zi = signal.sosfilt(so, nz[i:i + blk], axis=0, zi=zi)
    out += auf_rms(y, -24.0) * (t ** 3)[:, None] * 1.6
    out = hall(out, 1.6, 0.3, seed=13)[:n]
    out[-int(0.006 * SR):] *= np.linspace(1, 0, int(0.006 * SR))[:, None]
    return auf_spitze(out, -2.0)


def chime():
    """the crystal: real glockenspiel notes (E6, B6, G6, E7 – tuned from VSCO-2 CE), long shimmering hall"""
    import glob
    gl = {}
    for p in glob.glob(os.path.join(Q, VS, "Percussion/Glock/*.wav")):
        nm = os.path.basename(p).split("_")[-1][:-4]
        gl[hz(nm) * 2] = p                                   # glock sounds two octaves above written; VSCO names: +1 octave
    out = np.zeros((int(5.0 * SR), 2))
    for k, (nn, at, g, p) in enumerate((("E6", 0.0, 1.0, -0.3), ("B6", 0.0, 0.7, 0.3), ("G6", 0.35, 0.8, 0.0),
                                        ("E7", 0.7, 0.45, 0.5))):
        f = hz(nn)
        src_f = min(gl, key=lambda q: abs(np.log2(q / f)))
        x = lade(gl[src_f])
        meas = f0(x[: int(0.6 * SR)])
        ratio = f / (meas if abs(np.log2(meas / src_f)) < 0.6 else src_f)
        y = mono(resample(x, ratio))
        setze(out, pan(y, p), int(at * SR), g)
    out = hall(out, 3.5, 0.6, pre=0.02, hf=9000.0, breite=1.3, seed=17)
    return kuerzen(auf_spitze(out, -3.0), 5.0, 1.5)


def whoosh():
    """air past the camera: band noise sweeping (doppler), moving left -> right, with a real swish at the middle"""
    n = int(1.2 * SR)
    t = np.arange(n) / n
    nz = fft_band(n, 150.0, 9000.0, -3.0, seed=21, ch=1)
    blk = 512
    y = np.zeros(n)
    zi = None
    for i in range(0, n, blk):
        u = i / n
        fc = 400 + 2600 * np.sin(np.pi * u) ** 2
        so = sos("bp", (fc * 0.5, fc * 1.6), 1)
        if zi is None:
            zi = np.zeros((so.shape[0], 2))
        y[i:i + blk], zi = signal.sosfilt(so, nz[i:i + blk], zi=zi)
    env = np.sin(np.pi * t) ** 2.5
    y = y * env
    out = np.stack([y * np.cos((t + 0.0) * np.pi / 2), y * np.sin(t * np.pi / 2)], 1)
    sw = lade(LV + "Micro Pack - Organic Wooshes/Gentle Swish.wav")
    setze(out, auf_rms(sw, rms(out) * 0 - 18.0), int(0.42 * SR), 0.6)
    out = hall(out, 0.9, 0.2, seed=23)
    return kuerzen(auf_spitze(out, -3.0), 1.5, 0.3)


# ---- surroundings -----------------------------------------------------------------------------------------------------------
def wind(L_s=20.0):
    """mountain wind as a seamless loop: low rumble, a broad rushing band, gusts, a soft whistle, leaves – all circular"""
    n = int(L_s * SR)
    out = np.zeros((n, 2))
    boe = 0.55 + 0.25 * per_lfo(n, 3, 0.4) + 0.15 * per_lfo(n, 7, 1.9) + 0.08 * per_lfo(n, 13, 0.3)
    boe2 = 0.55 + 0.25 * per_lfo(n, 4, 2.4) + 0.15 * per_lfo(n, 9, 0.7) + 0.08 * per_lfo(n, 17, 2.0)
    low = fft_band(n, 25.0, 220.0, -4.0, seed=31)
    mid = fft_band(n, 180.0, 1400.0, -3.0, seed=32)
    hi = fft_band(n, 1200.0, 9000.0, -6.0, seed=33)
    out += low * (0.6 + 0.4 * boe)[:, None] * 0.55
    out += mid * np.stack([boe, boe2], 1) ** 1.6 * 0.45
    out += hi * np.stack([boe2, boe], 1) ** 3.0 * 0.05
    for k, (fc, cyc) in enumerate(((620.0, 2), (910.0, 3))):            # whistling in the rocks: narrow, slowly drifting
        w = fft_band(n, fc * 0.96, fc * 1.04, 0.0, seed=40 + k, ch=1)
        g = np.clip(per_lfo(n, cyc, k * 2.1), 0, 1) ** 2 * boe ** 2
        out += pan(w * g * 0.05, -0.5 + k)
    return auf_rms(out, -24.0)


def wasser(L_s=12.0):
    """a mountain brook: a real recording (rubberduck, CC0) made into a 12 s loop, with a bright bubbling layer"""
    x = lade(LV + "100-cc0-sfx-2/sfx100v2_loop_water_03.ogg")
    n = int(L_s * SR)
    xf = int(1.0 * SR)
    if len(x) < n + xf:
        reps = int(np.ceil((n + xf) / len(x))) + 1
        y = np.zeros((len(x) * reps, 2))
        step = len(x) - xf
        a = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
        for r_ in range(reps):
            seg = x.copy()
            seg[:xf] *= np.sqrt(a)[:, None] if r_ else 1
            seg[-xf:] *= np.sqrt(1 - a)[:, None]
            setze(y, seg, r_ * step)
        x = y
    lp = schleife(x, n, xf)
    bub = fft_band(n, 1800.0, 6000.0, -2.0, seed=51)
    bub *= (0.5 + 0.5 * np.clip(per_lfo(n, 37, 0.0) + per_lfo(n, 23, 1.0), 0, 2) / 2)[:, None]
    out = lp + auf_rms(bub, rms(lp) * 0 - 34.0)
    out = hall(out, 0.8, 0.15, circular=True, seed=53)
    return auf_rms(out, -21.0)


def regen(L_s=13.65):
    """rain: a real rain loop (rubberduck, CC0) twice + a circular layer of drops for variety, seamless"""
    x = lade(LV + "40-cc0-water-splash-slime-sfx/loop_rain.ogg")
    n1 = len(x)
    n = 2 * n1
    out = np.concatenate([x, x])
    r = np.random.default_rng(61)
    tro = np.zeros((n, 2))
    tick = filt0(r.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / (0.002 * SR)), "high", 2500.0)
    for _ in range(int(L_s * 40)):
        setze_rund(tro, pan(tick, r.uniform(-0.9, 0.9)), r.integers(0, n), r.uniform(0.05, 0.4))
    out = out + auf_rms(tro, -34.0) + auf_rms(fft_band(n, 60.0, 400.0, -3.0, seed=62), -38.0)
    return auf_rms(out, -20.0)


def donner():
    """a real thunder (Fugue State Audio, public domain) with the crack of a closer one (rubberduck, CC0) in front"""
    x = lade("stargatedaw_stargate-sample-pack/stargate-sample-pack/fugue-state-audio/found-sounds/thunder.wav")
    e = huelle(x)
    i0 = max(0, int(np.argmax(e > 0.2)) - int(0.3 * SR))
    x = x[i0:]
    x = kuerzen(x, 10.0, 3.0)
    c = lade(LV + "100-cc0-sfx-2/sfx100v2_thunder_01.ogg")
    out = np.zeros((int(10.5 * SR), 2))
    setze(out, auf_spitze(x, -3.0), int(0.25 * SR))
    setze(out, auf_spitze(filt0(c, "high", 120.0), -5.0), 0, 0.6)
    setze(out, pan(sub(48.0, 30.0, 3.0, 1.2, 0.6), 0), int(0.25 * SR), 0.3)
    out = hall(out, 3.5, 0.35, hf=3000.0, breite=1.4, seed=71)
    return kuerzen(auf_spitze(out, -1.5), 10.0, 2.5)


def schritte(step, rennen=False):
    """steps on a gravel path with grass at the edge (Kenney, CC0), 4 steps as a loop, a little outdoor reflection"""
    L = int(round(step * 4 * SR))
    out = np.zeros((L, 2))
    kies = [lade(KEN_R + "footstep_%d.ogg" % i) for i in range(10)]
    gras = [lade(KEN_I + "footstep_grass_%03d.ogg" % i) for i in range(5)]
    r = np.random.default_rng(81 if rennen else 82)
    for k in range(4):
        a = kies[(k * 3 + (5 if rennen else 0)) % 10]
        b = gras[(k * 2 + 1) % 5]
        at = k * step * SR + r.uniform(-0.01, 0.01) * SR
        p = -0.12 if k % 2 == 0 else 0.12
        setze_rund(out, pan(mono(a), p), max(0, at), (1.0 if k % 2 == 0 else 0.85) * (1.2 if rennen else 1.0))
        setze_rund(out, pan(mono(b), p), max(0, at + 0.01 * SR), 0.35)
    out = filt_rund(out, "high", 80.0)
    out = hall(out, 0.5, 0.12, circular=True, seed=83)
    return auf_rms(out, -22.0 if rennen else -24.0)


def tier(name, rt, wet, lp, hp=60.0, db=-14.0):
    """the old animal voices (they stay, like in the game) – only placed in a space: filters, a little saturation, hall"""
    p = os.path.join(ALT, name + ".wav")
    x = lade(p, mono=True)
    x = filt0(x, "high", hp)
    x = filt0(x, "low", lp)
    x = soft(auf_spitze(x, -2.0), 1.3)
    out = hall(x, rt, wet, pre=0.02, hf=min(lp, 6000.0), seed=hash(name) & 0xff)
    return auf_spitze(out, db + 12.0) if False else auf_spitze(out, -3.0)


def kraehen():
    """three crow caws: a raspy voice (pulse train through two formants, noise), pitch falling, hall of the forest"""
    out = np.zeros((int(2.6 * SR), 2))
    r = np.random.default_rng(91)
    for k, (at, f_, ln, p) in enumerate(((0.0, 560.0, 0.32, -0.4), (0.45, 600.0, 0.28, -0.35), (0.95, 530.0, 0.36, -0.45))):
        n = int(ln * SR)
        t = np.arange(n) / SR
        f = f_ * (1.06 - 0.16 * t / ln) * (1 + 0.02 * np.sin(2 * np.pi * 31 * t))
        ph = np.cumsum(f) / SR
        jit = 1 + 0.03 * filt(r.standard_normal(n), "low", 60.0) * 8
        ph = np.cumsum(f * jit) / SR
        saw = signal.sawtooth(2 * np.pi * ph)
        sub_ = 1 + 0.9 * np.sin(np.pi * ph)                     # period doubling: the rasp of a crow
        src = saw * sub_ + 1.1 * r.standard_normal(n) * (0.5 + 0.5 * t / ln)
        v = np.zeros(n)
        for fo, bw, g in ((1150.0, 260.0, 1.0), (1750.0, 300.0, 0.7), (2900.0, 500.0, 0.35)):
            v += filt(src, "bp", (fo - bw, fo + bw), 2) * g
        env = np.clip(t / 0.02, 0, 1) * np.clip((ln - t) / 0.07, 0, 1) * (1 - 0.3 * t / ln)
        v = soft(v * env * 3.0, 2.0)
        setze(out, pan(v, p), int(at * SR))
    out = hall(out, 1.6, 0.35, pre=0.02, hf=5000.0, seed=93)
    return kuerzen(auf_spitze(out, -3.0), 2.6, 0.8)


def zischen():
    """a hiss (snake / cat): air noise 2.5–10 kHz, swelling, a little throat underneath"""
    n = int(1.4 * SR)
    t = np.arange(n) / n
    x = fft_band(n, 2500.0, 10000.0, -1.0, seed=101, ch=1)
    x = x * (np.sin(np.pi * t) ** 0.7) * (1 + 0.15 * np.sin(2 * np.pi * 9 * t))
    th = fft_band(n, 400.0, 1500.0, -3.0, seed=102, ch=1) * 0.15 * np.sin(np.pi * t)
    out = hall(x + th, 0.7, 0.2, seed=103)
    return kuerzen(auf_spitze(out, -3.0), 1.7, 0.3)


def knacken():
    """a twig snaps in the dark: two dry wooden cracks (Kenney, CC0) with a splinter, a bit of forest echo"""
    a = lade(KEN_I + "impact_wood_light_002.ogg", mono=True)
    b = lade(KEN_I + "impact_wood_light_004.ogg", mono=True)
    r = np.random.default_rng(111)
    out = np.zeros(int(0.9 * SR))
    setze(out, filt0(a, "high", 700.0), 0, 1.0)
    setze(out, filt0(b, "high", 900.0), int(0.07 * SR), 0.6)
    spl = filt0(r.standard_normal(int(0.03 * SR)), "high", 3000.0) * np.exp(-np.arange(int(0.03 * SR)) / (0.004 * SR))
    setze(out, spl, int(0.012 * SR), 0.3)
    out = hall(out, 1.2, 0.3, seed=113)
    return kuerzen(auf_spitze(out, -3.0), 1.2, 0.4)


def rascheln():
    """something moves in the bushes: dense tiny leaf clicks in bursts (granular), plus soft cloth"""
    n = int(1.8 * SR)
    r = np.random.default_rng(121)
    out = np.zeros((n, 2))
    burst = np.clip(np.sin(2 * np.pi * np.arange(n) / SR * 2.1) * np.sin(np.pi * np.arange(n) / n), 0, 1)
    k = int(0.006 * SR)
    for _ in range(900):
        i = r.integers(0, n - k)
        if r.uniform() > burst[i]:
            continue
        c = r.standard_normal(k) * np.exp(-np.arange(k) / (0.0012 * SR))
        setze(out, pan(c, r.uniform(-0.5, 0.5)), i, r.uniform(0.1, 1.0))
    out = filt0(out, "bp", (1500.0, 9000.0), 2)
    cl = lade(KEN_R + "cloth_2.ogg")
    setze(out, auf_rms(cl, -30.0), int(0.3 * SR), 1.0)
    out = hall(out, 0.8, 0.2, seed=123)
    return kuerzen(auf_spitze(out, -4.0), 2.0, 0.3)


def kuhglocke():
    """a cow bell far away on the alp: a real bell stroke (Kenney impact_bell_heavy, CC0) – two strokes, distance and hall"""
    a = lade(KEN_I + "impact_bell_heavy_001.ogg", mono=True)
    b = lade(KEN_I + "impact_bell_heavy_003.ogg", mono=True)
    out = np.zeros(int(3.5 * SR))
    setze(out, resample(a, 0.84), 0)
    setze(out, resample(b, 0.84), int(0.55 * SR), 0.8)
    out = filt0(filt0(out, "low", 4200.0), "high", 300.0)
    out = hall(out, 2.5, 0.45, pre=0.04, hf=4000.0, seed=131)
    return kuerzen(auf_spitze(out, -3.0), 3.5, 1.2)


def papier():
    """an old letter is unfolded (Ben Burnes, CC0: page turns)"""
    a = lade(LV + "bb - Books, Paper, Writing (Jan 2021)/Page Turn 1.wav")
    b = lade(LV + "bb - Books, Paper, Writing (Jan 2021)/Page Turn 2.wav")
    out = np.zeros((int(2.0 * SR), 2))
    setze(out, a, 0)
    setze(out, b, int(0.55 * SR), 0.8)
    out = hall(out, 0.5, 0.12, seed=141)
    e = huelle(out)
    end = min(len(out), int(np.where(e > 0.02)[0][-1] + 0.2 * SR))
    return kuerzen(auf_spitze(out[:end], -3.0), end / SR, 0.2)


BAU = {
    # name: (function, loop?, stereo?)
    "pad_ruhig": (lambda: pad(["A2", "E3", "B3", "C4", "E4"], 16.0, 0.5, 1), True, True),
    "pad_dunkel": (lambda: pad(["A1", "D2", "A2", "D3", "F3", "A3"], 16.0, 0.0, 2), True, True),
    "pad_hell": (lambda: pad(["F2", "C3", "F3", "A3", "C4", "G4"], 16.0, 1.0, 3), True, True),
    "pulse": (lambda: puls(96.0, False, 2), True, True),
    "ostinato": (lambda: puls(120.0, True, 2), True, True),
    "pauke": (pauke, False, True),
    "boom": (boom, False, True),
    "riser": (riser, False, True),
    "chime": (chime, False, True),
    "whoosh": (whoosh, False, True),
    "wind": (wind, True, True),
    "wasser": (wasser, True, True),
    "regen": (regen, True, True),
    "donner": (donner, False, True),
    "schritte": (lambda: schritte(0.56), True, True),
    "rennen": (lambda: schritte(0.32, True), True, True),
    "knurren": (lambda: tier("knurren", 1.0, 0.2, 3500.0, 50.0), False, True),
    "bellen": (lambda: tier("bellen", 1.4, 0.3, 5000.0, 150.0), False, True),
    "heulen": (lambda: tier("heulen", 3.5, 0.55, 3500.0, 150.0), False, True),
    "grunzen": (lambda: tier("grunzen", 0.9, 0.2, 2500.0, 50.0), False, True),
    "kraehen": (kraehen, False, True),
    "zischen": (zischen, False, True),
    "knacken": (knacken, False, True),
    "rascheln": (rascheln, False, True),
    "kuhglocke": (kuhglocke, False, True),
    "papier": (papier, False, True),
    "pfiff": (lambda: tier("pfiff", 2.5, 0.45, 6000.0, 800.0), False, True),
}


# loudness as played in the trailer: (typical dB in the plan of trailer_buehne.gd, target LUFS at that dB) - the difference
# to the file is the «db» per sound in klaenge.json, which trailer.gd (and the plan for the browser) adds to the plan's dB
ZIELPEGEL = {
    "pad_ruhig": (-10, -24), "pad_dunkel": (-12, -24), "pad_hell": (-12, -24), "pulse": (-16, -28), "ostinato": (-14, -27),
    "pauke": (-6, -19), "boom": (-2, -16), "riser": (-6, -21), "chime": (-10, -24), "whoosh": (-12, -28),
    "wind": (-10, -29), "wasser": (-8, -27), "regen": (-8, -25), "donner": (-2, -16), "schritte": (-14, -31),
    "rennen": (-10, -28), "knurren": (-10, -23), "bellen": (-10, -23), "heulen": (-10, -25), "grunzen": (-10, -25),
    "kraehen": (-8, -23), "zischen": (-10, -27), "knacken": (-12, -27), "rascheln": (-12, -29), "kuhglocke": (-18, -33),
    "papier": (-10, -28), "pfiff": (-18, -31),
}


def lufs(path_or_x):
    """integrated loudness (EBU R128) and true peak of a file or a float array"""
    with tempfile.TemporaryDirectory() as td:
        if isinstance(path_or_x, str):
            src = ["-i", path_or_x]
        else:
            x = st(np.asarray(path_or_x, dtype=np.float32))
            w = os.path.join(td, "x.f32")
            x.astype(np.float32).tofile(w)
            src = ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", w]
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + src + ["-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    i_ = float(tail.split("I:")[1].split("LUFS")[0])
    tp = float(tail.split("Peak:")[1].split("dBFS")[0]) if "Peak:" in tail else 0.0
    return i_, tp


def pegel_rechnen(names):
    p = os.path.join(ZIEL, "klaenge.json")
    info = json.load(open(p)) if os.path.exists(p) else {}
    for nm in names:
        ref, tgt = ZIELPEGEL[nm]
        i_, tp = lufs(os.path.join(ZIEL, nm + ".ogg"))
        d = info.setdefault(nm, {})
        d["lufs"] = round(i_, 1)
        d["spitze"] = round(tp, 1)
        cap = -3.0 if nm in ("pauke", "boom", "donner", "riser") else -6.0     # a single sound never above this as played
        d["db"] = round(min(tgt - ref - i_, cap - ref - tp), 1)
    json.dump(dict(sorted(info.items())), open(p, "w"), indent=1)
    return info


def mix(plan, info, cache={}):
    """the trailer's music and noises as the simulator plays them (no narrator): float stereo"""
    d = float(plan["dauer"]) + 4.0
    n = int(d * SR)
    out = np.zeros((n, 2))
    musik = set(plan.get("musik", []))
    duck = np.ones(n)
    for e in plan["plan"]:
        if e[1] == "say":
            a = int(e[0] * SR)
            duck[a:a + int(e[2] * SR)] = 0.6
    def snd(nm):
        if nm not in cache:
            cache[nm] = lade(os.path.join(ZIEL, nm + ".ogg"))
        return cache[nm]
    # loops: gain curve per loop from loop/stop/stille commands (linear ramps)
    loops = {}
    for e in plan["plan"]:
        t, k = float(e[0]), e[1]
        if k == "loop":
            loops.setdefault(e[2], []).append((t, 10 ** ((e[3] + info[e[2]]["db"]) / 20), max(0.05, e[4])))
        elif k == "stop":
            loops.setdefault(e[2], []).append((t, 0.0, max(0.05, e[3])))
        elif k == "stille":
            for nm in list(loops):
                loops[nm].append((t, 0.0, max(0.05, e[2])))
            # (the one-shots stop too)
    for nm, cmds in loops.items():
        g = np.zeros(n)
        cur, last = 0.0, 0
        cmds.sort(key=lambda c: c[0])
        t0 = int(cmds[0][0] * SR)
        for (t, to, f) in cmds:
            a = int(t * SR)
            g[last:a] = cur if last >= a else g[last:a]
            b = min(n, a + int(f * SR))
            g[a:b] = np.linspace(cur, to, b - a, endpoint=False) if b > a else g[a:b]
            g[b:] = to
            cur, last = to, b
        x = snd(nm)
        reps = int(np.ceil((n - t0) / len(x))) + 1
        y = np.tile(x, (reps, 1))[: n - t0]
        gg = g[t0:] * (duck[t0:] if nm in musik else 1.0)
        out[t0:] += y * gg[:, None]
    stills = [float(e[0]) for e in plan["plan"] if e[1] == "stille"]
    for e in plan["plan"]:
        if e[1] != "one":
            continue
        t = float(e[0])
        x = snd(e[2]) * 10 ** ((e[3] + info[e[2]]["db"]) / 20)
        nxt = [s for s in stills if s > t]
        if nxt:
            x = x[: int((nxt[0] - t) * SR)]
        setze(out, x, int(t * SR))
    return out


def holen(ziel):
    """clone the sources (only the files needed: partial clone + sparse checkout)"""
    os.makedirs(ziel, exist_ok=True)
    for d, (url, commit, files) in QUELLEN.items():
        p = os.path.join(ziel, d)
        if not os.path.isdir(p):
            if files is None:
                subprocess.run(["git", "clone", "-q", url + ".git", p], check=True)
            else:
                subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", url + ".git", p], check=True)
        subprocess.run(["git", "-C", p, "checkout", "-q", commit] + (["--"] + files if files else []), check=True)


def alt_export(ziel):
    g = os.environ.get("GODOT") or "/tmp/claude-0/godot/Godot_v4.3-stable_linux.x86_64"
    os.makedirs(ziel, exist_ok=True)
    env = dict(os.environ, KLANG_OUT=ziel, KLANG_ALT="1")
    subprocess.run([g, "--headless", "--path", os.path.join(REPO, "simulator3d"), "-s",
                    os.path.join(HIER, "klang_alt_export.gd")], check=True, env=env, capture_output=True)


def main():
    global Q, ALT
    ap = argparse.ArgumentParser()
    ap.add_argument("--quellen", default="")
    ap.add_argument("--alt", default="")
    ap.add_argument("--nur", default="")
    ap.add_argument("--holen", action="store_true")
    ap.add_argument("--mix", default="", help="plan.json (trailer.gd ton_plan of both trailers): the mix, measured")
    ap.add_argument("--wav", default="", help="with --mix: write the mixes as WAV into this folder")
    a = ap.parse_args()
    Q = os.path.abspath(a.quellen)
    if a.holen:
        holen(Q)
    if a.mix:
        info = json.load(open(os.path.join(ZIEL, "klaenge.json")))
        plans = json.load(open(a.mix))
        for tid, pl in plans.items():
            x = mix(pl, info)
            i_, tp = lufs(x)
            win = int(3 * SR)
            st_ = [20 * np.log10(rms(x[i:i + win]) + 1e-9) for i in range(0, len(x) - win, win)]
            print("%-11s Musik+Geräusche: %.1f LUFS, Spitze %.1f dBFS (lautester 3-s-Abschnitt %.1f dB RMS)" % (tid, i_, tp, max(st_)))
            if a.wav:
                with tempfile.TemporaryDirectory() as td:
                    w = os.path.join(td, "x.f32")
                    x.astype(np.float32).tofile(w)
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", w,
                                    os.path.join(a.wav, "mix_%s.wav" % tid)], check=True)
        return
    ALT = a.alt or os.path.join(tempfile.gettempdir(), "klang_alt")
    if not os.path.exists(os.path.join(ALT, "knurren.wav")):
        alt_export(ALT)
    names = [n for n in a.nur.split(",") if n] or list(BAU)
    info = {}
    for nm in names:
        fn, loop, stereo = BAU[nm]
        x = fn()
        secs = speichern(nm, x, loop=loop, stereo=stereo)
        info[nm] = round(len(x) / SR, 3)
        print("%-10s %6.2f s  %s" % (nm, len(x) / SR, "Schleife" if loop else ""), flush=True)
    p = os.path.join(ZIEL, "klaenge.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    for k, v in info.items():
        old.setdefault(k, {}).update({"s": v, "loop": BAU[k][1]})
    json.dump(dict(sorted(old.items())), open(p, "w"), indent=1)
    pegel_rechnen(names)


if __name__ == "__main__":
    main()
