#@ MoveEye – Teil 539: Webseite «Servos» (/servo): Not-Aus / Freigeben, wer den Kopf steuert, Teach-in-Positionen, Diagnose mit Export; dazu Not-Aus und «wer steuert» auf der Live-Seite und der Eintrag unter Mehr → Werkzeuge. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.35 (Wunsch Daniel): one page for the servos, phone first: (1) state + ⏹ Not-Aus / ✅ Freigeben + who steers the head,
#   a small picture and arrows to drive, (2) the taught points (Teach-in: save, go, rename, order, round, park / home,
#   take over from «Platz einrichten»), (3) diagnosis (counters, fault memory, maintenance hints, export JSON / CSV).
#   Reached from Mehr → Werkzeuge («Servos»), from the live page («📍 Positionen») and the settings section.
# aufr (Konzept-Check): the old «Servo test» of the tools page is the tab «Test» here - ONE entry «Servos» under Werkzeuge
#   (positions, test, diagnosis); the test itself stays servo_test() (300), started through /api/tools {"action": "servo"}.
# The live page (530) only gets a small script at its end (like 537): a red «⏹ Stopp» in the camera controls, a red bar
#   while stopped (with who pressed it and «Freigeben»), the line «Kopf: gesteuert von …» and a short notice when another
#   panel (phone, PC, window, controller, simulator) takes the head. Everything from the usual state poll (st.servo).
# API: GET /api/servo (?diag=1, ?trace=<since>), POST /api/servo {"op": …}, GET /api/servo/export?fmt=json|csv.
#   Not-Aus may be pressed by every role (also a guest) - releasing and teaching only by the administrator.
# ----------------------------------------------------------------------------
def servo_client(request, d=None):
    """(key, label) of the panel that sent this request: device + browser + end of the address (+ user) - a label for
    people, the key (a short hash) for «is it me?»"""
    import hashlib
    try:
        from flask import g
        user = str(getattr(g, "user", "") or "")
    except Exception:
        user = ""
    ua = str(request.headers.get("User-Agent") or "")
    ip = str(request.remote_addr or "?")
    if "Godot" in ua or "MoveEye-Sim" in ua:
        dev = tr("Simulator")
    else:
        dev = ("iPhone" if "iPhone" in ua else "iPad" if "iPad" in ua else "Android" if "Android" in ua else "Mac" if "Macintosh" in ua
               else "Windows-PC" if "Windows" in ua else "Linux-PC" if "Linux" in ua else tr("Browser"))
    br = ("Edge" if "Edg/" in ua else "Firefox" if "Firefox/" in ua else "Chrome" if "Chrome/" in ua or "CriOS" in ua
          else "Safari" if "Safari/" in ua else "")
    where = tr("this computer") if ip.startswith("127.") or ip == "::1" else "…" + (ip.split(".")[-1] if "." in ip else ip[-4:])
    label = dev + (" · " + br if br else "") + f" ({where})" + (" · " + user if user else "")
    if isinstance(d, dict) and d.get("via") == "pad":
        label += " 🎮"
    key = hashlib.sha1((ip + "|" + ua).encode("utf-8", "replace")).hexdigest()[:10]
    return key, label[:60]


def servo_client_state(request, lang=None):
    """the small part for the state poll of every page: stopped? who steers? is it me?"""
    key, label = servo_client(request)
    drv = servo_driver(lang)
    return {"blocked": servo_blocked(), "text": servo_blocked_text(lang), "estop": bool(CFG.get("servo_estop")),
            "estop_by": CFG.get("servo_estop_by") or "", "driver": drv, "me": key, "mine": bool(drv.get("key")) and drv.get("key") == key,
            "me_label": label, "moving": bool(SRV["moving"]), "deg": [round(x, 1) for x in servo_pos_deg()]}


SERVO_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Servos</title>
<style>
/*BASECSS*/
main{padding:14px 16px 90px;max-width:980px;margin:0 auto}
.sv-tabs{display:flex;gap:6px;margin:0 0 12px}.sv-tabs a{flex:1;text-align:center;padding:8px 4px;border-radius:10px;border:1px solid var(--line);color:var(--mut);text-decoration:none;font-size:14px}
.sv-tabs a.on{border-color:var(--acc);color:var(--txt);font-weight:700}
.sv-state{border-radius:14px;padding:12px 14px;margin:0 0 10px;border:2px solid var(--line);font-size:16px;font-weight:700}
.sv-state.ok{border-color:#2ea043}.sv-state.stop{border-color:#e5534b;background:rgba(229,83,75,.14)}.sv-state.warn{border-color:#d29922;background:rgba(210,153,34,.12)}
.sv-state small{display:block;font-weight:400;font-size:13px;color:var(--mut);margin-top:4px}
.sv-big{display:flex;gap:8px;margin:8px 0}.sv-big button{flex:1;padding:16px 8px;font-size:18px;border-radius:14px;font-weight:700}
button.sv-stop{background:#d1242f;border-color:#d1242f;color:#fff}button.sv-rel{background:#2ea043;border-color:#2ea043;color:#fff}
#sv-img{width:100%;max-width:520px;aspect-ratio:16/9;object-fit:cover;background:#000;border-radius:12px;display:block;margin:8px auto}
.sv-pad{display:grid;grid-template-columns:repeat(3,64px);gap:6px;justify-content:center;margin:8px 0}.sv-pad button{height:52px;font-size:20px;border-radius:12px}
.sv-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}.sv-row input[type=text]{flex:1;min-width:140px}
.sv-pt{display:grid;grid-template-columns:1fr auto;gap:6px;padding:10px 0;border-top:1px solid var(--line);align-items:center}
.sv-pt b{font-size:15px}.sv-pt .sub{grid-column:1/-1;display:flex;gap:6px;flex-wrap:wrap}.sv-pt .sub button{padding:6px 9px;font-size:13px}
.sv-kv{display:grid;grid-template-columns:auto 1fr 1fr;gap:4px 12px;font-size:14px}.sv-kv b{font-weight:600}
.sv-bar{height:8px;border-radius:6px;background:var(--line);overflow:hidden}.sv-bar i{display:block;height:100%;background:var(--acc)}
.sv-f{padding:7px 0;border-top:1px solid var(--line);font-size:13.5px}.sv-f .lv{display:inline-block;min-width:18px}
.sv-hint{padding:8px 10px;border-radius:10px;margin:6px 0;background:rgba(210,153,34,.12)}.sv-hint.info{background:rgba(56,139,253,.10)}
#sv-drv{font-size:13.5px;margin:4px 0}
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
  <h2 style="margin:0 0 8px">🎯 <span data-i18n="Servos: safety, positions, test, diagnosis">Servos: safety, positions, test, diagnosis</span></h2>
  <div class="sv-tabs"><a href="#teach" id="tb-teach" data-i18n="Positions">Positions</a><a href="#test" id="tb-test" data-i18n="Test">Test</a><a href="#diag" id="tb-diag" data-i18n="Diagnosis">Diagnosis</a></div>
  <div id="sv-state" class="sv-state"></div>
  <div class="sv-big"><button type="button" class="sv-stop" id="sv-estop">⏹ <span data-i18n="Emergency stop">Emergency stop</span></button>
    <button type="button" class="sv-rel" id="sv-release" hidden>✅ <span data-i18n="Release">Release</span></button></div>
  <div id="sv-drv" class="mut"></div>
  <section id="p-teach" class="card">
    <img id="sv-img" alt="">
    <div class="sv-pad"><span></span><button type="button" class="sec" data-d="up">▲</button><span></span>
      <button type="button" class="sec" data-d="left">◀</button><button type="button" class="sec" data-d="center">◎</button><button type="button" class="sec" data-d="right">▶</button>
      <span></span><button type="button" class="sec" data-d="down">▼</button><span></span></div>
    <div class="sv-row"><span class="mut" data-i18n="Step">Step</span><select id="sv-step"><option>0.5</option><option>1</option><option selected>3</option><option>10</option></select>
      <span class="mut" id="sv-pos"></span></div>
    <div class="mut" data-i18n="teach-note">teach-note</div>
    <div class="sv-row"><input type="text" id="sv-name" maxlength="30" data-ph="Name, e.g. «Tent» or «Entrance»"><button type="button" id="sv-add">📍 <span data-i18n="Save position">Save position</span></button></div>
    <div id="sv-list"></div>
    <div class="sv-row"><button type="button" class="sec" id="sv-place">📍 <span data-i18n="Take over from «Set up the place»">Take over from «Set up the place»</span></button></div>
  </section>
  <section id="p-test" class="card" hidden>
    <div class="mut" data-i18n="servo-note">servo-note</div>
    <div class="sv-row"><button type="button" id="sv-test">▶ <span data-i18n="Start the servo test">Start the servo test</span></button><span class="mut" id="sv-tmsg"></span></div>
    <div id="sv-tres"></div>
  </section>
  <section id="p-diag" class="card" hidden>
    <div id="sv-hints"></div>
    <h3 data-i18n="Counters">Counters</h3>
    <div id="sv-cnt"></div>
    <div class="sv-row"><button type="button" class="sec" id="sv-svc">🔧 <span data-i18n="Maintenance done">Maintenance done</span></button>
      <a class="btn sec" href="/api/servo/export?fmt=json" download>⬇ JSON</a><a class="btn sec" href="/api/servo/export?fmt=csv" download>⬇ CSV</a></div>
    <h3 data-i18n="Fault memory">Fault memory</h3>
    <div id="sv-faults"></div>
    <div class="sv-row"><button type="button" class="sec" id="sv-clr">🗑 <span data-i18n="Clear fault memory">Clear fault memory</span></button></div>
  </section>
</main>
<script>
/*COMMON*/
/*SERVODE*/
const SV = {s: null, d: null, timer: 0, img: 0};
const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
const tf = (s, o) => t(s).replace(/\{(\w+)\}/g, (m, k) => (o && o[k] != null) ? o[k] : m);
const tab = () => location.hash === "#diag" ? "diag" : location.hash === "#test" ? "test" : "teach";
const LOC = () => ({de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"}[LANG] || "en-GB");
const when = s => new Date(s * 1000).toLocaleString(LOC(), {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"});
async function op(o) {
  const r = await post("/api/servo", Object.assign({lang: LANG}, o));
  if (!r.ok && r.error) toast("⚠ " + r.error);
  load(); return r;
}
function paintState() {
  const S = SV.s; if (!S) return;
  const b = document.getElementById("sv-state"); b.textContent = "";
  const cls = S.blocked === "estop" || S.blocked === "fault" ? "stop" : S.blocked ? "warn" : "ok";
  b.className = "sv-state " + cls;
  b.appendChild(document.createTextNode(S.blocked ? (S.blocked === "estop" ? "⛔ " + t("EMERGENCY STOP") : "⚠ " + S.text) : "✅ " + t("Ready - the servos may move")));
  if (S.blocked === "estop") b.appendChild(E("small", "", tf("pressed by {who}", {who: S.estop_by || "?"}) + " · " + t("Emergency stop - press «Release» to move again")));
  b.appendChild(E("small", "", tf("Pan {p}° · tilt {t}°", {p: S.deg[0], t: S.deg[1]}) + (S.moving ? " · " + t("moving") : "") + " · " + (S.backend || "")));
  document.getElementById("sv-release").hidden = !(S.blocked === "estop" || S.blocked === "fault");
  document.getElementById("sv-estop").hidden = S.blocked === "estop";
  const d = S.driver || {}, me = S.me || "";
  document.getElementById("sv-drv").textContent = d.kind === "manual" ? "🎮 " + tf("The head is steered by: {who}", {who: d.label}) + (d.key === me ? " (" + t("you") + ")" : "")
    : d.kind === "auto" ? "🤖 " + tf("The head moves by itself: {what}", {what: d.label}) : "";
  document.getElementById("sv-pos").textContent = tf("Pan {p}° · tilt {t}°", {p: S.deg[0], t: S.deg[1]});
}
function paintTeach() {
  const S = SV.s, L = document.getElementById("sv-list"); L.textContent = "";
  if (!S.points.length) L.appendChild(E("div", "mut", t("No positions yet: drive the head with the arrows or the joystick and save.")));
  S.points.forEach((p, k) => {
    const r = E("div", "sv-pt");
    const n = E("div"); n.appendChild(E("b", "", (k + 1) + ". " + (p.name || t("Waypoint") + " " + (k + 1))));
    n.appendChild(E("div", "mut", tf("Pan {p}° · tilt {t}°", {p: p.deg[0], t: p.deg[1]}) + (p.patrol ? " · 🔄 " + t("in the round") : "") + (p.park ? " · 🅿 " + t("parking") : "") + (p.home ? " · 🏠 " + t("home") : "")));
    const go = E("button", "", "▶ " + t("Go")); go.type = "button"; go.onclick = () => op({op: "goto", i: p.i});
    r.append(n, go);
    const sub = E("div", "sub");
    const B = (txt, f, tip) => { const b = E("button", "sec", txt); b.type = "button"; if (tip) b.title = t(tip); b.onclick = f; sub.appendChild(b); };
    B("✏️ " + t("Rename"), () => { const v = prompt(t("New name"), p.name || ""); if (v !== null) op({op: "rename", i: p.i, value: v}); });
    B("⤓ " + t("Here"), () => { if (confirm(t("Store the position of now in this point?"))) op({op: "update", i: p.i}); }, "Store the position of now in this point?");
    B("▲", () => op({op: "up", i: p.i})); B("▼", () => op({op: "down", i: p.i}));
    B((p.patrol ? "🔄 ✓" : "🔄 ✗"), () => op({op: "patrol", i: p.i, value: !p.patrol}), "in the round");
    B("🅿" + (p.park ? " ✓" : ""), () => op({op: "park", i: p.i}), "Parking position");
    B("🏠" + (p.home ? " ✓" : ""), () => op({op: "home", i: p.i}), "Home position");
    B("🗑", () => { if (confirm(t("Delete this position?"))) op({op: "delete", i: p.i}); });
    r.appendChild(sub); L.appendChild(r);
  });
}
function paintDiag() {
  const D = SV.d; if (!D) return;
  const H = document.getElementById("sv-hints"); H.textContent = "";
  if (!D.hints.length) H.appendChild(E("div", "sv-hint info", "✅ " + t("No maintenance hints.")));
  D.hints.forEach(h => H.appendChild(E("div", "sv-hint " + h.level, (h.level === "warn" ? "⚠ " : "ℹ ") + h.text)));
  const C = document.getElementById("sv-cnt"); C.textContent = "";
  [["hw", "Real servos"], ["sim", "Simulation"]].forEach(([k, nm]) => {
    const b = D[k]; C.appendChild(E("h4", "", t(nm) + " · " + tf("{h} h switched on", {h: b.on_h})));
    const g = E("div", "sv-kv"); g.append(E("b", "", ""), E("b", "", t("Pan")), E("b", "", t("Tilt")));
    const row = (lab, f) => { g.append(E("span", "mut", t(lab)), E("span", "", f(b.axes.pan)), E("span", "", f(b.axes.tilt))); };
    row("travelled", a => a.deg + "° (" + a.turns + " " + t("turns") + ")"); row("moving", a => a.move_h + " h"); row("moves", a => String(a.moves));
    if (k === "hw") row("since maintenance", a => a.service_h + " / " + D.service_h + " h");
    C.appendChild(g);
    if (k === "hw") ["pan", "tilt"].forEach(ax => { const br = E("div", "sv-bar"); const i = E("i"); i.style.width = b.axes[ax].service_pct + "%"; br.appendChild(i); br.title = t(ax === "pan" ? "Pan" : "Tilt"); C.appendChild(br); });
    if (b.uv_min) C.appendChild(E("div", "mut", "⚡ " + tf("{n} min with under-voltage", {n: b.uv_min})));
  });
  const F = document.getElementById("sv-faults"); F.textContent = "";
  if (!D.faults.length) F.appendChild(E("div", "mut", t("The fault memory is empty.")));
  D.faults.forEach(f => {
    const r = E("div", "sv-f"); r.appendChild(E("span", "lv", f.level === "error" ? "⛔" : f.level === "warn" ? "⚠" : "ℹ"));
    r.appendChild(document.createTextNode(" " + when(f.last) + " · " + f.what + (f.n > 1 ? " ×" + f.n : "") + (f.sim ? " · " + t("simulation") : "")));
    if (f.text) r.appendChild(E("div", "mut", f.text));
    F.appendChild(r);
  });
}
function paintTest(V) {                         // the servo test (300, before: Mehr → Werkzeuge → «Servo test»)
  const R = document.getElementById("sv-tres"); R.textContent = ""; V = V || {steps: []};
  const b = document.getElementById("sv-test"); b.disabled = !!V.running || !!(SV.s && SV.s.blocked);
  document.getElementById("sv-tmsg").textContent = V.running ? t("running…") : V.msg ? (V.msg === "ok" ? "✅ " + t("ok") : "⚠ " + (V.bad || "") + " " + t(V.msg)) : "";
  if ((V.steps || []).length) {
    const g = E("div", "sv-kv"); g.style.gridTemplateColumns = "auto auto auto auto";
    [t("Axis"), t("To"), t("Picture change"), t("Result")].forEach(x => g.appendChild(E("b", "", x)));
    V.steps.forEach(s => g.append(E("span", "", t(s.axis === "pan" ? "Pan" : "Tilt")), E("span", "", s.to + " %"), E("span", "", s.diff == null ? "–" : String(s.diff)),
      E("span", "", s.ok === false ? "⚠ " + t("no change") : (s.ok ? "✅" : "…"))));
    R.appendChild(g);
  }
}
async function load() {
  clearTimeout(SV.timer);
  const tb = tab();
  try { const r = await fetch("/api/servo?lang=" + LANG + (tb === "diag" ? "&diag=1" : ""), {cache: "no-store"}); if (r.ok) { const j = await r.json(); SV.s = j; if (j.diag) SV.d = j.diag; } } catch (e) {}
  let TV = null;
  if (tb === "test") { try { const r = await fetch("/api/tools", {cache: "no-store"}); if (r.ok) TV = (await r.json()).servo; } catch (e) {} }
  ["teach", "test", "diag"].forEach(k => { document.getElementById("p-" + k).hidden = tb !== k; document.getElementById("tb-" + k).classList.toggle("on", tb === k); });
  if (SV.s) { paintState(); if (tb === "teach") paintTeach(); else if (tb === "diag") paintDiag(); }
  if (tb === "test") paintTest(TV);
  if (tb === "teach" && Date.now() - SV.img > 900) { SV.img = Date.now(); document.getElementById("sv-img").src = "/api/frame.jpg?" + Date.now(); }
  SV.timer = setTimeout(load, tb === "teach" || (TV && TV.running) ? 1000 : 4000);
}
document.querySelectorAll(".sv-pad button").forEach(b => b.onclick = async () => {
  const r = await post("/api/move", {dir: b.dataset.d, step: parseFloat(document.getElementById("sv-step").value) || 3, lang: LANG});
  if (!r.ok && r.error) toast("⚠ " + r.error); setTimeout(load, 400);
});
document.getElementById("sv-estop").onclick = () => op({op: "estop"}).then(() => toast("⛔ " + t("EMERGENCY STOP")));
document.getElementById("sv-release").onclick = () => { if (confirm(t("Release the servos? The head may move again (also by itself)."))) op({op: "release"}); };
document.getElementById("sv-add").onclick = async () => { const n = document.getElementById("sv-name"); const r = await op({op: "add", name: n.value}); if (r.ok) { n.value = ""; toast("📍 " + t("Position saved")); } };
document.getElementById("sv-place").onclick = async () => { const r = await op({op: "from_place"}); if (r.ok) toast(tf("{n} positions taken over", {n: r.n})); };
document.getElementById("sv-svc").onclick = () => { if (confirm(t("Maintenance of both servos done? The maintenance counters start again."))) op({op: "service"}); };
document.getElementById("sv-test").onclick = async () => { const r = await post("/api/tools", {action: "servo", lang: LANG}); if (!r.ok && r.error) toast("⚠ " + r.error); setTimeout(load, 500); };
document.getElementById("sv-clr").onclick = () => { if (confirm(t("Clear the fault memory?"))) op({op: "clear_faults"}); };
addEventListener("hashchange", load);
(async () => { await initAppearance(); const n = document.getElementById("sv-name"); n.placeholder = t(n.dataset.ph); load(); })();
</script></body></html>"""

SERVO_PAGE_KEYS = ["Servos: safety, positions, test, diagnosis", "Positions", "Diagnosis", "Test", "servo-note", "Start the servo test", "running…", "ok",
                   "Axis", "To", "Picture change", "Result", "no change", "steps without a change of the picture - blocked, at the end or camera not on the head?", "Emergency stop", "Release", "Step", "teach-note",
                   "Name, e.g. «Tent» or «Entrance»", "Save position", "Take over from «Set up the place»", "Counters", "Maintenance done",
                   "Fault memory", "Clear fault memory", "EMERGENCY STOP", "Ready - the servos may move", "pressed by {who}",
                   "Emergency stop - press «Release» to move again", "Pan {p}° · tilt {t}°", "moving", "The head is steered by: {who}", "you",
                   "The head moves by itself: {what}", "No positions yet: drive the head with the arrows or the joystick and save.", "Waypoint",
                   "in the round", "parking", "home", "Go", "Rename", "New name", "Here", "Store the position of now in this point?",
                   "Parking position", "Home position", "Delete this position?", "No maintenance hints.", "Real servos", "Simulation",
                   "{h} h switched on", "Pan", "Tilt", "travelled", "turns", "moves", "since maintenance", "{n} min with under-voltage",
                   "The fault memory is empty.", "simulation", "Release the servos? The head may move again (also by itself).",
                   "Position saved", "{n} positions taken over", "Maintenance of both servos done? The maintenance counters start again.",
                   "Clear the fault memory?"]

# ---- the live page (530): Not-Aus, the red bar, who steers - one small script at its end -----------------------------
SERVO_LIVE_JS = r"""<script>
(() => {
  const SD = /*SVLDE*/{};
  const T = s => (LANG === "de" && SD[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && SD[s]) || s;
  const TF = (s, o) => T(s).replace(/\{(\w+)\}/g, (m, k) => (o && o[k] != null) ? o[k] : m);
  const P = (u, b) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b || {})}).then(r => r.json()).catch(() => ({ok: false}));
  const msg = m => { if (typeof toast === "function") toast(m); };
  try { if (typeof I18N !== "undefined" && I18N.de) Object.keys(SD).forEach(k => { if (!I18N.de[k]) I18N.de[k] = SD[k]; }); } catch (e) {}   // the controller view (538) too
  let lastN = null, bar = null, line = null;
  function estop() { P("/api/servo", {op: "estop", lang: LANG}).then(r => { msg("⛔ " + T("EMERGENCY STOP")); if (window.servoPoll) window.servoPoll(); }); }
  function release() { if (confirm(T("Release the servos? The head may move again (also by itself)."))) P("/api/servo", {op: "release", lang: LANG}).then(r => { if (!r.ok && r.error) msg("⚠ " + r.error); }); }
  window.servoEstop = estop;
  function build() {
    const side = document.getElementById("ctl-side");
    if (side && !document.getElementById("srv-stop")) {
      const row = document.createElement("div"); row.className = "sr";
      const b = document.createElement("button"); b.type = "button"; b.id = "srv-stop"; b.textContent = "⏹ " + T("Stop");
      b.title = T("Emergency stop"); b.style.cssText = "background:#d1242f;border-color:#d1242f;color:#fff;font-weight:700"; b.onclick = estop;
      const a = document.createElement("button"); a.type = "button"; a.className = "sec"; a.textContent = "📍 " + T("Positions"); a.onclick = () => { location.href = "/servo#teach"; };
      row.append(b, a); side.insertBefore(row, side.firstChild);
    }
    const sp = document.getElementById("spos-txt");
    if (sp && !document.getElementById("srv-drv")) { line = document.createElement("div"); line.id = "srv-drv"; line.className = "mut"; line.style.fontSize = "12px"; sp.after(line); }
    if (!bar) {
      bar = document.createElement("div"); bar.id = "srv-bar"; bar.hidden = true;
      bar.style.cssText = "position:sticky;top:0;z-index:60;display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 12px;background:#b62324;color:#fff;font-weight:700";
      document.body.insertBefore(bar, document.body.firstChild.nextSibling);
    }
  }
  window.servoPaint = j => {
    const s = (j && j.state && j.state.servo) || null; if (!s) return;
    build();
    if (s.blocked === "estop" || s.blocked === "fault" || s.blocked === "inhibit") {
      bar.textContent = ""; bar.hidden = false;
      const tx = document.createElement("span"); tx.style.flex = "1";
      tx.textContent = s.blocked === "estop" ? "⛔ " + T("EMERGENCY STOP") + " – " + TF("pressed by {who}", {who: s.estop_by || "?"}) : "⚠ " + s.text;
      bar.appendChild(tx);
      if (s.blocked !== "inhibit") { const r = document.createElement("button"); r.type = "button"; r.textContent = "✅ " + T("Release"); r.style.cssText = "background:#fff;color:#b62324;font-weight:700"; r.onclick = release; bar.appendChild(r); }
    } else if (bar) bar.hidden = true;
    const st = document.getElementById("srv-stop"); if (st) { st.disabled = s.blocked === "estop"; st.parentNode.hidden = s.stop_btn === false; }
    const d = s.driver || {};
    if (line) line.textContent = d.kind === "manual" ? "🎮 " + TF("The head is steered by: {who}", {who: d.label}) + (s.mine ? " (" + T("you") + ")" : "")
      : d.kind === "auto" ? "🤖 " + TF("The head moves by itself: {what}", {what: d.label}) : "";
    if (lastN !== null && d.n !== lastN && d.kind === "manual" && !s.mine) msg("🎮 " + TF("Now steered by {who}", {who: d.label}));
    lastN = d.n;
  };
})();
</script>"""
SERVO_LIVE_KEYS = ["EMERGENCY STOP", "Release the servos? The head may move again (also by itself).", "Stop", "Emergency stop", "Positions",
                   "pressed by {who}", "Release", "The head is steered by: {who}", "you", "The head moves by itself: {what}", "Now steered by {who}"]
WEB_PAGE = WEB_PAGE.replace("</body>", "<!--SERVOJS--></body>", 1)          # filled by 634 (after the German texts are known)
NAV_OF["servo"] = "more"
# Mehr → Werkzeuge: the one entry «Servos» (460) opens this page (aufr: before a second entry «Servo diagnosis» beside «Servo test»)


def servo_page():
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in SERVO_PAGE_KEYS}, ensure_ascii=False) + ");"
    return render_page(SERVO_PAGE, "servo").replace("/*SERVODE*/", js, 1)


def servo_live_js():
    return SERVO_LIVE_JS.replace("/*SVLDE*/{}", json.dumps({k: DE.get(k, k) for k in SERVO_LIVE_KEYS}, ensure_ascii=False), 1)


def servo_api_op(d, who, admin, lang=None):
    """POST /api/servo -> (reply dict, http code)"""
    o = str(d.get("op") or "")
    if o == "estop":
        servo_estop(who)
        return {"ok": True}, 200
    if not admin:
        return {"ok": False, "error": tr("not allowed", lang)}, 403
    if o == "release":
        ok, err = servo_release(who)
        return {"ok": ok, "error": tr(err, lang) if err else None}, 200 if ok else 409
    if o == "goto":
        ok, err = teach_goto(d.get("i"), who)
        return {"ok": ok, "error": tr(err, lang) if err else None}, 200 if ok else 409
    if o == "add":
        ok, err, i = teach_add(str(d.get("name") or ""), who[1] if isinstance(who, tuple) else who)
        return {"ok": ok, "i": i, "error": tr(err, lang) if err else None}, 200 if ok else 400
    if o in ("rename", "delete", "up", "down", "patrol", "update", "park", "home"):
        ok, err = teach_edit(o, d.get("i"), d.get("value"), who[1] if isinstance(who, tuple) else who)
        return {"ok": ok, "error": tr(err, lang) if err else None}, 200 if ok else 400
    if o == "from_place":
        return {"ok": True, "n": teach_from_place("web")}, 200
    if o == "service":
        servo_diag_service_done(str(d.get("axis") or "") if d.get("axis") in ("pan", "tilt") else "", "web")
        return {"ok": True}, 200
    if o == "clear_faults":
        servo_diag_clear_faults("web")
        return {"ok": True}, 200
    if o == "test_fault":                                  # tests with the simulator only: pretend a fault
        if not CFG.get("sim_on"):
            return {"ok": False, "error": "only in the simulation"}, 400
        k = str(d.get("kind") or "")
        if k == "uv":
            SRV["test_uv"] = bool(d.get("on", True))
        elif k == "i2c":
            for _ in range(3):
                servo_io_error(OSError("test: I2C write failed"))
        elif k == "pca_reset":
            servo_fault("pca_reset", "test")
        else:
            return {"ok": False, "error": "unknown"}, 400
        return {"ok": True}, 200
    return {"ok": False, "error": "unknown"}, 400


def servo_routes(app, reply, body):
    """the addresses (called once by the web server, 550)"""
    from flask import Response, request, g

    @app.route("/servo")
    def servo_web_page():
        return Response(servo_page(), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/servo", methods=["GET", "POST"])
    def api_servo():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang)
            res, code = servo_api_op(d, servo_client(request, d), getattr(g, "role", "admin") == "admin", lang)
            return reply(res, code)
        out = dict(servo_state(lang), ok=True, points=teach_list(lang), me=servo_client(request)[0], me_label=servo_client(request)[1],
                   sim_head=SIM.get("head") if CFG.get("sim_on") else None)
        if request.args.get("diag") == "1":
            out["diag"] = servo_diag_state(lang)
        if request.args.get("trace") is not None:
            try:
                since = float(request.args.get("trace") or 0)
            except ValueError:
                since = 0.0
            out["trace"] = [x for x in list(SRV["trace"]) if x[0] > since]
        return reply(out)

    @app.route("/api/servo/export")
    def api_servo_export():
        fmt = "csv" if request.args.get("fmt") == "csv" else "json"
        data, mt, fn = servo_diag_export(fmt, norm_lang(request.args.get("lang") or CFG.get("lang")))
        return Response(data, mimetype=mt, headers={"Content-Disposition": f"attachment; filename={fn}", "Cache-Control": "no-store"})
