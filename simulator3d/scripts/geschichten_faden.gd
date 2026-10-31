extends Node
## Roter Faden zwischen den Geschichten (Daniel, 31.10.2026): kleine Querverweise zwischen «Die Karte des Grossvaters»
## (Bergtal-Abenteuer, bergtal_abenteuer.gd + abenteuer_figuren.gd) und «Maggie und der Bergkristall» (maggie_story.gd).
## Beide spielen im Bergtal. Das Hospiz (Horror-Geschichte) wird NICHT verbunden.
## Regeln: nur kleine, freiwillige Details (Grüsse, eine Kerze, eine Tagebuchzeile, ein Abzeichen) - jede Geschichte bleibt
## allein spielbar, Handlung und Rätsel bleiben gleich. Nichts Neues über den Grossvater (deshalb KEINE Zeile in seinem
## Tagebuch: die Beobachtung an der Bergkapelle steht im eigenen Tour-Tagebuch).
##
## Die Querverweise:
##   Maggie-Seite (dieser Knoten läuft als Modul der Maggie-Geschichte, maggie_story.gd MODULES):
##     1. Herbst: Ruedi, der Wildhüter, steht beim ersten Rastplatz und grüsst («Ah, ihr zwei seid das …»).
##     2. … hat das Kind die Karte schon begonnen (gleicher Spielstand), erwähnt er den Enkel mit der alten Karte.
##     3. Sommer: Maggie riecht Vrenis Alpkäse von der Alp Tschuggen.
##     4. Finale: ist die Karte geschafft, liegt in der Bergkapelle ein Wanderbuch mit dem Eintrag des Enkels.
##   Karte-Seite (Einhänge-Punkte in abenteuer_figuren.gd start_talk, bergtal_abenteuer.gd _karte_update,
##   bergtal_abenteuer_karte.gd _symbol):
##     5. Anna, die Hüttenwartin, erzählt (einmal) von einem Kind mit einem kleinen, hellen Terrier.
##     6. Sepp, der Älpler: ein kleiner heller Hund hat seine Ziegen angebellt (einmal).
##     7. Ruedi, der Wildhüter: der Terrier mit der guten Nase (einmal).
##        (5–7 nur, wenn Maggie in diesem Spielstand begonnen ist.)
##     8. Tour-Tagebuch beim Tschingelspitz: die kleine Bergkapelle - drinnen leuchtet der Kristall, wenn Maggie geschafft ist.
##     9. Die Bergkapelle steht nach dem Ende der Karte auf der alten Karte; die Kerze brennt, wenn Maggie geschafft ist
##        (erst nach dem Ende, damit sie das Peilungs-Rätsel von Kapitel 5 nicht verrät).
##   Beide:
##    10. Abzeichen «Beide Geschichten geschafft» (🕯) im Spielbereich (spielbereich.gd badges(), zählt fürs Level).
## Spielstand: pro Platz (spielstand.gd) die Datei user://spielstand/<n>/faden.json {"maggie_begonnen", "maggie_fertig"} -
##   Maggie speichert pro Spielstand (spielstand.gd path_maggie, Platz 1 = user://maggie/spielstand.json); stand() liest
##   faden.json und zusätzlich Maggies Datei dieses Platzes (intro / finale). Dieser Knoten merkt, in welchem
##   Platz Maggie gespielt / geschafft wurde. Platz 1 ohne faden.json: Maggies alte Datei gilt (wie spielstand.gd: Platz 1 =
##   die bisherigen Dateien). Die Karte ist schon pro Platz (main.abenteuer.P: finale, runs, chapter).
## Test: Faden.info(main) gibt den Stand zurück (kein eigener Steuerbefehl - absichtlich klein).

const T = preload("res://scripts/i18n.gd")
const SS = preload("res://scripts/spielstand.gd")

const MAGGIE_SAVE := "user://maggie/spielstand.json"     # (= maggie_story.gd SAVE_FILE)
const KAPELLE := Vector2(-832, 512)                       # Bergkapelle (= maggie_welt.gd CHAPEL, Tal-Koordinaten)
const KAPELLE_R := 130.0                                  # so nah kommt die Tour (Kapitel 5 über den Tschingelspitz)

static var _st := {}
static var _st_slot := -1
static var _st_t := -1e9


# =======================================================================================================================
# the state per Spielstand
# =======================================================================================================================
static func _path(n: int) -> String:
	return SS.dir_of(n) + "/faden.json"


static func stand(n := -1) -> Dictionary:
	"""{maggie_begonnen, maggie_fertig} of the place n (read at most every 3 s)"""
	n = SS.slot() if n < 1 else n
	var now := Time.get_ticks_msec() / 1000.0
	if n == _st_slot and now - _st_t < 3.0:
		return _st
	var d := {"maggie_begonnen": false, "maggie_fertig": false}
	var p := _path(n)
	if FileAccess.file_exists(p):
		var j = JSON.parse_string(FileAccess.get_file_as_string(p))
		if j is Dictionary:
			for k in d:
				d[k] = bool(j.get(k, false))
	var mp := SS.path_maggie(n)                         # Maggie speichert pro Spielstand (Geschichten-Menü, spielstand.gd path_maggie)
	if FileAccess.file_exists(mp):
		var m = JSON.parse_string(FileAccess.get_file_as_string(mp))
		if m is Dictionary:
			d["maggie_begonnen"] = d["maggie_begonnen"] or bool(m.get("intro", false))
			d["maggie_fertig"] = d["maggie_fertig"] or bool(m.get("finale", false))
	_st = d
	_st_slot = n
	_st_t = now
	return d


static func _merken(k: String) -> void:
	var d := stand().duplicate()
	if bool(d.get(k, false)):
		return
	d[k] = true
	if k == "maggie_fertig":
		d["maggie_begonnen"] = true
	DirAccess.make_dir_recursive_absolute(SS.dir_of(SS.slot()))
	var f := FileAccess.open(_path(SS.slot()), FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))
		f.close()
	_st_t = -1e9


static func maggie_begonnen() -> bool:
	return bool(stand()["maggie_begonnen"])


static func maggie_fertig() -> bool:
	return bool(stand()["maggie_fertig"])


static func _P(main) -> Dictionary:
	return main.abenteuer.P if main != null and main.get("abenteuer") != null and main.abenteuer.P is Dictionary else {}


static func karte_begonnen(main) -> bool:
	var p := _P(main)
	return not (p.get("runs", []) as Array).is_empty() or int(p.get("chapter", 1)) > 1 or bool(p.get("finale", false))


static func karte_fertig(main) -> bool:
	return bool(_P(main).get("finale", false))


static func info(main) -> Dictionary:
	var s := stand()
	return {"slot": SS.slot(), "maggie_begonnen": s["maggie_begonnen"], "maggie_fertig": s["maggie_fertig"],
			"karte_begonnen": karte_begonnen(main), "karte_fertig": karte_fertig(main)}


# =======================================================================================================================
# hooks of the «Karte» side
# =======================================================================================================================
static func gruss(fig, fid: String, f: Dictionary) -> String:
	"""abenteuer_figuren.gd start_talk: an extra line of Anna / Sepp / Ruedi (once per figure, only after Maggie began)"""
	if not fid in ["huettenwartin", "aelpler", "wildhueter"] or not maggie_begonnen():
		return ""
	var fl = f.get("flags", null)
	if not fl is Dictionary or (fl as Dictionary).has("faden_maggie"):
		return ""
	fl["faden_maggie"] = true
	match fid:
		"huettenwartin":
			return "\n" + T.t("Übrigens: Neulich war ein Kind mit einem kleinen, hellen Terrier bei der Hütte. Die zwei wollten hinauf zum Tschingelspitz.")
		"aelpler":
			return "\n" + T.t("Stell dir vor: Ein kleiner heller Hund hat neulich meine Ziegen angebellt – ganz frech, aber lieb. Ein Kind war bei ihm.")
		_:
			return "\n" + T.t("Hast du den kleinen Terrier gesehen, der mit einem Kind durchs Tal zieht? Eine Nase hat der – der findet alles.")


static func karte(ab) -> void:
	"""bergtal_abenteuer.gd _karte_update: the chapel on the old map (after the end) and a line in the tour diary"""
	var k = ab.karte
	if k != null and bool(ab.P.get("finale", false)):
		k.symbols.append(["kapelle_kerze" if maggie_fertig() else "kapelle", KAPELLE])
	var R: Dictionary = ab.R
	if R.is_empty() or bool(R.get("faden_kapelle", false)) or not R.has("log"):
		return
	var near := false
	var pos = R.get("pos", null)
	if pos is Vector2 and (pos as Vector2).distance_to(KAPELLE) < KAPELLE_R:
		near = true
	for q in R.get("walked", []):
		if q is Vector2 and (q as Vector2).distance_to(KAPELLE) < KAPELLE_R:
			near = true
			break
	if not near:
		return
	R["faden_kapelle"] = true
	if maggie_fertig():
		ab._diary("faden", T.t("Bergkapelle"), T.t("Neben dem Tschingelspitz steht eine kleine Bergkapelle. Drinnen leuchtet etwas auf dem Stein vor dem Altar – wie ein Kristall."))
	else:
		ab._diary("faden", T.t("Bergkapelle"), T.t("Neben dem Tschingelspitz steht eine kleine Bergkapelle. Die Tür ist zu, drinnen ist es still."))


static func zeichne_kapelle(c: CanvasItem, p: Vector2, kerze: bool) -> void:
	"""bergtal_abenteuer_karte.gd _symbol: the small chapel in ink, the candle in the door if Maggie is done"""
	var ink := Color(0.33, 0.2, 0.1)
	c.draw_rect(Rect2(p + Vector2(-6, -3), Vector2(12, 10)), ink, false, 1.5)
	c.draw_polyline(PackedVector2Array([p + Vector2(-8, -2), p + Vector2(0, -10), p + Vector2(8, -2)]), ink, 1.5)
	c.draw_line(p + Vector2(0, -10), p + Vector2(0, -16), ink, 1.5)
	c.draw_line(p + Vector2(-2.5, -13.5), p + Vector2(2.5, -13.5), ink, 1.5)
	if kerze:
		c.draw_circle(p + Vector2(0, 1), 3.2, Color(1.0, 0.75, 0.2, 0.45))
		c.draw_circle(p + Vector2(0, 1), 1.6, Color(1.0, 0.6, 0.1))
		c.draw_line(p + Vector2(0, 3), p + Vector2(0, 6), Color(0.95, 0.92, 0.8), 1.5)
	c.draw_string(ThemeDB.fallback_font, p + Vector2(10, 4), T.t("Bergkapelle"), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(ink, 0.85))


# =======================================================================================================================
# the badge (spielbereich.gd badges())
# =======================================================================================================================
static func abzeichen(main) -> Array:
	var both := maggie_fertig() and karte_fertig(main)
	return [{"id": "faden_beide", "sym": "🕯", "name": T.t("Beide Geschichten geschafft"), "n": 1 if both else 0, "kind": "faden"}]


# =======================================================================================================================
# the Maggie side: a module of maggie_story.gd (main and story are set before it is added)
# =======================================================================================================================
var main
var story
var ruedi: Node3D = null
var _gruss_ok := false
var _kaese_t := -1.0
var _buch_ok := false
var _abz_ok := false
var _t := 0.0


func _ready() -> void:
	if story == null:
		return
	for sg in [["region_gestartet", "_on_region"], ["region_beendet", "_on_ende"], ["geschichte_beendet", "_on_ende_alles"]]:
		if story.has_signal(sg[0]) and not story.is_connected(sg[0], Callable(self, sg[1])):
			story.connect(sg[0], Callable(self, sg[1]))
	_abz_ok = maggie_fertig() and karte_fertig(main)


func _on_region(id: String) -> void:
	_weg()
	_gruss_ok = false
	_kaese_t = main.now() + 40.0 if id == "sommer" else -1.0
	if id == "herbst":
		_ruedi_bauen()


func _on_ende(_id := "") -> void:
	_weg()
	_kaese_t = -1.0


func _on_ende_alles() -> void:
	_on_ende()


func _weg() -> void:
	if ruedi != null and is_instance_valid(ruedi):
		ruedi.queue_free()
	ruedi = null


func _ruedi_bauen() -> void:
	"""Ruedi stands a few metres beside the first resting place (a puppet: never part of a MoveEye test)"""
	var mm = main.get("menschen")
	if mm != null:
		mm._next_look = {"force": true, "jacket": Color(0.32, 0.34, 0.2), "cap": true, "hood": false, "pack": true, "height": 1.78,
				"gait": "stand", "umbrella": false, "vest": false, "bag": false, "bike": false}      # (= abenteuer_figuren_daten.gd)
	var r: Vector3 = story.rastplatz_pos()
	var at := r + Vector3(5.5, 0, -4.5)
	at.y = main.ground_y(at.x, at.z)
	var v = main.spawn("person", at, r)
	if v == null:
		return
	v.puppet = true
	v.set_meta("nachbar", true)
	v.global_position = at
	var d := r - at
	v.heading = atan2(-d.x, -d.z)
	v.rotation.y = v.heading
	ruedi = v


func _process(dt: float) -> void:
	if story == null or not bool(story.get("running")):
		return
	_t += dt
	if _t < 0.5:
		return
	_t = 0.0
	var ph := str(story.get("phase"))
	# remember in which Spielstand Maggie was played / finished
	if not maggie_begonnen():
		_merken("maggie_begonnen")
	if ph in ["finale_cut", "ende", "abspann"] and not maggie_fertig():
		_merken("maggie_fertig")
	if not _abz_ok and maggie_fertig() and karte_fertig(main):
		_abz_ok = true
		story.tipp(T.t("Neues Abzeichen: Beide Geschichten geschafft"))
	if story.geschuetzt():
		return
	var me: Vector3 = story.spieler_pos()
	# 1/2 Ruedi in autumn
	if not _gruss_ok and ruedi != null and is_instance_valid(ruedi) and ph == "region":
		var dv := Vector2(me.x - ruedi.global_position.x, me.z - ruedi.global_position.z)
		if dv.length() < 5.0:
			_gruss_ok = true
			ruedi.heading = atan2(-dv.x, -dv.y)
			ruedi.rotation.y = ruedi.heading
			var s := T.t("Ruedi, der Wildhüter: «Salü! Ah, ihr zwei seid das – du und der kleine Hund! Anna von der Hütte hat mir von euch erzählt.»")
			if karte_begonnen(main):
				s += " " + T.t("«Der Enkel vom Bergführer war auch schon hier oben – mit einer alten Karte.»")
			story.tipp(s)
	# 3 the cheese in summer
	if _kaese_t > 0.0 and main.now() > _kaese_t and ph == "region":
		_kaese_t = -1.0
		story.tipp(T.t("Maggie hebt die Nase: Von der Alp Tschuggen her riecht es nach Vrenis Alpkäse."))
	# 4 the hiking book in the chapel
	if not _buch_ok and ph == "finale_walk" and karte_fertig(main):
		var c: Vector3 = story.tal_punkt(KAPELLE.x, KAPELLE.y)
		if Vector2(me.x - c.x, me.z - c.z).length() < 9.0:
			_buch_ok = true
			story.tipp(T.t("Neben der Tür liegt ein Wanderbuch. Ein Eintrag: «Mit der alten Karte durchs ganze Tal. Danke, Bergtal!»"))
