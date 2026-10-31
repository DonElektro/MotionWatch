extends RefCounted
## Bergtal-Abenteuer, Paket A3 (Daniel, 31.10.2026): Rätsel, Tagebuch des Grossvaters, Gegenstände des Grossvaters, Wege
## freischalten, Abzeichen, Hilfe-Stufen - eingebaut in die bestehenden Kapitel 1–5 (bergtal_abenteuer.gd ruft nur kleine
## Einhänge-Punkte auf: on_start, post_leg, on_ask, choose / after_choose, on_arrive, tick, paint_*, morning_xp, op, state).
##
##   * Karte + Kompass: nach dem ersten Wegstück jedes Kapitels findet man eine Tagebuchseite mit einer Peilung
##     («Von der Kapelle 195°, gut 600 m»). Der Ort wird auf der Landeskarte gesucht: drei nummerierte Punkte, Massstab, Norden
##     oben - antippen (oder die Knöpfe). Richtig = die nächste Tagebuchseite (+ Gegenstand), falsch = kleiner Umweg.
##   * Sternbild: in der Nacht (Zeitraffer) zeigt eine kleine Sternkarte den Nordhimmel (Grosser Wagen, Kleiner Wagen,
##     Kassiopeia, gedreht mit der Sternzeit von licht.gd). Welcher Stern ist der Polarstern? Er zeigt Norden - und damit die
##     Richtung zum nächsten Kartenstück. Den Sternhimmel selbst hat licht.gd / sky.gdshader schon (Sterne drehen mit der
##     Sternzeit) - hier nichts Neues in 3D, nur _draw (Lite-tauglich).
##   * Tagebuch des Grossvaters: Seiten 1–10 (je Kapitel zwei). Sie wiederholen nur, was Karte, Hinweise und Menschen schon
##     sagen (keine neuen Fakten über den Grossvater).
##   * Gegenstände: Hut (Kapitel 1, Alp - die Wirkung baut A2), Feldstecher (Kapitel 1, Peilung: Zoom 8× in der Fensteransicht,
##     ferne Hinweise beim Karte-Lesen, wirkt wie das Fernglas für die Wetterwarnung), Taschenuhr (Kapitel 2, Gumpisee: zeigt
##     die Sonnenzeit - Sonnen-Hinweise), Pickel (Kapitel 3, Ruine: vereiste Wege werden begehbar).
##   * Wege freischalten: Holzsteg im Riedmoos flicken (braucht «ersatzteil» → trockene Füsse), Seil am Fels (braucht «seil»,
##     bleibt hängen → kurzer Weg in Kapitel 5), Lawinenkegel (Kapitel 4, nur im Sommer).
##   * Abzeichen über das Entdecken-System (main.entdecken.register / mark_found, ids «berg.abenteuer.a3.*»).
##   * Hilfe = Schwierigkeit: Leicht (Pfeile: richtige Antwort markiert, Pfeil auf der Karte), Mittel (Tipp nach 20 s oder nach
##     einem Fehler, «Tipp jetzt» auf Wunsch), Schwer (keine Tipps). Gewählt nur mit der Schwierigkeit (Schritt «Schwierigkeit & Ziel»).
## Gespeichert im Spielstand des Abenteuers: P["a3_raetsel"] (fortschritt.json), der laufende Lauf in R["a3"].
## Gegenstände: hat(id) / gib(id) / nimm(id) gehen an das gemeinsame Inventar von Paket A4 (scripts/abenteuer_inventar.gd:
## Inv.hat / gib / finde / nimm; «feldstecher» liegt dort unter dem Schlüssel «fernglas»; Grossvaters Feldstecher ist der einzige im Abenteuer und
## gibt auch die Wetterwarnung einen Abschnitt früher).
## Für andere Pakete: ab.hilfe_stufe() bzw. ab.raetsel.hilfe() -> "leicht" | "normal" | "schwer" (A4: Essen/Trinken in Leicht aus).
## Ab 3D-4.74 (Daniel 31.10.2026) gibt es keine eigene Hilfe-Einstellung mehr: die Hilfe folgt der Schwierigkeit des Abenteuers
## (W/R["level"]: leicht = Pfeile, mittel = «normal» = Tipp nach Wartezeit, schwer = keine Hilfe). Unterwegs gibt es auf «Mittel»
## nur den Knopf «Tipp jetzt» (Tipp auf Wunsch, keine zweite Einstellung). Alte Spielstände: P["a3_raetsel"]["hilfe"] wird
## beim Laden einmal zur Schwierigkeit (bergtal_abenteuer._load → P["schwierigkeit"]).
## Steuerbefehl: {"action": "abenteuer", "do": "a3", "what": state | hilfe (value) | zoom | stern (value A/B/C) | nord |
##                gib (value) | badges}

const D = preload("res://scripts/bergtal_abenteuer_daten.gd")
const T = preload("res://scripts/i18n.gd")
const Bt = preload("res://scripts/bergtal.gd")
const Quality = preload("res://scripts/quality.gd")

const TIP_S := 20.0                          # Normal: so lange (echte Sekunden) bis zum Tipp
const MAG := 8.0                             # Feldstecher 8× (wie MAG_BINO in bergtal_aussicht.gd)
const ZOOM_S := 10.0

const LEVEL_HILFE := {"leicht": "leicht", "mittel": "normal", "schwer": "schwer"}     # Schwierigkeit -> Hilfe
const HILFE := {"leicht": ["Leicht", "Pfeile zeigen den Weg und die richtige Antwort."],
		"normal": ["Mittel", "Nach einer Weile (oder nach einem Fehler) kommt ein Tipp."],
		"schwer": ["Schwer", "Keine Tipps, keine Pfeile - nur Karte, Kompass und Sterne."]}
const HILFE_ORDER := ["leicht", "normal", "schwer"]

const ERBE := ["hut", "feldstecher", "taschenuhr", "pickel"]
const ITEM_NAME := {"hut": "Grossvaters Hut", "feldstecher": "Grossvaters Feldstecher", "taschenuhr": "Grossvaters Taschenuhr",
		"pickel": "Grossvaters Pickel", "seil": "Seil", "ersatzteil": "Ersatzteil (Brett mit Nägeln)"}

# die 10 Seiten des Tagebuchs (ungerade: mit einer Peilung - %d° und %d m kommen aus den Koordinaten der Karte)
const PAGES := ["«Von der Kapelle St. Jodern %d°, gut %d Meter: dort fällt der Bach aus der Schlucht. Wer zur Glocke will, steigt von dort hinauf zu den Weiden.»",
		"«Eine Glocke über einem Brunnen. Wer sie sucht, hört auf die Kühe, nicht auf den Kirchturm.»",
		"«Von der Alp Tschuggen %d°, etwa %d Meter: dort sammelt sich das Wasser, das zweimal gefallen ist.»",
		"«Steinmänner lesen: der flache Stein obenauf, die Kerbe zeigt den Weg. Auch im Nebel.»",
		"«Vom Gumpisee %d°, gut %d Meter: der alte Holzsteg über das Moos. Wer ihn flickt, kommt trocken hinüber.»",
		"«Lies die Karte mit der Sonne: am Morgen bekommt zuerst Licht, was hoch steht und gegen Osten frei ist.»",
		"«Von der alten Sennerei %d°, etwa %d Meter: der Wald aus Steinmännern. Einer schaut zurück.»",
		"«Ein Kästchen unter Felsblöcken, hoch oben: dort ist Platz für eine Nacht.»",
		"«Vom Biwak %d°, keine %d Meter: das Kreuz auf dem Tschingelspitz. Dahinter der Grat.»",
		"«Die Sonne steht in der Lücke im Fels. Was sie zuerst trifft, gehört der nächsten Seilschaft.»"]

# Karte + Kompass, je Kapitel: nach Wegstück «leg»; Bezugsort, Ziel und zwei andere Orte (Namen und Lage aus bergtal.gd PLACES /
# VIEWPOINTS); Seite mit der Peilung, Seite als Lohn, Gegenstand als Lohn
const KOMPASS := {1: {"leg": 0, "ref": ["Kapelle St. Jodern", Vector2(210, -700)], "target": ["Tüfelsschlund (Wasserfall)", Vector2(42, -92)],
			"decoys": [["Gumpisee", Vector2(-60, -390)], ["Schattwald", Vector2(-60, -650)]], "page": 1, "reward": 2, "item": "feldstecher",
			"found": "Beim Wegweiser über dem Wasserfall steht ein Blechkästchen. Darin: ein alter Feldstecher (8×) und die nächste Seite."},
		2: {"leg": 0, "ref": ["Alp Tschuggen", Vector2(60, 0)], "target": ["Gumpisee", Vector2(-60, -390)],
			"decoys": [["Gumpifall mit Höhle", Vector2(214, -330)], ["Riedmoos (Wollgras)", Vector2(-470, -265)]], "page": 3, "reward": 4, "item": "",
			"found": "Am Seeufer, unter einem flachen Stein: die nächste Seite, in Wachstuch gewickelt wie die Kartenstücke."},
		3: {"leg": 0, "ref": ["Gumpisee", Vector2(-60, -390)], "target": ["Holzsteg am Schwarzseeli", Vector2(-612, -262)],
			"decoys": [["Ruine Altstafel", Vector2(-830, -215)], ["Seeblick Gumpisee", Vector2(-250, -470)]], "page": 5, "reward": 6, "item": "",
			"found": "Am Anfang des alten Holzstegs steckt die nächste Seite zwischen zwei Brettern."},
		4: {"leg": 0, "ref": ["Alte Sennerei Chäsgaden", Vector2(-700, -130)], "target": ["Steimandli-Wald", Vector2(-650, 430)],
			"decoys": [["Gratspitz", Vector2(-625, 125)], ["Rüfi (Geröllhalde)", Vector2(-380, 120)]], "page": 7, "reward": 8, "item": "",
			"found": "Im Steimandli-Wald liegt unter einem Steinmann die nächste Seite."},
		5: {"leg": 0, "ref": ["Biwak Chüebodehorn", Vector2(-520, 560)], "target": ["Tschingelspitz (Gipfel West)", Vector2(-790, 520)],
			"decoys": [["Steimandli-Wald", Vector2(-650, 430)], ["Gratspitz", Vector2(-625, 125)]], "page": 9, "reward": 10, "item": "",
			"found": "Im Gipfelbuch beim Kreuz liegt die letzte Seite."}}

# am Ziel eines Kapitels: ein Gegenstand des Grossvaters (+ was es zum Weiterkommen braucht, falls ein anderes Paket es noch nicht gibt)
const ARRIVE := {1: ["hut", "An einem Haken im Stall der Alp hängt ein alter Hut. Im Hutband steckt eine Ecke derselben vergilbten Karte - es ist Grossvaters Hut."],
		2: ["taschenuhr", "Neben dem Eisenring im Block: eine Taschenuhr, in Wachstuch gewickelt wie das Kartenstück. Sie geht noch - aber sie zeigt nicht die Uhrzeit, sondern die Sonnenzeit."],
		3: ["pickel", "In einer Nische der Mauer lehnt ein alter Pickel mit Holzstiel, in Wachstuch gewickelt wie die Kartenstücke. Damit kommt man auch über Eis."],
		4: ["seil", "Im Biwak hängt ein langes Seil am Haken. Ein Zettel daran: «Für die nächste Seilschaft.»"]}
const NOTFALL := ["seil"]                    # zweiter (Notfall-)Ort, nur in «Leicht» (Daniel 31.10.): das Seil liegt sonst nur in der
                                            # alten Sennerei (A4 FUNDE), das Ersatzteil sonst nur beim A2-Botendienst q_ersatzteil
const ERSATZ_TEXT := "Neben der Seite liegt ein Brett mit Nägeln, sauber eingepackt - genau so eins fehlt am Steg."

# ferne Hinweise mit dem Feldstecher (beim Karte lesen): was man von weitem sieht (die Antwort, die Karte und Menschen schon nennen)
const FERN := {1: "Mit dem Feldstecher siehst du oben bei den Weiden einen Brunnentrog, daneben Kühe.",
		2: "Mit dem Feldstecher siehst du unten am Gumpisee einen grossen Block im Wasser.",
		3: "Mit dem Feldstecher siehst du oben im Westen Mauerreste, die schon in der Sonne liegen.",
		4: "Mit dem Feldstecher siehst du hoch oben eine kleine Blechhütte unter Felsblöcken.",
		5: "Mit dem Feldstecher siehst du hinter dem Grat einen kleinen See glitzern."}

# vereiste Wege (Kapitel -> [Gabelung (Stufe), Seite, Jahreszeiten]): ohne Pickel nicht begehbar
const ICE := {4: [2, 0, ["winter", "fruehling"], "Die Rinne über die Rüfi ist vereist."],
		5: [2, 0, ["winter", "fruehling", "herbst"], "Am Gipfelhang liegt Blankeis."]}
const LAWINE_PTS := [Vector2(-700, -130), Vector2(-705, 40), Vector2(-680, 240), Vector2(-650, 430)]
const SEIL_PTS := [Vector2(-700, 470), Vector2(-790, 462), Vector2(-870, 450)]

const BADGES := [["tagebuch", "Abzeichen: Grossvaters Tagebuch", "Alle zehn Seiten aus Grossvaters Tagebuch gefunden."],
		["kompass", "Abzeichen: Kartenleser", "Alle fünf Peilungen auf der Landeskarte gefunden."],
		["stern", "Abzeichen: Polarstern", "In der Nacht den Polarstern gefunden - er zeigt immer nach Norden."],
		["erbe", "Abzeichen: Grossvaters Ausrüstung", "Hut, Feldstecher, Taschenuhr und Pickel gefunden."],
		["wege", "Abzeichen: Wegmacher", "Den Steg geflickt, das Seil am Fels befestigt und über den Lawinenkegel gegangen."],
		["schwer", "Abzeichen: Ohne Hilfe", "Ein Kapitel auf der Schwierigkeit Schwer geschafft, ohne eine falsche Antwort."]]

# Sterne (Rektaszension h, Deklination °, Grösse) - Yale Bright Star Catalogue (J2000, gerundet)
const STARS := {"polaris": [2.53, 89.26, 2.0], "kochab": [14.85, 74.16, 2.1], "pherkad": [15.35, 71.83, 3.0], "yildun": [17.54, 86.59, 4.4],
		"eps_umi": [16.77, 82.04, 4.2], "zeta_umi": [15.73, 77.79, 4.3], "eta_umi": [16.29, 75.76, 5.0],
		"dubhe": [11.06, 61.75, 1.8], "merak": [11.03, 56.38, 2.4], "phecda": [11.90, 53.69, 2.4], "megrez": [12.26, 57.03, 3.3],
		"alioth": [12.90, 55.96, 1.8], "mizar": [13.40, 54.93, 2.2], "alkaid": [13.79, 49.31, 1.9],
		"caph": [0.15, 59.15, 2.3], "schedar": [0.68, 56.54, 2.2], "gam_cas": [0.95, 60.72, 2.2], "ruchbah": [1.43, 60.24, 2.7], "segin": [1.91, 63.67, 3.4]}
const LINES := [["dubhe", "merak"], ["merak", "phecda"], ["phecda", "megrez"], ["megrez", "dubhe"], ["megrez", "alioth"], ["alioth", "mizar"], ["mizar", "alkaid"],
		["polaris", "yildun"], ["yildun", "eps_umi"], ["eps_umi", "zeta_umi"], ["zeta_umi", "eta_umi"], ["eta_umi", "pherkad"], ["pherkad", "kochab"], ["kochab", "zeta_umi"],
		["caph", "schedar"], ["schedar", "gam_cas"], ["gam_cas", "ruchbah"], ["ruchbah", "segin"]]
const STAR_NAME := {"polaris": "Polarstern", "kochab": "Kochab (Kleiner Wagen)", "dubhe": "Dubhe (Grosser Wagen)"}
const STAR_CAND := ["polaris", "kochab", "dubhe"]

var ab                                       # bergtal_abenteuer.gd
var main
var pages_open := false
var _zoom := {}                              # {eye, look, until}
var _ov: Control = null                      # the overlay on the map
var _reg_t := 0.0
var _tip_seq := -1


func _init(a) -> void:
	ab = a
	main = a.main


static func _lite() -> bool:
	return Quality.lite()


# =======================================================================================================================
# the saved part (P["a3_raetsel"]) and the run (R["a3"])
# =======================================================================================================================
func S() -> Dictionary:
	if not ab.P.has("a3_raetsel") or not ab.P["a3_raetsel"] is Dictionary:
		ab.P["a3_raetsel"] = {}
	var s: Dictionary = ab.P["a3_raetsel"]
	for k in [["pages", []], ["badges", {}], ["wege", {}], ["kompass", []], ["stern", []]]:
		if not s.has(k[0]):
			s[k[0]] = k[1].duplicate() if k[1] is Array or k[1] is Dictionary else k[1]
	return s


func RR() -> Dictionary:
	if ab.R.is_empty():
		return {}
	if not ab.R.has("a3"):
		ab.R["a3"] = {"xp": 0, "pages": [], "items": [], "badges": [], "wrong": 0, "ask_t": 0.0, "star": "", "star_wrong": 0}
	return ab.R["a3"]


func hilfe() -> String:
	"""die Hilfe folgt der Schwierigkeit (unterwegs die des Laufs, sonst die gewählte; A6: Kinder-Modus = immer Leicht)"""
	if ab.has_method("kinder") and ab.kinder():
		return "leicht"
	var lv := str(ab.R.get("level", ab.W["level"])) if not ab.R.is_empty() else str(ab.W["level"])
	return str(LEVEL_HILFE.get(lv, "normal"))


static func level_of(h: String) -> String:
	"""Hilfe-Stufe (auch aus alten Spielständen) -> Schwierigkeit"""
	for k in LEVEL_HILFE:
		if LEVEL_HILFE[k] == h:
			return k
	return "mittel"


func set_hilfe(h: String) -> void:
	"""alter Steuerbefehl «hilfe»: setzt jetzt die Schwierigkeit (nur vor dem Start)"""
	if HILFE.has(h) and ab.R.is_empty():
		ab.op({"do": "pick", "key": "level", "value": level_of(h)})


func hilfe_stufe() -> String:
	return hilfe()


# ---- the inventory: abenteuer_inventar.gd of package A4 (static hat / gib / finde / nimm) ---------------------------------
const Inv = preload("res://scripts/abenteuer_inventar.gd")


func _inv():
	if Inv.ab == null:
		Inv.verbinde(ab)
	return Inv


func hat(id: String) -> bool:
	return bool(_inv().hat(id))


func gib(id: String) -> void:
	if id == "ersatzteil":
		_inv().gib(id, 1)                                # used up at the footbridge (Rucksack of this tour)
	elif not hat(id):
		_inv().finde(id)                                 # stays for all chapters (feldstecher / seil / grandfather's things / pages)
	if not ab.R.is_empty() and not id in RR()["items"]:
		RR()["items"].append(id)
	ab._save()


func nimm(id: String) -> void:
	_inv().nimm(id, 1)
	ab._save()


func page_text(n: int) -> String:
	"""a page of the diary (1 … 10); the odd ones with the bearing from the map"""
	var tx: String = T.t(PAGES[clampi(n, 1, 10) - 1])
	if n % 2 == 1:
		var k: Dictionary = KOMPASS[int((n + 1) / 2.0)]
		var b := bearing(k["ref"][1], k["target"][1])
		return tx % [int(b.x), int(b.y)]
	return tx


func _give_page(n: int) -> bool:
	var pg: Array = S()["pages"]
	var new := not n in pg
	if new:
		pg.append(n)
		pg.sort()
		if not ab.R.is_empty():
			RR()["pages"].append(n)
			RR()["xp"] = int(RR()["xp"]) + 10
		gib("tagebuchseite_%d" % n)
	ab._diary("a3_page", T.t("Tagebuch des Grossvaters, Seite %d") % n, page_text(n))
	if pg.size() >= 10:
		badge("tagebuch")
	return new


static func bearing(from: Vector2, to: Vector2) -> Vector2:
	"""(Peilung in Grad ab Norden im Uhrzeigersinn, auf 5° gerundet; Distanz in m, auf 50 m gerundet) - Tal: x = Osten, z = Süden"""
	var d := to - from
	var az := fposmod(rad_to_deg(atan2(d.x, -d.y)), 360.0)
	return Vector2(fposmod(round(az / 5.0) * 5.0, 360.0), maxf(50.0, round(d.length() / 50.0) * 50.0))


# =======================================================================================================================
# hooks from bergtal_abenteuer.gd
# =======================================================================================================================
func on_start() -> void:
	ab.R.erase("a3")
	var r := RR()
	r["hilfe0"] = hilfe()
	_zoom = {}
	_ensure_badges()


func post_leg(i: int) -> bool:
	"""after leg i: the page with the bearing (once per run) - true = the adventure waits for us"""
	var ch := int(ab.R.get("chapter", 1))
	if not KOMPASS.has(ch) or int(KOMPASS[ch]["leg"]) != i or ab.R["events_done"].has("a3k%d" % i):
		return false
	ab.R["events_done"]["a3k%d" % i] = true
	var k: Dictionary = KOMPASS[ch]
	var n: int = int(k["page"])
	_give_page(n)
	ab._ask("a3_seite", T.t("Eine Seite aus Grossvaters Tagebuch"), T.t("Unter einem Stein am Weg, in Wachstuch gewickelt: Seite %d.") % n + "\n" + page_text(n),
			[["ok", T.t("Die Peilung auf der Karte suchen")], ["skip", T.t("Später - weitergehen")]], {"a3_leg": i})
	return true


func _ask_kompass(i: int, lead := "") -> void:
	var ch := int(ab.R["chapter"])
	var k: Dictionary = KOMPASS[ch]
	var b := bearing(k["ref"][1], k["target"][1])
	var cands := _cands(ch)
	var opts := []
	for j in range(cands.size()):
		var c: Array = cands[j]
		opts.append([str(j), ("→ " if hilfe() == "leicht" and bool(c[2]) else "") + "%d · %s" % [j + 1, T.t(str(c[0]))]])
	opts.append(["skip", T.t("Auslassen")])
	var tx := (lead + "\n" if lead != "" else "") + T.t("Peilung %d° und %d m ab «%s». Norden ist auf der Karte oben, der Strich unten links ist 500 m lang. Welcher Punkt ist es? (auf der Karte antippen)") % [int(b.x), int(b.y), T.t(str(k["ref"][0]))]
	ab._ask("a3_kompass", T.t("Karte und Kompass"), tx, opts, {"a3_leg": i})


func _cands(ch: int) -> Array:
	"""the three places of the bearing puzzle [name, xz, right], in an order fixed by the seed"""
	var k: Dictionary = KOMPASS[ch]
	var out := [[k["target"][0], k["target"][1], true], [k["decoys"][0][0], k["decoys"][0][1], false], [k["decoys"][1][0], k["decoys"][1][1], false]]
	var r := RandomNumberGenerator.new()
	r.seed = int(ab.R.get("seed", 1)) + 77
	for j in range(2, 0, -1):
		var q := r.randi() % (j + 1)
		var t = out[j]
		out[j] = out[q]
		out[q] = t
	return out


func on_ask() -> void:
	"""a question / message of the adventure is shown: the help level, the far hints, the pocket watch, ice and the ways"""
	var pe: Dictionary = ab.R.get("pending", {})
	if pe.is_empty():
		return
	var r := RR()
	r["ask_t"] = main.now()
	r["tip"] = ""
	var ch := int(ab.R.get("chapter", 1))
	var si := int(ab.R.get("stage", 0))
	var st: Dictionary = ab.chapter()["stages"][si] if si < (ab.chapter()["stages"] as Array).size() else {}
	match str(pe["kind"]):
		"read":
			var rd: Dictionary = st.get("read", {})
			if rd.is_empty():
				return
			r["tip"] = T.t(str(rd["hint"]))
			if hat("feldstecher") and FERN.has(ch):
				pe["text"] = str(pe["text"]) + "\n" + T.t(FERN[ch])
			if hilfe() == "leicht":
				for o in pe["options"]:
					if bool(rd["options"][int(o[0])][1]):
						o[1] = "→ " + str(o[1])
		"info":
			if pe.get("detour", false) and hilfe() == "schwer":
				pe["text"] = T.t("Hier ist nichts - das war der falsche Ort.")
			elif str(st.get("clue", "")) == "sun" and hat("taschenuhr"):
				pe["text"] = str(pe["text"]) + "\n" + _watch_text(true)
		"a3_kompass":
			var b := bearing(KOMPASS[ch]["ref"][1], KOMPASS[ch]["target"][1])
			r["tip"] = T.t("%d° heisst: von Norden im Uhrzeigersinn - 90° ist Osten, 180° Süden, 270° Westen. Vom Bezugsort in diese Richtung, dann %d m (der Strich unten ist 500 m).") % [int(b.x), int(b.y)]
		"fork":
			_fork_ask(ch, si, pe)
	if hilfe() == "leicht" or (hilfe() == "normal" and bool(pe.get("a3_wrong", false))):
		r["ask_t"] = -1000.0


func _fork_ask(ch: int, si: int, pe: Dictionary) -> void:
	var opts: Array = pe["options"]
	var notes := []
	var season := str(ab.R.get("season", "sommer"))
	var w: Dictionary = S()["wege"]
	if ICE.has(ch) and int(ICE[ch][0]) == si and season in ICE[ch][2] and not ab.kinder():   # A6: Kinder-Modus ohne Eis
		var side := str(ICE[ch][1])
		for j in range(opts.size() - 1, -1, -1):
			if str(opts[j][0]) == side:
				if hat("pickel"):
					opts[j][1] = str(opts[j][1]) + "\n" + T.t("Vereist - mit Grossvaters Pickel begehbar.")
				else:
					opts.remove_at(j)
					notes.append(T.t(ICE[ch][3]) + " " + T.t("Ohne Pickel ist dieser Weg zu gefährlich."))
	if ch == 3 and si == 2:
		if bool(w.get("steg", false)):
			for o in opts:
				if str(o[0]) == "0":
					o[1] = str(o[1]).replace(T.t("Kurz: quer durchs Riedmoos (nasse Füsse)"), T.t("Kurz: über den geflickten Holzsteg (trockene Füsse)"))
		elif hat("ersatzteil"):
			opts.append(["a3steg", T.t("Den alten Holzsteg im Riedmoos flicken (Ersatzteil, 15 Min.) - dann trockene Füsse")])
		else:
			notes.append(T.t("Der alte Holzsteg im Riedmoos ist kaputt - mit einem Ersatzteil liesse er sich flicken."))
	if ch == 4 and si == 2:
		if season == "sommer":
			var li: Dictionary = ab.leg_info(LAWINE_PTS, [])
			opts.append(["a3lawine", "%s\n%s · %s" % [T.t("Mittel: über den Lawinenkegel (nur im Sommer)"), ab.leg_text(li), T.t("Kraft −%d") % int(round(float(li["cost"]) * ab._cost_f()))]])
		else:
			notes.append(T.t("Über den Lawinenkegel geht es nur im Sommer, wenn der alte Schnee fest ist."))
	if ch == 5 and si == 2 and not ab.kinder():                  # A6: Kinder-Modus ohne Felsstufe
		var li2: Dictionary = ab.leg_info(SEIL_PTS, ["steep"])
		var info2 := "\n%s · %s" % [ab.leg_text(li2), T.t("Kraft −%d") % int(round(float(li2["cost"]) * ab._cost_f()))]
		if bool(w.get("seil", false)):
			opts.append(["a3seil", T.t("Kurz: am Seil durch die Felsstufe") + info2])
		elif hat("seil"):
			opts.append(["a3seil", T.t("Das Seil am Haken im Fels befestigen und durch die Felsstufe (10 Min.)") + info2])
		else:
			notes.append(T.t("In der Felsstufe steckt ein alter Haken - mit einem Seil gäbe es hier einen kurzen Weg."))
	if not notes.is_empty():
		pe["text"] = str(pe["text"]) + "\n" + "\n".join(notes)


func choose(pe: Dictionary, v: String) -> bool:
	"""our own questions (a3_*) and our own fork sides (a3…) - true = handled"""
	var kind := str(pe.get("kind", ""))
	var r := RR()
	r["wet_before"] = bool(ab.R.get("wet", false))
	var ch := int(ab.R.get("chapter", 1))
	var i := int(pe.get("a3_leg", 0))
	match kind:
		"a3_seite":
			if v == "skip":
				ab._diary("a3", T.t("Peilung ausgelassen"), T.t("Die Seite kommt in den Rucksack."))
				ab._post_leg(i)
			else:
				_ask_kompass(i)
			return true
		"a3_kompass":
			if v == "skip":
				ab._diary("a3", T.t("Peilung ausgelassen"), T.t("Die Seite kommt in den Rucksack."))
				ab._post_leg(i)
				return true
			var cands := _cands(ch)
			var c: Array = cands[clampi(int(v), 0, cands.size() - 1)]
			if bool(c[2]):
				_kompass_ok(ch, i)
			else:
				r["wrong"] = int(r["wrong"]) + 1
				r["kwrong"] = int(r.get("kwrong", 0)) + 1
				ab._diary("a3", T.t("Falsch gepeilt"), T.t("Bei «%s» ist nichts - ein kleiner Umweg.") % T.t(str(c[0])))
				ab._pause(0.15, false)
				_ask_kompass(i, T.t("Bei «%s» ist nichts. Nochmals peilen.") % T.t(str(c[0])))
				ab.R["pending"]["a3_wrong"] = true
				on_ask()
			return true
		"a3_info":
			ab._post_leg(i)
			return true
		"fork":
			if not v.begins_with("a3"):
				return false
			var st_i := int(ab.R["stage"])
			match v:
				"a3steg":
					nimm("ersatzteil")
					S()["wege"]["steg"] = true
					ab._pause(0.25, false)
					ab._diary("a3_weg", T.t("Steg geflickt"), T.t("Das neue Brett sitzt, die Nägel halten. Über den Holzsteg kommt man jetzt trocken durchs Riedmoos."))
					ab._snap_later(T.t("Steg geflickt"), "view")
					_check_wege()
					ab._save()
					ab._advance()                            # the fork again - now with the dry way
				"a3lawine":
					S()["wege"]["lawine"] = true
					ab.R["fork_" + str(st_i)] = 2
					ab._diary("fork", T.t("Weggabelung"), T.t("Über den Lawinenkegel: der alte Schnee ist fest und trägt."))
					_check_wege()
					ab._save()
					ab._start_leg(st_i, LAWINE_PTS, [], T.t("Über den Lawinenkegel"))
				"a3seil":
					if not bool(S()["wege"].get("seil", false)):
						S()["wege"]["seil"] = true
						ab._pause(0.17, false)
						ab._diary("a3_weg", T.t("Seil am Fels"), T.t("Das Seil hängt jetzt fest am alten Haken - es bleibt für alle, die nach dir kommen."))
						ab._snap_later(T.t("Seil am Fels"), "view")
					ab.R["fork_" + str(st_i)] = 3
					ab._diary("fork", T.t("Weggabelung"), T.t("Am Seil durch die Felsstufe"))
					_check_wege()
					ab._save()
					ab._start_leg(st_i, SEIL_PTS, ["steep"], T.t("Am Seil durch die Felsstufe"))
			return true
	return false


func after_choose(pe: Dictionary, v: String) -> void:
	var kind := str(pe.get("kind", ""))
	var ch := int(ab.R.get("chapter", 1))
	var r := RR()
	if kind == "fork" and not v.begins_with("a3"):
		var si := int(ab.R["stage"])
		if ch == 3 and si == 2 and v == "0" and bool(S()["wege"].get("steg", false)):
			ab.R["wet"] = bool(r.get("wet_before", false))
		if ICE.has(ch) and int(ICE[ch][0]) == si and str(ICE[ch][1]) == v and str(ab.R.get("season", "")) in ICE[ch][2] and not ab.kinder():
			ab._diary("a3_weg", T.t("Grossvaters Pickel"), T.t("Mit dem Pickel schlägst du Stufen ins Eis - Schritt für Schritt, sicher."))


func _kompass_ok(ch: int, i: int) -> void:
	var k: Dictionary = KOMPASS[ch]
	var r := RR()
	if int(r.get("kwrong", 0)) == 0:
		r["xp"] = int(r["xp"]) + 25
	var kp: Array = S()["kompass"]
	if not ch in kp:
		kp.append(ch)
	if kp.size() >= 5:
		badge("kompass")
	var lines := [T.t("Richtig gepeilt: %s.") % T.t(str(k["target"][0])), T.t(str(k["found"]))]
	_give_page(int(k["reward"]))
	lines.append(T.t("Seite %d:") % int(k["reward"]) + " " + page_text(int(k["reward"])))
	var it := str(k["item"])
	if it != "" and not hat(it):
		gib(it)
		lines.append(T.t("Neu: %s.") % T.t(ITEM_NAME[it]))
	if ch == 3 and hilfe() == "leicht" and not hat("ersatzteil") and not bool(S()["wege"].get("steg", false)):
		gib("ersatzteil")                                # Notfall-Ort nur in «Leicht» (Daniel 31.10.); sonst nur A2-Botendienst q_ersatzteil
		lines.append(T.t(ERSATZ_TEXT))
	_check_erbe()
	ab._diary("a3", T.t("Karte und Kompass"), " ".join(lines.slice(0, 2)))
	ab._snap_later(T.t("Karte und Kompass"), "view")
	ab._ask("a3_info", T.t("Karte und Kompass"), "\n".join(lines), [["ok", T.t("Weiter")]], {"a3_leg": i})


func on_arrive() -> void:
	var ch := int(ab.R.get("chapter", 1))
	if not ARRIVE.has(ch):
		return
	var it := str(ARRIVE[ch][0])
	if hat(it) or (it in NOTFALL and hilfe() != "leicht"):
		return
	gib(it)
	RR()["arrive"] = [it, T.t(ARRIVE[ch][1])]
	ab._diary("a3_item", T.t(ITEM_NAME[it]), T.t(ARRIVE[ch][1]))
	main.start_info = T.t("Gefunden: %s") % T.t(ITEM_NAME[it])
	_check_erbe()


func morning_xp(arrived: bool) -> int:
	"""the morning: experience of this package; the badge «Ohne Hilfe»"""
	var r := RR()
	if arrived and str(r.get("hilfe0", "")) == "schwer" and hilfe() == "schwer" \
			and int(r.get("wrong", 0)) == 0 and int(ab.R.get("reads_wrong", 0)) == 0:
		badge("schwer")
	return int(r.get("xp", 0))


func _check_erbe() -> void:
	if ERBE.all(func(x): return hat(x)):
		badge("erbe")


func _check_wege() -> void:
	var w: Dictionary = S()["wege"]
	if bool(w.get("steg", false)) and bool(w.get("seil", false)) and bool(w.get("lawine", false)):
		badge("wege")


# ---- badges (the discovery system: main.entdecken) ---------------------------------------------------------------------
func _ensure_badges() -> void:
	var ed = main.get("entdecken")
	if ed == null or not ed.has_method("register"):
		return
	var never := func(): return false
	for bd in BADGES:
		var id := "berg.abenteuer.a3." + str(bd[0])
		if not ed.items.has(id):
			ed.register(id, {"scene": "bergtal", "title": T.t(str(bd[1])), "short_text": T.t(str(bd[2])), "hint": T.t("Ein Abzeichen aus dem Bergtal-Abenteuer."),
					"icon": "🏅", "position": Vector3.ZERO, "radius": 1.0, "kind": "szene", "los": false, "active": never})


func badge(id: String) -> void:
	var b: Dictionary = S()["badges"]
	if b.has(id):
		return
	b[id] = Time.get_datetime_string_from_system().substr(0, 16)
	if not ab.R.is_empty():
		RR()["badges"].append(id)
		RR()["xp"] = int(RR()["xp"]) + 50
	ab._save()
	for bd in BADGES:
		if bd[0] == id:
			main.start_info = "🏅 " + T.t(str(bd[1]))
			ab._diary("a3_badge", T.t(str(bd[1])), T.t(str(bd[2])))
	_ensure_badges()
	var ed = main.get("entdecken")
	if ed != null and ed.has_method("mark_found"):
		ed.mark_found("berg.abenteuer.a3." + id, "api")


# =======================================================================================================================
# the pocket watch (solar time) and the binoculars (zoom)
# =======================================================================================================================
func solar_h(h: float) -> float:
	"""true solar time (wahre Ortszeit) at the clock time h - same formula as sun_at (NOAA): 12:00 = the sun in the south"""
	var lo: float = main.ort_lon if main.ort_lon != 0.0 else 8.2
	var doy: int = main.day_of_year()
	var tz := 2.0 if doy >= 88 and doy < 300 else 1.0
	var hu := h - tz
	var g := TAU / 365.0 * (doy - 1 + (hu - 12.0) / 24.0)
	var eqt := 229.18 * (0.000075 + 0.001868 * cos(g) - 0.032077 * sin(g) - 0.014615 * cos(2 * g) - 0.040849 * sin(2 * g))
	return fposmod((hu * 60.0 + eqt + 4.0 * lo) / 60.0, 24.0)


func _watch_text(long := false) -> String:
	var h: float = main.hour()
	var sh := solar_h(h)
	var noon := fposmod(h + (12.0 - sh), 24.0)
	var t := T.t("Taschenuhr: Sonnenzeit %s (Mittag, Sonne im Süden: %s Uhr)") % [ab.hm(sh), ab.hm(noon)]
	if long:
		t += " " + T.t("Um 12 Uhr Sonnenzeit steht die Sonne genau im Süden, um 6 Uhr etwa im Osten, um 18 Uhr etwa im Westen.")
	return t


func zoom(to = null, from = null) -> Dictionary:
	"""the binoculars (8×): the window view from where you are toward the goal of the chapter (or a given place)"""
	if not hat("feldstecher"):
		return {"ok": false, "error": "kein Feldstecher"}
	if not _zoom.is_empty():
		_zoom_off()
		return {"ok": true, "zoom": false}
	var b = ab.bt()
	if b == null or ab.R.is_empty():
		return {"ok": false, "error": "not bergtal"}
	var p: Vector2 = from if from is Vector2 else ab.R["pos"]
	var q: Vector2
	if to is Vector2:
		q = to
	else:
		var last: Dictionary = ab.chapter()["stages"][-1]
		q = last["walk"][-1] if last.has("walk") else p + Vector2(0, -100)
	if q.distance_to(p) < 5.0:
		q = p + Vector2(0, -100)
	var eye: Vector3 = b.WG(p.x, p.y, 1.7)
	var look: Vector3 = b.WG(q.x, q.y, 2.0)
	main._to_free_view()
	if main.fly_tw != null:
		main.fly_tw.kill()
	_zoom = {"eye": eye, "look": look, "until": main.now() + ZOOM_S, "fov": rad_to_deg(2.0 * atan(tan(deg_to_rad(35.0)) / MAG))}
	if not RenderingServer.frame_pre_draw.is_connected(_pre_draw):
		RenderingServer.frame_pre_draw.connect(_pre_draw)
	main.start_info = T.t("Feldstecher (8×): Blick zum Ziel - %d m weit.") % int(p.distance_to(q))
	return {"ok": true, "zoom": true, "fov": snappedf(float(_zoom["fov"]), 0.1), "dist": int(p.distance_to(q))}


func _pre_draw() -> void:
	if _zoom.is_empty() or main == null or not is_instance_valid(main):
		return
	if main.now() > float(_zoom["until"]):
		_zoom_off()
		return
	main.view_cam.global_position = _zoom["eye"]
	main.view_cam.look_at(_zoom["look"], Vector3.UP)
	main.view_cam.fov = float(_zoom["fov"])


func _zoom_off() -> void:
	_zoom = {}
	if RenderingServer.frame_pre_draw.is_connected(_pre_draw):
		RenderingServer.frame_pre_draw.disconnect(_pre_draw)
	if main != null and is_instance_valid(main):
		main.view_cam.fov = 70.0


# =======================================================================================================================
# the star puzzle (in the night)
# =======================================================================================================================
func _lst() -> float:
	var l = main.get("licht")
	if l != null and l.get("sky") is Dictionary and (l.sky as Dictionary).has("lst"):
		return float(l.sky["lst"])
	# without licht.gd: GMST from the day of the year (rough, ±1°)
	var doy: int = main.day_of_year()
	return fposmod(100.46 + 0.9856 * (doy - 1) + 15.0 * (main.hour() - 1.0) + 8.2, 360.0)


func stars_visible() -> bool:
	var l = main.get("licht")
	var k := 1.0
	if l != null and l.get("sky") is Dictionary:
		k = float((l.sky as Dictionary).get("stars", 1.0))
	return main.is_dark() and k > 0.15 and main.weather in ["clear", ""]


func star_cands() -> Array:
	var out: Array = STAR_CAND.duplicate()
	var r := RandomNumberGenerator.new()
	r.seed = int(ab.R.get("seed", 1)) + 99
	for j in range(2, 0, -1):
		var q := r.randi() % (j + 1)
		var t = out[j]
		out[j] = out[q]
		out[q] = t
	return out


func star_answer(letter: String) -> Dictionary:
	if ab.R.is_empty() or ab.step != 6 or str(RR().get("star", "")) == "ok":
		return {"ok": false, "error": "no star puzzle now"}
	if not stars_visible():
		return {"ok": false, "error": "no stars visible"}
	var j := "ABC".find(letter.to_upper())
	if j < 0:
		return {"ok": false, "error": "A, B or C"}
	var id: String = star_cands()[j]
	var r := RR()
	if id == "polaris":
		r["star"] = "ok"
		r["xp"] = int(r["xp"]) + (40 if int(r["star_wrong"]) == 0 else 20)
		var sl: Array = S()["stern"]
		if not int(ab.R["chapter"]) in sl:
			sl.append(int(ab.R["chapter"]))
		ab._diary("a3_star", T.t("Der Polarstern"), star_result())
		badge("stern")
		ab._save()
	else:
		r["star_wrong"] = int(r["star_wrong"]) + 1
		r["wrong"] = int(r["wrong"]) + 1
		r["star_msg"] = T.t("Das ist %s. Nochmals schauen.") % T.t(STAR_NAME[id])
	ab._changed()
	return {"ok": true, "right": id == "polaris", "star": id}


func star_result() -> String:
	var ch := int(ab.R.get("chapter", 1))
	var t := T.t("Richtig! Der Polarstern steht immer im Norden.")
	if ch < 5:
		var nxt: Dictionary = D.CHAPTERS[ch]
		var last: Dictionary = nxt["stages"][-1]
		var c: Vector2 = ab.R.get("camp_xz", ab.R["pos"])
		var q: Vector2 = last["walk"][-1]
		var az := fposmod(rad_to_deg(atan2(q.x - c.x, -(q.y - c.y))), 360.0)
		t += " " + T.t("Das nächste Kartenstück liegt von hier aus im %s.") % T.t(ab.dir_word(az))
	return t


func look_north() -> Dictionary:
	"""the window view turns to the northern sky (at the height of the pole star = the latitude)"""
	var b = ab.bt()
	if b == null:
		return {"ok": false}
	_zoom_off()
	main._to_free_view()
	if main.fly_tw != null:
		main.fly_tw.kill()
	var la: float = main.ort_lat if main.ort_lat != 0.0 else 46.8
	var eye: Vector3 = main.view_cam.global_position
	var north: Vector3 = (b.tal.basis * Vector3(0, 0, -1)).normalized()
	var dir := (north + Vector3(0, tan(deg_to_rad(la)), 0)).normalized()
	var start: Transform3D = main.view_cam.global_transform
	var end := Transform3D(Basis(), eye).looking_at(eye + dir, Vector3.UP)
	main.fly_tw = main.create_tween()
	main.fly_tw.tween_method(func(x: float): main.view_cam.global_transform = start.interpolate_with(end, x), 0.0, 1.0, 1.0)
	return {"ok": true}


func star_xy(id: String, lst: float, k: float) -> Vector2:
	"""where a star stands looking north: around the pole, turned by its hour angle (east right, west left)"""
	var s: Array = STARS[id]
	var ha := deg_to_rad(lst - float(s[0]) * 15.0)
	return Vector2(-sin(ha), -cos(ha)) * (90.0 - float(s[1])) * k


# =======================================================================================================================
# paint (parts of the adventure panel)
# =======================================================================================================================
func paint_level(gg: Control) -> void:
	"""step «Schwierigkeit & Ziel» → Einstellungen: what the chosen difficulty means for the puzzles (no own setting)"""
	gg.add_child(ab._lab(T.t("Hilfe bei Rätseln (Karte lesen, Peilung, Sternbild)") + ": " + T.t(HILFE[hilfe()][1]), 12, Color(0.6, 0.66, 0.74)))


func paint_pending(g: Control, pe: Dictionary) -> void:
	var r := RR()
	var tip := str(r.get("tip", ""))
	if tip != "" and hilfe() != "schwer" and main.now() - float(r.get("ask_t", 0.0)) >= TIP_S:
		if ab.blinki == null or not ab.blinki.paint(g, tip):          # A6: Blinki sagt den Tipp
			g.add_child(ab._lab(T.t("Tipp: %s") % tip, 13, ab.ORG))
	elif tip != "" and hilfe() == "normal":
		ab._btn(g, T.t("Blinki um einen Tipp bitten"), func(): ab.op({"do": "a3", "what": "tipp"}))   # Tipp auf Wunsch (Mittel)
	if str(pe.get("kind", "")) == "a3_kompass" and hat("feldstecher"):
		var ch := int(ab.R["chapter"])
		var k: Dictionary = KOMPASS[ch]
		ab._btn(g, T.t("Feldstecher: vom Bezugsort in die Peilrichtung schauen"), func(): _zoom_bearing(k))


func _zoom_bearing(k: Dictionary) -> void:
	var b = ab.bt()
	if b == null:
		return
	var bb := bearing(k["ref"][1], k["target"][1])
	var a := deg_to_rad(bb.x)
	zoom(Vector2(k["ref"][1]) + Vector2(sin(a), -cos(a)) * bb.y, Vector2(k["ref"][1]))


func paint_hud(body: Control) -> void:
	if ab.R.is_empty():
		return
	var g: VBoxContainer = ab._group(T.t("Grossvaters Sachen"), body)
	if hat("taschenuhr"):
		g.add_child(ab._lab(_watch_text(), 12, Color(0.95, 0.85, 0.6)))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	g.add_child(row)
	if hat("feldstecher"):
		ab._btn(row, T.t("Feldstecher aus") if not _zoom.is_empty() else T.t("Feldstecher: zum Ziel schauen"), func(): ab.op({"do": "a3", "what": "zoom"}))
	var got := []
	for it in ERBE:
		if hat(it):
			got.append(T.t(ITEM_NAME[it]))
	for it in ["seil", "ersatzteil"]:
		if hat(it):
			got.append(T.t(ITEM_NAME[it]))
	if not got.is_empty():
		g.add_child(ab._lab(", ".join(got), 12))
	var pg: Array = S()["pages"]
	g.add_child(ab._lab(T.t("Tagebuch des Grossvaters: %d von 10 Seiten") % pg.size(), 12, Color(0.75, 0.8, 0.86)))


func paint_camp(body: Control) -> void:
	var a: Array = RR().get("arrive", [])
	if a.size() == 2:
		var g: VBoxContainer = ab._group(T.t("Gefunden: %s") % T.t(ITEM_NAME[str(a[0])]), body)
		g.add_child(ab._lab(str(a[1]), 13, Color(0.95, 0.85, 0.6)))


func paint_night(body: Control) -> void:
	if ab.R.is_empty() or (ab.R["night"] as Dictionary).is_empty():
		return
	var r := RR()
	var g: VBoxContainer = ab._group(T.t("Sternbild: wo ist Norden?"), body)
	if str(r.get("star", "")) == "ok":
		g.add_child(ab._lab(star_result(), 13, ab.GRN))
		return
	if not stars_visible():
		g.add_child(ab._lab(T.t("Sobald es dunkel und klar ist, zeigt ein Stern die Richtung."), 12, Color(0.6, 0.66, 0.74)))
		return
	g.add_child(ab._lab(T.t("Nachts zeigt ein Stern die Richtung: der Polarstern steht immer im Norden. Welcher ist es?"), 13))
	var chart := Control.new()
	chart.custom_minimum_size = Vector2(300, 230)
	chart.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lst := _lst()
	var cands := star_cands()
	var show_tip: bool = hilfe() == "leicht" or (hilfe() == "normal" and (int(r["star_wrong"]) > 0 or main.now() - float(r.get("star_t", main.now())) >= TIP_S))
	if not r.has("star_t"):
		r["star_t"] = main.now()
	var lite := _lite()
	var la: float = main.ort_lat if main.ort_lat != 0.0 else 46.8
	chart.draw.connect(func():
		var sz := chart.size
		var c := Vector2(sz.x / 2.0, sz.y * 0.42)
		var k := sz.y * 0.53 / la
		chart.draw_rect(Rect2(Vector2.ZERO, sz), Color(0.03, 0.05, 0.12))
		var hy := c.y + la * k
		chart.draw_rect(Rect2(Vector2(0, hy), Vector2(sz.x, sz.y - hy)), Color(0.06, 0.07, 0.08))
		chart.draw_string(chart.get_theme_default_font(), Vector2(sz.x / 2.0 - 4, sz.y - 4), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.7, 0.75, 0.82))
		if not lite:
			for ln in LINES:
				chart.draw_line(c + star_xy(ln[0], lst, k), c + star_xy(ln[1], lst, k), Color(0.4, 0.5, 0.75, 0.45), 1.0)
		for id in STARS:
			var p: Vector2 = c + star_xy(id, lst, k)
			if p.y < hy:
				chart.draw_circle(p, clampf(4.2 - float(STARS[id][2]) * 0.8, 1.0, 3.2), Color(1, 1, 0.92))
		if show_tip:
			var mk: Vector2 = c + star_xy("merak", lst, k)
			var dk: Vector2 = c + star_xy("dubhe", lst, k)
			var d := (dk - mk)
			var n := int(d.length() * 5.0 / 6.0)
			for q in range(0, n, 2):
				chart.draw_line(dk + d.normalized() * q * 3.0, dk + d.normalized() * (q * 3.0 + 3.0), Color(1.0, 0.62, 0.26, 0.8), 1.5)
		for j in range(cands.size()):
			var p2: Vector2 = c + star_xy(cands[j], lst, k)
			var col := Color(0.23, 0.55, 1.0)
			if hilfe() == "leicht" and cands[j] == "polaris":
				col = Color(0.3, 0.85, 0.45)
				chart.draw_line(p2 + Vector2(-26, 18), p2 + Vector2(-8, 5), col, 2.0)
				chart.draw_line(p2 + Vector2(-8, 5), p2 + Vector2(-15, 5), col, 2.0)
				chart.draw_line(p2 + Vector2(-8, 5), p2 + Vector2(-10, 12), col, 2.0)
			chart.draw_arc(p2, 7.0, 0.0, TAU, 16, col, 1.5)
			chart.draw_string(chart.get_theme_default_font(), p2 + Vector2(9, -6), "ABC"[j], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, col))
	g.add_child(chart)
	if show_tip and hilfe() != "schwer":
		g.add_child(ab._lab(T.t("Tipp: Verlängere die beiden hinteren Sterne des Grossen Wagens etwa fünfmal - dort steht der Polarstern."), 12, ab.ORG))
	if str(r.get("star_msg", "")) != "":
		g.add_child(ab._lab(str(r["star_msg"]), 12, ab.REDC))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	g.add_child(row)
	for j in range(3):
		var L: String = "ABC"[j]
		ab._btn(row, T.t("Stern %s") % L, func(): ab.op({"do": "a3", "what": "stern", "value": L}))
	ab._btn(row, T.t("Blick zum Nordhimmel"), func(): ab.op({"do": "a3", "what": "nord"}))


func paint_morning(parent: Control) -> void:
	var r := RR()
	var lines := []
	for n in r.get("pages", []):
		lines.append(T.t("Tagebuchseite %d") % int(n))
	for it in r.get("items", []):
		if ITEM_NAME.has(it):
			lines.append(T.t(ITEM_NAME[it]))
	for bd in BADGES:
		if bd[0] in r.get("badges", []):
			lines.append(T.t(str(bd[1])))
	if lines.is_empty() and int(r.get("xp", 0)) == 0:
		return
	var g: VBoxContainer = ab._group(T.t("Rätsel und Grossvaters Spuren"), parent)
	if not lines.is_empty():
		g.add_child(ab._lab(T.t("Neu: ") + ", ".join(lines), 13, Color(0.95, 0.85, 0.6)))
	g.add_child(ab._lab(T.t("+%d Erfahrung aus Rätseln und Funden · Schwierigkeit %s") % [int(r.get("xp", 0)), T.t(HILFE[hilfe()][0])], 12, Color(0.75, 0.8, 0.86)))


func paint_chapter(parent: Control) -> void:
	var s := S()
	var pg: Array = s["pages"]
	var got := ERBE.filter(func(x): return hat(x)).map(func(x): return T.t(ITEM_NAME[x]))
	var g: VBoxContainer = ab._group(T.t("Tagebuch des Grossvaters: %d von 10 Seiten · Abzeichen: %d von %d") % [pg.size(), (s["badges"] as Dictionary).size(), BADGES.size()], parent)
	g.add_child(ab._lab(T.t("Gegenstände: ") + (", ".join(got) if not got.is_empty() else T.t("noch keine")), 12, Color(0.6, 0.66, 0.74)))
	if pg.is_empty():
		return
	var eb := Button.new()
	eb.text = ("▾ " if pages_open else "▸ ") + T.t("Seiten lesen")
	eb.flat = true
	eb.alignment = HORIZONTAL_ALIGNMENT_LEFT
	eb.pressed.connect(func(): pages_open = not pages_open; ab._changed())
	g.add_child(eb)
	if pages_open:
		for n in pg:
			g.add_child(ab._lab(T.t("Seite %d:") % int(n) + " " + page_text(int(n)), 12, Color(0.95, 0.85, 0.6)))


# =======================================================================================================================
# the map overlay: the bearing puzzle (places, scale, arrows) and the arrow of «Leicht»
# =======================================================================================================================
class Overlay extends Control:
	var mod                                  # abenteuer_raetsel.gd

	func _ready() -> void:
		set_anchors_preset(Control.PRESET_FULL_RECT)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _gui_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			var j: int = mod.map_pick(ev.position)
			if j >= 0:
				mod.ab.op({"do": "choose", "value": str(j)})
				accept_event()

	func _draw() -> void:
		mod.draw_overlay(self)


func attach_map(karte: Control) -> void:
	if _ov != null or karte == null:
		return
	var ov := Overlay.new()
	ov.mod = self
	karte.add_child(ov)
	_ov = ov
	karte.draw.connect(func(): ov.queue_redraw.call_deferred())


func _puzzle() -> Dictionary:
	if ab.R.is_empty() or ab.step != 4:
		return {}
	var pe: Dictionary = ab.R.get("pending", {})
	return pe if str(pe.get("kind", "")) == "a3_kompass" else {}


func map_pick(pos: Vector2) -> int:
	if _puzzle().is_empty() or _ov == null:
		return -1
	var km = _ov.get_parent()
	var cands := _cands(int(ab.R["chapter"]))
	var best := -1
	var bd := 22.0
	for j in range(cands.size()):
		var d: float = (km.to_px(cands[j][1]) as Vector2).distance_to(pos)
		if d < bd:
			bd = d
			best = j
	return best


func draw_overlay(ov: Control) -> void:
	var km = ov.get_parent()
	if km == null or str(km.get("mode")) != "schatz" or ab.R.is_empty():
		ov.mouse_filter = Control.MOUSE_FILTER_IGNORE
		return
	var ink := Color(0.33, 0.2, 0.1)
	var blue := Color(0.15, 0.35, 0.85)
	var font := ov.get_theme_default_font()
	var pz := _puzzle()
	ov.mouse_filter = Control.MOUSE_FILTER_STOP if not pz.is_empty() else Control.MOUSE_FILTER_IGNORE
	if hilfe() == "leicht" and ab.step == 4 and pz.is_empty():
		var last: Dictionary = ab.chapter()["stages"][-1]
		if last.has("walk"):
			_arrow(ov, km.to_px(ab.R["pos"]), km.to_px(last["walk"][-1]), Color(0.23, 0.55, 1.0, 0.8))
	if pz.is_empty():
		return
	var ch := int(ab.R["chapter"])
	var k: Dictionary = KOMPASS[ch]
	var rp: Vector2 = km.to_px(k["ref"][1])
	ov.draw_line(rp, rp + Vector2(0, -16), ink, 2.0)
	ov.draw_colored_polygon(PackedVector2Array([rp + Vector2(0, -16), rp + Vector2(10, -12), rp + Vector2(0, -8)]), Color(0.72, 0.12, 0.08))
	var lab := T.t(str(k["ref"][0]))
	var lw: float = font.get_string_size(lab, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
	var lx: float = rp.x + 4.0 if rp.x + 4.0 + lw < ov.size.x * 0.72 else rp.x - 4.0 - lw    # (not under the compass rose)
	ov.draw_string(font, Vector2(lx, rp.y + 12), lab, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, ink)
	var cands := _cands(ch)
	var tip_now: bool = hilfe() == "leicht" or (hilfe() == "normal" and main.now() - float(RR().get("ask_t", 0.0)) >= TIP_S)
	if tip_now:
		var b := bearing(k["ref"][1], k["target"][1])
		var a := deg_to_rad(b.x)
		var far: Vector2 = km.to_px(Vector2(k["ref"][1]) + Vector2(sin(a), -cos(a)) * b.y * 1.35)
		var n := int(rp.distance_to(far) / 5.0)
		for q in range(0, n, 2):
			ov.draw_line(rp.lerp(far, float(q) / n), rp.lerp(far, float(q + 1) / n), Color(0.72, 0.12, 0.08, 0.7), 1.5)
	for j in range(cands.size()):
		var p: Vector2 = km.to_px(cands[j][1])
		var right: bool = bool(cands[j][2])
		var col := Color(0.3, 0.7, 0.35) if hilfe() == "leicht" and right else blue
		ov.draw_circle(p, 8.0, Color(0.95, 0.92, 0.85))
		ov.draw_arc(p, 8.0, 0.0, TAU, 18, col, 2.0)
		ov.draw_string(font, p + Vector2(-3.5, 4.5), str(j + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, col)
		if hilfe() == "leicht" and right:
			_arrow(ov, rp, p, Color(0.3, 0.7, 0.35, 0.85))
	# the scale: 500 m
	var s0: Vector2 = km.to_px(Vector2(-940, 600))
	var s1: Vector2 = km.to_px(Vector2(-440, 600))
	ov.draw_line(s0, s1, ink, 3.0)
	ov.draw_line(s0 + Vector2(0, -4), s0 + Vector2(0, 4), ink, 2.0)
	ov.draw_line(s1 + Vector2(0, -4), s1 + Vector2(0, 4), ink, 2.0)
	ov.draw_string(font, s0 + Vector2(2, -6), "500 m", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, ink)


func _arrow(ov: Control, a: Vector2, b: Vector2, col: Color) -> void:
	var d := b - a
	if d.length() < 12.0:
		return
	var u := d.normalized()
	var e := b - u * 9.0
	ov.draw_line(a, e, col, 2.5, true)
	ov.draw_colored_polygon(PackedVector2Array([b - u * 2.0, e + u.orthogonal() * 6.0 - u * 3.0, e - u.orthogonal() * 6.0 - u * 3.0]), col)


# =======================================================================================================================
func tick(dt: float) -> void:
	_reg_t -= dt
	if _reg_t <= 0.0:
		_reg_t = 3.0
		if main.scene == "bergtal":
			_ensure_badges()
	if ab.R.is_empty():
		return
	# Normal: the tip comes after a while - paint once when it is due
	var pe: Dictionary = ab.R.get("pending", {})
	var r := RR()
	if not pe.is_empty() and str(r.get("tip", "")) != "" and hilfe() == "normal":
		var due: bool = main.now() - float(r.get("ask_t", 0.0)) >= TIP_S
		if due and _tip_seq != int(float(r.get("ask_t", 0.0)) * 10.0):
			_tip_seq = int(float(r.get("ask_t", 0.0)) * 10.0)
			ab._changed()
			if _ov != null:
				_ov.queue_redraw()
	if ab.step == 6 and str(r.get("star", "")) != "ok" and r.has("star_t") and hilfe() == "normal" and not bool(r.get("star_tip", false)) \
			and main.now() - float(r["star_t"]) >= TIP_S:
		r["star_tip"] = true
		ab._changed()


func op(d: Dictionary) -> Dictionary:
	var what := str(d.get("what", "state"))
	var out := {"ok": true}
	match what:
		"hilfe":
			if not HILFE.has(str(d.get("value", ""))):
				return {"ok": false, "error": "leicht | normal | schwer"}
			set_hilfe(str(d["value"]))
		"tipp":                                          # Tipp auf Wunsch (Mittel): die Wartezeit ist sofort um
			var rt := RR()
			if not rt.is_empty() and hilfe() == "normal":
				rt["ask_t"] = main.now() - TIP_S
				if rt.has("star_t"):
					rt["star_t"] = main.now() - TIP_S
				ab._changed()
		"zoom":
			out = zoom()
		"stern":
			out = star_answer(str(d.get("value", "")))
		"nord":
			out = look_north()
		"gib":                                           # tests: give a thing (pickel, seil, ersatzteil …)
			gib(str(d.get("value", "")))
			_check_erbe()
			ab._changed()
		"badges":
			_ensure_badges()
		"tip_now":                                       # tests: the tip of Normal at once
			if not ab.R.is_empty():
				RR()["ask_t"] = -1000.0
				RR()["star_t"] = -1000.0
				ab._changed()
	out["a3"] = state()
	return out


func state() -> Dictionary:
	var s := S()
	var out := {"hilfe": hilfe(), "pages": s["pages"], "items": ERBE.filter(func(x): return hat(x)), "badges": s["badges"], "wege": s["wege"],
			"kompass": s["kompass"], "stern": s["stern"], "zoom": not _zoom.is_empty()}
	if not ab.R.is_empty():
		var r := RR()
		out["run"] = {"xp": r.get("xp", 0), "pages": r.get("pages", []), "items": r.get("items", []), "wrong": r.get("wrong", 0), "star": r.get("star", ""),
				"stars_visible": stars_visible(), "star_cands": star_cands(), "tip": str(r.get("tip", "")) if main.now() - float(r.get("ask_t", 0.0)) >= TIP_S and hilfe() != "schwer" else ""}
		var pz := _puzzle()
		if not pz.is_empty():
			var c := _cands(int(ab.R["chapter"]))
			out["run"]["kompass"] = c.map(func(x): return {"name": x[0], "x": x[1].x, "z": x[1].y, "right": x[2]})
	return out
