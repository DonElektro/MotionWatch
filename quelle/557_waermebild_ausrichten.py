#@ MoveEye – Teil 557: Assistent «Wärmebild ausrichten (warme Hand)» (Web /thermal_align und Fenster), Wärmebild-Modell des Simulators (Thermal-90 oder 45°), Texte und Anleitung der Teile 554 / 555 / 557. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026, «Wärmebild wie Thermal-90»): the simulator offers the thermal camera «Thermal-90 (Waveshare)»
#   (80 × 62 pixels, 90° × 67°, 15 pictures/s like the driver in 080, NETD 125 mK - Waveshare / Core Electronics data sheet)
#   or the old 45° model; /info and every answer («thermal_model») say which -> SIM["info"]["thermal"] (230 sim_geom fits the
#   picture with fov_h / fov_v, 290 fetches at the fps of the model).
# The assistant: somebody holds a warm hand in front of MoveEye (2-3 m, moves it slowly). MoveEye takes pairs: the top of
#   the moving thing in the main camera (difference of two pictures) and the top of the warm spot in the RAW thermal picture.
#   A straight line through the pairs gives the zoom (thermal_zoom: which part of the thermal width the camera sees) and the
#   shift (thermal_dx / thermal_dy) - the same three settings as by hand (230 ThermalCam.crop). The head stands still while
#   it measures (MANUAL pause). «Rückgängig» brings the old values back.
#   Simulator: «🖐 Warme Hand» of the simulator (simint.gd) is switched on by itself; the result is used instead of the
#   automatic fit by the field of view (CFG thermal_align_own, 230) - «Rückgängig» = automatic again. The page shows the
#   values the simulator would expect (from its field of view) for comparison.
# Pages: Settings → Thermal camera → «Camera and alignment» (button, 530) and Mehr → Werkzeuge → Geräte-Tests (link);
#   the window: Settings → Thermal camera (button) opens a window with the same steps.
# Translations (all new texts of 554 / 555 / 557) at the end: fr / it / rm at once, German after part 560 has made DE
#   (_simint_late, through load_settings / self_test - this part comes before 560 and 570).
# ----------------------------------------------------------------------------
for _k, _v in {"thermal_align_own": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TALIGN = {"busy": False, "phase": "idle", "t0": 0.0, "dur": 25.0, "n": 0, "msg": "", "res": None, "old": None, "hand_by_us": False,
          "pairs": [], "lock": threading.Lock(), "stop": False, "who": ""}
TALIGN_MIN = 8


# ---- the thermal model of the simulator -------------------------------------------------------------------------------
def talign_take(rep):
    tm = rep.get("thermal_model") if isinstance(rep, dict) else None
    if isinstance(tm, dict) and tm.get("fov_h"):
        info = SIM.get("info")
        if isinstance(info, dict):
            old = info.get("thermal") or {}
            if old.get("model") != tm.get("model") or old.get("fov_h") != tm.get("fov_h"):
                info["thermal"] = tm
                log_event("sys", f"Simulator thermal camera: {tm.get('name', '?')} ({tm.get('fov_h')}° × {tm.get('fov_v')}°, {tm.get('fps')} fps)")
    SIM["warm_hand"] = bool(rep.get("warm_hand")) if isinstance(rep, dict) else False


_simvals_take_555 = simvals_take


def simvals_take(rep):                                    # + 557: thermal model and warm hand of the simulator
    _simvals_take_555(rep)
    try:
        talign_take(rep)
    except Exception:
        pass


_th_wanted_230 = ThermalCam.wanted


def _th_wanted_557(self):                                 # + 557: the assistant needs the thermal picture (also when it is off)
    s = _th_wanted_230(self)
    if not s and TALIGN["busy"] and CFG.get("thermal_source") and CFG["thermal_source"] != STATE.get("source_id"):
        return CFG["thermal_source"]
    return s


# wraps: ThermalCam.wanted
ThermalCam.wanted = _th_wanted_557


def talign_sim():
    return bool(CFG.get("sim_on")) and str(CFG.get("thermal_source")) == "sim:thermal" and str(CFG.get("source", "")).startswith("sim:")


def talign_expected():
    """the simulator knows both fields of view: the values the assistant should find there (None outside)"""
    if not talign_sim():
        return None
    try:
        info = SIM.get("info") or {}
        th = info.get("thermal") or {}
        cam = next((c for c in info.get("cameras") or [] if str(c.get("id")) == str(CFG["source"])[4:]), None)
        z = math.tan(math.radians(float(cam["fov_h"])) / 2) / math.tan(math.radians(float(th["fov_h"])) / 2)   # part of the thermal width
        return {"zoom": int(round(min(1.0, z) * 100)), "model": str(th.get("name") or ""), "fov": f"{th.get('fov_h')}° × {th.get('fov_v')}°"}
    except (KeyError, TypeError, ValueError, ZeroDivisionError, StopIteration):
        return None


# ---- measuring ---------------------------------------------------------------------------------------------------------
def talign_main_point(prev, cur):
    """the top of the moving thing between two small grey pictures: (x, y) 0..1, or None"""
    H, W = cur.shape[:2]
    d = cv2.absdiff(cur, prev)
    _, m = cv2.threshold(d, 16, 255, cv2.THRESH_BINARY)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    cnts = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    if not cnts:
        return None
    big = max(cnts, key=cv2.contourArea)
    a = cv2.contourArea(big)
    if a < 0.0006 * W * H or a > 0.3 * W * H:
        return None
    x, y, w, h = cv2.boundingRect(big)
    top = m[y:y + max(2, int(h * 0.35)), x:x + w]
    ys, xs = np.nonzero(top)
    if not xs.size:
        return None
    return (x + float(xs.mean()) + 0.5) / W, (y + float(ys.mean()) + 0.5) / H


def _talign_gray(fr):
    a = np.asarray(fr, dtype=np.float32)
    return a.mean(axis=2) if a.ndim == 3 else a


def talign_th_point(fr, prev=None):
    """the top of the warm spot in the raw thermal picture: (u, v) 0..1 and the warmth above the background, or None.
    With the picture before (prev): only what is warm AND moved (a grill, the sun on a wall, a lamp do not move)"""
    a = _talign_gray(fr)
    H, W = a.shape[:2]
    bg = float(np.median(a))
    moved = None
    if prev is not None:
        p = _talign_gray(prev)
        if p.shape == a.shape:
            moved = cv2.dilate((np.abs(a - p) > 1.2).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) > 0
            if not moved.any():
                return None
    hot = float(np.percentile(a[moved], 99.0)) if moved is not None else float(np.percentile(a, 99.7))
    if hot - bg < 3.0:
        return None
    m = a >= bg + (hot - bg) * 0.55
    if moved is not None:
        m &= moved
    m = m.astype(np.uint8)
    n, lab, stats, _c = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[i, cv2.CC_STAT_AREA] > 0.25 * W * H:
        return None                                       # half the picture is warm: no hand, the sun or a wall
    x, y, w, h = (int(stats[i, k]) for k in (cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT))
    top = (lab[y:y + max(1, int(round(h * 0.35))), x:x + w] == i)
    ys, xs = np.nonzero(top)
    if not xs.size:
        return None
    return (x + float(xs.mean()) + 0.5) / W, (y + float(ys.mean()) + 0.5) / H, hot - bg


def talign_fit(pairs, th_w, th_h, asp, zoom_now):
    """pairs [(x, y, u, v)]: main 0..1 -> thermal 0..1. The crop of 230: u = 0.5 + dx - z/2 + z·x, v = 0.5 - dy - zv/2 + zv·y
    with zv = z · th_w · asp / th_h (asp = height / width of the main picture). -> dict or None"""
    P = np.asarray(pairs, dtype=np.float64)
    if P.shape[0] < TALIGN_MIN:
        return None
    keep = np.ones(P.shape[0], bool)
    note = []
    for _round in range(2):
        X, Y, U, V = (P[keep, i] for i in range(4))
        z, src = None, ""
        if X.std() >= 0.05:
            z, src = float(np.polyfit(X, U, 1)[0]), "x"
        elif Y.std() >= 0.05:
            z, src = float(np.polyfit(Y, V, 1)[0]) * th_h / (th_w * asp), "y"
        if z is None or not (0.15 < z < 3.0):
            z, src = zoom_now, "keep"
        zc = max(0.3, min(1.0, z))
        zv = zc * th_w * asp / th_h
        b = float(np.mean(U - zc * X)); e = float(np.mean(V - zv * Y))
        ru = (zc * P[:, 0] + b - P[:, 2]) * th_w; rv = (zv * P[:, 1] + e - P[:, 3]) * th_h
        r = np.sqrt(ru * ru + rv * rv)
        med = float(np.median(r[keep])) if keep.any() else 0.0
        new = r <= max(1.5, 2.5 * med)
        if new.sum() < TALIGN_MIN or (new == keep).all():
            break
        keep = new
    dx = b + zc / 2 - 0.5
    dy = 0.5 - (e + zv / 2)
    if z > 1.02:
        note.append("narrow")
    if src == "keep":
        note.append("still")
    vs = None
    if Y.std() >= 0.05 and src == "x":
        vs = float(np.polyfit(Y, V, 1)[0]) / zv            # 1.0 = the height fits too (Thermal-90: about 1.2, the lens is not square)
    rms = float(np.sqrt(np.mean(r[keep] ** 2))) if keep.any() else 0.0
    return {"zoom": int(round(zc * 100)), "dx": int(round(max(-30.0, min(30.0, dx * 100)))), "dy": int(round(max(-30.0, min(30.0, dy * 100)))),
            "dx_raw": round(dx * 100, 1), "dy_raw": round(dy * 100, 1), "zoom_raw": round(z * 100, 1), "rms_px": round(rms, 2), "n": int(keep.sum()),
            "spread": round(float(max(X.std(), Y.std())), 3), "v_scale": round(vs, 2) if vs is not None else None, "note": note,
            "clipped": abs(dx * 100) > 30.0 or abs(dy * 100) > 30.0}


def talign_pairs(mtrack, ttrack, lag):
    """pairs: every thermal point with the main point of the same moment (the thermal picture is late by «lag» s)"""
    if len(mtrack) < 2:
        return []
    mt = np.asarray([m[0] for m in mtrack]); mx = np.asarray([m[1] for m in mtrack]); my = np.asarray([m[2] for m in mtrack])
    out = []
    for t, u, v in ttrack:
        tm = t - lag
        i = int(np.searchsorted(mt, tm))
        if i <= 0 or i >= mt.size or mt[i] - mt[i - 1] > 2.2:
            continue
        k = (tm - mt[i - 1]) / max(1e-6, mt[i] - mt[i - 1])
        out.append((mx[i - 1] + k * (mx[i] - mx[i - 1]), my[i - 1] + k * (my[i] - my[i - 1]), u, v))
    return out


def talign_best_lag(mtrack, ttrack):
    """the delay of the thermal picture behind the main picture (0 … 1.5 s) where both tracks fit best together"""
    best = (-9.0, 0.0, [])
    for lag in np.arange(0.0, 1.55, 0.1):
        P = talign_pairs(mtrack, ttrack, float(lag))
        if len(P) < TALIGN_MIN:
            continue
        A = np.asarray(P)
        sc = 0.0
        for i, j_ in ((0, 2), (1, 3)):
            if A[:, i].std() > 0.02 and A[:, j_].std() > 0.005:
                sc += float(np.corrcoef(A[:, i], A[:, j_])[0, 1])
        if sc > best[0] + 1e-3:
            best = (sc, round(float(lag), 2), P)
    return best[1], best[2]


def _talign_run():
    w = WATCH_REF.get("w")
    prev, prev_t = None, 0.0
    T = TALIGN
    T["lag"] = 0.0
    sim = talign_sim()
    try:
        if sim and not SIM.get("warm_hand"):
            try:
                sim_control({"action": "set", "id": "warm_hand", "value": True})
                T["hand_by_us"] = True
            except Exception:
                pass
        t_end = time.time() + T["dur"]
        wait_th = time.time() + 8.0
        prev_th, prev_th_t = None, 0.0
        mtrack, ttrack = [], []                           # (time, x, y) of the main camera / (time, u, v) of the thermal camera
        last_f = [None]
        while not T["stop"] and time.time() < t_end:
            time.sleep(0.2)
            MANUAL["until"] = max(MANUAL.get("until", 0.0), time.time() + 2.0)     # the head stands still while measuring
            w = WATCH_REF.get("w")
            if w is None:
                continue
            w.raw_until = max(w.raw_until, time.time() + 2.0)
            f = w.frame_raw
            th = THERMAL
            if th is None or th.frame is None or time.time() - th.t > 1.0:
                if time.time() > wait_th:
                    raise RuntimeError("no thermal picture - choose the thermal camera (Settings → Thermal camera)")
                continue
            if f is None:
                continue
            now = time.time()
            if f is not last_f[0]:                        # a new picture of the main camera (a slow PC: maybe 1 per second)
                last_f[0] = f
                g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if f.ndim == 3 else f
                H, W = g.shape[:2]
                T["asp"] = H / float(W)
                small = cv2.GaussianBlur(cv2.resize(g, (320, max(2, int(320 * H / W)))), (5, 5), 0)
                if prev is not None and now - prev_t < 2.0:    # its own track with times (the middle of the two pictures)
                    p = talign_main_point(prev, small)
                    if p is not None:
                        mtrack.append((now - (now - prev_t) / 2.0, p[0], p[1]))
                prev, prev_t = small, now
            thf = np.asarray(th.frame, dtype=np.float32)
            if prev_th is not None and thf.shape == prev_th.shape and np.array_equal(thf, prev_th):
                continue                                  # the same thermal picture again: wait for a new one
            if prev_th is not None and now - prev_th_t < 2.0:
                q = talign_th_point(thf, prev_th)
                if q is not None:
                    ttrack.append((float(th.t), q[0], q[1]))
                    T["th_size"] = (int(thf.shape[1]), int(thf.shape[0]))
                    T["n"] = len(talign_pairs(mtrack, ttrack, T.get("lag", 0.0)))
                    if len(ttrack) >= 60:
                        break
            prev_th, prev_th_t = thf.copy(), now
        lag, T["pairs"] = talign_best_lag(mtrack, ttrack)
        T["lag"] = lag; T["n"] = len(T["pairs"])
        if T["stop"]:
            T.update(phase="idle", msg="stopped"); return
        if T["n"] < TALIGN_MIN:
            T.update(phase="error", msg="too few points - hold the warm hand 2-3 m in front of MoveEye and move it slowly (nobody else in the picture)")
            return
        tw, thh = T.get("th_size") or (80, 62)
        r = talign_fit(T["pairs"], tw, thh, T.get("asp", 9 / 16.0), max(0.3, min(1.0, float(CFG["thermal_zoom"]) / 100.0)))
        if r is None:
            T.update(phase="error", msg="too few points"); return
        r["lag_s"] = T.get("lag", 0.0)
        talign_apply(r, sim)
    except Exception as e:
        T.update(phase="error", msg=str(e)[:160])
    finally:
        if T["hand_by_us"]:
            try:
                sim_control({"action": "set", "id": "warm_hand", "value": False})
            except Exception:
                pass
            T["hand_by_us"] = False
        T["busy"] = False


def talign_apply(r, sim):
    T = TALIGN
    T["old"] = {k: CFG.get(k) for k in ("thermal_zoom", "thermal_dx", "thermal_dy", "thermal_align_own")}
    CFG.update(thermal_zoom=r["zoom"], thermal_dx=r["dx"], thermal_dy=r["dy"])
    if sim:
        CFG["thermal_align_own"] = True
    save_settings()
    T.update(phase="done", res=r, msg="")
    log_event("sys", f"Thermal alignment (warm hand): zoom {r['zoom']} %, shift {r['dx']} / {r['dy']} % ({r['n']} points, ±{r['rms_px']} px)")


def talign_start(who="web", dur=None):
    T = TALIGN
    with T["lock"]:
        if T["busy"]:
            return False, "the assistant is already measuring"
        if not CFG.get("thermal_source"):
            return False, "no thermal camera selected"
        T.update(busy=True, phase="collect", t0=time.time(), dur=float(dur or 25.0), n=0, msg="", res=None, pairs=[], stop=False, who=str(who)[:40])
    threading.Thread(target=_talign_run, daemon=True, name="thermal-align").start()
    log_event("sys", f"Thermal alignment started ({who})")
    return True, ""


def talign_undo():
    T = TALIGN
    if T["busy"]:
        return False, "the assistant is measuring"
    if T["old"]:
        CFG.update(T["old"]); T["old"] = None
    elif CFG.get("thermal_align_own"):
        CFG["thermal_align_own"] = False                   # the simulator: automatic again
    else:
        return False, "nothing to undo"
    save_settings()
    T.update(phase="idle", res=None, msg="")
    log_event("sys", "Thermal alignment: old values back")
    return True, ""


def talign_state(lang=None):
    T = TALIGN
    el_ = time.time() - T["t0"] if T["busy"] else 0.0
    return {"ok": True, "busy": T["busy"], "phase": T["phase"], "n": T["n"], "need": TALIGN_MIN, "progress": round(min(1.0, el_ / max(1.0, T["dur"])), 3),
            "msg": tr_err(T["msg"], lang) if T["msg"] else "", "res": T["res"], "undo": bool(T["old"]) or bool(CFG.get("thermal_align_own")),
            "now": {"zoom": CFG.get("thermal_zoom"), "dx": CFG.get("thermal_dx"), "dy": CFG.get("thermal_dy"), "own": bool(CFG.get("thermal_align_own"))},
            "sim": talign_sim(), "hand": bool(SIM.get("warm_hand")), "expect": talign_expected(),
            "thermal": STATE.get("thermal") or "", "source": CFG.get("thermal_source") or "",
            "pairs": [[round(x, 3) for x in p] for p in T["pairs"][-60:]]}


def talign_api(d, lang=None):
    o = str(d.get("op") or "")
    if o == "start":
        ok, err = talign_start("web", d.get("dur"))
    elif o == "stop":
        TALIGN["stop"] = True; ok, err = True, ""
    elif o == "undo":
        ok, err = talign_undo()
    elif o == "hand":
        if not talign_sim():
            return {"ok": False, "error": tr("only in the simulation", lang)}, 400
        try:
            sim_control({"action": "set", "id": "warm_hand", "value": bool(d.get("on", True))}); SIM["warm_hand"] = bool(d.get("on", True))
            ok, err = True, ""
        except Exception:
            ok, err = False, "simulator not reachable"
    else:
        return {"ok": False, "error": "unknown"}, 400
    return dict(talign_state(lang), ok=ok, error=tr_err(err, lang) if err else None), 200 if ok else 409


# ---- the web page -------------------------------------------------------------------------------------------------------
TALIGN_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Thermal alignment</title>
<style>
/*BASECSS*/
main{padding:14px 16px 90px;max-width:760px;margin:0 auto}
.ta-steps{display:flex;gap:6px;margin:0 0 10px}.ta-steps>span{flex:1;text-align:center;padding:7px 4px;border-radius:10px;border:1px solid var(--line);color:var(--mut);font-size:13.5px}
.ta-steps>span.on{border-color:var(--acc);color:var(--txt);font-weight:700}
#ta-img{width:100%;aspect-ratio:16/9;object-fit:cover;background:#000;border-radius:12px;display:block;margin:8px 0}
.ta-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}.ta-row button{flex:1;min-width:140px}
.ta-bar{height:8px;border-radius:6px;background:var(--line);overflow:hidden;margin:6px 0}.ta-bar i{display:block;height:100%;width:0;background:var(--acc);transition:width .3s}
.ta-kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:14px;margin:6px 0}.ta-kv b{font-weight:600}
.ta-msg{padding:8px 10px;border-radius:10px;margin:6px 0;background:rgba(56,139,253,.10)}.ta-msg.warn{background:rgba(210,153,34,.14)}.ta-msg.ok{background:rgba(46,160,67,.14)}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <h2 style="margin:0 0 8px">🖐 <span data-i18n="Align the thermal picture (warm hand)">Align the thermal picture (warm hand)</span></h2>
  <div class="ta-steps"><span id="st1">1 · <span data-i18n="Hand in front">Hand in front</span></span><span id="st2">2 · <span data-i18n="Measure">Measure</span></span><span id="st3">3 · <span data-i18n="Result">Result</span></span></div>
  <section class="card">
    <div class="mut" data-i18n="talign-note">talign-note</div>
    <img id="ta-img" alt="">
    <div class="ta-row" id="ta-simrow" hidden><button type="button" class="sec" id="ta-hand">🖐 <span id="ta-hand-t"></span></button></div>
    <div class="ta-row"><button type="button" id="ta-start">▶ <span data-i18n="Start measuring">Start measuring</span></button>
      <button type="button" class="sec" id="ta-stop" hidden data-i18n="Stop">Stop</button>
      <button type="button" class="sec" id="ta-undo" hidden>↶ <span data-i18n="Undo">Undo</span></button></div>
    <div class="ta-bar" id="ta-bar" hidden><i></i></div>
    <div class="mut" id="ta-prog"></div>
    <div id="ta-msg"></div>
    <div id="ta-res"></div>
    <div class="mut" id="ta-now"></div>
    <div class="ta-row"><a class="btn sec" href="/settings?open=th:cam" data-i18n="Thermal camera settings">Thermal camera settings</a></div>
  </section>
</main>
<script>
/*COMMON*/
/*TALIGNDE*/
const TA = {s: null, timer: 0, img: 0};
const $$ = id => document.getElementById(id);
const tf = (s, o) => t(s).replace(/\{(\w+)\}/g, (m, k) => (o && o[k] != null) ? o[k] : m);
async function op(o) { const r = await post("/api/thermal_align", Object.assign({lang: LANG}, o)); if (!r.ok && r.error) toast("⚠ " + r.error); TA.s = r.phase ? r : TA.s; paint(); return r; }
function kv(rows) { const g = el("div", "ta-kv"); rows.forEach(([a, b]) => g.append(el("b", "", a), el("span", "", b))); return g; }
function paint() {
  const S = TA.s; if (!S) return;
  const step = S.busy ? 2 : (S.phase === "done" ? 3 : 1);
  [1, 2, 3].forEach(i => $$("st" + i).classList.toggle("on", i === step));
  $$("ta-start").hidden = S.busy; $$("ta-stop").hidden = !S.busy; $$("ta-undo").hidden = S.busy || !S.undo;
  $$("ta-simrow").hidden = !S.sim; $$("ta-hand-t").textContent = t(S.hand ? "Simulator: take the warm hand away" : "Simulator: warm hand in front of MoveEye");
  $$("ta-bar").hidden = !S.busy; $$("ta-bar").firstElementChild.style.width = Math.round((S.progress || 0) * 100) + "%";
  $$("ta-prog").textContent = S.busy ? tf("{n} points (at least {need})", {n: S.n, need: S.need}) : "";
  const M = $$("ta-msg"); M.textContent = "";
  if (!S.source) M.appendChild(el("div", "ta-msg warn", t("no thermal camera selected")));
  if (S.msg) M.appendChild(el("div", "ta-msg warn", S.msg));
  const R = $$("ta-res"); R.textContent = "";
  if (S.phase === "done" && S.res) {
    const r = S.res;
    R.appendChild(el("div", "ta-msg ok", "✅ " + t("Taken over - the thermal picture is laid over the camera picture with these values.")));
    const rows = [[t("Zoom"), r.zoom + " %"], [t("Left / right"), r.dx + " %"], [t("Up / down"), r.dy + " %"],
                  [t("Accuracy"), "± " + r.rms_px + " " + t("thermal pixels")], [t("Points"), String(r.n)]];
    if (r.v_scale != null && Math.abs(r.v_scale - 1) > 0.08) rows.push([t("Height"), tf("fits only roughly ({p} %)", {p: Math.round((r.v_scale - 1) * 100)})]);
    if (S.expect) rows.push([t("Simulator expects"), tf("zoom {z} % ({m}, {f})", {z: S.expect.zoom, m: S.expect.model, f: S.expect.fov})]);
    R.appendChild(kv(rows));
    if ((r.note || []).includes("narrow")) R.appendChild(el("div", "ta-msg warn", t("The thermal camera sees less than the main camera: zoom stays at 100 %, only the shift is set.")));
    if ((r.note || []).includes("still")) R.appendChild(el("div", "ta-msg warn", t("The hand hardly moved: only the shift was measured, the zoom stayed.")));
    if (r.clipped) R.appendChild(el("div", "ta-msg warn", t("The shift is bigger than ±30 %: point the thermal camera better (mechanically).")));
  }
  const N = S.now || {};
  $$("ta-now").textContent = tf("Now: zoom {z} %, left / right {x} %, up / down {y} %", {z: N.zoom, x: N.dx, y: N.dy}) + (S.sim ? " · " + t(N.own ? "simulator: measured values" : "simulator: automatic by the field of view") : "");
}
async function load() {
  clearTimeout(TA.timer);
  try { const r = await fetch("/api/thermal_align?lang=" + LANG, {cache: "no-store"}); if (r.ok) TA.s = await r.json(); } catch (e) {}
  paint();
  if (Date.now() - TA.img > 900) { TA.img = Date.now(); $$("ta-img").src = "/api/frame.jpg?" + Date.now(); }
  TA.timer = setTimeout(load, TA.s && TA.s.busy ? 700 : 2000);
}
$$("ta-start").onclick = () => op({op: "start"}).then(load);
$$("ta-stop").onclick = () => op({op: "stop"});
$$("ta-undo").onclick = () => op({op: "undo"});
$$("ta-hand").onclick = () => op({op: "hand", on: !(TA.s && TA.s.hand)});
(async () => { await initAppearance(); load(); })();
</script></body></html>"""

TALIGN_PAGE_KEYS = ["Align the thermal picture (warm hand)", "Hand in front", "Measure", "Result", "talign-note", "Start measuring", "Stop", "Undo",
                    "Thermal camera settings", "Simulator: take the warm hand away", "Simulator: warm hand in front of MoveEye",
                    "{n} points (at least {need})", "no thermal camera selected",
                    "Taken over - the thermal picture is laid over the camera picture with these values.", "Zoom", "Left / right", "Up / down",
                    "Accuracy", "thermal pixels", "Points", "Height", "fits only roughly ({p} %)", "Simulator expects", "zoom {z} % ({m}, {f})",
                    "The thermal camera sees less than the main camera: zoom stays at 100 %, only the shift is set.",
                    "The hand hardly moved: only the shift was measured, the zoom stayed.",
                    "The shift is bigger than ±30 %: point the thermal camera better (mechanically).",
                    "Now: zoom {z} %, left / right {x} %, up / down {y} %", "simulator: measured values", "simulator: automatic by the field of view"]


def talign_page():
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in TALIGN_PAGE_KEYS}, ensure_ascii=False) + ");"
    return render_page(TALIGN_PAGE, "tools").replace("/*TALIGNDE*/", js, 1)


def talign_routes(app, reply, body):
    from flask import Response, request

    @app.route("/thermal_align")
    def talign_web_page():
        return Response(talign_page(), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/thermal_align", methods=["GET", "POST"])
    def api_talign():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang)
            res, code = talign_api(d, lang)
            return reply(res, code)
        return reply(talign_state(lang))


_servo_routes_541 = servo_routes


def servo_routes(app, reply, body):                       # + 557: the routes of the thermal assistant (550 calls servo_routes)
    _servo_routes_541(app, reply, body)
    talign_routes(app, reply, body)


# Mehr → Werkzeuge → Geräte-Tests: one entry (a link like «Servos»)
_TA_TOOL = ('<a class="tli" data-k="talign" href="/thermal_align" style="text-decoration:none;color:inherit"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M8 13V5a1.5 1.5 0 0 1 3 0v6M11 11V4a1.5 1.5 0 0 1 3 0v7M14 11V5a1.5 1.5 0 0 1 3 0v8M8 12a1.5 1.5 0 0 0-3 0v2c0 4 3 7 7 7s6-3 6-7v-1"/></svg>'
            '<span class="tln"><b data-i18n="Align the thermal picture">Align the thermal picture</b><span class="tsum" data-i18n="warm hand in front of MoveEye">warm hand in front of MoveEye</span></span><i class="tdot"></i></a>\n  ')
if 'data-k="talign"' not in TOOLS_PAGE and '<a class="tli" data-k="servo"' in TOOLS_PAGE:
    TOOLS_PAGE = TOOLS_PAGE.replace('<a class="tli" data-k="servo"', _TA_TOOL + '<a class="tli" data-k="servo"', 1)
    TOOLS_PAGE = TOOLS_PAGE.replace('Object.assign(I18N.de, {"All tools"', 'Object.assign(I18N.de, {"Align the thermal picture": "Wärmebild ausrichten", '
                                    '"warm hand in front of MoveEye": "warme Hand vor MoveEye"});\nObject.assign(I18N.de, {"All tools"', 1)


# ---- the window (Tkinter): the same steps --------------------------------------------------------------------------------
def _talign_tk_win(app):
    win = getattr(app, "_talign_w", None)
    try:
        if win is not None and win.winfo_exists():
            win.lift(); return
    except Exception:
        pass
    win = tk.Toplevel(app.root); app._talign_w = win
    win.title("MoveEye – " + tr("Align the thermal picture (warm hand)")); win.geometry("560x560")
    fr = ttk.Frame(win); fr.pack(fill="both", expand=True, padx=12, pady=10)
    steps = ttk.Frame(fr); steps.pack(fill="x")
    sl = []
    for i, k in enumerate(("Hand in front", "Measure", "Result")):
        lb = tk.Label(steps, text=f"{i + 1} · {tr(k)}", bg=C["panel"], fg=C["mut"], padx=6, pady=5, highlightthickness=1, highlightbackground=C["line"])
        lb.pack(side="left", expand=True, fill="x", padx=(0 if i == 0 else 6, 0)); sl.append(lb)
    ttk.Label(fr, text=tr("talign-note"), style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(8, 4))
    bf = ttk.Frame(fr); bf.pack(fill="x", pady=(6, 0))
    b_start = ttk.Button(bf, text="▶ " + tr("Start measuring"), command=lambda: _act(lambda: talign_start("window")))
    b_stop = ttk.Button(bf, text=tr("Stop"), command=lambda: TALIGN.update(stop=True))
    b_undo = ttk.Button(bf, text="↶ " + tr("Undo"), command=lambda: _act(talign_undo))
    b_hand = ttk.Button(fr, text="", command=lambda: _act(lambda: (bool(talign_api({"op": "hand", "on": not SIM.get("warm_hand")})[0].get("ok")), "simulator not reachable")))
    bar = ttk.Progressbar(fr, maximum=100); prog = ttk.Label(fr, text="", style="Mut.TLabel")
    msg = ttk.Label(fr, text="", wraplength=520, justify="left")
    res = ttk.Label(fr, text="", wraplength=520, justify="left", font=("DejaVu Sans", 10))
    now_l = ttk.Label(fr, text="", style="Mut.TLabel", wraplength=520, justify="left")
    for w_ in (bar, prog, msg, res, now_l):
        w_.pack(fill="x", anchor="w", pady=(6, 0))

    def _act(fn):
        def run():
            try:
                r = fn()
                if isinstance(r, tuple) and not r[0] and r[1]:
                    app.root.after(0, lambda: messagebox.showinfo("MoveEye", tr_err(r[1]), parent=win))
            except Exception as e:
                log_event("sys", f"Window: thermal alignment: {e}"[:160])
        threading.Thread(target=run, daemon=True).start()

    def refresh():
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return
        S = talign_state()
        step = 2 if S["busy"] else (3 if S["phase"] == "done" else 1)
        for i, lb in enumerate(sl):
            on = i + 1 == step
            lb.configure(fg=C["txt"] if on else C["mut"], highlightbackground=C["acc"] if on else C["line"], font=("DejaVu Sans", 9, "bold" if on else "normal"))
        for b in (b_start, b_stop, b_undo):
            b.pack_forget()
        (b_stop if S["busy"] else b_start).pack(side="left", expand=True, fill="x")
        if S["undo"] and not S["busy"]:
            b_undo.pack(side="left", expand=True, fill="x", padx=(6, 0))
        if S["sim"]:
            b_hand.configure(text="🖐 " + tr("Simulator: take the warm hand away" if S["hand"] else "Simulator: warm hand in front of MoveEye"))
            if not b_hand.winfo_ismapped():
                b_hand.pack(fill="x", pady=(6, 0), before=bar)
        elif b_hand.winfo_ismapped():
            b_hand.pack_forget()
        bar.configure(value=int(S["progress"] * 100) if S["busy"] else 0)
        prog.configure(text=trf("{n} points (at least {need})", n=S["n"], need=S["need"]) if S["busy"] else "")
        m = S["msg"] or ("" if S["source"] else tr("no thermal camera selected"))
        msg.configure(text=("⚠ " + m) if m else "")
        r = S["res"]
        if S["phase"] == "done" and r:
            L = ["✅ " + tr("Taken over - the thermal picture is laid over the camera picture with these values."),
                 f"{tr('Zoom')}: {r['zoom']} %   {tr('Left / right')}: {r['dx']} %   {tr('Up / down')}: {r['dy']} %",
                 f"{tr('Accuracy')}: ± {r['rms_px']} {tr('thermal pixels')}   {tr('Points')}: {r['n']}"]
            if r.get("v_scale") is not None and abs(r["v_scale"] - 1) > 0.08:
                L.append(tr("Height") + ": " + trf("fits only roughly ({p} %)", p=int(round((r["v_scale"] - 1) * 100))))
            if S["expect"]:
                L.append(tr("Simulator expects") + ": " + trf("zoom {z} % ({m}, {f})", z=S["expect"]["zoom"], m=S["expect"]["model"], f=S["expect"]["fov"]))
            for k_, txt in (("narrow", "The thermal camera sees less than the main camera: zoom stays at 100 %, only the shift is set."),
                            ("still", "The hand hardly moved: only the shift was measured, the zoom stayed.")):
                if k_ in (r.get("note") or []):
                    L.append("⚠ " + tr(txt))
            if r.get("clipped"):
                L.append("⚠ " + tr("The shift is bigger than ±30 %: point the thermal camera better (mechanically)."))
            res.configure(text="\n".join(L))
        else:
            res.configure(text="")
        N = S["now"]
        now_l.configure(text=trf("Now: zoom {z} %, left / right {x} %, up / down {y} %", z=N["zoom"], x=N["dx"], y=N["dy"])
                        + ((" · " + tr("simulator: measured values" if N["own"] else "simulator: automatic by the field of view")) if S["sim"] else ""))
        win.after(600, refresh)
    refresh()


def _talign_tk_build_section(self, sec, sbody, settings_parent=None):
    _TALIGN_TK["before"](self, sec, sbody, settings_parent)
    if sec == "Thermal camera":
        try:
            ttk.Button(sbody, text="🖐 " + tr("Align the thermal picture (warm hand)") + " …", command=lambda: _talign_tk_win(self)).pack(fill="x", pady=(6, 0))
        except Exception as e:
            log_event("sys", f"Window: thermal alignment button: {e}"[:160])


_TALIGN_TK = {"before": None}


# ---- texts (English key: German, French, Italian, Romansh) ---------------------------------------------------------------
_HX_SIMINT = {
    # 554
    'own sound ignored': ('eigener Ton ignoriert', 'son propre ignoré', 'suono proprio ignorato', 'agen tun ignorà'),
    # 555
    'a servo is blocked - the head does not follow (stuck at the end stop?)': ('ein Servo ist blockiert – der Kopf folgt nicht (klemmt am Anschlag?)', 'un servo est bloqué – la tête ne suit pas (coincée en butée ?)', 'un servo è bloccato – la testa non segue (incastrata a fine corsa?)', 'in servo è blocà – il chau na suonda betg (sa serra a la fin?)'),
    '5 V rail {v} V': ('5-V-Schiene {v} V', 'rail 5 V {v} V', 'linea 5 V {v} V', 'lingia da 5 V {v} V'),
    'under-voltage': ('Unterspannung', 'sous-tension', 'sottotensione', 'tensiun memia bassa'),
    'I2C error': ('I2C-Fehler', 'erreur I2C', 'errore I2C', 'errur I2C'),
    'PCA9685 reset': ('PCA9685-Reset', 'réinitialisation PCA9685', 'reset PCA9685', 'reset PCA9685'),
    'servo blocked': ('Servo blockiert', 'servo bloqué', 'servo bloccato', 'servo blocà'),
    # 557
    'Align the thermal picture (warm hand)': ('Wärmebild ausrichten (warme Hand)', 'Aligner l’image thermique (main chaude)', 'Allineare l’immagine termica (mano calda)', 'Drizzar il maletg termic (maun chauda)'),
    'Align the thermal picture': ('Wärmebild ausrichten', 'Aligner l’image thermique', 'Allineare l’immagine termica', 'Drizzar il maletg termic'),
    'warm hand in front of MoveEye': ('warme Hand vor MoveEye', 'main chaude devant MoveEye', 'mano calda davanti a MoveEye', 'maun chauda davant MoveEye'),
    'Hand in front': ('Hand davor', 'Main devant', 'Mano davanti', 'Maun davant'),
    'Measure': ('Messen', 'Mesurer', 'Misurare', 'Mesirar'),
    'Result': ('Ergebnis', 'Résultat', 'Risultato', 'Resultat'),
    'talign-note': ('Jemand hält eine warme Hand 2–3 m vor MoveEye und bewegt sie langsam hin und her, auf und ab (sonst niemand im Bild, der Kopf steht still). MoveEye sucht den warmen Fleck im Wärmebild und die Bewegung im Kamerabild und stellt Zoom und Verschiebung des Wärmebilds ein. Im Simulator hält eine warme Hand von selbst hin.',
                    'Quelqu’un tient une main chaude à 2–3 m devant MoveEye et la bouge lentement de gauche à droite et de haut en bas (personne d’autre dans l’image, la tête reste immobile). MoveEye cherche la tache chaude dans l’image thermique et le mouvement dans l’image de la caméra et règle le zoom et le décalage. Dans le simulateur, une main chaude apparaît toute seule.',
                    'Qualcuno tiene una mano calda a 2–3 m davanti a MoveEye e la muove lentamente a destra e sinistra, su e giù (nessun altro nell’immagine, la testa resta ferma). MoveEye cerca la macchia calda nell’immagine termica e il movimento nell’immagine della camera e imposta zoom e spostamento. Nel simulatore una mano calda appare da sola.',
                    'Insatgi tegna ina maun chauda 2–3 m davant MoveEye e la mova plaun da vart e si e giu (nagin auter en il maletg, il chau stat airi). MoveEye tschertga il fleck chaud en il maletg termic ed il moviment en il maletg da la camera e drizza zoom e spustament. En il simulatur cumpara ina maun chauda da sasezza.'),
    'Start measuring': ('Messen starten', 'Démarrer la mesure', 'Avviare la misura', 'Cumenzar a mesirar'),
    'Undo': ('Rückgängig', 'Annuler', 'Annulla', 'Revocar'),
    'Thermal camera settings': ('Einstellungen Wärmebild', 'Réglages caméra thermique', 'Impostazioni termocamera', 'Parameters camera termica'),
    'Simulator: take the warm hand away': ('Simulator: warme Hand wegnehmen', 'Simulateur : retirer la main chaude', 'Simulatore: togliere la mano calda', 'Simulatur: prender davent la maun chauda'),
    'Simulator: warm hand in front of MoveEye': ('Simulator: warme Hand vor MoveEye', 'Simulateur : main chaude devant MoveEye', 'Simulatore: mano calda davanti a MoveEye', 'Simulatur: maun chauda davant MoveEye'),
    '{n} points (at least {need})': ('{n} Punkte (mindestens {need})', '{n} points (au moins {need})', '{n} punti (almeno {need})', '{n} puncts (almain {need})'),
    'no thermal camera selected': ('keine Wärmebild-Kamera gewählt', 'aucune caméra thermique choisie', 'nessuna termocamera scelta', 'nagina camera termica tschernida'),
    'Taken over - the thermal picture is laid over the camera picture with these values.': ('Übernommen – das Wärmebild liegt mit diesen Werten über dem Kamerabild.', 'Repris – l’image thermique est superposée à l’image de la caméra avec ces valeurs.', 'Applicato – l’immagine termica è sovrapposta all’immagine della camera con questi valori.', 'Surpiglià – il maletg termic giascha cun questas valurs sur il maletg da la camera.'),
    'Zoom': ('Zoom', 'Zoom', 'Zoom', 'Zoom'),
    'Left / right': ('Links / rechts', 'Gauche / droite', 'Sinistra / destra', 'Sanester / dretg'),
    'Up / down': ('Oben / unten', 'Haut / bas', 'Su / giù', 'Si / giu'),
    'Accuracy': ('Genauigkeit', 'Précision', 'Precisione', 'Exactadad'),
    'thermal pixels': ('Wärmebild-Pixel', 'pixels thermiques', 'pixel termici', 'pixels termics'),
    'Points': ('Punkte', 'Points', 'Punti', 'Puncts'),
    'Height': ('Höhe', 'Hauteur', 'Altezza', 'Autezza'),
    'fits only roughly ({p} %)': ('passt nur ungefähr ({p} %)', 'ne correspond qu’approximativement ({p} %)', 'corrisponde solo approssimativamente ({p} %)', 'correspunda mo circa ({p} %)'),
    'Simulator expects': ('Simulator erwartet', 'Le simulateur attend', 'Il simulatore si aspetta', 'Il simulatur spetga'),
    'zoom {z} % ({m}, {f})': ('Zoom {z} % ({m}, {f})', 'zoom {z} % ({m}, {f})', 'zoom {z} % ({m}, {f})', 'zoom {z} % ({m}, {f})'),
    'The thermal camera sees less than the main camera: zoom stays at 100 %, only the shift is set.': ('Die Wärmebild-Kamera sieht weniger als die Hauptkamera: Zoom bleibt 100 %, nur die Verschiebung wird eingestellt.', 'La caméra thermique voit moins que la caméra principale : le zoom reste à 100 %, seul le décalage est réglé.', 'La termocamera vede meno della camera principale: lo zoom resta al 100 %, si imposta solo lo spostamento.', 'La camera termica vesa damain che la camera principala: il zoom resta 100 %, mo il spustament vegn drizzà.'),
    'The hand hardly moved: only the shift was measured, the zoom stayed.': ('Die Hand hat sich kaum bewegt: nur die Verschiebung gemessen, der Zoom bleibt.', 'La main a à peine bougé : seul le décalage a été mesuré, le zoom reste.', 'La mano si è mossa appena: misurato solo lo spostamento, lo zoom resta.', 'La maun è strusch sa movida: mo il spustament mesirà, il zoom resta.'),
    'The shift is bigger than ±30 %: point the thermal camera better (mechanically).': ('Die Verschiebung ist grösser als ±30 %: Wärmebild-Kamera besser ausrichten (mechanisch).', 'Le décalage dépasse ±30 % : orienter mieux la caméra thermique (mécaniquement).', 'Lo spostamento supera ±30 %: orientare meglio la termocamera (meccanicamente).', 'Il spustament è pli grond che ±30 %: drizzar meglier la camera termica (mecanicamain).'),
    'Now: zoom {z} %, left / right {x} %, up / down {y} %': ('Jetzt: Zoom {z} %, links / rechts {x} %, oben / unten {y} %', 'Maintenant : zoom {z} %, gauche / droite {x} %, haut / bas {y} %', 'Ora: zoom {z} %, sinistra / destra {x} %, su / giù {y} %', 'Ussa: zoom {z} %, sanester / dretg {x} %, si / giu {y} %'),
    'simulator: measured values': ('Simulator: gemessene Werte', 'simulateur : valeurs mesurées', 'simulatore: valori misurati', 'simulatur: valurs mesiradas'),
    'simulator: automatic by the field of view': ('Simulator: automatisch nach dem Blickwinkel', 'simulateur : automatique selon le champ de vision', 'simulatore: automatico secondo il campo visivo', 'simulatur: automatic tenor l’angul da vista'),
    'the assistant is already measuring': ('der Assistent misst schon', 'l’assistant mesure déjà', 'l’assistente sta già misurando', 'l’assistent mesira gia'),
    'the assistant is measuring': ('der Assistent misst gerade', 'l’assistant est en train de mesurer', 'l’assistente sta misurando', 'l’assistent mesira gist'),
    'nothing to undo': ('nichts zum Rückgängigmachen', 'rien à annuler', 'niente da annullare', 'nagut da revocar'),
    'stopped': ('gestoppt', 'arrêté', 'fermato', 'fermà'),
    'too few points': ('zu wenige Punkte', 'trop peu de points', 'troppo pochi punti', 'memia paucs puncts'),
    'too few points - hold the warm hand 2-3 m in front of MoveEye and move it slowly (nobody else in the picture)': ('zu wenige Punkte – die warme Hand 2–3 m vor MoveEye halten und langsam bewegen (sonst niemand im Bild)', 'trop peu de points – tenir la main chaude à 2–3 m devant MoveEye et la bouger lentement (personne d’autre dans l’image)', 'troppo pochi punti – tenere la mano calda a 2–3 m davanti a MoveEye e muoverla lentamente (nessun altro nell’immagine)', 'memia paucs puncts – tegnair la maun chauda 2–3 m davant MoveEye e la mover plaun (nagin auter en il maletg)'),
    'no thermal picture - choose the thermal camera (Settings → Thermal camera)': ('kein Wärmebild – Wärmebild-Kamera wählen (Einstellungen → Wärmebild)', 'pas d’image thermique – choisir la caméra thermique (Réglages → Caméra thermique)', 'nessuna immagine termica – scegliere la termocamera (Impostazioni → Termocamera)', 'nagin maletg termic – tscherner la camera termica (Parameters → Camera termica)'),
    'only in the simulation': ('nur in der Simulation', 'seulement dans la simulation', 'solo nella simulazione', 'mo en la simulaziun'),
    'simulator not reachable': ('Simulator nicht erreichbar', 'simulateur injoignable', 'simulatore non raggiungibile', 'simulatur betg cuntanschibel'),
}
for _k, _v in _HX_SIMINT.items():
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the manual (DE / EN)
_HX_SIMINT_HELP = (
    ('<section id="thermal" data-icon="🌡"><h2>Wärmebild</h2>',
     "<p><b>🖐 Wärmebild ausrichten (warme Hand):</b> Einstellungen → Wärmebild → «Kamera und Ausrichtung» → «Wärmebild ausrichten» (oder "
     "Mehr → Werkzeuge → Geräte-Tests). Jemand hält eine warme Hand 2–3 m vor MoveEye und bewegt sie langsam hin und her und auf und ab. "
     "MoveEye sucht den warmen Fleck im Wärmebild und die Bewegung im Kamerabild und stellt Zoom und Verschiebung (links / rechts, oben / "
     "unten) selbst ein – «Rückgängig» bringt die alten Werte zurück. Wegen des Abstands der beiden Kameras stimmt die Ausrichtung am "
     "besten in der Entfernung, in der gemessen wurde. Im 3D-Simulator hält eine warme Hand von selbst hin (Kamerabild → Wärmebild); "
     "dort ersetzen die gemessenen Werte die automatische Anpassung nach dem Blickwinkel, «Rückgängig» = wieder automatisch. "
     "Der Simulator kann das Wärmebild als <i>Thermal-90 (Waveshare)</i> (80 × 62 Pixel, 90° × 67°, 15 Bilder/s, Rauschen 125 mK) oder "
     "als altes 45°-Modell zeigen.</p>"),
    ('<section id="thermal" data-icon="🌡"><h2>Thermal camera</h2>',
     "<p><b>🖐 Align the thermal picture (warm hand):</b> Settings → Thermal camera → «Camera and alignment» → «Align the thermal picture» "
     "(or More → Tools → Device tests). Somebody holds a warm hand 2–3 m in front of MoveEye and moves it slowly from side to side and up and "
     "down. MoveEye finds the warm spot in the thermal picture and the movement in the camera picture and sets zoom and shift (left / right, "
     "up / down) by itself – «Undo» brings the old values back. Because the two cameras sit a little apart, the alignment fits best at the "
     "distance it was measured. In the 3D simulator a warm hand appears by itself (Camera picture → Thermal picture); there the measured "
     "values replace the automatic fit by the field of view, «Undo» = automatic again. The simulator can show the thermal picture as "
     "<i>Thermal-90 (Waveshare)</i> (80 × 62 pixels, 90° × 67°, 15 pictures/s, noise 125 mK) or as the old 45° model.</p>"),
    ('<section id="lightsound" data-icon="💡"><h2>Licht &amp; Ton</h2>',
     "<p><b>🔊 Sirene im Simulator:</b> Ist der 3D-Simulator verbunden, ist er der Lautsprecher von MoveEye: Sirene, Wecker-Melodie und "
     "Ansagen gehen an den Simulator – auch in Spielen, Übungen und Testläufen (Test-Postfach); der echte Lautsprecher bleibt dann still. "
     "Der Simulator spielt einfache Töne am PC (Sensoren → Lautsprecher: Lautstärke, «Am PC stumm»), Besucher fliehen, und das simulierte "
     "Mikrofon hört den Ton. MoveEye ignoriert seinen eigenen Ton für Lärm-Alarm und Klatschschalter, solange er spielt und 2 s danach. "
     "<b>🛠 Servo-Störungen:</b> Simulator → Testen → «Störungen»: Unterspannung (der simulierte Akku liefert zu wenig, die Servos werden "
     "schwach), PCA9685-Reset, I2C-Fehler, Servo blockiert – MoveEye stoppt die Servos wie bei echter Hardware, trägt es im Fehlerspeicher "
     "ein (Werkzeuge → Servos → Diagnose) und braucht bei Treiber-Fehlern und blockiertem Servo «Freigeben».</p>"),
    ('<section id="lightsound" data-icon="💡"><h2>Light &amp; sound</h2>',
     "<p><b>🔊 Siren in the simulator:</b> while the 3D simulator is connected it is MoveEye's loudspeaker: siren, wake-up melody and "
     "announcements go to the simulator – also in games, drills and test runs (test inbox); the real loudspeaker stays silent then. The "
     "simulator plays simple tones on the PC (Sensors → Loudspeaker: volume, «mute on the PC»), visitors flee, and the simulated microphone "
     "hears the sound. MoveEye ignores its own sound for the noise alarm and the clap switch while it plays and 2 s after it. "
     "<b>🛠 Servo faults:</b> simulator → Testing → «Faults»: under-voltage (the simulated battery delivers too little, the servos get "
     "weak), PCA9685 reset, I2C error, servo blocked – MoveEye stops the servos like with real hardware, notes it in the fault memory "
     "(Tools → Servos → Diagnosis) and needs «Release» after driver faults and a blocked servo.</p>"),
)
for _a, _b in _HX_SIMINT_HELP:
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)

_SIMINT_LATE = {"done": False}


def _simint_late():
    """after all parts: the German texts (DE is made in 560), the button in the window (App is made in 570), the tools page"""
    if _SIMINT_LATE["done"]:
        return
    _SIMINT_LATE["done"] = True
    G = globals()
    try:
        for k, v in _HX_SIMINT.items():
            G["DE"].setdefault(k, v[0])
        G["DE"].setdefault("Align the thermal picture", _HX_SIMINT["Align the thermal picture"][0])
    except KeyError:
        pass
    try:
        App_ = G.get("App")
        if App_ is not None and _TALIGN_TK["before"] is None:
            _TALIGN_TK["before"] = App_._build_section
            App_._build_section = _talign_tk_build_section
    except Exception:
        pass


_load_settings_040_557 = load_settings


def load_settings(*a, **k):                               # + 557: the late part once (all parts are there now)
    _simint_late()
    return _load_settings_040_557(*a, **k)


_self_test_390_557 = self_test


def self_test(folder=""):                                 # + 557: the late part once, also for --self-test
    _simint_late()
    return _self_test_390_557(folder)


def talign_selftest():
    """the fit finds zoom and shift from synthetic pairs; the hot spot and the moving hand are found; page and texts"""
    rng = np.random.default_rng(5)
    z, dx, dy, asp, tw, thh = 0.65, 0.04, -0.03, 9 / 16.0, 80, 62
    zv = z * tw * asp / thh
    P = []
    for _ in range(30):
        x, y = rng.uniform(0.25, 0.75), rng.uniform(0.3, 0.7)
        P.append((x, y, 0.5 + dx - z / 2 + z * x + rng.normal(0, 0.004), 0.5 - dy - zv / 2 + zv * y + rng.normal(0, 0.004)))
    P.append((0.5, 0.5, 0.95, 0.05))                       # an outlier
    r = talign_fit(P, tw, thh, asp, 1.0)
    assert r and abs(r["zoom"] - 65) <= 2 and abs(r["dx"] - 4) <= 1 and abs(r["dy"] + 3) <= 1, r
    mt = [(i * 0.2, 0.5 + 0.2 * math.sin(i * 0.2 * 0.9), 0.5 + 0.15 * math.sin(i * 0.2 * 0.6)) for i in range(120)]
    tt = [(i * 0.3 + 0.6, 0.5 + 0.65 * (0.2 * math.sin((i * 0.3) * 0.9)), 0.5 + 0.47 * 0.15 * math.sin((i * 0.3) * 0.6)) for i in range(70)]
    lag, LP = talign_best_lag(mt, tt)                   # the thermal picture is 0.6 s late
    assert abs(lag - 0.6) < 0.11 and len(LP) > 40, lag
    a = np.full((62, 80), 15.0, np.float32); a[20:30, 50:56] = 34.0
    u, v, dt = talign_th_point(a)
    assert abs(u * 80 - 53) < 1.5 and 20 <= v * 62 <= 25 and dt > 15
    b = np.full((62, 80), 15.0, np.float32); b[5:12, 5:12] = 45.0                 # a hot grill that does not move
    a2, b2 = b.copy(), b.copy(); a2[20:30, 50:56] = 34.0; b2[20:30, 46:52] = 34.0  # the hand moves
    u2, _v2, _d2 = talign_th_point(a2, b2)
    assert 0.55 < u2 < 0.72, u2
    p0 = np.zeros((180, 320), np.uint8); p1 = p0.copy()
    cv2.rectangle(p0, (100, 60), (120, 100), 200, -1); cv2.rectangle(p1, (106, 60), (126, 100), 200, -1)
    mp = talign_main_point(p0, p1)
    assert mp is not None and 0.3 < mp[0] < 0.42 and mp[1] < 0.5, mp
    _simint_late()
    assert DE.get("talign-note", "").startswith("Jemand") and 'data-k="talign"' in TOOLS_PAGE
    html = talign_page()
    assert "/*TALIGNDE*/" not in html and "ta-start" in html
    assert talign_api({"op": "nonsense"})[1] == 400
    return f"zoom {r['zoom']} %, shift {r['dx']} / {r['dy']} % from {r['n']} points"


SELFTEST_EXTRA.append(("Thermal alignment with a warm hand: fit, hot spot, moving hand, page (557)", talign_selftest))
