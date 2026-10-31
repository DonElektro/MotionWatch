extends RefCounted
## «Die Karte des Grossvaters» zu zweit - die Zwei-Spieler-Bausteine (zwei_bausteine.gd) eingebaut (Daniel 31.10.2026).
## Der Wirt (host) für zwei_bausteine.gd: kennt das Abenteuer (bergtal_abenteuer.gd «ab») und die zwei Wanderer
## (abenteuer_zweit.gd «z»). In abenteuer_zweit.gd nur kleine Einhänge-Punkte (Suche nach «team.»). Allein: nichts.
##   Rollen:  🗺 Kartenleser/in (Spieler 1; in «Rollen» Spieler 2, der die Karte hat) - sieht Teamstellen und den Weg zum Ziel,
##            X = Wegweiser (Pfeil zum nächsten Fund und zum Etappenziel)
##            🧭 Späher/in (Kompass + Spürnase) - kennt die Peilungen und die Hinweise, X = Spüren (Spuren sichtbar,
##            ein Geräusch orten); Kompass-Richtung immer im eigenen Bildschirmteil
##   Geteiltes Wissen: «Karte und Kompass» (A3) - die Zahlen der Peilung stehen nur beim Späher, im Bedienfeld «??»;
##            «Karte lesen» - den Hinweis hat der Späher, der Kartenleser wählt den Ort
##   Räuberleiter: höchstens eine Felsstufe pro Kapitel auf einem langen Wegstück (nur «Gemeinsam» / «Wettrennen»);
##            die Tour wartet dort (Gummiband), bis beide oben sind (längstens 4 Min.)
##   Wer findet mehr: pro Wegstück ein Glitzerstein, ein Steinmännchen und eine Spur (nur mit «Spüren» sichtbar) neben dem Weg;
##            Tagebuchseiten und Fundstücke der Tour zählen für den, der näher bei der Gruppe ist
##   Rücken an Rücken: ein Geräusch unterwegs (einmal nach ~2 Min., dann alle 4–7 Min., im Dunkeln öfter)
##   Lagerfeuer am Nachtlager (Frage an beide), Fotowettbewerb am Abend, Reisetagebuch am Morgen (pro Spielstand)
##   High-Five nach «Karte lesen» richtig, «Karte und Kompass» richtig, Polarstern, Räuberleiter, Rücken an Rücken
##   Gummiband: am Ende jedes Wegstücks wartet die Tour, wenn einer mehr als 60 m weg ist (längstens 60 s)
## Spielstand: R["zb"] (zwei_bausteine.zustand()) - kommt mit dem Lauf (Hütte / Lager) mit.
## Steuerbefehl: {"action": "abenteuer", "do": "zweit", "k": "zb", "was": … (zwei_bausteine.op) | ts_hier | funde_hier | lager}

const T = preload("res://scripts/i18n.gd")
const ZB = preload("res://scripts/zwei_bausteine.gd")
const Inv = preload("res://scripts/abenteuer_inventar.gd")
const A1 = preload("res://scripts/abenteuer_moveeye.gd")
const SS = preload("res://scripts/spielstand.gd")
const Bt = preload("res://scripts/bergtal.gd")

const ROLLEN := [{"id": "karte", "name": "Kartenleser", "name_f": "Kartenleserin", "icon": "🗺", "faehigkeit": "Wegweiser", "cd": 15,
			"text": "Hat die Karte: sieht Felsstufen und das Ziel. X = Wegweiser (Pfeil zum nächsten Fund und zum Etappenziel)."},
		{"id": "kompass", "name": "Späher", "name_f": "Späherin", "icon": "🧭", "faehigkeit": "Spüren", "cd": 15,
			"text": "Hat Kompass und Spürnase: kennt Peilungen und Hinweise. X = Spüren (Spuren sichtbar, Geräusche orten)."}]
const FRAGEN := ["Was war heute das Schönste?", "Welcher Moment war heute am lustigsten?", "Was hat dich heute überrascht?",
		"Wo möchtest du nochmals hin?", "Was war heute am schwierigsten?"]
const FUNDE := [["funde", "einen glitzernden Bergkristall"], ["funde", "eine alte Münze"], ["funde", "einen Edelweiss-Anstecker"],
		["steinmaennchen", "ein Steinmännchen"], ["spuren", "eine Gämsspur"], ["spuren", "eine Fuchsspur"], ["spuren", "eine Hasenspur"]]

var z                                  # abenteuer_zweit.gd
var ab                                 # bergtal_abenteuer.gd
var main
var zb                                 # zwei_bausteine.gd
var hoehe: Array = [0.0, 0.0]
var _run := ""
var _pe_sig := ""
var _log_n := 0
var _ger_t := 120.0
var _sync_t := 0.0
var _save_t := 0.0
var _leg_hold := {}                    # {i, t0}
var _step_last := -1
var _rng := RandomNumberGenerator.new()


func _init(zw) -> void:
	z = zw
	ab = zw.ab
	main = zw.main
	_rng.randomize()
	zb = ZB.new()
	zb.name = "ZweiBausteine"
	zb.setup(self, main, "abenteuer")
	zw.add_child(zb)


func team() -> bool:
	"""two people play (not alone) and a run is going"""
	return z.mode != "allein" and not ab.R.is_empty()


# =======================================================================================================================
# the host functions for zwei_bausteine.gd
# =======================================================================================================================
func zb_aktiv() -> bool:
	return bool(z.on) and z.mode != "allein"


func zb_spieler() -> int:
	return 1 if z.mode == "rollen" else 2


func zb_knoepfe(i: int) -> bool:
	return i == 0 or z.mode != "rollen"


func zb_pos(i: int) -> Vector2:
	if z.mode == "rollen":
		i = 0
	return z.pl[i]["pos"]


func zb_yaw(i: int) -> float:
	if z.mode == "rollen":
		i = 0
	return float(z.pl[i]["yaw"])


func zb_name(i: int) -> String:
	return str(z.names[i])


func zb_farbe(i: int) -> Color:
	return z.COLS[i]


func zb_dev(i: int) -> int:
	return int(z.pl[i]["dev"])


func zb_rect(i: int) -> Rect2:
	if z.merged:
		var a: Rect2 = z._area()
		return a
	if z.mode == "rollen" and i == 1:
		return Rect2(z._role_box.position, z._role_box.size) if z._role_box != null else Rect2()
	var bx = z.pl[i]["box"]
	return Rect2(bx.position, bx.size) if bx != null else Rect2()


func zb_ui():
	return z._root


func zb_welt(q: Vector2, h: float) -> Vector3:
	var b = ab.bt()
	return b.WG(q.x, q.y, h) if b != null else Vector3(q.x, h, q.y)


func zb_3d():
	return main


func zb_layer() -> int:
	return z.HELPER_LAYER


func zb_ordner() -> String:
	return "user://zwei_tagebuch/platz_%d/grossvater" % SS.slot()


func zb_eingabe_frei(_i: int) -> bool:
	return not (main.padmap != null and main.padmap.menu) and not z._typing()


func zb_heben(i: int, h: float) -> void:
	hoehe[clampi(i, 0, 1)] = h


func zb_setzen(i: int, q: Vector2) -> void:
	if not z.race.is_empty():
		z.pl[i]["pos"] = q
		return
	var anchor: Vector2 = ab.R.get("pos", Vector2.ZERO)
	z.pl[i]["off"] = q - anchor
	z.pl[i]["idle"] = -30.0                    # stays there a while (does not walk back to the group at once)


func zb_bild(i: int):
	var vp = z.pl[0 if z.merged or z.mode == "rollen" else i]["vp"]
	if vp == null:
		return null
	return (vp as SubViewport).get_texture().get_image()


func zb_kamera(i: int):
	return z.pl[0 if z.merged or z.mode == "rollen" else i]["cam"]


func zb_tiere() -> Array:
	var L: Array = []
	if main.visitors == null:
		return L
	for v in main.visitors.get_children():
		if (v.has_method("is_animal") and v.is_animal()) or v.has_meta("a1_tier") or v.has_meta("berg_kind"):
			L.append(v)
	return L


func zb_tier_id(a) -> String:
	var t: String = ab.a1.tier_of(a) if ab.a1 != null else ""
	if t == "" and a != null and "kind" in a:
		t = str(a.kind)
	return t


func zb_foto_wertung(f: Dictionary) -> Dictionary:
	return A1.foto_wertung(f)                  # Paket A1: Abstand, Grösse, Bewegungsunschärfe, Licht, Seltenheit


func zb_licht() -> float:
	return clampf((float(main.sun_el()) + 6.0) / 16.0, 0.05, 1.0)


func zb_rollen() -> Array:
	if z.mode == "rollen":                    # Spieler 2 hat die Karte (bedient MoveEye und die Karte)
		return [ROLLEN[0], ROLLEN[1]] if zb.tausch else [ROLLEN[1], ROLLEN[0]]
	return ROLLEN


func zb_maler():
	return ab


func zb_neu_malen() -> void:
	ab._changed()


func zb_info(i: int) -> String:
	if zb.rolle(i).get("id", "") == "kompass":
		var deg := int(round(fposmod(-rad_to_deg(zb_yaw(i)), 360.0)))        # 0 = north (-z), turning right = east
		return "🧭 %s %d°" % [T.t(ab.dir_word(float(deg))), deg]
	if not ab.leg.is_empty():
		var e: Vector2 = (ab.leg["pts"] as Array)[-1]
		return "🏁 %s %d m" % [T.t("Etappenziel"), int(zb_pos(i).distance_to(e))]
	return ""


func zb_faehigkeit(i: int, id: String) -> String:
	var q := zb_pos(i)
	match id:
		"karte":
			var f: Dictionary = zb.naechster_fund(q)
			var said := ""
			if not f.is_empty():
				zb.pfeil(-1, f["pos"], "%s %d m" % [str(ZB.KAT_ICON.get(str(f["kat"]), "💎")), int(q.distance_to(f["pos"]))], 9.0)
				said = T.t("Auf der Karte: etwas %d m entfernt.") % int(q.distance_to(f["pos"]))
			if not ab.leg.is_empty():
				var e: Vector2 = (ab.leg["pts"] as Array)[-1]
				zb.pfeil(-1, e, "🏁 %d m" % int(q.distance_to(e)), 9.0)
				if said == "":
					said = T.t("Das Etappenziel ist %d m entfernt.") % int(q.distance_to(e))
			return said
		"kompass":
			var n: int = zb.spuren_zeigen(q, 50.0, 25.0)
			var src: Vector2 = zb.ruecken_quelle()
			if src != Vector2.INF:
				zb.pfeil(i, src, "👂", 6.0)
				return T.t("Du hörst es genau: dort!")
			return T.t("Spuren in der Nähe: %d") % n if n > 0 else T.t("Keine Spuren in der Nähe.")
	return ""


func zb_ereignis(art: String, d: Dictionary) -> void:
	if ab.R.is_empty():
		return
	match art:
		"raeuberleiter":
			ab._diary("zb", T.t("Räuberleiter"), T.t("%s hat geholfen, zusammen sind wir über die Felsstufe.") % str(d.get("helfer", "")))
			ab._snap_later(T.t("Räuberleiter"), "view")
		"ruecken":
			ab._diary("zb", T.t("Rücken an Rücken"), T.t("Ein Geräusch - Rücken an Rücken haben wir alles abgesucht. %s hat %s gesehen.") % [str(d.get("wer", "")), str(d.get("wen", ""))])
		"high_five":
			pass
		"fund":
			pass


# =======================================================================================================================
# hooks from abenteuer_zweit.gd
# =======================================================================================================================
func tick(dt: float) -> void:
	"""every frame (zweit._process)"""
	if z.mode == "allein" or ab.R.is_empty():
		return
	var rid := str(ab.R.get("id", ""))
	if rid != _run:
		_run = rid
		_log_n = (ab.R.get("log", []) as Array).size()
		_pe_sig = ""
		_ger_t = _rng.randf_range(100.0, 160.0)
		_leg_hold = {}
		if ab.R.get("zb") is Dictionary:
			zb.laden(ab.R["zb"])                  # (a resumed run)
		else:
			zb.neu()
		hoehe = [0.0, 0.0]
	_sync_t -= dt
	if _sync_t <= 0.0:
		_sync_t = 1.0
		_sync_inv()
	_pending_tick()
	_log_tick()
	_step_tick()
	if zb_aktiv():
		_noise_tick(dt)
		_ts_near()
	_save_t -= dt
	if _save_t <= 0.0:
		_save_t = 2.0
		ab.R["zb"] = zb.zustand()


func holds() -> bool:
	"""zweit.holds_leg: a team place or the rubber band at the end of a leg"""
	if z.mode == "allein" or not z.on:
		return false
	if zb.haelt():
		return true
	if z.mode == "rollen" or ab.leg.is_empty() or not z.race.is_empty():
		return false
	if float(ab.leg.get("f", 0.0)) < 0.92:
		return false
	var li := int(ab.leg.get("i", 0))
	var far := false
	for i in range(2):
		if (z.pl[i]["off"] as Vector2).length() > 60.0:
			far = true
	if not far:
		zb.wichtig_weg("etappe")
		return false
	if _leg_hold.is_empty() or int(_leg_hold["i"]) != li:
		_leg_hold = {"i": li, "t0": zb.now()}
		zb.say(-1, T.t("⏳ Das Etappenziel ist nah - kommt zur Gruppe!"), 4.0, 2)
	if zb.now() - float(_leg_hold["t0"]) > 60.0:
		zb.wichtig_weg("etappe")
		return false
	zb.wichtig("etappe", ab.R.get("pos", Vector2.ZERO), 45.0, T.t("Gruppe"), false, 60.0)
	return true


func tempo(i: int) -> float:
	return zb.tempo(i)


func on_leg(lg: Dictionary) -> void:
	"""a new leg: things to find beside the way, maybe a rock step (Räuberleiter)"""
	if z.mode == "allein" or ab.fast or ab.replaying or lg.is_empty() or ab.bt() == null:
		return
	var pts: Array = lg["pts"]
	var total := 0.0
	for k in range(pts.size() - 1):
		total += (pts[k] as Vector2).distance_to(pts[k + 1])
	if total < 30.0:
		return
	var li := int(lg.get("i", 0))
	var tag := "%s_%d_%d" % [str(ab.R.get("id", "")).right(6), li, (ab.R.get("walked", []) as Array).size()]
	_aufraeumen()
	var kinds: Array = [FUNDE[_rng.randi() % 3], FUNDE[3], FUNDE[4 + _rng.randi() % 3]]
	for k in range(kinds.size()):
		var e: Array = kinds[k]
		var q := _beside(pts, _rng.randf_range(0.15, 0.85), _rng.randf_range(8.0, 30.0))
		zb.fundstueck("%s_%s_%d" % [str(e[0]), tag, k], q, str(e[0]), T.t(str(e[1])))
	var nts := int(ab.R.get("zb_ts", 0))
	if z.mode in ["gemeinsam", "wettrennen"] and total > 120.0 and nts < 1:
		ab.R["zb_ts"] = nts + 1
		var q2 := _beside(pts, 0.5, 9.0)
		zb.teamstelle("ts_" + tag, q2, T.t("Felsstufe"), 2.6, zb.rolle_index("karte"))
		var ki: int = zb.rolle_index("karte")
		var tx := ["", ""]
		tx[ki] = T.t("🗺 Auf der Karte: eine Felsstufe am Weg - nur mit Räuberleiter. Führ %s hin!") % zb_name(1 - ki)
		zb.wissen("ts", tx)


func _aufraeumen() -> void:
	"""things far behind the tour go (at most a few legs are kept)"""
	var a: Vector2 = ab.R.get("pos", Vector2.ZERO)
	for id in zb._funde.keys():
		if (zb._funde[id]["pos"] as Vector2).distance_to(a) > 260.0:
			zb.fund_weg(id)
	for id in zb._ts.keys():
		if (zb._ts[id]["pos"] as Vector2).distance_to(a) > 200.0:
			zb.teamstelle_weg(id)
			zb.wissen_weg("ts")


func _beside(pts: Array, f: float, side: float) -> Vector2:
	var p: Vector2 = ab._along(pts, f)
	var p2: Vector2 = ab._along(pts, minf(1.0, f + 0.02))
	var d := (p2 - p).normalized()
	if d == Vector2.ZERO:
		d = Vector2(0, -1)
	var s := 1.0 if _rng.randf() < 0.5 else -1.0
	return z._clamp_valley(p + Vector2(-d.y, d.x) * side * s)


func _ts_near() -> void:
	"""the tour comes to the rock step: the team place starts (the tour waits there)"""
	var anchor: Vector2 = ab.R.get("pos", Vector2.ZERO)
	for id in zb._ts:
		var s: Dictionary = zb._ts[id]
		if not bool(s["aktiv"]) and str(s["phase"]) != "fertig" and anchor.distance_to(s["pos"]) < 35.0:
			zb.teamstelle_aktiv(id)
		if str(s["phase"]) == "fertig":
			zb.wissen_weg("ts")


func _sync_inv() -> void:
	var L: Array = []
	for e in Inv.liste():
		var id := str(e[0])
		L.append([id, T.t(Inv.name_of(id)) + ("" if int(e[1]) <= 1 else " ×%d" % int(e[1])), float(e[2]) * int(e[1])])
	zb.rucksack_setzen(L)


# ---- shared knowledge: the questions in the panel ---------------------------------------------------------------------
var _re_deg := RegEx.create_from_string("(\\d{1,3})\\s?°")
var _re_m := RegEx.create_from_string("(\\d{2,4})(\\s?)(Meter|meters|mètres|metri|meters|m\\b)")


func _pending_tick() -> void:
	var pe: Dictionary = ab.R.get("pending", {})
	var sig := "" if pe.is_empty() else str(pe.get("kind", "")) + str(pe.get("title", "")) + str(int(ab.R.get("stage", 0)))
	if sig == _pe_sig:
		return
	_pe_sig = sig
	zb.wissen_weg("raetsel")
	if pe.is_empty() or z.mode == "allein" or bool(pe.get("zb_geteilt", false)):
		return
	var ki: int = zb.rolle_index("karte")
	var si := 1 - ki
	var kind := str(pe.get("kind", ""))
	var tx := str(pe.get("text", ""))
	match kind:
		"a3_kompass", "a3_seite":
			var nums: Array = []
			for m in _re_deg.search_all(tx):
				nums.append(m.get_string(1) + "°")
			for m in _re_m.search_all(tx):
				nums.append(m.get_string(1) + " m")
			if nums.is_empty():
				return
			var hidden := _re_m.sub(_re_deg.sub(tx, "??°", true), "??$2$3", true)
			pe["text"] = hidden + "\n" + T.t("🧭 Die Zahlen der Peilung kennt nur %s - fragt nach!") % zb_name(si)
			pe["zb_geteilt"] = true
			var w := ["", ""]
			w[si] = T.t("🧭 Peilung: %s") % " · ".join(nums)
			w[ki] = T.t("🗺 Du hast die Karte. Frag %s nach der Peilung und such den Punkt.") % zb_name(si)
			zb.wissen("raetsel", w)
			ab._changed()
		"read":
			pe["text"] = T.t("Den Hinweis kennt nur %s (🧭). %s hat die Karte und wählt den Ort - sprecht euch ab!") % [zb_name(si), zb_name(ki)]
			pe["zb_geteilt"] = true
			var w2 := ["", ""]
			w2[si] = "🧭 " + tx
			w2[ki] = T.t("🗺 Welcher Ort auf der Karte passt zu dem, was %s sagt?") % zb_name(si)
			zb.wissen("raetsel", w2)
			ab._changed()


# ---- the diary of the tour: high fives, who found what ---------------------------------------------------------------
func _log_tick() -> void:
	var lg: Array = ab.R.get("log", [])
	if lg.size() <= _log_n:
		_log_n = mini(_log_n, lg.size())
		return
	for e in lg.slice(_log_n):
		var k := str(e.get("k", ""))
		var ti := str(e.get("title", ""))
		match k:
			"read":
				if ti == T.t("Karte gelesen"):
					zb.high_five("karte")
			"a3":
				if ti == T.t("Karte und Kompass"):
					zb.high_five("kompass")
			"a3_star":
				zb.high_five("stern")
			"a3_page":
				zb.zaehle(_near_group(), "tagebuch")
			"find":
				zb.zaehle(_near_group(), "funde")
	_log_n = lg.size()


func _near_group() -> int:
	"""who is nearer to the tour (gets the page / the find)"""
	if z.mode == "rollen":
		return 0
	var a: Vector2 = ab.R.get("pos", Vector2.ZERO)
	return 0 if (z.pl[0]["pos"] as Vector2).distance_to(a) <= (z.pl[1]["pos"] as Vector2).distance_to(a) else 1


func _noise_tick(dt: float) -> void:
	if int(ab.step) != 4 or z.mode == "rollen" or not z.race.is_empty() or not (ab.R.get("pending", {}) as Dictionary).is_empty():
		return
	_ger_t -= dt
	if _ger_t > 0.0:
		return
	var dark: bool = main.is_dark()
	_ger_t = _rng.randf_range(110.0, 200.0) if dark else _rng.randf_range(240.0, 420.0)
	var L := ["Ein Knacken im Wald!", "Da raschelt etwas!", "Ein Pfiff - was war das?", "Steine kullern den Hang hinunter!"]
	zb.geraeusch(T.t(str(L[_rng.randi() % L.size()])))


func _step_tick() -> void:
	var st := int(ab.step)
	if st == _step_last:
		return
	_step_last = st
	if st == 5 and z.mode != "allein":
		lager()


func lager() -> void:
	"""at the camp: the campfire question (options from the day)"""
	var ch := int(ab.R.get("chapter", 1))
	var frage := T.t(str(FRAGEN[(ch - 1) % FRAGEN.size()]))
	var opts: Array = []
	for e in (ab.R.get("log", []) as Array):
		var k := str(e.get("k", ""))
		if k == "zb" and not T.t("Die Räuberleiter") in opts and str(e.get("title", "")) == T.t("Räuberleiter"):
			opts.append(T.t("Die Räuberleiter"))
		elif k == "find" and opts.size() < 4:
			var tx := str(e.get("text", ""))
			if tx != "" and not tx in opts:
				opts.append(tx.left(40))
	for o in ["Die Aussicht", "Zusammen wandern", "Die Tiere", "Das Rätsel"]:
		if opts.size() >= 5:
			break
		var oo := T.t(o)
		if not oo in opts:
			opts.append(oo)
	zb.lagerfeuer_frage(frage, opts)
	ab.R["zb"] = zb.zustand()


func on_morning() -> void:
	"""the day goes into the travel diary (pictures of the day: the diary pictures of the adventure)"""
	if z.mode == "allein" or ab.R.is_empty():
		return
	var bilder: Array = []
	var dd: String = ab.DIR + "/tagebuch/" + str(ab.R.get("id", ""))
	var da := DirAccess.open(dd)
	if da != null:
		var fs: Array = []
		for f in da.get_files():
			if str(f).ends_with(".png"):
				fs.append(dd + "/" + str(f))
		fs.sort()
		var step_n := maxi(1, int(ceil(fs.size() / 4.0)))
		for k in range(0, fs.size(), step_n):
			bilder.append(fs[k])
	var ch: Dictionary = ab.chapter()
	_last_day = zb.tag_speichern("%s %d · %s" % [T.t("Kapitel"), int(ab.R.get("chapter", 1)), T.t(str(ch.get("title", "")))], bilder)


var _last_day := {}


# ---- panels ----------------------------------------------------------------------------------------------------------
func paint_choice(gg: Control) -> void:
	"""step «Schwierigkeit & Ziel», group «Mitspieler»: the roles and the buttons"""
	if z.mode == "allein":
		return
	gg.add_child(ab._lab(T.t("Rollen (jede ist wichtig):"), 14, Color.WHITE, false))
	for i in range(2):
		var r: Dictionary = zb.rolle(i)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		gg.add_child(row)
		var l: Label = ab._lab("%d · %s: %s %s - %s" % [i + 1, zb_name(i), str(r["icon"]), zb.rolle_name(i), T.t(str(r["text"]))], 13, z.COLS[i])
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(l)
		var ii := i
		var fb: Button = ab._btn(row, T.t("sie") if zb.titel_form(i) == "f" else T.t("er"), func(): zb.set_form(ii, "m" if zb.titel_form(ii) == "f" else "f"); ab._changed())
		fb.tooltip_text = T.t("Titel und Rolle als «er» oder «sie» (Späher / Späherin)")
	if z.mode != "rollen":
		ab._btn(gg, T.t("⇄ Rollen tauschen"), func(): zb.rollen_tauschen(); ab._changed())
	else:
		gg.add_child(ab._lab(T.t("In «Rollen» hat Spieler 2 die Karte (Kartenleser), Spieler 1 den Kompass."), 12, Color(0.65, 0.7, 0.78)))
	gg.add_child(ab._lab(T.t("Unterwegs zu zweit: 🎮 A = Team (Räuberleiter, Seil, High-Five) · B = weitergeben · X = Fähigkeit · Y = Foto · ◀ ▶ = Ding im Rucksack wählen. Tastatur: Spieler 1 F / G / R / T (V wählen), Spieler 2 N / M / P / , (. wählen)."), 12, Color(0.65, 0.7, 0.78)))


func paint_camp(body: Control) -> void:
	if z.mode == "allein" or ab.R.is_empty():
		return
	if zb._lf.is_empty():
		lager()
	zb.paint_lagerfeuer(body)
	zb.paint_fotowettbewerb(body)
	zb.paint_zwischenstand(body)


func paint_morning(body: Control) -> void:
	if z.mode == "allein":
		return
	zb.paint_auszeichnungen(body, _last_day)
	var hb := HFlowContainer.new()
	body.add_child(hb)
	zb.tagebuch_knopf(hb)


func paint_chapter(left: Control) -> void:
	zb.tagebuch_knopf(left)


# ---- control API -----------------------------------------------------------------------------------------------------
func op(d: Dictionary) -> Dictionary:
	var w := str(d.get("was", "state"))
	match w:
		"ts_hier":                                  # a rock step 8 m in front of player 1 (tests)
			var q: Vector2 = z.pl[0]["pos"] + Vector2(-sin(float(z.pl[0]["yaw"])), -cos(float(z.pl[0]["yaw"]))) * 8.0
			zb.teamstelle(str(d.get("id", "test")), q, T.t("Felsstufe"), 2.6, zb.rolle_index("karte"))
			zb.teamstelle_aktiv(str(d.get("id", "test")))
			return {"ok": true, "pos": [q.x, q.y], "zb": zb.state()}
		"funde_hier":
			var p: Vector2 = z.pl[0]["pos"]
			zb.fundstueck("t_funde", p + Vector2(7, 0), "funde", T.t("eine alte Münze"))
			zb.fundstueck("t_stein", p + Vector2(-20, 0), "steinmaennchen", T.t("ein Steinmännchen"))
			zb.fundstueck("t_spur", p + Vector2(0, 20), "spuren", T.t("eine Fuchsspur"))
			return {"ok": true, "zb": zb.state()}
		"lager":
			lager()
			return {"ok": true, "zb": zb.state()}
		"morgen":
			on_morning()
			return {"ok": true, "tag": _last_day, "zb": zb.state()}
		"hoehe":
			return {"ok": true, "hoehe": hoehe}
		"setzen":                                   # tests: player p to (x, z) in valley coordinates, view yaw
			var i := clampi(int(d.get("p", 1)) - 1, 0, 1)
			if d.has("x"):
				zb_setzen(i, Vector2(float(d["x"]), float(d["z"])))
			if d.has("yaw"):
				z.pl[i]["yaw"] = float(d["yaw"])
			return {"ok": true, "zb": zb.state()}
	var out: Dictionary = zb.op(d)
	out["hoehe"] = hoehe
	return out


func state() -> Dictionary:
	return zb.state()
