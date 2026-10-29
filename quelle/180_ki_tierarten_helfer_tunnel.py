#@ Motion Watch – Teil 180: Tierarten, Alarm-Rückblick, KI-Rechenhilfe, KI-Prüfung, Tunnel, AIDetector. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Animal species: a second AI model (image classifier, ONNX) looks at the animals the first AI finds (COCO only knows
#   "dog", "cat", "bear" ... - a fox is often a "dog"). Files: <data>/models/species/<name>.onnx and <name>.txt with one
#   label per line in the order of the model's outputs, optionally "english;Deutsch" (e.g. "red fox;Fuchs").
# ----------------------------------------------------------------------------
SPECIES = {"net": None, "model": "", "labels": set(), "names": [], "msg": "off", "cache": [], "busy": False, "t": 0.0, "last": None}


def species_dir():
    return os.path.join(DATA_DIR, "models", "species")


def species_models():
    try:
        return sorted(f for f in os.listdir(species_dir()) if f.lower().endswith(".onnx") and REC_NAME_RE.match(f))[:20]
    except OSError:
        return []


def species_load():
    m = str(CFG["species_model"] or "")
    if SPECIES["model"] == m and (SPECIES["net"] is not None or not m):
        return SPECIES["net"]
    SPECIES.update(net=None, model=m, names=[], cache=[])
    if not m:
        SPECIES["msg"] = "no model chosen"; return None
    path = os.path.join(species_dir(), m)
    try:
        net = cv2.dnn.readNetFromONNX(path)
        with open(os.path.splitext(path)[0] + ".txt", encoding="utf-8") as f:
            rows = [ln.strip() for ln in f if ln.strip()]
    except (cv2.error, OSError) as e:
        SPECIES["msg"] = f"load error: {e}"[:120]; log_event("ai", f"Animal species model: {SPECIES['msg']}"); return None
    names = []
    for r in rows:
        en, _, de = r.partition(";")
        en = en.strip()[:40]; names.append(en)
        if de.strip():
            DE.setdefault(en, de.strip()[:40])
    SPECIES.update(net=net, names=names, labels=set(names), msg=f"ready · {len(names)} species")
    log_event("ai", f"Animal species model {m} loaded ({len(names)} species)")
    return net


def species_classify(crop):
    """(label, certainty) for one picture of an animal, or None."""
    net = species_load()
    if net is None or crop is None or crop.size == 0:
        return None
    n = int(CFG["species_size"]); img = cv2.cvtColor(cv2.resize(crop, (n, n), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    mode = CFG["species_norm"]
    if mode == "imagenet":
        img = (img - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    elif mode == "-11":
        img = img * 2.0 - 1.0
    net.setInput(img.transpose(2, 0, 1)[None])
    out = net.forward().reshape(-1).astype(np.float64)
    if out.size != len(SPECIES["names"]):
        SPECIES["msg"] = f"the label file has {len(SPECIES['names'])} lines, the model {out.size} outputs"; return None
    if out.min() < 0 or abs(out.sum() - 1.0) > 0.01:          # raw scores -> probabilities
        e = np.exp(out - out.max()); out = e / e.sum()
    i = int(out.argmax())
    return SPECIES["names"][i], float(out[i])


def species_update(objs, frame, pw, ph, t0):
    """Called by the camera loop: the biggest animal is classified in the background (at most every 2 s)."""
    SPECIES["cache"] = [c for c in SPECIES["cache"] if t0 - c[3] < 6]
    if not CFG["species_on"] or not CFG["species_model"] or SPECIES["busy"] or t0 - SPECIES["t"] < 2.0:
        return
    an = [o for o in objs if COCO_LABELS.get(o[5]) in ANIMALS]
    if not an:
        return
    o = max(an, key=lambda b: b[2] * b[3]); H, W = frame.shape[:2]; sx, sy = W / float(pw), H / float(ph)
    x, y, w, h = o[0] * sx, o[1] * sy, o[2] * sx, o[3] * sy
    m = 0.15
    crop = frame[max(0, int(y - h * m)):min(H, int(y + h * (1 + m))), max(0, int(x - w * m)):min(W, int(x + w * (1 + m)))].copy()
    SPECIES["busy"] = True; SPECIES["t"] = t0

    def run():
        try:
            r = species_classify(crop)
            if r and r[1] >= float(CFG["species_conf"]):
                SPECIES["cache"].append((o[:4], r[0], r[1], time.time()))
                if not SPECIES["last"] or SPECIES["last"][0] != r[0] or time.time() - SPECIES["last"][2] > 60:
                    log_event("ai", f"Animal species: {r[0]} {int(r[1] * 100)} % (first AI: {COCO_LABELS.get(o[5])})")
                SPECIES["last"] = (r[0], r[1], time.time())
        except Exception as e:
            SPECIES["msg"] = f"error: {e}"[:120]
        finally:
            SPECIES["busy"] = False
    threading.Thread(target=run, daemon=True, name="species").start()


def species_for(box):
    """The species found for a box of the first AI (overlap), or None."""
    best = None
    for b, lab, conf, _t in SPECIES["cache"]:
        if iou(box, b) > 0.3 and (best is None or conf > best[1]):
            best = (lab, conf)
    return best


def species_install(url):
    """Download a model (.onnx, its labels .txt next to it - or a .zip with both) into the species folder."""
    if not (isinstance(url, str) and re.match(r"^https://[^\s]{4,400}$", url)):
        return False, "address must start with https://"
    os.makedirs(species_dir(), exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9_.\-]", "_", url.rsplit("/", 1)[-1].split("?")[0])[:80] or "model.onnx"

    def get(u, dst, limit=400 * 1024 * 1024):
        req = urllib.request.Request(u, headers={"User-Agent": "MotionWatch/" + APP_VERSION})
        with urllib.request.urlopen(req, timeout=60) as r, open(dst + ".part", "wb") as f:
            n = 0
            for chunk in iter(lambda: r.read(1 << 20), b""):
                n += len(chunk)
                if n > limit:
                    raise ValueError("file too big")
                f.write(chunk)
        os.replace(dst + ".part", dst)
    try:
        if name.lower().endswith(".zip"):
            tmp = os.path.join(species_dir(), name); get(url, tmp)
            with zipfile.ZipFile(tmp) as z:
                for zi in z.infolist():
                    bn = os.path.basename(zi.filename)
                    if bn.lower().endswith((".onnx", ".txt")) and REC_NAME_RE.match(bn):
                        with z.open(zi) as src, open(os.path.join(species_dir(), bn), "wb") as dst:
                            shutil.copyfileobj(src, dst)
            os.remove(tmp)
        elif name.lower().endswith(".onnx"):
            get(url, os.path.join(species_dir(), name))
            try:
                get(url[:url.lower().rfind(".onnx")] + ".txt", os.path.join(species_dir(), name[:-5] + ".txt"), 2 * 1024 * 1024)
            except Exception:
                pass
        else:
            return False, "the address must end with .onnx or .zip"
    except Exception as e:
        return False, _short_net_err(e) if "_short_net_err" in globals() else str(e)[:120]
    ms = species_models()
    if ms and not CFG["species_model"]:
        CFG["species_model"] = ms[0]; save_settings()
    log_event("ai", f"Animal species model installed from {url[:80]}")
    return True, ""


# ---- Alarm-Rückblick (2.95.53): about twice a second, while somebody / an animal is in the picture, where the head looked and
# where in the picture each one was. Round an alarm (15 s before, 20 s after) this is kept as a track - the 3D simulator plays
# it back (Simulator → Alarm-Rückblick). Small: a few kB per alarm, the last 30 are kept. ----
TRACKLOG = deque(maxlen=400)
ALARM_TRACKS = deque(maxlen=30)
_ATR = {"open": None, "t": 0.0, "loaded": False}


def _atr_file():
    return os.path.join(DATA_DIR, "alarm_tracks.json")


def alarm_tracks_load():
    if _ATR["loaded"]:
        return
    _ATR["loaded"] = True
    try:
        with open(_atr_file()) as f:
            for t in json.load(f)[-30:]:
                if isinstance(t, dict) and isinstance(t.get("samples"), list):
                    ALARM_TRACKS.append(t)
    except (OSError, ValueError):
        pass


def _atr_save():
    try:
        tmp = _atr_file() + ".tmp"
        with open(tmp, "w") as f:
            json.dump(list(ALARM_TRACKS), f)
        os.replace(tmp, _atr_file())
    except OSError:
        pass


def alarm_track_sample(persons, animals, pw, ph):
    """from the detection loop: persons = tracks (t.box), animals = AI objects (x, y, w, h, conf, cls)"""
    now = time.time()
    if now - _ATR["t"] < 0.45 or (not persons and not animals):
        return
    _ATR["t"] = now
    hp, ht = servo_half("pan"), servo_half("tilt")
    objs = []
    for t in persons[:6]:
        x, y, w, h = t.box[:4]
        objs.append({"k": "person", "x": round((x + w / 2.0) / pw, 3), "y": round((y + h / 2.0) / ph, 3), "h": round(h / ph, 3)})
    for o in animals[:4]:
        x, y, w, h = o[:4]
        objs.append({"k": COCO_LABELS.get(o[5], "animal"), "x": round((x + w / 2.0) / pw, 3), "y": round((y + h / 2.0) / ph, 3), "h": round(h / ph, 3)})
    smp = {"t": round(now, 2), "pan": round((CFG["pan"] - 50) / 50 * hp, 1), "tilt": round((CFG["tilt"] - 50) / 50 * ht, 1), "objs": objs}
    TRACKLOG.append(smp)
    o_ = _ATR["open"]
    if o_ is not None:
        if now < o_["until"]:
            o_["samples"].append(smp)
        else:
            _ATR["open"] = None
            _atr_save()


def alarm_track_begin(kind, stamp, snap=None):
    """an alarm: keep the last 15 s and the next 20 s"""
    alarm_tracks_load()
    now = time.time()
    if _ATR["open"] is not None and now < _ATR["open"]["until"]:
        _ATR["open"]["until"] = now + 20.0
        return
    tr_ = {"id": stamp, "t": now, "kind": kind, "snap": os.path.basename(snap) if snap else "", "sim": bool(CFG.get("sim_on")),
           "samples": [s_ for s_ in TRACKLOG if now - s_["t"] <= 15.0], "until": now + 20.0}
    ALARM_TRACKS.append(tr_)
    _ATR["open"] = tr_


def alarm_tracks_list():
    alarm_tracks_load()
    out = []
    for t in list(ALARM_TRACKS)[::-1]:
        sm = t.get("samples") or []
        out.append({"id": t["id"], "t": t["t"], "kind": t.get("kind", "person"), "n": len(sm), "sec": round(sm[-1]["t"] - sm[0]["t"], 1) if len(sm) > 1 else 0,
                    "sim": t.get("sim", False)})
    return out


# ---- AI helper (2.95.53): a PC in the same network does the AI for the Pi. The simulator starts MoveEye on the PC with
# --helper; the Pi finds it through the simulator (address + pairing code) or by hand. The Pi sends a small picture, the PC
# answers with the boxes. No answer -> the Pi does it itself again. Only pictures go to the PC, nothing is stored there. ----
HELPER_PORT = 5057
HELPER = {"url": "", "code": "", "src": "", "ok": False, "ms": 0, "rtt": 0, "n": 0, "fails": 0, "next_try": 0.0, "msg": "",
          "busy": False, "res": None, "res_t": 0.0, "name": "", "last_ok": 0.0, "served": 0, "serve_ms": 0, "serve_from": ""}
HELPER_LOCK = threading.Lock()


def helper_target():
    if CFG.get("helper_url"):
        return CFG["helper_url"].rstrip("/"), CFG.get("helper_code") or "", "manual"
    if HELPER.get("auto_url"):
        return HELPER["auto_url"], HELPER.get("auto_code") or "", "simulator"
    return "", "", ""


def helper_ready():
    if not CFG.get("helper_use") or DEMO["on"]:
        return False
    u, _c, _s = helper_target()
    return bool(u) and HELPER["ok"]


def _helper_post(url, code, jpg, conf, oconf, timeout=2.5):
    rq = urllib.request.Request(url + f"/helper/detect?conf={conf:.2f}&oconf={oconf:.2f}", data=jpg, method="POST",
                                headers={"Content-Type": "image/jpeg", "X-Helper-Code": code, "User-Agent": "MotionWatch"})
    with _SIM_OPENER.open(rq, timeout=timeout) as r:
        return json.loads(r.read(200000))


def helper_detect(frame):
    """send the picture in the background, return the newest answer (boxes in the coordinates of this picture)"""
    u, code, _src = helper_target()
    if not u:
        return None
    if not HELPER["busy"]:
        h, w = frame.shape[:2]
        sc = min(1.0, 640.0 / max(1, w))
        small = cv2.resize(frame, (int(w * sc), int(h * sc))) if sc < 1.0 else frame
        ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            HELPER["busy"] = True

            def work(jpg=buf.tobytes(), sc=sc, u=u, code=code):
                t0 = time.time()
                try:
                    d = _helper_post(u, code, jpg, float(CFG["ai_conf"]), float(CFG["object_conf"]))
                    if not d.get("ok"):
                        raise ValueError(str(d.get("error") or "no answer"))
                    k = 1.0 / sc
                    boxes = [(int(b[0] * k), int(b[1] * k), int(b[2] * k), int(b[3] * k), float(b[4])) for b in d.get("boxes", [])]
                    objs = [(int(b[0] * k), int(b[1] * k), int(b[2] * k), int(b[3] * k), float(b[4]), int(b[5])) for b in d.get("objects", [])]
                    HELPER.update(res=(boxes, objs), res_t=time.time(), ms=int(d.get("ms") or 0), rtt=int((time.time() - t0) * 1000),
                                  n=HELPER["n"] + 1, fails=0, last_ok=time.time(), msg="")
                except Exception as e:
                    HELPER["fails"] += 1; HELPER["msg"] = str(e)[:80]
                    if HELPER["fails"] >= 3:
                        HELPER.update(ok=False, next_try=time.time() + 30, res=None)
                        log_event("ai", "AI helper not reachable - the Pi does the AI itself again")
                finally:
                    HELPER["busy"] = False
            threading.Thread(target=work, daemon=True, name="aihelper").start()
    if HELPER["res"] is not None and time.time() - HELPER["res_t"] < 3.0:
        return HELPER["res"]
    return None if time.time() - HELPER["last_ok"] > 3.0 else HELPER["res"]


def helper_tick():
    """every 10 s: find the helper through the simulator, check it (hello) - from the health thread"""
    if DEMO["on"]:
        return
    prev_ = TUN.get("prev_url") or CFG.get("tunnel_prev_url") or ""
    if (CFG["sim_url"].startswith("http://127.0.0.1:18765") and prev_ and time.time() - (TUN["last"] or START) > 180):
        CFG["sim_url"] = prev_; TUN["prev_url"] = ""; CFG["tunnel_prev_url"] = ""; save_settings()   # 2.95.55: also after a restart      # 2.95.54: the tunnel is gone - the old address again
        log_event("sys", "Tunnel of the simulator gone for 3 minutes - back to the normal address")
    _tun_reclaim()
    if CFG.get("sim_on") and not CFG.get("helper_url"):
        hi = None
        if not HELPER["ok"] or time.time() - HELPER.get("info_t", 0) > 60:
            try:
                hi = json.loads(_sim_get("/info", 3.0)[0]).get("helper"); HELPER["info_t"] = time.time()
            except Exception:
                hi = None
        if isinstance(hi, dict) and hi.get("port"):
            host = re.sub(r"^https?://", "", sim_base()).split("/")[0].rsplit(":", 1)[0]
            port = int(hi["port"])
            if sim_base().startswith("http://127.0.0.1:18765"):
                port = 15057                                # 2.95.54: the simulator came through the tunnel - the helper too
            HELPER["auto_url"] = f"http://{host}:{port}"; HELPER["auto_code"] = str(hi.get("code") or "")
    u, code, src = helper_target()
    HELPER["src"] = src
    if not u or not CFG.get("helper_use"):
        if HELPER["ok"]:
            HELPER["ok"] = False
        return
    if HELPER["ok"] and time.time() - HELPER["last_ok"] < 20:
        return
    if time.time() < HELPER["next_try"]:
        return
    try:
        with _SIM_OPENER.open(urllib.request.Request(u + "/helper/hello", headers={"X-Helper-Code": code, "User-Agent": "MotionWatch"}), timeout=3) as r:
            d = json.loads(r.read(20000))
        if not d.get("helper"):
            raise ValueError("not a MoveEye helper")
        if not d.get("paired"):
            raise ValueError("pairing code wrong")
        if not d.get("model"):
            raise ValueError("the PC is still loading its AI model")
        was = HELPER["ok"]
        HELPER.update(ok=True, fails=0, msg="", name=str(d.get("name") or "")[:40], last_ok=time.time(), gpu=str(d.get("accel") or ""))
        if not was:
            log_event("ai", f"AI helper found: {HELPER['name']} ({u}) - the PC does the AI now")
    except Exception as e:
        HELPER.update(ok=False, msg=str(e)[:80], next_try=time.time() + 20)


def helper_state():
    u, code, src = helper_target()
    return {"use": bool(CFG.get("helper_use")), "url": u, "src": src, "ok": HELPER["ok"], "name": HELPER["name"], "ms": HELPER["ms"],
            "rtt": HELPER["rtt"], "n": HELPER["n"], "msg": HELPER["msg"], "manual_url": CFG.get("helper_url") or "",
            "serve": bool(CFG.get("helper_serve")), "my_code": CFG.get("helper_my_code") if CFG.get("helper_serve") else "",
            "served": HELPER["served"], "serve_ms": HELPER["serve_ms"], "serve_from": HELPER["serve_from"], "accel": HELPER.get("gpu", "")}


# ---- KI-Prüfung mit Simulator-Bildern (2.95.53): the 3D simulator makes pictures with a person or an animal (day, dusk,
# night with infrared, rain, fog; near and far) and knows where it is. MoveEye runs its AI (or the PC helper) on each and
# counts what it found, what it missed and false persons. The pictures can be downloaded as training pictures (ZIP). ----
DSET = {"busy": False, "msg": "", "pct": 0, "res": [], "sum": None, "imgs": {}, "t": 0.0}
DSET_ANIMALS = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "animal"}


def _iou(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx)); iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    return inter / max(1e-6, aw * ah + bw * bh - inter)


def _dset_detect(jpg):
    """the AI on one picture: the PC helper if there is one, else here"""
    if helper_ready():
        u, code, _s = helper_target()
        d = _helper_post(u, code, jpg, float(CFG["ai_conf"]), float(CFG["object_conf"]), timeout=6.0)
        if d.get("ok"):
            return d, "PC"
    ai = getattr(WATCH_REF.get("w"), "ai", None)
    if ai is not None and ai.kind == "yolo" and ai.net is not None:     # part 195: the own model is checked, not the standard
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR); t0 = time.time()
        bx, ob = ai.infer(img, float(CFG["ai_conf"]), float(CFG["object_conf"]))
        return {"ok": True, "boxes": [list(b) for b in bx], "objects": [list(o) for o in ob], "ms": int((time.time() - t0) * 1000)}, "Pi · " + tr("Own (MoveEye model)")
    return helper_run(jpg, float(CFG["ai_conf"]), float(CFG["object_conf"])), "Pi"


def dset_run(n):
    if DSET["busy"]:
        return False, "already running"
    if not helper_ready() and not ai_model_paths()[0] and getattr(getattr(WATCH_REF.get("w"), "ai", None), "kind", "") != "yolo":
        return False, "no AI model - load it in the AI settings first (or use the PC helper)"
    DSET.update(busy=True, msg="the simulator makes the pictures …", pct=0, res=[], sum=None, imgs={}, t=time.time())

    def work():
        try:
            if n == "game":                                  # 2.95.75: the pictures the game collected (MoveEye missed the player)
                r = sim_control({"action": "dataset", "op": "game"})
                if not isinstance(r, dict) or not r.get("ok"):
                    raise ValueError("not supported - update the simulator")
                if int(r.get("total") or 0) <= 0:
                    raise ValueError("no missed pictures from the game yet - play a round with MoveEye first")
            else:
                r = sim_control({"action": "dataset", "op": "start", "n": int(n)})
            if not isinstance(r, dict) or not r.get("ok"):
                raise ValueError("not supported - update the simulator")
            t0 = time.time()
            while n != "game" and time.time() - t0 < 900:
                time.sleep(2.0)
                g = sim_control({"action": "dataset", "op": "get"})
                DSET["pct"] = int(60 * int(g.get("done", 0)) / max(1, int(g.get("total", n))))
                DSET["msg"] = "simulator: " + str(g.get("msg") or "")
                if not g.get("busy"):
                    break
            items = (sim_control({"action": "dataset", "op": "list"}) or {}).get("items") or []
            res = []
            for k_, it in enumerate(items):
                jpg, _h = _sim_get(f"/dataset/{int(it['i'])}.jpg", 8.0)
                DSET["imgs"][int(it["i"])] = jpg
                d, where = _dset_detect(jpg)
                img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                h, w = img.shape[:2]
                tb = [float(x) for x in it["box"]]
                pers = [[b[0] / w, b[1] / h, b[2] / w, b[3] / h, b[4]] for b in d.get("boxes", [])]
                objs = [[o[0] / w, o[1] / h, o[2] / w, o[3] / h, o[4], COCO_LABELS.get(o[5], "?")] for o in d.get("objects", [])]
                kind = str(it["kind"])
                found, as_ = False, ""
                if kind == "person":
                    best = max([(_iou(tb, b[:4]), b) for b in pers], default=(0, None), key=lambda x: x[0])
                    found = best[0] >= 0.25
                    as_ = "person" if found else ""
                else:
                    best = max([(_iou(tb, o[:4]), o) for o in objs if o[5] in DSET_ANIMALS], default=(0, None), key=lambda x: x[0])
                    found = best[0] >= 0.2
                    as_ = best[1][5] if found else ""
                false_p = sum(1 for b in pers if _iou(tb, b[:4]) < 0.1) if kind == "person" else len(pers)   # a person where there is none
                res.append({"i": int(it["i"]), "kind": kind, "cond": it["cond"], "dist": it["dist"], "found": found, "as": as_,
                            "false": int(false_p), "ms": int(d.get("ms") or 0), "where": where, "box": tb})
                DSET["pct"] = 60 + int(40 * (k_ + 1) / max(1, len(items)))
                DSET["msg"] = f"AI checks picture {k_ + 1} of {len(items)}"
            DSET["res"] = res
            def grp(key):
                o = {}
                for r_ in res:
                    g_ = o.setdefault(r_[key], [0, 0])
                    g_[0] += 1; g_[1] += 1 if r_["found"] else 0
                return {k: {"n": v[0], "found": v[1], "pct": int(100 * v[1] / max(1, v[0]))} for k, v in o.items()}
            near = [r_ for r_ in res if r_["dist"] < 8]; far = [r_ for r_ in res if r_["dist"] >= 8]
            DSET["sum"] = {"n": len(res), "found": sum(1 for r_ in res if r_["found"]), "false": sum(r_["false"] for r_ in res),
                           "by_cond": grp("cond"), "by_kind": grp("kind"),
                           "near": int(100 * sum(1 for r_ in near if r_["found"]) / max(1, len(near))), "far": int(100 * sum(1 for r_ in far if r_["found"]) / max(1, len(far))),
                           "ms": int(sum(r_["ms"] for r_ in res) / max(1, len(res))), "where": res[0]["where"] if res else ""}
            DSET["msg"] = "done"
            log_event("ai", f"AI test with simulator pictures: {DSET['sum']['found']} of {len(res)} found, {DSET['sum']['false']} false persons")
        except Exception as e:
            DSET["msg"] = "error: " + str(e)[:120]
        finally:
            DSET["busy"] = False; DSET["pct"] = 100 if DSET["sum"] else DSET["pct"]
    threading.Thread(target=work, daemon=True, name="dset").start()
    return True, ""


def dset_zip():
    """the pictures with their boxes for training (YOLO format: class x_center y_center width height, 0..1)"""
    import io
    bio = io.BytesIO()
    cls = {"person": 0}
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", "MoveEye - training pictures from the 3D simulator\nimages/*.jpg + labels/*.txt (YOLO: class cx cy w h, 0..1)\n"
                   "classes: 0 person, 1 animal\nmeta.json: kind, condition, distance, found by the AI\n")
        meta = []
        for r_ in DSET["res"]:
            jpg = DSET["imgs"].get(r_["i"])
            if not jpg:
                continue
            nm = f"sim_{r_['i']:03d}"
            z.writestr(f"images/{nm}.jpg", jpg)
            x, y, w, h = r_["box"]
            z.writestr(f"labels/{nm}.txt", f"{cls.get(r_['kind'], 1)} {x + w / 2:.4f} {y + h / 2:.4f} {w:.4f} {h:.4f}\n")
            meta.append(dict(r_, file=nm + ".jpg"))
        z.writestr("meta.json", json.dumps(meta, indent=1))
    return bio.getvalue()


def dset_state():
    return dict({k: DSET[k] for k in ("busy", "msg", "pct", "sum")}, res=DSET["res"][-80:])


# ---- Tunnel (2.95.54): a simulator behind a firewall that lets nothing in (a PC / virtual machine without admin rights)
# connects OUT to the Pi (port 8766) and keeps a few connections open. MoveEye then talks to it through them as if it
# ran here: 127.0.0.1:18765 = the simulator, 127.0.0.1:15057 = the AI helper on that PC. Paired with a 6-digit code. ----
import socket as _socket
TUN_PORT = 8766
TUN_LOCAL = {18765: 8765, 15057: 5057}
TUN = {"pool": deque(), "lock": threading.Lock(), "last": 0.0, "peer": "", "srv": False, "open": 0, "prev_url": "", "bytes": 0,
       "listen": "", "try": None}


def tunnel_code():
    if not CFG.get("tunnel_code"):
        CFG["tunnel_code"] = "%06d" % secrets.randbelow(1000000); save_settings()
    return CFG["tunnel_code"]


def tunnel_active():
    return time.time() - TUN["last"] < 45 and len(TUN["pool"]) + TUN["open"] > 0


def _tun_pipe(a, b):
    def one(x, y):
        try:
            while True:
                d_ = x.recv(65536)
                if not d_:
                    break
                y.sendall(d_); TUN["bytes"] += len(d_)
        except OSError:
            pass
        finally:
            for z in (x, y):
                try:
                    z.shutdown(_socket.SHUT_RDWR)
                except OSError:
                    pass
    TUN["open"] += 1
    t1 = threading.Thread(target=one, args=(a, b), daemon=True); t2 = threading.Thread(target=one, args=(b, a), daemon=True)
    t1.start(); t2.start()

    def done():
        t1.join(); t2.join()
        TUN["open"] -= 1
        for z in (a, b):
            try:
                z.close()
            except OSError:
                pass
    threading.Thread(target=done, daemon=True).start()


TUN_MAX_AGE = 100.0               # 2.95.101: an idle connection older than this is dead (a router forgot it); the simulator renews its own


def _tun_take():
    """an idle connection of the simulator (dead ones are dropped). 2.95.101: the newest first - the old ones are the ones a
    router may have forgotten, and the simulator (3D-3.75) renews them after 40-55 s anyway"""
    import select
    t0 = time.time()
    while time.time() - t0 < 4.0:
        with TUN["lock"]:
            ct = TUN["pool"].pop() if TUN["pool"] else None
        if ct is None:
            time.sleep(0.1); continue
        c, born = ct
        if time.time() - born > TUN_MAX_AGE:
            try:
                c.close()
            except OSError:
                pass
            continue
        try:
            r, _w, _x = select.select([c], [], [], 0)
            if r and not c.recv(1, _socket.MSG_PEEK):
                c.close(); continue                      # closed by the simulator
        except OSError:
            continue
        return c
    return None


def tunnel_flush():
    """2.98.11: close every idle line of the tunnel. After an update of the simulator on Windows the old lines may stay
    open (the new process inherits them) but nobody answers on them any more: MoveEye waited on them until they were
    100 s old. The simulator opens fresh ones at once."""
    with TUN["lock"]:
        old = list(TUN["pool"]); TUN["pool"].clear()
    for c, _b in old:
        try:
            c.close()
        except OSError:
            pass
    if old:
        log_event("sys", f"Tunnel: {len(old)} old lines closed - the simulator opens new ones")


def tunnel_start():
    """the listener for the simulator (whole network) and the two local doors (only this Pi)"""
    if TUN["srv"] or DEMO["on"]:
        return
    TUN["srv"] = True
    tunnel_code()

    def accept_sim():
        srv = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM); srv.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        try:
            srv.bind(("0.0.0.0", TUN_PORT)); srv.listen(32); TUN["listen"] = "ok"
        except OSError as e:
            TUN["listen"] = str(e)[:80]
            log_event("sys", f"Tunnel for the simulator could not start (port {TUN_PORT}): {e}"); return
        while True:
            c, addr = srv.accept()
            try:
                c.settimeout(6.0)
                line = b""
                while not line.endswith(b"\n") and len(line) < 100:
                    ch = c.recv(1)
                    if not ch:
                        break
                    line += ch
                parts = line.decode("ascii", "replace").split()
                good = bool(CFG.get("tunnel_on")) and len(parts) == 2 and parts[0] == "MWTUN1" and secrets.compare_digest(parts[1], tunnel_code())
                if parts and parts[0] == "MWTUN1":           # 2.95.66: only a simulator counts (not the own simulator search)
                    TUN["try"] = {"peer": addr[0], "t": time.time(), "ok": good}     # 2.95.60: shown on the page (wrong code?)
                if not good:
                    c.sendall(b"NO\n"); c.close(); continue
                c.sendall(b"OK\n"); c.settimeout(None)
                c.setsockopt(_socket.SOL_SOCKET, _socket.SO_KEEPALIVE, 1)
                with TUN["lock"]:
                    TUN["pool"].append((c, time.time()))
                    while len(TUN["pool"]) > 12 or (TUN["pool"] and time.time() - TUN["pool"][0][1] > TUN_MAX_AGE):
                        try:
                            TUN["pool"].popleft()[0].close()
                        except OSError:
                            pass
                was = tunnel_active()
                TUN["last"] = time.time(); TUN["peer"] = addr[0]
                if not was:
                    log_event("sys", f"Simulator connected through the tunnel from {addr[0]}")
                    if not CFG["sim_url"].startswith("http://127.0.0.1:18765"):
                        TUN["prev_url"] = CFG["tunnel_prev_url"] = CFG["sim_url"]; CFG["sim_url"] = "http://127.0.0.1:18765"; save_settings()
            except OSError:
                try:
                    c.close()
                except OSError:
                    pass

    def door(lport, rport):
        srv = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM); srv.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        try:
            srv.bind(("127.0.0.1", lport)); srv.listen(32)
        except OSError:
            return
        while True:
            cl, _a = srv.accept()
            def handle(cl=cl):
                c = _tun_take()
                if c is None:
                    cl.close(); return
                try:
                    c.sendall(f"GO {rport}\n".encode())
                except OSError:
                    cl.close(); c.close(); return
                TUN["last"] = time.time()
                _tun_pipe(cl, c)
            threading.Thread(target=handle, daemon=True).start()
    threading.Thread(target=accept_sim, daemon=True, name="tunnel").start()
    for lp, rp in TUN_LOCAL.items():
        threading.Thread(target=door, args=(lp, rp), daemon=True, name=f"tunnel{lp}").start()


_TUN_RECLAIM = {"t": 0.0}


def _tun_reclaim():
    """2.95.68: the tunnel runs, but the address was set to the direct one again (automatic search, card tapped) and that one
    does not answer (firewall) - back to the tunnel, otherwise the picture stays black for good"""
    if not tunnel_active() or CFG["sim_url"].startswith("http://127.0.0.1:18765"):
        _TUN_RECLAIM["t"] = 0.0; return
    if SIM["ok"] and time.time() - SIM["t"] < 5:
        _TUN_RECLAIM["t"] = 0.0; return            # the direct address works - leave it
    if not _TUN_RECLAIM["t"]:
        _TUN_RECLAIM["t"] = time.time(); return
    if time.time() - _TUN_RECLAIM["t"] < 8:
        return
    _TUN_RECLAIM["t"] = 0.0
    TUN["prev_url"] = CFG["tunnel_prev_url"] = CFG["sim_url"]; CFG["sim_url"] = "http://127.0.0.1:18765"; save_settings()
    log_event("sys", "Simulator does not answer directly, but the tunnel runs - back to the tunnel")
    w = WATCH_REF.get("w")
    if CFG.get("sim_on") and w is not None and str(CFG["source"]).startswith("sim:"):
        w._open_gen += 1; w._start_opener(CFG["source"])


def tunnel_state():
    from urllib.parse import urlparse
    return {"on": bool(CFG.get("tunnel_on")), "code": tunnel_code() if CFG.get("tunnel_on") else "", "port": TUN_PORT, "active": tunnel_active(),
            "peer": TUN["peer"], "idle": len(TUN["pool"]), "open": TUN["open"], "mb": round(TUN["bytes"] / 1e6, 1),
            "listen": TUN["listen"], "try": ({"peer": TUN["try"]["peer"], "ago": int(time.time() - TUN["try"]["t"]), "ok": TUN["try"]["ok"]} if TUN["try"] else None),
            "sim_port": _tun_direct_port()}


def _tun_direct_port():
    """the port MoveEye uses for the simulator without the tunnel (while the tunnel runs: the address from before)"""
    from urllib.parse import urlparse
    u = CFG.get("sim_url") or ""
    if u.startswith("http://127.0.0.1:18765"):
        u = TUN.get("prev_url") or CFG.get("tunnel_prev_url") or ""
    try:
        return int(urlparse(u).port or 8765) if u else 8765
    except ValueError:
        return 8765


# --- the helper side (on the PC) ---
HELPER_NET = {"net": None, "accel": "CPU", "lock": threading.Lock(), "srv": None}


def _helper_net():
    if HELPER_NET["net"] is None:
        pb, pbtxt = ai_model_paths()
        if not pb:
            if not AI_MODEL["busy"]:
                ai_model_download()
            return None
        net = cv2.dnn.readNetFromTensorflow(pb, pbtxt)
        try:                                            # a graphics card with CUDA makes it much faster
            if hasattr(cv2, "cuda") and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA); net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                HELPER_NET["accel"] = "CUDA"
        except Exception:
            pass
        HELPER_NET["net"] = net
    return HELPER_NET["net"]


def helper_run(jpg, conf, oconf):
    img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("no picture")
    net = _helper_net()
    if net is None:
        raise ValueError("AI model is loading")
    t0 = time.time()
    h, w = img.shape[:2]
    with HELPER_NET["lock"]:
        net.setInput(cv2.dnn.blobFromImage(img, size=(300, 300), swapRB=True, crop=False))
        det = net.forward()
    boxes, objects = [], []
    for i in range(det.shape[2]):
        cls, cf = int(det[0, 0, i, 1]), float(det[0, 0, i, 2])
        if cls < 1 or cf < (conf if cls == 1 else oconf):
            continue
        x1, y1, x2, y2 = (det[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
        x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(w - 1, x2), min(h - 1, y2)
        if x2 > x1 and y2 > y1:
            (boxes.append([int(x1), int(y1), int(x2 - x1), int(y2 - y1), round(cf, 3)]) if cls == 1
             else objects.append([int(x1), int(y1), int(x2 - x1), int(y2 - y1), round(cf, 3), cls]))
    ms = int((time.time() - t0) * 1000)
    HELPER["served"] += 1; HELPER["serve_ms"] = ms
    return {"ok": True, "boxes": boxes, "objects": objects, "ms": ms}


def helper_server_start():
    """a small separate web server for the helper (port 5057, whole network) - the page of MoveEye on the PC stays local"""
    if HELPER_NET["srv"] is not None:
        return
    if not CFG.get("helper_my_code"):
        CFG["helper_my_code"] = "%06d" % secrets.randbelow(1000000); save_settings()
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _js(self, obj, code=200):
            b = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
            self.end_headers(); self.wfile.write(b)

        def _paired(self):
            return secrets.compare_digest(str(self.headers.get("X-Helper-Code") or ""), str(CFG.get("helper_my_code") or "x"))

        def do_GET(self):
            if self.path.startswith("/helper/hello"):
                local = self.client_address[0] in ("127.0.0.1", "::1")
                d = {"helper": 1, "name": CFG.get("device_name") or __import__("socket").gethostname(), "ver": APP_VERSION, "paired": self._paired(),
                     "model": bool(ai_model_paths()[0]), "accel": HELPER_NET["accel"], "served": HELPER["served"], "ms": HELPER["serve_ms"]}
                if local:                                   # the simulator on this PC passes the code on to the Pi
                    d.update(code=CFG.get("helper_my_code"), port=HELPER_PORT, loading=AI_MODEL.get("busy"), pct=AI_MODEL.get("pct"))
                    if not d["model"] and not AI_MODEL["busy"]:
                        ai_model_download()
                return self._js(d)
            self._js({"error": "not found"}, 404)

        def do_POST(self):
            if not self.path.startswith("/helper/detect"):
                return self._js({"error": "not found"}, 404)
            if not self._paired():
                return self._js({"ok": False, "error": "pairing code wrong"}, 403)
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > 3 << 20:
                return self._js({"ok": False, "error": "picture too big"}, 413)
            jpg = self.rfile.read(n)
            q = dict(x.split("=", 1) for x in (self.path.split("?", 1)[1].split("&") if "?" in self.path else []) if "=" in x)
            try:
                HELPER["serve_from"] = self.client_address[0]
                res = helper_run(jpg, float(q.get("conf", 0.5)), float(q.get("oconf", 0.5)))
            except Exception as e:
                return self._js({"ok": False, "error": str(e)[:80]}, 503)
            self._js(res)

    try:
        srv = ThreadingHTTPServer(("0.0.0.0", HELPER_PORT), H)
    except OSError as e:
        log_event("ai", f"AI helper could not start (port {HELPER_PORT}): {e}")
        return
    srv.daemon_threads = True
    HELPER_NET["srv"] = srv
    threading.Thread(target=srv.serve_forever, daemon=True, name="helpersrv").start()
    log_event("ai", f"AI helper for other MoveEye ready (port {HELPER_PORT}, pairing code {CFG['helper_my_code']})")


class AIDetector:
    PB, PBTXT = "frozen_inference_graph.pb", "ssd_mobilenet_v2_coco.pbtxt"

    def __init__(self, force_ssd=False):
        self.net = None
        self.kind = "ssd"        # "ssd" or "yolo" (own MoveEye model, part 195)
        self.meta = None         # manifest of the own model
        self.boxes = []          # last persons, in processing-frame coordinates
        self.objects = []        # last non-person objects (x, y, w, h, conf, cls)
        self.frame_counter = 0
        STATE["ai_model_note"] = ""
        if CFG.get("ai_model") == "own" and not force_ssd:
            net, meta, why = own_ai_load()
            if net is not None:
                self.net, self.kind, self.meta = net, "yolo", meta
                STATE["ai_status"] = "ready"; STATE["ai_model"] = own_ai_name(meta)
                log_event("ai", f"AI model {STATE['ai_model']} loaded ({', '.join(meta['classes'])}, {meta['input']} px)")
                return
            STATE["ai_model_note"] = why
            log_event("ai", f"Own AI model not used ({why}) - the standard model (SSD) runs instead")
        STATE["ai_model"] = "SSD MobileNet V2"
        pb, pbtxt = ai_model_paths()
        if pb:
            try:
                self.net = cv2.dnn.readNetFromTensorflow(pb, pbtxt)
                STATE["ai_status"] = "ready"
                log_event("ai", "AI model SSD MobileNet V2 loaded")
            except Exception as e:
                STATE["ai_status"] = "load error"
                log_event("ai", f"AI model could not be loaded: {e}")
        else:
            CFG["ai_enabled"] = False
            STATE["ai_status"] = "no model files"
            log_event("ai", "AI off: model files not found - «Download AI model» in the self-check or the AI settings")

    def infer(self, img, conf_p, conf_o):
        """One run of the network on a picture: (persons [(x, y, w, h, conf)], objects [(x, y, w, h, conf, coco_cls)]) in
        picture coordinates. SSD and the own YOLO model give the same form (the own classes are mapped to COCO ids)."""
        h, w = img.shape[:2]
        if self.kind == "yolo":
            return own_ai_detect(self.net, self.meta, img, conf_p, conf_o)
        self.net.setInput(cv2.dnn.blobFromImage(img, size=(300, 300), swapRB=True, crop=False))
        det = self.net.forward()
        boxes, objects = [], []
        for i in range(det.shape[2]):
            cls, conf = int(det[0, 0, i, 1]), float(det[0, 0, i, 2])
            need = conf_p if cls == 1 else conf_o
            if cls < 1 or conf < need:
                continue
            x1, y1, x2, y2 = (det[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
            x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(w - 1, x2), min(h - 1, y2)
            if x2 > x1 and y2 > y1:
                if cls == 1:
                    boxes.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1), conf))
                else:
                    objects.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1), conf, cls))
        return boxes, objects

    def detect(self, frame):
        """Run every N frames; returns list of (x, y, w, h, conf) persons."""
        if DEMO["on"]:
            self.boxes, self.objects = demo_ai(frame); STATE["ai_status"] = "demo"
            return self.boxes
        hp = helper_ready()                                 # 2.95.53: a PC does the AI (faster, the Pi stays cool)
        if (self.net is None and not hp) or not CFG["ai_enabled"]:
            STATE["ai_status"] = "off" if (self.net or hp) else STATE["ai_status"]
            self.boxes = []; self.objects = []
            return self.boxes
        if hp:
            got = helper_detect(frame)
            if got is not None:
                self.boxes, self.objects = got
                STATE["ai_persons"] = len(self.boxes)
                STATE["ai_status"] = f"PC · {HELPER['ms']} ms"
                return self.boxes
            if self.net is None:
                return self.boxes
        self.frame_counter += 1
        if self.frame_counter % (max(1, int(CFG["ai_every"])) * batt_save_ai_k()) != 0:     # 2.98.13: battery saver (105)
            return self.boxes
        # at most a few times per second and slower when the Pi gets hot: the AI is the biggest load (power, heat)
        gap = max(0.3, 2.0 * (STATE.get("ai_ms") or 0) / 1000.0)
        ct = STATE.get("cpu_temp") or 0
        gap *= 4.0 if ct >= 80 else 2.0 if ct >= 75 else 1.0
        if CFG.get("sim_on") and sim_eco_now():
            gap *= 2.0
        gap *= batt_save_ai_k()                                     # simulation with CPU saving: the AI only half as often
        if time.time() - getattr(self, "_last_run", 0.0) < gap:
            return self.boxes
        self._last_run = time.time()
        t0 = time.time()
        h, w = frame.shape[:2]
        try:
            boxes, objects = self.infer(frame, CFG["ai_conf"], CFG["object_conf"])
        except Exception as e:
            if self.kind != "yolo":
                raise
            STATE["ai_model_note"] = f"error while running: {e}"[:120]     # own model fails on this Pi: back to the standard
            log_event("ai", f"Own AI model failed ({str(e)[:120]}) - the standard model (SSD) runs instead")
            note = STATE["ai_model_note"]; self.__init__(force_ssd=True); STATE["ai_model_note"] = note
            return self.boxes
        # 2.98.13: «KI-Lupe» - something small moves (a person far away, 20-30 pixels in the 300 x 300 picture of the AI):
        # look at that part once more, enlarged. Far persons were found by the AI only rarely before.
        if CFG.get("ai_zoom", True):
            for hb in sorted(getattr(self, "hints", []), key=lambda b: -b[2] * b[3])[:1]:
                if any(iou(hb, b[:4]) > 0.1 for b in boxes):
                    continue
                side = int(min(min(w, h), max(110, 3.2 * hb[3])))
                cx, cy = hb[0] + hb[2] // 2, hb[1] + hb[3] // 2
                x0 = max(0, min(w - side, cx - side // 2)); y0 = max(0, min(h - side, cy - side // 2))
                crop = frame[y0:y0 + side, x0:x0 + side]
                if crop.size == 0:
                    continue
                for a1, b1, bw, bh, conf in self.infer(crop, CFG["ai_conf"], 2.0)[0]:      # only persons
                    bx = (x0 + a1, y0 + b1, max(1, bw), max(1, bh), conf)
                    if bx[3] >= 0.6 * side and side > 0.8 * min(w, h):
                        continue                               # the whole crop as one «person»: not trusted
                    if not any(iou(bx[:4], b[:4]) > 0.3 for b in boxes):
                        boxes.append(bx); STATE["ai_zoom_hits"] = STATE.get("ai_zoom_hits", 0) + 1
        self.boxes = boxes; self.objects = objects
        STATE["ai_ms"] = int((time.time() - t0) * 1000)
        STATE["ai_status"] = f"running · {STATE['ai_ms']} ms"
        STATE["ai_persons"] = len(boxes)
        return boxes


# COCO class ids used by SSD MobileNet V2 (TensorFlow 91-id label map)
COCO_LABELS = {
    1: "person", 2: "bicycle", 3: "car", 4: "motorcycle", 5: "airplane", 6: "bus", 7: "train", 8: "truck",
    9: "boat", 10: "traffic light", 11: "fire hydrant", 13: "stop sign", 14: "parking meter", 15: "bench",
    16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep", 21: "cow", 22: "elephant", 23: "bear",
    24: "zebra", 25: "giraffe", 27: "backpack", 28: "umbrella", 31: "handbag", 32: "tie", 33: "suitcase",
    34: "frisbee", 35: "skis", 36: "snowboard", 37: "sports ball", 38: "kite", 39: "baseball bat",
    40: "baseball glove", 41: "skateboard", 42: "surfboard", 43: "tennis racket", 44: "bottle",
    46: "wine glass", 47: "cup", 48: "fork", 49: "knife", 50: "spoon", 51: "bowl", 52: "banana",
    53: "apple", 54: "sandwich", 55: "orange", 56: "broccoli", 57: "carrot", 58: "hot dog", 59: "pizza",
    60: "donut", 61: "cake", 62: "chair", 63: "couch", 64: "potted plant", 65: "bed", 67: "dining table",
    70: "toilet", 72: "tv", 73: "laptop", 74: "mouse", 75: "remote", 76: "keyboard", 77: "cell phone",
    78: "microwave", 79: "oven", 80: "toaster", 81: "sink", 82: "refrigerator", 84: "book", 85: "clock",
    86: "vase", 87: "scissors", 88: "teddy bear", 89: "hair drier", 90: "toothbrush",
}


