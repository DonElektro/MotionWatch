#@ MoveEye – Teil 542: «KI-Hilfe» für den Menschen am Auslöser (KI-Rahmen, KI zielt, KI-Autopilot) – Live-Seite, Controller-Ansicht, Kopf folgt, Runde «mit KI-Hilfe». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): the guards at MoveEye in «Team gegen MoveEye» (the shutter of part 539) may switch on help
# of the AI for the running round, on the live page and in the «Controller-Ansicht» (538: L2 in a round):
#   «KI-Rahmen»    MoveEye's live detection boxes (STATE person_boxes) on the live picture: persons green, uncertain dashed
#                  (not confirmed by the AI this picture - STATE person_sure, from erk_frame below)
#   «KI zielt»     the head follows the detected person like «Folgen» - although since 2.98.39 the head does not move by
#                  itself in such a round (162 kopf_track_blocked asks kihilfe_follow()); the person presses the shutter
#   «KI-Autopilot» aims and fires by itself when sure (the simulator decides: gamekihilfe.gd - a sure box in the hit
#                  circle for 0.5 s, shutter free, energy of gametools.gd enough). Steering by hand (joystick, controller,
#                  arrows: MANUAL) or the shutter pauses it 5 s (sent to the simulator: control «game_shut» op ki human).
#   Any help marks the round «mit KI-Hilfe» in the simulator: no leaderboard, no badges, marked in the results and in
#   the game report. During a round WITHOUT help the live picture has no burned-in person boxes (410 kihilfe_clean_stream):
#   otherwise the boxes would be a help for everybody.
# The mode lives in the simulator (game_info shut.ki, 340 sim_game → state.sim.game.shut.ki); switched through
# /api/sim {action: kihilfe, mode: off|frame|aim|auto|next} (550). The guard phone and the simulator PC have their own
# switch (simulator gamekihilfe.gd, gameshutter.gd). Translations: part 623.
# ----------------------------------------------------------------------------

KIH = {"mode": "off", "mode_t": 0.0, "man_was": 0.0, "hum_until": 0.0, "hum_sent": 0.0}
KIH_MODES = ("off", "frame", "aim", "auto")


def kihilfe_mode():
    """the help of the guards at MoveEye in a running round «Team gegen MoveEye» ('off' otherwise)"""
    if not CFG.get("sim_on"):
        return "off"
    try:
        g = sim_game()
    except Exception:
        g = None
    if not g or g.get("mode") != "mwhand" or g.get("round") not in ("play", "countdown"):
        return "off"
    if time.time() - KIH["mode_t"] < 4.0:                 # just switched here (the game info comes every 2.5 s)
        return KIH["mode"]
    m = str(((g.get("shut") or {}).get("ki") or {}).get("mode") or "off")
    return m if m in KIH_MODES else "off"


def kihilfe_follow():
    """162: the head may follow in a round «Team gegen MoveEye» - «KI zielt» / «KI-Autopilot» is on and nobody steers"""
    return kihilfe_mode() in ("aim", "auto") and time.time() >= KIH["hum_until"]


def kihilfe_clean_stream():
    """410: no burned-in person boxes on the live picture during a round «Team gegen MoveEye» without «KI-Rahmen»"""
    try:
        return kopf_game_hand() and kihilfe_mode() == "off"
    except Exception:
        return False


def _kihilfe_human():
    try:
        sim_control({"action": "game_shut", "op": "ki", "human": True})
    except Exception:
        pass


def kihilfe_frame(w, person_boxes, pw, ph):
    """once per picture (kopf_frame): the person steers → the AI waits; «KI zielt» without «Folgen»: follow here"""
    m = kihilfe_mode()
    if m not in ("aim", "auto"):
        return
    now = time.time()
    if manual_active():
        if MANUAL["until"] != KIH["man_was"]:
            KIH["man_was"] = MANUAL["until"]
            KIH["hum_until"] = now + (5.0 if m == "auto" else 1.5)
            if m == "auto" and now - KIH["hum_sent"] > 1.0:     # the autopilot in the simulator waits 5 s too
                KIH["hum_sent"] = now
                threading.Thread(target=_kihilfe_human, daemon=True, name="kihuman").start()
        return
    if now < KIH["hum_until"] or not person_boxes or CFG.get("track_person"):
        return                                            # («Folgen» on: 410 follows by itself, 162 lets it)
    try:
        w.track(max(person_boxes, key=lambda b: b[2] * b[3]), pw, ph)
    except Exception as e:
        log_event("servo", f"KI-Hilfe: {e}"[:160])


def kihilfe_api(d, who, lang):
    """/api/sim {action: kihilfe, mode}: switch the help of the guards at MoveEye in the simulator → (answer, status)"""
    m = str(d.get("mode") or "")
    if m not in KIH_MODES + ("next",):
        return {"ok": False, "error": tr_err("unknown action", lang)}, 400
    if m == "next":
        cur = kihilfe_mode()
        m = KIH_MODES[(KIH_MODES.index(cur) + 1) % len(KIH_MODES)] if cur in KIH_MODES else "frame"
    try:
        r = sim_control({"action": "game_shut", "op": "ki", "mode": m, "who": str(who or "")[:30]})
    except Exception:
        return {"ok": False, "error": tr_err("simulator not reachable", lang)}, 400
    if not isinstance(r, dict) or not r.get("ok"):
        return {"ok": False, "error": tr_err(str((r or {}).get("error") or "not supported - update the simulator"), lang)}, 400
    KIH.update(mode=str((r.get("ki") or {}).get("mode") or m), mode_t=time.time(), hum_until=0.0)
    SIMGAME["t"] = 0.0
    log_event("sim", f"KI-Hilfe of the guards at MoveEye: {KIH['mode']}" + (" - the round does not count for the leaderboard" if KIH["mode"] != "off" else ""))
    return dict(r, ok=True), 200


# ---- the boxes: which persons the AI has confirmed in this picture (for «uncertain» = dashed) ---------------------------
_erk_frame_kih_base = erk_frame


# wraps: erk_frame
def erk_frame(persons, candidates, ai_boxes, pw, ph, t0, small):
    try:
        ai_on = bool(CFG.get("ai_enabled")) and STATE.get("ai_status") in ("ready", "demo")
        STATE["person_sure"] = [bool(getattr(t, "ai_confirmed", False)) or not ai_on for t in persons[:8]]
    except Exception:
        pass
    return _erk_frame_kih_base(persons, candidates, ai_boxes, pw, ph, t0, small)


_kopf_frame_kih_base = kopf_frame


# wraps: kopf_frame
def kopf_frame(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0):
    try:
        kihilfe_frame(w, person_boxes, pw, ph)
    except Exception as e:
        log_event("servo", f"KI-Hilfe: {e}"[:160])
    return _kopf_frame_kih_base(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0)


def kihilfe_selftest():
    sg, sim0, keep, tp, pk = globals()["sim_game"], CFG.get("sim_on"), dict(KIH), CFG.get("track_person"), CFG.get("kopf_parked")
    try:
        CFG["sim_on"] = True; CFG["kopf_parked"] = False
        globals()["sim_game"] = lambda: {"mode": "mwhand", "round": "play", "shut": {"ki": {"mode": "off"}}}
        KIH["mode_t"] = 0.0
        assert kihilfe_mode() == "off" and kopf_track_blocked() and kihilfe_clean_stream()
        globals()["sim_game"] = lambda: {"mode": "mwhand", "round": "play", "shut": {"ki": {"mode": "aim"}}}
        assert kihilfe_mode() == "aim" and kihilfe_follow() and not kopf_track_blocked() and not kihilfe_clean_stream()
        assert not kopf_may("round"), "the round of the head stays paused"
        KIH["hum_until"] = time.time() + 5.0
        assert not kihilfe_follow() and kopf_track_blocked(), "the person steers: the AI waits"
        globals()["sim_game"] = lambda: {"mode": "mwhand", "round": "end", "shut": {"ki": {"mode": "auto"}}}
        assert kihilfe_mode() == "off" and not kihilfe_clean_stream()
        assert "/*KIHDE*/" not in WEB_PAGE and "kih-b" in WEB_PAGE
    finally:
        globals()["sim_game"] = sg; CFG["sim_on"] = sim0; KIH.clear(); KIH.update(keep); CFG["track_person"] = tp
        CFG["kopf_parked"] = pk; KOPF["game_was"] = False
    return "help off: head stays, clean picture; KI zielt: head follows; hand: waits; after the round: off"


SELFTEST_EXTRA.append(("KI-Hilfe in «Team gegen MoveEye» (542)", kihilfe_selftest))


KIH_JS = r"""
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*KIHDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, id) => { const x = document.createElement(tag); if (id) x.id = id; return x; };
  const css = E("style"); css.textContent =
    "#kih-c{position:absolute;z-index:57;pointer-events:none}#kih-c[hidden],#kih-b[hidden]{display:none}"
    + "#kih-b{position:absolute;z-index:62;border-radius:999px;border:1px solid #3a4658;background:rgba(10,14,20,.8);color:#e8eef5;font:600 13px/1.1 system-ui,sans-serif;padding:8px 12px;min-height:36px;cursor:pointer;touch-action:manipulation;white-space:nowrap;box-shadow:0 2px 10px rgba(0,0,0,.45)}"
    + "#kih-b.on{border-color:#34c759;color:#9ff0b4}#kih-b.pz{border-color:#ffd166;color:#ffd166}#kih-b small{display:block;font-size:10px;font-weight:600;opacity:.8;margin-top:2px}";
  document.head.appendChild(css);
  const CV = E("canvas", "kih-c"), BT = E("button", "kih-b"); CV.hidden = BT.hidden = true; BT.type = "button";
  const MODES = ["off", "frame", "aim", "auto"], NAMES = {off: "AI help off", frame: "AI frames", aim: "AI aims", auto: "AI autopilot"};
  const KH = {mode: "off", t: 0, busy: false};
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const ST = () => J().state || {};
  const game = () => (ST().sim || {}).game || null;
  const roundOn = () => !!(window.mwShutOn && window.mwShutOn());
  const ki = () => ((game() || {}).shut || {}).ki || {};
  const mode = () => Date.now() - KH.t < 4000 ? KH.mode : (MODES.includes(ki().mode) ? ki().mode : "off");
  function set(m) {
    if (KH.busy) return;
    KH.busy = true;
    post("/api/sim", {action: "kihilfe", mode: m, lang: LANG}).then(r => {
      KH.busy = false; r = r || {};
      if (!r.ok) { if (typeof toast === "function") toast("⚠ " + (r.error || T("error"))); return; }
      KH.mode = (r.ki || {}).mode || m; KH.t = Date.now();
      if (typeof toast === "function") toast("🤖 " + T(NAMES[KH.mode]) + (KH.mode !== "off" ? " · " + T("this round does not count for the leaderboard") : ""));
      paint();
    }).catch(() => { KH.busy = false; });
  }
  const next = () => set(MODES[(MODES.indexOf(mode()) + 1) % MODES.length]);
  BT.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); next(); });
  ["pointerdown", "pointerup", "dblclick"].forEach(k => BT.addEventListener(k, e => e.stopPropagation()));
  window.mwKiOn = roundOn;                                 // 538: in such a round L2 = the next help
  window.mwKiCycle = next;
  function picRect(v) {
    const r = v.getBoundingClientRect(), nw = v.naturalWidth || 16, nh = v.naturalHeight || 9;
    const fit = getComputedStyle(v).objectFit, k = fit === "cover" ? Math.max(r.width / nw, r.height / nh) : fit === "fill" ? 0 : Math.min(r.width / nw, r.height / nh);
    const w = k ? nw * k : r.width, h = k ? nh * k : r.height;
    return {left: r.left + (r.width - w) / 2, top: r.top + (r.height - h) / 2, width: w, height: h};
  }
  const hits = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  let sig = "";
  function paint() {
    const v = document.getElementById("video"), on = roundOn() && v && v.offsetParent !== null;
    if (!on) { CV.hidden = BT.hidden = true; return; }
    const cont = v.parentNode;
    if (CV.parentNode !== cont) cont.append(CV, BT);   // 549: BT may sit in Sim-Kompakt (below)
    if (getComputedStyle(cont).position === "static") cont.style.position = "relative";
    const cr = cont.getBoundingClientRect(), p = picRect(v);
    const vis = {left: Math.max(p.left, cr.left), top: Math.max(p.top, cr.top), right: Math.min(p.left + p.width, cr.right), bottom: Math.min(p.top + p.height, cr.bottom)};
    if (vis.right - vis.left < 60 || vis.bottom - vis.top < 60) { CV.hidden = BT.hidden = true; return; }
    const md = mode(), K = ki();
    // the button: top left of the picture, moved down until nothing else is there (gauges of 543, view buttons)
    let tx = "🤖 " + T(NAMES[md]), sub = "";
    if (md === "auto" && K.pause > 0) sub = T("paused") + " " + Math.ceil(K.pause) + " s – " + T("you steer");
    else if (md !== "off") sub = T("round with AI help");
    const s2 = tx + "|" + sub;
    if (s2 !== sig) { sig = s2; BT.textContent = tx; if (sub) { const sm = E("small"); sm.textContent = sub; BT.appendChild(sm); }
      BT.title = T("AI help for this round: off → AI frames → AI aims → AI autopilot (L2 on the controller). With AI help the round does not count for the leaderboard."); BT.setAttribute("aria-label", BT.title); }
    BT.classList.toggle("on", md !== "off"); BT.classList.toggle("pz", md === "auto" && K.pause > 0);
    BT.hidden = false;
    const SK = window.skSlot ? window.skSlot("kih") : null;   // 549 Sim-Kompakt: next to the head stick, not on the small picture
    if (SK && BT.parentNode !== SK) SK.appendChild(BT); else if (!SK && BT.parentNode !== cont) cont.appendChild(BT);
    if (SK) { BT.style.left = BT.style.top = ""; }
    const bw = BT.offsetWidth || 120, bh = BT.offsetHeight || 36, m = 10;
    const obs = [...cont.querySelectorAll("button, .vtag, #vo-ctl, #vo-mctl, #lv-tools, [role=application]")].concat([...document.querySelectorAll("#mwt, #pv-bar, #pv-x, #lv-vw .lv-vbtn, #iconhint, #pip")])
      .filter(x => x !== BT && !x.contains(v) && !x.hidden).map(x => x.getBoundingClientRect()).filter(r => r.width > 2 && r.height > 2 && r.width * r.height < 0.45 * p.width * p.height);
    let pos = {x: vis.left + m, y: vis.top + m};
    for (let y = vis.top + m; y <= vis.bottom - bh - m; y += 8) { const c = {left: vis.left + m - 2, top: y - 2, right: vis.left + m + bw + 2, bottom: y + bh + 2}; if (!obs.some(o => hits(c, o))) { pos.y = y; break; } }
    if (!SK) { BT.style.left = (pos.x - cr.left) + "px"; BT.style.top = (pos.y - cr.top) + "px"; }
    // the boxes: MoveEye's persons in this picture (green; dashed = not confirmed by the AI)
    const S = ST(), bx = (md !== "off" && S.persons) ? (S.person_boxes || []) : [], sure = S.person_sure || [];
    CV.hidden = !bx.length;
    if (!bx.length) return;
    const dp = devicePixelRatio || 1;
    CV.style.left = (p.left - cr.left) + "px"; CV.style.top = (p.top - cr.top) + "px"; CV.style.width = p.width + "px"; CV.style.height = p.height + "px";
    if (CV.width !== Math.round(p.width * dp) || CV.height !== Math.round(p.height * dp)) { CV.width = Math.round(p.width * dp); CV.height = Math.round(p.height * dp); }
    const x = CV.getContext("2d"); x.setTransform(dp, 0, 0, dp, 0, 0); x.clearRect(0, 0, p.width, p.height);
    bx.forEach((b, i) => {
      const ok = i >= sure.length || !!sure[i], X = b[0] * p.width, Y = b[1] * p.height, W = b[2] * p.width, H = b[3] * p.height;
      x.setLineDash(ok ? [] : [9, 7]); x.lineWidth = 4; x.strokeStyle = "rgba(0,0,0,.5)"; x.strokeRect(X, Y, W, H);
      x.lineWidth = 2.5; x.strokeStyle = "#34ff6a"; x.strokeRect(X, Y, W, H);
    });
    x.setLineDash([]);
  }
  setInterval(paint, 150);
  addEventListener("resize", paint); addEventListener("scroll", paint, {passive: true});
  addEventListener("keydown", e => { if (e.code === "KeyK" && e.shiftKey && roundOn()) { e.preventDefault(); next(); } });   // PC: Shift + K
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", KIH_JS + "</body>", 1)

# the manual (HELP_PAGE of 540): one paragraph after «Auslöser», German and English
_KIH_HELP = (
    ("ausserhalb einer Runde ein Schuss auf die Bildmitte.</p>",
     "<p><b>🤖 KI-Hilfe am Auslöser:</b> Wer mit dem Auslöser bewacht, kann für die laufende Runde Hilfe der KI einschalten: "
     "Knopf «🤖» oben links im Live-Bild (Controller-Ansicht: L2; Handy des Wächters: Knopf «KI»; Simulator-PC: Knopf neben dem "
     "Auslöser oder Taste K). <b>KI-Rahmen</b> zeigt die Erkennung von MoveEye im Bild (Personen grün, unsichere gestrichelt), "
     "<b>KI zielt</b> lässt den Kopf der erkannten Person folgen (du drückst ab), der <b>KI-Autopilot</b> zielt und drückt selbst ab, "
     "wenn er sicher ist (0,5 s im Kreis, Energie und Sperre gelten). Jede Eingabe von dir (Stick, Joystick, Auslöser) pausiert "
     "den Autopiloten 5 s. Eine Runde mit KI-Hilfe zählt nicht für Rangliste und Abzeichen und ist im Ergebnis und im Spielbericht "
     "markiert. Ohne KI-Hilfe zeigt das Live-Bild während der Runde keine Erkennungsrahmen.</p>"),
    ("outside a round too.</p>",
     "<p><b>🤖 AI help at the shutter:</b> whoever guards with the shutter can switch on help of the AI for the running round: "
     "button «🤖» at the top left of the live picture (controller view: L2; phone of the guard: button «KI»; simulator PC: button "
     "next to the shutter or key K). <b>AI frames</b> shows MoveEye's detection in the picture (persons green, uncertain dashed), "
     "<b>AI aims</b> lets the head follow the detected person (you press the shutter), the <b>AI autopilot</b> aims and fires by "
     "itself when it is sure (0.5 s in the circle; energy and lock apply). Any input of yours (stick, joystick, shutter) pauses the "
     "autopilot for 5 s. A round with AI help does not count for the leaderboard and badges and is marked in the result and the "
     "game report. Without AI help the live picture shows no detection boxes during the round.</p>"))
for _a, _b in _KIH_HELP:
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
