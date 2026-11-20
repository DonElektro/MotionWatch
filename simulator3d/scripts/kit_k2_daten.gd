extends RefCounted
## «Die Karte des Grossvaters» – Neubau, Kapitel 2 «Wo der Bach zweimal fällt» (Besitzer 20.11.2026, Geschichte freigegeben
## 20.11. 23:45): alle Texte, der Parcours und die 12 Szenen als DATEN für das Abenteuer-Kit (kit_abenteuer.gd). Die anderen
## Kapitel bekommen je eine eigene Datei im selben Format (kit_k1_daten.gd …).
##
## Texte: deutsche Schlüssel für T.t() (5 Sprachen über i18n/texte.json). Platzhalter in den Texten:
##   {name} Name der Spielfigur · {bezug} «Grossvater» / «Vater» · {jahr} 1974 / 2000 · {lia_bezug} «Enkelin» / «Tochter»
##   (Lia ist Tonis Enkelin bzw. Tochter, gleich wie die Spielfigur zum Grossvater / Vater steht).
##
## Ort: die Bachschlucht unterhalb der Alphütte (Tal-Koordinaten von bergtal.gd: x = Osten, z = Süden). Alles im Parcours
## wird über die ACHSE gesetzt: [s, q] = s m entlang der Schlucht (bachabwärts), q m quer dazu (+ = rechts bachabwärts).
## Höhen «h» relativ zum Boden in der Mitte des Dings (bergtal.H), «top» = Oberkante über dem Boden.
##
## Dinge (Parcours): art = stein | block | wand | tor | balken | leiter | seil | wasser | spalt | fund | fall (Wasserfall)
##   Gemeinsam: id, s, q, ls (halbe Länge entlang), lq (halbe Breite quer), top (m über Boden), dreh (Grad, zusätzlich)
##   «kante»: true = diese Oberkante kann man von unten erklettern (Kontext-Aktion «Hochklettern») - von welcher Seite: «von»
##   (Liste von [s, q], wo man davor stehen muss).
## Szenen: id, titel, start (Checkpoint [s, q]), schritte = Liste von Schritten (Ablauf in kit_abenteuer.gd szene_tick):
##   {"film": [...]}               Filmszene (kit_regie.gd spiele()): Einträge {t, k, ...} - siehe dort
##   {"ziel": Text, "bis": Bedingung}   Spielen, bis die Bedingung gilt: "ort:s,q,r" | "aktion:<id>" | "fund:<id>" | "zeit:s"
##   {"sag": Text, "wer": ...}     eine Zeile Untertitel (ohne anzuhalten)
##   {"musik": explore | spannung | action | entdeckung}
##   {"checkpoint": [s, q]}
## Rückblende: {"k": "farbe", "art": "alt"} (warm, alte Farben) in einem Film.

const KAPITEL := 2
const TITEL := "Wo der Bach zweimal fällt"

# the gorge axis: origin (valley x, z) and direction (downstream)
const ACHSE := [Vector2(66.0, -4.0), Vector2(-0.33, -0.944)]
# the place of MoveEye / the camp for this chapter (bergtal «frei»): on the west rim above the gorge
const LAGER := Vector2(40.0, -24.0)

const ROLLEN := ["enkelin", "enkel", "tochter", "sohn"]
const ROLLE_NAME := {"enkelin": "Enkelin", "enkel": "Enkel", "tochter": "Tochter", "sohn": "Sohn"}


static func bezug(rolle: String) -> Dictionary:
	"""die Platzhalter je nach Rolle (Besitzer 20.11.: Enkelin/Enkel → Grossvater 1974, Tochter/Sohn → Vater 2000)"""
	var alt := rolle in ["enkelin", "enkel"]
	return {"bezug": "Grossvater" if alt else "Vater", "jahr": "1974" if alt else "2000",
		"lia_bezug": "Enkelin" if alt else "Tochter", "jahr_kurz": "74" if alt else "00"}


# =======================================================================================================================
# the course (scenes 2–5 in the gorge)
# =======================================================================================================================
const DINGE := [
	# scene 2: the pool with stepping stones
	{"id": "gumpe", "art": "wasser", "s": 16.2, "q": 0.0, "ls": 3.1, "lq": 9.0},
	{"id": "stein1", "art": "stein", "s": 13.4, "q": 0.5, "ls": 0.55, "lq": 0.6, "top": 0.45},
	{"id": "stein2", "art": "stein", "s": 15.5, "q": -0.4, "ls": 0.5, "lq": 0.55, "top": 0.5},
	{"id": "stein3", "art": "stein", "s": 17.5, "q": 0.6, "ls": 0.5, "lq": 0.55, "top": 0.4},
	{"id": "stein4", "art": "stein", "s": 19.3, "q": -0.2, "ls": 0.45, "lq": 0.5, "top": 0.35},
	# the rock step (climb up, then down two steps)
	{"id": "stufe", "art": "block", "s": 26.0, "q": 0.0, "ls": 1.0, "lq": 9.0, "top": 1.5, "kante": true, "von": [[24.4, -1.5], [24.4, 1.5]]},
	{"id": "stufe2", "art": "block", "s": 28.0, "q": 0.0, "ls": 1.0, "lq": 9.0, "top": 0.8},
	# scene 3: the gate with the bolt; the side ledge with the window for Maggie
	{"id": "riegelwand", "art": "wand", "s": 37.0, "q": 0.0, "ls": 0.3, "lq": 9.0, "top": 2.6, "fenster": [-5.6, 0.5]},
	{"id": "tor", "art": "tor", "s": 37.0, "q": 0.8, "ls": 0.12, "lq": 1.3, "top": 2.0},
	{"id": "sims", "art": "block", "s": 35.6, "q": -5.6, "ls": 1.0, "lq": 1.0, "top": 1.5},
	# scene 4: the log over the second pool, the waterfall wall with ledge, ladder and the rope over the gap
	{"id": "gumpe2", "art": "wasser", "s": 41.3, "q": 0.0, "ls": 1.6, "lq": 9.0},
	{"id": "baum", "art": "balken", "s": 41.3, "q": 2.4, "ls": 2.6, "lq": 0.2, "top": 0.5},
	{"id": "fallwand", "art": "wand", "s": 45.0, "q": 0.0, "ls": 0.6, "lq": 9.0, "top": 4.0},
	{"id": "absatz", "art": "block", "s": 43.9, "q": -3.2, "ls": 0.55, "lq": 0.9, "top": 1.4, "kante": true, "von": [[43.0, -3.2]]},
	{"id": "leiter", "art": "leiter", "s": 44.35, "q": -3.2, "top": 4.0},
	{"id": "oben_a", "art": "block", "s": 46.1, "q": -4.4, "ls": 1.5, "lq": 3.6, "top": 4.0, "rand": true},
	{"id": "spalt", "art": "spalt", "s": 46.1, "q": 0.9, "ls": 1.5, "lq": 1.7},
	{"id": "oben_b", "art": "block", "s": 46.1, "q": 5.4, "ls": 1.5, "lq": 2.8, "top": 4.0, "rand": true},
	{"id": "seil", "art": "seil", "s": 46.1, "q": 0.9, "von": [46.1, -1.4], "nach": [46.1, 3.3], "top": 4.0},
	{"id": "wasserfall", "art": "fall", "s": 46.6, "q": 0.9, "top": 4.0, "breite": 1.4},
	# scene 5: the carabiner
	{"id": "karabiner", "art": "fund", "s": 46.4, "q": 6.2, "top": 4.0, "name": "Karabiner «G+T {jahr_kurz}»"},
]

# context actions (trigger volumes): id, art, [s, q] where you stand, r (m), plus what the action needs
const AKTIONEN := [
	{"id": "steine", "art": "steine", "s": 11.6, "q": 0.2, "r": 1.6, "kette": ["stein1", "stein2", "stein3", "stein4"], "nach": [21.0, 0.0]},
	{"id": "stufe_hoch", "art": "kante", "s": 24.6, "q": 0.0, "r": 6.0, "ding": "stufe"},
	{"id": "maggie_heben", "art": "maggie_heben", "s": 34.6, "q": -4.3, "r": 1.3, "ding": "sims", "nach": [35.6, -5.6]},
	{"id": "maggie_spalt", "art": "maggie_steuern", "s": 35.6, "q": -5.6, "r": 0.0, "ziel": [37.9, 0.2], "riegel": "tor"},
	{"id": "baum_balance", "art": "balance", "s": 39.4, "q": 2.4, "r": 1.3, "ding": "baum"},
	{"id": "absatz_hoch", "art": "kante", "s": 43.1, "q": -3.2, "r": 1.4, "ding": "absatz"},
	{"id": "leiter_hoch", "art": "leiter", "s": 43.9, "q": -3.2, "r": 0.9, "ding": "leiter", "oben": [45.4, -3.2]},
	{"id": "seil_schwingen", "art": "seil", "s": 46.1, "q": -1.9, "r": 1.0, "ding": "seil"},
	{"id": "karabiner_nehmen", "art": "fund", "s": 46.4, "q": 6.2, "r": 1.2, "ding": "karabiner"},
]

# the soft guide: the way through the gorge (s, q) - the figure is pulled back gently when it leaves the corridor
const WEG := [[0.0, 0.0], [10.5, 0.2], [21.0, 0.0], [24.0, 0.0], [31.0, 0.0], [34.6, -3.0], [38.5, 0.8], [39.4, 2.4],
		[43.6, 2.4], [43.1, -3.2]]
const WEG_BREITE := 5.5

const CHECKPOINTS := {"start": [2.0, 0.0], "steine": [21.0, 0.0], "stufe": [31.0, 0.0], "tor": [39.0, 0.8],
		"wand": [43.0, -2.0], "oben": [45.6, -4.6], "fund": [46.2, 5.0]}

# =======================================================================================================================
# who speaks (subtitle colour) and the badges
# =======================================================================================================================
const SPRECHER := {"erzaehler": ["", Color(0.92, 0.94, 0.97)], "figur": ["{name}", Color(1.0, 0.86, 0.55)],
		"grossvater": ["{bezug}", Color(0.95, 0.78, 0.55)], "toni": ["Toni", Color(0.7, 0.85, 1.0)],
		"lia": ["Lia", Color(1.0, 0.6, 0.55)], "blinki": ["Blinki", Color(0.55, 0.9, 1.0)], "maggie": ["Maggie", Color(1.0, 0.8, 0.4)]}

const ABZEICHEN := {"trockene_fuesse": ["Trockene Füsse", "Die Schlucht ohne einen Fuss im Wasser geschafft."],
		"bruecken_sprinter": ["Brücken-Sprinter", "Über die Hängebrücke, bevor sie einstürzt – ohne anzuhalten."],
		"maggies_held": ["Maggies Held", "Maggie gefangen, als die Brücke fiel."],
		"alle_funde": ["Alle Funde", "Karabiner, Foto und Tagebuchfetzen gefunden."]}

const FUNDE := {"karabiner": ["Karabiner «G+T {jahr_kurz}»", "Ein alter Stahlkarabiner. Jemand hat «G+T {jahr_kurz}» hineingeritzt."],
		"foto": ["Altes Foto", "Zwei junge Bergführer auf dem Grat, lachend. Auf der Rückseite: «Toni und ich, {jahr}»."],
		"tagebuch": ["Tagebuchfetzen", "«… der Sturm kam schneller als gedacht. Ich habe es ihm versprochen.»"]}

# =======================================================================================================================
# the 12 scenes of chapter 2 (as approved 20.11.2026). Scenes 6–12 are only partly built in this round (kit first).
# =======================================================================================================================
const SZENEN := [
	{"id": "s01_cold_open", "titel": "Sturm am Grat", "start": [2.0, 0.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "action"},
			{"t": 0.0, "k": "wetter", "w": "storm"},
			{"t": 0.0, "k": "shot", "art": "establish", "s": 46.0, "q": -9.0, "h": 14.0, "blick": [46.0, 0.0, 3.0], "d": 4.0},
			{"t": 0.3, "k": "sag", "wer": "erzaehler", "text": "Der Grat. Sturm. Und nur noch eine Hand am Fels."},
			{"t": 0.0, "k": "figur_haengen", "s": 46.1, "q": -1.0},
			{"t": 4.0, "k": "shot", "art": "schulter", "d": 3.0},
			{"t": 4.2, "k": "sag", "wer": "figur", "text": "Halt durch … halt durch!"},
			{"t": 7.0, "k": "spiel_haengen"}]},
		{"ziel": "Zieh dich hoch! (Springen/Greifen mehrmals tippen)", "bis": "aktion:haengen"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "zeitlupe", "f": 0.35, "s": 1.2},
			{"t": 0.2, "k": "sag", "wer": "erzaehler", "text": "Drei Tage vorher."},
			{"t": 0.0, "k": "blende", "s": 2.4},
			{"t": 2.4, "k": "wetter", "w": "clear"},
			{"t": 2.4, "k": "figur_setzen", "s": 2.0, "q": 0.0},
			{"t": 2.4, "k": "musik", "z": "explore"}]}]},
	{"id": "s02_schlucht", "titel": "Die Schlucht", "start": [2.0, 0.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "establish", "s": -6.0, "q": 2.0, "h": 9.0, "blick": [18.0, 0.0, 0.5], "d": 4.5},
			{"t": 0.4, "k": "sag", "wer": "erzaehler", "text": "Die Karte des {bezug}s führt in die Bachschlucht unter der Alp."},
			{"t": 4.5, "k": "shot", "art": "schulter", "d": 2.5},
			{"t": 4.6, "k": "sag", "wer": "blinki", "text": "Luftfeuchtigkeit 94 Prozent. Rutschgefahr: hoch. Stimmung: abenteuerlich."},
			{"t": 7.0, "k": "zug", "wer": "maggie", "s": 6.0, "q": 0.8}]},
		{"checkpoint": "start"},
		{"musik": "explore"},
		{"ziel": "Folge dem Bach durch die Schlucht", "bis": "ort:10.5,0.0,2.5"},
		{"sag": "Steine im Wasser … mit einem Sprung von Stein zu Stein.", "wer": "figur"},
		{"ziel": "Spring über die Steine (Springen)", "bis": "ort:21.0,0.0,2.2"},
		{"checkpoint": "steine"},
		{"ziel": "Klettere die Felsstufe hoch (Aktion)", "bis": "ort:31.0,0.0,2.5"},
		{"checkpoint": "stufe"}]},
	{"id": "s03_maggie_riegel", "titel": "Maggies Weg", "start": [31.0, 0.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "reveal", "s": 33.0, "q": 2.5, "h": 1.0, "blick": [37.0, 0.8, 1.4], "d": 3.5},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Ein Gatter. Und der Riegel ist auf der anderen Seite."},
			{"t": 3.0, "k": "sag", "wer": "blinki", "text": "Analyse: Dort oben ist ein Spalt. Zu klein für dich. Genau richtig für einen Terrier."},
			{"t": 6.0, "k": "zug", "wer": "maggie", "s": 34.0, "q": -3.6}]},
		{"musik": "spannung"},
		{"ziel": "Heb Maggie auf den Felssims (Aktion)", "bis": "aktion:maggie_heben"},
		{"sag": "Hopp, Maggie! Durch den Spalt – und zieh am Riegel!", "wer": "figur"},
		{"ziel": "Steuere Maggie durch den Spalt zum Riegel", "bis": "aktion:maggie_spalt"},
		{"film": [
			{"t": 0.0, "k": "shot", "art": "fix", "s": 39.5, "q": 3.5, "h": 1.4, "blick": [37.0, 0.8, 0.8], "d": 2.2},
			{"t": 0.2, "k": "ton", "name": "riegel"},
			{"t": 0.5, "k": "tor_auf", "ding": "tor"},
			{"t": 0.8, "k": "sag", "wer": "figur", "text": "Brave Maggie!"},
			{"t": 0.8, "k": "abzeichen_merken", "id": "maggie_riegel"}]},
		{"musik": "explore"},
		{"ziel": "Geh durch das Gatter", "bis": "ort:39.0,0.8,1.8"},
		{"checkpoint": "tor"}]},
	{"id": "s04_wasserfall", "titel": "Am Wasserfall", "start": [39.0, 0.8], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "reveal", "s": 40.0, "q": -6.0, "h": 0.6, "blick": [46.4, 0.9, 4.5], "d": 4.0},
			{"t": 0.4, "k": "musik", "z": "entdeckung"},
			{"t": 0.6, "k": "sag", "wer": "erzaehler", "text": "Wo der Bach zum ersten Mal fällt."},
			{"t": 3.5, "k": "sag", "wer": "maggie", "text": "Wuff!"}]},
		{"musik": "spannung"},
		{"ziel": "Balanciere über den Baumstamm", "bis": "ort:43.4,2.4,1.6"},
		{"checkpoint": "wand"},
		{"ziel": "Klettere über den Absatz und die Leiter hoch", "bis": "ort:45.6,-4.6,1.8"},
		{"checkpoint": "oben"},
		{"musik": "action"},
		{"ziel": "Schwing dich am Seil über den Spalt (Aktion, dann Springen)", "bis": "ort:46.1,4.6,1.4"},
		{"checkpoint": "fund"},
		{"musik": "explore"}]},
	{"id": "s05_karabiner", "titel": "Der Karabiner", "start": [46.2, 5.0], "schritte": [
		{"ziel": "Da glitzert etwas im Fels", "bis": "fund:karabiner"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "shot", "art": "nah", "s": 46.4, "q": 6.2, "h": 4.9, "d": 3.5},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Ein Karabiner. Da ist etwas eingeritzt: «G+T {jahr_kurz}»."},
			{"t": 3.6, "k": "sag", "wer": "blinki", "text": "G wie {bezug}. T wie … unbekannt. Ich lege eine Akte an."}]}]},
	{"id": "s06_bruecke", "titel": "Die Hängebrücke", "offen": true, "schritte": []},
	{"id": "s07_steinmann", "titel": "Der Steinmann", "offen": true, "schritte": []},
	{"id": "s08_rueckblende", "titel": "{jahr}", "offen": true, "schritte": [
		{"film": [
			{"t": 0.0, "k": "farbe", "art": "alt"},
			{"t": 0.3, "k": "sag", "wer": "toni", "text": "Wer zuerst oben ist, zahlt den Kaffee!"},
			{"t": 3.0, "k": "sag", "wer": "grossvater", "text": "Dann such schon mal dein Portemonnaie, Toni."},
			{"t": 6.0, "k": "farbe", "art": ""}]}]},
	{"id": "s09_funde", "titel": "Foto und Tagebuch", "offen": true, "schritte": []},
	{"id": "s10_lia", "titel": "Lia", "offen": true, "schritte": [
		{"sag": "Zu langsam. 😉", "wer": "lia"}]},
	{"id": "s11_nachtlager", "titel": "Nachtlager", "offen": true, "schritte": []},
	{"id": "s12_cliffhanger", "titel": "Das leere Zelt", "offen": true, "schritte": [
		{"sag": "«Er hat mich zurückgelassen.»", "wer": "toni"}]},
]
