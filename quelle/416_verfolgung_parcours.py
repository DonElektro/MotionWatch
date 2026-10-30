#@ MoveEye – Teil 416: Verfolgungs-Parcours des Simulators (Lektionen starten, Läufe speichern, A/B-Vergleich, Auto-Tuning nur als Vorschlag, mit / ohne Weitwinkel-Übergabe, Spiel «Entkomme der Kamera»), Vorausschauen beim Folgen, Kachel 🎯 in der Simulator-Zentrale. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Plan Daniel 30.10.2026 (docs/Verfolgungs_Parcours.md). The simulator (3D-4.18, parcours.gd) knows where the figures really
# are and measures: aim error, time in the picture, losses, swinging, servo travel, identity switches -> grade. MoveEye
# only starts the lessons (sim control «parcours»), keeps the runs with the values of the following that were used, and
# compares them. Nothing is changed by itself: the auto-tuning only PROPOSES a set (button «übernehmen»).
#  * The regulators of the following are the normal settings (same CFG keys as in Settings → Camera / Servos and «Servo
#    motion & safety»): track_gain, track_deadzone, track_lead (new, 0 = as before), servo_vmax_pan. The tile shows them
#    again as a shortcut (live).
#  * track_lead («look ahead»): the head aims where the target will be in track_lead seconds (speed of the direction of
#    the target, measured from the servo position + where it is in the picture). 0 = exactly the behaviour of before.
#  * During a run (only then): following on, smart round off, manual hold 1 s, back home after 5 s - restored afterwards.
#  * One lock (147): «tracking parcours» while it runs.
# Translations: part 569. Window: part 599.
# ----------------------------------------------------------------------------
for _k, _v in {"track_lead": 0.0}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

PARC_KEYS = ("servo_vmax_pan", "track_gain", "track_deadzone", "track_lead")
PARC_LIM = {"servo_vmax_pan": (10.0, 400.0), "track_gain": (0.1, 2.0), "track_deadzone": (0.02, 0.3), "track_lead": (0.0, 1.0)}
PARC_RUN_KEYS = ("track_person", "track_motion", "kopf_round", "manual_hold", "kopf_return_s")
PARC = {"busy": False, "kind": "", "step": "", "stop": False, "runs": None, "ab": None, "tune": None, "ww": None, "err": "", "sim": {}}
PARC_FILE = "parcours_runs.json"
PARC_AB = {"lead": ("Look ahead 0.3 s", {"track_lead": 0.3}), "gain": ("Gain +40 %", {"track_gain": "*1.4"}),
           "dead": ("Dead zone 0.05", {"track_deadzone": 0.05}), "fast": ("Speed 200 °/s", {"servo_vmax_pan": 200.0})}


def parc_params():
    return {k: float(CFG.get(k) or 0.0) for k in PARC_KEYS}


def parc_clip(k, v):
    lo, hi = PARC_LIM[k]
    return round(max(lo, min(hi, float(v))), 3)


# ---- look ahead (prediction) for the following of 410 -------------------------------------------------------------------
_PRED = {"hist": deque(maxlen=16)}


def parc_lead_shift(now, bear, hf, pw, lead, hist=None):
    """how many pixels to shift the target box: the direction of the target (degrees, world) moves with v °/s -> aim
    where it is in `lead` s. hist: [(t, bearing)] (kept here). Returns 0 until there is a short history."""
    H = _PRED["hist"] if hist is None else hist
    if H and (now - H[-1][0] > 1.0 or abs(bear - H[-1][1]) > 25.0):
        H.clear()                                         # another target / a jump: start again
    H.append((now, bear))
    pts = [p for p in H if now - p[0] <= 0.8]
    if lead <= 0.0 or len(pts) < 3 or pts[-1][0] - pts[0][0] < 0.25:
        return 0.0
    v = (pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0])
    v = max(-120.0, min(120.0, v))
    return max(-0.35 * pw, min(0.35 * pw, v * lead / max(10.0, hf) * pw))


_track_410 = MotionWatch.track


def _track_lead(self, target_box, pw, ph, gain=1.0):
    lead = float(CFG.get("track_lead") or 0.0)
    if lead <= 0.0:
        return _track_410(self, target_box, pw, ph, gain)   # 0 = exactly as before
    try:
        x, y, w, h = [float(v) for v in target_box[:4]]
        hf, _vf = cam_fov()
        p0, _t0 = servo_pos()
        bear = (p0 - 50.0) / 50.0 * servo_half("pan") + ((x + w / 2.0) / pw - 0.5) * hf
        sh = parc_lead_shift(time.time(), bear, hf, pw, lead)
        if sh:
            target_box = (int(x + sh), int(y), int(w), int(h)) + tuple(target_box[4:])
    except Exception:
        pass
    return _track_410(self, target_box, pw, ph, gain)


# wraps: MotionWatch.track
MotionWatch.track = _track_lead


# ---- runs -----------------------------------------------------------------------------------------------------------
def _parc_path():
    return os.path.join(DATA_DIR, PARC_FILE)


def parc_runs():
    if PARC["runs"] is None:
        try:
            with open(_parc_path(), encoding="utf-8") as f:
                d = json.load(f)
            PARC["runs"] = d.get("runs") if isinstance(d.get("runs"), list) else []
            PARC["tune"] = d.get("tune") if isinstance(d.get("tune"), dict) else None
            PARC["ab"] = d.get("ab") if isinstance(d.get("ab"), dict) else None
            PARC["ww"] = d.get("ww") if isinstance(d.get("ww"), list) else None
        except (OSError, ValueError):
            PARC["runs"] = []
    return PARC["runs"]


def _parc_save():
    try:
        tmp = _parc_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"runs": parc_runs()[-24:], "tune": PARC["tune"], "ab": PARC["ab"], "ww": PARC["ww"]}, f, ensure_ascii=False)
        os.replace(tmp, _parc_path())
    except OSError:
        pass


def parc_run_by(rid):
    for r in parc_runs():
        if r.get("id") == rid:
            return r
    return None


def _parc_short(rep):
    """a run report of the simulator without the long error curves (only 2 per lesson are kept small)"""
    out = {k: rep.get(k) for k in ("id", "t", "seed", "night", "score", "note", "mount", "pics", "realism")}
    out["lessons"] = [{k: v for k, v in l.items() if k != "curve"} for l in rep.get("lessons") or []]
    out["curves"] = {str(l.get("id")): (l.get("curve") or [])[:120] for l in rep.get("lessons") or []}
    return out


def _parc_one(lessons, params=None, label="", night=False, seed=1, extra=None):
    """one run in the simulator with these values of the following (None = as they are). Returns the run or raises."""
    keep = {k: CFG.get(k) for k in PARC_KEYS + PARC_RUN_KEYS}
    keep.update({k: CFG.get(k) for k in (extra or {})})
    try:
        if params:
            for k, v in params.items():
                if k in PARC_KEYS:
                    CFG[k] = parc_clip(k, v)
        CFG.update(track_person=True, track_motion=True, kopf_round=False, manual_hold=1.0, kopf_return_s=5.0)
        CFG.update(extra or {})
        used = parc_params()
        old = (sim_control({"action": "parcours", "do": "result"}) or {}).get("report") or {}
        r = sim_control({"action": "parcours", "do": "start", "lessons": list(lessons), "night": bool(night), "seed": int(seed), "prep_s": 2.5})
        if not r.get("ok"):
            raise RuntimeError(str(r.get("error") or "the simulator did not start the parcours"))
        est = float((r.get("run") or {}).get("est") or 120.0)
        t_end = time.time() + est * 3.0 + 120.0
        rep = None
        while time.time() < t_end:
            if PARC["stop"]:
                sim_control({"action": "parcours", "do": "stop"})
                raise RuntimeError("stopped")
            time.sleep(2.0)
            try:
                st = sim_control({"action": "parcours", "do": "state"})
            except Exception:
                continue
            ru = st.get("run") or {}
            if st.get("running"):
                PARC["step"] = (label + " · " if label else "") + "%d/%d · %s %s" % (int(ru.get("done") or 0) + 1, len(ru.get("lessons") or [1]),
                                                                                tr("lesson"), ru.get("lesson", ""))
                continue
            rp = st.get("report") or {}
            if rp.get("id") and rp.get("id") != old.get("id"):
                rep = rp
            break
        if rep is None:
            raise RuntimeError("no result from the simulator")
        run = {"id": "%d" % int(time.time() * 1000), "t": time.strftime("%Y-%m-%d %H:%M"), "label": label or "", "params": used,
               "lessons": list(lessons), "night": bool(night), "seed": int(seed), "ov": bool(CFG.get("kopf_ov_on")) and bool(CFG.get("kopf_ov")),
               "report": _parc_short(rep)}
        parc_runs().append(run)
        del parc_runs()[:-24]
        _parc_save()
        return run
    finally:
        for k, v in keep.items():
            CFG[k] = v


def _parc_thread(kind, fn):
    if PARC["busy"]:
        return False, "the tracking parcours is running"
    if not sim_ready():
        return False, "only with the simulator"
    if simtask_busy():
        return False, simtask_refuse("tracking parcours") or "already running"
    PARC.update(busy=True, kind=kind, step="…", stop=False, err="")
    _SIMHUB["t"] = 0.0

    def run():
        try:
            fn()
        except Exception as e:
            PARC["err"] = str(e)[:160]
            log_event("servo", "Tracking parcours: " + str(e)[:120])
        finally:
            PARC.update(busy=False, step="", kind="")
            _SIMHUB["t"] = 0.0
    threading.Thread(target=run, daemon=True, name="parcours").start()
    return True, ""


def parc_start(lessons, night=False):
    L = [int(x) for x in lessons or [] if str(x).isdigit() and 1 <= int(x) <= 8] or [1, 5, 6]
    return _parc_thread("run", lambda: _parc_one(L, None, tr("now"), night=night or 8 in L))


def _ab_params(preset):
    base = parc_params()
    p = dict(base)
    for k, v in PARC_AB.get(preset, PARC_AB["lead"])[1].items():
        p[k] = parc_clip(k, base[k] * float(v[1:]) if isinstance(v, str) and v.startswith("*") else v)
    return p


def parc_ab(lessons, preset):
    """A = the values now, B = A with one change - one run each, shown side by side (nothing is kept by itself)"""
    L = [int(x) for x in lessons or [] if str(x).isdigit() and 1 <= int(x) <= 7] or [1, 4]
    bp = _ab_params(preset)

    def go():
        a = _parc_one(L, None, "A")
        b = _parc_one(L, bp, "B " + tr(PARC_AB.get(preset, PARC_AB["lead"])[0]))
        PARC["ab"] = {"a": a["id"], "b": b["id"], "t": time.strftime("%Y-%m-%d %H:%M")}
        _parc_save()
        log_event("servo", "Tracking parcours A/B: A %.1f · B %.1f" % (float(a["report"].get("note") or 0), float(b["report"].get("note") or 0)))
    return _parc_thread("ab", go)


def parc_tune_cands(base, n=5):
    """the sets the auto-tuning tries: the values now and one change at a time around them"""
    c = [dict(base)]
    for k, f in (("track_gain", 1.4), ("track_lead", None), ("track_deadzone", None), ("track_gain", 0.7), ("servo_vmax_pan", 1.5)):
        p = dict(base)
        if k == "track_lead":
            p[k] = 0.3 if base[k] < 0.15 else 0.0
        elif k == "track_deadzone":
            p[k] = 0.05 if base[k] > 0.065 else 0.1
        else:
            p[k] = parc_clip(k, base[k] * f)
        if p not in c:
            c.append(p)
    return c[:max(2, min(6, int(n)))]


def parc_tune(lessons, n=4):
    """tries some sets on short lessons and PROPOSES the best - it never applies one (button «übernehmen»)"""
    L = [int(x) for x in lessons or [] if str(x).isdigit() and 1 <= int(x) <= 7] or [4]
    cands = parc_tune_cands(parc_params(), n)

    def go():
        res = []
        for i, p in enumerate(cands):
            r = _parc_one(L, p, "%s %d/%d" % (tr("Auto-tuning"), i + 1, len(cands)))
            res.append({"params": p, "score": float(r["report"].get("score") or 0), "note": float(r["report"].get("note") or 0), "run": r["id"]})
        best = max(range(len(res)), key=lambda i: res[i]["score"]) if res else 0
        PARC["tune"] = {"t": time.strftime("%Y-%m-%d %H:%M"), "lessons": L, "cands": res, "best": best, "base": 0, "applied": False}
        _parc_save()
        log_event("servo", "Tracking parcours auto-tuning: best set %d of %d (score %.0f, now %.0f) - only proposed"
                  % (best + 1, len(res), res[best]["score"] if res else 0, res[0]["score"] if res else 0))
    return _parc_thread("tune", go)


def parc_apply():
    """«übernehmen»: the proposed set of the auto-tuning becomes the setting"""
    tu = PARC.get("tune") or {}
    try:
        p = tu["cands"][int(tu["best"])]["params"]
    except (KeyError, IndexError, TypeError, ValueError):
        return False, "no proposal"
    for k in PARC_KEYS:
        if k in p:
            CFG[k] = parc_clip(k, p[k])
    save_settings()
    tu["applied"] = True
    _parc_save()
    log_event("servo", "Tracking: proposal of the auto-tuning taken over (" + ", ".join("%s %s" % (k, p.get(k)) for k in PARC_KEYS) + ")")
    return True, ""


def parc_ww(lessons, mounts):
    """with / without the hand-over of the wide camera (163: «The overview camera steers the head»), per mount"""
    L = [int(x) for x in lessons or [] if str(x).isdigit() and 1 <= int(x) <= 7] or [1]
    M = [m for m in mounts or [] if m in WEIT_DEVICE_MOUNTS] or ["base"]
    if not (CFG.get("armed") and STATE.get("arm_state") == "armed"):
        return False, "the overview steers the head only when the protection is on (Wachsam / Voll)"
    if "sim:1" not in (CFG.get("extra_cams") or []):
        return False, "the wide camera is not an extra camera of MoveEye"

    def go():
        out = []
        try:
            for m in M:
                sim_control({"action": "weit", "mount": m})
                time.sleep(3.0)
                on = _parc_one(L, None, "🔭 " + m + " · " + tr("with hand-over"), extra={"kopf_ov": "sim:1", "kopf_ov_on": True})
                off = _parc_one(L, None, "🔭 " + m + " · " + tr("without hand-over"), extra={"kopf_ov": "", "kopf_ov_on": False})
                out.append({"mount": m, "on": on["id"], "off": off["id"]})
        finally:
            PARC["ww"] = out
            _parc_save()
    return _parc_thread("ww", go)


def parc_game(name, bot=False):
    try:
        r = sim_control({"action": "parcours", "do": "game", "name": str(name or "")[:20] or "Spieler", "bot": bool(bot), "secs": 60})
    except Exception:
        return False, "simulator not reachable"
    if not CFG.get("track_person") or not CFG.get("track_motion"):
        CFG.update(track_person=True, track_motion=True)     # «Folgen» on for the game (like the button in the simulator)
    return bool(r.get("ok")), str(r.get("error") or "")


def parc_compare(a, b):
    """side by side: per lesson [id, name, A, B] with the main numbers (the page draws it)"""
    ra, rb = parc_run_by(a), parc_run_by(b)
    if not ra or not rb:
        return None
    la = {int(x["id"]): x for x in ra["report"].get("lessons") or []}
    lb = {int(x["id"]): x for x in rb["report"].get("lessons") or []}
    rows = []
    for i in sorted(set(la) | set(lb)):
        x, y = la.get(i), lb.get(i)
        pick = lambda l: None if l is None else {k: l.get(k) for k in ("note", "score", "err_mean", "in_pic_pct", "losses", "reacq_s", "osc", "overshoot_deg", "servo_deg", "switches")}
        rows.append({"id": i, "name": (x or y or {}).get("name", ""), "a": pick(x), "b": pick(y)})
    win = "A" if float(ra["report"].get("score") or 0) > float(rb["report"].get("score") or 0) + 1.0 else (
        "B" if float(rb["report"].get("score") or 0) > float(ra["report"].get("score") or 0) + 1.0 else "=")
    side = lambda r: dict({k: r.get(k) for k in ("id", "t", "label", "params", "night", "ov")}, note=r["report"].get("note"), score=r["report"].get("score"))
    return {"a": side(ra), "b": side(rb),
            "rows": rows, "winner": win}


def parc_hub():
    """the tile 🎯: state, values, the last runs, A/B, auto-tuning, the simulator side (pictures, game)"""
    runs = parc_runs()
    sim = {}
    try:
        st = sim_control({"action": "parcours", "do": "state"})
        if st.get("ok"):
            sim = {"running": bool(st.get("running")), "run": st.get("run"), "pics_n": st.get("pics_n"), "pics": st.get("pics"),
                   "overlay": st.get("overlay"), "ring": st.get("ring"), "game": st.get("game"), "lessons": [[x.get("id"), x.get("name"), x.get("icon")] for x in st.get("lessons") or []]}
    except Exception:
        sim = {"old": True}
    ab = PARC.get("ab") or {}
    cmp_ = parc_compare(ab.get("a"), ab.get("b")) if ab.get("a") else None
    ww = []
    for w in PARC.get("ww") or []:
        c = parc_compare(w.get("on"), w.get("off"))
        if c:
            ww.append({"mount": w.get("mount"), "cmp": c})
    return {"busy": PARC["busy"], "kind": PARC["kind"], "step": PARC["step"], "err": PARC["err"], "params": parc_params(), "lim": PARC_LIM,
            "runs": [{"id": r["id"], "t": r["t"], "label": r.get("label"), "note": r["report"].get("note"), "score": r["report"].get("score"),
                      "lessons": r.get("lessons"), "night": r.get("night"), "params": r.get("params")} for r in runs[-10:]][::-1],
            "last": runs[-1]["report"] if runs else None, "ab": cmp_, "ab_presets": [[k, v[0]] for k, v in PARC_AB.items()],
            "tune": PARC.get("tune"), "ww": ww, "sim": sim, "armed": bool(CFG.get("armed") and STATE.get("arm_state") == "armed")}


# ---- tile and lock --------------------------------------------------------------------------------------------------
_simtask_busy_416 = simtask_busy


def simtask_busy(except_=""):                              # + 416: one lock
    if PARC["busy"] and except_ != "tracking parcours":
        return "tracking parcours"
    return _simtask_busy_416(except_)


_simtask_local_416 = simtask_local


def simtask_local():                                       # + 416: the simulator refuses its own starts meanwhile
    return "tracking parcours" if PARC["busy"] else _simtask_local_416()


SIM_BUSY_NAMES.setdefault("Verfolgungs-Parcours", "tracking parcours")
_sim_hub_416 = sim_hub


def sim_hub(force=False):                                  # + 416: the tile 🎯 (Simulator centre, group «Testen»)
    d = _sim_hub_416(force)
    if d.get("ok"):
        try:
            d = dict(d, parc=parc_hub())
        except Exception as e:
            d = dict(d, parc={"err": str(e)[:80]})
    return d


_sim_hub_do_416 = sim_hub_do


def sim_hub_do(a, v=None):                                 # + 416: «parc» = {do: start | stop | set | ab | pick | tune | apply | ww | game | sim}
    if a != "parc":
        return _sim_hub_do_416(a, v)
    v = v if isinstance(v, dict) else {}
    op = str(v.get("do") or "")
    _SIMHUB["t"] = 0.0
    if op == "start":
        return parc_start(v.get("lessons"), bool(v.get("night")))
    if op == "stop":
        PARC["stop"] = True
        try:
            sim_control({"action": "parcours", "do": "stop"})
            sim_control({"action": "parcours", "do": "game_stop"})
        except Exception:
            pass
        return True, ""
    if op == "set":                                        # the regulators live (the same settings as in «Einstellungen»)
        k = str(v.get("k") or "")
        if k not in PARC_KEYS:
            return False, "invalid value"
        try:
            CFG[k] = parc_clip(k, v.get("v"))
        except (TypeError, ValueError):
            return False, "invalid value"
        save_settings()
        return True, ""
    if op == "ab":
        return parc_ab(v.get("lessons"), str(v.get("preset") or "lead"))
    if op == "pick":                                       # compare two kept runs
        if not parc_run_by(v.get("a")) or not parc_run_by(v.get("b")):
            return False, "invalid value"
        PARC["ab"] = {"a": v.get("a"), "b": v.get("b"), "t": time.strftime("%Y-%m-%d %H:%M")}
        _parc_save()
        return True, ""
    if op == "tune":
        return parc_tune(v.get("lessons"), int(v.get("n") or 4))
    if op == "apply":
        return parc_apply()
    if op == "ww":
        return parc_ww(v.get("lessons"), v.get("mounts") or [str((weit_sim_cam() or {}).get("mount") or "base")])
    if op == "game":
        return parc_game(v.get("name"), bool(v.get("bot")))
    if op in ("overlay", "ring", "pics"):
        try:
            r = sim_control({"action": "parcours", "do": op, "on": bool(v.get("on"))})
        except Exception:
            return False, "simulator not reachable"
        return bool(r.get("ok", True)), ""
    return False, "unknown action"


PARC_JS = r"""
<style>
.mwpc{flex:1 1 100%;display:flex;flex-direction:column;gap:8px;min-width:0;max-width:100%;box-sizing:border-box}
.mwpc *{box-sizing:border-box;max-width:100%}
.mwpc .row>button{flex:1 1 auto;min-width:0}.mwpc .chip{flex:0 1 auto!important}
.mwpc select{min-width:0;flex:1 1 140px}.mwpc td{overflow-wrap:anywhere}
.mwpc .row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.mwpc .chip{padding:6px 10px;border-radius:99px;font-size:13px}
.mwpc .sl{display:grid;grid-template-columns:minmax(90px,30%) 1fr 54px;gap:6px;align-items:center;font-size:13px}
.mwpc .sl input{width:100%}
.mwpc table{width:100%;border-collapse:collapse;font-size:12px}
.mwpc td,.mwpc th{padding:3px 4px;border-bottom:1px solid #1f2b3a;text-align:left;vertical-align:top}
.mwpc th{color:#8a9bb0;font-weight:600}
.mwpc .g{color:#3fcf6b}.mwpc .o{color:#f59a4a}.mwpc .r{color:#ff4d4d}
.mwpc .box{border:1px solid #1f2b3a;border-radius:10px;padding:8px}
.mwpc h4{margin:0 0 4px;font-size:13px}
.mwpc svg{width:100%;height:42px;background:#0c121a;border-radius:6px}
</style>
<script>
(function () {
  const DE = /*PDE*/{};
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) { return "de"; } };
  let merged = false;                                  // (like 591: the page's own dictionary learns these words, for 139 too)
  const merge = () => { if (merged) return; try { if (typeof I18N !== "undefined" && I18N.de) { for (const k in DE) if (!(k in I18N.de)) I18N.de[k] = DE[k]; merged = true; } } catch (e) {} };
  const tt = k => { merge(); try { if (typeof t === "function" && t(k) !== k) return t(k); } catch (e) {} return L() === "en" ? k : (DE[k] || k); };
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const B = (txt, fn, cls) => { const b = E("button", cls == null ? "sec" : cls, txt); b.type = "button"; b.onclick = fn; return b; };
  const LN = {1: "Slowly across the picture", 2: "Towards the camera / away", 3: "Zigzag and changes of speed", 4: "Stop and go on", 5: "Hidden behind obstacles",
    6: "Two persons cross", 7: "Animal: fox / deer, fast and irregular", 8: "Night run with infrared"};
  const ln = id => tt(LN[id] || String(id));
  const SEL = new Set([1, 5, 6]); let AB = "lead", GNAME = "";
  const nc = n => n == null ? "" : (n >= 4.5 ? "g" : n >= 3.5 ? "o" : "r");
  const SL = [["servo_vmax_pan", "Speed (°/s)", 5], ["track_gain", "Gain", 0.05], ["track_deadzone", "Dead zone", 0.01], ["track_lead", "Look ahead (s)", 0.05]];
  function spark(curve) {                               // the error curve of one lesson (0 … 30°), red where it was not in the picture
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("viewBox", "0 0 100 30"); s.setAttribute("preserveAspectRatio", "none");
    if (!curve || curve.length < 2) return s; const t1 = curve[curve.length - 1][0] || 1;
    for (let i = 1; i < curve.length; i++) { const a = curve[i - 1], b = curve[i]; const l = document.createElementNS("http://www.w3.org/2000/svg", "line");
      l.setAttribute("x1", a[0] / t1 * 100); l.setAttribute("x2", b[0] / t1 * 100); l.setAttribute("y1", 30 - Math.min(30, a[1])); l.setAttribute("y2", 30 - Math.min(30, b[1]));
      l.setAttribute("stroke", b[2] ? "#3fcf6b" : "#ff4d4d"); l.setAttribute("stroke-width", "1.2"); l.setAttribute("vector-effect", "non-scaling-stroke"); s.appendChild(l); }
    return s;
  }
  function cell(x) { if (!x) return "–"; return x.note.toFixed(1) + " · " + x.err_mean.toFixed(1) + "° · " + Math.round(x.in_pic_pct) + " %" + (x.losses ? " · " + x.losses + "×" : ""); }
  function cmpTable(c, ha, hb) {
    const tb = E("table"), h = E("tr"); h.append(E("th", "", tt("Lesson")), E("th", "", ha || "A"), E("th", "", hb || "B")); tb.appendChild(h);
    c.rows.forEach(r => { const tr = E("tr"), a = E("td", nc(r.a && r.a.note), cell(r.a)), b = E("td", nc(r.b && r.b.note), cell(r.b));
      tr.append(E("td", "", r.id + " " + ln(r.id)), a, b); tb.appendChild(tr); });
    const f = E("tr"); f.append(E("td", "", "Ø " + tt("grade")), E("td", nc(c.a.note), (c.a.note || 0).toFixed(1)), E("td", nc(c.b.note), (c.b.note || 0).toFixed(1))); tb.appendChild(f);
    const p = E("tr"); const pv = x => x ? "v " + Math.round(x.servo_vmax_pan) + " · g " + x.track_gain + " · dz " + x.track_deadzone + " · la " + x.track_lead : "";
    p.append(E("td", "", tt("Values")), E("td", "", pv(c.a.params)), E("td", "", pv(c.b.params))); tb.appendChild(p);
    return tb;
  }
  merge();
  window.mwParc = {
    sub: H => { merge(); const P = H && H.parc; if (!P || P.err && !P.params) return ""; if (P.busy) return "⏳ " + (P.step || ""); const S = P.sim || {};
      if (S.running) return "⏳ " + tt("lesson") + " " + ((S.run || {}).lesson || ""); if (S.game && S.game.on) return "🏃 " + S.game.score;
      return P.last ? tt("grade") + " " + P.last.note.toFixed(1) : tt("Train the following"); },
    sheet: (s, H, act) => {
      const P = H && H.parc, w = E("div", "mwpc"); s.appendChild(w);
      if (!P || !P.params) { w.appendChild(E("div", "mut", tt("not supported - update the simulator"))); return; }
      const S = P.sim || {};
      if (S.old) w.appendChild(E("div", "mut", "⚠ " + tt("not supported - update the simulator")));
      const pa = (d) => act("parc", d);
      // lessons
      const lr = E("div", "row"); (S.lessons || [[1, "Langsam quer durchs Bild", "🚶"], [2, "", "↕"], [3, "", "〰"], [4, "", "⏸"], [5, "", "🌳"], [6, "", "👥"], [7, "", "🦊"]]).filter(x => x[0] < 8).forEach(([id, nm, ic]) => {
        const b = B(ic + " " + id, () => { SEL.has(id) ? SEL.delete(id) : SEL.add(id); b.className = "chip" + (SEL.has(id) ? "" : " sec"); }, "chip" + (SEL.has(id) ? "" : " sec")); b.title = ln(id); lr.appendChild(b); });
      w.appendChild(lr);
      const busy = P.busy || S.running || (S.game && S.game.on);
      const r1 = E("div", "row");
      // the same buttons in the same order as in the simulator window (card «Testlauf» → «Verfolgungs-Parcours»)
      r1.append(B("▶ " + tt("Start"), () => pa({do: "start", lessons: [...SEL]}), busy ? "sec" : ""), B("🌙 " + tt("Night (lesson 8)"), () => pa({do: "start", lessons: [...SEL], night: true})),
        B("⏹ " + tt("Stop"), () => pa({do: "stop"})));
      if (busy) r1.appendChild(E("span", "mut", "⏳ " + (P.step || (S.run ? tt("lesson") + " " + S.run.lesson + (S.run.t != null ? " · " + Math.round(S.run.t) + " s" : "") : ""))));
      if (P.err) r1.appendChild(E("span", "r", "⚠ " + tt(P.err)));
      w.appendChild(r1);
      const sw = E("div", "row"); [["overlay", "Overlay in the simulator"], ["ring", "Ring round the device"], ["pics", "Collect learning pictures"]].forEach(([k, n]) => {
        sw.appendChild(B((S[k] ? "✓ " : "") + tt(n), () => pa({do: k, on: !S[k]}), S[k] ? "" : "sec")); });
      w.appendChild(sw);
      // the regulators (live: the same settings as in «Einstellungen»)
      const bx = E("div", "box"); bx.appendChild(E("h4", "", "🎚 " + tt("Regulators of the following (live)")));
      SL.forEach(([k, n, st]) => { const lim = (P.lim || {})[k] || [0, 1]; const r = E("div", "sl"), i = E("input"), o = E("b", "", String(P.params[k]));
        i.type = "range"; i.min = lim[0]; i.max = lim[1]; i.step = st; i.value = P.params[k]; i.oninput = () => o.textContent = i.value; i.onchange = () => pa({do: "set", k: k, v: +i.value});
        r.append(E("span", "", tt(n)), i, o); bx.appendChild(r); });
      bx.appendChild(E("div", "mut", tt("parc-reg-note"))); w.appendChild(bx);
      // last run
      if (P.last) { const lb = E("div", "box"); lb.appendChild(E("h4", "", "🎯 " + tt("Last run") + " · " + tt("grade") + " " + P.last.note.toFixed(1) + (P.last.night ? " · 🌙" : "")));
        (P.last.lessons || []).forEach(l => { const d = E("div"); d.appendChild(E("div", nc(l.note), l.id + " " + ln(l.id) + ": " + l.note.toFixed(1) + " · " + tt("aim error") + " " + l.err_mean.toFixed(1) + "° · "
          + tt("in the picture") + " " + Math.round(l.in_pic_pct) + " % · " + tt("losses") + " " + l.losses + (l.losses ? " (" + l.reacq_s + " s)" : "") + " · " + tt("swinging") + " " + l.osc + " · " + tt("servo travel") + " " + l.servo_deg + "°"
          + (l.id === 6 ? " · " + tt("switches") + " " + l.switches : "")));
          d.appendChild(spark(((P.last.curves || {})[String(l.id)]) || [])); lb.appendChild(d); });
        if (P.last.pics) lb.appendChild(E("div", "mut", "📷 " + P.last.pics + " " + tt("learning pictures (picture data only)")));
        w.appendChild(lb); }
      // A/B
      const ab = E("div", "box"); ab.appendChild(E("h4", "", "⚖ " + tt("A/B comparison")));
      const ar = E("div", "row"), sel = E("select"); (P.ab_presets || []).forEach(([k, n]) => { const o = E("option", "", "B = " + tt(n)); o.value = k; if (k === AB) o.selected = true; sel.appendChild(o); });
      sel.onchange = () => AB = sel.value; ar.append(sel, B("▶ " + tt("A/B run"), () => pa({do: "ab", preset: AB, lessons: [...SEL].filter(x => x < 8)}))); ab.appendChild(ar);
      if ((P.runs || []).length >= 2) { const pr = E("div", "row"), sa = E("select"), sb = E("select");
        P.runs.forEach((r, i) => { [sa, sb].forEach((x, j) => { const o = E("option", "", r.t.slice(5) + " · " + (r.label || "") + " · " + (r.note != null ? r.note.toFixed(1) : "–")); o.value = r.id;
          if ((P.ab && ((j === 0 && P.ab.a.id === r.id) || (j === 1 && P.ab.b.id === r.id))) || (!P.ab && i === j)) o.selected = true; x.appendChild(o); }); });
        pr.append(E("span", "", "A"), sa, E("span", "", "B"), sb, B(tt("Compare"), () => pa({do: "pick", a: sa.value, b: sb.value}))); ab.appendChild(pr); }
      if (P.ab) { ab.appendChild(cmpTable(P.ab, "A · " + (P.ab.a.label || ""), "B · " + (P.ab.b.label || "")));
        ab.appendChild(E("div", "mut", P.ab.winner === "=" ? tt("No clear difference.") : (P.ab.winner === "B" ? tt("B is better.") : tt("A is better.")) + " " + tt("Nothing is changed by itself."))); }
      w.appendChild(ab);
      // auto-tuning
      const tu = E("div", "box"); tu.appendChild(E("h4", "", "🤖 " + tt("Auto-tuning")));
      tu.appendChild(B("▶ " + tt("Try values (short, lessons as chosen)"), () => pa({do: "tune", lessons: [...SEL].filter(x => x < 8).slice(0, 2), n: 4})));
      const T = P.tune; if (T && T.cands) { const tb = E("table"), h = E("tr"); h.append(E("th", "", "#"), E("th", "", tt("Values")), E("th", "", tt("grade"))); tb.appendChild(h);
        T.cands.forEach((c, i) => { const tr = E("tr"), p = c.params; tr.append(E("td", "", (i === T.best ? "★ " : "") + (i === 0 ? tt("now") : String(i))),
          E("td", "", "v " + Math.round(p.servo_vmax_pan) + " · g " + p.track_gain + " · dz " + p.track_deadzone + " · la " + p.track_lead), E("td", nc(c.note), c.note.toFixed(1) + " (" + Math.round(c.score) + ")")); tb.appendChild(tr); });
        tu.appendChild(tb);
        if (T.best > 0 && !T.applied) tu.appendChild(B("✓ " + tt("take over proposal ★"), () => pa({do: "apply"}), ""));
        tu.appendChild(E("div", "mut", T.applied ? "✓ " + tt("taken over") : T.best === 0 ? tt("The values now are the best - nothing to change.") : tt("Only a proposal - nothing was changed."))); }
      w.appendChild(tu);
      // wide camera hand-over
      const ww = E("div", "box"); ww.appendChild(E("h4", "", "🔭 " + tt("With / without wide-angle hand-over")));
      ww.appendChild(B("▶ " + tt("Compare (mount now)"), () => pa({do: "ww", lessons: [...SEL].filter(x => x < 8).slice(0, 2)})));
      if (!P.armed) ww.appendChild(E("div", "mut", tt("the overview steers the head only when the protection is on (Wachsam / Voll)")));
      (P.ww || []).forEach(x => { ww.appendChild(E("div", "", "🔭 " + x.mount)); ww.appendChild(cmpTable(x.cmp, tt("with hand-over"), tt("without hand-over"))); });
      w.appendChild(ww);
      // the game and the switches of the simulator
      const g = E("div", "box"); g.appendChild(E("h4", "", "🏃 " + tt("Game «Escape the camera»")));
      const gi = E("input"); gi.placeholder = tt("Name"); gi.value = GNAME; gi.maxLength = 20; gi.oninput = () => GNAME = gi.value; gi.style.cssText = "flex:1;min-width:100px";
      const gr = E("div", "row"); gr.append(gi, B("▶ " + tt("Play (60 s)"), () => pa({do: "game", name: GNAME}), ""), B("🤖 " + tt("Bot"), () => pa({do: "game", name: "Bot", bot: true})));
      g.appendChild(gr); g.appendChild(E("div", "mut", tt("parc-game-note")));
      const GS = S.game || {}; if (GS.on) g.appendChild(E("div", "", "⏳ " + GS.name + " · " + GS.score + " " + tt("points") + " · " + Math.round(GS.left || 0) + " s"));
      else if (GS.result) g.appendChild(E("div", "", "🏁 " + GS.result.name + ": " + GS.result.score + " " + tt("points") + " · " + GS.result.out_s + " s " + tt("out of the picture") + " · " + GS.result.losses + "× " + tt("lost")));
      w.appendChild(g);
      w.appendChild(E("div", "mut", tt("parc-note")));
    }
  };
})();
</script>
"""
PARC_KEYS_TXT = ("not supported - update the simulator", "Night (lesson 8)", "Start", "Stop", "lesson", "Regulators of the following (live)", "Speed (°/s)",
                 "Gain", "Dead zone", "Look ahead (s)", "parc-reg-note", "Last run", "grade", "aim error", "in the picture", "losses", "swinging",
                 "servo travel", "switches", "learning pictures (picture data only)", "A/B comparison", "A/B run", "Compare", "No clear difference.",
                 "B is better.", "A is better.", "Nothing is changed by itself.", "Auto-tuning", "Try values (short, lessons as chosen)", "Values", "now",
                 "take over proposal ★", "taken over", "The values now are the best - nothing to change.", "Only a proposal - nothing was changed.",
                 "With / without wide-angle hand-over", "Compare (mount now)", "the overview steers the head only when the protection is on (Wachsam / Voll)",
                 "with hand-over", "without hand-over", "Game «Escape the camera»", "Name", "Play (60 s)", "Bot", "parc-game-note", "points",
                 "out of the picture", "lost", "Overlay in the simulator", "Ring round the device", "Collect learning pictures", "parc-note",
                 "Train the following", "Lesson", "Tracking parcours", "Look ahead 0.3 s", "Gain +40 %", "Dead zone 0.05", "Speed 200 °/s",
                 "Slowly across the picture", "Towards the camera / away", "Zigzag and changes of speed", "Stop and go on", "Hidden behind obstacles",
                 "Two persons cross", "Animal: fox / deer, fast and irregular", "Night run with infrared", "stopped",
                 "the tracking parcours is running", "no result from the simulator", "no proposal", "the simulator did not start the parcours")
_simhub_head_416 = simhub_head


def simhub_head():                                        # + 416: the tile 🎯 «Verfolgungs-Parcours»
    return _simhub_head_416() + PARC_JS.replace("/*PDE*/{}", json.dumps({k: DE[k] for k in PARC_KEYS_TXT if k in DE}, ensure_ascii=False), 1)


def parc_selftest():
    H = deque(maxlen=16)
    assert parc_lead_shift(0.0, 10.0, 66.0, 640, 0.3, H) == 0.0                 # no history yet
    for i in range(1, 6):
        sh = parc_lead_shift(0.1 * i, 10.0 + 2.0 * i, 66.0, 640, 0.3, H)         # 20 °/s to the right
    assert abs(sh - 20.0 * 0.3 / 66.0 * 640) < 0.5, sh
    assert parc_lead_shift(0.6, 12.0, 66.0, 640, 0.0, H) == 0.0                 # 0 = off
    assert parc_lead_shift(5.0, 50.0, 66.0, 640, 0.3, H) == 0.0                 # a pause: new start
    base = {"servo_vmax_pan": 120.0, "track_gain": 0.6, "track_deadzone": 0.08, "track_lead": 0.0}
    c = parc_tune_cands(base, 5)
    assert c[0] == base and len(c) == 5 and any(x["track_lead"] == 0.3 for x in c) and all(PARC_LIM[k][0] <= x[k] <= PARC_LIM[k][1] for x in c for k in PARC_KEYS)
    keep = {k: CFG.get(k) for k in PARC_KEYS}
    try:
        CFG.update(base)
        assert _ab_params("gain")["track_gain"] == 0.84 and _ab_params("dead")["track_deadzone"] == 0.05
        assert parc_clip("track_lead", 5) == 1.0 and parc_clip("servo_vmax_pan", 1) == 10.0
    finally:
        CFG.update(keep)
    keep_runs = PARC["runs"]
    try:
        PARC["runs"] = [{"id": "1", "t": "x", "label": "A", "params": base, "report": {"score": 80, "note": 5.0, "lessons": [{"id": 1, "name": "n", "note": 5.0, "score": 80, "err_mean": 2.0, "in_pic_pct": 95, "losses": 0}]}},
                        {"id": "2", "t": "y", "label": "B", "params": base, "report": {"score": 60, "note": 4.0, "lessons": [{"id": 1, "name": "n", "note": 4.0, "score": 60, "err_mean": 5.0, "in_pic_pct": 80, "losses": 1}]}}]
        cm = parc_compare("1", "2")
        assert cm["winner"] == "A" and cm["rows"][0]["a"]["note"] == 5.0 and cm["rows"][0]["b"]["losses"] == 1
    finally:
        PARC["runs"] = keep_runs
    assert "mwParc" in simhub_head()


SELFTEST_EXTRA.append(("Tracking parcours: look ahead, auto-tuning sets, A/B (416)", parc_selftest))
