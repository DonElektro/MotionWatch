extends Node
## Bergtal · Horror-Modus «Das Hospiz» – Rätsel (Daniel, 31.10.2026): in jedem der 3 Kapitel ein Rätsel, dessen Lösung nur auf
## einer MoveEye-Aufnahme zu sehen ist. Die Geschichte bleibt die von bergtal_horror.gd (Hospizwartin «B.», 1936, Glocke,
## Laterne, verlassene Hütte, Hospizbuch) – die Rätsel öffnen nur Türen, sie erfinden keine neue Handlung.
##
##   Kapitel 1 · Morgen: «Der Hüttenschlüssel» – in der Nacht fällt der Gestalt beim Zelt etwas ins Gras. Die Aufnahme
##       «Etwas fällt ins Gras» zeigt im Wärmebild einen kleinen warmen Fleck (MoveEye markiert ihn). Am Morgen hingehen
##       («Erkunden» oder die Ansicht, ≤ 1.8 m) → alter Schlüssel mit Anhänger «Hütte».
##   Kapitel 2 · Morgen: «Die Zahlen an der Wand» – die Hüttentür ist zugeschlagen (der Schlüssel von gestern sperrt auf),
##       drinnen ein Wandkasten mit Zahlenschloss. Die vier Ziffern stehen nur auf der Wärmebild-Aufnahme «Zahlen an der Wand»
##       (warm an die Hüttenwand geschrieben, im Bild vergrössert). Im Kasten: eine zweite Seite aus dem Hospizbuch.
##   Kapitel 3 · Abend: «Das Schloss am Hospiz» – Zahlenräder wie eine Uhr. Die Lösung ist die Uhrzeit der Aufnahme
##       «Die Glocke, ganz nah» aus der 2. Nacht (im Bild oben links und in der Liste, auch in MoveEyes Verlauf). Drinnen: der
##       leere Haken der Glocke.
## Nie eine Sackgasse: «Hinweis» (1. Stufe: Hilfe, 2. Stufe: Lösung). Fehlt eine Aufnahme (Nacht übersprungen, Simulator neu
## gestartet), sagt die Karte das und hilft gleich weiter.
## Schreck-Regler (horror.strength) wirkt weiter: unter 25 % haben die Rätsel KEINEN Schreckmoment (nur ruhiger Text);
## ab 25 % ein leises Geräusch beim Öffnen/Finden, ab 50 % zusätzlich Lampenflackern / kurzer dunkler Blitz, ab 75 % der Stich-Ton.
## Lite: nichts Teures (keine Lichter; der Hinweis-Lichtpunkt ist ein leuchtendes Kügelchen nur fürs Fenster).
## Eingehängt in bergtal_horror.gd an 6 Stellen (alle mit «raetsel» markiert): _ready, begin (Beats + Abendkarte), _beat,
## _morning, Pause/_reshow_phase, command («r_…»).
## Zustand in user://bergtal_horror.json unter «raetsel» (pro Spielstand: «raetsel_2» / «raetsel_3», spielstand.gd raetsel_key;
## im Kapitel-Sprung-Test «raetsel_test») (neben dem Fortschritt; der Passwort-Hash bleibt unberührt).
## Test: /control {"action": "horror", "do": "r_info" | "r_code" (code) | "r_hint" | "r_find" | "r_go"}.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

const FIND_DIST := 1.8                 # m (flat) – close enough to see the key in the grass
const HELPER_LAYER := 128              # only the window sees it (main.HELPER_LAYER)
const KEY_WARM_C := 31.0               # a key and the grass under it, warm from a hand: a few °C over the night air, fades in minutes

var h                                  # bergtal_horror.gd
var st := {}                           # {k1: {found, clip, pos}, k2: {code, clip, solved}, k3: {time, clip, solved}}
var active := ""                       # "" | k1 | k2 | k3 – the riddle on the screen
var searching := false                 # k1: the card is away, the player looks for the key
var _then := Callable()
var _pending: Array = []               # [due, k]
var _key: Node3D
var _warm: MeshInstance3D
var _beacon: MeshInstance3D
var _bar: PanelContainer
var _bar_lbl: Label
var _entry: LineEdit
var _msg: Label
var _tries := 0


func _main():
	return h.main


func _strength() -> float:
	return float(h.strength)


# =======================================================================================================================
# state (in the horror's store, next to «progress»)
# =======================================================================================================================
func _load() -> void:
	var s = h._store.get(h.raetsel_key(), {})
	st = (s as Dictionary).duplicate(true) if s is Dictionary else {}


func _save() -> void:
	h._store[h.raetsel_key()] = st
	h._save()


func _part(k: String) -> Dictionary:
	if not (st.get(k) is Dictionary):
		st[k] = {}
	return st[k]


func reset() -> void:
	"""a new game (night 1): new code for the box, nothing found yet"""
	var code := ""
	for _i in range(4):
		code += str(randi() % 10)
	st = {"k1": {"found": false}, "k2": {"code": code, "solved": false}, "k3": {"time": "", "solved": false}}
	active = ""
	searching = false
	_tries = 0
	_pending.clear()
	_save()


# =======================================================================================================================
# the nights: when MoveEye records the clue (beats between the ones of bergtal_horror.gd)
# =======================================================================================================================
func add_beats(n: int, beats: Array) -> Array:
	if n == 1:
		reset()
	else:
		_load()
		if st.is_empty():
			reset()
	var out := beats.duplicate()
	match n:
		1:
			out.append([0.935, "raetsel", {"k": "k1"}])          # right after «fig_away»: she was at the tent
		2:
			out.append([0.22, "raetsel", {"k": "k2"}])           # the door of the hut is open, she went in
			out.append([0.77, "raetsel", {"k": "k3"}])           # after the bell at 12 m
	out.sort_custom(func(a, b): return float(a[0]) < float(b[0]))
	return out


func beat(a: Dictionary) -> void:
	var k := str(a.get("k", ""))
	var m = _main()
	if k == "k1":
		_place_key()
	m._th_asked = m.now()                                       # a fresh thermal frame for the recording
	_pending.append([Time.get_ticks_msec() / 1000.0 + 1.2, k])


func _process(_dt: float) -> void:
	if h == null:
		return
	if not h.running:
		if active != "" or (_bar != null and is_instance_valid(_bar) and _bar.visible):
			clear()                                                  # the mode was ended (stop): the key went with horror._root
		return
	if not h.paused:
		var tn := Time.get_ticks_msec() / 1000.0
		for i in range(_pending.size() - 1, -1, -1):
			if tn >= float(_pending[i][0]):
				var k: String = _pending[i][1]
				_pending.remove_at(i)
				_record(k)
	if _beacon != null and is_instance_valid(_beacon) and _beacon.visible:
		var s := 0.8 + 0.3 * sin(Time.get_ticks_msec() / 250.0)
		_beacon.scale = Vector3.ONE * s
	if searching and not h.paused and _near_key():
		_found()


func _record(k: String) -> void:
	var c: Dictionary
	match k:
		"k1":
			c = h._clip_now(T.t("Etwas fällt ins Gras"), T.t("Kamera: Nebel. Wärmebild: wo die Gestalt beim Zelt stand, liegt ein kleiner warmer Fleck im Gras (markiert)."))
			_part("k1")["seen"] = _draw_mark(c, _key.global_position if _key != null and is_instance_valid(_key) else Vector3.ZERO, false)
		"k2":
			c = h._clip_now(T.t("Zahlen an der Wand"), T.t("Kamera: Nebel. Wärmebild (vergrössert): neben der Hüttentür vier warme Ziffern – wie mit einer warmen Hand an die Wand geschrieben."))
			var hp: Vector3 = h._hut.global_position + h._hut.global_transform.basis * Vector3(-1.6, 1.4, 2.6) if h._hut != null else Vector3.ZERO
			_draw_mark(c, hp, true)
			_draw_code(c, str(_part("k2").get("code", "0000")))
		"k3":
			c = h._clip_now(T.t("Die Glocke, ganz nah"), T.t("Das Mikrofon hört eine Glocke, ganz nah am Lager. Kamera: Nebel. Wärmebild: niemand."))
			_part("k3")["time"] = str(c["hhmm"])
			_draw_time(c, str(c["hhmm"]))
		_:
			return
	_part(k)["clip"] = int(c["id"])
	_save()


# =======================================================================================================================
# the key (chapter 1): a small thing in the grass in front of the tent + a warm spot only the thermal camera sees
# =======================================================================================================================
func _place_key() -> void:
	if h._root == null or not is_instance_valid(h._root):
		return
	_clear_key()
	var m = _main()
	var tf: Vector3 = h._tent_front()
	var o := Vector3(tf.x, 0, tf.z)
	o = o.normalized() if o.length() > 0.1 else Vector3(0, 0, -1)
	var p := tf + o * 1.2                                       # a step further out, where she turned away
	var fl := Vector2(p.x, p.z)
	if fl.length() < 3.0:                                       # not right under MoveEye: you have to walk there
		fl = fl.normalized() * 3.2 if fl.length() > 0.1 else Vector2(0, -3.2)
		p = Vector3(fl.x, 0, fl.y)
	p.y = m.ground_y(p.x, p.z)
	_key = Node3D.new()
	h._root.add_child(_key)
	_key.global_position = p
	var brass: StandardMaterial3D = m.mat(Color(0.45, 0.36, 0.2))
	m.add_mesh(_key, m.box(0.11, 0.012, 0.025), Vector3(0, 0.012, 0), brass, "stone", Vector3(0, 0.6, 0))
	m.add_mesh(_key, m.box(0.04, 0.012, 0.04), Vector3(-0.05, 0.012, 0.03), brass, "stone", Vector3(0, 0.6, 0))
	m.add_mesh(_key, m.box(0.07, 0.01, 0.045), Vector3(0.08, 0.01, -0.04), m.mat(Color(0.32, 0.22, 0.12)), "tree")  # the wooden tag
	_warm = MeshInstance3D.new()                                # warm grass under it (thermal only, gone in the morning)
	_warm.mesh = m.box(0.4, 0.07, 0.4)
	_warm.position = Vector3(0, 0.035, 0)
	_warm.material_override = m.tmat_fixed(KEY_WARM_C)
	_warm.layers = 2
	_warm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_key.add_child(_warm)
	_beacon = MeshInstance3D.new()                              # the hint: a faint point of light, only in the window
	var sp := SphereMesh.new()
	sp.radius = 0.07
	sp.height = 0.14
	_beacon.mesh = sp
	var bm := StandardMaterial3D.new()
	bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bm.albedo_color = Color(1.0, 0.85, 0.5)
	bm.emission_enabled = true
	bm.emission = Color(1.0, 0.8, 0.4)
	_beacon.material_override = bm
	_beacon.position = Vector3(0, 0.35, 0)
	_beacon.layers = HELPER_LAYER
	_beacon.visible = false
	_key.add_child(_beacon)
	_part("k1")["pos"] = [snappedf(p.x, 0.01), snappedf(p.z, 0.01)]


func _ensure_key() -> void:
	"""the night was skipped (or the simulator restarted): the key lies there anyway"""
	if _key != null and is_instance_valid(_key):
		return
	_place_key()


func _clear_key() -> void:
	if _key != null and is_instance_valid(_key):
		_key.queue_free()
	_key = null
	_warm = null
	_beacon = null


func _near_key() -> bool:
	if _key == null or not is_instance_valid(_key):
		return false
	var m = _main()
	var kp := _key.global_position
	var pts: Array = []
	if m.rig != null:
		pts.append(m.rig.global_position)                        # «Erkunden»: MoveEye on the rover drives there
	var cam: Camera3D = m.view_cam
	if cam != null and cam.global_position.y - m.ground_y(cam.global_position.x, cam.global_position.z) < 3.0:
		pts.append(cam.global_position)                          # the view (driver view, flying low)
	for q in pts:
		if Vector2(q.x - kp.x, q.z - kp.z).length() <= FIND_DIST:
			return true
	return false


func key_dist() -> float:
	if _key == null or not is_instance_valid(_key):
		return -1.0
	var m = _main()
	var r: Vector3 = m.rig.global_position if m.rig != null else Vector3.ZERO
	return Vector2(r.x - _key.global_position.x, r.z - _key.global_position.z).length()


# =======================================================================================================================
# drawing into the recording (the picture MoveEye gets): marker, enlarged digits, time stamp
# =======================================================================================================================
func _img(c: Dictionary) -> Image:
	return (c["tex"] as ImageTexture).get_image()


func _store_img(c: Dictionary, img: Image) -> void:
	c["jpg"] = img.save_jpg_to_buffer(0.82)
	c["tex"] = ImageTexture.create_from_image(img)


func _th_xy(p: Vector3):
	"""world → pixel in the thermal half of the recording (322 … 638 × 2 … 246), or null"""
	var m = _main()
	if m.cams.size() < 3 or p == Vector3.ZERO:
		return null
	var cam: Camera3D = m.cams[2]
	if cam.is_position_behind(p):
		return null
	var vp: Vector2 = Vector2(m.TH_W * 2, m.TH_H * 2)
	var q: Vector2 = cam.unproject_position(p)
	if q.x < 0 or q.y < 0 or q.x > vp.x or q.y > vp.y:
		return null
	return Vector2(322.0 + q.x / vp.x * 316.0, 2.0 + q.y / vp.y * 244.0)


func _draw_mark(c: Dictionary, p: Vector3, square: bool) -> bool:
	"""true = the place is in the thermal picture and marked"""
	var xy = _th_xy(p)
	if xy == null:
		return false
	var img := _img(c)
	var col := Color(0.35, 0.75, 1.0)                             # MoveEye's blue
	var r := 11.0
	for a in range(0, 360, 3):
		var t := deg_to_rad(a)
		var d := Vector2(cos(t), sin(t))
		if square:
			d = d / maxf(absf(d.x), absf(d.y))
		for w in [0.0, 1.0]:
			var q: Vector2 = xy + d * (r + w)
			_px(img, int(q.x), int(q.y), col)
	_store_img(c, img)
	return true


func _px(img: Image, x: int, y: int, col: Color) -> void:
	if x >= 0 and y >= 0 and x < img.get_width() and y < img.get_height():
		img.set_pixel(x, y, col)


func _rect(img: Image, x: int, y: int, w: int, hh: int, col: Color) -> void:
	img.fill_rect(Rect2i(x, y, w, hh).intersection(Rect2i(0, 0, img.get_width(), img.get_height())), col)


const SEG := {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
		"8": "abcdefg", "9": "abcdfg"}


func _digit(img: Image, x: int, y: int, w: int, hh: int, t: int, ch: String, col: Color) -> void:
	"""a seven-segment digit (or «:») into the picture"""
	if ch == ":":
		_rect(img, x + w / 2 - t / 2, y + hh / 3 - t / 2, t, t, col)
		_rect(img, x + w / 2 - t / 2, y + 2 * hh / 3 - t / 2, t, t, col)
		return
	var s: String = SEG.get(ch, "")
	var m := hh / 2
	if "a" in s: _rect(img, x, y, w, t, col)
	if "g" in s: _rect(img, x, y + m - t / 2, w, t, col)
	if "d" in s: _rect(img, x, y + hh - t, w, t, col)
	if "f" in s: _rect(img, x, y, t, m, col)
	if "b" in s: _rect(img, x + w - t, y, t, m, col)
	if "e" in s: _rect(img, x, y + m, t, hh - m, col)
	if "c" in s: _rect(img, x + w - t, y + m, t, hh - m, col)


func _draw_code(c: Dictionary, code: String) -> void:
	"""the four warm digits, enlarged in a box at the bottom of the thermal half (like a zoom of the wall)"""
	var m = _main()
	var img := _img(c)
	var x0 := 352
	var y0 := 168
	_rect(img, x0 - 2, y0 - 2, 260, 74, Color(0.35, 0.75, 1.0))
	_rect(img, x0, y0, 256, 70, m._inferno(0.14))                # the cold stone wall
	for i in range(code.length()):
		var dx := x0 + 30 + i * 52
		_digit(img, dx - 2, y0 + 10, 34, 52, 10, code[i], m._inferno(0.55))   # the warmth spreads a little
		_digit(img, dx, y0 + 12, 30, 48, 6, code[i], m._inferno(0.9))
	_store_img(c, img)


func _draw_time(c: Dictionary, hhmm: String) -> void:
	"""the time stamp of the recording (top left, next to REC) – like the on-screen time of a camera"""
	var img := _img(c)
	var x := 26
	for ch in hhmm:
		_digit(img, x + 1, 8, 9, 16, 2, ch, Color(0, 0, 0))
		_digit(img, x, 7, 9, 16, 2, ch, Color(0.95, 0.95, 0.95))
		x += 7 if ch == ":" else 13
	_store_img(c, img)


# =======================================================================================================================
# the riddle cards (hooks: morning(), evening())
# =======================================================================================================================
func morning(n: int, then: Callable) -> bool:
	"""before the morning card: chapter 1 the key, chapter 2 the box. true = a riddle is on the screen"""
	_load()
	if n == 1 and not bool(_part("k1").get("found", false)):
		if _warm != null and is_instance_valid(_warm):
			_warm.visible = false                                    # cold by the morning
		_ensure_key()
		return _open("k1", then)
	if n == 2 and not bool(_part("k2").get("solved", false)):
		return _open("k2", then)
	return false


func evening(n: int, then: Callable) -> bool:
	"""before the intro card of the 3rd night: the lock at the hospice"""
	_load()
	if n == 3 and not bool(_part("k3").get("solved", false)):
		return _open("k3", then)
	return false


func _open(k: String, then: Callable) -> bool:
	active = k
	_then = then
	_tries = 0
	searching = false
	reshow()
	return true


func reshow() -> void:
	"""after the pause (and at the start): the card of the active riddle again"""
	if active == "":
		return
	h.phase = "raetsel"
	if searching:
		h._clear_card()
		_show_bar()
		return
	match active:
		"k1":
			_card_k1()
		"k2":
			_card_code("k2")
		"k3":
			_card_code("k3")


func _clip_of(k: String) -> Dictionary:
	var id := int(_part(k).get("clip", -1))
	for c in h.clips:
		if int(c["id"]) == id:
			return c
	return {}


func _thumb(v: Control, k: String) -> void:
	var c := _clip_of(k)
	if c.is_empty():
		return
	var tr := TextureRect.new()
	tr.texture = c.get("tex", null)
	tr.custom_minimum_size = Vector2(560, 217)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	v.add_child(tr)
	h._text(v, "%s · %s · %s" % [T.t("Nacht {n}", {"n": int(c["night"])}), str(c["hhmm"]), str(c["title"])], 12, UI.MUT)


func _card_k1() -> void:
	h.phase = "raetsel"
	_hide_bar()
	var v: VBoxContainer = h._new_card(T.t("Rätsel: Der Hüttenschlüssel"), UI.ORG, 620)
	h._text(v, T.t("Die verlassene Hütte ist abgeschlossen. In der Nacht hat MoveEye beim Zelt etwas aufgenommen, das die Kamera nicht sieht."))
	if not _clip_of("k1").is_empty():
		_thumb(v, "k1")
		if bool(_part("k1").get("seen", true)):
			h._text(v, T.t("Im Wärmebild (rechts) liegt etwas Kleines, Warmes im Gras. Geh hin – mit «Erkunden» oder mit der Ansicht – und such es."), 14, UI.TXT)
		else:
			h._text(v, T.t("Der warme Fleck liegt knapp ausserhalb des Wärmebilds – ein paar Schritte vor dem Zelteingang. Geh hin – mit «Erkunden» oder mit der Ansicht – und such es."), 14, UI.TXT)
	else:
		h._text(v, T.t("Die Aufnahme dazu fehlt (Nacht übersprungen). Etwas liegt ein paar Schritte vor dem Zelt im Gras – «Hinweis» zeigt, wo."), 14, UI.TXT)
	var r: HBoxContainer = h._row(v)
	h._button(r, T.t("Suchen gehen"), _search, true)
	h._button(r, T.t("Aufnahmen"), func(): h._show_clips(reshow))
	h._button(r, T.t("Beenden"), h.stop)


func _search() -> void:
	searching = true
	h._clear_card()
	_show_bar()


func _show_bar() -> void:
	if _bar == null or not is_instance_valid(_bar):
		_bar = PanelContainer.new()
		_bar.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.92), UI.ORG, 10, 10, 1))
		h._anchor(_bar, 0.5, 1.0, 0.5, 1.0, -330, -150, 330, -86)
		h._ui.add_child(_bar)
		var hb := HBoxContainer.new()
		hb.add_theme_constant_override("separation", 10)
		_bar.add_child(hb)
		_bar_lbl = Label.new()
		_bar_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_bar_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_bar_lbl.add_theme_font_size_override("font_size", 13)
		hb.add_child(_bar_lbl)
		var b1 := Button.new()
		b1.text = T.t("Hinweis")
		b1.pressed.connect(_hint)
		hb.add_child(b1)
		var b2 := Button.new()
		b2.text = T.t("Zurück")
		b2.pressed.connect(func():
			searching = false
			_card_k1())
		hb.add_child(b2)
	_bar.visible = true
	_bar_text()


func _bar_text() -> void:
	if _bar_lbl == null:
		return
	var t := T.t("Such den kleinen warmen Fleck aus der Aufnahme – ein paar Schritte vor dem Zelt.")
	if _beacon != null and is_instance_valid(_beacon) and _beacon.visible:
		t = T.t("Ein schwacher Lichtpunkt zeigt die Stelle. Geh bis auf 2 m heran.")
	_bar_lbl.text = t


func _hide_bar() -> void:
	if _bar != null and is_instance_valid(_bar):
		_bar.visible = false


func _spieltest(art: String) -> void:
	"""Spieltest-Assistent (spieltest.gd): a hint / a wrong code of this riddle - nothing while it is off"""
	var st_ = _main().get("spieltest") if _main() != null else null
	if st_ != null and st_.on:
		preload("res://scripts/spieltest.gd").ereignis("horror", art, {"raetsel": st_.raetsel_key_horror()})


func _hint() -> void:
	_spieltest("tipp")
	match active:
		"k1":
			if _beacon != null and is_instance_valid(_beacon) and not _beacon.visible:
				_beacon.visible = true
				_bar_text()
			else:
				_found()                                             # second hint: you find it after a long search
		"k2", "k3":
			_tries = 2 if _tries < 2 else 10                         # 1st: the tip, 2nd: the solution
			_card_code(active)


func _found() -> void:
	searching = false
	_hide_bar()
	_part("k1")["found"] = true
	_save()
	var s := _strength()
	if s >= 0.25 and h._root != null:                             # (under 25 %: no scare at all)
		h._sound("whisper", h._behind(2.5), -36.0, T.t("(Flüstern, direkt hinter dir)"))
	if s >= 0.5:
		h._flicker_until = Time.get_ticks_msec() / 1000.0 + 0.6
		h._flash(0.3)
	_clear_key()
	var v: VBoxContainer = h._new_card(T.t("Gefunden"), UI.GRN, 560)
	h._text(v, T.t("Im nassen Gras liegt ein alter, schwerer Schlüssel. Am Ring ein Holzanhänger: «Hütte». Damit lässt sich die verlassene Hütte aufschliessen."))
	h._button(v, T.t("Weiter"), _done, true)


func _card_code(k: String) -> void:
	h.phase = "raetsel"
	_hide_bar()
	var v: VBoxContainer
	if k == "k2":
		v = h._new_card(T.t("Rätsel: Die Zahlen an der Wand"), UI.ORG, 620)
		h._text(v, T.t("Die Tür der Hütte ist in der Nacht zugeschlagen. Mit dem Schlüssel von gestern schliesst du auf. Drinnen an der Wand hängt ein alter Kasten mit einem Zahlenschloss: vier Ziffern."))
	else:
		v = h._new_card(T.t("Rätsel: Das Schloss am Hospiz"), UI.ORG, 620)
		h._text(v, T.t("Am Abend, bevor du zum Lager zurückgehst, stehst du vor dem alten Hospiz am Pass. Die Tür ist verschlossen. Das Schloss hat Räder wie eine Uhr: Stunden und Minuten."))
		h._text(v, T.t("«Die Glocke hilft im Nebel. Wer sie hört, soll ihr folgen.» Wann hast du die Glocke zuletzt gehört? MoveEye weiss es."), 14, Color(0.95, 0.8, 0.55), true)
	var have := not _clip_of(k).is_empty()
	if have:
		_thumb(v, k)
	var sol := _solution(k)
	if _tries >= 10 or (not have and sol != ""):
		var why := T.t("Die Aufnahme dazu fehlt (Nacht übersprungen).") + " " if not have else ""
		h._text(v, why + T.t("Die Lösung: {s}", {"s": sol}), 14, UI.ORG)
	elif _tries >= 2:
		h._text(v, T.t("Tipp: Die Aufnahme «Zahlen an der Wand» – unten im Wärmebild, vergrössert.") if k == "k2"
				else T.t("Tipp: Die Aufnahme «Die Glocke, ganz nah» aus der 2. Nacht – die Uhrzeit steht oben links und in der Liste."), 14, UI.MUT)
	var r: HBoxContainer = h._row(v)
	_entry = LineEdit.new()
	_entry.placeholder_text = T.t("4 Ziffern") if k == "k2" else T.t("HH:MM")
	_entry.max_length = 5
	_entry.custom_minimum_size = Vector2(160, 36)
	_entry.text_submitted.connect(func(_s): _try(k))
	r.add_child(_entry)
	h._button(r, T.t("Öffnen"), func(): _try(k), true)
	_msg = h._text(v, "", 14, UI.RED)
	var r2: HBoxContainer = h._row(v)
	h._button(r2, T.t("Hinweis"), _hint)
	h._button(r2, T.t("Aufnahmen"), func(): h._show_clips(reshow))
	h._button(r2, T.t("Beenden"), h.stop)
	_entry.grab_focus.call_deferred()


func _solution(k: String) -> String:
	if k == "k2":
		return str(_part("k2").get("code", ""))
	var t := str(_part("k3").get("time", ""))
	if t == "":                                                   # the recording never happened: the time of the beat
		var hh: float = h.H_START + 0.77 * h.H_HOURS
		t = "%02d:%02d" % [int(hh) % 24, int(fmod(hh, 1.0) * 60.0)]
		_part("k3")["time"] = t
		_save()
	return t


static func _minutes(s: String) -> int:
	"""«03:19», «3:19», «3.19», «0319» → minutes of the day (or -1)"""
	var d := ""
	var sep := -1
	for i in range(s.length()):
		var ch := s[i]
		if ch >= "0" and ch <= "9":
			d += ch
		elif ch in [":", ".", " ", "h"] and sep < 0:
			sep = d.length()
	if d.length() < 3 or d.length() > 4:
		return -1
	var hh := int(d.substr(0, sep if sep > 0 else d.length() - 2))
	var mm := int(d.substr(sep if sep > 0 else d.length() - 2))
	if hh > 23 or mm > 59:
		return -1
	return hh * 60 + mm


func check(k: String, s: String) -> bool:
	var sol := _solution(k)
	if k == "k2":
		return s.strip_edges().replace(" ", "") == sol
	var a := _minutes(s)
	var b := _minutes(sol)
	if a < 0 or b < 0:
		return false
	var diff := absi(a - b)
	return mini(diff, 1440 - diff) <= 1                          # ± 1 min (the clock of the night runs fast)


func _try(k: String, s = null) -> bool:
	var txt: String = str(s) if s != null else (_entry.text if _entry != null else "")
	if check(k, txt):
		_solved(k)
		return true
	_tries += 1
	_spieltest("falsch")                                          # Spieltest-Assistent: falscher Code
	if _tries == 2:
		_spieltest("tipp")                                        # (the tip comes by itself now)
		_card_code(k)                                             # with the tip now
	if _msg != null and is_instance_valid(_msg):
		_msg.text = T.t("Falsch – das Schloss bleibt zu.")
	if _entry != null and is_instance_valid(_entry):
		_entry.text = ""
	return false


func _solved(k: String) -> void:
	_part(k)["solved"] = true
	_save()
	var s := _strength()
	var v: VBoxContainer
	if k == "k2":
		if s >= 0.25 and h._hut != null:
			h._sound("creak", h._hut.global_position, -12.0, T.t("(der Kasten knarrt auf)"))
		if s >= 0.5:
			h._flash(0.35)
		if s >= 0.75:
			h._ui_play("sting", lerpf(-20.0, -8.0, s))
		v = h._new_card(T.t("Der Kasten ist offen"), UI.GRN, 600)
		h._text(v, T.t("Darin liegt eine zweite Seite aus dem Hospizbuch:"))
		h._text(v, T.t("«19. Januar 1936. Nebel. Licht ins Fenster gestellt, die Tür offen gelassen – für die, die noch kommen. – B.»"), 15, Color(0.95, 0.8, 0.55), true)
	else:
		if s >= 0.25:
			h._sound("bell", h._around(60.0), -14.0, T.t("(eine Glocke, weit weg)"))
		if s >= 0.5:
			h._flash(0.4)
		if s >= 0.75:
			h._ui_play("sting", lerpf(-20.0, -8.0, s))
		v = h._new_card(T.t("Das Hospiz ist offen"), UI.GRN, 600)
		h._text(v, T.t("Drinnen ist es kalt und still. Neben der Tür ein leerer Haken – hier hing die Glocke der Hospizwartin."))
	h._button(v, T.t("Weiter"), _done, true)


func _done() -> void:
	h.phase = "intro" if active == "k3" else "morning"           # back to the phase of bergtal_horror.gd
	active = ""
	searching = false
	_hide_bar()
	h._clear_card()
	var cb := _then
	_then = Callable()
	if cb.is_valid():
		cb.call()


func clear() -> void:
	"""the horror mode ends (stop): the world nodes go with horror._root"""
	active = ""
	searching = false
	_pending.clear()
	_hide_bar()
	_key = null
	_warm = null
	_beacon = null


# =======================================================================================================================
# /control {"action": "horror", "do": "r_…"} – tests
# =======================================================================================================================
func command(d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "r_info"))
	match what:
		"r_info":
			if st.is_empty():
				_load()
			return {"ok": true, "active": active, "searching": searching, "state": st, "key_dist": snappedf(key_dist(), 0.1),
					"near": _near_key(), "beacon": _beacon != null and is_instance_valid(_beacon) and _beacon.visible,
					"tries": _tries, "phase": h.phase, "strength": h.strength}
		"r_code":
			if active not in ["k2", "k3"]:
				return {"ok": false, "error": "no code riddle open"}
			return {"ok": _try(active, str(d.get("code", ""))), "active": active}
		"r_hint":
			if active == "k1" and not searching:
				_search()
			_hint()
			return {"ok": true, "active": active}
		"r_search":
			if active == "k1":
				_search()
			return {"ok": true, "searching": searching}
		"r_find":                                                    # as if found (same as the 2nd hint)
			if active == "k1":
				_found()
				return {"ok": true}
			return {"ok": false, "error": "no key riddle open"}
		"r_go":
			if active != "" and not searching and h._card != null:
				_done()
			return {"ok": true, "phase": h.phase}
	return {"ok": false, "error": "do: r_info | r_code | r_hint | r_search | r_find | r_go"}
