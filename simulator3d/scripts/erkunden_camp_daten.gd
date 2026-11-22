extends RefCounted
## «Camp aufstellen» beim Frei erkunden (Fragebogen des Besitzers 22.11.2026, 13:10–13:16): nur Daten und Regeln, ohne Knoten -
## damit sie der Test (werkzeuge/erkunden_camp_test.gd) direkt prüfen kann. Das Aufstellen, das Feuer, die Nacht und das Einpacken
## selbst: erkunden_camp.gd. Was im Rucksack ist: erkunden_rucksack.gd (main.ex_rucksack).
##   * DINGE: was man aufstellen kann - nur, was im Rucksack ist (der Rucksack selbst ist immer da).
##   * pruefen(): passt der Platz? rot = zu steil (Grenzen wie bergtal.gd flat_limit: Zelt 8°, Tarp / Isomatte 10°, Biwak 12°),
##     zu nah (an einem anderen Ding; das Feuer mindestens 3 m vom Schlafplatz) oder im Wasser; sonst grün. Hinweise (Bach,
##     Steinschlag, Wildruhezone, ziemlich steil) halten nicht auf - aufstellen darf man überall.
##   * Feuer: feuer_neu / anzuenden / nachlegen / ticken / loeschen / temp - brennt (Holz), Glut, aus. Einpacken erst, wenn aus.
##   * Gespeichert (ein stehen gelassenes Camp): eigene Datei user://erkunden_camp.json (camp_norm prüft sie beim Laden).

const T = preload("res://scripts/i18n.gd")
const RS = preload("res://scripts/erkunden_rucksack.gd")

const SCHLAFPLAETZE := ["kuppelzelt", "einmannzelt", "tarp", "biwaksack", "isomatte"]
# id -> {name, braucht (eines davon im Rucksack, [] = immer), dazu (zusätzlich eines davon), r (m, Platzbedarf), steil (Grad),
#        art (Bild aus bib_berg.gd / bib_objekte.gd, "" = eigenes), weit (m vor der Figur für die Vorschau), gruppe}
const DINGE := {
	"kuppelzelt": {"name": "Kuppelzelt", "braucht": ["kuppelzelt"], "dazu": [], "r": 1.5, "steil": 8.0, "art": "bed_tent", "weit": 3.2, "gruppe": "schlafen"},
	"einmannzelt": {"name": "Einmannzelt", "braucht": ["einmannzelt"], "dazu": [], "r": 1.2, "steil": 8.0, "art": "bed_tent1", "weit": 2.8, "gruppe": "schlafen"},
	"tarp": {"name": "Tarp", "braucht": ["tarp", "ultratarp"], "dazu": [], "r": 1.4, "steil": 10.0, "art": "bed_tarp", "weit": 3.0, "gruppe": "schlafen"},
	"biwaksack": {"name": "Biwaksack", "braucht": ["biwaksack"], "dazu": [], "r": 1.1, "steil": 12.0, "art": "bed_bivy", "weit": 2.5, "gruppe": "schlafen"},
	"isomatte": {"name": "Isomatte + Schlafsack", "braucht": ["isomatte"], "dazu": ["sommerschlafsack", "winterschlafsack", "daunenschlafsack"],
			"r": 1.0, "steil": 10.0, "art": "bed_mat", "weit": 2.3, "gruppe": "schlafen"},
	"feuerstelle": {"name": "Feuerstelle", "braucht": ["zuendhoelzer"], "dazu": [], "r": 0.9, "steil": 15.0, "art": "campfire", "weit": 2.4, "gruppe": "feuer"},
	"kocher": {"name": "Kocher", "braucht": ["kocher"], "dazu": [], "r": 0.35, "steil": 20.0, "art": "stove", "weit": 1.4, "gruppe": "feuer"},
	"rucksack": {"name": "Rucksack", "braucht": [], "dazu": [], "r": 0.4, "steil": 30.0, "art": "backpack", "weit": 1.3, "gruppe": "klein"},
	"stirnlampe": {"name": "Stirnlampe (als Licht)", "braucht": ["stirnlampe"], "dazu": [], "r": 0.2, "steil": 30.0, "art": "", "weit": 1.2, "gruppe": "klein"},
	"sitzkissen": {"name": "Sitzkissen", "braucht": ["sitzkissen"], "dazu": [], "r": 0.3, "steil": 25.0, "art": "", "weit": 1.3, "gruppe": "klein"},
	"stuhl": {"name": "Campingstuhl", "braucht": ["stuhl"], "dazu": [], "r": 0.45, "steil": 18.0, "art": "", "weit": 1.5, "gruppe": "klein"},
	"waescheleine": {"name": "Wäscheleine", "braucht": ["waescheleine"], "dazu": [], "r": 1.3, "steil": 30.0, "art": "", "weit": 2.2, "gruppe": "klein"},
	"moveeye": {"name": "MoveEye auf dem Mini-Stativ", "braucht": ["ministativ"], "dazu": [], "r": 0.3, "steil": 30.0, "art": "tripod", "weit": 1.6, "gruppe": "moveeye"}}
const ORDER := ["kuppelzelt", "einmannzelt", "tarp", "biwaksack", "isomatte", "feuerstelle", "kocher", "rucksack", "stirnlampe", "sitzkissen",
		"stuhl", "waescheleine", "moveeye"]
const FEUER_ABSTAND := 3.0            # m: Feuer ↔ Schlafplatz (Funkenflug)
const LUECKE := 0.3                   # m zwischen zwei Dingen
const MINI_STATIV := 0.35             # m: so hoch steht der Kopf von MoveEye auf dem Mini-Stativ

# the fire: seconds of real time (the night is wound on with ticken(28800 …))
const HOLZ_MAX := 4.0                 # Scheite
const HOLZ_S := 150.0                 # s, bis ein Scheit abgebrannt ist
const GLUT_S := 240.0                 # s, bis die Glut kalt ist (ohne Löschen)
const GELOESCHT_S := 30.0             # s, bis eine gelöschte Feuerstelle nur noch handwarm ist
const T_FLAMME := 650.0               # °C
const T_GLUT := 320.0
const T_AUS := 35.0                   # darunter: «aus» (der Glut-Wächter sieht nichts Warmes mehr)


static func ding(id: String) -> Dictionary:
	return DINGE.get(id, {})


static func verfuegbar(r: Dictionary, id: String) -> String:
	"""'' = it is in the pack (may be set up), else why not"""
	var d := ding(id)
	if d.is_empty():
		return "?"
	var br: Array = d["braucht"]
	if not br.is_empty() and not RS.hat_eins(r, br):
		return T.t("Nicht im Rucksack")
	var dz: Array = d["dazu"]
	if not dz.is_empty() and not RS.hat_eins(r, dz):
		return T.t("Dazu braucht es einen Schlafsack")
	return ""


static func moeglich(r: Dictionary, stehen: Array) -> Array:
	"""the ids that can be set up now: in the pack and not standing yet (each thing once)"""
	var da := {}
	for e in stehen:
		da[str(e.get("id", ""))] = true
	var out := []
	for id in ORDER:
		if not da.has(id) and verfuegbar(r, id) == "":
			out.append(id)
	return out


static func pruefen(id: String, p: Vector2, steil_grad: float, im_wasser: bool, stehen: Array) -> Dictionary:
	"""the place for the preview: {ok, grund, farbe} - red: too steep, too close, in the water; green: fits"""
	var d := ding(id)
	if d.is_empty():
		return {"ok": false, "grund": "?", "farbe": "rot"}
	if im_wasser:
		return {"ok": false, "grund": T.t("Im Wasser"), "farbe": "rot"}
	if steil_grad > float(d["steil"]):
		return {"ok": false, "grund": T.t("Zu steil (%d°, höchstens %d°)") % [int(round(steil_grad)), int(d["steil"])], "farbe": "rot",
				"steil": steil_grad, "grenze": float(d["steil"])}
	for e in stehen:
		var oid := str(e.get("id", ""))
		var od := ding(oid)
		if od.is_empty():
			continue
		var q := Vector2(float(e.get("x", 0.0)), float(e.get("z", 0.0)))
		var abst := p.distance_to(q)
		var mind := float(d["r"]) + float(od["r"]) + LUECKE
		var feuer_schlaf := (id == "feuerstelle" and oid in SCHLAFPLAETZE) or (oid == "feuerstelle" and id in SCHLAFPLAETZE)
		if feuer_schlaf:
			mind = maxf(mind, FEUER_ABSTAND + float(od["r"]) * (0.0 if oid == "feuerstelle" else 1.0) + float(d["r"]) * (0.0 if id == "feuerstelle" else 1.0))
		if abst < mind:
			var g := T.t("Zu nah am Feuer") if oid == "feuerstelle" else (T.t("Zu nah am Schlafplatz (Funken)") if feuer_schlaf else T.t("Zu nah an: %s") % T.t(str(od["name"])))
			return {"ok": false, "grund": g, "farbe": "rot", "abstand": abst, "mind": mind}
	return {"ok": true, "grund": "", "farbe": "gruen", "steil": steil_grad}


static func hinweise(id: String, steil_grad: float, w: Dictionary) -> Array:
	"""what one should know (never blocks): w = {bach_m, steinschlag, wildruhezone, wald, schutz, trocken}"""
	var out := []
	var d := ding(id)
	if not d.is_empty() and steil_grad > float(d["steil"]) * 0.7 and steil_grad <= float(d["steil"]):
		out.append(T.t("Ziemlich schräg – du rutschst vielleicht in der Nacht"))
	if float(w.get("bach_m", INF)) < 15.0:
		out.append(T.t("Nahe am Bach: laut, feucht, und bei Gewitter kann das Wasser steigen"))
	if float(w.get("steinschlag", 0.0)) > 0.4:
		out.append(T.t("Steinschlag möglich: Felswand oberhalb"))
	var wz = w.get("wildruhezone", {})
	if wz is Dictionary and not (wz as Dictionary).is_empty():
		out.append(T.t("In der Wildruhezone «%s» (Schutzzeit %s) – hier besser nicht übernachten") % [str(wz.get("name", "?")), str(wz.get("z", "?"))])
	if id == "feuerstelle":
		out.append_array(feuer_verbot(w))
	return out


static func feuer_verbot(w: Dictionary) -> Array:
	"""reasons for a fire ban here (empty = none): forest, protected area, drought"""
	var out := []
	if bool(w.get("wald", false)):
		out.append(T.t("Feuerverbot im Wald: Feuer nur an festen Feuerstellen"))
	if bool(w.get("schutz", false)) or (w.get("wildruhezone", {}) is Dictionary and not (w.get("wildruhezone", {}) as Dictionary).is_empty()):
		out.append(T.t("Schutzgebiet: hier ist Feuer verboten"))
	if bool(w.get("trocken", false)):
		out.append(T.t("Trockenheit: Feuerverbot im Freien"))
	return out


# ---- the fire ------------------------------------------------------------------------------------------------------------------
static func feuer_neu() -> Dictionary:
	return {"phase": "aus", "holz": 0.0, "glut": 0.0, "kalt": 0.0, "aus_seit": -1.0}


static func anzuenden(f: Dictionary) -> Dictionary:
	"""{f, ok, grund}: needs a cold or glowing fire place; the first wood is gathered on the spot"""
	var o := f.duplicate()
	if str(o["phase"]) == "brennt":
		return {"f": o, "ok": false, "grund": T.t("Das Feuer brennt schon")}
	if float(o["holz"]) < 1.0:
		o["holz"] = 1.0
	o["phase"] = "brennt"
	o["glut"] = 1.0
	o["kalt"] = 0.0
	o["aus_seit"] = -1.0
	return {"f": o, "ok": true, "grund": ""}


static func nachlegen(f: Dictionary) -> Dictionary:
	var o := f.duplicate()
	if float(o["holz"]) >= HOLZ_MAX:
		return {"f": o, "ok": false, "grund": T.t("Genug Holz im Feuer")}
	o["holz"] = minf(HOLZ_MAX, float(o["holz"]) + 1.0)
	if str(o["phase"]) == "glut":
		o["phase"] = "brennt"                                        # embers light the new wood
		o["glut"] = 1.0
	return {"f": o, "ok": true, "grund": ""}


static func loeschen(f: Dictionary) -> Dictionary:
	var o := f.duplicate()
	if str(o["phase"]) in ["aus", "geloescht"]:
		return {"f": o, "ok": false, "grund": T.t("Das Feuer ist schon aus")}
	o["phase"] = "geloescht"
	o["holz"] = 0.0
	o["glut"] = 0.0
	o["kalt"] = 1.0
	return {"f": o, "ok": true, "grund": ""}


static func ticken(f: Dictionary, s: float, uhr_h := -1.0) -> Dictionary:
	"""s seconds later (may be a whole night at once); uhr_h: the clock at the start (for «aus seit»)"""
	var o := f.duplicate()
	var rest := s
	var t := 0.0
	for _i in range(20):
		if rest <= 0.0:
			break
		match str(o["phase"]):
			"brennt":
				var dauer := float(o["holz"]) * HOLZ_S
				if rest < dauer:
					o["holz"] = float(o["holz"]) - rest / HOLZ_S
					rest = 0.0
				else:
					rest -= dauer
					t += dauer
					o["holz"] = 0.0
					o["phase"] = "glut"
					o["glut"] = 1.0
			"glut":
				var dauer2 := float(o["glut"]) * GLUT_S
				if rest < dauer2:
					o["glut"] = float(o["glut"]) - rest / GLUT_S
					rest = 0.0
				else:
					rest -= dauer2
					t += dauer2
					o["glut"] = 0.0
					o["phase"] = "aus"
					o["aus_seit"] = fposmod(uhr_h + t / 3600.0, 24.0) if uhr_h >= 0.0 else -1.0
			"geloescht":
				var dauer3 := float(o["kalt"]) * GELOESCHT_S
				if rest < dauer3:
					o["kalt"] = float(o["kalt"]) - rest / GELOESCHT_S
					rest = 0.0
				else:
					rest -= dauer3
					t += dauer3
					o["kalt"] = 0.0
					o["phase"] = "aus"
					o["aus_seit"] = fposmod(uhr_h + t / 3600.0, 24.0) if uhr_h >= 0.0 else -1.0
			_:
				rest = 0.0
	return o


static func temp(f: Dictionary, luft: float) -> float:
	"""°C on the surface - what the thermal camera sees"""
	match str(f.get("phase", "aus")):
		"brennt":
			return T_FLAMME
		"glut":
			return lerpf(T_AUS + 5.0, T_GLUT, clampf(float(f["glut"]), 0.0, 1.0))
		"geloescht":
			return lerpf(luft + 2.0, 60.0, clampf(float(f["kalt"]), 0.0, 1.0))
	return luft


static func ist_aus(f: Dictionary, luft := 15.0) -> bool:
	return str(f.get("phase", "aus")) == "aus" or (str(f.get("phase", "")) == "geloescht" and temp(f, luft) < T_AUS)


static func darf_einpacken(id: String, stehen: Array, f: Dictionary) -> String:
	"""'' = may be packed; the fire place only when the fire is out - and «Alles einpacken» too"""
	if id in ["feuerstelle", "*"]:
		var hat_feuer := id == "feuerstelle"
		if id == "*":
			for e in stehen:
				if str(e.get("id", "")) == "feuerstelle":
					hat_feuer = true
		if hat_feuer and not ist_aus(f):
			return T.t("Zuerst das Feuer löschen")
	return ""


# ---- a camp that was left standing -------------------------------------------------------------------------------------------
static func camp_norm(d) -> Dictionary:
	"""{scene, stehen: [{id, x, y, z, yaw}], feuer, uhr} - {} when it is not a valid camp"""
	if not (d is Dictionary) or str(d.get("scene", "")) == "" or not (d.get("stehen", null) is Array):
		return {}
	var st := []
	var da := {}
	for e in d["stehen"]:
		if not (e is Dictionary):
			continue
		var id := str(e.get("id", ""))
		if ding(id).is_empty() or da.has(id):
			continue
		da[id] = true
		st.append({"id": id, "x": float(e.get("x", 0.0)), "y": float(e.get("y", 0.0)), "z": float(e.get("z", 0.0)), "yaw": float(e.get("yaw", 0.0))})
	if st.is_empty():
		return {}
	var f = d.get("feuer", {})
	var fn := feuer_neu()
	if f is Dictionary:
		for k in fn:
			if f.has(k):
				fn[k] = f[k] if k == "phase" else float(f[k])
	if not str(fn["phase"]) in ["aus", "brennt", "glut", "geloescht"]:
		fn["phase"] = "aus"
	return {"scene": str(d["scene"]), "stehen": st, "feuer": fn, "uhr": float(d.get("uhr", 12.0))}


# ---- the night («Nacht spulen») ------------------------------------------------------------------------------------------------
const NACHT_ARTEN := [["fuchs", "Ein Fuchs schnüffelt am Camp", 0.55], ["reh", "Ein Reh zieht vorbei", 0.4], ["marder", "Ein Marder am Rucksack", 0.3],
		["igel", "Ein Igel raschelt im Gras", 0.3], ["wanderer", "Jemand mit Stirnlampe geht vorbei", 0.25], ["wind", "Windböe – die Zeltplane flattert", 0.35],
		["eule", "Eine Eule ruft", 0.3]]


static func nacht_plan(seed_: int, w: Dictionary) -> Array:
	"""the events of one night (fixed by seed_): [{art, text, uhr, winkel}] - w: {tiere, leute, wind} 0 … 1 make some more likely"""
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	var out := []
	for a in NACHT_ARTEN:
		var k := float(a[2])
		match str(a[0]):
			"fuchs", "reh", "marder", "igel":
				k *= 0.6 + float(w.get("tiere", 0.5))
			"wanderer":
				k *= 0.3 + 1.4 * float(w.get("leute", 0.3))
			"wind":
				k *= 0.4 + 1.2 * float(w.get("wind", 0.4))
		if rng.randf() < k:
			out.append({"art": str(a[0]), "text": str(a[1]), "uhr": fposmod(22.0 + rng.randf() * 8.5, 24.0), "winkel": rng.randf_range(-PI, PI)})
	out.sort_custom(func(x, y): return fposmod(float(x["uhr"]) - 12.0, 24.0) < fposmod(float(y["uhr"]) - 12.0, 24.0))
	return out


static func gesehen(ev: Dictionary, mw_da: bool, mw_yaw: float, sicht := 1.25) -> bool:
	"""MoveEye on the mini tripod sees what happens inside its field of view (the head turns: ± sicht rad); wind / owl: no picture"""
	if not mw_da or str(ev.get("art", "")) in ["eule"]:
		return false
	return absf(wrapf(float(ev["winkel"]) - mw_yaw, -PI, PI)) <= sicht


static func uhr_text(h: float) -> String:
	var hh := fposmod(h, 24.0)
	return "%02d:%02d" % [int(hh), int(fmod(hh, 1.0) * 60.0)]
