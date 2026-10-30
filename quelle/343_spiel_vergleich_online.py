#@ MoveEye – Teil 343: Spiel «Mensch gegen KI» (zwei Runden im 3D-Simulator, Ergebnis) und «Online über das WLAN hinaus»: Einladungslink mit Ablauf, Proxy /game/<token>/ zur Handy-Seite des Spiels (nur das Spiel), Ratenbremse, Spielerzahl, Protokoll. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Daniel 30.10.2026:
#   1. «Mensch gegen KI vergleichen»: the simulator (gamecompare.gd, control «game_compare») plays the same round twice -
#      a person (or the Bot-Wächter) guards, then the real detection of MoveEye. Here: start / state / result for the page
#      Simulator (543) and the window (592), GET / POST /api/game_compare.
#   2. «Online über das WLAN hinaus»: friends at home play along. MoveEye makes an invitation link with an expiry
#      (1-24 h, revocable, at most N players). The link opens /game/<token>/ on MoveEye: MoveEye fetches the phone page of
#      the game from the simulator (its game port, HTTP) and passes its WebSocket on (byte for byte). The simulator may be
#      reached directly or through the tunnel (180: extra doors 18770 / 18771, simulator tunnel.gd 3D-4.x). MoveEye itself
#      is reached from outside through Tailscale (serve / funnel) or the «Address of this page» (public_url).
#      Security: only these 4 addresses below /game/<token>/ are open without login (auth() in 550), every one checks the
#      token (compare_digest), the expiry and the revocation on every request and every 1 s on an open WebSocket; wrong
#      tokens are counted per address (20 in 5 min -> 429), requests per address are limited, the WebSocket gets at most
#      256 KB from the guest in 10 s, every join / leave / refusal is logged. The guest never sees anything else of MoveEye
#      (no camera, no settings): the page and the WebSocket are the ones of the simulator's game.
import select as _gselect

_GINV_CFG = {"game_invites": []}     # [{"id", "tok", "name", "t0", "until", "max", "revoked", "uses"}]
for _k, _v in _GINV_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TUN_LOCAL.update({18770: 8770, 18771: 8771})    # 180: the tunnel also carries the game (page / WebSocket) of the simulator
GINV_HOURS = (1, 3, 6, 12, 24)
GINV_MAX = 8                                    # invitations at the same time
GINV = {"lock": threading.Lock(), "conns": {}, "hits": {}, "bad": {}, "log": deque(maxlen=200), "tgt": None, "tgt_t": 0.0,
        "logged": {}, "rtt": {}}
GINV_HTTP_PER_MIN = 120
GINV_WS_PER_MIN = 30
GINV_IN_10S = 256 * 1024


def ginv_list():
    """the invitations (expired / revoked ones are kept a day for the list, then dropped)"""
    now = time.time()
    lst = [x for x in (CFG.get("game_invites") or []) if isinstance(x, dict) and x.get("tok")]
    keep = [x for x in lst if now - float(x.get("until") or 0) < 86400]
    if len(keep) != len(lst):
        CFG["game_invites"] = keep; save_settings()
    return keep


def ginv_valid(inv):
    return bool(inv) and not inv.get("revoked") and time.time() < float(inv.get("until") or 0)


def ginv_find(tok):
    tok = str(tok or "")
    if not tok or len(tok) > 64:
        return None
    for x in ginv_list():
        if secrets.compare_digest(str(x["tok"]), tok):
            return x
    return None


def ginv_create(hours=3, players=6, name=""):
    hours = min(GINV_HOURS, key=lambda h: abs(h - float(hours or 3)))
    act = [x for x in ginv_list() if ginv_valid(x)]
    if len(act) >= GINV_MAX:
        return None, "too many invitations - revoke an old one first"
    inv = {"id": secrets.token_hex(3), "tok": secrets.token_urlsafe(18), "name": re.sub(r"[^\w .,'!?\-]", "", str(name or ""))[:30],
           "t0": int(time.time()), "until": int(time.time() + hours * 3600), "max": max(1, min(12, int(players or 6))), "revoked": False, "uses": 0}
    CFG["game_invites"] = ginv_list() + [inv]; save_settings()
    log_event("web", f"Game invitation made ({hours} h, at most {inv['max']} players{', ' + inv['name'] if inv['name'] else ''})")
    return inv, ""


def ginv_revoke(iid):
    n = 0
    for x in ginv_list():
        if (iid == "all" or x["id"] == iid) and not x.get("revoked") and time.time() < float(x["until"]):
            x["revoked"] = True; n += 1
    if n:
        save_settings()
        log_event("web", f"Game invitation revoked ({'all' if iid == 'all' else iid})")
    return n


def ginv_base(host_url=""):
    """the address guests use: «Address of this page» (public_url), else https of Tailscale, else the address asked with"""
    pu = str(CFG.get("public_url") or "").strip()
    if pu.startswith(("http://", "https://")):
        return pu.rstrip("/")
    try:
        ts = tailscale_https_url()
    except Exception:
        ts = ""
    if ts:
        return ts.rstrip("/")
    return (host_url or f"http://{local_ip()}:{CFG['web_port']}").rstrip("/")


def ginv_url(inv, base):
    return f"{base}/game/{inv['tok']}/"


def ginv_note(ip, what, inv=None, important=True):
    """the protocol: the list for the page (last 200) and the MoveEye log (a refused address at most once a minute)"""
    e = {"t": int(time.time()), "ip": str(ip)[:45], "what": what, "inv": (inv or {}).get("id", ""), "name": (inv or {}).get("name", "")}
    GINV["log"].append(e)
    k = (ip, what)
    if important and time.time() - GINV["logged"].get(k, 0) > 60:
        GINV["logged"][k] = time.time()
        if len(GINV["logged"]) > 400:
            GINV["logged"].clear()
        log_event("web", f"Game guest {ip}: {what}" + (f" (invitation {e['inv']}{' ' + e['name'] if e['name'] else ''})" if inv else ""))


def ginv_players(inv):
    return int(GINV["conns"].get(inv["id"], 0)) if inv else 0


def ginv_state(host_url=""):
    base = ginv_base(host_url)
    now = time.time()
    out = []
    for x in ginv_list():
        a = ginv_valid(x)
        out.append({"id": x["id"], "name": x.get("name", ""), "url": ginv_url(x, base) if a else "", "until": x["until"], "left_s": max(0, int(x["until"] - now)),
                    "max": x["max"], "players": ginv_players(x), "uses": int(x.get("uses", 0)), "active": a, "revoked": bool(x.get("revoked"))})
    tgt, err = ginv_target()
    return {"ok": True, "invites": out, "log": list(GINV["log"])[-15:][::-1], "base": base, "public": not base.startswith(("http://192.168.", "http://10.", "http://127.", "http://172.")),
            "game_open": tgt is not None, "why": err, "tunnel": bool(tgt and tgt[3]), "hours": list(GINV_HOURS)}


def ginv_target():
    """(host, http port, websocket port, through the tunnel) of the game in the simulator, or (None, reason)"""
    now = time.time()
    if now - GINV["tgt_t"] < 5:
        return GINV["tgt"]
    from urllib.parse import urlparse
    res = (None, "simulator not reachable")
    try:
        r = sim_control(None)
        gm = r.get("game") or {}
        if not gm.get("open"):
            res = (None, "the game is not open in the simulator")
        else:
            tun = str(CFG.get("sim_url") or "").startswith("http://127.0.0.1:18765")
            if tun:
                res = (("127.0.0.1", 18770, 18771, True), "")
            else:
                hp = int(urlparse(str(gm.get("url") or "")).port or 0)
                host = urlparse(sim_base()).hostname or "127.0.0.1"
                res = ((host, hp, hp + 1, False), "") if hp else (None, "the simulator gives no game address")
    except Exception:
        pass
    GINV["tgt"], GINV["tgt_t"] = res, now
    return res


def _ginv_rate(ip, kind, per_min):
    now = time.time()
    with GINV["lock"]:
        lst = [x for x in GINV["hits"].get((ip, kind), []) if now - x < 60]
        lst.append(now)
        GINV["hits"][(ip, kind)] = lst
        if len(GINV["hits"]) > 1000:
            GINV["hits"] = {k: v for k, v in GINV["hits"].items() if v and now - v[-1] < 60}
    return len(lst) <= per_min


def _ginv_bad(ip, add=False):
    """wrong / old tokens per address: 20 in 5 minutes, then the address waits (no guessing)"""
    now = time.time()
    with GINV["lock"]:
        lst = [x for x in GINV["bad"].get(ip, []) if now - x < 300]
        if add:
            lst.append(now)
        GINV["bad"][ip] = lst
    return len(lst) >= 20


GINV_PAGE_JS = r"""<script>/* MoveEye: game for guests (window.__mwExit: no way back into MoveEye) */
(function () {
  var base = location.pathname.replace(/[^\/]*$/, ""), WSU = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + base + "ws";
  var W = window.WebSocket, tq = 0, rtt = [], full = false;
  function Px(u, p) { var w = new W(WSU); var s = w.send.bind(w);
    w.send = function (d) { if (d === '{"t":"frame"}' && !tq) tq = performance.now(); return s(d); };
    w.addEventListener("message", function (e) { if (typeof e.data !== "string" && tq) { rtt.push(performance.now() - tq); if (rtt.length > 12) rtt.shift(); tq = 0; } });
    w.addEventListener("close", function () { tq = 0; });
    return w; }
  Px.prototype = W.prototype; Px.CONNECTING = 0; Px.OPEN = 1; Px.CLOSING = 2; Px.CLOSED = 3; window.WebSocket = Px;
  var bar = null, left = -1, t0 = Date.now();
  function fmt(s) { var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60); return h > 0 ? h + ":" + String(m).padStart(2, "0") + " h" : m + " min"; }
  function paint() { if (!document.body) return; if (!bar) { bar = document.createElement("div"); bar.id = "mwg-bar";
      bar.style.cssText = "position:fixed;left:50%;transform:translateX(-50%);top:calc(env(safe-area-inset-top) + 44px);z-index:60;background:#000a;color:#e6edf3;font:12px system-ui,sans-serif;padding:3px 10px;border-radius:12px;pointer-events:none;white-space:nowrap;max-width:94vw;overflow:hidden;text-overflow:ellipsis";
      document.body.appendChild(bar); }
    var ms = 0; if (rtt.length) { var a = rtt.slice().sort(function (x, y) { return x - y; }); ms = Math.round(a[Math.floor(a.length / 2)]); }
    var l = left < 0 ? -1 : Math.max(0, left - Math.round((Date.now() - t0) / 1000)), t = "🌐 Online";
    if (ms) t += " · 📶 " + ms + " ms" + (ms > 700 ? " langsam – «Bild auf dem Handy: klein» hilft" : (ms > 350 ? " verzögert" : ""));
    if (l >= 0) t += " · ⏳ " + fmt(l);
    if (full) t = "⚠ Die Einladung ist voll – warte, bis jemand aufhört";
    if (l === 0) t = "⏳ Die Einladung ist abgelaufen";
    bar.textContent = t; bar.style.color = ms > 700 || full || l === 0 ? "#ff9f0a" : "#e6edf3"; }
  function info() { fetch(base + "info", {cache: "no-store"}).then(function (r) { return r.json(); }).then(function (j) { left = j.left_s; t0 = Date.now(); full = !!j.full; paint(); })
      .catch(function () { left = 0; paint(); }); }
  info(); setInterval(info, 30000); setInterval(paint, 2000);
})();
</script>"""

GINV_DENY = ("<!doctype html><html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
             "<title>Spiel</title><style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0a0e14;color:#e6edf3;"
             "font:16px system-ui,sans-serif;text-align:center;padding:20px;box-sizing:border-box}</style></head><body><div><h1 style=\"font-size:22px\">__T__</h1>"
             "<p style=\"color:#8b98a8\">__P__</p></div><!-- window.__mwExit --></body></html>")
GINV_TEXTS = {403: ("Diese Einladung gilt nicht (mehr)", "Der Link ist abgelaufen oder wurde zurückgezogen. Frag den Gastgeber nach einer neuen Einladung."),
              429: ("Zu viele Anfragen", "Bitte einen Moment warten und dann neu laden."),
              503: ("Das Spiel ist gerade nicht offen", "Der Gastgeber muss das Spiel im Simulator öffnen. Dann diese Seite neu laden."),
              409: ("Die Einladung ist voll", "Alle Plätze dieser Einladung sind besetzt. Warte, bis jemand aufhört.")}


def ginv_routes(app, reply, body):
    from flask import request, Response, g as g_, redirect
    import http.client

    SEC = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Robots-Tag": "noindex, nofollow", "X-Content-Type-Options": "nosniff",
           "X-Frame-Options": "DENY", "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
           "img-src 'self' data: blob:; media-src 'self' data: blob:; connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"}

    def gip():
        ip = request.remote_addr or "?"
        if ip in ("127.0.0.1", "::1") and request.headers.get("X-Forwarded-For"):
            ip = request.headers["X-Forwarded-For"].split(",")[0].strip()[:45] or ip      # behind Tailscale serve / funnel
        return ip

    def deny(code, extra=None):
        t_, p_ = GINV_TEXTS.get(code, GINV_TEXTS[403])
        h = dict(SEC)
        if code == 429:
            h["Retry-After"] = "60"
        h.update(extra or {})
        return Response(GINV_DENY.replace("__T__", t_).replace("__P__", p_), code, mimetype="text/html", headers=h)

    def check(tok, kind):
        """(invitation, None) or (None, response)"""
        ip = gip()
        if _ginv_bad(ip):
            ginv_note(ip, "blocked (too many wrong links)")
            return None, deny(429)
        if not _ginv_rate(ip, kind, GINV_WS_PER_MIN if kind == "ws" else GINV_HTTP_PER_MIN):
            ginv_note(ip, "too many requests")
            return None, deny(429)
        inv = ginv_find(tok)
        if inv is None or not ginv_valid(inv):
            _ginv_bad(ip, True)
            ginv_note(ip, "refused: " + ("expired or revoked invitation" if inv else "unknown link"), inv)
            return None, deny(403)
        return inv, None

    def nope():
        if getattr(g_, "role", "admin") != "admin" or getattr(g_, "appkey", None):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    def fetch(path):
        tgt, why = ginv_target()
        if tgt is None:
            return None, why
        try:
            con = http.client.HTTPConnection(tgt[0], tgt[1], timeout=6)
            con.request("GET", path, headers={"User-Agent": "MotionWatch", "Host": f"{tgt[0]}:{tgt[1]}"})
            r = con.getresponse()
            data = r.read(3_000_000)
            con.close()
            return (data if r.status == 200 else None), ("" if r.status == 200 else f"simulator {r.status}")
        except (OSError, http.client.HTTPException) as e:
            GINV["tgt_t"] = 0.0
            return None, str(e)[:60]

    @app.route("/game/<tok>")
    def ginv_noslash(tok):
        inv, bad = check(tok, "http")
        return bad if bad is not None else redirect(f"/game/{tok}/", 302)

    @app.route("/game/<tok>/")
    def ginv_page(tok):
        inv, bad = check(tok, "http")
        if bad is not None:
            return bad
        data, why = fetch("/")
        if data is None:
            ginv_note(gip(), "game not reachable: " + why, inv, False)
            return deny(503)
        txt = data.decode("utf-8", "replace").replace('href="/manifest.json"', 'href="manifest.json"')
        i = txt.find("<head>")
        txt = (txt[:i + 6] + GINV_PAGE_JS + txt[i + 6:]) if i >= 0 else GINV_PAGE_JS + txt
        ginv_note(gip(), "opened the game page", inv)
        return Response(txt, mimetype="text/html", headers=SEC)

    @app.route("/game/<tok>/manifest.json")
    def ginv_manifest(tok):
        inv, bad = check(tok, "http")
        if bad is not None:
            return bad
        return Response(json.dumps({"name": "Unentdeckt ans Ziel", "short_name": "Unentdeckt", "start_url": f"/game/{tok}/", "scope": f"/game/{tok}/",
                                    "display": "fullscreen", "orientation": "landscape", "background_color": "#0a0e14", "theme_color": "#0a0e14"}),
                        mimetype="application/manifest+json", headers=SEC)

    @app.route("/game/<tok>/info")
    def ginv_info(tok):
        inv, bad = check(tok, "http")
        if bad is not None:
            return Response(json.dumps({"ok": False, "left_s": 0}), bad.status_code, mimetype="application/json", headers=SEC)
        tgt, _w = ginv_target()
        return Response(json.dumps({"ok": True, "left_s": max(0, int(inv["until"] - time.time())), "players": ginv_players(inv), "max": inv["max"],
                                    "full": ginv_players(inv) >= int(inv["max"]), "open": tgt is not None}), mimetype="application/json", headers=SEC)

    @app.route("/game/<tok>/ws", websocket=True)       # werkzeug: a WebSocket request only matches a websocket rule
    def ginv_ws(tok):
        inv, bad = check(tok, "ws")
        if bad is not None:
            return bad
        ip = gip()
        key = request.headers.get("Sec-WebSocket-Key", "")
        sock = request.environ.get("werkzeug.socket")
        if request.headers.get("Upgrade", "").lower() != "websocket" or not re.match(r"^[A-Za-z0-9+/]{22}==$", key):
            return Response("WebSocket only", 400, headers=SEC)
        if sock is None:
            return Response("not supported", 501, headers=SEC)
        tgt, why = ginv_target()
        if tgt is None:
            return deny(503)
        with GINV["lock"]:
            n = int(GINV["conns"].get(inv["id"], 0))
            if n >= int(inv["max"]):
                full = True
            else:
                full = False
                GINV["conns"][inv["id"]] = n + 1
        if full:
            ginv_note(ip, f"refused: the invitation is full ({inv['max']} players)", inv)
            return deny(409)
        up = None
        t0 = time.time(); nin = 0; nout = 0; why_end = "left"
        try:
            try:
                up = _socket.create_connection((tgt[0], tgt[2]), timeout=6)
                up.sendall((f"GET / HTTP/1.1\r\nHost: {tgt[0]}:{tgt[2]}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
                resp = b""
                while b"\r\n\r\n" not in resp and len(resp) < 8192:
                    ch = up.recv(4096)
                    if not ch:
                        break
                    resp += ch
            except OSError as e:
                GINV["tgt_t"] = 0.0
                ginv_note(ip, "game not reachable: " + str(e)[:60], inv, False)
                return deny(503)
            head_, _s, rest = resp.partition(b"\r\n\r\n")
            m_ = re.search(rb"(?im)^sec-websocket-accept:\s*([A-Za-z0-9+/=]{20,40})\s*$", head_)
            if not head_.startswith(b"HTTP/1.1 101") or not m_:
                ginv_note(ip, "the game refused the connection", inv, False)
                return deny(503)
            inv["uses"] = int(inv.get("uses", 0)) + 1
            ginv_note(ip, "joined the game", inv)
            sock.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + m_.group(1) + b"\r\n\r\n")
            if rest:
                sock.sendall(rest)
            up.settimeout(None)
            sock.settimeout(None)
            win = deque()                                   # (time, bytes) from the guest in the last 10 s
            last_chk = 0.0
            while True:
                now = time.time()
                if now - last_chk > 1.0:                    # expiry / revocation also ends open games
                    last_chk = now
                    cur = ginv_find(tok)
                    if cur is None or not ginv_valid(cur):
                        why_end = "invitation expired or revoked - disconnected"; break
                pend = hasattr(sock, "pending") and sock.pending() > 0
                rd = [sock] if pend else _gselect.select([sock, up], [], [], 1.0)[0]
                if up in rd:
                    d_ = up.recv(65536)
                    if not d_:
                        why_end = "the game closed the connection"; break
                    sock.sendall(d_); nout += len(d_)
                if sock in rd:
                    try:
                        d_ = sock.recv(65536)
                    except (BlockingIOError, InterruptedError):
                        continue
                    except OSError as e:
                        if e.__class__.__name__ == "SSLWantReadError":
                            continue
                        raise
                    if not d_:
                        break
                    win.append((now, len(d_))); nin += len(d_)
                    while win and now - win[0][0] > 10.0:
                        win.popleft()
                    if sum(x[1] for x in win) > GINV_IN_10S:
                        why_end = "too much data from the guest - disconnected"; break
                    up.sendall(d_)
        except OSError:
            pass
        finally:
            with GINV["lock"]:
                GINV["conns"][inv["id"]] = max(0, int(GINV["conns"].get(inv["id"], 1)) - 1)
            for z in (up, sock):
                if z is None:
                    continue
                try:
                    z.shutdown(_socket.SHUT_RDWR)
                except OSError:
                    pass
            if up is not None:
                try:
                    up.close()
                except OSError:
                    pass
        ginv_note(ip, f"{why_end} after {int(time.time() - t0)} s ({nout // 1024} KB to the guest, {nin // 1024} KB from the guest)", inv,
                  why_end != "left")
        return Response("", 200)                            # never reaches the guest: the connection was taken over

    @app.route("/api/game_invite", methods=["GET", "POST"])
    def api_game_invite():
        n_ = nope()
        if n_ is not None:
            return n_
        lang = norm_lang(request.args.get("lang"))
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang)
            a_ = str(d.get("action") or "")
            if a_ == "create":
                inv, err = ginv_create(d.get("hours", 3), d.get("players", 6), d.get("name", ""))
                if inv is None:
                    return reply({"ok": False, "error": tr_err(err, lang)}, 400)
                st = ginv_state(request.host_url)
                st["new"] = ginv_url(inv, st["base"])
                return reply(st)
            if a_ == "revoke":
                ginv_revoke("all" if d.get("all") else str(d.get("id") or ""))
            else:
                return reply({"ok": False, "error": "unknown action"}, 400)
        st = ginv_state(request.host_url)
        st["why"] = tr(st["why"], lang) if st.get("why") else ""
        return reply(st)

    @app.route("/api/game_compare", methods=["GET", "POST"])
    def api_game_compare():
        n_ = nope()
        if n_ is not None and request.method == "POST":
            return n_
        lang = norm_lang(request.args.get("lang"))
        q = {"action": "game_compare", "op": "state"}
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang)
            op = str(d.get("op") or "")
            if op not in ("start", "stop"):
                return reply({"ok": False, "error": "unknown action"}, 400)
            q["op"] = op
            if op == "start":
                q.update(bots=max(0, min(3, int(d.get("bots", 2) or 0))), minutes=max(1, min(15, int(d.get("minutes", 3) or 3))),
                         source="ways" if d.get("source") == "ways" else "rec")
                log_event("sys", f"Game «Human vs AI» started from the web page ({q['bots']} bots, {q['minutes']} min)")
        try:
            r = sim_control(q)
        except Exception:
            return reply({"ok": False, "error": tr_err("simulator not reachable", lang)}, 400)
        if not isinstance(r, dict) or r.get("error") == "unknown action":
            return reply({"ok": False, "error": tr_err("not supported - update the simulator", lang)}, 400)
        return reply(r, 200 if r.get("ok", True) or request.method == "GET" else 400)
