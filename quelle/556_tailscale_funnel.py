#@ MoveEye – Teil 556: Online-Spiel über Tailscale Funnel – nur der Spiel-Pfad /game/ öffentlich im Internet (Freunde ohne Tailscale), eigene Tür nur für /game/, Sperre aller anderen Adressen bei Funnel-Anfragen, automatisch aus (letzte Einladung weg, Höchstzeit, Neustart), klare Fehler mit Abhilfe. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Daniel 30.10.2026 («Tailscale-Tunnel einbauen»): friends WITHOUT Tailscale join the online game (343) from home.
#   Switch «Online-Spiel über Tailscale Funnel» next to the invitations (web 544, window 592). Only an administrator may switch
#   it on (web: g.role == "admin" and no app key, else 403; window: not in operator mode).
#   How it is built (three walls, each one alone keeps the rest of MoveEye private):
#     1. Tailscale publishes only the path /game:  tailscale funnel --bg --https=<443|8443|10000> --set-path=/game http://127.0.0.1:<door>/game
#        (443 only when it is not used by «https über Tailscale» / other serve settings, else 8443, else 10000).
#     2. <door> is an own small web server on 127.0.0.1 (random free port, only while the funnel is on) in front of the same
#        Flask app: it lets through only /game/<token>/, /game/<token>/info, /manifest.json and /ws (GET), everything else -> 404.
#     3. MoveEye itself (all doors): a request with the header «Tailscale-Funnel-Request» (Tailscale sets it on funnel traffic)
#        gets 404 for anything but the game paths - before the login, independent of it.
#   Auto-off: the last invitation expired / revoked, no invitation within 15 min, the maximum time (CFG game_funnel_hours,
#   default 6, 1-24 h). The state is saved before the funnel goes on, so a restart (also after a crash) switches it off.
#   Every on / off is in the log and in the protocol of the invitations (GINV log), switching on sends a push «Online-Spiel öffentlich».
_FUN_CFG = {"game_funnel_hours": 6, "game_funnel_state": {}}
for _k, _v in _FUN_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
FUNNEL_PORTS = (443, 8443, 10000)
FUNNEL_HOURS = (1, 2, 3, 6, 12, 24)
FUNNEL_GRACE_S = 900                               # switched on without an invitation: 15 min to make one
FUNNEL_PATH_RE = re.compile(r"^/game/[A-Za-z0-9_-]{1,64}(/|/info|/manifest\.json|/ws)?$")
FUNNEL_DOCS = "https://tailscale.com/kb/1223/funnel"
FUNNEL_LINKS = {"install": ("Install Tailscale (official guide)", "https://tailscale.com/download/linux"),
                "login": ("Tailscale: log in a device", "https://tailscale.com/kb/1017/install"),
                "dns": ("Tailscale admin console → DNS", "https://login.tailscale.com/admin/dns"),
                "https": ("Docs: enabling HTTPS certificates", "https://tailscale.com/kb/1153/enabling-https"),
                "acl": ("Tailscale admin console → Access controls", "https://login.tailscale.com/admin/acls/file"),
                "funnel": ("Docs: Tailscale Funnel", FUNNEL_DOCS),
                "cli": ("Docs: tailscale funnel command", "https://tailscale.com/kb/1311/tailscale-funnel"),
                "operator": ("Docs: tailscale set --operator", "https://tailscale.com/kb/1080/cli")}
FUNNEL = {"lock": threading.RLock(), "on": False, "port": 0, "door": 0, "url": "", "t_on": 0.0, "until": 0.0, "srv": None,
          "had_inv": False, "err": None, "why_off": "", "legacy": False, "gen": 0, "ts": {"t": 0.0, "v": None}}


def _fun_exe():
    return shutil.which("tailscale")


def _fun_run1(cmd, timeout):
    """(rc, text) - also the text printed before a timeout (Tailscale prints the «enable» link and then waits)"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    except subprocess.TimeoutExpired as e:
        parts = []
        for x in (e.stdout, e.stderr):
            if isinstance(x, bytes):
                x = x.decode("utf-8", "replace")
            parts.append(x or "")
        return 124, ("\n".join(parts).strip() + "\n(timeout)").strip()
    except OSError as e:
        return 127, str(e)


def _fun_denied(txt):
    return bool(re.search(r"access denied|permission denied|not permitted|operator|must be root|requires root|use 'sudo", txt or "", re.I))


def _fun_run(args, timeout=25):
    """tailscale <args>: first as this user, then with «sudo -n» when Tailscale says no rights (like tailscale_https)"""
    exe = _fun_exe()
    if not exe:
        return 127, "Tailscale is not installed"
    rc, txt = _fun_run1([exe] + list(args), timeout)
    if rc != 0 and _fun_denied(txt) and shutil.which("sudo"):
        rc2, txt2 = _fun_run1(["sudo", "-n", exe] + list(args), timeout)
        if rc2 == 0 or not re.search(r"password is required|a terminal is required|not in the sudoers", txt2, re.I):
            return rc2, txt2
    return rc, txt


def _fun_save_now():
    """the funnel state is written at once (save_settings waits up to 15 s - a crash then would forget the public path)"""
    try:
        save_settings_now()
    except Exception:
        save_settings()


def funnel_ts(force=False):
    """tailscale_status() (090), at most every 20 s"""
    now = time.time()
    if force or FUNNEL["ts"]["v"] is None or now - FUNNEL["ts"]["t"] > 20:
        try:
            v = tailscale_status()
        except Exception:
            v = {"state": "error", "name": ""}
        FUNNEL["ts"] = {"t": now, "v": v}
    return FUNNEL["ts"]["v"]


def funnel_serve_cfg():
    """the serve / funnel settings of Tailscale as dict (ServeConfig: TCP, Web, AllowFunnel) or None"""
    rc, txt = _fun_run(["serve", "status", "--json"], timeout=10)
    if rc != 0:
        return None
    i = txt.find("{")
    try:
        j = json.loads(txt[i:]) if i >= 0 else {}
    except ValueError:
        return None
    return j if isinstance(j, dict) else None


def _fun_ours(h):
    """a serve handler made by this feature: the path /game to 127.0.0.1:<port>/game"""
    return bool(re.match(r"^http://127\.0\.0\.1:\d+/game/?$", str((h or {}).get("Proxy") or "")))


def funnel_pick_port(cfg):
    """443 if free, else 8443, else 10000 (only these three are allowed for Funnel); 0 = all used"""
    used = set()
    for k in ((cfg or {}).get("TCP") or {}):
        used.add(str(k))
    for hp, w in ((cfg or {}).get("Web") or {}).items():
        hs = (w or {}).get("Handlers") or {}
        if any(not (p.rstrip("/") == "/game" and _fun_ours(h)) for p, h in hs.items()):
            used.add(str(hp).rsplit(":", 1)[-1])
    if cfg is None:                                      # no status: at least keep «https über Tailscale» (443) free
        try:
            if _tailscale_https_url_base():
                used.add("443")
        except Exception:
            pass
    for p in FUNNEL_PORTS:
        if str(p) not in used:
            return p
    return 0


def funnel_explain(txt, code=""):
    """the error as {"code", "msg", "steps": [..], "cmd": "...", "links": [(label, url)], "raw"} - what exactly to do"""
    t_ = str(txt or "")
    low = t_.lower()
    enable = re.findall(r"https://login\.tailscale\.com/f/[^\s\"'<>]+", t_)
    E = {"code": code, "msg": "", "steps": [], "cmd": "", "links": [], "raw": t_.strip()[-300:]}
    L = lambda *ks: [FUNNEL_LINKS[k] for k in ks]
    if code == "notinstalled" or (not code and "not installed" in low):
        E.update(code="notinstalled", msg="Tailscale is not installed on this device.",
                 steps=["Install it on the Pi and log in once:"], cmd="curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up", links=L("install", "funnel"))
    elif code == "login" or (not code and re.search(r"needslogin|not logged in|logged out|tailscale up|stopped", low)):
        E.update(code="login", msg="Tailscale is not logged in or stopped.",
                 steps=["On the Pi start Tailscale and log in with your account (it shows a link):"], cmd="sudo tailscale up", links=L("login"))
    elif re.search(r"funnel", low) and re.search(r"not enabled|not available|node ?attr|nodeattrs|not allowed|policy|/f/funnel|no-funnel", low):
        E.update(code="funnel", msg="Funnel is not allowed in your tailnet policy.",
                 steps=["Tailscale admin console → Access controls: add the node attribute «funnel» (lines below) and save.",
                        "Also needed: DNS → MagicDNS on and «HTTPS Certificates» enabled.", "Then switch the funnel on again here."],
                 cmd='"nodeAttrs": [\n  {"target": ["autogroup:member"], "attr": ["funnel"]}\n]', links=L("acl", "funnel"))
        if enable:
            E["steps"].insert(0, "Easiest: open this link once – Tailscale enables Funnel for this device:")
            E["links"] = [("Enable Funnel (Tailscale link)", enable[0])] + E["links"]
    elif re.search(r"https", low) and re.search(r"not enabled|disabled|cert|/f/serve|serve is not enabled", low) or "serve is not enabled" in low:
        E.update(code="https", msg="HTTPS certificates are not enabled in your tailnet.",
                 steps=["Tailscale admin console → DNS: switch on MagicDNS.", "On the same page under «HTTPS Certificates» click «Enable HTTPS».",
                        "Then switch the funnel on again here."], links=L("dns", "https"))
        if enable:
            E["links"] = [("Enable HTTPS (Tailscale link)", enable[0])] + E["links"]
    elif _fun_denied(t_) or re.search(r"password is required|sudoers", low):
        E.update(code="perm", msg="MoveEye may not change the Tailscale settings.",
                 steps=["Once on the Pi (as the user MoveEye runs as), then switch on again:"], cmd="sudo tailscale set --operator=$USER", links=L("operator"))
    elif code == "ports":
        E.update(code="ports", msg="All three Funnel ports (443, 8443, 10000) are already used by other Tailscale serve settings.",
                 steps=["Look at them and switch one off:"], cmd="tailscale serve status", links=L("cli"))
    elif code == "door":
        E.update(code="door", msg="The game door of MoveEye could not start.", steps=["Restart MoveEye and try again."])
    elif "(timeout)" in low or code == "timeout":
        E.update(code="timeout", msg="Tailscale did not answer in time.", steps=["Check «tailscale status» on the Pi and try again."], cmd="tailscale status", links=L("funnel"))
    else:
        E.update(code=code or "other", msg="Tailscale refused the funnel.", steps=["Message of Tailscale:"], cmd=t_.strip()[-300:], links=L("funnel", "cli"))
    return E


def funnel_avail():
    """'' when Tailscale is ready for the funnel, else the error code (notinstalled / login)"""
    if not _fun_exe():
        return "notinstalled"
    st = funnel_ts()
    if str(st.get("state")) != "Running" or not st.get("name"):
        return "login"
    return ""


# ---- the own door for the funnel: only the game paths, only 127.0.0.1, only while the funnel is on ----------------------------
def _funnel_door_app(app):
    def door(environ, start_response):
        p = environ.get("PATH_INFO") or "/"
        if p.startswith("/game/game/"):                     # an old Tailscale that does not strip the mount path
            p = p[5:]; environ["PATH_INFO"] = p
        environ["HTTP_TAILSCALE_FUNNEL_REQUEST"] = environ.get("HTTP_TAILSCALE_FUNNEL_REQUEST") or "?1"   # all here is funnel traffic
        environ["mw.funnel"] = True
        if not FUNNEL["on"] or environ.get("REQUEST_METHOD", "GET") not in ("GET", "HEAD") or not FUNNEL_PATH_RE.match(p):
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8"), ("Cache-Control", "no-store"), ("X-Robots-Tag", "noindex")])
            return [b"Not found"]
        return app(environ, start_response)
    return door


def funnel_door_start():
    app = FUNNEL.get("app")
    if app is None:
        return 0
    if FUNNEL["srv"] is not None:
        return FUNNEL["door"]
    try:
        from werkzeug.serving import make_server
        srv = make_server("127.0.0.1", 0, _funnel_door_app(app), threaded=True)
    except Exception as e:
        log_event("web", f"Funnel game door could not start: {e}"[:200])
        return 0
    FUNNEL["srv"], FUNNEL["door"] = srv, int(srv.server_port)
    threading.Thread(target=srv.serve_forever, daemon=True, name="funnel-door").start()
    return FUNNEL["door"]


def funnel_door_stop():
    srv, FUNNEL["srv"], FUNNEL["door"] = FUNNEL["srv"], None, 0
    if srv is not None:
        threading.Thread(target=srv.shutdown, daemon=True).start()


def _funnel_url(name, port):
    return f"https://{name}" + ("" if int(port) == 443 else f":{int(port)}")


def _fun_off_cmds(port, legacy=False):
    new = [["funnel", f"--https={port}", "--set-path=/game", "off"]]
    old = [["funnel", str(port), "off"], ["serve", f"https:{port}", "/game", "off"]]
    return (old + new) if legacy else (new + old)


def _funnel_remove(port, legacy=False):
    """removes the path /game on <port> again; True when Tailscale shows no handler of ours there any more"""
    ok = False
    if legacy:                                          # Tailscale before 1.52: funnel off, then the serve path
        ok = all([_fun_run(c, timeout=20)[0] == 0 for c in _fun_off_cmds(port, True)[:2]])
    else:
        for c in _fun_off_cmds(port):
            rc, txt = _fun_run(c, timeout=20)
            if rc == 0:
                ok = True
                break
            if not re.search(r"flag provided but not defined|unknown|usage|invalid", txt, re.I):
                break
    cfg = funnel_serve_cfg()
    if cfg is not None:
        left = [hp for hp, w in (cfg.get("Web") or {}).items() if str(hp).endswith(f":{port}")
                and any(p.rstrip("/") == "/game" and _fun_ours(h) for p, h in ((w or {}).get("Handlers") or {}).items())]
        ok = not left
    return ok


def funnel_pw_set():
    """a web password (or a password per user) is set - otherwise everybody in the network is administrator"""
    return bool(CFG.get("web_password") or CFG.get("web_pw_hash"))


def funnel_on(hours=None, source="web"):
    """(True, None) or (False, error dict)"""
    with FUNNEL["lock"]:
        if CFG.get("lock_on"):
            return False, {"code": "locked", "msg": "Not possible in operator mode", "steps": [], "cmd": "", "links": [], "raw": ""}
        if not funnel_pw_set():                           # 2.98.47 (Daniel): only with a web password - without one everybody is admin
            return False, {"code": "nopw", "msg": "Set a web password first - without one everybody in the network is administrator",
                           "steps": ["Settings → 🔒 Password: set a web password, then switch the funnel on."], "cmd": "", "links": [], "raw": ""}
        h = float(hours if hours is not None else CFG.get("game_funnel_hours") or 6)
        h = max(0.05, min(24.0, h))                       # the switch: 1-24 h; inside (moving the port) also the rest of an hour
        if hours is not None:
            CFG["game_funnel_hours"] = int(h) if h == int(h) else h
        if FUNNEL["on"]:
            FUNNEL["until"] = time.time() + h * 3600
            CFG["game_funnel_state"] = dict(CFG.get("game_funnel_state") or {}, until=int(FUNNEL["until"])); save_settings()
            return True, None
        av = funnel_avail()
        if av == "login":
            funnel_ts(force=True); av = funnel_avail()
        if av:
            FUNNEL["err"] = funnel_explain("", av); return False, FUNNEL["err"]
        name = funnel_ts()["name"]
        cfg = funnel_serve_cfg()
        port = funnel_pick_port(cfg)
        if not port:
            FUNNEL["err"] = funnel_explain("", "ports"); return False, FUNNEL["err"]
        door = funnel_door_start()
        if not door:
            FUNNEL["err"] = funnel_explain("", "door"); return False, FUNNEL["err"]
        until = time.time() + h * 3600
        CFG["game_funnel_state"] = {"port": port, "door": door, "until": int(until), "name": name}   # first saved: a crash is cleaned up too
        _fun_save_now()
        tgt = f"http://127.0.0.1:{door}/game"
        rc, txt = _fun_run(["funnel", "--bg", f"--https={port}", "--set-path=/game", tgt], timeout=25)
        legacy = False
        if rc != 0 and re.search(r"flag provided but not defined|unknown flag", txt, re.I):     # Tailscale before 1.52
            legacy = True
            rc, txt = _fun_run(["serve", f"https:{port}", "/game", tgt], timeout=25)
            if rc == 0:
                rc, txt = _fun_run(["funnel", str(port), "on"], timeout=25)
                if rc != 0:
                    _fun_run(["serve", f"https:{port}", "/game", "off"], timeout=15)
        if rc != 0:
            funnel_door_stop()
            CFG["game_funnel_state"] = {}; _fun_save_now()
            FUNNEL["err"] = funnel_explain(txt)
            log_event("web", f"Online game over Tailscale Funnel could not be switched on: {FUNNEL['err']['msg']} ({txt.strip()[:120]})")
            return False, FUNNEL["err"]
        act = [x for x in ginv_list() if ginv_valid(x)]
        FUNNEL.update(on=True, port=port, url=_funnel_url(name, port), t_on=time.time(), until=until, had_inv=bool(act), err=None, why_off="",
                      legacy=legacy, gen=FUNNEL["gen"] + 1)
        gen = FUNNEL["gen"]
    msg = f"Online game public over Tailscale Funnel: switched on ({source}, {h:g} h, {FUNNEL['url']}/game/…)"
    log_event("web", msg)
    ginv_note("MoveEye", f"Funnel on: {FUNNEL['url']}/game/… ({h:g} h)", None, False)
    try:
        w = WATCH_REF["w"]
        if w is not None:
            w.notifier.info(trf("The online game is public on the internet for {h} h (only the game, through Tailscale Funnel)", h=f"{h:g}"),
                            title="{name}: " + tr("Online game public"))
    except Exception:
        pass
    threading.Thread(target=_funnel_watch, args=(gen,), daemon=True, name="funnel-watch").start()
    return True, None


def funnel_off(reason="switched off", source="web"):
    with FUNNEL["lock"]:
        st = dict(CFG.get("game_funnel_state") or {})
        was = FUNNEL["on"] or bool(st.get("port"))
        port = FUNNEL["port"] or int(st.get("port") or 0)
        FUNNEL.update(on=False, gen=FUNNEL["gen"] + 1, why_off=reason if source == "auto" else "")
        ok = _funnel_remove(port, FUNNEL["legacy"]) if port else True
        funnel_door_stop()
        CFG["game_funnel_state"] = {}; _fun_save_now()
        FUNNEL.update(port=0, url="", until=0.0, t_on=0.0)
    if was:
        log_event("web", f"Online game over Tailscale Funnel: switched off ({source}: {reason})" + ("" if ok else " - Tailscale still shows the path, check «tailscale serve status»"))
        ginv_note("MoveEye", f"Funnel off ({reason})", None, False)
    return ok


def funnel_check():
    """auto-off: maximum time, the last invitation gone, no invitation in 15 min"""
    if not FUNNEL["on"]:
        return
    now = time.time()
    act = [x for x in ginv_list() if ginv_valid(x)]
    if act:
        FUNNEL["had_inv"] = True
    if now >= FUNNEL["until"]:
        funnel_off("maximum time over", "auto")
    elif not act and FUNNEL["had_inv"]:
        funnel_off("the last invitation expired or was revoked", "auto")
    elif not act and now - FUNNEL["t_on"] > FUNNEL_GRACE_S:
        funnel_off("no invitation within 15 minutes", "auto")


def _funnel_watch(gen):
    n = 0
    while FUNNEL["on"] and FUNNEL["gen"] == gen:
        time.sleep(5)
        if not FUNNEL["on"] or FUNNEL["gen"] != gen:
            return
        try:
            funnel_check()
            n += 1
            if n % 12 == 0 and FUNNEL["on"]:                # every minute: still there? (e.g. «tailscale serve reset»)
                cfg = funnel_serve_cfg()
                if cfg is not None and not any(str(hp).endswith(f":{FUNNEL['port']}") and "/game" in ((w or {}).get("Handlers") or {})
                                               for hp, w in (cfg.get("Web") or {}).items()):
                    funnel_off("removed in Tailscale", "auto")
        except Exception as e:
            log_event("web", f"Funnel check: {e}"[:160])


def funnel_cleanup():
    """at the start of MoveEye: a funnel of the last run is switched off (no forgotten public access)"""
    st = CFG.get("game_funnel_state") or {}
    if not st.get("port"):
        return False
    port = int(st["port"])
    ok = _funnel_remove(port)
    CFG["game_funnel_state"] = {}; _fun_save_now()
    log_event("web", f"Online game: the Tailscale Funnel of the last run (port {port}) was switched off at the start" + ("" if ok else " - check «tailscale serve status»"))
    ginv_note("MoveEye", "Funnel of the last run switched off at the start", None, False)
    return ok


def funnel_state(lang=None, admin=True):
    on = FUNNEL["on"]
    av = funnel_avail() if not on else ""
    def tx(e):
        return {"code": e["code"], "msg": tr_err(e["msg"], lang), "steps": [tr(s, lang) for s in e["steps"]], "cmd": e["cmd"],
                "links": [{"t": tr(a, lang), "u": b} for a, b in e["links"]], "raw": e.get("raw", "")} if e else None
    e = tx(FUNNEL["err"])
    need = tx(funnel_explain("", av)) if (av and not e) else None          # what is missing before the switch can work
    return {"on": on, "url": (FUNNEL["url"] + "/game/…/") if on else "", "base": FUNNEL["url"], "port": FUNNEL["port"],
            "left_s": max(0, int(FUNNEL["until"] - time.time())) if on else 0, "hours": CFG.get("game_funnel_hours") or 6, "choices": list(FUNNEL_HOURS),
            "avail": av == "", "why": av, "err": e, "need": need, "why_off": tr(FUNNEL["why_off"], lang) if FUNNEL["why_off"] else "",
            "grace_s": max(0, int(FUNNEL_GRACE_S - (time.time() - FUNNEL["t_on"]))) if on and not FUNNEL["had_inv"] else 0,
            "can": bool(admin) and not CFG.get("lock_on") and (on or funnel_pw_set()), "nopw": not funnel_pw_set(), "docs": FUNNEL_DOCS}


def funnel_status_line(lang=None):
    """one line for the window / the page: on/off, address, time left"""
    s = funnel_state(lang)
    if s["on"]:
        m = s["left_s"] // 60
        return f"🌍 {tr('Funnel on', lang)} · {s['url']} · {tr('time left', lang)} {m // 60}:{m % 60:02d} {tr('h', lang)}"
    return "⚪ " + tr("Funnel off", lang) + (f" ({s['why_off']})" if s["why_off"] else "")


# ---- wrapped functions of 050 / 343 ----------------------------------------------------------------------------------------------
_tailscale_https_url_base = tailscale_https_url


def tailscale_https_url():
    """«https über Tailscale» only when «/» is served on 443 (the funnel path /game alone is not the page)"""
    st = CFG.get("game_funnel_state") or {}
    if not (FUNNEL["on"] or st.get("port")):
        return _tailscale_https_url_base()
    ts = funnel_ts()
    cfg = funnel_serve_cfg()
    if cfg is None or not ts.get("name"):
        return _tailscale_https_url_base()
    hs = ((cfg.get("Web") or {}).get(f"{ts['name']}:443") or {}).get("Handlers") or {}
    return f"https://{ts['name']}/" if "/" in hs else ""


_tailscale_https_base = tailscale_https


def tailscale_https(on=True):
    """«https über Tailscale» on / off keeps the funnel: a funnel on 443 moves (off, then on again with the same end time)"""
    if not (FUNNEL["on"] and FUNNEL["port"] == 443):
        return _tailscale_https_base(on)
    left_h = max(0.05, (FUNNEL["until"] - time.time()) / 3600)
    keep_h = CFG.get("game_funnel_hours")
    funnel_off("moved for «https über Tailscale»", "sys")
    r = _tailscale_https_base(on)
    funnel_on(left_h, "sys")
    CFG["game_funnel_hours"] = keep_h
    return r


_ginv_base_base = ginv_base


def ginv_base(host_url=""):
    """with the funnel on, the invitations use the public address https://<name>.ts.net[:port]"""
    if FUNNEL["on"] and FUNNEL["url"]:
        return FUNNEL["url"]
    return _ginv_base_base(host_url)


_ginv_revoke_base = ginv_revoke


def ginv_revoke(iid):
    n = _ginv_revoke_base(iid)
    try:
        funnel_check()
    except Exception:
        pass
    return n


_ginv_state_base = ginv_state


def ginv_state(host_url=""):
    st = _ginv_state_base(host_url)
    st["funnel"] = funnel_state()
    if FUNNEL["on"]:
        st["public"] = True
    return st


_ginv_routes_base = ginv_routes


def ginv_routes(app, reply, body):
    from flask import request, Response, g as g_
    _ginv_routes_base(app, reply, body)
    FUNNEL["app"] = app

    def funnel_guard():
        """wall 3: funnel traffic reaches only the game, before and independent of the login"""
        if request.headers.get("Tailscale-Funnel-Request") is None and not request.environ.get("mw.funnel"):
            return None
        if request.method in ("GET", "HEAD") and FUNNEL_PATH_RE.match(request.path or ""):
            return None
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()[:45] or request.remote_addr or "?"
        ginv_note(ip, "refused through the funnel: " + (request.path or "/")[:60])
        return Response("Not found", 404, mimetype="text/plain", headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})
    app.before_request_funcs.setdefault(None, []).insert(0, funnel_guard)

    def admin_ok():
        return getattr(g_, "role", "admin") == "admin" and not getattr(g_, "appkey", None)

    @app.route("/api/game_funnel", methods=["GET", "POST"])
    def api_game_funnel():
        lang = norm_lang(request.args.get("lang"))
        if not admin_ok():
            return reply({"ok": False, "error": tr("Only for the administrator", lang)}, 403)
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang)
            a_ = str(d.get("action") or "")
            if a_ == "on":
                try:
                    hh = max(1, min(24, int(d.get("hours") or CFG.get("game_funnel_hours") or 6)))
                except (TypeError, ValueError):
                    hh = 6
                ok, err = funnel_on(hh, "web")
                st = funnel_state(lang)
                st["ok"] = ok
                if not ok:
                    st["error"] = st["err"]["msg"] if st.get("err") else tr_err(str((err or {}).get("msg") or "error"), lang)
                return reply(st, 200 if ok else 400)
            if a_ == "off":
                FUNNEL["err"] = None
                funnel_off("switched off by hand", "web")
            elif a_ == "hours":
                try:
                    CFG["game_funnel_hours"] = max(1, min(24, int(d.get("hours") or 6))); save_settings()
                except (TypeError, ValueError):
                    return reply({"ok": False, "error": "bad hours"}, 400)
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
        st = funnel_state(lang)
        st["ok"] = True
        return reply(st)

    if (CFG.get("game_funnel_state") or {}).get("port"):
        threading.Thread(target=funnel_cleanup, daemon=True, name="funnel-cleanup").start()


LOCK_DENY_PATHS.add("/api/game_funnel")              # operator mode (390): no public access
DEMO_BLOCK = tuple(DEMO_BLOCK) + ("/api/game_funnel",)


# ---- window (592): the switch row in the card «Online» ---------------------------------------------------------------------------
def _tk_funnel_row(self, card):
    """the same as on the page: switch, hours, status line, error with the fix and links"""
    import webbrowser
    fr = tk.Frame(card, bg=C["panel"]); fr.pack(fill="x", pady=(8, 0))
    busy = {"b": False}

    def toggled(val):
        if busy["b"]:
            return
        if CFG.get("lock_on"):
            tg.set(FUNNEL["on"]); self._status("Simulator", tr("Not possible in operator mode")); return
        busy["b"] = True
        stl.configure(text="⏳ …")

        def work():
            if val:
                funnel_on(int(hv.get() or 6), "window")
            else:
                FUNNEL["err"] = None
                funnel_off("switched off by hand", "window")
            busy["b"] = False
            try:
                self.root.after(0, paint)
            except (tk.TclError, RuntimeError):
                pass
        threading.Thread(target=work, daemon=True, name="funnel").start()

    tg = Toggle(fr, "🌍 " + tr("Online game over Tailscale Funnel"), FUNNEL["on"], toggled); tg.pack(fill="x")
    ttk.Label(fr, text=tr("funnel-note"), style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(2, 2))
    hf = tk.Frame(fr, bg=C["panel"]); hf.pack(fill="x")
    tk.Label(hf, text=tr("switches off at the latest after"), bg=C["panel"], fg=C["mut"]).pack(side="left", padx=(0, 4))
    hv = tk.StringVar(value=str(CFG.get("game_funnel_hours") or 6))
    cb = ttk.Combobox(hf, textvariable=hv, values=[str(h) for h in FUNNEL_HOURS], width=3, state="readonly"); cb.pack(side="left", padx=(0, 4))
    tk.Label(hf, text=tr("h"), bg=C["panel"], fg=C["mut"]).pack(side="left")

    def hours_set(_e=None):
        try:
            CFG["game_funnel_hours"] = max(1, min(24, int(hv.get()))); save_settings()
        except ValueError:
            pass
    cb.bind("<<ComboboxSelected>>", hours_set)
    stl = ttk.Label(fr, text="–", wraplength=520, justify="left"); stl.pack(anchor="w", pady=(4, 0))
    ef = tk.Frame(fr, bg=C["panel"]); ef.pack(fill="x")

    def paint():
        try:
            if not fr.winfo_exists():
                return
        except tk.TclError:
            return
        s = funnel_state()
        tg.set(s["on"])
        lk = CFG.get("lock_on")
        tg.lbl.configure(fg=C["mut"] if lk else (C["txt"] if s["on"] else C["mut"]))
        txt = funnel_status_line()
        if s["on"] and s["grace_s"]:
            txt += "\n" + tr("Make an invitation now - without one the funnel switches off after 15 minutes.")
        if lk:
            txt += "\n🔒 " + tr("Not possible in operator mode")
        stl.configure(text=txt)
        for w in ef.winfo_children():
            w.destroy()
        e = s["err"] or s["need"]
        if e:
            tk.Label(ef, text="⚠ " + e["msg"], bg=C["panel"], fg=C.get("red", "#ff6b6b"), anchor="w", justify="left", wraplength=520).pack(anchor="w")
            for st_ in e["steps"]:
                tk.Label(ef, text="• " + st_, bg=C["panel"], fg=C["txt"], anchor="w", justify="left", wraplength=520).pack(anchor="w")
            if e["cmd"]:
                en = tk.Text(ef, height=min(4, e["cmd"].count("\n") + 1), width=60, bg=C["bg"], fg=C["txt"], relief="flat", font=("DejaVu Sans Mono", 9))
                en.insert("1.0", e["cmd"]); en.configure(state="disabled"); en.pack(anchor="w", fill="x", pady=2)
            for ln in e["links"]:
                lb = tk.Label(ef, text="🔗 " + ln["t"], bg=C["panel"], fg=C["acc"], cursor="hand2", anchor="w")
                lb.pack(anchor="w"); lb.bind("<Button-1>", lambda _e, u=ln["u"]: webbrowser.open(u))

    def loop():
        try:
            if not fr.winfo_exists():
                return
        except tk.TclError:
            return
        if not busy["b"]:
            paint()
        fr.after(5000, loop)
    fr.after(300, loop)
