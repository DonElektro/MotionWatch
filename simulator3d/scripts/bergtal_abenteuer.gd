extends PanelContainer
## Bergtal-Abenteuer «Die Karte des Bergführers» (Daniel, 31.10.2026 - Plan: Story / Abenteuer, Spiel & Ziele, Schlafplatz &
## Ausrüstung, Leben & Geschichten, Bergtal als Testgelände, Karte & Orientierung).
##
## Ablauf (gleicher Look wie der Spiel-Assistent gamewiz.gd: Punkte-Leiste, Karten, Zurück / Weiter):
##   Kapitel → Stimmung (geheimnisvoll / abenteuerlich / gemütlich / lustig; Horror = eigenes Paket, gesperrter Platz)
##   → Schwierigkeit & Ziel (+ Jahreszeit) → Rucksack packen (30 / 50 / 70 L, Gewichtsgrenze, Blinki-Vorschlag)
##   → Unterwegs (Kraft, Essen, Wasser, Gewicht, Steigung; Gabelungen kurz-steil / lang-flach, Begegnungen, Wetter,
##     Fundstücke; Hinweise auf der Karte, im Gelände, bei Menschen; Karte lesen mit Symbolen und Sonnenstand)
##   → Nachtlager (Schlafplatz aus bergtal.gd, MoveEye-Halterung, Windschutzmauer) → Nacht im Zeitraffer (nachtlauf.gd,
##     MoveEye bewacht) → Morgen (Bewertung bergtal.morning(), Bericht von MoveEye, Sterne, Tagebuch, Erfahrung).
## Unterwegs geht man nicht als Figur durchs Tal (2 × 2 km): die Tour läuft auf den Wanderwegen der Karte; Zeit, Distanz und
## Höhenmeter kommen aus der echten Höhenkarte, die Fensteransicht fliegt mit. Am Lager steht MoveEye wirklich dort.
## Testgelände: jeder Lauf hat einen Seed - «Situation speichern» merkt Seed, Einstellungen und alle Entscheide;
## «Genau gleich nochmals abspielen» fährt sie selbst ab (gleiche Ereignisse, gleiche Nacht) - zum Vergleich zweier
## MoveEye-Versionen. Treffer-Karte (gesehen / verpasst) und ein Bericht pro Lauf (user://bergtal_abenteuer/berichte/).
## Steuerbefehl: {"action": "abenteuer", "do": state | open | close | pick (key, value) | next | back | choose (value) | go |
##                pause | refill | eat | camp_here | night | save (name) | situations | replay (name) | report | fast | reset |
##                a2 (Figuren, Gespräche, Nebenaufgaben: abenteuer_figuren.gd)}

const D = preload("res://scripts/bergtal_abenteuer_daten.gd")
const T = preload("res://scripts/i18n.gd")
const Bt = preload("res://scripts/bergtal.gd")
const Karte = preload("res://scripts/bergtal_abenteuer_karte.gd")
const Inv = preload("res://scripts/abenteuer_inventar.gd")   # A4: gemeinsames Inventar (hat / gib / nimm / anzahl)
const Ruck = preload("res://scripts/abenteuer_rucksack.gd")  # A4: Essen/Trinken mild, Ausrüstung finden, Tausch

const STEPS := ["Kapitel", "Stimmung", "Schwierigkeit & Ziel", "Rucksack", "Unterwegs", "Nachtlager", "Nacht", "Morgen"]
const SAVE_FILE := "user://bergtal_abenteuer/fortschritt.json"
const DIR := "user://bergtal_abenteuer"
const ACC := Color(0.23, 0.55, 1.0)
const GRN := Color(0.3, 0.85, 0.45)
const ORG := Color(1.0, 0.62, 0.26)
const REDC := Color(1.0, 0.4, 0.35)

var main
var shown := false
var step := 0
var seq := 0
var _painted := -1
var _last_step := -1
var _pulse := 0.0
var _prog_f := 0.0
var error := ""
var dev_open := false

# the choice being made (the wizard steps)
var W := {"chapter": 1, "mood": "abenteuerlich", "level": "mittel", "goal": "dunkel", "season": "sommer", "pack": "50",
		"items": {}, "tempo": 5}
var P := {}                          # progress (saved): chapter, xp, stars, finds, finale, runs
var R := {}                          # the running adventure (one chapter)
var rng := RandomNumberGenerator.new()
var choices: Array = []              # every decision of this run: [stage, key, value] (for «genau gleich nochmals»)
var replay_q: Array = []             # replay: decisions still to apply
var replaying := false
var _replay_t := 0.0
var fast := false                    # tests: legs and the night without waiting
var leg := {}                        # the leg being walked: pts, t_h, cost, f …
var _fly_t := 0.0
var _night_seen := {}                # night event id -> true (MoveEye reported it while visible)
var _night_src := "moveeye"
var _night_t := 0.0
var _snaps: Array = []               # diary pictures of this run: [ImageTexture, caption]
var _registered := false

var prog: Control
var body: VBoxContainer
var _slide: MarginContainer
var back_btn: Button
var next_btn: Button
var karte                            # bergtal_abenteuer_karte.gd (kept between paints)
var title_lab: Label
var a2                               # A2: Figuren, Gespräche, Nebenaufgaben (abenteuer_figuren.gd)


# =======================================================================================================================
# progress (chapters, experience, level)
# =======================================================================================================================
func _load() -> void:
	P = {"chapter": 1, "xp": 0, "stars": {}, "finds": [], "finale": false, "runs": [], "pieces": []}
	if FileAccess.file_exists(SAVE_FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(SAVE_FILE))
		if d is Dictionary:
			for k in d:
				P[k] = d[k]
	W["chapter"] = clampi(int(P["chapter"]), 1, 5)


func _save() -> void:
	DirAccess.make_dir_recursive_absolute(DIR)
	var f := FileAccess.open(SAVE_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(P, " "))


func level() -> int:
	var lv := 1
	for i in range(D.LEVEL_XP.size()):
		if int(P.get("xp", 0)) >= int(D.LEVEL_XP[i]):
			lv = i + 1
	return lv


func item_unlocked(id: String) -> bool:
	if id == "karabiner":
		return bool(P.get("finale", false))
	return level() >= int(D.ITEMS[id][6])


# =======================================================================================================================
# the backpack
# =======================================================================================================================
func pack_kg(items: Dictionary = {}) -> float:
	var it: Dictionary = items if not items.is_empty() else W["items"]
	var kg: float = float(D.PACKS[str(W["pack"])][2])
	for k in it:
		if D.ITEMS.has(k):
			kg += float(D.ITEMS[k][1]) * int(it[k])
		elif str(k) in Inv.IDS:
			kg += Inv.gewicht(str(k)) * int(it[k])          # A4: neue Gegenstände (kaese, brief …)
	return snappedf(kg + Inv.extra_kg(), 0.01)


func pack_l() -> float:
	var l := 0.0
	for k in W["items"]:
		if D.ITEMS.has(k):
			l += float(D.ITEMS[k][2]) * int(W["items"][k])
	return l


func has(id: String) -> bool:
	return Inv.hat(id)                                   # A4: Rucksack + gefundene / bleibende Dinge


func blinki_suggest() -> Dictionary:
	"""Blinki's beginner kit (the only place Blinki speaks - Daniel): what fits the season and the goal"""
	var winter: bool = str(W["season"]) == "winter"
	var cold: bool = winter or str(W["season"]) in ["herbst", "fruehling"]
	var it := {"isomatte": 1, "einmannzelt": 1, "stirnlampe": 1, "jacke": 1, "kocher": 1, "essen": 2, "wasser": 2, "apotheke": 1, "powerbank": 1}
	it["winterschlafsack" if cold else "sommerschlafsack"] = 1
	if winter and item_unlocked("daunenschlafsack"):
		it.erase("winterschlafsack")
		it["daunenschlafsack"] = 1
	if int(W["chapter"]) >= 4:
		it["stoecke"] = 1
	W["pack"] = "70" if winter else "50"
	return it


# =======================================================================================================================
# sun (NOAA, like main.sun_pos - for any hour of the day; the mountains are not counted)
# =======================================================================================================================
func sun_at(h: float) -> Vector2:
	var la: float = main.ort_lat if main.ort_lat != 0.0 else 46.8
	var lo: float = main.ort_lon if main.ort_lon != 0.0 else 8.2
	var doy: int = main.day_of_year()
	var tz := 2.0 if doy >= 88 and doy < 300 else 1.0
	var hu := h - tz
	var g := TAU / 365.0 * (doy - 1 + (hu - 12.0) / 24.0)
	var eqt := 229.18 * (0.000075 + 0.001868 * cos(g) - 0.032077 * sin(g) - 0.014615 * cos(2 * g) - 0.040849 * sin(2 * g))
	var decl := 0.006918 - 0.399912 * cos(g) + 0.070257 * sin(g) - 0.006758 * cos(2 * g) + 0.000907 * sin(2 * g) - 0.002697 * cos(3 * g) + 0.00148 * sin(3 * g)
	var tst := hu * 60.0 + eqt + 4.0 * lo
	var ha := deg_to_rad(tst / 4.0 - 180.0)
	var phi := deg_to_rad(la)
	var cz := sin(phi) * sin(decl) + cos(phi) * cos(decl) * cos(ha)
	var el := 90.0 - rad_to_deg(acos(clampf(cz, -1.0, 1.0)))
	var az := fposmod(rad_to_deg(atan2(sin(ha), cos(ha) * sin(phi) - tan(decl) * cos(phi))) + 180.0, 360.0)
	return Vector2(el, az)


func sunset_h() -> float:
	var h := 12.0
	while h < 23.9 and sun_at(h).x > -0.8:
		h += 0.05
	return h


func sunrise_h() -> float:
	var h := 3.0
	while h < 11.0 and sun_at(h).x < -0.8:
		h += 0.05
	return h


static func dir_word(az: float) -> String:
	var w := ["Norden", "Nordosten", "Osten", "Südosten", "Süden", "Südwesten", "Westen", "Nordwesten"]
	return w[int(round(fposmod(az, 360.0) / 45.0)) % 8]


static func hm(h: float) -> String:
	var hh := fposmod(h, 24.0)
	return "%02d:%02d" % [int(hh), int(fmod(hh, 1.0) * 60.0)]


# =======================================================================================================================
# the way: length, height metres and time from the height map
# =======================================================================================================================
func leg_info(pts: Array, flags: Array = []) -> Dictionary:
	"""distance (m), up / down (m), time (h) like the Swiss hiking signposts (Schweizer Wanderwege: 4.2 km/h, + 1 h per
	300 m up / 500 m down, the bigger part + half the smaller; the same formula as the signposts in bergtal.gd), slowed by the
	load: + 2 % per kg over 8 kg (rule of thumb from the SAC / hiking guides), and the strength it costs"""
	var dist := 0.0
	var up := 0.0
	var down := 0.0
	var steep := 0.0
	var prev_h := -99999.0
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var L := a.distance_to(b)
		var n := maxi(1, int(L / 20.0))
		var ha := Bt.H(a.x, a.y)
		var hb := Bt.H(b.x, b.y)
		for k in range(n + 1):
			if i > 0 and k == 0:
				continue
			var q := a.lerp(b, float(k) / n)
			# a bridge or a gorge: never deeper than 40 m below the line between the two ends (the way goes over it)
			var h := maxf(Bt.H(q.x, q.y), lerpf(ha, hb, float(k) / n) - 40.0)
			if prev_h > -9999.0:
				var dh := h - prev_h
				if dh > 0.0:
					up += dh
				else:
					down -= dh
				steep = maxf(steep, rad_to_deg(atan(absf(dh) / maxf(1.0, L / n))))
			prev_h = h
		dist += L
	dist *= 1.15                                         # the path winds a bit
	var t1 := dist / 1000.0 / 4.2
	var t2 := maxf(up / 300.0, down / 500.0) if up > 0.0 or down > 0.0 else 0.0
	var t := maxf(t1, t2) + minf(t1, t2) / 2.0
	var kg := pack_kg(R.get("items", {})) + float(R.get("found_kg", 0.0))
	var loadf := 1.0 + maxf(0.0, kg - 8.0) * 0.02
	t *= loadf
	# strength: «Leistungskilometer» (km + 100 m up = 1 km more), heavier = harder, uphill with a heavy pack clearly harder
	var lkm := dist / 1000.0 + up / 100.0 + down / 300.0
	var cost := lkm * 6.0 * (1.0 + maxf(0.0, kg - 6.0) * 0.045)
	if "steep" in flags:
		cost *= 1.12
	if has("stoecke"):
		cost *= 0.92
	return {"dist": dist, "up": up, "down": down, "t_h": t, "cost": cost, "steep": steep, "kg": kg}


func leg_text(li: Dictionary) -> String:
	var mins := int(round(float(li["t_h"]) * 60.0 / 5.0) * 5.0)
	var tt := ("%d min" % mins) if mins < 60 else ("%d h %02d min" % [mins / 60, mins % 60])
	return T.t("%s · %.1f km · %d m hinauf · %d m hinunter") % [tt, float(li["dist"]) / 1000.0, int(li["up"]), int(li["down"])]


# =======================================================================================================================
# start of an adventure
# =======================================================================================================================
func bt():
	return main.scenes.data.get("bergtal", null) if main.scenes != null else null


func chapter() -> Dictionary:
	return D.CHAPTERS[clampi(int(R.get("chapter", W["chapter"])), 1, 5) - 1]


func start_run(seed_v := 0) -> Dictionary:
	if pack_kg() > float(D.PACKS[str(W["pack"])][3]) or pack_l() > float(D.PACKS[str(W["pack"])][1]):
		error = T.t("Der Rucksack ist zu voll - etwas herausnehmen oder einen grösseren nehmen.")
		_changed()
		return {"ok": false, "error": error}
	var b: String = main.busy_with("Bergtal-Abenteuer")
	if b == "Nacht-Testlauf" and main.nacht.opts.get("by", "") == "abenteuer":
		main.nacht.stop(false)
		b = ""
	if b != "":
		error = main.busy_msg(b)
		_changed()
		return {"ok": false, "error": error}
	var sd: int = seed_v if seed_v > 0 else randi() % 900000 + 1000
	rng.seed = sd
	var ch: Dictionary = D.CHAPTERS[int(W["chapter"]) - 1]
	var goal := str(W["goal"])
	if goal == "zufall":
		goal = "dunkel" if rng.randf() < 0.5 else "gipfel"
	var lv: Array = D.LEVELS[str(W["level"])]
	R = {"id": "%d" % int(Time.get_unix_time_from_system() * 1000.0), "seed": sd, "chapter": int(W["chapter"]), "mood": str(W["mood"]),
			"level": str(W["level"]), "goal": goal, "goal_pick": str(W["goal"]), "season": str(W["season"]), "pack": str(W["pack"]),
			"items": (W["items"] as Dictionary).duplicate(), "stage": 0, "smax": float(lv[2]), "stamina": float(lv[2]), "food": 80.0,
			"water": float(int(W["items"].get("wasser", 0))), "found": [], "found_kg": 0.0, "pos": Vector2(ch["start"][1], ch["start"][2]),
			"walked": [Vector2(ch["start"][1], ch["start"][2])], "log": [], "notes": [], "clues": {}, "reads_wrong": 0, "mw_warn": 0,
			"wet": false, "cold": 0, "hurt": false, "dark_walk": false, "pending": {}, "weather": {}, "meet": {}, "finds": {},
			"choices": [], "camp": {}, "night": {}, "result": {}, "events_done": {}, "bank": false, "bach": false,
			"mw_version": str(main.mw.get("mw_version", "")) if main.now() - main.mw_t < 30.0 else ""}
	choices = []
	_snaps = []
	_plan_events(ch)
	if a2 != null:
		a2.on_start()                                    # A2: memory of the figures, who you meet today
	# the valley: season, orientation, the scene
	main.bt_season = str(W["season"])
	if main.BT_MONTH.has(str(W["season"])):
		main.season = main.BT_MONTH[str(W["season"])]
		main._sun_cache = [-1.0, Vector2.ZERO]
	R["saved"] = {"bt_events": main.bt_events, "auto": main.auto_visitors, "speed": main.speed, "orient": main.bt_orient}
	main.bt_orient = str(lv[5])                          # the level sets the orientation (restored in the morning)
	main.bt_events = false                               # only the adventure's events (the night truth is complete)
	main.auto_visitors = false
	main.set_scene("bergtal")                            # (again: built with the season)
	var pc: Array = P.get("pieces", [])
	if not int(ch["piece"]) in pc:
		pc.append(int(ch["piece"]))
		P["pieces"] = pc
	# the start time: arrive about 1–2 hours before sunset (goal «dunkel»: the sunset is the deadline)
	var est := 0.0
	for st in ch["stages"]:
		if st.has("walk"):
			est += float(leg_info(st["walk"])["t_h"])
		elif st.has("fork"):
			est += float(leg_info(st["fork"][1][1])["t_h"]) * 0.9
	var buf: float = {"leicht": 2.5, "mittel": 1.8, "schwer": 1.2}.get(str(W["level"]), 1.8)
	var sh := clampf(sunset_h() - est * 1.25 - buf - 0.6, 8.0, float(ch.get("start_h", 15.0)) + 1.5)
	R["start_h"] = snappedf(sh, 0.25)
	main.set_hour(float(R["start_h"]))
	main._set_speed(1.0)
	main.weather = "clear"
	R["sunset"] = sunset_h()
	R["sunrise"] = sunrise_h()
	_diary("start", T.t(str(ch["title"])), T.t(str(D.FLAVOR[R["mood"]]["start"])))
	_karte_update()
	step = 4
	_snap_later("Start: " + T.t(str(ch["start"][0])), "view")
	_changed()
	_say(T.t("Los geht's: %s") % T.t(str(ch["start"][0])))
	_advance()
	return {"ok": true, "seed": sd, "goal": goal, "start_h": R["start_h"]}


func _plan_events(ch: Dictionary) -> void:
	"""everything random on the way, decided at the start from the seed (same seed = same tour)"""
	var md: Array = D.MOODS[str(R["mood"])]
	var lv: Array = D.LEVELS[str(R["level"])]
	var n: int = (ch["stages"] as Array).size()
	var meets: Array = []
	for k in D.MEET:
		var ms: Array = D.MEET[k][3]
		if ms.is_empty() or str(R["mood"]) in ms:
			meets.append(k)
	var finds: Array = []
	for k in D.FINDS:
		if not bool(D.FINDS[k][3]) or bool(md[5]):
			finds.append(k)
	var wx_done := false
	for i in range(n):
		var st: Dictionary = ch["stages"][i]
		if not (st.has("walk") or st.has("fork")):
			continue
		# weather: fog or a thunderstorm comes (at most twice a tour); more with «abenteuerlich» and «schwer»
		var pw: float = 0.22 * float(md[2]) * float(lv[3])
		if rng.randf() < pw and (not wx_done or rng.randf() < 0.3):
			wx_done = true
			R["weather"][str(i)] = "fog" if rng.randf() < float(md[4]) else "storm"
		if rng.randf() < 0.42 * float(md[3]) and not meets.is_empty():
			R["meet"][str(i)] = meets[rng.randi() % meets.size()]
		if rng.randf() < 0.28 and not finds.is_empty():
			R["finds"][str(i)] = finds[rng.randi() % finds.size()]
	R["night_seed"] = rng.randi() % 900000 + 1


# =======================================================================================================================
# the tour: stage after stage
# =======================================================================================================================
func _advance() -> void:
	"""the next thing on the way (walk, fork, clue, read the map) - or the goal"""
	if R.is_empty() or step != 4:
		return
	var ch := chapter()
	var stages: Array = ch["stages"]
	var i := int(R["stage"])
	if i >= stages.size():
		_arrive()
		return
	var st: Dictionary = stages[i]
	if st.has("walk"):
		_pre_leg(i, st["walk"], [] if not st.has("bach") else ["bach"], str(st.get("name", "")))
	elif st.has("fork"):
		var opts := []
		for k in range(2):
			var side: Array = st["fork"][k]
			var li := leg_info(side[1], side[2])
			opts.append([str(k), "%s\n%s · %s" % [T.t(str(side[0])), leg_text(li), T.t("Kraft −%d") % int(round(li["cost"] * _cost_f()))]])
		var tip := ""
		if R.get("tip_fork", false):
			tip = T.t("Die Wanderin hat gesagt: der flache Weg zieht sich, ist aber weniger anstrengend.")
		_ask("fork", T.t("Weggabelung"), T.t("Der Weg teilt sich. Welchen nimmst du?") + ("\n" + tip if tip != "" else ""), opts)
	elif st.has("clue"):
		var kind := str(st["clue"])
		if kind == "terrain":
			R["clues"]["terrain"] = true
			_diary("clue", T.t("Hinweis im Gelände"), T.t(str(st["text"])))
			_snap_later(T.t("Hinweis im Gelände"), "view")
			_ask("info", T.t("Hinweis im Gelände"), T.t(str(st["text"])), [["ok", T.t("Weiter")]])
		elif kind == "person":
			R["clues"]["person"] = true
			var pe: Array = ch["person"]
			_diary("person", T.t(str(pe[0])), T.t(str(pe[1])))
			_snap_later(T.t(str(pe[0])), "view")
			_ask("info", T.t(str(pe[0])), T.t(str(pe[1])), [["ok", T.t("Danke - weiter")]])
		elif kind == "sun":
			R["clues"]["sun"] = true
			var sp: Vector2 = main.sun_pos()
			var tx := ""
			if sp.x > 0.0:
				tx = T.t("Die Sonne steht jetzt im %s (%d°), %d° über dem Horizont. Am Morgen geht sie im Osten auf - der Schatten eines Steins zeigt dann nach Westen.") % [T.t(dir_word(sp.y)), int(sp.y), int(sp.x)]
			else:
				tx = T.t("Die Sonne ist schon untergegangen. Sie geht im Osten auf - am Morgen bekommt zuerst Licht, was hoch steht und gegen Osten frei ist.")
			_diary("sun", T.t("Karte mit der Sonne lesen"), tx)
			_ask("info", T.t("Karte mit der Sonne lesen"), tx, [["ok", T.t("Weiter")]])
	elif st.has("read"):
		var rd: Dictionary = st["read"]
		var opts2 := []
		var order := [0, 1, 2]
		var r2 := RandomNumberGenerator.new()
		r2.seed = int(R["seed"]) + i
		for k in range(2, 0, -1):                          # shuffled, the same for the same seed
			var j := r2.randi() % (k + 1)
			var tmp = order[k]
			order[k] = order[j]
			order[j] = tmp
		for k in order:
			opts2.append([str(k), T.t(str(rd["options"][k][0]))])
		var had := []
		for c in ["terrain", "person", "sun"]:
			if R["clues"].get(c, false):
				had.append(T.t({"terrain": "im Gelände", "person": "von Menschen", "sun": "die Sonne"}[c]))
		var lead := T.t(str(rd["q"]))
		if not had.is_empty():
			lead += "\n" + T.t("Deine Hinweise: die Karte, %s.") % ", ".join(had)
		_ask("read", T.t("Karte lesen"), lead, opts2)


func _cost_f() -> float:
	"""what makes walking harder now: hunger, thirst, cold, a hurt foot, darkness without a lamp"""
	var f := Ruck.kraft_f(self)                          # A4: hungrig / durstig = mild (nie Spielende, in «Leicht» aus)
	if int(R.get("cold", 0)) > 0:
		f *= 1.0 + 0.12 * int(R["cold"])
	if bool(R.get("hurt", false)):
		f *= 1.25
	if main.is_dark() and not has("stirnlampe"):
		f *= 1.3
	return f


func _pre_leg(i: int, pts: Array, flags: Array, nm: String) -> void:
	"""before a leg: MoveEye warns (weather / animals one leg early), then the leg starts"""
	var wx: String = str(R["weather"].get(str(i), ""))
	if wx == "" and has("fernglas"):                    # with the binoculars: one leg earlier
		wx = str(R["weather"].get(str(i + 1), ""))
		if wx == "":
			wx = str(R["weather"].get(str(i + 2), ""))
	if wx != "" and not R["events_done"].has("warn%d" % i):
		R["events_done"]["warn%d" % i] = true
		R["mw_warn"] = int(R["mw_warn"]) + 1
		var w := T.t("MoveEye: Der Luftdruck fällt (−3 hPa in einer Stunde). Gewitter möglich - ausgesetzte Wege meiden.") if wx == "storm" else T.t("MoveEye: Die Luftfeuchtigkeit steigt stark. Nebel kommt - Kompass bereithalten.")
		_diary("mw", T.t("MoveEye warnt"), w)
		_ask("info", T.t("MoveEye warnt"), w, [["ok", T.t("Verstanden")]], {"then_leg": [i, pts, flags, nm]})
		return
	_start_leg(i, pts, flags, nm)


func _start_leg(i: int, pts: Array, flags: Array, nm: String) -> void:
	var li := leg_info(pts, flags)
	var f := _cost_f()
	var dark0: bool = main.is_dark()
	var t_h: float = float(li["t_h"])
	if dark0 and not has("stirnlampe"):
		t_h *= 2.2
		if not R["events_done"].has("nolamp"):
			R["events_done"]["nolamp"] = true
			R["dark_walk"] = true
			R["notes"].append("nolamp")
			_diary("forgot", T.t("Keine Stirnlampe"), T.t("Es ist dunkel - und die Stirnlampe liegt zu Hause. Jeder Schritt ist unsicher, alles dauert doppelt so lange."))
	elif dark0:
		t_h *= 1.3
	if bool(R.get("hurt", false)):
		t_h *= 1.2
	t_h *= Ruck.tempo_f(self)                           # A4: hungrig / durstig = langsamer
	leg = {"i": i, "pts": pts, "flags": flags, "name": nm, "t_h": t_h, "cost": float(li["cost"]) * f, "f": 0.0, "h0": main.hour(),
			"s0": float(R["stamina"]), "food0": float(R["food"]), "water0": float(R["water"]), "up": float(li["up"]),
			"real_s": 0.6 if fast else clampf(t_h * 9.0, 3.0, 10.0), "dist": float(li["dist"])}
	R["walking"] = true
	R["bank"] = "bank" in flags
	R["bach"] = "bach" in flags
	if nm != "":
		R["now"] = T.t(nm)
	_fly_t = 0.0
	_changed()


func _tick_leg(dt: float) -> void:
	if leg.is_empty():
		return
	var f0: float = float(leg["f"])
	var f: float = minf(1.0, f0 + dt / float(leg["real_s"]))
	leg["f"] = f
	var t_h: float = float(leg["t_h"])
	main.set_hour(float(leg["h0"]) + t_h * f)
	R["stamina"] = maxf(0.0, float(leg["s0"]) - float(leg["cost"]) * f)
	R["food"] = maxf(0.0, float(leg["food0"]) - 10.0 * t_h * f * Ruck.verbrauch_f(self))   # A4: in «Leicht» kein Verbrauch
	# drinking: about 0.4 L per hour + 0.15 L per 100 m up (hiking guides: 0.3–0.5 L/h, more uphill and in the heat)
	R["water"] = maxf(0.0, float(leg["water0"]) - (0.4 * t_h + 0.15 * float(leg["up"]) / 100.0) * f * Ruck.verbrauch_f(self))
	var pts: Array = leg["pts"]
	var p := _along(pts, f)
	R["pos"] = p
	_fly_t -= dt
	var b = bt()
	if b != null and _fly_t <= 0.0:
		_fly_t = 1.4
		var ahead := _along(pts, minf(1.0, f + 0.08))
		var wp: Vector3 = b.WG(p.x, p.y, 1.7)
		var wa: Vector3 = b.WG(ahead.x, ahead.y, 1.7)
		if not fast:
			_fly_view(wp, wa)
	if Engine.get_process_frames() % 10 == 0:
		_karte_update()
		_paint_hud()
	if f >= 1.0:
		_end_leg()


func _along(pts: Array, f: float) -> Vector2:
	var total := 0.0
	for i in range(pts.size() - 1):
		total += (pts[i] as Vector2).distance_to(pts[i + 1])
	var want := total * f
	for i in range(pts.size() - 1):
		var L: float = (pts[i] as Vector2).distance_to(pts[i + 1])
		if want <= L or i == pts.size() - 2:
			return (pts[i] as Vector2).lerp(pts[i + 1], clampf(want / maxf(0.01, L), 0.0, 1.0))
		want -= L
	return pts[-1]


func _fly_view(wp: Vector3, ahead: Vector3) -> void:
	"""the window view walks along: a bit behind and above the walker, looking ahead"""
	var d := ahead - wp
	d.y = 0.0
	if d.length() < 0.5:
		d = Vector3(0, 0, -1)
	d = d.normalized()
	var eye := wp - d * 14.0 + Vector3(0, 7.0, 0)
	eye.y = maxf(eye.y, main.ground_y(eye.x, eye.z) + 2.0)
	main._to_free_view()
	if main.fly_tw != null:
		main.fly_tw.kill()
	var start: Transform3D = main.view_cam.global_transform
	var end := Transform3D(Basis(), eye).looking_at(ahead + Vector3(0, 1.0, 0), Vector3.UP)
	main.fly_tw = main.create_tween()
	main.fly_tw.tween_method(func(x: float): main.view_cam.global_transform = start.interpolate_with(end, x), 0.0, 1.0, 1.3)


func _end_leg() -> void:
	var i: int = int(leg["i"])
	var pts: Array = leg["pts"]
	(R["walked"] as Array).append_array(pts.slice(1))
	R["pos"] = pts[-1]
	R["walking"] = false
	var was_detour: bool = bool(leg.get("detour", false))
	leg = {}
	_karte_update()
	# the forgotten things show on the way
	var alt: float = Bt.H(R["pos"].x, R["pos"].y) + Bt.ALT0
	if not has("jacke") and (alt > 1950.0 or str(R["season"]) in ["herbst", "winter"] or main.sun_el() < 8.0) and not R["events_done"].has("nojacket"):
		R["events_done"]["nojacket"] = true
		R["cold"] = int(R["cold"]) + 1
		R["notes"].append("nojacket")
		_diary("forgot", T.t("Keine Jacke"), T.t("Der Wind wird kalt, und die warme Jacke fehlt. Du frierst - jeder Schritt kostet mehr Kraft."))
	if float(R["stamina"]) <= 0.0 and not was_detour:
		_ask("tired", T.t("Erschöpft"), T.t("Du kannst nicht mehr. Du musst dich hinsetzen und lange ausruhen (45 Minuten)."), [["rest", T.t("Ausruhen")]])
		return
	if was_detour:
		_advance()
		return
	_post_leg(i)


func _post_leg(i: int) -> void:
	"""what happens after leg i: weather, a meeting, a find (each once) - then the next stage"""
	var key := str(i)
	if R["weather"].has(key) and not R["events_done"].has("wx" + key):
		R["events_done"]["wx" + key] = true
		var wx: String = R["weather"][key]
		var b = bt()
		if b != null:
			if wx == "fog":
				b.fog_roll()
			else:
				b.storm()
		var tx := T.t("Nebel steigt aus dem Tal - in wenigen Minuten sieht man keine 30 Meter weit.") if wx == "fog" else T.t("Ein Gewitter zieht auf. Die ersten Blitze über dem Grat, der Donner kommt näher.")
		_diary("weather", T.t("Wetterumschwung"), tx)
		_snap_later(T.t("Wetterumschwung"), "view")
		_ask("weather", T.t("Wetterumschwung"), tx, [["go", T.t("Weitergehen")], ["wait", T.t("Warten, bis es vorbei ist (45 Min.)")], ["back", T.t("Umkehren zum letzten Ort")]], {"wx": wx})
		return
	if R["meet"].has(key) and not R["events_done"].has("meet" + key):
		R["events_done"]["meet" + key] = true
		var mk: String = R["meet"][key]
		var me: Array = D.MEET[mk]
		Ruck.begegnung(self, mk)                         # A4: mit dieser Figur kann man tauschen
		_diary("meet", T.t(str(me[0])), T.t(str(me[1])))
		_snap_later(T.t(str(me[0])), "view")
		match str(me[2]):
			"food":
				_ask("cheese", T.t(str(me[0])), T.t(str(me[1])), [["take", T.t("Danke, gern! (+ Proviant, +0,3 kg)")], ["no", T.t("Nein danke")]])
			"wait":
				_ask("wait_cows", T.t(str(me[0])), T.t(str(me[1])), [["wait", T.t("Warten (10 Min.)")]])
			_:
				if str(me[2]) == "tip_fork":
					R["tip_fork"] = true
				_ask("info", T.t(str(me[0])), T.t(str(me[1])), [["ok", T.t("Weiter")]], {"post": true})
		return
	if R["finds"].has(key) and not R["events_done"].has("find" + key):
		R["events_done"]["find" + key] = true
		var fk: String = R["finds"][key]
		var fd: Array = D.FINDS[fk]
		_ask("find", T.t("Etwas gefunden"), T.t(str(fd[2])) + "\n" + T.t("%s - %.1f kg") % [T.t(str(fd[0])), float(fd[1])],
				[["take", T.t("Mitnehmen (Rucksack wird schwerer)")], ["leave", T.t("Liegen lassen")]], {"find": fk})
		return
	if Ruck.nach_abschnitt(self, i):                     # A4: Quelle am Weg, Ausrüstung gefunden
		return
	if a2 != null and a2.after_leg(i):
		return                                           # A2: a talk or a side task here
	R["stage"] = int(R["stage"]) + 1
	_advance()


func _ask(kind: String, title: String, text: String, opts: Array, extra := {}) -> void:
	"""a decision (or a message) on the way; the replay answers it by itself"""
	R["pending"] = {"kind": kind, "title": title, "text": text, "options": opts}
	for k in extra:
		R["pending"][k] = extra[k]
	_replay_t = 0.7
	_changed()


func choose(v: String) -> Dictionary:
	if R.is_empty() or (R["pending"] as Dictionary).is_empty():
		return {"ok": false, "error": "nothing to choose"}
	var pe: Dictionary = R["pending"]
	var ok := false
	for o in pe["options"]:
		if str(o[0]) == v:
			ok = true
	if not ok:
		return {"ok": false, "error": "options: " + str((pe["options"] as Array).map(func(o): return o[0]))}
	R["pending"] = {}
	choices.append([int(R["stage"]), str(pe["kind"]), v])
	if str(pe["kind"]).begins_with("a2_") and a2 != null:
		a2.choose(pe, v)                                 # A2: talk / side task
		_changed()
		return {"ok": true}
	var ch := chapter()
	var st_i := int(R["stage"])
	match str(pe["kind"]):
		"info":
			if pe.has("then_leg"):
				var tl: Array = pe["then_leg"]
				_start_leg(int(tl[0]), tl[1], tl[2], str(tl[3]))
			elif pe.get("detour", false):
				var rd2: Dictionary = ch["stages"][st_i]["read"]
				_start_leg(st_i, rd2["detour"], [], T.t("Umweg"))     # then read the map again
				leg["detour"] = true
			elif pe.get("post", false):
				_post_leg(st_i)
			else:
				R["stage"] = st_i + 1
				_advance()
		"fork":
			var side: Array = ch["stages"][st_i]["fork"][int(v)]
			R["fork_" + str(st_i)] = int(v)
			_diary("fork", T.t("Weggabelung"), T.t(str(side[0])))
			var fl: Array = side[2]
			if "wet" in fl:
				R["wet"] = true
			if "steep" in fl and not has("apotheke") and str(R["level"]) == "schwer" and rng.randf() < 0.35:
				R["hurt"] = true
				R["notes"].append("hurt")
				_diary("forgot", T.t("Fuss verstaucht"), T.t("Im Geröll knickst du um. Ohne Erste Hilfe tut jeder Schritt weh - du bist langsamer."))
			_start_leg(st_i, side[1], fl, str(side[0]))
		"read":
			var rd: Dictionary = ch["stages"][st_i]["read"]
			if bool(rd["options"][int(v)][1]):
				_diary("read", T.t("Karte gelesen"), T.t("Richtig: %s") % T.t(str(rd["options"][int(v)][0])))
				R["read_ok"] = int(R.get("read_ok", 0)) + (1 if int(R["reads_wrong"]) == 0 else 0)
				R["stage"] = st_i + 1
				_advance()
			else:
				R["reads_wrong"] = int(R["reads_wrong"]) + 1
				_diary("read", T.t("Falscher Ort"), T.t("Hier ist nichts. %s") % T.t(str(rd["hint"])))
				_ask("info", T.t("Falscher Ort - ein Umweg"), T.t("Hier ist nichts. %s") % T.t(str(rd["hint"])), [["ok", T.t("Zurück und nochmals lesen")]], {"detour": true})
		"weather":
			var wx: String = str(pe.get("wx", "fog"))
			match v:
				"go":
					var nxt: Dictionary = ch["stages"][mini(st_i + 1, ch["stages"].size() - 1)]
					var exposed := false
					if nxt.has("fork"):
						exposed = "exposed" in nxt["fork"][0][2]
					if wx == "storm":
						R["wet"] = true
						if not has("jacke"):
							R["cold"] = int(R["cold"]) + 1
						R["storm_go"] = true
						_diary("weather", T.t("Weiter im Gewitter"), T.t("Nass bis auf die Haut. Am Grat wäre das gefährlich - Blitze treffen zuerst hohe Punkte.") if exposed else T.t("Nass bis auf die Haut, aber weiter."))
					else:
						R["fog_go"] = true
						if str(R["level"]) == "schwer" and not has("kompass"):   # A4: mit gefundenem Kompass nicht
							_diary("weather", T.t("Weiter im Nebel"), T.t("Ohne Kompass im Nebel - du verlierst kurz den Weg."))
							_pause(0.4, false)
					_post_leg(st_i)
				"wait":
					_pause(0.75, false)
					main.weather = "clear"
					main.thunder = false
					_diary("weather", T.t("Gewartet"), T.t("Nach einer Dreiviertelstunde ist es vorbei."))
					_post_leg(st_i)
				"back":
					var walked: Array = R["walked"]
					var back_to: Vector2 = walked[maxi(0, walked.size() - 3)]
					_diary("weather", T.t("Umgekehrt"), T.t("Sicher ist sicher. Zurück und abwarten, dann nochmals."))
					_pause(0.6, false)
					main.weather = "clear"
					main.thunder = false
					leg = {}
					var pts2 := [R["pos"], back_to, R["pos"]]
					_start_leg(st_i, pts2, [], "")
					leg["detour"] = true
					R["stage"] = st_i + 1
		"cheese":
			if v == "take":
				R["food"] = minf(100.0, float(R["food"]) + 35.0)
				R["found_kg"] = float(R["found_kg"]) + 0.3
				_diary("meet", T.t("Alpkäse"), T.t("Der beste Käse, den du je gegessen hast."))
			_post_leg(st_i)
		"wait_cows":
			_pause(0.17, false)
			_post_leg(st_i)
		"find":
			if v == "take":
				var fk: String = pe["find"]
				R["found"].append(fk)
				R["found_kg"] = float(R["found_kg"]) + float(D.FINDS[fk][1])
				_diary("find", T.t("Fundstück"), T.t(str(D.FINDS[fk][0])))
				_snap_later(T.t(str(D.FINDS[fk][0])), "view")
			_post_leg(st_i)
		"tired":
			_pause(0.75, false)
			R["stamina"] = maxf(float(R["stamina"]), float(R["smax"]) * 0.45)
			_post_leg(st_i)
		"a4_fund":                                        # A4
			Ruck.choose(self, pe, v)
			_post_leg(st_i)
		"camp_early":
			if v == "yes":
				_arrive(true)
			else:
				_advance()
	_changed()
	return {"ok": true}


func _pause(h: float, rest := true) -> void:
	"""time passes; a rest gives strength back (more on a bench or at a viewpoint), eating and drinking on the way"""
	main.set_hour(main.hour() + h)
	if rest:
		var gain := 12.0 * h / 0.25
		if bool(R.get("bank", false)):
			gain *= 2.0
		if float(R["food"]) < 60.0 and int(R["items"].get("essen", 0)) > 0:
			R["items"]["essen"] = int(R["items"]["essen"]) - 1
			R["food"] = minf(100.0, float(R["food"]) + 45.0)
			gain += 6.0
			if has("kocher"):
				gain += 4.0
		if float(R["food"]) <= 0.0:
			gain *= 0.5
		if float(R["water"]) <= 0.0:
			gain *= 0.6
		R["stamina"] = minf(float(R["smax"]), float(R["stamina"]) + gain)


func do_pause() -> Dictionary:
	if R.is_empty() or bool(R.get("walking", false)) or step != 4:
		return {"ok": false}
	_pause(0.25)
	choices.append([int(R["stage"]), "pause", "15"])
	_diary("pause", T.t("Pause"), T.t("Eine Viertelstunde Pause%s.") % (T.t(" auf der Bank mit Aussicht") if bool(R.get("bank", false)) else ""))
	_changed()
	return {"ok": true, "stamina": R["stamina"]}


func do_refill() -> Dictionary:
	if R.is_empty() or not (bool(R.get("bach", false)) or Ruck.quelle(self) != "" or not Ruck.huette(self).is_empty()) or bool(R.get("walking", false)):
		return {"ok": false, "error": "kein Bach hier"}
	var cap := float(maxi(1, int(R["items"].get("wasser", 0))))
	if str(R["season"]) == "winter" and not has("kocher"):
		_diary("forgot", T.t("Bach gefroren"), T.t("Der Bach ist gefroren - ohne Kocher kann man keinen Schnee schmelzen."))
		_changed()
		return {"ok": false, "error": "gefroren"}
	R["water"] = cap
	main.set_hour(main.hour() + 0.08)
	choices.append([int(R["stage"]), "refill", "1"])
	_diary("water", T.t("Wasser aufgefüllt"), T.t("Kaltes, klares Bergwasser."))
	_changed()
	return {"ok": true, "water": R["water"]}


func camp_here() -> Dictionary:
	"""stop early and sleep where you are (the chapter goes on next time from here: no - the chapter is not done)"""
	if R.is_empty() or bool(R.get("walking", false)) or step != 4:
		return {"ok": false}
	_ask("camp_early", T.t("Hier übernachten?"), T.t("Das Ziel ist noch nicht erreicht. Hier übernachten heisst: das Kapitel ist nicht geschafft (höchstens 1 Stern)."), [["yes", T.t("Ja, hier übernachten")], ["no", T.t("Nein, weiter")]])
	return {"ok": true}


func _arrive(early := false) -> void:
	var ch := chapter()
	R["arrived"] = not early
	R["arrive_h"] = main.hour()
	if not early:
		_diary("found", T.t("Am Ziel"), T.t(str(ch["found"])))
		var pc: Array = P.get("pieces", [])
		var nxt: int = int(ch["piece"]) + 1
		if nxt <= 4 and not nxt in pc:
			pc.append(nxt)
		if not int(ch["piece"]) in pc:
			pc.append(int(ch["piece"]))
		P["pieces"] = pc
		_karte_update()
		_snap_later(T.t("Am Ziel"), "view")
	R["camp_xz"] = R["pos"] if early or str(ch["camp"][0]) == "frei" else Vector2(float(ch["camp"][1]), float(ch["camp"][2]))
	R["camp_spot"] = "frei" if early else str(ch["camp"][0])
	step = 5
	_changed()


# =======================================================================================================================
# the camp and the night
# =======================================================================================================================
func bed_of() -> String:
	if has("kuppelzelt"):
		return "tent"
	if has("einmannzelt"):
		return "tent1"
	if has("tarp") or has("ultratarp"):
		return "tarp"
	if has("biwaksack"):
		return "bivy"
	return "mat"


func mounts() -> Array:
	var out := [["rucksack", true], ["stein", true], ["zelt", bed_of() in ["tent", "tent1"]], ["stativ", has("ministativ")]]
	var p: Vector2 = R.get("camp_xz", Vector2.ZERO)
	out.append(["baum", Bt.forest_k(p.x, p.y, Bt.H(p.x, p.y)) > 0.15 or str(R.get("camp_spot", "")) in ["huette", "kapelle", "waldlichtung", "pass"]])
	return out


func set_camp(mount: String, wall: bool) -> Dictionary:
	if R.is_empty() or step != 5:
		return {"ok": false}
	var ok := false
	for m2 in mounts():
		if m2[0] == mount and m2[1]:
			ok = true
	if not ok:
		mount = "rucksack"
	choices.append([99, "camp", "%s|%s" % [mount, "1" if wall else "0"]])
	var dark: bool = main.is_dark()
	var mins: float = {"tent": 25.0, "tent1": 20.0, "tarp": 15.0, "bivy": 8.0, "mat": 5.0}[bed_of()] + (20.0 if wall else 0.0)
	if dark and not has("stirnlampe"):
		mins *= 2.0
	main.set_hour(main.hour() + mins / 60.0)
	R["camp"] = {"mount": mount, "wall": wall, "bed": bed_of(), "set_h": main.hour(), "mins": mins}
	main.bt_bed = bed_of()
	main.bt_bag = "winter" if (has("winterschlafsack") or has("daunenschlafsack")) else "sommer"
	main.bt_stove = has("kocher")
	main.bt_wall = wall
	main.bt_mount = mount
	main._settings_dirty = true
	var spot := str(R["camp_spot"])
	var res := {}
	if spot != "frei":
		main.bt_spot = spot
		main.mover_home()
		main.set_scene("bergtal")
		res = {"ok": true, "spot": spot}
	else:
		var p: Vector2 = R["camp_xz"]
		var b = bt()
		if b == null:
			return {"ok": false, "error": "not bergtal"}
		b.bed = main.bt_bed
		var chk: Dictionary = b.check_place(p.x, p.y, Vector3.ZERO, float(R.get("look", 0.0)), "abenteuer")
		if not bool(chk.get("ok", false)):
			chk = {"ok": true, "x": p.x + 8.0, "z": p.y + 8.0, "yaw": 0.0, "note": ""}
		res = main.bt_take(chk)
	R["sunset_ok"] = float(R["camp"]["set_h"]) <= float(R["sunset"]) + 0.02
	_diary("camp", T.t("Lager aufgeschlagen"), T.t(str(D.FLAVOR[R["mood"]]["camp"])) + " " + T.t("(%s, MoveEye: %s)") % [T.t(_bed_name(bed_of())), T.t(str(Bt.MOUNTS.get(mount, ["?"])[0]))])
	if not has("isomatte") and bed_of() != "mat":
		R["notes"].append("nomat")
	step = 6
	_changed()
	_snap_later(T.t("Das Lager"), "view")
	return res


static func _bed_name(k: String) -> String:
	for b in Bt.BEDS:
		if b[0] == k:
			return str(b[1])
	return k


func _register_kinds() -> void:
	"""the animals and events of the Bergtal for the night test run (nachtlauf.gd register_kind)"""
	if _registered or main.nacht == null:
		return
	_registered = true
	var kinds := {"bt_fox": ["animal", "fox", "berg_fox_food"], "bt_chamois": ["animal", "chamois", "berg_chamois"],
			"bt_cows": ["animal", "cow", "berg_cows"], "bt_hare": ["animal", "hare", "berg_snowhare"], "bt_stoat": ["animal", "stoat", "berg_stoat"],
			"bt_deer": ["animal", "deer", "berg_deer"], "bt_stranger": ["incident", "incident", "berg_stranger"],
			"bt_rockfall": ["event", "rockfall", "berg_rockfall"], "bt_storm": ["event", "storm", "berg_storm"]}
	for k in kinds:
		var kk: String = kinds[k][2]
		main.nacht.register_kind(k, func(_ev): return _spawn_list(kk), kinds[k][0], kinds[k][1])


func _spawn_list(kind: String) -> Array:
	var b = bt()
	if b == null:
		return []
	var v = b.spawn_kind(kind)
	if v is Node:
		return [v]
	if v is Array:
		return v.filter(func(x): return x is Node)
	return []


func night_plan(from_h: float, to_h: float, speed: float) -> Array:
	"""the events of the night at the camp, from the seed, the mood, the level and the place (bergtal rating)"""
	var r := RandomNumberGenerator.new()
	r.seed = int(R["night_seed"])
	var sp: float = fposmod(to_h - from_h, 24.0)
	var md: Array = D.MOODS[str(R["mood"])]
	var lv: Array = D.LEVELS[str(R["level"])]
	var b = bt()
	var rt: Dictionary = b.rating if b != null else {}
	var out: Array = []
	var an: float = float(lv[4])
	var add := func(kind: String, at: float, extra := {}):
		var e := {"kind": kind, "at_h": clampf(at, 0.05, 0.93) * sp}
		for k in extra:
			e[k] = extra[k]
		out.append(e)
	if int(R["items"].get("essen", 0)) > 0 or r.randf() < 0.3:
		add.call("bt_fox", r.randf_range(0.15, 0.6))
	if r.randf() < 0.7 * an:
		add.call("bt_chamois", r.randf_range(0.3, 0.9))
	if str(R["season"]) in ["sommer", "herbst"] and str(R.get("camp_spot", "")) == "huette":
		add.call("bt_cows", r.randf_range(0.1, 0.4))
	if r.randf() < 0.5 * an:
		add.call("bt_hare" if r.randf() < 0.5 else "bt_stoat", r.randf_range(0.2, 0.8))
	if str(R["season"]) == "herbst" and r.randf() < 0.6:
		add.call("bt_deer", r.randf_range(0.2, 0.7))
	if float(rt.get("strangers", 0.2)) > 0.25 or r.randf() < 0.35 * an:
		add.call("bt_stranger", r.randf_range(0.25, 0.75))
	if float(rt.get("rockfall", 0.0)) > 0.3 or r.randf() < 0.15 * an:
		add.call("bt_rockfall", r.randf_range(0.2, 0.85))
	var wx: float = 0.35 * float(md[2]) * float(lv[3])
	if r.randf() < wx:
		if r.randf() < float(md[4]):
			out.append({"kind": "fog", "at_h": r.randf_range(0.5, 0.8) * sp, "dur_h": minf(1.5, 0.2 * sp)})
		else:
			out.append({"kind": "rain", "at_h": r.randf_range(0.15, 0.6) * sp, "dur_h": minf(1.0, 0.15 * sp)})
	if float(rt.get("wind", 0.3)) > 0.5:
		out.append({"kind": "wind", "at_h": r.randf_range(0.1, 0.7) * sp, "dur_h": minf(0.75, 0.12 * sp), "wind": 40.0 + 30.0 * float(rt.get("wind", 0.5))})
	# seconds, not two animals on top of each other
	out.sort_custom(func(a, c): return float(a["at_h"]) < float(c["at_h"]))
	var real_s := sp * 3600.0 / speed
	var gap := clampf(real_s / (out.size() + 2.0), 8.0, 40.0)
	var prev := -1000.0
	for e in out:
		e["at_s"] = snappedf(float(e["at_h"]) * 3600.0 / speed, 0.1)
		if not str(e["kind"]) in ["fog", "rain", "wind"]:
			e["at_s"] = clampf(maxf(float(e["at_s"]), prev + gap), 6.0, real_s * 0.93)
			prev = float(e["at_s"])
		if e.has("dur_h"):
			e["dur_s"] = snappedf(float(e["dur_h"]) * 3600.0 / speed, 0.1)
	out.sort_custom(func(a, c): return float(a["at_s"]) < float(c["at_s"]))
	for i in range(out.size()):
		out[i]["id"] = i + 1
		out[i]["at_h"] = snappedf(float(out[i]["at_s"]) * speed / 3600.0, 0.001)
	return out


func start_night() -> Dictionary:
	if R.is_empty() or step != 6 or main.nacht == null:
		return {"ok": false}
	if main.nacht.running:
		return {"ok": false, "error": "night already running"}
	_register_kinds()
	var from_h: float = main.hour()
	var to_h: float = float(R["sunrise"]) - (0.5 if str(R["goal"]) == "gipfel" else 0.0)
	var sp_h := fposmod(to_h - from_h, 24.0)
	var minutes: float = 0.3 if fast else float(W.get("tempo", 5))
	var speed := clampf(sp_h * 3600.0 / (minutes * 60.0), 1.0, 240.0)
	var plan := night_plan(from_h, to_h, speed)
	_night_seen = {}
	_night_src = "moveeye" if main.now() - main.mw_t < 10.0 else "schaetzung"
	_night_starting = true
	var r: Dictionary = main.nacht.start({"scene": "bergtal", "from": from_h, "to": to_h, "speed": speed, "seed": int(R["night_seed"]),
			"busy": "normal", "by": "abenteuer", "plan": plan, "free": true})
	_night_starting = false
	if not bool(r.get("ok", false)):
		error = str(r.get("error", ""))
		_changed()
		return r
	R["night"] = {"from": from_h, "to": to_h, "speed": speed, "plan": plan.size(), "run": r.get("run", {})}
	_diary("night", T.t("Die Nacht beginnt"), T.t(str(D.FLAVOR[R["mood"]]["night"])))
	_changed()
	return {"ok": true, "plan": plan, "speed": speed}


func _tick_night(dt: float) -> void:
	var n = main.nacht
	if n == null:
		return
	if n.running:
		_night_t -= dt
		if _night_t <= 0.0:
			_night_t = 0.25
			var t: float = n.elapsed()
			var fresh: bool = main.now() - main.mw_det_t < 2.0
			var det: bool = fresh and (int(main.mw_det.get("persons", 0)) > 0 or not (main.mw_det.get("present", []) as Array).is_empty())
			for id in n.active:
				var rec: Dictionary = n.active[id]["rec"]
				var iv: Array = rec.get("vis_iv", [])
				if not iv.is_empty() and t - float(iv[-1][1]) <= 0.6:
					if det:
						if not _night_seen.has(int(id)):
							_night_seen[int(id)] = snappedf(t - float(rec["first_vis"]), 0.1)
							_snap_later(T.t("Nacht: MoveEye meldet %s") % T.t(_kind_name(str(rec["kind"]))), "cam")
					elif not R["events_done"].has("nsnap%d" % int(id)):
						R["events_done"]["nsnap%d" % int(id)] = true
						_snap_later(T.t("Nacht: %s") % T.t(_kind_name(str(rec["kind"]))), "cam")
		if Engine.get_process_frames() % 15 == 0:
			_paint_hud()
	elif not (R["night"] as Dictionary).is_empty() and not R["night"].has("done") and str(n.last.get("id", "")) == str(R["night"].get("run", {}).get("id", "x")):
		R["night"]["done"] = true
		_morning()


static func _kind_name(k: String) -> String:
	return {"bt_fox": "Fuchs am Proviant", "bt_chamois": "Gämsen", "bt_cows": "Kühe", "bt_hare": "Schneehase", "bt_stoat": "Hermelin",
			"bt_deer": "Hirsch", "bt_stranger": "Fremder am Rucksack", "bt_rockfall": "Steinschlag", "bt_storm": "Gewitter", "rain": "Regen",
			"fog": "Nebel", "wind": "Windböen"}.get(k, k)


# =======================================================================================================================
# the morning: rating, report of MoveEye, stars, diary, experience
# =======================================================================================================================
func _morning() -> void:
	var sr: float = float(R["sunrise"])
	main.set_hour(sr - (0.6 if str(R["goal"]) == "gipfel" else -0.25))
	main.weather = "clear"
	main.thunder = false
	var b = bt()
	var mr: Dictionary = b.morning() if b != null else {"total": 3.0, "sicherheit": 3, "aussicht": 3, "ruhe": 3, "night": []}
	# the night as MoveEye saw it (truth of nachtlauf.gd + what MoveEye reported)
	var truth: Array = main.nacht.last.get("truth", [])
	var hits := []
	var seen := 0
	var missed := 0
	var hidden := 0
	var battery_h := -1.0
	var cold_night: bool = str(R["season"]) in ["winter", "herbst"] or float(b.exposure().get("cold_c", 5.0)) < 3.0 if b != null else false
	if not has("powerbank") and cold_night:
		# without a power bank in the cold the battery of MoveEye lasts about 70 % of the night (Li-ion: ≈ −20 … −30 %
		# capacity near 0 °C - typical 18650 datasheets, e.g. Samsung INR18650-35E)
		battery_h = fposmod(float(R["night"]["from"]) + fposmod(float(R["night"]["to"]) - float(R["night"]["from"]), 24.0) * 0.7, 24.0)
	for rec in truth:
		if str(rec.get("cat", "")) == "weather":
			continue
		var st := "hidden"
		var vis: float = float(rec.get("vis_s", 0.0)) + float(rec.get("th_s", 0.0))
		if vis > 0.0:
			if _night_src == "moveeye":
				st = "seen" if _night_seen.has(int(rec["id"])) else "missed"
			else:
				st = "seen" if vis >= 1.5 else "missed"       # without MoveEye: the simulator guesses (visible long enough)
		if battery_h >= 0.0 and st == "seen" and fposmod(float(rec.get("h0", 0.0)) - float(R["night"]["from"]), 24.0) > fposmod(battery_h - float(R["night"]["from"]), 24.0):
			st = "missed"
		if str(rec.get("kind", "")) in ["bt_rockfall", "bt_storm"]:
			continue                                         # no body to see (the stones / the storm are in the diary)
		var pos: Array = rec.get("pos", [])
		var pth: Array = rec.get("path", [])
		if (pos.size() < 2 or (absf(float(pos[0])) < 0.01 and absf(float(pos[1])) < 0.01)) and not pth.is_empty():
			pos = [pth[0][1], pth[0][2]]                     # (spawned this frame: the first point of its way)
		hits.append({"id": rec["id"], "kind": rec["kind"], "label": T.t(_kind_name(str(rec["kind"]))), "st": st, "x": float(pos[0]) if pos.size() > 1 else 0.0,
				"z": float(pos[1]) if pos.size() > 1 else 0.0, "path": rec.get("path", []), "near_m": rec.get("near_m", -1.0), "vis_s": vis,
				"t_detect": _night_seen.get(int(rec["id"]), -1.0), "h": rec.get("h0", 0.0)})
		match st:
			"seen":
				seen += 1
			"missed":
				missed += 1
			_:
				hidden += 1
	# sleeping: cold without mat / bag, wet without a roof
	var sleep := 1.0
	var notes: Array = R["notes"]
	var winter: bool = str(R["season"]) == "winter"
	if not has("isomatte"):
		sleep -= 0.3
		notes.append("nomat")
	if not (has("sommerschlafsack") or has("winterschlafsack") or has("daunenschlafsack")):
		sleep -= 0.45
		notes.append("nobag")
	elif winter and has("sommerschlafsack") and not (has("winterschlafsack") or has("daunenschlafsack")):
		sleep -= 0.3
		notes.append("summerbag")
	var rained := truth.any(func(x): return str(x.get("kind", "")) in ["rain", "bt_storm"])
	if rained and bed_of() == "mat":
		sleep -= 0.3
		R["wet"] = true
		notes.append("noroof")
	if int(R["cold"]) > 0:
		sleep -= 0.1
	sleep = clampf(sleep, 0.2, 1.0)
	R["stamina"] = float(R["smax"]) * sleep
	# the summit at sunrise
	var summit_ok := false
	if str(R["goal"]) == "gipfel":
		var vp: Array = []
		for v in Bt.VIEWPOINTS:
			if v[0] == chapter()["summit"]:
				vp = v
		var c: Vector2 = R["camp_xz"]
		var to: Vector2 = Bt.vp_xz(vp) if not vp.is_empty() else c
		var li := leg_info([c, c.lerp(to, 0.5), to], [])
		var t_h: float = float(li["t_h"]) * (1.0 if has("stirnlampe") else 2.0)
		main.set_hour(sr - t_h - 0.2)
		R["summit_start"] = main.hour()
		main.set_hour(main.hour() + t_h)
		R["summit_h"] = main.hour()
		summit_ok = main.hour() <= sr + 0.1
		R["walked"].append(to)
		_diary("summit", T.t("Gipfel zum Sonnenaufgang"), (T.t("Oben um %s - die Sonne kommt um %s. Geschafft!") if summit_ok else T.t("Oben um %s - die Sonne war schon um %s da.")) % [hm(float(R["summit_h"])), hm(sr)])
		if b != null and not fast:
			var wp: Vector3 = b.WG(to.x, to.y, 1.7)
			main.fly_to(wp, 6.0)
	# stars: 1 = chapter done, +1 = goal reached, +1 = well prepared (good place, nothing important forgotten, MoveEye good)
	var stars := 0
	var arrived: bool = bool(R.get("arrived", false))
	if arrived:
		stars = 1
		var goal_ok: bool = summit_ok if str(R["goal"]) == "gipfel" else bool(R.get("sunset_ok", false))
		if goal_ok:
			stars += 1
		var bad := ["nolamp", "nojacket", "nomat", "nobag", "summerbag", "noroof", "hurt"]
		var forgot := notes.any(func(x): return str(x) in bad)
		if float(mr.get("total", 0.0)) >= 3.3 and not forgot and missed <= seen:
			stars += 1
	stars = clampi(stars, 0 if not arrived else 1, 3)
	if not arrived:
		stars = 0
	# experience
	var xp := stars * 100 + int(R.get("read_ok", 0)) * 30 + (R["found"] as Array).size() * 20 + int(R["mw_warn"]) * 10 + seen * 15
	var lv0 := level()
	P["xp"] = int(P.get("xp", 0)) + xp
	var lv1 := level()
	var unlocked := []
	for l in range(lv0 + 1, lv1 + 1):
		if D.UNLOCKS.has(l):
			unlocked.append(D.UNLOCKS[l])
	var key := str(R["chapter"])
	P["stars"][key] = maxi(int(P["stars"].get(key, 0)), stars)
	if arrived and int(R["chapter"]) >= int(P["chapter"]) and int(R["chapter"]) < 5:
		P["chapter"] = int(R["chapter"]) + 1
	for f in R["found"]:
		P["finds"].append(f)
	var finale := arrived and int(R["chapter"]) == 5
	if finale:
		P["finale"] = true
		if not main.bt_marks.any(func(x): return str(x[0]) == "Dein Seeli"):
			main.bt_marks.append(["Dein Seeli", -878.0, 428.0])
			main._settings_dirty = true
		if b != null:
			b._publish()
	R["result"] = {"stars": stars, "xp": xp, "level": lv1, "level_up": lv1 > lv0, "unlocked": unlocked, "rating": mr, "seen": seen,
			"missed": missed, "hidden": hidden, "hits": hits, "summit_ok": summit_ok, "sunset_ok": bool(R.get("sunset_ok", false)),
			"sleep": snappedf(sleep, 0.01), "source": _night_src, "battery_h": battery_h, "finale": finale, "notes": notes}
	_diary("morning", T.t("Der Morgen"), T.t(str(D.FLAVOR[R["mood"]]["morning"])))
	P["runs"].append({"id": R["id"], "chapter": R["chapter"], "stars": stars, "date": Time.get_datetime_string_from_system().substr(0, 16), "seed": R["seed"]})
	P["runs"] = (P["runs"] as Array).slice(-30)
	_save()
	_write_report()
	_restore()
	step = 7
	_snap_later(T.t("Der Morgen"), "view")
	_changed()


func _restore() -> void:
	var sv: Dictionary = R.get("saved", {})
	main.bt_events = bool(sv.get("bt_events", true))
	main.auto_visitors = bool(sv.get("auto", true))
	if sv.has("orient"):
		main.bt_orient = str(sv["orient"])


func _forgot_text(k: String) -> String:
	return T.t({"nolamp": "Ohne Stirnlampe war es nach Sonnenuntergang stockdunkel.", "nojacket": "Ohne Jacke hast du gefroren.",
			"nomat": "Ohne Isomatte zog die Kälte des Bodens in den Schlafsack.", "nobag": "Ohne Schlafsack war die Nacht eiskalt - kaum geschlafen.",
			"summerbag": "Der Sommerschlafsack war für den Winter zu dünn.", "noroof": "Ohne Zelt oder Tarp hat der Regen alles nass gemacht.",
			"hurt": "Der verstauchte Fuss hat gebremst (Erste Hilfe hätte geholfen)."}.get(k, k))


# =======================================================================================================================
# test ground: save the situation, replay it, one report per run
# =======================================================================================================================
func situation() -> Dictionary:
	return {"seed": int(R.get("seed", 0)), "chapter": int(R.get("chapter", W["chapter"])), "mood": str(R.get("mood", W["mood"])),
			"level": str(R.get("level", W["level"])), "goal": str(R.get("goal_pick", W["goal"])), "season": str(R.get("season", W["season"])),
			"pack": str(R.get("pack", W["pack"])), "items": (R.get("items0", W["items"]) as Dictionary).duplicate(), "tempo": int(W["tempo"]),
			"choices": choices.duplicate(true), "a4_inventar": (R.get("a4_inv0", Inv.bleib_box()) as Dictionary).duplicate(true)}


func situation_key(s: Dictionary) -> String:
	var c := s.duplicate(true)
	c.erase("tempo")
	return str(JSON.stringify(c).hash())


func save_situation(nm := "") -> Dictionary:
	if R.is_empty() and choices.is_empty():
		return {"ok": false, "error": "no run yet"}
	DirAccess.make_dir_recursive_absolute(DIR + "/situationen")
	var s := situation()
	if nm.strip_edges() == "":
		nm = "Kapitel %d · Seed %d · %s" % [int(s["chapter"]), int(s["seed"]), Time.get_datetime_string_from_system().substr(0, 16).replace("T", " ")]
	s["name"] = nm
	var fn: String = DIR + "/situationen/" + nm.validate_filename() + ".json"
	var f := FileAccess.open(fn, FileAccess.WRITE)
	if f == null:
		return {"ok": false, "error": "cannot write"}
	f.store_string(JSON.stringify(s, " "))
	main.start_info = T.t("Situation gespeichert: %s") % nm
	return {"ok": true, "name": nm, "file": fn}


func situations() -> Array:
	var out := []
	var d := DirAccess.open(DIR + "/situationen")
	if d == null:
		return out
	for fn in d.get_files():
		if fn.ends_with(".json"):
			out.append(fn.trim_suffix(".json"))
	out.sort()
	return out


func replay(nm := "") -> Dictionary:
	"""play a saved situation again: same seed, same settings, the same decisions (MoveEye may be another version)"""
	var lst := situations()
	if lst.is_empty():
		return {"ok": false, "error": "keine gespeicherte Situation"}
	if nm == "" or not nm in lst:
		nm = lst[-1]
	var s = JSON.parse_string(FileAccess.get_file_as_string(DIR + "/situationen/" + nm + ".json"))
	if not s is Dictionary:
		return {"ok": false, "error": "file"}
	for k in ["chapter", "mood", "level", "goal", "season", "pack", "tempo"]:
		if s.has(k):
			W[k] = s[k] if k != "chapter" and k != "tempo" else int(s[k])
	W["items"] = {}
	for k in s["items"]:
		W["items"][k] = int(s["items"][k])
	replay_q = (s["choices"] as Array).duplicate(true)
	Inv.replay_box = (s["a4_inventar"] as Dictionary).duplicate(true) if s.get("a4_inventar") is Dictionary else null   # A4
	replaying = true
	shown = true
	var r := start_run(int(s["seed"]))
	R["replay_of"] = nm
	R["items0"] = (W["items"] as Dictionary).duplicate()
	return r


func _tick_replay(dt: float) -> void:
	if not replaying or R.is_empty():
		return
	_replay_t -= dt
	if _replay_t > 0.0:
		return
	_replay_t = 0.6
	if replay_q.is_empty():
		if step == 5:
			set_camp("rucksack", false)
		elif step == 6 and (R["night"] as Dictionary).is_empty():
			start_night()
		elif step == 7:
			replaying = false
		return
	var c: Array = replay_q[0]
	if str(c[1]).begins_with("a4_"):                    # A4: Essen, Kochen, Tausch
		if Ruck.replay(self, c):
			replay_q.pop_front()
		return
	match str(c[1]):
		"pause":
			if step == 4 and not bool(R.get("walking", false)) and (R["pending"] as Dictionary).is_empty():
				replay_q.pop_front()
				do_pause()
		"refill":
			if step == 4 and not bool(R.get("walking", false)):
				replay_q.pop_front()
				do_refill()
		"camp":
			if step == 5:
				replay_q.pop_front()
				var pr := str(c[2]).split("|")
				set_camp(pr[0], pr.size() > 1 and pr[1] == "1")
			elif step == 6 and (R["night"] as Dictionary).is_empty():
				start_night()
		_:
			if step == 4 and not (R["pending"] as Dictionary).is_empty() and str(R["pending"]["kind"]) == str(c[1]):
				replay_q.pop_front()
				choose(str(c[2]))


func _write_report() -> void:
	DirAccess.make_dir_recursive_absolute(DIR + "/berichte")
	var s := situation()
	var res: Dictionary = R["result"]
	var rep := {"id": R["id"], "date": Time.get_datetime_string_from_system(), "sim_version": main.VERSION, "mw_version": R.get("mw_version", ""),
			"situation": s, "situation_key": situation_key(s), "replay_of": R.get("replay_of", ""), "chapter": R["chapter"], "goal": R["goal"],
			"stars": res["stars"], "xp": res["xp"], "rating": res["rating"].duplicate() if res["rating"] is Dictionary else {},
			"night": {"from": R["night"].get("from", 0.0), "to": R["night"].get("to", 0.0), "speed": R["night"].get("speed", 0.0),
				"seed": R["night_seed"], "source": res["source"]},
			"moveeye": {"seen": res["seen"], "missed": res["missed"], "hidden": res["hidden"],
				"events": (res["hits"] as Array).map(func(h): return {"kind": h["kind"], "st": h["st"], "x": h["x"], "z": h["z"], "near_m": h["near_m"], "vis_s": h["vis_s"], "t_detect": h["t_detect"]})},
			"tour": {"start_h": R["start_h"], "arrive_h": R.get("arrive_h", -1.0), "sunset": R["sunset"], "sunrise": R["sunrise"],
				"camp": R["camp"], "notes": R["notes"], "found": R["found"], "mw_warn": R["mw_warn"], "reads_wrong": R["reads_wrong"]}}
	(rep["rating"] as Dictionary).erase("ranking")
	# the same situation before (another MoveEye version?): compare
	var d := DirAccess.open(DIR + "/berichte")
	var prev = null
	if d != null:
		var fs := Array(d.get_files())
		fs.sort()
		for fn in fs:
			var o = JSON.parse_string(FileAccess.get_file_as_string(DIR + "/berichte/" + fn))
			if o is Dictionary and str(o.get("situation_key", "")) == str(rep["situation_key"]) and str(o.get("id", "")) != str(rep["id"]):
				prev = o
		if fs.size() > 60:
			for i in range(fs.size() - 60):
				d.remove(fs[i])
	if prev != null:
		rep["compare"] = {"id": prev["id"], "mw_version": prev.get("mw_version", ""), "seen": prev["moveeye"]["seen"], "missed": prev["moveeye"]["missed"],
				"stars": prev["stars"]}
	R["report"] = rep
	var f := FileAccess.open(DIR + "/berichte/%s.json" % str(R["id"]), FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(rep, " "))


# =======================================================================================================================
# diary (pictures of the day and the night)
# =======================================================================================================================
func _diary(kind: String, title: String, text: String) -> void:
	if R.is_empty():
		return
	(R["log"] as Array).append({"k": kind, "h": snappedf(main.hour(), 0.01), "title": title, "text": text})


func _snap_later(cap: String, src: String) -> void:
	if _snaps.size() >= 14:
		return
	_snap.call_deferred(cap, src)


func _snap(cap: String, src: String) -> void:
	"""a small picture for the diary: the window view (without this panel) or the head camera of MoveEye"""
	var img: Image = null
	if src == "cam" and not main.vps.is_empty():
		img = (main.vps[0] as SubViewport).get_texture().get_image()
	else:
		var was := visible
		visible = false
		await RenderingServer.frame_post_draw
		img = get_viewport().get_texture().get_image()
		visible = was
		if img != null and not img.is_empty():
			var w := img.get_width()
			var h := img.get_height()
			img = img.get_region(Rect2i(int(w * 0.05), int(h * 0.08), int(w * 0.6), int(h * 0.75)))
	if img == null or img.is_empty():
		return
	img.resize(320, int(320.0 * img.get_height() / maxf(1.0, img.get_width())), Image.INTERPOLATE_BILINEAR)
	_snaps.append([ImageTexture.create_from_image(img), cap])
	if not R.is_empty():
		var dd := DIR + "/tagebuch/" + str(R["id"])
		DirAccess.make_dir_recursive_absolute(dd)
		img.save_png(dd + "/%02d.png" % _snaps.size())
	seq += 1


# =======================================================================================================================
# the panel (same look as the game wizard)
# =======================================================================================================================
func open_ab() -> void:
	_load()
	shown = true
	if R.is_empty() or step == 7:
		step = 0
	if bt() == null and main.scene != "bergtal":
		main.set_scene("bergtal")
	_changed()


func close_ab() -> void:
	shown = false
	_changed()


func _changed() -> void:
	seq += 1


func _ready() -> void:
	Inv.verbinde(self)                                   # A4
	_load()
	W["items"] = blinki_suggest()
	set_anchors_preset(Control.PRESET_FULL_RECT)
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
	title_lab = Label.new()
	title_lab.text = T.t("Bergtal-Abenteuer")
	title_lab.add_theme_font_size_override("font_size", 19)
	title_lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(title_lab)
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.tooltip_text = T.t("Schliessen (Esc) - das Abenteuer läuft weiter")
	x.pressed.connect(close_ab)
	top.add_child(x)
	prog = Control.new()
	prog.custom_minimum_size = Vector2(0, 54)
	prog.draw.connect(_draw_prog)
	prog.mouse_filter = Control.MOUSE_FILTER_STOP
	prog.gui_input.connect(_prog_input)
	v.add_child(prog)
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
	back_btn.text = T.t("‹ Zurück")
	back_btn.custom_minimum_size = Vector2(110, 40)
	back_btn.pressed.connect(func(): op({"do": "back"}))
	nav.add_child(back_btn)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nav.add_child(sp)
	next_btn = Button.new()
	next_btn.custom_minimum_size = Vector2(200, 40)
	next_btn.pressed.connect(func(): op({"do": "next"}))
	if main.UI.has_method("primary"):
		main.UI.primary(next_btn)
	nav.add_child(next_btn)
	karte = Karte.new()
	karte.custom_minimum_size = Vector2(320, 320)
	a2 = preload("res://scripts/abenteuer_figuren.gd").new()
	a2.ab = self
	add_child(a2)
	visible = false
	_layout()


func _layout() -> void:
	"""setup steps: big like the wizard; on the way / in the night: a column on the left (the valley stays visible)"""
	if step in [4, 6]:
		anchor_right = 0.0
		offset_left = 16
		offset_top = 40
		offset_right = 16 + 470
		offset_bottom = -40
	else:
		anchor_right = 1.0
		offset_left = 60
		offset_top = 40
		offset_right = -440
		offset_bottom = -40


func _unhandled_key_input(ev: InputEvent) -> void:
	if visible and ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		close_ab()
		get_viewport().set_input_as_handled()


func _process(dt: float) -> void:
	if not leg.is_empty():
		_tick_leg(dt)
	Ruck.tick(self, dt)                                  # A4: Stirnlampe als echtes Licht
	if not R.is_empty() and step == 6:
		_tick_night(dt)
	_tick_replay(dt)
	if visible != shown:
		visible = shown
		if shown:
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
	if seq != _painted:
		_painted = seq
		_layout()
		_paint()


func _draw_prog() -> void:
	var w := prog.size.x
	var n := STEPS.size()
	var x0 := 50.0
	var x1 := w - 50.0
	var y := 16.0
	prog.draw_line(Vector2(x0, y), Vector2(x1, y), Color(0.2, 0.25, 0.32), 4.0, true)
	prog.draw_line(Vector2(x0, y), Vector2(lerpf(x0, x1, _prog_f / float(n - 1)), y), ACC, 4.0, true)
	var font := get_theme_default_font()
	var narrow := w < 600.0
	for i in range(n):
		var x := lerpf(x0, x1, float(i) / float(n - 1))
		var c := GRN if i < step else (ACC if i == step else Color(0.25, 0.3, 0.37))
		if i == step:
			prog.draw_circle(Vector2(x, y), 13.0 + 3.0 * (0.5 + 0.5 * sin(_pulse * 4.0)), Color(ACC, 0.25))
		prog.draw_circle(Vector2(x, y), 11.0, c)
		prog.draw_string(font, Vector2(x - 12, y + 5), "✓" if i < step else str(i + 1), HORIZONTAL_ALIGNMENT_CENTER, 24, 13, Color.WHITE)
		if not narrow or i == step:
			prog.draw_string(font, Vector2(x - 60, y + 32), T.t(STEPS[i]), HORIZONTAL_ALIGNMENT_CENTER, 120, 12, Color.WHITE if i == step else Color(0.62, 0.68, 0.76))


func _prog_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT and R.is_empty():
		var n := STEPS.size()
		var i := clampi(int(round((ev.position.x - 50.0) / max(1.0, prog.size.x - 100.0) * (n - 1))), 0, n - 1)
		if i < step and i <= 3:
			step = i
			_changed()


func _lab(t: String, sz := 14, col := Color(0.85, 0.88, 0.92), wrap := true) -> Label:
	var l := Label.new()
	l.text = preload("res://scripts/gamewiz.gd").plain(t)
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


func _group(title: String, parent: Control = null) -> VBoxContainer:
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", _box(Color(0.09, 0.11, 0.14), Color(0.18, 0.22, 0.28), 1, 12, 12))
	(parent if parent != null else body).add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	pc.add_child(v)
	if title != "":
		v.add_child(_lab(title, 14, Color(0.62, 0.68, 0.76), false))
	return v


func _card(title: String, text: String, on: bool, cb: Callable, locked := false, badge := "") -> PanelContainer:
	"""a choice like the cards of the wizard: chosen = blue frame and «✓ gewählt»"""
	var pc := PanelContainer.new()
	pc.custom_minimum_size = Vector2(170, 0)
	pc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pc.add_theme_stylebox_override("panel", _box(Color(0.1, 0.16, 0.26) if on else Color(0.1, 0.12, 0.15), ACC if on else Color(0.2, 0.25, 0.32), 2 if on else 1, 14, 12))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(v)
	var tl := _lab(("🔒 " if locked else "") + title, 16, Color(0.55, 0.58, 0.62) if locked else Color.WHITE)
	tl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tl)
	var tx := _lab(text, 12, Color(0.5, 0.53, 0.58) if locked else Color(0.65, 0.7, 0.78))
	tx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tx)
	if badge != "":
		var bl := _lab(badge, 12, ORG, false)
		bl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(bl)
	if on:
		var ok := _lab(T.t("✓ gewählt"), 12, GRN, false)
		ok.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(ok)
	if not locked:
		pc.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		pc.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
				cb.call())
		pc.mouse_entered.connect(func():
			pc.pivot_offset = pc.size / 2.0
			pc.create_tween().tween_property(pc, "scale", Vector2(1.03, 1.03), 0.12))
		pc.mouse_exited.connect(func(): pc.create_tween().tween_property(pc, "scale", Vector2.ONE, 0.12))
	return pc


func _stars(n: int, of: int, sz: float) -> Control:
	"""stars drawn as shapes (the font of the window has no ★ on every PC): gold = got, grey outline = not"""
	var c := Control.new()
	c.custom_minimum_size = Vector2(of * sz * 1.12, sz)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func():
		for i in range(of):
			var ctr := Vector2(sz * 0.56 + i * sz * 1.12, sz * 0.52)
			var pts := PackedVector2Array()
			for k in range(10):
				var a := -PI / 2.0 + k * PI / 5.0
				var r := sz * (0.5 if k % 2 == 0 else 0.21)
				pts.append(ctr + Vector2(cos(a), sin(a)) * r)
			if i < n:
				c.draw_colored_polygon(pts, Color("#ffd166"))
			else:
				pts.append(pts[0])
				c.draw_polyline(pts, Color(0.45, 0.5, 0.58), 1.5, true))
	return c


func _rating(parent: Control, title: String, sich: int, aus: int, ruhe: int) -> void:
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 8)
	parent.add_child(fl)
	if title != "":
		fl.add_child(_lab(title, 13, Color(0.75, 0.8, 0.86), false))
	for e in [[T.t("Sicherheit"), sich], [T.t("Aussicht"), aus], [T.t("Ruhe"), ruhe]]:
		fl.add_child(_lab(str(e[0]), 13, Color(0.85, 0.88, 0.92), false))
		fl.add_child(_stars(int(e[1]), 5, 14.0))


func _grid(n: int) -> GridContainer:
	var g := GridContainer.new()
	g.columns = n
	g.add_theme_constant_override("h_separation", 10)
	g.add_theme_constant_override("v_separation", 10)
	body.add_child(g)
	return g


func _bar(parent: Control, label: String, v: float, vmax: float, col: Color, txt := "") -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	parent.add_child(row)
	var l := _lab(label, 13, Color(0.75, 0.8, 0.86), false)
	l.custom_minimum_size = Vector2(92, 0)
	row.add_child(l)
	var pb := ProgressBar.new()
	pb.min_value = 0.0
	pb.max_value = maxf(0.01, vmax)
	pb.value = clampf(v, 0.0, vmax)
	pb.show_percentage = false
	pb.custom_minimum_size = Vector2(150, 14)
	pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var fill := StyleBoxFlat.new()
	fill.bg_color = col
	fill.set_corner_radius_all(5)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.14, 0.17, 0.22)
	bg.set_corner_radius_all(5)
	pb.add_theme_stylebox_override("fill", fill)
	pb.add_theme_stylebox_override("background", bg)
	row.add_child(pb)
	var vl := _lab(txt if txt != "" else "%d" % int(v), 13, Color.WHITE, false)
	vl.custom_minimum_size = Vector2(70, 0)
	row.add_child(vl)


func _btn(parent: Control, text: String, cb: Callable, primary := false, disabled := false) -> Button:
	var b := Button.new()
	b.text = preload("res://scripts/gamewiz.gd").plain(text)
	if parent is VBoxContainer:                          # (in a row the text would get no width)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.disabled = disabled
	b.pressed.connect(cb)
	if primary and main.UI.has_method("primary"):
		main.UI.primary(b)
	parent.add_child(b)
	return b


func _karte_update() -> void:
	if karte == null:
		return
	karte.mode = "schatz"
	karte.pieces = P.get("pieces", [0]).duplicate()
	if not 0 in karte.pieces:
		karte.pieces.append(0)
	var sy := []
	for ch in D.CHAPTERS:
		if int(ch["piece"]) in karte.pieces:
			var st: Array = ch["stages"]
			var last: Dictionary = st[-1]
			var end: Vector2 = last["walk"][-1] if last.has("walk") else Vector2.ZERO
			sy.append([ch["symbol"], end])
	if bool(P.get("finale", false)):
		sy.append(["kreuz", Vector2(-878, 428)])
	karte.symbols = sy
	karte.route = PackedVector2Array(R.get("walked", []))
	if not leg.is_empty():
		var r2: PackedVector2Array = karte.route
		r2.append(R["pos"])
		karte.route = r2
	var pl := PackedVector2Array()
	if not R.is_empty() and step == 4:
		var ch2 := chapter()
		for i in range(int(R["stage"]), (ch2["stages"] as Array).size()):
			var s2: Dictionary = ch2["stages"][i]
			if s2.has("walk"):
				for q in s2["walk"]:
					pl.append(q)
			elif s2.has("fork"):
				for q in s2["fork"][1][1]:
					pl.append(q)
	karte.plan = pl
	var orient: String = main.bt_orient
	karte.me = R.get("pos", Vector2.INF) if orient == "leicht" and not R.is_empty() else Vector2.INF
	karte.compass = orient != "schwer"
	var sp: Vector2 = main.sun_pos()
	karte.sun_az = sp.y if sp.x > -4.0 else -1.0
	karte.sun_el = sp.x
	karte.marks = main.bt_marks if bool(P.get("finale", false)) else []
	karte.queue_redraw()


func _karte_in(parent: Control, h := 320.0) -> void:
	if karte.get_parent() != null:
		karte.get_parent().remove_child(karte)
	karte.custom_minimum_size = Vector2(h, h)
	karte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(karte)
	_karte_update()


func _paint() -> void:
	if karte != null and karte.get_parent() != null:
		karte.get_parent().remove_child(karte)
	for c in body.get_children():
		c.queue_free()
	if error != "":
		body.add_child(_lab(error, 13, REDC))
	match step:
		0:
			_paint_chapter()
		1:
			_paint_mood()
		2:
			_paint_level()
		3:
			_paint_pack()
		4, 6:
			_paint_hud()
		5:
			_paint_camp()
		7:
			_paint_morning()
	back_btn.visible = step in [1, 2, 3]
	next_btn.visible = step in [0, 1, 2, 3, 5, 7]
	next_btn.text = preload("res://scripts/gamewiz.gd").plain(T.t({0: "Weiter: Stimmung ›", 1: "Weiter: Schwierigkeit ›", 2: "Weiter: Rucksack packen ›",
			3: "Los geht's! ›", 5: "Lager aufschlagen ›", 7: "Nächstes Kapitel ›"}.get(step, "Weiter ›")))
	next_btn.disabled = step == 3 and (pack_kg() > float(D.PACKS[str(W["pack"])][3]) or pack_l() > float(D.PACKS[str(W["pack"])][1]))
	if step == 7 and int(R.get("chapter", 1)) >= 5:
		next_btn.text = T.t("Neues Abenteuer ›")
	if step != _last_step:
		var dir := 1.0 if step > _last_step else -1.0
		_last_step = step
		_slide.add_theme_constant_override("margin_left", int(40 * dir))
		_slide.add_theme_constant_override("margin_right", int(-40 * dir))
		body.modulate.a = 0.0
		var tw := create_tween().set_parallel(true)
		tw.tween_method(func(m): _slide.add_theme_constant_override("margin_left", int(m)); _slide.add_theme_constant_override("margin_right", int(-m)), 40.0 * dir, 0.0, 0.25).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tw.tween_property(body, "modulate:a", 1.0, 0.2)


func _paint_chapter() -> void:
	body.add_child(_lab(T.t("Die Karte des Bergführers"), 22, Color.WHITE))
	body.add_child(_lab(T.t("Dein Grossvater war Bergführer. Sein Brief und eine alte Karte führen dich in fünf Kapiteln durchs Bergtal - jedes Abenteuer ist ein Kapitel."), 13, Color(0.6, 0.66, 0.74)))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	body.add_child(row)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 8)
	row.add_child(left)
	var mapbox := VBoxContainer.new()
	row.add_child(mapbox)
	_karte_in(mapbox, 300.0)
	var lv := level()
	var nx: int = D.LEVEL_XP[mini(lv, D.LEVEL_XP.size() - 1)]
	var g := _group(T.t("Stufe %d · %d Erfahrung") % [lv, int(P["xp"])], left)
	_bar(g, T.t("Erfahrung"), float(P["xp"]) - float(D.LEVEL_XP[lv - 1]), float(nx - int(D.LEVEL_XP[lv - 1])) if lv < D.LEVEL_XP.size() else 1.0, ACC,
			T.t("noch %d") % maxi(0, nx - int(P["xp"])) if lv < D.LEVEL_XP.size() else T.t("höchste Stufe"))
	var nexts := []
	for l in D.UNLOCKS:
		if int(l) > lv:
			nexts.append(T.t("Stufe %d: %s") % [int(l), T.t(str(D.ITEMS[D.UNLOCKS[l]][0]))])
	if not nexts.is_empty():
		g.add_child(_lab(T.t("Wird frei: ") + ", ".join(nexts), 12, Color(0.6, 0.66, 0.74)))
	var gc := GridContainer.new()
	gc.columns = 1
	gc.add_theme_constant_override("v_separation", 8)
	left.add_child(gc)
	for ch in D.CHAPTERS:
		var n: int = int(ch["id"])
		var open: bool = n <= int(P["chapter"])
		var st: int = int(P["stars"].get(str(n), 0))
		var stars := T.t("%d von 3 Sternen") % st
		var nn := n
		gc.add_child(_card(T.t(str(ch["title"])), T.t(str(ch["intro"])) if n == int(W["chapter"]) else "", n == int(W["chapter"]),
				func(): op({"do": "pick", "key": "chapter", "value": nn}), not open, stars if open else T.t("noch nicht frei")))
	if a2 != null:
		a2.paint_overview(left)                          # A2: people in the valley, side tasks
	if not situations().is_empty() or dev_open:
		_dev_box(left)


func _dev_box(parent: Control) -> void:
	var eb := Button.new()
	eb.text = ("▾ " if dev_open else "▸ ") + T.t("Testgelände: Situation genau gleich nochmals abspielen")
	eb.flat = true
	eb.alignment = HORIZONTAL_ALIGNMENT_LEFT
	eb.pressed.connect(func(): dev_open = not dev_open; _changed())
	parent.add_child(eb)
	if not dev_open:
		return
	var g := _group("", parent)
	var lst := situations()
	if lst.is_empty():
		g.add_child(_lab(T.t("Noch keine gespeicherte Situation (am Morgen: «Situation speichern»)."), 13))
		return
	var ob := OptionButton.new()
	for s in lst:
		ob.add_item(s)
	ob.select(lst.size() - 1)
	g.add_child(ob)
	_btn(g, T.t("▶ Genau gleich nochmals abspielen (gleicher Seed, gleiche Entscheide)"), func(): op({"do": "replay", "value": lst[ob.selected]}), true)


func _paint_mood() -> void:
	body.add_child(_lab(T.t("Welche Stimmung soll das Abenteuer haben?"), 22, Color.WHITE))
	body.add_child(_lab(T.t("Die Stimmung ändert die Texte, die Ereignisse unterwegs und wie oft das Wetter umschlägt."), 13, Color(0.6, 0.66, 0.74)))
	var g := _grid(3)
	for k in D.MOOD_ORDER:
		var kk: String = k
		g.add_child(_card(T.t(str(D.MOODS[k][0])), T.t(str(D.MOODS[k][1])), str(W["mood"]) == k, func(): op({"do": "pick", "key": "mood", "value": kk})))
	if main.horror == null:
		g.add_child(_card(T.t(str(D.HORROR_SLOT[1])), T.t(str(D.HORROR_SLOT[2])), false, func(): pass, true))
		return
	# 3D-4.40: the 5th mood = Horror-Modus «Das Hospiz» (bergtal_horror.gd, password) - the only way in (no button under «Szene»)
	var hs: Dictionary = main.horror.mood_slot()
	var kids := bool(hs.get("kids", false))
	g.add_child(_card(("🔒 " if bool(hs.get("locked", true)) and not kids else "") + str(hs.get("name", "Horror")),
			T.t("Im Kinder-Modus gesperrt.") if kids else str(hs.get("hint", "")), false, func():
				close_ab()
				main.horror.open_from_mood(func(started):
					if not bool(started):
						open_ab()), kids))


func _paint_level() -> void:
	body.add_child(_lab(T.t("Wie schwierig - und was ist dein Ziel?"), 22, Color.WHITE))
	var g := _grid(3)
	for k in D.LEVEL_ORDER:
		var kk: String = k
		g.add_child(_card(T.t(str(D.LEVELS[k][0])), T.t(str(D.LEVELS[k][1])), str(W["level"]) == k, func(): op({"do": "pick", "key": "level", "value": kk})))
	body.add_child(_lab(T.t("Ziel"), 15, Color.WHITE, false))
	var g2 := _grid(3)
	for k in D.GOAL_ORDER:
		var kk: String = k
		g2.add_child(_card(T.t(str(D.GOALS[k][0])), T.t(str(D.GOALS[k][1])), str(W["goal"]) == k, func(): op({"do": "pick", "key": "goal", "value": kk})))
	var gg := _group(T.t("Einstellungen"))
	var row := HBoxContainer.new()
	gg.add_child(row)
	var l := _lab(T.t("Jahreszeit im Bergtal"), 14)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	var ob := OptionButton.new()
	var opts := [["fruehling", "Frühling"], ["sommer", "Sommer"], ["herbst", "Herbst (Lärchen gelb, Nebel)"], ["winter", "Winter (Schnee, Eis)"]]
	for i in range(opts.size()):
		ob.add_item(T.t(opts[i][1]))
		if opts[i][0] == str(W["season"]):
			ob.select(i)
	ob.item_selected.connect(func(i): op({"do": "pick", "key": "season", "value": opts[i][0]}))
	row.add_child(ob)
	var row2 := HBoxContainer.new()
	gg.add_child(row2)
	var l2 := _lab(T.t("Die Nacht im Zeitraffer dauert"), 14)
	l2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row2.add_child(l2)
	var ob2 := OptionButton.new()
	var tops := [3, 5, 8]
	for i in range(tops.size()):
		ob2.add_item(T.t("%d Minuten") % tops[i])
		if tops[i] == int(W["tempo"]):
			ob2.select(i)
	ob2.item_selected.connect(func(i): op({"do": "pick", "key": "tempo", "value": tops[i]}))
	row2.add_child(ob2)
	var ss := sunset_h()
	gg.add_child(_lab(T.t("Sonnenuntergang heute im Bergtal: %s · Sonnenaufgang: %s") % [hm(ss), hm(sunrise_h())], 12, Color(0.6, 0.66, 0.74)))


func _paint_pack() -> void:
	var pk: Array = D.PACKS[str(W["pack"])]
	var kg := pack_kg()
	var li := pack_l()
	body.add_child(_lab(T.t("Rucksack packen"), 22, Color.WHITE))
	body.add_child(_lab(T.t("Was nimmst du mit? Leichter = schneller, schwerer = langsamer und öfter Pause. MoveEye kommt immer mit und zählt nicht als Gewicht."), 13, Color(0.6, 0.66, 0.74)))
	var g := _grid(3)
	for k in ["30", "50", "70"]:
		var kk: String = k
		var pp: Array = D.PACKS[k]
		g.add_child(_card(T.t(str(pp[0])), T.t("Leer %.1f kg · bequem bis %d kg") % [float(pp[2]), int(pp[3])], str(W["pack"]) == k, func(): op({"do": "pick", "key": "pack", "value": kk})))
	var st := _group(T.t("Gewicht und Platz"))
	_bar(st, T.t("Gewicht"), kg, float(pk[3]), REDC if kg > float(pk[3]) else (ORG if kg > float(pk[3]) * 0.85 else GRN), "%.1f / %d kg" % [kg, int(pk[3])])
	_bar(st, T.t("Platz"), li, float(pk[1]), REDC if li > float(pk[1]) else ACC, "%d / %d L" % [int(li), int(pk[1])])
	var bl := HBoxContainer.new()
	st.add_child(bl)
	_btn(bl, T.t("Blinki schlägt vor (für Anfänger)"), func(): op({"do": "blinki"}))
	_btn(bl, T.t("Alles ausräumen"), func(): op({"do": "empty"}))
	var gi := _group(T.t("Ausrüstung"))
	for id in D.ITEM_ORDER:
		var it: Array = D.ITEMS[id]
		var unl := item_unlocked(id)
		if id == "karabiner" and not unl:
			continue
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		gi.add_child(row)
		var nm := _lab(T.t(str(it[0])) + ("" if unl else "  " + T.t("(ab Stufe %d)") % int(it[6])), 14, Color.WHITE if unl else Color(0.5, 0.53, 0.58), false)
		nm.custom_minimum_size = Vector2(210, 0)
		row.add_child(nm)
		var tx := _lab(T.t(str(it[4])) + "  · %.1f kg" % float(it[1]), 12, Color(0.6, 0.66, 0.74))
		tx.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(tx)
		var idd: String = id
		if int(it[5]) > 1:
			var sb := SpinBox.new()
			sb.min_value = 0
			sb.max_value = int(it[5])
			sb.value = int(W["items"].get(id, 0))
			sb.editable = unl
			sb.value_changed.connect(func(x): op({"do": "item", "key": idd, "value": int(x)}))
			row.add_child(sb)
		else:
			var cb := CheckButton.new()
			cb.button_pressed = int(W["items"].get(id, 0)) > 0
			cb.disabled = not unl
			cb.toggled.connect(func(x): op({"do": "item", "key": idd, "value": 1 if x else 0}))
			row.add_child(cb)
	Ruck.paint_pack(self)                                # A4: gefundene Ausrüstung


func _stat_box(parent: Control) -> void:
	var g := _group("", parent)
	var smax: float = float(R["smax"])
	var s: float = float(R["stamina"])
	_bar(g, T.t("Kraft"), s, smax, GRN if s > smax * 0.4 else (ORG if s > smax * 0.15 else REDC))
	if Ruck.essen_an(self):                              # A4: in «Leicht» keine Essen-/Wasser-Balken
		_bar(g, T.t("Essen"), float(R["food"]), 100.0, ORG, "%d %%" % int(R["food"]))
		_bar(g, T.t("Wasser"), float(R["water"]), maxf(1.0, float(int(R["items"].get("wasser", 0)))), ACC, "%.1f L" % float(R["water"]))
	var kg := pack_kg(R["items"]) + float(R["found_kg"])
	var pk: Array = D.PACKS[str(R["pack"])]
	_bar(g, T.t("Gewicht"), kg, float(pk[3]), ORG if kg > float(pk[3]) * 0.85 else Color(0.6, 0.66, 0.74), "%.1f kg" % kg)
	var h: float = main.hour()
	var sp: Vector2 = main.sun_pos()
	var line := T.t("%s Uhr · Sonnenuntergang %s · Höhe %d m") % [hm(h), hm(float(R["sunset"])), int(Bt.H(R["pos"].x, R["pos"].y) + Bt.ALT0)]
	if sp.x > 0.0 and main.bt_orient != "schwer":
		line += " · " + T.t("Sonne im %s") % T.t(dir_word(sp.y))
	g.add_child(_lab(line, 12, Color(0.75, 0.8, 0.86)))
	var flags := []
	if bool(R.get("wet", false)):
		flags.append(T.t("nass"))
	if int(R.get("cold", 0)) > 0:
		flags.append(T.t("friert"))
	if bool(R.get("hurt", false)):
		flags.append(T.t("Fuss verstaucht"))
	if not flags.is_empty():
		g.add_child(_lab(", ".join(flags), 12, ORG))
	Ruck.stat_extra(self, g)                             # A4: Rucksack-Inhalt, hungrig / durstig


func _paint_hud() -> void:
	if step == 6:
		_paint_night()
		return
	if R.is_empty():
		return
	for c in body.get_children():
		if c != karte:
			c.queue_free()
	if karte.get_parent() != null:
		karte.get_parent().remove_child(karte)
	var ch := chapter()
	body.add_child(_lab(T.t(str(ch["title"])), 18, Color.WHITE))
	if R.has("replay_of"):
		body.add_child(_lab(T.t("Wiedergabe: %s") % str(R["replay_of"]), 12, ORG))
	_stat_box(body)
	_karte_in(body, 260.0)
	var pe: Dictionary = R["pending"]
	if bool(R.get("walking", false)):
		var nm := str(R.get("now", ""))
		body.add_child(_lab(T.t("Unterwegs: %s …") % nm if nm != "" else T.t("Unterwegs …"), 15, Color.WHITE))
	elif not pe.is_empty():
		var g := _group(str(pe["title"]))
		g.add_child(_lab(str(pe["text"]), 14, Color.WHITE))
		for o in pe["options"]:
			var vv: String = str(o[0])
			var b := _btn(g, str(o[1]), func(): op({"do": "choose", "value": vv}), (pe["options"] as Array).size() == 1)
			b.custom_minimum_size = Vector2(0, 40)
	var acts := HFlowContainer.new()
	acts.add_theme_constant_override("h_separation", 8)
	acts.add_theme_constant_override("v_separation", 8)
	body.add_child(acts)
	var idle := not bool(R.get("walking", false))
	_btn(acts, T.t("Pause (15 Min.)") + (T.t(" - Bank") if bool(R.get("bank", false)) else ""), func(): op({"do": "pause"}), false, not idle)
	if bool(R.get("bach", false)):
		_btn(acts, T.t("Wasser auffüllen (Bach)"), func(): op({"do": "refill"}), false, not idle)
	_btn(acts, T.t("Hier übernachten"), func(): op({"do": "camp_here"}), false, not idle or not pe.is_empty())
	Ruck.hud_buttons(self, acts, idle and pe.is_empty())   # A4: Essen, Quelle, Kochen, Tauschen
	Ruck.paint_tausch(self, body)                        # A4: Tausch-Fenster
	var lg := _group(T.t("Tagebuch"))
	var lst: Array = R["log"]
	for e in lst.slice(maxi(0, lst.size() - 4)):
		lg.add_child(_lab("%s  %s - %s" % [hm(float(e["h"])), str(e["title"]), str(e["text"])], 12))


func _paint_camp() -> void:
	var ch := chapter()
	body.add_child(_lab(T.t("Nachtlager") + (" - " + T.t(str(ch["title"])) if bool(R.get("arrived", false)) else ""), 22, Color.WHITE))
	if bool(R.get("arrived", false)):
		body.add_child(_lab(T.t(str(ch["found"])), 14, Color(0.95, 0.85, 0.6)))
	var h: float = main.hour()
	body.add_child(_lab(T.t("Es ist %s Uhr. Sonnenuntergang: %s.") % [hm(h), hm(float(R["sunset"]))] + " " + (T.t("Noch hell genug zum Aufbauen.") if h < float(R["sunset"]) else T.t("Es ist schon dunkel.")), 13, Color(0.6, 0.66, 0.74)))
	var b = bt()
	var p: Vector2 = R["camp_xz"]
	if b != null:
		var ev: Dictionary = b.evaluate(p.x, p.y)
		_rating(body, T.t("Der Platz:"), int(ev.get("sicherheit", 3)), int(ev.get("aussicht", 3)), int(ev.get("ruhe", 3)))
	body.add_child(_lab(T.t("Wo soll MoveEye stehen? (Höhe und Blickwinkel ändern, was MoveEye sieht)"), 15, Color.WHITE, false))
	var g := _grid(3)
	var cur := str(R.get("mount_pick", "rucksack"))
	for mm in mounts():
		var k: String = mm[0]
		g.add_child(_card(T.t(str(Bt.MOUNTS[k][0])), T.t("Höhe %.1f m") % float(Bt.MOUNTS[k][1]), cur == k, func(): R["mount_pick"] = k; _changed(), not mm[1],
				"" if mm[1] else T.t({"zelt": "braucht ein Zelt", "stativ": "braucht das Mini-Stativ", "baum": "kein Baum in der Nähe"}.get(k, ""))))
	var gg := _group(T.t("Lager"))
	var row := HBoxContainer.new()
	gg.add_child(row)
	var l := _lab(T.t("Windschutzmauer aus Steinen bauen (20 Min., weniger Wind)"), 14)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	var cb := CheckButton.new()
	cb.button_pressed = bool(R.get("wall_pick", false))
	cb.toggled.connect(func(x): R["wall_pick"] = x)
	row.add_child(cb)
	gg.add_child(_lab(T.t("Schlafen: %s") % T.t(_bed_name(bed_of())), 13))
	if not Ruck.huette(self).is_empty():                 # A4: in der Hütte kochen
		var ka := HFlowContainer.new()
		gg.add_child(ka)
		Ruck.hud_buttons(self, ka, true)
	if a2 != null:
		a2.paint_camp(body)                              # A2: people at the camp, the talk


func _paint_night() -> void:
	for c in body.get_children():
		c.queue_free()
	var n = main.nacht
	body.add_child(_lab(T.t("Die Nacht"), 20, Color.WHITE))
	body.add_child(_lab(T.t(str(D.FLAVOR[R["mood"]]["night"])), 13, Color(0.6, 0.66, 0.74)))
	if (R["night"] as Dictionary).is_empty():
		body.add_child(_lab(T.t("MoveEye bewacht das Lager. Die ganze Nacht läuft im Zeitraffer (%d Minuten); am Morgen siehst du, was passiert ist.") % int(W["tempo"]), 14))
		if main.now() - main.mw_t > 10.0:
			body.add_child(_lab(T.t("MoveEye ist nicht verbunden - der Simulator schätzt, was MoveEye gesehen hätte."), 13, ORG))
		var b := _btn(body, T.t("Nacht starten (Zeitraffer)"), func(): op({"do": "night"}), true)
		b.custom_minimum_size = Vector2(0, 44)
		return
	var g := _group("")
	if n.running:
		var tot: float = maxf(1.0, float(n.total_s))
		_bar(g, T.t("Nacht"), float(n.elapsed()), tot, Color(0.4, 0.45, 0.8), "%s" % hm(main.hour()))
		g.add_child(_lab(T.t("Ereignis %d von %d · MoveEye hat %d gemeldet") % [int(n.next_i), (n.plan as Array).size(), _night_seen.size()], 13))
	for rec in (n.truth as Array).slice(maxi(0, (n.truth as Array).size() - 6)):
		var seen: bool = _night_seen.has(int(rec["id"]))
		g.add_child(_lab("%s  %s%s" % [hm(float(rec.get("h0", 0.0))), T.t(_kind_name(str(rec["kind"]))), ("  - " + T.t("MoveEye meldet")) if seen else ""], 12, GRN if seen else Color(0.75, 0.8, 0.86)))


func _paint_morning() -> void:
	var res: Dictionary = R.get("result", {})
	if res.is_empty():
		return
	var ch := chapter()
	var st: int = int(res["stars"])
	body.add_child(_lab(T.t("Der Morgen - %s") % T.t(str(ch["title"])), 22, Color.WHITE))
	body.add_child(_stars(st, 3, 34.0))
	var why := []
	why.append(T.t("Ziel erreicht") if bool(R.get("arrived", false)) else T.t("Ziel nicht erreicht"))
	if str(R["goal"]) == "gipfel":
		why.append(T.t("vor der Sonne auf dem Gipfel") if bool(res["summit_ok"]) else T.t("zu spät auf dem Gipfel"))
	else:
		why.append(T.t("Lager vor der Dunkelheit") if bool(res["sunset_ok"]) else T.t("Lager erst nach Sonnenuntergang"))
	body.add_child(_lab(", ".join(why), 13, Color(0.6, 0.66, 0.74)))
	if bool(res.get("finale", false)):
		var fg := _group(T.t("Die Überraschung"))
		for line in D.FINALE:
			fg.add_child(_lab(T.t(line), 15, Color(0.97, 0.9, 0.7)))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	body.add_child(row)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 8)
	row.add_child(left)
	var rt: Dictionary = res["rating"]
	var g := _group(T.t("Wie gut war dein Platz?"), left)
	_rating(g, "", int(rt.get("sicherheit", 3)), int(rt.get("aussicht", 3)), int(rt.get("ruhe", 3)))
	var g2 := _group(T.t("Bericht von MoveEye"), left)
	g2.add_child(_lab(T.t("%d gemeldet · %d verpasst · %d nicht im Bild") % [int(res["seen"]), int(res["missed"]), int(res["hidden"])], 14, Color.WHITE))
	if str(res["source"]) != "moveeye":
		g2.add_child(_lab(T.t("(MoveEye war nicht verbunden - geschätzt: lange genug im Bild = gemeldet)"), 12, ORG))
	if float(res["battery_h"]) >= 0.0:
		g2.add_child(_lab(T.t("Ohne Powerbank war der Akku von MoveEye in der Kälte um %s leer - danach hätte es nichts mehr gemeldet.") % hm(float(res["battery_h"])), 12, ORG))
	for h in res["hits"]:
		var col: Color = {"seen": GRN, "missed": REDC}.get(str(h["st"]), Color(0.6, 0.63, 0.68))
		var tt: String = {"seen": "gemeldet", "missed": "verpasst", "hidden": "nicht im Bild"}.get(str(h["st"]), "")
		g2.add_child(_lab("%s  %s - %s%s" % [hm(float(h["h"])), str(h["label"]), T.t(tt), (" (%.1f s)" % float(h["t_detect"])) if float(h["t_detect"]) >= 0.0 else ""], 12, col))
	var notes: Array = res["notes"]
	if not notes.is_empty():
		var g3 := _group(T.t("Was gefehlt hat"), left)
		var done := {}
		for k in notes:
			if not done.has(k):
				done[k] = true
				g3.add_child(_lab(_forgot_text(str(k)), 13, ORG))
	var g4 := _group(T.t("Erfahrung"), left)
	g4.add_child(_lab(T.t("+%d Erfahrung · Stufe %d") % [int(res["xp"]), int(res["level"])], 14, Color.WHITE))
	for u in res["unlocked"]:
		g4.add_child(_lab(T.t("Neu frei: %s") % T.t(str(D.ITEMS[u][0])), 14, GRN))
	var right := VBoxContainer.new()
	right.add_theme_constant_override("separation", 8)
	row.add_child(right)
	right.add_child(_lab(T.t("Treffer-Karte der Nacht"), 13, Color(0.62, 0.68, 0.76), false))
	var hk = Karte.new()
	hk.mode = "treffer"
	hk.hits = res["hits"]
	hk.cam_yaw = (main.cams[0] as Camera3D).global_rotation.y if not main.cams.is_empty() else 0.0
	hk.custom_minimum_size = Vector2(260, 260)
	right.add_child(hk)
	right.add_child(_lab(T.t("grün = gemeldet, rot = verpasst, grau = nicht im Bild"), 11, Color(0.6, 0.66, 0.74)))
	_karte_in(right, 260.0)
	# the diary with pictures of the day and the night
	var dg := _group(T.t("Tagebuch"))
	if not _snaps.is_empty():
		var fl := HFlowContainer.new()
		fl.add_theme_constant_override("h_separation", 8)
		fl.add_theme_constant_override("v_separation", 8)
		dg.add_child(fl)
		for s in _snaps:
			var vb := VBoxContainer.new()
			fl.add_child(vb)
			var tr := TextureRect.new()
			tr.texture = s[0]
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			tr.custom_minimum_size = Vector2(160, 96)
			vb.add_child(tr)
			var cl := _lab(str(s[1]), 11, Color(0.75, 0.8, 0.86))
			cl.custom_minimum_size = Vector2(160, 0)
			vb.add_child(cl)
	for e in R["log"]:
		dg.add_child(_lab("%s  %s - %s" % [hm(float(e["h"])), str(e["title"]), str(e["text"])], 12))
	# test ground
	var eb := Button.new()
	eb.text = ("▾ " if dev_open else "▸ ") + T.t("Testgelände (Situation speichern, nochmals abspielen, Bericht)")
	eb.flat = true
	eb.alignment = HORIZONTAL_ALIGNMENT_LEFT
	eb.pressed.connect(func(): dev_open = not dev_open; _changed())
	body.add_child(eb)
	if dev_open:
		var tg := _group("")
		var rep: Dictionary = R.get("report", {})
		tg.add_child(_lab(T.t("Seed %d · Bericht: %s") % [int(R["seed"]), ProjectSettings.globalize_path(DIR + "/berichte/%s.json" % str(R["id"]))], 12))
		if rep.has("compare"):
			var cp: Dictionary = rep["compare"]
			tg.add_child(_lab(T.t("Gleiche Situation vorher (MoveEye %s): %d gemeldet, %d verpasst - jetzt (MoveEye %s): %d gemeldet, %d verpasst") % [str(cp["mw_version"]) if str(cp["mw_version"]) != "" else "-",
					int(cp["seen"]), int(cp["missed"]), str(rep.get("mw_version", "")) if str(rep.get("mw_version", "")) != "" else "-", int(res["seen"]), int(res["missed"])], 13, Color.WHITE))
		var hb := HFlowContainer.new()
		hb.add_theme_constant_override("h_separation", 8)
		tg.add_child(hb)
		_btn(hb, T.t("Situation speichern"), func(): op({"do": "save"}))
		_btn(hb, T.t("▶ Genau gleich nochmals abspielen"), func(): save_situation(); op({"do": "replay"}))
		_btn(hb, T.t("Ordner der Berichte öffnen"), func(): OS.shell_open(ProjectSettings.globalize_path(DIR + "/berichte")))


# =======================================================================================================================
# control (window buttons and the control API use the same operations)
# =======================================================================================================================
func op(d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "state"))
	error = ""
	var out := {"ok": true}
	match what:
		"open":
			open_ab()
		"close":
			close_ab()
		"pick":
			var k := str(d.get("key", ""))
			var v = d.get("value")
			if k == "chapter":
				if int(v) <= int(P["chapter"]):
					W["chapter"] = int(v)
			elif k == "tempo":
				W["tempo"] = int(v)
			elif k in ["mood", "level", "goal", "season", "pack"]:
				W[k] = str(v)
			_changed()
		"item":
			var id := str(d.get("key", ""))
			if D.ITEMS.has(id) and item_unlocked(id):
				W["items"][id] = clampi(int(d.get("value", 0)), 0, int(D.ITEMS[id][5]))
				if int(W["items"][id]) == 0:
					W["items"].erase(id)
			_changed()
		"items":
			W["items"] = {}
			var it: Dictionary = d.get("value", {})
			for k2 in it:
				if D.ITEMS.has(k2) and item_unlocked(k2):
					W["items"][k2] = int(it[k2])
			_changed()
		"blinki":
			W["items"] = blinki_suggest()
			_changed()
		"empty":
			W["items"] = {}
			_changed()
		"next":
			if step < 3:
				step += 1
				if step == 3 and W["items"].is_empty():
					W["items"] = blinki_suggest()
				_changed()
			elif step == 3:
				R = {}
				var it0: Dictionary = (W["items"] as Dictionary).duplicate()
				out = start_run(int(d.get("seed", 0)))
				if not R.is_empty():
					R["items0"] = it0
			elif step == 5:
				out = set_camp(str(d.get("mount", R.get("mount_pick", "rucksack"))), bool(d.get("wall", R.get("wall_pick", false))))
			elif step == 7:
				R = {}
				leg = {}
				W["chapter"] = clampi(int(P["chapter"]), 1, 5)
				step = 0
				_changed()
		"back":
			if step in [1, 2, 3]:
				step -= 1
				_changed()
		"start":
			for k3 in ["chapter", "mood", "level", "goal", "season", "pack", "tempo"]:
				if d.has(k3):
					W[k3] = d[k3] if not k3 in ["chapter", "tempo"] else int(d[k3])
			if d.has("items"):
				op({"do": "items", "value": d["items"]})
			shown = true
			R = {}
			var it1: Dictionary = (W["items"] as Dictionary).duplicate()
			out = start_run(int(d.get("seed", 0)))
			if not R.is_empty():
				R["items0"] = it1
		"choose":
			out = choose(str(d.get("value", "")))
		"pause":
			out = do_pause()
		"refill":
			out = do_refill()
		"camp_here":
			out = camp_here()
		"camp":
			out = set_camp(str(d.get("mount", "rucksack")), bool(d.get("wall", false)))
		"night":
			out = start_night()
		"save":
			out = save_situation(str(d.get("value", "")))
		"situations":
			out = {"ok": true, "list": situations()}
		"replay":
			out = replay(str(d.get("value", "")))
		"report":
			out = {"ok": not (R.get("report", {}) as Dictionary).is_empty(), "report": R.get("report", {})}
		"fast":
			fast = bool(d.get("value", true))
		"a2":
			out = a2.op(d) if a2 != null else {"ok": false}
		"dev":
			dev_open = bool(d.get("value", not dev_open))
			_changed()
		"probe":                                       # tests: who is near MoveEye now, and does a camera see it?
			var lst := []
			for v in main.visitors.get_children():
				if v.has_method("add_torch") or "kind" in v:
					lst.append({"kind": str(v.kind), "pos": [snappedf(v.position.x, 0.1), snappedf(v.position.z, 0.1)], "cam": main.testrun.visible(v),
							"thermal": main.testrun.thermal_visible(v), "done": bool(v.done)})
			var cf: Vector3 = -(main.cams[0] as Camera3D).global_transform.basis.z if not main.cams.is_empty() else Vector3.ZERO
			out = {"ok": true, "visitors": lst, "cam_fwd": [snappedf(cf.x, 0.01), snappedf(cf.z, 0.01)], "dark": main.is_dark(), "hour": main.hour(),
					"head": [snappedf(main.head.global_position.y, 0.01)] if main.head != null else []}
		"reset":
			P = {"chapter": 1, "xp": 0, "stars": {}, "finds": [], "finale": false, "runs": [], "pieces": []}
			if d.has("chapter"):
				P["chapter"] = clampi(int(d["chapter"]), 1, 5)
			if d.has("xp"):
				P["xp"] = int(d["xp"])
			_save()
			W["chapter"] = int(P["chapter"])
			R = {}
			leg = {}
			step = 0
			_changed()
		_:
			if what.begins_with("a4_"):                  # A4: Rucksack (Essen, Kochen, Tausch, Inventar)
				out = Ruck.op(self, what, d)
	if not out.has("state"):
		out["state"] = state()
	return out


func state() -> Dictionary:
	var pe: Dictionary = R.get("pending", {})
	return {"shown": shown, "step": step, "step_name": STEPS[step], "chapter": W["chapter"], "progress": {"chapter": P.get("chapter", 1), "xp": P.get("xp", 0),
			"level": level(), "stars": P.get("stars", {}), "finale": P.get("finale", false)}, "choice": {"mood": W["mood"], "level": W["level"],
			"goal": W["goal"], "season": W["season"], "pack": W["pack"], "items": W["items"], "kg": pack_kg(), "liters": pack_l(), "tempo": W["tempo"]},
			"run": {} if R.is_empty() else {"seed": R["seed"], "goal": R["goal"], "stage": R["stage"], "walking": R.get("walking", false),
				"stamina": snappedf(float(R["stamina"]), 0.1), "food": snappedf(float(R["food"]), 0.1), "water": snappedf(float(R["water"]), 0.01),
				"pos": [snappedf(R["pos"].x, 0.1), snappedf(R["pos"].y, 0.1)], "hour": snappedf(main.hour(), 0.01), "sunset": R["sunset"],
				"sunrise": R["sunrise"], "pending": {"kind": pe.get("kind", ""), "title": pe.get("title", ""), "options": pe.get("options", [])} if not pe.is_empty() else {},
				"notes": R["notes"], "found": R["found"], "arrived": R.get("arrived", false), "night": R["night"], "result_stars": R.get("result", {}).get("stars", -1),
				"log": (R["log"] as Array).slice(-6), "choices": choices.size(), "replaying": replaying},
			"error": error}


var _night_starting := false


func status() -> String:
	"""main.busy_with: the adventure has the world (clock, weather, visitors) - but not while it starts its own night"""
	return "Bergtal-Abenteuer" if not R.is_empty() and step in [4, 5, 6] and not _night_starting and not (main.nacht != null and main.nacht.running) else ""


func _say(t: String) -> void:
	main.start_info = t
