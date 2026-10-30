#@ Motion Watch – Teil 550: Web: der Server (alle Adressen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_GZ_CACHE = {}                         # 2.98.40: gzip of the big pages (blake2b of the page -> gzip)


class WebStream:
    def __init__(self, watch):
        self.watch = watch; self.started = False

    @staticmethod
    def _port_free(port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
            sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sk.bind(("0.0.0.0" if WEB_OPTS["bind"] in ("", "0.0.0.0") else WEB_OPTS["bind"], port)); return True
            except OSError:
                return False

    def _serve(self, app, ctx):
        """Start the web server. If the port is taken by the autostart copy of MoveEye (e.g. an older version that runs as
        service), that copy is stopped: the program started by hand takes over (the next boot starts the service again)."""
        port = int(CFG["web_port"]); took = False; warned = False
        while not self._port_free(port):
            if not took and shutil.which("systemctl"):
                took = True
                for mode in ("user", "system"):
                    rc, out, _e = _systemctl(mode, "is-active", SERVICE_NAME, timeout=10)
                    if rc == 0 and out.strip() == "active" and (mode == "user" or _is_root()):
                        log_event("web", f"Port {port} is used by the autostart copy of MoveEye - it is stopped, this program takes over")
                        _systemctl(mode, "stop", SERVICE_NAME, timeout=30)
                        time.sleep(2.0)
                if self._port_free(port):
                    break
            STATE["web_status"] = f"port {port} busy - another program (an older MoveEye?) uses it"
            if not warned:
                warned = True
                STATE["web_status"] = f"port {port} busy - another program (an older MoveEye?) uses it"
                log_event("web", f"Web page NOT started: port {port} is used by another program (an older MoveEye still running?). "
                                 f"Stop it, e.g.: systemctl --user stop motionwatch  -  trying again every 10 s")
                print(f"   Web page: port {port} is busy (another MoveEye?) - trying again every 10 s")
            time.sleep(10)
        if warned:
            log_event("web", f"Port {port} is free again - web page started")
            STATE["web_status"] = getattr(self, "status_ok", f"on · port {port}")
        self.serving = True
        app.run(host=WEB_OPTS["bind"], port=port, threaded=True, use_reloader=False, ssl_context=ctx)

    def _start_https_extra(self, app):
        """Second, secure address (https, port + 1) of the same page: phones only give their microphone (talking) to
        https pages. Self-signed certificate: the browser asks once whether you trust it."""
        def work():
            cert = ensure_cert()
            if not cert[0]:
                log_event("web", "No secure page (openssl missing) - talking from the phone needs https"); return
            port = int(CFG["web_port"]) + 1
            try:
                from werkzeug.serving import make_server
                srv = make_server(WEB_OPTS["bind"], port, app, threaded=True, ssl_context=cert)
            except Exception as e:
                log_event("web", f"Secure page (https) on port {port} could not start: {e}"[:200]); return
            STATE["https_port"] = port
            log_event("web", f"Secure page for talking: https://<ip>:{port}/")
            srv.serve_forever()
        threading.Thread(target=work, daemon=True, name="https").start()

    def start(self):
        if self.started:
            return
        try:
            from flask import Flask, Response, request, send_file, g, redirect
        except ImportError:
            STATE["web_status"] = "flask not installed"
            log_event("web", "Web stream: pip install flask"); return
        if not GAMESRV["port"]:
            try:
                games_server_start()
            except Exception as e:
                GAMESRV["msg"] = str(e)[:120]
        app = Flask("motionwatch")
        app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024        # 2.95.35: no endless uploads
        watch = self.watch

        def reply(obj, code=200):
            return Response(json.dumps(obj, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
                            status=code, mimetype="application/json")

        def body():
            d_ = request.get_json(force=True, silent=True)
            return d_ if isinstance(d_, dict) else {}            # 2.95.33: [] / "x" / 5 gave error 500

        fails = {}                                  # ip -> times of wrong passwords (lock-out after 8 in 5 minutes)

        public = {"/i18n/fr.js", "/i18n/it.js", "/i18n/rm.js", "/manifest.webmanifest", "/icon-192.png", "/icon-512.png", "/apple-touch-icon.png",
                  "/apple-touch-icon-precomposed.png", "/favicon.ico", "/sw.js",
                  "/sim/simulator.zip"}                # the simulator fetches its updates here (public program, no secrets)

        def local_req():
            """really from this computer - not through Tailscale serve / a tunnel (those also arrive as 127.0.0.1)"""
            return (request.remote_addr or "") in ("127.0.0.1", "::1") and not (request.headers.get("X-Forwarded-For")
                                                                               or request.headers.get("Forwarded") or request.headers.get("X-Forwarded-Host"))

        def origin_ok():
            """2.95.33 (CSRF): a POST from a page of another web site is refused. Browsers always send «Origin» on such
            requests; programs (simulator, other MoveEye devices, shortcuts) send none and are let through."""
            o = request.headers.get("Origin")
            if o is None:
                return True
            from urllib.parse import urlparse
            try:
                u_ = urlparse(o)
            except ValueError:
                return False
            if not u_.netloc:
                return False                                  # "null" (sandboxed page, file://)
            def norm(h, scheme):
                h = (h or "").strip().lower()
                if (scheme == "https" and h.endswith(":443")) or (scheme == "http" and h.endswith(":80")):
                    h = h.rsplit(":", 1)[0]
                return h
            want = norm(u_.netloc, u_.scheme)
            have = {norm(request.host, request.scheme), norm(request.host, u_.scheme)}
            for hh in (request.headers.get("X-Forwarded-Host", ""),):
                if hh:
                    have.add(norm(hh.split(",")[0], u_.scheme))
            pu = (CFG.get("public_url") or "").strip()
            if pu:
                try:
                    pp = urlparse(pu); have.add(norm(pp.netloc, pp.scheme))
                except ValueError:
                    pass
            return want in have

        @app.before_request
        def auth():
            if _RESTART_M["todo"]:
                restart_measure()
            if request.method not in ("GET", "HEAD", "OPTIONS") and not origin_ok():
                if (request.content_length or 0) < 1 << 20:
                    request.get_data()                      # read the body first, else the connection is reset
                log_event("web", f"Blocked a request from another web page ({request.headers.get('Origin', '')[:60]}) to {request.path}")
                return sx_err(403, "foreign")                  # in the own language (578)
            if request.path.startswith(("/g/", "/x/", "/k/", "/p/", "/na/", "/spiele", "/tv/", "/nt/", "/info", "/almanach", "/game/")) or request.path in public:
                return None                         # guest links check their own key; app icons are not secret
            pw = CFG["web_password"]
            g.user, g.role = "", "admin"
            if not pw and not CFG["web_pw_hash"]:
                return None
            ip = request.remote_addr or "?"
            if ip in ("127.0.0.1", "::1") and request.headers.get("X-Forwarded-For"):
                ip = request.headers["X-Forwarded-For"].split(",")[0].strip()[:45] or ip   # behind Tailscale serve / a tunnel
            now = time.time()
            k_ = appkey_from_request(request)       # «App-Schlüssel» (573): programs, also over plain http (the key is no password)
            if k_ is not None:
                recent = [x for x in fails.get(ip, []) if now - x < 300]
                if len(recent) >= 8:
                    fails[ip] = recent
                    return sx_err(429, "toomany", {"Retry-After": "300"})
                ke = appkey_find(k_, api=True)      # a shortcut key (scope «shortcut», 573) opens only /k/…
                if ke is None:
                    recent.append(now); fails[ip] = recent
                    if len(recent) == 8:
                        log_event("web", f"Login blocked for 5 minutes after 8 wrong app keys from {ip}")
                    return appkey_refused(request, ip)
                fails.pop(ip, None)
                g.user, g.role, g.appkey = "🔑 " + str(ke.get("name") or "?"), "admin", ke["id"]
                appkey_seen(ke, ip)
                return appkey_guard(request)        # never the password, users, keys or security settings
            tf = trust_find(request.cookies.get(TRUST_COOKIE, ""))   # a trusted device: no login (also after updates)
            if tf:
                g.user, g.role = tf[0]
                if now - float(tf[1].get("seen", 0)) > 3600:
                    tf[1]["seen"] = int(now); tf[1]["ip"] = ip[:45]; save_settings()
                return None
            if seclogin_plain(request):              # «Anmelden nur verschlüsselt» (574): no password over plain http
                return seclogin_block(request)
            recent = [x for x in fails.get(ip, []) if now - x < 300]
            if len(recent) >= 8:
                fails[ip] = recent
                return sx_err(429, "toomany", {"Retry-After": "300"})
            a = request.authorization
            who = user_login(a.username or "", a.password or "") if a else None
            if who:
                fails.pop(ip, None)
                g.user, g.role = who
                if request.method == "GET" and not request.path.startswith(("/api/", "/video", "/cam_feed", "/sim/", "/snapshot")):
                    g.new_trust = trust_add(who[0], who[1], request.headers.get("User-Agent", ""), ip)   # remember this device
                return None
            if a:
                recent.append(now)
                if len(recent) == 8:
                    log_event("web", f"Login blocked for 5 minutes after 8 wrong passwords from {ip}")
            fails[ip] = recent
            if len(fails) > 500:
                for k in [k for k, v in fails.items() if not v or now - v[-1] > 300]:
                    fails.pop(k, None)
            return sx_err(401, "login", {"WWW-Authenticate": 'Basic realm="MoveEye", charset="UTF-8"'})   # guests see the realm

        @app.before_request
        def seclogin_guard():                       # 574: setting a password over plain http from another device
            return seclogin_body_check(request)

        @app.route("/api/seclogin")
        def api_seclogin():
            return reply(dict(seclogin_info(request, norm_lang(request.args.get("lang"))), ok=True))

        @app.before_request
        def role_guard():                           # users with a role: what they may do
            role = getattr(g, "role", "admin")
            if role == "admin":
                return None
            if request.path == "/api/sim/upload":                # only the administrator (and the body is a big video)
                return reply({"ok": False, "error": tr("not allowed for your user", norm_lang(request.args.get("lang") or CFG["lang"]))}, 403)
            d = request.get_json(force=True, silent=True) if request.method == "POST" else None
            if role_allows(role, request.path, request.method, d if isinstance(d, dict) else {}):
                return None
            lang = norm_lang(((d or {}).get("lang") if isinstance(d, dict) else None) or request.args.get("lang") or CFG["lang"])
            return reply({"ok": False, "error": tr("not allowed for your user", lang)}, 403)

        @app.after_request
        def gzip_text(resp):                        # 2.98.40 (Daniel: menus build up slowly): pages are ~800 KB - gzip makes
            try:                                    # ~5× less over Wi-Fi / Tailscale; registered first = runs last
                if (request.method == "GET" or request.method == "POST") and resp.status_code == 200 and not resp.direct_passthrough \
                        and not resp.is_streamed and "gzip" in (request.headers.get("Accept-Encoding") or "").lower() \
                        and not resp.headers.get("Content-Encoding") \
                        and (resp.mimetype or "").startswith(("text/", "application/javascript", "application/json", "image/svg")):
                    raw = resp.get_data()
                    if len(raw) >= 2048:
                        import hashlib, gzip as _gz
                        k_ = hashlib.blake2b(raw, digest_size=16).digest()
                        z_ = _GZ_CACHE.get(k_)
                        if z_ is None:
                            z_ = _gz.compress(raw, compresslevel=5)
                            if len(raw) > 50000:          # the big pages come again and again: keep a few
                                if len(_GZ_CACHE) > 12:
                                    _GZ_CACHE.pop(next(iter(_GZ_CACHE)))
                                _GZ_CACHE[k_] = z_
                        resp.set_data(z_)
                        resp.headers["Content-Encoding"] = "gzip"
                        resp.headers["Content-Length"] = str(len(z_))
                        resp.vary.add("Accept-Encoding")
            except Exception:
                pass
            return resp

        @app.after_request
        def trust_cookie(resp):                     # a device that just logged in gets its «trusted» cookie (one year)
            tok = getattr(g, "new_trust", None)
            if tok:
                resp.set_cookie(TRUST_COOKIE, tok, max_age=365 * 86400, httponly=True, samesite="Lax", secure=request.is_secure, path="/")
            return resp

        @app.route("/api/trusted", methods=["GET", "POST"])
        def api_trusted():
            if getattr(g, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            mine = _trust_hash(request.cookies.get(TRUST_COOKIE, "")) if request.cookies.get(TRUST_COOKIE) else ""
            if request.method == "POST":
                d = body(); a_ = d.get("action")
                if a_ == "remove":
                    i_ = int(d.get("i", -1)); lst = CFG.get("trusted") or []
                    if 0 <= i_ < len(lst):
                        log_event("web", f"Trusted device removed: {lst[i_].get('name')}")
                        CFG["trusted"] = lst[:i_] + lst[i_ + 1:]; save_settings()
                elif a_ == "clear":
                    CFG["trusted"] = []; save_settings(); log_event("web", "All trusted devices removed")
            return reply({"ok": True, "pw": web_pw_active(), "devices": [{"name": e.get("name"), "user": e.get("user"), "t0": e.get("t0"), "seen": e.get("seen"),
                          "ip": e.get("ip"), "me": e.get("h") == mine} for e in (CFG.get("trusted") or [])]})

        @app.after_request
        def count_viewer(resp):                     # who has a page open: counted for the header (other MoveEye devices not)
            p = request.path
            if resp.status_code < 400 and (p == "/api/state" or (p.startswith("/g/") and p.endswith(("/state", "/state.json")))):
                ua = request.headers.get("User-Agent", "")
                if "MotionWatch" not in ua:
                    VIEWERS[(request.remote_addr or "?") + "|" + ua[:120] + "|" + (request.headers.get("X-View-Id") or "")] = time.time()
            return resp

        @app.after_request
        def page_exit(resp):                        # 2.95.56: a way back on every page (home-screen app, full screen)
            try:
                if (resp.status_code == 200 and resp.mimetype == "text/html" and not resp.direct_passthrough and not resp.is_streamed
                        and request.method == "GET"):
                    new = page_exit_inject(request.path, resp.get_data(as_text=True))
                    if new is not None:
                        resp.set_data(new)
            except Exception:
                pass
            return resp

        @app.after_request
        def who_did_it(resp):                       # with several users the log tells who switched what
            if request.method == "POST" and CFG["users"] and resp.status_code < 400 and request.path in (
                    "/api/arm", "/api/night", "/api/camping", "/api/light", "/api/quick", "/api/lock", "/api/password", "/api/pause", "/api/power"):
                d = request.get_json(force=True, silent=True) or {}
                act_ = d.get("action") or d.get("mode") or d.get("on") or ""
                log_event("web", f"{getattr(g, 'user', '') or 'admin'}: {request.path[5:]} {str(act_)[:20]}".strip())
            return resp

        @app.route("/api/species", methods=["GET", "POST"])
        def api_species():
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang"))
                ok, err = species_install(d.get("url"))
                return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "models": species_models()}, 200 if ok else 400)
            if CFG["species_on"]:
                species_load()
            last = SPECIES["last"]; lg = norm_lang(request.args.get("lang"))
            msg = (tr("ready", lg) + f" · {len(SPECIES['names'])} " + tr("species", lg)) if SPECIES["net"] is not None else tr_err(SPECIES["msg"], lg)
            return reply({"models": species_models(), "folder": species_dir(), "msg": msg if CFG["species_on"] else tr("off", lg),
                          "last": {"label": tr(last[0], norm_lang(request.args.get("lang"))), "conf": round(last[1], 2),
                                   "ago": int(time.time() - last[2])} if last else None})

        @app.route("/api/sim", methods=["GET", "POST"])
        def api_sim():
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang"))
                if "url" in d:
                    ok, err = set_text("sim_url", str(d.get("url") or ""))
                    if not ok:
                        return reply({"ok": False, "error": tr_err(err, lang)}, 400)
                if "on" in d:
                    ok_s, err_s = sim_set(d.get("on"), "web " + (request.remote_addr or "?"), bool(d.get("confirm")))
                    if not ok_s and err_s == "armed":       # 2.97.0: the page asks «disarm and simulate?»
                        return reply({"ok": False, "need_confirm": "armed",
                                      "error": tr_err("MoveEye is armed. The simulation replaces the real camera - nothing real is watched then. Disarm and switch the simulation on?", lang)})
                act_ = d.get("action")
                if act_ == "ctl":                           # remote control of the simulator: passed on as it is (CONTROL protocol 1)
                    c_ = str(d.get("ctl") or "get")
                    if c_ not in ("get", "scenario", "delete", "set", "press"):
                        return reply({"ok": False, "error": "unknown action"}, 400)
                    q_ = {"action": c_}
                    if c_ != "get":
                        q_["id"] = str(d.get("id") or "")[:200]
                    if c_ == "set":
                        v_ = d.get("value")
                        q_["value"] = v_ if isinstance(v_, (bool, int, float)) else str(v_)[:200]
                    try:
                        r = sim_control(None if c_ == "get" else q_)
                    except Exception as e:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang) + f" ({_short_net_err(e) if '_short_net_err' in globals() else str(e)[:60]})"}, 400)
                    if not r.get("ok"):
                        return reply({"ok": False, "error": tr_err(str(r.get("error") or "not supported - update the simulator"), lang)}, 400)
                    if c_ in ("scenario", "delete"):
                        log_event("sys", f"Simulator: {c_} {q_.get('id', '')[:80]}")
                    return reply(dict(r, ok=True))
                if act_ == "dataset":                            # 2.95.53: KI-Prüfung mit Simulator-Bildern
                    if d.get("export"):                          # 2.95.99: a training set (YOLO) made in the simulator, saved on its PC
                        try:
                            r = kidata_export(d.get("n"), d.get("vielfalt"))
                        except Exception:
                            return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                        return reply({"ok": True, "export": r})
                    if d.get("packs") or d.get("clean"):         # KI-Daten: the training packs on the PC of the simulator (197)
                        try:
                            return reply(dict(kidata_packs(bool(d.get("clean")), lang), ok=True))
                        except Exception as e:
                            return reply({"ok": False, "error": tr_err(str(e) if isinstance(e, ValueError) else "simulator not reachable", lang)}, 400)
                    if d.get("start"):
                        ok_, err_ = dset_run("game" if str(d.get("n")) == "game" else (int(d.get("n") or 24) if str(d.get("n") or "24").isdigit() else 24))
                        if not ok_:
                            return reply({"ok": False, "error": tr_err(err_, lang)}, 400)
                    return reply({"ok": True, "dataset": dset_state()})
                if act_ == "replay":                             # 2.95.53: Alarm-Rückblick in 3D
                    alarm_tracks_load()
                    if d.get("stop"):
                        try:
                            sim_control({"action": "replay", "stop": True})
                        except Exception:
                            pass
                        return reply({"ok": True})
                    tid = str(d.get("id") or "")
                    tr_ = next((t for t in ALARM_TRACKS if t["id"] == tid), None)
                    if tr_ is None or len(tr_.get("samples") or []) < 2:
                        return reply({"ok": False, "error": tr_err("no track for this alarm", lang)}, 400)
                    title = datetime.fromtimestamp(tr_["t"]).strftime("%d.%m. %H:%M") + " · " + tr(tr_.get("kind", "person"), "de")
                    try:
                        r = sim_control({"action": "replay", "track": {"title": title, "samples": tr_["samples"], "speed": float(d.get("speed") or 1.0)}})
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    if not isinstance(r, dict) or not r.get("ok"):
                        return reply({"ok": False, "error": tr_err(str((r or {}).get("error") or "not supported - update the simulator"), lang)}, 400)
                    return reply({"ok": True, "replay": r})
                if act_ in ("planner_open", "planner_apply"):     # 2.95.53: the Aufstell-Planer of the 3D simulator
                    try:
                        r = sim_control({"action": "planner", "op": "open" if act_ == "planner_open" else "get"})
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    if not isinstance(r, dict) or not r.get("ok"):
                        return reply({"ok": False, "error": tr_err("not supported - update the simulator", lang)}, 400)
                    if act_ == "planner_apply":
                        wps = [[max(0.0, min(100.0, float(w[0]))), max(0.0, min(100.0, float(w[1])))] for w in (r.get("waypoints") or [])[:10]
                               if isinstance(w, (list, tuple)) and len(w) == 2]
                        if len(wps) < 2:
                            return reply({"ok": False, "error": tr_err("no waypoints", lang)}, 400)
                        WAYPOINTS[:] = wps
                        CFG["patrol"] = True; CFG["patrol_mode"] = "pendulum"; save_settings()
                        log_event("patrol", f"Patrol from the Aufstell-Planer of the simulator: {len(wps)} waypoints, {r.get('pct')} % of the area in view")
                    return reply({"ok": True, "planner": r})
                if act_ == "shoot":                          # 2.95.96: a shot / trigger into the simulation (tap on the live picture)
                    try:
                        q_ = {"action": "shoot", "who": str(d.get("who") or getattr(g, "user", "") or "")[:30],
                              "x": max(0.0, min(1.0, float(d.get("x", 0.5)))), "y": max(0.0, min(1.0, float(d.get("y", 0.5)))),
                              "shutter": bool(d.get("shutter"))}      # 2.98.35: «Auslöser» - a shot at the middle (539, gameshutter.gd)
                        r = sim_control(q_)
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    if not isinstance(r, dict):
                        return reply({"ok": False, "error": tr_err("not supported - update the simulator", lang)}, 400)
                    if r.get("ok") and not r.get("hit"):
                        log_event("sim", f"False alarm marked: a shot of {q_['who'] or 'MoveEye'} into the simulation missed")
                    SIMGAME["t"] = 0.0
                    return reply(r)
                if act_ == "game_mwcatch":                   # «Team gegen MoveEye»: «Erwischt!» from this page (3D-3.27)
                    try:
                        q_ = {"action": "game_mwcatch", "who": str(d.get("who") or getattr(g, "user", "") or "")[:30]}
                        if d.get("x") is not None and d.get("y") is not None:      # 2.95.74: the hunter tapped this spot of the live picture
                            q_["x"] = max(0.0, min(1.0, float(d["x"]))); q_["y"] = max(0.0, min(1.0, float(d["y"])))
                        r = sim_control(q_)
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    SIMGAME["t"] = 0.0
                    return reply(r if isinstance(r, dict) else {"ok": False})
                if act_ == "gamewiz":                        # the game wizard runs in the 3D simulator (3D-3.41), worked from here
                    q_ = {"action": "gamewiz", "op": str(d.get("op") or "get")[:12]}
                    if "key" in d:
                        q_["key"] = str(d.get("key"))[:40]
                    if "value" in d:
                        v_ = d.get("value")
                        q_["value"] = v_ if isinstance(v_, (bool, int, float)) else str(v_)[:80]
                    try:
                        r = sim_control(q_)
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    if not isinstance(r, dict) or not r.get("ok"):
                        return reply({"ok": False, "error": tr_err(str((r or {}).get("error") or "not supported - update the simulator"), lang)}, 400)
                    return reply(r)
                if act_ == "game_hc":                        # handicap for a player (3D-3.25)
                    try:
                        r = sim_control({"action": "game_handicap", "slot": int(d.get("slot", -1)), "level": max(0, min(2, int(d.get("level", 0))))})
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    return reply({"ok": bool(r.get("ok"))})
                if act_ == "game":                           # the game in numbers for the spectators (3D-3.22)
                    try:
                        r = sim_control({"action": "game_info"})
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    return reply(r if isinstance(r, dict) else {"ok": False})
                if act_ == "view_in":                        # the simulator window: mouse / finger / keys (3D-3.18)
                    evs = []
                    for e in (d.get("ev") or [])[:60]:
                        if not isinstance(e, dict) or e.get("t") not in ("move", "down", "up", "dbl", "wheel", "key"):
                            continue
                        x = {"t": e["t"]}
                        for k_ in ("x", "y", "d"):
                            if isinstance(e.get(k_), (int, float)):
                                x[k_] = float(e[k_])
                        if isinstance(e.get("b"), int):
                            x["b"] = max(1, min(3, e["b"]))
                        for k_ in ("down", "alt", "shift"):
                            if k_ in e:
                                x[k_] = bool(e[k_])
                        if isinstance(e.get("k"), str):
                            x["k"] = e["k"][:12]
                        evs.append(x)
                    if not evs:
                        return reply({"ok": True, "n": 0})
                    try:
                        r = sim_control({"action": "input", "ev": evs})
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    return reply({"ok": bool(r.get("ok")), "n": r.get("n", 0)})
                if act_ == "pad":                            # 2.95.83: a game controller at the browser (e.g. PS5) drives the rover
                    try:
                        ax_ = [max(-1.0, min(1.0, float(v))) for v in (d.get("ax") or [])[:6]]
                        bt_ = [round(max(0.0, min(1.0, float(v))), 2) for v in (d.get("bt") or [])[:17]]   # triggers have a value
                        r = sim_control({"action": "pad", "ax": ax_, "bt": bt_, "name": str(d.get("name") or "")[:40]})
                    except (TypeError, ValueError):
                        return reply({"ok": False, "error": "invalid values"}, 400)
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    return reply(r if isinstance(r, dict) else {"ok": False})
                if act_ == "padview":                        # «Controller-Ansicht» (538): views, turning, flying, zoom of the simulator view
                    q_ = {"action": "padview"}
                    try:
                        if str(d.get("view") or "") in ("follow", "driver", "top", "head", "free", "next", "rnext", "off"):
                            q_["view"] = str(d["view"])
                        for k_ in ("look", "fly"):
                            if isinstance(d.get(k_), list) and len(d[k_]) >= 2:
                                q_[k_] = [max(-1.0, min(1.0, float(v_))) for v_ in d[k_][:2]]
                        if d.get("zoom") is not None:
                            q_["zoom"] = 1 if float(d["zoom"]) > 0 else -1
                        if d.get("dt") is not None:
                            q_["dt"] = max(0.0, min(0.5, float(d["dt"])))
                        r = sim_control(q_)
                    except (TypeError, ValueError):
                        return reply({"ok": False, "error": "invalid values"}, 400)
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    return reply(r if isinstance(r, dict) else {"ok": False})
                if act_ == "look":                           # the phone as a window (3D-3.27): turning the phone turns the view
                    try:
                        yw = max(-360.0, min(360.0, float(d.get("yaw", 0)))); pt = max(-90.0, min(90.0, float(d.get("pitch", 0))))
                        r = sim_control({"action": "view_look", "yaw": yw, "pitch": pt, "start": bool(d.get("start"))})
                    except (TypeError, ValueError):
                        return reply({"ok": False, "error": "invalid values"}, 400)
                    except Exception:
                        return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
                    return reply({"ok": bool(r.get("ok")), "error": r.get("error")})
                if act_ == "search":
                    sim_scan()
                    return reply(dict(sim_status(), ok=True))
                if act_ == "use":                            # take over a simulator that was found in the network
                    ip_, port_ = str(d.get("ip") or ""), int(d.get("port") or 8765)
                    if not re.fullmatch(r"[0-9.]{7,15}", ip_) or not (1 <= port_ <= 65535):
                        return reply({"ok": False, "error": "bad address"}, 400)
                    if tunnel_active() and ip_ == TUN.get("peer"):   # 2.95.68: this simulator comes through the tunnel
                        TUN["prev_url"] = CFG["tunnel_prev_url"] = f"http://{ip_}:{port_}"; CFG["sim_url"] = "http://127.0.0.1:18765"
                    else:
                        CFG["sim_url"] = f"http://{ip_}:{port_}"
                    save_settings()
                    log_event("sys", f"Simulator address set to {CFG['sim_url']} (web)")
                    if CFG["sim_on"] and WATCH_REF.get("w") is not None and str(CFG["source"]).startswith("sim:"):
                        w_ = WATCH_REF["w"]; w_._open_gen += 1; w_._start_opener(CFG["source"])
                if act_ in ("install", "start", "stop"):
                    try:
                        ok, msg = {"install": sim_install, "start": sim_start, "stop": sim_stop}[act_]()
                    except Exception as e:
                        ok, msg = False, str(e)[:120]
                    if not ok:
                        return reply({"ok": False, "error": tr_err(msg, lang)}, 400)
            return reply(dict(sim_status(), ok=True, connected=sim_status()["ok"]))

        @app.route("/api/qs", methods=["POST"])
        def api_qs():
            d = body()
            if d.get("reset"):
                qs_layout_set([], [])
            else:
                qs_layout_set(d.get("order"), d.get("hidden"), d.get("favs"), d.get("cards"), d.get("chide"))   # 2.98.29: «for all devices»
            return reply({"ok": True, "qs_layout": CFG["qs_layout"]})

        @app.route("/api/simtest", methods=["GET", "POST"])
        def api_simtest():
            if request.method == "GET":
                if not TESTOPT["busy"] and CFG["sim_on"] and SIM["ok"]:
                    st = _simtest("test_report")            # also a test run started in the simulator window
                    if st:
                        TESTOPT["sim"] = st
                return reply(testopt_state())
            if getattr(g, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            d = body(); a = d.get("action"); plan = str(d.get("plan") or "standard")
            if plan not in ("standard", "quick", "hard", "night", "spielwege"):     # 2.97.0: the sneak paths of the games too
                plan = "standard"
            if a in ("run", "auto"):
                if TESTOPT["busy"] or simtask_busy():
                    return reply({"ok": False, "error": tr_err(simtask_refuse("test run") or "a test run is already going", norm_lang(d.get("lang")))}, 409)
                if not (CFG["sim_on"] and SIM["ok"]):
                    return reply({"ok": False, "error": "the simulation is not connected"}, 409)
                TESTOPT["plan"] = plan
                threading.Thread(target=_testopt_thread, args=(a, plan, max(1, min(8, int(d.get("tries") or 4)))), daemon=True).start()
            elif a == "stop":
                TESTOPT["stop"] = True; _simtest("test_stop")
            elif a in ("apply", "apply_all", "undo") and TESTOPT["busy"]:
                return reply({"ok": False, "error": "a test run is going on - wait until it is finished"}, 409)
            elif a in ("apply", "apply_all"):
                sel = [x for x in TESTOPT["sugg"] if a == "apply_all" or x["id"] == d.get("id")]
                if not sel:
                    return reply({"ok": False, "error": "no such proposal"}, 404)
                ch = {}
                for x in sel:                                # several proposals: the later (less important) do not overwrite
                    for k, o, n in x["changes"]:
                        ch.setdefault(k, [k, o, n])
                before = opt_apply(list(ch.values()), "taken over: " + ", ".join(x["id"] for x in sel))
                TESTOPT["undo"] = {"cfg": before, "t": time.time(), "what": ",".join(x["id"] for x in sel), "sim": bool(CFG.get("sim_on"))}
                TESTOPT["sugg"] = [x for x in TESTOPT["sugg"] if x not in sel]
                testopt_save()
            elif a == "undo":
                if not TESTOPT["undo"]:
                    return reply({"ok": False, "error": "nothing to undo"}, 404)
                if bool(TESTOPT["undo"].get("sim", CFG.get("sim_on"))) != bool(CFG.get("sim_on")):   # 2.97.0
                    return reply({"ok": False, "error": tr_err("This was changed in the other profile (simulation / real). Switch the simulation back first.", norm_lang(d.get("lang")))}, 409)
                opt_restore(TESTOPT["undo"]["cfg"]); TESTOPT["undo"] = None; testopt_save()
            elif a == "clear":
                TESTOPT["runs"] = []; TESTOPT["sugg"] = []; TESTOPT["auto"] = None; testopt_save()
            elif a == "nightly":
                CFG["testopt_nightly"] = bool(d.get("on")); CFG["testopt_hour"] = max(0, min(23, int(d.get("hour", CFG["testopt_hour"]))))
                if d.get("plan") in ("standard", "quick", "hard", "night", "spielwege"):
                    CFG["testopt_plan"] = d["plan"]
                save_settings()
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply(dict(testopt_state(), ok=True))

        # ---- game corner (2.95.29): the phones of the players, with the room key instead of a password ----
        def _pkey(key):
            import hmac
            return party_on() and hmac.compare_digest(PARTY["key"], key)

        @app.route("/p/<key>/")
        def party_page(key):
            if not _pkey(key):
                return Response("<h2 style='font-family:sans-serif'>Die Spielecke ist geschlossen.</h2>", 404, mimetype="text/html")
            return Response(PARTY_PAGE.replace("__KEY__", key).replace("__NTJS__", NT_JS), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/p/<key>/join", methods=["POST"])
        def party_join(key):
            if not _pkey(key):
                return reply({"error": "closed"}, 404)
            d = body(); name = re.sub(r"[\x00-\x1f<>]", "", str(d.get("name") or "")).strip()[:20]
            if not name:
                return reply({"error": "name missing"}, 400)
            pid = str(d.get("pid") or "")
            if pid not in PARTY["players"]:
                if len(PARTY["players"]) >= 30:          # 2.95.33: players away for 10 minutes make room
                    for k_ in [k_ for k_, p_ in PARTY["players"].items() if time.time() - p_["t"] > 600 and k_ != PARTY["host"]]:
                        PARTY["players"].pop(k_, None)
                if len(PARTY["players"]) >= 30:
                    return reply({"error": "full (30 players)"}, 409)
                pid = secrets.token_urlsafe(9)
                PARTY["players"][pid] = {"name": name, "score": 0, "t": time.time()}
            else:
                PARTY["players"][pid].update(name=name, t=time.time())
            if not PARTY["host"] or PARTY["host"] not in PARTY["players"]:
                PARTY["host"] = pid
            party_bump()
            return reply({"ok": True, "pid": pid})

        @app.route("/p/<key>/s")
        def party_state(key):
            if not _pkey(key):
                return reply({"error": "closed"}, 404)
            pid = request.args.get("pid", ""); seq = int(request.args.get("seq", "-1") or -1) if str(request.args.get("seq", "-1")).lstrip("-").isdigit() else -1
            p = PARTY["players"].get(pid)
            if p:
                p["t"] = time.time()
            end = time.time() + 20
            with PARTY_COND:
                while PARTY["seq"] == seq and time.time() < end and party_on():
                    PARTY_COND.wait(min(1.0, end - time.time()))
                    party_tick()
            return reply(party_view(pid))

        @app.route("/p/<key>/a", methods=["POST"])
        def party_action(key):
            if not _pkey(key):
                return reply({"error": "closed"}, 404)
            d = body(); pid = str(d.get("pid") or "")
            try:
                with PARTY_COND:
                    err = party_act(pid, party_unpub(d))
                    G_ = PARTY["g"]
                    if isinstance(G_.get("log"), list) and len(G_["log"]) > 60:
                        G_["log"] = G_["log"][-40:]
            except (TypeError, ValueError, KeyError, IndexError, AttributeError):
                err = "invalid values"
            if not err and not PARTY.pop("_quiet", False):
                party_bump()
            return reply({"ok": not err, "error": err or None, "v": party_view(pid)})

        @app.route("/p/<key>/g/<game>/")
        @app.route("/p/<key>/g/<game>/<path:fn>")
        def party_game_file(key, game, fn=""):
            if not _pkey(key):
                return Response("closed", 404)
            u_ = games_url(game, fn, request.host) if lan_guest_ip(request.remote_addr, request.headers.get("X-Forwarded-For", "")) else ""
            if u_:
                return redirect(u_)
            p_ = games_file(game, fn)
            if p_ and p_.lower().endswith((".html", ".htm")):
                with open(p_, "rb") as f_:
                    return Response(games_inject_back(f_.read(), "/p/" + key + "/"), mimetype="text/html")
            return send_file(p_, max_age=3600) if p_ else Response("not found", 404)

        def _lan_ok():
            return lan_guest_ip(request.remote_addr, request.headers.get("X-Forwarded-For", "") or request.headers.get("Forwarded", ""))

        _lan_no = "<h2 style='font-family:sans-serif'>Die Spielecke ist nur im eigenen WLAN offen.</h2>"

        @app.route("/api/usb")
        def api_usb():
            return reply({"ok": True, "devices": usb_list(), "ids": len(_usb_ids()) > 1})

        # ---- network check (2.95.52): open only while a check runs ----
        def _nt_ip():
            return request.remote_addr or "?"

        @app.route("/api/dataset.zip")
        def api_dataset_zip():
            if not DSET["res"]:
                return Response("no pictures yet", 404)
            return Response(dset_zip(), mimetype="application/zip", headers={"Content-Disposition": "attachment; filename=motionwatch_trainingsbilder.zip"})

        @app.route("/almanach")
        @app.route("/almanach/")
        def almanac_page():
            return Response(ALM_PAGE.replace("__DATA__", json.dumps(ALMANAC, ensure_ascii=False).replace("</", "<\\/")), mimetype="text/html",
                            headers={"Cache-Control": "no-store"})

        @app.route("/api/refscan", methods=["GET", "POST"])
        def api_refscan():                                   # 2.95.97: reference scan (assistant on the tools page)
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang")); op = str(d.get("op") or "")
                if op == "report":
                    r_ = refscan_report(str(d.get("id") or ""))
                    return reply({"ok": bool(r_), "report": r_})
                if getattr(g, "role", "admin") != "admin":
                    return reply({"ok": False, "error": "not allowed"}, 403)
                if op in ("scan", "compare"):
                    ok_, err_ = refscan_start(op, "by hand")
                    if not ok_:
                        return reply({"ok": False, "error": tr(err_, lang)}, 400)
                elif op == "stop":
                    refscan_stop()
                elif op == "watch":                          # 2.95.98: things to guard
                    if not refscan_set_watch(str(d.get("kind") or "day"), d.get("items") or []):
                        return reply({"ok": False, "error": tr("no reference yet - scan first", lang)}, 400)
                elif op == "panorama":                       # 2.96.1: the panorama report now (the last 24 h)
                    path_, js_ = pano_build(time.time() - 86400, None)
                    if not path_:
                        return reply({"ok": False, "error": tr(js_, lang)}, 400)
                    if d.get("send"):
                        pano_send(path_, js_)
                elif op == "pano_on":
                    CFG["refscan_pano_on"] = bool(d.get("on")); save_settings()
                else:
                    return reply({"ok": False, "error": "unknown"}, 400)
            st_ = refscan_state()
            st_["cfg"] = {k: v for k, v in CFG.items() if k.startswith("refscan_")}
            st_["panoramas"] = pano_list()
            return reply(dict(st_, ok=True))

        @app.route("/refscan")
        def refscan_page():
            return redirect("/tools#refscan")

        @app.route("/refscan/file/<path:fp>")
        def refscan_file(fp):
            if not re.fullmatch(r"(ref(_night)?/pos_\d{2}\.jpg|reports/\d{8}_\d{6}/(cur|ref)_\d{2}\.jpg|panorama/\d{8}_\d{4}\.jpg)", fp):
                return Response("not found", 404)
            p_ = refscan_dir(*fp.split("/"))
            return send_file(p_, max_age=60) if os.path.isfile(p_) else Response("not found", 404)

        @app.route("/api/helper", methods=["GET", "POST"])
        def api_helper():
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang"))
                if "use" in d:
                    CFG["helper_use"] = bool(d["use"])
                if "url" in d:
                    u_ = str(d.get("url") or "").strip()
                    if u_ and not u_.startswith("http"):
                        u_ = "http://" + u_
                    if u_ and not re.match(r"^https?://[A-Za-z0-9.\-\[\]]{1,80}(:\d{1,5})?$", u_):
                        return reply({"ok": False, "error": tr("address not valid", lang)}, 400)
                    if u_ and not re.search(r":\d+$", u_):
                        u_ += f":{HELPER_PORT}"
                    CFG["helper_url"] = u_; CFG["helper_code"] = re.sub(r"\D", "", str(d.get("code") or ""))[:6]
                    HELPER.update(ok=False, next_try=0.0)
                if "serve" in d:
                    CFG["helper_serve"] = bool(d["serve"])
                    if CFG["helper_serve"]:
                        helper_server_start()
                save_settings()
                threading.Thread(target=helper_tick, daemon=True).start()
            return reply({"ok": True, "helper": helper_state()})

        # ---- the product page for guests (2.95.52) ----
        @app.route("/info")
        @app.route("/info/")
        def info_page():
            if not CFG.get("info_page"):
                return Response("<h2 style='font-family:sans-serif'>MoveEye</h2>", 404, mimetype="text/html")
            return Response(info_html(), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/info/ask", methods=["POST"])
        def info_ask():
            if not CFG.get("info_page"):
                return reply({"error": "closed"}, 404)
            ip = request.remote_addr or "?"; now = time.time()
            ts = [t_ for t_ in _INFO_ASK.get(ip, []) if now - t_ < 3600]
            if len(ts) >= 5:
                return reply({"error": "too many"}, 429)
            d = body()
            clean = lambda x, n: re.sub(r"[\x00-\x08\x0b-\x1f<>]", "", str(x or "")).strip()[:n]
            m = {"t": now, "ip": ip, "name": clean(d.get("name"), 40), "topic": clean(d.get("topic"), 60), "msg": clean(d.get("msg"), 1500)}
            if not m["msg"]:
                return reply({"error": "empty"}, 400)
            ts.append(now); _INFO_ASK[ip] = ts
            INFO_MSGS.append(m)
            log_event("sys", f"Question from the product page: {m['name'] or ip} - {m['topic']}")
            try:
                watch.notifier.info((m["name"] or ip) + " (" + m["topic"] + "):\n" + m["msg"], title="{name}: " + tr("question from the product page"))
            except Exception:
                pass
            return reply({"ok": True})

        @app.route("/api/info", methods=["GET", "POST"])
        def api_info():
            if request.method == "POST":
                d = body()
                if "on" in d:
                    CFG["info_page"] = bool(d["on"]); save_settings()
                if "mail" in d:
                    v_ = str(d.get("mail") or "").strip()[:80]
                    if v_ and not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", v_):
                        return reply({"ok": False, "error": tr("not a valid e-mail address", norm_lang(d.get("lang")))}, 400)
                    CFG["info_mail"] = v_; save_settings()
                if d.get("action") == "clear":
                    INFO_MSGS.clear()
            url = (page_address() or request.host_url).rstrip("/") + "/info/"
            return reply({"ok": True, "on": bool(CFG.get("info_page")), "mail": CFG.get("info_mail") or "", "url": url, "qr": qr_svg(url),
                          "msgs": list(INFO_MSGS)[::-1]})

        @app.route("/nt/")
        def nt_page():
            if not nettest_open():
                return Response("<h2 style='font-family:sans-serif'>Der Netz-Check ist gerade nicht offen. / The network check is not open.</h2>", 404, mimetype="text/html")
            return Response(NT_PAGE.replace("__NTJS__", NT_JS), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/nt/walk/")
        def nt_walk_page():
            if not nettest_open():
                return Response("<h2 style='font-family:sans-serif'>Der Netz-Check ist gerade nicht offen. / The network check is not open.</h2>", 404, mimetype="text/html")
            return Response(NT_WALK_PAGE, mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/nt/walk/points")
        def nt_walk_points():
            if not nettest_open():
                return reply({"error": "closed"}, 404)
            return reply({"points": [{k: p_[k] for k in ("x", "z", "q")} for p_ in NETWALK]})

        @app.route("/nt/walk/point", methods=["POST"])
        def nt_walk_point():
            if not nettest_open():
                return reply({"error": "closed"}, 404)
            pt = netwalk_add(_nt_ip(), body())
            return reply({"ok": bool(pt), "point": pt, "error": None if pt else "position missing"}, 200 if pt else 400)

        @app.route("/nt/ping")
        def nt_ping():
            if not nettest_open():
                return Response("", 404)
            return Response("1", mimetype="text/plain", headers={"Cache-Control": "no-store"})

        @app.route("/nt/down")
        def nt_down():
            if not nettest_open():
                return Response("", 404)
            ip = _nt_ip(); kb = request.args.get("kb", "256")
            n = (int(kb) if kb.isdigit() else 256) * 1024
            n = max(1024, min(4 << 20, n))
            used = NETTEST["bytes"].get(ip, [0, 0])
            if used[0] + n > NT_DOWN_MAX:
                return Response("limit", 429)
            used[0] += n; NETTEST["bytes"][ip] = used

            def gen(n=n):
                while n > 0:
                    b = NT_BLOB[:min(n, len(NT_BLOB))]; n -= len(b)
                    yield b
            return Response(gen(), mimetype="application/octet-stream", headers={"Cache-Control": "no-store", "Content-Length": str(n)})

        @app.route("/nt/up", methods=["POST"])
        def nt_up():
            if not nettest_open():
                return Response("", 404)
            ip = _nt_ip(); used = NETTEST["bytes"].get(ip, [0, 0]); got = 0
            while True:
                b = request.stream.read(65536)
                if not b:
                    break
                got += len(b)
                if used[1] + got > NT_UP_MAX:
                    return Response("limit", 429)
            used[1] += got; NETTEST["bytes"][ip] = used
            return Response(str(got), mimetype="text/plain")

        @app.route("/nt/report", methods=["POST"])
        def nt_report():
            if not nettest_open():
                return reply({"error": "closed"}, 404)
            if len(NETTEST["res"]) >= 60 and _nt_ip() not in NETTEST["res"]:
                return reply({"error": "full"}, 409)
            r = nettest_report(_nt_ip(), body())
            return reply({k: r[k] for k in ("grade", "why", "rtt", "jitter", "loss", "down", "up", "dbm") if k in r})

        @app.route("/api/nettest", methods=["GET", "POST"])
        def api_nettest():
            if request.method == "POST":
                d = body()
                if d.get("action") == "start":
                    nettest_start(int(d.get("minutes") or 3) if str(d.get("minutes") or "3").isdigit() else 3)
                elif d.get("action") == "stop":
                    nettest_stop()
                elif d.get("action") == "clear":
                    NETTEST["res"] = {}
                elif d.get("action") == "walk_clear":
                    NETWALK.clear()
                elif d.get("action") == "walk_sim":                 # the map as patches on the ground of the 3D simulator
                    try:
                        r_ = sim_control({"action": "netmap", "points": [{k: p_[k] for k in ("x", "z", "q", "rtt", "down", "dbm")} for p_ in NETWALK]})
                        if not (isinstance(r_, dict) and r_.get("ok")):
                            return reply({"ok": False, "error": tr("not supported - update the simulator", norm_lang(d.get("lang")))}, 400)
                    except Exception:
                        return reply({"ok": False, "error": tr("simulator not reachable", norm_lang(d.get("lang")))}, 400)
            st_ = nettest_state()
            st_["full_url"] = (page_address() or request.host_url).rstrip("/") + "/nt/"
            st_["qr"] = qr_svg(st_["full_url"])
            st_["walk_url"] = st_["full_url"] + "walk/"
            st_["walk_qr"] = qr_svg(st_["walk_url"]) if NETTEST["until"] > time.time() else ""
            st_["sim_ok"] = bool(CFG.get("sim_on") and time.time() - SIM.get("t", 0) < 15)
            return reply(dict(st_, ok=True))

        @app.route("/tv/<key>/")
        def tv_page(key):
            if not CFG.get("tv_key") or not secrets.compare_digest(key, CFG["tv_key"]):
                return Response("not found", 404)
            return Response(TV_PAGE, mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/tv/<key>/data")
        def tv_page_data(key):
            if not CFG.get("tv_key") or not secrets.compare_digest(key, CFG["tv_key"]):
                return Response("not found", 404)
            return reply(tv_data())

        @app.route("/tv/<key>/view.jpg")
        def tv_view(key):
            if not CFG.get("tv_key") or not secrets.compare_digest(key, CFG["tv_key"]):
                return Response("not found", 404)
            if CFG.get("sim_on"):
                try:
                    b_, _h = _sim_get("/view.jpg", 3.0)
                    if b_:
                        ct_ = (_h.get("Content-Type") if _h is not None else "") or "image/jpeg"     # 2.95.81: may be WebP
                        return Response(b_, mimetype="image/webp" if "webp" in ct_ else "image/jpeg", headers={"Cache-Control": "no-store"})
                except Exception:
                    pass
            if time.time() > watch.raw_until:
                watch.frame_raw = None
            watch.raw_until = time.time() + 15
            for _ in range(20):
                if watch.frame_raw is not None:
                    break
                time.sleep(0.1)
            f_ = watch.frame_raw
            if f_ is None:
                return Response("no picture", 503, {"Retry-After": "1"})
            ok_, buf_ = cv2.imencode(".jpg", f_, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return Response(buf_.tobytes() if ok_ else b"", mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

        @app.route("/api/tv", methods=["POST"])
        def api_tv():
            d = body(); lang = norm_lang(d.get("lang"))
            if "auto" in d:
                CFG["tv_auto"] = bool(d["auto"]); save_settings()
            ok, err = (True, "")
            if "sim" in d:
                ok, err = tv_sim(bool(d["sim"]), "web " + (request.remote_addr or "?"))
            elif "on" in d:
                ok, err = tv_show(bool(d["on"]), "web " + (request.remote_addr or "?"))
            return reply({"ok": ok, "error": tr(err, lang) if err else None, "tv": tv_state()}, 200 if ok else 400)

        @app.route("/spiele")
        @app.route("/spiele/")
        def spiele_home():
            if not _lan_ok():
                return Response(_lan_no, 403, mimetype="text/html")
            return Response(spiele_page(request.host), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/spiele/g/<game>/")
        @app.route("/spiele/g/<game>/<path:fn>")
        def spiele_file(game, fn=""):
            if not _lan_ok():
                return Response(_lan_no, 403, mimetype="text/html")
            u_ = games_url(game, fn, request.host)
            if u_:
                return redirect(u_)                      # 2.95.35: games come from their own port
            p_ = games_file(game, fn)
            if p_ and p_.lower().endswith((".html", ".htm")):
                with open(p_, "rb") as f_:
                    return Response(games_inject_back(f_.read(), "/spiele"), mimetype="text/html")
            return send_file(p_, max_age=3600) if p_ else Response("not found", 404)

        @app.route("/games/<game>/")
        @app.route("/games/<game>/<path:fn>")
        def games_file_auth(game, fn=""):
            u_ = games_url(game, fn, request.host) if lan_guest_ip(request.remote_addr, request.headers.get("X-Forwarded-For", "")) else ""
            if u_:
                return redirect(u_)
            p_ = games_file(game, fn)
            if p_ and p_.lower().endswith((".html", ".htm")):
                with open(p_, "rb") as f_:
                    return Response(games_inject_back(f_.read(), "/party"), mimetype="text/html")
            return send_file(p_, max_age=3600) if p_ else Response("not found", 404)

        @app.route("/api/party", methods=["GET", "POST"])
        def api_party():
            if request.method == "POST":
                if getattr(g, "role", "admin") != "admin":
                    return reply({"ok": False, "error": "not allowed"}, 403)
                d = body(); a_ = d.get("action")
                if a_ in ("open", "all"):                     # 2.98.7: «Spiele freigeben» = all games at once
                    games_all_open(float(d.get("hours") or 6), "web " + (request.remote_addr or "?"))
                elif a_ == "close":
                    games_all_close("web " + (request.remote_addr or "?"))
                elif a_ == "rest":                     # MoveEye rests, only the game server runs (2.95.31)
                    if d.get("on"):
                        mins = (PARTY["until"] - time.time()) / 60 if party_on() else float(d.get("hours") or 6) * 60
                        ok_, e_ = toolmode_set(max(5, min(720, int(mins + 0.99))), "game corner")
                        if not ok_:
                            return reply({"ok": False, "error": e_}, 400)
                    else:
                        toolmode_set(0, "web " + (request.remote_addr or "?"))
                elif a_ == "kick" and d.get("id") in PARTY["players"]:
                    PARTY["players"].pop(d["id"], None)
                    if PARTY["host"] == d["id"]:
                        PARTY["host"] = next(iter(PARTY["players"]), "")
                    party_bump()
                elif a_ == "host" and d.get("id") in PARTY["players"]:
                    PARTY["host"] = d["id"]; party_bump()
                elif a_ == "install":
                    threading.Thread(target=games_install, daemon=True).start()
            base = (CFG.get("public_url") or "").strip().rstrip("/")
            local = page_address().rstrip("/") if "page_address" in globals() else request.host_url.rstrip("/")
            url = (local or request.host_url.rstrip("/")) + "/p/" + PARTY["key"] + "/" if party_on() else ""
            return reply({"ok": True, "on": party_on(), "url": url, "lan_url": (local or request.host_url.rstrip("/")) + "/spiele", "qr": qr_svg(url) if url else "", "left": int(max(0, PARTY["until"] - time.time())),
                          "players": [{"id": k, "name": v["name"], "score": v["score"], "host": k == PARTY["host"], "on": time.time() - v["t"] < 25}
                                      for k, v in PARTY["players"].items()], "game": PARTY["game"],
                          "games": games_list(), "games_ver": games_installed_version(), "rest": toolmode_state(), "games_pkg": GAMES_PKG, "dl": dict(GAMES_DL),
                          "remote": base, "all": games_all_state()})

        @app.route("/api/simtest/pic/<int:rid>/<name>")
        def api_simtest_pic(rid, name):
            if not re.fullmatch(r"[fm]\d{2}\.jpg", name):
                return Response("", 404)
            p_ = os.path.join(_testopt_dir(rid), name)
            if not os.path.isfile(p_):
                return Response("", 404)
            with open(p_, "rb") as f_:
                return Response(f_.read(), mimetype="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})

        @app.route("/api/simtest/report.zip")
        def api_simtest_report():
            """«Report for the development» (2.95.28): the last test runs with versions, settings of the recognition, results,
            causes and the pictures of the mistakes - no passwords, no addresses, no recordings"""
            import io
            n_ = max(1, min(30, int(request.args.get("n", 10)) if str(request.args.get("n", "10")).isdigit() else 10))
            runs = TESTOPT["runs"][-n_:]
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                info_ = {"made": datetime.now().isoformat(timespec="seconds"), "motion_watch": APP_VERSION, "simulator_expected": SIM3D["version"],
                         "platform": "pi" if _is_pi() else sys.platform, "ai": STATE.get("ai_status"), "compare": testopt_compare(),
                         "runs": [{k: r.get(k) for k in ("t", "plan", "score", "cfg", "mw", "sim", "night", "pics", "report")} for r in runs]}
                for r in info_["runs"]:
                    r["report"] = {k: v for k, v in (r.get("report") or {}).items() if k != "device"}
                z.writestr("testlauf_bericht.json", json.dumps(info_, indent=1, ensure_ascii=False))
                z.writestr("LIES_MICH.txt", "Bericht der Testläufe von MoveEye " + APP_VERSION + " für die Entwicklung.\n"
                           "Einfach im Chat mit Claude anhängen oder auf GitHub in den Ordner feedback/ hochladen.\n"
                           "Enthält: Versionen, Erkennungs-Einstellungen, Ergebnisse pro Phase, Ursachen, kleine Bilder der Fehler.\n"
                           "Enthält nicht: Passwörter, Schlüssel, Adressen, Aufnahmen.\n")
                for r in runs:
                    for pc in r.get("pics") or []:
                        p_ = os.path.join(_testopt_dir(r["t"]), pc["file"])
                        if os.path.isfile(p_):
                            z.write(p_, f"bilder/{int(r['t'])}_{pc['file']}")
            name = "MotionWatch_Testbericht_" + APP_VERSION.replace(".", "_") + "_" + datetime.now().strftime("%Y%m%d_%H%M") + ".zip"
            return Response(buf.getvalue(), mimetype="application/zip", headers={"Content-Disposition": f'attachment; filename="{name}"'})

        @app.route("/api/sim/upload", methods=["POST"])
        def api_sim_upload():
            lang = norm_lang(request.args.get("lang"))
            name = os.path.basename(str(request.args.get("name") or ""))[:120]
            n = int(request.content_length or 0)
            if not name or n <= 0:
                return reply({"ok": False, "error": tr_err("no file", lang)}, 400)
            try:
                r = sim_upload(name, request.stream, n)
            except Exception as e:
                return reply({"ok": False, "error": tr_err("simulator not reachable", lang) + f" ({str(e)[:60]})"}, 400)
            if not r.get("ok"):
                return reply({"ok": False, "error": tr_err(str(r.get("error") or "not supported - update the simulator"), lang)}, 400)
            log_event("sys", f"Video for the simulator uploaded: {r.get('saved', name)} ({n / 1024 ** 2:.0f} MB)")
            return reply(dict(r, ok=True))

        @app.route("/sim/simulator3d.zip")
        def sim3d_zip():
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            if sim3d_ready():
                return send_file(sim3d_path(), mimetype="application/zip", as_attachment=True,
                                 download_name=f"MotionWatch3D_Simulator_{SIM3D['version']}.zip", conditional=True)
            if request.args.get("retry"):
                SIM3D_DL["msg"] = ""
            if not SIM3D_DL["msg"]:
                sim3d_fetch()
            return Response(sim3d_wait_page(lang), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/sim/game_pic/<int:i>.jpg")
        def sim_game_pic(i):
            """a «caught» photo of the game (3D-3.25)"""
            if not CFG["sim_on"]:
                return Response("simulation off", 404)
            try:
                b_, _h = _sim_get(f"/game_pic/{int(i)}.jpg", 3.0)
            except Exception:
                return Response("no picture", 404)
            return Response(b_, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

        @app.route("/sim/game_qr.png")
        def sim_game_qr():
            """the QR code of the game in the 3D simulator (3D-3.20): players photograph it with their phone"""
            if not CFG["sim_on"]:
                return Response("simulation off", 404)
            try:
                b_, _h = _sim_get("/game_qr.png", 3.0)
            except Exception:
                return Response("game not open", 404)
            return Response(b_, mimetype="image/png", headers={"Cache-Control": "no-store"})

        @app.route("/sim/view.jpg")
        def sim_view_jpg():
            """one picture of the simulator window (the page fetches them one by one: never a growing delay)"""
            if not CFG["sim_on"]:
                return Response("simulation off", 404)
            q_ = []                                          # 2.95.81: size (width × pixel density), quality, WebP from the page
            for k_ in ("w", "q"):
                v_ = str(request.args.get(k_) or "")
                if v_.isdigit():
                    q_.append(f"{k_}={int(v_)}")
            if request.args.get("fmt") in ("webp", "jpg"):
                q_.append("fmt=" + request.args.get("fmt"))
            if request.args.get("clean") == "1":
                q_.append("clean=1")                         # 2.95.92: full screen - the simulator hides its rover stick
            if request.args.get("bare") == "1":
                q_.append("bare=1")                          # «Controller-Ansicht» (538): the picture without the buttons of the window
            try:
                b_, h_ = _sim_get("/view.jpg" + ("?" + "&".join(q_) if q_ else ""), 3.0)
            except Exception:
                return Response("simulator not reachable", 502)
            if not b_:
                return Response("no picture yet", 503, {"Retry-After": "1"})
            ct_ = (h_.get("Content-Type") if h_ is not None else "") or "image/jpeg"
            return Response(b_, mimetype="image/webp" if "webp" in ct_ else "image/jpeg", headers={"Cache-Control": "no-store"})

        @app.route("/sim/view.mjpg")
        def sim_view():
            """the simulator window (3D view with map, compass and view buttons), passed on from the simulator (3D-3.18)"""
            if not CFG["sim_on"]:
                return Response("simulation off", 404)
            try:
                fps_ = max(1, min(10, int(request.args.get("fps") or 6)))
            except ValueError:
                fps_ = 6
            try:
                up_ = _SIM_OPENER.open(urllib.request.Request(sim_base() + f"/view.mjpg?fps={fps_}", headers={"User-Agent": "MotionWatch"}), timeout=5)
            except Exception:
                return Response("simulator not reachable", 502)
            ctype_ = up_.headers.get("Content-Type") or "multipart/x-mixed-replace; boundary=mwsimframe"

            def gen():
                try:
                    while CFG["sim_on"]:
                        b_ = up_.read1(65536) if hasattr(up_, "read1") else up_.read(65536)
                        if not b_:
                            break
                        yield b_
                except Exception:
                    pass
                finally:
                    try:
                        up_.close()
                    except Exception:
                        pass
            return Response(gen(), mimetype=None, content_type=ctype_, headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

        @app.route("/sim/simulator_py.zip")
        def simpy_zip():
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            if sim3d_ready(SIMPY):
                return send_file(sim3d_path(SIMPY), mimetype="application/zip", as_attachment=True,
                                 download_name=f"{SIMPY['stem']}_{SIMPY['version']}.zip", conditional=True)
            if request.args.get("retry"):
                SIMPY_DL["msg"] = ""
            if not SIMPY_DL["msg"]:
                sim3d_fetch(SIMPY, SIMPY_DL)
            return Response(sim3d_wait_page(lang, SIMPY, SIMPY_DL, "/sim/simulator_py.zip"), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/sim/simulator.zip")
        def sim_zip():
            import base64
            return Response(base64.b64decode("".join(SIM_ZIP_B64.split())), mimetype="application/zip",
                            headers={"Content-Disposition": 'attachment; filename="MotionWatch_Simulator.zip"'})

        @app.route("/api/hwcheck", methods=["POST"])
        def api_hwcheck():
            d = body(); res = d.get("results") if isinstance(d.get("results"), dict) else {}
            parts = [f"{str(k)[:16]}={str(v)[:5]}" for k, v in list(res.items())[:30]]
            n_ok = sum(1 for v in res.values() if v == "ok"); n_bad = sum(1 for v in res.values() if v == "bad")
            log_event("sys", f"Hardware check: {n_ok} ok, {n_bad} failed - " + ", ".join(parts))
            return reply({"ok": True})

        @app.route("/api/users", methods=["GET", "POST"])
        def api_users():
            if request.method == "GET":
                return reply({"users": [{"name": u["name"], "role": u["role"]} for u in CFG["users"]], "pw": web_pw_active()})
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = users_action(d, getattr(g, "user", "") or "admin")
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None,
                          "users": [{"name": u["name"], "role": u["role"]} for u in CFG["users"]]}, 200 if ok else 400)

        @app.before_request
        def demo_guard():                           # demo: nothing that changes the computer or reaches outside
            if DEMO["on"] and request.method == "POST" and (request.path.startswith(DEMO_BLOCK)
                                                            or (request.path == "/api/update" and (body().get("action") == "install"))
                                                            or (request.path == "/api/setup" and body().get("password"))
                                                            or (request.path == "/api/webpush" and body().get("action") == "https")):
                lang = norm_lang(body().get("lang") or CFG["lang"])
                return reply({"ok": False, "error": tr("not possible in the demo", lang)}, 403)
            return None

        @app.before_request
        def remote_seen():                          # runs only after a successful login (auth() above did not answer)
            remote_touch(request.remote_addr or "")

        @app.before_request
        def operator_lock():                        # operator mode: only the allowed actions get through
            if not CFG["lock_on"] or request.path.startswith("/g/"):
                return None
            d = request.get_json(force=True, silent=True) if request.method == "POST" else None
            if lock_allows(request.path, request.method, d if isinstance(d, dict) else {}):
                return None
            lang = norm_lang(((d or {}).get("lang") if isinstance(d, dict) else None) or CFG["lang"])
            return reply({"ok": False, "error": tr_err("locked - settings can only be changed after unlocking (PIN)", lang)}, 423)

        timeline_routes(app, reply, body, request, Response)    # 2.98.14: Verlauf → Zeitleiste + weekly report (523)
        alx_routes(app, watch, reply, body)                # 2.98.13: push buttons /na/, «What was it?» (066)
        sx_routes(app, watch, reply, body)                 # night view / screen reader script, «holiday over», error pages (578)
        fbx_routes(app, watch, reply, body)                # 2.98.33: feedback from every page, «About MoveEye» (584)
        appkey_routes(app, reply, body)                    # app keys, security check in Settings → Security (573)
        place_routes(app, watch, reply, body)              # 2.98.30: «Platz einrichten» /place, field of view per camera (537)
        g2_routes(app, watch, reply, body)                 # guide 2: tours, tip of the day, factory reset (586)
        qr_routes(app, reply, body)                        # QR codes: POST /api/qr, gallery /qr, print page, no-store for secrets (587)
        servo_routes(app, reply, body)                     # 2.98.35: servos - Not-Aus, taught points, diagnosis /servo, /api/servo (539)
        ginv_routes(app, reply, body)                      # game for guests online /game/<token>/ (only the game, token + expiry), «Human vs AI» (343)

        @app.route("/messages")
        def messages_page():                               # 2.98.13: the push messages (Verlauf → Nachrichten)
            return Response(render_page(MSG_PAGE, "msgs"), mimetype="text/html")

        @app.route("/api/messages", methods=["GET", "POST"])
        def api_messages():
            if request.method == "POST":
                if (body().get("action") or "") == "clear":
                    msglog_clear()
                    return reply({"ok": True})
                return reply({"ok": False, "error": "unknown action"}, 400)
            if request.args.get("src") == "server":
                items, err = ntfy_server_messages(str(request.args.get("since", "24h")))
                return reply({"ok": not err, "items": items, "error": err or None})
            return reply({"ok": True, "items": msglog_list()})

        @app.route("/api/messages/img/<mid>")
        def api_messages_img(mid):
            p = msglog_img(mid)
            if not p:
                return Response("not found", status=404)
            return send_file(p, mimetype="image/jpeg", max_age=86400)

        @app.route("/log")
        def log_page():
            return Response(render_page(LOG_PAGE, "log"), mimetype="text/html")

        @app.route("/api/log")
        def api_log():
            try:
                lim = max(10, min(5000, int(request.args.get("limit", 300))))
            except ValueError:
                lim = 300
            return reply({"lines": log_lines(request.args.get("file", ""), lim, str(request.args.get("kind") or "")[:12],
                                             str(request.args.get("q") or "")[:80]), "archive": log_archive()})

        @app.route("/api/log/file/<name>")
        def api_log_file(name):
            if name == "motionwatch.log":
                path = LOG_FILE
            elif LOG_NAME_RE.match(name):
                path = os.path.join(log_dir(), name)
            else:
                return Response("not found", 404)
            if not os.path.isfile(path):
                return Response("not found", 404)
            dl = name if name != "motionwatch.log" else "motionwatch_" + datetime.now().strftime("%Y-%m-%d") + "_bis_" + datetime.now().strftime("%H%M") + ".log"
            return send_file(path, mimetype="application/gzip" if name.endswith(".gz") else "text/plain", as_attachment=True,
                             download_name=dl, max_age=0)

        @app.route("/api/lock", methods=["POST"])
        def api_lock():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = lock_set(d.get("action"), d.get("pin", ""), d.get("new_pin", ""), source="web " + (request.remote_addr or "?"))
            return reply(dict(lock_info(), ok=ok, error=tr_err(err, lang) if err else None), 200 if ok else 400)

        @app.route("/api/version")
        def api_version():
            if _RESTART_M["todo"]:
                restart_measure()
            now = time.time(); P_ = UPD_PROG
            up = ({"phase": P_["phase"], "got": P_["got"], "size": P_["size"], "el": round(now - P_["t0"], 1), "since": round(now - P_["tp"], 1)}
                  if P_["phase"] else {})
            return reply({"app": "Motion Watch", "version": APP_VERSION, "file": os.path.basename(__file__), "upd": up, "est": round(restart_est())})

        @app.after_request
        def secure_headers(resp):
            mt_ = resp.mimetype or ""
            if resp.is_streamed and mt_.startswith(("multipart/x-mixed-replace", "text/event-stream")):
                ip_ = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr or "?"
                with STREAMS["lock"]:
                    if STREAMS["n"] >= 16 or STREAMS["ip"].get(ip_, 0) >= 6:      # 2.95.35: a Pi cannot feed more
                        try:
                            resp.response.close()
                        except Exception:
                            pass
                        return Response("too many live pictures open - close some pages", 503, {"Retry-After": "10"})
                    STREAMS["n"] += 1; STREAMS["ip"][ip_] = STREAMS["ip"].get(ip_, 0) + 1
                inner = resp.response

                def counted():
                    try:
                        yield from inner
                    finally:
                        with STREAMS["lock"]:
                            STREAMS["n"] -= 1; STREAMS["ip"][ip_] = STREAMS["ip"].get(ip_, 1) - 1
                            if STREAMS["ip"][ip_] <= 0:
                                STREAMS["ip"].pop(ip_, None)
                resp.response = counted()
            if resp.mimetype == "text/html":
                resp.headers["Cache-Control"] = "no-store"          # always the page of the program that runs now
                resp.headers.setdefault("Content-Security-Policy", "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'")
            resp.headers.setdefault("X-Content-Type-Options", "nosniff")
            resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")    # only our own preview page (/preview) may show it in a frame
            resp.headers.setdefault("Referrer-Policy", "no-referrer")
            return resp

        @app.route("/preview")
        def preview_page():                         # the page as it looks on a phone / tablet, upright and across (for the simulator)
            return Response(PREVIEW_PAGE, mimetype="text/html")

        @app.route("/")
        def index():
            return Response(main_tab_page("live"), mimetype="text/html")

        @app.route("/protect")                             # 2.98.0: the tabs «Schutz» and «Einstellungen» = the main page, other part shown
        def protect_page():
            return Response(main_tab_page("protect"), mimetype="text/html")

        @app.route("/settings")
        def settings_page():
            return Response(main_tab_page("settings"), mimetype="text/html")

        @app.route("/more")
        def more_page_():
            return Response(more_page(), mimetype="text/html")

        @app.route("/cams")
        def cams_page():
            return Response(render_page(CAMS_PAGE, "cams"), mimetype="text/html")

        @app.route("/zones")
        def zones_page():
            return Response(render_page(ZONES_PAGE, "zones"), mimetype="text/html")

        @app.route("/video_feed")
        def video_feed():
            rip = request.remote_addr or ""
            def gen():
                last = -1
                watch.web_viewers += 1; STATE["web_viewers"] = watch.web_viewers
                remote_stream(rip, +1)
                try:
                    while True:
                        jpg, seq = watch.jpeg, watch.jpeg_seq
                        if jpg and seq != last:
                            last = seq
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode()
                                   + b"\r\n\r\n" + jpg + b"\r\n")
                        else:
                            time.sleep(0.02)
                finally:
                    watch.web_viewers = max(0, watch.web_viewers - 1); STATE["web_viewers"] = watch.web_viewers
                    remote_stream(rip, -1)
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

        def _ext_ok(tok):
            return bool(CFG["ext_on"]) and isinstance(tok, str) and len(tok) >= 20 and hmac.compare_digest(tok, ext_token())

        @app.route("/x/<tok>/video.mjpg")
        def ext_video(tok):
            if not _ext_ok(tok):
                return Response("not found", 404)
            def gen():
                last = -1
                watch.web_viewers += 1; STATE["web_viewers"] = watch.web_viewers      # the camera loop makes JPEGs while somebody watches
                try:
                    while True:
                        jpg, seq = watch.jpeg, watch.jpeg_seq
                        if jpg and seq != last:
                            last = seq
                            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n"
                        else:
                            time.sleep(0.03)
                finally:
                    watch.web_viewers = max(0, watch.web_viewers - 1); STATE["web_viewers"] = watch.web_viewers
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame", headers={"Cache-Control": "no-store"})

        @app.route("/x/<tok>/snapshot.jpg")
        def ext_snapshot(tok):
            if not _ext_ok(tok):
                return Response("not found", 404)
            f = watch.frame_out
            if f is None:
                return Response("no picture yet", 503)
            ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                return Response("encode error", 500)
            return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

        @app.route("/api/ext", methods=["GET", "POST"])
        def api_ext():
            if request.method == "POST" and body().get("action") == "renew":
                ext_new_token()
            host = (request.host or "").rsplit(":", 1)[0] or None
            return reply(ext_links(host if host not in ("localhost", "127.0.0.1") else None))

        # ---- shortcut addresses (2.95.27): an iPhone shortcut calls them without the password, with its own key ----
        SC_FAILS = {}

        @app.route("/k/<key>/<action>")
        def shortcut(key, action):
            import hmac
            ip = request.remote_addr or "?"; now = time.time()
            rec = [x for x in SC_FAILS.get(ip, []) if now - x < 600]
            if len(rec) >= 10:
                return Response("too many wrong keys - wait 10 minutes", 429)
            ke = appkey_find(key)                  # aufr: one key system - shortcut keys and every other app key (573)
            if ke is None:
                rec.append(now); SC_FAILS[ip] = rec
                return Response("unknown key", 403)
            appkey_seen(ke, ip)
            txt = None
            if action == "arm":
                arm(); txt = "armed" if is_armed() else "arming (delay " + str(CFG.get("arm_delay", "")) + " s)"
            elif action == "disarm":
                disarm(); txt = "disarmed"
            elif action == "siren_off":
                sound_stop(); txt = "siren off"
            elif action in ("light_on", "light_off", "light_auto"):
                light_set("white", action.split("_")[1]); txt = "white light " + action.split("_")[1]
            elif action == "ir_on" or action == "ir_off":
                light_set("ir", action.split("_")[1]); txt = "infrared " + action.split("_")[1]
            elif action == "status":
                return reply({"device": CFG["device_name"] or "MoveEye", "armed": is_armed(), "persons": int(STATE.get("persons") or 0),
                              "simulation": bool(CFG["sim_on"]), "last_alarm": STATE.get("last_person_str") or ""})
            elif action == "photo.jpg":
                if watch.frame_out is None:
                    return Response("no picture yet", 503)
                ok, buf = cv2.imencode(".jpg", watch.frame_out, [cv2.IMWRITE_JPEG_QUALITY, 85])
                return Response(buf.tobytes(), mimetype="image/jpeg") if ok else Response("error", 500)
            else:
                return Response("unknown action", 404)
            log_event("web", f"Shortcut from {ip}: {txt}")
            return Response(txt, mimetype="text/plain")

        @app.route("/api/shortcut", methods=["GET", "POST"])
        def api_shortcut():
            if getattr(g, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            base = (CFG.get("public_url") or "").strip().rstrip("/") or request.host_url.rstrip("/")
            if request.method == "POST":                   # aufr: the shortcut keys are app keys (573)
                res_, code_ = shortcut_action(body(), getattr(g, "user", "") or "admin", request)
                return reply(dict(shortcut_state(base), **res_), code_)
            return reply(shortcut_state(base))

        @app.route("/snapshot.jpg")
        def snapshot():
            if watch.frame_out is None:
                return Response("no frame yet", 503)
            ok, buf = cv2.imencode(".jpg", watch.frame_out, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ok:
                return Response("encode error", 500)
            watch_jpeg = buf.tobytes()
            name = datetime.now().strftime("snapshot_%Y%m%d_%H%M%S.jpg")
            return Response(watch_jpeg, mimetype="image/jpeg",
                            headers={"Content-Disposition": f'attachment; filename="{name}"'})

        @app.route("/api/schema")
        def api_schema():
            lang = request.args.get("lang") or CFG["lang"]
            sv = request.args.get("simple")                # Simple / Expert of this page (586)
            _G2_SIMPLE.v = None if sv not in ("0", "1") else sv == "1"
            try:
                return reply(web_schema(norm_lang(lang), request.args.get("sec") or None))   # 2.98.14: ?sec= one section (page Simulator)
            finally:
                _G2_SIMPLE.v = None

        @app.route("/api/appearance")
        def api_appearance():
            return reply({"theme": CFG["theme"], "lang": CFG["lang"]})

        @app.route("/api/state")
        def api_state():
            with LOCK:
                st = {k: v for k, v in STATE.items() if k != "events"}
                st["viewers"] = viewers_now()
                st["project"] = project_info()
                st["gps"] = gps_state()
                st["gpsmod"] = {"status": GPSMOD["status"], "via": GPSMOD["via"], "sats": GPSMOD["sats"], "lat": GPSMOD["lat"], "lon": GPSMOD["lon"],
                                "age": int(time.time() - GPSMOD["t"]) if GPSMOD["t"] else None, "anchor": bool(GPSMOD["anchor"]), "dist": GPSMOD.get("dist"),
                                "theft": bool(GPSMOD["alarm_t"])}
                imp = [dict(e) for e in STATE["events"] if e.get("imp")][:25]
                if len(imp) < 10:                      # at least 10 lines: fill up with the newest other entries (shown pale)
                    ids = {id(e) for e in STATE["events"] if e.get("imp")}
                    extra = [dict(e, dim=True) for e in STATE["events"] if id(e) not in ids and e.get("kind") != "status"][:10 - len(imp)]
                    pos = {id(e): i for i, e in enumerate(STATE["events"])}
                    both = [(e, True) for e in STATE["events"] if e.get("imp")][:25] + [(e, False) for e in STATE["events"]
                            if id(e) not in ids and e.get("kind") != "status"][:10 - len(imp)]
                    both.sort(key=lambda x: pos[id(x[0])])
                    imp = [dict(e) if keep else dict(e, dim=True) for e, keep in both]
                events = imp
                relays = [dict(r) for r in RELAYS]
                schedules = [dict(x) for x in SCHEDULES]
                st["extra"] = cams_status()
                st["camping"] = bool(CFG["camping"]); st["net_mode"] = CFG["net_mode"]; st["power_msg"] = POWER["msg"]
                st["pw_set"] = web_pw_active(); st["pw_cli"] = bool(CFG["web_password"]); st["version"] = APP_VERSION
                st["seclogin"] = {k: v for k, v in seclogin_info(request).items() if k in ("mode", "plain", "url", "secure")}
                try:
                    st["health"] = health_check()["count"]
                except Exception:
                    st["health"] = None
                st["mqtt"] = {"status": MQTT["status"], "topic": (CFG["mqtt_prefix"].strip().strip("/") or "motionwatch") + "/" + device_uid() if CFG["mqtt_on"] else ""}
                st["web_open"] = not st["pw_set"] and WEB_OPTS["bind"] not in ("127.0.0.1", "localhost", "::1")
                st["guest"] = guest_info(); st["report_on"] = bool(CFG["report_on"]); st["lock"] = lock_info()
                st["me"] = {"name": getattr(g, "user", ""), "role": getattr(g, "role", "admin"), "users": len(CFG["users"])}
                st["pending"] = RESTART["pending"]
                st["quick_rec"] = time.time() < QUICK["rec_until"]
                st["games"] = {"on": party_on(), "n": len(PARTY["players"])}           # 2.98.7: quick switch «Spiele»
                st["settings_status_txt"] = settings_status_text(norm_lang(request.args.get("lang") or CFG["lang"]))
                st["autostart_msg"] = tr_err(AUTOSTART["msg"], norm_lang(request.args.get("lang") or CFG["lang"])) if AUTOSTART["msg"] else ""
                lang_ = norm_lang(request.args.get("lang") or CFG["lang"])
                st["light_cfg"] = {k: CFG["light_" + k] for k in ("white", "ir", "white_out", "ir_out")}
                if CFG["sim_on"]:                          # the simulation has its own lamps
                    st["light_cfg"]["white_out"] = st["light_cfg"]["white_out"] or "sim"; st["light_cfg"]["ir_out"] = st["light_cfg"]["ir_out"] or "sim"
                st["sim"] = sim_status()
                st["turbo"] = turbo_state()
                st["mode"] = mode_state()
                st["tv"] = tv_state()
                st["disco"] = disco_state()
                st["protect"] = protect_status(lang_)          # 2.95.105
                st["tunnel"] = tunnel_state()
                st["helper"] = helper_state()
                st["alarm_tracks"] = alarm_tracks_list()[:12]
                st["mover"] = {"avail": MOVER["avail"], "sim": MOVER["sim"], "test": MOVER["test"], "hw": MOVER["hw"], "l": MOVER["l"], "r": MOVER["r"],
                               "msg": tr(MOVER["msg"], lang_), "mode": CFG["mover_mode"],
                               "pose": SIM.get("mover_pose") if MOVER["sim"] else None}
                st["soundev"] = soundev_state()
                st["servo"] = servo_client_state(request, lang_)      # 2.98.35: Not-Aus, who steers the head (539)
                st["wake"] = dict(wake_state(), text=wake_text(norm_lang(request.args.get("lang") or CFG["lang"])))   # 2.98.7
                st["light_cfg"].update({n + "_auto_label": dict(text_choice_pairs("light_white_auto")).get(CFG[f"light_{n}_auto"], "")
                                        for n in ("white", "ir")})
                st["tether"] = STATE.get("tether") or {"on": False}
                st["hotspot_cfg"] = {"ssid": CFG["hotspot_ssid"], "password": CFG["hotspot_password"] if getattr(g, "role", "admin") == "admin" else "",
                                     "address": page_address("10.42.0.1")}
                if getattr(g, "role", "admin") != "admin":
                    st["guest"] = {}
            cfg = {k: CFG[k] for k in web_specs()}
            cfg.update({k: CFG[k] for k in ("thermal_source", "deter_person_act", "deter_big_act", "deter_small_act", "deter_warm_act", "backup_type", "audio_in", "patrol_mode",
                                            "siren_on", "web_stream", "sensors", "qs_layout")})        # for the green arrows (overview)
            return reply({"state": st, "cfg": cfg, "waypoints": list(WAYPOINTS), "events": events, "relays": relays,
                          "schedules": schedules})

        @app.route("/api/triggers")
        def api_triggers():
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            return reply([{"key": k, "label": tr_trigger(k, lang)} for k in TRIGGERS])

        @app.route("/api/relay", methods=["POST"])
        def api_relay():
            d = body(); a = d.get("action"); idx = d.get("index")
            lang = norm_lang(d.get("lang"))
            if a == "set":
                ok, err = relay_update(idx, d.get("field"), d.get("value"))
            elif a == "add":
                ok, err = relay_add()
            elif a == "remove":
                ok, err = relay_remove(idx)
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/storm_test", methods=["POST"])
        def api_storm_test():
            d = body(); lang = norm_lang(d.get("lang"))
            storm_warn("test", tr("test - it works", lang), test=True)
            return reply({"ok": True})

        @app.route("/api/tts", methods=["POST"])
        def api_tts():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, msg = tts_say(d.get("text"), d.get("voice") or lang, bool(d.get("save")))
            return reply({"ok": ok, "error": tr_err(msg, lang) if not ok else None, "file": msg if ok and d.get("save") else ""}, 200 if ok else 400)

        @app.route("/api/sensors", methods=["POST"])
        def api_sensors():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = sens_action(d, lang)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "sensors": CFG["sensors"]}, 200 if ok else 400)

        @app.route("/api/feedback", methods=["POST"])
        def api_feedback():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = feedback_send(d.get("kind"), d.get("text"), str(d.get("contact") or "").strip(), bool(d.get("diag")), d.get("stars"),
                                    d.get("page"), fbx_web_shot(False) if d.get("shot") else None, "web")      # 2.98.33: stars, page, picture (584)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/quick", methods=["POST"])
        def api_quick():
            """Quick switches below the joystick: manual recording on / off, a photo into the recordings."""
            d = body(); a = d.get("action")
            if a in ("photo", "rec") and CFG["sim_on"]:
                return reply({"ok": False, "error": tr("simulation: nothing is recorded", norm_lang(d.get("lang") or request.args.get("lang")))}, 409)
            if a == "rec":
                return reply({"ok": True, "rec": quick_rec()})
            if a == "photo":
                name = quick_photo(watch.frame_out)
                if name is None:
                    return reply({"ok": False, "error": "no picture yet"}, 503)
                return reply({"ok": True, "name": name})
            if a == "patrol":                  # one button: off -> back and forth -> round trip -> off
                on, mode = quick_patrol("web")
                return reply({"ok": True, "patrol": on, "mode": mode})
            return reply({"ok": False, "error": "unknown action"}, 400)

        @app.route("/api/set", methods=["POST"])
        def api_set():
            d = body()
            ok, msg = set_cfg(d.get("key"), d.get("value"))
            return reply({"ok": ok, "error": msg or None}, 200 if ok else 400)

        @app.route("/api/move", methods=["POST"])
        def api_move():
            d = body()
            if not move_camera(d.get("dir"), d.get("step", 3), servo_client(request, d)):
                if servo_blocked():                        # 2.98.35: Not-Aus / fault (072)
                    return reply({"ok": False, "error": servo_blocked_text(norm_lang(d.get("lang") or CFG["lang"])), "blocked": servo_blocked()}, 423)
                return reply({"ok": False, "error": "unknown direction"}, 400)
            return reply({"ok": True, "pan": CFG["pan"], "tilt": CFG["tilt"]})

        @app.route("/api/mover", methods=["POST"])
        def api_mover():
            d = body()
            ok = mover_drive(d.get("v", 0), d.get("w", 0), "web")
            return reply({"ok": ok, "l": MOVER["l"], "r": MOVER["r"], "avail": MOVER["avail"]})

        @app.route("/api/stick", methods=["POST"])
        def api_stick():
            d = body()
            if not stick_camera(d.get("x", 0), d.get("y", 0), d.get("speed", 30), servo_client(request, d)):
                if servo_blocked():
                    return reply({"ok": False, "error": servo_blocked_text(norm_lang(d.get("lang") or CFG["lang"])), "blocked": servo_blocked()}, 423)
                return reply({"ok": False, "error": "invalid values"}, 400)
            return reply({"ok": True, "pan": CFG["pan"], "tilt": CFG["tilt"]})

        @app.route("/api/arm", methods=["POST"])
        def api_arm():
            a = body().get("action")
            if a == "arm":
                arm()
            elif a == "arm_now":
                arm(0)
            elif a == "disarm":
                if CFG.get("protect_pin"):                 # 2.95.105: disarming needs the PIN
                    ok_, err_ = protect_disarm(body().get("pin"), "web")
                    if not ok_:
                        return reply({"ok": False, "error": tr(err_, norm_lang(body().get("lang"))), "need_pin": True}, 403)
                else:
                    protect_cancel_escalation()
                    CFG["protect_level"] = "off"
                    disarm()
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True, "state": STATE["arm_state"], "left": STATE["arm_left"], "forecast": arm_forecast_text(body().get("lang")) if a != "disarm" else ""})

        @app.route("/api/simhub", methods=["GET", "POST"])
        def api_simhub():                                    # 2.96.4: the tiles of the simulator (start page, simulator centre)
            if request.method == "POST":
                d = body()
                ok, err = sim_hub_do(str(d.get("a") or ""), d.get("v"))
                return reply({"ok": ok, "error": tr_err(err, norm_lang(d.get("lang"))) if err else "", "hub": sim_hub(True)})
            return reply(sim_hub())

        @app.route("/api/whatif", methods=["POST"])
        def api_whatif():                                    # 2.96.5: re-enact a recording in the simulator
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err, txt = whatif(str(d.get("name") or ""))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else "", "text": txt}, 200 if ok else 400)

        @app.route("/kino")
        def kino_page():                                     # 2.96.4: cinema mode (TV / projector)
            return Response(KINO_PAGE, mimetype="text/html")

        @app.route("/api/kino")
        def api_kino():
            return reply(kino_state())

        @app.route("/api/lab", methods=["GET", "POST"])
        def api_lab():                                       # 2.96.6: makeover 12-15 (141_makeover_uebungen)
            if request.method == "GET":
                return reply(dict(lab_state(), ok=True))
            d = body(); lang = norm_lang(d.get("lang")); a = str(d.get("do") or "")
            ok, err, extra = True, "", {}
            if a == "sandbox":
                CFG["notify_sandbox"] = bool(d.get("on")); save_settings()
            elif a == "clear":
                SANDBOX["items"].clear()
            elif a == "chain":
                if not sim_ready():
                    ok, err = False, "only with the simulator"
                else:
                    extra["chain"] = [dict(x, text=tr(x["text"], lang) if x.get("text") else "") for x in alarmchain_test()]
            elif a == "drill":
                ok, err = drill_start(str(d.get("kind") or ""))
            elif a == "train":
                if d.get("start"):
                    ok, err = train_run(True)
                elif d.get("stop"):
                    TRAIN["stop"] = True; TESTOPT["stop"] = True
                if "on" in d:
                    CFG["train_night_on"] = bool(d.get("on")); save_settings()
                if "hour" in d:
                    CFG["train_hour"] = max(0, min(23, int(d.get("hour") or 1))); save_settings()
            elif a == "ab":
                ok, err = ab_run(str(d.get("preset") or ""), "night" if d.get("plan") == "night" else "quick")
            else:
                ok, err = False, "unknown action"
            return reply(dict(lab_state(), ok=ok, error=tr_err(err, lang) if err else "", **extra))

        @app.route("/api/lab/img/<name>")
        def api_lab_img(name):
            if not re.match(r"^\d+\.jpg$", name):
                return reply({"ok": False}, 404)
            p = os.path.join(DATA_DIR, "testinbox", name)
            if not os.path.isfile(p):
                return reply({"ok": False}, 404)
            with open(p, "rb") as f:
                return Response(f.read(), mimetype="image/jpeg")

        @app.route("/api/simstats")
        def api_simstats():                                  # 2.96.7: makeover 18 / 19
            return reply(dict(simdiary_stats(28), ok=True))

        @app.route("/api/demo", methods=["POST"])
        def api_demo():                                      # 2.96.7: makeover 20 - the one-click demo
            d = body(); lang = norm_lang(d.get("lang"))
            if d.get("stop"):
                DEMO_RUN["stop"] = True
                return reply({"ok": True})
            ok, err = demo_start()
            return reply({"ok": ok, "error": tr_err(err, lang) if err else ""}, 200 if ok else 400)

        @app.route("/api/learn", methods=["GET", "POST"])
        def api_learn():                                     # 2.96.8: makeover 21-25 (143_makeover_lernen)
            if request.method == "GET":
                return reply(dict(learn_state(), ok=True))
            d = body(); lang = norm_lang(d.get("lang")); a = str(d.get("do") or "")
            ok, err = True, ""
            if a == "falearn":
                ok, err = falearn_start(str(d.get("name") or ""), str(d.get("cause") or "other"))
            elif a == "blind":
                ok, err = blind_start("map")
            elif a == "rehearsal":
                ok, err = blind_start("rehearsal")
            elif a == "autoth":
                ok, err = autoth_start()
            elif a == "facheck":                         # 2.98.38: «Lernbilder prüfen» (148)
                fa_review()
            elif a == "set" and d.get("key") in ("fa_learn_auto", "rehearsal_on_arm", "weekcheck_on"):
                CFG[d["key"]] = bool(d.get("on")); save_settings()
            else:
                ok, err = False, "unknown action"
            return reply(dict(learn_state(), ok=ok, error=tr_err(err, lang) if err else ""))

        @app.route("/api/tune", methods=["GET", "POST"])
        def api_tune():                                      # 2.98.14: the assistant «Erkennung verbessern» (312)
            if request.method == "GET":
                return reply(tune_assist_state(request.args.get("lang")))
            if getattr(g, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            d = body(); lang = norm_lang(d.get("lang")); a = str(d.get("do") or "")
            fn = {"start": lambda: tune_assist_start(str(d.get("depth") or "quick")), "stop": tune_assist_stop, "undo": tune_assist_undo,
                  "set": lambda: tune_assist_set(str(d.get("key") or ""), bool(d.get("on")))}.get(a)
            ok, err = fn() if fn else (False, "unknown action")
            return reply(dict(tune_assist_state(lang), ok=ok, error=tr_err(err, lang) if err else ""))

        @app.route("/api/simbar")
        def api_simbar():                                    # 2.96.4: the stripe «SIMULATION» on every page
            return reply({"ok": True, "on": bool(CFG.get("sim_on"))})

        @app.route("/api/news", methods=["GET", "POST"])
        def api_news():                                      # 2.96.3: «Neu in dieser Version» after an update
            who = "tk" if request.args.get("who") == "tk" else "web"
            if request.method == "POST":
                d = body()
                if d.get("off"):
                    CFG["news_popup"] = False
                news_seen(who)
            return reply(dict(news_state(who), ok=True))

        @app.route("/api/sim_diary")
        def api_sim_diary():                                 # 2.96.1: the diary of the simulator
            day = str(request.args.get("day") or "")[:10]
            return reply({"ok": True, "items": simdiary_read(day or None, int(request.args.get("days") or 1)), "days": simdiary_days()})

        @app.route("/api/protect", methods=["GET", "POST"])
        def api_protect():
            """2.95.105: the protection level, the assistant, the PIN, «Schutz testen», escalation, presence"""
            if request.method == "GET":
                return reply(dict(protect_status(request.args.get("lang")), ok=True))
            d = body(); a = str(d.get("action") or ""); lang = norm_lang(d.get("lang"))
            ok, err = True, ""
            if a == "level":
                lv = str(d.get("level") or "")
                if lv == "off" and CFG.get("protect_pin"):
                    ok, err = protect_disarm(d.get("pin"), "web")
                else:
                    ok, err = protect_set(lv, "web", d.get("answers") if isinstance(d.get("answers"), dict) else None)
            elif a == "pin":
                ok, err = protect_pin_set(d.get("new"), d.get("old"))
            elif a == "test":
                ok, err = protect_test(lang)
            elif a == "escalate":
                CFG["escalate_on"] = bool(d.get("on", CFG.get("escalate_on")))
                try:
                    CFG["escalate_siren_s"] = max(0, min(600, int(d.get("s", CFG.get("escalate_siren_s", 30)))))
                except (TypeError, ValueError):
                    pass
                save_settings()
            elif a == "presence":
                if "on" in d:
                    CFG["presence_auto"] = bool(d.get("on"))
                if d.get("back") in PRESENCE_BACK_KEYS:           # 2.98.15: when my phone comes back: off / ask / nothing (577)
                    CFG["presence_back"] = d["back"]
                save_settings()
            elif a == "fix_push":
                CFG["notify_on"] = True; sched_user_changed("notify_on"); save_settings()
            else:
                ok, err = False, "unknown action"
            return reply(dict(protect_status(lang, True), ok=ok, error=tr(err, lang) if err else None), 200 if ok else 400)

        @app.route("/api/hotspot", methods=["POST"])
        def api_hotspot():
            d = body(); lang = norm_lang(d.get("lang"))
            if wifi_backend() != "nm":
                return reply({"ok": False, "error": tr("the own Wi-Fi needs NetworkManager (Raspberry Pi OS Bookworm or newer)", lang)}, 400)
            hotspot_password()
            netauto_pause()
            hotspot_switch_later(bool(d.get("on")))
            return reply({"ok": True, "ssid": CFG["hotspot_ssid"], "password": CFG["hotspot_password"], "address": page_address("10.42.0.1")})

        @app.route("/api/mode", methods=["POST"])
        def api_mode():
            d = body(); lang = norm_lang(d.get("lang"))
            for k, typ in (("mode_fire_until", str), ("mode_fire_min_pct", int), ("mode_gamer_watch", bool), ("mode_fire_hours", float), ("mode_fire_persons", bool)):
                if k in d:
                    try:
                        CFG[k] = typ(d[k])
                    except (TypeError, ValueError):
                        pass
            ok, err = (True, "")
            if "mode" in d:
                ok, err = mode_set(d.get("mode"), "web " + (request.remote_addr or "?"))
            else:
                save_settings()
            return reply({"ok": ok, "error": tr(err, lang) if err else None, "mode": mode_state()}, 200 if ok else 400)

        @app.route("/api/follow", methods=["POST"])           # 2.98.1: one «Folgen» for persons, animals and moving things
        def api_follow():
            follow_set(bool(body().get("on")), "web " + (request.remote_addr or "?"))
            return reply({"ok": True, "on": bool(CFG["track_person"] or CFG["track_motion"])})

        @app.route("/api/turbo", methods=["POST"])
        def api_turbo():
            d = body()
            ok, err = turbo_set(bool(d.get("on")), "web " + (request.remote_addr or "?"))
            return reply({"ok": ok, "turbo": turbo_state()})

        @app.route("/api/camping", methods=["POST"])
        def api_camping():
            d = body()
            hotspot_password()
            ok, err = camping_set(bool(d.get("on")))
            return reply({"ok": ok, "error": err or None, "ssid": CFG["hotspot_ssid"], "password": CFG["hotspot_password"],
                          "address": page_address("10.42.0.1"), "hotspot": wifi_backend() == "nm"})

        @app.route("/api/autostart", methods=["GET", "POST"])
        def api_autostart():
            if request.method == "GET":
                return reply(autostart_refresh())
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = autostart_set(bool(d.get("on")))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "autostart": STATE["autostart"]}, 200 if ok else 400)

        @app.route("/api/password", methods=["POST"])
        def api_password():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = web_pw_set(d.get("password") if d.get("action") != "remove" else "")
            if ok:
                STATE["web_open"] = not web_pw_active() and WEB_OPTS["bind"] not in ("127.0.0.1", "localhost", "::1")
                STATE["web_status"] = STATE["web_status"].replace(" · NO PASSWORD", " · password") if web_pw_active() else STATE["web_status"].replace(" · password", " · NO PASSWORD")
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/settings/export")
        def api_settings_export():
            data = dict(settings_data(), app="MoveEye", version=os.path.basename(__file__))
            name = "motionwatch_einstellungen_" + datetime.now().strftime("%Y%m%d_%H%M") + ".json"
            return Response(json.dumps(data, indent=1), mimetype="application/json",
                            headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})

        @app.route("/api/settings/import", methods=["POST"])
        def api_settings_import():
            lang = norm_lang(request.args.get("lang"))
            if (request.content_length or 0) > 4 * 1024 * 1024:
                return reply({"ok": False, "error": "too large"}, 413)
            try:
                data = json.loads(request.get_data(cache=False) or b"null")
            except ValueError:
                data = None
            ok, err = import_settings(data)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/update", methods=["GET", "POST"])
        def api_update():
            lang = norm_lang(request.args.get("lang") or (body().get("lang") if request.method == "POST" else ""))
            ok, err = True, UPD["msg"]
            if request.method == "POST":
                d = body(); a = d.get("action")
                if a == "check":
                    _items, err = update_check()
                    if not err:                              # the "new version" bar on the page shows it right away
                        new = sorted((x for x in _items if x.get("available") and _installable(x) and _vkey(x["version"]) > _vkey(APP_VERSION)), key=lambda x: _vkey(x["version"]))
                        STATE["update_new"] = ({"version": new[-1]["version"], "notes": new[-1].get("notes", "")[:300], "date": new[-1].get("date", "")}
                                               if new else {})
                elif a == "install":
                    if not web_pw_active() and not local_req():
                        return reply({"ok": False, "error": tr("set a web password first - otherwise anybody in the network could install a program", lang)}, 403)
                    ok, err = update_install(str(d.get("version", "")))
                    return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)
                else:
                    return reply({"ok": False, "error": "unknown action"}, 400)
            items = UPD["items"] or update_check()[0]
            return reply({"ok": True, "error": tr_err(err, lang) if err else None, "current": APP_VERSION, "source": CFG["update_url"],
                          "items": items, "newer": [x["version"] for x in items if _vkey(x["version"]) > _vkey(APP_VERSION)],
                          "pending": RESTART["pending"], "checked": datetime.fromtimestamp(UPD["time"]).strftime("%H:%M:%S") if UPD["time"] else "",
                          "list_time": UPD["list_time"], "unsigned_ok": bool(CFG["update_unsigned"])})

        @app.route("/api/light", methods=["POST"])
        def api_light():
            d = body()
            ok, err = light_set(d.get("light"), d.get("mode"))
            return reply({"ok": ok, "error": err or None, "lights": STATE["lights"]}, 200 if ok else 400)

        @app.route("/api/power", methods=["POST"])
        def api_power():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = power_action(d.get("action"), source="web " + (request.remote_addr or "?"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/pause", methods=["POST"])
        def api_pause():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = pause_program(d.get("minutes"), source="web " + (request.remote_addr or "?"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/soundev/upload", methods=["POST"])
        def api_soundev_upload():
            lang = norm_lang(request.args.get("lang"))
            if (request.content_length or 0) > 8 * 1024 * 1024:
                return reply({"ok": False, "error": tr_err("the file is too large (max. 8 MB)", lang)}, 413)
            ok, err, name = sneeze_upload(request.get_data(cache=False))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "name": name}, 200 if ok else 400)

        @app.route("/dev")
        def dev_home():
            if not dev_available():
                return Response("not found", 404)
            return Response(dev_page(), mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/api/dev", methods=["GET", "POST"])
        def api_dev():
            """2.98.7: the developer area - only this device, read-only, behind its own PIN. Admin only."""
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            if getattr(g, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            if not dev_available():
                return reply({"ok": False, "error": "the developer area is switched off"}, 404)
            if request.method == "POST":
                d = body(); a_ = d.get("action"); lang = norm_lang(d.get("lang") or lang)
                if a_ == "setpin":
                    ok_, err_ = dev_pin_set(d.get("pin"), d.get("old") or "")
                    if not ok_:
                        return reply({"ok": False, "error": tr(err_, lang)}, 400)
                elif a_ == "unlock":
                    ok_, err_, tok = dev_unlock(d.get("pin"), "web " + (request.remote_addr or "?"))
                    if not ok_:
                        return reply({"ok": False, "error": tr(err_, lang)}, 400)
                    return reply({"ok": True, "token": tok, "dev": dev_state(lang)})
                elif a_ == "lock":
                    dev_lock()
                else:
                    return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True, "dev": dev_state(lang)})

        @app.route("/api/dev/<what>")
        def api_dev_data(what):
            if getattr(g, "role", "admin") != "admin" or not dev_available():
                return reply({"ok": False, "error": "not allowed"}, 403)
            if not dev_token_ok(request.args.get("token")):
                return reply({"ok": False, "error": "locked"}, 401)
            fns = {"conns": dev_connections, "dns": dev_dns, "ifaces": dev_ifaces}
            fn = fns.get(what)
            if fn is None:
                return reply({"ok": False, "error": "unknown"}, 404)
            return reply({"ok": True, "items": fn(), "dev": dev_state()})

        @app.route("/api/wake", methods=["GET", "POST"])
        def api_wake():
            """2.98.7: wake-up alarm - state, test, snooze, off, direction for the night, good night"""
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang") or lang)
                if getattr(g, "role", "admin") != "admin" and d.get("action") not in ("snooze", "stop"):
                    return reply({"ok": False, "error": "not allowed"}, 403)
                ok, err = wake_action(str(d.get("action") or ""), "web " + (request.remote_addr or "?"))
                if not ok:
                    return reply({"ok": False, "error": tr(err, lang)}, 400)
            return reply({"ok": True, "wake": dict(wake_state(), text=wake_text(lang))})

        @app.route("/api/soundev", methods=["POST"])
        def api_soundev():
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            if a == "install":
                ok, err = sneeze_install()
            elif a == "test_reply":
                SOUNDEV["sneeze_last"] = 0.0
                if not out_selected():
                    ok, err = False, "no loudspeaker selected"
                else:
                    n0 = sneeze_count(); sneeze_reply(); _SNEEZE_DAYS["days"][datetime.now().strftime("%Y-%m-%d")] = n0
                    ok, err = True, ""
            elif a == "test_beep":
                sev_beep(int(d.get("n") or 2)); ok, err = True, ""
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "soundev": soundev_state()}, 200 if ok else 400)

        @app.route("/api/audio", methods=["GET", "POST"])
        def api_audio():
            if request.method == "GET":
                return reply({"state": STATE["audio"], "devices": AUDIO_DEVS, "sounds": own_sounds(), "folder": sounds_dir()})
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            if a == "scan":
                ins, outs = audio_scan()
                ok, err = True, AUDIO_DEVS["err"]
                return reply({"ok": True, "in": len(ins), "out": len(outs), "error": tr_err(err, lang) if err else None})
            if a == "test":
                ok, err = sound_play(d.get("sound") or None, 2.5, None, "test")
            elif a == "siren":
                ok, err = sound_play(None, None, None, reason="by hand (web)")
            elif a == "stop":
                sound_stop(); ok, err = True, ""
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/talk", methods=["POST"])
        def api_talk():
            lang = norm_lang(request.args.get("lang"))
            if (request.content_length or 0) > 96000:
                return reply({"ok": False, "error": "too large"}, 413)
            ok, err = talk_chunk(request.get_data(cache=False), request.remote_addr or "")
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/talk/stop", methods=["POST"])
        def api_talk_stop():
            talk_stop()
            return reply({"ok": True})

        @app.route("/api/tunnel", methods=["GET", "POST"])
        def api_tunnel():
            if request.method == "POST":
                d = body()
                if "on" in d:
                    CFG["tunnel_on"] = bool(d["on"]); save_settings()
                if d.get("new_code"):
                    CFG["tunnel_code"] = ""; tunnel_code()
            return reply({"ok": True, "tunnel": tunnel_state(), "address": page_address() or request.host_url})

        @app.route("/api/disco", methods=["POST"])
        def api_disco():
            d = body()
            disco_set(bool(d.get("on", DISCO["on"])), d.get("mode"), d.get("bpm"), d.get("minutes"), "web " + (request.remote_addr or "?"))
            return reply({"ok": True, "disco": disco_state()})

        @app.route("/api/bt", methods=["GET", "POST"])
        def api_bt():
            if request.method == "GET":
                return reply({"available": bt_available(), "scanning": BT["scanning"], "busy": BT["busy"], "msg": BT["msg"],
                              "devices": BT["devices"], "out": CFG["audio_out"]})
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            if a == "scan":
                ok, err = bt_scan()
            elif a == "connect":
                ok, err = bt_connect(d.get("mac"))
            elif a in ("disconnect", "remove"):
                ok, err = bt_disconnect(d.get("mac"), remove=a == "remove")
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "devices": BT["devices"], "out": CFG["audio_out"]},
                         200 if ok else 400)

        @app.route("/api/audio/live")
        def api_audio_live():
            """Live sound of the microphone: raw 16 bit / 16 kHz mono (the page plays it with WebAudio, works on every phone)."""
            if AUDIO is None or AUDIO.proc is None:
                return reply({"ok": False, "error": "no microphone"}, 404)
            q = AUDIO.listen()

            def gen():
                try:
                    while True:
                        try:
                            yield q.get(timeout=1.0)
                        except queue.Empty:
                            if AUDIO.proc is None and not CFG["audio_in"]:
                                break
                            yield bytes(AUDIO_CHUNK * 2)          # silence keeps the connection (and the timing) alive
                finally:
                    AUDIO.unlisten(q)
            return Response(gen(), mimetype="application/octet-stream",
                            headers={"Cache-Control": "no-store", "X-Audio-Rate": str(AUDIO_RATE), "X-Accel-Buffering": "no"})

        @app.route("/api/gps", methods=["GET", "POST"])
        def api_gps():
            if request.method == "GET":
                return reply({"on": bool(CFG["gps_phone"]), "gps": gps_state(), "map_online": bool(CFG["map_online"]),
                              "lat": float(CFG["latitude"]), "lon": float(CFG["longitude"]),
                              "factory": (round(float(CFG["latitude"]), 2), round(float(CFG["longitude"]), 2)) == GPS_DEFAULT})
            d = body()
            ok, err = gps_set(d.get("lat"), d.get("lon"), d.get("acc"))
            return reply({"ok": ok, "error": err or None}, 200 if ok or err == "off" else 400)

        @app.route("/api/time", methods=["POST"])
        def api_time():
            d = body()
            return reply({"ok": True, "status": sync_time_from_client(d.get("t"), d.get("tz") or "", getattr(g, "role", "admin") == "admin")})

        @app.route("/api/wifi", methods=["GET", "POST"])
        def api_wifi():
            if request.method == "GET":
                return reply(wifi_status())
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            if not web_pw_active() and not local_req():
                return reply({"ok": False, "error": tr("set a web password first (--web-password) - otherwise anybody in the network could change the Wi-Fi", lang)}, 403)
            if a == "scan":
                ok, err = wifi_scan()
            elif a == "connect":
                ok, err = wifi_connect(d.get("ssid"), d.get("password") or "", bool(d.get("preferred", True)))
            elif a == "save":
                ok, err = wifi_save(d.get("ssid"), d.get("password") or "", bool(d.get("preferred", True)))
            elif a == "forget":
                ok, err = wifi_forget(d.get("id"))
            else:
                ok, err = False, "unknown action"
            out = wifi_status(); out.update(ok=ok, error=tr_err(err, lang) if err else None)
            return reply(out, 200 if ok else 400)

        @app.route("/api/ui", methods=["GET", "POST"])
        def api_ui():
            if request.method == "POST":
                d = body()
                if not web_ui_update(d.get("set", {}), d.get("del", [])):
                    return reply({"ok": False, "error": "invalid"}, 400)
                return reply({"ok": True})
            return reply(CFG["web_ui"])

        @app.route("/api/simprofile", methods=["GET", "POST"])
        def api_simprofile():
            """2.95.86: after the simulation - which changed settings to take over (GET: the open question, POST {take: [keys]})"""
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            if request.method == "POST":
                d = body()
                if d.get("ignore") or d.get("reset_ignore"):          # 2.96.10: «never ask again» for some settings
                    simprof_ignore([str(k) for k in (d.get("ignore") or [])][:200], bool(d.get("reset_ignore")))
                    if "take" not in d:
                        return reply({"ok": True, "ignored": len(CFG.get("simprof_ignore") or [])})
                n = simprof_answer([str(k) for k in (d.get("take") or [])][:200])
                return reply({"ok": True, "taken": n})
            return reply({"ok": True, "q": simprof_state(lang)})

        @app.route("/api/alerts")
        def api_alerts():
            """Server-Sent Events: open pages get every alarm at once (also in a background tab)."""
            try:
                last = int(request.headers.get("Last-Event-ID") or 0)
            except ValueError:
                last = 0
            now0 = time.time()
            with ALERTS_COND:
                if last <= 0 or last > ALERTS["seq"]:
                    last = ALERTS["seq"]

            def gen():
                nonlocal last
                yield "retry: 3000\n\n"
                while True:
                    with ALERTS_COND:
                        if ALERTS["seq"] <= last:
                            ALERTS_COND.wait(timeout=15.0)
                        items = [dict(a) for a in ALERTS["items"] if a["seq"] > last]
                    if items:
                        for a in items:
                            last = a["seq"]
                            if time.time() - a["ts"] < 60:     # after a reconnect: nothing older than a minute
                                yield f"id: {a['seq']}\nevent: alert\ndata: {json.dumps(a)}\n\n"
                    else:
                        yield ": ping\n\n"                  # keeps proxies / phones from closing the connection
            return Response(gen(), mimetype="text/event-stream",
                            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})

        @app.route("/api/timelapse")
        def api_timelapse():
            return reply(tl_overview())

        @app.route("/api/timelapse", methods=["POST"])
        def api_timelapse_post():
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            if a == "now":
                watch.timelapse.request_now(); log_event("servo", "Timelapse photo requested (web)")
            elif a == "here":                                  # take the position the camera has right now
                CFG["timelapse_pan"] = round(float(CFG["pan"]), 1); CFG["timelapse_tilt"] = round(float(CFG["tilt"]), 1)
                save_settings(); log_event("servo", f"Timelapse position set to pan {CFG['timelapse_pan']:.0f}% / tilt {CFG['timelapse_tilt']:.0f}%")
            elif a == "goto":                                  # look at the picture of the chosen position
                CFG["pan"], CFG["tilt"] = float(CFG["timelapse_pan"]), float(CFG["timelapse_tilt"])
                MANUAL["until"] = time.time() + max(10.0, CFG["manual_hold"])
            elif a == "render":
                ok, err = timelapse_render(d.get("day", ""), d.get("fps"))
                return reply({"ok": ok, "error": tr(err, lang) if err else None}, 200 if ok else 400)
            elif a == "delete_video":
                p = tl_path(d.get("name"))
                if not p or not TL_VIDEO_RE.match(d.get("name", "")):
                    return reply({"ok": False, "error": "not found"}, 404)
                os.remove(p)
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True})

        @app.route("/timelapse/<name>")
        def timelapse_file(name):
            p = tl_path(name)
            if not p:
                return Response("not found", 404)
            return send_file(p, mimetype="video/mp4" if name.endswith(".mp4") else "image/jpeg", conditional=True,
                             as_attachment=request.args.get("dl") == "1", download_name=name)

        @app.route("/api/action", methods=["POST"])
        def api_action():
            a = body().get("action")
            if a == "wp_add":
                wp_add(); save_settings()
                log_event("patrol", f"Waypoint added at pan {CFG['pan']:.0f}% / tilt {CFG['tilt']:.0f}% (web)  ->  {wp_text()}")
            elif a == "wp_clear":
                WAYPOINTS.clear(); save_settings(); log_event("patrol", "Waypoints cleared (web)")
            elif a == "recalibrate":
                watch.tuner.reset()
            elif a == "reset_counter":
                STATE["detections_total"] = 0; STATE["ignored_vehicles"] = 0
                log_event("person", "Person counter reset (web)")
            elif a == "save_settings":
                save_settings_now()
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": True})

        # ---- video source ----
        @app.route("/api/sources")
        def api_sources():
            return reply(source_info())

        @app.route("/api/sources/scan", methods=["POST"])
        def api_sources_scan():
            scan_sources(STATE["source_id"])               # takes a few seconds; the server is threaded
            return reply(source_info())

        @app.route("/api/source", methods=["POST"])
        def api_source():
            d = body(); a = d.get("action")
            lang = norm_lang(d.get("lang"))
            if a == "select":
                ok, err = source_select(watch, d.get("id"))
            elif a == "add":
                ok, err, sid = source_add(d.get("name"), d.get("url"))
                if ok and d.get("select"):
                    source_select(watch, "url:" + sid)
                if ok:
                    return reply({"ok": True, "error": None, "id": "url:" + sid})
            elif a == "remove":
                ok, err = source_remove(watch, d.get("id"))
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        # ---- schedule ----
        @app.route("/api/schedule")
        def api_schedule_get():
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            with LOCK:
                plans = [dict(x) for x in SCHEDULES]
            return reply({"features": [{"key": k, "label": tr(l, lang)} for k, l in SCHED_FEATURES], "schedules": plans})

        @app.route("/api/schedule", methods=["POST"])
        def api_schedule_post():
            d = body(); a = d.get("action")
            lang = norm_lang(d.get("lang"))
            if a == "add":
                ok, err = schedule_add()
            elif a == "save":
                ok, err = schedule_save(d.get("index"), d.get("schedule"))
            elif a == "remove":
                ok, err = schedule_remove(d.get("index"))
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        # ---- recordings preview ----
        @app.route("/help")
        def help_page():
            return Response(render_page(HELP_PAGE, "help"), mimetype="text/html")

        @app.route("/recordings")
        def recordings_page():
            return Response(render_page(REC_PAGE, "rec"), mimetype="text/html")

        @app.route("/api/recordings")
        def api_recordings():
            return reply(list_recordings(request.args, watch))

        @app.route("/api/ui_simple", methods=["GET", "POST"])
        def api_ui_simple():
            pg = str(request.args.get("page") or "")[:20]
            if request.method == "POST":
                d = body(); pg = str(d.get("page") or pg)[:20]
                if pg and re.fullmatch(r"[a-z]{2,20}", pg):     # 586: Simple / Expert of ONE page (the default stays)
                    m_ = page_modes(); m_[pg] = "simple" if d.get("on") else "expert"
                    if (m_[pg] == "simple") == bool(CFG["ui_simple"]):
                        m_.pop(pg)
                    web_ui_update({"mw-page-mode": json.dumps(m_)})
                else:
                    CFG["ui_simple"] = bool(d.get("on")); save_settings()      # the default (the Pi window follows by itself)
            return reply({"on": page_simple(pg) if pg else bool(CFG["ui_simple"]), "default": bool(CFG["ui_simple"]), "own": pg in page_modes()})

        @app.route("/api/night", methods=["POST"])
        def api_night():
            return reply(night_guard(body().get("lang")))

        @app.route("/api/ai_model", methods=["GET", "POST"])
        def api_ai_model():
            if request.method == "POST":
                ok, err = ai_model_download()
                return reply({"ok": ok, "error": err or None, **AI_MODEL}, 200 if ok else 409)
            return reply(dict(AI_MODEL, present=bool(ai_model_paths()[0])))

        @app.route("/api/own_model", methods=["GET", "POST"])
        def api_own_model():                             # part 195: own MoveEye model (YOLO, ONNX) from the GitHub release
            lg = request.args.get("lang") or body().get("lang") if request.method == "POST" else request.args.get("lang")
            if request.method == "POST":                 # part 196: with a model already there only a new one that is not worse
                ok, err = own_ai_download(only_better=bool(own_ai_paths()[0]) and not body().get("force"))
                return reply({"ok": ok, "error": tr_err(err, lg) if err else None, **own_ai_info(lg)}, 200 if ok else 409)
            return reply(dict(own_ai_info(lg), text=own_ai_text(lg)))

        @app.route("/api/storage", methods=["GET", "POST"])
        def api_storage():
            if request.method == "POST":
                d = body()
                ok, err = storage_set(d.get("path", ""), bool(d.get("move", True)))
                return reply({"ok": ok, "error": tr_err(err, norm_lang(d.get("lang"))) if err else None, **storage_info()}, 200 if ok else 400)
            return reply(storage_info())

        @app.route("/api/loop")
        def api_loop():
            return reply(dict(loop_day(request.args.get("day") or datetime.now().strftime("%Y-%m-%d")), on=bool(CFG["loop_on"])))

        @app.route("/api/health")
        def api_health():
            return reply(health_check(request.args.get("lang")))

        @app.route("/api/places", methods=["POST"])
        def api_places():
            d = body()
            ok = place_rename(d.get("id"), d.get("name"))
            return reply({"ok": ok}, 200 if ok else 400)

        @app.route("/rec/thumb/<path:name>")
        def rec_thumb_route(name):
            p = rec_thumb(name)
            if not p:
                return Response("no thumbnail", 404)
            return send_file(p, mimetype="image/jpeg", max_age=3600)

        @app.route("/rec/file/<path:name>")
        def rec_file(name):
            p = rec_path(name)
            ext = os.path.splitext(name)[1].lower()
            if not p or ext not in REC_EXTS:
                return Response("not found", 404)
            return send_file(p, mimetype="video/mp4" if ext == ".mp4" else "image/jpeg", conditional=True,
                             as_attachment=request.args.get("dl") == "1", download_name=name)

        @app.route("/rec/report/<path:name>")
        def rec_report(name):
            lang = norm_lang(request.args.get("lang"))
            if rec_path(name) is None or os.path.splitext(name)[1].lower() not in REC_EXTS:
                return Response("not found", 404)
            if _is_live(name, self.watch if hasattr(self, "watch") else WATCH_REF.get("w")):
                return Response("the recording is still being written - try again in a few minutes", 409)
            try:
                pdf = rec_report_pdf(name, lang)
            except Exception as e:
                log_event("web", f"Report failed: {e}"[:160]); return Response("report failed", 500)
            fn = "MotionWatch_" + os.path.splitext(os.path.basename(name))[0] + ".pdf"
            log_event("web", f"Event report (PDF) created: {name}")
            return Response(pdf, mimetype="application/pdf", headers={"Content-Disposition": f'inline; filename="{fn}"'})

        @app.route("/rec/play/<path:name>")
        def rec_play(name):
            if rec_path(name) is None or not name.lower().endswith(".mp4") or not os.path.isfile(_cache_path(name)):
                return Response("not converted yet", 404)
            return send_file(_cache_path(name), mimetype="video/mp4", conditional=True)

        @app.route("/api/rec/prepare", methods=["POST"])
        def api_rec_prepare():
            return reply(rec_play_state(body().get("name"), watch))

        @app.route("/api/rec/delete", methods=["POST"])
        def api_rec_delete():
            return reply({"ok": True, "deleted": rec_delete(body().get("names"), watch)})

        # ---- more cameras ----
        @app.route("/api/cams")
        def api_cams():
            return reply({"cams": cams_status(), "sources": source_info()})

        @app.route("/api/cams", methods=["POST"])
        def api_cams_post():
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            if a == "add":
                ok, err = cams_add(d.get("id"))
            elif a == "remove":
                ok, err = cams_remove(d.get("id"))
            else:
                ok, err = False, "unknown action"
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/cam_feed/<int:n>")
        def cam_feed(n):
            cam = next((c for c in CAMS if c.idx == n), None)
            if cam is None:
                return Response("unknown camera", 404)

            def gen():
                last = -1
                cam.viewers += 1
                try:
                    while not cam.stop:
                        jpg, seq = cam.jpeg, cam.seq
                        if jpg and seq != last:
                            last = seq
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                        else:
                            time.sleep(0.03)
                finally:
                    cam.viewers = max(0, cam.viewers - 1)
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

        # ---- zones ----
        # ---- app icon (home screen) ----
        @app.route("/manifest.webmanifest")
        def manifest():
            return Response(app_manifest(), mimetype="application/manifest+json")

        @app.route("/i18n/<lang>.js")
        def i18n_file(lang):
            if lang not in ("fr", "it", "rm"):
                return Response("", 404)
            return Response(i18n_js(lang, request.args.get("h") == "1"), mimetype="application/javascript",
                            headers={"Cache-Control": "public, max-age=604800"})

        @app.route("/icon-192.png")
        @app.route("/favicon.ico")
        def icon192():
            return Response(app_icon_png(192, host_variant()), mimetype="image/png", headers={"Cache-Control": "no-cache"})

        @app.route("/icon-512.png")
        def icon512():
            return Response(app_icon_png(512, host_variant()), mimetype="image/png", headers={"Cache-Control": "no-cache"})

        @app.route("/app-icon/anim.svg")
        def app_icon_anim():
            ic = request.args.get("i") or app_icon_id()
            if ic not in APP_ICONS_ANIM:
                return Response("", 404)
            return Response(APP_ICONS_ANIM[ic], mimetype="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})

        @app.route("/app-icon/<ic>.png")
        def app_icon_preview(ic):                        # the choice in the settings (2.95.23)
            if ic not in dict(APP_ICON_LIST):
                return Response("", 404)
            return Response(app_icon_png(int(request.args.get("s", 96)) if request.args.get("s", "96").isdigit() and 16 <= int(request.args.get("s", 96)) <= 512 else 96, "", ic),
                            mimetype="image/png", headers={"Cache-Control": "public, max-age=86400"})

        @app.route("/sim-icon/<k>.png")
        def sim_icon(k):
            if k not in SIM_ICONS_PNG:
                return Response("", 404)
            import base64
            return Response(base64.b64decode("".join(SIM_ICONS_PNG[k])), mimetype="image/png", headers={"Cache-Control": "public, max-age=86400"})

        @app.route("/api/appicon", methods=["GET", "POST"])
        def api_appicon():
            if request.method == "POST":
                if getattr(g, "role", "admin") != "admin":
                    return reply({"ok": False, "error": "not allowed"}, 403)
                ic = str(body().get("icon") or app_icon_id())
                if ic not in dict(APP_ICON_LIST):
                    return reply({"ok": False, "error": "unknown icon"}, 400)
                d_ = body()
                if "anim" in d_:
                    CFG["app_icon_anim"] = bool(d_.get("anim")); save_settings()
                else:
                    CFG["app_icon"] = ic; save_settings()
                    log_event("sys", f"App icon: {ic}")
            return reply({"ok": True, "icon": app_icon_id(), "anim": bool(CFG.get("app_icon_anim", True)), "animated": list(APP_ICONS_ANIM),
                          "list": [{"id": k, "name": n} for k, n in APP_ICON_LIST]})

        @app.route("/apple-touch-icon.png")
        @app.route("/apple-touch-icon-precomposed.png")
        def icon180():
            return Response(app_icon_png(180, host_variant()), mimetype="image/png", headers={"Cache-Control": "no-cache"})

        @app.route("/sim")
        def sim_page():
            return Response(render_page(SIM_PAGE, "sim"), mimetype="text/html")

        # ---- tools page ----
        @app.route("/tools")
        def tools_page():
            return Response(render_page(TOOLS_PAGE, "tools"), mimetype="text/html")

        @app.route("/party")
        def party_admin_page():
            """own tab «Game corner» (2.95.31): the tools page showing only the game corner"""
            pg = TOOLS_PAGE.replace('<main class="tools">', '<main class="tools solo">', 1).replace("<head>", "<head><script>window.MW_SOLO='party';</script>", 1)
            return Response(render_page(pg, "party"), mimetype="text/html")

        @app.route("/api/tools", methods=["GET", "POST"])
        def api_tools():
            if request.method == "GET":
                return reply(tools_state())
            d = body(); a = d.get("action"); lang = norm_lang(d.get("lang"))
            jobs = {"net": net_scan, "wifi": wifi_survey, "speed": speed_test, "sec": security_check, "bt": tracker_scan, "sd": sd_test}
            if a in jobs:
                if TOOLS[a].get("running"):
                    return reply({"ok": False, "error": tr_err("already running", lang)}, 409)
                if a == "sec":
                    TOOLS["sec"]["running"] = True
                    def _sec():
                        try:
                            security_check()
                        finally:
                            TOOLS["sec"]["running"] = False
                    threading.Thread(target=_sec, daemon=True, name="tool-sec").start()
                else:
                    threading.Thread(target=jobs[a], daemon=True, name="tool-" + a).start()
                log_event("web", f"Tool started: {a} ({request.remote_addr or '?'})")
                return reply({"ok": True})
            if a == "servo":
                ok = servo_test()
                return reply({"ok": ok, "error": None if ok else tr_err("not possible now", lang)}, 200 if ok else 409)
            if a == "known":
                ok = net_known_set(d.get("mac"), d.get("name"))
                return reply({"ok": ok, "error": None if ok else tr_err("bad address", lang)}, 200 if ok else 400)
            if a == "dual":
                ok, err = dual_set(d.get("key"), d.get("value"))
                return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)
            if a == "noinet":
                ok, err = noinet_set(d.get("mac"), bool(d.get("value")))
                for d_ in TOOLS["net"]["devices"]:
                    d_["noinet"] = d_["mac"] in (CFG.get("net_noinet") or [])
                return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)
            if a == "adapters":
                dual_roles()
                return reply({"ok": True})
            if a == "toolmode":
                ok, err = toolmode_set(d.get("minutes"), "web " + (request.remote_addr or "?"))
                return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "toolmode": toolmode_state()}, 200 if ok else 400)
            if a == "cfg":
                ok, err = tools_cfg(d.get("key"), d.get("value"), d.get("mac"))
                return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)
            return reply({"ok": False, "error": tr_err("unknown action", lang)}, 400)

        @app.route("/api/tools/live")
        def api_tools_live():
            f = focus_value() if request.args.get("focus") == "1" else None
            a_ = STATE.get("audio") or {}
            return reply({"focus": f, "audio": {"level": a_.get("level"), "dev": a_.get("dev"), "status": a_.get("status")}})

        @app.route("/tools/diag.zip")
        def tools_diag():
            log_event("web", f"Diagnosis package downloaded ({request.remote_addr or '?'})")
            return Response(diag_zip(), mimetype="application/zip",
                            headers={"Content-Disposition": f'attachment; filename="motionwatch_diagnose_{datetime.now():%Y%m%d_%H%M}.zip"'})

        # ---- animal diary + night report ----
        @app.route("/diary")
        def diary_page():
            return Response(render_page(DIARY_PAGE, "diary"), mimetype="text/html")

        @app.route("/api/diary")
        def api_diary():
            lang = norm_lang(request.args.get("lang"))
            return reply(diary_items(str(request.args.get("label") or "")[:30], lang, request.args.get("fav") == "1"))

        @app.route("/api/diary", methods=["POST"])
        def api_diary_post():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = diary_action(d.get("action"), str(d.get("id") or ""), d.get("value"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/day")
        def api_day():
            lang = norm_lang(request.args.get("lang"))
            day = str(request.args.get("d") or datetime.now().strftime("%Y-%m-%d"))[:10]
            if request.args.get("refresh") == "1" and CFG["weather_on"] and not DEMO["on"]:
                weather_fetch()
            r = day_summary(day, lang)
            return reply(r if r else {"error": "invalid date"}, 200 if r else 400)

        @app.route("/diary/img/<name>")
        def diary_img(name):
            if not _DIARY_NAME.match(name or ""):
                return Response("not found", 404)
            path = diary_thumb(name) if request.args.get("thumb") else os.path.join(diary_dir(), name)
            try:
                with open(path or "", "rb") as f:
                    data = f.read()
            except OSError:
                return Response("not found", 404)
            if request.args.get("share"):
                data = share_jpg(data, str(request.args.get("cap") or "")[:60])
                return Response(data, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
            return Response(data, mimetype="image/jpeg", headers={"Cache-Control": "max-age=3600"})

        @app.route("/rec/share/<path:name>")
        def rec_share(name):
            p = rec_path(name)
            ext = os.path.splitext(name)[1].lower()
            if not p or ext not in REC_EXTS:
                return Response("not found", 404)
            cap = str(request.args.get("cap") or "")[:60]
            if ext != ".mp4":
                with open(p, "rb") as f:
                    data = f.read()
                return Response(share_jpg(data, cap), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
            out, err = share_video(p, cap)
            if not out:
                return Response(err or "error", 500)
            return send_file(out, mimetype="video/mp4", conditional=True)

        @app.route("/api/report")
        def api_report():
            lang = norm_lang(request.args.get("lang"))
            start, end = report_window()
            return reply({"on": bool(CFG["report_on"]), "last": STATE.get("report_last") or {},
                          "preview": report_build(lang, start, end), "partial": (datetime.now() - end).total_seconds() < 5})

        @app.route("/api/report/send", methods=["POST"])
        def api_report_send():
            r, ok = report_send(watch, manual=True)
            return reply({"ok": ok, "text": r["text"]})

        # ---- guest access ----
        @app.route("/api/guest")
        def api_guest():
            return reply(guest_info())

        @app.route("/api/guest", methods=["POST"])
        def api_guest_post():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = guest_set(d.get("action"), d.get("hours", 24))
            return reply(dict(guest_info(), ok=ok, error=tr_err(err, lang) if err else None), 200 if ok else 400)

        @app.route("/g/<token>")
        def guest_page(token):
            if not guest_ok(token):
                return sx_err(404, "guest")
            keep = COMMON_JS[COMMON_JS.index("function keepStream"):COMMON_JS.index("\nconst post")]
            gt = {L: {k: TRX[L][k] for k in GUEST_KEYS if TRX[L].get(k)} for L in ("fr", "it", "rm")}
            return Response(GUEST_PAGE.replace("__BASE__", "/g/" + token).replace("/*KEEP*/", keep).replace("/*GT*/{}", json.dumps(gt, ensure_ascii=False)),
                            mimetype="text/html")

        @app.route("/g/<token>/state")
        def guest_state(token):
            if not guest_ok(token):
                return reply({"ok": False}, 404)
            return reply({"armed": is_armed(), "persons": STATE["persons"], "until": CFG["guest_until"] or 0})

        @app.route("/g/<token>/video")
        def guest_video(token):
            if not guest_ok(token):
                return Response("not found", 404)
            def gen():
                last, chk = -1, time.time()
                watch.web_viewers += 1; STATE["web_viewers"] = watch.web_viewers; GUESTS["streams"] += 1
                try:
                    while True:
                        if time.time() - chk > 2.0:
                            chk = time.time()
                            if not guest_ok(token):
                                break                       # guest access ended or expired: stop the picture
                        jpg, seq = watch.jpeg, watch.jpeg_seq
                        if jpg and seq != last:
                            last = seq
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode()
                                   + b"\r\n\r\n" + jpg + b"\r\n")
                        else:
                            time.sleep(0.03)
                finally:
                    watch.web_viewers = max(0, watch.web_viewers - 1); STATE["web_viewers"] = watch.web_viewers
                    GUESTS["streams"] = max(0, GUESTS["streams"] - 1)
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

        # ---- battery ----
        @app.route("/api/battery", methods=["POST"])
        def api_battery():
            ok, err = battery_full()
            return reply({"ok": ok})

        @app.route("/api/walktest", methods=["GET", "POST"])
        def api_walktest():                                  # 2.98.13: walk test and battery saver (415, 105)
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang"))
                act = str(d.get("action") or "")
                if act == "start":
                    ok, err = walktest_start("web")
                elif act == "stop":
                    ok, err = walktest_stop("button"), ""
                else:
                    ok, err = False, "unknown action"
                return reply(dict(walktest_state(lang), ok=ok, error=tr_err(err, lang) if err else None), 200 if (ok or act == "stop") else 400)
            return reply(dict(walktest_state(norm_lang(request.args.get("lang") or CFG["lang"])), ok=True))

        @app.route("/api/kopf", methods=["GET", "POST"])
        def api_kopf():                                      # 2.98.30: automatic head movement (162)
            lang = norm_lang(request.args.get("lang") or CFG["lang"])
            if request.method == "POST":
                d = body(); lang = norm_lang(d.get("lang") or lang)
                act = str(d.get("do") or "")
                if act == "glance":
                    ok, err = kopf_glance_now()
                elif act == "ov_calib":
                    try:
                        x = None if d.get("x") is None else max(0.0, min(1.0, float(d.get("x"))))
                    except (TypeError, ValueError):
                        x = None
                    ok, err = kopf_ov_calibrate(x, "web")
                elif act == "cont_mid":
                    CFG["cont_set_mid"] = True; ok, err = True, ""
                else:
                    ok, err = False, "unknown action"
                return reply(dict(kopf_state(lang), ok=ok, error=tr_err(err, lang) if err else None), 200 if ok else 400)
            return reply(dict(kopf_state(lang), text=kopf_text(lang), ok=True))

        @app.route("/api/walktest.jpg")
        def api_walktest_jpg():
            p = walktest_img()
            if not p:
                return Response("not found", status=404)
            return send_file(p, mimetype="image/jpeg", max_age=0)

        @app.route("/api/zones")
        def api_zones_get():
            sleep_update()                                   # 2.98.7: the sleeping places for the direction the camera has now
            return reply({"zones": [{k: v for k, v in z.items() if k != "_at"} for z in ZONES]})

        @app.route("/api/zones", methods=["POST"])
        def api_zones_post():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = zones_set(d.get("zones"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/frame.jpg")
        def api_frame():
            if time.time() > watch.raw_until:
                watch.frame_raw = None
            watch.raw_until = time.time() + 15
            for _ in range(25):
                if watch.frame_raw is not None:
                    break
                time.sleep(0.1)
            f = watch.frame_raw
            if f is None:
                return Response("no frame yet", 503)
            ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

        # ---- text settings, test notification ----
        @app.route("/api/text", methods=["POST"])
        def api_text():
            d = body(); lang = norm_lang(d.get("lang"))
            ok, err = set_text(d.get("key"), d.get("value"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/sw.js")
        def service_worker():
            return Response(SW_JS, mimetype="application/javascript", headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})

        @app.route("/api/webpush", methods=["GET", "POST"])
        def api_webpush():
            if request.method == "GET":
                sup = webpush_supported()
                return reply({"supported": sup, "on": CFG["webpush_on"], "key": webpush_public() if sup else "", "count": len(webpush_subs()),
                              "devices": [{"label": x.get("label", ""), "added": x.get("added", "")} for x in webpush_subs()],
                              "https_url": tailscale_https_url(), "status": WEBPUSH["status"]})
            d = body(); lang = norm_lang(d.get("lang")); a = d.get("action")
            ok, err = True, ""
            if a == "subscribe":
                if not webpush_supported():
                    ok, err = False, "python3-cryptography is missing (sudo apt install python3-cryptography)"
                else:
                    ok, err = webpush_add(d.get("sub") or {}, d.get("label", ""))
            elif a == "unsubscribe":
                webpush_remove(str((d.get("sub") or {}).get("endpoint") or d.get("endpoint") or ""))
            elif a == "test":
                de = lang == "de"
                n = webpush_all("MoveEye: Test", tr("Web push works ✓", lang), "/", tag="mw-test")
                ok, err = n > 0, ("" if n else "no device reached")
            elif a == "https":
                if not local_req() and not web_pw_active():
                    return reply({"ok": False, "error": tr_err("set a web password first", lang)}, 403)
                ok, err = tailscale_https(bool(d.get("on", True)))
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "https_url": tailscale_https_url() if a == "https" else None},
                         200 if ok else 400)

        @app.route("/api/backup", methods=["POST"])
        def api_backup():
            d = body(); lang = norm_lang(d.get("lang"))
            if d.get("action") != "test":
                return reply({"ok": False, "error": "unknown action"}, 400)
            ok, err = backup_copy("", None, test=True)
            STATE["backup_status"] = ("✓ test " + datetime.now().strftime("%H:%M")) if ok else ("⚠ " + err)[:200]
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/fleet_state")
        def api_fleet_state():
            return reply(fleet_hello())

        @app.route("/api/fleet", methods=["GET", "POST"])
        def api_fleet():
            FLEET["seen"] = time.time()
            if request.method == "GET":
                with FLEET["lock"]:
                    out = [{"id": d["id"], "name": d.get("name", ""), "url": d["url"], "has_pw": bool(d.get("pw")),
                            "st": FLEET["state"].get(d["id"], {})} for d in CFG["fleet"]]
                return reply({"devices": out, "me": fleet_hello()})
            d = body(); lang = norm_lang(d.get("lang")); a = d.get("action")
            if a == "add":
                ok, err, id_ = fleet_add(d.get("url"), d.get("name"), d.get("password"))
                return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "id": id_}, 200 if ok else 400)
            if a == "remove":
                CFG["fleet"] = [x for x in CFG["fleet"] if x["id"] != d.get("id")]; save_settings()
                return reply({"ok": True})
            if a == "password":
                for x in CFG["fleet"]:
                    if x["id"] == d.get("id"):
                        x["pw"] = str(d.get("password") or "")[:64]; save_settings(); fleet_poll_one(x)
                return reply({"ok": True})
            if a == "scan":
                return reply({"ok": True, "found": fleet_scan()})
            if a in ("arm", "disarm"):
                ids = [x["id"] for x in CFG["fleet"]] if d.get("id") == "all" else [d.get("id")]
                res = {}
                if d.get("id") == "all" or d.get("id") == "me":
                    (arm() if a == "arm" else disarm()); res["me"] = True
                for x in CFG["fleet"]:
                    if x["id"] in ids:
                        try:
                            _fleet_req(x, "/api/arm", {"action": a}); res[x["id"]] = True; fleet_poll_one(x)
                        except Exception:
                            res[x["id"]] = False
                return reply({"ok": all(res.values()) if res else False, "result": res})
            return reply({"ok": False, "error": "unknown action"}, 400)

        @app.route("/fleet/snap/<dev_id>")
        def fleet_snap_route(dev_id):
            data = fleet_snap(str(dev_id)[:16])
            if not data:
                return Response("no picture", 404)
            return Response(data, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

        @app.route("/api/sms", methods=["POST"])
        def api_sms():
            d = body(); lang = norm_lang(d.get("lang"))
            if d.get("action") != "test":
                return reply({"ok": False, "error": "unknown action"}, 400)
            de = CFG["lang"] == "de"
            ok, err = sms_send(f"{CFG['device_name'] or 'MoveEye'}: " + tr("test SMS - it works"), force=True)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/api/qr")
        def api_qr():
            txt = str(request.args.get("t") or "")[:600]
            try:
                svg = qr_svg(txt or " ")
            except ValueError:
                return Response("too long", 400)
            return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "no-store"})

        @app.route("/api/setup", methods=["GET", "POST"])
        def api_setup():
            if request.method == "GET":
                hs_pw = CFG["hotspot_password"]
                return reply({"done": CFG["setup_done"], "lang": CFG["lang"], "device_name": CFG["device_name"], "has_pw": web_pw_active(),
                              "pw_cmdline": bool(CFG["web_password"]), "notify_type": CFG["notify_type"], "notify_url": CFG["notify_url"],
                              "addresses": setup_addresses(), "hotspot": {"on": CFG["hotspot_on"], "ssid": CFG["hotspot_ssid"], "has_pw": bool(hs_pw)},
                              "locked": CFG["lock_on"], "use_case": CFG.get("use_case") or "",
                              "guide": g2_state(request.args.get("lang") or CFG["lang"]), "lat": CFG["latitude"], "lon": CFG["longitude"],
                              "time": datetime.now().strftime("%d.%m.%Y %H:%M")})
            d = body(); lang = norm_lang(d.get("lang")); step = d.get("step")
            ok, err = True, ""
            if step == "basics":
                if d.get("ui_lang") in LANGS:
                    CFG["lang"] = d["ui_lang"]
                ok, err = set_text("device_name", str(d.get("device_name") or "")[:40])
            elif step == "push":
                url = str(d.get("url") or "").strip()
                if url:
                    ok, err = set_text("notify_url", url)
                    if ok:
                        ok, err = set_text("notify_type", "ntfy")
                        CFG["notify_on"] = True
            elif step == "finish":
                pw = str(d.get("password") or "")
                if pw:
                    ok, err = web_pw_set(pw)
                if ok:
                    CFG["setup_done"] = True; save_settings_now()
                    log_event("sys", "Setup assistant finished" + (" (with web password)" if web_pw_active() else " (without web password)"))
            elif step == "usecase":                      # 2.98.9: «What is MoveEye for?»
                ok, err = use_case_set(str(d.get("use") or ""), "setup assistant")
            elif step == "skip":
                CFG["setup_done"] = True; save_settings_now()
            elif step == "again":
                CFG["setup_done"] = False; save_settings()
            elif step == "guide":                        # 586: the one guide (quick / thorough, resumable)
                ok, err = g2_action(d, "web")
            else:
                return reply({"ok": False, "error": "unknown step"}, 400)
            if ok and step == "basics":
                save_settings()
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)

        @app.route("/quick")
        def quick_page():
            return Response(quick_guide_html(request.args.get("lang") or CFG["lang"]), mimetype="text/html")

        @app.route("/setup-card")
        def setup_card():
            L = norm_lang(request.args.get("lang") or CFG["lang"])
            T = (lambda d_, e_: tr(e_, L))
            name = html_escape(CFG["device_name"] or "MoveEye")
            cards = []
            if CFG["hotspot_on"] and CFG["hotspot_password"]:
                cards.append((T("1 · Mit dem WLAN des Geräts verbinden", "1 · Join the device's Wi-Fi"),
                              qr_svg(wifi_qr_text(CFG["hotspot_ssid"], CFG["hotspot_password"])),
                              T("WLAN", "Wi-Fi") + f": <b>{html_escape(CFG['hotspot_ssid'])}</b>"))
                cards.append((T("2 · Seite öffnen (eigenes WLAN)", "2 · Open the page (own Wi-Fi)"), qr_svg(page_address("10.42.0.1")),
                              html_escape(page_address("10.42.0.1"))))
            for a in setup_addresses():
                if a["kind"] == "hotspot":
                    continue
                t_ = {"lan": T("Seite öffnen (Heimnetz)", "Open the page (home network)"),
                      "tailscale": T("Von unterwegs (Tailscale)", "On the road (Tailscale)")}[a["kind"]]
                cards.append((t_, qr_svg(a["url"]), html_escape(a["url"])))
            items = "".join(f'<div class="c"><h3>{h}</h3>{svg}<p>{txt}</p></div>' for h, svg, txt in cards)
            steps = T("<li>QR-Code mit der Handy-Kamera scannen.</li><li>Seite öffnen, beim ersten Mal führt der Einrichtungs-Assistent durch Passwort und Push-Nachrichten.</li>"
                      "<li>Teilen → «Zum Home-Bildschirm»: MoveEye wie eine App starten.</li><li>Schutz Schutz einschalten: grosse Taste «Schutz» oben.</li>",
                      "<li>Scan the QR code with the phone camera.</li><li>Open the page; the first time the setup assistant guides you through password and push messages.</li>"
                      "<li>Share → «Add to Home Screen»: start MoveEye like an app.</li><li>Arm the protection: big «Armed» button at the top.</li>")
            page = (f'<!doctype html><html lang="{L}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                    f'<title>{name} – {T("Kurzanleitung", "Quick start")}</title><style>body{{font:15px/1.45 system-ui,sans-serif;color:#111;background:#fff;margin:0;padding:24px;max-width:780px;margin:auto}}'
                    'h1{font-size:22px;margin:0 0 4px}.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;margin:18px 0}'
                    '.c{border:2px solid #e8590c;border-radius:14px;padding:12px;text-align:center}.c h3{margin:0 0 8px;font-size:15px}.c svg{width:170px;height:170px}'
                    '.c p{margin:6px 0 0;font-size:12px;word-break:break-all}ol{padding-left:20px}.np{margin-top:16px}@media print{.np{display:none}body{padding:0}}'
                    '</style></head><body>'
                    f'<h1>📷 {name}</h1><div>{T("Kurzanleitung – zum Ausdrucken und ins Gehäuse legen", "Quick start – print it and keep it with the device")}</div>'
                    f'<div class="g">{items or "<p>" + T("Keine Adresse gefunden (Netzwerk?)", "No address found (network?)") + "</p>"}</div><ol>{steps}</ol>'
                    f'<p style="font-size:12px;color:#555">{T("Achtung: der WLAN-Code enthält das Passwort – Karte nicht öffentlich aushängen.", "Note: the Wi-Fi code contains the password – do not post the card in public.")}</p>'
                    f'<button class="np" onclick="print()">🖨 {T("Drucken", "Print")}</button></body></html>')
            return Response(page, mimetype="text/html", headers={"Cache-Control": "no-store"})

        @app.route("/api/notify_test", methods=["POST"])
        def api_notify_test():
            lang = norm_lang(body().get("lang"))
            if not Notifier.configured() and not CFG.get("mqtt_on"):
                return reply({"ok": False, "error": tr_err("notification is not configured", lang)}, 400)
            if body().get("all"):
                return reply({"ok": True, "results": watch.notifier.test_all(watch.frame_out)})
            watch.notifier.test(watch.frame_out)
            return reply({"ok": True})

        # ---- recordings: favourites, zip, statistics ----
        @app.route("/api/rec/false", methods=["POST"])
        def api_rec_false():
            d = body()
            return reply({"ok": True, "changed": rec_set_false(d.get("names"), d.get("cause") or "", watch)})

        @app.route("/api/fa", methods=["GET", "POST"])
        def api_fa():
            if request.method == "POST":
                d = body()
                return reply({"ok": fa_apply(d.get("id"), d.get("lang")), "fa": fa_suggestions(d.get("lang"))})
            return reply(fa_suggestions(request.args.get("lang")))

        @app.route("/api/rec/fav", methods=["POST"])
        def api_rec_fav():
            d = body()
            return reply({"ok": True, "changed": rec_set_fav(d.get("names"), bool(d.get("value")), watch)})

        @app.route("/api/recordings/stats")
        def api_rec_stats():
            return reply(rec_stats(request.args.get("days", 14), request.args.get("day")))

        @app.route("/rec/zip", methods=["GET", "POST"])
        def rec_zip_route():
            if request.method == "POST":
                try:
                    names = json.loads(request.form.get("names", "[]"))
                except ValueError:
                    names = []
            else:
                names = [n for n in (request.args.get("names") or "").split(",") if n]
            p = rec_zip(names, watch)
            if not p:
                return Response("nothing to download", 404)
            def gen():                                    # streamed, so the temporary file can be removed afterwards
                try:
                    with open(p, "rb") as f:
                        while True:
                            chunk = f.read(1 << 20)
                            if not chunk:
                                break
                            yield chunk
                finally:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            fname = "motionwatch_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip"
            return Response(gen(), mimetype="application/zip",
                            headers={"Content-Disposition": f'attachment; filename="{fname}"', "Content-Length": str(os.path.getsize(p))})

        import logging; logging.getLogger("werkzeug").setLevel(logging.ERROR)
        ctx = None
        if WEB_OPTS["https"]:
            ctx = ensure_cert()
            if not ctx[0]:
                STATE["web_status"] = "https failed (no certificate; install openssl or pass --cert/--key)"
                log_event("web", "HTTPS requested but no certificate available - web page NOT started"); return
        threading.Thread(target=self._serve, args=(app, ctx), daemon=True, name="web").start()
        self.started = True
        scheme = "https" if ctx else "http"
        if ctx is None and CFG.get("https_extra", True):
            self._start_https_extra(app)
        STATE["web_open"] = not web_pw_active() and WEB_OPTS["bind"] not in ("127.0.0.1", "localhost", "::1")
        self.status_ok = f"on · {scheme} · port {CFG['web_port']}" + (" · password" if web_pw_active() else " · NO PASSWORD")
        if not STATE["web_status"].startswith("port "):
            STATE["web_status"] = self.status_ok
        log_event("web", f"Web control started: {scheme}://<ip>:{CFG['web_port']}/  (raw stream: /video_feed)")
        if STATE["web_open"]:
            log_event("web", "WARNING: the web page has no password and is reachable from the network - use --web-password, --bind 127.0.0.1 or a VPN")
        self.app = app


