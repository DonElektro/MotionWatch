#@ Motion Watch – Teil 260: mehrere Motion-Watch-Geräte. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Several devices: one Motion Watch shows the others (Cameras page): picture, armed / alarm, battery, last event; arm or
#   disarm one or all. The other devices are reached over the network (home network or Tailscale) with their own password.
#   Passwords are only ever sent to the address of that device.
# ----------------------------------------------------------------------------
FLEET = {"state": {}, "seen": 0.0, "snaps": {}, "lock": threading.Lock()}
_FLEET_URL = re.compile(r"^https?://[A-Za-z0-9.\-\[\]:]{1,120}(:\d{1,5})?/?$")


def device_uid():
    """Short id of this Pi (from /etc/machine-id): the same device over two addresses is shown once."""
    if not FLEET.get("uid"):
        try:
            with open("/etc/machine-id") as f:
                raw = f.read().strip()
        except OSError:
            raw = str(uuid.getnode())
        FLEET["uid"] = hashlib.sha256(("motionwatch|" + raw).encode()).hexdigest()[:12]
    return FLEET["uid"]


def fleet_hello():
    """Small status of this device for the overview of another one."""
    imp = [e for e in STATE["events"] if e.get("imp")][:1]
    b = STATE.get("battery") or {}
    return {"app": "Motion Watch", "uid": device_uid(), "name": CFG["device_name"] or "Motion Watch", "version": APP_VERSION, "arm": STATE["arm_state"],
            "persons": STATE["persons"], "recording": bool(STATE.get("recording")), "fps": STATE.get("fps"),
            "battery": b.get("pct"), "mains": (not b.get("on_battery")) if b.get("src") == "ups" else None,
            "temp": STATE.get("cpu_temp"), "last": (imp[0].get("t", "")[:5] + " " + imp[0].get("text", ""))[:120] if imp else "",
            "tamper": (STATE.get("tamper") or {}).get("last", ""), "time": datetime.now().strftime("%H:%M:%S")}


def _fleet_req(dev, path, data=None, timeout=4.0):
    import base64
    url = dev["url"].rstrip("/") + path
    h = {"Content-Type": "application/json"} if data is not None else {}
    if dev.get("pw"):
        h["Authorization"] = "Basic " + base64.b64encode(("mw:" + dev["pw"]).encode()).decode()
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=h, method="POST" if data is not None else "GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))      # devices are in the own network: no proxy
    with opener.open(req, timeout=timeout) as r:
        return r.read(4 * 1024 * 1024), r.headers.get("Content-Type", "")


def fleet_poll_one(dev):
    try:
        raw, _ct = _fleet_req(dev, "/api/fleet_state")
        st = json.loads(raw.decode()); st["ok"] = True; st["err"] = ""
        if not dev.get("name") and st.get("name") and dev in CFG["fleet"]:
            dev["name"] = str(st["name"])[:40]; save_settings()
    except urllib.error.HTTPError as e:
        st = {"ok": False, "err": "password wrong" if e.code == 401 else f"HTTP {e.code}"}
    except Exception as e:
        st = {"ok": False, "err": "not reachable"}
    st["checked"] = time.time()
    with FLEET["lock"]:
        old = FLEET["state"].get(dev["id"], {})
        if old.get("ok") and not st["ok"] and is_armed():
            log_event("sys", f"Device {dev.get('name') or dev['url']} not reachable any more")
        FLEET["state"][dev["id"]] = st
    return st


def fleet_loop():
    while True:
        time.sleep(1.0)
        devs = list(CFG["fleet"])
        if not devs:
            continue
        busy = time.time() - FLEET["seen"] < 60
        for d in devs:
            last = FLEET["state"].get(d["id"], {}).get("checked", 0)
            if time.time() - last > (4 if busy else 60):
                fleet_poll_one(d)


def fleet_add(url, name="", pw=""):
    url = str(url or "").strip()
    if not url.startswith("http"):
        url = "http://" + url
    if re.match(r"^https?://[^/:]+$", url):
        url += f":{CFG['web_port']}"
    if not _FLEET_URL.match(url):
        return False, "invalid address (e.g. http://192.168.1.20:5000)", None
    if any(d["url"].rstrip("/") == url.rstrip("/") for d in CFG["fleet"]):
        return False, "this device is in the list already", None
    if len(CFG["fleet"]) >= 12:
        return False, "at most 12 devices", None
    dev = {"id": uuid.uuid4().hex[:8], "url": url.rstrip("/"), "name": str(name or "")[:40], "pw": str(pw or "")[:64]}
    st = fleet_poll_one(dev)
    if st.get("uid") == device_uid():
        FLEET["state"].pop(dev["id"], None)
        return False, "this is this device itself", None
    if st.get("ok") and not dev["name"]:
        dev["name"] = str(st.get("name") or "")[:40]
    CFG["fleet"] = CFG["fleet"] + [dev]; save_settings()
    log_event("sys", f"Device added to the overview: {dev['name'] or url}")
    return True, "", dev["id"]


def fleet_scan():
    """Look for other Motion Watch devices: own network (x.y.z.1-254, same port) + Tailscale devices."""
    from concurrent.futures import ThreadPoolExecutor
    ips = set()
    ip = wifi_ip()
    if ip and ip.count(".") == 3:
        pre = ip.rsplit(".", 1)[0]
        ips |= {f"{pre}.{i}" for i in range(1, 255)} - {ip}
    try:
        ips |= set((tailscale_status().get("peers") or {}).keys())
    except Exception:
        pass
    known = {d["url"] for d in CFG["fleet"]}
    found = []

    def probe(a):
        if ":" in a:
            return None
        url = f"http://{a}:{CFG['web_port']}"
        if url in known:
            return None
        try:
            raw, _ = _fleet_req({"url": url}, "/api/fleet_state", timeout=0.8)
            j = json.loads(raw.decode())
            return {"url": url, "name": j.get("name", ""), "needs_pw": False, "uid": j.get("uid", "")} if j.get("app") == "Motion Watch" else None
        except urllib.error.HTTPError as e:
            if e.code == 401 and "Motion Watch" in str(e.headers.get("WWW-Authenticate", "")):
                return {"url": url, "name": "", "needs_pw": True}
        except Exception:
            pass
        return None
    have = {device_uid()} | {st.get("uid") for st in FLEET["state"].values() if st.get("uid")}
    with ThreadPoolExecutor(64) as ex:
        for r in ex.map(probe, sorted(ips)):
            if r and (not r.get("uid") or r["uid"] not in have):
                found.append(r)
                if r.get("uid"):
                    have.add(r["uid"])
    return found


def fleet_snap(dev_id):
    dev = next((d for d in CFG["fleet"] if d["id"] == dev_id), None)
    if dev is None:
        return None
    c = FLEET["snaps"].get(dev_id)
    if c and time.time() - c[0] < 2.0:
        return c[1]
    try:
        raw, _ct = _fleet_req(dev, "/snapshot.jpg", timeout=5)
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return None
        h, w = img.shape[:2]
        if w > 640:
            img = cv2.resize(img, (640, int(h * 640 / w)), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        data = buf.tobytes() if ok else None
    except Exception:
        data = None
    FLEET["snaps"][dev_id] = (time.time(), data)
    return data

