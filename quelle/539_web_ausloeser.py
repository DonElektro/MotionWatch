#@ MoveEye – Teil 539: «Auslöser» – ein Mensch steuert die Kamera und drückt ab (Fadenkreuz, runder Knopf, R2, Test-Postfach). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): when a PERSON steers the camera instead of the AI («Team gegen MoveEye», the game of the
# 3D simulator where the guards sit at MoveEye), the guard aims the MIDDLE of the live picture at a player and presses the
# shutter. The simulator decides (simulator3d/scripts/gameshutter.gd): a hit = the player touches the circle in the middle
# (its size by the difficulty of the game: easy big, hard small), a miss = a false alarm (−50, the shutter locked 3 s).
#   Web (live page and «Controller-Ansicht» 538): crosshair over the live picture and ONE big round 🎯 button at the
#     bottom right of the live picture (thumb) - the former 🎯 «Schiessen» button of 2.95.96 (530 simShootPaint), now only
#     during such a round, inside the picture and moved away from other controls (no overlap in any layout).
#     R2 of the controller in the Controller-Ansicht = the shutter whenever the simulator is there (outside a round: the
#     shot into the world of 2.95.96, at the middle). Request: /api/sim {action: shoot, x: .5, y: .5, shutter: true}.
#   A hit is a real alarm of MoveEye like with the AI: the simulator switches its light on and sounds its siren, and puts the
#     hit into world_reply «shut»; MoveEye (350 → shut_feed) then writes a push with the photo (crosshair, time, name) into
#     its TEST INBOX only (sandbox_add + msglog_add «Test-Postfach») - never a real push - and the alarm light (light_alarm).
#   The phone of a guard and the game at the simulator PC have the same (game.gd, localplay.gd, headpad.gd).
# Translations: part 634.
# ----------------------------------------------------------------------------

SHUT = {"seen": 0, "n": 0, "last": None}


def shut_feed(lst, first=False):
    """world_reply «shut» of the simulator: new hits of the shutter become an alarm in the test inbox (never a real push)"""
    if not isinstance(lst, list):
        return
    for it in lst[-6:]:
        if not isinstance(it, dict):
            continue
        try:
            id_ = int(it.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if id_ <= SHUT["seen"]:
            continue
        SHUT["seen"] = id_
        if first:                                         # old shots of before the connection do not count
            continue
        if it.get("hit"):
            threading.Thread(target=shut_alarm, args=(dict(it),), daemon=True, name="shutalarm").start()
        else:
            log_event("sim", f"Shutter: {str(it.get('by') or 'guard')[:30]} missed - counted as a false alarm")


def shut_alarm(it):
    """a hit of the shutter: like a person alarm of the AI - alarm light, the push with the photo into the TEST INBOX"""
    jpg = None
    try:
        jpg, _h = _sim_get(f"/shut_pic/{int(it.get('id') or 0)}.jpg", 3.0)
        if not jpg or jpg[:2] != b"\xff\xd8":
            jpg = None
    except Exception:
        jpg = None
    try:
        light_alarm()                                     # the light as at an alarm (what «Licht bei Alarm» says)
    except Exception:
        pass
    nm, by = str(it.get("n") or "?")[:30], str(it.get("by") or "MoveEye")[:30]
    t_ = int(it.get("t") or 0)
    title = ("[SIM] " if CFG.get("sim_on") else "") + "🎯 " + trf("Shutter: {name} caught", name=nm)
    text = trf("Photo by {by} · {m}:{s} in the round · {d} m · +{pts} points", by=by, m=t_ // 60, s=f"{t_ % 60:02d}",
               d=int(round(float(it.get("d") or 0))), pts=int(it.get("pts") or 0))
    try:
        sandbox_add(title, text, jpg, "person")
        msglog_add(title, text, "person", jpg, "test", "Test-Postfach")
    except Exception as e:
        log_event("sim", f"Shutter: test inbox failed: {e}"[:160])
    SHUT["n"] += 1
    SHUT["last"] = {"t": time.time(), "name": nm, "pts": int(it.get("pts") or 0)}
    log_event("sim", f"Shutter: {by} caught {nm} (+{int(it.get('pts') or 0)}) - alarm into the test inbox")


SHUT_JS = r"""
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*AUSLDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, id) => { const x = document.createElement(tag); if (id) x.id = id; return x; };
  const css = E("style"); css.textContent =
    "#msh-x{position:absolute;z-index:58;pointer-events:none;border:3px solid #ff3b30;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 1px rgba(0,0,0,.55),inset 0 0 0 1px rgba(0,0,0,.55)}"
    + "#msh-x::before,#msh-x::after{content:'';position:absolute;left:50%;top:50%;width:3px;height:calc(100% + 28px);background:#ff3b30;transform:translate(-50%,-50%)}#msh-x::after{transform:translate(-50%,-50%) rotate(90deg)}"
    + "#msh-x.hard::before,#msh-x.hard::after{height:calc(100% + 40px)}"
    + "#msh-b{position:absolute;z-index:62;border-radius:50%;padding:0;margin:0;border:3px solid #fff;color:#fff;font-size:30px;line-height:1;display:flex;align-items:center;justify-content:center;"
    + "background:radial-gradient(circle,#e5383b 0 60%,transparent 61%),conic-gradient(#ffd34d var(--p,0%),rgba(255,255,255,.28) 0);box-shadow:0 4px 18px rgba(0,0,0,.55);touch-action:manipulation;cursor:pointer;-webkit-tap-highlight-color:transparent}"
    + "#msh-b:active{transform:scale(.94)}#msh-b.lock{opacity:.85;cursor:not-allowed}#msh-b span{font-weight:800;text-shadow:0 1px 3px rgba(0,0,0,.6)}"
    + "#msh-x[hidden],#msh-b[hidden]{display:none}"
    + "#msh-fl{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none;z-index:57}#msh-fl.on{animation:mshfl .35s ease-out}@keyframes mshfl{0%{opacity:.85}100%{opacity:0}}";
  document.head.appendChild(css);
  const XH = E("div", "msh-x"), BT = E("button", "msh-b"), FL = E("div", "msh-fl"), IC = E("span");
  XH.hidden = true; BT.hidden = true; BT.type = "button"; BT.appendChild(IC); IC.textContent = "🎯";
  const SH = {until: 0, len: 3, busy: false};
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const ST = () => J().state || {};
  const game = () => (ST().sim || {}).game || null;
  const simLive = () => { const s = ST().sim || {}; return !!(s.on && s.ok); };
  // a round of «Team gegen MoveEye»: the guards at MoveEye steer the real head - the shutter is theirs
  const roundOn = () => { const G = game(); return !!(G && G.mode === "mwhand" && (G.round === "play" || G.round === "countdown") && (!G.shut || G.shut.on !== false)); };
  function flash() { const c = FL.parentNode; if (!c) return; FL.classList.remove("on"); void FL.offsetWidth; FL.classList.add("on"); }
  function fire() {
    if (!simLive()) return false;
    const now = Date.now();
    if (now < SH.until) { if (typeof toast === "function") toast("⏳ " + T("Shutter locked") + " – " + Math.ceil((SH.until - now) / 1000) + " s"); return true; }
    if (SH.busy) return true;
    SH.busy = true; flash();
    post("/api/sim", {action: "shoot", x: 0.5, y: 0.5, shutter: true, lang: LANG}).then(r => {
      SH.busy = false; r = r || {};
      if (r.lock > 0) { SH.until = Date.now() + r.lock * 1000; SH.len = r.hit ? r.lock : Math.max(r.lock, 3); }
      let m;
      if (!r.ok) m = "⚠ " + (r.error || T("error"));
      else if (r.shutter && r.hit && r.pts > 0) m = "🎯 " + r.name + " " + T("caught!") + " +" + r.pts + " " + T("points") + " (" + Math.round(r.dist || 0) + " m) · 🚨 " + T("alarm into the test inbox");
      else if (r.shutter && !r.hit) m = "✗ " + T("Missed - false alarm") + " (" + (r.pts || -50) + ") · " + T("shutter locked 3 s");
      else m = r.text || "";
      if (typeof toast === "function" && m) toast(m);
      paint();
    }).catch(() => { SH.busy = false; });
    return true;
  }
  BT.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); fire(); });
  ["pointerdown", "pointerup", "dblclick"].forEach(k => BT.addEventListener(k, e => e.stopPropagation()));
  window.mwShutCan = () => simLive();                     // 538: R2 = the shutter while the simulator is there
  window.mwShutFire = fire;
  window.mwShutOn = roundOn;
  // where the picture really is inside the element (object-fit: contain = black edges)
  function picRect(v) {
    const r = v.getBoundingClientRect(), nw = v.naturalWidth || 16, nh = v.naturalHeight || 9;
    const fit = getComputedStyle(v).objectFit, k = fit === "cover" ? Math.max(r.width / nw, r.height / nh) : fit === "fill" ? 0 : Math.min(r.width / nw, r.height / nh);
    const w = k ? nw * k : r.width, h = k ? nh * k : r.height;
    return {left: r.left + (r.width - w) / 2, top: r.top + (r.height - h) / 2, width: w, height: h};
  }
  const hits = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  function obstacles(cont, v) {
    const L = [...cont.querySelectorAll("button, .vtag, #vo-ctl, #vo-mctl, #lv-tools, #lv-joy > *, [role=application]")]
      .concat([...document.querySelectorAll("#pv-bar, #pv-x, #pv-pad, #pv-more, #mwg, #lv-vw .lv-vbtn, #iconhint, #pip")]);
    const vr = v.getBoundingClientRect(), out = [];
    L.forEach(x => {
      if (x === BT || x.contains(v) || BT.contains(x) || x.hidden) return;
      const r = x.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return;
      if (r.width * r.height > 0.45 * vr.width * vr.height) return;      // a big layer over the whole picture, not a control
      const cs = getComputedStyle(x); if (cs.display === "none" || cs.visibility === "hidden") return;
      out.push(r);
    });
    return out;
  }
  let lastSig = "";
  function paint() {
    const v = document.getElementById("video"), on = roundOn() && simLive() && v && v.offsetParent !== null;
    if (!on) { XH.hidden = BT.hidden = true; return; }
    const cont = v.parentNode;
    if (XH.parentNode !== cont) { cont.append(FL, XH, BT); }
    if (getComputedStyle(cont).position === "static") cont.style.position = "relative";
    const cr = cont.getBoundingClientRect(), p = picRect(v);
    // the visible part of the picture (the container cuts it off)
    const vis = {left: Math.max(p.left, cr.left), top: Math.max(p.top, cr.top), right: Math.min(p.left + p.width, cr.right), bottom: Math.min(p.top + p.height, cr.bottom)};
    if (vis.right - vis.left < 60 || vis.bottom - vis.top < 60) { XH.hidden = BT.hidden = true; return; }
    const G = game() || {}, S = G.shut || {}, rr = +S.r || 0.1;
    const d = Math.max(16, 2 * rr * p.height);
    XH.style.width = XH.style.height = d + "px";
    XH.style.left = (p.left + p.width / 2 - cr.left) + "px"; XH.style.top = (p.top + p.height / 2 - cr.top) + "px";
    XH.classList.toggle("hard", S.lv === "hard"); XH.title = T("Hit area") + ": " + T(S.lv === "easy" ? "easy" : S.lv === "hard" ? "hard" : "normal");
    XH.hidden = false;
    // the round shutter at the bottom right of the picture, moved up (then left) until nothing else is there
    const ph = vis.bottom - vis.top, sz = ph >= 300 ? 84 : ph >= 170 ? 68 : 56, m = 12;   // thumb-sized
    const obs = obstacles(cont, v);
    let pos = null;
    for (const side of ["r", "l"]) {
      const x = side === "r" ? vis.right - m - sz : vis.left + m;
      for (let y = vis.bottom - m - sz; y >= vis.top + m; y -= 10) {
        const c = {left: x - 4, top: y - 4, right: x + sz + 4, bottom: y + sz + 4};
        if (!obs.some(o => hits(c, o)) && !(d > 0 && hits(c, {left: p.left + p.width / 2 - d / 2, right: p.left + p.width / 2 + d / 2, top: p.top + p.height / 2 - d / 2, bottom: p.top + p.height / 2 + d / 2}))) { pos = {x, y}; break; }
      }
      if (pos) break;
    }
    if (!pos) pos = {x: vis.right - m - sz, y: vis.bottom - m - sz};
    BT.style.width = BT.style.height = sz + "px"; BT.style.fontSize = Math.round(sz * 0.38) + "px";
    BT.style.left = (pos.x - cr.left) + "px"; BT.style.top = (pos.y - cr.top) + "px";
    const left = Math.max(0, SH.until - Date.now()) / 1000;
    BT.style.setProperty("--p", (left > 0 ? Math.min(100, left / SH.len * 100) : 0) + "%");
    BT.classList.toggle("lock", left > 0);
    const tx = left > 0 ? String(Math.ceil(left)) : "🎯"; if (IC.textContent !== tx) IC.textContent = tx;
    const sig = LANG + (S.pts || 0);
    if (sig !== lastSig) { lastSig = sig; BT.title = T("Shutter: a shot at the middle of the picture (R2 on the controller)") + " · " + (S.pts || 0) + " " + T("points"); BT.setAttribute("aria-label", BT.title); }
    BT.hidden = false;
  }
  setInterval(paint, 120);
  addEventListener("resize", paint); addEventListener("scroll", paint, {passive: true});
  addEventListener("keydown", e => { if (e.code === "Enter" && e.shiftKey && roundOn()) { e.preventDefault(); fire(); } });   // PC: Shift + Enter
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", SHUT_JS + "</body>", 1)
