#@ MoveEye – Teil 639zzzzk_blinki_y_cloud: «Blinki fragen» – Cloud-Schalter (Stufe 2): Formate «OpenAI-kompatibel» und «Anthropic Messages», Schlüssel nur vom Administrator, geheim wie das Telegram-Token, Bilder nur mit Einzel-OK, ohne Netz zurück auf offline. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026, Stufe 2): Blinki darf statt des Modells auf dem Gerät einen Cloud-Dienst fragen.
#  Formate    generisch, kein fester Anbieter: «OpenAI-kompatibel» (POST <Adresse>/chat/completions, Authorization: Bearer;
#             passt auch für eigene Server wie llama.cpp / vLLM / Ollama) und «Anthropic Messages» (POST <Adresse>/v1/messages,
#             x-api-key, anthropic-version 2023-06-01). Adresse und Modellname gibt der Administrator ein - nichts Geratenes.
#  Schlüssel  CFG blinki_cloud_key: nur der Administrator setzt ihn (USER_SETTINGS_DENY, APPKEY_DENY_KEYS, nicht im
#             Bedienermodus); er geht nie zurück an eine Seite (nur «gesetzt»), steht nie im Protokoll und nie in einer Antwort
#             (Fehlermeldungen werden geschwärzt), im Diagnose-Paket «***» (Name enthält «key», 300 _SECRET_RE).
#             Adresse nur https:// (http:// nur zu einem Gerät im eigenen Netz / localhost), ohne Benutzer:Passwort@.
#  Bilder     nur in «🦌 Naturführer» und nur, wenn die Seite für genau diese Frage «image_ok» schickt (Häkchen + Rückfrage, danach
#             wieder aus). Offline gehen nie Bilder weg.
#  Ohne Netz  bricht die Verbindung ab (kein Netz, Zeitüberschreitung) und ist das Modell auf dem Gerät da: dieselbe Frage offline.
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Besitzer / Koordinator 15.11.2026: Hauptdatei klein): werkzeuge/bauen.py
# legt es in die Zusatz-ZIP, beim Start läuft es hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es
# «Blinki fragen» nicht - es gehört nicht zu Start, Schutz oder Alarm. Die ZIP ist über ZD_SHA256 (Teil 012) mit signiert.
_BK_SECRET_KEYS = ("blinki_cloud_on", "blinki_cloud_fmt", "blinki_cloud_url", "blinki_cloud_model", "blinki_cloud_key")
USER_SETTINGS_DENY.update(_BK_SECRET_KEYS); APPKEY_DENY_KEYS.update(_BK_SECRET_KEYS)     # also without the zip: only the administrator
BLINKI_CLOUD_PY = r'''BLINKI_CLOUD_DEF = {"blinki_cloud_on": False, "blinki_cloud_fmt": "openai", "blinki_cloud_url": "", "blinki_cloud_model": "", "blinki_cloud_key": ""}
for _k, _v in BLINKI_CLOUD_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)
    if "FACTORY_CFG" in globals():
        FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update(BLINKI_CLOUD_DEF)
APPKEY_DENY_KEYS.update(BLINKI_CLOUD_DEF)
BLINKI_CLOUD_FMTS = (("openai", "OpenAI-compatible"), ("anthropic", "Anthropic Messages"))
BLINKI_IMAGE_MODES = ("natur",)


def blinki_cloud_url_ok(u):
    """(ok, url or English reason): https://host[:port][/path]; http only to this network / localhost; never user:password@"""
    from urllib.parse import urlsplit
    import ipaddress as _ip
    u = str(u or "").strip().rstrip("/")
    if not u:
        return True, ""
    if len(u) > 200 or re.search(r"[\s\x00-\x1f]", u):
        return False, "invalid address"
    try:
        p = urlsplit(u)
        host, _port = p.hostname or "", p.port
    except ValueError:
        return False, "invalid address"
    if p.scheme not in ("https", "http") or not host or "@" in p.netloc or p.query or p.fragment:
        return False, "invalid address"
    if p.scheme == "http":
        try:
            a = _ip.ip_address(host)
            if not (a.is_private or a.is_loopback):
                raise ValueError
        except ValueError:
            if host != "localhost" and not host.endswith(".local"):
                return False, "only https:// (http:// only inside your own network)"
    return True, u


def _bk_cfg_url(v):
    return blinki_cloud_url_ok(v)


def _bk_cfg_model(v):
    v = str(v or "").strip()
    return (True, v) if re.fullmatch(r"[A-Za-z0-9._:/@+\-]{0,80}", v) else (False, "invalid value")


def _bk_cfg_key(v):
    v = str(v or "").strip()
    return (True, v) if not v or re.fullmatch(r"[\x21-\x7e]{8,400}", v) else (False, "invalid value")


def _bk_cfg_fmt(v):
    return (True, v) if v in dict(BLINKI_CLOUD_FMTS) else (False, "invalid value")


def _bk_cfg_on(v):
    on = v is True or str(v).lower() in ("1", "true", "on")
    if on and not blinki_cloud_ready(True):
        return False, "first the address, the model and the key of the cloud service"
    return True, on


BLINKI_SET.update({"blinki_cloud_on": _bk_cfg_on, "blinki_cloud_fmt": _bk_cfg_fmt, "blinki_cloud_url": _bk_cfg_url, "blinki_cloud_model": _bk_cfg_model,
                   "blinki_cloud_key": _bk_cfg_key})


def blinki_cloud_ready(ignore_switch=False):
    return (ignore_switch or bool(CFG.get("blinki_cloud_on"))) and bool(CFG.get("blinki_cloud_url")) and bool(CFG.get("blinki_cloud_model")) \
        and bool(CFG.get("blinki_cloud_key")) and blinki_cloud_url_ok(CFG.get("blinki_cloud_url"))[0]


def blinki_cloud_state():
    """what a page may know - never the key"""
    from urllib.parse import urlsplit
    u = str(CFG.get("blinki_cloud_url") or "")
    try:
        host = urlsplit(u).hostname or ""
    except ValueError:
        host = ""
    return {"on": blinki_cloud_ready(), "switch": bool(CFG.get("blinki_cloud_on")), "fmt": CFG.get("blinki_cloud_fmt") or "openai", "url": u,
            "model": CFG.get("blinki_cloud_model") or "", "key_set": bool(CFG.get("blinki_cloud_key")), "name": host,
            "fmts": [{"v": k, "label": n} for k, n in BLINKI_CLOUD_FMTS], "images": list(BLINKI_IMAGE_MODES)}


def blinki_scrub(t):
    """a text that could hold the key (answers of a server): the key never leaves"""
    t = str(t or "")
    k = str(CFG.get("blinki_cloud_key") or "")
    if len(k) >= 8:
        t = t.replace(k, "•••")
    return re.sub(r"(?i)(bearer\s+|x-api-key[\"':\s]+|sk-[a-z0-9_\-]{4})[A-Za-z0-9_\-\.]{6,}", r"\1•••", t)


_blinki_state_cloud = blinki_state


# wraps: blinki_state
def blinki_state():                                             # + 639zzzzk_blinki_y_cloud: the cloud (without the key)
    st = _blinki_state_cloud()
    st["cloud"] = blinki_cloud_state()
    return st


_blinki_engine_for_cloud = blinki_engine_for


# wraps: blinki_engine_for
def blinki_engine_for(mode):                                    # + 639zzzzk_blinki_y_cloud
    return "cloud" if blinki_cloud_ready() else _blinki_engine_for_cloud(mode)


def blinki_cloud_image():
    """the newest clean picture of the head camera as JPEG (at most 768 px) - only after the OK of the user"""
    w = WATCH_REF.get("w")
    fr = getattr(w, "frame_raw", None) if w is not None else None
    if fr is None:
        fr = getattr(w, "frame_out", None) if w is not None else None
    if fr is None:
        return None
    h_, w_ = fr.shape[:2]
    k = min(1.0, 768.0 / max(h_, w_))
    if k < 1.0:
        fr = cv2.resize(fr, (int(w_ * k), int(h_ * k)))
    ok_, buf = cv2.imencode(".jpg", fr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    import base64 as _b64
    return _b64.b64encode(buf.tobytes()).decode() if ok_ else None


def blinki_cloud_call(j):
    """one question to the cloud service (stream); raises like _blinki_stream"""
    from urllib.parse import urlsplit
    u = urlsplit(str(CFG.get("blinki_cloud_url") or ""))
    fmt, key, model = CFG.get("blinki_cloud_fmt") or "openai", str(CFG.get("blinki_cloud_key") or ""), str(CFG.get("blinki_cloud_model") or "")
    tls = u.scheme == "https"
    port = u.port or (443 if tls else 80)
    base = (u.path or "").rstrip("/")
    msgs = [dict(m) for m in j["messages"]]
    img = j.get("image")
    extra = {"model": model, "top_p": None, "cache_prompt": None}
    if fmt == "anthropic":
        system = "\n\n".join(m["content"] for m in msgs if m["role"] == "system")
        msgs = [m for m in msgs if m["role"] != "system"]
        if img:
            msgs[-1]["content"] = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img}},
                                   {"type": "text", "text": msgs[-1]["content"]}]
        extra["system"] = system
        path = base + "/v1/messages" if not base.endswith("/v1") else base + "/messages"
        hdr = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    else:
        if img:
            msgs[-1]["content"] = [{"type": "text", "text": msgs[-1]["content"]}, {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + img}}]
        path = base + "/chat/completions"
        hdr = {"Authorization": "Bearer " + key}
    _blinki_stream(j, u.hostname, port, path or "/", hdr, msgs, tls=tls, body_extra=extra)


_blinki_answer_cloud = blinki_answer


# wraps: blinki_answer
def blinki_answer(j):                                           # + 639zzzzk_blinki_y_cloud: the cloud first when it is switched on
    if j.get("engine") != "cloud":
        return _blinki_answer_cloud(j)
    j["state"] = "think"
    try:
        blinki_cloud_call(j)
    except (OSError, _bhttp.HTTPException) as e:                # no network, time out: the same question offline
        if blinki_offline_ok() and not j["text"] and not j["stop"]:
            j.update(engine="offline", image=None)
            log_event("sys", "Blinki: cloud not reachable - offline instead")
            return _blinki_answer_cloud(j)
        raise RuntimeError("the cloud service does not answer: " + blinki_scrub(str(e))[:120])
    except RuntimeError as e:
        raise RuntimeError(blinki_scrub(str(e))[:200])
    finally:
        j["image"] = None                                        # the picture is never kept


_blinki_ask_cloud = blinki_ask


# wraps: blinki_ask
def blinki_ask(mode, q, lang=None, prev=None, who="web", client="", extra=None):   # + 639zzzzk_blinki_y_cloud: a picture only with its own OK
    extra = dict(extra or {})
    extra.pop("image", None)
    if extra.pop("image_ok", None) is True and mode in BLINKI_IMAGE_MODES and blinki_cloud_ready():
        extra["image"] = blinki_cloud_image()
        extra["sent_image"] = bool(extra["image"])
    j, err = _blinki_ask_cloud(mode, q, lang, prev, who, client, extra)
    if j is not None and extra.get("sent_image"):
        log_event("sys", f"Blinki: one camera picture sent to the cloud (OK by {who})")
    return j, err
'''
zd_exec(BLINKI_CLOUD_PY, '639zzzzk_blinki_y_cloud.py')
