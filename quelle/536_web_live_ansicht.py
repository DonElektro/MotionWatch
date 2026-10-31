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
# aufr: «mw-hidden» (the ☰ menu of the other tabs) is per device now as well (WEB_UI_LOCAL) - the same rule and wording; the
# live cards are only in «◫ Ansicht» (the ☰ menu leaves them out), so no card has two «hide» switches.
# 530 stays as it is except the phone placement (not on the Live tab any more). Translations: part 626.
# 2.98.29 (Wunsch Daniel): ONE edit mode for the arrangement (the separate «✏️ Anpassen» of the quick switches is gone):
#   favourites ★, order ▲ ▼ and hidden ✕ of the quick switches and of the cards, per device; «Für alle Geräte übernehmen»
#   stores it on MoveEye (CFG qs_layout: order, hidden, favs, cards, chide) as the default for devices without an own one -
#   the earlier «Anpassen» arrangement (order / hidden) is that default. The small simulator tile only when the
#   «Simulator-Steuerung» is not shown; «Kalibrieren» without a pan / tilt head under «… mehr»; «Grösse» (UI scale 60–160 %,
#   one CSS variable --lv-ui, CSS zoom on everything except the picture). Window: part 581. Translations: part 627.
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
body.lv-port:not(.videoonly) #video{width:100%;height:auto;aspect-ratio:auto 16/9;max-height:var(--lv-ph,60vh);min-height:0;object-fit:contain}   /* 2.98.31: no picture yet = 16:9 black box, not a 0 px strip */
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
/* 3.16 (Daniel 31.10.2026): simulation (body.sim-on = CFG sim_on, the source of the stripe) - no speed, ⇆, 🚜, centre, calibrate, waypoints */
body.sim-on #ctl-side{display:none!important}
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
body.lv-edit.lv-port main>section{padding-bottom:calc(var(--lv-ui,1) * 210px)!important}
#lv-setup .btns{margin-top:8px}
/* 2.98.29: the small simulator tile only when the «Simulator-Steuerung» is not shown (no second copy of the controls) */
body.lv #lv-side>#simtile.lvdup{display:none!important}
/* hidden quick switches (per device / for all devices): gone, in the edit mode dimmed */
body.lv:not(.lv-edit) #qsw>button.lvqh{display:none!important}
body.lv-edit #qsw>button.lvqh{opacity:.4}
body.lv-edit #qsw>button.lvqh:not(#lv-more)::after{content:"✕"!important;color:var(--red,#e5484d)!important}
/* the list of the quick switches (Ansicht panel and edit mode) */
.lvqs-row{display:flex;align-items:center;gap:6px;padding:3px 0}
.lvqs-row>span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lvqs-row.off>span{opacity:.5;text-decoration:line-through}
.lvqs-row button{padding:3px 8px;font-size:12px;min-height:0;line-height:1.3}
.lvqs-row button.st{width:32px;padding:3px 0;font-size:15px}
.lvqs-row button.st.on{color:var(--yel,#f5c518)}
#lv-qsed{margin-top:10px;padding:8px 10px;border:1px dashed var(--acc);border-radius:10px;max-height:46vh;overflow-y:auto}
#lv-qsed h4{margin:0 0 4px;font-size:12px;color:var(--mut)}
#lv-menu .lvsz{display:flex;align-items:center;gap:8px}#lv-menu .lvsz input{flex:1}#lv-menu .lvsz b{min-width:44px;text-align:right;font-size:13px}
/* 2.98.29: «Grösse» = one factor for text, buttons, tiles and joystick (not the picture: it always fits) */
body.lv:not(.videoonly) header,body.lv #lv-side,body.lv #lv-main>:not(#vcard),body.lv #lv-tools,#lv-menu,#lv-editbar{zoom:var(--lv-ui,1)}
body.lv #lv-joy{zoom:var(--lv-uij,1)}   /* the stick in the picture: not bigger than 115 % (it would cover the picture) */
body.lv #vcard>:not(.vwrap){zoom:var(--lv-ui,1)}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*LVDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  try { const D = /*LVDE2*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}   // 2.98.29 (627)
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const KEY = "mw-live-view";                          // per browser (this phone / PC) - never sent to the device
  // favs / qorder / qhide (quick switches) and order / hide (cards): null = this device has no own arrangement -> the one
  // «for all devices» on MoveEye (cfg.qs_layout), else the standard. ui = «Grösse» ("auto" or 60 … 160 %)
  const DEF = {layout: "auto", size: 60, ui: "auto", joy: "auto", ov: "auto", favs: null, qorder: null, qhide: null, order: null, more: false, preset: "", hide: null};
  const DEFFAV = ["rec", "photo", "track", "patrol", "white", "ir", "listen", "therm"];
  const DEFORDER = ["walktest", "controls", "whatwas", "simtile", "lvsetup"];   // Daniel: picture → simulator → walk test → the rest
  let V = Object.assign({}, DEF);
  try { Object.assign(V, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) {}
  ["hide", "favs", "qorder", "qhide", "order"].forEach(k => { V[k] = Array.isArray(V[k]) ? V[k].filter(x => typeof x === "string") : null; });
  if (V.favs && !V.qorder) V.qorder = V.favs.slice();    // 2.98.28 kept the order of the favourites: it becomes the order of the switches
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(V)); } catch (e) {} };
  // ---- the arrangement «for all devices» (on MoveEye) and the effective one of this device ----
  const SH = () => { const j = (typeof QSJ !== "undefined" && QSJ) || {}; return (j.cfg && j.cfg.qs_layout) || {}; };
  const has = a => Array.isArray(a) && a.length > 0;
  const qhideL = () => V.qhide || (Array.isArray(SH().hidden) ? SH().hidden : []);
  const hideL = () => V.hide || (Array.isArray(SH().chide) ? SH().chide : ["lvsetup"]);
  const corder = () => V.order || (has(SH().cards) ? SH().cards : null);
  const own = () => ["favs", "qorder", "qhide", "order", "hide"].some(k => V[k] !== null);
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
  if (firstRun && typeof HIDDEN !== "undefined") ["controls", "walktest", "simctl", "whatwas", "simtile"].forEach(k => { if (HIDDEN.has(k) && !hideL().includes(k)) V.hide = hideL().concat([k]); });
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
  // ---- «Kalibrieren» needs no pan / tilt head (it learns the picture again): without a head it is a quick switch behind «… more» ----
  try {
    if (typeof QS !== "undefined" && Array.isArray(QS) && !QS.some(q => q.id === "recal"))
      QS.push({id: "recal", ic: "↻", lb: "Calibrate", tip: "Learn the picture again (after moving the camera)", on: () => false, ok: () => !lvHead(),
        go: () => { if (typeof act === "function") act("recalibrate"); if (typeof toast === "function") toast("↻ " + T("Recalibrating - keep the picture empty for a few seconds")); return Promise.resolve({ok: true}); }});
  } catch (e) {}
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
      const co = corder() || [], ord = co.concat(DEFORDER.filter(k => !co.includes(k)));
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
  function uiScale() {                                 // «Grösse»: own choice, or automatic (a big screen a bit bigger)
    const n = +V.ui; if (V.ui !== "auto" && n >= 60 && n <= 160) return n / 100;
    const w = innerWidth, h = innerHeight;
    return w >= 1800 && h >= 1000 ? 1.15 : w >= 1500 && h >= 860 ? 1.05 : 1;
  }
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
    const u = uiScale(); document.documentElement.style.setProperty("--lv-ui", String(u)); document.documentElement.style.setProperty("--lv-uij", String(Math.min(u, 1.15)));
    if (md === "land") {
      const W = main.clientWidth - 24, share = 0.5 + Math.max(0, Math.min(100, +V.size)) / 100 * 0.35;
      let side = Math.round(Math.max(260 * Math.min(u, 1.3), Math.min(Math.max(640, W * 0.45) * Math.max(1, u), (1 - share) * W * u)));
      side = Math.min(side, Math.round(W * 0.62));       // a big «Grösse» makes the cards column wider, the picture keeps at least 38 %
      const v = document.getElementById("video"), ar = (v && v.naturalWidth && v.naturalHeight) ? v.naturalWidth / v.naturalHeight : 16 / 9;
      const peek = simOn ? Math.round(54 * u) : 0, picH = H - 12 - 18 - peek, picW = picH * ar + 18;
      if (W - side - 12 > picW) side = Math.round(Math.min(Math.max(side, W - picW - 12), Math.max(side, W * Math.min(0.7, 0.55 * Math.max(1, u)))));   // picture limited by the height: the spare width goes to the cards
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
    if (typeof window.skOwns === "function" && window.skOwns()) { document.body.classList.remove("lv-ovon"); jc.remove(); return; }   // 549: Sim-Kompakt holds the sticks
    const st = document.getElementById("stick"), box = document.querySelector(".ctl-stick .stickbox");
    if (!st || !box || isVO()) return;                   // full screen: setVideoOnly / voStick own the stick
    const ov = head && (md === "mini" || (V.ov === "auto" ? md === "land" : V.ov === "on"));
    document.body.classList.toggle("lv-ovon", ov);
    if (ov && st.parentNode !== J) { J.appendChild(st); J.appendChild(jc); jWake(); }
    if (!ov && st.parentNode === J) { box.insertBefore(st, box.firstChild); jc.remove(); }
    if (!ov && st.parentNode !== J) jc.remove();
  }
  // ---- quick switches: favourites ★, order, hidden (one list; the favourites show in the order of the list) ----
  const qsIds = () => [...document.querySelectorAll("#qsw > button")].filter(b => b.id !== "lv-more" && !b.classList.contains("na")).map(b => b.id.replace(/^qs-/, ""));
  function qorder() {                                   // the order of this device, else the one for all devices, else the favourites first
    const o = V.qorder || (has(SH().order) ? SH().order : null);
    return o ? o.slice() : favs();
  }
  function favs() {
    const H = qhideL(), F = V.favs || (has(SH().favs) ? SH().favs : DEFFAV);
    const all = [...document.querySelectorAll("#qsw > button")].map(b => b.id.replace(/^qs-/, "")).filter(x => x !== "lv-more");
    return F.filter(id => !H.includes(id) && (!all.length || all.includes(id))).slice(0, 8);    // a switch of the window only (or gone) takes no place
  }
  window.lvQsLay = () => ({order: qorder(), hidden: []});     // 530 qsArrange(): the order of this device; hidden ones get the class lvqh
  function reQs() { try { if (typeof QSJ !== "undefined" && QSJ && typeof qsPaint === "function") qsPaint(QSJ); } catch (e) {} paintFavs(); }
  function paintFavs() {
    const q = document.getElementById("qsw"); if (!q) return;
    const F = favs(), H = qhideL();
    q.querySelectorAll(":scope > button").forEach(b => {
      if (b.id === "lv-more") return;
      const id = b.id.replace(/^qs-/, "");
      b.classList.toggle("lvfav", F.includes(id)); b.classList.toggle("lvqh", H.includes(id)); b.style.setProperty("--o", 0);
    });
    let m = document.getElementById("lv-more");
    if (!m || m.parentNode !== q) { m = E("button", "sec"); m.type = "button"; m.id = "lv-more"; m.append(E("span", "", "…"), E("small", "", ""));
      m.onclick = e => { e.stopPropagation(); V.more = !V.more; save(); paintFavs(); }; q.appendChild(m); }
    q.classList.toggle("lvopen", !!V.more || document.body.classList.contains("lv-edit"));
    const sm = m.querySelector("small"), tx = T(q.classList.contains("lvopen") ? "less" : "more");
    if (sm.textContent !== tx) sm.textContent = tx;
    m.title = T(q.classList.contains("lvopen") ? "Show only the favourites" : "Show all quick switches");
  }
  function setFav(id, on) {
    const F = favs(), i = F.indexOf(id);
    if (on && i < 0) { if (F.length >= 8) { if (typeof toast === "function") toast("★ " + T("At most 8 favourites")); return false; } F.push(id); if (qhideL().includes(id)) setQHide(id, false); }
    if (!on && i >= 0) F.splice(i, 1);
    V.favs = F; V.preset = ""; save(); return true;
  }
  function setQHide(id, hide) {
    const H = new Set(qhideL()); if (hide) H.add(id); else H.delete(id); V.qhide = [...H];
    if (hide && favs().includes(id)) V.favs = favs().filter(x => x !== id);
    V.preset = ""; save();
  }
  function qMove(id, d) {                               // ▲ ▼ in the list of the available switches (the others keep their place)
    const vis = qsIds(), L = qorder(); vis.forEach(x => { if (!L.includes(x)) L.push(x); });
    const order = L.filter(x => vis.includes(x)), i = order.indexOf(id), j = i + d; if (i < 0 || j < 0 || j >= order.length) return;
    const a = L.indexOf(order[i]), b = L.indexOf(order[j]); [L[a], L[b]] = [L[b], L[a]];
    V.qorder = L; V.preset = ""; save(); reQs();
  }
  function qsRows(box, after) {                         // the list ★ name ▲ ▼ ✕ - the same in the Ansicht panel and in the edit mode
    box.textContent = "";
    const F = favs(), H = qhideL(), ids = qsIds();
    const name = id => { const b = document.getElementById("qs-" + id); return b ? ((b.querySelector("span") || {}).textContent || "") + " " + ((b.querySelector("small") || {}).textContent || "") : id; };
    ids.forEach((id, i) => {
      const row = E("div", "lvqs-row" + (H.includes(id) ? " off" : ""));
      const mk = (txt, tip, fn, cls) => { const b = E("button", "sec" + (cls ? " " + cls : ""), txt); b.type = "button"; b.title = T(tip);
        b.onclick = e => { e.preventDefault(); e.stopPropagation(); fn(); paintFavs(); qsRows(box, after); if (after) after(); }; row.appendChild(b); return b; };
      const st = mk(F.includes(id) ? "★" : "☆", "Favourite (shown without «… more»)", () => setFav(id, !F.includes(id)), "st" + (F.includes(id) ? " on" : ""));
      st.disabled = H.includes(id) || (!F.includes(id) && F.length >= 8);
      row.appendChild(E("span", "", name(id)));
      mk("▲", "Up", () => qMove(id, -1)).disabled = i === 0;
      mk("▼", "Down", () => qMove(id, 1)).disabled = i === ids.length - 1;
      mk(H.includes(id) ? "👁" : "✕", "Hide / show", () => setQHide(id, !H.includes(id)));
      box.appendChild(row);
    });
  }
  // edit mode: a tap on a quick switch makes it a favourite (★) instead of switching
  document.addEventListener("click", e => {
    if (!document.body.classList.contains("lv-edit")) return;
    const b = e.target.closest && e.target.closest("#qsw > button"); if (!b || b.id === "lv-more" || b.classList.contains("qs-edit")) return;
    e.preventDefault(); e.stopPropagation();
    const id = b.id.replace(/^qs-/, "");
    setFav(id, !favs().includes(id)); paintFavs(); const qe = document.getElementById("lv-qsed"); if (qe) qsEdBuild(qe);
  }, true);
  document.addEventListener("pointerdown", e => {          // the talk tile listens to pointerdown: no talking in the edit mode
    if (document.body.classList.contains("lv-edit") && e.target.closest && e.target.closest("#qsw > button[data-talk]")) { e.stopPropagation(); e.preventDefault(); }
  }, true);
  // ---- cards: hide / show, move (per device; «Für alle Geräte übernehmen» = the default on MoveEye) ----
  function cards() { return [...S.children].filter(x => keyOf(x) && x.id !== "mbtns2"); }
  const labelOf = x => T(x.dataset.vlabel || keyOf(x));
  const isHid = k => hideL().includes(k);
  function setHidden(k, hide) {
    const H = new Set(hideL()); if (hide) H.add(k); else H.delete(k); V.hide = [...H]; save(); paintHidden();
  }
  function simDup() {                                   // the «Simulator-Steuerung» is shown: the small tile would be a second copy
    const sw = document.getElementById("lv-simw");
    return !!(sw && !sw.hidden && !isHid("simctl"));
  }
  function paintHidden() {
    [...cards(), document.getElementById("lv-sim")].forEach(x => { if (x) x.classList.toggle("lvh", isHid(keyOf(x))); });
    const st = document.getElementById("simtile"); if (st) st.classList.toggle("lvdup", simDup());
  }
  function move(x, d) {
    const L = cards().filter(c => !c.classList.contains("lvdup")), i = L.indexOf(x), j = i + d; if (i < 0 || j < 0 || j >= L.length) return;
    [L[i], L[j]] = [L[j], L[i]]; const keep = (corder() || []).filter(k => !L.some(c => keyOf(c) === k));
    V.order = L.map(keyOf).concat(keep); V.preset = ""; save(); arrange(); editTools(); x.scrollIntoView({block: "nearest"});
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
    const qe = document.getElementById("lv-qsed"), q = document.getElementById("qsw");
    if (q && (!qe || qe.previousElementSibling !== q)) { const n = qe || E("div"); n.id = "lv-qsed"; q.after(n); qsEdBuild(n); }
  }
  function qsEdBuild(n) {
    n.textContent = ""; n.appendChild(E("h4", "", "⚡ " + T("Quick switches") + " – " + T("★ = favourite (max. 8), ▲ ▼ = order, ✕ = hide")));
    const L = E("div"); n.appendChild(L); qsRows(L);
  }
  // ---- «Für alle Geräte übernehmen»: this arrangement becomes the default on MoveEye ----
  async function shareAll() {
    if (!confirm(T("Use this arrangement (favourites, order, hidden switches and cards) for all devices that have no own arrangement?"))) return;
    const vis = qsIds(), qo = qorder(); vis.forEach(x => { if (!qo.includes(x)) qo.push(x); });
    const co = cards().map(keyOf).concat(["simctl"]);
    const body = {order: qo, hidden: qhideL(), favs: favs(), cards: co, chide: hideL()};
    let r; try { r = await post("/api/qs", body); } catch (e) { r = {ok: false, error: String(e)}; }
    if (!r || !r.ok) { if (typeof toast === "function") toast("⚠ " + ((r && r.error) || "error")); return; }
    if (typeof QSJ !== "undefined" && QSJ && QSJ.cfg) QSJ.cfg.qs_layout = r.qs_layout;
    ["favs", "qorder", "qhide", "order", "hide"].forEach(k => { V[k] = null; }); save();    // this device follows the default from now on
    if (typeof toast === "function") toast("✓ " + T("Saved on MoveEye for all devices"));
    apply(); reQs();
  }
  async function shareReset() {
    if (!confirm(T("Delete the arrangement for all devices? Devices without an own arrangement get the standard again."))) return;
    const r = await post("/api/qs", {reset: true});
    if (r && r.ok && typeof QSJ !== "undefined" && QSJ && QSJ.cfg) QSJ.cfg.qs_layout = r.qs_layout;
    if (typeof toast === "function") toast(r && r.ok ? "✓ " + T("Standard") : "⚠ " + ((r && r.error) || "error"));
    apply(); reQs(); if (!MN.hidden) menuBuild();
  }
  function edit(on) {
    document.body.classList.toggle("lv-edit", on);
    document.querySelectorAll(".lv-et").forEach(x => x.remove());
    const qe = document.getElementById("lv-qsed"); if (qe && !on) qe.remove();
    let bar = document.getElementById("lv-editbar");
    if (on) {
      menuClose();
      const cc = document.querySelector('#lv-side > [data-view="controls"]'); if (cc && cc.tagName === "DETAILS") cc.open = true;
      if (!bar) {
        bar = E("div"); bar.id = "lv-editbar";
        bar.appendChild(E("span", "", "✏️ " + T("Edit: cards ▲ ▼ move, ✕ hides (👁 shows again). Quick switches: tap = favourite ★ (max. 8), the list below them = order and hide. Stored on this device.")));
        const a = E("button", "sec", "📲 " + T("Use for all devices")); a.type = "button"; a.title = T("Store this arrangement on MoveEye as the default for devices without an own arrangement"); a.onclick = () => shareAll();
        const r = E("button", "sec", T("Reset")); r.type = "button"; r.onclick = () => { if (confirm(T("Back to the standard view of the live page?"))) reset(); };
        const d = E("button", "", T("Finish")); d.type = "button"; d.onclick = () => edit(false);
        bar.append(a, r, d); document.body.appendChild(bar);
      }
      editTools();
      setTimeout(() => { const c = document.getElementById("lv-side"); if (c && mode() === "port") c.scrollIntoView({behavior: "smooth", block: "start"}); }, 50);
    } else if (bar) bar.remove();
    paintFavs();
  }
  window.lvEdit = edit;
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
  function reset() {                                    // this device: back to the arrangement for all devices (or the standard)
    const keep = {ui: V.ui}; V = Object.assign({}, DEF, keep); save(); paintHidden();
    edit(false); apply(); reQs();
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
    const top = MN.scrollTop;
    MN.textContent = "";
    const hd = E("div", "lvhead"); hd.appendChild(E("b", "", "◫ " + T("View of the live page")));
    const x = E("button", "sec", "✕"); x.type = "button"; x.title = T("Close"); x.onclick = e => { e.stopPropagation(); menuClose(); }; hd.appendChild(x); MN.appendChild(hd);
    MN.appendChild(E("h3", "", T("Ready-made views")));
    const pr = E("div", "lvpre");
    Object.entries(PRESETS).forEach(([k, P]) => { const b = E("button", "sec" + (V.preset === k ? " on" : "")); b.type = "button";
      b.append(E("span", "", P.ic + " " + T(P.lb)), E("small", "", T(P.d)));
      b.onclick = e => { e.stopPropagation(); preset(k); menuBuild(); }; pr.appendChild(b); });
    MN.appendChild(pr);
    if (typeof window.pvMenu === "function") try { window.pvMenu(MN, E, T); } catch (e) {}     // 538: «Controller-Ansicht»
    if (typeof window.skMenu === "function") try { window.skMenu(MN, E, T); } catch (e) {}     // 549: «Sim-Kompakt»
    MN.appendChild(E("h3", "", T("Layout")));
    MN.appendChild(seg([["auto", "Automatic"], ["port", "Portrait"], ["land", "Landscape"], ["mini", "Picture only"]], V.layout, v => { V.layout = v; }));
    const md = mode();
    MN.appendChild(E("div", "mut", T("Now") + ": " + T({land: "picture left, cards right", port: "picture on top, cards below", mini: "only the picture (☰ = cards)"}[md])));
    MN.appendChild(E("h3", "", T("Picture size")));
    const r = E("input"); r.type = "range"; r.min = 0; r.max = 100; r.step = 5; r.value = V.size;
    r.oninput = () => { V.size = +r.value; V.preset = ""; save(); fit(); };
    MN.appendChild(r);
    MN.appendChild(E("div", "mut", T(md === "land" ? "Landscape: how wide the picture is next to the cards (it never gets higher than the window)." : "Portrait: how high the picture may be.")));
    // «Grösse»: text, buttons, tiles and joystick together (like a resolution); the picture always fits
    MN.appendChild(E("h3", "", T("Size of text and buttons")));
    const sz = E("div", "lvsz"), sr = E("input"), sv = E("b");
    const auto = V.ui === "auto";
    sr.type = "range"; sr.min = 60; sr.max = 160; sr.step = 10; sr.value = auto ? Math.round(uiScale() * 100 / 10) * 10 : +V.ui;
    sv.textContent = auto ? T("Automatic") : V.ui + " %";
    sr.oninput = () => { sv.textContent = sr.value + " %"; };
    sr.onchange = () => { V.ui = +sr.value; save(); fit(); apply(); menuBuild(); };
    const sa = E("button", "sec" + (auto ? " on" : ""), T("Automatic")); sa.type = "button";
    sa.onclick = e => { e.stopPropagation(); V.ui = "auto"; save(); fit(); apply(); menuBuild(); };
    sz.append(sr, sv); MN.appendChild(sz);
    const s2 = E("div", "lvseg"); [70, 100, 130].forEach(n => { const b = E("button", "sec" + (+V.ui === n ? " on" : ""), n + " %"); b.type = "button";
      b.onclick = e => { e.stopPropagation(); V.ui = n; save(); fit(); apply(); menuBuild(); }; s2.appendChild(b); });
    s2.insertBefore(sa, s2.firstChild); MN.appendChild(s2);
    MN.appendChild(E("div", "mut", T("Like a resolution: everything except the picture gets smaller or bigger (only on this device).")));
    MN.appendChild(E("h3", "", T("Joystick")));
    MN.appendChild(seg([["auto", "Automatic"], ["on", "Always"], ["off", "Never"]], V.joy, v => { V.joy = v; }));
    const j = J_(), hs = j.state ? (lvHead() ? "pan / tilt head found" : "no pan / tilt head found") : "";
    if (hs && V.joy === "auto") MN.appendChild(E("div", "mut", T("Automatic") + ": " + T(hs)));
    MN.appendChild(seg([["auto", "In the picture in landscape"], ["on", "In the picture"], ["off", "In the controls"]], V.ov, v => { V.ov = v; }));
    MN.appendChild(E("h3", "", T("Quick switches") + " · " + T("Favourite buttons (4–8)")));
    const ql = E("div"); MN.appendChild(ql); qsRows(ql);
    MN.appendChild(E("div", "mut", T("★ = always visible, the others behind «… more». ✕ hides a switch on this device.")));
    MN.appendChild(E("h3", "", T("Cards")));
    const sw = document.getElementById("lv-sim");
    const list = cards().filter(c => !c.classList.contains("lvdup")).concat(sw && !document.getElementById("lv-simw").hidden ? [sw] : []);
    list.forEach(c => { const k = keyOf(c); const row = E("label", "lvrow"), cb = E("input"); cb.type = "checkbox";
      cb.checked = !isHid(k);
      cb.onchange = () => { setHidden(k, !cb.checked); V.preset = ""; save(); fit(); menuBuild(); };
      row.append(cb, E("span", "", labelOf(c))); MN.appendChild(row); });
    if (simDup()) MN.appendChild(E("div", "mut", T("The small simulator tile only shows when the «Simulator control» is hidden.")));
    const ft = E("div", "lvfoot");
    const eb = E("button", "sec", "✏️ " + T("Edit")); eb.type = "button"; eb.onclick = e => { e.stopPropagation(); edit(true); };
    const rb = E("button", "sec", T("Reset")); rb.type = "button"; rb.onclick = e => { e.stopPropagation(); if (confirm(T("Back to the standard view of the live page?"))) { reset(); menuBuild(); } };
    ft.append(eb, rb); MN.appendChild(ft);
    const f2 = E("div", "lvfoot");
    const ab = E("button", "sec", "📲 " + T("Use for all devices")); ab.type = "button"; ab.title = T("Store this arrangement on MoveEye as the default for devices without an own arrangement");
    ab.onclick = e => { e.stopPropagation(); shareAll().then(() => { if (!MN.hidden) menuBuild(); }); };
    f2.appendChild(ab);
    const shd = SH(), shOn = has(shd.order) || has(shd.hidden) || has(shd.favs) || has(shd.cards) || Array.isArray(shd.chide);
    if (shOn) { const xb = E("button", "sec", "🗑 " + T("Default for all")); xb.type = "button"; xb.title = T("Delete the arrangement for all devices");
      xb.onclick = e => { e.stopPropagation(); shareReset(); }; f2.appendChild(xb); }
    MN.appendChild(f2);
    MN.appendChild(E("div", "mut", T(own() ? "This device has its own arrangement (only in this browser). «Reset» = back to the arrangement for all devices."
      : shOn ? "This device uses the arrangement for all devices (stored on MoveEye). A change makes it its own." : "Stored only in this browser (this phone / PC).")));
    MN.scrollTop = top;
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
    const sh = JSON.stringify(SH());
    const sig = [lvHead(), sw && sw.hidden, document.getElementById("qsw") && document.getElementById("qsw").childElementCount, typeof LANG !== "undefined" && LANG, sh].join("|");
    paintFavs();
    if (sig !== lastSig) { const re = lastSig && lastSig.split("|").pop() !== sh; lastSig = sig; apply(); if (re && !own()) reQs(); }
  }, 1000);
  apply(); setTimeout(apply, 600); setTimeout(apply, 2000);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", LIVE_VIEW_JS + "</body>", 1)
WEB_UI_LOCAL.add("mw-live-view")                         # per device: the layout of the phone is not the one of the PC (not copied to the Pi)
WEB_UI_LOCAL.add("mw-hidden")                            # aufr: the ☰ menu (fields shown / hidden) per device too - one rule for «hide» on every page
