extends SceneTree
## Test «Roboter-Labor, Menü» (Besitzer, Fragebogen 28.11.2026 14:49: 5 Reiter statt 9, Gruppen, Suche – nichts entfernt,
## nur umsortiert). Ohne Bild. Geprüft:
##   · Kopf: «Roboter-Labor» in Orange, Versionsanzeige rechts = «Sim » + VERSION aus main.gd, gezeichnetes Logo
##   · Genau 5 Reiter (Fahren, Haltung, Bauen, Welt, Messen); die alten 9 Namen (/control «tab») führen in den neuen Reiter
##   · Auswahlliste «Modell» mit Bild je Eintrag; jede Variante aus VARIANTEN ist wählbar, die aktive ist ausgewählt
##   · JEDE frühere Bedienfunktion (Liste VORHER: Knöpfe, Schalter, Regler der 9 alten Reiter) ist in der neuen Struktur da,
##     mindestens so oft wie vorher, und erreichbar (ihr Reiter gewählt, ihre Gruppe offen → sichtbar)
##   · «Alle zuklappen · Nur Gruppen · Alle aufklappen» und das Suchfeld (Treffer aus allen Reitern, «Kein Treffer»)
##   · Kein Zeichen im Bedienfeld, das die Schrift nicht kann (leere Kästchen; ▾ ▸ der Simulator-Gruppen ausgenommen)
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_menue_test.gd"   (absoluter Pfad nötig)
## Ende: «Roboter-Menü-Test OK» oder «SCRIPT ERROR: Roboter-Menü-Test: …» (Exit-Code 0 / 1).

const T = preload("res://scripts/i18n.gd")
const BEW = preload("res://scripts/roboter_bewegung.gd")
const GEL = preload("res://scripts/roboter_gelaende.gd")
const MAIN_GD = preload("res://scripts/main.gd")
const L = preload("res://scripts/roboter_labor.gd")
const MODELL = preload("res://scripts/roboter_modell.gd")

# Die Bedienfunktionen VOR dem Umbau (9 Reiter, Stand main 28.11.2026 + sim-ring-oeffnen): [Text, Art, wie oft mindestens]
#   Art «=»: Text eines Knopfs / Schalters / Regler-Titels genau so; «~»: Text enthält es; «tip»: Tooltip genau so
const VORHER := [
	# Form
	["Segmente", "=", 1], ["Halbe Breite", "=", 1], ["Halbe Breite Spitze", "=", 1], ["Länge Mittelteil", "=", 1],
	["Abstand im Gelenk", "=", 1], ["Oberschenkel", "=", 1], ["Unterschenkel", "=", 1], ["Mast der Kamera", "=", 1],
	["Massstab (Meter pro Einheit)", "=", 1], ["Masse je Segment", "=", 1], ["Masse je Bein", "=", 1],
	["Startwerte (modell.json)", "=", 1],
	# Gelenke
	["Kamera schwenken", "=", 1], ["Riegel darf schliessen (Ring)", "=", 1], ["Segmentgelenk 1", "~", 1], ["Beine an Segment 1", "~", 1],
	# Posen
	["Sofort (ohne Weg)", "=", 1], ["Füsse seitlich", "=", 1], ["Neu aufstellen (R)", "=", 1],
	["Körperhöhe über dem Boden", "=", 2], ["Ring öffnen (gerade)", "=", 2],
	# Bewegen
	["Körper passt sich dem Untergrund an", "=", 1], ["Im Ring rollen (die Füsse stossen, Kurve = Ring neigen)", "=", 1],
	["Kurve (− rechts, + links)", "=", 1], ["Tempo", "=", 1], ["Spurbreite beim Gehen (Fuss links bis Fuss rechts)", "=", 1],
	["Schrittlänge", "=", 1], ["Schritthöhe", "=", 1],
	["vorne links", "tip", 1], ["Vorwärts", "tip", 1], ["vorne rechts", "tip", 1], ["seitwärts links", "tip", 1], ["Stopp", "tip", 1],
	["seitwärts rechts", "tip", 1], ["hinten links", "tip", 1], ["Rückwärts", "tip", 1], ["hinten rechts", "tip", 1],
	["an Ort drehen links", "~", 1], ["an Ort drehen rechts", "~", 1],
	# Anzeigen
	["Servo-Last an den Gelenken (grün bis rot)", "=", 1], ["Schwerpunkt und Stützfläche", "=", 1],
	# Rund rollen
	["Höhe über Boden (0 = auf den Ecken, mehr = auf Stelzen)", "=", 1], ["Spurbreite beim Rollen (Fuss links bis Fuss rechts)", "=", 1],
	["Im Ring rollen", "=", 1], ["Stopp", "=", 1], ["Messen (diese Methode)", "=", 1], ["Alle Methoden vergleichen", "=", 1],
	["Reihe Höhe (C)", "=", 1], ["Reihe Spurbreite (C)", "=", 1], ["Beste Methode als Standard übernehmen", "=", 1],
	# Gelände
	["Im Ring rollen statt gehen", "=", 1], ["Alle nacheinander", "=", 1], ["Abbrechen", "=", 1],
	# Physik
	["Schwerkraft", "=", 1], ["Servo-Moment Segmentgelenk", "=", 1], ["Servo-Moment Bein", "=", 1], ["Servo-Tempo", "=", 1],
	["Reibung am Boden", "=", 1], ["Physik anhalten (P)", "=", 1], ["Festhalten: mittleres Segment in der Luft (F)", "=", 1],
	# Ansicht
	["Kamerabild klein einblenden (K)", "=", 1], ["Info-Feld oben links einblenden (I)", "=", 1], ["Ansicht folgt dem Roboter", "=", 1],
	# Kopf
	["Schliessen (Esc)", "tip", 1],
]

var main
var lab
var errs := []
var step := 0
var t_start := 0.0
var t0 := 0.0


func _initialize() -> void:
	for f in ["user://roboter_labor.json", "user://roboter_steuerung.json"]:
		var p := ProjectSettings.globalize_path(f)
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	t_start = Time.get_ticks_msec() / 1000.0


func check(name: String, ok: bool, detail := "") -> void:
	print(("  ok   " if ok else "  FEHLER ") + name + ("" if detail == "" else "  (" + detail + ")"))
	if not ok:
		errs.append(name + ("" if detail == "" else " (" + detail + ")"))


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


static func vorher() -> Array:
	"""VORHER plus the lists that come from the constants (every pose, gait, sequence, ring method, terrain, view, variant)"""
	var out := VORHER.duplicate()
	for lst in [BEW.POSEN, BEW.GAENGE, BEW.ABLAEUFE, BEW.RING_METHODEN, GEL.NAMEN]:
		for e in lst:
			out.append([e[1], "=", 1])
	for v in [["Frei"], ["Seite"], ["Oben"], ["Roboter-Kamera"]]:
		out.append([v[0], "=", 1])                         # the group «Ansicht» (the bar in the view is outside the panel)
	return out


func controls(n: Node, out: Array) -> Array:
	if n is Control:
		out.append(n)
	for c in n.get_children():
		controls(c, out)
	return out


static func passt(c: Control, txt: String, art: String) -> bool:
	if art == "tip":
		return c.tooltip_text == txt
	var t := ""
	if c is Button:
		t = (c as Button).text
	elif c is Label:
		t = (c as Label).text
	else:
		return false
	return t.strip_edges() == txt if art == "=" else t.contains(txt)


func page_of(c: Node) -> String:
	var n := c
	while n != null:
		for tb in L.TABS:
			if lab._w.get("page_" + tb[0]) == n:
				return tb[0]
		n = n.get_parent()
	return ""


func _process(_dt: float) -> bool:
	if now() - t_start > 200.0:
		errs.append("Zeit abgelaufen in Schritt %d" % step)
		return _end()
	match step:
		0:
			if now() - t_start < 2.0:
				return false
			main.control({"action": "roboter", "do": "open", "variante": "8"})
			lab = main.roboter
			t0 = now()
			step = 1
		1:
			if now() - t0 < 1.5:
				return false
			# Kopf
			var ver: Label = lab._w.get("version")
			var soll: String = "Sim " + MAIN_GD.VERSION
			check("Versionsanzeige = «Sim » + VERSION (main.gd)", ver != null and ver.text == soll and ver.is_visible_in_tree(),
					"%s / %s" % [ver.text if ver != null else "-", soll])
			var tl: Label = lab._w.get("titel")
			check("Kopf «Roboter-Labor» in Orange wie die Kupplung", tl != null and tl.get_theme_color("font_color").is_equal_approx(Color("#ef9f27"))
					and L.AKZENT.is_equal_approx(MODELL.FARBE["kupplung"]))
			# Reiter
			check("5 Reiter: Fahren, Haltung, Bauen, Welt, Messen", L.TABS.map(func(x): return x[0]) == ["fahren", "haltung", "bauen", "welt", "messen"])
			var alt_ok := true
			var alt_det := []
			for alt in ["form", "gelenke", "posen", "bewegen", "anzeigen", "rund", "gelaende", "physik", "ansicht"]:
				lab.control({"do": "tab", "value": alt})
				var want: String = L.TAB_ALT[alt][0]
				var grp: Control = lab._gruppen.get(L.TAB_ALT[alt][1])
				if lab.tab != want or not (lab._w["page_" + want] as Control).visible or grp == null or not grp.is_visible_in_tree():
					alt_ok = false
					alt_det.append(alt)
			check("Alte Reiter-Namen führen in den neuen Reiter, ihre Gruppe offen", alt_ok, ", ".join(alt_det))
			# Modell
			var ob: OptionButton = lab._w.get("modell")
			var ids := []
			var pics := true
			for i in ob.item_count:
				if not ob.is_item_disabled(i):
					ids.append(str(ob.get_item_metadata(i)))
				pics = pics and ob.get_item_icon(i) != null
			var want_ids: Array = L.VARIANTEN.map(func(x): return x[0])
			var all_in := want_ids.all(func(v): return v in ids)
			check("Auswahlliste «Modell»: jede Variante wählbar, mit Bild, aktive ausgewählt", all_in and pics
					and str(ob.get_item_metadata(ob.selected)) == lab.variante, "%s / %s" % [ids, want_ids])
			# jede frühere Funktion da und erreichbar
			lab.fold_all("open")
			var cs := controls(lab._w["panel"], [])
			var fehlt := []
			var weg := []
			for e in vorher():
				var txt: String = T.t(e[0])
				var found := cs.filter(func(c): return passt(c, txt, e[1]))
				if found.size() < int(e[2]):
					fehlt.append("%s (%d/%d)" % [e[0], found.size(), e[2]])
					continue
				for c in found:
					var pg := page_of(c)
					if pg != "":
						lab.set_tab(pg)
					var ctl: Control = c
					if not ctl.is_visible_in_tree():
						weg.append(e[0])
						break
			check("Jede frühere Bedienfunktion ist im neuen Menü (%d Einträge)" % vorher().size(), fehlt.is_empty(), ", ".join(fehlt))
			check("… und erreichbar (Reiter gewählt, Gruppen offen → sichtbar)", weg.is_empty(), ", ".join(weg))
			# zuklappen / Nur Gruppen / aufklappen
			(lab._w["fold_close"] as Button).pressed.emit()
			var zu: bool = lab._gruppen.values().all(func(b): return not (b as Control).visible)
			(lab._w["fold_groups"] as Button).pressed.emit()
			var gr_auf: bool = lab._gruppen.values().all(func(b): return (b as Control).visible)
			var sub_zu: bool = lab._sub_folds(lab._gruppen["gelenke"]).all(func(b): return not (b.get_meta("fold") as Control).visible)
			(lab._w["fold_open"] as Button).pressed.emit()
			var sub_auf: bool = lab._sub_folds(lab._gruppen["gelenke"]).all(func(b): return (b.get_meta("fold") as Control).visible)
			check("Alle zuklappen · Nur Gruppen · Alle aufklappen", zu and gr_auf and sub_zu and sub_auf, "%s %s %s %s" % [zu, gr_auf, sub_zu, sub_auf])
			# Suche: über alle Reiter
			lab.set_tab("fahren")
			lab.fold_all("close")
			lab.suche(T.t("Reibung am Boden").to_lower())
			var hit: Control = null
			for c in controls(lab._w["panel"], []):
				if passt(c, T.t("Reibung am Boden"), "="):
					hit = c
			var other_hidden: bool = not (lab._gruppen["gang"].get_meta("card") as Control).visible
			check("Suche findet «Reibung am Boden» (Reiter Welt) vom Reiter Fahren aus", hit != null and hit.is_visible_in_tree() and other_hidden)
			lab.suche("zzzz-nichts")
			check("Suche ohne Treffer: «Kein Treffer»", (lab._w["kein_treffer"] as Control).visible)
			lab.suche("")
			check("Suche leer: alles wie vorher (nur der aktive Reiter)", not (lab._w["kein_treffer"] as Control).visible
					and (lab._w["page_fahren"] as Control).visible and not (lab._w["page_welt"] as Control).visible
					and (lab._gruppen["gang"].get_meta("card") as Control).visible)
			# Zeichen, die die Schrift nicht kann
			var f: Font = lab._w["panel"].get_theme_default_font()
			var miss := {}
			lab.fold_all("open")
			for c in controls(lab._w["panel"], []):
				var t := ""
				if c is Button:
					t = (c as Button).text
				elif c is Label:
					t = (c as Label).text
				for i in t.length():
					var ch := t.unicode_at(i)
					if ch > 32 and not t[i] in ["▾", "▸"] and not f.has_char(ch):
						miss[t[i]] = true
			check("Keine Zeichen, die die Schrift nicht kann (leere Kästchen)", miss.is_empty(), " ".join(miss.keys()))
			# Variante wechseln über die Liste
			for i in ob.item_count:
				if str(ob.get_item_metadata(i)) == "4":
					ob.select(i)
					ob.item_selected.emit(i)
			t0 = now()
			step = 2
		2:
			if now() - t0 < 1.5:
				return false
			lab = main.roboter
			var ob2: OptionButton = lab._w.get("modell")
			check("Modell «4 Segmente» aus der Liste gewählt", lab.variante == "4" and lab.model.n() == 4 and str(ob2.get_item_metadata(ob2.selected)) == "4",
					"%s / %d" % [lab.variante, lab.model.n()])
			main.roboter.control({"do": "close"})
			return _end()
	return false


func _end() -> bool:
	if errs.is_empty():
		print("Roboter-Menü-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Roboter-Menü-Test: " + " | ".join(errs))
		quit(1)
	return true
