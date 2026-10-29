#@ MoveEye – Teil 195: Eigenes KI-Modell (YOLO als ONNX, trainiert auf GitHub aus Simulator- und echten Bildern). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# «KI-Modell: Standard (SSD) / Eigenes (MoveEye-Modell)». The own model is a small YOLOv8 / YOLO11 detector, trained by
#   the GitHub workflow .github/workflows/ki_modell.yml (ki_training/README.md) and published as a release asset:
#     moveeye_model.onnx   the network (input 1 x 3 x N x N, RGB 0..1, letterbox; output 1 x (4 + nc) x A)
#     moveeye_model.json   its manifest: {"format": "moveeye-model-1", "version", "classes": ["person", "animal", "vehicle"],
#                          "input": 320, "file": "moveeye_model.onnx", "sha256", "size", "conf": {"person": 0.3, ...},
#                          "metrics": {"map50", "map50_95", ...}, "made", "images"}
#   It runs with cv2.dnn.readNetFromONNX (no extra Python packages on the Pi). The classes are mapped to COCO ids so that
#   the rest of MoveEye (relays, deterrence, diary, species) keeps working: person -> the person boxes, animal -> id 92
#   "animal" (new, counts as an animal), vehicle -> 3 "car", any COCO name (dog, cat ...) -> its own id.
#   If the files are missing or the model fails, the standard model (SSD MobileNet V2) runs instead.
# ----------------------------------------------------------------------------
OWN_AI = {"busy": False, "msg": "", "pct": 0}
OWN_AI_ONNX, OWN_AI_JSON = "moveeye_model.onnx", "moveeye_model.json"
OWN_AI_ANIMAL_ID = 92
OWN_AI_WILD = {"animal", "fox", "deer", "boar", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "lynx", "chamois", "ibex",
               "roe deer", "wild boar", "rabbit", "mouse", "rat", "raccoon", "goat", "pig"}
COCO_LABELS.setdefault(OWN_AI_ANIMAL_ID, "animal")       # after part 190 (TRIGGERS has "animal" already)
ANIMALS.add("animal")


def own_ai_paths():
    """(onnx, json) of the first folder that has both - next to the program or in <data>/models."""
    for d in ai_model_dirs():
        a, b = os.path.join(d, OWN_AI_ONNX), os.path.join(d, OWN_AI_JSON)
        if os.path.isfile(a) and os.path.isfile(b):
            return a, b
    return None, None


def own_ai_check_manifest(m):
    """The manifest as a clean dict - raises ValueError with a short reason if something does not fit."""
    if not isinstance(m, dict) or m.get("format") != "moveeye-model-1":
        raise ValueError("not a MoveEye model description")
    cl = m.get("classes")
    if not (isinstance(cl, list) and 1 <= len(cl) <= 100 and all(isinstance(c, str) and 0 < len(c) <= 40 for c in cl)):
        raise ValueError("classes missing in the model description")
    n = int(m.get("input") or 0)
    if not (n % 32 == 0 and 160 <= n <= 1280):
        raise ValueError("input size of the model not valid")
    sha = str(m.get("sha256") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError("checksum missing in the model description")
    fn = str(m.get("file") or OWN_AI_ONNX)
    if not re.fullmatch(r"[A-Za-z0-9_.\-]{1,80}\.onnx", fn):
        raise ValueError("file name not valid")
    conf = m.get("conf") if isinstance(m.get("conf"), dict) else {}
    out = dict(m, classes=[c.strip().lower() for c in cl], input=n, sha256=sha, file=fn,
               conf={str(k): min(0.9, max(0.05, float(v))) for k, v in conf.items() if isinstance(v, (int, float))},
               version=str(m.get("version") or "?")[:40])
    return out


def own_ai_name(meta):
    return f"MoveEye model {meta.get('version', '?')}" if meta else "SSD MobileNet V2"


def own_ai_classmap(names):
    """[(coco_id or 1 for person, is_person)] per class of the own model; None = class not used."""
    by_name = {v: k for k, v in COCO_LABELS.items()}
    out = []
    for nm in names:
        if nm == "person":
            out.append((1, True))
        elif nm in ("vehicle", "car"):
            out.append((3, False))
        elif nm in by_name:
            out.append((by_name[nm], False))
        elif nm in OWN_AI_WILD:
            out.append((OWN_AI_ANIMAL_ID, False))
        else:
            out.append(None)
    return out


def own_ai_letterbox(img, n):
    """the picture into an n x n square (aspect kept, grey borders like at the training): (square, scale, dx, dy)"""
    h, w = img.shape[:2]; r = min(n / float(w), n / float(h))
    nw, nh = max(1, int(round(w * r))), max(1, int(round(h * r)))
    sq = np.full((n, n, 3), 114, np.uint8); dx, dy = (n - nw) // 2, (n - nh) // 2
    sq[dy:dy + nh, dx:dx + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if r < 1 else cv2.INTER_LINEAR)
    return sq, r, dx, dy


def own_ai_decode(out, nc, thr, r, dx, dy, w, h, nms_iou=0.45):
    """YOLOv8 / YOLO11 output 1 x (4 + nc) x A (or 1 x A x (4 + nc)): cx, cy, bw, bh in pixels of the square input and nc class
    scores (already 0..1). thr = minimum score per class. Returns [(x, y, w, h, conf, class)] in picture pixels after NMS per class."""
    a = np.asarray(out, dtype=np.float32)
    while a.ndim > 2 and a.shape[0] == 1:
        a = a[0]
    if a.ndim != 2 or (a.shape[0] != 4 + nc and a.shape[1] != 4 + nc):
        raise ValueError(f"unexpected model output {tuple(np.asarray(out).shape)} for {nc} classes")
    if a.shape[0] == 4 + nc and a.shape[1] != 4 + nc:
        a = a.T                                            # -> A x (4 + nc)
    sc = a[:, 4:4 + nc]
    k = sc.argmax(1); conf = sc[np.arange(sc.shape[0]), k]
    keep = conf >= np.asarray(thr, np.float32)[k]
    if not keep.any():
        return []
    a, k, conf = a[keep], k[keep], conf[keep]
    x1 = np.clip((a[:, 0] - a[:, 2] / 2 - dx) / r, 0, w - 1); y1 = np.clip((a[:, 1] - a[:, 3] / 2 - dy) / r, 0, h - 1)
    x2 = np.clip((a[:, 0] + a[:, 2] / 2 - dx) / r, 0, w - 1); y2 = np.clip((a[:, 1] + a[:, 3] / 2 - dy) / r, 0, h - 1)
    ok = (x2 - x1 >= 1) & (y2 - y1 >= 1)
    x1, y1, x2, y2, k, conf = x1[ok], y1[ok], x2[ok], y2[ok], k[ok], conf[ok]
    if not len(conf):
        return []
    off = k.astype(np.float32) * float(w + h + 10)          # NMS per class: each class moved to its own place
    rects = [[float(x1[i] + off[i]), float(y1[i]), float(x2[i] - x1[i]), float(y2[i] - y1[i])] for i in range(len(conf))]
    idx = cv2.dnn.NMSBoxes(rects, [float(c) for c in conf], 0.0, nms_iou)
    idx = np.asarray(idx).reshape(-1) if len(idx) else []
    res = [(int(x1[i]), int(y1[i]), int(round(x2[i] - x1[i])), int(round(y2[i] - y1[i])), float(conf[i]), int(k[i])) for i in idx]
    return sorted(res, key=lambda b: -b[4])


def own_ai_thresholds(meta, conf_p, conf_o):
    """the sliders keep their meaning: 0.5 = the best threshold found at the training («conf» of the manifest), higher = stricter"""
    th = []
    for nm in meta["classes"]:
        base = float(meta["conf"].get(nm, 0.35))
        th.append(round(min(0.95, max(0.05, base + (float(conf_p if nm == "person" else conf_o) - 0.5))), 3))
    return th


def own_ai_detect(net, meta, img, conf_p, conf_o):
    """(persons, objects) like the SSD part of AIDetector.infer"""
    h, w = img.shape[:2]; n = int(meta["input"])
    sq, r, dx, dy = own_ai_letterbox(img, n)
    net.setInput(cv2.dnn.blobFromImage(sq, 1.0 / 255.0, (n, n), swapRB=True, crop=False))
    out = net.forward()
    cmap = meta.get("_map") or own_ai_classmap(meta["classes"])
    th = own_ai_thresholds(meta, conf_p, conf_o)
    th = [2.0 if cmap[i] is None or (not cmap[i][1] and conf_o > 1.0) else t for i, t in enumerate(th)]    # conf_o > 1: only persons
    boxes, objects = [], []
    for x, y, bw, bh, cf, k in own_ai_decode(out, len(meta["classes"]), th, r, dx, dy, w, h):
        cid, is_p = cmap[k]
        if is_p:
            boxes.append((x, y, bw, bh, cf))
        else:
            objects.append((x, y, bw, bh, cf, cid))
    return boxes, objects


def own_ai_load():
    """(net, manifest, "") or (None, None, reason) - the network is tried once on an empty picture (an OpenCV that cannot
    run the model is found here, not at the first alarm)."""
    onnx, js = own_ai_paths()
    if not onnx:
        return None, None, "own model not downloaded yet"
    try:
        with open(js, encoding="utf-8") as f:
            meta = own_ai_check_manifest(json.load(f))
        net = cv2.dnn.readNetFromONNX(onnx)
        n = meta["input"]
        net.setInput(cv2.dnn.blobFromImage(np.zeros((n, n, 3), np.uint8), 1.0 / 255.0, (n, n), swapRB=True))
        o = net.forward()
        own_ai_decode(o, len(meta["classes"]), [2.0] * len(meta["classes"]), 1.0, 0, 0, n, n)    # shape check
        meta["_map"] = own_ai_classmap(meta["classes"])
        if not any(m and m[1] for m in meta["_map"]):
            raise ValueError("the model has no class «person»")
        return net, meta, ""
    except (OSError, ValueError, TypeError, cv2.error) as e:
        return None, None, f"load error: {str(e).splitlines()[0] if str(e) else e.__class__.__name__}"[:140]


def own_ai_switched():
    """«KI-Modell» changed: load it (in the background - the network needs a moment)"""
    w = WATCH_REF.get("w")
    if w is None:
        return
    def run():
        try:
            w.ai = AIDetector()
            if w.ai.kind == "yolo" and not CFG["ai_enabled"]:
                CFG["ai_enabled"] = True; save_settings()  # chosen by hand: the AI is wanted (it was switched off without a model)
        except Exception as e:
            log_event("ai", f"AI model switch failed: {e}"[:200])
    threading.Thread(target=run, daemon=True, name="ai-switch").start()


def _own_ai_get(url, limit, progress=None):
    """bytes of an https address (certificates checked, size limited) and their sha256"""
    req = urllib.request.Request(url, headers={"User-Agent": "MotionWatch/" + APP_VERSION})
    h = hashlib.sha256(); buf = bytearray()
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        if total > limit:
            raise ValueError("file too big")
        for chunk in iter(lambda: r.read(256 * 1024), b""):
            buf += chunk; h.update(chunk)
            if len(buf) > limit:
                raise ValueError("file too big")
            if progress:
                progress(len(buf), total)
    return bytes(buf), h.hexdigest()


def own_ai_download(url=None):
    """Fetch the own model: manifest (moveeye_model.json) from the address in the settings, then the .onnx file next to it;
    the sha256 of the manifest must match. Then switch to it («KI-Modell: Eigenes»)."""
    if OWN_AI["busy"]:
        return False, "already running"
    if DEMO["on"]:
        return False, "not in the demo"
    url = str(url or CFG.get("ai_own_url") or DEFAULTS["ai_own_url"]).strip()
    if not (url.startswith("https://") and _http_ok(url)):
        return False, "https://... address of moveeye_model.json expected"
    OWN_AI.update(busy=True, msg="downloading", pct=0)

    def run():
        dst = os.path.join(DATA_DIR, "models"); tmp_o = os.path.join(dst, OWN_AI_ONNX + ".part"); tmp_j = os.path.join(dst, OWN_AI_JSON + ".part")
        try:
            os.makedirs(dst, exist_ok=True)
            raw, _h = _own_ai_get(url, 256 * 1024)
            try:
                meta = own_ai_check_manifest(json.loads(raw.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                raise RuntimeError("the model description is not valid")
            except ValueError as e:
                raise RuntimeError(str(e))
            src = meta.get("url") if str(meta.get("url") or "").startswith("https://") else url.rsplit("/", 1)[0] + "/" + meta["file"]
            def prog(got, total):
                OWN_AI["pct"] = int(got * 90 / total) if total else min(89, got // (200 * 1024))
            data, sha = _own_ai_get(src, 80 * 1024 * 1024, prog)
            if sha != meta["sha256"]:
                raise RuntimeError("checksum wrong - the file is damaged or not the right one")
            OWN_AI["pct"] = 95
            with open(tmp_o, "wb") as f:
                f.write(data)
            with open(tmp_j, "wb") as f:
                f.write(raw)
            try:
                net = cv2.dnn.readNetFromONNX(tmp_o)
                n = meta["input"]; net.setInput(cv2.dnn.blobFromImage(np.zeros((n, n, 3), np.uint8), 1.0 / 255.0, (n, n), swapRB=True))
                own_ai_decode(net.forward(), len(meta["classes"]), [2.0] * len(meta["classes"]), 1.0, 0, 0, n, n)
            except (cv2.error, ValueError) as e:
                raise RuntimeError(("this OpenCV cannot run the model: " + str(e).splitlines()[0][:80]) if str(e) else "model damaged")
            os.replace(tmp_o, os.path.join(dst, OWN_AI_ONNX)); os.replace(tmp_j, os.path.join(dst, OWN_AI_JSON))
            CFG["ai_model"] = "own"; CFG["ai_enabled"] = True; save_settings()
            w = WATCH_REF.get("w")
            if w is not None:
                w.ai = AIDetector()
            OWN_AI.update(msg="ready", pct=100)
            log_event("ai", f"Own AI model {meta['version']} downloaded ({len(data) // 1024} kB, sha256 ok) and switched on")
        except Exception as e:
            reason = _short_net_err(e) if isinstance(e, (OSError, urllib.error.URLError)) else str(e)
            OWN_AI.update(msg=f"failed: {tr(reason)}"[:140], pct=0)
            log_event("ai", f"Own AI model download failed: {reason}"[:200])
        finally:
            OWN_AI["busy"] = False
            for p_ in (tmp_o, tmp_j):
                try:
                    os.remove(p_)
                except OSError:
                    pass
    threading.Thread(target=run, daemon=True, name="own-ai").start()
    return True, ""


def own_ai_info(lang=None):
    """for the web page, the window and the self-check"""
    onnx, js = own_ai_paths(); meta = None
    if js:
        try:
            key = (js, os.path.getmtime(js))
            if OWN_AI.get("_mkey") != key:               # read again only when the file changed (the window asks every second)
                with open(js, encoding="utf-8") as f:
                    OWN_AI["_meta"] = own_ai_check_manifest(json.load(f))
                OWN_AI["_mkey"] = key
            meta = OWN_AI.get("_meta")
        except (OSError, ValueError, TypeError):
            meta = None; OWN_AI["_mkey"] = None
    ai = getattr(WATCH_REF.get("w"), "ai", None)
    running = "own" if ai is not None and ai.kind == "yolo" else ("ssd" if ai is not None and ai.net is not None else "")
    m = (meta or {}).get("metrics") or {}
    return {"choice": CFG.get("ai_model", "ssd"), "running": running, "running_version": ai.meta.get("version") if running == "own" else None, "note": tr(STATE.get("ai_model_note") or "", lang),
            "present": bool(onnx), "version": (meta or {}).get("version"), "classes": (meta or {}).get("classes"),
            "input": (meta or {}).get("input"), "map50": m.get("map50"), "made": (meta or {}).get("made"),
            "busy": OWN_AI["busy"], "pct": OWN_AI["pct"], "msg": OWN_AI["msg"], "url": CFG.get("ai_own_url") or DEFAULTS["ai_own_url"]}


def own_ai_text(lang=None):
    """one line: which model runs (status lines in the window and on the page)"""
    i = own_ai_info(lang)
    run = {"own": tr("MoveEye model", lang) + " " + str(i["running_version"]), "ssd": "SSD MobileNet V2"}.get(i["running"]) or tr("none", lang)
    t = "🧠 " + tr("AI model", lang) + ": " + run
    if i["choice"] == "own" and i["note"]:
        t += " · ⚠ " + tr("own model not used", lang) + " (" + i["note"] + ")"
    if i["present"]:
        t += f" · {tr('downloaded', lang)}: {i['version']}" + (f" · mAP50 {i['map50']:.2f}" if isinstance(i["map50"], (int, float)) else "")
    return t


def own_ai_selftest():
    """self-test: a fake YOLO output (2 classes, 6 anchors) - decoding, letterbox back to the picture, NMS, class mapping"""
    n, nc, A = 320, 3, 6
    o = np.zeros((1, 4 + nc, A), np.float32)
    cand = [(160, 120, 40, 100, 0, 0.9), (162, 121, 42, 98, 0, 0.8),      # one person twice (NMS keeps one)
            (60, 200, 50, 30, 1, 0.7), (61, 200, 50, 30, 0, 0.6),         # an animal and a weaker «person» on the same place (other class: both stay)
            (250, 100, 20, 20, 2, 0.1), (100, 100, 10, 10, 1, 0.2)]       # below the thresholds
    for j, (cx, cy, bw, bh, k, cf) in enumerate(cand):
        o[0, :4, j] = (cx, cy, bw, bh); o[0, 4 + k, j] = cf
    w, h = 640, 480                                        # picture 640 x 480 -> scale 0.5, 40 px border above and below
    _sq, r, dx, dy = own_ai_letterbox(np.zeros((h, w, 3), np.uint8), n)
    assert abs(r - 0.5) < 1e-6 and (dx, dy) == (0, 40), f"letterbox {r} {dx} {dy}"
    got = own_ai_decode(o, nc, [0.5, 0.5, 0.5], r, dx, dy, w, h)
    assert len(got) == 3, f"{len(got)} boxes instead of 3: {got}"
    p = got[0]
    assert p[5] == 0 and abs(p[4] - 0.9) < 1e-6 and abs(p[0] - 280) <= 1 and abs(p[1] - 60) <= 1 and abs(p[2] - 80) <= 1 and abs(p[3] - 200) <= 1, f"person {p}"
    assert sorted(b[5] for b in got) == [0, 0, 1], f"classes {got}"
    got_t = own_ai_decode(o.transpose(0, 2, 1), nc, [0.5, 0.5, 0.5], r, dx, dy, w, h)     # 1 x A x (4 + nc) gives the same
    assert got_t == got, "transposed output"
    cm = own_ai_classmap(["person", "animal", "vehicle", "dog", "fox", "toaster-robot"])
    assert cm[0] == (1, True) and cm[1] == (OWN_AI_ANIMAL_ID, False) and cm[2] == (3, False) and cm[3] == (18, False) and cm[4] == (OWN_AI_ANIMAL_ID, False) and cm[5] is None
    assert COCO_LABELS[OWN_AI_ANIMAL_ID] in ANIMALS
    try:
        own_ai_decode(np.zeros((1, 9, 5), np.float32), nc, [0.5] * 3, 1, 0, 0, w, h); raise AssertionError("wrong shape not found")
    except ValueError:
        pass
    m = own_ai_check_manifest({"format": "moveeye-model-1", "classes": ["person", "animal", "vehicle"], "input": 320, "sha256": "a" * 64, "conf": {"person": 0.3}})
    assert own_ai_thresholds(m, 0.5, 0.6) == [0.3, 0.45, 0.45], own_ai_thresholds(m, 0.5, 0.6)
