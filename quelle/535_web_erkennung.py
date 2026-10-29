#@ MoveEye – Teil 535: Webseite: Gehtest (Live und Schutz), Akku-Sparen auf der Schutz-Seite. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13: a small script at the end of the main page (530 stays as it is): the card «Gehtest» under the live picture,
# the button «Gehtest» on the Schutz page and the line of the battery saver beside «Power saving». Asks /api/walktest
# (every 5 s, every second while the walk test runs) and beeps on this phone / PC at every detection.
# ----------------------------------------------------------------------------
WALKTEST_DE = {
    "🚶 Walk test": "🚶 Gehtest", "▶ Start walk test": "▶ Gehtest starten", "■ Stop": "■ Beenden",
    "Walk past the camera like a visitor would: MoveEye beeps at every detection and draws where you were recognised (and where only movement was seen). 3 minutes, no alarms meanwhile.":
        "Geh an der Kamera vorbei, wie es ein Besucher tun würde: MoveEye piepst bei jeder Erkennung und zeichnet auf, wo du erkannt wurdest (und wo nur Bewegung zu sehen war). 3 Minuten, in dieser Zeit keine Alarme.",
    "left": "übrig", "Person recognised": "Person erkannt", "Movement, no person": "Bewegung, keine Person", "only in the thermal picture": "nur im Wärmebild",
    "last": "zuletzt", "about": "ca.", "Last walk test": "Letzter Gehtest", "Distance": "Entfernung", "recognised": "erkannt",
    "only movement": "nur Bewegung", "No loudspeaker on the Pi - this page beeps (keep it open).": "Kein Lautsprecher am Pi – diese Seite piepst (offen lassen).",
    "Walk test running - no alarms": "Gehtest läuft – keine Alarme", "saver": "Sparen", "Battery saver active: fewer pictures, the AI less often": "Akku-Sparen aktiv: weniger Bilder, die KI seltener",
    "Test the range: walk past the camera": "Reichweite testen: an der Kamera vorbeigehen", "Walk test started": "Gehtest gestartet",
    "error": "Fehler", "distance estimated from the height (person 1.7 m)": "Entfernung geschätzt aus der Höhe (Person 1,7 m)",
}
WALKTEST_JS = r"""
<script>
(function () {
  try { const D = /*WTDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const W = {s: null, ctx: null, beeps: -1, timer: 0, key: ""};
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  function beep() {
    try { const C = W.ctx || (W.ctx = new (window.AudioContext || window.webkitAudioContext)()); if (C.state === "suspended") C.resume();
      const o = C.createOscillator(), g = C.createGain(); o.type = "sine"; o.frequency.value = 1400; g.gain.value = 0.18;
      o.connect(g); g.connect(C.destination); o.start(); o.stop(C.currentTime + 0.12); } catch (e) {}
  }
  async function act(a) {
    if (a === "start") { try { W.ctx = W.ctx || new (window.AudioContext || window.webkitAudioContext)(); W.ctx.resume(); } catch (e) {} }
    try { const r = await fetch("/api/walktest", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: a, lang: L()})});
      const j = await r.json(); if (!j.ok && j.error && typeof toast === "function") toast("⚠ " + j.error);
      else if (a === "start" && typeof toast === "function") toast("🚶 " + T("Walk test started"));
      W.key = ""; paint(j); } catch (e) {}
    clearTimeout(W.timer); W.timer = setTimeout(poll, 800);
  }
  function mmss(s) { s = Math.max(0, s | 0); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
  function dot(col, ring) { const d = E("span"); d.style.cssText = "display:inline-block;width:11px;height:11px;border-radius:50%;margin:0 5px 0 0;vertical-align:-1px;"
    + (ring ? "border:2px solid " + col : "background:" + col); return d; }
  function result(box, R) {
    if (!R) return;
    box.appendChild(E("div", "mut", T("Last walk test") + " · " + R.when));
    if (R.img) { const im = E("img"); im.src = "/api/walktest.jpg?t=" + Math.round(R.t); im.alt = ""; im.style.cssText = "width:100%;border-radius:10px;margin:6px 0;display:block"; box.appendChild(im); }
    const lg = E("div", "mut"); lg.style.cssText = "display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;margin-bottom:6px";
    const a = E("span"); a.append(dot("#3cc83c"), T("Person recognised")); const b = E("span"); b.append(dot("#ffa500", true), T("Movement, no person"));
    lg.append(a, b); if (R.n_thermal) { const c = E("span"); c.append(dot("#e63cc8"), T("only in the thermal picture")); lg.appendChild(c); } box.appendChild(lg);
    (R.text || []).forEach(x => box.appendChild(E("div", "", "• " + x)));
    const rows = (R.bands || []).filter(b => b.det || b.mot);
    if (rows.length) {
      const tb = E("table"); tb.style.cssText = "width:100%;border-collapse:collapse;margin-top:8px;font-size:13px";
      const hd = E("tr"); [T("Distance"), T("recognised"), T("only movement")].forEach(h => { const th = E("th", "", h); th.style.cssText = "text-align:left;padding:2px 4px;opacity:.75;font-weight:600"; hd.appendChild(th); }); tb.appendChild(hd);
      rows.forEach(b => { const tr = E("tr"); [(b.hi >= 999 ? "> " + b.lo : b.lo + "–" + b.hi) + " m", "" + b.det, "" + b.mot].forEach((v, i) => { const td = E("td", "", v);
        td.style.cssText = "padding:2px 4px;border-top:1px solid rgba(128,128,128,.25)" + (i === 1 && b.det ? ";color:#3cc83c;font-weight:700" : ""); tr.appendChild(td); }); tb.appendChild(tr); });
      box.appendChild(tb); box.appendChild(E("div", "mut", T("distance estimated from the height (person 1.7 m)")));
    }
  }
  function body(box, S, where) {
    box.textContent = "";
    if (S.on) {
      const big = E("div", "", "🚶 " + mmss(S.left) + " " + T("left")); big.style.cssText = "font-size:20px;font-weight:700;margin:2px 0 4px";
      box.appendChild(big);
      const ln = E("div"); ln.append(dot("#3cc83c"), T("Person recognised") + " " + S.n_det + "×  ", dot("#ffa500", true), T("Movement, no person") + " " + S.n_mot + "×");
      box.appendChild(ln);
      if (S.last_m) box.appendChild(E("div", "mut", T("last") + ": " + T("about") + " " + S.last_m + " m"));
      box.appendChild(E("div", "mut", "🔕 " + T("Walk test running - no alarms") + (S.speaker ? "" : " · " + T("No loudspeaker on the Pi - this page beeps (keep it open)."))));
      const bar = E("div", "bar"); const i = E("i"); i.style.width = Math.round(100 * (1 - S.left / (S.total || 180))) + "%"; bar.appendChild(i); bar.style.margin = "8px 0"; box.appendChild(bar);
      const st = E("button", "sec", T("■ Stop")); st.type = "button"; st.onclick = () => act("stop"); box.appendChild(st);
      return;
    }
    if (where === "live") box.appendChild(E("div", "mut", T("Walk past the camera like a visitor would: MoveEye beeps at every detection and draws where you were recognised (and where only movement was seen). 3 minutes, no alarms meanwhile.")));
    const go = E("button", where === "live" ? "" : "sec", T("▶ Start walk test")); go.type = "button"; go.style.margin = "8px 0"; go.onclick = () => act("start");
    box.appendChild(go);
    if (where === "live") result(box, S.result);
  }
  function paint(S) {
    if (!S || S.on == null) return;
    W.s = S;
    if (S.on && W.beeps >= 0 && S.beeps > W.beeps) beep();
    W.beeps = S.on ? S.beeps : -1;
    const key = JSON.stringify([S.on, S.left, S.n_det, S.n_mot, S.result && S.result.t, S.batt_save && S.batt_save.text]);
    if (key === W.key) return; W.key = key;
    const vc = document.getElementById("vcard");
    let c = document.getElementById("wt-card");
    if (vc && !c) {
      c = E("details", "card"); c.id = "wt-card"; c.setAttribute("data-view", "walktest"); c.setAttribute("data-vgroup", "Panels"); c.setAttribute("data-vlabel", "Walk test");
      const sm = E("summary"); sm.appendChild(E("span", "", T("🚶 Walk test"))); c.appendChild(sm); const b = E("div"); b.id = "wt-body"; c.appendChild(b);
      vc.after(c);
      if (S.on || (S.result && Date.now() / 1000 - S.result.t < 900)) c.open = true;
    }
    if (c) { if (S.on) c.open = true; body(document.getElementById("wt-body"), S, "live"); }
    const nr = document.getElementById("night-res") || document.getElementById("pr-night");
    let p = document.getElementById("pr-wt");
    if (nr && !p) {
      p = E("div"); p.id = "pr-wt"; p.style.margin = "8px 0";
      p.appendChild(E("div", "mut", "🚶 " + T("Test the range: walk past the camera")));
      const b = E("div"); b.id = "pr-wt-b"; p.appendChild(b); nr.after(p);
    }
    if (p) body(document.getElementById("pr-wt-b"), S, "protect");
    const ei = document.getElementById("pr-eco-info");
    if (ei && S.batt_save) {
      let x = document.getElementById("pr-bsave");
      if (!x) { x = E("span", "mut"); x.id = "pr-bsave"; x.style.display = "block"; ei.after(x); }
      const B = S.batt_save; x.textContent = (B.on ? "🐢 " : "🔋 ") + (B.text || ""); x.style.fontWeight = B.on ? "700" : "";
      x.hidden = !(B.on || B.pct != null);
    }
  }
  async function poll() {
    clearTimeout(W.timer);
    try { const r = await fetch("/api/walktest?lang=" + L(), {cache: "no-store"}); if (r.ok) paint(await r.json()); } catch (e) {}
    W.timer = setTimeout(poll, W.s && W.s.on ? 1000 : 5000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", poll); else setTimeout(poll, 300);
})();
</script>
"""
WALKTEST_JS = WALKTEST_JS.replace("/*WTDE*/{}", json.dumps(WALKTEST_DE, ensure_ascii=False))
WEB_PAGE = WEB_PAGE.replace("</body>", WALKTEST_JS + "</body>", 1)
