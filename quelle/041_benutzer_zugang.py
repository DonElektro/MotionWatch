#@ MoveEye – Teil 041: Benutzer mit Rechten – Zeitfenster und Ablaufdatum, Handy verknüpfen (QR-Einmal-Link), Push pro Benutzer, Geräte pro Benutzer. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (30.10.2026): feste Personen statt nur Gastlink.
#   * Rollen = Vorlagen von Rechten (040: USER_PERMS / ROLE_PERMS): Kind · Freund · Familie · Nur ansehen · Eigene Rechte.
#     Der Server prüft jedes Recht (role_allows, 040); die Seite blendet aus, was nicht erlaubt ist (users_ui_css unten).
#   * Zeitfenster (z. B. Kind täglich 08–20) und Ablaufdatum (Freund): ausserhalb nur eine freundliche Seite
#     «Zugang gerade nicht aktiv», keine Daten (user_gate, aufgerufen von role_guard in 550). Laufende Bildströme enden.
#   * «Handy verknüpfen»: ein Einmal-Link (/l/<token>, 10 Minuten, nur der Fingerabdruck bleibt im Speicher) als QR-Code.
#     Scannen = dieses Handy ist als dieser Benutzer angemeldet (Vertrauens-Cookie wie nach einem Login, 040), ohne Passwort.
#     Sicherheit wie das Passwort (574): ist «Anmelden nur verschlüsselt» aktiv, zeigt der QR die sichere Seite (https);
#     kommt der Link trotzdem über unverschlüsseltes http von einem anderen Gerät, wird er sofort gesperrt (er könnte
#     mitgelesen worden sein) und ein neuer QR-Code ist nötig. Tailscale und dieses Gerät selbst gelten als sicher.
#     Höchstens 10 Fehlversuche je Adresse in 10 Minuten.
#   * Geräte pro Benutzer: Name/Browser, zuletzt gesehen; «Entfernen» meldet das Gerät sofort ab (auch der Bildstrom).
#   * Push pro Benutzer: Alarme / Infos / Spiel-Einladungen; Web-Push-Abos merken sich den Benutzer, optional ein eigenes
#     ntfy-Thema (steht nur in den Einstellungen des Geräts, nie in Dateien des Projekts). Der Hauptkanal (ntfy) bleibt beim
#     Administrator. Ausserhalb des Zeitfensters bekommt ein Benutzer keine Nachrichten.
# Übersetzungen: Teil 623. Web: Teil 547 (Karte «Benutzer» in Einstellungen → Sicherheit), Fenster: 573.
# ----------------------------------------------------------------------------
USER_LINK = {"links": {}, "fails": {}}               # sha256(token) -> {"user", "exp", "by"}; ip -> [times of wrong links]
USER_LINK_TTL = 600


def _ul_hash(tok):
    import hashlib
    return hashlib.sha256(("mw-link|" + str(tok)).encode()).hexdigest()


def user_active(u, now=None):
    """(True, "") or (False, why) - why = "until" (expired) or "window" (outside the time window)"""
    if not isinstance(u, dict):
        return False, "gone"
    now = now or datetime.now()
    if u.get("until") and now.strftime("%Y-%m-%d") > u["until"]:
        return False, "until"
    w = u.get("win")
    if w:
        hm, wd, days = now.strftime("%H:%M"), now.weekday(), w.get("days") or list(range(7))
        a, b = w["from"], w["to"]
        if a == b:
            inside = wd in days
        elif a < b:
            inside = wd in days and a <= hm < b
        else:                                               # over midnight, e.g. 18:00-02:00
            inside = (wd in days and hm >= a) or ((wd - 1) % 7 in days and hm < b)
        if not inside:
            return False, "window"
    return True, ""


def user_when_text(u, lang=None):
    """«daily 08:00-20:00 · until 31.12.2026» for the pages and the window"""
    out = []
    w = u.get("win") if isinstance(u, dict) else None
    if w:
        days = w.get("days") or list(range(7))
        names = [tr(x, lang) for x in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")]
        d_ = tr("daily", lang) if len(days) == 7 else ", ".join(names[i] for i in days)
        out.append(f"{d_} {w['from']}–{w['to']}")
    if isinstance(u, dict) and u.get("until"):
        y, m, d = u["until"].split("-")
        out.append(tr("until", lang) + f" {d}.{m}.{y}")
    return " · ".join(out)


def user_gate(req, g_):
    """called by role_guard (550) for every user who is not the administrator: outside the time window / after the expiry
    date only a friendly page (or a short JSON for the scripts) - no data"""
    if getattr(g_, "role", "admin") == "admin":
        return None
    u = user_get(getattr(g_, "user", ""))
    if u is None:
        return None
    ok, why = user_active(u)
    if ok:
        return None
    from flask import Response
    import html as _h
    L = sx_req_lang()
    msg = tr("This access has expired.", L) if why == "until" else tr("Your access is not active right now.", L)
    when = user_when_text(u, L)
    if sx_wants_html() or req.path in ("/", "/more", "/help", "/quick"):
        body_ = ("<p>" + _h.escape(tr("Hello", L) + " " + u["name"] + "! " + msg) + "</p>"
                 + ("<p class=\"mut\">" + _h.escape(tr("Access", L) + ": " + when) + "</p>" if when else "")
                 + "<p class=\"mut\">" + _h.escape(tr("Ask the owner of MoveEye if you need it now.", L)) + "</p>"
                 + '<a class="btn" href="/">' + _h.escape(tr("Try again", L)) + "</a>")
        return Response(sx_page(tr("Access not active right now", L), body_, "🌙", L), 403, {"Cache-Control": "no-store"}, mimetype="text/html")
    return Response(json.dumps({"ok": False, "inactive": why, "error": msg}), 403, {"Cache-Control": "no-store"}, mimetype="application/json")


def user_perms_list(name, role):
    """for /api/state «me»: the rights of the current user (the administrator: all)"""
    if role == "admin":
        return list(USER_PERMS)
    u = user_get(name)
    return sorted(user_perms(u)) if u else sorted(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))


def user_req_perms(g_):
    """the rights for role_allows (None = the preset of the role)"""
    if getattr(g_, "role", "admin") in ("admin",):
        return None
    u = user_get(getattr(g_, "user", ""))
    return user_perms(u) if u else set()


# ---- linking a phone (QR, one-time link) ---------------------------------------------------------------------------------
def user_link_base(req=None):
    """the address the phone opens: the secure page when «Log in only encrypted» is active (574)"""
    host, scheme, own = "", "http", ""
    if req is not None:
        fh = str(req.headers.get("X-Forwarded-Host") or "").split(",")[0].strip()
        host = own = fh or str(req.host or "")
        proto = str(req.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
        scheme = "https" if (req.is_secure or proto == "https") else "http"
        if host.rsplit(":", 1)[0] in ("127.0.0.1", "localhost", "[::1]"):
            host = ""                                       # the phone cannot open the Pi's own «localhost»
    if not host:
        a = page_address() if "page_address" in globals() else ""
        if not a:
            try:
                ip_ = local_ip()
            except Exception:
                ip_ = ""
            a = f"http://{ip_}:{CFG['web_port']}/" if ip_ else (f"{scheme}://{own}/" if own else "")
        if not a:
            return ""
        scheme, host = a.split("://", 1)[0], a.split("://", 1)[1].rstrip("/")
    if scheme == "http" and seclogin_mode() == "on":
        port = seclogin_https_port()
        name = host[:host.find("]") + 1] if host.startswith("[") else (host.rsplit(":", 1)[0] if host.count(":") == 1 else host)
        return f"https://{name}:{port}"
    return f"{scheme}://{host}"


def user_link_make(name, req=None, who="admin"):
    """(url, seconds, secure) for a new one-time link of this user, or (None, error, False)"""
    import secrets
    u = user_get(name)
    if u is None:
        return None, "unknown user", False
    now = time.time()
    L = USER_LINK["links"]
    for k in [k for k, v in L.items() if v["exp"] < now or v["user"].lower() == u["name"].lower()]:
        L.pop(k, None)                                      # one open link per user: a new QR code makes the old one invalid
    if len(L) >= 20:
        return None, "too many open links - wait 10 minutes", False
    base = user_link_base(req)
    if not base:
        return None, "no network address of MoveEye", False
    tok = secrets.token_urlsafe(24)
    L[_ul_hash(tok)] = {"user": u["name"], "exp": now + USER_LINK_TTL, "by": who}
    log_event("web", f"{who}: link for a phone of «{u['name']}» made (valid 10 min, once)")
    return base + "/l/" + tok, USER_LINK_TTL, base.startswith("https://")


def user_link_page(title, text, ok, L, extra=""):
    import html as _h
    from flask import Response
    b = "<p>" + _h.escape(text) + "</p>" + extra
    return Response(sx_page(title, b, "📱" if ok else "⚠️", L), 200 if ok else 403, {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
                    mimetype="text/html")


# ---- devices of a user (the trusted devices of 040) ---------------------------------------------------------------------
def user_devices(name, mine_h=""):
    return [{"id": e.get("h", "")[:12], "name": e.get("name"), "t0": e.get("t0"), "seen": e.get("seen"), "ip": e.get("ip"),
             "via": e.get("via", ""), "me": bool(mine_h) and e.get("h") == mine_h}
            for e in (CFG.get("trusted") or []) if str(e.get("user", "")).lower() == str(name).lower() and e.get("role") != "admin"]


def user_device_remove(name, did, who="admin"):
    lst = CFG.get("trusted") or []
    hit = next((e for e in lst if str(e.get("user", "")).lower() == str(name).lower() and e.get("role") != "admin"
                and len(str(did)) >= 8 and e.get("h", "").startswith(str(did))), None)
    if hit is None:
        return False
    CFG["trusted"] = [e for e in lst if e is not hit]
    save_settings_now()
    log_event("web", f"{who}: device «{hit.get('name')}» of «{name}» removed - logged out")
    return True


def users_public(mine_h=""):
    """the users for the page (never the password hash or the own ntfy topic in full)"""
    out = []
    for u in CFG["users"]:
        t_ = str(u.get("ntfy") or "")
        out.append({"name": u["name"], "role": u["role"], "perms": sorted(user_perms(u)), "win": u.get("win"), "until": u.get("until", ""),
                    "push": u.get("push", []), "ntfy": ("…" + t_[-4:]) if t_ else "", "nopw": bool(u.get("nopw")),
                    "active": user_active(u)[0], "devices": user_devices(u["name"], mine_h),
                    "webpush": sum(1 for x in webpush_subs() if str(x.get("user", "")).lower() == u["name"].lower())})
    return out


# ---- push per user ---------------------------------------------------------------------------------------------------------
def push_cat(tag):
    """the kind of a message from the tag of the web push: alarm / info / games / test"""
    t_ = str(tag or "")[3:]
    if t_ in ("person", "warm", "noise", "tamper", "prealarm"):
        return "alarm"
    if t_.startswith("game"):
        return "games"
    return "test" if t_ == "test" else "info"


def users_push_wants(name, cat):
    u = user_get(name)
    if u is None or not user_active(u)[0]:
        return False
    prefs = u.get("push") or []
    if cat == "test":
        return bool(prefs)
    if cat == "games" and "games" not in user_perms(u):
        return False
    return cat in prefs


def push_sub_wants(sub, cat):
    """webpush_all (050): may this browser get this message? Browsers without a user = the administrator (as before)"""
    n = sub.get("user") if isinstance(sub, dict) else ""
    if not n:
        return cat != "games"
    return users_push_wants(n, cat)


def users_push_forget(name):
    subs = webpush_subs()
    new = [x for x in subs if str(x.get("user", "")).lower() != str(name).lower()]
    if len(new) != len(subs):
        _webpush_save(new)


def _users_ntfy_url(topic):
    if topic.startswith("https://"):
        return topic
    base = "https://ntfy.sh"
    if CFG.get("notify_type") == "ntfy":
        m = re.match(r"^(https://[^/\s]+)/", str(CFG.get("notify_url") or "").strip())
        if m:
            base = m.group(1)
    return base + "/" + topic


def _users_ntfy_send(name, url, title, text, cat, click):
    h = {"Title": _hdr(title), "Priority": "high" if cat == "alarm" else "default",
         "Tags": {"alarm": "warning", "games": "game_die", "info": "information_source"}.get(cat, "bell")}
    if click:
        h["Click"] = click
    try:
        req = urllib.request.Request(url, data=str(text)[:2000].encode("utf-8"), headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            log_event("web", f"Push to «{name}» (own ntfy topic): HTTP {r.status}")
    except Exception as e:
        log_event("web", f"Push to «{name}» (own ntfy topic) failed: {str(e)[:80]}".replace(url, "ntfy"))


def users_push_dispatch(title, text, cat, click=""):
    """the own ntfy topics of the users (the main channel stays with the administrator)"""
    n = 0
    for u in list(CFG["users"]):
        if u.get("ntfy") and users_push_wants(u["name"], cat):
            threading.Thread(target=_users_ntfy_send, args=(u["name"], _users_ntfy_url(u["ntfy"]), title, text, cat, click),
                             daemon=True, name="push-user").start()
            n += 1
    return n


def users_push_games():
    """«Spiele freigeben» (320): an invitation to the users who want it"""
    if not CFG["users"]:
        return
    title, text = tr("🎲 Games are open"), tr("Come to the game corner - scan the QR code there or open MoveEye.")
    click = (page_address().rstrip("/") + "/party") if "page_address" in globals() and page_address() else ""
    try:
        if CFG.get("webpush_on") and any(x.get("user") for x in webpush_subs()):
            threading.Thread(target=webpush_all, args=(title, text, "/party", "mw-games", False), daemon=True, name="push-games").start()
    except Exception:
        pass
    users_push_dispatch(title, text, "games", click)


# ---- what the page hides for a user (the server refuses it anyway) --------------------------------------------------------
USER_UI_HIDE = {
    "live": '#vcard,#video,#pip,nav.subnav a[href="/cams"],#lv-vin,#lv-vbig',
    "rec": 'nav.nav a[href="/recordings"],a[href="/kino"],#b-rec',
    "arm": 'nav.nav a[href="/protect"],#b-arm,#pr-card,#protect-box,details[data-view="protect"],details[data-view="controls"]',
    "light": '#b-light,#b-lights,#light-quick,#lights-box,#mode-disco,#disco-more,#disco-sum',
    "head": '#stick,#mstickbox,#ctl-mstick,#stick-center,#vo-mctl,#vo-center,#mctl,#b-pat,#vo-mslot,#vo-mgrip',
    "talk": '#talk-slot',
    "games": 'a[href="/party"]',
    "settings": 'nav.nav a[href="/settings"]',
}
USER_UI_ADMIN = ('nav.nav a[href="/sim"],a[href="/tools"],a[href="/qr"],#m-qr,a[href="/timeline"],a[href="/messages"],a[href="/log"],'
                 'a[href="/info"],#m-info,#g2-sys,aside[data-view="sidebar"],#side-open,#wf-card,[data-view="wifi"],#games #g-btn')


def users_ui_css(perms):
    sel = [USER_UI_ADMIN] + [v for k, v in USER_UI_HIDE.items() if k not in perms]
    return "<style id=\"mw-user-css\">" + ",".join(sel) + "{display:none!important}</style>"


def users_routes(app, reply, body):
    from flask import request, Response, g as g_

    @app.route("/l/<tok>")
    def user_link_open(tok):
        L = sx_req_lang()
        ip = request.remote_addr or "?"
        now = time.time()
        recent = [x for x in USER_LINK["fails"].get(ip, []) if now - x < 600]
        if len(recent) >= 10:
            USER_LINK["fails"][ip] = recent
            return sx_err(429, "toomany", {"Retry-After": "600"})
        h = _ul_hash(tok) if 20 <= len(tok) <= 64 else ""
        e = USER_LINK["links"].get(h) if h else None
        if e is None or e["exp"] < now:
            if h:
                USER_LINK["links"].pop(h, None)
            recent.append(now); USER_LINK["fails"][ip] = recent
            if len(USER_LINK["fails"]) > 300:
                USER_LINK["fails"].clear()
            return user_link_page(tr("Link not valid", L), tr("This link is not valid any more (10 minutes, only once). Ask for a new QR code.", L), False, L)
        if seclogin_plain(request):                    # 574: it came unencrypted through the network - it could have been read
            USER_LINK["links"].pop(h, None)
            log_event("web", f"Phone link of «{e['user']}» opened over plain http from {ip} - blocked, make a new QR code")
            return user_link_page(tr("Link blocked", L), tr("This link was opened without encryption (http) and is blocked now for safety. Make a new QR code and scan it - it leads to the secure page (https).", L), False, L)
        USER_LINK["links"].pop(h, None)                # only once
        u = user_get(e["user"])
        if u is None:
            return user_link_page(tr("Link not valid", L), tr("This user does not exist any more.", L), False, L)
        cookie = trust_add(u["name"], u["role"], request.headers.get("User-Agent", ""), ip[:45], via="link")
        log_event("web", f"Phone linked to «{u['name']}» ({ip})")
        import html as _h
        r = user_link_page("✓ " + tr("Phone linked", L), tr("This phone is now logged in as", L) + " «" + u["name"] + "». "
                           + tr("No password needed. The owner can remove it at any time.", L), True, L,
                           '<a class="btn" href="/">' + _h.escape(tr("Open MoveEye", L)) + "</a>"
                           '<script>setTimeout(function(){location.replace("/")},1800)</script>')
        r.set_cookie(TRUST_COOKIE, cookie, max_age=365 * 86400, httponly=True, samesite="Lax", secure=request.is_secure, path="/")
        return r

    @app.after_request
    def users_after(resp):                         # the page shows only what this user may do; a removed device stops at once
        role = getattr(g_, "role", "admin")
        if role == "admin" or not CFG["users"]:
            return resp
        try:
            if resp.status_code == 200 and resp.mimetype == "text/html" and not resp.direct_passthrough and not resp.is_streamed \
                    and request.method == "GET":
                perms = user_req_perms(g_) or set()
                html_ = resp.get_data(as_text=True)
                if "</head>" in html_:
                    resp.set_data(html_.replace("</head>", users_ui_css(perms) + "</head>", 1))
            elif resp.mimetype and resp.mimetype.startswith("multipart/x-mixed-replace") and resp.is_streamed:
                tok = request.cookies.get(TRUST_COOKIE, "")
                th = _trust_hash(tok) if tok else ""
                name = getattr(g_, "user", "")
                inner = resp.response

                def guarded():
                    last = 0.0
                    try:
                        for chunk in inner:
                            if time.monotonic() - last > 1.0:
                                last = time.monotonic()
                                u = user_get(name)
                                if u is None or not user_active(u)[0] or (th and not any(e.get("h") == th for e in (CFG.get("trusted") or []))):
                                    break
                            yield chunk
                    finally:
                        c_ = getattr(inner, "close", None)
                        if c_:
                            c_()
                resp.response = guarded()
        except Exception:
            pass
        return resp


def users_api(request, reply, body, g_):
    """/api/users (only the administrator - ADMIN_GET + role_guard): list, add, update, link a phone, remove a device"""
    mine = _trust_hash(request.cookies.get(TRUST_COOKIE, "")) if request.cookies.get(TRUST_COOKIE) else ""
    who = getattr(g_, "user", "") or "admin"
    if getattr(g_, "appkey", None):
        who = "app key"
    if request.method == "GET":
        return reply({"users": users_public(mine), "pw": web_pw_active(), "plain": seclogin_mode() != "on" and web_pw_active(),
                      "roles": {r: list(p) for r, p in ROLE_PERMS.items()}, "perms": list(USER_PERMS), "push": list(USER_PUSH)})
    d = body(); lang = norm_lang(d.get("lang"))
    a = d.get("action")
    res = {}
    if a == "link":
        url, sec, secure = user_link_make(str(d.get("name") or ""), request, who)
        if url is None:
            return reply({"ok": False, "error": tr_err(sec, lang)}, 400)
        res = {"url": url, "seconds": sec, "secure": secure}
        ok, err = True, ""
    elif a == "device_remove":
        ok = user_device_remove(str(d.get("name") or ""), str(d.get("id") or ""), who); err = "" if ok else "unknown device"
    else:
        ok, err = users_action(d, who)
    return reply(dict(res, ok=ok, error=tr_err(err, lang) if err else None, users=users_public(mine)), 200 if ok else 400)


def users_selftest():
    """rights, time window, push filter, link tokens - without a server"""
    from datetime import datetime as _dt
    assert role_allows("kid", "/video_feed", "GET", {}) and role_allows("kid", "/party", "GET", {})
    assert not role_allows("kid", "/api/recordings", "GET", {}) and not role_allows("kid", "/api/arm", "POST", {})
    assert not role_allows("kid", "/settings", "GET", {}) and not role_allows("kid", "/api/light", "POST", {})
    assert role_allows("friend", "/api/light", "POST", {}) and role_allows("friend", "/api/talk", "POST", {})
    assert not role_allows("friend", "/api/arm", "POST", {}) and not role_allows("friend", "/rec/file/x.mp4", "GET", {})
    assert role_allows("family", "/api/arm", "POST", {}) and role_allows("family", "/rec/file/x.mp4", "GET", {})
    assert role_allows("family", "/api/audio", "POST", {"action": "siren"}) and not role_allows("family", "/settings", "GET", {})
    assert not role_allows("family", "/api/users", "GET", {}) and not role_allows("family", "/api/set", "POST", {"key": "web_port"})
    assert role_allows("operate", "/api/arm", "POST", {}) and not role_allows("view", "/api/arm", "POST", {})
    assert role_allows("custom", "/api/set", "POST", {"key": "record"}, {"settings"})
    assert not role_allows("custom", "/api/set", "POST", {"key": "users"}, {"settings"})
    assert not role_allows("custom", "/api/text", "POST", {"key": "notify_url"}, {"settings"})
    assert users_clean([{"name": "Alt", "hash": "pbkdf2$1$00$00", "role": "operate"}])[0]["role"] == "family"
    k = users_clean([{"name": "Kid", "hash": "pbkdf2$1$00$00", "role": "kid", "win": {"from": "08:00", "to": "20:00"}}])[0]
    assert k["push"] == ["games"] and k["win"]["days"] == list(range(7))
    assert user_active(k, _dt(2026, 10, 30, 12, 0))[0] and not user_active(k, _dt(2026, 10, 30, 21, 0))[0]
    n = dict(k, win={"from": "18:00", "to": "02:00", "days": [4]})
    assert user_active(n, _dt(2026, 10, 30, 23, 0))[0] and user_active(n, _dt(2026, 10, 31, 1, 0))[0] and not user_active(n, _dt(2026, 10, 31, 3, 0))[0]
    assert not user_active(dict(k, win=None, until="2026-10-29"), _dt(2026, 10, 30, 9, 0))[0]
    assert user_active(dict(k, win=None, until="2026-10-30"), _dt(2026, 10, 30, 23, 59))[0]
    assert push_cat("mw-person") == "alarm" and push_cat("mw-games") == "games" and push_cat("mw-info") == "info"
    assert push_sub_wants({}, "alarm") and not push_sub_wants({}, "games")
    return True

