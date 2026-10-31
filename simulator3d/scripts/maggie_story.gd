extends Node
## «Maggie und der Bergkristall» (Daniel, 31.10.2026) – eine Geschichte für Kinder (ca. 12) im Bergtal. Paket S1 «Rahmen».
## Eigene Kachel unter «Spielen» (spielbereich.gd). Alles selbst erfunden (nur lose Inspiration: vier Reiche = vier
## Jahreszeiten). Ablauf:
##   Figur wählen (Name + Aussehen) → Einstieg: Spaziergang auf der Alp, Maggie gräbt einen leuchtenden Bergkristall aus,
##   in seinem Licht kurze Bilder der Zukunft → Auswahl der Region (Reihenfolge frei: Herbst, Winter, Frühling, Sommer) →
##   jede Region: Rastplätze (Autosave), Aufgaben der Module, Jahreszeiten-Tor am Ende → nach allen vier: Finale am Gipfel
##   (Bergkapelle, dort ruht der Kristall sicher) → Abspann.
## Gehen: W A S D / Pfeile (Shift = rennen), Maus ziehen = umschauen, Rad = näher / weiter, K = in den Kristall schauen
## (Bild der Zukunft), Esc = Pause. Controller: linker Stick = gehen, rechter Stick = umschauen.
## Erwischt von einem bösen Tier: kurzer Schreck (dunkler, ein Rauschen – kein Schrei, nichts Hartes), dann sicher
## zurück zum letzten Rastplatz; der Kristall bleibt bei dir. MoveEye wird nicht aufgestellt: es ist «einfach dabei»
## und sagt ab und zu, was es jetzt machen würde (moveeye_sagt).
## Speichern: user://maggie/spielstand.json (Name, Aussehen, geschaffte Regionen, Region + letzter Rastplatz, Finale).
## Lite (Quality.lite()): kein Bild-Effekt beim Zukunftsbild (nur Tönung), weniger Teilchen, keine Schatten der Lichter.
##
## API für S2 (maggie_hund.gd / maggie_helfer.gd) und S3 (maggie_gefahr.gd) – Zugriff über main.maggie (oder `story`):
##   region_aktiv() -> String         "herbst" | "winter" | "fruehling" | "sommer" | "" (keine Region läuft: Einstieg, Auswahl,
##                                    Finale; Pause / Zukunftsbild zählen als laufend)
##   spieler_pos() -> Vector3         wo die Spielfigur steht (WELT-Koordinaten, wie main.ground_y / visitors)
##   spieler() -> Node3D              die Figur selbst (actor.gd, controlled) oder null
##   kristall_bei_spieler() -> bool   der Kristall ist bei der Figur (true, sobald Maggie ihn ausgegraben hat)
##   erwischt(von: String)            ein böses Tier hat die Figur erwischt ("wildschwein" | "wolf" | "kraehe" | "viper" …):
##                                    kurzer Schreck, dann sicher zurück zum letzten Rastplatz; der Kristall bleibt. Danach
##                                    ein paar Sekunden Schonzeit (geschuetzt() = true) – in der Zeit nicht nochmals erwischen.
##   geschuetzt() -> bool             gerade erwischt / Schreck läuft / Karte offen / Pause / Film: böse Tiere warten
##   tipp(text: String)               kurzer Tipp unten im Bild (einfache Sprache; schon mit T.t() übersetzt übergeben)
##   moveeye_sagt(text: String)       ein kurzer Satz «MoveEye würde jetzt …» (kindgerecht, keine Technik-Wörter)
##   aufgabe_anmelden(id: String, text: String)   eine Aufgabe der Region (Rätsel, Schutzding …) – nach region_gestartet
##   aufgabe_erledigt(id: String)     die Aufgabe ist geschafft. Sind alle angemeldeten Aufgaben erledigt, leuchtet das
##                                    Jahreszeiten-Tor am Ende der Region; wer hindurchgeht, hat die Region geschafft
##                                    (ohne angemeldete Aufgaben ist das Tor nach 2 s offen). region_fertig(id) geht auch direkt.
##   tor_pos() -> Vector3             wo das Jahreszeiten-Tor der Region steht (Welt)
##   region_fertig(id: String)        die Region ist geschafft -> Freude, Speichern, zurück zur Auswahl der Regionen
##   region_mitte(id: String) -> Vector3   die Mitte einer Region in WELT-Koordinaten auf dem Boden (gilt für die Szene,
##                                    die gerade gebaut ist; jede Region baut das Bergtal neu, mit ihrer Jahreszeit)
##   tal_punkt(x: float, z: float) -> Vector3   Tal-Koordinaten (bergtal.gd: x = Osten, z = Süden) -> Welt, auf dem Boden
##   rastplatz_pos() -> Vector3       der letzte Rastplatz (Welt)
##   zukunftsbild_ort(pos: Vector3, text: String)   ein Ort, den der Kristall als «Bild der Zukunft» zeigen darf (eine
##                                    Gefahr oder ein Weg; text z. B. T.t("Hinter den Felsen warten Wölfe.")) – gilt bis
##                                    zum Ende der Region
##   spieler_setzen(welt_pos: Vector3)  die Figur dorthin setzen (Steinbock trägt dich; Maggie setzt S2 selbst)
##   speichern()                      sofort speichern (nach einem gelösten Rätsel); dabei auch zustand() der Module
##   boese_ablenken(welt_pos, sekunden)   die bösen Tiere laufen dorthin (Fuchs, S2) -> ablenken(pos, secs) der Module (S3)
## Module-Speicher: hat ein Modul zustand() -> Dictionary, wird das beim Autosave (Rastplatz, speichern()) mitgespeichert
##   und beim Weiterspielen mit laden(d) bzw. lade(d) zurückgegeben; neu() (wenn vorhanden) beim Neubeginn.
## Sperren: hat ein Modul sperren() -> [[welt_pos, radius], …], hält der Rahmen die Figur aus diesen Kreisen heraus.
## Tasten: der Rahmen nimmt W A S D, Pfeile, Shift, K, Esc; die Module (Kinder dieses Knotens) bekommen jede Taste zuerst
##   (S3: B = Schutzding benutzen); Maggies Knöpfe sind am Bildschirm.
##   signal szene_bereit(art)         das Bergtal ist (neu) gebaut und die Figur steht dort: art = "einstieg" | Region-id |
##                                    "finale" (S2: Maggie neben die Figur setzen)
##   signal region_gestartet(id)      eine Region beginnt (Szene fertig gebaut, Figur am ersten / letzten Rastplatz)
##   signal region_beendet(id)        die Region ist vorbei (geschafft oder verlassen): eigene Knoten der Region entfernen
##   signal einstieg_graben(pos)      der Einstieg: Maggie soll bei pos graben (S2 lässt den Hund hinlaufen und graben)
##   signal geschichte_beendet()      die Geschichte wurde verlassen oder ist fertig (alles aufräumen)
## Module: gibt es res://scripts/maggie_hund.gd, maggie_helfer.gd oder maggie_gefahr.gd, wird jedes beim Start der
## Geschichte angelegt (als Kind dieses Knotens, wenn es ein Node ist); vorher werden (wenn vorhanden) die Variablen
## `main` und `story` gesetzt. Beim Beenden werden sie wieder entfernt.
## Test / Fernsteuerung: /control {"action": "maggie", "do": "info" | "open" | "start" (name, look) | "region" (id) |
##   "aufgabe" (id, text) | "erledigt" (id) | "fertig" | "erwischt" (von) | "zukunft" | "finale" | "rast" (i) | "gehe" (x, z
##   = Welt) | "pause" | "weiter" | "stop" | "reset"}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Welt = preload("res://scripts/maggie_welt.gd")
const ActorS = preload("res://scripts/actor.gd")
const Figur = preload("res://scripts/figur.gd")

signal szene_bereit(art: String)
signal region_gestartet(id: String)
signal region_beendet(id: String)
signal einstieg_graben(pos: Vector3)
signal geschichte_beendet()

const REGIONEN := ["herbst", "winter", "fruehling", "sommer"]
# the middle of every region (valley coordinates x, z of bergtal.gd)
const MITTE := {"herbst": Vector2(-640, -200), "winter": Vector2(590, 360), "fruehling": Vector2(-120, -250), "sommer": Vector2(-530, 480)}
const SAVE_FILE := "user://maggie/spielstand.json"
const MODULES := ["res://scripts/maggie_hund.gd", "res://scripts/maggie_helfer.gd", "res://scripts/maggie_gefahr.gd"]
const COLS := ["red", "orange", "navy", "olive", "brown", "grey", "white", "black"]
const COL_NAMES := {"red": "Rot", "orange": "Orange", "navy": "Dunkelblau", "olive": "Olivgrün", "brown": "Braun", "grey": "Grau",
		"white": "Weiss", "black": "Schwarz"}
const TIERE := {"wildschwein": "Ein Wildschwein", "wolf": "Ein Wolf", "kraehe": "Die Krähen", "viper": "Eine Viper"}
const WALK := ["intro_walk", "region", "finale_walk"]
const REST_R := 5.0                   # a rest place counts as reached closer than this (m)
const TOR_R := 2.0
const ZK_PAUSE := 35.0                # the crystal needs a rest between two pictures of the future (s)

var main
var running := false                  # the story is on (from the start of the walk to the end)
var phase := ""                       # "" | figur | reise | intro | intro_walk | intro_dig | auswahl | region | schreck | film |
                                      # pause | geschafft | finale | finale_walk | finale_cut | abspann | ende
var region := ""
var player: Node3D = null
var has_crystal := false
var S := {}                           # the saved state
var _seq := 0                         # +1 on every new stage: old timers stop
var _root: Node3D = null              # the things of the stage (rest places, gate, chapel …)
var _proot: Node3D = null             # the figure
var _crystal: Node3D = null
var _crystal_on_player := false
var _rests: Array = []                # [{pos, node, reached}]
var _last_rest := 0
var _rest := Vector3.ZERO
var _tor: Node3D = null
var _tor_p := Vector3.ZERO
var _tor_open := false
var _tor_check_at := 0.0
var _beam: MeshInstance3D = null
var _tasks := {}                      # id -> {text, done}
var _task_order: Array = []
var _safe_until := 0.0
var _zk_orte: Array = []              # [pos, text]
var _zk_i := 0
var _zk_ready_at := 0.0
var _modules: Array = []
var _saved := {}
var _dig_p := Vector3.ZERO
var _chapel: Node3D = null
var _me_next := 0.0
var _region_t0 := 0.0
var _resume_phase := ""
# camera
var cam_yaw := 0.0
var cam_pitch := 0.42
var cam_dist := 6.5
var _drag_t := -10.0
var _shots: Array = []                # film: [{at, look, fly, hold, text}]
var _shot_i := 0
var _shot_t := 0.0
var _shot_from := Transform3D.IDENTITY
var _shot_cb := Callable()
var _film_back := false
var _film_prev := ""
# ui
var _layer: CanvasLayer = null
var _ui: Control = null
var _card: PanelContainer = null
var _hud: Control = null
var _hud_title: Label = null
var _hud_tasks: Label = null
var _hud_goal: Label = null
var _arrow: Control = null
var _tipp: Label = null
var _tipp_until := 0.0
var _me_box: PanelContainer = null
var _me_lbl: Label = null
var _me_until := 0.0
var _help: Label = null
var _kbtn: Button = null
var _fade: ColorRect = null
var _fade_lbl: Label = null
var _zk_fx: ColorRect = null
var _zk_lbl: Label = null
var _credits: Control = null
var _snd: AudioStreamPlayer = null
var _streams := {}
var _name_edit: LineEdit = null
var _look := {}


class Arrow:
	extends Control
	var ang := 0.0
	var col := Color(1, 1, 1)

	func _draw() -> void:
		var c := size / 2.0
		var pts := PackedVector2Array([Vector2(0, -16), Vector2(11, 10), Vector2(0, 4), Vector2(-11, 10)])
		var out := PackedVector2Array()
		for p in pts:
			out.append(c + p.rotated(ang))
		draw_colored_polygon(out, col)
		draw_polyline(out + PackedVector2Array([out[0]]), Color(0, 0, 0, 0.7), 2.0)


class Eye:
	extends Control

	func _draw() -> void:
		var c := size / 2.0
		var pts := PackedVector2Array()
		for i in range(24):
			var a := i * TAU / 24.0
			pts.append(c + Vector2(cos(a) * 16.0, sin(a) * 9.0 * pow(absf(sin(a)), 0.4)))
		draw_colored_polygon(pts, Color(0.9, 0.94, 1.0))
		draw_circle(c, 6.0, Color(0.23, 0.55, 1.0))
		draw_circle(c, 2.6, Color(0.02, 0.04, 0.08))


func _ready() -> void:
	process_priority = 50                 # after main: the camera of the window is ours while walking
	_load()


# =======================================================================================================================
# API (S2 / S3)
# =======================================================================================================================
func _bt():
	if main == null or main.scenes == null:
		return null
	return main.scenes.data.get("bergtal", null)


func tal_punkt(x: float, z: float) -> Vector3:
	var bt = _bt()
	if bt == null:
		return Vector3(x, 0.0, z)
	var p: Vector3 = bt.WG(x, z)
	p.y = main.ground_y(p.x, p.z)
	return p


func region_mitte(id: String) -> Vector3:
	var m: Vector2 = MITTE.get(id, Vector2.ZERO)
	return tal_punkt(m.x, m.y)


func region_aktiv() -> String:
	return region if running else ""


func spieler() -> Node3D:
	return player if player != null and is_instance_valid(player) else null


func spieler_pos() -> Vector3:
	var p := spieler()
	return p.global_position if p != null else Vector3.ZERO


func kristall_bei_spieler() -> bool:
	return running and has_crystal


func geschuetzt() -> bool:
	return not running or phase not in WALK or main.now() < _safe_until


func rastplatz_pos() -> Vector3:
	return _rest


func tor_pos() -> Vector3:
	return _tor_p


func tipp(text: String) -> void:
	if _tipp == null:
		return
	_tipp.text = text
	_tipp.visible = true
	_tipp_until = main.now() + clampf(3.0 + text.length() * 0.06, 5.0, 11.0)


func moveeye_sagt(text: String) -> void:
	if _me_lbl == null:
		return
	_me_lbl.text = text
	_me_box.visible = true
	_me_until = main.now() + clampf(3.0 + text.length() * 0.07, 6.0, 12.0)
	_me_next = maxf(_me_next, main.now() + 45.0)


func zukunftsbild_ort(pos: Vector3, text: String) -> void:
	for z in _zk_orte:
		if (z[0] as Vector3).distance_to(pos) < 3.0:
			z[1] = text
			return
	_zk_orte.append([pos, text])


func aufgabe_anmelden(id: String, text: String) -> void:
	if not _tasks.has(id):
		_task_order.append(id)
	_tasks[id] = {"text": text, "done": bool(_tasks.get(id, {}).get("done", false))}
	_paint_tasks()


func aufgabe_erledigt(id: String) -> void:
	if not _tasks.has(id):
		_tasks[id] = {"text": id, "done": true}
		_task_order.append(id)
	_tasks[id]["done"] = true
	_paint_tasks()


func erwischt(von: String) -> void:
	if not running or phase not in ["region", "finale_walk", "intro_walk"] or main.now() < _safe_until:
		return
	var sq := _seq
	phase = "schreck"
	_safe_until = main.now() + 9.0
	_freeze(true)
	S["erwischt"] = int(S.get("erwischt", 0)) + 1
	_play("whoosh")
	_fade_lbl.text = T.t("Puh, das war knapp!") + "\n\n" + T.t("%s wollte den Kristall. Maggie bellt laut – und ihr lauft schnell zurück zum Rastplatz.",
			[T.t(TIERE.get(von, "Ein wildes Tier"))])
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 0.86, 0.35)
	tw.parallel().tween_property(_fade_lbl, "modulate:a", 1.0, 0.35)
	await get_tree().create_timer(2.4).timeout
	if sq != _seq or not running:
		return
	_place_player(_rest)
	_cam_snap()
	var tw2 := create_tween()
	tw2.tween_property(_fade, "color:a", 0.0, 0.9)
	tw2.parallel().tween_property(_fade_lbl, "modulate:a", 0.0, 0.5)
	await tw2.finished
	if sq != _seq or not running or phase != "schreck":
		return
	phase = "finale_walk" if str(S.get("region", "")) == "finale" else ("region" if region != "" else "intro_walk")
	_freeze(false)
	_safe_until = main.now() + 5.0
	moveeye_sagt(T.t(_pick(Welt.MOVEEYE["erwischt"])))


func spieler_setzen(welt_pos: Vector3) -> void:
	_place_player(welt_pos)


func speichern() -> void:
	_modules_save()
	_save()


func boese_ablenken(welt_pos: Vector3, sekunden: float) -> void:
	for m in _modules:
		if is_instance_valid(m) and m.has_method("ablenken"):
			m.ablenken(welt_pos, sekunden)


func _mod_key(m) -> String:
	var sc = m.get_script()
	return str(sc.resource_path.get_file().get_basename()) if sc != null else ""


func _modules_save() -> void:
	var d := {}
	for m in _modules:
		if is_instance_valid(m) and m.has_method("zustand"):
			d[_mod_key(m)] = m.zustand()
	S["module"] = d


func _modules_load() -> void:
	var d: Dictionary = S.get("module", {}) if S.get("module", {}) is Dictionary else {}
	for m in _modules:
		if not is_instance_valid(m):
			continue
		var k := _mod_key(m)
		if not d.has(k):
			if m.has_method("neu"):
				m.neu()
			elif m.has_method("laden"):
				m.laden({})
			elif m.has_method("lade"):
				m.lade({})
			continue
		if m.has_method("laden"):
			m.laden(d[k])
		elif m.has_method("lade"):
			m.lade(d[k])


func _modules_pause(on: bool) -> void:
	for m in _modules:
		if is_instance_valid(m) and m.has_method("pause"):
			m.pause(on)


func _sperren() -> void:
	var a = spieler()
	if a == null:
		return
	for m in _modules:
		if not is_instance_valid(m) or not m.has_method("sperren"):
			continue
		for e in m.sperren():
			var c: Vector3 = e[0]
			var r := float(e[1]) + 0.3
			var dv := Vector2(a.position.x - c.x, a.position.z - c.z)
			if dv.length() < r:
				var n := dv.normalized() if dv.length() > 0.01 else Vector2(1, 0)
				a.position.x = c.x + n.x * r
				a.position.z = c.z + n.y * r


func region_fertig(id: String) -> void:
	if not running or id != region or region == "":
		return
	_seq += 1
	phase = "geschafft"
	_freeze(true)
	var done: Array = S.get("done", [])
	if not (id in done):
		done.append(id)
	S["done"] = done
	S["region"] = ""
	S["rest"] = 0
	var mins := int((main.now() - _region_t0) / 60.0)
	var times: Dictionary = S.get("minutes", {})
	times[id] = int(times.get(id, 0)) + mins
	S["minutes"] = times
	_modules_save()
	_save()
	_play("fanfare")
	region_beendet.emit(id)
	var r: Dictionary = Welt.REG[id]
	region = ""
	_clear_stage_things()
	_hud.visible = false
	var v := _new_card(T.t("Geschafft!"), r["col"])
	_text(v, T.t(str(r["done"])), 17)
	var left := 4 - done.size()
	if left > 0:
		_text(v, T.t("Noch %d Jahreszeiten – dann geht es hinauf zum Gipfel.", [left]) if left > 1 else T.t("Noch eine Jahreszeit – dann geht es hinauf zum Gipfel."), 14, UI.MUT)
	else:
		_text(v, T.t("Alle vier Jahreszeiten sind geschafft! Jetzt bringst du den Kristall hinauf zur Bergkapelle."), 15, UI.GRN)
	var row := _row(v)
	_button(row, T.t("Weiter"), _choose_card, true)


# =======================================================================================================================
# state
# =======================================================================================================================
func _load() -> void:
	S = {}
	if FileAccess.file_exists(SAVE_FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(SAVE_FILE))
		if d is Dictionary:
			S = d


func _save() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_FILE.get_base_dir())
	var f := FileAccess.open(SAVE_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(S))
		f.close()


func done_count() -> int:
	return (S.get("done", []) as Array).size()


func _pick(a: Array) -> String:
	return str(a[randi() % a.size()]) if not a.is_empty() else ""


func info() -> Dictionary:
	var p := spieler_pos()
	var tasks := []
	for id in _task_order:
		tasks.append({"id": id, "text": _tasks[id]["text"], "done": _tasks[id]["done"]})
	var rs := []
	for r in _rests:
		rs.append(bool(r["reached"]))
	return {"ok": true, "running": running, "phase": phase, "region": region, "has_crystal": has_crystal, "save": S,
			"player": [snappedf(p.x, 0.1), snappedf(p.y, 0.1), snappedf(p.z, 0.1)], "rests": rs, "last_rest": _last_rest,
			"tor": [snappedf(_tor_p.x, 0.1), snappedf(_tor_p.z, 0.1)], "tor_open": _tor_open, "tasks": tasks,
			"zukunft_orte": _zk_orte.size(), "modules": _modules.size(), "geschuetzt": geschuetzt(), "scene": main.scene,
			"lite": Welt.lite()}


# =======================================================================================================================
# the tile under «Spielen» (spielbereich.gd)
# =======================================================================================================================
func kachel(W: float) -> Control:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UI.box(UI.PANEL2, Color(0.62, 0.85, 1.0) if running else UI.LINE, 12, 8, 1))
	p.custom_minimum_size = Vector2(W, 0)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	p.add_child(h)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var tl := HBoxContainer.new()
	tl.add_theme_constant_override("separation", 6)
	v.add_child(tl)
	var t := Label.new()
	t.text = T.t("Maggie und der Bergkristall")
	t.add_theme_font_override("font", UI.heading_font())
	t.add_theme_font_size_override("font_size", 14)
	tl.add_child(t)
	var n := done_count()
	var chip := ""
	var cc := UI.ACC
	if bool(S.get("finale", false)):
		chip = T.t("✓ Geschafft")
		cc = UI.GRN
	elif not bool(S.get("intro", false)):
		chip = T.t("Neu")
	if chip != "":
		var ch := UI.small(chip, cc)
		ch.autowrap_mode = TextServer.AUTOWRAP_OFF
		ch.add_theme_font_size_override("font_size", 11)
		tl.add_child(ch)
	var sh := UI.small(T.t("Mit Maggie, dem kleinen Hund, bringst du einen leuchtenden Kristall durch vier Jahreszeiten zum Gipfel. Etwa 2 Stunden, ein bisschen gruselig."), UI.MUT)
	sh.custom_minimum_size = Vector2(W - 230.0, 0)
	v.add_child(sh)
	if bool(S.get("intro", false)) and not bool(S.get("finale", false)):
		v.add_child(UI.small(T.t("%d von 4 Jahreszeiten geschafft", [n]), UI.TXT))
	var b := Button.new()
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.custom_minimum_size = Vector2(150, 34)
	b.text = T.t("Weiter spielen") if bool(S.get("intro", false)) or running else T.t("Geschichte starten")
	UI.primary(b)
	b.pressed.connect(func():
		if main.spielbereich != null:
			main.spielbereich.close()
		open())
	h.add_child(b)
	return p


# =======================================================================================================================
# start: choose the figure, or go on
# =======================================================================================================================
func open() -> void:
	_ensure_ui()
	if main.mehr != null:
		main.mehr.close_menu()
	if running:
		if phase in WALK:
			_pause()
		return
	_load()
	if not bool(S.get("intro", false)):
		_figure_card()
	else:
		_continue_card()


func _continue_card() -> void:
	phase = "figur"
	var v := _new_card(T.t("Maggie und der Bergkristall"), Color(0.62, 0.85, 1.0))
	if bool(S.get("finale", false)):
		_text(v, T.t("Du hast die Geschichte schon geschafft – der Kristall ruht in der Bergkapelle. Willst du nochmals von vorne beginnen?"))
	else:
		_text(v, T.t("Schön, bist du wieder da, %s! %d von 4 Jahreszeiten sind geschafft.", [str(S.get("name", "")), done_count()]))
		var rg := str(S.get("region", ""))
		if Welt.REG.has(rg):
			_text(v, T.t("Du warst im %s, beim Rastplatz %d.", [T.t(str(Welt.REG[rg]["name"])), int(S.get("rest", 0)) + 1]), 14, UI.MUT)
	var row := _row(v)
	if not bool(S.get("finale", false)):
		_button(row, T.t("Weiter spielen"), _resume, true)
	_button(row, T.t("Neu beginnen"), func():
		var keep := {"name": S.get("name", ""), "look": S.get("look", {})}
		S = keep
		_save()
		_figure_card(), bool(S.get("finale", false)))
	_button(row, T.t("Schliessen"), _close_cards)


func _figure_card() -> void:
	phase = "figur"
	_look = (S.get("look", {}) as Dictionary).duplicate() if S.get("look", {}) is Dictionary else {}
	if _look.is_empty():
		_look = {"col": "red", "size": "", "build": "", "hat": "", "pack": true}
	var v := _new_card(T.t("Maggie und der Bergkristall"), Color(0.62, 0.85, 1.0), 640)
	_text(v, T.t("Wer bist du? Gib deiner Figur einen Namen und such dir aus, wie sie aussieht."), 15)
	var r0 := _row(v)
	var nl := Label.new()
	nl.text = T.t("Name")
	nl.custom_minimum_size = Vector2(110, 0)
	r0.add_child(nl)
	_name_edit = LineEdit.new()
	_name_edit.text = str(S.get("name", ""))
	_name_edit.placeholder_text = T.t("Dein Name")
	_name_edit.max_length = 16
	_name_edit.custom_minimum_size = Vector2(260, 36)
	r0.add_child(_name_edit)
	var r1 := _row(v)
	var cl := Label.new()
	cl.text = T.t("Jacke")
	cl.custom_minimum_size = Vector2(110, 0)
	r1.add_child(cl)
	for c in COLS:
		var b := Button.new()
		b.custom_minimum_size = Vector2(38, 34)
		b.tooltip_text = T.t(COL_NAMES[c])
		var sb := UI.box(Figur.LOOK_COLS[c], Color.WHITE if _look.get("col", "") == c else UI.LINE, 8, 4, 3 if _look.get("col", "") == c else 1)
		b.add_theme_stylebox_override("normal", sb)
		b.add_theme_stylebox_override("hover", sb)
		b.add_theme_stylebox_override("pressed", sb)
		var cc: String = c
		b.pressed.connect(func():
			_look["col"] = cc
			_keep_name()
			_figure_card())
		r1.add_child(b)
	_choice_row(v, T.t("Grösse"), "size", [["s", T.t("klein")], ["", T.t("mittel")], ["l", T.t("gross")]])
	_choice_row(v, T.t("Figur"), "build", [["slim", T.t("schlank")], ["", T.t("normal")], ["strong", T.t("kräftig")]])
	_choice_row(v, T.t("Kopf"), "hat", [["", T.t("Haare")], ["cap", T.t("Mütze")], ["hood", T.t("Kapuze")]])
	_text(v, T.t("Maggie ist euer Familienhund: ein kleiner, heller Terrier mit hellbraunen Flecken. Sie hat eine sehr gute Nase."), 13, UI.MUT)
	var row := _row(v)
	_button(row, T.t("Los geht's!"), _begin, true)
	_button(row, T.t("Abbrechen"), _close_cards)
	_name_edit.grab_focus.call_deferred()


func _keep_name() -> void:
	if _name_edit != null and is_instance_valid(_name_edit):
		S["name"] = _name_edit.text.strip_edges()


func _choice_row(v: Control, label: String, key: String, opts: Array) -> void:
	var r := _row(v)
	var l := Label.new()
	l.text = label
	l.custom_minimum_size = Vector2(110, 0)
	r.add_child(l)
	for o in opts:
		var b := Button.new()
		b.text = str(o[1])
		b.custom_minimum_size = Vector2(110, 34)
		if str(_look.get(key, "")) == str(o[0]):
			UI.primary(b)
		var val: String = o[0]
		b.pressed.connect(func():
			_look[key] = val
			_keep_name()
			_figure_card())
		r.add_child(b)


func _begin() -> void:
	_keep_name()
	if str(S.get("name", "")) == "":
		S["name"] = T.t("Du")
	S["look"] = _look
	S["started"] = int(main.now())
	_save()
	_start()
	_start_intro()


func _resume() -> void:
	_start()
	var rg := str(S.get("region", ""))
	has_crystal = true
	if Welt.REG.has(rg):
		_start_region(rg, int(S.get("rest", 0)))
	elif rg == "finale":
		_start_finale()
	else:
		_choose_card()


func _start() -> void:
	"""the story takes the world: keep what it changes"""
	if running:
		return
	_ensure_ui()
	running = true
	_saved = {"hour": main.hour(), "speed": main.speed, "weather": main.weather, "auto": main.auto_visitors, "bt_events": main.bt_events,
			"bt_season": main.bt_season, "bt_spot": main.bt_spot, "bt_free": (main.bt_free as Array).duplicate(), "bt_bed": main.bt_bed,
			"scene": main.scene, "panel": main.ui_root.visible}
	main.auto_visitors = false
	main.bt_events = false
	main.show_panel(false)
	if main.explore != null and main.explore.on:
		main.explore.set_on(false)
	_root = Node3D.new()
	_root.name = "MaggieWelt"
	add_child(_root)
	_proot = Node3D.new()
	_proot.name = "MaggieFigur"
	add_child(_proot)
	_load_modules()
	_modules_load()


func _load_modules() -> void:
	for path in MODULES:
		if not ResourceLoader.exists(path):
			continue
		var scr = load(path)
		if scr == null:
			continue
		var m = scr.new()
		if "main" in m:
			m.main = main
		if "story" in m:
			m.story = self
		if m is Node:
			add_child(m)
		_modules.append(m)


func stop() -> void:
	"""leave the story: everything back as before (the progress stays saved)"""
	if not running:
		_close_cards()
		return
	_seq += 1
	if region != "":
		region_beendet.emit(region)
	region = ""
	geschichte_beendet.emit()
	for m in _modules:
		if m is Node and is_instance_valid(m):
			(m as Node).queue_free()
	_modules.clear()
	running = false
	phase = ""
	has_crystal = false
	_crystal = null
	_crystal_on_player = false
	if _root != null:
		_root.queue_free()
	if _proot != null:
		_proot.queue_free()
	_root = null
	_proot = null
	player = null
	_rests.clear()
	_tor = null
	_chapel = null
	_beam = null
	_shots.clear()
	_close_cards()
	if _hud != null:
		_hud.visible = false
	if _zk_fx != null:
		_zk_fx.visible = false
	if _credits != null:
		_credits.queue_free()
		_credits = null
	_fade.color.a = 0.0
	_fade_lbl.modulate.a = 0.0
	main.auto_visitors = bool(_saved.get("auto", true))
	main.bt_events = bool(_saved.get("bt_events", true))
	main.weather = str(_saved.get("weather", "clear"))
	main.bt_season = str(_saved.get("bt_season", "auto"))
	main.bt_spot = str(_saved.get("bt_spot", "huette"))
	main.bt_free = _saved.get("bt_free", [])
	main.bt_bed = str(_saved.get("bt_bed", "tent"))
	main.set_hour(float(_saved.get("hour", 12.0)))
	main._set_speed(float(_saved.get("speed", 1.0)))
	var sc := str(_saved.get("scene", main.scene))
	if sc != "" and (sc != main.scene or sc == "bergtal"):
		main.set_scene(sc)
	if bool(_saved.get("panel", true)):
		main.show_panel(true)


# =======================================================================================================================
# building a stage: the Bergtal with a season, the spot of MoveEye at the first rest place
# =======================================================================================================================
func _build_stage(season: String, spot: Vector2, hour: float, weather: String, art: String) -> bool:
	_seq += 1
	var sq := _seq
	phase = "reise"
	_hud.visible = false
	var v := _new_card(T.t("Unterwegs …"), Color(0.62, 0.85, 1.0), 460)
	_text(v, T.t("Einen Moment – das Tal wird vorbereitet."), 15, UI.MUT)
	await get_tree().process_frame
	await get_tree().process_frame
	if sq != _seq or not running:
		return false
	_clear_stage_things()
	main.bt_season = season
	main.bt_spot = "frei"
	main.bt_free = [spot.x, spot.y, 0.0]
	main.bt_bed = "tent"
	main.set_scene("bergtal")
	await get_tree().process_frame
	if sq != _seq or not running:
		return false
	if _bt() == null:
		main.start_info = T.t("Das Bergtal fehlt – die Geschichte braucht die Szene Bergtal.")
		stop()
		return false
	main.weather = weather
	main.set_hour(hour)
	main._set_speed(0.0)
	_clear_card()
	_ensure_player(tal_punkt(spot.x, spot.y) + Vector3(-2.0, 0, 3.5))
	_cam_snap()
	szene_bereit.emit(art)
	return true


func _clear_stage_things() -> void:
	if _root != null:
		for c in _root.get_children():
			if c != _crystal:
				c.queue_free()
	_rests.clear()
	_tor = null
	_tor_open = false
	_chapel = null
	_beam = null
	_tasks.clear()
	_task_order.clear()
	_zk_orte.clear()
	_zk_i = 0


func _ensure_player(at: Vector3) -> void:
	if spieler() == null:
		var a = ActorS.new()
		a.controlled = true
		var lk: Dictionary = S.get("look", {}) if S.get("look", {}) is Dictionary else {}
		a.look = lk.duplicate()
		a.look["pack"] = true
		a.player_color = Figur.LOOK_COLS.get(str(lk.get("col", "red")), Figur.LOOK_COLS["red"])
		_proot.add_child(a)
		a.setup(main, "person", at, at + Vector3(0, 0, -1), 1.5)
		player = a
	_place_player(at)
	if has_crystal:
		_crystal_to_player()


func _place_player(at: Vector3) -> void:
	var a = spieler()
	if a == null:
		return
	at.y = main.ground_y(at.x, at.z)
	a.position = at
	a.cur_speed = 0.0
	a.ctl_move = Vector2.ZERO


func _freeze(on: bool) -> void:
	var a = spieler()
	if a != null:
		a.frozen = on
		a.ctl_move = Vector2.ZERO


func _crystal_to_player() -> void:
	if _crystal == null or not is_instance_valid(_crystal):
		_crystal = Welt.crystal(1.0)
		_root.add_child(_crystal)
	_crystal_on_player = true


# =======================================================================================================================
# the start: a walk with Maggie on the Alp – Maggie digs out the crystal
# =======================================================================================================================
func _start_intro() -> void:
	has_crystal = false
	var ok: bool = await _build_stage("herbst", Welt.INTRO_SPOT, 17.3, "clear", "einstieg")
	if not ok:
		return
	_dig_p = tal_punkt(Welt.INTRO_DIG.x, Welt.INTRO_DIG.y)
	_beam = Welt.beam(Color(0.62, 0.85, 1.0))
	_root.add_child(_beam)
	_beam.position = _dig_p + Vector3(0, 35, 0)
	phase = "intro"
	_freeze(true)
	var v := _new_card(T.t("Ein Abendspaziergang"), Color(0.62, 0.85, 1.0))
	_text(v, T.t("Ein ruhiger Herbstabend auf der Alp. Du gehst mit Maggie spazieren, eurem kleinen Hund. MoveEye ist auch dabei und passt beim Zelt auf."), 16)
	_text(v, T.t("Plötzlich bleibt Maggie stehen. Sie schnuppert … und rennt los!"), 16)
	_text(v, T.t("Gehen: W A S D oder Pfeiltasten · Shift = rennen · Maus ziehen = umschauen · Esc = Pause"), 13, UI.MUT)
	var row := _row(v)
	_button(row, T.t("Maggie folgen"), func():
		_clear_card()
		phase = "intro_walk"
		_freeze(false)
		_hud.visible = true
		_hud_title.text = T.t("Ein Abendspaziergang")
		_hud_tasks.text = ""
		einstieg_graben.emit(_dig_p)
		tipp(T.t("Folge Maggie! Sie hat etwas gerochen – dort, wo das Licht leuchtet."))
		moveeye_sagt(T.t(_pick(Welt.MOVEEYE["einstieg"]))), true)


func _dig() -> void:
	var sq := _seq
	phase = "intro_dig"
	_freeze(true)
	tipp(T.t("Maggie gräbt und gräbt …"))
	var d := Welt.dirt()
	_root.add_child(d)
	d.position = _dig_p + Vector3(0, 0.1, 0)
	d.emitting = true
	await get_tree().create_timer(2.6).timeout
	if sq != _seq:
		return
	d.emitting = false
	_crystal = Welt.crystal(1.6)
	_root.add_child(_crystal)
	_crystal.position = _dig_p + Vector3(0, -0.3, 0)
	var sp := Welt.sparkles(Color(0.7, 0.9, 1.0))
	_crystal.add_child(sp)
	sp.emitting = true
	_play("chime")
	var tw := create_tween()
	tw.tween_property(_crystal, "position", _dig_p + Vector3(0, 1.1, 0), 1.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tipp(T.t("Ein Bergkristall! Er leuchtet ganz von selbst."))
	await get_tree().create_timer(2.6).timeout
	if sq != _seq:
		return
	_crystal.queue_free()
	_crystal = null
	has_crystal = true
	_crystal_to_player()
	if _beam != null:
		_beam.visible = false
	# the first pictures of the future: the four valleys and the summit
	var shots := []
	for id in Welt.ORDER:
		var c := region_mitte(id)
		shots.append({"look": c, "at": c + Vector3(80, 60, 80), "fly": 1.8, "hold": 2.8,
				"text": T.t(str(Welt.REG[id]["short"]))})
	var g := tal_punkt(Welt.CHAPEL.x, Welt.CHAPEL.y)
	shots.append({"look": g, "at": g + Vector3(40, 30, -30), "fly": 1.8, "hold": 3.2,
			"text": T.t("Ganz oben am Gipfel steht eine kleine Bergkapelle. Dort ist der Kristall sicher.")})
	_film(shots, T.t("Im Licht des Kristalls siehst du Bilder der Zukunft …"), _story_card)


func _story_card() -> void:
	phase = "intro"
	_freeze(true)
	S["intro"] = true
	_save()
	var v := _new_card(T.t("Der Bergkristall"), Color(0.62, 0.85, 1.0))
	_text(v, T.t("In seinem Licht sieht man kurze Bilder der Zukunft. Darum darf der Kristall nicht in falsche Hände geraten."), 16)
	_text(v, T.t("Böse Tiere wollen ihn haben. Bring ihn mit Maggie durch alle vier Jahreszeiten hinauf zur Bergkapelle am Gipfel. Dort ruht er sicher."), 16)
	_text(v, T.t("Die Reihenfolge darfst du selbst wählen. Wenn dich ein Tier erwischt, ist das nicht schlimm: Du kommst zurück zum letzten Rastplatz, und der Kristall bleibt bei dir."), 14, UI.MUT)
	_text(v, T.t("Drück K, um in den Kristall zu schauen – er zeigt dir dann eine Gefahr oder einen Weg."), 14, UI.MUT)
	var row := _row(v)
	_button(row, T.t("Wohin zuerst?"), _choose_card, true)


# =======================================================================================================================
# choose the region (free order) – and the summit after all four
# =======================================================================================================================
func _choose_card() -> void:
	phase = "auswahl"
	_freeze(true)
	_hud.visible = false
	var done: Array = S.get("done", [])
	var v := _new_card(T.t("Wohin gehst du?"), Color(0.62, 0.85, 1.0), 660)
	_text(v, T.t("Jede Jahreszeit ist ein eigenes Tal mit eigenen Gefahren. Wähle eins aus."), 15)
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 10)
	g.add_theme_constant_override("v_separation", 10)
	v.add_child(g)
	for id in Welt.ORDER:
		var r: Dictionary = Welt.REG[id]
		var b := Button.new()
		var ok: bool = id in done
		b.text = T.t(str(r["name"])) + ("   ✓" if ok else "") + "\n" + T.t(str(r["short"]))
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.custom_minimum_size = Vector2(305, 74)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.disabled = ok
		if not ok:
			var sb := UI.box(UI.PANEL2, r["col"], 10, 8, 2)
			b.add_theme_stylebox_override("normal", sb)
		var rid: String = id
		b.pressed.connect(func(): _start_region(rid, 0))
		g.add_child(b)
	_text(v, T.t("%d von 4 geschafft", [done.size()]), 13, UI.MUT)
	var row := _row(v)
	var fb := _button(row, T.t("Zum Gipfel"), _start_finale, done.size() >= 4)
	fb.disabled = done.size() < 4
	fb.tooltip_text = T.t("Erst wenn alle vier Jahreszeiten geschafft sind.")
	_button(row, T.t("Speichern und beenden"), stop)


# =======================================================================================================================
# a region
# =======================================================================================================================
func _start_region(id: String, rest_i: int) -> void:
	var r: Dictionary = Welt.REG[id]
	S["region"] = id
	S["rest"] = rest_i
	_save()
	var rs: Array = r["rests"]
	var ok: bool = await _build_stage(id, rs[0], float(r["hour"]), str(r["weather"]), id)
	if not ok:
		return
	var sq := _seq
	region = id
	_region_t0 = main.now()
	var col: Color = r["col"]
	for i in range(rs.size()):
		var p := tal_punkt((rs[i] as Vector2).x, (rs[i] as Vector2).y)
		var mp := p + (Vector3(-3.5, 0, -1.0) if i == 0 else Vector3.ZERO)      # (the first one: beside the tent and MoveEye)
		mp.y = main.ground_y(mp.x, mp.z)
		var n := Welt.rest_place(i + 1, col)
		_root.add_child(n)
		n.position = mp
		_rests.append({"pos": mp, "node": n, "reached": i <= rest_i})
		if i <= rest_i:
			Welt.rest_lit(n, col)
	_last_rest = clampi(rest_i, 0, rs.size() - 1)
	_rest = _rests[_last_rest]["pos"] + Vector3(1.5, 0, 2.0)
	var tz: Vector2 = r["tor"]
	_tor_p = tal_punkt(tz.x, tz.y)
	_tor = Welt.gate(col)
	_root.add_child(_tor)
	_tor.position = _tor_p
	var from := _rests[_rests.size() - 1]["pos"] as Vector3
	_tor.rotation.y = atan2(from.x - _tor_p.x, from.z - _tor_p.z)
	_tor_open = false
	_beam = Welt.beam(col)
	_root.add_child(_beam)
	_place_player(_rest)
	_cam_snap()
	_tor_check_at = main.now() + 2.0
	region_gestartet.emit(id)
	_freeze(true)
	phase = "region"
	_safe_until = main.now() + 1e6                       # the card first
	var v := _new_card(T.t(str(r["name"])), col)
	_text(v, T.t(str(r["intro"])), 16)
	_text(v, T.t("Geh von Rastplatz zu Rastplatz bis zum Jahreszeiten-Tor. Das Tor leuchtet, wenn alle Aufgaben gelöst sind."), 14, UI.MUT)
	var row := _row(v)
	_button(row, T.t("Los!"), func():
		if sq != _seq:
			return
		_clear_card()
		_hud.visible = true
		_paint_tasks()
		_film([_shot_to(_tor_p)], T.t("Der Kristall zeigt dir das Ziel: das Jahreszeiten-Tor."), func():
			_safe_until = main.now() + 3.0
			tipp(T.t(str(r["tipp"])))
			moveeye_sagt(T.t(_pick(Welt.MOVEEYE["start"])))
			_me_next = main.now() + 70.0
			_zk_ready_at = main.now() + 20.0), true)
	_button(row, T.t("Zurück zur Auswahl"), func():
		region_beendet.emit(id)
		region = ""
		S["region"] = ""
		_save()
		_clear_stage_things()
		_choose_card())


func _region_tick() -> void:
	_sperren()
	var p := spieler_pos()
	var r: Dictionary = Welt.REG[region]
	for i in range(_rests.size()):
		var e: Dictionary = _rests[i]
		if Vector2(p.x - e["pos"].x, p.z - e["pos"].z).length() < REST_R:
			if not bool(e["reached"]) or _last_rest != i:
				var first := not bool(e["reached"])
				e["reached"] = true
				_last_rest = i
				_rest = e["pos"] + Vector3(1.5, 0, 2.0)
				S["rest"] = i
				_modules_save()
				_save()
				if first:
					Welt.rest_lit(e["node"], r["col"])
					_play("rest")
					tipp(T.t("Rastplatz %d erreicht – gespeichert. Wenn dich ein Tier erwischt, kommst du hierher zurück.", [i + 1]))
					moveeye_sagt(T.t(_pick(Welt.MOVEEYE["rast"])))
	if not _tor_open and main.now() > _tor_check_at and _all_tasks_done():
		_tor_open = true
		Welt.gate_open(_tor, r["col"], true)
		_play("chime")
		tipp(T.t("Das Jahreszeiten-Tor leuchtet! Geh hindurch."))
		moveeye_sagt(T.t(_pick(Welt.MOVEEYE["tor"])))
	if _tor_open and Vector2(p.x - _tor_p.x, p.z - _tor_p.z).length() < TOR_R:
		region_fertig(region)
		return
	if main.now() > _me_next:
		_me_next = main.now() + randf_range(80.0, 130.0)
		moveeye_sagt(T.t(_pick(Welt.MOVEEYE.get(region, []))))


func _all_tasks_done() -> bool:
	for id in _tasks:
		if not bool(_tasks[id]["done"]):
			return false
	return true


func _next_goal() -> Array:
	"""[world position, name] of where to go next"""
	if str(S.get("region", "")) == "finale" and _chapel != null:
		return [_chapel.to_global(Welt.ALTAR + Vector3(0, 0, 1.2)), T.t("Bergkapelle")]
	if phase == "intro_walk":
		return [_dig_p, T.t("Maggie")]
	for i in range(_rests.size()):
		if not bool(_rests[i]["reached"]):
			return [_rests[i]["pos"], T.t("Rastplatz %d", [i + 1])]
	if _tor != null:
		return [_tor_p, T.t("Jahreszeiten-Tor") if _tor_open else T.t("Jahreszeiten-Tor (noch zu)")]
	return []


# =======================================================================================================================
# the summit: the Bergkapelle – there the crystal is safe
# =======================================================================================================================
func _start_finale() -> void:
	S["region"] = "finale"
	_save()
	var ok: bool = await _build_stage("sommer", Welt.FIN_START, 19.4, "clear", "finale")
	if not ok:
		return
	var sq := _seq
	var c := tal_punkt(Welt.CHAPEL.x, Welt.CHAPEL.y)
	var st := spieler_pos()
	_chapel = Welt.chapel()
	_root.add_child(_chapel)
	_chapel.position = c
	_chapel.rotation.y = atan2(st.x - c.x, st.z - c.z)
	if Welt.lite():
		var cl := _chapel.get_node_or_null("candles") as OmniLight3D
		if cl != null:
			cl.omni_range = 3.5
	_beam = Welt.beam(Color(1.0, 0.9, 0.6))
	_root.add_child(_beam)
	_rest = st
	phase = "finale"
	_freeze(true)
	_safe_until = main.now() + 1e6
	var v := _new_card(T.t("Hinauf zum Gipfel"), Color(1.0, 0.85, 0.5))
	_text(v, T.t("Alle vier Jahreszeiten sind geschafft. Die Sonne geht langsam unter. Nur noch ein kurzes Stück – oben wartet die kleine Bergkapelle."), 16)
	_text(v, T.t("Bring den Kristall hinein und leg ihn auf den Stein vor dem Altar."), 14, UI.MUT)
	var row := _row(v)
	_button(row, T.t("Los!"), func():
		if sq != _seq:
			return
		_clear_card()
		_hud.visible = true
		_hud_title.text = T.t("Zum Gipfel")
		_hud_tasks.text = ""
		phase = "finale_walk"
		_film([_shot_to(c + Vector3(0, 2, 0))], T.t("Der Kristall zeigt dir die Bergkapelle."), func():
			_safe_until = main.now() + 2.0
			moveeye_sagt(T.t("MoveEye würde jetzt den Weg nach oben im Auge behalten."))), true)


func _finale_tick() -> void:
	var a = spieler()
	if a == null or _chapel == null:
		return
	var lp := _chapel.to_local(a.global_position)
	var q := Welt.chapel_push(lp, 0.3)
	if q != lp:
		var g := _chapel.to_global(q)
		a.position.x = g.x
		a.position.z = g.z
	var altar := _chapel.to_global(Welt.ALTAR + Vector3(0, 0, 0.75))
	if Vector2(a.global_position.x - altar.x, a.global_position.z - altar.z).length() < 0.9:
		_finale_cut()


func _finale_cut() -> void:
	var sq := _seq
	phase = "finale_cut"
	_freeze(true)
	_hud.visible = false
	S["region"] = ""
	_save()
	var holder := _chapel.to_global(Welt.ALTAR + Vector3(0, 1.14, 0))
	_crystal_on_player = false
	var tw := create_tween()
	tw.tween_property(_crystal, "global_position", holder, 2.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.parallel().tween_property(_crystal, "scale", Vector3.ONE * 1.8, 2.2)
	await tw.finished
	if sq != _seq:
		return
	has_crystal = false
	_play("chime")
	var sp := Welt.sparkles(Color(0.75, 0.92, 1.0))
	_crystal.add_child(sp)
	sp.emitting = true
	var l := _crystal.get_node_or_null("light") as OmniLight3D
	if l != null:
		create_tween().tween_property(l, "light_energy", 3.0, 2.0)
		l.omni_range = 6.0
	if _beam != null:
		_beam.position = holder + Vector3(0, 35, 0)
		_beam.visible = true
	moveeye_sagt(T.t(_pick(Welt.MOVEEYE["finale"])))
	var c := _chapel.global_position
	var fw := _chapel.global_transform.basis.z
	var rt := _chapel.global_transform.basis.x
	var shots := [{"look": holder, "at": _chapel.to_global(Vector3(0.9, 1.6, 0.6)), "fly": 2.0, "hold": 2.5, "text": T.t("Der Kristall leuchtet heller als je zuvor.")},
			{"look": c + Vector3(0, 3, 0), "at": c + fw * 14.0 + rt * 8.0 + Vector3(0, 5, 0), "fly": 2.5, "hold": 2.5, "text": T.t("Jetzt ruht er sicher in der Bergkapelle.")},
			{"look": c + Vector3(0, 3, 0), "at": c - fw * 12.0 + rt * 14.0 + Vector3(0, 9, 0), "fly": 3.0, "hold": 2.5, "text": T.t("Die bösen Tiere können ihn hier nicht mehr finden.")},
			{"look": c + Vector3(0, 2, 0), "at": c - rt * 30.0 + Vector3(0, 18, 0), "fly": 3.5, "hold": 3.0, "text": T.t("Und unten im Tal wird es ganz still.")}]
	_play("fanfare")
	_film(shots, "", _final_card, false)


func _final_card() -> void:
	phase = "ende"
	_play("fanfare")
	var v := _new_card(T.t("Geschafft!"), Color(1.0, 0.85, 0.5))
	_text(v, T.t("Du hast den Bergkristall durch alle vier Jahreszeiten getragen, %s. Jetzt ruht er sicher in der Bergkapelle.", [str(S.get("name", ""))]), 17)
	_text(v, T.t("Danke, Maggie – ohne deine Nase hätten wir das nie geschafft!"), 16)
	var mins := 0
	for k in (S.get("minutes", {}) as Dictionary):
		mins += int(S["minutes"][k])
	_text(v, T.t("Unterwegs: etwa %d Minuten · erwischt: %d Mal (zum Glück immer gut ausgegangen)", [mins, int(S.get("erwischt", 0))]), 13, UI.MUT)
	var row := _row(v)
	_button(row, T.t("Abspann"), _abspann, true)


func _abspann() -> void:
	var sq := _seq
	phase = "abspann"
	_clear_card()
	S["finale"] = true
	_save()
	if _credits != null:
		_credits.queue_free()
	_credits = ColorRect.new()
	(_credits as ColorRect).color = Color(0.02, 0.03, 0.06, 0.92)
	_credits.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ui.add_child(_credits)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 14)
	box.custom_minimum_size = Vector2(700, 0)
	_credits.add_child(box)
	var lines := [[T.t("Maggie und der Bergkristall"), 30], ["", 20],
			[T.t("Mit"), 15], [str(S.get("name", "")), 24], [T.t("Maggie, der kleine Terrier mit der guten Nase"), 18], ["", 10],
			[T.t("Die Helfer"), 15], [T.t("die Eule, die im Dunkeln den Weg zeigt"), 17], [T.t("der Steinbock, der über steile Felsen trägt"), 17],
			[T.t("das Murmeltier, das pfeift und Geheimgänge kennt"), 17], [T.t("der Fuchs, der die bösen Tiere ablenkt"), 17], ["", 10],
			[T.t("Die bösen Tiere (die am Ende leer ausgingen)"), 15], [T.t("Wildschweine · Wölfe · Krähen · Vipern"), 17], ["", 10],
			[T.t("Immer dabei"), 15], [T.t("MoveEye, das gut aufgepasst hat"), 18], ["", 10],
			[T.t("Eine Geschichte im Bergtal des MoveEye-Simulators"), 14], [T.t("Für alle, die gerne mit ihrem Hund unterwegs sind."), 14], ["", 30],
			[T.t("Ende"), 28]]
	for ln in lines:
		var l := Label.new()
		l.text = str(ln[0])
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(700, 0)
		l.add_theme_font_size_override("font_size", int(ln[1]))
		l.add_theme_color_override("font_color", UI.TXT if int(ln[1]) >= 17 else UI.MUT)
		box.add_child(l)
	var skip := Button.new()
	skip.text = T.t("Überspringen")
	skip.position = Vector2(20, 20)
	skip.pressed.connect(func():
		if sq == _seq and phase == "abspann":
			_end_card())
	_credits.add_child(skip)
	await get_tree().process_frame
	if sq != _seq or _credits == null:
		return
	var vs := _ui.size
	box.position = Vector2((vs.x - 700.0) / 2.0, vs.y + 10.0)
	var tw := create_tween()
	tw.tween_property(box, "position:y", -box.size.y - 20.0, 30.0)
	await tw.finished
	if sq == _seq and phase == "abspann":
		_end_card()


func _end_card() -> void:
	phase = "ende"
	if _credits != null:
		_credits.queue_free()
		_credits = null
	var v := _new_card(T.t("Ende"), Color(1.0, 0.85, 0.5), 520)
	_text(v, T.t("Danke fürs Spielen!"), 17)
	var row := _row(v)
	_button(row, T.t("Zurück zu «Spielen»"), func():
		stop()
		if main.spielbereich != null:
			main.spielbereich.open(), true)
	_button(row, T.t("Nochmals von vorne"), func():
		var keep := {"name": S.get("name", ""), "look": S.get("look", {})}
		S = keep
		_save()
		stop()
		open())


# =======================================================================================================================
# pictures of the future (the crystal) and other camera films
# =======================================================================================================================
func _shot_to(target: Vector3) -> Dictionary:
	var p := spieler_pos()
	var d := Vector3(target.x - p.x, 0, target.z - p.z)
	if d.length() < 1.0:
		d = Vector3(0, 0, -1)
	d = d.normalized()
	var at := target - d * 16.0 + Vector3(0, 8.0, 0) + d.cross(Vector3.UP) * 5.0
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 4.0)
	return {"look": target + Vector3(0, 1.0, 0), "at": at, "fly": 1.6, "hold": 3.0, "text": ""}


func _film(shots: Array, title: String, cb: Callable, crystal_fx := true) -> void:
	if shots.is_empty():
		cb.call()
		return
	_film_prev = phase if phase != "film" else _film_prev
	phase = "film"
	_freeze(true)
	_shots = shots
	_shot_i = 0
	_shot_t = 0.0
	_shot_from = main.view_cam.global_transform
	_shot_cb = cb
	_film_back = false
	_zk_fx.visible = crystal_fx
	if crystal_fx:
		_play("chime")
	_zk_lbl.visible = true
	_zk_lbl.text = title if title != "" else str(shots[0].get("text", ""))
	_hud.visible = false


func _film_tick(dt: float) -> void:
	var cam: Camera3D = main.view_cam
	_shot_t += dt
	if _film_back:
		var k := clampf(_shot_t / 1.0, 0.0, 1.0)
		cam.global_transform = _shot_from.interpolate_with(_follow_xform(), smoothstep(0.0, 1.0, k))
		if k >= 1.0:
			_film_end()
		return
	var s: Dictionary = _shots[_shot_i]
	var to := Transform3D(Basis.IDENTITY, s["at"]).looking_at(s["look"], Vector3.UP)
	var fly := float(s["fly"])
	var k2 := clampf(_shot_t / fly, 0.0, 1.0)
	cam.global_transform = _shot_from.interpolate_with(to, smoothstep(0.0, 1.0, k2))
	if _shot_t > fly * 0.6 and str(s.get("text", "")) != "":
		_zk_lbl.text = str(s["text"])
	if _shot_t >= fly + float(s["hold"]):
		_shot_i += 1
		_shot_t = 0.0
		_shot_from = cam.global_transform
		if _shot_i >= _shots.size():
			_film_back = phase_after_film_follows()


func phase_after_film_follows() -> bool:
	"""after the film: fly back to the figure (true) – except when a card or the end follows"""
	if _film_prev in WALK or _film_prev == "region" or spieler() != null:
		return true
	_film_end()
	return false


func _film_end() -> void:
	_shots.clear()
	_film_back = false
	_zk_fx.visible = false
	_zk_lbl.visible = false
	phase = _film_prev
	if phase in WALK:
		_freeze(false)
		_hud.visible = true
	if _shot_cb.is_valid():
		var cb := _shot_cb
		_shot_cb = Callable()
		cb.call()


func _film_skip() -> void:
	if phase != "film":
		return
	_shot_i = _shots.size() - 1
	var s: Dictionary = _shots[_shot_i]
	_shot_t = float(s["fly"]) + float(s["hold"])


func look_into_crystal() -> void:
	"""K: the crystal shows a danger or a way (a place S2 / S3 told, else the next goal)"""
	if not running or phase not in WALK or not has_crystal:
		return
	var t: float = main.now()
	if t < _zk_ready_at:
		tipp(T.t("Der Kristall muss sich noch ein wenig ausruhen (%d s).", [int(ceil(_zk_ready_at - t))]))
		return
	_zk_ready_at = t + ZK_PAUSE
	var pos := Vector3.ZERO
	var text := ""
	if not _zk_orte.is_empty():
		var best := -1
		var bd := 1e9
		for k in range(_zk_orte.size()):            # the nearest of the ones not shown last time
			var i := (_zk_i + k) % _zk_orte.size()
			var d := (_zk_orte[i][0] as Vector3).distance_to(spieler_pos())
			if d < bd and (i != _zk_i - 1 or _zk_orte.size() == 1):
				bd = d
				best = i
		best = maxi(best, 0)
		_zk_i = best + 1
		pos = _zk_orte[best][0]
		text = str(_zk_orte[best][1])
	else:
		var g := _next_goal()
		if g.is_empty():
			return
		pos = g[0]
		text = T.t("Der Weg führt dorthin: %s.", [str(g[1])])
	var keep := _safe_until
	_film([_shot_to(pos)], T.t("Der Kristall zeigt: %s", [text]), func():
		_safe_until = maxf(keep, main.now() + 2.0))


# =======================================================================================================================
# every frame: walking, camera, HUD
# =======================================================================================================================
func _process(dt: float) -> void:
	if not running:
		return
	if _crystal != null and is_instance_valid(_crystal) and _crystal_on_player and spieler() != null:
		var a = spieler()
		var tt: float = Time.get_ticks_msec() / 1000.0
		var side: Vector3 = a.global_transform.basis.x
		_crystal.global_position = a.global_position + side * 0.38 + Vector3(0, 1.25 + 0.05 * sin(tt * 2.2), 0)
		_crystal.rotation.y = tt * 0.8
	if phase == "film":
		_film_tick(dt)
		return
	if phase == "abspann" or phase == "reise":
		return
	if spieler() == null:
		return
	if main.scene != "bergtal" or _bt() == null:
		main.start_info = T.t("Die Geschichte wurde unterbrochen (andere Szene).")
		stop()
		return
	_steer(dt)
	_cam(dt)
	_hud_tick()
	match phase:
		"intro_walk":
			if Vector2(spieler_pos().x - _dig_p.x, spieler_pos().z - _dig_p.z).length() < 3.5:
				_dig()
		"region":
			_region_tick()
		"finale_walk":
			_finale_tick()


func _steer(dt: float) -> void:
	var a = spieler()
	if phase not in WALK or a.frozen:
		a.ctl_move = Vector2.ZERO
		return
	var k := Vector2.ZERO                   # (forward, right)
	if not main.typing():
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
			k.x += 1.0
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
			k.x -= 1.0
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			k.y += 1.0
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			k.y -= 1.0
	var run := Input.is_key_pressed(KEY_SHIFT)
	for j in Input.get_connected_joypads():
		var lx := Input.get_joy_axis(j, JOY_AXIS_LEFT_X)
		var ly := Input.get_joy_axis(j, JOY_AXIS_LEFT_Y)
		if Vector2(lx, ly).length() > 0.2:
			k += Vector2(-ly, lx)
		var rx := Input.get_joy_axis(j, JOY_AXIS_RIGHT_X)
		var ry := Input.get_joy_axis(j, JOY_AXIS_RIGHT_Y)
		if absf(rx) > 0.2:
			cam_yaw -= rx * dt * 2.2
			_drag_t = main.now()
		if absf(ry) > 0.2:
			cam_pitch = clampf(cam_pitch + ry * dt * 1.2, 0.08, 1.2)
		run = run or Input.get_joy_axis(j, JOY_AXIS_TRIGGER_RIGHT) > 0.5
		if Input.is_joy_button_pressed(j, JOY_BUTTON_Y) and phase in WALK:
			look_into_crystal()
	k = k.limit_length(1.0)
	var fwd := Vector3(-sin(cam_yaw), 0, -cos(cam_yaw))
	var rt := Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
	var mv := fwd * k.x + rt * k.y
	a.ctl_move = Vector2(mv.x, mv.z)
	a.ctl_run = run
	if mv.length() > 0.1 and main.now() - _drag_t > 1.5:      # walking: the view swings slowly behind the figure
		cam_yaw = lerp_angle(cam_yaw, a.heading, clampf(dt * 0.9, 0.0, 1.0))


func _follow_xform() -> Transform3D:
	var tp := spieler_pos() + Vector3(0, 1.35, 0)
	var back := Vector3(sin(cam_yaw), 0, cos(cam_yaw))
	var want := tp + back * cam_dist * cos(cam_pitch) + Vector3(0, cam_dist * sin(cam_pitch), 0)
	want.y = maxf(want.y, main.ground_y(want.x, want.z) + 0.8)
	return Transform3D(Basis.IDENTITY, want).looking_at(tp, Vector3.UP)


func _cam(dt: float) -> void:
	var cam: Camera3D = main.view_cam
	main.view_mode = 0
	var want := _follow_xform()
	cam.global_transform = cam.global_transform.interpolate_with(want, clampf(dt * 5.0, 0.0, 1.0))


func _cam_snap() -> void:
	var a = spieler()
	if a == null:
		return
	cam_yaw = a.heading
	main.view_cam.global_transform = _follow_xform()


func _hud_tick() -> void:
	var t: float = main.now()
	if _tipp.visible and t > _tipp_until:
		_tipp.visible = false
	if _me_box.visible and t > _me_until:
		_me_box.visible = false
	if not _hud.visible:
		return
	var g := _next_goal()
	if g.is_empty():
		_arrow.visible = false
		_hud_goal.text = ""
	else:
		var gp: Vector3 = g[0]
		var cam: Camera3D = main.view_cam
		var loc := cam.global_transform.basis.inverse() * (gp - cam.global_position)
		(_arrow as Arrow).ang = atan2(loc.x, -loc.z)
		_arrow.visible = true
		_arrow.queue_redraw()
		var d := Vector2(gp.x - spieler_pos().x, gp.z - spieler_pos().z).length()
		_hud_goal.text = "%s · %d m" % [str(g[1]), int(d)]
		if _beam != null and phase != "finale_cut":
			_beam.visible = d > 6.0
			_beam.position = gp + Vector3(0, 35, 0)
	var left := maxf(0.0, _zk_ready_at - t)
	_kbtn.visible = has_crystal and phase in WALK
	_kbtn.text = (T.t("K · Kristall") if left <= 0.0 else T.t("Kristall %d s", [int(ceil(left))]))
	_kbtn.disabled = left > 0.0


func _paint_tasks() -> void:
	if _hud_title == null or region == "":
		return
	var r: Dictionary = Welt.REG[region]
	_hud_title.text = T.t(str(r["name"]))
	var lines := []
	for id in _task_order:
		lines.append(("✓ " if bool(_tasks[id]["done"]) else "○ ") + str(_tasks[id]["text"]))
	var n := 0
	for e in _rests:
		n += 1 if bool(e["reached"]) else 0
	lines.append(T.t("Rastplätze: %d von %d", [n, _rests.size()]))
	_hud_tasks.text = "\n".join(lines)


# =======================================================================================================================
# input (before main: W A S D must not fly the view, Esc = our pause)
# =======================================================================================================================
func walking() -> bool:
	"""main._fly asks: the keys belong to the story"""
	return running and phase not in ["", "figur"]


func _unhandled_input(ev: InputEvent) -> void:
	if not running or phase in ["", "figur"]:
		return
	if ev is InputEventKey and ev.pressed and not ev.echo:
		match ev.keycode:
			KEY_ESCAPE:
				if phase == "film":
					_film_skip()
				elif phase in WALK:
					_pause()
				elif phase == "pause":
					_unpause()
				elif phase == "abspann":
					_end_card()
			KEY_K:
				look_into_crystal()
			KEY_SPACE, KEY_ENTER:
				if phase == "film":
					_film_skip()
	if ev is InputEventKey:
		get_viewport().set_input_as_handled()
	elif ev is InputEventMouseMotion:
		if (ev.button_mask & (MOUSE_BUTTON_MASK_LEFT | MOUSE_BUTTON_MASK_RIGHT)) != 0 and phase in WALK:
			cam_yaw -= ev.relative.x * 0.006
			cam_pitch = clampf(cam_pitch + ev.relative.y * 0.004, 0.08, 1.2)
			_drag_t = main.now()
		get_viewport().set_input_as_handled()
	elif ev is InputEventMouseButton:
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			cam_dist = clampf(cam_dist - 0.6, 2.5, 16.0)
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cam_dist = clampf(cam_dist + 0.6, 2.5, 16.0)
		get_viewport().set_input_as_handled()
	elif ev is InputEventJoypadButton and ev.pressed:
		if ev.button_index == JOY_BUTTON_START:
			if phase in WALK:
				_pause()
			elif phase == "pause":
				_unpause()
		get_viewport().set_input_as_handled()


func _pause() -> void:
	if phase not in WALK:
		return
	_resume_phase = phase
	phase = "pause"
	_freeze(true)
	_modules_pause(true)
	var v := _new_card(T.t("Pause"), Color(0.62, 0.85, 1.0), 520)
	_text(v, T.t("%d von 4 Jahreszeiten geschafft. Gespeichert wird an jedem Rastplatz.", [done_count()]), 15)
	var row := _row(v)
	_button(row, T.t("Weiter"), _unpause, true)
	if region != "":
		_button(row, T.t("Zur Auswahl"), func():
			_modules_pause(false)
			region_beendet.emit(region)
			region = ""
			S["region"] = ""
			_save()
			_clear_stage_things()
			_choose_card())
	_button(row, T.t("Speichern und beenden"), stop)


func _unpause() -> void:
	if phase != "pause":
		return
	_clear_card()
	phase = _resume_phase
	_freeze(false)
	_modules_pause(false)
	_safe_until = maxf(_safe_until, main.now() + 2.0)


# =======================================================================================================================
# ui
# =======================================================================================================================
func _ensure_ui() -> void:
	if _layer != null:
		return
	_layer = CanvasLayer.new()
	_layer.layer = 60
	add_child(_layer)
	_ui = Control.new()
	_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.theme = UI.theme()
	_layer.add_child(_ui)
	# the picture of the future: a bluish, slightly wavy view through the crystal (Lite: only a tint)
	_zk_fx = ColorRect.new()
	_zk_fx.set_anchors_preset(Control.PRESET_FULL_RECT)
	_zk_fx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_zk_fx.visible = false
	if Welt.lite():
		_zk_fx.color = Color(0.35, 0.55, 1.0, 0.22)
	else:
		var sh := Shader.new()
		sh.code = """shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 d = uv - 0.5;
	float r = length(d);
	uv += d * 0.012 * sin(TIME * 2.0 + r * 14.0);
	vec3 c = texture(screen_tex, uv).rgb;
	float g = dot(c, vec3(0.3, 0.59, 0.11));
	vec3 t = mix(c, vec3(g * 0.75, g * 0.95, g * 1.3), 0.6);
	float v = smoothstep(0.78, 0.28, r);
	t = t * mix(0.35, 1.0, v) + vec3(0.12, 0.22, 0.42) * (1.0 - v);
	COLOR = vec4(t, 1.0);
}"""
		var m := ShaderMaterial.new()
		m.shader = sh
		_zk_fx.material = m
	_ui.add_child(_zk_fx)
	_zk_lbl = Label.new()
	_anchor(_zk_lbl, 0.5, 0.0, 0.5, 0.0, -380, 40, 380, 120)
	_zk_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_zk_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_zk_lbl.add_theme_font_size_override("font_size", 20)
	_zk_lbl.add_theme_color_override("font_color", Color(0.85, 0.94, 1.0))
	_zk_lbl.add_theme_color_override("font_outline_color", Color(0.02, 0.05, 0.12))
	_zk_lbl.add_theme_constant_override("outline_size", 6)
	_zk_lbl.visible = false
	_ui.add_child(_zk_lbl)
	_build_hud()
	_fade = ColorRect.new()                                    # the short fright: darker for a moment
	_fade.color = Color(0.02, 0.03, 0.08, 0.0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_fade)
	_fade_lbl = Label.new()
	_anchor(_fade_lbl, 0.5, 0.5, 0.5, 0.5, -330, -90, 330, 90)
	_fade_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_fade_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_fade_lbl.add_theme_font_size_override("font_size", 20)
	_fade_lbl.add_theme_color_override("font_color", UI.TXT)
	_fade_lbl.modulate.a = 0.0
	_ui.add_child(_fade_lbl)
	_snd = AudioStreamPlayer.new()
	_snd.volume_db = -6.0
	add_child(_snd)


func _build_hud() -> void:
	_hud = Control.new()
	_hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.visible = false
	_ui.add_child(_hud)
	var tp := PanelContainer.new()
	tp.add_theme_stylebox_override("panel", UI.box(Color(0.04, 0.06, 0.1, 0.72), UI.LINE, 10, 10, 1))
	tp.position = Vector2(16, 14)
	tp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(tp)
	var tv := VBoxContainer.new()
	tv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tp.add_child(tv)
	_hud_title = Label.new()
	_hud_title.add_theme_font_size_override("font_size", 18)
	tv.add_child(_hud_title)
	_hud_tasks = Label.new()
	_hud_tasks.add_theme_font_size_override("font_size", 14)
	_hud_tasks.add_theme_color_override("font_color", Color(0.82, 0.86, 0.92))
	tv.add_child(_hud_tasks)
	_arrow = Arrow.new()
	_anchor(_arrow, 0.5, 0.0, 0.5, 0.0, -22, 12, 22, 56)
	_arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	(_arrow as Arrow).col = Color(1.0, 0.9, 0.55)
	_hud.add_child(_arrow)
	_hud_goal = _out_label(15)
	_anchor(_hud_goal, 0.5, 0.0, 0.5, 0.0, -250, 58, 250, 82)
	_hud_goal.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hud.add_child(_hud_goal)
	_tipp = _out_label(19)
	_anchor(_tipp, 0.5, 1.0, 0.5, 1.0, -380, -200, 380, -110)
	_tipp.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_tipp.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_tipp.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_tipp.visible = false
	_ui.add_child(_tipp)
	# MoveEye's speech bubble (bottom left): an eye and a short sentence
	_me_box = PanelContainer.new()
	_me_box.add_theme_stylebox_override("panel", UI.box(Color(0.04, 0.07, 0.12, 0.85), UI.ACC, 14, 10, 1))
	_anchor(_me_box, 0.0, 1.0, 0.0, 1.0, 16, -230, 420, -120)
	_me_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_me_box.visible = false
	_ui.add_child(_me_box)
	var mh := HBoxContainer.new()
	mh.add_theme_constant_override("separation", 10)
	_me_box.add_child(mh)
	var eye := Eye.new()
	eye.custom_minimum_size = Vector2(34, 24)
	eye.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	mh.add_child(eye)
	var mv := VBoxContainer.new()
	mv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mh.add_child(mv)
	var mn := Label.new()
	mn.text = "MoveEye"
	mn.add_theme_font_size_override("font_size", 12)
	mn.add_theme_color_override("font_color", UI.ACC)
	mv.add_child(mn)
	_me_lbl = Label.new()
	_me_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_me_lbl.custom_minimum_size = Vector2(330, 0)
	_me_lbl.add_theme_font_size_override("font_size", 15)
	mv.add_child(_me_lbl)
	_help = _out_label(12)
	_anchor(_help, 1.0, 1.0, 1.0, 1.0, -520, -30, -16, -10)
	_help.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_help.add_theme_color_override("font_color", Color(0.75, 0.8, 0.88))
	_help.text = T.t("W A S D gehen · Shift rennen · Maus ziehen umschauen · K Kristall · Esc Pause")
	_hud.add_child(_help)
	_kbtn = Button.new()
	_anchor(_kbtn, 1.0, 0.0, 1.0, 0.0, -170, 16, -70, 56)
	_kbtn.tooltip_text = T.t("In den Kristall schauen: ein Bild der Zukunft (eine Gefahr oder ein Weg)")
	_kbtn.pressed.connect(look_into_crystal)
	_kbtn.focus_mode = Control.FOCUS_NONE
	_hud.add_child(_kbtn)


func _out_label(size: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color(0.95, 0.96, 0.98))
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 5)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _anchor(c: Control, al: float, at: float, ar: float, ab: float, ol: float, ot: float, orr: float, ob: float) -> void:
	c.anchor_left = al
	c.anchor_top = at
	c.anchor_right = ar
	c.anchor_bottom = ab
	c.offset_left = ol
	c.offset_top = ot
	c.offset_right = orr
	c.offset_bottom = ob


func _close_cards() -> void:
	_clear_card()
	if not running:
		phase = ""


func _clear_card() -> void:
	if _card != null and is_instance_valid(_card):
		_card.queue_free()
	_card = null


func _new_card(title: String, accent := UI.ACC, width := 600) -> VBoxContainer:
	_clear_card()
	_card = PanelContainer.new()
	_card.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.95), accent, 16, 20, 2))
	_card.custom_minimum_size = Vector2(width, 0)
	_ui.add_child(_card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	_card.add_child(v)
	var h := Label.new()
	h.text = title
	h.add_theme_font_size_override("font_size", 24)
	h.add_theme_color_override("font_color", UI.TXT)
	v.add_child(h)
	_card.resized.connect(_center_card)
	_center_card.call_deferred()
	return v


func _center_card() -> void:
	if _card != null and is_instance_valid(_card):
		_card.position = ((_ui.size - _card.size) * 0.5).floor()


func _text(parent: Control, t: String, size := 15, col := UI.TXT) -> Label:
	var l := Label.new()
	l.text = t
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(maxf(300.0, (_card.custom_minimum_size.x if _card != null else 600.0) - 44.0), 0)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
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
	b.custom_minimum_size = Vector2(0, 40)
	b.add_theme_font_size_override("font_size", 15)
	if primary:
		UI.primary(b)
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func _play(kind: String) -> void:
	if _snd == null:
		return
	if not _streams.has(kind):
		match kind:
			"chime":
				_streams[kind] = Welt.snd_chime()
			"fanfare":
				_streams[kind] = Welt.snd_fanfare()
			"whoosh":
				_streams[kind] = Welt.snd_whoosh()
			"rest":
				_streams[kind] = Welt.snd_rest()
			_:
				return
	_snd.stream = _streams[kind]
	_snd.play()


# =======================================================================================================================
# /control {"action": "maggie", …}
# =======================================================================================================================
func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"open":
			open()
		"start":                                       # tests: figure without the card
			_ensure_ui()
			S = {"name": str(d.get("name", "Test")), "look": d.get("look", {"col": "red", "size": "", "build": "", "hat": "", "pack": true})}
			_save()
			if running:
				stop()
			_start()
			_start_intro()
		"region":
			var id := str(d.get("id", ""))
			if not Welt.REG.has(id):
				return {"ok": false, "error": "unknown region"}
			if not running:
				_ensure_ui()
				_start()
			has_crystal = true
			S["intro"] = true
			_start_region(id, int(d.get("rest", 0)))
		"los":                                         # tests: press the primary button of the card
			_press_primary()
		"aufgabe":
			aufgabe_anmelden(str(d.get("id", "")), str(d.get("text", d.get("id", ""))))
		"erledigt":
			aufgabe_erledigt(str(d.get("id", "")))
		"fertig":
			if region != "":
				region_fertig(region)
		"erwischt":
			erwischt(str(d.get("von", "wolf")))
		"zukunft":
			_zk_ready_at = 0.0
			look_into_crystal()
		"finale":
			if not running:
				_ensure_ui()
				_start()
			has_crystal = true
			_start_finale()
		"rast":
			var i := int(d.get("i", 0))
			if i >= 0 and i < _rests.size():
				_place_player(_rests[i]["pos"])
		"gehe":
			_place_player(Vector3(float(d.get("x", 0.0)), 0.0, float(d.get("z", 0.0))))
		"zum_ziel":                                     # tests: right in front of the next goal
			var g := _next_goal()
			if not g.is_empty():
				_place_player(g[0])
		"pause":
			_pause()
		"weiter":
			_unpause()
		"stop":
			stop()
		"reset":
			if running:
				stop()
			S = {}
			_save()
	return info()


func _press_primary() -> void:
	if _card == null:
		return
	var st: Array = [_card]
	while not st.is_empty():
		var n: Node = st.pop_back()
		if n is Button and not (n as Button).disabled and (n as Button).has_theme_stylebox_override("normal") and (n as Button).get_theme_stylebox("normal").bg_color == UI.ACC:
			(n as Button).pressed.emit()
			return
		for c in n.get_children():
			st.append(c)
