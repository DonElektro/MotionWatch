#@ MoveEye – Teil 639zt: «Sim-Ansicht» der Live-Seite im Simulator-Betrieb (Handy / Tablet zuerst): grosses Simulator-Bild, grosse Touch-Knöpfe (IR, Licht, Sirene, Aufnahme, Kopf-Stick, Folgen), «🎮 Spielen» mit einem Tipp (eigene Spielauswahl im Browser, Spielknöpfe und Spielanzeige im Browser), «⋯ Mehr» und «Klassisch». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (02.11.2026, Paket «spielmodus»): am iPad war das Spielen «nicht spielbar», obwohl alles da ist -
# der Spiel-Assistent kam als kleines, abgeschnittenes PC-Bild im Stream, die Knöpfe waren Fernbedienung eines PC-Bilds, die
# Live-Seite war voll, bis zum Spielen brauchte es viele Schritte. Entscheid:
#   * NUR im Simulator-Betrieb (Simulation ein und verbunden) zeigt die Live-Seite eine eigene, ruhige Vollbild-Ansicht
#     «Sim-Ansicht»: oben eine schmale Leiste (Schutz-Zustand, 🎮 Spielen, ⋯ Mehr, ▦ Klassisch), in der Mitte das Bild des
#     Simulators (view.jpg mit dock=1: nur 3D-Bild und Karten / Fenster, ohne Bedienfeld, ohne Abschneiden; klein darüber das
#     Kamerabild von MoveEye), unten gross: Kopf-Stick, 🎯 Folgen, 🔴 IR, 💡 Licht, 🚨 Sirene, ⏺ Aufnahme.
#   * Alles andere der Live-Seite liegt hinter «⋯ Mehr» (alle Schnellschalter in derselben Reihenfolge wie auf der Live-Seite,
#     dazu Controller-Ansicht, Sticks fliegen / umschauen, Simulator, Schutz, Einstellungen) - nichts ist entfernt.
#     «▦ Klassisch» führt zur bisherigen Live-Seite (gemerkt pro Gerät, localStorage «mw-simv»); dort bringt «📱 Sim-Ansicht»
#     (Karte «Simulator-Steuerung») sie zurück. Im echten Betrieb (ohne Simulator) bleibt die Live-Seite genau wie bisher.
#   * «🎮 Spielen»: die Spiele des Spiel-Assistenten (Schnellstart der Simulator-Datei gamewiz.gd, «quick»: Schleichen,
#     Wächter-Duell, Diebstahl, KI-Turm, Spielabend-Turnier, MoveEye ins Schwitzen, Nacht-Spiel, Mission, Die Karte des
#     Grossvaters, das Spiel zur Szene) als grosse Karten im Browser. Ein Tipp = spielen: gamewiz «quick» (alles eingestellt,
#     Spiel offen), «Hier am PC mitspielen» (Steuerung game_local, localplay.gd), gamewiz «next» (Runde startet). Der
#     Assistent selbst öffnet sich im Simulator nicht. «⚙ Anpassen» = der ganze Assistent (Seite Simulator, /sim#gw).
#   * Im Spiel: die Spielknöpfe sind Knöpfe im Browser (Stick gehen links, Stick umschauen rechts, Ducken, Kriechen, Stein,
#     Lampe, Rennen; Wächter: Auslöser, «Erwischt!», Licht, Scan, Sirene, Zoom). Sie wirken wie ein Game-Controller am Browser
#     (/api/sim «pad», die EINE Belegung von padmap.gd: rechter Stick = gehen, linker = umschauen, A Lampe, B Ducken, X Stein,
#     Y Kriechen, R2 Rennen / Auslöser, Start = Runde starten, Select = Wiederholung). Zeit, Verdacht, Leben und das Ergebnis
#     zeigt der Browser selbst (game_info, wie die Zuschauer-Anzeige der Seite Simulator). «× Beenden» = localplay stop.
# Die Geschichten (Maggie, Grossvater, Hospiz) laufen weiter im Simulator-Fenster: dort zeigt die Sim-Ansicht die Sticks
# «gehen / umschauen» von selbst (470 simTouchPad, /api/play «playing»).
# Daten: /api/state (530 refresh → QSJ), /api/sim (gamewiz, ctl, pad, game, localplay), /snapshot.jpg. Kein neuer Begriff
# auf dem Pi, keine neue Einstellung. Übersetzungen: unten (_HX_SIMV, alle 5 Sprachen).
# ----------------------------------------------------------------------------

SIMV_JS = r"""
<style id="sv-css">
#sv{position:fixed;inset:0;z-index:58;background:#05070b;color:#fff;display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:auto minmax(0,1fr) auto;
  padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px);
  touch-action:manipulation;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;overscroll-behavior:none;font-family:system-ui,-apple-system,sans-serif}
#sv[hidden]{display:none}
#sv.land{grid-template-columns:minmax(0,1fr) auto;grid-template-rows:auto minmax(0,1fr)}
#sv.land #sv-stage{grid-column:1;grid-row:2}#sv.land #sv-low{grid-column:2;grid-row:1/3;border-top:0;border-left:1px solid rgba(255,255,255,.1);flex-direction:column;justify-content:center;overflow-y:auto}
#sv-top{display:flex;align-items:center;gap:8px;padding:8px 10px;background:rgba(8,12,20,.9);border-bottom:1px solid rgba(255,255,255,.1);min-width:0}
#sv.land #sv-top{grid-column:1}
#sv-top .sv-nm{font-weight:700;font-size:15px;white-space:nowrap}
#sv-chip{font-size:12px;padding:3px 9px;border-radius:999px;border:1px solid rgba(255,255,255,.25);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
#sv-chip.on{border-color:#3fb950;color:#7ee28f}#sv-chip.alarm{border-color:#ff5b4b;color:#ff8b7b}
#sv-top .sv-sp{flex:1}
#sv button{font:inherit;color:#fff;cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent}
#sv .svt{height:44px;min-width:44px;padding:0 12px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.08);font-size:15px;white-space:nowrap}
#sv .svt.pri{background:var(--acc,#3b8cff);border-color:transparent;font-weight:700;font-size:16px}
#sv .svt.on{background:var(--acc,#3b8cff);border-color:transparent}
#sv-stage{position:relative;min-height:0;overflow:hidden;background:#000;display:flex;align-items:center;justify-content:center}
#sv-img{width:100%;height:100%;object-fit:contain;display:block;outline:none;-webkit-user-drag:none;touch-action:none;max-height:none!important}
#sv-wait{position:absolute;color:#8a96a6;font-size:14px;pointer-events:none;text-align:center;padding:0 20px}
#sv-pip{position:absolute;left:8px;top:8px;width:min(30%,240px);border:2px solid rgba(255,255,255,.75);border-radius:8px;overflow:hidden;background:#000;z-index:3;cursor:pointer;transition:width .2s}
#sv-pip.big{width:min(62%,520px)}#sv-pip img{display:block;width:100%}#sv-pip span{position:absolute;left:4px;top:4px;font:700 10px/1 system-ui,sans-serif;background:rgba(200,0,0,.75);padding:3px 5px;border-radius:4px}
#sv-pip[hidden]{display:none}
#sv-low{display:flex;align-items:center;justify-content:center;gap:14px;padding:10px 12px;background:rgba(8,12,20,.92);border-top:1px solid rgba(255,255,255,.1);flex-wrap:wrap}
#sv-stick{width:132px;height:132px;flex:none;border-radius:50%;position:relative;background:radial-gradient(circle,rgba(255,255,255,.1),rgba(255,255,255,.03));border:2px solid rgba(255,255,255,.3);touch-action:none}
#sv-stick.on{border-color:var(--acc,#3b8cff)}
#sv-stick i{position:absolute;left:50%;top:50%;width:52px;height:52px;margin:-26px 0 0 -26px;border-radius:50%;background:rgba(255,255,255,.85);pointer-events:none}
#sv-stick b{position:absolute;left:0;right:0;bottom:-18px;text-align:center;font-size:11px;font-weight:600;color:#c9d3df}
#sv-btns{display:grid;grid-template-columns:repeat(3,72px);gap:10px}
#sv.land #sv-btns{grid-template-columns:repeat(2,72px)}
#sv .svb{width:72px;height:72px;border-radius:16px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.08);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;padding:0}
#sv .svb span{font-size:26px;line-height:1}#sv .svb small{font-size:11px;font-weight:600;opacity:.9;max-width:68px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#sv .svb.on{background:var(--acc,#3b8cff);border-color:transparent}
#sv .svb.rec{background:#d93636;border-color:transparent}
#sv .svb:disabled{opacity:.35}
#sv .svb.hold:active,#sv .svb.down{background:var(--acc,#3b8cff)}
.sv-sheet{position:absolute;left:0;right:0;bottom:0;z-index:20;max-height:88%;display:flex;flex-direction:column;background:var(--panel,#111822);color:var(--txt,#e8eef5);
  border-radius:18px 18px 0 0;border-top:1px solid rgba(255,255,255,.14);box-shadow:0 -10px 40px rgba(0,0,0,.5);padding-bottom:env(safe-area-inset-bottom,0px)}
.sv-sheet[hidden]{display:none}
.sv-sh{display:flex;align-items:center;gap:10px;padding:14px 16px 8px}.sv-sh h2{margin:0;font-size:19px;flex:1}
.sv-sb{overflow-y:auto;padding:4px 16px 18px;-webkit-overflow-scrolling:touch}
.sv-sb .mut{color:var(--mut,#8b9bb0);font-size:13px;margin:4px 0 10px}
#sv-mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:10px;margin-bottom:14px}
#sv-mgrid .svb{width:auto}
.sv-links{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.sv-links button{min-height:48px;text-align:left;padding:8px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);font-size:15px}
#sv-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:12px}
.sv-card{display:flex;flex-direction:column;gap:6px;text-align:left;padding:10px;border-radius:16px;border:2px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);min-height:100px}
.sv-card:active{border-color:var(--acc,#3b8cff)}
.sv-card img{width:100%;aspect-ratio:16/9;border-radius:10px;display:block;background:#1a2230}
.sv-card b{font-size:18px}.sv-card small{font-size:13.5px;line-height:1.35;color:var(--mut,#a7b3c3);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.sv-card .go{align-self:flex-start;margin-top:4px;font-size:15px;font-weight:700;color:#fff;background:var(--acc,#3b8cff);border-radius:10px;padding:8px 16px}
.sv-card.scene{border-color:var(--acc,#3b8cff)}
#sv-gtop{position:absolute;top:8px;left:50%;transform:translateX(-50%);z-index:4;display:flex;gap:8px;align-items:center;background:rgba(8,12,20,.8);border-radius:14px;padding:6px 12px;font-size:15px;white-space:nowrap;max-width:calc(100% - 16px)}
#sv-gtop[hidden],#sv-gcard[hidden],#sv-gctl[hidden],#sv-ctl[hidden]{display:none}
#sv-gtop .tm{font-size:22px;font-weight:800;font-variant-numeric:tabular-nums}#sv-gtop .tm.hot{color:#ff6b5b}
#sv-gtop .mb{width:70px;height:8px;border-radius:4px;background:rgba(255,255,255,.2);overflow:hidden}#sv-gtop .mb i{display:block;height:100%;background:#3fb950}
#sv-gtop .mb i.w{background:#e8b33a}#sv-gtop .mb i.d{background:#ff5b4b}
#sv-gcard{position:absolute;inset:0;z-index:5;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.45);padding:12px}
#sv-gcard .bx{background:rgba(10,14,20,.95);border-radius:18px;padding:18px 20px;width:min(440px,100%);max-height:100%;overflow:auto;text-align:center}
#sv-gcard h3{margin:0 0 6px;font-size:22px}#sv-gcard p{margin:6px 0;font-size:15px;color:#c9d3df}
#sv-gcard .r{display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.1);text-align:left;font-size:15px}
#sv-gcard .r b{flex:1}#sv-gcard .r .dot{width:12px;height:12px;border-radius:50%;flex:none}
#sv-gcard .big{width:100%;min-height:56px;margin-top:12px;border-radius:14px;border:0;background:var(--acc,#3b8cff);font-size:19px;font-weight:700}
#sv-gcard .sec2{width:100%;min-height:48px;margin-top:8px;border-radius:14px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.07);font-size:16px}
#sv-gctl{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%}
#sv.land #sv-gctl{flex-direction:column;justify-content:center;gap:26px}#sv.game #sv-low{padding-bottom:28px}
.sv-gs{width:124px;height:124px;flex:none;border-radius:50%;position:relative;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.3);touch-action:none}
.sv-gs i{position:absolute;left:50%;top:50%;width:48px;height:48px;margin:-24px 0 0 -24px;border-radius:50%;background:rgba(255,255,255,.85);pointer-events:none}
.sv-gs b{position:absolute;left:0;right:0;bottom:-18px;text-align:center;font-size:11px;font-weight:600;color:#c9d3df}
#sv-gb{display:grid;grid-template-columns:repeat(3,66px);gap:8px}
#sv-gb .svb{width:66px;height:62px}
#sv:not(.land) #sv-gctl{flex-wrap:wrap;justify-content:space-around;row-gap:12px}
#sv:not(.land) #sv-gb{order:-1;width:100%;grid-template-columns:repeat(6,minmax(0,62px));justify-content:center}
#sv:not(.land) #sv-gb .svb{width:auto;height:58px}#sv-gb .svb small{font-size:10.5px}
@media (max-width:380px){#sv-btns{grid-template-columns:repeat(3,64px)}#sv .svb{width:64px;height:64px}#sv-stick{width:116px;height:116px}#sv-gb{grid-template-columns:repeat(3,58px)}#sv-gb .svb{width:58px}.sv-gs{width:108px;height:108px}}
@media (max-height:430px){#sv .svb{width:60px;height:56px}#sv .svb span{font-size:22px}#sv-btns,#sv.land #sv-btns{grid-template-columns:repeat(3,60px);gap:6px}#sv-stick{width:110px;height:110px}
  .sv-gs{width:100px;height:100px}#sv-gb .svb{width:56px;height:50px}#sv-gb{grid-template-columns:repeat(3,56px);gap:6px}#sv .svt{height:38px}}
body.sv-on{overflow:hidden}body.sv-on #lv-side,body.sv-on #lv-tools,body.sv-on #lv-editbar,body.sv-on #lv-menu{display:none!important}   /* the floating parts of the usual live screen (536): only there */
@media (max-width:560px){#sv-top .sv-nm{display:none}#sv-top .svt .lb{display:none}#sv-top{gap:6px;padding:6px 8px}#sv .svt{padding:0 10px}}
#sv-back{margin:0 0 8px;width:100%;min-height:44px}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*SIMVDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const B = (cls, ic, lb) => { const b = E("button", cls); b.type = "button"; if (ic != null) b.append(E("span", "", ic)); if (lb != null) b.append(E("small", "", lb)); return b; };
  const P = (u, d) => (typeof post === "function" ? post(u, d) : fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)}).then(r => r.json())).catch(() => null);
  const say = m => { try { toast(m); } catch (e) {} };
  const LS = {get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} }};
  const SV = {open: false, klass: LS.get("mw-simv") === "klassisch", sticks: false, game: false, role: "runner", gi: null, poll: null, VP: null, VB: null, pipT: null};
  window.SIMV = SV;

  // ---- the layer ----
  const R = E("div"); R.id = "sv"; R.hidden = true;
  const top = E("div"); top.id = "sv-top";
  const chip = E("span"); chip.id = "sv-chip";
  const bPlay = E("button", "svt pri", "🎮 " + T("Let’s play")); bPlay.type = "button"; bPlay.id = "sv-play";
  const lbB = (ic, tx) => { const b = E("button", "svt"); b.type = "button"; b.append(ic + " ", E("span", "lb", tx)); b.title = tx; return b; };
  const bMore = lbB("⋯", T("More")); bMore.id = "sv-more-b";
  const bKl = lbB("▦", T("Classic")); bKl.id = "sv-klass"; bKl.title = T("Back to the usual live screen");
  top.append(E("span", "sv-nm", "MoveEye Sim"), chip, E("span", "sv-sp"), bPlay, bMore, bKl);
  const stage = E("div", "fs"); stage.id = "sv-stage";
  const img = E("img"); img.id = "sv-img"; img.alt = ""; img.draggable = false; img.tabIndex = 0; img.dataset.dock = "1";
  const wait = E("div", "", T("Waiting for the picture of the simulator …")); wait.id = "sv-wait";
  const pip = E("div"); pip.id = "sv-pip"; pip.title = T("Camera picture of MoveEye (tap: bigger / smaller)");
  const pimg = E("img"); pimg.alt = ""; pip.append(pimg, E("span", "", "📷 LIVE"));
  const gtop = E("div"); gtop.id = "sv-gtop"; gtop.hidden = true;
  const gcard = E("div"); gcard.id = "sv-gcard"; gcard.hidden = true;
  stage.append(img, wait, pip, gtop, gcard);
  const low = E("div"); low.id = "sv-low";
  // normal: head stick + the big buttons
  const ctl = E("div"); ctl.id = "sv-ctl"; ctl.style.cssText = "display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap";
  const stick = E("div"); stick.id = "sv-stick"; stick.setAttribute("role", "application"); stick.setAttribute("aria-label", T("Head")); stick.append(E("i"), E("b", "", "🎥 " + T("Head")));
  const btns = E("div"); btns.id = "sv-btns";
  ctl.append(stick, btns);
  // game: two sticks and the buttons of the role
  const gctl = E("div"); gctl.id = "sv-gctl"; gctl.hidden = true;
  const gsL = E("div", "sv-gs"); gsL.append(E("i"), E("b", "", T("walk")));
  const gsR = E("div", "sv-gs"); gsR.append(E("i"), E("b", "", T("look around")));
  const gb = E("div"); gb.id = "sv-gb";
  gctl.append(gsL, gb, gsR);
  low.append(ctl, gctl);
  // sheets: «⋯ Mehr» and the game choice
  const sheet = (id, title) => { const s = E("div", "sv-sheet"); s.id = id; s.hidden = true; const h = E("div", "sv-sh"); h.append(E("h2", "", title));
    const x = E("button", "svt", "✕"); x.type = "button"; x.setAttribute("aria-label", "close"); x.onclick = () => { s.hidden = true; }; h.append(x);
    const b = E("div", "sv-sb"); s.append(h, b); return [s, b, h]; };
  const [mS, mB] = sheet("sv-more", "⋯ " + T("More"));
  const [pS, pB, pH] = sheet("sv-pick", "🎮 " + T("What do you want to play?"));
  const bAdj = E("button", "svt", "⚙ " + T("Customise")); bAdj.type = "button"; bAdj.title = T("The whole game wizard (all rules and extras)");
  pH.insertBefore(bAdj, pH.lastChild);
  R.append(top, stage, low, mS, pS);
  document.body.appendChild(R);

  // ---- the stream of the simulator window: the same functions as the window on the live page / page Simulator (470) ----
  try {
    SV.VP = simViewPoll(img, 10);
    SV.VB = simViewBind(img, {ctl: () => true, active: () => SV.open && !SV.game});
    simTouchPad(stage, SV.VB, () => SV.open && !SV.game && (SV.sticks || !!SV.story));
  } catch (e) {}
  img.addEventListener("load", () => { wait.hidden = true; });
  pip.onclick = () => pip.classList.toggle("big");
  const pipTick = () => { clearTimeout(SV.pipT); if (!SV.open || document.hidden) return;
    const n = new Image(); n.onload = () => { pimg.src = n.src; SV.pipT = setTimeout(pipTick, 700); }; n.onerror = () => { SV.pipT = setTimeout(pipTick, 2000); };
    n.src = "/snapshot.jpg?r=" + Date.now(); };

  // ---- the big buttons: the same switches as the live page (530 QS) ----
  const QSA = id => (typeof QS !== "undefined" ? QS : []).find(q => q.id === id);
  const BIG = [["track", "🎯", "Follow"], ["ir", "🔴", "IR light"], ["white", "💡", "Spotlight"], ["siren", "🚨", "Siren"], ["rec", "⏺", "Recording"]];
  const bigB = {};
  BIG.forEach(([id, ic, lb]) => { const b = B("svb", ic, T(lb)); b.id = "sv-b-" + id; bigB[id] = b; btns.appendChild(b);
    b.onclick = async () => { const J = typeof QSJ !== "undefined" ? QSJ : null; if (!J) return; b.disabled = true; let r = null;
      if (id === "siren") { const on = !!(J.state.audio && J.state.audio.playing); r = await P("/api/audio", {action: on ? "stop" : "siren", lang: LANG}); }
      else { const q = QSA(id); if (q) r = await q.go(J.cfg, J.state); }
      b.disabled = false; if (r && r.ok === false) say("⚠ " + (r.error || "error")); try { refresh(); } catch (e) {} }; });
  const paintBig = () => { const J = typeof QSJ !== "undefined" ? QSJ : null; if (!J) return; const c = J.cfg || {}, s = J.state || {};
    BIG.forEach(([id]) => { const b = bigB[id]; if (id === "siren") { b.classList.toggle("on", !!(s.audio && s.audio.playing)); b.disabled = false; return; }
      const q = QSA(id); if (!q) { b.disabled = true; return; } const on = !!q.on(c, s); b.classList.toggle(q.cls || "on", on);
      const ok = q.ok ? q.ok(c, s) : true; b.disabled = !ok; b.title = T(q.tip) + (ok ? "" : " – " + T("not connected")); });
    const armed = s.arm_state === "armed" || s.arm_state === "arming", lv = s.protect_level || c.protect_level || "watch";
    chip.textContent = "🛡 " + (armed ? T(lv === "full" ? "Full" : "Alert") : T("Off")) + (s.persons ? " · 🚶 " + s.persons : "");
    chip.className = s.persons ? "alarm" : armed ? "on" : ""; };

  // ---- the head stick: like the joystick of the live page (/api/stick, ~10 × per second) ----
  (function () { let id = null, vx = 0, vy = 0, ox = 0, oy = 0, tm = null, busy = false; const kn = stick.querySelector("i");
    const send = () => { if (busy) return; busy = true; const sp = document.getElementById("stick-speed");
      P("/api/stick", {x: vx, y: vy, speed: sp ? parseFloat(sp.value) : 30}).then(() => { busy = false; }); };
    const track = e => { const Rr = stick.clientWidth / 2 - 26; let dx = e.clientX - ox, dy = e.clientY - oy; const m = Math.hypot(dx, dy);
      if (m > Rr) { dx *= Rr / m; dy *= Rr / m; } kn.style.transform = "translate(" + dx + "px," + dy + "px)";
      const dz = Rr * 0.12, mm = Math.min(m, Rr), k = mm <= dz ? 0 : (mm - dz) / (Rr - dz) / (mm || 1) * Rr;
      vx = Math.round(dx * k / Rr * 1000) / 1000; vy = Math.round(-dy * k / Rr * 1000) / 1000; };
    const rel = () => { if (id === null) return; id = null; vx = vy = 0; clearInterval(tm); stick.classList.remove("on"); kn.style.transform = ""; busy = false; send(); };
    stick.addEventListener("pointerdown", e => { if (id !== null) return; e.preventDefault(); id = e.pointerId; try { stick.setPointerCapture(id); } catch (x) {}
      ox = e.clientX; oy = e.clientY; stick.classList.add("on"); track(e); busy = false; send(); tm = setInterval(send, 100); });
    stick.addEventListener("pointermove", e => { if (e.pointerId === id) { e.preventDefault(); track(e); } });
    ["pointerup", "pointercancel", "lostpointercapture"].forEach(n => stick.addEventListener(n, e => { if (e.pointerId === id) rel(); }));
    stick.addEventListener("dblclick", () => { try { move("center"); } catch (e) {} });
  })();

  // ---- «⋯ Mehr»: every quick switch of the live page (same order) + the other screens - nothing is left out ----
  function moreBuild() {
    mB.textContent = ""; const J = typeof QSJ !== "undefined" ? QSJ : null;
    mB.append(E("div", "mut", T("All switches of the live screen. Tap «▦ Classic» for the complete usual live screen.")));
    const g = E("div"); g.id = "sv-mgrid";
    let L = []; try { L = qsArrange(qsList(J), J && J.cfg, true); } catch (e) {}
    L.forEach(q => { const o = document.getElementById("qs-" + q.id), b = B("svb", q.ic, q.raw ? q.lb : T(q.lb)); b.title = T(q.tip || "");
      if (J) { try { const ok = q.ok ? q.ok(J.cfg, J.state) : true; b.disabled = !ok; if (q.on(J.cfg, J.state)) b.classList.add(q.cls || "on"); } catch (e) {} }
      b.onclick = () => { if (q.talk) { klass(true); say("🎙 " + T("Talk: hold the button on the usual live screen")); return; }
        if (o) o.click(); else if (q.go && J) q.go(J.cfg, J.state); setTimeout(moreBuild, 900); };
      g.appendChild(b); });
    mB.appendChild(g);
    const lk = E("div", "sv-links"), add = (tx, f) => { const b = E("button", "", tx); b.type = "button"; b.onclick = f; lk.appendChild(b); };
    add("▦ " + T("Classic live screen (everything)"), () => klass(true));
    add("🕹 " + T("Sticks fly / look around") + (SV.sticks ? " ✓" : ""), () => { SV.sticks = !SV.sticks; LS.set("mw-simv-sticks", SV.sticks ? "1" : "0"); moreBuild(); });
    if (typeof window.pvOpen === "function") add("🎮 " + T("Controller view"), () => { mS.hidden = true; window.pvOpen(true); });
    add("🧪 " + T("Simulator (tab)"), () => { location.href = "/sim"; });
    add("📖 " + T("Stories and places"), () => { location.href = "/play"; });
    add("🛡 " + T("Protection"), () => { location.href = "/protect"; });
    add("🕘 " + T("History"), () => { location.href = "/recordings"; });
    add("⚙ " + T("Settings"), () => { location.href = "/settings"; });
    add("☰ " + T("More (tab)"), () => { location.href = "/more"; });
    mB.append(E("div", "mut", T("Screens")), lk);
  }
  bMore.onclick = () => { pS.hidden = true; moreBuild(); mS.hidden = !mS.hidden; };

  // ---- «🎮 Spielen»: the games of the wizard (gamewiz «quick») as big cards - one tap = play ----
  async function wiz(o) { return P("/api/sim", Object.assign({action: "gamewiz", lang: LANG}, o)); }
  async function pickOpen() {
    mS.hidden = true; pS.hidden = false; pB.textContent = ""; pB.append(E("div", "mut", "⏳ " + T("loading the games …")));
    let r = await wiz({op: "get"});
    for (let i = 0; i < 3 && r && r.ok !== false && !(r.quick || []).length && !r.shown && r.step > 0; i++) r = await wiz({op: "back"});   // the wizard at step 0 (hidden: nobody sees it)
    pB.textContent = "";
    if (!r || r.ok === false) { pB.append(E("div", "mut", "⚠ " + ((r && r.error) || T("simulator not reachable")))); return; }
    if (!(r.quick || []).length) { pB.append(E("div", "mut", T("The game wizard is open at the simulator PC. «⚙ Customise» shows it here."))); return; }
    pB.append(E("div", "mut", T("One tap: everything is set (3 minutes, good rules) and you play here with the buttons. «⚙ Customise» for your own rules.")));
    const g = E("div"); g.id = "sv-cards";
    r.quick.forEach(q => { const c = E("button", "sv-card" + (q.scene ? " scene" : "")); c.type = "button";
      if (q.pic) { const im = E("img"); im.alt = ""; im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(q.pic); c.appendChild(im); }
      c.append(E("b", "", (q.icon ? q.icon + " " : "") + q.title), E("small", "", q.text || ""), E("span", "go", "▶ " + T("Let’s play")));
      c.onclick = () => play(q.v, c); g.appendChild(c); });
    pB.appendChild(g);
  }
  bPlay.onclick = () => { if (!pS.hidden) { pS.hidden = true; return; } pickOpen(); };
  bAdj.onclick = () => { location.href = "/sim#gw"; };
  async function play(v, card) {
    if (card) card.disabled = true;
    try {
      const r = await wiz({op: "quick", value: v});
      if (!r || r.ok === false) { say("⚠ " + ((r && r.error) || T("simulator not reachable"))); return; }
      pS.hidden = true;
      if (v === "abenteuer" || v === "escape_quick") { SV.sticks = true; say("▶ " + T("It starts in the simulator window – walk with the sticks.")); return; }   // a story / the parcours: in the window
      const l = await P("/api/sim", {action: "ctl", ctl: "press", id: "game_local", lang: LANG});              // «Hier am PC mitspielen» (localplay.gd)
      if (!l || l.ok === false) { say("⚠ " + ((l && l.error) || T("not possible"))); return; }
      await wiz({op: "next"});                                                                              // step 4: the round starts
      gameOn(true); say("▶ " + T("The round starts"));
    } finally { if (card) card.disabled = false; }
  }

  // ---- in the game: the buttons are a game controller at the browser (/api/sim «pad», padmap.gd) ----
  const PAD = {ax: [0, 0, 0, 0], bt: new Array(17).fill(0), hold: {}, busy: false, last: 0, sig: ""};
  const WB = {a: 0, b: 1, x: 2, y: 3, l1: 4, r1: 5, l2: 6, r2: 7, select: 8, start: 9, l3: 10, r3: 11};
  function padSend(force) {
    if (PAD.busy) return; const now = Date.now();
    const neutral = PAD.ax.every(v => Math.abs(v) < 0.05) && PAD.bt.every(v => !v), sig = JSON.stringify([PAD.ax.map(v => Math.round(v * 40)), PAD.bt]);
    if (!force && neutral && sig === PAD.sig) return;
    if (!force && sig === PAD.sig && now - PAD.last < 300) return;
    PAD.busy = true; PAD.sig = sig; PAD.last = now;
    P("/api/sim", {action: "pad", ax: PAD.ax.slice(), bt: PAD.bt.slice(), name: "Touch (MoveEye)"}).then(() => { PAD.busy = false; });
  }
  setInterval(() => { if (SV.game) padSend(false); }, 70);
  const tap = k => { PAD.bt[WB[k]] = 1; padSend(true); setTimeout(() => { PAD.bt[WB[k]] = 0; }, 220); };
  const hold = (b, k) => { b.classList.add("hold");
    b.addEventListener("pointerdown", e => { e.preventDefault(); try { b.setPointerCapture(e.pointerId); } catch (x) {} b.classList.add("down"); PAD.bt[WB[k]] = 1; padSend(true); });
    ["pointerup", "pointercancel"].forEach(n => b.addEventListener(n, () => { b.classList.remove("down"); PAD.bt[WB[k]] = 0; })); };
  const gstick = (el, i) => { const kn = el.querySelector("i"); let id = null;
    const at = e => { const r = el.getBoundingClientRect(); let x = (e.clientX - r.left) / r.width * 2 - 1, y = (e.clientY - r.top) / r.height * 2 - 1;
      const m = Math.hypot(x, y); if (m > 1) { x /= m; y /= m; } kn.style.transform = "translate(" + x * 70 + "%," + y * 70 + "%)"; PAD.ax[i] = Math.round(x * 100) / 100; PAD.ax[i + 1] = Math.round(y * 100) / 100; };
    el.addEventListener("pointerdown", e => { e.preventDefault(); id = e.pointerId; try { el.setPointerCapture(id); } catch (x) {} at(e); padSend(true); });
    el.addEventListener("pointermove", e => { if (e.pointerId === id) { e.preventDefault(); at(e); } });
    const end = e => { if (e.pointerId !== id) return; id = null; kn.style.transform = ""; PAD.ax[i] = PAD.ax[i + 1] = 0; padSend(true); };
    ["pointerup", "pointercancel"].forEach(n => el.addEventListener(n, end)); };
  gstick(gsL, 2); gstick(gsR, 0);                                    // padmap «runner»: right stick = walk, left stick = look around
  const GB_RUN = [["b", "🧎", "Crouch"], ["y", "🐍", "Crawl"], ["x", "🪨", "Stone"], ["a", "🔦", "Torch"], ["r2", "🏃", "Run", 1], ["select", "🎬", "Replay"]];
  const GB_GUARD = [["r2", "🎯", "Shutter"], ["x", "✋", "Caught!"], ["a", "💡", "Spotlight"], ["b", "📡", "Radar scan"], ["y", "📢", "Siren"], ["l1", "🔍", "Zoom"]];
  function gbBuild() { gb.textContent = ""; (SV.role === "guard" ? GB_GUARD : GB_RUN).forEach(([k, ic, lb, h]) => { const b = B("svb", ic, T(lb));
    if (h) hold(b, k); else b.onclick = () => tap(k); gb.appendChild(b); });
    gsL.querySelector("b").textContent = T(SV.role === "guard" ? "aim finely" : "walk"); gsR.querySelector("b").textContent = T(SV.role === "guard" ? "turn the camera" : "look around"); }
  const bEnd = E("button", "svt", "× " + T("Quit")); bEnd.type = "button"; bEnd.id = "sv-quit";
  const bAdj2 = E("button", "svt", "⚙"); bAdj2.type = "button"; bAdj2.title = T("Customise"); bAdj2.onclick = () => { location.href = "/sim#gw"; };
  bEnd.onclick = async () => { bEnd.disabled = true; await P("/api/sim", {action: "localplay", do: "stop", lang: LANG}); bEnd.disabled = false; gameOn(false); };
  function gameOn(on) {
    SV.game = on; R.classList.toggle("game", on); gctl.hidden = !on; ctl.hidden = on; gtop.hidden = !on; bEnd.hidden = !on; bAdj2.hidden = !on;
    bPlay.hidden = on; bMore.hidden = on; bKl.hidden = on; pip.hidden = on;
    if (!on) { gcard.hidden = true; PAD.ax = [0, 0, 0, 0]; PAD.bt.fill(0); } else gbBuild();
    clearTimeout(SV.poll); if (on) gamePoll();
  }
  top.insertBefore(bAdj2, bKl); top.insertBefore(bEnd, bKl); bEnd.hidden = bAdj2.hidden = true;
  const mmss = n => Math.floor(n / 60) + ":" + ("0" + (n % 60)).slice(-2);
  async function gamePoll() {
    clearTimeout(SV.poll); if (!SV.game) return;
    const g = await P("/api/sim", {action: "game", lang: LANG}); SV.gi = g;
    if (g && g.ok !== false) gamePaint(g);
    SV.poll = setTimeout(gamePoll, g && ["countdown", "play"].includes(g.round) ? 700 : 1500);
  }
  let GSIG = "";
  function gamePaint(g) {
    const me = (g.players || []).find(p => p.n === "Ich (PC)") || null;
    if (!g.open || !me) { if (SV.gi_off = (SV.gi_off || 0) + 1, SV.gi_off > 3) gameOn(false); return; }
    SV.gi_off = 0;
    const role = me.r === "guard" ? "guard" : "runner"; if (role !== SV.role) { SV.role = role; gbBuild(); }
    gtop.textContent = "";
    const tm = E("span", "tm" + (g.round === "play" && g.left <= 30 ? " hot" : ""), g.round === "play" ? mmss(g.left || 0) : g.round === "countdown" ? String(g.cd || "") : "–");
    gtop.append(tm);
    if (role === "runner") { const mb = E("span", "mb"), i = E("i", me.susp > 75 ? "d" : me.susp > 40 ? "w" : ""); i.style.width = Math.max(0, Math.min(100, me.susp || 0)) + "%"; mb.appendChild(i);
      gtop.append(E("span", "", "👁"), mb); }
    gtop.append(E("span", "", (me.k ? "🔒 " + me.k + " · " : "") + (g.items_all ? "💎 " + me.i + " · " : "") + (role === "guard" ? "👮 " + T("Guard") : "🏃 " + T("Sneaker"))));
    const sig = g.round + "|" + (g.round === "end" ? JSON.stringify(g.res || []) : "");
    if (sig === GSIG) return; GSIG = sig;
    gcard.textContent = ""; gcard.hidden = !(g.round === "lobby" || g.round === "end");
    if (gcard.hidden) return;
    const bx = E("div", "bx");
    if (g.round === "lobby") {
      bx.append(E("h3", "", "🎮 " + T("Ready?")), E("p", "", role === "guard" ? T("You are the guard: turn the camera and catch them") : T("Sneak unseen to the green light – the arrow shows the way.")));
      if (g.url) bx.append(E("p", "", "📱 " + T("More players: open on the phone") + " " + g.url));
    } else {
      bx.append(E("h3", "", "🏁 " + T("Round over")));
      (g.res || []).slice(0, 8).forEach(x => { const r = E("div", "r"), d = E("span", "dot"); d.style.background = x.c || "#888";
        r.append(d, E("b", "", x.n || ""), E("span", "", String(x.score != null ? x.score : ""))); if (x.info) r.title = x.info; bx.appendChild(r); });
    }
    const go = E("button", "big", "▶ " + T(g.round === "end" ? "Play again" : "Start the round")); go.type = "button"; go.onclick = () => { tap("start"); gcard.hidden = true; GSIG = ""; };
    bx.appendChild(go);
    if (g.round === "end") { const rp = E("button", "sec2", "🎬 " + T("Replay")); rp.type = "button"; rp.onclick = () => { tap("select"); gcard.hidden = true; }; bx.appendChild(rp); }
    const other = E("button", "sec2", "🎮 " + T("Another game")); other.type = "button";
    other.onclick = async () => { await P("/api/sim", {action: "localplay", do: "stop", lang: LANG}); gameOn(false); pickOpen(); }; bx.appendChild(other);
    gcard.appendChild(bx);
  }

  // ---- open / close: only in simulator operation, only on the live tab, not over the controller view ----
  function klass(on) { SV.klass = on; LS.set("mw-simv", on ? "klassisch" : "sim"); tick(); }
  bKl.onclick = () => klass(true);
  SV.sticks = LS.get("mw-simv-sticks") === "1";
  function land() { R.classList.toggle("land", innerWidth > innerHeight * 1.15); }
  addEventListener("resize", land); land();
  async function tick() {
    const J = typeof QSJ !== "undefined" ? QSJ : null, S_ = J && J.state && J.state.sim;
    const now = Date.now(); let sim = !!(S_ && S_.on && S_.ok);
    if (sim) SV.okT = now; else if (S_ && S_.on && SV.open && now - (SV.okT || 0) < 10000) sim = true;   // a short hiccup (the simulator builds a scene): stay
    const want = sim && !SV.klass && !document.body.classList.contains("pv-on");
    backBtn(sim && SV.klass);
    if (want !== SV.open) {
      SV.open = want; R.hidden = !want; document.body.classList.toggle("sv-on", want);
      if (want) { try { scrollTo(0, 0); } catch (e) {} wait.hidden = false; if (SV.VP) SV.VP.start(); pipTick(); land();
        const l = await P("/api/sim", {action: "localplay", do: "get", lang: LANG}); if (l && l.active && !SV.game) gameOn(true); }   // a game of this device after a reload
      else { if (SV.VP) SV.VP.stop(); img.removeAttribute("src"); mS.hidden = pS.hidden = true; if (SV.game) gameOn(false); }
    }
    if (want) { const sb = document.querySelector(".mwsimbar"); R.style.top = (sb && !sb.hidden ? Math.max(0, Math.round(sb.getBoundingClientRect().bottom)) : 0) + "px";   // the stripe «SIMULATION» stays visible
      paintBig(); if (!document.hidden && S_.view === false) wait.textContent = T("This simulator does not send its window (update the simulator)."); }
  }
  // a story playing (Maggie, Grossvater): the sticks «gehen / umschauen» come by themselves (470 simTouchPad)
  setInterval(async () => { if (!SV.open || SV.game || document.hidden) return; const j = await fetch("/api/play", {cache: "no-store"}).then(x => x.ok ? x.json() : null).catch(() => null);
    SV.story = !!(j && !j.offline && j.playing); }, 4000);
  function backBtn(show) {                         // on the usual live screen: the way back (card «Simulator-Steuerung»)
    let b = document.getElementById("sv-back"); const w = document.getElementById("lv-simw");
    if (!b && w && show) { b = E("button", "", "📱 " + T("Sim view") + " · 🎮 " + T("Let’s play")); b.type = "button"; b.id = "sv-back"; b.onclick = () => klass(false); w.insertBefore(b, w.firstChild); }
    if (b) b.hidden = !show;
  }
  document.addEventListener("visibilitychange", () => { if (!SV.open) return; if (document.hidden) { if (SV.VP) SV.VP.stop(); } else { if (SV.VP) SV.VP.start(); pipTick(); } });
  setInterval(tick, 1000); setTimeout(tick, 600);
})();
</script>
"""

# Key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_SIMV = {
    'Let’s play': ('Spielen', 'Jouer', 'Gioca', 'Giugar'),
    'More': ('Mehr', 'Plus', 'Altro', 'Dapli'),
    'Classic': ('Klassisch', 'Classique', 'Classico', 'Classic'),
    'Back to the usual live screen': ('Zurück zur gewohnten Live-Seite', 'Retour à l’écran live habituel', 'Torna alla solita schermata live',
                                      'Enavos al visur live usità'),
    'Waiting for the picture of the simulator …': ('Warte auf das Bild des Simulators …', 'En attente de l’image du simulateur …',
                                                    'In attesa dell’immagine del simulatore …', 'Spetg sin il maletg dal simulatur …'),
    'Camera picture of MoveEye (tap: bigger / smaller)': ('Kamerabild von MoveEye (antippen: grösser / kleiner)', 'Image caméra de MoveEye (toucher : plus grand / plus petit)',
                                                          'Immagine della telecamera di MoveEye (tocca: più grande / più piccola)', 'Maletg da la camera da MoveEye (tutgar: pli grond / pli pitschen)'),
    'Head': ('Kopf', 'Tête', 'Testa', 'Chau'),
    'walk': ('gehen', 'marcher', 'camminare', 'ir'),
    'look around': ('umschauen', 'regarder autour', 'guardarsi intorno', 'guardar enturn'),
    'aim finely': ('fein zielen', 'viser finement', 'mirare fine', 'mirar fin'),
    'turn the camera': ('Kamera drehen', 'tourner la caméra', 'girare la telecamera', 'volver la camera'),
    'What do you want to play?': ('Was willst du spielen?', 'À quoi veux-tu jouer ?', 'A cosa vuoi giocare?', 'Tge vuls ti giugar?'),
    'Customise': ('Anpassen', 'Personnaliser', 'Personalizza', 'Adattar'),
    'The whole game wizard (all rules and extras)': ('Der ganze Spiel-Assistent (alle Regeln und Extras)', 'L’assistant de jeu complet (toutes les règles et options)',
                                                     'L’assistente di gioco completo (tutte le regole e gli extra)', 'L’entir assistent da gieu (tut las reglas ed extras)'),
    'Follow': ('Folgen', 'Suivre', 'Seguire', 'Suandar'),
    'IR light': ('IR-Licht', 'Lumière IR', 'Luce IR', 'Glisch IR'),
    'Spotlight': ('Licht', 'Lumière', 'Luce', 'Glisch'),
    'Siren': ('Sirene', 'Sirène', 'Sirena', 'Sirena'),
    'Recording': ('Aufnahme', 'Enregistrement', 'Registrazione', 'Registraziun'),
    'Full': ('Voll', 'Complet', 'Pieno', 'Cumplain'),
    'Alert': ('Wachsam', 'Vigilant', 'Vigile', 'Attent'),
    'Off': ('Aus', 'Arrêt', 'Spento', 'Giu'),
    'not connected': ('nicht angeschlossen', 'non connecté', 'non collegato', 'betg collià'),
    'All switches of the live screen. Tap «▦ Classic» for the complete usual live screen.': (
        'Alle Schalter der Live-Seite. «▦ Klassisch» zeigt die ganze gewohnte Live-Seite.',
        'Tous les interrupteurs de l’écran live. «▦ Classique» montre tout l’écran live habituel.',
        'Tutti gli interruttori della schermata live. «▦ Classico» mostra tutta la solita schermata live.',
        'Tut ils interruttus dal visur live. «▦ Classic» mussa l’entir visur live usità.'),
    'Talk: hold the button on the usual live screen': ('Sprechen: auf der gewohnten Live-Seite den Knopf gedrückt halten',
                                                      'Parler : maintenir le bouton sur l’écran live habituel',
                                                      'Parlare: tenere premuto il pulsante nella solita schermata live',
                                                      'Discurrer: tegnair smatgà il buttun sin il visur live usità'),
    'Classic live screen (everything)': ('Klassische Live-Seite (alles)', 'Écran live classique (tout)', 'Schermata live classica (tutto)', 'Visur live classic (tut)'),
    'Sticks fly / look around': ('Sticks fliegen / umschauen', 'Sticks voler / regarder autour', 'Stick volare / guardarsi intorno', 'Sticks sgular / guardar enturn'),
    'Controller view': ('Controller-Ansicht', 'Vue manette', 'Vista controller', 'Vista dal controller'),
    'Simulator (tab)': ('Simulator (Reiter)', 'Simulateur (onglet)', 'Simulatore (scheda)', 'Simulatur (register)'),
    'Stories and places': ('Geschichten und Orte', 'Histoires et lieux', 'Storie e luoghi', 'Istorgias e lieus'),
    'Protection': ('Schutz', 'Protection', 'Protezione', 'Protecziun'),
    'Settings': ('Einstellungen', 'Réglages', 'Impostazioni', 'Parameters'),
    'History': ('Verlauf', 'Historique', 'Cronologia', 'Cronologia'),
    'More (tab)': ('Mehr (Reiter)', 'Plus (onglet)', 'Altro (scheda)', 'Dapli (register)'),
    'Screens': ('Ansichten', 'Écrans', 'Schermate', 'Visurs'),
    'loading the games …': ('lade die Spiele …', 'chargement des jeux …', 'caricamento dei giochi …', 'chargia ils gieus …'),
    'simulator not reachable': ('Simulator nicht erreichbar', 'simulateur injoignable', 'simulatore non raggiungibile', 'simulatur betg cuntanschibel'),
    'The game wizard is open at the simulator PC. «⚙ Customise» shows it here.': (
        'Der Spiel-Assistent ist am Simulator-PC offen. «⚙ Anpassen» zeigt ihn hier.',
        'L’assistant de jeu est ouvert sur le PC du simulateur. «⚙ Personnaliser» l’affiche ici.',
        'L’assistente di gioco è aperto sul PC del simulatore. «⚙ Personalizza» lo mostra qui.',
        'L’assistent da gieu è avert al PC dal simulatur. «⚙ Adattar» al mussa qua.'),
    'One tap: everything is set (3 minutes, good rules) and you play here with the buttons. «⚙ Customise» for your own rules.': (
        'Ein Tipp: alles ist eingestellt (3 Minuten, gute Regeln) und du spielst hier mit den Knöpfen. «⚙ Anpassen» für eigene Regeln.',
        'Un toucher : tout est réglé (3 minutes, bonnes règles) et tu joues ici avec les boutons. «⚙ Personnaliser» pour tes propres règles.',
        'Un tocco: è tutto impostato (3 minuti, buone regole) e giochi qui con i pulsanti. «⚙ Personalizza» per regole proprie.',
        'In tip: tut è endrizzà (3 minutas, bunas reglas) e ti giogas qua cun ils buttuns. «⚙ Adattar» per atgnas reglas.'),
    'It starts in the simulator window – walk with the sticks.': ('Es startet im Simulator-Fenster – mit den Sticks gehen.',
                                                                 'Ça démarre dans la fenêtre du simulateur – marche avec les sticks.',
                                                                 'Parte nella finestra del simulatore – cammina con gli stick.',
                                                                 'I cumenza en la fanestra dal simulatur – ir cun ils sticks.'),
    'not possible': ('nicht möglich', 'impossible', 'non possibile', 'betg pussaivel'),
    'The round starts': ('Die Runde startet', 'La manche commence', 'Il round inizia', 'La runda cumenza'),
    'Crouch': ('Ducken', 'Se baisser', 'Abbassarsi', 'Sa sbassar'),
    'Crawl': ('Kriechen', 'Ramper', 'Strisciare', 'Ruschnar'),
    'Stone': ('Stein', 'Pierre', 'Sasso', 'Crap'),
    'Torch': ('Lampe', 'Lampe', 'Lampada', 'Lampa'),
    'Run': ('Rennen', 'Courir', 'Correre', 'Currer'),
    'Replay': ('Wiederholung', 'Ralenti', 'Replay', 'Repetiziun'),
    'Shutter': ('Auslöser', 'Déclencheur', 'Scatto', 'Deliberader'),
    'Caught!': ('Erwischt!', 'Attrapé !', 'Preso!', 'Tschiffà!'),
    'Radar scan': ('Scan', 'Scan', 'Scansione', 'Scan'),
    'Zoom': ('Zoom', 'Zoom', 'Zoom', 'Zoom'),
    'Quit': ('Beenden', 'Quitter', 'Esci', 'Terminar'),
    'Guard': ('Wächter', 'Gardien', 'Guardiano', 'Guardian'),
    'Sneaker': ('Schleicher', 'Furtif', 'Furtivo', 'Furtiv'),
    'Ready?': ('Bereit?', 'Prêt ?', 'Pronto?', 'Pront?'),
    'You are the guard: turn the camera and catch them': ('Du bist Wächter: Kamera drehen und erwischen', 'Tu es le gardien : tourne la caméra et attrape-les',
                                                          'Sei il guardiano: gira la telecamera e prendili', 'Ti es il guardian: volva la camera e tschiffa els'),
    'Sneak unseen to the green light – the arrow shows the way.': ('Schleich ungesehen zum grünen Licht – der Pfeil zeigt den Weg.',
                                                                   'Faufile-toi sans être vu jusqu’à la lumière verte – la flèche montre le chemin.',
                                                                   'Arriva di nascosto alla luce verde – la freccia mostra la strada.',
                                                                   'Sa zuppa fin tar la glisch verda – la frizza mussa la via.'),
    'More players: open on the phone': ('Weitere Spieler: auf dem Handy öffnen', 'Autres joueurs : ouvrir sur le portable', 'Altri giocatori: apri sul telefono',
                                        'Ulteriurs giugaders: avrir sin il telefonin'),
    'Round over': ('Runde vorbei', 'Manche terminée', 'Round finito', 'Runda terminada'),
    'Play again': ('Nochmals spielen', 'Rejouer', 'Gioca ancora', 'Giugar anc ina giada'),
    'Start the round': ('Runde starten', 'Lancer la manche', 'Avvia il round', 'Cumenzar la runda'),
    'Another game': ('Anderes Spiel', 'Autre jeu', 'Altro gioco', 'Auter gieu'),
    'This simulator does not send its window (update the simulator).': ('Dieser Simulator schickt sein Fenster nicht (Simulator aktualisieren).',
                                                                         'Ce simulateur n’envoie pas sa fenêtre (mettre à jour le simulateur).',
                                                                         'Questo simulatore non invia la sua finestra (aggiorna il simulatore).',
                                                                         'Quest simulatur na tramet betg sia fanestra (actualisar il simulatur).'),
    'Sim view': ('Sim-Ansicht', 'Vue simulateur', 'Vista simulatore', 'Vista dal simulatur'),
}
for _k, _v in _HX_SIMV.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = WEB_PAGE.replace("</body>", SIMV_JS.replace("/*SIMVDE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_SIMV.items()}, ensure_ascii=False), 1)
                            + "</body>", 1)


def simv_selftest():
    html = WEB_PAGE
    assert html.count('id="sv-css"') == 1 and "/*SIMVDE*/" not in html and '"Sim-Ansicht"' in html, "Sim-Ansicht not in the live page"
    i = html.find('id="sv-css"')
    assert html.find("function simTouchPad", 0, i) > 0 and html.find("function simViewPoll", 0, i) > 0, "Sim-Ansicht before the stream functions (470)"
    js = SIMV_JS
    for need in ('action: "gamewiz"', 'op: "quick"', 'id: "game_local"', 'op: "next"', 'action: "pad"', 'action: "localplay", do: "stop"',
                 'action: "game"', '"/api/stick"', '"/snapshot.jpg', 'dataset.dock = "1"', '"mw-simv"', "S_.on && S_.ok",
                 'dataset.tab !== "live"', "qsArrange(qsList(J)", '"/sim#gw"'):
        assert need in js, ("Sim-Ansicht: missing " + need)
    for k, v in _HX_SIMV.items():                         # all five languages
        assert len(v) == 4 and all(v), k
        assert k in TRX["fr"] and k in TRX["it"] and k in TRX["rm"] and k in DE, k
    assert tr("Sim view", "rm") == "Vista dal simulatur" and DE.get("Quit") == "Beenden"
    assert HELP_PAGE.count('<section id="simview"') == 2 and all('id="simview"' in (HELP_X.get(L) or 'id="simview"') for L in ("fr", "it", "rm")), "manual: simview"
    try:
        src_ = open(__file__, encoding="utf-8").read()
    except OSError:
        src_ = 'act_ == "localplay"'
    assert 'act_ == "localplay"' in src_, "server: /api/sim localplay (550)"
    return "Sim-Ansicht: live page in simulator operation, game choice, pad, translations"


# ---- the manual (HELP_PAGE 540 + HELP_X): a short chapter «Sim-Ansicht und Spielen» before «Tipps & Tricks» ----
_HELP_SIMV = {
    "de": ('<section id="simview" data-icon="🎮"><h2>Sim-Ansicht und Spielen (Handy / Tablet)</h2><ul>'
           '<li><b>Nur im Simulator-Betrieb:</b> ist die Simulation ein und verbunden, zeigt die Live-Seite die ruhige «Sim-Ansicht»: '
           'grosses Simulator-Bild, darüber klein das Kamerabild, unten Kopf-Stick, Folgen, IR-Licht, Licht, Sirene und Aufnahme. '
           'Im echten Betrieb bleibt die Live-Seite wie immer.</li>'
           '<li><b>⋯ Mehr:</b> alle anderen Schalter der Live-Seite und die anderen Seiten. <b>▦ Klassisch</b> zeigt die gewohnte Live-Seite; '
           'dort führt «📱 Sim-Ansicht» (Karte Simulator-Steuerung) zurück. Die Wahl gilt pro Gerät.</li>'
           '<li><b>🎮 Spielen:</b> Spiel antippen – alles ist eingestellt, die Runde startet, du spielst mit den Knöpfen im Browser '
           '(Stick links gehen, rechts umschauen, Ducken, Kriechen, Stein, Lampe, Rennen; als Wächter Auslöser, «Erwischt!», Licht, Scan, Sirene, Zoom). '
           '<b>⚙ Anpassen</b> öffnet den ganzen Spiel-Assistenten, <b>× Beenden</b> verlässt das Spiel.</li>'
           '</ul></section>\n'),
    "en": ('<section id="simview" data-icon="🎮"><h2>Sim view and playing (phone / tablet)</h2><ul>'
           '<li><b>Only in simulator operation:</b> while the simulation is on and connected, the live page shows the calm «Sim view»: '
           'a big simulator picture, the camera picture small on top, below the head stick, Follow, IR light, light, siren and recording. '
           'In real operation the live page stays as always.</li>'
           '<li><b>⋯ More:</b> all other switches of the live page and the other pages. <b>▦ Classic</b> shows the usual live page; '
           '«📱 Sim view» (card Simulator control) leads back. The choice is kept per device.</li>'
           '<li><b>🎮 Play:</b> tap a game – everything is set, the round starts and you play with the buttons in the browser '
           '(left stick walk, right look around, crouch, crawl, stone, lamp, run; as the guard shutter, «Caught!», light, scan, siren, zoom). '
           '<b>⚙ Customise</b> opens the whole game wizard, <b>× Quit</b> leaves the game.</li>'
           '</ul></section>\n'),
    "fr": ('<section id="simview" data-icon="🎮"><h2>Vue simulateur et jeux (portable / tablette)</h2><ul>'
           '<li><b>Seulement avec le simulateur :</b> quand la simulation est active et connectée, la page live montre la «Vue simulateur» : '
           'grande image du simulateur, petite image de la caméra, en bas le stick de la tête, Suivre, lumière IR, lumière, sirène et enregistrement. '
           'En fonctionnement réel, la page live reste comme toujours.</li>'
           '<li><b>⋯ Plus :</b> tous les autres interrupteurs de la page live et les autres pages. <b>▦ Classique</b> montre la page live habituelle ; '
           '«📱 Vue simulateur» (carte Commande du simulateur) y ramène. Le choix vaut pour cet appareil.</li>'
           '<li><b>🎮 Jouer :</b> toucher un jeu – tout est réglé, la manche commence et tu joues avec les boutons du navigateur. '
           '<b>⚙ Personnaliser</b> ouvre tout l’assistant de jeu, <b>× Quitter</b> quitte le jeu.</li>'
           '</ul></section>\n'),
    "it": ('<section id="simview" data-icon="🎮"><h2>Vista simulatore e giochi (telefono / tablet)</h2><ul>'
           '<li><b>Solo con il simulatore:</b> quando la simulazione è attiva e collegata, la pagina live mostra la «Vista simulatore»: '
           'grande immagine del simulatore, piccola immagine della telecamera, in basso lo stick della testa, Seguire, luce IR, luce, sirena e registrazione. '
           'Nel funzionamento reale la pagina live resta come sempre.</li>'
           '<li><b>⋯ Altro:</b> tutti gli altri interruttori della pagina live e le altre pagine. <b>▦ Classico</b> mostra la solita pagina live; '
           '«📱 Vista simulatore» (scheda Comando del simulatore) riporta indietro. La scelta vale per questo dispositivo.</li>'
           '<li><b>🎮 Gioca:</b> tocca un gioco – è tutto impostato, il round parte e giochi con i pulsanti nel browser. '
           '<b>⚙ Personalizza</b> apre tutto l’assistente di gioco, <b>× Esci</b> lascia il gioco.</li>'
           '</ul></section>\n'),
    "rm": ('<section id="simview" data-icon="🎮"><h2>Vista dal simulatur e giugar (telefonin / tablet)</h2><ul>'
           '<li><b>Mo cun il simulatur:</b> sch’la simulaziun è activa e colliada, mussa la pagina live la «Vista dal simulatur»: '
           'grond maletg dal simulatur, pitschen maletg da la camera, sutvart il stick dal chau, Suandar, glisch IR, glisch, sirena e registraziun. '
           'En il funcziunament real resta la pagina live sco adina.</li>'
           '<li><b>⋯ Dapli:</b> tut ils auters interruttus da la pagina live e las autras paginas. <b>▦ Classic</b> mussa la pagina live usitada; '
           '«📱 Vista dal simulatur» (carta Commond dal simulatur) maina enavos. La tscherna vala per quest apparat.</li>'
           '<li><b>🎮 Giugar:</b> tutgar in gieu – tut è endrizzà, la runda cumenza e ti giogas cun ils buttuns en il navigatur. '
           '<b>⚙ Adattar</b> avra l’entir assistent da gieu, <b>× Terminar</b> banduna il gieu.</li>'
           '</ul></section>\n'),
}


def _help_simv(doc, lang):
    if 'id="simview"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_SIMV[lang] + doc[i:] if i >= 0 else doc


_hp_en_simv = HELP_PAGE.find('<div lang="en">')
if _hp_en_simv > 0:
    HELP_PAGE = _help_simv(HELP_PAGE[:_hp_en_simv], "de") + _help_simv(HELP_PAGE[_hp_en_simv:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_simv(HELP_X[_L], _L)


SELFTEST_EXTRA.append(("Sim view: live screen in simulator operation, one-tap games, touch pad (639zt)", simv_selftest))
