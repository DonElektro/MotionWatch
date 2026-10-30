#@ MoveEye – Teil 543: «Wächter-Werkzeuge» der Wächter an MoveEye im Spiel des 3D-Simulators (Energie, Licht, Sirene, Scan, Zoom, Hinweis-Marken). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Spielkonzept of Daniel (30.10.2026), «Wächter-Werkzeuge mit Kosten»: in the game of the 3D simulator the guard has a budget
# of energy per round (by the difficulty) and every tool costs some and has a cooldown (simulator gametools.gd):
# 💡 light, 📢 siren (whoever moves is noticed), 📡 scan (hint markers where runners are), 🔍 zoom of the head camera and
# the 🎯 shutter (part 539). The guard at the phone and at the simulator PC have their own gauges (game.gd, localplay.gd).
# Here: the guards at MoveEye in «Team gegen MoveEye» (they steer the real head on the live page or in the
# «Controller-Ansicht» 538) get a small gauge row at the top of the live picture: the energy, the four tools with their
# price and cooldown (tap = use: the simulator controls game_tool_* through /api/sim «ctl press»), and the hint markers
# (👣 a runner runs = loud, 📡 found by the scan) at their direction in the picture. Only during such a round.
# Data: the simulator's game_info «tools» (340 sim_game → state.sim.game.tools). Translations: part 612.
# ----------------------------------------------------------------------------

WAECHTER_JS = r"""
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*WAECHTERDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, id, cls) => { const x = document.createElement(tag); if (id) x.id = id; if (cls) x.className = cls; return x; };
  const css = E("style"); css.textContent =
    "#mwt{position:absolute;z-index:61;display:flex;gap:6px;align-items:center;transform:translateX(-50%);background:rgba(10,14,20,.78);border:1px solid #2a3646;border-radius:12px;padding:4px 6px;color:#e8eef5;font:600 12px/1.1 system-ui,sans-serif}"
    + "#mwt[hidden],#mwt-h[hidden]{display:none}#mwt .en{min-width:74px}#mwt .en i{display:block;height:6px;border-radius:9px;background:#1f2b3a;overflow:hidden;margin-top:3px}#mwt .en i b{display:block;height:100%;background:linear-gradient(90deg,#ffd166,#34c759)}"
    + "#mwt button{min-width:44px;height:40px;border-radius:10px;border:1px solid #3a4658;background:#151e2b;color:#fff;font-size:17px;padding:0 6px;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;cursor:pointer;touch-action:manipulation}"
    + "#mwt button small{font-size:9px;font-weight:600;opacity:.85;margin-top:2px}#mwt button.off{opacity:.4;filter:grayscale(1)}#mwt button.cd small{color:#ffd166}"
    + "#mwt-h{position:absolute;z-index:60;pointer-events:none;inset:0}#mwt-h span{position:absolute;transform:translateX(-50%);font-size:22px;text-shadow:0 0 6px #000}#mwt-h span b{display:block;font-size:10px;text-align:center;color:#fff}";
  document.head.appendChild(css);
  const BOX = E("div", "mwt"), HB = E("div", "mwt-h"), EN = E("div", "", "en"); BOX.hidden = true; HB.hidden = true; BOX.appendChild(EN);
  const NAMES = {light: "Light", siren: "Siren", scan: "Scan", zoom: "Zoom"}, BTN = {};
  Object.keys(NAMES).forEach(k => { const b = E("button"); b.type = "button"; b.dataset.k = k; BTN[k] = b; BOX.appendChild(b);
    b.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); use(k); });
    ["pointerdown", "pointerup", "dblclick"].forEach(x => b.addEventListener(x, ev => ev.stopPropagation())); });
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const game = () => ((J().state || {}).sim || {}).game || null;
  const simLive = () => { const s = (J().state || {}).sim || {}; return !!(s.on && s.ok); };
  const roundOn = () => { const G = game(); return !!(G && G.mode === "mwhand" && (G.round === "play" || G.round === "countdown") && G.tools && G.tools.on); };
  let lastMsg = "";
  function use(k) {
    const G = game() || {}, Tl = (G.tools || {}).t || [], x = Tl.find(y => y[0] === k);
    if (x && !x[5]) { if (typeof toast === "function") toast("⏳ " + T(NAMES[k]) + ": " + (x[4] > 0 ? x[4] + " s" : T("not enough energy"))); return; }
    post("/api/sim", {action: "ctl", ctl: "press", id: "game_tool_" + k, lang: LANG}).then(() => { if (typeof toast === "function") toast(BTN[k].firstChild.textContent + " " + T(NAMES[k])); }).catch(() => {});
  }
  function picRect(v) {
    const r = v.getBoundingClientRect(), nw = v.naturalWidth || 16, nh = v.naturalHeight || 9;
    const fit = getComputedStyle(v).objectFit, k = fit === "cover" ? Math.max(r.width / nw, r.height / nh) : fit === "fill" ? 0 : Math.min(r.width / nw, r.height / nh);
    const w = k ? nw * k : r.width, h = k ? nh * k : r.height;
    return {left: r.left + (r.width - w) / 2, top: r.top + (r.height - h) / 2, width: w, height: h};
  }
  function paint() {
    const v = document.getElementById("video"), on = roundOn() && simLive() && v && v.offsetParent !== null;
    if (!on) { BOX.hidden = HB.hidden = true; return; }
    const cont = v.parentNode;
    if (BOX.parentNode !== cont) cont.append(HB, BOX);
    if (getComputedStyle(cont).position === "static") cont.style.position = "relative";
    const cr = cont.getBoundingClientRect(), p = picRect(v), G = game() || {}, TL = G.tools || {};
    const top = Math.max(p.top, cr.top) - cr.top + (p.width < 520 ? 54 : 30);      // under the text line of the picture (phone: under the corner buttons)
    BOX.style.left = (p.left + p.width / 2 - cr.left) + "px"; BOX.style.top = top + "px";
    const f = Math.max(0, Math.min(1, (TL.e || 0) / Math.max(1, TL.max || 1)));
    EN.innerHTML = "⚡ " + T("Energy") + " " + (TL.e || 0) + "<i><b style=\"width:" + Math.round(f * 100) + "%\"></b></i>";
    (TL.t || []).forEach(x => { const b = BTN[x[0]]; if (!b) return; const sig = x.join("|") + LANG; if (b.dataset.s === sig) return; b.dataset.s = sig;
      b.innerHTML = x[1] + "<small>" + (x[4] > 0 ? x[4] + " s" : x[3] + " ⚡") + "</small>"; b.classList.toggle("off", !x[5] && !(x[4] > 0)); b.classList.toggle("cd", x[4] > 0);
      b.title = T(NAMES[x[0]]) + " · " + x[3] + " " + T("energy") + (x[4] > 0 ? " · " + x[4] + " s" : ""); b.setAttribute("aria-label", b.title); });
    BOX.hidden = false;
    const H = TL.hints || [];
    HB.innerHTML = H.map(x => "<span style=\"left:" + Math.round(p.left - cr.left + x[0] * p.width) + "px;top:" + Math.round(top + 52) + "px\">" + (x[3] ? (x[0] < 0.5 ? "◀" : "▶") : "") + (x[1] === "scan" ? "📡" : "👣") + "<b>" + x[2] + " m</b></span>").join("");
    HB.hidden = !H.length;
    if (TL.msg && TL.msg !== lastMsg) { lastMsg = TL.msg; if (typeof toast === "function") toast(TL.msg); }
  }
  setInterval(paint, 250);
  addEventListener("resize", paint);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", WAECHTER_JS + "</body>", 1)
