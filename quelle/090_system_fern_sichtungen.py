#@ Motion Watch – Teil 090: System, Fernzugriff, Sichtungen, Nachtbericht, Gast-Zugang. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# System monitor: CPU load (+ temperature) sampled once per second
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Remote access (Tailscale): who watches from outside right now
#   Tailscale addresses are 100.64.0.0/10 and fd7a:115c:a1e0::/48. A device counts as "watching" while it streams the
#   video or has asked the page for news in the last 20 s. Names come from "tailscale status --json" (every 30 s).
# ----------------------------------------------------------------------------
_TS_NETS = (ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48"))
REMOTE = {"seen": {}, "streams": {}, "names": {}}
REMOTE_LOCK = threading.Lock()


def is_remote_ip(ip):
    try:
        a = ipaddress.ip_address((ip or "").split("%")[0])
        if getattr(a, "ipv4_mapped", None):
            a = a.ipv4_mapped
        return any(a.version == n.version and a in n for n in _TS_NETS)
    except ValueError:
        return False


def remote_touch(ip):
    if is_remote_ip(ip):
        with REMOTE_LOCK:
            REMOTE["seen"][ip] = time.time()


def remote_stream(ip, delta):
    if is_remote_ip(ip):
        with REMOTE_LOCK:
            n = REMOTE["streams"].get(ip, 0) + delta
            if n > 0:
                REMOTE["streams"][ip] = n
            else:
                REMOTE["streams"].pop(ip, None)
            REMOTE["seen"][ip] = time.time()


def tailscale_status():
    """{'state': 'Running' | 'NeedsLogin' | 'Stopped' | '' (not installed), 'ip', 'name', 'peers': {ip: name}}"""
    exe = shutil.which("tailscale")
    if not exe:
        return {"state": "", "ip": "", "name": "", "peers": {}}
    try:
        r = subprocess.run([exe, "status", "--json"], capture_output=True, text=True, timeout=8)
        j = json.loads(r.stdout or "{}")
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"state": "error", "ip": "", "name": "", "peers": {}}
    me = j.get("Self") or {}
    ips = me.get("TailscaleIPs") or []
    peers = {}
    for p in (j.get("Peer") or {}).values():
        nm = (p.get("HostName") or (p.get("DNSName") or "").split(".")[0] or "?")[:32]
        for ip in p.get("TailscaleIPs") or []:
            peers[ip] = nm
    return {"state": str(j.get("BackendState") or "")[:20], "ip": next((x for x in ips if ":" not in x), ips[0] if ips else ""),
            "name": (me.get("DNSName") or "").rstrip(".")[:80], "peers": peers}


class RemoteMonitor:
    """Keeps STATE["remote"] (names of devices watching from outside) and STATE["remote_ts"] up to date."""
    HOLD = 20.0

    def __init__(self):
        self._ts_t = 0.0; self._prev = set()
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                self.tick()
            except Exception as e:                           # never let this thread die
                log_event("sys", f"Remote access check: {e}")
            time.sleep(2.0)

    def tick(self):
        now = time.time()
        if now - self._ts_t > 30:
            self._ts_t = now
            ts = tailscale_status()
            with REMOTE_LOCK:
                REMOTE["names"] = ts.pop("peers")
            STATE["remote_ts"] = ts
        with REMOTE_LOCK:
            for ip in [ip for ip, t in REMOTE["seen"].items() if now - t > self.HOLD and ip not in REMOTE["streams"]]:
                REMOTE["seen"].pop(ip, None)
            active = set(REMOTE["seen"]) | set(REMOTE["streams"])
            names = {ip: REMOTE["names"].get(ip, ip) for ip in active}
        STATE["remote"] = sorted(set(names.values()))
        new = active - self._prev
        for ip in sorted(new):
            log_event("web", f"Remote access from {names[ip]} ({ip})")
        for ip in sorted(self._prev - active):
            log_event("web", f"Remote access ended: {REMOTE['names'].get(ip, ip)}")
        if new and not self._prev and CFG["notify_remote"]:
            w = WATCH_REF["w"]
            if w is not None:
                who = ", ".join(sorted({names[ip] for ip in new}))
                de = CFG["lang"] == "de"
                w.notifier.info(trf("Remote access: {who} is watching", who=who), title="{name}: " + tr("remote access"))
        self._prev = active


# ----------------------------------------------------------------------------
# Sightings: every "visit" of a person, an animal, a warm body or a noise is noted (start, end, best picture).
#   Used by the animal diary (/diary, the best picture of every animal visit) and the night report (push in the morning).
#   A visit ends when the label was not seen for 45 s. Pictures: <recordings>/diary/, list: <data>/sightings.json
# ----------------------------------------------------------------------------
SIGHT = {"list": [], "loaded": False}
SIGHT_LOCK = threading.Lock()
_DIARY_NAME = re.compile(r"^[0-9]{8}_[0-9]{6}_[a-z ]{2,20}_[0-9a-f]{6}\.jpg$")


def diary_dir():
    return os.path.join(rec_dir(), "diary")


def _sight_file():
    return os.path.join(DATA_DIR, "sightings.json")


def sight_kind(label):
    return "animal" if label in ANIMALS or label in SPECIES["labels"] else (label if label in ("person", "warm", "noise") else "object")


def sight_load():
    with SIGHT_LOCK:
        if SIGHT["loaded"]:
            return
        SIGHT["loaded"] = True
        try:
            with open(_sight_file()) as f:
                lst = json.load(f)
            SIGHT["list"] = [e for e in lst if isinstance(e, dict) and isinstance(e.get("label"), str) and isinstance(e.get("start"), str)][-5000:]
        except (OSError, ValueError):
            SIGHT["list"] = []


def _sight_save():
    try:
        tmp = _sight_file() + ".tmp"
        with open(tmp, "w") as f:
            json.dump(SIGHT["list"], f)
        os.replace(tmp, _sight_file())
    except OSError as e:
        log_event("sys", f"Sightings could not be saved: {e}")


def sight_purge():
    """Forget visits older than the keep time (favourites stay) and delete their pictures."""
    keep = max(7, int(CFG["diary_keep_days"]))
    limit = (datetime.now() - timedelta(days=keep)).isoformat(timespec="seconds")
    with SIGHT_LOCK:
        old = [e for e in SIGHT["list"] if e["start"] < limit and not e.get("fav")]
        if not old:
            return 0
        SIGHT["list"] = [e for e in SIGHT["list"] if not (e["start"] < limit and not e.get("fav"))]
        _sight_save()
    for e in old:
        if e.get("img"):
            for p in (os.path.join(diary_dir(), e["img"]), os.path.join(diary_dir(), ".thumbs", e["img"])):
                try:
                    os.remove(p)
                except OSError:
                    pass
    return len(old)


class SightingTracker:
    GAP = 45.0          # s without the label -> the visit is over
    MIN_FRAMES = 3      # seen in at least 3 pictures (a single wrong detection is no visit)

    def __init__(self):
        self.open = {}
        sight_load()
        self._purge_t = 0.0

    def see(self, label, t0, frame=None, box=None, conf=1.0, pw=1, ph=1):
        v = self.open.get(label)
        if v is None:
            v = self.open[label] = {"start": t0, "last": t0, "frames": 0, "score": 0.0, "jpg": None, "conf": 0.0, "img_t": 0.0}
        v["last"] = t0; v["frames"] += 1
        if frame is None or box is None or sight_kind(label) not in ("animal", "person"):
            return
        area = max(0.0, box[2] * box[3] / float(max(1, pw * ph)))
        score = float(conf) * min(1.0, area * 6.0) ** 0.5
        if score <= v["score"] * 1.05 or t0 - v["img_t"] < 0.5:
            return
        try:
            H, W = frame.shape[:2]; sx, sy = W / float(pw), H / float(ph)
            img = frame.copy()
            x, y, w, h = int(box[0] * sx), int(box[1] * sy), int(box[2] * sx), int(box[3] * sy)
            cv2.rectangle(img, (x, y), (x + w, y + h), (80, 200, 255), 2, cv2.LINE_AA)
            if W > 1280:
                img = cv2.resize(img, (1280, int(H * 1280 / W)), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ok:
                v.update(score=score, jpg=buf.tobytes(), conf=float(conf), img_t=t0)
        except (cv2.error, ValueError):
            pass

    def tick(self, t0, force=False):
        for label in [k for k, v in self.open.items() if force or t0 - v["last"] > self.GAP]:
            v = self.open.pop(label)
            if v["frames"] >= self.MIN_FRAMES:
                self._store(label, v)
        if t0 - self._purge_t > 3600:
            self._purge_t = t0
            n = sight_purge()
            if n:
                log_event("rec", f"Diary: {n} old entries removed")

    def _store(self, label, v):
        st = datetime.fromtimestamp(v["start"])
        e = {"id": uuid.uuid4().hex[:6], "label": label, "kind": sight_kind(label),
             "start": st.isoformat(timespec="seconds"), "end": datetime.fromtimestamp(v["last"]).isoformat(timespec="seconds"),
             "dur": int(round(v["last"] - v["start"])), "conf": round(v["conf"], 2), "img": "", "fav": False}
        if v["jpg"]:
            name = f"{st.strftime('%Y%m%d_%H%M%S')}_{re.sub(r'[^a-z ]', '', label)[:20] or 'x'}_{e['id']}.jpg"
            try:
                os.makedirs(diary_dir(), exist_ok=True)
                with open(os.path.join(diary_dir(), name), "wb") as f:
                    f.write(v["jpg"])
                gps_tag_jpg(os.path.join(diary_dir(), name))
                e["img"] = name
                g = gps_now()
                if g:
                    e["gps"] = [round(g[0], 5), round(g[1], 5)]
            except OSError as ex:
                log_event("rec", f"Diary picture could not be saved: {ex}")
        with SIGHT_LOCK:
            SIGHT["list"].append(e)
            if len(SIGHT["list"]) > 5000:                # 2.95.34: starred entries stay, the others go (with their pictures)
                drop = [e for e in SIGHT["list"][:len(SIGHT["list"]) - 5000] if not e.get("fav")]
                ids = {id(e) for e in drop}
                SIGHT["list"] = [e for e in SIGHT["list"] if id(e) not in ids]
                for e in drop:
                    for k_ in ("pic", "img", "jpg"):
                        if isinstance(e.get(k_), str) and re.fullmatch(r"[\w.\-]+\.jpg", e[k_]):
                            try:
                                os.remove(os.path.join(diary_dir(), e[k_]))
                            except (OSError, NameError):
                                pass
            _sight_save()
        if e["kind"] == "animal":
            log_event("rec", f"Diary: {label} ({e['dur']} s)")


def diary_items(label="", lang="en", fav=False):
    sight_load()
    with SIGHT_LOCK:
        lst = [dict(e) for e in SIGHT["list"] if e["kind"] == "animal" and e.get("img")]
    counts = {}
    for e in lst:
        counts[e["label"]] = counts.get(e["label"], 0) + 1
    if label:
        lst = [e for e in lst if e["label"] == label]
    if fav:
        lst = [e for e in lst if e.get("fav")]
    lst.sort(key=lambda e: e["start"], reverse=True)
    for e in lst:
        e["name"] = tr_trigger(e["label"], lang)
    labels = sorted(({"key": k, "label": tr_trigger(k, lang), "count": c} for k, c in counts.items()), key=lambda x: -x["count"])
    return {"items": lst[:600], "labels": labels, "total": sum(counts.values())}


def diary_action(action, eid, value=None):
    sight_load()
    with SIGHT_LOCK:
        e = next((x for x in SIGHT["list"] if x.get("id") == eid), None)
        if e is None:
            return False, "unknown entry"
        if action == "fav":
            e["fav"] = bool(value)
        elif action == "delete":
            SIGHT["list"].remove(e)
        else:
            return False, "unknown action"
        _sight_save()
    if action == "delete" and e.get("img"):
        for p in (os.path.join(diary_dir(), e["img"]), os.path.join(diary_dir(), ".thumbs", e["img"])):
            try:
                os.remove(p)
            except OSError:
                pass
    return True, ""


def diary_thumb(name):
    """Path of a 400 px picture of a diary entry (made once), or None."""
    if not _DIARY_NAME.match(name or ""):
        return None
    src = os.path.join(diary_dir(), name)
    if not os.path.isfile(src):
        return None
    tp = os.path.join(diary_dir(), ".thumbs", name)
    if not os.path.isfile(tp):
        try:
            img = cv2.imread(src)
            if img is None:
                return None
            h, w = img.shape[:2]
            os.makedirs(os.path.dirname(tp), exist_ok=True)
            cv2.imwrite(tp, cv2.resize(img, (400, max(1, int(h * 400 / w))), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 75])
        except (OSError, cv2.error):
            return None
    return tp


# ---- night report -----------------------------------------------------------
def report_window(now=None):
    """(start, end) of the night the report is about: from <report_from> o'clock to <report_hour> o'clock.
    Before the report hour: the night so far. While the simulator is connected: its clock (285)."""
    now = now or sim_now()
    hr, fr = int(CFG["report_hour"]) % 24, int(CFG["report_from"]) % 24
    span = (hr - fr) % 24 or 24
    end = now.replace(hour=hr, minute=0, second=0, microsecond=0)
    if now < end:
        return end - timedelta(hours=span), now
    return end - timedelta(hours=span), end


def report_build(lang=None, start=None, end=None):
    """Text + best picture (path) of the night report."""
    lang = cur_lang(lang)
    if start is None:
        start, end = report_window()
        a, b = sim_to_real(start).isoformat(timespec="seconds"), sim_to_real(end).isoformat(timespec="seconds")   # the simulated night in real time (285)
    else:
        a, b = start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")
    sight_load()
    with SIGHT_LOCK:
        ev = [dict(e) for e in SIGHT["list"] if a <= e["start"] < b]
    span = f"{start.strftime('%H')}–{end.strftime('%H')} " + tr("o'clock", lang)
    if not ev:
        return {"text": trf("Quiet night – nothing detected ({span}).", lang, span=span),
                "img": "", "count": 0, "from": a, "to": b}
    groups = {}
    for e in sorted(ev, key=lambda e: e["start"]):
        groups.setdefault(e["label"], []).append(e)
    order = sorted(groups, key=lambda k: ({"person": 0, "warm": 2, "noise": 3}.get(k, 1), -len(groups[k])))
    parts = []
    for k in order:
        times = [e["start"][11:16] for e in groups[k]]
        nm = tr_trigger(k, lang) if k not in ("warm", "noise") else (tr("thermal", lang) if k == "warm" else tr("noise", lang))
        nm = nm.split(" (")[0]
        parts.append(f"{nm} {len(times)}× ({', '.join(times[:4])}{' …' if len(times) > 4 else ''})")
    animals = sum(len(v) for k, v in groups.items() if k in ANIMALS)
    persons = len(groups.get("person", []))
    head = []
    if persons:
        head.append(trf("{n} persons" if persons > 1 else "{n} person", lang, n=persons))
    if animals:
        head.append(trf("{n} animals" if animals > 1 else "{n} animal", lang, n=animals))
    text = ((", ".join(head) + " – ") if head else "") + "; ".join(parts) + f" ({span})"
    best = [e for e in ev if e.get("img")]
    best.sort(key=lambda e: (e["label"] == "person", e.get("conf", 0)), reverse=True)
    return {"text": text, "img": best[0]["img"] if best else "", "count": len(ev), "from": a, "to": b}


MORNING_EXTRA = {"day": "", "lines": [], "jpg": None}    # 2.98.1: one morning push - panorama and simulator week go into the night report


def morning_add(text, jpg=None):
    """2.98.1: something for this morning's push. True = it comes with the night report; False = send it yourself
    (night report off, or already sent today)."""
    day = datetime.now().strftime("%Y-%m-%d")
    if not CFG.get("report_on") or CFG.get("report_last_day") == day:
        return False
    if MORNING_EXTRA["day"] != day:
        MORNING_EXTRA.update(day=day, lines=[], jpg=None)
    MORNING_EXTRA["lines"].append(str(text))
    if jpg and MORNING_EXTRA["jpg"] is None:
        MORNING_EXTRA["jpg"] = jpg
    return True


def morning_wait(now):
    """2.98.1: in the first 10 minutes wait for the panorama, so it comes in the same push (the simulator week: weekly report, 426)"""
    if now.minute >= 10:
        return False
    day = now.strftime("%Y-%m-%d")
    try:
        if CFG.get("refscan_pano_on") and (PANO.get("busy") or (PANO.get("day") != day and CFG.get("refscan_pano_day") != day)):
            return True
    except NameError:
        pass
    return False


def report_send(w, manual=False):
    r = report_build()
    if MORNING_EXTRA["day"] == datetime.now().strftime("%Y-%m-%d") and MORNING_EXTRA["lines"]:
        r["text"] = r["text"] + "\n" + "\n".join(MORNING_EXTRA["lines"])
    STATE["report_last"] = {"t": datetime.now().isoformat(timespec="seconds"), "text": r["text"], "img": r["img"], "sent": False}
    if w is None or not Notifier.configured() or not CFG["notify_on"]:
        return r, False
    jpg = None
    if r["img"]:
        try:
            p = os.path.join(diary_dir(), r["img"])
            img = cv2.imread(p)
            if img is not None:
                h, wd = img.shape[:2]
                if wd > 800:
                    img = cv2.resize(img, (800, int(h * 800 / wd)), interpolation=cv2.INTER_AREA)
                if CFG["share_logo"]:
                    img = brand_image(img, tr("Night report") + " " + datetime.now().strftime("%d.%m.%Y"))
                ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
                jpg = buf.tobytes() if ok else None
        except (OSError, cv2.error):
            jpg = None
    msg = r["text"]
    if CFG.get("report_strip", True):                      # 2.98.13: one sentence + a picture strip of the night (066)
        try:
            sent, strip = alx_morning(r)
            extra = r["text"].split("\n", 1)[1] if "\n" in r["text"] else ""
            msg = sent + (("\n" + extra) if extra else "")
            jpg = strip or jpg
        except Exception as e:
            log_event("sys", f"Night report strip: {e}"[:160])
    if jpg is None and MORNING_EXTRA["jpg"]:
        jpg = MORNING_EXTRA["jpg"]                         # 2.98.1: no picture of an animal: the panorama
    if not manual:
        MORNING_EXTRA.update(lines=[], jpg=None)
    de = CFG["lang"] == "de"
    pub = CFG["public_url"].strip().rstrip("/")
    ok = w.notifier.info(msg, pub + "/diary" if pub else "", title="{name}: " + tr("night report"),
                         jpg=jpg, fname="nachtbericht.jpg")
    STATE["report_last"]["sent"] = bool(ok)
    log_event("web", ("Night report sent" if ok else "Night report not sent") + (" (by hand)" if manual else "") + f": {r['text'][:80]}")
    return r, ok


class ReportScheduler:
    """Sends the night report once a day at the report hour (also up to 3 h late, e.g. when the Pi was off)."""
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            time.sleep(30)
            try:
                now = sim_now(); hr = int(CFG["report_hour"]) % 24     # the simulated morning while connected (285)
                day = now.strftime("%Y-%m-%d")
                if CFG["report_on"] and CFG["report_last_day"] != day and hr <= now.hour < hr + 3 and not morning_wait(now):
                    CFG["report_last_day"] = day; save_settings()
                    report_send(WATCH_REF["w"])
            except Exception as e:
                log_event("sys", f"Night report: {e}")


# ---- guest access -------------------------------------------------------------
GUESTS = {"streams": 0}


def guest_ok(token):
    tok = CFG["guest_token"]
    if not tok or not isinstance(token, str) or not hmac.compare_digest(token.encode(), tok.encode()):
        return False
    if CFG["guest_until"] and time.time() > CFG["guest_until"]:
        return False
    return True


def guest_info():
    tok = CFG["guest_token"]
    active = bool(tok) and not (CFG["guest_until"] and time.time() > CFG["guest_until"])
    return {"active": active, "path": f"/g/{tok}" if active else "", "until": CFG["guest_until"] if active else 0,
            "watching": GUESTS["streams"]}


def guest_set(action, hours=24):
    if action == "end":
        CFG["guest_token"] = ""; CFG["guest_until"] = 0.0
        save_settings(); log_event("web", "Guest access ended")
        return True, ""
    if action != "create":
        return False, "unknown action"
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        return False, "not a number"
    if not math.isfinite(hours) or hours < 0 or hours > 24 * 365:
        return False, "not a number"
    CFG["guest_token"] = secrets.token_urlsafe(18)
    CFG["guest_until"] = time.time() + hours * 3600 if hours else 0.0
    save_settings()
    log_event("web", "Guest access created" + (f" for {hours:g} h" if hours else " (no time limit)"))
    return True, ""


# ---- battery (powerbank) runtime estimate ---------------------------------------
def _pmic_watts():
    """Power of the Pi 5 itself from its power chip (all rails, V x A), or None."""
    if not shutil.which("vcgencmd"):
        return None
    rc, txt, _e = _run(["vcgencmd", "pmic_read_adc"], timeout=5)
    if rc != 0 or not txt:
        return None
    amps, volts = {}, {}
    for m in re.finditer(r"(\S+)_A\s+current\(\d+\)=([0-9.]+)A", txt):
        amps[m.group(1)] = float(m.group(2))
    for m in re.finditer(r"(\S+)_V\s+volt\(\d+\)=([0-9.]+)V", txt):
        volts[m.group(1)] = float(m.group(2))
    p = sum(a * volts[k] for k, a in amps.items() if k in volts)
    return p if p > 0.2 else None


