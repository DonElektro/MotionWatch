#@ MoveEye – Teil 549: Live-Seite «Sim-Kompakt»: mit verbundenem Simulator zwei kleine Bilder (Kamera, Simulator), darunter Kopf- und Rover-Stick am Rand und die Simulator-Kacheln dazwischen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): on the tab Live, while the simulation is on AND connected, a compact view «Sim-Kompakt»
# (on by itself, switchable in «◫ Ansicht», stored per device in localStorage «mw-simkompakt»):
#   top     two small pictures side by side: left MoveEye's camera (#video, the one stream), right the simulator window
#           (the picture poll of 530/470 simViewPoll - the same <img>, moved here, no second stream; data-dock = the naked
#           picture of the simulator when it knows dock=1). Tap = big (over both columns), tap again = back. The simulator
#           picture when big is the simulator window (mouse / ✋ finger go to the simulator, ✕ = back).
#   below   left the head stick (#stick of the controls, moved here) with ◎, the shutter 🎯 (539) and the AI help 🤖 (546)
#           next to it; right the rover stick (#mstick, /api/mover) - in a game round only when the game mode drives the
#           rover (seek, patrol), otherwise locked with a hint; between them the tiles: Szene, Tageszeit, Wetter, Besuch (the
#           sheets of the Simulator-Zentrale 139), Spiel, Wildbeobachtung, Dein Platz (the simulator controls of the
#           «Simulator-Steuerung», simCtlBuild of 470, one group each), KI-Wächter (simulator control game_kiguard, only when
#           the simulator has it), Ansicht (views of the simulator window, /api/sim padview like 538), Folgen (the quick
#           switch «Follow» of 530) and «… mehr» = the whole «Simulator-Steuerung» card (search, Simple / Expert).
#   The explanation of the simulator window is behind «?», «Bildqualität» is in «◫ Ansicht».
# Nothing changes when the simulator is not connected (or Sim-Kompakt is off): every element goes back to its place.
# Hooks: 536 (placeStick leaves the stick alone, menuBuild calls skMenu), 539 / 546 (window.skSlot), 139 (mwSimHub, sheets
# with data-simhub="sheet"). Window (Tk): no live sticks / simulator window there - nothing to do. Translations: part 597.
# ----------------------------------------------------------------------------

SIMKOMPAKT_JS = r"""
<style id="sk-css">
body.sk.lv:not(.videoonly) main>section{display:block!important;height:100%;overflow-y:auto!important;overflow-x:hidden;padding-bottom:16px!important}
body.sk.sk-wide.lv:not(.videoonly) main>section{display:grid!important;grid-template-columns:minmax(0,1fr) var(--sk-sw,340px);gap:12px;overflow:hidden!important;padding-bottom:0!important}
body.sk.sk-wide.lv:not(.videoonly) #lv-main,body.sk.sk-wide.lv:not(.videoonly) #lv-side{height:100%;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;scrollbar-width:thin;padding-bottom:12px}
body.sk.lv:not(.videoonly) #lv-side{margin-top:12px}
body.sk.sk-wide.lv:not(.videoonly) #lv-side{margin-top:0}
body.sk.lv:not(.videoonly) #lv-main{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-areas:"cam sim" "ctl ctl" "more more";gap:8px;align-content:start;padding-bottom:0}
body.sk.lv:not(.videoonly) #lv-main>*+*{margin-top:0}
body.sk.lv:not(.videoonly) #lv-simw{display:contents}   /* also while 530 hides it for a moment (the simulator is busy): 20 s grace */
body.sk.lv:not(.videoonly) #vcard{grid-area:cam;height:var(--sk-ph,180px);min-height:0;padding:0!important;margin:0;display:block;overflow:hidden;flex:none}
body.sk.lv:not(.videoonly) #vcard>:not(.vwrap){display:none}
body.sk.lv:not(.videoonly) #vcard .vwrap{height:100%;border-radius:12px}
body.sk.lv:not(.videoonly) #video{width:100%!important;height:100%!important;max-height:none!important;min-height:0!important;object-fit:contain;aspect-ratio:auto;cursor:zoom-in}
body.sk.lv:not(.videoonly) #lv-joy,body.sk #pip{display:none!important}
body.sk.lv:not(.videoonly) #lv-tools button{width:30px;height:30px;font-size:14px;border-radius:8px}
body.sk.lv:not(.videoonly) #lv-tools{top:5px;right:5px;gap:4px}
body.sk.lv:not(.videoonly) #lv-tools button svg{width:15px;height:15px}
#sk-sim,#sk-ctl{display:none}
body.sk.lv:not(.videoonly) #sk-sim{display:flex;grid-area:sim;height:var(--sk-ph,180px);padding:0;margin:0;align-items:center;justify-content:center;background:#000;border-radius:12px;overflow:hidden;position:relative;border:1px solid var(--line)}
#sk-sim #lv-vw{width:100%;height:100%;display:flex;align-items:center;justify-content:center}
#sk-sim #lv-vw[hidden]{display:none}
#sk-sim .lv-vbox{border-radius:0;display:flex;align-items:center;justify-content:center;width:100%;height:100%}
#sk-sim .lv-vbox img{width:auto;height:auto;max-width:100%;max-height:100%;cursor:zoom-in}
#sk-sim .lv-vhelp{display:none}
#sk-sim:not(.big) .lv-vbtn,#sk-sim:not(.big) .stp{display:none!important}
#sk-sim .lv-vbtn button{width:32px;height:32px;font-size:15px}
#sk-sim.big .lv-vbox img{cursor:grab}
#sk-cap{position:absolute;left:6px;bottom:5px;right:6px;font-size:10.5px;line-height:1.25;color:#fff;text-shadow:0 1px 2px #000;pointer-events:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;z-index:2}
#sk-sim .sk-wait{color:var(--mut);font-size:13px}
#sk-back{position:absolute;left:6px;top:6px;z-index:4;width:32px;height:32px;padding:0;border-radius:8px;border:1px solid rgba(255,255,255,.3);background:rgba(8,12,20,.65);color:#fff;font-size:15px;display:none}
#sk-sim.big #sk-back{display:block}
/* big: one picture over both columns, the other one away until tapped back */
body.sk.lv:not(.videoonly) #lv-main.sk-bc{grid-template-areas:"cam cam" "ctl ctl" "more more"}
body.sk.lv:not(.videoonly) #lv-main.sk-bs{grid-template-areas:"sim sim" "ctl ctl" "more more"}
body.sk.lv:not(.videoonly) #lv-main.sk-bc #sk-sim,body.sk.lv:not(.videoonly) #lv-main.sk-bs #vcard{display:none!important}
body.sk.lv:not(.videoonly) #lv-main.sk-bc #vcard,body.sk.lv:not(.videoonly) #lv-main.sk-bs #sk-sim{height:var(--sk-phb,320px)}
body.sk.lv:not(.videoonly) #lv-main.sk-bc #video{cursor:zoom-out}
/* the controls: head stick | tiles | rover stick (narrow: sticks in one row, the tiles below) */
body.sk.lv:not(.videoonly) #sk-ctl{display:grid;grid-area:ctl;grid-template-columns:auto minmax(0,1fr) auto;grid-template-areas:"hs tl ms";gap:8px 10px;align-items:start;
  background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:8px}
body.sk.lv:not(.videoonly) #sk-ctl.sk-n{grid-template-areas:"hs . ms" "tl tl tl"}
body.sk.lv.swapside:not(.videoonly) #sk-ctl{grid-template-areas:"ms tl hs"}
body.sk.lv.swapside:not(.videoonly) #sk-ctl.sk-n{grid-template-areas:"ms . hs" "tl tl tl"}
#sk-hs{grid-area:hs;display:flex;gap:8px;align-items:flex-start}
body.swapside #sk-hs{flex-direction:row-reverse}
#sk-ms{grid-area:ms;display:flex;flex-direction:column;align-items:center;gap:3px}
#sk-ms[hidden]{display:none}
.sk-sb{display:flex;flex-direction:column;align-items:center;gap:3px}
.sk-slot{width:var(--sk-st,140px);height:var(--sk-st,140px);position:relative}
#sk-ctl .sk-slot>.stick{width:100%!important;height:100%!important;margin:0}
.sk-lb{font-size:11.5px;color:var(--mut);text-align:center;max-width:var(--sk-st,140px);line-height:1.2}
#sk-act{display:flex;flex-direction:column;gap:8px;align-items:center;padding-top:2px}
#sk-act>button,#sk-act>div>button{margin:0}
#sk-cen{width:44px;height:44px;border-radius:50%;padding:0;font-size:20px}
#sk-shut:empty,#sk-kih:empty{display:none}
#sk-shut #msh-b{position:relative!important;left:auto!important;top:auto!important;width:64px!important;height:64px!important;font-size:24px!important}
#sk-kih #kih-b{position:relative!important;left:auto!important;top:auto!important;max-width:92px;white-space:normal;padding:6px 8px;font-size:12px}
#sk-ms.off .sk-slot{opacity:.35;pointer-events:none;filter:grayscale(1)}
#sk-ms{position:relative}
#sk-mhint{position:absolute;left:4px;right:4px;top:calc(var(--sk-st,140px) / 2 - 22px);font-size:11.5px;font-weight:600;color:#fff;text-align:center;
  background:rgba(10,14,20,.78);border:1px solid var(--org,#f2a33a);border-radius:10px;padding:4px 6px;pointer-events:none}
#sk-act.two{display:grid;grid-template-columns:auto auto;gap:6px 6px;align-items:center;justify-items:center}
#sk-mon{font-size:11px;padding:3px 8px;max-width:var(--sk-st,140px);line-height:1.2}
#sk-hlp{width:32px;height:32px;border-radius:50%;padding:0;font-size:15px;font-weight:700}
#sk-hlp.on{background:var(--acc);color:#fff;border-color:transparent}
#sk-tl{grid-area:tl;min-width:0}
#sk-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:6px}
#sk-tiles .skt{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;padding:5px 3px;min-height:52px;border-radius:12px;border:1px solid var(--line);
  background:var(--panel2,#151e2b);color:var(--txt);font:inherit;cursor:pointer;min-width:0;line-height:1.15}
#sk-tiles .skt i{font-style:normal;font-size:18px;line-height:1}
#sk-tiles .skt b{font-size:11.5px;font-weight:600;max-width:100%;overflow:hidden;text-align:center;overflow-wrap:anywhere;hyphens:auto;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
#sk-tiles .skt small{font-size:10px;color:var(--mut);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#sk-tiles .skt.open{border-color:var(--acc);box-shadow:inset 0 0 0 1px var(--acc)}
#sk-tiles .skt.on{border-color:#f59a4a}
#sk-tiles .skt.on small{color:#f59a4a}
#sk-tiles .skt.q{min-height:0}
#sk-sheet:empty{display:none}
#sk-sheet{margin-top:8px;max-height:min(46vh,420px);overflow-y:auto;overscroll-behavior:contain}
#sk-sheet .shsheet{margin-top:0}
#sk-sheet .sc-card{margin:0}#sk-sheet .sc-hd{display:none}#sk-sheet .sc-bd{display:block!important;padding:4px 10px 8px}
#sk-sheet .skv{display:flex;flex-wrap:wrap;gap:6px}#sk-sheet .skv button{flex:1 1 auto;min-width:96px}
#sk-sheet .skv button.on{background:var(--acc);color:#fff;border-color:transparent}
#sk-sheet .skh{font-size:12.5px;line-height:1.45;padding:8px 10px;border:1px solid var(--line);border-radius:12px;background:var(--panel2,#151e2b)}
#sk-sheet .skh p{margin:0 0 6px}
body.sk.lv:not(.videoonly) #lv-sim{grid-area:more;margin:0}
body.sk.lv:not(.videoonly):not(.sk-more) #lv-sim{display:none!important}
body.sk #lv-sim .simq,body.sk #lv-simst{display:none}
#lv-menu .simq{margin-top:4px}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*SKDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  try { I18N.en = I18N.en || {}; Object.assign(I18N.en, {
    "sk-note": "With the simulator connected: two small pictures at the top (camera and simulator), below them the head and rover sticks at the edges, the tiles of the simulator in between. Only for this device.",
    "sk-help": "Sim compact: tap a picture = big, tap again = small. The big simulator picture is the simulator window (mouse and ✋ finger steer the simulator, ✕ = back). Left stick = MoveEye's head, right stick = rover (in a game round only when the game drives the rover). The tiles = what happens in the simulator; «… more» = all settings of the simulator. On / off and picture quality under «◫ View»."}); } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const $i = id => document.getElementById(id);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const W = $i("lv-simw"), D = $i("lv-sim"), VW = $i("lv-vw"), VI = $i("lv-vimg"), main = document.querySelector("main"), M0 = () => $i("lv-main");
  if (!W || !D || !VW || !VI || !main) return;
  const KEY = "mw-simkompakt";                          // per device: {on: "auto" | "off"}
  let P = {on: "auto"};
  try { Object.assign(P, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(P)); } catch (e) {} };
  const SQ = D.querySelector(".simq");                  // «Bildqualität» (470 simQBox) - in «◫ Ansicht» while Sim-Kompakt is on
  const VWHOME = document.createComment("lv-vw");       // the places the moved elements go back to
  // ---- the elements ----
  const SIM = E("div", "card"); SIM.id = "sk-sim"; SIM.dataset.dock = "1";      // card: simViewPoll asks for the size of this box; dock=1 = naked picture
  const CAP = E("div"); CAP.id = "sk-cap";
  const BK = E("button", "", "✕"); BK.id = "sk-back"; BK.type = "button";
  const WAIT = E("div", "sk-wait", "…");
  SIM.append(WAIT, CAP, BK);
  const C = E("div"); C.id = "sk-ctl";
  const HS = E("div"); HS.id = "sk-hs";
  const HSB = E("div", "sk-sb"), HSL = E("div", "sk-slot"), HLB = E("div", "sk-lb");
  HSB.append(HSL, HLB);
  const ACT = E("div"); ACT.id = "sk-act";
  const CEN = E("button", "sec", "◎"); CEN.id = "sk-cen"; CEN.type = "button";
  const HLP = E("button", "sec", "?"); HLP.id = "sk-hlp"; HLP.type = "button"; HLP.onclick = () => setOpen(open === "help" ? "" : "help");
  const SHUT = E("div"); SHUT.id = "sk-shut"; const KIH = E("div"); KIH.id = "sk-kih";
  ACT.append(CEN, SHUT, KIH, HLP); HS.append(HSB, ACT);
  const MS = E("div"); MS.id = "sk-ms";
  const MSL = E("div", "sk-slot"), MLB = E("div", "sk-lb"), MH = E("div"); MH.id = "sk-mhint"; MH.hidden = true;
  const MON = E("button", "sec"); MON.id = "sk-mon"; MON.type = "button"; MON.hidden = true;
  MS.append(MSL, MLB, MH, MON);
  const TL = E("div"); TL.id = "sk-tl";
  const TI = E("div"); TI.id = "sk-tiles"; const SH = E("div"); SH.id = "sk-sheet";
  TL.append(TI, SH);
  C.append(HS, TL, MS);
  W.append(SIM, C);
  CEN.onclick = () => { const c = $i("stick-center"); if (c) c.click(); };
  D.addEventListener("toggle", () => { if (ON && !D.open) { D.open = true; document.body.classList.remove("sk-more"); TI.dataset.sig = ""; paint(); } });   // closing the card = «… weniger» (530 needs it open for the picture)
  // ---- state ----
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const ST = () => J().state || {};
  let ON = false, R = null, G = null, open = "", big = "", rSig = "";
  let linkT = 0;
  const linked = () => { const s = ST().sim || {}; if (s.on && s.ok && !W.hidden) linkT = Date.now(); return !!s.on && Date.now() - linkT < 20000; };
  const want = () => P.on !== "off" && linked() && !document.body.classList.contains("videoonly") && !document.body.classList.contains("lv-mini")
    && !document.body.classList.contains("pv-on") && !D.classList.contains("lvh") && !!M0();
  window.skOwns = () => ON;                             // 536 placeStick: the head stick belongs to Sim-Kompakt
  window.skSlot = k => ON ? (k === "shut" ? SHUT : k === "kih" ? KIH : null) : null;   // 539 / 546: their buttons next to the stick
  // ---- switching on / off: the elements move here and back ----
  function sticks(on) {
    const st = $i("stick"), ms = $i("mstick"), box = document.querySelector(".ctl-stick .stickbox"), mbox = $i("mstickbox");
    if (on) {
      if (st && st.parentNode !== HSL && !document.body.classList.contains("videoonly")) HSL.appendChild(st);
      if (ms && ms.parentNode !== MSL && !document.body.classList.contains("videoonly")) MSL.appendChild(ms);
    } else {
      if (st && box && st.parentNode === HSL) box.insertBefore(st, box.firstChild);
      if (ms && mbox && ms.parentNode === MSL) mbox.insertBefore(ms, mbox.firstChild);
    }
  }
  function setOn(on) {
    if (on === ON) { if (on) sticks(true); return; }
    ON = on; document.body.classList.toggle("sk", on);
    if (on) {
      if (VW.parentNode !== SIM) { VW.before(VWHOME); SIM.insertBefore(VW, CAP); }
      if (SQ) SQ.remove();
      D.open = true;                                     // 530 shows the simulator window only while its card is open
      sticks(true);
    } else {
      setBig(""); setOpen(""); document.body.classList.remove("sk-more", "sk-wide");
      if (VWHOME.parentNode) { VWHOME.replaceWith(VW); }
      if (SQ) VW.after(SQ);
      VI.style.width = VI.style.height = "";               // the size of the small picture (fitSim)                               // back from «◫ Ansicht» (also when the panel holds it right now)
      sticks(false);
      const m = M0(); if (m) m.classList.remove("sk-bc", "sk-bs");
    }
    if (typeof window.lvApply === "function") try { window.lvApply(); } catch (e) {}
    layout(); paint();
  }
  // ---- the size of the pictures and sticks ----
  function layout() {
    const m = M0(); if (!ON || !m) return;
    const B = document.body, land = B.classList.contains("lv-land");
    const wide = land && innerWidth >= 1100;
    B.classList.toggle("sk-wide", wide);
    const Hh = main.clientHeight || innerHeight;
    const mw = m.clientWidth || (main.clientWidth - 24);
    const narrow = mw < 620; C.classList.toggle("sk-n", narrow);
    const stk = Math.round(Math.max(104, Math.min(narrow ? Math.min(innerWidth * 0.36, 150) : 150, land ? Math.min(innerHeight * 0.34, 150) : 170)));
    document.documentElement.style.setProperty("--sk-st", stk + "px");
    const ch = Math.max(stk + 22, C.querySelector("#sk-tiles").offsetHeight + 16) + (narrow ? TI.offsetHeight + 8 : 0) + 20;
    const col = (mw - 8) / 2;
    let ph = land ? Math.min(col * 9 / 16, Hh - ch - 26) : Math.min(col * 9 / 16, Hh * 0.42);
    ph = Math.round(Math.max(90, ph));
    let pb = land ? Math.min(mw * 9 / 16, Hh - ch - 26) : Math.min(mw * 9 / 16, Hh * 0.62);
    pb = Math.round(Math.max(ph, pb));
    m.style.setProperty("--sk-ph", ph + "px"); m.style.setProperty("--sk-phb", pb + "px");
    ACT.classList.remove("two"); if (ACT.scrollHeight > stk + 24) ACT.classList.add("two");   // ◎ 🎯 🤖 ? in two columns when higher than the stick
    fitSim();
  }
  function fitSim() {                                  // the simulator picture without black edges (simViewBind maps clicks onto the element)
    const bw = SIM.clientWidth, bh = SIM.clientHeight; if (!bw || !bh) return;
    const a = (VI.naturalWidth && VI.naturalHeight) ? VI.naturalWidth / VI.naturalHeight : 16 / 9;
    let w = bw, h = bw / a; if (h > bh) { h = bh; w = bh * a; }
    w = Math.floor(w); h = Math.floor(h);
    if (VI.style.width !== w + "px") VI.style.width = w + "px";
    if (VI.style.height !== h + "px") VI.style.height = h + "px";
  }
  VI.addEventListener("load", () => { if (ON) { WAIT.hidden = true; fitSim(); } });
  // ---- tap = big, tap again = back ----
  function setBig(k) {
    big = k; const m = M0(); if (!m) return;
    m.classList.toggle("sk-bc", k === "cam"); m.classList.toggle("sk-bs", k === "sim"); SIM.classList.toggle("big", k === "sim");
    if (k !== "sim" && VW.classList.contains("big")) { VW.classList.remove("big"); const b = $i("lv-vbig"); if (b) b.textContent = "⛶"; }
    requestAnimationFrame(() => { fitSim(); if (k) (k === "cam" ? $i("vcard") : SIM).scrollIntoView({block: "nearest"}); });
  }
  BK.onclick = e => { e.stopPropagation(); setBig(""); };
  const v = $i("video");
  let vT = null;
  if (v) {
    v.addEventListener("click", () => {
      if (!ON) return;
      const g = $i("mwg"); if (g && !g.hidden) return;   // the hunter of the game taps on players (530)
      clearTimeout(vT); vT = setTimeout(() => setBig(big === "cam" ? "" : "cam"), 260);
    });
    v.addEventListener("dblclick", () => clearTimeout(vT));     // double tap = full screen (530)
  }
  // the simulator picture: small = a tap makes it big (and does not reach the simulator); big = it is the simulator window
  // (mouse and ✋ finger go to the simulator; a finger tap without ✋ = back)
  let tp = null;
  const vbox = VI.parentNode;
  vbox.addEventListener("pointerdown", e => {
    if (!ON || e.target !== VI) return;
    const ctl = $i("lv-vctl") && $i("lv-vctl").classList.contains("on");
    if (big !== "sim" || (e.pointerType !== "mouse" && !ctl)) { tp = {x: e.clientX, y: e.clientY, t: Date.now(), id: e.pointerId}; e.stopPropagation(); }
  }, true);
  ["pointermove", "pointerup", "pointercancel"].forEach(n => vbox.addEventListener(n, e => {
    if (!ON || !tp || e.pointerId !== tp.id) return;
    e.stopPropagation();
    if (n === "pointermove") { if (Math.hypot(e.clientX - tp.x, e.clientY - tp.y) > 12) tp.moved = true; return; }
    const ok = n === "pointerup" && !tp.moved && Date.now() - tp.t < 700; tp = null;
    if (ok) setBig(big === "sim" ? "" : "sim");
  }, true));
  ["click", "dblclick", "wheel"].forEach(n => vbox.addEventListener(n, e => { if (ON && big !== "sim" && e.target === VI) { e.stopPropagation(); if (n === "wheel") e.preventDefault(); } }, {capture: true, passive: false}));
  // ---- the simulator controls (the same request as the «Simulator-Steuerung» of 530) ----
  const fmt = (c, x) => (x == null ? "–" : (Math.abs(x) >= 100 || c.step >= 1 ? Math.round(x) : (+x).toFixed(c.step < 0.1 ? 2 : 1))) + (c.unit ? " " + c.unit : "");
  const ctl = async d => { const r = await post("/api/sim", Object.assign({action: "ctl", lang: LANG}, d)); if (r && r.ok) { R = r; paint(); } else toast("⚠ " + ((r && r.error) || T("simulator not reachable"))); return r; };
  let busy = false, gBusy = false, gT = 0;
  async function poll() {
    if (!ON || busy || document.hidden) return;
    busy = true;
    try { const r = await post("/api/sim", {action: "ctl", ctl: "get", lang: LANG}); if (r && r.ok) { R = r; paint(); } } catch (e) {} finally { busy = false; }
    if (R && R.game && R.game.open && !gBusy && Date.now() - gT > 3500) {      // a game round: may the rover drive?
      gBusy = true; gT = Date.now();
      try { const g = await post("/api/sim", {action: "game", lang: LANG}); G = g && g.ok !== false ? g : null; } catch (e) {} finally { gBusy = false; }
    } else if (!(R && R.game && R.game.open)) G = null;
  }
  const cv = id => { const c = R && (R.controls || []).find(x => x.id === id); return c ? c : null; };
  const HUB = () => window.mwSimHub || null;
  const H = () => { const h = HUB(); return h ? h.H() : null; };
  const TT = k => { const h = HUB(); return h && h.tt ? h.tt(k) : T(k); };          // the words of the Simulator-Zentrale (139: weather …)
  const WXI = {clear: "☀", cloudy: "☁", rain: "🌧", fog: "🌫", snow: "❄"};
  const VIEWS = [["head", "🎥", "Head camera"], ["top", "🛰", "From above"], ["follow", "🚜", "Behind the rover"], ["driver", "🧑‍✈️", "Driver's view"], ["free", "🕊", "Free view"], ["off", "↺", "Normal view"]];
  let VIEW = "";
  function tiles() {
    const h = H() || {}, sc = (h.scenes || []).find(x => x.id === h.scene) || {};
    const L = [["scene", "🗺", "Scene", sc.name || h.scene || (R && R.scenario) || ""],
      ["hour", h.dark ? "🌙" : "☀", "Time of day", h.clock || ""],
      ["weather", WXI[h.weather] || "☁", "Weather", h.weather ? TT(h.weather) : ""],
      ["visit", "🚶", "Visit", h.visitors != null ? h.visitors + " " + T("now") : ""],
      ["game", "🎮", "Game", R && R.game ? (R.game.open ? "🟢 " + (R.game.players || 0) : T("off")) : ""],
      ["wildlife", "🦌", "Wildlife watching", cv("rifle") ? (cv("rifle").value ? T("on") : T("off")) : ""],
      ["place", "🪞", "Your place", cv("twin_on") ? (cv("twin_on").value ? T("on") : T("off")) : ""]];
    if (h.wide && window.mwWide) L.splice(1, 0, ["wide", "🔭", "Wide camera", window.mwWide.sub(h)]);   // 591: the wide picture (tap = big)
    const kg = cv("game_kiguard");                      // simulator with «MoveEye as AI guard»
    if (kg) L.push(["kig", "🤖", "AI guard", kg.value ? T("on") : T("off")]);
    L.push(["view", "👁", "View", VIEW ? T((VIEWS.find(x => x[0] === VIEW) || [0, 0, ""])[2]) : ""]);
    const tb = $i("qs-track"); if (tb && !tb.classList.contains("na") && !document.body.classList.contains("lv-nohead")) L.push(["follow", "🎯", "Follow", tb.classList.contains("on") ? T("on") : T("off")]);
    L.push(["more", "…", document.body.classList.contains("sk-more") ? "less" : "more", ""]);
    const sig = JSON.stringify([L, open, LANG]); if (sig === TI.dataset.sig) return; TI.dataset.sig = sig;
    TI.textContent = "";
    L.forEach(([k, ic, lb, sub]) => {
      const b = E("button", "skt" + (open === k ? " open" : "") + ((k === "kig" && kg && kg.value) || (k === "follow" && sub === T("on")) || (k === "more" && document.body.classList.contains("sk-more")) ? " on" : ""));
      b.type = "button"; b.dataset.k = k; b.title = T(lb);
      b.append(E("i", "", ic), E("b", "", T(lb))); if (sub) b.appendChild(E("small", "", sub));
      b.onclick = () => tap(k); TI.appendChild(b);
    });
  }
  function tap(k) {
    if (k === "kig") { const c = cv("game_kiguard"); return ctl({ctl: "set", id: "game_kiguard", value: !(c && c.value)}); }
    if (k === "follow") { const b = $i("qs-track"); if (b) b.click(); setTimeout(paint, 700); return; }
    if (k === "more") { document.body.classList.toggle("sk-more"); D.open = true; paint(); if (document.body.classList.contains("sk-more")) setTimeout(() => D.scrollIntoView({behavior: "smooth", block: "start"}), 60); return; }
    setOpen(open === k ? "" : k);
  }
  function setOpen(k) { open = k; SH.textContent = ""; SH.dataset.sig = ""; TI.dataset.sig = ""; if (ON) paint(); if (k) setTimeout(() => SH.scrollIntoView({block: "nearest", behavior: "smooth"}), 60); }
  function sheet() {
    if (!open) { if (SH.firstChild) SH.textContent = ""; return; }
    if (["scene", "hour", "weather", "visit", "wide"].includes(open)) {   // the sheets of the Simulator-Zentrale (139; wide: 591)
      let b = SH.firstChild;
      if (!b || b.dataset.kind !== open) { SH.textContent = ""; b = E("div"); b.dataset.simhub = "sheet"; b.dataset.kind = open; SH.appendChild(b); const h = HUB(); if (h) h.paint(); }
      return;
    }
    if (["game", "wildlife", "place"].includes(open)) {                   // one group of the «Simulator-Steuerung» (470 simCtlBuild)
      if (!R || typeof simCtlBuild !== "function") return;
      const gid = open === "place" ? "scene" : open;
      let cs = (R.controls || []).filter(c => (c.gid || "") === gid || (!c.gid && gid === "game" && /^(Spiel|Game)$/.test(c.group || "")));
      if (open === "place") cs = cs.filter(c => c.sub === "Dein Platz" || /^twin_/.test(c.id)).map(c => Object.assign({}, c, {sub: ""}));
      const sig = JSON.stringify([open, cs.map(c => [c.id, c.type, c.label, c.options])]);
      let b = SH.firstChild;
      if (!b || SH.dataset.sig !== sig) {
        SH.textContent = ""; SH.dataset.sig = sig; b = E("div"); b.dataset.only = gid; SH.appendChild(b);
        if (!cs.length) { b.appendChild(E("div", "mut", T("not supported - update the simulator"))); return; }
        simCtlBuild(b, Object.assign({}, R, {controls: cs}), ctl, fmt);
        b.querySelectorAll(".sc-card").forEach(c => c.classList.add("open"));
      }
      b.querySelectorAll("[data-cid]").forEach(row => {                  // the values, like 530 lpaint
        const c = cs.find(x => x.id === row.dataset.cid); const inp = row.querySelector(".simv"); if (!c || !inp || inp === document.activeElement) return;
        if (c.type === "toggle") inp.checked = !!c.value; else if (c.value != null) inp.value = c.value;
        const vv = row.querySelector(".simvv"); if (vv) vv.textContent = fmt(c, c.value);
      });
      if (open === "game") {
        let gl = SH.querySelector(".skgl");
        if (!gl) { gl = E("a", "btn sec skgl", "🎮 " + T("Game") + " → " + T("Simulator")); gl.href = "/sim#c-game"; gl.style.cssText = "display:inline-block;margin-top:6px"; SH.appendChild(gl); }
      }
      return;
    }
    const sig = open + "|" + VIEW + "|" + LANG; if (SH.dataset.sig === sig) return; SH.dataset.sig = sig; SH.textContent = "";
    if (open === "view") {
      const w = E("div", "skv");
      VIEWS.forEach(([k, ic, lb]) => { const b = E("button", "sec" + (VIEW === k ? " on" : ""), ic + " " + T(lb)); b.type = "button";
        b.onclick = async () => { const r = await post("/api/sim", {action: "padview", view: k, lang: LANG}); if (r && r.ok) { VIEW = k === "off" ? "" : (r.view || k); SH.dataset.sig = ""; paint(); } else toast("⚠ " + ((r && r.error) || T("not supported - update the simulator"))); };
        w.appendChild(b); });
      SH.appendChild(w);
    }
    if (open === "help") {
      const w = E("div", "skh"), hv = $i("lv-vhelp");
      w.appendChild(E("p", "", T("sk-help"))); if (hv && hv.textContent) w.appendChild(E("p", "mut", hv.textContent));   // the explanation of the simulator window (530)
      SH.appendChild(w);
    }
  }
  // ---- the rover stick: in a game round only when the game drives the rover ----
  function rover() {
    const m = ST().mover || {}, av = !!m.avail;
    MS.hidden = !av;
    if (!av) return;
    const round = G && (G.round === "play" || G.round === "countdown"), okMode = G && ["seek", "patrol"].includes(G.mode);
    const off = !!(round && !okMode);
    MS.classList.toggle("off", off);
    MH.hidden = !off; if (off) MH.textContent = "🔒 " + T("Rover locked in this game round");
    MLB.textContent = "🚜 " + T("Rover");
    const test = !!(m.sim && m.test) && !!cv("mover_on");
    MON.hidden = !test || off; if (test) { MON.textContent = "🚜 " + T("Switch on"); MON.title = T("Switch the rover on in the simulator"); }
  }
  MON.onclick = () => ctl({ctl: "set", id: "mover_on", value: true});
  function paint() {
    if (!ON) return;
    HLB.textContent = "🎥 " + T("Head"); CEN.title = T("Centre"); HLP.title = T("Help"); HLP.classList.toggle("on", open === "help");
    BK.title = T("Back");
    const st = R && R.status ? String(R.status) : ""; if (CAP.textContent !== st) CAP.textContent = st;
    WAIT.hidden = VI.naturalWidth > 0 && !!VI.getAttribute("src");
    rover(); tiles(); sheet();
  }
  // ---- «◫ Ansicht» (536 menuBuild): the switch and the picture quality ----
  window.skMenu = (MN, E_, T_) => {
    if (!linked() && !ON) return;
    MN.appendChild(E("h3", "", "🧩 " + T("Sim compact")));
    const s = E("div", "lvseg");
    [["auto", "On when connected"], ["off", "Off"]].forEach(([k, lb]) => { const b = E("button", "sec" + (P.on === k ? " on" : ""), T(lb)); b.type = "button";
      b.onclick = e => { e.stopPropagation(); P.on = k; save(); tick(); if (typeof window.lvMenu === "function") { window.lvMenu(); window.lvMenu(); } };
      s.appendChild(b); });
    MN.appendChild(s);
    MN.appendChild(E("div", "mut", T("sk-note")));
    if (ON && SQ) {
      MN.appendChild(E("h3", "", T("Picture quality") + " · " + T("Simulator"))); MN.appendChild(SQ);
      const lb = SQ.querySelector("span"); if (lb) lb.textContent = T("Picture quality") + ":";
      SQ.querySelectorAll("option").forEach(o => { o.textContent = T({auto: "automatic", max: "very high", high: "high", mid: "medium", low: "low"}[o.value] || o.value); });
    }
  };
  // ---- the loop ----
  function tick() {
    setOn(want());
    if (ON) { sticks(true); layout(); paint(); }
  }
  addEventListener("resize", () => { if (ON) requestAnimationFrame(layout); });
  if (window.visualViewport) visualViewport.addEventListener("resize", () => { if (ON) layout(); });
  let lastCls = "";
  new MutationObserver(() => { const c = document.body.className; if (c === lastCls) return; lastCls = c; tick(); })
    .observe(document.body, {attributes: true, attributeFilter: ["class"]});
  new MutationObserver(tick).observe(W, {attributes: true, attributeFilter: ["hidden"]});
  setInterval(tick, 1000);
  setInterval(poll, 3000);
  setTimeout(() => { tick(); poll(); }, 900);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", SIMKOMPAKT_JS + "</body>", 1)
WEB_UI_LOCAL.add("mw-simkompakt")                         # per device: a phone may want it, the PC not

# the manual (HELP_PAGE of 540): one paragraph in the section «Live-Seite», German and English
for _a, _b in (('<section id="live" data-icon="📺"><h2>Die Live-Seite</h2>',
                "<p><b>🧩 Sim-Kompakt (ab 2.98.46):</b> Ist der Simulator verbunden, zeigt die Live-Seite oben zwei kleine Bilder (links "
                "die Kamera von MoveEye, rechts das Simulator-Fenster; antippen = gross, nochmals = zurück), darunter links den Kopf-Stick "
                "(mit ◎, Auslöser 🎯 und KI-Hilfe 🤖), rechts den Rover-Stick und dazwischen die Kacheln Szene, Tageszeit, Wetter, Besuch, "
                "Spiel, Wildbeobachtung, Dein Platz, KI-Wächter, Ansicht und Folgen; «… mehr» öffnet die ganze Simulator-Steuerung, «?» "
                "die Erklärung. Ein- und ausschalten (pro Gerät) und die Bildqualität des Simulators unter «◫ Ansicht».</p>"),
               ('<section id="live" data-icon="📺"><h2>The live page</h2>',
                "<p><b>🧩 Sim compact (from 2.98.46):</b> while the simulator is connected the live page shows two small pictures at the "
                "top (left MoveEye's camera, right the simulator window; tap = big, tap again = back), below them the head stick on the "
                "left (with ◎, shutter 🎯 and AI help 🤖), the rover stick on the right and the tiles in between: scene, time of day, "
                "weather, visit, game, wildlife watching, your place, AI guard, view and follow; «… more» opens the whole simulator "
                "control, «?» the explanation. On / off (per device) and the picture quality of the simulator under «◫ View».</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
