extends "res://scripts/bergtal_erleben_base.gd"
## «Maggie und der Bergkristall» (Daniel 31.10.2026, Paket S2 «Maggie + liebe Tiere»): Maggie, der Familienhund.
## Ein kleiner heller Terrier (Jack-Russell-artig: weiss mit hellbraunen Flecken, Schulterhöhe ≈ 30 cm – Rassestandard
## FCI 345: 25–30 cm), folgt der Spielfigur und hat vier Fähigkeiten:
##   * Riechen      – findet versteckte Spuren und Wege (leuchtende Pfotenspuren), ohne Rätsel in der Nähe: Spur zum nächsten
##   * Warnen       – knurrt / bellt von selbst, wenn böse Tiere nah sind (Knoten der Gruppe «maggie_boese», Paket S3) und an
##                    Weggabelungen, wo auf einem Weg Gefahr lauert
##   * Graben/Holen – gräbt Dinge aus (Laub, Schnee, Geröll) und holt Gegenstände, wo du nicht hinkommst (dünnes Eis)
##   * Durchschlüpfen – kriecht durch enge Stellen (Spalt unter der Tür, Felsspalte, Gatter) und öffnet von der anderen Seite
## Jede Region (Jahreszeit) hat 4 Stationen in fester Reihenfolge (Paket «Dauer»: je eine zweite Gabelung), davon mindestens 2 Maggie-Rätsel (STATIONEN unten).
## Die lieben Tiere (Eule, Steinbock, Murmeltier, Fuchs) stehen in maggie_helfer.gd.
##
## Verbindung mit dem Rahmen (Paket S1, scripts/maggie_story.gd = main.maggie): S1 legt diese Datei beim Öffnen der
##   Geschichte als Kind des Story-Knotens an und setzt vorher `main` und `story`. Benutzt werden region_aktiv(),
##   spieler_pos() (Welt), region_mitte(id) (Welt), tipp(), moveeye_sagt(), aufgabe_anmelden(id, text) /
##   aufgabe_erledigt(id) (alle Stationen sind Aufgaben – sind alle erledigt, leuchtet das Jahreszeiten-Tor),
##   zukunftsbild_ort(pos, text) (die Gefahr an der Weggabelung), die Signale region_gestartet / region_beendet /
##   einstieg_graben(pos) (Maggie läuft hin und gräbt den Kristall aus) / geschichte_beendet.
##   Jede Region baut das Bergtal neu: Maggie, die Stationen und die Helfer werden bei region_gestartet neu gebaut.
##   Optional, wenn der Rahmen sie hat: story.spieler_setzen(welt_pos) (Steinbock trägt dich), story.speichern() (nach Rätsel).
##   Speichern: zustand() -> Dictionary für den Autosave am Rastplatz, laden(d) beim Weiterspielen.
##   Sperren: sperren() -> [[welt_pos, radius], …] – noch geschlossene Stellen (Tür, Spalte, Gatter, Fels), falls der
##   Rahmen die Figur dort aufhalten will.
##   Ohne Rahmen (Tests): StubStory unten, gestartet über /control maggie_hund start.
## Paket S3 (maggie_gefahr.gd): böse Tiere in die Gruppe «maggie_boese» (Node3D, Welt-Position); optional
##   Methode ablenken(welt_pos: Vector3, sekunden: float) – der Fuchs lockt sie weg; Meta «art» = wildschwein | wolf | kraehe | viper.
## Lite: _lite() (Bergtal/Bib.lite() = Engine-Meta «lite»): weniger Erdkrümel, keine Lämpchen.
## Test: /control {"action": "maggie_hund", "do": "info" | "start" (region) | "befehl" (f) | "spieler" (x, z) | "loesen" | "stop"}

const Helfer = preload("res://scripts/maggie_helfer.gd")
const Spieltest = preload("res://scripts/spieltest.gd")   # Haken für den Spieltest-Assistenten
const UI = preload("res://scripts/ui_style.gd")

signal raetsel_geloest(region: String, id: String)
signal region_raetsel_fertig(region: String)

const REGIONEN := ["herbst", "winter", "fruehling", "sommer"]
const FOLGE_D := 1.6                 # m: so weit hinter / neben der Figur
const NAH_R := 7.0                   # m: so nah an einer Station = «du bist dort»
const WARN_R := 26.0                 # m: so nah ein böses Tier = Maggie warnt
const WEIT_R := 45.0                 # m: weiter weg = Maggie kommt nachgelaufen (springt hin, wenn man es nicht sieht)
const HILFE_S := 25.0                # s an einer Station ohne Lösung: der richtige Knopf leuchtet
# Maggie: weiss mit hellbraunen Flecken; Fell-Oberfläche ≈ 30 °C (Wärmebild, wie «dog» in actor.gd)
const FELL := Color(0.93, 0.91, 0.86)
const FLECK := Color(0.72, 0.5, 0.28)
const FELL_C := 30.0

var story = null                     # maggie_story.gd (S1) oder StubStory
var hund: Node3D                     # Maggie (actor.gd «dog», puppet)
var helfer                           # maggie_helfer.gd
var region := ""
var c := Vector2.ZERO                # Mitte der Region (Tal)
var stationen: Array = []            # die Stationen dieser Region (Dictionaries, siehe _stationen())
var idx := 0                         # die aktuelle Station
var geloest := {}                    # id -> true (über alle Regionen, gespeichert)
var gefunden: Array = []             # ids der gefundenen Dinge (Kartenstücke, Seil …)
var fertig := {}                     # region -> true
var zustand_hund := "folgen"         # folgen | aktion
var _q := {"a": null, "q": [], "t": 0.0}
var _rroot: Node3D                   # Dinge der Region (Tal-Raum)
var _sp_alt := Vector3.ZERO
var _sp_dir := Vector3(0, 0, 1)
var _steh_t := 0.0
var _warn_bis := 0.0
var _gabel_warn := 0.0
var _nah_t := 0.0
var _poll := 0.0
var _kruemel: Array = []             # [mesh, velocity, end]
var _pfoten: Array = []              # [mesh, show at, end]
var _uhr := 0.0
var _layer: CanvasLayer
var _bar: PanelContainer
var _knoepfe := {}
var _status: Label
var _msg: Label
var _msg_bis := 0.0
var _gesagt := {}                    # station id -> true (Hinweis schon gesagt)


var main                             # gesetzt von maggie_story.gd (S1) vor dem Anlegen
var zwei = null                      # maggie_zwei.gd (zwei Spieler): führt Maggie selbst, ersetzt eine Station durch ein Teamrätsel
var _bt_alt = null


func _ready() -> void:
	if m == null:
		m = main
	if m == null:
		return
	main = m
	name = "maggie_hund"
	helfer = Helfer.new(self)
	_ui()
	if story == null:
		story = _story_suchen()
	verbinden(story)


func _part() -> String:
	return "maggie"


func _binden() -> bool:
	"""an das Bergtal anhängen, das gerade gebaut ist (jede Region baut es neu, mit ihrer Jahreszeit)"""
	var b = m.scenes.data.get("bergtal", null) if m != null and m.scenes != null else null
	if b == null or b.tal == null or not is_instance_valid(b.tal):
		return false
	if b == _bt_alt and holder != null and is_instance_valid(holder):
		return true
	_aufraeumen()
	bt = b
	_bt_alt = b
	s = bt.s
	season = str(bt.season)
	lite = _lite() or str(m.quality) == "simple"
	process_priority = 100
	holder = Node3D.new()
	holder.name = "maggie_hund"
	bt.tal.add_child(holder)
	return true


func _aufraeumen() -> void:
	"""alles der Region weg (Maggie, Stationen, Helfer, Effekte)"""
	if helfer != null:
		helfer.aufraeumen()
	if hund != null and is_instance_valid(hund):
		hund.queue_free()
	hund = null
	if _rroot != null and is_instance_valid(_rroot):
		_rroot.queue_free()
	_rroot = null
	for k in _kruemel + _pfoten:
		if is_instance_valid(k[0]):
			k[0].queue_free()
	_kruemel = []
	_pfoten = []
	stationen = []
	region = ""
	_q["q"] = []
	zustand_hund = "folgen"
	if _bar != null:
		_bar.visible = false


func _story_suchen():
	for k in ["maggie", "maggie_story"]:
		var s_ = m.get(k)
		if s_ != null and s_ is Object and (s_ as Object).has_method("region_aktiv"):
			return s_
	var g := get_tree().get_nodes_in_group("maggie_story") if is_inside_tree() else []
	return g[0] if g.size() > 0 else null


func verbinden(s_) -> void:
	story = s_
	if story == null:
		return
	for sg in [["region_gestartet", "_on_region"], ["region_beendet", "_on_ende"], ["einstieg_graben", "_on_einstieg"],
			["geschichte_beendet", "_on_schluss"]]:
		if story.has_signal(sg[0]) and not story.is_connected(sg[0], Callable(self, sg[1])):
			story.connect(sg[0], Callable(self, sg[1]))
	var r := _region_der_story()
	if r != "" and r != region:
		_on_region(r)


func _on_ende(_id: String) -> void:
	_aufraeumen()


func _on_schluss() -> void:
	_aufraeumen()
	if holder != null and is_instance_valid(holder):
		holder.queue_free()
	holder = null
	_bt_alt = null


func _on_einstieg(pos: Vector3) -> void:
	"""der Einstieg: beim Spaziergang läuft Maggie zu pos und gräbt den leuchtenden Bergkristall aus"""
	if not _binden():
		return
	_hund_bauen()
	var p := VL(pos)
	var ziel := Vector3(p.x, 0, p.z)
	if ppos(hund).distance_to(_spieler()) > 6.0:
		place(hund, _spieler() + Vector3(1.0, 0, 1.0))
	_aktion([{"t": "idle", "k": "sniff", "s": 1.2}, {"t": "bark", "n": 1}, {"t": "walk", "p": ziel + Vector3(0, 0, 0.6), "spd": 3.0},
		{"t": "face", "p": ziel}, {"t": "call", "fn": func(): _graben_hier(true)}, {"t": "idle", "k": "root", "s": 3.0},
		{"t": "call", "fn": func(): _graben_hier(false)}, {"t": "bark", "n": 3}, {"t": "idle", "k": "sit", "s": 2.0}])


var _graben_frei := false


func _graben_hier(an: bool) -> void:
	_graben_frei = an


func _region_der_story() -> String:
	if story != null and story.has_method("region_aktiv"):
		return str(story.region_aktiv())
	return ""


# ---- Rahmen-API (mit Rückfall, falls etwas fehlt) ----------------------------------------------------------------------
func _spieler() -> Vector3:
	"""wo die Spielfigur ist (Tal, y = 0)"""
	var w = story.spieler_pos() if story != null and story.has_method("spieler_pos") else null
	if not (w is Vector3):
		w = view_pos()
	var q := VL(w)
	return Vector3(q.x, 0, q.z)


func _mitte(r: String) -> Vector2:
	var w = story.region_mitte(r) if story != null and story.has_method("region_mitte") else null
	if w is Vector3:
		var q := VL(w)
		return Vector2(q.x, q.z)
	return StubStory.MITTE.get(r, Vector2(60, 20))


func tipp(t: String) -> void:
	if story != null and story.has_method("tipp"):
		story.tipp(t)                                 # (S1 zeigt den Tipp gross unten – nicht doppelt)
	else:
		_zeige(t)


func moveeye(t: String) -> void:
	if story != null and story.has_method("moveeye_sagt"):
		story.moveeye_sagt(t)
	else:
		_zeige(t)


func _zeige(t: String) -> void:
	"""eigene kleine Zeile über Maggies Knöpfen (immer, damit man weiss, was Maggie gerade macht)"""
	if _msg != null:
		_msg.text = t
		_msg.visible = true
		_msg_bis = _uhr + 7.0


# ---- die Stationen ---------------------------------------------------------------------------------------------------
func _stationen(r: String) -> Array:
	"""f: riechen | graben | schluepfen | warnen | helfer; ding: was dort steht; off: Tal-Versatz zur Regionsmitte (m);
	texte kurz und einfach (für 12-Jährige)"""
	match r:
		"herbst":
			return [
				{"id": "h_spur", "f": "riechen", "ding": "spur", "off": Vector2(170, 40), "ziel": Vector2(160, 28),
					"hinweis": T.t("Im Nebel ist der Weg verschwunden. Maggie hält die Nase in die Luft."),
					"hilfe": T.t("Lass Maggie riechen!"),
					"ok": T.t("Maggie hat die Spur! Leuchtende Pfotenspuren führen bis zu den Steinen im Bach."),
					"me": T.t("MoveEye würde jetzt die frischen Spuren am Boden bemerken und dir zeigen.")},
				{"id": "h_laub", "f": "graben", "ding": "haufen", "off": Vector2(115, -148), "item": "kartenstueck_herbst",
					"hinweis": T.t("Unter dem gelben Lärchenlaub glitzert etwas."),
					"hilfe": T.t("Maggie kann graben!"),
					"ok": T.t("Maggie gräbt und bringt dir ein Stück einer alten Karte!"),
					"me": T.t("MoveEye würde sich merken, wo etwas vergraben ist.")},
				{"id": "h_gabel", "f": "warnen", "ding": "gabel", "off": Vector2(-100, -100), "boese": -1,
					"hinweis": T.t("Der Weg teilt sich. Hör auf Maggie!"),
					"hilfe": T.t("Maggie knurrt einen der Wege an. Nimm lieber den anderen!"),
					"ok": T.t("Gut gemacht! Du hast auf Maggie gehört."),
					"me": T.t("MoveEye würde jetzt merken, dass sich im Gebüsch etwas bewegt, und dir Bescheid geben.")},
				# Paket «Dauer»: eine zweite Gabelung kurz vor dem Tor (gleiche Texte, der Weg ist länger geworden)
				{"id": "h_gabel2", "f": "warnen", "ding": "gabel", "off": Vector2(-220, -40), "boese": 1,
					"hinweis": T.t("Der Weg teilt sich. Hör auf Maggie!"),
					"hilfe": T.t("Maggie knurrt einen der Wege an. Nimm lieber den anderen!"),
					"ok": T.t("Gut gemacht! Du hast auf Maggie gehört."),
					"me": T.t("MoveEye würde jetzt merken, dass sich im Gebüsch etwas bewegt, und dir Bescheid geben.")},
			]
		"winter":
			return [
				{"id": "w_tuer", "f": "schluepfen", "ding": "tuer", "off": Vector2(-214, -80),
					"hinweis": T.t("Die Tür der Schutzhütte klemmt. Unten ist ein schmaler Spalt."),
					"hilfe": T.t("Maggie passt durch enge Stellen!"),
					"ok": T.t("Maggie schlüpft durch und schiebt den Riegel weg. Die Tür ist offen!"),
					"me": T.t("MoveEye würde dir sagen, ob in der Hütte jemand ist.")},
				{"id": "w_eis", "f": "graben", "ding": "eis", "off": Vector2(-154, -152), "item": "kartenstueck_winter",
					"hinweis": T.t("Auf dem Eis liegt ein Stück Papier. Das Eis ist zu dünn für dich!"),
					"hilfe": T.t("Maggie ist leicht. Sie kann es holen."),
					"ok": T.t("Maggie tapst übers Eis und holt dir ein Kartenstück!"),
					"me": T.t("MoveEye würde das Eis knacken hören und dich warnen.")},
				{"id": "w_gabel", "f": "warnen", "ding": "gabel", "off": Vector2(-58, 32), "boese": 1,
					"hinweis": T.t("Zwei Wege im Schnee. Maggie spitzt die Ohren."),
					"hilfe": T.t("Maggie knurrt einen der Wege an. Nimm lieber den anderen!"),
					"ok": T.t("Richtig! Auf dem anderen Weg leuchteten Augen im Dunkeln."),
					"me": T.t("MoveEye würde auch im Dunkeln sehen, wo sich etwas Warmes versteckt.")},
				{"id": "w_gabel2", "f": "warnen", "ding": "gabel", "off": Vector2(102, 32), "boese": -1,      # Paket «Dauer»
					"hinweis": T.t("Zwei Wege im Schnee. Maggie spitzt die Ohren."),
					"hilfe": T.t("Maggie knurrt einen der Wege an. Nimm lieber den anderen!"),
					"ok": T.t("Richtig! Auf dem anderen Weg leuchteten Augen im Dunkeln."),
					"me": T.t("MoveEye würde auch im Dunkeln sehen, wo sich etwas Warmes versteckt.")},
			]
		"fruehling":
			return [
				{"id": "f_lawine", "f": "graben", "ding": "haufen", "off": Vector2(60, 100), "item": "kartenstueck_fruehling",
					"hinweis": T.t("Ein Rest Lawinenschnee liegt auf dem Weg. Darunter steckt ein Wegweiser."),
					"hilfe": T.t("Maggie kann graben!"),
					"ok": T.t("Maggie gräbt den Wegweiser frei. Daran hängt ein Kartenstück!"),
					"me": T.t("MoveEye würde sich den Weg merken, damit du ihn wieder findest.")},
				{"id": "f_loecher", "f": "riechen", "ding": "loecher", "off": Vector2(-80, 110), "richtig": 1,
					"hinweis": T.t("Drei Löcher im Hang. Nur eines ist ein Geheimgang."),
					"hilfe": T.t("Lass Maggie riechen, wo das Murmeltier war!"),
					"ok": T.t("Maggie hat es! Das Murmeltier zeigt dir seinen Geheimgang."),
					"me": T.t("MoveEye würde zählen, wie oft das Murmeltier aus dem Loch schaut.")},
				{"id": "f_gatter", "f": "schluepfen", "ding": "gatter", "off": Vector2(-185, 90),
					"hinweis": T.t("Das Weidegatter ist zu. Der Haken ist auf der anderen Seite."),
					"hilfe": T.t("Maggie passt unten durch!"),
					"ok": T.t("Maggie kriecht unten durch und stupst den Haken hoch. Offen!"),
					"me": T.t("MoveEye würde sehen, ob auf der Weide Tiere sind.")},
				{"id": "f_gabel", "f": "warnen", "ding": "gabel", "off": Vector2(-95, -55), "boese": 1,       # Paket «Dauer»
					"hinweis": T.t("Der Weg teilt sich. Hör auf Maggie!"),
					"hilfe": T.t("Maggie knurrt einen der Wege an. Nimm lieber den anderen!"),
					"ok": T.t("Gut gemacht! Du hast auf Maggie gehört."),
					"me": T.t("MoveEye würde jetzt merken, dass sich im Gebüsch etwas bewegt, und dir Bescheid geben.")},
			]
		_:
			return [
				{"id": "s_spalte", "f": "schluepfen", "ding": "spalte", "off": Vector2(110, 80), "item": "seil",
					"hinweis": T.t("Zwei grosse Felsen. Der Spalt dazwischen ist viel zu eng für dich."),
					"hilfe": T.t("Maggie passt durch enge Stellen!"),
					"ok": T.t("Maggie kriecht durch und bringt dir ein Seilende. Jetzt kommst du hinüber!"),
					"me": T.t("MoveEye würde schauen, ob hinter den Felsen alles ruhig ist.")},
				{"id": "s_fels", "f": "helfer", "ding": "fels", "off": Vector2(120, -40), "helfer": "steinbock",
					"hinweis": T.t("Die Felswand ist steil. Oben steht ein Steinbock."),
					"hilfe": T.t("Geh nah zum Steinbock."),
					"ok": T.t("Der Steinbock trägt dich sicher über die Felsen."),
					"me": T.t("MoveEye würde von oben weit ins Tal schauen.")},
				{"id": "s_geroell", "f": "graben", "ding": "haufen", "off": Vector2(-48, -150), "item": "kartenstueck_sommer",
					"hinweis": T.t("Geröll versperrt eine kleine Nische. Etwas schaut heraus."),
					"hilfe": T.t("Maggie kann graben!"),
					"ok": T.t("Maggie scharrt die Steine weg und bringt dir ein Kartenstück!"),
					"me": T.t("MoveEye würde hören, wenn Steine rollen.")},
				{"id": "s_gabel", "f": "warnen", "ding": "gabel", "off": Vector2(-190, -130), "boese": -1,
					"hinweis": T.t("Der Weg teilt sich im hohen Gras. Maggie schnuppert."),
					"hilfe": T.t("Maggie knurrt einen der Wege an. Nimm lieber den anderen!"),
					"ok": T.t("Gut! Im Gras auf dem anderen Weg hat es geraschelt."),
					"me": T.t("MoveEye würde merken, dass sich im Gras etwas bewegt, und dir Bescheid geben.")},
			]


func _aufgaben_namen() -> Dictionary:
	"""kurze Namen der Stationen (für die Aufgaben-Liste des Rahmens)"""
	return {"h_spur": T.t("Den Weg im Nebel finden"), "h_laub": T.t("Was glitzert im Laub?"), "h_gabel": T.t("Der richtige Weg an der Gabelung"),
		"h_gabel2": T.t("Der richtige Weg an der Gabelung"),
		"w_tuer": T.t("Die Tür der Schutzhütte öffnen"), "w_eis": T.t("Das Kartenstück auf dem Eis"), "w_gabel": T.t("Der richtige Weg im Schnee"), "w_gabel2": T.t("Der richtige Weg im Schnee"),
		"f_lawine": T.t("Den Wegweiser ausgraben"), "f_loecher": T.t("Den Geheimgang finden"), "f_gatter": T.t("Das Weidegatter öffnen"), "f_gabel": T.t("Der richtige Weg an der Gabelung"),
		"s_spalte": T.t("Durch die Felsspalte"), "s_fels": T.t("Über die steilen Felsen"), "s_geroell": T.t("Was steckt im Geröll?"),
		"s_gabel": T.t("Der richtige Weg im hohen Gras")}


func _platz(p: Vector2) -> Vector2:
	"""ein Ort in der Nähe, der nicht im See und nicht zu steil ist"""
	for rr in [0.0, 4.0, 8.0, 12.0, 16.0, 22.0, 30.0]:
		for k in range(8 if rr > 0.0 else 1):
			var q := p + Vector2(rr, 0).rotated(k * TAU / 8.0)
			var z := str(bt.zone(q.x, q.y))
			if z != "lake" and z != "glacier" and float(bt.slope_deg(q.x, q.y)) < 24.0:
				return q
	return p


func _on_region(r: String) -> void:
	if not r in REGIONEN or not _binden():
		return
	_aufraeumen()
	region = r
	c = _mitte(r)
	_gesagt = {}
	_rroot = Node3D.new()
	_rroot.name = "maggie_" + r
	holder.add_child(_rroot)
	stationen = _stationen(r)
	for st_ in stationen:
		var p := _platz(c + (st_["off"] as Vector2))
		st_["p"] = Vector3(p.x, 0, p.y)
		if st_.has("ziel"):
			var z := _platz(c + (st_["ziel"] as Vector2))
			st_["z"] = Vector3(z.x, 0, z.y)
		_bauen(st_)
	idx = 0
	while idx < stationen.size() and geloest.has(str(stationen[idx]["id"])):
		_geloest_zeigen(stationen[idx])
		idx += 1
	_hund_bauen()
	helfer.region_bauen(r, c, stationen)
	var namen := _aufgaben_namen()
	for st_ in stationen:                            # alle Stationen sind Aufgaben der Region (das Tor wartet auf sie)
		var id := str(st_["id"])
		if story != null and story.has_method("aufgabe_anmelden"):
			story.aufgabe_anmelden(id, str(namen.get(id, st_["hinweis"])))
			if geloest.has(id) and story.has_method("aufgabe_erledigt"):
				story.aufgabe_erledigt(id)
		if str(st_["ding"]) == "gabel" and story != null and story.has_method("zukunftsbild_ort"):
			story.zukunftsbild_ort(W(G((st_["boese_p"] as Vector3).x, (st_["boese_p"] as Vector3).z)),
				T.t("An der Weggabelung leuchten Augen im Gebüsch. Hör auf Maggie!"))
	_bar.visible = true
	_knopf_hilfe("")


# ---- Maggie -----------------------------------------------------------------------------------------------------------
func _hund_bauen() -> void:
	if hund != null and is_instance_valid(hund):
		return
	var sp := _spieler()
	hund = actor("dog", G(sp.x + 1.2, sp.z + 1.2), G(sp.x, sp.z), 1.6)
	hund.name = "maggie"
	hund.body_root.scale = Vector3.ONE * 0.6         # «dog» hat 50 cm Rücken-Mitte → ≈ 30 cm Schulterhöhe
	bt._recolor(hund, FELL, FELL_C)
	# hellbraune Flecken: Ohren, ein Fleck über einem Auge, einer auf dem Rücken, Schwanzwurzel
	var hd: Node3D = hund.head
	var big: MeshInstance3D = null
	for mi in hd.find_children("*", "MeshInstance3D", true, false):
		var g := mi as MeshInstance3D
		if g.layers != 1:
			continue
		if g.mesh is PrismMesh or (g.mesh is CapsuleMesh and g.position.x != 0.0):
			g.material_override = m.mat(FLECK)
		elif g.mesh is SphereMesh and (big == null or (g.mesh as SphereMesh).radius > (big.mesh as SphereMesh).radius):
			big = g
	if big != null:
		var r := (big.mesh as SphereMesh).radius
		part(hd, sphm(r * 0.75), big.position + Vector3(r * 0.32, r * 0.28, -r * 0.12), FLECK, FELL_C)
	part(hund.body_root, sphm(0.11, 0.12), Vector3(0.02, 0.62, 0.12), FLECK, FELL_C, Vector3.ZERO, Vector3(1.0, 0.6, 1.4))
	if hund.tail != null:
		part(hund.tail, sphm(0.04), Vector3(0, 0.03, 0.02), FLECK, FELL_C - 2.0)
	hund.process_mode = Node.PROCESS_MODE_INHERIT
	_q["a"] = hund


func _folgen(dt: float) -> void:
	var sp := _spieler()
	var mv := sp - _sp_alt
	if mv.length() > 0.05:
		_sp_dir = mv.normalized()
		_steh_t = 0.0
	else:
		_steh_t += dt
	_sp_alt = sp
	var ziel := sp - _sp_dir * FOLGE_D + Vector3(-_sp_dir.z, 0, _sp_dir.x) * 0.7
	var hp := ppos(hund)
	var d := hp.distance_to(ziel)
	if d > WEIT_R and unseen(W(G(hp.x, hp.z)), 25.0):
		place(hund, ziel)
		return
	if d > 0.6:
		idle(hund, "")
		walk(hund, ziel, clampf(d * 1.3, 1.2, 5.5), dt)
	else:
		stop(hund, dt)
		face(hund, sp - hp)
		if _steh_t > 5.0 and (str(hund.idle_kind) == "" or hund.now_s() > float(hund.idle_until) + 2.0):
			if _steh_t > 14.0 and randf() < 0.4:
				idle(hund, "lie", randf_range(6.0, 12.0))      # anim_tier.gd: lies down, the head up now and then
			else:
				idle(hund, ["sniff", "sit", "sniff", "schief"][randi() % 4], randf_range(2.0, 4.0))


func place(a, p: Vector3, lift := false) -> void:
	"""wie in der Basis, aber ohne «lift» immer auf den Boden (p.y egal)"""
	super.place(a, p if lift else G(p.x, p.z), lift)


func _q_tick(r: Dictionary, dt: float) -> bool:
	"""eine kleine Abfolge für eine Figur abspielen: walk, wait, idle, call, hide, show, tp, face, bark … – true = leer"""
	var q: Array = r["q"]
	var a = r["a"]
	if q.is_empty() or a == null or not is_instance_valid(a):
		return true
	var s_: Dictionary = q[0]
	r["t"] = float(r["t"]) + dt
	var tt := float(r["t"])
	var ok := false
	match str(s_["t"]):
		"walk":
			ok = walk(a, s_["p"], float(s_.get("spd", 1.8)), dt, s_.get("y", null))
		"wait":
			stop(a, dt)
			ok = tt >= float(s_.get("s", 1.0))
		"idle":
			if not s_.has("_on"):
				s_["_on"] = true
				idle(a, str(s_["k"]), float(s_.get("s", 1.5)))
			stop(a, dt)
			ok = tt >= float(s_.get("s", 1.5))
			if ok:
				idle(a, "")
		"call":
			(s_["fn"] as Callable).call()
			ok = true
		"hide":
			a.visible = false
			ok = tt >= float(s_.get("s", 1.0))
		"show":
			a.visible = true
			ok = true
		"tp":
			place(a, s_["p"], s_.has("y"))
			ok = true
		"face":
			ok = turn_to(a, (s_["p"] as Vector3) - ppos(a), dt, 6.0) or tt > 1.0
		"bark":
			bellen(ppos(a), int(s_.get("n", 2)))
			ok = true
	if ok:
		q.pop_front()
		r["t"] = 0.0
	return q.is_empty()


func _aktion(schritte: Array) -> void:
	zustand_hund = "aktion"
	_q["q"] = schritte
	_q["t"] = 0.0


# ---- Töne -------------------------------------------------------------------------------------------------------------
func bellen(p: Vector3, n := 2) -> void:
	# Kleiner Terrier: Bellen mit Grundton um 500–700 Hz, je ≈ 0,15 s
	var notes := []
	for i in range(n):
		notes.append([i * 0.28, 0.16, 720.0, 520.0, 1.0])
	sound(p, "bark", notes, -2.0, -8.0)


func knurren(p: Vector3) -> void:
	if hund != null and is_instance_valid(hund):
		idle(hund, "knurren", 1.4)                       # anim_tier.gd: ducks while growling
	sound(p, "growl", [[0.0, 1.1, 110.0, 95.0, 1.0]], -4.0, -22.0)


func _synth(kind: String, notes: Array, dur: float) -> AudioStreamWAV:
	"""eigene Töne: bark (Bellen), growl (Knurren), hoot (Eule), yip (Fuchs, hell); sonst wie die Bergtal-Erlebnisse"""
	if not kind in ["bark", "growl", "hoot", "yip"]:
		return super._synth(kind, notes, dur)
	var rate := 16000
	var ns := int((dur + 0.2) * rate)
	var buf := PackedFloat32Array()
	buf.resize(ns)
	for n in notes:
		var i0 := int(float(n[0]) * rate)
		var ln := float(n[1])
		var cnt := mini(int(ln * rate), ns - i0)
		var ph := 0.0
		for i in range(cnt):
			var t := float(i) / rate
			var f := lerpf(float(n[2]), float(n[3]), t / ln)
			ph += TAU * f / rate
			var v := 0.0
			match kind:
				"bark", "yip":
					var env := minf(1.0, t / 0.008) * exp(-t * (14.0 if kind == "bark" else 22.0))
					v = (sin(ph) + 0.5 * sin(2.0 * ph) + 0.35 * (randf() * 2.0 - 1.0)) * env * 1.6
				"growl":
					var env2 := minf(1.0, t / 0.15) * clampf((ln - t) / 0.2, 0.0, 1.0)
					v = (sin(ph) + 0.7 * sin(2.0 * ph + 0.3) + 0.4 * (randf() * 2.0 - 1.0)) * (0.6 + 0.4 * sin(t * TAU * 23.0)) * env2
				"hoot":                                   # Waldkauz: «hu-huuu», weich, tief
					var env3 := minf(1.0, t / 0.05) * clampf((ln - t) / 0.12, 0.0, 1.0)
					v = sin(ph) * (1.0 + 0.05 * sin(t * TAU * 6.0)) * env3 * 1.3
			buf[i0 + i] += v * float(n[4] if n.size() > 4 else 1.0) * 0.22
	var pcm := PackedByteArray()
	pcm.resize(ns * 2)
	for i in range(ns):
		pcm.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = pcm
	return w


# ---- Befehle (Knöpfe) ---------------------------------------------------------------------------------------------------
func aktuell() -> Dictionary:
	return stationen[idx] if idx < stationen.size() else {}


func _nah(st_: Dictionary, r := NAH_R) -> bool:
	if not st_.is_empty() and zwei != null and is_instance_valid(zwei) and zwei.nah_bei(st_["p"], r):
		return true                                   # zwei Spieler: Spieler 2 oder Maggie (selbst gesteuert) ist dort
	return not st_.is_empty() and _spieler().distance_to(st_["p"]) < r


func _zwei_ersetzt(st_: Dictionary) -> bool:
	"""zwei Spieler: diese Station ist ein Teamrätsel (maggie_zwei.gd löst sie)"""
	return zwei != null and is_instance_valid(zwei) and zwei.ersetzt(str(st_.get("id", "")))


func befehl(f: String) -> Dictionary:
	"""ein Knopf: riechen | graben | schluepfen"""
	if hund == null or region == "":
		return {"ok": false, "error": "keine Region"}
	if zustand_hund != "folgen":
		_zeige(T.t("Maggie ist noch beschäftigt."))
		return {"ok": false, "error": "busy"}
	var st_ := aktuell()
	var nah := _nah(st_)
	var hp := ppos(hund)
	if nah and str(st_["f"]) == f:
		_loesen_start(st_)
		return {"ok": true, "loest": st_["id"]}
	match f:
		"riechen":
			_aktion([{"t": "idle", "k": "sniff", "s": 1.6}, {"t": "call", "fn": func():
				if not st_.is_empty():
					_pfoten_legen(ppos(hund), st_["p"], 14.0)
					_zeige(T.t("Maggie riecht etwas! Folge den leuchtenden Pfotenspuren."))
				else:
					_zeige(T.t("Maggie riecht nur Gras und Blumen."))}])
		"graben":
			_aktion([{"t": "idle", "k": "root", "s": 1.8}, {"t": "call", "fn": func():
				_kruemel_werfen(ppos(hund), _boden_farbe(), 4)
				_zeige([T.t("Maggie gräbt … einen alten Knochen. Den behält sie lieber selbst."),
					T.t("Maggie gräbt ein Loch. Da ist nichts. Sie wedelt trotzdem."),
					T.t("Maggie findet einen Tannzapfen und ist sehr stolz.")][randi() % 3])}])
		"schluepfen":
			_aktion([{"t": "idle", "k": "sniff", "s": 0.8}, {"t": "call", "fn": func():
				_zeige(T.t("Hier gibt es keine enge Stelle zum Durchschlüpfen."))}])
	if nah and str(st_["f"]) in ["riechen", "graben", "schluepfen"]:
		_zeige(T.t("Das klappt hier nicht. Probier etwas anderes!"))
	var sp_ := _spieler()
	return {"ok": true, "loest": "", "pos": [snappedf(hp.x, 0.1), snappedf(hp.z, 0.1)], "spieler": [snappedf(sp_.x, 0.1), snappedf(sp_.z, 0.1)],
		"station": str(st_.get("id", "")), "abstand": snappedf(sp_.distance_to(st_["p"]), 0.1) if not st_.is_empty() else -1.0}


func _loesen_start(st_: Dictionary) -> void:
	var p: Vector3 = st_["p"]
	var id := str(st_["id"])
	var sp := _spieler()
	match str(st_["ding"]):
		"spur":
			var z: Vector3 = st_["z"]
			_aktion([{"t": "walk", "p": p, "spd": 2.0}, {"t": "idle", "k": "sniff", "s": 1.5},
				{"t": "call", "fn": func(): _pfoten_legen(p, z, 30.0)},
				{"t": "walk", "p": p.lerp(z, 0.5), "spd": 1.4}, {"t": "idle", "k": "sniff", "s": 0.8},
				{"t": "walk", "p": z, "spd": 1.4}, {"t": "idle", "k": "schuetteln", "s": 1.2}, {"t": "bark", "n": 2},
				{"t": "call", "fn": func(): _fertig(st_)}])
		"haufen":
			_aktion([{"t": "walk", "p": p + Vector3(0, 0, 0.9), "spd": 2.2}, {"t": "face", "p": p},
				{"t": "call", "fn": func(): _graben_an(st_, true)}, {"t": "idle", "k": "root", "s": 2.6},
				{"t": "call", "fn": func(): _graben_an(st_, false)}, {"t": "bark", "n": 1},
				{"t": "walk", "p": sp + Vector3(0.6, 0, 0.6), "spd": 2.5}, {"t": "idle", "k": "sit", "s": 1.0},
				{"t": "call", "fn": func(): _fertig(st_)}])
		"eis":
			var item: Vector3 = st_["item_p"]
			var rand_: Vector3 = st_["rand"]
			var y := float(st_["eis_y"])
			_aktion([{"t": "walk", "p": rand_, "spd": 2.0}, {"t": "walk", "p": item, "spd": 0.9, "y": y},
				{"t": "idle", "k": "sniff", "s": 0.8}, {"t": "call", "fn": func(): _ding_weg(st_)},
				{"t": "walk", "p": rand_, "spd": 1.0, "y": y}, {"t": "walk", "p": sp + Vector3(0.6, 0, 0.6), "spd": 2.5},
				{"t": "idle", "k": "sit", "s": 1.0}, {"t": "call", "fn": func(): _fertig(st_)}])
		"tuer", "gatter", "spalte":
			var vorn: Vector3 = st_["vorn"]
			var hinten: Vector3 = st_["hinten"]
			var schr := [{"t": "walk", "p": vorn, "spd": 2.0}, {"t": "face", "p": hinten}, {"t": "idle", "k": "sniff", "s": 0.8},
				{"t": "walk", "p": vorn.lerp(hinten, 0.4), "spd": 0.8}, {"t": "hide", "s": 1.4},
				{"t": "tp", "p": hinten}, {"t": "show"}, {"t": "bark", "n": 2}, {"t": "wait", "s": 0.6},
				{"t": "call", "fn": func(): _oeffnen(st_)}, {"t": "wait", "s": 1.2}]
			if str(st_["ding"]) == "spalte":               # mit dem Seilende zurück
				schr += [{"t": "walk", "p": vorn.lerp(hinten, 0.6), "spd": 0.8}, {"t": "hide", "s": 1.0}, {"t": "tp", "p": vorn},
					{"t": "show"}, {"t": "walk", "p": sp + Vector3(0.6, 0, 0.6), "spd": 2.0}]
			schr.append({"t": "call", "fn": func(): _fertig(st_)})
			_aktion(schr)
		"loecher":
			var lo: Array = st_["loch_p"]
			var schr2 := [{"t": "walk", "p": lo[0], "spd": 1.6}, {"t": "idle", "k": "sniff", "s": 1.2},
				{"t": "walk", "p": lo[2], "spd": 1.6}, {"t": "idle", "k": "sniff", "s": 1.2},
				{"t": "walk", "p": lo[int(st_["richtig"])], "spd": 1.6}, {"t": "idle", "k": "root", "s": 1.4}, {"t": "bark", "n": 3},
				{"t": "call", "fn": func(): helfer.szene("murmeltier_loch", st_)}, {"t": "wait", "s": 2.5},
				{"t": "call", "fn": func(): _fertig(st_)}]
			_aktion(schr2)
	if not _gesagt.has(id + "_me"):
		_gesagt[id + "_me"] = true
		moveeye(str(st_["me"]))


func _fertig(st_: Dictionary) -> void:
	var id := str(st_["id"])
	if geloest.has(id):
		return
	geloest[id] = true
	if st_.has("item") and not gefunden.has(str(st_["item"])):
		gefunden.append(str(st_["item"]))
	tipp(str(st_["ok"]))
	_geloest_zeigen(st_)
	var sf = story.spieler() if story != null and story.has_method("spieler") else null
	if sf != null and is_instance_valid(sf) and sf.has_method("aktion"):   # anim_mensch.gd: take it / be happy
		sf.aktion("aufheben" if st_.has("item") else "freude")
	raetsel_geloest.emit(region, id)
	Spieltest.ereignis("maggie", "fortschritt", {"raetsel": id})              # Spieltest: Rätsel gelöst
	if id == "h_gabel":                                   # (der Fuchs nur an der ersten Gabelung)
		helfer.szene("fuchs_ablenken", st_)
	if idx < stationen.size() and str(stationen[idx]["id"]) == id:
		idx += 1
	_knopf_hilfe("")
	if story != null and story.has_method("speichern"):
		story.speichern()
	if story != null and story.has_method("aufgabe_erledigt"):
		story.aufgabe_erledigt(id)
	if idx >= stationen.size() and not fertig.has(region):
		fertig[region] = true
		region_raetsel_fertig.emit(region)
		if story != null and story.has_method("aufgabe_erledigt"):
			tipp(T.t("Alle Rätsel gelöst! Jetzt leuchtet das Tor der Jahreszeit."))
		elif story != null and story.has_method("region_fertig"):
			story.region_fertig(region)
		else:
			_zeige(T.t("Alle Rätsel dieser Jahreszeit gelöst!"))


# ---- die Dinge der Stationen ------------------------------------------------------------------------------------------
func _boden_farbe() -> Color:
	return {"herbst": Color(0.85, 0.6, 0.18), "winter": Color(0.93, 0.95, 0.98), "fruehling": Color(0.9, 0.92, 0.95)}.get(region, Color(0.55, 0.52, 0.47))


func _bauen(st_: Dictionary) -> void:
	var p: Vector3 = st_["p"]
	var n := node(_rroot, G(p.x, p.z))
	st_["node"] = n
	var holz := Color(0.42, 0.3, 0.18)
	match str(st_["ding"]):
		"spur":                                   # das Ziel: Trittsteine im Bach (zuerst unsichtbar)
			var z: Vector3 = st_["z"]
			var zn := node(_rroot, G(z.x, z.z))
			st_["ziel_node"] = zn
			for i in range(4):
				part(zn, cylm(0.35, 0.42, 0.18, 8), Vector3(i * 0.9 - 1.3, 0.05, sin(i) * 0.4), Color(0.5, 0.5, 0.48), "stone")
			zn.visible = false
		"haufen":
			var col := _boden_farbe()
			var hm := part(n, sphm(1.0, 0.9, 12), Vector3(0, 0.05, 0), col, "tree" if region == "herbst" else ("snow" if region in ["winter", "fruehling"] else "stone"), Vector3.ZERO, Vector3(1.0, 0.7, 0.85))
			st_["haufen"] = hm
			if region == "fruehling":                  # der Wegweiser schaut oben heraus
				part(n, cylm(0.04, 0.04, 1.4, 6), Vector3(0.2, 0.5, 0), holz, "tree")
				part(n, boxm(0.7, 0.16, 0.03), Vector3(0.5, 1.1, 0), Color(0.95, 0.75, 0.1), "tree")
			var glanz := light_part(n, sphm(0.06), Vector3(0.3, 0.55, -0.4), glow_mat(Color(1.0, 0.92, 0.6), 2.5))
			st_["glanz"] = glanz
		"eis":                                    # dünnes Eis auf einem Tümpel, das Kartenstück 5 m vom Rand
			var y := float(bt.H(p.x, p.z)) + 0.04
			part(n, cylm(6.0, 6.0, 0.04, 20), Vector3(0, 0.02, -6.5), Color(0.7, 0.82, 0.9), "snow")
			for k in range(5):
				part(n, boxm(0.03, 0.01, randf_range(1.0, 2.5)), Vector3(randf_range(-3, 3), 0.07, -6.5 + randf_range(-3, 3)), Color(0.4, 0.5, 0.6), "snow", Vector3(0, randf() * PI, 0))
			var pap := part(n, boxm(0.25, 0.02, 0.18), Vector3(0.4, 0.08, -5.5), Color(0.95, 0.9, 0.75), "tree")
			st_["ding_mesh"] = pap
			st_["glanz"] = light_part(n, sphm(0.08), Vector3(0.4, 0.2, -5.5), glow_mat(Color(1.0, 0.92, 0.6), 2.0))
			st_["rand"] = p + Vector3(0.3, 0, -0.6)
			st_["item_p"] = p + Vector3(0.4, 0, -5.4)
			st_["eis_y"] = y + 0.04
		"tuer", "gatter":
			var gat := str(st_["ding"]) == "gatter"
			var bw := 1.4 if not gat else 2.4
			for sx in [-1, 1]:
				part(n, boxm(0.16, 1.9, 0.16), Vector3(sx * (bw * 0.5 + 0.08), 0.95, 0), holz.darkened(0.2), "tree")
			if not gat:                               # ein Stück Hüttenwand mit Dach
				for sx in [-1, 1]:
					part(n, boxm(1.6, 2.2, 0.25), Vector3(sx * (bw * 0.5 + 0.95), 1.1, 0.1), Color(0.5, 0.48, 0.45), "stone")
				part(n, boxm(bw + 3.6, 0.2, 1.4), Vector3(0, 2.3, 0.3), Color(0.3, 0.22, 0.16), "tree", Vector3(0.12, 0, 0))
			var piv := node(n, Vector3(-bw * 0.5, 0, 0))
			if gat:
				for k in range(4):
					part(piv, boxm(bw, 0.08, 0.05), Vector3(bw * 0.5, 0.45 + k * 0.32, 0), Color(0.6, 0.5, 0.35), "tree")
			else:
				part(piv, boxm(bw, 1.65, 0.07), Vector3(bw * 0.5, 0.25 + 0.83, 0), holz, "tree")
				part(piv, sphm(0.05), Vector3(bw - 0.15, 1.05, -0.05), Color(0.2, 0.2, 0.2), "stone")
			st_["tuer"] = piv
			st_["vorn"] = p + Vector3(0, 0, -1.2)
			st_["hinten"] = p + Vector3(0, 0, 1.4)
			st_["sperre"] = [p, bw * 0.6]
		"spalte":
			for sx in [-1, 1]:
				part(n, boxm(2.4, 3.2, 3.0), Vector3(sx * 1.38, 1.4, 0), Color(0.5, 0.49, 0.46), "stone", Vector3(0, 0, sx * 0.05))
			var seil := part(n, cylm(0.025, 0.025, 4.0, 6), Vector3(0, 2.9, 0), Color(0.85, 0.3, 0.15), "tent", Vector3(PI / 2, 0, 0))
			seil.visible = false
			twin_of(seil).visible = false
			st_["seil"] = seil
			st_["vorn"] = p + Vector3(0, 0, -1.9)
			st_["hinten"] = p + Vector3(0, 0, 1.9)
			st_["sperre"] = [p, 1.2]
		"fels":                                   # steile Felsstufe; der Steinbock steht oben (maggie_helfer.gd)
			for k in range(3):
				part(n, boxm(5.0 - k, 1.4, 2.0), Vector3(0, 0.7 + k * 1.3, k * 1.2), Color(0.55, 0.53, 0.5), "stone")
			st_["oben"] = p + Vector3(0, 0, 3.6)
			st_["oben_y"] = float(bt.H(p.x, p.z)) + 3.9
			st_["sperre"] = [p + Vector3(0, 0, 1.0), 2.6]
		"loecher":
			var lp := []
			for k in range(3):
				var o := Vector3((k - 1) * 2.4, 0, 0)
				lp.append(p + o + Vector3(0, 0, -0.9))
				part(n, cylm(0.28, 0.3, 0.06, 10), o + Vector3(0, 0.02, 0), Color(0.08, 0.06, 0.05), "stone")
				part(n, sphm(0.55, 0.3, 10), o + Vector3(0, 0.0, 0.25), Color(0.42, 0.33, 0.24), "stone", Vector3.ZERO, Vector3(1.0, 1.0, 0.6))
			st_["loch_p"] = lp
		"gabel":                                  # zwei Wegweiser; beim gefährlichen Weg ein dunkles Gebüsch mit Augen
			var b := int(st_["boese"])
			for sx in [-1, 1]:
				var arm := node(n, Vector3(sx * 0.35, 0, 0))
				part(arm, cylm(0.04, 0.04, 1.6, 6), Vector3(0, 0.8, 0), holz, "tree")
				part(arm, boxm(0.6, 0.14, 0.03), Vector3(sx * 0.3, 1.45, 0), Color(0.95, 0.75, 0.1), "tree")
			var busch := node(n, Vector3(b * 6.0, 0, 7.0))
			for k in range(4):
				part(busch, sphm(0.8, 1.1, 8), Vector3(randf_range(-1, 1), 0.5, randf_range(-0.6, 0.6)), Color(0.12, 0.16, 0.1), "tree")
			var augen := []
			for k in range(2):
				for sx in [-1, 1]:
					augen.append(light_part(busch, sphm(0.035), Vector3(k * 0.7 - 0.35 + sx * 0.07, 0.6 + k * 0.15, -1.05), glow_mat(Color(1.0, 0.75, 0.2), 3.0)))
			st_["augen"] = augen
			st_["busch"] = busch
			st_["gut_p"] = p + Vector3(-b * 6.0, 0, 9.0)
			st_["boese_p"] = p + Vector3(b * 6.0, 0, 6.0)


func _graben_an(st_: Dictionary, an: bool) -> void:
	st_["graben"] = an
	if not an:
		var hm = st_.get("haufen", null)
		if hm != null and is_instance_valid(hm):
			show_part(hm, false)
		_ding_weg(st_)


func _ding_weg(st_: Dictionary) -> void:
	for k in ["glanz", "ding_mesh"]:
		var g = st_.get(k, null)
		if g != null and is_instance_valid(g):
			if k == "ding_mesh":
				show_part(g, false)
			else:
				g.visible = false


func _oeffnen(st_: Dictionary) -> void:
	st_["offen"] = true
	if st_.has("tuer"):
		st_["tuer_auf"] = 0.0
	if st_.has("seil"):
		show_part(st_["seil"], true)


func _geloest_zeigen(st_: Dictionary) -> void:
	"""der Zustand nach dem Lösen (auch beim Laden eines Spielstands)"""
	st_["offen"] = true
	match str(st_["ding"]):
		"spur":
			if st_.has("ziel_node"):
				(st_["ziel_node"] as Node3D).visible = true
		"haufen":
			_graben_an(st_, false)
		"eis":
			_ding_weg(st_)
		"tuer", "gatter":
			(st_["tuer"] as Node3D).rotation.y = -1.7
		"spalte":
			show_part(st_["seil"], true)
		"gabel":
			for e in st_.get("augen", []):
				if is_instance_valid(e):
					e.visible = false


func sperren() -> Array:
	"""noch geschlossene Stellen [[Welt-Position, Radius m], …] (für den Rahmen, falls er die Figur aufhält)"""
	var out := []
	for st_ in stationen:
		if st_.has("sperre") and not bool(st_.get("offen", false)):
			var sp: Array = st_["sperre"]
			out.append([W(G((sp[0] as Vector3).x, (sp[0] as Vector3).z)), float(sp[1])])
	return out


# ---- kleine Effekte -----------------------------------------------------------------------------------------------------
func _kruemel_werfen(p: Vector3, col: Color, n: int) -> void:
	if lite:
		n = maxi(1, n / 2)
	for i in range(n):
		var k := light_part(holder, sphm(0.035, -1.0, 6), G(p.x, p.z, 0.1), m.mat(col))
		_kruemel.append([k, Vector3(randf_range(-1.2, 1.2), randf_range(1.5, 2.6), randf_range(0.6, 1.6)), _uhr + 0.7])


func _pfoten_legen(a: Vector3, b: Vector3, lang: float) -> void:
	"""leuchtende Pfotenspuren von a nach b (höchstens «lang» m), eine nach der anderen, verblassen nach 14 s"""
	var d := b - a
	var L := minf(d.length(), lang)
	if L < 0.5:
		return
	var dir := d.normalized()
	var seite := Vector3(-dir.z, 0, dir.x)
	var mt := glow_mat(Color(0.55, 0.85, 1.0), 1.6, 0.85)
	if hund != null and is_instance_valid(hund):
		hund.set_meta("anim_spur_bis", hund.now_s() + 4.0 + L / 1.4)   # anim_tier.gd: the nose on the ground
	var n := int(L / 0.9)
	for i in range(n):
		var q := a + dir * (0.6 + i * 0.9) + seite * (0.12 if i % 2 == 0 else -0.12)
		var pf := light_part(holder, sphm(0.07, 0.02, 6), G(q.x, q.z, 0.03), mt)
		pf.visible = false
		_pfoten.append([pf, _uhr + i * 0.18, _uhr + 14.0 + i * 0.18])


func _effekte(dt: float) -> void:
	for i in range(_kruemel.size() - 1, -1, -1):
		var k: Array = _kruemel[i]
		var mi: MeshInstance3D = k[0]
		if _uhr > float(k[2]) or not is_instance_valid(mi):
			if is_instance_valid(mi):
				mi.queue_free()
			_kruemel.remove_at(i)
			continue
		var v: Vector3 = k[1]
		v.y -= 9.8 * dt
		k[1] = v
		mi.position += v * dt
	for i in range(_pfoten.size() - 1, -1, -1):
		var pf: Array = _pfoten[i]
		var mi2: MeshInstance3D = pf[0]
		if not is_instance_valid(mi2):
			_pfoten.remove_at(i)
			continue
		mi2.visible = _uhr >= float(pf[1])
		if _uhr > float(pf[2]):
			mi2.queue_free()
			_pfoten.remove_at(i)
	for st_ in stationen:
		if bool(st_.get("graben", false)) and randf() < dt * 6.0:
			_kruemel_werfen(ppos(hund) - _richtung(hund) * 0.3, _boden_farbe(), 2)
		if st_.has("tuer_auf"):
			var tw := minf(1.0, float(st_["tuer_auf"]) + dt * 0.8)
			st_["tuer_auf"] = tw
			(st_["tuer"] as Node3D).rotation.y = -1.7 * smoothstep(0.0, 1.0, tw)
			if tw >= 1.0:
				st_.erase("tuer_auf")
		if str(st_["ding"]) == "gabel" and not bool(st_.get("offen", false)):      # die Augen blinzeln
			var aug: Array = st_["augen"]
			var zu := fmod(_uhr + float(aug.size()), 3.7) < 0.15
			for e in aug:
				if is_instance_valid(e):
					e.visible = not zu and (_nah(st_, 18.0) or dark())


func _richtung(a) -> Vector3:
	var h := float(a.heading) - float(bt.tal.rotation.y)
	return Vector3(-sin(h), 0, -cos(h))


# ---- Warnen ----------------------------------------------------------------------------------------------------------
func boese_nah(p: Vector3, r: float) -> Array:
	"""böse Tiere (Paket S3, Gruppe «maggie_boese») näher als r am Tal-Punkt p: [[node, Tal-Pos, Abstand], …]"""
	var out := []
	if not is_inside_tree():
		return out
	for n in get_tree().get_nodes_in_group("maggie_boese"):
		if n is Node3D and (n as Node3D).is_visible_in_tree():
			var q := VL((n as Node3D).global_position)
			var d := Vector2(q.x - p.x, q.z - p.z).length()
			if d < r:
				out.append([n, Vector3(q.x, 0, q.z), d])
	return out


func _warnen() -> void:
	var sp := _spieler()
	if zustand_hund == "folgen" and _uhr > _warn_bis:
		var nah := boese_nah(sp, WARN_R)
		if not nah.is_empty():
			_warn_bis = _uhr + 14.0
			var q: Vector3 = nah[0][1]
			_aktion([{"t": "face", "p": q}, {"t": "call", "fn": func(): knurren(ppos(hund))}, {"t": "wait", "s": 1.0},
				{"t": "bark", "n": 3}, {"t": "wait", "s": 0.8}])
			_zeige(T.t("Maggie knurrt! Da vorne ist etwas. Sei vorsichtig."))
	var st_ := aktuell()                              # die Weggabelung
	if st_.is_empty() or str(st_["ding"]) != "gabel" or _zwei_ersetzt(st_):
		return
	if sp.distance_to(st_["gut_p"]) < 4.0:
		_fertig(st_)
		return
	if zustand_hund != "folgen":
		return
	if _nah(st_, 9.0) and _uhr > _gabel_warn:
		_gabel_warn = _uhr + 9.0
		var bp: Vector3 = st_["boese_p"]
		_aktion([{"t": "walk", "p": (st_["p"] as Vector3).lerp(bp, 0.25), "spd": 1.5}, {"t": "face", "p": bp},
			{"t": "call", "fn": func(): knurren(ppos(hund))}, {"t": "wait", "s": 1.4}])
	if sp.distance_to(st_["boese_p"]) < 3.5 and _uhr > _warn_bis:
		_warn_bis = _uhr + 6.0
		_aktion([{"t": "walk", "p": sp.lerp(st_["boese_p"], 0.5), "spd": 4.0}, {"t": "bark", "n": 4}])
		_zeige(T.t("Maggie stellt sich dir in den Weg und bellt. Lieber den anderen Weg!"))


# ---- Ablauf ------------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if m == null or bt == null or not is_inside_tree() or bt.tal == null or not is_instance_valid(bt.tal):
		return
	super._process(dt)
	dt = minf(dt, 0.25)
	_uhr += dt
	if _msg != null and _msg.visible and _uhr > _msg_bis:
		_msg.visible = false
	_poll -= dt
	if _poll <= 0.0:
		_poll = 1.0
		if story == null:
			verbinden(_story_suchen())
		var r := _region_der_story()
		if r != "" and r != region:
			_on_region(r)
	if hund == null or not is_instance_valid(hund):
		return
	if zustand_hund == "aktion":
		if _q_tick(_q, dt):
			zustand_hund = "folgen"
	elif zwei == null or not is_instance_valid(zwei) or not zwei.fuehrt_hund():
		_folgen(dt)
	if _graben_frei and randf() < dt * 6.0:
		_kruemel_werfen(ppos(hund) - _richtung(hund) * 0.3, _boden_farbe(), 2)
	if region == "":
		_effekte(dt)
		return
	_warnen()
	_effekte(dt)
	_station_hinweis(dt)
	helfer.tick(dt)


func _station_hinweis(dt: float) -> void:
	var st_ := aktuell()
	if st_.is_empty() or not _nah(st_) or _zwei_ersetzt(st_):
		_nah_t = 0.0
		return
	_nah_t += dt
	var id := str(st_["id"])
	if not _gesagt.has(id):
		_gesagt[id] = true
		tipp(str(st_["hinweis"]))
		if str(st_["f"]) == "helfer":
			helfer.szene(str(st_["helfer"]), st_)
	if _nah_t > HILFE_S and not _gesagt.has(id + "_hilfe"):
		_gesagt[id + "_hilfe"] = true
		tipp(str(st_["hilfe"]))
		_knopf_hilfe(str(st_["f"]))


# ---- Knöpfe -------------------------------------------------------------------------------------------------------------
func _ui() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 6
	add_child(_layer)
	var root := VBoxContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	root.grow_horizontal = Control.GROW_DIRECTION_BOTH
	root.grow_vertical = Control.GROW_DIRECTION_BEGIN
	root.offset_bottom = -64                          # über der Leiste unten (Bewegen / Ansicht)
	root.theme = UI.theme()
	root.alignment = BoxContainer.ALIGNMENT_END
	_layer.add_child(root)
	_msg = Label.new()
	_msg.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_msg.custom_minimum_size = Vector2(420, 0)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg.add_theme_color_override("font_color", UI.TXT)
	_msg.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_msg.add_theme_constant_override("outline_size", 5)
	_msg.visible = false
	root.add_child(_msg)
	_bar = PanelContainer.new()
	_bar.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.9), UI.LINE, 12, 8))
	root.add_child(_bar)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 8)
	_bar.add_child(hb)
	_status = Label.new()
	_status.text = T.t("Maggie")
	_status.add_theme_color_override("font_color", UI.ORG)
	hb.add_child(_status)
	for k in [["riechen", T.t("Riechen")], ["graben", T.t("Graben / Holen")], ["schluepfen", T.t("Durchschlüpfen")]]:
		var b := Button.new()
		b.text = k[1]
		b.focus_mode = Control.FOCUS_NONE
		b.tooltip_text = {"riechen": T.t("Maggie sucht Spuren und versteckte Wege"), "graben": T.t("Maggie gräbt etwas aus oder holt es dir"),
			"schluepfen": T.t("Maggie kriecht durch enge Stellen und öffnet den Weg")}[k[0]]
		b.pressed.connect(func(): befehl(k[0]))
		hb.add_child(b)
		_knoepfe[k[0]] = b
	_bar.visible = false


func _knopf_hilfe(f: String) -> void:
	for k in _knoepfe:
		var b: Button = _knoepfe[k]
		if k == f:
			UI.primary(b)
		else:
			for s_ in ["normal", "hover", "pressed", "disabled"]:
				b.remove_theme_stylebox_override(s_)
			b.remove_theme_color_override("font_color")


# ---- Speichern (der Rahmen ruft das beim Autosave am Rastplatz) ---------------------------------------------------------
func zustand() -> Dictionary:
	return {"geloest": geloest.keys(), "gefunden": gefunden.duplicate(), "fertig": fertig.keys()}


func laden(d: Dictionary) -> void:
	geloest = {}
	for k in d.get("geloest", []):
		geloest[str(k)] = true
	gefunden = []
	for k in d.get("gefunden", []):
		gefunden.append(str(k))
	fertig = {}
	for k in d.get("fertig", []):
		fertig[str(k)] = true
	if region != "":
		var r := region
		region = ""
		_on_region(r)


func kartenstuecke() -> int:
	var n := 0
	for g in gefunden:
		n += 1 if str(g).begins_with("kartenstueck_") else 0
	return n


func info() -> Dictionary:
	var hp := ppos(hund) if hund != null and is_instance_valid(hund) else Vector3.ZERO
	var sp := _spieler()
	var sts := []
	for st_ in stationen:
		var p: Vector3 = st_["p"]
		sts.append({"id": st_["id"], "f": st_["f"], "x": snappedf(p.x, 0.1), "z": snappedf(p.z, 0.1), "geloest": geloest.has(str(st_["id"]))})
	return {"region": region, "mitte": [snappedf(c.x, 0.1), snappedf(c.y, 0.1)], "idx": idx, "zustand": zustand_hund,
		"hund": [snappedf(hp.x, 0.1), snappedf(hp.z, 0.1)], "spieler": [snappedf(sp.x, 0.1), snappedf(sp.z, 0.1)],
		"stationen": sts, "gefunden": gefunden, "fertig": fertig.keys(), "stub": story is StubStory,
		"log": (story.log_.slice(-8) if story is StubStory else []),
		"helfer": helfer.info() if helfer != null else {}, "lite": lite}


# ---- Fernsteuerung für Tests ----------------------------------------------------------------------------------------------
static func control(main, d: Dictionary) -> Dictionary:
	var h = main.get_meta("maggie_hund") if main.has_meta("maggie_hund") else null
	if h != null and not is_instance_valid(h):
		h = null
	var mg = main.get("maggie")
	if h == null and mg != null and mg is Node and (mg as Node).has_node("maggie_hund"):
		h = (mg as Node).get_node("maggie_hund")
	var what := str(d.get("do", "info"))
	if what == "start":
		if main.scenes.data.get("bergtal", null) == null:
			return {"ok": false, "error": "Szene bergtal zuerst laden"}
		if h == null:
			var st_ = main.get("maggie")
			if st_ != null and st_ is Node and (st_ as Node).has_node("maggie_hund"):
				h = (st_ as Node).get_node("maggie_hund")
			else:
				h = (load("res://scripts/maggie_hund.gd") as GDScript).new()
				h.main = main
				main.add_child(h)
			main.set_meta("maggie_hund", h)
		if h.story == null:
			h.story = StubStory.new(h)
			h.verbinden(h.story)
		if h.story is StubStory:
			h.story.region = str(d.get("region", "herbst"))
			h.story.pos = null
		if h.story.has_method("region_aktiv") and h.story.region_aktiv() != "" and h.story.region_aktiv() != h.region:
			h._on_region(str(h.story.region_aktiv()))
		return {"ok": true, "info": h.info()}
	if h == null:
		return {"ok": false, "error": "Maggie ist nicht da (do: start)"}
	match what:
		"befehl":
			return h.befehl(str(d.get("f", "riechen")))
		"spieler":                                    # Stub: die Figur an einen Tal-Punkt stellen (x, z) oder zur Station
			if h.story is StubStory:
				var p := Vector3(float(d.get("x", 0)), 0, float(d.get("z", 0)))
				if d.has("station"):
					var st_ := h.aktuell() as Dictionary
					if not st_.is_empty():
						var key := str(d.get("station"))
						p = st_.get(key, st_["p"]) if key != "" else st_["p"]
				h.story.pos = p
			return {"ok": true, "info": h.info()}
		"blick":                                      # Tests: die Fensteransicht schaut Maggie von schräg oben an
			if h.hund == null or not is_instance_valid(h.hund):
				return {"ok": false, "error": "kein Hund"}
			var hw: Vector3 = (h.hund as Node3D).global_position
			var off: Array = d.get("off", [3.0, 1.8, 3.0])
			main.view_mode = 0
			main.view_cam.position = hw + Vector3(float(off[0]), float(off[1]), float(off[2]))
			main.view_cam.look_at(hw + Vector3(0, 0.3, 0))
			main.show_panel(false)
			return {"ok": true}
		"einstieg":                                   # Tests: wie das Signal einstieg_graben des Rahmens (x, z Tal)
			h._on_einstieg(h.W(h.G(float(d.get("x", 0)), float(d.get("z", 0)))))
			return {"ok": true}
		"loesen":
			var st2 := h.aktuell() as Dictionary
			if st2.is_empty():
				return {"ok": false, "error": "keine Station offen"}
			h._fertig(st2)
			return {"ok": true, "info": h.info()}
		"stop":
			main.remove_meta("maggie_hund")
			h._on_schluss()
			h.queue_free()
			return {"ok": true}
	return {"ok": true, "info": h.info()}


# =============================================================================================================================
class StubStory:
	## TODO verbinden mit maggie_story.gd (Paket S1): nur solange es den Rahmen noch nicht gibt – für Tests ohne S1.
	## Die Figur steht an «pos» (Tal), die Regionen sind feste Orte im Bergtal.
	signal region_gestartet(id: String)
	const MITTE := {"herbst": Vector2(-640, -200), "winter": Vector2(590, 360), "fruehling": Vector2(-110, -330), "sommer": Vector2(-530, 480)}   # wie maggie_story.gd
	var h
	var region := "herbst"
	var pos = null
	var log_: Array = []

	func _init(h_) -> void:
		h = h_

	func region_aktiv() -> String:
		return region

	func spieler_pos() -> Vector3:
		if pos is Vector3:
			return h.W(h.G((pos as Vector3).x, (pos as Vector3).z))
		return h.view_pos()

	func region_mitte(id: String) -> Vector3:
		var p: Vector2 = MITTE.get(id, Vector2(60, 20))
		return h.W(h.G(p.x, p.y))

	func kristall_bei_spieler() -> bool:
		return true

	func tipp(t: String) -> void:
		log_.append("tipp: " + t)

	func moveeye_sagt(t: String) -> void:
		log_.append("moveeye: " + t)
		h._zeige(t)

	func region_fertig(id: String) -> void:
		log_.append("fertig: " + id)

	func aufgabe_anmelden(id: String, text: String) -> void:
		log_.append("aufgabe: " + id + " " + text)

	func aufgabe_erledigt(id: String) -> void:
		log_.append("erledigt: " + id)

	func zukunftsbild_ort(_pos: Vector3, text: String) -> void:
		log_.append("zukunft: " + text)
