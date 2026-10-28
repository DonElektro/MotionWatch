#@ Motion Watch – Teil 050: Meldungen (ntfy, Telegram, Webhook), Web-Push. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Notifications: webhook / ntfy / Telegram when a person is detected (with cooldown)
# ----------------------------------------------------------------------------
TELEGRAM_API = "https://api.telegram.org"
LANGS = ("de", "fr", "it", "rm", "en")            # the five languages (Swiss national languages + English)
LANG_NAMES = {"de": "Deutsch", "fr": "Français", "it": "Italiano", "rm": "Rumantsch", "en": "English"}
LOCALES = {"de": "de-CH", "fr": "fr-CH", "it": "it-CH", "rm": "de-CH", "en": "en-GB"}
TRX = {"fr": {}, "it": {}, "rm": {}}     # English text -> French / Italian / Romansh (filled at the end of the file)
HELP_X = {}                             # the manual in French / Italian / Romansh (filled at the end of the file)
LANG_JS = r"""
// ---- language: menu with the five languages (the choice is kept per device) ----
var LANGN = {de: "Deutsch", fr: "Français", it: "Italiano", rm: "Rumantsch", en: "English"};
var LOCALE = l => ({de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"})[l] || "en-GB";
function langSet(k) {      // keep the language (also on the Pi, for the other pages / devices), then load the page in it
  try { localStorage.setItem("mw-lang", k); } catch (e) {}
  const go = () => location.reload();
  try { fetch("/api/ui", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({set: {"mw-lang": k}})}).then(go, go); setTimeout(go, 1500); }
  catch (e) { go(); }
}
function langMenu(anchor) {
  let m = document.getElementById("langmenu"); if (m) { m.remove(); return; }
  m = document.createElement("div"); m.id = "langmenu"; m.setAttribute("role", "menu");
  Object.keys(LANGN).forEach(k => { const b = document.createElement("button"); b.type = "button"; b.textContent = LANGN[k];
    if (k === (typeof LANG !== "undefined" ? LANG : "")) b.className = "on";
    b.onclick = () => langSet(k); m.appendChild(b); });
  document.body.appendChild(m);
  let r = anchor ? anchor.getBoundingClientRect() : null;
  if (!r || !r.width) r = {right: innerWidth - 10, bottom: 56};          // the button is hidden (compact header): top right
  m.style.top = Math.round(r.bottom + 6) + "px"; m.style.right = Math.max(8, Math.round(innerWidth - r.right)) + "px";
  setTimeout(() => { const off = e => { if (!m.contains(e.target)) { m.remove(); removeEventListener("pointerdown", off, true); } };
    addEventListener("pointerdown", off, true); }, 0);
}
"""   # in the first script of every page (the language button and the setup assistant use it)


def norm_lang(lang):
    lang = str(lang or "").lower()[:2]
    return lang if lang in LANGS else "en"


def cur_lang(lang=None):
    return norm_lang(lang or CFG.get("lang") or "en")


def msg_defaults(lang=None):
    L = cur_lang(lang)
    return MSG_DEFAULTS.get(L) or MSG_DEFAULTS["de" if L == "rm" else "en"]


MSG_DEFAULTS = {
    "de": {"person": ("{name}: Person erkannt", "{count} Person(en) erkannt um {time} - Kamera: {camera}"),
           "prealarm": ("{name}: Bewegung (Voralarm)", "Voralarm: Bewegung um {time} - Kamera: {camera}"),
           "warm": ("{name}: Wärme erkannt", "Wärmebild: warmer Körper in der Zone um {time} - Kamera: {camera}"),
           "noise": ("{name}: Geräusch", "Geräusch-Alarm: laut ({db} dB) um {time} - Kamera: {camera}")},
    "en": {"person": ("{name}: person detected", "{count} person(s) detected at {time} - camera: {camera}"),
           "prealarm": ("{name}: movement (pre-alarm)", "Pre-alarm: movement at {time} - camera: {camera}"),
           "warm": ("{name}: warm body detected", "Thermal camera: warm body in the zone at {time} - camera: {camera}"),
           "noise": ("{name}: noise", "Noise alarm: loud ({db} dB) at {time} - camera: {camera}")},
}
MSG_PLACEHOLDERS = "{name} {time} {date} {count} {camera} {link} {db}"


def msg_template(kind, part):
    """Own text if set, otherwise the standard text in the language of the program. part = 0 title, 1 text."""
    own = CFG.get(f"msg_{kind}_{'title' if part == 0 else 'text'}", "")
    return own if own.strip() else msg_defaults()[kind][part]


def render_msg(tpl, p):
    t = p.get("time", "")
    vals = {"name": CFG["device_name"].strip() or "MoveEye", "time": t[11:19], "count": str(p.get("persons", 0)),
            "date": f"{t[8:10]}.{t[5:7]}.{t[0:4]}" if len(t) >= 10 else "", "camera": p.get("source", ""), "link": p.get("link", ""),
            "db": str(p.get("db", ""))}
    return re.sub(r"\{(\w+)\}", lambda m: vals.get(m.group(1), m.group(0)), tpl)     # only known placeholders, nothing else


def _hdr(v):
    """HTTP headers are latin-1: umlauts / emoji go as RFC 2047 (ntfy understands that)."""
    import base64
    v = " ".join(str(v).split())
    return v if v.isascii() else "=?UTF-8?B?" + base64.b64encode(v.encode()).decode() + "?="


# ----------------------------------------------------------------------------
# Web push: alarm messages straight to the phone / PC browser - no extra app. The page must be opened over https (Tailscale:
#   «https über Tailscale» gives https://<name>.<tailnet>.ts.net with a real certificate); on the iPhone the page must be on the
#   home screen. Standard Web Push (RFC 8030 / 8291 / 8292) with python3-cryptography (part of Raspberry Pi OS).
# ----------------------------------------------------------------------------
WEBPUSH = {"lock": threading.Lock(), "subs": None, "key": None, "status": ""}


def _b64u(b):
    import base64
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64u_dec(s_):
    import base64
    s_ = str(s_ or "")
    return base64.urlsafe_b64decode(s_ + "=" * (-len(s_) % 4))


def webpush_supported():
    try:
        import cryptography  # noqa: F401
        return True
    except ImportError:
        return False


def _wp_file(name):
    return os.path.join(DATA_DIR, name)


def webpush_key():
    """The server's own key pair (VAPID, P-256); made once and kept in the data folder (never sent anywhere)."""
    if WEBPUSH["key"] is not None:
        return WEBPUSH["key"]
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    p_ = _wp_file("webpush_vapid.pem")
    key = None
    try:
        with open(p_, "rb") as f:
            key = serialization.load_pem_private_key(f.read(), None)
    except (OSError, ValueError):
        key = ec.generate_private_key(ec.SECP256R1())
        try:
            fd = os.open(p_, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        except OSError:
            pass
    WEBPUSH["key"] = key
    return key


def webpush_public():
    from cryptography.hazmat.primitives import serialization
    return _b64u(webpush_key().public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))


def webpush_subs():
    with WEBPUSH["lock"]:
        if WEBPUSH["subs"] is None:
            try:
                with open(_wp_file("webpush_subs.json")) as f:
                    WEBPUSH["subs"] = [x for x in json.load(f) if isinstance(x, dict) and x.get("endpoint")][:50]
            except (OSError, ValueError):
                WEBPUSH["subs"] = []
        return list(WEBPUSH["subs"])


def _webpush_save(subs):
    with WEBPUSH["lock"]:
        WEBPUSH["subs"] = subs[:50]
        try:
            tmp = _wp_file("webpush_subs.json.part")
            with open(tmp, "w") as f:
                json.dump(WEBPUSH["subs"], f)
            os.replace(tmp, _wp_file("webpush_subs.json"))
        except OSError:
            pass


_WP_HOST = re.compile(r"^https://[A-Za-z0-9.\-]+(:\d+)?/[^\s]{1,900}$")


def webpush_add(sub, label=""):
    try:
        ep = str(sub["endpoint"]); keys = sub.get("keys") or {}
        p256, auth = _b64u_dec(keys["p256dh"]), _b64u_dec(keys["auth"])
    except (KeyError, TypeError, ValueError):
        return False, "invalid subscription"
    if not _WP_HOST.match(ep) or len(p256) != 65 or len(auth) != 16:
        return False, "invalid subscription"
    subs = [x for x in webpush_subs() if x["endpoint"] != ep]
    subs.append({"endpoint": ep, "p256dh": _b64u(p256), "auth": _b64u(auth), "label": str(label or "")[:60],
                 "added": datetime.now().strftime("%Y-%m-%d %H:%M")})
    _webpush_save(subs)
    log_event("web", f"Web push switched on for {str(label or 'a device')[:60]}")
    return True, ""


def webpush_remove(endpoint):
    subs = webpush_subs()
    new = [x for x in subs if x["endpoint"] != endpoint]
    _webpush_save(new)
    return len(new) != len(subs)


def _webpush_encrypt(payload, p256dh, auth):
    """RFC 8291 (aes128gcm): encrypt the message for one browser."""
    from cryptography.hazmat.primitives import hashes, hmac as chmac, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    def hm(key, data):
        h = chmac.HMAC(key, hashes.SHA256()); h.update(data); return h.finalize()
    ua_pub = _b64u_dec(p256dh); secret = _b64u_dec(auth)
    eph = ec.generate_private_key(ec.SECP256R1())
    as_pub = eph.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    shared = eph.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub))
    ikm = hm(hm(secret, shared), b"WebPush: info\x00" + ua_pub + as_pub + b"\x01")
    salt = os.urandom(16)
    prk = hm(salt, ikm)
    cek = hm(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
    nonce = hm(prk, b"Content-Encoding: nonce\x00\x01")[:12]
    ct = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)
    return salt + (4096).to_bytes(4, "big") + bytes([len(as_pub)]) + as_pub + ct


def _vapid_header(endpoint):
    """RFC 8292: a short signed note (JWT, ES256) that says which server sends."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    m = re.match(r"^(https://[^/]+)", endpoint)
    head = _b64u(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    claims = _b64u(json.dumps({"aud": m.group(1), "exp": int(time.time()) + 12 * 3600, "sub": "mailto:motionwatch@example.invalid"},
                              separators=(",", ":")).encode())
    r, s_ = decode_dss_signature(webpush_key().sign((head + "." + claims).encode(), ec.ECDSA(hashes.SHA256())))
    jwt = head + "." + claims + "." + _b64u(r.to_bytes(32, "big") + s_.to_bytes(32, "big"))
    return f"vapid t={jwt}, k={webpush_public()}"


def webpush_send(sub, msg, ttl=86400, urgent=True):
    body_ = _webpush_encrypt(json.dumps(msg, ensure_ascii=False).encode()[:3000], sub["p256dh"], sub["auth"])
    req = urllib.request.Request(sub["endpoint"], data=body_, method="POST", headers={
        "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream", "TTL": str(int(ttl)),
        "Urgency": "high" if urgent else "normal", "Authorization": _vapid_header(sub["endpoint"])})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def webpush_all(title, text, url="/", tag="mw", urgent=True):
    """Send to every browser that switched web push on; browsers that are gone (404 / 410) are removed."""
    subs = webpush_subs()
    if not subs or not webpush_supported():
        return 0
    ok = 0; gone = []
    for sb in subs:
        try:
            code = webpush_send(sb, {"title": title[:120], "body": text[:400], "url": url or "/", "tag": tag, "urgent": bool(urgent)},
                                urgent=urgent)
        except Exception as e:
            code = 0; WEBPUSH["status"] = f"error: {str(e)[:120]}"
        if code in (404, 410):
            gone.append(sb["endpoint"])
        elif 200 <= code < 300:
            ok += 1
    if gone:
        _webpush_save([x for x in webpush_subs() if x["endpoint"] not in gone])
        log_event("web", f"Web push: {len(gone)} device(s) no longer subscribed - removed")
    WEBPUSH["status"] = f"{datetime.now().strftime('%H:%M:%S')}: {ok}/{len(subs)}"
    return ok


def tailscale_https(on=True):
    """«https über Tailscale»: tailscale serve passes https://<name>.ts.net (real certificate) on to this page."""
    exe = shutil.which("tailscale")
    if not exe:
        return False, "Tailscale is not installed"
    args = ["serve", "--bg", str(CFG["web_port"])] if on else ["serve", "--https=443", "off"]
    err = ""
    for c in ([exe] + args, ["sudo", "-n", exe] + args):
        rc, out, e = _run(c, timeout=30)
        if rc == 0:
            log_event("web", "https over Tailscale " + ("switched on" if on else "switched off"))
            return True, ""
        err = (e or out or f"exit {rc}").strip()[:200]
    if "HTTPS" in err or "certificate" in err.lower():
        err += " - in the Tailscale admin page switch on «HTTPS certificates» (DNS)"
    return False, err


def tailscale_https_url():
    ts = tailscale_status()
    exe = shutil.which("tailscale")
    if not exe or ts.get("state") != "Running" or not ts.get("name"):
        return ""
    rc, out, _e = _run([exe, "serve", "status"], timeout=8)
    return f"https://{ts['name']}/" if rc == 0 and ts["name"] in (out or "") else ""


