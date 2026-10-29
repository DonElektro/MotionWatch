#@ Motion Watch – Teil 250: Klatschschalter, Bluetooth, Lautsprecher, Sprachausgabe. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Clap switch and «Bless you!»: listens to the microphone (the same stream as the noise alarm).
#   Clap switch: 2 / 3 / 4 claps in a row (¼ to ¾ s apart) -> an action (relay, light, photo, recording, arm / disarm).
#     A clap = the level jumps up within 20 ms and is down again after 150 ms (speech, music, doors last longer).
#   Bless you: after a loud sound, a small sound recognition model (YAMNet, Google, about 4 MB, ~500 kinds of sounds)
#     checks whether it was a sneeze; then the loudspeaker says «Gesundheit!» (or plays an own recording).
# ----------------------------------------------------------------------------
SOUNDEV = {"claps": [], "last_clap": 0.0, "seq_n": 0, "last_n": 0, "last_n_t": 0.0, "last_act": "", "last_act_t": 0.0,
           "sneeze_t": 0.0, "sneeze_score": None, "sneeze_last": 0.0, "model": "off", "model_msg": "", "install": "", "checks": 0}
YAMNET_URLS = ("https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/android/"
               "lite-model_yamnet_classification_tflite_1.tflite",
               "https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1?lite-format=tflite")
YAMNET_SNEEZE = 44                       # index of «Sneeze» in the 521 YAMNet classes (when the label list is missing)
_SNEEZE_DAYS = {"loaded": False, "days": {}}


def clap_act_pairs():
    out = [("none", tr("nothing"))]
    for i, r in enumerate(RELAYS):
        out.append((f"relay:{i}", trf("{name} on / off", name=r.get("name") or f"Relay {i + 1}")))
    out += [("light_white", tr("White light on / off")), ("light_ir", tr("Infrared light on / off")), ("photo", tr("Take a photo")),
            ("rec", tr("Record (10 min) / stop")), ("arm", tr("Arm / disarm (with a beep)"))]
    return out


def sneeze_reply_pairs():
    return [("tts", tr("Speak the words below"))] + [("file:" + f, "🎵 " + f) for f in own_sounds()]


def sev_beep(n=1, ok=True):
    """Short beep(s) as an answer: n beeps rising (done) or one low beep (only counted / not allowed)."""
    if not CFG.get("clap_beep") or not out_selected():
        return
    sound_play("beep%d" % max(1, min(4, n)) if ok else "beeplow", 0.18 * max(1, n) + 0.1, CFG.get("clap_volume", 60), reason="test")


def clap_action(n):
    """n claps in a row: what was chosen for it."""
    act = str(CFG.get(f"clap_{n}") or "none")
    SOUNDEV.update(last_n=n, last_n_t=time.time())
    if act == "none":
        SOUNDEV["last_act"] = ""; return
    label = dict(clap_act_pairs()).get(act, act)
    if CFG.get("clap_practice"):
        SOUNDEV.update(last_act=tr("practice") + ": " + label, last_act_t=time.time()); sev_beep(n); return
    if CFG.get("clap_disarmed") and CFG["armed"] and act != "arm":
        SOUNDEV.update(last_act=tr("not while armed"), last_act_t=time.time()); sev_beep(1, ok=False); return
    w = WATCH_REF.get("w")
    done = ""
    try:
        if act.startswith("relay:"):
            i = int(act[6:])
            if 0 <= i < len(RELAYS):
                new = "off" if RELAYS[i].get("mode") == "on" else "on"
                ok, _e = relay_update(i, "mode", new)
                if ok:
                    save_settings(); done = f"{RELAYS[i].get('name') or 'Relay %d' % (i + 1)} → {tr(new)}"
        elif act in ("light_white", "light_ir"):
            nm = act[6:]; new = "off" if CFG["light_" + nm] == "on" else "on"
            ok, _e = light_set(nm, new)
            if ok:
                done = f"{tr('White light') if nm == 'white' else tr('Infrared light')} → {tr(new)}"
        elif act == "photo":
            nm = quick_photo(getattr(w, "frame_out", None)) if w is not None else None
            done = tr("Photo") + f" {nm}" if nm else ""
        elif act == "rec":
            done = tr("Recording") + " → " + tr("on" if quick_rec() else "off")
        elif act == "arm":
            if is_armed() or CFG["armed"]:
                if CFG.get("protect_pin"):                  # 2.97.0: with a PIN, clapping only arms (anyone can clap)
                    done = ""; log_event("sys", "Clap switch: disarming needs the PIN")
                else:
                    disarm(); done = tr("disarmed")
            else:
                arm(); done = tr("armed (countdown)")
    except Exception as e:
        done = ""; log_event("sys", f"Clap switch: {e}"[:160])
    SOUNDEV.update(last_act=done or tr("not possible"), last_act_t=time.time())
    if done:
        log_event("sys", f"Clap switch ({n}×): {done}")
        sev_beep(n)
    else:
        sev_beep(1, ok=False)


class SoundEvents:
    """Fed with every 0.1 s piece of the microphone (16 kHz, 16 bit). Looks at 10 ms steps."""
    FR = AUDIO_RATE // 100                                  # 10 ms

    def __init__(self):
        self.hist = deque(maxlen=60)                         # (t, dB) of the last 0.6 s in 10 ms steps
        self.bg = None
        self.pending = []                                    # onsets waiting for the check «short?» (t, peak dB)
        self.pcm = deque(maxlen=30)                          # the last 3 s as float pieces (for the sneeze model)
        self.q = queue.Queue(maxsize=2)
        self.loud_t = 0.0
        threading.Thread(target=self._model_loop, daemon=True, name="sneeze").start()

    def feed(self, a, now):
        if not (CFG.get("clap_on") or CFG.get("sneeze_on")):
            self.pending.clear(); SOUNDEV["claps"] = []; return
        muted = (AUDIO is not None and now < AUDIO.mute_until) or SOUND["playing"] or now - SERVO_MOVE["t"] < 1.0
        x = a / 32768.0
        self.pcm.append((now, x.astype(np.float32)))
        n = x.size // self.FR
        if n <= 0:
            return
        fr = x[:n * self.FR].reshape(n, self.FR)
        dbs = 10.0 * np.log10(np.mean(fr * fr, axis=1) + 1e-10)
        t0 = now - n * 0.01
        for i, db in enumerate(dbs):
            t = t0 + (i + 1) * 0.01
            self._step(t, float(db), muted)

    def _step(self, t, db, muted):
        prev = [d for (tt, d) in self.hist if t - tt <= 0.04]
        before = min(prev) if prev else db
        self.hist.append((t, db))
        if self.bg is None:
            self.bg = db
        quiet = db < self.bg + 6
        self.bg += (db - self.bg) * (0.02 if quiet else 0.002)          # background follows slowly (not the claps)
        sens = float(CFG.get("clap_sens", 5))
        rise = 26.0 - 1.6 * sens                                          # sensitivity 1 = +24 dB ... 10 = +10 dB
        loud = db > max(self.bg + rise, -42.0)
        if CFG.get("sneeze_on") and db > max(self.bg + 14.0, -45.0) and t - self.loud_t > 0.7 and not muted:
            self.loud_t = t                                              # something loud: look at it with the model in 0.6 s
            threading.Timer(0.6, self._ask_model, args=(t,)).start()
        if CFG.get("clap_on") and not muted and loud and before < db - 12.0 and not any(abs(t - p[0]) < 0.12 for p in self.pending):
            self.pending.append((t, db))
        for p in list(self.pending):
            if t - p[0] >= 0.16:                                          # 160 ms later: was it short (a clap)?
                self.pending.remove(p)
                after = [d for (tt, d) in self.hist if 0.11 <= tt - p[0] <= 0.16]
                if after and max(after) < p[1] - 10.0:
                    self._clap(p[0])
        c = SOUNDEV["claps"]
        if c and t - c[-1] > 1.0:                                         # the row is over
            n = len(c); SOUNDEV["claps"] = []
            if 2 <= n <= 4:
                clap_action(n)
            elif n > 4:
                SOUNDEV.update(last_n=n, last_n_t=time.time(), last_act=tr("too many claps"))

    def _clap(self, t):
        c = SOUNDEV["claps"]
        if c and t - c[-1] < 0.15:
            return
        if c and t - c[-1] > 0.9:
            c.clear()
        c.append(t); SOUNDEV["last_clap"] = time.time(); SOUNDEV["seq_n"] = len(c)

    # ---- sneeze ----
    def _ask_model(self, t):
        if not CFG.get("sneeze_on"):
            return
        pieces = [x for (tt, x) in list(self.pcm) if t - 0.45 <= tt <= t + 0.6]
        if not pieces:
            return
        w = np.concatenate(pieces)[-15600:]
        if w.size < 15600:
            w = np.concatenate([np.zeros(15600 - w.size, np.float32), w])
        try:
            self.q.put_nowait((t, w))
        except queue.Full:
            pass

    def _model_loop(self):
        it = None
        while True:
            t, w = self.q.get()
            if it is None:
                it = yamnet_interpreter()
                if it is None:
                    continue
            try:
                sc = yamnet_scores(it, w)
            except Exception as e:
                SOUNDEV.update(model="error", model_msg=str(e)[:120]); it = None; continue
            SOUNDEV["checks"] += 1
            idx = YAMNET_INFO.get("sneeze", YAMNET_SNEEZE)
            s = float(sc[idx]) if idx < sc.size else 0.0
            top3 = np.argsort(sc)[-3:]
            SOUNDEV.update(sneeze_score=round(s, 2), sneeze_t=time.time())
            thr = 0.55 - 0.04 * (float(CFG.get("sneeze_sens", 5)) - 5)
            if s >= thr and idx in top3:
                sneeze_reply()


YAMNET_INFO = {}


def yamnet_runtime():
    for mod in ("ai_edge_litert.interpreter", "tflite_runtime.interpreter"):
        try:
            import importlib
            return importlib.import_module(mod).Interpreter
        except Exception:
            continue
    try:
        import tensorflow as tf
        return tf.lite.Interpreter
    except Exception:
        return None


def yamnet_path():
    return os.path.join(DATA_DIR, "models", "yamnet.tflite")


def yamnet_fetch():
    """Fetch the sound recognition model once (about 4 MB, from Google)."""
    p = yamnet_path()
    if os.path.isfile(p) and os.path.getsize(p) > 1000000:
        return True
    os.makedirs(os.path.dirname(p), exist_ok=True)
    SOUNDEV.update(model="downloading", model_msg="")
    for u in YAMNET_URLS:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "MotionWatch/" + APP_VERSION})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read(20 * 1024 * 1024)
            if len(data) < 1000000 or data[4:8] != b"TFL3":
                raise ValueError("not a model file")
            with open(p + ".part", "wb") as f:
                f.write(data)
            os.replace(p + ".part", p)
            log_event("sys", f"Sound recognition model loaded ({len(data) // 1024} kB)")
            return True
        except Exception as e:
            SOUNDEV["model_msg"] = str(e)[:120]
    SOUNDEV["model"] = "download failed"; SOUNDEV["fail_t"] = time.time()
    return False


def yamnet_interpreter():
    if time.time() - SOUNDEV.get("fail_t", 0.0) < 600:
        return None                                           # it did not work a moment ago: try again in 10 minutes
    Interp = yamnet_runtime()
    if Interp is None:
        SOUNDEV.update(model="no runtime", model_msg="pip install ai-edge-litert"); return None
    if not yamnet_fetch():
        return None
    try:
        it = Interp(model_path=yamnet_path())
        it.allocate_tensors()
        inp = it.get_input_details()[0]
        YAMNET_INFO["in"] = inp; YAMNET_INFO["out"] = it.get_output_details()[0]
        try:                                                  # the class names travel inside the model file (zip part)
            with zipfile.ZipFile(yamnet_path()) as z:
                names = [n for n in z.namelist() if n.endswith(".txt")]
                labels = z.read(names[0]).decode("utf-8", "replace").splitlines() if names else []
            if "Sneeze" in labels:
                YAMNET_INFO["sneeze"] = labels.index("Sneeze")
        except (zipfile.BadZipFile, OSError, IndexError):
            pass
        SOUNDEV.update(model="ready", model_msg="")
        return it
    except Exception as e:
        SOUNDEV.update(model="error", model_msg=str(e)[:120], fail_t=time.time()); return None


def yamnet_scores(it, w):
    inp, out = YAMNET_INFO["in"], YAMNET_INFO["out"]
    x = w.astype(np.float32)
    if len(inp["shape"]) == 2:
        x = x.reshape(1, -1)
    if tuple(inp["shape"]) != tuple(x.shape):
        it.resize_tensor_input(inp["index"], list(x.shape)); it.allocate_tensors()
    it.set_tensor(inp["index"], x)
    it.invoke()
    sc = np.asarray(it.get_tensor(out["index"]), dtype=np.float32)
    return sc.reshape(-1, sc.shape[-1]).mean(axis=0) if sc.ndim > 1 else sc


def sneeze_count(add=False):
    d = datetime.now().strftime("%Y-%m-%d"); p = os.path.join(DATA_DIR, "sneezes.json")
    if not _SNEEZE_DAYS["loaded"]:
        _SNEEZE_DAYS["loaded"] = True
        try:
            with open(p) as f:
                _SNEEZE_DAYS["days"] = {k: int(v) for k, v in json.load(f).items()}
        except (OSError, ValueError, AttributeError):
            pass
    if add:
        D = _SNEEZE_DAYS["days"]; D[d] = D.get(d, 0) + 1
        for k in sorted(D)[:-120]:
            D.pop(k, None)
        try:
            with open(p, "w") as f:
                json.dump(D, f)
        except OSError:
            pass
    return _SNEEZE_DAYS["days"].get(d, 0)


def sneeze_reply():
    now = time.time()
    if now - SOUNDEV["sneeze_last"] < 5.0:                     # «hatschi - hatschi»: one answer
        return
    SOUNDEV["sneeze_last"] = now
    n = sneeze_count(add=True)
    h = datetime.now().hour
    quiet = CFG.get("sneeze_night") and (h >= 22 or h < 7)
    log_event("sys", f"Sneeze recognised (today {n}×)" + (" - quiet at night" if quiet else ""))
    if quiet or not out_selected() or SOUND["playing"]:
        return
    rep = str(CFG.get("sneeze_reply") or "tts")
    vol = CFG.get("sneeze_volume", 70)
    if rep.startswith("file:") and rep[5:] in own_sounds():
        sec = 3.0
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                os.path.join(sounds_dir(), rep[5:])], capture_output=True, text=True, timeout=10)
            sec = max(0.5, min(10.0, float(r.stdout.strip() or 3)))
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
        sound_play(rep, sec, vol, reason="test"); return
    words = [x.strip() for x in str(CFG.get("sneeze_texts") or "").split("|") if x.strip()] or [tr("Bless you!")]
    text = tr("Again? Get well soon!") if n >= 3 and n % 3 == 0 else words[(n - 1) % len(words)]
    ok, err = tts_make(text, CFG["lang"], TTS["file"])
    if not ok:                                                # no speech program: a small friendly melody
        sound_play("beep3", 0.7, vol, reason="test"); SOUNDEV["model_msg"] = err; return
    try:
        import wave
        with wave.open(TTS["file"]) as w_:
            dur = w_.getnframes() / float(w_.getframerate() or 1)
    except Exception:
        dur = 2.0
    sound_play("tts", dur + 0.3, vol, reason="test")


def sneeze_upload(data):
    """An own answer (e.g. «Gesundheit!» recorded on a phone): converted to a short .wav in the own sounds and chosen at once."""
    if not data or len(data) > 8 * 1024 * 1024:
        return False, "the file is too large (max. 8 MB)", ""
    if not shutil.which("ffmpeg"):
        return False, "ffmpeg is missing (sudo apt install ffmpeg)", ""
    os.makedirs(sounds_dir(), exist_ok=True)
    i = 1
    while os.path.exists(os.path.join(sounds_dir(), f"Gesundheit {i}.wav")):
        i += 1
    name = f"Gesundheit {i}.wav"
    tmp = os.path.join(tempfile.gettempdir(), "mw_sneeze_upload.bin")
    with open(tmp, "wb") as f:
        f.write(data)
    try:
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-t", "8", "-ac", "1", "-ar", "22050", os.path.join(sounds_dir(), name)],
                           capture_output=True, timeout=60)
        if r.returncode != 0 or not os.path.isfile(os.path.join(sounds_dir(), name)):
            return False, "the file could not be read (a sound file like .m4a, .mp3 or .wav is needed)", ""
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    CFG["sneeze_reply"] = "file:" + name; save_settings()
    log_event("sys", f"Own answer for «Bless you!» saved: {name}")
    return True, "", name


def sneeze_install():
    """Install the runtime for the sound recognition model (pip, a few minutes; in the background)."""
    if SOUNDEV["install"] == "running":
        return False, "already running"
    SOUNDEV["install"] = "running"

    def work():
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "ai-edge-litert"],
                               capture_output=True, text=True, timeout=1200)
            ok = r.returncode == 0
            SOUNDEV["fail_t"] = 0.0
            SOUNDEV["install"] = "done" if ok else "failed: " + ((r.stderr or r.stdout).strip().splitlines() or ["?"])[-1][:140]
            log_event("sys", "Sound recognition: runtime installed" if ok else "Sound recognition: " + SOUNDEV["install"])
            if ok:
                SOUNDEV.update(model="off", model_msg="")
        except Exception as e:
            SOUNDEV["install"] = "failed: " + str(e)[:120]
    threading.Thread(target=work, daemon=True, name="sneeze-install").start()
    return True, ""


def soundev_state():
    now = time.time()
    return {"clap_on": bool(CFG.get("clap_on")), "sneeze_on": bool(CFG.get("sneeze_on")), "counting": len(SOUNDEV["claps"]),
            "last_n": SOUNDEV["last_n"] if now - SOUNDEV["last_n_t"] < 30 else 0, "last_act": SOUNDEV["last_act"] if now - SOUNDEV["last_act_t"] < 30 else "",
            "model": SOUNDEV["model"], "model_msg": SOUNDEV["model_msg"], "install": SOUNDEV["install"], "runtime": yamnet_runtime() is not None,
            "sneeze_score": SOUNDEV["sneeze_score"] if now - SOUNDEV["sneeze_t"] < 20 else None, "sneezes_today": sneeze_count(),
            "mic": bool(CFG["audio_in"]), "spk": out_selected(), "tts": tts_engine() is not None}


def soundev_text(which, lang=None):
    s = soundev_state()
    if not s["mic"]:
        return tr("no microphone selected (Microphone)", lang)
    if which == "clap":
        if not s["clap_on"]:
            return tr("off", lang)
        t = tr("listening", lang) + (" · " + tr("counting", lang) + f": {s['counting']}×" if s["counting"] else "")
        if s["last_n"]:
            t += f" · {tr('last', lang)}: {s['last_n']}× → " + (tr(s["last_act"], lang) if s["last_act"] else "–")
        return t + ("" if s["spk"] else " · " + tr("no loudspeaker for the beep", lang))
    if not s["sneeze_on"]:
        return tr("off", lang) + (f" · {tr('today', lang)}: {s['sneezes_today']}× {tr('sneezed', lang)}" if s["sneezes_today"] else "")
    m = s["model"]
    t = {"ready": tr("listening", lang), "downloading": tr("loading the sound recognition …", lang), "off": tr("waiting for the first loud sound", lang),
         "no runtime": tr("needs the sound recognition program - button «Install»", lang), "download failed": tr("model could not be loaded", lang),
         "error": tr("error", lang)}.get(m, m)
    if s["install"] == "running":
        t = tr("installing … (a few minutes)", lang)
    elif s["install"].startswith("failed"):
        t += " · ⚠ " + s["install"]
    if s["sneeze_score"] is not None:
        t += f" · {tr('last check', lang)}: {round(100 * s['sneeze_score'])} %"
    t += f" · {tr('today', lang)}: {s['sneezes_today']}× {tr('sneezed', lang)}"
    if not s["tts"] and str(CFG.get("sneeze_reply") or "tts") == "tts":
        t += " · " + tr("no speech program (sudo apt install libttspico-utils)", lang)
    return t


SOUNDEV_OBJ = {"o": None}


class AudioMonitor:
    """Reads the microphone (arecord), measures the level, raises the noise alarm, feeds the live listeners and the
    sound file of a running recording."""
    def __init__(self):
        self.proc = None; self.dev = ""; self.err = ""; self.restart_at = 0.0
        self.lk = threading.Lock()
        self.ring = deque()                  # (end time, pcm bytes) of the last seconds: the pre-roll of a recording
        self.listeners = set()               # queues of open "listen" connections
        self.rec = None                      # {"wave", "path", "video", "frames"}
        self.level = None; self.bg = None; self.peak = -90.0; self.peak_t = 0.0
        self.loud_since = 0.0; self.last_loud = 0.0; self.noisy_until = 0.0
        self.noise_alerted = False; self.last_noise = 0.0
        self.sim_t = 0.0                     # the 3D simulator sends the sound of its world (no real microphone)
        self.mute_until = 0.0                # the Pi plays a sound itself: the noise alarm does not listen
        self.mux_threads = []
        self._status("off")
        threading.Thread(target=self.run, daemon=True, name="audio").start()

    # ---- status for the page / window ----
    def _status(self, status):
        lv, bg = self.level, self.bg
        STATE["audio"] = {"status": status, "dev": self.dev if self.proc else "", "level": lv, "bg": None if bg is None else round(bg, 1),
                          "thr": None if bg is None else round(max(bg + CFG["noise_threshold"], -70.0), 1),
                          "peak": self.peak if time.time() - self.peak_t < 3 else lv, "loud": time.time() < self.noisy_until,
                          "listeners": len(self.listeners), "playing": SOUND["playing"], "sound_msg": SOUND["msg"],
                          "rec": self.rec is not None, "mic": bool(CFG["audio_in"]), "spk": out_selected(),
                          "bt": {"avail": bt_available(), "scanning": BT["scanning"], "busy": BT["busy"], "msg": BT["msg"]},
                          "talk": TALK["proc"] is not None, "https_port": STATE.get("https_port")}

    def noisy(self):
        return (self.proc is not None or time.time() - self.sim_t < 1.5) and time.time() < self.noisy_until

    def feed_sim(self, lvl):
        """the sound level (dB) of the simulated world - only when no real microphone runs: noise alarm like with a microphone"""
        if self.proc is not None:
            return
        now = time.time()
        if now - self.sim_t > 5.0:
            self._started = now; self.bg = None          # a new start: learn the background again
        self.sim_t = now
        self.level = float(lvl)
        if self.level >= self.peak or now - self.peak_t > 3:
            self.peak, self.peak_t = self.level, now
        self._noise(now, self.level)
        self._status("simulated")

    # ---- microphone process ----
    def _stop(self):
        p, self.proc = self.proc, None
        if p is not None:
            try:
                p.kill(); p.wait(timeout=3)
            except Exception:
                pass
        self.level = None; self.bg = None

    def run(self):
        try:
            audio_scan()
        except Exception:
            pass
        while True:
            try:
                self._loop_once()
            except Exception as e:                       # never let the audio thread die
                self.err = str(e)[:200]; self._stop(); self.restart_at = time.time() + 5.0
                self._status("error: " + self.err); time.sleep(1.0)

    def _loop_once(self):
        want = CFG["audio_in"]
        if not want or not AUDIO_DEV_RE.match(want):
            if time.time() - self.sim_t < 1.5:           # the simulator supplies the sound
                time.sleep(0.5); return
            if self.proc is not None:
                self._stop(); log_event("sys", "Microphone off")
            self.rec_abort(); self._status("off"); time.sleep(0.5); return
        if self.proc is None or self.dev != want:
            self._stop()
            if time.time() < self.restart_at:
                self._status("error: " + self.err if self.err else "starting"); time.sleep(0.3); return
            if not shutil.which("arecord"):
                self.err = "arecord is missing (sudo apt install alsa-utils)"; self.restart_at = time.time() + 30.0
                return
            self.dev = want
            self.proc = subprocess.Popen(["arecord", "-q", "-D", want, "-f", "S16_LE", "-r", str(AUDIO_RATE), "-c", "1", "-t", "raw"],
                                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._started = time.time(); self.err = ""
        data = self.proc.stdout.read(AUDIO_CHUNK * 2)
        if not data or len(data) < 2:
            p = self.proc
            try:
                p.wait(timeout=2); err = (p.stderr.read() or b"").decode(errors="replace").strip()
            except Exception:
                err = ""
            self.err = (err.splitlines()[-1] if err else f"arecord stopped (exit {p.poll()})")[:200]
            log_event("sys", f"Microphone: {self.err}")
            self._stop(); self.restart_at = time.time() + 10.0; self._status("error: " + self.err)
            return
        self._chunk(data[:len(data) // 2 * 2])

    def _chunk(self, data):
        now = time.time()
        a = np.frombuffer(data, dtype="<i2").astype(np.float32)
        gain = 10.0 ** (float(CFG["audio_gain"]) / 20.0)
        if abs(gain - 1.0) > 1e-3:
            a = np.clip(a * gain, -32768, 32767)
            data = a.astype("<i2").tobytes()
        lvl = _db(float(np.sqrt(np.mean(a * a))) if a.size else 0.0)
        self.level = lvl
        if lvl >= self.peak or now - self.peak_t > 3:
            self.peak, self.peak_t = lvl, now
        with self.lk:
            self.ring.append((now, data))
            keep = max(3.0, float(CFG["pre_roll"]) + 2.0)
            while self.ring and now - self.ring[0][0] > keep:
                self.ring.popleft()
            if self.rec is not None:
                try:
                    self.rec["wave"].writeframes(data)
                except Exception:
                    self.rec = None
            for q in list(self.listeners):
                try:
                    q.put_nowait(data)
                except queue.Full:
                    pass                                 # slow phone: drop instead of waiting
        self._noise(now, lvl)
        if SOUNDEV_OBJ["o"] is not None:
            try:
                SOUNDEV_OBJ["o"].feed(a, now)
            except Exception as e:
                SOUNDEV["model_msg"] = str(e)[:120]
        self._status("listening")

    # ---- noise alarm ----
    def _noise(self, now, lvl):
        if now - getattr(self, "_started", 0) < 1.5:
            return                                       # the first moments of a microphone are often a click
        muted = now < self.mute_until or SOUND["playing"] or now - SERVO_MOVE["t"] < 1.0    # servo motors are loud
        if self.bg is None:
            self.bg = lvl
        thr = max(self.bg + float(CFG["noise_threshold"]), -70.0)       # never below -70 dB: microphone hiss is no noise
        loud = lvl > thr and not muted
        # background level: follows quiet phases fast, loud ones very slowly (a running generator becomes "normal" after ~1 min)
        k = 0.1 if lvl < self.bg else (0.003 if loud else 0.02)
        if not muted:
            self.bg += k * (lvl - self.bg)
        if loud:
            self.last_loud = now
            if not self.loud_since:
                self.loud_since = now
            if now - self.loud_since >= float(CFG["noise_min"]) - 0.05:
                self.noisy_until = now + 2.0
                if CFG["noise_alarm"] and is_armed():
                    self.last_noise = now                # keeps a recording running (like a person in the picture)
                if CFG["noise_alarm"] and not self.noise_alerted:
                    self.noise_alerted = True
                    self._alarm(lvl)
        else:
            self.loud_since = 0.0
            if self.noise_alerted and now - self.last_loud > 5.0:
                self.noise_alerted = False

    def _alarm(self, lvl):
        txt = f"Noise: {lvl:.0f} dB (background {self.bg:.0f} dB)"
        if not is_armed():
            log_event("person", txt + " (disarmed - no alarm)"); return
        w = WATCH_REF["w"]
        push_alert("noise", "noise", db=round(lvl), source=STATE["source_label"])
        sent = w is not None and w.notifier.prealarm(w.frame_out, "noise")
        log_event("person", "Noise alarm: " + txt + (" - push message sent" if sent else ""))
        siren_alarm("noise")

    # ---- live listening ----
    def listen(self):
        q = queue.Queue(maxsize=25)
        with self.lk:
            self.listeners.add(q)
        return q

    def unlisten(self, q):
        with self.lk:
            self.listeners.discard(q)

    # ---- sound of a recording: a WAV file next to the video, joined with it when the recording ends ----
    def rec_start(self, video_path, t0):
        if not (CFG["audio_record"] and self.proc is not None) or self.rec is not None:
            return False
        import wave
        tdir = os.path.join(os.path.dirname(os.path.abspath(video_path)), ".tmp")
        try:
            os.makedirs(tdir, exist_ok=True)
            path = os.path.join(tdir, os.path.basename(video_path) + ".wav")
            wf = wave.open(path, "wb"); wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(AUDIO_RATE)
        except Exception as e:
            log_event("rec", f"Sound recording failed: {e}"[:200]); return False
        with self.lk:
            for t, data in self.ring:                    # the seconds before the detection (pre-roll), like the video
                if t > t0:
                    wf.writeframes(data)
            self.rec = {"wave": wf, "path": path, "video": video_path}
        return True

    def rec_abort(self):
        with self.lk:
            r, self.rec = self.rec, None
        if r:
            try:
                r["wave"].close(); os.remove(r["path"])
            except Exception:
                pass

    def rec_stop(self, video_path, frames, fps):
        with self.lk:
            r = self.rec
            if r is None or r["video"] != video_path:
                return
            self.rec = None
        try:
            r["wave"].close()
        except Exception:
            return
        th = threading.Thread(target=audio_mux, args=(video_path, r["path"], frames, fps), daemon=True)
        th.start()
        self.mux_threads = [t for t in self.mux_threads if t.is_alive()] + [th]

    def wait_mux(self, timeout=30.0):
        end = time.time() + timeout
        for t in list(self.mux_threads):
            t.join(max(0.1, end - time.time()))


def audio_mux(video, wav, frames, fps):
    """Put the sound into the finished video (ffmpeg, the picture is copied, not encoded again). The video runs at the
    measured frame rate; if that was a bit off, the picture timing is stretched to the real length of the sound."""
    import wave
    name = os.path.basename(video)
    LIVE_RECS.add(name)                                  # not playable / deletable while it is replaced
    tmp = os.path.join(os.path.dirname(wav), "mux_" + name)
    try:
        with wave.open(wav, "rb") as w:
            adur = w.getnframes() / float(w.getframerate() or AUDIO_RATE)
        vdur = frames / fps if fps else 0.0
        if adur < 0.3 or not shutil.which("ffmpeg") or not os.path.isfile(video):
            return
        ratio = adur / vdur if vdur > 0.2 else 1.0
        scale = ratio if 0.25 <= ratio <= 4.0 else 1.0
        cmd = (["nice", "-n", "10"] if shutil.which("nice") else []) + [
            "ffmpeg", "-y", "-loglevel", "error", "-itsscale", f"{scale:.5f}", "-i", video, "-i", wav,
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "64k"] + (
            ["-metadata", "location=" + gps_iso6709(gps_now()), "-metadata", "location-eng=" + gps_iso6709(gps_now())] if CFG["gps_tag"] and gps_now() else []) + [
            "-movflags", "+faststart", tmp]
        r = subprocess.run(cmd, capture_output=True, timeout=900)
        if r.returncode != 0 or not os.path.isfile(tmp) or os.path.getsize(tmp) < 1000:
            log_event("rec", "Sound could not be added: " + (r.stderr.decode(errors="replace").strip()[-160:] or f"ffmpeg exit {r.returncode}"))
            return
        os.replace(tmp, video)
        side = os.path.splitext(video)[0] + ".json"
        try:
            with open(side) as f:
                meta = json.load(f)
            meta.update(audio=True, duration=round(vdur * scale, 1))
            with open(side, "w") as f:
                json.dump(meta, f)
        except (OSError, ValueError):
            pass
        stem = os.path.splitext(name)[0]
        for p in (os.path.join(os.path.dirname(video), ".cache", stem + ".h264.mp4"),):
            try:
                os.remove(p)
            except OSError:
                pass
        _REC_META.pop(name, None)
    except Exception as e:
        log_event("rec", f"Sound could not be added: {e}"[:200])
    finally:
        LIVE_RECS.discard(name)
        for p in (wav, tmp):
            try:
                os.remove(p)
            except OSError:
                pass


# ---- Bluetooth loudspeaker (bluetoothctl + PipeWire / PulseAudio of Raspberry Pi OS) -----------------------------------
#   Search, pair, trust, connect from the page / the window. The sound goes through the sound server of the user session
#   (paplay or pw-cat). Bluetooth speakers often switch themselves off when idle: the Pi reconnects as soon as it is back.
BT_MAC_RE = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")
BT = {"devices": [], "scanning": False, "busy": "", "msg": "", "time": 0.0}
_BT_LOCK = threading.Lock()


def bt_available():
    return shutil.which("bluetoothctl") is not None


def _btctl(*args, timeout=15):
    return _run(["bluetoothctl"] + list(args), timeout=timeout)


def bt_info(mac):
    rc, out, _e = _btctl("info", mac, timeout=8)
    d = {"mac": mac, "name": mac, "paired": False, "connected": False, "trusted": False, "audio": False}
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("Name:"):
            d["name"] = line[5:].strip()[:60] or mac
        elif line.startswith("Alias:") and d["name"] == mac:
            d["name"] = line[6:].strip()[:60] or mac
        elif line.startswith("Paired:"):
            d["paired"] = line.endswith("yes")
        elif line.startswith("Connected:"):
            d["connected"] = line.endswith("yes")
        elif line.startswith("Trusted:"):
            d["trusted"] = line.endswith("yes")
        elif line.startswith("Icon:") and "audio" in line:
            d["audio"] = True
        elif "Audio Sink" in line or "Headset" in line or "Handsfree" in line:
            d["audio"] = True
    return d


def bt_list():
    rc, out, _e = _btctl("devices", timeout=8)
    macs = []
    for line in (out or "").splitlines():
        m = re.match(r"^Device\s+(([0-9A-F]{2}:){5}[0-9A-F]{2})\b", line.strip())
        if m and m.group(1) not in macs:
            macs.append(m.group(1))
    devs = [bt_info(m) for m in macs[:30]]
    devs.sort(key=lambda d: (not d["connected"], not d["paired"], not d["audio"], d["name"].lower()))
    BT["devices"] = devs; BT["time"] = time.time()
    return devs


def bt_scan(seconds=12):
    """Look for Bluetooth devices (the loudspeaker must be in pairing mode). Runs in the background."""
    if not bt_available():
        return False, "bluetoothctl is missing (sudo apt install bluez)"
    if BT["scanning"]:
        return True, ""
    BT["scanning"] = True; BT["msg"] = ""

    def work():
        try:
            _btctl("power", "on", timeout=8)
            t0 = time.time()
            rc, _o, _e = _btctl("--timeout", str(int(seconds)), "scan", "on", timeout=seconds + 8)   # 2.95.54: newer bluez
            if time.time() - t0 < seconds / 2:                      # old bluez without --timeout: keep it open by hand
                p = subprocess.Popen(["bluetoothctl", "scan", "on"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(seconds)
                try:
                    p.terminate(); p.wait(timeout=3)
                except Exception:
                    p.kill()
            _btctl("scan", "off", timeout=5)
            bt_list()
        except Exception as e:
            BT["msg"] = str(e)[:200]
        finally:
            BT["scanning"] = False
    threading.Thread(target=work, daemon=True, name="bt-scan").start()
    return True, ""


def bt_connected(mac):
    return bt_info(mac)["connected"]


def bt_connect(mac, select=True):
    """Pair (if needed), trust and connect a loudspeaker, then use it for the siren / talking."""
    mac = str(mac or "").upper()
    if not BT_MAC_RE.match(mac):
        return False, "invalid Bluetooth address"
    if not bt_available():
        return False, "bluetoothctl is missing (sudo apt install bluez)"
    with _BT_LOCK:
        BT["busy"] = mac
        try:
            _btctl("power", "on", timeout=8)
            info = bt_info(mac)
            if not info["paired"]:
                rc, out, err = _btctl("--agent", "NoInputNoOutput", "pair", mac, timeout=30)   # 2.95.54: a speaker has no keyboard
                if not bt_info(mac)["paired"]:
                    rc, out, err = _btctl("pair", mac, timeout=30)
                if not bt_info(mac)["paired"]:
                    return False, "pairing failed - is the loudspeaker in pairing mode (blue light blinking)?"
            _btctl("trust", mac, timeout=8)
            rc, out, err = _btctl("connect", mac, timeout=25)
            info = bt_info(mac)
            if not info["connected"]:
                return False, "could not connect - switch the loudspeaker on and bring it closer"
            if select and CFG["audio_out"] != "bt:" + mac:
                CFG["audio_out"] = "bt:" + mac; save_settings()
            log_event("sys", f"Bluetooth loudspeaker connected: {info['name']}")
            return True, ""
        finally:
            BT["busy"] = ""
            try:
                bt_list()
            except Exception:
                pass


def bt_disconnect(mac, remove=False):
    mac = str(mac or "").upper()
    if not BT_MAC_RE.match(mac):
        return False, "invalid Bluetooth address"
    _btctl("disconnect", mac, timeout=10)
    if remove:
        _btctl("remove", mac, timeout=10)
        if CFG["audio_out"] == "bt:" + mac:
            CFG["audio_out"] = ""; save_settings()
    log_event("sys", f"Bluetooth loudspeaker {'removed' if remove else 'disconnected'}: {mac}")
    bt_list()
    return True, ""


def bt_keeper():
    """While a Bluetooth loudspeaker is chosen: reconnect it when it was switched off and on again (every 60 s)."""
    warned = False
    while True:
        time.sleep(60)
        out = CFG["audio_out"]
        if not out.startswith("bt:") or not bt_available() or BT["busy"] or SOUND["playing"] or TALK["proc"] is not None:
            continue
        mac = out[3:]
        try:
            if not bt_connected(mac):
                ok, _m = bt_connect(mac, select=False)
                if not ok and not warned:
                    warned = True; log_event("sys", "Bluetooth loudspeaker not reachable - trying again every minute")
                elif ok:
                    warned = False
        except Exception:
            pass


def _bt_sink(mac):
    rc, out, _e = _run(["pactl", "list", "short", "sinks"], timeout=5) if shutil.which("pactl") else (1, "", "")
    key = mac.replace(":", "_")
    for line in (out or "").splitlines():
        parts = line.split("\t")
        if len(parts) > 1 and key in parts[1]:
            return parts[1]
    return None


def out_cmd(rate, connect=True):
    """Command that plays raw 16 bit mono at `rate` on the chosen loudspeaker -> (argv, error)."""
    dev = CFG["audio_out"]
    if dev.startswith("bt:") and BT_MAC_RE.match(dev[3:]):
        if _is_root():
            return None, "Bluetooth sound needs the program as normal user (not with sudo / not as system service)"
        mac = dev[3:]
        if not bt_connected(mac):
            if not connect:                              # talking: do not block, connect in the background
                if not BT["busy"]:
                    threading.Thread(target=bt_connect, args=(mac, False), daemon=True).start()
                return None, "the Bluetooth loudspeaker is being connected - try again in a few seconds"
            ok, err = bt_connect(mac, select=False)
            if not ok:
                return None, err
        sink = _bt_sink(mac)
        if shutil.which("paplay"):
            return ["paplay", "--raw", "--format=s16le", f"--rate={rate}", "--channels=1"] + (["-d", sink] if sink else []), ""
        if shutil.which("pw-cat"):
            return ["pw-cat", "--playback", "--format", "s16", "--rate", str(rate), "--channels", "1"] + (["--target", sink] if sink else []) + ["-"], ""
        return None, "paplay is missing (sudo apt install pulseaudio-utils)"
    if not dev or not AUDIO_DEV_RE.match(dev):
        return None, "no loudspeaker selected"
    if not shutil.which("aplay"):
        return None, "aplay is missing (sudo apt install alsa-utils)"
    return ["aplay", "-q", "-D", dev, "-t", "raw", "-f", "S16_LE", "-r", str(rate), "-c", "1"], ""


def out_selected():
    dev = CFG["audio_out"]
    return bool(dev) and (AUDIO_DEV_RE.match(dev) is not None or (dev.startswith("bt:") and BT_MAC_RE.match(dev[3:]) is not None))


# ---- loudspeaker: siren / test sound -------------------------------------------------------------
SOUND = {"proc": None, "playing": False, "msg": "", "last_alarm": 0.0, "gen": 0}
_SOUND_LOCK = threading.Lock()


def _smooth(env, rate):
    k = max(1, int(rate * 0.006))                        # 6 ms edges: no clicks when a beep starts / stops
    return np.convolve(env.astype(np.float32), np.ones(k, np.float32) / k, mode="same")


def sound_samples(kind, seconds, rate=OUT_RATE):
    """Float samples -1..1 of a generated alarm sound or an own file (looped to the length)."""
    n = max(1, int(seconds * rate)); t = np.arange(n, dtype=np.float64) / rate
    if kind.startswith("beep"):                          # short answer beeps (clap switch): 1-4 rising, or one low
        y = np.zeros(n, np.float32)
        segs = [(0.0, 0.16, 440.0)] if kind == "beeplow" else [(i * 0.18, 0.12, 880.0 * (1.19 ** i)) for i in range(int(kind[4:] or 1))]
        for st_, du, f in segs:
            i0, i1 = int(st_ * rate), min(n, int((st_ + du) * rate))
            if i1 > i0:
                y[i0:i1] = (np.sin(2 * np.pi * f * (t[i0:i1] - st_)) * _smooth(np.ones(i1 - i0), rate) * 0.8).astype(np.float32)
        return y
    if kind in ("chime", "birds"):                       # 2.98.7: wake-up sounds - a soft bell melody / bird song
        y = np.zeros(n, np.float32)
        rng_ = np.random.default_rng(3)
        if kind == "chime":
            notes = [523.25, 659.25, 783.99, 1046.5, 783.99, 659.25]
            pos = 0.0
            while pos < seconds:
                for k, f in enumerate(notes):
                    st_ = pos + k * 0.32
                    i0 = int(st_ * rate)
                    if i0 >= n:
                        break
                    L = min(n - i0, int(1.6 * rate)); tt = np.arange(L) / rate
                    env = np.exp(-tt * 2.6) * np.minimum(1.0, tt / 0.004)
                    y[i0:i0 + L] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.0 * f * tt) + 0.12 * np.sin(2 * np.pi * 3.01 * f * tt)) * env * 0.5
                pos += 3.2
        else:
            pos = 0.2
            while pos < seconds:
                i0 = int(pos * rate)
                if i0 >= n:
                    break
                for k in range(int(rng_.integers(2, 6))):          # a short phrase of chirps
                    L = int(rng_.uniform(0.06, 0.14) * rate); j0 = i0 + k * int(0.16 * rate)
                    if j0 + L >= n:
                        break
                    tt = np.arange(L) / rate; f0 = rng_.uniform(2800, 4200); f1 = f0 * rng_.uniform(0.7, 1.35)
                    ph = 2 * np.pi * np.cumsum(f0 + (f1 - f0) * tt / tt[-1]) / rate
                    y[j0:j0 + L] += np.sin(ph) * np.sin(np.pi * tt / tt[-1]) * 0.7
                pos += float(rng_.uniform(0.8, 2.2))
        return (y / max(1e-6, float(np.max(np.abs(y))))).astype(np.float32)
    if kind == "marmot":                                 # two short whistles
        y = np.zeros(n, np.float32)
        for st in (0.05, 0.55):
            i0, L = int(st * rate), int(0.26 * rate)
            if i0 + L > n:
                break
            tt = np.arange(L) / rate
            f = 3000.0 - 900.0 * (tt / 0.26) ** 1.5
            ph = 2 * np.pi * np.cumsum(f) / rate
            env = np.minimum(1.0, tt / 0.015) * np.minimum(1.0, (0.26 - tt) / 0.06)
            y[i0:i0 + L] = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env
        return (y / max(1e-6, float(np.max(np.abs(y))))).astype(np.float32)
    if kind.startswith("file:") or kind == "tts":
        name = kind[5:]
        path = TTS["file"] if kind == "tts" else os.path.join(sounds_dir(), name)
        if not ((kind == "tts" or SOUND_NAME_RE.match(name)) and os.path.isfile(path)):
            raise ValueError("sound file not found")
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-t", "300", "-f", "s16le", "-ac", "1", "-ar", str(rate), "-"],
                           capture_output=True, timeout=60)
        y = np.frombuffer(r.stdout[:len(r.stdout) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0
        if not y.size:
            raise ValueError("the sound file could not be read")
        return np.tile(y, int(math.ceil(n / y.size)))[:n] if y.size < n else y[:n]
    if kind == "two-tone":
        f = np.where((t % 1.2) < 0.6, 960.0, 770.0)
        env = np.ones(n)
    elif kind == "beeps":
        f = np.full(n, 2400.0); env = _smooth((t % 0.25) < 0.12, rate)
    elif kind == "horn":
        f = np.full(n, 330.0); env = _smooth((t % 1.5) < 1.0, rate)
    elif kind == "whistle":                              # high, fast sweeps (many animals react strongly; small speakers manage)
        f = 6500.0 + 3500.0 * np.abs(((t * 3.0) % 2.0) - 1.0)
        env = _smooth((t % 0.6) < 0.45, rate)
    elif kind == "bangs":                                # short loud noise bursts at irregular times, like claps / banging
        rng_ = np.random.default_rng(7)
        y = np.zeros(n, np.float32); pos = 0.0
        while pos < seconds:
            i = int(pos * rate); L = int(0.06 * rate)
            if i >= n:
                break
            burst = rng_.uniform(-1, 1, min(L, n - i)).astype(np.float32) * np.exp(-np.arange(min(L, n - i)) / (0.012 * rate)).astype(np.float32)
            y[i:i + burst.size] += burst
            pos += float(rng_.uniform(0.18, 0.7))
        return (y / max(1e-6, float(np.max(np.abs(y))))).astype(np.float32)
    else:                                                # siren: rising and falling
        f = 950.0 + 550.0 * np.sin(2 * np.pi * t / 1.8)
        env = np.ones(n)
    ph = 2 * np.pi * np.cumsum(f) / rate
    y = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)          # some harmonics: louder on small speakers
    if kind == "horn":
        y = y + 0.25 * np.sin(4 * ph) + 0.15 * np.sin(5 * ph)
    y = y / np.max(np.abs(y)) * env
    fade = min(n // 4, int(rate * 0.02))
    if fade:
        y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    return y.astype(np.float32)


def sound_play(kind=None, seconds=None, volume=None, reason="test"):
    """Play a sound on the loudspeaker of the Pi. Returns (ok, error). Runs in the background."""
    dev = CFG["audio_out"]
    if not out_selected():
        return False, "no loudspeaker selected"
    if not dev.startswith("bt:") and not shutil.which("aplay"):
        return False, "aplay is missing (sudo apt install alsa-utils)"
    kind = kind or CFG["siren_sound"]
    if kind not in SOUND_KINDS + ("marmot", "chime", "birds", "tts", "beep1", "beep2", "beep3", "beep4", "beeplow") and not (kind.startswith("file:") and kind[5:] in own_sounds()):
        kind = "siren"
    seconds = max(0.5, min(120.0, float(seconds if seconds is not None else CFG["siren_seconds"])))
    vol = max(0.0, min(100.0, float(volume if volume is not None else CFG["siren_volume"]))) / 100.0
    sound_stop(); talk_stop()
    with _SOUND_LOCK:
        SOUND["gen"] += 1; gen = SOUND["gen"]
        SOUND["playing"] = True; SOUND["msg"] = ""

    def work():
        p = None
        try:
            y = sound_samples(kind, seconds)
            data = (np.clip(y * (vol ** 2), -1, 1) * 32767).astype("<i2").tobytes()     # volume: squared feels linear to the ear
            cmd, err = out_cmd(OUT_RATE)                  # Bluetooth: connects first if needed (a few seconds)
            if cmd is None:
                raise RuntimeError(err)
            with _SOUND_LOCK:
                if gen != SOUND["gen"]:
                    return
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                SOUND["proc"] = p
            if AUDIO is not None:
                AUDIO.mute_until = time.time() + seconds + 2.0
            try:
                p.stdin.write(data); p.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            try:
                p.wait(timeout=seconds + 30)
            except subprocess.TimeoutExpired:           # 2.95.34: hangs (Bluetooth) - free the sound device
                p.kill(); p.wait(timeout=5)
            err = (p.stderr.read() or b"").decode(errors="replace").strip()
            if p.returncode not in (0, -9, -15) and gen == SOUND["gen"]:
                SOUND["msg"] = (err.splitlines()[-1] if err else f"{cmd[0]} exit {p.returncode}")[:200]
                log_event("sys", f"Loudspeaker: {SOUND['msg']}")
        except Exception as e:
            SOUND["msg"] = str(e)[:200]
            log_event("sys", f"Loudspeaker: {SOUND['msg']}")
        finally:
            with _SOUND_LOCK:
                if gen == SOUND["gen"]:
                    SOUND["playing"] = False; SOUND["proc"] = None
            if AUDIO is not None:
                AUDIO.mute_until = time.time() + 2.0      # the echo of the room must not trigger the noise alarm
    threading.Thread(target=work, daemon=True, name="sound").start()
    if reason != "test":
        log_event("sys", f"Loudspeaker: {kind} for {seconds:.0f} s ({reason})")
    return True, ""


# ---- spoken announcement from text (offline): pico2wave (nicer voice) or espeak-ng ----
TTS = {"file": os.path.join(tempfile.gettempdir(), "motionwatch_tts.wav")}
_TTS_VOICES = {"de": ("de-DE", "de"), "fr": ("fr-FR", "fr"), "it": ("it-IT", "it"), "rm": ("de-DE", "de"), "en": ("en-GB", "en")}


def tts_engine():
    for e in ("pico2wave", "espeak-ng", "espeak"):
        if shutil.which(e):
            return e
    return None


def tts_make(text, lang, path):
    eng = tts_engine()
    if eng is None:
        return False, "no speech program (sudo apt install espeak-ng - or libttspico-utils for a nicer voice)"
    pico, esp = _TTS_VOICES.get(norm_lang(lang), ("de-DE", "de"))
    cmd = (["pico2wave", "-l", pico, "-w", path, text] if eng == "pico2wave"
           else [eng, "-v", esp, "-s", "145", "-a", "200", "-w", path, text])
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)[:120]
    if r.returncode != 0 or not os.path.isfile(path) or os.path.getsize(path) < 100:
        return False, (r.stderr or b"").decode(errors="replace").strip()[:120] or "speech failed"
    return True, ""


def tts_say(text, lang=None, save=False):
    """Speak a text on the loudspeaker; save=True also keeps it as an own sound («Announcement ….wav»)."""
    text = re.sub(r"[\x00-\x1f]", " ", str(text or "")).strip()[:200]
    if not text:
        return False, "empty text"
    lang = norm_lang(lang or CFG["lang"])
    if save:
        import unicodedata
        tx = text
        for x, y in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ß", "ss")):
            tx = tx.replace(x, y)
        tx = unicodedata.normalize("NFKD", tx).encode("ascii", "ignore").decode()
        nm = re.sub(r"[^A-Za-z0-9 _\-]", "", tx)[:40].strip() or "text"
        path = os.path.join(sounds_dir(), f"{tr('Announcement', lang)} {nm}.wav")
        path = path.encode("ascii", "ignore").decode()
        os.makedirs(sounds_dir(), exist_ok=True)
        ok, err = tts_make(text, lang, path)
        if not ok:
            return False, err
        log_event("sys", f"Announcement saved as sound: {os.path.basename(path)}")
        return True, os.path.basename(path)
    ok, err = tts_make(text, lang, TTS["file"])
    if not ok:
        return False, err
    try:
        import wave
        with wave.open(TTS["file"]) as w_:
            dur = w_.getnframes() / float(w_.getframerate() or 1)
    except Exception:
        dur = 5.0
    log_event("sys", f"Announcement: «{text[:60]}»")
    return sound_play("tts", dur + 0.3, None, reason="test")


def sound_stop():
    with _SOUND_LOCK:
        SOUND["gen"] += 1
        p = SOUND["proc"]; SOUND["proc"] = None; SOUND["playing"] = False
    if p is not None:
        try:
            p.kill()
        except Exception:
            pass


def siren_quiet():
    """2.97.0: no real siren while the test inbox takes the messages (simulation, game round, drill, demo)"""
    try:
        return sandbox_active()
    except Exception:
        return False


def siren_alarm(kind):
    """Siren on the Pi at an alarm (only when armed). siren_on: off | person | alarm (person, thermal, noise) | all (+ pre-alarm)."""
    mode = CFG["siren_on"]
    if mode == "off" or not out_selected() or not is_armed() or SOUND["playing"] or TALK["proc"] is not None:
        return                                           # somebody talks through the loudspeaker: no siren over the voice
    if siren_quiet():
        log_event("sys", f"Siren held back ({kind}): simulation / game / drill - into the test inbox")
        return
    if kind == "person" and CFG.get("escalate_on"):
        return                                           # 2.97.0: the escalation decides (light now, siren after the wait)
    if kind == "prealarm" and mode != "all":
        return
    if kind in ("warm", "noise") and mode not in ("alarm", "all"):
        return
    now = time.time()
    if now - SOUND["last_alarm"] < float(CFG["siren_pause"]):
        return
    SOUND["last_alarm"] = now
    sound_play(None, None, None, reason={"person": "person alarm", "warm": "thermal alarm", "noise": "noise alarm",
                                         "prealarm": "pre-alarm", "tamper": "sabotage alarm", "sensor": "sensor alarm"}.get(kind, kind))


