extends Node
## Paket «PIR, Mikrofon & Umgebungsgeräusche» (Zweig real-pir-ton, 31.10.2026): das USB-Mikrofon vorne oben am Gehäuse
## wie echt und die Geräusche der Umgebung als Tonquellen in der Welt.
##   Mikrofon: Pegel in dBFS (wie MoveEye ihn misst, 0 = Vollaussteuerung; ungefähr Schalldruck − 100 dB).
##     - Abstand: 1/r (−6 dB pro Verdopplung), lange Quellen (Strasse, Bach, Seeufer) nur −3 dB pro Verdopplung
##     - Boden und Luft dämpfen zusätzlich (hohe, kurze Töne wie Klatschen am meisten, das Brummen der Strasse am wenigsten)
##     - Richtung: das Gehäuse schattet ab - von hinten bis −5 dB (vorne = Pan-0-Richtung wie der PIR)
##     - Hintergrund: Grundrauschen der fernen Welt + Mikrofon-Eigenrauschen, Wind am Mikrofon, Regen, die Quellen unten
##     - drinnen (Szene Schlafzimmer): alles von draussen −25 dB
##   Umgebungsgeräusche (je Familie abschaltbar, am PC hörbar wie das Mikrofon sie hört):
##     Wetter: Wind, Regen · Wasser: Bach (Wald, «Bach 10 m / 30 m»), Seeufer (Szene Seeufer), Frösche nachts am Wasser
##     Tiere: Grillen in warmen Sommernächten (Tempo nach Temperatur), Vogelchor am Morgen, tagsüber einzelne Vögel, Eule
##            nachts, ein Hund bellt in der Ferne, Kuhglocken (Bauernhof)
##     Menschen: Strasse in der Ferne (tags laut, nachts leise, Abstand je Szene), Stimmen der Nachbarn (Campingplätze)
##   An MoveEye: sound_db (wie bisher, jetzt aus diesem Modell), sound_ev mit dem Pegel am Mikrofon (Klatschen in 2 m
##   −19 dBFS = erkannt, in 15 m −43 dBFS = zu leise) und neu «mic» {db, bg, src: [{k, db, az, d}]} - MoveEye macht daraus beim
##   «Mithören» ein Geräusch in der richtigen Lautstärke (Teil 558p).
## Einstellungen: user://mikrofon.json.

var main
const T = preload("res://scripts/i18n.gd")
const FILE := "user://mikrofon.json"
const SAVE := ["real_on", "amb_on", "f_wetter", "f_wasser", "f_tiere", "f_menschen", "water", "pc_on", "pc_vol"]
var real_on := true                # Mikrofon wie echt (sonst die alte einfache Formel)
var amb_on := true                 # Umgebungsgeräusche
var f_wetter := true
var f_wasser := true
var f_tiere := true
var f_menschen := true
var water := "auto"                # auto (je nach Szene) | off | bach10 | bach30
var pc_on := true                  # am PC hören
var pc_vol := 40.0                 # %

# zusätzliche Dämpfung durch Boden und Luft: [dB pro m ab 1 m, höchstens dB]
const EX := {"clap": [0.5, 12.0], "sneeze": [0.4, 10.0], "voice": [0.35, 10.0], "shout": [0.3, 10.0], "voices": [0.35, 10.0],
		"dog": [0.15, 15.0], "birds": [0.3, 10.0], "crickets": [0.4, 12.0], "owl": [0.12, 10.0], "frogs": [0.25, 10.0],
		"cows": [0.2, 10.0], "road": [0.04, 10.0], "water": [0.1, 8.0], "speaker": [0.2, 10.0], "noise": [0.25, 10.0]}
const FAM := {"wind": "wetter", "rain": "wetter", "water": "wasser", "frogs": "wasser", "crickets": "tiere", "birds": "tiere",
		"owl": "tiere", "dog": "tiere", "cows": "tiere", "road": "menschen", "voices": "menschen"}
const NAMES := {"wind": "Wind", "rain": "Regen", "water": "Wasser", "frogs": "Frösche", "crickets": "Grillen", "birds": "Vögel",
		"owl": "Eule", "dog": "Hund (fern)", "cows": "Kuhglocken", "road": "Strasse", "voices": "Stimmen", "clap": "Klatschen",
		"sneeze": "Niesen", "voice": "Stimme", "shout": "Rufen", "speaker": "Lautsprecher", "noise": "Geräusch", "bg": "Grundrauschen"}
# Abstand zur nächsten Strasse je Szene (m; 0 = keine)
const ROAD_D := {"camping": 160.0, "wald": 450.0, "parkplatz": 35.0, "garten": 45.0, "lustig": 120.0, "wild": 600.0,
		"verstecken": 200.0, "ort": 150.0, "zuhause": 45.0, "bauernhof": 300.0, "seeufer": 250.0, "baustelle": 40.0,
		"stellplatz": 70.0, "vorlage": 150.0, "schlafzimmer": 60.0, "camping_voll": 120.0, "tarnen": 300.0, "velodieb": 25.0, "parcours": 300.0}
const VOICE_SC := {"camping": 28.0, "camping_voll": 12.0, "stellplatz": 18.0, "seeufer": 30.0, "parkplatz": 25.0, "garten": 35.0, "zuhause": 35.0, "lustig": 25.0}

var amb: Array = []                # aktive Quellen: {k, pos (Vector3 / null = am Mikrofon), db, line}
var _spots := {}                   # Szene -> feste Plätze der Quellen
var _scene := ""
var _amb_t := 0.0
var _st := {}                      # Zustand der Quellen mit Pausen (Hund, Eule, Vögel, Stimmen)
var last := {"db": -70.0, "bg": -70.0, "src": []}
var _calc_t := -1.0
var info_label: Label
var _players := {}                 # Art -> AudioStreamPlayer (am PC)
var _cache := {}
var _pending := {}
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.randomize()
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY:
			for k in SAVE:
				if d.has(k):
					set(k, d[k])
	pc_vol = clampf(float(pc_vol), 0.0, 100.0)


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


# ---- Mikrofon ----------------------------------------------------------------------------------------------------------
func mic_pos() -> Vector3:
	if main.rig == null:
		return Vector3(0, main.HEAD_H, 0)
	return main.rig.global_transform * Vector3(0, maxf(0.3, main.mast_h - 0.05), -0.1)


func forward() -> Vector3:
	if main.pir != null:
		return main.pir.forward()
	return Vector3(0, 0, -1)


func indoor() -> bool:
	return str(main.scene) == "schlafzimmer"


func at_mic(db1m: float, pos: Vector3, kind := "noise", line := false) -> Array:
	"""[Pegel am Mikrofon dBFS, Richtung ° (0 = vorne, + = rechts), Abstand m] einer Quelle mit db1m in 1 m"""
	var m := mic_pos()
	var c := pos - m
	var d := maxf(1.0, c.length())
	var ex: Array = EX.get(kind, EX["noise"])
	var lv := db1m - (10.0 if line else 20.0) * log(d) / log(10.0) - minf(float(ex[1]), float(ex[0]) * (d - 1.0))
	var az := 0.0
	var h := Vector3(c.x, 0, c.z)
	if h.length() > 0.05:
		az = rad_to_deg(forward().signed_angle_to(h, Vector3.UP))
		az = -az                                         # signed_angle_to: links +, hier rechts +
		lv -= 2.5 * (1.0 - cos(deg_to_rad(az)))          # Gehäuse-Schatten: hinten −5 dB
	if indoor() and kind in FAM:
		lv -= 25.0
	return [lv, az, d]


func level(db1m: float, pos: Vector3, kind := "noise") -> float:
	return float(at_mic(db1m, pos, kind)[0])


static func _p(db: float) -> float:
	return pow(10.0, db / 10.0)


static func _db(p: float) -> float:
	return 10.0 * log(maxf(p, 1e-12)) / log(10.0)


func compute() -> Dictionary:
	"""was das Mikrofon jetzt hört: Summe, Hintergrund, die lautesten Quellen (höchstens 10 × pro s gerechnet)"""
	var t: float = main.now()
	if absf(t - _calc_t) < 0.09:
		return last
	_calc_t = t
	var dark: bool = main.is_dark()
	var parts: Array = []                              # [k, dB, az, d]
	var floor_db := -72.0 if indoor() else (-68.0 if dark else -60.0)
	parts.append(["bg", floor_db, null, null])
	if amb_on:
		for s in amb:
			if s["pos"] == null:
				parts.append([s["k"], float(s["db"]), null, null])
			else:
				var a := at_mic(float(s["db"]), s["pos"], str(s["k"]), bool(s.get("line", false)))
				parts.append([s["k"], a[0], a[1], a[2]])
	var bg := 0.0
	for x in parts:
		bg += _p(float(x[1]))
	var tot := bg
	for snd in main.sounds:
		if t < float(snd[2]):
			var k := str(snd[3]) if snd.size() > 3 else "noise"
			var a := at_mic(float(snd[0]), snd[1], k)
			parts.append([k, a[0], a[1], a[2]])
			tot += _p(float(a[0]))
	var tdb := _db(tot)
	parts.sort_custom(func(a, b): return float(a[1]) > float(b[1]))
	var src := []
	for x in parts:
		if src.size() >= 6 or float(x[1]) < tdb - 35.0:
			break
		src.append({"k": x[0], "db": snappedf(float(x[1]), 0.1), "az": snappedf(float(x[2]), 1.0) if x[2] != null else null,
				"d": snappedf(float(x[3]), 0.1) if x[3] != null else null})
	last = {"db": snappedf(tdb, 0.1), "bg": snappedf(_db(bg), 0.1), "src": src}
	return last


func sound_db() -> float:
	return float(compute()["db"])


func reply() -> Dictionary:
	"""Feld «mic» an MoveEye (world_reply): Summe, Hintergrund, Quellen - fürs Mithören (558p)"""
	return compute()


# ---- Umgebungsgeräusche: alle 0.25 s die aktiven Quellen ------------------------------------------------------------
func _rand_spot(r0: float, r1: float, ang := TAU, a0 := 0.0) -> Vector3:
	var a := a0 + _rng.randf() * ang
	var r := _rng.randf_range(r0, r1)
	return Vector3(sin(a) * r, 0.3, -cos(a) * r)


func _make_spots() -> void:
	_scene = str(main.scene)
	var s := {}
	var c := mic_pos()
	c.y = 0.0
	s["crickets"] = []
	for i in range(6):
		s["crickets"].append(c + _rand_spot(5.0, 30.0))
	s["birds"] = []
	var trees: Array = main.tree_spots
	for i in range(8):
		if trees.size() > 0 and _rng.randf() < 0.7:
			var tp: Array = trees[_rng.randi() % trees.size()]
			var v: Vector2 = tp[0]
			s["birds"].append(Vector3(v.x, 6.0, v.y))
		else:
			s["birds"].append(c + _rand_spot(12.0, 55.0) + Vector3(0, 6.0, 0))
	s["owl"] = c + _rand_spot(35.0, 70.0) + Vector3(0, 8.0, 0)
	s["dog"] = c + _rand_spot(90.0, 220.0)
	s["cows"] = [c + _rand_spot(30.0, 60.0), c + _rand_spot(40.0, 80.0)]
	var vd: float = VOICE_SC.get(_scene, 0.0)
	s["voices"] = [c + _rand_spot(vd, vd * 1.4), c + _rand_spot(vd * 1.2, vd * 1.8)] if vd > 0.0 else []
	var rd: float = ROAD_D.get(_scene, 150.0)
	s["road"] = c + Vector3(rd * 0.6, 0.5, rd * 0.8) if rd > 0.0 else null
	_spots = s


func _water_src() -> Array:
	"""[pos, db1m] des nächsten Wassers (Bach / Seeufer) oder []"""
	var m := mic_pos()
	var w := water
	if w == "auto":
		w = {"seeufer": "lake", "wald": "bach30", "bauernhof": "bach30"}.get(str(main.scene), "off")
	match w:
		"lake":
			return [Vector3(m.x, 0.0, -25.0), -40.0 + clampf(float(main.wind) * float(main.gust()) / 6.0, 0.0, 8.0)]
		"bach10":
			return [m + forward().rotated(Vector3.UP, deg_to_rad(-70.0)) * 10.0 - Vector3(0, m.y, 0), -32.0]
		"bach30":
			return [m + forward().rotated(Vector3.UP, deg_to_rad(110.0)) * 30.0 - Vector3(0, m.y, 0), -32.0]
	return []


func _gate(k: String, t: float, p_start: float, dur: Array, pause: Array) -> float:
	"""an / aus mit zufälligen Längen: 1 = es tönt"""
	var st: Dictionary = _st.get(k, {"on": false, "until": t + _rng.randf_range(float(pause[0]), float(pause[1])), "t0": 0.0})
	if t >= float(st["until"]):
		if st["on"]:
			st["on"] = false
			st["until"] = t + _rng.randf_range(float(pause[0]), float(pause[1]))
		elif _rng.randf() < p_start:
			st["on"] = true
			st["t0"] = t
			st["until"] = t + _rng.randf_range(float(dur[0]), float(dur[1]))
		else:
			st["until"] = t + _rng.randf_range(float(pause[0]), float(pause[1])) * 0.5
	_st[k] = st
	return 1.0 if st["on"] else 0.0


func update_amb() -> void:
	var t: float = main.now()
	if _spots.is_empty() or _scene != str(main.scene):
		_make_spots()
	var out: Array = []
	var h: float = main.hour()
	var dark: bool = main.is_dark()
	var el: float = main.sun_el()
	var doy: int = main.day_of_year()
	var amb_c: float = main.ambient
	var wet: bool = main.weather in ["rain", "snow"]
	if f_wetter:
		var g: float = float(main.wind) * float(main.gust())
		out.append({"k": "wind", "pos": null, "db": -72.0 + maxf(0.0, g - 5.0) * 0.6 - (20.0 if indoor() else 0.0)})
		if main.weather == "rain":
			out.append({"k": "rain", "pos": null, "db": (-36.0 if main.storm_t > 0.0 else -42.0) - (18.0 if indoor() else 0.0)})
		elif main.weather == "snow":
			out.append({"k": "rain", "pos": null, "db": -68.0})
	if f_wasser:
		var w := _water_src()
		if not w.is_empty():
			out.append({"k": "water", "pos": w[0], "db": w[1], "line": true})
			if dark and doy > 90 and doy < 240 and amb_c > 8.0 and not wet:
				out.append({"k": "frogs", "pos": (w[0] as Vector3) + Vector3(3, 0, 0), "db": -26.0, "line": true})
	if f_tiere:
		if dark and amb_c >= 12.0 and doy > 135 and doy < 275 and not wet:
			for p in _spots["crickets"]:
				out.append({"k": "crickets", "pos": p, "db": -34.0 + clampf((amb_c - 16.0) * 0.5, -3.0, 3.0)})
		if not dark and main.weather != "rain":
			var dawn: bool = h < 10.5 and el > -8.0 and el < 18.0
			var spring: bool = doy > 60 and doy < 200
			var n := 8 if dawn else 3
			for i in range(n):
				var on := _gate("bird%d" % i, t, 0.8 if dawn else 0.25, [1.5, 3.5], [2.0, 9.0] if dawn else [8.0, 40.0])
				if on > 0.0:
					out.append({"k": "birds", "pos": _spots["birds"][i], "db": -22.0 + (2.0 if spring else -4.0)})
		if dark and not wet:
			if _gate("owl", t, 0.3, [3.5, 4.5], [40.0, 160.0]) > 0.0:
				out.append({"k": "owl", "pos": _spots["owl"], "db": -16.0})
		if _gate("dog", t, 0.25 if dark else 0.15, [3.0, 7.0], [60.0, 300.0]) > 0.0:
			var st: Dictionary = _st["dog"]
			if fmod(t - float(st["t0"]), 0.6) < 0.25:              # bellt: wau … wau …
				out.append({"k": "dog", "pos": _spots["dog"], "db": -4.0})
		if str(main.scene) == "bauernhof" and not dark:
			for p in _spots["cows"]:
				out.append({"k": "cows", "pos": p, "db": -30.0})
	if f_menschen:
		if _spots["road"] != null:
			var busy := 1.0 if h >= 6.0 and h < 21.0 else (0.5 if h >= 5.0 and h < 23.0 else 0.0)
			out.append({"k": "road", "pos": _spots["road"], "db": -44.0 + 14.0 * busy, "line": true})
		if h >= 8.0 and h < 23.0 and not wet:
			var loud := 4.0 if h >= 18.0 else 0.0
			for i in range((_spots["voices"] as Array).size()):
				if _gate("voice%d" % i, t, 0.6, [1.0, 4.0], [0.6, 3.0] if h > 9.0 else [5.0, 30.0]) > 0.0:
					out.append({"k": "voices", "pos": _spots["voices"][i], "db": -36.0 + loud})
	amb = out


func _process(delta: float) -> void:
	if main == null:
		return
	_amb_t -= delta
	if _amb_t <= 0.0:
		_amb_t = 0.1
		update_amb()
		_pc_update()
		if info_label != null and info_label.is_visible_in_tree() and Engine.get_process_frames() % 5 == 0:
			info_label.text = main.no_emoji(status_text())


# ---- am PC hören: pro Art eine erzeugte Schleife, so laut wie am Mikrofon ------------------------------------------------
const PC_KINDS := ["wind", "rain", "water", "frogs", "crickets", "birds", "owl", "dog", "cows", "road", "voices"]
const ONESHOT := ["owl", "dog"]           # start with the call (owl: once, dog: the barking loop)


func _pc_update() -> void:
	var want := {}
	if pc_on and main.sound_on and amb_on and main.sim_active:
		var lv := {}
		for s in amb:
			var a: float = float(s["db"]) if s["pos"] == null else float(at_mic(float(s["db"]), s["pos"], str(s["k"]), bool(s.get("line", false)))[0])
			lv[s["k"]] = _db(_p(a) + _p(float(lv.get(s["k"], -150.0))))
		if bool((_st.get("dog", {}) as Dictionary).get("on", false)) and f_tiere and not _spots.is_empty():
			lv["dog"] = float(at_mic(-4.0, _spots["dog"], "dog")[0])      # the loop barks by itself (the gate only starts it)
		for k in lv:
			if float(lv[k]) > -88.0:
				want[k] = float(lv[k])
	for k in PC_KINDS:
		var pl: AudioStreamPlayer = _players.get(k, null)
		if not want.has(k):
			if pl != null and pl.playing and k != "owl":
				pl.stop()
			continue
		if not _cache.has(k):
			if not _pending.has(k):
				_pending[k] = true
				WorkerThreadPool.add_task(_make_task.bind(k, 11025 if _lite() else 16000))
			continue
		if pl == null:
			pl = AudioStreamPlayer.new()
			add_child(pl)
			pl.stream = _cache[k]
			_players[k] = pl
		pl.volume_db = clampf(0.75 * (float(want[k]) + 20.0) + linear_to_db(maxf(0.001, pc_vol / 100.0)) - 2.0, -80.0, 6.0)
		if k in ONESHOT:
			var st: Dictionary = _st.get(k, {})
			if float(st.get("t0", 0.0)) != float(pl.get_meta("t0", -1.0)):
				pl.set_meta("t0", float(st.get("t0", 0.0)))
				pl.play()
		elif not pl.playing:
			pl.play(_rng.randf() * 0.5)


func _lite() -> bool:
	"""Lite graphics (Raspberry Pi): quality.gd (3D-4.52, set by main.lite_update)"""
	return preload("res://scripts/quality.gd").lite()


func _make_task(k: String, rate: int) -> void:
	var w := Gen.make(k, rate, float(main.ambient))
	call_deferred("_made", k, w)


func _made(k: String, w: AudioStreamWAV) -> void:
	_cache[k] = w
	_pending.erase(k)


func stop_all() -> void:
	for k in _players:
		(_players[k] as AudioStreamPlayer).stop()


# ---- Anzeige, Regler, Test-Aktion ----------------------------------------------------------------------------------------------
func _dir_word(az) -> String:
	if az == null:
		return T.t("rundum")
	var a := float(az)
	if absf(a) <= 30.0:
		return T.t("vorne")
	if absf(a) >= 150.0:
		return T.t("hinten")
	var side := T.t("rechts") if a > 0.0 else T.t("links")
	return side + (" " + T.t("vorne") if absf(a) < 75.0 else (" " + T.t("hinten") if absf(a) > 105.0 else ""))


func status_text() -> String:
	var r := compute()
	var s := T.t("Mikrofon am Gerät: %.0f dB · Hintergrund %.0f dB") % [float(r["db"]), float(r["bg"])]
	if not real_on:
		s += " · " + T.t("einfaches Modell")
	var top: Array = []
	for x in r["src"]:
		if str(x["k"]) == "bg":
			continue
		var tx := T.t(str(NAMES.get(str(x["k"]), x["k"]))) + " %.0f" % float(x["db"])
		if x["d"] != null:
			tx += " (%s, %.0f m)" % [_dir_word(x["az"]), float(x["d"])]
		top.append(tx)
		if top.size() >= 3:
			break
	if not top.is_empty():
		s += "\n" + T.t("Laut: %s") % ", ".join(PackedStringArray(top))
	return s


func add_controls() -> void:
	var g := "Licht & Ton"
	var M := {"sub": "Mikrofon"}
	main.add_control("toggle", "mic_real", "Mikrofon wie echt (Abstand, Richtung, Boden dämpft)", func(): return real_on, func(v): real_on = bool(v); save(), g, M)
	var U := {"sub": "Umgebungsgeräusche"}
	main.add_control("toggle", "amb_on", "Umgebungsgeräusche (Wind, Regen, Wasser, Tiere, Strasse, Stimmen)", func(): return amb_on, func(v): amb_on = bool(v); save(), g, U)
	main.add_control("toggle", "amb_pc", "Am PC hören (so laut, wie das Mikrofon es hört)", func(): return pc_on, func(v): pc_on = bool(v); save(); if not pc_on: stop_all(), g, U)
	main.add_control("slider", "amb_vol", "Lautstärke am PC", func(): return pc_vol, func(v): pc_vol = clampf(float(v), 0.0, 100.0); save(), g,
			{"sub": "Umgebungsgeräusche", "min": 0, "max": 100, "step": 5, "unit": "%"})
	var X := {"sub": "Umgebungsgeräusche", "expert": true}
	main.add_control("toggle", "amb_wetter", "Wetter: Wind am Mikrofon, Regen", func(): return f_wetter, func(v): f_wetter = bool(v); save(), g, X)
	main.add_control("toggle", "amb_wasser", "Wasser: Bach, Seeufer, Frösche", func(): return f_wasser, func(v): f_wasser = bool(v); save(), g, X)
	main.add_control("toggle", "amb_tiere", "Tiere: Grillen, Vögel, Eule, Hund in der Ferne, Kuhglocken", func(): return f_tiere, func(v): f_tiere = bool(v); save(), g, X)
	main.add_control("toggle", "amb_menschen", "Menschen: Strasse in der Ferne, Stimmen der Nachbarn", func(): return f_menschen, func(v): f_menschen = bool(v); save(), g, X)
	main.add_control("select", "amb_water", "Wasser in der Nähe", func(): return water, func(v): water = str(v); save(), g,
			{"sub": "Umgebungsgeräusche", "expert": true, "options": [["auto", "je nach Szene"], ["off", "keins"], ["bach10", "Bach 10 m links"], ["bach30", "Bach 30 m hinten"], ["lake", "Seeufer"]]})


func add_info(parent: Control, ui) -> void:
	info_label = ui.small(main.no_emoji(status_text()))
	info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(info_label)


func op(d: Dictionary) -> Dictionary:
	"""Test-Aktion «mikro»: {do: info | set (key, value) | probe (kind, db1m, x, z)}"""
	match str(d.get("do", "info")):
		"set":
			var k := str(d.get("key", ""))
			if k in SAVE:
				var v = d.get("value")
				set(k, float(v) if k == "pc_vol" else (str(v) if k == "water" else bool(v)))
				save()
		"probe":
			var kind := str(d.get("kind", "clap"))
			var db1m: float = float(d.get("db1m", main.SOUND_EV_DB.get(kind, -13.0)))
			var p := Vector3(float(d.get("x", 0.0)), 1.5, float(d.get("z", -2.0)))
			var a := at_mic(db1m, p, kind)
			return {"ok": true, "db": snappedf(float(a[0]), 0.1), "az": snappedf(float(a[1]), 1.0), "d": snappedf(float(a[2]), 0.1), "bg": compute()["bg"]}
	_calc_t = -1.0
	var r := compute().duplicate(true)
	r["ok"] = true
	r["amb"] = amb.map(func(s): return str(s["k"]))
	r["status"] = status_text()
	r["pc"] = {"on": pc_on, "vol": pc_vol, "playing": _players.keys().filter(func(k): return (_players[k] as AudioStreamPlayer).playing), "made": _cache.keys()}
	for k in SAVE:
		r[k] = get(k)
	return r


const Gen = preload("res://scripts/mikrofon_klang.gd")
