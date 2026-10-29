#@ MoveEye – Teil 258: Entwickler-Bereich (2.98.7). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# A small area only for the developer (Daniel). It is HIDDEN until it is switched on, and protected with its own PIN.
# What it shows is only about THIS device and is read-only - never the traffic of other people:
#   - the device's own open network connections (to where, which program, how much data) with a reverse-DNS name
#   - the names the device itself looked up (its own DNS questions, from the connections it holds)
#   - the data volume per network card (how much came in and went out since the start)
#   - the programs that listen on a port on this device
# No «sniffer» of foreign packets, no promiscuous / monitor mode, no password cracking, no scan of other devices.
# That keeps it on the right side of the law (Art. 143bis / 179novies StGB, data-protection act): the developer looks at
# his own machine, like `ss`, `netstat` or a router page do. Every time the area is opened and every look is written to the
# log (kind «dev»). Short-lived snapshots (the lists below) are kept at most 24 h in memory, never on disk.
# ----------------------------------------------------------------------------
import socket

DEV = {"token": "", "token_t": 0.0, "fails": [], "snaps": deque(maxlen=48)}   # snaps: (t, kind) - for the 24 h note only
DEV_TTL = 900.0                       # an unlock lasts 15 minutes
_DEV_IFACE_BASE = {}


def dev_available():
    """the area exists only when it was switched on (CFG.dev_area) - otherwise it is invisible everywhere"""
    return bool(CFG.get("dev_area"))


def dev_pin_ok(pin):
    h = CFG.get("dev_pin") or ""
    if not h or "$" not in h or not isinstance(pin, str):
        return False
    try:
        return hmac.compare_digest(_pin_hash(pin.strip(), h.split("$", 1)[0]), h)
    except Exception:
        return False


def dev_pin_set(new_pin, old_pin=""):
    new_pin = str(new_pin or "").strip()
    if CFG.get("dev_pin") and not dev_pin_ok(old_pin):
        return False, "wrong PIN"
    if new_pin and not re.fullmatch(r"\d{4,10}", new_pin):
        return False, "the PIN must have 4 to 10 digits"
    CFG["dev_pin"] = _pin_hash(new_pin) if new_pin else ""
    save_settings()
    log_event("dev", "Developer PIN " + ("set" if new_pin else "removed"))
    return True, ""


def dev_unlocked():
    return bool(DEV["token"]) and time.time() - DEV["token_t"] < DEV_TTL


def dev_unlock(pin, source="web"):
    now = time.time()
    DEV["fails"] = [t for t in DEV["fails"] if now - t < 600]
    if len(DEV["fails"]) >= 5:
        return False, "too many wrong PINs - try again in 10 minutes", ""
    if CFG.get("dev_pin") and not dev_pin_ok(pin):
        DEV["fails"].append(now)
        log_event("dev", f"Developer area: wrong PIN ({source})")
        return False, "wrong PIN", ""
    DEV["token"] = secrets.token_urlsafe(18); DEV["token_t"] = now
    log_event("dev", f"Developer area opened ({source})")
    return True, "", DEV["token"]


def dev_token_ok(tok):
    return dev_unlocked() and isinstance(tok, str) and tok and hmac.compare_digest(tok, DEV["token"])


def dev_lock():
    DEV["token"] = ""; DEV["token_t"] = 0.0


def _dev_note(kind):
    DEV["snaps"].append((time.time(), kind))


def _rev_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


_DEV_PROC_CACHE = {"t": 0.0, "map": {}}


def _dev_proc_map():
    """inode -> (pid, program) for the own sockets (from /proc), so a connection can show which program it belongs to.
    Only this device's own processes - the same a task manager shows."""
    now = time.time()
    if now - _DEV_PROC_CACHE["t"] < 2.0:
        return _DEV_PROC_CACHE["map"]
    m = {}
    try:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            fd = "/proc/%s/fd" % pid
            try:
                names = os.listdir(fd)
            except OSError:
                continue
            name = ""
            for f in names:
                try:
                    link = os.readlink(os.path.join(fd, f))
                except OSError:
                    continue
                if link.startswith("socket:["):
                    if not name:
                        try:
                            with open("/proc/%s/comm" % pid) as c:
                                name = c.read().strip()
                        except OSError:
                            name = "?"
                    m[link[8:-1]] = (pid, name)
    except OSError:
        pass
    _DEV_PROC_CACHE.update(t=now, map=m)
    return m


def _hx_ip(hx):
    """the little-endian hex address of /proc/net/tcp -> a readable IP"""
    if len(hx) == 8:
        b = bytes.fromhex(hx)
        return ".".join(str(x) for x in b[::-1])
    try:
        parts = [hx[i:i + 8] for i in range(0, 32, 8)]
        segs = []
        for p in parts:
            b = bytes.fromhex(p)[::-1]
            segs.append("%02x%02x" % (b[0], b[1])); segs.append("%02x%02x" % (b[2], b[3]))
        ip = ":".join(segs)
        import ipaddress as _ipa
        return str(_ipa.ip_address(int(_ipa.IPv6Address(ip))))
    except Exception:
        return hx


_TCP_STATES = {"01": "aktiv", "02": "SYN", "06": "wartet", "08": "wartet", "0A": "lauscht"}


def dev_connections():
    """the device's own TCP connections to the outside (established or listening), with program and reverse-DNS name.
    Read from /proc/net - the same data `ss` or `netstat` show. Only this machine."""
    _dev_note("connections")
    pm = _dev_proc_map()
    seen_names = {}
    out = []
    for fn in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(fn) as f:
                rows = f.read().splitlines()[1:]
        except OSError:
            continue
        for ln in rows[:4000]:
            p = ln.split()
            if len(p) < 10:
                continue
            la, lp = p[1].split(":"); ra, rp = p[2].split(":")
            st = p[3].upper(); rip = _hx_ip(ra); lport = int(lp, 16); rport = int(rp, 16)
            if st not in _TCP_STATES or (st != "0A" and rport == 0):
                continue
            pid, prog = pm.get(p[9], ("", ""))
            local = st == "0A" or rip in ("0.0.0.0", "::", "127.0.0.1", "::1")
            name = ""
            if not local and rip:
                name = seen_names.get(rip)
                if name is None:
                    name = _rev_dns(rip); seen_names[rip] = name
            out.append({"state": _TCP_STATES.get(st, st), "lport": lport, "rip": "" if st == "0A" else rip, "rport": rport,
                        "host": name, "prog": prog, "pid": pid, "listen": st == "0A", "local": local})
    out.sort(key=lambda x: (x["listen"], x["local"], x["host"] or x["rip"]))
    return out[:400]


def dev_dns():
    """the names the device itself reached (from its own open connections) - a reverse-DNS of the outside addresses,
    grouped. This is the device's own activity, not anybody else's."""
    _dev_note("dns")
    hosts = {}
    for c in dev_connections():
        if c["listen"] or c["local"] or not c["rip"]:
            continue
        key = c["host"] or c["rip"]
        e = hosts.setdefault(key, {"host": c["host"], "ip": c["rip"], "ports": set(), "progs": set()})
        e["ports"].add(c["rport"])
        if c["prog"]:
            e["progs"].add(c["prog"])
    res = [{"host": v["host"], "ip": v["ip"], "ports": sorted(v["ports"])[:8], "progs": sorted(v["progs"])} for v in hosts.values()]
    res.sort(key=lambda x: x["host"] or x["ip"])
    return res


def dev_ifaces():
    """data volume per network card since the start of the system (/proc/net/dev) - how much came in and went out.
    Only this device's own cards."""
    _dev_note("ifaces")
    out = []
    try:
        with open("/proc/net/dev") as f:
            rows = f.read().splitlines()[2:]
    except OSError:
        return out
    now = time.time()
    for ln in rows:
        if ":" not in ln:
            continue
        name, rest = ln.split(":", 1)
        name = name.strip()
        if name == "lo":
            continue
        v = rest.split()
        if len(v) < 16:
            continue
        rx, tx = int(v[0]), int(v[8])
        base = _DEV_IFACE_BASE.get(name)
        rate_rx = rate_tx = None
        if base and now - base[0] > 0.5:
            rate_rx = max(0, rx - base[1]) / (now - base[0])
            rate_tx = max(0, tx - base[2]) / (now - base[0])
        _DEV_IFACE_BASE[name] = (now, rx, tx)
        out.append({"name": name, "rx": rx, "tx": tx, "rx_rate": rate_rx, "tx_rate": rate_tx,
                    "up": int(v[3]) >= 0 and (rx > 0 or tx > 0)})
    out.sort(key=lambda x: -(x["rx"] + x["tx"]))
    return out


def dev_state(lang=None):
    """everything for the developer page (only if unlocked)"""
    cutoff = time.time() - 86400
    recent = sum(1 for t, _k in DEV["snaps"] if t > cutoff)
    return {"on": dev_available(), "has_pin": bool(CFG.get("dev_pin")), "unlocked": dev_unlocked(),
            "left": int(max(0, DEV_TTL - (time.time() - DEV["token_t"]))) if dev_unlocked() else 0,
            "looks_24h": recent, "host": socket.gethostname(), "uid": device_uid()}


DEV_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Developer</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:900px;margin:0 auto}
.warn-law{border:1px solid var(--line);border-left:4px solid #e9a23b;border-radius:12px;background:var(--panel);padding:12px 14px;margin:0 0 14px;font-size:13px;color:var(--mut)}
.dev-lock{max-width:420px;margin:30px auto;text-align:center}
.dev-lock input{font:inherit;text-align:center;letter-spacing:.3em;padding:12px;border-radius:12px;border:1px solid var(--line);background:var(--field);color:var(--txt);width:100%;margin:10px 0}
.dtabs{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0}
.dtabs button{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--txt);border-radius:999px;padding:9px 14px;cursor:pointer}
.dtabs button.on{background:var(--acc);border-color:var(--acc);color:#fff}
table.dt{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
table.dt th,table.dt td{text-align:left;padding:7px 9px;border-top:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
table.dt th{color:var(--mut);font-weight:600;font-size:12px}
.pill{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;background:var(--field);border:1px solid var(--line);margin:1px}
.bar{height:8px;border-radius:4px;background:var(--field);overflow:hidden;min-width:90px}
.bar i{display:block;height:100%;background:var(--acc)}
.dhead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.dhead .mut{font-size:12px}
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
  <div class="dhead"><h2 style="margin:0">🛠 <span data-i18n="Developer">Developer</span></h2>
    <span class="mut" id="dev-sub"></span>
    <button class="sec" id="dev-lockbtn" style="margin-left:auto" onclick="devLock()" hidden data-i18n="Lock">Lock</button></div>
  <div class="warn-law" data-i18n="dev-law">dev-law</div>
  <div id="dev-gate" class="dev-lock">
    <p id="dev-gate-msg" class="mut"></p>
    <input id="dev-pin" type="password" inputmode="numeric" autocomplete="off" placeholder="PIN">
    <div id="dev-pin2wrap" hidden><input id="dev-pin2" type="password" inputmode="numeric" autocomplete="off" placeholder="PIN"></div>
    <button id="dev-go" style="width:100%"></button>
    <p class="note" id="dev-note" style="min-height:1.3em"></p>
  </div>
  <div id="dev-body" hidden>
    <div class="dtabs">
      <button data-d="conns" class="on" onclick="devTab('conns')" data-i18n="Connections">Connections</button>
      <button data-d="dns" onclick="devTab('dns')" data-i18n="Reached names">Reached names</button>
      <button data-d="ifaces" onclick="devTab('ifaces')" data-i18n="Data volume">Data volume</button>
    </div>
    <div id="dev-out"></div>
    <p class="mut" id="dev-foot" style="margin-top:12px;font-size:12px"></p>
  </div>
</main>
<script>
/*COMMON*/
/*DEVDE*/
const $$ = s => [...document.querySelectorAll(s)];
let DTOK = "", DTAB = "conns", dtimer = null;
try { DTOK = sessionStorage.getItem("mw-dev") || ""; } catch (e) {}                 // this browser tab only
const dtokSave = v => { DTOK = v; try { v ? sessionStorage.setItem("mw-dev", v) : sessionStorage.removeItem("mw-dev"); } catch (e) {} };
function devSub(j) { const d = j.dev || {}; $("#dev-sub").textContent = d.host ? d.host + (d.unlocked ? " · " + t("open for") + " " + Math.round(d.left / 60) + " min" : "") : ""; }
async function devInit() {
  const r = await fetch("/api/dev", {cache: "no-store"}).then(x => x.ok ? x.json() : null).catch(() => null);
  if (!r || !r.ok) { document.querySelector("main").innerHTML = "<p class='mut'>" + t("The developer area is switched off.") + "</p>"; return; }
  devSub(r); devGate(r.dev);
}
function devGate(d) {
  const g = $("#dev-gate"), b = $("#dev-body");
  if (d.unlocked && DTOK) { g.hidden = true; b.hidden = false; $("#dev-lockbtn").hidden = false; devTab(DTAB); return; }
  g.hidden = false; b.hidden = true; $("#dev-lockbtn").hidden = true;
  const needSet = !d.has_pin;
  $("#dev-pin2wrap").hidden = !needSet;
  $("#dev-gate-msg").textContent = needSet ? t("Set a PIN for the developer area (4 to 10 digits).") : t("Enter the developer PIN.");
  $("#dev-go").textContent = needSet ? t("Set PIN") : t("Open");
  $("#dev-go").onclick = needSet ? devSetPin : devUnlock;
}
async function devSetPin() {
  const p1 = $("#dev-pin").value, p2 = $("#dev-pin2").value;
  if (p1 !== p2) { $("#dev-note").textContent = t("The two PINs are different."); return; }
  const r = await post("/api/dev", {action: "setpin", pin: p1, lang: LANG});
  if (!r.ok) { $("#dev-note").textContent = "⚠ " + (r.error || ""); return; }
  $("#dev-note").textContent = ""; devUnlock();
}
async function devUnlock() {
  const r = await post("/api/dev", {action: "unlock", pin: $("#dev-pin").value, lang: LANG});
  if (!r.ok) { $("#dev-note").textContent = "⚠ " + (r.error || ""); return; }
  dtokSave(r.token); $("#dev-pin").value = ""; $("#dev-pin2").value = ""; $("#dev-note").textContent = ""; devSub(r); devGate(r.dev);
}
async function devLock() { await post("/api/dev", {action: "lock", lang: LANG}); dtokSave(""); clearTimeout(dtimer); devInit(); }
function esc(s) { return String(s == null ? "" : s).replace(/[&<>]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;"}[c])); }
function fmtBytes(n) { const u = ["B", "kB", "MB", "GB", "TB"]; let i = 0; n = +n || 0; while (n >= 1024 && i < 4) { n /= 1024; i++; } return n.toFixed(n < 10 && i ? 1 : 0) + " " + u[i]; }
function devTab(k) {
  DTAB = k; $$(".dtabs button").forEach(b => b.classList.toggle("on", b.dataset.d === k));
  devLoad();
}
async function devLoad() {
  clearTimeout(dtimer);
  const r = await fetch("/api/dev/" + DTAB + "?token=" + encodeURIComponent(DTOK) + "&lang=" + LANG, {cache: "no-store"}).then(x => x.json()).catch(() => null);
  if (!r) return;
  if (r.error === "locked") { dtokSave(""); devInit(); return; }
  if (!r.ok) { $("#dev-out").innerHTML = "<p class='mut'>⚠ " + (r.error || "") + "</p>"; return; }
  devSub(r); render(r.items);
  if (r.dev) $("#dev-foot").textContent = t("Only this device, read-only.") + " · " + t("Looks in the last 24 h") + ": " + r.dev.looks_24h;
  dtimer = setTimeout(devLoad, 4000);
}
function render(items) {
  const o = $("#dev-out"); items = items || [];
  if (DTAB === "conns") {
    o.innerHTML = "<table class='dt'><tr><th>" + [t("State"), t("Program"), t("To"), t("Port")].join("</th><th>") + "</th></tr>"
      + items.map(c => "<tr><td>" + (c.listen ? "👂 " + t("listening") : c.local ? t("local") : esc(c.state)) + "</td><td>" + esc(c.prog || "–") + (c.pid ? " <span class='mut'>#" + c.pid + "</span>" : "")
        + "</td><td>" + (c.listen ? ":" + c.lport : esc(c.host || c.rip || "–")) + "</td><td>" + (c.listen ? "" : c.rport) + "</td></tr>").join("")
      + "</table>" + (items.length ? "" : "<p class='mut'>" + t("no connections") + "</p>");
  } else if (DTAB === "dns") {
    o.innerHTML = "<table class='dt'><tr><th>" + [t("Name"), t("Address"), t("Ports"), t("Program")].join("</th><th>") + "</th></tr>"
      + items.map(h => "<tr><td>" + esc(h.host || "–") + "</td><td class='mut'>" + esc(h.ip) + "</td><td>" + h.ports.map(p => "<span class='pill'>" + p + "</span>").join("")
        + "</td><td>" + h.progs.map(esc).join(", ") + "</td></tr>").join("")
      + "</table>" + (items.length ? "" : "<p class='mut'>" + t("nothing reached") + "</p>");
  } else {
    const max = Math.max(1, ...items.map(i => i.rx + i.tx));
    o.innerHTML = "<table class='dt'><tr><th>" + [t("Card"), t("Received"), t("Sent"), t("Now")].join("</th><th>") + "</th><th></th></tr>"
      + items.map(i => "<tr><td>" + esc(i.name) + "</td><td>" + fmtBytes(i.rx) + "</td><td>" + fmtBytes(i.tx)
        + "</td><td class='mut'>" + (i.rx_rate != null ? "↓ " + fmtBytes(i.rx_rate) + "/s · ↑ " + fmtBytes(i.tx_rate) + "/s" : "…")
        + "</td><td style='width:120px'><div class='bar'><i style='width:" + Math.round((i.rx + i.tx) / max * 100) + "%'></i></div></td></tr>").join("")
      + "</table>";
  }
}
(async () => { await initAppearance(); devInit(); })();
/*ALERTS*/
</script>
</body></html>
"""

DEV_DE = {"Developer": "Entwickler", "Lock": "Sperren", "Connections": "Verbindungen", "Reached names": "Erreichte Namen",
          "Data volume": "Datenmenge", "open for": "offen noch", "Set a PIN for the developer area (4 to 10 digits).": "Lege eine PIN für den Entwickler-Bereich fest (4 bis 10 Ziffern).",
          "Enter the developer PIN.": "Entwickler-PIN eingeben.", "Set PIN": "PIN festlegen", "Open": "Öffnen",
          "The two PINs are different.": "Die beiden PINs sind verschieden.", "The developer area is switched off.": "Der Entwickler-Bereich ist ausgeschaltet.",
          "State": "Zustand", "Program": "Programm", "To": "Ziel", "Port": "Port", "listening": "lauscht", "local": "lokal",
          "no connections": "keine Verbindungen", "Name": "Name", "Address": "Adresse", "Ports": "Ports", "nothing reached": "nichts erreicht",
          "Card": "Netzwerkkarte", "Received": "Empfangen", "Sent": "Gesendet", "Now": "Jetzt",
          "Only this device, read-only.": "Nur dieses Gerät, nur lesen.", "Looks in the last 24 h": "Abfragen in den letzten 24 h",
          "dev-law": "Nur dieses Gerät, nur lesen: eigene Verbindungen, erreichte Namen und die Datenmenge der eigenen Netzwerkkarten – wie «netstat» oder eine Router-Seite. MoveEye liest keine fremden Pakete mit und durchsucht keine fremden Geräte. Jede Nutzung wird ins Protokoll geschrieben. Bitte nur im eigenen Netz und auf eigenen Geräten verwenden."}


def dev_page():
    js = "Object.assign(I18N.de, " + json.dumps(DEV_DE, ensure_ascii=False) + ");" \
         + "I18N.en=I18N.en||{};Object.assign(I18N.en,{\"dev-law\":\"Only this device, read-only: its own connections, the names it reached and the data volume of its own network cards – like netstat or a router page. MoveEye does not capture other people's packets and does not scan other devices. Every use is written to the log. Please use it only in your own network and on your own devices.\"});"
    return render_page(DEV_PAGE, "dev").replace("/*DEVDE*/", js, 1)
