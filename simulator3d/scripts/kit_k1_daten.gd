extends RefCounted
## «Die Karte des Grossvaters» – Neubau Phase 2, Kapitel 1 «Die Karte» (Besitzer 21.11.2026: Vorschlag freigegeben): der Abend
## vor Kapitel 2 an der Selbstversorgerhütte Alp Tschuggen (bergtal_orte.gd _hut: Stube mit Holzofen, Leiter, Matratzenlager
## unter dem Dach). Gleiches Format wie kit_k2_daten.gd (siehe dort); hier ohne eigene Schlucht.
##
## Achse: Ursprung = Mitte der Hütte (Tal 51, 3), s = Tal +z, q = Tal −x → s = −(z der Hütte), q = x der Hütte (die Hütte steht
## um 180° gedreht, ihre Tür zeigt nach Tal −z). Also: Tür bei s −3.75, Ofen hinten rechts (q 3, s 2.6), Leiter q 3.6, s 0.35.
## Der Dachboden: eigene «Ebene» – Böden (decks), die nur gelten, solange man oben ist (kit_abenteuer.gd ebene()), weil ein deck
## im Bergtal überall unter sich gilt (keine zwei Stockwerke übereinander).
## Neu in Kapitel 1: Stirnlampe (Lichtkegel, Funde nur im Licht: «nur_lampe»), Ofen anfeuern, Rucksack packen (3 von 6),
## MoveEye aufstellen, Maggie holt etwas (maggie_such), Murmeltier am Fenster.

const KAPITEL := 1
const TITEL := "Die Karte"
const ENDE := "Ende von Kapitel 1 – weiter mit Kapitel 2 «Wo der Bach zweimal fällt»."

const ACHSE := [Vector2(51.0, 3.0), Vector2(0.0, 1.0)]
const LAGER := Vector2(44.5, -6.0)                 # MoveEye on its tripod, west of the door (bergtal «frei»)
const START := {"wetter": "rain", "stunde": 15.5}  # arrival in the rain, afternoon

const ROLLEN := ["enkelin", "enkel", "tochter", "sohn"]
const ROLLE_NAME := {"enkelin": "Enkelin", "enkel": "Enkel", "tochter": "Tochter", "sohn": "Sohn"}


static func bezug(rolle: String) -> Dictionary:
	var alt := rolle in ["enkelin", "enkel"]
	return {"bezug": "Grossvater" if alt else "Vater", "jahr": "1974" if alt else "2000",
		"lia_bezug": "Enkelin" if alt else "Tochter", "jahr_kurz": "74" if alt else "00"}


# =======================================================================================================================
# things (s, q around the hut; «boden_deck»: heights over the floor of the hut, not over the terrain)
# =======================================================================================================================
const DINGE := [
	# the ladder of the hut (it is already there): only its height and place for the ladder state
	{"id": "dachleiter", "art": "leiter", "s": 0.35, "q": 3.6, "top": 2.5, "boden_deck": true, "unsichtbar": true},
	# the attic: floor parts (around the hatch at q > 3.2, s -0.75 … 1.2), the plank beds as steps, the walls round it
	{"id": "dach_a", "art": "deck", "ebene": "dach", "s": 1.4, "q": -0.6, "ls": 2.15, "lq": 3.8, "top": 2.5},
	{"id": "dach_b", "art": "deck", "ebene": "dach", "s": 2.375, "q": 3.8, "ls": 1.175, "lq": 0.6, "top": 2.5},
	{"id": "dach_c", "art": "deck", "ebene": "dach", "s": -2.15, "q": -0.7, "ls": 1.5, "lq": 3.9, "top": 2.5},
	{"id": "pritsche_hinten", "art": "deck", "ebene": "dach", "s": 2.5, "q": 0.0, "ls": 1.0, "lq": 4.2, "top": 3.05},
	{"id": "pritsche_vorne", "art": "deck", "ebene": "dach", "s": -2.6, "q": -0.9, "ls": 0.9, "lq": 3.3, "top": 3.05},
	{"id": "dachwand_o", "art": "deck", "ebene": "dach", "s": 0.0, "q": 4.55, "ls": 3.9, "lq": 0.12, "top": 4.8},
	{"id": "dachwand_w", "art": "deck", "ebene": "dach", "s": 0.0, "q": -4.55, "ls": 3.9, "lq": 0.12, "top": 4.8},
	{"id": "dachwand_v", "art": "deck", "ebene": "dach", "s": -3.82, "q": 0.0, "ls": 0.12, "lq": 4.6, "top": 4.8},
	{"id": "dachwand_h", "art": "deck", "ebene": "dach", "s": 3.82, "q": 0.0, "ls": 0.12, "lq": 4.6, "top": 4.8},
	{"id": "laterne", "art": "licht", "s": -1.8, "q": 2.0, "top": 1.0, "boden_deck": true, "energie": 0.7, "weite": 5.5, "glas": true},
	{"id": "fensterlicht", "art": "licht", "s": -4.6, "q": 1.7, "top": 1.3, "boden_deck": true, "energie": 0.8, "weite": 4.5},
	{"id": "decke", "art": "decke", "s": 0.0, "q": 0.0, "ls": 3.7, "lq": 4.45, "top": 4.62, "boden_deck": true},
	# finds up there - only to be seen in the cone of the headlamp
	{"id": "dose", "art": "fund", "s": 0.25, "q": -3.7, "top": 2.5, "boden_deck": true, "nur_lampe": true, "form": "dose"},
	{"id": "skischuh", "art": "fund", "s": 1.1, "q": -1.2, "top": 2.5, "boden_deck": true, "nur_lampe": true, "form": "schuh"},
	{"id": "maeusenest", "art": "fund", "s": -1.3, "q": 1.6, "top": 2.5, "boden_deck": true, "nur_lampe": true, "form": "nest"},
	# outside: the wood pile (Maggie finds the torn corner of the map in it)
	{"id": "holzstapel", "art": "holz", "s": 0.5, "q": 6.6},
	{"id": "kartenecke", "art": "fund", "s": 0.5, "q": 5.6, "top": 0.0, "versteckt": true},
]

const AKTIONEN := [
	{"id": "ofen", "art": "ofen", "s": 1.9, "q": 2.4, "r": 1.4},
	{"id": "dach_hoch", "art": "leiter", "s": -0.15, "q": 3.6, "r": 0.9, "ding": "dachleiter", "oben": [0.9, 1.6]},
	{"id": "dach_runter", "art": "runter", "s": 0.3, "q": 3.1, "r": 0.55, "ebene": "dach", "nach": [-0.6, 3.6]},
	{"id": "lampe", "art": "lampe", "s": 0.9, "q": 1.6, "r": 6.0, "ebene": "dach"},
	{"id": "dose_nehmen", "art": "fund", "s": 0.25, "q": -3.7, "r": 1.3, "ding": "dose", "ebene": "dach"},
	{"id": "skischuh_nehmen", "art": "fund", "s": 1.1, "q": -1.2, "r": 1.1, "ding": "skischuh", "ebene": "dach"},
	{"id": "maeusenest_nehmen", "art": "fund", "s": -1.3, "q": 1.6, "r": 1.1, "ding": "maeusenest", "ebene": "dach"},
	{"id": "moveeye", "art": "moveeye", "tal": [44.5, -5.2], "r": 1.8},
	{"id": "maggie_such", "art": "maggie_such", "s": 0.5, "q": 4.6, "r": 2.2, "ding": "kartenecke", "ziel": [0.5, 6.3]},
]

# ceilings for the camera (kit_regie.gd): inside the hut it stays under the ceiling of the floor the figure is on
const DECKEN := [{"s": 0.0, "q": 0.0, "ls": 3.25, "lq": 4.0, "unten": 2.3, "oben": 4.5, "trenn": 1.6}]

const WEG := [[-16.0, -1.5], [-9.0, -2.0], [-4.6, -2.25]]
const WEG_BREITE := 5.0
const WEGE := {"s01_ankunft": [[-16.0, -1.5], [-9.0, -2.0], [-4.6, -2.25]]}

const CHECKPOINTS := {"start": [-16.0, -1.5], "tuer": [-5.2, -2.25], "stube": [-1.0, 1.0], "dach": [0.9, 1.6],
		"draussen": [-6.0, 2.0], "schopf": [-0.5, 5.6]}

const SPRECHER := {"erzaehler": ["", Color(0.92, 0.94, 0.97)], "figur": ["{name}", Color(1.0, 0.86, 0.55)],
		"grossvater": ["{bezug}", Color(0.95, 0.78, 0.55)], "toni": ["Toni", Color(0.7, 0.85, 1.0)],
		"lia": ["Lia", Color(1.0, 0.6, 0.55)], "blinki": ["Blinki", Color(0.55, 0.9, 1.0)], "maggie": ["Maggie", Color(1.0, 0.8, 0.4)]}

const ABZEICHEN := {"stoeberer": ["Stöberer", "Auf dem Dachboden alles gefunden – auch das Mäusenest."]}
const FUNDE_ALLE := ["dose", "skischuh", "maeusenest"]
const FUNDE := {"dose": ["Blechdose", "Eine alte Blechdose unter einem losen Brett. Darin: eine halbe Karte."],
		"skischuh": ["Alter Skischuh", "Leder, Grösse 44. Riecht nach 1974."],
		"maeusenest": ["Mäusenest", "Aus Zeitungspapier. Die Zeitung ist von {jahr}."],
		"kartenecke": ["Kartenecke", "Die fehlende Ecke der Karte – Maggie hat sie im Holzstapel gefunden."]}

# the backpack: 3 of 6 (kept for the later chapters: spielstand setting «k_rucksack»)
const RUCKSACK := [["seil", "Seil"], ["stirnlampe", "Stirnlampe"], ["proviant", "Proviant"], ["kompass", "Kompass"],
		["apotheke", "Apotheke"], ["fernglas", "Fernglas"]]

# =======================================================================================================================
# the 10 scenes
# =======================================================================================================================
const SZENEN := [
	{"id": "s01_ankunft", "titel": "Ankunft im Regen", "start": [-16.0, -1.5], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "explore"},
			{"t": 0.0, "k": "shot", "art": "establish", "s": -22.0, "q": -6.0, "h": 4.5, "blick": [0.0, 0.0, 2.0], "d": 4.0, "ziel": [0.0, 0.0, 2.0], "groesse": 1.5},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Die Alp Tschuggen. Regen seit Mittag."},
			{"t": 3.4, "k": "shot", "art": "schulter", "s": -18.0, "q": -1.0, "h": 1.7, "blick": [-4.0, -2.0, 1.4], "d": 3.0, "ziel": [-16.0, -1.5, 1.5], "groesse": 0.5},
			{"t": 3.6, "k": "sag", "wer": "blinki", "text": "Niederschlag: viel. Laune von Maggie: trotzdem gut."},
			{"t": 6.4, "k": "maggie_lauf", "s": -5.4, "q": -1.6}]},
		{"ziel": "Geh zur Hütte", "bis": "ort:-5.2,-2.25,1.6"},
		{"checkpoint": "tuer"},
		{"sag": "Offen. Und drinnen ist es kälter als draussen.", "wer": "figur"},
		{"film": [{"t": 0.0, "k": "wetter", "w": "cloudy"}, {"t": 0.0, "k": "zeit", "h": 17.0}]}]},
	{"id": "s02_ofen", "titel": "Kalte Stube", "start": [-1.0, 1.0], "schritte": [
		{"ziel": "Mach Feuer im Ofen (Aktion)", "bis": "aktion:ofen"},
		{"film": [
			{"t": 0.0, "k": "ofen"},
			{"t": 0.0, "k": "shot", "art": "nah", "s": 2.4, "q": 2.9, "h": 0.6, "r": 1.7, "d": 2.2, "ziel": [2.6, 3.0, 0.6], "groesse": 0.6},
			{"t": 0.3, "k": "sag", "wer": "blinki", "text": "Rauch: viel. Wärme: noch wenig. Klappe am Ofenrohr: zu. Ich sage ja nur."},
			{"t": 3.6, "k": "sag", "wer": "figur", "text": "… jetzt ist sie offen."},
			{"t": 5.4, "k": "musik", "z": "explore"}]},
		{"checkpoint": "stube"},
		{"sag": "Der {bezug} hat erzählt, auf dem Dachboden liege noch etwas von ihm.", "wer": "figur"}]},
	{"id": "s03_dachboden", "titel": "Der Dachboden", "start": [-1.0, 1.0], "schritte": [
		{"ziel": "Steig die Leiter auf den Dachboden", "bis": "aktion:dach_hoch_oben",
			"hinweise": [[12.0, "Die Leiter steht hinten rechts, neben dem Ofen.", "blinki"]]},
		{"checkpoint": "dach"},
		{"sag": "Stockdunkel hier oben.", "wer": "figur"},
		{"ziel": "Schalte die Stirnlampe ein (Aktion)", "bis": "aktion:lampe"},
		{"musik": "spannung"},
		{"ziel": "Such im Licht der Stirnlampe nach der Blechdose", "bis": "fund:dose",
			"hinweise": [[15.0, "Leuchte langsam herum: was im Licht glänzt, kann man nehmen.", "blinki"],
				[35.0, "Ganz hinten links, unter einem losen Brett.", "blinki"]]},
		{"abzeichen": "stoeberer", "wenn": "funde_alle"}]},
	{"id": "s04_karte", "titel": "Die halbe Karte", "start": [], "schritte": [
		{"film": [
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "shot", "art": "nah", "s": 0.25, "q": -3.7, "h": 0.25, "r": 1.2, "d": 1.6, "ziel": [0.25, -3.7, 0.2], "groesse": 0.35},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Eine Karte. Halb. Jemand hat sie mittendurch gerissen."},
			{"t": 3.4, "k": "karte_zeigen", "teil": "halb"},
			{"t": 3.6, "k": "sag", "wer": "blinki", "text": "Massstab 1:25 000. Eine Linie mit Bleistift. Und am Rand: «G+T»."},
			{"t": 7.4, "k": "karte_weg"}]},
		{"film": [
			{"t": 0.0, "k": "ebene", "id": "dach", "an": false},
			{"t": 0.0, "k": "setzen", "s": -1.2, "q": 2.6},
			{"t": 0.0, "k": "farbe", "art": "alt"},
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "sag", "wer": "erzaehler", "text": "{jahr}. Am selben Tisch."},
			{"t": 0.2, "k": "person", "id": "gv", "s": -1.0, "q": 1.5, "blick": [-1.8, 2.3], "jacke": [0.55, 0.32, 0.18],
				"look": {"kopf": "hut", "pack": true, "hose": [0.32, 0.3, 0.26], "umbrella": false, "lamp": ""}},
			{"t": 0.2, "k": "person", "id": "toni", "s": -2.4, "q": 3.0, "blick": [-1.8, 2.3], "jacke": [0.25, 0.4, 0.62],
				"look": {"kopf": "muetze", "pack": false, "hose": [0.2, 0.22, 0.3], "umbrella": false, "lamp": ""}},
			{"t": 0.4, "k": "shot", "art": "fix", "s": -4.2, "q": 1.6, "h": 1.7, "blick": [-1.8, 2.3, 1.1], "d": 3.0, "ziel": [-1.7, 2.2, 1.2], "groesse": 1.0},
			{"t": 3.0, "k": "sag", "wer": "toni", "text": "Wenn einer von uns nicht zurückkommt, holt der andere die Dose."},
			{"t": 6.4, "k": "sag", "wer": "grossvater", "text": "Wir kommen beide zurück, Toni. Versprochen."},
			{"t": 9.6, "k": "person_weg", "id": "gv"},
			{"t": 9.6, "k": "person_weg", "id": "toni"},
			{"t": 9.6, "k": "farbe", "art": ""}]},
		{"checkpoint": "stube"}]},
	{"id": "s05_rucksack", "titel": "Packen", "start": [-1.2, 2.6], "schritte": [
		{"sag": "Morgen geht es los. Drei Sachen passen noch in den Rucksack.", "wer": "figur"},
		{"wahl": "rucksack", "n": 3, "titel": "Rucksack packen: wähle 3 Sachen"},
		{"sag": "Gute Wahl. Wahrscheinlich. Ich hätte die Batterien genommen.", "wer": "blinki"}]},
	{"id": "s06_moveeye", "titel": "Nachtwache", "start": [-1.2, 2.6], "schritte": [
		{"film": [{"t": 0.0, "k": "zeit", "h": 19.6}, {"t": 0.0, "k": "wetter", "w": "clear"},
			{"t": 0.0, "k": "sag", "wer": "erzaehler", "text": "Der Regen hört auf. Es wird Nacht."}]},
		{"ziel": "Geh hinaus und stell MoveEye beim Weg auf (Aktion)", "bis": "aktion:moveeye",
			"ueber": [[-5.2, -2.25, 1.4]]},
		{"film": [
			{"t": 0.0, "k": "zeit", "h": 20.3},
			{"t": 0.0, "k": "ir", "an": true},
			{"t": 0.0, "k": "shot", "art": "schulter", "s": -11.0, "q": 4.5, "h": 1.6, "blick": [-8.2, 6.5, 1.2], "d": 3.0, "ziel": [-8.2, 6.5, 1.2], "groesse": 0.8},
			{"t": 0.3, "k": "sag", "wer": "blinki", "text": "MoveEye ist wach. Infrarot an. Ich sehe: Gras. Viel Gras."},
			{"t": 4.0, "k": "sag", "wer": "figur", "text": "Dann sind wir ja sicher."}]},
		{"checkpoint": "draussen"}]},
	{"id": "s07_murmeltier", "titel": "Etwas am Fenster", "start": [-6.0, 2.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "ir", "an": false},
			{"t": 0.0, "k": "tier_k1", "s": -4.95, "q": 1.5, "blick": [-3.7, 1.7]},
			{"t": 0.2, "k": "shot", "art": "fix", "s": -6.5, "q": 3.4, "h": 1.15, "blick": [-4.7, 1.45, 0.5], "d": 2.4, "ziel": [-4.95, 1.5, 0.3], "groesse": 0.4},
			{"t": 0.4, "k": "sag", "wer": "blinki", "text": "Bewegung am Fenster! Grösse: klein. Gefahr: … flauschig."},
			{"t": 3.2, "k": "maggie_warnen", "s": -5.0, "q": 1.2},
			{"t": 3.4, "k": "sag", "wer": "figur", "text": "Ein Murmeltier. Maggie, das ist kein Einbrecher."},
			{"t": 6.0, "k": "sag", "wer": "maggie", "text": "Wuff! (Doch.)"},
			{"t": 8.0, "k": "tier_weg"},
			{"t": 8.0, "k": "musik", "z": "explore"}]}]},
	{"id": "s08_holzstapel", "titel": "Maggie, such!", "start": [-6.0, 2.0], "schritte": [
		{"sag": "Die Karte ist an der Ecke abgerissen. Vielleicht liegt das Stück noch hier irgendwo …", "wer": "figur"},
		{"ziel": "Geh mit Maggie zum Holzstapel und lass sie suchen (Aktion)", "bis": "aktion:maggie_such",
			"hinweise": [[15.0, "Der Holzstapel liegt neben der Hütte, auf der Seite des Ofens.", "blinki"]]},
		{"ziel": "Warte, bis Maggie etwas bringt", "bis": "fund:kartenecke"},
		{"film": [
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "karte_zeigen", "teil": "ganz"},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Brave Maggie! Die Ecke passt."},
			{"t": 3.2, "k": "sag", "wer": "blinki", "text": "Die Linie führt hinunter in die Schlucht. Zum Bach. Und weiter."},
			{"t": 6.6, "k": "karte_weg"}]},
		{"checkpoint": "schopf"}]},
	{"id": "s09_nacht", "titel": "Sterne", "start": [-0.5, 5.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "ir", "an": false},
			{"t": 0.0, "k": "wetter", "w": "clear"},
			{"t": 0.0, "k": "shot", "art": "establish", "s": -12.0, "q": 9.0, "h": 2.4, "blick": [0.0, 0.0, 5.0], "d": 4.0, "ziel": [0.0, 0.0, 3.0], "groesse": 1.2},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Später. Der Himmel ist klar. Unten rauscht der Bach."},
			{"t": 4.0, "k": "sag", "wer": "figur", "text": "Was hast du hier oben versteckt, {bezug}?"},
			{"t": 7.4, "k": "sag", "wer": "blinki", "text": "Schlafenszeit. Ich wache. MoveEye wacht. Maggie … schnarcht."}]}]},
	{"id": "s10_morgen", "titel": "Morgen", "start": [-0.5, 5.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "zeit", "h": 9.0},
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "shot", "art": "establish", "s": -20.0, "q": -10.0, "h": 6.0, "blick": [10.0, -20.0, 0.0], "d": 4.0, "ziel": [0.0, 0.0, 2.0], "groesse": 1.0},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Am Morgen."},
			{"t": 2.6, "k": "sag", "wer": "figur", "text": "Die Linie zeigt in die Bachschlucht. Gehen wir, Maggie."},
			{"t": 5.6, "k": "sag", "wer": "maggie", "text": "Wuff!"},
			{"t": 6.0, "k": "ende", "text": "Ende von Kapitel 1 – weiter mit Kapitel 2 «Wo der Bach zweimal fällt»."}]}]},
]
