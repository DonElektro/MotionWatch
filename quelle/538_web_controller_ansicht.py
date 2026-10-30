#@ MoveEye – Teil 538: Web: «Controller-Ansicht» der Live-Seite für Handy und Tablet (Live-Bild + Simulator-Bild, Game-Controller, Gesten). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (29.10.2026): a full-screen view for phones and tablets (web only - the Tk window has its own
# camera control) with a Bluetooth / USB game controller or the fingers:
#   portrait = live picture on top, simulator picture below; landscape = live left, simulator right; swappable (long tap
#   on a picture or Select); without the simulator only the live picture. The simulator picture is naked (view.jpg with
#   bare=1: the simulator hides its buttons, map and boxes for MoveEye - simulator padview.gd).
#   Gestures on the simulator picture: one finger = turn the view, two fingers = zoom (the view events «view_in» of the
#   simulator window, 3D-3.18), double tap = next view (head camera → from above → behind the rover), long tap = swap.
#   Slim bar (the quick switches of 530: Lamp, IR, Thermal, Night vision, Marks, Photo, Record, Follow, then Centre …),
#   at most 8 visible (fewer on a narrow phone), the rest behind «…», hides itself after 4 s, a tap shows it again.
#   Controller (standard mapping of the Gamepad API):
#     left stick = head (pan / tilt, /api/stick like the joystick: real servos and simulator) · L3 = centre
#     right stick = rover (up = forward, sideways = steer) through MoveEye's mover (/api/mover → MOVER: the real mover
#       later, in the simulation the simulator's rover); the simulator view follows behind the rover (explore «hinterher»)
#     without a rover: right stick = fly the simulator view (up = forward, sideways = turn)
#     R1 held + right stick = turn the simulator view · L1 = zoom out, R1 short = zoom in, L2 = zoom out too
#     (2.98.35: with the simulator R2 = the shutter «Auslöser», part 539; aufr: the help no longer says «L2 / R2 zoom»)
#     R3 = next view (behind the rover → driver → from above; without rover: head camera → from above → free)
#     A Photo · B Record · X Lamp (IR without lamp) · Y Follow · D-pad ← → choose a button of the bar, ↑ press it, ↓ help
#     Select = swap the pictures · Start = bar on / off, held 1 s = leave
#   While it is open the raw controller is not sent to the simulator (470 simPadLink: mwPadOwn), the small simulator
#   window of the live page pauses (530) - one picture, one mapping. Stored per device (localStorage «mw-pad», not on
#   the Pi): open, swapped, asked. Translations: part 628.
# ----------------------------------------------------------------------------

PADVIEW_JS = r"""
<style id="pv-css">
#pv{position:fixed;inset:0;z-index:190;background:#000;display:flex;flex-direction:column;touch-action:none;user-select:none;-webkit-user-select:none;
  overscroll-behavior:none;-webkit-touch-callout:none;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)}
#pv[hidden]{display:none}
#pv.land{flex-direction:row}
#pv .pv-p{flex:1 1 0;min-width:0;min-height:0;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#000}
#pv.swap #pv-live{order:2}
#pv:not(.land) .pv-p+.pv-p{border-top:2px solid #1a1f27}#pv.land .pv-p+.pv-p{border-left:2px solid #1a1f27}
#pv.swap:not(.land) #pv-sim{border-top:0;border-bottom:2px solid #1a1f27}#pv.swap.land #pv-sim{border-left:0;border-right:2px solid #1a1f27}
#pv.nosim #pv-sim{display:none}
#pv #pv-live img,#pv #pv-sim img{width:100%;height:100%;max-height:none!important;min-height:0;aspect-ratio:auto;object-fit:contain;display:block;-webkit-user-drag:none;touch-action:none;visibility:visible}
#pv .pv-tag{position:absolute;left:8px;top:8px;font:700 10px/1 system-ui,sans-serif;letter-spacing:.08em;color:#fff;background:rgba(220,40,40,.75);padding:3px 6px;border-radius:5px;pointer-events:none}
#pv #pv-simwait{position:absolute;color:#8a96a6;font-size:13px;pointer-events:none}
#pv-x{position:absolute;z-index:3;top:max(8px,env(safe-area-inset-top,0px));right:max(8px,env(safe-area-inset-right,0px));width:44px;height:44px;border-radius:12px;
  border:1px solid rgba(255,255,255,.3);background:rgba(8,12,20,.6);color:#fff;font-size:20px;padding:0;transition:opacity .3s}
#pv-pad{position:absolute;z-index:3;top:max(10px,env(safe-area-inset-top,0px));left:50%;transform:translateX(-50%);font-size:12px;color:#fff;background:rgba(8,12,20,.55);
  padding:4px 10px;border-radius:10px;pointer-events:none;transition:opacity .3s;white-space:nowrap}
#pv.calm #pv-x,#pv.calm #pv-pad{opacity:0;pointer-events:none}
#pv-bar{position:absolute;z-index:3;left:50%;bottom:max(10px,env(safe-area-inset-bottom,0px));transform:translateX(-50%);display:flex;gap:6px;padding:6px;border-radius:16px;
  background:rgba(8,12,20,.74);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.12);transition:opacity .3s,transform .3s;max-width:calc(100% - 16px)}
#pv.calm #pv-bar{opacity:0;pointer-events:none;transform:translate(-50%,24px)}
#pv button.pvb{width:54px;height:54px;flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;font-size:21px;line-height:1;border-radius:12px;
  border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.07);color:#fff;padding:0;position:relative;cursor:pointer;touch-action:manipulation}
#pv button.pvb small{font-size:9.5px;line-height:1.1;opacity:.85;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:52px}
#pv button.pvb.on{background:var(--acc,#3b8cff);border-color:transparent}
#pv button.pvb.rec{background:#d93636;border-color:transparent}
#pv button.pvb.foc{outline:3px solid #ffd34d;outline-offset:1px}
#pv button.pvb.flash{background:#fff;color:#000}
#pv button.pvb i{position:absolute;top:-6px;right:-6px;width:18px;height:18px;border-radius:50%;font:700 10px/18px system-ui,sans-serif;font-style:normal;color:#fff;background:#4b5563;border:1px solid rgba(255,255,255,.5)}
#pv button.pvb i.kA{background:#2f9e44}#pv button.pvb i.kB{background:#d9480f}#pv button.pvb i.kX{background:#1c7ed6}#pv button.pvb i.kY{background:#e0a800}
#pv-more{position:absolute;z-index:4;left:50%;transform:translateX(-50%);bottom:calc(max(10px,env(safe-area-inset-bottom,0px)) + 76px);display:grid;grid-template-columns:repeat(auto-fill,54px);
  gap:8px;justify-content:center;width:min(calc(100% - 24px),400px);padding:10px;border-radius:16px;background:rgba(8,12,20,.88);border:1px solid rgba(255,255,255,.14)}
#pv-more[hidden],#pv-help[hidden],#pv-ask[hidden]{display:none}
#pv-help{position:absolute;z-index:5;left:50%;top:50%;transform:translate(-50%,-50%);width:min(calc(100% - 24px),460px);max-height:calc(100% - 24px);overflow-y:auto;
  background:rgba(8,12,20,.92);color:#e8eef5;border:1px solid rgba(255,255,255,.18);border-radius:14px;padding:12px 14px;font-size:13px;line-height:1.45}
#pv-help b{display:block;margin:2px 0 6px;font-size:14px}#pv-help table{border-collapse:collapse;width:100%}
#pv-help td{padding:3px 4px;vertical-align:top;border-top:1px solid rgba(255,255,255,.08)}#pv-help td:first-child{white-space:nowrap;color:#ffd34d;padding-right:10px}
#pv-help .mut{color:#8a96a6;margin-top:8px}
#pv-ask{position:fixed;z-index:260;left:12px;right:12px;top:max(12px,env(safe-area-inset-top,0px));max-width:520px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  background:var(--panel,#121821);color:var(--txt,#e8eef5);border:1px solid var(--acc,#3b8cff);border-radius:14px;padding:12px;box-shadow:0 8px 30px rgba(0,0,0,.45)}
#pv-ask>span{flex:1 1 100%;font-size:14px}#pv-ask button{flex:1 1 auto;padding:10px 12px;min-height:44px}
body.pv-on{overflow:hidden}
body.pv-on #gd-card{display:none!important}   /* the tips of the guide (515) not over the controller view */
body.pv-on main,body.pv-on header,body.pv-on #lv-menu{visibility:hidden}
#lv-b-pad{font-size:17px}
body.pv-on #toast{z-index:205;bottom:calc(max(10px,env(safe-area-inset-bottom,0px)) + 80px)}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*PVDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const KEY = "mw-pad";                                  // per device (this phone / tablet) - never copied to the Pi
  const P = {open: false, swap: false, ask: true, help: false};
  try { Object.assign(P, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(P)); } catch (e) {} };
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const ST = () => J().state || {};
  const simOn = () => { const s = ST().sim; return !!(s && s.on && s.ok && s.view); };
  const rover = () => { const m = ST().mover; return !!(m && m.avail && (m.hw || !m.test)); };   // a real mover, or the simulator has its rover
  const touchDev = () => (navigator.maxTouchPoints || 0) > 0 || (window.matchMedia && matchMedia("(pointer: coarse)").matches);
  const handy = () => touchDev() || Math.min(innerWidth, innerHeight) <= 900;   // phone / tablet / small window
  const r3 = v => Math.round(v * 1000) / 1000;
  const toastT = m => { if (typeof toast === "function") toast(m); };
  const PV = {open: false, view: "", followed: false};
  // ---- the page ----
  const W = E("div"); W.id = "pv"; W.hidden = true;
  const PL = E("div", "pv-p"); PL.id = "pv-live"; const slot = E("div", "pv-p"); slot.style.cssText = "position:absolute;inset:0"; PL.appendChild(slot);
  PL.appendChild(E("span", "pv-tag", "LIVE"));
  const PS = E("div", "pv-p"); PS.id = "pv-sim"; PS.dataset.bare = "1";             // naked: only the picture of the simulator
  const SI = E("img"); SI.alt = ""; SI.draggable = false; PS.appendChild(SI);
  const SW = E("div"); SW.id = "pv-simwait"; SW.textContent = "…"; PS.appendChild(SW);
  SI.addEventListener("load", () => { SW.hidden = true; });
  const X = E("button", "", "✕"); X.id = "pv-x"; X.type = "button";
  const PADI = E("div"); PADI.id = "pv-pad"; PADI.hidden = true;
  const BAR = E("div"); BAR.id = "pv-bar";
  const MORE = E("div"); MORE.id = "pv-more"; MORE.hidden = true;
  const HELP = E("div"); HELP.id = "pv-help"; HELP.hidden = true;
  W.append(PL, PS, X, PADI, BAR, MORE, HELP); document.body.appendChild(W);
  X.onclick = e => { e.stopPropagation(); open(false); };
  // ---- the bar: the quick switches of the live page (530 QS), in this order; not available (no lamp …) = not shown ----
  const QD = id => (typeof QS !== "undefined" && Array.isArray(QS) ? QS.find(q => q.id === id) : null);
  const EXTRA = {
    center: {ic: "◎", lb: "Centre", tip: "Head to the middle", on: () => false, go: () => post("/api/move", {dir: "center"})},
    rover: {ic: "🚜", lb: "Rover", tip: "The rover in the simulator on / off", on: () => rover(), ok: () => simOn() && !(ST().mover || {}).hw,
            go: () => post("/api/sim", {action: "ctl", ctl: "set", id: "mover_on", value: !rover(), lang: LANG})},
    swap: {ic: "⇅", lb: "Swap", tip: "Swap the pictures (long tap on a picture, Select)", on: () => !!P.swap, ok: () => simOn(), go: () => { swap(); return Promise.resolve({ok: true}); }, util: true},
    help: {ic: "?", lb: "Help", tip: "Controller and gestures", on: () => !HELP.hidden, go: () => { help(HELP.hidden); return Promise.resolve({ok: true}); }, util: true},
    exit: {ic: "✕", lb: "Exit", tip: "Leave the controller view", on: () => false, go: () => { open(false); return Promise.resolve({ok: true}); }, util: true}};
  const ORDER = ["white", "ir", "therm", "nv", "marks", "photo", "rec", "track", "center", "patrol", "listen", "mask", "rover", "swap", "help", "exit"];
  const KEYS = () => ({photo: "A", rec: "B", [okId("white") ? "white" : "ir"]: "X", track: "Y"});
  const item = id => EXTRA[id] || QD(id);
  function okId(id) { const q = item(id); if (!q) return false; const c = J().cfg || {}, s = ST(); try { return q.ok ? !!q.ok(c, s) : true; } catch (e) { return false; } }
  function act(id, btn) {
    const q = item(id); if (!q || !okId(id)) return;
    const c = J().cfg || {}, s = ST();
    if (btn) btn.disabled = true;
    Promise.resolve(q.go(c, s)).then(r => {
      if (btn) btn.disabled = false;
      if (r && r.ok === false) toastT("⚠ " + (r.error || "error"));
      else if (q.flash) { if (btn) { btn.classList.add("flash"); setTimeout(() => btn.classList.remove("flash"), 400); } toastT("📷 " + T("Photo saved")); }
      if (typeof refresh === "function") refresh();
      setTimeout(paintBar, 300);
    });
  }
  let BSIG = "", focus = -1;
  const mkBtn = id => { const q = item(id), b = E("button", "pvb"); b.type = "button"; b.dataset.id = id;
    b.append(E("span", "", q.ic), E("small", "", q.raw ? q.lb : T(q.lb))); b.title = T(q.tip || q.lb);
    b.onclick = e => { e.stopPropagation(); wake(); if (id === "more") return; act(id, b); }; return b; };
  function fitN() { const w = W.clientWidth || innerWidth; return Math.max(3, Math.min(8, Math.floor((w - 28) / 60) - 1)); }
  function paintBar() {
    if (!PV.open) return;
    const avail = ORDER.filter(id => item(id) && okId(id)), main_ = avail.filter(id => !(EXTRA[id] && EXTRA[id].util));
    const n = fitN(), vis = main_.slice(0, n), rest = main_.slice(n).concat(avail.filter(id => EXTRA[id] && EXTRA[id].util));
    const sig = vis.join() + "|" + rest.join() + "|" + LANG + JSON.stringify(KEYS());
    if (sig !== BSIG) {
      BSIG = sig; BAR.textContent = ""; MORE.textContent = "";
      vis.forEach(id => BAR.appendChild(mkBtn(id)));
      const m = E("button", "pvb"); m.type = "button"; m.dataset.id = "more"; m.append(E("span", "", "…"), E("small", "", T("more"))); m.title = T("More buttons");
      m.onclick = e => { e.stopPropagation(); MORE.hidden = !MORE.hidden; wake(); paintBar(); }; BAR.appendChild(m);
      rest.forEach(id => MORE.appendChild(mkBtn(id)));
      const K = KEYS(); W.querySelectorAll("button.pvb").forEach(b => { const k = K[b.dataset.id]; if (k) { const i = E("i", "k" + k, k); b.appendChild(i); } });
    }
    const c = J().cfg || {}, s = ST();
    W.querySelectorAll("button.pvb").forEach(b => { const id = b.dataset.id; if (id === "more") { b.classList.toggle("on", !MORE.hidden); return; }
      const q = item(id); if (!q) return; let on = false; try { on = !!q.on(c, s); } catch (e) {}
      b.classList.toggle(q.cls || "on", on);
      if (q.lbf) { const sm = b.querySelector("small"), tx = T(q.lbf(c, s)); if (sm.textContent !== tx) sm.textContent = tx; }
      if (q.icf) { const sp = b.querySelector("span"), ic = q.icf(c, s); if (sp.textContent !== ic) sp.textContent = ic; } });
    const L = [...BAR.children]; L.forEach((b, i) => b.classList.toggle("foc", i === focus));
  }
  // ---- the bar hides itself after 4 s without touch; a tap shows it again ----
  let calmT = null;
  function wake() { W.classList.remove("calm"); clearTimeout(calmT); calmT = setTimeout(() => { if (MORE.hidden && HELP.hidden) { W.classList.add("calm"); focus = -1; paintBar(); } else wake(); }, 4000); }
  function barToggle() { if (W.classList.contains("calm")) wake(); else { MORE.hidden = true; W.classList.add("calm"); clearTimeout(calmT); } }
  W.addEventListener("pointerdown", e => { if (BAR.contains(e.target) || MORE.contains(e.target) || e.target === X) wake(); }, true);
  // ---- help: what the controller and the fingers do ----
  function help(on) {
    HELP.hidden = !on; if (!on) { paintBar(); return; }
    HELP.textContent = ""; HELP.appendChild(E("b", "", "🎮 " + T("Controller view")));
    const tb = E("table");
    [["L ◉", "Left stick: turn / tilt the head of MoveEye"], ["L3", "Press the left stick: head to the middle"],
     ["R ◉", rover() ? "Right stick: drive the rover (up = forward, sideways = steer) - the view follows behind it" : "Right stick: move the simulator view (no rover)"],
     ["R1 + R ◉", "Hold R1 + right stick: turn the simulator view"], ["L1 / R1", "Zoom out / in (L2 = zoom out too)"],
     ["R2 🎯", "Shutter: a shot at the middle of the picture (with the simulator; in «Team gegen MoveEye» a catch)"],
     ["R3", "Press the right stick: next view (behind the rover, driver, from above)"],
     ["A B X Y", "A Photo · B Record · X Lamp · Y Follow"], ["✚ ← →", "Choose a button of the bar, ↑ presses it, ↓ this help"],
     ["Select", "Swap the pictures"], ["Start", "Bar on / off · hold 1 s = leave"],
     ["☝", "Simulator picture: one finger = turn, two fingers = zoom, double tap = next view, long tap = swap the pictures"]]
      .forEach(([k, v]) => { const tr = E("tr"); tr.append(E("td", "", k), E("td", "", T(v))); tb.appendChild(tr); });
    HELP.appendChild(tb); HELP.appendChild(E("div", "mut", T("Tap here to close. Stored on this device only.")));
    wake();
  }
  HELP.addEventListener("click", e => { e.stopPropagation(); help(false); });
  // ---- layout: portrait = on top of each other, landscape = side by side; swapped; without simulator only the live picture ----
  function layout() {
    if (!PV.open) return;
    W.classList.toggle("land", innerWidth > innerHeight);
    W.classList.toggle("swap", !!P.swap);
    W.classList.toggle("nosim", !simOn());
  }
  function swap() { if (!simOn()) return; P.swap = !P.swap; save(); layout(); paintBar(); toastT("⇅ " + T("Pictures swapped")); }
  addEventListener("resize", () => { layout(); paintBar(); });
  // ---- the simulator picture: the picture poll of the simulator window (470 simViewPoll), naked (bare=1) ----
  let VP = null, vOn = false;
  function simTick() {
    const want = PV.open && simOn() && !document.hidden;
    if (want && !VP && typeof simViewPoll === "function") VP = simViewPoll(SI, 8);
    if (want && !vOn && VP) { vOn = true; SW.hidden = false; VP.start(); }
    else if (!want && vOn && VP) { vOn = false; VP.stop(); }
    if (want && rover() && !PV.followed) { PV.followed = true; sim({view: "follow"}); }   // the view goes behind the rover
    if (!rover()) PV.followed = false;
  }
  function sim(d) { if (!simOn()) return Promise.resolve({ok: false});
    return post("/api/sim", Object.assign({action: "padview", lang: LANG}, d)).then(r => { if (r && r.ok && r.view != null) PV.view = r.view; return r; }); }
  // ---- view events into the simulator window (the protocol of simViewBind, 470: view_in) ----
  const VB = typeof simViewBind === "function" ? simViewBind(E("img"), {active: () => false}) : null;   // only its sender (queue of 70 ms)
  const vpush = (e, now) => { if (VB) VB.push(e, now); else post("/api/sim", {action: "view_in", ev: [e], lang: LANG}); };
  function posIn(img, cx, cy) {                           // x / y 0 … 1 in the shown picture (object-fit: contain = black edges)
    const r = img.getBoundingClientRect(), nw = img.naturalWidth || 16, nh = img.naturalHeight || 9, k = Math.min(r.width / nw, r.height / nh);
    const w = nw * k, h = nh * k;
    return {x: Math.max(0, Math.min(1, (cx - r.left - (r.width - w) / 2) / w)), y: Math.max(0, Math.min(1, (cy - r.top - (r.height - h) / 2) / h))};
  }
  // gestures: one finger turns (right mouse button drag), two fingers zoom (wheel), double tap = next view, long tap = swap
  function gestures(el, img, isSim) {
    const pts = new Map(); let g = null, pinch = 0, lastTap = 0, longT = null;
    const cancelLong = () => { clearTimeout(longT); longT = null; };
    el.addEventListener("contextmenu", e => e.preventDefault());
    el.addEventListener("dblclick", e => { e.preventDefault(); e.stopPropagation(); }, true);   // not the full screen of the live picture
    el.addEventListener("pointerdown", e => {
      if (e.target.closest && e.target.closest("button")) return;
      e.preventDefault(); try { el.setPointerCapture(e.pointerId); } catch (x) {}
      pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
      if (pts.size === 1) {
        g = {id: e.pointerId, x: e.clientX, y: e.clientY, t: Date.now(), drag: false, mouse: e.pointerType === "mouse"};
        cancelLong(); longT = setTimeout(() => { longT = null; if (g && !g.drag && pts.size === 1) { g.long = true; swap(); } }, 650);
      } else if (pts.size === 2) {
        cancelLong();
        if (g && g.drag && isSim) { const p = posIn(img, g.lx, g.ly); vpush(Object.assign({t: "up", b: 2}, p), true); }
        if (g) { g.drag = false; g.pinch = true; }
        const [a, b] = [...pts.values()]; pinch = Math.hypot(a.x - b.x, a.y - b.y);
      }
    });
    el.addEventListener("pointermove", e => {
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
      if (pts.size === 2 && pinch && isSim) {
        const [a, b] = [...pts.values()], d = Math.hypot(a.x - b.x, a.y - b.y);
        if (Math.abs(d - pinch) > 36) { vpush(Object.assign({t: "wheel", d: d > pinch ? 1 : -1}, posIn(img, (a.x + b.x) / 2, (a.y + b.y) / 2)), true); pinch = d; }
        return;
      }
      if (!g || g.id !== e.pointerId || g.pinch) return;
      if (!g.drag && Math.hypot(e.clientX - g.x, e.clientY - g.y) > 10) {
        cancelLong(); g.drag = true;
        if (isSim) { const p = posIn(img, g.x, g.y); vpush(Object.assign({t: "move"}, p)); vpush(Object.assign({t: "down", b: 2}, p), true); }
      }
      if (g.drag && isSim) { g.lx = e.clientX; g.ly = e.clientY; vpush(Object.assign({t: "move"}, posIn(img, e.clientX, e.clientY))); }
    });
    const up = e => {
      if (!pts.delete(e.pointerId)) return;
      if (pts.size < 2) pinch = 0;
      if (!g || g.id !== e.pointerId) { if (!pts.size) g = null; return; }
      cancelLong();
      if (g.drag && isSim) vpush(Object.assign({t: "up", b: 2}, posIn(img, e.clientX, e.clientY)), true);
      else if (!g.drag && !g.pinch && !g.long && e.type === "pointerup" && Date.now() - g.t < 400) {
        const now = Date.now();
        if (isSim && now - lastTap < 320) { lastTap = 0; sim({view: "next"}).then(r => { if (r && r.ok) toastT("👁 " + T(VIEWNAME[r.view] || "Free view")); }); }
        else { lastTap = now; wake(); }
      }
      g = null;
    };
    el.addEventListener("pointerup", up); el.addEventListener("pointercancel", up);
    if (isSim) el.addEventListener("wheel", e => { e.preventDefault(); vpush(Object.assign({t: "wheel", d: e.deltaY < 0 ? 1 : -1}, posIn(img, e.clientX, e.clientY)), true); }, {passive: false});
  }
  const VIEWNAME = {follow: "Behind the rover", driver: "Driver's view", top: "From above", head: "Head camera", free: "Free view"};
  gestures(PS, SI, true);
  gestures(PL, slot, false);
  // ---- the game controller (Gamepad API, standard mapping) ----
  const GP = {mute: false, prev: [], lastHead: 0, headZero: true, lastR: 0, rZero: true, r1T: 0, r1Used: false, startT: 0, startLong: false, l1T: 0, zT: 0, name: ""};
  function pad() { try { return [...(navigator.getGamepads ? navigator.getGamepads() : [])].find(g => g && g.connected) || null; } catch (e) { return null; } }
  const dz = (x, y) => { const m = Math.hypot(x, y); if (m < 0.18) return [0, 0]; const k = Math.min(1, (m - 0.18) / 0.78) / m; return [x * k, y * k]; };
  const spd = () => { const s = document.getElementById("stick-speed"); return s ? parseFloat(s.value) || 30 : 30; };
  const zoom = d => sim({zoom: d});
  function focusMove(d) { const n = BAR.children.length; if (!n) return; wake(); focus = focus < 0 ? (d > 0 ? 0 : n - 1) : (focus + d + n) % n; paintBar(); }
  function focusPress() { const b = BAR.children[focus]; if (b) b.click(); }
  function gpTick() {
    const g = pad();
    if (GP.mute && !(g && [...g.buttons].some(b => b && b.pressed))) GP.mute = false;   // left with Start held: let go first
    if (!PV.open || !g || document.hidden) return;
    const cur = [...g.buttons].map(b => !!(b && (b.pressed || b.value > 0.5))), prev = GP.prev; GP.prev = cur;
    const down = i => cur[i] && !prev[i], up = i => !cur[i] && prev[i], val = i => (g.buttons[i] ? g.buttons[i].value || (g.buttons[i].pressed ? 1 : 0) : 0);
    const now = Date.now();
    const [lx, ly] = dz(g.axes[0] || 0, g.axes[1] || 0), [rx, ry] = dz(g.axes[2] || 0, g.axes[3] || 0);
    // left stick = head (the same as the joystick of the live page: /api/stick, real servos and the simulator)
    if (lx || ly) { if (now - GP.lastHead >= 100) { GP.lastHead = now; GP.headZero = false; post("/api/stick", {x: r3(lx), y: r3(-ly), speed: spd(), via: "pad"}); } }
    else if (!GP.headZero) { GP.headZero = true; post("/api/stick", {x: 0, y: 0, speed: spd()}); }
    // right stick = rover (MoveEye's mover: real mover or the simulator's rover) · R1 held = turn the view · no rover = fly the view
    if (down(5)) { GP.r1T = now; GP.r1Used = false; }
    if (rx || ry) {
      if (now - GP.lastR >= 100) { GP.lastR = now;
        if (cur[5] && simOn()) { GP.r1Used = true; sim({look: [r3(rx), r3(ry)], dt: 0.1}); if (!GP.rZero) { GP.rZero = true; post("/api/mover", {v: 0, w: 0}); } }
        else if (rover()) { GP.rZero = false; post("/api/mover", {v: r3(-ry), w: r3(rx)}); }
        else if (simOn()) sim({fly: [r3(-ry), r3(rx)], dt: 0.1}); }
    } else if (!GP.rZero) { GP.rZero = true; post("/api/mover", {v: 0, w: 0}); }
    if (up(5) && !GP.r1Used && now - GP.r1T < 400) zoom(1);              // R1 short = zoom in
    if (down(4)) { GP.l1T = now; zoom(-1); }                              // L1 = zoom out (held: again and again)
    else if (cur[4] && now - GP.l1T > 450 && now - GP.zT > 300) { GP.zT = now; zoom(-1); }
    const l2 = val(6), r2 = val(7);                                       // L2 / R2: zoom out / in while pressed
    const shut = !!(window.mwShutCan && window.mwShutCan());              // 2.98.35: with the simulator R2 = the shutter («Auslöser», 539)
    if (shut && r2 > 0.5 && !GP.r2) window.mwShutFire();
    GP.r2 = r2 > 0.5;
    const kih = !!(window.mwKiOn && window.mwKiOn());                     // KI-Hilfe (542): in a round of «Team gegen MoveEye» L2 = the next help
    if (kih && l2 > 0.5 && !GP.l2) window.mwKiCycle();
    GP.l2 = l2 > 0.5;
    if (((l2 > 0.4 && !kih) || (!shut && r2 > 0.4)) && now - GP.zT > 250) { GP.zT = now; zoom(!shut && r2 > l2 ? 1 : -1); }
    if (down(10)) act("center");                                           // L3
    if (down(11)) sim({view: "rnext"}).then(r => { if (r && r.ok) toastT("👁 " + T(VIEWNAME[r.view] || "Free view")); });   // R3
    const K = KEYS(), byKey = k => Object.keys(K).find(id => K[id] === k);
    [[0, "A"], [1, "B"], [2, "X"], [3, "Y"]].forEach(([i, k]) => { if (down(i)) { const id = byKey(k), b = W.querySelector('button.pvb[data-id="' + id + '"]'); act(id, b); wake(); } });
    if (down(8)) { GP.selT = now; GP.selLong = false; }                   // Select: short = swap the pictures,
    if (cur[8] && !GP.selLong && now - GP.selT > 1500) { GP.selLong = true; if (window.servoEstop) window.servoEstop(); else post("/api/servo", {op: "estop"}); toastT("⛔ " + T("EMERGENCY STOP")); }   // held 1.5 s = Not-Aus (2.98.35, 539)
    if (up(8) && !GP.selLong) swap();
    if (down(9)) { GP.startT = now; GP.startLong = false; }               // Start: short = bar, held 1 s = leave
    if (cur[9] && !GP.startLong && now - GP.startT > 1000) { GP.startLong = true; GP.mute = true; open(false); return; }   // (the held Start must not reach the simulator)
    if (up(9) && !GP.startLong) barToggle();
    if (down(14)) focusMove(-1); if (down(15)) focusMove(1); if (down(12)) focusPress(); if (down(13)) help(HELP.hidden);
  }
  setInterval(gpTick, 50);
  window.mwPadOwn = () => (PV.open || GP.mute) && !!pad();                // 470: the raw controller does not go to the simulator meanwhile
  // ---- open / close ----
  let vHome = null;
  function open(on) {
    on = !!on; if (on === PV.open) return;
    PV.open = on; P.open = on; save();
    const v = document.getElementById("video");
    if (on) {
      if (typeof videoOnly !== "undefined" && videoOnly && typeof setVideoOnly === "function") setVideoOnly(false);
      if (document.body.classList.contains("lv-edit") && typeof window.lvEdit === "function") window.lvEdit(false);
      if (typeof window.pipShow === "function") window.pipShow(false);
      const mn = document.getElementById("lv-menu"); if (mn) mn.hidden = true;
      if (v) { vHome = v.parentNode; slot.appendChild(v); }            // the same picture element (no second stream)
      document.body.classList.add("pv-on"); W.hidden = false; GP.prev = []; PV.followed = false; focus = -1;
      layout(); BSIG = ""; paintBar(); wake(); simTick();
      if (!P.help && pad()) { P.help = true; save(); help(true); }
      try { if (touchDev() && W.requestFullscreen && !document.fullscreenElement) W.requestFullscreen({navigationUI: "hide"}).catch(() => {}); } catch (e) {}
    } else {
      document.body.classList.remove("pv-on"); W.hidden = true; MORE.hidden = true; HELP.hidden = true;
      if (v && vHome) vHome.insertBefore(v, vHome.firstChild);
      if (!GP.headZero) post("/api/stick", {x: 0, y: 0, speed: spd()}); if (!GP.rZero) post("/api/mover", {v: 0, w: 0}); GP.headZero = GP.rZero = true;
      if (PV.view) sim({view: "off"}); PV.view = "";
      simTick();
      try { if (document.fullscreenElement === W) document.exitFullscreen().catch(() => {}); } catch (e) {}
      if (typeof window.lvApply === "function") setTimeout(window.lvApply, 50);
    }
  }
  window.pvOpen = open;
  // ---- ask when a controller connects on a phone / tablet (and not the usual hint of 470) ----
  const ASK = E("div"); ASK.id = "pv-ask"; ASK.hidden = true; document.body.appendChild(ASK);
  let askT = null;
  window.mwPadAsk = e => {
    const nm = String((e && e.gamepad && e.gamepad.id) || "").replace(/\(.*?\)/g, "").trim().slice(0, 40);
    if (PV.open) { toastT("🎮 " + T("Controller connected") + (nm ? ": " + nm : "")); return true; }
    if (!handy() || P.ask === false) return false;
    ASK.textContent = ""; ASK.appendChild(E("span", "", "🎮 " + T("Controller connected") + (nm ? ": " + nm : "") + " – " + T("Open the controller view?")));
    const b1 = E("button", "", T("Open")), b2 = E("button", "sec", T("Not now")), b3 = E("button", "sec", T("Don't ask again"));
    [b1, b2, b3].forEach(b => { b.type = "button"; });
    b1.onclick = () => { ASK.hidden = true; open(true); }; b2.onclick = () => { ASK.hidden = true; };
    b3.onclick = () => { ASK.hidden = true; P.ask = false; save(); toastT(T("The controller view stays in «View» (◫) and the 🎮 on the picture")); };
    ASK.append(b1, b2, b3); ASK.hidden = false; clearTimeout(askT); askT = setTimeout(() => { ASK.hidden = true; }, 20000);
    return true;
  };
  // ---- the ways in: 🎮 on the picture (next to ◫) and the «View» panel (536) ----
  function toolBtn() {
    const TB = document.getElementById("lv-tools"); if (!TB || document.getElementById("lv-b-pad")) return;
    const b = E("button", "", "🎮"); b.type = "button"; b.id = "lv-b-pad"; b.title = T("Controller view (phone / tablet, game controller)"); b.setAttribute("aria-label", b.title);
    b.onclick = e => { e.stopPropagation(); open(true); }; b.addEventListener("dblclick", e => e.stopPropagation());
    TB.insertBefore(b, TB.firstChild);
  }
  window.pvMenu = (MN, E_, T_) => {
    MN.appendChild(E_("h3", "", T_("Controller view")));
    const b = E_("button", "sec", "🎮 " + T_("Open the controller view")); b.type = "button"; b.style.width = "100%";
    b.onclick = e => { e.stopPropagation(); MN.hidden = true; open(true); }; MN.appendChild(b);
    MN.appendChild(E_("div", "mut", T_("Full screen for phone and tablet: live picture and simulator, steered with a game controller or the fingers.")));
    if (P.ask === false) { const a = E_("button", "sec", T_("Ask again when a controller connects")); a.type = "button"; a.style.cssText = "width:100%;margin-top:6px";
      a.onclick = e => { e.stopPropagation(); P.ask = true; save(); a.remove(); }; MN.appendChild(a); }
  };
  // ---- every second: state of the buttons, simulator there?, controller there? ----
  setInterval(() => {
    toolBtn();
    const g = pad(); const nm = g ? String(g.id).replace(/\(.*?\)/g, "").trim().slice(0, 30) : "";
    if (PV.open) {
      PADI.hidden = !g; if (g && PADI.textContent !== "🎮 " + nm) PADI.textContent = "🎮 " + nm;
      layout(); paintBar(); simTick();
    }
  }, 1000);
  addEventListener("pagehide", () => { if (PV.open) { if (!GP.headZero) post("/api/stick", {x: 0, y: 0}); if (!GP.rZero) post("/api/mover", {v: 0, w: 0}); } });
  document.addEventListener("visibilitychange", simTick);
  addEventListener("keydown", e => { if (PV.open && e.key === "Escape" && !document.fullscreenElement) open(false); });
  toolBtn();
  if (P.open) setTimeout(() => { if (!PV.open) open(true); }, 900);   // it was open when this device left the page
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", PADVIEW_JS + "</body>", 1)
WEB_UI_LOCAL.add("mw-pad")                                # per device: the controller view of the tablet is not the one of the PC
