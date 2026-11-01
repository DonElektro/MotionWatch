extends Node
## P2 «totale Integration» (MoveEye Teil 639zb): die Ansicht mit dem verbundenen MoveEye abgleichen, ohne eigenen Schalter.
## Geteilt (res://ui_gemeinsam.json «shared» / «sync»): Einfach/Experte, Symbole farbig/schlicht, Sprache, Bewegung reduzieren,
## Stimme, Rundgang, Blinki, «Neu in …», «Links zu Neuerungen». Hell/Dunkel/Rotlicht bleibt pro Gerät.
##   * MoveEye schickt im Zustand «ui» = {rev, took, v}. Eine eigene Änderung geht in der Antwort als «ui» = {n, base, set}
##     mit (reply()), bis MoveEye sie mit «took» >= n bestätigt; danach gelten wieder die Werte von MoveEye.
##   * Letzte Änderung gewinnt (MoveEye zählt), im selben Takt gewinnt MoveEye. Nach dem Neuverbinden (Pause > 3 s, anderer
##     Leiter, kleinere Revision) führt MoveEye: der Simulator übernimmt alles (kurzer Hinweis). Nur mit dem Leiter.
##   * Ohne Verbindung arbeitet der Simulator mit seinen eigenen, gespeicherten Werten weiter. Ein älteres MoveEye schickt
##     kein «ui» - dann geschieht nichts.
## Dazu die kleinen Hinweise (★ review_integration2, keine neuen Karten - unten links neben dem Bedienfeld):
##   * Zustand «Aus / Wachsam / Voll / Gehtest» mit der Farbe der Status-LED von MoveEye («level», auch in der Statuszeile)
##   * Push-Vorschau «Push (Test-Postfach): … · 22:14» (Feld «push», 10 s sichtbar, Antippen öffnet den Verlauf von MoveEye)
##   * Versions-Paar «MoveEye 3.x · Sim 3.x ✓», sonst ⚠ mit Knopf zum Aktualisieren der älteren Seite (pair())
##   * Bedienermodus: MoveEye gesperrt («lock») -> nur die Hauptschalter (Einfach, ohne Feineinstellungen, ohne Entwickler
##     und Werkseinstellungen); Entsperren mit der PIN von MoveEye (geprüft nur in MoveEye, Antwort «ui.unlock»)
## Test ohne Bild: werkzeuge/ui_gemeinsam_test.gd (Wert auf der einen Seite ändern -> erscheint auf der anderen).

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const UG = preload("res://scripts/ui_gemeinsam.gd")
const Stimme = preload("res://scripts/abenteuer_stimme.gd")
const KEYS := ["simple", "icons", "lang", "motion", "voice", "tours", "blinki", "news", "news_links"]
const LINKS := ["auto", "on", "off"]   # «Links zu Neuerungen» (news.gd)
const GAP := 3.0                      # seconds without a packet = a new connection (MoveEye leads again)
const MOTION_TO := {"auto": "auto", "on": "an", "off": "aus"}
const VOICE_TO := {"on": "an", "off": "aus", "subtitles": "untertitel"}

var main
var synced := false                   # this connection already has the values of MoveEye
var lead_uid := ""
var rev := 0                          # the last revision of MoveEye
var snap := {}                        # the own values at the last packet
var dirty := {}                       # own changes MoveEye has not confirmed yet
var seq := 0                          # number of the last own change packet
var last_t := -100.0
var note := ""                        # «Ansicht von MoveEye übernommen (…)»
var level := {}                       # {id, col, arming} of MoveEye
var lock := {}                        # {on, n, msg, pin}
var push := {}                        # the newest message of MoveEye
var diag: Array = []                  # the self-diagnosis of MoveEye (every 15 s)
var diag_t := -100.0
var unlock_n := 0
var _unlock_pin := ""
var _unlock_t := -100.0
var upd_n := 0
var _upd_ver := ""
var _push_seen := "-"
var _push_t := -100.0
var _lock_on := false
var _keep_simple := true
var _layer: CanvasLayer = null
var _box: VBoxContainer = null
var _lv_row: HBoxContainer = null
var _lv_dot: Control = null
var _lv_l: Label = null
var _push_row: Button = null
var _ver_row: HBoxContainer = null
var _ver_l: Label = null
var _ver_b: Button = null
var _lock_row: VBoxContainer = null
var _lock_l: Label = null
var _lock_pin: LineEdit = null
var _tick := 0.0
var synced_once := false              # there was a connection before (the hint «taken over» only then)


static func txt(k: String, sect := "hint") -> String:
	"""a text of ui_gemeinsam.json «hint» / «level» in the language of the simulator (5 languages, no texte.json)"""
	var h: Dictionary = UG.data().get(sect, {})
	var e = h.get(k, {})
	if typeof(e) == TYPE_DICTIONARY and e.has("names"):
		e = e["names"]
	if typeof(e) != TYPE_DICTIONARY:
		return k
	return str(e.get(T.lang(), e.get("de", k)))


static func norm(k: String, v):
	"""a value of MoveEye, checked (null = not usable)"""
	match k:
		"simple", "tours", "blinki", "news":
			return v if typeof(v) == TYPE_BOOL else null
		"icons":
			return str(v) if str(v) in ["color", "plain"] else null
		"lang":
			return str(v) if str(v) in T.codes() else null
		"motion":
			return str(v) if MOTION_TO.has(str(v)) else null
		"voice":
			return str(v) if VOICE_TO.has(str(v)) else null
		"news_links":
			return str(v) if str(v) in LINKS else null
	return null


func values() -> Dictionary:
	"""the shared values of the simulator now (the names of MoveEye)"""
	var rm := str(main.get("reduce_motion"))
	var vm := Stimme.modus()
	return {"simple": _keep_simple if _lock_on else bool(main.ui_simple), "icons": "plain" if str(main.ui_icons) == "plain" else "color",
			"lang": T.lang(), "motion": "on" if rm == "an" else ("off" if rm == "aus" else "auto"),
			"voice": {"an": "on", "aus": "off", "untertitel": "subtitles"}.get(vm, "on"),
			"tours": bool(main.tour_auto), "blinki": bool(main.blinki_on), "news": bool(main.news_popup),
			"news_links": str(main.get("news_links")) if str(main.get("news_links")) in LINKS else "auto"}


func apply(v: Dictionary) -> Array:
	"""take values of MoveEye; returns the keys that really changed"""
	var cur := values()
	var ch := []
	for k in KEYS:
		if not v.has(k):
			continue
		var x = norm(k, v[k])
		if x == null or str(cur[k]) == str(x):
			continue
		ch.append(k)
		match k:
			"simple":
				if _lock_on:
					_keep_simple = bool(x)
				else:
					main.set_simple(bool(x))
			"icons":
				main.set_icons(str(x))
			"lang":
				T.set_moveeye_lang(str(x))
				if T.choice() != "" and T.choice() != str(x):
					T.set_lang(str(x))
			"motion":
				main.reduce_motion = MOTION_TO[str(x)]
				if main.has_method("motion_reduced"):
					UI.motion_still = main.motion_reduced()
			"voice":
				Stimme.set_modus(VOICE_TO[str(x)])
			"tours":
				main.tour_auto = bool(x)
			"blinki":
				main.blinki_on = bool(x)
			"news":
				main.news_popup = bool(x)
			"news_links":
				main.news_links = str(x)
	if not ch.is_empty():
		main._settings_dirty = true
		if main.has_method("_sync_ui"):
			main._sync_ui()
		if main.get("leiste") != null and main.leiste.has_method("paint"):
			main.leiste.paint(main.ui_simple, main.ui_icons, main.start_groups)
	return ch


func connected() -> bool:
	return synced and main.now() - last_t < GAP


func on_state(d: Dictionary, lead: bool) -> void:
	"""POST /state of MoveEye (net.gd): the view, and what the hints show"""
	if not lead:
		return                                        # a MoveEye that only watches does not share the view
	var t: float = main.now()
	if typeof(d.get("level")) == TYPE_DICTIONARY:
		level = d["level"]
	lock = d["lock"] if typeof(d.get("lock")) == TYPE_DICTIONARY else {}
	if typeof(d.get("push")) == TYPE_DICTIONARY:
		_on_push(d["push"], t)
	if typeof(d.get("diag")) == TYPE_ARRAY:
		diag = d["diag"]
		diag_t = t
	var lm := str(lock.get("msg", ""))
	if int(lock.get("n", 0)) >= unlock_n and unlock_n > 0 and _unlock_pin != "":
		_unlock_pin = ""                               # MoveEye answered: never keep the PIN
		if lm != "ok" and lm != "":
			_say(txt("wrong_pin") if lm == "wrong PIN" else lm)
	var u = d.get("ui")
	if typeof(u) != TYPE_DICTIONARY:
		synced = false                                 # an older MoveEye: the simulator stays on its own
		return
	var r := int(u.get("rev", 0))
	var took := int(u.get("took", 0))
	var v: Dictionary = u.get("v", {}) if typeof(u.get("v")) == TYPE_DICTIONARY else {}
	var uid := str(d.get("uid", d.get("device", "")))
	var fresh: bool = not synced or t - last_t > GAP or uid != lead_uid or r < rev
	last_t = t
	lead_uid = uid
	if fresh:                                          # new connection: MoveEye leads (offline changes of the simulator give way)
		dirty.clear()
		seq = maxi(seq, took)
		var ch := apply(v)
		if not ch.is_empty() and synced_once:
			_say(txt("taken") + " (" + ", ".join(ch) + ")")
		synced = true
		synced_once = true
		rev = r
		snap = values()
		return
	var cur := values()
	var new_ := false
	for k in KEYS:                                     # own changes since the last packet
		if str(cur[k]) != str(snap.get(k, "")):
			dirty[k] = cur[k]
			new_ = true
	if new_:
		seq += 1
	if took >= seq:                                    # MoveEye has every own packet: its values count again
		dirty.clear()
		apply(v)
	else:
		var keep := {}
		for k in v:
			if not dirty.has(k):
				keep[k] = v[k]
		apply(keep)
	rev = r
	snap = values()



func reply() -> Dictionary:
	"""world_reply «ui» (net.gd): own changes, the PIN, «update MoveEye» - empty when there is nothing"""
	var o := {}
	if connected() and not dirty.is_empty():
		o["n"] = seq
		o["base"] = rev
		o["set"] = dirty.duplicate()
	if _unlock_pin != "" and main.now() - _unlock_t < 10.0:
		o["unlock"] = {"n": unlock_n, "pin": _unlock_pin}
	if upd_n > 0:
		o["update_mw"] = {"n": upd_n, "ver": _upd_ver}
	return o


func unlock(pin: String) -> void:
	"""Entsperren mit der PIN von MoveEye (MoveEye prüft, 5 Fehlversuche = 5 Minuten Pause)"""
	unlock_n = maxi(unlock_n, int(lock.get("n", 0))) + 1
	_unlock_pin = pin.strip_edges().left(12)
	_unlock_t = main.now()


func locked() -> bool:
	"""MoveEye (the leader, connected) is in the operator mode"""
	return main != null and main.now() - last_t < GAP and bool(lock.get("on", false))


# ---- ★4 the version pair --------------------------------------------------------------------------------------------------
static func vkey(s: String) -> Array:
	var rx := RegEx.new()
	rx.compile("(\\d+)\\.(\\d+)(?:\\.(\\d+))?")
	var m := rx.search(s)
	if m == null:
		return []
	var a := [int(m.get_string(1)), int(m.get_string(2)), int(m.get_string(3)) if m.get_string(3) != "" else 0]
	if s.contains("3D-"):
		a[0] -= 2                                      # «3D-5.0.0» = 3.0.0 (CLAUDE.md «Brücke für alte Simulatoren»)
	return a


func pair() -> Dictionary:
	"""{mw, sim, same, older ("" | "sim" | "mw"), text} - «MoveEye 3.34.0 · Sim 3.34.0 ✓»"""
	var mv := str(main.mw.get("mw_version", "")) if main.now() - float(main.mw_t) < GAP else ""
	var sv := str(main.VERSION)
	var a := vkey(mv)
	var b := vkey(sv)
	var o := {"mw": mv, "sim": sv, "same": not a.is_empty() and a == b, "older": ""}
	if not a.is_empty() and not b.is_empty() and a != b:
		o["older"] = "sim" if (b[0] * 1000000 + b[1] * 1000 + b[2]) < (a[0] * 1000000 + a[1] * 1000 + a[2]) else "mw"
	var tx := "MoveEye %s · Sim %s" % [mv if mv != "" else "?", sv]
	if o["same"]:
		tx += " ✓"
	elif o["older"] != "":
		tx = "⚠ " + txt("sim_older" if o["older"] == "sim" else "mw_older") + ": " + tx
	o["text"] = tx
	return o


func update_older() -> void:
	var p := pair()
	if p["older"] == "sim":
		main.control({"action": "press", "id": "update_now"})
	elif p["older"] == "mw":
		upd_n += 1
		_upd_ver = str(p["sim"])


# ---- ★1 the state -----------------------------------------------------------------------------------------------------------
func level_text() -> String:
	"""«Wachsam», «Voll in 12 s» … in the words of MoveEye (ui_gemeinsam.json «level»), "" without MoveEye"""
	if main.now() - float(main.mw_t) > GAP or level.is_empty():
		return ""
	var id := str(level.get("id", "off"))
	var t := txt(id, "level")
	if bool(level.get("arming", false)) and id != "off":
		t += " (" + txt("arming", "level") + " …)"
	return t


func level_color() -> Color:
	var h := str(level.get("col", ""))
	if h == "":
		h = str((UG.data().get("level", {}).get(str(level.get("id", "off")), {}) as Dictionary).get("col", "#888888"))
	return Color.html(h) if Color.html_is_valid(h) else UI.MUT


# ---- ★2 the push preview ----------------------------------------------------------------------------------------------------
func _on_push(p: Dictionary, t: float) -> void:
	var id := str(p.get("id", ""))
	if _push_seen == "-":                              # the first packet: an old message is not new
		_push_seen = id
		return
	if id == "" or id == _push_seen:
		return
	_push_seen = id
	push = p
	_push_t = t


func push_text() -> String:
	if push.is_empty():
		return ""
	var w := txt("push") if str(push.get("status", "")) in ["test", "none"] or str(push.get("where", "")).contains("Test") else txt("push_real")
	return "%s: %s%s" % [w, str(push.get("title", "")), (" · " + str(push.get("hm", ""))) if str(push.get("hm", "")) != "" else ""]


# ---- the hints (small, bottom left of the panel) ------------------------------------------------------------------------------
func _ready() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 55
	add_child(_layer)
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 6)
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_box)
	_lv_row = _chip()
	_lv_dot = Control.new()
	_lv_dot.custom_minimum_size = Vector2(12, 18)
	_lv_dot.draw.connect(func(): _lv_dot.draw_circle(Vector2(6, 9), 5.5, level_color()))
	_lv_l = UI.small("", UI.TXT)
	_lv_row.add_child(_lv_dot)
	_lv_row.add_child(_lv_l)
	_push_row = Button.new()
	_push_row.flat = false
	_push_row.icon = null
	_push_row.alignment = HORIZONTAL_ALIGNMENT_LEFT
	_push_row.add_theme_font_size_override("font_size", 13)
	_push_row.pressed.connect(_open_history)
	_push_row.visible = false
	_box.add_child(_push_row)
	_ver_row = _chip()
	_ver_l = UI.small("", UI.TXT)
	_ver_row.add_child(_ver_l)
	_ver_b = Button.new()
	_ver_b.add_theme_font_size_override("font_size", 12)
	_ver_b.pressed.connect(update_older)
	_ver_row.add_child(_ver_b)
	_lock_row = VBoxContainer.new()
	_lock_row.visible = false
	_box.add_child(_lock_row)
	var lh := _chip(_lock_row)
	_lock_l = UI.small("", UI.TXT)
	_lock_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_lock_l.custom_minimum_size = Vector2(260, 0)
	lh.add_child(_lock_l)
	var lp := HBoxContainer.new()
	_lock_row.add_child(lp)
	_lock_pin = LineEdit.new()
	_lock_pin.secret = true
	_lock_pin.custom_minimum_size = Vector2(110, 0)
	_lock_pin.max_length = 8
	_lock_pin.text_submitted.connect(func(_s): _send_pin())
	lp.add_child(_lock_pin)
	var lb := Button.new()
	lb.name = "Unlock"
	lb.pressed.connect(_send_pin)
	lp.add_child(lb)


func _chip(parent: Control = null) -> HBoxContainer:
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.94), UI.LINE, 99, 6))
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	pc.add_child(h)
	(parent if parent != null else _box).add_child(pc)
	return h


func _send_pin() -> void:
	if _lock_pin != null and _lock_pin.text.strip_edges() != "":
		unlock(_lock_pin.text)
		_lock_pin.text = ""


func _open_history() -> void:
	var host := str(main.get("mw_addr"))
	if host == "":
		return
	OS.shell_open("%s://%s:%d/recordings" % [str(main.mw.get("mw_scheme", "http")), host, int(main.mw.get("mw_port", 8080))])


func _say(t: String) -> void:
	note = t
	if main.get("mehr") != null and main.mehr.has_method("toast"):
		main.mehr.toast(t)


func _process(dt: float) -> void:
	_tick -= dt
	if _tick > 0.0 or main == null:
		return
	_tick = 0.3
	_lock_apply()
	if _box == null:
		return
	var on: bool = main.now() - float(main.mw_t) < GAP
	var lt := level_text()
	_lv_row.get_parent().visible = on and lt != ""
	_lv_l.text = lt
	_lv_dot.queue_redraw()
	var pt := push_text()
	_push_row.visible = on and pt != "" and main.now() - _push_t < 10.0
	_push_row.text = pt
	var p := pair()
	_ver_row.get_parent().visible = on and str(p["mw"]) != "" and not bool(p["same"])
	_ver_l.text = str(p["text"])
	_ver_b.visible = p["older"] != "" and not _lock_on and not bool(main.get("kids_on"))
	_ver_b.text = txt("update_sim" if p["older"] == "sim" else "update_mw")
	_lock_row.visible = _lock_on
	_lock_l.text = txt("locked")
	var ub := _lock_row.find_child("Unlock", true, false) as Button
	if ub != null:
		ub.text = txt("unlock")
	var vs: Vector2 = _box.get_viewport_rect().size
	var right: float = vs.x - (main.ui_root.size.x if main.get("ui_root") != null and main.ui_root.visible else 0.0)
	_box.reset_size()
	_box.position = Vector2(maxf(8.0, right - _box.size.x - 12.0), vs.y - _box.size.y - 120.0)


func _lock_apply() -> void:
	"""★6 Bedienermodus: only the main switches while MoveEye is locked (Einfach, no «Feineinstellungen»); back afterwards"""
	var want := locked()
	if want and not _lock_on:
		_keep_simple = bool(main.ui_simple)
		_lock_on = true
		if not main.ui_simple:
			main.set_simple(true)
	elif not want and _lock_on:
		_lock_on = false
		if bool(main.ui_simple) != _keep_simple:
			main.set_simple(_keep_simple)
		elif main.has_method("_apply_simple"):
			main._apply_simple()
		snap["simple"] = _keep_simple
	if not _lock_on:
		return
	if not main.ui_simple:                             # «Experte» pressed while locked
		main.set_simple(true)
		_say(txt("locked"))
	for fb in main.get("fine_bodies") if main.get("fine_bodies") != null else []:
		if is_instance_valid(fb) and (fb as Control).has_meta("wrap"):
			var w = fb.get_meta("wrap")
			if w is Control and (w as Control).visible:
				(w as Control).visible = false
