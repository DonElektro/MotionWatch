#@ MoveEye – Teil 639zzzzx: Unterseiten als Fenster über der Seite (Besitzer 15.11.2026) – Von unten / Mitte / Von der Seite oder «Ganze Seite» wie bisher (Einstellungen → Darstellung & Sprache → Unterseiten, pro Gerät, ab Werk «Mitte»); gilt für Einstellungen, Schutz, Verlauf und Mehr, Live bleibt. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheide des Besitzers (15.11.2026):
#   - Stil wählbar: «Von unten» (Blatt mit Griff, oben bleibt die Seite sichtbar), «Mitte» (Fenster, ringsum die Seite), «Von der
#     Seite» (von rechts, links ein Streifen der Seite) und «Ganze Seite» (wie bisher). Ab Werk «Mitte». Pro Gerät (mw-sheet,
#     WEB_UI_LOCAL): auf dem Handy passt anderes als am PC.
#   - Überall: Einstellungen (+ Kameras), Schutz, Verlauf und Mehr. Live bleibt unverändert (auch seine Zeilen), Simulator-Seite
#     ebenso (der 3D-Simulator bekommt die Wahl später).
#   - Schliessen: ✕, Tipp auf den Hintergrund, Esc, Zurück (Verlauf des Browsers). Wischen nur am Griff / an der Titelzeile:
#     nach unten (Von unten, Mitte), nach rechts (Von der Seite).
# Zwei Arten Unterseiten:
#   1. Teil 639zzzg (Einstellungen, Schutz, Verlauf): die Karte wandert schon heute nach #ms-page – hier wird #ms-page selbst zum
#      Fenster (MWFX.show / MWFX.hide), #s=… und Zurück bleiben, ein tabOpen ersetzt den Inhalt des offenen Fensters.
#   2. Mehr (eigene Seiten wie /radio, /morse, /karte): ein Rahmen (iframe) mit ?fenster=1 im Fenster; Kopf, Reiter und «‹ Mehr»
#      der Seite im Rahmen sind ausgeblendet. Adresse #f=/radio, Zurück schliesst. Links, die die Seite verlassen, öffnen in der
#      Hauptseite (auch ein tabOpen / location.href der Seite im Rahmen). /radio direkt aufgerufen = ganze Seite wie bisher.
#      Radio (639zzzzd, mwRadioHost): der Spieler läuft in der Hauptseite (mwRadioP), der Rahmen mit /radio zeigt ihn nur an.
#      📻 im Kopf und jeder Link auf /radio öffnet auf jeder Seite das Radio-Fenster (bei «Ganze Seite»: über den ganzen
#      Bildschirm). Spielt das Radio (mwRadioP.S.on), lädt die Hauptseite nicht neu: jeder andere Link öffnet seine Seite als
#      Rahmen über den ganzen Bildschirm mit eigenem Kopf (#p=…, Zurück schliesst). Spielt im Rahmen sonst noch Ton (<audio> /
#      <video>), bleibt er beim Schliessen unsichtbar stehen und kommt beim nächsten Öffnen derselben Seite unverändert zurück.
# Fokus bleibt im Fenster (Tab), danach zurück auf die Zeile; die Seite dahinter scrollt nicht mit; ohne Bewegung bei
# «Bewegung reduzieren» des Systems. Pi-Fenster (Tk): nicht betroffen (eigene Ansicht).
# ----------------------------------------------------------------------------
WEB_UI_LOCAL.add("mw-sheet")                                   # per device: a phone may want «From below», the PC «Middle»

UF_CSS = r"""<style id="fx-css">
/* 639zzzzx: sub-pages as a window over the page (bottom sheet / middle / side panel) */
html.fx-lock,html.fx-lock>body{overflow:hidden!important;overscroll-behavior:none}
#fx-dim{position:fixed;inset:0;z-index:236;background:rgba(0,0,0,.45);animation:fx-fade .2s ease-out;-webkit-tap-highlight-color:transparent}
#fx-dim.fx-out{animation:fx-fade-out .2s ease-in forwards}
.fx-win{position:fixed!important;z-index:237;display:block!important;margin:0!important;box-sizing:border-box;overflow:auto;overscroll-behavior:contain;
  -webkit-overflow-scrolling:touch;background:var(--bg,#0a0e14);color:var(--txt);border:1px solid var(--line);box-shadow:0 12px 48px rgba(0,0,0,.5);
  padding:0 14px calc(14px + env(safe-area-inset-bottom,0px));outline:none}
.fx-win.fx-bottom{left:max(0px,calc(50% - 380px));right:max(0px,calc(50% - 380px));bottom:0;top:max(64px,calc(env(safe-area-inset-top,0px) + 56px),11vh);
  border-radius:20px 20px 0 0;border-bottom:0;animation:fx-up .26s cubic-bezier(.2,.8,.2,1)}
.fx-win.fx-mid{left:max(14px,calc(50% - 380px));right:max(14px,calc(50% - 380px));top:max(72px,calc(env(safe-area-inset-top,0px) + 56px),10vh);
  bottom:max(40px,calc(env(safe-area-inset-bottom,0px) + 24px),7vh);border-radius:22px;padding-bottom:14px;animation:fx-pop .22s ease-out}
.fx-win.fx-side{top:0;bottom:0;right:0;left:max(60px,calc(100% - 560px));border-radius:20px 0 0 20px;border-right:0;animation:fx-left .26s cubic-bezier(.2,.8,.2,1)}
.fx-win.fx-bottom.fx-out{animation:fx-down-out .2s ease-in forwards}.fx-win.fx-mid.fx-out{animation:fx-pop-out .18s ease-in forwards}
.fx-win.fx-side.fx-out{animation:fx-right-out .2s ease-in forwards}
.fx-win.fx-full{inset:0;border:0;border-radius:0;box-shadow:none;animation:fx-fade .15s ease-out}.fx-win.fx-full.fx-out{animation:fx-fade-out .15s ease-in forwards}
.fx-win.fx-full>.fx-bar{padding-top:max(8px,env(safe-area-inset-top,0px))}.fx-win.fx-drag{animation:none!important;transition:none!important}
.fx-win.fx-back{transition:transform .2s ease-out}
@keyframes fx-fade{from{opacity:0}}@keyframes fx-fade-out{to{opacity:0}}
@keyframes fx-up{from{transform:translateY(100%)}}@keyframes fx-down-out{to{transform:translateY(100%)}}
@keyframes fx-pop{from{opacity:0;transform:scale(.96)}}@keyframes fx-pop-out{to{opacity:0;transform:translateY(24px) scale(.97)}}
@keyframes fx-left{from{transform:translateX(100%)}}@keyframes fx-right-out{to{transform:translateX(100%)}}
@media(prefers-reduced-motion:reduce){#fx-dim,.fx-win,.fx-win.fx-out,#fx-dim.fx-out{animation:none!important;transition:none!important}}
/* the title row: grip (from below), title, ✕ - sticky on top; dragging here closes */
.fx-win>.fx-bar,.fx-win>#ms-bar{position:sticky;top:0;z-index:3;display:flex;align-items:center;gap:10px;margin:0 -14px 12px;padding:8px 8px 8px 16px;
  min-height:56px;box-sizing:border-box;background:inherit;border-bottom:1px solid var(--line);touch-action:none;cursor:grab;user-select:none;-webkit-user-select:none}
.fx-win.fx-bottom>.fx-bar,.fx-win.fx-bottom>#ms-bar{padding-top:20px}
.fx-win.fx-side>.fx-bar,.fx-win.fx-side>#ms-bar{padding-top:max(8px,env(safe-area-inset-top,0px))}
.fx-win .fx-grab{display:none}.fx-win.fx-bottom .fx-grab{display:block;position:absolute;top:7px;left:50%;width:42px;height:5px;margin-left:-21px;border-radius:3px;background:var(--mut);opacity:.55}
.fx-win>.fx-bar>b,.fx-win>#ms-bar>b{order:2;flex:1;min-width:0;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fx-win .fx-x{order:3;flex:none;width:44px;height:44px;min-width:44px;min-height:44px!important;padding:0!important;margin:0 0 0 auto;border-radius:50%;
  border:0;background:rgba(127,140,160,.18);color:var(--txt);font-size:18px;line-height:44px;box-shadow:none;cursor:pointer}
.fx-win .fx-x:hover{background:rgba(127,140,160,.3)}
/* a page in the window (Mehr): the frame fills it, the page inside scrolls */
.fx-win.fx-fr{display:flex!important;flex-direction:column;overflow:hidden;padding:0}.fx-win.fx-fr>.fx-bar{margin:0;flex:none}
.fx-win.fx-fr>iframe{flex:1;width:100%;min-height:0;border:0;display:block;background:var(--bg,#0a0e14);opacity:0;transition:opacity .12s}
.fx-win.fx-fr.fx-ok>iframe{opacity:1}
.fx-park{position:fixed!important;left:-200vw!important;top:0!important;width:320px!important;height:200px!important;visibility:hidden!important;pointer-events:none!important}
/* the choice in Einstellungen → Darstellung & Sprache → Unterseiten */
#fx-card h3{margin:0 0 .3rem}.fx-pick{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:.5rem 0}
.fx-pick button{display:flex;align-items:center;gap:10px;min-height:52px;padding:6px 12px;border-radius:12px;border:1px solid var(--line);background:var(--field);
  color:var(--txt);font:inherit;font-size:15px;font-weight:600;text-align:left;box-shadow:none;cursor:pointer}
.fx-pick button svg{width:22px;height:30px;flex:none}.fx-pick button[aria-checked="true"]{background:var(--acc);border-color:var(--acc);color:#fff}
</style>"""

UF_JS = r"""<script>
(function () {
  if (window.MWFX) return;
  let T = null; try { if (window !== window.top && window.top.MWFX && window.top.location.origin === location.origin) T = window.top; } catch (e) {}
  // inside a frame of the main page: «📻» / a link to /radio opens the radio window of the main page (its player keeps playing there)
  if (T) document.addEventListener("click", e => {
    const a = !e.defaultPrevented && !e.button && e.target.closest && e.target.closest("a[href]"); if (!a || (a.target && a.target !== "_self")) return;
    let u; try { u = new URL(a.href, location.href); } catch (_) { return; }
    if (u.origin === location.origin && u.pathname === "/radio" && location.pathname !== "/radio") { e.preventDefault(); T.MWFX.radio(a); }
  });
  if (T && /[?&]fenster=1/.test(location.search)) { window.MWFX = {frame: true, on: () => false}; return; }   // a sub-page in a window opens nothing of its own
  const TX = /*FXTX*/{};
  const B = document.body, D = document.documentElement;
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || D.lang || "de"; } catch (e) { return "de"; } };
  const tr = k => ((TX[L()] || {})[k]) || ((TX.en || {})[k]) || k;
  const lsg = (k, d) => { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } };
  const lss = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const MODES = ["full", "bottom", "mid", "side"], NAMES = {full: "Full page", bottom: "From below", mid: "Middle", side: "From the side"};
  const mode = () => { const v = lsg("mw-sheet", "mid"); return MODES.includes(v) ? v : "mid"; };
  // where: the tabs Schutz, Verlauf, Einstellungen, Mehr (Live and the simulator page stay as they are)
  const navHrefs = () => [...document.querySelectorAll("header nav.nav a[href], header nav.subnav a[href]")].map(a => new URL(a.href, location.href).pathname);
  const topTab = () => { const a = document.querySelector("header nav.nav a.on"); return a ? new URL(a.href, location.href).pathname : ""; };
  const here = () => ["/protect", "/recordings", "/settings", "/more"].includes(topTab());
  const on = () => here() && mode() !== "full";
  const still = () => { try { return matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; } };
  let dim = null, cur = null;                                  // cur = {win, o, ret, done, timer}
  // the style: the chosen one; «Full page» (only the radio while it plays, a page while the radio plays) = the whole screen
  function variant(w) { w.classList.remove("fx-bottom", "fx-mid", "fx-side", "fx-full"); w.classList.add("fx-" + (w.dataset.fxForce || mode())); }
  const radioOn = () => { try { const P = window.mwRadioP; return !!(P && P.S && P.S.on); } catch (e) { return false; } };
  const FOC = 'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),iframe,[tabindex]:not([tabindex="-1"]),summary';
  // ---- dialogs opened from a window lie above it (Web-Passwort #pwd-ov, «Neuer Benutzer», menus, pickers, toasts …): every overlay
  // of the page that appears while a window is open (a child of <body> or an overlay anywhere, fixed / absolute, visible, not there
  // when the window opened) gets 1000 + its z-index (inline, !important) - back when the window closes. One rule for all parts.
  const OVSEL = '[id$="-ov"],[class*="-ov"],[id$="-pop"],.pop,[role=dialog],[role=alertdialog],[role=menu],[role=listbox],[aria-modal=true],.mwt-ov,.g2m,.modal,dialog,#toast,.toast,'
    + '#viewer,#big,.tz-lb,.tz-drop,.pl-lb,.prt-wiz,#rs-ed,#langmenu,.sndpop,#lv-menu,#kw-menu,#v3-menu,.mwg-shot,#pv,.pvw.fs';   // (fixed layers of other parts)
  const DLG = '[id$="-ov"],[class*="-ov"],[role=dialog],[role=alertdialog],[aria-modal=true],.mwt-ov,.g2m,.modal,dialog,#gw';
  let base = new Set(), up = [], mo = null, raf = 0;
  const seen = el => { if (!el.getClientRects().length) return false; const cs = getComputedStyle(el);
    return (cs.position === "fixed" || cs.position === "absolute") && cs.display !== "none" && cs.visibility !== "hidden"; };
  const cands = () => new Set([...B.children, ...document.querySelectorAll(OVSEL)]);
  const mine = el => el === dim || el.closest(".fx-win,.fx-park,#fx-dim") || /^(SCRIPT|STYLE|LINK|TEMPLATE)$/.test(el.tagName);
  function lift() {
    raf = 0; if (!cur) return;
    cands().forEach(el => { if (el.dataset.fxUp != null || base.has(el) || mine(el) || !seen(el)) return;
      const z = parseInt(getComputedStyle(el).zIndex, 10) || 0; el.dataset.fxUp = el.style.getPropertyValue("z-index") || "-";
      el.style.setProperty("z-index", String(1000 + Math.max(0, z)), "important"); up.push(el); });
  }
  function watch() {
    base = new Set([...cands()].filter(el => !mine(el) && seen(el))); up = [];
    mo = new MutationObserver(() => { if (!raf) raf = requestAnimationFrame(lift); });
    mo.observe(B, {childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class", "hidden", "open"]});
  }
  function unwatch() {
    if (mo) mo.disconnect(); mo = null; if (raf) cancelAnimationFrame(raf); raf = 0;
    up.forEach(el => { const v = el.dataset.fxUp; delete el.dataset.fxUp; if (v === "-") el.style.removeProperty("z-index"); else el.style.setProperty("z-index", v); });
    up = []; base = new Set();
  }
  const dialog = () => !!document.querySelector(".mwt-ov,.g2m,#gw") || up.some(el => el.isConnected && el.matches(DLG) && seen(el));
  const overlay = t => !!(t && t.closest && t.closest("[data-fx-up]," + OVSEL + ",#g2-bub,#g2-pop,#g2-ov") && !t.closest(".fx-win"));
  function keys(e) {
    if (!cur) return;
    if (dialog() || overlay(e.target)) return;                // Esc / Tab belong to the dialog on top
    if (e.key === "Escape") { e.preventDefault(); cur.o.close(); return; }
    if (e.key !== "Tab") return;
    const f = [...cur.win.querySelectorAll(FOC)].filter(x => x.getClientRects().length && !x.closest("[hidden],#ms-hide"));
    if (!f.length) { e.preventDefault(); cur.win.focus(); return; }
    const a = document.activeElement, first = f[0], last = f[f.length - 1];
    if (!cur.win.contains(a)) { e.preventDefault(); first.focus(); }
    else if (e.shiftKey && (a === first || a === cur.win)) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && a === last) { e.preventDefault(); first.focus(); }
  }
  function focusIn(e) { if (cur && !cur.win.contains(e.target) && !overlay(e.target) && !dialog()) { try { (cur.x || cur.win).focus({preventScroll: true}); } catch (_) {} } }
  // drag the grip / the title row: down (from below, middle) or right (from the side) - far or fast enough = close
  function drag(w, bar) {
    if (bar.dataset.fxDrag) return; bar.dataset.fxDrag = "1"; let s = null;
    bar.addEventListener("pointerdown", e => {
      if (!cur || cur.win !== w || e.button || e.target.closest("button,a,input,select,textarea")) return;
      s = {x: e.clientX, y: e.clientY, t: Date.now(), d: 0, id: e.pointerId}; try { bar.setPointerCapture(e.pointerId); } catch (_) {}
    });
    bar.addEventListener("pointermove", e => {
      if (!s || e.pointerId !== s.id) return; const side = w.classList.contains("fx-side");
      const d = Math.max(0, side ? e.clientX - s.x : e.clientY - s.y); if (!s.d && d < 4) return;
      s.d = d; w.classList.add("fx-drag"); w.classList.remove("fx-back"); w.style.transform = side ? "translateX(" + d + "px)" : "translateY(" + d + "px)";
    });
    const end = e => { if (!s || (e && e.pointerId !== s.id)) return; const d = s.d, v = d / Math.max(1, Date.now() - s.t); s = null; w.classList.remove("fx-drag");
      if (d > 90 || (d > 30 && v > 0.6)) { if (cur && cur.win === w) cur.o.close(); return; }
      w.classList.add("fx-back"); w.style.transform = ""; setTimeout(() => w.classList.remove("fx-back"), 250); };
    bar.addEventListener("pointerup", end); bar.addEventListener("pointercancel", end); bar.addEventListener("lostpointercapture", () => end());
  }
  // o = {bar, x (close button), close(), ret (focus after)}
  function show(w, o) {
    if (cur && cur.win === w) { clearTimeout(cur.timer); if (cur.done) { cur.done = null; w.classList.remove("fx-out"); if (dim) dim.classList.remove("fx-out"); } cur.o = o; return; }
    if (cur) finish(true);
    if (!dim) { dim = E("div"); dim.id = "fx-dim"; dim.addEventListener("click", () => { if (cur) cur.o.close(); }); }
    dim.classList.remove("fx-out"); if (!o.solo) B.appendChild(dim); else dim.remove();   // (a whole page over it: no dim)
    w.classList.remove("fx-out", "fx-drag", "fx-back", "fx-park"); w.style.transform = ""; w.classList.add("fx-win"); variant(w);
    w.setAttribute("role", "dialog"); w.setAttribute("aria-modal", "true"); w.tabIndex = -1;
    const bar = o.bar; if (bar) { if (!bar.querySelector(".fx-grab")) bar.prepend(E("i", "fx-grab")); drag(w, bar);
      const t = bar.querySelector("b"); if (t) { if (!t.id) t.id = "fx-t-" + (w.id || "w"); w.setAttribute("aria-labelledby", t.id); } }
    const x = o.x; if (x) { if (x.dataset.fxTxt == null) x.dataset.fxTxt = x.textContent; x.textContent = "✕"; x.classList.add("fx-x"); x.title = tr("Close"); x.setAttribute("aria-label", tr("Close")); }
    cur = {win: w, o, x, ret: o.ret || document.activeElement, done: null, timer: 0};
    D.classList.add("fx-lock"); B.classList.add("fx-open");
    document.addEventListener("keydown", keys, true); document.addEventListener("focusin", focusIn); watch();
    setTimeout(() => { try { (x || w).focus({preventScroll: true}); } catch (_) {} }, 30);
  }
  function finish(quick) {
    if (!cur) return; const c = cur; cur = null; clearTimeout(c.timer);
    document.removeEventListener("keydown", keys, true); document.removeEventListener("focusin", focusIn); unwatch();
    const w = c.win; w.classList.remove("fx-win", "fx-out", "fx-bottom", "fx-mid", "fx-side", "fx-full", "fx-drag", "fx-back"); w.style.transform = "";
    w.removeAttribute("role"); w.removeAttribute("aria-modal"); w.removeAttribute("aria-labelledby");
    if (c.x) { c.x.textContent = c.x.dataset.fxTxt || c.x.textContent; delete c.x.dataset.fxTxt; c.x.classList.remove("fx-x"); c.x.removeAttribute("aria-label"); c.x.removeAttribute("title"); }
    if (dim) { dim.classList.remove("fx-out"); dim.remove(); }
    D.classList.remove("fx-lock"); B.classList.remove("fx-open");
    if (c.done) { const d = c.done; c.done = null; d(); }
    if (!quick && c.ret && c.ret.isConnected) { try { c.ret.focus({preventScroll: true}); } catch (_) {} }
  }
  // close with the animation; done() runs at the end (the part goes back to its place)
  function hide(w, done) {
    if (!cur || cur.win !== w) { if (done) done(); return; }
    cur.done = done || null;
    if (still() || !w.getClientRects().length) { finish(); return; }
    w.classList.add("fx-out"); if (dim) dim.classList.add("fx-out"); cur.timer = setTimeout(() => finish(), 210);
  }
  // ---- 2. a page of «Mehr» in the window: a frame -------------------------------------------------------------------------
  const FRAME_CSS = "header,#mwbar,.mwb-grip,#g2-ov,#g2-spot,#g2-bub,#ra-frame,.fx-hide{display:none!important}body{padding-top:0!important}main{margin-top:0!important;padding-top:10px!important}";
  const SKIP = /^\/(tv|k|g|p|x|na|l|game|spiele|api|static)\//;
  let fr = null, parked = null;                               // fr = {win, f, path, url, title}
  const clean = s => String(s || "").replace(/[^\p{L}\p{N}]+/gu, " ").trim().toLowerCase();
  function eligible(a) {
    if (!a || !a.href || (a.target && a.target !== "_self") || a.hasAttribute("download") || a.closest(".fx-win")) return null;
    let u; try { u = new URL(a.href, location.href); } catch (e) { return null; }
    if (u.origin !== location.origin || u.pathname === location.pathname || navHrefs().includes(u.pathname) || SKIP.test(u.pathname + "/")) return null;
    return u;
  }
  function frameHref(u, kind) { const v = new URL(u.href); if (kind !== "page") v.searchParams.set("fenster", "1"); v.hash = ""; return v.pathname + v.search; }
  function prep(w, f, title, path) {                          // inside the frame: no header / tabs / «‹ Mehr», the same title once
    let d; try { d = f.contentDocument; } catch (e) { return false; }
    if (!d || !d.documentElement || (f.contentWindow.location.href || "").startsWith("about:")) return false;
    if (d.documentElement.classList.contains("mw-fenster")) return true;
    d.documentElement.classList.add("mw-fenster");
    const s = d.createElement("style"); s.textContent = FRAME_CSS; (d.head || d.documentElement).appendChild(s);
    const tidy = () => {
      const nav = new Set(navHrefs());
      d.querySelectorAll("main a[href]").forEach(a => { try { if (/^\s*‹/.test(a.textContent) && nav.has(new URL(a.href, d.baseURI).pathname)) a.classList.add("fx-hide"); } catch (e) {} });
      const h = d.querySelector("main h1, main h2"); if (h && clean(h.textContent) && clean(h.textContent) === clean(title)) h.classList.add("fx-hide");
      w.classList.add("fx-ok");
    };
    if (d.readyState === "loading") d.addEventListener("DOMContentLoaded", tidy); else tidy();
    setTimeout(() => w.classList.add("fx-ok"), 1500);
    d.addEventListener("keydown", e => { if (e.key === "Escape" && cur && cur.win === w) { e.preventDefault(); cur.o.close(); } });
    d.addEventListener("click", e => {                         // a link that leaves the page: in the main page (the opener itself = close)
      if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey) return;
      const a = e.target.closest && e.target.closest("a[href]"); if (!a || (a.target && a.target !== "_self") || a.hasAttribute("download")) return;
      let u; try { u = new URL(a.href, d.baseURI); } catch (_) { return; }
      if (u.origin === location.origin && u.pathname === path) return;
      if (/^(javascript|mailto|tel|sms):/i.test(u.protocol)) return;
      e.preventDefault(); leave(u);
    });
    return true;
  }
  function leave(u) {
    if (u.origin === location.origin && u.pathname === location.pathname && !u.search) { closeFrame(); return; }
    if (fr) { const w = fr.win; finish(true); w.remove(); fr = null; }
    if (radioOn() && u.origin === location.origin) { openFrame(u, "", null, true, "page"); return; }   // no reload while the radio plays here
    location.href = u.href;
  }
  function playing(f) {                                       // (the radio itself plays in the main page: mwRadioHost, 639zzzzd)
    try { return [...f.contentDocument.querySelectorAll("audio,video")].some(m => !m.paused); } catch (e) { return false; }
  }
  // kind: "sub" (a page of «Mehr»), "radio" (📻 / a link to /radio, on every page), "page" (any other page while the radio plays:
  // the whole screen with its own header - the main page does not reload, so the radio plays on)
  function openFrame(u, title, ret, push, kind) {
    kind = kind || "sub"; const key = kind === "page" ? u.pathname + u.search : u.pathname;
    if (fr && fr.path === key) return;
    if (fr) { const o = fr; fr = null; finish(true); park(o); }
    let n = null;
    if (parked && parked.path === key) { n = parked; parked = null; n.win.classList.remove("fx-park"); n.win.id = "fx-frame"; }
    else {
      const w = E("div", "fx-fr"); w.id = "fx-frame"; const bar = E("div", "fx-bar"), t = E("b"), x = E("button", "sec");
      x.type = "button"; bar.append(t, x); const f = E("iframe"); f.title = title; f.setAttribute("allow", "autoplay; fullscreen; geolocation; clipboard-write");
      f.src = frameHref(u, kind); if (kind === "page") { w.classList.add("fx-page"); w.append(f); } else w.append(bar, f); B.appendChild(w);
      n = {win: w, f, bar, t, x, path: key, url: u.href, title, first: true, kind};
      f.addEventListener("load", () => {
        let p = null; try { p = f.contentWindow.location; } catch (e) {}
        if (n.kind === "page") { w.classList.add("fx-ok"); if (p && fr === n) { try { history.replaceState(history.state, "", "#p=" + encodeURIComponent(p.pathname + p.search)); } catch (e) {} } return; }
        if (p && n.first) { n.first = false; prep(w, f, n.title, n.path); return; }
        if (!p || p.pathname !== n.path || !/[?&]fenster=1/.test(p.search)) { if (fr === n) leave(new URL(p ? p.href : location.href)); return; }
        prep(w, f, n.title, n.path);
      });
      if (kind !== "page") { const poll = setInterval(() => { if (!w.isConnected || prep(w, f, n.title, n.path)) clearInterval(poll); }, 25);
        setTimeout(() => clearInterval(poll), 15000); }
    }
    n.t.textContent = title; n.title = title; n.x.onclick = () => closeFrame(); fr = n;
    if (kind === "page" || mode() === "full") n.win.dataset.fxForce = "full"; else delete n.win.dataset.fxForce;
    show(n.win, kind === "page" ? {close: () => closeFrame(), ret, solo: true} : {bar: n.bar, x: n.x, ret, close: () => closeFrame()});
    if (push) { const h = u.pathname + u.search; try { history.pushState({fx: h, k: kind}, "", (kind === "page" ? "#p=" : "#f=") + encodeURIComponent(h)); } catch (e) {} }
  }
  function park(n) {                                          // still playing: keep the page alive, out of sight
    if (playing(n.f)) { if (parked && parked !== n) parked.win.remove(); n.win.classList.add("fx-park"); n.win.id = "fx-parked"; parked = n; }
    else n.win.remove();
  }
  function closeFrame(fromHistory) {
    if (!fr) return;
    if (!fromHistory && history.state && history.state.fx) { history.back(); return; }
    const n = fr; fr = null;
    hide(n.win, () => park(n));
    if (/^#[fp]=/.test(location.hash)) { try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {} }
  }
  function rowTitle(a) {
    const b = a.querySelector("b"), i = a.querySelector(":scope > i");
    const t = (b ? b.textContent : a.textContent).trim().split("\n")[0].trim().slice(0, 60);
    const ic = i && !i.querySelector("svg") ? i.textContent.trim() : "";
    return {text: t, full: (ic && ic.length <= 4 ? ic + " " : "") + t};
  }
  const RADIO = "📻 Radio";
  function radio(a) { openFrame(new URL("/radio", location.href), RADIO, a || document.activeElement, true, "radio"); }
  document.addEventListener("click", e => {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest && e.target.closest("a[href]"); if (!a || a.closest(".fx-win") || (a.target && a.target !== "_self") || a.hasAttribute("download")) return;
    let u; try { u = new URL(a.href, location.href); } catch (_) { return; }
    if (u.origin !== location.origin || /^(javascript|mailto|tel|sms):/i.test(u.protocol)) return;
    // 📻 in the header / any link to the radio: its window (also on Live - a window over it, the page itself stays)
    if (u.pathname === "/radio" && location.pathname !== "/radio") { e.preventDefault(); radio(a); return; }
    if (on() && topTab() === "/more" && a.matches("main a.mi[href]") && eligible(a)) { e.preventDefault(); const t = rowTitle(a); openFrame(u, t.full, a, true); return; }
    // the radio plays in this page: no reload - the other page opens over it (whole screen, with its own header)
    if (radioOn() && (u.pathname !== location.pathname || u.search !== location.search) && !SKIP.test(u.pathname + "/")) { e.preventDefault(); openFrame(u, "", a, true, "page"); }
  });
  window.addEventListener("popstate", e => {
    const s = e.state && e.state.fx, k = (e.state && e.state.k) || "sub";
    if (s) { const u = new URL(s, location.href); const a = [...document.querySelectorAll("main a.mi[href]")].find(x => eligible(x) && eligible(x).pathname === u.pathname);
      if (k !== "sub" || on()) openFrame(u, k === "radio" ? RADIO : (a ? rowTitle(a).full : u.pathname.slice(1)), a, false, k); return; }
    if (fr) closeFrame(true);
  });
  function deep() {                                           // /more#f=/radio: the window over «Mehr»
    if (location.hash.startsWith("#p=")) { try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {} return; }   // (the radio stopped with the reload)
    const m = location.hash.match(/^#f=(.+)$/); if (!m) return;
    let u; try { u = new URL(decodeURIComponent(m[1]), location.href); } catch (e) { return; }
    const a = [...document.querySelectorAll("main a.mi[href]")].find(x => eligible(x) && eligible(x).pathname === u.pathname);
    if (u.pathname !== "/radio" && (!a || !on())) return;
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    if (u.pathname === "/radio") radio(a); else openFrame(u, rowTitle(a).full, a, true);
  }
  // ---- 3. the choice: Einstellungen → Darstellung & Sprache → «Unterseiten» (the card for the row of 639zzzg) -------------
  const ICON = {full: '<rect x="4.5" y="3.5" width="13" height="23" rx="1.5"/>', bottom: '<rect x="4.5" y="11" width="13" height="15.5" rx="2"/>',
                mid: '<rect x="5" y="8" width="12" height="14" rx="2"/>', side: '<rect x="9" y="3.5" width="8.5" height="23" rx="2"/>'};
  let card = null;
  function paintCard() {
    if (!card) return; const st = (el, v) => { if (el.textContent !== v) el.textContent = v; };
    st(card.querySelector("h3"), tr("Sub-pages")); st(card.querySelector("p"), tr("fx-note"));
    card.querySelectorAll(".fx-pick button").forEach(b => { const k = b.dataset.v, sel = k === mode() ? "true" : "false";
      if (b.getAttribute("aria-checked") !== sel) { b.setAttribute("aria-checked", sel); b.tabIndex = sel === "true" ? 0 : -1; } st(b.lastChild, tr(NAMES[k])); });
  }
  function set(v) {
    if (!MODES.includes(v)) return; lss("mw-sheet", v); paintCard();
    if (cur && v !== "full" && !cur.win.dataset.fxForce) variant(cur.win);   // the open window shows the new style at once (full page: next time)
  }
  function placeCard() {
    const S = document.getElementById("settings"); if (!S || topTab() !== "/settings") return;
    if (card) { if (!card.isConnected) S.appendChild(card); return; }   // (the settings page builds its groups anew: the card comes back)
    card = E("section", "card"); card.id = "fx-card"; const g = E("div", "fx-pick"); g.setAttribute("role", "radiogroup");
    MODES.forEach(k => { const b = E("button"); b.type = "button"; b.dataset.v = k; b.setAttribute("role", "radio");
      b.innerHTML = '<svg viewBox="0 0 22 30" aria-hidden="true"><rect x="2" y="1" width="18" height="28" rx="3" fill="none" stroke="currentColor" stroke-width="1.6"/>'
        + '<g fill="currentColor">' + ICON[k] + '</g></svg><span></span>'; b.onclick = () => set(k); g.appendChild(b); });
    g.addEventListener("keydown", e => { const i = MODES.indexOf(mode()), d = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[e.key]; if (!d) return;
      e.preventDefault(); const v = MODES[(i + d + MODES.length) % MODES.length]; set(v); g.querySelector('[data-v="' + v + '"]').focus(); });
    card.append(E("h3"), g, E("p", "mut")); S.appendChild(card); paintCard();
  }
  window.MWFX = {on, mode, set, label: () => tr(NAMES[mode()]), show, hide, finish, open: () => !!cur, frame: false, radio,
                 openFrame: (href, title) => { const u = new URL(href, location.href); openFrame(u, title || u.pathname.slice(1), document.activeElement, true); }};
  placeCard(); setTimeout(deep, 0);
  setInterval(() => { placeCard(); paintCard(); }, 1500);      // late #settings, another language
})();
</script>"""

UF_TX_JS = r"""{
"Close": [
"Close",
"Schliessen",
"Fermer",
"Chiudi",
"Serrar"
],
"Sub-pages": [
"Sub-pages",
"Unterseiten",
"Sous-pages",
"Sottopagine",
"Sutpaginas"
],
"Full page": [
"Full page",
"Ganze Seite",
"Page entière",
"Pagina intera",
"Pagina entira"
],
"From below": [
"From below",
"Von unten",
"Par le bas",
"Dal basso",
"Da sut"
],
"Middle": [
"Middle",
"Mitte",
"Au milieu",
"Al centro",
"Amez"
],
"From the side": [
"From the side",
"Von der Seite",
"Par le côté",
"Dal lato",
"Da la vart"
],
"fx-note": [
"How the pages of Settings, Protection, History and More open: over the page or as a full page. Live stays as it is. Close: ✕, tap beside the window, Esc or back; or drag the title row down (from the side: to the right).",
"So öffnen sich die Unterseiten von Einstellungen, Schutz, Verlauf und Mehr: über der Seite oder als ganze Seite. Live bleibt, wie es ist. Schliessen: ✕, neben das Fenster tippen, Esc oder Zurück; oder die Titelzeile nach unten ziehen (von der Seite: nach rechts).",
"Comment s’ouvrent les sous-pages de Réglages, Protection, Historique et Plus : par-dessus la page ou en page entière. Direct reste tel quel. Fermer : ✕, toucher à côté de la fenêtre, Échap ou retour ; ou tirer la ligne de titre vers le bas (par le côté : vers la droite).",
"Come si aprono le sottopagine di Impostazioni, Protezione, Cronologia e Altro: sopra la pagina o a pagina intera. Live resta com’è. Chiudere: ✕, toccare accanto alla finestra, Esc o indietro; oppure trascinare la riga del titolo in basso (dal lato: a destra).",
"Uschia s’avran las sutpaginas da Parameters, Protecziun, Cronologia e Dapli: sur la pagina u sco pagina entira. Live resta sco ch’el è. Serrar: ✕, tutgar sper la fanestra, Esc u enavos; u trair la lingia dal titel engiu (da la vart: a dretga)."
]
}"""   # key: [en, de, fr, it, rm] (one JSON literal: werkzeuge/bauen.py puts it into the data zip)
try:
    UF_TX = {k: tuple(v) for k, v in json.loads(UF_TX_JS).items()}
except ValueError:
    UF_TX = {}
for _k, _v in UF_TX.items():                                   # the same texts for tr() on the server side (the check of 395: fr / it / rm)
    if len(_v) == 5:
        DE.setdefault(_k, _v[1])
        for _i, _L in enumerate(("fr", "it", "rm")):
            TRX[_L].setdefault(_k, _v[_i + 2])


def uf_tx():
    return {L: {k: v[i] for k, v in UF_TX.items()} for i, L in enumerate(("en", "de", "fr", "it", "rm"))}


# the manual: one paragraph in «Tipps & Tricks» (HELP_PAGE de / en of 540, HELP_X fr / it / rm of 600) - one JSON literal (data zip)
UF_HELP_JS = r"""{
"de": "<p><b>🪟 Unterseiten als Fenster:</b> Tippst du in Einstellungen, Schutz, Verlauf oder Mehr auf eine Zeile, öffnet sich die Unterseite als Fenster über der Seite – die Seite bleibt dahinter sichtbar. Wie, wählst du in Einstellungen → Darstellung &amp; Sprache → Unterseiten: Von unten, Mitte (ab Werk), Von der Seite oder Ganze Seite (wie früher). Jedes Gerät merkt sich das selbst. Schliessen: ✕, neben das Fenster tippen, Esc oder Zurück; oder die Titelzeile nach unten ziehen (Von der Seite: nach rechts). Live bleibt, wie es ist. Ein Radio im Fenster spielt weiter, wenn du das Fenster schliesst.</p>",
"en": "<p><b>🪟 Sub-pages as a window:</b> tap a row in Settings, Protection, History or More and the sub-page opens as a window over the page – the page stays visible behind it. Choose how in Settings → Display &amp; language → Sub-pages: From below, Middle (default), From the side or Full page (as before). Every device remembers it by itself. Close: ✕, tap beside the window, Esc or back; or drag the title row down (From the side: to the right). Live stays as it is. A radio in the window keeps playing when you close the window.</p>",
"fr": "<p><b>🪟 Sous-pages en fenêtre :</b> touche une ligne dans Réglages, Protection, Historique ou Plus et la sous-page s’ouvre en fenêtre par-dessus la page – la page reste visible derrière. Choisis comment dans Réglages → Affichage et langue → Sous-pages : Par le bas, Au milieu (par défaut), Par le côté ou Page entière (comme avant). Chaque appareil s’en souvient. Fermer : ✕, toucher à côté de la fenêtre, Échap ou retour ; ou tirer la ligne de titre vers le bas (Par le côté : vers la droite). Direct reste tel quel. Une radio dans la fenêtre continue de jouer quand tu fermes la fenêtre.</p>",
"it": "<p><b>🪟 Sottopagine in una finestra:</b> tocca una riga in Impostazioni, Protezione, Cronologia o Altro e la sottopagina si apre in una finestra sopra la pagina – la pagina resta visibile dietro. Scegli come in Impostazioni → Aspetto e lingua → Sottopagine: Dal basso, Al centro (predefinito), Dal lato o Pagina intera (come prima). Ogni dispositivo se lo ricorda. Chiudere: ✕, toccare accanto alla finestra, Esc o indietro; oppure trascinare la riga del titolo in basso (Dal lato: a destra). Live resta com’è. Una radio nella finestra continua a suonare quando chiudi la finestra.</p>",
"rm": "<p><b>🪟 Sutpaginas sco fanestra:</b> tutga ina lingia en Parameters, Protecziun, Cronologia u Dapli e la sutpagina s’avra sco fanestra sur la pagina – la pagina resta visibla davos. Tscherna co en Parameters → Preschentaziun e lingua → Sutpaginas: Da sut, Amez (da fabrica), Da la vart u Pagina entira (sco pli baud). Mintga apparat sa regorda da quai. Serrar: ✕, tutgar sper la fanestra, Esc u enavos; u trair la lingia dal titel engiu (Da la vart: a dretga). Live resta sco ch’el è. In radio en la fanestra suna vinavant, sche ti serras la fanestra.</p>"
}"""
try:
    UF_HELP = json.loads(UF_HELP_JS)
except ValueError:
    UF_HELP = {}


def uf_help(doc, lang):
    """the paragraph right under the heading of «Tipps & Tricks» (once; a manual without the section stays as it is)"""
    p = UF_HELP.get(lang)
    if not p or not isinstance(doc, str) or p[:40] in doc:
        return doc
    i = doc.find('<section id="tips"')
    j = doc.find("</h2>", i) if i >= 0 else -1
    return doc[:j + 5] + p + doc[j + 5:] if j >= 0 else doc


try:                                                           # (without the data zip the pages are short stand-ins - nothing to do)
    _hp_en_uf = HELP_PAGE.find('<div lang="en">')
    if _hp_en_uf > 0:
        HELP_PAGE = uf_help(HELP_PAGE[:_hp_en_uf], "de") + uf_help(HELP_PAGE[_hp_en_uf:], "en")
    for _L in ("fr", "it", "rm"):
        if HELP_X.get(_L):
            HELP_X[_L] = uf_help(HELP_X[_L], _L)
except Exception as _e:
    print(f"639zzzzx help: {_e}")


_render_page_before_uf = render_page


# wraps: render_page
def render_page(page, active):
    """+ 639zzzzx: sub-pages as a window on every page with tabs (the script decides: Schutz, Verlauf, Einstellungen, Mehr)"""
    out = _render_page_before_uf(page, active)
    if '<nav class="nav">' not in out or "</body>" not in out or "</head>" not in out:
        return out
    out = out.replace("</head>", UF_CSS + "</head>", 1)
    i = out.rfind("</body>")
    js = UF_JS.replace("/*FXTX*/{}", json.dumps(uf_tx(), ensure_ascii=False).replace("</", "<\\/"), 1)
    return out[:i] + js + out[i:]


def _uf_selftest():
    p = render_page("<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>", "settings")
    assert p.count('id="fx-css"') == 1 and p.count("window.MWFX = {on") == 1 and "/*FXTX*/" not in p, "639zzzzx: window script missing / twice"
    assert "fx-css" not in render_page("<html><head></head><body><main></main></body></html>", "guest"), "639zzzzx: on a page without tabs"
    assert "mw-sheet" in WEB_UI_LOCAL, "639zzzzx: the style is per device"
    for k, v in UF_TX.items():
        assert len(v) == 5 and all(v), "639zzzzx: text " + k
    for L in ("de", "en", "fr", "it", "rm"):
        assert "🪟" in UF_HELP.get(L, ""), "639zzzzx: manual " + L
    if '<section id="tips"' in HELP_PAGE:
        assert HELP_PAGE.count("🪟 Unterseiten als Fenster") == 1 and HELP_PAGE.count("🪟 Sub-pages as a window") == 1, "639zzzzx: manual de / en"
    for k in ('lsg("mw-sheet", "mid")', '"/protect", "/recordings", "/settings", "/more"', "history.pushState({fx:", "T.MWFX.radio(a)", "radioOn()", "prefers-reduced-motion",
              'card.id = "fx-card"', 'setAttribute("aria-modal", "true")'):
        assert k in UF_JS or k in UF_CSS, "639zzzzx: " + k


SELFTEST_EXTRA.append(("Sub-pages as a window (639zzzzx)", _uf_selftest))
