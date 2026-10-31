extends Node
## P10 «Menschen-Verhalten» (Zweig real-menschen, 31.10.2026): Besucher bewegen und verhalten sich wie echte Menschen auf
## einem Campingplatz - damit Personenerkennung, Folgen und Alarm-Logik von MoveEye realistisch getestet werden.
##
##  Gangarten (set_gait): stroll ~1,2 m/s · walk ~1,4 · hurry ~1,9 · run ~3,5 (Kinder ~3) · sneak (geduckt, ~0,6 m/s,
##   Stop-and-go, schaut zur Kamera) · crawl (liegend, ~0,35 m/s, wie «Tarnen und Kriechen») · stand. Die Schritte passen
##   von selbst zum Tempo (actor.gd _animate: Schrittfrequenz und -länge aus der Geschwindigkeit).
##  Natürliche Streuung («Verhalten realistisch»): Tempo je Person, leichte Umwege (Kurve statt Gerade), Kinder rennen
##   sprunghaft (Spurt, Haken, kurz stehen), Hindernissen ausweichen (gab es schon: main.avoid).
##  Vielfalt (vor dem Bau der Figur über Actor.npc_look): Grösse (Kinder 1,0–1,4 m, Erwachsene 1,55–1,95 m), Kleider
##   (nachts öfter dunkel), Leuchtweste (Rückstrahler im Infrarot), Kapuze / Mütze, Rucksack, Tasche, geschobenes Velo,
##   Schirm bei Regen (auch wenn der Regen erst unterwegs anfängt).
##  Gruppen: Familie (Kinder rennen voraus und zurück), Gruppe bleibt stehen und redet (3–5), draussen sitzen (Stühle),
##   Paare gab es schon (main.visit «couple»), gehende Gruppen auch (simreal «group2..4»).
##  Tagesablauf (Besuch → Von selbst): morgens WC / Dusche (Tuch, Necessaire), tagsüber spazieren, abends draussen sitzen,
##   nachts fast leer ausser WC-Gänge mit Taschenlampe (actor.add_lamp("torch") - es gibt noch kein Licht-Paket mit einer
##   Taschenlampen-Funktion; ein späteres kann add_lamp ersetzen, die Aufrufe hier bleiben).
##
## Schnittstelle für Szenarien (das Paket «Einbruch-Abläufe» baut damit seine Abläufe; die Methoden stehen auch direkt an
## der Figur, actor.gd: person.sneak_to(...)). Aufrufe hintereinander werden der Reihe nach ausgeführt; danach geht die
## Person ihren alten Weg weiter.
##   set_gait(v, g)                  stroll | walk | hurry | run | sneak | crawl | stand | "" (= wieder normal)
##   sneak_to(v, p, crawl_last=0)    geduckt hin, Stop-and-go, die letzten crawl_last Meter kriechend
##   loiter(v, center, secs, r=4)    herumlungern: ein paar Schritte, stehen, umschauen, Handy, zur Kamera schauen
##   peek_into(v, p, secs=5)         nah an Auto / Zelt, bückt sich und schaut hinein
##   hide_behind(v, p=null, secs=8)  geduckt hinter das nächste Ding (von der Kamera aus gesehen) bei p bzw. bei der Person
##   avoid_light(v, on=true)         meidet Licht: Lampe aus, Wegpunkte aus dem Schein der Lampen, weisses Licht von
##                                    MoveEye -> geduckt zur Seite, warten, weiter
##   come_back(v, after_s, center)   geht aus dem Bild, wartet, kommt zurück (center, sonst wo sie war)
##   busy(v) -> bool                 führt noch einen Auftrag aus
## Einstellungen: user://menschen.json. Test: /control {"action": "menschen", "do": info | set | spawn | api | probe}.
## Testläufe / Prüfstand: die Streuung (Look, Tempo, Umwege) ist dann aus, damit die Zahlen vergleichbar bleiben;
## die Schnittstelle wirkt immer.

const ActorS = preload("res://scripts/actor.gd")
const Quality = preload("res://scripts/quality.gd")

var main
const FILE := "user://menschen.json"
const SAVE := ["m_real", "m_kids", "m_groups", "m_plan"]
var m_real := true          # «Verhalten realistisch»
var m_kids := 0.15          # share of children among the people that come by themselves
var m_groups := true        # people also come in groups (families, standing and talking)
var m_plan := true          # the day of a campsite (WC in the morning, sitting in the evening, at night only WC walks)

const GAITS := {"stroll": [1.2, 0], "walk": [1.4, 0], "hurry": [1.95, 0], "run": [3.5, 0], "sneak": [1.0, 1], "crawl": [1.2, 2], "stand": [0.0, 0]}
const PLAN_SCENES := ["camping", "camping_voll", "stellplatz", "seeufer", "ort", "vorlage", "lustig"]
const KINDS := {
	"m_familie": ["Familie mit Kindern (Kinder rennen voraus und zurück)", "Menschen schicken"],
	"m_gespraech": ["Gruppe bleibt stehen und redet (3–5 Personen)", "Menschen schicken"],
	"m_sitzen": ["Draussen sitzen (bringen Stühle mit, bleiben eine Weile)", "Menschen schicken"],
	"m_wc": ["Gang zum WC / zur Dusche (nachts mit Taschenlampe)", "Menschen schicken"],
	"m_spazieren": ["Spaziergang: schlendert, bleibt stehen, schaut sich um", "Menschen schicken"],
	"m_eilig": ["Eilt oder rennt vorbei", "Menschen schicken"],
	"m_velo": ["Schiebt ein Velo vorbei", "Menschen schicken"],
	"m_gangarten": ["Gangarten nacheinander vor der Kamera (gehen, eilen, rennen, schleichen, kriechen)", "Menschen schicken"],
}
const DARK := [Color(0.07, 0.07, 0.08), Color(0.1, 0.12, 0.2), Color(0.16, 0.16, 0.17), Color(0.15, 0.17, 0.11), Color(0.17, 0.12, 0.09)]
const BRIGHT := [Color(0.75, 0.15, 0.12), Color(0.15, 0.35, 0.7), Color(0.9, 0.75, 0.2), Color(0.2, 0.55, 0.3), Color(0.85, 0.85, 0.82),
		Color(0.55, 0.3, 0.55), Color(0.95, 0.5, 0.15), Color(0.45, 0.6, 0.75), Color(0.6, 0.5, 0.35), Color(0.3, 0.3, 0.33)]

var E := {}                  # instance id -> entry {v, q, cur, saved, gait, avoid, ...}
var _next_look := {}         # what before_build should put on the next figure (from spawn_kind / pick_person)
var _tick := 0.0
var _next_plan := 0.0
var _rain := false
var _seq: Array = []         # «Gangarten nacheinander»: gaits still to send
var _seq_v = null
var stats := {"spawned": 0, "groups": 0, "kids": 0, "torches": 0, "vests": 0, "umbrellas": 0, "api": 0, "lit_dodges": 0}


func now_s() -> float:
	return Time.get_ticks_msec() / 1000.0              # the clock of the visitors (actor.now_s)


func _lite() -> bool:
	return Quality.lite()


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, float(d[k]) if k == "m_kids" else bool(d[k]))


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func _put(k: String, v) -> void:
	set(k, v)
	save()


func add_controls() -> void:
	var m = main
	var vh := {"sub": "Verhalten"}
	m.add_control("toggle", "m_real", "Menschen wie echt: jeder mit eigenem Tempo, Pausen und leichten Umwegen, Kinder rennen sprunghaft; verschieden gross (Kinder 1,0–1,4 m, Erwachsene 1,55–1,95 m) und angezogen (nachts öfter dunkel, Leuchtweste, Kapuze, Mütze, Rucksack, Tasche, Schirm bei Regen)",
			func(): return m_real, func(v): _put("m_real", bool(v)), "Besuch", vh)
	m.add_control("slider", "m_kids", "Anteil Kinder unter den Menschen, die von selbst kommen", func(): return m_kids, func(v): _put("m_kids", float(v)), "Besuch",
			{"sub": "Verhalten", "min": 0.0, "max": 0.6, "step": 0.05})
	m.add_control("toggle", "m_groups", "Menschen kommen auch in Gruppen: Familien mit Kindern, Leute bleiben stehen und reden",
			func(): return m_groups, func(v): _put("m_groups", bool(v)), "Besuch", vh)
	m.add_control("toggle", "m_plan", "Tagesablauf auf dem Campingplatz: morgens zu WC und Dusche, tagsüber spazieren, abends draussen sitzen, nachts fast leer – nur WC-Gänge mit Taschenlampe",
			func(): return m_plan, func(v): _put("m_plan", bool(v)), "Besuch", {"sub": "Von selbst"})
	for k in KINDS:
		var kk: String = k
		m.add_control("button", "m_send_" + kk.trim_prefix("m_"), KINDS[kk][0], null, func(): main.spawn(kk), "Besuch", {"sub": KINDS[kk][1]})


func info() -> Dictionary:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var g := {}
	var people := []
	for id in E:
		var e: Dictionary = E[id]
		var v = e["v"]
		if not is_instance_valid(v):
			continue
		var gk: String = str(e.get("gait", ""))
		g[gk] = int(g.get(gk, 0)) + 1
		people.append({"id": int(id), "variant": v.variant, "gait": gk, "speed": snappedf(v.cur_speed, 0.01), "crouch": snappedf(v.crouch, 0.01),
				"prone": snappedf(v.prone, 0.01), "h": snappedf(ActorS.BASE_H * v.body_root.scale.y, 0.01), "x": snappedf(v.position.x, 0.1),
				"z": snappedf(v.position.z, 0.1), "busy": busy(v), "lamp": v.lamp != null and v.lamp.light_energy > 0.0, "idle": v.idle_kind if v.now_s() < v.idle_until else "",
				"job": str(e["cur"].get("do", "")), "queue": e["q"].size(), "tx": snappedf(v.target.x, 0.1), "tz": snappedf(v.target.z, 0.1),
				"route": v.route.size(), "wait": snappedf(clampf(v.wait_until - v.now_s(), 0.0, 9999.0), 0.1)})
	d["gaits"] = g
	d["people"] = people
	d["stats"] = stats
	d["kinds"] = KINDS.keys()
	d["lite"] = _lite()
	d["testing"] = _testing()
	return d


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | spawn (kind, from [x, z], to [x, z]) | api (id, fn, args) | probe (gait, dist, dark)}"""
	var op := str(d.get("do", "info"))
	if op == "set" and str(d.get("key", "")) in SAVE:
		var k := str(d["key"])
		_put(k, float(d.get("value", 0.15)) if k == "m_kids" else bool(d.get("value", true)))
	elif op == "spawn":
		var f = _v3(d.get("from", null))
		var t = _v3(d.get("to", null))
		var v = main.spawn(str(d.get("kind", "m_spazieren")), f, t)
		return {"ok": v != null, "id": v.get_instance_id() if v != null else 0, "info": info()}
	elif op == "probe":
		var v = probe(str(d.get("gait", "walk")), float(d.get("dist", 10.0)), bool(d.get("dark", false)), float(d.get("off", 0.0)))
		return {"ok": v != null, "id": v.get_instance_id() if v != null else 0}
	elif op == "api":
		var v = instance_from_id(int(d.get("id", 0))) if d.has("id") else _last_person()
		if v == null or not is_instance_valid(v):
			return {"ok": false, "error": "no such person"}
		var a: Array = d.get("args", [])
		var fn := str(d.get("fn", ""))
		match fn:
			"set_gait":
				set_gait(v, str(a[0]) if a.size() > 0 else "walk")
			"sneak_to":
				sneak_to(v, _v3(a[0]), float(a[1]) if a.size() > 1 else 0.0)
			"loiter":
				loiter(v, _v3(a[0]), float(a[1]) if a.size() > 1 else 30.0, float(a[2]) if a.size() > 2 else 4.0)
			"peek_into":
				peek_into(v, _v3(a[0]), float(a[1]) if a.size() > 1 else 5.0)
			"hide_behind":
				hide_behind(v, _v3(a[0]) if a.size() > 0 else null, float(a[1]) if a.size() > 1 else 8.0)
			"avoid_light":
				avoid_light(v, bool(a[0]) if a.size() > 0 else true)
			"come_back":
				come_back(v, float(a[0]) if a.size() > 0 else 20.0, _v3(a[1]) if a.size() > 1 else null)
			_:
				return {"ok": false, "error": "unknown fn"}
		return {"ok": true, "id": v.get_instance_id()}
	return {"ok": true, "info": info()}


func _v3(a):
	if typeof(a) == TYPE_VECTOR3:
		return a
	if typeof(a) == TYPE_ARRAY and a.size() >= 2:
		return Vector3(float(a[0]), 0, float(a[a.size() - 1]))
	return null


func _last_person():
	var best = null
	for v in main.visitors.get_children():
		if v.kind == "person" and not v.done:
			best = v
	return best


func _testing() -> bool:
	"""a test run / the bench / a game round: no random look and pace (comparable numbers), the API still works"""
	if main == null:
		return true
	if main.testrun != null and main.testrun.running:
		return true
	if main.pruef != null and main.pruef.running:
		return true
	if main.get("einbruch") != null and main.einbruch.running:     # Einbruch-Abläufe: the thieves get their look from there
		return true
	return main.game != null and main.game.round_state in ["countdown", "play"]


func real() -> bool:
	return m_real and not _testing()


# ---- the look: before the figure is built -------------------------------------------------------------------------------
func before_build(kind: String) -> void:
	"""main.spawn, just before Actor.setup: the look of the next figure (actor.gd reads ActorS.npc_look)"""
	ActorS.npc_look = {}
	var extra: Dictionary = _next_look
	_next_look = {}
	if (not real() and not extra.has("force")) or ActorS.npc_camo:
		return
	if not kind in ["person", "child", "elderly", "jogger", "police", "courier", "drunk", "burglar"]:
		return
	var kid := kind == "child"
	var nl := {}
	var h: float = randf_range(1.0, 1.4) if kid else clampf(randfn(1.73 if randf() < 0.5 else 1.62, 0.07), 1.55, 1.95)
	if kind == "elderly":
		h = clampf(h - 0.04, 1.55, 1.9)
	nl["height"] = h
	if kind in ["person", "child", "elderly"]:
		var dark: bool = main.is_dark()
		var wet: bool = main.weather == "rain"
		var cold: bool = main.ambient < 10.0 or preload("res://scripts/kleidung.gd").stufe(main) == "warm"   # Winter: Mütze / Kapuze
		if randf() < (0.5 if dark else 0.2):
			nl["jacket"] = DARK[randi() % DARK.size()]
		else:
			nl["jacket"] = BRIGHT[randi() % BRIGHT.size()]
		if randf() < (0.6 if dark else 0.3):
			nl["trousers"] = DARK[randi() % DARK.size()]
		nl["hood"] = randf() < (0.5 if wet or cold else (0.15 if dark else 0.04))
		nl["cap"] = not bool(nl["hood"]) and randf() < (0.3 if cold else 0.12)
		nl["pack"] = randf() < (0.15 if kid else 0.25)
		if not kid:
			nl["umbrella"] = wet and kind != "jogger" and randf() < 0.55
	for k in extra:
		nl[k] = extra[k]
	ActorS.npc_look = nl


func after_build(v, kind: String) -> void:
	"""main.spawn, right after Actor.setup: clear the look, the extras (vest, bag, bike), the pace, follow the person"""
	var nl: Dictionary = ActorS.npc_look
	ActorS.npc_look = {}
	if v == null or v.kind != "person" or v.controlled or v.preview:
		return
	if not real() and not nl.has("force"):
		return
	stats["spawned"] += 1
	if str(nl.get("lamp", "")) == "torch":
		stats["torches"] += 1
	if bool(nl.get("umbrella", false)):
		_hold_umbrella(v)
		stats["umbrellas"] += 1
	var plain: bool = v.variant in ["", "elderly", "child"]
	if plain:
		var vest: bool = bool(nl.get("vest", randf() < (0.08 if main.is_dark() else 0.04))) and v.variant != "child"
		if vest:
			add_vest(v)
		if bool(nl.get("bag", false)):
			add_bag(v, str(nl.get("bag_kind", "bag")))
		if bool(nl.get("bike", false)) and not _lite():
			add_bike(v)
	var e := _entry(v)
	e["kid"] = v.variant == "child"
	if e["kid"]:
		stats["kids"] += 1
	if plain and not nl.has("gait"):
		var r := randf()
		var g := "stroll" if r < 0.55 else ("walk" if r < 0.88 else ("hurry" if r < 0.97 else "run"))
		if main.weather == "rain" and randf() < 0.45:
			g = "hurry"
		if main.is_dark() and g == "stroll":
			g = "walk"
		if e["kid"]:
			g = "walk"
		_pace(v, g)
	elif nl.has("gait"):
		_pace(v, str(nl["gait"]))
	e["to"] = v.target
	e["curve_t"] = now_s() + 0.3


func _entry(v) -> Dictionary:
	var id: int = v.get_instance_id()
	if not E.has(id):
		E[id] = {"v": v, "q": [], "cur": {}, "saved": null, "gait": "", "avoid": false, "next": now_s() + randf_range(1.0, 3.0),
				"kid": v.variant == "child", "base": v.speed, "curved": false, "pose": {}, "posed": false, "props": []}
	return E[id]


func _pace(v, g: String) -> void:
	"""speed of a gait with a personal spread (kids a bit slower when running, the elderly slower)"""
	if not GAITS.has(g):
		return
	var e := _entry(v)
	e["gait"] = g
	var s: float = float(GAITS[g][0]) * randf_range(0.9, 1.1)
	if v.variant == "elderly":
		s *= 0.7
	if v.variant == "child" and g == "run":
		s = randf_range(2.6, 3.3)
	if g != "stand":
		v.speed = s
		e["base"] = s
	if g in ["sneak", "crawl"]:
		v.next_idle = v.now_s() + 1.0e5                     # no random «bend» / «phone» while sneaking (stop and go: _process)
	elif v.next_idle - v.now_s() > 1.0e4 and e["cur"].is_empty():
		v.next_idle = v.now_s() + randf_range(6.0, 15.0)
	v.hold_post = int(GAITS[g][1]) if int(GAITS[g][1]) > 0 else -1
	v._want_c = 1.0 if v.hold_post >= 1 else 0.0
	v._want_p = 1.0 if v.hold_post >= 2 else 0.0
	v._post_smooth = true


# ---- things to wear and to carry ---------------------------------------------------------------------------------------
func add_vest(v) -> void:
	"""a high-visibility vest: yellow / orange over the jacket, two reflective stripes front and back (glow in the IR light)"""
	if v.torso == null:
		return
	var col: Color = Color(0.85, 0.95, 0.15) if randf() < 0.7 else Color(1.0, 0.45, 0.1)
	var t: float = v._cloth_t
	v._part(v.torso, v._caps(0.215, 0.38), Vector3(0, 0.3, 0), col, t, Vector3.ZERO, Vector3(1.07, 1.0, 0.72))
	for y in [0.2, 0.36]:
		v._part(v.torso, v._caps(0.218, 0.36), Vector3(0, y, 0), Color(0.82, 0.82, 0.8), t, Vector3.ZERO, Vector3(1.09, 0.1, 0.74))
		if main.simreal != null:
			main.simreal.add_reflector(v.torso, Vector3(0, y, -0.16), Vector2(0.34, 0.04), Color(0.85, 0.85, 0.82))
			main.simreal.add_reflector(v.torso, Vector3(0, y, 0.16), Vector2(0.34, 0.04), Color(0.85, 0.85, 0.82), Vector3(0, PI, 0))
	stats["vests"] += 1


func add_bag(v, what := "bag") -> void:
	"""bag = shopping bag / toilet bag in the left hand, towel = a towel over the shoulder too"""
	if v.arms.size() < 2:
		return
	var col: Color = BRIGHT[randi() % BRIGHT.size()]
	if what in ["wash", "towel"]:
		v._part(v.arms[0][2], v._box(0.22, 0.13, 0.1), Vector3(0, -0.4, 0), col.darkened(0.3), main.ambient + 2.0)
		v._part(v.torso, v._box(0.12, 0.5, 0.16), Vector3(0.17, 0.33, 0.0), Color(0.92, 0.92, 0.9) if randf() < 0.5 else col.lightened(0.4), v._cloth_t, Vector3(0, 0, 0.25))
	else:
		v._part(v.arms[0][2], v._box(0.1, 0.34, 0.36), Vector3(-0.02, -0.5, 0), col, main.ambient + 2.0)
	v.arm_hold[-1] = Vector3(0.0, 0.12, 0.1)


func _hold_umbrella(v) -> void:
	"""the umbrella of actor.add_umbrella hangs at the torso - the right hand holds the stick"""
	v.arm_hold[1] = Vector3(0.75, 1.35, -0.2)


func add_bike(v) -> void:
	"""a bike pushed on the right side, the right hand on the handlebar; wheels turn, rear reflector"""
	var bk: Node3D = v._pivot(v.body_root, Vector3(0.48, 0, -0.15))
	var fc: Color = BRIGHT[randi() % BRIGHT.size()]
	var amb: float = main.ambient
	for z in [-0.55, 0.55]:
		var w: Node3D = v._pivot(bk, Vector3(0, 0.34, z))
		v._part(w, v._cyl(0.34, 0.34, 0.035, 18), Vector3.ZERO, Color(0.06, 0.06, 0.06), amb + 3.0, Vector3(0, 0, PI / 2))
		v.wheels.append([w, 0.34])
	v._part(bk, v._cyl(0.022, 0.022, 0.75, 6), Vector3(0, 0.55, -0.05), fc, amb, Vector3(PI / 2 - 0.25, 0, 0))
	v._part(bk, v._cyl(0.022, 0.022, 0.62, 6), Vector3(0, 0.48, 0.12), fc, amb, Vector3(0.35, 0, 0))
	v._part(bk, v._cyl(0.022, 0.022, 0.6, 6), Vector3(0, 0.48, -0.45), fc, amb, Vector3(-0.3, 0, 0))
	v._part(bk, v._box(0.12, 0.04, 0.24), Vector3(0, 0.86, 0.08), Color(0.08, 0.08, 0.08), amb)
	v._part(bk, v._cyl(0.016, 0.016, 0.5, 6), Vector3(0, 0.98, -0.5), Color(0.1, 0.1, 0.1), amb, Vector3(0, 0, PI / 2))
	if main.simreal != null:
		main.simreal.add_reflector(bk, Vector3(0, 0.8, 0.62), Vector2(0.06, 0.04), Color(0.9, 0.1, 0.05))
	v.arm_hold[1] = Vector3(0.55, 0.35, 0.3)
	v.radius = 0.55


func _chair(v) -> Node3D:
	"""a folding chair where the person sits (put there when it arrives, taken away when it leaves)"""
	var c := Node3D.new()
	main.scenes.root.add_child(c)
	c.global_position = v.global_position
	c.rotation.y = v.heading
	var col: Color = [Color(0.15, 0.3, 0.55), Color(0.2, 0.4, 0.2), Color(0.5, 0.12, 0.1), Color(0.2, 0.2, 0.22)][randi() % 4]
	var amb: float = main.ambient
	v._part(c, v._box(0.5, 0.04, 0.45), Vector3(0, v.sit_seat - 0.02, 0.0), col, amb + 1.0)
	v._part(c, v._box(0.5, 0.5, 0.04), Vector3(0, v.sit_seat + 0.25, 0.24), col, amb + 1.0, Vector3(-0.15, 0, 0))
	for sx in [-0.23, 0.23]:
		v._part(c, v._cyl(0.012, 0.012, 0.62, 5), Vector3(sx, v.sit_seat * 0.5, 0.0), Color(0.6, 0.6, 0.62), amb, Vector3(0.6, 0, 0))
		v._part(c, v._cyl(0.012, 0.012, 0.62, 5), Vector3(sx, v.sit_seat * 0.5, 0.0), Color(0.6, 0.6, 0.62), amb, Vector3(-0.6, 0, 0))
	return c


# ---- where: points in the picture of the head camera ----------------------------------------------------------------------
func in_view(dist: float, off_deg := 0.0) -> Vector3:
	"""a point on the ground in the direction the head camera looks (off_deg: to the side, + = right)"""
	var hp: Vector3 = main.head.global_position
	var f: Vector3 = -main.cams[0].global_transform.basis.z
	f.y = 0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	f = f.rotated(Vector3.UP, deg_to_rad(-off_deg))
	return Vector3(hp.x, 0, hp.z) + f * dist


func _cross(dist: float) -> Array:
	"""start and end outside the picture, the way across it at about dist metres"""
	var half: float = float(main.CAM_FOV[0]) * 0.5
	var s := 1.0 if randf() < 0.5 else -1.0
	var a: Vector3 = in_view(dist / cos(deg_to_rad(half + 25.0)), -s * (half + 25.0))
	var b: Vector3 = in_view(dist / cos(deg_to_rad(half + 25.0)), s * (half + 25.0))
	return [main.free_spot(a, 0.4, true), main.free_spot(b, 0.4, true)]


func _out_of_view(from: Vector3) -> Vector3:
	"""a place outside the picture of the head camera, on the side nearest to from"""
	var half: float = float(main.CAM_FOV[0]) * 0.5
	var hp: Vector3 = main.head.global_position
	var f: Vector3 = -main.cams[0].global_transform.basis.z
	f.y = 0
	var r := Vector3(-f.z, 0, f.x)
	var s := 1.0 if (from - hp).dot(r) >= 0.0 else -1.0
	var d: float = clampf(Vector2(from.x - hp.x, from.z - hp.z).length(), 10.0, 22.0)
	return main.free_spot(in_view(d * 1.3, s * (half + 30.0)), 0.4, true)


# ---- spawning the new kinds ----------------------------------------------------------------------------------------------
func is_kind(k: String) -> bool:
	return KINDS.has(k)


func pick_person(kk: String) -> String:
	"""main._life: a «person» that comes by itself may be a child or a group instead (Anteil Kinder, Gruppen)"""
	if kk != "person" or not real():
		return kk
	var r := randf()
	if r < m_kids:
		return "child"
	if m_groups and r < m_kids + 0.14:
		return ["m_familie", "m_gespraech", "couple"][randi() % 3]
	if randf() < 0.1:
		_next_look = {"bag": true}
	return kk


func spawn_kind(kind: String, from, to) -> Node3D:
	match kind:
		"m_familie":
			return _family(from, to)
		"m_gespraech":
			return _talk_group(from, to)
		"m_sitzen":
			return _sitting(from, to)
		"m_wc":
			return _wc_walk(from, to)
		"m_spazieren":
			return _stroll(from, to)
		"m_eilig":
			var rt := _cross(randf_range(7.0, 16.0))
			_next_look = {"gait": "run" if randf() < 0.5 else "hurry", "force": true}
			return main.spawn("person", from if from != null else rt[0], to if to != null else rt[1])
		"m_velo":
			var rt2 := _cross(randf_range(7.0, 14.0))
			_next_look = {"bike": true, "gait": "walk", "force": true, "pack": false}
			return main.spawn("person", from if from != null else rt2[0], to if to != null else rt2[1])
		"m_gangarten":
			_seq = ["walk", "hurry", "run", "sneak", "crawl"]
			_seq_v = null
			return null
	return main.spawn("person", from, to)


func _stroll(from, to) -> Node3D:
	var rt := _cross(randf_range(6.0, 16.0))
	_next_look = {"gait": "stroll", "force": true, "bag": randf() < 0.15}
	var v = main.spawn("person", from if from != null else rt[0], to if to != null else rt[1])
	var b: Vector3 = to if to != null else rt[1]
	var stop: Vector3 = main.free_spot(v.position.lerp(b, randf_range(0.35, 0.65)), 0.4, true)
	v.target = stop
	v.route = [[stop, randf_range(4.0, 14.0), 0.0, stop + Vector3(randf_range(-6, 6), 0, randf_range(-6, 6))], b]
	var e := _entry(v)
	e["pose"] = {"p": stop, "kind": ["look", "phone", "look"][randi() % 3]}
	e["curved"] = true
	return v


func _family(from, to) -> Node3D:
	"""two adults (or one), 1-3 children: the children run ahead, back, stop - the parents walk on"""
	var rt := _cross(randf_range(7.0, 15.0))
	var a: Vector3 = from if from != null else rt[0]
	var b: Vector3 = to if to != null else rt[1]
	_next_look = {"gait": "stroll", "force": true}
	var lead = main.spawn("person", a, b)
	lead.speed = randf_range(0.95, 1.15)
	lead.next_idle = lead.now_s() + randf_range(10.0, 25.0)
	var two := randf() < 0.75
	if two:
		_next_look = {"force": true, "gait": "stroll"}
		var p2 = main.spawn("person", a + Vector3(0.0, 0, 0.8), b)
		p2.leader = lead
		p2.follow_off = Vector3(0.75, 0, 0.1)
		p2.speed = lead.speed * 1.35
	var n_kids: int = randi_range(1, 1 if _lite() else 3)
	for i in range(n_kids):
		_next_look = {"force": true}
		var o := Vector3(randf_range(-1.2, 1.2), 0, randf_range(-1.5, 1.5))
		var k = main.spawn("child", a + o, b)
		k.leader = lead
		k.follow_off = o
		k.speed = lead.speed * 1.5
		var e := _entry(k)
		e["family"] = true
		e["off0"] = o
		e["fam_speed"] = k.speed
	stats["groups"] += 1
	return lead


func _talk_group(from, to) -> Node3D:
	"""3-5 people meet at a place in the picture, stand in a ring and talk for a while, then go their ways"""
	var n: int = randi_range(3, 3 if _lite() else 5)
	var c: Vector3 = from if from != null else main.free_spot(in_view(randf_range(8.0, 15.0), randf_range(-18.0, 18.0)), 0.8, true)
	var t_end: float = randf_range(40.0, 120.0)
	var first = null
	var a0 := randf() * TAU
	for i in range(n):
		var ang := a0 + TAU * float(i) / float(n) + randf_range(-0.2, 0.2)
		var rr := randf_range(0.65, 0.95)
		var spot: Vector3 = main.free_spot(c + Vector3(cos(ang), 0, sin(ang)) * rr, 0.3, true)
		var rt := _cross(Vector2(c.x - main.head.global_position.x, c.z - main.head.global_position.z).length())
		var st: Vector3 = rt[0] if i % 2 == 0 else rt[1]
		var ex: Vector3 = rt[1] if randf() < 0.5 else rt[0]
		_next_look = {"force": true, "gait": "walk"}
		var kind := "child" if randf() < m_kids * 0.5 else "person"
		var v = main.spawn(kind, st.lerp(c, randf_range(0.0, 0.3)), spot)
		var eta: float = v.position.distance_to(spot) / maxf(0.5, v.speed)
		v.route = [[spot, maxf(5.0, t_end - eta + randf_range(-6.0, 6.0)), 0.0, c], ex]
		v.next_idle = v.now_s() + 1.0e5
		var e := _entry(v)
		e["pose"] = {"p": spot, "kind": "talk"}
		e["curved"] = true
		if first == null:
			first = v
	stats["groups"] += 1
	return first


func _sitting(from, to) -> Node3D:
	"""1-3 people come with folding chairs, sit (evening: also at the grill / the table) and talk, then take the chairs away"""
	var n: int = randi_range(1, 2 if _lite() else 3)
	var c: Vector3 = from if from != null else main.free_spot(in_view(randf_range(7.0, 13.0), randf_range(-15.0, 15.0)), 1.0, true)
	var secs: float = randf_range(90.0, 240.0)
	var first = null
	for i in range(n):
		var ang := TAU * float(i) / float(maxi(n, 2)) + randf_range(-0.3, 0.3)
		var spot: Vector3 = main.free_spot(c + Vector3(cos(ang), 0, sin(ang)) * (0.9 if n > 1 else 0.0), 0.4, true)
		var rt := _cross(Vector2(c.x - main.head.global_position.x, c.z - main.head.global_position.z).length())
		_next_look = {"force": true, "gait": "stroll"}
		var st0: Vector3 = rt[0]
		var v = main.spawn("elderly" if randf() < 0.2 else "person", st0.lerp(c, 0.2), spot)
		var eta: float = v.position.distance_to(spot) / maxf(0.5, v.speed)
		var look: Vector3 = c if n > 1 else in_view(30.0, randf_range(-30.0, 30.0))
		v.route = [[spot, secs - eta + randf_range(-10.0, 10.0), 0.0, look], to if to != null else rt[0]]
		v.next_idle = v.now_s() + 1.0e5
		v.sit_seat = 0.05 if _lite() else 0.45
		var e := _entry(v)
		e["pose"] = {"p": spot, "kind": "sit"}
		e["curved"] = true
		if first == null:
			first = v
	stats["groups"] += 1 if n > 1 else 0
	return first


func _wc_walk(from, to) -> Node3D:
	"""to the toilet block and back: in the morning with towel and toilet bag, at night with a torch (or the phone light)"""
	var h: float = main.hour()
	var night: bool = main.is_dark()
	var rt := _cross(randf_range(6.0, 14.0))
	var a: Vector3 = from if from != null else rt[0]
	var wc: Vector3 = to if to != null else main.scenes.data.get("wc", rt[1])
	var lk := {"force": true, "gait": "hurry" if night or main.ambient < 8.0 else "walk"}
	if h >= 5.5 and h < 10.5:
		lk["bag"] = true
		lk["bag_kind"] = "towel"
	if night:
		var r := randf()
		lk["lamp"] = "torch" if r < 0.8 else ("phone" if r < 0.93 else "")
		lk["hood"] = randf() < 0.3
	_next_look = lk
	var v = main.spawn("person", a, wc)
	if v == null:
		return null
	v.route = [[wc, randf_range(60.0, 240.0) if not night else randf_range(90.0, 300.0), 0.0], a]
	v.next_idle = v.now_s() + 1.0e5
	return v


# ---- the scenario API ---------------------------------------------------------------------------------------------------
func busy(v) -> bool:
	var id: int = v.get_instance_id()
	return E.has(id) and (not E[id]["cur"].is_empty() or not E[id]["q"].is_empty())


func set_gait(v, g: String) -> void:
	stats["api"] += 1
	var e := _entry(v)
	if g == "stand":
		e["gait"] = "stand"
		v.wait_until = v.now_s() + 1.0e6
		return
	if e["gait"] == "stand":
		v.wait_until = 0.0
	if g == "":
		e["gait"] = ""
		v.hold_post = -1
		v._want_c = 0.0
		v._want_p = 0.0
		v._post_smooth = true
		return
	_pace(v, g)


func sneak_to(v, p, crawl_last := 0.0) -> void:
	_queue(v, {"do": "sneak", "p": p, "crawl": crawl_last})


func loiter(v, center, secs: float, radius := 4.0) -> void:
	_queue(v, {"do": "loiter", "p": center, "secs": secs, "r": radius})


func peek_into(v, p, secs := 5.0) -> void:
	_queue(v, {"do": "peek", "p": p, "secs": secs})


func hide_behind(v, p = null, secs := 8.0) -> void:
	_queue(v, {"do": "hide", "p": p, "secs": secs})


func come_back(v, after_s: float, center = null) -> void:
	_queue(v, {"do": "back", "p": center, "secs": after_s})


func avoid_light(v, on := true) -> void:
	stats["api"] += 1
	var e := _entry(v)
	e["avoid"] = on
	_lamp(v, not on)


func _queue(v, a: Dictionary) -> void:
	stats["api"] += 1
	var e := _entry(v)
	if a.get("p", null) == null and a["do"] in ["back"]:
		a["p"] = v.position
	e["q"].append(a)
	if e["cur"].is_empty():
		_start_next(e)


func _start_next(e: Dictionary) -> void:
	var v = e["v"]
	if e["saved"] == null:                                  # the old way, to go on with afterwards
		e["saved"] = {"target": v.target, "route": v.route.duplicate(true), "speed": v.speed, "post": v.hold_post, "gait": e["gait"]}
	if e["q"].is_empty():
		_restore(e)
		return
	var a: Dictionary = e["q"].pop_front()
	e["cur"] = a
	var pts := _points(v, a)
	if pts.is_empty():
		e["cur"] = {}
		_start_next(e)
		return
	var last = pts[-1]
	var lp: Vector3 = last[0] if typeof(last) == TYPE_ARRAY else last
	var post := float(last[2]) if typeof(last) == TYPE_ARRAY and last.size() > 2 else 0.0
	pts.append([lp, 1.0e6, post])                          # hold here: the end of the job (the next one starts from here)
	v.route = pts
	v.target = v.position
	v.wait_until = 0.0
	v.idle_until = 0.0
	v.next_idle = v.now_s() + 1.0e5
	v.leader = null


func _restore(e: Dictionary) -> void:
	var v = e["v"]
	var s = e["saved"]
	e["saved"] = null
	e["cur"] = {}
	if s == null:
		return
	v.hold_post = int(s["post"])
	v.speed = float(s["speed"])
	e["gait"] = str(s["gait"])
	v.route = s["route"]
	v.target = s["target"]
	v.wait_until = 0.0
	v.next_idle = v.now_s() + randf_range(6.0, 15.0)
	v._want_c = 1.0 if v.hold_post >= 1 else 0.0
	v._want_p = 1.0 if v.hold_post >= 2 else 0.0
	v._post_smooth = true
	if v.route.is_empty() and v.position.distance_to(v.target) < 0.5:
		v.target = _out_of_view(v.position)                 # nothing left to do: walk out of the picture (then it is gone)


func _points(v, a: Dictionary) -> Array:
	"""the route of one job ([point, wait, posture 0/1/2, look at] like actor.gd)"""
	var hp: Vector3 = main.head.global_position
	var pos: Vector3 = v.position
	var out := []
	match str(a["do"]):
		"sneak":
			var p: Vector3 = a["p"]
			v.speed = randf_range(0.95, 1.1)                  # × 0.6 crouched, × 0.3 crawling (actor._step)
			var e := _entry(v)
			e["gait"] = "sneak"
			var d := Vector2(p.x - pos.x, p.z - pos.z).length()
			var n: int = maxi(1, int(ceil(d / 2.2)))
			var side := Vector3(-(p - pos).z, 0, (p - pos).x).normalized()
			var cl: float = float(a.get("crawl", 0.0))
			for i in range(1, n + 1):
				var f := float(i) / float(n)
				var q: Vector3 = pos.lerp(p, f)
				if i < n:
					q += side * randf_range(-0.6, 0.6)
				q = main.free_spot(q, 0.35, true)
				var post := 2.0 if d * (1.0 - f) < cl or (cl > 0.0 and i == n) else 1.0
				out.append([q, 0.0, post])
				if i < n and randf() < 0.45:                 # stop and go: still, watching the camera
					out.append([q, randf_range(1.5, 5.0), post, hp])
			v.hold_post = 1
		"loiter":
			var c: Vector3 = a["p"]
			var r: float = float(a.get("r", 4.0))
			var left: float = float(a.get("secs", 30.0))
			v.speed = randf_range(0.7, 1.0)
			var e2 := _entry(v)
			e2["gait"] = "stroll"
			out.append(main.free_spot(c + Vector3(randf_range(-r, r), 0, randf_range(-r, r)) * 0.5, 0.4, true))
			while left > 0.0:
				var q: Vector3 = main.free_spot(c + Vector3(randf_range(-r, r), 0, randf_range(-r, r)), 0.4, true)
				var w := minf(left, randf_range(3.0, 12.0))
				var look: Vector3 = hp if randf() < 0.35 else c + Vector3(randf_range(-8, 8), 0, randf_range(-8, 8))
				out.append(q)
				out.append([q, w, 0.0, look])
				left -= w + q.distance_to(c) / 0.9
			e2["pose"] = {"p": null, "kind": "loiter"}
			v.hold_post = -1
		"peek":
			var p2: Vector3 = a["p"]
			var dirn := Vector3(pos.x - p2.x, 0, pos.z - p2.z)
			dirn = dirn.normalized() if dirn.length() > 0.1 else Vector3(1, 0, 0)
			var spot: Vector3 = main.free_spot(p2 + dirn * 0.8, 0.35, true)
			spot = main.free_spot(spot, 0.35, true)
			v.speed = randf_range(0.9, 1.15)
			e3_gait(v, "walk")
			out.append([spot, 0.0, 0.0])
			out.append([spot, float(a.get("secs", 5.0)), 0.0, p2])
			var e3 := _entry(v)
			e3["pose"] = {"p": spot, "kind": "bend"}
			v.hold_post = -1
		"hide":
			var at: Vector3 = a["p"] if a.get("p", null) != null else pos
			var spot2 = cover_spot(at)
			if spot2 == null:
				spot2 = main.free_spot(at, 0.4, true)
			v.speed = randf_range(1.6, 2.0)
			out.append([spot2, 0.0, 1.0])
			out.append([spot2, float(a.get("secs", 8.0)), 1.0, hp])
			var e4 := _entry(v)
			e4["gait"] = "sneak"
			v.hold_post = 1
		"back":
			var away := _out_of_view(pos)
			var c2: Vector3 = a["p"]
			v.speed = randf_range(1.2, 1.5)
			e3_gait(v, "walk")
			out.append(away)
			out.append([away, float(a.get("secs", 20.0)), 0.0])
			out.append(main.free_spot(c2, 0.4, true))
			v.hold_post = -1
	return out


func e3_gait(v, g: String) -> void:
	var e := _entry(v)
	e["gait"] = g


func cover_spot(at: Vector3):
	"""behind the nearest thing (seen from the head camera) within 12 m of at that is big and high enough to hide a crouching person"""
	var hp: Vector3 = main.head.global_position
	var best = null
	var bd := 1.0e9
	for o in main.obstacles:
		var c: Vector2 = o["c"]
		var ext: float = float(o["r"]) if o.has("r") else minf(o["h"].x, o["h"].y)
		if ext < 0.35 or float(o.get("ht", 3.0)) < 0.9:
			continue
		var d := Vector2(at.x, at.z).distance_to(c)
		var dc := Vector2(hp.x, hp.z).distance_to(c)
		if d > 12.0 or dc < 4.0 or d >= bd:
			continue
		var away := (c - Vector2(hp.x, hp.z)).normalized()
		var big: float = float(o["r"]) if o.has("r") else maxf(o["h"].x, o["h"].y)
		var q: Vector2 = c + away * (big + 0.55)
		best = Vector3(q.x, 0, q.y)
		bd = d
	return main.free_spot(best, 0.35, true) if best != null else null


# ---- light ---------------------------------------------------------------------------------------------------------------
func _lamp(v, on: bool) -> void:
	"""switched off = hidden (set_night of actor.gd only sets the energy, so it stays off)"""
	if v.lamp != null:
		v.lamp.visible = on
		v.lamp_mat.emission_enabled = on
	if v.torch != null:
		v.torch.visible = on                                   # (actor.gd sets the energy of the thief's torch every frame)


func lit_by_moveeye(v) -> bool:
	"""the white light of MoveEye shines on the person (dark, near, in front of the head)"""
	if not main.is_dark() or main.white_light == null or main.white_light.light_energy < 0.05:
		return false
	var hp: Vector3 = main.head.global_position
	var to: Vector3 = v.global_position - hp
	if to.length() > 18.0:
		return false
	var f: Vector3 = -main.cams[0].global_transform.basis.z
	return f.normalized().dot(to.normalized()) > cos(deg_to_rad(float(main.CAM_FOV[0]) * 0.5 + 8.0))


func _lamp_reach(p: Vector3) -> float:
	"""> 0: p is in the light of a lamp of the scene (how far inside, metres)"""
	if not main.is_dark():
		return 0.0
	var best := 0.0
	for l in main.lamps:
		if not is_instance_valid(l) or not (l is Light3D) or not l.is_visible_in_tree() or l.light_energy < 0.05:
			continue
		var r: float = (l.omni_range if l is OmniLight3D else (l.spot_range * 0.6 if l is SpotLight3D else 0.0)) * 0.55
		var g: Vector3 = l.global_position
		var d := Vector2(p.x - g.x, p.z - g.z).length()
		if d < r:
			best = maxf(best, r - d)
	return best


func _out_of_lamps(p: Vector3) -> Vector3:
	for l in main.lamps:
		if not is_instance_valid(l) or not (l is Light3D) or l.light_energy < 0.05:
			continue
		var r: float = (l.omni_range if l is OmniLight3D else (l.spot_range * 0.6 if l is SpotLight3D else 0.0)) * 0.55
		var g: Vector3 = l.global_position
		var dv := Vector2(p.x - g.x, p.z - g.z)
		if dv.length() < r:
			var n := dv.normalized() if dv.length() > 0.05 else Vector2(1, 0)
			var q := Vector2(g.x, g.z) + n * (r + 0.8)
			p = Vector3(q.x, p.y, q.y)
	return main.free_spot(p, 0.35, true)


# ---- every frame (a few times a second) -----------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or main.visitors == null:
		return
	_tick -= dt
	if _tick > 0.0:
		return
	_tick = 0.5 if _lite() else 0.2
	var t := now_s()
	var wet: bool = main.weather == "rain"
	var started_rain: bool = wet and not _rain
	_rain = wet
	for id in E.keys():
		var e: Dictionary = E[id]
		var v = e["v"]
		if not is_instance_valid(v) or v.is_queued_for_deletion() or v.done:
			if e.has("chair") and is_instance_valid(e["chair"]):
				e["chair"].queue_free()
			E.erase(id)
			continue
		_job(e, t)
		_poses(e, t)
		if e["avoid"]:
			_avoid(e, t)
		if not real() and e["cur"].is_empty():
			continue
		if started_rain and v.variant in ["", "elderly"] and randf() < 0.5 and not v.arm_hold.has(1):
			v.add_umbrella()                                     # the rain starts: the umbrella comes out
			_hold_umbrella(v)
			stats["umbrellas"] += 1
		if not e["curved"] and t > float(e.get("curve_t", 0.0)) and e["cur"].is_empty():
			_curve(e)
		if e["kid"] and e["cur"].is_empty():
			_kid(e, t)
		elif e["gait"] == "sneak" and e["cur"].is_empty() and t > float(e["next"]):
			e["next"] = t + randf_range(2.0, 5.0)              # sneaking gait without a job: stop and go
			if randf() < (0.25 if _lite() else 0.4) and t > v.wait_until:
				v.wait_until = t + randf_range(1.0, 4.0)
				v.dir = (main.head.global_position - v.position).normalized()
	_plan_tick(t)
	_seq_tick()


func _job(e: Dictionary, t: float) -> void:
	"""a job of the API is done when the figure stands at its hold point"""
	if e["cur"].is_empty():
		return
	var v = e["v"]
	var dd := Vector2(v.target.x - v.position.x, v.target.z - v.position.z).length()
	if t >= v.wait_until and t >= v.idle_until and dd > 0.3:                  # the point is not reachable (beside a tent, a car,
		if not e.has("near_t") or dd < float(e["near_d"]) - 0.25:             # behind a fence): no closer for 3 s (near) / 8 s = skip it
			e["near_t"] = t
			e["near_d"] = dd
		elif t - float(e["near_t"]) > (3.0 if dd < 1.3 else 8.0):
			e.erase("near_t")
			v._next_point(v.now_s())
	else:
		e.erase("near_t")
	if v.wait_until - t > 1.0e5 and v.route.is_empty():
		e["cur"] = {}
		if e["pose"].get("kind", "") in ["loiter", "bend"]:
			e["pose"] = {}
		_start_next(e)


func _poses(e: Dictionary, t: float) -> void:
	"""standing at a place of the route: sit / talk / bend / look round - the idle pose of actor.gd while it waits there"""
	var v = e["v"]
	var pz: Dictionary = e["pose"]
	if pz.is_empty():
		return
	var waiting: bool = t < v.wait_until and v.wait_until - t < 1.0e5
	var near: bool = pz.get("p", null) == null or v.position.distance_to(pz["p"]) < 0.8
	var k: String = str(pz["kind"])
	if waiting and near:
		if k == "loiter":                                     # look round, phone, towards the camera
			if t >= v.idle_until:
				v.idle_kind = ["look", "phone", "stare", "look"][randi() % 4]
				v.idle_until = minf(v.wait_until, t + randf_range(2.0, 5.0))
				v.look_yaw = randf_range(-1.0, 1.0)
			return
		if k == "talk" and t >= v.idle_until:
			v.look_yaw = randf_range(-0.5, 0.5)
			v.idle_kind = "talk" if randf() < 0.8 else ("phone" if randf() < 0.4 else "look")
			v.idle_until = minf(v.wait_until, t + randf_range(3.0, 8.0))
		elif k != "talk":
			v.idle_kind = k
			v.idle_until = v.wait_until
		if k == "sit" and not e["posed"] and not _lite():
			e["chair"] = _chair(v)
		e["posed"] = true
	elif e["posed"] and not waiting:
		e["posed"] = false
		if e.has("chair") and is_instance_valid(e["chair"]):
			e["chair"].queue_free()
		e.erase("chair")
		if k != "loiter":
			e["pose"] = {}


func _curve(e: Dictionary) -> void:
	"""nobody walks a ruler-straight line: a gentle bend through a point beside the way"""
	e["curved"] = true
	var v = e["v"]
	if v.leader != null or not v.route.is_empty() or v.target != e.get("to", Vector3.INF):
		return
	var d := Vector2(v.target.x - v.position.x, v.target.z - v.position.z).length()
	if d < 14.0:
		return
	var b: Vector3 = v.target
	var side := Vector3(-(b - v.position).z, 0, (b - v.position).x).normalized()
	var mid: Vector3 = main.free_spot(v.position.lerp(b, randf_range(0.35, 0.65)) + side * randf_range(-0.12, 0.12) * d, 0.4, true)
	v.route = [b]
	v.target = mid


func _kid(e: Dictionary, t: float) -> void:
	"""children: sprint, a sudden hook, stand still a moment, run ahead of the parents and back"""
	var v = e["v"]
	if t < float(e["next"]):
		if e.has("sprint_end") and t > float(e["sprint_end"]):
			e.erase("sprint_end")
			v.speed = float(e.get("fam_speed", e["base"]))
			if e.get("family", false):
				v.follow_off = e["off0"]
		return
	e["next"] = t + randf_range(1.5, 4.5) * (1.6 if _lite() else 1.0)
	var r := randf()
	if r < 0.4:
		e["sprint_end"] = t + randf_range(1.0, 2.5)
		if e.get("family", false) and v.leader != null:
			v.follow_off = Vector3(randf_range(-2.5, 2.5), 0, -randf_range(2.5, 5.0))   # runs ahead
			v.speed = minf(3.4, float(e["fam_speed"]) * 2.0)
		else:
			v.speed = randf_range(2.6, 3.5)
	elif r < 0.6 and v.leader == null and v.target.distance_to(v.position) > 3.0:
		v.route.push_front(v.target)                          # a hook to the side and on
		var side := Vector3(-(v.target - v.position).z, 0, (v.target - v.position).x).normalized()
		v.target = main.free_spot(v.position + (v.target - v.position).normalized() * 2.0 + side * randf_range(-2.5, 2.5), 0.3, true)
	elif r < 0.75 and v.leader == null:
		v.wait_until = t + randf_range(0.5, 1.5)
		v.idle_kind = "look" if randf() < 0.6 else "bend"
		v.idle_until = v.wait_until
		v.look_yaw = randf_range(-1.0, 1.0)


func _avoid(e: Dictionary, t: float) -> void:
	"""avoid_light: lamp off, the next point out of the light of the lamps, MoveEye's white light -> crouched to the side"""
	var v = e["v"]
	_lamp(v, false)
	if e.has("dodge_speed") and t < v.wait_until:          # in the dark again: back to the old pace
		v.speed = float(e["dodge_speed"])
		e.erase("dodge_speed")
	if typeof(v.target) == TYPE_VECTOR3 and _lamp_reach(v.target) > 0.0:
		v.target = _out_of_lamps(v.target)
	if t < float(e.get("lit_t", 0.0)) or not lit_by_moveeye(v):
		return
	e["lit_t"] = t + 10.0
	stats["lit_dodges"] += 1
	var hp: Vector3 = main.head.global_position
	var to: Vector3 = v.position - hp
	to.y = 0
	var side := Vector3(-to.z, 0, to.x).normalized()
	if randf() < 0.5:
		side = -side
	var dark: Vector3 = main.free_spot(v.position + side * 5.0 + to.normalized() * 3.0, 0.35, true)
	v.startle()
	v.route.push_front(v.target)
	v.route.push_front([dark, randf_range(6.0, 12.0), 1.0, hp])
	v.route.push_front([dark, 0.0, 1.0])
	v.target = v.position
	v.wait_until = 0.0
	e["dodge_speed"] = v.speed
	v.speed = maxf(v.speed, 1.8)


# ---- the day of a campsite ----------------------------------------------------------------------------------------------
func plan_pick(h: float) -> String:
	var w: Dictionary
	if h >= 6.5 and h < 9.5:
		w = {"m_wc": 0.55, "m_spazieren": 0.2, "m_eilig": 0.1, "m_familie": 0.05, "m_gespraech": 0.1}
	elif h >= 9.5 and h < 17.5:
		w = {"m_spazieren": 0.35, "m_familie": 0.2, "m_gespraech": 0.2, "m_wc": 0.1, "m_eilig": 0.08, "m_velo": 0.07}
	elif h >= 17.5 and h < 22.5:
		w = {"m_sitzen": 0.35, "m_gespraech": 0.2, "m_spazieren": 0.2, "m_wc": 0.15, "m_familie": 0.1}
	else:
		w = {"m_wc": 0.85, "m_spazieren": 0.15}
	if not m_groups:
		w.erase("m_familie")
		w.erase("m_gespraech")
	var tot := 0.0
	for k in w:
		tot += float(w[k])
	var r := randf() * tot
	for k in w:
		r -= float(w[k])
		if r <= 0.0:
			return k
	return "m_spazieren"


func _plan_tick(t: float) -> void:
	if not m_plan or not real() or not main.auto_visitors or main.busy_with() != "":
		return
	if not main.scene in PLAN_SCENES:
		return
	if t < _next_plan:
		return
	var h: float = main.hour()
	var night := h >= 22.5 or h < 6.0
	_next_plan = t + (randf_range(150.0, 360.0) if night else randf_range(40.0, 100.0)) / maxf(0.1, main.visit_rate) * (1.6 if _lite() else 1.0)   # Lite: fewer people
	if main.visitors.get_child_count() + 3 > main.max_visitors:
		return
	main.visit(plan_pick(h))


func _seq_tick() -> void:
	"""«Gangarten nacheinander»: the next one when the last one is gone"""
	if _seq.is_empty():
		return
	if _seq_v != null and is_instance_valid(_seq_v) and not _seq_v.done:
		return
	var g: String = _seq.pop_front()
	_seq_v = probe(g, 9.0, false, 0.0)


func probe(g: String, dist: float, dark_clothes: bool, off := 0.0) -> Node3D:
	"""tests (/control menschen probe, «Gangarten nacheinander»): one person crosses the picture at dist metres with gait g"""
	var half: float = float(main.CAM_FOV[0]) * 0.5
	var s := 1.0 if randf() < 0.5 else -1.0
	var span: float = half + (10.0 if g in ["sneak", "crawl"] else 22.0)
	var a: Vector3 = main.free_spot(in_view(dist / cos(deg_to_rad(span)), -s * span + off), 0.4, true)
	var b: Vector3 = main.free_spot(in_view(dist / cos(deg_to_rad(span)), s * span + off), 0.4, true)
	var lk := {"force": true, "gait": g}
	if dark_clothes:
		lk["jacket"] = DARK[0]
		lk["trousers"] = DARK[1]
		lk["hood"] = true
		lk["vest"] = false
		lk["lamp"] = ""
		lk["umbrella"] = false
	_next_look = lk
	var v = main.spawn("person", a, b)                      # «force»: the probe gets its gait even with «wie echt» off
	if v == null:
		return null
	var e := _entry(v)
	e["curved"] = true                                       # straight across (comparable)
	return v
