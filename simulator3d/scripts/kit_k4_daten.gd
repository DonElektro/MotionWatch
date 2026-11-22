extends RefCounted
## «Die Karte des Grossvaters» – Kapitel 4 «Nebel im Couloir» (Phase 2, Besitzer 21.11.2026): mit Lia und Maggie vom
## Gumpisee hinauf zum alten Biwak. Nebel im Couloir (neu: das Wärmebild von MoveEye findet Lia und Maggie), auf Kurs nach
## Kompass (neu: Peilung ohne Leuchtpunkt), angeseilt über die Felsstufen (neu: Seilpartnerin Lia – erst einhängen, dann
## klettern), Querung am Stahlseil über den Spalt (an jedem Anker umhängen), Steinschlag (warnen!), Maggie im Rucksack,
## das Biwak und sein Buch von {jahr}. Rückblende: der Sturm – der {bezug} steigt ab, Hilfe holen; Toni soll warten. Der
## Eintrag der Rettung: «Toni nicht mehr da.» Ein Missverständnis, kein Verrat. Am Abend: hinauf zum Grat, zum Sonnenaufgang.
##
## Format wie kit_k2_daten.gd; das Couloir baut kit_schlucht.gd (SCHLUCHT) am Osthang über dem Gumpisee.
## Achse: s = x − 138 (hinauf nach Osten), q = z + 400 (+ = Süden). Neue Teile in kit_k4.gd.

const KAPITEL := 4
const TITEL := "Nebel im Couloir"
const ENDE := "Ende von Kapitel 4 – Fortsetzung folgt."

const ACHSE := [Vector2(138.0, -400.0), Vector2(1.0, 0.0)]
const LAGER := Vector2(96.0, -372.0)
const START := {"wetter": "fog", "stunde": 9.5}

# the couloir: floor (valley y) along s, half width of the floor, a cut across the floor for the traverse (only a strip on the
# north side stays, along the wall with the steel cable)
const SCHLUCHT := {"mitte": Vector2(138.0, -400.0), "achse": Vector2(1.0, 0.0), "s": [-2.0, 62.0], "q": 22.0,
		"boden": [[-2.0, 70.0], [0.0, 70.15], [12.0, 70.2], [16.0, 72.0], [20.0, 73.9], [24.0, 76.3], [28.0, 79.1], [32.0, 81.8],
			[36.0, 84.7], [40.0, 87.7], [44.0, 90.9], [47.0, 93.8], [50.0, 96.6], [53.0, 98.8], [56.0, 99.3], [62.0, 99.4]],
		"breite": [[-2.0, 5.5], [12.0, 4.6], [30.0, 4.3], [44.0, 4.6], [50.0, 8.0], [56.0, 12.0], [62.0, 12.0]],
		"kanal": [[34.6, 40.4, -2.6, 6.0, 78.0]]}

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
	# scene 4: three rock steps, a bolt at the foot of each (clip in first, then climb)
	{"id": "stufe1", "art": "block", "s": 24.2, "q": 0.0, "ls": 0.6, "lq": 4.6, "top": 1.35, "kante": true, "von": [[23.2, 0.0]]},
	{"id": "stufe2", "art": "block", "s": 28.2, "q": 0.0, "ls": 0.6, "lq": 4.6, "top": 1.35, "kante": true, "von": [[27.2, 0.0]]},
	{"id": "stufe3", "art": "block", "s": 32.2, "q": 0.0, "ls": 0.6, "lq": 4.6, "top": 1.35, "kante": true, "von": [[31.2, 0.0]]},
	# scene 5: the cleft across the floor (only the strip along the north wall stays) - falling in: back to the checkpoint
	{"id": "spalt", "art": "spalt", "s": 37.5, "q": 1.7, "ls": 2.9, "lq": 4.3},
	# scene 8: the logbook in the old bivouac
	{"id": "logbuch", "art": "fund", "s": 55.15, "q": 2.6, "top": 0.8},
]

# kit_k4.gd: the bolts of the rope pitch, the anchors of the steel cable, the bivouac, the rock fall
const SEIL := {"haken": [["haken1", 23.3, -1.2, 1.5], ["haken2", 27.3, -1.2, 1.5], ["haken3", 31.3, -1.2, 1.5]],
		"lia_stand": [[21.2, 1.0], [25.4, 1.0], [29.4, 1.0], [33.6, 1.0]]}
const KLETTERSTEIG := {"anker": [["anker1", 34.8, -4.0], ["anker2", 37.5, -4.0], ["anker3", 40.2, -4.0]], "seil_h": 1.25,
		"vor": 0.35}
const BIWAK := {"c": [54.0, 2.4], "gross": [3.4, 4.2], "tuer": "west"}
const PEILUNG := {"von": [11.0, 0.0], "nach": [21.5, 0.4]}
# the bivouac: the camera stays under its roof and inside its walls (like the hut of Kapitel 1)
const DECKEN := [{"s": 54.0, "q": 2.4, "ls": 1.7, "lq": 2.1, "unten": 2.3, "oben": 2.3, "trenn": 9.0}]
const WAERME := {"lia": [15.5, 1.2], "maggie": [14.6, -0.8]}

const AKTIONEN := [
	{"id": "waerme", "art": "waerme", "s": 4.0, "q": 0.0, "r": 9.0},
	{"id": "haken1", "art": "haken", "s": 23.25, "q": 0.0, "r": 1.4},
	{"id": "stufe1_hoch", "art": "kante", "s": 23.3, "q": 0.0, "r": 1.4, "ding": "stufe1"},
	{"id": "haken2", "art": "haken", "s": 27.25, "q": 0.0, "r": 1.4},
	{"id": "stufe2_hoch", "art": "kante", "s": 27.3, "q": 0.0, "r": 1.4, "ding": "stufe2"},
	{"id": "haken3", "art": "haken", "s": 31.25, "q": 0.0, "r": 1.4},
	{"id": "stufe3_hoch", "art": "kante", "s": 31.3, "q": 0.0, "r": 1.4, "ding": "stufe3"},
	{"id": "anker1", "art": "anker", "s": 34.6, "q": -3.6, "r": 1.1},
	{"id": "anker2", "art": "anker", "s": 37.3, "q": -3.6, "r": 1.1},
	{"id": "anker3", "art": "anker", "s": 40.0, "q": -3.6, "r": 1.1},
	{"id": "logbuch_nehmen", "art": "fund", "s": 54.6, "q": 2.6, "r": 1.3, "ding": "logbuch"},
]

const WEG := [[2.0, 0.0], [11.0, 0.0], [21.5, 0.4], [23.0, 0.0], [33.6, 0.0], [34.4, -3.6], [40.6, -3.6], [42.0, 0.0], [50.0, 1.0], [52.0, 1.6]]
const WEG_BREITE := 4.5
const WEGE := {
	"s05_querung": [[33.4, -1.0], [34.4, -3.6], [40.6, -3.6], [42.0, -1.0]],
}

const CHECKPOINTS := {"start": [2.0, 0.0], "peilung": [11.0, 0.0], "seil": [21.6, 0.4], "querung": [33.6, -2.4],
		"oben": [42.2, 0.0], "biwak": [49.6, 0.6]}

# =======================================================================================================================
# who speaks, badges, finds
# =======================================================================================================================
const SPRECHER := {"erzaehler": ["", Color(0.92, 0.94, 0.97)], "figur": ["{name}", Color(1.0, 0.86, 0.55)],
		"grossvater": ["{bezug}", Color(0.95, 0.78, 0.55)], "toni": ["Toni", Color(0.7, 0.85, 1.0)],
		"lia": ["Lia", Color(1.0, 0.6, 0.55)], "blinki": ["Blinki", Color(0.55, 0.9, 1.0)], "maggie": ["Maggie", Color(1.0, 0.8, 0.4)]}

const ABZEICHEN := {"seilschaft": ["Seilschaft", "Am Stahlseil über den Spalt ohne Sturz – und Lia vor dem Steinschlag gewarnt."]}

const FUNDE_ALLE := []
const FUNDE := {"logbuch": ["Biwakbuch {jahr}", "Das alte Buch des Biwaks. Die letzte Seite von {jahr} ist voller Regenflecken."]}

const LIA := {"jacke": [0.86, 0.35, 0.3], "look": {"kopf": "zopf", "pack": true, "hose": [0.18, 0.2, 0.24], "umbrella": false, "lamp": ""}}

# =======================================================================================================================
# the 12 scenes
# =======================================================================================================================
const SZENEN := [
	{"id": "s01_nebel", "titel": "Nebel", "start": [2.0, 0.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "nebel", "an": true},
			{"t": 0.0, "k": "shot", "art": "fix", "s": -1.5, "q": 2.6, "h": 1.7, "blick": [6.0, -0.5, 1.4], "d": 6.0, "ziel": [2.0, 0.0, 0.0], "groesse": 1.7},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Am Morgen. Das Couloir über dem Gumpisee. Nebel."},
			{"t": 2.8, "k": "maggie_lauf", "s": 14.6, "q": -0.8},
			{"t": 2.8, "k": "person_k4", "id": "lia", "s": 15.5, "q": 1.2},
			{"t": 3.0, "k": "sag", "wer": "lia", "text": "Ich geh schon mal vor. Maggie kommt mit, die kennt den Weg."},
			{"t": 6.2, "k": "sag", "wer": "figur", "text": "Lia? … Maggie? Ich sehe keine drei Meter weit!"},
			{"t": 9.0, "k": "sag", "wer": "blinki", "text": "Augen: nutzlos. Wärmebild: nicht nutzlos. MoveEye hat eins."}]},
		{"checkpoint": "start"},
		{"ziel": "Schalte das Wärmebild von MoveEye ein (Aktion)", "bis": "aktion:waerme"},
		{"sag": "Im Wärmebild leuchtet, was warm ist: Menschen, Hunde – nicht der Nebel.", "wer": "blinki"}]},
	{"id": "s02_waerme", "titel": "Wärmebild", "start": [2.0, 0.0], "schritte": [
		{"ziel": "Finde Lia und Maggie im Nebel (Wärmebild)", "bis": "ort:15.0,0.4,2.4",
			"hinweise": [[20.0, "Zwei warme Flecken, weiter oben im Couloir. Geh darauf zu.", "blinki"]]},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "waerme", "an": false},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 11.8, "q": 2.4, "h": 1.6, "blick": [15.4, 0.6, 1.2], "d": 6.0, "ziel": [15.5, 1.2, 0.0], "groesse": 1.7},
			{"t": 0.3, "k": "sag", "wer": "lia", "text": "Na endlich. Ich dachte schon, du gehst im Nebel verloren."},
			{"t": 3.4, "k": "sag", "wer": "figur", "text": "Du bist einfach abgehauen!"},
			{"t": 5.6, "k": "sag", "wer": "lia", "text": "Ich war fünf Meter vor dir. In Nebel-Metern sind das viele."},
			{"t": 8.4, "k": "sag", "wer": "maggie", "text": "Wuff!"}]}]},
	{"id": "s03_peilung", "titel": "Auf Kurs", "start": [11.0, 0.0], "schritte": [
		{"checkpoint": "peilung"},
		{"sag": "Die Karte zeigt eine Linie durchs Couloir. Mit dem Kompass finden wir sie – auch ohne Sicht.", "wer": "figur"},
		{"ziel": "Geh auf Kurs durch den Nebel – nur nach dem Kompass", "bis": "ort:21.5,0.4,1.8", "peilung": true,
			"hinweise": [[25.0, "Die gelbe Marke auf dem Kompass ist der Kurs. Halte sie in der Mitte.", "blinki"]]},
		{"sag": "Hier wird es steil. Felsstufen – und alte Bohrhaken!", "wer": "figur"}]},
	{"id": "s04_seil", "titel": "Seilschaft", "start": [21.6, 0.4], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "nebel", "an": false},
			{"t": 0.0, "k": "seil_an"},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 19.0, "q": 3.4, "h": 1.8, "blick": [22.4, 0.2, 1.1], "d": 6.0, "ziel": [21.8, 0.4, 0.0], "groesse": 1.7},
			{"t": 0.3, "k": "sag", "wer": "lia", "text": "Ab hier seilen wir uns an. Ich sichere dich."},
			{"t": 3.2, "k": "sag", "wer": "lia", "text": "An jedem Haken: erst einhängen, dann klettern. Sonst bleibst du am Seil hängen."},
			{"t": 6.6, "k": "sag", "wer": "blinki", "text": "Ich hänge mich nirgends ein. Ich schwebe."}]},
		{"checkpoint": "seil"},
		{"ziel": "Häng das Seil in den Haken und klettere die Stufen hinauf (Aktion)", "bis": "ort:33.4,0.0,1.4",
			"hinweise": [[25.0, "Am Haken: Aktion = einhängen. Danach an der Kante: Aktion = hochklettern.", "lia"]]},
		{"sag": "Gut gemacht. Jetzt kommt der Spalt – da hilft nur das Stahlseil an der Wand.", "wer": "lia"}]},
	{"id": "s05_querung", "titel": "Am Stahlseil", "start": [33.6, -2.4], "schritte": [
		{"checkpoint": "querung"},
		{"ziel": "Quere am Stahlseil über den Spalt – an jedem Anker umhängen (Aktion)", "bis": "ort:41.6,-2.0,1.4",
			"hinweise": [[25.0, "Der schmale Absatz an der linken Wand. Vor jedem Anker: Aktion, dann weiter.", "lia"]]},
		{"sag": "Geschafft! Und kein Blick nach unten.", "wer": "figur"}]},
	{"id": "s06_steinschlag", "titel": "Steinschlag", "start": [42.2, 0.0], "schritte": [
		{"checkpoint": "oben"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "action"},
			{"t": 0.0, "k": "seil_aus"},
			{"t": 0.0, "k": "person_k4", "id": "lia", "s": 39.6, "q": -3.6},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 42.6, "q": 0.4, "h": 2.0, "blick": [40.0, -3.0, 1.1], "d": 4.0, "ziel": [39.6, -3.6, 0.0], "groesse": 1.7},
			{"t": 0.4, "k": "steinschlag"},
			{"t": 0.5, "k": "qte", "id": "lia_gewarnt", "text": "Steinschlag! – Warnen!", "s": 1.8},
			{"t": 0.6, "k": "sag", "wer": "blinki", "text": "Achtung – oben löst sich Fels!"},
			{"t": 2.6, "k": "lia_reagiert"},
			{"t": 3.6, "k": "musik", "z": "explore"}]},
		{"abzeichen": "seilschaft", "wenn": "merker:seilschaft"}]},
	{"id": "s07_rucksack", "titel": "Maggie im Rucksack", "start": [42.2, 0.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 45.0, "q": -2.0, "h": 1.5, "blick": [42.3, 0.2, 1.1], "d": 5.0, "ziel": [42.2, 0.0, 0.0], "groesse": 1.7},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Maggie mag nicht mehr. Na komm – rein in den Rucksack."},
			{"t": 2.6, "k": "maggie_rucksack", "an": true},
			{"t": 3.0, "k": "sag", "wer": "blinki", "text": "Zusatzgewicht: sieben Komma vier Kilo. Moral der Truppe: steigend."},
			{"t": 6.0, "k": "sag", "wer": "maggie", "text": "Wuff. (Bequem.)"}]},
		{"ziel": "Steig mit Maggie im Rucksack hinauf zur Schulter", "bis": "ort:50.0,1.0,2.2"}]},
	{"id": "s08_biwak", "titel": "Das Biwak", "start": [49.6, 0.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "maggie_rucksack", "an": false},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 47.2, "q": -1.6, "h": 2.2, "blick": [52.2, 1.8, 1.3], "d": 6.0, "ziel": [52.0, 1.8, 0.0], "groesse": 2.4},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Das alte Biwak. Seit {jahr} hat sich hier wenig verändert."},
			{"t": 3.2, "k": "sag", "wer": "lia", "text": "Hier haben sie übernachtet. Toni und dein {bezug}."}]},
		{"checkpoint": "biwak"},
		{"musik": "explore"},
		{"ziel": "Such im Biwak das alte Biwakbuch", "bis": "fund:logbuch",
			"hinweise": [[25.0, "Drinnen, auf dem Brett an der hinteren Wand.", "lia"]]}]},
	{"id": "s09_rueckblende", "titel": "{jahr}", "start": [49.6, 0.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "blende", "s": 1.6},
			{"t": 0.8, "k": "farbe", "art": "alt"},
			{"t": 0.8, "k": "wetter", "w": "rain"},
			{"t": 0.8, "k": "zeit", "h": 15.2},
			{"t": 0.8, "k": "setzen", "s": 44.0, "q": 6.0},
			{"t": 0.8, "k": "person_weg", "id": "lia"},
			{"t": 0.8, "k": "person", "id": "gv", "s": 51.6, "q": 1.2, "blick": [52.0, 1.8], "jacke": [0.55, 0.32, 0.18],
				"look": {"kopf": "hut", "pack": true, "hose": [0.32, 0.3, 0.26], "umbrella": false, "lamp": ""}},
			{"t": 0.8, "k": "person", "id": "toni", "s": 52.2, "q": 3.4, "blick": [51.6, 1.2], "jacke": [0.25, 0.4, 0.62],
				"look": {"kopf": "muetze", "pack": true, "hose": [0.2, 0.22, 0.3], "umbrella": false, "lamp": ""}},
			{"t": 0.8, "k": "shot", "art": "fix", "s": 48.0, "q": 5.6, "h": 1.7, "blick": [52.0, 2.2, 1.3], "d": 14.0, "ziel": [51.9, 2.3, 0.0], "groesse": 1.8},
			{"t": 1.2, "k": "sag", "wer": "erzaehler", "text": "{jahr}. Der Sturm kam schneller als gedacht."},
			{"t": 3.8, "k": "sag", "wer": "toni", "text": "Mein Knöchel … ich komme nicht weiter."},
			{"t": 6.4, "k": "sag", "wer": "grossvater", "text": "Bleib im Biwak, Toni. Ich steige ab und hole Hilfe. Ich komme zurück. Versprochen."},
			{"t": 11.2, "k": "zug", "wer": "gv", "s": 38.0, "q": -1.0},
			{"t": 11.4, "k": "sag", "wer": "toni", "text": "Ich warte. Wohin sollte ich auch gehen …"},
			{"t": 15.0, "k": "blende", "s": 1.6},
			{"t": 15.8, "k": "farbe", "art": ""},
			{"t": 15.8, "k": "wetter", "w": "cloudy"},
			{"t": 15.8, "k": "zeit", "h": 18.4},
			{"t": 15.8, "k": "person_weg", "id": "gv"},
			{"t": 15.8, "k": "person_weg", "id": "toni"},
			{"t": 15.8, "k": "setzen", "s": 49.6, "q": 0.6}]}]},
	{"id": "s10_eintrag", "titel": "Der Eintrag", "start": [49.6, 0.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "person_k4", "id": "lia", "s": 51.3, "q": -0.5},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 48.2, "q": 2.4, "h": 1.6, "blick": [51.1, 0.3, 1.2], "d": 10.0, "ziel": [51.1, 0.3, 0.0], "groesse": 1.7},
			{"t": 0.3, "k": "logbuch_zeigen"},
			{"t": 0.4, "k": "sag", "wer": "figur", "text": "Die letzte Seite. Ein anderer Name … die Bergrettung."},
			{"t": 3.2, "k": "sag", "wer": "erzaehler", "text": "«Zwei Tage nach dem Sturm. Biwak leer. Toni nicht mehr da. Keine Spur.»"},
			{"t": 7.6, "k": "logbuch_weg"},
			{"t": 7.8, "k": "sag", "wer": "figur", "text": "Er ist nicht abgehauen. Er hat Hilfe geholt – und Toni war schon weg."},
			{"t": 11.2, "k": "sag", "wer": "lia", "text": "Und Toni dachte die ganze Zeit, er hätte ihn zurückgelassen."}]}]},
	{"id": "s11_still", "titel": "Still", "start": [49.6, 0.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 48.6, "q": 2.8, "h": 1.5, "blick": [51.3, -0.5, 1.1], "d": 8.0, "ziel": [51.3, -0.5, 0.0], "groesse": 1.7},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Lia sagt lange nichts."},
			{"t": 3.0, "k": "sag", "wer": "blinki", "text": "Witz zur Auflockerung: Was macht ein Biwak bei Nebel? … Nichts. Es steht da."},
			{"t": 6.6, "k": "sag", "wer": "blinki", "text": "Verstanden. Ich bin dann mal still."},
			{"t": 9.2, "k": "sag", "wer": "lia", "text": "So lange hat er geglaubt, er sei allein gelassen worden."}]}]},
	{"id": "s12_nacht", "titel": "Zum Grat", "start": [49.6, 0.6], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "zeit", "h": 21.9},
			{"t": 0.0, "k": "wetter", "w": "clear"},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 46.6, "q": -2.6, "h": 2.0, "blick": [53.0, 2.4, 3.0], "d": 12.0, "ziel": [52.0, 1.8, 0.0], "groesse": 2.4},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Die Nacht kommt. Über dem Biwak die Sterne."},
			{"t": 3.0, "k": "sag", "wer": "figur", "text": "Die Karte endet oben am Grat. Beim Sonnenaufgang."},
			{"t": 6.0, "k": "sag", "wer": "lia", "text": "Dann gehen wir in der Nacht. Mit Stirnlampen. Zusammen."},
			{"t": 9.0, "k": "sag", "wer": "maggie", "text": "Wuff!"},
			{"t": 11.0, "k": "ende", "text": "Ende von Kapitel 4 – Fortsetzung folgt."}]}]},
]
