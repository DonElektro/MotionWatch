#@ MoveEye – Teil 639zzb: Piper-Stimme – natürliche Offline-Stimme (neuronales TTS) für Ansagen, Test und «Gesundheit!»: Stimme pro Sprache, Tempo, Lautstärke, «Stimme testen», Laden mit fester Prüfsumme, Ersatz pico2wave / espeak-ng; zu hören am Lautsprecher, im Browser, im Pi-Fenster und im Simulator. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (07.11.2026, freigegeben): Piper als Stimme von MoveEye (viel natürlicher als pico2wave / espeak-ng).
#
# Motor (Lizenz-Entscheid, das Produkt wird verkauft):
#   * NICHT das pip-Paket «piper-tts»: ab 1.3 kommt es aus OHF-Voice/piper1-gpl (GPL-3). Die alten MIT-Fassungen (1.2.x,
#     rhasspy/piper) brauchen «piper-phonemize», das libespeak-ng (GPL-3) in den Python-Prozess lädt (Bindung = Graubereich
#     für ein geschlossenes Produkt), und es gibt sie nur für Python bis 3.11.
#   * Statt dessen: das ONNX-Modell der Stimme direkt mit onnxruntime (MIT, pip, PIPER_ORT unten) und die Lautschrift mit dem
#     Programm espeak-ng (apt; als eigener Prozess aufgerufen wie heute schon der alte Ersatz - keine Bindung). Ablauf wie
#     Piper 1.x (piper-phonemize): Sätze / Teilsätze an , ; : . ! ?, IPA ohne Bindebogen, NFD, Kennzahlen ^ _ … _ $.
#   * Die Rechnung läuft in einem eigenen Python-Prozess mit «nice 10» (PIPER_WORKER): die Erkennung behält den Vorrang,
#     der Hauptprozess lädt kein 60-MB-Modell. Der Prozess bleibt 20 Min. nach der letzten Ansage warm (dann ~0,3-1 s bis zum
#     Ton auf dem Pi 5 für kurze Sätze, geschätzt; kalt +1-2 s), danach beendet er sich.
# Stimmen (PIPER_VOICES): rhasspy/piper-voices auf Hugging Face, feste Revision + feste Grösse + feste Prüfsumme pro Datei in
#   dieser (signierten) Datei - dieselbe Idee wie ZD_SHA256 (012) und SIM3D (300): die Signatur der Hauptdatei bürgt für die
#   Stimme. Laden nur auf Knopfdruck («Stimme laden» / «Stimme testen»), mit Fortsetzen (.part + Range), Fortschritt im Web und
#   im Fenster; stimmt Grösse oder Prüfsumme nicht, wird die Datei verworfen. Danach offline. Eine Stimme ohne vollständige
#   Werte («kommt mit einem Update») wird nie geladen: werkzeuge/piper_stimmen.py --pins (Integrator, mit Internet) prüft und
#   ergänzt die Tabelle.
# Ersatz: tts_engine = auto (Piper, sonst die alte Stimme) | piper (nur Piper) | old (alte Stimme). Fehlt die Stimme, die
#   Laufzeit oder espeak-ng, oder geht etwas schief: pico2wave / espeak-ng wie bisher (250 tts_make).
# Zwischenspeicher: jede erzeugte Ansage als WAV unter DATA_DIR/piper/cache (Schlüssel = sha256 aus Motor, Stimme, Tempo,
#   Text), höchstens PIPER_CACHE_N Dateien / PIPER_CACHE_MB.
# Überall hörbar:
#   * Lautsprecher am Gerät: wie bisher (tts_make schreibt die WAV, sound_play «tts» spielt sie; Lautstärke tts_volume).
#   * Browser: jede Ansage geht als Ereignis «speech» über /api/alerts (alle Seiten, ALERT_JS 510) und ist als
#     /api/tts_audio/<id>.wav abrufbar (hinter dem Web-Passwort). Schalter «🔊 Ton im Browser (Ansagen)» pro Browser
#     (Glocke oben und Karte Lautsprecher); abgespielt über Web Audio, das der erste Tipp auf die Seite freischaltet (iPhone).
#   * Pi-Fenster: spricht über den Lautsprecher des Geräts (Knöpfe «Stimme testen» / «Stimme laden» unter Lautsprecher).
#   * Simulator: ist er verbunden, bekommt er die WAV über POST /speech (simint.gd speech_in) und spielt sie statt des
#     Gemurmels; ältere Simulatoren antworten 404 und behalten das Gemurmel.
# Selbsttest: piper_selftest (Tabelle, Auswahl, Ersatz, Zwischenspeicher, Adressen, Texte). Tests: werkzeuge/piper_test.py.
# ----------------------------------------------------------------------------
PIPER_ORT = "onnxruntime==1.20.1"    # MIT; Wheels für Python 3.10-3.13 aarch64 (Pi 5, Bookworm) und x86_64
PIPER_HF = "https://huggingface.co/rhasspy/piper-voices/resolve/"
PIPER_BASE = {"url": PIPER_HF}       # Tests setzen hier einen lokalen Server ein
PIPER_IDLE_S = 20 * 60
PIPER_CACHE_N, PIPER_CACHE_MB = 300, 40
PIPER_TIMEOUT_S = 60.0
# id -> lang, Name, Revision (fest), Pfad im Repository, Lizenz des Datensatzes (MODEL_CARD), Dateien mit Grösse + Prüfsumme.
# Werte aus voices.json (Revision v1.0.0: size_bytes, md5_digest) und den Seiten der Dateien (SHA256), 07.11.2026.
PIPER_VOICES = {
    "de_DE-thorsten-medium": {
        "lang": "de", "name": "Thorsten", "quality": "medium", "rev": "v1.0.0", "path": "de/de_DE/thorsten/medium/",
        "licence": "CC0 (Thorsten-Voice, github.com/thorstenMueller/Thorsten-Voice)",
        "model": {"size": 63201294, "sha256": "7e64762d8e5118bb578f2eea6207e1a35a8e0c30595010b666f983fc87bb7819",
                  "md5": "a129b00fb3078df43c96bab6c94535c0"},
        "config": {"size": 4819, "sha256": "974adee790533adb273a1ac88f49027d2a1b8f0f2cf4905954a4791e79264e85",
                   "md5": "843a7bd7272724f750534dd5a26d1aad"}},
    "de_DE-thorsten-high": {
        "lang": "de", "name": "Thorsten", "quality": "high", "rev": "v1.0.0", "path": "de/de_DE/thorsten/high/",
        "licence": "CC0 (Thorsten-Voice, github.com/thorstenMueller/Thorsten-Voice)",
        "model": {"size": 113895201, "sha256": "9df1c43c61149ef9b39e618e2b861fbe41e1fcea9390b2dac62e8761573ea4f1",
                  "md5": "256505fe58fb8b9d6ed78b83f6b8a9d2"},
        "config": {"size": 4875, "sha256": "6de734444e4c3f9e33b7ebe2746dbc19b71e85f613e79c65acf623200b99a76a",
                   "md5": "e81686e00a9d825e2488ead660bec6fd"}},
    "en_GB-cori-medium": {
        "lang": "en", "name": "Cori", "quality": "medium", "rev": "v1.0.0", "path": "en/en_GB/cori/medium/",
        "licence": "public domain (LibriVox)",
        "model": {"size": 63531379, "sha256": "1899f98e5fb8310154f3c2973f4b8a929ba7245e722b3d3a85680b833d95f10d",
                  "md5": "f143307611eccea9d976235d0895f57c"},
        "config": {"size": 4966, "sha256": "e262c16d7f192f69d4edd6b4ef8a5915379e67495fcc402f1ab15eeb33da3d36",
                   "md5": "12b1dc45d8919f3475cf296d5f16a4c6"}},
    "fr_FR-siwis-medium": {          # Werte 07.11.2026 (Workflow «Piper-Stimmen»: API + ganze Datei nachgerechnet, gleich)
        "lang": "fr", "name": "Siwis", "quality": "medium", "rev": "v1.0.0", "path": "fr/fr_FR/siwis/medium/",
        "licence": "CC BY 4.0 (SIWIS French Speech Synthesis Database, Univ. Edinburgh) – Nennung nötig",
        "model": {"size": 63201294, "sha256": "641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99",
                  "md5": "20e876e8c839e9b11a26085858f2300c"},
        "config": {"size": 4875, "sha256": "39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959",
                   "md5": "a407e7e6901feb79c2ea2a5466076cce"}},
    "it_IT-paola-medium": {          # gesperrt (Besitzer 07.11.2026): erst wenn die Herkunft der Aufnahmen geklärt ist, Werte eintragen
        "lang": "it", "name": "Paola", "quality": "medium", "rev": "3f71c558aea760af723ae1c111c62f265892b59f",
        "path": "it/it_IT/paola/medium/", "licence": "CC0 (paolapersico1/Voice-Dataset-Italian, Herkunft der Aufnahmen prüfen)",
        "model": {"size": 0, "sha256": "6fc918b5a0ea6137382833dddfa567bffbe6a5060c02043c87192ee59c04210c"},
        "config": {"size": 0}},
}
PIPER_DEFAULT = {"de": "de_DE-thorsten-medium", "fr": "fr_FR-siwis-medium", "it": "it_IT-paola-medium",
                 "en": "en_GB-cori-medium", "rm": "de_DE-thorsten-medium"}     # Rumantsch: keine Piper-Stimme -> Deutsch
PIPER_ENGINES = (("auto", "Piper (else the old voice)"), ("piper", "only Piper (no fallback)"),
                 ("old", "old voice (pico2wave / espeak-ng)"))
_PIPER_ID_RE = re.compile(r"^[0-9a-f]{20}$")

for _k, _v in {"tts_engine": "auto", "tts_speed": 1.0, "tts_volume": 80,
               **{"tts_voice_" + _L: PIPER_DEFAULT[_L] for _L in LANGS}}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)   # 636 took its copy before this part

PIPER = {"lock": threading.Lock(), "proc": None, "q": None, "last": 0.0, "model": "", "err": "", "t_err": 0.0,
         "ms": None, "warm_t": 0.0, "install": "", "install_step": "", "sim_ok": None}
PIPER_DL = {"voice": "", "running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": ""}


def piper_dir():
    return os.path.join(DATA_DIR, "piper")


def piper_cache_dir():
    return os.path.join(piper_dir(), "cache")


def piper_paths(vid):
    d = piper_dir()
    return os.path.join(d, vid + ".onnx"), os.path.join(d, vid + ".onnx.json")


def piper_pin_ok(pin):
    """a file pin is complete: exact size and a sha256 (64 hex) or at least an md5 (32 hex) - nothing else is downloaded"""
    if not isinstance(pin, dict) or not isinstance(pin.get("size"), int) or pin["size"] <= 0:
        return False
    sha, md5 = str(pin.get("sha256") or ""), str(pin.get("md5") or "")
    if sha and not re.fullmatch(r"[0-9a-f]{64}", sha):
        return False
    if md5 and not re.fullmatch(r"[0-9a-f]{32}", md5):
        return False
    return bool(sha or md5)


def piper_pinned(vid):
    v = PIPER_VOICES.get(vid)
    return bool(v) and piper_pin_ok(v.get("model")) and bool((v.get("model") or {}).get("sha256")) and piper_pin_ok(v.get("config"))


def piper_installed(vid):
    """both files are there with the pinned size and were checked once at the download (marker <id>.ok holds the sha256)"""
    v = PIPER_VOICES.get(vid)
    if not v or not piper_pinned(vid):
        return False
    m, c = piper_paths(vid)
    try:
        if os.path.getsize(m) != v["model"]["size"] or os.path.getsize(c) != v["config"]["size"]:
            return False
        with open(os.path.join(piper_dir(), vid + ".ok"), encoding="utf-8") as f:
            return f.read().strip() == v["model"]["sha256"]
    except OSError:
        return False


def piper_runtime():
    """(onnxruntime there?, espeak-ng there?) - the worker needs both"""
    import importlib.util
    try:
        ort = importlib.util.find_spec("onnxruntime") is not None
    except (ImportError, ValueError):
        ort = False
    return ort, bool(shutil.which("espeak-ng"))


def piper_voice_for(lang=None):
    """the chosen Piper voice of a language, or "" (old voice / engine «old»)"""
    L = norm_lang(lang or CFG.get("lang"))
    if str(CFG.get("tts_engine") or "auto") == "old":
        return ""
    vid = str(CFG.get("tts_voice_" + L) or PIPER_DEFAULT.get(L, ""))
    return vid if vid in PIPER_VOICES else ""


def piper_ready(lang=None):
    vid = piper_voice_for(lang)
    return bool(vid) and piper_installed(vid) and all(piper_runtime())


def piper_key(engine, voice, speed, text):
    return hashlib.sha256(f"{engine}|{voice}|{float(speed):.2f}|{text}".encode("utf-8")).hexdigest()[:20]


def piper_cache_path(sid):
    return os.path.join(piper_cache_dir(), sid + ".wav")


def piper_cache_put(sid, src):
    try:
        os.makedirs(piper_cache_dir(), exist_ok=True)
        dst = piper_cache_path(sid)
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst + ".tmp"); os.replace(dst + ".tmp", dst)
        piper_cache_trim()
        return True
    except OSError:
        return False


def piper_cache_trim():
    try:
        fs = [os.path.join(piper_cache_dir(), f) for f in os.listdir(piper_cache_dir()) if f.endswith(".wav")]
    except OSError:
        return
    fs.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    tot = sum(os.path.getsize(p) for p in fs if os.path.exists(p))
    while fs and (len(fs) > PIPER_CACHE_N or tot > PIPER_CACHE_MB * 1024 * 1024):
        p = fs.pop(0)
        try:
            tot -= os.path.getsize(p); os.remove(p)
        except OSError:
            pass


def piper_wav_seconds(path):
    try:
        import wave
        with wave.open(path) as w_:
            return w_.getnframes() / float(w_.getframerate() or 1)
    except Exception:
        return 0.0


# ---- the worker (own process, nice 10): phonemes with espeak-ng, the model with onnxruntime --------------------------------
PIPER_WORKER = r'''
import json, os, re, subprocess, sys, time, unicodedata, wave
def out(d):
    sys.stdout.write(json.dumps(d) + "\n"); sys.stdout.flush()
try:
    import numpy as np
    import onnxruntime as ort
except Exception as e:
    out({"ready": False, "error": "onnxruntime: " + str(e)[:160]}); sys.exit(0)
S = {}
PUN = {",": ", ", ";": "; ", ":": ": ", ".": ".", "!": "!", "?": "?"}
def espeak(chunk, voice):
    if os.environ.get("MW_PIPER_FAKE_PHON") == "1":
        return chunk.lower()
    r = subprocess.run(["espeak-ng", "-q", "--ipa", "-v", voice, "--", chunk], capture_output=True, timeout=20)
    if r.returncode != 0:
        raise RuntimeError("espeak-ng: " + (r.stderr or b"").decode("utf-8", "replace").strip()[:120])
    ph = " ".join(r.stdout.decode("utf-8", "replace").split())
    return re.sub(r"\([a-z]{2,3}(-[a-z0-9]+)?\)", "", ph)
def sentences(text, voice):
    res, cur = [], ""
    for chunk, p in re.findall(r"([^,;:.!?]*)([,;:.!?]+|$)", text):
        if chunk.strip():
            cur += espeak(chunk.strip(), voice)
        if p:
            cur += PUN.get(p[0], "")
            if p[0] in ".!?":
                if cur.strip(): res.append(cur.strip())
                cur = ""
    if cur.strip(): res.append(cur.strip())
    return res
def ids(ph, m):
    pad = list(m.get("_", [0]))
    x = list(m.get("^", [1])) + pad
    for c in unicodedata.normalize("NFD", ph):
        if c in m:
            x += list(m[c]) + pad
    return x + list(m.get("$", [2]))
def load(model, config, threads):
    if S.get("model") != model:
        so = ort.SessionOptions(); so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
        with open(config, encoding="utf-8") as f:
            cfg = json.load(f)
        S.clear(); S.update(model=model, cfg=cfg, sess=ort.InferenceSession(model, so, providers=["CPUExecutionProvider"]))
        S["names"] = {i.name for i in S["sess"].get_inputs()}
def synth(q):
    t0 = time.time()
    load(q["model"], q["config"], int(q.get("threads") or 2))
    cfg = S["cfg"]; inf = cfg.get("inference") or {}
    rate = int((cfg.get("audio") or {}).get("sample_rate") or 22050)
    voice = str((cfg.get("espeak") or {}).get("voice") or q.get("lang") or "de")
    speed = max(0.5, min(2.0, float(q.get("speed") or 1.0)))
    sc = np.array([float(inf.get("noise_scale", 0.667)), float(inf.get("length_scale", 1.0)) / speed,
                   float(inf.get("noise_w", 0.8))], dtype=np.float32)
    pcm = []
    for s in sentences(q["text"], voice):
        x = np.array([ids(s, cfg["phoneme_id_map"])], dtype=np.int64)
        feed = {"input": x, "input_lengths": np.array([x.shape[1]], dtype=np.int64), "scales": sc}
        if "sid" in S["names"]:
            feed["sid"] = np.array([0], dtype=np.int64)
        a = np.asarray(S["sess"].run(None, feed)[0], dtype=np.float32).reshape(-1)
        a = a * (32767.0 / max(0.01, float(np.abs(a).max()) if a.size else 1.0))
        pcm.append(np.clip(a, -32767, 32767).astype("<i2")); pcm.append(np.zeros(int(rate * 0.12), dtype="<i2"))
    if not pcm:
        raise RuntimeError("nothing to say")
    y = np.concatenate(pcm)
    tmp = q["out"] + ".tmp"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(y.tobytes())
    os.replace(tmp, q["out"])
    return {"ok": True, "dur": round(len(y) / float(rate), 3), "ms": int((time.time() - t0) * 1000)}
out({"ready": True, "ort": getattr(ort, "__version__", "?")})
for line in sys.stdin:
    try:
        out(synth(json.loads(line)))
    except Exception as e:
        out({"ok": False, "error": str(e)[:200]})
'''


def _piper_reader(p, q):
    try:
        for line in p.stdout:
            try:
                q.put(json.loads(line))
            except ValueError:
                pass
    except Exception:
        pass
    q.put(None)


def piper_worker_start():
    """the worker process (called with PIPER["lock"]); (ok, error)"""
    import queue
    p = PIPER["proc"]
    if p is not None and p.poll() is None:
        return True, ""
    os.makedirs(piper_dir(), exist_ok=True)
    cmd = [sys.executable, "-E"] + (["-P"] if sys.version_info >= (3, 11) else []) + ["-c", PIPER_WORKER]
    if shutil.which("nice"):
        cmd = ["nice", "-n", "10"] + cmd                 # the detection keeps the priority
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                             bufsize=1, cwd=piper_dir(), env={k: v for k, v in os.environ.items() if k in (
                                 "PATH", "HOME", "LANG", "LC_ALL", "USER", "MW_PIPER_FAKE_PHON")})
    except OSError as e:
        return False, str(e)[:160]
    q = queue.Queue()
    threading.Thread(target=_piper_reader, args=(p, q), daemon=True, name="piper-read").start()
    try:
        r = q.get(timeout=30)
    except queue.Empty:
        r = None
    if not r or not r.get("ready"):
        try:
            p.kill()
        except OSError:
            pass
        return False, (r or {}).get("error") or "Piper did not start"
    PIPER.update(proc=p, q=q, model="", last=time.time(), warm_t=time.time())
    _piper_idle_watch()
    return True, ""


def piper_worker_stop():
    p = PIPER.get("proc")
    PIPER["proc"] = None
    if p is not None:
        try:
            p.stdin.close()
        except Exception:
            pass
        try:
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except OSError:
                pass


def _piper_idle_watch():
    if PIPER.get("idle_thread"):
        return
    PIPER["idle_thread"] = True

    def run():
        while True:
            time.sleep(30)
            with PIPER["lock"]:
                if PIPER.get("proc") is not None and time.time() - PIPER["last"] > PIPER_IDLE_S:
                    piper_worker_stop()
    threading.Thread(target=run, daemon=True, name="piper-idle").start()


def piper_synth(text, vid, out, speed=None):
    """synthesise text with the voice vid into the WAV file out; (ok, error, info)"""
    import queue
    v = PIPER_VOICES.get(vid)
    if not v or not piper_installed(vid):
        return False, "voice not loaded", {}
    m, c = piper_paths(vid)
    with PIPER["lock"]:
        ok, err = piper_worker_start()
        if not ok:
            PIPER.update(err=err, t_err=time.time())
            return False, err, {}
        req = {"text": text, "model": m, "config": c, "out": os.path.abspath(out), "lang": v["lang"],
               "speed": float(CFG.get("tts_speed") if speed is None else speed), "threads": 2}
        try:
            PIPER["proc"].stdin.write(json.dumps(req) + "\n"); PIPER["proc"].stdin.flush()
            r = PIPER["q"].get(timeout=PIPER_TIMEOUT_S)
        except (OSError, ValueError, queue.Empty) as e:
            piper_worker_stop()
            r = {"ok": False, "error": "Piper: " + (str(e)[:100] or "no answer")}
        if r is None:
            piper_worker_stop(); r = {"ok": False, "error": "Piper stopped"}
        PIPER["last"] = time.time()
    if not r.get("ok"):
        PIPER.update(err=str(r.get("error") or "Piper failed")[:200], t_err=time.time())
        return False, PIPER["err"], {}
    PIPER.update(err="", ms=r.get("ms"))
    return True, "", r


def piper_warm(lang=None):
    """start the worker early (after the start of MoveEye, when the settings page asks): the first announcement comes faster"""
    if not piper_ready(lang):
        return False

    def run():
        with PIPER["lock"]:
            ok, _e = piper_worker_start()
            if ok:
                PIPER["last"] = time.time()
    threading.Thread(target=run, daemon=True, name="piper-warm").start()
    return True


# ---- the speech path: Piper first (cache), else the old engine (250) ----------------------------------------------------------
TTS.setdefault("id", ""); TTS.setdefault("engine", ""); TTS.setdefault("text", "")
_tts_make_639zzb = tts_make


# wraps: tts_make
def tts_make(text, lang, path):                           # + 639zzb: Piper with the cache; the old engine as fallback
    text = re.sub(r"[\x00-\x1f]", " ", str(text or "")).strip()[:400]
    L = norm_lang(lang or CFG.get("lang"))
    eng = str(CFG.get("tts_engine") or "auto")
    vid = piper_voice_for(L)
    TTS.update(id="", engine="", text=text)
    if vid and eng != "old":
        sid = piper_key("piper", vid, CFG.get("tts_speed", 1.0), text)
        cp = piper_cache_path(sid)
        try:
            if os.path.isfile(cp) and os.path.getsize(cp) > 100:
                shutil.copyfile(cp, path); os.utime(cp, None)
                TTS.update(id=sid, engine="piper")
                return True, ""
        except OSError:
            pass
        if piper_ready(L):
            ok, err, _i = piper_synth(text, vid, path)
            if ok and os.path.isfile(path) and os.path.getsize(path) > 100:
                piper_cache_put(sid, path)
                TTS.update(id=sid, engine="piper")
                return True, ""
            log_event("sys", f"Piper voice: {err} - old voice instead"[:160])
            if eng == "piper":
                return False, err
        elif eng == "piper":
            return False, "Piper voice not ready (load the voice under Loudspeaker)"
    ok, err = _tts_make_639zzb(text, L, path)
    if ok:
        sid = piper_key("old", L, 1.0, text)
        if piper_cache_put(sid, path):
            TTS.update(id=sid, engine="old")
    return ok, err


_tts_engine_639zzb = tts_engine


# wraps: tts_engine
def tts_engine():                                         # + 639zzb: «piper» when the voice of the language is ready
    if str(CFG.get("tts_engine") or "auto") != "old" and piper_ready():
        return "piper"
    return _tts_engine_639zzb()


def speech_alert(sid, text=""):
    """an announcement for the open web pages (ALERT_JS 510 plays /api/tts_audio/<id>.wav when «Sound in the browser» is on)"""
    if not _PIPER_ID_RE.match(str(sid or "")):
        return False
    with ALERTS_COND:
        ALERTS["seq"] += 1
        ALERTS["items"].append(dict(seq=ALERTS["seq"], kind="speech", text=str(text or "")[:200], id=sid,
                                    time=datetime.now().strftime("%H:%M:%S"), ts=time.time()))
        ALERTS_COND.notify_all()
    return True


def speech_to_sim(path):
    """the simulator plays the real announcement instead of its murmur (simint.gd speech_in); older ones answer 404"""
    try:
        if not sim_speaker() or not os.path.isfile(path) or os.path.getsize(path) > 4 * 1024 * 1024:
            return False
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, NameError):
        return False

    def run():
        try:
            req = urllib.request.Request(sim_base() + "/speech", data=data, method="POST",
                                         headers={"Content-Type": "audio/wav", "User-Agent": "MotionWatch"})
            with _SIM_OPENER.open(req, timeout=4) as r:
                PIPER["sim_ok"] = r.status == 200
        except Exception:
            PIPER["sim_ok"] = False
    threading.Thread(target=run, daemon=True, name="speech-sim").start()
    return True


def _announce_file_id(name):
    """a saved announcement («Announcement ….wav» in all languages) played as a sound: into the cache for the browser"""
    if not any(name.startswith(tr("Announcement", L_) + " ") for L_ in LANGS):
        return ""
    p = os.path.join(sounds_dir(), name)
    try:
        st = os.stat(p)
        sid = hashlib.sha256(f"file|{name}|{st.st_size}|{int(st.st_mtime)}".encode("utf-8")).hexdigest()[:20]
        if not os.path.isfile(piper_cache_path(sid)):
            piper_cache_put(sid, p)
        return sid
    except OSError:
        return ""


_sound_play_639zzb = sound_play


# wraps: sound_play
def sound_play(kind=None, seconds=None, volume=None, reason="test"):   # + 639zzb: announcements also to the browser + the simulator
    k = str(kind or "")
    sid, path, text = "", "", ""
    if k == "tts":
        sid, path, text = TTS.get("id") or "", TTS["file"], TTS.get("text") or ""
        if volume is None:
            volume = CFG.get("tts_volume", 80)
    elif k.startswith("file:"):
        sid = _announce_file_id(k[5:])
        path = os.path.join(sounds_dir(), k[5:]) if sid else ""
        text = os.path.splitext(k[5:])[0] if sid else ""
    if sid:
        speech_alert(sid, text)
        speech_to_sim(path)
    return _sound_play_639zzb(kind, seconds, volume, reason)


# ---- download: pinned revision, size and checksum; resume; progress ----------------------------------------------------------
def piper_url(vid, which):
    v = PIPER_VOICES[vid]
    return PIPER_BASE["url"] + v["rev"] + "/" + v["path"] + vid + (".onnx" if which == "model" else ".onnx.json") + "?download=true"


def piper_check_file(p, pin):
    """(ok, error): exact size and every pinned checksum"""
    try:
        if os.path.getsize(p) != pin["size"]:
            return False, "size wrong - the file was changed or is damaged"
        hs = {"sha256": hashlib.sha256(), "md5": hashlib.md5()}
        with open(p, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    break
                for h in hs.values():
                    h.update(b)
    except OSError as e:
        return False, str(e)[:120]
    for k, h in hs.items():
        if pin.get(k) and h.hexdigest() != pin[k]:
            return False, "checksum wrong - the file was changed or is damaged"
    return True, ""


def piper_fetch(url, dest, pin, dl=None):
    """fetch one file with resume (.part + Range) and check it; raises on any problem (the .part is removed on a wrong check)"""
    dl = PIPER_DL if dl is None else dl
    part = dest + ".part"
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    if have > pin["size"]:
        os.remove(part); have = 0
    if have < pin["size"]:
        hdr = {"Range": f"bytes={have}-"} if have else {}
        with urllib.request.urlopen(_upd_request(url, hdr), timeout=30) as r:
            code = getattr(r, "status", 200)
            if have and code != 206:
                have = 0                                     # the server does not resume: from the start
            elif have and not str(r.headers.get("Content-Range") or "").startswith(f"bytes {have}-"):
                have = 0
            dl["got"] += have
            with open(part, "ab" if have else "wb") as f:
                while True:
                    if dl.get("stop"):
                        raise InterruptedError("cancelled")
                    b = r.read(1 << 16)
                    if not b:
                        break
                    have += len(b)
                    if have > pin["size"]:
                        raise ValueError("file too large")
                    f.write(b); dl["got"] += len(b)
    ok, err = piper_check_file(part, pin)
    if not ok:
        try:
            os.remove(part)
        except OSError:
            pass
        raise ValueError(err)
    os.replace(part, dest)


def piper_download(vid, wait=False):
    """load a voice once (background); (ok, error)"""
    if vid not in PIPER_VOICES:
        return False, "unknown voice"
    if not piper_pinned(vid):
        return False, "This voice is not pinned yet (comes with an update)"
    if piper_installed(vid):
        return True, ""
    if PIPER_DL["running"]:
        return False, "already running"
    v = PIPER_VOICES[vid]
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 1 << 40
    if free < v["model"]["size"] + 300 * 1024 * 1024:
        return False, "not enough free space on the memory card"
    PIPER_DL.update(voice=vid, running=True, got=0, total=v["model"]["size"] + v["config"]["size"], msg="", stop=False, done="")

    def work():
        try:
            os.makedirs(piper_dir(), exist_ok=True)
            m, c = piper_paths(vid)
            try:
                os.remove(os.path.join(piper_dir(), vid + ".ok"))
            except OSError:
                pass
            for which, dest in (("config", c), ("model", m)):
                pin = v[which]
                if os.path.isfile(dest) and piper_check_file(dest, pin)[0]:
                    PIPER_DL["got"] += pin["size"]; continue
                piper_fetch(piper_url(vid, which), dest, pin)
            with open(c, encoding="utf-8") as f:
                cj = json.load(f)
            if not isinstance(cj.get("phoneme_id_map"), dict) or not (cj.get("audio") or {}).get("sample_rate"):
                raise ValueError("the voice description is not a Piper voice")
            with open(os.path.join(piper_dir(), vid + ".ok"), "w", encoding="utf-8") as f:
                f.write(v["model"]["sha256"])
            PIPER_DL["done"] = vid
            log_event("sys", f"Piper voice {vid} loaded and checked ({v['licence'][:40]})")
        except InterruptedError:
            PIPER_DL["msg"] = "cancelled"
        except Exception as e:
            try:                                             # network: the readable reason of the update source (390)
                PIPER_DL["msg"] = (_upd_error(e) if hasattr(e, "code") or hasattr(e, "reason") else str(e))[:160]
            except Exception:
                PIPER_DL["msg"] = str(e)[:160]
            log_event("sys", f"Piper voice {vid} not loaded: {PIPER_DL['msg']}")
        finally:
            PIPER_DL["running"] = False
    if wait:
        work()
        return (not PIPER_DL["msg"]), PIPER_DL["msg"]
    threading.Thread(target=work, daemon=True, name="piper-dl").start()
    return True, ""


def piper_delete(vid):
    if vid not in PIPER_VOICES or (PIPER_DL["running"] and PIPER_DL["voice"] == vid):
        return False, "unknown voice"
    with PIPER["lock"]:
        piper_worker_stop()
    for p in list(piper_paths(vid)) + [os.path.join(piper_dir(), vid + x) for x in (".ok", ".onnx.part", ".onnx.json.part")]:
        try:
            os.remove(p)
        except OSError:
            pass
    log_event("sys", f"Piper voice {vid} deleted (frees about {PIPER_VOICES[vid]['model']['size'] // 1048576} MB)")
    return True, ""


PIPER_APT_TIMEOUT_S = 600            # 3.62.1: apt-get for espeak-ng (once apt-get update + install)


def piper_espeak_install():
    """3.62.1: espeak-ng (the phonemes of Piper) with apt, if it is missing - (ok, english reason).
    Same privilege path as the other system calls of MoveEye (050 / 400 / 556): as root directly, otherwise «sudo -n»
    (only works when sudo needs no password, as for the user of Raspberry Pi OS). Never asks for a password; non-interactive
    (DEBIAN_FRONTEND=noninteractive, -y), with a time limit. «Unable to locate package» -> once apt-get update, then again."""
    if shutil.which("espeak-ng"):
        return True, ""
    apt = shutil.which("apt-get")
    if not apt:
        return False, "no apt-get on this system - install espeak-ng by hand"
    pre = [] if (hasattr(os, "geteuid") and os.geteuid() == 0) else ["sudo", "-n"]
    if pre and not shutil.which("sudo"):
        return False, "MoveEye has no rights for apt (no sudo) - in a terminal: sudo apt install espeak-ng"
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", APT_LISTCHANGES_FRONTEND="none")

    def run(args, step):
        PIPER["install_step"] = step
        try:
            r = subprocess.run(pre + [apt] + args, capture_output=True, text=True, timeout=PIPER_APT_TIMEOUT_S, env=env,
                               stdin=subprocess.DEVNULL)
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            return -9, "timeout"
        except OSError as e:
            return -1, str(e)
    inst = ["install", "-y", "--no-install-recommends", "-o", "Dpkg::Options::=--force-confold", "espeak-ng"]
    rc, out = run(inst, "espeak-ng")
    if rc != 0 and re.search(r"Unable to locate package|has no installation candidate|404\s+Not Found|Failed to fetch", out):
        rc_u, out_u = run(["update"], "apt-get update")
        rc, out = run(inst, "espeak-ng") if rc_u == 0 else (rc_u, out_u)
    PIPER["install_step"] = ""
    if rc == 0 and shutil.which("espeak-ng"):
        log_event("sys", "Piper: espeak-ng installed (apt)")
        return True, ""
    low = out.lower()
    if pre and ("password is required" in low or "a terminal is required" in low or "not in the sudoers" in low
                or "may not run sudo" in low):
        why = "MoveEye has no rights for apt (sudo asks for a password) - in a terminal: sudo apt install espeak-ng"
    elif rc == -9:
        why = "apt took too long (over 10 min.) - try again later"
    elif "could not get lock" in low or "unable to acquire the dpkg frontend lock" in low or "is another process using it" in low:
        why = "apt is busy right now (another installation or update) - try again in a few minutes"
    elif "temporary failure resolving" in low or "could not resolve" in low or "failed to fetch" in low:
        why = "no internet for apt - try again with internet"
    elif rc == 0:
        why = "apt finished, but espeak-ng is still missing"
    else:
        why = (out.strip().splitlines() or ["?"])[-1][:120]
    log_event("sys", "Piper: espeak-ng not installed: " + why)
    return False, why


def piper_install():
    """«Install Piper» in the background: espeak-ng (apt, if missing, 3.62.1) and the runtime onnxruntime (pip, MIT, pinned)
    - like the sound recognition (250 sneeze_install)"""
    if PIPER["install"] == "running":
        return False, "already running"
    PIPER["install"] = "running"
    PIPER["install_step"] = ""

    def work():
        try:
            fail = []
            ok_e, why = piper_espeak_install()
            if not ok_e:
                fail.append(tr("espeak-ng could not be installed") + " – " + tr(why))
            if not piper_runtime()[0]:
                PIPER["install_step"] = "onnxruntime"
                r = subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", PIPER_ORT],
                                   capture_output=True, text=True, timeout=1500)
                if r.returncode == 0:
                    log_event("sys", "Piper: runtime installed (" + PIPER_ORT + ")")
                else:
                    fail.append("onnxruntime: " + ((r.stderr or r.stdout).strip().splitlines() or ["?"])[-1][:140])
            PIPER["install"] = "done" if not fail else " · ".join(fail)
            if fail:
                log_event("sys", "Piper: " + PIPER["install"])
        except Exception as e:
            PIPER["install"] = "failed: " + str(e)[:120]
        PIPER["install_step"] = ""
    threading.Thread(target=work, daemon=True, name="piper-install").start()
    return True, ""


def piper_test(lang=None, text=None):
    """«Test voice»: the test sentence in the chosen voice (loads the voice first if needed); (ok, message, id)"""
    L = norm_lang(lang or CFG.get("lang"))
    vid = piper_voice_for(L)
    if vid and not piper_installed(vid) and piper_pinned(vid) and not PIPER_DL["running"]:
        piper_download(vid)
    ok, err = tts_say(text or tr("Attention, you are being filmed.", L), L, False)
    sid = TTS.get("id") or ""
    if not ok and sid and err == "no loudspeaker selected":
        return True, "no loudspeaker selected - only in the browser", sid
    return ok, err if not ok else (tr("speaks with", L) + " " + piper_engine_label(L)), sid


def piper_engine_label(lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    if TTS.get("engine") == "piper":
        v = PIPER_VOICES.get(piper_voice_for(L)) or {}
        return f"Piper · {v.get('name', '?')} ({v.get('quality', '')})"
    return _tts_engine_639zzb() or "–"


def piper_state(lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    ort, esp = piper_runtime()
    vs = []
    for vid, v in PIPER_VOICES.items():
        vs.append({"id": vid, "lang": v["lang"], "name": v["name"], "quality": v["quality"], "licence": v["licence"],
                   "mb": round((v["model"].get("size") or 63000000) / 1048576.0), "pinned": piper_pinned(vid), "installed": piper_installed(vid)})
    cur = {L_: piper_voice_for(L_) for L_ in LANGS}
    return {"engine": str(CFG.get("tts_engine") or "auto"), "voices": vs, "chosen": cur, "voice": cur.get(L, ""),
            "ready": piper_ready(L), "ort": ort, "espeak": esp, "install": PIPER["install"], "install_step": PIPER.get("install_step") or "", "warm": PIPER.get("proc") is not None,
            "dl": dict({k: PIPER_DL[k] for k in ("voice", "running", "got", "total", "done")}, msg=tr_err(PIPER_DL["msg"], L) if PIPER_DL["msg"] else ""),
            "err": tr_err(PIPER["err"], L) if PIPER["err"] and time.time() - PIPER["t_err"] < 600 else "", "ms": PIPER.get("ms"),
            "old": _tts_engine_639zzb() or "", "speed": CFG.get("tts_speed"), "volume": CFG.get("tts_volume"), "sim": PIPER.get("sim_ok")}


def piper_text(lang=None):
    """one line for the window (and tests)"""
    L = norm_lang(lang or CFG.get("lang"))
    s = piper_state(L)
    vid = s["voice"]
    if PIPER_DL["running"]:
        pct = int(100 * PIPER_DL["got"] / max(1, PIPER_DL["total"]))
        return f"{tr('loading the voice …', L)} {pct} %"
    if s["engine"] == "old" or not vid:
        return tr("old voice (pico2wave / espeak-ng)", L)
    parts = []
    v = PIPER_VOICES[vid]
    parts.append(f"{tr('Piper voice', L)}: {v['name']} ({v['quality']}) – " + (
        tr("loaded", L) if piper_installed(vid) else (tr("comes with an update", L) if not piper_pinned(vid)
                                                                      else trf("{mb} MB to load", L, mb=round(v["model"]["size"] / 1048576.0)))))
    if not s["ort"]:
        parts.append(tr("Piper runtime missing (onnxruntime, about 15 MB) – «Install Piper»", L))
    if not s["espeak"]:
        parts.append(tr("espeak-ng is missing – «Install Piper» installs it", L))
    if PIPER["install"] == "running":
        parts.append(tr("installing …", L) + (f" ({PIPER['install_step']})" if PIPER.get("install_step") else ""))
    elif PIPER["install"] and PIPER["install"] != "done":
        parts.append("⚠ " + PIPER["install"])
    if PIPER_DL["msg"]:
        parts.append("⚠ " + tr_err(PIPER_DL["msg"], L))
    if s["err"]:
        parts.append("⚠ " + s["err"])
    return " · ".join(parts)


# ---- settings: engine, a voice per language, speed, volume (Licht & Ton → Lautsprecher; web and window from the lists) ----
TEXTS.extend([("Loudspeaker", "tts_engine", "Speech engine", "enum", "tts_engines")]
             + [("Loudspeaker", "tts_voice_" + _L, _n, "enum", "tts_voices_" + _L) for _L, _n in (
                 ("de", "Voice German"), ("fr", "Voice French"), ("it", "Voice Italian"), ("en", "Voice English"),
                 ("rm", "Voice Romansh (no own voice: German)"))])
TEXT_SPECS.update({k: (kind, extra) for s, k, l, kind, extra in TEXTS if k == "tts_engine" or k.startswith("tts_voice_")})
_piper_sl = next((i for i, s_ in enumerate(SLIDERS) if s_[1] == "talk_gain"), len(SLIDERS) - 1)
SLIDERS.insert(_piper_sl + 1, ("Loudspeaker", "tts_speed", "Speech speed", 0.7, 1.4, 0.05))
SLIDERS.insert(_piper_sl + 2, ("Loudspeaker", "tts_volume", "Speech volume (%)", 10, 100, 5))
SIMPLE_KEYS.update({"tts_volume"})                       # «Simple»: the card «Piper voice» + the volume; the rest under «Expert»
SET_HELP.update({
    "tts_engine": ("Piper is a natural offline voice (about 60 MB per voice, loaded once from Hugging Face and checked). "
                   "«Automatic» speaks with Piper and takes the old voice (pico2wave / espeak-ng) while Piper is missing or fails.",
                   "Piper (else the old voice)"),
    "tts_speed": ("1.0 = normal; smaller = slower, larger = faster (Piper only).", "1.0."),
})

_text_choice_pairs_639zzb = text_choice_pairs


# wraps: text_choice_pairs
def text_choice_pairs(key):                               # + 639zzb: engine and the voices
    ex = (TEXT_SPECS.get(key) or (None, None))[1]
    if ex == "tts_engines":
        return [(k, tr(l)) for k, l in PIPER_ENGINES]
    if isinstance(ex, str) and ex.startswith("tts_voices_"):
        L = ex[len("tts_voices_"):]
        want = "de" if L == "rm" else L
        out = []
        for vid, v in PIPER_VOICES.items():
            if v["lang"] != want:
                continue
            st = "✓ " + tr("loaded") if piper_installed(vid) else (f"⬇ {round(v['model']['size'] / 1048576.0)} MB"
                                                                   if piper_pinned(vid) else tr("comes with an update"))
            out.append((vid, f"{v['name']} ({v['quality']}) · {st}"))
        return out + [("old", tr("old voice (pico2wave / espeak-ng)"))]
    return _text_choice_pairs_639zzb(key)


# ---- web: /api/piper (state, load, cancel, delete, install, test), /api/tts_audio/<id>.wav (behind the password) -------------
_smalltv_routes_639zzb = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzb
    _smalltv_routes_639zzb(app, reply, body)
    from flask import Response, request, send_file

    @app.route("/api/piper", methods=["GET", "POST"])
    def piper_api():
        if request.method == "GET":
            L = norm_lang(request.args.get("lang"))
            piper_warm(L)
            return reply(piper_state(L))
        d = body(); L = norm_lang(d.get("lang")); a = str(d.get("action") or "")
        vid = str(d.get("voice") or piper_voice_for(norm_lang(d.get("tlang") or L)))
        if a == "download":
            ok, err = piper_download(vid)
        elif a == "cancel":
            PIPER_DL["stop"] = True; ok, err = True, ""
        elif a == "delete":
            ok, err = piper_delete(vid)
        elif a == "install":
            ok, err = piper_install()
        elif a == "test":
            ok, msg, sid = piper_test(norm_lang(d.get("tlang") or L), d.get("text"))
            return reply({"ok": ok, "id": sid, "text": tr_err(msg, L) if msg else "", "error": None if ok else tr_err(msg, L),
                          "state": piper_state(L)}, 200 if ok else 400)
        else:
            ok, err = False, "unknown action"
        return reply({"ok": ok, "error": tr_err(err, L) if err else None, "state": piper_state(L)}, 200 if ok else 400)

    @app.route("/api/tts_audio/<name>")
    def piper_audio(name):
        m = re.fullmatch(r"([0-9a-f]{20})\.wav", name or "")
        p_ = piper_cache_path(m.group(1)) if m else ""
        if not p_ or not os.path.isfile(p_):
            return Response("not found", 404)
        return send_file(p_, mimetype="audio/wav", max_age=3600)


# ---- translations (English key: Deutsch, Français, Italiano, Rumantsch) ----------------------------------------------------
_HX_PIPER = {
    "Speech engine": ("Sprach-Ausgabe", "Moteur vocal", "Motore vocale", "Motor da vusch"),
    "Piper (else the old voice)": ("Piper (sonst alte Stimme)", "Piper (sinon l’ancienne voix)", "Piper (altrimenti la voce vecchia)",
                                   "Piper (uschiglio la vusch veglia)"),
    "only Piper (no fallback)": ("nur Piper (kein Ersatz)", "seulement Piper (sans repli)", "solo Piper (nessun ripiego)", "mo Piper (nagin substitut)"),
    "old voice (pico2wave / espeak-ng)": ("alte Stimme (pico2wave / espeak-ng)", "ancienne voix (pico2wave / espeak-ng)",
                                          "voce vecchia (pico2wave / espeak-ng)", "vusch veglia (pico2wave / espeak-ng)"),
    "Voice German": ("Stimme Deutsch", "Voix allemande", "Voce tedesca", "Vusch tudestga"),
    "Voice French": ("Stimme Französisch", "Voix française", "Voce francese", "Vusch franzosa"),
    "Voice Italian": ("Stimme Italienisch", "Voix italienne", "Voce italiana", "Vusch taliana"),
    "Voice English": ("Stimme Englisch", "Voix anglaise", "Voce inglese", "Vusch englaisa"),
    "Voice Romansh (no own voice: German)": ("Stimme Romanisch (keine eigene: Deutsch)", "Voix romanche (pas de voix propre : allemand)",
                                             "Voce romancia (nessuna propria: tedesco)", "Vusch rumantscha (nagina atgna: tudestg)"),
    "Speech speed": ("Sprechtempo", "Vitesse de parole", "Velocità del parlato", "Tempo da discurrer"),
    "Speech volume (%)": ("Lautstärke der Ansage (%)", "Volume de l’annonce (%)", "Volume dell’annuncio (%)", "Volumen da l’annunzia (%)"),
    "loaded": ("geladen", "chargée", "caricata", "chargiada"),
    "{mb} MB to load": ("{mb} MB zu laden", "{mb} Mo à charger", "{mb} MB da caricare", "{mb} MB da chargiar"),
    "comes with an update": ("kommt mit einem Update", "arrive avec une mise à jour", "arriva con un aggiornamento", "vegn cun in’actualisaziun"),
    "Test voice": ("Stimme testen", "Tester la voix", "Prova la voce", "Testar la vusch"),
    "Load voice": ("Stimme laden", "Charger la voix", "Carica la voce", "Chargiar la vusch"),
    "Delete voice": ("Stimme löschen", "Supprimer la voix", "Elimina la voce", "Stizzar la vusch"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "Install Piper": ("Piper installieren", "Installer Piper", "Installa Piper", "Installar Piper"),
    "Piper voice": ("Piper-Stimme", "Voix Piper", "Voce Piper", "Vusch Piper"),
    "🔊 Sound in the browser (announcements)": ("🔊 Ton im Browser (Ansagen)", "🔊 Son dans le navigateur (annonces)",
                                                "🔊 Audio nel browser (annunci)", "🔊 Tun en il navigatur (annunzias)"),
    "Attention, you are being filmed.": ("Achtung, Sie werden gefilmt.", "Attention, vous êtes filmé.", "Attenzione, siete ripresi.",
                                         "Attenziun, Vus vegnis filmads."),
    "Piper runtime missing (onnxruntime, about 15 MB) – «Install Piper»": (
        "Piper-Laufzeit fehlt (onnxruntime, etwa 15 MB) – «Piper installieren»", "Moteur Piper absent (onnxruntime, env. 15 Mo) – «Installer Piper»",
        "Manca il motore Piper (onnxruntime, circa 15 MB) – «Installa Piper»", "Il motor Piper manca (onnxruntime, var 15 MB) – «Installar Piper»"),
    "espeak-ng is missing (sudo apt install espeak-ng)": ("espeak-ng fehlt (sudo apt install espeak-ng)", "espeak-ng manque (sudo apt install espeak-ng)",
                                                          "manca espeak-ng (sudo apt install espeak-ng)", "espeak-ng manca (sudo apt install espeak-ng)"),
    "espeak-ng is missing – «Install Piper» installs it": (
        "espeak-ng fehlt – «Piper installieren» richtet es ein", "espeak-ng manque – «Installer Piper» l’installe",
        "manca espeak-ng – «Installa Piper» lo installa", "espeak-ng manca – «Installar Piper» l’installescha"),
    "espeak-ng could not be installed": ("espeak-ng konnte nicht installiert werden", "espeak-ng n’a pas pu être installé",
                                         "non è stato possibile installare espeak-ng", "espeak-ng n’ha betg pudì vegnir installà"),
    "no apt-get on this system - install espeak-ng by hand": (
        "kein apt-get auf diesem System – espeak-ng von Hand installieren", "pas d’apt-get sur ce système – installer espeak-ng à la main",
        "nessun apt-get su questo sistema – installare espeak-ng a mano", "nagin apt-get sin quest sistem – installar espeak-ng a maun"),
    "MoveEye has no rights for apt (no sudo) - in a terminal: sudo apt install espeak-ng": (
        "MoveEye hat keine Rechte für apt (kein sudo) – im Terminal: sudo apt install espeak-ng",
        "MoveEye n’a pas les droits pour apt (pas de sudo) – dans un terminal : sudo apt install espeak-ng",
        "MoveEye non ha i permessi per apt (niente sudo) – nel terminale: sudo apt install espeak-ng",
        "MoveEye n’ha nagins dretgs per apt (nagin sudo) – en il terminal: sudo apt install espeak-ng"),
    "MoveEye has no rights for apt (sudo asks for a password) - in a terminal: sudo apt install espeak-ng": (
        "MoveEye hat keine Rechte für apt (sudo will ein Passwort) – im Terminal: sudo apt install espeak-ng",
        "MoveEye n’a pas les droits pour apt (sudo demande un mot de passe) – dans un terminal : sudo apt install espeak-ng",
        "MoveEye non ha i permessi per apt (sudo chiede una password) – nel terminale: sudo apt install espeak-ng",
        "MoveEye n’ha nagins dretgs per apt (sudo dumonda in pled-clav) – en il terminal: sudo apt install espeak-ng"),
    "apt took too long (over 10 min.) - try again later": (
        "apt hat zu lange gebraucht (über 10 Min.) – später nochmals versuchen", "apt a pris trop de temps (plus de 10 min) – réessayer plus tard",
        "apt ha impiegato troppo (oltre 10 min) – riprovare più tardi", "apt ha durà memia ditg (dapli che 10 min.) – empruvar pli tard"),
    "apt is busy right now (another installation or update) - try again in a few minutes": (
        "apt ist gerade beschäftigt (andere Installation oder Update) – in ein paar Minuten nochmals",
        "apt est occupé (autre installation ou mise à jour) – réessayer dans quelques minutes",
        "apt è occupato (altra installazione o aggiornamento) – riprovare tra qualche minuto",
        "apt è gist occupà (autra installaziun u actualisaziun) – empruvar en in pèr minutas"),
    "no internet for apt - try again with internet": (
        "kein Internet für apt – mit Internet nochmals versuchen", "pas d’Internet pour apt – réessayer avec Internet",
        "nessuna connessione Internet per apt – riprovare con Internet", "nagin internet per apt – empruvar cun internet"),
    "apt finished, but espeak-ng is still missing": (
        "apt ist fertig, aber espeak-ng fehlt immer noch", "apt a terminé, mais espeak-ng manque toujours",
        "apt ha finito, ma espeak-ng manca ancora", "apt è finì, ma espeak-ng manca anc adina"),
    "loading the voice …": ("lade die Stimme …", "chargement de la voix …", "caricamento della voce …", "chargiar la vusch …"),
    "This voice is not pinned yet (comes with an update)": (
        "Diese Stimme ist noch nicht freigegeben (kommt mit einem Update)", "Cette voix n’est pas encore validée (arrive avec une mise à jour)",
        "Questa voce non è ancora approvata (arriva con un aggiornamento)", "Questa vusch n’è anc betg liberada (vegn cun in’actualisaziun)"),
    "speaks with": ("spricht mit", "parle avec", "parla con", "discurra cun"),
    "Licence": ("Lizenz", "Licence", "Licenza", "Licenza"),
    "installing …": ("installiere …", "installation …", "installazione …", "installar …"),
    "Voice is ready": ("Stimme ist bereit", "La voix est prête", "La voce è pronta", "La vusch è pronta"),
    "Loaded once from Hugging Face (checked), then works offline": (
        "Einmal von Hugging Face geladen (geprüft), danach ohne Internet", "Chargée une fois depuis Hugging Face (vérifiée), puis sans Internet",
        "Caricata una volta da Hugging Face (verificata), poi senza Internet", "Chargiada ina giada da Hugging Face (controllada), lura senza internet"),
    "The voice in the browser needs one tap on the page (iPhone: silent switch off)": (
        "Die Stimme im Browser braucht einmal Antippen der Seite (iPhone: Stummschalter aus)",
        "La voix dans le navigateur demande de toucher une fois la page (iPhone : mode silencieux désactivé)",
        "La voce nel browser richiede un tocco sulla pagina (iPhone: silenzioso disattivato)",
        "La vusch en il navigatur dovra ina giada tutgar la pagina (iPhone: modus silenzius stizzà)"),
    "Piper voice not ready (load the voice under Loudspeaker)": (
        "Piper-Stimme nicht bereit (Stimme unter Lautsprecher laden)", "Voix Piper pas prête (charger la voix sous Haut-parleur)",
        "Voce Piper non pronta (caricare la voce in Altoparlante)", "Vusch Piper betg pronta (chargiar la vusch sut Autpledader)"),
    "voice not loaded": ("Stimme nicht geladen", "voix non chargée", "voce non caricata", "vusch betg chargiada"),
    "not enough free space on the memory card": ("zu wenig freier Platz auf der Speicherkarte", "pas assez d’espace libre sur la carte mémoire",
                                                 "spazio libero insufficiente sulla scheda di memoria", "memia pauc plaz liber sin la carta da memoria"),
    "size wrong - the file was changed or is damaged": ("Grösse falsch – die Datei wurde verändert oder ist beschädigt",
                                                        "taille incorrecte – le fichier a été modifié ou est endommagé",
                                                        "dimensione errata – il file è stato modificato o è danneggiato",
                                                        "grondezza sbagliada – la datoteca è vegnida midada u è donnegiada"),
    "checksum wrong - the file was changed or is damaged": ("Prüfsumme falsch – die Datei wurde verändert oder ist beschädigt",
                                                            "somme de contrôle incorrecte – le fichier a été modifié ou est endommagé",
                                                            "checksum errato – il file è stato modificato o è danneggiato",
                                                            "summa da controlla sbagliada – la datoteca è vegnida midada u è donnegiada"),
    "the voice description is not a Piper voice": ("die Beschreibung ist keine Piper-Stimme", "la description n’est pas une voix Piper",
                                                   "la descrizione non è una voce Piper", "la descripziun n’è betg ina vusch Piper"),
    "no loudspeaker selected - only in the browser": ("kein Lautsprecher gewählt – nur im Browser", "aucun haut-parleur choisi – seulement dans le navigateur",
                                                      "nessun altoparlante scelto – solo nel browser", "nagin autpledader tschernì – mo en il navigatur"),
    "cancelled": ("abgebrochen", "annulé", "annullato", "interrut"),
    "Piper is a natural offline voice (about 60 MB per voice, loaded once from Hugging Face and checked). «Automatic» speaks with Piper and takes the old voice (pico2wave / espeak-ng) while Piper is missing or fails.": (
        "Piper ist eine natürliche Stimme ohne Internet (etwa 60 MB pro Stimme, einmal von Hugging Face geladen und geprüft). "
        "«Automatisch» spricht mit Piper und nimmt die alte Stimme (pico2wave / espeak-ng), solange Piper fehlt oder nicht geht.",
        "Piper est une voix naturelle hors ligne (env. 60 Mo par voix, chargée une fois depuis Hugging Face et vérifiée). "
        "«Automatique» parle avec Piper et prend l’ancienne voix (pico2wave / espeak-ng) tant que Piper manque ou échoue.",
        "Piper è una voce naturale offline (circa 60 MB per voce, caricata una volta da Hugging Face e verificata). "
        "«Automatico» parla con Piper e usa la voce vecchia (pico2wave / espeak-ng) finché Piper manca o non funziona.",
        "Piper è ina vusch natirala senza internet (var 60 MB per vusch, chargiada ina giada da Hugging Face e controllada). "
        "«Automatic» discurra cun Piper e prenda la vusch veglia (pico2wave / espeak-ng) uschè ditg che Piper manca u na va betg."),
    "1.0 = normal; smaller = slower, larger = faster (Piper only).": (
        "1.0 = normal; kleiner = langsamer, grösser = schneller (nur Piper).", "1.0 = normal ; plus petit = plus lent, plus grand = plus rapide (Piper seulement).",
        "1.0 = normale; più piccolo = più lento, più grande = più veloce (solo Piper).", "1.0 = normal; pli pitschen = pli plaun, pli grond = pli svelt (mo Piper)."),
    "1.0.": ("1.0.", "1.0.", "1.0.", "1.0."),
}
for _k, _v in _HX_PIPER.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_PIPER_DE = {_k: _v[0] for _k, _v in _HX_PIPER.items()}

# ---- the main page: the card «Piper voice» under Loudspeaker (ttsBox, 530) ------------------------------------------------
PIPER_WEB_JS = r"""
<script>
Object.assign(I18N.de, /*PIPERDE*/{});
function piperBox() {                                      // 639zzb: Piper voice - state, load (progress), test, sound in the browser
  const w = el("div"); w.id = "piper-box"; w.style.marginTop = "10px";
  const head = el("div", "mut", "🗣 " + t("Piper voice")); head.style.fontWeight = "600";
  const st = el("div", "mut", "…"); st.style.fontSize = "12px";
  const bar = el("div"); bar.style.cssText = "height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin:6px 0;display:none";
  const fill = el("div"); fill.style.cssText = "height:100%;width:0;background:#2f81f7"; bar.appendChild(fill);
  const bs = el("div", "btns"); bs.style.flexWrap = "wrap";
  const bTest = el("button", "", "🗣 " + t("Test voice")), bLoad = el("button", "sec", "⬇ " + t("Load voice")),
        bStop = el("button", "sec", t("Cancel")), bInst = el("button", "sec", "⚙ " + t("Install Piper")), bDel = el("button", "sec", "🗑 " + t("Delete voice"));
  [bTest, bLoad, bStop, bInst, bDel].forEach(b => { b.type = "button"; b.style.fontSize = "12px"; });
  const sw = el("label", "row"); const cb = el("input"); cb.type = "checkbox"; cb.className = "sw"; cb.id = "piper-browser";
  cb.checked = !!(window.mwSpeechOn && mwSpeechOn());
  cb.onchange = () => { if (window.mwSpeechSet) mwSpeechSet(cb.checked); };
  sw.append(el("span", "", t("🔊 Sound in the browser (announcements)")), cb);
  const hint = el("div", "mut", t("The voice in the browser needs one tap on the page (iPhone: silent switch off)")); hint.style.fontSize = "11px";
  const lic = el("div", "mut", ""); lic.style.fontSize = "11px";
  const msg = el("div", "mut", ""); msg.id = "piper-msg";
  bs.append(bTest, bLoad, bStop, bInst, bDel); w.append(head, st, bar, bs, sw, hint, lic, msg);
  let J = null, timer = 0;
  const vName = id => { const v = J && J.voices.find(x => x.id === id); return v ? v.name + " (" + v.quality + ")" : ""; };
  function paint() {
    if (!J) return;
    const v = J.voices.find(x => x.id === J.voice), d = J.dl || {};
    const parts = [];
    if (J.engine === "old" || !v) parts.push(t("old voice (pico2wave / espeak-ng)"));
    else parts.push("Piper · " + vName(v.id) + " – " + (v.installed ? t("loaded") : (v.pinned ? t("{mb} MB to load").replace("{mb}", v.mb) : t("comes with an update"))));
    if (!J.ort) parts.push(t("Piper runtime missing (onnxruntime, about 15 MB) – «Install Piper»"));
    if (!J.espeak) parts.push(t("espeak-ng is missing – «Install Piper» installs it"));
    if (J.install && J.install !== "done") parts.push(J.install === "running" ? t("installing …") + (J.install_step ? " (" + J.install_step + ")" : "") : "⚠ " + J.install);
    if (d.msg) parts.push("⚠ " + d.msg);
    if (J.err) parts.push("⚠ " + J.err);
    st.textContent = parts.join(" · ");
    bar.style.display = d.running ? "" : "none"; fill.style.width = (d.total ? Math.round(100 * d.got / d.total) : 0) + "%";
    if (d.running) st.textContent = t("loading the voice …") + " " + (d.total ? Math.round(100 * d.got / d.total) : 0) + " %";
    bLoad.hidden = !v || v.installed || !v.pinned || d.running || J.engine === "old";
    bStop.hidden = !d.running; bInst.hidden = (J.ort && J.espeak) || J.install === "running"; bDel.hidden = !v || !v.installed;
    lic.textContent = v ? t("Licence") + ": " + v.licence + " · " + t("Loaded once from Hugging Face (checked), then works offline") : "";
    clearTimeout(timer); if (d.running || J.install === "running") timer = setTimeout(load, 1000);
  }
  async function load() { try { J = await (await fetch("/api/piper?lang=" + LANG)).json(); paint(); } catch (e) {} }
  async function act(a) { const r = await post("/api/piper", {action: a, lang: LANG}); if (r.state) { J = r.state; paint(); }
    msg.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); return r; }
  bLoad.onclick = () => act("download"); bStop.onclick = () => act("cancel"); bInst.onclick = () => act("install");
  bDel.onclick = () => { if (confirm(t("Delete voice") + "?")) act("delete"); };
  bTest.onclick = async () => {
    if (window.mwSpeechUnlock) mwSpeechUnlock();          // inside the tap: the browser allows the sound (iPhone)
    bTest.disabled = true; msg.textContent = "…";
    const r = await post("/api/piper", {action: "test", lang: LANG});
    bTest.disabled = false; if (r.state) { J = r.state; paint(); }
    msg.textContent = r.ok ? "✓ " + (r.text || "") : "⚠ " + (r.error || "error");
    if (r.ok && r.id && window.mwSpeak) mwSpeak(r.id);
  };
  load(); return w;
}
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", PIPER_WEB_JS.replace("/*PIPERDE*/{}", json.dumps(_PIPER_DE, ensure_ascii=False), 1) + "</body>", 1)


# ---- the window (Tkinter): state line, «Test voice», «Load voice», «Install Piper» under Loudspeaker (570 calls it) ----------
def piper_tk_box(app, parent):
    import tkinter as tk
    from tkinter import ttk
    lab = ttk.Label(parent, text=piper_text(), style="Mut.TLabel", wraplength=330, justify="left")
    lab.pack(anchor="w", pady=(6, 0))
    bf = ttk.Frame(parent); bf.pack(fill="x", pady=(4, 0))

    def poll(n=0):
        try:
            lab.configure(text=piper_text())
        except tk.TclError:
            return
        if (PIPER_DL["running"] or PIPER["install"] == "running") and n < 3600:
            parent.after(1000, lambda: poll(n + 1))

    def test():
        def run():
            ok, m, _sid = piper_test()
            try:
                app._status("Announcement", ("✓ " if ok else "⚠ ") + tr_err(m))
            except Exception:
                pass
        threading.Thread(target=run, daemon=True, name="piper-tk").start()
        parent.after(800, poll)

    def dl():
        ok, err = piper_download(piper_voice_for())
        if not ok:
            app._status("Announcement", "⚠ " + tr_err(err))
        poll()

    def inst():
        piper_install(); poll()
    ttk.Button(bf, text=tr("Test voice"), command=test).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text=tr("Load voice"), command=dl).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text=tr("Install Piper"), command=inst).pack(side="left", expand=True, fill="x")
    return lab


# ---- the manual: «Piper-Stimme» (all 5 languages, after the section about light and sound) ------------------------------------
_HELP_PIPER = {
    "de": ('<section id="piper" data-icon="🗣"><h2>Piper-Stimme</h2><ul>'
           '<li>MoveEye spricht Ansagen mit <b>Piper</b>, einer natürlichen Stimme ohne Internet. Einmal einrichten unter '
           'Einstellungen → Licht &amp; Ton → Lautsprecher: «Piper installieren» (onnxruntime, etwa 15 MB), «Stimme laden» '
           '(etwa 60 MB von Hugging Face, mit fester Prüfsumme geprüft), dann «Stimme testen». «Piper installieren» richtet auch '
           '<code>espeak-ng</code> ein (apt, ohne Passwort-Abfrage; geht das nicht: <code>sudo apt install espeak-ng</code>).</li>'
           '<li>Pro Sprache eine Stimme (Deutsch: Thorsten, Englisch: Cori, Französisch: Siwis; Italienisch folgt), Tempo und Lautstärke. '
           'Rätoromanisch spricht mit der deutschen Stimme. Fehlt Piper, spricht die alte Stimme (pico2wave / espeak-ng).</li>'
           '<li><b>🔊 Ton im Browser:</b> Schalter bei der Glocke oben oder unter Lautsprecher – Ansagen kommen dann auch aus dem Handy oder PC '
           '(einmal auf die Seite tippen; iPhone: Stummschalter aus). Mit dem Simulator hört man die Ansage im Simulator.</li>'
           '<li><b>Stimmen und Lizenzen:</b> Piper-Modelle von rhasspy/piper-voices (MIT). Thorsten: Thorsten-Voice (Thorsten Müller), CC0. Cori: LibriVox, gemeinfrei. <b>Siwis</b> (Französisch): «SIWIS French Speech Synthesis Database» (University of Edinburgh / Idiap, datashare.ed.ac.uk/handle/10283/2353), Lizenz CC BY 4.0 – wir danken den Urhebern. Die Lautschrift macht espeak-ng (GPL, eigenes Programm), die Rechnung onnxruntime (MIT).</li>'
           '</ul></section>\n'),
    "en": ('<section id="piper" data-icon="🗣"><h2>Piper voice</h2><ul>'
           '<li>MoveEye speaks announcements with <b>Piper</b>, a natural voice without internet. Set it up once under '
           'Settings → Light &amp; sound → Loudspeaker: «Install Piper» (onnxruntime, about 15 MB), «Load voice» '
           '(about 60 MB from Hugging Face, checked with a fixed checksum), then «Test voice». «Install Piper» also sets up '
           '<code>espeak-ng</code> (apt, never asks for a password; if that fails: <code>sudo apt install espeak-ng</code>).</li>'
           '<li>One voice per language (German: Thorsten, English: Cori, French: Siwis; Italian follows), speed and volume. '
           'Romansh speaks with the German voice. Without Piper the old voice speaks (pico2wave / espeak-ng).</li>'
           '<li><b>🔊 Sound in the browser:</b> switch at the bell at the top or under Loudspeaker – announcements then also come from the phone or PC '
           '(tap the page once; iPhone: silent switch off). With the simulator the announcement is heard in the simulator.</li>'
           '<li><b>Voices and licences:</b> Piper models from rhasspy/piper-voices (MIT). Thorsten: Thorsten-Voice (Thorsten Müller), CC0. Cori: LibriVox, public domain. <b>Siwis</b> (French): «SIWIS French Speech Synthesis Database» (University of Edinburgh / Idiap, datashare.ed.ac.uk/handle/10283/2353), licence CC BY 4.0 – with thanks to its authors. Phonemes by espeak-ng (GPL, separate program), inference by onnxruntime (MIT).</li>'
           '</ul></section>\n'),
    "fr": ('<section id="piper" data-icon="🗣"><h2>Voix Piper</h2><ul>'
           '<li>MoveEye prononce les annonces avec <b>Piper</b>, une voix naturelle sans Internet. À configurer une fois sous '
           'Réglages → Lumière et son → Haut-parleur : «Installer Piper» (onnxruntime, env. 15 Mo), «Charger la voix» '
           '(env. 60 Mo depuis Hugging Face, vérifiée par une somme de contrôle fixe), puis «Tester la voix». Le Pi a besoin une fois de '
           '<code>sudo apt install espeak-ng</code>.</li>'
           '<li>Une voix par langue (allemand : Thorsten, anglais : Cori, français : Siwis ; l’italien suivra), vitesse et volume. Le romanche parle avec la voix allemande. Sans Piper, l’ancienne voix parle.</li>'
           '<li><b>🔊 Son dans le navigateur :</b> interrupteur à la cloche en haut ou sous Haut-parleur – les annonces sortent aussi du téléphone ou du PC '
           '(toucher une fois la page ; iPhone : mode silencieux désactivé). Avec le simulateur, l’annonce s’entend dans le simulateur.</li>'
           '<li><b>Voix et licences :</b> modèles Piper de rhasspy/piper-voices (MIT). Thorsten : Thorsten-Voice (Thorsten Müller), CC0. Cori : LibriVox, domaine public. <b>Siwis</b> (français) : «SIWIS French Speech Synthesis Database» (University of Edinburgh / Idiap, datashare.ed.ac.uk/handle/10283/2353), licence CC BY 4.0 – merci à ses auteurs. Phonèmes : espeak-ng (GPL, programme séparé), calcul : onnxruntime (MIT).</li>'
           '</ul></section>\n'),
    "it": ('<section id="piper" data-icon="🗣"><h2>Voce Piper</h2><ul>'
           '<li>MoveEye pronuncia gli annunci con <b>Piper</b>, una voce naturale senza Internet. Da configurare una volta in '
           'Impostazioni → Luce e suono → Altoparlante: «Installa Piper» (onnxruntime, circa 15 MB), «Carica la voce» '
           '(circa 60 MB da Hugging Face, verificata con un checksum fisso), poi «Prova la voce». Sul Pi serve una volta '
           '<code>sudo apt install espeak-ng</code>.</li>'
           '<li>Una voce per lingua (tedesco: Thorsten, inglese: Cori, francese: Siwis; l’italiano seguirà), velocità e volume. Il romancio parla con la voce tedesca. Senza Piper parla la voce vecchia.</li>'
           '<li><b>🔊 Audio nel browser:</b> interruttore alla campanella in alto o in Altoparlante – gli annunci escono anche dal telefono o dal PC '
           '(toccare una volta la pagina; iPhone: silenzioso disattivato). Con il simulatore l’annuncio si sente nel simulatore.</li>'
           '<li><b>Voci e licenze:</b> modelli Piper da rhasspy/piper-voices (MIT). Thorsten: Thorsten-Voice (Thorsten Müller), CC0. Cori: LibriVox, pubblico dominio. <b>Siwis</b> (francese): «SIWIS French Speech Synthesis Database» (University of Edinburgh / Idiap, datashare.ed.ac.uk/handle/10283/2353), licenza CC BY 4.0 – grazie agli autori. Fonemi: espeak-ng (GPL, programma separato), calcolo: onnxruntime (MIT).</li>'
           '</ul></section>\n'),
    "rm": ('<section id="piper" data-icon="🗣"><h2>Vusch Piper</h2><ul>'
           '<li>MoveEye di annunzias cun <b>Piper</b>, ina vusch natirala senza internet. Ina giada endrizzar sut '
           'Parameters → Glisch &amp; tun → Autpledader: «Installar Piper» (onnxruntime, var 15 MB), «Chargiar la vusch» '
           '(var 60 MB da Hugging Face, controllada cun ina summa fixa), lura «Testar la vusch». Il Pi dovra ina giada '
           '<code>sudo apt install espeak-ng</code>.</li>'
           '<li>Ina vusch per lingua (tudestg: Thorsten, englais: Cori, franzos: Siwis; talian suonda), tempo e volumen. Il rumantsch discurra cun la vusch tudestga. Senza Piper discurra la vusch veglia.</li>'
           '<li><b>🔊 Tun en il navigatur:</b> interruptur tar la sain sura u sut Autpledader – las annunzias vegnan lura er dal telefonin u dal PC '
           '(ina giada tutgar la pagina; iPhone: modus silenzius stizzà). Cun il simulatur auda ins l’annunzia en il simulatur.</li>'
           '<li><b>Vuschs e licenzas:</b> models Piper da rhasspy/piper-voices (MIT). Thorsten: Thorsten-Voice (Thorsten Müller), CC0. Cori: LibriVox, dominio public. <b>Siwis</b> (franzos): «SIWIS French Speech Synthesis Database» (University of Edinburgh / Idiap, datashare.ed.ac.uk/handle/10283/2353), licenza CC BY 4.0 – grazia fitg als auturs. Fonems: espeak-ng (GPL, agen program), quint: onnxruntime (MIT).</li>'
           '</ul></section>\n'),
}


def _help_piper(doc, lang):
    if 'id="piper"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_PIPER[lang] + doc[i:] if i >= 0 else doc


_hp_en_piper = HELP_PAGE.find('<div lang="en">')
if _hp_en_piper > 0:
    HELP_PAGE = _help_piper(HELP_PAGE[:_hp_en_piper], "de") + _help_piper(HELP_PAGE[_hp_en_piper:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_piper(HELP_X[_L], _L)


def _piper_boot_warm():
    """some time after the start: warm the worker when the voice of the language is ready (first announcement faster)"""
    def run():
        time.sleep(90)
        try:
            piper_warm()
        except Exception:
            pass
    threading.Thread(target=run, daemon=True, name="piper-boot").start()


if __name__ == "__main__" and "--self-test" not in sys.argv:
    _piper_boot_warm()


# ---- self-test --------------------------------------------------------------------------------------------------------------
def piper_selftest():
    """the table, the choice, the fallback to the old engine, the cache and the browser address; no network, no model"""
    for vid, v in PIPER_VOICES.items():
        assert re.fullmatch(r"[a-z]{2}_[A-Z]{2}-[a-z_]+-(x_low|low|medium|high)", vid), vid
        assert v["lang"] in LANGS and v["licence"] and v["path"].endswith("/") and vid.startswith(v["path"].split("/")[1]), vid
        assert re.fullmatch(r"v\d+\.\d+\.\d+|[0-9a-f]{40}", v["rev"]), f"{vid}: revision must be a tag or a commit"
        assert re.fullmatch(r"[0-9a-f]{64}", v["model"].get("sha256") or ""), f"{vid}: the model needs a sha256"
        assert piper_pinned(vid) == (piper_pin_ok(v["model"]) and piper_pin_ok(v["config"])), vid
        assert piper_url(vid, "model").startswith(PIPER_HF + v["rev"] + "/") or PIPER_BASE["url"] != PIPER_HF
    for L_ in LANGS:
        assert PIPER_DEFAULT[L_] in PIPER_VOICES and CFG.get("tts_voice_" + L_), L_
        ks = [k for k, _l in text_choice_pairs("tts_voice_" + L_)]
        assert "old" in ks and PIPER_DEFAULT[L_] in ks, (L_, ks)
    assert piper_pinned("de_DE-thorsten-medium"), "the default German voice must be pinned"
    assert piper_pinned("fr_FR-siwis-medium") and not piper_pinned("it_IT-paola-medium"), "French on (07.11.2026), Italian locked"
    assert [k for k, _l in text_choice_pairs("tts_engine")] == ["auto", "piper", "old"]
    for k, v in _HX_PIPER.items():
        assert len(v) == 4 and all(v) and k in DE and all(k in TRX[L] for L in ("fr", "it", "rm")), k
    assert len({piper_key("piper", "a", 1.0, "x"), piper_key("piper", "a", 1.1, "x"), piper_key("piper", "b", 1.0, "x"), piper_key("old", "a", 1.0, "x")}) == 4
    assert _PIPER_ID_RE.match(piper_key("piper", "a", 1.0, "x"))
    keep = {k: CFG.get(k) for k in ("tts_engine", "tts_voice_de", "lang")}
    keep_dir = globals()["DATA_DIR"]
    tmp = tempfile.mkdtemp(prefix="mw_piper_")
    G = globals(); keep_make = G["_tts_make_639zzb"]; keep_log = G["log_event"]
    calls = []

    def fake_old(text, lang, path):
        calls.append((text, lang))
        import wave
        with wave.open(path, "wb") as w_:
            w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(16000); w_.writeframes(b"\x00\x01" * 1600)
        return True, ""
    try:
        G["DATA_DIR"] = tmp; G["_tts_make_639zzb"] = fake_old; G["log_event"] = lambda *a, **k: None
        CFG.update(tts_engine="auto", tts_voice_de="de_DE-thorsten-medium", lang="de")
        assert not piper_installed("de_DE-thorsten-medium") and not piper_ready("de")
        out = os.path.join(tmp, "a.wav")
        ok, err = tts_make("Achtung, Sie werden gefilmt.", "de", out)
        assert ok and calls and TTS["engine"] == "old" and os.path.isfile(piper_cache_path(TTS["id"])), (ok, err, TTS)
        CFG["tts_engine"] = "piper"
        ok, err = tts_make("Hallo", "de", out)
        assert not ok and "Piper" in err, "only Piper without a voice must fail"
        CFG["tts_engine"] = "old"
        assert piper_voice_for("de") == "" and tts_make("Hallo", "de", out)[0]
        n0 = ALERTS["seq"]
        assert speech_alert(TTS["id"], "Hallo") and ALERTS["seq"] == n0 + 1 and ALERTS["items"][-1]["kind"] == "speech"
        assert not speech_alert("../x")
        ok, err = piper_download("it_IT-paola-medium") if not piper_pinned("it_IT-paola-medium") else (False, "This voice is not pinned yet (comes with an update)")
        assert not ok and "not pinned" in err
        js = WEB_PAGE if isinstance(globals().get("WEB_PAGE"), str) else ""
        assert not js or ("piperBox" in js and "piperBox()" in js), "the card «Piper voice» is missing on the main page"
        assert not ALERT_JS.strip() or "mwSpeak" in ALERT_JS, "ALERT_JS: the speech player is missing"
        assert HELP_PAGE.count('<section id="piper"') in (0, 2)
    finally:
        G["DATA_DIR"] = keep_dir; G["_tts_make_639zzb"] = keep_make; G["log_event"] = keep_log
        CFG.update(keep)
        shutil.rmtree(tmp, ignore_errors=True)
    n_ok = sum(1 for vid in PIPER_VOICES if piper_pinned(vid))
    return f"{len(PIPER_VOICES)} voices ({n_ok} pinned), engine {PIPER_ORT}, old voice: {_tts_engine_639zzb() or 'none'}"


SELFTEST_EXTRA.append(("Piper voice: pinned voices, fallback to the old voice, cache, browser announcement (639zzb)", piper_selftest))
