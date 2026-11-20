extends RefCounted
## «Die Karte des Grossvaters» – Neubau, Kapitel 2 «Wo der Bach zweimal fällt» (Besitzer 20.11.2026, Geschichte freigegeben
## 20.11. 23:45): alle Texte, der Parcours und die 12 Szenen als DATEN für das Abenteuer-Kit (kit_abenteuer.gd). Die anderen
## Kapitel bekommen je eine eigene Datei im selben Format (kit_k1_daten.gd …).
##
## Texte: deutsche Schlüssel für T.t() (5 Sprachen über i18n/texte.json). Platzhalter in den Texten:
##   {name} Name der Spielfigur · {bezug} «Grossvater» / «Vater» · {jahr} 1974 / 2000 · {lia_bezug} «Enkelin» / «Tochter»
##   (Lia ist Tonis Enkelin bzw. Tochter, gleich wie die Spielfigur zum Grossvater / Vater steht).
##
## Ort: eine eigene Schlucht westlich der Alphütte (SCHLUCHT, gebaut von kit_schlucht.gd – unabhängig vom Bach-Einschnitt
## von bergtal.gd). Tal-Koordinaten von bergtal.gd: x = Osten, z = Süden. Alles im Parcours wird über die ACHSE gesetzt:
## [s, q] = s m entlang der Schlucht (bachaufwärts, so geht man), q m quer dazu (+ = rechts in Gehrichtung).
## «top» = Oberkante über dem Boden an der Vorderkante des Dings (s − ls: von dort kommt man); Boden = Schlucht-Gelände.
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
const ACHSE := [Vector2(-40.0, -40.0), Vector2(-0.055, 0.998)]
# the place of MoveEye / the camp for this chapter (bergtal «frei»): on the rim above the gorge
const LAGER := Vector2(-22.0, -9.0)
# the gorge set (kit_schlucht.gd): centre and axis like ACHSE; s from … to, half width of the whole set (q);
# boden = floor height (valley y) along s; breite = half width of the floor; kanal = [s0, s1, q0, q1, floor y] (the cleft
# of the stream in the upper terrace - only the rope gets you across)
const SCHLUCHT := {"mitte": Vector2(-40.0, -40.0), "achse": Vector2(-0.055, 0.998), "s": [-14.0, 66.0], "q": 30.0,
		"boden": [[-14.0, 127.6], [0.0, 128.0], [12.0, 128.3], [13.0, 128.4], [19.5, 128.4], [24.0, 128.6], [25.95, 128.7],
			[26.05, 130.2], [37.0, 130.5], [39.5, 130.6], [43.2, 130.6], [44.5, 130.7], [44.65, 134.7], [60.0, 135.5], [66.0, 136.0]],
		"breite": [[-14.0, 5.0], [0.0, 7.5], [16.0, 9.5], [30.0, 8.0], [37.0, 9.0], [42.0, 9.5], [46.0, 9.0], [56.0, 7.0], [66.0, 6.0]],
		"kanal": [[44.6, 60.0, -0.8, 2.6, 132.6], [52.0, 56.0, -3.0, 5.0, 132.6]]}

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
	{"id": "bach", "art": "bach", "s": 0.0, "q": 0.6, "breite": 1.6, "teile": [[-14.0, 25.9], [26.1, 44.3], [44.7, 59.4]]},
	{"id": "gumpe", "art": "wasser", "s": 16.2, "q": 0.0, "ls": 3.1, "lq": 9.0},
	{"id": "stein1", "art": "stein", "s": 13.4, "q": 0.5, "ls": 0.55, "lq": 0.6, "top": 0.45},
	{"id": "stein2", "art": "stein", "s": 15.5, "q": -0.4, "ls": 0.5, "lq": 0.55, "top": 0.5},
	{"id": "stein3", "art": "stein", "s": 17.5, "q": 0.6, "ls": 0.5, "lq": 0.55, "top": 0.4},
	{"id": "stein4", "art": "stein", "s": 19.3, "q": -0.2, "ls": 0.45, "lq": 0.5, "top": 0.35},
	# the rock step (climb up, then down two steps)
	{"id": "stufe", "art": "block", "s": 26.0, "q": 0.0, "ls": 1.0, "lq": 9.0, "top": 1.5, "kante": true, "von": [[24.4, -1.5], [24.4, 1.5]]},
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
	{"id": "spalt", "art": "spalt", "s": 52.3, "q": 0.9, "ls": 7.7, "lq": 1.7},
	{"id": "seil", "art": "seil", "s": 46.1, "q": 0.9, "von": [46.1, -1.4], "nach": [46.1, 3.3]},
	{"id": "wasserfall", "art": "fall", "s": 44.3, "q": 0.9, "top": 4.0, "breite": 1.4},
	{"id": "wasserfall2", "art": "fall", "s": 59.6, "q": 0.9, "top": 16.0, "breite": 2.2},
	# scene 5: the carabiner
	{"id": "karabiner", "art": "fund", "s": 46.4, "q": 6.2, "top": 0.0, "name": "Karabiner «G+T {jahr_kurz}»"},
	# scene 6: the old suspension bridge over the wide cleft (planks along q; they fall behind you)
	{"id": "spalt2", "art": "spalt", "s": 54.0, "q": 1.0, "ls": 2.0, "lq": 4.0},
	{"id": "bruecke", "art": "bruecke", "s": 54.0, "q": 1.0, "ls": 0.65, "lq": 4.6, "boden_bei": [54.0, 6.5]},
	# scenes 7, 9: the cairn, the photo, the diary scrap
	{"id": "steinmann", "art": "steinmann", "s": 57.6, "q": -5.3},
	{"id": "foto", "art": "fund", "s": 58.6, "q": -5.6, "top": 0.0},
	{"id": "tagebuch", "art": "fund", "s": 55.2, "q": -6.1, "top": 0.0},
	# scenes 11, 12: at the camp on the rim (valley coordinates «tal»)
	{"id": "ir_fels", "art": "findling", "tal": [-26.5, -3.0], "r": 0.9},
	{"id": "ir_zeichen", "art": "fund", "tal": [-26.5, -3.75], "top": 0.75, "nur_ir": true},
	{"id": "lia_zelt", "art": "zelt", "tal": [-10.0, -16.5], "dreh": 40.0},
	{"id": "notizbuch", "art": "buch", "tal": [-10.2, -14.8]},
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
	{"id": "karte", "art": "karte", "s": 57.0, "q": -4.6, "r": 1.9, "ding": "steinmann", "richtung_tal": [-60.0, -390.0]},
	{"id": "foto_nehmen", "art": "fund", "s": 58.6, "q": -5.6, "r": 1.2, "ding": "foto"},
	{"id": "tagebuch_nehmen", "art": "fund", "s": 55.2, "q": -6.1, "r": 1.2, "ding": "tagebuch"},
	{"id": "ir", "art": "ir", "tal": [-22.0, -9.0], "r": 3.0},
	{"id": "ir_zeichen_nehmen", "art": "fund", "tal": [-26.5, -3.9], "r": 1.4, "ding": "ir_zeichen"},
]

# the soft guide: the way through the gorge (s, q) - the figure is pulled back gently when it leaves the corridor
const WEG := [[0.0, 0.0], [10.5, 0.2], [21.0, 0.0], [24.0, 0.0], [31.0, 0.0], [34.6, -3.0], [38.5, 0.8], [39.4, 2.4],
		[43.6, 2.4], [43.1, -3.2]]
const WEG_BREITE := 5.5

const CHECKPOINTS := {"start": [2.0, 0.0], "steine": [21.0, 0.0], "stufe": [31.0, 0.0], "tor": [39.0, 0.8],
		"wand": [43.0, -2.0], "oben": [45.6, -4.6], "fund": [46.2, 5.0], "steinmann": [55.5, -4.5], "lager": {"tal": [-19.5, -7.0]}}

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

const FUNDE_ALLE := ["karabiner", "foto", "tagebuch"]      # «Alle Funde»: the three finds with a story (the IR mark is not one)
const FUNDE := {"ir_zeichen": ["Zeichen im Fels", "Ein eingeritztes Zeichen, nur im Infrarot zu sehen: zwei Linien und ein Kreuz."],
		"karabiner": ["Karabiner «G+T {jahr_kurz}»", "Ein alter Stahlkarabiner. Jemand hat «G+T {jahr_kurz}» hineingeritzt."],
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
		{"abzeichen": "trockene_fuesse", "wenn": "trocken"},
		{"musik": "explore"}]},
	{"id": "s05_karabiner", "titel": "Der Karabiner", "start": [46.2, 5.0], "schritte": [
		{"ziel": "Da glitzert etwas im Fels", "bis": "fund:karabiner"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "shot", "art": "nah", "s": 46.4, "q": 6.2, "h": 4.9, "d": 3.5},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Ein Karabiner. Da ist etwas eingeritzt: «G+T {jahr_kurz}»."},
			{"t": 3.6, "k": "sag", "wer": "blinki", "text": "G wie {bezug}. T wie … unbekannt. Ich lege eine Akte an."}]}]},
	{"id": "s06_bruecke", "titel": "Die Hängebrücke", "start": [47.5, 5.0], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "shot", "art": "reveal", "s": 50.5, "q": 5.5, "h": 1.0, "blick": [54.0, 1.0, 0.5], "d": 3.5},
			{"t": 0.3, "k": "sag", "wer": "figur", "text": "Eine Hängebrücke. Alt. Sehr alt."},
			{"t": 2.6, "k": "sag", "wer": "blinki", "text": "Tragfähigkeit: unbekannt. Empfehlung: zügig gehen. Nicht hüpfen."}]},
		{"musik": "spannung"},
		{"ziel": "Geh über die Hängebrücke – zügig!", "bis": "ort:54.0,-0.3,1.0", "merke_halt": "bruecke"},
		{"film": [
			{"t": 0.0, "k": "musik", "z": "action"},
			{"t": 0.0, "k": "zeitlupe", "f": 0.35, "s": 2.4},
			{"t": 0.0, "k": "shot", "art": "fix", "s": 51.5, "q": -4.5, "h": 3.0, "blick": [54.0, 2.0, 0.0], "d": 2.6},
			{"t": 0.1, "k": "bruecke_einsturz", "ding": "bruecke", "ab_q": 0.6},
			{"t": 0.2, "k": "ton", "name": "einsturz"},
			{"t": 0.3, "k": "zug", "wer": "figur", "s": 54.0, "q": -4.2},
			{"t": 0.5, "k": "maggie_sprung", "s": 54.0, "q": 3.0},
			{"t": 0.6, "k": "qte", "id": "maggie_gefangen", "text": "Greifen!", "s": 1.6},
			{"t": 0.7, "k": "sag", "wer": "figur", "text": "Maggie – spring!"},
			{"t": 2.8, "k": "sag", "wer": "maggie", "text": "Wuff!"}]},
		{"abzeichen": "bruecken_sprinter", "wenn": "nicht:bruecke_halt"},
		{"abzeichen": "maggies_held", "wenn": "merker:maggie_gefangen"},
		{"sag": "Okay. Zurück geht es jedenfalls nicht mehr.", "wer": "figur"},
		{"musik": "explore"},
		{"checkpoint": "steinmann"}]},
	{"id": "s07_steinmann", "titel": "Der Steinmann", "start": [55.5, -4.5], "schritte": [
		{"ziel": "Untersuche den Steinmann", "bis": "ort:57.0,-4.6,1.8"},
		{"sag": "Ein Steinmann – genau wie auf dem Kartenstück! Ich halte die Karte über die Landschaft …", "wer": "figur"},
		{"ziel": "Halte das Kartenstück über die Landschaft (Aktion am Steinmann, dann umschauen)", "bis": "aktion:karte"},
		{"film": [
			{"t": 0.0, "k": "musik", "z": "entdeckung"},
			{"t": 0.0, "k": "sag", "wer": "figur", "text": "Die Linie auf der Karte … sie zeigt zum Seeblock!"},
			{"t": 2.8, "k": "sag", "wer": "blinki", "text": "Richtung gespeichert. Ich hätte es auch gefunden. Wahrscheinlich."}]},
		{"checkpoint": "steinmann"}]},
	{"id": "s08_rueckblende", "titel": "{jahr}", "start": [56.0, -4.5], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "blende", "s": 1.6},
			{"t": 0.8, "k": "farbe", "art": "alt"},
			{"t": 0.8, "k": "person", "id": "gv", "s": 56.3, "q": -6.0, "blick": [60.0, -4.0], "jacke": [0.55, 0.32, 0.18]},
			{"t": 0.8, "k": "person", "id": "toni", "s": 57.4, "q": -3.6, "blick": [60.0, -4.0], "jacke": [0.25, 0.4, 0.62]},
			{"t": 0.8, "k": "shot", "art": "fix", "s": 53.5, "q": -3.0, "h": 1.7, "blick": [57.0, -4.8, 1.5], "d": 9.0},
			{"t": 1.2, "k": "sag", "wer": "erzaehler", "text": "{jahr}. Genau hier."},
			{"t": 3.4, "k": "zug", "wer": "toni", "s": 61.0, "q": -3.0},
			{"t": 3.6, "k": "sag", "wer": "toni", "text": "Wer zuerst oben ist, zahlt den Kaffee!"},
			{"t": 6.4, "k": "sag", "wer": "grossvater", "text": "Dann such schon mal dein Portemonnaie, Toni."},
			{"t": 9.2, "k": "blende", "s": 1.6},
			{"t": 10.0, "k": "farbe", "art": ""},
			{"t": 10.0, "k": "person_weg", "id": "gv"},
			{"t": 10.0, "k": "person_weg", "id": "toni"},
			{"t": 10.4, "k": "sag", "wer": "figur", "text": "Toni … T wie Toni."}]}]},
	{"id": "s09_funde", "titel": "Foto und Tagebuch", "start": [56.0, -4.5], "schritte": [
		{"sag": "Maggie schnüffelt am Fels. Sie hat etwas!", "wer": "erzaehler"},
		{"maggie": "riechen", "s": 58.6, "q": -5.6},
		{"ziel": "Folge Maggies Spur", "bis": "fund:foto"},
		{"sag": "Ein Foto … {bezug} und Toni. Beide lachen.", "wer": "figur"},
		{"ziel": "Da liegt noch etwas zwischen den Steinen", "bis": "fund:tagebuch"},
		{"sag": "«Ich habe es ihm versprochen.» – Was hat er versprochen?", "wer": "figur"}]},
	{"id": "s10_lia", "titel": "Lia", "start": [57.0, -4.0], "schritte": [
		{"ziel": "Geh zum zweiten Wasserfall", "bis": "ort:58.0,-3.0,2.0"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "maggie_warnen", "s": 64.6, "q": -3.0},
			{"t": 0.0, "k": "person", "id": "lia", "s": 64.6, "q": -3.0, "blick": [56.0, -3.0], "jacke": [0.86, 0.35, 0.3]},
			{"t": 0.3, "k": "shot", "art": "fix", "s": 56.5, "q": -1.5, "h": 1.3, "blick": [64.6, -3.0, 1.6], "d": 6.0},
			{"t": 0.6, "k": "sag", "wer": "lia", "text": "Na? Auch auf der Suche nach dem Schatz von deinem {bezug}?"},
			{"t": 3.4, "k": "sag", "wer": "figur", "text": "Wer bist du?"},
			{"t": 4.8, "k": "sag", "wer": "lia", "text": "Lia. Lia Arnold. Toni war mein {bezug}. Und du: zu langsam. ;-)"},
			{"t": 7.8, "k": "zug", "wer": "lia", "s": 70.0, "q": -6.0},
			{"t": 8.4, "k": "sag", "wer": "blinki", "text": "Arnold. Wie T. Ich aktualisiere die Akte."}]},
		{"musik": "explore"}]},
	{"id": "s11_nachtlager", "titel": "Nachtlager", "start": [], "schritte": [
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "blende", "s": 2.0},
			{"t": 0.9, "k": "zeit", "h": 21.6},
			{"t": 0.9, "k": "figur_tal", "x": -19.5, "z": -7.0},
			{"t": 0.9, "k": "shot", "art": "fix", "tal": [-27.0, -14.0], "h": 2.2, "blick_tal": [-21.0, -8.0, 0.8], "d": 5.0},
			{"t": 1.2, "k": "sag", "wer": "erzaehler", "text": "Am Abend. Oben am Rand der Schlucht."},
			{"t": 3.6, "k": "sag", "wer": "blinki", "text": "MoveEye wacht. Ich wache auch. Aber MoveEye hat die bessere Kamera."},
			{"t": 4.0, "k": "musik", "z": "spannung"}]},
		{"checkpoint": "lager"},
		{"ziel": "Schalte bei MoveEye das IR-Licht ein (Aktion am Lager)", "bis": "aktion:ir"},
		{"film": [
			{"t": 0.0, "k": "tier", "art": "fox", "tal": [-12.0, -2.0], "nach_tal": [-30.0, 4.0]},
			{"t": 0.2, "k": "maggie_warnen_tal", "x": -12.0, "z": -2.0},
			{"t": 0.4, "k": "sag", "wer": "blinki", "text": "Bewegung! Ein Fuchs. Harmlos. Maggie sieht das anders."},
			{"t": 3.0, "k": "sag", "wer": "figur", "text": "Da – am Felsen leuchtet etwas im IR-Licht!"}]},
		{"ziel": "Untersuche das Zeichen am Felsen", "bis": "fund:ir_zeichen"},
		{"sag": "Ein eingeritztes Zeichen … nur im Infrarot zu sehen. Wie hat er das gemacht?", "wer": "figur"},
		{"ziel": "Mach ein Foto mit MoveEye (Foto-Knopf oder P)", "bis": "aktion:foto"},
		{"musik": "explore"}]},
	{"id": "s12_cliffhanger", "titel": "Das leere Zelt", "start": [], "schritte": [
		{"ziel": "Was ist mit Lias Zelt?", "bis": "ort_tal:-11.0,-15.0,2.6"},
		{"film": [
			{"t": 0.0, "k": "balken", "an": true},
			{"t": 0.0, "k": "musik", "z": "spannung"},
			{"t": 0.0, "k": "shot", "art": "fix", "tal": [-14.5, -18.5], "h": 1.4, "blick_tal": [-10.0, -16.0, 0.3], "d": 6.0},
			{"t": 0.4, "k": "sag", "wer": "figur", "text": "Lia? … Das Zelt ist leer."},
			{"t": 3.2, "k": "shot", "art": "nah_tal", "tal": [-10.2, -14.8], "h": 0.15, "d": 5.0},
			{"t": 3.4, "k": "sag", "wer": "erzaehler", "text": "Tonis Notizbuch. Aufgeschlagen."},
			{"t": 5.6, "k": "sag", "wer": "toni", "text": "«Er hat mich zurückgelassen.»", "d": 4.0},
			{"t": 9.8, "k": "ende", "text": "Ende von Kapitel 2 – Fortsetzung folgt."}]}]},
]
