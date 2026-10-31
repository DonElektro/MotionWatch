extends Node
## Bergtal · Horror-Modus «Das Hospiz» (Daniel, 31.10.2026 05:38 / 05:44): die 5. Stimmung des Bergtal-Abenteuers als eigener,
## in sich geschlossener Modus. Oben am Pass steht das alte Hospiz: im Winter 1936 verschwand dort die Hospizwartin – Licht im
## Fenster, Tür offen, die Glocke läutete, das Haus war leer. Nie geklärt. Drei Nächte (3 Kapitel, steigende Spannung) bewacht
## MoveEye das Lager im Bergtal; erzählt wird über seltsame MoveEye-Aufnahmen, die man am Morgen in MoveEyes Verlauf findet.
##
## Schutz:
##   * Passwort: beim ersten Mal legt Daniel es hier im Simulator selbst fest. Gespeichert wird NUR ein gesalzener Hash
##     (PBKDF2-HMAC-SHA256, 12 000 Runden, 16 Byte Salz) in user://bergtal_horror.json – nie im Repository, nie im Log.
##     Danach: Passwort eingeben = entsperrt bis zum Neustart des Simulators. 5 Fehlversuche = 30 s Pause.
##     Vergessen: die Datei user://bergtal_horror.json löschen (dann wird es beim nächsten Mal neu festgelegt).
##   * Nicht im Kinder-Modus (main.kids_on). Warnhinweis vor dem Start. Esc = Pause jederzeit (heller, leiser, Zeit steht).
##   * Regler «Schreck-Stärke» (0 … 100 %): Lautstärke UND Häufigkeit der Schreckmomente (ab 25 % ein Jump-Scare pro Nacht,
##     ab 50 % zwei, ab 75 % drei). Kein Blut, keine Gewalt.
## Elemente: dichter Nebel und Dunkelheit (kein Mond, nur der Stirnlampen-Kegel), Geräusche (Schritte, Knacken, Flüstern,
## Kuhglocke ohne Kuh, Stimmen im Nebel, knarrende Tür), eine Gestalt NUR im Wärmebild (Ebene 2 = nur die Wärmebild-Kamera; das
## Kamerabild von MoveEye und das Fenster sehen nichts), verlassene Hütte (Tür geht von selbst auf, Licht im Fenster).
## Nachts: MoveEye-Alarm (PIR Zelt wie main.gd: Person < 3 m vom Zelt), im Kamerabild niemand, nur im Wärmebild. Am Morgen ist
## das Lager verändert (Rucksack / Proviant verschoben, Spuren ums Zelt, eine Laterne vor dem Zelt).
##
## Aufnahmen → MoveEye: jede «Aufnahme» ist ein Bild (links Kamerabild, rechts Wärmebild) mit Titel und Text. Der Simulator
## schickt die neuen in world_reply «horror» (schnittstelle.json), MoveEye holt das Bild über /horror_pic/<id>.jpg und legt es
## in seinen Verlauf → Nachrichten (Teil 539a, Status «Test-Postfach», nie ein echter Push). Ohne MoveEye: die eigene Ansicht
## «Aufnahmen» hier im Simulator (Startbild und Morgen).
##
## Hook für die Stimmungswahl des Abenteuers (Zweig bergtal-abenteuer, gesperrter 5. Platz «Horror»):
##   main.horror.mood_slot() -> {"id": "horror", "name": "Horror", "locked": bool, "has_password": bool, "kids": bool}
##   main.horror.open_from_mood(on_close: Callable)   # Passwort (oder beim ersten Mal festlegen) -> Warnung -> Startbild;
##                                                    # on_close.call(started: bool) wenn der Modus wieder zu ist
## Lite: _lite() (Bergtal._lite() = Bib.lite() = Engine-Meta «lite»): keine Schatten der Lampen, weniger Geräusche gleichzeitig.
## Test / Fernsteuerung: /control {"action": "horror", "do": "info" | "set_password" | "unlock" | "start" | "skip" | "pause" |
##   "resume" | "choose" | "stop" | "clip", …} (Passwort nur über "pw", wird nie ausgegeben oder geloggt).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Bergtal = preload("res://scripts/bergtal.gd")

const FILE := "user://bergtal_horror.json"
const ITER := 12000                    # PBKDF2 rounds (RFC 8018); a few 100 ms on a normal PC, once per unlock
const ENDS := ["gut", "flucht", "offen", "harmlos"]
const NIGHT_SECS := 360.0              # one night = 6 min real time (22:00 → 05:00)
const H_START := 22.0
const H_HOURS := 7.0
const HELPER_LAYER := 128              # main.HELPER_LAYER: only the window sees it, never a camera of MoveEye
const SR := 16000                      # sample rate of the generated sounds
# surface temperatures of a clothed person at night, outdoors 0 … 10 °C: clothing 24 … 30 °C, face 32 … 34 °C
# (IR thermography of skin: ≈ 33–34 °C at rest; clothing several °C lower) – the Thermal-90 shows that clearly through fog
const BODY_C := 28.5
const HEAD_C := 33.0
const PIR_DIST := 3.0                  # like main.gd: a person closer than 3 m to the tent sets off «PIR Zelt»

var main
var unlocked := false
var phase := ""                        # "" | setpw | lock | warn | start | intro | night | morning | ending | clips
var running := false                   # the world belongs to the horror (night / morning between nights)
var paused := false
var chapter := 0
var end_kind := "offen"
var strength := 0.6
var choices := {}                      # d1: follow | stay · d2: back | keep
var clips: Array = []                  # {id, t, night, hhmm, title, text, jpg, tex}
var _clip_id := 0
var _clip_pending: Array = []          # [due, title, text]
var _fails := 0
var _lock_until := 0.0
var _on_close := Callable()
var _started_once := false
var _store := {}

# night
var _t := 0.0                          # seconds of the night (pause does not count)
var _beats: Array = []
var _bi := 0
var _amb_next := 0.0
var _jumps := 0
var _saved := {}
var _bt = null
var _fog := 0.0

# world nodes
var _root: Node3D
var _fig: Node3D
var _fig_mats: Array = []
var _fig_to := Vector3.ZERO
var _fig_speed := 0.6
var _fig_face := false                 # turned to MoveEye
var _fig_fade := -1.0                  # «gut»: the figure grows cold
var _fig_pir := false
var _ghost: Node3D
var _ghost_until := 0.0
var _hut: Node3D
var _hut_door: Node3D
var _hut_light: OmniLight3D
var _hut_win: MeshInstance3D
var _door_to := 0.0
var _lamp: SpotLight3D
var _pause_light: OmniLight3D
var _flicker_until := 0.0
var _extra: Array = []                 # tracks, lantern (removed at the end)
var _moved: Array = []                 # [node, old transform]
var _hidden: Array = []                # animals of the spot hidden during the horror
var _lantern: Node3D

# sound
var _snd := {}
var _drone: AudioStreamPlayer
var _ui_snd: AudioStreamPlayer
var _players: Array = []

# window
var _layer: CanvasLayer
var _ui: Control
var _card: PanelContainer
var _hud: Control
var _hud_title: Label
var _hud_sub: Label
var _hud_alarm: Label
var _sub_until := 0.0
var _alarm_until := 0.0
var _bright: ColorRect
var _scare: ColorRect
var _pw1: LineEdit
var _pw2: LineEdit
var _msg: Label


static func _lite() -> bool:
	"""the central question «Lite?» (Brief: Engine-Meta «lite»; Bergtal._lite() → Bib.lite(); the coordinator connects it)"""
	return Bergtal._lite()


func _ready() -> void:
	_load()
	strength = clampf(float(_store.get("strength", 0.6)), 0.0, 1.0)
	var rs = _store.get("restore", null)
	if rs is Dictionary and not (rs as Dictionary).is_empty():      # the simulator was closed in the middle of a night
		_apply_restore(rs)
		_store.erase("restore")
		_save()


# =======================================================================================================================
# hook for the mood choice of the adventure + entry
# =======================================================================================================================
func mood_slot() -> Dictionary:
	return {"id": "horror", "name": T.t("Horror"), "locked": not unlocked, "has_password": has_password(),
			"kids": bool(main.get("kids_on")), "hint": T.t("Passwortgeschützt – unheimlich, mit Schreckmomenten")}


func open_from_mood(on_close := Callable()) -> void:
	_on_close = on_close
	open()


func open() -> void:
	if bool(main.get("kids_on")):
		main.start_info = T.t("Der Horror-Modus ist im Kinder-Modus gesperrt.")
		return
	_ensure_ui()
	if running:
		_set_pause(true)
		return
	if not has_password():
		_show_setpw()
	elif not unlocked:
		_show_lock()
	else:
		_show_warn()


func _close_all(started := false) -> void:
	_clear_card()
	phase = ""
	if _on_close.is_valid():
		var cb := _on_close
		_on_close = Callable()
		cb.call(started)


# =======================================================================================================================
# password: only a salted hash in user:// (never in the repository, never in the log)
# =======================================================================================================================
func _load() -> void:
	_store = {}
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if d is Dictionary:
			_store = d


func _save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(_store))
		f.close()


func has_password() -> bool:
	return str(_store.get("hash", "")).length() == 64 and str(_store.get("salt", "")).length() == 32


static func _pbkdf2(pw: String, salt: PackedByteArray, iter: int) -> PackedByteArray:
	"""PBKDF2-HMAC-SHA256, one block of 32 bytes (RFC 8018)"""
	var c := Crypto.new()
	var key := pw.to_utf8_buffer()
	var s1 := salt.duplicate()
	s1.append_array(PackedByteArray([0, 0, 0, 1]))
	var u := c.hmac_digest(HashingContext.HASH_SHA256, key, s1)
	var out := u.duplicate()
	for _i in range(iter - 1):
		u = c.hmac_digest(HashingContext.HASH_SHA256, key, u)
		for k in range(out.size()):
			out[k] = out[k] ^ u[k]
	return out


func set_password(pw: String) -> Dictionary:
	if has_password():
		return {"ok": false, "error": T.t("Das Passwort ist schon festgelegt.")}
	if pw.length() < 4:
		return {"ok": false, "error": T.t("Mindestens 4 Zeichen.")}
	var salt := Crypto.new().generate_random_bytes(16)
	_store["salt"] = salt.hex_encode()
	_store["iter"] = ITER
	_store["hash"] = _pbkdf2(pw, salt, ITER).hex_encode()
	_store["v"] = 1
	_save()
	unlocked = true
	return {"ok": true}


func unlock(pw: String) -> Dictionary:
	if not has_password():
		return {"ok": false, "error": T.t("Noch kein Passwort festgelegt.")}
	var now_: float = Time.get_ticks_msec() / 1000.0
	if now_ < _lock_until:
		return {"ok": false, "error": T.t("Zu viele Versuche – bitte {s} s warten.", {"s": int(ceil(_lock_until - now_))})}
	var h := _pbkdf2(pw, str(_store["salt"]).hex_decode(), int(_store.get("iter", ITER))).hex_encode()
	var want := str(_store["hash"])
	var diff := 0
	for i in range(64):
		diff |= h.unicode_at(i) ^ want.unicode_at(i)
	if diff != 0:
		_fails += 1
		if _fails >= 5:
			_fails = 0
			_lock_until = now_ + 30.0
		return {"ok": false, "error": T.t("Falsches Passwort.")}
	_fails = 0
	unlocked = true
	return {"ok": true}


# =======================================================================================================================
# window: cards (password, warning, start, chapter, morning, ending, recordings) and the HUD of the night
# =======================================================================================================================
func _ensure_ui() -> void:
	if _layer != null:
		return
	_layer = CanvasLayer.new()
	_layer.layer = 70
	add_child(_layer)
	_ui = Control.new()
	_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.theme = UI.theme()
	_layer.add_child(_ui)
	_bright = ColorRect.new()                                  # pause: brighter
	_bright.color = Color(0.85, 0.88, 0.92, 0.22)
	_bright.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bright.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bright.visible = false
	_ui.add_child(_bright)
	_scare = ColorRect.new()                                   # jump scare: a short dark flash
	_scare.color = Color(0, 0, 0, 0)
	_scare.set_anchors_preset(Control.PRESET_FULL_RECT)
	_scare.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_scare)
	_build_hud()
	_ui_snd = AudioStreamPlayer.new()
	add_child(_ui_snd)


func _build_hud() -> void:
	_hud = Control.new()
	_hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.visible = false
	_ui.add_child(_hud)
	_hud_title = Label.new()
	_hud_title.position = Vector2(16, 12)
	_hud_title.add_theme_font_size_override("font_size", 15)
	_hud_title.add_theme_color_override("font_color", Color(0.8, 0.84, 0.9))
	_hud_title.add_theme_color_override("font_outline_color", Color.BLACK)
	_hud_title.add_theme_constant_override("outline_size", 4)
	_hud.add_child(_hud_title)
	var box := VBoxContainer.new()                             # the two pictures of MoveEye: camera and thermal
	_anchor(box, 1.0, 0.0, 1.0, 0.0, -262, 12, -12, 12)
	box.add_theme_constant_override("separation", 4)
	_hud.add_child(box)
	for k in range(2):
		var pc := PanelContainer.new()
		pc.add_theme_stylebox_override("panel", UI.box(Color(0, 0, 0, 0.6), UI.LINE, 6, 3, 1))
		box.add_child(pc)
		var v := VBoxContainer.new()
		pc.add_child(v)
		var lb := Label.new()
		lb.text = T.t("MoveEye · Kamera") if k == 0 else T.t("MoveEye · Wärmebild")
		lb.add_theme_font_size_override("font_size", 11)
		lb.add_theme_color_override("font_color", UI.MUT)
		v.add_child(lb)
		var tr := TextureRect.new()
		tr.custom_minimum_size = Vector2(240, 135) if k == 0 else Vector2(240, 186)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		if k == 0 and main.vps.size() > 0:
			tr.texture = main.vps[0].get_texture()
		elif k == 1:
			tr.texture = main.th_preview
		v.add_child(tr)
	_hud_alarm = Label.new()
	_anchor(_hud_alarm, 0.5, 0.0, 0.5, 0.0, -300, 46, 300, 70)
	_hud_alarm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hud_alarm.add_theme_font_size_override("font_size", 16)
	_hud_alarm.add_theme_color_override("font_color", UI.RED)
	_hud_alarm.add_theme_color_override("font_outline_color", Color.BLACK)
	_hud_alarm.add_theme_constant_override("outline_size", 5)
	_hud.add_child(_hud_alarm)
	_hud_sub = Label.new()
	_anchor(_hud_sub, 0.5, 1.0, 0.5, 1.0, -340, -130, 340, -80)
	_hud_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hud_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hud_sub.add_theme_font_size_override("font_size", 17)
	_hud_sub.add_theme_color_override("font_color", Color(0.78, 0.8, 0.84))
	_hud_sub.add_theme_color_override("font_outline_color", Color.BLACK)
	_hud_sub.add_theme_constant_override("outline_size", 5)
	_hud.add_child(_hud_sub)
	var hint := Label.new()
	_anchor(hint, 0.0, 1.0, 0.0, 1.0, 16, -30, 300, -10)
	hint.text = T.t("Esc = Pause (heller, leiser)")
	hint.add_theme_font_size_override("font_size", 12)
	hint.add_theme_color_override("font_color", UI.MUT)
	_hud.add_child(hint)


func _anchor(c: Control, al: float, at: float, ar: float, ab: float, ol: float, ot: float, orr: float, ob: float) -> void:
	c.anchor_left = al
	c.anchor_top = at
	c.anchor_right = ar
	c.anchor_bottom = ab
	c.offset_left = ol
	c.offset_top = ot
	c.offset_right = orr
	c.offset_bottom = ob


func _clear_card() -> void:
	if _card != null and is_instance_valid(_card):
		_card.queue_free()
	_card = null
	_pw1 = null
	_pw2 = null
	_msg = null


func _new_card(title: String, accent := UI.ORG, width := 600) -> VBoxContainer:
	_clear_card()
	_card = PanelContainer.new()
	_card.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.96), accent, 14, 18, 2))
	_card.set_anchors_preset(Control.PRESET_CENTER)
	_card.custom_minimum_size = Vector2(width, 0)
	_ui.add_child(_card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_card.add_child(v)
	var h := Label.new()
	h.text = title
	h.add_theme_font_size_override("font_size", 22)
	h.add_theme_color_override("font_color", UI.TXT)
	v.add_child(h)
	_card.resized.connect(_center_card)
	_center_card.call_deferred()
	return v


func _center_card() -> void:
	if _card != null and is_instance_valid(_card):
		_card.position = ((_ui.size - _card.size) * 0.5).floor()


func _text(parent: Control, t: String, size := 15, col := UI.TXT, italic := false) -> Label:
	var l := Label.new()
	l.text = t
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(560, 0)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	if italic:
		var fv := FontVariation.new()
		fv.base_font = ThemeDB.fallback_font
		fv.variation_transform = Transform2D(Vector2(1, 0), Vector2(0.2, 1), Vector2.ZERO)
		l.add_theme_font_override("font", fv)
	parent.add_child(l)
	return l


func _row(parent: Control) -> HBoxContainer:
	var r := HBoxContainer.new()
	r.add_theme_constant_override("separation", 10)
	parent.add_child(r)
	return r


func _button(parent: Control, t: String, cb: Callable, primary := false) -> Button:
	var b := Button.new()
	b.text = t
	b.custom_minimum_size = Vector2(0, 38)
	if primary:
		UI.primary(b)
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func _pw_field(parent: Control, ph: String) -> LineEdit:
	var e := LineEdit.new()
	e.secret = true
	e.placeholder_text = ph
	e.custom_minimum_size = Vector2(320, 36)
	parent.add_child(e)
	return e


func _show_setpw() -> void:
	phase = "setpw"
	var v := _new_card(T.t("Horror-Modus: Passwort festlegen"), UI.ACC, 520)
	_text(v, T.t("Beim ersten Mal legst du das Passwort selbst fest. Gespeichert wird nur ein verschlüsselter Fingerabdruck (Hash) auf diesem PC – nie das Passwort selbst."), 14, UI.MUT)
	_pw1 = _pw_field(v, T.t("Neues Passwort"))
	_pw2 = _pw_field(v, T.t("Nochmals eingeben"))
	_pw2.text_submitted.connect(func(_s): _do_setpw())
	_msg = _text(v, "", 14, UI.RED)
	var r := _row(v)
	_button(r, T.t("Festlegen"), _do_setpw, true)
	_button(r, T.t("Abbrechen"), func(): _close_all())
	_pw1.grab_focus.call_deferred()


func _do_setpw() -> void:
	if _pw1 == null or _pw2 == null:
		return
	if _pw1.text != _pw2.text:
		_msg.text = T.t("Die beiden Eingaben sind nicht gleich.")
		return
	var r := set_password(_pw1.text)
	_pw1.text = ""
	_pw2.text = ""
	if not bool(r["ok"]):
		_msg.text = str(r["error"])
		return
	_show_warn()


func _show_lock() -> void:
	phase = "lock"
	var v := _new_card(T.t("Horror-Modus: gesperrt"), UI.ACC, 520)
	_text(v, T.t("Dieser Modus ist mit einem Passwort geschützt."), 14, UI.MUT)
	_pw1 = _pw_field(v, T.t("Passwort"))
	_pw1.text_submitted.connect(func(_s): _do_unlock())
	_msg = _text(v, "", 14, UI.RED)
	var r := _row(v)
	_button(r, T.t("Entsperren"), _do_unlock, true)
	_button(r, T.t("Abbrechen"), func(): _close_all())
	_pw1.grab_focus.call_deferred()


func _do_unlock() -> void:
	if _pw1 == null:
		return
	var r := unlock(_pw1.text)
	_pw1.text = ""
	if not bool(r["ok"]):
		_msg.text = str(r["error"])
		return
	_show_warn()


func _show_warn() -> void:
	phase = "warn"
	var v := _new_card(T.t("Bevor es losgeht"), UI.ORG, 600)
	_text(v, T.t("Achtung: Dieser Modus ist unheimlich und hat einige Schreckmomente – plötzliche laute Geräusche und Bilder, Dunkelheit, dichter Nebel. Kein Blut, keine Gewalt. Nicht für kleine Kinder."))
	_text(v, T.t("Esc hält jederzeit an: dann wird es heller und leiser, und die Zeit steht still. Mit dem Regler «Schreck-Stärke» stellst du Lautstärke und Häufigkeit der Schreckmomente ein."), 14, UI.MUT)
	var r := _row(v)
	_button(r, T.t("Ich habe verstanden"), _show_start, true)
	_button(r, T.t("Lieber nicht"), func(): _close_all())


func _show_start() -> void:
	phase = "start"
	var v := _new_card(T.t("Das Hospiz"), Color(0.55, 0.12, 0.12), 640)
	_text(v, T.t("Für die Mutigste."), 18, Color(0.95, 0.8, 0.55), true)
	_text(v, T.t("Oben am Pass steht das alte Hospiz. Im Winter 1936, in einer Sturmnacht, brannte im Fenster Licht, die Tür stand offen, die Glocke der Hospizwartin läutete – aber das Haus war leer. Was geschah, wurde nie geklärt."))
	_text(v, T.t("Drei Nächte lang bewacht MoveEye dein Lager im Bergtal. Was es aufnimmt, findest du am Morgen in seinem Verlauf."), 14, UI.MUT)
	_text(v, T.t("Wie soll die Geschichte enden?"), 15, UI.TXT)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	v.add_child(grid)
	var names := {"gut": T.t("Gut – die Gestalt findet Ruhe"), "flucht": T.t("Flucht – im Morgengrauen weg vom Pass"),
			"offen": T.t("Offen – manches bleibt ungeklärt"), "harmlos": T.t("Harmlos – es gibt eine einfache Erklärung")}
	var bg := ButtonGroup.new()
	var pr = _store.get("progress", {})
	if pr is Dictionary and ENDS.has(str(pr.get("end", ""))):
		end_kind = str(pr["end"])
	for k in ENDS:
		var b := Button.new()
		b.text = names[k]
		b.toggle_mode = true
		b.button_group = bg
		b.button_pressed = k == end_kind
		b.custom_minimum_size = Vector2(290, 36)
		b.pressed.connect(func(): end_kind = k)
		grid.add_child(b)
	_strength_row(v)
	var r := _row(v)
	var done := int(pr.get("done", 0)) if pr is Dictionary else 0
	if done > 0 and done < 3:
		_button(r, T.t("Weiter mit Nacht {n}", {"n": done + 1}), func(): _continue(done + 1), true)
		_button(r, T.t("Von vorne"), func(): begin(1))
	else:
		_button(r, T.t("Erste Nacht beginnen"), func(): begin(1), true)
	if not clips.is_empty():
		_button(r, T.t("Aufnahmen"), func(): _show_clips(_show_start))
	_button(r, T.t("Schliessen"), func(): _close_all())


func _continue(n: int) -> void:
	var pr = _store.get("progress", {})
	if pr is Dictionary and pr.get("choices") is Dictionary:
		choices = (pr["choices"] as Dictionary).duplicate()
	begin(n)


func _strength_row(v: Control) -> void:
	var r := _row(v)
	var lb := Label.new()
	lb.text = T.t("Schreck-Stärke")
	r.add_child(lb)
	var sl := HSlider.new()
	sl.min_value = 0
	sl.max_value = 100
	sl.step = 5
	sl.value = round(strength * 100.0)
	sl.custom_minimum_size = Vector2(260, 28)
	r.add_child(sl)
	var val := Label.new()
	val.text = "%d %%" % int(sl.value)
	r.add_child(val)
	var hint := Label.new()
	hint.add_theme_color_override("font_color", UI.MUT)
	hint.add_theme_font_size_override("font_size", 12)
	hint.text = _strength_text()
	v.add_child(hint)
	sl.value_changed.connect(func(x: float):
		set_strength(x / 100.0)
		val.text = "%d %%" % int(x)
		hint.text = _strength_text())


func _strength_text() -> String:
	if strength < 0.25:
		return T.t("leise und selten, keine Jump-Scares")
	if strength < 0.5:
		return T.t("ein Jump-Scare pro Nacht")
	if strength < 0.75:
		return T.t("zwei Jump-Scares pro Nacht")
	return T.t("laut und oft, drei Jump-Scares pro Nacht")


func set_strength(s: float) -> void:
	strength = clampf(s, 0.0, 1.0)
	_store["strength"] = strength
	_save()
	if _drone != null:
		_drone.volume_db = _amb_db()


func _input(ev: InputEvent) -> void:
	if not (ev is InputEventKey and ev.pressed and not ev.echo and (ev as InputEventKey).keycode == KEY_ESCAPE):
		return
	if running:
		_set_pause(not paused)
		get_viewport().set_input_as_handled()
	elif phase in ["setpw", "lock", "warn", "start", "clips"]:
		_close_all()
		get_viewport().set_input_as_handled()


# =======================================================================================================================
# the nights
# =======================================================================================================================
func begin(n: int) -> void:
	if n == 1:
		choices = {}
		clips.clear()
	chapter = n
	_store["progress"] = {"done": n - 1, "end": end_kind, "choices": choices}
	_save()
	if str(main.scene) != "bergtal":
		main.set_scene("bergtal")
		await get_tree().process_frame
		await get_tree().process_frame
	_bt = main.scenes.data.get("bergtal", null)
	if _bt == null:
		main.start_info = T.t("Das geht nur in der Szene Bergtal.")
		_close_all()
		return
	if not running:
		_take_world()
	_started_once = true
	_build_world()
	_make_sounds()
	_t = 0.0
	_bi = 0
	_jumps = 0
	_beats = _chapter_beats(n)
	_amb_next = randf_range(20.0, 35.0)
	main.set_hour(H_START)
	main._set_speed(0.0)
	main.weather = "fog"
	_fog = 0.03
	phase = "intro"
	running = true
	paused = false
	_hud.visible = false
	_hide_residents()
	_door_to = 0.25 if n == 2 and str(choices.get("d1", "")) == "follow" else 0.0
	if _hut_door != null:
		_hut_door.rotation.y = _door_to
	_hut_lit(false)
	if n == 3 and str(choices.get("d2", "")) == "back" and _lantern != null and is_instance_valid(_lantern):
		_lantern.queue_free()                                   # it is back in the hut
		_lantern = null
	_intro_card()


func _intro_card() -> void:
	var v := _new_card(_chapter_title(chapter), Color(0.55, 0.12, 0.12), 600)
	_text(v, _chapter_intro(chapter))
	_text(v, T.t("Halte im Wärmebild (oben rechts) die Augen offen. Mit «Erkunden» kannst du mit der Stirnlampe herumgehen."), 13, UI.MUT)
	var r := _row(v)
	_button(r, T.t("Die Nacht beginnt"), _night_go, true)
	_button(r, T.t("Beenden"), stop)


func _hide_residents() -> void:
	"""the cows, sheep … of bergtal.gd at the spot would spoil «a bell without a cow»: away while the horror runs"""
	if _bt == null:
		return
	for r in _bt._residents:
		if r is Node3D and is_instance_valid(r) and (r as Node3D).visible:
			(r as Node3D).visible = false
			(r as Node).process_mode = Node.PROCESS_MODE_DISABLED
			_hidden.append(r)


func _night_go() -> void:
	_clear_card()
	phase = "night"
	main._set_speed(H_HOURS * 3600.0 / NIGHT_SECS)
	_hud.visible = true
	if _drone != null:
		_drone.volume_db = _amb_db()
		_drone.play()


func _take_world() -> void:
	"""what the horror changes, kept for the end (and in user:// if the simulator is closed during the night)"""
	_saved = {"speed": main.speed, "weather": main.weather, "moon": main.moon, "moon_auto": main.moon_auto, "hour": main.hour(),
			"bt_events": main.bt_events}
	main.moon_auto = false
	main.moon = 0.0
	main.bt_events = false                                       # no rockfall / stranger in between
	_store["restore"] = _saved.duplicate()
	_save()


func _apply_restore(rs: Dictionary) -> void:
	main.speed = float(rs.get("speed", 1.0))
	main.weather = str(rs.get("weather", "clear"))
	main.moon = float(rs.get("moon", 0.6))
	main.moon_auto = bool(rs.get("moon_auto", true))
	main.bt_events = bool(rs.get("bt_events", true))


func stop() -> void:
	"""end the mode: everything back as before"""
	if running:
		_apply_restore(_saved)
		main.set_hour(float(_saved.get("hour", 12.0)))
		main._set_speed(float(_saved.get("speed", 1.0)))
	running = false
	paused = false
	_store.erase("restore")
	_save()
	_clear_world()
	for r in _hidden:
		if is_instance_valid(r):
			(r as Node3D).visible = true
			(r as Node).process_mode = Node.PROCESS_MODE_INHERIT
	_hidden.clear()
	_bt = null
	if _hud != null:
		_hud.visible = false
		_bright.visible = false
	if _drone != null:
		_drone.stop()
	_close_all(_started_once)


func _set_pause(on: bool) -> void:
	if not running:
		return
	paused = on
	_bright.visible = on
	if _pause_light != null:
		_pause_light.visible = on
	if on:
		_saved["speed_run"] = main.speed
		main._set_speed(0.0)
		for p in _players:
			if is_instance_valid(p):
				p.stop()
		if _drone != null:
			_drone.volume_db = -40.0
		if _ghost != null:
			_ghost.visible = false
		var v := _new_card(T.t("Pause"), UI.ACC, 520)
		_text(v, T.t("Alles ist ruhig. Die Zeit steht still. Atme durch – es geht erst weiter, wenn du willst."), 15, UI.TXT)
		_strength_row(v)
		var r := _row(v)
		_button(r, T.t("Weiter"), func(): _set_pause(false), true)
		if phase == "night":
			_button(r, T.t("Zum Morgen springen"), func():
				_set_pause(false)
				_morning())
		if not clips.is_empty():
			_button(r, T.t("Aufnahmen"), func(): _show_clips(func(): _set_pause(true)))
		_button(r, T.t("Beenden"), stop)
	else:
		_clear_card()
		if phase == "night":
			main._set_speed(float(_saved.get("speed_run", H_HOURS * 3600.0 / NIGHT_SECS)))
		if _drone != null and phase == "night":
			_drone.volume_db = _amb_db()
		if phase == "morning" or phase == "ending" or phase == "intro":
			_reshow_phase()


func _reshow_phase() -> void:
	match phase:
		"morning":
			_morning_card()
		"ending":
			_ending_card()
		"intro":
			_intro_card()


func _process(dt: float) -> void:
	if not running:
		return
	if _bt != null and (not is_instance_valid(_bt.tal) or main.scenes.data.get("bergtal", null) != _bt):
		main.start_info = T.t("Szene gewechselt – der Horror-Modus ist beendet.")
		stop()
		return
	# fog and darkness (after bergtal.gd: main → children): thick fog, brighter during the pause
	var want := 0.02 if paused else (0.03 + 0.05 * clampf(_t / 60.0, 0.0, 1.0) if phase == "night" else 0.035)
	_fog = move_toward(_fog, want, dt * 0.01)
	main.env.fog_density = maxf(main.env.fog_density, _fog)
	_tick_lamp()
	var tn := Time.get_ticks_msec() / 1000.0
	if _hud.visible:
		_hud_title.text = "%s · %s" % [_chapter_title(chapter), _hhmm()]
		_hud_sub.visible = tn < _sub_until
		_hud_alarm.visible = tn < _alarm_until
	if _scare.color.a > 0.0:
		_scare.color.a = maxf(0.0, _scare.color.a - dt * 2.5)
	if _ghost != null and _ghost.visible and tn > _ghost_until:
		_ghost.visible = false
	if paused:
		return
	_tick_door(dt)
	_tick_fig(dt)
	_tick_clips()
	if phase != "night":
		return
	_t += dt
	while _bi < _beats.size() and _t >= float(_beats[_bi][0]) * NIGHT_SECS:
		_beat(_beats[_bi])
		_bi += 1
	if _t >= _amb_next:
		_ambient()
		var f := lerpf(1.0, 0.35, strength)                      # «Häufigkeit»
		_amb_next = _t + randf_range(35.0, 70.0) * f
	if _t >= NIGHT_SECS:
		_morning()


func _hhmm() -> String:
	var h: float = main.hour()
	return "%02d:%02d" % [int(h), int(fmod(h, 1.0) * 60.0)]


# ---- the story -------------------------------------------------------------------------------------------------------
func _chapter_title(n: int) -> String:
	match n:
		1:
			return T.t("Erste Nacht – Die Glocke ohne Kuh")
		2:
			return T.t("Zweite Nacht – Das Licht im Fenster")
	return T.t("Dritte Nacht – Das Hospiz")


func _chapter_intro(n: int) -> String:
	match n:
		1:
			return T.t("Am Abend kommt der Nebel. Irgendwo im Grau läutet eine Kuhglocke. Seit Jahren sind keine Kühe mehr auf dieser Alp.")
		2:
			if str(choices.get("d1", "")) == "follow":
				return T.t("Die Spur endete gestern an der verlassenen Hütte. Heute Nacht steht ihre Tür einen Spalt offen. Und im Nebel rufen Stimmen.")
			return T.t("Du hast MoveEye höher gestellt und bleibst beim Lager. Heute Nacht rufen Stimmen im Nebel – wie Wanderer, die sich verirrt haben.")
	if str(choices.get("d2", "")) == "back":
		return T.t("Die Laterne steht wieder in der Hütte. Die letzte Nacht. Die Glocke ist jetzt ganz nah.")
	return T.t("Die Laterne steht neben deinem Zelt. Die letzte Nacht. Die Glocke ist jetzt ganz nah.")


func _chapter_beats(n: int) -> Array:
	# [part of the night, what, args]  (jump: needs strength ≥ 0.25 / 0.5 / 0.75 for the 1st / 2nd / 3rd)
	match n:
		1:
			return [[0.06, "bell", {"d": 60.0}], [0.14, "steps", {"d": 12.0}], [0.2, "fig", {"az": 28.0, "d": 22.0, "to_az": 8.0}],
					[0.25, "clip", {"k": "c1"}], [0.33, "bell", {"d": 30.0}], [0.38, "crack", {"d": 6.0}], [0.45, "jump", {}],
					[0.5, "fig", {"az": -12.0, "d": 15.0, "stand": true}], [0.53, "clip", {"k": "c2"}], [0.62, "hut_light", {"on": true}],
					[0.65, "fig_hut", {}], [0.72, "clip", {"k": "c3"}], [0.8, "whisper", {}], [0.85, "fig_tent", {}],
					[0.9, "steps", {"d": 4.0}], [0.93, "fig_away", {}], [0.97, "hut_light", {"on": false}]]
		2:
			return [[0.04, "voice", {"d": 50.0, "say": 0}], [0.1, "fig_hut", {}], [0.14, "door", {"open": true}], [0.18, "clip", {"k": "c4"}],
					[0.24, "voice", {"d": 35.0, "say": 1}], [0.3, "jump", {}], [0.36, "hut_light", {"on": true}], [0.42, "whisper", {}],
					[0.48, "fig", {"az": 20.0, "d": 9.0, "stand": true}], [0.5, "clip", {"k": "c5"}], [0.56, "door", {"open": false}],
					[0.64, "voice", {"d": 20.0, "say": 2}], [0.7, "jump", {}], [0.76, "bell", {"d": 12.0}], [0.82, "fig_tent", {}],
					[0.86, "steps", {"d": 3.0}], [0.9, "jump", {}], [0.94, "fig_away", {}], [0.97, "hut_light", {"on": false}]]
	return [[0.05, "bell", {"d": 25.0}], [0.1, "fig", {"az": 30.0, "d": 18.0, "to_az": 10.0}], [0.15, "clip", {"k": "c6"}],
			[0.22, "voice", {"d": 25.0, "say": 3}], [0.28, "whisper", {}], [0.32, "jump", {}], [0.4, "fig", {"az": -8.0, "d": 9.0}],
			[0.46, "door", {"open": true}], [0.5, "hut_light", {"on": true}], [0.55, "fig_tent", {}], [0.6, "steps", {"d": 3.0}],
			[0.64, "fig", {"az": 4.0, "d": 5.0, "stand": true, "face": true}], [0.67, "clip", {"k": "c7"}], [0.72, "jump", {}],
			[0.78, "bell", {"d": 3.0}], [0.84, "end", {}], [0.9, "jump", {}], [0.93, "clip", {"k": "c8"}]]


func _clip_text(k: String) -> Array:
	var d := snappedf(_fig_dist(), 1.0)
	match k:
		"c1":
			return [T.t("Bewegung im Nebel"), T.t("Kamera: niemand. Wärmebild: eine Gestalt, {d} m entfernt, langsam.", {"d": int(d)})]
		"c2":
			return [T.t("Glocke ohne Kuh"), T.t("Das Mikrofon hört eine Kuhglocke. Wärmebild: die Gestalt steht still und schaut zum Lager.")]
		"c3":
			return [T.t("Licht in der verlassenen Hütte"), T.t("Kamera: das Fenster ist hell. Wärmebild: vor der Tür steht jemand.")]
		"c4":
			return [T.t("Die Tür geht auf"), T.t("Die Tür der verlassenen Hütte öffnet sich von selbst. Kamera: niemand. Wärmebild: die Gestalt geht hinein.")]
		"c5":
			return [T.t("Etwas Warmes in der Hand"), T.t("Bewegung {d} m vor MoveEye – nur im Wärmebild. Sie trägt etwas Warmes: eine Laterne?", {"d": int(d)})]
		"c6":
			return [T.t("Sie kommt wieder"), T.t("Die Gestalt ist zurück, {d} m entfernt. Im Kamerabild nur Nebel.", {"d": int(d)})]
		"c7":
			return [T.t("Sie schaut in die Kamera"), T.t("{d} m. Kamera: Nebel. Wärmebild: die Gestalt steht still und schaut direkt zu MoveEye.", {"d": int(d)})]
		"c8":
			match end_kind:
				"gut":
					return [T.t("Sie wird kalt"), T.t("Im Wärmebild kühlt die Gestalt ab, bis sie nicht mehr zu sehen ist. Oben beim Hospiz läutet die Glocke ein letztes Mal.")]
				"flucht":
					return [T.t("Leeres Zelt"), T.t("Dein Zelt ist leer. Daneben steht die warme Gestalt und schaut dir nach.")]
				"harmlos":
					return [T.t("Jemand mit Glocke"), T.t("Die Gestalt geht ruhig zum Pass hinauf. Die Glocke läutet bei jedem Schritt – sie trägt sie am Gurt.")]
			return [T.t("Ganz still"), T.t("Kein Geräusch mehr. Die Gestalt ist weg. Die Aufnahme endet mitten im Bild.")]
		"alarm":
			return [T.t("Alarm am Zelt"), T.t("PIR Zelt hat ausgelöst – Kamera: niemand. Wärmebild: eine Gestalt, {d} m vor MoveEye.", {"d": int(d)})]
		"extra":
			return [T.t("Eine Aufnahme zu viel"), T.t("Diese Aufnahme trägt das Datum von morgen Nacht.")]
	return ["", ""]


func _say(i: int) -> String:
	match i:
		0:
			return T.t("Eine Stimme im Nebel: «Hallo?»")
		1:
			return T.t("Eine Stimme, näher: «Ist da jemand?»")
		2:
			return T.t("Ganz nah, im Nebel: «Hier oben … hier!»")
	return T.t("Eine leise Stimme: «Komm … zum Hospiz.»")


func _beat(b: Array) -> void:
	var a: Dictionary = b[2]
	match str(b[1]):
		"bell":
			_sound("bell", _around(float(a["d"])), -8.0, T.t("(eine Kuhglocke – aber keine Kuh)"))
		"steps":
			_sound("steps", _around(float(a["d"])), -26.0, T.t("(Schritte im nassen Gras)"))
		"crack":
			_sound("crack", _around(float(a["d"])), -14.0, T.t("(es knackt, ganz nah)"))
		"whisper":
			_sound("whisper", _behind(2.5), -34.0, T.t("(Flüstern, direkt hinter dir)"))
		"voice":
			var p := _around(float(a["d"]))
			_sound("voice%d" % (int(a["say"]) % 3), p, -10.0, _say(int(a["say"])))
			main.emit_sound("voice", 1, p)                         # MoveEye's microphone hears a voice too
		"fig":
			_fig_place(float(a["az"]), float(a["d"]), a.get("to_az", null), bool(a.get("stand", false)), bool(a.get("face", false)))
		"fig_hut":
			if _hut != null:
				_fig_walk(_hut.global_position + _hut.global_transform.basis * Vector3(0, 0, 3.6), 0.9)
		"fig_tent":
			var tf := _tent_front()
			_fig_show()
			if _fig.global_position.distance_to(tf) > 9.0:        # out of the fog, 8 m before the tent (≈ 10 s to the PIR)
				var o := Vector3(tf.x, 0, tf.z).normalized() if Vector2(tf.x, tf.z).length() > 0.1 else Vector3(0, 0, -1)
				var st := tf + o * 8.0
				st.y = main.ground_y(st.x, st.z)
				_fig.global_position = st
			_fig_walk(tf, 0.8)
		"fig_away":
			_fig_walk(_around(45.0), 1.1)
		"hut_light":
			_hut_lit(bool(a["on"]))
			if bool(a["on"]):
				_sub(T.t("(in der verlassenen Hütte geht ein Licht an)"))
		"door":
			_door_to = 1.6 if bool(a["open"]) else 0.0
			var hp: Vector3 = _hut.global_position if _hut != null else _around(40.0)
			_sound("creak" if bool(a["open"]) else "slam", hp, -10.0 if bool(a["open"]) else -4.0,
					T.t("(eine Tür knarrt – von selbst)") if bool(a["open"]) else T.t("(eine Tür schlägt zu)"))
		"jump":
			_jump()
		"clip":
			var ct := _clip_text(str(a["k"]))
			_clip_later(ct[0], ct[1], 1.2)
		"end":
			_end_beat()


func _ambient() -> void:
	"""between the beats: small things of the night (how often: «Schreck-Stärke»)"""
	var r := randf()
	if r < 0.3:
		_sound("crack", _around(randf_range(8.0, 25.0)), -18.0, T.t("(ein Ast knackt)"))
	elif r < 0.55:
		_sound("steps", _around(randf_range(10.0, 30.0)), -28.0, T.t("(Schritte – oder der Wind?)"))
	elif r < 0.8:
		_sound("bell", _around(randf_range(40.0, 90.0)), -12.0, T.t("(eine Glocke, weit weg)"))
	elif strength > 0.4:
		_sound("whisper", _behind(3.0), -36.0, T.t("(Flüstern)"))


func _end_beat() -> void:
	match end_kind:
		"gut":
			_fig_place(0.0, 6.0, null, true, true)
			_fig_fade = 0.0
			_sound("bell", _around(120.0), -6.0, T.t("(oben beim Hospiz läutet eine Glocke – ruhig, ein letztes Mal)"))
		"flucht":
			var bp := _bed_pos()
			_fig_show()
			_fig_walk(bp + (bp - Vector3.ZERO).normalized() * 1.6, 0.9)
			_sub(T.t("Das Wärmebild zeigt sie direkt hinter dem Zelt. Lauf – zur Passstrasse!"), 6.0)
			_flash(0.5)
		"harmlos":
			_fig_place(-20.0, 8.0, -60.0, false, false)
			_sound("bell", _fig.global_position, -10.0, T.t("(die Glocke läutet bei jedem Schritt der Gestalt)"), _fig)
		_:
			_fig_hide()
			if _drone != null:
				_drone.volume_db = -40.0
			_sub(T.t("(plötzlich ist es ganz still)"), 5.0)


# ---- morning ---------------------------------------------------------------------------------------------------------
func _morning() -> void:
	phase = "morning"
	_hud.visible = false
	if _drone != null:
		_drone.stop()
	for p in _players:
		if is_instance_valid(p):
			p.stop()
	if _bt != null:
		_bt._was_dark = false                                   # (not bergtal.gd's own morning rating)
	main._set_speed(1.0)
	main.set_hour(8.2)
	main.weather = "cloudy" if chapter == 3 and end_kind in ["gut", "harmlos"] else "fog"
	_fig_hide()
	_hut_lit(false)
	_camp_changes()
	if chapter == 3 and end_kind == "offen":
		if _lantern != null and is_instance_valid(_lantern):
			_lantern.queue_free()                               # «die Laterne ist weg»
			_lantern = null
		var ct := _clip_text("extra")
		_clip_now(ct[0], ct[1])
	_store["progress"] = {"done": chapter, "end": end_kind, "choices": choices}
	_save()
	if chapter >= 3:
		phase = "ending"
		_ending_card()
	else:
		_morning_card()


func _night_clips() -> int:
	return clips.filter(func(c): return int(c["night"]) == chapter).size()


func _morning_card() -> void:
	var v := _new_card(T.t("Morgen nach der {n}. Nacht", {"n": chapter}), UI.ORG, 640)
	if chapter == 1:
		_text(v, T.t("Rund ums Zelt sind Spuren im feuchten Boden. Dein Rucksack liegt einen Meter weiter weg als gestern Abend."))
	else:
		_text(v, T.t("Vor dem Zelt steht eine alte Sturmlaterne. Sie ist noch warm. Eingeritzt: «B. 1936 · Hospiz». Der Proviantsack liegt am Zelteingang."))
	_text(v, T.t("MoveEye hat in der Nacht {n} Aufnahmen gemacht – im Kamerabild ist niemand, nur im Wärmebild. Schau in MoveEyes Verlauf (Nachrichten) oder hier unter «Aufnahmen».", {"n": _night_clips()}), 14, UI.MUT)
	if chapter == 1:
		_text(v, T.t("Was machst du?"), 15)
		var r := _row(v)
		_button(r, T.t("Der Spur folgen (zur Hütte)"), func(): _choose("d1", "follow"), true)
		_button(r, T.t("Beim Lager bleiben"), func(): _choose("d1", "stay"))
	else:
		_text(v, T.t("Was machst du mit der Laterne?"), 15)
		var r2 := _row(v)
		_button(r2, T.t("Zurück in die Hütte bringen"), func(): _choose("d2", "back"), true)
		_button(r2, T.t("Behalten"), func(): _choose("d2", "keep"))
	var r3 := _row(v)
	_button(r3, T.t("Aufnahmen"), func(): _show_clips(_morning_card))
	_button(r3, T.t("Beenden"), stop)


func _choose(k: String, val: String) -> void:
	choices[k] = val
	_store["progress"] = {"done": chapter, "end": end_kind, "choices": choices}
	_save()
	if k == "d1" and val == "follow":
		var v := _new_card(T.t("In der verlassenen Hütte"), UI.ORG, 600)
		_text(v, T.t("Die Spur führt zur Hütte. Drinnen riecht es nach kaltem Rauch. Auf dem Tisch liegt eine Seite aus einem alten Hospizbuch:"))
		_text(v, T.t("«18. Januar 1936. Sturm. Zwei Wanderer über den Pass geholt. Die Glocke hilft im Nebel. Wer sie hört, soll ihr folgen. – B.»"), 15, Color(0.95, 0.8, 0.55), true)
		_button(v, T.t("Zur nächsten Nacht"), func(): begin(chapter + 1), true)
		return
	if k == "d1":
		var v2 := _new_card(T.t("Beim Lager"), UI.ORG, 600)
		_text(v2, T.t("Du stellst MoveEye höher und bleibst wach. Gegen Mittag weht der Wind eine vergilbte Seite gegen dein Zelt:"))
		_text(v2, T.t("«18. Januar 1936. Sturm. Zwei Wanderer über den Pass geholt. Die Glocke hilft im Nebel. Wer sie hört, soll ihr folgen. – B.»"), 15, Color(0.95, 0.8, 0.55), true)
		_button(v2, T.t("Zur nächsten Nacht"), func(): begin(chapter + 1), true)
		return
	begin(chapter + 1)


func _ending_card() -> void:
	var titles := {"gut": T.t("Ende: Ruhe am Pass"), "flucht": T.t("Ende: Flucht im Morgengrauen"), "offen": T.t("Ende: Ungeklärt"),
			"harmlos": T.t("Ende: Die Erklärung")}
	var v := _new_card(str(titles.get(end_kind, "")), Color(0.55, 0.12, 0.12), 660)
	match end_kind:
		"gut":
			_text(v, T.t("Um vier Uhr stand die Gestalt still neben dem Zelt, lange. Dann läutete oben beim Hospiz die Glocke, und im Wärmebild wurde sie langsam kalt, bis sie verschwand."))
			if str(choices.get("d2", "")) == "back":
				_text(v, T.t("Am Morgen ist der Nebel weg. Im Fenster des Hospizes steht die Laterne, die du zurückgebracht hast."))
			else:
				_text(v, T.t("Am Morgen ist der Nebel weg. Die Laterne neben deinem Zelt ist erloschen – zum ersten Mal kalt."))
			_text(v, T.t("Die Hospizwartin holte in Sturmnächten Verirrte über den Pass. Vielleicht hat sie nur nachgeschaut, ob du sicher bist."), 15, Color(0.95, 0.8, 0.55), true)
		"flucht":
			_text(v, T.t("Kurz vor fünf: das Wärmebild zeigt sie direkt hinter dem Zelt. Du packst nichts mehr ein, du rennst – der Kegel der Stirnlampe springt über die Steine, hinunter zur Passstrasse."))
			_text(v, T.t("Dort: Scheinwerfer, das Dreiklang-Horn des ersten Postautos. Geschafft."))
			_text(v, T.t("MoveEyes letzte Aufnahme zeigt dein leeres Zelt – und daneben eine warme Gestalt, die dir nachschaut."), 15, Color(0.95, 0.8, 0.55), true)
		"harmlos":
			_text(v, T.t("Am Morgen klopft jemand ans Zelt: ein alter Mann in dunklem Lodenmantel, eine Kuhglocke am Gurt. «Ich bin der Enkel der Hospizwartin», sagt er. «In Nebelnächten gehe ich mit ihrer Glocke über den Pass – wie sie damals, für die Verirrten.»"))
			_text(v, T.t("Darum sah ihn MoveEyes Kamera nicht: dunkler Mantel, dichter Nebel, kein Licht. Das Wärmebild schon. Die Spuren sind von ihm, und den Rucksack hat er aus dem Bach geholt."))
			_text(v, T.t("Für MoveEye heisst das: im Nebel sieht das Wärmebild, was die Kamera nicht sieht."), 15, Color(0.95, 0.8, 0.55), true)
		_:
			_text(v, T.t("Am Morgen ist alles ruhig. Das Lager ist, wie du es verlassen hast – fast. Die Laterne ist weg."))
			_text(v, T.t("In MoveEyes Verlauf ist eine Aufnahme mehr, als in der Nacht passiert ist. Sie trägt das Datum von morgen Nacht."))
			_text(v, T.t("Was im Hospiz geschah, bleibt ungeklärt."), 15, Color(0.95, 0.8, 0.55), true)
	_text(v, T.t("Für die Mutigste – du hast alle drei Nächte überstanden."), 14, UI.MUT, true)
	var r := _row(v)
	_button(r, T.t("Aufnahmen"), func(): _show_clips(_ending_card))
	_button(r, T.t("Fertig"), stop, true)


func _show_clips(back: Callable) -> void:
	var was := phase
	phase = "clips" if not running else was
	var v := _new_card(T.t("Aufnahmen (MoveEye)"), UI.ACC, 720)
	_text(v, T.t("Diese Aufnahmen hat MoveEye auch in seinen Verlauf gelegt (Nachrichten, als Test – kein echter Push)."), 13, UI.MUT)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(680, 420)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 10)
	sc.add_child(list)
	for i in range(clips.size() - 1, -1, -1):
		var c: Dictionary = clips[i]
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		list.add_child(row)
		var tr := TextureRect.new()
		tr.texture = c.get("tex", null)
		tr.custom_minimum_size = Vector2(300, 116)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(tr)
		var tv := VBoxContainer.new()
		row.add_child(tv)
		var h := Label.new()
		h.text = "%s · %s · %s" % [T.t("Nacht {n}", {"n": int(c["night"])}), str(c["hhmm"]), str(c["title"])]
		h.add_theme_color_override("font_color", UI.TXT)
		tv.add_child(h)
		var tx := Label.new()
		tx.text = str(c["text"])
		tx.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		tx.custom_minimum_size = Vector2(360, 0)
		tx.add_theme_font_size_override("font_size", 13)
		tx.add_theme_color_override("font_color", UI.MUT)
		tv.add_child(tx)
	if clips.is_empty():
		_text(list, T.t("Noch keine Aufnahmen."), 14, UI.MUT)
	_button(v, T.t("Zurück"), back, true)


# =======================================================================================================================
# the world: abandoned hut, figure (thermal only), ghost (window only), headlamp, tracks
# =======================================================================================================================
func _fwd() -> Vector3:
	"""where the head of MoveEye looks (flat)"""
	var f := Vector3(0, 0, -1)
	if main.cams.size() > 2:
		f = -(main.cams[2] as Camera3D).global_transform.basis.z
	f.y = 0.0
	return f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)


func _at(az: float, d: float) -> Vector3:
	var p := _fwd().rotated(Vector3.UP, -deg_to_rad(az)) * d
	return Vector3(p.x, main.ground_y(p.x, p.z), p.z)


func _around(d: float) -> Vector3:
	var a := randf() * TAU
	var p := Vector3(sin(a) * d, 0, cos(a) * d)
	p.y = main.ground_y(p.x, p.z) + 1.0
	return p


func _behind(d: float) -> Vector3:
	var cam: Camera3D = main.view_cam
	return cam.global_position + cam.global_transform.basis.z * d + Vector3(randf_range(-0.6, 0.6), -0.2, 0)


func _bed_pos() -> Vector3:
	if _bt != null and _bt._bed_node != null and is_instance_valid(_bt._bed_node) and _bt._bed_node.is_inside_tree():
		return _bt._bed_node.global_position
	return Vector3(2.4, main.ground_y(2.4, 2.2), 2.2)


func _tent_front() -> Vector3:
	"""a point 2.3 m from the tent (the PIR goes off) that the thermal camera of MoveEye sees best"""
	var bp := _bed_pos()
	var f := _fwd()
	var best := bp + Vector3(0, 0, -2.3)
	var bd := -9.0
	for k in range(16):
		var a := TAU * k / 16.0
		var q := bp + Vector3(cos(a), 0, sin(a)) * 2.3
		var fl := Vector2(q.x, q.z)
		if fl.length() < 1.5:
			continue
		var sc := Vector3(q.x, 0, q.z).normalized().dot(f)
		if sc > bd:
			bd = sc
			best = q
	return best


func _build_world() -> void:
	if _root != null and is_instance_valid(_root) and _root.is_inside_tree():
		return
	_clear_world()
	_root = Node3D.new()
	_root.name = "horror"
	main.scene_parent.add_child(_root)
	_build_hut()
	_build_fig()
	_build_ghost()
	_lamp = SpotLight3D.new()                                  # the headlamp of the player (if bergtal.gd's is not on)
	_lamp.spot_range = 22.0
	_lamp.spot_angle = 20.0
	_lamp.light_energy = 2.2
	_lamp.light_color = Color(1.0, 0.95, 0.88)
	_lamp.shadow_enabled = not _lite()
	main.view_cam.add_child(_lamp)
	_pause_light = OmniLight3D.new()                           # the pause: brighter
	_pause_light.omni_range = 45.0
	_pause_light.light_energy = 1.6
	_pause_light.light_color = Color(0.95, 0.95, 1.0)
	_pause_light.shadow_enabled = false
	_pause_light.visible = false
	main.view_cam.add_child(_pause_light)


func _clear_world() -> void:
	for mv in _moved:
		if is_instance_valid(mv[0]):
			(mv[0] as Node3D).global_transform = mv[1]
	_moved.clear()
	for n in [_root, _lamp, _pause_light]:
		if n != null and is_instance_valid(n):
			n.queue_free()
	_root = null
	_lamp = null
	_pause_light = null
	_fig = null
	_ghost = null
	_hut = null
	_hut_door = null
	_hut_light = null
	_extra.clear()
	_players.clear()
	_fig_mats.clear()


func _tick_lamp() -> void:
	if _lamp == null:
		return
	var other: bool = _bt != null and _bt._headlamp != null and is_instance_valid(_bt._headlamp) and _bt._headlamp.visible
	_lamp.visible = not other and main.is_dark()
	var e := 2.2
	if Time.get_ticks_msec() / 1000.0 < _flicker_until:
		e = 2.2 * (0.15 if randf() < 0.5 else 1.0)
	_lamp.light_energy = e


func _hut_spot() -> Transform3D:
	"""a flat place 30 … 45 m away, a little to the side of where MoveEye looks (not in water)"""
	var best := Transform3D.IDENTITY
	var bd := 1e9
	for az in [32.0, -30.0, 45.0, -45.0, 20.0, 60.0, -60.0]:
		for d in [38.0, 32.0, 45.0]:
			var c := _at(az, d)
			var hs := []
			for q in [Vector2(-3, -3), Vector2(3, -3), Vector2(-3, 3), Vector2(3, 3)]:
				hs.append(main.ground_y(c.x + q.x, c.z + q.y))
			var sp: float = hs.max() - hs.min()
			var wet := false
			if _bt != null:
				var vq: Vector3 = _bt.V(c)
				wet = Bergtal.zone(vq.x, vq.z) in ["lake", "shore", "glacier"]
			var score := sp + (100.0 if wet else 0.0) + absf(az) * 0.01
			if score < bd:
				bd = score
				var look := (-c).normalized()
				look.y = 0.0
				best = Transform3D(Basis.looking_at(-look.normalized(), Vector3.UP), Vector3(c.x, hs.min(), c.z))
	return best


func _build_hut() -> void:
	_hut = Node3D.new()
	_root.add_child(_hut)
	_hut.global_transform = _hut_spot()                     # its front (+z) looks to MoveEye
	var stone: StandardMaterial3D = main.mat(Color(0.36, 0.35, 0.33))
	var wood: StandardMaterial3D = main.mat(Color(0.2, 0.15, 0.1))
	var roof: StandardMaterial3D = main.mat(Color(0.16, 0.16, 0.17))
	main.add_mesh(_hut, main.box(6.0, 2.6, 0.5), Vector3(0, 1.3, -2.25), stone, "stone")
	main.add_mesh(_hut, main.box(0.5, 2.6, 5.0), Vector3(-2.75, 1.3, 0), stone, "stone")
	main.add_mesh(_hut, main.box(0.5, 2.6, 5.0), Vector3(2.75, 1.3, 0), stone, "stone")
	main.add_mesh(_hut, main.box(2.1, 2.6, 0.5), Vector3(-1.95, 1.3, 2.25), stone, "stone")     # front: door gap at x ≈ -0.4
	main.add_mesh(_hut, main.box(2.6, 2.6, 0.5), Vector3(1.7, 1.3, 2.25), stone, "stone")      # window in it (x 1.5)
	main.add_mesh(_hut, main.box(1.0, 0.6, 0.5), Vector3(-0.4, 2.3, 2.25), stone, "stone")
	main.add_mesh(_hut, main.box(6.6, 0.18, 3.4), Vector3(0, 3.2, -1.2), roof, "stone", Vector3(deg_to_rad(28), 0, 0))
	main.add_mesh(_hut, main.box(6.6, 0.18, 3.4), Vector3(0, 3.2, 1.2), roof, "stone", Vector3(deg_to_rad(-28), 0, 0))
	_hut_door = Node3D.new()                                   # the hinge at the left of the door
	_hut_door.position = Vector3(-0.9, 0, 2.3)
	_hut.add_child(_hut_door)
	main.add_mesh(_hut_door, main.box(1.0, 2.0, 0.08), Vector3(0.5, 1.0, 0), wood, "tree")
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.05, 0.05, 0.05)
	wm.emission_enabled = true
	wm.emission = Color(1.0, 0.7, 0.35)
	wm.emission_energy_multiplier = 0.0
	_hut_win = MeshInstance3D.new()
	_hut_win.mesh = main.box(0.8, 0.6, 0.52)
	_hut_win.position = Vector3(1.5, 1.5, 2.25)
	_hut_win.material_override = wm
	_hut_win.layers = 1
	_hut.add_child(_hut_win)
	_hut_light = OmniLight3D.new()
	_hut_light.position = Vector3(1.4, 1.5, 1.2)
	_hut_light.omni_range = 9.0
	_hut_light.light_color = Color(1.0, 0.68, 0.32)
	_hut_light.light_energy = 0.0
	_hut_light.shadow_enabled = false
	_hut.add_child(_hut_light)


func _hut_lit(on: bool) -> void:
	if _hut_win == null:
		return
	(_hut_win.material_override as StandardMaterial3D).emission_energy_multiplier = 2.5 if on else 0.0
	_hut_light.light_energy = 1.4 if on else 0.0


func _tick_door(dt: float) -> void:
	if _hut_door == null:
		return
	var cur := _hut_door.rotation.y
	var tgt := _door_to
	if tgt == 0.0 and cur > 0.05:
		_hut_door.rotation.y = maxf(0.0, cur - dt * 6.0)        # slams
	else:
		_hut_door.rotation.y = move_toward(cur, tgt, dt * 0.45)  # opens slowly by itself


func _thermal_part(parent: Node3D, mesh: Mesh, p: Vector3, temp: float) -> void:
	"""a part ONLY the thermal camera sees (layer 2)"""
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = p
	var mt := (main.tmat_fixed(temp) as ShaderMaterial).duplicate() as ShaderMaterial
	mi.material_override = mt
	mi.layers = 2
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	_fig_mats.append([mt, temp])


func _capsule(r: float, h: float) -> CapsuleMesh:
	var c := CapsuleMesh.new()
	c.radius = r
	c.height = h
	c.radial_segments = 10
	c.rings = 4
	return c


func _build_fig() -> void:
	_fig = Node3D.new()
	_root.add_child(_fig)
	_thermal_part(_fig, _capsule(0.2, 0.9), Vector3(0, 1.15, 0), BODY_C)            # body (a long coat)
	_thermal_part(_fig, _capsule(0.24, 0.8), Vector3(0, 0.62, 0), BODY_C - 2.0)     # coat below
	_thermal_part(_fig, _capsule(0.07, 0.62), Vector3(-0.27, 1.12, 0.02), BODY_C - 1.0)
	_thermal_part(_fig, _capsule(0.07, 0.62), Vector3(0.27, 1.12, 0.02), BODY_C - 1.0)
	var hd := SphereMesh.new()
	hd.radius = 0.12
	hd.height = 0.25
	_thermal_part(_fig, hd, Vector3(0, 1.72, 0), HEAD_C)
	_fig.visible = false


func _fig_show() -> void:
	if _fig != null:
		if not _fig.visible:
			_fig.global_position = _at(randf_range(-40.0, 40.0), 25.0)
		_fig.visible = true
		_fig_fade = -1.0
		_fig_temp(1.0)


func _fig_hide() -> void:
	if _fig != null:
		_fig.visible = false
	_fig_pir = false


func _fig_temp(k: float) -> void:
	"""k = 1: warm; k → 0: as cold as the night (the figure fades in the thermal picture)"""
	var amb: float = main.ambient
	for fm in _fig_mats:
		(fm[0] as ShaderMaterial).set_shader_parameter("temp", lerpf(amb, float(fm[1]), k))


func _fig_place(az: float, d: float, to_az, stand: bool, face: bool) -> void:
	if _fig == null:
		return
	_fig.visible = true
	_fig_fade = -1.0
	_fig_temp(1.0)
	_fig.global_position = _at(az, d)
	_fig_face = face
	_fig_to = _fig.global_position
	if to_az != null and not stand:
		_fig_walk(_at(float(to_az), d), 0.5)


func _fig_walk(to: Vector3, spd: float) -> void:
	if _fig == null:
		return
	_fig.visible = true
	_fig_to = to
	_fig_speed = spd
	_fig_face = false


func _fig_dist() -> float:
	return _fig.global_position.length() if _fig != null else 0.0


func _tick_fig(dt: float) -> void:
	if _fig == null or not _fig.visible:
		return
	var p := _fig.global_position
	var d := Vector3(_fig_to.x - p.x, 0, _fig_to.z - p.z)
	if d.length() > 0.1:
		var st := d.normalized() * minf(d.length(), _fig_speed * dt)
		p += st
		_fig.rotation.y = atan2(d.x, d.z)
	elif _fig_face:
		_fig.rotation.y = atan2(-p.x, -p.z)
	p.y = main.ground_y(p.x, p.z)
	_fig.global_position = p
	if _fig_fade >= 0.0:
		_fig_fade += dt / 25.0
		_fig_temp(1.0 - _fig_fade)
		if _fig_fade >= 1.0:
			_fig_hide()
	# the PIR at the tent (like main.gd: a person closer than 3 m) – MoveEye's alarm, the camera sees nobody
	var near := p.distance_to(main.obj.get("pir", _bed_pos())) < PIR_DIST
	if near and not _fig_pir and phase == "night":
		main.add_event("PIR Zelt", "pir")
		_alarm(T.t("MoveEye: Alarm – PIR Zelt. Im Kamerabild: niemand."))
		var ct := _clip_text("alarm")
		_clip_later(ct[0], ct[1], 0.8)
	_fig_pir = near


func _build_ghost() -> void:
	"""the jump scare: a dark shape in the cone of the headlamp – only the window sees it (HELPER_LAYER), never MoveEye"""
	_ghost = Node3D.new()
	_root.add_child(_ghost)
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.03, 0.03, 0.035)
	m.roughness = 1.0
	for part in [[_capsule(0.26, 1.5), Vector3(0, 0.85, 0)], [_capsule(0.14, 0.32), Vector3(0, 1.72, 0)]]:
		var mi := MeshInstance3D.new()
		mi.mesh = part[0]
		mi.position = part[1]
		mi.material_override = m
		mi.layers = HELPER_LAYER
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_ghost.add_child(mi)
	_ghost.visible = false


func _jump() -> void:
	_jumps += 1
	var need: float = [0.25, 0.5, 0.75][mini(_jumps - 1, 2)]
	if strength < need:
		return
	var cam: Camera3D = main.view_cam
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var p := cam.global_position + f * 3.2
	p.y = main.ground_y(p.x, p.z)
	if _ghost != null:
		_ghost.global_position = p
		_ghost.rotation.y = atan2(-f.x, -f.z)
		_ghost.visible = true
		_ghost_until = Time.get_ticks_msec() / 1000.0 + 0.45
	_flicker_until = Time.get_ticks_msec() / 1000.0 + 0.7
	_flash(0.55)
	_ui_play("sting", lerpf(-16.0, -2.0, strength))


func _flash(a: float) -> void:
	if _scare != null:
		_scare.color.a = a * (0.5 + 0.5 * strength)


func _camp_changes() -> void:
	"""the morning: things moved, tracks around the tent (chapter 2+: the lantern of the hut in front of the tent)"""
	if _bt == null or _root == null:
		return
	var moves := []
	if chapter == 1 and _bt._pack_node != null:
		moves.append([_bt._pack_node, Vector3(-0.9, 0, 0.5), 1.1])
	if chapter >= 2 and _bt._food_node != null:
		moves.append([_bt._food_node, _bed_pos() + Vector3(0.6, 0, -0.9) - (_bt._food_node as Node3D).global_position, 0.6])
	for mv in moves:
		var n: Node3D = mv[0]
		if not is_instance_valid(n) or not n.is_inside_tree():
			continue
		if not _moved.any(func(x): return x[0] == n):
			_moved.append([n, n.global_transform])
		var p: Vector3 = n.global_position + (mv[1] as Vector3)
		p.y = main.ground_y(p.x, p.z)
		n.global_position = p
		n.rotate_y(float(mv[2]))
	var bp := _bed_pos()
	var mud: StandardMaterial3D = main.mat(Color(0.12, 0.11, 0.09))
	var fp := CylinderMesh.new()
	fp.top_radius = 0.07
	fp.bottom_radius = 0.07
	fp.height = 0.012
	fp.radial_segments = 8
	var n_steps := 14 if chapter == 1 else 22
	for i in range(n_steps):
		var a := TAU * float(i) / float(n_steps) + chapter
		var r := 2.0 + 0.25 * sin(i * 1.7)
		var side := 0.12 if i % 2 == 0 else -0.12
		var dir := Vector3(cos(a), 0, sin(a))
		var q := bp + dir * (r + side)
		q.y = main.ground_y(q.x, q.z) + 0.006
		var mi: MeshInstance3D = main.add_mesh(_root, fp, q, mud, "ground", Vector3(0, -a, 0), Vector3(1.0, 1.0, 1.9))
		_extra.append(mi)
	if chapter == 2:                                           # the lantern of the hut stands in front of the tent – still warm
		var ln := Node3D.new()
		_lantern = ln
		_root.add_child(ln)
		var lp := bp + (Vector3.ZERO - bp).normalized() * 1.3
		lp.y = main.ground_y(lp.x, lp.z)
		ln.global_position = lp
		main.add_mesh(ln, main.box(0.16, 0.24, 0.16), Vector3(0, 0.14, 0), main.mat(Color(0.25, 0.22, 0.18)), 40.0)
		main.add_mesh(ln, main.box(0.06, 0.06, 0.06), Vector3(0, 0.3, 0), main.mat(Color(0.15, 0.15, 0.15)), 30.0)
		_extra.append(ln)


# =======================================================================================================================
# recordings for MoveEye (world_reply «horror», /horror_pic/<id>.jpg) and for the own view «Aufnahmen»
# =======================================================================================================================
func _clip_later(title: String, text: String, secs: float) -> void:
	if _fig != null and _fig.visible:
		main._th_asked = main.now()                                 # the thermal picture is drawn now (a fresh frame)
	_clip_pending.append([Time.get_ticks_msec() / 1000.0 + secs, title, text])


func _tick_clips() -> void:
	var tn := Time.get_ticks_msec() / 1000.0
	for i in range(_clip_pending.size() - 1, -1, -1):
		if tn >= float(_clip_pending[i][0]):
			var c: Array = _clip_pending[i]
			_clip_pending.remove_at(i)
			_clip_now(c[1], c[2])


func _clip_now(title: String, text: String) -> Dictionary:
	var img := _clip_image()
	_clip_id += 1
	var c := {"id": _clip_id, "t": Time.get_unix_time_from_system(), "night": chapter, "hhmm": _hhmm(), "title": title,
			"text": text, "jpg": img.save_jpg_to_buffer(0.82), "tex": ImageTexture.create_from_image(img)}
	clips.append(c)
	if clips.size() > 24:
		clips.pop_front()
	_sub(T.t("(MoveEye hat etwas aufgenommen: «{t}»)", {"t": title}), 3.0)
	return c


func _clip_image() -> Image:
	"""left: the camera picture of MoveEye (nobody), right: the thermal picture (the figure) – 640 × 248"""
	var out := Image.create(640, 248, false, Image.FORMAT_RGB8)
	out.fill(Color(0.02, 0.02, 0.025))
	var cam: Image = null
	if main.vps.size() > 0:
		cam = (main.vps[0] as SubViewport).get_texture().get_image()
	if cam != null and not cam.is_empty():
		cam.convert(Image.FORMAT_RGB8)
		cam.resize(316, 178, Image.INTERPOLATE_BILINEAR)
		out.blit_rect(cam, Rect2i(0, 0, 316, 178), Vector2i(2, 35))
	else:
		for y in range(35, 213):
			for x in range(2, 318):
				var g := randf() * 0.06
				out.set_pixel(x, y, Color(g, g, g))
	var th: PackedFloat32Array = main.thermal
	var tw: int = main.TH_W
	var thh: int = main.TH_H
	var ti := Image.create(tw, thh, false, Image.FORMAT_RGB8)
	if th.size() == tw * thh:
		var lo := 1e9
		var hi := -1e9
		for v in th:
			lo = minf(lo, v)
			hi = maxf(hi, v)
		var span := maxf(4.0, hi - lo)
		for y in range(thh):
			for x in range(tw):
				ti.set_pixel(x, y, main._inferno((th[y * tw + x] - lo) / span))
	else:
		ti.fill(Color(0.1, 0.02, 0.2))
	ti.resize(316, 244, Image.INTERPOLATE_BILINEAR)
	out.blit_rect(ti, Rect2i(0, 0, 316, 244), Vector2i(322, 2))
	for y in range(8, 18):                                         # the red «REC» dot
		for x in range(8, 18):
			if Vector2(x - 12.5, y - 12.5).length() < 5.0:
				out.set_pixel(x, y, Color(0.9, 0.1, 0.1))
	return out


func reply():
	"""world_reply «horror»: the new recordings of the last 10 min (MoveEye 539a puts them into its Verlauf) or null"""
	if clips.is_empty():
		return null
	var t := Time.get_unix_time_from_system()
	var out := []
	for c in clips.slice(-6):
		if t - float(c["t"]) < 600.0:
			out.append({"id": c["id"], "t": int(c["t"]), "night": c["night"], "time": c["hhmm"], "title": c["title"], "text": c["text"]})
	return out if not out.is_empty() else null


func pic(id: int) -> PackedByteArray:
	for c in clips:
		if int(c["id"]) == id:
			return c["jpg"]
	return PackedByteArray()


# =======================================================================================================================
# sounds (generated, no files): steps, cracking, whispering, cowbell, voices, door, sting, the drone of the night
# =======================================================================================================================
func _amb_db() -> float:
	return lerpf(-34.0, -18.0, strength)


func _vol(db: float) -> float:
	return clampf(db + 16.0, -30.0, 6.0) + lerpf(-14.0, 0.0, strength)


func _sound(kind: String, pos: Vector3, db1m: float, sub := "", follow: Node3D = null) -> void:
	"""a sound of the night at a place: you hear it at the PC (3D), MoveEye's microphone hears it too (main.add_sound)"""
	if paused or not _snd.has(kind):
		return
	var w: AudioStreamWAV = _snd[kind]
	main.add_sound(db1m, pos, w.get_length())
	if sub != "":
		_sub(sub)
	_players = _players.filter(func(p): return is_instance_valid(p))
	if _players.size() >= (3 if _lite() else 6):
		return
	var p := AudioStreamPlayer3D.new()
	p.stream = w
	p.unit_size = 4.0
	p.max_distance = 220.0
	p.max_db = 2.0
	p.volume_db = _vol(db1m)
	p.attenuation_filter_cutoff_hz = 2500.0                   # fog: far sounds are dull
	p.attenuation_filter_db = -18.0
	if follow != null and is_instance_valid(follow):
		follow.add_child(p)
		p.position = Vector3(0, 1.0, 0)
	elif _root != null:
		_root.add_child(p)
		p.global_position = pos
	else:
		return
	p.finished.connect(p.queue_free)
	_players.append(p)
	p.play()


func _ui_play(kind: String, db: float) -> void:
	if _ui_snd == null or not _snd.has(kind):
		return
	_ui_snd.stream = _snd[kind]
	_ui_snd.volume_db = db
	_ui_snd.play()


func _sub(t: String, secs := 3.5) -> void:
	if _hud_sub != null:
		_hud_sub.text = t
		_sub_until = Time.get_ticks_msec() / 1000.0 + secs


func _alarm(t: String) -> void:
	if _hud_alarm != null:
		_hud_alarm.text = t
		_alarm_until = Time.get_ticks_msec() / 1000.0 + 5.0


func _make_sounds() -> void:
	if not _snd.is_empty():
		return
	var t0 := Time.get_ticks_msec()
	_snd["step"] = _wav(_s_step(1.0))
	var st := PackedFloat32Array()
	st.resize(int(3.2 * SR))
	for k in range(6):
		var one := _s_step(randf_range(0.7, 1.0))
		var o := int((k * 0.52 + randf_range(-0.04, 0.04)) * SR)
		for i in range(one.size()):
			if o + i < st.size():
				st[o + i] += one[i]
	_snd["steps"] = _wav(st)
	_snd["crack"] = _wav(_s_crack())
	_snd["whisper"] = _wav(_s_whisper())
	_snd["bell"] = _wav(_s_bell())
	_snd["voice0"] = _wav(_s_voice([[750.0, 1200.0, 0.3, 150.0, 140.0], [450.0, 800.0, 0.5, 135.0, 180.0]]))
	_snd["voice1"] = _wav(_s_voice([[350.0, 2000.0, 0.18, 160.0, 150.0], [700.0, 1200.0, 0.2, 150.0, 140.0], [400.0, 2100.0, 0.18, 145.0, 140.0], [700.0, 1250.0, 0.35, 140.0, 185.0]]))
	_snd["voice2"] = _wav(_s_voice([[350.0, 2000.0, 0.22, 170.0, 160.0], [500.0, 1500.0, 0.3, 165.0, 150.0], [300.0, 2200.0, 0.4, 175.0, 150.0]]))
	_snd["creak"] = _wav(_s_creak())
	_snd["slam"] = _wav(_s_slam())
	_snd["sting"] = _wav(_s_sting())
	_drone = AudioStreamPlayer.new()
	_drone.stream = _wav(_s_drone(), true)
	_drone.volume_db = _amb_db()
	add_child(_drone)
	print("Horror: Geräusche erzeugt (%d ms)" % (Time.get_ticks_msec() - t0))


func _wav(buf: PackedFloat32Array, loop := false) -> AudioStreamWAV:
	var pcm := PackedByteArray()
	pcm.resize(buf.size() * 2)
	for i in range(buf.size()):
		pcm.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = SR
	w.data = pcm
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = buf.size()
	return w


func _buf(secs: float) -> PackedFloat32Array:
	var b := PackedFloat32Array()
	b.resize(int(secs * SR))
	return b


func _s_step(k: float) -> PackedFloat32Array:
	var b := _buf(0.22)
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		lp += (randf() * 2.0 - 1.0 - lp) * 0.25
		b[i] = (sin(TAU * 70.0 * t) * exp(-t / 0.03) * 0.7 + lp * exp(-t / 0.06) * 0.8) * k
	return b


func _s_crack() -> PackedFloat32Array:
	var b := _buf(0.35)
	var prev := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var n := randf() * 2.0 - 1.0
		var hp := n - prev
		prev = n
		var v := hp * exp(-t / 0.02) * 0.9
		if t > 0.07:
			v += hp * exp(-(t - 0.07) / 0.015) * 0.6
		if t < 0.003:
			v += n
		b[i] = v
	return b


func _s_whisper() -> PackedFloat32Array:
	var b := _buf(2.2)
	var prev := 0.0
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var n := randf() * 2.0 - 1.0
		var hp := n - prev
		prev = n
		lp += (hp - lp) * 0.5
		var syl := pow(0.5 + 0.5 * sin(TAU * 5.3 * t + 2.0 * sin(TAU * 0.7 * t)), 2.0)
		var env := minf(1.0, t / 0.2) * minf(1.0, (2.2 - t) / 0.4)
		b[i] = lp * syl * env * 0.55
	return b


func _s_bell() -> PackedFloat32Array:
	# a cowbell («Treichel»): inharmonic partials, a short clank, two strikes as if the animal moved its head
	var b := _buf(2.8)
	var parts := [[560.0, 1.0, 0.9], [845.0, 0.6, 0.6], [1137.0, 0.45, 0.45], [1546.0, 0.3, 0.3], [1904.0, 0.2, 0.25]]
	for st in [[0.0, 1.0], [0.42, 0.6]]:
		var o := int(float(st[0]) * SR)
		for i in range(b.size() - o):
			var t := float(i) / SR
			var v := (randf() * 2.0 - 1.0) * exp(-t / 0.008) * 0.5
			for p in parts:
				v += sin(TAU * float(p[0]) * t) * float(p[1]) * exp(-t / float(p[2]))
			b[o + i] += v * 0.22 * float(st[1])
	return b


func _s_voice(syls: Array) -> PackedFloat32Array:
	"""a voice calling far away in the fog: a pulse source through two formant filters, syllable by syllable, with echo"""
	var total := 0.0
	for s in syls:
		total += float(s[2]) + 0.06
	var b := _buf(total + 1.0)
	var ph := 0.0
	var y1 := [0.0, 0.0]
	var y2 := [0.0, 0.0]
	var pos := 0
	for s in syls:
		var n := int(float(s[2]) * SR)
		for i in range(n):
			var f := float(i) / float(n)
			var f0 := lerpf(float(s[3]), float(s[4]), f)
			ph += f0 / SR
			var src: float = (ph - floor(ph)) * 2.0 - 1.0 + (randf() - 0.5) * 0.3
			var env := minf(1.0, f / 0.15) * minf(1.0, (1.0 - f) / 0.25)
			var x: float = src * env
			var out := 0.0
			for k in range(2):
				var fr: float = s[k]
				var r := exp(-PI * (90.0 + 60.0 * k) / SR)
				var c1 := 2.0 * r * cos(TAU * fr / SR)
				var yy: Array = y1 if k == 0 else y2
				var y: float = (1.0 - r) * x + c1 * float(yy[0]) - r * r * float(yy[1])
				yy[1] = yy[0]
				yy[0] = y
				out += y * (1.0 if k == 0 else 0.6)
			if pos + i < b.size():
				b[pos + i] = out * 0.9
		pos += n + int(0.06 * SR)
	var e := b.duplicate()                                         # echo from the mountains
	for d in [[0.23, 0.35], [0.51, 0.2]]:
		var o := int(float(d[0]) * SR)
		for i in range(e.size() - o):
			b[i + o] += e[i] * float(d[1])
	return b


func _s_creak() -> PackedFloat32Array:
	var b := _buf(1.7)
	var y1 := 0.0
	var y2 := 0.0
	var nxt := 0.0
	var r := exp(-PI * 120.0 / SR)
	var c1 := 2.0 * r * cos(TAU * 900.0 / SR)
	for i in range(b.size()):
		var t := float(i) / SR
		var x := 0.0
		if t >= nxt:
			x = 1.0
			nxt = t + 1.0 / (60.0 + 90.0 * sin(PI * t / 1.7)) * randf_range(0.8, 1.2)
		var y := (1.0 - r) * x * 8.0 + c1 * y1 - r * r * y2
		y2 = y1
		y1 = y
		b[i] = y * minf(1.0, t / 0.1) * minf(1.0, (1.7 - t) / 0.3) * 0.8
	return b


func _s_slam() -> PackedFloat32Array:
	var b := _buf(0.6)
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		lp += (randf() * 2.0 - 1.0 - lp) * 0.3
		var v := sin(TAU * 55.0 * t) * exp(-t / 0.12) + lp * exp(-t / 0.04) * 1.2
		if t > 0.11:
			v += lp * exp(-(t - 0.11) / 0.03) * 0.5
		b[i] = v * 0.8
	return b


func _s_sting() -> PackedFloat32Array:
	var b := _buf(1.3)
	var fr := [220.0, 233.1, 311.1, 329.6, 466.2, 493.9]
	for i in range(b.size()):
		var t := float(i) / SR
		var v := (randf() * 2.0 - 1.0) * exp(-t / 0.06) * 0.7
		for f in fr:
			var ph: float = fposmod(f * t, 1.0)
			v += (ph * 2.0 - 1.0) * 0.16
		b[i] = v * minf(1.0, t / 0.01) * exp(-t / 0.5)
	return b


func _s_drone() -> PackedFloat32Array:
	"""the night: low wind and a deep hum, 6 s, seamless loop (the end is faded into the start)"""
	var n := int(6.0 * SR)
	var x := int(0.8 * SR)
	var raw := PackedFloat32Array()
	raw.resize(n + x)
	var br := 0.0
	for i in range(raw.size()):
		var t := float(i) / SR
		br = br * 0.995 + (randf() * 2.0 - 1.0) * 0.03
		raw[i] = br * (0.7 + 0.3 * sin(TAU * 0.23 * t)) * 2.2 + sin(TAU * 48.0 * t) * 0.05
	var b := PackedFloat32Array()
	b.resize(n)
	for i in range(n):
		b[i] = raw[i]
	for i in range(x):
		var k := float(i) / float(x)
		b[i] = raw[i] * k + raw[n + i] * (1.0 - k)
	return b


# =======================================================================================================================
# /control {"action": "horror", "do": …} – tests and remote control (the password only in "pw", never shown)
# =======================================================================================================================
func command(d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "info"))
	match what:
		"info":
			return {"ok": true, "unlocked": unlocked, "has_password": has_password(), "phase": phase, "running": running,
					"paused": paused, "chapter": chapter, "end": end_kind, "strength": strength, "choices": choices,
					"t": snappedf(_t, 0.1), "beat": _bi, "beats": _beats.size(), "clips": clips.size(), "jumps": _jumps,
					"fig": [snappedf(_fig.global_position.x, 0.1), snappedf(_fig.global_position.z, 0.1)] if _fig != null and _fig.visible else null,
					"hut": [snappedf(_hut.global_position.x, 0.1), snappedf(_hut.global_position.z, 0.1)] if _hut != null else null,
					"clock": _hhmm(), "fog": snappedf(main.env.fog_density, 0.001), "lite": _lite(), "slot": mood_slot()}
		"open":
			open()
			return {"ok": true, "phase": phase}
		"set_password":
			return set_password(str(d.get("pw", "")))
		"unlock":
			return unlock(str(d.get("pw", "")))
		"start":
			if not unlocked:
				return {"ok": false, "error": "locked"}
			if ENDS.has(str(d.get("end", ""))):
				end_kind = str(d["end"])
			if d.has("strength"):
				set_strength(float(d["strength"]))
			_ensure_ui()
			begin(int(d.get("chapter", 1)))
			return {"ok": true}
		"go":
			if phase == "intro":
				_night_go()
			return {"ok": true, "phase": phase}
		"skip":                                                 # to the next beat (or to the morning)
			if phase == "night" and _bi < _beats.size():
				_t = float(_beats[_bi][0]) * NIGHT_SECS
			elif phase == "night":
				_t = NIGHT_SECS
			return {"ok": true, "t": _t}
		"beat":
			_beat([0.0, str(d.get("kind", "bell")), d.get("args", {"d": 10.0})])
			return {"ok": true}
		"choose":
			_choose(str(d.get("k", "d1")), str(d.get("v", "follow")))
			return {"ok": true, "chapter": chapter}
		"pause":
			_set_pause(true)
			return {"ok": true}
		"resume":
			_set_pause(false)
			return {"ok": true}
		"clips":
			_ensure_ui()
			_show_clips(func(): _clear_card())
			return {"ok": true}
		"clip":
			var c := _clip_now("Test", "Test")
			return {"ok": true, "id": c["id"]}
		"stop":
			stop()
			return {"ok": true}
	return {"ok": false, "error": "do: info | open | set_password | unlock | start | go | skip | beat | choose | pause | resume | clips | clip | stop"}
