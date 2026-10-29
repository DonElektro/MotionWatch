extends PanelContainer
## The game wizard (from 3D-3.41): it lives here in the simulator. Step by step: game type -> goal -> difficulty (with
## the extras) -> start (summary, rules, QR code, players). MoveEye shows the same steps on its page and works them
## from afar (CONTROL action «gamewiz»: get, open, close, pick, set, next, back, last). The settings are the normal
## controls of the game; «Like last time» is kept in user://gamewiz_last.json.
## 3D-4.x: the wizard is THE place to set up a game. Three quick starts («Kinder · 5 Min.», «Familie», «Profis») set
## everything in one tap; all single options are under «Extras». The kids mode and «Mitspieler einladen» use the same
## presets (apply_preset). The panel card «Spiel» only has Öffnen / Start / Stopp / Assistent (the rest under «Experte»).

var main
var shown := false               # open (in this window and / or on the page of MoveEye)
var step := 0
var W := {}                      # the choice being made
var lvl := "normal"
var extras_open := false
var error := ""
var seq := 0                     # every change counts up: MoveEye repaints only when it changed

var steps_box: HBoxContainer
var body: VBoxContainer
var back_btn: Button
var next_btn: Button
var _painted := -1
var _qr_for := ""

const LAST := "user://gamewiz_last.json"
const Pics = preload("res://scripts/wizpics.gd")
var _tex := {}
const KEYS := ["game_mode", "game_goal", "game_level", "game_lives", "game_minutes", "game_items", "game_teams", "game_rescue", "game_stones",
		"game_cones", "game_powers", "game_spectate", "game_photos", "game_hides", "game_decoy", "game_night", "game_events", "game_checkpoints",
		"game_autohandicap", "game_tasks", "game_bots", "game_tutorial", "game_daily", "game_ghost", "game_heart", "game_botguard"]
const STEPS := ["Spielart", "Ziel", "Schwierigkeit", "Mitspieler & Start"]
const STEPS_JG := ["Spielart", "Lockvögel", "Dauer", "Mitspieler & Start"]    # 3D-4.x: «Fehlalarm-Jäger» has its own simple setup
const JG_TIME := [["3", "⏱", "3 Minuten", "Kurz – gut für Kinder und zum Ausprobieren."], ["5", "⏱", "5 Minuten", "Eine normale Runde."],
		["8", "⏱", "8 Minuten", "Lang – Zeit, viele Lockvögel zu testen."]]
# everything that has no use when the players are animals and things (set on «Fehlalarm-Jäger»)
const JG_FIXED := {"game_goal": "reach", "game_lives": "0", "game_items": 0, "game_teams": false, "game_rescue": false, "game_stones": false,
		"game_cones": false, "game_powers": false, "game_photos": false, "game_hides": 0, "game_decoy": false, "game_events": false,
		"game_checkpoints": 0, "game_autohandicap": false, "game_tasks": false, "game_tutorial": false, "game_daily": false, "game_ghost": false,
		"game_heart": false, "game_botguard": false}
# 3D-3.77: on the last step - who plays along
const PLAYER_OPTS := [["game_bots", "Computer-Spieler (Bots)", "select", 0, 0, "", false, [["0", "keine"], ["1", "1 Bot"], ["2", "2 Bots"], ["3", "3 Bots"]]],
		["game_botguard", "🤖 Bot-Wächter, wenn niemand Wächter sein will (Spielart «Wächter»)", "toggle", 0, 0, "", false],
		["game_tutorial", "Übungsrunde für alle: Schritt für Schritt erklärt, niemand wird erwischt (wer zum ersten Mal spielt, bekommt sie von selbst)", "toggle", 0, 0, "", true],
		["game_daily", "Tagesaufgabe: heute für alle dieselbe Szene, dasselbe Ziel, dieselben Startpunkte", "toggle", 0, 0, "", true],
		["game_ghost", "Geisterläufer: der eigene beste Weg läuft als Geist mit", "toggle", 0, 0, "", true],
		["game_heart", "Herzschlag, wenn die Kamera dich gleich sieht", "toggle", 0, 0, "", true]]
# 3D-3.90: four game types with a use for MoveEye first; the others (true = old) only with «Experte»
const MODES := [["mw", "🛡", "Gegen MoveEye", "Die echte Erkennung von MoveEye passt auf: Meldet sie eine Person, ist der erwischt, den die Kamera am besten sieht. Was MoveEye verpasst, kommt ins Training und auf die Karte der blinden Flecken."],
		["guard", "👮", "Wächter", "Ein Spieler ist Wächter – am Handy oder am PC: Er dreht den Kopf, schaltet das Licht ein und ruft «Erwischt!». Will niemand, passt der Bot-Wächter auf (zu zweit spielbar). Am Schluss das Duell: wer hat mehr erwischt, der Wächter oder MoveEye?"],
		["seek", "🙈", "Verstecken mit dem Rover", "Alle starten bei der Basis und verstecken sich 30 s lang. Der Fänger sieht nur die Kamera, fährt den Rover und drückt «Gefunden!». Wer die Basis berührt, rettet alle. Danach steht MoveEye wieder am alten Ort."],
		["free", "🧪", "Zonen-Check", "Ohne Erwischen: geh die Grenzen deiner Zonen und die Wege ums Zelt ab. Das Handy sagt laufend, ob MoveEye dich sieht – jede Stelle, wo es dich nicht meldet, kommt auf die Karte der blinden Flecken."],
		["jaeger", "🦊", "Fehlalarm-Jäger", "Ihr seid keine Menschen, sondern Fuchs, Katze, Ast im Wind, Lampe, Ballon … Schafft ihr es, dass MoveEye trotzdem «Person!» meldet? Jeder Fehlalarm gibt Punkte – und MoveEye lernt daraus. Nur mit MoveEye."],
		["camera", "🎥", "Alle gegen die Kamera (ältere Spielart)", "Wie «Gegen MoveEye», aber immer schätzt der Simulator, wer gesehen wird – auch wenn MoveEye verbunden ist.", true],
		["teamguard", "🔴🔵", "Team gegen Team (ältere Spielart)", "Wie «Wächter», aber ein ganzes Team bewacht und die Teams tauschen nach einer Runde.", true],
		["mwhand", "🕹", "Team gegen MoveEye", "Die Spieler schleichen mit dem Handy. Die Wächter sitzen an MoveEye: Sie drehen die echte Kamera mit dem Joystick auf der Live-Seite und drücken «Erwischt!».", true],
		["patrol", "🚜", "Patrouille", "MoveEye fährt auf dem Mover eine Route ab und schaut sich an jedem Punkt um. Die Spieler schleichen zum Ziel, während die Patrouille unterwegs ist.", true]]
const GOALS := [["reach", "🟢", "Zum Ziel schleichen", "Ziel: zum grünen Licht schleichen, ohne erwischt zu werden. Der Pfeil auf dem Handy zeigt den Weg."],
		["return", "💰", "Beute holen und zurückbringen", "Ziel: die Beute beim grünen Licht holen und zurück zum Start bringen."],
		["flag", "🚩", "Fahne erobern (zwei Teams)", "Ziel: zwei Teams. Holt die Fahne der anderen und bringt sie zur eigenen Basis. Wer mit der Fahne erwischt wird, verliert sie. Es gewinnt das Team mit mehr eroberten Fahnen (z. B. Rot 2 : 1 Blau)."],
		["sprint", "⏱", "Sprint (90 Sekunden)", "Für Kinder und kurze Runden: immer derselbe Parcours mit 3 Toren. Durch die Tore, dann ins Ziel – je schneller, desto mehr Punkte."]]
const LEVELS := [["easy", "🌱", "Anfänger", "Wächter leicht, unbegrenzte Leben, 8 Minuten, Sichtfeld der Kameras sichtbar."],
		["normal", "🎯", "Normal", "Wächter normal, 3 Leben, 5 Minuten."],
		["hard", "🔥", "Profis", "Wächter schwer, nur 1 Leben, 4 Minuten, kein Sichtfeld."]]
const LEVEL_SET := {"easy": {"game_level": "easy", "game_lives": "0", "game_minutes": 8, "game_cones": true},
		"normal": {"game_level": "normal", "game_lives": "3", "game_minutes": 5, "game_cones": false},
		"hard": {"game_level": "hard", "game_lives": "1", "game_minutes": 4, "game_cones": false}}
# [key, label, type, min, max, unit, extra]
const OPTIONS := [["game_minutes", "Dauer einer Runde", "range", 1, 15, " min", true], ["game_lives", "Leben", "select", 0, 0, "", true],
		["game_items", "Kristalle zum Sammeln", "range", 0, 6, "", true], ["game_teams", "Zwei Teams (Rot gegen Blau)", "toggle", 0, 0, "", true],
		["game_rescue", "Befreien (Erwischte warten in der Zelle)", "toggle", 0, 0, "", true], ["game_stones", "Steine werfen zum Ablenken", "toggle", 0, 0, "", true],
		["game_cones", "Sichtfeld der Kameras zeigen", "toggle", 0, 0, "", true], ["game_powers", "Power-ups: Tarnkappe (lila) und Turbo (gelb)", "toggle", 0, 0, "", true],
		["game_spectate", "Zuschauer-Kamera: fliegt selbst übers Spielfeld", "toggle", 0, 0, "", true],
		["game_photos", "📸 Erwischt-Fotos (Galerie am Schluss)", "toggle", 0, 0, "", true], ["game_hides", "🌳 Verstecke (Büsche, 8 s unsichtbar)", "range", 0, 6, "", true],
		["game_decoy", "🦆 Lockvogel erlaubt", "toggle", 0, 0, "", true], ["game_night", "🌙 Nacht-Runde mit Taschenlampen", "toggle", 0, 0, "", true],
		["game_events", "⛈ Zufallsereignisse (Gewitter, Hund, Auto)", "toggle", 0, 0, "", true], ["game_checkpoints", "🚩 Checkpoints (+150 Punkte je)", "range", 0, 3, "", true],
		["game_autohandicap", "🎯 Handicap für den Ersten der Rangliste", "toggle", 0, 0, "", true], ["game_tasks", "✅ Eine Aufgabe für jede Runde (Bonus)", "toggle", 0, 0, "", true]]
const LIVES := [["0", "unbegrenzt"], ["3", "3 Leben"], ["1", "1 Leben"]]
const EXTRAS_LABEL := ["Extras – Übungsrunde, Tagesaufgabe, Geist, Herzschlag", "Extras – Dauer, Leben, Kristalle, Teams, Steine, Fotos, Verstecke, Nacht, Ereignisse …"]
const RULES := {"tips": "Tipps: Ducken und Kriechen hilft. Im Dunkeln und hinter Dingen sieht euch die Kamera schlechter. Rennen hört das Mikrofon.",
		"rescue": "Befreien: Wer erwischt wird, wartet in der Zelle, bis ihn ein Teamkollege befreit.",
		"items": "Kristalle: Wer welche einsammelt, bekommt Extrapunkte.",
		"powers": "Power-ups: Die lila Kugel ist eine Tarnkappe (9 s fast unsichtbar), die gelbe ein Turbo (7 s schneller, aber lauter).",
		"lastmin": "Letzte Minute: Die Kamera passt dann besser auf – jetzt wird es spannend!",
		"photos": "📸 Erwischt-Fotos: Wer erwischt wird, sieht auf dem Handy das Bild der Kamera. Am Schluss gibt es eine Galerie.",
		"hides": "🌳 Verstecke: In einem Busch geduckt oder kriechend sieht dich die Kamera nicht – aber nur 8 Sekunden lang.",
		"decoy": "🦆 Lockvogel: Wer will, wählt auf dem Handy «Lockvogel». Er lässt sich absichtlich sehen, lockt die Kamera weg und holt Teampunkte.",
		"night": "🌙 Nacht-Runde: Es ist dunkel. Mit 🔦 siehst du mehr – aber die Kamera sieht dich auch.",
		"events": "⛈ Zufallsereignisse: Gewitter (man hört dich kaum), ein bellender Hund, ein Auto mit Scheinwerfern.",
		"cps": "🚩 Checkpoints: Leuchtende Ringe unterwegs geben je 150 Punkte.",
		"tasks": "🎯 Jede Runde hat eine Aufgabe, z. B. «nur kriechend ins Ziel» oder «nie über 50 % Verdacht». Wer sie schafft, bekommt Bonuspunkte.",
		"hc": "🎯 Handicap: Wer in der Rangliste vorne liegt, wird leichter gesehen und ist etwas langsamer.",
		"botguard": "🤖 Bot-Wächter: Will niemand Wächter sein, dreht ein Bot den Kopf und ruft «Erwischt!» – auch er kann sich täuschen lassen.",
		"level": "⭐ Stufen: Jede Runde gibt Erfahrungspunkte (Punkte, Abzeichen, Aufgabe, Tagesaufgabe). Höhere Stufen schalten Dinge für die eigene Figur frei.",
		"watch": "👀 Zuschauer machen mit: Sie tippen, wer durchkommt, und dürfen zwei Locksteine werfen.",
		"new": "🎓 Wer zum ersten Mal spielt, bekommt von selbst die Übungsschritte (gehen, ducken, kriechen, Stein, Busch).",
		"jg_how": "🦊 So geht's: Jeder wählt auf dem Handy einen Lockvogel und bewegt ihn vor der Kamera. Der Pfeil zeigt zur Kamera 📷. Die Dinge haben einen eigenen Knopf (Windstoss, Schwenken, Steigen, Fallen, Schwärmen).",
		"jg_score": "🎉 Punkte: Meldet MoveEye eine Person, obwohl nur dein Lockvogel im Bild ist, gibt es 100 Punkte (+50 für jeden neuen Lockvogel). Ist ein echter Mensch im Bild, zählt es nicht.",
		"jg_learn": "🧠 Jeder Fehlalarm wird ein Lernfall: MoveEye bekommt das Bild und die Lage (was, wie weit, Licht, Wetter) und lässt sich beim nächsten Mal weniger täuschen.",
		"jg_night": "🌙 Nacht-Runde: Lampen-Strahl und Insekten am Licht wirken im Dunkeln am besten.",
		"jg_nomw": "⚠ MoveEye ist gerade nicht verbunden. Ohne MoveEye zählt kein Fehlalarm – zuerst in MoveEye den Simulator verbinden."}
# 3D-4.x: the quick starts and the presets for the kids mode and «Mitspieler einladen» - every key of KEYS is set
const BASE := {"game_mode": "mw", "game_goal": "reach", "game_level": "normal", "game_lives": "3", "game_minutes": 5, "game_items": 3, "game_teams": false,
		"game_rescue": false, "game_stones": true, "game_cones": false, "game_powers": true, "game_spectate": true, "game_photos": true, "game_hides": 3,
		"game_decoy": true, "game_night": false, "game_events": true, "game_checkpoints": 0, "game_autohandicap": false, "game_tasks": true, "game_bots": "0",
		"game_tutorial": false, "game_daily": false, "game_ghost": true, "game_heart": true, "game_botguard": true}
const PRESETS := {"kids": {"game_mode": "mw", "game_level": "easy", "game_lives": "0", "game_minutes": 5, "game_cones": true, "game_events": false,
			"game_tasks": false, "game_decoy": false, "game_heart": false, "game_bots": "1", "game_items": 3, "game_hides": 4},
		"family": {"game_mode": "guard", "game_level": "normal", "game_lives": "3", "game_minutes": 5, "game_botguard": true, "game_autohandicap": true},
		"pro": {"game_mode": "mw", "game_level": "hard", "game_lives": "1", "game_minutes": 4, "game_powers": false, "game_items": 2, "game_hides": 2,
			"game_checkpoints": 2, "game_autohandicap": true},
		"kids_pc": {"game_mode": "camera", "game_level": "easy", "game_lives": "0", "game_minutes": 5, "game_cones": true, "game_events": false,
			"game_tasks": false, "game_decoy": false, "game_heart": false, "game_bots": "2", "game_tutorial": true, "game_hides": 4},
		"free": {"game_mode": "free", "game_lives": "0", "game_items": 0, "game_hides": 0, "game_powers": false, "game_events": false, "game_tasks": false,
			"game_decoy": false, "game_checkpoints": 0, "game_bots": "0", "game_botguard": false, "game_spectate": false, "game_photos": false}}
const QUICK := [["kids", "🧒", "Kinder · 5 Min.", "Leicht: unbegrenzte Leben, Sichtfeld sichtbar, Verstecke, 1 Bot läuft mit. Ohne Aufgaben und Zufallsereignisse."],
		["family", "👪", "Familie", "Einer ist Wächter (sonst der Bot-Wächter), 3 Leben, 5 Minuten, Aufgaben und Zufallsereignisse. Am Schluss das Duell gegen MoveEye."],
		["pro", "🔥", "Profis", "Gegen MoveEye, schwer: nur 1 Leben, 4 Minuten, Checkpoints, Handicap für den Ersten, keine Power-ups."]]
const LEVEL_OF := {"kids": "easy", "family": "normal", "pro": "hard", "kids_pc": "easy", "free": "normal"}


# ---- the model (the same for this window and for MoveEye) ------------------------------------------------------
func _cur() -> Dictionary:
	var o := {}
	for c in main.controls:
		if c.id in KEYS and c["get"] != null:
			o[c.id] = c["get"].call()
	o["game_lures"] = main.game.jaeger.allowed_str()        # «Fehlalarm-Jäger»: which lures (not a control of the card)
	return o


func _last():
	if not FileAccess.file_exists(LAST):
		return null
	var d = JSON.parse_string(FileAccess.get_file_as_string(LAST))
	return d if typeof(d) == TYPE_DICTIONARY else null


func open_wiz() -> void:
	W = _cur()
	W["game_lives"] = str(W.get("game_lives", "3"))
	lvl = str(W.get("game_level", "normal"))
	step = 0
	error = ""
	shown = true
	visible = true
	get_parent().move_child(self, -1)
	_changed()


func close_wiz() -> void:
	shown = false
	visible = false
	_changed()


func _changed() -> void:
	seq += 1
	_painted = -1


func _summary(c: Dictionary) -> String:
	var md := ""
	var gl := ""
	for m in MODES:
		if m[0] == str(c.get("game_mode", "")):
			md = m[2]
	for g in GOALS:
		if g[0] == str(c.get("game_goal", "")):
			gl = g[2]
	return "%s · %s · %d min" % [md, gl, int(c.get("game_minutes", 5))]


func _rules() -> Array:
	var out := []
	if jg():                                               # «Fehlalarm-Jäger»: its own short rules
		for m in MODES:
			if m[0] == "jaeger":
				out.append(m[3])
		out.append(RULES["jg_how"])
		out.append(RULES["jg_score"])
		out.append(RULES["jg_learn"])
		if W.get("game_night", false):
			out.append(RULES["jg_night"])
		if not main.game.jaeger.mw_on():
			out.append(RULES["jg_nomw"])
		out.append(RULES["level"])
		return out
	for m in MODES:
		if m[0] == str(W.get("game_mode")):
			out.append(m[3])
	for g in GOALS:
		if g[0] == str(W.get("game_goal")):
			out.append(g[3])
	out.append(RULES["tips"])
	for pair in [["game_rescue", "rescue"], ["game_items", "items"], ["game_powers", "powers"], ["game_powers", "lastmin"], ["game_photos", "photos"],
			["game_hides", "hides"], ["game_night", "night"], ["game_events", "events"], ["game_checkpoints", "cps"], ["game_tasks", "tasks"], ["game_autohandicap", "hc"]]:
		var v = W.get(pair[0], false)
		if (typeof(v) == TYPE_BOOL and v) or (typeof(v) != TYPE_BOOL and float(v) > 0.0):
			out.append(RULES[pair[1]])
	if W.get("game_decoy", false) and str(W.get("game_mode")) in ["camera", "mw"]:
		out.append(RULES["decoy"])
	if str(W.get("game_mode")) == "guard" and W.get("game_botguard", false):
		out.append(RULES["botguard"])
	out.append(RULES["new"])
	out.append(RULES["watch"])
	out.append(RULES["level"])
	return out


func preset(id: String) -> Dictionary:
	"""3D-4.x: a full set of settings (BASE + the preset)"""
	var d := BASE.duplicate()
	d.merge(PRESETS.get(id, {}), true)
	return d


func apply_preset(id: String, open_game := true) -> Array:
	"""3D-4.x: set everything of a preset at once (quick start, kids mode, «Mitspieler einladen»). Returns what failed."""
	var d := preset(id)
	var errs := []
	for k in KEYS:
		if d.has(k):
			var r: Dictionary = main.control_set(k, d[k])
			if not r.get("ok", false):
				errs.append(k)
	if open_game:
		main.game.set_open(true)
	return errs


func jg() -> bool:
	return str(W.get("game_mode", "")) == "jaeger"


func steps() -> Array:
	return STEPS_JG if jg() else STEPS


func _jg_list() -> Array:
	return Array(str(W.get("game_lures", "")).split(",", false))


func model() -> Dictionary:
	var g = main.game
	var cards := []
	var key := ""
	var title := ""
	var lead := ""
	var src := []
	match step:
		0:
			title = "Welches Spiel?"
			lead = "Bis zu 12 Spieler laufen mit dem Handy mit (einstellbar, Standard 6), weitere schauen zu. Wähle die Spielart – der Assistent erklärt die Regeln und stellt alles ein."
			key = "game_mode"
			src = MODES
		1:
			title = "Was ist das Ziel?"
			lead = "Sprint: 90 Sekunden, immer derselbe Parcours – gut für Kinder und kurze Runden."
			key = "game_goal"
			src = GOALS
		2:
			title = "Wie schwierig?"
			key = "_lvl"
			src = LEVELS
		3:
			title = "Bereit!"
	if jg() and step in [1, 2]:                            # «Fehlalarm-Jäger»: which lures, how long
		title = "Welche Lockvögel sind erlaubt?" if step == 1 else "Wie lange?"
		lead = "Tippe an, was mitmachen darf (mehrere möglich). Jeder Spieler wählt dann auf dem Handy seinen Lockvogel." if step == 1 else "Wie lange dauert eine Runde?"
		key = "game_lures" if step == 1 else "game_minutes"
		src = []
		if step == 1:
			for l in main.game.jaeger.LURES:
				src.append([l[0], l[1], l[2], l[4]])
		else:
			src = JG_TIME
	if jg() and not main.game.jaeger.mw_on():
		lead = (lead + "\n" if lead != "" else "") + RULES["jg_nomw"]
	for c in src:
		var on: bool = (lvl == c[0]) if key == "_lvl" else str(W.get(key, "")) == c[0]
		if key == "game_lures":
			on = c[0] in _jg_list()
		elif key == "game_minutes":
			on = int(W.get("game_minutes", 5)) == int(c[0])
		if key == "game_mode" and c.size() > 4 and bool(c[4]) and main.ui_simple and not on:
			continue                                       # 3D-3.90: the old game types only with «Experte»
		var tx: String = c[3]
		if key == "game_mode" and c[0] == "jaeger" and not main.game.jaeger.mw_on():
			tx += " ⚠ MoveEye ist gerade nicht verbunden."
		cards.append({"v": c[0], "icon": c[1], "title": c[2], "text": tx, "on": on, "pic": Pics.PICS.get(c[0], "")})
	var quick := []
	if step == 0:                                          # 3D-4.x: one tap - everything set
		for q in QUICK:
			quick.append({"v": q[0], "icon": q[1], "title": q[2], "text": q[3]})
	var opts := []
	if step == 2 or step == 3:
		for o in (OPTIONS if step == 2 else PLAYER_OPTS):
			if not W.has(o[0]):
				continue
			if jg() and not (o[0] in ["game_night", "game_bots"]):
				continue                                       # «Fehlalarm-Jäger»: only the night round and the bots
			if jg() and o[0] == "game_night":
				opts.append({"id": o[0], "label": "🌙 Nacht-Runde (Lampe und Insekten wirken besser)", "type": "toggle", "value": W[o[0]], "extra": false})
				continue
			if o[0] == "game_botguard" and str(W.get("game_mode")) != "guard":
				continue
			var d := {"id": o[0], "label": o[1], "type": o[2], "value": W[o[0]], "extra": o[6]}
			if o[2] == "range":
				d["min"] = o[3]
				d["max"] = o[4]
				d["unit"] = o[5]
			elif o[2] == "select":
				d["options"] = o[7] if o.size() > 7 else LIVES
			opts.append(d)
	var summary := []
	if step == 3:
		var md := ""
		var gl := ""
		for m in MODES:
			if m[0] == str(W.get("game_mode")):
				md = m[1] + " " + m[2]
		for x in GOALS:
			if x[0] == str(W.get("game_goal")):
				gl = x[1] + " " + x[2]
		summary = [["Spielart", md], ["Ziel", gl], ["Dauer einer Runde", "%d min" % int(W.get("game_minutes", 5))],
				["Leben", "unbegrenzt" if str(W.get("game_lives")) == "0" else str(W.get("game_lives"))], ["Kristalle", str(int(W.get("game_items", 0)))],
				["Teams", "Rot gegen Blau" if W.get("game_teams", false) else "nein"]]
		if jg():
			var ll := PackedStringArray()
			for l in main.game.jaeger.LURES:
				if l[0] in _jg_list():
					ll.append(l[1] + " " + l[2])
			summary = [["Spielart", md], ["Lockvögel", ", ".join(ll)], ["Dauer einer Runde", "%d min" % int(W.get("game_minutes", 5))],
					["Nacht-Runde", "ja" if W.get("game_night", false) else "nein"],
					["MoveEye", "✓ verbunden – entscheidet" if main.game.jaeger.mw_on() else "⚠ nicht verbunden – ohne MoveEye zählt nichts"]]
	var last = _last()
	var nl := "Weiter ›"
	if step == 3:
		nl = "▶ Runde starten" if g.open else "✓ Spiel öffnen & QR-Code zeigen"
	return {"ok": true, "shown": shown, "seq": seq, "step": step, "steps": steps(), "title": title, "lead": lead, "key": key, "cards": cards,
			"options": opts, "extras_open": extras_open, "summary": summary, "quick": quick, "quick_title": "Schnellstart – ein Tipp, alles eingestellt" if step == 0 else "",
			"own_title": "Oder selbst zusammenstellen:" if step == 0 else "",
			"extras_label": EXTRAS_LABEL[1] if step == 2 else (EXTRAS_LABEL[0] if step == 3 else ""),
			"pics": ([Pics.PICS.get(str(W.get("game_mode")), ""), "" if jg() else Pics.PICS.get(str(W.get("game_goal")), "")]) if step == 3 else [], "rules": _rules() if step == 3 else [],
			"last": _summary(last) if last != null and step == 0 else "", "error": error, "next": nl, "back": step > 0,
			"game": {"open": g.open, "url": g.address() if g.open else "", "players": g.count(), "round": g.round_state, "max": int(main.game_max)}}


func op(d: Dictionary) -> Dictionary:
	"""MoveEye (or this window) works the wizard"""
	var o := str(d.get("op", "get"))
	match o:
		"open":
			open_wiz()
		"close":
			close_wiz()
		"pick":
			_pick(str(d.get("key", "")), str(d.get("value", "")))
		"set":
			var k := str(d.get("key", ""))
			if W.has(k):
				var v = d.get("value")
				if typeof(W[k]) == TYPE_BOOL:
					v = bool(v)
				elif typeof(W[k]) in [TYPE_INT, TYPE_FLOAT]:
					v = float(v) if typeof(W[k]) == TYPE_FLOAT else int(float(v))
				else:
					v = str(v)
				W[k] = v
				_changed()
		"extras":
			extras_open = bool(d.get("value", not extras_open))
			_changed()
		"next":
			_next()
		"back":
			step = max(0, step - 1)
			_changed()
		"quick":                                        # 3D-4.x: a quick start - set, open the game, show the QR code
			var qv := str(d.get("value", ""))
			if PRESETS.has(qv):
				W = preset(qv)
				lvl = LEVEL_OF.get(qv, "normal")
				extras_open = false
				step = 3
				error = ""
				_apply()
		"last":
			var l = _last()
			if l != null:
				for k in l:
					if W.has(k) or k == "_lvl":
						W[k] = l[k]
				lvl = str(l.get("_lvl", lvl))
				step = 3
				_changed()
	return model()


func _pick(key: String, v: String) -> void:
	if key == "_lvl":
		lvl = v
		for k in LEVEL_SET.get(v, {}):
			if W.has(k):
				W[k] = LEVEL_SET[v][k]
	elif key == "game_lures":                              # «Fehlalarm-Jäger»: on / off, at least one stays
		var l := _jg_list()
		if v in l:
			if l.size() > 1:
				l.erase(v)
		elif v in main.game.jaeger.ALL:
			l.append(v)
		W["game_lures"] = ",".join(PackedStringArray(l))
	elif key == "game_minutes":
		W["game_minutes"] = clampi(int(v), 1, 15)
	elif W.has(key):
		W[key] = v
		if key == "game_mode" and v == "teamguard":
			W["game_teams"] = true
		if key == "game_goal" and v == "flag":
			W["game_teams"] = true
	_changed()


func _next() -> void:
	if step < 3:
		step += 1
		error = ""
		_changed()
		return
	var g = main.game
	if g.open:                                         # the game is open: take over the settings, start the round
		_apply()
		g.start_round()
		close_wiz()
		return
	_apply()


func _apply() -> void:
	"""take over the settings (and keep them for «Wie letztes Mal»), open the game"""
	var g = main.game
	var save := W.duplicate()
	save["_lvl"] = lvl
	var f := FileAccess.open(LAST, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(save))
	var errs := []
	if jg():                                               # «Fehlalarm-Jäger»: the extras of the other games off, the lures
		W.merge(JG_FIXED, true)
		g.jaeger.set_allowed(str(W.get("game_lures", "")))
	for k in KEYS:
		if W.has(k):
			var r: Dictionary = main.control_set(k, W[k])
			if not r.get("ok", false):
				errs.append(k)
	g.set_open(true)
	if not g.open:
		errs.append("Spiel öffnen")
	error = ("⚠ Nicht übernommen: " + ", ".join(PackedStringArray(errs))) if not errs.is_empty() else ""
	_changed()


# ---- in this window (3D-3.77: clearer and animated) ------------------------------------------------------------------
var prog: Control                 # the steps: dots on a line, the line fills up
var _prog_f := 0.0                # 0 .. 3, animated
var _pulse := 0.0
var _last_step := -1
var _slide: MarginContainer
var _hover_tw := {}
const ACC := Color(0.23, 0.55, 1.0)
const GRN := Color(0.3, 0.85, 0.45)
const ORG := Color(1.0, 0.62, 0.26)


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	offset_left = 60
	offset_top = 40
	offset_right = -440
	offset_bottom = -40
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.075, 0.095, 0.97)
	sb.set_corner_radius_all(16)
	sb.set_content_margin_all(16)
	sb.border_color = Color(0.2, 0.27, 0.35)
	sb.set_border_width_all(1)
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 18
	add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	add_child(v)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 10)
	v.add_child(top)
	var logo: Control = load("res://scripts/mw_logo.gd").new()
	logo.custom_minimum_size = Vector2(30, 30)
	top.add_child(logo)
	var t := Label.new()
	t.text = "Spiel-Assistent"
	t.add_theme_font_size_override("font_size", 19)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(t)
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.tooltip_text = "Schliessen (Esc)"
	x.pressed.connect(close_wiz)
	top.add_child(x)
	prog = Control.new()
	prog.custom_minimum_size = Vector2(0, 54)
	prog.draw.connect(_draw_prog)
	prog.mouse_filter = Control.MOUSE_FILTER_STOP
	prog.gui_input.connect(_prog_input)
	v.add_child(prog)
	steps_box = HBoxContainer.new()                  # kept for compatibility (not shown)
	steps_box.visible = false
	v.add_child(steps_box)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	_slide = MarginContainer.new()
	_slide.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(_slide)
	body = VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 10)
	_slide.add_child(body)
	var nav := HBoxContainer.new()
	nav.add_theme_constant_override("separation", 8)
	v.add_child(nav)
	back_btn = Button.new()
	back_btn.text = "‹ Zurück"
	back_btn.custom_minimum_size = Vector2(110, 40)
	back_btn.pressed.connect(func(): op({"op": "back"}))
	nav.add_child(back_btn)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nav.add_child(sp)
	next_btn = Button.new()
	next_btn.custom_minimum_size = Vector2(200, 40)
	next_btn.pressed.connect(func(): op({"op": "next"}))
	if main.UI.has_method("primary"):
		main.UI.primary(next_btn)
	nav.add_child(next_btn)
	visible = false


func _unhandled_key_input(ev: InputEvent) -> void:
	if visible and ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		close_wiz()
		get_viewport().set_input_as_handled()


func _process(dt: float) -> void:
	if visible != shown:
		visible = shown
		if shown:                                         # a little pop when it opens
			pivot_offset = size / 2.0
			scale = Vector2(0.96, 0.96)
			modulate.a = 0.0
			var tw := create_tween().set_parallel(true)
			tw.tween_property(self, "scale", Vector2.ONE, 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			tw.tween_property(self, "modulate:a", 1.0, 0.18)
	if not visible:
		return
	_pulse += dt
	_prog_f = move_toward(_prog_f, float(step), dt * 4.0)
	prog.queue_redraw()
	var g = main.game
	var sig: int = seq * 100 + (1 if g.open else 0) * 10 + mini(9, g.count())
	if sig != _painted:
		_painted = sig
		_paint()


func _draw_prog() -> void:
	"""the steps as dots on a line: done = green tick, now = blue and pulsing, later = grey"""
	var w := prog.size.x
	var ST := steps()
	var n := ST.size()
	var x0 := 40.0
	var x1 := w - 40.0
	var y := 16.0
	prog.draw_line(Vector2(x0, y), Vector2(x1, y), Color(0.2, 0.25, 0.32), 4.0, true)
	var xf := lerpf(x0, x1, _prog_f / float(n - 1))
	prog.draw_line(Vector2(x0, y), Vector2(xf, y), ACC, 4.0, true)
	var font := get_theme_default_font()
	for i in range(n):
		var x := lerpf(x0, x1, float(i) / float(n - 1))
		var c := GRN if i < step else (ACC if i == step else Color(0.25, 0.3, 0.37))
		if i == step:
			var r := 13.0 + 3.0 * (0.5 + 0.5 * sin(_pulse * 4.0))
			prog.draw_circle(Vector2(x, y), r, Color(ACC, 0.25))
		prog.draw_circle(Vector2(x, y), 11.0, c)
		var mark := "✓" if i < step else str(i + 1)
		prog.draw_string(font, Vector2(x - 12, y + 5), mark, HORIZONTAL_ALIGNMENT_CENTER, 24, 13, Color.WHITE)
		prog.draw_string(font, Vector2(x - 70, y + 32), ST[i], HORIZONTAL_ALIGNMENT_CENTER, 140, 12, Color.WHITE if i == step else Color(0.62, 0.68, 0.76))


func _prog_input(ev: InputEvent) -> void:
	"""click on a step that is done: back to it"""
	if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
		var n := STEPS.size()
		var i := clampi(int(round((ev.position.x - 40.0) / max(1.0, prog.size.x - 80.0) * (n - 1))), 0, n - 1)
		if i < step:
			step = i
			error = ""
			_changed()


static func plain(t: String) -> String:
	"""without emoji (the font of the window does not have them on every PC); MoveEye shows them"""
	var o := ""
	for i in range(t.length()):
		var c := t.unicode_at(i)
		if c >= 0x2600 and c != 0x2715 or c == 0xFE0F or c == 0x200D:
			continue
		o += String.chr(c)
	return o.strip_edges()


func _lab(t: String, sz := 14, col := Color(0.85, 0.88, 0.92), wrap := true) -> Label:
	var l := Label.new()
	l.text = plain(t)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if wrap else TextServer.AUTOWRAP_OFF
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	return l


func _box(bg: Color, border: Color, bw := 1, r := 12, pad := 12) -> StyleBoxFlat:
	var b := StyleBoxFlat.new()
	b.bg_color = bg
	b.border_color = border
	b.set_border_width_all(bw)
	b.set_corner_radius_all(r)
	b.set_content_margin_all(pad)
	return b


func _card(c: Dictionary, k: String) -> PanelContainer:
	"""a choice: picture, title, text; chosen = blue frame and «✓ gewählt»; the mouse over it: a little bigger"""
	var pc := PanelContainer.new()
	pc.custom_minimum_size = Vector2(190, 0)
	pc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var on: bool = c["on"]
	pc.add_theme_stylebox_override("panel", _box(Color(0.1, 0.16, 0.26) if on else Color(0.1, 0.12, 0.15), ACC if on else Color(0.2, 0.25, 0.32), 2 if on else 1, 14, 12))
	pc.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(v)
	if not _tex.has(c["v"]):
		_tex[c["v"]] = Pics.texture(c["v"], 0.8)
	if _tex[c["v"]] != null:
		var tr := TextureRect.new()
		tr.texture = _tex[c["v"]]
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.custom_minimum_size = Vector2(0, 96)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(tr)
	var tl := _lab(c["title"], 16, Color.WHITE)
	tl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tl)
	var tx := _lab(c["text"], 12, Color(0.65, 0.7, 0.78))
	tx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tx)
	if on:
		var ok := _lab("✓ gewählt", 12, GRN, false)
		ok.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(ok)
	var vv: String = c["v"]
	pc.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			var tw := pc.create_tween()
			pc.pivot_offset = pc.size / 2.0
			tw.tween_property(pc, "scale", Vector2(0.96, 0.96), 0.06)
			tw.tween_property(pc, "scale", Vector2.ONE, 0.1)
			tw.tween_callback(func(): op({"op": "pick", "key": k, "value": vv})))
	pc.mouse_entered.connect(func():
		pc.pivot_offset = pc.size / 2.0
		pc.create_tween().tween_property(pc, "scale", Vector2(1.03, 1.03), 0.12))
	pc.mouse_exited.connect(func(): pc.create_tween().tween_property(pc, "scale", Vector2.ONE, 0.12))
	return pc


func _group(title: String) -> VBoxContainer:
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", _box(Color(0.09, 0.11, 0.14), Color(0.18, 0.22, 0.28), 1, 12, 12))
	body.add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	pc.add_child(v)
	if title != "":
		v.add_child(_lab(title, 14, Color(0.62, 0.68, 0.76), false))
	return v


func _option_row(o: Dictionary, parent: Control) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var l := _lab(o["label"], 14)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	var id: String = o["id"]
	match o["type"]:
		"range":
			var s := HSlider.new()
			s.min_value = o["min"]
			s.max_value = o["max"]
			s.step = 1
			s.value = float(o["value"])
			s.custom_minimum_size = Vector2(160, 0)
			var vl := _lab("%d%s" % [int(o["value"]), o["unit"]], 14, Color(1, 1, 1))
			vl.custom_minimum_size = Vector2(54, 0)
			var unit: String = o["unit"]
			s.value_changed.connect(func(x): vl.text = "%d%s" % [int(x), unit]; W[id] = int(x) if typeof(W[id]) == TYPE_INT else float(x); seq += 1; _painted = seq * 100 + (1 if main.game.open else 0) * 10 + mini(9, main.game.count()))
			row.add_child(s)
			row.add_child(vl)
		"toggle":
			var cb := CheckButton.new()
			cb.button_pressed = bool(o["value"])
			cb.toggled.connect(func(x): W[id] = x; seq += 1; _painted = seq * 100 + (1 if main.game.open else 0) * 10 + mini(9, main.game.count()))
			row.add_child(cb)
		"select":
			var ob := OptionButton.new()
			var opts: Array = o.get("options", LIVES)
			for i in range(opts.size()):
				ob.add_item(opts[i][1])
				if str(opts[i][0]) == str(o["value"]):
					ob.select(i)
			ob.item_selected.connect(func(i): W[id] = (int(opts[i][0]) if typeof(W[id]) == TYPE_INT else str(opts[i][0])); seq += 1; _painted = seq * 100 + (1 if main.game.open else 0) * 10 + mini(9, main.game.count()))
			row.add_child(ob)


func _paint() -> void:
	var M := model()
	for c in body.get_children():
		c.queue_free()
	if error != "":
		body.add_child(_lab(error, 13, Color(1.0, 0.55, 0.45)))
	body.add_child(_lab(M["title"], 22, Color(1, 1, 1)))
	if M["lead"] != "":
		body.add_child(_lab(M["lead"], 13, Color(0.6, 0.66, 0.74)))
	if not M["quick"].is_empty():                       # 3D-4.x: the three quick starts, big
		body.add_child(_lab(M["quick_title"], 15, Color(1, 1, 1), false))
		var qg := GridContainer.new()
		qg.columns = 3
		qg.add_theme_constant_override("h_separation", 10)
		body.add_child(qg)
		for q in M["quick"]:
			var qb := Button.new()
			qb.text = plain(q["title"]) + "\n" + plain(q["text"])
			qb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			qb.custom_minimum_size = Vector2(190, 92)
			qb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			if main.UI.has_method("primary"):
				main.UI.primary(qb)
			var qv: String = q["v"]
			qb.pressed.connect(func(): op({"op": "quick", "value": qv}))
			qg.add_child(qb)
		body.add_child(_lab(M["own_title"], 13, Color(0.6, 0.66, 0.74), false))
	if M["last"] != "":
		var lb := Button.new()
		lb.text = plain("Wie letztes Mal: " + M["last"])
		lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lb.pressed.connect(func(): op({"op": "last"}))
		body.add_child(lb)
	if not M["cards"].is_empty():
		var grid := GridContainer.new()
		grid.columns = 4 if M["cards"].size() >= 7 else (3 if M["cards"].size() >= 3 else 2)
		grid.add_theme_constant_override("h_separation", 10)
		grid.add_theme_constant_override("v_separation", 10)
		body.add_child(grid)
		var i := 0
		for c in M["cards"]:
			var cd := _card(c, M["key"])
			grid.add_child(cd)
			if step != _last_step:                         # the cards come in one after the other
				cd.modulate.a = 0.0
				cd.create_tween().tween_property(cd, "modulate:a", 1.0, 0.25).set_delay(0.04 * i)
			i += 1
	var basic: VBoxContainer = null
	var extra: VBoxContainer = null
	for o in M["options"]:
		if o["extra"]:
			if extra == null:
				var eb := Button.new()
				eb.text = plain(("▾ " if extras_open else "▸ ") + str(M["extras_label"]))
				eb.flat = true
				eb.alignment = HORIZONTAL_ALIGNMENT_LEFT
				eb.pressed.connect(func(): op({"op": "extras", "value": not extras_open}))
				body.add_child(eb)
				extra = _group("")
				extra.get_parent().visible = extras_open
			_option_row(o, extra)
		else:
			if basic == null:
				basic = _group("Wer spielt mit?" if step == 3 else "Einstellungen")
			_option_row(o, basic)
	if step == 3:
		var G: Dictionary = M["game"]
		var pv := _group("Mitspielen")
		var pr := HBoxContainer.new()                      # the players: phones (QR) or here at the PC
		pr.add_theme_constant_override("separation", 14)
		pv.add_child(pr)
		if G["open"]:
			var qr := TextureRect.new()
			qr.custom_minimum_size = Vector2(150, 150)
			qr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			qr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
			qr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			qr.texture = main.game.Qr.texture(G["url"], 4)
			pr.add_child(qr)
		var pt := VBoxContainer.new()
		pt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		pt.add_theme_constant_override("separation", 8)
		pr.add_child(pt)
		pt.add_child(_lab(("Handys: QR-Code scannen (gleiches WLAN) oder %s öffnen" % G["url"]) if G["open"] else "Handys: nach «Spiel öffnen» erscheint hier der QR-Code.", 13))
		pt.add_child(_lab("Dabei: %d (laufen höchstens %d, die anderen schauen zu und tippen)" % [G["players"], int(G["max"])], 15, Color.WHITE, false))
		var lr := HBoxContainer.new()
		lr.add_theme_constant_override("separation", 8)
		pt.add_child(lr)
		var lb1 := Button.new()
		lb1.text = "Hier am PC mitspielen"
		lb1.pressed.connect(func(): _apply_and_open(); main.localplay.start("runner"))
		lr.add_child(lb1)
		if str(W.get("game_mode")) in ["guard", "teamguard", "seek"]:
			var lb2 := Button.new()
			lb2.text = "Fänger am PC" if str(W.get("game_mode")) == "seek" else "Wächter am PC"
			lb2.pressed.connect(func(): _apply_and_open(); main.localplay.start("guard"))
			lr.add_child(lb2)
		var sg := _group("Zusammenfassung")
		var gs := GridContainer.new()
		gs.columns = 2
		gs.add_theme_constant_override("h_separation", 16)
		gs.add_theme_constant_override("v_separation", 4)
		sg.add_child(gs)
		for p in M["summary"]:
			gs.add_child(_lab(p[0], 13, Color(0.6, 0.66, 0.74), false))
			gs.add_child(_lab(p[1], 13, Color(1, 1, 1), false))
		var rb := Button.new()
		rb.flat = true
		rb.alignment = HORIZONTAL_ALIGNMENT_LEFT
		rb.text = "▸ Regeln (%d)" % M["rules"].size()
		sg.add_child(rb)
		var rbox := VBoxContainer.new()
		rbox.visible = false
		sg.add_child(rbox)
		for r in M["rules"]:
			rbox.add_child(_lab("• " + r, 13))
		rb.pressed.connect(func(): rbox.visible = not rbox.visible; rb.text = ("▾" if rbox.visible else "▸") + " Regeln (%d)" % M["rules"].size())
	back_btn.visible = M["back"]
	next_btn.text = plain(M["next"])
	if step != _last_step:                               # the new step slides in from the side
		var dir := 1.0 if step > _last_step else -1.0
		_last_step = step
		_slide.add_theme_constant_override("margin_left", int(40 * dir))
		_slide.add_theme_constant_override("margin_right", int(-40 * dir))
		body.modulate.a = 0.0
		var tw := create_tween().set_parallel(true)
		tw.tween_method(func(m): _slide.add_theme_constant_override("margin_left", int(m)); _slide.add_theme_constant_override("margin_right", int(-m)), 40.0 * dir, 0.0, 0.25).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tw.tween_property(body, "modulate:a", 1.0, 0.2)


func _apply_and_open() -> void:
	"""«Hier am PC mitspielen» on the last step: take over the settings and open the game first"""
	if not main.game.open:
		_next()
