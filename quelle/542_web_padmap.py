#@ MoveEye – Teil 542: EIN Controller-Konzept (MWPad): dieselbe Belegung des Game-Controllers für die Controller-Ansicht (538), die Simulator-Seite, das Handy-Spiel und den 3D-Simulator. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026, «einheitliches Controller-Konzept»): one base mapping everywhere - left stick = head,
# right stick = rover / view (R1 held = turn the view), R2 = shutter, A / B / X / Y = light / IR / photo / follow,
# Select = swap pictures, Start = menu (held = leave), L3 = head to the middle, R3 = next view; a game round puts the
# tools of the guard and the moves of the sneaker on the same places. The table MAP (modes, keys, texts in English and
# German), the reader of a controller (dead zone, sensitivity, invert Y, swap the sticks - stored per device in
# localStorage «mw-padset»), the vibration (vibrationActuator / hapticActuators), the help made from MAP, ONE crosshair
# and the mini-map with the field of view of the head are in PADMAP_JS (window.MWPad).
# The SAME text is in simulator3d/scripts/padmap.gd (const JS, between «# <padmap-js>» and «# </padmap-js>»): the
# simulator acts on the same MAP and serves the JS to the phones. The self-test compares both when the folder is there.
# Translations of the texts: part 639.
# ----------------------------------------------------------------------------

PADMAP_JS = r"""window.MWPad = window.MWPad || (function () {
  "use strict";
  // ONE mapping of the game controller for MoveEye and its simulator (3D-4.13 / MoveEye 2.98.38, wish of Daniel 30.10.2026).
  // The same text is in simulator3d/scripts/padmap.gd (JS) and in MoveEye part 542 (PADMAP_JS) - the self-test compares them.
  // modes: [key, action, English, Deutsch]; the simulator acts on the action, the help overlays are made from the texts.
  const MAP = /*MAP*/{
    "keys": {"ls": "L ◉", "rs": "R ◉", "r1rs": "R1 + R ◉", "dpad": "✚", "a": "A", "b": "B", "x": "X", "y": "Y", "l1": "L1", "r1": "R1",
             "l2": "L2", "r2": "R2", "select": "Select", "select_long": "Select ⏱", "start": "Start", "start_long": "Start ⏱", "l3": "L3", "r3": "R3"},
    "modes": {
      "sim": [["ls", "head", "Turn / tilt the head of MoveEye", "Kopf von MoveEye drehen / neigen"],
              ["rs", "drive", "Drive the rover (without rover: move the view)", "Rover fahren (ohne Rover: Ansicht bewegen)"],
              ["r1rs", "orbit", "Hold R1: turn the view", "R1 halten: Ansicht drehen"],
              ["r2", "shutter", "Shutter in a game round (otherwise zoom in)", "Auslöser in einer Spielrunde (sonst hineinzoomen)"],
              ["l1", "zoom_out", "Zoom out", "Herauszoomen"], ["r1", "zoom_in", "Tap R1: zoom in", "R1 tippen: hineinzoomen"],
              ["a", "light", "Light on / off", "Licht ein / aus"], ["b", "ir", "IR light on / off", "IR-Licht ein / aus"],
              ["x", "photo", "Photo", "Foto"], ["y", "follow", "Follow on / off", "Folgen ein / aus"],
              ["l3", "center", "Head to the centre", "Kopf zur Mitte"], ["r3", "view", "Next view", "Nächste Ansicht"],
              ["select", "swap", "Swap pictures / views", "Bilder / Ansichten tauschen"],
              ["start", "menu", "Menu (control panel)", "Menü (Bedienfeld)"], ["start_long", "exit", "Hold 1 s: leave", "1 s halten: beenden"],
              ["dpad", "head", "Head in small steps", "Kopf in kleinen Schritten"],
              ["l2", "pole", "Hold L2 + ✚ ↑↓: pole longer / shorter", "L2 halten + ✚ ↑↓: Stange länger / kürzer"]],
      "view": [["ls", "head", "Turn / tilt the head of MoveEye", "Kopf von MoveEye drehen / neigen"],
               ["rs", "drive", "Drive the rover (without rover: move the view)", "Rover fahren (ohne Rover: Ansicht bewegen)"],
               ["r1rs", "orbit", "Hold R1: turn the view", "R1 halten: Ansicht drehen"],
               ["r2", "shutter", "Shutter in a game round (otherwise zoom in)", "Auslöser in einer Spielrunde (sonst hineinzoomen)"],
               ["l1", "zoom_out", "Zoom out", "Herauszoomen"], ["r1", "zoom_in", "Tap R1: zoom in", "R1 tippen: hineinzoomen"],
               ["a", "light", "Light on / off", "Licht ein / aus"], ["b", "ir", "IR light on / off", "IR-Licht ein / aus"],
               ["x", "photo", "Photo", "Foto"], ["y", "follow", "Follow on / off", "Folgen ein / aus"],
               ["l3", "center", "Head to the centre", "Kopf zur Mitte"], ["r3", "view", "Next view", "Nächste Ansicht"],
               ["select", "swap", "Swap pictures / views", "Bilder / Ansichten tauschen"],
               ["select_long", "estop", "Hold 1.5 s: emergency stop of the servos", "1,5 s halten: Not-Aus der Servos"],
               ["start", "menu", "Menu (the bar)", "Menü (die Leiste)"], ["start_long", "exit", "Hold 1 s: leave", "1 s halten: beenden"],
               ["dpad", "nav", "Choose a button of the bar (A = press, B = back)", "Knopf der Leiste wählen (A = drücken, B = zurück)"]],
      "guard": [["ls", "head", "Turn / tilt the head (the camera)", "Kopf (die Kamera) drehen / neigen"],
                ["rs", "fine", "Aim finely (slow)", "Fein zielen (langsam)"],
                ["r2", "shutter", "Shutter: a shot at the middle of the picture", "Auslöser: Schuss auf die Bildmitte"],
                ["l1", "zoom", "Zoom (tool)", "Zoom (Werkzeug)"],
                ["a", "light", "Light", "Licht"], ["b", "scan", "Scan (tool)", "Scan (Werkzeug)"],
                ["x", "catch", "«Caught!»", "«Erwischt!»"], ["y", "siren", "Siren (tool)", "Sirene (Werkzeug)"],
                ["l3", "center", "Head back to the start direction", "Kopf zurück in die Startrichtung"],
                ["select", "replay", "Replay (after the round)", "Wiederholung (nach der Runde)"],
                ["start", "menu", "Pause menu · start the round", "Pause-Menü · Runde starten"], ["start_long", "exit", "Hold 1 s: leave the game", "1 s halten: Spiel verlassen"],
                ["dpad", "head", "Head in steps · menus: choose", "Kopf in Schritten · Menüs: wählen"]],
      "seek": [["ls", "head", "Turn / tilt the head (the camera)", "Kopf (die Kamera) drehen / neigen"],
               ["rs", "drive", "Drive the rover", "Rover fahren"],
               ["a", "light", "Light", "Licht"], ["x", "catch", "«Found!»", "«Gefunden!»"],
               ["l3", "center", "Head back to the start direction", "Kopf zurück in die Startrichtung"],
               ["select", "replay", "Replay (after the round)", "Wiederholung (nach der Runde)"],
               ["start", "menu", "Pause menu · start the round", "Pause-Menü · Runde starten"], ["start_long", "exit", "Hold 1 s: leave the game", "1 s halten: Spiel verlassen"],
               ["dpad", "head", "Head in steps · menus: choose", "Kopf in Schritten · Menüs: wählen"]],
      "runner": [["ls", "look", "Look around", "Umschauen"], ["rs", "walk", "Walk", "Gehen"],
                 ["r2", "run", "Run (hold)", "Rennen (halten)"],
                 ["a", "lamp", "Lamp", "Lampe"], ["b", "crouch", "Crouch", "Ducken"],
                 ["x", "stone", "Throw a stone (hunter: press the thing)", "Stein werfen (Jäger: Ding drücken)"], ["y", "crawl", "Crawl", "Kriechen"],
                 ["l3", "center", "Look straight ahead", "Geradeaus schauen"],
                 ["select", "replay", "Replay (after the round)", "Wiederholung (nach der Runde)"],
                 ["start", "menu", "Pause menu · start the round", "Pause-Menü · Runde starten"], ["start_long", "exit", "Hold 1 s: leave the game", "1 s halten: Spiel verlassen"],
                 ["dpad", "walk", "Walk · menus: choose", "Gehen · Menüs: wählen"]],
      "menu": [["dpad", "nav", "Choose (left stick too)", "Wählen (auch linker Stick)"], ["a", "ok", "Select", "Auswählen"],
               ["b", "back", "Back / close", "Zurück / schliessen"], ["l1", "area", "L1 / R1: control panel ⇄ dock", "L1 / R1: Bedienfeld ⇄ Leiste"],
               ["start", "close", "Close the menu", "Menü schliessen"]]},
    "roles": {"all": ["everything", "alles", "#c0ccdd"], "guard": ["guard (head)", "Wächter (Kopf)", "#ff9933"],
              "runner": ["sneaker", "Schleicher", "#59e673"], "rover": ["rover", "Rover", "#59a6ff"]},
    "rumble": {"caught": [1.0, 0.8, 500], "hit": [0.7, 0.5, 250], "alarm": [0.9, 0.6, 800], "seen": [0.25, 0.35, 120], "catch": [0.5, 0.7, 200]},
    "long": {"start": 800, "select": 1500}
  }/*END*/;
  const IX = {a: 0, b: 1, x: 2, y: 3, l1: 4, r1: 5, l2: 6, r2: 7, select: 8, start: 9, l3: 10, r3: 11, up: 12, down: 13, left: 14, right: 15};
  const SK = "mw-padset";                                  // dead zone, sensitivity, invert Y, swap sticks, vibration - per device
  const S = {dead: 0.18, sens: 1, inv: false, swap: false, rumble: true};
  try { Object.assign(S, JSON.parse(localStorage.getItem(SK) || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem(SK, JSON.stringify(S)); } catch (e) {} };
  function pads() { try { return [...(navigator.getGamepads ? navigator.getGamepads() : [])].filter(g => g && g.connected); } catch (e) { return []; } }
  const name = g => (g ? String(g.id).replace(/[(].*?[)]/g, "").trim().slice(0, 30) : "");
  function dz(x, y) {
    const d = Math.max(0.02, Math.min(0.5, +S.dead || 0.18)), l = Math.hypot(x, y);
    if (l <= d) return [0, 0];
    const k = Math.min(1, (l - d) / (1 - d)) / l; return [x * k, y * k];
  }
  // a reader for one controller: call read(gamepad, mode) every tick; then .head .move .orbit .dpad, .fired (actions), .btn(key)
  function Pad(mode) {
    const P = {mode: mode || "sim", cur: [], prev: [], fired: [], keys: [], head: [0, 0], move: [0, 0], orbit: [0, 0], dpad: [0, 0], downT: {}, longDone: {}, r1Used: false, g: null};
    P.btn = k => !!P.cur[IX[k]];
    P.val = k => { const b = P.g && P.g.buttons[IX[k]]; return b ? (b.value || (b.pressed ? 1 : 0)) : 0; };
    P.read = function (g, md) {
      if (md) P.mode = md;
      P.g = g || null; P.prev = P.cur; P.fired = []; P.keys = [];
      if (!g) { P.cur = []; P.head = P.move = P.orbit = P.dpad = [0, 0]; return P; }
      P.cur = [...g.buttons].map(b => !!(b && (b.pressed || b.value > 0.5)));
      let L = dz(g.axes[0] || 0, g.axes[1] || 0), R = dz(g.axes[2] || 0, g.axes[3] || 0);
      if (S.swap) [L, R] = [R, L];
      const k = Math.max(0.2, Math.min(3, +S.sens || 1)), iv = S.inv ? -1 : 1, now = Date.now();
      const M = MAP.modes[P.mode] || [], has = key => M.some(e => e[0] === key);
      const dn = i => P.cur[i] && !P.prev[i], up = i => !P.cur[i] && P.prev[i];
      P.head = [L[0] * k, L[1] * k * iv];
      P.dpad = [(P.cur[15] ? 1 : 0) - (P.cur[14] ? 1 : 0), (P.cur[13] ? 1 : 0) - (P.cur[12] ? 1 : 0)];
      const r1 = P.cur[5] && has("r1rs");
      if (dn(5)) { P.downT.r1 = now; P.r1Used = false; }
      if (r1 && (R[0] || R[1])) P.r1Used = true;
      P.orbit = r1 ? [R[0] * k, R[1] * k * iv] : [0, 0];
      P.move = r1 ? [0, 0] : R;
      ["a", "b", "x", "y", "l1", "l2", "r2", "l3", "r3", "up", "down", "left", "right"].forEach(key => { if (dn(IX[key])) P.keys.push(key); });
      if (up(5) && !P.r1Used && now - (P.downT.r1 || 0) < 400) P.keys.push("r1");
      ["start", "select"].forEach(key => {
        const i = IX[key], ms = MAP.long[key];
        if (dn(i)) { P.downT[key] = now; P.longDone[key] = false; }
        if (P.cur[i] && !P.longDone[key] && now - (P.downT[key] || now) >= ms && has(key + "_long")) { P.longDone[key] = true; P.keys.push(key + "_long"); }
        if (up(i) && !P.longDone[key]) P.keys.push(key);
      });
      P.keys.forEach(key => { const e = M.find(x => x[0] === key); if (e) P.fired.push(e[1]); });
      return P;
    };
    return P;
  }
  // vibration (Gamepad API: vibrationActuator, or hapticActuators where only those exist); g = null: all controllers
  function rumble(g, kind) {
    if (!S.rumble) return false;
    const r = MAP.rumble[kind] || MAP.rumble.hit; let ok = false;
    (g ? [g] : pads()).forEach(p => {
      try {
        const va = p.vibrationActuator;
        if (va && va.playEffect) { const q = va.playEffect("dual-rumble", {startDelay: 0, duration: r[2], strongMagnitude: r[0], weakMagnitude: r[1]}); if (q && q.catch) q.catch(() => {}); ok = true; }
        else if (p.hapticActuators && p.hapticActuators[0] && p.hapticActuators[0].pulse) { p.hapticActuators[0].pulse(r[0], r[2]); ok = true; }
      } catch (e) {}
    });
    return ok;
  }
  // the help: rows [key, text] of a mode (T = translation of the English text, de = take the German text)
  function help(mode, T, de) { return (MAP.modes[mode] || []).map(e => [MAP.keys[e[0]] || e[0], de ? e[3] : (T ? T(e[2]) : e[2])]); }
  function helpLine(mode, T, de, only) { return help(mode, T, de).filter((r, i) => !only || only.includes(MAP.modes[mode][i][1])).map(r => r[0] + " " + r[1]).join(" · "); }
  function helpTable(mode, T, de) {
    const tb = document.createElement("table"); tb.className = "mwpad-help";
    help(mode, T, de).forEach(([k, v]) => { const tr = document.createElement("tr"), a = document.createElement("td"), b = document.createElement("td"); a.textContent = k; b.textContent = v; tr.append(a, b); tb.appendChild(tr); });
    return tb;
  }
  // ONE crosshair: a red ring with a cross through it (simulator: gameshutter.gd draws the same)
  const XH_CSS = sel => sel + "{position:absolute;pointer-events:none;border:3px solid #ff3b30;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 1px rgba(0,0,0,.55),inset 0 0 0 1px rgba(0,0,0,.55)}"
    + sel + "::before," + sel + "::after{content:'';position:absolute;left:50%;top:50%;width:3px;height:calc(100% + 28px);background:#ff3b30;transform:translate(-50%,-50%);box-shadow:0 0 0 1px rgba(0,0,0,.4)}"
    + sel + "::after{transform:translate(-50%,-50%) rotate(90deg)}";
  // the mini-map: north up, the head in the middle, its field of view (yellow), the rover (green), me (white);
  // on the rim: yellow = where the head looks, green = where the rover drives. d = {hx, hz, hy (deg), fov, rx, rz, ry (deg), me: [x, z]}
  function drawMap(cv, d, span) {
    if (!cv || !cv.getContext || !d) return;
    const c = cv.getContext("2d"), W = cv.width, H = cv.height, R = Math.min(W, H) / 2 - 3, cx = W / 2, cy = H / 2, sc = R / ((span || 40) / 2);
    const dir = deg => { const a = deg * Math.PI / 180; return [-Math.sin(a), -Math.cos(a)]; };
    const at = (x, z) => [cx + (x - (d.hx || 0)) * sc, cy + (z - (d.hz || 0)) * sc];
    c.clearRect(0, 0, W, H);
    c.save(); c.beginPath(); c.arc(cx, cy, R, 0, 2 * Math.PI); c.fillStyle = "rgba(8,12,20,.72)"; c.fill(); c.clip();
    const half = (d.fov || 66) / 2, n = 12;
    c.beginPath(); c.moveTo(cx, cy);
    for (let i = 0; i <= n; i++) { const v = dir((d.hy || 0) - half + 2 * half * i / n); c.lineTo(cx + v[0] * R * 0.95, cy + v[1] * R * 0.95); }
    c.closePath(); c.fillStyle = "rgba(255,210,60,.28)"; c.fill();
    if (d.rx != null) { const p = at(d.rx, d.rz), v = dir(d.ry || 0); c.save(); c.translate(p[0], p[1]); c.rotate(Math.atan2(v[1], v[0]) + Math.PI / 2);
      c.beginPath(); c.moveTo(0, -7); c.lineTo(5, 5); c.lineTo(-5, 5); c.closePath(); c.fillStyle = "#59e673"; c.fill(); c.restore(); }
    if (d.me) { const p = at(d.me[0], d.me[1]); c.beginPath(); c.arc(p[0], p[1], 4, 0, 2 * Math.PI); c.fillStyle = "#fff"; c.fill(); }
    c.beginPath(); c.arc(cx, cy, 4, 0, 2 * Math.PI); c.fillStyle = "#ff9933"; c.fill();
    c.restore();
    c.lineWidth = 2; c.strokeStyle = "rgba(255,255,255,.35)"; c.beginPath(); c.arc(cx, cy, R, 0, 2 * Math.PI); c.stroke();
    const mark = (deg, col) => { const v = dir(deg), a = Math.atan2(v[1], v[0]); c.save(); c.translate(cx + v[0] * R, cy + v[1] * R); c.rotate(a + Math.PI / 2);
      c.beginPath(); c.moveTo(0, -1); c.lineTo(6, 9); c.lineTo(-6, 9); c.closePath(); c.fillStyle = col; c.fill(); c.restore(); };
    mark(d.hy || 0, "#ffd34d"); if (d.ry != null) mark(d.ry, "#59e673");
    c.fillStyle = "rgba(255,255,255,.8)"; c.font = "bold 10px system-ui,sans-serif"; c.textAlign = "center"; c.fillText("N", cx, cy - R + 12);
  }
  // the settings (one place per device: dead zone, sensitivity, invert Y, swap sticks, vibration)
  function settingsUI(el, T, de) {
    const tx = (en, dt) => (de ? dt : (T ? T(en) : en));
    const box = document.createElement("div"); box.className = "mwpad-set";
    const row = (lb, inp) => { const l = document.createElement("label"); l.style.cssText = "display:flex;align-items:center;gap:8px;margin:4px 0"; const s = document.createElement("span"); s.textContent = lb; s.style.flex = "1"; l.append(s, inp); box.appendChild(l); };
    const rng = (k, min, max, step) => { const i = document.createElement("input"); i.type = "range"; i.min = min; i.max = max; i.step = step; i.value = S[k]; i.style.width = "120px"; i.oninput = () => { S[k] = parseFloat(i.value); save(); }; return i; };
    const chk = k => { const i = document.createElement("input"); i.type = "checkbox"; i.checked = !!S[k]; i.onchange = () => { S[k] = i.checked; save(); }; return i; };
    row(tx("Dead zone", "Totzone"), rng("dead", 0.02, 0.5, 0.01)); row(tx("Sensitivity", "Empfindlichkeit"), rng("sens", 0.3, 2.5, 0.1));
    row(tx("Invert Y (look)", "Y umkehren (schauen)"), chk("inv")); row(tx("Swap the sticks", "Sticks tauschen"), chk("swap"));
    row(tx("Vibration", "Vibration"), chk("rumble"));
    box.addEventListener("click", e => e.stopPropagation());
    el.appendChild(box); return box;
  }
  return {MAP, IX, S, save, pads, name, Pad, rumble, help, helpLine, helpTable, XH_CSS, drawMap, settingsUI};
})();
"""


def _padmap_inject(page):
    """the script before the first script of the page (538, 539 and the simulator part of 470 use MWPad)"""
    i = page.find("<script")
    return page if i < 0 else page[:i] + "<script>" + PADMAP_JS + "</script>" + page[i:]


WEB_PAGE = _padmap_inject(WEB_PAGE)
SIM_PAGE = _padmap_inject(SIM_PAGE)
WEB_UI_LOCAL.add("mw-padset")                             # per device: the controller settings of the tablet are not those of the PC


def padmap_selftest():
    """the mapping of the simulator (simulator3d/scripts/padmap.gd) is the same as PADMAP_JS; MAP is valid JSON"""
    m = re.search(r"/\*MAP\*/(.*?)/\*END\*/", PADMAP_JS, re.S)
    assert m, "MAP not found in PADMAP_JS"
    mp = json.loads(m.group(1))
    for k in ("sim", "view", "guard", "seek", "runner", "menu"):
        assert mp["modes"].get(k), f"mode {k} missing"
        for e in mp["modes"][k]:
            assert len(e) == 4 and e[0] in mp["keys"], f"bad entry {e}"
    assert "MWPad" in WEB_PAGE and "MWPad" in SIM_PAGE, "MWPad not in the pages"
    gd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "scripts", "padmap.gd")
    if not os.path.exists(gd):
        return f"{len(mp['modes'])} modes (simulator folder not here)"
    t = open(gd, encoding="utf-8").read()
    m2 = re.search(r'# <padmap-js>\nconst JS := r"""(.*?)"""\n# </padmap-js>', t, re.S)
    assert m2, "padmap.gd: JS not found"
    assert m2.group(1) == PADMAP_JS, "padmap.gd (simulator) and PADMAP_JS (part 542) differ - copy the same text into both"
    return f"{len(mp['modes'])} modes, same as the simulator"


SELFTEST_EXTRA.append(("One controller mapping (MWPad = simulator padmap.gd)", padmap_selftest))
