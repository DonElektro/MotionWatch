extends Node
## «Maggie und der Bergkristall» für zwei Spieler - die Zwei-Spieler-Bausteine (zwei_bausteine.gd) eingebaut (Daniel 31.10.2026).
## Der Wirt (host) für zwei_bausteine.gd; ein Kind von maggie_zwei.gd («mz», Einhänge-Punkt dort in _ready), nur aktiv, wenn
## zwei spielen und Spieler 2 dabei ist (mz.dabei()) und die geteilten Ansichten laufen. Allein: nichts.
##   Rollen:  💎 Kristall-Hüter/in (Spieler 1, trägt den Kristall): sieht, was der Kristall über Gefahren in der Nähe weiss;
##            ⬇ = Kristall-Licht (Bild der Zukunft)
##            🐕 Hundeführer/in (Spieler 2 als Wanderer) bzw. 🐕 Maggie (Spieler 2 steuert Maggie): weiss, was Maggie riecht
##            (was die nächste Station braucht); ⬇ = Spürnase (Spuren sichtbar, Pfeil zur nächsten Station)
##   Controller: A B X Y gehören Maggie und den Teamrätseln - die Bausteine nehmen LB = Team (Räuberleiter, High-Five,
##            Lagerfeuer «so!»), RB = weitergeben, ⬇ = Fähigkeit, ⬆ = Foto, ◀ ▶ = wählen. Tastatur Spieler 1: F G V R T.
##   Geteiltes Wissen: Kristall-Wissen (story._zk_orte, die Zukunftsbild-Orte der Gefahren) nur bei Spieler 1, Maggies Nase
##            (maggie_hund.aktuell()) nur bei Spieler 2
##   Räuberleiter: eine Felsstufe pro Region auf dem Weg vom Rastplatz zum Tor (nur Spieler 2 als Wanderer); «oben» heisst
##            hier: über die Stufe drüber (die Figuren der Geschichte bleiben am Boden)
##   Rucksack teilen: die Schutzdinge (maggie_gefahr.schutz: Wasserflasche, Fackel, Kuhglocke, Wanderstock); B (Schutzding
##            benutzen) geht nur, wenn Spieler 1 es trägt - sonst gibt Spieler 2 es mit RB weiter (Einhänge-Punkt in mz._p1_buttons)
##   Rücken an Rücken: maggie_gefahr.warnung (ein böses Tier ist nah) → das Geräusch kommt aus seiner Richtung
##   Wer findet mehr: pro Region Glitzersteine, ein Steinmännchen, eine Spur; gelöste Stationen zählen für den, der näher ist
##   Lagerfeuer: am ersten neuen Rastplatz der Region ein Fenster mit der Frage an beide (◀ ▶ wählen, LB = so!)
##   Reisetagebuch: am Ende jeder Region (region_beendet) - pro Spielstand in user://zwei_tagebuch/platz_<n>/maggie
##   High-Five: nach Teamrätsel, Rettung, Station, Räuberleiter, Rücken an Rücken
##   Gummiband: ist das Tor offen und einer weiter als 15 m weg, wartet das Tor (Einhänge-Punkt in maggie_story._region_tick)
## Steuerbefehl: /control {"action": "maggie", "do": "zwei", "k": "zb", "was": … (zwei_bausteine.op) | setzen (p, x, z, yaw)}

const T = preload("res://scripts/i18n.gd")
const Bausteine = preload("res://scripts/zwei_bausteine.gd")
const SS = preload("res://scripts/spielstand.gd")

const ROLLE_1 := {"id": "kristall", "name": "Kristall-Hüter", "name_f": "Kristall-Hüterin", "icon": "💎", "faehigkeit": "Kristall-Licht", "cd": 25,
		"text": "Trägt den Kristall und weiss, wo Gefahren lauern. ⬇ = Bild der Zukunft."}
const ROLLE_2 := {"id": "nase", "name": "Hundeführer", "name_f": "Hundeführerin", "icon": "🐕", "faehigkeit": "Spürnase", "cd": 15,
		"text": "Weiss, was Maggie riecht. ⬇ = Spuren sichtbar und Pfeil zur nächsten Aufgabe."}
const ROLLE_2M := {"id": "nase", "name": "Maggie", "name_f": "Maggie", "icon": "🐕", "faehigkeit": "Spürnase", "cd": 15,
		"text": "Ist Maggie und riecht, was die anderen nicht wissen. ⬇ = Spuren und Pfeil zur nächsten Aufgabe."}
const PAD := {"team": "l1", "geben": "r1", "faehig": "down", "foto": "up"}
const BOESE := {"wildschwein": "ein Wildschwein", "wolf": "einen Wolf", "kraehe": "Krähen", "viper": "eine Viper"}
const FAEHIG := {"riechen": "riechen", "graben": "graben", "schluepfen": "durchschlüpfen", "warnen": "warnen"}
const FRAGEN := ["Was war in dieser Jahreszeit das Schönste?", "Welches Tier hat dir am besten gefallen?", "Was war am gruseligsten?",
		"Was hat Maggie heute am besten gemacht?"]

var mz                                 # maggie_zwei.gd
var story
var main
var zb
var _reg := ""
var _frage_reg := ""
var _wiss_t := 0.0
var _ger_next := 0.0
var _rng := RandomNumberGenerator.new()
var _verbunden := false
var _spawn_reg := ""


func _init(m) -> void:
	mz = m
	story = m.story
	main = m.main
	name = "zwei_team"
	_rng.randomize()
	zb = Bausteine.new()
	zb.name = "ZweiBausteine"
	zb.setup(self, main, "maggie")
	add_child(zb)


func _bt():
	return mz._bt()


func _yaw_tal(world_yaw: float) -> float:
	var b = _bt()
	return world_yaw - float(b.wrot(0.0)) if b != null else world_yaw


# =======================================================================================================================
# host functions
# =======================================================================================================================
func zb_aktiv() -> bool:
	return mz.aktiv and mz.on and mz.dabei() and story != null and story.running


func zb_spieler() -> int:
	return 2


func zb_pos(i: int) -> Vector2:
	if i == 0:
		return mz._p1_tal()
	var q = mz._p2_tal()
	return q if q is Vector2 else mz._p1_tal()


func zb_yaw(i: int) -> float:
	return _yaw_tal(float(story.cam_yaw) if i == 0 else float(mz.yaw2))


func zb_name(i: int) -> String:
	return mz._n1() if i == 0 else mz._n2()


func zb_farbe(i: int) -> Color:
	return mz.COLS[i]


func zb_dev(i: int) -> int:
	if i == 0:
		var L: Array = mz._p1_devs()
		return int(L[0]) if not L.is_empty() else -1
	return int(mz.p2dev) if int(mz.p2dev) >= 0 else -1


func zb_pad() -> Dictionary:
	return PAD


func zb_rect(i: int) -> Rect2:
	if mz.merged or (mz._v[1] as Dictionary).is_empty():
		var bx0 = (mz._v[0] as Dictionary).get("box")
		return Rect2(bx0.position, bx0.size) if bx0 != null else Rect2()
	var bx = (mz._v[i] as Dictionary).get("box")
	return Rect2(bx.position, bx.size) if bx != null else Rect2()


func zb_ui():
	return mz._root


func zb_welt(q: Vector2, h: float) -> Vector3:
	return story.tal_punkt(q.x, q.y) + Vector3(0, h, 0)


func zb_3d():
	return story


func zb_ordner() -> String:
	return "user://zwei_tagebuch/platz_%d/maggie" % SS.slot()


func zb_eingabe_frei(_i: int) -> bool:
	return not main.typing() and not bool(mz._frozen)


func zb_setzen(i: int, q: Vector2) -> void:
	"""«oben» = über die Felsstufe drüber (die Figuren bleiben am Boden)"""
	var w := zb_welt(q + Vector2(0, 2.2), 0.0)
	if i == 0:
		story.spieler_setzen(w)
	elif mz.rolle == "wanderer":
		mz._fig2_place(w)


func zb_bild(i: int):
	var v: Dictionary = mz._v[0 if mz.merged else i]
	if v.is_empty():
		return null
	return (v["vp"] as SubViewport).get_texture().get_image()


func zb_kamera(i: int):
	var v: Dictionary = mz._v[0 if mz.merged else i]
	return v.get("cam")


func zb_tiere() -> Array:
	var L: Array = []
	if main.visitors != null:
		for v in main.visitors.get_children():
			if v.has_method("is_animal") and v.is_animal():
				L.append(v)
	var hl = story.get_node_or_null("maggie_hund")
	if hl != null:
		for c in hl.get_children():
			if c is Node3D and (c as Node3D).has_meta("tier"):
				L.append(c)
	return L


func zb_tier_id(a) -> String:
	if a.has_meta("tier"):
		return str(a.get_meta("tier"))
	return str(a.kind) if "kind" in a else ""


func zb_licht() -> float:
	return clampf((float(main.sun_el()) + 6.0) / 16.0, 0.05, 1.0)


func zb_rollen() -> Array:
	return [ROLLE_1, ROLLE_2M if mz.rolle == "maggie" else ROLLE_2]


func zb_faehigkeit(i: int, id: String) -> String:
	match id:
		"kristall":
			if story.has_method("look_into_crystal"):
				story.look_into_crystal()
				return T.t("Der Kristall zeigt ein Bild der Zukunft.")
		"nase":
			var q := zb_pos(i)
			var n: int = zb.spuren_zeigen(q, 50.0, 25.0)
			var h = mz._hund()
			var st: Dictionary = h.aktuell() if h != null and h.has_method("aktuell") else {}
			if not st.is_empty() and st.get("p") is Vector3:
				var sp: Vector3 = st["p"]
				zb.pfeil(i, Vector2(sp.x, sp.z), "🐕 %d m" % int(q.distance_to(Vector2(sp.x, sp.z))), 9.0)
				return T.t("Maggie hat eine Spur! Spuren in der Nähe: %d") % n
			return T.t("Spuren in der Nähe: %d") % n
	return ""


func zb_ereignis(art: String, d: Dictionary) -> void:
	match art:
		"raeuberleiter":
			story.tipp(T.t("Geschafft - zusammen über die Felsstufe!"))
		"ruecken":
			story.tipp(T.t("Gut aufgepasst! %s hat %s gesehen.") % [str(d.get("wer", "")), str(d.get("wen", ""))])


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _process(dt: float) -> void:
	if story == null or not mz.aktiv:
		return
	if not _verbunden:
		_verbinden()
	var reg := str(story.region)
	if reg != _reg:
		_reg = reg
		_spawn_reg = ""
	if not zb_aktiv():
		return
	if reg != "" and _spawn_reg != reg:
		_spawn_reg = reg
		_region_start(reg)                      # (also when player 2 joins later)
	_wiss_t -= dt
	if _wiss_t <= 0.0:
		_wiss_t = 0.8
		_wissen()
		_rucksack()


func _verbinden() -> void:
	_verbunden = true
	if mz.has_signal("rastplatz"):
		mz.rastplatz.connect(_on_rast)
	if mz.has_signal("teamraetsel_geloest"):
		mz.teamraetsel_geloest.connect(func(_r, _a): zb.zaehle(0, "teamwork"); zb.zaehle(1, "teamwork"); zb.high_five("teamraetsel"))
	if mz.has_signal("gerettet_zwei"):
		mz.gerettet_zwei.connect(func(_w): zb.zaehle(1, "teamwork"); zb.high_five("gerettet"))
	if mz.has_signal("fund"):
		mz.fund.connect(_on_fund)
	if story.has_signal("region_beendet"):
		story.region_beendet.connect(_on_region_ende)
	var g = mz._gefahr()
	if g != null and g.has_signal("warnung"):
		g.warnung.connect(_on_warnung)


func _region_start(reg: String) -> void:
	"""things to find, a rock step between the rest place and the gate"""
	zb.neu()
	var a := _tal2(story.rastplatz_pos())
	var b := _tal2(story.tor_pos())
	var d := b - a
	if d.length() < 20.0:
		d = Vector2(60, 0)
	var side := Vector2(-d.y, d.x).normalized()
	var kinds := [["funde", "einen Glitzerstein"], ["funde", "eine Feder"], ["steinmaennchen", "ein Steinmännchen"], ["spuren", "eine Spur"]]
	for k in range(kinds.size()):
		var f := _rng.randf_range(0.15, 0.85)
		var q := a + d * f + side * _rng.randf_range(-18.0, 18.0)
		zb.fundstueck("%s_%s_%d" % [reg, kinds[k][0], k], q, str(kinds[k][0]), T.t(str(kinds[k][1])))
	if mz.rolle == "wanderer":
		zb.teamstelle("ts_" + reg, a + d * 0.45 + side * 6.0, T.t("Felsstufe"), 1.6, 0)
	_frage_reg = ""


func _tal2(w: Vector3) -> Vector2:
	return mz._tal(w)


func _wissen() -> void:
	"""Kristall (player 1) and Maggie's nose (player 2): each sees only his own"""
	var w := ["", ""]
	var p1 := zb_pos(0)
	var best := ""
	var bd := 60.0
	var zk = story.get("_zk_orte")
	for e in (zk if zk is Array else []):
		var q := _tal2(e[0])
		var dd := p1.distance_to(q)
		if dd < bd:
			bd = dd
			best = str(e[1])
	if best != "":
		w[0] = T.t("💎 Der Kristall flüstert: %s") % best
	var h = mz._hund()
	if h != null and h.has_method("aktuell"):
		var st: Dictionary = h.aktuell()
		if not st.is_empty() and st.get("p") is Vector3:
			var sp: Vector3 = st["p"]
			var d2 := zb_pos(1).distance_to(Vector2(sp.x, sp.z))
			if d2 < 45.0:
				var f := str(st.get("f", ""))
				w[1] = T.t("🐕 Maggie riecht etwas (%d m): hier hilft %s.") % [int(d2), T.t(str(FAEHIG.get(f, f)))]
	zb.wissen("maggie", w)


func _rucksack() -> void:
	var g = mz._gefahr()
	if g == null or mz.rolle != "wanderer":
		zb.rucksack_setzen([])
		return
	var L: Array = []
	for id in g.schutz:
		L.append([str(id), T.t(str(g.SCHUTZ_NAME.get(str(id), str(id)))), 0.6])
	zb.rucksack_setzen(L)


func darf_benutzen() -> bool:
	"""maggie_zwei._p1_buttons (B = Schutzding): only when player 1 carries it"""
	if not zb_aktiv() or mz.rolle != "wanderer":
		return true
	var g = mz._gefahr()
	if g == null:
		return true
	var id := str(g.SCHUTZ.get(str(story.region), ""))
	if id == "" or zb.traeger(id) != 1:
		return true
	zb.say(0, T.t("Das Schutzding hat %s - %s: %s = dir geben") % [zb_name(1), zb_name(1), zb._k(1, "geben")], 3.0, 3)
	zb.say(1, T.t("%s braucht das Schutzding! %s = geben") % [zb_name(0), zb._k(1, "geben")], 3.0, 3)
	return false


func haelt() -> bool:
	"""maggie_story._region_tick: the gate waits for both"""
	if not zb_aktiv():
		return false
	var t := _tal2(story.tor_pos())
	if zb_pos(1).distance_to(t) > 15.0:
		zb.wichtig("tor", t, 15.0, T.t("Tor"), true, 60.0)
		return zb.haelt()
	zb.wichtig_weg("tor")
	return false


func _on_rast(_i: int) -> void:
	if not zb_aktiv() or _frage_reg == str(story.region):
		return
	_frage_reg = str(story.region)
	var opts: Array = [T.t("Maggie"), T.t("Der Kristall"), T.t("Die Tiere"), T.t("Das Teamrätsel"), T.t("Zusammen wandern")]
	zb.lagerfeuer_frage(T.t(str(FRAGEN[_rng.randi() % FRAGEN.size()])), opts, true)
	zb.lagerfeuer_fenster()


func _on_fund(_id: String) -> void:
	if not zb_aktiv():
		return
	var h = mz._hund()
	var hp := zb_pos(0)
	if h != null and h.hund != null and is_instance_valid(h.hund):
		hp = _tal2((h.hund as Node3D).global_position)
	var i := 0 if zb_pos(0).distance_to(hp) <= zb_pos(1).distance_to(hp) else 1
	zb.zaehle(i, "funde")
	zb.high_five("station")


func _on_warnung(_stufe: int, art: String, pos: Vector3) -> void:
	if not zb_aktiv() or zb.now() < _ger_next:
		return
	_ger_next = zb.now() + 150.0
	zb.geraeusch(T.t("Da ist etwas!"), art, T.t(str(BOESE.get(art, "ein Tier"))), _tal2(pos))


func _on_region_ende(id: String) -> void:
	if not mz.aktiv or not mz.dabei():
		return
	var nm := {"herbst": "Herbst", "winter": "Winter", "fruehling": "Frühling", "sommer": "Sommer"}
	zb.tag_speichern(T.t("Maggie und der Bergkristall") + " · " + T.t(str(nm.get(id, id))))
	zb.neu()


func control(d: Dictionary) -> Dictionary:
	if str(d.get("was", "")) == "setzen":
		var i := clampi(int(d.get("p", 1)) - 1, 0, 1)
		if d.has("x"):
			var w := zb_welt(Vector2(float(d["x"]), float(d["z"])), 0.0)
			if i == 0:
				story.spieler_setzen(w)
			elif mz.rolle == "wanderer":
				mz._fig2_place(w)
		if d.has("yaw"):
			if i == 0:
				story.cam_yaw = float(d["yaw"]) + (float(_bt().wrot(0.0)) if _bt() != null else 0.0)
			else:
				mz.yaw2 = float(d["yaw"]) + (float(_bt().wrot(0.0)) if _bt() != null else 0.0)
		return {"ok": true, "zb": zb.state()}
	if str(d.get("was", "")) == "region":
		_region_start(str(story.region))
		return {"ok": true, "zb": zb.state()}
	return zb.op(d)
