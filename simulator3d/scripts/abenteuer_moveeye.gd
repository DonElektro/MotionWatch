extends Node
## Paket A1 «MoveEye im Abenteuer: Lager, Wildkamera, seltene Tiere» (Abenteuer-Ausbau Kapitel 1–5, Daniel 31.10.2026).
## Ein Kind von bergtal_abenteuer.gd («ab»), dort nur mit kleinen Einhänge-Punkten (Suche nach «a1.» bzw. «A1.»).
##
## Was es macht:
##   * Am Lager wählt man, was MoveEye in der Nacht tut: «Lager bewachen» (Alarm weckt dich) oder «Wildkamera am Wildwechsel»
##     (still, keine Alarme, dafür gehen mehr Tiere vor der Kamera durch). Dazu: Proviant sichern (beim Rucksack lassen,
##     ins Zelt nehmen, aufhängen).
##   * In der Nacht (nachtlauf.gd, Zeitraffer): der Fuchs geht an den Proviant. Nicht gesichert und kein Alarm = Proviant weg.
##     Meldet MoveEye den Fuchs (echte Erkennung main.mw_det, siehe unten), bevor er beim Proviant ist, wachst du auf und
##     verscheuchst ihn. Tiere, die MoveEye meldet, werden fotografiert (Bild der Kopfkamera) und zählen für die Sammlung.
##     Eine Hinweis-Aufnahme: ein blinkendes Licht am Berg in Richtung des nächsten Kapitels (nur wenn MoveEye es aufnimmt).
##   * Wildkamera tagsüber: am Morgen MoveEye noch ein paar Stunden (Zeitraffer) stehen lassen - Murmeltier, Steinadler,
##     Bartgeier, Gämse und Steinbock in der Morgendämmerung.
##   * Aufnahmen auswerten: auf jeder Aufnahme bestimmt man selbst das Tier (3 Antworten); richtig = in der Sammlung.
##   * Sammlung seltener Tiere (7): Luchs, Steinbock, Gämse, Bartgeier, Steinadler, Murmeltier, Schneehase, mit Tageszeit und Ort.
##   * Wildkamera-Aufgaben (AUFGABEN): ein bestimmtes Tier an einem bestimmten Ort - der Wildhüter (Paket A2) kann sie vergeben.
##
## Erkennung = echte MoveEye-Ereignisse: ein Tier gilt als aufgenommen, wenn es für die Kopf- oder Wärmebildkamera sichtbar ist
## (testrun.visible / thermal_visible - dieselbe Wahrheit wie Nacht-Testlauf und Prüfstand) UND MoveEye im selben Moment etwas
## meldet (main.mw_det: persons > 0 oder present enthält motion / animal / warm / prealarm, nicht älter als 2 s). Ist MoveEye
## nicht verbunden, schätzt der Simulator (lange genug im Bild = aufgenommen) - die Aufnahme ist dann als «geschätzt» markiert.
##
## ---- Schnittstelle für andere Pakete -------------------------------------------------------------------------------------
##   const A1 = preload("res://scripts/abenteuer_moveeye.gd")
##   A1.foto_wertung(foto: Dictionary) -> {"tier": String, "schaerfe": float 0…1, "punkte": int}     (für A5 Bestenliste)
##       foto = ein Eintrag aus P["a1_fotos"] (siehe unten). Schärfe aus Abstand, Grösse im Bild, Bewegung während der
##       Belichtung, Licht (und, wenn das Bild da ist, dem Kontrast im Rahmen); Punkte = Seltenheit × Schärfe, × 0.7 wenn
##       MoveEye nicht selbst aufgenommen hat (geschätzt). Unabhängig davon, ob der Spieler das Tier richtig bestimmt hat.
##   A1.TIERE / A1.REIHE                -> die Sammlung (Name, Tageszeit, Ort, Tipp, Seltenheit)
##   ab.a1.sammlung() -> {tier: {...}}  ab.a1.fotos() -> Array    ab.a1.aufgaben() -> Array    ab.a1.aufgabe_geben(id)
##   Signal aufgabe_fertig(id)          (Wildhüter A2, Abzeichen A3)
## Spielstand (im bestehenden Abenteuer-Spielstand, Präfix a1_):
##   P["a1_fotos"]    [{id, tier, h, kapitel, modus (lager|wildwechsel|tag), ort, xz, dist, px, speed, licht, waerme, mw, quelle,
##                      bild (user://…png), box [x,y,w,h 0…1], kontrast, bestimmt ("" = noch nicht ausgewertet), falsch, datum}]
##   P["a1_sammlung"] {tier: {n, best (foto id), punkte, datum}}     P["a1_hinweise"] {"<kapitel>": {ziel, richtung, bild, mw}}
##   P["a1_aufgaben"] {id: "gegeben" | "erfuellt"}                   R["a1"] die laufende Nacht (modus, sichern, fuchs, licht …)
## Steuerbefehl: {"action": "abenteuer", "do": "a1", "was": state | modus (value) | sichern (value) | auswerten (id, tier) |
##               tag | sammlung (mit fotos) | wertung (id) | aufgabe (id) | reset}
## Gegenstände: über das Inventar von A4 (abenteuer_inventar.gd: hat / anzahl / nimm), solange es fehlt direkt R["items"].
## Lite: weniger und kleinere Aufnahmen, das Licht am Berg ohne echte Lichtquelle (Quality.lite()).

signal aufgabe_fertig(id)

const T = preload("res://scripts/i18n.gd")
const Bt = preload("res://scripts/bergtal.gd")
const D = preload("res://scripts/bergtal_abenteuer_daten.gd")
const Waerme = preload("res://scripts/waerme.gd")
const Quality = preload("res://scripts/quality.gd")

# ---- die Sammlung -------------------------------------------------------------------------------------------------------
# tier -> name, Tageszeit, Ort, Tipp, Seltenheit (Punkte für ein scharfes Bild), woran man es erkennt
const TIERE := {
	"luchs": {"name": "Luchs", "zeit": "nachts", "ort": "Wald und Waldrand", "selten": 100,
		"tipp": "Sehr scheu: MoveEye als Wildkamera am Wildwechsel, am besten in Waldnähe.", "merkmal": "Pinselohren, kurzer Schwanz mit schwarzer Spitze, gefleckt"},
	"steinbock": {"name": "Steinbock", "zeit": "Dämmerung", "ort": "Felsen und steile Hänge", "selten": 40,
		"tipp": "Lager nahe am Fels - abends oder früh am Morgen.", "merkmal": "lange, gebogene Hörner"},
	"gaemse": {"name": "Gämse", "zeit": "Dämmerung (nachts nah)", "ort": "Felsen und Geröll", "selten": 30,
		"tipp": "Am Fels und im Geröll; in der Nacht kommen sie nah ans Lager.", "merkmal": "kurze Hakenhörner, helles Gesicht mit dunklem Streifen"},
	"bartgeier": {"name": "Bartgeier", "zeit": "tagsüber", "ort": "Himmel über Grat und Fels", "selten": 80,
		"tipp": "Tagsüber über Felsen - am Morgen MoveEye als Wildkamera stehen lassen.", "merkmal": "riesig, rostroter Bauch, keilförmiger Schwanz"},
	"steinadler": {"name": "Steinadler", "zeit": "tagsüber", "ort": "Himmel über den Hängen", "selten": 60,
		"tipp": "Kreist tagsüber über den Hängen - Wildkamera am Morgen.", "merkmal": "dunkelbraun, breite Flügel mit «Fingern»"},
	"murmeltier": {"name": "Murmeltier", "zeit": "tagsüber", "ort": "Alpweiden und Blockfelder", "selten": 10,
		"tipp": "Häufig: tagsüber auf den Weiden (im Winter im Winterschlaf).", "merkmal": "rundlich, braun, kurzer Schwanz"},
	"schneehase": {"name": "Schneehase", "zeit": "Dämmerung und Nacht", "ort": "Weiden, Blockfelder, Waldgrenze", "selten": 15,
		"tipp": "Häufig: in der Dämmerung und nachts rund ums Lager.", "merkmal": "lange Ohren, im Winter ganz weiss"},
}
const REIHE := ["murmeltier", "schneehase", "gaemse", "steinbock", "steinadler", "bartgeier", "luchs"]
const EXTRA := {"fuchs": {"name": "Fuchs", "selten": 10, "merkmal": "rotbraun, buschiger Schwanz mit weisser Spitze"}}

# Wildkamera-Aufgaben: [id, tier, Text, x, z (Tal), Umkreis m (0 = überall), Modus ("" = egal)]
const AUFGABEN := [["a1_murmeltier_alp", "murmeltier", "Ein Murmeltier bei der Alp Tschuggen", 30.0, 22.0, 350.0, "tag"],
		["a1_schneehase_see", "schneehase", "Ein Schneehase am Gumpisee", -142.0, -332.0, 350.0, ""],
		["a1_gaemse_ruine", "gaemse", "Eine Gämse bei der Ruine Altstafel", -810.0, -230.0, 400.0, ""],
		["a1_steinbock_biwak", "steinbock", "Ein Steinbock beim Biwak Chüebodehorn", -512.0, 548.0, 400.0, ""],
		["a1_steinadler", "steinadler", "Ein Steinadler (Wildkamera am Tag)", 0.0, 0.0, 0.0, "tag"],
		["a1_bartgeier_grat", "bartgeier", "Ein Bartgeier oben beim Biwak", -512.0, 548.0, 600.0, "tag"],
		["a1_luchs", "luchs", "Der Luchs (Wildkamera am Wildwechsel, nachts)", 0.0, 0.0, 0.0, "wildwechsel"]]

# ---- die Kamera (wie testrun.visible: Kopfkamera 41° senkrecht, 540 Bildpunkte hoch) --------------------------------------
const VFOV := 41.0
const IMG_H := 540.0
# Belichtungszeit nach Licht (Schätzwerte: Kamera mit automatischer Belichtung - Tag kurz, Dämmerung länger, nachts mit
# Infrarot lang; Camera Module 3 / IMX708 kann bis 112 s belichten, für Bewegung nimmt man nachts typisch 1/15 … 1/5 s)
const EXPO := [[0.6, 1.0 / 500.0], [0.25, 1.0 / 60.0], [0.0, 1.0 / 10.0]]
const MELDET := ["motion", "animal", "warm", "prealarm", "person"]
const DIR := "user://bergtal_abenteuer"           # (= bergtal_abenteuer.DIR)
const ACC := Color(0.23, 0.55, 1.0)
const GRN := Color(0.3, 0.85, 0.45)
const ORG := Color(1.0, 0.62, 0.26)
const REDC := Color(1.0, 0.4, 0.35)

var ab                                   # bergtal_abenteuer.gd
var main
var _t := 0.0
var _seen := {}                          # actor instance id -> {vis, shot, now}
var _fuechse: Array = []
var _voegel: Array = []                  # {n: WeakRef, tier, vis, shot, span, v}
var _licht: Node3D = null
var _licht_t := 0.0
var _licht_vis := 0.0
var _vorgabe := {}                       # replay: the saved choice of the camp
var _tex := {}                           # bild path -> ImageTexture
var _tag_id := ""
var _show_all := false
var _rp := 0.0


static func _lite() -> bool:
	return Quality.lite()


# =======================================================================================================================
# Gegenstände: das Inventar von A4 (scripts/abenteuer_inventar.gd: hat / anzahl / nimm). Liegt die Datei noch nicht
# auf diesem Stand (vor dem Zusammenführen mit 2.98.94), gilt der Rucksack R["items"] direkt (proviant = «essen»).
# =======================================================================================================================
const INV_PATH := "res://scripts/abenteuer_inventar.gd"
const _ALT_ID := {"proviant": "essen", "feldstecher": "fernglas"}
static var _inv_s = null
static var _inv_tried := false


static func _inv():
	if not _inv_tried:
		_inv_tried = true
		if ResourceLoader.exists(INV_PATH):
			_inv_s = load(INV_PATH)
	return _inv_s


func hat(id: String) -> bool:
	var iv = _inv()
	if iv != null:
		return bool(iv.hat(id))
	if ab == null or ab.R.is_empty():
		return false
	return int((ab.R.get("items", {}) as Dictionary).get(_ALT_ID.get(id, id), 0)) > 0


func nimm(id: String, n := 999) -> int:
	"""nimmt bis n Stück aus dem Rucksack; gibt zurück, wie viele es waren"""
	var iv = _inv()
	if iv != null:
		var k := mini(int(iv.anzahl(id)), n)
		return k if k > 0 and bool(iv.nimm(id, k)) else 0
	if ab == null or ab.R.is_empty():
		return 0
	var it: Dictionary = ab.R.get("items", {})
	var key: String = _ALT_ID.get(id, id)
	var had := int(it.get(key, 0))
	var take := mini(had, n)
	if take > 0:
		it[key] = had - take
		if int(it[key]) <= 0:
			it.erase(key)
	return take


# =======================================================================================================================
# helpers
# =======================================================================================================================
func _a() -> Dictionary:
	if ab.R.is_empty():
		return {}
	if not ab.R.has("a1"):
		ab.R["a1"] = {"modus": "lager", "sichern": "offen", "fotos": [], "fuchs": "", "geweckt": 0, "licht": {}, "proviant_weg": false, "tag": {}}
	return ab.R["a1"]


func _pick() -> Dictionary:
	if not ab.R.has("a1_pick"):
		ab.R["a1_pick"] = {"modus": "lager", "sichern": "offen"}
	return ab.R["a1_pick"]


func _mw_da() -> bool:
	return main.now() - main.mw_t < 10.0


func _mw_meldet() -> bool:
	"""MoveEye meldet gerade etwas (die echte Erkennung, nicht älter als 2 s)"""
	if main.now() - main.mw_det_t > 2.0:
		return false
	if int(main.mw_det.get("persons", 0)) > 0:
		return true
	var pr = main.mw_det.get("present", [])
	if typeof(pr) == TYPE_ARRAY:
		for x in pr:
			if str(x) in MELDET:
				return true
	return false


static func tier_name(t: String) -> String:
	if TIERE.has(t):
		return str(TIERE[t]["name"])
	if EXTRA.has(t):
		return str(EXTRA[t]["name"])
	return t


static func kind_name(k: String) -> String:
	"""names of the night events of this package (bergtal_abenteuer._kind_name)"""
	var m := {"bt_lynx": "Luchs", "bt_ibex": "Steinbock", "a1_licht": "Licht am Berg", "a1_vogel_steinadler": "Steinadler",
			"a1_vogel_bartgeier": "Bartgeier"}
	if m.has(k):
		return m[k]
	if k.begins_with("a1_ww_"):
		return tier_name(k.substr(6))
	return k


func tier_of(a) -> String:
	if a == null or not is_instance_valid(a):
		return ""
	if a.has_meta("a1_tier"):
		return str(a.get_meta("a1_tier"))
	var bk := str(a.get_meta("berg_kind")) if a.has_meta("berg_kind") else ""
	match bk:
		"marmot":
			return "murmeltier"
		"snowhare":
			return "schneehase"
		"fox_food":
			return "fuchs"
		"lynx":
			return "luchs"
	match str(a.get("kind")):
		"lynx":
			return "luchs"
		"ibex":
			return "steinbock"
		"chamois":
			return "gaemse"
		"fox":
			return "fuchs"
	return ""


func _lebensraum(p: Vector2) -> Dictionary:
	"""what the camp is like for animals: forest (0 … 1), rock around (share of steep points within 40 m), altitude"""
	var h := Bt.H(p.x, p.y)
	var rock := 0
	for k in range(8):
		var q := p + Vector2(cos(TAU * k / 8.0), sin(TAU * k / 8.0)) * 40.0
		if Bt.slope_deg(q.x, q.y, 2.0) > 32.0:
			rock += 1
	return {"wald": clampf(Bt.forest_k(p.x, p.y, h), 0.0, 1.0), "fels": rock / 8.0, "alt": int(h + Bt.ALT0)}


func _ort_name() -> String:
	var spot := str(ab.R.get("camp_spot", "frei"))
	if Bt.SPOTS.has(spot):
		return str(Bt.SPOTS[spot][0])
	var p: Vector2 = ab.R.get("camp_xz", Vector2.ZERO)
	var best := ""
	var bd := INF
	for pl in Bt.PLACES:
		var d := p.distance_to(Vector2(float(pl[1]), float(pl[2])))
		if d < bd:
			bd = d
			best = str(pl[0])
	return best if bd < 400.0 else "Bergtal"


static func richtung(dx: float, dz: float) -> String:
	"""compass direction in the valley (x = east, z = south)"""
	var a := fposmod(rad_to_deg(atan2(dx, -dz)), 360.0)
	return ["Norden", "Nordosten", "Osten", "Südosten", "Süden", "Südwesten", "Westen", "Nordwesten"][int(round(a / 45.0)) % 8]


# =======================================================================================================================
# the camp (hook in set_camp) and the night plan (hook in night_plan)
# =======================================================================================================================
func on_camp() -> void:
	"""set_camp: take the choice of the camp into the run; securing the food takes a few minutes"""
	var a := _a()
	var pk := _pick()
	if ab.replaying and not _vorgabe.is_empty():
		pk["modus"] = str(_vorgabe.get("modus", "lager"))
		pk["sichern"] = str(_vorgabe.get("sichern", "offen"))
	a["modus"] = str(pk.get("modus", "lager"))
	var s := str(pk.get("sichern", "offen"))
	if not s in sichern_moeglich():
		s = "offen"
	a["sichern"] = s
	var mins: float = {"offen": 0.0, "zelt": 2.0, "haengen": 10.0}.get(s, 0.0)
	if mins > 0.0:
		main.set_hour(main.hour() + mins / 60.0)
	a["lr"] = _lebensraum(ab.R.get("camp_xz", Vector2.ZERO))


func sichern_moeglich() -> Array:
	var out := ["offen"]
	if ab.bed_of() in ["tent", "tent1"]:
		out.append("zelt")
	var mm: Array = ab.mounts()
	var baum := false
	for m2 in mm:
		if m2[0] == "baum" and m2[1]:
			baum = true
	if baum or hat("seil"):
		out.append("haengen")
	return out


func plan_extra(out: Array, r: RandomNumberGenerator, sp: float, speed: float) -> void:
	"""night_plan: the animals of this package and the hint light (from the night seed - same seed, same night)"""
	var a := _a()
	if a.is_empty():
		return
	_seen = {}
	_fuechse = []
	_voegel = []
	a["fotos"] = []
	a["fuchs"] = ""
	a["licht"] = {}
	var lr: Dictionary = a.get("lr", _lebensraum(ab.R.get("camp_xz", Vector2.ZERO)))
	var ww: bool = str(a["modus"]) == "wildwechsel"
	var add := func(kind: String, f: float, extra := {}):
		var e := {"kind": kind, "at_h": clampf(f, 0.04, 0.93) * sp}
		for k in extra:
			e[k] = extra[k]
		out.append(e)
	# the lynx: rare, at night, near the forest, more at the game trail
	if r.randf() < 0.08 + 0.3 * float(lr["wald"]) + (0.22 if ww else 0.0):
		add.call("a1_ww_luchs" if ww else "bt_lynx", r.randf_range(0.3, 0.75))
	# the ibex: rock, at dusk or at dawn
	if r.randf() < 0.15 + 0.6 * float(lr["fels"]):
		add.call("bt_ibex", r.randf_range(0.04, 0.12) if r.randf() < 0.5 else r.randf_range(0.86, 0.93))
	if ww:
		# the game trail: 2–4 animals cross in front of MoveEye (the habitat decides who)
		var wts := {"schneehase": 1.0, "gaemse": 0.4 + float(lr["fels"]), "steinbock": 0.15 + 0.8 * float(lr["fels"]), "fuchs": 0.6}
		for i in range(2 + r.randi() % 3):
			var tot := 0.0
			for k in wts:
				tot += float(wts[k])
			var x := r.randf() * tot
			for k in wts:
				x -= float(wts[k])
				if x <= 0.0:
					add.call("a1_ww_" + k, r.randf_range(0.08, 0.9))
					break
	# the hint: a light on the mountain towards the next chapter (not in the last chapter)
	if int(ab.R.get("chapter", 1)) < 5:
		add.call("a1_licht", r.randf_range(0.35, 0.7), {"dur_h": 40.0 * speed / 3600.0})
	_apply_food()


func _apply_food() -> void:
	var b = ab.bt()
	if b == null or b._food_node == null or not is_instance_valid(b._food_node):
		return
	match str(_a().get("sichern", "offen")):
		"zelt":
			b._food_node.visible = false                      # in the tent (the fox only smells it)
		"haengen":
			b._food_node.position.y += 1.7                    # hung on the tree / with the rope: out of reach
			b._food_node.rotation.z = 0.0


# =======================================================================================================================
# the events (nachtlauf.gd register_kind)
# =======================================================================================================================
func register_kinds() -> void:
	var n = main.nacht
	if n == null:
		return
	n.register_kind("bt_fox", _ev_fox, "animal", "fox")
	n.register_kind("bt_lynx", func(_e): return _ev_spawn("berg_lynx"), "animal", "lynx")
	n.register_kind("bt_ibex", func(_e): return _ev_spawn("berg_ibex"), "animal", "ibex")
	for t in ["luchs", "steinbock", "gaemse", "schneehase", "murmeltier", "fuchs"]:
		var tt: String = t
		n.register_kind("a1_ww_" + tt, func(_e): return _ev_wechsel(tt), "animal",
				{"luchs": "lynx", "steinbock": "ibex", "gaemse": "chamois", "schneehase": "hare", "murmeltier": "marmot", "fuchs": "fox"}[tt])
	n.register_kind("a1_vogel_steinadler", func(_e): return _ev_vogel("steinadler"), "animal", "eagle")
	n.register_kind("a1_vogel_bartgeier", func(_e): return _ev_vogel("bartgeier"), "animal", "vulture")
	n.register_kind("a1_licht", func(_e): return [], "weather", "light")       # weather: no body (the light is played here)


func _ev_spawn(kind: String) -> Array:
	var b = ab.bt()
	if b == null:
		return []
	var v = b.spawn_kind(kind)
	return [v] if v is Node else []


func _ev_fox(_ev) -> Array:
	"""the fox goes to the food bag (bergtal _at_food) - secured: it finds nothing"""
	var b = ab.bt()
	if b == null:
		return []
	var fn: Node3D = b._food_node
	var ok_fn := fn != null and is_instance_valid(fn)
	var keep := fn.visible if ok_fn else false
	if ok_fn and not bool(_a().get("proviant_weg", false)):
		fn.visible = true                                     # (the fox smells it even in the tent)
	var v = b.spawn_kind("berg_fox_food")
	if ok_fn:
		fn.visible = keep
	if not v is Node:
		return []
	v.set_meta("a1_tier", "fuchs")
	if str(_a().get("sichern", "offen")) != "offen":
		b._thieves = b._thieves.filter(func(x): return x[0] != v)
	_fuechse.append(v)
	return [v]


func _pfad(near: float, far: float) -> Array:
	"""a game trail across the picture of the head camera (global randf: nachtlauf seeds it per event)"""
	var b = ab.bt()
	var cam: Camera3D = main.cams[0]
	var o := cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	f = f.rotated(Vector3.UP, randf_range(-0.3, 0.3))
	var rr := Vector3(-f.z, 0, f.x)
	var d := randf_range(near, far)
	var side := 1.0 if randf() < 0.5 else -1.0
	var half := d * 0.8 + 8.0
	var p0 := o + f * d - rr * side * half
	var p1 := o + f * (d + randf_range(-3.0, 3.0)) + rr * side * half
	if b != null:
		p0.y = b.gy(p0.x, p0.z)
		p1.y = b.gy(p1.x, p1.z)
	return [p0, p1]


func _ev_wechsel(t: String) -> Array:
	var b = ab.bt()
	if b == null or main.cams.is_empty():
		return []
	var near: float = {"luchs": 12.0, "steinbock": 10.0, "gaemse": 10.0, "schneehase": 5.0, "murmeltier": 6.0, "fuchs": 6.0}[t]
	var pt := _pfad(near, near * 2.0)
	var v = null
	match t:
		"luchs":
			v = b.spawn_kind("berg_lynx", pt[0], pt[1])
		"schneehase":
			v = b.spawn_kind("berg_snowhare", pt[0], pt[1])
		"murmeltier":
			if str(ab.R.get("season", "")) == "winter":
				return []                                         # Winterschlaf
			v = b._marmot((pt[0] as Vector3).lerp(pt[1], 0.5))
		_:
			v = main.spawn({"steinbock": "ibex", "gaemse": "chamois", "fuchs": "fox"}[t], pt[0], pt[1])
			if v != null and t != "fuchs":
				v.speed *= 0.5
	if not v is Node:
		return []
	if t == "luchs" and str(v.get("kind")) != "lynx":
		return [v]                                            # (Kinder-Modus: a hare instead of the lynx)
	v.set_meta("a1_tier", t)
	return [v]


func _ev_vogel(t: String) -> Array:
	"""a big bird glides across the picture (40–90 m away, a bit above the horizon) - not an actor: watched here"""
	var b = ab.bt()
	if b == null or main.cams.is_empty():
		return []
	# Bartgeier (Gypaetus barbatus) Spannweite 2,6–2,9 m · Steinadler (Aquila chrysaetos) 1,9–2,3 m; Gleitflug ~10–15 m/s
	var vul := t == "bartgeier"
	var span := 2.8 if vul else 2.1
	var temp: float = Waerme.animal("vulture" if vul else "eagle", float(main.ambient), "body")
	var n: Node3D = b._bird_node(span, Color(0.62, 0.45, 0.32) if vul else Color(0.3, 0.22, 0.14), temp)
	b.s.root.add_child(n)
	var cam: Camera3D = main.cams[0]
	var o := cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var rr := Vector3(-f.z, 0, f.x)
	var d := randf_range(40.0, 90.0)
	var side := 1.0 if randf() < 0.5 else -1.0
	var half := d * 0.9 + 20.0
	var y := o.y + d * tan(deg_to_rad(randf_range(3.0, 14.0)))
	var p0 := o + f * d - rr * side * half
	var p1 := o + f * (d + randf_range(-10.0, 10.0)) + rr * side * half
	p0.y = maxf(y, b.gy(p0.x, p0.z) + 8.0)
	p1.y = maxf(y + randf_range(-4.0, 6.0), b.gy(p1.x, p1.z) + 8.0)
	var v := randf_range(10.0, 14.0)
	var dur := p0.distance_to(p1) / v
	var t0: float = main.now()
	var wr: WeakRef = weakref(n)
	n.position = p0
	n.look_at_from_position(p0, p1, Vector3.UP)
	main.anims.append(func(_dt, _tt):
		var bn = wr.get_ref()
		if bn == null:
			return true
		var k: float = (main.now() - t0) / maxf(1.0, dur)
		if k >= 1.0:
			bn.queue_free()
			return true
		bn.position = p0.lerp(p1, k) + Vector3(0, 2.0 * sin(k * PI * 2.0), 0)
		for w in ["wing_l", "wing_r"]:
			var wn = bn.get_node_or_null(w)
			if wn != null:
				wn.rotation.z = (0.06 if w == "wing_l" else -0.06) * sin((main.now() - t0) * 2.0)
		return false)
	_voegel.append({"n": wr, "tier": t, "vis": 0.0, "shot": false, "span": span, "v": v})
	return []


# =======================================================================================================================
# the night / the day run: who is in the picture, does MoveEye report it -> picture
# =======================================================================================================================
func _process(dt: float) -> void:
	if main == null or ab == null:
		return
	var n = main.nacht
	if n == null:
		return
	if not n.running:
		if _licht != null:
			_licht_aus()
		_tag_done(n)
		return
	if str(n.opts.get("by", "")) != "abenteuer" or ab.R.is_empty() or not ab.R.has("a1"):
		return
	_t -= dt
	if _t > 0.0:
		return
	_t = 0.25
	var meldet := _mw_meldet()
	var da := _mw_da()
	for id in n.active:
		for a in n.active[id]["actors"]:
			_sieh(a, meldet, da)
	for vg in _voegel:
		_sieh_vogel(vg, meldet, da)
	_fuchs_tick(meldet, da)
	_licht_tick(n, meldet, da)
	_rp += 0.25
	if ab.shown and ab.step == 7 and _rp >= 1.5:
		_rp = 0.0
		ab._changed()                                         # the bar of the day run


func _sieh(a, meldet: bool, da: bool) -> void:
	if not is_instance_valid(a) or a.is_queued_for_deletion():
		return
	var t := tier_of(a)
	if t == "":
		return
	var key: int = a.get_instance_id()
	var st: Dictionary = _seen.get(key, {"vis": 0.0, "shot": false, "now": false})
	var cam_v: bool = main.testrun.visible(a)
	var th_v: bool = (not cam_v) and main.testrun.thermal_visible(a)
	st["now"] = cam_v or th_v
	if cam_v or th_v:
		st["vis"] = float(st["vis"]) + 0.25
		if not bool(st["shot"]) and ((da and meldet) or (not da and float(st["vis"]) >= 1.5)):
			st["shot"] = true
			_foto(a, t, da, th_v)
		if t == "luchs" and bool(main.mw.get("lights", {}).get("white", false)) and da:
			a.scare()                                         # scheu: the white light of MoveEye chases it away
	_seen[key] = st


func _sieh_vogel(vg: Dictionary, meldet: bool, da: bool) -> void:
	var n = vg["n"].get_ref()
	if n == null or bool(vg["shot"]):
		return
	var cam: Camera3D = main.cams[0]
	var p: Vector3 = n.global_position
	if not cam.is_position_in_frustum(p):
		return
	var d: float = maxf(1.0, cam.global_position.distance_to(p))
	var px: float = float(vg["span"]) / (2.0 * d * tan(deg_to_rad(VFOV) / 2.0)) * IMG_H
	if px < 14.0 or main.game.light_at(p, 0) < 0.25:
		return
	vg["vis"] = float(vg["vis"]) + 0.25
	if (da and meldet) or (not da and float(vg["vis"]) >= 1.5):
		vg["shot"] = true
		_foto_at(str(vg["tier"]), p, float(vg["span"]) * 0.5, d, px, float(vg["v"]), da, false)


func _foto(a, t: String, mw: bool, thermal: bool) -> void:
	var cam: Camera3D = main.cams[0]
	var h: float = maxf(0.4, float(a.body_h) * 1.5)
	var d: float = maxf(0.5, cam.global_position.distance_to(a.global_position))
	var px: float = h / (2.0 * d * tan(deg_to_rad(VFOV) / 2.0)) * IMG_H
	_foto_at(t, a.global_position, h, d, px, float(a.cur_speed), mw, thermal)


func _foto_at(t: String, pos: Vector3, h: float, d: float, px: float, speed: float, mw: bool, thermal: bool) -> void:
	var a := _a()
	var lim := 8 if _lite() else 14
	if (a["fotos"] as Array).size() >= lim:
		return
	var cam: Camera3D = main.cams[0]
	var xz: Vector2 = ab.R.get("camp_xz", Vector2.ZERO)
	var nr := (a["fotos"] as Array).size() + 1
	var tag: bool = bool((a.get("tag", {}) as Dictionary).get("laeuft", false))
	var f := {"id": "%s_%s%d" % [str(ab.R["id"]), "t" if tag else "n", nr], "tier": t, "h": snappedf(main.hour(), 0.01), "kapitel": int(ab.R.get("chapter", 1)),
			"modus": "tag" if tag else str(a["modus"]), "ort": _ort_name(), "xz": [snappedf(xz.x, 0.1), snappedf(xz.y, 0.1)],
			"dist": snappedf(d, 0.1), "px": snappedf(px, 0.1), "speed": snappedf(speed, 0.01), "licht": snappedf(float(main.game.light_at(pos, 0)), 0.01),
			"waerme": thermal, "mw": mw, "quelle": "moveeye" if mw else "schaetzung", "bild": "", "box": _box(cam, pos, h), "kontrast": -1.0,
			"bestimmt": "", "falsch": 0, "datum": Time.get_datetime_string_from_system().substr(0, 16)}
	_bild(f)
	(a["fotos"] as Array).append(f)
	ab._diary("a1_foto", T.t("Aufnahme von MoveEye"), T.t("%s um %s (%s)") % [T.t(tier_name(t)), ab.hm(main.hour()), T.t("gemeldet von MoveEye") if mw else T.t("geschätzt")])
	ab._changed()


func _box(cam: Camera3D, pos: Vector3, h: float) -> Array:
	"""where the animal is in the picture (0 … 1)"""
	if cam.is_position_behind(pos):
		return [0.4, 0.4, 0.2, 0.2]
	var vp := cam.get_viewport().get_visible_rect().size
	var lo := cam.unproject_position(pos) / vp
	var hi := cam.unproject_position(pos + Vector3(0, h, 0)) / vp
	var hh := clampf(absf(lo.y - hi.y), 0.02, 1.0)
	var ww := hh * 1.4
	return [snappedf(clampf(lo.x - ww / 2.0, 0.0, 1.0), 0.001), snappedf(clampf(hi.y, 0.0, 1.0), 0.001), snappedf(ww, 0.001), snappedf(hh, 0.001)]


func _bild(f: Dictionary) -> void:
	"""the picture of the head camera (what MoveEye recorded) + the contrast in the frame (Laplace: blur and noise)"""
	if main.vps.is_empty():
		return
	var img: Image = (main.vps[0] as SubViewport).get_texture().get_image()
	if img == null or img.is_empty():
		return
	var bx: Array = f["box"]
	var w := img.get_width()
	var hgt := img.get_height()
	var rc := Rect2i(int(float(bx[0]) * w), int(float(bx[1]) * hgt), maxi(4, int(float(bx[2]) * w)), maxi(4, int(float(bx[3]) * hgt))).intersection(Rect2i(0, 0, w, hgt))
	if rc.size.x >= 4 and rc.size.y >= 4:
		var c := img.get_region(rc)
		var k := minf(1.0, 48.0 / maxf(c.get_width(), c.get_height()))
		if k < 1.0:
			c.resize(maxi(3, int(c.get_width() * k)), maxi(3, int(c.get_height() * k)), Image.INTERPOLATE_BILINEAR)
		f["kontrast"] = snappedf(_laplace(c), 0.01)
	var sw := 240 if _lite() else 320
	img.resize(sw, int(sw * float(hgt) / maxf(1.0, w)), Image.INTERPOLATE_BILINEAR)
	var dd: String = DIR + "/a1_fotos"
	DirAccess.make_dir_recursive_absolute(dd)
	var fn: String = dd + "/" + str(f["id"]) + ".png"
	if img.save_png(fn) == OK:
		f["bild"] = fn
		_tex[fn] = ImageTexture.create_from_image(img)


static func _laplace(c: Image) -> float:
	"""0 … 1: how much fine detail the frame has (variance of the Laplace filter on the brightness)"""
	var w := c.get_width()
	var h := c.get_height()
	var s := 0.0
	var s2 := 0.0
	var n := 0
	for y in range(1, h - 1):
		for x in range(1, w - 1):
			var l := 4.0 * c.get_pixel(x, y).get_luminance() - c.get_pixel(x - 1, y).get_luminance() - c.get_pixel(x + 1, y).get_luminance() \
					- c.get_pixel(x, y - 1).get_luminance() - c.get_pixel(x, y + 1).get_luminance()
			s += l
			s2 += l * l
			n += 1
	if n == 0:
		return 0.0
	var vr := s2 / n - (s / n) * (s / n)
	return clampf(sqrt(maxf(0.0, vr)) / 0.12, 0.0, 1.0)


func _fuchs_tick(meldet: bool, da: bool) -> void:
	var a := _a()
	var b = ab.bt()
	if b == null or str(a["fuchs"]) in ["geklaut", "verjagt"]:
		return
	var fn: Node3D = b._food_node
	var offen: bool = str(a["sichern"]) == "offen"
	for v in _fuechse:
		if not is_instance_valid(v) or v.done:
			continue
		if str(a["fuchs"]) == "":
			a["fuchs"] = "da" if offen else "gesichert"
		if not offen:
			continue
		if fn == null or not is_instance_valid(fn) or not fn.visible:
			a["fuchs"] = "geklaut"
			a["proviant_weg"] = true
			ab._diary("a1_fuchs", T.t("Der Fuchs"), T.t("Der Fuchs hat den Proviant geholt."))
			ab._say(T.t("Der Fuchs hat den Proviant geholt!"))
			return
		if str(a["modus"]) != "lager":
			continue                                          # Wildkamera: still, no alarm
		var st: Dictionary = _seen.get(v.get_instance_id(), {})
		if bool(st.get("now", false)) and (meldet or (not da and float(st.get("vis", 0.0)) >= 1.0)) and v.global_position.distance_to(fn.global_position) > 1.2:
			v.scare()
			b._thieves = b._thieves.filter(func(x): return x[0] != v)
			a["fuchs"] = "verjagt"
			a["geweckt"] = int(a["geweckt"]) + 1
			a["fuchs_mw"] = da
			ab._diary("a1_fuchs", T.t("Alarm von MoveEye"), T.t("MoveEye schlägt Alarm - du wachst auf und verscheuchst den Fuchs. Der Proviant ist noch da."))
			ab._say(T.t("MoveEye-Alarm: ein Fuchs am Rucksack! Du verscheuchst ihn."))
			return


# ---- the hint light ------------------------------------------------------------------------------------------------------
func _ziel() -> Array:
	"""where the next chapter goes: [name, x, z] (from the camp of the next chapter)"""
	var ch := int(ab.R.get("chapter", 1))
	if ch >= 5:
		return []
	var nx: Dictionary = D.CHAPTERS[ch]
	var c: Array = nx["camp"]
	var nm: String = str(Bt.SPOTS[c[0]][0]) if Bt.SPOTS.has(str(c[0])) else "Hinter dem Grat"
	return [nm, float(c[1]), float(c[2])]


func _licht_tick(n, meldet: bool, da: bool) -> void:
	var a := _a()
	var on := false
	for id in n.active:
		if str(n.active[id]["rec"]["kind"]) == "a1_licht":
			on = true
	if on and _licht == null and not (a["licht"] as Dictionary).has("gezeigt"):
		_licht_an()
	elif not on and _licht != null:
		_licht_aus()
	if _licht == null:
		return
	_licht_t += 0.25
	var mi = _licht.get_node_or_null("glow")
	if mi != null:
		mi.visible = fmod(_licht_t, 1.25) < 0.75                 # it blinks like a lantern that is swung
	var cam: Camera3D = main.cams[0]
	if not cam.is_position_in_frustum(_licht.global_position):
		return
	_licht_vis += 0.25
	var li: Dictionary = a["licht"]
	li["im_bild"] = true
	if not li.has("bild") and ((da and meldet) or (not da and _licht_vis >= 2.0)):
		li["mw"] = da
		li["h"] = snappedf(main.hour(), 0.01)
		var f := {"id": "%s_licht" % str(ab.R["id"]), "box": _box(cam, _licht.global_position, 4.0)}
		_bild(f)
		li["bild"] = str(f.get("bild", ""))
		ab._diary("a1_licht", T.t("Licht am Berg"), T.t("MoveEye hat ein blinkendes Licht am Berg aufgenommen."))
		ab._changed()


func _licht_an() -> void:
	var a := _a()
	var b = ab.bt()
	var zl := _ziel()
	if b == null or main.cams.is_empty() or zl.is_empty():
		a["licht"]["gezeigt"] = true
		return
	var cam: Camera3D = main.cams[0]
	var o := cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var tw: Vector3 = b.WG(float(zl[1]), float(zl[2]))
	var to := Vector3(tw.x - o.x, 0, tw.z - o.z)
	var delta := 0.0
	if to.length() > 1.0:
		delta = clampf(f.signed_angle_to(to.normalized(), Vector3.UP), -0.2, 0.2)   # in the picture, as near as it goes towards the goal
	var dir := f.rotated(Vector3.UP, delta)
	var p := Vector3.ZERO
	for s in range(40, 281, 10):                              # the first slope along the view = «am Berg»
		var q := o + dir * float(s)
		var gq: float = b.gy(q.x, q.z)
		if gq > o.y + float(s) * 0.03:
			p = Vector3(q.x, gq + 2.5, q.z)
			break
	if p == Vector3.ZERO:
		p = o + dir * 260.0
		p.y = b.gy(p.x, p.z) + 2.5
	if not cam.is_position_in_frustum(p):
		p = o + dir * 90.0
		p.y = maxf(b.gy(p.x, p.z) + 2.5, o.y + 3.0)
	_licht = Node3D.new()
	b.s.root.add_child(_licht)
	_licht.global_position = p
	var mi := MeshInstance3D.new()
	mi.name = "glow"
	var sm := SphereMesh.new()
	var r := clampf(o.distance_to(p) * 0.008, 0.5, 1.8)          # a lantern with its glow: a few pixels in the picture
	sm.radius = r
	sm.height = r * 2.0
	mi.mesh = sm
	var mt := StandardMaterial3D.new()
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mt.albedo_color = Color(1.0, 0.82, 0.45)
	mi.material_override = mt
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_licht.add_child(mi)
	if not _lite():
		var ol := OmniLight3D.new()
		ol.light_color = Color(1.0, 0.8, 0.45)
		ol.light_energy = 1.5
		ol.omni_range = 18.0
		_licht.add_child(ol)
	_licht_t = 0.0
	_licht_vis = 0.0
	var cxz: Vector2 = ab.R.get("camp_xz", Vector2.ZERO)
	a["licht"] = {"gezeigt": true, "ziel": zl[0], "richtung": richtung(float(zl[1]) - cxz.x, float(zl[2]) - cxz.y), "kapitel": int(ab.R.get("chapter", 1))}


func _licht_aus() -> void:
	if _licht != null and is_instance_valid(_licht):
		_licht.queue_free()
	_licht = null


# =======================================================================================================================
# the day run: MoveEye stays as a camera trap after the morning (Zeitraffer)
# =======================================================================================================================
func tag_start() -> Dictionary:
	var a := _a()
	var n = main.nacht
	if a.is_empty() or ab.step != 7 or n == null:
		return {"ok": false, "error": "only in the morning"}
	if n.running:
		return {"ok": false, "error": "a run is already going"}
	if not (a.get("tag", {}) as Dictionary).is_empty():
		return {"ok": false, "error": "already done"}
	ab._register_kinds()
	var from_h: float = main.hour() + 0.25
	var to_h: float = from_h + 5.0
	var minutes: float = 0.3 if ab.fast else 2.0
	var speed := clampf(5.0 * 3600.0 / (minutes * 60.0), 1.0, 240.0)
	var plan := _tag_plan(speed, 5.0)
	_seen = {}
	_fuechse = []
	_voegel = []
	a["fotos"] = []                                   # (the night pictures are already in P)
	var r: Dictionary = n.start({"scene": "bergtal", "from": from_h, "to": to_h, "speed": speed, "seed": int(ab.R.get("night_seed", 1)) + 7,
			"busy": "normal", "by": "abenteuer", "plan": plan, "free": true})   # («abenteuer»: a new run stops it)
	if not bool(r.get("ok", false)):
		return r
	_tag_id = str(r.get("run", {}).get("id", ""))
	a["tag"] = {"laeuft": true, "from": from_h, "to": to_h, "plan": plan.size()}
	ab._diary("a1_tag", T.t("Wildkamera am Tag"), T.t("MoveEye bleibt noch ein paar Stunden als Wildkamera stehen."))
	ab._changed()
	return {"ok": true, "plan": plan, "speed": speed}


func _tag_plan(speed: float, sp: float) -> Array:
	var r := RandomNumberGenerator.new()
	r.seed = int(ab.R.get("night_seed", 1)) + 77
	var lr: Dictionary = _a().get("lr", _lebensraum(ab.R.get("camp_xz", Vector2.ZERO)))
	var out := []
	var add := func(kind: String, f: float):
		out.append({"kind": kind, "at_h": f * sp})
	if str(ab.R.get("season", "")) != "winter":
		add.call("a1_ww_murmeltier", r.randf_range(0.2, 0.5))
		add.call("a1_ww_murmeltier", r.randf_range(0.5, 0.9))
	if r.randf() < 0.4:
		add.call("a1_ww_schneehase", r.randf_range(0.02, 0.1))
	if r.randf() < 0.45 + 0.4 * float(lr["fels"]):
		add.call("a1_ww_gaemse", r.randf_range(0.02, 0.15))
	if r.randf() < 0.25 + 0.6 * float(lr["fels"]):
		add.call("a1_ww_steinbock", r.randf_range(0.03, 0.18))
	if r.randf() < 0.75:
		add.call("a1_vogel_steinadler", r.randf_range(0.3, 0.8))
	if r.randf() < 0.3 + 0.4 * float(lr["fels"]) + (0.2 if int(lr["alt"]) > 2100 else 0.0):
		add.call("a1_vogel_bartgeier", r.randf_range(0.5, 0.9))       # Bartgeier: braucht Thermik (später Vormittag)
	out.sort_custom(func(x, y): return float(x["at_h"]) < float(y["at_h"]))
	var real_s := sp * 3600.0 / speed
	var gap := clampf(real_s / (out.size() + 2.0), 6.0, 30.0)
	var prev := -1000.0
	for i in range(out.size()):
		var e: Dictionary = out[i]
		e["at_s"] = clampf(maxf(float(e["at_h"]) * 3600.0 / speed, prev + gap), 4.0, real_s * 0.92)
		prev = float(e["at_s"])
		e["id"] = i + 1
		e["at_h"] = snappedf(float(e["at_s"]) * speed / 3600.0, 0.001)
	return out


func _tag_done(n) -> void:
	if ab.R.is_empty() or not ab.R.has("a1"):
		return
	var tg: Dictionary = ab.R["a1"].get("tag", {})
	if not bool(tg.get("laeuft", false)) or str(n.last.get("id", "")) != _tag_id:
		return
	tg["laeuft"] = false
	var fs: Array = ab.R["a1"]["fotos"]
	tg["fotos"] = fs.size()
	_in_p(fs)
	ab._diary("a1_tag", T.t("Wildkamera am Tag"), T.t("%d Aufnahmen - jetzt auswerten.") % fs.size())
	ab._save()
	ab._changed()


# =======================================================================================================================
# the morning (hook in _morning) and the collection
# =======================================================================================================================
func morning(res: Dictionary) -> void:
	var a := _a()
	if a.is_empty():
		return
	var xp := 0
	var out := {"modus": a["modus"], "sichern": a["sichern"], "fuchs": a["fuchs"], "fotos": (a["fotos"] as Array).size(), "hinweis": {}}
	if bool(a.get("proviant_weg", false)):
		var n := nimm("proviant")
		out["proviant_weg"] = n
		ab.R["stamina"] = float(ab.R["stamina"]) * 0.85            # no breakfast: a bit less strength
	elif str(a["fuchs"]) == "verjagt":
		xp += 20
	elif str(a["fuchs"]) == "gesichert":
		xp += 10
	_in_p(a["fotos"])
	xp += 5 * (a["fotos"] as Array).filter(func(x): return bool(x["mw"])).size()
	var li: Dictionary = a["licht"]
	if li.has("bild") and str(li["bild"]) != "":
		var hw := {"ziel": li["ziel"], "richtung": li["richtung"], "bild": li["bild"], "mw": li.get("mw", false), "h": li.get("h", 0.0)}
		var hs: Dictionary = ab.P.get("a1_hinweise", {})
		hs[str(li["kapitel"])] = hw
		ab.P["a1_hinweise"] = hs
		out["hinweis"] = hw
		xp += 40
		ab._diary("a1_licht", T.t("Der Hinweis"), T.t("Auf der Nachtaufnahme blinkt ein Licht im %s - dort liegt: %s. Da geht es weiter.") % [T.t(str(li["richtung"])), T.t(str(li["ziel"]))])
	elif li.has("gezeigt"):
		out["hinweis"] = {"verpasst": true, "im_bild": li.get("im_bild", false)}
	out["xp"] = xp
	ab.P["xp"] = int(ab.P.get("xp", 0)) + xp
	res["xp"] = int(res["xp"]) + xp
	res["level"] = ab.level()
	res["a1"] = out


func _in_p(fs: Array) -> void:
	var all: Array = ab.P.get("a1_fotos", [])
	var have := {}
	for f in all:
		have[str(f["id"])] = true
	for f in fs:
		if not have.has(str(f["id"])):
			all.append(f)
	# keep: all not yet evaluated + the best evaluated per animal + the newest (at most 80)
	if all.size() > 80:
		var best := {}
		for f in all:
			if str(f["bestimmt"]) != "":
				var t := str(f["tier"])
				if not best.has(t) or int(foto_wertung(f)["punkte"]) > int(foto_wertung(best[t])["punkte"]):
					best[t] = f
		all = all.filter(func(f): return str(f["bestimmt"]) == "" or best.get(str(f["tier"])) == f or all.find(f) >= all.size() - 40)
	ab.P["a1_fotos"] = all


func fotos() -> Array:
	return ab.P.get("a1_fotos", [])


func offen() -> Array:
	return fotos().filter(func(f): return str(f["bestimmt"]) == "")


func sammlung() -> Dictionary:
	return ab.P.get("a1_sammlung", {})


static func foto_wertung(foto: Dictionary) -> Dictionary:
	"""A5 (Bestenliste): which animal, how sharp (0 … 1), how many points. Physical model of the head camera: size in the picture,
	blur from moving during the exposure (EXPO), light; with the picture also its contrast in the frame (Laplace)."""
	var t := str(foto.get("tier", ""))
	var d := maxf(0.5, float(foto.get("dist", 10.0)))
	var px := float(foto.get("px", 30.0))
	var lt := float(foto.get("licht", 1.0))
	var expo := 1.0 / 10.0
	for e in EXPO:
		if lt >= float(e[0]):
			expo = float(e[1])
			break
	var fpx := IMG_H / (2.0 * tan(deg_to_rad(VFOV) / 2.0))          # focal length in pixels (≈ 721)
	var blur := float(foto.get("speed", 0.0)) * expo * fpx / d       # pixels of motion blur (sideways)
	var s_blur := 1.0 / (1.0 + blur / 3.0)
	var s_size := sqrt(clampf((px - 14.0) / (100.0 - 14.0), 0.0, 1.0))
	var s_light := clampf(lt / 0.6, 0.3, 1.0)
	var s := s_blur * (0.35 + 0.65 * s_size) * (0.5 + 0.5 * s_light)
	if bool(foto.get("waerme", false)):
		s *= 0.55                                                  # only in the thermal picture (80 × 62 px): a warm blob
	var k := float(foto.get("kontrast", -1.0))
	if k >= 0.0:
		s *= 0.85 + 0.15 * k
	s = snappedf(clampf(s, 0.0, 1.0), 0.01)
	var sel: float = float(TIERE[t]["selten"]) if TIERE.has(t) else float(EXTRA.get(t, {"selten": 5})["selten"])
	var p := int(round(sel * (0.25 + 0.75 * s) * (1.0 if bool(foto.get("mw", false)) else 0.7)))
	return {"tier": t, "schaerfe": s, "punkte": p}


func auswerten(id: String, tier: String) -> Dictionary:
	"""the player says which animal is on the picture: right = into the collection"""
	for f in fotos():
		if str(f["id"]) != id:
			continue
		if str(f["bestimmt"]) != "":
			return {"ok": true, "richtig": str(f["bestimmt"]) == str(f["tier"]), "schon": true}
		if tier != str(f["tier"]):
			f["falsch"] = int(f["falsch"]) + 1
			ab._changed()
			return {"ok": true, "richtig": false, "tipp": T.t(_merkmal(str(f["tier"])))}
		f["bestimmt"] = tier
		var w := foto_wertung(f)
		var xp := int(int(w["punkte"]) / (2 + int(f["falsch"])))
		var neu := false
		if TIERE.has(tier):
			var sm: Dictionary = sammlung()
			var e: Dictionary = sm.get(tier, {"n": 0, "best": "", "punkte": 0, "datum": ""})
			neu = int(e["n"]) == 0
			e["n"] = int(e["n"]) + 1
			if int(w["punkte"]) > int(e["punkte"]):
				e["punkte"] = int(w["punkte"])
				e["best"] = id
			if neu:
				e["datum"] = str(f["datum"])
				xp += 30
				ab._say(T.t("Neu in der Sammlung: %s!") % T.t(tier_name(tier)))
			sm[tier] = e
			ab.P["a1_sammlung"] = sm
		ab.P["xp"] = int(ab.P.get("xp", 0)) + xp
		var done := _aufgaben_pruefen(f)
		ab._save()
		ab._changed()
		return {"ok": true, "richtig": true, "neu": neu, "xp": xp, "wertung": w, "aufgaben": done}
	return {"ok": false, "error": "unknown picture"}


func _merkmal(t: String) -> String:
	return str(TIERE[t]["merkmal"]) if TIERE.has(t) else str(EXTRA.get(t, {"merkmal": ""})["merkmal"])


func _optionen(f: Dictionary) -> Array:
	"""three answers: the right one and two others (always the same for one picture)"""
	var r := RandomNumberGenerator.new()
	r.seed = str(f["id"]).hash()
	var others: Array = REIHE.duplicate() + ["fuchs"]
	others.erase(str(f["tier"]))
	var out := [str(f["tier"])]
	while out.size() < 3 and not others.is_empty():
		out.append(others.pop_at(r.randi() % others.size()))
	for i in range(out.size() - 1, 0, -1):
		var j := r.randi() % (i + 1)
		var x = out[i]
		out[i] = out[j]
		out[j] = x
	return out


# ---- Wildkamera-Aufgaben -------------------------------------------------------------------------------------------------
func aufgaben() -> Array:
	var st: Dictionary = ab.P.get("a1_aufgaben", {})
	var out := []
	for a in AUFGABEN:
		out.append({"id": a[0], "tier": a[1], "text": a[2], "x": a[3], "z": a[4], "r": a[5], "modus": a[6], "status": str(st.get(a[0], "offen"))})
	return out


func aufgabe_geben(id: String) -> void:
	"""Wildhüter (A2): gives a task (it shows as «vom Wildhüter»)"""
	var st: Dictionary = ab.P.get("a1_aufgaben", {})
	if str(st.get(id, "")) != "erfuellt":
		st[id] = "gegeben"
	ab.P["a1_aufgaben"] = st
	ab._save()
	ab._changed()


func _aufgaben_pruefen(f: Dictionary) -> Array:
	var st: Dictionary = ab.P.get("a1_aufgaben", {})
	var done := []
	var xz := Vector2(float(f["xz"][0]), float(f["xz"][1]))
	for a in AUFGABEN:
		if str(st.get(a[0], "")) == "erfuellt" or str(a[1]) != str(f["tier"]):
			continue
		if float(a[5]) > 0.0 and xz.distance_to(Vector2(float(a[3]), float(a[4]))) > float(a[5]):
			continue
		if str(a[6]) != "" and str(a[6]) != str(f["modus"]):
			continue
		st[a[0]] = "erfuellt"
		done.append(a[0])
		ab.P["xp"] = int(ab.P.get("xp", 0)) + 50
		ab._diary("a1_aufgabe", T.t("Wildkamera-Aufgabe erfüllt"), T.t(str(a[2])))
		aufgabe_fertig.emit(a[0])
	ab.P["a1_aufgaben"] = st
	return done


# =======================================================================================================================
# replay (hooks in situation / replay)
# =======================================================================================================================
func situation_add(s: Dictionary) -> void:
	var a: Dictionary = ab.R.get("a1", {})
	if not a.is_empty() and (str(a.get("modus", "lager")) != "lager" or str(a.get("sichern", "offen")) != "offen"):
		s["a1"] = {"modus": a["modus"], "sichern": a["sichern"]}      # (only when not the default: older situations keep their key)


func replay_from(s: Dictionary) -> void:
	_vorgabe = s.get("a1", {}) if s.get("a1", {}) is Dictionary else {}


# =======================================================================================================================
# the panel (hooks in _paint_camp, _paint_night, _paint_morning, _paint_chapter)
# =======================================================================================================================
func paint_camp() -> void:
	var pk := _pick()
	var gg: VBoxContainer = ab._group(T.t("MoveEye in der Nacht"))
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 10)
	gg.add_child(g)
	g.add_child(ab._card(T.t("Lager bewachen"), T.t("MoveEye schlägt Alarm und weckt dich - zum Beispiel, wenn ein Fuchs an den Rucksack geht."),
			str(pk["modus"]) == "lager", func(): op({"was": "modus", "value": "lager"})))
	g.add_child(ab._card(T.t("Wildkamera am Wildwechsel"), T.t("Still, ohne Alarm - dafür gehen mehr Tiere vor der Kamera durch. Den Proviant besser sichern!"),
			str(pk["modus"]) == "wildwechsel", func(): op({"was": "modus", "value": "wildwechsel"})))
	gg.add_child(ab._lab(T.t("Proviant:"), 14, Color.WHITE, false))
	var g2 := GridContainer.new()
	g2.columns = 3
	g2.add_theme_constant_override("h_separation", 10)
	gg.add_child(g2)
	var ok := sichern_moeglich()
	for o in [["offen", "Beim Rucksack lassen", "Schnell - aber ein Fuchs riecht ihn.", ""], ["zelt", "Ins Zelt nehmen", "Sicher (2 Min.).", "braucht ein Zelt"],
			["haengen", "Aufhängen", "An einen Baum oder mit dem Seil (10 Min.).", "kein Baum und kein Seil"]]:
		var k: String = o[0]
		g2.add_child(ab._card(T.t(o[1]), T.t(o[2]), str(pk["sichern"]) == k, func(): op({"was": "sichern", "value": k}), not k in ok, "" if k in ok else T.t(o[3])))
	var nx := _naechste_aufgabe()
	if not nx.is_empty():
		gg.add_child(ab._lab(T.t("Wildkamera-Aufgabe: %s") % T.t(str(nx["text"])), 12, Color(0.6, 0.66, 0.74)))


func _naechste_aufgabe() -> Dictionary:
	var lst := aufgaben()
	for a in lst:
		if str(a["status"]) == "gegeben":
			return a
	for a in lst:
		if str(a["status"]) == "offen":
			return a
	return {}


func paint_night(g: VBoxContainer) -> void:
	var a := _a()
	if a.is_empty():
		return
	var tx := T.t("MoveEye: Lager bewachen") if str(a["modus"]) == "lager" else T.t("MoveEye: Wildkamera (still)")
	tx += " · " + T.t("%d Aufnahmen") % (a["fotos"] as Array).size()
	g.add_child(ab._lab(tx, 13, Color(0.75, 0.8, 0.86)))
	match str(a["fuchs"]):
		"verjagt":
			g.add_child(ab._lab(T.t("Alarm: Fuchs am Rucksack - verscheucht."), 13, GRN))
		"geklaut":
			g.add_child(ab._lab(T.t("Der Fuchs hat den Proviant geholt."), 13, REDC))
	if (a["licht"] as Dictionary).has("bild"):
		g.add_child(ab._lab(T.t("MoveEye hat ein Licht am Berg aufgenommen!"), 13, Color(1.0, 0.85, 0.5)))


func paint_morning(body: VBoxContainer) -> void:
	var res: Dictionary = ab.R.get("result", {}).get("a1", {})
	var a := _a()
	if res.is_empty() or a.is_empty():
		return
	var g: VBoxContainer = ab._group(T.t("MoveEye am Lager"))
	g.add_child(ab._lab(T.t("Lager bewachen") if str(res["modus"]) == "lager" else T.t("Wildkamera am Wildwechsel"), 14, Color.WHITE))
	match str(res["fuchs"]):
		"verjagt":
			g.add_child(ab._lab(T.t("Der Fuchs kam an den Rucksack - MoveEye hat dich geweckt, du hast ihn verscheucht. Proviant gerettet!"), 13, GRN))
		"geklaut":
			g.add_child(ab._lab(T.t("Der Fuchs hat den Proviant geholt - kein Frühstück (etwas weniger Kraft)."), 13, REDC))
		"gesichert":
			g.add_child(ab._lab(T.t("Ein Fuchs hat am Lager geschnüffelt - der Proviant war gesichert."), 13, GRN))
		"da":
			g.add_child(ab._lab(T.t("Ein Fuchs war in der Nähe - der Proviant ist noch da."), 13, Color(0.75, 0.8, 0.86)))
		_:
			g.add_child(ab._lab(T.t("Kein Fuchs am Proviant heute Nacht."), 13, Color(0.6, 0.66, 0.74)))
	var hw: Dictionary = res.get("hinweis", {})
	if hw.has("bild"):
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		g.add_child(row)
		row.add_child(_thumb(str(hw["bild"]), Vector2(200, 120)))
		var tl: Label = ab._lab(T.t("Hinweis-Aufnahme: In der Nacht blinkt ein Licht am Berg, Richtung %s. Dort liegt: %s - da geht es im nächsten Kapitel weiter.") % [T.t(str(hw["richtung"])), T.t(str(hw["ziel"]))], 13, Color(1.0, 0.88, 0.6))
		tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(tl)
	elif bool(hw.get("verpasst", false)):
		g.add_child(ab._lab(T.t("In der Nacht war ein Licht am Berg - MoveEye hat es nicht aufgenommen.") if bool(hw.get("im_bild", false))
				else T.t("In der Nacht war irgendwo ein Licht - aber nicht im Bild von MoveEye."), 13, ORG))
	# the day run
	var tg: Dictionary = a.get("tag", {})
	if tg.is_empty():
		ab._btn(g, T.t("MoveEye tagsüber als Wildkamera stehen lassen (Zeitraffer, 2 Min.)"), func(): op({"was": "tag"}))
	elif bool(tg.get("laeuft", false)):
		var n = main.nacht
		ab._bar(g, T.t("Wildkamera"), float(n.elapsed()), maxf(1.0, float(n.total_s)), Color(0.45, 0.7, 0.4), ab.hm(main.hour()))
	else:
		g.add_child(ab._lab(T.t("Wildkamera am Tag: %d Aufnahmen.") % int(tg.get("fotos", 0)), 13, Color(0.75, 0.8, 0.86)))
	paint_auswerten(body)


func _thumb(path: String, sz: Vector2) -> TextureRect:
	var tr := TextureRect.new()
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.custom_minimum_size = sz
	if path != "":
		if not _tex.has(path) and FileAccess.file_exists(path):
			var img := Image.load_from_file(path)
			if img != null and not img.is_empty():
				_tex[path] = ImageTexture.create_from_image(img)
		tr.texture = _tex.get(path, null)
	return tr


func paint_auswerten(parent: Control) -> void:
	var of := offen()
	if of.is_empty():
		return
	var g: VBoxContainer = ab._group(T.t("Aufnahmen auswerten (%d offen) - welches Tier ist das?") % of.size(), parent)
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 10)
	fl.add_theme_constant_override("v_separation", 10)
	g.add_child(fl)
	for f in of.slice(0, 6):
		var vb := VBoxContainer.new()
		vb.custom_minimum_size = Vector2(200, 0)
		fl.add_child(vb)
		vb.add_child(_thumb(str(f["bild"]), Vector2(200, 120)))
		vb.add_child(ab._lab("%s · %s%s" % [ab.hm(float(f["h"])), T.t(str(f["ort"])), "" if bool(f["mw"]) else " · " + T.t("geschätzt")], 11, Color(0.62, 0.68, 0.76)))
		if int(f["falsch"]) > 0:
			vb.add_child(ab._lab(T.t("Nicht ganz - schau genau: %s") % T.t(_merkmal(str(f["tier"]))), 11, ORG))
		var hb := HFlowContainer.new()
		hb.add_theme_constant_override("h_separation", 6)
		vb.add_child(hb)
		for t in _optionen(f):
			var id := str(f["id"])
			var tt: String = t
			ab._btn(hb, T.t(tier_name(tt)), func(): op({"was": "auswerten", "id": id, "tier": tt}))
	if of.size() > 6:
		g.add_child(ab._lab(T.t("… und %d weitere") % (of.size() - 6), 12, Color(0.6, 0.66, 0.74)))


func paint_sammlung(parent: Control) -> void:
	var sm := sammlung()
	var n := 0
	for t in REIHE:
		if int(sm.get(t, {}).get("n", 0)) > 0:
			n += 1
	var g: VBoxContainer = ab._group(T.t("Sammlung seltener Tiere · %d von %d") % [n, REIHE.size()], parent)
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 8)
	fl.add_theme_constant_override("v_separation", 8)
	g.add_child(fl)
	var byid := {}
	for f in fotos():
		byid[str(f["id"])] = f
	for t in REIHE:
		var e: Dictionary = sm.get(t, {})
		var got := int(e.get("n", 0)) > 0
		var pc := PanelContainer.new()
		pc.custom_minimum_size = Vector2(150, 0)
		pc.add_theme_stylebox_override("panel", ab._box(Color(0.1, 0.16, 0.26) if got else Color(0.1, 0.12, 0.15), ACC if got else Color(0.2, 0.25, 0.32), 1, 12, 8))
		fl.add_child(pc)
		var vb := VBoxContainer.new()
		vb.add_theme_constant_override("separation", 4)
		pc.add_child(vb)
		vb.add_child(ab._lab(("✓ " if got else "") + T.t(tier_name(t)), 14, Color.WHITE if got else Color(0.7, 0.74, 0.8), false))
		if got and byid.has(str(e.get("best", ""))) and str(byid[str(e["best"])]["bild"]) != "":
			vb.add_child(_thumb(str(byid[str(e["best"])]["bild"]), Vector2(134, 80)))
			vb.add_child(ab._lab(T.t("%d Punkte · %d×") % [int(e["punkte"]), int(e["n"])], 11, GRN, false))
		else:
			vb.add_child(ab._lab(T.t(str(TIERE[t]["zeit"])) + " · " + T.t(str(TIERE[t]["ort"])), 11, Color(0.6, 0.66, 0.74)))
	var eb := Button.new()
	eb.text = ("▾ " if _show_all else "▸ ") + T.t("Tipps und Wildkamera-Aufgaben")
	eb.flat = true
	eb.alignment = HORIZONTAL_ALIGNMENT_LEFT
	eb.pressed.connect(func(): _show_all = not _show_all; ab._changed())
	g.add_child(eb)
	if _show_all:
		for t in REIHE:
			g.add_child(ab._lab("%s: %s" % [T.t(tier_name(t)), T.t(str(TIERE[t]["tipp"]))], 12, Color(0.75, 0.8, 0.86)))
		for a in aufgaben():
			var dn := str(a["status"]) == "erfuellt"
			g.add_child(ab._lab(("✓ " if dn else "○ ") + T.t(str(a["text"])) + (" (" + T.t("vom Wildhüter") + ")" if str(a["status"]) == "gegeben" else ""), 12,
					GRN if dn else Color(0.75, 0.8, 0.86)))
	paint_auswerten(parent)


# =======================================================================================================================
# control
# =======================================================================================================================
func op(d: Dictionary) -> Dictionary:
	var was := str(d.get("was", "state"))
	var out := {"ok": true}
	match was:
		"modus":
			var v := str(d.get("value", "lager"))
			_pick()["modus"] = v if v in ["lager", "wildwechsel"] else "lager"
			ab._changed()
		"sichern":
			var v2 := str(d.get("value", "offen"))
			_pick()["sichern"] = v2 if v2 in ["offen", "zelt", "haengen"] else "offen"
			ab._changed()
		"auswerten":
			out = auswerten(str(d.get("id", "")), str(d.get("tier", "")))
		"tag":
			out = tag_start()
		"sammlung":
			out = {"ok": true, "sammlung": sammlung(), "offen": offen().size(), "aufgaben": aufgaben(), "hinweise": ab.P.get("a1_hinweise", {}),
					"fotos": fotos().map(func(f): return {"id": f["id"], "tier": f["tier"], "bestimmt": f["bestimmt"], "mw": f["mw"], "wertung": foto_wertung(f)})}
		"wertung":
			out = {"ok": false}
			for f in fotos():
				if str(f["id"]) == str(d.get("id", "")):
					out = {"ok": true, "wertung": foto_wertung(f), "foto": f}
		"aufgabe":
			aufgabe_geben(str(d.get("id", "")))
		"reset":
			for k in ["a1_fotos", "a1_sammlung", "a1_hinweise", "a1_aufgaben"]:
				ab.P.erase(k)
			ab._save()
			ab._changed()
	out["a1"] = state()
	return out


func state() -> Dictionary:
	var a: Dictionary = ab.R.get("a1", {}) if not ab.R.is_empty() else {}
	return {"pick": ab.R.get("a1_pick", {}) if not ab.R.is_empty() else {}, "modus": a.get("modus", ""), "sichern": a.get("sichern", ""),
			"fuchs": a.get("fuchs", ""), "proviant_weg": a.get("proviant_weg", false), "fotos": (a.get("fotos", []) as Array).size(),
			"licht": a.get("licht", {}), "tag": a.get("tag", {}), "sammlung": sammlung().keys(), "offen": offen().size() if ab.P.size() > 0 else 0,
			"mw": _mw_da()}
