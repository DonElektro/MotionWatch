#@ MoveEye – Teil 548: Web: «🤖 MoveEye als KI-Wächter» in der Karte «Spiel» der Seite Simulator (Schalter, Liste «gegen die KI») und das Simulator-Fenster ohne Einblendungen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wishes of Daniel (30.10.2026):
#  · «MoveEye überwacht automatisch» (for his tests in online games): a switch on the game card of the page Simulator. When it is
#    on and a round with a guard role runs (Wächter / Wächter-Duell, Team gegen Team, Team gegen MoveEye, online rounds), the
#    simulator lets MoveEye be the guard (simulator gamekiwaechter.gd): every player sneaks, the round runs as «Team gegen
#    MoveEye» with the «KI-Autopilot» of the shutter (gamekihilfe.gd + gameshutter.gd + gametools.gd) - MoveEye's real
#    detection, the head follows (542 kihilfe_follow, so the pause of 2.98.39 does not stop it), the autopilot fires.
#    Results «Wächter: MoveEye (KI)», kept in an own list «gegen die KI» (not in the ranking of the evening). The Bot-Wächter
#    stays out (the round is no «Wächter» round any more). Switched through the simulator control «game_kiguard»
#    (/api/sim ctl set), read from game_info «kig» (/api/sim action game). Not saved in the simulator: off after its restart.
#  · The picture «Simulator-Fenster» on this page asks the simulator with dock=1 (470 simViewPoll, 550): only the 3D view and the
#    dock - no camera picture, map, compass, rover stick (simulator padview.gd). MoveEye's own buttons on the picture stay; they
#    fade while the mouse / finger is away (they come back on a move or a tap) so they do not cover the picture.
# Texts: German here (I18N.de of the page), all languages in 596.
# ----------------------------------------------------------------------------

KIG_KEYS = ["MoveEye as AI guard", "In rounds with a guard role (guard, team against team, team against MoveEye, online rounds) MoveEye itself is the guard: everybody sneaks, MoveEye's real detection watches, the head follows and the shutter fires by itself. Such rounds go into their own list «against the AI», not into the ranking.", "On: MoveEye guards rounds with a guard role itself", "This round: MoveEye guards (AI)",
            "MoveEye is not connected to the simulator game", "Against the AI", "rounds", "caught", "at the goal", "never caught",
            "The AI", "catches", "false alarms", "shots", "Reset the list «against the AI»", "Reset the list «against the AI»?",
            "not supported - update the simulator", "no rounds against the AI yet",
            "AI tower", "floor", "highest floor", "towers", "AI tower now: floor", "Start the AI tower: quick start «KI-Turm» in the game wizard"]

KIG_JS = r"""<script>
Object.assign(I18N.de, /*KIGDE*/{});
(function () {
  const B = document.getElementById("g-kig"); if (!B) return;
  let SIG = "", busy = false, D = null;
  const send = async (v) => { busy = true; try { const r = await post("/api/sim", {action: "ctl", ctl: "set", id: "game_kiguard", value: v, lang: LANG});
      if (r && r.ok === false) toast("⚠ " + (r.error || t("not supported - update the simulator"))); } finally { busy = false; SIG = ""; poll(true); } };
  function paint(K) {
    const sig = JSON.stringify(K || null); if (sig === SIG) return; SIG = sig;
    B.textContent = ""; if (!K) return;
    if (!D) { D = el("details", "sub"); D.open = true; }
    D.textContent = ""; B.appendChild(D);
    D.appendChild(el("summary", "", "🤖 " + t("MoveEye as AI guard")));
    D.appendChild(el("div", "mut", t("In rounds with a guard role (guard, team against team, team against MoveEye, online rounds) MoveEye itself is the guard: everybody sneaks, MoveEye's real detection watches, the head follows and the shutter fires by itself. Such rounds go into their own list «against the AI», not into the ranking.")));
    const lb = el("label", "sc-row"); lb.style.cssText = "display:flex;gap:10px;align-items:center;margin:8px 0;cursor:pointer";
    const cb = document.createElement("input"); cb.type = "checkbox"; cb.id = "g-kig-on"; cb.checked = !!K.on; cb.disabled = !K.mw && !K.on;
    cb.onchange = () => send(cb.checked);
    lb.append(cb, el("span", "", "🤖 " + t("On: MoveEye guards rounds with a guard role itself"))); D.appendChild(lb);
    if (K.active) { const a = el("div", ""); a.style.fontWeight = "700"; a.textContent = "🛡 " + t("This round: MoveEye guards (AI)"); D.appendChild(a); }
    if (!K.mw) D.appendChild(el("div", "mut", "⚠ " + t("MoveEye is not connected to the simulator game")));
    const h = el("div", "", "🤖 " + t("Against the AI")); h.style.cssText = "margin-top:8px;font-weight:600"; D.appendChild(h);
    const k = K.ki || {};
    D.appendChild(el("div", "mut", t("The AI") + ": " + (k.rounds || 0) + " " + t("rounds") + " · " + (k.catches || 0) + " " + t("catches") + " · " + (k.false || 0) + " " + t("false alarms") + " · " + (k.shots || 0) + " " + t("shots")));
    if (!(K.board || []).length) D.appendChild(el("div", "mut", t("no rounds against the AI yet")));
    else { const tb = el("table", "gw-board");
      K.board.forEach((b, i) => { const tr = el("tr"); const n = el("td", "", (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + " " + b.n + (b.bot ? " 🤖" : "")); n.style.color = b.c;
        tr.append(n, el("td", "", String(b.score)), el("td", "mut", b.rounds + " " + t("rounds") + " · " + b.caught + "× " + t("caught") + (b.goal ? " · " + b.goal + "× " + t("at the goal") : "") + (b.clean ? " · " + b.clean + "× " + t("never caught") : ""))); tb.appendChild(tr); });
      D.appendChild(tb);
      const rb = el("button", "sec", t("Reset the list «against the AI»")); rb.type = "button"; rb.style.marginTop = "6px";
      rb.onclick = async () => { if (!confirm(t("Reset the list «against the AI»?"))) return; await post("/api/sim", {action: "ctl", ctl: "press", id: "game_kig_reset", lang: LANG}); SIG = ""; poll(true); };
      D.appendChild(rb); }
    // Gameplay ausfeilen (simulator 31.10.2026): the AI tower - the highest floor per player, also «against the AI»
    const TW = K.turm || [];
    const th = el("div", "", "🗼 " + t("AI tower")); th.style.cssText = "margin-top:8px;font-weight:600"; D.appendChild(th);
    if (K.turm_on) D.appendChild(el("div", "", "🗼 " + t("AI tower now: floor") + " " + K.turm_floor));
    if (!TW.length) D.appendChild(el("div", "mut", t("Start the AI tower: quick start «KI-Turm» in the game wizard")));
    else { const tb2 = el("table", "gw-board");
      TW.forEach((b, i) => { const tr = el("tr"); tr.append(el("td", "", (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + " " + b.n), el("td", "", t("floor") + " " + b.best + (b.ki ? " 🛡" : "")),
        el("td", "mut", (b.towers || 0) + " " + t("towers"))); tb2.appendChild(tr); });
      D.appendChild(tb2); }
  }
  let tm = null;
  async function poll(now) {
    clearTimeout(tm);
    const g = document.getElementById("c-game");
    if (!busy && g && !g.hidden && !document.hidden && typeof S !== "undefined" && S && S.on) {
      try { const r = await post("/api/sim", {action: "game", lang: LANG}); paint(r && r.ok !== false && r.kig ? r.kig : null); } catch (e) {}
    } else if (!(typeof S !== "undefined" && S && S.on)) paint(null);
    tm = setTimeout(poll, 4000);
  }
  setTimeout(poll, 1200);
  // ---- the picture «Simulator-Fenster»: MoveEye's buttons fade while nobody uses them (they stay working) ----
  const W = document.getElementById("s-pvw");
  if (W) {
    const cs = document.createElement("style");
    cs.textContent = "#s-pvw .pvbtn{transition:opacity .35s}#s-pvw.view.kig-idle>.pvbtn{opacity:.22}#s-pvw.view.kig-idle>.pvbtn:hover,#s-pvw.view.kig-idle>.pvbtn:focus-within{opacity:1}";
    document.head.appendChild(cs);
    let it = null;
    const wake = () => { W.classList.remove("kig-idle"); clearTimeout(it); it = setTimeout(() => W.classList.add("kig-idle"), 3000); };
    ["pointermove", "pointerdown", "touchstart", "keydown"].forEach(n => W.addEventListener(n, wake, {passive: true}));
    wake();
  }
})();
</script>"""
SIM_PAGE = SIM_PAGE.replace('<div id="g-cmp"></div>', '<div id="g-kig"></div><div id="g-cmp"></div>', 1)
SIM_PAGE = SIM_PAGE.replace("</body>", "<!--KIGJS--></body>", 1)          # filled by 596 (after the German texts are known)
