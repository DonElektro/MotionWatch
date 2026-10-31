extends Node
## «Maggie und der Bergkristall» für zwei Spieler (Daniel, 31.10.2026): ein Bildschirm, zwei Controller, einfache Bedienung –
## damit Daniel die Geschichte mit seiner Tochter (12) zusammen erleben kann. Vorbild: «Die Karte des Grossvaters» zu zweit
## (abenteuer_zweit.gd); der Teil «Bildschirm wechselnd» steht für beide in zweit_bild.gd.
##
## Wahl vor dem Start (gemeinsamer Start in geschichten.gd: Spielstand → Figur; auf der Seite «Figur» «1 oder 2 Spieler»):
##   wanderer   zwei Wanderer (Spieler 2 mit eigenem Namen und eigener Jacke); Maggie folgt beiden und hilft
##   maggie     Spieler 2 steuert Maggie selbst: linker Stick = laufen, rechter Stick = umschauen, R2 = rennen und
##              A = warnen (bellen) · B = riechen · X = graben / holen · Y = durchschlüpfen – die Plätze wie in padmap.gd
##              (Modus «runner»: A Lampe, B ducken = Nase runter, X Ding drücken = graben, Y kriechen = durchschlüpfen).
##              Maggie bleibt in Leinen-Reichweite (LEINE = 25 m von Spieler 1), sonst läuft sie sanft zurück.
## Spieler 1 = Tastatur (W A S D, wie allein; E = A-Knopf) und / oder jeder andere Controller (wie allein: linker Stick gehen,
##   rechter Stick umschauen, R2 rennen, Y Kristall, Start Pause; dazu A = Teamrätsel / retten, B = Schutzding, X = «Maggie,
##   hilf!»). Spieler 2 = der Controller, der beim Start A drückt («Spieler 2: Drücke A auf deinem Controller»). Ohne zweiten
##   Controller läuft Spieler 2 einfach mit (bzw. Maggie folgt wie allein), die Geschichte geht wie allein weiter.
## Der Kristall bleibt bei Spieler 1: die bösen Tiere jagen ihn (maggie_gefahr.gd zielt auf story.spieler_pos()).
##
## Bildschirm wechselnd: geteilt, bei Nähe (< 18 m, wieder geteilt ab 26 m) ein gemeinsames Bild. Lite: halbe Auflösung,
## Sichtweite 280 m, jede Ansicht jedes zweite Bild (zweit_bild.gd). Ansicht 1 = die Kamera der Geschichte (folgt Spieler 1).
##
## Teamrätsel – pro Region eines, nur zu zweit lösbar (nur im Zwei-Spieler-Modus und erst, wenn Spieler 2 dabei ist; sonst gilt
## die bisherige Station). Es ersetzt die zweite Weggabelung der Region (ERSETZT) am selben Ort, der Pfeil führt hin:
##   herbst     «Die zwei Zaubersteine»: beide stellen sich gleichzeitig auf einen Stein → der Steg senkt sich
##   winter     «Die Wolfsschlucht»: Spieler 2 hält an der Feuerschale die Fackel (A; Maggie: A bellen), Spieler 1 bringt den
##              Kristall an den leuchtenden Augen vorbei bis zum Steinmann
##   fruehling  «Das Weidegatter mit dem Seil»: Spieler 2 schlüpft durch das Loch im Zaun (A; Maggie: Y) und hält drüben das
##              Seil am Haken, Spieler 1 zieht an der Winde (A halten) → das Gatter geht auf
##   sommer     «Der Viperweg»: Spieler 2 stampft am Stampfstein (A; Maggie: X scharren), Spieler 1 geht über den Viperweg
## Erwischt (nur in einer Region): Spieler 1 ist umzingelt (die Tiere kreisen um ihn, maggie_gefahr.ablenken); Spieler 2 kann
##   retten: hingehen (3 m) und A drücken. Sonst gehen nach 20 s beide zum letzten Rastplatz (wie allein). Der Kristall bleibt.
## Speichern: als Modul der Geschichte (zustand / laden / neu) im gewählten Spielstand (spielstand.gd path_maggie) – der
##   Fortschritt ist gemeinsam (dieselbe Datei). Die Wahl des Starts kommt über das Meta «maggie_zwei_wahl» von main.
## Spieltest: Spieltest.ereignis("maggie", …) mit {"spieler": 2, "rolle": …} (abschnitt, fortschritt, erwischt, neustart).
## Lite: _lite() = Quality.lite() (oder force_lite für Tests): keine Lichter an den Teamrätseln, die Ansichten wie oben.
## Einhängepunkte (klein gehalten): maggie_story.gd (MODULES, erwischt → faengt, _steer → eigen, control "zwei"),
##   maggie_hund.gd (var zwei: _nah → nah_bei, _folgen → fuehrt_hund, ersetzte Gabelung), padmap.gd (pad_devs),
##   geschichten.gd (Seite «Figur»: seite_figur, gs_taste, wahl_laden, wahl_merken).
## Test / Fernsteuerung: /control {"action": "maggie", "do": "zwei", "k": "wahl" (n, rolle, name2, col2) | "info" | "an" (n, rolle)
##   | "join" (dev) | "pad" (ls [x, y], rs [x, y], run, secs, press [a b x y]) | "p1" (press [a b x], hold secs) | "hin" (p 1|2,
##   ort a|b|h|d|z|l|k|w|s0|p) | "p2" (x, z Tal) | "fest" (von) | "loesen" | "lite" (value) | "fps"}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Welt = preload("res://scripts/maggie_welt.gd")
const ZB = preload("res://scripts/zweit_bild.gd")
const ActorS = preload("res://scripts/actor.gd")
const Figur = preload("res://scripts/figur.gd")
const Quality = preload("res://scripts/quality.gd")
const Spieltest = preload("res://scripts/spieltest.gd")

const COLS := [Color(0.23, 0.55, 1.0), Color(1.0, 0.62, 0.26)]     # wie abenteuer_zweit.gd: 1 blau, 2 orange
const LEINE := 25.0                  # m: so weit darf Maggie (Spieler 2) von Spieler 1 weg
const LEINE_ZURUECK := 17.0          # m: bis hierher läuft sie zurück
const RETTEN_S := 20.0               # s: so lange kann Spieler 2 retten
const RETTEN_R := 3.0                # m: so nah muss Spieler 2 sein
const TEST_DEV := -2                 # der nachgestellte Controller (Steuer-API «pad»)
const WALK := ["intro_walk", "region", "finale_walk"]
const VIEW_PH := ["intro_walk", "region", "finale_walk", "schreck", "pause"]
const ERSETZT := {"herbst": "h_gabel2", "winter": "w_gabel2", "fruehling": "f_gabel", "sommer": "s_gabel"}
const ART := {"herbst": "steine", "winter": "fackel", "fruehling": "seil", "sommer": "stampfen"}
const TITEL := {"steine": "Die zwei Zaubersteine", "fackel": "Die Wolfsschlucht", "seil": "Das Weidegatter mit dem Seil",
		"stampfen": "Der Viperweg"}
const AUFGABE := {"steine": "Teamrätsel: Die zwei Zaubersteine", "fackel": "Teamrätsel: Die Wolfsschlucht",
		"seil": "Teamrätsel: Das Weidegatter mit dem Seil", "stampfen": "Teamrätsel: Der Viperweg"}
const GESCHAFFT := {"steine": "Geschafft! Zusammen auf den Zaubersteinen – der Steg über den Bach ist unten.",
		"fackel": "Geschafft! Das Feuer hat die Wölfe in ihrer Höhle gehalten. Der Kristall ist sicher vorbei.",
		"seil": "Geschafft! Zusammen habt ihr am Seil gezogen – das Gatter ist offen.",
		"stampfen": "Geschafft! Die Vipern sind vor dem Stampfen weggekrochen. Der Weg ist frei."}

var main
var story
# the choice (saved)
var aktiv := false
var rolle := "wanderer"              # wanderer | maggie
var name2 := ""
var look2 := {"col": "navy", "size": "", "build": "", "hat": "", "pack": true}
var gerettet := 0
# players
var p2dev := -1                      # the controller of player 2 (-1 none yet, TEST_DEV = tests)
var fig2: Node3D = null              # player 2 as a walker (actor.gd, controlled)
var yaw2 := 0.0
var pitch2 := 0.4
var _drag2 := -10.0
var _p1_last := Vector3.INF
var _p2_head := 0.0                  # where Maggie looks (world yaw) - for the camera of player 2
var _hund_last := Vector3.INF
var _leine := false
var _later := false                  # «Später» on the join card
var _frozen := false
# views
var on := false
var merged := false
var force_lite := false
var _layer: CanvasLayer
var _root: Control
var _v: Array = [{}, {}]
var _line: ColorRect
var _frame := 0
var _fps: Array = []
# hud
var _hl: CanvasLayer
var _big: PanelContainer
var _big_t: Label
var _big_1: Label
var _big_2: Label
var _join: PanelContainer
var _join_t: Label
var _say_l: Label
var _say_until := 0.0
# the team puzzle of this region
var team := {}
var _tnode: Node3D = null
# caught
var fest := {}
# tests
var _vpad := {}
var _p1_test := {"press": [], "hold_until": 0.0}
var _e_hit := false


# =======================================================================================================================
# the common start (geschichten.gd): «1 oder 2 Spieler», role and figure of player 2
# =======================================================================================================================
static func _wahl_def() -> Dictionary:
	return {"n": 1, "rolle": "wanderer", "name2": "", "col2": "navy"}


static func wahl_laden(m, fl: Dictionary) -> void:
	"""what the active Spielstand had chosen last"""
	var w := _wahl_def()
	var st = m.get("maggie")
	if st != null:
		var md = (st.S.get("module", {}) as Dictionary).get("maggie_zwei", {}) if st.S.get("module", {}) is Dictionary else {}
		if md is Dictionary and not md.is_empty():
			w["n"] = 2 if bool(md.get("an", false)) else 1
			w["rolle"] = str(md.get("rolle", "wanderer"))
			w["name2"] = str(md.get("name2", ""))
			w["col2"] = str((md.get("look2", {}) as Dictionary).get("col", "navy")) if md.get("look2", {}) is Dictionary else "navy"
	fl["zwei"] = w


static func wahl_merken(m, fl: Dictionary) -> void:
	m.set_meta("maggie_zwei_wahl", (fl.get("zwei", _wahl_def()) as Dictionary).duplicate())


static func gs_taste(fl: Dictionary, d: Dictionary) -> bool:
	"""a button of the common start: zwei (1 | 2) · rolle (wanderer | maggie) · name2 · col2"""
	var k := str(d.get("k", ""))
	if str(fl.get("id", "")) != "maggie" or not k in ["zwei", "rolle", "name2", "col2"]:
		return false
	if not fl.has("zwei"):
		fl["zwei"] = _wahl_def()
	var w: Dictionary = fl["zwei"]
	match k:
		"zwei":
			w["n"] = 2 if int(d.get("v", 1)) == 2 else 1
		"rolle":
			w["rolle"] = "maggie" if str(d.get("v", "")) == "maggie" else "wanderer"
		"name2":
			w["name2"] = str(d.get("v", "")).strip_edges().left(16)
		"col2":
			if Figur.LOOK_COLS.has(str(d.get("v", ""))):
				w["col2"] = str(d["v"])
	return true


static func seite_figur(g, fl: Dictionary) -> void:
	"""on the page «Figur» of the common start (g = geschichten.gd)"""
	if not fl.has("zwei"):
		fl["zwei"] = _wahl_def()
	var w: Dictionary = fl["zwei"]
	g._say(T.t("Wie viele spielen?"), 15)
	var r0: HBoxContainer = g._row(T.t("Spieler"))
	for n in [1, 2]:
		var b := Button.new()
		b.text = T.t("1 Spieler") if n == 1 else T.t("2 Spieler")
		b.custom_minimum_size = Vector2(150, 40)
		b.add_theme_font_size_override("font_size", g.fs(15))
		if int(w["n"]) == n:
			UI.primary(b)
		var nn: int = n
		b.pressed.connect(func(): g.gs({"k": "zwei", "v": nn}))
		r0.add_child(b)
	if int(w["n"]) != 2:
		return
	var gr := HBoxContainer.new()
	gr.add_theme_constant_override("separation", 8)
	g._body.add_child(gr)
	for e in [["wanderer", T.t("Zwei Wanderer"), T.t("Ihr wandert beide. Maggie folgt euch und hilft.")],
			["maggie", T.t("Spieler 2 ist Maggie"), T.t("Spieler 2 steuert Maggie: laufen, riechen, graben, durchschlüpfen, warnen.")]]:
		var b2 := Button.new()
		b2.text = str(e[1]) + "\n" + str(e[2])
		b2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b2.custom_minimum_size = Vector2(296, 78)
		b2.add_theme_font_size_override("font_size", g.fs(13))
		if str(w["rolle"]) == str(e[0]):
			UI.primary(b2)
		var rr: String = e[0]
		b2.pressed.connect(func(): g.gs({"k": "rolle", "v": rr}))
		gr.add_child(b2)
	if str(w["rolle"]) == "wanderer":
		var r1: HBoxContainer = g._row(T.t("Name 2"))
		var le := LineEdit.new()
		le.text = str(w["name2"])
		le.placeholder_text = T.t("Name von Spieler 2")
		le.max_length = 16
		le.custom_minimum_size = Vector2(260, 36)
		le.text_changed.connect(func(t): w["name2"] = str(t).strip_edges().left(16))
		r1.add_child(le)
		var r2: HBoxContainer = g._row(T.t("Jacke 2"))
		for c in ["navy", "orange", "red", "olive", "brown", "grey", "white", "black"]:
			var cb := Button.new()
			cb.custom_minimum_size = Vector2(38, 34)
			var sel: bool = str(w["col2"]) == c
			var st := UI.box(Figur.LOOK_COLS[c], Color.WHITE if sel else UI.LINE, 8, 4, 3 if sel else 1)
			for k in ["normal", "hover", "pressed"]:
				cb.add_theme_stylebox_override(k, st)
			var cc: String = c
			cb.pressed.connect(func(): g.gs({"k": "col2", "v": cc}))
			r2.add_child(cb)
	g._say(T.t("Ein Bildschirm, zwei Controller. Beim Start drückt Spieler 2 A auf seinem Controller. Spieler 1 spielt mit der Tastatur (wie allein) oder mit dem anderen Controller."), 13, UI.MUT)


# =======================================================================================================================
# the module (maggie_story.gd: MODULES – main and story are set before _ready)
# =======================================================================================================================
func _ready() -> void:
	process_priority = 60                 # after the story (50): its camera of player 1 is ready
	_build_hud()
	if story != null:
		if story.has_signal("szene_bereit"):
			story.szene_bereit.connect(_on_szene)
		if story.has_signal("region_gestartet"):
			story.region_gestartet.connect(_on_region)
		if story.has_signal("region_beendet"):
			story.region_beendet.connect(_on_region_ende)


func _exit_tree() -> void:
	_views(false)
	_team_weg()


func _lite() -> bool:
	return force_lite or Quality.lite()


func _now() -> float:
	return main.now()


func _hund():
	return story.get_node_or_null("maggie_hund") if story != null else null


func _gefahr():
	return story.get_node_or_null("maggie_gefahr") if story != null else null


func _n1() -> String:
	return str(story.S.get("name", T.t("Spieler 1"))) if story != null else T.t("Spieler 1")


func _n2() -> String:
	if rolle == "maggie":
		return T.t("Maggie")
	return name2 if name2 != "" else T.t("Spieler 2")


func _apply(w: Dictionary) -> void:
	aktiv = int(w.get("n", 1)) == 2
	rolle = "maggie" if str(w.get("rolle", "")) == "maggie" else "wanderer"
	name2 = str(w.get("name2", ""))
	look2 = {"col": str(w.get("col2", "navy")), "size": "", "build": "", "hat": "", "pack": true}


# ---- saving (the story calls these at every rest place) -----------------------------------------------------------------
func zustand() -> Dictionary:
	return {"an": aktiv, "rolle": rolle, "name2": name2, "look2": look2.duplicate(), "gerettet": gerettet}


func laden(d: Dictionary) -> void:
	if main != null and main.has_meta("maggie_zwei_wahl"):
		neu()
		return
	aktiv = bool(d.get("an", false))
	rolle = "maggie" if str(d.get("rolle", "")) == "maggie" else "wanderer"
	name2 = str(d.get("name2", ""))
	if d.get("look2", {}) is Dictionary and not (d["look2"] as Dictionary).is_empty():
		look2 = (d["look2"] as Dictionary).duplicate()
	gerettet = int(d.get("gerettet", 0))


func neu() -> void:
	"""a new story: the choice of the common start (or 1 player)"""
	var w: Dictionary = main.get_meta("maggie_zwei_wahl") if main != null and main.has_meta("maggie_zwei_wahl") else _wahl_def()
	if main != null and main.has_meta("maggie_zwei_wahl"):
		main.remove_meta("maggie_zwei_wahl")
	_apply(w)
	gerettet = 0


func pause(v: bool) -> void:
	_frozen = v


func spieler_zahl() -> int:
	return 2 if aktiv else 1


func _ev(art: String, d := {}) -> void:
	var dd: Dictionary = d.duplicate()
	dd["spieler"] = spieler_zahl()
	dd["rolle"] = rolle
	Spieltest.ereignis("maggie", art, dd)                 # Spieltest: mit Spielerzahl


# ---- hooks for the others ------------------------------------------------------------------------------------------------
func eigen(j: int) -> bool:
	"""maggie_story._steer: this controller is player 2's (it does not walk player 1)"""
	return aktiv and j == p2dev and j >= 0


func pad_devs() -> Array:
	"""padmap.gd: while we walk, the controllers are ours (no MoveEye light on A …)"""
	if not aktiv or story == null or not story.running or not (str(story.phase) in VIEW_PH) or main.padmap == null:
		return []
	return main.padmap.devices()


func fuehrt_hund() -> bool:
	"""maggie_hund.gd: Maggie follows not by herself (player 2 steers her, or she follows both walkers)"""
	if not aktiv or story == null or not story.running:
		return false
	if rolle == "maggie":
		return p2dev != -1
	return fig2 != null and is_instance_valid(fig2)


func _team_moeglich() -> bool:
	return aktiv and p2dev != -1


func ersetzt(id: String) -> bool:
	"""maggie_hund.gd: this station is a team puzzle now (only with two players)"""
	return _team_moeglich() and story != null and ERSETZT.get(str(story.region), "") == id


func nah_bei(p_tal: Vector3, r: float) -> bool:
	"""maggie_hund._nah: player 2 (or Maggie, when player 2 steers her) is near this station (valley point)"""
	if not aktiv:
		return false
	var q = _p2_tal()
	return q is Vector2 and (q as Vector2).distance_to(Vector2(p_tal.x, p_tal.z)) < r


# ---- positions (valley = bergtal.gd x / z) ---------------------------------------------------------------------------
func _bt():
	return main.scenes.data.get("bergtal", null) if main != null and main.scenes != null else null


func _tal(w: Vector3) -> Vector2:
	var b = _bt()
	if b == null:
		return Vector2(w.x, w.z)
	var q: Vector3 = b.V(w)
	return Vector2(q.x, q.z)


func _welt(q: Vector2) -> Vector3:
	return story.tal_punkt(q.x, q.y)


func _p1_tal() -> Vector2:
	return _tal(story.spieler_pos())


func _p2_welt():
	if rolle == "maggie":
		var h = _hund()
		if h != null and h.hund != null and is_instance_valid(h.hund):
			return (h.hund as Node3D).global_position
		return null
	if fig2 != null and is_instance_valid(fig2):
		return fig2.global_position
	return null


func _p2_tal():
	var w = _p2_welt()
	return _tal(w) if w is Vector3 else null


# =======================================================================================================================
# player 2 as a walker
# =======================================================================================================================
func _fig2_ensure(at: Vector3) -> void:
	if rolle != "wanderer" or not aktiv:
		_fig2_weg()
		return
	if fig2 == null or not is_instance_valid(fig2):
		var a = ActorS.new()
		a.controlled = true
		a.look = look2.duplicate()
		a.look["pack"] = true
		a.player_color = Figur.LOOK_COLS.get(str(look2.get("col", "navy")), Figur.LOOK_COLS["navy"])
		add_child(a)
		a.setup(main, "person", at, at + Vector3(0, 0, -1), 1.5)
		fig2 = a
	_fig2_place(at)


func _fig2_place(at: Vector3) -> void:
	if fig2 == null or not is_instance_valid(fig2):
		return
	at.y = main.ground_y(at.x, at.z)
	fig2.position = at
	fig2.cur_speed = 0.0
	fig2.ctl_move = Vector2.ZERO
	yaw2 = float(fig2.heading)


func _fig2_weg() -> void:
	if fig2 != null and is_instance_valid(fig2):
		fig2.queue_free()
	fig2 = null


func _neben_p1() -> Vector3:
	var a = story.spieler()
	var p: Vector3 = story.spieler_pos()
	if a == null:
		return p + Vector3(1.6, 0, 1.6)
	var side: Vector3 = (a as Node3D).global_transform.basis.x
	return p + side * 1.8 + (a as Node3D).global_transform.basis.z * 1.2


func _on_szene(_art: String) -> void:
	"""the valley is (re)built and player 1 stands there: player 2 beside"""
	if not aktiv:
		return
	_fig2_ensure(_neben_p1())
	_p1_last = story.spieler_pos()


func _on_region(_id: String) -> void:
	if aktiv:
		_ev("abschnitt", {"name": "Zwei Spieler"})
	_team_weg()


func _on_region_ende(_id: String) -> void:
	_team_weg()
	fest = {}


# =======================================================================================================================
# input
# =======================================================================================================================
func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo and ev.keycode == KEY_E and aktiv and story != null and story.running:
		_e_hit = true                                     # (the story marks all keys handled afterwards)


func _p2_in() -> Dictionary:
	"""{ls, rs, run, keys} of player 2's controller (or the one of the tests)"""
	var o := {"ls": Vector2.ZERO, "rs": Vector2.ZERO, "run": false, "keys": [], "a_held": false}
	if p2dev == TEST_DEV:
		if not _vpad.is_empty() and _now() < float(_vpad.get("until", 0.0)):
			o["ls"] = _vpad.get("ls", Vector2.ZERO)
			o["rs"] = _vpad.get("rs", Vector2.ZERO)
			o["run"] = bool(_vpad.get("run", false))
			o["a_held"] = "a" in (_vpad.get("hold", []) as Array)
		o["keys"] = (_vpad.get("press", []) as Array).duplicate()
		_vpad["press"] = []
		return o
	var pm = main.padmap
	if p2dev < 0 or pm == null:
		return o
	o["ls"] = pm.stick_clean(0, p2dev)
	o["rs"] = pm.stick_clean(1, p2dev)
	o["run"] = pm.raw_axis(JOY_AXIS_TRIGGER_RIGHT, p2dev) > 0.5
	o["keys"] = pm.keys([p2dev])
	o["a_held"] = pm.raw_btn("a", p2dev)
	return o


func _p1_devs() -> Array:
	var pm = main.padmap
	if pm == null:
		return []
	return pm.devices().filter(func(d): return d != p2dev)


func _p1_keys() -> Array:
	var o: Array = []
	var pm = main.padmap
	if pm != null and not _p1_devs().is_empty():
		o = pm.keys(_p1_devs()).duplicate()
	if _e_hit:
		o.append("a")
	_e_hit = false
	for k in _p1_test["press"]:
		o.append(k)
	_p1_test["press"] = []
	return o


func _p1_a_held() -> bool:
	if not main.typing() and Input.is_key_pressed(KEY_E):
		return true
	if _now() < float(_p1_test["hold_until"]):
		return true
	var pm = main.padmap
	if pm != null:
		for d in _p1_devs():
			if pm.raw_btn("a", d):
				return true
	return false


func _join_tick() -> void:
	"""«Spieler 2: Drücke A auf deinem Controller»"""
	var pm = main.padmap
	if p2dev >= 0 and pm != null and not (p2dev in pm.devices()):
		p2dev = -1                                        # unplugged: join again
		_later = false
	if p2dev != -1 or pm == null:
		return
	for d in pm.devices():
		if "a" in pm.keys([d]):
			_set_p2(d)
			return


func _set_p2(d: int) -> void:
	p2dev = d
	_later = false
	if main.padmap != null and d >= 0:
		main.padmap.rumble("catch", [d])
	_say(T.t("Spieler 2 ist dabei! %s", [_n2()]))
	_ev("abschnitt", {"name": "Spieler 2 dabei"})
	if rolle == "maggie":
		story.tipp(T.t("Spieler 2 ist Maggie: A = warnen, B = riechen, X = graben, Y = durchschlüpfen."))
	else:
		story.tipp(T.t("Spieler 2: linker Stick = gehen, rechter Stick = umschauen, A = Teamrätsel und retten, X = Maggie hilft."))


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _process(dt: float) -> void:
	if main == null or story == null:
		return
	_frame += 1
	dt = minf(dt, 0.25)
	var walk: bool = aktiv and story.running and str(story.phase) in VIEW_PH and main.scene == "bergtal" and story.spieler() != null
	if not walk:
		if on:
			_views(false)
		_join.visible = false
		_big.visible = false
		if fig2 != null and is_instance_valid(fig2):
			fig2.frozen = true
			fig2.ctl_move = Vector2.ZERO
		_say_l.visible = _now() < _say_until
		return
	if rolle == "wanderer" and (fig2 == null or not is_instance_valid(fig2)):
		_fig2_ensure(_neben_p1())
	elif rolle == "maggie":
		_fig2_weg()
	_join_tick()
	var walking: bool = str(story.phase) in WALK and not _frozen
	var inp := _p2_in()
	var k1 := _p1_keys()
	_follow_jumps()
	if rolle == "wanderer":
		_steer_fig2(inp, dt, walking)
	_hund_tick(inp, dt, walking)
	_p1_buttons(k1, walking)
	_p2_buttons(inp["keys"], walking)
	_sperren2()
	if str(story.region) != "":
		_team_tick(dt, inp, k1, walking)
	else:
		_big.visible = false
	_fest_tick(inp["keys"])
	_views(true)
	_view_tick(dt)
	_hud_tick()


func _follow_jumps() -> void:
	"""player 1 was carried away (rest place, Steinbock, a new stage): player 2 comes along"""
	var p1: Vector3 = story.spieler_pos()
	if _p1_last != Vector3.INF and p1.distance_to(_p1_last) > 8.0:
		if rolle == "wanderer":
			_fig2_place(_neben_p1())
		else:
			var h = _hund()
			if h != null and h.hund != null and is_instance_valid(h.hund) and fuehrt_hund():
				var q := _tal(p1)
				h.place(h.hund, Vector3(q.x + 1.2, 0, q.y + 1.2))
	_p1_last = p1


func _steer_fig2(inp: Dictionary, dt: float, walking: bool) -> void:
	var a = fig2
	if a == null or not is_instance_valid(a):
		return
	var stuck: bool = not walking
	a.frozen = stuck
	if stuck:
		a.ctl_move = Vector2.ZERO
		return
	var rs: Vector2 = inp["rs"]
	if absf(rs.x) > 0.05:
		yaw2 -= rs.x * dt * 2.2
		_drag2 = _now()
	if absf(rs.y) > 0.05:
		pitch2 = clampf(pitch2 + rs.y * dt * 1.2, 0.08, 1.2)
	if p2dev == -1:                                       # nobody holds controller 2: walk along with player 1
		var to: Vector3 = _neben_p1() - a.global_position
		to.y = 0.0
		var d := to.length()
		if d > 40.0:
			_fig2_place(_neben_p1())
			return
		a.ctl_move = Vector2(to.x, to.z).normalized() if d > 2.5 else Vector2.ZERO
		a.ctl_run = d > 9.0
		if d > 2.5:
			yaw2 = lerp_angle(yaw2, float(a.heading), clampf(dt * 0.9, 0.0, 1.0))
		return
	var ls: Vector2 = inp["ls"]
	var k := Vector2(-ls.y, ls.x)
	k = k.limit_length(1.0)
	var fwd := Vector3(-sin(yaw2), 0, -cos(yaw2))
	var rt := Vector3(cos(yaw2), 0, -sin(yaw2))
	var mv := fwd * k.x + rt * k.y
	a.ctl_move = Vector2(mv.x, mv.z)
	a.ctl_run = bool(inp["run"])
	if mv.length() > 0.1 and _now() - _drag2 > 1.5:
		yaw2 = lerp_angle(yaw2, float(a.heading), clampf(dt * 0.9, 0.0, 1.0))


func _hund_tick(inp: Dictionary, dt: float, walking: bool) -> void:
	"""Maggie: player 2 steers her (on a leash of 25 m) – or she follows both walkers"""
	var h = _hund()
	if h == null or h.hund == null or not is_instance_valid(h.hund) or not fuehrt_hund():
		return
	var hp: Vector3 = h.ppos(h.hund)
	var wnow: Vector3 = (h.hund as Node3D).global_position
	if _hund_last != Vector3.INF and wnow.distance_to(_hund_last) > 0.02:
		_p2_head = atan2(-(wnow.x - _hund_last.x), -(wnow.z - _hund_last.z))
	_hund_last = wnow
	if str(h.zustand_hund) != "folgen":
		return                                            # Maggie does something (digging, slipping through …)
	var p1 := _p1_tal()
	var p1v := Vector3(p1.x, 0, p1.y)
	if not walking:
		h.stop(h.hund, dt)
		return
	if rolle == "wanderer":
		var q2 = _p2_tal()
		var tgt := p1
		if q2 is Vector2 and (q2 as Vector2).distance_to(p1) < 20.0:
			tgt = (p1 + (q2 as Vector2)) / 2.0                 # Maggie stays between the two
		var tv := Vector3(tgt.x, 0, tgt.y)
		var d := Vector2(hp.x, hp.z).distance_to(tgt)
		if d > 45.0:
			h.place(h.hund, tv + Vector3(1.2, 0, 1.2))
		elif d > 2.2:
			h.idle(h.hund, "")
			h.walk(h.hund, tv, clampf(d * 1.3, 1.2, 5.5), dt)
		else:
			h.stop(h.hund, dt)
		return
	# Maggie steered by player 2
	var dist := Vector2(hp.x, hp.z).distance_to(p1)
	if dist > LEINE:
		if not _leine:
			_leine = true
			_say(T.t("Maggie bleibt in der Nähe (25 m) – sie läuft zurück."))
	if _leine:
		if dist < LEINE_ZURUECK:
			_leine = false
		else:
			h.idle(h.hund, "")
			h.walk(h.hund, p1v, 4.5, dt)
			return
	var rs: Vector2 = inp["rs"]
	if absf(rs.x) > 0.05:
		yaw2 -= rs.x * dt * 2.2
		_drag2 = _now()
	if absf(rs.y) > 0.05:
		pitch2 = clampf(pitch2 + rs.y * dt * 1.2, 0.08, 1.2)
	var ls: Vector2 = inp["ls"]
	var k := Vector2(-ls.y, ls.x).limit_length(1.0)
	if k.length() < 0.1:
		h.stop(h.hund, dt)
		return
	var fwd := Vector3(-sin(yaw2), 0, -cos(yaw2))
	var rt := Vector3(cos(yaw2), 0, -sin(yaw2))
	var mv := (fwd * k.x + rt * k.y)
	var tq := _tal(wnow + mv.normalized() * 1.5)
	h.idle(h.hund, "")
	h.walk(h.hund, Vector3(tq.x, 0, tq.y), (5.5 if bool(inp["run"]) else 3.0) * k.length(), dt)
	if _now() - _drag2 > 1.5:
		yaw2 = lerp_angle(yaw2, _p2_head, clampf(dt * 1.2, 0.0, 1.0))


func _maggie_hilft(near_tal) -> void:
	"""X: «Maggie, hilf!» – the ability the station wants (otherwise: smell)"""
	var h = _hund()
	if h == null or not h.has_method("befehl"):
		return
	var st: Dictionary = h.aktuell()
	var f := "riechen"
	if not st.is_empty() and str(st.get("f", "")) in ["riechen", "graben", "schluepfen"] and near_tal is Vector2 \
			and (near_tal as Vector2).distance_to(Vector2((st["p"] as Vector3).x, (st["p"] as Vector3).z)) < 9.0:
		f = str(st["f"])
	h.befehl(f)


func _p1_buttons(keys: Array, walking: bool) -> void:
	if not walking or keys.is_empty():
		return
	if "b" in keys:
		var g = _gefahr()
		if g != null and g.has_method("benutze"):
			g.benutze()                                   # das Schutzding (wie die Taste B)
	if "x" in keys and rolle == "wanderer":
		_maggie_hilft(_p1_tal())


func _p2_buttons(keys: Array, walking: bool) -> void:
	if not walking or keys.is_empty() or p2dev == -1:
		return
	var h = _hund()
	if rolle == "wanderer":
		if "x" in keys:
			_maggie_hilft(_p2_tal())
		return
	if h == null or h.hund == null or not is_instance_valid(h.hund):
		return
	if not fest.is_empty() or _team_braucht_knopf(keys):
		return                                            # A/X/Y belong to the rescue / the team puzzle now
	if "b" in keys:
		h.befehl("riechen")
	elif "x" in keys:
		h.befehl("graben")
	elif "y" in keys:
		h.befehl("schluepfen")
	elif "a" in keys:
		_warnen(h)


func _warnen(h) -> void:
	"""A (Maggie): warnen – bellen; an einer Weggabelung knurrt sie den gefährlichen Weg an"""
	var hp: Vector3 = h.ppos(h.hund)
	var st: Dictionary = h.aktuell()
	if not st.is_empty() and str(st.get("ding", "")) == "gabel" and not ersetzt(str(st["id"])) and st.has("boese_p") \
			and Vector2(hp.x, hp.z).distance_to(Vector2((st["p"] as Vector3).x, (st["p"] as Vector3).z)) < 14.0 and str(h.zustand_hund) == "folgen":
		var bp: Vector3 = st["boese_p"]
		h._aktion([{"t": "walk", "p": (st["p"] as Vector3).lerp(bp, 0.3), "spd": 2.0}, {"t": "face", "p": bp},
			{"t": "call", "fn": func(): h.knurren(h.ppos(h.hund))}, {"t": "wait", "s": 1.0}, {"t": "bark", "n": 3}])
		story.tipp(T.t("Maggie knurrt diesen Weg an. Dort lauert etwas – nehmt den anderen!"))
		return
	h.bellen(hp, 3)
	var nah: Array = h.boese_nah(hp, 30.0) if h.has_method("boese_nah") else []
	if not nah.is_empty():
		story.tipp(T.t("Maggie bellt: Achtung, da ist ein böses Tier!"))
	else:
		_say(T.t("Wuff! Maggie passt auf."))


func _sperren2() -> void:
	"""like maggie_story._sperren for player 2 (closed doors, gaps …): stay outside the circles"""
	if fig2 == null or not is_instance_valid(fig2):
		return
	for m in story._modules:
		if not is_instance_valid(m) or not m.has_method("sperren") or m == self:
			continue
		for e in m.sperren():
			var c: Vector3 = e[0]
			var r := float(e[1])
			var q: Vector3 = fig2.global_position - c
			q.y = 0.0
			if q.length() < r and q.length() > 0.001:
				var np: Vector3 = c + q.normalized() * r
				fig2.global_position = Vector3(np.x, main.ground_y(np.x, np.z), np.z)


# =======================================================================================================================
# caught: the other one can rescue
# =======================================================================================================================
func faengt(von: String) -> bool:
	"""maggie_story.erwischt: true = we take it (player 2 may rescue within 20 s)"""
	if not _team_moeglich() or not story.running or str(story.phase) != "region" or _p2_welt() == null:
		return false
	if not fest.is_empty():
		return true
	fest = {"von": von, "t0": _now(), "bis": _now() + RETTEN_S}
	story._freeze(true)
	story._safe_until = _now() + RETTEN_S + 5.0
	var g = _gefahr()
	if g != null and g.has_method("ablenken"):
		g.ablenken(story.spieler_pos(), RETTEN_S)          # the animals circle around player 1
	if story.has_method("_play"):
		story._play("whoosh")
	if main.padmap != null and p2dev >= 0:
		main.padmap.rumble("alarm", [p2dev])
	_ev("erwischt", {"von": von})
	story.tipp(T.t("%s ist umzingelt! %s: lauf hin und drück A!", [_n1(), _n2()]))
	return true


func _fest_tick(keys2: Array) -> void:
	if fest.is_empty():
		return
	if str(story.phase) != "region":
		fest = {}
		return
	var left := float(fest["bis"]) - _now()
	var q2 = _p2_tal()
	var near: bool = q2 is Vector2 and (q2 as Vector2).distance_to(_p1_tal()) < RETTEN_R
	if near and "a" in keys2:
		retten()
		return
	if left <= 0.0:
		_aufgeben()


func retten() -> void:
	if fest.is_empty():
		return
	fest = {}
	gerettet += 1
	var g = _gefahr()
	if g != null and g.has_method("vertreiben"):
		g.vertreiben()
	story._freeze(false)
	story._safe_until = _now() + 6.0
	if rolle == "maggie":
		var h = _hund()
		if h != null and h.hund != null and is_instance_valid(h.hund):
			h.bellen(h.ppos(h.hund), 4)
		story.tipp(T.t("Maggie bellt laut – die Tiere laufen weg! %s ist gerettet.", [_n1()]))
	else:
		story.tipp(T.t("Gerettet! Zusammen seid ihr stärker – die Tiere laufen weg."))
	story.moveeye_sagt(T.t("MoveEye würde sich freuen: Ihr passt gut aufeinander auf."))
	if main.padmap != null and p2dev >= 0:
		main.padmap.rumble("catch", [p2dev])
	_ev("fortschritt", {"gerettet": true})


func _aufgeben() -> void:
	"""nobody came in 20 s: both back to the last rest place (the story's normal fright)"""
	var von := str(fest.get("von", ""))
	fest = {}
	_ev("neustart", {"grund": "nicht gerettet"})
	story._safe_until = 0.0
	story._schreck(von)                                   # (player 2 follows the jump: _follow_jumps)


# =======================================================================================================================
# the team puzzle of the region
# =======================================================================================================================
func _team_weg() -> void:
	if _tnode != null and is_instance_valid(_tnode):
		_tnode.queue_free()
	_tnode = null
	team = {}


func _team_station() -> Dictionary:
	var h = _hund()
	if h == null or not (h.get("stationen") is Array):
		return {}
	var id: String = ERSETZT.get(str(story.region), "")
	for st in h.stationen:
		if str(st.get("id", "")) == id and st.has("p"):
			return st
	return {}


func _team_bauen(st: Dictionary) -> void:
	_team_weg()
	var reg := str(story.region)
	var art: String = ART.get(reg, "")
	if art == "":
		return
	var p := Vector2((st["p"] as Vector3).x, (st["p"] as Vector3).z)
	var tor: Vector2 = Welt.REG[reg]["tor"]
	var u := (tor - p).normalized()
	if u == Vector2.ZERO:
		u = Vector2(0, 1)
	var v := Vector2(-u.y, u.x)
	var side0 := -1.0
	var h = _hund()
	var idx: int = (h.stationen as Array).find(st) if h != null else -1
	if idx > 0:
		var pp: Vector3 = h.stationen[idx - 1]["p"]
		side0 = signf((Vector2(pp.x, pp.z) - p).dot(u))
		if side0 == 0.0:
			side0 = -1.0
	team = {"region": reg, "art": art, "id": str(st["id"]), "st": st, "p": p, "u": u, "v": v, "stage": 0, "t": 0.0,
			"held_until": 0.0, "passed": false, "side0": side0, "said": 0.0, "done": false, "last": {}}
	_tnode = Node3D.new()
	_tnode.name = "teamraetsel_" + art
	add_child(_tnode)
	match art:
		"steine":
			team["a"] = p + v * 4.0
			team["b"] = p - v * 4.0
			team["steg"] = p + u * 6.0
		"fackel", "stampfen":
			team["h"] = p + v * 7.0
			team["d"] = p + u * 3.0
			team["z"] = p + u * 13.0
			team["s0"] = p - u * 6.0
		"seil":
			team["l"] = p + v * 6.0 + u * side0 * 1.2
			team["l2"] = p + v * 6.0 - u * side0 * 2.2
			team["w"] = p + u * side0 * 2.6 - v * 2.6
			team["k"] = p - u * side0 * 2.4 + v * 2.8
	_props()
	st["ok"] = T.t(GESCHAFFT[art])                        # the text of maggie_hund._fertig
	story.aufgabe_anmelden(str(st["id"]), T.t(AUFGABE[art]))


func _team_tick(dt: float, inp: Dictionary, k1: Array, walking: bool) -> void:
	var h = _hund()
	var st := _team_station()
	var solved: bool = h == null or st.is_empty() or (h.geloest as Dictionary).has(str(st.get("id", "")))
	if solved or not _team_moeglich():
		if not team.is_empty() and (solved or not _team_moeglich()):
			if not solved and st.has("node") and is_instance_valid(st["node"]):
				(st["node"] as Node3D).visible = true          # nobody joined (yet): the old station again
			if not solved:
				_team_weg()
		_big.visible = false
		return
	if team.is_empty() or not is_same(team.get("st"), st):
		_team_bauen(st)
	if st.has("node") and is_instance_valid(st["node"]):
		(st["node"] as Node3D).visible = false            # the fork of maggie_hund.gd is replaced
	var cur: Dictionary = h.aktuell()
	var current: bool = str(cur.get("id", "")) == str(team["id"])
	var p1 := _p1_tal()
	var q2 = _p2_tal()
	var p2: Vector2 = q2 if q2 is Vector2 else Vector2.INF
	var p: Vector2 = team["p"]
	var near := p1.distance_to(p) < 30.0 or p2.distance_to(p) < 30.0
	_props_tick(dt)
	if not current:
		if near and _now() > float(team["said"]):
			team["said"] = _now() + 20.0
			story.tipp(T.t("Hier wartet ein Teamrätsel – aber zuerst kommt etwas anderes. Folgt dem Pfeil!"))
		_big.visible = false
		return
	if not walking:
		return
	var ak: Array = inp["keys"]
	var a2: bool = "a" in ak
	match str(team["art"]):
		"steine":
			var on_a1 := p1.distance_to(team["a"]) < 1.8
			var on_b1 := p1.distance_to(team["b"]) < 1.8
			var on_a2 := p2.distance_to(team["a"]) < 1.8
			var on_b2 := p2.distance_to(team["b"]) < 1.8
			team["occ"] = [on_a1 or on_a2, on_b1 or on_b2]
			if (on_a1 and on_b2) or (on_b1 and on_a2):
				team["t"] = float(team["t"]) + dt
				if float(team["t"]) > 0.8:
					_team_geloest()
					return
			else:
				team["t"] = 0.0
			_big_set(T.t(TITEL["steine"]), T.t("Stell dich auf einen Zauberstein."), T.t("Stell dich auf den anderen Stein – gleichzeitig!"), near)
		"fackel", "stampfen":
			var maggie_key := "a" if str(team["art"]) == "fackel" else "x"
			var key_hit: bool = (maggie_key in ak) if rolle == "maggie" else a2
			var at_h := p2.distance_to(team["h"]) < 3.2
			if at_h and key_hit:
				team["held_until"] = _now() + (12.0 if str(team["art"]) == "fackel" else 5.0)
				_laut_halten()
			elif not at_h and p2.distance_to(team["h"]) > 4.5:
				team["held_until"] = 0.0
			var held: bool = _now() < float(team["held_until"])
			team["held"] = held
			var d1 := p1.distance_to(team["d"])
			if d1 < 4.0:
				if held:
					team["passed"] = true
				else:
					var out: Vector2 = team["d"] + (p1 - (team["d"] as Vector2)).normalized() * 4.3
					story.spieler_setzen(_welt(out))      # (sanft: nur an den Rand – die Tiere lassen dich nicht durch)
					_p1_last = story.spieler_pos()
					if _now() > float(team["said"]):
						team["said"] = _now() + 6.0
						story.tipp(T.t("Die Wölfe lassen dich nicht vorbei! Zuerst muss die Fackel brennen.") if str(team["art"]) == "fackel" \
								else T.t("Die Vipern liegen auf dem Weg! Zuerst muss jemand stampfen."))
			if bool(team["passed"]) and p1.distance_to(team["z"]) < 2.6:
				_team_geloest()
				return
			if p1.distance_to(team["z"]) < 2.6 and not bool(team["passed"]) and _now() > float(team["said"]):
				team["said"] = _now() + 8.0
				story.tipp(T.t("Fast! Aber der Kristall muss durch die Mitte – an den Augen vorbei.") if str(team["art"]) == "fackel" \
						else T.t("Fast! Aber du musst über den Viperweg gehen, nicht daneben."))
			var k2 := "A" if rolle != "maggie" else ("A" if maggie_key == "a" else "X")
			if str(team["art"]) == "fackel":
				_big_set(T.t(TITEL["fackel"]), T.t("Bring den Kristall durch die Schlucht bis zum Steinmann – wenn das Feuer brennt."),
						(T.t("Geh zur Feuerschale und drück %s: das Feuer hält die Wölfe in der Höhle.", [k2]) if rolle != "maggie" else T.t("Lauf zur Feuerschale und drück A: Maggie bellt die Wölfe in die Höhle.")) \
						+ ("   🔥 %d s" % int(ceil(float(team["held_until"]) - _now())) if held else ""), near)
			else:
				_big_set(T.t(TITEL["stampfen"]), T.t("Geh über den Viperweg bis zum Steinmann – wenn gestampft wird."),
						(T.t("Stell dich auf den Stampfstein und drück immer wieder %s.", [k2]) if rolle != "maggie" else T.t("Lauf zum Stampfstein und drück immer wieder X: Maggie scharrt und stampft.")) \
						+ ("   👣" if held else ""), near)
		"seil":
			_zaun(dt)
			var side0: float = team["side0"]
			var p2_far: bool = signf((p2 - p).dot(team["u"])) == -side0 and absf((p2 - p).dot(team["v"])) < 14.0
			if int(team["stage"]) == 0:
				var key := ("y" in ak) if rolle == "maggie" else a2
				if p2_far:
					team["stage"] = 1
				elif p2.distance_to(team["l"]) < 2.4 and key:
					_p2_setzen(team["l2"])
					(team["last"] as Dictionary)["2"] = team["l2"]
					team["stage"] = 1
					_seil_zeigen(true)
					story.tipp(T.t("%s ist durchgeschlüpft und hält das Seil!", [_n2()]))
				_big_set(T.t(TITEL["seil"]), T.t("Warte bei der Winde."), T.t("Schlüpf durch das Loch im Zaun: dort hinstellen und %s drücken.", ["Y" if rolle == "maggie" else "A"]), near)
			else:
				if not p2_far:
					team["stage"] = 0
					_seil_zeigen(false)
					return
				var at_k := p2.distance_to(team["k"]) < 3.6
				var at_w := p1.distance_to(team["w"]) < 2.6
				if at_k and at_w and _p1_a_held():
					team["t"] = float(team["t"]) + dt
					if float(team["t"]) >= 2.5:
						_team_geloest()
						return
				else:
					team["t"] = maxf(0.0, float(team["t"]) - dt * 0.5)
				var pull := int(float(team["t"]) / 2.5 * 100.0)
				_big_set(T.t(TITEL["seil"]), T.t("Stell dich an die Winde und halte A (Tastatur: E) gedrückt.") + ("   %d %%" % pull if pull > 0 else ""),
						T.t("Bleib beim Haken und halte das Seil fest.") if at_k else T.t("Geh zum Haken am Zaun und halte das Seil."), near)


func _team_braucht_knopf(keys: Array) -> bool:
	"""(Maggie) the key belongs to the team puzzle right now"""
	if team.is_empty() or _big == null or not _big.visible:
		return false
	var q2 = _p2_tal()
	if not (q2 is Vector2):
		return false
	match str(team["art"]):
		"fackel":
			return "a" in keys and (q2 as Vector2).distance_to(team["h"]) < 3.2
		"stampfen":
			return "x" in keys and (q2 as Vector2).distance_to(team["h"]) < 3.2
		"seil":
			return "y" in keys and (q2 as Vector2).distance_to(team["l"]) < 2.4
	return false


func _team_geloest() -> void:
	var h = _hund()
	var st: Dictionary = team.get("st", {})
	var art := str(team["art"])
	team["done"] = true
	_big.visible = false
	_props_geloest()
	_seil_zeigen(false)
	if h != null and not st.is_empty():
		h._fertig(st)                                     # the station is solved: task done, saved, the next one
	if story.has_method("_play"):
		story._play("chime")
	_ev("fortschritt", {"raetsel": "team_" + art})
	for d in [p2dev] + _p1_devs():
		if main.padmap != null and int(d) >= 0:
			main.padmap.rumble("catch", [int(d)])


func _p2_setzen(q: Vector2) -> void:
	if rolle == "wanderer":
		_fig2_place(_welt(q))
	else:
		var h = _hund()
		if h != null and h.hund != null and is_instance_valid(h.hund):
			h.place(h.hund, Vector3(q.x, 0, q.y))
			_hund_last = Vector3.INF


func _zaun(_dt: float) -> void:
	"""the fence (spring): nobody walks through it before the gate is open (only through the hole: the key at the hole)"""
	var p: Vector2 = team["p"]
	var u: Vector2 = team["u"]
	var v: Vector2 = team["v"]
	var L: Dictionary = team["last"]
	var who := {"1": _p1_tal()}
	var q2 = _p2_tal()
	if q2 is Vector2:
		who["2"] = q2
	for k in who:
		var q: Vector2 = who[k]
		var s := signf((q - p).dot(u))
		if L.has(k) and (L[k] as Vector2).distance_to(q) < 6.0:   # (a jump - rest place, tests - is no walk through)
			var lq: Vector2 = L[k]
			var ls := signf((lq - p).dot(u))
			if s != ls and s != 0.0 and ls != 0.0 and absf((q - p).dot(v)) < 11.0:
				if k == "1":
					story.spieler_setzen(_welt(lq))
					_p1_last = story.spieler_pos()
				else:
					_p2_setzen(lq)
				if _now() > float(team["said"]):
					team["said"] = _now() + 6.0
					story.tipp(T.t("Der Zaun ist zu hoch. Nur durch das kleine Loch kommt man hinüber."))
				continue
		L[k] = q


# ---- the things of the team puzzles ------------------------------------------------------------------------------------
func _put(n: Node3D, q: Vector2, y := 0.0) -> Node3D:
	var w := _welt(q)
	n.global_position = w + Vector3(0, y, 0)
	return n


func _yaw_of(dir: Vector2) -> float:
	"""a valley direction as a world rotation (the valley may be turned)"""
	var a := _welt(Vector2.ZERO)
	var b := _welt(dir * 10.0)
	var d := b - a
	return atan2(d.x, d.z)


func _props() -> void:
	var art := str(team["art"])
	var stone := Welt.mat(Color(0.52, 0.52, 0.5))
	var holz := Welt.mat(Color(0.42, 0.3, 0.18))
	var lite := _lite()
	var col: Color = Color(0.62, 0.85, 1.0)
	var mark := Node3D.new()                               # a tall light above the puzzle (seen from far)
	_tnode.add_child(mark)
	_put(mark, team["p"])
	var bm := Welt.beam(col)
	mark.add_child(bm)
	bm.position = Vector3(0, 35, 0)
	team["beam"] = bm
	match art:
		"steine":
			for k in ["a", "b"]:
				var n := Node3D.new()
				_tnode.add_child(n)
				_put(n, team[k])
				Welt.cyl(n, 0.85, 0.95, 0.25, Vector3(0, 0.1, 0), stone, 14)
				var g := Welt.cyl(n, 0.6, 0.6, 0.05, Vector3(0, 0.25, 0), Welt.glow(Color(0.5, 0.75, 1.0), 1.2), 14)
				team["glow_" + k] = g
			var steg := Node3D.new()
			_tnode.add_child(steg)
			_put(steg, team["steg"])
			steg.rotation.y = _yaw_of(team["u"])
			var piv := Node3D.new()
			steg.add_child(piv)
			piv.position = Vector3(0, 0.2, -2.0)
			Welt.box(piv, Vector3(1.4, 0.12, 4.0), Vector3(0, 0, 2.0), holz)
			piv.rotation.x = 1.25                         # upright: closed
			team["steg_piv"] = piv
			Welt.cyl(steg, 0.1, 0.1, 2.4, Vector3(-0.8, 1.2, -2.0), holz, 6)
			Welt.cyl(steg, 0.1, 0.1, 2.4, Vector3(0.8, 1.2, -2.0), holz, 6)
		"fackel", "stampfen":
			var hn := Node3D.new()
			_tnode.add_child(hn)
			_put(hn, team["h"])
			if art == "fackel":
				Welt.cyl(hn, 0.55, 0.3, 0.5, Vector3(0, 0.6, 0), Welt.mat(Color(0.2, 0.18, 0.17)), 12)
				Welt.cyl(hn, 0.08, 0.1, 0.4, Vector3(0, 0.2, 0), Welt.mat(Color(0.2, 0.18, 0.17)), 6)
				var fl := MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = 0.35
				sm.height = 0.8
				fl.mesh = sm
				fl.material_override = Welt.glow(Color(1.0, 0.55, 0.15), 3.0)
				fl.position = Vector3(0, 1.05, 0)
				fl.visible = false
				hn.add_child(fl)
				team["flame"] = fl
				if not lite:
					var ol := OmniLight3D.new()
					ol.light_color = Color(1.0, 0.6, 0.3)
					ol.omni_range = 14.0
					ol.light_energy = 0.0
					ol.shadow_enabled = false
					ol.position = Vector3(0, 1.4, 0)
					hn.add_child(ol)
					team["light"] = ol
			else:
				Welt.cyl(hn, 0.9, 1.0, 0.3, Vector3(0, 0.12, 0), stone, 10)
				Welt.cyl(hn, 0.04, 0.04, 1.4, Vector3(0.5, 0.95, 0), holz, 6)
			# the narrow place: rocks on both sides, the danger in the middle
			var dn := Node3D.new()
			_tnode.add_child(dn)
			_put(dn, team["d"])
			dn.rotation.y = _yaw_of(team["u"])
			var rock := Welt.mat(Color(0.36, 0.35, 0.34))
			for sx in [-1.0, 1.0]:
				for i in range(4):
					Welt.box(dn, Vector3(1.6, 2.2 + i % 2 * 0.8, 2.6), Vector3(sx * 3.4, 1.0, -4.0 + i * 2.7), rock, Vector3(0, 0.3 * i * sx, 0.1 * sx))
			var bad := Node3D.new()
			dn.add_child(bad)
			team["bad"] = bad
			if art == "fackel":
				var busch := Welt.mat(Color(0.1, 0.13, 0.1))
				for i in range(3):
					var bs := MeshInstance3D.new()
					var sp := SphereMesh.new()
					sp.radius = 0.9
					sp.height = 1.3
					bs.mesh = sp
					bs.material_override = busch
					bs.position = Vector3(2.0 + i * 0.4, 0.55, -0.8 + i * 0.8)
					bad.add_child(bs)
				var eyes := []
				for i in range(2):
					for sx in [-1.0, 1.0]:
						var e := MeshInstance3D.new()
						var es := SphereMesh.new()
						es.radius = 0.05
						es.height = 0.1
						e.mesh = es
						e.material_override = Welt.glow(Color(1.0, 0.78, 0.25), 4.0)
						e.position = Vector3(1.25, 0.7 + i * 0.12, -0.4 + i * 0.9 + sx * 0.09)
						bad.add_child(e)
						eyes.append(e)
				team["eyes"] = eyes
			else:
				var vip := Welt.mat(Color(0.25, 0.27, 0.16))
				for i in range(3):
					var sn := Node3D.new()
					bad.add_child(sn)
					sn.position = Vector3(-0.8 + i * 0.8, 0.06, -1.0 + i * 1.0)
					sn.rotation.y = 0.6 * i
					for j in range(5):
						var c := MeshInstance3D.new()
						var cs := SphereMesh.new()
						cs.radius = 0.06
						cs.height = 0.1
						c.mesh = cs
						c.material_override = vip
						c.position = Vector3(sin(j * 1.1) * 0.12, 0, j * 0.11)
						sn.add_child(c)
			var zn := Node3D.new()
			_tnode.add_child(zn)
			_put(zn, team["z"])
			for i in range(3):
				Welt.cyl(zn, 0.4 - i * 0.1, 0.45 - i * 0.1, 0.35, Vector3(0, 0.17 + i * 0.33, 0), stone, 8)
			Welt.cyl(zn, 0.12, 0.12, 0.12, Vector3(0, 1.15, 0), Welt.glow(Color(0.62, 0.85, 1.0), 2.5), 8)
		"seil":
			var fz := Node3D.new()
			_tnode.add_child(fz)
			_put(fz, team["p"])
			fz.rotation.y = _yaw_of(team["v"])               # the fence runs along v (local z)
			for i in range(-5, 6):
				Welt.cyl(fz, 0.07, 0.08, 1.6, Vector3(0, 0.8, i * 2.0), holz, 6)
			for y in [0.5, 1.0, 1.45]:
				Welt.box(fz, Vector3(0.06, 0.12, 9.0), Vector3(0, y, -5.5), holz)
				if y > 0.6:
					Welt.box(fz, Vector3(0.06, 0.12, 9.0), Vector3(0, y, 5.5), holz)
				else:                                      # the hole at +6: no low rail from 5 to 7 m
					Welt.box(fz, Vector3(0.06, 0.12, 4.0), Vector3(0, y, 3.0), holz)
					Welt.box(fz, Vector3(0.06, 0.12, 3.0), Vector3(0, y, 8.5), holz)
			var hole := Welt.cyl(fz, 0.5, 0.5, 0.04, Vector3(0, 0.03, 6.0), Welt.mat(Color(0.12, 0.1, 0.08)), 10)
			hole.scale = Vector3(1.6, 1, 1.6)
			var gate := Node3D.new()
			fz.add_child(gate)
			gate.position = Vector3(0, 0, -1.0)
			for y in [0.5, 1.0, 1.45]:
				Welt.box(gate, Vector3(0.06, 0.12, 2.0), Vector3(0, y, 1.0), Welt.mat(Color(0.55, 0.4, 0.22)))
			Welt.box(gate, Vector3(0.06, 1.2, 0.08), Vector3(0, 0.95, 1.0), holz, Vector3(0.9, 0, 0))
			team["gate"] = gate
			var wn := Node3D.new()
			_tnode.add_child(wn)
			_put(wn, team["w"])
			Welt.box(wn, Vector3(0.9, 0.9, 0.6), Vector3(0, 0.45, 0), holz)
			Welt.cyl(wn, 0.25, 0.25, 1.0, Vector3(0, 1.05, 0), Welt.mat(Color(0.3, 0.3, 0.32)), 10)
			var kn := Node3D.new()
			_tnode.add_child(kn)
			_put(kn, team["k"])
			Welt.cyl(kn, 0.08, 0.08, 1.4, Vector3(0, 0.7, 0), holz, 6)
			Welt.cyl(kn, 0.1, 0.1, 0.1, Vector3(0, 1.35, 0), Welt.glow(Color(1.0, 0.8, 0.3), 2.0), 6)
			var rope := Node3D.new()
			_tnode.add_child(rope)
			var ropem := Welt.mat(Color(0.75, 0.62, 0.4))
			for seg in [["w", "l"], ["l", "k"]]:
				var a := _welt(team[seg[0]]) + Vector3(0, 0.9, 0)
				var b := _welt(team[seg[1]]) + Vector3(0, 0.5, 0)
				var mi := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.025
				cm.bottom_radius = 0.025
				cm.height = a.distance_to(b)
				cm.radial_segments = 5
				mi.mesh = cm
				mi.material_override = ropem
				rope.add_child(mi)
				var dir := (b - a).normalized()
				var ax := Vector3.UP.cross(dir)
				var bs := Basis(ax.normalized(), Vector3.UP.angle_to(dir)) if ax.length() > 0.001 else Basis()
				mi.global_transform = Transform3D(bs, (a + b) / 2.0)
			rope.visible = false
			team["rope"] = rope


func _props_tick(_dt: float) -> void:
	var art := str(team.get("art", ""))
	var held := bool(team.get("held", false))
	match art:
		"steine":
			var occ: Array = team.get("occ", [false, false])
			for i in range(2):
				var g = team.get("glow_" + ["a", "b"][i])
				if g != null and is_instance_valid(g):
					((g as MeshInstance3D).material_override as StandardMaterial3D).emission_energy_multiplier = 4.0 if bool(occ[i]) else 1.0
		"fackel":
			var fl = team.get("flame")
			if fl != null and is_instance_valid(fl):
				(fl as Node3D).visible = held
				(fl as Node3D).scale = Vector3.ONE * (1.0 + 0.12 * sin(_now() * 11.0))
			var ol = team.get("light")
			if ol != null and is_instance_valid(ol):
				(ol as OmniLight3D).light_energy = (2.5 + 0.4 * sin(_now() * 13.0)) if held else 0.0
			for e in team.get("eyes", []):
				if is_instance_valid(e):
					(e as Node3D).visible = not held and not bool(team.get("done", false))
		"stampfen":
			var bad = team.get("bad")
			if bad != null and is_instance_valid(bad):
				var want := 3.2 if held or bool(team.get("done", false)) else 0.0
				(bad as Node3D).position.x = move_toward((bad as Node3D).position.x, want, _dt * 2.0)


func _props_geloest() -> void:
	match str(team.get("art", "")):
		"steine":
			var piv = team.get("steg_piv")
			if piv != null and is_instance_valid(piv):
				var tw := create_tween()
				tw.tween_property(piv, "rotation:x", 0.0, 1.6).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
		"seil":
			var g = team.get("gate")
			if g != null and is_instance_valid(g):
				var tw2 := create_tween()
				tw2.tween_property(g, "rotation:y", -1.7, 1.4).set_trans(Tween.TRANS_SINE)
		"fackel":
			team["held_until"] = _now() + 600.0
	var bm = team.get("beam")
	if bm != null and is_instance_valid(bm):
		(bm as Node3D).visible = false


func _seil_zeigen(v: bool) -> void:
	var r = team.get("rope")
	if r != null and is_instance_valid(r):
		(r as Node3D).visible = v


func _laut_halten() -> void:
	var h = _hund()
	if rolle == "maggie" and h != null and h.hund != null and is_instance_valid(h.hund):
		if str(team["art"]) == "fackel":
			h.bellen(h.ppos(h.hund), 2)
		return


# =======================================================================================================================
# the views (zweit_bild.gd)
# =======================================================================================================================
func _views(v: bool) -> void:
	if v == on:
		if v:
			main.get_viewport().disable_3d = true          # (main._check_active sets it every 0.5 s – we are after it)
		return
	on = v
	if v:
		_build_views()
		var p2 = _p2_welt()
		merged = p2 is Vector3 and story.spieler_pos().distance_to(p2) < ZB.NEAR_IN
	if _layer != null:
		_layer.visible = v
	for i in range(2):
		if _v[i].is_empty():
			continue
		(_v[i]["vp"] as SubViewport).render_target_update_mode = SubViewport.UPDATE_ALWAYS if v else SubViewport.UPDATE_DISABLED
		(_v[i]["cam"] as Camera3D).current = v
	main.get_viewport().disable_3d = v or not main.win_open
	_fps.clear()


func _build_views() -> void:
	if _layer != null:
		return
	_layer = CanvasLayer.new()
	_layer.layer = -1                                     # under the cards and the HUD of the story
	add_child(_layer)
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_root)
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.04, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(bg)
	var mask: int = (main.view_cam as Camera3D).cull_mask
	for i in range(2):
		_v[i] = ZB.ansicht(_root, COLS[i], mask, 17)
	_line = ColorRect.new()
	_line.color = Color(0.02, 0.03, 0.04)
	_line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_line)


func _p2_cam_xf(p2: Vector3) -> Transform3D:
	var dog := rolle == "maggie"
	var tp := p2 + Vector3(0, 0.55 if dog else 1.35, 0)
	var dist := 4.2 if dog else 6.5
	var back := Vector3(sin(yaw2), 0, cos(yaw2))
	var want := tp + back * dist * cos(pitch2) + Vector3(0, dist * sin(pitch2), 0)
	want.y = maxf(want.y, main.ground_y(want.x, want.z) + 0.8)
	return Transform3D(Basis.IDENTITY, want).looking_at(tp, Vector3.UP)


func _view_tick(dt: float) -> void:
	var p2 = _p2_welt()
	var p1: Vector3 = story.spieler_pos()
	var d := p1.distance_to(p2) if p2 is Vector3 else 999.0
	var m := ZB.zusammen(merged, d)
	if m != merged:
		merged = m
		_say(T.t("Zusammen – ein Bild") if merged else T.t("Getrennt – geteilter Bildschirm"))
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	var a := Rect2(Vector2.ZERO, vs)
	var rr := ZB.teilen(a, merged)
	ZB.setzen(_v[0], rr[0])
	(_v[1]["box"] as Control).visible = not merged
	if not merged:
		ZB.setzen(_v[1], rr[1])
	ZB.trennlinie(_line, rr[0], a, bool(rr[2]), merged)
	ZB.zeichnen(_v[0], _v[1], not merged, _lite(), _frame, main.get_viewport().msaa_3d)
	var c0: Camera3D = _v[0]["cam"]
	var c1: Camera3D = _v[1]["cam"]
	var k := clampf(dt * 6.0, 0.0, 1.0)
	if merged and p2 is Vector3:
		var mid: Vector3 = (p1 + p2) / 2.0
		var cy := float(story.cam_yaw)
		var fw := Vector3(-sin(cy), 0.0, -cos(cy))
		var eye := mid - fw * (6.5 + d * 0.7) + Vector3(0, 2.6 + d * 0.3, 0)
		eye.y = maxf(eye.y, main.ground_y(eye.x, eye.z) + 1.5)
		var xf := Transform3D(Basis(), eye).looking_at(mid + fw * 3.0 + Vector3(0, 0.8, 0), Vector3.UP)
		c0.global_transform = c0.global_transform.interpolate_with(xf, k)
	else:
		c0.global_transform = (main.view_cam as Camera3D).global_transform    # the story's camera of player 1
		c0.fov = (main.view_cam as Camera3D).fov
		if p2 is Vector3:
			c1.global_transform = c1.global_transform.interpolate_with(_p2_cam_xf(p2), k)
	# the chips
	var c0l: Label = _v[0]["chip"]
	var c1l: Label = _v[1]["chip"]
	var dev1 := "🎮" if not _p1_devs().is_empty() else "⌨"
	var dev2 := "🎮" if p2dev != -1 else T.t("wartet auf A")
	c0l.position = (rr[0] as Rect2).position + Vector2(12, 12)
	c1l.visible = not merged
	c1l.position = (rr[1] as Rect2).position + Vector2(12, 12)
	if merged:
		c0l.text = "1 · %s %s   +   2 · %s %s" % [_n1(), dev1, _n2(), dev2]
	else:
		c0l.text = "1 · %s %s" % [_n1(), dev1]
		c1l.text = "2 · %s %s" % [_n2(), dev2]
	var t := _now()
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
# big hints (who presses what)
# =======================================================================================================================
func _build_hud() -> void:
	_hl = CanvasLayer.new()
	_hl.layer = 7                                         # above Maggie's buttons (6), under the cards of the story
	add_child(_hl)
	var top := VBoxContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	top.grow_horizontal = Control.GROW_DIRECTION_BOTH
	top.offset_top = 70
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.alignment = BoxContainer.ALIGNMENT_BEGIN
	_hl.add_child(top)
	_big = PanelContainer.new()
	_big.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.93), Color(0.62, 0.85, 1.0), 14, 12, 2))
	_big.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(_big)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	_big.add_child(v)
	_big_t = _lab(22, Color(0.62, 0.85, 1.0))
	v.add_child(_big_t)
	_big_1 = _lab(19, COLS[0])
	v.add_child(_big_1)
	_big_2 = _lab(19, COLS[1])
	v.add_child(_big_2)
	_big.visible = false
	_say_l = _lab(20, UI.TXT)
	_say_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	top.add_child(_say_l)
	_say_l.visible = false
	# «Spieler 2: Drücke A»
	var cc := CenterContainer.new()
	cc.set_anchors_preset(Control.PRESET_FULL_RECT)
	cc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hl.add_child(cc)
	_join = PanelContainer.new()
	_join.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.95), COLS[1], 18, 18, 3))
	cc.add_child(_join)
	var jv := VBoxContainer.new()
	jv.add_theme_constant_override("separation", 10)
	_join.add_child(jv)
	var jt := _lab(30, COLS[1])
	jt.text = T.t("Spieler 2: Drücke A auf deinem Controller")
	jt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	jv.add_child(jt)
	_join_t = _lab(17, UI.TXT)
	_join_t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	jv.add_child(_join_t)
	var later := Button.new()
	later.text = T.t("Später (Spieler 2 läuft einfach mit)")
	later.focus_mode = Control.FOCUS_NONE
	later.custom_minimum_size = Vector2(0, 40)
	later.pressed.connect(func(): _later = true)
	jv.add_child(later)
	_join.visible = false


func _lab(sz: int, col: Color) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 6)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(620, 0)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _big_set(title: String, t1: String, t2: String, show: bool) -> void:
	if not fest.is_empty():
		return
	_big.visible = show
	_big_t.text = "🤝 " + title
	_big_1.text = "1 · %s: %s" % [_n1(), t1]
	_big_2.text = "2 · %s: %s" % [_n2(), t2]


func _say(t: String) -> void:
	_say_l.text = t
	_say_until = _now() + 4.0


func _hud_tick() -> void:
	_say_l.visible = _now() < _say_until
	var want_join: bool = p2dev == -1 and not _later and str(story.phase) in WALK and not _frozen
	_join.visible = want_join
	if want_join:
		var n: int = main.padmap.devices().size() if main.padmap != null else 0
		_join_t.text = (T.t("Kein Controller gefunden – USB oder Bluetooth anschliessen.") if n == 0 else T.t("%d Controller verbunden.", [n])) \
				+ "\n" + T.t("Spieler 1 spielt mit der Tastatur (W A S D, E = A-Knopf) oder mit dem anderen Controller.")
	if not fest.is_empty():
		var left := maxf(0.0, float(fest["bis"]) - _now())
		_big.visible = true
		_big_t.text = "⚠ " + T.t("%s ist umzingelt!", [_n1()])
		_big_1.text = "1 · %s: %s" % [_n1(), T.t("Warte – Hilfe kommt!")]
		_big_2.text = "2 · %s: %s" % [_n2(), T.t("Lauf hin und drück A! (noch %d s)", [int(ceil(left))])]


# =======================================================================================================================
# control API (through maggie_story.control {"do": "zwei", …})
# =======================================================================================================================
static func steuer(st, d: Dictionary) -> Dictionary:
	var k := str(d.get("k", "info"))
	if k == "wahl":
		st.main.set_meta("maggie_zwei_wahl", {"n": int(d.get("n", 2)), "rolle": str(d.get("rolle", "wanderer")),
				"name2": str(d.get("name2", "")), "col2": str(d.get("col2", "navy"))})
		return {"ok": true, "wahl": st.main.get_meta("maggie_zwei_wahl")}
	var z = st.get_node_or_null("maggie_zwei")
	if z == null:
		return {"ok": false, "error": "Geschichte läuft nicht (maggie_zwei fehlt)"}
	return z.control(d)


func control(d: Dictionary) -> Dictionary:
	var k := str(d.get("k", "info"))
	var out := {"ok": true}
	match k:
		"an":
			_apply({"n": int(d.get("n", 2)), "rolle": str(d.get("rolle", rolle)), "name2": str(d.get("name2", name2)), "col2": str(d.get("col2", look2.get("col", "navy")))})
			if rolle == "wanderer" and aktiv and story.spieler() != null:
				_fig2_ensure(_neben_p1())
			else:
				_fig2_weg()
			_team_weg()
		"join":
			_set_p2(int(d.get("dev", TEST_DEV)))
		"pad":
			var ls: Array = d.get("ls", [0, 0])
			var rs: Array = d.get("rs", [0, 0])
			_vpad = {"ls": Vector2(float(ls[0]), float(ls[1])), "rs": Vector2(float(rs[0]), float(rs[1])), "run": bool(d.get("run", false)),
					"until": _now() + float(d.get("secs", 1.0)), "press": d.get("press", []), "hold": d.get("hold", [])}
		"p1":
			_p1_test["press"] = d.get("press", [])
			if d.has("hold"):
				_p1_test["hold_until"] = _now() + float(d["hold"])
		"hin":                                           # tests: player 1 / 2 to a place of the team puzzle (or the station)
			var who := int(d.get("p", 1))
			var ort := str(d.get("ort", "p"))
			var q = null
			if ort == "p" and not team.is_empty():
				q = team["p"]
			elif team.has(ort):
				q = team[ort]
			elif ort == "p1":
				q = _p1_tal()
			if q == null:
				var st := _team_station()
				if st.is_empty():
					return {"ok": false, "error": "kein Teamrätsel", "info": info()}
				q = Vector2((st["p"] as Vector3).x, (st["p"] as Vector3).z)
			var off: Array = d.get("off", [0, 0])
			var qq: Vector2 = (q as Vector2) + Vector2(float(off[0]), float(off[1]))
			if who == 1:
				story.spieler_setzen(_welt(qq))
				_p1_last = story.spieler_pos()
				var tl: Dictionary = team.get("last", {})
				tl.erase("1")
			else:
				_p2_setzen(qq)
				var tl2: Dictionary = team.get("last", {})
				tl2.erase("2")
		"p2":
			_p2_setzen(Vector2(float(d.get("x", 0)), float(d.get("z", 0))))
		"fest":
			out["faengt"] = faengt(str(d.get("von", "wolf")))
		"retten":
			retten()
		"loesen":
			if not team.is_empty():
				_team_geloest()
		"lite":
			force_lite = bool(d.get("value", true))
		"fps":
			out["fps"] = snappedf(fps_avg(), 0.1)
	out["zwei"] = info()
	return out


func info() -> Dictionary:
	var p2 = _p2_tal()
	var p1 := _p1_tal() if story != null and story.spieler() != null else Vector2.ZERO
	var tm := {}
	if not team.is_empty():
		tm = {"art": team["art"], "id": team["id"], "stage": team["stage"], "held": bool(team.get("held", false)),
				"passed": team["passed"], "t": snappedf(float(team["t"]), 0.01), "done": team["done"],
				"p": [snappedf((team["p"] as Vector2).x, 0.1), snappedf((team["p"] as Vector2).y, 0.1)]}
		var h = _hund()
		if h != null:
			tm["aktuell"] = str(h.aktuell().get("id", ""))
	var hd = _hund()
	return {"aktiv": aktiv, "rolle": rolle, "name2": _n2(), "p2dev": p2dev, "on": on, "merged": merged,
			"p1": [snappedf(p1.x, 0.1), snappedf(p1.y, 0.1)],
			"p2": [snappedf((p2 as Vector2).x, 0.1), snappedf((p2 as Vector2).y, 0.1)] if p2 is Vector2 else [],
			"abstand": snappedf(p1.distance_to(p2), 0.1) if p2 is Vector2 else -1.0,
			"fest": snappedf(float(fest["bis"]) - _now(), 0.1) if not fest.is_empty() else -1.0, "gerettet": gerettet,
			"team": tm, "hund_gefuehrt": fuehrt_hund(), "hund_zustand": str(hd.zustand_hund) if hd != null else "",
			"leine": _leine, "join": _join.visible if _join != null else false, "gross": _big.visible if _big != null else false,
			"gross_text": (_big_t.text + " | " + _big_1.text + " | " + _big_2.text) if _big != null else "",
			"lite": _lite(), "fps": snappedf(fps_avg(), 0.1), "phase": str(story.phase) if story != null else ""}
