extends Node
## Paket A5 «Zu zweit, Handy-Begleiter, Familien-Bestenliste» (Bergtal-Abenteuer, Daniel 31.10.2026).
##
## Spielart (Schritt «Schwierigkeit & Ziel», Gruppe «Mitspieler»), vor dem Start wählbar:
##   allein      wie bisher (die Fensteransicht fliegt mit der Tour)
##   gemeinsam   zwei Wanderer, jeder mit eigenem Controller: beide gehen mit der Tour mit und dürfen sich bis 110 m von
##               der Gruppe entfernen (umschauen, voraus spähen); lässt man den Stick los, kommt man zur Gruppe zurück
##   rollen      Spieler 1 wandert, Spieler 2 bedient MoveEye (Kopf, Licht, Foto - die gewohnte Belegung der Rolle
##               «Wächter», padmap.gd) und sieht die Karte; der Bildschirm ist immer geteilt
##   wettrennen  vor jeder Etappe ein Rennen zu einem Fähnchen (bis 300 m den Weg entlang, Abkürzungen erlaubt); wer zuerst
##               dort ist, bekommt einen Etappensieg (zählt in der Familien-Bestenliste); danach geht die Tour weiter
## Controller: die Belegung bleibt die von padmap.gd (Modus «runner» wie beim Spiel am PC): rechter Stick = gehen,
## linker Stick = umschauen, R2 = rennen, Start = Menü (Fragen unterwegs beantworten). Ohne zweiten Controller:
## Spieler 1 W A S D (Q / E umschauen, Shift rennen), Spieler 2 I J K L (U / O umschauen, H rennen).
##
## Bildschirm wechselnd: zwei Ansichten nebeneinander (schmaler Platz: übereinander) rechts der Abenteuer-Spalte; sind
## beide näher als 18 m beieinander, eine gemeinsame Ansicht (wieder geteilt ab 26 m). Die grosse Fensteransicht wird
## solange nicht gezeichnet (main._check_active).
## Leistung: zwei Ansichten = die Welt zweimal zeichnen. Normal: volle Auflösung, Sichtweite 1500 m. Lite: halbe Auflösung
## (stretch_shrink 2), Sichtweite 280 m, keine Schatten der Figuren, MSAA aus und im geteilten Bild abwechselnd je eine
## Ansicht pro Bild (jede mit halber Bildrate). Gemessen wird relativ: {"action": "abenteuer", "do": "zweit", "k": "fps"}.
##
## Handy als Begleiter: öffnet die bestehende Handy-Spielseite (game.gd, gleiche Adresse und QR-Code wie das Spiel; auf der
## MoveEye-Seite «Simulator» erscheint der QR-Code von selbst). Wer beitritt, schaut zu (Rolle «watch»: das Bild der
## Kopfkamera, also was MoveEye sieht) und bekommt dazu die Landeskarte mit Weg, Wanderern, Lager, MoveEye und Tipps:
## Karte antippen = 📍 Tipp (steht als gelbe Stange im Tal), Zurufe, Rat zur aktuellen Frage, 📸 Foto für die Bestenliste.
## Am MoveEye-Programm (quelle/) ändert sich dafür nichts.
## Familien-Bestenliste: abenteuer_bestenliste.gd (am Morgen jedes Kapitels).
## Spielstand: R["a5_zweit"] = {mode, names, wins}; W["a5_spielart"].
## Steuerbefehl: {"action": "abenteuer", "do": "zweit", "k": state | mode (value) | names (value) | phone (value) | drive
##                (p, x, y, secs, run) | place (p, x, z) | pin (x, z) | foto | lite (value) | fps | board | reset_board}

const T = preload("res://scripts/i18n.gd")
const Bt = preload("res://scripts/bergtal.gd")
const Board = preload("res://scripts/abenteuer_bestenliste.gd")
const Karte = preload("res://scripts/bergtal_abenteuer_karte.gd")
const Quality = preload("res://scripts/quality.gd")
const Qr = preload("res://scripts/qr.gd")

const MODES := ["allein", "gemeinsam", "rollen", "wettrennen"]
const STEPS := ["Kapitel", "Stimmung", "Schwierigkeit & Ziel", "Rucksack", "Unterwegs", "Nachtlager", "Nacht", "Morgen"]   # = bergtal_abenteuer.STEPS
const LEASH := 110.0                 # m: so weit darf man sich von der Gruppe entfernen
const NEAR_IN := 18.0                # m: näher = gemeinsame Ansicht
const NEAR_OUT := 26.0               # m: weiter = wieder geteilt
const RACE_M := 300.0                # m: längstens so weit den Weg entlang geht ein Rennen
const COLS := [Color(0.23, 0.55, 1.0), Color(1.0, 0.62, 0.26)]
const HELPER_LAYER := 128            # main.HELPER_LAYER: die Kameras von MoveEye sehen die Figuren nicht

var ab                                # bergtal_abenteuer.gd
var main
var mode := "allein"
var names := ["Spieler 1", "Spieler 2"]
var phone := false
var force_lite := false               # tests: the Lite path without the Lite renderer
var on := false                       # the own views are drawn (instead of the big window view)
var merged := false
var pl: Array = []                    # per player: pos (valley), off, yaw, pitch, idle, dev, node, vp, cam, box, chip
var race := {}
var wins := {"1": 0, "2": 0}
var pins: Array = []                  # [{"x", "z", "by", "node"}]
var _test: Array = [{}, {}]
var _layer: CanvasLayer
var _root: Control
var _line: ColorRect
var _role_box: PanelContainer
var _role_head: TextureRect
var _role_karte
var _role_lab: Label
var _msg: Label
var _msg_t := 0.0
var _run_id := ""
var _we_opened := false
var _saved_roles = null
var _ph_t := 0.0
var _vis_t := 0.0
var _pend_sig := ""
var _flag: Node3D
var _fps: Array = []                  # [time, fps] the last seconds (measurement)
var _frame := 0


func setup(a) -> void:
	ab = a
	main = a.main
	var d := Board.load_all()
	names = [str(d["names"][0]), str(d["names"][1])]
	mode = str(ab.W.get("a5_spielart", "allein"))
	if not mode in MODES:
		mode = "allein"
	for i in range(2):
		pl.append({"pos": Vector2.ZERO, "off": Vector2(-1.6 if i == 0 else 1.6, 2.0), "yaw": 0.0, "pitch": -0.12, "idle": 0.0, "dev": -1,
				"node": null, "vp": null, "cam": null, "box": null, "chip": null, "far_said": 0.0})


func _lite() -> bool:
	return force_lite or Quality.lite()


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


# =======================================================================================================================
# hooks for the others (bergtal_abenteuer.gd, main.gd, padmap.gd, game.gd)
# =======================================================================================================================
func views_on() -> bool:
	return on


func head_fps() -> float:
	"""main._wanted_fps: the head camera for player 2 (Rollen) and for the phones (MoveEye pictures)"""
	if on and mode == "rollen" and not merged:
		return 4.0 if _lite() else 8.0
	if phone and _watchers() > 0:
		return 2.0 if _lite() else 4.0
	return 0.0


func pad_devs() -> Array:
	"""padmap.gd: these controllers walk the figures (the window does not get their sticks)"""
	if not on or (main.padmap != null and main.padmap.menu):
		return []
	var L: Array = []
	for i in range(2 if mode != "rollen" else 1):
		if int(pl[i]["dev"]) >= 0:
			L.append(int(pl[i]["dev"]))
	return L


func holds_leg() -> bool:
	"""bergtal_abenteuer._tick_leg: the leg waits while the race runs"""
	return not race.is_empty()


func on_leg(lg: Dictionary) -> void:
	"""bergtal_abenteuer._start_leg: a new leg - in «Wettrennen» first a race"""
	if mode != "wettrennen" or ab.fast or ab.replaying or lg.is_empty() or ab.bt() == null:
		return
	var pts: Array = lg["pts"]
	var total := 0.0
	for i in range(pts.size() - 1):
		total += (pts[i] as Vector2).distance_to(pts[i + 1])
	if total < 40.0:
		return
	var tgt: Vector2 = ab._along(pts, minf(1.0, RACE_M / total))
	var st: Vector2 = pts[0]
	var dir := (tgt - st).normalized()
	var side := Vector2(-dir.y, dir.x)
	var yaw := atan2(-dir.x, -dir.y)
	for i in range(2):
		pl[i]["pos"] = st + side * (1.5 if i == 0 else -1.5)
		pl[i]["yaw"] = yaw
	race = {"target": tgt, "t0": now(), "arr": [-1.0, -1.0], "first": -1, "dist": st.distance_to(tgt), "leg": int(lg.get("i", 0))}
	_make_flag(tgt)
	_say(T.t("🏁 Wettrennen: Wer ist zuerst beim Fähnchen? (%d m, Abkürzungen erlaubt)") % int(race["dist"]))


func on_morning() -> void:
	"""bergtal_abenteuer._morning: the family board gets this chapter"""
	var who: Array = [names[0]] if mode == "allein" else [names[0], names[1]]
	Board.record_run(who, ab, wins)
	_keep()


func on_a1_fotos(fs: Array) -> void:
	"""A1 (abenteuer_moveeye.gd _tag_done): die Aufnahmen der Wildkamera am Tag kommen auch auf die Bestenliste"""
	if Board.add_a1_fotos(fs, str(names[0])) > 0:
		ab._changed()


func phone_msg(p: Dictionary, t: String, m: Dictionary) -> bool:
	"""game._message: what the companion phone sends ({"t": "abz", "k": pin | say | rat | foto})"""
	if t != "abz":
		return false
	var nm := str(p.get("name", "Handy"))
	match str(m.get("k", "")):
		"pin":
			add_pin(float(m.get("x", 0.0)), float(m.get("z", 0.0)), nm)
		"say":
			var v := str(m.get("v", ""))
			var tx: String = {"links": "Links!", "rechts": "Rechts!", "pause": "Macht eine Pause!", "super": "Super gemacht!", "achtung": "Achtung, pass auf!", "wasser": "Wasser auffüllen!"}.get(v, "")
			if tx != "":
				_say("📱 %s: %s" % [nm, T.t(tx)])
		"rat":
			var pe: Dictionary = ab.R.get("pending", {})
			for o in pe.get("options", []):
				if str(o[0]) == str(m.get("v", "")):
					_say("📱 %s %s «%s»" % [nm, T.t("rät:"), str(o[1]).get_slice("\n", 0)])
		"foto":
			var e := take_foto(nm, "handy")
			_send(p, {"t": "abzinfo", "txt": (T.t("📸 Foto gespeichert: %d Punkte") % int(e["punkte"])) if not e.is_empty() else T.t("Noch kein MoveEye-Bild")})
	return true


# =======================================================================================================================
# choices
# =======================================================================================================================
func set_mode(v: String) -> void:
	if not v in MODES:
		return
	mode = v
	ab.W["a5_spielart"] = v
	_keep()
	ab._changed()


func set_names(a: String, b: String) -> void:
	names = [a.strip_edges().left(20) if a.strip_edges() != "" else "Spieler 1", b.strip_edges().left(20) if b.strip_edges() != "" else "Spieler 2"]
	var d := Board.load_all()
	d["names"] = names.duplicate()
	Board.save_all(d)
	_keep()


func _keep() -> void:
	if not ab.R.is_empty():
		ab.R["a5_zweit"] = {"mode": mode, "names": names.duplicate(), "wins": wins.duplicate()}


func set_phone(v: bool) -> void:
	var g = main.game
	if g == null:
		return
	if v and not g.open:
		if g.busy():
			_say(T.t("Das Spiel läuft gerade - das Handy kann erst danach helfen."))
			return
		g.set_open(true)
		_we_opened = g.open
		if g.open:
			g.set_bots.call_deferred(0)                         # no computer players in the valley
	elif not v and _we_opened and g.open and g.round_state == "lobby":
		g.set_open(false)
		_we_opened = false
	phone = v and g.open
	ab._changed()


func _watchers() -> int:
	var g = main.game
	if g == null or not g.open:
		return 0
	var n := 0
	for p in g.players:
		if p != null and p["sock"] != null and str(p["role"]) == "watch":
			n += 1
	return n


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _want_on() -> bool:
	if mode == "allein" or ab.R.is_empty() or ab.bt() == null or main.scene != "bergtal":
		return false
	return int(ab.step) == 4 or (int(ab.step) == 5 and not ab.visible)


func _process(dt: float) -> void:
	_frame += 1
	if str(ab.R.get("id", "")) != _run_id:                  # a new run: new races, no old tips
		_run_id = str(ab.R.get("id", ""))
		wins = {"1": 0, "2": 0}
		race = {}
		_free_flag()
		for p in pins:
			if is_instance_valid(p["node"]):
				p["node"].queue_free()
		pins.clear()
		var a5: Dictionary = ab.R.get("a5_zweit", {})
		if a5.has("mode") and str(a5["mode"]) in MODES:      # (a replayed situation)
			mode = str(a5["mode"])
		_keep()
	_ph_t -= dt
	if _ph_t <= 0.0:
		_ph_t = 0.5
		_phone_tick()
	_pending_tick()
	_pins_tick()
	var want := _want_on()
	if want != on:
		_set_on(want)
	_figures_show(mode != "allein" and not ab.R.is_empty() and int(ab.step) in [4, 5] and ab.bt() != null)
	if not on:
		return
	_assign_devs()
	var b = ab.bt()
	var anchor: Vector2 = ab.R.get("pos", Vector2.ZERO)
	var n := 1 if mode == "rollen" else 2
	var frozen: bool = (main.padmap != null and main.padmap.menu) or (not race.is_empty() and now() - float(race["t0"]) < 3.0)
	for i in range(n):
		_walk(i, dt, anchor, frozen)
	if not race.is_empty():
		_race_tick()
	var d: float = (pl[0]["pos"] as Vector2).distance_to(pl[1]["pos"]) if n == 2 else 999.0
	var m := merged
	if mode == "rollen":
		m = false
	elif merged and d > NEAR_OUT:
		m = false
	elif not merged and d < NEAR_IN:
		m = true
	if m != merged:
		merged = m
		_say(T.t("Zusammen - eine Ansicht") if merged else T.t("Getrennt - geteilter Bildschirm"))
	for i in range(n):
		_place_fig(i, b)
	_cams(b, dt)
	_layout()
	_hud()
	_visited(dt)
	_measure()


func _set_on(v: bool) -> void:
	on = v
	if v:
		_build()
		var anchor: Vector2 = ab.R.get("pos", Vector2.ZERO)
		for i in range(2):
			if race.is_empty():
				pl[i]["pos"] = anchor + (pl[i]["off"] as Vector2)
		if mode == "rollen" and main.padmap != null:
			_saved_roles = main.padmap.roles.duplicate(true)
	else:
		if _saved_roles != null and main.padmap != null:
			main.padmap.roles = _saved_roles
			_saved_roles = null
		race = {}
		_free_flag()
	if _layer != null:
		_layer.visible = v
	for i in range(2):
		var vp: SubViewport = pl[i]["vp"]
		if vp != null:
			vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS if v else SubViewport.UPDATE_DISABLED
			(pl[i]["cam"] as Camera3D).current = v
	main.get_viewport().disable_3d = v or not main.win_open
	_fps.clear()


func _assign_devs() -> void:
	var pm = main.padmap
	var devs: Array = pm.devices().duplicate() if pm != null else []
	if pm != null:
		devs.sort_custom(func(a, b2): return pm.number(a) < pm.number(b2))
	pl[0]["dev"] = devs[0] if devs.size() >= 1 else -1
	pl[1]["dev"] = devs[1] if devs.size() >= 2 else -1
	if mode == "rollen" and pm != null and int(pl[1]["dev"]) >= 0:
		var d2 := int(pl[1]["dev"])
		if not (pm.roles.size() == 1 and pm.roles.has(d2) and str(pm.roles[d2]["role"]) == "guard"):
			pm.roles = {}
			pm.set_role(d2, "guard")                       # the usual mapping of the role «Wächter»: head, light, photo …


func _input_of(i: int) -> Dictionary:
	var mv := Vector2.ZERO
	var lk := Vector2.ZERO
	var run := false
	var d := int(pl[i]["dev"])
	var pm = main.padmap
	if d >= 0 and pm != null:
		mv = pm.move([d])
		lk = pm.look([d])
		run = pm.trig("r2", [d]) > 0.35
		if pm.hit("start", [d]):
			pm.set_menu(true)                              # Start = the menu (answer the questions on the way)
	if d < 0 and not _typing():
		var K: Array = [[KEY_W, KEY_S, KEY_A, KEY_D, KEY_Q, KEY_E, KEY_SHIFT], [KEY_I, KEY_K, KEY_J, KEY_L, KEY_U, KEY_O, KEY_H]][i]
		var kv := Vector2(float(Input.is_physical_key_pressed(K[3])) - float(Input.is_physical_key_pressed(K[2])),
				float(Input.is_physical_key_pressed(K[1])) - float(Input.is_physical_key_pressed(K[0])))
		if kv != Vector2.ZERO:
			mv = kv.normalized()
		var kl := float(Input.is_physical_key_pressed(K[5])) - float(Input.is_physical_key_pressed(K[4]))
		if kl != 0.0:
			lk.x = kl
		run = run or Input.is_physical_key_pressed(K[6])
	var tt: Dictionary = _test[i]
	if not tt.is_empty() and now() < float(tt["until"]):
		mv = tt["v"]
		run = bool(tt.get("run", false))
	return {"mv": mv, "lk": lk, "run": run}


func _typing() -> bool:
	var f: Control = main.get_viewport().gui_get_focus_owner()
	return f is LineEdit or f is TextEdit


func _walk(i: int, dt: float, anchor: Vector2, frozen: bool) -> void:
	var p: Dictionary = pl[i]
	var inp := _input_of(i)
	var mv: Vector2 = inp["mv"]
	var lk: Vector2 = inp["lk"]
	if frozen:
		mv = Vector2.ZERO
		lk = Vector2.ZERO
	p["yaw"] = wrapf(float(p["yaw"]) - lk.x * 2.2 * dt, -PI, PI)
	p["pitch"] = clampf(float(p["pitch"]) - lk.y * 1.2 * dt, -0.6, 0.35)
	var yaw: float = p["yaw"]
	var fw := Vector2(-sin(yaw), -cos(yaw))
	var rt := Vector2(cos(yaw), -sin(yaw))
	var racing := not race.is_empty()
	var sp: float = (7.0 if bool(inp["run"]) else 4.0) if racing else (5.5 if bool(inp["run"]) else 2.8)   # (game time: a bit faster than real)
	var step: Vector2 = (fw * -mv.y + rt * mv.x) * sp * dt
	if racing:
		p["pos"] = _clamp_valley((p["pos"] as Vector2) + step)
		return
	var off: Vector2 = p["off"]
	if mv != Vector2.ZERO:
		p["idle"] = 0.0
		off += step
	else:
		p["idle"] = float(p["idle"]) + dt
		var slot := Vector2(-1.6 if i == 0 else 1.6, 2.0)
		if float(p["idle"]) > 6.0 and off.distance_to(slot) > 1.0:   # let go: back to the group
			off = off.move_toward(slot, 2.5 * dt)
	if off.length() > LEASH:
		off = off.normalized() * LEASH
		if now() - float(p["far_said"]) > 8.0:
			p["far_said"] = now()
			_say(T.t("%s: nicht weiter weg von der Gruppe (%d m)") % [names[i], int(LEASH)])
	p["off"] = off
	p["pos"] = _clamp_valley(anchor + off)


func _clamp_valley(q: Vector2) -> Vector2:
	return Vector2(clampf(q.x, Bt.LO + 30.0, -Bt.LO - 30.0), clampf(q.y, Bt.LO + 30.0, -Bt.LO - 30.0))


func _race_tick() -> void:
	var t := now()
	var tgt: Vector2 = race["target"]
	var arr: Array = race["arr"]
	for i in range(2):
		if float(arr[i]) < 0.0 and (pl[i]["pos"] as Vector2).distance_to(tgt) < 6.0:
			arr[i] = t - float(race["t0"])
			if int(race["first"]) < 0:
				race["first"] = i
				wins[str(i + 1)] = int(wins.get(str(i + 1), 0)) + 1
				_keep()
				_say(T.t("🏁 %s ist zuerst beim Fähnchen! (%d s)") % [names[i], int(arr[i])])
				ab._diary("a5", T.t("Etappensieg"), T.t("%s gewinnt das Rennen zur Etappe.") % names[i])
				if main.padmap != null and int(pl[i]["dev"]) >= 0:
					main.padmap.rumble("catch", [int(pl[i]["dev"])])
	var first := int(race["first"])
	var done := float(arr[0]) >= 0.0 and float(arr[1]) >= 0.0
	if first >= 0 and t - float(race["t0"]) - float(arr[first]) > 20.0:
		done = true                                          # the other one is carried along after 20 s
	if t - float(race["t0"]) > 180.0:
		done = true
		if first < 0:
			_say(T.t("🏁 Keiner war beim Fähnchen - die Tour geht weiter."))
	if done:
		race = {}
		_free_flag()
		for i in range(2):
			pl[i]["off"] = Vector2(-1.6 if i == 0 else 1.6, 2.0)   # together on with the group
			pl[i]["idle"] = 0.0


# =======================================================================================================================
# the two views
# =======================================================================================================================
func _build() -> void:
	if _layer != null:
		return
	_layer = CanvasLayer.new()
	_layer.layer = -1                                       # under the panels of the window
	main.add_child(_layer)
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_root)
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.04, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(bg)
	for i in range(2):
		var box := SubViewportContainer.new()
		box.stretch = true
		box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_root.add_child(box)
		var vp := SubViewport.new()
		vp.handle_input_locally = false
		vp.gui_disable_input = true
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		vp.msaa_3d = Viewport.MSAA_DISABLED
		vp.positional_shadow_atlas_size = 1024
		box.add_child(vp)
		var cam := Camera3D.new()
		cam.fov = 70.0
		cam.near = 0.1
		cam.cull_mask = 1 | HELPER_LAYER
		vp.add_child(cam)
		var chip := Label.new()
		chip.add_theme_font_size_override("font_size", 15)
		chip.add_theme_color_override("font_color", Color.WHITE)
		chip.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
		chip.add_theme_constant_override("outline_size", 6)
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.03, 0.05, 0.08, 0.72)
		sb.border_color = COLS[i]
		sb.border_width_left = 4
		sb.set_corner_radius_all(8)
		sb.set_content_margin_all(6)
		chip.add_theme_stylebox_override("normal", sb)
		_root.add_child(chip)
		pl[i]["box"] = box
		pl[i]["vp"] = vp
		pl[i]["cam"] = cam
		pl[i]["chip"] = chip
	# «Rollen»: player 2 has MoveEye and the map instead of a second 3D view
	_role_box = PanelContainer.new()
	var sb2 := StyleBoxFlat.new()
	sb2.bg_color = Color(0.06, 0.075, 0.095, 0.97)
	sb2.border_color = COLS[1]
	sb2.border_width_left = 3
	sb2.set_content_margin_all(10)
	_role_box.add_theme_stylebox_override("panel", sb2)
	_role_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_role_box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	_role_box.add_child(v)
	_role_lab = Label.new()
	_role_lab.add_theme_font_size_override("font_size", 15)
	_role_lab.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(_role_lab)
	_role_head = TextureRect.new()
	_role_head.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_role_head.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_role_head.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_role_head.custom_minimum_size = Vector2(160, 90)
	v.add_child(_role_head)
	_role_karte = Karte.new()
	_role_karte.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_role_karte.custom_minimum_size = Vector2(160, 160)
	_role_karte.draw.connect(_draw_role_extra)
	v.add_child(_role_karte)
	_line = ColorRect.new()
	_line.color = Color(0.02, 0.03, 0.04)
	_line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_line)
	_msg = Label.new()
	_msg.add_theme_font_size_override("font_size", 18)
	_msg.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_msg.add_theme_constant_override("outline_size", 7)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_msg)


func _area() -> Rect2:
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	var x0 := 0.0
	if ab.visible and int(ab.step) in [4, 6]:
		x0 = ab.position.x + ab.size.x + 8.0
	return Rect2(Vector2(x0, 0), Vector2(maxf(200.0, vs.x - x0), vs.y))


func _layout() -> void:
	var a := _area()
	var lite := _lite()
	var b0: SubViewportContainer = pl[0]["box"]
	var b1: SubViewportContainer = pl[1]["box"]
	var vp0: SubViewport = pl[0]["vp"]
	var vp1: SubViewport = pl[1]["vp"]
	for bx in [b0, b1]:
		if bx.stretch_shrink != (2 if lite else 1):
			bx.stretch_shrink = 2 if lite else 1
	var side := a.size.x / a.size.y >= 1.25
	var r0 := a
	var r1 := Rect2()
	if not merged:
		if side:
			r0 = Rect2(a.position, Vector2(a.size.x / 2.0 - 2.0, a.size.y))
			r1 = Rect2(a.position + Vector2(a.size.x / 2.0 + 2.0, 0), Vector2(a.size.x / 2.0 - 2.0, a.size.y))
		else:
			r0 = Rect2(a.position, Vector2(a.size.x, a.size.y / 2.0 - 2.0))
			r1 = Rect2(a.position + Vector2(0, a.size.y / 2.0 + 2.0), Vector2(a.size.x, a.size.y / 2.0 - 2.0))
	b0.position = r0.position
	b0.size = r0.size
	var second_3d := not merged and mode != "rollen"
	b1.visible = second_3d
	if second_3d:
		b1.position = r1.position
		b1.size = r1.size
	_role_box.visible = mode == "rollen"
	if mode == "rollen":
		_role_box.position = r1.position
		_role_box.size = r1.size
	_line.visible = not merged
	_line.position = (r0.position + Vector2(r0.size.x, 0)) if side else (r0.position + Vector2(0, r0.size.y))
	_line.size = Vector2(4, a.size.y) if side else Vector2(a.size.x, 4)
	# what is drawn: Lite and split = every view every second frame
	if second_3d and lite:
		vp0.render_target_update_mode = SubViewport.UPDATE_ONCE if _frame % 2 == 0 else SubViewport.UPDATE_DISABLED
		vp1.render_target_update_mode = SubViewport.UPDATE_ONCE if _frame % 2 == 1 else SubViewport.UPDATE_DISABLED
	else:
		vp0.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		vp1.render_target_update_mode = SubViewport.UPDATE_ALWAYS if second_3d else SubViewport.UPDATE_DISABLED
	for i in range(2):
		var cam: Camera3D = pl[i]["cam"]
		cam.far = 280.0 if lite else 1500.0
		vp0.msaa_3d = Viewport.MSAA_DISABLED if lite else main.get_viewport().msaa_3d
		vp1.msaa_3d = vp0.msaa_3d
		vp0.positional_shadow_atlas_size = 0 if lite else 1024
		vp1.positional_shadow_atlas_size = vp0.positional_shadow_atlas_size
	var c0: Label = pl[0]["chip"]
	var c1: Label = pl[1]["chip"]
	c0.position = r0.position + Vector2(10, 10)
	c1.visible = second_3d or mode == "rollen"
	c1.position = (r1.position + Vector2(10, 10)) if mode != "rollen" else Vector2(-1000, -1000)
	_msg.position = Vector2(a.position.x, a.size.y - 64.0)
	_msg.size = Vector2(a.size.x, 30)


func _cam_xf(b, i: int) -> Transform3D:
	var p: Dictionary = pl[i]
	var q: Vector2 = p["pos"]
	var wp: Vector3 = b.WG(q.x, q.y, 1.6)
	var wy: float = b.wrot(float(p["yaw"]))
	var fw := Vector3(-sin(wy), 0.0, -cos(wy))
	var eye := wp - fw * 5.5 + Vector3(0, 1.9, 0)
	eye.y = maxf(eye.y, main.ground_y(eye.x, eye.z) + 1.2)
	return Transform3D(Basis(), eye).looking_at(wp + fw * 6.0 + Vector3(0, float(p["pitch"]) * 6.0, 0), Vector3.UP)


func _cams(b, dt: float) -> void:
	var k := clampf(dt * 6.0, 0.0, 1.0)
	var c0: Camera3D = pl[0]["cam"]
	var c1: Camera3D = pl[1]["cam"]
	if merged:                                              # one view: behind the middle of both, far enough for both
		var q0: Vector2 = pl[0]["pos"]
		var q1: Vector2 = pl[1]["pos"]
		var mid := (q0 + q1) / 2.0
		var wm: Vector3 = b.WG(mid.x, mid.y, 1.6)
		var wy: float = b.wrot(float(pl[0]["yaw"]))
		var fw := Vector3(-sin(wy), 0.0, -cos(wy))
		var dd := q0.distance_to(q1)
		var eye := wm - fw * (6.5 + dd * 0.7) + Vector3(0, 2.6 + dd * 0.3, 0)
		eye.y = maxf(eye.y, main.ground_y(eye.x, eye.z) + 1.5)
		var xf := Transform3D(Basis(), eye).looking_at(wm + fw * 5.0, Vector3.UP)
		c0.global_transform = c0.global_transform.interpolate_with(xf, k) if c0.is_inside_tree() else xf
	else:
		c0.global_transform = c0.global_transform.interpolate_with(_cam_xf(b, 0), k)
		if mode != "rollen":
			c1.global_transform = c1.global_transform.interpolate_with(_cam_xf(b, 1), k)
	# the window camera stays with player 1 (visited places, cliff edges, the headlamp, the distance of the far things)
	if main.fly_tw != null:
		main.fly_tw.kill()
	main.view_cam.global_transform = c0.global_transform


func _hud() -> void:
	var b = ab.bt()
	for i in range(2):
		var c: Label = pl[i]["chip"]
		if c == null or not c.visible:
			continue
		var tx := "%d · %s" % [i + 1, names[i]]
		if merged:
			tx = "1 · %s  +  2 · %s" % [names[0], names[1]]
		if not race.is_empty():
			var tg: Vector2 = race["target"]
			var ii := 0 if merged else i
			tx += "   🏁 %d m %s" % [int((pl[ii]["pos"] as Vector2).distance_to(tg)), _arrow(ii, tg)]
			var cd := 3.0 - (now() - float(race["t0"]))
			if cd > 0.0:
				tx += "   %s %d" % [T.t("Start in"), int(ceil(cd))]
			var arr: Array = race["arr"]
			if float(arr[ii]) >= 0.0:
				tx += "  ✓"
		elif not pins.is_empty():
			var pn: Dictionary = pins[-1]
			var q := Vector2(float(pn["x"]), float(pn["z"]))
			tx += "   📍 %d m %s" % [int((pl[i]["pos"] as Vector2).distance_to(q)), _arrow(i, q)]
		var dv := int(pl[i]["dev"])
		tx += "   " + ("🎮" if dv >= 0 else ("⌨ W A S D" if i == 0 else "⌨ I J K L"))
		c.text = tx
	if mode == "rollen" and _role_box != null:
		var dv2 := int(pl[1]["dev"])
		_role_lab.text = "2 · %s - %s\n%s" % [names[1], T.t("MoveEye und Karte"), (T.t("🎮 Linker Stick = Kopf drehen · A Licht · X Foto (Belegung «Wächter»)") if dv2 >= 0 else T.t("Kein zweiter Controller: MoveEye mit der Maus im Bedienfeld bedienen"))]
		if main.vps.size() > 0:
			_role_head.texture = main.vps[0].get_texture()
		var k = ab.karte
		if k != null and _frame % 15 == 0:
			for f in ["mode", "pieces", "symbols", "route", "plan", "compass", "sun_az", "sun_el", "marks"]:
				_role_karte.set(f, k.get(f))
			_role_karte.me = pl[0]["pos"]                    # player 2 always sees where player 1 is
			_role_karte.queue_redraw()
	if _msg != null:
		_msg.visible = now() < _msg_t
	if b == null:
		return


func _draw_role_extra() -> void:
	"""on the map of player 2: the tips of the phone"""
	for p in pins:
		var px: Vector2 = _role_karte.to_px(Vector2(float(p["x"]), float(p["z"])))
		_role_karte.draw_circle(px, 5.0, Color("#ffd166"))
		_role_karte.draw_arc(px, 8.0, 0.0, TAU, 16, Color(0.2, 0.15, 0.05), 1.5)


func _arrow(i: int, q: Vector2) -> String:
	var to: Vector2 = q - (pl[i]["pos"] as Vector2)
	var a := wrapf(atan2(-to.x, -to.y) - float(pl[i]["yaw"]), -PI, PI)      # 0 = straight ahead, + = left
	var arrows := ["⬆", "↖", "⬅", "↙", "⬇", "↘", "➡", "↗"]
	return arrows[int(round(fposmod(a, TAU) / (TAU / 8.0))) % 8]


func _measure() -> void:
	var t := now()
	_fps.append([t, Engine.get_frames_per_second()])
	while not _fps.is_empty() and t - float(_fps[0][0]) > 6.0:
		_fps.pop_front()


func fps_avg() -> float:
	if _fps.is_empty():
		return Engine.get_frames_per_second()
	var s := 0.0
	for e in _fps:
		s += float(e[1])
	return s / _fps.size()


# =======================================================================================================================
# the figures, the flag, the tips
# =======================================================================================================================
func _fig(i: int) -> Node3D:
	var n := Node3D.new()
	var col: Color = COLS[i]
	var parts := [[CapsuleMesh.new(), Vector3(0, 0.85, 0), col], [SphereMesh.new(), Vector3(0, 1.78, 0), Color(0.93, 0.78, 0.66)],
			[BoxMesh.new(), Vector3(0, 1.15, 0.22), Color(0.42, 0.28, 0.16)]]
	(parts[0][0] as CapsuleMesh).radius = 0.27
	(parts[0][0] as CapsuleMesh).height = 1.6
	(parts[1][0] as SphereMesh).radius = 0.16
	(parts[1][0] as SphereMesh).height = 0.32
	(parts[2][0] as BoxMesh).size = Vector3(0.38, 0.5, 0.2)
	for e in parts:
		var mi := MeshInstance3D.new()
		mi.mesh = e[0]
		mi.position = e[1]
		var mt := StandardMaterial3D.new()
		mt.albedo_color = e[2]
		mt.roughness = 0.8
		mi.material_override = mt
		mi.layers = HELPER_LAYER
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if _lite() else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		n.add_child(mi)
	var lb := Label3D.new()
	lb.text = str(i + 1)
	lb.font_size = 72
	lb.pixel_size = 0.006
	lb.position = Vector3(0, 2.35, 0)
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.no_depth_test = true
	lb.modulate = col
	lb.outline_size = 12
	lb.layers = HELPER_LAYER
	n.add_child(lb)
	main.add_child(n)
	return n


func _figures_show(v: bool) -> void:
	for i in range(2):
		var n = pl[i]["node"]
		var want := v and (i == 0 or mode != "rollen")
		if want and n == null:
			pl[i]["node"] = _fig(i)
			n = pl[i]["node"]
			if not on:
				var anchor: Vector2 = ab.R.get("pos", Vector2.ZERO)
				pl[i]["pos"] = anchor + (pl[i]["off"] as Vector2)
		if n != null:
			n.visible = want
			if want and not on:                              # (the camp: they stand by the group)
				_place_fig(i, ab.bt())


func _place_fig(i: int, b) -> void:
	var n = pl[i]["node"]
	if n == null or b == null:
		return
	var q: Vector2 = pl[i]["pos"]
	n.global_position = b.WG(q.x, q.y, 0.0)
	n.rotation.y = b.wrot(float(pl[i]["yaw"]))


func _pole(col: Color, h: float, txt: String) -> Node3D:
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var cy := CylinderMesh.new()
	cy.top_radius = 0.12
	cy.bottom_radius = 0.12
	cy.height = h
	mi.mesh = cy
	mi.position.y = h / 2.0
	var mt := StandardMaterial3D.new()
	mt.albedo_color = col
	mt.emission_enabled = true
	mt.emission = col
	mt.emission_energy_multiplier = 1.6
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mt
	mi.layers = HELPER_LAYER
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	n.add_child(mi)
	var lb := Label3D.new()
	lb.text = txt
	lb.font_size = 64
	lb.pixel_size = 0.012
	lb.position.y = h + 1.0
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.no_depth_test = true
	lb.modulate = col
	lb.outline_size = 10
	lb.layers = HELPER_LAYER
	n.add_child(lb)
	main.add_child(n)
	return n


func _make_flag(q: Vector2) -> void:
	_free_flag()
	var b = ab.bt()
	if b == null:
		return
	_flag = _pole(Color(0.3, 0.85, 0.45), 9.0, "🏁")
	_flag.global_position = b.WG(q.x, q.y, 0.0)


func _free_flag() -> void:
	if _flag != null and is_instance_valid(_flag):
		_flag.queue_free()
	_flag = null


func add_pin(x: float, z: float, by: String) -> void:
	var q := _clamp_valley(Vector2(x, z))
	while pins.size() >= 5:
		var old: Dictionary = pins.pop_front()
		if is_instance_valid(old["node"]):
			old["node"].queue_free()
	var e := {"x": snappedf(q.x, 0.1), "z": snappedf(q.y, 0.1), "by": by, "node": null}
	var b = ab.bt()
	if b != null:
		e["node"] = _pole(Color("#ffd166"), 12.0, "📍 " + by)
		e["node"].global_position = b.WG(q.x, q.y, 0.0)
	pins.append(e)
	var from: Vector2 = ab.R.get("pos", Vector2.ZERO)
	_say("📍 %s: %s (%d m)" % [by, T.t("Schau dort!"), int(from.distance_to(q))])


func _pins_tick() -> void:
	"""a tip is reached (a player or the tour within 8 m): it goes"""
	if pins.is_empty():
		return
	var who: Array = [ab.R.get("pos", Vector2.INF)]
	if on:
		who.append(pl[0]["pos"])
		if mode != "rollen":
			who.append(pl[1]["pos"])
	for p in pins.duplicate():
		var q := Vector2(float(p["x"]), float(p["z"]))
		for w in who:
			if w is Vector2 and (w as Vector2).distance_to(q) < 8.0:
				if is_instance_valid(p["node"]):
					p["node"].queue_free()
				pins.erase(p)
				_say(T.t("📍 Tipp von %s erreicht") % str(p["by"]))
				break


func take_foto(wer: String, quelle: String) -> Dictionary:
	"""the picture MoveEye sees right now - for the family board (no A1 data: rated by Board.bild_wertung)"""
	if main.vps.is_empty():
		return {}
	var img: Image = (main.vps[0] as SubViewport).get_texture().get_image()
	if img == null or img.is_empty():
		return {}
	return Board.add_foto(img, wer, {"kapitel": int(ab.R.get("chapter", ab.W["chapter"])), "quelle": quelle})


func _visited(dt: float) -> void:
	"""like bergtal._tick_visited, for the two walkers (the window camera follows only player 1)"""
	_vis_t -= dt
	if _vis_t > 0.0:
		return
	_vis_t = 2.0
	var vis: Array = main.bt_visited
	for i in range(1 if mode == "rollen" else 2):
		var q: Vector2 = pl[i]["pos"]
		for p in Bt.all_places():
			if str(p[0]) in vis:
				continue
			if q.distance_to(Vector2(float(p[1]), float(p[2]))) < 70.0:
				vis.append(str(p[0]))
				main._settings_dirty = true
				_say("%s: %s %s" % [names[i], T.t("Neuer Ort entdeckt:"), T.t(str(p[0]))])


func _pending_tick() -> void:
	"""a question on the way: the controllers move to the panel (Start = menu); answered: back to walking"""
	var pe: Dictionary = ab.R.get("pending", {}) if not ab.R.is_empty() else {}
	var sig := str(pe.get("title", "")) + str(pe.get("text", "")).left(30) if not pe.is_empty() else ""
	if sig == _pend_sig:
		return
	_pend_sig = sig
	var pm = main.padmap
	if not on or pm == null or pm.devices().is_empty():
		return
	if sig != "" and ab.visible:
		pm.set_menu(true)
	elif sig == "" and pm.menu:
		pm.set_menu(false)


func _say(t: String) -> void:
	main.start_info = t
	if _msg != null:
		_msg.text = t
		_msg_t = now() + 4.0


# =======================================================================================================================
# the companion phone (game.gd page, role «watch»)
# =======================================================================================================================
var _map_b64 := ""


func _map64() -> String:
	if _map_b64 == "" and not Bt._hm.is_empty():
		var img: Image = Bt.map_texture().get_image()
		_map_b64 = Marshalls.raw_to_base64(img.save_jpg_to_buffer(0.72))
	return _map_b64


func _send(p: Dictionary, d: Dictionary) -> void:
	if p.get("sock") == null:
		return
	var w: WebSocketPeer = p["sock"]["ws"]
	if w.get_ready_state() == WebSocketPeer.STATE_OPEN and w.get_current_outbound_buffered_amount() < 900000:
		w.send_text(JSON.stringify(d))


func _pts(a) -> Array:
	var o: Array = []
	var n: int = a.size()
	var k := maxi(1, int(ceil(n / 80.0)))
	for i in range(0, n, k):
		o.append([int(a[i].x), int(a[i].y)])
	if n > 0 and (n - 1) % k != 0:
		o.append([int(a[n - 1].x), int(a[n - 1].y)])
	return o


func phone_state() -> Dictionary:
	var R: Dictionary = ab.R
	var b = ab.bt()
	var d := {"t": "abz", "on": not R.is_empty(), "step": T.t(str(STEPS[clampi(int(ab.step), 0, STEPS.size() - 1)])), "mode": mode, "names": names,
			"title": T.t(str(ab.chapter()["title"])) if not R.is_empty() else T.t("Die Karte des Grossvaters"), "h": snappedf(main.hour(), 0.01)}
	if R.is_empty():
		return d
	var pos: Vector2 = R.get("pos", Vector2.ZERO)
	d["pos"] = [int(pos.x), int(pos.y)]
	d["stamina"] = int(R.get("stamina", 0))
	d["smax"] = int(R.get("smax", 100))
	d["water"] = snappedf(float(R.get("water", 0.0)), 0.1)
	d["food"] = int(R.get("food", 0))
	if ab.karte != null:
		d["route"] = _pts(ab.karte.route)
		d["plan"] = _pts(ab.karte.plan)
	var ps: Array = []
	if mode != "allein":
		for i in range(1 if mode == "rollen" else 2):
			var q: Vector2 = pl[i]["pos"] if on else pos + (pl[i]["off"] as Vector2)
			ps.append([int(q.x), int(q.y), snappedf(float(pl[i]["yaw"]), 0.01), names[i], "#" + COLS[i].to_html(false)])
	d["p"] = ps
	if b != null:
		d["camp"] = [int(b.spot_xz.x), int(b.spot_xz.y)]
		if main.head != null and not main.cams.is_empty():
			var hv: Vector3 = b.V(main.head.global_position)
			var fw: Vector3 = b.inv.basis * (-(main.cams[0] as Camera3D).global_transform.basis.z)
			d["mw"] = [int(hv.x), int(hv.z), snappedf(atan2(-fw.x, -fw.z), 0.01)]
	var pl2: Array = []
	for p in pins:
		pl2.append([p["x"], p["z"], p["by"]])
	d["pins"] = pl2
	var pe: Dictionary = R.get("pending", {})
	if not pe.is_empty():
		var opts: Array = []
		for o in pe.get("options", []):
			opts.append([str(o[0]), str(o[1]).get_slice("\n", 0)])
		d["q"] = {"title": str(pe.get("title", "")), "text": str(pe.get("text", "")), "options": opts}
	if not race.is_empty():
		var tg: Vector2 = race["target"]
		d["race"] = [int(tg.x), int(tg.y)]
	d["wins"] = wins
	return d


func _phone_tick() -> void:
	var g = main.game
	if g == null:
		return
	if phone and not g.open:
		phone = false
	if not phone:
		return
	if g.round_state in ["countdown", "play"]:
		return                                               # a real game round runs: that has the phones now
	var st := {}
	var have := false
	for p in g.players:
		if p == null or p["sock"] == null or str(p.get("kind", "phone")) != "phone":
			continue
		if str(p["role"]) != "watch":
			g._assign(p, "watch")                           # sees what MoveEye sees (head camera)
		if st.is_empty():
			st = phone_state()
		if p.get("a5_map_sock") != p["sock"]:
			p["a5_map_sock"] = p["sock"]
			var mb := _map64()
			if mb != "":
				_send(p, {"t": "abzmap", "b64": mb, "lo": Bt.LO, "hi": -Bt.LO})
		_send(p, st)
		have = true
	if have:
		main.snap_want[0] = main.now()                       # MoveEye pictures for the phones


# =======================================================================================================================
# in the panel of the adventure
# =======================================================================================================================
func paint_choice(body: Control) -> void:
	"""step «Schwierigkeit & Ziel»: who plays (Spielart, names, controllers, the phone)"""
	var gg: VBoxContainer = ab._group(T.t("Mitspieler"), body)
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 10)
	g.add_theme_constant_override("v_separation", 10)
	gg.add_child(g)
	var M := {"allein": ["Allein", "Wie bisher: die Ansicht wandert mit der Tour."],
			"gemeinsam": ["Gemeinsam", "Zwei Wanderer, jeder mit eigenem Controller. Bis 110 m von der Gruppe weg spähen."],
			"rollen": ["Rollen", "Einer wandert, der andere bedient MoveEye und die Karte."],
			"wettrennen": ["Wettrennen", "Vor jeder Etappe: wer ist zuerst beim Fähnchen? Etappensiege zählen."]}
	for k in MODES:
		var kk: String = k
		g.add_child(ab._card(T.t(str(M[k][0])), T.t(str(M[k][1])), mode == k, func(): set_mode(kk)))
	if mode != "allein":
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		gg.add_child(row)
		var eds: Array = []
		for i in range(2):
			var l: Label = ab._lab("%d" % (i + 1), 14, COLS[i], false)
			row.add_child(l)
			var e := LineEdit.new()
			e.text = names[i]
			e.max_length = 20
			e.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			e.placeholder_text = T.t("Name")
			row.add_child(e)
			eds.append(e)
		for e in eds:
			e.text_changed.connect(func(_t): set_names(eds[0].text, eds[1].text))
		var nd: int = main.padmap.devices().size() if main.padmap != null else 0
		var need := 1 if mode == "rollen" else 2
		var tx := T.t("🎮 %d Controller verbunden.") % nd
		if nd < need:
			tx += " " + (T.t("Ohne Controller: Spieler 1 mit W A S D (Q / E umschauen, Shift rennen), Spieler 2 mit I J K L (U / O, H).") if mode != "rollen" else T.t("Ohne Controller: Spieler 1 mit W A S D, MoveEye mit der Maus."))
		else:
			tx += " " + T.t("Rechter Stick = gehen, linker Stick = umschauen, R2 = rennen, Start = Menü (wie beim Spiel am PC).")
		gg.add_child(ab._lab(tx, 12, Color(0.65, 0.7, 0.78)))
		gg.add_child(ab._lab(T.t("Geteilter Bildschirm, nahe beieinander eine gemeinsame Ansicht. Zwei Ansichten brauchen mehr Leistung - in Lite mit halber Auflösung und kleinerer Sichtweite."), 12, Color(0.55, 0.6, 0.68)))
	var cb := CheckButton.new()
	cb.text = T.t("Handy als Begleiter (Karte und MoveEye-Bilder auf dem Handy)")
	cb.button_pressed = phone
	cb.toggled.connect(func(v): set_phone(v))
	gg.add_child(cb)
	if phone and main.game != null and main.game.open:
		var hb := HBoxContainer.new()
		hb.add_theme_constant_override("separation", 10)
		gg.add_child(hb)
		var ad: String = main.game.address()
		var qr := TextureRect.new()
		qr.custom_minimum_size = Vector2(120, 120)
		qr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		qr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
		qr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		qr.texture = Qr.texture(ad, 4)
		hb.add_child(qr)
		var l2: Label = ab._lab(T.t("Mit dem Handy (gleiches WLAN) den QR-Code scannen oder %s öffnen - auch auf der MoveEye-Seite «Simulator». Das Handy zeigt, was MoveEye sieht, und die Karte: antippen = Tipp für die Wanderer.") % ad, 12)
		l2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hb.add_child(l2)
		gg.add_child(ab._lab(T.t("📱 %d Begleiter verbunden") % _watchers(), 12, Color(0.3, 0.85, 0.45)))


func paint_board(body: Control, compact := false) -> void:
	"""the family board (morning; small on the chapter page)"""
	var d := Board.load_all()
	var L := Board.people_sorted(d)
	if compact and L.is_empty() and (d["fotos"] as Array).is_empty():
		return
	var gg: VBoxContainer = ab._group(T.t("Familien-Bestenliste"), body)
	if L.is_empty():
		gg.add_child(ab._lab(T.t("Noch leer - am Morgen jedes Kapitels zählt, was ihr gefunden habt."), 12, Color(0.6, 0.66, 0.74)))
	var rank := 1
	for e in L.slice(0, 3 if compact else 8):
		var pe: Dictionary = e[1]
		var tx := "%d. %s   📖 %d/10   🐾 %d   🎒 %d   💎 %d" % [rank, str(e[0]), (pe.get("tagebuch", []) as Array).size(), (pe.get("tiere", []) as Array).size(),
				(pe.get("ausruestung", []) as Array).size(), (pe.get("funde", []) as Array).size()]
		if int(pe.get("etappen", 0)) > 0:
			tx += "   🏁 %d" % int(pe["etappen"])
		gg.add_child(ab._lab(tx, 14 if rank == 1 else 13, Color("#ffd166") if rank == 1 else Color(0.85, 0.88, 0.92), false))
		rank += 1
	if not compact:
		gg.add_child(ab._lab(T.t("📖 Tagebuchseiten · 🐾 Tiere · 🎒 Ausrüstung · 💎 Fundstücke · 🏁 Etappensiege"), 11, Color(0.55, 0.6, 0.68)))
	var fotos: Array = d["fotos"]
	if not fotos.is_empty():
		gg.add_child(ab._lab(T.t("Beste Wildkamera-Fotos (Schärfe und Tier)"), 13, Color(0.62, 0.68, 0.76), false))
		var fl := HFlowContainer.new()
		fl.add_theme_constant_override("h_separation", 8)
		gg.add_child(fl)
		for f in fotos.slice(0, 2 if compact else 4):
			var vb := VBoxContainer.new()
			fl.add_child(vb)
			var tr := TextureRect.new()
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			tr.custom_minimum_size = Vector2(150, 84)
			if FileAccess.file_exists(str(f.get("file", ""))):
				var im := Image.load_from_file(str(f["file"]))
				if im != null:
					tr.texture = ImageTexture.create_from_image(im)
			vb.add_child(tr)
			var cap := "%d %s · %s" % [int(f.get("punkte", 0)), T.t("Punkte"), str(f.get("wer", ""))]
			if str(f.get("tier", "")) != "":
				cap += " · " + T.t(str(f["tier"]))
			var cl: Label = ab._lab(cap, 11, Color(0.75, 0.8, 0.86))
			cl.custom_minimum_size = Vector2(150, 0)
			vb.add_child(cl)
	if not compact:
		var rk: Array = Bt.ranking()                          # the existing ranking of the sleeping places (bergtal.gd)
		if not rk.is_empty():
			gg.add_child(ab._lab(T.t("Beste Schlafplätze"), 13, Color(0.62, 0.68, 0.76), false))
			for e in rk.slice(0, 3):
				gg.add_child(ab._lab("%s  %.1f ★" % [T.t(str(e.get("name", ""))), float(e.get("total", 0.0))], 12))
		var hb := HFlowContainer.new()
		hb.add_theme_constant_override("h_separation", 8)
		gg.add_child(hb)
		ab._btn(hb, T.t("📸 MoveEye-Bild jetzt bewerten"), func(): take_foto(names[0], "pc"); ab._changed())
		ab._btn(hb, T.t("Bestenliste zurücksetzen"), func(): Board.reset(); ab._changed())


# =======================================================================================================================
# control API
# =======================================================================================================================
func op(d: Dictionary) -> Dictionary:
	var k := str(d.get("k", "state"))
	var out := {"ok": true}
	match k:
		"mode":
			set_mode(str(d.get("value", "allein")))
		"names":
			var v: Array = d.get("value", [])
			set_names(str(v[0]) if v.size() > 0 else "", str(v[1]) if v.size() > 1 else "")
		"phone":
			set_phone(bool(d.get("value", true)))
		"drive":
			var i := clampi(int(d.get("p", 1)) - 1, 0, 1)
			_test[i] = {"v": Vector2(float(d.get("x", 0.0)), float(d.get("y", -1.0))).limit_length(1.0), "until": now() + float(d.get("secs", 2.0)), "run": bool(d.get("run", false))}
		"place":
			var i2 := clampi(int(d.get("p", 2)) - 1, 0, 1)
			if race.is_empty():
				pl[i2]["off"] = Vector2(float(d.get("x", 0.0)), float(d.get("z", 0.0)))
				pl[i2]["idle"] = 0.0
			else:
				pl[i2]["pos"] = Vector2(float(d.get("x", 0.0)), float(d.get("z", 0.0)))
		"pin":
			add_pin(float(d.get("x", 0.0)), float(d.get("z", 0.0)), str(d.get("by", "Test")))
		"foto":
			out["foto"] = take_foto(str(d.get("by", names[0])), "test")
		"lite":
			force_lite = bool(d.get("value", true))
		"fps":
			out["fps"] = snappedf(fps_avg(), 0.1)
			out["fps_now"] = Engine.get_frames_per_second()
		"board":
			out["board"] = Board.load_all()
		"reset_board":
			Board.reset()
		"phone_state":
			out["phone_state"] = phone_state()
	out["zweit"] = state()
	return out


func state() -> Dictionary:
	var ps: Array = []
	for i in range(2):
		var q: Vector2 = pl[i]["pos"]
		ps.append({"name": names[i], "pos": [snappedf(q.x, 0.1), snappedf(q.y, 0.1)], "off": [snappedf(pl[i]["off"].x, 0.1), snappedf(pl[i]["off"].y, 0.1)], "dev": pl[i]["dev"]})
	var rc := {}
	if not race.is_empty():
		rc = {"target": [snappedf(race["target"].x, 0.1), snappedf(race["target"].y, 0.1)], "arr": race["arr"], "first": race["first"], "dist": int(race["dist"])}
	return {"mode": mode, "on": on, "merged": merged, "players": ps, "race": rc, "wins": wins, "pins": pins.size(), "phone": phone,
			"watchers": _watchers(), "lite": _lite(), "fps": snappedf(fps_avg(), 0.1), "head_fps": head_fps()}


# =======================================================================================================================
# the companion page on the phone (appended to game.gd PAGE, handler GM.abz / GM.abzmap / GM.abzinfo)
# =======================================================================================================================
const PHONE_JS := r"""<style>
#abz{position:fixed;right:max(8px,env(safe-area-inset-right));top:calc(max(8px,env(safe-area-inset-top)) + 44px);width:min(46vw,420px);max-height:calc(100vh - 70px);overflow:auto;z-index:11;background:#111822ee;border:1px solid #3b8cff;border-radius:14px;padding:8px 10px;color:#e6edf3;font-size:13px;pointer-events:auto}
#abz[hidden]{display:none}#abz h3{margin:0 0 4px;font-size:15px;display:flex;justify-content:space-between;align-items:center;gap:6px}#abz h3 button{font-size:12px;padding:2px 8px}
#abz canvas{width:100%;aspect-ratio:1;border-radius:10px;display:block;touch-action:none;background:#f7f5ec}
#abz .row{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}#abz button{background:#151e2b;color:#e6edf3;border:1px solid #1f2b3a;border-radius:10px;padding:6px 9px;font-size:13px}
#abz .q{border:1px solid #ffd166;border-radius:10px;padding:6px 8px;margin-top:6px}#abz .q b{color:#ffd166}#abz .st{color:#9fb0c3;font-size:12px;margin-top:4px}
#abz.min canvas,#abz.min .row,#abz.min .q,#abz.min .st{display:none}#abzinfo{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:#111822ee;border:1px solid #34c759;border-radius:10px;padding:5px 12px;z-index:13;opacity:0;transition:opacity .3s;pointer-events:none}
@media (orientation:portrait){#abz{left:8px;right:8px;width:auto;top:auto;bottom:8px;max-height:58vh}}
</style>
<div id="abz" hidden></div><div id="abzinfo"></div>
<script>
// Bergtal-Abenteuer · Handy als Begleiter (abenteuer_zweit.gd): Karte, Wanderer, MoveEye, Tipps - das Bild dahinter ist MoveEyes Kopfkamera
(function () {
  const G = window.GM = window.GM || {};
  let map = null, lo = -1024, hi = 1024, A = null, built = false, mini = false, qsig = "";
  const box = document.getElementById("abz");
  G.abzmap = function (m) { const im = new Image(); im.onload = () => { map = im; draw(); }; im.src = "data:image/jpeg;base64," + m.b64; lo = m.lo; hi = m.hi; };
  G.abzinfo = function (m) { const e = document.getElementById("abzinfo"); e.textContent = m.txt || ""; e.style.opacity = 1; clearTimeout(G._abzI); G._abzI = setTimeout(() => e.style.opacity = 0, 3000); };
  function build() {
    built = true;
    box.innerHTML = '<h3><span id="abzt">🧭 Begleiter</span><button id="abzmin">▁</button></h3><canvas id="abzc" width="420" height="420"></canvas>' +
      '<div class="st" id="abzs"></div><div id="abzq"></div><div class="row">' +
      [["links", "⬅ Links!"], ["rechts", "Rechts! ➡"], ["pause", "☕ Pause"], ["wasser", "💧 Wasser"], ["achtung", "⚠ Achtung"], ["super", "👍 Super"]].map(b => '<button data-s="' + b[0] + '">' + b[1] + '</button>').join("") +
      '<button id="abzf">📸 Foto für die Bestenliste</button></div><div class="st">Karte antippen = 📍 Tipp für die Wanderer</div>';
    box.querySelectorAll("button[data-s]").forEach(b => b.onclick = () => send({t: "abz", k: "say", v: b.dataset.s}));
    document.getElementById("abzf").onclick = () => send({t: "abz", k: "foto"});
    document.getElementById("abzmin").onclick = () => { mini = !mini; box.classList.toggle("min", mini); };
    const c = document.getElementById("abzc");
    c.onclick = (e) => { const r = c.getBoundingClientRect(), v = view(); const x = v.x0 + (e.clientX - r.left) / r.width * v.s, z = v.z0 + (e.clientY - r.top) / r.height * v.s; send({t: "abz", k: "pin", x: x, z: z}); };
  }
  function view() {                      // a square of 700 m around the walkers (the whole valley is 2 km)
    const P = (A && A.pos) || [0, 0], s = 700; let x0 = P[0] - s / 2, z0 = P[1] - s / 2;
    x0 = Math.max(lo, Math.min(hi - s, x0)); z0 = Math.max(lo, Math.min(hi - s, z0)); return {x0: x0, z0: z0, s: s};
  }
  function draw() {
    const c = document.getElementById("abzc"); if (!c || !A) return; const g = c.getContext("2d"), W = c.width, v = view(), k = W / v.s;
    const X = (x) => (x - v.x0) * k, Z = (z) => (z - v.z0) * k;
    g.fillStyle = "#f7f5ec"; g.fillRect(0, 0, W, W);
    if (map) { const px = map.width / (hi - lo); g.drawImage(map, (v.x0 - lo) * px, (v.z0 - lo) * px, v.s * px, v.s * px, 0, 0, W, W); }
    const line = (pts, col, w, dash) => { if (!pts || pts.length < 2) return; g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(X(p[0]), Z(p[1])) : g.moveTo(X(p[0]), Z(p[1]))); g.stroke(); g.setLineDash([]); };
    line(A.plan, "#b3261e", 3, [7, 6]); line(A.route, "#b3261e", 4);
    const dot = (p, col, r, txt) => { g.fillStyle = col; g.beginPath(); g.arc(X(p[0]), Z(p[1]), r, 0, 7); g.fill(); g.strokeStyle = "#0a0e14"; g.lineWidth = 2; g.stroke(); if (txt) { g.fillStyle = "#0a0e14"; g.font = "bold 13px sans-serif"; g.fillText(txt, X(p[0]) + r + 3, Z(p[1]) + 4); } };
    if (A.camp) dot(A.camp, "#34c759", 6, "⛺");
    if (A.mw) { const p = A.mw, a = p[2]; g.fillStyle = "rgba(59,140,255,.25)"; g.beginPath(); g.moveTo(X(p[0]), Z(p[1])); g.arc(X(p[0]), Z(p[1]), 60 * k, -Math.PI / 2 - a - 0.6, -Math.PI / 2 - a + 0.6); g.closePath(); g.fill(); dot(p, "#3b8cff", 5, "MoveEye"); }
    (A.pins || []).forEach(p => dot(p, "#ffd166", 7, "📍"));
    if (A.race) dot(A.race, "#34c759", 7, "🏁");
    if (A.pos) dot(A.pos, "#e6edf3", 6, "");
    (A.p || []).forEach(p => dot(p, p[4], 6, p[3]));
  }
  G.abz = function (m) {
    A = m; if (!m.on) { box.hidden = true; return; }
    if (!built) build(); box.hidden = false;
    document.getElementById("abzt").textContent = "🧭 " + m.title + " · " + m.step;
    const hh = Math.floor(m.h), mm = Math.round((m.h - hh) * 60);
    document.getElementById("abzs").textContent = "🕐 " + hh + ":" + String(mm).padStart(2, "0") + "  💪 " + m.stamina + "/" + m.smax + "  💧 " + m.water + " L  🍞 " + m.food + (m.wins && m.mode === "wettrennen" ? "  🏁 " + m.names[0] + " " + m.wins["1"] + " : " + m.wins["2"] + " " + m.names[1] : "");
    const sig = JSON.stringify(m.q || null);
    if (sig !== qsig) { qsig = sig; const q = document.getElementById("abzq");
      q.innerHTML = m.q ? '<div class="q"><b>' + esc(m.q.title) + '</b><div>' + esc(m.q.text) + '</div><div class="row">' + m.q.options.map(o => '<button data-r="' + esc(o[0]) + '">💡 ' + esc(o[1]) + '</button>').join("") + '</div></div>' : "";
      q.querySelectorAll("button[data-r]").forEach(b => b.onclick = () => send({t: "abz", k: "rat", v: b.dataset.r})); }
    draw();
  };
})();
</script>
"""
