#@ MoveEye – Teil 639o: ein Geheimnis im Bergtal des 3D-Simulators – das Herz in der Live-Ansicht (Daniel 1.11.2026, Paket real-easter-egg). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# NICHTS davon in Hilfe, Anleitung oder Blinki – keine sichtbaren Texte. (Spoiler, nur für Entwickler: simulator3d/scripts/
# bergtal_ei.gd beschreibt den ganzen Ablauf.) Hier nur das Ende in MoveEye:
#   * Der Simulator meldet in seiner Antwort (world_reply «egg») nur dann etwas, wenn man ein Herz zeichnen kann und das
#     Murmeltier im Bild der Kopfkamera ist: {"st": "heart", "x", "y", "r"} (0 … 1 im Bild). simvals_take legt es in SIM["egg"].
#   * Die Live-Ansicht (WEB_PAGE, Bild #video) fragt /api/simegg alle 2.5 s (nur sichtbar, nur mit Simulation). Steht dort ein
#     Murmeltier, beginnt ein Strich, der nahe beim Murmeltier anfängt, eine Herz-Zeichnung (sonst bleibt alles wie immer);
#     mwHeart (510, dieselben Regeln wie ccw_heart in 230) prüft im Browser, POST /api/simegg prüft es hier noch einmal und
#     schickt die Mitte (0 … 1 im Bild) an den Simulator: sim_control {"action": "egg", "do": "heart", "x", "y"}. Der Simulator
#     entscheidet, ob es auf dem Murmeltier ist. Danach Herzchen und ein leiser Pfiff im Browser.
#   * Das MoveEye-Fenster (Tk) zeigt das Simulator-Bild auch, kann hier aber (noch) nicht zeichnen.
# Hier (nach 639n) weil sim_control, ccw_heart (230), smalltv_routes, WEB_PAGE, SIM vorher kommen.
# ----------------------------------------------------------------------------
_simvals_take_egg = simvals_take


def simvals_take(rep):                                    # + 639o: where the marmot is (only while a heart can be drawn)
    _simvals_take_egg(rep)
    try:
        e = rep.get("egg")
        SIM["egg"] = dict(e, t=time.time()) if isinstance(e, dict) and e.get("st") == "heart" else None
    except Exception:
        SIM["egg"] = None


def egg_state():
    e = SIM.get("egg") if CFG.get("sim_on") and SIM.get("ok") else None
    if not isinstance(e, dict) or time.time() - float(e.get("t") or 0) > 4.0:
        return {"ok": True, "egg": None}
    return {"ok": True, "egg": {k: e.get(k) for k in ("st", "x", "y", "r")}}


def egg_post(d):
    """a stroke over the live picture: {pts: [[x, y] …] (screen px), rect: [left, top, width, height] of the picture}"""
    d = d if isinstance(d, dict) else {}
    try:
        pts = [(float(p[0]), float(p[1])) for p in (d.get("pts") or [])[:3000]]
        l_, t_, w_, h_ = (float(v) for v in (d.get("rect") or [])[:4])
    except (TypeError, ValueError, IndexError):
        return {"ok": False, "error": "bad stroke", "code": 400}
    if w_ < 40 or h_ < 30 or not ccw_heart(pts):
        return {"ok": False, "error": "no heart"}
    if not CFG.get("sim_on"):
        return {"ok": False, "error": "no simulator"}
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x = ((min(xs) + max(xs)) / 2 - l_) / w_; y = ((min(ys) + max(ys)) / 2 - t_) / h_
    try:
        r = sim_control({"action": "egg", "do": "heart", "x": round(x, 4), "y": round(y, 4), "src": "mw"}) or {}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
    if r.get("ok"):
        SIM["egg"] = None
    return {"ok": bool(r.get("ok")), "error": r.get("error")}


_smalltv_routes_egg_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639o: /api/simegg (550 calls smalltv_routes once)
    _smalltv_routes_egg_base(app, reply, body)

    @app.route("/api/simegg", methods=["GET", "POST"])
    def api_simegg():
        from flask import request
        if request.method == "GET":
            return reply(egg_state())
        r = egg_post(body())
        code = r.pop("code", None)
        return reply(r, code) if code else reply(r)


EGG_JS = r"""<script>
// 639o: (no texts) - over the live picture of the simulator, see the comment of part 639o
(function () {
  const v = document.getElementById("video"), wrap = v && v.closest(".vwrap"); if (!wrap) return;
  let E = null, pts = null, trail = null;
  const rect = () => { const r = v.getBoundingClientRect(), nw = v.naturalWidth || 16, nh = v.naturalHeight || 9;
    const s = Math.min(r.width / nw, r.height / nh), w = nw * s, h = nh * s;       // object-fit: contain
    return [r.left + (r.width - w) / 2, r.top + (r.height - h) / 2, w, h]; };
  const poll = async () => {
    try { if (document.visibilityState === "visible" && !pts) { const j = await (await fetch("/api/simegg", {cache: "no-store"})).json(); E = j && j.egg; } } catch (e) { E = null; }
    setTimeout(poll, E ? 1200 : 2500); };
  setTimeout(poll, 3000);
  const near = (x, y) => { if (!E) return false; const R = rect(), mx = R[0] + E.x * R[2], my = R[1] + E.y * R[3];
    return Math.hypot(x - mx, y - my) < Math.max(140, (E.r || 0.05) * R[3] * 3); };
  wrap.addEventListener("pointerdown", e => { if (!E || !near(e.clientX, e.clientY)) return;
    e.preventDefault(); e.stopPropagation(); pts = [[e.clientX, e.clientY]];
    trail = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    trail.setAttribute("style", "position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;z-index:99998");
    trail.innerHTML = '<polyline fill="none" stroke="#ff7aa2" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>';
    document.body.appendChild(trail); try { wrap.setPointerCapture(e.pointerId); } catch (x) {} }, true);
  wrap.addEventListener("pointermove", e => { if (!pts) return; e.preventDefault(); e.stopPropagation(); pts.push([e.clientX, e.clientY]);
    trail.firstChild.setAttribute("points", pts.map(p => p[0] + "," + p[1]).join(" ")); }, true);
  const end = async e => { if (!pts) return; e.stopPropagation(); const P = pts; pts = null; if (trail) { trail.remove(); trail = null; }
    if (!(window.mwHeart ? window.mwHeart(P) : false)) return;
    try { const j = await (await fetch("/api/simegg", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({pts: P, rect: rect()})})).json();
      if (j && j.ok) { E = null; fx(P); } } catch (x) {} };
  wrap.addEventListener("pointerup", end, true); wrap.addEventListener("pointercancel", end, true);
  wrap.addEventListener("click", e => { if (pts) e.stopPropagation(); }, true);
  function fx(P) {                                   // little hearts and a quiet whistle (like the marmot of 510)
    const xs = P.map(p => p[0]), ys = P.map(p => p[1]), cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
    for (let i = 0; i < 9; i++) { const h = document.createElement("div"); h.textContent = "♥";
      h.style.cssText = "position:fixed;z-index:99999;pointer-events:none;font-size:" + (14 + i % 3 * 5) + "px;color:" + (i % 2 ? "#e8436a" : "#ff7aa2")
        + ";left:" + cx + "px;top:" + cy + "px;transition:transform 1.6s ease-out,opacity 1.6s ease-in;opacity:1";
      document.body.appendChild(h);
      requestAnimationFrame(() => requestAnimationFrame(() => { h.style.transform = "translate(" + Math.round((Math.random() - .5) * 140) + "px," + Math.round(-60 - Math.random() * 90) + "px)"; h.style.opacity = "0"; }));
      setTimeout(() => h.remove(), 1800); }
    try { const A = window.AudioContext || window.webkitAudioContext; if (!A) return; const ac = new A();
      [0.0, 0.5].forEach(st => { const o = ac.createOscillator(), g = ac.createGain(), t0 = ac.currentTime + 0.3 + st;
        o.type = "sine"; o.frequency.setValueAtTime(3000, t0); o.frequency.exponentialRampToValueAtTime(2100, t0 + 0.26);
        g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.12, t0 + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.27);
        o.connect(g); g.connect(ac.destination); o.start(t0); o.stop(t0 + 0.3); });
      setTimeout(() => ac.close(), 1800); } catch (x) {}
  }
})();
</script>"""
WEB_PAGE = WEB_PAGE.replace("</body>", EGG_JS + "</body>", 1)


def egg_selftest():
    hp = heart_points(400, 300, 120)
    assert ccw_heart(list(reversed(hp))) and not ccw_heart(hp)
    keep = (CFG.get("sim_on"), dict(SIM))
    _sc = globals()["sim_control"]; asked = []
    try:
        CFG["sim_on"] = True
        SIM.update(ok=True)
        simvals_take({"egg": {"st": "heart", "x": 0.5, "y": 0.6, "r": 0.05}})
        assert egg_state()["egg"] == {"st": "heart", "x": 0.5, "y": 0.6, "r": 0.05}
        simvals_take({})
        assert egg_state()["egg"] is None
        globals()["sim_control"] = lambda d_: (asked.append(d_), {"ok": True})[1]
        assert not egg_post({"pts": hp, "rect": [100, 100, 600, 400]})["ok"] and not asked      # clockwise: no heart
        assert egg_post({"pts": "x"}).get("code") == 400
        r = egg_post({"pts": list(reversed(hp)), "rect": [100, 100, 600, 400]})
        assert r["ok"] and asked[-1]["action"] == "egg" and asked[-1]["do"] == "heart", (r, asked)
        assert abs(asked[-1]["x"] - 0.5) < 0.02 and 0.3 < asked[-1]["y"] < 0.6, asked[-1]
    finally:
        globals()["sim_control"] = _sc
        CFG["sim_on"] = keep[0]
        SIM.clear(); SIM.update(keep[1])
    assert "/api/simegg" in WEB_PAGE and "mwHeart" in WEB_PAGE
    gd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "scripts", "bergtal_ei.gd")
    if os.path.exists(gd):                                # the simulator shows the same pattern as the marmot of MoveEye
        with open(gd, encoding="utf-8") as f:
            assert 'const BELLY := "' + _BELLY + '"' in f.read(), "bergtal_ei.gd BELLY differs from _BELLY (230)"
    return "heart over the live picture: rules, forwarding to the simulator, same belly pattern"


SELFTEST_EXTRA.append(("A secret of the simulator (heart over the live picture)", egg_selftest))
