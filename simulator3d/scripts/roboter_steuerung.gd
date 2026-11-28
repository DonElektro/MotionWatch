extends RefCounted
## Roboter-Labor: Steuerung (Besitzer 23.11.2026, freigegeben 28.11.2026) - Tastatur, Controller (Godot-Joypad) und Maus.
##   · Alle Eingaben werden zu vorwärts / seitwärts / drehen (x = seitwärts + links, y = vor, z = drehen + links), sanft
##     über Rampen (keine Sprünge). Im Ring wirken links / rechts als «Ring kippen» (Kurve), wie bisher A / D.
##   · Belegung frei wählbar: Profile (Standard fest, eigene speichern / umbenennen / löschen), je Aktion eine Taste und ein
##     Controller-Knopf oder eine Achse («Taste drücken …»), Achsen umkehren, Totzone, Doppelbelegung erlaubt und angezeigt,
##     «Standard wiederherstellen». Gespeichert in user://roboter_steuerung.json (gilt für alle Varianten).
##   · Untere Leiste: Modus Gehen / Ring, Körper verschieben, Gangart, Tempo, Höhe, Spurbreite, Maus-Joystick, Kompass,
##     verbundener Controller, Knopf «Belegung …».
##   · Körper verschieben (Aufgabe B): auf der Stelle stehen, die Füsse bleiben am Boden (Bein-Rechnung leg_ik), der Körper
##     geht vor / zurück / seitwärts, höher / tiefer, dreht (gieren) und neigt sich. Grenzen: Reichweite der Beine, Servo-
##     Grenzen und Kipp-Reserve (Schwerpunkt-Lot bleibt in der Stützfläche der Füsse). Loslassen = sanft zur Mitte (Schalter).
## Eingang: roboter_labor.gd ruft input(ev) aus _input, tick(dt) / koerper_step(dt) aus _physics_process, process(dt) aus
## _process; /control {"action": "roboter", "do": "koerper", on, x, y, z, h, neigen, mitte} und {"do": "steuerung", profil}.

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const BEWEGUNG = preload("res://scripts/roboter_bewegung.gd")
const ANZEIGE = preload("res://scripts/roboter_anzeige.gd")
const SPEICHER := "user://roboter_steuerung.json"
const STANDARD := "Standard"
const RAMPE_AUF := 2.5                 # 1/s: so schnell steigt ein Fahrbefehl (0 → 1 in 0.4 s)
const RAMPE_AB := 4.0                  # 1/s: so schnell fällt er beim Loslassen
const SCHWELLE := 0.6                  # Achse als Knopf: ab diesem Ausschlag «gedrückt»
# [id, Name, Art]: «halten» wirkt stufenlos, solange gedrückt; «druck» einmal beim Drücken
const AKTIONEN := [
	["vor", "Vorwärts", "halten"], ["zurueck", "Rückwärts", "halten"],
	["links", "Seitwärts links (Ring: Kurve links)", "halten"], ["rechts", "Seitwärts rechts (Ring: Kurve rechts)", "halten"],
	["drehen_links", "Drehen links", "halten"], ["drehen_rechts", "Drehen rechts", "halten"],
	["hoeher", "Körper höher", "halten"], ["tiefer", "Körper tiefer", "halten"],
	["schneller", "Schneller (halten)", "halten"], ["langsamer", "Langsamer (halten)", "halten"],
	["stopp", "Stopp", "druck"], ["neu", "Neu aufstellen", "druck"],
	["gang_weiter", "Nächste Gangart", "druck"], ["gang_zurueck", "Vorherige Gangart", "druck"],
	["modus", "Modus Gehen / Ring", "druck"], ["ring_rollen", "Ring rollen", "druck"], ["ring_oeffnen", "Ring öffnen", "druck"],
	["koerper", "Körper verschieben ein / aus", "druck"]]
const ACHSEN := [[JOY_AXIS_LEFT_X, "Linker Stick links / rechts"], [JOY_AXIS_LEFT_Y, "Linker Stick hoch / runter"],
		[JOY_AXIS_RIGHT_X, "Rechter Stick links / rechts"], [JOY_AXIS_RIGHT_Y, "Rechter Stick hoch / runter"],
		[JOY_AXIS_TRIGGER_LEFT, "Linker Trigger (LT)"], [JOY_AXIS_TRIGGER_RIGHT, "Rechter Trigger (RT)"]]
const KNOPF_NAMEN := ["A", "B", "X", "Y", "Back", "Guide", "Start", "L3", "R3", "LB", "RB", "↑", "↓", "←", "→", "Misc",
		"P1", "P2", "P3", "P4", "Touchpad"]

var lab                                # roboter_labor.gd
var profile := {}                      # eigene Profile: Name -> {tasten, pad, umkehren, totzone}
var aktiv := STANDARD
var leiste := true                     # untere Leiste sichtbar
var zur_mitte := true                  # Körper verschieben: loslassen = sanft zurück zur Mitte
var out := Vector3.ZERO                # sanfter Fahrbefehl (x seitwärts + links, y vor, z drehen + links)
var roh := Vector3.ZERO                # ungeglättet, ohne Tempo-Faktor
var tempo_k := 1.0                     # Shift / Ctrl, Trigger
var maus := Vector2.ZERO               # Maus-Joystick: x + = rechts, y + = vor
var capture := {}                      # «Taste drücken …»: {akt, art: taste | pad}
var meldung := ""
var _meldung_t := 0.0
var _keys := {}                        # keycode -> true (gedrückt)
var _btns := {}                        # Joypad-Knopf -> true
var _axes := {}                        # Joypad-Achse -> Wert −1 … 1
var _axis_on := {}                     # Achse als «druck»-Knopf: schon ausgelöst
var _hv := 0.0                         # höher / tiefer (−1 … 1)
var _latch_back_t := -1.0              # Rückfall ohne ring_oeffnen(): Riegel später wieder erlauben
var _ui := {}
var _ui_t := 0.0
var _map: Control = null               # Fenster «Belegung»
# ---- Körper verschieben ----
var koerper := false
var k_phase := ""                      # warten (Füsse setzen sich) | aktiv | zurueck
var k_off := Vector3.ZERO              # jetzt: x vor, y hoch, z links (m, im Rahmen des Roboters beim Start)
var k_rot := Vector2.ZERO              # jetzt: x drehen (°, + links), y neigen (°, + Kopf runter)
var k_soll_off := Vector3.ZERO
var k_soll_rot := Vector2.ZERO
var k_grenze := 1.0                    # 1 = der Wunsch geht ganz, < 1 = an der Grenze (Reichweite, Servo, Kipp-Reserve)
var neigen := 0.0                      # Regler / Befehl −1 … 1
var _k_t := 0.0
var _k_x0 := []                        # Lage der Segmente beim Start
var _k_feet := []                      # [Segment][0 = links, 1 = rechts] Fusspunkt in der Welt
var _k_c0 := Vector3.ZERO
var _k_com0 := Vector3.ZERO
var _k_fw := Vector3.RIGHT
var _k_left := Vector3.FORWARD
var _k_hull := PackedVector2Array()
var _k_reserve := 0.02
var _k_cmd := {}                       # /control: fester Wunsch (x, y, z, h) statt der Eingaben


# ==== Profile ===============================================================================================================
static func standard() -> Dictionary:
	return {"tasten": {"vor": KEY_W, "zurueck": KEY_S, "links": KEY_A, "rechts": KEY_D, "drehen_links": KEY_Q,
			"drehen_rechts": KEY_E, "hoeher": KEY_PAGEUP, "tiefer": KEY_PAGEDOWN, "schneller": KEY_SHIFT, "langsamer": KEY_CTRL,
			"stopp": KEY_SPACE, "neu": KEY_R, "gang_weiter": KEY_N, "modus": KEY_M, "koerper": KEY_V},
		"pad": {"vor": _ax(JOY_AXIS_LEFT_Y, -1), "zurueck": _ax(JOY_AXIS_LEFT_Y, 1), "links": _ax(JOY_AXIS_LEFT_X, -1),
			"rechts": _ax(JOY_AXIS_LEFT_X, 1), "drehen_links": _ax(JOY_AXIS_RIGHT_X, -1), "drehen_rechts": _ax(JOY_AXIS_RIGHT_X, 1),
			"hoeher": _ax(JOY_AXIS_RIGHT_Y, -1), "tiefer": _ax(JOY_AXIS_RIGHT_Y, 1), "schneller": _ax(JOY_AXIS_TRIGGER_RIGHT, 1),
			"langsamer": _ax(JOY_AXIS_TRIGGER_LEFT, 1), "stopp": _bt(JOY_BUTTON_A), "neu": _bt(JOY_BUTTON_Y),
			"gang_weiter": _bt(JOY_BUTTON_RIGHT_SHOULDER), "gang_zurueck": _bt(JOY_BUTTON_LEFT_SHOULDER), "modus": _bt(JOY_BUTTON_START),
			"ring_rollen": _bt(JOY_BUTTON_B), "ring_oeffnen": _bt(JOY_BUTTON_X), "koerper": _bt(JOY_BUTTON_BACK)},
		"umkehren": [], "totzone": 0.15}


static func _ax(i: int, d: int) -> Dictionary:
	return {"t": "achse", "i": i, "d": d}


static func _bt(i: int) -> Dictionary:
	return {"t": "knopf", "i": i}


func prof() -> Dictionary:
	"""the active profile (Standard comes from the code and never changes)"""
	return profile[aktiv] if profile.has(aktiv) else standard()


func namen() -> Array:
	var n := [STANDARD]
	var own := profile.keys()
	own.sort()
	n.append_array(own)
	return n


func waehle(name: String) -> void:
	aktiv = name if profile.has(name) else STANDARD
	capture = {}
	speichern()
	_map_fill()


func neues_profil(name := "") -> String:
	"""a copy of the active profile under a new (unique) name; it becomes the active one"""
	var base := name.strip_edges() if name.strip_edges() != "" else T.t("Eigenes Profil")
	var nm := base
	var k := 2
	while nm == STANDARD or profile.has(nm):
		nm = "%s %d" % [base, k]
		k += 1
	profile[nm] = _sauber(prof().duplicate(true))
	aktiv = nm
	speichern()
	_map_fill()
	return nm


func umbenennen(neu: String) -> bool:
	neu = neu.strip_edges()
	if aktiv == STANDARD or neu == "" or neu == STANDARD or profile.has(neu):
		return false
	profile[neu] = profile[aktiv]
	profile.erase(aktiv)
	aktiv = neu
	speichern()
	_map_fill()
	return true


func loeschen() -> bool:
	if aktiv == STANDARD or not profile.has(aktiv):
		return false
	profile.erase(aktiv)
	aktiv = STANDARD
	speichern()
	_map_fill()
	return true


func standard_wiederherstellen() -> void:
	"""the active own profile gets the standard values again (Standard itself stays as it is)"""
	if profile.has(aktiv):
		profile[aktiv] = standard()
		speichern()
	capture = {}
	_map_fill()


func _eigen() -> Dictionary:
	"""the profile to change: Standard stays fixed, so a change there makes an own copy first"""
	if aktiv == STANDARD:
		var nm := neues_profil()
		_melde(T.t("Neues Profil «%s» angelegt – Standard bleibt, wie er ist") % nm)
	return profile[aktiv]


func belege(akt: String, art: String, wert) -> void:
	"""art «taste»: keycode (0 = leer); art «pad»: {t: knopf | achse, i, d} ({} = leer)"""
	var p := _eigen()
	if art == "taste":
		if int(wert) == 0:
			(p["tasten"] as Dictionary).erase(akt)
		else:
			p["tasten"][akt] = int(wert)
	else:
		if typeof(wert) != TYPE_DICTIONARY or (wert as Dictionary).is_empty():
			(p["pad"] as Dictionary).erase(akt)
		else:
			p["pad"][akt] = wert
	speichern()
	_map_fill()


func umkehren(achse: int, on: bool) -> void:
	var p := _eigen()
	var u: Array = p["umkehren"]
	if on and not u.has(achse):
		u.append(achse)
	elif not on:
		u.erase(achse)
	speichern()
	_map_fill()


func set_totzone(z: float) -> void:
	var p := _eigen()
	p["totzone"] = clampf(z, 0.0, 0.9)
	speichern()


static func _sauber(p: Dictionary) -> Dictionary:
	"""after JSON (numbers come back as float): the right types; missing parts from the standard"""
	var s := standard()
	var out_ := {"tasten": {}, "pad": {}, "umkehren": [], "totzone": float(p.get("totzone", s["totzone"]))}
	var ta = p.get("tasten", s["tasten"])
	if typeof(ta) == TYPE_DICTIONARY:
		for k in ta:
			if int(ta[k]) != 0:
				out_["tasten"][str(k)] = int(ta[k])
	var pa = p.get("pad", s["pad"])
	if typeof(pa) == TYPE_DICTIONARY:
		for k in pa:
			var b = pa[k]
			if typeof(b) == TYPE_DICTIONARY and str(b.get("t", "")) in ["knopf", "achse"]:
				var e := {"t": str(b["t"]), "i": int(b.get("i", 0))}
				if e["t"] == "achse":
					e["d"] = 1 if float(b.get("d", 1)) >= 0.0 else -1
				out_["pad"][str(k)] = e
	var um = p.get("umkehren", [])
	if typeof(um) == TYPE_ARRAY:
		for a in um:
			out_["umkehren"].append(int(a))
	return out_


func laden() -> void:
	profile = {}
	aktiv = STANDARD
	if not FileAccess.file_exists(SPEICHER):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(SPEICHER))
	if typeof(d) != TYPE_DICTIONARY:
		return
	var pr = d.get("profile", {})
	if typeof(pr) == TYPE_DICTIONARY:
		for k in pr:
			if str(k) != STANDARD and typeof(pr[k]) == TYPE_DICTIONARY:
				profile[str(k)] = _sauber(pr[k])
	aktiv = str(d.get("aktiv", STANDARD)) if profile.has(str(d.get("aktiv", ""))) else STANDARD
	leiste = bool(d.get("leiste", true))
	zur_mitte = bool(d.get("zur_mitte", true))


func speichern() -> void:
	var f := FileAccess.open(SPEICHER, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"aktiv": aktiv, "profile": profile, "leiste": leiste, "zur_mitte": zur_mitte}, " "))


static func bind_key(b: Dictionary) -> String:
	return "k%d" % int(b["i"]) if b.get("t", "") == "taste" else ("b%d" % int(b["i"]) if b.get("t", "") == "knopf"
			else "a%d%s" % [int(b["i"]), "+" if int(b.get("d", 1)) > 0 else "-"])


func doppelt() -> Dictionary:
	"""action -> [other actions with the same key / button / axis direction] (allowed, but shown)"""
	var by := {}
	var p := prof()
	for a in AKTIONEN:
		var bs := []
		if (p["tasten"] as Dictionary).has(a[0]):
			bs.append({"t": "taste", "i": p["tasten"][a[0]]})
		if (p["pad"] as Dictionary).has(a[0]):
			bs.append(p["pad"][a[0]])
		for b in bs:
			var k := bind_key(b)
			if not by.has(k):
				by[k] = []
			if not (by[k] as Array).has(a[0]):
				by[k].append(a[0])
	var out_ := {}
	for k in by:
		if (by[k] as Array).size() > 1:
			for a in by[k]:
				if not out_.has(a):
					out_[a] = []
				for o in by[k]:
					if o != a and not (out_[a] as Array).has(o):
						out_[a].append(o)
	return out_


static func akt_name(id: String) -> String:
	for a in AKTIONEN:
		if a[0] == id:
			return T.t(a[1])
	return id


static func taste_text(code: int) -> String:
	return OS.get_keycode_string(code) if code != 0 else "–"


static func pad_text(b: Dictionary) -> String:
	if b.is_empty():
		return "–"
	if b["t"] == "knopf":
		var i := int(b["i"])
		return KNOPF_NAMEN[i] if i >= 0 and i < KNOPF_NAMEN.size() else T.t("Knopf %d") % i
	var i := int(b["i"])
	var d := int(b.get("d", 1))
	match i:
		JOY_AXIS_LEFT_X:
			return T.t("Linker Stick") + (" →" if d > 0 else " ←")
		JOY_AXIS_LEFT_Y:
			return T.t("Linker Stick") + (" ↓" if d > 0 else " ↑")
		JOY_AXIS_RIGHT_X:
			return T.t("Rechter Stick") + (" →" if d > 0 else " ←")
		JOY_AXIS_RIGHT_Y:
			return T.t("Rechter Stick") + (" ↓" if d > 0 else " ↑")
		JOY_AXIS_TRIGGER_LEFT:
			return "LT"
		JOY_AXIS_TRIGGER_RIGHT:
			return "RT"
	return T.t("Achse %d") % i + (" +" if d > 0 else " −")


# ==== Eingaben ==============================================================================================================
func achse(i: int) -> float:
	"""a joypad axis with the profile's direction and dead zone (−1 … 1)"""
	var p := prof()
	var v := float(_axes.get(i, 0.0))
	if (p["umkehren"] as Array).has(i):
		v = -v
	var dz := float(p["totzone"])
	var a := absf(v)
	if a <= dz:
		return 0.0
	return signf(v) * minf(1.0, (a - dz) / maxf(1e-3, 1.0 - dz))


func wert(akt: String) -> float:
	"""how strongly an action is held now (0 … 1): key / button = 1, axis = its travel past the dead zone"""
	var p := prof()
	var v := 0.0
	var k := int((p["tasten"] as Dictionary).get(akt, 0))
	if k != 0 and _keys.has(k):
		v = 1.0
	var b: Dictionary = (p["pad"] as Dictionary).get(akt, {})
	if not b.is_empty():
		if b["t"] == "knopf":
			if _btns.has(int(b["i"])):
				v = 1.0
		else:
			v = maxf(v, maxf(0.0, achse(int(b["i"])) * float(b.get("d", 1))))
	return v


func input(ev: InputEvent) -> bool:
	"""from roboter_labor._input: true = used here (the lab does nothing more with it)"""
	if not capture.is_empty():
		return _capture_input(ev)
	if map_open() and ev is InputEventKey and (ev as InputEventKey).pressed and (ev as InputEventKey).keycode == KEY_ESCAPE:
		close_map()
		return true
	if ev is InputEventKey:
		var k := ev as InputEventKey
		var code := int(k.keycode) if k.keycode != KEY_NONE else int(k.physical_keycode)
		if k.pressed:
			_keys[code] = true
		else:
			_keys.erase(code)
		if not k.pressed or k.echo:
			return _haelt_taste(code)
		for a in AKTIONEN:
			if a[2] == "druck" and int((prof()["tasten"] as Dictionary).get(a[0], 0)) == code:
				aktion(a[0])
				return true
		return _haelt_taste(code)
	if ev is InputEventJoypadButton:
		var jb := ev as InputEventJoypadButton
		if jb.pressed:
			_btns[int(jb.button_index)] = true
			for a in AKTIONEN:
				var b: Dictionary = (prof()["pad"] as Dictionary).get(a[0], {})
				if a[2] == "druck" and b.get("t", "") == "knopf" and int(b["i"]) == int(jb.button_index):
					aktion(a[0])
		else:
			_btns.erase(int(jb.button_index))
		return true
	if ev is InputEventJoypadMotion:
		var jm := ev as InputEventJoypadMotion
		_axes[int(jm.axis)] = clampf(jm.axis_value, -1.0, 1.0)
		for a in AKTIONEN:
			var b: Dictionary = (prof()["pad"] as Dictionary).get(a[0], {})
			if a[2] != "druck" or b.get("t", "") != "achse" or int(b["i"]) != int(jm.axis):
				continue
			var on := achse(int(jm.axis)) * float(b.get("d", 1)) > SCHWELLE
			if on and not _axis_on.get(a[0], false):
				aktion(a[0])
			_axis_on[a[0]] = on
		return true
	return false


func _haelt_taste(code: int) -> bool:
	"""a key of a «halten» action: used here (so the lab's own keys never fire twice)"""
	for a in AKTIONEN:
		if a[2] == "halten" and int((prof()["tasten"] as Dictionary).get(a[0], 0)) == code:
			return true
	return false


func loslassen() -> void:
	"""window lost the focus: nothing stays held"""
	_keys = {}
	_btns = {}
	_axes = {}
	_axis_on = {}
	maus = Vector2.ZERO


func start_capture(akt: String, art: String) -> void:
	capture = {"akt": akt, "art": art}
	_map_fill()


func _capture_input(ev: InputEvent) -> bool:
	var art: String = capture["art"]
	var akt: String = capture["akt"]
	if ev is InputEventKey and (ev as InputEventKey).pressed and not (ev as InputEventKey).echo:
		var k := ev as InputEventKey
		var code := int(k.keycode) if k.keycode != KEY_NONE else int(k.physical_keycode)
		if code == KEY_ESCAPE:
			capture = {}
		elif code == KEY_DELETE or code == KEY_BACKSPACE:
			capture = {}
			belege(akt, art, 0 if art == "taste" else {})
		elif art == "taste":
			capture = {}
			belege(akt, "taste", code)
		_map_fill()
		return true
	if art == "pad" and ev is InputEventJoypadButton and (ev as InputEventJoypadButton).pressed:
		capture = {}
		belege(akt, "pad", _bt(int((ev as InputEventJoypadButton).button_index)))
		return true
	if art == "pad" and ev is InputEventJoypadMotion:
		var jm := ev as InputEventJoypadMotion
		_axes[int(jm.axis)] = jm.axis_value
		if absf(jm.axis_value) > SCHWELLE:
			var d := 1 if jm.axis_value > 0.0 else -1
			if (prof()["umkehren"] as Array).has(int(jm.axis)):
				d = -d                                   # the direction as the profile reads it
			capture = {}
			belege(akt, "pad", _ax(int(jm.axis), d))
		return true
	return ev is InputEventKey or ev is InputEventJoypadButton or ev is InputEventJoypadMotion


func _melde(t: String) -> void:
	meldung = t
	_meldung_t = 4.0


# ==== jeden Physik-Schritt ===================================================================================================
func tick(dt: float) -> Vector3:
	"""the smooth drive command for the lab (zero while «Körper verschieben» is on: then the inputs move the body)"""
	if DisplayServer.get_name() != "headless":
		for code in _keys.keys():                       # a release lost (focus): never stuck
			if not Input.is_key_pressed(code) and not Input.is_physical_key_pressed(code):
				_keys.erase(code)
	var r := Vector3(wert("links") - wert("rechts") - maus.x, wert("vor") - wert("zurueck") + maus.y,
			wert("drehen_links") - wert("drehen_rechts"))
	if not _k_cmd.is_empty():
		r = Vector3(float(_k_cmd.get("x", 0.0)), float(_k_cmd.get("y", 0.0)), float(_k_cmd.get("z", 0.0)))
	r = r.clamp(-Vector3.ONE, Vector3.ONE)
	roh = r
	tempo_k = clampf(1.0 + 0.6 * wert("schneller") - 0.6 * wert("langsamer"), 0.4, 1.6)
	var ziel := r if koerper else r * tempo_k
	var rate := RAMPE_AUF if ziel.length() > out.length() + 1e-4 else RAMPE_AB
	out = out.move_toward(ziel, dt * rate)
	_hv = clampf(wert("hoeher") - wert("tiefer"), -1.0, 1.0) if _k_cmd.is_empty() else float(_k_cmd.get("h", 0.0))
	if not koerper and absf(_hv) > 0.01:
		_hoehe(dt, _hv)
	if _latch_back_t > 0.0:
		_latch_back_t -= dt
		if _latch_back_t <= 0.0 and lab.model != null:
			lab.model.latch_wanted = true
	return Vector3.ZERO if koerper else out


func _hoehe(dt: float, hv: float) -> void:
	var bew = lab.bew
	if ist_ring():
		bew.ring_hoehe = clampf(bew.ring_hoehe + hv * 0.05 * dt, 0.0, bew.ring_height_max())
	else:
		bew.hoehe = clampf(bew.hoehe + hv * 0.5 * dt, 0.3, 1.8)
		if bew.mode == "" and lab.last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			bew.apply(bew.pose(lab.last_pose))
	lab.mark_dirty()


func ist_ring() -> bool:
	return lab.model != null and (lab.model.latch["state"] == "locked" or lab.bew.mode == "ring")


func aktion(akt: String) -> void:
	if lab == null or lab.model == null:
		return
	match akt:
		"stopp":
			out = Vector3.ZERO
			maus = Vector2.ZERO
			if koerper:
				koerper_aus()
			else:
				lab.stop_all()
		"neu":
			out = Vector3.ZERO
			_k_ende()
			lab.reset()
		"gang_weiter":
			gang_wechseln(1)
		"gang_zurueck":
			gang_wechseln(-1)
		"modus":
			set_modus("gehen" if ist_ring() else "ring")
		"ring_rollen":
			set_modus("ring")
		"ring_oeffnen":
			ring_oeffnen()
		"koerper":
			if koerper:
				koerper_aus()
			else:
				koerper_an()
	refresh()


func gang_wechseln(dirn: int) -> void:
	var bew = lab.bew
	var ids: Array = BEWEGUNG.GAENGE.map(func(x): return x[0])
	var i := ids.find(bew.gang)
	var g: String = ids[posmod(i + dirn, ids.size())]
	set_gang(g)


func set_gang(g: String) -> void:
	var bew = lab.bew
	bew.gang = g
	if bew.mode == "gang":
		bew.start_gang(g)
	_melde(T.t("Gangart: %s") % T.t(str(BEWEGUNG.GAENGE.filter(func(x): return x[0] == g)[0][1])))
	lab._paint_gang()
	refresh()


func set_modus(m: String) -> void:
	var bew = lab.bew
	var model = lab.model
	if m == "ring":
		_k_ende()
		model.latch_wanted = true
		_latch_back_t = -1.0
		if model.latch["state"] != "locked":
			lab.apply_pose("ring", true)
		bew.start_ring()
	elif ist_ring():
		ring_oeffnen()
	lab._paint_gang()
	refresh()


func ring_oeffnen() -> void:
	"""Knopf «Ring öffnen»: the lab's own function if it has one (branch sim-ring-oeffnen), otherwise latch open + Gerade"""
	_k_ende()
	if lab.has_method("ring_oeffnen"):
		lab.call("ring_oeffnen", "gerade")
		return
	var model = lab.model
	if model.latch["state"] == "open" and lab.bew.mode != "ring":
		return
	lab.bew.stop()
	model.latch_wanted = false
	model.unlock()
	lab.apply_pose("gerade")
	_latch_back_t = 4.0                                    # the ends are apart by then: the latch may close again later


# ==== Körper verschieben =====================================================================================================
func koerper_an() -> bool:
	if lab.model == null or not lab.model.built_ok:
		return false
	if lab.model.latch["state"] == "locked" or lab.bew.mode == "ring":
		_melde(T.t("Körper verschieben geht nur auf den Beinen – zuerst den Ring öffnen"))
		return false
	lab.stop_all()
	koerper = true
	k_phase = "warten"
	_k_t = 0.0
	k_off = Vector3.ZERO
	k_rot = Vector2.ZERO
	k_soll_off = Vector3.ZERO
	k_soll_rot = Vector2.ZERO
	k_grenze = 1.0
	neigen = 0.0
	out = Vector3.ZERO
	_melde(T.t("Körper verschieben: die Fahr-Eingaben verschieben jetzt den Körper, die Füsse bleiben stehen"))
	refresh()
	return true


func koerper_aus() -> void:
	"""sanft zurück zur Mitte, dann aus"""
	if not koerper:
		return
	if k_phase == "warten":
		_k_ende()
		return
	k_phase = "zurueck"
	_k_cmd = {}
	refresh()


func _k_ende() -> void:
	koerper = false
	k_phase = ""
	_k_cmd = {}
	k_off = Vector3.ZERO
	k_rot = Vector2.ZERO


func k_max() -> Dictionary:
	"""the largest wish per full input (the limits below may make it smaller)"""
	var reach: float = lab.model.u("oberschenkel") + lab.model.u("unterschenkel")
	return {"vor": 0.45 * reach, "seit": 0.45 * reach, "hoch": 0.35 * reach, "drehen": 20.0, "neigen": 12.0}


func _k_capture() -> void:
	var m = lab.model
	var N: int = m.n()
	_k_x0 = []
	_k_feet = []
	_k_c0 = Vector3.ZERO
	var pts := PackedVector2Array()
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		_k_x0.append(xf)
		_k_c0 += xf.origin
		var fl: Vector3 = m.foot_world(i, -1)
		var fr: Vector3 = m.foot_world(i, 1)
		_k_feet.append([fl, fr])
		pts.append(Vector2(fl.x, fl.z))
		pts.append(Vector2(fr.x, fr.z))
	_k_c0 /= N
	_k_com0 = m.com()
	var hd: Vector3 = m.segment_xf(0).origin - m.segment_xf(N - 1).origin
	hd.y = 0.0
	if hd.length() < 0.01:
		hd = m.segment_xf(0).basis.x
		hd.y = 0.0
	_k_fw = hd.normalized() if hd.length() > 0.01 else Vector3.RIGHT
	_k_left = Vector3(_k_fw.z, 0.0, -_k_fw.x)
	_k_hull = ANZEIGE.hull(pts)
	var m0 := ANZEIGE.signed_margin(Vector2(_k_com0.x, _k_com0.z), _k_hull)
	_k_reserve = clampf(m0 * 0.6, 0.0, 0.03)
	k_phase = "aktiv"


func k_xf(off: Vector3, rot: Vector2) -> Transform3D:
	"""where the whole body goes: turned about its centre (drehen, neigen), then shifted (vor, hoch, links)"""
	var right := -_k_left
	var r := Basis(Vector3.UP, deg_to_rad(rot.x)) * Basis(right, deg_to_rad(-rot.y))
	var tw := _k_fw * off.x + Vector3.UP * off.y + _k_left * off.z
	return Transform3D(r, _k_c0 + tw - r * _k_c0)


func k_ziele(off: Vector3, rot: Vector2) -> Dictionary:
	"""servo targets of all legs for this body pose with the feet where they stood; {} = not possible"""
	var m = lab.model
	var bew = lab.bew
	var w: float = m.u("halbe_breite")
	var l1: float = m.u("oberschenkel")
	var l2: float = m.u("unterschenkel")
	var tf := k_xf(off, rot)
	var d := {}
	for i in range(_k_x0.size()):
		var inv: Transform3D = (tf * (_k_x0[i] as Transform3D)).affine_inverse()
		for si in range(2):
			var s := -1 if si == 0 else 1
			var fs: Vector3 = inv * (_k_feet[i][si] as Vector3)
			var r := (fs - Vector3(0, 0, s * w)).length()
			if r > (l1 + l2) * 0.93 or r < absf(l1 - l2) + 0.01:
				return {}
			var a: Array = bew.leg_ik(s, fs)
			var sd := "l" if s < 0 else "r"
			var ids := ["hy%d%s" % [i, sd], "hp%d%s" % [i, sd], "kn%d%s" % [i, sd]]
			for j in range(3):
				var sv: Dictionary = m.servos[m.servo_index(ids[j])]
				if float(a[j]) < float(sv["min"]) + 2.0 or float(a[j]) > float(sv["max"]) - 2.0:
					return {}
				d[ids[j]] = a[j]
	var c := tf * _k_com0
	if ANZEIGE.signed_margin(Vector2(c.x, c.z), _k_hull) < _k_reserve:
		return {}
	return d


func k_moeglich(off: Vector3, rot: Vector2) -> float:
	"""the largest share (0 … 1) of this wish that keeps every leg in reach, every servo in its range and the robot stable"""
	if not k_ziele(off, rot).is_empty():
		return 1.0
	var lo := 0.0
	var hi := 1.0
	for _k in range(8):
		var mid := (lo + hi) * 0.5
		if k_ziele(off * mid, rot * mid).is_empty():
			hi = mid
		else:
			lo = mid
	return lo


func koerper_step(dt: float) -> void:
	if not koerper:
		return
	if k_phase == "warten":
		_k_t += dt
		if _k_t > 0.6:                                     # the feet stand (stop_all put the legs into the standing pose)
			_k_capture()
		return
	var mx := k_max()
	var inp := Vector3(out.y, _hv, out.x)                 # vor, hoch, links
	var irot := Vector2(out.z, neigen)
	if not _k_cmd.is_empty() and _k_cmd.has("neigen"):
		irot.y = float(_k_cmd["neigen"])
	if k_phase == "zurueck":
		k_soll_off = Vector3.ZERO
		k_soll_rot = Vector2.ZERO
	elif zur_mitte:
		k_soll_off = Vector3(inp.x * mx["vor"], inp.y * mx["hoch"], inp.z * mx["seit"])
		k_soll_rot = Vector2(irot.x * mx["drehen"], irot.y * mx["neigen"])
	else:                                                  # without «zur Mitte»: the inputs move the body, it stays there
		k_soll_off += Vector3(inp.x * mx["vor"], inp.y * mx["hoch"], inp.z * mx["seit"]) * dt * 0.8
		k_soll_rot += Vector2(irot.x * mx["drehen"], irot.y * mx["neigen"]) * dt * 0.8
		k_soll_off = k_soll_off.clamp(-Vector3(mx["vor"], mx["hoch"], mx["seit"]), Vector3(mx["vor"], mx["hoch"], mx["seit"]))
		k_soll_rot = k_soll_rot.clamp(-Vector2(mx["drehen"], mx["neigen"]), Vector2(mx["drehen"], mx["neigen"]))
	k_grenze = k_moeglich(k_soll_off, k_soll_rot)
	if k_grenze < 1.0:
		k_soll_off *= k_grenze
		k_soll_rot *= k_grenze
	var rate: float = float(mx["vor"]) * 1.2 * dt
	k_off = k_off.move_toward(k_soll_off, rate)
	k_rot = k_rot.move_toward(k_soll_rot, 25.0 * dt)
	var d := k_ziele(k_off, k_rot)
	if d.is_empty():                                       # (between two possible poses) go back a little
		k_off *= 0.97
		k_rot *= 0.97
		d = k_ziele(k_off, k_rot)
	if not d.is_empty():
		lab.bew.apply(d)
	if k_phase == "zurueck" and k_off.length() < 0.002 and k_rot.length() < 0.3:
		_k_ende()
		refresh()


func koerper_info() -> Dictionary:
	return {"on": koerper, "phase": k_phase, "off": [k_off.x, k_off.y, k_off.z], "rot": [k_rot.x, k_rot.y], "grenze": k_grenze,
			"zur_mitte": zur_mitte, "reserve": _k_reserve,
			"feet": _k_feet.map(func(f): return [[f[0].x, f[0].y, f[0].z], [f[1].x, f[1].y, f[1].z]])}


func info() -> Dictionary:
	var pads := []
	for id in Input.get_connected_joypads():
		pads.append(Input.get_joy_name(id))
	return {"profil": aktiv, "profile": namen(), "cmd": [out.x, out.y, out.z], "tempo_k": tempo_k, "controller": pads,
			"doppelt": doppelt(), "leiste": leiste, "koerper": koerper_info()}


func control(d: Dictionary) -> void:
	"""/control «roboter»: do «koerper» {on, x, y, z, h, neigen, mitte} · do «steuerung» {profil, leiste}"""
	if str(d.get("do", "")) == "koerper":
		if d.has("mitte"):
			zur_mitte = bool(d["mitte"])
		if d.has("on"):
			if bool(d["on"]) and not koerper:
				koerper_an()
			elif not bool(d["on"]):
				koerper_aus()
		var c := {}
		for k in ["x", "y", "z", "h", "neigen"]:
			if d.has(k):
				c[k] = float(d[k])
		if not c.is_empty():
			_k_cmd = c
		elif d.has("los"):
			_k_cmd = {}
	else:
		if d.has("profil"):
			waehle(str(d["profil"]))
		if d.has("leiste"):
			set_leiste(bool(d["leiste"]))


# ==== Untere Leiste ==========================================================================================================
func build(area: Control) -> void:
	var bar := PanelContainer.new()
	bar.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.92), UI.LINE, 10, 6, 1))
	bar.anchor_left = 0.0
	bar.anchor_right = 1.0
	bar.anchor_top = 1.0
	bar.anchor_bottom = 1.0
	bar.offset_left = 10
	bar.offset_right = -10
	bar.offset_top = -8
	bar.offset_bottom = -8
	bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	bar.mouse_filter = Control.MOUSE_FILTER_STOP
	area.add_child(bar)
	_ui["bar"] = bar
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 10)
	fl.add_theme_constant_override("v_separation", 6)
	bar.add_child(fl)
	# Modus
	var mo := _gruppe(fl, T.t("Modus"))
	var mh := HBoxContainer.new()
	mh.add_theme_constant_override("separation", 4)
	mo.add_child(mh)
	_ui["m_gehen"] = _knopf(mh, T.t("Gehen"), func(): set_modus("gehen"), T.t("Auf den Beinen gehen (öffnet den Ring)"))
	_ui["m_ring"] = _knopf(mh, T.t("Ring"), func(): set_modus("ring"), T.t("Im Ring rollen – links / rechts kippt den Ring (Kurve)"))
	_ui["m_koerper"] = _knopf(mh, T.t("Körper verschieben"), func(): aktion("koerper"),
			T.t("Auf der Stelle stehen, die Fahr-Eingaben verschieben den Körper (V / Back)"))
	# Gangart
	var ga := _gruppe(fl, T.t("Gangart"))
	var ob := OptionButton.new()
	ob.focus_mode = Control.FOCUS_NONE
	for g in BEWEGUNG.GAENGE:
		ob.add_item(T.t(g[1]))
	ob.item_selected.connect(func(i: int): set_gang(BEWEGUNG.GAENGE[i][0]))
	ob.tooltip_text = T.t("Gangart wechseln (N, Schultertasten LB / RB)")
	ga.add_child(ob)
	_ui["gang"] = ob
	# Tempo, Höhe, Spurbreite (Neigen nur beim Körper verschieben)
	_ui["s_tempo"] = _regler(fl, T.t("Tempo"), 0.01, 0.25, 0.01, func(x: float):
		lab.bew.tempo = x
		lab.mark_dirty())
	_ui["s_hoehe"] = _regler(fl, T.t("Höhe"), 0.0, 1.0, 0.01, func(x: float): _set_hoehe_anteil(x))
	_ui["s_spur"] = _regler(fl, T.t("Spurbreite"), 0.0, 1.0, 0.01, func(x: float): _set_spur_anteil(x))
	_ui["s_neigen"] = _regler(fl, T.t("Neigen"), -1.0, 1.0, 0.05, func(x: float): neigen = x)
	var zm := CheckButton.new()
	zm.text = T.t("Loslassen = zur Mitte")
	zm.focus_mode = Control.FOCUS_NONE
	zm.button_pressed = zur_mitte
	zm.add_theme_font_size_override("font_size", 12)
	zm.toggled.connect(func(on: bool):
		zur_mitte = on
		speichern())
	fl.add_child(zm)
	_ui["zur_mitte"] = zm
	# Maus-Joystick und Kompass
	var js := Control.new()
	js.custom_minimum_size = Vector2(64, 64)
	js.mouse_filter = Control.MOUSE_FILTER_STOP
	js.tooltip_text = T.t("Maus-Joystick: ziehen = fahren (hoch = vorwärts, zur Seite = seitwärts)")
	js.draw.connect(func(): _draw_joystick(js))
	js.gui_input.connect(func(ev: InputEvent): _joystick_input(js, ev))
	fl.add_child(js)
	_ui["joy"] = js
	var ko := Control.new()
	ko.custom_minimum_size = Vector2(56, 64)
	ko.mouse_filter = Control.MOUSE_FILTER_PASS
	ko.tooltip_text = T.t("Kompass: Blickrichtung des Roboters (N = −Z der Welt)")
	ko.draw.connect(func(): _draw_kompass(ko))
	fl.add_child(ko)
	_ui["kompass"] = ko
	# Controller und Belegung
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", 2)
	cv.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	fl.add_child(cv)
	var cl := UI.small("", UI.TXT)
	cl.custom_minimum_size = Vector2(150, 0)
	cl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cv.add_child(cl)
	_ui["pad"] = cl
	var bh := HBoxContainer.new()
	bh.add_theme_constant_override("separation", 4)
	cv.add_child(bh)
	_ui["belegung"] = _knopf(bh, T.t("Belegung …"), func(): open_map(), T.t("Tasten und Controller frei belegen, Profile"))
	var ml := UI.small("", UI.ORG)
	ml.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ml.custom_minimum_size = Vector2(150, 0)
	cv.add_child(ml)
	_ui["meldung"] = ml
	# chip «Steuerung» in the bar of the lab (views / camera / info): the drive bar on / off
	var vb: Control = lab._w.get("viewbar")
	if vb != null:
		var chip := Button.new()
		chip.text = T.t("Steuerung")
		chip.tooltip_text = T.t("Untere Leiste mit Steuerung ein / aus")
		chip.focus_mode = Control.FOCUS_NONE
		chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		chip.pressed.connect(func(): set_leiste(not leiste))
		vb.add_child(chip)
		var hint: Control = lab._w.get("hint")
		if hint != null:
			vb.move_child(chip, hint.get_index())
		_ui["chip"] = chip
	if not Input.joy_connection_changed.is_connected(_joy_changed):
		Input.joy_connection_changed.connect(_joy_changed)
	bar.visible = leiste
	refresh()


func close() -> void:
	if Input.joy_connection_changed.is_connected(_joy_changed):
		Input.joy_connection_changed.disconnect(_joy_changed)
	speichern()
	_ui = {}
	_map = null
	capture = {}
	_k_ende()
	loslassen()
	out = Vector3.ZERO


func _joy_changed(_id: int, _connected: bool) -> void:
	_axes = {}
	_btns = {}
	refresh()
	_map_fill()


func set_leiste(on: bool) -> void:
	leiste = on
	var b: Control = _ui.get("bar")
	if b != null:
		b.visible = on
	speichern()
	refresh()


func lift() -> float:
	"""how far the lab's own bar (views) and the camera picture move up over the drive bar"""
	var b: Control = _ui.get("bar")
	return b.size.y + 6.0 if b != null and b.visible else 0.0


func _gruppe(parent: Control, title: String) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	parent.add_child(v)
	v.add_child(UI.small(title))
	return v


func _knopf(parent: Control, title: String, cb: Callable, tip := "") -> Button:
	var b := Button.new()
	b.text = title
	b.tooltip_text = tip
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func _regler(parent: Control, title: String, lo: float, hi: float, stp: float, cb: Callable) -> Dictionary:
	var v := _gruppe(parent, title)
	var l: Label = v.get_child(0)
	var sl := HSlider.new()
	sl.min_value = lo
	sl.max_value = hi
	sl.step = stp
	sl.custom_minimum_size = Vector2(110, 0)
	sl.focus_mode = Control.FOCUS_NONE
	sl.value_changed.connect(cb)
	v.add_child(sl)
	return {"box": v, "sl": sl, "title": l, "name": title}


func _spur_bereich(ring: bool) -> Vector2:
	var m = lab.model
	var w: float = m.u("halbe_breite")
	var reach: float = m.u("oberschenkel") + m.u("unterschenkel")
	return Vector2(w * 2.0, 2.0 * (w + reach * 0.6)) if ring else Vector2(w * 2.0 + 0.02, 2.0 * (w + reach * 0.95))


func _set_hoehe_anteil(x: float) -> void:
	var bew = lab.bew
	if ist_ring():
		bew.ring_hoehe = x * bew.ring_height_max()
	else:
		bew.hoehe = 0.3 + x * 1.5
		if bew.mode == "" and lab.last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			bew.apply(bew.pose(lab.last_pose))
	lab.mark_dirty()
	_regler_texte()


func _set_spur_anteil(x: float) -> void:
	var bew = lab.bew
	var r := ist_ring()
	var b := _spur_bereich(r)
	var v := lerpf(b.x, b.y, x)
	if r:
		bew.spur_rollen = v
	else:
		bew.set_spur_gehen(v)
		if bew.mode == "" and lab.last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			bew.apply(bew.pose(lab.last_pose))
	lab.mark_dirty()
	_regler_texte()


func _regler_texte() -> void:
	if _ui.is_empty() or lab.bew == null:
		return
	var bew = lab.bew
	var r := ist_ring()
	(_ui["s_tempo"]["title"] as Label).text = T.t("Tempo") + " %.2f m/s" % bew.tempo + (" × %.1f" % tempo_k if absf(tempo_k - 1.0) > 0.05 else "")
	(_ui["s_hoehe"]["title"] as Label).text = T.t("Höhe") + (" %.1f cm" % (bew.ring_hoehe * 100.0) if r else " %.2f E" % bew.hoehe)
	(_ui["s_spur"]["title"] as Label).text = T.t("Spurbreite") + " %.1f cm" % ((bew.spur_rollen if r else bew.spur_gehen()) * 100.0)
	(_ui["s_neigen"]["title"] as Label).text = T.t("Neigen") + " %d°" % int(round(neigen * float(k_max()["neigen"])))


func refresh() -> void:
	"""bring the bar up to date (buttons blue when on, slider positions, controller, message)"""
	if _ui.is_empty() or lab == null or lab.model == null or lab.bew == null or not lab.model.built_ok:
		return
	var bew = lab.bew
	var r := ist_ring()
	lab._paint_btn(_ui["m_gehen"], not r and not koerper)
	lab._paint_btn(_ui["m_ring"], r)
	lab._paint_btn(_ui["m_koerper"], koerper)
	var chip: Button = _ui.get("chip")
	if chip != null:
		lab._paint_btn(chip, leiste)
	var ob: OptionButton = _ui["gang"]
	var gi: int = BEWEGUNG.GAENGE.map(func(x): return x[0]).find(bew.gang)
	if ob.selected != gi:
		ob.select(gi)
	(_ui["s_tempo"]["sl"] as HSlider).set_value_no_signal(bew.tempo)
	var hm: float = bew.ring_height_max()
	(_ui["s_hoehe"]["sl"] as HSlider).set_value_no_signal(bew.ring_hoehe / maxf(hm, 1e-4) if r else (bew.hoehe - 0.3) / 1.5)
	var b := _spur_bereich(r)
	var sv: float = bew.spur_rollen if r else bew.spur_gehen()
	(_ui["s_spur"]["sl"] as HSlider).set_value_no_signal(inverse_lerp(b.x, b.y, sv))
	(_ui["s_neigen"]["sl"] as HSlider).set_value_no_signal(neigen)
	(_ui["s_neigen"]["box"] as Control).visible = koerper
	(_ui["zur_mitte"] as CheckButton).visible = koerper
	(_ui["zur_mitte"] as CheckButton).set_pressed_no_signal(zur_mitte)
	_regler_texte()
	var pads := []
	for id in Input.get_connected_joypads():
		pads.append(Input.get_joy_name(id))
	(_ui["pad"] as Label).text = (T.t("Controller: %s") % ", ".join(pads) if not pads.is_empty() else T.t("Kein Controller verbunden")) \
			+ "\n" + T.t("Profil: %s") % (T.t("Standard") if aktiv == STANDARD else aktiv)
	var mt := meldung if _meldung_t > 0.0 else ""
	if koerper and k_phase == "aktiv" and k_grenze < 0.999:
		mt = T.t("Grenze erreicht (Reichweite, Servo oder Kipp-Reserve)")
	(_ui["meldung"] as Label).text = mt
	(_ui["meldung"] as Label).visible = mt != ""


func process(dt: float) -> void:
	if _meldung_t > 0.0:
		_meldung_t -= dt
	if _ui.is_empty():
		return
	(_ui["joy"] as Control).queue_redraw()
	(_ui["kompass"] as Control).queue_redraw()
	_ui_t -= dt
	if _ui_t <= 0.0:
		_ui_t = 0.25
		refresh()
		if _map != null and is_instance_valid(_map) and _map.visible:
			var pl: Label = _ui.get("map_pad")
			if pl != null:
				pl.text = (_ui["pad"] as Label).text.split("\n")[0]
			_map_live()


func _draw_joystick(c: Control) -> void:
	var sz := c.size
	var mid := sz * 0.5
	var rad := minf(sz.x, sz.y) * 0.5 - 2.0
	c.draw_circle(mid, rad, UI.FIELD)
	c.draw_arc(mid, rad, 0.0, TAU, 40, UI.LINE, 1.5)
	c.draw_line(mid - Vector2(rad * 0.6, 0), mid + Vector2(rad * 0.6, 0), UI.LINE, 1.0)
	c.draw_line(mid - Vector2(0, rad * 0.6), mid + Vector2(0, rad * 0.6), UI.LINE, 1.0)
	var v := Vector2(-out.x, -out.y)                       # what the robot gets now (all inputs, smooth)
	if v.length() > 1.0:
		v = v.normalized()
	c.draw_circle(mid + v * (rad - 9.0), 9.0, UI.ACC if v.length() > 0.02 or maus != Vector2.ZERO else UI.BTN2)
	c.draw_arc(mid + v * (rad - 9.0), 9.0, 0.0, TAU, 20, UI.TXT if maus != Vector2.ZERO else UI.LINE, 1.0)


func _joystick_input(c: Control, ev: InputEvent) -> void:
	var pos := Vector2.ZERO
	var on := false
	if ev is InputEventMouseButton and (ev as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		on = (ev as InputEventMouseButton).pressed
		pos = (ev as InputEventMouseButton).position
		if not on:
			maus = Vector2.ZERO
			return
	elif ev is InputEventMouseMotion and ((ev as InputEventMouseMotion).button_mask & MOUSE_BUTTON_MASK_LEFT) != 0:
		on = true
		pos = (ev as InputEventMouseMotion).position
	else:
		return
	var mid := c.size * 0.5
	var rad := minf(c.size.x, c.size.y) * 0.5 - 9.0
	var v := (pos - mid) / maxf(rad, 1.0)
	if v.length() > 1.0:
		v = v.normalized()
	maus = Vector2(v.x, -v.y)
	c.accept_event()


func _draw_kompass(c: Control) -> void:
	var sz := c.size
	var mid := Vector2(sz.x * 0.5, sz.y * 0.5 + 4.0)
	var rad := minf(sz.x, sz.y - 8.0) * 0.5 - 2.0
	c.draw_circle(mid, rad, UI.FIELD)
	c.draw_arc(mid, rad, 0.0, TAU, 40, UI.LINE, 1.5)
	var f := ThemeDB.fallback_font
	c.draw_string(f, Vector2(mid.x - 4.0, mid.y - rad + 11.0), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, UI.MUT)
	var m = lab.model
	if m == null or not m.built_ok:
		return
	var hd: Vector3 = m.segment_xf(0).origin - m.segment_xf(m.n() - 1).origin
	if ist_ring():
		hd = lab.bew.ring_state()["fw"]
	hd.y = 0.0
	if hd.length() < 0.01:
		return
	hd = hd.normalized()
	var dv := Vector2(hd.x, hd.z)                          # screen: x right = +X, down = +Z (north = −Z up)
	var tip := mid + dv * (rad - 4.0)
	var side := Vector2(-dv.y, dv.x) * 5.0
	c.draw_colored_polygon(PackedVector2Array([tip, mid - dv * 6.0 + side, mid - dv * 2.0, mid - dv * 6.0 - side]), UI.ACC)
	var deg := int(round(fposmod(rad_to_deg(atan2(hd.x, -hd.z)), 360.0)))
	c.draw_string(f, Vector2(2.0, 10.0), "%d°" % deg, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, UI.TXT)


# ==== Fenster «Belegung» =====================================================================================================
func open_map() -> void:
	if _map != null and is_instance_valid(_map):
		_map.visible = true
		_map_fill()
		return
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_STOP
	lab.win.add_child(root)
	_map = root
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.45)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(dim)
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.LINE, 10, 12, 1))
	pc.set_anchors_preset(Control.PRESET_CENTER)
	root.add_child(pc)
	_ui["map_panel"] = pc
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	pc.add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var tl := Label.new()
	tl.text = T.t("Belegung: Tastatur und Controller")
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 16)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(tl)
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.focus_mode = Control.FOCUS_NONE
	x.tooltip_text = T.t("Schliessen")
	x.pressed.connect(close_map)
	hd.add_child(x)
	var pl := UI.small("", UI.TXT)
	v.add_child(pl)
	_ui["map_pad"] = pl
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.set_meta("rad_scroll", true)
	v.add_child(sc)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 6)
	sc.add_child(body)
	_ui["map_body"] = body
	_map_fill()


func close_map() -> void:
	capture = {}
	if _map != null and is_instance_valid(_map):
		_map.visible = false


func map_open() -> bool:
	return _map != null and is_instance_valid(_map) and _map.visible


func _map_size() -> void:
	var pc: Control = _ui.get("map_panel")
	if pc == null:
		return
	var vs: Vector2 = lab.get_viewport().get_visible_rect().size
	var w := minf(620.0, vs.x - 16.0)
	var h := minf(680.0, vs.y - 16.0)
	pc.custom_minimum_size = Vector2(w, h)
	pc.size = Vector2(w, h)
	pc.position = (vs - Vector2(w, h)) * 0.5


func _map_fill() -> void:
	if not map_open():
		return
	_map_size()
	var body: VBoxContainer = _ui["map_body"]
	for c in body.get_children():
		body.remove_child(c)
		c.queue_free()
	var std := aktiv == STANDARD
	# Profile
	body.add_child(UI.small(T.t("Profil")))
	var pr := HFlowContainer.new()
	pr.add_theme_constant_override("h_separation", 4)
	pr.add_theme_constant_override("v_separation", 4)
	body.add_child(pr)
	var ob := OptionButton.new()
	ob.focus_mode = Control.FOCUS_NONE
	var ns := namen()
	for i in range(ns.size()):
		ob.add_item(T.t("Standard") if ns[i] == STANDARD else ns[i])
		if ns[i] == aktiv:
			ob.select(i)
	ob.item_selected.connect(func(i: int): waehle.call_deferred(ns[i]))
	pr.add_child(ob)
	var le := LineEdit.new()
	le.placeholder_text = T.t("Name")
	le.custom_minimum_size = Vector2(130, 0)
	le.text = "" if std else aktiv
	pr.add_child(le)
	_knopf(pr, T.t("Neu"), func(): neues_profil.call_deferred(le.text if le.text != aktiv else ""), T.t("Kopie des Profils unter neuem Namen"))
	var rb := _knopf(pr, T.t("Umbenennen"), func(): umbenennen.call_deferred(le.text))
	rb.disabled = std
	var db := _knopf(pr, T.t("Löschen"), func(): loeschen.call_deferred())
	db.disabled = std
	var sb := _knopf(pr, T.t("Standard wiederherstellen"), func(): standard_wiederherstellen.call_deferred())
	sb.disabled = std
	if std:
		body.add_child(UI.small(T.t("«Standard» bleibt fest – eine Änderung legt zuerst ein eigenes Profil an.")))
	# Totzone + Achsen umkehren
	var p := prof()
	var tz := HBoxContainer.new()
	body.add_child(tz)
	var tzl := UI.small(T.t("Totzone der Sticks: %d %%") % int(round(float(p["totzone"]) * 100.0)), UI.TXT)
	tzl.custom_minimum_size = Vector2(190, 0)
	tz.add_child(tzl)
	var tzs := HSlider.new()
	tzs.min_value = 0.0
	tzs.max_value = 0.5
	tzs.step = 0.01
	tzs.value = float(p["totzone"])
	tzs.focus_mode = Control.FOCUS_NONE
	tzs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tzs.drag_ended.connect(func(_c: bool): set_totzone.call_deferred(tzs.value))
	tzs.value_changed.connect(func(x: float): tzl.text = T.t("Totzone der Sticks: %d %%") % int(round(x * 100.0)))
	tz.add_child(tzs)
	body.add_child(UI.small(T.t("Achsen umkehren (Balken = Ausschlag jetzt)")))
	var ag := GridContainer.new()
	ag.columns = 2
	ag.add_theme_constant_override("h_separation", 8)
	body.add_child(ag)
	_ui["map_axes"] = []
	for a in ACHSEN:
		var ai: int = a[0]
		var cb := CheckButton.new()
		cb.text = T.t(a[1])
		cb.focus_mode = Control.FOCUS_NONE
		cb.add_theme_font_size_override("font_size", 12)
		cb.button_pressed = (p["umkehren"] as Array).has(ai)
		cb.toggled.connect(func(on: bool): umkehren.call_deferred(ai, on))
		cb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ag.add_child(cb)
		var pb := ProgressBar.new()
		pb.min_value = -1.0
		pb.max_value = 1.0
		pb.show_percentage = false
		pb.custom_minimum_size = Vector2(90, 10)
		pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		ag.add_child(pb)
		_ui["map_axes"].append([ai, pb])
	# Aktionen
	var hint := T.t("Feld anklicken, dann Taste drücken oder Knopf / Stick bewegen · Esc abbrechen · Entf leert")
	if not capture.is_empty():
		hint = (T.t("Taste drücken …") if capture["art"] == "taste" else T.t("Knopf drücken oder Stick / Trigger bewegen …")) \
				+ "  " + akt_name(capture["akt"]) + " · " + T.t("Esc abbrechen · Entf leert")
	var hl := UI.small(hint, UI.ACC if not capture.is_empty() else UI.MUT)
	hl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(hl)
	if not capture.is_empty():
		var ch := HBoxContainer.new()
		ch.add_theme_constant_override("separation", 6)
		body.add_child(ch)
		var ca: String = capture["akt"]
		var cr: String = capture["art"]
		_knopf(ch, T.t("Abbrechen"), func():
			capture = {}
			_map_fill.call_deferred())
		_knopf(ch, T.t("Leeren"), func():
			capture = {}
			belege.call_deferred(ca, cr, 0 if cr == "taste" else {}))
	var dp := doppelt()
	var gh := HBoxContainer.new()
	body.add_child(gh)
	for t in [[T.t("Aktion"), 0.0], [T.t("Tastatur"), 96.0], [T.t("Controller"), 124.0]]:
		var l := UI.small(t[0])
		if float(t[1]) > 0.0:
			l.custom_minimum_size = Vector2(t[1], 0)
		else:
			l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		gh.add_child(l)
	for a in AKTIONEN:
		var aid: String = a[0]
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 4)
		body.add_child(row)
		var nl := Label.new()
		nl.text = T.t(a[1])
		nl.add_theme_font_size_override("font_size", 13)
		nl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		nl.custom_minimum_size = Vector2(120, 0)
		if dp.has(aid):
			nl.add_theme_color_override("font_color", UI.ORG)
		row.add_child(nl)
		var kb := _knopf(row, taste_text(int((p["tasten"] as Dictionary).get(aid, 0))), func(): start_capture.call_deferred(aid, "taste"),
				T.t("Taste zuweisen"))
		kb.custom_minimum_size = Vector2(92, 0)
		kb.clip_text = true
		var pb := _knopf(row, pad_text((p["pad"] as Dictionary).get(aid, {})), func(): start_capture.call_deferred(aid, "pad"),
				T.t("Controller-Knopf oder Achse zuweisen"))
		pb.custom_minimum_size = Vector2(120, 0)
		pb.clip_text = true
		lab._paint_btn(kb, capture.get("akt", "") == aid and capture.get("art", "") == "taste")
		lab._paint_btn(pb, capture.get("akt", "") == aid and capture.get("art", "") == "pad")
		if capture.get("akt", "") == aid:
			(kb if capture["art"] == "taste" else pb).text = "…"
		if dp.has(aid):
			var dl := UI.small(T.t("doppelt belegt mit: %s") % ", ".join((dp[aid] as Array).map(func(o): return akt_name(o))), UI.ORG)
			dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			body.add_child(dl)
	body.add_child(UI.small(T.t("Im Ring wirken «Seitwärts links / rechts» als Kurve (Ring kippen). Beim Körper verschieben: vor / zurück / seitwärts verschieben, drehen = gieren, höher / tiefer = heben / senken.")))


func _map_live() -> void:
	for e in _ui.get("map_axes", []):
		var pb: ProgressBar = e[1]
		if is_instance_valid(pb):
			pb.value = achse(int(e[0]))
