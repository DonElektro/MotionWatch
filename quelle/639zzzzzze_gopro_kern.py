#@ MoveEye – Teil 639zzzzzze_gopro_kern: GoPro als Zusatzkamera – Grundgerüst (GOPRO, gopro_register_weg, gopro_quelle) und HERO8 über GoPro Labs (QR-Codes + RTMP-Live-Strom, Empfänger mediamtx). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (#44, Fragebogen 28.11.2026): die GoPro (er hat eine HERO8 Black) wie eine Zusatzkamera einbinden –
# Erkennung, Aufnahme, Live-Bild, Drehen (cam_turn) wie bei den anderen Zusatzkameras (Teil 440). Drei Wege, drei Helfer:
#   rtmp       (G1, dieser Teil) HERO8 und neuer mit GoPro-Labs-Firmware: die GoPro liest QR-Codes und schickt einen RTMP-Strom
#   ble        (G2, 639zzzzzzf…) Open GoPro über Bluetooth (HERO9 und neuer)
#   hero8_ble  (G3, 639zzzzzzg…) HERO8 über Bluetooth (inoffiziell) und einen 2. WLAN-Stick
# Schnittstelle (verbindlich, /home/claude/helfer/gopro_schnittstelle.md):
#   GOPRO = {id: {"name", "modell", "weg", "zustand", "akku", "fehler", "quelle", …}}
#   gopro_register_weg(name, *, start, stop, status, faehig)   start(dev) -> Adresse für open_source, stop(dev),
#        status(dev) -> {"verbunden", "akku", "streamt", "fehler"}, faehig = {"titel", "modelle", "akku", "steuern"} oder fn(dev)
#   gopro_quelle(dev_id) -> str
# Eine GoPro ist die Quelle «gopro:<id>» (SRC_RE in Teil 200): eine Zusatzkamera wie jede andere (440 ExtraCam, cam_turn,
# Kamerawahl 639zzi). open_source fragt hier gopro_open -> der Weg liefert die Adresse (gopro_quelle) -> _open_url (200).
#
# GoPro Labs (offizielle Doku gopro.github.io/labs, Quelle github.com/gopro/labs docs/control/rtmp + docs/control/tech,
# nachgesehen 28.11.2026): «Pair with the GoPro mobile app once» (sonst kein Live-Strom), dann drei QR-Codes:
#   WLAN    !MJOIN="<ssid>:<passwort>"        (alte Schreibweise !M…, gilt bis HERO9 und auf allen Modellen; dauerhaft gespeichert)
#   Ziel    !MRTMP="rtmp://<pi>:<port>/gopro/<id>-<schlüssel>"
#   Start   oW1mVr1080!W!G<S|M|L>[C]       (S = 480p, M = 720p, L = 1080p, C = Kopie auf der Speicherkarte der GoPro;
#           HERO12 / 13 ohne «oW1mVr1080!W», genau wie der Generator auf der Labs-Seite)
# Das WLAN-Passwort wird NIE gespeichert und nie protokolliert: es kommt nur in der Anfrage für den QR-Code (POST, no-store)
# bzw. im Fenster aus einem Feld, das danach geleert wird; der QR-Code mit WLAN-Daten erscheint erst nach «anzeigen» und
# verschwindet nach 2 Minuten.
#
# Empfänger: mediamtx (MIT, github.com/bluenviron/mediamtx) als eigener Prozess, gestartet vom Faden «gopro-wache»
# (PR_SET_PDEATHSIG: stirbt MoveEye, geht er mit). RTMP auf dem eigenen Port gopro_rtmp_port (ab Werk 19350, alle
# Schnittstellen, Senden nur aus privaten Netzen = LAN / WLAN des Geräts, nicht Tailscale), RTSP und API nur auf 127.0.0.1
# (Port +1 / +2). Fehlt mediamtx: «Installieren» (mit Rückfrage) holt die feste Fassung MTX["version"] (Prüfsumme fest im
# Programm, sonst aus dem Release) nach DATA_DIR/gopro/bin; bis dahin ein einfacher Empfänger mit ffmpeg (eine GoPro).
# Abbruch: kommt GOPRO_ABBRUCH_S lang kein Strom mehr, Zustand «lost», eine stille Meldung (notifier.info, kein Alarm),
# die Seite zeigt wieder den Start-QR-Code. Steuern nur der Administrator (/gopro, /api/gopro: ADMIN_GET + Prüfung im Weg).
# Test: werkzeuge/gopro_test.py (nachgestellter Strom ffmpeg testsrc2 -> Empfänger -> MoveEye).
# ----------------------------------------------------------------------------
for _k, _v in {"gopro_devs": [], "gopro_rtmp_port": 19350, "gopro_mtx": ""}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
USER_SETTINGS_DENY.update({"gopro_devs", "gopro_rtmp_port", "gopro_mtx"})     # stream keys, programs: administrator only
ADMIN_GET = tuple(ADMIN_GET) + ("/gopro", "/api/gopro")


def gopro_cfg_dev(spec_or_id):
    """the saved entry of a GoPro (CFG gopro_devs) by «gopro:<id>» or <id>; None"""
    gid = str(spec_or_id or "").partition(":")[2] if str(spec_or_id or "").startswith("gopro:") else str(spec_or_id or "")
    return next((x for x in CFG.get("gopro_devs") or [] if isinstance(x, dict) and str(x.get("id")) == gid), None)


_open_source_gopro_base = open_source


# wraps: open_source
def open_source(spec, thermal=False):                     # + 639zzzzzze: a GoPro = the stream of its way (gopro_open, zip)
    if str(spec).startswith("gopro:") and not thermal and not DEMO["on"] and not HOST["on"]:
        try:
            return gopro_open(str(spec))
        except NameError:
            return None, spec, source_label(spec), "GoPro: additional data missing - update MoveEye"
        except Exception as e:                            # noqa: BLE001 - never takes another camera with it
            return None, spec, source_label(spec), ("GoPro: " + type(e).__name__ + ": " + str(e))[:160]
    return _open_source_gopro_base(spec, thermal)


_source_label_gopro_base = source_label


# wraps: source_label
def source_label(spec):                                   # + 639zzzzzze: «GoPro <name>»
    if str(spec).startswith("gopro:"):
        d = gopro_cfg_dev(spec)
        return ("GoPro " + str((d or {}).get("name") or "")[:30]).strip()
    return _source_label_gopro_base(spec)


GOPRO_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="referrer" content="no-referrer">
<title>MoveEye - GoPro</title>
<style>
/*BASECSS*/
main{padding:16px 16px 100px;max-width:760px;margin:0 auto}
.gp-back{display:inline-flex;align-items:center;min-height:40px;text-decoration:none;color:var(--acc);font-weight:600}
.gp-card{border:1px solid var(--line);border-radius:16px;background:var(--panel);padding:14px;margin:0 0 12px}
.gp-card h3{margin:0 0 6px;font-size:16px;text-transform:none;letter-spacing:0;color:inherit}
.gp-card p,.gp-card li{color:var(--mut);font-size:14px;margin:4px 0}.gp-card ol{margin:4px 0;padding-left:22px}
.gp-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;align-items:center}.gp-row>*{min-height:42px}
.gp-row input[type=text],.gp-row input[type=password],.gp-row select{flex:1 1 180px;min-width:0}
.gp-chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:13px;color:var(--mut)}
.gp-chip i{width:9px;height:9px;border-radius:50%;background:var(--mut);font-style:normal}
.gp-chip.ok i{background:var(--grn)}.gp-chip.wait i{background:var(--yel,#e0b040)}.gp-chip.bad i{background:var(--red)}
.gp-step{border-top:1px solid var(--line);margin-top:10px;padding-top:10px}
.gp-step b.n{display:inline-flex;width:24px;height:24px;border-radius:50%;background:var(--acc);color:#fff;align-items:center;justify-content:center;font-size:13px;margin-right:6px}
.gp-qr{background:#fff;border-radius:12px;padding:10px;margin-top:8px;max-width:300px}
.gp-qr svg{display:block;width:100%;height:auto}
.gp-code{font:12px/1.4 ui-monospace,Menlo,monospace;color:var(--mut);overflow-wrap:anywhere;margin-top:4px}
.gp-warn{color:var(--org,#e08a2c);font-size:14px;margin-top:6px}
.gp-sec{font-size:13px;color:var(--mut);margin-top:6px}
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
  <a class="gp-back" href="/cams">‹ <span data-i18n="Cameras">Cameras</span></a>
  <h2 style="margin:4px 0 10px">📹 <span data-i18n="Add GoPro">Add GoPro</span></h2>
  <section class="gp-card" id="gp-prep">
    <h3 data-i18n="Once before: prepare the GoPro">Once before: prepare the GoPro</h3>
    <ol>
      <li data-i18n="Pair the GoPro once with the GoPro app (Quik) - without that the GoPro does not send a live stream.">Pair the GoPro once with the GoPro app (Quik) - without that the GoPro does not send a live stream.</li>
      <li><span data-i18n="Install the GoPro Labs firmware (free, from GoPro): gopro.com/labs - then the GoPro reads QR codes.">Install the GoPro Labs firmware (free, from GoPro): gopro.com/labs - then the GoPro reads QR codes.</span>
        <a href="https://gopro.com/labs" target="_blank" rel="noopener noreferrer">gopro.com/labs</a></li>
      <li data-i18n="GoPro and MoveEye in the same Wi-Fi: home network, phone hotspot or the Wi-Fi of the device.">GoPro and MoveEye in the same Wi-Fi: home network, phone hotspot or the Wi-Fi of the device.</li>
    </ol>
  </section>
  <section class="gp-card" id="gp-rx"></section>
  <div id="gp-devs"></div>
  <section class="gp-card" id="gp-new">
    <h3 data-i18n="New GoPro">New GoPro</h3>
    <div class="gp-row">
      <input type="text" id="gp-name" maxlength="30" data-i18n-ph="Name" placeholder="Name">
      <select id="gp-modell" aria-label="Model"></select>
    </div>
    <div class="gp-row"><select id="gp-weg" aria-label="Way"></select></div>
    <div class="gp-row"><button type="button" id="gp-add" onclick="gpAdd()" data-i18n="Add GoPro">Add GoPro</button></div>
    <div class="err" id="gp-err"></div>
  </section>
</main>
<div id="toast"></div>
<script>
/*COMMON*/
Object.assign(I18N.de, /*GPDE*/{});
let S = null, SIG = "";
const L = () => LANG || "en";
const E = (tag, cls, text) => el(tag, cls, text);
const QRT = {};                                   // device id -> timer of a shown Wi-Fi code
async function load() {
  try { S = await (await fetch("/api/gopro?lang=" + L(), {cache: "no-store"})).json(); } catch (e) { return; }
  if (!S || !S.ok) { $("#gp-devs").textContent = (S && S.error) || ""; return; }
  rx(); fillNew();
  const sig = S.devs.map(d => d.id + d.aktiv + d.weg + d.modell).join("|") + L();
  if (sig !== SIG) { SIG = sig; const box = $("#gp-devs"); box.textContent = ""; S.devs.forEach(d => box.appendChild(card(d))); }
  S.devs.forEach(d => { const c = document.querySelector('.gp-card[data-id="' + d.id + '"]'); if (c && c._u) c._u(d); });
}
function chip(d) {
  const z = d.zustand, cls = z === "streaming" ? "ok" : (z === "lost" || z === "error") ? "bad" : z === "stopped" ? "" : "wait";
  const c = E("span", "gp-chip " + cls); c.append(E("i"), E("span", "", t(S.zustaende[z] || z))); return c;
}
function rx() {
  const r = S.rx, b = $("#gp-rx"); b.textContent = "";
  b.appendChild(E("h3", "", "📡 " + t("Receiver for the live stream")));
  const st = r.art === "mediamtx" ? "mediamtx " + (r.version || "") : r.art === "ffmpeg" ? t("simple receiver (ffmpeg, one GoPro)") : t("no receiver installed");
  const row = E("div", "gp-row"); row.appendChild(E("span", "gp-chip " + (r.art === "mediamtx" ? "ok" : r.art ? "wait" : "bad"), "")).append(E("i"), E("span", "", st));
  row.appendChild(E("span", "mut", t("Port") + " " + r.port + (r.laeuft ? " · " + t("running") : "")));
  b.appendChild(row);
  if (r.fehler) b.appendChild(E("div", "gp-warn", "⚠ " + r.fehler));
  if (r.art !== "mediamtx") {
    b.appendChild(E("p", "", t("mediamtx receives the stream of several GoPros reliably. MoveEye loads the fixed version from GitHub and checks it.") + " (" + r.mtx_version + ", " + r.arch + ")"));
    const ib = E("button", "sec", "⬇ " + t("Install mediamtx")); ib.type = "button"; ib.disabled = !!r.install.running || !r.arch_ok;
    ib.onclick = async () => { if (!confirm(t("Load and install mediamtx now (about 10 MB from github.com)?"))) return;
      const q = await post("/api/gopro", {action: "install", lang: L()}); toast(q.ok ? "⬇ …" : "⚠ " + (q.error || "")); load(); };
    const r2 = E("div", "gp-row"); r2.appendChild(ib); b.appendChild(r2);
    if (r.install.msg) b.appendChild(E("div", "gp-sec", r.install.msg));
  }
}
function fillNew() {
  const m = $("#gp-modell"), w = $("#gp-weg");
  if (!m.options.length) S.modelle.forEach(([k, n]) => { const o = E("option", "", n); o.value = k; m.appendChild(o); });
  const cur = w.value; w.textContent = "";
  S.wege.filter(x => x.modelle.includes(m.value)).forEach(x => { const o = E("option", "", t(x.titel)); o.value = x.name; w.appendChild(o); });
  if ([...w.options].some(o => o.value === cur)) w.value = cur;
  m.onchange = fillNew;
  $("#gp-add").disabled = !w.options.length;
}
async function gpAdd() {
  const q = await post("/api/gopro", {action: "add", name: $("#gp-name").value, modell: $("#gp-modell").value, weg: $("#gp-weg").value, lang: L()});
  $("#gp-err").textContent = q.ok ? "" : "⚠ " + (q.error || "");
  if (q.ok) { $("#gp-name").value = ""; SIG = ""; load(); }
}
async function qrInto(box, body, secs) {
  box.textContent = "";
  let r; try { r = await fetch("/api/gopro/qr", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body), cache: "no-store"}); } catch (e) { r = null; }
  if (!r || !r.ok) { let m = ""; try { m = (await r.json()).error; } catch (e) {} box.appendChild(E("div", "gp-warn", "⚠ " + (m || t("error")))); return false; }
  const q = E("div", "gp-qr"); q.innerHTML = await r.text(); box.appendChild(q);
  if (secs) { clearTimeout(QRT[body.id]); QRT[body.id] = setTimeout(() => { box.textContent = ""; box.appendChild(E("div", "gp-sec", "🔒 " + t("Hidden again (Wi-Fi data).")));}, secs * 1000); }
  return true;
}
function card(d) {
  const c = E("section", "gp-card"); c.dataset.id = d.id;
  const h = E("div", "gp-row"); h.style.marginTop = "0";
  const title = E("h3", "", "📹 " + d.label); title.style.flex = "1"; h.append(title);
  const ch = E("span"); h.appendChild(ch); c.appendChild(h);
  const info = E("div", "gp-sec"); c.appendChild(info);
  const warn = E("div", "gp-warn"); warn.hidden = true; c.appendChild(warn);
  if (d.weg === "rtmp") {
    // step 1: Wi-Fi (password only for the code, never saved)
    const s1 = E("div", "gp-step"); s1.appendChild(E("b", "n", "1")); s1.appendChild(E("b", "", t("Wi-Fi for the GoPro")));
    s1.appendChild(E("p", "", t("The GoPro remembers the Wi-Fi. The password is used only for this code - MoveEye does not save it.")));
    const net = E("select"); net.setAttribute("aria-label", t("Network"));
    S.netze.forEach(n => { const o = E("option", "", t(n.titel) + (n.ip ? " · " + n.ip : "")); o.value = n.id; net.appendChild(o); });
    const ssid = E("input"); ssid.type = "text"; ssid.maxLength = 32; ssid.placeholder = t("Wi-Fi name (SSID)"); ssid.autocomplete = "off";
    const pw = E("input"); pw.type = "password"; pw.maxLength = 63; pw.placeholder = t("Wi-Fi password"); pw.autocomplete = "new-password";
    const fillSsid = () => { const n = S.netze.find(x => x.id === net.value); if (n && n.ssid && !ssid.value) ssid.value = n.ssid; };
    net.onchange = fillSsid; fillSsid();
    const r1 = E("div", "gp-row"); r1.append(net); const r1b = E("div", "gp-row"); r1b.append(ssid, pw);
    const b1 = E("button", "sec", "▦ " + t("Show Wi-Fi code")); b1.type = "button";
    const q1 = E("div");
    b1.onclick = async () => { const v = pw.value; pw.value = "";
      await qrInto(q1, {id: d.id, art: "join", ssid: ssid.value, pw: v, lang: L()}, 120); };
    const r1c = E("div", "gp-row"); r1c.appendChild(b1);
    s1.append(r1, r1b, r1c, q1, E("div", "gp-sec", t("Show the code to the GoPro (it beeps / shows «QR code accepted»).")));
    c.appendChild(s1);
    // step 2: address of the receiver
    const s2 = E("div", "gp-step"); s2.appendChild(E("b", "n", "2")); s2.appendChild(E("b", "", t("Where the GoPro sends the picture")));
    const ip = E("input"); ip.type = "text"; ip.maxLength = 45; ip.setAttribute("aria-label", t("Address of MoveEye")); ip.value = d.ip || "";
    const b2 = E("button", "sec", "▦ " + t("Show address code")); b2.type = "button"; const q2 = E("div");
    const cd2 = E("div", "gp-code");
    b2.onclick = async () => { if (await qrInto(q2, {id: d.id, art: "rtmp", ip: ip.value, lang: L()}, 0)) cd2.textContent = "rtmp://" + ip.value + ":" + S.rx.port + "/gopro/…"; };
    const r2 = E("div", "gp-row"); r2.append(ip, b2);
    s2.append(E("p", "", t("The address of MoveEye in the network of the GoPro (filled in by itself).")), r2, q2, cd2);
    c.appendChild(s2);
    // step 3: start
    const s3 = E("div", "gp-step"); s3.appendChild(E("b", "n", "3")); s3.appendChild(E("b", "", t("Start the live stream")));
    const res = E("select"); res.setAttribute("aria-label", t("Resolution"));
    [["480", "480p"], ["720", "720p"], ["1080", "1080p"]].forEach(([k, n]) => { const o = E("option", "", n); o.value = k; res.appendChild(o); });
    res.value = d.res;
    const cpl = E("label", "mut"); const cp = E("input"); cp.type = "checkbox"; cp.checked = !!d.copy; cpl.append(cp, " " + t("Also record on the memory card of the GoPro"));
    const sv = async () => { const q = await post("/api/gopro", {action: "set", id: d.id, res: res.value, copy: cp.checked, lang: L()}); if (!q.ok) toast("⚠ " + (q.error || "")); else { c._qr = ""; load(); } };
    res.onchange = sv; cp.onchange = sv;
    const r3 = E("div", "gp-row"); r3.append(res, cpl);
    const q3 = E("div"), cd3 = E("div", "gp-code");
    s3.append(E("p", "", t("Show this code to the GoPro: it joins the Wi-Fi and sends the picture to MoveEye. It works again and again - print it if you like.")), r3, q3, cd3,
              E("div", "gp-sec", t("Stop: end the live stream on the GoPro (shutter button) or switch it off.")));
    c.appendChild(s3);
    c._q3 = q3; c._cd3 = cd3;
  }
  const bt = E("div", "gp-row");
  const bs = E("button", "", "▶ " + t("Start")); bs.type = "button";
  const bp = E("button", "sec", "■ " + t("Stop")); bp.type = "button";
  const bx = E("button", "sec", "✕ " + t("Remove")); bx.type = "button";
  bs.onclick = async () => { await post("/api/gopro", {action: "start", id: d.id, lang: L()}); c._qr = ""; load(); };
  bp.onclick = async () => { await post("/api/gopro", {action: "stop", id: d.id, lang: L()}); load(); };
  bx.onclick = async () => { if (!confirm(t("Remove this GoPro?"))) return; await post("/api/gopro", {action: "remove", id: d.id, lang: L()}); SIG = ""; load(); };
  bt.append(bs, bp, bx); c.appendChild(bt);
  c._u = async d2 => {
    ch.textContent = ""; ch.appendChild(chip(d2));
    info.textContent = [d2.modell_name, t(S.wege_titel[d2.weg] || d2.weg), d2.res + "p", d2.akku != null ? "🔋 " + d2.akku + " %" : "", d2.cam || ""].filter(Boolean).join(" · ");
    warn.hidden = !d2.fehler && !d2.hinweis; warn.textContent = "⚠ " + [d2.fehler, d2.hinweis].filter(Boolean).join(" · ");
    bs.hidden = d2.aktiv; bp.hidden = !d2.aktiv;
    if (c._q3) {                                   // the start code: while it waits or after a drop-out (not while streaming)
      const want = d2.aktiv && d2.zustand !== "streaming";
      const key = want ? d2.start_qr : "";
      if (key !== c._qr) { c._qr = key; c._q3.textContent = ""; c._cd3.textContent = "";
        if (want) { await qrInto(c._q3, {id: d2.id, art: "start", lang: L()}, 0); c._cd3.textContent = d2.start_qr; }
        else if (d2.zustand === "streaming") c._q3.appendChild(E("div", "gp-sec", "✓ " + t("The GoPro sends the picture.")));
      }
    }
  };
  return c;
}
(async () => { await initAppearance(); load(); setInterval(load, 2000); })();
/*ALERTS*/
</script></body></html>
"""


GOPRO_KERN_PY = r'''import platform as _gplat
import tarfile as _gptar
import urllib.parse as _gpup

GOPRO = {}                       # id -> {"name", "modell", "weg", "zustand", "akku", "fehler", "quelle", "aktiv", "res", "copy", …}
GOPRO_WEGE = {}                  # name -> {"start", "stop", "status", "faehig"}
_GP_LOCK = threading.RLock()
GOPRO_ABBRUCH_S = 8.0            # no stream for so long = dropped out (the GoPro needs a few seconds to start)
GOPRO_MELDUNG_S = 600.0          # at most one quiet message per GoPro in 10 minutes
GOPRO_ZUSTAENDE = {"new": "new", "waiting": "waiting for the GoPro", "streaming": "picture is coming", "lost": "stream dropped out",
                   "stopped": "stopped", "error": "error"}
GOPRO_MODELLE = [("hero8", "HERO8 Black"), ("hero9", "HERO9 Black"), ("hero10", "HERO10 Black"), ("hero11", "HERO11 Black"),
                 ("hero12", "HERO12 Black"), ("hero13", "HERO13 Black")]
GOPRO_RES = {"480": "S", "720": "M", "1080": "L"}
# mediamtx: fixed version; the checksums of the packages are pinned here as soon as they are measured (werkzeuge/gopro_test.py
# --mtx-pruefsummen), until then the checksum list of the same release (https, github.com) is used - never an unchecked file
MTX = {"version": "v1.21.4", "url": "https://github.com/bluenviron/mediamtx/releases/download/",
       "pins": {"arm64": None, "armv7": None, "amd64": None}, "max": 80 * 1048576}
RX = {"proc": None, "art": "", "paths": [], "fehler": "", "t_start": 0.0, "fails": 0, "api": {}, "t_api": 0.0, "ff_dev": "",
      "ff_in": False, "version": "", "install": {"running": False, "msg": "", "done": False, "got": 0, "total": 0}}
_GP_W = {"thread": None}
_GP_PRIV = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16", "127.0.0.1/32", "fd00::/8", "fe80::/10", "::1/128"]

_HX_GP = {
    "Add GoPro": ("GoPro hinzufügen", "Ajouter une GoPro", "Aggiungi GoPro", "Agiuntar ina GoPro"),
    "Once before: prepare the GoPro": ("Einmal vorher: GoPro vorbereiten", "Une fois avant : préparer la GoPro", "Una volta prima: preparare la GoPro",
                                       "Ina giada avant: preparar la GoPro"),
    "Pair the GoPro once with the GoPro app (Quik) - without that the GoPro does not send a live stream.":
        ("Die GoPro einmal mit der GoPro-App (Quik) koppeln – sonst sendet die GoPro keinen Live-Strom.",
         "Associer une fois la GoPro à l'app GoPro (Quik) – sinon la GoPro n'envoie pas de flux en direct.",
         "Associa una volta la GoPro all'app GoPro (Quik) – altrimenti la GoPro non invia lo streaming dal vivo.",
         "Colliar ina giada la GoPro cun l'app GoPro (Quik) – uschiglio na trametta la GoPro nagin stream live."),
    "Install the GoPro Labs firmware (free, from GoPro): gopro.com/labs - then the GoPro reads QR codes.":
        ("Die GoPro-Labs-Firmware installieren (gratis, von GoPro): gopro.com/labs – dann liest die GoPro QR-Codes.",
         "Installer le firmware GoPro Labs (gratuit, de GoPro) : gopro.com/labs – la GoPro lit alors les codes QR.",
         "Installa il firmware GoPro Labs (gratuito, di GoPro): gopro.com/labs – poi la GoPro legge i codici QR.",
         "Installar il firmware GoPro Labs (gratuit, da GoPro): gopro.com/labs – lura legia la GoPro codes QR."),
    "GoPro and MoveEye in the same Wi-Fi: home network, phone hotspot or the Wi-Fi of the device.":
        ("GoPro und MoveEye im selben WLAN: Heimnetz, Handy-Hotspot oder das WLAN des Geräts.",
         "GoPro et MoveEye dans le même Wi-Fi : réseau domestique, partage de connexion du téléphone ou le Wi-Fi de l'appareil.",
         "GoPro e MoveEye nella stessa Wi-Fi: rete di casa, hotspot del telefono o la Wi-Fi del dispositivo.",
         "GoPro e MoveEye en il medem WLAN: rait da chasa, hotspot dal telefonin u il WLAN da l'apparat."),
    "Receiver for the live stream": ("Empfänger für den Live-Strom", "Récepteur du flux en direct", "Ricevitore dello streaming",
                                     "Retschavider per il stream live"),
    "simple receiver (ffmpeg, one GoPro)": ("einfacher Empfänger (ffmpeg, eine GoPro)", "récepteur simple (ffmpeg, une GoPro)",
                                            "ricevitore semplice (ffmpeg, una GoPro)", "retschavider simpel (ffmpeg, ina GoPro)"),
    "no receiver installed": ("kein Empfänger installiert", "aucun récepteur installé", "nessun ricevitore installato", "nagin retschavider installà"),
    "Port": ("Port", "Port", "Porta", "Port"),
    "running": ("läuft", "en marche", "in funzione", "funcziuna"),
    "mediamtx receives the stream of several GoPros reliably. MoveEye loads the fixed version from GitHub and checks it.":
        ("mediamtx empfängt den Strom mehrerer GoPros zuverlässig. MoveEye lädt die feste Fassung von GitHub und prüft sie.",
         "mediamtx reçoit de façon fiable le flux de plusieurs GoPro. MoveEye charge la version fixe depuis GitHub et la vérifie.",
         "mediamtx riceve in modo affidabile lo streaming di più GoPro. MoveEye carica la versione fissa da GitHub e la verifica.",
         "mediamtx retschaiva fidaivlamain il stream da pliras GoPros. MoveEye chargia la versiun fixa da GitHub e la controllescha."),
    "Install mediamtx": ("mediamtx installieren", "Installer mediamtx", "Installa mediamtx", "Installar mediamtx"),
    "Load and install mediamtx now (about 10 MB from github.com)?": ("mediamtx jetzt laden und installieren (etwa 10 MB von github.com)?",
                                                                     "Charger et installer mediamtx maintenant (environ 10 Mo depuis github.com) ?",
                                                                     "Caricare e installare mediamtx ora (circa 10 MB da github.com)?",
                                                                     "Chargiar ed installar ussa mediamtx (circa 10 MB da github.com)?"),
    "New GoPro": ("Neue GoPro", "Nouvelle GoPro", "Nuova GoPro", "Nova GoPro"),
    "Name": ("Name", "Nom", "Nome", "Num"),
    "HERO8 and newer: QR codes + live stream (GoPro Labs)": ("HERO8 und neuer: QR-Codes + Live-Strom (GoPro Labs)",
                                                             "HERO8 et plus récentes : codes QR + flux en direct (GoPro Labs)",
                                                             "HERO8 e successive: codici QR + streaming (GoPro Labs)",
                                                             "HERO8 e pli novas: codes QR + stream live (GoPro Labs)"),
    "Wi-Fi for the GoPro": ("WLAN für die GoPro", "Wi-Fi pour la GoPro", "Wi-Fi per la GoPro", "WLAN per la GoPro"),
    "The GoPro remembers the Wi-Fi. The password is used only for this code - MoveEye does not save it.":
        ("Die GoPro merkt sich das WLAN. Das Passwort dient nur für diesen Code – MoveEye speichert es nicht.",
         "La GoPro mémorise le Wi-Fi. Le mot de passe sert uniquement à ce code – MoveEye ne l'enregistre pas.",
         "La GoPro memorizza la Wi-Fi. La password serve solo per questo codice – MoveEye non la salva.",
         "La GoPro memorisescha il WLAN. Il pled-clav serva mo per quest code – MoveEye n'al memorisescha betg."),
    "Network": ("Netz", "Réseau", "Rete", "Rait"),
    "Home network": ("Heimnetz", "Réseau domestique", "Rete di casa", "Rait da chasa"),
    "Wi-Fi of the device": ("WLAN des Geräts", "Wi-Fi de l'appareil", "Wi-Fi del dispositivo", "WLAN da l'apparat"),
    "Wi-Fi name (SSID)": ("WLAN-Name (SSID)", "Nom du Wi-Fi (SSID)", "Nome Wi-Fi (SSID)", "Num dal WLAN (SSID)"),
    "Wi-Fi password": ("WLAN-Passwort", "Mot de passe Wi-Fi", "Password Wi-Fi", "Pled-clav dal WLAN"),
    "Show Wi-Fi code": ("WLAN-Code anzeigen", "Afficher le code Wi-Fi", "Mostra codice Wi-Fi", "Mussar il code WLAN"),
    "Hidden again (Wi-Fi data).": ("Wieder verborgen (WLAN-Daten).", "Masqué à nouveau (données Wi-Fi).", "Di nuovo nascosto (dati Wi-Fi).",
                                   "Puspè zuppà (datas dal WLAN)."),
    "Show the code to the GoPro (it beeps / shows «QR code accepted»).": ("Den Code der GoPro zeigen (sie piepst bzw. meldet, dass sie den Code gelesen hat).",
                                                                        "Montrer le code à la GoPro (elle bipe / indique qu'elle a lu le code).",
                                                                        "Mostra il codice alla GoPro (emette un bip / indica di aver letto il codice).",
                                                                        "Mussar il code a la GoPro (ella piepa / annunzia ch'ella ha legì il code)."),
    "Where the GoPro sends the picture": ("Wohin die GoPro das Bild schickt", "Où la GoPro envoie l'image", "Dove la GoPro invia l'immagine",
                                          "Nua che la GoPro trametta il maletg"),
    "Address of MoveEye": ("Adresse von MoveEye", "Adresse de MoveEye", "Indirizzo di MoveEye", "Adressa da MoveEye"),
    "Show address code": ("Adress-Code anzeigen", "Afficher le code d'adresse", "Mostra codice indirizzo", "Mussar il code da l'adressa"),
    "The address of MoveEye in the network of the GoPro (filled in by itself).": ("Die Adresse von MoveEye im Netz der GoPro (von selbst ausgefüllt).",
                                                                                  "L'adresse de MoveEye dans le réseau de la GoPro (remplie automatiquement).",
                                                                                  "L'indirizzo di MoveEye nella rete della GoPro (compilato da solo).",
                                                                                  "L'adressa da MoveEye en la rait da la GoPro (emplenida automaticamain)."),
    "Start the live stream": ("Live-Strom starten", "Démarrer le flux en direct", "Avviare lo streaming", "Aviar il stream live"),
    "Resolution": ("Auflösung", "Résolution", "Risoluzione", "Resoluziun"),
    "Also record on the memory card of the GoPro": ("Zusätzlich auf der Speicherkarte der GoPro aufnehmen", "Enregistrer aussi sur la carte mémoire de la GoPro",
                                                    "Registra anche sulla scheda di memoria della GoPro", "Registrar era sin la carta da memoria da la GoPro"),
    "Show this code to the GoPro: it joins the Wi-Fi and sends the picture to MoveEye. It works again and again - print it if you like.":
        ("Diesen Code der GoPro zeigen: sie verbindet sich mit dem WLAN und schickt das Bild an MoveEye. Er funktioniert immer wieder – gern ausdrucken.",
         "Montre ce code à la GoPro : elle se connecte au Wi-Fi et envoie l'image à MoveEye. Il fonctionne à chaque fois – imprime-le si tu veux.",
         "Mostra questo codice alla GoPro: si collega alla Wi-Fi e invia l'immagine a MoveEye. Funziona sempre – stampalo se vuoi.",
         "Mussar quest code a la GoPro: ella sa colliescha cun il WLAN e trametta il maletg a MoveEye. El funcziuna adina puspè – stampar sche ti vuls."),
    "Stop: end the live stream on the GoPro (shutter button) or switch it off.": ("Beenden: an der GoPro den Live-Strom beenden (Auslöser) oder sie ausschalten.",
                                                                                 "Arrêter : terminer le flux sur la GoPro (déclencheur) ou l'éteindre.",
                                                                                 "Fermare: termina lo streaming sulla GoPro (pulsante di scatto) o spegnila.",
                                                                                 "Terminar: finir il stream live sin la GoPro (buttun da sviluppar) u la stizzar."),
    "Start": ("Start", "Démarrer", "Avvia", "Aviar"),
    "Stop": ("Stopp", "Arrêter", "Ferma", "Fermar"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "Remove this GoPro?": ("Diese GoPro entfernen?", "Supprimer cette GoPro ?", "Rimuovere questa GoPro?", "Allontanar questa GoPro?"),
    "The GoPro sends the picture.": ("Die GoPro schickt das Bild.", "La GoPro envoie l'image.", "La GoPro invia l'immagine.", "La GoPro trametta il maletg."),
    "new": ("neu", "nouvelle", "nuova", "nov"),
    "waiting for the GoPro": ("wartet auf die GoPro", "attend la GoPro", "in attesa della GoPro", "spetga sin la GoPro"),
    "picture is coming": ("Bild kommt", "l'image arrive", "l'immagine arriva", "il maletg arriva"),
    "stream dropped out": ("Strom abgebrochen", "flux interrompu", "streaming interrotto", "stream interrut"),
    "stopped": ("gestoppt", "arrêtée", "fermata", "fermà"),
    "error": ("Fehler", "erreur", "errore", "errur"),
    "GoPro {n}: the live picture dropped out. To start it again show the start code (Cameras → GoPro).":
        ("GoPro {n}: das Live-Bild ist abgebrochen. Zum Neustart den Start-Code zeigen (Kameras → GoPro).",
         "GoPro {n} : l'image en direct s'est interrompue. Pour la relancer, montre le code de démarrage (Caméras → GoPro).",
         "GoPro {n}: l'immagine dal vivo si è interrotta. Per riavviarla mostra il codice di avvio (Telecamere → GoPro).",
         "GoPro {n}: il maletg live è interrut. Per l'aviar danovamain mussar il code d'aviament (Cameras → GoPro)."),
    "The address of MoveEye has changed since the address code was shown ({a} → {b}) - show the address code again.":
        ("Die Adresse von MoveEye hat sich seit dem Adress-Code geändert ({a} → {b}) – den Adress-Code nochmals zeigen.",
         "L'adresse de MoveEye a changé depuis le code d'adresse ({a} → {b}) – montre à nouveau le code d'adresse.",
         "L'indirizzo di MoveEye è cambiato dopo il codice indirizzo ({a} → {b}) – mostra di nuovo il codice indirizzo.",
         "L'adressa da MoveEye è sa midada dapi il code da l'adressa ({a} → {b}) – mussar anc ina giada il code da l'adressa."),
    "unknown GoPro": ("unbekannte GoPro", "GoPro inconnue", "GoPro sconosciuta", "GoPro nunenconuschenta"),
    "unknown way": ("unbekannter Weg", "voie inconnue", "via sconosciuta", "via nunenconuschenta"),
    "unknown model": ("unbekanntes Modell", "modèle inconnu", "modello sconosciuto", "model nunenconuschent"),
    "this way does not work with this model": ("dieser Weg geht mit diesem Modell nicht", "cette voie ne marche pas avec ce modèle",
                                               "questa via non funziona con questo modello", "questa via na funcziuna betg cun quest model"),
    "maximum 6 GoPros": ("höchstens 6 GoPros", "au maximum 6 GoPro", "al massimo 6 GoPro", "maximalmain 6 GoPros"),
    "Wi-Fi name missing": ("WLAN-Name fehlt", "nom du Wi-Fi manquant", "manca il nome Wi-Fi", "il num dal WLAN manca"),
    "the Wi-Fi name or password contains a character the GoPro cannot read (\" or line break; «:» in the name)":
        ("WLAN-Name oder Passwort enthält ein Zeichen, das die GoPro nicht lesen kann (\" oder Zeilenumbruch; «:» im Namen)",
         "le nom ou le mot de passe du Wi-Fi contient un caractère illisible pour la GoPro (\" ou saut de ligne ; «:» dans le nom)",
         "il nome o la password Wi-Fi contiene un carattere che la GoPro non sa leggere (\" o a capo; «:» nel nome)",
         "il num u il pled-clav dal WLAN cuntegna in caracter che la GoPro na po betg leger (\" u midada da lingia; «:» en il num)"),
    "invalid address": ("ungültige Adresse", "adresse non valable", "indirizzo non valido", "adressa nunvalaivla"),
    "no address of MoveEye known - type it in": ("keine Adresse von MoveEye bekannt – bitte eintippen", "aucune adresse de MoveEye connue – saisis-la",
                                                 "nessun indirizzo di MoveEye noto – inseriscilo", "nagina adressa da MoveEye enconuschenta – tippar ella"),
    "already running": ("läuft schon", "déjà en cours", "già in corso", "funcziuna gia"),
    "no package for this computer": ("kein Paket für diesen Rechner", "aucun paquet pour cet ordinateur", "nessun pacchetto per questo computer",
                                     "nagin pachet per quest computer"),
    "mediamtx installed": ("mediamtx installiert", "mediamtx installé", "mediamtx installato", "mediamtx installà"),
    "checksum from the release list (not yet fixed in the program)": ("Prüfsumme aus der Liste des Releases (noch nicht fest im Programm)",
                                                                      "somme de contrôle de la liste de la version (pas encore fixée dans le programme)",
                                                                      "checksum dall'elenco della release (non ancora fisso nel programma)",
                                                                      "summa da controlla da la glista da la versiun (anc betg fixa en il program)"),
    "waiting for the GoPro stream": ("wartet auf den Strom der GoPro", "attend le flux de la GoPro", "in attesa dello streaming della GoPro",
                                     "spetga sin il stream da la GoPro"),
    "GoPro stopped": ("GoPro gestoppt", "GoPro arrêtée", "GoPro fermata", "GoPro fermada"),
    "the receiver stopped right after the start": ("der Empfänger stoppte gleich nach dem Start", "le récepteur s'est arrêté juste après le démarrage",
                                                   "il ricevitore si è fermato subito dopo l'avvio", "il retschavider è sa fermà gist suenter l'aviament"),
    "no receiver - install mediamtx or ffmpeg": ("kein Empfänger – mediamtx oder ffmpeg installieren", "aucun récepteur – installe mediamtx ou ffmpeg",
                                                 "nessun ricevitore – installa mediamtx o ffmpeg", "nagin retschavider – installar mediamtx u ffmpeg"),
    "the simple receiver takes only one GoPro - install mediamtx": ("der einfache Empfänger nimmt nur eine GoPro – mediamtx installieren",
                                                                   "le récepteur simple ne prend qu'une GoPro – installe mediamtx",
                                                                   "il ricevitore semplice accetta una sola GoPro – installa mediamtx",
                                                                   "il retschavider simpel prenda mo ina GoPro – installar mediamtx"),
    "GoPro (live stream)": ("GoPro (Live-Strom)", "GoPro (flux en direct)", "GoPro (streaming)", "GoPro (stream live)"),
    "Add GoPro …": ("GoPro hinzufügen …", "Ajouter une GoPro …", "Aggiungi GoPro …", "Agiuntar ina GoPro …"),
    "Open in the browser": ("Im Browser öffnen", "Ouvrir dans le navigateur", "Apri nel browser", "Avrir en il navigatur"),
    "Close": ("Schliessen", "Fermer", "Chiudi", "Serrar"),
    "Only for the administrator": ("Nur für den Administrator", "Réservé à l'administrateur", "Solo per l'amministratore", "Mo per l'administratur"),
}
for _k, _v in _HX_GP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- the interface for the ways (G1 rtmp, G2 ble, G3 hero8_ble) -------------------------------------------------------------
def gopro_register_weg(name, *, start, stop, status, faehig):
    """a way registers itself: start(dev) -> address for open_source, stop(dev), status(dev) -> {"verbunden", "akku", "streamt",
    "fehler"}, faehig = {"titel": English text, "modelle": [ids of GOPRO_MODELLE], "akku": bool, "steuern": bool} or fn(dev)->bool"""
    if not re.fullmatch(r"[a-z0-9_]{1,20}", str(name or "")) or not all(callable(f) for f in (start, stop, status)):
        raise ValueError("gopro_register_weg: name a-z0-9_, start / stop / status callable")
    GOPRO_WEGE[name] = {"start": start, "stop": stop, "status": status, "faehig": faehig}
    return True


def _gp_weg_info(name):
    w = GOPRO_WEGE.get(name) or {}
    f = w.get("faehig")
    f = f if isinstance(f, dict) else {}
    return {"name": name, "titel": str(f.get("titel") or name), "modelle": list(f.get("modelle") or [m for m, _n in GOPRO_MODELLE]),
            "akku": bool(f.get("akku")), "steuern": bool(f.get("steuern"))}


def _gp_weg_ok(name, modell):
    w = GOPRO_WEGE.get(name)
    if not w:
        return False
    f = w.get("faehig")
    if callable(f):
        try:
            return bool(f({"modell": modell}))
        except Exception:
            return False
    return modell in _gp_weg_info(name)["modelle"]


def gopro_sync():
    """CFG gopro_devs -> GOPRO (runtime fields stay); returns GOPRO"""
    with _GP_LOCK:
        seen = set()
        for d in CFG.get("gopro_devs") or []:
            if not isinstance(d, dict) or not re.fullmatch(r"[0-9a-f]{8}", str(d.get("id") or "")):
                continue
            gid = d["id"]; seen.add(gid)
            g = GOPRO.setdefault(gid, {"id": gid, "zustand": "new", "akku": None, "fehler": "", "quelle": "", "t_stream": 0.0,
                                      "t_meld": 0.0, "hinweis": ""})
            for k in ("name", "modell", "weg", "key", "res", "copy", "aktiv", "ip", "x"):
                g[k] = d.get(k)
            g["res"] = g["res"] if g["res"] in GOPRO_RES else "720"
            g["aktiv"] = bool(g["aktiv"]); g["copy"] = bool(g["copy"]); g["spec"] = "gopro:" + gid
        for gid in list(GOPRO):
            if gid not in seen:
                GOPRO.pop(gid, None)
        return GOPRO


def gopro_dev(gid):
    gopro_sync()
    return GOPRO.get(str(gid or ""))


def gopro_quelle(dev_id):
    """the address of the video source MoveEye opens for this GoPro (from its way: start(dev)); "" while there is none"""
    dev = gopro_dev(dev_id)
    if not dev:
        return ""
    w = GOPRO_WEGE.get(dev.get("weg"))
    if not w:
        return ""
    if not dev.get("quelle"):
        dev["quelle"] = str(w["start"](dev) or "")
    return dev["quelle"]


def gopro_status(gid):
    dev = gopro_dev(gid)
    w = GOPRO_WEGE.get((dev or {}).get("weg"))
    if not dev or not w:
        return {"verbunden": False, "akku": None, "streamt": False, "fehler": "unknown GoPro"}
    try:
        st = w["status"](dev) or {}
    except Exception as e:                                # noqa: BLE001 - a way must not stop the others
        st = {"fehler": f"{type(e).__name__}: {e}"[:120]}
    return {"verbunden": bool(st.get("verbunden")), "akku": st.get("akku"), "streamt": bool(st.get("streamt")), "fehler": str(st.get("fehler") or "")}


def gopro_open(spec):
    """open_source for «gopro:<id>» (the hook in the main file): only while the way says the stream is there"""
    gid = spec.partition(":")[2]; label = source_label(spec)
    gopro_wache_an()
    dev = gopro_dev(gid)
    if not dev:
        return None, spec, label, "unknown GoPro"
    if not dev.get("aktiv"):
        return None, spec, label, "GoPro stopped"
    url = gopro_quelle(gid)
    if not gopro_status(gid)["streamt"] or not url:
        return None, spec, label, "waiting for the GoPro stream"
    src = _open_url(url)
    return (src, spec, label, "") if src else (None, spec, label, "waiting for the GoPro stream")


# ---- devices: add, remove, start, stop -------------------------------------------------------------------------------------
def _gp_save(devs):
    CFG["gopro_devs"] = devs
    save_settings()


def gopro_add(name, modell="hero8", weg="rtmp", **extra):
    """a new GoPro (also as extra camera); (ok, error, id)"""
    if modell not in dict(GOPRO_MODELLE):
        return False, "unknown model", ""
    if weg not in GOPRO_WEGE:
        return False, "unknown way", ""
    if not _gp_weg_ok(weg, modell):
        return False, "this way does not work with this model", ""
    devs = [d for d in CFG.get("gopro_devs") or [] if isinstance(d, dict)]
    if len(devs) >= 6:
        return False, "maximum 6 GoPros", ""
    nm = re.sub(r"[\x00-\x1f<>\"]", "", str(name or "")).strip()[:30] or dict(GOPRO_MODELLE)[modell]
    gid = secrets.token_hex(4)
    d = {"id": gid, "name": nm, "modell": modell, "weg": weg, "key": secrets.token_hex(8), "res": "720", "copy": False, "aktiv": True,
         "ip": "", "x": {k: v for k, v in extra.items() if isinstance(v, (str, int, float, bool))}}
    _gp_save(devs + [d])
    gopro_sync()
    ok, err = cams_add("gopro:" + gid)
    if not ok:
        _gp_save([x for x in CFG["gopro_devs"] if x.get("id") != gid]); gopro_sync()
        return False, err, ""
    log_event("sys", f"GoPro added: {nm} ({dict(GOPRO_MODELLE)[modell]}, way {weg})")
    gopro_wache_an()
    return True, "", gid


def _gp_set(gid, **kw):
    devs = [dict(d) for d in CFG.get("gopro_devs") or [] if isinstance(d, dict)]
    for d in devs:
        if d.get("id") == gid:
            d.update(kw)
    _gp_save(devs); gopro_sync()


def gopro_remove(gid):
    dev = gopro_dev(gid)
    if not dev:
        return False, "unknown GoPro"
    gopro_stop(gid, log=False)
    if dev["spec"] in (CFG.get("extra_cams") or []):
        cams_remove(dev["spec"])
    _gp_save([d for d in CFG.get("gopro_devs") or [] if isinstance(d, dict) and d.get("id") != gid])
    gopro_sync()
    log_event("sys", f"GoPro removed: {dev['name']}")
    return True, ""


def gopro_start(gid):
    dev = gopro_dev(gid)
    if not dev:
        return False, "unknown GoPro"
    if not dev["aktiv"]:
        _gp_set(gid, aktiv=True)
    dev = gopro_dev(gid); dev["quelle"] = ""; dev["zustand"] = "waiting"; dev["t_stream"] = 0.0
    if dev["spec"] not in (CFG.get("extra_cams") or []):
        ok, err = cams_add(dev["spec"])
        if not ok:
            return False, err
    gopro_wache_an()
    log_event("sys", f"GoPro {dev['name']}: start")
    return True, ""


def gopro_stop(gid, log=True):
    dev = gopro_dev(gid)
    if not dev:
        return False, "unknown GoPro"
    w = GOPRO_WEGE.get(dev["weg"])
    try:
        if w:
            w["stop"](dev)
    except Exception as e:                                # noqa: BLE001
        log_event("sys", f"GoPro {dev['name']}: stop: {type(e).__name__}")
    if dev["aktiv"]:
        _gp_set(gid, aktiv=False)
    dev = gopro_dev(gid); dev["quelle"] = ""; dev["zustand"] = "stopped"
    if dev["spec"] in (CFG.get("extra_cams") or []):
        cams_remove(dev["spec"])
    if log:
        log_event("sys", f"GoPro {dev['name']}: stopped")
    return True, ""


# ---- the watch: state, drop-out, quiet message ----------------------------------------------------------------------------
def gopro_wache_an():
    with _GP_LOCK:
        t_ = _GP_W["thread"]
        if t_ is None or not t_.is_alive():
            _radio_prctl()
            _GP_W["thread"] = threading.Thread(target=_gp_wache, daemon=True, name="gopro-wache"); _GP_W["thread"].start()


def _gp_wache():
    while True:
        try:
            gopro_tick()
        except Exception as e:                            # noqa: BLE001 - the watch never ends (it owns the receiver)
            if time.time() - RX.get("t_err", 0) > 60:
                RX["t_err"] = time.time(); log_event("sys", f"GoPro watch: {type(e).__name__}: {e}"[:160])
        time.sleep(1.0)


def gopro_tick(now=None):
    now = time.time() if now is None else now
    gopro_sync()
    _rx_manage()
    for gid, dev in list(GOPRO.items()):
        st = gopro_status(gid)
        dev["akku"] = st["akku"]; dev["fehler"] = st["fehler"]
        dev["hinweis"] = _gp_hinweis(dev)
        if not dev["aktiv"]:
            dev["zustand"] = "stopped"; continue
        if st["streamt"]:
            if dev["zustand"] != "streaming":
                log_event("sys", f"GoPro {dev['name']}: picture is coming" + (" again" if dev["zustand"] == "lost" else ""))
            dev["zustand"] = "streaming"; dev["t_stream"] = now
            continue
        if dev["zustand"] == "streaming" and now - dev["t_stream"] < GOPRO_ABBRUCH_S:
            continue                                     # a short gap: not yet a drop-out
        if dev["zustand"] == "streaming":
            dev["zustand"] = "lost"
            log_event("sys", f"GoPro {dev['name']}: the live stream dropped out")
            if now - dev["t_meld"] > GOPRO_MELDUNG_S:
                dev["t_meld"] = now
                gopro_meldung(dev)
            continue
        if dev["zustand"] != "lost":
            dev["zustand"] = "error" if st["fehler"] and st["fehler"] != "waiting for the GoPro stream" else "waiting"


def gopro_meldung(dev):
    """a quiet message (information, no alarm): the live picture of a GoPro dropped out"""
    try:
        w = WATCH_REF.get("w")
        if w is not None and getattr(w, "notifier", None) is not None:
            return bool(w.notifier.info(trf("GoPro {n}: the live picture dropped out. To start it again show the start code (Cameras → GoPro).", n=dev["name"]),
                                        title="{name}: GoPro"))
    except Exception as e:                                # noqa: BLE001
        log_event("sys", f"GoPro message: {type(e).__name__}")
    return False


def _gp_hinweis(dev):
    if dev.get("weg") != "rtmp" or not dev.get("ip"):
        return ""
    now_ips = {n["ip"] for n in gopro_netze() if n.get("ip")}
    if now_ips and dev["ip"] not in now_ips:
        return trf("The address of MoveEye has changed since the address code was shown ({a} → {b}) - show the address code again.",
                   a=dev["ip"], b=", ".join(sorted(now_ips)))
    return ""


# ---- QR codes (GoPro Labs) -------------------------------------------------------------------------------------------------
def gopro_netze():
    """where the GoPro can be: the home network (or phone hotspot) and the own Wi-Fi of the device - with the address of MoveEye"""
    out = []
    try:
        ip = wifi_ip() or local_ip()
    except Exception:
        ip = ""
    if ip and not ip.startswith("127.") and ip != "10.42.0.1":
        out.append({"id": "lan", "titel": "Home network", "ip": ip, "ssid": ""})
    if CFG.get("hotspot_on"):
        out.append({"id": "hotspot", "titel": "Wi-Fi of the device", "ip": "10.42.0.1", "ssid": str(CFG.get("hotspot_ssid") or "")})
    if not out:
        out.append({"id": "lan", "titel": "Home network", "ip": "", "ssid": ""})
    return out


def gopro_rtmp_path(dev):
    return f"gopro/{dev['id']}-{dev['key']}"


def gopro_rtmp_url(dev, ip):
    return f"rtmp://{ip}:{int(CFG.get('gopro_rtmp_port') or 19350)}/{gopro_rtmp_path(dev)}"


def gopro_qr_text(art, dev=None, ssid="", pw="", ip=""):
    """the text of a GoPro Labs code (gopro.github.io/labs/control/rtmp + control/tech); raises ValueError with an English text.
    The Wi-Fi password is only in the return value - never stored, never logged."""
    if art == "join":
        ssid, pw = str(ssid or ""), str(pw or "")
        if not ssid.strip():
            raise ValueError("Wi-Fi name missing")
        if any(c in ssid + pw for c in '"\r\n\x00') or ":" in ssid or len(ssid) > 32 or len(pw) > 63:
            raise ValueError("the Wi-Fi name or password contains a character the GoPro cannot read (\" or line break; «:» in the name)")
        return '!MJOIN="' + ssid + ":" + pw + '"'
    if dev is None:
        raise ValueError("unknown GoPro")
    if art == "rtmp":
        try:
            a = ipaddress.ip_address(str(ip or "").strip())
        except ValueError:
            raise ValueError("invalid address") from None
        if a.is_loopback or a.is_unspecified or a.is_multicast:
            raise ValueError("invalid address")
        host = f"[{a}]" if a.version == 6 else str(a)
        return '!MRTMP="' + gopro_rtmp_url(dev, host) + '"'
    if art == "start":
        pre = "" if dev.get("modell") in ("hero12", "hero13") else "oW1mVr1080!W"
        return pre + "!G" + GOPRO_RES.get(dev.get("res") or "720", "M") + ("C" if dev.get("copy") else "")
    raise ValueError("unknown")


# ---- the receiver (mediamtx, else ffmpeg) -----------------------------------------------------------------------------------
def _rx_dir():
    p = os.path.join(DATA_DIR, "gopro")
    os.makedirs(p, mode=0o700, exist_ok=True)
    return p


def rx_arch():
    m = _gplat.machine().lower()
    return {"aarch64": "arm64", "arm64": "arm64", "armv7l": "armv7", "armv8l": "armv7", "x86_64": "amd64", "amd64": "amd64"}.get(m, "")


def rx_mtx_exe():
    for p in (str(CFG.get("gopro_mtx") or ""), os.path.join(DATA_DIR, "gopro", "bin", "mediamtx"), shutil.which("mediamtx") or "",
              "/usr/local/bin/mediamtx"):
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return ""


def rx_ports():
    p = int(CFG.get("gopro_rtmp_port") or 19350)
    return p, p + 1, p + 2, p + 3            # RTMP (network), RTSP / API / UDP (only 127.0.0.1)


def _rx_paths():
    return sorted(gopro_rtmp_path(d) for d in GOPRO.values() if d.get("weg") == "rtmp" and d.get("aktiv"))


def rx_conf_text(paths):
    """mediamtx configuration (JSON is YAML): RTMP on the own port, publishing only from private networks and only to the paths
    of the GoPros, reading and the API only from this computer; everything else off"""
    rtmp, rtsp, api, _u = rx_ports()
    conf = {
        "logLevel": "warn", "logDestinations": ["stdout"], "readTimeout": "10s", "writeTimeout": "10s",
        "authMethod": "internal",
        "authInternalUsers": [
            {"user": "any", "pass": None, "ips": list(_GP_PRIV), "permissions": [{"action": "publish", "path": p} for p in paths]},
            {"user": "any", "pass": None, "ips": ["127.0.0.1/32", "::1/128"],
             "permissions": [{"action": "read", "path": None}, {"action": "api", "path": None}]}],
        "api": True, "apiAddress": f"127.0.0.1:{api}", "metrics": False, "pprof": False, "playback": False,
        "rtsp": True, "rtspTransports": ["tcp"], "rtspAddress": f"127.0.0.1:{rtsp}",
        "rtmp": True, "rtmpAddress": f":{rtmp}",
        "hls": False, "webrtc": False, "srt": False,
        "paths": {p: {} for p in paths},
    }
    return json.dumps(conf, indent=1)


def _rx_local_url(dev):
    rtmp, rtsp, _api, udp = rx_ports()
    if RX["art"] == "ffmpeg":
        return f"udp://127.0.0.1:{udp}?overrun_nonfatal=1&fifo_size=1000000"
    return f"rtsp://127.0.0.1:{rtsp}/{gopro_rtmp_path(dev)}"


def rx_stop():
    p = RX.get("proc")
    RX.update(proc=None, ff_in=False, ff_dev="", api={})
    if p is not None and p.poll() is None:
        try:
            p.terminate(); p.wait(5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


atexit.register(rx_stop)


def _rx_manage():
    """only in the thread «gopro-wache»: the receiver runs while a GoPro of the way rtmp is on, with exactly its paths"""
    paths = _rx_paths()
    if not paths:
        if RX.get("proc") is not None:
            rx_stop(); log_event("sys", "GoPro receiver stopped (no GoPro on)")
        RX["paths"] = []; return
    exe = rx_mtx_exe()
    art = "mediamtx" if exe and RX["fails"] < 3 else ("ffmpeg" if shutil.which("ffmpeg") else "")
    p = RX.get("proc")
    alive = p is not None and p.poll() is None
    if alive and art == RX["art"] and paths == RX["paths"]:
        if art == "mediamtx":
            _rx_api()
        return
    if p is not None and not alive and time.time() - RX["t_start"] < 4.0 and RX["art"] == "mediamtx":
        RX["fails"] += 1; RX["fehler"] = "the receiver stopped right after the start" + _rx_log_tail()
    if alive:
        rx_stop()
    if p is not None and not alive and time.time() - RX["t_start"] < 1.5:
        return                                           # do not restart faster than every 1.5 s
    if not art:
        RX.update(art="", fehler="no receiver - install mediamtx or ffmpeg"); return
    RX["art"] = art; RX["paths"] = paths
    for d in GOPRO.values():
        d["quelle"] = ""                                  # the local address depends on the receiver
    if art == "mediamtx":
        _rx_start_mtx(exe, paths)
    else:
        _rx_start_ff(paths)


def _rx_log_tail():
    try:
        with open(os.path.join(_rx_dir(), "rx.log"), errors="replace") as f:
            t_ = f.read()[-400:]
        t_ = re.sub(r"gopro/[0-9a-f]{8}-[0-9a-f]{16}", "gopro/…", t_)       # never the stream key
        ln = [x for x in t_.splitlines() if x.strip()]
        return (": " + ln[-1][-160:]) if ln else ""
    except OSError:
        return ""


def _rx_popen(cmd):
    logf = open(os.path.join(_rx_dir(), "rx.log"), "w")
    try:
        os.chmod(logf.name, 0o600)
    except OSError:
        pass
    _radio_prctl()
    return subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT if "ffmpeg" not in os.path.basename(cmd[0]) else subprocess.PIPE,
                            stdin=subprocess.DEVNULL, preexec_fn=_radio_pre, close_fds=True)


def _rx_start_mtx(exe, paths):
    cf = os.path.join(_rx_dir(), "mediamtx.yml")
    fd = os.open(cf, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(rx_conf_text(paths))
    try:
        if not RX["version"]:
            RX["version"] = (subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5).stdout or "").strip()[:20]
        RX["proc"] = _rx_popen([exe, cf]); RX["t_start"] = time.time(); RX["fehler"] = ""
        log_event("sys", f"GoPro receiver started: mediamtx, port {rx_ports()[0]}, {len(paths)} GoPro(s)")
    except OSError as e:
        RX["fails"] += 1; RX["fehler"] = str(e)[:120]


def _rx_start_ff(paths):
    rtmp, _rtsp, _api, udp = rx_ports()
    path = paths[0]
    gid = path.split("/")[1].split("-")[0]
    RX["ff_dev"] = gid; RX["ff_in"] = False
    RX["fehler"] = "the simple receiver takes only one GoPro - install mediamtx" if len(paths) > 1 else ""
    cmd = [shutil.which("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "info", "-listen", "1", "-i", f"rtmp://0.0.0.0:{rtmp}/{path}",
           "-map", "0:v:0", "-c", "copy", "-f", "mpegts", f"udp://127.0.0.1:{udp}?pkt_size=1316"]
    try:
        p = _rx_popen(cmd)
    except OSError as e:
        RX["fehler"] = str(e)[:120]; return
    RX["proc"] = p; RX["t_start"] = time.time()
    threading.Thread(target=_rx_ff_read, args=(p,), daemon=True, name="gopro-ff").start()
    log_event("sys", f"GoPro receiver started: ffmpeg (simple), port {rtmp}")


def _rx_ff_read(p):
    """the simple receiver: «Input #0» = the GoPro is sending; the end of ffmpeg = the stream is over (restarted by the watch)"""
    try:
        for ln in iter(p.stderr.readline, b""):
            if b"Input #0" in ln:
                RX["ff_in"] = True
    except (OSError, ValueError):
        pass
    if RX.get("proc") is p:
        RX["ff_in"] = False


def _rx_api():
    if time.time() - RX["t_api"] < 0.9:
        return
    RX["t_api"] = time.time()
    _r, _s, api, _u = rx_ports()
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(f"http://127.0.0.1:{api}/v3/paths/list", timeout=2) as r:
            items = json.loads(r.read().decode() or "{}").get("items") or []
        RX["api"] = {str(i.get("name")): bool(i.get("online", i.get("ready"))) for i in items if isinstance(i, dict)}
    except Exception:
        RX["api"] = {}


def _rtmp_start(dev):
    gopro_wache_an()
    return _rx_local_url(dev)


def _rtmp_stop(dev):
    dev["quelle"] = ""


def _rtmp_status(dev):
    p = RX.get("proc")
    alive = p is not None and p.poll() is None
    if RX["art"] == "ffmpeg":
        on = alive and RX["ff_dev"] == dev["id"] and RX["ff_in"]
    else:
        on = alive and bool(RX["api"].get(gopro_rtmp_path(dev)))
    f = RX["fehler"] if not alive or RX["fehler"] else ""
    if RX["art"] == "ffmpeg" and RX["ff_dev"] and RX["ff_dev"] != dev["id"]:
        f = "the simple receiver takes only one GoPro - install mediamtx"
    return {"verbunden": on, "akku": None, "streamt": on, "fehler": f or ("" if on else "waiting for the GoPro stream")}


gopro_register_weg("rtmp", start=_rtmp_start, stop=_rtmp_stop, status=_rtmp_status,
                   faehig={"titel": "HERO8 and newer: QR codes + live stream (GoPro Labs)", "modelle": [m for m, _n in GOPRO_MODELLE],
                           "akku": False, "steuern": False})


# ---- install mediamtx (only after the question on the page / in the window) ------------------------------------------------
def rx_install(wait=False):
    I = RX["install"]
    if I["running"]:
        return False, "already running"
    arch = rx_arch()
    if not arch:
        return False, "no package for this computer"
    I.update(running=True, msg="…", done=False, got=0, total=0)
    t_ = threading.Thread(target=_rx_install_run, args=(arch,), daemon=True, name="gopro-install"); t_.start()
    if wait:
        t_.join(600)
    return True, ""


def _rx_install_run(arch):
    I = RX["install"]
    v = MTX["version"]; name = f"mediamtx_{v}_linux_{arch}.tar.gz"
    base = MTX["url"].rstrip("/") + "/" + v + "/"
    d = os.path.join(_rx_dir(), "bin"); os.makedirs(d, exist_ok=True)
    tgz = os.path.join(d, name)
    note = ""
    try:
        pin = MTX["pins"].get(arch)
        if not pin:                                       # not pinned yet: the checksum list of the same release
            with urllib.request.urlopen(_upd_request(base + "checksums.sha256"), timeout=30) as r:
                lst = r.read(65536).decode(errors="replace")
            m = re.search(r"^([0-9a-f]{64})\s+\*?" + re.escape(name) + r"\s*$", lst, re.M)
            if not m:
                raise ValueError("no checksum for " + name)
            pin = {"sha256": m.group(1), "size": MTX["max"]}
            note = " · " + tr("checksum from the release list (not yet fixed in the program)")
        _rx_fetch(base + name, tgz, pin)
        with _gptar.open(tgz, "r:gz") as tf:
            mem = next((m_ for m_ in tf.getmembers() if m_.name in ("mediamtx", "./mediamtx") and m_.isfile()), None)
            if mem is None or mem.size > MTX["max"]:
                raise ValueError("no program mediamtx in the package")
            src = tf.extractfile(mem)
            tmp = os.path.join(d, "mediamtx.part")
            with open(tmp, "wb") as f:
                shutil.copyfileobj(src, f)
            os.chmod(tmp, 0o755); os.replace(tmp, os.path.join(d, "mediamtx"))
        I.update(msg="✓ " + tr("mediamtx installed") + f" ({v}){note}", done=True)
        RX["fails"] = 0; RX["version"] = ""
        log_event("sys", f"GoPro: mediamtx {v} installed ({arch})" + (" - checksum from the release list" if note else ""))
    except Exception as e:                                # noqa: BLE001
        I.update(msg="⚠ " + f"{type(e).__name__}: {e}"[:160])
        log_event("sys", f"GoPro: mediamtx not installed: {type(e).__name__}: {e}"[:160])
    finally:
        try:
            os.remove(tgz)
        except OSError:
            pass
        I["running"] = False


def _rx_fetch(url, dest, pin):
    h = hashlib.sha256(); n = 0
    with urllib.request.urlopen(_upd_request(url), timeout=60) as r, open(dest + ".part", "wb") as f:
        RX["install"]["total"] = int(r.headers.get("Content-Length") or 0)
        while True:
            b = r.read(1 << 16)
            if not b:
                break
            n += len(b)
            if n > (pin.get("size") or MTX["max"]):
                raise ValueError("file too large")
            h.update(b); f.write(b); RX["install"]["got"] = n
    if pin.get("size") and pin["size"] != MTX["max"] and n != pin["size"]:
        os.remove(dest + ".part"); raise ValueError("wrong size")
    if h.hexdigest() != pin["sha256"]:
        os.remove(dest + ".part"); raise ValueError("wrong checksum")
    os.replace(dest + ".part", dest)


# ---- state for the page and the window ------------------------------------------------------------------------------------
def gopro_state(lang=None):
    L = norm_lang(lang)
    gopro_sync()
    rtmp = rx_ports()[0]
    p = RX.get("proc")
    art = RX["art"] or ("mediamtx" if rx_mtx_exe() else ("ffmpeg" if shutil.which("ffmpeg") else ""))
    netze = gopro_netze()
    cams = {c["id"]: c for c in cams_status()} if callable(globals().get("cams_status")) else {}
    devs = []
    for d in GOPRO.values():
        c = cams.get(d["spec"]) or {}
        devs.append({"id": d["id"], "label": source_label(d["spec"]), "name": d["name"], "modell": d["modell"],
                     "modell_name": dict(GOPRO_MODELLE).get(d["modell"], d["modell"]), "weg": d["weg"], "zustand": d["zustand"],
                     "akku": d["akku"], "fehler": tr_err(d["fehler"], L) if d["fehler"] and d["fehler"] != "waiting for the GoPro stream" else "",
                     "hinweis": d.get("hinweis") or "", "aktiv": d["aktiv"], "res": d["res"], "copy": d["copy"], "spec": d["spec"],
                     "ip": d.get("ip") or (netze[0]["ip"] if netze else ""),
                     "start_qr": gopro_qr_text("start", d) if d["weg"] == "rtmp" else "",
                     "cam": (c.get("res") + (" · " + str(c.get("fps")) + " fps" if c.get("fps") else "")) if c.get("status") == "connected" else ""})
    return {"ok": True, "devs": devs, "netze": netze, "modelle": [[k, n] for k, n in GOPRO_MODELLE],
            "wege": [_gp_weg_info(n) for n in GOPRO_WEGE], "wege_titel": {n: _gp_weg_info(n)["titel"] for n in GOPRO_WEGE},
            "zustaende": dict(GOPRO_ZUSTAENDE),
            "rx": {"art": art, "version": RX["version"], "port": rtmp, "laeuft": p is not None and p.poll() is None,
                   "fehler": tr_err(RX["fehler"], L) if RX["fehler"] else "", "mtx_version": MTX["version"], "arch": rx_arch() or "?",
                   "arch_ok": bool(rx_arch()), "install": dict(RX["install"])}}


# ---- web: /gopro and /api/gopro (administrator only) ----------------------------------------------------------------------
_gp_routes_before = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzzzze: the page /gopro, /api/gopro, /api/gopro/qr
    _gp_routes_before(app, reply, body)
    from flask import Response, request, g as g_

    def nope():
        if getattr(g_, "role", "admin") != "admin" or getattr(g_, "appkey", None):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    @app.route("/gopro")
    def gopro_page():
        n = nope()
        if n is not None:
            return n
        return Response(render_page(GOPRO_PAGE, "cams"), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/gopro", methods=["GET", "POST"])
    def gopro_api():
        n = nope()
        if n is not None:
            return n
        gopro_wache_an()
        L = norm_lang(request.args.get("lang"))
        if request.method == "POST":
            d = body() or {}
            L = norm_lang(d.get("lang") or L)
            a = d.get("action"); gid = str(d.get("id") or "")
            if a == "add":
                ok, err, gid = gopro_add(d.get("name"), str(d.get("modell") or "hero8"), str(d.get("weg") or "rtmp"))
            elif a == "remove":
                ok, err = gopro_remove(gid)
            elif a == "start":
                ok, err = gopro_start(gid)
            elif a == "stop":
                ok, err = gopro_stop(gid)
            elif a == "set":
                dev = gopro_dev(gid)
                res = str(d.get("res") or (dev or {}).get("res") or "720")
                ok, err = (False, "unknown GoPro") if not dev else ((False, "invalid value") if res not in GOPRO_RES else (True, ""))
                if ok:
                    _gp_set(gid, res=res, copy=bool(d.get("copy")))
            elif a == "install":
                ok, err = rx_install()
            else:
                ok, err = False, "unknown action"
            if not ok:
                return reply({"ok": False, "error": tr_err(err, L)}, 400)
        return reply(gopro_state(L))

    @app.route("/api/gopro/qr", methods=["POST"])
    def gopro_api_qr():
        n = nope()
        if n is not None:
            return n
        d = body() or {}
        L = norm_lang(d.get("lang"))
        art = str(d.get("art") or "")
        dev = gopro_dev(str(d.get("id") or "")) if art != "join" or d.get("id") else None
        if art != "join" and not dev:
            return reply({"ok": False, "error": tr("unknown GoPro", L)}, 400)
        ip = str(d.get("ip") or "").strip()
        if art == "rtmp" and not ip:
            return reply({"ok": False, "error": tr("no address of MoveEye known - type it in", L)}, 400)
        try:
            txt = gopro_qr_text(art, dev, ssid=d.get("ssid"), pw=d.get("pw"), ip=ip)
            svg = qr_svg(txt)
        except ValueError as e:
            msg = str(e) if str(e) in _HX_GP else "invalid value"       # never the input itself
            return reply({"ok": False, "error": tr(msg, L)}, 400)
        txt = ""; d.pop("pw", None)
        if art == "rtmp" and dev and dev.get("ip") != ip:
            _gp_set(dev["id"], ip=ip)
            if dev["weg"] == "rtmp":
                log_event("sys", f"GoPro {dev['name']}: address code shown ({ip})")
        return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "no-store"})


# ---- the Kameras page: a button to the GoPro page ---------------------------------------------------------------------------
_GP_CAMS_A = '<details style="margin-top:6px"><summary class="mut" style="cursor:pointer" data-i18n="Add network camera">'
if 'href="/gopro"' not in CAMS_PAGE and CAMS_PAGE.count(_GP_CAMS_A) == 1:
    CAMS_PAGE = CAMS_PAGE.replace(_GP_CAMS_A, '<div class="btns" style="margin-top:8px"><button type="button" class="sec" id="gp-link" '
                                  'onclick="location.href=\'/gopro\'" data-href="/gopro">📹 <span data-i18n="Add GoPro">Add GoPro</span></button>'
                                  '<a href="/gopro" hidden>GoPro</a></div>' + _GP_CAMS_A, 1)
    CAMS_PAGE = CAMS_PAGE.replace('Object.assign(I18N.de, {"Add camera": "Kamera hinzufügen",',
                                  'Object.assign(I18N.de, {"Add GoPro": "GoPro hinzufügen", "Add camera": "Kamera hinzufügen",', 1)
_GP_PAGE_KEYS = sorted(set(_HX_GP) | {"Cameras", "Remove"})
GOPRO_PAGE = GOPRO_PAGE.replace("/*GPDE*/{}", json.dumps({k: DE.get(k, k) for k in _GP_PAGE_KEYS}, ensure_ascii=False), 1)


# ---- Pi window: «Add GoPro …» under the video source -----------------------------------------------------------------------
_gp_source_box_570 = App._build_source_box


def _gp_app_source_box(self, parent):
    _gp_source_box_570(self, parent)
    try:
        ttk.Button(parent, text="📹 " + tr("Add GoPro …"), command=lambda: gopro_tk_dialog(self)).pack(fill="x", pady=(8, 0))
    except Exception as e:                                # noqa: BLE001
        print(f"GoPro button: {e}")


# wraps: App._build_source_box
App._build_source_box = _gp_app_source_box


def _gp_tk_qr(parent, text, secret=False):
    """a QR picture in a small window - without the text (the Wi-Fi code holds the password); a Wi-Fi code closes after 2 min"""
    import base64
    w = tk.Toplevel(parent); w.title("MoveEye – GoPro"); w.configure(bg=C["panel"])
    img = tk.PhotoImage(data=base64.b64encode(qr_png(text, 6)).decode())
    lb = tk.Label(w, image=img, bg="#ffffff"); lb.image = img; lb.pack(padx=14, pady=10)
    if secret:
        tk.Label(w, text="🔒 " + tr("The GoPro remembers the Wi-Fi. The password is used only for this code - MoveEye does not save it."),
                 bg=C["panel"], fg=C["mut"], wraplength=360, justify="center").pack(padx=14)
        w.after(120000, w.destroy)
    else:
        tk.Label(w, text=text, bg=C["panel"], fg=C["mut"], wraplength=360, justify="center").pack(padx=14)
    ttk.Button(w, text=tr("Close"), command=w.destroy).pack(pady=(6, 12))
    return w


def gopro_tk_dialog(app):
    """the same steps as /gopro in the Pi window: receiver, GoPros with state, Wi-Fi / address / start code, start / stop"""
    gopro_wache_an()
    top = tk.Toplevel(app.root); top.title("MoveEye – " + tr("Add GoPro")); top.configure(bg=C["panel"])
    ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat", highlightthickness=1, highlightbackground=C["line"],
                  highlightcolor=C["acc"])
    tk.Label(top, text="📹 " + tr("Add GoPro"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
    for k in ("Pair the GoPro once with the GoPro app (Quik) - without that the GoPro does not send a live stream.",
              "Install the GoPro Labs firmware (free, from GoPro): gopro.com/labs - then the GoPro reads QR codes.",
              "GoPro and MoveEye in the same Wi-Fi: home network, phone hotspot or the Wi-Fi of the device."):
        tk.Label(top, text="• " + tr(k), bg=C["panel"], fg=C["mut"], wraplength=440, justify="left").pack(anchor="w", padx=14)
    rxl = tk.Label(top, text="", bg=C["panel"], fg=C["txt"], wraplength=440, justify="left"); rxl.pack(anchor="w", padx=14, pady=(8, 0))
    ib = ttk.Button(top, text="⬇ " + tr("Install mediamtx"))
    ib.pack(anchor="w", padx=14, pady=(2, 0))
    msg = tk.Label(top, text="", bg=C["panel"], fg=C["red"], wraplength=440, justify="left"); msg.pack(anchor="w", padx=14)

    def inst():
        if messagebox.askyesno("MoveEye", tr("Load and install mediamtx now (about 10 MB from github.com)?"), parent=top):
            ok, err = rx_install()
            msg.config(text="" if ok else "⚠ " + tr_err(err))
    ib.config(command=inst)
    devf = tk.Frame(top, bg=C["panel"]); devf.pack(fill="x", padx=14, pady=(8, 0))
    newf = tk.Frame(top, bg=C["panel"]); newf.pack(fill="x", padx=14, pady=(8, 12))
    tk.Label(newf, text=tr("New GoPro"), bg=C["panel"], fg=C["txt"]).pack(anchor="w")
    v_name = tk.StringVar(newf, "")
    tk.Entry(newf, textvariable=v_name, **ent_kw).pack(fill="x", pady=(2, 2))
    cb_m = ttk.Combobox(newf, values=[n for _k, n in GOPRO_MODELLE], state="readonly"); cb_m.current(0); cb_m.pack(fill="x")

    def add():
        k = GOPRO_MODELLE[max(0, cb_m.current())][0]
        ok, err, _gid = gopro_add(v_name.get(), k, "rtmp")
        msg.config(text="" if ok else "⚠ " + tr_err(err))
        if ok:
            v_name.set(""); build()
    ttk.Button(newf, text=tr("Add GoPro"), command=add).pack(fill="x", pady=(4, 0))
    rows = {}

    def build():
        for w_ in list(rows.values()):
            try:
                w_["f"].destroy()
            except Exception:
                pass
        rows.clear()
        st = gopro_state()
        for d in st["devs"]:
            f = tk.Frame(devf, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"]); f.pack(fill="x", pady=(0, 8))
            hl = tk.Label(f, text="📹 " + d["label"], bg=C["panel"], fg=C["txt"]); hl.pack(anchor="w", padx=8, pady=(6, 0))
            sl = tk.Label(f, text="", bg=C["panel"], fg=C["mut"], wraplength=420, justify="left"); sl.pack(anchor="w", padx=8)
            if d["weg"] == "rtmp":
                tk.Label(f, text="1 · " + tr("Wi-Fi for the GoPro"), bg=C["panel"], fg=C["txt"]).pack(anchor="w", padx=8, pady=(6, 0))
                v_s = tk.StringVar(f, next((n["ssid"] for n in st["netze"] if n.get("ssid")), ""))
                v_p = tk.StringVar(f, "")
                tk.Entry(f, textvariable=v_s, **ent_kw).pack(fill="x", padx=8, pady=(2, 2))
                tk.Entry(f, textvariable=v_p, show="•", **ent_kw).pack(fill="x", padx=8)

                def join(d=d, v_s=v_s, v_p=v_p):
                    pw = v_p.get(); v_p.set("")
                    try:
                        _gp_tk_qr(top, gopro_qr_text("join", None, v_s.get(), pw), secret=True)
                    except ValueError as e:
                        msg.config(text="⚠ " + tr(str(e) if str(e) in _HX_GP else "invalid value"))
                    pw = ""
                ttk.Button(f, text="▦ " + tr("Show Wi-Fi code"), command=join).pack(anchor="w", padx=8, pady=(2, 0))
                tk.Label(f, text="2 · " + tr("Where the GoPro sends the picture"), bg=C["panel"], fg=C["txt"]).pack(anchor="w", padx=8, pady=(6, 0))
                v_ip = tk.StringVar(f, d["ip"])
                tk.Entry(f, textvariable=v_ip, **ent_kw).pack(fill="x", padx=8)

                def rtmp(d=d, v_ip=v_ip):
                    try:
                        _gp_tk_qr(top, gopro_qr_text("rtmp", gopro_dev(d["id"]), ip=v_ip.get()))
                        _gp_set(d["id"], ip=v_ip.get().strip())
                    except ValueError as e:
                        msg.config(text="⚠ " + tr(str(e) if str(e) in _HX_GP else "invalid value"))
                ttk.Button(f, text="▦ " + tr("Show address code"), command=rtmp).pack(anchor="w", padx=8, pady=(2, 0))
                tk.Label(f, text="3 · " + tr("Start the live stream"), bg=C["panel"], fg=C["txt"]).pack(anchor="w", padx=8, pady=(6, 0))
                cb_r = ttk.Combobox(f, values=["480p", "720p", "1080p"], state="readonly", width=10)
                cb_r.current(["480", "720", "1080"].index(d["res"])); cb_r.pack(anchor="w", padx=8)
                v_c = tk.BooleanVar(f, bool(d["copy"]))

                def setr(*_a, d=d, cb_r=cb_r, v_c=v_c):
                    _gp_set(d["id"], res=["480", "720", "1080"][max(0, cb_r.current())], copy=bool(v_c.get()))
                cb_r.bind("<<ComboboxSelected>>", setr)
                ttk.Checkbutton(f, variable=v_c, text=tr("Also record on the memory card of the GoPro"), command=setr).pack(anchor="w", padx=8)
                ttk.Button(f, text="▦ " + tr("Start the live stream"),
                           command=lambda d=d: _gp_tk_qr(top, gopro_qr_text("start", gopro_dev(d["id"])))).pack(anchor="w", padx=8, pady=(2, 0))
            bf = tk.Frame(f, bg=C["panel"]); bf.pack(fill="x", padx=8, pady=(6, 8))
            ttk.Button(bf, text="▶ " + tr("Start"), command=lambda d=d: (gopro_start(d["id"]), upd())).pack(side="left", padx=(0, 4))
            ttk.Button(bf, text="■ " + tr("Stop"), command=lambda d=d: (gopro_stop(d["id"]), upd())).pack(side="left", padx=(0, 4))

            def rem(d=d):
                if messagebox.askyesno("MoveEye", tr("Remove this GoPro?"), parent=top):
                    gopro_remove(d["id"]); build()
            ttk.Button(bf, text="✕ " + tr("Remove"), command=rem).pack(side="left")
            rows[d["id"]] = {"f": f, "s": sl}
        upd(st)

    def upd(st=None):
        try:
            st = st if isinstance(st, dict) else gopro_state()
            r = st["rx"]
            rxl.config(text="📡 " + tr("Receiver for the live stream") + ": " + (("mediamtx " + r["version"]) if r["art"] == "mediamtx" else
                       tr("simple receiver (ffmpeg, one GoPro)") if r["art"] == "ffmpeg" else tr("no receiver installed"))
                       + f" · {tr('Port')} {r['port']}" + (" · ⚠ " + r["fehler"] if r["fehler"] else "") + ("\n" + r["install"]["msg"] if r["install"]["msg"] else ""))
            if r["art"] == "mediamtx":
                ib.pack_forget()
            for d in st["devs"]:
                w_ = rows.get(d["id"])
                if w_:
                    w_["s"].config(text=" · ".join(x for x in (tr(GOPRO_ZUSTAENDE.get(d["zustand"], d["zustand"])), d["modell_name"], d["res"] + "p",
                                                               d["fehler"], d["hinweis"]) if x))
            if top.winfo_exists():
                top.after(2000, upd)
        except Exception:                                 # noqa: BLE001 - the window was closed
            pass
    build()
    return top


# ---- manual (HELP_PAGE de / en, HELP_X fr / it / rm): section «Kamera & Servos» --------------------------------------------
HELP_GP = {
    "de": '<p id="gp-help"><b>📹 GoPro als Zusatzkamera (HERO8 und neuer, GoPro Labs):</b> Einmal vorher die GoPro mit der GoPro-App (Quik) '
          'koppeln – sonst sendet sie keinen Live-Strom – und die Firmware <i>GoPro Labs</i> installieren (gratis, gopro.com/labs). Dann unter '
          '<i>Kameras → 📹 GoPro hinzufügen</i> (im Pi-Fenster: Videoquelle → «GoPro hinzufügen …») die GoPro anlegen und ihr drei QR-Codes zeigen: '
          '<b>1. WLAN</b> (Name und Passwort tippst du nur für den Code ein – MoveEye speichert das Passwort nie, der Code erscheint erst nach dem '
          'Antippen und verschwindet nach 2 Minuten), <b>2. Adresse</b> (wohin die GoPro das Bild schickt, die Adresse von MoveEye steht schon da) und '
          '<b>3. Start</b> mit Auflösung 480p / 720p / 1080p (auf Wunsch zusätzlich Aufnahme auf der Speicherkarte der GoPro). Die GoPro merkt sich '
          'WLAN und Adresse; danach genügt der Start-Code (gern ausdrucken). Das Bild kommt als Zusatzkamera: Bewegungserkennung, Aufnahmen, '
          'Live-Bild in der Kamerawahl und «Bild drehen» wie bei jeder Zusatzkamera. Empfänger ist <i>mediamtx</i> (eigener Port 19350, Senden nur '
          'aus dem lokalen Netz; «mediamtx installieren» lädt nach Rückfrage die feste Fassung von GitHub und prüft sie), ohne mediamtx ein einfacher '
          'Empfänger mit ffmpeg für eine GoPro. Bricht der Strom ab, kommt eine stille Meldung (kein Alarm) und die Seite zeigt wieder den Start-Code. '
          'Nur der Administrator richtet GoPros ein. Beenden: an der GoPro den Live-Strom beenden oder sie ausschalten; «Stopp» in MoveEye nimmt sie aus den Kameras.</p>',
    "en": '<p id="gp-help"><b>📹 GoPro as extra camera (HERO8 and newer, GoPro Labs):</b> once before, pair the GoPro with the GoPro app (Quik) – '
          'otherwise it sends no live stream – and install the <i>GoPro Labs</i> firmware (free, gopro.com/labs). Then under <i>Cameras → 📹 Add GoPro</i> '
          '(in the Pi window: video source → «Add GoPro …») add the GoPro and show it three QR codes: <b>1. Wi-Fi</b> (you type name and password only '
          'for the code – MoveEye never saves the password, the code appears only after tapping and disappears after 2 minutes), <b>2. Address</b> '
          '(where the GoPro sends the picture, the address of MoveEye is already filled in) and <b>3. Start</b> with resolution 480p / 720p / 1080p '
          '(optionally also recording on the memory card of the GoPro). The GoPro remembers Wi-Fi and address; afterwards the start code is enough '
          '(print it if you like). The picture comes as an extra camera: motion detection, recordings, live picture in the camera choice and «Turn '
          'picture» like every extra camera. The receiver is <i>mediamtx</i> (own port 19350, sending only from the local network; «Install mediamtx» '
          'loads the fixed version from GitHub after a question and checks it); without mediamtx a simple receiver with ffmpeg for one GoPro. When the '
          'stream drops out a quiet message comes (no alarm) and the page shows the start code again. Only the administrator sets up GoPros. To end: '
          'end the live stream on the GoPro or switch it off; «Stop» in MoveEye takes it out of the cameras.</p>',
    "fr": '<p id="gp-help"><b>📹 GoPro comme caméra supplémentaire (HERO8 et plus récentes, GoPro Labs) :</b> une fois avant, associe la GoPro à l\'app '
          'GoPro (Quik) – sinon elle n\'envoie pas de flux – et installe le firmware <i>GoPro Labs</i> (gratuit, gopro.com/labs). Puis sous <i>Caméras → '
          '📹 Ajouter une GoPro</i> (fenêtre du Pi : source vidéo → « Ajouter une GoPro … ») ajoute la GoPro et montre-lui trois codes QR : <b>1. Wi-Fi</b> '
          '(nom et mot de passe uniquement pour le code – MoveEye n\'enregistre jamais le mot de passe, le code n\'apparaît qu\'après avoir touché et '
          'disparaît après 2 minutes), <b>2. Adresse</b> (où la GoPro envoie l\'image, déjà remplie) et <b>3. Démarrage</b> en 480p / 720p / 1080p. '
          'La GoPro mémorise Wi-Fi et adresse ; ensuite le code de démarrage suffit. L\'image arrive comme caméra supplémentaire (détection de mouvement, '
          'enregistrements, image en direct, « Tourner l\'image »). Récepteur : <i>mediamtx</i> (port 19350, envoi seulement depuis le réseau local), '
          'sinon un récepteur simple avec ffmpeg pour une GoPro. Si le flux s\'interrompt : message discret (pas d\'alarme) et le code de démarrage '
          'réapparaît. Seul l\'administrateur configure les GoPro.</p>',
    "it": '<p id="gp-help"><b>📹 GoPro come telecamera aggiuntiva (HERO8 e successive, GoPro Labs):</b> una volta prima associa la GoPro all\'app '
          'GoPro (Quik) – altrimenti non invia lo streaming – e installa il firmware <i>GoPro Labs</i> (gratuito, gopro.com/labs). Poi in <i>Telecamere → '
          '📹 Aggiungi GoPro</i> (finestra del Pi: sorgente video → «Aggiungi GoPro …») aggiungi la GoPro e mostrale tre codici QR: <b>1. Wi-Fi</b> '
          '(nome e password solo per il codice – MoveEye non salva mai la password, il codice appare solo dopo un tocco e sparisce dopo 2 minuti), '
          '<b>2. Indirizzo</b> (dove la GoPro invia l\'immagine, già compilato) e <b>3. Avvio</b> a 480p / 720p / 1080p. La GoPro memorizza Wi-Fi e '
          'indirizzo; poi basta il codice di avvio. L\'immagine arriva come telecamera aggiuntiva (rilevamento movimento, registrazioni, immagine dal '
          'vivo, «Ruota immagine»). Ricevitore: <i>mediamtx</i> (porta 19350, invio solo dalla rete locale), altrimenti un ricevitore semplice con '
          'ffmpeg per una GoPro. Se lo streaming si interrompe: messaggio discreto (nessun allarme) e il codice di avvio ricompare. Solo '
          'l\'amministratore configura le GoPro.</p>',
    "rm": '<p id="gp-help"><b>📹 GoPro sco camera supplementara (HERO8 e pli novas, GoPro Labs):</b> ina giada avant colliar la GoPro cun l\'app '
          'GoPro (Quik) – uschiglio na trametta ella nagin stream – ed installar il firmware <i>GoPro Labs</i> (gratuit, gopro.com/labs). Lura sut '
          '<i>Cameras → 📹 Agiuntar ina GoPro</i> (fanestra dal Pi: funtauna da video → «Agiuntar ina GoPro …») agiuntar la GoPro e la mussar trais codes '
          'QR: <b>1. WLAN</b> (num e pled-clav mo per il code – MoveEye na memorisescha mai il pled-clav, il code cumpara pir suenter tutgar e '
          'svanescha suenter 2 minutas), <b>2. Adressa</b> (nua che la GoPro trametta il maletg, gia emplenida) e <b>3. Aviament</b> cun 480p / 720p / '
          '1080p. La GoPro memorisescha WLAN ed adressa; suenter tanscha il code d\'aviament. Il maletg arriva sco camera supplementara (identificaziun '
          'da moviment, registraziuns, maletg live, «Volver il maletg»). Retschavider: <i>mediamtx</i> (port 19350, trametter mo da la rait locala), '
          'uschiglio in retschavider simpel cun ffmpeg per ina GoPro. Sch\'il stream vegn interrut: in messadi quiet (nagin alarm) ed il code '
          'd\'aviament cumpara puspè. Mo l\'administratur endrizza GoPros.</p>',
}


def _help_gp(doc, lang):
    i = doc.find('<section id="camera"')
    if i < 0 or 'id="gp-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_GP[lang] + doc[j:] if j >= 0 else doc


_hp_en_gp = HELP_PAGE.find('<div lang="en">')
if _hp_en_gp > 0:
    HELP_PAGE = _help_gp(HELP_PAGE[:_hp_en_gp], "de") + _help_gp(HELP_PAGE[_hp_en_gp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_gp(HELP_X[_L], _L)


# ---- self-test ---------------------------------------------------------------------------------------------------------------
def gopro_selftest():
    keys = ("gopro_devs", "extra_cams", "extra_cams_off", "gopro_rtmp_port", "source", "sim_on")
    sv = {k: CFG.get(k) for k in keys}
    _save = globals()["save_settings"]; _apply = globals()["cams_apply"]; _log = globals()["log_event"]
    logged = []
    try:
        globals()["save_settings"] = lambda *a, **k: None
        globals()["cams_apply"] = lambda *a, **k: None
        globals()["log_event"] = lambda kind, text: logged.append(str(text))
        CFG.update(gopro_devs=[], extra_cams=[], extra_cams_off=[], gopro_rtmp_port=19350, source="demo", sim_on=False)
        assert SRC_RE.match("gopro:0123abcd") and not SRC_RE.match("gopro:XYZ")
        ok, err, gid = gopro_add("Zelt", "hero8", "rtmp")
        assert ok and re.fullmatch(r"[0-9a-f]{8}", gid) and "gopro:" + gid in CFG["extra_cams"], err
        assert source_label("gopro:" + gid) == "GoPro Zelt"
        dev = gopro_dev(gid)
        # the three Labs codes (gopro.github.io/labs/control/rtmp)
        pw = "Geheim-" + secrets.token_hex(4)
        assert gopro_qr_text("join", None, "Camping WLAN", pw) == '!MJOIN="Camping WLAN:' + pw + '"'
        for bad in (("a:b", "x"), ("ok", 'x"y'), ("", "x"), ("ok", "a\nb")):
            try:
                gopro_qr_text("join", None, *bad); raise AssertionError(bad)
            except ValueError:
                pass
        assert gopro_qr_text("rtmp", dev, ip="192.168.1.20") == f'!MRTMP="rtmp://192.168.1.20:19350/gopro/{gid}-{dev["key"]}"'
        try:
            gopro_qr_text("rtmp", dev, ip="127.0.0.1"); raise AssertionError("loopback")
        except ValueError:
            pass
        assert gopro_qr_text("start", dev) == "oW1mVr1080!W!GM"
        _gp_set(gid, res="1080", copy=True)
        assert gopro_qr_text("start", gopro_dev(gid)) == "oW1mVr1080!W!GLC"
        _gp_set(gid, modell="hero13", res="480", copy=False)
        assert gopro_qr_text("start", gopro_dev(gid)) == "!GS"
        assert not any(pw in x for x in logged), "the Wi-Fi password is never logged"
        assert pw not in json.dumps(settings_data()), "the Wi-Fi password is never saved"
        # the receiver: publishing only from private networks, reading / API only here
        c = json.loads(rx_conf_text([gopro_rtmp_path(gopro_dev(gid))]))
        assert c["rtmpAddress"] == ":19350" and c["rtspAddress"] == "127.0.0.1:19351" and c["apiAddress"] == "127.0.0.1:19352"
        assert "100.64.0.0/10" not in c["authInternalUsers"][0]["ips"] and c["authInternalUsers"][1]["ips"] == ["127.0.0.1/32", "::1/128"]
        assert [p["action"] for p in c["authInternalUsers"][1]["permissions"]] == ["read", "api"] and not c["hls"] and not c["webrtc"]
        # a way of G2 / G3: register, the source address, the state machine with a drop-out
        S_ = {"on": False}
        gopro_register_weg("selftest", start=lambda d: "udp://@:8554", stop=lambda d: None,
                           status=lambda d: {"verbunden": S_["on"], "akku": 77, "streamt": S_["on"], "fehler": ""},
                           faehig={"titel": "x", "modelle": ["hero9"]})
        assert not gopro_add("x", "hero8", "selftest")[0], "the way says which models"
        ok, err, g2 = gopro_add("Neun", "hero9", "selftest")
        assert ok, err
        assert gopro_quelle(g2) == "udp://@:8554"
        msgs = []
        _m = globals()["gopro_meldung"]; globals()["gopro_meldung"] = lambda d: msgs.append(d["name"])
        _rxm = globals()["_rx_manage"]; globals()["_rx_manage"] = lambda: None
        try:
            t0 = 1000.0
            gopro_tick(t0); assert GOPRO[g2]["zustand"] == "waiting" and GOPRO[g2]["akku"] == 77
            S_["on"] = True; gopro_tick(t0 + 1); assert GOPRO[g2]["zustand"] == "streaming"
            S_["on"] = False; gopro_tick(t0 + 3); assert GOPRO[g2]["zustand"] == "streaming", "a short gap is no drop-out"
            gopro_tick(t0 + 1 + GOPRO_ABBRUCH_S + 1); assert GOPRO[g2]["zustand"] == "lost" and msgs == ["Neun"]
            S_["on"] = True; gopro_tick(t0 + 20); S_["on"] = False; gopro_tick(t0 + 40)
            assert GOPRO[g2]["zustand"] == "lost" and msgs == ["Neun"], "at most one message in 10 minutes"
            assert gopro_stop(g2)[0] and GOPRO[g2]["zustand"] == "stopped" and "gopro:" + g2 not in CFG["extra_cams"]
        finally:
            globals()["gopro_meldung"] = _m; globals()["_rx_manage"] = _rxm
            GOPRO_WEGE.pop("selftest", None)
        assert gopro_remove(gid)[0] and not gopro_cfg_dev(gid) and "gopro:" + gid not in CFG["extra_cams"]
        assert all(TRX[L].get(k) for L in ("fr", "it", "rm") for k in _HX_GP), "texts fr / it / rm"
        assert HELP_PAGE.count('id="gp-help"') == 2 and all('id="gp-help"' in HELP_X.get(L, 'id="gp-help"') for L in ("fr", "it", "rm"))
        assert 'href="/gopro"' in CAMS_PAGE and '"Add GoPro": "GoPro hinzufügen"' in CAMS_PAGE and "/*GPDE*/" not in GOPRO_PAGE
        assert "/gopro" in ADMIN_GET and "gopro_devs" in USER_SETTINGS_DENY
        return "Labs codes (Wi-Fi, address, start 480/720/1080 + copy), password never saved / logged, receiver only LAN, way interface, drop-out + one message"
    finally:
        globals()["save_settings"] = _save; globals()["cams_apply"] = _apply; globals()["log_event"] = _log
        for k, v in sv.items():
            CFG[k] = v
        gopro_sync()


SELFTEST_EXTRA.append(("GoPro as extra camera (639zzzzzze)", gopro_selftest))
'''
zd_exec(GOPRO_KERN_PY, '639zzzzzze_gopro_kern.py')
