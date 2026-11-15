#@ MoveEye – Teil 639zzzzk_blinki_z_sprache: «Blinki fragen» Stufe 3 – Sprechen: Handy 🎙 gedrückt halten (Aufnahme im Browser → /api/ki/stt), am Gerät nur nach einem Auslöser (2× klatschen, Knopf am Gerät, QR-Karte) einen Satz zuhören, Antwort über den Lautsprecher. Spracherkennung offline mit whisper.cpp (feste Prüfsumme), Cloud möglich. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026, Stufe 3; «Steuern mit Worten» gehört NICHT dazu):
#  Handy     🎙 auf /blinki gedrückt halten: MediaRecorder (webm/opus oder mp4/aac) -> POST /api/ki/stt (höchstens 2 MB, 20 s) ->
#            ffmpeg -> 16 kHz mono WAV -> Text -> die Frage geht wie getippt. iPhone: das Mikrofon geht nur über https:// - ohne
#            sichere Verbindung zeigt die Seite den Hinweis mit der https-Adresse.
#  Gerät     zuhören NUR nach einem Auslöser, nie dauernd:
#              «2× klatschen» (blinki_clap, ab Werk AUS, auch bei bestehenden Geräten; nur Administrator): nur wenn 2× klatschen
#                sonst nichts tut - der Klatschschalter (clap_2 gewählt), das Schlummern des Weckers und alles andere bleibt genau
#                wie vorher (Haken in Teil 250, clap_action: zuerst das Alte);
#              «Knopf am Gerät» (blinki_btn, ab Werk AUS, nur Administrator): Taste «Alarm quittieren» lange drücken, wenn nichts zu
#                quittieren ist - die Taste quittiert zuerst wie immer (Haken in Teil 163a), die Taste
#                «Schutz» bleibt unberührt;
#              QR-Karte «💬 Blinki zuhören» (Teil 639zzp, Befehl B).
#            Dann ein kurzer Ton, ein Satz (Stille-Erkennung, höchstens BLINKI_LISTEN_MAX_S), Text, Antwort über den Lautsprecher.
#  Nie       während Alarm, Sirene, Morse- / Funk-Empfang, Radio oder Wecker (blinki_listen_block); Aufnahmen werden nie
#            gespeichert: der Ton liegt nur im Speicher bzw. als Datei in /dev/shm (sonst DATA_DIR/blinki/tmp) und wird nach dem
#            Erkennen sofort gelöscht.
#  Erkennung whisper.cpp (MIT, fester Tag + Commit wie llama.cpp) mit ggml-tiny (mehrsprachig, Deutsch mit «-l de»; MIT, feste
#            Revision / Grösse / SHA-256 aus dem LFS-Zeiger, 15.11.2026). Vosk small-de als Rückfall: Prüfsumme hier NICHT
#            nachprüfbar (alphacephei.com von hier aus gesperrt) -> Eintrag ohne Grösse = wird nie geladen («kommt mit einem Update»);
#            ein von Hand abgelegtes Vosk-Modell (DATA_DIR/blinki/vosk-model-small-de-0.15) mit pip «vosk» wird benutzt.
#            Cloud (Schalter aus Stufe 2, nur «OpenAI-kompatibel»): POST <Adresse>/audio/transcriptions mit dem Modell
#            blinki_cloud_stt (leer = nur offline).
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Besitzer / Koordinator 15.11.2026: Hauptdatei klein): werkzeuge/bauen.py
# legt es in die Zusatz-ZIP, beim Start läuft es hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es
# «Blinki fragen» nicht - es gehört nicht zu Start, Schutz oder Alarm. Die ZIP ist über ZD_SHA256 (Teil 012) mit signiert.
USER_SETTINGS_DENY.update(("blinki_clap", "blinki_btn", "blinki_cloud_stt")); APPKEY_DENY_KEYS.update(("blinki_clap", "blinki_btn", "blinki_cloud_stt"))


def blinki_clap_listens():                                     # 250 asks this; the literal below answers it (without the zip: never)
    return False
BLINKI_SPRACHE_PY = r'''BLINKI_STT_MODELS = {
    "whisper-tiny": {"name": "Whisper tiny (ggml)", "repo": "ggerganov/whisper.cpp", "rev": "98aa99a0a9db05ae2342309f5096248665f7cba3", "file": "ggml-tiny.bin",
                     "size": 77691713, "sha256": "be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21", "licence": "MIT (OpenAI Whisper, ggml: whisper.cpp)"},
    "vosk-small-de": {"name": "Vosk small-de 0.15", "url": "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip", "size": 0, "sha256": "",
                      "licence": "Apache-2.0"},
}
BLINKI_WHISPER = {"repo": "https://github.com/ggml-org/whisper.cpp", "tag": "v1.9.5", "commit": "d1be6fde11ac6e0407606b4e42fe72d34add8037"}
BLINKI_WHISPER_CMAKE = ("-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DGGML_NATIVE=ON", "-DWHISPER_BUILD_TESTS=OFF", "-DWHISPER_BUILD_SERVER=OFF",
                        "-DWHISPER_BUILD_EXAMPLES=ON", "-DWHISPER_SDL2=OFF", "-DWHISPER_CURL=OFF")
BLINKI_STT = {"install": "", "step": "", "pct": 0}
BLINKI_STT_DL = {"model": "", "running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": ""}
BLINKI_BUILDS["stt"] = (BLINKI_STT, BLINKI_WHISPER, BLINKI_WHISPER_CMAKE, "whisper-cli", "whisper.cpp")
BLINKI_LISTEN_MAX_S, BLINKI_LISTEN_WAIT_S, BLINKI_LISTEN_END_S = 10.0, 5.0, 1.0
BLINKI_STT_MAX_BYTES, BLINKI_STT_MAX_S = 2 * 1024 * 1024, 20
BLINKI_SPEECH_DEF = {"blinki_clap": False, "blinki_btn": False, "blinki_cloud_stt": ""}
for _k, _v in BLINKI_SPEECH_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)
    if "FACTORY_CFG" in globals():
        FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update(BLINKI_SPEECH_DEF)
APPKEY_DENY_KEYS.update(BLINKI_SPEECH_DEF)
BLINKI_SET.update({"blinki_clap": "bool", "blinki_btn": "bool", "blinki_cloud_stt": _bk_cfg_model})
LISTEN = {"on": False, "why": "", "phase": "", "t0": 0.0, "buf": [], "bg": None, "speech_t": 0.0, "last_loud": 0.0, "msg": "", "jid": "", "lock": threading.Lock()}


def blinki_stt_path():
    return os.path.join(blinki_dir(), BLINKI_STT_MODELS["whisper-tiny"]["file"])


def blinki_stt_engine():
    """('whisper', exe) | ('vosk', model dir) | ('', '')"""
    own = os.path.join(blinki_dir(), "bin", "whisper-cli")
    exe = own if os.access(own, os.X_OK) else (shutil.which("whisper-cli") or "")
    if exe and blinki_stt_model_ok():
        return "whisper", exe
    vd = os.path.join(blinki_dir(), "vosk-model-small-de-0.15")
    if os.path.isdir(vd):
        try:
            import importlib.util
            if importlib.util.find_spec("vosk"):
                return "vosk", vd
        except (ImportError, ValueError):
            pass
    return "", ""


def blinki_stt_model_ok():
    m = BLINKI_STT_MODELS["whisper-tiny"]
    p = blinki_stt_path()
    try:
        return os.path.getsize(p) == m["size"] and open(p + ".ok", encoding="utf-8").read().strip() == m["sha256"]
    except OSError:
        return False


def blinki_stt_download(wait=False):
    m = BLINKI_STT_MODELS["whisper-tiny"]
    if blinki_stt_model_ok():
        return True, ""
    if BLINKI_STT_DL["running"]:
        return False, "already running"
    os.makedirs(blinki_dir(), exist_ok=True)
    if shutil.disk_usage(blinki_dir()).free < m["size"] + 300 * 1024 * 1024:
        return False, "not enough free space on the memory card"
    BLINKI_STT_DL.update(model="whisper-tiny", running=True, got=0, total=m["size"], msg="", stop=False, done="")

    def work():
        try:
            url = BLINKI_HF["url"] + m["repo"] + "/resolve/" + m["rev"] + "/" + m["file"] + "?download=true"
            piper_fetch(url, blinki_stt_path(), {"size": m["size"], "sha256": m["sha256"]}, BLINKI_STT_DL)
            with open(blinki_stt_path() + ".ok", "w", encoding="utf-8") as f:
                f.write(m["sha256"])
            BLINKI_STT_DL["done"] = "whisper-tiny"
            log_event("sys", "Blinki: speech recognition model loaded and checked")
        except InterruptedError:
            BLINKI_STT_DL["msg"] = "cancelled"
        except Exception as e:
            BLINKI_STT_DL["msg"] = str(e)[:160]
        finally:
            BLINKI_STT_DL["running"] = False
    if wait:
        work()
        return not BLINKI_STT_DL["msg"], BLINKI_STT_DL["msg"]
    threading.Thread(target=work, daemon=True, name="blinki-stt-dl").start()
    return True, ""


def _bk_tmpdir():
    d = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else os.path.join(blinki_dir(), "tmp")
    os.makedirs(d, exist_ok=True)
    return d


def blinki_stt_pcm(pcm, lang=None):
    """16 kHz mono int16 bytes -> (text, English reason); the sound is never kept"""
    L = norm_lang(lang or CFG.get("lang"))
    wl = {"rm": "de"}.get(L, L)
    if blinki_cloud_ready() and CFG.get("blinki_cloud_stt") and (CFG.get("blinki_cloud_fmt") or "openai") == "openai":
        try:
            return blinki_cloud_stt(pcm, wl), ""
        except Exception as e:
            if not blinki_stt_engine()[0]:
                return "", "the cloud service does not answer: " + blinki_scrub(str(e))[:100]
    kind, where = blinki_stt_engine()
    if not kind:
        return "", "no speech recognition (set it up under Blinki)"
    import tempfile as _tf
    import wave
    fd, path = _tf.mkstemp(prefix="bk-", suffix=".wav", dir=_bk_tmpdir())
    try:
        with os.fdopen(fd, "wb") as f, wave.open(f, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(pcm)
        if kind == "whisper":
            r = subprocess.run(["nice", "-n", "10", where, "-m", blinki_stt_path(), "-f", path, "-l", wl, "-nt", "-np", "-t", "2"],
                               capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
            txt = " ".join(x.strip() for x in (r.stdout or "").splitlines() if x.strip() and not x.strip().startswith("["))
            if r.returncode != 0:
                return "", "speech recognition failed"
        else:
            import vosk
            rec = vosk.KaldiRecognizer(vosk.Model(where), 16000)
            rec.AcceptWaveform(pcm)
            txt = json.loads(rec.FinalResult()).get("text", "")
        txt = re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", txt)).strip()
        return txt[:500], ("" if txt else "nothing understood")
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return "", str(e)[:120]
    finally:
        try:
            os.remove(path)                                    # never stored
        except OSError:
            pass


def blinki_cloud_stt(pcm, lang):
    """OpenAI-compatible /audio/transcriptions (multipart) - only with the cloud switch and a model name for it"""
    from urllib.parse import urlsplit
    import io
    import wave
    u = urlsplit(str(CFG.get("blinki_cloud_url") or ""))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(pcm)
    bd = "----bk" + os.urandom(8).hex()
    parts = []
    for k, v in (("model", str(CFG.get("blinki_cloud_stt"))), ("language", lang)):
        parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode() + buf.getvalue() + b"\r\n")
    parts.append(f"--{bd}--\r\n".encode())
    tls = u.scheme == "https"
    c = (_bhttp.HTTPSConnection if tls else _bhttp.HTTPConnection)(u.hostname, u.port or (443 if tls else 80), timeout=30)
    try:
        c.request("POST", (u.path or "").rstrip("/") + "/audio/transcriptions", b"".join(parts),
                  {"Authorization": "Bearer " + str(CFG.get("blinki_cloud_key") or ""), "Content-Type": "multipart/form-data; boundary=" + bd})
        r = c.getresponse(); data = r.read(200000)
        if r.status != 200:
            raise RuntimeError("the cloud service answered %d" % r.status)
        return str(json.loads(data).get("text") or "").strip()[:500]
    finally:
        c.close()


def blinki_stt_upload(data, lang=None):
    """a recording of the browser (webm / ogg / mp4 / wav) -> (text, English reason); ffmpeg makes 16 kHz mono, nothing is kept"""
    if not data or len(data) > BLINKI_STT_MAX_BYTES:
        return "", "the recording is too long"
    if not shutil.which("ffmpeg"):
        return "", "ffmpeg is missing (sudo apt install ffmpeg)"
    try:
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-nostdin", "-i", "pipe:0", "-t", str(BLINKI_STT_MAX_S), "-ac", "1", "-ar", "16000", "-f", "s16le", "pipe:1"],
                           input=data, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "", "the recording could not be read"
    if r.returncode != 0 or len(r.stdout) < 3200:
        return "", "the recording could not be read"
    return blinki_stt_pcm(r.stdout, lang)


# ---- at the device: listen to ONE sentence after a trigger --------------------------------------------------------------------
def blinki_listen_block():
    """why MoveEye must not listen now ('' = it may)"""
    try:
        if (globals().get("LED") or {}).get("alarm"):
            return "alarm"
        if SOUND.get("playing") and SOUND.get("kind") not in ("beep1", "beep2", "tts"):
            return "siren"
        if WAKE.get("state") == "ring":
            return "wake"
        if MORSE.get("until") and morse_on() and (CFG.get("morse_rx_sound") or funk_on()):
            return "morse"
        if (globals().get("RADIO") or {}).get("want"):
            return "radio"
        if AUDIO is None or not CFG.get("audio_in"):
            return "mic"
    except Exception:
        pass
    return ""


def blinki_listen(why="button"):
    """a trigger: a beep, then one sentence -> question -> the answer on the loudspeaker; (ok, English reason)"""
    b = blinki_listen_block()
    if b:
        log_event("sys", f"Blinki: not listening ({why}): {b}")
        return False, "not now: " + b
    if not (blinki_stt_engine()[0] or (blinki_cloud_ready() and CFG.get("blinki_cloud_stt"))):
        return False, "no speech recognition (set it up under Blinki)"
    with LISTEN["lock"]:
        if LISTEN["on"]:
            return False, "already running"
        LISTEN.update(on=True, why=why, phase="beep", t0=time.time(), buf=[], speech_t=0.0, last_loud=0.0, msg="", jid="")
    log_event("sys", f"Blinki listens ({why})")
    try:
        sound_play("beep2", 0.5, CFG.get("clap_volume", 60), reason="test")
        led_flash("blue", 10.0, 2.0)
    except Exception:
        pass
    threading.Thread(target=_blinki_listen_run, daemon=True, name="blinki-listen").start()
    return True, ""


def blinki_mic_feed(a, now):
    """every 0.1 s piece of the microphone (int16 numpy, 16 kHz) while Blinki listens"""
    if not LISTEN["on"] or LISTEN["phase"] not in ("beep", "listen"):
        return
    if LISTEN["phase"] == "beep":
        if SOUND.get("playing") or now - LISTEN["t0"] < 0.6:
            return                                             # not the own beep
        LISTEN["phase"] = "listen"; LISTEN["t0"] = now
    x = a.astype(np.float32) / 32768.0
    db = 10.0 * np.log10(float(np.mean(x * x)) + 1e-10)
    if LISTEN["bg"] is None:
        LISTEN["bg"] = db
    if db > max(LISTEN["bg"] + 10.0, -50.0):
        LISTEN["last_loud"] = now
        LISTEN["speech_t"] = LISTEN["speech_t"] or now
    elif not LISTEN["speech_t"]:
        LISTEN["bg"] += (db - LISTEN["bg"]) * 0.1
    LISTEN["buf"].append(a.astype("<i2").tobytes())


def _blinki_listen_run():
    L = norm_lang(CFG.get("lang"))
    try:
        while True:
            time.sleep(0.1)
            now = time.time()
            b = blinki_listen_block()
            if b:
                LISTEN["msg"] = "stopped: " + b; return
            if LISTEN["phase"] == "beep" and now - LISTEN["t0"] > 5:
                LISTEN["msg"] = "no microphone sound"; return
            if LISTEN["phase"] != "listen":
                continue
            el = now - LISTEN["t0"]
            if not LISTEN["speech_t"] and el > BLINKI_LISTEN_WAIT_S:
                LISTEN["msg"] = "nothing heard"; return
            if LISTEN["speech_t"] and (now - LISTEN["last_loud"] > BLINKI_LISTEN_END_S or el > BLINKI_LISTEN_MAX_S):
                break
        LISTEN["phase"] = "stt"
        pcm = b"".join(LISTEN["buf"]); LISTEN["buf"] = []
        txt, err = blinki_stt_pcm(pcm, L)
        pcm = b""
        if not txt:
            LISTEN["msg"] = err or "nothing understood"
            try:
                tts_say(tr("Sorry, I did not understand that.", L), L)
            except Exception:
                pass
            return
        LISTEN["phase"] = "think"
        j, err = blinki_ask("frag", txt, L, None, "device (" + LISTEN["why"] + ")", "device")
        if j is None:
            LISTEN["msg"] = err; return
        LISTEN["jid"] = j["id"]
        t0 = time.time()
        while j["state"] in ("wait", "think", "write") and time.time() - t0 < 400:
            time.sleep(0.3)
        if j["text"]:
            blinki_say(j["id"], "pi", 0, L)
    finally:
        LISTEN["buf"] = []
        LISTEN.update(on=False, phase="")


_SoundEvents_feed_blinki = SoundEvents.feed


def _blinki_soundevents_feed(self, a, now):                    # + 639zzzzk_blinki_z_sprache: Blinki gets the microphone only while it listens
    try:
        blinki_mic_feed(a, now)
    except Exception:
        pass
    return _SoundEvents_feed_blinki(self, a, now)


# wraps: SoundEvents.feed (250)
SoundEvents.feed = _blinki_soundevents_feed


def blinki_clap_listens():
    """250 listens for claps also for Blinki (only with the switch of the administrator)"""
    return bool(CFG.get("blinki_clap")) and not LISTEN["on"]


# 2× clapping (hook in Teil 250, clap_action) and «acknowledge» long (hook in Teil 163a, led_button_event) call blinki_listen
# only after the old code had its turn; the QR card «B» runs from qrk_exec (hook in Teil 639zzp). The hooks stay in the main
# file - nothing of protection or alarm runs from the zip.


# ---- QR card «💬 Blinki zuhören» (639zzp, command B) ---------------------------------------------------------------------------
QRK_CMDS["B"] = ("blinki", "💬", "Blinki listens")
if "B" not in QRK_CMD_ORDER:
    QRK_CMD_ORDER = QRK_CMD_ORDER + "B"
_qrk_make_param_blinki = qrk_make_param
_qrk_what_blinki = qrk_what


# wraps: qrk_make_param
def qrk_make_param(cmd, d):                                    # + 639zzzzk_blinki_z_sprache
    return ("", "") if cmd == "B" else _qrk_make_param_blinki(cmd, d)


# wraps: qrk_what
def qrk_what(card, lang=None, icon=True):                      # + 639zzzzk_blinki_z_sprache
    if card.get("cmd") == "B":
        return ("💬 " if icon else "") + tr("Blinki listens", norm_lang(lang))
    return _qrk_what_blinki(card, lang, icon)


_blinki_state_speech = blinki_state


# wraps: blinki_state
def blinki_state():                                             # + 639zzzzk_blinki_z_sprache: speech recognition, triggers, listening
    st = _blinki_state_speech()
    kind, _w = blinki_stt_engine()
    m = BLINKI_STT_MODELS["whisper-tiny"]
    st["speech"] = {"engine": kind, "model_ok": blinki_stt_model_ok(), "mb": m["size"] // 1048576, "licence": m["licence"],
                    "exe": bool(os.access(os.path.join(blinki_dir(), "bin", "whisper-cli"), os.X_OK) or shutil.which("whisper-cli")),
                    "install": BLINKI_STT["install"], "step": BLINKI_STT["step"], "pct": BLINKI_STT["pct"],
                    "dl": {k: BLINKI_STT_DL[k] for k in ("running", "got", "total", "msg")}, "clap": bool(CFG.get("blinki_clap")),
                    "btn": bool(CFG.get("blinki_btn")), "cloud_stt": CFG.get("blinki_cloud_stt") or "", "qr": bool(CFG.get("qrk_on")),
                    "listen": {"on": LISTEN["on"], "why": LISTEN["why"], "phase": LISTEN["phase"], "msg": LISTEN["msg"]},
                    "ok": bool(kind) or bool(blinki_cloud_ready() and CFG.get("blinki_cloud_stt"))}
    st["https_port"] = STATE.get("https_port")
    return st


_smalltv_routes_speech = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                          # + 639zzzzk_blinki_z_sprache: /api/ki/stt, /api/ki/listen, speech setup
    _smalltv_routes_speech(app, reply, body)
    from flask import request

    @app.route("/api/ki/stt", methods=["POST"])
    def blinki_api_stt():
        L = norm_lang(request.args.get("lang"))
        if request.content_length and request.content_length > BLINKI_STT_MAX_BYTES:
            return reply({"ok": False, "error": tr_err("the recording is too long", L)}, 413)
        data = request.get_data(cache=False)[:BLINKI_STT_MAX_BYTES + 1]
        txt, err = blinki_stt_upload(data, L)
        data = b""
        return reply({"ok": bool(txt), "text": txt, "error": None if txt else tr_err(err, L)}, 200 if txt else 400)

    @app.route("/api/ki/speech", methods=["POST"])
    def blinki_api_speech():
        d = body(); L = norm_lang(d.get("lang")); a = str(d.get("action") or "")
        if a == "load":
            ok_, err = blinki_stt_download()
        elif a == "cancel":
            BLINKI_STT_DL["stop"] = True; ok_, err = True, ""
        elif a == "engine":
            ok_, err = blinki_install("stt")
        elif a == "listen":
            ok_, err = blinki_listen("web test")
        else:
            ok_, err = False, "unknown action"
        return reply({"ok": ok_, "error": None if ok_ else tr_err(err, L), "state": blinki_page_state(L)}, 200 if ok_ else 400)


APPKEY_DENY_PATHS.add("/api/ki/speech")
LOCK_DENY_PATHS.add("/api/ki/speech")
'''
zd_exec(BLINKI_SPRACHE_PY, '639zzzzk_blinki_z_sprache.py')
