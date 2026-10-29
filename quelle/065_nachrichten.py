#@ MoveEye – Teil 065: Nachrichten – alle Push-Nachrichten (ntfy / Telegram / Webhook) in einer Liste, auch vom ntfy-Server. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13 (Wunsch Daniel): ein eigenes Menü «Nachrichten» (Reiter Verlauf): was MoveEye an das Handy geschickt hat – mit Bild,
# Zeit, Art und ob es angekommen ist (gesendet / fehlgeschlagen / Test-Postfach). Zusätzlich: die Nachrichten des ntfy-Themas
# direkt vom ntfy-Server holen (auch die von anderen Geräten im selben Thema). Die Adresse des Themas bleibt auf dem Pi –
# die Webseite bekommt nur die Nachrichten, nie die Adresse.
# ----------------------------------------------------------------------------
MSGLOG = {"lock": threading.Lock(), "items": None}
MSGLOG_MAX = 300
MSGLOG_IMG_MAX = 80


def _msglog_dir():
    return os.path.join(DATA_DIR, "nachrichten")


def _msglog_load():
    if MSGLOG["items"] is not None:
        return MSGLOG["items"]
    items = []
    try:
        with open(os.path.join(_msglog_dir(), "index.jsonl"), encoding="utf-8") as f:
            for ln in f:
                try:
                    items.append(json.loads(ln))
                except ValueError:
                    pass
    except OSError:
        pass
    MSGLOG["items"] = items[-MSGLOG_MAX:]
    return MSGLOG["items"]


def msglog_add(title, text, ev, jpg=None, status="sent", where=""):
    """one message that was sent (or tried, or went to the test inbox) - kept with a small picture"""
    try:
        d = _msglog_dir(); os.makedirs(d, exist_ok=True)
        it = {"id": "%d" % int(time.time() * 1000), "t": time.time(), "title": str(title)[:200], "text": str(text)[:600],
              "ev": str(ev or "info"), "status": status, "where": str(where)[:60]}
        if jpg:
            try:
                img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    h, w = img.shape[:2]
                    if w > 480:
                        img = cv2.resize(img, (480, int(h * 480 / w)), interpolation=cv2.INTER_AREA)
                    ok_, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 72])
                    if ok_:
                        with open(os.path.join(d, it["id"] + ".jpg"), "wb") as f:
                            f.write(buf.tobytes())
                        it["img"] = True
            except Exception:
                pass
        with MSGLOG["lock"]:
            items = _msglog_load()
            items.append(it)
            del items[:-MSGLOG_MAX]
            with open(os.path.join(d, "index.jsonl.tmp"), "w", encoding="utf-8") as f:
                for x in items:
                    f.write(json.dumps(x, ensure_ascii=False) + "\n")
            os.replace(os.path.join(d, "index.jsonl.tmp"), os.path.join(d, "index.jsonl"))
            pics = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
            for x in pics[:-MSGLOG_IMG_MAX]:
                try:
                    os.remove(os.path.join(d, x))
                except OSError:
                    pass
    except Exception as e:
        log_event("sys", f"Message list: {e}"[:160])


def msglog_list(limit=200):
    with MSGLOG["lock"]:
        items = list(_msglog_load())[-limit:]
    d = _msglog_dir()
    out = []
    for x in reversed(items):
        y = dict(x)
        y["img"] = bool(x.get("img")) and os.path.exists(os.path.join(d, x["id"] + ".jpg"))
        out.append(y)
    return out


def msglog_img(mid):
    if not re.fullmatch(r"\d{10,16}", str(mid)):
        return None
    p = os.path.join(_msglog_dir(), mid + ".jpg")
    return p if os.path.exists(p) else None


def msglog_clear():
    with MSGLOG["lock"]:
        MSGLOG["items"] = []
        d = _msglog_dir()
        try:
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
        except OSError:
            pass
    log_event("web", "Message list cleared")


def ntfy_server_messages(since="24h"):
    """the messages of the ntfy topic, straight from the ntfy server (also the ones of other devices in the same topic).
    Returns (list, error). The address of the topic never leaves the Pi."""
    if CFG.get("notify_type") != "ntfy" or not str(CFG.get("notify_url") or "").strip():
        return [], "ntfy is not set up (Settings → Push)"
    if not re.fullmatch(r"\d{1,3}[mhd]|all", since):
        since = "24h"
    url = CFG["notify_url"].strip().rstrip("/") + "/json?poll=1&since=" + since
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MoveEye"})
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read(4_000_000).decode("utf-8", "replace")
    except Exception as e:
        return [], (str(e).replace(CFG["notify_url"].strip(), _url_host(CFG["notify_url"])))[:160]
    out = []
    for ln in raw.splitlines():
        try:
            m = json.loads(ln)
        except ValueError:
            continue
        if m.get("event") != "message":
            continue
        att = m.get("attachment") or {}
        tags = m.get("tags") or []
        ev = "person" if "warning" in tags else ("tamper" if "rotating_light" in tags else ("warm" if "fire" in tags else
             ("noise" if "loud_sound" in tags else ("prealarm" if "eyes" in tags else "info"))))
        aurl = str(att.get("url") or "")
        out.append({"id": str(m.get("id", "")), "t": float(m.get("time") or 0), "title": str(m.get("title") or "")[:200],
                    "text": str(m.get("message") or "")[:600], "ev": ev, "status": "server", "where": "ntfy",
                    "img_url": aurl if aurl.startswith("https://") and str(att.get("type", "")).startswith("image/") else "",
                    "prio": int(m.get("priority") or 3)})
    out.sort(key=lambda x: -x["t"])
    return out[:300], ""
