extends RefCounted
## «Die Karte des Grossvaters» – Kapitel 3 «Der Seeblock» (Phase 2, Besitzer 21.11.2026): der Morgen nach dem leeren Zelt.
## Lias Spur führt zum Gumpisee; Maggie folgt dem Duft (neu: Duftwolken, die verblassen), über den Bach von Stein zu Stein,
## über die Felsblöcke ans Ostufer, ein Floss aus Treibholz bauen und über den See staken (neu: Floss mit Windböen),
## am Seeblock das Zeichen aus Kapitel 2 im Riss finden, drei Zeichen am Fels lesen und die Kiste öffnen (neu: Zahlenschloss
## mit Zeichen). Lia sitzt oben auf dem Block. Streit, dann ein wackliger Waffenstillstand. Rückblende: das Versprechen am See.
## Abends am Feuer: Tonis Notizbuch. Gemeinsames Ziel: das Biwak.
##
## Format wie kit_k2_daten.gd. Ort: das Südufer des Gumpisees (bergtal LAKE1), kein eigenes Gelände: die Achse liegt am Ufer,
## s = −x (nach Westen), q = −z − 300 (+ = Norden, zum See). «top_see» = Höhe über dem Seespiegel (statt über dem Boden).
## Die neuen Mechaniken stehen in kit_k3.gd (eigene Datei); kit_abenteuer.gd hängt sie nur ein.

const KAPITEL := 3
const TITEL := "Der Seeblock"
const ENDE := "Ende von Kapitel 3 – Fortsetzung folgt."

const ACHSE := [Vector2(0.0, -300.0), Vector2(-1.0, 0.0)]
# the camp (bergtal «frei»: tent, MoveEye, the camp people): further east on the shore, away from the course
const LAGER := Vector2(38.0, -293.0)
const START := {"wetter": "clear", "stunde": 10.2}

const ROLLEN := ["enkelin", "enkel", "tochter", "sohn"]
const ROLLE_NAME := {"enkelin": "Enkelin", "enkel": "Enkel", "tochter": "Tochter", "sohn": "Sohn"}


static func bezug(rolle: String) -> Dictionary:
	var alt := rolle in ["enkelin", "enkel"]
	return {"bezug": "Grossvater" if alt else "Vater", "jahr": "1974" if alt else "2000",
		"lia_bezug": "Enkelin" if alt else "Tochter", "jahr_kurz": "74" if alt else "00"}


# =======================================================================================================================
# the course
# =======================================================================================================================
const DINGE := [
	# scene 1: Lia's tent at the camp of chapter 2 (empty)
	{"id": "lia_zelt", "art": "zelt", "tal": [-10.0, -16.5], "dreh": 40.0},
	# scene 3: the brook where it runs into the lake - stepping stones (over the lake level), then the boulders
	{"id": "bach", "art": "wasser", "s": 19.5, "q": -7.0, "ls": 6.2, "lq": 3.2, "top_see": 0.02},
	{"id": "stein1", "art": "stein", "s": 24.4, "q": -7.0, "ls": 0.5, "lq": 0.55, "top_see": 0.4},
	{"id": "stein2", "art": "stein", "s": 22.2, "q": -6.7, "ls": 0.5, "lq": 0.55, "top_see": 0.45},
	{"id": "stein3", "art": "stein", "s": 20.0, "q": -7.2, "ls": 0.45, "lq": 0.5, "top_see": 0.38},
	{"id": "stein4", "art": "stein", "s": 17.8, "q": -6.8, "ls": 0.5, "lq": 0.55, "top_see": 0.42},
	{"id": "stein5", "art": "stein", "s": 15.6, "q": -7.0, "ls": 0.5, "lq": 0.55, "top_see": 0.4},
	{"id": "block_a", "art": "block", "s": 10.0, "q": -5.0, "ls": 1.0, "lq": 2.6, "top": 1.4, "kante": true, "von": [[11.6, -5.0], [11.6, -6.5], [11.6, -3.5]]},
	{"id": "block_b", "art": "block", "s": 7.95, "q": -4.6, "ls": 1.05, "lq": 2.0, "top": 1.9},
	# down to the beach in two rock steps (each under 1.05 m: one walks down, no jump needed)
	{"id": "stufe1", "art": "block", "s": 6.3, "q": -4.4, "ls": 0.62, "lq": 1.4, "top_see": 2.15},
	{"id": "stufe2", "art": "block", "s": 5.1, "q": -4.0, "ls": 0.6, "lq": 1.2, "top_see": 1.25},
	# scene 4: driftwood on the east beach
	{"id": "stamm1", "art": "fund", "s": 3.0, "q": 2.0, "top": 0.0, "form": "holz"},
	{"id": "stamm2", "art": "fund", "s": 9.0, "q": 3.4, "top": 0.0, "form": "holz"},
	{"id": "stamm3", "art": "fund", "s": 6.5, "q": -0.6, "top": 0.0, "form": "holz"},
	# scenes 6–9: around the Seeblock the lake is water (a fall in: back to the landing); the landing is a deck (dry)
	{"id": "see_block", "art": "wasser", "s": 42.0, "q": 38.0, "ls": 11.0, "lq": 11.0, "top_see": 0.0, "unsichtbar": true},
]

# the set of kit_k3.gd: the Seeblock (centre, half axes along s / q, height of the top over the lake), its landing (a ledge at
# the water on the beach side), the crack with the sign of chapter 2, three marks and the box in a niche; the raft; the fire
const SEEBLOCK := {"c": [42.0, 40.0], "rs": 4.6, "rq": 4.2, "top_see": 5.0, "deck_see": 4.75,
		"steg": {"c": [42.0, 34.7], "ls": 3.0, "lq": 1.1, "top_see": 0.55},
		"riss": [42.0, 0.0, 2.3],
		"marken": [["marke1", 39.4, "I", "G"], ["marke2", 41.0, "II", "+"], ["marke3", 44.6, "III", "T"]],
		"kiste": [42.8, 35.6]}
const FLOSS := {"bau": [5.0, 4.4], "start": [6.0, 9.2], "kurs": [[14.0, 18.0], [28.0, 26.5], [42.0, 32.4]], "breite": 7.0,
		"stamm": ["stamm1", "stamm2", "stamm3"]}
const FEUER := [2.0, -2.0]
# the scent trail (scene 2): the clouds one after the other; one fades in «fade» s while one dawdles or goes the wrong way
# (coming closer it hardly fades) - when it is gone, Maggie sniffs again on the action
const DUFT := {"spur": {"punkte": [[64.0, -2.0], [58.0, -4.6], [52.0, -7.0], [46.0, -9.0], [40.0, -10.6], [34.0, -9.0], [28.2, -7.4]],
		"fade": 6.0, "r": 2.3}}
# the combination box (scene 7): the symbols on each wheel; the solution is read off the three marks (I, II, III)
const SCHLOSS := {"symbole": ["G", "T", "+", "×", "★", "▲"], "loesung": ["G", "+", "T"]}

const AKTIONEN := [
	{"id": "steine", "art": "steine", "s": 26.4, "q": -7.0, "r": 1.6, "kette": ["stein1", "stein2", "stein3", "stein4", "stein5"], "nach": [12.9, -6.8]},
	{"id": "block_hoch", "art": "kante", "s": 11.6, "q": -5.0, "r": 1.4, "ding": "block_a"},
	{"id": "stamm1_nehmen", "art": "fund", "s": 3.0, "q": 2.0, "r": 1.3, "ding": "stamm1"},
	{"id": "stamm2_nehmen", "art": "fund", "s": 9.0, "q": 3.4, "r": 1.3, "ding": "stamm2"},
	{"id": "stamm3_nehmen", "art": "fund", "s": 6.5, "q": -0.6, "r": 1.3, "ding": "stamm3"},
	{"id": "floss_bauen", "art": "floss_bauen", "s": 5.0, "q": 4.4, "r": 1.8},
	{"id": "zeichen", "art": "zeichen", "s": 42.0, "q": 34.4, "r": 1.4},
	{"id": "marke1", "art": "marke", "s": 39.4, "q": 34.6, "r": 0.85},
	{"id": "marke2", "art": "marke", "s": 41.0, "q": 34.6, "r": 0.75},
	{"id": "marke3", "art": "marke", "s": 44.6, "q": 34.6, "r": 0.85},
	{"id": "schloss", "art": "schloss", "s": 42.8, "q": 34.7, "r": 0.75},
]

const WEG := [[72.0, -1.0], [64.0, -2.0], [58.0, -4.6], [52.0, -7.0], [46.0, -9.0], [40.0, -10.6], [34.0, -9.0], [27.0, -7.2]]
const WEG_BREITE := 6.0
const WEGE := {
	"s02_duft": WEG,
	"s03_blockfeld": [[27.0, -7.2], [24.4, -7.0], [15.6, -7.0], [12.0, -5.0], [10.0, -5.0], [7.6, -4.6], [4.0, -1.0]],
	"s04_floss": [[7.6, -4.6], [6.3, -4.4], [5.1, -4.0], [4.0, -1.0], [3.0, 2.0], [9.0, 3.4], [6.5, -0.6], [5.0, 4.4]],
	"s06_seeblock": [[39.0, 34.7], [45.0, 34.7]],
	"s07_kiste": [[39.0, 34.7], [45.0, 34.7]],
	"s08_kartenstueck": [[39.0, 34.7], [45.0, 34.7]],
	"s09_lia": [[39.0, 34.7], [45.0, 34.7]],
}

const CHECKPOINTS := {"start": [7.4, -289.0], "spur": [72.0, -1.0], "bach": [27.0, -7.2], "felsen": [12.4, -5.0],
		"strand": [4.0, 1.0], "block": [42.0, 34.7], "abend": [3.5, -1.0]}

# =======================================================================================================================
# who speaks, badges, finds
# =======================================================================================================================
const SPRECHER := {"erzaehler": ["", Color(0.92, 0.94, 0.97)], "figur": ["{name}", Color(1.0, 0.86, 0.55)],
		"grossvater": ["{bezug}", Color(0.95, 0.78, 0.55)], "toni": ["Toni", Color(0.7, 0.85, 1.0)],
		"lia": ["Lia", Color(1.0, 0.6, 0.55)], "blinki": ["Blinki", Color(0.55, 0.9, 1.0)], "maggie": ["Maggie", Color(1.0, 0.8, 0.4)]}

const ABZEICHEN := {"spuernase": ["Spürnase", "Maggies Duftspur bis zum Bach – ohne sie ein einziges Mal zu verlieren."],
		"kapitaen": ["Kapitän", "Mit dem Floss zum Seeblock – auf Kurs geblieben und jede Böe gehalten."]}

const FUNDE_ALLE := []
const FUNDE := {"stamm1": ["Treibholz", "Ein langer, gerader Stamm – angeschwemmt und trocken."],
		"stamm2": ["Treibholz", "Ein zweiter Stamm, etwas krumm, aber stark."],
		"stamm3": ["Treibholz", "Der dritte Stamm. Mit dem Seil aus dem Rucksack wird das ein Floss."],
		"kartenstueck": ["Zweites Kartenstück", "Die fehlende Hälfte der Karte: der Weg vom See hinauf zum Biwak."],
		"notiz": ["Notiz «Treffpunkt Biwak»", "«Treffpunkt Biwak. Wer zuerst da ist, macht Tee. – G.» ({jahr})"]}

# =======================================================================================================================
# the 11 scenes
# =======================================================================================================================
const LIA := {"jacke": [0.86, 0.35, 0.3], "look": {"kopf": "zopf", "pack": true, "hose": [0.18, 0.2, 0.24], "umbrella": false, "lamp": ""}}
const GV_JUNG := {"jacke": [0.55, 0.32, 0.18], "look": {"kopf": "hut", "pack": true, "hose": [0.32, 0.3, 0.26], "umbrella": false, "lamp": ""}}
const TONI_JUNG := {"jacke": [0.25, 0.4, 0.62], "look": {"kopf": "muetze", "pack": true, "hose": [0.2, 0.22, 0.3], "umbrella": false, "lamp": ""}}

const SZENEN := [
	{"id": "s01_zelt", "titel": "Der Morgen danach", "start": [7.4, -289.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "shot", "art": "fix", "tal": [-13.8, -12.6], "h": 1.6, "blick_tal": [-10.0, -16.5, 0.5], "d": 5.0, "ziel_tal": [-10.0, -16.5, 0.0], "groesse": 1.4},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Am Morgen. Lias Zelt steht noch da – leer."},
			{"t": 3.0, "k": "sag", "wer": "blinki", "text": "Keine Lia. Kein Notizbuch. Aber Fussspuren. Ich liebe Fussspuren."}]},
		{"musik": "explore"},
		{"ziel": "Sieh dir die Spuren hinter dem Zelt an", "bis": "ort_tal:-9.5,-21.0,2.4"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "nah_tal", "tal": [-9.6, -23.0], "h": 0.1, "r": 1.4, "d": 4.0, "ziel_tal": [-9.6, -23.0, 0.0], "groesse": 0.8},
			{"t": 0.0, "k": "maggie_lauf", "s": 9.6, "q": -276.0},
			{"t": 0.4, "k": "sag", "wer": "figur", "text": "Ihre Schuhe. Sie ist Richtung Norden gegangen … zum Gumpisee."},
			{"t": 3.4, "k": "sag", "wer": "maggie", "text": "Wuff!"},
			{"t": 4.2, "k": "sag", "wer": "figur", "text": "Die Linie auf der Karte zeigt auch dorthin. Zum Seeblock. Los, Maggie!"},
			{"t": 7.4, "k": "blende", "s": 1.8},
			{"t": 8.3, "k": "zeit", "h": 11.6}]}]},
	{"id": "s02_duft", "titel": "Maggies Nase", "start": [72.0, -1.0], "blick": [64.0, -2.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "establish", "s": 52.0, "q": 13.0, "h_see": 3.2, "blick_see": [42.0, 36.0, 2.0], "d": 6.0, "ziel_see": [42.0, 35.3, 0.0], "groesse": 5.0},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Eine Stunde später. Am Ufer des Gumpisees."},
			{"t": 3.0, "k": "sag", "wer": "figur", "text": "Da draussen im See – der grosse Felsblock. Das muss der Seeblock sein."},
			{"t": 6.0, "k": "sag", "wer": "blinki", "text": "Lias Spur ist hier zu Ende. Für Augen. Nicht für Nasen."}]},
		{"checkpoint": "spur"},
		{"sag": "Maggie hat Lias Duft. Folge den Duftwolken – sie verblassen schnell!", "wer": "blinki"},
		{"ziel": "Folge Maggies Nase: von Duftwolke zu Duftwolke", "bis": "aktion:duft", "duft": "spur",
			"hinweise": [[25.0, "Verloren? Drück die Aktion – dann schnüffelt Maggie die Spur neu.", "blinki"]]},
		{"abzeichen": "spuernase", "wenn": "nicht:duft_verloren"},
		{"sag": "Die Spur geht über den Bach. Lia ist hier rübergesprungen.", "wer": "figur"}]},
	{"id": "s03_blockfeld", "titel": "Das Blockfeld", "start": [27.0, -7.2], "blick": [24.4, -7.0], "schritte": [
		{"checkpoint": "bach"},
		{"ziel": "Spring von Stein zu Stein über den Bach", "bis": "ort:12.6,-6.0,2.0",
			"hinweise": [[20.0, "Lauf auf den ersten Stein zu und spring (Leertaste / Springen) – der nächste Stein ist nah.", "blinki"]]},
		{"checkpoint": "felsen"},
		{"ziel": "Klettere über die Felsblöcke (Aktion an der Kante)", "bis": "ort:7.6,-4.6,1.2",
			"hinweise": [[20.0, "An der hellen Kante: Aktion zum Hochklettern. Der zweite Block ist nur eine Stufe höher.", "blinki"]]},
		{"sag": "Von hier oben sieht man den ganzen See. Und da drüben – Treibholz!", "wer": "figur"}]},
	{"id": "s04_floss", "titel": "Ein Floss", "start": [4.0, 1.0], "schritte": [
		{"checkpoint": "strand"},
		{"ziel": "Sammle drei Stämme Treibholz am Ufer", "bis": "aktion:staemme",
			"hinweise": [[30.0, "Die Stämme liegen am Ufer verstreut – der leuchtende Punkt zeigt den nächsten.", "blinki"]]},
		{"ziel": "Bau am Ufer das Floss (Aktion)", "bis": "aktion:floss_bauen"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 1.0, "q": 1.0, "h": 1.7, "blick": [6.0, 8.0, 0.3], "d": 5.0, "ziel": [6.0, 9.2, 0.0], "groesse": 2.0},
			{"t": 0.2, "k": "floss_zeigen"},
			{"t": 0.4, "k": "sag", "wer": "figur", "text": "Drei Stämme, das Seil aus dem Rucksack … fertig!"},
			{"t": 3.2, "k": "sag", "wer": "blinki", "text": "Schwimmfähigkeit: wahrscheinlich. Maggie ist skeptisch."},
			{"t": 6.0, "k": "sag", "wer": "maggie", "text": "Wuff."}]}]},
	{"id": "s05_see", "titel": "Wind auf dem See", "start": [4.0, 1.0], "schritte": [
		{"sag": "Mit der Stange staken: in die Richtung lenken, in die es gehen soll. Bei einer Böe: Aktion – Stange einstemmen!", "wer": "blinki"},
		{"musik": "action"},
		{"ziel": "Stake das Floss zum Seeblock", "bis": "aktion:floss", "floss": true,
			"hinweise": [[40.0, "Folge den Bojen: der leuchtende Punkt zeigt die nächste.", "blinki"]]},
		{"abzeichen": "kapitaen", "wenn": "merker:kapitaen"},
		{"musik": "explore"},
		{"checkpoint": "block"}]},
	{"id": "s06_seeblock", "titel": "Der Seeblock", "start": [42.0, 34.7], "blick": [42.0, 38.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 36.5, "q": 30.0, "h_see": 1.6, "blick_see": [42.0, 36.0, 1.8], "d": 5.0, "ziel_see": [42.0, 35.8, 1.5], "groesse": 3.0},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Der Seeblock. Von Nahem ist er riesig."},
			{"t": 3.0, "k": "sag", "wer": "blinki", "text": "Da ist ein Riss im Fels. Erinnert dich das an etwas?"}]},
		{"ziel": "Vergleiche den Riss mit dem Zeichen aus der Schlucht (Aktion)", "bis": "aktion:zeichen"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 42.0, "q": 33.4, "h_see": 2.1, "blick_see": [42.0, 35.8, 2.8], "d": 4.0, "ziel_see": [42.0, 35.8, 2.85], "groesse": 0.8},
			{"t": 0.0, "k": "riss_leuchtet"},
			{"t": 0.0, "k": "setzen", "s": 44.8, "q": 35.0},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Zwei Linien und ein Kreuz – genau wie das Zeichen im Infrarot!"},
			{"t": 3.4, "k": "sag", "wer": "blinki", "text": "Übereinstimmung: hundert Prozent. Ich bin beeindruckt. Von mir."}]}]},
	{"id": "s07_kiste", "titel": "Die Kiste", "start": [42.0, 34.7], "blick": [42.0, 38.0], "schritte": [
		{"sag": "Unter dem Riss: eine alte Kiste in einer Nische. Mit drei Rädchen statt einem Schlüssel.", "wer": "erzaehler"},
		{"ziel": "Lies die drei eingeritzten Zeichen am Fels (Aktion)", "bis": "aktion:marken",
			"hinweise": [[25.0, "Die Zeichen sind links und rechts der Kiste in den Fels geritzt.", "blinki"]]},
		{"ziel": "Öffne die Kiste mit den drei Zeichen (Aktion)", "bis": "aktion:schloss",
			"hinweise": [[30.0, "Die Zeichen am Fels haben Nummern: I, II, III. In dieser Reihenfolge.", "blinki"]]}]},
	{"id": "s08_kartenstueck", "titel": "Das zweite Stück", "start": [42.0, 34.7], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "setzen", "s": 44.8, "q": 34.6},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 43.6, "q": 34.6, "h_see": 1.6, "blick_see": [42.8, 35.6, 0.75], "d": 5.0, "ziel_see": [42.8, 35.6, 0.75], "groesse": 0.6},
			{"t": 0.0, "k": "kiste_auf"},
			{"t": 0.4, "k": "sag", "wer": "figur", "text": "Das zweite Kartenstück! Und ein Zettel …"},
			{"t": 2.6, "k": "fund", "id": "kartenstueck"},
			{"t": 3.2, "k": "karte_zeigen", "teil": "ganz"},
			{"t": 3.4, "k": "sag", "wer": "grossvater", "text": "«Treffpunkt Biwak. Wer zuerst da ist, macht Tee.»"},
			{"t": 6.8, "k": "fund", "id": "notiz"},
			{"t": 7.0, "k": "karte_weg"},
			{"t": 7.2, "k": "sag", "wer": "figur", "text": "Die Karte ist ganz. Der Weg geht hinauf zum Biwak."}]}]},
	{"id": "s09_lia", "titel": "Lia", "start": [42.0, 34.7], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "person", "id": "lia", "s": 42.6, "q": 38.6, "y_see": 4.75, "blick": [42.0, 30.0], "jacke": [0.86, 0.35, 0.3],
				"look": {"kopf": "zopf", "pack": true, "hose": [0.18, 0.2, 0.24], "umbrella": false, "lamp": ""}},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 40.0, "q": 31.6, "h_see": 3.2, "blick_see": [42.4, 38.2, 5.3], "d": 6.0, "ziel_see": [42.6, 38.6, 4.75], "groesse": 1.7},
			{"t": 0.3, "k": "sag", "wer": "lia", "text": "Ich war schneller. Schon wieder."},
			{"t": 2.8, "k": "sag", "wer": "figur", "text": "Und trotzdem hast du die Kiste nicht aufgekriegt."},
			{"t": 5.4, "k": "sag", "wer": "lia", "text": "Die Zeichen waren unter dem Moos. Ich hatte keine Zeit."},
			{"t": 8.2, "k": "sag", "wer": "lia", "text": "Dein {bezug} hat meinen im Sturm zurückgelassen. Das weisst du, oder?"},
			{"t": 11.8, "k": "sag", "wer": "figur", "text": "Das stimmt nicht! … Ich weiss nicht, was damals passiert ist."},
			{"t": 15.0, "k": "sag", "wer": "blinki", "text": "Vorschlag: Waffenstillstand. Zwei Leute, eine Karte, ein Hund."},
			{"t": 18.0, "k": "sag", "wer": "lia", "text": "Na gut. Bis zum Biwak. Dann sehen wir weiter."},
			{"t": 20.6, "k": "sag", "wer": "maggie", "text": "Wuff!"},
			{"t": 22.0, "k": "blende", "s": 1.6}]}]},
	{"id": "s10_rueckblende", "titel": "{jahr}", "start": [4.0, 1.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "blende", "s": 1.6},
			{"t": 0.8, "k": "person_weg", "id": "lia"},
			{"t": 0.8, "k": "setzen", "s": -6.0, "q": -6.0},
			{"t": 0.8, "k": "farbe", "art": "alt"},
			{"t": 0.8, "k": "zeit", "h": 16.2},
			{"t": 0.8, "k": "person", "id": "gv", "s": 4.6, "q": 1.4, "blick": [42.0, 40.0], "jacke": [0.55, 0.32, 0.18],
				"look": {"kopf": "hut", "pack": true, "hose": [0.32, 0.3, 0.26], "umbrella": false, "lamp": ""}},
			{"t": 0.8, "k": "person", "id": "toni", "s": 6.0, "q": 2.4, "blick": [42.0, 40.0], "jacke": [0.25, 0.4, 0.62],
				"look": {"kopf": "muetze", "pack": true, "hose": [0.2, 0.22, 0.3], "umbrella": false, "lamp": ""}},
			{"t": 0.8, "k": "shot", "art": "fix", "s": 2.0, "q": -3.6, "h": 1.5, "blick": [6.0, 3.0, 1.3], "d": 12.0, "ziel": [5.3, 1.9, 0.0], "groesse": 1.8},
			{"t": 1.2, "k": "sag", "wer": "erzaehler", "text": "{jahr}. Am selben Ufer."},
			{"t": 3.6, "k": "sag", "wer": "toni", "text": "Versprich mir was. Wenn einer von uns nicht weiterkann …"},
			{"t": 6.6, "k": "sag", "wer": "grossvater", "text": "… bringt der andere die Karte zu Ende. Versprochen. Bis zum Sonnenaufgang auf dem Grat."},
			{"t": 10.8, "k": "sag", "wer": "toni", "text": "Und wer zuerst oben ist –"},
			{"t": 12.4, "k": "sag", "wer": "grossvater", "text": "– zahlt den Kaffee. Ich weiss, Toni."},
			{"t": 14.6, "k": "blende", "s": 1.6},
			{"t": 15.4, "k": "farbe", "art": ""},
			{"t": 15.4, "k": "person_weg", "id": "gv"},
			{"t": 15.4, "k": "person_weg", "id": "toni"}]}]},
	{"id": "s11_feuer", "titel": "Am Feuer", "start": [3.5, -1.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "zeit", "h": 19.7},
			{"t": 0.0, "k": "feuer"},
			{"t": 0.0, "k": "setzen", "s": 3.4, "q": -0.6},
			{"t": 0.0, "k": "person", "id": "lia", "s": 0.8, "q": -2.6, "blick": [2.0, -2.0], "jacke": [0.86, 0.35, 0.3],
				"look": {"kopf": "zopf", "pack": true, "hose": [0.18, 0.2, 0.24], "umbrella": false, "lamp": ""}},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 5.6, "q": -5.4, "h": 1.5, "blick": [1.8, -1.6, 0.8], "d": 8.0, "ziel": [2.0, -2.0, 0.0], "groesse": 2.4},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Am Abend. Ein Feuer am Ufer."},
			{"t": 2.8, "k": "sag", "wer": "lia", "text": "Das hier hat Toni geschrieben. Lies."},
			{"t": 5.2, "k": "sag", "wer": "toni", "text": "«Er hat mich zurückgelassen.»", "d": 3.6},
			{"t": 9.0, "k": "sag", "wer": "figur", "text": "Vielleicht war es anders, als es aussieht."},
			{"t": 11.8, "k": "sag", "wer": "lia", "text": "Toni lebt noch, weisst du. Er redet nur nicht darüber. Nie."},
			{"t": 15.4, "k": "sag", "wer": "lia", "text": "Dann finden wir es raus. Am Biwak."},
			{"t": 18.0, "k": "sag", "wer": "blinki", "text": "Neue Akte: «Team». Mitglieder: drei. Plus ich."},
			{"t": 21.0, "k": "ende", "text": "Ende von Kapitel 3 – Fortsetzung folgt."}]}]},
]
