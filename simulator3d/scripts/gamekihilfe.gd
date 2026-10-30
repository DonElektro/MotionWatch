extends Node
## 3D-4.x «KI-Hilfe» (wish of Daniel): a PERSON is the guard with the shutter (gameshutter.gd: «Team gegen MoveEye» or
## «Wächter» / «Team gegen Team» with a person as guard) and may switch on help of the AI, for this round, in its own picture:
##   · «KI-Rahmen»   the live detection boxes of MoveEye on the guard's picture (main.mw_det.boxes: persons green, uncertain
##                   = not confirmed by the AI dashed). Without MoveEye (or for the fixed camera) the simulator's own AI
##                   (what the camera notices, game.cam_sees) gives the boxes - shown as «Sim-KI».
##   · «KI zielt»    the head follows the detected person like «Folgen»; the person presses the shutter.
##                   «Team gegen MoveEye»: MoveEye follows (part 542 / 162 of MoveEye read the mode from game_info shut.ki);
##                   a guard at the phone / PC: the head of the game (game.guard_yaw / guard_tilt) is turned here.
##   · «KI-Autopilot» aims AND fires the shutter by itself when sure (a confirmed box touches the hit circle for 0.5 s),
##                   only when the shutter is free and the energy is enough (gametools.gd). Any input of the person
##                   (stick, turning, shutter) pauses it 5 s - the person can take over any time.
## Every help marks the round «mit KI-Hilfe»: game.end_round gives no badges / XP, the round is not added to the
## leaderboard (board, records, week, challenge of the day), the results say it, and the game report (gamelearn.gd,
## shut.report()) has «ki_hilfe».
## Switches: phone (button «KI» on the guard page, message {t: "ki", mode}), PC (button on the picture, key K), MoveEye
## (live page and Controller-Ansicht: part 542 → /api/sim kihilfe → control «game_shut» {op: "ki", mode, slot}).

const MODES := ["off", "frame", "aim", "auto"]
const NAMES := {"off": "KI aus", "frame": "KI-Rahmen", "aim": "KI zielt", "auto": "KI-Autopilot"}
const HOLD := 0.5                          # the autopilot: a sure box in the hit circle this long → shot
const HUMAN_AUTO := 5.0                    # input of the person: the autopilot waits this long
const HUMAN_AIM := 1.5                     # … and «KI zielt» this long (like «Folgen» after steering by hand)
const AUTO_WHO := "KI-Autopilot"

var shut
var game
var main
var mode := {}                             # shooter key ("mw" / "p<slot>") -> mode
var used := {}                             # the modes used in this round
var used_by := {}                          # shooter key -> name (for the report)
var human_until := {}                      # shooter key -> time the AI may act again
var since := {}                            # shooter key -> since when a sure box is in the hit circle
var auto_shots := 0
var auto_hits := 0
var firing := false                        # the autopilot is firing right now (gameshutter.fire: no «human» input)
var _last := {}                            # shooter key -> [yaw, tilt] after our own turn (a change = the person turned)
var _goal := {}                            # shooter key -> [yaw, tilt, until] (the aim with MoveEye's boxes)
var _det_seen := 0.0
var _cache := {}                           # cam -> [time, boxes]
var _near_t := {}                          # shooter key -> last time a sure box was in the hit circle (KI-Wächter)
var _kg_det := 0.0
var _kg_n := 0
const GAP := 1.2                           # KI-Wächter: a gap without a box this long does not start the reaction time again


func now() -> float:
	return game.now()


func key(g) -> String:
	return shut._key(g)


func mode_of(g) -> String:
	return str(mode.get(key(g), "off"))


func used_round() -> bool:
	return not used.is_empty()


func _shooters() -> Array:
	"""who has the shutter now: [null] (the guards at MoveEye) or the human guards"""
	var hm: String = shut.human_mode()
	if hm == "mw":
		return [null]
	var out := []
	if hm == "guard":
		for p in game.players:
			if p != null and p["role"] == "guard" and str(p.get("kind", "phone")) != "bot":
				out.append(p)
	return out


func set_mode(g, m: String, who := "") -> Dictionary:
	if not m in MODES:
		return {"ok": false, "error": "unbekannte KI-Hilfe: " + m}
	if shut.human_mode() == "" or (g == null) != (shut.human_mode() == "mw"):
		return {"ok": false, "error": "Die KI-Hilfe gibt es nur in einer Runde, in der ein Mensch mit dem Auslöser bewacht."}
	var k := key(g)
	var old := str(mode.get(k, "off"))
	mode[k] = m
	since.erase(k)
	_goal.erase(k)
	human_until.erase(k)
	if m != old:
		var nm: String = who if who != "" else ("Wächter an MoveEye" if g == null else str(g["name"]))
		game.news("🤖 %s: %s" % [nm, NAMES[m]] + (" – die Runde zählt nicht für die Rangliste" if m != "off" else ""))
		if g != null:
			game._say(g, "🤖 " + NAMES[m] + (" – Runde zählt nicht für die Rangliste" if m != "off" else ""), 3.0)
		if m != "off" and game.round_state in ["countdown", "play"]:
			used[m] = true
			used_by[k] = nm
	return {"ok": true, "ki": info_for(g)}


func cycle(g) -> Dictionary:
	var i := MODES.find(mode_of(g))
	return set_mode(g, MODES[(i + 1) % MODES.size()])


func human(g) -> void:
	"""the person steers or shoots: the AI holds back (autopilot 5 s, aiming 1.5 s)"""
	var k := key(g)
	var m := str(mode.get(k, "off"))
	if m == "off" or m == "frame":
		return
	var was: bool = now() < float(human_until.get(k, 0.0))
	human_until[k] = now() + (HUMAN_AUTO if m == "auto" else HUMAN_AIM)
	since.erase(k)
	_goal.erase(k)
	if m == "auto" and not was:
		if g != null:
			game._say(g, "🤖 Autopilot pausiert 5 s – du steuerst", 2.0)
		game.news("🤖 KI-Autopilot pausiert – %s steuert" % ("Wächter an MoveEye" if g == null else str(g["name"])))


func paused(g) -> float:
	return maxf(0.0, float(human_until.get(key(g), 0.0)) - now())


func round_start() -> void:
	mode.clear()
	used.clear()
	used_by.clear()
	human_until.clear()
	since.clear()
	_last.clear()
	_goal.clear()
	auto_shots = 0
	auto_hits = 0


# ---- the boxes ---------------------------------------------------------------------------------------------------------
func boxes(cam_i: int) -> Dictionary:
	"""{src: "mw" (MoveEye's live detection) | "sim" (the simulator's own AI), b: [[x, y, w, h, sure], …] 0..1}"""
	var c = _cache.get(cam_i, null)
	if c != null and now() - float(c[0]) < 0.1:
		return c[1]
	var out := []
	var src := "sim"
	if cam_i == 0 and main.now() - main.mw_det_t < 1.5 and typeof(main.mw_det.get("boxes", null)) == TYPE_ARRAY:
		src = "mw"
		var b: Array = main.mw_det["boxes"]
		var s = main.mw_det.get("sure", null)
		for i in range(min(b.size(), 8)):
			var bx = b[i]
			if typeof(bx) != TYPE_ARRAY or bx.size() < 4:
				continue
			var sure: bool = true if typeof(s) != TYPE_ARRAY or i >= (s as Array).size() else bool(s[i])
			out.append([snappedf(float(bx[0]), 0.001), snappedf(float(bx[1]), 0.001), snappedf(float(bx[2]), 0.001), snappedf(float(bx[3]), 0.001), sure])
	else:
		for p in game.players:                             # what the camera notices (the AI of the game without MoveEye)
			if p == null or p["role"] != "runner" or p["state"] != "play" or int(p.get("hide_i", -1)) >= 0:
				continue
			var v: float = game.cam_sees(p, cam_i)
			if v < 0.12:
				continue
			var bb: Array = shut.box_cam(p, cam_i)
			if bb.is_empty():
				continue
			var sure: bool = v >= 0.35 or float(p.get("susp", 0.0)) >= 30.0    # sure like the guard of the game: the meter at 30 %
			out.append([snappedf(float(bb[0]), 0.001), snappedf(float(bb[1]), 0.001), snappedf(float(bb[2]), 0.001), snappedf(float(bb[3]), 0.001), sure])
	var r := {"src": src, "b": out}
	_cache[cam_i] = [now(), r]
	return r


func _cam(g) -> int:
	return 0 if g == null else game.guard_cam(g)


func _in_circle(bx: Array, cam_i: int) -> float:
	"""how far the box is from the middle (in picture heights; -1 = not in the hit circle)"""
	var vs := Vector2(main.vps[cam_i].size)
	var asp: float = vs.x / maxf(1.0, vs.y)
	var nx := clampf(0.5, float(bx[0]), float(bx[0]) + float(bx[2]))
	var ny := clampf(0.5, float(bx[1]), float(bx[1]) + float(bx[3]))
	var dd := Vector2((nx - 0.5) * asp, ny - 0.5).length()
	return dd if dd <= shut.radius() * 0.9 else -1.0


func _target(bl: Array) -> Array:
	"""the person to aim at: the biggest sure box (otherwise the biggest)"""
	var best: Array = []
	var ba := -1.0
	for bx in bl:
		var a: float = float(bx[2]) * float(bx[3]) * (2.0 if bool(bx[4]) else 1.0)
		if a > ba:
			ba = a
			best = bx
	return best


# ---- every frame -------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if game == null or shut == null:
		return
	var sh := _shooters()
	if sh.is_empty():
		since.clear()
		return
	var playing: bool = game.round_state == "play"
	for g in sh:
		var k := key(g)
		var m := str(mode.get(k, "off"))
		if m == "off":
			_last.erase(k)
			continue
		if game.round_state in ["countdown", "play"] and not used.has(m):
			used[m] = true
			used_by[k] = "Wächter an MoveEye" if g == null else str(g["name"])
		if m == "frame" or not playing:
			_last.erase(k)
			continue
		if g != null:
			_watch_human(g)
			if _cam(g) == 0 and g == game.guard_player():
				_aim(g, dt)
		if m == "auto":
			_auto(g)


func _watch_human(g) -> void:
	"""the guard at the phone / PC steers (stick, drag, mouse): a change of the head we did not make"""
	var k := key(g)
	if absf(float(g.get("mx", 0.0))) > 0.05 or absf(float(g.get("my", 0.0))) > 0.05:
		human(g)
	elif _last.has(k) and g == game.guard_player():
		var l: Array = _last[k]
		if absf(angle_difference(float(l[0]), game.guard_yaw)) > 0.002 or absf(float(l[1]) - game.guard_tilt) > 0.002:
			human(g)
	if g == game.guard_player():
		_last[k] = [game.guard_yaw, game.guard_tilt]


func _aim(g, dt: float) -> void:
	"""«KI zielt» / Autopilot for a guard at the phone / PC: turn the head of the game to the detected person"""
	var k := key(g)
	if paused(g) > 0.0:
		return
	var bd := boxes(0)
	var t := _target(bd["b"])
	var cam: Camera3D = main.cams[0]
	var vs := Vector2(main.vps[0].size)
	var vf: float = deg_to_rad(cam.fov)
	var hf: float = 2.0 * atan(tan(vf / 2.0) * vs.x / maxf(1.0, vs.y))
	if not t.is_empty():
		var ex: float = float(t[0]) + float(t[2]) / 2.0 - 0.5
		var ey: float = float(t[1]) + float(t[3]) * 0.4 - 0.5          # the chest, not the feet
		if str(bd["src"]) == "mw":
			# MoveEye's boxes come late (picture → MoveEye → back): one step per new box, then let the picture settle
			if main.mw_det_t != _det_seen and now() >= float(_goal.get(k, [0, 0, 0.0])[2]):
				_det_seen = main.mw_det_t
				_goal[k] = [game.guard_yaw - ex * hf * 0.8, game.guard_tilt - ey * vf * 0.8, now() + 0.6]
		else:
			_goal[k] = [game.guard_yaw - ex * hf, game.guard_tilt - ey * vf, now()]
	if _goal.has(k):
		var gl: Array = _goal[k]
		var f: float = clampf(dt * 5.0, 0.0, 1.0)
		game.guard_yaw = wrapf(lerp_angle(game.guard_yaw, float(gl[0]), f), -PI, PI)
		game.guard_tilt = clampf(lerpf(game.guard_tilt, float(gl[1]), f), deg_to_rad(-40.0), deg_to_rad(15.0))
		_last[k] = [game.guard_yaw, game.guard_tilt]
		if t.is_empty() and now() > float(gl[2]) + 1.0:
			_goal.erase(k)                                     # lost: stay where we are


func _auto(g) -> void:
	"""the autopilot fires when a sure box is in the hit circle for HOLD seconds (shutter free, energy enough)"""
	var k := key(g)
	if paused(g) > 0.0 or shut.lock_left(g) > 0.0:
		since.erase(k)
		return
	if game.tools != null and game.tools.on() and game.tools.check(g, "shut") != "":
		since.erase(k)
		return
	var cam_i := _cam(g)
	var bd := boxes(cam_i)
	var near := false
	var kg = game.kig if game.kig != null and game.kig.active and g == null else null   # «MoveEye als KI-Wächter»: fair by the difficulty
	var still := true
	if kg != null:
		still = _head_still()
	for bx in bd["b"]:
		if bool(bx[4]) and _in_circle(bx, cam_i) >= 0.0 and (kg == null or (kg.big_enough(bx) and not _protected_box(bx, cam_i))):
			near = true
			break
	if kg != null and main.mw_det_t != _kg_det:            # KI-Wächter: count MoveEye's new pictures in a row with the target in the circle
		_kg_det = main.mw_det_t
		_kg_n = _kg_n + 1 if near else 0
	if not near:
		if kg != null and since.has(k) and now() - float(_near_t.get(k, 0.0)) < GAP:
			return                                         # KI-Wächter: MoveEye's boxes flicker (a picture without a box) - keep the time
		since.erase(k)
		return
	_near_t[k] = now()
	if not since.has(k):
		since[k] = now()
		return
	if now() - float(since[k]) < (kg.hold_s() if kg != null else HOLD):
		return
	if kg != null and (_kg_n < 2 or main.now() - main.mw_det_t > 0.8 or not still):
		return                                             # KI-Wächter: two fresh pictures agree - no shot on an old box (the head moves)
	since.erase(k)
	_kg_n = 0
	firing = true
	var r: Dictionary = shut.fire(g, AUTO_WHO)
	firing = false
	if bool(r.get("ok", false)) and bool(r.get("shutter", false)):
		auto_shots += 1
		if bool(r.get("hit", false)):
			auto_hits += 1


var _hd_rot := Vector3.ZERO
var _hd_t := 0.0


func _head_still() -> bool:
	"""KI-Wächter: the head has not turned for 0.3 s (MoveEye's boxes belong to a picture of before - no shot while it turns)"""
	if main.head == null:
		return true
	var r: Vector3 = main.head.global_rotation
	if (r - _hd_rot).length() > deg_to_rad(0.4):
		_hd_rot = r
		_hd_t = now()
	return now() - _hd_t >= 0.3


func _protected_box(bx: Array, cam_i: int) -> bool:
	"""KI-Wächter: the box belongs to a runner who is protected right now (just caught, at the start) - never aim at him"""
	for p in game.players:
		if p == null or p["role"] != "runner":
			continue
		if p["state"] == "play" and now() >= float(p.get("safe_until", 0.0)):
			continue
		var b: Array = shut.box_cam(p, cam_i)
		if b.is_empty():
			continue
		var ix: float = maxf(0.0, minf(float(bx[0]) + float(bx[2]), float(b[0]) + float(b[2])) - maxf(float(bx[0]), float(b[0])))
		var iy: float = maxf(0.0, minf(float(bx[1]) + float(bx[3]), float(b[1]) + float(b[3])) - maxf(float(bx[1]), float(b[1])))
		if ix * iy > 0.3 * minf(float(bx[2]) * float(bx[3]), float(b[2]) * float(b[3])):
			return true
	return false


func hold(g) -> float:
	var k := key(g)
	var hs: float = game.kig.hold_s() if game.kig != null and game.kig.active and g == null else HOLD
	return clampf((now() - float(since[k])) / hs, 0.0, 1.0) if since.has(k) else 0.0


# ---- for the pages and the report --------------------------------------------------------------------------------------
func info_for(g, with_boxes := false) -> Dictionary:
	var m := mode_of(g)
	var d := {"mode": m, "name": NAMES[m], "pause": snappedf(paused(g), 0.1), "used": used_round(), "hold": snappedf(hold(g), 0.1),
			"auto": [auto_shots, auto_hits], "modes": MODES}
	if g == null and game.kig != null and game.kig.active:
		d["kig_n"] = _kg_n                                  # KI-Wächter: fresh pictures in a row with the target in the circle
	if with_boxes and m != "off":
		var bd := boxes(_cam(g))
		d["src"] = bd["src"]
		d["box"] = bd["b"]
	return d


func report() -> Dictionary:
	return {"benutzt": used_round(), "arten": used.keys(), "wer": used_by.values(), "autopilot_schuesse": auto_shots, "autopilot_treffer": auto_hits}


func mark_results(results: Array) -> void:
	"""game.end_round: every line says that this round does not count"""
	var what := ", ".join(PackedStringArray(used.keys().map(func(x): return NAMES.get(x, x))))
	for r in results:
		r["ki"] = true
		r["info"] = str(r.get("info", "")) + " · 🤖 mit KI-Hilfe (%s) – zählt nicht für Rangliste und Abzeichen" % what
	game.news("🤖 Runde mit KI-Hilfe – sie zählt nicht für die Rangliste und gibt keine Abzeichen")


func from_phone(p: Dictionary, m: Dictionary) -> void:
	"""message {t: "ki", mode} of the guard page (game.gd)"""
	if p["role"] != "guard":
		return
	var r: Dictionary = cycle(p) if str(m.get("mode", "")) == "next" else set_mode(p, str(m.get("mode", "off")))
	if not bool(r.get("ok", false)):
		game._say(p, str(r.get("error", "")), 3.0)


func command(d: Dictionary) -> Dictionary:
	"""control «game_shut» {op: "ki", mode?: off|frame|aim|auto|next, slot?: guard (none / -1 = the guards at MoveEye),
	human?: true (the person steers: MoveEye 542), local_guard?: true (tests: play as guard at this PC)}"""
	if bool(d.get("local_guard", false)) and main.localplay != null:
		main.localplay.start("guard")
		return {"ok": true}
	var g = null
	if d.has("slot") and int(d["slot"]) >= 0 and int(d["slot"]) < game.players.size():
		g = game.players[int(d["slot"])]
	elif shut.human_mode() == "guard":
		g = game.guard_player()
	if bool(d.get("human", false)):
		human(g)
		return {"ok": true, "ki": info_for(g)}
	if d.has("mode"):
		var md := str(d["mode"])
		var who := str(d.get("who", "")).left(30)
		return cycle(g) if md == "next" else set_mode(g, md, who)
	var r := {"ok": true, "ki": info_for(g, true), "report": report()}
	return r


# ---- PC: key K = the next help (game at the PC as guard, «Kopf steuern» in «Team gegen MoveEye») ------------------------
func pc_shooter() -> Array:
	"""[true, g] when a person at this PC holds the shutter"""
	var hm: String = shut.human_mode()
	var lp = main.localplay
	if hm == "guard" and lp != null and lp.active and lp.p != null and str(lp.role) == "guard":
		return [true, lp.p]
	if hm == "mw" and main.headpad != null and main.headpad.visible:
		return [true, null]
	return [false, null]


func _ready() -> void:
	var kc := KeyK.new()                                   # last child of the root: gets the keys before localplay.gd takes them
	kc.ki = self
	get_tree().root.add_child.call_deferred(kc)


func key_k() -> bool:
	var s := pc_shooter()
	if bool(s[0]):
		cycle(s[1])
		return true
	return false


class KeyK extends Node:
	var ki

	func _input(ev: InputEvent) -> void:
		if ev is InputEventKey and ev.pressed and not ev.echo and ev.keycode == KEY_K and ki != null and ki.key_k():
			get_viewport().set_input_as_handled()


# ---- the guard page of the phone (game.gd PAGE: added before </body>) --------------------------------------------------
const PHONE_JS := r"""<script>
(function () {   // KI-Hilfe (gamekihilfe.gd): the button «KI» and MoveEye's boxes on the picture of the guard
  const KN = {off: "KI aus", frame: "KI-Rahmen", aim: "KI zielt", auto: "KI-Autopilot"};
  const css = document.createElement("style");
  css.textContent = "#kib{position:fixed;right:max(12px,env(safe-area-inset-right));top:calc(max(8px,env(safe-area-inset-top)) + 200px);z-index:3;background:#0a0e14cc;border:1px solid #1f2b3a;color:#e6edf3;border-radius:999px;padding:7px 12px;font:600 13px system-ui,sans-serif;touch-action:manipulation}"
    + "#kib.on{border-color:#34c759;color:#9ff0b4}#kib.pz{border-color:#ffd166;color:#ffd166}#kib[hidden]{display:none}#kic{position:fixed;inset:0;width:100%;height:100%;pointer-events:none}";
  document.head.appendChild(css);
  const B = document.createElement("button"), C = document.createElement("canvas"), V = document.getElementById("v");
  B.id = "kib"; B.type = "button"; B.hidden = true; C.id = "kic"; document.body.appendChild(B); if (V) V.after(C);
  B.title = "KI-Hilfe für diese Runde: aus → KI-Rahmen → KI zielt → KI-Autopilot. Mit KI-Hilfe zählt die Runde nicht für die Rangliste.";
  B.addEventListener("pointerdown", e => { e.preventDefault(); e.stopPropagation(); send({t: "ki", mode: "next"}); });
  let sig = "";
  function paint() {
    const m = (typeof st !== "undefined" && st) || {}, S = m.shut || {}, K = S.ki || {};
    const on = role === "guard" && !!S.on && (m.rs === "play" || m.rs === "countdown"), md = K.mode || "off";
    B.hidden = !on;
    const W = innerWidth, H = innerHeight, dp = devicePixelRatio || 1;
    if (C.width !== Math.round(W * dp) || C.height !== Math.round(H * dp)) { C.width = Math.round(W * dp); C.height = Math.round(H * dp); }
    const x = C.getContext("2d"); x.setTransform(dp, 0, 0, dp, 0, 0); x.clearRect(0, 0, W, H);
    if (!on) return;
    let tx = "🤖 " + (KN[md] || md);
    if (md === "auto" && K.pause > 0) tx += " · Pause " + Math.ceil(K.pause) + " s";
    if (md !== "off" && K.src === "sim") tx += " · Sim-KI";
    if (tx !== sig) { sig = tx; B.textContent = tx; }
    B.classList.toggle("on", md !== "off"); B.classList.toggle("pz", md === "auto" && K.pause > 0);
    if (md === "off" || !K.box || !V) return;
    const nw = V.naturalWidth || 16, nh = V.naturalHeight || 9, k = Math.min(W / nw, H / nh), pw = nw * k, ph = nh * k, ox = (W - pw) / 2, oy = (H - ph) / 2;
    K.box.forEach(b => {
      const bx = ox + b[0] * pw, by = oy + b[1] * ph, bw = b[2] * pw, bh = b[3] * ph;
      x.lineWidth = 3; x.strokeStyle = "rgba(0,0,0,.55)"; x.setLineDash(b[4] ? [] : [9, 7]); x.strokeRect(bx - 1, by - 1, bw + 2, bh + 2);
      x.lineWidth = 2.5; x.strokeStyle = "#33ff66"; x.strokeRect(bx, by, bw, bh);
      if (b[4] && md === "auto" && K.hold > 0) { x.setLineDash([]); x.fillStyle = "#ffd166"; x.fillRect(bx, by + bh + 4, bw * Math.min(1, K.hold), 4); }
    });
    x.setLineDash([]);
  }
  setInterval(paint, 120);
  addEventListener("keydown", e => { if (e.code === "KeyK" && e.target.tagName !== "INPUT" && !B.hidden) send({t: "ki", mode: "next"}); });
})();
</script>"""
