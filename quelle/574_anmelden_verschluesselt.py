#@ MoveEye – Teil 574: «Anmelden nur verschlüsselt» – das Web-Passwort geht nie unverschlüsselt durchs Netz (Web und Fenster). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (29.10.2026): the web password must not travel unencrypted over the network.
#   * A login (the browser's password question, the password of a program, setting a password) over plain http is only
#     taken from this device itself (127.0.0.1, its own addresses) and from encrypted ways: the secure page (https,
#     port + 1, self-signed certificate made once in the settings folder, part 420), Tailscale (WireGuard, 100.64.0.0/10)
#     and «https over Tailscale» / a tunnel on this device (arrives as 127.0.0.1 with X-Forwarded-*).
#   * From any other address the page answers with a short hint (certificate warning of the browser) and leads to the
#     secure page - WITHOUT asking for the password over http (no «WWW-Authenticate»), so the browser never sends it.
#   * Never lock Daniel out: if the secure page cannot run (no openssl / cryptography, port busy, «https_extra» off),
#     the http login keeps working and a warning is shown (self-check, settings, window).
#   * Unchanged: links with their own key (/na/ buttons in the push, /g/ guests, /x/ shares, /k/ kiosk, /tv/ ...), the
#     public files, and a device that is already trusted (its cookie is no password).
# ----------------------------------------------------------------------------
_SECLOGIN_CFG = {"login_https_only": True}
for _k, _v in _SECLOGIN_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TOGGLES.extend([
    ("Security", "login_https_only", "Log in only encrypted (https): from other devices the password is only accepted over the secure page"),
])
# «Simple» shows the section only when something is wrong (no secure page, or switched off with a password); «Expert» always
SIMPLE_IN_USE["Security"] = lambda: web_pw_active() and seclogin_mode() != "on"
SIMPLE_KEYS.add("login_https_only")
SECLOGIN = {"own": (0.0, frozenset()), "logged": {}, "fallback_logged": False}
SECLOGIN_NOTE = ("The password is only accepted over the secure page (https://…:port + 1) or from this device itself. Over plain http "
                 "everybody in the same Wi-Fi (camping!) could read it. The browser warns once about the certificate (it is made by MoveEye "
                 "itself) - accept it once. Tailscale and «https over Tailscale» are encrypted and work as before. Links with their own key "
                 "(buttons in the push message, guests, shares) keep working. Programs (Home Assistant, shortcuts) use an app key (below) or the https address.")


def _seclogin_ip(s):
    import ipaddress
    try:
        return ipaddress.ip_address(str(s or "").split("%")[0])
    except ValueError:
        return None


def seclogin_tailscale(ip):
    """Tailscale addresses (WireGuard: always encrypted): 100.64.0.0/10 and fd7a:115c:a1e0::/48"""
    import ipaddress
    a = _seclogin_ip(ip)
    if a is None:
        return False
    if getattr(a, "ipv4_mapped", None):
        a = a.ipv4_mapped
    nets = (ipaddress.ip_network("100.64.0.0/10"),) if a.version == 4 else (ipaddress.ip_network("fd7a:115c:a1e0::/48"),)
    return any(a in n for n in nets)


def seclogin_own_ips():
    """the addresses of this device (a browser on the Pi that opens http://<own address>/ is the device itself)"""
    t, ips = SECLOGIN["own"]
    if time.time() - t < 60:
        return ips
    import socket
    s = {"127.0.0.1", "::1"}
    try:
        ip_ = local_ip()
        if ip_:
            s.add(ip_)
    except Exception:
        pass
    try:
        for x in socket.getaddrinfo(socket.gethostname(), None):
            s.add(x[4][0].split("%")[0])
    except OSError:
        pass
    if shutil.which("hostname"):
        try:
            out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=3).stdout
            s.update(x.split("%")[0] for x in out.split())
        except (OSError, subprocess.SubprocessError):
            pass
    ips = frozenset(s)
    SECLOGIN["own"] = (time.time(), ips)
    return ips


def seclogin_https_port():
    """the port of the secure page, or None when there is none"""
    if WEB_OPTS.get("https"):
        return int(CFG["web_port"])
    return STATE.get("https_port") or None


def seclogin_secure(req):
    """may a password come with this request? (https, this device, Tailscale, a proxy on this device that is https)"""
    if req.is_secure:
        return True
    ra = str(req.remote_addr or "")
    fwd = req.headers.get("X-Forwarded-For") or req.headers.get("Forwarded") or req.headers.get("X-Forwarded-Host")
    if ra in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        if not fwd:
            return True                                     # really this device (the window, a browser on the Pi)
        proto = str(req.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
        return proto != "http"                              # «https over Tailscale» (tailscale serve) / a tunnel: https outside
    if seclogin_tailscale(ra):
        return True
    return ra.split("%")[0] in seclogin_own_ips()


def seclogin_mode():
    """"off" (setting off), "fallback" (setting on, but no secure page: http login allowed with a warning), "on" """
    if not CFG.get("login_https_only", True):
        return "off"
    if not seclogin_https_port():
        if not SECLOGIN["fallback_logged"] and time.time() - START > 60:
            SECLOGIN["fallback_logged"] = True
            log_event("web", "Warning: no secure page (https) - the web password still goes unencrypted through the network (install openssl)")
        return "fallback"
    return "on"


def seclogin_plain(req):
    """True = this request comes over plain http from another device and must not carry a password"""
    return seclogin_mode() == "on" and not seclogin_secure(req)


def seclogin_url(req):
    """the same address on the secure page"""
    port = seclogin_https_port()
    host = str(req.host or "")
    if not re.fullmatch(r"[A-Za-z0-9.\-\[\]:]{1,200}", host):
        host = local_ip() or "localhost"
    if host.startswith("["):
        name = host[:host.find("]") + 1] if "]" in host else host
    else:
        name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    path = req.full_path if req.query_string else req.path
    return f"https://{name}:{port}{path if path.startswith('/') else '/' + path}"


def seclogin_block(req):
    """the answer for a login over plain http from another device: a hint page (browser) or a short JSON (programs)"""
    from flask import Response
    import html as _h
    url = seclogin_url(req)
    ip = str(req.remote_addr or "?")
    if req.authorization:                                 # the password came already: tell it once per hour and device
        now = time.time()
        if now - SECLOGIN["logged"].get(ip, 0) > 3600:
            SECLOGIN["logged"][ip] = now
            if len(SECLOGIN["logged"]) > 200:
                SECLOGIN["logged"].clear()
            log_event("web", f"Login over unencrypted http from {ip} refused - only over the secure page {url.split('/', 3)[2]}")
    L = sx_req_lang()
    if sx_wants_html():
        body = ("<p>" + _h.escape(tr("For your safety MoveEye takes the password only over the secure page (https). Over plain http everybody in the same Wi-Fi could read it.", L)) + "</p>"
                "<p>" + _h.escape(tr("The browser will warn once that the certificate is not trusted: MoveEye made it itself. Choose «Advanced» → «Continue» (iPhone: «Show details» → «visit this website»).", L)) + "</p>"
                '<a class="btn" id="go" href="' + _h.escape(url) + '">🔒 ' + _h.escape(tr("To the secure page", L)) + "</a>"
                '<p style="font-size:13px;opacity:.75;word-break:break-all">' + _h.escape(url) + "</p>"
                "<script>setTimeout(function(){location.href=document.getElementById('go').href;},12000);</script>")
        return Response(sx_page(tr("Log in only encrypted", L), body, "🔒", L), 403, {"Cache-Control": "no-store"}, mimetype="text/html")
    return Response(json.dumps({"ok": False, "error": tr("log in only over the secure page (https)", L) + ": " + url, "https": url}),
                    403, {"Cache-Control": "no-store"}, mimetype="application/json")


def seclogin_body_check(req):
    """a request that SETS a password (web password, users, setup assistant) over plain http from another device:
    refused with the https address (also when no password is set yet - else the first password goes unencrypted)"""
    if req.method != "POST" or req.path not in ("/api/password", "/api/users", "/api/setup"):
        return None
    if not seclogin_plain(req):
        return None
    d = req.get_json(force=True, silent=True)
    if not (isinstance(d, dict) and str(d.get("password") or "")):
        return None
    L = norm_lang(d.get("lang") or sx_req_lang())
    url = seclogin_url(req).split("/api/")[0] + "/"
    return _seclogin_json({"ok": False, "error": tr("For your safety a password can only be set over the secure page", L) + ": " + url, "https": url}, 403)


def _seclogin_json(obj, code=200):
    from flask import Response
    return Response(json.dumps(obj), status=code, mimetype="application/json", headers={"Cache-Control": "no-store"})


def seclogin_info(req=None, lang=None):
    """for the page (Settings → Security), /api/state and the window"""
    m = seclogin_mode()
    port = seclogin_https_port()
    i = {"on": bool(CFG.get("login_https_only", True)), "mode": m, "port": port, "pw": web_pw_active(),
         "note": tr(SECLOGIN_NOTE, lang), "warn": ""}
    if req is not None:
        i["secure"] = seclogin_secure(req)
        i["plain"] = m == "on" and not i["secure"]
        i["url"] = seclogin_url(req) if port else ""
    if m == "fallback":
        i["warn"] = tr("No secure page (https) - the password still goes unencrypted through the network. Install openssl (sudo apt install openssl) and restart MoveEye.", lang)
    elif m == "off" and web_pw_active():
        i["warn"] = tr("Off: the password may go unencrypted through the network (http).", lang)
    return i


def seclogin_text(lang=None):
    """one line for the window"""
    i = seclogin_info(None, lang)
    if i["mode"] == "on":
        return "🔒 " + tr("on", lang) + f" · https {tr('port', lang)} {i['port']}"
    return "⚠ " + i["warn"] if i["warn"] else "🔓 " + tr("off", lang)


def seclogin_selftest():
    """the address rules (no server needed)"""
    class _H(dict):
        def get(self, k, d=None):
            return dict.get(self, k, d)

    class _R:
        def __init__(self, ra, sec=False, h=None, host="192.168.1.5:5000", path="/"):
            self.remote_addr, self.is_secure, self.headers, self.host, self.path = ra, sec, _H(h or {}), host, path
            self.query_string, self.full_path = b"", path + "?"
    assert seclogin_tailscale("100.101.102.103") and seclogin_tailscale("fd7a:115c:a1e0::1") and not seclogin_tailscale("192.168.1.20")
    assert seclogin_secure(_R("127.0.0.1")) and seclogin_secure(_R("10.0.0.9", sec=True))
    assert seclogin_secure(_R("127.0.0.1", h={"X-Forwarded-For": "1.2.3.4", "X-Forwarded-Proto": "https"}))
    assert not seclogin_secure(_R("127.0.0.1", h={"X-Forwarded-For": "1.2.3.4", "X-Forwarded-Proto": "http"}))
    assert not seclogin_secure(_R("192.0.2.77"))                       # TEST-NET: never an own address
    keep = STATE.get("https_port"), CFG.get("login_https_only")
    try:
        STATE["https_port"] = 5001; CFG["login_https_only"] = True
        assert seclogin_url(_R("192.0.2.77", path="/zones")) == "https://192.168.1.5:5001/zones"
        assert seclogin_url(_R("192.0.2.77", host="[fe80::1]:5000")) == "https://[fe80::1]:5001/"
        assert seclogin_mode() == "on" and seclogin_plain(_R("192.0.2.77")) and not seclogin_plain(_R("100.64.0.5"))
        STATE["https_port"] = None
        assert seclogin_mode() == "fallback" and not seclogin_plain(_R("192.0.2.77"))   # no secure page: never locked out
        STATE["https_port"] = 5001; CFG["login_https_only"] = False
        assert not seclogin_plain(_R("192.0.2.77"))
    finally:
        STATE["https_port"], CFG["login_https_only"] = keep
    return True


SELFTEST_EXTRA.append(("Log in only encrypted (https rules)", seclogin_selftest))
