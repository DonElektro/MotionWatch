extends RefCounted
## A2 «Figuren, Gespräche, Nebenaufgaben» - die Daten (Bergtal-Abenteuer, Daniel 31.10.2026).
## Die Abläufe stehen in abenteuer_figuren.gd. Tal-Koordinaten wie bergtal.gd (x = Osten, z = Süden).
## Die Figuren werden mit actor.gd / menschen.gd gebaut (Aussehen über menschen._next_look) - keine neuen Figuren.
## Grossvater: die Figuren kennen ihn, erzählen aber nichts Neues über ihn (Daniel) - nur was die Geschichte schon sagt
## (Bergführer, die Karte, der Brief «lies sie mit der Sonne»).
##
## Gespräche: GRUSS[fid] = [[Bedingung, Text], …] - der erste passende Gruss gilt. THEMEN[fid] = Themen, die man wählen
## kann (höchstens 3 Antworten auf einmal, eine davon «Tschüss»). Ein Thema kann eine Rückfrage haben («frage2»); die
## Antwort merkt sich die Figur (Flag) und erwähnt sie beim nächsten Mal.
## Bedingungen (mit «&» verbunden): erst (noch nie gesprochen) · wieder · hut (trägt den Hut des Grossvaters) ·
## neuhut (Hut, aber die Figur hat ihn noch nie gesehen) · f:x / !f:x (Flag der Figur) · v1 / v2 / v3 (Vertrauen) ·
## q:id (Nebenaufgabe id fertig)

# ---- die Figuren ---------------------------------------------------------------------------------------------------------
# rolle: aelpler | sennerin | huettenwartin | wildhueter | wanderer | bergsteiger
# orte: wo man sie antrifft (Umkreis r); unterwegs: Chance, sie irgendwo unterwegs zu treffen
const FIG := {
	"aelpler": {"name": "Sepp, der Älpler", "rolle": "aelpler", "kind": "person", "jacke": Color(0.15, 0.25, 0.5), "cap": true,
		"gross": 1.82, "pack": false, "orte": [Vector2(60, 0)], "r": 240.0, "unterwegs": 0.15, "wo": "Alp Tschuggen"},
	"sennerin": {"name": "Vreni, die Sennerin", "rolle": "sennerin", "kind": "person", "jacke": Color(0.72, 0.16, 0.14), "cap": false,
		"gross": 1.66, "pack": false, "orte": [Vector2(60, 0)], "r": 240.0, "unterwegs": 0.1, "wo": "Alp Tschuggen"},
	"huettenwartin": {"name": "Anna, die Betreuerin der Hütte", "rolle": "huettenwartin", "kind": "person", "jacke": Color(0.22, 0.46, 0.32),
		"cap": false, "gross": 1.7, "pack": true, "orte": [Vector2(60, 0), Vector2(-520, 560)], "r": 220.0, "unterwegs": 0.1,
		"wo": "Hütte und Biwak"},
	"wildhueter": {"name": "Ruedi, der Wildhüter", "rolle": "wildhueter", "kind": "person", "jacke": Color(0.32, 0.34, 0.2), "cap": true,
		"gross": 1.78, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.45, "wo": "überall im Tal"},
	# Wanderer und Bergsteiger: jeden Tag (jede Tour) andere
	"w_lena": {"name": "Lena, Wanderin", "rolle": "wanderer", "kind": "person", "jacke": Color(0.95, 0.5, 0.15), "cap": false,
		"gross": 1.68, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.55, "wo": "unterwegs"},
	"w_gerber": {"name": "Herr Gerber, Wanderer", "rolle": "wanderer", "kind": "elderly", "jacke": Color(0.45, 0.35, 0.25), "cap": true,
		"gross": 1.74, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.55, "wo": "unterwegs"},
	"w_jonas": {"name": "Jonas, Wanderer", "rolle": "wanderer", "kind": "person", "jacke": Color(0.2, 0.55, 0.3), "cap": false,
		"gross": 1.86, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.55, "wo": "unterwegs"},
	"b_nina": {"name": "Nina, Bergsteigerin", "rolle": "bergsteiger", "kind": "person", "jacke": Color(0.9, 0.75, 0.2), "cap": true,
		"gross": 1.67, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.45, "wo": "am Berg"},
	"b_toni": {"name": "Toni, Bergsteiger", "rolle": "bergsteiger", "kind": "person", "jacke": Color(0.75, 0.15, 0.12), "cap": true,
		"gross": 1.79, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.45, "wo": "am Berg"},
	"b_urs": {"name": "Urs, Kletterer", "rolle": "bergsteiger", "kind": "person", "jacke": Color(0.15, 0.35, 0.7), "cap": false,
		"gross": 1.76, "pack": true, "orte": [], "r": 0.0, "unterwegs": 0.45, "wo": "am Berg"}}
const ORDER := ["aelpler", "sennerin", "huettenwartin", "wildhueter", "w_lena", "w_gerber", "w_jonas", "b_nina", "b_toni", "b_urs"]
const FEST := ["aelpler", "sennerin", "huettenwartin", "wildhueter"]
const WANDERER := ["w_lena", "w_gerber", "w_jonas"]
const BERGSTEIGER := ["b_nina", "b_toni", "b_urs"]

# ---- Gegenstände (feste IDs, Brief Abenteuer-Ausbau) - nur die Namen für die Anzeige -----------------------------------------
const ITEM_NAMES := {"seil": "Seil", "stirnlampe": "Stirnlampe", "feldstecher": "Feldstecher", "kompass": "Kompass", "pickel": "Pickel",
		"hut": "Hut des Grossvaters", "taschenuhr": "Taschenuhr", "proviant": "Proviant", "kaese": "Käse", "batterien": "Batterien",
		"brief": "Brief", "ersatzteil": "Ersatzteil"}

# ---- Tausch: feste Wunschliste je Figur (kein Geld). Die Mechanik baut A4 (Rucksack) - hier nur wer will was gegen was.
# {will, will_n, gibt, gibt_n, einmal (nur ein einziges Mal)}
const WUENSCHE := {
	"aelpler": [{"will": "batterien", "will_n": 1, "gibt": "kaese", "gibt_n": 1, "einmal": false},
		{"will": "proviant", "will_n": 2, "gibt": "seil", "gibt_n": 1, "einmal": true}],
	"sennerin": [{"will": "proviant", "will_n": 1, "gibt": "kaese", "gibt_n": 1, "einmal": false},
		{"will": "batterien", "will_n": 2, "gibt": "kompass", "gibt_n": 1, "einmal": true}],
	"huettenwartin": [{"will": "kaese", "will_n": 1, "gibt": "proviant", "gibt_n": 2, "einmal": false},
		{"will": "batterien", "will_n": 1, "gibt": "stirnlampe", "gibt_n": 1, "einmal": true}],
	"wildhueter": [{"will": "proviant", "will_n": 1, "gibt": "batterien", "gibt_n": 1, "einmal": false},
		{"will": "kaese", "will_n": 1, "gibt": "batterien", "gibt_n": 2, "einmal": false}],
	"w_lena": [{"will": "kaese", "will_n": 1, "gibt": "proviant", "gibt_n": 1, "einmal": false}],
	"w_gerber": [{"will": "batterien", "will_n": 1, "gibt": "proviant", "gibt_n": 1, "einmal": false}],
	"w_jonas": [{"will": "kaese", "will_n": 1, "gibt": "batterien", "gibt_n": 1, "einmal": false}],
	"b_nina": [{"will": "proviant", "will_n": 2, "gibt": "seil", "gibt_n": 1, "einmal": true}],
	"b_toni": [{"will": "kaese", "will_n": 1, "gibt": "stirnlampe", "gibt_n": 1, "einmal": true}],
	"b_urs": [{"will": "proviant", "will_n": 1, "gibt": "batterien", "gibt_n": 1, "einmal": false}]}

# ---- Grüsse ----------------------------------------------------------------------------------------------------------------
const GRUSS := {
	"aelpler": [["neuhut", "Moment … diesen Hut kenne ich! Der gehört dem Bergführer. Dann bist du also sein Enkel. Willkommen auf der Alp!"],
		["erst", "Grüessech! Ich bin der Sepp, ich schaue diesen Sommer zu den Kühen. Was führt dich so weit hinauf?"],
		["f:markiert", "Da ist ja mein Wegmacher! Die frischen Markierungen sieht man von weitem."],
		["f:kaese_ja", "Ah, der Käsefreund ist wieder da! Die Kühe haben dich schon vermisst."],
		["f:kaese_nein", "Du schon wieder - der einzige Mensch, der keinen Käse mag. Trotzdem willkommen."],
		["hut", "Der Enkel des Bergführers! Schön, dass du wieder vorbeikommst."],
		["", "Grüessech! Wieder unterwegs?"]],
	"sennerin": [["neuhut", "Ui, dieser Hut! Den kennt hier jeder - du bist der Enkel vom Bergführer. Komm, setz dich kurz."],
		["erst", "Grüezi! Ich bin die Vreni. Ich mache hier oben den Käse - riechst du's?"],
		["q:q_schaf", "Da ist ja der, der mein schwarzes Schaf gefunden hat!"],
		["f:probiert", "Grüezi! Und, wie hat der Käse geschmeckt?"],
		["hut", "Schön, dich wieder zu sehen - mit dem Hut erkennt man dich schon von weitem."],
		["", "Grüezi! Grad recht zum Zvieri."]],
	"huettenwartin": [["neuhut", "Der Hut des Bergführers! Er steht dir. Für seinen Enkel gibt es in der Hütte immer einen Platz."],
		["erst", "Hoi! Ich bin die Anna, ich schaue zur Hütte und zum Biwak. Brauchst du einen Wetterbericht?"],
		["f:wetter_gefragt", "Hoi, schön dich zu sehen! Wieder Lust auf meinen Wetterbericht?"],
		["hut", "Hoi! Der Hut ist wieder unterwegs - schön."],
		["", "Hoi! Alles gut unterwegs?"]],
	"wildhueter": [["neuhut", "Den Hut kenne ich - der Bergführer! Dann bist du sein Enkel. Freut mich."],
		["erst", "Salü. Ich bin Ruedi, der Wildhüter. Ich zähle die Tiere im Tal - und dafür brauche ich manchmal Hilfe."],
		["f:auftrag_fertig", "Salü! Deine Aufnahmen waren gut. Vielleicht hätte ich wieder etwas für dich."],
		["", "Salü. Leise sein - dort oben am Fels steht eine Gämse."]],
	"w_lena": [["f:hilfe_bekommen", "Du! Dank dir ist mein Fuss wieder gut. Danke nochmals!"],
		["erst", "Hallo! Ich bin Lena, ich laufe heute bis zum Pass. Schöner Tag, oder?"],
		["hut", "Hallo nochmals! Schöner Hut - der sieht aus, als hätte er schon viele Gipfel gesehen."],
		["", "Hallo nochmals! Wir sehen uns ja immer wieder."]],
	"w_gerber": [["f:hilfe_bekommen", "Ah, mein Retter! Der Knöchel hält wieder. Vielen Dank."],
		["erst", "Guten Tag. Gerber, pensionierter Lehrer. Ich wandere jedes Jahr einmal durch dieses Tal."],
		["f:gelernt", "Guten Tag! Na, heute schon ein Edelweiss gesehen - und stehen lassen?"],
		["", "Guten Tag, guten Tag. Wieder auf Tour?"]],
	"w_jonas": [["f:hilfe_bekommen", "Hoi! Weisst du noch, der Fuss? Alles wieder gut - danke dir!"],
		["erst", "Hoi, ich bin Jonas. Ich trage alles für eine Woche mit - deshalb ist der Rucksack so gross."],
		["f:rat_fondue", "Hoi! Siehst du? Das Fondue-Set ist zu Hause geblieben. Zwei Kilo weniger!"],
		["", "Hoi! Wieder unterwegs?"]],
	"b_nina": [["f:hilfe_bekommen", "Hallo! Danke nochmals für die Hilfe neulich - der Fuss ist wieder ganz."],
		["erst", "Hallo! Ich bin Nina. Wir wollen morgen früh auf den Grat - und du?"],
		["f:seil_interesse", "Hallo! Na, immer noch Lust aufs Seil?"],
		["", "Hallo! Schön, dich wieder zu sehen."]],
	"b_toni": [["f:hilfe_bekommen", "Salü! Ohne dich wäre ich neulich lange dort gesessen. Merci!"],
		["erst", "Salü! Ich bin Toni. Ich bin heute schon um vier Uhr losgegangen."],
		["", "Salü! Wieder früh auf den Beinen?"]],
	"b_urs": [["f:hilfe_bekommen", "Hoi! Der Fuss ist wieder gut - danke dir nochmals."],
		["erst", "Hoi, ich bin Urs. Ich klettere am Gratspitz - der Fels ist dort richtig gut."],
		["", "Hoi! Auch wieder am Berg?"]]}

# Paket angleich (Daniel 31.10.2026): Sepps erster Gruss passt zur Jahreszeit der Runde (bergtal_abenteuer.gd SEASONS).
# GRUSS_JZ[fid][Bedingung][Jahreszeit] ersetzt den Text aus GRUSS; fehlt die Jahreszeit, gilt GRUSS («sommer»).
const GRUSS_JZ := {
	"aelpler": {"erst": {
		"fruehling": "Grüessech! Ich bin der Sepp, ich mache diesen Frühling die Alp parat für die Kühe. Was führt dich so weit hinauf?",
		"herbst": "Grüessech! Ich bin der Sepp, ich schaue diesen Herbst zu den Kühen, bis wir mit ihnen ins Tal ziehen. Was führt dich so weit hinauf?",
		"winter": "Grüessech! Ich bin der Sepp, ich schaue diesen Winter zur Alp und zu den Tieren im Stall. Was führt dich so weit hinauf?"}}}

# ---- Themen ----------------------------------------------------------------------------------------------------------------
# id, frage (was du sagst), cond, antwort (Text oder [[cond, Text], …]), merkt (Flag), effekt (siehe abenteuer_figuren.gd),
# frage2 {text, antworten [[Text, Flag]], nach {Flag: Antwort der Figur}}, einmal (nur ein Mal im ganzen Spiel)
const THEMEN := {
	"aelpler": [
		{"id": "grossvater", "frage": "Kanntest du meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Jeder hier kennt den Bergführer. Wenn er dir seine Karte gegeben hat, dann hat er dir den Weg zugetraut. Lies sie gut."},
		{"id": "alp", "frage": "Wie ist das Leben auf der Alp?",
			"antwort": "Um fünf Uhr melken, dann die Kühe auf die Weide, abends wieder melken. Dazwischen Zäune flicken. Streng - aber schöner kann man nicht arbeiten.",
			"frage2": {"text": "Und du - magst du Alpkäse?", "antworten": [["Sehr! Am liebsten würzig.", "kaese_ja"], ["Ehrlich gesagt nicht so.", "kaese_nein"]],
				"nach": {"kaese_ja": "Das hört man gern! Die Vreni macht den besten im ganzen Tal.", "kaese_nein": "Na ja - dann bleibt mehr für mich."}}},
		{"id": "kuehe", "frage": "Spüren die Kühe das Wetter?",
			"antwort": "Wenn sie am Morgen dicht beieinander liegen, kommt oft schlechtes Wetter, sagt man. Sicher ist das nicht - schau lieber, was MoveEye zum Luftdruck sagt."},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"sennerin": [
		{"id": "grossvater", "frage": "Kanntest du meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Natürlich. Dass du jetzt seinen Hut trägst und seine Karte liest - das hätte ihn gefreut. Mehr musst du nicht wissen, den Rest erzählt dir die Karte."},
		{"id": "kaese", "frage": "Wie macht man Alpkäse?",
			"antwort": "Milch ins Kessi, langsam wärmen, Lab dazu, dann mit der Harfe schneiden. Danach pressen und im Keller pflegen, jeden Tag mit Salzwasser. Ein Laib braucht Monate.",
			"frage2": {"text": "Möchtest du ein Stück probieren?", "antworten": [["Gern, danke!", "probiert"], ["Nein danke, ich habe genug dabei.", "nicht_probiert"]],
				"nach": {"probiert": "Hier, für unterwegs. Das gibt Kraft für den Aufstieg.", "nicht_probiert": "Wie du willst. Das Angebot steht."}},
			"effekt2": {"probiert": "essen"}},
		{"id": "tiere", "frage": "Gibt es hier viele Tiere?",
			"antwort": "Murmeltiere überall, am Fels Gämsen und manchmal Steinböcke. Der Ruedi - der Wildhüter - weiss viel mehr. Er sucht immer Leute, die mit MoveEye Tiere aufnehmen."},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"huettenwartin": [
		{"id": "grossvater", "frage": "Kanntest du meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Sein Name steht viele Male im Hüttenbuch. Was er dir sagen wollte, steht auf deiner Karte - nicht bei mir."},
		{"id": "wetter", "frage": "Wie wird das Wetter?", "effekt": "wetter", "merkt": "wetter_gefragt"},
		{"id": "platz", "frage": "Wo schlafe ich heute gut?", "effekt": "schlafplatz"},
		{"id": "tipp", "frage": "Hast du einen Tipp für den Berg?", "effekt": "tipp"},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"wildhueter": [
		{"id": "grossvater", "frage": "Kanntest du meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Wer im Tal kennt den Bergführer nicht? Seine Karte führt dich - ich kümmere mich um die Tiere."},
		{"id": "arbeit", "frage": "Was macht ein Wildhüter?",
			"antwort": "Tiere zählen, verletzte Tiere suchen, schauen, dass niemand das Wild stört. Eine Wildkamera hilft mir viel - sie sieht auch nachts."},
		{"id": "selten", "frage": "Welche Tiere sind hier selten?",
			"antwort": "Der Luchs - den sieht fast niemand, er ist nachts unterwegs und sehr scheu. Bartgeier und Steinadler kreisen über dem Grat. Murmeltiere und Schneehasen findest du leicht.",
			"frage2": {"text": "Hast du schon einmal einen Luchs gesehen?", "antworten": [["Nein, noch nie.", "luchs_nein"], ["Ich glaube schon - nur ganz kurz!", "luchs_ja"]],
				"nach": {"luchs_ja": "Dann hast du Glück gehabt. Nächstes Mal MoveEye aufstellen - dann hast du den Beweis.",
					"luchs_nein": "Wer Geduld hat und MoveEye gut hinstellt, hat eine Chance."}}},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"w_lena": [
		{"id": "grossvater", "frage": "Kennst du den Bergführer, meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Den Bergführer? Die Leute im Tal reden mit Respekt von ihm. Und der Hut steht dir!"},
		{"id": "geruecht", "frage": "Hast du unterwegs etwas Spezielles gesehen?", "effekt": "geruecht"},
		{"id": "wohin", "frage": "Wohin gehst du heute?",
			"antwort": "Über den Pass, am alten Hospiz vorbei. Früher soll es dort die beste Suppe im ganzen Kanton gegeben haben.",
			"frage2": {"text": "Und du, wohin?", "antworten": [["Ich folge einer alten Karte.", "karte_erzaehlt"], ["Einfach so, schauen.", "einfach_so"]],
				"nach": {"karte_erzaehlt": "Eine alte Karte? Wie spannend! Viel Glück.", "einfach_so": "Das ist das Schönste am Wandern."}}},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"w_gerber": [
		{"id": "grossvater", "frage": "Kennen Sie den Bergführer, meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Der Bergführer, natürlich - den Namen hört man hier oft. Ein schöner Hut, tragen Sie ihn mit Stolz."},
		{"id": "geruecht", "frage": "Haben Sie unterwegs etwas Spezielles gesehen?", "effekt": "geruecht"},
		{"id": "blumen", "frage": "Kennen Sie sich mit Blumen aus?",
			"antwort": "Dort am Hang blüht Enzian, weiter oben Edelweiss. Nur schauen, nicht pflücken - das Edelweiss ist in vielen Kantonen geschützt.",
			"frage2": {"text": "Wussten Sie das?", "antworten": [["Ja, natürlich.", "wusste"], ["Nein - gut zu wissen!", "gelernt"]],
				"nach": {"wusste": "Sehr gut. Dann sind Sie besser als meine ganze letzte Klasse.", "gelernt": "Dafür ist ein alter Lehrer da."}}},
		{"id": "tausch", "frage": "Möchten Sie etwas tauschen?", "effekt": "tausch"}],
	"w_jonas": [
		{"id": "grossvater", "frage": "Kennst du den Bergführer, meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Nur vom Hörensagen - die Leute hier reden gern von ihm. Cooler Hut!"},
		{"id": "geruecht", "frage": "Hast du unterwegs etwas Spezielles gesehen?", "effekt": "geruecht"},
		{"id": "rucksack", "frage": "Ist der Rucksack nicht zu schwer?",
			"antwort": "Sechzehn Kilo. Zu viel. Das Fondue-Set hätte ich zu Hause lassen sollen.",
			"frage2": {"text": "Was würdest du nächstes Mal weglassen?", "antworten": [["Das Fondue-Set!", "rat_fondue"], ["Nichts - Fondue muss sein.", "rat_kein"]],
				"nach": {"rat_fondue": "Du hast recht. Nächstes Mal bleibt es daheim.", "rat_kein": "Genau! Dafür trage ich gern zwei Kilo mehr."}}},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"b_nina": [
		{"id": "grossvater", "frage": "Kennst du den Bergführer, meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Unter Bergsteigern kennt man den Namen. Mit dem Hut bist du hier überall willkommen."},
		{"id": "geruecht", "frage": "Hast du unterwegs etwas Spezielles gesehen?", "effekt": "geruecht"},
		{"id": "seil", "frage": "Wozu braucht ihr das Seil?",
			"antwort": "Am Grat gibt es Stellen, da sichern wir uns. Ohne Seil und ohne Erfahrung: lieber den Wanderweg nehmen.",
			"frage2": {"text": "Soll ich dir einmal zeigen, wie man sichert?", "antworten": [["Gern, irgendwann!", "seil_interesse"], ["Nein, mir reicht der Wanderweg.", "seil_nein"]],
				"nach": {"seil_interesse": "Abgemacht. Zuerst aber mit einem Bergführer üben, nicht allein.", "seil_nein": "Auch gut. Der Wanderweg hat die schönere Aussicht."}}},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"b_toni": [
		{"id": "grossvater", "frage": "Kennst du den Bergführer, meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Wer am Berg unterwegs ist, kennt den Namen. Pass gut auf den Hut auf."},
		{"id": "geruecht", "frage": "Hast du unterwegs etwas Spezielles gesehen?", "effekt": "geruecht"},
		{"id": "frueh", "frage": "Warum bist du so früh los?",
			"antwort": "Am Morgen ist der Schnee hart und das Wetter am ruhigsten. Am Nachmittag kommen oft die Gewitter."},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}],
	"b_urs": [
		{"id": "grossvater", "frage": "Kennst du den Bergführer, meinen Grossvater?", "cond": "hut", "einmal": true,
			"antwort": "Klar habe ich von ihm gehört. Schön, dass sein Hut wieder am Berg ist."},
		{"id": "geruecht", "frage": "Hast du unterwegs etwas Spezielles gesehen?", "effekt": "geruecht"},
		{"id": "klettersteig", "frage": "Ist der Klettersteig schwierig?",
			"antwort": "Mit Klettersteig-Set, Helm und etwas Übung geht's gut. Eisenstufen, Leitern, Drahtseil - und eine Aussicht!"},
		{"id": "tausch", "frage": "Möchtest du etwas tauschen?", "effekt": "tausch"}]}

# Gerüchte der Wanderer und Bergsteiger (je Tag ein anderes) - nur lustige Dinge im Tal, nichts zur Schatzkarte
const GERUECHTE := ["Im Bunker beim Pass soll es nachts ein Büro für Murmeltiere geben. Ich glaube kein Wort.",
		"Eine Kuh hat mir heute fast eine Socke gestohlen. Pass auf deine Schuhe auf!",
		"Oben am Grat soll es einen Platz geben, wo man im August viele Sternschnuppen sieht.",
		"Bei Niedrigwasser soll man hinter den Wasserfall gehen können. Dahinter glitzert es.",
		"Gestern ist ein Gleitschirm mitten auf der Kuhweide gelandet. Die Kühe waren begeistert.",
		"In der alten Sennerei liegt ein uralter Käse. Riechen kann man ihn bis zum Weg.",
		"Im Gipfelbuch auf dem Tschingelspitz stehen sehr lustige Einträge.",
		"Eine Gämse stand heute Morgen auf dem Dach vom Hospiz. Einfach so."]
# Tipps von Anna, der Betreuerin der Hütte (je Tag einer)
const TIPPS := ["Früh los, früh zurück: am Nachmittag kommen die Gewitter.",
		"Trink, bevor du Durst hast. Am Bach kannst du auffüllen.",
		"Die Stirnlampe gehört immer in den Rucksack - auch wenn du vor dem Dunkeln zurück sein willst.",
		"Wenn Nebel kommt: stehen bleiben, Kompass heraus, dann erst weiter.",
		"Den Proviant nachts gut verschliessen - der Fuchs hat eine feine Nase."]

# ---- Nebenaufgaben ---------------------------------------------------------------------------------------------------------
# typ: tier (Tier zurückbringen) | bote (Botendienst) | hilfe (Hilfe am Berg) | wild (Wildhüter-Auftrag, Foto macht A1)
# von: wer den Auftrag gibt · cond: wann er ihn anbietet · kurz: Zeile in der Übersicht · lohn: Erfahrung, Vertrauen, Gegenstand
const QUESTS := {
	"q_ziege": {"typ": "tier", "von": "aelpler", "tier": "ziege", "ort": Vector2(-175, -300), "r": 230.0, "kurz": "Ziege Flocke suchen (beim Fondueplätzli am Gumpisee)",
		"angebot": "Meine Ziege Flocke ist ausgebüxt. Zuletzt hat man sie beim Fondueplätzli am Gumpisee gesehen. Bringst du sie zurück, wenn du sie siehst?",
		"erinnerung": "Und? Schon etwas von Flocke gesehen?",
		"gefunden": "Da steht eine Ziege mit einer Glocke und kaut an einem Busch - das muss Flocke sein!",
		"dank": "Flocke! Da bist du ja, du Ausreisserin. Danke vielmals - ohne dich hätte ich den ganzen Tag gesucht.",
		"lohn": {"xp": 60, "v": 1, "gib": ""}},
	"q_schaf": {"typ": "tier", "von": "sennerin", "tier": "schaf", "ort": Vector2(-470, -265), "r": 220.0, "kurz": "Schwarzes Schaf suchen (beim Riedmoos)",
		"angebot": "Ein Schaf hat sich von der Herde getrennt - ein schwarzes, gut zu erkennen. Zuletzt war es beim Riedmoos. Hältst du die Augen offen?",
		"erinnerung": "Hast du mein schwarzes Schaf irgendwo gesehen?",
		"gefunden": "Im Wollgras steht ein schwarzes Schaf und blökt dich an.",
		"dank": "Mein schwarzes Schaf! Danke - da hast du dir ein Stück Käse verdient.",
		"lohn": {"xp": 60, "v": 1, "gib": "kaese"}},
	"q_kuh": {"typ": "tier", "von": "aelpler", "cond": "q:q_ziege", "tier": "kuh", "ort": Vector2(-650, 430), "r": 240.0, "kurz": "Kuh Bless suchen (Steimandli-Wald)",
		"angebot": "Die Bless ist wieder weg - meine neugierigste Kuh. Die läuft immer den Steinmännern nach, hinauf Richtung Biwak.",
		"erinnerung": "Die Bless ist immer noch nicht zurück …",
		"gefunden": "Zwischen den Steinmännern steht eine Kuh mit einem weissen Fleck auf der Stirn und schaut dich an. Die Bless!",
		"dank": "Die Bless! Du bist ein Goldschatz. Die Alp ist dir etwas schuldig.",
		"lohn": {"xp": 80, "v": 1, "gib": "kaese"}},
	"q_brief": {"typ": "bote", "von": "huettenwartin", "item": "brief", "an": "sennerin", "kurz": "Brief von Anna zur Sennerin Vreni bringen",
		"angebot": "Kannst du der Vreni auf der Alp diesen Brief bringen? Es ist die Bestellung für den Käse.",
		"abgabe": "Ich habe einen Brief von Anna für dich.",
		"dank": "Die Käse-Bestellung! Danke - richte Anna einen Gruss aus.",
		"lohn": {"xp": 40, "v": 1, "gib": ""}},
	"q_kaese": {"typ": "bote", "von": "sennerin", "cond": "q:q_brief", "item": "kaese", "an": "huettenwartin", "kurz": "Käse von Vreni zu Anna, der Betreuerin der Hütte, bringen",
		"angebot": "Anna wartet auf einen Laib Käse für die Hütte. Nimmst du ihn mit, wenn du sie siehst?",
		"abgabe": "Ich bringe dir den Käse von Vreni.",
		"dank": "Wunderbar! Dann gibt es heute Abend Käseschnitten.",
		"lohn": {"xp": 40, "v": 1, "gib": "proviant"}},
	"q_ersatzteil": {"typ": "bote", "von": "aelpler", "item": "ersatzteil", "hol": Vector2(205, -690), "r": 240.0, "an": "aelpler",
		"kurz": "Ersatzteil bei der Postauto-Haltestelle holen und Sepp bringen",
		"angebot": "Bei der Postauto-Haltestelle unten bei der Kapelle liegt ein Paket für mich - ein Ersatzteil für die Melkmaschine. Holst du es, wenn du dort vorbeikommst?",
		"erinnerung": "Das Paket liegt noch bei der Haltestelle, oder?",
		"abholen": "An der Postauto-Haltestelle steht ein Paket: «Für Sepp, Alp Tschuggen». Das Ersatzteil!",
		"abgabe": "Hier ist dein Ersatzteil von der Haltestelle.",
		"dank": "Endlich! Jetzt läuft die Melkmaschine wieder. Merci vielmal.",
		"lohn": {"xp": 50, "v": 1, "gib": ""}},
	"q_proviant": {"typ": "bote", "von": "huettenwartin", "item": "proviant", "an_ort": Vector2(-520, 560), "r": 240.0, "cond": "v1",
		"kurz": "Proviant ins Biwak Chüebodehorn bringen",
		"angebot": "Im Biwak am Chüebodehorn ist der Vorrat leer. Kannst du diesen Proviant mitnehmen und dort ins Kästchen legen?",
		"abholen": "Du legst den Proviant ins Kästchen im Biwak. Die nächsten Bergsteiger werden sich freuen.",
		"dank": "Du warst im Biwak? Danke - jetzt ist der Vorrat wieder voll.",
		"lohn": {"xp": 50, "v": 1, "gib": ""}},
	"q_markieren": {"typ": "hilfe", "von": "aelpler", "cond": "wieder", "kurz": "Wegmarkierungen auffrischen (unterwegs)",
		"angebot": "Die weiss-rot-weissen Markierungen am Bergweg sind verblasst. Nimmst du Farbe und Pinsel mit und frischst unterwegs ein paar auf?",
		"erinnerung": "Hast du schon Zeit gefunden für die Markierungen?",
		"arbeit": "Am Fels ist eine verblasste weiss-rot-weisse Markierung. Zeit für Pinsel und Farbe.",
		"gemacht": "Weiss, rot, weiss - jetzt sieht man den Weg wieder, auch im Nebel.",
		"dank": "Du hast die Markierungen aufgefrischt? Merci - die Wanderer werden es dir danken.",
		"lohn": {"xp": 50, "v": 1, "gib": ""}},
	# Hilfe am Berg: ein Wanderer oder Bergsteiger hat sich verletzt (kommt von selbst, kein Auftrag)
	"q_verletzt": {"typ": "hilfe", "von": "", "kurz": "Verletzten Wanderer melden (Betreuerin der Hütte oder Wildhüter)",
		"angebot": "%s sitzt am Weg und hält sich den Knöchel. «Umgeknickt. Ich komme kaum noch weiter.»",
		"abgabe": "Am Weg sitzt jemand mit verstauchtem Fuss.",
		"dank": "Danke, dass du Bescheid sagst. Ich schicke gleich jemanden hinauf.",
		"lohn": {"xp": 40, "v": 1, "gib": ""}},
	# Wildhüter-Aufträge: nur Auftrag und Abschluss - das Foto macht MoveEye (Paket A1)
	"q_wild_murmeltier": {"typ": "wild", "von": "wildhueter", "tier": "murmeltier", "kurz": "Wildhüter: Murmeltier mit MoveEye aufnehmen",
		"angebot": "Ich zähle die Murmeltiere. Stell MoveEye bei deinem Lager auf und bring mir eine Aufnahme von einem Murmeltier.",
		"erinnerung": "Schon ein Murmeltier vor MoveEye gehabt?", "abgabe": "Hier ist die Aufnahme von einem Murmeltier.",
		"dank": "Ein schönes Bild - man sieht sogar den Bau. Danke!", "lohn": {"xp": 50, "v": 1, "gib": ""}},
	"q_wild_schneehase": {"typ": "wild", "von": "wildhueter", "cond": "q:q_wild_murmeltier", "tier": "schneehase", "kurz": "Wildhüter: Schneehase mit MoveEye aufnehmen",
		"angebot": "Der Schneehase wechselt sein Fell mit der Jahreszeit. Bringst du mir eine Aufnahme von einem?",
		"erinnerung": "Hast du schon einen Schneehasen erwischt?", "abgabe": "Hier ist die Aufnahme vom Schneehasen.",
		"dank": "Perfekt, genau das brauchte ich für die Zählung.", "lohn": {"xp": 60, "v": 1, "gib": ""}},
	"q_wild_gaemse": {"typ": "wild", "von": "wildhueter", "cond": "q:q_wild_schneehase", "tier": "gaemse", "kurz": "Wildhüter: Gämse an der Rüfi aufnehmen",
		"angebot": "In der Dämmerung kommen die Gämsen an der Rüfi herunter. Stell MoveEye dort an den Wildwechsel - eine Aufnahme wäre wertvoll.",
		"erinnerung": "Und die Gämsen an der Rüfi?", "abgabe": "Hier ist die Aufnahme von der Gämse.",
		"dank": "Eine Geiss mit Kitz - sehr gut! Danke.", "lohn": {"xp": 70, "v": 1, "gib": ""}},
	"q_wild_steinbock": {"typ": "wild", "von": "wildhueter", "cond": "q:q_wild_gaemse", "tier": "steinbock", "kurz": "Wildhüter: Steinbock am Fels aufnehmen",
		"angebot": "Am Fels über dem Biwak stehen manchmal Steinböcke. Eine Aufnahme in der Dämmerung, das wäre etwas.",
		"erinnerung": "Hast du die Steinböcke gesehen?", "abgabe": "Hier ist die Aufnahme vom Steinbock.",
		"dank": "Ein alter Bock - an den Hörnern sieht man, wie alt er ist. Danke!", "lohn": {"xp": 80, "v": 1, "gib": ""}},
	"q_wild_bartgeier": {"typ": "wild", "von": "wildhueter", "cond": "q:q_wild_steinbock", "tier": "bartgeier", "kurz": "Wildhüter: Bartgeier über dem Grat aufnehmen",
		"angebot": "Über dem Grat kreist ein Bartgeier. Wir wissen nicht, ob er hier brütet. Eine Aufnahme würde helfen.",
		"erinnerung": "Hast du den Bartgeier erwischt?", "abgabe": "Hier ist die Aufnahme vom Bartgeier.",
		"dank": "Tatsächlich, ein junger! Das muss ich gleich melden.", "lohn": {"xp": 90, "v": 1, "gib": ""}},
	"q_wild_luchs": {"typ": "wild", "von": "wildhueter", "cond": "q:q_wild_bartgeier&v3", "tier": "luchs", "kurz": "Wildhüter: den Luchs aufnehmen (nachts)",
		"angebot": "Jetzt das Schwierigste: der Luchs. Nachts, sehr scheu. Stell MoveEye an einen Wildwechsel und hab Geduld.",
		"erinnerung": "Der Luchs lässt sich Zeit, oder?", "abgabe": "Ich habe den Luchs aufgenommen!",
		"dank": "Der Luchs! Das ist die beste Aufnahme des Sommers. Danke!", "lohn": {"xp": 150, "v": 1, "gib": ""}}}
const QUEST_ORDER := ["q_ziege", "q_ersatzteil", "q_markieren", "q_kuh", "q_schaf", "q_brief", "q_kaese", "q_proviant",
		"q_wild_murmeltier", "q_wild_schneehase", "q_wild_gaemse", "q_wild_steinbock", "q_wild_bartgeier", "q_wild_luchs"]
# Tiere für «Tier zurückbringen»: Art in actor.gd, Farbe (Ziege braun), Wärmebild-Fell °C
const TIERE := {"ziege": ["sheep", Color(0.55, 0.42, 0.3), 37.0], "schaf": ["sheep", Color(0.1, 0.1, 0.1), 37.0],
		"kuh": ["cow", Color(0.45, 0.3, 0.2), 36.0]}
const ALP := Vector2(60, 0)
