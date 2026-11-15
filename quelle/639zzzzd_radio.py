#@ MoveEye – Teil 639zzzzd: «📻 Radio» – Internet-Radio auf dem Lautsprecher (Sender aus dem offenen Verzeichnis radio-browser.info oder eine eigene Adresse), Einschlaf-Timer, Radio als Wecker; Sirene, Ansagen, Morse und Wecker gehen vor. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026). Mehr → «📻 Radio» (/radio, /api/radio), Fenster: Mehr → «📻 Radio».
#  Sender     CFG radio_stations (pro Gerät): {id, name, sub, uuid | url | find}. Ab Werk «Radio Pilatus» (Luzern) als
#             find = Name + Land im Verzeichnis: beim ersten Abspielen wird der Sender dort gesucht und seine stationuuid
#             gemerkt. KEINE eingebaute Stream-Adresse (keine von Radio Pilatus selbst bestätigte gefunden - Besitzer-Regel:
#             keine geratene Adresse). Der Besitzer sucht weitere im Verzeichnis (über den Pi: ein User-Agent, die Server-Liste
#             wie empfohlen über /json/servers bzw. DNS von all.api.radio-browser.info) oder fügt eine Adresse ein; ordnen, entfernen.
#  Abspielen  die Adresse wird JEDES Mal frisch geholt (uuid → /json/url/<uuid>, das zählt auch den Klick wie radio-browser
#             es wünscht; sonst byuuid → url_resolved), dann Wiedergabelisten (.pls / .m3u, verschachtelt bis 3) aufgelöst.
#             Eigener kleiner HTTP-Leser (HTTP/1.0, Weiterleitungen, auch «ICY 200 OK» alter Shoutcast-Server) mit
#             «Icy-MetaData: 1»: der Titel («StreamTitle») kommt aus dem Strom, der Ton geht ohne die Titel an ffmpeg
#             (stdin → 44.1 kHz mono s16), der Pi rechnet die Lautstärke (eigener Regler radio_volume, nicht die Sirene) und
#             schreibt auf denselben Lautsprecher wie alle Töne (out_cmd, Teil 250: aplay / Bluetooth). HLS (.m3u8) liest
#             ffmpeg selbst (dann ohne Titel). ffmpeg und aplay laufen mit nice 5 und PR_SET_PDEATHSIG: stirbt MoveEye, gehen sie mit.
#  Vorrang    Sirene / alle Töne (sound_play), Ansagen (Piper / alte Stimme = sound_play «tts»), Gegensprechen (talk_chunk),
#             Morse / Funk senden (morse_beep_play) rufen radio_yield() BEVOR sie den Lautsprecher öffnen: das Radio gibt den
#             Lautsprecher sofort frei (aplay beendet, ohne auf eine Sperre zu warten) und spielt 1.5 s nach dem Ende weiter -
#             derselbe Strom, kein neues Verbinden. Ebenso pausiert es, solange der Wecker klingelt (mit Ton) und solange das
#             Mikrofon im Morse-Modus Ton / Funk empfängt (sonst hört es das Radio = Rückkopplung; die Seite sagt das).
#             Pausiert es länger als 60 s, wird der Strom getrennt (Datenmenge) und danach neu verbunden.
#             Solange das Radio spielt, hört der Geräusch-Alarm (und der Klatschschalter) nicht mit - wie bei jedem Ton.
#  Ohne Netz  kein endloses Wiederholen: nach 5, 10, 20, 40, 80 s aufgeben (RADIO_BACKOFF), Hinweis «Kein Internet» auf der Karte.
#  Timer      Einschlaf-Timer 15 / 30 / 60 / 90 min, die letzten 45 s leiser bis aus.
#  Wecker     Weckton «📻 <Sender>» (wake_sound = radio:<id>, Teil 255 _ring_sound): spielt nichts nach 10 s (kein Netz, Strom
#             bricht ab), nimmt der Wecker seine Melodie. Lauter werdend wie die Melodie.
#  Rechte     ansehen: alle; abspielen / stoppen / Lautstärke / Timer: wer Töne darf (Recht «siren», wie /api/audio), die
#             Senderliste: nur der Administrator (nicht im Bedienermodus).
#  Favoriten  für den Zweig «★ Favoriten» (mw-favoriten, noch nicht auf main): radio_fav_items() liefert
#             page:/radio · Schalter radio:on (POST /api/radio {"action": "toggle"}) · je Sender radio:play:<id>
#             (POST /api/radio {"action": "play", "id": <id>}).
# Test: werkzeuge/radio_test.py (falsches Verzeichnis, lokaler Teststrom mit ICY, nie das echte Internet).
# ----------------------------------------------------------------------------
import socket as _rsock

RADIO_UA = "MoveEye/" + APP_VERSION + " (internet radio; github.com/DonElektro/MotionWatch)"
RADIO_DISCOVER = "https://all.api.radio-browser.info"   # the server list (they ask apps not to hard-code one server)
RADIO_RATE = 44100
RADIO_CHUNK = RADIO_RATE // 10 * 2      # bytes of 0.1 s (mono s16)
RADIO_MAX = 40
RADIO_BACKOFF = (5.0, 10.0, 20.0, 40.0, 80.0)    # s between the tries; after the last one the radio gives up
RADIO_WAKE_S = 10.0                     # the wake-up alarm: no sound after 10 s = the tone
RADIO_FIRST_S = 20.0                    # otherwise: no sound after 20 s = a failed try
RADIO_FADE_S = 45.0
RADIO_SLEEP = (0, 15, 30, 60, 90)
RADIO_GAP_S = 1.5                       # after a sound of MoveEye the radio waits this long
RADIO_HELD_DROP_S = 60.0
RADIO_PLAY_ACTIONS = ("play", "stop", "toggle", "volume", "sleep", "bplay", "bstop")      # bplay / bstop: «📱 dieser Browser»
RADIO_BR_MAX = 2                        # listeners at the same time through /radio/stream/<id> (the Pi passes the stream on)
RADIO_BR_TTL = 600.0                    # a resolved address for the browser stays this long (the proxy only takes these)
RADIO_DEF = {"radio_stations": [{"id": "pilatus", "name": "Radio Pilatus", "sub": "Luzern", "find": {"name": "Radio Pilatus", "cc": "CH"}}],
             "radio_volume": 40, "radio_last": "pilatus"}
for _k, _v in RADIO_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
USER_SETTINGS_DENY.update({"radio_stations", "radio_last"})
APPKEY_DENY_KEYS.update({"radio_stations"})
VIEW_GET_PAGES.add("/radio")
VIEW_GET = VIEW_GET + ("/api/radio",)
PERM_GET["siren"] = tuple(PERM_GET.get("siren", ())) + ("/radio/stream/",)    # the proxy: the same right as playing
_RADIO_ID = re.compile(r"^[a-z0-9]{1,16}$")
_RADIO_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_RADIO_PL_CT = ("audio/x-scpls", "audio/scpls", "audio/x-mpegurl", "audio/mpegurl", "application/x-mpegurl", "application/vnd.apple.mpegurl",
                "application/pls+xml", "text/plain")
_RADIO_FMT = {"audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/mpeg3": "mp3", "audio/aac": "aac", "audio/aacp": "aac", "audio/x-aac": "aac",
              "audio/ogg": "ogg", "application/ogg": "ogg", "audio/opus": "ogg", "audio/flac": "flac", "audio/x-flac": "flac"}
RADIO = {"want": False, "gen": 0, "sid": "", "name": "", "title": "", "state": "off", "msg": "", "offline": False, "err_n": 0, "retry_at": 0.0,
         "t_audio": 0.0, "hold_t": 0.0, "hold_why": "", "held": "", "sleep_until": 0.0, "sleep_min": 0, "fade": 1.0, "wake": False,
         "wake_t0": 0.0, "wake_fail": 0.0, "wvol": 0.0, "out": None, "dec": None, "conn": None, "thread": None, "ev": threading.Event(),
         "lock": threading.RLock(), "olock": threading.Lock(), "tries": deque(maxlen=30), "net_err": "", "servers": [], "srv_t": 0.0}


def _radio_txt(s, n=60):
    return re.sub(r"[\x00-\x1f\x7f]+", " ", str(s or "")).strip()[:n]


def radio_url_ok(u):
    """an address to play: http(s), a host, no user / password, no spaces"""
    if not isinstance(u, str) or len(u) > 500 or not re.match(r"^https?://[^\s/@]+(/[^\s]*)?$", u, re.I):
        return False
    try:
        from urllib.parse import urlsplit
        h = urlsplit(u).hostname or ""
        return bool(h) and ".." not in h and not h.startswith((".", "-"))
    except ValueError:
        return False


def radio_clean(lst):
    out, ids = [], set()
    for x in (lst if isinstance(lst, list) else [])[:RADIO_MAX]:
        if not isinstance(x, dict) or not _RADIO_ID.match(str(x.get("id") or "")) or x["id"] in ids:
            continue
        e = {"id": x["id"], "name": _radio_txt(x.get("name")), "sub": _radio_txt(x.get("sub"))}
        if _RADIO_UUID.match(str(x.get("uuid") or "")):
            e["uuid"] = x["uuid"]
        if radio_url_ok(x.get("url")):
            e["url"] = x["url"]
        f = x.get("find")
        if isinstance(f, dict) and _radio_txt(f.get("name")):
            e["find"] = {"name": _radio_txt(f.get("name")), "cc": str(f.get("cc") or "")[:2].upper() if re.match(r"^[A-Za-z]{2}$", str(f.get("cc") or "")) else ""}
        if e["name"] and ("uuid" in e or "url" in e or "find" in e):
            ids.add(e["id"]); out.append(e)
    return out


def radio_list():
    return radio_clean(CFG.get("radio_stations"))


def radio_station(sid):
    for e in CFG.get("radio_stations") or []:
        if isinstance(e, dict) and e.get("id") == sid:
            return e
    return None


# ---- a small HTTP reader (HTTP/1.0: no chunks; also «ICY 200 OK» of old Shoutcast servers) -------------------------------------
def _rh_open(url, timeout=8.0, icy=False):
    """-> (code, headers (lower case), file, socket, final address); follows up to 5 redirects"""
    import ssl
    from urllib.parse import urlsplit, urljoin, quote
    for _hop in range(6):
        if not radio_url_ok(url):
            raise ValueError("not a valid address")
        u = urlsplit(url)
        port = u.port or (443 if u.scheme.lower() == "https" else 80)
        s = _rsock.create_connection((u.hostname, port), timeout)
        try:
            if u.scheme.lower() == "https":
                s = ssl.create_default_context().wrap_socket(s, server_hostname=u.hostname)
            path = quote((u.path or "/") + ("?" + u.query if u.query else ""), safe="/?&=%:+,;!$'()*~-._@")
            s.sendall(("GET %s HTTP/1.0\r\nHost: %s\r\nUser-Agent: %s\r\nAccept: */*\r\n%sConnection: close\r\n\r\n"
                       % (path, u.netloc, RADIO_UA, "Icy-MetaData: 1\r\n" if icy else "")).encode("latin-1", "replace"))
            f = s.makefile("rb")
            m = re.match(rb"^(?:HTTP/\d(?:\.\d)?|ICY) (\d{3})", f.readline(4096))
            if not m:
                raise ValueError("no HTTP answer")
            code, hdr = int(m.group(1)), {}
            for _i in range(100):
                ln = f.readline(8192)
                if ln in (b"\r\n", b"\n", b""):
                    break
                k, _sep, v = ln.decode("latin-1").partition(":")
                hdr[k.strip().lower()] = v.strip()
        except Exception:
            s.close(); raise
        if code in (301, 302, 303, 307, 308) and hdr.get("location"):
            s.close(); url = urljoin(url, hdr["location"]); continue
        return code, hdr, f, s, url
    raise ValueError("too many redirects")


def _rh_get(url, timeout=8.0, limit=2 << 20):
    code, _h, f, s, _u = _rh_open(url, timeout)
    try:
        data = f.read(limit)
    finally:
        s.close()
    if code != 200:
        raise ValueError("HTTP %d" % code)
    return data


def radio_offline_err(e):
    """does the error mean «no internet» (name not found, network unreachable, no answer at all)?"""
    import errno
    return isinstance(e, (_rsock.gaierror, _rsock.timeout, TimeoutError)) or getattr(e, "errno", None) in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN)


# ---- the open directory radio-browser.info --------------------------------------------------------------------------------------
def radio_servers(force=False):
    """the API servers: /json/servers of the discovery name (as radio-browser recommends), else its DNS names; 6 h in memory.
    MW_RADIO_DISCOVER (tests): another discovery address - then never the real DNS."""
    now = time.time()
    if RADIO["servers"] and not force and now - RADIO["srv_t"] < 6 * 3600:
        return list(RADIO["servers"])
    env = os.environ.get("MW_RADIO_DISCOVER", "").strip()
    base = env or RADIO_DISCOVER
    sch = "http" if base.lower().startswith("http://") else "https"
    names = []
    try:
        for x in json.loads(_rh_get(base.rstrip("/") + "/json/servers", 6.0, 200000).decode("utf-8", "replace")):
            n = str((x or {}).get("name") or "").lower()
            if re.match(r"^[a-z0-9.\-]{3,80}(:\d{2,5})?$", n) and (env or n.endswith(".api.radio-browser.info")) and n not in names:
                names.append(n)
    except Exception:
        pass
    if not names and not env:
        try:
            for ip in {a[4][0] for a in _rsock.getaddrinfo("all.api.radio-browser.info", 443, proto=_rsock.IPPROTO_TCP)}:
                try:
                    n = _rsock.gethostbyaddr(ip)[0].lower()
                    if n.endswith(".api.radio-browser.info") and n not in names:
                        names.append(n)
                except OSError:
                    pass
        except OSError:
            pass
    if not names:
        names = [base.split("://", 1)[1].strip("/")] if env else ["all.api.radio-browser.info"]
    import random
    random.shuffle(names)
    RADIO["servers"] = [sch + "://" + n for n in names[:8]]; RADIO["srv_t"] = now
    return list(RADIO["servers"])


def radio_api(path, timeout=8.0):
    """GET a JSON answer of the directory; tries up to 3 servers"""
    last = None
    for srv in radio_servers()[:3]:
        try:
            j = json.loads(_rh_get(srv + path, timeout).decode("utf-8", "replace"))
            if RADIO["servers"] and RADIO["servers"][0] != srv and srv in RADIO["servers"]:
                RADIO["servers"].remove(srv); RADIO["servers"].insert(0, srv)
            return j
        except Exception as e:
            last = e
    RADIO["srv_t"] = 0.0                                     # next time: the server list again
    raise last if last is not None else ValueError("no directory server")


def _radio_hit(x):
    if not isinstance(x, dict) or not _RADIO_UUID.match(str(x.get("stationuuid") or "")):
        return None
    try:
        br = max(0, min(9999, int(x.get("bitrate") or 0)))
    except (TypeError, ValueError):
        br = 0
    return {"uuid": x["stationuuid"], "name": _radio_txt(x.get("name")), "cc": _radio_txt(x.get("countrycode"), 2).upper(),
            "country": _radio_txt(x.get("country"), 40), "codec": _radio_txt(x.get("codec"), 10), "bitrate": br, "tags": _radio_txt(x.get("tags"), 60),
            "url": x.get("url_resolved") or x.get("url") or ""}


def radio_search(q, cc=""):
    from urllib.parse import urlencode
    q = _radio_txt(q, 60)
    if len(q) < 2:
        return None, "type at least 2 letters"
    p = {"name": q, "hidebroken": "true", "order": "clickcount", "reverse": "true", "limit": "25"}
    if re.match(r"^[A-Za-z]{2}$", str(cc or "")):
        p["countrycode"] = cc.upper()
    try:
        lst = radio_api("/json/stations/search?" + urlencode(p))
    except Exception as e:
        return None, "no internet - the directory cannot be reached" if radio_offline_err(e) else "the directory does not answer"
    return [h for h in (_radio_hit(x) for x in (lst if isinstance(lst, list) else [])) if h and h["name"]][:25], ""


def radio_resolve(st):
    """the stream address of a station NOW (the directory first, so a changed address keeps working)"""
    from urllib.parse import urlencode, quote
    if st.get("uuid"):
        try:
            u = (radio_api("/json/url/" + st["uuid"]) or {}).get("url")      # counts the click (asked by radio-browser)
        except Exception:
            u = None
        if not radio_url_ok(u):
            lst = radio_api("/json/stations/byuuid/" + st["uuid"])
            h = _radio_hit(lst[0]) if isinstance(lst, list) and lst else None
            u = h["url"] if h else None
            if not h and st.get("find"):
                st.pop("uuid", None)                        # not in the directory any more: look for it again by name
        if radio_url_ok(u):
            return u
    if st.get("find"):
        f = st["find"]
        p = {"name": f["name"], "hidebroken": "true", "order": "votes", "reverse": "true", "limit": "10"}
        if f.get("cc"):
            p["countrycode"] = f["cc"]
        hits = [h for h in (_radio_hit(x) for x in (radio_api("/json/stations/search?" + urlencode(p)) or [])) if h]
        best = next((h for h in hits if h["name"].casefold() == f["name"].casefold()), hits[0] if hits else None)
        if not best:
            raise ValueError("the station is not in the directory")
        with RADIO["lock"]:
            st["uuid"] = best["uuid"]
            if not st.get("sub"):
                st["sub"] = " · ".join(x for x in (best["country"], best["codec"]) if x)
        save_settings()
        try:
            u = (radio_api("/json/url/" + quote(best["uuid"])) or {}).get("url")
        except Exception:
            u = None
        u = u if radio_url_ok(u) else best["url"]
        if radio_url_ok(u):
            return u
    if radio_url_ok(st.get("url")):
        return st["url"]
    raise ValueError("the station has no address")


def radio_playlist_urls(txt, base):
    """the addresses of a .pls / .m3u list (relative ones made absolute)"""
    from urllib.parse import urljoin
    pls = "[playlist]" in txt[:2000].lower()
    out = []
    for ln in txt.splitlines()[:500]:
        s = ln.strip()
        m = re.match(r"(?i)^file\d+\s*=\s*(\S+)$", s)
        v = m.group(1) if m else (s if not pls and s and not s.startswith(("#", "[")) and "=" not in s.split("://", 1)[0] else None)
        if v:
            v = urljoin(base, v)
            if radio_url_ok(v) and v not in out:
                out.append(v)
    return out[:10]


def radio_open(url, depth=0):
    """open the stream; a play list is read and its first working entry opened -> dict(kind icy | hls, ...)"""
    from urllib.parse import urlsplit
    code, hdr, f, s, final = _rh_open(url, 10.0, icy=True)
    ok = False
    try:
        if code != 200:
            raise ValueError("HTTP %d" % code)
        ct = hdr.get("content-type", "").split(";")[0].strip().lower()
        path = urlsplit(final).path.lower()
        if ct in _RADIO_PL_CT or (ct.startswith("text/") and not ct.startswith("text/html")) or path.endswith((".pls", ".m3u", ".m3u8")):
            txt = f.read(65536).decode("utf-8", "replace")
            if "#EXT-X-" in txt:
                return {"kind": "hls", "url": final, "ct": ct}
            if depth >= 3:
                raise ValueError("play list in a play list too often")
            urls = radio_playlist_urls(txt, final)
            if not urls:
                raise ValueError("the play list has no stream address")
            last = None
            for u in urls[:3]:
                try:
                    return radio_open(u, depth + 1)
                except Exception as e:
                    last = e
            raise last
        if ct.startswith("text/html"):
            raise ValueError("this is a web page, not a stream")
        try:
            mi = max(0, min(1 << 20, int(hdr.get("icy-metaint") or 0)))
        except ValueError:
            mi = 0
        ok = True
        return {"kind": "icy", "f": f, "sock": s, "url": final, "ct": ct, "metaint": mi}
    finally:
        if not ok:
            s.close()


def radio_icy_title(meta):
    m = re.search(rb"StreamTitle='(.*?)';(?:Stream|\s*$|\x00)", meta + b"\x00", re.S)
    if not m:
        return None
    raw = m.group(1)
    try:
        t_ = raw.decode("utf-8")
    except UnicodeDecodeError:
        t_ = raw.decode("latin-1")
    return _radio_txt(t_, 120)


# ---- playing ----------------------------------------------------------------------------------------------------------------------
_RADIO_PRCTL = []


def _radio_prctl():
    """prctl of the C library, looked up in MoveEye itself (after fork only the call happens: no loader lock in the child)"""
    if not _RADIO_PRCTL:
        try:
            import ctypes
            _RADIO_PRCTL.append(ctypes.CDLL(None, use_errno=True).prctl)
        except Exception:
            _RADIO_PRCTL.append(None)
    return _RADIO_PRCTL[0]


def _radio_pre():                                            # child processes: a bit lower priority, die with MoveEye
    try:
        os.nice(5)
    except OSError:
        pass
    f = _RADIO_PRCTL[0] if _RADIO_PRCTL else None
    if f is not None:
        try:
            f(1, 9)                                          # PR_SET_PDEATHSIG = SIGKILL (the thread that started it ends = it ends)
        except Exception:
            pass


def _radio_kill(p):
    if p is None:
        return
    try:
        if p.poll() is None:
            p.kill()
        p.wait(timeout=2)
    except Exception:
        pass


def radio_held(now=None):
    """why the radio must be quiet now ("" = it may play)"""
    now = time.time() if now is None else now
    try:
        if SOUND.get("playing"):
            k = str(SOUND.get("kind") or "")
            return "wake" if WAKE.get("state") == "ring" else "voice" if k == "tts" else "morse" if k == "morse" else "siren" if k in SOUND_KINDS or k.startswith("file:") else "sound"
        if TALK.get("proc") is not None:
            return "talk"
        if MORSE.get("tx") is not None:
            return "morse"
        if MORSE.get("until") and morse_on() and (CFG.get("morse_rx_sound") or funk_on()):
            return "mic"
        if WAKE.get("state") == "ring" and not RADIO["wake"]:
            return "wake"
    except Exception:
        pass
    return (RADIO["hold_why"] or "sound") if now - RADIO["hold_t"] < RADIO_GAP_S else ""


def radio_yield(why="sound"):
    """250 / 370 / 639zzz call this BEFORE they open the loudspeaker: the radio lets it go at once (never waits long)"""
    if not RADIO["want"]:
        return
    got = RADIO["olock"].acquire(timeout=0.3)
    try:
        RADIO["hold_t"] = time.time(); RADIO["hold_why"] = why
        p = RADIO["out"]; RADIO["out"] = None
    finally:
        if got:
            RADIO["olock"].release()
    _radio_kill(p)


def radio_play(sid=None, who="web", wake=False, vol=None):
    """-> (ok, English error); the station plays in the background"""
    sid = sid or CFG.get("radio_last") or ((radio_list() or [{}])[0].get("id"))
    st = radio_station(sid) if sid else None
    if not st or not radio_clean([st]):
        return False, "unknown station"
    if not out_selected():
        return False, "no loudspeaker selected"
    if not shutil.which("ffmpeg"):
        return False, "ffmpeg is missing (sudo apt install ffmpeg)"
    keep_sleep = RADIO["sleep_until"] if RADIO["want"] and not wake else 0.0
    radio_stop("another station", quiet=True)
    with RADIO["lock"]:
        RADIO["gen"] += 1; gen = RADIO["gen"]
        RADIO.update(want=True, sid=sid, name=st["name"], title="", state="connecting", msg="", offline=False, err_n=0, retry_at=0.0, t_audio=0.0,
                     held="", sleep_until=keep_sleep, sleep_min=RADIO["sleep_min"] if keep_sleep else 0, fade=1.0, wake=bool(wake),
                     wake_t0=time.time() if wake else 0.0, wvol=float(vol or 0.0), net_err="")
        RADIO["ev"].clear()
        th = threading.Thread(target=_radio_session, args=(gen,), daemon=True, name="radio")
        RADIO["thread"] = th
    if not wake and CFG.get("radio_last") != sid:
        CFG["radio_last"] = sid; save_settings()
    th.start()
    log_event("sys", f"Radio: {st['name']} ({who})"[:160])
    return True, ""


def radio_stop(why="button", who="", quiet=False):
    with RADIO["lock"]:
        was = RADIO["want"] or RADIO["thread"] is not None
        RADIO["want"] = False; RADIO["gen"] += 1
        RADIO["ev"].set()
        th = RADIO["thread"]; RADIO["thread"] = None
        c = RADIO["conn"]
    if c is not None:
        try:
            c.shutdown(_rsock.SHUT_RDWR)
        except OSError:
            pass
    _radio_kill(RADIO["dec"]); _radio_kill(RADIO["out"])
    if th is not None and th is not threading.current_thread():
        th.join(timeout=4)
    RADIO.update(state="off", held="", sleep_until=0.0, sleep_min=0, wake=False, title="")
    if was and not quiet:
        log_event("sys", f"Radio off ({why}{', ' + who if who else ''})"[:160])
    return was


def _radio_session(gen):
    """one thread per play: it starts and ends ffmpeg / aplay itself (PR_SET_PDEATHSIG follows this thread)"""
    alive = lambda: RADIO["gen"] == gen and RADIO["want"]
    try:
        while alive():
            how, err = _radio_once(gen)
            if not alive() or how == "stop":
                break
            if how == "held":                                # paused long: wait until MoveEye is quiet, then connect again
                while alive() and radio_held():
                    RADIO["ev"].wait(0.5)
                continue
            if how == "fatal":
                RADIO.update(want=False, state="error", msg=err)
                break
            now = time.time()
            if how == "drop":                                # it played a while: the next try counts from the start
                RADIO["err_n"] = 0
            RADIO["err_n"] += 1
            RADIO["tries"].append((round(now, 2), err[:80]))
            if RADIO["wake"]:
                RADIO.update(wake_fail=now, want=False, state="error", msg=err)
                log_event("sys", f"Radio as wake-up alarm: {err} - the alarm takes its tone"[:160])
                break
            if RADIO["err_n"] > len(RADIO_BACKOFF):
                RADIO.update(want=False, state="offline" if RADIO["offline"] else "error", msg=err)
                log_event("sys", f"Radio: given up after {RADIO['err_n']} tries ({err})"[:160])
                break
            d = RADIO_BACKOFF[RADIO["err_n"] - 1]
            RADIO.update(state="retry", msg=err, retry_at=now + d)
            RADIO["ev"].wait(d)
    except Exception as e:                                   # never let the thread die silently
        RADIO.update(want=False, state="error", msg=str(e)[:160])
    finally:
        if RADIO["gen"] == gen:
            _radio_kill(RADIO["dec"]); _radio_kill(RADIO["out"])
            RADIO["out"] = RADIO["dec"] = RADIO["conn"] = None
            if not RADIO["want"]:
                RADIO.update(sleep_until=0.0, sleep_min=0, held="", fade=1.0)
                if RADIO["state"] not in ("error", "offline"):
                    RADIO["state"] = "off"
            RADIO["thread"] = None if RADIO["thread"] is threading.current_thread() else RADIO["thread"]


def _radio_reader(gen, src, w):
    """network -> ffmpeg; takes the titles out of the stream (ICY)"""
    f, mi = src["f"], src["metaint"]
    try:
        while RADIO["gen"] == gen:
            data = f.read(mi) if mi else f.read(8192)
            if not data:
                RADIO["net_err"] = RADIO["net_err"] or "the station stopped sending"
                break
            w.write(data)
            if mi:
                n = f.read(1)
                if not n:
                    break
                if n[0]:
                    t_ = radio_icy_title(f.read(n[0] * 16))
                    if t_ is not None:
                        RADIO["title"] = t_
    except (OSError, ValueError) as e:
        if RADIO["gen"] == gen:
            RADIO["net_err"] = "the station stopped sending" if isinstance(e, (_rsock.timeout, TimeoutError)) else (RADIO["net_err"] or "")
    finally:
        for c in (w, src["sock"]):
            try:
                c.close()
            except Exception:
                pass


def _radio_once(gen):
    """connect, decode and play until the stream ends -> (how, English error); how = stop | fail | drop | held | fatal"""
    st = radio_station(RADIO["sid"])
    if st is None:
        return "fatal", "unknown station"
    RADIO.update(state="connecting", t_audio=0.0, net_err="")
    try:
        src = radio_open(radio_resolve(st))
    except Exception as e:
        RADIO["offline"] = radio_offline_err(e)
        return "fail", "no internet" if RADIO["offline"] else "the station does not answer: " + _radio_txt(e, 100)
    RADIO["offline"] = False
    if RADIO["gen"] != gen:
        if src.get("sock"):
            src["sock"].close()
        return "stop", ""
    hls = src["kind"] == "hls"
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-threads", "1"]
    cmd += (["-user_agent", RADIO_UA, "-i", src["url"]] if hls else (["-f", _RADIO_FMT[src["ct"]]] if src["ct"] in _RADIO_FMT else []) + ["-i", "pipe:0"])
    cmd += ["-vn", "-ac", "1", "-ar", str(RADIO_RATE), "-f", "s16le", "pipe:1"]
    errf = tempfile.TemporaryFile()
    _radio_prctl()
    try:
        dec = subprocess.Popen(cmd, stdin=subprocess.DEVNULL if hls else subprocess.PIPE, stdout=subprocess.PIPE, stderr=errf, preexec_fn=_radio_pre)
    except OSError as e:
        errf.close()
        if src.get("sock"):
            src["sock"].close()
        return "fatal", "ffmpeg: " + str(e)[:100]
    RADIO["dec"] = dec
    mine = []                                                # the loudspeaker processes of this call (only these are ended here)
    if not hls:
        RADIO["conn"] = src["sock"]
        threading.Thread(target=_radio_reader, args=(gen, src, dec.stdin), daemon=True, name="radio-net").start()
    t0 = time.time(); first = RADIO_WAKE_S if RADIO["wake"] else RADIO_FIRST_S
    watch = threading.Timer(first, lambda: _radio_kill(dec) if RADIO["dec"] is dec and not RADIO["t_audio"] else None)
    watch.daemon = True; watch.start()
    how, err, ramp, held_t, fatal = "fail", "", 0, 0.0, ""
    try:
        while RADIO["gen"] == gen and RADIO["want"]:
            chunk = dec.stdout.read(RADIO_CHUNK)
            if not chunk:
                break
            now = time.time()
            if not RADIO["t_audio"]:
                RADIO.update(t_audio=now, state="playing", err_n=0 if not RADIO["err_n"] else RADIO["err_n"])
            if RADIO["sleep_until"]:
                left = RADIO["sleep_until"] - now
                if left <= 0:
                    RADIO.update(want=False, msg="sleep timer: the radio is off")
                    log_event("sys", "Radio off (sleep timer)")
                    how = "stop"; break
                RADIO["fade"] = min(1.0, left / RADIO_FADE_S)
            else:
                RADIO["fade"] = 1.0
            why = radio_held(now)
            kill = None
            if why:
                held_t = held_t or now
                with RADIO["olock"]:
                    kill = RADIO["out"]; RADIO["out"] = None
                RADIO["held"] = why
                _radio_kill(kill)
                if now - held_t > RADIO_HELD_DROP_S:
                    how = "held"; break
                continue
            held_t = 0.0; RADIO["held"] = ""
            o = RADIO["out"]
            if o is None or o.poll() is not None:
                ocmd, oerr = out_cmd(RADIO_RATE)             # Bluetooth may connect first: not under the lock
                if ocmd is None:
                    fatal = oerr; break
                with RADIO["olock"]:
                    if radio_held() or RADIO["gen"] != gen:
                        continue
                    try:
                        o = subprocess.Popen(ocmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=_radio_pre)
                    except OSError as e:
                        fatal = "loudspeaker: " + str(e)[:100]; break
                    RADIO["out"] = o; mine.append(o)
                ramp = 0
            vol = RADIO["wvol"] if RADIO["wake"] else float(CFG.get("radio_volume", 40))
            y = np.frombuffer(chunk[:len(chunk) // 2 * 2], dtype="<i2").astype(np.float32) * ((max(0.0, min(100.0, vol)) / 100.0) ** 2 * RADIO["fade"])
            if ramp < RADIO_RATE // 3:                       # 0.3 s softly in after (re)opening: no click
                k = np.minimum(1.0, (ramp + np.arange(y.size, dtype=np.float32)) / (RADIO_RATE / 3.0)); y *= k; ramp += y.size
            try:
                o.stdin.write(np.clip(y, -32768, 32767).astype("<i2").tobytes())
            except (BrokenPipeError, OSError, ValueError):
                with RADIO["olock"]:
                    if RADIO["out"] is o:
                        RADIO["out"] = None
                _radio_kill(o)
            if AUDIO is not None:
                AUDIO.mute_until = now + 2.0                 # the noise alarm does not hear the radio
    except (OSError, ValueError) as e:
        err = str(e)[:100]
    finally:
        watch.cancel()
        _radio_kill(dec)
        with RADIO["olock"]:
            if RADIO["out"] in mine:
                RADIO["out"] = None
        for o in mine:
            _radio_kill(o)
        if RADIO["dec"] is dec:
            RADIO["dec"] = RADIO["conn"] = None
        try:
            errf.seek(0); fe = errf.read()[-400:].decode(errors="replace").strip().splitlines()
        except Exception:
            fe = []
        errf.close()
    if fatal:
        return "fatal", fatal
    if how in ("stop", "held") or RADIO["gen"] != gen or not RADIO["want"]:
        return how if how == "held" else "stop", ""
    if RADIO["t_audio"] and time.time() - RADIO["t_audio"] > 30:
        return "drop", RADIO["net_err"] or "the station stopped sending"
    if not RADIO["t_audio"]:
        return "fail", "no sound from the station" if time.time() - t0 >= first - 0.5 else ("the station sends no sound" + (": " + fe[-1][:80] if fe else ""))
    return "fail", RADIO["net_err"] or err or (fe[-1][:80] if fe else "the station stopped sending")


def radio_sleep(minutes):
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return False, "invalid value"
    if m not in RADIO_SLEEP:
        return False, "invalid value"
    if m and not RADIO["want"]:
        return False, "the radio is off"
    RADIO.update(sleep_min=m, sleep_until=time.time() + m * 60.0 if m else 0.0, fade=1.0)
    return True, ""


# ---- the wake-up alarm with a station (255 _ring_sound) ------------------------------------------------------------------------
def radio_wake_pairs():
    return [("radio:" + e["id"], "📻 " + e["name"]) for e in radio_list()]


def radio_wake_sound(kind, now):
    """True = the radio rings (or is connecting); False = the wake-up alarm takes its tone"""
    sid = str(kind)[6:]
    t0 = WAKE.get("t0") or 0.0
    if RADIO["wake_fail"] and RADIO["wake_fail"] >= t0:
        return False
    full = float(CFG.get("wake_volume", 60))
    lvl = full * min(1.0, 0.4 + 0.6 * max(0.0, now - t0) / 120.0)
    if not (RADIO["want"] and RADIO["wake"] and RADIO["sid"] == sid):
        ok, err = radio_play(sid, "wake-up alarm", wake=True, vol=lvl)
        if not ok:
            RADIO["wake_fail"] = now; WAKE["msg"] = err
            log_event("sys", f"Radio as wake-up alarm: {err} - the alarm takes its tone"[:160])
            return False
        return True
    RADIO["wvol"] = lvl
    if not RADIO["t_audio"] and now - RADIO["wake_t0"] > RADIO_WAKE_S + 1.0:
        radio_stop("wake-up alarm: no sound", quiet=True)
        RADIO["wake_fail"] = now
        log_event("sys", "Radio as wake-up alarm: no sound after 10 s - the alarm takes its tone")
        return False
    return True


def radio_wake_end():
    if RADIO["wake"]:
        radio_stop("wake-up alarm off")


# ---- state, rights, actions (one entry for the web and the window) ------------------------------------------------------------
_RADIO_HELD_TXT = {"siren": "Paused: the siren / an alarm sound plays", "sound": "Paused: MoveEye plays a sound", "voice": "Paused: announcement",
                   "talk": "Paused: somebody talks through the loudspeaker", "morse": "Paused: Morse / radio signal is being sent",
                   "mic": "Paused: the microphone receives Morse / radio signals (no feedback)", "wake": "Paused: the wake-up alarm rings"}


def radio_tr(msg, L):
    """an English message, also «known text: detail» (the detail stays as it is)"""
    head, sep, rest = str(msg).partition(": ")
    if sep and head in _HX_RADIO:
        return tr(head, L) + ": " + rest
    return tr_err(msg, L)


def radio_may(role="admin", perms=None, edit=False, appkey=None):
    if role == "admin":
        return not (edit and CFG.get("lock_on"))
    return not edit and "siren" in set(perms if perms is not None else ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))


def radio_state(lang=None, role="admin", perms=None):
    L = norm_lang(lang or CFG.get("lang"))
    now = time.time()
    lst = radio_list()
    msg = RADIO["msg"]
    st = {"on": RADIO["want"], "state": RADIO["state"], "sid": RADIO["sid"], "name": RADIO["name"], "title": RADIO["title"],
          "msg": radio_tr(msg, L) if msg else "", "offline": bool(RADIO["offline"]) and RADIO["state"] in ("retry", "offline"),
          "held": tr(_RADIO_HELD_TXT[RADIO["held"]], L) if RADIO["want"] and RADIO["held"] in _RADIO_HELD_TXT else "",
          "vol": int(CFG.get("radio_volume", 40)), "wake": RADIO["wake"], "last": CFG.get("radio_last") or "",
          "sleep": {"min": RADIO["sleep_min"], "left": max(0, int(RADIO["sleep_until"] - now)) if RADIO["sleep_until"] else 0, "opts": list(RADIO_SLEEP)},
          "retry": {"in": max(0, int(RADIO["retry_at"] - now)), "n": RADIO["err_n"], "max": len(RADIO_BACKOFF) + 1} if RADIO["state"] == "retry" else None,
          "quiet": bool(CFG.get("noise_alarm") or CFG.get("clap_on")),     # Besitzer: say it on the card and the row
          "spk": bool(out_selected()), "ffmpeg": bool(shutil.which("ffmpeg")), "mic": bool(CFG.get("audio_in")),
          "wake_radio": str(CFG.get("wake_sound") or "").startswith("radio:"),
          "stations": [{"id": e["id"], "name": e["name"], "sub": e.get("sub", ""), "kind": "url" if ("url" in e and "uuid" not in e and "find" not in e) else "dir"} for e in lst],
          "may": {"play": radio_may(role, perms), "edit": radio_may(role, perms, True)}, "max": RADIO_MAX}
    return st


def radio_add(d):
    lst = list(CFG.get("radio_stations") or [])
    if len(lst) >= RADIO_MAX:
        return False, "the list is full"
    uuid, url = str(d.get("uuid") or ""), str(d.get("url") or "").strip()
    if uuid:
        if not _RADIO_UUID.match(uuid):
            return False, "invalid value"
        if any(e.get("uuid") == uuid for e in lst):
            return False, "the station is already in the list"
        try:
            got = radio_api("/json/stations/byuuid/" + uuid)
        except Exception as e:
            return False, "no internet - the directory cannot be reached" if radio_offline_err(e) else "the directory does not answer"
        h = _radio_hit(got[0]) if isinstance(got, list) and got else None
        if not h or not h["name"]:
            return False, "the station is not in the directory"
        import hashlib
        e = {"id": "b" + hashlib.sha1(uuid.encode()).hexdigest()[:12], "name": h["name"], "sub": " · ".join(x for x in (h["country"], (h["codec"] + (" %d kbit/s" % h["bitrate"] if h["bitrate"] else "")).strip()) if x), "uuid": uuid}
    else:
        if not radio_url_ok(url):
            return False, "not a valid address (http:// or https://)"
        if any(e.get("url") == url for e in lst):
            return False, "the station is already in the list"
        import hashlib
        from urllib.parse import urlsplit
        e = {"id": "u" + hashlib.sha1(url.encode()).hexdigest()[:12], "name": _radio_txt(d.get("name")) or urlsplit(url).hostname[:60],
             "sub": urlsplit(url).hostname[:60], "url": url}
    if any(x.get("id") == e["id"] for x in lst):
        return False, "the station is already in the list"
    with RADIO["lock"]:
        CFG["radio_stations"] = radio_clean(lst + [e])
    save_settings()
    log_event("sys", f"Radio: station added «{e['name']}»"[:160])
    return True, ""


def radio_do(d, who="web", role="admin", perms=None, appkey=None, lang=None):
    """an action of the page or of the window -> (HTTP code, answer)"""
    d = d if isinstance(d, dict) else {}
    L = norm_lang(lang or d.get("lang") or CFG.get("lang"))
    a = str(d.get("action") or "")
    edit = a not in RADIO_PLAY_ACTIONS
    if not radio_may(role, perms, edit):
        return 403, {"ok": False, "error": tr("Only for the administrator" if edit else "not allowed for your user", L)}

    def out(ok, err="", **kw):
        return (200 if ok else 400), dict({"ok": ok, "error": radio_tr(err, L) if err else None, "state": radio_state(L, role, perms)}, **kw)
    if a == "toggle":
        a = "stop" if RADIO["want"] else "play"
    if a == "bplay":                                         # «📱 dieser Browser»: the address for the <audio> of the page
        ok, err, src = radio_bplay(str(d.get("id") or "") or None)
        return out(ok, err, src=src)
    if a == "bstop":
        BR["sid"] = ""
        return out(True)
    if a == "play":
        return out(*radio_play(str(d.get("id") or "") or None, who))
    if a == "stop":
        radio_stop("button", who)
        RADIO["msg"] = ""
        return out(True)
    if a == "volume":
        try:
            CFG["radio_volume"] = int(max(0, min(100, float(d.get("v")))))
        except (TypeError, ValueError):
            return out(False, "invalid value")
        save_settings()
        return out(True)
    if a == "sleep":
        return out(*radio_sleep(d.get("min")))
    if a == "search":
        hits, err = radio_search(d.get("q"), d.get("cc") or "")
        have = {e.get("uuid") for e in CFG.get("radio_stations") or []}
        return out(hits is not None, err, hits=[dict({k: v for k, v in h.items() if k != "url"}, have=h["uuid"] in have) for h in hits or []])
    if a == "add":
        return out(*radio_add(d))
    if a in ("remove", "move"):
        sid = str(d.get("id") or "")
        lst = list(CFG.get("radio_stations") or [])
        i = next((n for n, e in enumerate(lst) if isinstance(e, dict) and e.get("id") == sid), -1)
        if i < 0:
            return out(False, "unknown station")
        if a == "remove":
            if RADIO["want"] and RADIO["sid"] == sid:
                radio_stop("station removed", who)
            gone = lst.pop(i)
            if CFG.get("wake_sound") == "radio:" + sid:
                CFG["wake_sound"] = "chime"                  # the wake-up alarm never points to nothing
            log_event("sys", f"Radio: station removed «{gone.get('name')}»"[:160])
        else:
            try:
                j = max(0, min(len(lst) - 1, i + int(d.get("by") or 0)))
            except (TypeError, ValueError):
                return out(False, "invalid value")
            lst.insert(j, lst.pop(i))
        with RADIO["lock"]:
            CFG["radio_stations"] = radio_clean(lst)
        save_settings()
        return out(True)
    return 400, {"ok": False, "error": "unknown action"}


def radio_fav_items(lang=None):
    """for «★ Favoriten» (639zzzi, branch mw-favoriten): the switch and one action per station"""
    L = norm_lang(lang or CFG.get("lang"))
    its = [{"k": "page:/radio", "i": "📻", "l": tr("Radio", L), "kind": "page", "href": "/radio"},
           {"k": "radio:on", "i": "📻", "l": tr("Radio on / off", L), "kind": "switch", "on": RADIO["want"], "post": ["/api/radio", {"action": "toggle"}]}]
    return its + [{"k": "radio:play:" + e["id"], "i": "▶", "l": e["name"], "kind": "action", "post": ["/api/radio", {"action": "play", "id": e["id"]}]}
                  for e in radio_list()]


atexit.register(lambda: radio_stop("program end", quiet=True))


# ---- «📱 dieser Browser» (Besitzer, after 3.99.0): the page plays the station itself ------------------------------------------------
# The Pi resolves the address as for its loudspeaker (directory, play lists); the page tries it directly. Does that fail (http on an
# https page, the station refuses the browser, a format the browser cannot), it takes /radio/stream/<id>: the Pi passes the stream
# through unchanged (no decoding, no ffmpeg), at most RADIO_BR_MAX listeners, only addresses resolved for a station of the list -
# the address never comes from the request (no open proxy). The title comes from the ICY reading of the Pi: the proxy reads it on
# the way, otherwise a short look every 20 s while the page asks (one block, then closed). The loudspeaker of MoveEye stays silent.
BR = {"sid": "", "t_poll": 0.0, "title": "", "title_sid": "", "src": {}, "n": 0, "lock": threading.Lock(), "watch": None}


def radio_br_src(sid, fresh=False):
    """the stream address of a station for the browser (play lists resolved) -> dict(url, kind, ct, metaint)"""
    st = radio_station(sid) if _RADIO_ID.match(str(sid or "")) else None
    if not st:
        raise KeyError("unknown station")
    c = BR["src"].get(sid)
    if c and not fresh and time.time() - c["t"] < RADIO_BR_TTL:
        return c
    src = radio_open(radio_resolve(st))
    if src.get("sock") is not None:
        src["sock"].close()
    c = {"t": time.time(), "url": src["url"], "kind": src["kind"], "ct": src.get("ct") or "", "metaint": int(src.get("metaint") or 0)}
    BR["src"][sid] = c
    return c


def radio_bplay(sid=None):
    sid = sid or CFG.get("radio_last") or ((radio_list() or [{}])[0].get("id"))
    try:
        c = radio_br_src(sid, fresh=True)
    except KeyError:
        return False, "unknown station", None
    except Exception as e:
        return False, "no internet" if radio_offline_err(e) else "the station does not answer: " + _radio_txt(e, 100), None
    if BR["title_sid"] != sid:
        BR.update(title="", title_sid=sid)
    BR.update(sid=sid, t_poll=time.time())
    th = BR["watch"]
    if th is None or not th.is_alive():
        BR["watch"] = threading.Thread(target=_radio_br_watch, daemon=True, name="radio-title")
        BR["watch"].start()
    return True, "", {"id": sid, "name": radio_station(sid)["name"], "url": c["url"], "kind": c["kind"], "ct": c["ct"], "proxy": "/radio/stream/" + sid}


def _radio_icy_peek(url, sid):
    """one look at the stream: the first title block, then closed"""
    src = radio_open(url)
    try:
        f, mi = src["f"], src["metaint"]
        if not mi:
            return False
        for _i in range(3):
            if not f.read(mi):
                break
            n = f.read(1)
            if not n:
                break
            if n[0]:
                t_ = radio_icy_title(f.read(n[0] * 16))
                if t_ is not None and BR["sid"] == sid:
                    BR.update(title=t_, title_sid=sid)
                    break
        return True
    finally:
        src["sock"].close()


def _radio_br_watch():
    """the title for the browser while its page asks (stops 20 s after the last question)"""
    last, wait_ = "", 0.0
    while BR["sid"] and time.time() - BR["t_poll"] < 20.0:
        sid = BR["sid"]; c = BR["src"].get(sid)
        if BR["n"] > 0 or not c or c["kind"] != "icy" or (sid == last and time.time() < wait_):
            time.sleep(1.0); continue                        # the proxy reads the titles itself / nothing to read / not yet
        try:
            has = _radio_icy_peek(c["url"], sid)
            last, wait_ = sid, time.time() + (20.0 if has else 600.0)
        except Exception:
            last, wait_ = sid, time.time() + 30.0
    BR["watch"] = None


def radio_br_proxy(sid):
    """-> (HTTP code, English error or content type, generator)"""
    if not _RADIO_ID.match(str(sid or "")) or not radio_station(sid):
        return 404, "unknown station", None
    try:
        c = radio_br_src(sid)
    except KeyError:
        return 404, "unknown station", None
    except Exception as e:
        return 502, "no internet" if radio_offline_err(e) else "the station does not answer", None
    if c["kind"] != "icy":
        return 415, "this stream (HLS) cannot go through MoveEye", None
    with BR["lock"]:
        if BR["n"] >= RADIO_BR_MAX:
            return 429, "too many listeners through MoveEye (at most 2)", None
        BR["n"] += 1
    try:
        src = radio_open(c["url"])
    except Exception as e:
        with BR["lock"]:
            BR["n"] -= 1
        return 502, "no internet" if radio_offline_err(e) else "the station does not answer", None
    ct = src.get("ct") or c["ct"]
    ct = ct if (ct.startswith("audio/") or ct == "application/ogg") else "audio/mpeg"

    return 200, ct, _RadioBrStream(src, sid)


class _RadioBrStream:
    """the stream for one listener: passed on unchanged, titles read on the way; close() (also when nothing was sent, e.g. HEAD)
    frees the place of the listener exactly once"""

    def __init__(self, src, sid):
        self.src, self.sid, self.done = src, sid, False

    def __iter__(self):
        f, mi = self.src["f"], self.src["metaint"]
        try:
            while not self.done:
                data = f.read(mi) if mi else f.read(8192)
                if not data:
                    break
                yield data
                if mi:
                    n = f.read(1)
                    if not n:
                        break
                    if n[0]:
                        t_ = radio_icy_title(f.read(n[0] * 16))
                        if t_ is not None:
                            BR.update(title=t_, title_sid=self.sid)
        except (OSError, ValueError):
            pass
        finally:
            self.close()

    def close(self):
        with BR["lock"]:
            if self.done:
                return
            self.done = True
            BR["n"] -= 1
        try:
            self.src["sock"].close()
        except OSError:
            pass


# ---- the web: /radio and /api/radio ---------------------------------------------------------------------------------------------
_smalltv_routes_radio = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzzd: the radio page and its API
    _smalltv_routes_radio(app, reply, body)
    from flask import Response, request, g

    def who_():
        role = getattr(g, "role", "admin")
        return role, (None if role == "admin" else user_req_perms(g))

    @app.route("/api/radio", methods=["GET", "POST"])
    def api_radio():
        role, perms = who_()
        if request.method == "GET":
            st = radio_state(request.args.get("lang"), role, perms)
            b = request.args.get("b") or ""
            if b and b == BR["sid"]:                         # «📱 dieser Browser» plays: keep the title reading alive
                BR["t_poll"] = time.time()
            st["btitle"] = BR["title"] if b and BR["title_sid"] == b else ""
            return reply({"ok": True, "state": st})
        code, ans = radio_do(body(), getattr(g, "user", "") or "web", role, perms, getattr(g, "appkey", None))
        return reply(ans, code)

    @app.route("/radio/stream/<sid>")
    def radio_stream(sid):
        role, perms = who_()
        L = norm_lang(request.args.get("lang"))
        if not radio_may(role, perms):
            return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
        if set(request.args) - {"t", "lang"}:                # never an address from outside: only the stations of the list
            return reply({"ok": False, "error": radio_tr("only the stations of the list", L)}, 400)
        code, ct, gen = radio_br_proxy(sid)
        if code != 200:
            return reply({"ok": False, "error": radio_tr(ct, L)}, code)
        return Response(gen, mimetype=ct, direct_passthrough=True, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @app.route("/radio")
    def radio_page():
        return Response(render_page(RADIO_PAGE, "more"), mimetype="text/html", headers={"Cache-Control": "no-store"})


# ---- the window (Tk): Mehr -> «📻 Radio»: stations, play / stop, volume -----------------------------------------------------------
if GUI_OK:
    def _radio_tk_win(self):
        w = getattr(self, "_radio_top", None)
        if w is not None and w.winfo_exists():
            w.lift(); return
        w = self._radio_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Radio")); w.configure(bg=C["bg"]); w.geometry("440x440")
        st = tk.Label(w, text="", bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"), wraplength=410, justify="left", anchor="w")
        st.pack(fill="x", padx=12, pady=(10, 2))
        sub = tk.Label(w, text="", bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), wraplength=410, justify="left", anchor="w")
        sub.pack(fill="x", padx=12)
        lb = tk.Listbox(w, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11), height=8, activestyle="none", exportselection=False, bd=0)
        lb.pack(fill="both", expand=True, padx=12, pady=8)
        bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=12)
        msg = tk.Label(w, text="", bg=C["bg"], fg=C.get("yel", "#ffd60a"), font=("DejaVu Sans", 9), wraplength=410, justify="left", anchor="w")
        ids = []

        def do(d):
            _c, ans = radio_do(d, "window")                  # the same entry as the web page
            msg.config(text="" if ans.get("ok") else "⚠ " + str(ans.get("error") or ""))
            tick(False)

        def play():
            sel = lb.curselection()
            do({"action": "play", "id": ids[sel[0]] if sel and sel[0] < len(ids) else None})
        self._fbtn(bf, "▶ " + tr("Play"), play, primary=True).pack(side="left", padx=(0, 6))
        self._fbtn(bf, "⏹ " + tr("Stop"), lambda: do({"action": "stop"})).pack(side="left")
        vf = tk.Frame(w, bg=C["bg"]); vf.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(vf, text="🔈 " + tr("Volume"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 10)).pack(side="left")
        vol = tk.Scale(vf, from_=0, to=100, orient="horizontal", showvalue=True, bg=C["bg"], fg=C["txt"], highlightthickness=0, troughcolor=C["panel"],
                       command=lambda v: CFG.update(radio_volume=int(float(v))))
        vol.set(int(CFG.get("radio_volume", 40)))
        vol.bind("<ButtonRelease-1>", lambda _e: do({"action": "volume", "v": vol.get()}))
        vol.pack(side="left", fill="x", expand=True, padx=(6, 0))
        msg.pack(fill="x", padx=12, pady=(6, 0))
        self._fbtn(w, "🌐 " + tr("Add stations, sleep timer (browser)"), lambda: self._open_page("/radio")).pack(anchor="w", padx=12, pady=6)
        self._fbtn(w, tr("Close"), w.destroy, primary=True).pack(side="bottom", anchor="e", padx=12, pady=(0, 10))

        def tick(again=True):
            try:
                if not w.winfo_exists():
                    return
                s = radio_state()
                new = [e["id"] for e in s["stations"]]
                if new != ids or lb.size() != len(new):
                    ids[:] = new; lb.delete(0, "end")
                    for e in s["stations"]:
                        lb.insert("end", e["name"])
                st.config(text=("▶ " + s["name"] if s["on"] else tr("The radio is off.")) if s["on"] or s["state"] not in ("offline", "error") else "⚠ " + (s["msg"] or s["name"]))
                sub.config(text=s["held"] or s["title"] or ((tr("No internet - the radio needs a connection.") if s["offline"] else s["msg"]) if s["state"] in ("retry", "offline", "error") else
                                                            (tr("connecting …") if s["state"] == "connecting" else "")))
                if again:
                    w.after(1000, tick)
            except Exception:
                pass
        tick()

    App._radio_win = _radio_tk_win
    _radio_tk_more_base = App._tk_more_bar

    def _radio_tk_more_bar(self, parent):
        f = _radio_tk_more_base(self, parent)
        row = max([int(x.grid_info().get("row", 0)) for x in f.grid_slaves()] + [-1]) + 1
        self._fbtn(f, "📻 " + tr("Radio"), self._radio_win).grid(row=row, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639zzz «Morse»)
    App._tk_more_bar = _radio_tk_more_bar


RADIO_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Radio</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:720px;margin:0 auto;box-sizing:border-box}
.ra-back{display:inline-flex;align-items:center;min-height:40px;text-decoration:none;color:var(--acc);font-weight:600;margin:0 0 4px}
#ra-title{margin:0 0 10px;font-size:20px}
.ra-now{border:2px solid var(--line);border-radius:16px;background:var(--panel);padding:14px;margin:0 0 14px;display:flex;flex-direction:column;gap:10px}
.ra-now.on{border-color:var(--grn)}.ra-now.bad{border-color:var(--yel)}
.ra-st{font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}.ra-now.on .ra-st{color:var(--grn)}
.ra-name{font-size:22px;font-weight:700;overflow-wrap:anywhere;line-height:1.2}
.ra-tit{font-size:15px;color:var(--txt);overflow-wrap:anywhere;min-height:1.2em}.ra-tit:empty{display:none}
.ra-hint{font-size:13px;color:var(--mut);overflow-wrap:anywhere}.ra-hint:empty{display:none}.ra-hint.warn{color:var(--yel)}
.ra-off{border:1px solid var(--yel);border-radius:10px;padding:8px 10px;font-size:13px;overflow-wrap:anywhere}
.ra-go{min-height:52px;font:inherit;font-size:18px;font-weight:700;border-radius:12px;width:100%}
.ra-sl{display:grid;grid-template-columns:auto minmax(0,1fr) 3em;gap:10px;align-items:center}.ra-sl input{width:100%;min-height:40px}.ra-sl b{text-align:right;font-variant-numeric:tabular-nums}
.ra-lab{font-size:13px;color:var(--mut)}
.ra-seg{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}.ra-seg button{min-height:40px;font:inherit;font-size:14px;padding:0 2px}
.ra-seg button.sel,.ra-wh button.sel{outline:2px solid var(--acc);outline-offset:-2px;font-weight:700}
.ra-wh{display:grid;grid-template-columns:1fr 1fr;gap:6px}.ra-wh button{min-height:44px;font:inherit;font-size:14px;padding:2px 6px;overflow-wrap:anywhere}
.ra-h{display:flex;align-items:center;gap:8px;margin:0 0 8px}.ra-h h3{margin:0;flex:1}
.ra-list{list-style:none;margin:0;padding:0;border:1px solid var(--line);border-radius:14px;overflow:hidden}.ra-list:empty{display:none}
.ra-list li{display:flex;align-items:center;gap:8px;min-height:56px;padding:6px 10px;border-top:1px solid var(--line)}.ra-list li:first-child{border-top:0}
.ra-list .ra-r{all:unset;cursor:pointer;flex:1;min-width:0;display:flex;flex-direction:column;gap:2px;padding:4px 0}
.ra-list .ra-r b{font-size:15px;overflow-wrap:anywhere}.ra-list .ra-r small{color:var(--mut);font-size:12px;overflow-wrap:anywhere}
.ra-list li.cur .ra-r b{color:var(--grn)}.ra-list li .ra-i{width:24px;text-align:center;flex:none}
.ra-list li button.sec{min-height:40px;min-width:40px;padding:0 8px;flex:none}
.ra-f{display:flex;gap:8px}.ra-f input{flex:1;min-width:0;font:inherit;font-size:16px;min-height:44px;box-sizing:border-box;background:var(--field);color:var(--txt);
border:1px solid var(--line);border-radius:10px;padding:6px 10px}.ra-f button{min-height:44px;flex:none}
.ra-col{display:flex;flex-direction:column;gap:8px;margin-top:10px}.ra-col>input{font:inherit;font-size:16px;min-height:44px;width:100%;box-sizing:border-box;
background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:6px 10px}
section.card h3{margin:0 0 10px}details>summary{cursor:pointer;font-weight:600;min-height:36px;display:flex;align-items:center}
.ra-how{margin:0;padding-left:18px;font-size:13px;color:var(--mut)}.ra-how li{margin:0 0 4px}
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
  <a class="ra-back" href="/more" id="ra-back">‹ More</a>
  <h2 id="ra-title">📻 Radio</h2>
  <section class="ra-now" id="ra-now">
    <div class="ra-lab" id="ra-l-where">Where to play</div>
    <div class="ra-wh" id="ra-where" role="group"><button type="button" class="sec" data-w="pi" id="ra-w-pi">🔊 MoveEye loudspeaker</button><button type="button" class="sec" data-w="br" id="ra-w-br">📱 this browser</button></div>
    <div class="ra-st" id="ra-st"></div>
    <div class="ra-name" id="ra-name">…</div>
    <div class="ra-tit" id="ra-tit"></div>
    <div class="ra-hint" id="ra-hint"></div>
    <div class="ra-off" id="ra-off" hidden></div>
    <div class="ra-hint warn" id="ra-qn" hidden></div>
    <button type="button" class="ra-go" id="ra-go">▶</button>
    <div class="ra-sl"><span aria-hidden="true">🔈</span><input type="range" id="ra-vol" min="0" max="100" step="1" aria-label="Volume"><b id="ra-vol-v"></b></div>
    <div class="ra-lab" id="ra-l-sleep">Sleep timer</div>
    <div class="ra-seg" id="ra-sleep" role="group"></div>
    <div class="ra-hint" id="ra-err"></div>
  </section>
  <section class="card" id="ra-lc"><div class="ra-h"><h3 id="ra-lt">My stations</h3><button type="button" class="sec" id="ra-edit" hidden>Edit</button></div>
    <ul class="ra-list" id="ra-list"></ul><div class="ra-hint" id="ra-empty"></div></section>
  <section class="card" id="ra-ac" hidden><h3 id="ra-at">Add a station</h3>
    <form class="ra-f" id="ra-sf"><input type="search" id="ra-q" maxlength="60" autocomplete="off" enterkeyhint="search"><button type="submit" id="ra-sgo">Search</button></form>
    <div class="ra-hint" id="ra-src" style="margin-top:6px"></div>
    <div class="ra-hint" id="ra-serr"></div>
    <ul class="ra-list" id="ra-res" style="margin-top:8px"></ul>
    <details id="ra-ud" style="margin-top:10px"><summary id="ra-us">Paste a stream address</summary>
      <div class="ra-col"><input class="ra-u" type="url" id="ra-url" maxlength="500" placeholder="https://…" autocomplete="off" spellcheck="false" autocapitalize="off">
        <div class="ra-f"><input type="text" id="ra-un" maxlength="60" autocomplete="off"><button type="button" id="ra-uadd">Add</button></div>
        <div class="ra-hint" id="ra-uh"></div></div></details>
  </section>
  <section class="card"><h3 id="ra-ht">Good to know</h3><ul class="ra-how" id="ra-how"></ul><div style="margin-top:8px"><a class="btn sec" id="ra-wake" href="/settings?setting=wake_sound">⏰ Radio as wake-up alarm</a></div></section>
</main>
<script>
/*COMMON*/
/*RADIODE*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  let J = null, edit = false, tm = 0, busy = false;
  // «📱 dieser Browser»: where it plays, remembered per browser; the <audio> of the page plays the station itself
  const LS = {get: (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } },
              set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} }};
  let W = LS.get("mw-radio-where", "pi") === "br" ? "br" : "pi", bvol = Math.max(0, Math.min(100, +LS.get("mw-radio-bvol", 70) || 0)), hls = null;
  const A = new Audio(); A.preload = "none"; window.mwRadioAudio = A;
  const B = {on: false, sid: "", name: "", st: "off", via: "", err: "", until: 0, min: 0, again: 0, t0: 0};
  const bv = () => { A.volume = Math.max(0, Math.min(1, bvol / 100 * (B.until ? Math.min(1, (B.until - Date.now()) / 45000) : 1))); };
  bv();
  const api = async (b) => { try { const r = await fetch("/api/radio", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))});
    return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  document.title = "MoveEye – " + t("Radio");
  $i("ra-back").textContent = "‹ " + t("More"); $i("ra-title").textContent = "📻 " + t("Radio");
  $i("ra-l-sleep").textContent = "💤 " + t("Sleep timer"); $i("ra-lt").textContent = t("My stations"); $i("ra-at").textContent = t("Add a station");
  $i("ra-q").placeholder = t("Name of the station, e.g. Pilatus"); $i("ra-sgo").textContent = "🔍 " + t("Search");
  $i("ra-src").textContent = t("Directory: radio-browser.info (open and free). MoveEye asks it, not your phone.");
  $i("ra-us").textContent = t("Paste a stream address"); $i("ra-un").placeholder = t("Name"); $i("ra-uadd").textContent = "+ " + t("Add");
  $i("ra-uh").textContent = t("A stream (MP3, AAC, Ogg) or a play list (.pls, .m3u). Only http:// or https://.");
  $i("ra-ht").textContent = t("Good to know"); $i("ra-wake").textContent = "⏰ " + t("Radio as wake-up alarm");
  $i("ra-vol").setAttribute("aria-label", t("Volume"));
  ["Siren, alarms, announcements, Morse and the wake-up alarm always go first: the radio pauses and plays on afterwards.",
   "While the microphone receives Morse or radio signals the radio pauses - otherwise the microphone would hear it.",
   "While the radio plays, the noise alarm does not listen (like with every sound of MoveEye).",
   "The radio needs internet. Without it MoveEye tries a few times and then stops - tap ▶ again later.",
   "The station address is fetched fresh every time: a station that changes its address keeps working.",
   "Radio as wake-up alarm: Settings › Wake-up alarm › Wake-up sound. Without internet the alarm takes its tone after 10 s.",
   "«📱 this browser»: the phone plays the station, the MoveEye loudspeaker stays silent. If the station does not play directly, it runs through MoveEye (at most 2 listeners)."].forEach(s => $i("ra-how").appendChild(E("li", "", t(s))));
  const mm = s => { s = Math.max(0, s | 0); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); };
  function tryUrl(u, isHls) {
    return new Promise((res, rej) => {
      let done = false;
      const fin = (f, x) => { if (done) return; done = true; clearTimeout(tt); A.removeEventListener("playing", okf); A.removeEventListener("error", erf); f(x); };
      const okf = () => fin(res), erf = () => fin(rej, new Error("media")), tt = setTimeout(() => fin(rej, new Error("timeout")), 12000);
      A.addEventListener("playing", okf); A.addEventListener("error", erf);
      if (hls) { try { hls.destroy(); } catch (e) {} hls = null; }
      if (isHls) { hls = new window.Hls(); hls.loadSource(u); hls.attachMedia(A); } else A.src = u;
      const p = A.play(); if (p && p.catch) p.catch(e => fin(rej, e));
    });
  }
  async function bplay(id) {
    if (busy) return; busy = true;
    const j = await api({action: "bplay", id: id || ""}); busy = false;
    if (!j.ok || !j.src) { B.st = "error"; B.err = j.error || ""; take(j); return; }
    const s = j.src; Object.assign(B, {on: true, sid: s.id, name: s.name, st: "connecting", err: "", via: ""}); if (j.state) J = j.state; paint();
    const tries = [];
    if (s.kind === "hls") {
      if (A.canPlayType("application/vnd.apple.mpegurl")) tries.push(["direct", s.url, false]);
      else if (window.Hls && window.Hls.isSupported && window.Hls.isSupported()) tries.push(["direct", s.url, true]);
    } else {
      if (!(location.protocol === "https:" && /^http:/i.test(s.url))) tries.push(["direct", s.url, false]);   // http on an https page: blocked anyway
      tries.push(["proxy", s.proxy + "?t=" + Date.now(), false]);
    }
    for (const [via, u, h] of tries) {
      if (!B.on || B.sid !== s.id) return;
      try { await tryUrl(u, h); B.via = via; B.st = "playing"; B.t0 = Date.now(); window.mwRadioVia = via; ms(); paint(); load(); return; } catch (e) {}
    }
    if (B.sid !== s.id) return;
    bstop(true); B.st = "error";
    B.err = s.kind === "hls" ? t("This station (HLS) cannot play in this browser - use the MoveEye loudspeaker.") : t("The station does not play in this browser.");
    paint();
  }
  function bstop(keep) {
    const was = B.on; B.on = false; B.st = "off"; B.until = 0; B.min = 0; B.via = ""; if (!keep) B.err = "";
    if (hls) { try { hls.destroy(); } catch (e) {} hls = null; }
    A.pause(); A.removeAttribute("src"); try { A.load(); } catch (e) {}
    bv(); if (was) api({action: "bstop"}); ms(); paint();
  }
  A.addEventListener("ended", () => again()); A.addEventListener("error", () => { if (B.st === "playing") again(); });
  function again() {                                       // the stream broke off: at most 3 new tries, then the card says so
    if (!B.on) return;
    if (Date.now() - B.t0 > 60000) B.again = 0;
    if (B.again++ >= 3) { bstop(true); B.st = "error"; B.err = t("The station does not play in this browser."); paint(); return; }
    const id = B.sid; B.st = "connecting"; paint(); setTimeout(() => { if (B.on && B.sid === id) bplay(id); }, 3000);
  }
  setInterval(() => { if (B.on && B.until) { if (Date.now() >= B.until) bstop(); else { bv(); paint(); } } }, 1000);   // the sleep timer of the browser
  let msSet = false;
  function ms() {                                          // lock screen (iPhone / Android): title and the buttons
    if (!("mediaSession" in navigator)) return;
    try {
      navigator.mediaSession.metadata = B.on && window.MediaMetadata ? new MediaMetadata({title: (J && J.btitle) || B.name, artist: (J && J.btitle) ? B.name : "MoveEye", album: "MoveEye · " + t("Radio")}) : null;
      navigator.mediaSession.playbackState = B.on ? "playing" : "none";
      if (!msSet) {
        msSet = true;
        navigator.mediaSession.setActionHandler("play", () => bplay(B.sid || (J && J.last) || ""));
        ["pause", "stop"].forEach(a => { try { navigator.mediaSession.setActionHandler(a, () => bstop()); } catch (e) {} });
      }
    } catch (e) {}
  }
  function where(w) {
    if (w === W) return;
    W = w; LS.set("mw-radio-where", w);
    if (w === "br" && J && J.on) api({action: "stop"}).then(take);   // the loudspeaker of MoveEye stays silent
    if (w === "pi") bstop();
    paint();
  }
  $i("ra-w-pi").onclick = () => where("pi"); $i("ra-w-br").onclick = () => where("br");
  $i("ra-l-where").textContent = t("Where to play") + ":"; $i("ra-w-pi").textContent = "🔊 " + t("MoveEye loudspeaker"); $i("ra-w-br").textContent = "📱 " + t("this browser");
  function paintBr() {                                     // the card in «📱 dieser Browser»
    const box = $i("ra-now"), bad = B.st === "error";
    box.classList.toggle("on", B.st === "playing"); box.classList.toggle("bad", bad);
    $i("ra-st").textContent = B.st === "playing" ? "● " + t("on air") + (B.via === "proxy" ? " · " + t("via MoveEye") : "") : B.st === "connecting" ? t("connecting …") : bad ? t("stopped") : t("off");
    const cur = (J.stations || []).find(x => x.id === (B.on ? B.sid : J.last)) || (J.stations || [])[0];
    $i("ra-name").textContent = B.on ? B.name : (cur ? cur.name : t("No station yet"));
    $i("ra-tit").textContent = B.on && J.btitle ? "♪ " + J.btitle : "";
    $i("ra-hint").textContent = B.until ? "💤 " + t("off in") + " " + mm((B.until - Date.now()) / 1000) : ""; $i("ra-hint").className = "ra-hint";
    $i("ra-off").textContent = B.err; $i("ra-off").hidden = !B.err;
    $i("ra-qn").hidden = true;                             // the noise alarm / clap switch keep listening: MoveEye plays nothing
    const go = $i("ra-go");
    go.textContent = B.on ? "⏹ " + t("Stop") : "▶ " + t("Play"); go.className = "ra-go" + (B.on ? " sec" : ""); go.disabled = !J.may.play || (!B.on && !cur);
    const v = $i("ra-vol"); if (document.activeElement !== v) v.value = bvol; $i("ra-vol-v").textContent = v.value + "%"; v.disabled = !J.may.play;
    const sg = $i("ra-sleep"); sg.textContent = "";
    J.sleep.opts.forEach(m => { const b = E("button", "sec" + (m === B.min ? " sel" : ""), m ? m + " min" : t("off")); b.type = "button";
      b.disabled = !J.may.play || (!!m && !B.on); b.onclick = () => { B.min = m; B.until = m ? Date.now() + m * 60000 : 0; bv(); paint(); }; sg.appendChild(b); });
    return cur;
  }
  function paint() {
    if (!J) return;
    $i("ra-w-pi").classList.toggle("sel", W === "pi"); $i("ra-w-br").classList.toggle("sel", W === "br");
    $i("ra-w-pi").disabled = $i("ra-w-br").disabled = !J.may.play;
    if (W === "br") { paintBr(); paintList(); return; }
    const on = !!J.on, box = $i("ra-now"), st = J.state, bad = st === "retry" || st === "offline" || st === "error";
    box.classList.toggle("on", on && st === "playing" && !J.held); box.classList.toggle("bad", bad);
    $i("ra-st").textContent = st === "playing" ? (J.held ? "⏸ " + t("paused") : "● " + t("on air")) : st === "connecting" ? t("connecting …") : st === "retry" ? t("trying again") : bad ? t("stopped") : t("off");
    const cur = (J.stations || []).find(x => x.id === (on ? J.sid : J.last)) || (J.stations || [])[0];
    $i("ra-name").textContent = on ? J.name : (cur ? cur.name : t("No station yet"));
    $i("ra-tit").textContent = on && J.title ? "♪ " + J.title : "";
    $i("ra-hint").textContent = J.held || (J.sleep.left ? "💤 " + t("off in") + " " + mm(J.sleep.left) : "") || (J.wake ? "⏰ " + t("Wake-up alarm") : "");
    $i("ra-hint").className = "ra-hint" + (J.held ? " warn" : "");
    const off = $i("ra-off");
    let ot = "";
    if (!J.spk) ot = t("No loudspeaker selected: Settings › Light & sound › Loudspeaker.");
    else if (!J.ffmpeg) ot = t("ffmpeg is missing (sudo apt install ffmpeg)");
    else if (J.offline) ot = "📡 " + t("No internet - the radio needs a connection.") + (J.retry ? " " + t("Next try in") + " " + J.retry.in + " s (" + J.retry.n + " / " + J.retry.max + ")." : " " + t("MoveEye has stopped trying - tap ▶ again later."));
    else if (bad) ot = (J.msg || t("The station does not answer.")) + (J.retry ? " · " + t("Next try in") + " " + J.retry.in + " s" : "");
    off.textContent = ot; off.hidden = !ot;
    $i("ra-qn").textContent = J.quiet ? "🔇 " + t("While the radio plays: noise alarm and clap switch paused - the camera alarm works as usual") : ""; $i("ra-qn").hidden = !J.quiet;
    const go = $i("ra-go");
    go.textContent = on ? "⏹ " + t("Stop") : "▶ " + t("Play");
    go.className = "ra-go" + (on ? " sec" : ""); go.disabled = !J.may.play || (!on && !cur);
    const v = $i("ra-vol"); if (document.activeElement !== v) v.value = J.vol; $i("ra-vol-v").textContent = v.value + "%"; v.disabled = !J.may.play;
    const sg = $i("ra-sleep"); sg.textContent = "";
    J.sleep.opts.forEach(m => { const b = E("button", "sec" + (m === J.sleep.min ? " sel" : ""), m ? m + " min" : t("off")); b.type = "button";
      b.disabled = !J.may.play || (!!m && !on); b.onclick = async () => { const j = await api({action: "sleep", min: m}); take(j); }; sg.appendChild(b); });
    paintList();
  }
  function paintList() {
    const br = W === "br", on = br ? B.on : !!J.on, sid = br ? B.sid : J.sid;
    const ul = $i("ra-list"); ul.textContent = "";
    $i("ra-edit").hidden = !J.may.edit || !(J.stations || []).length; $i("ra-edit").textContent = edit ? t("Done") : t("Edit");
    (J.stations || []).forEach((s, n) => {
      const li = E("li", on && s.id === sid ? "cur" : ""), r = E("button", "ra-r");
      r.type = "button"; r.appendChild(E("b", "", s.name)); r.appendChild(E("small", "", s.sub || (s.kind === "url" ? t("own address") : "radio-browser.info")));
      li.appendChild(E("span", "ra-i", on && s.id === sid ? (br ? "📱" : "🔊") : "📻"));
      r.disabled = !J.may.play; r.onclick = async () => { if (br) { bplay(s.id); return; } const j = await api({action: "play", id: s.id}); take(j); };
      li.appendChild(r);
      if (edit) {
        const B = (txt, lab, f) => { const b = E("button", "sec", txt); b.type = "button"; b.title = lab; b.setAttribute("aria-label", lab); b.onclick = f; li.appendChild(b); };
        if (n > 0) B("↑", t("up"), async () => take(await api({action: "move", id: s.id, by: -1})));
        if (n < J.stations.length - 1) B("↓", t("down"), async () => take(await api({action: "move", id: s.id, by: 1})));
        B("✕", t("Remove"), async () => { if (confirm(t("Remove this station?") + "\n" + s.name)) take(await api({action: "remove", id: s.id})); });
      }
      ul.appendChild(li);
    });
    $i("ra-empty").textContent = (J.stations || []).length ? "" : t("No station yet") + (J.may.edit ? " – " + t("search one below.") : ".");
    $i("ra-ac").hidden = !J.may.edit;
    if (!J.may.play) $i("ra-err").textContent = t("Playing the radio needs the right «Siren / sounds».");
  }
  function take(j) { if (j && j.state) J = j.state; $i("ra-err").textContent = j && !j.ok ? (j.error || "") : ""; paint(); clearTimeout(tm); tm = setTimeout(load, 1500); }
  async function load() {
    clearTimeout(tm);
    const was = J && J.btitle;
    try { const j = await (await fetch("/api/radio?lang=" + L() + (W === "br" && B.on ? "&b=" + encodeURIComponent(B.sid) : ""), {cache: "no-store"})).json();
      if (j && j.state) J = j.state; } catch (e) {}
    if (J && J.btitle !== was) ms();
    paint(); tm = setTimeout(load, J && (J.on || J.state === "retry" || (W === "br" && B.on)) ? 2000 : 8000);
  }
  $i("ra-go").onclick = async () => { if (W === "br") { if (B.on) bstop(); else bplay(J && J.last || ""); return; }
    if (busy) return; busy = true; $i("ra-go").disabled = true;
    const j = await api(J && J.on ? {action: "stop"} : {action: "play", id: J && J.last || ""}); busy = false; take(j); };
  let vt = 0;
  $i("ra-vol").oninput = () => { $i("ra-vol-v").textContent = $i("ra-vol").value + "%"; clearTimeout(vt);
    if (W === "br") { bvol = +$i("ra-vol").value; LS.set("mw-radio-bvol", String(bvol)); bv(); return; } vt = setTimeout(async () => take(await api({action: "volume", v: +$i("ra-vol").value})), 250); };
  $i("ra-edit").onclick = () => { edit = !edit; paint(); };
  $i("ra-sf").onsubmit = async (ev) => {
    ev.preventDefault(); const q = $i("ra-q").value.trim(), res = $i("ra-res"); $i("ra-serr").textContent = "";
    if (q.length < 2) { $i("ra-serr").textContent = t("type at least 2 letters"); return; }
    $i("ra-sgo").disabled = true; res.textContent = ""; $i("ra-serr").textContent = t("searching …");
    const j = await api({action: "search", q: q}); $i("ra-sgo").disabled = false;
    $i("ra-serr").textContent = j.ok ? ((j.hits || []).length ? "" : t("Nothing found.")) : (j.error || "");
    (j.hits || []).forEach(h => {
      const li = E("li"), r = E("div", "ra-r");
      r.appendChild(E("b", "", h.name)); r.appendChild(E("small", "", [h.country || h.cc, h.codec, h.bitrate ? h.bitrate + " kbit/s" : "", h.tags].filter(Boolean).join(" · ")));
      li.appendChild(E("span", "ra-i", "📻")); li.appendChild(r);
      const b = E("button", "sec", h.have ? "✓" : "+"); b.type = "button"; b.disabled = !!h.have; b.title = t("Add"); b.setAttribute("aria-label", t("Add") + ": " + h.name);
      b.onclick = async () => { b.disabled = true; const k = await api({action: "add", uuid: h.uuid}); if (k.ok) b.textContent = "✓"; else b.disabled = false; take(k); };
      li.appendChild(b); res.appendChild(li);
    });
  };
  $i("ra-uadd").onclick = async () => { const k = await api({action: "add", url: $i("ra-url").value.trim(), name: $i("ra-un").value.trim()});
    if (k.ok) { $i("ra-url").value = ""; $i("ra-un").value = ""; } take(k); };
  load();
})();
</script>
</body></html>
"""

RADIO_MORE_ROW = ('  <a class="mi" href="/radio" id="m-radio"><i>📻</i><span><b data-i18n="Radio">Radio</b><small id="m-radio-s" data-i18n="Internet radio on the loudspeaker">'
                  'Internet radio on the loudspeaker</small></span><span class="ar">›</span></a>\n')
_ra_anchor = '  <a class="mi" href="/tools">'
if 'href="/radio"' not in MORE_PAGE and MORE_PAGE.count(_ra_anchor) == 1:
    MORE_PAGE = MORE_PAGE.replace(_ra_anchor, RADIO_MORE_ROW + _ra_anchor, 1)
    MORE_PAGE = MORE_PAGE.replace("/*ALERTS*/", 'fetch("/api/radio", {cache: "no-store"}).then(r => r.json()).then(j => { const s = document.getElementById("m-radio-s"), x = j && j.state; '
                                  'if (s && x && x.on) { s.removeAttribute("data-i18n"); s.textContent = "▶ " + x.name + (x.title ? " · " + x.title : ""); } '
                                  'if (s && x && x.quiet) { const q = document.createElement("small"); q.style.cssText = "display:block;color:var(--yel)"; '
                                  'q.textContent = "🔇 " + t("While the radio plays: noise alarm and clap switch paused - the camera alarm works as usual"); s.after(q); } }).catch(() => {});\n/*ALERTS*/', 1)

_render_page_radio = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzzzd: the German texts of the radio page
    out = _render_page_radio(page, active)
    if "/*RADIODE*/" in out:
        out = out.replace("/*RADIODE*/", "Object.assign(I18N.de, " + json.dumps(_RADIO_DE, ensure_ascii=False).replace("</", "<\\/") + ");", 1)
    return out


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_RADIO = {
    "Radio": ("Radio", "Radio", "Radio", "Radio"),
    "Internet radio on the loudspeaker": ("Internet-Radio auf dem Lautsprecher", "Radio internet sur le haut-parleur", "Radio internet sull’altoparlante", "Radio d’internet sin l’autpledader"),
    "While the radio plays: noise alarm and clap switch paused - the camera alarm works as usual": (
        "Während Radio: Geräusch-Alarm und Klatschschalter pausiert – Kamera-Alarm läuft normal",
        "Pendant la radio : alarme sonore et interrupteur à claquements en pause – l’alarme caméra fonctionne normalement",
        "Durante la radio: allarme rumore e interruttore a battito di mani in pausa – l’allarme della telecamera funziona normalmente",
        "Durant il radio: alarm da canera ed interruptur da batter las mauns en pausa – l’alarm da la camera funcziuna normal"),
    "Where to play": ("Wo spielen", "Où écouter", "Dove ascoltare", "Nua tadlar"),
    "MoveEye loudspeaker": ("MoveEye-Lautsprecher", "Haut-parleur de MoveEye", "Altoparlante di MoveEye", "Autpledader da MoveEye"),
    "this browser": ("dieser Browser", "ce navigateur", "questo browser", "quest navigatur"),
    "via MoveEye": ("über MoveEye", "via MoveEye", "tramite MoveEye", "via MoveEye"),
    "This station (HLS) cannot play in this browser - use the MoveEye loudspeaker.": (
        "Dieser Sender (HLS) spielt nicht in diesem Browser – den MoveEye-Lautsprecher wählen.",
        "Cette station (HLS) ne joue pas dans ce navigateur – choisis le haut-parleur de MoveEye.",
        "Questa stazione (HLS) non suona in questo browser – scegli l’altoparlante di MoveEye.",
        "Quest emettur (HLS) na suna betg en quest navigatur – tscherna l’autpledader da MoveEye."),
    "The station does not play in this browser.": ("Der Sender spielt nicht in diesem Browser.", "La station ne joue pas dans ce navigateur.",
                                                   "La stazione non suona in questo browser.", "L’emettur na suna betg en quest navigatur."),
    "«📱 this browser»: the phone plays the station, the MoveEye loudspeaker stays silent. If the station does not play directly, it runs through MoveEye (at most 2 listeners).": (
        "«📱 dieser Browser»: das Handy spielt den Sender, der MoveEye-Lautsprecher bleibt still. Spielt der Sender nicht direkt, läuft er über MoveEye (höchstens 2 Zuhörer).",
        "«📱 ce navigateur» : le téléphone joue la station, le haut-parleur de MoveEye reste muet. Si la station ne joue pas directement, elle passe par MoveEye (2 auditeurs au plus).",
        "«📱 questo browser»: il telefono riproduce la stazione, l’altoparlante di MoveEye resta muto. Se la stazione non suona direttamente, passa da MoveEye (al massimo 2 ascoltatori).",
        "«📱 quest navigatur»: il telefonin suna l’emettur, l’autpledader da MoveEye resta quiet. Sch’il emettur na suna betg directamain, va el tras MoveEye (maximalmain 2 auditurs)."),
    "only the stations of the list": ("nur die Sender der Liste", "seulement les stations de la liste", "solo le stazioni dell’elenco", "mo ils emetturs da la glista"),
    "this stream (HLS) cannot go through MoveEye": ("dieser Stream (HLS) geht nicht über MoveEye", "ce flux (HLS) ne peut pas passer par MoveEye",
                                                    "questo stream (HLS) non può passare da MoveEye", "quest stream (HLS) na po betg ir tras MoveEye"),
    "too many listeners through MoveEye (at most 2)": ("zu viele Zuhörer über MoveEye (höchstens 2)", "trop d’auditeurs via MoveEye (2 au plus)",
                                                       "troppi ascoltatori tramite MoveEye (al massimo 2)", "memia blers auditurs via MoveEye (maximalmain 2)"),
    "Radio on / off": ("Radio ein / aus", "Radio marche / arrêt", "Radio acceso / spento", "Radio en / ora"),
    "Play": ("Abspielen", "Écouter", "Ascolta", "Tadlar"),
    "Volume": ("Lautstärke", "Volume", "Volume", "Volumen"),
    "Sleep timer": ("Einschlaf-Timer", "Minuterie de sommeil", "Timer per dormire", "Temporisatur per sa durmentar"),
    "My stations": ("Meine Sender", "Mes stations", "Le mie stazioni", "Mes emetturs"),
    "Add a station": ("Sender hinzufügen", "Ajouter une station", "Aggiungi una stazione", "Agiuntar in emettur"),
    "Name of the station, e.g. Pilatus": ("Name des Senders, z. B. Pilatus", "Nom de la station, p. ex. Pilatus", "Nome della stazione, p. es. Pilatus", "Num da l’emettur, p. ex. Pilatus"),
    "Search": ("Suchen", "Chercher", "Cerca", "Tschertgar"),
    "Directory: radio-browser.info (open and free). MoveEye asks it, not your phone.": (
        "Verzeichnis: radio-browser.info (offen und frei). MoveEye fragt dort nach, nicht dein Handy.",
        "Annuaire : radio-browser.info (ouvert et libre). MoveEye le consulte, pas ton téléphone.",
        "Elenco: radio-browser.info (aperto e libero). Lo consulta MoveEye, non il tuo telefono.",
        "Register: radio-browser.info (avert e liber). MoveEye dumonda là, betg tes telefonin."),
    "Paste a stream address": ("Stream-Adresse einfügen", "Coller une adresse de flux", "Incolla un indirizzo di stream", "Encollar ina adressa da stream"),
    "Name": ("Name", "Nom", "Nome", "Num"),
    "Add": ("Hinzufügen", "Ajouter", "Aggiungi", "Agiuntar"),
    "A stream (MP3, AAC, Ogg) or a play list (.pls, .m3u). Only http:// or https://.": (
        "Ein Stream (MP3, AAC, Ogg) oder eine Wiedergabeliste (.pls, .m3u). Nur http:// oder https://.",
        "Un flux (MP3, AAC, Ogg) ou une liste de lecture (.pls, .m3u). Seulement http:// ou https://.",
        "Uno stream (MP3, AAC, Ogg) o una playlist (.pls, .m3u). Solo http:// o https://.",
        "In stream (MP3, AAC, Ogg) u ina glista da reproducziun (.pls, .m3u). Mo http:// u https://."),
    "Good to know": ("Gut zu wissen", "Bon à savoir", "Buono a sapersi", "Bun da savair"),
    "Radio as wake-up alarm": ("Radio als Wecker", "Radio comme réveil", "Radio come sveglia", "Radio sco svegliarin"),
    "Siren, alarms, announcements, Morse and the wake-up alarm always go first: the radio pauses and plays on afterwards.": (
        "Sirene, Alarme, Ansagen, Morse und der Wecker gehen immer vor: das Radio pausiert und spielt danach weiter.",
        "Sirène, alarmes, annonces, morse et réveil passent toujours avant : la radio fait une pause puis reprend.",
        "Sirena, allarmi, annunci, Morse e sveglia hanno sempre la precedenza: la radio fa una pausa e poi riprende.",
        "Sirena, alarms, annunzias, morse ed il svegliarin han adina la precedenza: il radio fa pausa e suna suenter vinavant."),
    "While the microphone receives Morse or radio signals the radio pauses - otherwise the microphone would hear it.": (
        "Solange das Mikrofon Morse- oder Funksignale empfängt, pausiert das Radio – sonst würde das Mikrofon es hören.",
        "Tant que le microphone reçoit des signaux morse ou radio, la radio fait une pause – sinon le microphone l’entendrait.",
        "Mentre il microfono riceve segnali Morse o radio, la radio fa una pausa – altrimenti il microfono la sentirebbe.",
        "Uschè ditg ch’il microfon retschaiva signals da morse u da radio, fa il radio pausa – uschiglio udiss il microfon el."),
    "While the radio plays, the noise alarm does not listen (like with every sound of MoveEye).": (
        "Solange das Radio spielt, hört der Geräusch-Alarm nicht mit (wie bei jedem Ton von MoveEye).",
        "Tant que la radio joue, l’alarme sonore n’écoute pas (comme pour chaque son de MoveEye).",
        "Mentre la radio suona, l’allarme rumore non ascolta (come per ogni suono di MoveEye).",
        "Uschè ditg ch’il radio suna, na taidla l’alarm da canera betg (sco tar mintga tun da MoveEye)."),
    "The radio needs internet. Without it MoveEye tries a few times and then stops - tap ▶ again later.": (
        "Das Radio braucht Internet. Ohne versucht es MoveEye ein paar Mal und hört dann auf – später nochmals ▶ tippen.",
        "La radio a besoin d’internet. Sans, MoveEye essaie quelques fois puis s’arrête – touche ▶ plus tard.",
        "La radio ha bisogno di internet. Senza, MoveEye prova alcune volte e poi smette – tocca ▶ più tardi.",
        "Il radio dovra internet. Senza emprova MoveEye intgins giadas e chala lura – tutga pli tard danovamain ▶."),
    "The station address is fetched fresh every time: a station that changes its address keeps working.": (
        "Die Adresse des Senders wird jedes Mal frisch geholt: ein Sender mit neuer Adresse geht weiter.",
        "L’adresse de la station est récupérée à chaque fois : une station qui change d’adresse continue de fonctionner.",
        "L’indirizzo della stazione viene preso ogni volta da capo: una stazione che cambia indirizzo continua a funzionare.",
        "L’adressa da l’emettur vegn prendida mintga giada da nov: in emettur cun ina nova adressa funcziuna vinavant."),
    "Radio as wake-up alarm: Settings › Wake-up alarm › Wake-up sound. Without internet the alarm takes its tone after 10 s.": (
        "Radio als Wecker: Einstellungen › Wecker › Weckton. Ohne Internet nimmt der Wecker nach 10 s seinen Ton.",
        "Radio comme réveil : Réglages › Réveil › Son du réveil. Sans internet, le réveil prend sa sonnerie après 10 s.",
        "Radio come sveglia: Impostazioni › Sveglia › Suono della sveglia. Senza internet la sveglia usa il suo suono dopo 10 s.",
        "Radio sco svegliarin: Parameters › Svegliarin › Tun dal svegliarin. Senza internet prenda il svegliarin ses tun suenter 10 s."),
    "paused": ("pausiert", "en pause", "in pausa", "en pausa"),
    "on air": ("läuft", "en direct", "in onda", "en emissiun"),
    "connecting …": ("verbindet …", "connexion …", "connessione …", "colliescha …"),
    "trying again": ("versucht es wieder", "nouvel essai", "nuovo tentativo", "emprova danovamain"),
    "stopped": ("gestoppt", "arrêtée", "fermata", "fermà"),
    "off": ("aus", "arrêt", "spento", "ora"),
    "No station yet": ("Noch kein Sender", "Pas encore de station", "Ancora nessuna stazione", "Anc nagin emettur"),
    "off in": ("aus in", "arrêt dans", "spento tra", "ora en"),
    "No loudspeaker selected: Settings › Light & sound › Loudspeaker.": (
        "Kein Lautsprecher gewählt: Einstellungen › Licht & Ton › Lautsprecher.", "Aucun haut-parleur choisi : Réglages › Lumière et son › Haut-parleur.",
        "Nessun altoparlante scelto: Impostazioni › Luce e suono › Altoparlante.", "Nagin autpledader tschernì: Parameters › Glisch e tun › Autpledader."),
    "No internet - the radio needs a connection.": ("Kein Internet – das Radio braucht eine Verbindung.", "Pas d’internet – la radio a besoin d’une connexion.",
                                                     "Niente internet – la radio ha bisogno di una connessione.", "Nagin internet – il radio dovra ina colliaziun."),
    "Next try in": ("Nächster Versuch in", "Prochain essai dans", "Prossimo tentativo tra", "Proxim emprov en"),
    "MoveEye has stopped trying - tap ▶ again later.": ("MoveEye hat aufgehört zu versuchen – später nochmals ▶ tippen.", "MoveEye a arrêté d’essayer – touche ▶ plus tard.",
                                                        "MoveEye ha smesso di provare – tocca ▶ più tardi.", "MoveEye ha chalà dad empruvar – tutga pli tard danovamain ▶."),
    "The station does not answer.": ("Der Sender antwortet nicht.", "La station ne répond pas.", "La stazione non risponde.", "L’emettur na respunda betg."),
    "Done": ("Fertig", "Terminé", "Fatto", "Finì"),
    "Edit": ("Bearbeiten", "Modifier", "Modifica", "Modifitgar"),
    "own address": ("eigene Adresse", "adresse propre", "indirizzo proprio", "atgna adressa"),
    "up": ("hinauf", "monter", "su", "ensi"),
    "down": ("hinunter", "descendre", "giù", "engiu"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "Remove this station?": ("Diesen Sender entfernen?", "Supprimer cette station ?", "Rimuovere questa stazione?", "Allontanar quest emettur?"),
    "search one below.": ("unten einen suchen.", "cherches-en une ci-dessous.", "cercane una qui sotto.", "tschertga in sutvart."),
    "Playing the radio needs the right «Siren / sounds».": ("Radio hören braucht das Recht «Sirene / Töne».", "Écouter la radio demande le droit «Sirène / sons».",
                                                           "Ascoltare la radio richiede il diritto «Sirena / suoni».", "Tadlar radio dovra il dretg «Sirena / tuns»."),
    "type at least 2 letters": ("mindestens 2 Buchstaben eingeben", "tape au moins 2 lettres", "scrivi almeno 2 lettere", "tippa almain 2 bustabs"),
    "searching …": ("sucht …", "recherche …", "ricerca …", "tschertga …"),
    "Nothing found.": ("Nichts gefunden.", "Rien trouvé.", "Nessun risultato.", "Chattà nagut."),
    "The radio is off.": ("Das Radio ist aus.", "La radio est arrêtée.", "La radio è spenta.", "Il radio è ora."),
    "Add stations, sleep timer (browser)": ("Sender hinzufügen, Einschlaf-Timer (Browser)", "Ajouter des stations, minuterie (navigateur)",
                                            "Aggiungi stazioni, timer (browser)", "Agiuntar emetturs, temporisatur (navigatur)"),
    "Paused: the siren / an alarm sound plays": ("Pausiert: die Sirene / ein Alarmton läuft", "En pause : la sirène / un son d’alarme joue",
                                                 "In pausa: suona la sirena / un suono d’allarme", "En pausa: la sirena / in tun d’alarm suna"),
    "Paused: MoveEye plays a sound": ("Pausiert: MoveEye spielt einen Ton", "En pause : MoveEye joue un son", "In pausa: MoveEye riproduce un suono", "En pausa: MoveEye suna in tun"),
    "Paused: announcement": ("Pausiert: Ansage", "En pause : annonce", "In pausa: annuncio", "En pausa: annunzia"),
    "Paused: somebody talks through the loudspeaker": ("Pausiert: jemand spricht über den Lautsprecher", "En pause : quelqu’un parle par le haut-parleur",
                                                       "In pausa: qualcuno parla dall’altoparlante", "En pausa: insatgi discurra tras l’autpledader"),
    "Paused: Morse / radio signal is being sent": ("Pausiert: Morse / Funksignal wird gesendet", "En pause : envoi morse / signal radio",
                                                   "In pausa: invio Morse / segnale radio", "En pausa: morse / signal da radio vegn tramess"),
    "Paused: the microphone receives Morse / radio signals (no feedback)": (
        "Pausiert: das Mikrofon empfängt Morse- / Funksignale (keine Rückkopplung)", "En pause : le microphone reçoit des signaux morse / radio (pas de larsen)",
        "In pausa: il microfono riceve segnali Morse / radio (niente ritorno)", "En pausa: il microfon retschaiva signals da morse / radio (nagin effect larsen)"),
    "Paused: the wake-up alarm rings": ("Pausiert: der Wecker klingelt", "En pause : le réveil sonne", "In pausa: la sveglia suona", "En pausa: il svegliarin scalina"),
    # errors (tr_err)
    "unknown station": ("unbekannter Sender", "station inconnue", "stazione sconosciuta", "emettur nunenconuschent"),
    "no internet": ("kein Internet", "pas d’internet", "niente internet", "nagin internet"),
    "no internet - the directory cannot be reached": ("kein Internet – das Verzeichnis ist nicht erreichbar", "pas d’internet – l’annuaire est injoignable",
                                                      "niente internet – l’elenco non è raggiungibile", "nagin internet – il register n’è betg cuntanschibel"),
    "the directory does not answer": ("das Verzeichnis antwortet nicht", "l’annuaire ne répond pas", "l’elenco non risponde", "il register na respunda betg"),
    "the station is not in the directory": ("der Sender ist nicht im Verzeichnis", "la station n’est pas dans l’annuaire", "la stazione non è nell’elenco", "l’emettur n’è betg en il register"),
    "the station has no address": ("der Sender hat keine Adresse", "la station n’a pas d’adresse", "la stazione non ha indirizzo", "l’emettur n’ha nagina adressa"),
    "the station is already in the list": ("der Sender ist schon in der Liste", "la station est déjà dans la liste", "la stazione è già nell’elenco", "l’emettur è gia en la glista"),
    "the list is full": ("die Liste ist voll", "la liste est pleine", "l’elenco è pieno", "la glista è plaina"),
    "not a valid address (http:// or https://)": ("keine gültige Adresse (http:// oder https://)", "adresse non valable (http:// ou https://)",
                                                  "indirizzo non valido (http:// o https://)", "nagina adressa valaivla (http:// u https://)"),
    "the radio is off": ("das Radio ist aus", "la radio est arrêtée", "la radio è spenta", "il radio è ora"),
    "sleep timer: the radio is off": ("Einschlaf-Timer: das Radio ist aus", "minuterie : la radio est arrêtée", "timer: la radio è spenta", "temporisatur: il radio è ora"),
    "the station stopped sending": ("der Sender sendet nicht mehr", "la station n’émet plus", "la stazione non trasmette più", "l’emettur na trametta betg pli"),
    "the station sends no sound": ("der Sender liefert keinen Ton", "la station n’envoie pas de son", "la stazione non invia suono", "l’emettur na furnescha nagin tun"),
    "the station does not answer": ("der Sender antwortet nicht", "la station ne répond pas", "la stazione non risponde", "l’emettur na respunda betg"),
    "no sound from the station": ("kein Ton vom Sender", "aucun son de la station", "nessun suono dalla stazione", "nagin tun da l’emettur"),
    "Only for the administrator": ("Nur für den Administrator", "Uniquement pour l’administrateur", "Solo per l’amministratore", "Mo per l’administratur"),
    "ffmpeg is missing (sudo apt install ffmpeg)": ("ffmpeg fehlt (sudo apt install ffmpeg)", "ffmpeg manque (sudo apt install ffmpeg)",
                                                    "manca ffmpeg (sudo apt install ffmpeg)", "ffmpeg manca (sudo apt install ffmpeg)"),
}
for _k, _v in _HX_RADIO.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_RADIO_DE = {_k: DE.get(_k, _v[0]) for _k, _v in _HX_RADIO.items()}
_RADIO_DE.update({k: DE[k] for k in ("More", "Stop", "Wake-up alarm", "No connection to MoveEye.", "not allowed for your user") if DE.get(k)})
MORE_DE.update({k: _HX_RADIO[k][0] for k in ("Radio", "Internet radio on the loudspeaker", "While the radio plays: noise alarm and clap switch paused - the camera alarm works as usual")})

# ---- the manual: a section «Radio» ----------------------------------------------------------------------------------------------
_HELP_RADIO = {
    "de": ('<section id="radio" data-icon="📻"><h2>Radio</h2><ul>'
           '<li><b>Was:</b> Mehr → «📻 Radio»: Internet-Radio auf dem Lautsprecher von MoveEye. Ab Werk «Radio Pilatus» (Luzern). Weitere Sender sucht der '
           'Administrator im offenen Verzeichnis radio-browser.info oder fügt eine Stream-Adresse ein (MP3, AAC, Ogg, .pls, .m3u); ordnen und entfernen mit «Bearbeiten». '
           'Die Liste gilt für dieses Gerät.</li>'
           '<li><b>Vorrang:</b> Sirene, Alarmtöne, Ansagen, Gegensprechen, Morse / Funk senden und der Wecker gehen immer vor – das Radio pausiert und spielt danach weiter. '
           'Solange das Mikrofon im Morse-Modus Ton empfängt, pausiert es ebenfalls (keine Rückkopplung). Solange das Radio spielt, hört der Geräusch-Alarm nicht mit.</li>'
           '<li><b>Lautstärke</b> eigener Regler (nicht die Sirene). <b>Einschlaf-Timer</b> 15 / 30 / 60 / 90 Minuten, am Ende leiser bis aus.</li>'
           '<li><b>Radio als Wecker:</b> Einstellungen → Wecker → Weckton «📻 …». Kommt nach 10 s kein Ton (kein Internet, Sender gestört), nimmt der Wecker seine Melodie.</li>'
           '<li><b>Ohne Internet:</b> MoveEye versucht es nach 5, 10, 20, 40 und 80 s nochmals und hört dann auf; die Karte sagt es. Später wieder ▶.</li>'
           '<li><b>📱 Im Browser hören:</b> auf der Karte «Wo spielen» → «📱 dieser Browser» (pro Browser gemerkt). Das Handy spielt den Sender, der '
           'MoveEye-Lautsprecher bleibt still, Geräusch-Alarm und Klatschschalter hören weiter. Geht der Sender nicht direkt (http auf einer https-Seite, Sender '
           'sperrt Browser), läuft er unverändert über MoveEye (/radio/stream, höchstens 2 Zuhörer, nur Sender der Liste). Lautstärke und Einschlaf-Timer gelten '
           'nur in diesem Browser; auf dem Sperrbildschirm erscheinen Titel und Knöpfe.</li>'
           '<li><b>Rechte:</b> abspielen und stoppen darf, wer Töne darf (Recht «Sirene»); die Senderliste nur der Administrator. Im Pi-Fenster: Mehr → «📻 Radio».</li>'
           '</ul></section>\n'),
    "en": ('<section id="radio" data-icon="📻"><h2>Radio</h2><ul>'
           '<li><b>What:</b> More → «📻 Radio»: internet radio on the loudspeaker of MoveEye. Out of the box «Radio Pilatus» (Lucerne). The administrator finds more '
           'stations in the open directory radio-browser.info or pastes a stream address (MP3, AAC, Ogg, .pls, .m3u); sort and remove with «Edit». The list belongs to this device.</li>'
           '<li><b>Priority:</b> siren, alarm sounds, announcements, talking, sending Morse / radio signals and the wake-up alarm always go first - the radio pauses and plays on '
           'afterwards. While the microphone receives sound in the Morse mode it pauses too (no feedback). While the radio plays, the noise alarm does not listen.</li>'
           '<li><b>Volume</b> has its own slider (not the siren). <b>Sleep timer</b> 15 / 30 / 60 / 90 minutes, quieter at the end until off.</li>'
           '<li><b>Radio as wake-up alarm:</b> Settings → Wake-up alarm → Wake-up sound «📻 …». No sound after 10 s (no internet, station down): the alarm takes its melody.</li>'
           '<li><b>Without internet:</b> MoveEye tries again after 5, 10, 20, 40 and 80 s and then stops; the card says so. Tap ▶ later.</li>'
           '<li><b>📱 Listen in the browser:</b> on the card «Where to play» → «📱 this browser» (remembered per browser). The phone plays the station, the '
           'MoveEye loudspeaker stays silent, the noise alarm and the clap switch keep listening. If the station does not play directly (http on an https page, '
           'the station refuses browsers), it runs unchanged through MoveEye (/radio/stream, at most 2 listeners, only stations of the list). Volume and sleep timer '
           'apply only in this browser; the lock screen shows the title and the buttons.</li>'
           '<li><b>Rights:</b> whoever may use sounds (right «siren») may play and stop; the station list only the administrator. Pi window: More → «📻 Radio».</li>'
           '</ul></section>\n'),
    "fr": ('<section id="radio" data-icon="📻"><h2>Radio</h2><ul>'
           '<li>Plus → «📻 Radio» : radio internet sur le haut-parleur de MoveEye. D’origine «Radio Pilatus» (Lucerne) ; l’administrateur cherche d’autres stations dans '
           'l’annuaire ouvert radio-browser.info ou colle une adresse de flux.</li>'
           '<li>Sirène, alarmes, annonces, morse et réveil passent avant : la radio fait une pause puis reprend. Tant que la radio joue, l’alarme sonore n’écoute pas.</li>'
           '<li>Minuterie de sommeil 15 / 30 / 60 / 90 min. Radio comme réveil : Réglages → Réveil → Son du réveil ; sans son après 10 s, le réveil prend sa mélodie.</li>'
           '<li>Sans internet, MoveEye réessaie après 5, 10, 20, 40 et 80 s puis s’arrête.</li></ul></section>\n'),
    "it": ('<section id="radio" data-icon="📻"><h2>Radio</h2><ul>'
           '<li>Altro → «📻 Radio»: radio internet sull’altoparlante di MoveEye. Di fabbrica «Radio Pilatus» (Lucerna); l’amministratore cerca altre stazioni '
           'nell’elenco aperto radio-browser.info o incolla un indirizzo di stream.</li>'
           '<li>Sirena, allarmi, annunci, Morse e sveglia hanno la precedenza: la radio fa una pausa e poi riprende. Mentre la radio suona, l’allarme rumore non ascolta.</li>'
           '<li>Timer per dormire 15 / 30 / 60 / 90 min. Radio come sveglia: Impostazioni → Sveglia → Suono della sveglia; senza suono dopo 10 s la sveglia usa la sua melodia.</li>'
           '<li>Senza internet MoveEye riprova dopo 5, 10, 20, 40 e 80 s e poi smette.</li></ul></section>\n'),
    "rm": ('<section id="radio" data-icon="📻"><h2>Radio</h2><ul>'
           '<li>Dapli → «📻 Radio»: radio d’internet sin l’autpledader da MoveEye. Da fabrica «Radio Pilatus» (Lucerna); l’administratur tschertga ulteriurs emetturs en '
           'il register avert radio-browser.info u encolla ina adressa da stream.</li>'
           '<li>Sirena, alarms, annunzias, morse ed il svegliarin han la precedenza: il radio fa pausa e suna suenter vinavant. Uschè ditg ch’il radio suna, na taidla l’alarm da canera betg.</li>'
           '<li>Temporisatur 15 / 30 / 60 / 90 min. Radio sco svegliarin: Parameters → Svegliarin → Tun dal svegliarin; senza tun suenter 10 s prenda il svegliarin sia melodia.</li>'
           '<li>Senza internet emprova MoveEye anc ina giada suenter 5, 10, 20, 40 ed 80 s e chala lura.</li></ul></section>\n'),
}


def _help_radio(doc, lang):
    if 'id="radio"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_RADIO[lang] + doc[i:] if i >= 0 else doc


_hp_en_radio = HELP_PAGE.find('<div lang="en">')
if _hp_en_radio > 0:
    HELP_PAGE = _help_radio(HELP_PAGE[:_hp_en_radio], "de") + _help_radio(HELP_PAGE[_hp_en_radio:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_radio(HELP_X[_L], _L)


# ---- self-test (no network, no process) -------------------------------------------------------------------------------------------
def radio_selftest():
    lst = radio_clean(RADIO_DEF["radio_stations"])
    assert lst and lst[0]["name"] == "Radio Pilatus" and "url" not in lst[0] and lst[0]["find"]["cc"] == "CH", "default: Pilatus by name, no guessed address"
    assert radio_url_ok("https://a.example/live.mp3") and radio_url_ok("http://1.2.3.4:8000/;") and not any(
        radio_url_ok(u) for u in ("file:///etc/passwd", "javascript:alert(1)", "http://u:p@x.example/", "http:// x", "ftp://x.example/a", "https://..x/"))
    bad = radio_clean([{"id": "A B", "name": "x", "url": "http://x.example/"}, {"id": "ok", "name": "", "url": "http://x.example/"}, {"id": "n", "name": "N"},
                       {"id": "d", "name": "D\x00\x1b", "url": "http://x.example/"}, {"id": "d", "name": "twice", "url": "http://y.example/"}])
    assert [e["id"] for e in bad] == ["d"] and bad[0]["name"] == "D", bad
    assert radio_playlist_urls("[playlist]\nNumberOfEntries=2\nFile1=http://a.example/s1\nTitle1=x\nFile2=s2.mp3\n", "http://b.example/l/x.pls") == \
        ["http://a.example/s1", "http://b.example/l/s2.mp3"]
    assert radio_playlist_urls("#EXTM3U\n#EXTINF:-1,X\nhttps://c.example/live\n\nrel.aac\nfile:///etc/x\n", "https://c.example/p/a.m3u") == \
        ["https://c.example/live", "https://c.example/p/rel.aac"]
    assert radio_icy_title(b"StreamTitle='AC/DC - It\xe2\x80\x99s a long way';StreamUrl='';") == "AC/DC - It’s a long way"
    assert radio_icy_title(b"StreamTitle='Caf\xe9;mix';\x00\x00") == "Café;mix" and radio_icy_title(b"nothing") is None
    assert radio_icy_title(b"StreamTitle='a\x1b[31mb';") == "a [31mb"
    keep = {k: RADIO[k] for k in ("want", "hold_t", "hold_why", "wake")}
    snd, tlk, wk = dict(SOUND), TALK["proc"], WAKE.get("state")
    try:
        RADIO.update(want=True, hold_t=0.0, wake=False); SOUND["playing"] = False; TALK["proc"] = None; WAKE["state"] = "off"
        assert radio_held() == ""
        SOUND.update(playing=True, kind="siren"); assert radio_held() == "siren"
        SOUND.update(kind="tts"); assert radio_held() == "voice"
        SOUND.update(playing=False); WAKE["state"] = "ring"; assert radio_held() == "wake"
        RADIO["wake"] = True; assert radio_held() == ""
        WAKE["state"] = "off"; RADIO["wake"] = False
        radio_yield("voice"); assert radio_held() == "voice" and RADIO["out"] is None, "after a sound: a short gap"
    finally:
        SOUND.clear(); SOUND.update(snd); TALK["proc"] = tlk; WAKE["state"] = wk; RADIO.update(keep)
    assert role_allows("family", "/api/radio", "POST", {"action": "play"}) and not role_allows("view", "/api/radio", "POST", {"action": "play"})
    assert not role_allows("family", "/api/radio", "POST", {"action": "add"}) and role_allows("view", "/api/radio", "GET", {}) and role_allows("kid", "/radio", "GET", {})
    assert radio_may("admin", None, True) and not radio_may("family", None, True) and radio_may("custom", ["siren"]) and not radio_may("custom", ["live"])
    assert ("radio:pilatus" in [c for c, _l in text_choice_pairs("wake_sound")]) == bool(radio_station("pilatus")), "wake-up sound: the stations"
    assert all(DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")) for k in _HX_RADIO), "texts in 5 languages"
    assert radio_offline_err(_rsock.gaierror(-2, "x")) and not radio_offline_err(ConnectionRefusedError(111, "x"))
    assert len(RADIO_BACKOFF) == 5 and sum(RADIO_BACKOFF) < 200, "no endless tries"
    assert role_allows("family", "/radio/stream/pilatus", "GET", {}) and not role_allows("view", "/radio/stream/pilatus", "GET", {}), "the proxy: the right to play"
    assert radio_br_proxy("../x")[0] == 404 and radio_br_proxy("nichtda")[0] == 404 and RADIO_BR_MAX == 2, "the proxy: only stations of the list"
    return "Pilatus by name (no guessed address), addresses, play lists, ICY titles, priority / pause, rights, wake-up sound, texts, back-off"


SELFTEST_EXTRA.append(("Radio: stations, play lists, ICY, priority, rights (639zzzzd)", radio_selftest))
