#@ MoveEye – Teil 573: «App-Schlüssel» für andere Programme und «Sicherheit an einem Ort» (Passwort, Benutzer, App-Schlüssel, Sicherheits-Check unter Einstellungen → Sicherheit; Web und Fenster). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (29.10.2026):
#  1  «App-Schlüssel» for other programs (Home Assistant, iPhone shortcuts, an older MoveEye in the device overview): since
#     2.98.23 (574) the password is refused over plain http from other devices. A key is made with a name, shown ONCE in full,
#     stored only as a hash in the settings folder (like the cookies of the trusted devices, 040 - same idea, for programs).
#     It works as header «X-MoveEye-Key: <key>», «Authorization: Bearer <key>», as «?key=<key>» (simple shortcuts) and as the
#     password of a Basic login (any user name: older MoveEye, Home Assistant «rest» with username/password) - also over http.
#     A key can do what the administrator does EXCEPT the security: password, users, trusted devices, app keys, shortcut key,
#     guest link, operator mode, settings file, «Log in only encrypted» and the update source (APPKEY_DENY_*). Wrong keys count
#     like wrong passwords (8 in 5 minutes per address -> 5 minutes blocked, auth() in 550). The shortcut addresses
#     /k/<key>/<action> (550) take an app key too.
#  2  «Sicherheit an einem Ort»: Settings → Security (own group, web and window) holds the encrypted login (574), the web
#     password, the users (+ trusted devices), the app keys and the security check (before: Tools). The old places keep a link.
# ----------------------------------------------------------------------------
_AK_CFG = {"app_keys": []}       # [{"id", "name", "h": sha256 of the key, "t0", "seen", "ip", "scope"}] - the key itself is never stored
# aufr (Konzept-Check, one key system): the old «shortcut key» (CFG shortcut_token, plain text, 2.95.27) is an app key now with
#   "scope": "shortcut" = it opens ONLY the shortcut addresses /k/<key>/<action> (arm, siren off, light, photo, status), like
#   before - not the rest of MoveEye. shortcut_migrate() takes an old key over once (as hash, the same key, the /k/ addresses
#   keep working); the card «iPhone shortcuts» (530) lists and makes these keys through /api/shortcut. Every normal app key
#   works on /k/ too.
for _k, _v in _AK_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
APPKEY_PREFIX = "me_"
APPKEY_MAX = 20
APPKEY = {"seen": {}, "logged": {}}            # id -> last use (memory; saved at most once an hour), ip -> time of the last log line
APPKEY_DENY_PATHS = {"/api/password", "/api/users", "/api/trusted", "/api/appkeys", "/api/shortcut", "/api/setup",
                     "/api/settings/import", "/api/settings/export", "/api/lock", "/api/dev"}
APPKEY_DENY_POST = {"/api/guest", "/api/ext"}  # reading is fine (links for Home Assistant), making new secret addresses is not
APPKEY_DENY_KEYS = {"login_https_only", "https_extra", "web_port", "lock_on", "lock_pin", "update_unsigned", "update_url",
                    "update_token", "protect_pin", "users", "trusted", "app_keys", "shortcut_token", "web_pw_hash", "guest_token", "ext_token"}
LOCK_DENY_PATHS.add("/api/appkeys")             # operator mode (390): no new keys either
# wraps: DEMO_BLOCK
DEMO_BLOCK = tuple(DEMO_BLOCK) + ("/api/appkeys",)
SIMPLE_SECTIONS.add("Security")                 # the password lives here now: always shown (also «Simple»)


def _appkey_hash(key):
    import hashlib
    return hashlib.sha256(("mw-appkey|" + str(key)).encode()).hexdigest()


def appkey_entries():
    """the stored keys (cleaned: a broken settings file never gives a key without hash)"""
    out = []
    for e in (CFG.get("app_keys") or [])[:APPKEY_MAX]:
        if isinstance(e, dict) and re.fullmatch(r"[0-9a-f]{64}", str(e.get("h", ""))) and re.fullmatch(r"[0-9a-f]{6,16}", str(e.get("id", ""))):
            out.append(e)
    return out


SHORTCUT_SCOPE = "shortcut"
SHORTCUT_KEY_NAME = "iPhone shortcuts"


def appkey_find(key, api=False):
    """the entry of this key, or None (compares the hashes in constant time). api=True (the login of 550): a key that only
    opens the shortcut addresses (scope «shortcut») counts as unknown there"""
    if not isinstance(key, str) or not (10 <= len(key) <= 120):
        return None
    h = _appkey_hash(key.strip())
    hit = None
    for e in appkey_entries():
        if hmac.compare_digest(str(e.get("h", "")), h):
            hit = e
    if api and hit is not None and hit.get("scope") == SHORTCUT_SCOPE:
        return None
    return hit


def appkey_from_request(req):
    """the key a program sends, or None (header, Bearer, ?key=, Basic password starting with «me_»)"""
    k = req.headers.get("X-MoveEye-Key")
    if k:
        return k.strip()
    a = str(req.headers.get("Authorization") or "")
    if a[:7].lower() == "bearer ":
        return a[7:].strip()
    k = req.args.get("key")
    if k:
        return k.strip()
    au = req.authorization
    if au is not None and str(getattr(au, "type", "basic") or "basic").lower() == "basic" and str(au.password or "").startswith(APPKEY_PREFIX):
        return str(au.password)
    return None


def appkey_seen(e, ip):
    now = time.time()
    APPKEY["seen"][e["id"]] = now
    if now - float(e.get("seen") or 0) > 3600:
        e["seen"] = int(now); e["ip"] = str(ip)[:45]
        save_settings()


def appkey_denied(path, method, d):
    """True = an app key may not do this (the security of MoveEye stays with the owner)"""
    if path in APPKEY_DENY_PATHS or path.startswith("/api/dev/"):
        return True
    if method == "POST" and path in APPKEY_DENY_POST:
        return True
    if method == "POST" and path in ("/api/set", "/api/text", "/api/quick") and isinstance(d, dict):
        k = str(d.get("key") or "")
        sec = {x[1] for x in list(TOGGLES) + list(SLIDERS) + list(TEXTS) if x and x[0] == "Security"}
        return k in APPKEY_DENY_KEYS or k in sec
    return False


def appkey_guard(req):
    """after a good key: None, or the 403 answer for the security functions"""
    d = req.get_json(force=True, silent=True) if req.method == "POST" else None
    if not appkey_denied(req.path, req.method, d):
        return None
    L = norm_lang((d.get("lang") if isinstance(d, dict) else None) or req.args.get("lang") or CFG["lang"])
    return _seclogin_json({"ok": False, "error": tr("An app key cannot change the password, the users, the app keys or the security settings", L)}, 403)


def appkey_refused(req, ip):
    """a wrong or blocked key: 401 without «WWW-Authenticate» (no password question in a browser), logged once a minute"""
    now = time.time()
    if now - APPKEY["logged"].get(ip, 0) > 60:
        APPKEY["logged"][ip] = now
        if len(APPKEY["logged"]) > 200:
            APPKEY["logged"].clear()
        log_event("web", f"Wrong or blocked app key from {ip} ({req.path[:40]})")
    L = norm_lang(req.args.get("lang") or CFG["lang"])
    return _seclogin_json({"ok": False, "error": tr("unknown or blocked app key", L)}, 401)


def appkey_list():
    out = []
    for e in appkey_entries():
        seen = max(float(e.get("seen") or 0), float(APPKEY["seen"].get(e["id"], 0)))
        out.append({"id": e["id"], "name": e.get("name") or "?", "t0": int(e.get("t0") or 0), "seen": int(seen), "ip": e.get("ip") or "",
                    "scope": e.get("scope") or ""})
    return out


def appkey_create(name, who="web", scope=""):
    """(ok, error, key): the key is only returned here - once. scope «shortcut»: only the shortcut addresses /k/…"""
    name = re.sub(r"[\x00-\x1f<>]", "", str(name or "")).strip()[:40]
    if not name:
        return False, "give the key a name (e.g. Home Assistant)", ""
    lst = appkey_entries()
    if len(lst) >= APPKEY_MAX:
        return False, "at most 20 app keys", ""
    if any(str(e.get("name", "")).lower() == name.lower() for e in lst):
        return False, "this name exists already", ""
    key = APPKEY_PREFIX + secrets.token_urlsafe(24)
    now = int(time.time())
    e = {"id": secrets.token_hex(4), "name": name, "h": _appkey_hash(key), "t0": now, "seen": 0, "ip": ""}
    if scope == SHORTCUT_SCOPE:
        e["scope"] = SHORTCUT_SCOPE
    lst.append(e)
    CFG["app_keys"] = lst
    save_settings_now()
    log_event("web", f"{who}: app key «{name}» made")
    return True, "", key


def appkey_revoke(kid, who="web"):
    lst = appkey_entries()
    e = next((x for x in lst if x["id"] == str(kid or "")), None)
    if e is None:
        return False, "unknown app key"
    CFG["app_keys"] = [x for x in lst if x is not e]
    APPKEY["seen"].pop(e["id"], None)
    save_settings_now()
    log_event("web", f"{who}: app key «{e.get('name')}» blocked")
    return True, ""


# ---- the shortcut keys (before: CFG shortcut_token in plain text) ----------------------------------------------------------
def shortcut_migrate(cfg_in):
    """settings of 2.98.36 and older: the plain shortcut key becomes an app key «iPhone shortcuts» (scope shortcut, only its
    hash is kept). The same key keeps working on /k/<key>/…; nothing happens when it was taken over already."""
    if not isinstance(cfg_in, dict):
        return []
    tok = str(cfg_in.get("shortcut_token") or "").strip()
    if len(tok) < 20:
        return []
    lst = appkey_entries()
    h = _appkey_hash(tok)
    if any(hmac.compare_digest(str(e.get("h", "")), h) for e in lst):
        return []
    if len(lst) >= APPKEY_MAX:
        lst = lst[:APPKEY_MAX - 1]                     # (never happens in practice: 20 keys) - the shortcut key must not get lost
    names = {str(e.get("name", "")).lower() for e in lst}
    nm0 = tr(SHORTCUT_KEY_NAME)                       # in the language of the device
    name = nm0 if nm0.lower() not in names else nm0 + " (2)"
    lst.append({"id": secrets.token_hex(4), "name": name, "h": h, "t0": int(time.time()), "seen": 0, "ip": "", "scope": SHORTCUT_SCOPE})
    CFG["app_keys"] = lst
    try:
        save_settings()                               # the plain key is gone from the file with the next save (MIGRATE_ONLY)
    except Exception:
        pass
    return ["shortcut key -> app key «" + name + "» (only the shortcut addresses /k/, stored as hash)"]


def shortcut_state(base):
    """/api/shortcut GET: the keys that work on /k/ (shortcut keys first, then the other app keys) and the keywords"""
    keys = appkey_list()
    sc = [k for k in keys if k["scope"] == SHORTCUT_SCOPE]
    return {"ok": True, "on": bool(keys), "base": base, "keys": sc, "other": [k["name"] for k in keys if k["scope"] != SHORTCUT_SCOPE],
            "actions": [a for a, _n in QR_SHORTCUTS],
            "prefix": msg_keyword("person").split("-")[0] if msg_keyword("person") else "MW",
            "keywords": {k: msg_keyword(k) or ("MW-" + v) for k, v in MSG_KEYWORDS.items()}}


def shortcut_action(d, who, plain_req=None):
    """/api/shortcut POST {action: new | off}: new = one more shortcut key (shown once, like every app key); off = block all
    shortcut keys. -> (reply dict, http code)"""
    a = d.get("action"); lang = norm_lang(d.get("lang"))
    if a == "new":
        if plain_req is not None and seclogin_plain(plain_req):     # like every app key: never unencrypted through the network (574)
            url = seclogin_url(plain_req).split("/api/")[0] + "/"
            return {"ok": False, "error": tr("For your safety an app key can only be made over the secure page", lang) + ": " + url, "https": url}, 403
        names = {k["name"].lower() for k in appkey_list()}
        nm = tr(SHORTCUT_KEY_NAME, lang)
        n = 2
        while nm.lower() in names and n < 30:
            nm = tr(SHORTCUT_KEY_NAME, lang) + f" ({n})"; n += 1
        ok, err, key = appkey_create(nm, who, SHORTCUT_SCOPE)
        return {"ok": ok, "error": tr_err(err, lang) if err else None, "key": key, "name": nm}, 200 if ok else 400
    if a == "off":
        n = 0
        for k in appkey_list():
            if k["scope"] == SHORTCUT_SCOPE:
                appkey_revoke(k["id"], who); n += 1
        return {"ok": True, "n": n}, 200
    return {"ok": False, "error": tr_err("unknown action", lang)}, 400


# ---- the security check (300) translated on the server: the same lines for the web page and the window --------------------
def seccheck_start():
    T = TOOLS["sec"]
    if T.get("running"):
        return False

    def run():
        try:
            security_check()
        finally:
            T["running"] = False
    T["running"] = True
    threading.Thread(target=run, daemon=True, name="tool-sec").start()
    return True


def seccheck_state(lang=None):
    T = TOOLS["sec"]
    items = [{"level": it.get("level", "info"), "text": (tr(it.get("text", ""), lang) + (" " + str(it["arg"]) if it.get("arg") else "")).strip(),
              "tip": tr(it["tip"], lang) if it.get("tip") else ""} for it in (T.get("items") or [])]
    nb = sum(1 for x in items if x["level"] == "bad"); nw = sum(1 for x in items if x["level"] == "warn")
    return {"ok": True, "running": bool(T.get("running")), "t": T.get("t") or 0, "items": items, "bad": nb, "warn": nw}


def appkey_routes(app, reply, body):
    """the addresses (called once by the web server, 550)"""
    from flask import request, g

    @app.route("/api/appkeys", methods=["GET", "POST"])
    def api_appkeys():
        if getattr(g, "role", "admin") != "admin" or getattr(g, "appkey", None):
            return reply({"ok": False, "error": "not allowed"}, 403)
        if request.method == "GET":
            return reply({"ok": True, "keys": appkey_list(), "pw": web_pw_active(), "plain": seclogin_plain(request)})
        d = body(); lang = norm_lang(d.get("lang")); a = d.get("action")
        who = getattr(g, "user", "") or "admin"
        if a == "create":
            if seclogin_plain(request):                # the key would go unencrypted through the network (574)
                url = seclogin_url(request).split("/api/")[0] + "/"
                return reply({"ok": False, "error": tr("For your safety an app key can only be made over the secure page", lang) + ": " + url, "https": url}, 403)
            ok, err, key = appkey_create(d.get("name"), who)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "key": key, "keys": appkey_list()}, 200 if ok else 400)
        if a == "revoke":
            ok, err = appkey_revoke(d.get("id"), who)
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "keys": appkey_list()}, 200 if ok else 400)
        return reply({"ok": False, "error": tr_err("unknown action", lang)}, 400)

    @app.route("/api/seccheck", methods=["GET", "POST"])
    def api_seccheck():
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        lang = norm_lang(request.args.get("lang") or (body().get("lang") if request.method == "POST" else None))
        if request.method == "POST":
            if seccheck_start():
                log_event("web", f"Security check started ({request.remote_addr or '?'})")
        return reply(seccheck_state(lang))


# ---- web page: the section «Security» (530 calls secExtras; this script fills it) -------------------------------------------
SECPANEL_JS = r"""
<script>
(function () {
  try { const D = /*AKDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  try { if (typeof LANG !== "undefined" && LANG && typeof applyI18n === "function") applyI18n(); } catch (e) {}   // the static texts (530 ran first)
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const d2 = n => { if (!n) return "–"; const d = new Date(n * 1000); return d.toLocaleDateString() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); };
  const head = (box, txt) => { const h = E("div", "", txt); h.style.cssText = "font-weight:700;margin:14px 0 4px"; box.appendChild(h); return h; };
  const copy = (txt, done) => { const ok = () => { if (typeof toast === "function") toast("✓ " + T("Copied")); if (done) done(); };
    try { navigator.clipboard.writeText(txt).then(ok, () => { prompt(T("Copy"), txt); }); } catch (e) { prompt(T("Copy"), txt); } };
  // -- web password (the dialog of 530) --
  function pwBlock(box) {
    head(box, "🔒 " + T("Web password"));
    const info = E("div", "mut"); info.id = "pw-info"; box.appendChild(info);
    const b = E("button", "sec", "🔒 " + T("Set / change the web password")); b.type = "button"; b.style.marginTop = "6px";
    b.onclick = () => { if (typeof pwDialog === "function") pwDialog(false); }; box.appendChild(b);
  }
  // -- app keys --
  async function akLoad(box) {
    let j = null; try { j = await (await fetch("/api/appkeys", {cache: "no-store"})).json(); } catch (e) { return; }
    box.textContent = "";
    head(box, "🔑 " + T("App keys"));
    box.appendChild(E("div", "mut", T("ak-note")));
    if (!j || !j.ok) { box.appendChild(E("div", "err", "⚠ " + ((j && j.error) || "error"))); return; }
    if (!j.pw) box.appendChild(E("div", "mut", "ℹ " + T("Without a web password every program can use MoveEye anyway - keys are needed only with a password.")));
    (j.keys || []).forEach(k => {
      const r = E("div", "sens-card"), r1 = E("div", "row"); r1.style.gap = "8px";
      const tx = E("div", ""); tx.style.flex = "1";
      tx.append(E("b", "", "🔑 " + k.name), E("div", "mut", (k.scope === "shortcut" ? "📲 " + T("only the shortcut addresses /k/") + " · " : "") + T("made") + " " + d2(k.t0) + " · " + T("last used") + " " + (k.seen ? d2(k.seen) + (k.ip ? " · " + k.ip : "") : T("never"))));
      const bl = E("button", "red", "⛔ " + T("Block")); bl.type = "button";
      bl.onclick = async () => { if (!confirm(T("Block this key? Programs that use it get no access any more.") + "\n" + k.name)) return;
        const r_ = await post("/api/appkeys", {action: "revoke", id: k.id, lang: L()}); if (!r_.ok) toast("⚠ " + (r_.error || "error")); akLoad(box); };
      r1.append(tx, bl); r.appendChild(r1); box.appendChild(r);
    });
    if (!(j.keys || []).length) box.appendChild(E("div", "mut", T("No app keys yet.")));
    const add = E("div", "row"); add.style.cssText = "gap:8px;margin-top:8px";
    const nm = E("input"); nm.type = "text"; nm.maxLength = 40; nm.placeholder = T("Name (e.g. Home Assistant)"); nm.style.flex = "1"; nm.id = "ak-name";
    const ab = E("button", "", "+ " + T("Make an app key")); ab.type = "button"; ab.id = "ak-add";
    const er = E("div", "err"), out = E("div", "");
    ab.onclick = async () => { er.textContent = ""; const r_ = await post("/api/appkeys", {action: "create", name: nm.value, lang: L()});
      if (!r_.ok) { er.textContent = "⚠ " + (r_.error || "error"); if (r_.https) { const a = E("a", "btn sec", "🔒 " + T("To the secure page")); a.href = r_.https; a.style.cssText = "display:inline-block;margin-top:6px"; er.appendChild(E("br")); er.appendChild(a); } return; }
      akShow(box, r_.key, nm.value); };
    add.append(nm, ab); box.append(add, er, out);
    if (j.plain) box.appendChild(E("div", "mut", "🔓 " + T("New keys only over the secure page (https) - the key would go unencrypted through the network.")));
    const ex = E("details", ""); ex.style.marginTop = "8px"; ex.appendChild(E("summary", "", T("Example: Home Assistant and iPhone shortcuts")));
    const base = location.protocol + "//" + location.host;
    const pre = E("pre", ""); pre.style.cssText = "white-space:pre-wrap;font-size:12px;overflow:auto;padding:8px;border:1px solid var(--line);border-radius:8px";
    pre.textContent = "# Home Assistant (configuration.yaml)\nrest:\n  - resource: " + base + "/api/state\n    headers:\n      X-MoveEye-Key: !secret moveeye_key\n    sensor:\n      - name: MoveEye Personen\n        value_template: \"{{ value_json.persons }}\"\n\n"
      + "# " + T("iPhone shortcut «Get contents of URL»") + "\n" + base + "/k/me_…/status\n" + base + "/api/state?key=me_…";
    ex.appendChild(pre); box.appendChild(ex);
  }
  function akShow(box, key, name) {
    const ov = E("div", "sx-ak"); ov.style.cssText = "position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:16px";
    const c = E("div", "card"); c.style.cssText = "max-width:440px;width:100%;text-align:left"; ov.appendChild(c);
    c.appendChild(E("h3", "", "🔑 " + T("App key") + " «" + name + "»"));
    c.appendChild(E("div", "", T("Copy the key now - it is shown only this one time. MoveEye keeps only a fingerprint of it.")));
    const k = E("code", ""); k.id = "ak-key"; k.textContent = key; k.style.cssText = "display:block;margin:10px 0;padding:10px;border:1px solid var(--line);border-radius:8px;word-break:break-all;font-size:14px;user-select:all";
    c.appendChild(k);
    const bb = E("div", "btns"), cp = E("button", "", "📋 " + T("Copy")), cl = E("button", "sec", T("Done")); cp.type = cl.type = "button";
    cp.onclick = () => copy(key); cl.onclick = () => { ov.remove(); akLoad(box); }; bb.append(cp, cl); c.appendChild(bb);
    if (window.qrBtn) { const qb = qrBtn(key, T("App key") + " «" + name + "»", {secret: true}); qb.id = "ak-qr"; bb.insertBefore(qb, cl); }   // 585: once, while it is shown
    document.body.appendChild(ov);
  }
  // -- security check (before: Tools) --
  async function scPaint(box, j) {
    const list = box.querySelector(".sc-list"), btn = box.querySelector(".sc-btn"); list.textContent = "";
    btn.disabled = !!j.running; btn.textContent = j.running ? T("running…") : "🛡 " + T("Check now");
    (j.items || []).forEach(it => { const r = E("div", ""); r.style.margin = "4px 0";
      r.append(E("span", "", it.level === "bad" ? "❌ " : it.level === "warn" ? "⚠️ " : it.level === "ok" ? "✅ " : "ℹ️ "), E("span", "", it.text));
      if (it.tip) { r.appendChild(E("br")); r.appendChild(E("span", "mut", it.tip)); } list.appendChild(r); });
    if (j.t && !j.running) list.appendChild(E("div", "mut", d2(j.t)));
    if (j.running) setTimeout(async () => { try { scPaint(box, await (await fetch("/api/seccheck?lang=" + L(), {cache: "no-store"})).json()); } catch (e) {} }, 1500);
  }
  function scBlock(box) {
    head(box, "🛡 " + T("Security check"));
    box.appendChild(E("div", "mut", T("What can be reached from the network or the internet, and what is risky.")));
    const b = E("button", "sec sc-btn", "🛡 " + T("Check now")); b.type = "button"; b.style.marginTop = "6px";
    b.onclick = async () => { b.disabled = true; try { scPaint(box, await (await fetch("/api/seccheck", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({lang: L()})})).json()); } catch (e) { b.disabled = false; } };
    box.append(b, E("div", "sc-list"));
    fetch("/api/seccheck?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(j => scPaint(box, j)).catch(() => {});
  }
  window.secPanel = function (d) {
    if (d.querySelector("#secpanel")) return;
    const p = E("div", "auxbox"); p.id = "secpanel";
    const pw = E("div", "l-hide"), us = E("div", "l-hide"), ak = E("div", "l-hide"), sc = E("div", "");
    pwBlock(pw);
    head(us, "👥 " + T("Users")); const ub = E("div", ""); ub.id = "users-box"; us.appendChild(ub);
    p.append(pw, us, ak, sc); d.appendChild(p);
    scBlock(sc); akLoad(ak);
    try { if (typeof MAINSW === "object") MAINSW["grp:security"] = MAINSW["sec:Security"] = (c, s) => !!s.pw_set; } catch (e) {}
  };
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", SECPANEL_JS + "</body>", 1)


# ---- window (Tkinter): the same in Settings → Security ------------------------------------------------------------------------
def _ak_tk_build_section(self, sec, sbody, settings_parent=None):
    _ak_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != "Security":
        return
    try:
        _ak_tk_security(self, sbody)
    except Exception as e:
        log_event("sys", f"Window: security section: {e}"[:160])


def _ak_tk_line(sbody, text):
    tk.Frame(sbody, bg=C["line"], height=1).pack(fill="x", pady=(10, 6))
    tk.Label(sbody, text=text.upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").pack(fill="x")


def _ak_tk_security(app, sbody):
    ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                  highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
    if CFG["lock_on"]:                               # operator mode: password, users and keys are off limits (like before)
        ttk.Label(sbody, text="🔐 " + tr("Operator mode is on"), style="Mut.TLabel").pack(anchor="w", pady=(8, 0))
    else:
        # web password (moved here from «Setup»)
        _ak_tk_line(sbody, tr("Web password"))
        app.pw_var = tk.StringVar()
        tk.Entry(sbody, textvariable=app.pw_var, show="•", **ent_kw).pack(fill="x", pady=(4, 0))
        bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
        ttk.Button(bf, text=tr("Set password"), command=lambda: app._pw(True)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text=tr("Remove password"), command=lambda: app._pw(False)).pack(side="left", expand=True, fill="x")
        app.status_labels["Web password"] = ttk.Label(sbody, text=tr("Web password") + ": " + (tr("set") if web_pw_active() else "–"),
                                                     style="Mut.TLabel", wraplength=330, justify="left")
        app.status_labels["Web password"].pack(anchor="w", pady=(4, 0))
        # users
        _ak_tk_line(sbody, tr("Users"))
        uf = tk.Frame(sbody, bg=C["panel"]); uf.pack(fill="x")
        _ak_tk_users(app, uf)
        # app keys
        _ak_tk_line(sbody, tr("App keys"))
        ttk.Label(sbody, text=tr("ak-note"), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(2, 0))
        kf = tk.Frame(sbody, bg=C["panel"]); kf.pack(fill="x")
        _ak_tk_keys(app, kf)
    app.status_labels["App keys"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
    app.status_labels["App keys"].pack(anchor="w", pady=(4, 0))
    # security check (before: only on the web page Tools)
    _ak_tk_line(sbody, tr("Security check"))
    ttk.Label(sbody, text=tr("What can be reached from the network or the internet, and what is risky."), style="Mut.TLabel",
              wraplength=330, justify="left").pack(anchor="w", pady=(2, 0))
    res = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")

    def paint():
        try:
            if not res.winfo_exists():
                return
        except Exception:
            return
        s = seccheck_state()
        sym = {"bad": "✗ ", "warn": "⚠ ", "ok": "✓ "}
        lines = [sym.get(x["level"], "· ") + x["text"] + (("\n    " + x["tip"]) if x["tip"] else "") for x in s["items"]]
        res.config(text=(tr("running…") + "\n" if s["running"] else "") + "\n".join(lines)
                   + (("\n" + datetime.fromtimestamp(s["t"]).strftime("%d.%m. %H:%M")) if s["t"] and not s["running"] else ""))
        if s["running"]:
            app.root.after(1500, paint)
    ttk.Button(sbody, text="🛡 " + tr("Check now"), command=lambda: (seccheck_start(), app.root.after(300, paint))).pack(fill="x", pady=(6, 0))
    res.pack(anchor="w", pady=(4, 0))
    paint()


def _ak_tk_users(app, box):
    for w in box.winfo_children():
        w.destroy()
    if not web_pw_active():
        ttk.Label(box, text="⚠ " + tr("set the web password first (it is the administrator)"), style="Mut.TLabel", wraplength=330).pack(anchor="w", pady=(4, 0))
        return
    roles = {"operate": tr("operate"), "view": tr("view only")}

    def act(d):
        ok, err = users_action(d, "window")
        if not ok:
            app._status("App keys", "⚠ " + tr_err(err))
        _ak_tk_users(app, box)
    for u in CFG["users"]:
        r = tk.Frame(box, bg=C["panel"]); r.pack(fill="x", pady=(4, 0))
        tk.Label(r, text="👤 " + u["name"] + " · " + roles.get(u["role"], u["role"]), bg=C["panel"], fg=C["txt"], anchor="w").pack(side="left", fill="x", expand=True)
        ttk.Button(r, text="✕", width=3, command=lambda n=u["name"]: act({"action": "remove", "name": n})).pack(side="right")
    ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat", highlightthickness=1, highlightbackground=C["line"])
    nv, pv = tk.StringVar(), tk.StringVar()
    f = tk.Frame(box, bg=C["panel"]); f.pack(fill="x", pady=(6, 0))
    tk.Entry(f, textvariable=nv, width=12, **ent_kw).pack(side="left", fill="x", expand=True)
    tk.Entry(f, textvariable=pv, width=12, show="•", **ent_kw).pack(side="left", fill="x", expand=True, padx=(4, 0))
    rc = ttk.Combobox(box, state="readonly", values=[roles["operate"], roles["view"]]); rc.current(0); rc.pack(fill="x", pady=(4, 0))
    ttk.Button(box, text="+ " + tr("Add user") + "  (" + tr("Name") + " · " + tr("Password (6–64)") + ")",
               command=lambda: act({"action": "add", "name": nv.get(), "password": pv.get(), "role": "operate" if rc.current() == 0 else "view"})).pack(fill="x", pady=(4, 0))


def _ak_tk_keys(app, box):
    for w in box.winfo_children():
        w.destroy()
    for k in appkey_list():
        r = tk.Frame(box, bg=C["panel"]); r.pack(fill="x", pady=(4, 0))
        seen = datetime.fromtimestamp(k["seen"]).strftime("%d.%m. %H:%M") if k["seen"] else tr("never")
        tk.Label(r, text="🔑 " + k["name"] + ("  ·  " + tr("only the shortcut addresses /k/") if k["scope"] == SHORTCUT_SCOPE else "") + "\n" + tr("made") + " " + datetime.fromtimestamp(k["t0"]).strftime("%d.%m.%Y") + " · " + tr("last used") + " " + seen,
                 bg=C["panel"], fg=C["txt"], anchor="w", justify="left").pack(side="left", fill="x", expand=True)

        def block(kid=k["id"], name=k["name"]):
            from tkinter import messagebox
            if messagebox.askyesno("MoveEye", tr("Block this key? Programs that use it get no access any more.") + "\n" + name, parent=app.root):
                appkey_revoke(kid, "window"); _ak_tk_keys(app, box)
        ttk.Button(r, text="⛔ " + tr("Block"), command=block).pack(side="right")
    nv = tk.StringVar()
    tk.Entry(box, textvariable=nv, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat", highlightthickness=1,
             highlightbackground=C["line"]).pack(fill="x", pady=(6, 0))

    def make():
        ok, err, key = appkey_create(nv.get(), "window")
        if not ok:
            app._status("App keys", "⚠ " + tr_err(err)); return
        _ak_tk_keys(app, box); _ak_tk_show(app, nv.get().strip(), key)
    ttk.Button(box, text="+ " + tr("Make an app key") + "  (" + tr("Name (e.g. Home Assistant)") + ")", command=make).pack(fill="x", pady=(4, 0))


def _ak_tk_show(app, name, key):
    win = tk.Toplevel(app.root); win.title("MoveEye"); win.configure(bg=C["panel"]); win.transient(app.root)
    tk.Label(win, text="🔑 " + tr("App key") + " «" + name + "»", bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
    tk.Label(win, text=tr("Copy the key now - it is shown only this one time. MoveEye keeps only a fingerprint of it."), bg=C["panel"], fg=C["mut"],
             wraplength=380, justify="left").pack(anchor="w", padx=14)
    e = tk.Entry(win, bg=C["field"], fg=C["txt"], relief="flat", width=44); e.insert(0, key); e.config(state="readonly"); e.pack(fill="x", padx=14, pady=8)

    def cp():
        win.clipboard_clear(); win.clipboard_append(key); app._status("App keys", "✓ " + tr("Copied"))
    bf = tk.Frame(win, bg=C["panel"]); bf.pack(fill="x", padx=14, pady=(0, 12))
    ttk.Button(bf, text="📋 " + tr("Copy"), command=cp).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="▦ QR", command=lambda: qr_tk_dialog(win, key, tr("App key") + " «" + name + "»", True)).pack(side="left", padx=(0, 4))   # 585
    ttk.Button(bf, text=tr("Done"), command=win.destroy).pack(side="left", expand=True, fill="x")


_ak_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _ak_tk_build_section


# ---- self-test ----------------------------------------------------------------------------------------------------------------
def appkey_selftest():
    keep = (list(CFG.get("app_keys") or []), CFG.get("lang"))
    try:
        CFG["app_keys"] = []
        _save, globals()["save_settings_now"] = globals()["save_settings_now"], lambda: None
        try:
            ok, err, key = appkey_create("Home Assistant", "test")
            assert ok and key.startswith(APPKEY_PREFIX) and len(key) > 30
            assert key not in json.dumps(CFG["app_keys"]), "the key itself must never be stored"
            assert appkey_find(key) and appkey_find(key)["name"] == "Home Assistant" and appkey_find(key + "x") is None and appkey_find("") is None
            assert not appkey_create("home assistant", "test")[0], "the same name twice"
            for p in ("/api/password", "/api/users", "/api/appkeys", "/api/trusted", "/api/settings/import", "/api/setup"):
                assert appkey_denied(p, "POST", {}), p
            assert appkey_denied("/api/set", "POST", {"key": "login_https_only", "value": False})
            assert appkey_denied("/api/set", "POST", {"key": "update_unsigned", "value": True})
            assert not appkey_denied("/api/arm", "POST", {}) and not appkey_denied("/api/state", "GET", None)
            assert not appkey_denied("/api/set", "POST", {"key": "sensitivity", "value": 50})
            kid = appkey_find(key)["id"]
            assert appkey_revoke(kid, "test")[0] and appkey_find(key) is None
            # aufr: the old plain shortcut key becomes an app key (hash), the same key keeps working on /k/, not for the API
            old = "Ab3_" + "x" * 28
            did = shortcut_migrate({"shortcut_token": old})
            assert did and shortcut_migrate({"shortcut_token": old}) == [], "taken over only once"
            e_ = appkey_find(old)
            assert e_ and e_["scope"] == SHORTCUT_SCOPE and old not in json.dumps(CFG["app_keys"]) and appkey_find(old, api=True) is None
            assert "shortcut_token" not in CFG and "shortcut_token" in MIGRATE_ONLY
            r_, c_ = shortcut_action({"action": "new"}, "test")
            assert c_ == 200 and appkey_find(r_["key"])["scope"] == SHORTCUT_SCOPE and len(shortcut_state("x")["keys"]) == 2
            assert shortcut_action({"action": "off"}, "test")[0]["n"] == 2 and appkey_find(old) is None
        finally:
            globals()["save_settings_now"] = _save
        for k_ in ("ak-note", "App keys", "Block", "An app key cannot change the password, the users, the app keys or the security settings"):
            assert tr(k_, "de") != k_ and tr(k_, "fr") != k_, "not translated: " + k_
        assert "/*AKDE*/" not in WEB_PAGE and "secPanel" in WEB_PAGE
    finally:
        CFG["app_keys"], CFG["lang"] = keep
    return True


SELFTEST_EXTRA.append(("App keys (hash only, no security changes)", appkey_selftest))
