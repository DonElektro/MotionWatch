extends RefCounted
## Bergtal-Abenteuer «Die Karte des Grossvaters» - die Daten (Daniel, 31.10.2026, Abschnitt «Story / Abenteuer» im Plan):
## Stimmungen, Schwierigkeit, Ziele, Rucksack und Ausrüstung, die 5 Kapitel der Schatzkarte (Wege mit Gabelungen,
## Hinweise auf der Karte / im Gelände / bei Menschen), Begegnungen, Fundstücke, Stufen (Erfahrung).
## Die Abläufe stehen in bergtal_abenteuer.gd, die Karte in bergtal_abenteuer_karte.gd.
## Tal-Koordinaten wie bergtal.gd: x = Osten, z = Süden (zum Pass); Höhen kommen aus der Höhenkarte (bergtal.gd H()).

# ---- Stimmung (beeinflusst Texte, Ereignisse, Wetterhäufigkeit) -----------------------------------------------------------
# id -> [Name, Beschreibung, Wetter-Faktor, Begegnungs-Faktor, Nebel-Anteil am Wetter, lustige Dinge]
const MOODS := {"geheimnisvoll": ["Geheimnisvoll", "Nebel zieht durchs Tal, alte Zeichen im Fels, leise Begegnungen.", 1.0, 0.8, 0.75, false],
		"abenteuerlich": ["Abenteuerlich", "Steile Abkürzungen, Wetterumschwung, ein Tag, an dem man über sich hinauswächst.", 1.4, 1.0, 0.4, false],
		"gemuetlich": ["Gemütlich", "Ruhiges Wetter, Bänke mit Aussicht, Käse beim Senner, Zeit zum Schauen.", 0.5, 1.2, 0.5, false],
		"lustig": ["Lustig", "Neugierige Kühe, freche Dohlen, schräge Funde - das Tal nimmt sich nicht so ernst.", 0.8, 1.4, 0.5, true]}
const MOOD_ORDER := ["geheimnisvoll", "abenteuerlich", "gemuetlich", "lustig"]
# die 5. Stimmung ist ein eigenes Paket (Horror «Das Hospiz», passwortgeschützt) - hier nur der gesperrte Platz
const HORROR_SLOT := ["horror", "Horror", "Eigenes Paket «Das Hospiz» - kommt später, mit Passwort."]

# Stimmungs-Sätze zu den Momenten der Tour
const FLAVOR := {"geheimnisvoll": {"start": "Über dem Tal liegt ein dünner Schleier. Irgendwo pfeift ein Murmeltier - dann ist es still.",
			"camp": "Die Felsen werfen lange Schatten. Fast wirkt es, als würde jemand zuschauen.",
			"night": "Die Nacht ist sehr still. Jedes Geräusch fällt auf.",
			"morning": "Der Nebel hebt sich langsam vom See."},
		"abenteuerlich": {"start": "Der Rucksack sitzt, die Schuhe sind geschnürt. Heute geht es hoch hinaus.",
			"camp": "Geschafft - die Beine brennen, aber der Platz ist es wert.",
			"night": "Der Wind drückt gegen das Lager. MoveEye passt auf.",
			"morning": "Die ersten Sonnenstrahlen treffen die Gipfel. Weiter geht's!"},
		"gemuetlich": {"start": "Kein Stress heute. Das Tal läuft nicht davon.",
			"camp": "Der Kocher summt, der Tee dampft. Was will man mehr?",
			"night": "Die Sterne über dem Tal - man könnte stundenlang schauen.",
			"morning": "Kaffee mit Aussicht. So darf jeder Tag anfangen."},
		"lustig": {"start": "Eine Kuh schaut dich an, als wüsste sie mehr über die Karte als du.",
			"camp": "Eine Dohle beobachtet dein Sandwich sehr genau.",
			"night": "Irgendwo bimmelt eine Kuhglocke. Schläft hier eigentlich irgendwer?",
			"morning": "Neben dem Lager liegt eine Socke, die dir nicht gehört."}}

# ---- Schwierigkeit: [Name, Text, Kraft höchstens, Wetter-Faktor, Tier-Faktor, Orientierung (bergtal bt_orient)] ---------
const LEVELS := {"leicht": ["Leicht", "Mehr Kraft, ruhiges Wetter, Standort auf der Karte. Rätsel: Pfeile zeigen den Weg.", 100.0, 0.6, 0.7, "leicht"],
		"mittel": ["Mittel", "Normales Bergwetter, Tiere in der Nacht, nur Kompass. Rätsel: Tipp nach einer Weile.", 85.0, 1.0, 1.0, "mittel"],
		"schwer": ["Schwer", "Weniger Kraft, öfter schlechtes Wetter, mehr Tiere, nur Wegweiser und die Sonne. Rätsel: keine Hilfe.", 70.0, 1.5, 1.4, "schwer"]}
const LEVEL_ORDER := ["leicht", "mittel", "schwer"]

# ---- Ziel ---------------------------------------------------------------------------------------------------------------
const GOALS := {"dunkel": ["Schlafplatz vor Dunkelheit", "Das Lager steht, bevor die Sonne untergeht. Start am Nachmittag."],
		"gipfel": ["Gipfel zum Sonnenaufgang", "Am Ziel übernachten, früh aufstehen und vor der Sonne oben sein."],
		"zufall": ["Freie Wahl (ausgelost)", "Das Tal entscheidet: eines der beiden Ziele wird ausgelost."]}
const GOAL_ORDER := ["dunkel", "gipfel", "zufall"]

# ---- Rucksack (Gewichtsgrenze je Grösse - vereinfacht, Daniel: echte Grammangaben nicht nötig) ------------------------------
# id -> [Name, Volumen L, Leergewicht kg, Gewicht höchstens kg (bequem tragbar)]
const PACKS := {"30": ["Rucksack 30 L", 30.0, 0.9, 8.0], "50": ["Rucksack 50 L", 50.0, 1.5, 13.0], "70": ["Rucksack 70 L", 70.0, 2.1, 18.0]}
# id -> [Name, kg, Liter, Gruppe, Text, höchstens Anzahl, ab Stufe]
# Gewichte gerundet nach typischen Katalogwerten (Kuppelzelt 2-P. 2,3–3 kg, Einmannzelt 1,2–1,6 kg, Tarp 0,4–0,7 kg,
# Biwaksack 0,3–0,6 kg, Isomatte 0,4–0,7 kg, Sommerschlafsack 0,7–1 kg, Winterschlafsack 1,5–2 kg, Gaskocher mit Kartusche
# 0,4–0,6 kg, Stirnlampe 0,1 kg); Wasser 1 kg pro Liter.
const ITEMS := {"isomatte": ["Isomatte", 0.5, 6.0, "schlafen", "Gegen den kalten Boden.", 1, 1],
		"kuppelzelt": ["Kuppelzelt", 2.6, 9.0, "dach", "Viel Platz, Schutz vor Wind und Regen. Schwer.", 1, 1],
		"einmannzelt": ["Einmannzelt", 1.4, 5.0, "dach", "Leicht und dicht - braucht einen flachen Platz.", 1, 1],
		"tarp": ["Tarp", 0.6, 2.0, "dach", "Plane gegen Regen, offen für die Sterne. Wind kommt durch.", 1, 1],
		"biwaksack": ["Biwaksack", 0.4, 2.0, "dach", "Hülle über den Schlafsack - geht auch auf schrägem Boden.", 1, 1],
		"sommerschlafsack": ["Sommerschlafsack", 0.8, 6.0, "schlafen", "Warm genug bis etwa 5 °C.", 1, 1],
		"winterschlafsack": ["Winterschlafsack", 1.6, 12.0, "schlafen", "Warm bis unter den Gefrierpunkt. Gross und schwer.", 1, 1],
		"kocher": ["Kocher mit Gas", 0.5, 2.0, "kochen", "Warmes Essen erholt mehr; im Winter Schnee schmelzen.", 1, 1],
		"stirnlampe": ["Stirnlampe", 0.1, 0.3, "licht", "Ohne Lampe ist es nach Sonnenuntergang wirklich dunkel.", 1, 1],
		"jacke": ["Warme Jacke", 0.5, 3.0, "kleider", "Gegen Wind, Regen und die Kälte am Abend.", 1, 1],
		"essen": ["Proviant (1 Portion)", 0.6, 2.0, "essen", "Eine Mahlzeit - gibt Kraft in den Pausen.", 4, 1],
		"wasser": ["Wasser (1 Liter)", 1.0, 1.0, "essen", "Am Bach kann man nachfüllen.", 3, 1],
		"apotheke": ["Erste Hilfe", 0.2, 0.5, "sicher", "Pflaster und Binde - ein verstauchter Fuss tut weniger weh.", 1, 1],
		"stoecke": ["Wanderstöcke", 0.5, 0.0, "sicher", "Bergauf und bergab etwas weniger anstrengend.", 1, 1],
		"ministativ": ["Mini-Stativ für MoveEye", 0.3, 0.5, "moveeye", "MoveEye frei aufstellen (Höhe und Richtung frei).", 1, 1],
		"powerbank": ["Powerbank für MoveEye", 0.3, 0.3, "moveeye", "Strom für MoveEye bis zum Morgen, auch bei Kälte.", 1, 1],
		"ultratarp": ["Ultraleicht-Tarp", 0.3, 1.0, "dach", "Wie das Tarp, nur halb so schwer.", 1, 3],
		"daunenschlafsack": ["Daunen-Winterschlafsack", 1.0, 8.0, "schlafen", "Warm wie der Winterschlafsack, viel leichter.", 1, 4],
		"karabiner": ["Der alte Karabiner", 0.05, 0.0, "andenken", "Aus der Blechdose am versteckten See.", 1, 99]}
const ITEM_ORDER := ["isomatte", "einmannzelt", "kuppelzelt", "tarp", "ultratarp", "biwaksack", "sommerschlafsack", "winterschlafsack",
		"daunenschlafsack", "kocher", "stirnlampe", "jacke", "essen", "wasser", "apotheke", "stoecke", "ministativ", "powerbank", "karabiner"]
# MoveEye ist Teil der Ausrüstung, zählt aber nicht als Gewicht (Daniel)

# ---- Stufen (Erfahrung) -------------------------------------------------------------------------------------------------
const LEVEL_XP := [0, 300, 700, 1200, 2000, 3000]
const UNLOCKS := {3: "ultratarp", 4: "daunenschlafsack"}     # (Daniel 31.10.: kein «Fernglas» mehr - nur Grossvaters Feldstecher, A3)

# ---- Fundstücke unterwegs (machen den Rucksack schwerer) ------------------------------------------------------------------
# id -> [Name, kg, Text, nur lustig]
const FINDS := {"kristall": ["Bergkristall", 0.3, "Ein klarer Kristall, halb im Geröll.", false],
		"stein": ["Schöner Stein mit Glimmer", 0.8, "Er glitzert in der Sonne. Schwer, aber schön.", false],
		"horn": ["Altes Kuhhorn", 0.4, "Vielleicht von einer Glocke? Jemand hat Kerben hineingeschnitzt.", false],
		"laterne": ["Alte Stalllaterne", 1.1, "Rostig, aber das Glas ist noch ganz.", false],
		"kaeselaib": ["Ein ganzer Käselaib", 2.5, "Der Senner hat ihn vergessen. Riecht kräftig.", true],
		"holzski": ["Ein alter Holzski", 3.0, "Nur einer. Wo ist wohl der andere?", true],
		"socke": ["Eine Socke (nicht deine)", 0.05, "Eine Kuh hatte sie im Maul.", true]}

# ---- Begegnungen unterwegs -------------------------------------------------------------------------------------------------
# id -> [Wer, Text, Art: tip | food | clue | wait | fun, Stimmungen (leer = alle)]
const MEET := {"wanderer": ["Ein Wanderer", "«Weiter oben gibt es einen Brunnen - dort kannst du Wasser auffüllen.»", "tip_water", []],
		"wanderer2": ["Eine Wanderin mit Hund", "«Bei der nächsten Gabelung: der flache Weg ist schöner, aber er zieht sich.»", "tip_fork", []],
		"senner": ["Der Senner bei den Kühen", "Er schneidet ein Stück Alpkäse ab: «Nimm, du hast noch einen weiten Weg.»", "food", []],
		"fotograf": ["Ein Fotograf mit Stativ", "«Morgen früh kommt das Alpenglühen. Oben auf dem Grat ist es am schönsten.»", "tip_sun", []],
		"strahler": ["Ein Strahler am Fels", "Er klopft vorsichtig am Fels. «Kristalle findet man, wo Quarzbänder sind.»", "tip_find", []],
		"bergsteiger": ["Zwei Bergsteiger mit Seil", "«Oben am Grat zieht es zu. Pass auf das Wetter auf.»", "tip_weather", ["abenteuerlich", "geheimnisvoll"]],
		"trailrunner": ["Ein Trailrunner", "Er rennt vorbei, kommt zurück und fragt dich nach dem Weg.", "fun", ["lustig", "gemuetlich"]],
		"kuehe": ["Kühe auf dem Weg", "Die ganze Herde steht auf dem Weg und denkt gar nicht daran weiterzugehen. Da hilft nur warten.", "wait", ["lustig", "gemuetlich"]],
		"dohlen": ["Alpendohlen", "Drei Dohlen landen neben dir und schauen in deinen Rucksack.", "fun", ["lustig"]],
		"grenzwache": ["Eine Grenzwächter-Patrouille", "«Schöner Abend. Übernachte nicht zu nah an der Passstrasse.»", "tip_spot", ["geheimnisvoll", "abenteuerlich"]]}

# ---- die 5 Kapitel der Schatzkarte ---------------------------------------------------------------------------------------
# Jedes Abenteuer ist ein Kapitel. Wege: Liste von Abschnitten; ein Abschnitt ist {"walk": [Punkte], …} oder eine Gabelung
# {"fork": [kurz-steil, lang-flach]} - jede Seite [Name, Punkte, Merkmale]. Merkmale: bach (Wasser auffüllen), bank
# (Rastplatz), exposed (ausgesetzt: Gewitter gefährlich), steep (steiler Hang: Steinschlag, Gämsen).
# «read» = Karte lesen: die drei Hinweise (Karte, Gelände, Mensch) zeigen auf den richtigen Ort; falsch = Umweg.
const CHAPTERS := [
	{"id": 1, "title": "Kapitel 1 - Der Brief",
		"intro": "Ein Brief vom Grossvater, mit Wachs verschlossen. Darin nur ein Satz: «Die Karte gehört jetzt dir - lies sie mit der Sonne.» Dazu ein Stück einer alten, vergilbten Karte des Bergtals - das erste von fünf. Es zeigt eine Glocke über einem Brunnen.",
		"start": ["Postauto-Haltestelle bei der Kapelle St. Jodern", 205.0, -690.0], "season_hint": "",
		"symbol": "glocke", "piece": 0,
		"stages": [{"walk": [Vector2(205, -690), Vector2(200, -600), Vector2(190, -500)], "name": "Der Strasse entlang ins Tal"},
			{"fork": [["Kurz und steil: über die Chanzle", [Vector2(190, -500), Vector2(262, -430), Vector2(200, -300), Vector2(178, -200)], ["bank", "steep"]],
				["Lang und flach: der Strasse nach", [Vector2(190, -500), Vector2(190, -400), Vector2(182, -300), Vector2(178, -200)], []]]},
			{"clue": "terrain", "text": "An einem Wegweiser ist eine Kerbe in den Pfosten geschnitten - sie zeigt nicht zum See, sondern hinauf zu den Kuhweiden."},
			{"walk": [Vector2(178, -200), Vector2(178, -40), Vector2(110, -20)], "name": "Hinauf zu den Weiden", "bach": true},
			{"clue": "person"},
			{"read": {"q": "Auf dem Kartenstück: eine Glocke über einem Brunnen. Wo ist das?",
				"options": [["Alp Tschuggen (Brunnen beim Stall)", true], ["Kapelle St. Jodern (Glockenturm)", false], ["Tüfelsschlund (Wasserfall)", false]],
				"hint": "Glocke = Kuhglocke, nicht Kirchenglocke. Der Senner hat es gesagt.",
				"detour": [Vector2(110, -20), Vector2(60, -110), Vector2(110, -20)]}},
			{"walk": [Vector2(110, -20), Vector2(60, 0), Vector2(38, 18)], "name": "Zur Alp Tschuggen"}],
		"person": ["Der Senner bei den Kühen", "Er lacht, als er die Karte sieht: «Eine Glocke? Hier bei uns hat jede Kuh eine. Und hier oben bei den Weiden gibt es nur einen Brunnen - den bei meinem Stall.»"],
		"found": "Unter dem Brunnentrog der Alp ist ein Zeichen eingemeisselt: zwei Wellen, eine über der anderen. Das zweite Kartenstück passt genau daneben - es zeigt einen Bach, der zweimal fällt.",
		"camp": ["huette", 30.0, 22.0], "summit": "vp_kanzel", "summit_name": "Chanzle über dem Gumpisee", "start_h": 15.5},
	{"id": 2, "title": "Kapitel 2 - Wo der Bach zweimal fällt",
		"intro": "Das zweite Kartenstück zeigt den Bach, der zweimal fällt: zwei Wellen übereinander, darunter ein Strich wie ein Steg. Daneben, ganz klein: ein Steinmann mit einer Kerbe.",
		"start": ["Alp Tschuggen", 38.0, 18.0], "symbol": "wellen", "piece": 1,
		"stages": [{"walk": [Vector2(38, 18), Vector2(60, 0), Vector2(70, -70)], "name": "Dem Bach entlang abwärts", "bach": true},
			{"clue": "person"},
			{"fork": [["Kurz und ausgesetzt: über die Hängebrücke", [Vector2(70, -70), Vector2(50, -130), Vector2(34, -170), Vector2(-5, -175), Vector2(-40, -230)], ["exposed"]],
				["Lang und flach: um die Schlucht herum", [Vector2(70, -70), Vector2(20, -60), Vector2(-60, -100), Vector2(-150, -230)], ["bank"]]]},
			{"clue": "terrain", "text": "Ein Steinmann am Weg hat oben einen flachen Stein mit einer Kerbe - sie zeigt hinunter zum Seeufer, wo ein grosser Block im Wasser steht."},
			{"read": {"q": "Der Bach fällt zweimal - und der Steinmann zeigt zum Wasser. Wohin?",
				"options": [["Ans Ufer des Gumpisees", true], ["Hinauf zum Gletscherseeli", false], ["Ins Riedmoos", false]],
				"hint": "Der Wasserfall ist der erste Fall, die Schlucht der zweite. Danach kommt der See.",
				"detour": [Vector2(-150, -230), Vector2(-260, -250), Vector2(-150, -230)]}},
			{"walk": [Vector2(-150, -230), Vector2(-200, -330), Vector2(-142, -332)], "name": "Hinunter zum Gumpisee", "bach": true}],
		"person": ["Ein alter Wanderer", "Er stützt sich auf den Stock: «Zweimal fällt der Bach - einmal beim Wasserfall, einmal in der Schlucht. Wer Steinmänner liest, findet den Weg auch im Nebel.»"],
		"found": "Am Ufer liegt der grosse Block, auf den der Steinmann gezeigt hat. In seiner Seite steckt ein Eisenring, und darunter: das dritte Kartenstück, in Wachstuch gewickelt. Es zeigt eine Sonne über einem Stein.",
		"camp": ["seeufer", -142.0, -332.0], "summit": "vp_seeblick", "summit_name": "Seeblick Gumpisee", "start_h": 15.0},
	{"id": 3, "title": "Kapitel 3 - Wo die Sonne am Morgen den Stein trifft",
		"intro": "Das dritte Stück zeigt eine Sonne, die über zwei Zacken aufgeht, und einen Stein mit einem langen Schatten. Darunter steht: «Wo die Sonne am Morgen den Stein trifft.»",
		"start": ["Am Ufer des Gumpisees", -142.0, -332.0], "symbol": "sonne", "piece": 2,
		"stages": [{"walk": [Vector2(-142, -332), Vector2(-200, -330), Vector2(-320, -300)], "name": "Am See vorbei nach Westen"},
			{"clue": "sun"},
			{"fork": [["Kurz: quer durchs Riedmoos (nasse Füsse)", [Vector2(-320, -300), Vector2(-470, -265), Vector2(-600, -255)], ["bach", "wet"]],
				["Lang: am Moorrand entlang", [Vector2(-320, -300), Vector2(-420, -220), Vector2(-540, -200), Vector2(-600, -255)], ["bank"]]]},
			{"clue": "person"},
			{"read": {"q": "Die Sonne geht im Osten auf, die Schatten fallen dann nach Westen. Wo steht der Stein, den die Sonne am Morgen zuerst trifft?",
				"options": [["Bei der Ruine Altstafel (oben im Westen, frei gegen Osten)", true], ["Im Schattwald (unten im Norden)", false], ["Am Schwarzseeli (in der Mulde)", false]],
				"hint": "Den ersten Sonnenstrahl bekommt, was hoch steht und gegen Osten frei ist - nicht, was in einer Mulde liegt.",
				"detour": [Vector2(-600, -255), Vector2(-640, -330), Vector2(-600, -255)]}},
			{"walk": [Vector2(-600, -255), Vector2(-700, -250), Vector2(-810, -230)], "name": "Hinauf zur Ruine Altstafel"}],
		"person": ["Ein Strahler am Fels", "Er zeigt mit dem Hammer nach Westen: «Bei der Ruine oben steht ein Stein mit einer Inschrift. Am Morgen ist er der erste, der Sonne bekommt.»"],
		"found": "In der Mauer der Ruine ist ein Stein mit einer Inschrift: ein Pfeil nach Süden und daneben ein Steinmann mit zwei Punkten - wie Augen. Hinter dem Stein steckt das vierte Kartenstück.",
		"camp": ["ruine", -810.0, -230.0], "summit": "vp_moorsee", "summit_name": "Ob em Schwarzseeli", "start_h": 14.5},
	{"id": 4, "title": "Kapitel 4 - Der Steinmann mit den Augen",
		"intro": "Das vierte Stück zeigt viele kleine Steinmänner, einer davon mit zwei Punkten. Ein Pfeil führt von dort hinauf zu einem Kästchen unter Felsblöcken.",
		"start": ["Bei der Ruine Altstafel", -810.0, -230.0], "symbol": "steinmann", "piece": 3,
		"stages": [{"walk": [Vector2(-810, -230), Vector2(-760, -180), Vector2(-700, -130)], "name": "Zur alten Sennerei"},
			{"clue": "person"},
			{"fork": [["Kurz und steil: über die Rüfi (Geröll)", [Vector2(-700, -130), Vector2(-640, 0), Vector2(-625, 125), Vector2(-640, 300), Vector2(-650, 430)], ["steep", "exposed"]],
				["Lang: über den alten Säumerweg", [Vector2(-700, -130), Vector2(-780, 0), Vector2(-770, 150), Vector2(-720, 300), Vector2(-650, 430)], ["bank", "bach"]]]},
			{"clue": "terrain", "text": "Im Steimandli-Wald stehen Hunderte Steinmänner. Einer hat zwei dunkle Steine wie Augen - und er schaut genau zur Biwakschachtel."},
			{"read": {"q": "Der Steinmann mit den Augen schaut zu einem Kästchen unter Felsblöcken. Was ist gemeint?",
				"options": [["Die Biwakschachtel am Chüebodehorn", true], ["Der Bunker Fort Chrüzli", false], ["Die Obri Stafelhütte", false]],
				"hint": "Ein Kästchen unter Felsblöcken, hoch oben - das ist eine Biwakschachtel.",
				"detour": [Vector2(-650, 430), Vector2(-700, 520), Vector2(-650, 430)]}},
			{"walk": [Vector2(-650, 430), Vector2(-590, 500), Vector2(-512, 548)], "name": "Hinauf zum Biwak"}],
		"person": ["Zwei Bergsteiger mit Seil", "«Der Steinmann mit den Augen? Den kennen alle hier. Er schaut immer zum Biwak - als würde er es bewachen.»"],
		"found": "Im Biwak liegt ein Hüttenbuch. Zwischen den letzten Seiten: das fünfte Kartenstück. Es zeigt einen kleinen See hinter dem Grat und eine Sonne, die genau in einer Lücke im Fels steht.",
		"camp": ["biwak", -512.0, 548.0], "summit": "vp_horn", "summit_name": "Tschingelspitz", "start_h": 13.5},
	{"id": 5, "title": "Kapitel 5 - Hinter dem Grat",
		"intro": "Das letzte Stück: ein kleiner See hinter dem Grat, ein schmaler Pfad, und eine Sonne, die genau in einer Lücke im Fels steht. Daneben ein Kreuz - aber kein Gipfelkreuz. Ein Zeichen: hier.",
		"start": ["Bei der Biwakschachtel", -512.0, 548.0], "symbol": "see", "piece": 4,
		"stages": [{"walk": [Vector2(-512, 548), Vector2(-600, 500), Vector2(-700, 470)], "name": "Über das Plateau nach Westen"},
			{"clue": "sun"},
			{"fork": [["Kurz: über den Gipfel (Tschingelspitz)", [Vector2(-700, 470), Vector2(-827, 505), Vector2(-870, 450)], ["exposed", "bank"]],
				["Lang: um den Gipfel herum (schmaler Pfad)", [Vector2(-700, 470), Vector2(-760, 400), Vector2(-830, 380), Vector2(-870, 450)], ["steep"]]]},
			{"clue": "terrain", "text": "Am Grat ist eine Lücke im Fels, wie ein Fenster. Am Boden davor: eine Inschrift, fast verwittert - nur ein Pfeil und ein Kreuz."},
			{"read": {"q": "Die Sonne steht in der Lücke im Fels - wo fällt das Licht am Morgen hin?",
				"options": [["Auf den kleinen See hinter dem Grat", true], ["Auf das Gipfelkreuz", false], ["Ins Tal hinunter zur Alp", false]],
				"hint": "Die Lücke schaut nach Osten - das erste Licht fällt durch sie auf die andere Seite, zum versteckten See.",
				"detour": [Vector2(-870, 450), Vector2(-827, 505), Vector2(-870, 450)]}},
			{"walk": [Vector2(-870, 450), Vector2(-878, 428)], "name": "Der schmale Pfad zum versteckten See"}],
		"person": ["Ein alter Wanderer", "Er bleibt stehen und schaut lange zum Grat: «Hinter dem Grat gibt es einen See, den kaum jemand kennt. Am schönsten ist er, wenn die Sonne kommt.»"],
		"found": "Am versteckten See liegt ein flacher Stein mit einem eingemeisselten Kreuz. Was darunter ist, zeigt die Sonne - morgen früh.",
		"camp": ["frei", -860.0, 432.0], "summit": "vp_horn", "summit_name": "Tschingelspitz", "start_h": 14.0}]

# ---- die Überraschung am Schluss (Kapitel 5, Sonnenaufgang) ----------------------------------------------------------------
const FINALE := ["Die Sonne kommt. Ihr erster Strahl fällt genau durch die Lücke im Grat - und trifft den flachen Stein am See.",
		"Unter dem Stein ist eine Blechdose. Darin: ein alter Karabiner, blank gerieben, und eine Karte des Bergtals. Alle Wege sind eingezeichnet. Aber kein einziger Name. Alle Felder sind leer.",
		"In den Karabiner ist ein Satz eingeritzt: «Für die nächste Seilschaft.»",
		"Die Namen darfst jetzt du geben. Deine eigenen Markierungen erscheinen ab heute auf dieser Karte - und dieser See ist ab jetzt ein Schlafplatz: «Dein Seeli»."]
