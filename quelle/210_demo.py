#@ Motion Watch – Teil 210: Demo-Modus. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Demo mode (--demo): a drawn camping scene where now and then a person, a dog or a bear walks by - the whole program reacts
#   as with a real camera (alarm, recording, diary, deterrence, header). Own settings folder, nothing is changed on the
#   computer: shutting down, Wi-Fi, updates, passwords and the like are switched off. For trying it out / an online demo.
# ----------------------------------------------------------------------------
DEMO = {"on": False, "objs": [], "size": (960, 540)}
DEMO_BLOCK = ("/api/power", "/api/wifi", "/api/hotspot", "/api/password", "/api/settings/import", "/api/pause", "/api/autostart",
              "/api/backup", "/api/fleet", "/api/time", "/api/gps", "/api/bt", "/api/lock", "/api/ai_model", "/api/ext")


class DemoSource:
    def __init__(self):
        W, H = DEMO["size"]
        self.t0 = time.time(); self.fps = 15.0; self.last = 0.0
        bg = np.zeros((H, W, 3), np.float32)
        for y in range(H):                                            # sky
            k = y / (H * 0.55)
            bg[y] = (235 - 60 * k, 200 - 50 * k, 150 - 40 * k)
        hz = int(H * 0.55)
        pts = np.array([[0, hz], [120, hz - 90], [260, hz - 30], [420, hz - 140], [600, hz - 40], [760, hz - 110], [960, hz - 20], [960, hz], [0, hz]], np.int32)
        cv2.fillPoly(bg, [pts], (120, 110, 100))                       # mountains
        bg[hz:] = (60, 120, 70)                                        # meadow
        rng = np.random.default_rng(3)
        for i in range(600):
            x, y = int(rng.integers(0, W)), int(rng.integers(hz, H))
            cv2.line(bg, (x, y), (x + int(rng.integers(-2, 3)), y - int(rng.integers(3, 9))), (40, 100 + int(rng.integers(0, 50)), 50), 1)
        for x in (70, 150, 840, 900):                                  # trees
            cv2.rectangle(bg, (x - 5, hz - 10), (x + 5, hz + 40), (40, 60, 80), -1)
            cv2.fillPoly(bg, [np.array([[x - 40, hz + 5], [x, hz - 110], [x + 40, hz + 5]], np.int32)], (40, 90, 50))
        tent = np.array([[560, hz + 120], [660, hz + 10], [760, hz + 120]], np.int32)   # tent
        cv2.fillPoly(bg, [tent], (60, 140, 230)); cv2.fillPoly(bg, [np.array([[640, hz + 120], [660, hz + 50], [680, hz + 120]], np.int32)], (40, 70, 120))
        self.bg = bg; self.hz = hz

    def set_fps(self, fps):
        self.fps = float(fps) if fps else 15.0

    def _person(self, img, x, y, ph):
        s_ = ph / 100.0; leg = math.sin(ph * 0 + time.time() * 7) * 12 * s_
        c = (60, 50, 60)
        cv2.circle(img, (int(x), int(y - 88 * s_)), int(9 * s_), (170, 190, 220), -1)
        cv2.rectangle(img, (int(x - 10 * s_), int(y - 78 * s_)), (int(x + 10 * s_), int(y - 38 * s_)), (50, 60, 160), -1)
        cv2.line(img, (int(x), int(y - 40 * s_)), (int(x + leg), int(y)), c, max(2, int(7 * s_)))
        cv2.line(img, (int(x), int(y - 40 * s_)), (int(x - leg), int(y)), c, max(2, int(7 * s_)))

    def _animal(self, img, x, y, size, col):
        leg = math.sin(time.time() * 9) * 6 * size
        cv2.ellipse(img, (int(x), int(y - 22 * size)), (int(28 * size), int(13 * size)), 0, 0, 360, col, -1)
        cv2.circle(img, (int(x + 30 * size), int(y - 30 * size)), int(10 * size), col, -1)
        for dx in (-18, 16):
            cv2.line(img, (int(x + dx * size), int(y - 15 * size)), (int(x + dx * size + leg), int(y)), col, max(2, int(4 * size)))

    def read(self):
        wait = 1.0 / max(1.0, self.fps) - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        t = time.time() - self.t0; W, H = DEMO["size"]
        img = self.bg.copy()
        for i, (cx, cy) in enumerate(((120, 60), (420, 90), (760, 50))):    # clouds drift
            x = int((cx + t * (6 + i * 2)) % (W + 200)) - 100
            cv2.ellipse(img, (x, cy), (70, 22), 0, 0, 360, (245, 245, 245), -1)
        objs = []
        cyc = t % 90.0
        if 12 < cyc < 26:                                               # a person walks past the tent
            k = (cyc - 12) / 14.0; x = -40 + k * (W + 80); y = self.hz + 150
            self._person(img, x, y, 110); objs.append(("person", int(x - 16), int(y - 110), 32, 112))
        if 55 < cyc < 66:                                               # an animal crosses the meadow
            k = (cyc - 55) / 11.0; big = int(t // 90) % 3 == 2
            x = W + 60 - k * (W + 120); y = self.hz + 210
            sz = 2.2 if big else 1.1
            self._animal(img, x, y, sz, (40, 50, 70) if big else (40, 110, 200))
            objs.append(("bear" if big else "dog", int(x - 30 * sz), int(y - 40 * sz), int(72 * sz), int(42 * sz)))
        night = max(0.0, math.sin(t / 600.0 * math.pi)) * 0.0               # (kept bright: a demo should be seen)
        img = np.clip(img * (1 - night) + np.random.default_rng(int(t * 15)).normal(0, 2.0, img.shape), 0, 255).astype(np.uint8)
        DEMO["objs"] = objs
        return True, img

    def release(self):
        pass


def demo_ai(frame):
    """AI results in the demo: what the scene has drawn (in the coordinates of the processing picture)."""
    H, W = frame.shape[:2]; sx, sy = W / DEMO["size"][0], H / DEMO["size"][1]
    ids = {v: k for k, v in COCO_LABELS.items()}
    boxes, objs = [], []
    for lab, x, y, w, h in DEMO["objs"]:
        b = (int(x * sx), int(y * sy), max(2, int(w * sx)), max(2, int(h * sy)))
        if lab == "person":
            boxes.append(b + (0.91,))
        else:
            objs.append(b + (0.86, ids.get(lab, 18)))
    return boxes, objs


def open_source(spec, thermal=False):
    """Open a source (may block for seconds - always call from a background thread). thermal=True opens USB cameras unforced.
    Returns (source or None, resolved id, label, error text)."""
    label = source_label(spec)
    try:
        kind, _, arg = spec.partition(":")
        if spec == "demo" or DEMO["on"]:
            return DemoSource(), "demo", "Demo", ""
        if kind == "sim":                                  # the separate simulation program (simulator connection)
            if arg == "thermal":
                src = SimThermalSource()
                return (src, spec, label, "") if src.ok() else (None, spec, label, "simulator not reachable")
            src = _open_url(sim_base() + f"/cam/{arg}/video.mjpg" + (f"?fps={sim_cam_fps(arg)}" if sim_eco_now() else ""))
            return (src, spec, label, "") if src else (None, spec, label, "simulator not reachable - is it running?")
        if spec == "auto":
            for idx in range(4):
                src = _open_usb(idx)
                if src:
                    return src, f"usb:{idx}", f"USB camera {idx}", ""
            return None, spec, label, "no working USB camera found (ls /dev/video*)"
        if kind == "usb":
            src = (_open_usb(int(arg), raw=True) or _open_usb(int(arg))) if thermal else _open_usb(int(arg))
            return (src, spec, label, "") if src else (None, spec, label, f"no picture from /dev/video{arg}")
        if kind == "pi":
            return PiCamSource(int(arg)), spec, label, ""
        if kind == "senxor":
            if not thermal:
                return None, spec, label, "the Thermal-90 can only be used as thermal camera"
            return SenxorSource(), spec, label, ""
        if kind == "url":
            s = find_ip_source(arg)
            if not s:
                return None, spec, label, "unknown network camera"
            src = _open_url(s["url"])
            return (src, spec, label, "") if src else (None, spec, label, "no picture from " + mask_url(s["url"]))
        return None, spec, label, "unknown source"
    except ImportError:
        return None, spec, label, "picamera2 not installed (sudo apt install python3-picamera2)"
    except Exception as e:
        return None, spec, label, str(e)[:160]


def _v4l_name(idx):
    try:
        with open(f"/sys/class/video4linux/video{idx}/name") as f:
            return f.read().strip()
    except OSError:
        return ""


def _is_pi():
    try:
        with open("/proc/device-tree/model") as f:
            return "raspberry" in f.read().lower()
    except OSError:
        return False


def scan_sources(active_id=""):
    """Look for every camera that is connected right now (a few seconds). The camera that is in use cannot be opened a
    second time, so it is listed without probing."""
    if not _SCAN_LOCK.acquire(blocking=False):
        return SOURCES["items"]                             # a scan is already running
    SOURCES["scanning"] = True
    try:
        items, hints = [], []
        idxs = sorted({int(re.sub(r"\D", "", p)) for p in glob.glob("/dev/video*") if re.sub(r"\D", "", p)})
        if not idxs and not sys.platform.startswith("linux"):
            idxs = [0, 1, 2, 3]
        for idx in idxs:
            name = _v4l_name(idx)
            if any(b in name.lower() for b in V4L_SKIP):
                continue
            sid = f"usb:{idx}"
            entry = {"id": sid, "kind": "usb", "name": "USB camera: " + (name or f"video{idx}"),
                     "detail": f"/dev/video{idx}", "available": True}
            if sid == active_id:
                entry["detail"] += " · in use"
            else:
                src = _open_usb(idx) or _open_usb(idx, raw=True)     # thermal cameras do not like the forced format
                if src is None:
                    continue                                # metadata node or camera that is busy / not working
                entry["detail"] += f" · {src.size[0]}x{src.size[1]}"; src.release()
            items.append(entry)
        try:
            from picamera2 import Picamera2
            for n, info in enumerate(Picamera2.global_camera_info()):
                if "usb" in str(info.get("Id", "")).lower():
                    continue                                # USB cameras were found above
                num = int(info.get("Num", n))
                items.append({"id": f"pi:{num}", "kind": "pi", "name": "Raspberry Pi camera: " + str(info.get("Model", "camera")),
                              "detail": f"CSI port {num}", "available": True})
        except ImportError:
            if _is_pi():
                hints.append("Raspberry Pi cameras need picamera2:  sudo apt install python3-picamera2  "
                             "(in a virtual environment create it with --system-site-packages)")
        except Exception as e:
            hints.append(f"Pi camera scan failed: {e}")
        SOURCES.update(items=items, hints=hints, time=time.time())
        log_event("sys", f"Camera scan: {len(items)} camera(s) found")
        return items
    finally:
        SOURCES["scanning"] = False
        _SCAN_LOCK.release()


def list_sources():
    """Everything the user can pick: automatic + scanned cameras + saved network cameras."""
    items = [{"id": "auto", "kind": "auto", "name": "Automatic (first working USB camera)", "detail": "", "available": None}]
    items += [dict(i) for i in SOURCES["items"] if i["kind"] != "url"]
    items += [{"id": "url:" + s["id"], "kind": "url", "name": s["name"], "detail": mask_url(s["url"]), "available": None}
              for s in CFG["ip_sources"]]
    ids = {i["id"] for i in items}
    act = STATE["source_id"]
    if act and act not in ids:                              # the running camera is always in the list
        items.insert(1, {"id": act, "kind": act.split(":")[0], "name": STATE["source_label"], "detail": "in use", "available": True})
    return items


def source_info():
    return {"items": list_sources(), "selected": CFG["source"], "active": STATE["source_id"], "label": STATE["source_label"],
            "status": STATE["source_status"], "res": STATE["source_res"], "scanning": SOURCES["scanning"],
            "scanned": SOURCES["time"], "hints": list(SOURCES["hints"])}


def source_select(watch, sid):
    if not isinstance(sid, str) or not SRC_RE.match(sid):
        return False, "unknown source"
    if sid.startswith("url:") and not find_ip_source(sid[4:]):
        return False, "unknown network camera"
    watch.request_source(sid)
    return True, ""


def source_add(name, url):
    """Save a network camera. Returns (ok, error, new id)."""
    url = str(url or "").strip()
    if not _url_ok(url):
        return False, "invalid URL (rtsp:// or http:// expected)", ""
    if len(CFG["ip_sources"]) >= MAX_IP_SOURCES:
        return False, "too many network cameras", ""
    sid = uuid.uuid4().hex[:8]
    name = str(name or "").strip()[:40] or "Network camera"
    CFG["ip_sources"] = CFG["ip_sources"] + [{"id": sid, "name": name, "url": url}]     # re-assign, never mutate (DEFAULTS share the list)
    save_settings(); log_event("sys", f"Network camera added: {name} ({mask_url(url)})")
    return True, "", sid


def source_remove(watch, sid):
    s = find_ip_source(sid) if isinstance(sid, str) else None
    if not s:
        return False, "unknown network camera"
    CFG["ip_sources"] = [x for x in CFG["ip_sources"] if x["id"] != sid]
    save_settings(); log_event("sys", f"Network camera removed: {s['name']}")
    if CFG["source"] == "url:" + sid:
        watch.request_source("auto")
    return True, ""


