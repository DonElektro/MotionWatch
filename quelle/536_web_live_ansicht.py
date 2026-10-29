#@ MoveEye – Teil 536: Live-Seite neu angeordnet: Hoch- / Querformat, Bild immer ganz sichtbar, «Ansicht» (Vorlagen, Bildgrösse, Lieblingsknöpfe, Karten, Bearbeiten). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.26 (Wunsch Daniel): the tab Live arranges itself by the window format
#   portrait  = picture on top (max. height = «Picture size»), simulator, walk test, controls and the other cards below
#   landscape = picture left (as large as the height allows, never cropped: object-fit contain), the cards in a sidebar
#               on the right that scrolls on its own; the simulator directly under the picture (left column)
#   very small window = only the picture with a few floating buttons (☰ opens the cards as a drawer)
# The joystick, «Centre» and «Calibrate» only when there is a pan / tilt head (PCA9685, GPIO chosen by hand, or the simulator);
# in landscape the joystick floats see-through in a corner of the picture. Everything is stored per browser
# (localStorage «mw-live-view», the hidden cards in the existing «mw-hidden» of the ☰ view menu) - not on the device.
# 530 stays as it is except the phone placement (not on the Live tab any more). Translations: part 626.
# ----------------------------------------------------------------------------


def live_has_head():
    """Is there a pan / tilt head to steer? Real servos (PCA9685 found, or GPIO servos chosen by hand) or the simulator.
    «automatic» without PCA9685 falls back to GPIO 17/27 - that cannot be detected, so it does not count (no joystick
    on a Pi with only a camera). The web page uses the same rule (lvHead in LIVE_VIEW_JS) and can override it per browser."""
    global _LIVE_HEAD_T
    b = str(STATE.get("servo_backend") or "")
    h = b.startswith("pca9685") or (CFG.get("servo_driver") == "gpio" and b.startswith(("gpiozero", "pigpio")))
    try:
        h = h or bool(CFG.get("sim_on") and sim_live())
    except Exception:
        pass
    if h:
        _LIVE_HEAD_T = time.time()
    return h or time.time() - _LIVE_HEAD_T < 30          # a slow simulator drops out for a moment: the window is not rebuilt each time


_LIVE_HEAD_T = 0.0


LIVE_VIEW_JS = r"""
<style id="lv-css">
/* ---- 2.98.26: Live page by format (part 536). Everything only on the Live tab and never in full screen ---- */
body.lv:not(.videoonly) main{display:block!important;max-width:none;padding:10px 12px 0;height:var(--lv-h,calc(100dvh - var(--hdr-h,64px)));overflow:hidden}
body.lv:not(.videoonly) main>section{min-height:0;padding:0!important}
#lv-main,#lv-side{min-width:0;min-height:0}
body.lv #lv-main>*,body.lv #lv-side>*{margin-top:0}
body.lv #lv-side>*+*{margin-top:12px}
body.lv #lv-main>*+*{margin-top:12px}
body.lv #vcard{margin:0}
body.lv #vcard .vwrap{display:flex;align-items:center;justify-content:center;background:#000}
body.lv #mctl{display:none!important}
/* landscape: two columns, each scrolls on its own; the picture fills the left column (minus a peek at the simulator) */
body.lv-land:not(.videoonly) main>section{display:grid!important;grid-template-columns:minmax(0,1fr) var(--lv-sw,360px);gap:12px;height:100%;overflow:hidden!important}
body.lv-land:not(.videoonly) #lv-main{overflow-y:auto;overflow-x:hidden;display:flex;flex-direction:column;overscroll-behavior:contain;scrollbar-width:thin;padding-bottom:12px}
body.lv-land:not(.videoonly) #lv-side{overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;scrollbar-width:thin;padding-bottom:16px}
body.lv-land:not(.videoonly) #vcard{flex:0 0 var(--lv-pich,100%);min-height:160px;display:flex;flex-direction:column;padding:8px}
body.lv-land:not(.videoonly) #vcard .vwrap{flex:1 1 auto;min-height:0}
body.lv-land:not(.videoonly) #video{width:100%;height:100%;max-height:none;min-height:0;object-fit:contain}
body.lv-land:not(.videoonly) #lv-main>:not(#vcard){flex:none}
/* portrait: one column, the page (phone) or the column (computer) scrolls; picture height limited by «Picture size» */
body.lv-port:not(.videoonly) main>section{display:block!important;height:100%;overflow-y:auto!important;overflow-x:hidden;scrollbar-width:thin;padding-bottom:16px!important}
body.lv-port:not(.videoonly) #lv-side{margin-top:12px}
body.lv-port:not(.videoonly) #vcard{padding:8px}
body.lv-port:not(.videoonly) #video{width:100%;height:auto;max-height:var(--lv-ph,60vh);min-height:0;object-fit:contain}
body.lv-low:not(.videoonly) header{position:static}
body.lv-ovon .ctl-stick{display:none!important}
/* very small window: only the picture, the cards as a drawer (☰) */
body.lv-mini:not(.videoonly) header{display:none!important}
body.lv-mini:not(.videoonly) main{padding:0}
body.lv-mini:not(.videoonly) main>section{display:block!important;height:100%;overflow:hidden!important}
body.lv-mini:not(.videoonly) #lv-main{height:100%}
body.lv-mini:not(.videoonly) #lv-main>:not(#vcard){display:none!important}
body.lv-mini:not(.videoonly) #vcard{height:100%;padding:0;border:0;border-radius:0;display:flex;flex-direction:column}
body.lv-mini:not(.videoonly) #vcard .vwrap{flex:1 1 auto;min-height:0;border-radius:0}
body.lv-mini:not(.videoonly) #video{width:100%;height:100%;min-height:0;object-fit:contain}
body.lv-mini:not(.videoonly) #lv-side{display:none}
body.lv-mini.lv-drawer:not(.videoonly) #lv-side{display:block;position:fixed;z-index:70;top:0;right:0;bottom:0;width:min(360px,92vw);overflow-y:auto;
  background:var(--bg);border-left:1px solid var(--line);padding:52px 10px 16px;box-shadow:var(--shadow)}
body.videoonly .mwsimbar{position:fixed;top:0;left:0;right:0;opacity:.85}   /* the simulation stripe over the picture, not pushing it down */
body.videoonly #lv-side,body.videoonly #lv-tools,body.videoonly #lv-joy{display:none!important}
body.videoonly #lv-main>:not(#vcard){display:none!important}
/* the tool buttons on the picture: Ansicht, full screen (+ ☰ in the small window) */
#lv-tools{position:absolute;top:8px;right:8px;z-index:6;display:flex;gap:6px}
#lv-tools button{width:38px;height:38px;padding:0;border-radius:10px;border:1px solid rgba(255,255,255,.3);background:rgba(8,12,20,.55);color:#fff;
  font-size:17px;line-height:1;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px)}
#lv-tools button svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#lv-tools #lv-b-drawer{display:none}body.lv-mini #lv-tools #lv-b-drawer{display:inline-flex}
body.lv-mini.lv-drawer #lv-tools{position:fixed;z-index:71}
/* the joystick see-through in a picture corner */
#lv-joy{position:absolute;z-index:5;right:12px;bottom:12px;display:flex;align-items:flex-end;gap:8px;transition:opacity .5s;touch-action:none}
body.swapside #lv-joy{right:auto;left:12px;flex-direction:row-reverse}
#lv-joy.idle{opacity:.45}#lv-joy:empty{display:none}
#lv-joy .stick{width:clamp(96px,18vmin,140px);height:clamp(96px,18vmin,140px);background:rgba(8,12,20,.22);border:2px solid rgba(255,255,255,.7);
  box-shadow:0 2px 14px rgba(0,0,0,.35);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)}
#lv-joy .stick::before,#lv-joy .stick::after{background:rgba(255,255,255,.3)}
#lv-joy .stick .ar{color:#fff;text-shadow:0 1px 3px #000}
#lv-joy .knob{width:30%;height:30%;margin:-15% 0 0 -15%}
#lv-joy button{width:40px;height:40px;border-radius:50%;padding:0;font-size:18px;background:rgba(8,12,20,.4);color:#fff;border:2px solid rgba(255,255,255,.6)}
/* no pan / tilt head: no joystick, no centre / calibrate / waypoints, no follow / patrol */
body.lv-nohead #stick,body.lv-nohead .ctl-stick,body.lv-nohead #qs-track,body.lv-nohead #qs-patrol,body.lv-nohead #patrol-st,body.lv-nohead #vo-center,body.lv-nohead #lv-joy{display:none!important}
body.lv-nohead:not(.moveravail) #ctl-side{display:none!important}
body.lv-nohead.moveravail #ctl-side>:not(.spd),body.lv-nohead.moveravail #ctl-side .spd>:not(#mv-tog){display:none!important}
/* the controls card: wraps instead of overlapping (the old fixed columns pushed «Mittel» under the switches) */
body.lv #ctl-left{display:flex!important;flex-wrap:wrap;align-items:flex-start;justify-content:center;gap:12px 18px;padding:0 2px;grid-template-areas:none!important}
body.lv #ctl-left>*{min-width:0}
body.lv #ctl-left .ctl-stick,body.lv #ctl-left .ctl-mstick{flex:none}
body.lv #ctl-left .ctl-side{flex:1 1 170px;max-width:260px}
body.lv #ctl-left .ctl-mid{flex:1 1 100%;width:100%;order:5}
body.lv.swapside #ctl-left .ctl-side{order:-1}
body.lv #ctl-left #set-foot{order:9;flex:1 1 100%}
body.lv #ctl-left .stick{width:140px;height:140px}
body.lv-land #ctl-left .stick{width:124px;height:124px}
body.lv .ctl-grid{display:block!important}
/* favourites: one row; the rest behind «… more» */
body.lv #qsw{display:flex!important;flex-wrap:wrap;gap:6px;margin:4px 0 0!important}
body.lv #qsw>button{flex:1 1 0;min-width:44px;max-width:96px}
body.lv #qsw{container-type:inline-size}
@container (max-width:430px){body.lv #qsw:not(.lvopen)>button small{display:none}body.lv #qsw:not(.lvopen)>button{padding:7px 1px}}
body.lv #qsw:not(.lvopen){flex-wrap:nowrap}
body.lv #qsw:not(.lvopen)>button{min-width:0}
body.lv #qsw.lvopen>button{flex:0 0 calc((100% - 30px) / 6);max-width:none;min-width:52px}
body.lv #qsw:not(.lvopen)>button:not(.lvfav):not(#lv-more){display:none}
body.lv #qsw>button.lvfav{order:var(--o,0)}
body.lv #qsw>button:not(.lvfav){order:200}
body.lv #qsw>#lv-more{order:150}body.lv #qsw.lvopen>#lv-more{order:300}
body.lv #qsw.lvopen>button.lvfav{box-shadow:inset 0 -3px 0 var(--acc)}
#lv-more small{color:var(--acc2)!important}
/* the «Ansicht» panel */
#lv-menu{position:fixed;z-index:80;top:calc(var(--hdr-h,64px) + 6px);right:12px;width:min(380px,calc(100vw - 24px));max-height:calc(100dvh - var(--hdr-h,64px) - 20px);overflow-y:auto;
  background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:6px 14px 14px;box-shadow:var(--shadow)}
body.lv-mini #lv-menu{top:8px;max-height:calc(100dvh - 16px)}
#lv-menu[hidden]{display:none}
#lv-menu h3{margin:12px 0 6px;font-size:11px;color:var(--mut);letter-spacing:.08em;text-transform:uppercase}
#lv-menu .lvseg{display:flex;flex-wrap:wrap;gap:6px}#lv-menu .lvseg button{flex:1 1 auto;padding:7px 8px;font-size:13px}
#lv-menu .lvseg button.on{background:var(--acc);color:#fff;border-color:transparent}
#lv-menu .lvpre{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
#lv-menu .lvpre button{display:flex;flex-direction:column;align-items:center;gap:2px;padding:8px 4px;font-size:13px}
#lv-menu .lvpre button small{font-size:10.5px;color:var(--mut);font-weight:500;text-align:center}
#lv-menu .lvpre button.on{box-shadow:inset 0 0 0 2px var(--acc)}
#lv-menu .lvrow{display:flex;align-items:center;gap:8px;padding:4px 0}
#lv-menu .lvrow>span{flex:1;min-width:0}
#lv-menu .lvrow button{padding:3px 9px;font-size:12px}
#lv-menu input[type=range]{width:100%}
#lv-menu .lvfoot{display:flex;gap:8px;margin-top:14px}#lv-menu .lvfoot button{flex:1;padding:9px}
#lv-menu .lvhead{display:flex;align-items:center;justify-content:space-between;position:sticky;top:-6px;background:var(--panel);padding:8px 0 4px;z-index:1}
#lv-menu .lvhead b{font-size:15px}#lv-menu .lvhead button{width:34px;height:34px;padding:0}
/* the live cards are shown / hidden per device (class lvh); the shared «mw-hidden» (vh) of the ☰ menu does not apply here */
body.lv #lv-side>.vh:not([hidden]),body.lv #lv-simw>.vh{display:block!important}
body.lv #lv-side>.lvh,body.lv #lv-simw>.lvh{display:none!important}
/* edit mode */
body.lv-edit #lv-side>.lvh:not([hidden]){display:block!important;opacity:.45}
body.lv-edit #lv-side>*{outline:2px dashed var(--acc);outline-offset:2px}
.lv-et{display:inline-flex;gap:4px;margin-left:auto;float:right;position:relative;z-index:3}
.lv-et button{padding:2px 8px;font-size:13px;line-height:1.3;min-height:0}
#lv-editbar{position:fixed;z-index:85;left:12px;right:12px;bottom:max(12px,env(safe-area-inset-bottom));max-width:720px;margin:0 auto;display:flex;gap:8px;align-items:center;
  flex-wrap:wrap;background:var(--panel);border:1px solid var(--acc);border-radius:12px;padding:10px 12px;box-shadow:var(--shadow)}
#lv-editbar>span{flex:1 1 220px;font-size:13px}#lv-editbar button{padding:8px 12px}
body.lv-edit #qsw>button{position:relative}
body.lv-edit #qsw>button:not(#lv-more):not(.qs-edit)::after{content:"☆";position:absolute;top:1px;right:3px;font-size:11px;color:var(--mut)}
body.lv-edit #qsw>button.lvfav:not(#lv-more):not(.qs-edit)::after{content:"★";color:var(--yel)}
body.lv-edit #lv-side{padding-bottom:90px!important}
#lv-setup .btns{margin-top:8px}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*LVDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const KEY = "mw-live-view";                          // per browser (this phone / PC) - never sent to the device
  const DEF = {layout: "auto", size: 60, joy: "auto", ov: "auto", favs: null, order: null, more: false, preset: "", hide: ["lvsetup"]};
  const DEFFAV = ["rec", "photo", "track", "patrol", "white", "ir", "listen", "therm"];
  const DEFORDER = ["walktest", "controls", "whatwas", "simtile", "lvsetup"];   // Daniel: picture → simulator → walk test → the rest
  let V = Object.assign({}, DEF);
  try { Object.assign(V, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) {}
  V.hide = Array.isArray(V.hide) ? V.hide.slice() : ["lvsetup"];
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(V)); } catch (e) {} };
  const sec = document.querySelector("main>section"), vc = document.getElementById("vcard");
  if (!sec || !vc) return;
  document.body.classList.add("lv");
  const M = E("div"); M.id = "lv-main"; const S = E("div"); S.id = "lv-side";
  sec.insertBefore(M, sec.firstChild); M.appendChild(vc); sec.appendChild(S);
  // ---- the extra card «Set up» (preset «Einrichten»): only links, no second copy of a control ----
  const SU = E("details", "card"); SU.id = "lv-setup"; SU.open = true;
  SU.dataset.view = "lvsetup"; SU.dataset.vgroup = "Panels"; SU.dataset.vlabel = "Set up";
  const sus = E("summary"); sus.appendChild(E("span", "", "🛠 " + T("Set up"))); SU.appendChild(sus);
  SU.appendChild(E("div", "mut", T("Draw where MoveEye should watch, then check the range with the walk test.")));
  const sub = E("div", "btns");
  const zb = E("button", "sec", "✏️ " + T("Draw the zones")); zb.type = "button"; zb.onclick = () => { location.href = "/zones"; };
  const wb = E("button", "sec", "🚶 " + T("Walk test")); wb.type = "button";
  wb.onclick = () => { const w = document.getElementById("wt-card"); if (w) { w.open = true; w.scrollIntoView({behavior: "smooth", block: "start"}); } };
  sub.append(zb, wb); SU.appendChild(sub); S.appendChild(SU);
  // first time in this browser: take over the cards hidden earlier with the ☰ view menu (from now on the live cards are per device)
  let firstRun = false;
  try { firstRun = localStorage.getItem(KEY) === null; } catch (e) {}
  if (firstRun && typeof HIDDEN !== "undefined") ["controls", "walktest", "simctl", "whatwas", "simtile"].forEach(k => { if (HIDDEN.has(k) && !V.hide.includes(k)) V.hide.push(k); });
  // ---- tool buttons on the picture ----
  const vw = vc.querySelector(".vwrap");
  const TB = E("div"); TB.id = "lv-tools";
  const tbtn = (id, html, tip, fn) => { const b = E("button"); b.type = "button"; b.id = id; b.innerHTML = html; b.title = T(tip); b.setAttribute("aria-label", T(tip));
    b.onclick = e => { e.stopPropagation(); fn(e); }; b.addEventListener("dblclick", e => e.stopPropagation()); TB.appendChild(b); return b; };
  tbtn("lv-b-drawer", "☰", "Controls and cards", () => document.body.classList.toggle("lv-drawer"));
  tbtn("lv-b-view", '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M14 4v16"/></svg>', "View: layout, picture size, buttons, cards", () => menu());
  tbtn("lv-b-fs", '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/></svg>', "Full screen (double click on the picture, Esc = back)",
       () => { if (typeof setVideoOnly === "function") setVideoOnly(true); });
  if (vw) vw.appendChild(TB);
  const J = E("div"); J.id = "lv-joy"; if (vw) vw.appendChild(J);
  let jIdle = null;
  const jWake = () => { J.classList.remove("idle"); clearTimeout(jIdle); jIdle = setTimeout(() => J.classList.add("idle"), 3000); };
  J.addEventListener("pointerdown", jWake); J.addEventListener("pointermove", e => { if (e.buttons) jWake(); });
  J.addEventListener("dblclick", e => e.stopPropagation());
  const jc = E("button", "", "◎"); jc.type = "button"; jc.title = T("Centre"); jc.onclick = e => { e.stopPropagation(); const c = document.getElementById("stick-center"); if (c) c.click(); };
  // ---- what the page knows ----
  const J_ = () => (typeof QSJ !== "undefined" && QSJ) || {};
  let headT = 0;
  function lvHead() {                                   // same rule as live_has_head() in Python; «Joystick: always / never» overrides it
    if (V.joy === "on") return true; if (V.joy === "off") return false;
    const j = J_(), s = j.state || {}, c = j.cfg || {}, b = String(s.servo_backend || "");
    if (!j.state) return true;                          // not loaded yet: do not let the stick flicker away
    const h = !!(s.sim && s.sim.on && s.sim.ok) || b.indexOf("pca9685") === 0 || (c.servo_driver === "gpio" && /^(gpiozero|pigpio)/.test(b));
    if (h) headT = Date.now();
    return h || Date.now() - headT < 30000;              // a slow simulator drops out for a moment: keep the stick 30 s
  }
  function mode() {
    const w = innerWidth, h = innerHeight;
    if (V.layout === "mini") return "mini";
    if (h < 300 || w < 300 || (w < 560 && h < 420)) return "mini";
    if (V.layout === "port") return "port";
    if (V.layout === "land") return w < 520 ? "port" : "land";
    return (w >= 640 && w >= h * 1.1) ? "land" : "port";
  }
  const isVO = () => document.body.classList.contains("videoonly");
  // ---- order of the cards ----
  const keyOf = x => (x.dataset && x.dataset.view) || x.id || "";
  let busy = false;
  function tagCards() {
    const aw = document.getElementById("alx-what");
    if (aw && !aw.dataset.view) { aw.dataset.view = "whatwas"; aw.dataset.vgroup = "Panels"; aw.dataset.vlabel = "What was that?"; if (typeof applyHidden === "function") applyHidden(); }
    const st = document.getElementById("simtile");
    if (st && !st.dataset.view) { st.dataset.view = "simtile"; st.dataset.vgroup = "Panels"; st.dataset.vlabel = "Simulator tile"; st.style.marginBottom = "0"; if (typeof applyHidden === "function") applyHidden(); }
  }
  function remember(d) {                                // cards added later (walk test …) remember open / closed like the others
    if (d.tagName !== "DETAILS" || d.dataset.lvo) return; d.dataset.lvo = "1";
    const k = "mw-open:" + (d.dataset.view || (d.querySelector("summary") || {}).textContent);
    try { const v = localStorage.getItem(k); if (v !== null) d.open = v === "1"; } catch (e) {}
    d.addEventListener("toggle", () => { try { localStorage.setItem(k, d.open ? "1" : "0"); } catch (e) {} });
  }
  function arrange() {
    if (busy) return; busy = true;
    try {
      tagCards();
      const sw = document.getElementById("lv-simw");
      if (M.firstChild !== vc) M.insertBefore(vc, M.firstChild);
      if (sw && (sw.parentNode !== M || vc.nextSibling !== sw)) vc.after(sw);       // the simulator directly under the picture
      const items = [...M.children, ...S.children, ...[...sec.children].filter(x => x !== M && x !== S)]
        .filter(x => x !== vc && x !== sw && x.tagName !== "STYLE" && x.tagName !== "SCRIPT");
      const ord = (V.order && V.order.length ? V.order : []).concat(DEFORDER.filter(k => !(V.order || []).includes(k)));
      const dom = new Map(items.map((x, i) => [x, i]));
      const rank = x => { const i = ord.indexOf(keyOf(x)); return i >= 0 ? i : 100 + dom.get(x); };
      const want = items.slice().sort((a, b) => rank(a) - rank(b));
      const now = [...S.children];
      if (want.length !== now.length || want.some((x, i) => now[i] !== x)) want.forEach(x => S.appendChild(x));
      S.querySelectorAll(":scope > details.card").forEach(remember);
      if (document.body.classList.contains("lv-edit")) editTools();
    } finally { busy = false; }
  }
  const mo = new MutationObserver(() => { if (!busy) requestAnimationFrame(() => { arrange(); fit(); }); });
  mo.observe(sec, {childList: true}); mo.observe(M, {childList: true});
  // ---- layout ----
  function fit() {
    const md = mode(), B = document.body;
    B.classList.toggle("lv-low", md === "land" && innerHeight < 560);   // phone held sideways: the header scrolls away, the picture gets the whole height
    B.classList.toggle("lv-land", md === "land"); B.classList.toggle("lv-port", md === "port"); B.classList.toggle("lv-mini", md === "mini");
    if (md !== "mini" && B.classList.contains("lv-drawer")) B.classList.remove("lv-drawer");
    const main = document.querySelector("main"); if (!main || isVO()) return;
    const low = B.classList.contains("lv-low");
    const top = low ? 0 : Math.max(0, main.getBoundingClientRect().top + scrollY);
    const vh = window.visualViewport ? visualViewport.height : innerHeight;
    const H = Math.max(200, Math.round(vh - top));
    document.documentElement.style.setProperty("--lv-h", H + "px");
    const sw = document.getElementById("lv-simw"), simOn = sw && !sw.hidden && !isHid("simctl");
    if (md === "land") {
      const W = main.clientWidth - 24, share = 0.5 + Math.max(0, Math.min(100, +V.size)) / 100 * 0.35;
      let side = Math.round(Math.max(260, Math.min(Math.max(640, W * 0.45), (1 - share) * W)));
      const v = document.getElementById("video"), ar = (v && v.naturalWidth && v.naturalHeight) ? v.naturalWidth / v.naturalHeight : 16 / 9;
      const peek = simOn ? 54 : 0, picH = H - 12 - 18 - peek, picW = picH * ar + 18;
      if (W - side - 12 > picW) side = Math.round(Math.min(Math.max(side, W - picW - 12), Math.max(side, W * 0.55)));   // picture limited by the height: the spare width goes to the cards
      document.documentElement.style.setProperty("--lv-sw", side + "px");
      document.documentElement.style.setProperty("--lv-pich", peek ? "calc(100% - " + peek + "px)" : "100%");
    } else if (md === "port") {
      document.documentElement.style.setProperty("--lv-ph", Math.round(H * (30 + Math.max(0, Math.min(100, +V.size)) * 0.6) / 100) + "px");
    }
  }
  let lowWas = false;
  function lowScroll() {                                // sideways phone: put the picture at the top of the screen (header above, scrolled away)
    const low = document.body.classList.contains("lv-low");
    if (low && !lowWas && !isVO()) [80, 400, 1000].forEach(ms => setTimeout(() => { const m = document.querySelector("main"); if (m && document.body.classList.contains("lv-low")) scrollTo(0, m.getBoundingClientRect().top + scrollY); }, ms));
    lowWas = low;
  }
  function placeStick() {
    const head = lvHead(), md = mode();
    document.body.classList.toggle("lv-nohead", !head);
    const st = document.getElementById("stick"), box = document.querySelector(".ctl-stick .stickbox");
    if (!st || !box || isVO()) return;                   // full screen: setVideoOnly / voStick own the stick
    const ov = head && (md === "mini" || (V.ov === "auto" ? md === "land" : V.ov === "on"));
    document.body.classList.toggle("lv-ovon", ov);
    if (ov && st.parentNode !== J) { J.appendChild(st); J.appendChild(jc); jWake(); }
    if (!ov && st.parentNode === J) { box.insertBefore(st, box.firstChild); jc.remove(); }
    if (!ov && st.parentNode !== J) jc.remove();
  }
  // ---- favourites in the quick switches ----
  function favs() { return (V.favs && V.favs.length ? V.favs : DEFFAV).slice(0, 8); }
  function paintFavs() {
    const q = document.getElementById("qsw"); if (!q) return;
    const F = favs();
    q.querySelectorAll(":scope > button").forEach(b => {
      if (b.id === "lv-more") return;
      const id = b.id.replace(/^qs-/, ""), i = F.indexOf(id);
      b.classList.toggle("lvfav", i >= 0); b.style.setProperty("--o", i >= 0 ? i : 0);
    });
    let m = document.getElementById("lv-more");
    if (!m || m.parentNode !== q) { m = E("button", "sec"); m.type = "button"; m.id = "lv-more"; m.append(E("span", "", "…"), E("small", "", ""));
      m.onclick = e => { e.stopPropagation(); V.more = !V.more; save(); paintFavs(); }; q.appendChild(m); }
    q.classList.toggle("lvopen", !!V.more || document.body.classList.contains("lv-edit"));
    const sm = m.querySelector("small"), tx = T(q.classList.contains("lvopen") ? "less" : "more");
    if (sm.textContent !== tx) sm.textContent = tx;
    m.title = T(q.classList.contains("lvopen") ? "Show only the favourites" : "Show all quick switches");
  }
  // edit mode: a tap on a quick switch makes it a favourite (★) instead of switching
  document.addEventListener("click", e => {
    if (!document.body.classList.contains("lv-edit")) return;
    const b = e.target.closest && e.target.closest("#qsw > button"); if (!b || b.id === "lv-more" || b.classList.contains("qs-edit")) return;
    e.preventDefault(); e.stopPropagation();
    const id = b.id.replace(/^qs-/, ""), F = favs();
    const i = F.indexOf(id); if (i >= 0) F.splice(i, 1); else { if (F.length >= 8) { if (typeof toast === "function") toast("★ " + T("At most 8 favourites")); return; } F.push(id); }
    V.favs = F; V.preset = ""; save(); paintFavs();
  }, true);
  document.addEventListener("pointerdown", e => {          // the talk tile listens to pointerdown: no talking in the edit mode
    if (document.body.classList.contains("lv-edit") && e.target.closest && e.target.closest("#qsw > button[data-talk]")) { e.stopPropagation(); e.preventDefault(); }
  }, true);
  // ---- cards: hide / show (the same «mw-hidden» as the ☰ view menu), move ----
  function cards() { return [...S.children].filter(x => keyOf(x) && x.id !== "mbtns2"); }
  const labelOf = x => T(x.dataset.vlabel || keyOf(x));
  const isHid = k => (V.hide || []).includes(k);
  function setHidden(k, hide) {                         // per device («mw-live-view»), not the shared «mw-hidden» of the ☰ menu
    const H = new Set(V.hide || []); if (hide) H.add(k); else H.delete(k); V.hide = [...H]; save(); paintHidden();
  }
  function paintHidden() {
    [...cards(), document.getElementById("lv-sim")].forEach(x => { if (x) x.classList.toggle("lvh", isHid(keyOf(x))); });
  }
  function move(x, d) {
    const L = cards(), i = L.indexOf(x), j = i + d; if (i < 0 || j < 0 || j >= L.length) return;
    [L[i], L[j]] = [L[j], L[i]]; V.order = L.map(keyOf); V.preset = ""; save(); arrange(); editTools(); x.scrollIntoView({block: "nearest"});
  }
  function editTools() {
    cards().forEach(x => {
      let tb = x.querySelector(":scope > .lv-et, :scope > summary > .lv-et");
      if (tb) { const h = tb.querySelector(".lv-eh"); if (h) h.textContent = isHid(keyOf(x)) ? "👁" : "✕"; return; }
      tb = E("span", "lv-et");
      const mk = (txt, tip, fn, cls) => { const b = E("button", "sec" + (cls ? " " + cls : ""), txt); b.type = "button"; b.title = T(tip);
        b.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); fn(); }); tb.appendChild(b); return b; };
      mk("▲", "Up", () => move(x, -1)); mk("▼", "Down", () => move(x, 1));
      mk(isHid(keyOf(x)) ? "👁" : "✕", "Hide / show", () => { setHidden(keyOf(x), !isHid(keyOf(x))); V.preset = ""; save(); editTools(); }, "lv-eh");
      const sm = x.tagName === "DETAILS" ? x.querySelector(":scope > summary") : null;
      if (sm) sm.appendChild(tb); else x.insertBefore(tb, x.firstChild);
    });
  }
  function edit(on) {
    document.body.classList.toggle("lv-edit", on);
    document.querySelectorAll(".lv-et").forEach(x => x.remove());
    let bar = document.getElementById("lv-editbar");
    if (on) {
      menuClose();
      if (!bar) {
        bar = E("div"); bar.id = "lv-editbar";
        bar.appendChild(E("span", "", "✏️ " + T("Edit: move the cards with ▲ ▼, ✕ hides one (👁 shows it again). Tap a quick switch = favourite ★ (max. 8).")));
        const r = E("button", "sec", T("Reset")); r.type = "button"; r.onclick = () => { if (confirm(T("Back to the standard view of the live page?"))) reset(); };
        const d = E("button", "", T("Finish")); d.type = "button"; d.onclick = () => edit(false);
        bar.append(r, d); document.body.appendChild(bar);
      }
      editTools();
      setTimeout(() => { const c = document.getElementById("lv-side"); if (c && mode() === "port") c.scrollIntoView({behavior: "smooth", block: "start"}); }, 50);
    } else if (bar) bar.remove();
    paintFavs();
  }
  // ---- presets ----
  const LIVEKEYS = () => cards().map(keyOf).concat(["simctl"]);
  const PRESETS = {
    look: {ic: "👁", lb: "Just watching", d: "big picture", v: {size: 100, ov: "auto", more: false}, show: ["controls", "simctl"]},
    operate: {ic: "🕹", lb: "Operating", d: "everything", v: {size: 60, ov: "auto"}, hide: ["lvsetup"]},
    setup: {ic: "🛠", lb: "Setting up", d: "walk test, zones", v: {size: 40, ov: "off"}, hide: []}};
  function preset(k) {
    const P = PRESETS[k]; if (!P) return;
    Object.assign(V, P.v, {preset: k, order: null}); save();
    LIVEKEYS().forEach(c => setHidden(c, P.show ? !P.show.includes(c) : (P.hide || []).includes(c)));
    if (k === "setup") { const w = document.getElementById("wt-card"); if (w) w.open = true; SU.open = true; }
    apply(); if (typeof toast === "function") toast("✓ " + P.ic + " " + T(P.lb));
  }
  function reset() {
    V = Object.assign({}, DEF); save();
    V.hide = ["lvsetup"]; save(); paintHidden();
    edit(false); apply();
  }
  // ---- the «Ansicht» panel ----
  const MN = E("div"); MN.id = "lv-menu"; MN.hidden = true; document.body.appendChild(MN);
  function menuClose() { MN.hidden = true; }
  document.addEventListener("click", e => { if (!MN.hidden && !MN.contains(e.target) && !TB.contains(e.target) && document.body.contains(e.target)) menuClose(); });
  addEventListener("keydown", e => { if (e.key === "Escape" && !MN.hidden) menuClose(); });
  function seg(opts, cur, fn) {
    const s = E("div", "lvseg");
    opts.forEach(([v, lb]) => { const b = E("button", "sec" + (cur === v ? " on" : ""), T(lb)); b.type = "button";
      b.onclick = e => { e.stopPropagation(); fn(v); V.preset = ""; save(); apply(); menuBuild(); }; s.appendChild(b); });
    return s;
  }
  function menuBuild() {
    MN.textContent = "";
    const hd = E("div", "lvhead"); hd.appendChild(E("b", "", "◫ " + T("View of the live page")));
    const x = E("button", "sec", "✕"); x.type = "button"; x.title = T("Close"); x.onclick = e => { e.stopPropagation(); menuClose(); }; hd.appendChild(x); MN.appendChild(hd);
    MN.appendChild(E("h3", "", T("Ready-made views")));
    const pr = E("div", "lvpre");
    Object.entries(PRESETS).forEach(([k, P]) => { const b = E("button", "sec" + (V.preset === k ? " on" : "")); b.type = "button";
      b.append(E("span", "", P.ic + " " + T(P.lb)), E("small", "", T(P.d)));
      b.onclick = e => { e.stopPropagation(); preset(k); menuBuild(); }; pr.appendChild(b); });
    MN.appendChild(pr);
    MN.appendChild(E("h3", "", T("Layout")));
    MN.appendChild(seg([["auto", "Automatic"], ["port", "Portrait"], ["land", "Landscape"], ["mini", "Picture only"]], V.layout, v => { V.layout = v; }));
    const md = mode();
    MN.appendChild(E("div", "mut", T("Now") + ": " + T({land: "picture left, cards right", port: "picture on top, cards below", mini: "only the picture (☰ = cards)"}[md])));
    MN.appendChild(E("h3", "", T("Picture size")));
    const r = E("input"); r.type = "range"; r.min = 0; r.max = 100; r.step = 5; r.value = V.size;
    r.oninput = () => { V.size = +r.value; V.preset = ""; save(); fit(); };
    MN.appendChild(r);
    MN.appendChild(E("div", "mut", T(md === "land" ? "Landscape: how wide the picture is next to the cards (it never gets higher than the window)." : "Portrait: how high the picture may be.")));
    MN.appendChild(E("h3", "", T("Joystick")));
    MN.appendChild(seg([["auto", "Automatic"], ["on", "Always"], ["off", "Never"]], V.joy, v => { V.joy = v; }));
    const j = J_(), hs = j.state ? (lvHead() ? "pan / tilt head found" : "no pan / tilt head found") : "";
    if (hs && V.joy === "auto") MN.appendChild(E("div", "mut", T("Automatic") + ": " + T(hs)));
    MN.appendChild(seg([["auto", "In the picture in landscape"], ["on", "In the picture"], ["off", "In the controls"]], V.ov, v => { V.ov = v; }));
    MN.appendChild(E("h3", "", T("Favourite buttons (4–8)")));
    const F = favs(), all = [...document.querySelectorAll("#qsw > button")].filter(b => b.id !== "lv-more" && !b.classList.contains("qs-edit") && !b.classList.contains("na"));
    const name = id => { const b = document.getElementById("qs-" + id); return b ? (b.querySelector("span") || {}).textContent + " " + (b.querySelector("small") || {}).textContent : id; };
    const ids = F.filter(id => all.some(b => b.id === "qs-" + id)).concat(all.map(b => b.id.replace(/^qs-/, "")).filter(id => !F.includes(id)));
    ids.forEach(id => {
      const row = E("label", "lvrow"), cb = E("input"); cb.type = "checkbox"; cb.checked = F.includes(id);
      cb.disabled = !cb.checked && F.length >= 8;
      cb.onchange = () => { const G = favs(); const i = G.indexOf(id); if (cb.checked && i < 0) G.push(id); if (!cb.checked && i >= 0) G.splice(i, 1); V.favs = G; V.preset = ""; save(); paintFavs(); menuBuild(); };
      row.append(cb, E("span", "", name(id)));
      if (F.includes(id)) {
        const up = E("button", "sec", "▲"), dn = E("button", "sec", "▼"); up.type = dn.type = "button";
        const mv = d => ev => { ev.preventDefault(); ev.stopPropagation(); const G = favs(), i = G.indexOf(id), k = i + d; if (k < 0 || k >= G.length) return; [G[i], G[k]] = [G[k], G[i]]; V.favs = G; save(); paintFavs(); menuBuild(); };
        up.onclick = mv(-1); dn.onclick = mv(1); row.append(up, dn);
      }
      MN.appendChild(row);
    });
    MN.appendChild(E("div", "mut", T("The other quick switches stay behind «… more». Hide a switch everywhere: «✏️ Arrange» in the quick switches.")));
    MN.appendChild(E("h3", "", T("Cards")));
    const sw = document.getElementById("lv-sim");
    const list = cards().concat(sw && !document.getElementById("lv-simw").hidden ? [sw] : []);
    list.forEach(c => { const k = keyOf(c); const row = E("label", "lvrow"), cb = E("input"); cb.type = "checkbox";
      cb.checked = !isHid(k);
      cb.onchange = () => { setHidden(k, !cb.checked); V.preset = ""; save(); fit(); };
      row.append(cb, E("span", "", labelOf(c))); MN.appendChild(row); });
    const ft = E("div", "lvfoot");
    const eb = E("button", "sec", "✏️ " + T("Edit")); eb.type = "button"; eb.onclick = e => { e.stopPropagation(); edit(true); };
    const rb = E("button", "sec", T("Reset")); rb.type = "button"; rb.onclick = e => { e.stopPropagation(); if (confirm(T("Back to the standard view of the live page?"))) { reset(); menuBuild(); } };
    ft.append(eb, rb); MN.appendChild(ft);
    MN.appendChild(E("div", "mut", T("Stored only in this browser (this phone / PC).")));
  }
  function menu() { MN.hidden = !MN.hidden; if (!MN.hidden) { const vm = document.getElementById("viewmenu"); if (vm) vm.hidden = true; menuBuild(); } }
  window.lvMenu = menu;
  // ---- everything ----
  function apply() { arrange(); paintHidden(); fit(); placeStick(); paintFavs(); lowScroll(); }
  window.lvApply = apply;
  addEventListener("resize", () => { fit(); placeStick(); lowScroll(); });
  if (window.visualViewport) visualViewport.addEventListener("resize", fit);
  let lastCls = "";                                     // full screen on / off, ⇆, mover …: place again (only when the classes really changed)
  new MutationObserver(() => { const c = document.body.className; if (c === lastCls) return;
    if (/\bvideoonly\b/.test(lastCls) && !isVO()) lowWas = false;      // back from full screen: the sideways phone shows the picture again
    lastCls = c; fit(); placeStick(); lowScroll(); })
    .observe(document.body, {attributes: true, attributeFilter: ["class"]});
  const v = document.getElementById("video"); if (v) v.addEventListener("load", fit);
  let lastSig = "";
  setInterval(() => {
    const sw = document.getElementById("lv-simw");
    const sig = [lvHead(), sw && sw.hidden, document.getElementById("qsw") && document.getElementById("qsw").childElementCount, typeof LANG !== "undefined" && LANG].join("|");
    paintFavs();
    if (sig !== lastSig) { lastSig = sig; apply(); }
  }, 1000);
  apply(); setTimeout(apply, 600); setTimeout(apply, 2000);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", LIVE_VIEW_JS + "</body>", 1)
WEB_UI_LOCAL.add("mw-live-view")                         # per device: the layout of the phone is not the one of the PC (not copied to the Pi)
