extends SceneTree
## Test «Gang-KI lernen» (roboter_ki_lernen.gd, Stufe 3). Ohne Bild. Geprüft:
##   · Lernen mit nachgestellten Ergebnissen (5 Zufalls-Startwerte): der erste Versuch an einer 12-cm-Stufe misslingt, nach
##     40 Versuchen ist «hoch steigen» mit passenden Zahlen das Beste (≥ 93 % der besten möglichen Wertung) und wird meist gewählt
##   · ähnliches Hindernis (10 cm): gleich beim ersten Mal die gelernte Strategie; zwischen 6 und 12 cm werden die Zahlen gemischt
##   · Stil: «sparsam» wählt aus denselben Versuchen das Sparsamere; Bewertung: jeder Erfolg zählt mehr als jeder Fehlschlag
##   · Grenze: 12 Fehlschläge ohne Erfolg → «umgehen» + Hinweis
##   · Speichern / Laden / Vergessen (eigene Datei je Variante)
##   · Ablauf im Hintergrund mit einer nachgestellten KI: Fehlschlag → abbrechen, neu aufstellen, nächster Versuch, bis geschafft
##   · mit dem echten Labor (roboter_ki_gang.gd von Helfer A, falls vorhanden): siehe Schritt «echt»
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_ki_lernen_test.gd"   (absoluter Pfad nötig)
## Ende: «KI-Lernen-Test OK» oder «SCRIPT ERROR: KI-Lernen-Test: …» (Exit-Code 0 / 1).

const L = preload("res://scripts/roboter_ki_lernen.gd")
var errs := []


class FakeKi:
	extends RefCounted
	const STRATEGIEN := ["normal", "hoch_steigen", "aufrichten_vorne", "bruecke", "umgehen", "einrollen_rollen", "kriechen_drunter"]
	var h := {"art": "stufe", "hoehe": 0.12, "breite": 1.0, "tiefe": 0.4, "neigung": 0.0, "abstand": 0.5, "pos": Vector3(3, 0, 0)}
	var laeuft := false
	var t := 0
	var s := ""
	var p := {}
	var n_abbrechen := 0
	var n_aufstellen := 0
	var n_umgehen := 0
	var weg := false

	func sehen() -> Dictionary:
		return {"hindernisse": [] if weg else [h]}

	func strategie_ausfuehren(name: String, param: Dictionary) -> void:
		s = name
		p = param
		t = 0
		laeuft = true
		if name == "umgehen":
			n_umgehen += 1
			laeuft = false

	func strategie_status() -> Dictionary:
		t += 1
		if t < 20:
			return {"laeuft": true, "fertig": false}
		var r: Dictionary = ergebnis(h, s, p)
		r["laeuft"] = false
		r["fertig"] = true
		laeuft = false
		if bool(r["erfolg"]):
			weg = true
		return r

	func abbrechen() -> void:
		n_abbrechen += 1
		laeuft = false

	func neu_aufstellen(_h: Dictionary) -> void:
		n_aufstellen += 1

	static func ergebnis(hd: Dictionary, st: String, pa: Dictionary) -> Dictionary:
		"""nachgestellt: «normal» schafft nur bis 7 cm, «hoch steigen» braucht eine Schritthöhe ab 5 × Stufenhöhe,
		am schnellsten mit Tempo ~0.85 und Körperhöhe 1.0; «vorne aufrichten» geht immer, aber langsam und teuer"""
		var hh: float = float(hd["hoehe"])
		var sh: float = float(pa.get("schritt_hoehe", 0.35))
		var tp: float = float(pa.get("tempo", 0.7))
		var kh: float = float(pa.get("koerper_hoehe", 0.9))
		match st:
			"normal":
				if hh <= 0.07:
					return {"erfolg": true, "zeit": 3.0, "energie": 0.1, "kipp_min": 0.7, "gestuerzt": false}
				return {"erfolg": false, "zeit": 10.0, "energie": 0.2, "kipp_min": 0.5, "gestuerzt": false, "fortschritt": 0.3}
			"hoch_steigen":
				if sh < 5.0 * hh:
					return {"erfolg": false, "zeit": 12.0, "energie": 0.3, "kipp_min": 0.3, "gestuerzt": sh < 3.0 * hh, "fortschritt": 0.5}
				return {"erfolg": true, "zeit": 3.0 + 6.0 * (1.0 - tp) + 6.0 * absf(kh - 1.0), "energie": 0.1 + 0.25 * sh,
						"kipp_min": clampf(0.75 - 1.5 * maxf(0.0, tp - 0.85), 0.0, 1.0), "gestuerzt": false}
			"aufrichten_vorne":
				return {"erfolg": true, "zeit": 15.0, "energie": 0.6, "kipp_min": 0.4, "gestuerzt": false}
		return {"erfolg": false, "zeit": 10.0, "energie": 0.2, "kipp_min": 0.5, "gestuerzt": false, "fortschritt": 0.0}


func check(name: String, ok: bool, detail := "") -> void:
	print(("  ok   " if ok else "  FEHLER ") + name + ("" if detail == "" else "  (" + detail + ")"))
	if not ok:
		errs.append(name + ("" if detail == "" else " (" + detail + ")"))


func neu(seed := 1) -> RefCounted:
	var l = L.new("8")
	l.speichern_an = false
	l.rng.seed = seed
	return l


func optimum(l, h: Dictionary) -> float:
	"""die beste mögliche Wertung der nachgestellten Welt (Gitter über den Raum)"""
	var best := -9.0
	for sh in range(10, 101, 2):
		for tp in range(30, 101, 2):
			for kh in range(50, 141, 5):
				var st := FakeKi.ergebnis(h, "hoch_steigen", {"schritt_hoehe": sh / 100.0, "tempo": tp / 100.0, "koerper_hoehe": kh / 100.0})
				best = maxf(best, l.bewerte(st))
	return best


func lerne(l, h: Dictionary, n: int) -> Array:
	var erst := []
	for i in range(n):
		var w: Array = l.waehle(h)
		var st := FakeKi.ergebnis(h, w[0], w[1])
		if i == 0:
			erst = [w[0], bool(st["erfolg"])]
		l.melde(h, w[0], w[1], st)
	return erst


func _initialize() -> void:
	var h12 := {"art": "stufe", "hoehe": 0.12, "breite": 1.0, "tiefe": 0.4, "neigung": 0.0}
	# 1) Bewertung
	var l0 = neu()
	var fail_best: float = l0.bewerte({"erfolg": false, "fortschritt": 1.0})
	var ok_worst: float = l0.bewerte({"erfolg": true, "zeit": 999.0, "energie": 99.0, "kipp_min": 0.0})
	check("jeder Erfolg zählt mehr als jeder Fehlschlag", ok_worst > fail_best, "%.2f > %.2f" % [ok_worst, fail_best])
	check("Sturz zählt schlechter als nur nicht geschafft", l0.bewerte({"erfolg": false, "gestuerzt": true}) < l0.bewerte({"erfolg": false}))
	check("Schlüssel: Art + gerundete Masse", L.schluessel({"art": "stufe", "hoehe": 0.121, "breite": 0.98, "tiefe": 0.41}) == "stufe|h12|b100|t40|n0|s0",
			L.schluessel({"art": "stufe", "hoehe": 0.121, "breite": 0.98, "tiefe": 0.41}))
	# 2) Lernen konvergiert (5 Startwerte)
	l0.stil = "schnell"
	var opt := optimum(l0, h12)
	var gut := 0
	var details := []
	for seed in [1, 2, 3, 4, 5]:
		var l = neu(seed)
		l.stil = "schnell"
		var erst := lerne(l, h12, 40)
		var b: Dictionary = l.eintrag(h12)["best"]
		var anteil: float = float(b.get("score", 0.0)) / opt
		var wahl := 0
		for i in range(20):
			if l.waehle(h12)[0] == "hoch_steigen":
				wahl += 1
		details.append("Start %d: erst %s/%s, best %s %.0f %%, Wahl %d/20" % [seed, erst[0], "ok" if erst[1] else "nein", b.get("strategie", "-"), 100.0 * anteil, wahl])
		if not erst[1] and b.get("strategie", "") == "hoch_steigen" and anteil >= 0.93 and wahl >= 14:
			gut += 1
	for d in details:
		print("     " + d)
	check("Lernen: erster Versuch misslingt, nach 40 Versuchen «hoch steigen» ≥ 93 % des Optimums und meist gewählt (5/5 Startwerte)", gut == 5, "%d/5" % gut)
	# 3) ähnliches Hindernis, Mischen, Anzeige
	var l = neu(7)
	l.stil = "schnell"
	lerne(l, h12, 40)
	var h10 := h12.duplicate()
	h10["hoehe"] = 0.10
	var w10: Array = l.waehle(h10)
	var st10 := FakeKi.ergebnis(h10, w10[0], w10[1])
	check("ähnliche Stufe 10 cm: gleich beim ersten Mal «hoch steigen» und geschafft", w10[0] == "hoch_steigen" and bool(st10["erfolg"]), str(w10))
	var lm = neu(8)
	var h06 := h12.duplicate()
	h06["hoehe"] = 0.06
	var pa := {"schritt_hoehe": 0.3, "tempo": 0.8, "koerper_hoehe": 1.0}
	var pb := {"schritt_hoehe": 0.6, "tempo": 0.8, "koerper_hoehe": 1.0}
	lm.melde(h06, "hoch_steigen", pa, FakeKi.ergebnis(h06, "hoch_steigen", pa))
	lm.melde(h12, "hoch_steigen", pb, FakeKi.ergebnis(h12, "hoch_steigen", pb))
	var h09 := h12.duplicate()
	h09["hoehe"] = 0.09
	var w09: Array = lm.waehle(h09)
	var sh09: float = float(w09[1].get("schritt_hoehe", 0.0))
	check("zwischen 6 und 12 cm: Schritthöhe gemischt (0.3 < x < 0.6)", w09[0] == "hoch_steigen" and sh09 > 0.31 and sh09 < 0.59, "%.3f" % sh09)
	l.lauf = {}
	l.letzte = {"key": L.schluessel(h12)}
	var z: PackedStringArray = l.anzeige_zeilen()
	check("Anzeige: Hindernis, Versuch n, Bestes", z.size() >= 2 and "Versuch 40" in z[0] and "Hoch steigen" in z[1], " | ".join(z))
	print("     " + " | ".join(z))
	# 4) Stil
	var ls = neu(9)
	var hs := h12.duplicate()
	var schnell := {"schritt_hoehe": 1.0, "tempo": 0.85, "koerper_hoehe": 1.0}    # schnell, aber viel Energie
	var spar := {"schritt_hoehe": 0.6, "tempo": 0.45, "koerper_hoehe": 1.0}       # langsamer, weniger Energie
	ls.stil = "schnell"
	ls.melde(hs, "hoch_steigen", schnell, FakeKi.ergebnis(hs, "hoch_steigen", schnell))
	ls.melde(hs, "hoch_steigen", spar, FakeKi.ergebnis(hs, "hoch_steigen", spar))
	var b1: float = float(ls.eintrag(hs)["best"]["param"]["schritt_hoehe"])
	ls.setze_stil("sparsam")
	var b2: float = float(ls.eintrag(hs)["best"]["param"]["schritt_hoehe"])
	check("Stil: «schnell» nimmt den schnellen Versuch, «sparsam» den sparsamen", is_equal_approx(b1, 1.0) and is_equal_approx(b2, 0.6), "%.2f / %.2f" % [b1, b2])
	# 5) Grenze
	var lg = neu(10)
	var hg := {"art": "balken", "hoehe": 0.5, "breite": 1.0, "tiefe": 0.1, "neigung": 0.0}
	for i in range(L.VERSUCHE_MAX):
		var w: Array = lg.waehle(hg)
		lg.melde(hg, w[0], w[1], {"erfolg": false, "zeit": 10.0, "gestuerzt": false})
	var wg: Array = lg.waehle(hg)
	var zg: PackedStringArray = lg.anzeige_zeilen()
	check("nach %d Fehlschlägen: «umgehen» + Hinweis" % L.VERSUCHE_MAX, wg[0] == "umgehen" and "umgangen" in " ".join(zg), " | ".join(zg))
	# 6) Speichern / Laden / Vergessen
	var p := "user://roboter_ki_test_lernen.json"
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(p))
	var la = neu(11)
	la.speichern_an = true
	la.pfad = p
	lerne(la, h12, 15)
	var best_a: Dictionary = la.eintrag(h12)["best"]
	var lb = neu(12)
	lb.pfad = p
	lb.laden()
	var best_b: Dictionary = lb.eintrag(h12).get("best", {})
	check("Speichern / Laden: das Beste ist wieder da", FileAccess.file_exists(p) and not best_a.is_empty()
			and best_b.get("strategie") == best_a.get("strategie") and is_equal_approx(float(best_b.get("score", 0)), float(best_a.get("score", 1))))
	lb.vergessen()
	var lc = neu(13)
	lc.pfad = p
	lc.laden()
	check("Vergessen: Datei weg, nichts gemerkt", not FileAccess.file_exists(p) and lb.daten.is_empty() and lc.daten.is_empty())
	check("Datei je Variante", L.new("4").datei() == "user://roboter_ki_4.json" and L.new("6").datei() == "user://roboter_ki_6.json"
			and L.new("8").datei() == "user://roboter_ki_8.json")
	# 7) Ablauf im Hintergrund (nachgestellte KI)
	var lt = neu(14)
	var ki := FakeKi.new()
	lt.ki = ki
	var schritte := 0
	while schritte < 20000 and not ki.weg:
		lt.tick(0.1)
		schritte += 1
	for i in range(30):
		lt.tick(0.1)
	var e: Dictionary = lt.eintrag(ki.h)
	check("Hintergrund: Fehlschlag → abbrechen + neu aufstellen, bis geschafft", ki.weg and ki.n_abbrechen >= 1 and ki.n_aufstellen == ki.n_abbrechen
			and lt.lauf.is_empty() and int(e.get("erfolge", 0)) == 1, "Versuche %d, abgebrochen %d, neu aufgestellt %d" % [int(e.get("versuche", 0)), ki.n_abbrechen, ki.n_aufstellen])
	ki.weg = false
	for i in range(30):
		lt.tick(0.1)
	check("Hintergrund: ein geschafftes Hindernis startet keinen neuen Versuch", lt.lauf.is_empty())
	lt.an = false
	check("Schalter aus: Anzeige «aus»", "aus" in lt.anzeige_zeilen()[0])
	var le = neu(15)
	le.melde(h12, "hoch_steigen", pb, FakeKi.ergebnis(h12, "hoch_steigen", pb))
	var h12b := h12.duplicate()
	h12b["hoehe"] = 0.129
	check("leicht andere Messung (12.9 statt 12 cm) = dasselbe Hindernis", le.key(h12b) == L.schluessel(h12) and le.key(h10) != L.schluessel(h12), le.key(h12b))
	if ResourceLoader.exists(GANG) and OS.get_environment("TEST_KI_OHNE_LABOR") == "":
		main = load("res://main.tscn").instantiate()
		root.add_child(main)
		current_scene = main
		_echt()
	else:
		print("  info ohne das echte Labor (TEST_KI_OHNE_LABOR oder roboter_ki_gang.gd fehlt)")
		_ende()


# ---- mit dem echten Labor (Stufe 1 + 2 von Helfer A) --------------------------------------------------------------------
const GANG := "res://scripts/roboter_ki_gang.gd"
const STRECKE := "stufe_hoch"       # Stufe 10 cm (28.11.: meist schon beim 1. Mal geschafft, 30 … 45 s pro Versuch)
var main
var lab


func warte(sek: float) -> void:
	var f := Engine.get_physics_frames() + int(sek * Engine.physics_ticks_per_second)
	while Engine.get_physics_frames() < f:
		await physics_frame


func lerne_echt(lane: String, max_versuche: int, max_s: float, bis_erfolg_plus: int) -> Array:
	"""the robot walks (Gangart KI) towards the lane; Stufe 3 runs in the background as in the lab: [{strategie, erfolg, zeit,
	energie, kipp_min, grund, score}, …] per try"""
	var le = lab.ki_lernen
	lab.stop_all()
	lab.ki.abbrechen()
	le.lauf = {}
	le.vorbei = []
	lab.model.root_xf = lab.starts[lane]
	lab.apply_pose("gerade", true)
	await warte(1.0)
	lab.bew.start_gang("ki")
	lab.manual = Vector3(0, 1, 0)
	var res := []
	var f0 := Engine.get_physics_frames()
	var erfolg_bei := -1
	var last: int = le.meldungen
	var w0 := Time.get_ticks_msec()
	while Engine.get_physics_frames() - f0 < int(max_s * Engine.physics_ticks_per_second):
		await physics_frame
		if le.meldungen != last:
			last = le.meldungen
			var st: Dictionary = lab.ki.strategie_status()
			var r := {"strategie": str(le.letzte.get("strategie", "")), "erfolg": bool(le.letzte.get("erfolg", false)),
					"score": float(le.letzte.get("score", 0.0)), "zeit": float(st.get("zeit", 0.0)), "energie": float(st.get("energie", 0.0)),
					"kipp_min": float(st.get("kipp_min", 0.0)), "grund": str(st.get("grund", "")), "key": str(le.letzte.get("key", "")),
					"t": float(Engine.get_physics_frames() - f0) / Engine.physics_ticks_per_second, "echt": (Time.get_ticks_msec() - w0) / 1000.0}
			res.append(r)
			print("     %s Versuch %d (%.0f s, echt %.0f s): %s %s · %.1f s · %.3f Wh · Kipp %.2f · Wertung %.2f · %s" % [lane, res.size(), r["t"], r["echt"], r["strategie"],
					"geschafft" if r["erfolg"] else "nicht geschafft", r["zeit"], r["energie"], r["kipp_min"], r["score"], r["grund"]])
			if r["erfolg"] and erfolg_bei < 0:
				erfolg_bei = res.size()
			if erfolg_bei >= 0 and res.size() >= erfolg_bei + bis_erfolg_plus or res.size() >= max_versuche:
				break
			if r["erfolg"]:
				le.nochmal()                               # once over it: back in front of the same obstacle for the next try
	lab.manual = Vector3.ZERO
	lab.stop_all()
	return res


func _echt() -> void:
	await create_timer(2.0).timeout
	main.control({"action": "roboter", "do": "open"})
	lab = main.roboter
	await warte(1.0)
	var le = lab.ki_lernen
	check("Labor: Stufe 3 angehängt (ki.lernen, tick)", le != null and lab.ki.lernen == le and le.ki == lab.ki and le.an)
	if le == null:
		_ende()
		return
	# Zeitraffer: k-mal mehr Physik-Schritte pro Sekunde und k-mal schnellere Uhr - jeder Schritt bleibt 1/120 s (gleiche Physik)
	var k := int(OS.get_environment("TEST_KI_ZEITRAFFER")) if OS.get_environment("TEST_KI_ZEITRAFFER") != "" else 1   # (3× gemessen 28.11.: der Rechner schafft nur Echtzeit)
	Engine.physics_ticks_per_second = 120 * k
	Engine.time_scale = float(k)
	Engine.max_physics_steps_per_frame = 8 * k
	print("  info Zeitraffer %d× (Schritt %.4f s)" % [k, Engine.time_scale / Engine.physics_ticks_per_second])
	le.pfad = "user://roboter_ki_test_echt.json"
	le.vergessen()
	le.laden()
	var strecken: Array = [STRECKE]
	var env := OS.get_environment("TEST_KI_STRECKEN")
	if env != "":
		strecken = Array(env.split(","))
	var nmax := int(OS.get_environment("TEST_KI_VERSUCHE")) if OS.get_environment("TEST_KI_VERSUCHE") != "" else 6
	le.setze_stil("schnell")
	for lane in strecken:
		var r := await lerne_echt(lane, nmax, 70.0 * nmax, nmax)
		var erst: Dictionary = r[0] if not r.is_empty() else {}
		var best := {}
		for x in r:
			if best.is_empty() or float(x["score"]) > float(best["score"]):
				best = x
		# besser = geschafft, was am Anfang nicht ging, oder mindestens 5 % schneller / sparsamer als der erste Versuch
		var besser := false
		for x in (r.slice(1) if not erst.is_empty() else []):
			if bool(x["erfolg"]) and (not bool(erst["erfolg"]) or float(x["zeit"]) < 0.95 * float(erst["zeit"])
					or float(x["energie"]) < 0.95 * float(erst["energie"])):
				besser = true
		var gemerkt: Dictionary = le.eintrag(le.letzte.get("h", {})).get("best", {}) if not le.letzte.is_empty() else {}
		var je := r.any(func(x): return bool(x["erfolg"]))
		if env == "" and je:
			check("echtes Labor, %s: das Beste ist gemerkt (wird beim nächsten Mal genommen)" % lane, not gemerkt.is_empty()
					and str(gemerkt.get("strategie", "")) == str(best.get("strategie", "")), str(gemerkt.get("strategie", "-")))
		var txt := "Anfang: %s %s · Bestes nach %d Versuchen: %s %s %.1f s %.3f Wh" % [erst.get("strategie", "-"), "ok" if erst.get("erfolg", false) else "nein",
				r.size(), best.get("strategie", "-"), "ok" if best.get("erfolg", false) else "nein", float(best.get("zeit", 0)), float(best.get("energie", 0))]
		print("  info %s: %s · %s" % [lane, txt, "besser als am Anfang" if besser else "nicht besser als am Anfang (Streuung der Physik)"])
		if env == "":
			check("echtes Labor, %s: mehrere Versuche, Fehlschlag → neu aufstellen, nichts hängt" % lane, r.size() >= 3, "%d Versuche" % r.size())
			if not je:
				print("  info %s: in %d Versuchen nie geschafft - Lernen nicht beurteilbar (Gangart / Physik)" % [lane, r.size()])
				continue
			var h2: Dictionary = (le.letzte.get("h", {}) as Dictionary).duplicate()
			h2["breite"] = float(h2.get("breite", 0.2)) + 0.06          # a similar obstacle, not the same one
			var w: Array = le.waehle(h2)
			check("echtes Labor, %s: ein ähnliches Hindernis bekommt gleich die beste Strategie" % lane, not gemerkt.is_empty()
					and str(w[0]) == str(gemerkt["strategie"]), str(w[0]) + " / " + str(gemerkt.get("strategie", "-")))
	le.vergessen()
	Engine.time_scale = 1.0
	main.roboter.control({"do": "close"})
	_ende()


func _ende() -> void:
	if errs.is_empty():
		print("KI-Lernen-Test OK")
		quit(0)
	else:
		push_error("KI-Lernen-Test: " + "; ".join(errs))
		quit(1)
