extends Node
## Paket «Statisten (Hintergrund-Figuren)» (Zweig real-statisten, 31.10.2026): die Leute im Hintergrund ohne Story-Rolle –
## Besucher, Wanderer, Ferienpark-Gäste, Dorfleute – sollen sich glaubwürdig verhalten. Erweitert die bestehenden Systeme
## (main.spawn / _life, menschen.gd, simreal.leash, bergtal.gd Wanderer, Dev.alle_orte), keine zweite Figuren-Technik.
##
##  1 Auf den Spieler reagieren (Spielfiguren von game.gd / maggie_story.gd, beim «Erkunden» der Rover): kurz hinschauen und
##    grüssen («Grüezi», je nach Sprache T.t), auf schmalen Wegen nach rechts ausweichen und kurz warten, stehen bleiben,
##    wenn der Spieler rennt. Selten (höchstens alle 90 s) ein Satz zur Gegend – nie eine Rätsel-Lösung.
##  2 Tagesablauf: ein Statist hat 1–3 Ziele (Bank, Brunnen, Hütte, Parkplatz, Aussichtspunkt, WC, Platz vor MoveEye), die in
##    seiner Gehrichtung liegen (kein Hin und Her), verweilt dort und geht weiter. Am Abend: übrige Ziele weg, heim (Ausgang).
##  3 Kleine Tätigkeiten am Ziel: Handy, Foto machen, Schuh binden, sitzen und trinken, Rucksack absetzen; Hund an der Leine
##    (simreal.leash). Posen in actor.gd (idle «photo», «drink», «sitdrink», «tie»; «phone», «look», «talk», «bend» gab es).
##  4 Gruppen: Paare und Familien (menschen.gd «m_familie») gehen zusammen, bleiben gemeinsam stehen und reden mit Gesten.
##  5 Wetter und Zeit: Regen -> Schirm (menschen.gd), schneller, kürzer verweilen, nicht sitzen; abends weniger, nachts kaum.
##  6 Nicht stören: Abstand zu Rätselstellen, Gefahren, Toren, Vignetten (Dev.alle_orte «vignette» / «erlebnis», Abenteuer-
##    Kapitel, maggie_story tor / Rastplätze / sperren(), Ferienpark-Aufgaben, Spielziel). Keine in Zwischenszenen (sie
##    verschwinden), bei Maggie und im Hospiz keine oder ganz wenige. Tests (Testlauf, Prüfstand, Nacht-Testlauf …): aus,
##    nichts wird verändert (die Zahlen bleiben vergleichbar).
##  7 Keine Fehler: Ausweichen vor anderen Figuren (steer(): sanfte Abstossung, rechts vorbei, von actor.gd beim Lenken
##    gefragt), Überlappung wird aufgelöst, Wände / Zäune wie bisher (main.avoid / keep_out); Steckenbleiben: nach 6 s
##    Punkt überspringen / Umweg, nach 15 s direkt zum Ausgang, nach 35 s weg (nur ausserhalb des Kamerabilds).
##  8 Menge pro Modus: wenig / normal / belebt (Spielmodi zusätzlich «aus»): Besuch → Von selbst («frei» ohne Spiel),
##    die Spielmodi im selben Teil (Experte) und im Bergtal-Abenteuer in seinen Einstellungen.
## Leistung: Logik 4 × pro Sekunde (Lite 2 ×), ferne Statisten (> 45 m) nur jedes 4. Mal; steer() nutzt ein Raster.
## Lite: _lite() = Quality.lite() (quality.gd, die zentrale Abfrage): halb so viele, nur 1–2 Ziele, keine Familien mit 3 Kindern.
## Steuerung: /control {"action": "statisten", "do": "info" | "set" (mode, value) | "spawn" (n, group) | "clear"}.

const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")
const Dev = preload("res://scripts/devtool.gd")
const Figur = preload("res://scripts/figur.gd")
const AbD = preload("res://scripts/bergtal_abenteuer_daten.gd")

var main
const FILE := "user://statisten.json"
const MODES := ["frei", "spiel", "abenteuer", "aufgabe", "maggie"]
const LEVELS := ["aus", "wenig", "normal", "belebt"]
var menge := {"frei": "normal", "spiel": "aus", "abenteuer": "wenig", "aufgabe": "wenig", "maggie": "aus"}
# how many statists my own spawner keeps (before world / time / Lite factors); «frei» + «normal» = only the old visitors
const COUNT := {"aus": 0, "wenig": 2, "normal": 4, "belebt": 8}
const WORLD_F := {"bergtal": 0.5, "ferienpark": 1.5, "festival": 1.5, "camping": 1.0}
const GOAL_R := {"camping": 35.0, "bergtal": 160.0, "ferienpark": 120.0, "festival": 70.0}
const SPAWN_R := {"camping": 30.0, "bergtal": 70.0, "ferienpark": 55.0, "festival": 45.0}
const TEST_BUSY := ["Testlauf", "Prüfstand", "Nacht-Testlauf", "Trainingsbilder", "Blinde Flecken", "Fehlalarm nachstellen",
		"Verfolgungs-Parcours", "Einbruch-Ablauf", "Wiedergabe", "Spiel (Wächter)"]

var S := {}                     # instance id -> state of a statist (managed: spawned here or adopted)
var seen := {}                  # instance id -> true: every visitor is looked at once (adopt or not)
var goals: Array = []           # [{p, type, name}] of the scene that is loaded
var zones: Array = []           # [[centre Vector3, radius]] - keep away (riddles, dangers, gates, vignettes, tasks)
var zones_static: Array = []
var _scene_key := ""
var _tick := 0.0
var _n := 0
var _zone_t := 0.0
var _spawn_t := 0.0
var _tip_t := -100.0
var _rebuild_t := 0.0
var _mode := "frei"
var _was_cut := false
var _grid := {}                 # Vector2i -> [actor] (persons, for steer())
var _players: Array = []        # [{n, p, v}]
var _pl_last := {}
var stats := {"spawned": 0, "adopted": 0, "greet": 0, "tips": 0, "dodge": 0, "stop_run": 0, "stuck_skip": 0, "stuck_exit": 0,
		"stuck_gone": 0, "home": 0, "cut_hidden": 0, "zone_out": 0, "acts": {}}


func _lite() -> bool:
	return Quality.lite()


func now_s() -> float:
	return Time.get_ticks_msec() / 1000.0                  # the clock of the visitors (actor.now_s)


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY and typeof(d.get("menge", null)) == TYPE_DICTIONARY:
		for k in MODES:
			var v := str(d["menge"].get(k, menge[k]))
			if v in LEVELS:
				menge[k] = v


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"menge": menge}))


func set_menge(mode: String, v: String) -> void:
	if mode in MODES and v in LEVELS:
		menge[mode] = v
		save()


# ---- controls (main._register_controls, next to menschen.add_controls) --------------------------------------------------
func add_controls() -> void:
	var m = main
	var L3 := [["wenig", T.t("wenig")], ["normal", T.t("normal")], ["belebt", T.t("belebt")]]
	var L4 := [["aus", T.t("keine")], ["wenig", T.t("wenig")], ["normal", T.t("normal")], ["belebt", T.t("belebt")]]
	m.add_control("select", "st_frei", "Statisten (Leute im Hintergrund): wie viele, mit Zielen, Tätigkeiten und Gruppen",
			func(): return menge["frei"], func(v): set_menge("frei", str(v)), "Besuch", {"sub": "Von selbst", "options": L3})
	m.add_control("select", "st_spiel", "Statisten in Spielrunden", func(): return menge["spiel"], func(v): set_menge("spiel", str(v)),
			"Besuch", {"sub": "Von selbst", "options": L4, "expert": true})
	m.add_control("select", "st_abenteuer", "Statisten im Bergtal-Abenteuer", func(): return menge["abenteuer"], func(v): set_menge("abenteuer", str(v)),
			"Besuch", {"sub": "Von selbst", "options": L4, "expert": true})
	m.add_control("select", "st_aufgabe", "Statisten bei den Ferienpark-Aufgaben", func(): return menge["aufgabe"], func(v): set_menge("aufgabe", str(v)),
			"Besuch", {"sub": "Von selbst", "options": L4, "expert": true})
	m.add_control("select", "st_maggie", "Statisten bei Maggie und im Hospiz", func(): return menge["maggie"], func(v): set_menge("maggie", str(v)),
			"Besuch", {"sub": "Von selbst", "options": [["aus", T.t("keine")], ["wenig", T.t("ganz wenige")]], "expert": true})


func info() -> Dictionary:
	var people := []
	for id in S:
		var e: Dictionary = S[id]
		var v = e["v"]
		if not is_instance_valid(v):
			continue
		people.append({"id": int(id), "own": bool(e.get("own", false)), "x": snappedf(v.position.x, 0.1), "z": snappedf(v.position.z, 0.1),
				"goals": int(e.get("goals_left", 0)), "act": str(e.get("act", "")), "idle": v.idle_kind if v.now_s() < v.idle_until else "",
				"wait": snappedf(clampf(v.wait_until - v.now_s(), 0.0, 999.0), 0.1), "speed": snappedf(v.cur_speed, 0.01),
				"group": int(e.get("group", 0)), "home": bool(e.get("home", false)), "visible": v.visible})
	return {"ok": true, "mode": _mode, "menge": menge, "want": want_count(), "own": own_count(), "managed": S.size(), "goals": goals.size(),
			"goal_list": goals.map(func(g): return [g["type"], str(g["name"]), snappedf(g["p"].x, 0.1), snappedf(g["p"].z, 0.1)]),
			"zones": zones.size(), "players": _players.size(), "lite": _lite(), "fps": Engine.get_frames_per_second(), "visitors": main.visitors.get_child_count(),
			"stats": stats, "people": people}


func control(d: Dictionary) -> Dictionary:
	var op := str(d.get("do", "info"))
	if op == "set":
		set_menge(str(d.get("mode", "frei")), str(d.get("value", "normal")))
	elif op == "spawn":
		var made := 0
		for i in range(int(d.get("n", 1))):
			if spawn_one(str(d.get("group", ""))) != null:
				made += 1
		return {"ok": made > 0, "made": made, "info": info()}
	elif op == "clear":
		for id in S.keys():
			var v = S[id]["v"]
			if is_instance_valid(v) and bool(S[id].get("own", false)):
				_remove(v)
	elif op == "goals":
		_scene_key = ""
	return info()


# ---- which mode has the world ---------------------------------------------------------------------------------------------
func mode() -> String:
	"""frei | spiel | abenteuer | aufgabe | maggie | cut (a cut scene) | test (tests: hands off)"""
	if main == null:
		return "test"
	var mg = main.get("maggie")
	if mg != null and is_instance_valid(mg) and bool(mg.running):
		return "cut" if str(mg.phase) in ["reise", "intro", "intro_dig", "film", "finale_cut", "abspann"] else "maggie"
	var hr = main.get("horror")
	if hr != null and is_instance_valid(hr) and bool(hr.running):
		return "cut" if str(hr.phase) in ["intro", "ending", "clips"] else "maggie"
	var ab = main.get("abenteuer")
	if ab != null and is_instance_valid(ab) and not ab.R.is_empty() and bool(ab.R.get("intro", false)):
		return "cut"                                             # A6: Zwischenszene (Kamerafahrt)
	var b: String = main.busy_with()
	if b == "":
		return "frei"
	if b in TEST_BUSY:
		return "test"
	if b == "Bergtal-Abenteuer":
		return "abenteuer"
	if b == "Ferienpark-Aufgabe":
		return "aufgabe"
	if b == "Spielrunde":
		return "spiel"
	if b in ["Maggie-Geschichte", "Horror-Modus"]:
		return "maggie"
	return "test"


func want_count() -> int:
	"""how many statists my own spawner keeps now (the old visitors of «frei» come on top)"""
	var m := _mode
	if m in ["cut", "test"]:
		return 0
	var lv: String = menge.get(m, "normal")
	if m == "frei":
		if lv != "belebt" or not main.auto_visitors:
			return 0                                             # «frei»: normal = the visitors as before, wenig = fewer of them
	if m == "maggie":
		return 1 if lv != "aus" else 0                           # Maggie, Hospiz: none or very few
	var n: float = float(COUNT.get(lv, 0)) * float(WORLD_F.get(_world(), 1.0))
	var h: float = main.hour()
	if h >= 22.5 or h < 6.0:
		n *= 0.12                                                # night: hardly anybody
	elif h >= 19.5 or h < 7.5 or main.is_dark():
		n *= 0.45
	if main.weather == "rain":
		n *= 0.6
	if _lite():
		n *= 0.5
	return int(round(n)) if n >= 0.6 else 0


func accept(kind: String) -> bool:
	"""main._life: «frei» with «wenig» - only about half of the people come (animals, cars as before)"""
	if _mode != "frei" or menge["frei"] != "wenig":
		return true
	if not kind in ["person", "child", "elderly", "couple", "dogwalk", "bench", "m_spazieren", "m_familie", "m_gespraech", "m_sitzen", "jogger", "stroller", "cyclist"]:
		return true
	return randf() < 0.45


func own_count() -> int:
	var n := 0
	for id in S:
		if bool(S[id].get("auto", false)) and int(S[id].get("group", 0)) <= 0 and is_instance_valid(S[id]["v"]):
			n += 1
	return n


# ---- the world: goals and places to keep away from -------------------------------------------------------------------------
func _world() -> String:
	if main.mehr != null and main.mehr.get("dev") != null:
		return str(main.mehr.dev.loaded_world())
	return str(main.scene)


func _dev():
	return main.mehr.dev if main.mehr != null and main.mehr.get("dev") != null else null


func _walkable(p: Vector3) -> bool:
	var d: Dictionary = main.scenes.data if main.scenes != null else {}
	var bt = d.get("bergtal", null)
	if bt != null and is_instance_valid(bt) and is_instance_valid(bt.tal):
		var q: Vector3 = bt.V(p)
		return bt.zone(q.x, q.z) != "lake" and bt.slope_deg(q.x, q.z, 2.0) < 28.0
	var fp = d.get("ferienpark", null)
	if fp != null and is_instance_valid(fp) and is_instance_valid(fp.park):
		var q2: Vector3 = fp.inv * p
		return fp.H(q2.x, q2.z) >= 0.8                           # (ferienpark_leben._grill_place: below = the lake shore)
	return true


func _goal_type(name: String, kind: String) -> String:
	var n := name.to_lower()
	if kind == "aussicht" or n.contains("aussicht") or n.contains("seeblick") or n.contains("steg") or n.contains("brücke"):
		return "view"
	if n.contains("bank") or n.contains("rast") or n.contains("picknick"):
		return "bench"
	if n.contains("brunnen"):
		return "fountain"
	if n.contains("parkplatz") or n.contains("haltestelle") or n.contains("postauto"):
		return "parking"
	if n.contains("hütte") or n.contains("kiosk") or n.contains("restaurant") or n.contains("laden") or n.contains("bäckerei") or n.contains("stall") or n.contains("beizli") or n.contains("rezeption"):
		return "hut"
	if n.contains("sanitär") or n.contains("wc"):
		return "wc"
	return "place"


func _rebuild() -> void:
	"""the goals of the scene that is loaded: named places of Dev.alle_orte near MoveEye, the benches and the WC of the
	scene, three spots in front of MoveEye; vignettes / Erlebniswelt places become zones to keep away from"""
	goals.clear()
	zones_static.clear()
	var dv = _dev()
	var w := _world()
	var gr: float = GOAL_R.get(w, 60.0)
	if dv != null:
		for e in Dev.alle_orte(main):
			if str(e["world"]) != w and not w.begins_with("solo:"):
				continue
			var k := str(e["kind"])
			if k in ["szene", "raum"] or bool(e.get("at_mw", false)):
				continue
			var p = dv.scene_pos(e)
			if p == null:
				continue
			var pp: Vector3 = p
			if k in ["vignette", "erlebnis"]:
				if Vector2(pp.x, pp.z).length() < gr + 30.0:
					zones_static.append([pp, maxf(7.0, float(e.get("r", 6.0)) * 0.8)])
				continue
			if Vector2(pp.x, pp.z).length() > gr or Vector2(pp.x, pp.z).length() < 3.0 or not _walkable(pp):
				continue
			goals.append({"p": main.free_spot(pp, 0.5, true), "type": _goal_type(str(e["name"]), k), "name": str(e["name"])})
	var d: Dictionary = main.scenes.data if main.scenes != null else {}
	for bk in ["bench", "bench2"]:
		if d.get(bk, null) is Vector3:
			goals.append({"p": d[bk], "type": "bench", "name": "Bank", "exact": true})
	if d.get("wc", null) is Vector3 and Vector2(d["wc"].x, d["wc"].z).length() < gr:
		goals.append({"p": main.free_spot(d["wc"], 0.5, true), "type": "wc", "name": "WC"})
	var cam_f: Vector3 = -main.cams[0].global_transform.basis.z
	var cam_az: float = rad_to_deg(atan2(cam_f.x, -cam_f.z))
	var n_spot := 0
	for i in range(12):                                         # a few spots in front of MoveEye (in its picture: a good test)
		var p2: Vector3 = main.pos_of(cam_az + randf_range(-30.0, 30.0), randf_range(7.0, 20.0))
		if _walkable(p2):
			goals.append({"p": main.free_spot(p2, 0.5, true), "type": "spot", "name": ""})
			n_spot += 1
			if n_spot >= 3:
				break


func _zones_now() -> Array:
	"""the places the modes report (riddles, dangers, gates, task figures, the goal of a round) + the static ones"""
	var out: Array = zones_static.duplicate()
	var m := _mode
	var mg = main.get("maggie")
	if mg != null and is_instance_valid(mg) and bool(mg.running):
		if mg.has_method("tor_pos"):
			out.append([mg.tor_pos(), 12.0])
		for r in mg._rests:
			if r is Dictionary and r.get("pos", null) is Vector3:
				out.append([r["pos"], 10.0])
		for z in mg._zk_orte:
			if z is Array and z.size() > 0 and z[0] is Vector3:
				out.append([z[0], 12.0])
		for md in mg._modules:
			if not is_instance_valid(md):
				continue
			if md.has_method("sperren"):
				for sp in md.sperren():
					out.append([sp[0], float(sp[1]) + 6.0])
			if md.get("_dens") is Array:
				for dn in md._dens:
					if dn is Vector3:
						out.append([dn, 15.0])
			if md.get("_tiere") is Array:
				for ti in md._tiere:
					if ti is Dictionary and is_instance_valid(ti.get("n", null)):
						out.append([ti["n"].global_position, 12.0])
	var ab = main.get("abenteuer")
	if m == "abenteuer" and ab != null and is_instance_valid(ab) and not ab.R.is_empty():
		var bt = main.scenes.data.get("bergtal", null) if main.scenes != null else null
		var ci: int = clampi(int(ab.R.get("chapter", ab.W.get("chapter", 1))) - 1, 0, AbD.CHAPTERS.size() - 1)
		var ch: Dictionary = AbD.CHAPTERS[ci]
		if bt != null and is_instance_valid(bt):
			var cp: Array = ch.get("camp", [])
			if cp.size() >= 3:
				out.append([bt.WG(float(cp[1]), float(cp[2])), 14.0])        # the camp of the chapter (MoveEye stands there)
			for stg in ch.get("stages", []):
				var pts: Array = []
				if stg.has("walk"):
					pts = stg["walk"]
				elif stg.has("fork"):
					for sd in stg["fork"]:
						pts.append_array(sd[1])
				elif stg.has("read"):
					pts = stg["read"].get("detour", [])
				if not pts.is_empty():
					var last: Vector2 = pts[-1]
					out.append([bt.WG(last.x, last.y), 12.0])                # the places of the clues and of the found piece
	var fa = main.get_node_or_null("fp_aufgaben")
	if fa != null and str(fa.get("what")) != "":
		for k in ["kid", "mum", "thief"]:
			var a = fa.get(k)
			if a != null and is_instance_valid(a):
				out.append([a.global_position, 8.0])
		out.append([Vector3.ZERO, 7.0])                         # your bike beside MoveEye
	var gm = main.get("game")
	if m == "spiel" and gm != null:
		out.append([gm.goal, 8.0])
	if m != "frei":
		out.append([Vector3.ZERO, 5.0])                         # in the modes nobody stands right in front of MoveEye
	return out


func _in_zone(p: Vector3, pad := 0.0) -> int:
	for i in range(zones.size()):
		var c: Vector3 = zones[i][0]
		if Vector2(p.x - c.x, p.z - c.z).length() < float(zones[i][1]) + pad:
			return i
	return -1


func _push_out(p: Vector3) -> Vector3:
	for z in zones:
		var c: Vector3 = z[0]
		var r: float = float(z[1]) + 1.0
		var dv := Vector2(p.x - c.x, p.z - c.z)
		if dv.length() < r:
			var n := dv.normalized() if dv.length() > 0.05 else Vector2(1, 0)
			p = Vector3(c.x + n.x * r, p.y, c.z + n.y * r)
	return main.free_spot(p, 0.4, true)


# ---- every few frames -----------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or main.visitors == null or main.head == null:
		return
	_tick -= dt
	if _tick > 0.0:
		return
	_tick = 0.5 if _lite() else 0.25
	_n += 1
	_mode = mode()
	var t := now_s()
	var key := str(main.scene) + ":" + str(main.scenes.root.get_instance_id() if main.scenes != null and main.scenes.root != null else 0)
	if key != _scene_key:
		_scene_key = key
		S.clear()
		seen.clear()
		_rebuild()
		_rebuild_t = t + 8.0
	elif t > _rebuild_t:
		_rebuild_t = t + (60.0 if goals.size() >= 4 else 10.0)   # (a world may still be building: look again)
		_rebuild()
	if _mode == "test":
		_grid.clear()
		return                                                   # tests: hands off (comparable numbers)
	_zone_t -= 0.25
	if _zone_t <= 0.0:
		_zone_t = 2.0
		zones = _zones_now()
	_players = _find_players()
	_cut(_mode == "cut")
	if _mode == "cut":
		return
	_build_grid()
	_adopt_new(t)
	var h: float = main.hour()
	var evening: bool = h >= 19.5 or h < 5.0
	for id in S.keys():
		var e: Dictionary = S[id]
		var v = e["v"]
		if not is_instance_valid(v) or v.is_queued_for_deletion() or v.done:
			_cleanup(e)
			S.erase(id)
			continue
		var far: bool = Vector2(v.position.x, v.position.z).distance_to(_centre2()) > 45.0
		if far and (_n + int(id)) % 4 != 0:
			continue                                             # far away: only every 4th time (simplified)
		if int(e.get("group", 0)) > 0:
			_follower(e, t)
			continue
		if evening and not bool(e.get("home", false)):
			_go_home(e)
		_weather(e)
		_activity(e, t)
		_zone_check(e)
		_stuck(e, t)
		if not _players.is_empty():
			_react(e, t)
	_spawner(t)


func _centre2() -> Vector2:
	for p in _players:
		return Vector2(p["p"].x, p["p"].z)
	return Vector2.ZERO


func _find_players() -> Array:
	"""the figures of the players: game.gd (phones), maggie_story.gd, the rover while exploring"""
	var out := []
	var nodes := []
	var gm = main.get("game")
	if gm != null and gm.get("players") is Array:
		for p in gm.players:
			if p is Dictionary and is_instance_valid(p.get("actor", null)):
				nodes.append(p["actor"])
	var mg = main.get("maggie")
	if mg != null and is_instance_valid(mg) and bool(mg.running) and mg.spieler() != null:
		nodes.append(mg.spieler())
	var ex = main.get("explore")
	if ex != null and bool(ex.get("on")) and main.rig != null:
		nodes.append(main.rig)
	var t := now_s()
	var seen_now := {}
	for n in nodes:
		var id: int = n.get_instance_id()
		seen_now[id] = true
		var p: Vector3 = n.global_position
		var vel := Vector3.ZERO
		if _pl_last.has(id):
			var lp: Array = _pl_last[id]
			var ddt: float = maxf(0.05, t - float(lp[1]))
			vel = (p - (lp[0] as Vector3)) / ddt
			vel.y = 0
		if n.get("cur_speed") != null:
			vel = Vector3(-sin(n.heading), 0, -cos(n.heading)) * float(n.cur_speed)
		_pl_last[id] = [p, t]
		out.append({"n": n, "p": p, "v": vel})
	for id in _pl_last.keys():
		if not seen_now.has(id):
			_pl_last.erase(id)
	return out


func _build_grid() -> void:
	_grid.clear()
	for v in main.visitors.get_children():
		if v.get("kind") != "person" or v.done or v.preview:
			continue
		var c := Vector2i(floori(v.position.x / 2.0), floori(v.position.z / 2.0))
		if not _grid.has(c):
			_grid[c] = []
		_grid[c].append(v)
	for p in _players:
		var n = p["n"]
		var c2 := Vector2i(floori(n.global_position.x / 2.0), floori(n.global_position.z / 2.0))
		if not _grid.has(c2):
			_grid[c2] = []
		_grid[c2].append(n)


# ---- steering: called by actor.gd (every 0.12 s per person) ---------------------------------------------------------------
func steer(v, d: Vector2) -> Vector2:
	"""keep apart from other figures: a gentle push away, pass on the right of somebody ahead (Lite-light: a 2 m grid)"""
	if _mode in ["test", "cut"] or _grid.is_empty() or v.controlled:
		return d
	var p := Vector2(v.position.x, v.position.z)
	var c := Vector2i(floori(p.x / 2.0), floori(p.y / 2.0))
	var out := d
	for gx in range(c.x - 1, c.x + 2):
		for gz in range(c.y - 1, c.y + 2):
			var cell = _grid.get(Vector2i(gx, gz), null)
			if cell == null:
				continue
			for u in cell:
				if u == v or not is_instance_valid(u) or u == v.leader or u.get("leader") == v:
					continue
				var q: Vector2 = Vector2(u.global_position.x, u.global_position.z) - p
				var dist := q.length()
				if dist > 1.8 or dist < 0.01:
					continue
				var n := q / dist
				var w: float = clampf((1.8 - dist) / 1.8, 0.0, 1.0)
				if n.dot(d) > 0.2:                                   # ahead: go round on the right
					out += Vector2(-d.y, d.x) * -1.0 * w * 1.1
				out -= n * w * 0.6
	return out.normalized() if out.length() > 0.01 else d


# ---- adopting the plain visitors (they get goals and things to do) --------------------------------------------------------
func _plain(v) -> bool:
	if v.get("kind") != "person" or v.controlled or v.preview or v.puppet or v.leader != null:
		return false
	if not v.variant in ["", "elderly", "backpacker"]:
		return false
	for k in v.get_meta_list():
		var ks := str(k)
		if ks == "berg_kind" and str(v.get_meta(k)) == "hiker":
			continue
		if ks.begins_with("st_"):
			continue
		return false                                             # a story / an event figure: leave it alone
	var me = main.get("menschen")
	if me != null and me.E.has(v.get_instance_id()):
		var me_e: Dictionary = me.E[v.get_instance_id()]
		if not me_e["cur"].is_empty() or not me_e["pose"].is_empty() or not me_e["q"].is_empty():
			return false
	return true


func _adopt_new(t: float) -> void:
	if _mode != "frei":
		return
	var p_adopt: float = {"wenig": 0.35, "normal": 0.5, "belebt": 0.65}.get(menge["frei"], 0.5)
	for v in main.visitors.get_children():
		var id: int = v.get_instance_id()
		if seen.has(id) or S.has(id):
			continue
		seen[id] = true
		if not _plain(v) or v.route.size() > 2:
			if _plain(v) and v.has_meta("berg_kind"):
				S[id] = _new_entry(v, false)                     # a hiker on its trail: only the reactions and the rests
			continue
		if randf() > p_adopt:
			continue
		var e := _new_entry(v, false)
		S[id] = e
		var b: Vector3 = v.route[-1] if v.route.size() > 0 and v.route[-1] is Vector3 else v.target
		_plan(e, v.position, b)
		stats["adopted"] += 1
		var kids := 0
		for u in main.visitors.get_children():                   # a couple / a family of the old visitors: the others too
			if u.get("leader") == v and u.get("kind") == "person":
				var f := _new_entry(u, false)
				f["group"] = id
				S[u.get_instance_id()] = f
				seen[u.get_instance_id()] = true
				e["kind"] = "couple"
				kids += 1 if u.variant == "child" else 0
		if kids > 0:
			e["kind"] = "family"


func _new_entry(v, own: bool) -> Dictionary:
	return {"v": v, "own": own, "act": "", "goals_left": 0, "exit": v.target, "home": false, "rain": false,
			"st_p": v.position, "st_t": now_s(), "st_n": 0, "greeted": {}, "dodge_t": 0.0, "run_t": 0.0, "group": 0, "props": [],
			"born": now_s()}


func _plan(e: Dictionary, a: Vector3, b: Vector3) -> void:
	"""1–3 goals that lie on the way from a to b (in order: no back and forth), verweilen, then on to b"""
	var v = e["v"]
	var ab := Vector2(b.x - a.x, b.z - a.z)
	var L := ab.length()
	if L < 4.0 or goals.is_empty():
		return
	var dirn := ab / L
	var cand := []
	for g in goals:
		var gp: Vector3 = g["p"]
		var q := Vector2(gp.x - a.x, gp.z - a.z)
		var along := q.dot(dirn) / L
		var side := absf(q.cross(dirn))
		if along < 0.08 or along > 0.92 or side > maxf(18.0, L * 0.45) or _in_zone(gp) >= 0:
			continue
		cand.append([along + randf_range(-0.05, 0.05), g])
	cand.shuffle()
	var k: int = randi_range(1, 2 if _lite() else 3)
	cand = cand.slice(0, k)
	cand.sort_custom(func(x, y): return x[0] < y[0])
	var route := []
	for c in cand:
		var g: Dictionary = c[1]
		var gp: Vector3 = g["p"]
		var spot: Vector3 = gp if bool(g.get("exact", false)) else main.free_spot(gp + Vector3(randf_range(-1.5, 1.5), 0, randf_range(-1.5, 1.5)), 0.4, true)
		var dwell: float = randf_range(12.0, 45.0) * (0.45 if main.weather == "rain" else 1.0)
		var look: Vector3 = spot + Vector3(dirn.x, 0, dirn.y) * 5.0
		if g["type"] in ["view", "spot"]:
			look = spot + (spot - a).normalized() * 10.0
		if g["type"] == "bench" and bool(g.get("exact", false)):
			look = spot + Vector3(0, 0, 5)
		route.append(spot)
		route.append([spot, dwell, 0.0, look])
		e["types"] = e.get("types", [])
		e["types"].append(g["type"])
	if route.is_empty():
		return
	route.append(b)
	v.target = route[0]
	v.route = route.slice(1)
	v.wait_until = 0.0
	v._face(v.target)
	e["goals_left"] = cand.size()
	e["exit"] = b
	v.next_idle = v.now_s() + randf_range(20.0, 40.0)          # no random stops between the goals (they stop there)


# ---- own statists (modes, «belebt») ---------------------------------------------------------------------------------------
func _spawner(t: float) -> void:
	if t < _spawn_t:
		return
	_spawn_t = t + (6.0 if _lite() else 4.0)
	var want := want_count()
	var have := own_count()
	if have > want:                                              # fewer wanted now: the last ones go home
		for id in S:
			var e: Dictionary = S[id]
			if bool(e.get("auto", false)) and int(e.get("group", 0)) <= 0 and not bool(e.get("home", false)):
				_go_home(e)
				have -= 1
				if have <= want:
					break
		return
	if have >= want or main.visitors.get_child_count() + 3 > int(main.max_visitors) + (4 if _mode != "frei" else 0):
		return
	var v = spawn_one("")
	if v != null and S.has(v.get_instance_id()):
		S[v.get_instance_id()]["auto"] = true                    # (only these go home when fewer are wanted - not the ones sent by hand)


func _edge_point(c: Vector3, r: float, az_deg: float) -> Vector3:
	"""a walkable point about r metres from c (looks round a little if water / steep rock is there)"""
	for i in range(8):
		var a := deg_to_rad(az_deg + (i * 23.0 if i % 2 == 0 else -i * 23.0))
		var p := c + Vector3(sin(a), 0, -cos(a)) * r * randf_range(0.85, 1.1)
		if _walkable(p) and _in_zone(p, 2.0) < 0:
			return main.free_spot(p, 0.4, true)
	return _push_out(main.free_spot(c + Vector3(sin(deg_to_rad(az_deg)), 0, -cos(deg_to_rad(az_deg))) * r, 0.4, true))


func spawn_one(group := "") -> Node3D:
	"""a statist (or a couple, a family, somebody with the dog) comes in from the edge, has goals, leaves on the other side"""
	var c := Vector3.ZERO
	var cp := _centre2()
	c = Vector3(cp.x, 0, cp.y)
	var r: float = SPAWN_R.get(_world(), 35.0)
	var cam_f: Vector3 = -main.cams[0].global_transform.basis.z
	var cam_az: float = rad_to_deg(atan2(cam_f.x, -cam_f.z))
	var half: float = float(main.CAM_FOV[0]) * 0.5
	var az: float = cam_az + (half + randf_range(20.0, 80.0)) * (1.0 if randf() < 0.5 else -1.0)   # outside MoveEye's picture
	if not _players.is_empty():
		az = randf() * 360.0
	var a := _edge_point(c, r, az)
	var b := _edge_point(c, r, az + 180.0 + randf_range(-40.0, 40.0))
	if group == "":
		var rr := randf()
		group = "single" if rr < 0.55 else ("dog" if rr < 0.7 else ("couple" if rr < 0.88 else "family"))
		if _mode == "maggie" or main.is_dark():
			group = "single" if randf() < 0.7 else "couple"
	var me = main.get("menschen")
	var lead = null
	var members := []
	match group:
		"family":
			if me != null:
				lead = me.spawn_kind("m_familie", a, b)
		"couple":
			lead = main.spawn("person", a, b)
			if lead != null:
				var p2 = main.spawn("person", a + Vector3(0.0, 0, 0.9), b)
				if p2 != null:
					p2.leader = lead
					p2.speed = lead.speed * 1.3
					p2.follow_off = Vector3(0.8, 0, 0.1)
		"dog":
			lead = main.spawn("person", a, b)
			if lead != null and main.simreal != null:
				var dg = main.spawn("dog", a + Vector3(1.0, 0, 1.0), b)
				if dg != null:
					main.simreal.leash(lead, dg)
		_:
			lead = main.spawn("elderly" if randf() < 0.12 else "person", a, b)
	if lead == null:
		return null
	for v in main.visitors.get_children():
		if v.get("leader") == lead and v.get("kind") == "person":
			members.append(v)
	var e := _new_entry(lead, true)
	e["kind"] = group
	S[lead.get_instance_id()] = e
	seen[lead.get_instance_id()] = true
	lead.set_meta("st_statist", true)
	for mbr in members:
		var f := _new_entry(mbr, true)
		f["group"] = lead.get_instance_id()
		S[mbr.get_instance_id()] = f
		seen[mbr.get_instance_id()] = true
		mbr.set_meta("st_statist", true)
	_plan(e, a, b)
	stats["spawned"] += 1
	return lead


func _remove(v) -> void:
	if not is_instance_valid(v):
		return
	for u in main.visitors.get_children():
		if u.get("leader") == v:
			u.done = true
			u.queue_free()
	v.done = true
	v.queue_free()


# ---- the parts of the tick ------------------------------------------------------------------------------------------------
func _cut(on: bool) -> void:
	"""cut scene: the statists disappear (mine are removed, the adopted ones hidden until it is over)"""
	if on == _was_cut:
		return
	_was_cut = on
	for id in S.keys():
		var e: Dictionary = S[id]
		var v = e["v"]
		if not is_instance_valid(v):
			continue
		if on:
			if bool(e.get("own", false)):
				_remove(v)
			else:
				v.visible = false
				e["cut_wait"] = v.wait_until
				v.wait_until = v.now_s() + 1.0e5
			stats["cut_hidden"] += 1
		else:
			v.visible = true
			if e.has("cut_wait"):
				v.wait_until = float(e["cut_wait"])
				e.erase("cut_wait")


func _go_home(e: Dictionary) -> void:
	"""evening (or fewer wanted): the goals left out, straight home (the exit / the parking)"""
	var v = e["v"]
	e["home"] = true
	if int(e.get("goals_left", 0)) <= 0 and not bool(e.get("own", false)):
		return
	var b: Vector3 = e.get("exit", v.target)
	for g in goals:
		if g["type"] == "parking" and Vector2(g["p"].x - v.position.x, g["p"].z - v.position.z).length() < 120.0 and randf() < 0.5:
			b = g["p"]
	v.route = [b] if v.position.distance_to(b) > 2.0 else []
	if v.route.is_empty():
		v.route = [main.free_spot(b + Vector3(randf_range(-30, 30), 0, randf_range(-30, 30)), 0.4, true)]
	v.target = v.route.pop_front()
	v.wait_until = 0.0
	v.idle_until = 0.0
	e["goals_left"] = 0
	_end_act(e)
	stats["home"] += 1


func _weather(e: Dictionary) -> void:
	var v = e["v"]
	var wet: bool = main.weather == "rain"
	if wet and not bool(e["rain"]):
		e["rain"] = true
		e["dry_speed"] = v.speed
		v.speed = minf(v.speed * 1.3, 2.0)                       # rain: quicker steps
		if v.wait_until - v.now_s() > 8.0 and v.wait_until - v.now_s() < 1.0e4:
			v.wait_until = v.now_s() + randf_range(2.0, 6.0)      # nobody stays long in the rain
	elif not wet and bool(e["rain"]):
		e["rain"] = false
		v.speed = float(e.get("dry_speed", v.speed))


func _activity(e: Dictionary, t: float) -> void:
	"""waiting at a goal / a rest of the route: something to do (phone, photo, shoe, drink, backpack off, sit)"""
	var v = e["v"]
	var waiting: bool = t < v.wait_until and v.wait_until - t < 1.0e4
	if not waiting:
		if str(e["act"]) != "":
			_end_act(e)
		return
	if str(e["act"]) == "":
		if v.wait_until - t < 4.0:
			return                                               # a short stop (letting somebody pass): nothing to start
		var types: Array = e.get("types", [])
		var ty: String = str(types[0]) if not types.is_empty() else "place"
		if not types.is_empty() and v.position.distance_to(v.target) < 1.0:
			types.pop_front()
			e["goals_left"] = maxi(0, int(e["goals_left"]) - 1)
		e["act"] = _pick_act(e, ty)
		e["seq"] = _act_seq(e, str(e["act"]))
		var a: Dictionary = stats["acts"]
		a[e["act"]] = int(a.get(e["act"], 0)) + 1
		e["seg_t"] = 0.0
	if t < float(e.get("seg_t", 0.0)):
		return
	var seq: Array = e.get("seq", [])
	if seq.is_empty():
		seq = [["look", 4.0], ["phone", 5.0], ["look", 3.0]] if randf() < 0.5 else [["look", 5.0]]
		e["seq"] = seq
	var s: Array = seq.pop_front()
	var k: String = str(s[0])
	var dur: float = minf(float(s[1]) * randf_range(0.8, 1.3), v.wait_until - t)
	e["seg_t"] = t + dur
	_group_talk(e, t, dur)
	if k == "pack_down":
		_pack(e, true)
		k = "bend"
	elif k == "pack_up":
		_pack(e, false)
		k = "bend"
	if k in ["sit", "sitdrink"]:
		v.sit_seat = 0.45 if bool(e.get("bench_ok", false)) else 0.05
	if str(e.get("kind", "")) in ["couple", "family"] and k in ["look", "phone"] and randf() < 0.5:
		k = "talk"                                               # together: the leader talks too
	v.idle_kind = k
	v.idle_until = t + dur
	v.look_yaw = randf_range(-0.8, 0.8)


func _pick_act(e: Dictionary, ty: String) -> String:
	var v = e["v"]
	var wet: bool = main.weather == "rain"
	var has_pack: bool = _pack_mesh(v).size() > 0
	var w := {"phone": 1.0, "photo": 0.6, "tie": 0.35, "drink": 0.6, "look": 1.0}
	match ty:
		"view":
			w["photo"] = 3.0
		"bench":
			w = {"sitdrink": 3.0, "phone": 0.7}
			e["bench_ok"] = true
		"fountain":
			w["drink"] = 3.0
		"hut", "place":
			w["drink"] = 1.2
		"parking", "wc":
			w["phone"] = 2.0
	if has_pack and not wet:
		w["pack"] = 1.2 if ty in ["view", "hut", "place", "spot"] else 0.4
	if wet:
		for k in ["sit", "sitdrink", "tie", "photo", "drink"]:
			w.erase(k)
		w["phone"] = 1.0
		w["look"] = 1.0
	if str(e.get("kind", "")) == "family" or str(e.get("kind", "")) == "couple":
		w["talk"] = 2.0
	var tot := 0.0
	for k in w:
		tot += float(w[k])
	var r := randf() * tot
	for k in w:
		r -= float(w[k])
		if r <= 0.0:
			return k
	return "look"


func _act_seq(e: Dictionary, act: String) -> Array:
	match act:
		"photo":
			return [["look", 2.0], ["photo", 4.0], ["look", 2.5], ["photo", 3.0]]
		"tie":
			return [["tie", 4.5], ["look", 3.0], ["phone", 6.0]]
		"drink":
			return [["drink", 4.0], ["look", 5.0], ["drink", 3.0]]
		"sitdrink":
			return [["sitdrink", 30.0]]
		"sit":
			e["bench_ok"] = false
			return [["sit", 30.0]]
		"pack":
			return [["pack_down", 1.6], ["drink", 4.0], ["look", 6.0], ["photo", 3.0], ["look", 8.0]]
		"talk":
			return [["talk", 6.0], ["look", 3.0], ["talk", 8.0]]
	return [[act, 6.0], ["look", 4.0]]


func _end_act(e: Dictionary) -> void:
	var v = e["v"]
	if bool(e.get("pack_down", false)):
		_pack(e, false)
	e["act"] = ""
	e["seq"] = []
	if is_instance_valid(v) and v.idle_kind in ["photo", "drink", "sitdrink", "tie", "sit", "talk", "phone", "look", "bend"]:
		v.idle_until = 0.0


func _pack_mesh(v) -> Array:
	"""the backpack of actor.add_backpack (and its twin): boxes 0.3 × 0.4 × 0.15 on the torso"""
	var out := []
	if v.torso == null:
		return out
	for c in v.torso.get_children():
		if c is MeshInstance3D and c.mesh is BoxMesh and (c.mesh as BoxMesh).size.is_equal_approx(Vector3(0.3, 0.4, 0.15)):
			out.append(c)
	return out


func _pack(e: Dictionary, down: bool) -> void:
	"""Rucksack absetzen: off the back onto the ground beside the person (and on again when going on)"""
	var v = e["v"]
	var ms := _pack_mesh(v)
	if down and not bool(e.get("pack_down", false)) and not ms.is_empty():
		e["pack_down"] = true
		for m in ms:
			m.visible = false
		var n := Node3D.new()
		main.scenes.root.add_child(n)
		var side := Vector3(cos(v.heading), 0, -sin(v.heading))
		n.global_position = v.global_position + side * 0.45 + Vector3(0, 0.2, 0)
		n.rotation.y = v.heading + 0.4
		for m in ms:
			var c: MeshInstance3D = m.duplicate()
			c.visible = true
			c.position = Vector3.ZERO
			n.add_child(c)
		e["props"].append(n)
	elif not down and bool(e.get("pack_down", false)):
		e["pack_down"] = false
		for m in ms:
			m.visible = true
		_cleanup(e)


func _cleanup(e: Dictionary) -> void:
	for n in e.get("props", []):
		if is_instance_valid(n):
			n.queue_free()
	e["props"] = []


func _group_talk(e: Dictionary, t: float, dur: float) -> void:
	"""a couple / a family stands together at a goal: the others look at the leader and talk with gestures"""
	var v = e["v"]
	for id in S:
		var f: Dictionary = S[id]
		if int(f.get("group", 0)) != v.get_instance_id():
			continue
		var u = f["v"]
		if not is_instance_valid(u) or u.variant == "child" and randf() < 0.5:
			continue
		u.idle_kind = "talk" if randf() < 0.75 else "look"
		u.idle_until = t + dur
		var to: Vector3 = v.position - u.position
		u.look_yaw = clampf(wrapf(atan2(-to.x, -to.z) - u.heading, -PI, PI), -1.2, 1.2)


func _follower(e: Dictionary, t: float) -> void:
	"""members of a group: when the leader stands still at a goal, they gather and talk (with gestures)"""
	var u = e["v"]
	var lead = u.leader
	if lead == null or not is_instance_valid(lead):
		return
	if t < lead.wait_until and lead.wait_until - t < 1.0e4 and t >= u.idle_until and u.cur_speed < 0.2 and u.variant != "child":
		u.idle_kind = "talk" if randf() < 0.7 else "look"
		u.idle_until = t + randf_range(3.0, 7.0)
		var to: Vector3 = lead.position - u.position
		u.look_yaw = clampf(wrapf(atan2(-to.x, -to.z) - u.heading, -PI, PI), -1.2, 1.2)


func _zone_check(e: Dictionary) -> void:
	"""not into a riddle place / a danger / a gate: the next point is moved out, standing inside ends the stay"""
	if zones.is_empty():
		return
	var v = e["v"]
	if v.target is Vector3 and _in_zone(v.target) >= 0:
		v.target = _push_out(v.target)
		stats["zone_out"] += 1
	if _in_zone(v.position) >= 0 and v.wait_until - v.now_s() > 0.5 and v.wait_until - v.now_s() < 1.0e4:
		v.wait_until = v.now_s()
		_end_act(e)
	for i in range(v.route.size()):
		var p = v.route[i]
		var q: Vector3 = p[0] if p is Array else p
		if _in_zone(q) >= 0:
			var nq := _push_out(q)
			if p is Array:
				p[0] = nq
			else:
				v.route[i] = nq


func _stuck(e: Dictionary, t: float) -> void:
	"""no progress although it wants to walk: 6 s -> skip the point / a detour, 15 s -> straight to the exit, 35 s -> gone"""
	var v = e["v"]
	var walking: bool = t >= v.wait_until and t >= v.idle_until and Vector2(v.target.x - v.position.x, v.target.z - v.position.z).length() > 0.6
	if not walking or v.position.distance_to(e["st_p"]) > 0.6:
		e["st_p"] = v.position
		e["st_t"] = t
		e["st_n"] = 0
		return
	var stuck_s: float = t - float(e["st_t"])
	var n: int = int(e["st_n"])
	if stuck_s > 6.0 and n == 0:
		e["st_n"] = 1
		stats["stuck_skip"] += 1
		if v.route.size() > 0:
			v._next_point(v.now_s())
		else:
			var side := Vector3(-(v.target - v.position).z, 0, (v.target - v.position).x).normalized() * (3.0 if randf() < 0.5 else -3.0)
			v.route.push_front(v.target)
			v.target = main.free_spot(v.position + side, 0.4, true)
	elif stuck_s > 15.0 and n == 1:
		e["st_n"] = 2
		stats["stuck_exit"] += 1
		v.route = []
		v.target = _push_out(main.free_spot(e.get("exit", v.target), 0.4, true))
		e["goals_left"] = 0
	elif stuck_s > 35.0 and n == 2 and not _in_picture(v.position):
		stats["stuck_gone"] += 1
		_remove(v)


func _in_picture(p: Vector3) -> bool:
	var hp: Vector3 = main.head.global_position
	var to: Vector3 = p - hp
	to.y = 0
	if to.length() > 60.0:
		return false
	var f: Vector3 = -main.cams[0].global_transform.basis.z
	f.y = 0
	return f.normalized().dot(to.normalized()) > cos(deg_to_rad(float(main.CAM_FOV[0]) * 0.5 + 5.0))


# ---- the player -----------------------------------------------------------------------------------------------------------
func _react(e: Dictionary, t: float) -> void:
	var v = e["v"]
	for pl in _players:
		var pp: Vector3 = pl["p"]
		var pv: Vector3 = pl["v"]
		var to: Vector3 = pp - v.position
		to.y = 0
		var d := to.length()
		if d > 10.0:
			continue
		var pid: int = pl["n"].get_instance_id()
		var fwd := Vector3(-sin(v.heading), 0, -cos(v.heading))
		var rel: float = wrapf(atan2(-to.x, -to.z) - v.heading, -PI, PI)
		# runs: stand still, look
		if pv.length() > 2.6 and d < 9.0 and t > float(e["run_t"]):
			e["run_t"] = t + 5.0
			if v.wait_until - t < 2.0:
				v.wait_until = t + randf_range(1.5, 2.5)
			_look_at(v, rel, 2.0)
			stats["stop_run"] += 1
			continue
		# narrow way: coming towards each other - step to the right, wait a moment
		var head_on: bool = d < 4.5 and v.cur_speed > 0.3 and fwd.dot(to / maxf(d, 0.01)) > 0.75 and (pv.length() < 0.3 or pv.normalized().dot(-to / maxf(d, 0.01)) > 0.5)
		if head_on and t > float(e["dodge_t"]):
			e["dodge_t"] = t + 8.0
			var right := Vector3(-fwd.z, 0, fwd.x) * -1.0
			var spot: Vector3 = main.free_spot(v.position + right * 1.1 + fwd * 0.6, 0.35, true)
			v.route.push_front(v.target)
			v.route.push_front([spot, randf_range(1.2, 2.0), 0.0, pp])
			v.target = spot
			stats["dodge"] += 1
		# look and greet (once per player)
		if d < 7.0 and absf(rel) < 1.4 and not e["greeted"].has(pid):
			e["greeted"][pid] = true
			_look_at(v, rel, 1.6)
			if randf() < 0.75:
				_say(v, _greeting(e), 2.2)
				stats["greet"] += 1
				if t - _tip_t > 90.0 and randf() < 0.25 and main.weather != "rain" and not main.is_dark():
					_tip_t = t
					var tip := _tip()
					if tip != "":
						get_tree().create_timer(2.4).timeout.connect(func(): _say(v, tip, 5.0))
						stats["tips"] += 1


func _look_at(v, rel: float, secs: float) -> void:
	v._glance_yaw = clampf(rel, -1.1, 1.1)
	v._glance_until = v.now_s() + secs
	v._glance_next = v.now_s() + secs + 1.0
	if v.now_s() < v.idle_until and v.idle_kind == "look":
		v.look_yaw = clampf(rel, -1.1, 1.1)


func _greeting(e: Dictionary) -> String:
	var h: float = main.hour()
	if str(e.get("kind", "")) in ["family", "couple"] and randf() < 0.5:
		return T.t("Grüezi mitenand")
	if h >= 18.0:
		return T.t("Guten Abend")
	if main.scene == "bergtal" or _world() == "bergtal":
		return T.t("Grüezi") if randf() < 0.7 else T.t("Hoi")
	return T.t("Grüezi") if randf() < 0.6 else T.t("Hallo")


func _tip() -> String:
	"""a sentence about the area - never the answer of a riddle"""
	var w := _world()
	var L: Array
	match w:
		"bergtal":
			L = [T.t("Das Wetter ändert hier oben schnell – lieber früh los."), T.t("Wenn Nebel kommt, gut auf die Wegweiser achten."),
				T.t("Die Murmeltiere pfeifen, wenn ein Adler kommt."), T.t("Oben am Grat ist es windig – eine Jacke hilft."),
				T.t("Am Abend sieht man hier manchmal Gämsen.")]
		"ferienpark":
			L = [T.t("Vom Aussichtspunkt sieht man über den ganzen See."), T.t("Am Morgen sind beim Steg oft Enten."),
				T.t("Nach 22 Uhr ist Nachtruhe – dann wird es still."), T.t("Am Abend riecht es überall nach Grillwurst.")]
		_:
			L = [T.t("Schöner Platz hier, nicht?"), T.t("Heute Nacht soll es kühl werden."),
				T.t("Am Waldrand sieht man abends manchmal Rehe."), T.t("Am Abend sind viele mit dem Hund unterwegs.")]
	return str(L[randi() % L.size()])


func _say(v, text: String, secs: float) -> void:
	"""a speech bubble above the head - only the players and the operator see it (never MoveEye's cameras)"""
	if not is_instance_valid(v) or text == "":
		return
	var old = v.get_node_or_null("st_say")
	if old != null:
		old.free()
	var lb := Label3D.new()
	lb.name = "st_say"
	lb.text = text
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.no_depth_test = false
	lb.font_size = 40
	lb.pixel_size = 0.006
	lb.outline_size = 10
	lb.modulate = Color(1, 1, 1)
	lb.outline_modulate = Color(0.05, 0.05, 0.08, 0.85)
	lb.width = 420.0
	lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lb.layers = Figur.TAG_LAYERS
	lb.position = Vector3(0, 2.15 * (v.body_root.scale.y if v.body_root != null else 1.0), 0)
	v.add_child(lb)
	get_tree().create_timer(secs).timeout.connect(func():
		if is_instance_valid(lb):
			lb.queue_free())
