#@ MoveEye – Teil 312: Assistent «Erkennung verbessern» – ein geführter Ablauf statt sechs einzelner Funktionen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Konzept, Wunsch Daniel): sechs Funktionen drehten an denselben Schwellen (Empfindlichkeit, Mindestgrösse, KI-Schwelle …):
# Testlauf «Automatisch optimieren» (310), A/B-Vergleich (141), Auto-Tuner (190), «Schwellen automatisch» (143),
# Trainings-Nacht (141), Wochen-Check / Fehlalarm-Lernen (143). Jetzt gibt es EINEN Assistenten in Schritten:
#   1 Prüfen      - ist der Simulator verbunden, ist der Schutz aus, läuft nichts anderes?
#   2 Wie gründlich? - schnell (Tag) oder gründlich (Tag + Nacht)
#   3 Verbessern  - Messen, Vorschläge ausprobieren, nur Besseres behalten (die bewährte Optimierung aus 310)
#   4 Ergebnis    - vorher → nachher, was geändert wurde; «Behalten» oder «Rückgängig»
#   5 Dranbleiben - Auto-Tuner am echten Ort (Schalter mit Erklärung); Trainings-Nacht, Wochen-Check, Fehlalarm-Lernen ab 2.98.24
#                   nur noch als Kacheln der Simulator-Zentrale (ein Verweis darauf)
# Die einzelnen Funktionen bleiben im Simulator-Tab unter «Experte». Es läuft immer nur eine (gemeinsame Sperre
# simtask_busy, 141); der Auto-Tuner macht Pause, solange eine davon misst (autotune_paused, aufgerufen in 190).
# ----------------------------------------------------------------------------
TUNEA = {"busy": False, "step": "", "depth": "", "plans": [], "i": 0, "stop": False, "t0": 0.0, "start_cfg": None, "last": None}
TUNEA_KEYS = ("auto_tune", "train_night_on", "weekcheck_on", "fa_learn_auto")


def autotune_paused():
    """2.98.14: the auto-tuner holds still while anything measures or trains with the simulator (fixed values needed) -
    test run, optimization, A/B, training night, thresholds, false alarm learning, blind spots, this assistant"""
    try:
        if TESTOPT.get("busy") or ABT.get("busy") or TRAIN.get("busy") or TUNEA.get("busy"):
            return True
        for ref in ("AUTOTH", "FALEARN", "BLIND"):
            d = globals().get(ref)
            if isinstance(d, dict) and d.get("busy"):
                return True
    except Exception:
        return False
    return False


def _tunea_plans(depth):
    return [("quick", 3)] if depth == "quick" else [("quick", 4), ("night", 4)]


def tune_assist_check(L=None):
    """step 1: what is missing for the measuring (empty list = ready)"""
    T = lambda x: tr(x, L)
    miss = []
    if not CFG.get("sim_on"):
        miss.append({"id": "sim", "text": T("The simulation is off - switch it on in the tab Simulator (a 3D simulator on a PC is needed)."), "fix": "/sim"})
    elif not sim_ready():
        miss.append({"id": "sim", "text": T("No simulator answers - start the 3D simulator on the PC."), "fix": "/sim"})
    if is_armed():
        miss.append({"id": "armed", "text": T("Protection is on - the test needs it off (a test person would give a real alarm)."), "fix": "/protect"})
    b = simtask_busy("improve assistant")
    if b:
        miss.append({"id": "busy", "text": trf("The simulator is busy: {what}", L, what=tr(b, L)), "fix": ""})
    return miss


def tune_assist_start(depth="quick"):
    if TUNEA["busy"]:
        return False, "already running"
    miss = tune_assist_check()
    if miss:
        return False, miss[0]["text"]
    depth = "thorough" if depth == "thorough" else "quick"
    TUNEA.update(busy=True, step="measure", depth=depth, plans=[], i=0, stop=False, t0=time.time(), start_cfg=opt_snapshot())
    threading.Thread(target=_tunea_thread, args=(depth,), daemon=True, name="tune-assist").start()
    log_event("sys", f"Improve detection: started ({depth})")
    return True, ""


def _tunea_thread(depth):
    res = []
    try:
        for i, (plan, tries) in enumerate(_tunea_plans(depth)):
            if TUNEA["stop"]:
                break
            TUNEA.update(i=i, step=plan)
            _sim_free()
            _testopt_thread("auto", plan, tries)             # base run, try the proposals, keep only what is clearly better
            A = TESTOPT.get("auto") or {}
            res.append({"plan": plan, "base": A.get("base"), "best": A.get("best"),
                        "kept": [{"id": x["id"], "title": x["title"]} for x in A.get("log", []) if x.get("kept")]})
            TUNEA["plans"] = list(res)
    except Exception as e:
        log_event("sys", f"Improve detection: {type(e).__name__}: {e}"[:160])
    finally:
        start = TUNEA.get("start_cfg") or {}
        changed = [[k, start[k], CFG[k]] for k in start if k in CFG and CFG[k] != start[k]]
        TUNEA.update(busy=False, step="", last={"t": time.time(), "depth": depth, "plans": res, "changed": changed,
                                                "stopped": bool(TUNEA["stop"]), "start_cfg": start, "min": round((time.time() - TUNEA["t0"]) / 60.0, 1),
                                                "msg": str(TESTOPT.get("msg") or "")})
        _tunea_autotune_base()
        log_event("sys", "Improve detection: done - " + ("; ".join(f"{r['plan']} {r['base']} -> {r['best']}" for r in res) or "no result")
                  + (f", {len(changed)} value(s) changed" if changed else ", nothing changed"))


def _tunea_autotune_base():
    """the auto-tuner takes the measured values as its new starting point (no new calibration that would undo them)"""
    w = WATCH_REF.get("w")
    tu = getattr(w, "tuner", None) if w is not None else None
    if tu is not None:
        try:
            tu.calibrated = True; tu.base_min_area = float(CFG["min_area"]); tu.last_eval = time.time()
        except Exception:
            pass
    try:                                                     # 2.98.15 (577): the measured values = the middle of the ±20 %
        autotune_base_set("assistant")
    except Exception as e:
        log_event("sys", f"Auto-tune base: {e}"[:120])


def tune_assist_stop():
    TUNEA["stop"] = True; TESTOPT["stop"] = True
    try:
        _simtest("test_stop")
    except Exception:
        pass
    return True, ""


def tune_assist_undo():
    """«Rückgängig»: the values from before the assistant come back"""
    if TUNEA["busy"]:
        return False, "the assistant is still running"
    last = TUNEA.get("last") or {}
    snap = last.get("start_cfg")
    if not snap:
        return False, "nothing to undo"
    opt_restore(snap, "improve detection: undo")
    last["undone"] = True; last["changed"] = []
    _tunea_autotune_base()
    return True, ""


def tune_assist_set(key, on):
    if key not in TUNEA_KEYS:
        return False, "unknown setting"
    CFG[key] = bool(on)
    sched_user_changed(key)
    save_settings()
    log_event("sys", f"Improve detection: {key} {'on' if on else 'off'}")
    return True, ""


def tune_assist_state(lang=None):
    L = norm_lang(lang) if lang else cur_lang()
    A = TESTOPT.get("auto") or {}
    run = TESTOPT.get("sim") or {}
    last = TUNEA.get("last")
    if last:
        last = {k: v for k, v in last.items() if k != "start_cfg"}
        last["can_undo"] = bool((TUNEA.get("last") or {}).get("start_cfg")) and not last.get("undone") and bool(last.get("changed"))
    runs = [r for r in TESTOPT.get("runs", []) if r.get("score") is not None]
    return {"ok": True, "busy": TUNEA["busy"], "step": TUNEA["step"], "depth": TUNEA["depth"], "i": TUNEA["i"],
            "n": len(_tunea_plans(TUNEA["depth"] or "quick")), "plans": TUNEA["plans"],
            "now": {"try": A.get("step", 0), "tries": A.get("tries", 0), "what": A.get("now", ""), "base": A.get("base"), "best": A.get("best"),
                    "running": bool(isinstance(run, dict) and run.get("running")), "left": run.get("left_s") if isinstance(run, dict) else None,
                    "total": run.get("total_s") if isinstance(run, dict) else None},
            "missing": tune_assist_check(L), "last": last, "score": runs[-1]["score"] if runs else None,
            "keys": {k: bool(CFG.get(k)) for k in TUNEA_KEYS}, "train_hour": int(CFG.get("train_hour", 1)),
            "auto_status": str(STATE.get("auto_status") or ""), "simple": bool(CFG.get("ui_simple")), "sim_on": bool(CFG.get("sim_on"))}


# ---- the page part (main page: Einstellungen → Erkennung; Simulator tab: tile «Erkennung verbessern») ------------------------
TUNE_CSS = r"""
.mwt-ov{position:fixed;inset:0;z-index:260;background:rgba(0,0,0,.66);display:flex;align-items:center;justify-content:center;padding:12px}
.mwt-card{background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:18px;padding:16px 16px 14px;
  width:min(520px,100%);max-height:92vh;overflow:auto;box-sizing:border-box;display:flex;flex-direction:column;gap:10px;font:15px/1.45 system-ui,sans-serif}
.mwt-card h3{margin:0;font-size:18px}.mwt-card p{margin:0}.mwt-mut{color:var(--mut,#8a9bb0);font-size:13px}
.mwt-steps{display:flex;gap:4px}.mwt-steps i{flex:1;height:5px;border-radius:3px;background:var(--line,#1f2b3a)}.mwt-steps i.on{background:var(--acc,#3b8cff)}
.mwt-steps i.done{background:var(--grn,#3fcf6b)}
.mwt-opt{display:flex;gap:12px;align-items:center;text-align:left;padding:12px;border-radius:14px;border:1px solid var(--line,#1f2b3a);
  background:var(--panel2,#151e2b);color:inherit;font:inherit;cursor:pointer;width:100%}
.mwt-opt.on{outline:2px solid var(--acc,#3b8cff)}.mwt-opt .ic{font-size:26px}.mwt-opt small{display:block;color:var(--mut,#8a9bb0);font-size:12.5px}
.mwt-item{display:flex;gap:8px;align-items:flex-start;padding:8px 10px;border-radius:12px;background:rgba(255,255,255,.04);font-size:14px}
.mwt-item a{color:var(--acc,#3b8cff);white-space:nowrap}
.mwt-nav{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:4px}.mwt-nav button{min-width:96px}
.mwt-bar{height:8px;border-radius:4px;background:var(--line,#1f2b3a);overflow:hidden}.mwt-bar i{display:block;height:100%;background:var(--acc,#3b8cff);transition:width .5s}
.mwt-sw{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:8px 0;border-top:1px solid var(--line,#1f2b3a);cursor:pointer}
.mwt-sw span{flex:1}.mwt-sw small{display:block;color:var(--mut,#8a9bb0);font-size:12.5px}
.mwt-res{font-size:15px;padding:10px;border-radius:12px;background:rgba(63,207,107,.08);border-left:4px solid var(--grn,#3fcf6b)}
.mwt-res.same{background:rgba(255,255,255,.04);border-left-color:var(--mut,#8a9bb0)}
.mwt-entry{display:flex;flex-direction:column;gap:8px}.mwt-entry button{width:100%}
"""

TUNE_JS = r"""
(function () {
  const DE = {"Improve detection": "Erkennung verbessern", "MoveEye tests itself in the 3D simulator: people and animals walk past, and the simulator knows exactly what MoveEye should have reported. The assistant tries changes and keeps only what is clearly better.": "MoveEye testet sich selbst im 3D-Simulator: dort gehen Personen und Tiere vorbei, und der Simulator weiss genau, was MoveEye hätte melden müssen. Der Assistent probiert Änderungen aus und behält nur, was klar besser ist.",
    "Check": "Prüfen", "How thorough?": "Wie gründlich?", "Improving": "Verbessern", "Result": "Ergebnis", "Keep it up": "Dranbleiben",
    "Everything ready.": "Alles bereit.", "Still missing:": "Fehlt noch:", "open": "öffnen", "Next": "Weiter", "Back": "Zurück", "Close": "Schliessen", "Start": "Starten", "Stop": "Stopp",
    "Without the simulator": "Ohne Simulator", "Quick": "Schnell", "Thorough": "Gründlich",
    "only the day test, up to 3 tries - about 10 to 20 minutes": "nur der Tag-Test, bis 3 Versuche – etwa 10 bis 20 Minuten", "day and night, up to 4 tries each - about 40 to 60 minutes": "Tag und Nacht, je bis 4 Versuche – etwa 40 bis 60 Minuten",
    "You can close the page - the assistant keeps running. The auto-tuner pauses meanwhile.": "Du kannst die Seite schliessen – der Assistent läuft weiter. Der Auto-Tuner macht so lange Pause.",
    "Day": "Tag", "Night": "Nacht", "first a test run as it is now": "zuerst ein Testlauf, so wie es jetzt ist", "Try": "Versuch", "still about": "noch etwa", "min": "Min.",
    "starting …": "startet …", "Score": "Punkte", "kept": "behalten", "nothing was clearly better - everything stays as it was": "nichts war klar besser – alles bleibt, wie es war",
    "values changed": "Werte geändert", "Keep": "Behalten", "Undo": "Rückgängig", "Undone - the values from before are back.": "Rückgängig gemacht – die Werte von vorher sind zurück.",
    "stopped": "abgebrochen", "Last time": "Letztes Mal", "Running": "Läuft",
    "Auto-tuner at the real place": "Auto-Tuner am echten Ort", "adapts the sensitivity to the place all the time (wind, light); starts from the measured values": "passt die Empfindlichkeit laufend an den Ort an (Wind, Licht); startet von den gemessenen Werten aus",
    "Training night": "Trainings-Nacht", "every night test runs in several scenes and the same improving - only when protection is off": "jede Nacht Testläufe in mehreren Szenen und dasselbe Verbessern – nur wenn der Schutz aus ist",
    "Weekly check": "Wochen-Check", "every Sunday night a test run; a push when it got worse": "jeden Sonntag in der Nacht ein Testlauf; ein Push, wenn es schlechter wurde",
    "False alarm learning": "Fehlalarm-Lernen", "mark a recording with 👎 and the simulator re-enacts it and learns from it": "markierst du eine Aufnahme mit 👎, stellt der Simulator sie nach und lernt daraus",
    "Training night, weekly check, false alarm learning: tiles in the Simulator centre": "Trainings-Nacht, Wochen-Check, Fehlalarm-Lernen: Kacheln in der Simulator-Zentrale",
    "Single tools (Expert)": "Einzelne Werkzeuge (Experte)", "Test run, A/B comparison, thresholds automatic … in the tab Simulator, Simulator centre (view «Expert»).": "Testlauf, A/B-Vergleich, Schwellen automatisch … im Tab Simulator, Simulator-Zentrale (Ansicht «Experte»).",
    "One guided flow: check, measure, improve, see the result. Replaces the single tools (they stay in «Expert»).": "Ein geführter Ablauf: prüfen, messen, verbessern, Ergebnis ansehen. Ersetzt die einzelnen Werkzeuge (die bleiben unter «Experte»).",
    "the simulator is needed for measuring": "zum Messen braucht es den Simulator", "Auto-tune": "Auto-Tuner",
    "Calm down wind and cloud shadows": "Wind und Wolkenschatten beruhigen", "AI confirms every person": "KI bestätigt jede Person", "Stronger rain and snow filter": "Stärkerer Regen- und Schnee-Filter",
    "Ignore changes of the light": "Lichtwechsel nicht beachten", "Do not take animals for persons": "Tiere nicht für Personen halten", "Less sensitive": "Weniger empfindlich",
    "See better in the dark": "Im Dunkeln besser sehen", "Find small and crouching persons": "Kleine und geduckte Personen finden", "Catch fast persons": "Schnelle Personen erwischen",
    "More sensitive by day": "Am Tag empfindlicher", "React faster": "Schneller reagieren"};
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || "de"; } catch (e) { return "de"; } };
  const tt = k => { try { if (typeof t === "function" && t(k) !== k) return t(k); } catch (e) {} const x = window.LX ? window.LX(k) : ""; return x || (L() === "en" ? k : (DE[k] || k)); };
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const B = (txt, fn, cls) => { const b = E("button", cls == null ? "" : cls, txt); b.type = "button"; b.onclick = fn; return b; };
  let S = null, ov = null, step = 1, depth = "quick", poll = null, seenLast = 0;
  const api = async (d) => { try { const r = d ? await (await fetch("/api/tune", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})).json()
      : await (await fetch("/api/tune?lang=" + L())).json(); if (r && r.ok !== undefined) S = r; if (r && r.ok === false && r.error && typeof toast === "function") toast("⚠ " + r.error); return r; } catch (e) { return null; } };
  const planName = p => p === "night" ? "🌙 " + tt("Night") : "☀ " + tt("Day");
  const dur = s => s == null ? "" : Math.max(1, Math.round(s / 60)) + " " + tt("min");
  function resultBox(last) {
    const box = E("div");
    (last.plans || []).forEach(r => { const up = r.base != null && r.best != null ? r.best - r.base : 0;
      const d = E("div", "mwt-res" + (r.kept && r.kept.length ? "" : " same")); d.append(E("b", "", planName(r.plan) + ": " + tt("Score") + " " + (r.base != null ? r.base : "–") + " → " + (r.best != null ? r.best : "–") + (up > 0 ? "  (+" + Math.round(up * 10) / 10 + ")" : "")));
      d.appendChild(E("div", "mwt-mut", r.kept && r.kept.length ? tt("kept") + ": " + r.kept.map(x => tt(x.title)).join(", ") : tt("nothing was clearly better - everything stays as it was")));
      d.style.marginBottom = "6px"; box.appendChild(d); });
    if (!(last.plans || []).length) box.appendChild(E("div", "mwt-res same", last.msg ? "⚠ " + tt(last.msg) : tt("nothing was clearly better - everything stays as it was")));
    if (last.stopped) box.appendChild(E("div", "mwt-mut", "⏹ " + tt("stopped")));
    if (last.undone) box.appendChild(E("div", "mwt-mut", "↩ " + tt("Undone - the values from before are back.")));
    else if ((last.changed || []).length) box.appendChild(E("div", "mwt-mut", last.changed.length + " " + tt("values changed") + ": " + last.changed.map(c => c[0] + " " + c[1] + " → " + c[2]).join(" · ")));
    return box;
  }
  function render() {
    if (!ov || !S) return;
    const c = ov.firstChild; c.textContent = "";
    if (S.busy) step = 3;
    const st = E("div", "mwt-steps"); for (let i = 1; i <= 5; i++) { const x = E("i", i === step ? "on" : i < step ? "done" : ""); st.appendChild(x); } c.appendChild(st);
    const names = ["Check", "How thorough?", "Improving", "Result", "Keep it up"];
    c.appendChild(E("h3", "", "🎯 " + tt("Improve detection") + " · " + step + "/5 " + tt(names[step - 1])));
    const nav = E("div", "mwt-nav");
    const close = B(tt("Close"), () => tuneClose(), "sec");
    if (step === 1) {
      c.appendChild(E("p", "", tt("MoveEye tests itself in the 3D simulator: people and animals walk past, and the simulator knows exactly what MoveEye should have reported. The assistant tries changes and keeps only what is clearly better.")));
      const miss = S.missing || [];
      if (!miss.length) c.appendChild(E("div", "mwt-item", "✅ " + tt("Everything ready.")));
      else { c.appendChild(E("b", "", tt("Still missing:"))); miss.forEach(m => { const it = E("div", "mwt-item"); it.appendChild(E("span", "", "⚠ " + m.text));
        if (m.fix) { const a = E("a", "", tt("open") + " ›"); a.href = m.fix; it.appendChild(a); } c.appendChild(it); }); }
      if (S.last) { c.appendChild(E("b", "", tt("Last time") + " (" + new Date(S.last.t * 1000).toLocaleString([], {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"}) + ")")); c.appendChild(resultBox(S.last)); }
      if (miss.length) nav.appendChild(B(tt("Without the simulator") + " ›", () => { step = 5; render(); }, "sec"));
      const nx = B(tt("Next") + " ›", () => { step = 2; render(); }); nx.disabled = !!miss.length; nav.append(close, nx);
    } else if (step === 2) {
      [["quick", "⚡", "Quick", "only the day test, up to 3 tries - about 10 to 20 minutes"], ["thorough", "🔬", "Thorough", "day and night, up to 4 tries each - about 40 to 60 minutes"]].forEach(([v, ic, n, note]) => {
        const b = E("button", "mwt-opt" + (depth === v ? " on" : "")); b.type = "button"; const tx = E("span"); tx.append(E("b", "", tt(n)), E("small", "", tt(note)));
        b.append(E("span", "ic", ic), tx); b.onclick = () => { depth = v; render(); }; c.appendChild(b); });
      c.appendChild(E("div", "mwt-mut", tt("You can close the page - the assistant keeps running. The auto-tuner pauses meanwhile.")));
      nav.append(B("‹ " + tt("Back"), () => { step = 1; render(); }, "sec"), B("▶ " + tt("Start"), async () => { const r = await api({do: "start", depth: depth}); if (r && r.ok) { step = 3; seenLast = 0; } render(); }));
    } else if (step === 3) {
      const N = S.now || {}, plan = (S.n > 1 ? (S.i + 1) + "/" + S.n + " · " : "") + planName(S.step || "quick");
      c.appendChild(E("b", "", "⏳ " + tt("Running") + ": " + plan));
      c.appendChild(E("div", "", N.tries ? "🤖 " + tt("Try") + " " + (N.try || 0) + "/" + N.tries + " · " + (N.what ? tt(N.what) : tt("first a test run as it is now")) : tt("starting …")));
      if (N.base != null) c.appendChild(E("div", "mwt-mut", tt("Score") + ": " + N.base + " → " + (N.best != null ? N.best : "…")));
      const bar = E("div", "mwt-bar"), i = E("i"); const pct = N.total ? Math.max(2, Math.min(100, 100 * (1 - (N.left || 0) / N.total))) : 3; i.style.width = pct + "%"; bar.appendChild(i); c.appendChild(bar);
      if (N.running && N.left != null) c.appendChild(E("div", "mwt-mut", tt("still about") + " " + dur(N.left)));
      (S.plans || []).forEach(r => c.appendChild(E("div", "mwt-mut", "✓ " + planName(r.plan) + ": " + r.base + " → " + r.best)));
      c.appendChild(E("div", "mwt-mut", tt("You can close the page - the assistant keeps running. The auto-tuner pauses meanwhile.")));
      if (!S.busy) { step = 4; return render(); }
      nav.append(close, B("⏹ " + tt("Stop"), () => api({do: "stop"}).then(render), "sec"));
    } else if (step === 4) {
      if (S.last) c.appendChild(resultBox(S.last)); else c.appendChild(E("div", "mwt-mut", "–"));
      if (S.last && S.last.can_undo) nav.appendChild(B("↩ " + tt("Undo"), () => api({do: "undo"}).then(render), "sec"));
      nav.appendChild(B((S.last && S.last.can_undo ? "✓ " + tt("Keep") : tt("Next")) + " ›", () => { step = 5; render(); }));
    } else {
      const K = S.keys || {};
      const sw = (key, title, note) => { const l = E("label", "mwt-sw"); const tx = E("span"); tx.append(E("b", "", tt(title)), E("small", "", tt(note)));
        const cb = E("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!K[key]; cb.onchange = () => api({do: "set", key: key, on: cb.checked}).then(render);
        l.append(tx, cb); c.appendChild(l); };
      sw("auto_tune", "Auto-tuner at the real place", "adapts the sensitivity to the place all the time (wind, light); starts from the measured values");
      if (S.auto_status && K.auto_tune) c.appendChild(E("div", "mwt-mut", "🎚 " + tt("Auto-tune") + ": " + tt(S.auto_status)));
      // 2.98.24 («Sim-Schalter nur einmal»): Trainings-Nacht, Wochen-Check, Fehlalarm-Lernen are switched in their tiles only
      { const tl = E("div", "mwt-mut"); const ta = E("a", "", "🎛 " + tt("Training night, weekly check, false alarm learning: tiles in the Simulator centre") + " ›"); ta.href = "/sim#c-hub"; ta.style.color = "var(--acc,#3b8cff)"; tl.appendChild(ta); c.appendChild(tl); }
      const ex = E("div", "mwt-mut"); const a = E("a", "", "🧰 " + tt("Single tools (Expert)") + " ›"); a.href = "/sim#c-hub"; a.style.color = "var(--acc,#3b8cff)"; ex.append(a, E("div", "", tt("Test run, A/B comparison, thresholds automatic … in the tab Simulator, Simulator centre (view «Expert»)."))); c.appendChild(ex);
      nav.append(B("‹ " + tt("Back"), () => { step = S.last ? 4 : 1; render(); }, "sec"), B("✓ " + tt("Close"), () => tuneClose()));
    }
    c.appendChild(nav);
  }
  function tuneClose() { if (ov) ov.remove(); ov = null; if (poll) clearInterval(poll); poll = null; entryPaint(); }
  async function tuneOpen() {
    await api(); if (!S) return;
    step = S.busy ? 3 : 1;
    if (ov) ov.remove(); ov = E("div", "mwt-ov"); ov.appendChild(E("div", "mwt-card")); document.body.appendChild(ov);
    ov.onclick = e => { if (e.target === ov) tuneClose(); };
    render();
    if (poll) clearInterval(poll);
    poll = setInterval(async () => { if (!ov) return; const was = S && S.busy; await api(); if (step === 3 || (was && !S.busy)) render(); }, 2500);
  }
  window.mwTune = {open: tuneOpen, state: () => S};
  function entryPaint() {                                   // the entry under Einstellungen → Erkennung
    const box = document.getElementById("tune-box"); if (!box) return;
    if (!box.dataset.built) { box.dataset.built = 1; box.className = "mwt-entry";
      box.append(E("div", "mut", tt("One guided flow: check, measure, improve, see the result. Replaces the single tools (they stay in «Expert»).")), B("🎯 " + tt("Improve detection") + " ›", () => tuneOpen()), E("div", "mut")); box.lastChild.id = "tune-st"; }
    const st = document.getElementById("tune-st"); if (!st || !S) return;
    st.textContent = S.busy ? "⏳ " + tt("Running") + " · " + planName(S.step || "quick") : S.last ? tt("Last time") + ": " + (S.last.plans || []).map(r => planName(r.plan) + " " + r.base + " → " + r.best).join(" · ")
      : (S.missing || []).some(m => m.id === "sim") ? "🧪 " + tt("the simulator is needed for measuring") : "";
  }
  function simPagePaint() {                                 // page Simulator, card «Test run»: «Simple» = the assistant instead of «optimize»
    const ta = document.getElementById("tr-auto"); if (!ta || !S) return;
    ta.hidden = !!S.simple;
    let tb = document.getElementById("tr-tune");
    if (!tb) { tb = B("🎯 " + tt("Improve detection"), () => tuneOpen(), "sec"); tb.id = "tr-tune"; ta.after(tb); }
    tb.hidden = !S.simple;
  }
  document.addEventListener("DOMContentLoaded", () => { if (document.getElementById("tr-auto")) api().then(simPagePaint); });
  document.addEventListener("DOMContentLoaded", () => { if (!document.getElementById("tune-box")) return;
    api().then(entryPaint); setTimeout(entryPaint, 2500); setInterval(() => { if (!document.hidden && document.getElementById("tune-box")) api().then(entryPaint); }, 20000); });
})();
"""


def tune_head():
    return "<style>" + TUNE_CSS + "</style><script>" + TUNE_JS + "</script>"
