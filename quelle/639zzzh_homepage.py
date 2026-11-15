#@ MoveEye – Teil 639zzzh: «🌐 Homepage» (Mehr → Homepage, nur der Admin): die öffentlichen Seiten des Besitzers auf seinen Webspace hochladen – Startseite, Handy-Funkgerät (Funk/), Simulator im Browser (Sim/, Release-Asset sim-web.zip, signiert) und die Test-Seite; nur Geändertes, im Hintergrund, nie während eines Alarms; danach jede öffentliche Adresse prüfen (Status, Grösse, Typ, Umleitungen, Content-Security-Policy). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Auftrag des Besitzers (14.11.2026): MoveEye lädt seine öffentlichen Seiten selbst auf seinen Webspace, damit er es nicht
# von Hand machen muss. Schnittstelle des Webspace (Bildschirmfoto des Besitzers), Grundadresse ab Werk https://kevlaschef.com:
#   * Hochladen: POST <Grund>/api/moveeye/upload?path=<Pfad>, «Authorization: Bearer <Schlüssel>» und «X-KV: 1», Inhalt = die
#     Bytes der Datei. Höchstens 100 MB pro Datei, 500 MB zusammen. Öffentlich: <Grund>/moveeye/<Pfad>.
#   * Liste: GET <Grund>/api/moveeye/files (Authorization). Löschen: DELETE …/files?path=<Pfad> (Authorization, X-KV: 1).
#   * Beobachtet: der Server macht aus jedem Punkt im Dateinamen ausser dem letzten «_» («index.audio.worklet.js» →
#     «index_audio_worklet.js»). Darum hat jede Datei, die MoveEye hochlädt, genau einen Punkt (sim-web.zip ist schon so
#     gebaut: werkzeuge/sim_web_paket.py); Ordner unterscheiden Gross / Klein – die Ordner des Besitzers heissen «Funk», «Sim».
# Inhalt (hp_items): index.html (Startseite, 5 Sprachen), Funk/ = die 6 Dateien der PWA (dieselben Bytes wie funk/ im
# Repository, werkzeuge/funk_pwa.py), Sim/ = die 8 Dateien aus dem Release-Asset «sim-web.zip» (nur mit der signierten Prüfsumme
# aus versions.json «sim.anhang.web», Teil 300 / 390 – genau wie die anderen Sim-Pakete), Sim/test.html (Test-Seite).
# Sicherheit:
#   * Schlüssel (hp_key) wie die anderen Geheimnisse in den Einstellungen (Datei nur für MoveEye lesbar), nur der Admin setzt,
#     ersetzt oder löscht ihn, nie wieder angezeigt; nie in Protokoll, Zustand (/api/state, /api/homepage), Push, Schema
#     (kein TEXTS-Eintrag) und nicht für «Einstellungen»-Benutzer, App-Schlüssel oder den Bedienermodus. Gesetzt nur über die
#     sichere Seite. Fehlertexte des Servers werden gekürzt und ohne den Schlüssel gezeigt.
#   * Der Schlüssel geht nur an die eingestellte https-Adresse; Umleitungen werden beim Hochladen NIE befolgt (http.client statt
#     urllib: urllib schickt die Kopfzeile Authorization nach einer Umleitung mit). Eine neue Grundadresse löscht den Schlüssel
#     (er gehört zu genau diesem Webspace).
#   * Gelöscht werden nur Dateien, die MoveEye selbst hochgeladen hat und die es nicht mehr gibt (eigene Liste), sonst nichts.
# Ablauf: ein Faden mit tiefer Priorität, «3/15 · 41 MB», wartet bei einem Alarm (rotes Blinken, Person, Aufnahme, Licht nach
# Alarm, GPS-Diebstahl) und bricht eine laufende Datei dann ab (später neu), bis zu 3 Versuche bei Netzfehlern / 5xx; falscher
# Schlüssel (401/403), voller Platz (507 / 413 mit «quota») und zu grosse Dateien als klare Meldung. «nach jedem Update
# automatisch» (ab Werk an): alle 15 Min. vergleicht hp_auto_tick den Inhalt mit dem zuletzt veröffentlichten (hp_content_id) –
# nur wenn sich etwas geändert hat (neue MoveEye mit neuer Funk-Seite, neuer signierter Browser-Simulator), wird hochgeladen.
# Prüfung (hp_check): jede öffentliche Adresse ohne Schlüssel abrufen, Umleitungen selbst verfolgen (höchstens 5, andere
# Herkunft wird gemeldet), Status, Grösse, Content-Type, Inhalt (kleine Dateien: SHA-256), X-Content-Type-Options, Cross-Origin-*
# und die Content-Security-Policy: «connect-src blockiert fetch()» (das «Load failed» am iPhone), «script-src ohne
# 'wasm-unsafe-eval'», «ohne 'unsafe-inline'» (Startskript von Godot).
# Tests: werkzeuge/homepage_test.py (falscher Webspace auf localhost mit derselben Schnittstelle).
# ----------------------------------------------------------------------------
_HP_CFG = {"hp_key": "", "hp_base": "https://kevlaschef.com", "hp_auto": True}
for _k, _v in _HP_CFG.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update(_HP_CFG)
APPKEY_DENY_KEYS.update(_HP_CFG)
LOCK_DENY_KEYS.update(_HP_CFG)
APPKEY_DENY_PATHS.update({"/api/homepage", "/homepage"})
LOCK_DENY_PATHS.add("/api/homepage")

HP_MAX_FILE = 100 * 1024 * 1024
HP_MAX_TOTAL = 500 * 1024 * 1024
HP_TRIES = 3
HP_RETRY = [5.0, 30.0]                                     # s between the tries (tests: shorter)
HP_TICK = 900.0                                            # s: the automatic comparison
HP_TEST_HTTP = False                                       # tests only: http://127.0.0.1 instead of https
HP_SIM_NAMES = ("index.html", "index.js", "index.wasm", "index.pck", "index_audio_worklet.js", "index.png", "index_icon.png",
                "index_apple-touch-icon.png")
_HP_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}\.[a-z0-9]{1,12}$")
HP = {"lock": threading.Lock(), "busy": "", "prog": {}, "cancel": False, "err": "", "msg": "", "run": False, "wait": False}
_HP_TYPES = {"html": ("text/html",), "js": ("text/javascript", "application/javascript", "application/x-javascript"),
             "wasm": ("application/wasm",), "png": ("image/png",), "webmanifest": ("application/manifest+json", "application/json")}


class HpErr(Exception):
    def __init__(self, kind, detail=""):
        Exception.__init__(self, kind)
        self.kind, self.detail = kind, str(detail)


def _hp_file():
    return os.path.join(DATA_DIR, "homepage.json")


def hp_state():
    try:
        with open(_hp_file(), encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            return d
    except (OSError, ValueError):
        pass
    return {}


def hp_save(st):
    try:
        tmp = _hp_file() + ".neu"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f)
        os.replace(tmp, _hp_file())
    except OSError:
        pass


def _hp_clean(t):
    """a text from outside: short, one line, never the key"""
    t = re.sub(r"\s+", " ", str(t or ""))[:160]
    k = str(CFG.get("hp_key") or "")
    return t.replace(k, "•••") if len(k) >= 4 else t


def hp_base_ok(u):
    u = str(u or "").strip().rstrip("/")
    if re.fullmatch(r"https://[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}\.)+[A-Za-z]{2,63}(?::\d{1,5})?", u):
        return u
    if HP_TEST_HTTP and re.fullmatch(r"http://127\.0\.0\.1:\d{1,5}", u):
        return u
    return ""


def _hp_conn(url, timeout=60):
    """(connection, path?query) - only https (tests: http to 127.0.0.1)"""
    import http.client
    from urllib.parse import urlsplit
    s = urlsplit(url)
    if s.scheme == "https":
        import ssl
        c = http.client.HTTPSConnection(s.hostname, s.port or 443, timeout=timeout, context=ssl.create_default_context())
    elif s.scheme == "http" and HP_TEST_HTTP and s.hostname == "127.0.0.1":
        c = http.client.HTTPConnection(s.hostname, s.port or 80, timeout=timeout)
    else:
        raise HpErr("url", url[:80])
    return c, (s.path or "/") + ("?" + s.query if s.query else "")


def _hp_api(method, path, data=None):
    """one call of the web space API with the key; never follows a redirect -> (status, body ≤ 1 MB)"""
    base, key = hp_base_ok(CFG.get("hp_base")), str(CFG.get("hp_key") or "")
    if not base:
        raise HpErr("url")
    if not key:
        raise HpErr("nokey")
    try:
        c, p = _hp_conn(base + path, 30)
        h = {"Authorization": "Bearer " + key, "User-Agent": "MoveEye/" + APP_VERSION}
        if method != "GET":
            h["X-KV"] = "1"
        c.request(method, p, body=data, headers=h)
        r = c.getresponse()
        b = r.read(1 << 20)
        c.close()
    except HpErr:
        raise
    except Exception as e:
        raise HpErr("net", e.__class__.__name__)
    _hp_status(r.status, b)
    return r.status, b


def _hp_status(code, b=b""):
    if 300 <= code < 400:
        raise HpErr("redirect", code)
    if code in (401, 403):
        raise HpErr("key", code)
    t = b.decode("utf-8", "replace").lower() if isinstance(b, bytes) else ""
    if code == 507 or (code in (413, 400, 409) and re.search(r"quota|space|full|speicher|voll", t)):
        raise HpErr("quota", code)
    if code == 413:
        raise HpErr("large", code)
    if code >= 500:
        raise HpErr("http5", code)
    if code >= 400:
        raise HpErr("http", f"{code} {_hp_clean(t)[:60]}")


def _hp_norm(p):
    p = str(p or "").lstrip("/")
    return p[8:] if p.startswith("moveeye/") else p


def hp_list():
    """the files on the web space -> ({path: {"size": n|None, "sha": hex|None}}, used bytes)"""
    _c, b = _hp_api("GET", "/api/moveeye/files")
    try:
        d = json.loads(b.decode("utf-8"))
    except ValueError:
        raise HpErr("http", "list: no JSON")
    rows = d if isinstance(d, list) else next((d[k] for k in ("files", "items", "list") if isinstance(d.get(k), list)), []) if isinstance(d, dict) else []
    out = {}
    for e in rows[:5000]:
        e = {"path": e} if isinstance(e, str) else e
        if not isinstance(e, dict):
            continue
        p = _hp_norm(e.get("path") or e.get("name") or e.get("key"))
        sz, sh = e.get("size"), str(e.get("sha256") or e.get("sha") or e.get("hash") or "").lower()
        if p:
            out[p] = {"size": sz if isinstance(sz, int) else None, "sha": sh if re.fullmatch(r"[0-9a-f]{64}", sh) else None}
    used = d.get("used") if isinstance(d, dict) and isinstance(d.get("used"), int) else sum(v["size"] or 0 for v in out.values())
    return out, used


# ---- the content -------------------------------------------------------------------------------------------------------------
def hp_funk_files():
    """the 6 files of the PWA «Handy-Funkgerät» - the same bytes as funk/ in the repository (werkzeuge/funk_pwa.py)"""
    import base64
    import hashlib
    html = funk_page("pwa").encode("utf-8")
    ver = hashlib.sha256(html).hexdigest()[:12]
    man = {"name": "Handy-Funkgerät", "short_name": "Funk", "description": "Morse und das eigene Protokoll mit zwei Tönen über ein Handfunkgerät (MoveEye)",
           "lang": "de", "start_url": "./", "scope": "./", "display": "standalone", "background_color": "#111418", "theme_color": "#111418",
           "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}
    out = {"index.html": html, "manifest.webmanifest": (json.dumps(man, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
           "sw.js": HP_FUNK_SW_JS.replace("@VER@", ver).encode("utf-8")}
    try:
        out.update({k: base64.b64decode(v) for k, v in json.loads(HP_FUNK_PNG).items()})
    except (ValueError, TypeError):
        pass                                               # without the data zip: no symbols (the page itself still works)
    return out


def _hp_item(path, data):
    import hashlib
    import io
    return {"path": path, "size": len(data), "sha": hashlib.sha256(data).hexdigest(), "get": lambda d=data: io.BytesIO(d)}


def hp_fixed_items():
    out = [_hp_item("index.html", HP_INDEX_HTML.encode("utf-8"))]
    out += [_hp_item("Funk/" + n, b) for n, b in sorted(hp_funk_files().items())]
    return out + [_hp_item("Sim/test.html", HP_TEST_HTML.encode("utf-8"))]


def hp_sim_check(p):
    """the browser simulator package -> (names, "" or the english reason); same rules as werkzeuge/sim_web_paket.py"""
    import zipfile
    try:
        with zipfile.ZipFile(p) as z:
            inf = z.infolist()
            names = [i.filename for i in inf]
            if len(inf) > 16 or any(not _HP_NAME_RE.match(i.filename) or i.file_size > HP_MAX_FILE for i in inf):
                return [], "a name or a size is not allowed"
            if sum(i.file_size for i in inf) > 400 * 1024 * 1024 or not set(HP_SIM_NAMES[:5]) <= set(names):
                return [], "files missing or too large"
            if b"`${loadPath}_audio_worklet.js`" not in z.read("index.js"):
                return [], "index.js does not load index_audio_worklet.js"
            return names, ""
    except Exception as e:
        return [], "no valid zip (%s)" % e.__class__.__name__


def hp_sim_items(fetch=True):
    """the files of Sim/ from the signed «sim-web.zip» -> (items, None or a note (english key, detail))"""
    import hashlib
    import zipfile
    sim_manifest_load()
    pk = SIM3D_WEB
    if not (pk["size"] and pk["sha256"]):
        return [], ("The browser simulator is not released yet – Sim/ only gets the test page.", "")
    if not sim3d_ready(pk) and fetch:
        HP["busy"] = "fetching the browser simulator"
        sim3d_fetch(pk, SIM3D_WEB_DL)
        while SIM3D_WEB_DL["running"] and not HP["cancel"]:
            time.sleep(0.5)
    if not sim3d_ready(pk):
        return [], ("Browser simulator: download failed", _hp_clean(SIM3D_WEB_DL.get("msg"))) if fetch else None
    p = sim3d_path(pk)
    st = hp_state()
    c = st.get("simsha") if isinstance(st.get("simsha"), dict) else {}
    tag = [pk["sha256"], os.path.getsize(p), int(os.path.getmtime(p))]
    if c.get("tag") != tag:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        if h.hexdigest() != pk["sha256"]:
            return [], ("Browser simulator: package is wrong", "checksum")
        names, why = hp_sim_check(p)
        if why:
            return [], ("Browser simulator: package is wrong", why)
        files = {}
        with zipfile.ZipFile(p) as z:
            for n in names:
                h = hashlib.sha256()
                with z.open(n) as f:
                    for b in iter(lambda: f.read(1 << 20), b""):
                        h.update(b)
                files[n] = [z.getinfo(n).file_size, h.hexdigest()]
        c = {"tag": tag, "files": files}
        st["simsha"] = c
        hp_save(st)

    def opener(n):
        z = zipfile.ZipFile(p)
        f = z.open(n)
        f.close_zip = z
        return f
    return [{"path": "Sim/" + n, "size": v[0], "sha": v[1], "get": lambda n=n: opener(n)} for n, v in sorted(c["files"].items())], None


def hp_content_id():
    """what would be published (without fetching anything): changes with a new Funk page, a new signed browser simulator,
    another address"""
    import hashlib
    sim_manifest_load()
    t = "|".join(it["path"] + ":" + it["sha"] for it in hp_fixed_items()) + "|sim:" + str(SIM3D_WEB.get("sha256") or "")
    return hashlib.sha256((t + "|" + str(CFG.get("hp_base"))).encode("utf-8")).hexdigest()


# ---- the job (one thread, low priority) ------------------------------------------------------------------------------------------
def hp_quiet():
    """False while an alarm is going on (red blinking, a person, a recording, the light after an alarm, GPS theft)"""
    try:
        if LED.get("alarm") or STATE.get("persons") or STATE.get("recording") or GPSMOD.get("alarm_t"):
            return False
        return not (LIGHTS.get("alarm_t") and time.time() - LIGHTS["alarm_t"] < 300)
    except Exception:
        return True


def _hp_wait_quiet():
    while not hp_quiet():
        HP["wait"] = True
        if HP["cancel"]:
            raise HpErr("cancel")
        time.sleep(2)
    HP["wait"] = False


def _hp_upload_once(it):
    base, key = hp_base_ok(CFG.get("hp_base")), str(CFG.get("hp_key") or "")
    from urllib.parse import quote
    c, p = _hp_conn(base + "/api/moveeye/upload?path=" + quote(it["path"], safe="/"), 120)
    f = it["get"]()
    sent = 0
    try:
        c.putrequest("POST", p)
        for k, v in (("Authorization", "Bearer " + key), ("X-KV", "1"), ("Content-Type", "application/octet-stream"),
                     ("Content-Length", str(it["size"])), ("User-Agent", "MoveEye/" + APP_VERSION)):
            c.putheader(k, v)
        c.endheaders()
        for b in iter(lambda: f.read(256 * 1024), b""):
            if HP["cancel"]:
                raise HpErr("cancel")
            if not hp_quiet():
                raise HpErr("alarm")
            c.send(b)
            sent += len(b)
            HP["prog"]["bytes"] = HP["prog"].get("base", 0) + sent
        r = c.getresponse()
        body = r.read(65536)
    except HpErr:
        raise
    except Exception as e:
        raise HpErr("net", e.__class__.__name__)
    finally:
        try:
            f.close(); getattr(f, "close_zip", None) and f.close_zip.close()
        except Exception:
            pass
        c.close()
    _hp_status(r.status, body)
    try:
        got = _hp_norm(json.loads(body.decode("utf-8")).get("path"))
    except Exception:
        got = ""
    return got if got and got != it["path"] else ""


def _hp_put(it):
    n = 0
    while True:
        _hp_wait_quiet()
        try:
            return _hp_upload_once(it)
        except HpErr as e:
            if e.kind == "alarm":
                continue                                    # not counted: the file again after the alarm
            n += 1
            if e.kind not in ("net", "http5") or n >= HP_TRIES:
                raise
            HP["msg"] = "retry"
            time.sleep(HP_RETRY[min(n - 1, len(HP_RETRY) - 1)])


def _hp_ours(p):
    return p == "index.html" or p.startswith(("Funk/", "Sim/"))


def hp_publish(auto=False):
    st = hp_state()
    cid = hp_content_id()
    HP.update(busy="comparing", prog={}, msg="")
    items = hp_fixed_items()
    sim, note = hp_sim_items(True)
    items += sim
    if HP["cancel"]:
        raise HpErr("cancel")
    remote, used = hp_list()
    up = st.get("up") if isinstance(st.get("up"), dict) else {}
    plan = []
    for it in items:
        r, m = remote.get(it["path"]), up.get(it["path"])
        same = r is not None and r["size"] in (None, it["size"]) and (r["sha"] == it["sha"] if r["sha"] else m == [it["size"], it["sha"]])
        if not same:
            plan.append(it)
    for it in plan:
        if it["size"] > HP_MAX_FILE:
            raise HpErr("large", it["path"])
    if used - sum((remote.get(it["path"]) or {}).get("size") or 0 for it in plan) + sum(it["size"] for it in plan) > HP_MAX_TOTAL:
        raise HpErr("quota")
    tot = sum(it["size"] for it in plan)
    HP.update(busy="uploading", prog={"i": 0, "n": len(plan), "bytes": 0, "total": tot, "base": 0})
    ren = []
    for i, it in enumerate(plan):
        HP["prog"].update(i=i + 1, file=it["path"], base=sum(x["size"] for x in plan[:i]))
        got = _hp_put(it)
        if got:
            ren.append(it["path"] + " → " + got)
        up[it["path"]] = [it["size"], it["sha"]]
        st["up"] = up
        hp_save(st)
    paths = {it["path"] for it in items}
    gone = [p for p in list(up) if p not in paths and _hp_ours(p)]
    for p in gone:
        from urllib.parse import quote
        if p in remote:
            _hp_api("DELETE", "/api/moveeye/files?path=" + quote(p, safe="/"))
        up.pop(p, None)
    st.update(up=up, done_id=cid, fail=None, last={"t": int(time.time()), "up": len(plan), "same": len(items) - len(plan), "gone": len(gone),
                                                   "bytes": tot, "note": note, "ren": ren[:5], "auto": bool(auto)})
    hp_save(st)
    log_event("sys", f"Homepage: {len(plan)} files uploaded, {len(items) - len(plan)} unchanged, {len(gone)} deleted" + (" (automatic)" if auto else ""))
    return items


def _hp_job(kind, auto):
    try:
        try:
            os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), 19)     # this thread only (Linux)
        except (AttributeError, OSError):
            pass
        items = hp_publish(auto) if kind == "publish" else None
        HP["busy"] = "checking"
        hp_check(items)
    except HpErr as e:
        HP["err"] = e.kind if e.kind != "cancel" else ""
        HP["msg"] = "cancel" if e.kind == "cancel" else _hp_clean(e.detail)
        if e.kind != "cancel":
            log_event("sys", "Homepage: " + {"key": "upload key wrong", "quota": "web space full", "large": "file too large"}.get(
                e.kind, "stopped") + f" ({e.kind} {_hp_clean(e.detail)})"[:120])
            if kind == "publish":
                st = hp_state()
                st["fail"] = {"id": hp_content_id(), "t": int(time.time())}
                hp_save(st)
    except Exception as e:
        HP.update(err="error", msg=e.__class__.__name__)
        log_event("sys", "Homepage: error " + e.__class__.__name__)
    finally:
        HP.update(busy="", wait=False, prog={})


def hp_start(kind, auto=False):
    with HP["lock"]:
        if HP["busy"]:
            return False
        HP.update(busy="starting", cancel=False, err="", msg="")
    threading.Thread(target=_hp_job, args=(kind, auto), daemon=True, name="homepage").start()
    return True


def hp_auto_tick(now=None):
    """«nach jedem Update automatisch»: only when the content changed since the last publish (and not right after a failure)"""
    now = now or time.time()
    if not (CFG.get("hp_auto") and CFG.get("hp_key") and hp_base_ok(CFG.get("hp_base"))) or HP["busy"] or not hp_quiet():
        return False
    st = hp_state()
    if now - float(st.get("t_man") or 0) > 6 * 3600:
        try:
            src = CFG["update_url"].strip()
            sim_manifest_refresh(src.rsplit("/", 1)[0] + "/" if src.startswith("https://") else SIM3D_BASE, 6 * 3600)
        except Exception:
            pass
        st["t_man"] = int(now)
        hp_save(st)
    cid = hp_content_id()
    f = st.get("fail") or {}
    if cid == st.get("done_id") or (f.get("id") == cid and now - float(f.get("t") or 0) < 6 * 3600):
        return False
    return hp_start("publish", auto=True)


def _hp_worker():
    time.sleep(180)
    while True:
        try:
            hp_auto_tick()
        except Exception as e:
            log_event("sys", "Homepage: automatic comparison: " + e.__class__.__name__)
        time.sleep(HP_TICK)


# ---- the check of the public addresses ----------------------------------------------------------------------------------------
def _hp_src_ok(lst, origin):
    origin = origin.lower()
    host = origin.split("//", 1)[-1]
    return any(x in ("*", "'self'", "https:", origin, origin + "/", host) for x in lst) and lst != ["'none'"]


def hp_csp(h, origin):
    """problems of a Content-Security-Policy for this page: [(english key, detail)]"""
    out = []
    for pol in str(h or "").split(","):
        d = {}
        for part in pol.split(";"):
            t = part.strip().split()
            if t:
                d.setdefault(t[0].lower(), [x.lower() for x in t[1:]])
        c = d.get("connect-src", d.get("default-src"))
        if c is not None and not _hp_src_ok(c, origin):
            out.append(("connect-src blocks fetch() – the page cannot load its files («Load failed»)", " ".join(c) or "'none'"))
        s = d.get("script-src", d.get("default-src"))
        if s is not None:
            if not _hp_src_ok(s, origin):
                out.append(("script-src blocks the scripts of this address", " ".join(s) or "'none'"))
            if "'wasm-unsafe-eval'" not in s and "'unsafe-eval'" not in s:
                out.append(("script-src without 'wasm-unsafe-eval' – WebAssembly does not start", " ".join(s)))
            if "'unsafe-inline'" not in s and not any(x.startswith(("'nonce-", "'sha")) for x in s):
                out.append(("script-src without 'unsafe-inline' – the start script of the page is blocked", ""))
        if "sandbox" in d:
            out.append(("CSP sandbox – the page runs restricted", " ".join(d["sandbox"])))
    return out


def hp_probe(url, want=None, origin=""):
    """one public address: follows redirects itself (at most 5) -> a row for the page"""
    import hashlib
    row = {"url": url, "chain": [], "probs": []}
    try:
        for _ in range(6):
            c, p = _hp_conn(url, 30)
            c.request("GET", p, headers={"User-Agent": "MoveEye/" + APP_VERSION, "Cache-Control": "no-cache"})
            r = c.getresponse()
            if r.status in (301, 302, 303, 307, 308) and r.getheader("Location"):
                from urllib.parse import urljoin
                url = urljoin(url, r.getheader("Location"))
                row["chain"].append(f"{r.status} → {_hp_clean(url)[:120]}")
                c.close()
                continue
            break
        else:
            raise HpErr("loop")
        H = {k: _hp_clean(r.getheader(k) or "")[:300] for k in ("Content-Type", "Content-Length", "Content-Security-Policy",
                                                                 "X-Content-Type-Options", "Cross-Origin-Embedder-Policy",
                                                                 "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy")}
        exp = want.get("size") if want else None
        small = want is None or (exp is not None and exp <= 2 * 1024 * 1024)
        cl = H["Content-Length"] if H["Content-Length"].isdigit() else ""
        h, n, head = hashlib.sha256(), 0, b""
        lim = (3 << 20) + (exp or 0) if small else (exp or 300 << 20) + (1 << 20)
        while n < lim:
            b = r.read(1 << 16)
            if not b:
                break
            if len(head) < 16:
                head += b[:16]
            h.update(b); n += len(b)
            if not small and cl:
                break                                       # a large file: its length from the header, the start for the check
        c.close()
        size = int(cl) if (not small and cl) else n
        row.update(status=r.status, size=size, type=H["Content-Type"], headers={k: v for k, v in H.items() if v})
    except HpErr:
        row.update(status=0, size=0, type="", headers={}); row["probs"].append(("too many redirects", ""))
        return row
    except Exception as e:
        row.update(status=0, size=0, type="", headers={}); row["probs"].append(("no connection", e.__class__.__name__))
        return row
    P = row["probs"]
    fin = re.match(r"^[a-z]+://[^/]+", url)
    if row["chain"] and fin and fin.group(0) != origin:
        P.append(("redirected to another address – fetch() and WebAssembly often fail there", fin.group(0)))
    if r.status != 200:
        P.append(("answer {code} instead of 200", str(r.status)))
        return row
    ext = want["path"].rsplit(".", 1)[-1] if want else "html"
    ok_t = _HP_TYPES.get(ext)
    ct = row["type"].split(";")[0].strip().lower()
    if ok_t and ct not in ok_t:
        P.append(("type {t} – expected {e}", f"{ct or '?'}|{ok_t[0]}"))
        if ext == "js" and H["X-Content-Type-Options"].lower() == "nosniff":
            P.append(("wrong type and nosniff – the browser refuses the script", ""))
    if want and want.get("size") is not None and row["size"] != want["size"]:
        P.append(("size {a} instead of {b}", f"{row['size']}|{want['size']}"))
    elif want and small and want.get("sha") and h.hexdigest() != want["sha"]:
        P.append(("content differs from the file of MoveEye", ""))
    if ext == "wasm" and head[:4] != b"\0asm":
        P.append(("not a WebAssembly file", ""))
    if H["Content-Security-Policy"] and (ext == "html" or ct == "text/html"):
        P += hp_csp(H["Content-Security-Policy"], origin)
    return row


def hp_check(items=None):
    base = hp_base_ok(CFG.get("hp_base"))
    if not base:
        raise HpErr("url")
    if items is None:
        items = hp_fixed_items() + (hp_sim_items(False)[0] or [{"path": "Sim/" + n, "size": None, "sha": None} for n in HP_SIM_NAMES])
    from urllib.parse import quote
    rows = []
    for i, it in enumerate([{"path": ""}, {"path": "Funk/"}, {"path": "Sim/"}] + list(items)):
        HP["prog"] = {"i": i + 1, "n": len(items) + 3, "file": it["path"] or "/"}
        if HP["cancel"]:
            raise HpErr("cancel")
        want = {"path": it["path"], "size": it.get("size"), "sha": it.get("sha")} if it["path"] and not it["path"].endswith("/") else None
        row = hp_probe(base + "/moveeye/" + quote(it["path"], safe="/"), want, base)
        row["path"] = it["path"] or "/"
        rows.append(row)
    st = hp_state()
    st["check"] = {"t": int(time.time()), "rows": rows}
    for r in rows:                                          # changed on the web space: the next publish uploads it again
        if any(k.startswith(("size {a}", "content differs", "answer {code}")) for k, _ in r["probs"]):
            (st.get("up") or {}).pop(r["path"], None)
    hp_save(st)
    bad = sum(1 for r in rows if r["probs"])
    log_event("sys", f"Homepage: {len(rows)} public addresses checked, {bad} with problems")
    return rows


# ---- state for the page (never the key) ---------------------------------------------------------------------------------------
def hp_status():
    """for the page (raw english keys, the page translates and formats them: HP_FMT_JS) - never the key"""
    st, p, pk = hp_state(), HP["prog"], SIM3D_WEB
    return {"ok": True, "key_set": bool(CFG.get("hp_key")), "base": CFG.get("hp_base") or "", "auto": bool(CFG.get("hp_auto")),
            "busy": HP["busy"], "wait": HP["wait"], "prog": {k: p.get(k) for k in ("i", "n", "bytes", "total", "file")} if p.get("n") else None,
            "err": [HP["err"], HP["msg"]] if HP["err"] else None, "cancelled": HP["msg"] == "cancel", "last": st.get("last"),
            "check": st.get("check"), "public": (hp_base_ok(CFG.get("hp_base")) or "") + "/moveeye/",
            "sim": {"ver": pk["version"] if pk["size"] else "", "ready": bool(pk["size"]) and sim3d_ready(pk)}}


def hp_action(d, lang=None):
    """POST /api/homepage -> (ok, english error)"""
    a = str(d.get("action") or "")
    if a == "key":
        k = str(d.get("key") or "").strip()
        if not re.fullmatch(r"[\x21-\x7e]{8,512}", k):
            return False, "The key: 8 to 512 signs, no spaces."
        CFG["hp_key"] = k
        st = hp_state(); st.pop("fail", None); hp_save(st)
        save_settings()
        log_event("sys", "Homepage: upload key set")
        return True, ""
    if a == "key_del":
        CFG["hp_key"] = ""
        save_settings()
        log_event("sys", "Homepage: upload key deleted")
        return True, ""
    if a == "base":
        b = hp_base_ok(d.get("base"))
        if not b:
            return False, "Only https addresses."
        if b != CFG.get("hp_base"):
            CFG.update(hp_base=b, hp_key="")                # the key belongs to exactly this web space
            st = hp_state(); st.pop("up", None); st.pop("check", None); hp_save(st)
            save_settings()
            log_event("sys", "Homepage: address changed, upload key deleted")
        return True, ""
    if a == "auto":
        CFG["hp_auto"] = bool(d.get("on"))
        save_settings()
        return True, ""
    if a in ("publish", "check"):
        if a == "publish" and not CFG.get("hp_key"):
            return False, "No upload key set."
        return (True, "") if hp_start(a) else (False, "busy - try again")
    if a == "cancel":
        HP["cancel"] = True
        return True, ""
    return False, "unknown action"


_smalltv_routes_hp = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                      # + 639zzzh: /homepage and /api/homepage (only the administrator)
    _smalltv_routes_hp(app, reply, body)
    from flask import Response, request, g

    @app.route("/api/homepage", methods=["GET", "POST"])
    def api_homepage():
        d = body() if request.method == "POST" else {}
        L = norm_lang(request.args.get("lang") or d.get("lang") or CFG.get("lang"))
        if not qrk_admin_ok(g):
            return reply({"ok": False, "error": tr("Only for the administrator", L)}, 403)
        if request.method == "POST":
            if d.get("key") and seclogin_plain(request):
                url = seclogin_url(request).split("/api/")[0] + "/"
                return reply({"ok": False, "error": tr("For your safety a password can only be set over the secure page", L) + ": " + url}, 403)
            ok, err = hp_action(d, L)
            if not ok:
                return reply(dict(hp_status(), ok=False, error=tr(err, L)), 400)
        return reply(hp_status())

    @app.route("/homepage")
    def homepage_page():
        if not qrk_admin_ok(g):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return Response(render_page(HP_PAGE, "more").replace("/*HPFMT*/", HP_FMT_JS, 1).replace("/*HPDE*/", "Object.assign(I18N.de, " + json.dumps(
            _HP_DE, ensure_ascii=False).replace("</", "<\\/") + ");", 1), mimetype="text/html", headers={"Cache-Control": "no-store"})

    if not HP["run"]:
        HP["run"] = True
        threading.Thread(target=_hp_worker, daemon=True, name="homepage-auto").start()


HP_MORE_ITEM = ('<a class="mi" href="/homepage" id="m-homepage"><i>🌐</i><span><b data-i18n="Homepage">Homepage</b>'
                '<small data-i18n="Put the public pages on your web space">Put the public pages on your web space</small></span><span class="ar">›</span></a>\n  ')
_render_page_hp = render_page


# wraps: render_page
def render_page(page, active):                              # + 639zzzh: the item under «Mehr» (administrator)
    out = _render_page_hp(page, active)
    if active == "more" and 'href="/homepage"' not in out and '<a class="mi" href="/tools">' in out:
        try:
            from flask import g as _g
            admin = qrk_admin_ok(_g)
        except Exception:
            admin = False
        if admin:
            i = out.find('<a class="mi" href="/tools">')
            de_ = "Object.assign(I18N.de, " + json.dumps({k: _HP_DE[k] for k in ("Homepage", "Put the public pages on your web space")},
                                                         ensure_ascii=False) + ");"
            out = out[:i] + HP_MORE_ITEM + out[i:]
            out = out.replace("/*MOREDE*/", de_ + "/*MOREDE*/", 1) if "/*MOREDE*/" in out else out.replace("</body>", "<script>" + de_ + "</script></body>", 1)
    return out


if GUI_OK:
    _hp_tk_more_base = App._tk_more_bar

    def _hp_tk_more_bar(self, parent):
        f = _hp_tk_more_base(self, parent)
        row = max([int(x.grid_info().get("row", 0)) for x in f.grid_slaves()] + [-1]) + 1
        self._fbtn(f, "🌐 " + tr("Homepage") + " (" + tr("browser") + ")", lambda: self._open_page("/homepage")).grid(
            row=row, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639zzz «Morse»)
    App._tk_more_bar = _hp_tk_more_bar


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
HP_TEXTS = {
    "Homepage": ("Homepage", "Page d’accueil", "Homepage", "Pagina d’entrada"),
    "Put the public pages on your web space": ("Öffentliche Seiten auf deinen Webspace laden", "Mettre les pages publiques sur ton espace web",
                                               "Caricare le pagine pubbliche sul tuo spazio web", "Chargiar las paginas publicas sin tes spazi web"),
    "browser": ("Browser", "navigateur", "browser", "browser"),
    "MoveEye uploads your public pages to your web space: start page, phone radio (Funk/), simulator in the browser (Sim/) and the test page.":
        ("MoveEye lädt deine öffentlichen Seiten auf deinen Webspace: Startseite, Handy-Funkgerät (Funk/), Simulator im Browser (Sim/) und die Test-Seite.",
         "MoveEye charge tes pages publiques sur ton espace web : page d’accueil, radio du téléphone (Funk/), simulateur dans le navigateur (Sim/) et la page de test.",
         "MoveEye carica le tue pagine pubbliche sul tuo spazio web: pagina iniziale, radio del telefono (Funk/), simulatore nel browser (Sim/) e la pagina di test.",
         "MoveEye chargia tias paginas publicas sin tes spazi web: pagina d’entrada, radio dal telefonin (Funk/), simulatur en il browser (Sim/) e la pagina da test."),
    "Publish on the homepage": ("Auf Homepage veröffentlichen", "Publier sur la page d’accueil", "Pubblicare sulla homepage", "Publitgar sin la pagina d’entrada"),
    "Check the addresses": ("Adressen prüfen", "Vérifier les adresses", "Verificare gli indirizzi", "Controllar las adressas"),
    "Cancel": ("Abbrechen", "Annuler", "Annullare", "Interrumper"),
    "automatically after every update": ("nach jedem Update automatisch", "automatiquement après chaque mise à jour", "automaticamente dopo ogni aggiornamento",
                                         "automaticamain suenter mintga actualisaziun"),
    "Only changed files are uploaded, in the background and never during an alarm.":
        ("Hochgeladen wird nur, was sich geändert hat – im Hintergrund und nie während eines Alarms.",
         "Seuls les fichiers modifiés sont envoyés, en arrière-plan et jamais pendant une alarme.",
         "Vengono caricati solo i file modificati, in background e mai durante un allarme.",
         "Chargià vegn mo quai ch’è midà – en il fund e mai durant in alarm."),
    "Access": ("Zugang", "Accès", "Accesso", "Access"),
    "Address of the web space": ("Adresse des Webspace", "Adresse de l’espace web", "Indirizzo dello spazio web", "Adressa dal spazi web"),
    "Save the address": ("Adresse speichern", "Enregistrer l’adresse", "Salvare l’indirizzo", "Memorisar l’adressa"),
    "A new address deletes the upload key.": ("Eine neue Adresse löscht den Upload-Schlüssel.", "Une nouvelle adresse supprime la clé d’envoi.",
                                              "Un nuovo indirizzo cancella la chiave di caricamento.", "Ina nova adressa stizza la clav da chargiar."),
    "Upload key": ("Upload-Schlüssel", "Clé d’envoi", "Chiave di caricamento", "Clav da chargiar"),
    "Upload key is set (never shown again).": ("Upload-Schlüssel ist gesetzt (wird nie mehr angezeigt).", "La clé d’envoi est définie (plus jamais affichée).",
                                               "La chiave di caricamento è impostata (non viene più mostrata).", "La clav da chargiar è definida (na vegn mai pli mussada)."),
    "No upload key set.": ("Kein Upload-Schlüssel gesetzt.", "Aucune clé d’envoi définie.", "Nessuna chiave di caricamento impostata.", "Nagina clav da chargiar definida."),
    "Set the key": ("Schlüssel setzen", "Définir la clé", "Impostare la chiave", "Definir la clav"),
    "Replace the key": ("Schlüssel ersetzen", "Remplacer la clé", "Sostituire la chiave", "Remplazzar la clav"),
    "Delete the key": ("Schlüssel löschen", "Supprimer la clé", "Cancellare la chiave", "Stizzar la clav"),
    "Delete the upload key?": ("Upload-Schlüssel löschen?", "Supprimer la clé d’envoi ?", "Cancellare la chiave di caricamento?", "Stizzar la clav da chargiar?"),
    "Result of the check": ("Ergebnis der Prüfung", "Résultat de la vérification", "Risultato della verifica", "Resultat da la controlla"),
    "Open the homepage": ("Homepage öffnen", "Ouvrir la page d’accueil", "Aprire la homepage", "Avrir la pagina d’entrada"),
    "Browser simulator": ("Simulator im Browser", "Simulateur dans le navigateur", "Simulatore nel browser", "Simulatur en il browser"),
    "not released yet": ("noch nicht veröffentlicht", "pas encore publié", "non ancora pubblicato", "anc betg publitgà"),
    "ready": ("bereit", "prêt", "pronto", "pront"),
    "comparing": ("vergleicht", "compare", "confronta", "cumpareglia"),
    "uploading": ("lädt hoch", "envoi", "carica", "chargia"),
    "checking": ("prüft", "vérifie", "verifica", "controllescha"),
    "starting": ("startet", "démarre", "avvia", "cumenza"),
    "fetching the browser simulator": ("holt den Simulator für den Browser", "télécharge le simulateur pour le navigateur", "scarica il simulatore per il browser",
                                       "chargia giu il simulatur per il browser"),
    "waiting – alarm": ("wartet – Alarm", "en attente – alarme", "in attesa – allarme", "spetga – alarm"),
    "Cancelled.": ("Abgebrochen.", "Annulé.", "Annullato.", "Interrut."),
    "Done: {up} uploaded, {same} unchanged, {gone} deleted.": ("Fertig: {up} hochgeladen, {same} unverändert, {gone} gelöscht.",
                                                               "Terminé : {up} envoyés, {same} inchangés, {gone} supprimés.",
                                                               "Fatto: {up} caricati, {same} invariati, {gone} cancellati.",
                                                               "Fatg: {up} chargiads, {same} betg midads, {gone} stizzads."),
    "The browser simulator is not released yet – Sim/ only gets the test page.":
        ("Der Simulator für den Browser ist noch nicht veröffentlicht – Sim/ bekommt nur die Test-Seite.",
         "Le simulateur pour le navigateur n’est pas encore publié – Sim/ ne reçoit que la page de test.",
         "Il simulatore per il browser non è ancora pubblicato – Sim/ riceve solo la pagina di test.",
         "Il simulatur per il browser n’è anc betg publitgà – Sim/ survegn mo la pagina da test."),
    "Browser simulator: download failed": ("Simulator für den Browser: Laden fehlgeschlagen", "Simulateur pour le navigateur : échec du téléchargement",
                                           "Simulatore per il browser: download non riuscito", "Simulatur per il browser: chargiar n’è betg reussì"),
    "Browser simulator: package is wrong": ("Simulator für den Browser: Paket stimmt nicht", "Simulateur pour le navigateur : paquet incorrect",
                                            "Simulatore per il browser: pacchetto errato", "Simulatur per il browser: il pachet è fauss"),
    "Wrong upload key (the server answered {d}) – set it again.": ("Upload-Schlüssel falsch (Antwort {d}) – bitte neu setzen.",
                                                                   "Clé d’envoi incorrecte (réponse {d}) – la définir à nouveau.",
                                                                   "Chiave di caricamento errata (risposta {d}) – impostarla di nuovo.",
                                                                   "Clav da chargiar faussa (resposta {d}) – la definir da nov."),
    "The web space is full (500 MB) – delete old files there.": ("Der Webspace ist voll (500 MB) – dort alte Dateien löschen.",
                                                                 "L’espace web est plein (500 Mo) – y supprimer d’anciens fichiers.",
                                                                 "Lo spazio web è pieno (500 MB) – cancellare lì i vecchi file.",
                                                                 "Il spazi web è plain (500 MB) – stizzar là vegls datotecas."),
    "File too large for the web space (at most 100 MB): {d}": ("Datei zu gross für den Webspace (höchstens 100 MB): {d}",
                                                               "Fichier trop grand pour l’espace web (100 Mo au plus) : {d}",
                                                               "File troppo grande per lo spazio web (al massimo 100 MB): {d}",
                                                               "Datoteca memia gronda per il spazi web (maximalmain 100 MB): {d}"),
    "The server answered {d}.": ("Der Server antwortete {d}.", "Le serveur a répondu {d}.", "Il server ha risposto {d}.", "Il server ha respundì {d}."),
    "No connection to the web space.": ("Keine Verbindung zum Webspace.", "Pas de connexion à l’espace web.", "Nessuna connessione allo spazio web.",
                                        "Nagina colliaziun cun il spazi web."),
    "Address not valid.": ("Adresse ungültig.", "Adresse non valable.", "Indirizzo non valido.", "Adressa nunvalaivla."),
    "Only https addresses.": ("Nur https-Adressen.", "Seulement des adresses https.", "Solo indirizzi https.", "Mo adressas https."),
    "The key: 8 to 512 signs, no spaces.": ("Der Schlüssel: 8 bis 512 Zeichen, ohne Leerzeichen.", "La clé : 8 à 512 caractères, sans espaces.",
                                            "La chiave: da 8 a 512 caratteri, senza spazi.", "La clav: 8 fin 512 caracters, senza spazis."),
    "The server redirected the upload – stopped (the key is never sent to another address).":
        ("Der Server hat das Hochladen umgeleitet – gestoppt (der Schlüssel geht nie an eine andere Adresse).",
         "Le serveur a redirigé l’envoi – arrêté (la clé n’est jamais envoyée à une autre adresse).",
         "Il server ha reindirizzato il caricamento – fermato (la chiave non va mai a un altro indirizzo).",
         "Il server ha devià il chargiar – fermà (la clav na va mai ad ina autra adressa)."),
    "Error: {d}": ("Fehler: {d}", "Erreur : {d}", "Errore: {d}", "Errur: {d}"),
    "busy - try again": ("beschäftigt – später nochmals", "occupé – réessayer", "occupato – riprovare", "occupà – empruvar pli tard"),
    "all addresses ok": ("alle Adressen in Ordnung", "toutes les adresses sont en ordre", "tutti gli indirizzi sono in ordine", "tut las adressas èn en urden"),
    "{n} addresses with problems": ("{n} Adressen mit Problemen", "{n} adresses avec des problèmes", "{n} indirizzi con problemi", "{n} adressas cun problems"),
    "answer {code} instead of 200": ("Antwort {code} statt 200", "réponse {code} au lieu de 200", "risposta {code} invece di 200", "resposta {code} empè da 200"),
    "redirected to another address – fetch() and WebAssembly often fail there": (
        "umgeleitet auf eine andere Adresse – fetch() und WebAssembly scheitern dort oft",
        "redirigé vers une autre adresse – fetch() et WebAssembly y échouent souvent",
        "reindirizzato a un altro indirizzo – fetch() e WebAssembly lì falliscono spesso",
        "deviò sin in’autra adressa – fetch() e WebAssembly fallan là savens"),
    "type {t} – expected {e}": ("Typ {t} – erwartet {e}", "type {t} – attendu {e}", "tipo {t} – atteso {e}", "tip {t} – spetgà {e}"),
    "wrong type and nosniff – the browser refuses the script": ("falscher Typ und nosniff – der Browser weist das Skript ab",
                                                                "mauvais type et nosniff – le navigateur refuse le script",
                                                                "tipo errato e nosniff – il browser rifiuta lo script",
                                                                "tip fauss e nosniff – il browser refusa il script"),
    "size {a} instead of {b}": ("Grösse {a} statt {b}", "taille {a} au lieu de {b}", "dimensione {a} invece di {b}", "grondezza {a} empè da {b}"),
    "content differs from the file of MoveEye": ("Inhalt anders als die Datei von MoveEye", "contenu différent du fichier de MoveEye",
                                                 "contenuto diverso dal file di MoveEye", "cuntegn auter che la datoteca da MoveEye"),
    "not a WebAssembly file": ("keine WebAssembly-Datei", "pas un fichier WebAssembly", "non è un file WebAssembly", "nagina datoteca WebAssembly"),
    "no connection": ("keine Verbindung", "pas de connexion", "nessuna connessione", "nagina colliaziun"),
    "too many redirects": ("zu viele Umleitungen", "trop de redirections", "troppi reindirizzamenti", "memia bleras deviaziuns"),
    "connect-src blocks fetch() – the page cannot load its files («Load failed»)": (
        "connect-src sperrt fetch() – die Seite kann ihre Dateien nicht laden («Load failed»)",
        "connect-src bloque fetch() – la page ne peut pas charger ses fichiers («Load failed»)",
        "connect-src blocca fetch() – la pagina non può caricare i suoi file («Load failed»)",
        "connect-src bloccha fetch() – la pagina na po betg chargiar sias datotecas («Load failed»)"),
    "script-src blocks the scripts of this address": ("script-src sperrt die Skripte dieser Adresse", "script-src bloque les scripts de cette adresse",
                                                      "script-src blocca gli script di questo indirizzo", "script-src bloccha ils scripts da questa adressa"),
    "script-src without 'wasm-unsafe-eval' – WebAssembly does not start": (
        "script-src ohne 'wasm-unsafe-eval' – WebAssembly startet nicht", "script-src sans 'wasm-unsafe-eval' – WebAssembly ne démarre pas",
        "script-src senza 'wasm-unsafe-eval' – WebAssembly non parte", "script-src senza 'wasm-unsafe-eval' – WebAssembly na cumenza betg"),
    "script-src without 'unsafe-inline' – the start script of the page is blocked": (
        "script-src ohne 'unsafe-inline' – das Startskript der Seite ist gesperrt", "script-src sans 'unsafe-inline' – le script de démarrage de la page est bloqué",
        "script-src senza 'unsafe-inline' – lo script di avvio della pagina è bloccato", "script-src senza 'unsafe-inline' – il script da start da la pagina è bloccà"),
    "CSP sandbox – the page runs restricted": ("CSP sandbox – die Seite läuft eingeschränkt", "CSP sandbox – la page est restreinte",
                                               "CSP sandbox – la pagina è limitata", "CSP sandbox – la pagina è restrenschida"),
    "Headers": ("Kopfzeilen", "En-têtes", "Intestazioni", "Lingias da chau"),
    "last": ("zuletzt", "dernière fois", "ultima volta", "l’ultima giada"),
    "automatic": ("automatisch", "automatique", "automatico", "automatic"),
}
for _k, _v in HP_TEXTS.items():                            # (the table is in the data zip: without it the page is not there either)
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_HP_DE = {_k: DE.get(_k, _v[0]) for _k, _v in HP_TEXTS.items()}

HP_FUNK_SW_JS = ("// Service Worker der Seite «Handy-Funkgerät» (erzeugt von werkzeuge/funk_pwa.py): alles aus dem Speicher, damit die Seite\n"
                 "// nach dem ersten Laden ohne Internet geht. Eine neue Seite = ein neuer Name des Speichers (die alte wird gelöscht).\n"
                 "const C = 'funk-@VER@';\n"
                 "const TEILE = [\"./\", \"index.html\", \"manifest.webmanifest\", \"icon-192.png\", \"icon-512.png\", \"apple-touch-icon.png\"];\n"
                 "self.addEventListener('install', e => { e.waitUntil(caches.open(C).then(c => c.addAll(TEILE)).then(() => self.skipWaiting())); });\n"
                 "self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k))))\n"
                 "  .then(() => self.clients.claim())); });\n"
                 "self.addEventListener('fetch', e => {\n"
                 "  const r = e.request; if (r.method !== 'GET' || new URL(r.url).origin !== self.location.origin) return;\n"
                 "  e.respondWith(caches.match(r, {ignoreSearch: true}).then(h => h || fetch(r).catch(() => r.mode === 'navigate' ? caches.match('index.html') : Response.error())));\n"
                 "});\n")

# the three symbols of the PWA (funk/*.png of the repository, werkzeuge/funk_pwa.py) as base64 - in the data zip
HP_FUNK_PNG = r"""{"apple-touch-icon.png": "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", "icon-192.png": "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", "icon-512.png": "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"}"""

# the start page of the web space (template of the owner, 5 languages from the browser language)
HP_INDEX_HTML = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye</title><style>body{margin:0;font:17px system-ui,sans-serif;background:#111418;color:#e8eaed;display:flex;min-height:100vh;align-items:center;justify-content:center}
main{padding:24px;max-width:420px;width:100%}h1{margin:0 0 20px}a{display:block;margin:12px 0;padding:18px;border-radius:14px;background:#1d2229;color:#e8eaed;text-decoration:none;border:1px solid #2c333c}
small{display:block;color:#9aa3ad;margin-top:4px}</style></head><body><main><h1>MoveEye</h1>
<a href="Funk/"><span id="f">📡 Handy-Funkgerät</span><small id="fs">Morse und eigenes Protokoll, geht auch offline</small></a>
<a href="Sim/"><span id="s">🎮 Simulator (Demo)</span><small id="ss">Im Browser, ohne Verbindung zu MoveEye · ca. 80 MB</small></a>
</main><script>(function(){var T={en:["📡 Phone radio","Morse and own protocol, works offline too","🎮 Simulator (demo)","In the browser, without a connection to MoveEye · about 80 MB"],
fr:["📡 Radio du téléphone","Morse et protocole propre, fonctionne aussi hors ligne","🎮 Simulateur (démo)","Dans le navigateur, sans connexion à MoveEye · env. 80 Mo"],
it:["📡 Radio del telefono","Morse e protocollo proprio, funziona anche offline","🎮 Simulatore (demo)","Nel browser, senza connessione a MoveEye · ca. 80 MB"],
rm:["📡 Radio dal telefonin","Morse ed agen protocol, funcziuna er offline","🎮 Simulatur (demo)","En il browser, senza colliaziun cun MoveEye · ca. 80 MB"]};
var l=(navigator.language||"de").slice(0,2).toLowerCase(),t=T[l];if(!t)return;document.documentElement.lang=l;
["f","fs","s","ss"].forEach(function(id,i){document.getElementById(id).textContent=t[i];});})();</script></body></html>
"""

# the test page in Sim/ (template of the owner): fetch of every file; a blocked address shows the directive of the CSP
HP_TEST_HTML = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sim-Test</title><style>body{margin:0;padding:16px;font:15px system-ui,sans-serif;background:#111418;color:#e8eaed}
button{font:inherit;padding:14px 18px;border-radius:12px;border:0;background:#e8a54b;color:#111;margin:8px 0}
pre{white-space:pre-wrap;word-break:break-all;background:#1d2229;padding:12px;border-radius:10px;font-size:13px}</style></head><body>
<h2>Sim-Test</h2><p>Liegt im Ordner «Sim». Tippe auf «Prüfen» und mach danach ein Bildschirmfoto.</p>
<button id="b">Prüfen</button><pre id="o">–</pre>
<script>
const files=["index.html","index.js","index_audio_worklet.js","index.wasm","index.pck"];
const o=document.getElementById('o');const log=t=>{o.textContent+=t+"\n";};
document.addEventListener('securitypolicyviolation',e=>log("CSP sperrt: "+e.violatedDirective+" → "+(e.blockedURI||"?")+" (Regel: "+(e.originalPolicy||"").slice(0,200)+")"));
document.getElementById('b').onclick=async()=>{o.textContent="Seite: "+location.href+"\n";
 log("WebAssembly: "+(typeof WebAssembly)+" · WebGL2: "+(!!document.createElement('canvas').getContext('webgl2')));
 try{await WebAssembly.compile(new Uint8Array([0,97,115,109,1,0,0,0]));log("WebAssembly.compile: ok");}catch(e){log("WebAssembly.compile: FEHLER "+e.name+" – "+e.message);}
 for(const f of files){const t0=performance.now();
  try{const r=await fetch(f,{cache:"no-store"});
   let n=0;const rd=r.body&&r.body.getReader?r.body.getReader():null;
   if(rd){for(;;){const {done,value}=await rd.read();if(done)break;n+=value.length;}}else{n=(await r.arrayBuffer()).byteLength;}
   log(f+": "+r.status+" · "+(n/1048576).toFixed(1)+" MB · Typ "+(r.headers.get('content-type')||'?')+(r.redirected?" · umgeleitet nach "+r.url:"")+" · "+((performance.now()-t0)/1000).toFixed(1)+" s");
  }catch(e){log(f+": FEHLER "+e.name+" – "+e.message);}
 }
 log("fertig");};
</script></body></html>
"""

# the formatting of the state for the page (also run by werkzeuge/homepage_test.py in node)
HP_FMT_JS = r"""
const hpMB = n => ((n || 0) / 1048576).toFixed(1) + " MB";
const HP_ERR = {key: "Wrong upload key (the server answered {d}) – set it again.", quota: "The web space is full (500 MB) – delete old files there.",
  large: "File too large for the web space (at most 100 MB): {d}", http5: "The server answered {d}.", http: "The server answered {d}.",
  net: "No connection to the web space.", nokey: "No upload key set.", url: "Address not valid.",
  redirect: "The server redirected the upload – stopped (the key is never sent to another address)."};
function hpProg(p) { return p ? p.i + "/" + p.n + (p.bytes != null ? " · " + hpMB(p.bytes) : "") + (p.file ? " · " + p.file : "") : ""; }
function hpProb(k, d, t) { d = String(d || ""); let [a, b] = d.split("|"); b = b || "";
  if (k.indexOf("{a}") >= 0) { a = hpMB(+a); b = hpMB(+b); }
  if (k.indexOf("{") < 0) return t(k) + (d ? ": " + d : "");
  return t(k).replace("{code}", a).replace("{t}", a).replace("{e}", b).replace("{a}", a).replace("{b}", b); }
function hpRow(r, t) { return {line: r.path + ": " + (r.status || "–") + " · " + hpMB(r.size) + " · " + (r.type || "?"),
  probs: (r.probs || []).map(p => hpProb(p[0], p[1], t)), chain: r.chain || [], headers: r.headers || {}}; }
function hpErr(e, t) { return e ? t(HP_ERR[e[0]] || "Error: {d}").replace("{d}", e[1] || "") : ""; }
function hpNote(n, t) { return n && n[0] ? t(n[0]) + (n[1] ? " – " + n[1] : "") : ""; }
function hpLast(l, t) { return t("Done: {up} uploaded, {same} unchanged, {gone} deleted.").replace("{up}", l.up || 0).replace("{same}", l.same || 0)
  .replace("{gone}", l.gone || 0) + " · " + hpMB(l.bytes); }
function hpSum(rows, t) { const n = rows.filter(r => r.probs.length).length; return n ? t("{n} addresses with problems").replace("{n}", n) : t("all addresses ok"); }
"""

HP_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Homepage</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:720px;margin:0 auto}
.hp-back{display:inline-block;margin:0 0 8px;color:var(--acc);text-decoration:none;font-weight:600;min-height:32px}
.hp-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.hp-row>*{flex:1 1 180px;min-height:44px}
.hp-f{display:flex;flex-direction:column;gap:8px}
.hp-f input[type=text],.hp-f input[type=password],.hp-f input[type=url]{font:inherit;font-size:16px;min-height:44px;width:100%;box-sizing:border-box;
background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:6px 10px}
.hp-hint{font-size:13px;color:var(--mut);overflow-wrap:anywhere}.hp-bad{color:var(--red)}.hp-ok{color:var(--grn)}
.hp-st{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:0 0 12px;overflow-wrap:anywhere}
.hp-bar{height:10px;border-radius:999px;background:var(--line);overflow:hidden;margin-top:6px}.hp-bar i{display:block;height:100%;width:0;background:var(--acc)}
.hp-res{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.hp-res li{border:1px solid var(--line);border-radius:10px;padding:8px 10px;font-size:14px;overflow-wrap:anywhere}
.hp-res li.bad{border-color:var(--red)}.hp-res b{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}
.hp-res ul{margin:4px 0 0 18px;padding:0;color:var(--red)}.hp-res details{font-size:12px;color:var(--mut)}
label.hp-chk{display:flex;gap:8px;align-items:center;min-height:44px}
section.card h3{margin:0 0 10px}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <a class="hp-back" href="/more" id="hp-back">‹ More</a>
  <h2 id="hp-title">🌐 Homepage</h2>
  <div class="hp-hint" id="hp-intro" style="margin:0 0 12px"></div>
  <div class="hp-st" id="hp-st">…</div>
  <section class="card"><div class="hp-f">
    <div class="hp-row"><button type="button" id="hp-go"></button><button type="button" class="sec" id="hp-chk"></button>
      <button type="button" class="sec" id="hp-stop" hidden></button></div>
    <label class="hp-chk"><input type="checkbox" id="hp-auto"><span id="hp-auto-l"></span></label>
    <div class="hp-hint" id="hp-auto-h"></div>
    <div class="hp-hint" id="hp-sim"></div>
    <a id="hp-open" href="#" target="_blank" rel="noopener noreferrer"></a>
  </div></section>
  <section class="card"><h3 id="hp-acc-t"></h3><div class="hp-f">
    <label class="hp-hint" for="hp-base" id="hp-base-l"></label>
    <div class="hp-row"><input type="url" id="hp-base" autocomplete="off" spellcheck="false" maxlength="200"><button type="button" class="sec" id="hp-base-b"></button></div>
    <div class="hp-hint" id="hp-base-h"></div>
    <div id="hp-key-st"></div>
    <label class="hp-hint" for="hp-key" id="hp-key-l"></label>
    <input type="password" id="hp-key" maxlength="512" autocomplete="new-password" autocapitalize="off" spellcheck="false">
    <div class="hp-row"><button type="button" id="hp-key-b"></button><button type="button" class="sec" id="hp-key-d"></button></div>
    <div class="hp-hint hp-bad" id="hp-err2"></div>
  </div></section>
  <section class="card" id="hp-res-c" hidden><h3 id="hp-res-t"></h3><div class="hp-hint" id="hp-res-s"></div><ul class="hp-res" id="hp-res"></ul></section>
</main>
<script>
/*COMMON*/
/*HPDE*/
/*HPFMT*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $ = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  let J = null, TM = 0;
  const api = async (b) => { try { const r = await fetch("/api/homepage?lang=" + L(), b ? {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify(Object.assign({lang: L()}, b))} : {cache: "no-store"}); return await r.json(); } catch (e) { return null; } };
  document.title = "MoveEye – " + t("Homepage");
  $("hp-back").textContent = "‹ " + t("More"); $("hp-title").textContent = "🌐 " + t("Homepage");
  $("hp-intro").textContent = t("MoveEye uploads your public pages to your web space: start page, phone radio (Funk/), simulator in the browser (Sim/) and the test page.");
  $("hp-go").textContent = "⬆ " + t("Publish on the homepage"); $("hp-chk").textContent = "🔍 " + t("Check the addresses"); $("hp-stop").textContent = "⏹ " + t("Cancel");
  $("hp-auto-l").textContent = t("automatically after every update");
  $("hp-auto-h").textContent = t("Only changed files are uploaded, in the background and never during an alarm.");
  $("hp-acc-t").textContent = t("Access"); $("hp-base-l").textContent = t("Address of the web space"); $("hp-base-b").textContent = t("Save the address");
  $("hp-base-h").textContent = t("A new address deletes the upload key."); $("hp-key-l").textContent = t("Upload key");
  $("hp-key-d").textContent = t("Delete the key"); $("hp-res-t").textContent = t("Result of the check"); $("hp-open").textContent = "↗ " + t("Open the homepage");
  function paint(j) {
    if (!j) return; J = j;
    const st = $("hp-st"); st.textContent = "";
    if (j.error) st.appendChild(E("div", "hp-bad", j.error));
    if (j.busy) { st.appendChild(E("div", "", "⏳ " + t(j.busy) + (j.wait ? " · " + t("waiting – alarm") : ""))); if (j.prog) st.appendChild(E("div", "hp-hint", hpProg(j.prog)));
      if (j.prog && j.prog.total) { const b = E("div", "hp-bar"), i = E("i"); i.style.width = Math.round(100 * j.prog.bytes / j.prog.total) + "%"; b.appendChild(i); st.appendChild(b); } }
    else if (j.err) st.appendChild(E("div", "hp-bad", "⚠ " + hpErr(j.err, t)));
    else if (j.cancelled) st.appendChild(E("div", "", t("Cancelled.")));
    const l = j.last;
    if (l && !j.busy) { st.appendChild(E("div", "hp-ok", "✓ " + hpLast(l, t) + (l.auto ? " (" + t("automatic") + ")" : "")));
      if (l.t) st.appendChild(E("div", "hp-hint", t("last") + ": " + new Date(l.t * 1000).toLocaleString()));
      if (l.note) st.appendChild(E("div", "hp-hint", hpNote(l.note, t))); (l.ren || []).forEach(x => st.appendChild(E("div", "hp-bad", x))); }
    if (!st.childNodes.length) st.textContent = j.key_set ? "–" : t("No upload key set.");
    $("hp-go").disabled = !!j.busy || !j.key_set; $("hp-chk").disabled = !!j.busy; $("hp-stop").hidden = !j.busy;
    $("hp-auto").checked = !!j.auto;
    if (document.activeElement !== $("hp-base")) $("hp-base").value = j.base || "";
    $("hp-key-st").textContent = j.key_set ? "🔑 " + t("Upload key is set (never shown again).") : t("No upload key set.");
    $("hp-key-b").textContent = j.key_set ? t("Replace the key") : t("Set the key"); $("hp-key-d").hidden = !j.key_set;
    $("hp-sim").textContent = "🎮 " + t("Browser simulator") + ": " + (j.sim && j.sim.ver ? j.sim.ver + (j.sim.ready ? " · " + t("ready") : "") : t("not released yet"));
    $("hp-open").href = j.public || "#";
    const c = j.check; $("hp-res-c").hidden = !c;
    if (c) { const rows = (c.rows || []).map(r => hpRow(r, t)); $("hp-res-s").textContent = (c.t ? new Date(c.t * 1000).toLocaleString() + " · " : "") + hpSum(rows, t);
      const ul = $("hp-res"); ul.textContent = "";
      rows.forEach(r => { const li = E("li", r.probs.length ? "bad" : ""); li.appendChild(E("b", "", (r.probs.length ? "✗ " : "✓ ") + r.line));
        if (r.chain.length) li.appendChild(E("div", "hp-hint", r.chain.join(" · ")));
        if (r.probs.length) { const u = E("ul"); r.probs.forEach(p => u.appendChild(E("li", "", p))); li.appendChild(u); }
        const hk = Object.keys(r.headers); if (hk.length) { const d = E("details"), s = E("summary", "", t("Headers")); d.appendChild(s);
          hk.forEach(k => d.appendChild(E("div", "", k + ": " + r.headers[k]))); li.appendChild(d); }
        ul.appendChild(li); }); }
    clearTimeout(TM); TM = setTimeout(async () => paint(await api()), j.busy ? 1500 : 15000);
  }
  const act = async (b, btn) => { if (btn) btn.disabled = true; $("hp-err2").textContent = ""; const j = await api(b);
    if (j && j.ok === false && j.error) $("hp-err2").textContent = j.error; if (j && j.key_set !== undefined) paint(j); if (btn) btn.disabled = false; return j; };
  $("hp-go").onclick = () => act({action: "publish"}, $("hp-go")); $("hp-chk").onclick = () => act({action: "check"}, $("hp-chk"));
  $("hp-stop").onclick = () => act({action: "cancel"}); $("hp-auto").onchange = () => act({action: "auto", on: $("hp-auto").checked});
  $("hp-base-b").onclick = () => act({action: "base", base: $("hp-base").value.trim()}, $("hp-base-b"));
  $("hp-key-b").onclick = async () => { const k = $("hp-key").value.trim(); if (!k) return; const j = await act({action: "key", key: k}, $("hp-key-b"));
    if (j && j.ok !== false) $("hp-key").value = ""; };
  $("hp-key-d").onclick = () => { if (confirm(t("Delete the upload key?"))) act({action: "key_del"}); };
  paint(await api());
})();
</script></body></html>
"""

# ---- the manual: one point in the section «Morse-Modus» (the phone radio lives there) --------------------------------------------
HP_HELP_HTML = r"""
de|<li><b>🌐 Homepage</b> (Mehr → Homepage, nur der Administrator): lädt deine öffentlichen Seiten auf deinen Webspace – Startseite, Handy-Funkgerät (<code>Funk/</code>), Simulator im Browser (<code>Sim/</code>, nur das signierte Paket «sim-web.zip») und <code>Sim/test.html</code>. Adresse ab Werk <code>https://kevlaschef.com</code> (nur https), dazu der Upload-Schlüssel: setzen, ersetzen oder löschen, er wird nie mehr angezeigt und steht nie im Protokoll; eine neue Adresse löscht ihn. Hochgeladen wird nur, was sich geändert hat, im Hintergrund, nie während eines Alarms; «nach jedem Update automatisch» ist ab Werk an. Danach prüft MoveEye jede öffentliche Adresse (Status, Grösse, Typ, Umleitungen, Content-Security-Policy) – z. B. «connect-src sperrt fetch()» erklärt «Load failed» am iPhone.</li>
en|<li><b>🌐 Homepage</b> (More → Homepage, administrator only): puts your public pages on your web space – start page, phone radio (<code>Funk/</code>), simulator in the browser (<code>Sim/</code>, only the signed package «sim-web.zip») and <code>Sim/test.html</code>. Address by default <code>https://kevlaschef.com</code> (https only), plus the upload key: set, replace or delete it; it is never shown again and never in the log; a new address deletes it. Only changed files are uploaded, in the background, never during an alarm; «automatically after every update» is on by default. Then MoveEye checks every public address (status, size, type, redirects, Content-Security-Policy) – e.g. «connect-src blocks fetch()» explains «Load failed» on the iPhone.</li>
fr|<li><b>🌐 Page d’accueil</b> (Plus → Page d’accueil, administrateur seulement) : met tes pages publiques sur ton espace web – page d’accueil, radio du téléphone (<code>Funk/</code>), simulateur dans le navigateur (<code>Sim/</code>, seulement le paquet signé «sim-web.zip») et <code>Sim/test.html</code>. Adresse par défaut <code>https://kevlaschef.com</code> (https seulement) et la clé d’envoi : jamais réaffichée, jamais dans le journal ; une nouvelle adresse la supprime. Seuls les fichiers modifiés sont envoyés, jamais pendant une alarme. Ensuite MoveEye vérifie chaque adresse publique (statut, taille, type, redirections, Content-Security-Policy).</li>
it|<li><b>🌐 Homepage</b> (Altro → Homepage, solo l’amministratore): carica le tue pagine pubbliche sul tuo spazio web – pagina iniziale, radio del telefono (<code>Funk/</code>), simulatore nel browser (<code>Sim/</code>, solo il pacchetto firmato «sim-web.zip») e <code>Sim/test.html</code>. Indirizzo di fabbrica <code>https://kevlaschef.com</code> (solo https) e la chiave di caricamento: mai più mostrata, mai nel registro; un nuovo indirizzo la cancella. Vengono caricati solo i file modificati, mai durante un allarme. Poi MoveEye verifica ogni indirizzo pubblico (stato, dimensione, tipo, reindirizzamenti, Content-Security-Policy).</li>
rm|<li><b>🌐 Pagina d’entrada</b> (Dapli → Pagina d’entrada, mo l’administratur): chargia tias paginas publicas sin tes spazi web – pagina d’entrada, radio dal telefonin (<code>Funk/</code>), simulatur en il browser (<code>Sim/</code>, mo il pachet signà «sim-web.zip») e <code>Sim/test.html</code>. Adressa da fabrica <code>https://kevlaschef.com</code> (mo https) e la clav da chargiar: mai pli mussada, mai en il protocol; ina nova adressa la stizza. Chargià vegn mo quai ch’è midà, mai durant in alarm. Suenter controllescha MoveEye mintga adressa publica (status, grondezza, tip, deviaziuns, Content-Security-Policy).</li>
"""


def _help_hp(doc, lang):
    try:
        li = dict(x.split("|", 1) for x in HP_HELP_HTML.strip().split("\n") if "|" in x).get(lang)
    except ValueError:
        li = None
    i = doc.find('<section id="morse"')
    j = doc.find("</ul></section>", i)
    return doc if not li or i < 0 or j < 0 or "🌐 " in doc[i:j] else doc[:j] + li + doc[j:]


_hp_en_hp = HELP_PAGE.find('<div lang="en">')
if _hp_en_hp > 0:
    HELP_PAGE = _help_hp(HELP_PAGE[:_hp_en_hp], "de") + _help_hp(HELP_PAGE[_hp_en_hp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_hp(HELP_X[_L], _L)


# ---- self-test (only for --self-test) ----------------------------------------------------------------------------------------------
def homepage_selftest():
    for k, v in HP_TEXTS.items():
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), "639zzzh: text " + k
    assert "hp_key" in USER_SETTINGS_DENY and "hp_key" in APPKEY_DENY_KEYS and "/api/homepage" in APPKEY_DENY_PATHS
    assert not any(t[1] == "hp_key" for t in TEXTS), "the key is no schema text (never in /api/state)"
    assert hp_base_ok("https://kevlaschef.com") and not hp_base_ok("http://kevlaschef.com") and not hp_base_ok("https://a.b/x?y")
    o = "https://kevlaschef.com"
    assert any("connect-src" in k for k, _ in hp_csp("default-src 'self'; connect-src 'none'", o))
    assert any("wasm-unsafe-eval" in k for k, _ in hp_csp("script-src 'self' 'unsafe-inline'", o))
    assert not hp_csp("default-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'", o)
    f = hp_funk_files()
    assert set(f) == {"index.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png"}, sorted(f)
    assert all(_HP_NAME_RE.match(n) for n in f) and all(_HP_NAME_RE.match(n) for n in HP_SIM_NAMES)
    assert "Funk/" in HP_INDEX_HTML and "Sim/" in HP_INDEX_HTML and "index_audio_worklet.js" in HP_TEST_HTML
    k0 = CFG.get("hp_key")
    try:
        CFG["hp_key"] = "SelbsttestSchluessel123"
        assert "SelbsttestSchluessel123" not in json.dumps(hp_status()) and "•••" in _hp_clean("x SelbsttestSchluessel123")
    finally:
        CFG["hp_key"] = k0
    return True


SELFTEST_EXTRA.append(("Homepage: web space upload, check of the public addresses, texts (639zzzh)", homepage_selftest))
