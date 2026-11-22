extends Node
## «Als Person gehen» (Besitzer 13.11.2026) - ab «Frei erkunden mit eigener Figur» (Besitzer 21.11.2026, Etappe 1) mit der
## Figur aus Grossvater Kapitel 2 (kit_figur.gd: springen, klettern; kit_regie.gd: die Federkamera). Die alte
## Wanderer-Figur mit Panzersteuerung ist ersetzt (Entfernen vom Besitzer bestätigt). Ein Kind von explore.gd («ex»).
##   * Umschalten wie bisher: Knopf «🚶 Person» / «🚜 Mover» (Erkunden-Leiste oben, Menü «Ansicht» der Leiste unten,
##     Abenteuer-Spalte), Taste U, Controller Select 1 s halten. Neu: «🥾 Frei erkunden» (Spielen → Abenteuer, Spiel-Assistent)
##     startet Erkunden gleich als Figur, in der Welt, die gerade geladen ist (jede Welt).
##   * Gehen: W A S D / Pfeile, grüner Stick (Maus, Touch), rechter Stick des Controllers - relativ zur Kamera (W = weg von
##     der Kamera). Rennen: Shift, oder Stick / grüne Kugel ganz am Rand. Rechte Maustaste / R1 + rechter Stick = umschauen,
##     Rad = Abstand.
##   * Haltung (C / ✚ ↓ / Knopf am Rand): stehen → geduckt → kriechen → stehen. X (✚ ←) = hinsetzen (auf eine Bank oder einen
##     Stein in der Nähe, sonst auf den Boden), Z (✚ →) = hinlegen und still liegen; nochmals oder losgehen = aufstehen.
##     Leertaste (✚ ↑) = springen, vor einer Kante (0,6–2,2 m, erkunden_welt.gd) hochklettern; E / F = nur hochklettern.
##     Geduckt und kriechend ist die Figur wirklich niedriger (Gelenke von actor.gd, Crouch-Clips von figur_paket.gd) - MoveEye
##     sieht ein kleineres Ziel (Sinn der Sache). Geduckt / kriechend kein Rennen, kein Springen (zuerst aufstehen).
##   * Wasser (erkunden_welt.gd): seicht = waten (langsamer, nicht rennen), tief = schwimmen an der Oberfläche (kein Tauchen,
##     niemand ertrinkt); hinaus geht es einfach, wo das Wasser wieder seicht wird oder das Ufer beginnt.
##   * Schnelllauf zum Testen: rennen bis 40 m/s in Stufen 1,8 / 3 / 5 / 10 / 15 / 20 / 30 / 40 (Besitzer: 40 statt 20; Knopf «Tempo» oben, main.ex_ptempo,
##     bleibt gespeichert). Schalter im Entwickler-Bereich «Schnelllauf beim Erkunden» (main.ex_schnell): aus = normales
##     Rennen (3,45 m/s, wie actor.gd). Auch schnell nie durch eine Wand: actor.gd und hier in Schritten von höchstens 0,2 m
##     mit main.keep_out (auch im Sprung).
##   * Ansichten (V / R3 / Knopf): hinter der Figur (Federkamera kit_regie.gd), aus den Augen (die Augenhöhe folgt der Haltung:
##     der Kopf der Figur), von oben.
##   * Die Kameras von MoveEye sehen die Figur wie einen Besucher (heute immer; Etappe 2: Schalter).
##   * Nie während einer Messung, nicht beim Spiel am PC, nicht in einer Spielrunde ausser «Zonen-Check», nicht zu zweit im
##     Abenteuer, nicht in «Maggie» (why_not): dann ist der Knopf weg und eine laufende Figur wird wieder zum Mover.
## In der Geschichte (bergtal_abenteuer.gd, Schritte «Unterwegs» und «Nachtlager»): wie bisher - die Figur zählt wie ein
##   Wanderer zu zweit (abenteuer_geheim.gd walkers()), main.walker_pos() ist ihr Standort, sie geht mit der Gruppe mit und darf
##   sich höchstens LEASH = 110 m entfernen.
## Steuerbefehl {"action": "explore", "person": true | false, "pwalk": [vor, drehen, Sekunden, rennen], "pplace": [x, z],
##   "haltung": stehen | geduckt | kriechen | weiter, "sitzen": bool, "liegen": bool, "sprung": true, "klettern": true,
##   "pview": chase | driver | top, "ptempo": m/s, "schnell": bool} - Zustand in explore.state() unter «person».

const T = preload("res://scripts/i18n.gd")
const ActorS = preload("res://scripts/actor.gd")
const Figur = preload("res://scripts/figur.gd")
const Bt = preload("res://scripts/bergtal.gd")
const KitFigur = preload("res://scripts/kit_figur.gd")
const Regie = preload("res://scripts/kit_regie.gd")
const Welt = preload("res://scripts/erkunden_welt.gd")
const Touch = preload("res://scripts/erkunden_touch.gd")
const EFigur = preload("res://scripts/erkunden_figur.gd")
const Begleiter = preload("res://scripts/erkunden_begleiter.gd")
const Gestalten = preload("res://scripts/erkunden_gestalten.gd")
const Sachen = preload("res://scripts/erkunden_sachen.gd")
const Extras = preload("res://scripts/erkunden_extras.gd")

const TURN := 2.4                    # rad/s: A / D drehen in der Ich-Sicht (und im Testgang pwalk)
const LEASH := 110.0                 # m: so weit von der Gruppe weg in der Geschichte (wie abenteuer_zweit.gd)
const EYE := 1.62                    # m: Augenhöhe stehend (Rückfall, wenn die Figur keinen Kopf-Knoten hat)
const BOUND := 180.0                 # m: ausserhalb des Bergtals so weit wie der Mover (main._drive)
const FULL := 0.95                   # Stick / grüne Kugel so weit draussen = rennen
const HALTUNGEN := ["stehen", "geduckt", "kriechen"]
const POSTUR := {"stehen": 0, "geduckt": 1, "kriechen": 2, "sitzen": 0, "liegen": 2}
const AUGE := {"stehen": 1.62, "geduckt": 1.05, "kriechen": 0.38, "sitzen": 1.15, "liegen": 0.3}   # Rückfall ohne Kopf
const TEMPI := [1.8, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0]   # m/s: Schnelllauf (rennen), Besitzer 21.11.2026 (bis 40)
const V_MAX := 40.0
const V_RENNEN := 3.45               # m/s: normales Rennen (actor.PLAYER_SPEED[0] × 2.3) - Schnelllauf aus
const SCHWIMM_V := 0.9               # m/s an der Oberfläche
const SCHWIMM_TIEF := 0.25           # m: die Füsse so weit unter dem Wasserspiegel (der Körper liegt, der Kopf ist oben)
const WATEN_K := 0.55                # waten: so viel vom Tempo
const LOOK := {"col": "red", "size": "", "build": "", "hat": "", "pack": true}

var ex
var main
var active := false                  # die Figur wird gesteuert (sonst steht sie, wo man sie gelassen hat)
var actor: Node3D = null             # = figur.a (actor.gd, controlled)
var yaw := 0.0                       # wohin die Figur schaut (actor.heading)
var cmd := Vector2.ZERO              # (vorwärts, rechts) von rover_pad.command()
var run := false
var haltung := "stehen"              # stehen | geduckt | kriechen | sitzen | liegen
var wasser := ""                     # "" | waten | schwimmen
var spiegel := 0.0                   # Welt-y des Wasserspiegels (beim Schwimmen)
var sitz := {}                       # erkunden_welt.sitz(): wo sie sitzt
var touch: CanvasLayer = null
var begleiter: Node = null           # erkunden_begleiter.gd: Maggie, Blinki, «MoveEye sieht dich» (Etappe 2)
var gestalten: CanvasLayer = null    # erkunden_gestalten.gd: die Figur gestalten (Etappe 2)
var sachen: Node = null              # erkunden_sachen.gd: Rucksack-Sachen und Kraft (Etappe 3)
var extras: Node = null              # erkunden_extras.gd: Fotomodus, Ort merken, Startpunkte (Etappe 4)
var _abseil := {}                    # rappelling: {von, kante, nach, t, dauer}
var _y_hoch := -INF                  # the highest point of the last flight (a hard landing, «Echt»)
var _scene := ""
var _anchor = null                   # Geschichte: wo die Gruppe zuletzt war (Tal)
var _test := {}                      # Tests: {"v": Vector2, "run": bool, "until": s}
var _far_t := -100.0
var _ein := {}
var _wunsch := {}                    # Tasten / Knöpfe seit dem letzten Bild: sprung, klettern, haltung, sitzen, liegen
var _eye_yaw := 0.0                  # Ich-Sicht: wohin man schaut
var _eye_p := Vector3.ZERO
var _eye_ok := false
var _top_yaw := 0.0
var _orbit_alt := 0.0
var _pitch_alt := 0.5
var _dist_alt := 6.0
var _view_alt := ""
var _spaet: Node = null
var _sk: Skeleton3D = null
var _sk_von: Node = null
var _sk_kopf := -1

# ---- what kit_figur.gd / kit_regie.gd read from their «kit» (here: no parcours, no film) ----
var par = ParLeer.new()
var figur
var regie
var uhr := 0.0
var phase := "spiel"                 # kit_figur.gd: small steps up only «im Spiel»
var weg := PackedVector2Array()      # no way to guide along
var daten = null
var kinder := false
var film_move := Vector2.ZERO
var film_run := false
var film_hang := false
var film_hang_p := Vector3.ZERO
var film_hang_auf := Vector3.ZERO
var nach_klettern := {}
var _karte := {}


class ParLeer:
	## kit_parcours.gd without a parcours: no actions, no dangers (the water: erkunden_welt.gd)
	var aktionen: Array = []
	var dinge := {}
	var schlucht = null

	func aktion_bei(_w: Vector3, _nur := true) -> Dictionary:
		return {}

	func gefahr_bei(_w: Vector3) -> Dictionary:
		return {}

	func ding_bei(_w: Vector3, _pad := 0.0) -> String:
		return ""

	func tal_von(w: Vector3) -> Vector2:
		return Vector2(w.x, w.z)

	func sq_von(w: Vector3) -> Vector2:
		return Vector2(w.x, w.z)

	func W(p: Vector3) -> Vector3:
		return p


static func why_not(m) -> String:
	"""'' = hier darf man als Person gehen; sonst der Grund (der Knopf ist dann weg)"""
	if m == null:
		return "-"
	if m.measuring() or m.busy_with() == "Nacht-Testlauf":
		return "Messung läuft"
	if m.localplay != null and m.localplay.active:
		return "Spiel am PC"
	if m.game != null and bool(m.game.open) and str(m.game.round_state) in ["countdown", "play"] and str(m.game_mode) != "free":
		return "Spielrunde läuft"
	var ab = m.get("abenteuer")
	if ab != null and ab.get("zweit") != null and bool(ab.zweit.on):
		return "zu zweit unterwegs"
	var mg = m.get("maggie")
	if mg != null and is_instance_valid(mg) and bool(mg.get("running")):
		return "Maggie läuft"
	var kt = m.get("kit")
	if kt != null and is_instance_valid(kt) and bool(kt.get("running")):
		return "Abenteuer läuft"
	return ""


func _ready() -> void:
	process_priority = -20                                   # before the actors: what the figure wants
	regie = Regie.new(self)
	figur = KitFigur.new(self)
	_spaet = Node.new()
	_spaet.name = "erkunden_spaet"
	_spaet.process_priority = 95                             # after the actors: height, walls, water, the camera
	_spaet.set_script(preload("res://scripts/kit_spaet.gd"))
	_spaet.set("kit", self)
	add_child(_spaet)
	touch = Touch.new()
	touch.person = self
	add_child(touch)
	begleiter = Begleiter.new()
	begleiter.person = self
	begleiter.main = main
	add_child(begleiter)
	gestalten = Gestalten.new()
	gestalten.person = self
	gestalten.main = main
	add_child(gestalten)
	sachen = Sachen.new()
	sachen.person = self
	sachen.main = main
	add_child(sachen)
	extras = Extras.new()
	extras.person = self
	extras.main = main
	add_child(extras)


func _now() -> float:
	return main.now()


func ok() -> bool:
	return actor != null and is_instance_valid(actor)


# ---- settings: fast run ------------------------------------------------------------------------------------------------
static func schnell_an(m) -> bool:
	return m != null and bool(m.get("ex_schnell"))


static func renn_tempo(m) -> float:
	"""the running speed of the standing figure: the chosen step (fast run on) or the normal 3.45 m/s"""
	if not schnell_an(m):
		return V_RENNEN
	return clampf(float(m.get("ex_ptempo")), 1.0, V_MAX)


static func tempo_naechste(v: float) -> float:
	"""the step of TEMPI nearest to v"""
	var i := 0
	for k in TEMPI.size():
		if absf(float(TEMPI[k]) - v) < absf(float(TEMPI[i]) - v):
			i = k
	return float(TEMPI[i])


func tempo_stufe(dir: int, wrap := false) -> void:
	var i := 0
	for k in TEMPI.size():
		if absf(float(TEMPI[k]) - float(main.ex_ptempo)) < absf(float(TEMPI[i]) - float(main.ex_ptempo)):
			i = k
	i += dir
	if wrap:
		i = posmod(i, TEMPI.size())
	set_tempo(float(TEMPI[clampi(i, 0, TEMPI.size() - 1)]))
	main.start_info = T.t("Rennen (Shift): %s m/s") % _num(float(main.ex_ptempo))


func set_tempo(v: float) -> void:
	main.ex_ptempo = clampf(v, 1.0, V_MAX)
	main._settings_dirty = true


static func _num(v: float) -> String:
	return str(snappedf(v, 0.1)).trim_suffix(".0")


# ---- the story ---------------------------------------------------------------------------------------------------------
func story():
	"""bergtal_abenteuer.gd, wenn die Person dort mitgeht (Unterwegs / Nachtlager im Bergtal), sonst null"""
	var ab = main.get("abenteuer")
	if ab == null or ab.R.is_empty() or main.scene != "bergtal" or ab.bt() == null:
		return null
	if not int(ab.step) in [4, 5]:
		return null
	return ab


func _anchor_of(ab) -> Vector2:
	if int(ab.step) == 5:
		return ab.R.get("camp_xz", ab.R["pos"])
	return ab.R["pos"]


func valley_pos():
	"""wo die Person im Tal steht (Vector2) - null ohne Bergtal oder ohne Person"""
	if not ok():
		return null
	var b = main.scenes.data.get("bergtal", null) if main.scene == "bergtal" and main.scenes != null else null
	if b == null:
		return null
	var q: Vector3 = b.V(actor.global_position)
	return Vector2(q.x, q.z)


# ---- the figure ----------------------------------------------------------------------------------------------------------
func _spawn_at() -> Vector3:
	var ab = story()
	if ab != null:
		var an := _anchor_of(ab)
		var q := an + Vector2(1.6, 2.0)                   # neben der Gruppe (wie Spieler 1 zu zweit)
		return ab.bt().WG(q.x, q.y, 0.0)
	var r: Node3D = main.rig
	var side: Vector3 = r.global_transform.basis.x
	var back: Vector3 = r.global_transform.basis.z
	var p: Vector3 = r.global_position + side * 1.4 + back * 0.6   # neben dem Mover
	var q2: Vector2 = main.keep_out(Vector2(p.x, p.z), 0.35, true)
	return Vector3(q2.x, main.ground_y(q2.x, q2.y), q2.y)


func _ensure() -> void:
	if ok() and _scene == main.scene:
		return
	remove()
	var at := _spawn_at()
	yaw = main.rig.rotation.y if story() == null else yaw
	_bauen(at, yaw)
	haltung = "stehen"
	wasser = ""
	sitz = {}
	_scene = main.scene
	_anchor = null
	_eye_ok = false


func figur_wahl() -> Dictionary:
	"""the own figure (Etappe 2: main.ex_figur, erkunden_figur.gd) - always complete"""
	return EFigur.norm(main.get("ex_figur"))


func _bauen(at: Vector3, hd: float) -> void:
	var fd := figur_wahl()
	var a = ActorS.new()
	a.controlled = true
	a.look = EFigur.look(fd)
	a.player_color = EFigur.farbe(str(fd["jacke"]))
	a.name = "erkunden_person"
	a.water_ok = true
	main.add_child(a)
	a.setup(main, EFigur.art(fd), at, at + Vector3(-sin(hd), 0, -cos(hd)), 1.5)
	actor = a
	figur.a = a
	figur.zustand = "film"
	figur.setzen(at, hd)
	figur.geh_zu("boden")
	_sk = null
	if begleiter != null:
		begleiter.mw_anwenden(true)


func figur_setzen(d: Dictionary) -> void:
	"""a new look (the window «Figur gestalten», control command): saved, the figure rebuilt where it stands"""
	main.ex_figur = EFigur.norm(d)
	main._settings_dirty = true
	if not ok():
		return
	var p: Vector3 = figur.pos()
	var hd := float(actor.heading)
	var h_alt := haltung
	var sw := wasser
	var war_aktiv := active
	if haltung == "sitzen":
		_aufstehen("stehen")
	actor.queue_free()
	_bauen(p, hd)
	if sw == "schwimmen":
		figur.y = spiegel - SCHWIMM_TIEF
		actor.position.y = figur.y
		figur._p0 = actor.position
	wasser = sw
	haltung = h_alt if h_alt != "sitzen" else "stehen"
	actor.frozen = not war_aktiv


func remove() -> void:
	if begleiter != null:
		begleiter.hund_weg()
	if extras != null and extras.foto_an:
		extras.fotomodus(false)
	if sachen != null:
		sachen.lager_weg()
		if sachen.fernglas:
			sachen.feldstecher(false)
		sachen.menu(false)
	_abseil = {}
	if gestalten != null and gestalten.offen:
		gestalten.zeigen(false)
	if ok():
		actor.queue_free()
	actor = null
	if figur != null:
		figur.a = null
	active = false
	_anchor = null


func set_active(v: bool) -> void:
	if v:
		_ensure()
		if ok():
			actor.frozen = false
			if figur.zustand in ["film", "zurueck"]:
				figur.geh_zu("boden")
			_eye_yaw = float(actor.heading)
			_top_yaw = float(actor.heading)
			_eye_ok = false
			regie.hinter_figur()
			_view_alt = ""
	active = v
	cmd = Vector2.ZERO
	run = false
	_wunsch = {}
	if not v and ok():
		actor.ctl_move = Vector2.ZERO
		actor.frozen = true                                 # bleibt stehen, wo sie ist


func place(p: Vector3) -> void:
	if not ok():
		return
	var q: Vector2 = main.keep_out(Vector2(p.x, p.z), 0.35, true, true)
	if haltung == "sitzen":
		_aufstehen("stehen")
	figur.setzen(Vector3(q.x, 0, q.y))
	if figur.zustand != "boden":
		figur.geh_zu("boden")
	wasser = ""
	_anchor = null


func test_walk(v: Vector2, secs: float, r: bool) -> void:
	"""tests: v = (forward, turn right) along the figure's own heading (like the old person), secs long"""
	_test = {"v": v, "run": r, "until": _now() + secs}


func speed_now() -> float:
	return float(actor.cur_speed) if ok() else 0.0


func tick(_dt: float) -> void:
	"""(explore.gd calls it every frame; the work is in _process / spaet: before and after the actors)"""
	if ok() and _scene != main.scene:                       # another scene: new beside the mover
		_ensure()
		if active:
			set_active(true)


# ---- posture -----------------------------------------------------------------------------------------------------------
func wunsch(k: String) -> void:
	"""a key / button / control command: sprung | klettern | haltung | sitzen | liegen | ansicht"""
	_wunsch[k] = true


func ruhig() -> bool:
	"""binoculars or the photo mode: the picture alone (no stick, no edge buttons, no bar)"""
	return (sachen != null and sachen.fernglas) or (extras != null and extras.foto_an)


func touch_tipp(id: String) -> void:
	if id == "ansicht":
		ex.next_view()
	elif id == "rucksack":
		sachen.menu(not sachen.menu_offen())
	else:
		wunsch(id)


func haltung_weiter() -> void:
	"""C: stehen → geduckt → kriechen → stehen (sitting / lying: up to standing)"""
	if wasser == "schwimmen":
		return
	if haltung in ["sitzen", "liegen"]:
		_aufstehen("stehen")
		return
	set_haltung(HALTUNGEN[(HALTUNGEN.find(haltung) + 1) % HALTUNGEN.size()])


func set_haltung(h: String) -> void:
	if not h in POSTUR or not ok():
		return
	if wasser == "schwimmen" and h != "stehen":
		return                                              # swimming: no posture
	if h == haltung:
		return
	if haltung == "sitzen" and h != "sitzen":
		_aufstehen(h)
		return
	if h == "sitzen":
		_hinsetzen()
		return
	if h == "liegen" and wasser != "":
		main.start_info = T.t("Im Wasser kann man sich nicht hinlegen")
		return
	haltung = h


func _hinsetzen() -> void:
	if wasser != "":
		main.start_info = T.t("Im Wasser kann man sich nicht hinsetzen")
		return
	if figur.zustand != "boden":
		return
	var s: Dictionary = Welt.sitz(main, actor.global_position, float(actor.heading))
	sitz = s
	haltung = "sitzen"
	actor.cur_speed = 0.0
	actor.sit_seat = float(s["h"])
	actor.idle_kind = "sit"
	actor.idle_until = actor.now_s() + 1.0e6
	actor.ctl_sit = true
	if str(s["art"]) != "boden":
		var sp: Vector3 = s["p"]
		actor.position = Vector3(sp.x, actor.position.y, sp.z)
		actor.heading = float(s["yaw"])
		actor.rotation.y = actor.heading
		figur._p0 = actor.position


func _aufstehen(nach: String) -> void:
	if haltung == "sitzen":
		actor.ctl_sit = false
		actor.idle_until = 0.0
		actor.idle_kind = ""
		if str(sitz.get("art", "boden")) != "boden":        # off the bench: a step away from it
			var q: Vector2 = main.keep_out(Vector2(actor.position.x, actor.position.z), float(actor.radius), true, true)
			actor.position.x = q.x
			actor.position.z = q.y
			figur._p0 = actor.position
		sitz = {}
	haltung = nach if nach in POSTUR and nach != "sitzen" else "stehen"


func _haltung_tick(ein: Dictionary) -> void:
	var mv: Vector2 = ein.get("mv", Vector2.ZERO)
	if bool(_wunsch.get("haltung", false)):
		haltung_weiter()
	if bool(_wunsch.get("sitzen", false)):
		if haltung == "sitzen":
			_aufstehen("stehen")
		else:
			set_haltung("sitzen")
	if bool(_wunsch.get("liegen", false)):
		set_haltung("stehen" if haltung == "liegen" else "liegen")
	if haltung == "sitzen" and mv.length() > 0.3:
		_aufstehen("stehen")                                # walking off: up from the seat
	elif haltung == "liegen" and mv.length() > 0.3:
		haltung = "kriechen"                                # lying still, then moving: crawling on
	if wasser == "schwimmen" and haltung != "stehen":
		if haltung == "sitzen":
			_aufstehen("stehen")
		haltung = "stehen"
	# what actor.gd does with it
	actor.ctl_posture = 2 if wasser == "schwimmen" else int(POSTUR[haltung])
	actor.gear_speed = (SCHWIMM_V / float(ActorS.PLAYER_SPEED[2])) if wasser == "schwimmen" else (WATEN_K if wasser == "waten" else 1.0)
	actor.gear_norun = wasser != "" or (sachen != null and not sachen.darf_rennen())
	if sachen != null:
		actor.gear_speed *= sachen.tempo_faktor()            # Etappe 3: strength, snow without ice axe, hurt
	actor.run_top = renn_tempo(main)
	actor.frozen = haltung in ["sitzen", "liegen"]


func _skelett() -> Skeleton3D:
	"""the visible body of the figure (figur_mensch.gd / figur_paket.gd: a skeleton) - null = built from shapes"""
	if not ok():
		return null
	if _sk != null and is_instance_valid(_sk) and _sk.is_inside_tree() and _sk_von == actor:
		return _sk
	_sk = null
	_sk_von = actor
	for s in actor.find_children("*", "Skeleton3D", true, false):
		if (s as Skeleton3D).is_visible_in_tree():
			_sk = s
			_sk_kopf = _sk.find_bone("Head")
			if _sk_kopf < 0:
				for i in _sk.get_bone_count():
					if _sk.get_bone_name(i).to_lower().contains("head"):
						_sk_kopf = i
						break
			break
	return _sk


func hoehe() -> float:
	"""how high the figure is now (m above its feet): the highest bone of its visible skeleton + the top of the head (the
	joints of actor.gd without a skeleton) - crouching, sitting and crawling make it lower; MoveEye sees the same body"""
	if not ok():
		return 0.0
	var sk := _skelett()
	var top := -INF
	if sk != null:
		for i in sk.get_bone_count():
			top = maxf(top, (sk.global_transform * sk.get_bone_global_pose(i).origin).y)
		top += 0.18                                          # the bones end at the base of the head
	else:
		var hd = actor.get("head")
		if hd != null and is_instance_valid(hd):
			top = (hd as Node3D).global_position.y + 0.2
	if top == -INF:
		return 0.0
	return top - float(figur.y)


# ---- every frame, before the actors ----------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if not ok():
		return
	uhr += dt
	if not active or not ex.on:
		actor.frozen = true
		actor.ctl_move = Vector2.ZERO
		return
	var ein := _eingabe(dt)
	if (gestalten != null and gestalten.offen) or (sachen != null and sachen.fernglas) or not _abseil.is_empty() \
			or (extras != null and extras.foto_an):
		ein["mv"] = Vector2.ZERO                             # designing / binoculars / rappelling: the figure stands
		ein["sprung"] = false
		_wunsch = {}
	_haltung_tick(ein)
	if haltung in ["sitzen", "liegen"]:
		ein["mv"] = Vector2.ZERO
		ein["sprung"] = false
	if bool(_wunsch.get("klettern", false)) or bool(ein.get("sprung", false)):
		if wasser == "" and figur.zustand == "boden":
			if haltung != "stehen":
				if bool(ein.get("sprung", false)):
					haltung = "stehen"                      # first up, then a jump
				ein["sprung"] = false
			else:
				var hmax: float = 3.5 if (sachen != null and sachen.hat("pickel") and sachen.auf_schnee()) else Welt.KANTE_MAX
				var k: Dictionary = Welt.kante(main, figur.pos(), float(actor.heading), hmax)
				if not k.is_empty():
					figur._hochziehen(k["ziel"], k["kante"])   # over the edge (the mantle of kit_figur.gd)
					ein["sprung"] = false
				elif bool(_wunsch.get("klettern", false)) and not bool(ein.get("sprung", false)):
					var ab: Dictionary = sachen.abgrund() if sachen != null else {}
					if not ab.is_empty() and sachen.hat("seil"):
						abseilen()                              # Etappe 3: with the rope down a drop
					elif not ab.is_empty():
						sachen.sag(T.t("Zu steil – mit einem Seil kannst du dich hier abseilen"))
					else:
						main.start_info = T.t("Hier gibt es nichts zum Hochklettern")
		else:
			ein["sprung"] = false                              # swimming / wading: no jumps (no diving)
	_wunsch = {}
	_ein = ein
	if not _abseil.is_empty():
		actor.puppet = true
		return
	if wasser == "schwimmen":
		actor.puppet = false
		actor.frozen = false
		actor.ctl_move = ein.get("mv", Vector2.ZERO)
		actor.ctl_run = false
	else:
		figur.vor(dt, ein)
		if haltung in ["sitzen", "liegen"]:
			actor.ctl_move = Vector2.ZERO
	yaw = float(actor.heading)


func _view_yaw() -> float:
	match str(ex.view):
		"driver":
			return _eye_yaw
		"top":
			return _top_yaw
	return float(regie.yaw)


func _eingabe(dt: float) -> Dictionary:
	"""rover_pad.gd (W A S D, arrows, green stick, controller) → one wish; mv in WORLD x/z, relative to the view"""
	var c := cmd
	var r := run
	var tst := false
	if not _test.is_empty():
		if _now() < float(_test["until"]):
			c = _test["v"]
			r = bool(_test["run"])
			tst = true
		else:
			_test = {}
	c = c.limit_length(1.0)
	var mv := Vector2.ZERO
	if tst:                                                  # tests (pwalk): along the own heading, turning like before
		yaw = wrapf(float(actor.heading) - c.y * TURN * dt, -PI, PI)
		if absf(c.x) < 0.08:
			actor.heading = rotate_toward(float(actor.heading), yaw, 6.0 * dt)
			actor.rotation.y = actor.heading
		mv = Vector2(-sin(yaw), -cos(yaw)) * c.x
	elif str(ex.view) == "driver":                           # own eyes: A / D turn the view, W / S along it
		_eye_yaw = wrapf(_eye_yaw - c.y * TURN * dt, -PI, PI)
		mv = Vector2(-sin(_eye_yaw), -cos(_eye_yaw)) * c.x * (0.6 if c.x < 0.0 else 1.0)
	else:
		var vy := _view_yaw()
		var fw := Vector3(-sin(vy), 0, -cos(vy))
		var rt := fw.cross(Vector3.UP).normalized()
		var m3 := fw * c.x + rt * c.y
		mv = Vector2(m3.x, m3.z)
	var sp := bool(_wunsch.get("sprung", false))
	return {"mv": mv.limit_length(1.0), "run": r and c.length() > 0.1, "sprung": sp, "sprung_h": false, "aktion": false,
			"vor": c.x, "quer": c.y}


# ---- every frame, after the actors (kit_spaet.gd) --------------------------------------------------------------------------
func spaet(dt: float, real_dt: float) -> void:
	if not ok() or not active or not ex.on:
		return
	if not _abseil.is_empty():
		_abseil_tick(dt)
		_bounds()
		_kamera(dt, real_dt)
		touch.tick()
		return
	var zs := str(figur.zustand)
	if zs == "luft":                                         # (on the ground actor.gd already steps 0.2 m with keep_out)
		_waende(figur._p0)
		_y_hoch = maxf(_y_hoch, figur.y)
	elif _y_hoch > -INF:
		if sachen != null:
			sachen.gelandet(_y_hoch - figur.y)                # Etappe 3: a hard landing («Echt»)
		_y_hoch = -INF
	var w: Dictionary = Welt.wasser(main, actor.position)
	var art: String = Welt.art_fuer_tiefe(float(w.get("tiefe", 0.0)), str(w.get("art", "")) == "bach")
	if art == "schwimmen" and (zs == "boden" or (zs == "luft" and figur.y <= float(w["spiegel"]) - SCHWIMM_TIEF + 0.05)):
		if wasser != "schwimmen":
			ton("platsch")
			figur.nass += 1
			if haltung == "sitzen":
				_aufstehen("stehen")
			haltung = "stehen"
		wasser = "schwimmen"
		spiegel = float(w["spiegel"])
		if zs == "luft":
			figur.geh_zu("boden")
		figur.y = spiegel - SCHWIMM_TIEF
		figur.vy = 0.0
		actor.position.y = figur.y
		figur._p0 = actor.position
	else:
		if wasser == "schwimmen":                            # out of the deep water: the feet on the bed / the bank
			figur.y = main.ground_y(actor.position.x, actor.position.z)
			figur._p0 = Vector3(figur._p0.x, figur.y, figur._p0.z)
		wasser = art if art != "schwimmen" else ""
		figur.nach(dt, _ein)
	_bounds()
	_kamera(dt, real_dt)
	touch.tick()


func abseilen() -> bool:
	"""Etappe 3: with the rope down the drop ahead (1–40 m) - to the edge, then slowly down, at the bottom on the ground"""
	if sachen == null or not sachen.hat("seil") or figur.zustand != "boden" or wasser != "":
		return false
	var ab: Dictionary = sachen.abgrund()
	if ab.is_empty():
		return false
	if haltung != "stehen":
		if haltung == "sitzen":
			_aufstehen("stehen")
		haltung = "stehen"
	_abseil = {"von": figur.pos(), "kante": ab["kante"], "nach": ab["nach"], "t": 0.0, "dauer": 1.0 + float(ab["h"]) / 1.6}
	actor.cur_speed = 0.0
	sachen.sag(T.t("Abseilen …"), 1.5)
	return true


func _abseil_tick(dt: float) -> void:
	var A := _abseil
	A["t"] = float(A["t"]) + dt
	var f := clampf(float(A["t"]) / float(A["dauer"]), 0.0, 1.0)
	var von: Vector3 = A["von"]
	var kante: Vector3 = A["kante"]
	var nach: Vector3 = A["nach"]
	var p: Vector3
	if f < 0.15:                                              # to the edge, turn round (face the wall)
		p = von.lerp(kante, smoothstep(0.0, 1.0, f / 0.15))
	else:                                                     # down along the wall, a little away from it
		var u := smoothstep(0.0, 1.0, (f - 0.15) / 0.85)
		p = Vector3(lerpf(kante.x, nach.x, u), lerpf(kante.y, nach.y, u), lerpf(kante.z, nach.z, u))
	var to := nach - von
	actor.heading = atan2(to.x, to.z)                         # back to the drop
	actor.rotation.y = actor.heading
	actor.position = p
	figur.y = p.y
	figur._p0 = p
	actor.cur_speed = 0.0
	actor.aktion("haengen" if f > 0.15 else "klettern", 0.3)
	if f >= 1.0:
		_abseil = {}
		actor.puppet = false
		actor.heading = atan2(-to.x, -to.z)
		actor.rotation.y = actor.heading
		figur.setzen(nach, actor.heading)
		figur.geh_zu("boden")
		sachen.sag(T.t("Unten!"), 1.5)


func _waende(von: Vector3) -> void:
	"""fast or in the air: from where it was to where it is now in steps of 0.2 m with main.keep_out - never through a wall"""
	var a := Vector2(von.x, von.z)
	var b := Vector2(actor.position.x, actor.position.z)
	var d := b - a
	var n := int(ceil(d.length() / 0.2))
	if n <= 1:
		return
	var q := a
	for i in range(n):
		q = main.keep_out(q + d / float(n), float(actor.radius), true, true)
	actor.position.x = q.x
	actor.position.z = q.y


func _setz_xz(w: Vector3) -> void:
	var g: float = main.ground_y(w.x, w.z)
	actor.position = Vector3(w.x, g if wasser != "schwimmen" else figur.y, w.z)
	if wasser != "schwimmen":
		figur.y = g
	figur._p0 = actor.position


func _bounds() -> void:
	var ab = story()
	var p: Vector3 = actor.position
	if ab != null:                                          # mit der Gruppe mitgehen, höchstens LEASH weg
		var b = ab.bt()
		var an := _anchor_of(ab)
		var v3: Vector3 = b.V(p)
		var q := Vector2(v3.x, v3.z)
		var q0 := q
		if _anchor is Vector2 and an.distance_to(_anchor) > 0.001:
			q += an - (_anchor as Vector2)
		var off := q - an
		if off.length() > LEASH:
			off = off.normalized() * LEASH
			if _now() - _far_t > 8.0:
				_far_t = _now()
				main.start_info = T.t("Nicht weiter weg von der Gruppe (%d m)") % int(LEASH)
		q = an + off
		q = Vector2(clampf(q.x, Bt.LO + 30.0, -Bt.LO - 30.0), clampf(q.y, Bt.LO + 30.0, -Bt.LO - 30.0))
		_anchor = an
		if q.distance_to(q0) > 0.001:
			_setz_xz(b.WG(q.x, q.y, 0.0))
		return
	_anchor = null
	if main.scene != "bergtal":
		var cx := clampf(p.x, -BOUND, BOUND)
		var cz := clampf(p.z, -BOUND, BOUND)
		if cx != p.x or cz != p.z:
			_setz_xz(Vector3(cx, 0, cz))


# ---- the views ---------------------------------------------------------------------------------------------------------------
func _kamera(dt: float, real_dt: float) -> void:
	var v := str(ex.view)
	if main.spectate:
		return                                               # the spectator moves the view (explore.gd)
	# mouse / R1 + stick (explore.gd orbit, pitch) and the wheel (dist): as changes
	var d_or: float = float(ex.orbit) - _orbit_alt
	var d_pi: float = float(ex.pitch) - _pitch_alt
	var d_di: float = float(ex.dist) - _dist_alt
	ex.orbit = 0.0
	_orbit_alt = 0.0
	_pitch_alt = float(ex.pitch)
	_dist_alt = float(ex.dist)
	if v != _view_alt:
		_view_alt = v
		_eye_yaw = float(actor.heading)
		_top_yaw = float(regie.yaw)
		if v == "chase":
			regie.hinter_figur()
		_eye_ok = false
	var cam: Camera3D = main.view_cam
	if gestalten != null and gestalten.offen:
		_portrait(cam, dt)
		return
	if extras != null and extras.foto_an:                   # Etappe 4: the photo mode - the camera free round the figure
		extras.kamera(cam, dt, d_or, d_pi, d_di)
		return
	if sachen != null and sachen.fernglas:                  # Etappe 3: through the binoculars (mouse / R1 look, wheel zoom)
		_eye_yaw = wrapf(_eye_yaw + d_or, -PI, PI)
		if d_di != 0.0:
			sachen.set_zoom(sachen.zoom - d_di * 0.6)
		main.view_mode = 0
		sachen.kamera(cam, dt)
		return
	match v:
		"driver":
			_eye_yaw = wrapf(_eye_yaw + d_or, -PI, PI)
			var fw := Vector3(-sin(_eye_yaw), 0, -cos(_eye_yaw))
			var want := augen_punkt() + fw * 0.12
			_eye_p = want if not _eye_ok else _eye_p.lerp(want, clampf(dt * 14.0, 0.0, 1.0))
			_eye_ok = true
			main.view_mode = 0
			cam.fov = 70.0
			cam.near = 0.05
			cam.global_position = _eye_p
			cam.look_at(_eye_p + fw * 10.0 + Vector3(0, -1.2 + (0.38 - float(ex.pitch)) * 4.0, 0), Vector3.UP)
		"top":
			_top_yaw = wrapf(_top_yaw + d_or, -PI, PI)
			var tp: Vector3 = figur.pos() + Vector3(0, 0.8, 0)
			var hgt := float(ex.dist) * 2.6 + 6.0
			var want2: Vector3 = tp + Vector3(0.01, hgt, 0.01)
			main.view_mode = 0
			cam.fov = 70.0
			cam.global_position = cam.global_position.lerp(want2, clampf(dt * (3.0 + speed_now() * 0.8), 0.0, 1.0)) if _eye_ok else want2
			_eye_ok = true
			cam.look_at(tp, Vector3.FORWARD.rotated(Vector3.UP, _top_yaw))
		_:
			var look := Vector2(-d_or, d_pi)
			regie.tick(dt, real_dt, {"look": look, "zoom": d_di * 0.4})


var _por := {}


func portrait_start() -> void:
	"""«Figur gestalten»: the figure turns to the view, the camera in front of it (a live preview in the world)"""
	if not ok():
		return
	var cam: Camera3D = main.view_cam
	if _por.is_empty():
		var to := cam.global_position - actor.global_position
		var hd := atan2(-to.x, -to.z) + PI                       # facing the camera
		_por = {"hd": hd}
		actor.heading = hd
		actor.rotation.y = hd
	_eye_ok = false


func _portrait(cam: Camera3D, dt: float) -> void:
	var hd := float(_por.get("hd", actor.heading))
	var fw := Vector3(-sin(hd), 0, -cos(hd))                   # where the figure looks = towards the camera
	var rt := fw.cross(Vector3.UP).normalized()
	var s: Vector2 = get_viewport().get_visible_rect().size
	var hoch := s.y > s.x
	var hh: float = clampf(hoehe(), 0.5, 2.0)
	var mitte: Vector3 = figur.pos() + Vector3(0, hh * 0.55, 0)
	var dist := hh * (3.4 if hoch else 1.9) + 0.8
	var want := mitte + fw * dist + Vector3(0, 0.25, 0)
	# the figure where the window is not: left of the window on the PC, above it on the phone (the camera looks along -fw:
	# its right is -rt, so looking a little to -rt puts the figure left in the picture)
	var blick := mitte + (-rt * dist * 0.3 if not hoch else Vector3(0, -dist * 0.17, 0))
	main.view_mode = 0
	cam.fov = 50.0
	var tr := Transform3D(Basis.IDENTITY, want).looking_at(blick, Vector3.UP)
	cam.global_transform = tr if not _eye_ok else cam.global_transform.interpolate_with(tr, clampf(dt * 6.0, 0.0, 1.0))
	_eye_ok = true
	actor.heading = hd
	actor.rotation.y = hd


func portrait_ende() -> void:
	_por = {}
	_eye_ok = false
	regie.hinter_figur()


func decke_bei(_w: Vector3, _figur_y: float) -> float:
	"""kit_regie asks the adventure for a ceiling (Kapitel 1: the hut) - free exploring: open sky everywhere"""
	return INF


func raum_klemmen(w: Vector3) -> Vector3:
	"""kit_regie: keep the camera inside a room of the adventure - free exploring has none (walls: main.line_blocker)"""
	return w


func augen_punkt() -> Vector3:
	"""where the eyes of the figure are now (world): the head bone of the visible body (else the head of actor.gd) + a
	little up - follows the posture (crouching, sitting, crawling, swimming)"""
	var sk := _skelett()
	if sk != null and _sk_kopf >= 0:
		return sk.global_transform * sk.get_bone_global_pose(_sk_kopf).origin + Vector3(0, 0.1, 0)
	var hd = actor.get("head")
	if hd != null and is_instance_valid(hd):
		return (hd as Node3D).global_position + Vector3(0, 0.1, 0)
	return Vector3(actor.position.x, figur.y + float(AUGE.get(haltung, EYE)), actor.position.z)


# ---- the frame of kit_figur.gd / kit_regie.gd (no parcours, no film, no Maggie) --------------------------------------------
func ton(nm: String) -> void:
	var k = main.get("klang")
	if k != null and k.has_method("kit_ton"):
		k.kit_ton(nm)


func musik(_z: String) -> void:
	pass


func sag(text: String, _wer := "", _d := 0.0) -> void:
	main.start_info = text


func tx(s: String) -> String:
	return T.t(s)


func wasser_fx(_p: Vector3) -> void:
	pass


func zurueck_zum_checkpoint() -> void:
	"""nobody dies (kit_figur.gd zurueck): here simply on the ground where it is"""
	if ok():
		figur.setzen(figur.pos())
		figur.geh_zu("boden")


func aktion_fertig(_id: String) -> void:
	pass


func fund(_id: String) -> void:
	pass


func karte_start(_d: Dictionary) -> void:
	pass


func ir_umschalten() -> void:
	pass


func maggie_heben(_d: Dictionary) -> void:
	pass


func zeitlupe(f: float, s: float) -> void:
	regie.zeitlupe(f, s)


func tal_dir_welt(v: Vector2) -> Vector2:
	return v


func hund_pos() -> Vector3:
	return figur.pos()


func hund_heading() -> float:
	return float(actor.heading) if ok() else 0.0


func hund_tempo() -> float:
	return 0.0


func ziel_welt():
	return null


func state() -> Dictionary:
	var o := {"on": active, "why_not": why_not(main), "there": ok()}
	if o["there"]:
		var p: Vector3 = actor.global_position
		o["x"] = snappedf(p.x, 0.01)
		o["y"] = snappedf(figur.y, 0.01)
		o["z"] = snappedf(p.z, 0.01)
		o["speed"] = snappedf(speed_now(), 0.01)
		o["heading"] = snappedf(float(actor.heading), 0.001)
		o["haltung"] = haltung
		o["wasser"] = wasser
		o["zustand"] = str(figur.zustand)
		o["hoehe"] = snappedf(hoehe(), 0.01)
		o["sitz"] = str(sitz.get("art", "")) if haltung == "sitzen" else ""
		o["run_top"] = snappedf(renn_tempo(main), 0.01)
		o["figur"] = figur_wahl()
		o["kind_figur"] = str(actor.get("variant")) == "child"
		var vq = valley_pos()
		if vq is Vector2:
			o["tal"] = [snappedf(vq.x, 0.1), snappedf(vq.y, 0.1)]
	o["story"] = story() != null
	o["schnell"] = schnell_an(main)
	o["ptempo"] = float(main.get("ex_ptempo")) if main.get("ex_ptempo") != null else 0.0
	o["touch"] = touch.info() if touch != null else {}
	o["begleiter"] = begleiter.info() if begleiter != null else {}
	o["sachen"] = sachen.info() if sachen != null and ok() else {}
	o["abseilen"] = not _abseil.is_empty()
	o["extras"] = extras.info() if extras != null else {}
	o["gestalten"] = gestalten.info() if gestalten != null else {}
	return o
