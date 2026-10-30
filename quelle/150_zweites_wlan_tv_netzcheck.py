#@ Motion Watch – Teil 150: zweites WLAN, USB-Tethering, TV-Anzeige, Netz-Check, WLAN-Wächter. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Second Wi-Fi adapter (USB stick): one adapter makes the own Wi-Fi, the other one joins a known network (campsite, phone)
# -> repeater: the devices in the own Wi-Fi have internet (NetworkManager "shared" does the routing). Also: automatic change
# to another known network when the internet is gone, devices in the own Wi-Fi without internet (cameras), and a guard
# that listens for Wi-Fi jamming (deauthentication attacks) when the stick can listen ("monitor mode").
# ----------------------------------------------------------------------------
DUAL = {"on": False, "ap": "", "up": "", "adapters": [], "t": 0.0, "msg": "", "log": [], "sig": [], "drops": [], "unstable": False,
        "switch_t": 0.0, "offline_since": None, "iso": "", "iso_msg": ""}
WGUARD = {"state": "off", "iface": "", "phy": "", "msg": "", "deauth_min": [], "deauth_now": 0, "all_now": 0, "frames": 0,
          "last_alarm": 0.0, "alarms": [], "count_on": False, "count_now": None, "count_hist": [], "chan": None}
WIFI_CHIPS = {"brcmfmac": ("Broadcom (built in)", ""),
              "mt76x2u": ("MediaTek MT7612U", "very good: own Wi-Fi, 5 GHz and listening (monitor) work"),
              "mt7921u": ("MediaTek MT7921AU (Wi-Fi 6)", "very good: own Wi-Fi, 5 GHz and listening (monitor) work"),
              "mt76x0u": ("MediaTek MT7610U", "good: 5 GHz and listening (monitor) work"),
              "mt7601u": ("MediaTek MT7601U", "simple stick: only 2.4 GHz"),
              "rt2800usb": ("Ralink RT5370 / RT3070", "only 2.4 GHz, listening (monitor) works"),
              "ath9k_htc": ("Atheros AR9271", "only 2.4 GHz, listening (monitor) works"),
              "rtl8xxxu": ("Realtek (rtl8xxxu)", "simple driver: no own Wi-Fi, no listening"),
              "r8188eu": ("Realtek RTL8188EU", "simple driver: no listening"),
              "rtw88_8821cu": ("Realtek RTL8811CU / RTL8821CU", "listening (monitor) mostly not possible"),
              "rtw88_8822bu": ("Realtek RTL8812BU / RTL8822BU", "listening (monitor) mostly not possible"),
              "rtw88_8723du": ("Realtek RTL8723DU", "only 2.4 GHz"),
              "rtl88xxau": ("Realtek RTL8812AU / RTL8821AU (extra driver)", "extra driver needed"),
              "8812au": ("Realtek RTL8812AU (extra driver)", "extra driver needed"),
              "88XXau": ("Realtek RTL8812AU / RTL8821AU (extra driver)", "extra driver needed")}


def _rd(p):
    try:
        with open(p) as f:
            return f.read().strip()
    except OSError:
        return ""


def _iw_phy(phy):
    """What the radio can do: kinds of use (AP = own Wi-Fi, monitor = listening), 5 GHz."""
    if not phy or shutil.which("iw") is None:
        return [], False, ""
    code, out, _e = _run(["iw", "phy", phy, "info"], 6)
    if code != 0:
        return [], False, ""
    modes, in_modes = [], False
    for ln in out.splitlines():
        s = ln.strip()
        if s.startswith("Supported interface modes"):
            in_modes = True; continue
        if in_modes:
            if s.startswith("* "):
                modes.append(s[2:].strip())
            else:
                in_modes = False
    five = bool(re.search(r"\b5[1-8]\d\d(\.\d+)? MHz \[\d+\](?![^\n]*disabled)", out))
    comb = ""
    m = re.search(r"valid interface combinations:(.*?)(?:\n\t[A-Z]|\Z)", out, re.S)
    if m:
        comb = " ".join(m.group(1).split())[:200]
    return modes, five, comb


def wifi_adapters():
    out = []
    for i in _wifi_ifaces():
        if i.startswith("mwmon"):
            continue
        base = f"/sys/class/net/{i}"
        dev = os.path.realpath(base + "/device") if os.path.exists(base + "/device") else ""
        usb = "/usb" in dev
        drv = os.path.basename(os.path.realpath(base + "/device/driver")) if os.path.exists(base + "/device/driver") else ""
        phy = _rd(base + "/phy80211/name")
        prod, vid = "", ""
        if usb:
            p = os.path.dirname(dev)
            vid = (_rd(p + "/idVendor") + ":" + _rd(p + "/idProduct")).strip(":")
            prod = (_rd(p + "/manufacturer") + " " + _rd(p + "/product")).strip()
        modes, five, comb = _iw_phy(phy)
        chip, note = WIFI_CHIPS.get(drv, (prod or drv or "?", ""))
        out.append({"iface": i, "usb": usb, "driver": drv, "chip": chip, "product": prod[:60], "usb_id": vid, "phy": phy,
                    "mac": _rd(base + "/address"), "ap": ("AP" in modes) if modes else None, "monitor": ("monitor" in modes) if modes else None,
                    "five": five, "note": note, "comb": comb, "up": _rd(base + "/operstate") == "up"})
    return out


def _nm_dev_autoconnect(iface, on):
    if iface and shutil.which("nmcli"):
        _run(["nmcli", "device", "set", iface, "autoconnect", "yes" if on else "no"], 10)


def dual_roles():
    """Which adapter does what. Default: the built-in one makes the own Wi-Fi (devices are near), the USB stick joins the
    campsite / phone network (it often has a better antenna and may hang higher on a cable)."""
    ads = wifi_adapters()
    DUAL["adapters"] = ads; DUAL["t"] = time.time()
    was = (DUAL["on"], DUAL["ap"], DUAL["up"])
    if len(ads) < 2 or not CFG.get("wifi_repeater") or wifi_backend() != "nm":
        DUAL.update(on=False, ap="", up="",
                    msg="" if len(ads) >= 2 or not ads else "only one Wi-Fi adapter")
        if len(ads) >= 2 and wifi_backend() != "nm":
            DUAL["msg"] = "needs NetworkManager"
        if was[0]:
            WIFI["iface"] = ads[0]["iface"] if ads else "wlan0"; WIFI.pop("ap_iface", None)
            for a in ads:
                _nm_dev_autoconnect(a["iface"], True)
            dual_log(tr("Second Wi-Fi adapter: off - back to one adapter"))
        DUAL["choice"] = None
        return DUAL
    names = [a["iface"] for a in ads]
    ch = DUAL.get("choice")
    if ch and ch[0] in names and ch[1] in names and ch[2] == bool(CFG.get("wifi_swap")):
        ap = next(a for a in ads if a["iface"] == ch[0]); up = next(a for a in ads if a["iface"] == ch[1])   # keep the roles once chosen
    else:
        # the adapter that is connected to a network now keeps that connection (the Pi must stay reachable);
        # only when none is connected the USB stick is used for the internet (often the better antenna)
        conn = [a for a in ads if (_iw_link(a["iface"]) or {}).get("connected")]
        intern = next((a for a in ads if not a["usb"]), ads[0])
        stick = next((a for a in ads if a is not intern), ads[1])
        if CFG.get("wifi_swap"):                         # «internet over the USB stick (better antenna)»
            up = stick
        else:
            up = conn[0] if conn else stick
        ap = next(a for a in ads if a is not up)
        if ap["ap"] is False and up["ap"]:
            ap, up = up, ap                                  # this adapter cannot make an own Wi-Fi
        DUAL["choice"] = (ap["iface"], up["iface"], bool(CFG.get("wifi_swap")))
    DUAL.update(on=True, ap=ap["iface"], up=up["iface"], msg="")
    WIFI["iface"] = up["iface"]; WIFI["ap_iface"] = ap["iface"]
    if was != (True, ap["iface"], up["iface"]):
        _nm_unbind(ap["iface"])                              # known networks bound to the own-Wi-Fi adapter may use the other one
        _nm_dev_autoconnect(ap["iface"], False)              # the own Wi-Fi adapter does not join networks by itself
        _nm_dev_autoconnect(up["iface"], True)
        DUAL["since"] = time.time(); DUAL["had_conn"] = bool((STATE.get("wifi") or {}).get("connected"))
        dual_log(trf("Second Wi-Fi adapter: own Wi-Fi on {ap} ({a}), internet over {up} ({b})", ap=ap["iface"], a=ap["chip"], up=up["iface"], b=up["chip"]))
        if STATE["hotspot"].get("on") and was[1] and was[1] != ap["iface"]:
            hotspot_switch_later(True, 0.5)                  # the own Wi-Fi moves to the other adapter
        WIFI["refresh"] = True
    return DUAL


def _nm_unbind(iface):
    """Saved networks that only work on one adapter (connection.interface-name, e.g. made by the Raspberry Pi Imager) may
    then be used by the other adapter too - otherwise the stick cannot join the home Wi-Fi."""
    if not iface or not shutil.which("nmcli"):
        return
    code, out, _e = _run(["nmcli", "-t", "-f", "UUID,TYPE", "connection", "show"], 10)
    if code != 0:
        return
    for ln in out.splitlines():
        f = _nm_split(ln)
        if len(f) < 2 or f[1] not in ("802-11-wireless", "wifi"):
            continue
        c2, o2, _e = _run(["nmcli", "-t", "-g", "connection.interface-name,802-11-wireless.mode,connection.id", "connection", "show", "uuid", f[0]], 10)
        g = o2.splitlines() if c2 == 0 else []
        if len(g) >= 2 and g[0].strip() == iface and g[1].strip() != "ap":
            if _run(["nmcli", "connection", "modify", "uuid", f[0], "connection.interface-name", ""], 10)[0] == 0:
                log_event("sys", f"Wi-Fi «{g[2] if len(g) > 2 else f[0]}» may now be used by every adapter")


def dual_safety():
    """Safety net: the repeater was switched on, but the Pi has had no connection to a network for 2.5 minutes since then
    -> switch it off again by itself, so the Pi becomes reachable again the old way."""
    if not DUAL["on"] or not DUAL.get("had_conn"):
        return
    since = DUAL.get("since") or 0
    if time.time() - since < 150 or time.time() - since > 600:
        return
    w = STATE.get("wifi") or {}
    if w.get("connected") or (STATE.get("net") or {}).get("online"):
        DUAL["had_conn"] = False                             # it works - the safety net is no longer needed
        return
    CFG["wifi_repeater"] = False; save_settings()
    DUAL["choice"] = None
    dual_roles()
    if not CFG.get("hotspot_on"):
        hotspot_set(False, persist=False)
    DUAL["msg"] = "repeater switched off again: no connection to a network"
    dual_log(tr("Repeater switched off again by itself: the Pi had no connection to a network any more"), push=True)


def dual_log(text, push=False):
    DUAL["log"] = ([{"t": time.time(), "text": text}] + DUAL["log"])[:30]
    log_event("sys", text)
    if push and CFG.get("net_inet_notify", True):
        w = WATCH_REF.get("w")
        if w is not None:
            threading.Thread(target=w.notifier.info, args=(text,), kwargs={"title": "{name}: " + tr("Network")}, daemon=True).start()


def _visible_saved(iface):
    """Known networks that can be seen now with this adapter, strongest first."""
    code, out, _e = _run(["nmcli", "-t", "-f", "SSID,SIGNAL", "device", "wifi", "list", "ifname", iface, "--rescan", "auto"], 30)
    if code != 0:
        return []
    sig = {}
    for ln in out.splitlines():
        f = _nm_split(ln)
        if len(f) >= 2 and f[0]:
            try:
                sig[f[0]] = max(sig.get(f[0], 0), int(f[1]))
            except ValueError:
                pass
    saved = [s for s in _nm_saved() if s["ssid"] in sig]
    for s in saved:
        s["signal"] = sig[s["ssid"]]
    return sorted(saved, key=lambda s: (-s["prio"], -s["signal"]))


# ---- USB tethering (2.95.51): a phone on the USB cable gives its internet (Android «USB tethering», iPhone «Personal
# hotspot» + cable). NetworkManager prefers the cable to the Wi-Fi, so the own Wi-Fi (game network) gets the internet of
# the phone too - without a second Wi-Fi adapter. MoveEye finds the phone, connects it and shows it. ----
TETHER_DRV = {"rndis_host": "Android", "cdc_ether": "Android", "cdc_ncm": "Android", "ipheth": "iPhone"}
TETHER = {"t_try": 0.0, "was": ""}


def tether_scan():
    out = []
    for d in glob.glob("/sys/class/net/*"):
        try:
            drv = os.path.basename(os.readlink(os.path.join(d, "device", "driver")))
        except OSError:
            continue
        if drv in TETHER_DRV:
            out.append({"iface": os.path.basename(d), "kind": TETHER_DRV[drv], "drv": drv})
    return out


def tether_tick():
    found = tether_scan()
    if not found:
        if TETHER["was"]:
            log_event("sys", f"Phone on the USB cable gone ({TETHER['was']}) - internet over Wi-Fi again")
            TETHER["was"] = ""
        STATE["tether"] = {"on": False}
        return
    t = found[0]
    rc, txt, _e = _run(["ip", "-4", "-o", "addr", "show", "dev", t["iface"]], 5)
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", txt or "")
    ip = m.group(1) if m else ""
    if not ip and wifi_backend() == "nm" and time.time() - TETHER["t_try"] > 60:
        TETHER["t_try"] = time.time()
        _run(["nmcli", "device", "set", t["iface"], "managed", "yes"], 10)
        _run(["nmcli", "device", "connect", t["iface"]], 30)
    if ip and TETHER["was"] != t["iface"]:
        TETHER["was"] = t["iface"]
        log_event("sys", f"Phone on the USB cable ({t['kind']}, {t['iface']} {ip}): internet over the phone - also for the own Wi-Fi")
    STATE["tether"] = {"on": True, "iface": t["iface"], "kind": t["kind"], "ip": ip, "ready": bool(ip)}


# ---- TV view (2.95.51): a big page for a television - on the HDMI of the Pi (browser in kiosk mode, starts by itself in
# the campfire / gamer mode) or any screen with the link. Left the simulator window (or the camera), right the game:
# the wizard while it is set up, the QR code to join, the time, the players, the ranking; or the game corner of the Pi. ----
TV_PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye · TV</title>
<style>
:root{--bg:#0b0f14;--panel:#111822;--line:#1f2b3a;--txt:#e8eef5;--mut:#8a9bb0;--acc:#3b8cff;--grn:#3fcf6b;--org:#f2a33a;--red:#e5484d}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--txt);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;overflow:hidden;cursor:none}
.top{display:flex;align-items:center;gap:18px;padding:1.2vh 2vw;height:9vh;border-bottom:1px solid var(--line)}
.top img{height:6vh;border-radius:1.2vh}.top .n{font-size:3.4vh;font-weight:800}.top .m{font-size:2.6vh;color:var(--mut)}.top .c{margin-left:auto;font-size:3.4vh;font-weight:700}
.main{display:grid;grid-template-columns:62% 38%;height:91vh}
.view{position:relative;background:#000;display:flex;align-items:center;justify-content:center;border-right:1px solid var(--line)}
.view img{max-width:100%;max-height:100%;object-fit:contain}.view .lbl{position:absolute;left:1.5vw;top:1.5vh;background:rgba(0,0,0,.55);padding:.6vh 1vw;border-radius:1vh;font-size:2vh}
.side{padding:2.2vh 2vw;overflow:hidden;display:flex;flex-direction:column;gap:1.6vh}
h1{font-size:4.2vh;margin:0}h2{font-size:2.6vh;margin:0;color:var(--mut);font-weight:600}
.qr{display:flex;gap:2vw;align-items:center}.qr .q{background:#fff;padding:1.2vh;border-radius:1.4vh;width:30vh;height:30vh}.qr .q svg{width:100%;height:100%}
.qr .t{font-size:2.4vh;line-height:1.35}.qr .u{font-size:2.8vh;font-weight:800;color:var(--acc);word-break:break-all}
.pl{display:flex;flex-direction:column;gap:.8vh}.p{display:flex;align-items:center;gap:1vw;font-size:2.8vh;background:var(--panel);border:1px solid var(--line);border-radius:1.2vh;padding:.8vh 1vw}
.p .d{width:2.2vh;height:2.2vh;border-radius:50%}.p .s{margin-left:auto;color:var(--mut);font-size:2.2vh}
.big{font-size:9vh;font-weight:900;line-height:1}.round{display:flex;align-items:baseline;gap:1.4vw}
.pics{display:flex;gap:1vw}.pics img{width:calc(50% - .5vw);border-radius:1.2vh}
.feed{font-size:2.2vh;color:var(--mut);display:flex;flex-direction:column;gap:.5vh}
.board td{font-size:2.4vh;padding:.4vh .8vw}.board{border-collapse:collapse}
.steps{display:flex;gap:.6vw}.steps span{font-size:1.9vh;padding:.4vh .9vw;border-radius:99px;border:1px solid var(--line);color:var(--mut)}.steps span.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:1vh}.card{border:2px solid var(--line);border-radius:1.2vh;padding:.8vh;font-size:2vh}.card.on{border-color:var(--acc);background:rgba(59,140,255,.15)}.card img{width:100%;border-radius:.8vh}
.idle{font-size:2.6vh;line-height:1.5;color:var(--mut)}
</style></head><body>
<div class="top"><img src="/icon-192.png" id="ic" alt=""><div><div class="n">MoveEye</div><div class="m" id="mode"></div></div><div class="c" id="clock"></div></div>
<div class="main"><div class="view"><img id="v" alt=""><div class="lbl" id="vl"></div></div><div class="side" id="side"></div></div>
<script>
const K = location.pathname.split("/")[2];
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => "&#" + c.charCodeAt(0) + ";");
const svgImg = s => s ? '<img alt="" src="data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s) + '">' : "";
const mmss = n => Math.floor(n / 60) + ":" + ("0" + (n % 60)).slice(-2);
let D = null, vBusy = false;
function clock() { const d = new Date(); $("#clock").textContent = ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); }
function view() {                                   // one picture after the other: never a growing delay
  if (vBusy) return; vBusy = true; const im = new Image();
  im.onload = () => { $("#v").src = im.src; vBusy = false; setTimeout(view, 150); };
  im.onerror = () => { vBusy = false; setTimeout(view, 1500); };
  im.src = "/tv/" + K + "/view.jpg?r=" + Date.now();
}
function players(list) {
  return '<div class="pl">' + list.map(p => '<div class="p"><span class="d" style="background:' + esc(p.c || "#3b8cff") + '"></span>' + esc(p.n) +
    '<span class="s">' + esc(p.s || "") + '</span></div>').join("") + '</div>';
}
function paint() {
  const d = D; if (!d) return;
  $("#mode").textContent = d.mode || ""; $("#vl").textContent = d.view_label || "";
  let h = "";
  const G = d.game || {}, W = d.wiz || {}, P = d.party || {};
  if (W.shown) {
    h += '<h2>🎮 ' + esc(d.t_setup) + '</h2><div class="steps">' + (W.steps || []).map((x, i) => '<span class="' + (i === W.step ? "on" : "") + '">' + (i + 1) + " " + esc(x) + '</span>').join("") + '</div>';
    h += '<h1>' + esc(W.title) + '</h1>';
    if ((W.cards || []).length) h += '<div class="cards">' + W.cards.map(c => '<div class="card' + (c.on ? " on" : "") + '">' + svgImg(c.pic) + '<b>' + esc(c.title) + '</b></div>').join("") + '</div>';
    if ((W.pics || []).some(x => x)) h += '<div class="pics">' + W.pics.map(svgImg).join("") + '</div>';
    if (G.open && G.qr) h += '<div class="qr"><div class="q">' + G.qr + '</div><div class="t">' + esc(d.t_join) + '<div class="u">' + esc(G.url) + '</div></div></div>';
  } else if (G.open) {
    const r = G.round;
    h += '<h2>🎮 ' + esc(G.title || "") + '</h2>';
    if (r === "countdown") h += '<div class="round"><div class="big">' + esc(G.cd) + '</div><h1>' + esc(d.t_ready) + '</h1></div>';
    else if (r === "play") h += '<div class="round"><div class="big">' + mmss(G.left || 0) + '</div><h1>' + esc(d.t_play) + (G.last_minute ? " 🔥" : "") + '</h1></div>';
    else if (r === "end") h += '<h1>🏁 ' + esc(d.t_end) + '</h1>' + (G.win && G.win.title ? '<h2>' + esc(G.win.title) + (G.win.score >= 0 ? " · " + esc(G.win.score) : "") + '</h2>' : "");
    else h += '<h1>' + esc(d.t_waiting) + '</h1>';
    if ((r === "lobby" || r === "end") && G.next) h += '<div class="idle">' + esc(G.next) + '</div>';
    if (G.mw) h += '<h2>🎯 ' + esc(String(d.t_mw || "").replace("{n}", G.mw)) + '</h2>';
    if (r !== "play" && r !== "countdown" && G.qr) h += '<div class="qr"><div class="q">' + G.qr + '</div><div class="t">' + esc(d.t_join) + '<div class="u">' + esc(G.url) + '</div></div></div>';
    if ((G.players || []).length) h += players(G.players);
    if ((G.feed || []).length) h += '<div class="feed">' + G.feed.map(x => '<div>• ' + esc(x) + '</div>').join("") + '</div>';
    if ((G.board || []).length && r !== "play") h += '<h2>🏆 ' + esc(d.t_board) + '</h2><table class="board">' + G.board.slice(0, 6).map((b, i) => '<tr><td>' + (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + '</td><td style="color:' + esc(b.c) + '">' + esc(b.n) + '</td><td>' + esc(b.score) + '</td></tr>').join("") + '</table>';
  } else if (P.on) {
    h += '<h2>🎲 ' + esc(d.t_corner) + '</h2><h1>' + esc(P.game || "") + '</h1>';
    if (P.qr) h += '<div class="qr"><div class="q">' + P.qr + '</div><div class="t">' + esc(d.t_join) + '<div class="u">' + esc(P.url) + '</div></div></div>';
    if ((P.players || []).length) h += players(P.players);
  } else {
    h += '<h1>' + esc(d.state || "") + '</h1><div class="idle">' + esc(d.t_idle) + '</div>';
    if (d.tip) h += '<div style="margin-top:2vh;border:1px solid var(--line);border-radius:1.4vh;padding:1.6vh 1.4vw"><h2>🌙 ' + esc(d.t_tip) + '</h2><div style="font-size:2.8vh;font-weight:700;margin:.6vh 0">' + esc(d.tip.title) + '</div><div class="idle">' + esc(d.tip.text) + '</div></div>';
    if (d.info && d.info.qr) h += '<div class="qr"><div class="q">' + d.info.qr + '</div><div class="t">' + esc(d.t_info) + '<div class="u">' + esc(d.info.url) + '</div></div></div>';
    if ((d.events || []).length) h += '<div class="feed">' + d.events.map(x => '<div>• ' + esc(x) + '</div>').join("") + '</div>';
  }
  if ($("#side").dataset.h !== h) { $("#side").dataset.h = h; $("#side").innerHTML = h; }
}
async function poll() {
  try { const r = await fetch("/tv/" + K + "/data", {cache: "no-store"}); if (r.ok) { D = await r.json(); paint(); } } catch (e) {}
  setTimeout(poll, 1500);
}
clock(); setInterval(clock, 5000); view(); poll();
</script></body></html>
"""
TV = {"proc": None, "msg": "", "sim": False}


def tv_sim(on, who="web"):
    """2.95.53: the TV mode of the 3D simulator (on the PC at the television) - smoother than the browser"""
    iu = (page_address().rstrip("/") + "/info/") if CFG.get("info_page") and page_address() else ""
    try:
        r = sim_control({"action": "tv", "on": bool(on), "info_url": iu})
    except Exception as e:
        return False, "simulator not reachable"
    if not isinstance(r, dict) or not r.get("ok"):
        return False, "not supported - update the simulator"
    TV["sim"] = bool(on)
    log_event("sys", f"TV mode of the simulator {'on' if on else 'off'} ({who})")
    return True, ""


def tv_key():
    if not CFG.get("tv_key"):
        CFG["tv_key"] = secrets.token_urlsafe(9); save_settings()
    return CFG["tv_key"]


def tv_url(local=True):
    return f"{'https' if WEB_OPTS.get('https') else 'http'}://127.0.0.1:{CFG.get('web_port') or 5000}/tv/{tv_key()}/" if local else "/tv/" + tv_key() + "/"


def _tv_browser():
    for b in ("chromium-browser", "chromium", "firefox"):
        p_ = shutil.which(b)
        if p_:
            return p_
    return ""


def tv_show(on, who="web"):
    """the TV view on the HDMI of the Pi: a browser in kiosk mode on the desktop of the Pi"""
    if not on:
        pr = TV["proc"]
        if pr is not None and pr.poll() is None:
            try:
                pr.terminate()
            except Exception:
                pass
        TV["proc"] = None; TV["msg"] = "off"
        return True, ""
    if TV["proc"] is not None and TV["proc"].poll() is None:
        return True, ""
    br = _tv_browser()
    if not br:
        TV["msg"] = "no browser on this device (Chromium)"
        return False, TV["msg"]
    env = dict(os.environ)
    uid = os.getuid() if hasattr(os, "getuid") else 1000
    rt = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    if not env.get("WAYLAND_DISPLAY") and not env.get("DISPLAY"):
        way = next((os.path.basename(x) for x in sorted(glob.glob(os.path.join(rt, "wayland-*"))) if not x.endswith(".lock")), "")
        if way:
            env["WAYLAND_DISPLAY"] = way; env["XDG_RUNTIME_DIR"] = rt
        elif os.path.exists("/tmp/.X11-unix/X0"):
            env["DISPLAY"] = ":0"
        else:
            TV["msg"] = "no desktop on the HDMI (Raspberry Pi OS with desktop needed)"
            return False, TV["msg"]
    args = [br, "--kiosk", tv_url(True)] if "firefox" in br else [br, "--kiosk", "--noerrdialogs", "--disable-infobars", "--incognito",
            "--password-store=basic", "--ignore-certificate-errors", "--autoplay-policy=no-user-gesture-required", "--check-for-update-interval=31536000", tv_url(True)]
    try:
        TV["proc"] = subprocess.Popen(args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception as e:
        TV["msg"] = "browser: " + str(e)[:80]
        return False, TV["msg"]
    TV["msg"] = "on"
    log_event("sys", f"TV view on the HDMI ({who})")
    return True, ""


def tv_state():
    on = TV["proc"] is not None and TV["proc"].poll() is None
    return {"on": on, "msg": TV["msg"], "browser": bool(_tv_browser()),
            "url": tv_url(False), "auto": bool(CFG["tv_auto"]), "sim": TV["sim"], "sim_ok": bool(CFG.get("sim_on") and time.time() - SIM.get("t", 0) < 15)}


GAME_STATE_WORDS = {"goal": "at the goal", "out": "caught", "jail": "in jail", "play": "on the way", "lobby": "ready"}


def game_live_tv(g, T):
    """Aufräumen 2: «game_live» of the simulator -> the game part of the TV page (the same words as tv.gd and the SmallTV)"""
    url = str(g.get("url") or "")
    def ps_(p):
        k, pt = int(p.get("k", 0) or 0), p.get("pt")
        return {"n": p.get("n"), "c": p.get("c") or "#3b8cff",
                "s": " · ".join(x for x in (T(GAME_STATE_WORDS.get(str(p.get("s")), str(p.get("s") or ""))), f"{k}×" if k else "",
                                            f"{int(pt)} {T('points')}" if pt is not None else "") if x)}
    return {"open": True, "round": g.get("round"), "cd": g.get("cd"), "left": g.get("left"), "last_minute": g.get("lm"),
            "title": T("Game in the 3D simulator") + (" · " + str(g.get("goal")) if g.get("goal") else ""), "url": url, "qr": qr_svg(url) if url else "",
            "players": [ps_(p) for p in g.get("players") or []], "feed": [str(x)[:80] for x in (g.get("feed") or [])][:4],
            "board": [{"n": b.get("n"), "c": b.get("c"), "score": b.get("score")} for b in (g.get("board") or [])],
            "win": g.get("win"), "next": g.get("next") or "", "mw": g.get("mw")}


def tv_data():
    """what the TV page shows"""
    L = norm_lang(CFG.get("lang")) or "de"
    T = lambda x: tr(x, L)
    m = CFG.get("mode") or ""
    md = dict((x[0], x) for x in MODES).get(m)
    d = {"mode": (md[1] + " " + T(md[2])) if md else "",
         "state": T({"armed": "Armed", "arming": "Arming …", "disarmed": "Not armed"}.get(STATE.get("arm_state"), "")),
         "t_setup": T("The game is being set up"), "t_join": T("Join: scan the QR code with the phone (same Wi-Fi) or open"),
         "t_ready": T("Get ready"), "t_play": T("Round running"), "t_end": T("Round over"), "t_waiting": T("Waiting for players"),
         "t_board": T("Ranking of the evening"), "t_mw": T("MoveEye caught {n}"), "t_corner": T("Game corner"), "t_idle": T("Nothing is going on at the moment - MoveEye keeps watch."),
         "events": [], "game": {}, "wiz": {}, "party": {}}
    try:
        d["events"] = [str(e.get("text") or e.get("msg") or "")[:90] for e in list(EVENTS)[-5:]][::-1] if "EVENTS" in globals() else []
    except Exception:
        d["events"] = []
    if CFG.get("sim_on"):
        d["view_label"] = T("Simulator")
        try:
            wz = sim_control({"action": "gamewiz", "op": "get"})
            if isinstance(wz, dict) and wz.get("ok"):
                d["wiz"] = {k: wz.get(k) for k in ("shown", "step", "steps", "title", "cards", "pics")}
            # Aufräumen 2: ONE source for all game displays - «game_live» of the simulator (in every answer, 552 keeps it in
            # STV «game»), the same as the SmallTV and the TV mode of the simulator (tv.gd); older simulators: «game_info»
            gl = STV["game"] if "STV" in globals() and STV.get("game") and time.time() - STV.get("game_t", 0.0) < 10 else None
            if gl is not None:
                d["game"] = game_live_tv(gl, T)
            else:
                gi = sim_control({"action": "game_info"})
                if isinstance(gi, dict) and gi.get("open"):
                    url = ((wz or {}).get("game") or {}).get("url") or ""
                    d["game"] = game_live_tv({"round": gi.get("round"), "cd": gi.get("cd"), "left": gi.get("left"), "lm": gi.get("last_minute"),
                                              "goal": gi.get("goal"), "url": url, "players": gi.get("players") or [],
                                              "feed": [str(x.get("x")) for x in (gi.get("feed") or [])][::-1][:4], "board": gi.get("board") or []}, T)
        except Exception:
            pass
    else:
        d["view_label"] = T("Camera")
    try:
        d["tip"] = almanac_tip(); d["t_tip"] = T("Tip of the evening")
    except Exception:
        pass
    if CFG.get("info_page") and page_address():
        iu = page_address().rstrip("/") + "/info/"
        d["info"] = {"url": iu, "qr": qr_svg(iu)}; d["t_info"] = T("More about MoveEye")
    if party_on():
        url = page_address().rstrip("/") + "/p/" + PARTY["key"] + "/"
        d["party"] = {"on": True, "url": url, "qr": qr_svg(url), "game": str(PARTY.get("game") or ""),
                      "players": [{"n": v["name"], "c": "#3b8cff", "s": str(v.get("score", 0))} for k, v in PARTY["players"].items() if time.time() - v["t"] < 25]}
    return d


# ---- network check of the players (2.95.52): every phone measures its connection to MoveEye - ping (reaction time),
# jitter, losses, download and upload - and MoveEye adds what only it sees: the signal of each phone at its own Wi-Fi.
# Open only while a check runs (a few minutes); limited data per phone, so nobody can use it to load the Pi. ----
NETTEST = {"round": 0, "until": 0.0, "res": {}, "bytes": {}, "t0": 0.0}
NT_DOWN_MAX = 8 << 20          # one phone: at most this much down and up per check
NT_UP_MAX = 4 << 20
NT_BLOB = os.urandom(1 << 16)


def nettest_open():
    return time.time() < NETTEST["until"]


def nettest_start(minutes=3):
    NETTEST.update(round=NETTEST["round"] + 1, until=time.time() + 60 * max(1, min(15, minutes)), res={}, bytes={}, t0=time.time())
    try:
        party_bump()                                    # the phones in the game corner start their measurement by themselves
    except Exception:
        pass
    log_event("sys", "Network check of the players started")


def nettest_stop():
    NETTEST["until"] = 0.0


def _wifi_stations():
    """the phones at the own Wi-Fi of MoveEye: MAC -> signal, speeds (only when MoveEye is the access point)"""
    out = {}
    hs = STATE.get("hotspot") or {}
    if not hs.get("on") or shutil.which("iw") is None:
        return out
    ap_if = WIFI.get("ap_iface") or WIFI["iface"]
    code, txt, _e = _run(["iw", "dev", ap_if, "station", "dump"], 5)
    if code != 0:
        return out
    cur = None
    for line in txt.splitlines():
        m = re.match(r"Station\s+([0-9a-f:]{17})", line.strip(), re.I)
        if m:
            cur = out.setdefault(m.group(1).lower(), {}); continue
        if cur is None:
            continue
        k, _, v = line.strip().partition(":")
        v = v.strip()
        if k == "signal":
            mm = re.match(r"(-?\d+)", v); cur["dbm"] = int(mm.group(1)) if mm else None
        elif k == "tx bitrate":
            mm = re.match(r"([\d.]+)", v); cur["tx"] = float(mm.group(1)) if mm else None
        elif k == "rx bitrate":
            mm = re.match(r"([\d.]+)", v); cur["rx"] = float(mm.group(1)) if mm else None
        elif k == "connected time":
            mm = re.match(r"(\d+)", v); cur["conn_s"] = int(mm.group(1)) if mm else None
    return out


def _nt_grade(r):
    """good / fair / weak with the main reason (shown to the player and in the list)"""
    why = []
    rtt, jit, loss, dn, up, dbm = r.get("rtt"), r.get("jitter"), r.get("loss", 0), r.get("down"), r.get("up"), r.get("dbm")
    bad = 0
    if loss and loss >= 2:
        bad = 2; why.append("lost packets")
    if rtt is not None and rtt > 150:
        bad = 2; why.append("slow reaction")
    elif rtt is not None and rtt > 60:
        bad = max(bad, 1); why.append("reaction a bit slow")
    if jit is not None and jit > 40:
        bad = max(bad, 1); why.append("unsteady")
    if dn is not None and dn < 2:
        bad = 2; why.append("little speed")
    elif dn is not None and dn < 8:
        bad = max(bad, 1); why.append("medium speed")
    if dbm is not None and dbm < -75:
        bad = 2; why.append("weak signal")
    elif dbm is not None and dbm < -67:
        bad = max(bad, 1); why.append("signal could be better")
    return ["good", "fair", "weak"][bad], why


def nettest_report(ip, d):
    name = re.sub(r"[\x00-\x1f<>]", "", str(d.get("name") or "")).strip()[:20] or ip
    def num(k, lo, hi):
        try:
            v = float(d.get(k))
            return round(max(lo, min(hi, v)), 1)
        except (TypeError, ValueError):
            return None
    r = {"name": name, "ip": ip, "t": time.time(), "rtt": num("rtt", 0, 10000), "jitter": num("jitter", 0, 10000), "loss": int(num("loss", 0, 50) or 0),
         "down": num("down", 0, 10000), "up": num("up", 0, 10000), "dev": re.sub(r"[\x00-\x1f<>]", "", str(d.get("dev") or ""))[:30],
         "src": str(d.get("src") or "page")[:10]}
    mac = _arp_table().get(ip, "")
    r["mac"] = mac
    try:
        r["maker"] = oui_vendor(mac) if mac else ""
    except Exception:
        r["maker"] = ""
    st_ = _wifi_stations().get(mac) if mac else None
    if st_:
        r.update(dbm=st_.get("dbm"), link_tx=st_.get("tx"), link_rx=st_.get("rx"), via="own Wi-Fi")
    else:
        r["via"] = "this computer" if ip in ("127.0.0.1", "::1") else "network"
    r["grade"], r["why"] = _nt_grade(r)
    NETTEST["res"][ip] = r
    return r


NETWALK = deque(maxlen=200)          # 2.95.53: Empfangs-Rundgang: measured spots round MoveEye (metres; z = where the camera looks)


def netwalk_add(ip, d):
    def num(k, lo, hi):
        try:
            return round(max(lo, min(hi, float(d.get(k)))), 1)
        except (TypeError, ValueError):
            return None
    x, z = num("x", -60, 60), num("z", -60, 60)
    if x is None or z is None:
        return None
    pt = {"x": x, "z": z, "rtt": num("rtt", 0, 10000), "down": num("down", 0, 10000), "loss": int(num("loss", 0, 50) or 0), "t": time.time(),
          "name": re.sub(r"[\x00-\x1f<>]", "", str(d.get("name") or ""))[:20]}
    mac = _arp_table().get(ip, "")
    st_ = _wifi_stations().get(mac) if mac else None
    pt["dbm"] = st_.get("dbm") if st_ else None
    # 0 (bad) .. 1 (good): signal if known, else reaction time and speed
    q = []
    if pt["dbm"] is not None:
        q.append(max(0.0, min(1.0, (pt["dbm"] + 85) / 30.0)))
    if pt["rtt"] is not None:
        q.append(max(0.0, min(1.0, 1.0 - (pt["rtt"] - 10) / 140.0)))
    if pt["down"] is not None:
        q.append(max(0.0, min(1.0, pt["down"] / 20.0)))
    if pt["loss"]:
        q.append(0.0)
    pt["q"] = round(sum(q) / len(q), 2) if q else 0.0
    NETWALK.append(pt)
    return pt


def nettest_state():
    now = time.time()
    hs = STATE.get("hotspot") or {}
    w = STATE.get("wifi") or {}
    res = sorted(NETTEST["res"].values(), key=lambda r: (["weak", "fair", "good"].index(r["grade"]), r["name"].lower()))
    st_ = _wifi_stations()
    known = {r.get("mac") for r in res}
    others = [{"mac": m, "maker": oui_vendor(m), "dbm": v.get("dbm"), "tx": v.get("tx")} for m, v in st_.items() if m not in known]
    players = [v["name"] for k, v in PARTY["players"].items() if now - v["t"] < 25] if party_on() else []
    return {"open": nettest_open(), "left": max(0, int(NETTEST["until"] - now)), "round": NETTEST["round"], "res": res, "others": others,
            "hotspot": bool(hs.get("on")), "pi_link": {"ssid": w.get("ssid"), "dbm": w.get("dbm"), "rate": w.get("rate")} if w and w.get("connected") else None,
            "party": party_on(), "party_players": players, "url": "/nt/",
            "pending": [n for n in players if n not in {r["name"] for r in res}], "walk": list(NETWALK)}


NT_JS = r"""
// network check (2.95.52): reaction time, jitter, losses, download, upload - to MoveEye, not to the internet
async function ntMeasure(name, step, src) {
  const now = () => performance.now(), rtts = []; let loss = 0;
  step("ping", 0);
  for (let i = 0; i < 15; i++) {
    const c = new AbortController(), to = setTimeout(() => c.abort(), 1500), t0 = now();
    try { const r = await fetch("/nt/ping?r=" + Math.random(), {cache: "no-store", signal: c.signal}); await r.text(); if (i > 0) rtts.push(now() - t0); } catch (e) { loss++; }
    clearTimeout(to); step("ping", (i + 1) / 15);
  }
  rtts.sort((a, b) => a - b);
  const med = rtts.length ? rtts[Math.floor(rtts.length / 2)] : null;
  const jit = rtts.length > 2 ? rtts.slice(1).reduce((s, v, i) => s + Math.abs(v - rtts[i]), 0) / (rtts.length - 1) : null;
  const down = async (kb) => { const t0 = now(); const r = await fetch("/nt/down?kb=" + kb + "&r=" + Math.random(), {cache: "no-store"}); const b = await r.arrayBuffer(); return {mb: b.byteLength * 8 / 1e6, s: (now() - t0) / 1000}; };
  let dn = null, up = null;
  try {
    step("down", 0); const w = await down(256);
    const kb = w.s < 0.15 ? 4096 : w.s < 0.6 ? 2048 : 768;          // a slow phone does not wait forever
    const m = await down(kb); dn = m.mb / Math.max(0.01, m.s); step("down", 1);
  } catch (e) {}
  try {
    step("up", 0); const kb = dn && dn > 20 ? 2048 : 512, buf = new Uint8Array(kb * 1024); for (let i = 0; i < buf.length; i += 4096) buf[i] = (Math.random() * 255) | 0;
    const t0 = now(); const r = await fetch("/nt/up", {method: "POST", body: buf}); await r.text(); up = buf.length * 8 / 1e6 / Math.max(0.01, (now() - t0) / 1000); step("up", 1);
  } catch (e) {}
  const dev = (navigator.userAgentData && navigator.userAgentData.platform) || (/iPhone|iPad|Android|Windows|Mac OS|Linux/.exec(navigator.userAgent) || [""])[0];
  const res = {name: name, rtt: med, jitter: jit, loss: loss, down: dn, up: up, dev: dev, src: src || "page"};
  try { const r = await fetch("/nt/report", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(res)}); return await r.json(); } catch (e) { return Object.assign(res, {grade: "?"}); }
}
"""


NT_WALK_PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Empfangs-Rundgang</title><style>
:root{--bg:#0e1621;--panel:#16212f;--line:#24324a;--txt:#e8eef6;--mut:#8ea0b6;--acc:#3b8cff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:14px;max-width:520px;margin:auto}
h1{font-size:20px;margin:4px 0 8px}.mut{color:var(--mut);font-size:14px}canvas{width:100%;aspect-ratio:1;background:#0b1310;border-radius:14px;border:1px solid var(--line);touch-action:none;margin:10px 0}
button{font:inherit;width:100%;padding:14px;border:0;border-radius:12px;background:var(--acc);color:#fff;font-weight:700}button:disabled{opacity:.5}
input{font:inherit;width:100%;padding:11px;border-radius:12px;border:1px solid var(--line);background:#0b121c;color:var(--txt);margin-top:6px}
</style></head><body>
<h1>📶 Empfangs-Rundgang</h1>
<div class="mut">Geh mit dem Handy um den Platz. Tippe auf dem Plan, wo du gerade stehst (MoveEye ist in der Mitte, oben ist die Richtung, in die die Kamera schaut, die Kreise sind 5 / 10 / 20 m), dann «Hier messen». Jede Messung dauert 2–3 Sekunden.</div>
<input id="nm" maxlength="20" placeholder="Dein Name (freiwillig)">
<canvas id="cv" width="640" height="640"></canvas>
<button id="go" disabled>Zuerst auf dem Plan tippen</button>
<div class="mut" id="st" style="margin-top:8px"></div>
<script>
const R = 25, cv = document.getElementById("cv"), cx = cv.getContext("2d"), go = document.getElementById("go"), st = document.getElementById("st");
let me = null, pts = [];
try { document.getElementById("nm").value = localStorage.getItem("mw-nt-name") || ""; } catch (e) {}
const toPx = (x, z) => [320 + x / R * 300, 320 - z / R * 300];
function col(q) { const h = Math.round(q * 120); return "hsl(" + h + ",80%,50%)"; }
function draw() {
  cx.clearRect(0, 0, 640, 640);
  cx.strokeStyle = "#24324a"; cx.lineWidth = 2; [5, 10, 20].forEach(r => { cx.beginPath(); cx.arc(320, 320, r / R * 300, 0, 7); cx.stroke(); });
  cx.fillStyle = "#8ea0b6"; cx.font = "22px system-ui"; [5, 10, 20].forEach(r => cx.fillText(r + " m", 326, 320 - r / R * 300 + 22));
  cx.strokeStyle = "#e8eef6"; cx.lineWidth = 4; cx.beginPath(); cx.moveTo(320, 320); cx.lineTo(320, 250); cx.stroke();
  cx.fillStyle = "#e8eef6"; cx.beginPath(); cx.moveTo(320, 230); cx.lineTo(306, 256); cx.lineTo(334, 256); cx.fill();
  pts.forEach(p => { const [a, b] = toPx(p.x, p.z); cx.fillStyle = col(p.q); cx.beginPath(); cx.arc(a, b, 16, 0, 7); cx.fill(); });
  cx.fillStyle = "#f59a4a"; cx.beginPath(); cx.arc(320, 320, 14, 0, 7); cx.fill();
  if (me) { const [a, b] = toPx(me[0], me[1]); cx.strokeStyle = "#3b8cff"; cx.lineWidth = 5; cx.beginPath(); cx.arc(a, b, 22, 0, 7); cx.stroke(); }
}
cv.addEventListener("pointerdown", ev => { const r = cv.getBoundingClientRect(); const a = (ev.clientX - r.left) / r.width * 640, b = (ev.clientY - r.top) / r.height * 640;
  me = [(a - 320) / 300 * R, (320 - b) / 300 * R]; go.disabled = false; go.textContent = "Hier messen (" + Math.round(Math.hypot(me[0], me[1])) + " m)"; draw(); });
async function load() { try { const r = await fetch("/nt/walk/points", {cache: "no-store"}); if (r.ok) { pts = (await r.json()).points || []; draw(); } } catch (e) {} }
go.onclick = async () => {
  if (!me) return; go.disabled = true; st.textContent = "misst …";
  const rt = []; let loss = 0;
  for (let i = 0; i < 8; i++) { const c = new AbortController(), to = setTimeout(() => c.abort(), 1500), t0 = performance.now();
    try { await (await fetch("/nt/ping?r=" + Math.random(), {cache: "no-store", signal: c.signal})).text(); if (i) rt.push(performance.now() - t0); } catch (e) { loss++; } clearTimeout(to); }
  rt.sort((a, b) => a - b); let down = null;
  try { const t0 = performance.now(); const b = await (await fetch("/nt/down?kb=512&r=" + Math.random(), {cache: "no-store"})).arrayBuffer(); down = b.byteLength * 8 / 1e6 / ((performance.now() - t0) / 1000); } catch (e) {}
  const nm = document.getElementById("nm").value.trim(); try { localStorage.setItem("mw-nt-name", nm); } catch (e) {}
  try { const r = await fetch("/nt/walk/point", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({x: me[0], z: me[1], rtt: rt.length ? rt[Math.floor(rt.length / 2)] : null, down: down, loss: loss, name: nm})});
    const j = await r.json(); if (j.ok) { st.textContent = "✓ " + (j.point.q >= .66 ? "gut" : j.point.q >= .33 ? "geht so" : "schwach") + " · " + Math.round(j.point.rtt || 0) + " ms · " + (j.point.down || 0).toFixed(1) + " Mbit/s" + (j.point.dbm != null ? " · " + j.point.dbm + " dBm" : ""); }
    else st.textContent = "⚠ " + (j.error || "Fehler"); } catch (e) { st.textContent = "⚠ keine Verbindung"; }
  me = null; go.textContent = "Zuerst auf dem Plan tippen"; load();
};
load(); draw();
</script></body></html>"""


NT_PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Netz-Check</title><style>
:root{--bg:#0e1621;--panel:#16212f;--line:#24324a;--txt:#e8eef6;--mut:#8ea0b6;--acc:#3b8cff;--grn:#3fcf6b;--org:#e9a23b;--red:#ff5a5f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:16px;max-width:520px;margin:auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:12px}h1{font-size:21px;margin:4px 0 12px}
input{font:inherit;width:100%;padding:12px;border-radius:12px;border:1px solid var(--line);background:#0b121c;color:var(--txt)}
button{font:inherit;width:100%;margin-top:10px;padding:14px;border:0;border-radius:12px;background:var(--acc);color:#fff;font-weight:700}button:disabled{opacity:.5}
.mut{color:var(--mut);font-size:14px}.bar{height:10px;border-radius:5px;background:#24324a;overflow:hidden;margin:10px 0}.bar i{display:block;height:100%;width:0;background:var(--acc);transition:width .2s}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.v{background:#0b121c;border-radius:12px;padding:10px}.v b{display:block;font-size:22px}
.good{color:var(--grn)}.fair{color:var(--org)}.weak{color:var(--red)}.big{font-size:26px;font-weight:800;margin:8px 0}
</style></head><body>
<h1>📶 <span id="h">Netz-Check</span></h1>
<div class="card" id="c-run"><div class="mut" id="intro"></div><input id="nm" maxlength="20" autocomplete="nickname"><button id="go"></button>
<div class="bar"><i id="pb"></i></div><div class="mut" id="st"></div></div>
<div class="card" id="c-res" hidden><div class="big" id="gr"></div><div class="grid" id="vals"></div><div class="mut" id="why" style="margin-top:10px"></div></div>
<script>
const L = (navigator.language || "de").slice(0, 2);
const T = {de: {h: "Netz-Check", intro: "Misst, wie gut dein Handy MoveEye erreicht: Reaktionszeit, Schwankung, Verluste und Geschwindigkeit. Dauert etwa 10 Sekunden.", name: "Dein Name", go: "Jetzt messen", ping: "Reaktionszeit …", down: "Download …", up: "Upload …", closed: "Der Netz-Check ist gerade nicht offen.", good: "✅ Gute Verbindung", fair: "🟠 Geht so", weak: "🔴 Schwache Verbindung", rtt: "Reaktion", jitter: "Schwankung", down2: "Download", up2: "Upload", sig: "Signal", again: "Nochmals messen", tip: "Tipp: näher zu MoveEye, Hindernisse (Wände, Auto, Körper) vermeiden."},
  en: {h: "Network check", intro: "Measures how well your phone reaches MoveEye: reaction time, jitter, losses and speed. Takes about 10 seconds.", name: "Your name", go: "Measure now", ping: "Reaction time …", down: "Download …", up: "Upload …", closed: "The network check is not open right now.", good: "✅ Good connection", fair: "🟠 So-so", weak: "🔴 Weak connection", rtt: "Reaction", jitter: "Jitter", down2: "Download", up2: "Upload", sig: "Signal", again: "Measure again", tip: "Tip: closer to MoveEye, avoid obstacles (walls, car, bodies)."}};
const X = T[L] || (L === "fr" || L === "it" ? T.en : T.de);
const $ = s => document.querySelector(s);
$("#h").textContent = X.h; $("#intro").textContent = X.intro; $("#nm").placeholder = X.name; $("#go").textContent = X.go;
try { $("#nm").value = localStorage.getItem("mw-nt-name") || localStorage.getItem("mw-party-name") || ""; } catch (e) {}
__NTJS__
const W = {ping: [0, .35], down: [.35, .4], up: [.75, .25]};
function show(r) {
  $("#c-res").hidden = false; $("#gr").textContent = X[r.grade] || "?"; $("#gr").className = "big " + (r.grade || "");
  const f = (v, u, d) => v == null ? "–" : (+v).toFixed(d) + " " + u;
  $("#vals").innerHTML = "";
  [[X.rtt, f(r.rtt, "ms", 0)], [X.jitter, f(r.jitter, "ms", 0)], [X.down2, f(r.down, "Mbit/s", 1)], [X.up2, f(r.up, "Mbit/s", 1)]].concat(r.dbm != null ? [[X.sig, r.dbm + " dBm"]] : [])
    .forEach(x => { const d = document.createElement("div"); d.className = "v"; d.textContent = x[0]; const b = document.createElement("b"); b.textContent = x[1]; d.appendChild(b); $("#vals").appendChild(d); });
  $("#why").textContent = r.grade && r.grade !== "good" ? X.tip : "";
}
$("#go").onclick = async () => {
  const nm = $("#nm").value.trim(); try { localStorage.setItem("mw-nt-name", nm); } catch (e) {}
  $("#go").disabled = true;
  const r = await ntMeasure(nm, (k, p) => { $("#st").textContent = X[k]; $("#pb").style.width = Math.round(100 * (W[k][0] + W[k][1] * p)) + "%"; }, "page");
  $("#go").disabled = false; $("#go").textContent = X.again;
  if (r && r.error) { $("#st").textContent = X.closed; return; }
  $("#st").textContent = ""; show(r);
};
</script></body></html>"""


class UplinkWatch:
    """Every 10 s: internet there? Connection drops? -> after 3 min without internet try another known network (only with two
    adapters - with one adapter the network automatic does it). Push message when the internet is back (with how long it was gone)."""
    def __init__(self):
        self.was_conn = None; self.n = 0; self.warned_unstable = 0.0
        threading.Thread(target=self.loop, daemon=True, name="uplink").start()

    def step(self):
        now = time.time(); self.n += 1
        if self.n % 6 == 1:
            try:
                dual_roles()
            except Exception as e:
                DUAL["msg"] = str(e)[:100]
        try:
            dual_safety()
        except Exception as e:
            DUAL["msg"] = str(e)[:100]
        try:
            tether_tick()
        except Exception as e:
            STATE["tether"] = {"on": False, "err": str(e)[:80]}
        try:
            noinet_apply()                               # 2.95.33: was only called after an error (also after a restart now)
        except Exception as e:
            DUAL["msg"] = str(e)[:100]
        net = STATE.get("net") or {}; w = STATE.get("wifi") or {}
        online = net.get("online")
        if online is False and DUAL["offline_since"] is None:
            DUAL["offline_since"] = now
        elif online and DUAL["offline_since"] is not None:
            gone = now - DUAL["offline_since"]; DUAL["offline_since"] = None
            if gone > 120:
                dual_log(trf("Internet was gone for {min} min - it is back ({ssid})", min=int(gone / 60 + 0.5), ssid=w.get("ssid") or "?"), push=True)
        conn = bool(w.get("connected")) and not w.get("ap")
        if self.was_conn and not conn:
            DUAL["drops"] = [t_ for t_ in DUAL["drops"] if now - t_ < 600] + [now]
            good = [v for v in list(STATE.get("wifi_hist") or [])[-10:] if v is not None]
            if len(DUAL["drops"]) >= 3 and good and max(good) > -70:
                DUAL["unstable"] = True
                if now - self.warned_unstable > 3600:
                    self.warned_unstable = now
                    dual_log(tr("Wi-Fi connection dropped 3 times in 10 minutes although the signal is good - interference or jamming?"),
                             push=bool(CFG.get("wifi_guard")))
        elif DUAL["drops"] and now - DUAL["drops"][-1] > 1800:
            DUAL["unstable"] = False
        self.was_conn = conn
        if self.n % 6 == 0 and conn and w.get("dbm") is not None:
            DUAL["sig"] = (DUAL["sig"] + [[int(now), w["dbm"]]])[-240:]          # one value per minute, 4 hours
        if (DUAL["on"] and DUAL["offline_since"] and now - DUAL["offline_since"] > 180 and now - DUAL["switch_t"] > 300
                and not WIFI.get("busy")):
            DUAL["switch_t"] = now
            cur = w.get("ssid") if conn else ""
            cand = [s for s in _visible_saved(DUAL["up"]) if s["ssid"] != cur]
            if cand:
                c = cand[0]
                code, _o, err = _run(["nmcli", "--wait", "40", "connection", "up", "uuid", c["id"], "ifname", DUAL["up"]], 50)
                dual_log(trf("No internet over «{a}» - changed to «{b}»", a=cur or "?", b=c["ssid"]) if code == 0
                         else trf("No internet - «{b}» did not work either", b=c["ssid"]))
                WIFI["refresh"] = True

    def loop(self):
        time.sleep(15)
        while True:
            try:
                self.step()
            except Exception as e:
                DUAL["msg"] = ("error: " + str(e))[:120]
            time.sleep(10)


# ---- devices in the own Wi-Fi without internet (e.g. cheap Wi-Fi cameras that "call home") ----
def noinet_apply(force=False):
    macs = sorted(m for m in (CFG.get("net_noinet") or []) if re.fullmatch(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}", m))
    key = ",".join(macs)
    if key == DUAL["iso"] and not force:
        return True
    nft, ipt = shutil.which("nft"), shutil.which("iptables")
    ok, err = False, ""
    if nft:
        _run([nft, "add", "table", "inet", "mw_iso"], 8); _run([nft, "delete", "table", "inet", "mw_iso"], 8)
        if macs:
            rules = ("table inet mw_iso {\n chain mwfwd {\n  type filter hook forward priority -10; policy accept;\n"
                     f"  ether saddr {{ {', '.join(macs)} }} drop\n }}\n}}\n")
            code, _o, e = _run([nft, "-f", "-"], 10, inp=rules)
            ok, err = code == 0, e
        else:
            ok = True
    elif ipt:
        _run([ipt, "-D", "FORWARD", "-j", "MW_ISO"], 8); _run([ipt, "-F", "MW_ISO"], 8); _run([ipt, "-X", "MW_ISO"], 8)
        ok = True
        if macs:
            code, _o, err = _run([ipt, "-N", "MW_ISO"], 8)
            for m in macs:
                c2, _o, e2 = _run([ipt, "-A", "MW_ISO", "-m", "mac", "--mac-source", m, "-j", "DROP"], 8)
                if c2:
                    err = e2
            c3, _o, e3 = _run([ipt, "-I", "FORWARD", "1", "-j", "MW_ISO"], 8)
            ok = code == 0 and c3 == 0 and not err
            err = err or e3
    else:
        err = "nft / iptables missing"
    if ok:
        DUAL["iso"] = key; DUAL["iso_msg"] = ""
        if macs or force:
            log_event("sys", f"Without internet: {len(macs)} device(s)")
    else:
        DUAL["iso_msg"] = _perm_hint((err or "error").strip())[:160]
    return ok


# ---- Wi-Fi guard: listens with the stick ("monitor mode") for deauthentication frames = the usual Wi-Fi jamming attack ----
_PRESENCE_SALT = {"day": "", "salt": b""}


def presence_eval():
    P = TOOLS["presence"]
    if not (CFG.get("presence_macs") or CFG.get("presence_bt")):
        return
    now = time.time()
    is_here = now - P.get("last", 0) < float(CFG.get("presence_gone_min", 10)) * 60
    if is_here != P["here"]:
        was = P["here"]; P.update(here=is_here, since=now)
        if was is not None:
            log_event("sys", "Presence: " + ("your device is back" if is_here else "your device is gone"))
            if CFG.get("mode") != "transport":                  # 2.97.0: not while travelling
                # 2.98.15: «Wenn mein Handy zurückkommt: ausschalten / fragen / nichts» (presence_back, 577); presence_auto = arm when gone
                if is_here and CFG["armed"] and presence_back_mode() == "off":
                    disarm(); log_event("sys", "Disarmed automatically (your device is here)")
                elif not is_here and CFG.get("presence_auto"):
                    if PRESENCE.get("home") is True:
                        log_event("sys", "Presence: your device is gone, but a device still answers the ping - not armed")
                    elif not CFG["armed"]:
                        arm(); log_event("sys", "Armed automatically (your device is gone)")


class WifiGuard:
    def __init__(self):
        self.sock = None; self.mon = ""
        threading.Thread(target=self.loop, daemon=True, name="wifiguard").start()

    def want(self):
        return bool(CFG.get("wifi_guard") or CFG.get("wifi_count") or (CFG.get("presence_macs") and CFG.get("wifi_presence")))

    def pick(self):
        ads = DUAL["adapters"] or wifi_adapters()
        cand = [a for a in ads if a["monitor"] and a["driver"] != "brcmfmac" and a["phy"]]
        cand.sort(key=lambda a: (a["iface"] != DUAL.get("up"), not a["usb"]))
        return cand[0] if cand else None

    def open(self):
        import socket
        a = self.pick()
        if a is None:
            WGUARD.update(state="no adapter", msg="no Wi-Fi adapter here can listen (monitor mode) - e.g. a stick with MediaTek MT7612U / MT7921AU")
            return False
        name = "mwmon0"
        if not os.path.exists(f"/sys/class/net/{name}"):
            code, _o, err = _run(["iw", "phy", a["phy"], "interface", "add", name, "type", "monitor"], 8)
            if code != 0:
                WGUARD.update(state="not possible", msg=_perm_hint(err.strip() or "monitor mode not possible")[:160]); return False
        _run(["ip", "link", "set", name, "up"], 8)
        if not a["up"] or (a["iface"] not in (DUAL.get("up"), DUAL.get("ap"), WIFI.get("iface"))):
            ch = None                                         # the stick is free: listen on the channel of the own Wi-Fi
            code, out, _e = _run(["iw", "dev", DUAL.get("ap") or WIFI.get("iface") or "wlan0", "info"], 5)
            m = re.search(r"channel (\d+)", out or "")
            if m:
                ch = m.group(1); _run(["iw", "dev", name, "set", "channel", ch], 5)
        try:
            s_ = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
            s_.bind((name, 0)); s_.settimeout(1.0)
        except (OSError, AttributeError) as e:
            WGUARD.update(state="not possible", msg=str(e)[:160]); return False
        self.sock, self.mon = s_, name
        WGUARD.update(state="listening", iface=a["iface"], phy=a["phy"], msg="")
        log_event("sys", f"Wi-Fi guard: listening with {a['iface']} ({a['chip']})")
        return True

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        if self.mon:
            _run(["iw", "dev", self.mon, "del"], 8); self.mon = ""
        WGUARD["state"] = "off"

    def own_bssids(self):
        own = set()
        for i in (DUAL.get("ap"), DUAL.get("up"), WIFI.get("iface")):
            if i:
                m = _rd(f"/sys/class/net/{i}/address")
                if m:
                    own.add(m.lower())
                code, out, _e = _run(["iw", "dev", i, "link"], 4)
                mm = re.search(r"Connected to ([0-9a-f:]{17})", out or "")
                if mm:
                    own.add(mm.group(1).lower())
        return own

    def loop(self):
        while True:                                     # 2.95.33: an error must not end the jamming detection for good
            try:
                self._loop()
            except Exception as e:
                log_event("sys", f"Wi-Fi guard error (restarted): {type(e).__name__}: {e}"[:200])
                time.sleep(30)

    def _loop(self):
        time.sleep(20)
        minute_t = time.time(); dea = dall = 0; seen = {}; own = set(); own_t = 0.0; mine = set()
        while True:
            beat("wifiguard", 600, "Wi-Fi guard")
            if not self.want():
                if self.sock is not None:
                    self.close()
                time.sleep(5); continue
            if self.sock is None:
                if not self.open():
                    time.sleep(120); continue
            now = time.time()
            if now - own_t > 60:
                own = self.own_bssids(); own_t = now; mine = set(CFG.get("presence_macs") or [])
                d_ = datetime.now().strftime("%Y%m%d")
                if _PRESENCE_SALT["day"] != d_:
                    _PRESENCE_SALT.update(day=d_, salt=os.urandom(16)); seen.clear()
            try:
                pkt = self.sock.recv(4096)
            except OSError as e:
                if "timed out" not in str(e):
                    WGUARD.update(state="error", msg=str(e)[:120]); self.close(); time.sleep(30); continue
                pkt = b""
            if len(pkt) > 8:
                rl = pkt[2] | (pkt[3] << 8)
                f = pkt[rl:]
                if len(f) >= 16:
                    fc = f[0]; typ = (fc >> 2) & 3; sub = (fc >> 4) & 15
                    WGUARD["frames"] += 1
                    a2 = f[10:16].hex(":")
                    if typ == 0 and sub in (10, 12) and len(f) >= 22:          # disassociation / deauthentication
                        dall += 1
                        if f[16:22].hex(":") in own or a2 in own or f[4:10].hex(":") in own:
                            dea += 1
                    elif typ == 0 and sub == 4 and CFG.get("wifi_count"):    # probe request: only counted, never stored
                        import hashlib
                        seen[hashlib.sha256(_PRESENCE_SALT["salt"] + f[10:16]).hexdigest()[:12]] = now
                    if mine and a2 in mine:
                        TOOLS["presence"]["last"] = now
            if now - minute_t >= 60:
                minute_t = now
                WGUARD["deauth_min"] = (WGUARD["deauth_min"] + [[int(now), dea, dall]])[-120:]
                WGUARD["deauth_now"], WGUARD["all_now"] = dea, dall
                if CFG.get("wifi_count"):
                    for k in [k for k, t_ in seen.items() if now - t_ > 300]:
                        seen.pop(k, None)
                    WGUARD["count_now"] = len(seen)
                    WGUARD["count_hist"] = (WGUARD["count_hist"] + [[int(now), len(seen)]])[-288:]
                else:
                    seen.clear(); WGUARD["count_now"] = None
                if CFG.get("wifi_guard") and (dea >= int(CFG.get("wifi_guard_thr", 20)) or dall >= 300) and (not WGUARD["last_alarm"] or now - WGUARD["last_alarm"] > 1800):
                    WGUARD["last_alarm"] = now
                    txt = trf("Wi-Fi jamming: {n} disconnect frames in one minute ({all} in total on the channel)", n=dea, all=dall)
                    WGUARD["alarms"] = ([{"t": now, "n": dea, "all": dall}] + WGUARD["alarms"])[:20]
                    log_event("tamper", txt)
                    w = WATCH_REF.get("w")
                    if w is not None:
                        w.notifier.alert("{name}: " + tr("Wi-Fi jamming attack"), txt, getattr(w, "frame_out", None))
                dea = dall = 0
                presence_eval()


def dual_state():
    hs = STATE.get("hotspot") or {}; w = STATE.get("wifi") or {}
    return {"on": DUAL["on"], "ap": DUAL["ap"], "up": DUAL["up"], "adapters": DUAL["adapters"], "msg": DUAL["msg"], "log": DUAL["log"][:12],
            "sig": DUAL["sig"][-120:], "unstable": DUAL["unstable"], "offline_since": DUAL["offline_since"], "iso_msg": DUAL["iso_msg"],
            "repeater": bool(DUAL["on"] and hs.get("on") and w.get("connected")), "hotspot": {"on": hs.get("on"), "ssid": hs.get("ssid"), "clients": hs.get("clients")},
            "uplink": {"ssid": w.get("ssid"), "dbm": w.get("dbm"), "pct": w.get("pct"), "connected": w.get("connected")},
            "online": (STATE.get("net") or {}).get("online"),
            "cfg": {k: CFG.get(k) for k in ("wifi_repeater", "wifi_swap", "wifi_guard", "wifi_guard_thr", "wifi_count", "wifi_presence", "net_inet_notify", "net_noinet")},
            "guard": {k: WGUARD[k] for k in ("state", "iface", "msg", "deauth_min", "deauth_now", "all_now", "frames", "alarms", "count_now", "count_hist")}}


def dual_set(key, value):
    if key in ("wifi_repeater", "wifi_swap"):
        CFG[key] = bool(value); save_settings(); DUAL["choice"] = None; dual_roles()
        if key == "wifi_repeater" and value:
            log_event("sys", "Repeater switched on by hand")
        if STATE["hotspot"].get("on"):
            hotspot_switch_later(True, 0.5)
        return True, ""
    if key in ("wifi_guard", "wifi_count", "wifi_presence", "net_inet_notify"):
        CFG[key] = bool(value); save_settings(); return True, ""
    if key == "wifi_guard_thr":
        try:
            CFG[key] = int(min(500, max(5, int(value)))); save_settings(); return True, ""
        except (TypeError, ValueError):
            return False, "bad value"
    return False, "unknown setting"


def noinet_set(mac, on):
    mac = str(mac or "").lower()
    if not re.fullmatch(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}", mac):
        return False, "bad address"
    L = [m for m in (CFG.get("net_noinet") or []) if m != mac]
    if on:
        L.append(mac)
    CFG["net_noinet"] = L[-30:]; save_settings()
    ok = noinet_apply(force=True)
    return ok, "" if ok else DUAL["iso_msg"]


