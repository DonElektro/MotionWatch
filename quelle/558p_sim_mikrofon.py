#@ MoveEye – Teil 558p: Mithören im Simulator – aus dem Feld «mic» des 3D-Simulators (Pegel, Hintergrund, lauteste Quellen) ein Geräusch in der richtigen Lautstärke erzeugen (Paket real-pir-ton). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Der 3D-Simulator hat kein echtes Tonsignal, nur Pegel. Ab dem Paket «PIR, Mikrofon & Umgebungsgeräusche» schickt er in der
# Antwort auf /state das Feld «mic»: {"db": Summe dBFS, "bg": Hintergrund dBFS, "src": [{"k": Art, "db": Pegel am Mikrofon,
# "az": Richtung ° (0 = vorne), "d": Abstand m}, ...]} (simulator3d/scripts/mikrofon.gd). 250 AudioMonitor.feed_sim gibt es
# hierher, solange jemand mithört: pro Quelle ein Stück Rauschen mit grob passendem Klang (Wind tief, Regen hell, Grillen
# ~4.6 kHz, Stimmen im Silbentakt …), zusammen genau so laut wie «db». Das ist kein echter Ton - nur damit «🎧 Mithören» im
# Simulator dieselbe Lautstärke und denselben Wechsel (still / Hund bellt / Klatschen) hören lässt wie das echte Mikrofon.
# Klatschschalter, Gesundheit und Lärm-Alarm laufen wie bisher über sound_db / sound_ev (250), nicht über dieses Geräusch.
# ----------------------------------------------------------------------------
# Art -> (tiefste Hz, höchste Hz, Ton Hz oder 0, Takt Hz der Lautstärke oder 0)
SIMMIC_KIND = {"bg": (40, 6000, 0, 0), "wind": (20, 400, 0, 0.3), "rain": (1200, 7500, 0, 0), "water": (180, 1500, 0, 6.0),
               "frogs": (150, 900, 260, 9.0), "crickets": (4200, 5200, 4600, 18.0), "birds": (2000, 6500, 3400, 7.0),
               "owl": (300, 600, 400, 0.8), "dog": (250, 2000, 500, 1.7), "cows": (600, 3000, 720, 1.2), "road": (20, 300, 0, 0.1),
               "voices": (200, 2500, 160, 4.5), "voice": (200, 2500, 160, 4.5), "shout": (250, 3500, 240, 3.0),
               "clap": (500, 7000, 0, 0), "sneeze": (300, 6000, 0, 0), "speaker": (400, 3500, 900, 2.0), "noise": (80, 4000, 0, 0)}
_SIMMIC = {"n": 0, "rng": None}


def _simmic_piece(kind, n, t0):
    """n samples (RMS 1) that sound roughly like this kind"""
    lo, hi, tone, am = SIMMIC_KIND.get(kind, SIMMIC_KIND["noise"])
    rng = _SIMMIC["rng"]
    f = np.fft.rfftfreq(n, 1.0 / AUDIO_RATE)
    spec = np.fft.rfft(rng.standard_normal(n))
    spec *= ((f >= lo) & (f <= hi)) * (1.0 / np.sqrt(np.maximum(f, 20.0) / 200.0) if hi <= 600 else 1.0)
    x = np.fft.irfft(spec, n)
    t = t0 + np.arange(n) / AUDIO_RATE
    if tone:
        x = x * 0.5 + np.sin(2 * np.pi * tone * t) * np.std(x) * 2.0
    if am:
        x = x * (0.25 + 0.75 * np.clip(np.sin(2 * np.pi * am * t), 0.0, 1.0))
    s = float(np.sqrt(np.mean(x * x)))
    return x / s if s > 1e-9 else x


def sim_mic_pcm(mic, n):
    """250 feed_sim: n samples 16 bit / 16 kHz from the «mic» field of the 3D simulator, as loud as mic["db"]"""
    if _SIMMIC["rng"] is None:
        _SIMMIC["rng"] = np.random.default_rng()
    t0 = _SIMMIC["n"] / AUDIO_RATE
    _SIMMIC["n"] += n
    srcs = [s for s in (mic.get("src") or []) if isinstance(s, dict)][:6] or [{"k": "bg", "db": mic.get("db", -70.0)}]
    out = np.zeros(n)
    for s in srcs:
        a = 10.0 ** (float(s.get("db") or -90.0) / 20.0)
        out += _simmic_piece(str(s.get("k") or "noise"), n, t0) * a
    want = 10.0 ** (float(mic.get("db", -70.0)) / 20.0) * 32768.0          # the total (dBFS RMS, like _db in 240)
    cur = float(np.sqrt(np.mean(out * out)))
    if cur > 1e-12:
        out *= want / cur
    return np.clip(out, -32768, 32767).astype("<i2").tobytes()


def _simmic_selftest():
    m = {"db": -30.0, "bg": -55.0, "src": [{"k": "dog", "db": -31.0, "az": 40, "d": 12.0}, {"k": "crickets", "db": -50.0}, {"k": "bg", "db": -55.0}]}
    b = sim_mic_pcm(m, AUDIO_CHUNK * 3)
    a = np.frombuffer(b, dtype="<i2").astype(np.float32)
    lv = _db(float(np.sqrt(np.mean(a * a))))
    assert len(b) == AUDIO_CHUNK * 6 and abs(lv - (-30.0)) < 1.0, f"level {lv} dB instead of -30 dB"
    q = sim_mic_pcm({"db": -62.0, "src": []}, AUDIO_CHUNK)
    a = np.frombuffer(q, dtype="<i2").astype(np.float32)
    lv2 = _db(float(np.sqrt(np.mean(a * a))))
    assert abs(lv2 - (-62.0)) < 1.5, f"background {lv2} dB instead of -62 dB"
    return f"listening in the simulator: {lv:.1f} dB (want -30), background {lv2:.1f} dB (want -62)"


SELFTEST_EXTRA.append(("Listening in the 3D simulator: made-up sound as loud as its microphone (558p)", _simmic_selftest))
