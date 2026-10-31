extends RefCounted
## Abenteuer A4 «Rucksack» (Daniel, 31.10.2026): Essen und Trinken (mild), Ausrüstung finden, Tauschen, Rucksack-Anzeige.
## Eigene Datei; bergtal_abenteuer.gd ruft sie nur an kleinen Einhänge-Punkten auf («# A4»). Das Inventar selbst steht in
## abenteuer_inventar.gd (hat / gib / nimm / anzahl / gewicht - auch für die anderen Pakete).
##
## Essen und Trinken MILD: hungrig oder durstig = nur langsamer (Gehzeit und Kraft je ~10–20 % mehr), nie Spielende.
##   Auf der Hilfe-Stufe «Leicht» (Paket A3) ist es ganz aus: kein Verbrauch, keine Balken. Quellen und Brunnen am Weg füllen
##   die Flasche auf, in der Hütte (Alp Tschuggen, Holzofen; im Biwak mit eigenem Kocher) wird gekocht.
## Ausrüstung finden: an festen Fundorten der Kapitel liegen Kompass, Stirnlampe und Seil (den Feldstecher gibt es nur als
##   Grossvaters Feldstecher von A3, Daniel 31.10.2026); einmal gefunden
##   bleiben sie für alle weiteren Kapitel (abenteuer_inventar.gd finde()). Die Stirnlampe ist ein echtes Licht (licht.gd
##   attach_lamp): im Dunkeln leuchtet sie vor dem Wanderer und am Lager - bis zum Schlafen (dann bewacht MoveEye im Dunkeln).
## Tauschen: jede Figur hat eine feste Wunschliste (was sie sucht / was sie dafür gibt) - kein Geld, feste Paare.
##   Die Listen kommen von Paket A2 (abenteuer_figuren.gd wuensche() / wunschliste(): feste Paare mit Anzahl, z. B. 2 Proviant
##   gegen 1 Seil, «einmal» = nur einmal). Nach dem Tausch meldet A4 das an A2 (tausch_erledigt).
## Steuerbefehl: {"action": "abenteuer", "do": "a4_eat" | "a4_cook" | "a4_tausch" (figur) | "a4_tausch_gib" (value) |
##                "a4_tausch_bekomme" (value) | "a4_tausch_ok" | "a4_tausch_zu" | "a4_inv" | "a4_gib" (key, n) | "a4_find" (key)}

const T = preload("res://scripts/i18n.gd")
const Inv = preload("res://scripts/abenteuer_inventar.gd")
const Fig = preload("res://scripts/abenteuer_figuren.gd")      # A2: wuensche(fid) (statisch); Paare über ab.a2.wunschliste(fid)

# ---- Quellen und Brunnen (Tal-Koordinaten wie bergtal.gd: x = Osten, z = Süden): [Name, x, z] --------------------------------
const QUELLEN := [["Brunnen bei der Kapelle St. Jodern", 210.0, -700.0], ["Brunnen bei der Alp Tschuggen", 69.0, -9.0],
		["Quelle am Gumpisee", -150.0, -330.0], ["Brunnen bei der alten Sennerei", -700.0, -130.0],
		["Quelle unter dem Biwak", -540.0, 530.0]]
const QUELLE_R := 80.0                 # so nah muss der Weg vorbeiführen (m)
# ---- Hütten zum Kochen: [Name, x, z, braucht eigenen Kocher] ---------------------------------------------------------------
const HUETTEN := [["Alp Tschuggen (Holzofen)", 60.0, 0.0, false], ["Biwakschachtel Chüebodehorn", -512.0, 548.0, true]]
const HUETTE_R := 70.0
# ---- Fundorte der Ausrüstung: id -> [Kapitel, x, z, Text] ----------------------------------------------------------------
const FUNDE := {"kompass": [1, 178.0, -200.0, "Am Fuss des Wegweisers steckt eine verbeulte Blechdose. Darin: ein alter Kartenkompass, die Nadel zittert und zeigt nach Norden."],
		"stirnlampe": [2, -150.0, -230.0, "Neben dem Weg hängt eine Stirnlampe an einem Ast - jemand hat sie vergessen. Sie leuchtet noch."],
		"seil": [4, -700.0, -130.0, "In der alten Sennerei hängt ein aufgerolltes Seil am Haken - stark genug für den Fels."]}
const FUND_R := 70.0
# Begegnungen von heute (bergtal_abenteuer_daten.gd MEET) -> Figur zum Tauschen
const MEET_FIGUR := {"senner": "aelpler", "wanderer": "wanderer", "wanderer2": "wanderer", "bergsteiger": "bergsteiger"}

const ORG := Color(1.0, 0.62, 0.26)
const DIM := Color(0.6, 0.66, 0.74)

static var _lamp_holder: Node3D = null    # der «Kopf» des Wanderers mit der Stirnlampe (licht.gd attach_lamp)
static var _lamp_on := false
static var _lamp_t := 0.0


# =======================================================================================================================
# Hilfe-Stufe (kommt von A3) und Essen / Trinken
# =======================================================================================================================
static func hilfe_stufe(ab) -> String:
	"""«leicht» | «normal» | «schwer» - die Hilfe-Stufe von A3 (abenteuer_raetsel.gd hilfe(), über ab.hilfe_stufe())"""
	if ab != null and ab.has_method("hilfe_stufe"):
		return str(ab.hilfe_stufe())
	return "normal"


static func essen_an(ab) -> bool:
	return hilfe_stufe(ab) != "leicht"


static func verbrauch_f(ab) -> float:
	return 1.0 if essen_an(ab) else 0.0


static func hungrig(ab) -> bool:
	return essen_an(ab) and float(ab.R.get("food", 50.0)) < 20.0


static func durstig(ab) -> bool:
	return essen_an(ab) and float(ab.R.get("water", 1.0)) <= 0.05


static func kraft_f(ab) -> float:
	"""mild: so viel mehr Kraft kostet ein Weg hungrig / durstig (statt früher ×1,4 / ×1,3)"""
	var f := 1.0
	if hungrig(ab):
		f *= 1.1 if float(ab.R["food"]) > 0.0 else 1.15
	if durstig(ab):
		f *= 1.12
	return f


static func tempo_f(ab) -> float:
	"""mild: so viel länger dauert ein Weg hungrig / durstig - nur langsamer, nie Spielende"""
	var f := 1.0
	if hungrig(ab):
		f *= 1.1 if float(ab.R["food"]) > 0.0 else 1.2
	if durstig(ab):
		f *= 1.15
	return f


static func essen(ab) -> Dictionary:
	"""eine Portion essen: Proviant, sonst Alpkäse"""
	if ab.R.is_empty() or bool(ab.R.get("walking", false)):
		return {"ok": false, "error": "unterwegs"}
	var was := "proviant" if Inv.hat("proviant") else ("kaese" if Inv.hat("kaese") else "")
	if was == "":
		return {"ok": false, "error": T.t("Kein Proviant und kein Käse mehr im Rucksack.")}
	Inv.nimm(was)
	ab.R["food"] = minf(100.0, float(ab.R["food"]) + (45.0 if was == "proviant" else 30.0))
	ab.main.set_hour(ab.main.hour() + 0.1)
	ab.choices.append([int(ab.R["stage"]), "a4_eat", was])
	ab._diary("pause", T.t("Gegessen"), T.t("Eine Portion Proviant.") if was == "proviant" else T.t("Ein Stück Alpkäse - kräftig und gut."))
	ab._changed()
	return {"ok": true, "food": ab.R["food"], "ate": was}


static func quelle(ab) -> String:
	return str(ab.R.get("a4_quelle", ""))


static func huette(ab) -> Array:
	"""die Hütte, bei der man gerade ist ([] = keine)"""
	if ab.R.is_empty():
		return []
	var p: Vector2 = ab.R.get("camp_xz", ab.R["pos"]) if int(ab.step) == 5 else ab.R["pos"]
	for h in HUETTEN:
		if p.distance_to(Vector2(float(h[1]), float(h[2]))) < HUETTE_R:
			if bool(h[3]) and not Inv.hat("kocher"):
				continue
			return h
	return []


static func kochen(ab) -> Dictionary:
	var h := huette(ab)
	if h.is_empty() or bool(ab.R.get("walking", false)):
		return {"ok": false, "error": T.t("Hier ist keine Hütte zum Kochen.")}
	if ab.R.get("a4_gekocht", "") == "%s@%d" % [str(h[0]), int(ab.R["stage"])]:
		return {"ok": false, "error": T.t("Hier hast du schon gekocht.")}
	ab.R["a4_gekocht"] = "%s@%d" % [str(h[0]), int(ab.R["stage"])]
	var mit := Inv.nimm("proviant")
	ab.main.set_hour(ab.main.hour() + 0.75)
	ab.R["food"] = 100.0
	ab.R["water"] = float(maxi(1, int(ab.R["items"].get("wasser", 0))))
	ab.R["stamina"] = minf(float(ab.R["smax"]), float(ab.R["stamina"]) + (30.0 if mit else 20.0))
	ab.choices.append([int(ab.R["stage"]), "a4_cook", "1"])
	ab._diary("pause", T.t("In der Hütte gekocht"), T.t("Im Ofen knistert das Holz, die Suppe dampft. Die Flasche ist wieder voll.") if mit
			else T.t("Kein Proviant mehr - aber im Hüttenvorrat sind Teigwaren und Tee. Die Flasche ist wieder voll."))
	ab._changed()
	return {"ok": true, "food": ab.R["food"], "stamina": ab.R["stamina"]}


# =======================================================================================================================
# nach jedem Abschnitt: Quelle in der Nähe? Ausrüstung gefunden?
# =======================================================================================================================
static func _near(ab, x: float, z: float, r: float) -> bool:
	var w: Array = ab.R["walked"]
	for p in w.slice(maxi(0, w.size() - 6)):
		if (p as Vector2).distance_to(Vector2(x, z)) < r:
			return true
	return false


static func nach_abschnitt(ab, _i: int) -> bool:
	"""aus _post_leg aufgerufen; true = es kommt eine Frage (Fund), _post_leg hört dann auf"""
	ab.R["a4_quelle"] = ""
	for q in QUELLEN:
		if _near(ab, float(q[1]), float(q[2]), QUELLE_R):
			ab.R["a4_quelle"] = str(q[0])
	for id in FUNDE:
		var fd: Array = FUNDE[id]
		if int(fd[0]) != int(ab.R["chapter"]) or ab.R["events_done"].has("a4_fund_" + id):
			continue
		if _near(ab, float(fd[1]), float(fd[2]), FUND_R):
			ab.R["events_done"]["a4_fund_" + id] = true
			if Inv.hat(id) and Inv.bleibend(id):
				continue
			ab._diary("find", T.t("Ausrüstung gefunden"), T.t(str(fd[3])))
			ab._snap_later(T.t(Inv.name_of(id)), "view")
			ab._ask("a4_fund", T.t("Ausrüstung gefunden: %s") % T.t(Inv.name_of(id)), T.t(str(fd[3])) + "\n" + T.t("%.2f kg") % Inv.gewicht(id),
					[["take", T.t("Einpacken (bleibt für alle Kapitel)")], ["leave", T.t("Liegen lassen")]], {"a4_item": id})
			return true
	return false


static func choose(ab, pe: Dictionary, v: String) -> void:
	match str(pe["kind"]):
		"a4_fund":
			if v == "take":
				Inv.finde(str(pe["a4_item"]))


static func begegnung(ab, meet_id: String) -> void:
	"""eine Begegnung unterwegs: kann man mit ihr tauschen, merkt man sich die Figur (Knopf «Tauschen mit …»)"""
	if MEET_FIGUR.has(meet_id):
		ab.R["a4_figur"] = MEET_FIGUR[meet_id]


# =======================================================================================================================
# Tauschen (feste Wunschliste je Figur, kein Geld)
# =======================================================================================================================
static func wuensche(figur_id: String) -> Dictionary:
	"""{name, will: [ids], gibt: [ids], figur} - von Paket A2 (abenteuer_figuren.gd wuensche())"""
	return Fig.wuensche(figur_id)


static func paare(ab, figur_id: String) -> Array:
	"""die offenen festen Paare der Figur (A2 wunschliste: will, will_n, gibt, gibt_n, einmal, i, figur, erledigt)"""
	var a2 = ab.get("a2") if ab != null else null
	if a2 == null or not is_instance_valid(a2):
		return []
	return (a2.wunschliste(figur_id) as Array).filter(func(w): return not bool(w["erledigt"]))


static func _paar(m: Dictionary, g: String, b: String) -> Dictionary:
	for w in m.get("paare", []):
		if str(w["will"]) == g and str(w["gibt"]) == b:
			return w
	return {}


static func tausch_oeffnen(ab, figur_id: String) -> Dictionary:
	"""öffnet das Tausch-Fenster (A2 ruft das bei einem Gespräch auf)"""
	var w := wuensche(figur_id)
	if w.is_empty():
		return {"ok": false, "error": "keine Wunschliste: " + figur_id}
	ab.R["a4_tausch"] = {"figur": figur_id, "gib": "", "bekomme": ""}
	ab._changed()
	return {"ok": true, "wuensche": w}


static func _tausch_moeglich(ab) -> Dictionary:
	"""geben = was die Figur will und genug im Rucksack ist; bekommen = was sie dafür gibt (ist «gib» gewählt: nur das Passende)"""
	var tz: Dictionary = ab.R.get("a4_tausch", {})
	if tz.is_empty():
		return {}
	var w := wuensche(str(tz["figur"]))
	var done: Array = (ab.P.get("a4_getauscht", {}) as Dictionary).get(str(tz["figur"]), [])
	var ps: Array = []
	for p in paare(ab, str(tz["figur"])):
		var s := str(p["gibt"])
		if (Inv.bleibend(s) or s in ["stirnlampe", "feldstecher"]) and (Inv.hat(s) or s in done):
			continue
		ps.append(p)
	var geben := []
	var bekommen := []
	var nn := {}
	for p in ps:
		var g := str(p["will"])
		if Inv.anzahl(g) >= int(p["will_n"]) and not g in geben:
			geben.append(g)
		if (str(tz.get("gib", "")) == "" or str(tz["gib"]) == g) and not str(p["gibt"]) in bekommen:
			bekommen.append(str(p["gibt"]))
		nn[g] = int(p["will_n"])
		nn[str(p["gibt"])] = int(p["gibt_n"])
	return {"w": w, "geben": geben, "bekommen": bekommen, "paare": ps, "n": nn}


static func tausch(ab) -> Dictionary:
	var tz: Dictionary = ab.R.get("a4_tausch", {})
	var m := _tausch_moeglich(ab)
	if m.is_empty():
		return {"ok": false, "error": "kein Tausch offen"}
	var g := str(tz.get("gib", ""))
	var b := str(tz.get("bekomme", ""))
	var p := _paar(m, g, b)
	if not g in m["geben"] or p.is_empty() or Inv.anzahl(g) < int(p["will_n"]):
		return {"ok": false, "error": T.t("Wähle, was du gibst und was du dafür bekommst.")}
	Inv.nimm(g, int(p["will_n"]))
	if Inv.bleibend(b) or b in ["stirnlampe", "feldstecher"]:
		Inv.finde(b)
	else:
		Inv.gib(b, int(p["gibt_n"]))
	var gt: Dictionary = ab.P.get("a4_getauscht", {})
	var lst: Array = gt.get(str(tz["figur"]), [])
	lst.append(b)
	gt[str(tz["figur"])] = lst
	ab.P["a4_getauscht"] = gt
	var a2 = ab.get("a2")
	if a2 != null and is_instance_valid(a2):
		a2.tausch_erledigt(str(p["figur"]), int(p["i"]))            # A2: «einmal»-Paare sind danach erledigt
	ab._save()
	ab.choices.append([int(ab.R["stage"]), "a4_tausch", "%s:%s>%s" % [str(tz["figur"]), g, b]])
	ab._diary("meet", T.t("Getauscht"), T.t("%s gegen %s - mit %s.") % [_n_name(g, int(p["will_n"])), _n_name(b, int(p["gibt_n"])), T.t(str(m["w"].get("name", tz["figur"])))])
	tz["gib"] = ""
	tz["bekomme"] = ""
	ab._changed()
	return {"ok": true, "gab": g, "bekam": b, "gab_n": int(p["will_n"]), "bekam_n": int(p["gibt_n"])}


static func _n_name(id: String, n: int) -> String:
	return "%d× %s" % [n, T.t(Inv.name_of(id))] if n > 1 else T.t(Inv.name_of(id))


# =======================================================================================================================
# Steuerbefehl (bergtal_abenteuer.gd op() leitet «a4_…» hierher)
# =======================================================================================================================
static func op(ab, what: String, d: Dictionary) -> Dictionary:
	match what:
		"a4_eat":
			return essen(ab)
		"a4_cook":
			return kochen(ab)
		"a4_tausch":
			return tausch_oeffnen(ab, str(d.get("figur", ab.R.get("a4_figur", ""))))
		"a4_tausch_gib":
			if ab.R.has("a4_tausch"):
				ab.R["a4_tausch"]["gib"] = str(d.get("value", ""))
				var bk: Array = _tausch_moeglich(ab).get("bekommen", [])
				if bk.size() == 1 or not str(ab.R["a4_tausch"]["bekomme"]) in bk:
					ab.R["a4_tausch"]["bekomme"] = str(bk[0]) if bk.size() == 1 else ""
				ab._changed()
			return {"ok": ab.R.has("a4_tausch")}
		"a4_tausch_bekomme":
			if ab.R.has("a4_tausch"):
				ab.R["a4_tausch"]["bekomme"] = str(d.get("value", ""))
				ab._changed()
			return {"ok": ab.R.has("a4_tausch")}
		"a4_tausch_ok":
			return tausch(ab)
		"a4_tausch_zu":
			ab.R.erase("a4_tausch")
			ab._changed()
			return {"ok": true}
		"a4_inv":
			return {"ok": true, "liste": Inv.liste(), "extra_kg": Inv.extra_kg(), "hilfe": hilfe_stufe(ab), "essen_an": essen_an(ab),
					"quelle": quelle(ab), "huette": huette(ab), "lampe": _lamp_on, "tausch": _tausch_moeglich(ab).get("bekommen", [])}
		"a4_gib":                                       # Tests
			return {"ok": true, "n": Inv.gib(str(d.get("key", "")), int(d.get("n", 1)))}
		"a4_find":                                      # Tests
			Inv.finde(str(d.get("key", "")))
			return {"ok": true}
	return {"ok": false, "error": "unbekannt: " + what}


static func replay(ab, c: Array) -> bool:
	"""«Genau gleich nochmals»: eine A4-Entscheidung wiederholen; true = erledigt (aus der Liste nehmen)"""
	var idle: bool = int(ab.step) in [4, 5] and not bool(ab.R.get("walking", false)) and (ab.R["pending"] as Dictionary).is_empty()
	if not idle:
		return false
	match str(c[1]):
		"a4_eat":
			essen(ab)
		"a4_cook":
			kochen(ab)
		"a4_tausch":
			var pr := str(c[2]).split(":")
			if pr.size() == 2 and pr[1].contains(">"):
				var gb := pr[1].split(">")
				tausch_oeffnen(ab, pr[0])
				ab.R["a4_tausch"]["gib"] = gb[0]
				ab.R["a4_tausch"]["bekomme"] = gb[1]
				tausch(ab)
				ab.R.erase("a4_tausch")
	return true


# =======================================================================================================================
# Stirnlampe: ein echtes Licht (licht.gd) am Wanderer
# =======================================================================================================================
static func tick(ab, dt: float) -> void:
	_lamp_t -= dt
	if _lamp_t > 0.0:
		return
	_lamp_t = 0.25
	if ab.R.is_empty():
		_lampe(ab, false, Vector2.ZERO, Vector2.ZERO)
		return
	if not ab.R.has("a4_inv0"):                         # für «Situation speichern»: die bleibenden Dinge beim Start
		ab.R["a4_inv0"] = Inv.bleib_box().duplicate(true)
	if bool(ab.R.get("walking", false)):
		ab.R["a4_quelle"] = ""
	var want: bool = int(ab.step) in [4, 5] and ab.main.is_dark() and Inv.hat("stirnlampe")
	var p: Vector2 = ab.R["pos"] if int(ab.step) == 4 else ab.R.get("camp_xz", ab.R["pos"])
	var ahead := p + Vector2(0, -1)
	if not ab.leg.is_empty():
		ahead = ab._along(ab.leg["pts"], minf(1.0, float(ab.leg["f"]) + 0.05))
	_lampe(ab, want, p, ahead)


static func _lampe(ab, on: bool, p: Vector2, ahead: Vector2) -> void:
	var lic = ab.main.licht if "licht" in ab.main else null
	if lic == null:
		return
	if on and (_lamp_holder == null or not is_instance_valid(_lamp_holder)):
		_lamp_holder = Node3D.new()
		_lamp_holder.name = "A4Stirnlampe"
		ab.main.add_child(_lamp_holder)
		lic.attach_lamp(_lamp_holder, "head", true)
	if _lamp_holder == null or not is_instance_valid(_lamp_holder):
		_lamp_on = false
		return
	if on:
		var b = ab.bt()
		var gp := Vector3(p.x, 0.0, p.y)
		var ga := Vector3(ahead.x, 0.0, ahead.y)
		if b != null:
			gp = b.WG(p.x, p.y, 0.0)
			ga = b.WG(ahead.x, ahead.y, 0.0)
		_lamp_holder.global_position = gp
		var d := ga - gp
		d.y = 0.0
		if d.length() > 0.2:
			_lamp_holder.look_at(gp + d, Vector3.UP)
	if on != _lamp_on:
		_lamp_on = on
		for x in lic._extra:
			if x["node"] == _lamp_holder:
				x["force"] = on
		lic._lamps_extra_now()


# =======================================================================================================================
# Anzeige (Rucksack, Knöpfe, Tausch-Fenster)
# =======================================================================================================================
static func stat_extra(ab, g: Control) -> void:
	"""unter den Balken: was im Rucksack ist und wie es dir geht"""
	var parts := []
	for e in Inv.liste():
		var nm := T.t(Inv.name_of(str(e[0])))
		parts.append(nm if int(e[1]) == 1 else "%d× %s" % [int(e[1]), nm])
	if not parts.is_empty():
		g.add_child(ab._lab(T.t("Im Rucksack: %s") % ", ".join(parts), 12, DIM))
	if not essen_an(ab):
		g.add_child(ab._lab(T.t("Essen und Trinken: aus (Schwierigkeit Leicht)"), 12, DIM))
	elif hungrig(ab) or durstig(ab):
		var w := []
		if hungrig(ab):
			w.append(T.t("hungrig"))
		if durstig(ab):
			w.append(T.t("durstig"))
		g.add_child(ab._lab(T.t("Du bist %s - du gehst langsamer. Essen, trinken oder an einer Quelle auffüllen.") % T.t(" und ").join(w), 12, ORG))


static func hud_buttons(ab, acts: Control, idle: bool) -> void:
	if essen_an(ab):
		var n := Inv.anzahl("proviant") + Inv.anzahl("kaese")
		ab._btn(acts, T.t("Essen (%d Portionen)") % n, func(): ab.op({"do": "a4_eat"}), false, not idle or n == 0)
		if quelle(ab) != "" and not bool(ab.R.get("bach", false)):
			ab._btn(acts, T.t("Wasser auffüllen (%s)") % T.t(quelle(ab)), func(): ab.op({"do": "refill"}), false, not idle)
	var h := huette(ab)
	if not h.is_empty():
		ab._btn(acts, T.t("Kochen: %s (45 Min.)") % T.t(str(h[0])), func(): ab.op({"do": "a4_cook"}), false, not idle)
	var fg := str(ab.R.get("a4_figur", ""))
	if fg != "" and not ab.R.has("a4_tausch"):
		var w := wuensche(fg)
		if not w.is_empty():
			ab._btn(acts, T.t("Tauschen mit: %s") % T.t(str(w.get("name", fg))), func(): ab.op({"do": "a4_tausch", "figur": fg}), false, not idle)


static func paint_tausch(ab, parent: Control) -> void:
	var tz: Dictionary = ab.R.get("a4_tausch", {})
	var m := _tausch_moeglich(ab)
	if m.is_empty():
		return
	var w: Dictionary = m["w"]
	var g = ab._group(T.t("Tauschen mit: %s") % T.t(str(w.get("name", tz["figur"]))), parent)
	var sucht := []
	for id in w.get("will", []):
		sucht.append(T.t(Inv.name_of(str(id))))
	g.add_child(ab._lab(T.t("Kein Geld - nur Tausch nach der Wunschliste. Gesucht: %s.") % ", ".join(sucht), 13, DIM))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 6)
	g.add_child(row)
	row.add_child(ab._lab(T.t("Du gibst:"), 13, Color.WHITE, false))
	if (m["geben"] as Array).is_empty():
		row.add_child(ab._lab(T.t("(nichts davon im Rucksack)"), 13, ORG, false))
	for id in m["geben"]:
		var ii: String = id
		var b: Button = ab._btn(row, _n_name(ii, int(m["n"].get(ii, 1))), func(): ab.op({"do": "a4_tausch_gib", "value": ii}), str(tz["gib"]) == ii)
		b.toggle_mode = true
		b.button_pressed = str(tz["gib"]) == ii
	var row2 := HFlowContainer.new()
	row2.add_theme_constant_override("h_separation", 6)
	g.add_child(row2)
	row2.add_child(ab._lab(T.t("Du bekommst:"), 13, Color.WHITE, false))
	if (m["bekommen"] as Array).is_empty():
		row2.add_child(ab._lab(T.t("(hat nichts mehr für dich)"), 13, ORG, false))
	for id in m["bekommen"]:
		var ii: String = id
		var b: Button = ab._btn(row2, "%s (%.2f kg)" % [_n_name(ii, int(m["n"].get(ii, 1))), Inv.gewicht(ii) * int(m["n"].get(ii, 1))], func(): ab.op({"do": "a4_tausch_bekomme", "value": ii}), str(tz["bekomme"]) == ii)
		b.toggle_mode = true
		b.button_pressed = str(tz["bekomme"]) == ii
	var r3 := HBoxContainer.new()
	r3.add_theme_constant_override("separation", 8)
	g.add_child(r3)
	ab._btn(r3, T.t("Tauschen"), func(): ab.op({"do": "a4_tausch_ok"}), true, str(tz["gib"]) == "" or str(tz["bekomme"]) == "")
	ab._btn(r3, T.t("Fertig"), func(): ab.op({"do": "a4_tausch_zu"}))


static func paint_pack(ab) -> void:
	"""Packliste: gefundene Ausrüstung (immer dabei, zählt ins Gewicht)"""
	var bb := Inv.bleib_box()
	if bb.is_empty():
		return
	var parts := []
	for e in Inv.liste():
		var id := str(e[0])
		if Inv.bleibend(id) or bb.has("fund_" + Inv._id(id)):
			parts.append("%s (%.2f kg)" % [T.t(Inv.name_of(id)), Inv.gewicht(id) * int(e[1])])
	if parts.is_empty():
		return
	var g = ab._group(T.t("Gefundene Ausrüstung (immer dabei)"))
	g.add_child(ab._lab(", ".join(parts), 13, Color.WHITE))
	g.add_child(ab._lab(T.t("Zusammen %.1f kg - schon im Gewicht oben eingerechnet.") % Inv.extra_kg(), 12, DIM))
