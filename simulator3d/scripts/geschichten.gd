extends Node
## Geschichten-Menü (Daniel, 31.10.2026): das Regal «Geschichten» im Fenster «Spielen» (spielbereich.gd) und der gemeinsame
## Start aller Geschichten.
##   * Geschichten = Storys mit Kapiteln, als grosse Karten (2 pro Zeile, wie Bücher im Regal): «Die Karte des Grossvaters»
##     (bergtal_abenteuer.gd), «Maggie und der Bergkristall» (maggie_story.gd), «Das Hospiz» (bergtal_horror.gd) und
##     «Teil 2 – Die zweite Karte» (gesperrt, kommt später). Jede Karte: Bild, ein Satz Inhalt, Spieldauer, «ab X Jahren»,
##     Fortschritt in %, «Weiterspielen» und «Neu beginnen».
##   * Bild = ein Ausschnitt aus der Geschichte selbst, im Simulator gerendert: Grossvater = das neueste Tagebuchbild (sonst
##     die alte Schatzkarte, wie sie im Spiel aussieht), Maggie = ein Bild aus der zuletzt gespielten Region (einmal pro Region
##     beim Spielen aufgenommen, user://geschichten/maggie.jpg, Platz 2/3 im Ordner des Spielstands), Hospiz = die neueste «Aufnahme» von MoveEye. Solange es noch
##     keines gibt: eine kleine gezeichnete Szene (_draw, kein fremdes Bild).
##   * «Das Hospiz»: nur für den Besitzer (devtool.is_owner - wie das Entwicklertool: nie im Kinder-Modus), mit Schloss: zum
##     Öffnen fragt das Spiel nach dem Passwort (bergtal_horror.gd open_locked - Prüfung, Hash, Widmung, Warnung unverändert).
##     Daneben «Ohne Passwort starten» (nur Besitzer, nie Kinder-Modus, bergtal_horror.gd ohne_passwort). «Weiterspielen» und
##     «Neu beginnen» gehen beide über dieselbe Regel (horror.may_play, Code-Prüfung H1).
##     Für alle anderen gibt es die Karte nicht (auch nicht in MoveEye: dort nur für den Administrator, 639i).
##   * Kinder-Modus (main.kids_on): nur Karten «ab X Jahren» mit X ≤ KIDS_AGE, grössere Schrift.
##   * Gemeinsamer Start (ein Ablauf für alle): Spielstand wählen → Figur (Name / Aussehen, wo die Geschichte eine hat: Maggie)
##     → Schwierigkeit und Jahreszeit (wo sinnvoll: Grossvater). Die Spielstände bleiben, wie sie sind (spielstand.gd: Platz 1 =
##     die alten Dateien). «Neu beginnen» in einem Platz mit Fortschritt warnt zuerst (Stufe und Abzeichen bleiben).
##   * «Weiterspielen: <Geschichte>, <Kapitel/Region> (x %)» ganz oben: die zuletzt gespielte Geschichte dieses Spielstands
##     (spielstand.gd last_story, wird hier jede Sekunde nachgeführt).
## Lite: keine teuren Effekte (die Bilder sind gezeichnet oder einmal aufgenommen; die Aufnahme ist ein einziges Bild).
##   * «Trailer ansehen» (Grossvater, Maggie): ein Film von ≈ 3 Min. (trailer.gd), Esc / Klick = zurück zu «Spielen».
## Steuerbefehl (über spielbereich.gd): {"action": "spielbereich", "do": "stories" | "story" (id, what: weiter | neu | open | trailer) |
##   "gs" (k: info | next | back | cancel | slot (v) | level (v) | season (v) | name (v) | col (v))}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const SS = preload("res://scripts/spielstand.gd")
const Dev = preload("res://scripts/devtool.gd")
const Karte = preload("res://scripts/bergtal_abenteuer_karte.gd")
const AbD = preload("res://scripts/bergtal_abenteuer_daten.gd")
const Ab = preload("res://scripts/bergtal_abenteuer.gd")
const Mg = preload("res://scripts/maggie_story.gd")
const Figur = preload("res://scripts/figur.gd")
const MZ = preload("res://scripts/maggie_zwei.gd")      # Maggie für zwei Spieler: «1 oder 2 Spieler» auf der Seite «Figur»
const Trailer = preload("res://scripts/trailer.gd")   # «Trailer ansehen» auf den Karten Grossvater und Maggie

const IDS := ["grossvater", "maggie", "horror", "teil2"]
const AGE := {"grossvater": 8, "maggie": 10, "horror": 16, "teil2": 8}
const KIDS_AGE := 10                     # Kinder-Modus: Geschichten «ab X Jahren» mit X ≤ 10
const PIC_DIR := "user://geschichten"
const PIC_H := 132.0

var main
var sb                                   # spielbereich.gd
var _t := 0.0
var _mg_snap := ""                       # the region of which Maggie's picture was taken (once per region)
var _mg_since := -1.0
var _tex := {}                           # id -> [key, Texture2D]
var _fl := {}                            # the common start: {id, what, steps, i, slot, name, look, level, season, err, back}
var _body: VBoxContainer = null


func _lite() -> bool:
	"""the central question «Lite?» (Brief: Engine-Meta «lite»; the coordinator connects it with Quality.lite())"""
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


func kids() -> bool:
	return main != null and bool(main.get("kids_on"))


func fs(sz: int) -> int:
	"""Kinder-Modus: bigger text"""
	return int(round(sz * (1.25 if kids() else 1.0)))


# ---- the stories ---------------------------------------------------------------------------------------------------------
func _def(id: String) -> Dictionary:
	match id:
		"grossvater":
			return {"title": T.t("Die Karte des Grossvaters"), "short": T.t("Mit Grossvaters alter Schatzkarte wanderst du in fünf Kapiteln durchs Bergtal – nachts bewacht MoveEye dein Lager."),
					"dauer": T.t("5 Kapitel, je 30–45 Min."), "figur": false, "level": true, "season": true}
		"maggie":
			return {"title": T.t("Maggie und der Bergkristall"), "short": T.t("Mit Maggie, dem kleinen Hund, bringst du einen leuchtenden Kristall durch vier Jahreszeiten zum Gipfel."),
					"dauer": T.t("etwa 2 Stunden"), "figur": true, "level": false, "season": false,
					"figur_note": T.t("Maggie ist euer Familienhund: ein kleiner, heller Terrier mit hellbraunen Flecken. Sie hat eine sehr gute Nase.")}
		"horror":
			return {"title": T.t("Das Hospiz"), "short": T.t("Drei Nächte am Pass beim alten Hospiz – was nimmt MoveEye auf? Unheimlich, mit Schreckmomenten."),
					"dauer": T.t("3 Nächte, je etwa 10 Min."), "figur": false, "level": false, "season": false}
		"teil2":
			return {"title": T.t("Teil 2 – Die zweite Karte"), "short": T.t("Über den Pass ins nächste Tal: Grossvaters zweite Karte wartet. Kommt mit einer nächsten Version."),
					"dauer": T.t("kommt bald"), "figur": false, "level": false, "season": false}
	return {}


func _there(id: String) -> bool:
	match id:
		"grossvater", "teil2":
			return main.abenteuer != null
		"maggie":
			return main.get("maggie") != null
		"horror":
			return main.get("horror") != null
	return false


func shown_ids() -> Array:
	"""the cards this viewer sees: «Das Hospiz» only for the owner (never in the children's mode); in the children's mode
	only the stories for their age"""
	var out := []
	for id in IDS:
		if not _there(id):
			continue
		if id == "horror" and (kids() or not Dev.is_owner(main)):
			continue
		if kids() and int(AGE[id]) > KIDS_AGE:
			continue
		out.append(id)
	return out


func progress(id: String) -> Dictionary:
	"""{pct, where, started, done, locked, soon} of the active Spielstand"""
	var p := {"pct": 0, "where": "", "started": false, "done": false}
	match id:
		"grossvater":
			p = main.abenteuer.fortschritt()
		"maggie":
			p = main.maggie.fortschritt()
		"horror":
			p = main.horror.fortschritt()
	p["locked"] = id == "teil2" or (id == "horror" and not bool(main.horror.unlocked))
	p["soon"] = id == "teil2"
	return p


func progress_of_slot(id: String, n: int) -> int:
	"""the % of a story in another Spielstand (for the choice of the place) - read from its files, nothing is switched"""
	if n == SS.slot():
		return int(progress(id).get("pct", 0))
	match id:
		"grossvater":
			var inf := SS.info(n)
			if not bool(inf["used"]):
				return 0
			var d = JSON.parse_string(FileAccess.get_file_as_string(SS.path_ab(n))) if FileAccess.file_exists(SS.path_ab(n)) else null
			if d is Dictionary and bool(d.get("finale", false)):
				return 100
			return (clampi(int(inf["chapter"]), 1, 5) - 1) * 20
		"maggie":
			var p := SS.path_maggie(n)
			var d = JSON.parse_string(FileAccess.get_file_as_string(p)) if FileAccess.file_exists(p) else null
			if not (d is Dictionary):
				return 0
			if bool(d.get("finale", false)):
				return 100
			return 10 + (d.get("done", []) as Array).size() * 20 if bool(d.get("intro", false)) else 0
		"horror":
			var st: Dictionary = main.horror._store
			var pr = st.get(SS.horror_key(n), {})
			return int(round(100.0 * clampi(int(pr.get("done", 0)), 0, 3) / 3.0)) if pr is Dictionary else 0
	return 0


func stories() -> Array:
	"""the cards (also for MoveEye, 639i): [{id, title, short, dauer, age, pct, where, started, done, locked, soon, pic, last}]"""
	var out := []
	var last := SS.last_story()
	for id in shown_ids():
		var d := _def(id)
		var p := progress(id)
		out.append({"id": id, "title": d["title"], "short": d["short"], "dauer": d["dauer"], "age": int(AGE[id]), "pct": int(p["pct"]),
				"where": str(p["where"]), "started": bool(p["started"]), "done": bool(p["done"]), "locked": bool(p["locked"]),
				"soon": bool(p["soon"]), "pic": not pic_bytes(id, true).is_empty(), "last": id == last})
	return out


func resume_info() -> Dictionary:
	"""«Weiterspielen» on top: the story played last on this Spielstand (if it is started and not done)"""
	var ids := shown_ids()
	var cand := [SS.last_story()] + ids
	for id in cand:
		if id == "" or not (id in ids) or id == "teil2":
			continue
		var p := progress(id)
		if bool(p["started"]) and not bool(p["done"]):
			var d := _def(id)
			var w := str(p["where"])
			return {"id": id, "title": d["title"], "where": w, "pct": int(p["pct"]), "locked": bool(p["locked"]),
					"text": T.t("Weiterspielen: %s, %s (%d %%)", [d["title"], w, int(p["pct"])]) if w != "" else T.t("Weiterspielen: %s (%d %%)", [d["title"], int(p["pct"])])}
	return {}


# ---- the last story and Maggie's picture (once a second) --------------------------------------------------------------------
func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0 or main == null:
		return
	_t = 1.0
	var mg = main.get("maggie")
	var ho = main.get("horror")
	if mg != null and bool(mg.get("demo")):
		return                                         # Vorführmodus: no picture, no «zuletzt gespielt» (Daniel's Spielstände stay)
	if mg != null and bool(mg.running):
		SS.set_last_story("maggie")
		if str(mg.phase) == "region" and str(mg.region) != "" and _mg_snap != str(mg.region):
			if _mg_since < 0.0:
				_mg_since = main.now()
			elif main.now() - _mg_since > 8.0:          # 8 s after the region started: the figure stands in the scene
				_mg_snap = str(mg.region)
				_mg_since = -1.0
				_snap_maggie()
		else:
			_mg_since = -1.0
	elif main.abenteuer != null and not (main.abenteuer.R as Dictionary).is_empty():
		SS.set_last_story("grossvater")
	elif ho != null and bool(ho.running):
		SS.set_last_story("horror")


func _snap_maggie() -> void:
	"""one picture of the region for Maggie's card: the 3D view without any buttons or windows (one frame), the middle of it"""
	var hidden := []                                   # all buttons, windows and notes off for this one picture
	for n in get_tree().root.find_children("*", "CanvasLayer", true, false):
		if (n as CanvasLayer).visible:
			(n as CanvasLayer).visible = false
			hidden.append(n)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	for n in hidden:
		if is_instance_valid(n):
			(n as CanvasLayer).visible = true
	if img == null or img.is_empty():
		return
	var w := img.get_width()
	var h := img.get_height()
	img = img.get_region(Rect2i(int(w * 0.18), int(h * 0.16), int(w * 0.64), int(h * 0.56)))
	img.resize(480, int(480.0 * img.get_height() / maxf(1.0, img.get_width())), Image.INTERPOLATE_BILINEAR)
	var mp := SS.path_maggie_pic()                               # per Spielstand (place 1 = PIC_DIR/maggie.jpg)
	DirAccess.make_dir_recursive_absolute(mp.get_base_dir())
	img.save_jpg(mp, 0.82)
	_tex.erase("maggie")


func _pic_image(id: String) -> Array:
	"""[key, Image] of the card picture - a picture from the story itself; [] = none yet"""
	match id:
		"grossvater":
			var p: String = main.abenteuer.last_pic_path()
			if p != "":
				return [p + str(FileAccess.get_modified_time(p)), p]
		"maggie":
			var p := SS.path_maggie_pic()
			if FileAccess.file_exists(p):
				return [p + str(FileAccess.get_modified_time(p)), p]
		"horror":
			var j: PackedByteArray = main.horror.last_pic()
			if not j.is_empty():
				return ["h%d" % j.size(), j]
	return []


func _load_img(src) -> Image:
	var img: Image = null
	if src is String:
		img = Image.load_from_file(src)
	elif src is PackedByteArray:
		img = Image.new()
		if img.load_jpg_from_buffer(src) != OK:
			return null
		img = img.get_region(Rect2i(0, 0, img.get_width() / 2, img.get_height()))   # the recording: left = camera, right = thermal
	return img


func texture(id: String) -> Texture2D:
	var k := _pic_image(id)
	if k.is_empty():
		return null
	if _tex.has(id) and str(_tex[id][0]) == str(k[0]):
		return _tex[id][1]
	var img := _load_img(k[1])
	if img == null or img.is_empty():
		return null
	var t := ImageTexture.create_from_image(img)
	_tex[id] = [k[0], t]
	return t


func pic_bytes(id: String, only_check := false) -> PackedByteArray:
	"""the card picture as JPEG for MoveEye (/story_pic/<id>.jpg) - only for the cards this viewer may see"""
	if not (id in shown_ids()):
		return PackedByteArray()
	var k := _pic_image(id)
	if k.is_empty():
		return PackedByteArray()
	if only_check:
		return PackedByteArray([1])
	var img := _load_img(k[1])
	if img == null or img.is_empty():
		return PackedByteArray()
	if img.get_width() > 480:
		img.resize(480, int(480.0 * img.get_height() / img.get_width()), Image.INTERPOLATE_BILINEAR)
	return img.save_jpg_to_buffer(0.8)


# ---- the shelf (painted into the window «Spielen» by spielbereich.gd) ---------------------------------------------------
func shelf(W: float) -> Control:
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 10)
	g.add_theme_constant_override("v_separation", 10)
	var cw := floorf((W - 10.0) / 2.0)
	for s in stories():
		g.add_child(card(s, cw))
	return g


func card(s: Dictionary, w: float) -> Control:
	var id: String = s["id"]
	var off: bool = bool(s["soon"])
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(w, 0)
	p.add_theme_stylebox_override("panel", UI.box(UI.PANEL2 if not off else UI.FIELD, UI.ACC if bool(s["last"]) and bool(s["started"]) else UI.LINE, 14, 0, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	p.add_child(v)
	v.add_child(picture(id, Vector2(w - 2.0, PIC_H), bool(s["locked"])))
	var m := MarginContainer.new()
	for k in ["left", "right"]:
		m.add_theme_constant_override("margin_" + k, 12)
	m.add_theme_constant_override("margin_bottom", 12)
	v.add_child(m)
	var tv := VBoxContainer.new()
	tv.add_theme_constant_override("separation", 4)
	m.add_child(tv)
	var tl := HBoxContainer.new()
	tl.add_theme_constant_override("separation", 6)
	tv.add_child(tl)
	var t := Label.new()
	t.text = str(s["title"])
	t.add_theme_font_override("font", UI.heading_font())
	t.add_theme_font_size_override("font_size", fs(15))
	t.add_theme_color_override("font_color", UI.MUT if off else UI.TXT)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tl.add_child(t)
	var chip := ""
	var cc := UI.ACC
	if off:
		chip = T.t("Kommt bald")
		cc = UI.MUT
	elif bool(s["locked"]):
		chip = T.t("Gesperrt")
		cc = UI.ORG
	elif bool(s["done"]):
		chip = T.t("✓ Geschafft")
		cc = UI.GRN
	elif not bool(s["started"]):
		chip = T.t("Neu")
	if chip != "":
		var ch := UI.small(chip, cc)
		ch.autowrap_mode = TextServer.AUTOWRAP_OFF
		ch.add_theme_font_size_override("font_size", fs(11))
		ch.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		tl.add_child(ch)
	var sh := UI.small(str(s["short"]), UI.MUT)
	sh.add_theme_font_size_override("font_size", fs(12))
	sh.custom_minimum_size = Vector2(w - 26.0, 0)
	tv.add_child(sh)
	var meta := UI.small("⏱ " + str(s["dauer"]) + "  ·  " + T.t("ab %d Jahren", [int(s["age"])]), UI.TXT)
	meta.add_theme_font_size_override("font_size", fs(12))
	tv.add_child(meta)
	var ph := HBoxContainer.new()
	ph.add_theme_constant_override("separation", 8)
	tv.add_child(ph)
	var bar := ProgressBar.new()
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(0, 6)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	bar.max_value = 100.0
	bar.value = float(s["pct"])
	ph.add_child(bar)
	var pl := UI.small("%d %%" % int(s["pct"]) + ("  ·  " + str(s["where"]) if str(s["where"]) != "" and not bool(s["done"]) else ""), UI.TXT)
	pl.autowrap_mode = TextServer.AUTOWRAP_OFF
	pl.add_theme_font_size_override("font_size", fs(12))
	ph.add_child(pl)
	var br := HBoxContainer.new()
	br.add_theme_constant_override("separation", 8)
	tv.add_child(br)
	if off:
		var b := _btn(br, T.t("Kommt bald"), func(): pass)
		b.disabled = true
		b.tooltip_text = T.t("Nach Kapitel 5 der «Karte des Grossvaters» gibt es einen Hinweis auf die zweite Karte.")
		return p
	if bool(s["locked"]):
		var b := _btn(br, T.t("Öffnen (Passwort)"), func(): unlock(id), true)
		b.tooltip_text = T.t("Passwortgeschützt – unheimlich, mit Schreckmomenten")
		if id == "horror" and bool(main.horror.knopf_erlaubt()):   # the second button (only the owner, never the children)
			var br2 := HBoxContainer.new()                       # own row: fits the narrow card in every language
			tv.add_child(br2)
			var bo := _btn(br2, T.t("Ohne Passwort starten"), func(): ohne_passwort(id))
			bo.tooltip_text = T.t("Nur für den Besitzer (nicht im Kinder-Modus). Das Passwort bleibt, die Warnung kommt trotzdem.")
		return p
	var can := bool(s["started"]) and (not bool(s["done"]) or id == "grossvater")
	var bw := _btn(br, T.t("Weiterspielen"), func(): weiter(id), can)
	bw.disabled = not can
	_btn(br, T.t("Neu beginnen"), func(): neu(id), not can)
	if id in Trailer.IDS:                                  # Trailer (trailer.gd): eigene Zeile, passt in jeder Sprache
		var br3 := HBoxContainer.new()
		tv.add_child(br3)
		var bt := _btn(br3, T.t("Trailer ansehen"), func(): trailer(id))
		bt.tooltip_text = T.t("Etwa 3 Minuten · Esc oder Klick = zurück")
	return p


func _btn(parent: Control, text: String, cb: Callable, primary := false) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 36 if not kids() else 42)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.add_theme_font_size_override("font_size", fs(14))
	if primary:
		UI.primary(b)
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func picture(id: String, sz: Vector2, locked := false) -> Control:
	"""the picture of the card: from the story itself, else the old map (Grossvater) or a small drawn scene"""
	var c := Panel.new()
	c.custom_minimum_size = sz
	c.clip_contents = true
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	var tex := texture(id) if not (id == "horror" and locked) else null
	if tex != null:
		var tr := TextureRect.new()
		tr.texture = tex
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		tr.set_anchors_preset(Control.PRESET_FULL_RECT)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.add_child(tr)
	elif id == "grossvater":
		var paper := ColorRect.new()
		paper.color = Karte.PAPER.darkened(0.25)
		paper.set_anchors_preset(Control.PRESET_FULL_RECT)
		paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.add_child(paper)
		var k = Karte.new()
		var pc: Array = (main.abenteuer.P.get("pieces", []) as Array).duplicate()
		if not 0 in pc:
			pc.append(0)
		k.pieces = pc
		k.compass = true
		k.set_anchors_preset(Control.PRESET_FULL_RECT)
		k.offset_top = -sz.x * 0.25                       # a part of the square map
		k.offset_bottom = sz.x * 0.25
		c.add_child(k)
	else:
		var d := Bild.new()
		d.kind = id
		d.set_anchors_preset(Control.PRESET_FULL_RECT)
		d.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.add_child(d)
	if locked:                                         # a drawn lock (the emoji has no glyph in the default font)
		var lk := Bild.new()
		lk.kind = "lock"
		lk.set_anchors_preset(Control.PRESET_FULL_RECT)
		lk.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.add_child(lk)
	return c


class Bild extends Control:
	## a small drawn scene from the story (only while there is no picture from playing yet)
	var kind := "maggie"

	func _vgrad(r: Rect2, top: Color, bot: Color) -> void:
		draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]),
				PackedColorArray([top, top, bot, bot]))

	func _ell(c: Vector2, rx: float, ry: float, col: Color) -> void:
		var pts := PackedVector2Array()
		for i in range(20):
			var a := TAU * i / 20.0
			pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
		draw_colored_polygon(pts, col)

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		var w := size.x
		var h := size.y
		match kind:
			"maggie":
				_vgrad(r, Color(0.36, 0.58, 0.86), Color(0.78, 0.88, 0.97))
				var cols := [Color(0.82, 0.48, 0.2), Color(0.93, 0.96, 1.0), Color(0.5, 0.78, 0.42), Color(0.3, 0.6, 0.32)]
				for i in range(4):                          # the four realms: autumn, winter, spring, summer
					var x0 := w * (i / 4.0) - w * 0.08
					var x1 := w * ((i + 1) / 4.0) + w * 0.08
					var pk := Vector2((x0 + x1) / 2.0, h * (0.28 + 0.08 * (i % 2)))
					draw_colored_polygon(PackedVector2Array([Vector2(x0, h), pk, Vector2(x1, h)]), cols[i])
					draw_colored_polygon(PackedVector2Array([pk, pk + Vector2(-w * 0.04, h * 0.1), pk + Vector2(w * 0.04, h * 0.1)]), Color(1, 1, 1, 0.85))
				draw_rect(Rect2(0, h * 0.8, w, h * 0.2), Color(0.32, 0.5, 0.28))
				var cr := Vector2(w * 0.56, h * 0.72)       # the crystal and its light
				for k in range(5):
					draw_circle(cr, 34.0 - k * 6.0, Color(0.62, 0.85, 1.0, 0.08 + k * 0.05))
				draw_colored_polygon(PackedVector2Array([cr + Vector2(0, -16), cr + Vector2(8, 0), cr + Vector2(0, 12), cr + Vector2(-8, 0)]), Color(0.75, 0.92, 1.0))
				var dg := Vector2(w * 0.4, h * 0.82)        # Maggie: a small light terrier with light brown spots
				_ell(dg, 16, 8, Color(0.96, 0.93, 0.86))
				_ell(dg + Vector2(-5, -1), 5, 4, Color(0.78, 0.6, 0.4))
				draw_circle(dg + Vector2(16, -9), 7.0, Color(0.96, 0.93, 0.86))
				draw_colored_polygon(PackedVector2Array([dg + Vector2(12, -14), dg + Vector2(16, -22), dg + Vector2(18, -13)]), Color(0.78, 0.6, 0.4))
				draw_circle(dg + Vector2(21, -9), 1.6, Color(0.1, 0.08, 0.06))
				for lx in [-10.0, -4.0, 7.0, 12.0]:
					draw_rect(Rect2(dg + Vector2(lx, 5), Vector2(3, 7)), Color(0.96, 0.93, 0.86))
			"horror":
				_vgrad(r, Color(0.02, 0.03, 0.05), Color(0.1, 0.12, 0.15))
				draw_colored_polygon(PackedVector2Array([Vector2(0, h), Vector2(0, h * 0.45), Vector2(w * 0.3, h * 0.25), Vector2(w * 0.5, h * 0.4),
						Vector2(w * 0.75, h * 0.2), Vector2(w, h * 0.42), Vector2(w, h)]), Color(0.05, 0.06, 0.08))
				var hx := Vector2(w * 0.58, h * 0.78)       # the old hospice: house, roof, bell tower, light in the window
				draw_rect(Rect2(hx + Vector2(-34, -30), Vector2(68, 30)), Color(0.12, 0.12, 0.13))
				draw_colored_polygon(PackedVector2Array([hx + Vector2(-40, -30), hx + Vector2(0, -52), hx + Vector2(40, -30)]), Color(0.09, 0.09, 0.1))
				draw_rect(Rect2(hx + Vector2(18, -64), Vector2(8, 16)), Color(0.09, 0.09, 0.1))
				for k in range(4):
					draw_circle(hx + Vector2(-14, -16), 16.0 - k * 3.5, Color(1.0, 0.75, 0.35, 0.05 + k * 0.04))
				draw_rect(Rect2(hx + Vector2(-19, -21), Vector2(10, 10)), Color(1.0, 0.8, 0.42))
				draw_rect(Rect2(hx + Vector2(6, -20), Vector2(8, 20)), Color(0.02, 0.02, 0.02))
				for k in range(6):                          # fog
					draw_rect(Rect2(-20 + k * 37 % int(maxf(w, 1.0)), h * (0.55 + 0.07 * k), w * 0.7, 10 + k * 2), Color(0.8, 0.85, 0.9, 0.06))
				draw_rect(Rect2(0, h * 0.82, w, h * 0.18), Color(0.7, 0.75, 0.8, 0.08))
			"lock":
				var m := size / 2.0
				draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.35))
				draw_arc(m + Vector2(0, -6), 11.0, PI, TAU, 16, Color(0.95, 0.8, 0.45), 4.0)
				draw_line(m + Vector2(-11, -6), m + Vector2(-11, 2), Color(0.95, 0.8, 0.45), 4.0)
				draw_line(m + Vector2(11, -6), m + Vector2(11, 2), Color(0.95, 0.8, 0.45), 4.0)
				draw_rect(Rect2(m + Vector2(-17, 0), Vector2(34, 26)), Color(0.95, 0.8, 0.45))
				draw_circle(m + Vector2(0, 11), 3.5, Color(0.2, 0.15, 0.08))
			"teil2":
				draw_rect(r, Color(0.86, 0.78, 0.6).darkened(0.35))
				for k in range(1, 4):
					draw_line(Vector2(w * k / 4.0, 0), Vector2(w * k / 4.0, h), Color(0.33, 0.2, 0.1, 0.2), 1.0)
				draw_line(Vector2(0, h / 2.0), Vector2(w, h / 2.0), Color(0.33, 0.2, 0.1, 0.2), 1.0)
				var pts := [Vector2(w * 0.1, h * 0.8), Vector2(w * 0.3, h * 0.6), Vector2(w * 0.5, h * 0.66), Vector2(w * 0.7, h * 0.4), Vector2(w * 1.02, h * 0.3)]
				for i in range(pts.size() - 1):
					draw_dashed_line(pts[i], pts[i + 1], Color(0.72, 0.12, 0.08, 0.7), 2.0, 6.0)
				draw_string(get_theme_default_font(), Vector2(w * 0.78, h * 0.62), "?", HORIZONTAL_ALIGNMENT_LEFT, -1, 40, Color(0.33, 0.2, 0.1, 0.5))
				draw_rect(r, Color(0, 0, 0, 0.25))


# ---- the buttons of a card -------------------------------------------------------------------------------------------------
func _close_play() -> void:
	if sb != null:
		sb.close()


func weiter(id: String) -> Dictionary:
	"""«Weiterspielen»: straight into the story where it stopped (not started yet: the common start)"""
	if not (id in shown_ids()) or id == "teil2":
		return {"ok": false, "error": "unknown story"}
	if id == "horror" and not bool(main.horror.may_play()):     # H1: «Weiterspielen» before the first night went around
		_close_play()                                          # the password - now the same rule as every other way
		main.horror.open_locked(func(): weiter("horror"))
		return {"ok": true, "locked": true}
	var p := progress(id)
	if not bool(p["started"]):
		open_start(id, "start")
		return {"ok": true, "start": true}
	_close_play()
	SS.set_last_story(id)
	match id:
		"grossvater":
			var r: Dictionary = main.abenteuer.weiter()
			if not bool(r.get("ok", false)) and main.mehr != null:
				main.mehr.toast(str(r.get("error", "")))
			return r
		"maggie":
			main.maggie.weiter()
		"horror":
			main.horror.open_locked(func(): main.horror.weiter())
	return {"ok": true}


func trailer(id: String) -> Dictionary:
	"""«Trailer ansehen»: der Film zur Geschichte (trailer.gd); danach / bei Esc wieder das Fenster «Spielen»"""
	if not (id in shown_ids()) or not id in Trailer.IDS:
		return {"ok": false, "error": "unknown story"}
	var r: Dictionary = await Trailer.inst(main).starten(id, {"von": "karte"})
	return r


func neu(id: String) -> Dictionary:
	"""«Neu beginnen»: the common start (Spielstand → Figur → Schwierigkeit & Jahreszeit)"""
	if not (id in shown_ids()) or id == "teil2":
		return {"ok": false, "error": "unknown story"}
	if id == "horror":
		_close_play()
		main.horror.open_locked(func(): open_start("horror", "neu"))
		return {"ok": true}
	open_start(id, "neu")
	return {"ok": true}


func unlock(id: String) -> void:
	"""the lock of «Das Hospiz»: the password of bergtal_horror.gd, then back to the shelf (the card is open now)"""
	if id != "horror" or not (id in shown_ids()):
		return
	_close_play()
	main.horror.open_locked(func():
		if sb != null:
			sb.open())


func ohne_passwort(id: String) -> void:
	"""«Ohne Passwort starten» on the locked card (only pressed at this PC): unlocked until the restart, then «Weiterspielen»
	(not started yet: the common start) - the warning and the dedication come as always"""
	if id != "horror" or not (id in shown_ids()):
		return
	if bool(main.horror.ohne_passwort().get("ok", false)):
		weiter(id)


# ---- the common start of all stories -------------------------------------------------------------------------------------
func open_start(id: String, what := "neu", from := "spiel") -> void:
	"""what: neu | start (= the whole start) · slot (only the Spielstand) · level (only Schwierigkeit & Jahreszeit);
	from: spiel (back to «Spielen» afterwards / on «Abbrechen») | ab (back to the window of «Die Karte des Grossvaters»)"""
	if main.mehr == null:
		return
	var d := _def(id)
	if d.is_empty():
		return
	var steps := []
	if what in ["neu", "start", "slot"]:
		steps.append("slot")
	if what in ["neu", "start"] and bool(d["figur"]):
		steps.append("figur")
	if (what in ["neu", "start", "level"]) and (bool(d["level"]) or bool(d["season"])):
		steps.append("level")
	_fl = {"id": id, "what": what, "from": from, "steps": steps, "i": 0, "slot": SS.slot(), "err": "", "level": "mittel", "season": "sommer",
			"name": "", "look": {"col": "red", "size": "", "build": "", "hat": "", "pack": true}}
	_fill_from_slot()
	main.mehr.close_menu()
	var title: String = T.t("Neu beginnen: %s", [d["title"]]) if what == "neu" else str(d["title"])
	if what == "slot":
		title = T.t("Spielstand wechseln")
	_body = main.mehr._window(title, "pad")
	main.mehr.win_id = "gstart"
	_paint_start()


func _fill_from_slot() -> void:
	"""what the active Spielstand had chosen last (figure, difficulty, season)"""
	var id: String = _fl["id"]
	if id == "maggie":
		var f: Dictionary = main.maggie.figur()
		_fl["name"] = str(f["name"]) if str(f["name"]) != "" else SS.name_of(SS.slot())
		if not (f["look"] as Dictionary).is_empty():
			_fl["look"] = f["look"]
		MZ.wahl_laden(main, _fl)
	if id == "grossvater":
		_fl["level"] = str(main.abenteuer.W.get("level", "mittel"))
		_fl["season"] = str(main.abenteuer.W.get("season", "sommer"))


func start_open() -> bool:
	return main.mehr != null and main.mehr.win_id == "gstart" and _body != null and is_instance_valid(_body)


func _step() -> String:
	var st: Array = _fl.get("steps", [])
	return str(st[clampi(int(_fl["i"]), 0, st.size() - 1)]) if not st.is_empty() else ""


func _paint_start() -> void:
	if not start_open():
		return
	for c in _body.get_children():
		c.queue_free()
	var W := 600.0
	var steps: Array = _fl["steps"]
	if steps.size() > 1:                               # the steps, like a small bar: 1 Spielstand › 2 Figur › 3 …
		var sr := HBoxContainer.new()
		sr.add_theme_constant_override("separation", 6)
		_body.add_child(sr)
		var names := {"slot": T.t("Spielstand"), "figur": T.t("Figur"), "level": T.t("Schwierigkeit & Jahreszeit")}
		if not bool(_def(_fl["id"])["level"]):
			names["level"] = T.t("Jahreszeit")
		for i in range(steps.size()):
			var l := UI.small("%d  %s" % [i + 1, names[steps[i]]] + ("   ›" if i < steps.size() - 1 else ""), UI.ACC if i == int(_fl["i"]) else UI.MUT)
			l.autowrap_mode = TextServer.AUTOWRAP_OFF
			l.add_theme_font_size_override("font_size", fs(13))
			sr.add_child(l)
	match _step():
		"slot":
			_page_slot(W)
		"figur":
			_page_figur(W)
		"level":
			_page_level(W)
	if str(_fl["err"]) != "":
		_body.add_child(UI.small("⚠ " + str(_fl["err"]), UI.RED))
	var nav := HBoxContainer.new()
	nav.add_theme_constant_override("separation", 8)
	_body.add_child(nav)
	if int(_fl["i"]) > 0:
		var bk := Button.new()
		bk.text = T.t("‹ Zurück")
		bk.custom_minimum_size = Vector2(110, 38)
		bk.pressed.connect(func(): gs({"k": "back"}))
		nav.add_child(bk)
	var ab := Button.new()
	ab.text = T.t("Abbrechen")
	ab.custom_minimum_size = Vector2(110, 38)
	ab.pressed.connect(func(): gs({"k": "cancel"}))
	nav.add_child(ab)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nav.add_child(sp)
	var nx := Button.new()
	var last := int(_fl["i"]) >= steps.size() - 1
	nx.text = (T.t("Übernehmen") if str(_fl["what"]) in ["slot", "level"] else T.t("Los geht's!")) if last else T.t("Weiter ›")
	nx.custom_minimum_size = Vector2(170, 38)
	nx.add_theme_font_size_override("font_size", fs(14))
	UI.primary(nx)
	nx.pressed.connect(func(): gs({"k": "next"}))
	nav.add_child(nx)


func _say(t: String, sz := 14, col := UI.TXT) -> Label:
	var l := UI.small(t, col)
	l.add_theme_font_size_override("font_size", fs(sz))
	l.custom_minimum_size = Vector2(600, 0)
	_body.add_child(l)
	return l


func _page_slot(W: float) -> void:
	var id: String = _fl["id"]
	_say(T.t("Wer spielt? Wähle deinen Spielstand – jeder in der Familie kann seinen eigenen haben."), 15)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_body.add_child(row)
	var title: String = _def(id)["title"]
	for n in range(1, SS.N + 1):
		var nm := SS.name_of(n) if SS.name_of(n) != "" else T.t("Spielstand %d", [n])
		var pc := progress_of_slot(id, n)
		var lv := SS.lv_of(n)
		var b := Button.new()
		b.custom_minimum_size = Vector2((W - 16.0) / 3.0, 86)
		b.text = nm + "\n" + (T.t("Stufe %d", [lv]) if lv > 0 else T.t("noch leer")) + "\n" + (T.t("%d %% geschafft", [pc]) if pc > 0 else T.t("noch nicht begonnen"))
		b.tooltip_text = title
		b.add_theme_font_size_override("font_size", fs(13))
		if n == int(_fl["slot"]):
			UI.primary(b)
		var nn := n
		b.pressed.connect(func(): gs({"k": "slot", "v": nn}))
		row.add_child(b)
	var nr := HBoxContainer.new()
	nr.add_theme_constant_override("separation", 8)
	_body.add_child(nr)
	var nl := Label.new()
	nl.text = T.t("Name des Spielstands")
	nl.add_theme_font_size_override("font_size", fs(14))
	nr.add_child(nl)
	var le := LineEdit.new()
	le.name = "SlotName"
	le.text = SS.name_of(int(_fl["slot"]))
	le.placeholder_text = T.t("z. B. Lea")
	le.max_length = 24
	le.custom_minimum_size = Vector2(220, 34)
	le.text_changed.connect(func(t): _fl["slot_name"] = t)
	nr.add_child(le)
	var pc := progress_of_slot(id, int(_fl["slot"]))
	if str(_fl["what"]) == "neu" and pc > 0:
		_say(T.t("Achtung: «%s» beginnt in diesem Spielstand von vorne (%d %% sind geschafft). Stufe und Abzeichen bleiben. Ein leerer Spielstand behält alles.", [title, pc]), 13, UI.ORG)


func _page_figur(W: float) -> void:
	_say(T.t("Wer bist du? Gib deiner Figur einen Namen und such dir aus, wie sie aussieht."), 15)
	var look: Dictionary = _fl["look"]
	var r0 := _row(T.t("Name"))
	var le := LineEdit.new()
	le.text = str(_fl["name"])
	le.placeholder_text = T.t("Dein Name")
	le.max_length = 16
	le.custom_minimum_size = Vector2(260, 36)
	le.text_changed.connect(func(t): _fl["name"] = t)
	r0.add_child(le)
	var r1 := _row(T.t("Jacke"))
	for c in Mg.COLS:
		var b := Button.new()
		b.custom_minimum_size = Vector2(38, 34)
		b.tooltip_text = T.t(Mg.COL_NAMES[c])
		var on: bool = str(look.get("col", "")) == c
		var st := UI.box(Figur.LOOK_COLS[c], Color.WHITE if on else UI.LINE, 8, 4, 3 if on else 1)
		for k in ["normal", "hover", "pressed"]:
			b.add_theme_stylebox_override(k, st)
		var cc: String = c
		b.pressed.connect(func(): gs({"k": "look", "key": "col", "v": cc}))
		r1.add_child(b)
	_choice(T.t("Grösse"), "size", [["s", T.t("klein")], ["", T.t("mittel")], ["l", T.t("gross")]])
	_choice(T.t("Figur"), "build", [["slim", T.t("schlank")], ["", T.t("normal")], ["strong", T.t("kräftig")]])
	_choice(T.t("Kopf"), "hat", [["", T.t("Haare")], ["cap", T.t("Mütze")], ["hood", T.t("Kapuze")]])
	var note := str(_def(_fl["id"]).get("figur_note", ""))
	if note != "":
		_say(note, 13, UI.MUT)
	if str(_fl["id"]) == "maggie":
		MZ.seite_figur(self, _fl)                         # 1 oder 2 Spieler, Rolle und Figur von Spieler 2
	le.grab_focus.call_deferred()


func _row(label: String) -> HBoxContainer:
	var r := HBoxContainer.new()
	r.add_theme_constant_override("separation", 8)
	_body.add_child(r)
	var l := Label.new()
	l.text = label
	l.custom_minimum_size = Vector2(110, 0)
	l.add_theme_font_size_override("font_size", fs(14))
	r.add_child(l)
	return r


func _choice(label: String, key: String, opts: Array) -> void:
	var r := _row(label)
	for o in opts:
		var b := Button.new()
		b.text = str(o[1])
		b.custom_minimum_size = Vector2(110, 34)
		b.add_theme_font_size_override("font_size", fs(14))
		if str((_fl["look"] as Dictionary).get(key, "")) == str(o[0]):
			UI.primary(b)
		var val: String = o[0]
		b.pressed.connect(func(): gs({"k": "look", "key": key, "v": val}))
		r.add_child(b)


func _page_level(W: float) -> void:
	var d := _def(_fl["id"])
	var kid := kids()
	if bool(d["level"]):
		_say(T.t("Wie schwierig?"), 15)
		if kid:
			_say(T.t("Kinder-Modus: immer Leicht, keine Gefahren (Eis, Fels), kein Hunger, kurze Texte."), 13, UI.ORG)
		var g := GridContainer.new()
		g.columns = 3
		g.add_theme_constant_override("h_separation", 8)
		g.add_theme_constant_override("v_separation", 8)
		_body.add_child(g)
		for k in AbD.LEVEL_ORDER:
			var on: bool = (k == "leicht") if kid else str(_fl["level"]) == k
			g.add_child(_pick_card(T.t(str(AbD.LEVELS[k][0])), _first(T.t(str(AbD.LEVELS[k][1]))), on, kid and k != "leicht", "level", k, (W - 16.0) / 3.0))
	if bool(d["season"]):
		_say(T.t("Jahreszeit (gilt für die ganze Runde)"), 15)
		var g2 := GridContainer.new()
		g2.columns = 4
		g2.add_theme_constant_override("h_separation", 8)
		g2.add_theme_constant_override("v_separation", 8)
		_body.add_child(g2)
		for sn in Ab.SEASONS:
			g2.add_child(_pick_card(T.t(str(sn[1])), _first(T.t(str(sn[2]))), str(_fl["season"]) == str(sn[0]), false, "season", str(sn[0]), (W - 24.0) / 4.0, 104.0))


static func _first(s: String) -> String:
	var i := s.find(". ")
	return s.substr(0, i + 1) if i > 0 else s


func _pick_card(title: String, text: String, on: bool, off: bool, key: String, val: String, w: float, h := 74.0) -> Control:
	var b := Button.new()
	b.custom_minimum_size = Vector2(w, h * (1.2 if kids() else 1.0))
	b.text = title + "\n" + text
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.add_theme_font_size_override("font_size", fs(12))
	b.disabled = off
	if on:
		UI.primary(b)
	b.pressed.connect(func(): gs({"k": key, "v": val}))
	return b


func _finish() -> Dictionary:
	"""the last step: into the story"""
	var id: String = _fl["id"]
	var what: String = _fl["what"]
	if main.mehr != null:
		main.mehr.close_window()
	_body = null
	match what:
		"slot":
			if str(_fl.get("from", "")) == "ab" and main.abenteuer != null:
				main.abenteuer.open_ab()
			elif sb != null:
				sb.open()
			return {"ok": true, "slot": SS.slot()}
		"level":
			main.abenteuer.neu(str(_fl["level"]), str(_fl["season"]), false)
			return {"ok": true}
	SS.set_last_story(id)
	match id:
		"grossvater":
			main.abenteuer.neu("leicht" if kids() else str(_fl["level"]), str(_fl["season"]), true)
		"maggie":
			MZ.wahl_merken(main, _fl)
			main.maggie.beginnen(str(_fl["name"]), _fl["look"])
		"horror":
			main.horror.neu_beginnen()
	return {"ok": true, "id": id}


func open_slots() -> void:
	"""«Spielstand wechseln» in the head line of «Spielen»: only the choice of the place (with the level of each)"""
	var ids := shown_ids()
	open_start(SS.last_story() if SS.last_story() in ids and SS.last_story() != "teil2" else str(ids[0]) if not ids.is_empty() else "grossvater", "slot")


func _err_text(e: String) -> String:
	return {"tour": T.t("Gerade läuft eine Tour – erst am Lager oder nach dem Morgen wechseln."),
			"geschichte": T.t("Gerade läuft eine Geschichte – zuerst beenden, dann wechseln."),
			"test": T.t("Das Entwicklertool «Kapitel-Sprung» ist aktiv – zuerst dort beenden.")}.get(e, e)


func gs(d: Dictionary) -> Dictionary:
	"""a button of the common start (also /control for tests)"""
	if _fl.is_empty():
		return {"ok": false, "error": "no start"}
	_fl["err"] = ""
	if MZ.gs_taste(_fl, d):                             # Maggie: zwei (1 | 2), rolle, name2, col2
		_paint_start()
		return gs_info()
	match str(d.get("k", "info")):
		"slot":
			_fl["slot"] = clampi(int(d.get("v", 1)), 1, SS.N)
			_fl.erase("slot_name")
		"name":
			_fl["name"] = str(d.get("v", ""))
		"slot_name":
			_fl["slot_name"] = str(d.get("v", ""))
		"look", "col":
			var key := "col" if str(d.get("k")) == "col" else str(d.get("key", "col"))
			(_fl["look"] as Dictionary)[key] = str(d.get("v", ""))
		"level":
			if AbD.LEVELS.has(str(d.get("v", ""))):
				_fl["level"] = str(d["v"])
		"season":
			_fl["season"] = str(d.get("v", "sommer"))
		"back":
			_fl["i"] = maxi(0, int(_fl["i"]) - 1)
		"cancel":
			var back := str(_fl.get("from", ""))
			_fl = {}
			if main.mehr != null:
				main.mehr.close_window()
			if back == "ab" and main.abenteuer != null:
				main.abenteuer.open_ab()
			elif sb != null:
				sb.open()
			return {"ok": true, "closed": true}
		"next":
			if _step() == "slot":
				var n := int(_fl["slot"])
				if _fl.has("slot_name"):
					SS.set_slot_name(n, str(_fl["slot_name"]))
				if n != SS.slot():
					var r: Dictionary = SS.switch(main, n)
					if not bool(r.get("ok", false)):
						_fl["err"] = _err_text(str(r.get("error", "")))
						_paint_start()
						return gs_info()
					_fill_from_slot()
				if str(_fl["name"]) == "":
					_fl["name"] = SS.name_of(n)
			if int(_fl["i"]) >= (_fl["steps"] as Array).size() - 1:
				var r := _finish()
				_fl = {}
				return r
			_fl["i"] = int(_fl["i"]) + 1
	_paint_start()
	return gs_info()


func gs_info() -> Dictionary:
	if _fl.is_empty():
		return {"ok": true, "open": false}
	return {"ok": true, "open": start_open(), "id": _fl["id"], "what": _fl["what"], "step": _step(), "steps": _fl["steps"], "slot": _fl["slot"],
			"level": _fl["level"], "season": _fl["season"], "name": _fl["name"], "look": _fl["look"], "err": _fl["err"],
			"zwei": _fl.get("zwei", {})}
