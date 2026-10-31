extends RefCounted
## «Abzeichen pro Szene» (Gameplay ausfeilen, Punkt 10, Daniel 31.10.2026): small goals per scene («Unsichtbar im vollen
## Campingplatz», «Velodieb-Profi» …) plus a few that go in every scene. Checked at the end of a round for every person
## (not the bots), kept PER DEVICE in user://spiel/szenen_ziele.json (scene -> goal -> how often, first time, by whom) and
## shown in the summary of the round (result line, winner screen, end card of the phone: «3 von 4 Zielen dieser Szene»).
## Separate and simple on purpose - the discovery book («entdecken», another branch) is not touched.

const T = preload("res://scripts/i18n.gd")
const FILE := "user://spiel/szenen_ziele.json"
const ALL := "_alle"                     # the goals of every scene
# [id, icon, name, how]
const GOALS := {
	"camping_voll": [["invisible", "👻", "Unsichtbar im vollen Campingplatz", "ins Ziel, nie erwischt, Verdacht nie über 40 %"]],
	"velodieb": [["bike_pro", "🚲", "Velodieb-Profi", "das Velo unbemerkt zum Ausgang bringen"]],
	"tarnen": [["camo", "🌿", "Tarn-Meister", "ins Ziel, nie erwischt, mindestens 20 s gekrochen"]],
	"camping": [["tent_sneak", "⛺", "Zeltplatz-Schleicher", "in unter 90 s ins Ziel, nie erwischt"]],
	"wald": [["forest", "🌲", "Waldläufer", "ins Ziel und mindestens 10 s in Verstecken"]],
	"garten": [["garden", "🌻", "Gartenzwerg", "ins Ziel, Verdacht nie über 30 %"]],
	"parkplatz": [["car", "🚗", "Parkplatz-Phantom", "ins Ziel, nie erwischt"]],
	"wild": [["wild", "🦌", "Wildhüter", "ins Ziel und mindestens 10 s gekrochen"]],
	"verstecken": [["bushes", "🌳", "Busch-Hüpfer", "mindestens 20 s in Verstecken"]],
	"bauernhof": [["farm", "🐄", "Hofgeist", "ins Ziel, nie erwischt"]],
	"seeufer": [["lake", "🛶", "Uferschleicher", "in unter 120 s ins Ziel"]],
	"baustelle": [["site", "🚧", "Bauzaun-Kletterer", "ins Ziel, nie erwischt"]],
	"stellplatz": [["camper", "🚐", "Wohnmobil-Wiesel", "in unter 100 s ins Ziel"]],
	"_alle": [["arrived", "🏁", "Angekommen", "einmal ins Ziel kommen"], ["clean", "✨", "Spurlos", "ins Ziel, nie erwischt"],
		["night", "🌙", "Nachtfalter", "nachts ins Ziel, nie erwischt"], ["mission", "🎒", "Auftrag erledigt", "eine Mission schaffen"],
		["quiet", "🤫", "Leise Sohle", "mit «Geräusche zählen» ohne ein Geräusch ins Ziel"]]}

var game
var main
var more
var fresh := {}                          # this round: name -> [[id, icon, name, new?]]


func on() -> bool:
	return more.on("game_badges")


func goals_here() -> Array:
	"""the goals of the scene now (own ones first, then the ones of every scene)"""
	return (GOALS.get(str(main.scene), []) as Array) + (GOALS[ALL] as Array)


func _db() -> Dictionary:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _save(d: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute("user://spiel")
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func _ok(id: String, p: Dictionary) -> bool:
	var goal: bool = p["state"] == "goal" or float(p.get("t_goal", 0.0)) > 0.0
	var clean := int(p.get("caught", 0)) == 0
	var secs: float = float(p.get("t_goal", 0.0)) - float(game.t_start) if goal else 1e9
	var ms: float = float(p.get("max_susp", 100.0))
	match id:
		"invisible":
			return goal and clean and ms <= 40.0
		"bike_pro":
			return not game.plus.theft.is_empty() and bool(game.plus.theft.get("stolen", false)) and str(game.plus.theft.get("thief", "")) == str(p["name"])
		"camo":
			return goal and clean and float(p.get("crawl_s", 0.0)) >= 20.0
		"tent_sneak":
			return goal and clean and secs < 90.0
		"forest":
			return goal and float(p.get("hide_s", 0.0)) >= 10.0
		"garden":
			return goal and ms <= 30.0
		"car", "farm", "site", "clean":
			return goal and clean
		"wild":
			return goal and float(p.get("crawl_s", 0.0)) >= 10.0
		"bushes":
			return float(p.get("hide_s", 0.0)) >= 20.0
		"lake":
			return goal and secs < 120.0
		"camper":
			return goal and secs < 100.0
		"arrived":
			return goal
		"night":
			return goal and clean and main.is_dark()
		"mission":
			return bool(p.get("ms_ok", false))
		"quiet":
			return goal and more.nacht.noise_on() and int(p.get("nz_n", 0)) == 0
	return false


func check(p: Dictionary) -> Array:
	"""game.end_round (gamemore.score_line) for one person: the goals reached in this round [[id, icon, name, new]]"""
	if not on() or p["role"] != "runner" or str(p.get("kind", "phone")) == "bot" or main.game_mode in ["free", "jaeger"]:
		return []
	var out := []
	var d := _db()
	var sc := str(main.scene)
	var mine: Dictionary = d.get(sc, {})
	for g in goals_here():
		if not _ok(str(g[0]), p):
			continue
		var e: Dictionary = mine.get(g[0], {"n": 0})
		var is_new := int(e["n"]) == 0
		e["n"] = int(e["n"]) + 1
		if is_new:
			e["first"] = Time.get_datetime_string_from_system(false, true)
			e["who"] = str(p["name"])
		mine[g[0]] = e
		out.append([g[0], g[1], T.t(g[2]), is_new])
	if not out.is_empty():
		d[sc] = mine
		_save(d)
		fresh[str(p["name"])] = out
	return out


func round_start() -> void:
	fresh.clear()


func progress() -> Dictionary:
	"""this scene: which goals are reached on this device (for the summary)"""
	var mine: Dictionary = _db().get(str(main.scene), {})
	var lst := []
	var n := 0
	for g in goals_here():
		var got := int((mine.get(g[0], {}) as Dictionary).get("n", 0)) > 0
		n += 1 if got else 0
		lst.append([g[1], T.t(g[2]), T.t(g[3]), got])
	return {"n": n, "of": lst.size(), "list": lst, "head": T.t("🏅 Abzeichen dieser Szene: %d von %d", [n, lst.size()])}


func line_for(got: Array) -> String:
	return " · ".join(PackedStringArray(got.map(func(b): return "%s %s%s" % [b[1], b[2], " (" + T.t("neu") + ")" if bool(b[3]) else ""])))


func lines() -> Array:
	if not on() or fresh.is_empty():
		return []
	var out := []
	for nm in fresh:
		out.append(T.t("🏅 %s: %s", [nm, line_for(fresh[nm])]))
	return out


func debug() -> Dictionary:
	return {"scene": main.scene, "fresh": fresh, "progress": progress(), "all": _db()}
