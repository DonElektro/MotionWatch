#@ Motion Watch – Teil 630: Extras: Überlebens-Almanach. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ---- Überlebens-Almanach (2.95.54): tips and tricks for camping in Switzerland, to look up or to read in the evening;
# offline on the device (/almanach/, also for guests in the same Wi-Fi), «Tipp des Abends» on the TV view. ----
# Überlebens-Almanach für MoveEye: Kapitel -> Artikel. Text: Absätze mit Leerzeile, Listenpunkte mit "- ".
ALMANAC = [
 ("notfall", "🆘", "Notfall", [
  ("Notrufnummern Schweiz", """Merk dir diese Nummern:

- 144 – Sanität / Rettungsdienst: für alle medizinischen Notfälle richtig
- 1414 – Rega (Rettungshelikopter), am besten über die Rega-App: sie schickt deinen Standort mit
- Im Wallis wird die Bergrettung über 144 alarmiert, nicht über 1414
- 112 – europäische Notrufnummer; lässt sich auch ohne PIN wählen
- 117 – Polizei
- 118 – Feuerwehr
- 145 – Tox Info Suisse (Vergiftungen)

Am Telefon: Wo ist der Unfallort (Koordinaten – siehe «Mein Standort» oben im Kapitel)? Wer ruft an und ist wie erreichbar? Was ist passiert? Wie viele Personen sind betroffen, wie sind sie verletzt? Wie ist das Wetter vor Ort?"""),
  ("Kein Netz – was jetzt?", """Für einen Alarm mit dem Handy braucht es wenigstens eine schwache Verbindung zu einem Mobilfunknetz.

- Den Standort wechseln: ein paar Meter höher oder auf eine Kuppe steigen hilft oft.
- Kommst du mit der Rega-App oder 1414 nicht durch, versuche die 112.
- Akku sparen: Bildschirm dunkel, nichts anderes laufen lassen.
- Ohne jedes Netz: alpines Notsignal (siehe «Notsignale»), beim Verletzten bleiben, wenn jemand anderes Hilfe holt.

Wer oft ohne Empfang unterwegs ist: Es gibt Notfunkgeräte und Satelliten-Melder."""),
  ("Notsignale", """Alpines Notsignal: sechsmal pro Minute ein Zeichen geben (rufen, pfeifen, blinken), eine Minute warten, dann wiederholen. Die Antwort: dreimal pro Minute ein Zeichen, eine Minute warten, wiederholen.

Für den Helikopter: Beide Arme schräg hoch wie ein Y bedeutet YES = «Ja, wir brauchen Hilfe». Ein Arm schräg hoch, der andere schräg nach unten wie ein N bedeutet NO = «Nein, wir brauchen keine Hilfe»."""),
  ("Die stabile Seitenlage", """Für Bewusstlose, die normal atmen. Zuerst die Atmung prüfen.

- Neben die Person knien. Den Arm, der dir zugewandt ist, rechtwinklig abspreizen.
- Den anderen Arm auf die Brust der Person legen.
- Die Beine gestreckt nebeneinander legen.
- Die Person an Schulter und Hüfte zu dir drehen, bis der Bauch deutlich zum Boden zeigt.
- Den oberen Arm und das obere Bein anwinkeln – sie stützen den Körper ab.
- Den Kopf leicht nach hinten strecken, sodass der geöffnete Mund nach unten schaut.
- Notruf 144. Vor Kälte, Hitze und Nässe schützen, Atmung immer wieder kontrollieren.

Atmet die Person nicht normal: sofort 144 und wiederbeleben. 30 Mal in der Mitte der Brust drücken, 5–6 cm tief, 100 bis 120 Mal pro Minute, dann 2 Beatmungen – oder ohne Beatmung einfach weiterdrücken. Ist ein Defibrillator (AED) da: einschalten und den Anweisungen folgen.

Das lernt man am besten in einem Kurs, zum Beispiel bei einem Samariterverein."""),
  ("Blutungen", """Stark blutende Wunden: sofort fest auf die Wunde drücken – mit allem, was gerade da ist (sauberes Tuch, Verband, notfalls die Hand). Wenn es geht, den blutenden Arm oder das Bein dabei hochhalten.

Bei starker Blutung sofort 144 anrufen oder jemanden damit beauftragen. Einen kräftigen Druckverband anlegen und weiter drücken, bis Hilfe da ist."""),
  ("Verbrennungen", """Mindestens 10 Minuten unter fliessendem, handwarmem Wasser kühlen (etwa 15–20 °C, nicht eiskalt). Wegen der Gefahr der Unterkühlung nur die verletzte Stelle kühlen – das gilt besonders für Kinder.

- Eingebrannte Kleidung nicht entfernen.
- Nie Hausmittel wie Mehl, Zahnpasta oder Öl auf die Wunde geben.
- Danach mit einem trockenen, sauberen Verband abdecken.

Bei schweren oder grossen Verbrennungen und bei Kindern: 144 anrufen. Im Zweifel die Wunde ärztlich zeigen."""),
  ("Erste-Hilfe-Set für das Camping", """- Pflaster in mehreren Grössen, sterile Kompressen, zwei Gazebinden, elastische Binde
- Desinfektionsmittel, Zeckenzange oder -karte, Pinzette, Schere
- Rettungsdecke, Einweghandschuhe, Dreiecktuch
- Blasenpflaster, Wundsalbe, Sonnencreme, Insektenschutz
- Schmerzmittel und eigene Medikamente (genug für ein paar Tage mehr)
- Stirnlampe mit vollen Akkus, Trillerpfeife

Einmal im Jahr durchsehen: Ablaufdaten, verbrauchte Sachen nachfüllen."""),
 ]),
]
# Hauptdatei kleiner (Nov. 2026): only the chapter «Notfall» above stays in the program file (ALMANAC is pinned in bauen.py:
# emergency numbers and first aid are there without the data zip, and almanac_tip() never sees an empty list). The other
# chapters are a plain literal of their own, so bauen.py moves them into the data zip; with the zip the list is the same
# as before. Without the zip /almanach shows the chapter «Notfall» as a plain page (alm_notfall_seite below).
ALMANAC_WEITER = [
 ("wetter", "⛈", "Wetter lesen", [
  ("Gewitter: wie nah ist es?", """Zähle die Sekunden zwischen Blitz und Donner: Drei Sekunden entsprechen etwa einem Kilometer. Wer den Donner hört, ist schon in Reichweite (weniger als etwa 10 km) – jetzt Schutz suchen. Liegen Blitz und Donner 10 Sekunden oder weniger auseinander, besteht unmittelbare Lebensgefahr. Erst wenn eine halbe Stunde lang kein Donner mehr zu hören war, ist das Gewitter vorbei.

Sicher: feste Gebäude und geschlossene Autos. Unsicher: einzelne Bäume, Baumgruppen, Waldränder, Gipfel, freies Feld. Ein Zelt schützt nicht – es ist so gefährlich wie der Aufenthalt im Freien."""),
  ("Draussen vom Gewitter überrascht", """- Weg von Gipfeln, einzelnen Bäumen, Baumgruppen und Waldrändern. Etwas Schutz bieten eine Mulde oder ein Hohlweg – aber kein Bachbett (Hochwasser).
- Zu allen Bäumen und Ästen möglichst 10 m Abstand halten.
- In die Hocke gehen, die Füsse eng zusammen, wenn möglich auf einer isolierenden Unterlage (Rucksack, Isomatte).
- Jede Person für sich, mit Abstand zueinander: mindestens einen Meter, besser drei.
- Abstand zu Metallzäunen; Velos und andere Metallgegenstände weglegen.
- Vom Zelt aus wenn möglich in ein Auto oder ein Gebäude wechseln."""),
  ("Wolken als Wettervorhersage", """Das sind überlieferte Erfahrungsregeln. Sie helfen beim Beobachten, sind aber keine sichere Vorhersage – die Wetter-App und der Luftdruck oben im Kapitel gehören dazu.

- Schäfchenwolken am Morgen: oft schlägt das Wetter im Lauf des Tages um.
- Quellwolken, die schon am Vormittag hoch in die Höhe wachsen: Gewittergefahr am Nachmittag.
- Ein Amboss oben auf einer Wolke: das Gewitter ist da oder kommt.
- Federwolken, die dichter werden und in einen Schleier übergehen: oft kommt in den nächsten ein bis zwei Tagen Regen.
- Ein Hof um Sonne oder Mond: Feuchtigkeit kommt, oft Regen."""),
  ("Föhn und Bise", """Föhn: warmer, trockener Fallwind auf der Alpennordseite. Sehr klare Sicht, die Berge wirken nah. Gefährlich: Sturmböen in Föhntälern (Reuss, Linth, Rhein), Waldbrandgefahr, und wenn er zusammenbricht kommt oft schnell Regen. Zelt gut abspannen.

Bise: kalter Nordostwind im Mittelland, vor allem am Genfersee und im Seeland. Fühlt sich viel kälter an, als das Thermometer zeigt. Das Zelt mit der schmalen Seite in den Wind stellen."""),
  ("Kälte in der Nacht", """Auch im Sommer wird es in den Bergen nachts kalt – pro 100 Höhenmeter etwa 0,6 °C kühler, bei klarem Himmel noch kälter.

- Die Isomatte ist wichtiger als der Schlafsack: von unten verliert man am meisten Wärme.
- Trockene Kleider für die Nacht, nicht die verschwitzten vom Tag.
- Mütze auf, vor dem Schlafen etwas essen und warm trinken, kurz bewegen.
- Eine Flasche mit warmem Wasser (gut verschlossen) im Schlafsack wärmt stundenlang."""),
 ]),
 ("gesundheit", "🩹", "Gesundheit draussen", [
  ("Zecken", """Zecken gibt es in der Schweiz bis etwa 2000 m über Meer; sie können FSME und Borreliose übertragen. Die ganze Schweiz ausser dem Kanton Tessin gilt als FSME-Risikogebiet, die Impfung wird dort im Allgemeinen ab 3 Jahren empfohlen – frag deine Hausärztin.

- Lange Hosen, Socken über die Hosenbeine, Zeckenschutzmittel.
- Abends den ganzen Körper absuchen, auch Kniekehlen, Leisten, Achseln, Haaransatz (bei Kindern Kopf!).
- Eine Zecke sofort mit einer feinen Pinzette, Zeckenzange oder -karte direkt über der Haut fassen und mit gleichmässigem Zug gerade herausziehen. Nicht quetschen, kein Öl, kein Klebstoff. Danach die Stelle desinfizieren.
- Die Stelle markieren und Datum notieren. Wird sie in den nächsten Wochen rot und grösser (Wanderröte) oder kommen Fieber und Gliederschmerzen: zum Arzt."""),
  ("Unterkühlung", """Wer lange friert, verliert mehr Wärme, als der Körper nachliefern kann. Zittern ist die Heizung des Körpers.

- Vor weiterem Auskühlen schützen: aus Wind und Nässe, zudecken (Schlafsack, Rettungsdecke, Jacken) und gegen den kalten Boden isolieren (Isomatte, Rucksack, Äste).
- Nicht zu lange warten mit dem Alarm – besonders in der kalten Jahreszeit: 144 oder Rega 1414.
- Ist die Person verwirrt, sehr schläfrig oder bewusstlos, ist es ein Notfall."""),
  ("Hitze und Sonne", """Hitzschlag: Die Haut ist heiss oder gerötet, trocken oder feucht; dazu können Benommenheit, Erbrechen und eine erhöhte Körpertemperatur kommen. Ein Hitzschlag ist lebensgefährlich – sofort 144.

- An einen kühleren Ort bringen, enge Kleider lockern.
- Kühle, feuchte Tücher auflegen, Luft zufächeln. Wenn nötig schneller kühlen: kalte Umschläge an Nacken, Achseln, Leisten, Hand- und Fussgelenken.
- Ist die Person bei Bewusstsein: kühles Wasser in kleinen Schlucken trinken lassen.
- Vorbeugen: Hut, viel trinken, in der Mittagshitze Pause, Sonnenschutz."""),
  ("Schlangen in der Schweiz", """In der Schweiz gibt es acht Schlangenarten; nur zwei sind giftig: die Aspisviper und die Kreuzotter. Sie leben vor allem an sonnigen Hängen im Jura und in den Alpen, im Mittelland kommen sie praktisch nicht vor.

Vipern haben eine schlitzförmige Pupille, die harmlosen Nattern eine runde. Farbe und Zeichnung sind bei allen Arten sehr verschieden und taugen nicht zum Erkennen. Eine einheimische Schlange, die länger als 90 cm ist, ist sicher harmlos. So nah muss aber niemand hingehen: nicht anfassen, der Schlange den Fluchtweg frei lassen oder ruhig mit etwa 2 m Abstand vorbeigehen. Alle Schlangen sind in der Schweiz geschützt.

Nach einem Biss:

- Ruhe bewahren. Ringe und Uhr am gebissenen Arm ablegen.
- Die Wunde desinfizieren, den Arm oder das Bein ruhigstellen.
- Schonend zum Arzt oder ins Spital – jeder Biss einer Giftschlange gehört in ärztliche Betreuung, auch ohne Beschwerden. Hilfe: 144, Tox Info 145.
- Nicht abbinden, nicht einschneiden, nicht aussaugen, kein Eis, kein Alkohol.

Bisse sind selten, und schwere Verläufe sind die Ausnahme; gefährlich sind vor allem allergische Reaktionen."""),
  ("Wespen und Bienen", """- Keine hastigen Bewegungen. Essensreste und offene Getränke nicht herumstehen lassen.
- Stich: Den Stachel möglichst schnell entfernen, ohne die Giftblase zu quetschen – mit dem Fingernagel oder einer Karte seitlich wegschieben. Kühlen (kaltes Wasser, Kühlgel).
- Stich am Hals, im Mund oder im Rachen: sofort 144 – die Schwellung kann die Atemwege verschliessen.
- Auch 144 bei Anzeichen einer schweren allergischen Reaktion: Ausschlag am ganzen Körper, Herzrasen, Schwindel, Atemnot. Allergiker haben ihr Notfallset immer dabei."""),
  ("Blasen an den Füssen", """Früh reagieren: Spürst du eine heisse, reibende Stelle, sofort ein Blasenpflaster darauf, bevor die Blase entsteht. Eine kleine Blase nicht aufstechen, mit einem Blasenpflaster schützen. Gute Socken (keine Baumwolle), eingelaufene Schuhe, Schnürung prüfen."""),
 ]),
 ("wasser", "💧", "Wasser", [
  ("Wie viel Wasser braucht man?", """Etwa 2–3 Liter pro Person und Tag zum Trinken, bei Hitze oder Anstrengung deutlich mehr. Dazu Wasser zum Kochen und Abwaschen. Dunkler Urin heisst: mehr trinken."""),
  ("Wasser aus Bach und See", """Auch klares Bergwasser kann Keime enthalten (Kühe und Wild weiter oben). Sicher machen:

- Abkochen: Wasser sprudelnd aufkochen lassen. In grosser Höhe etwas länger kochen.
- Filtern: ein Wasserfilter mit feinen Poren hält Bakterien und Parasiten zurück, meist aber keine Viren.
- Tabletten (Chlor oder Chlordioxid): Einwirkzeit auf der Packung beachten.

Trübes Wasser zuerst durch ein Tuch laufen lassen oder stehen lassen, damit sich der Schmutz setzt. Quellen sind meist besser als Bäche, Bäche besser als stehende Tümpel."""),
  ("Wasser finden", """- Grüne, saftige Vegetation und Mulden im Gelände zeigen Wasser an.
- Vögel und Tierpfade führen am Abend oft zu Wasser.
- Brunnen in Dörfern und auf Alpen: «Kein Trinkwasser» beachten.
- Am Morgen: Tau von Gras mit einem Tuch aufsaugen und auswringen (danach trotzdem behandeln)."""),
 ]),
 ("feuer", "🔥", "Feuer", [
  ("Bevor du ein Feuer machst", """Zuerst: Gilt ein Feuerverbot? Bei Trockenheit erlassen die Kantone Feuerverbote im Wald und in Waldnähe – sie gelten auch für Grillstellen. Informationen: Website des Kantons, MeteoSchweiz (Waldbrandgefahr), Schilder vor Ort.

- Nur auf bestehenden Feuerstellen oder mit Erlaubnis des Grundeigentümers.
- Mindestens 10 m Abstand zu Zelten, Bäumen und trockenem Gras.
- Wasser oder Sand zum Löschen bereitstellen.
- Bei starkem Wind kein Feuer."""),
  ("Ein Feuer aufbauen", """Feuer braucht drei Dinge: Brennstoff, Hitze und Luft.

- Zunder: trockenes Gras, Birkenrinde, Tannenzapfen, Watte mit etwas Vaseline.
- Anzündholz: dünne, trockene Ästchen, so dick wie ein Streichholz bis wie ein Finger. Tote Äste, die noch am Baum hängen, sind trockener als die am Boden.
- Brennholz: armdick, erst nachlegen, wenn das Anzündholz gut brennt.

Als Pyramide aufbauen (Zunder in der Mitte, Ästchen schräg darüber wie ein Tipi) – sie brennt schnell an. Als Pagodenfeuer (Hölzer kreuzweise geschichtet wie eine Blockhütte) gibt es gleichmässige Glut zum Kochen. Beim Sternfeuer liegen dicke Äste wie Speichen um die Glut und werden nachgeschoben: sparsam für lange Abende. Von der Windseite her anzünden."""),
  ("Feuer richtig löschen", """Wasser darüber, mit einem Stock umrühren, nochmals Wasser – bis nichts mehr zischt und alles kalt ist (Hand darüber halten). Glut kann unter der Asche tagelang weiterglimmen und bei Wind wieder aufflammen. Nie ein Feuer unbeaufsichtigt lassen."""),
  ("Feuer ohne Streichhölzer", """- Feuerstahl: Funken auf sehr feinen, trockenen Zunder schlagen. Funktioniert auch nass.
- Batterie und Stahlwolle: die Pole einer 9-Volt-Batterie an feine Stahlwolle halten – sie glüht sofort.
- Lupe oder Brillenglas bei starker Sonne.
Übe das zu Hause, bevor du es brauchst."""),
 ]),
 ("orientierung", "🧭", "Orientierung", [
  ("Norden finden mit der Sonne", """Die Sonne steht um die Mittagszeit (in der Schweiz im Sommer etwa um 13:30, im Winter um 12:30) im Süden. Am Morgen ist sie im Osten, am Abend im Westen.

Mit einer Zeigeruhr: den Stundenzeiger auf die Sonne richten. Die Mitte zwischen Stundenzeiger und der 1 (Sommerzeit) bzw. 12 (Winterzeit) zeigt nach Süden.

Mit einem Stock: einen Stock senkrecht in den Boden stecken und die Spitze seines Schattens mit einem Stein markieren. Nach etwa 20 Minuten die neue Schattenspitze markieren. Die Linie vom ersten zum zweiten Stein zeigt von Westen nach Osten."""),
  ("Norden finden in der Nacht", """Den Grossen Wagen suchen (sieben helle Sterne wie eine Pfanne). Die Strecke der beiden hinteren Sterne des «Wagenkastens» fünfmal verlängern – dort ist der Polarstern, ein nicht besonders heller Stern. Er steht fast genau im Norden und bewegt sich die ganze Nacht nicht."""),
  ("Karte und Handy", """- Lade die Karte des Gebiets vorher herunter (z. B. swisstopo-App – sie zeigt auch Wanderwege und funktioniert offline).
- Merk dir markante Punkte: Gipfel, Seen, Kirchtürme, Strassen.
- Ein Zettel mit Notfallnummern und der Adresse des Campingplatzes gehört in den Rucksack – falls der Akku leer ist.
- Verlaufen? Stehen bleiben, nachdenken, zurück zum letzten bekannten Punkt. Im Nebel nicht weiter ins Unbekannte."""),
 ]),
 ("lager", "⛺", "Lagerplatz und Tiere", [
  ("Den Zeltplatz wählen", """- Leicht erhöht, nicht in einer Mulde (Kaltluft und Wasser sammeln sich dort).
- Nicht unter toten Ästen oder einzelnen hohen Bäumen.
- Weg von Bachbetten – nach einem Gewitter kann ein Bach in Minuten anschwellen.
- Eingang weg vom Wind, Zelt mit der schmalen Seite zum Wind.
- Wildcampen ist in der Schweiz von Kanton zu Kanton verschieden geregelt, in Naturschutzgebieten und Wildruhezonen verboten. Über der Waldgrenze für eine Nacht oft geduldet – vorher erkundigen."""),
  ("Essen und Tiere", """Füchse, Marder, Dachse, Krähen und Wildschweine finden jedes Essen.

- Essen und Abfall nie im Zelt lassen, sondern im Auto oder dicht verschlossen und hoch aufgehängt.
- Abfall jeden Abend wegräumen.
- Tiere nie füttern – sie verlieren die Scheu und werden zum Problem.
- Marder beissen gern Kabel im Motorraum an: ein Duftstoff oder ein Marderschutz hilft, MoveEye meldet sie in der Nacht."""),
  ("Wolf, Bär, Luchs", """Der Wolf ist in vielen Regionen der Schweiz zurück, vereinzelt streifen Bären aus Italien durch Graubünden, der Luchs lebt im Jura und in den Alpen. Für Menschen sind sie sehr selten gefährlich.

- Begegnung mit einem Wolf: stehen bleiben, auf sich aufmerksam machen (laut sprechen, gross machen), langsam zurückziehen. Nicht rennen, nicht füttern. Hunde an die Leine.
- Begegnung mit einem Bär: ruhig sprechen, langsam zurückweichen, Abstand geben, nie zwischen Bärin und Junge geraten. Nicht wegrennen, nicht auf Bäume klettern.
- Sichtungen melden: Wildhut des Kantons."""),
  ("Herdenschutzhunde und Kühe", """Auf Alpen schützen Herdenschutzhunde die Schafe. Ruhig bleiben, Abstand halten, die Herde umgehen, nicht auf den Hund zugehen, Velo schieben.

Mutterkühe verteidigen ihre Kälber. Nicht zwischen Kuh und Kalb, Hund an die kurze Leine – greift die Kuh an, Hund loslassen. Langsam und ruhig, mit Abstand vorbeigehen."""),
 ]),
 ("knoten", "🪢", "Knoten und Werkzeug", [
  ("Spannknoten für Zeltleinen", """Mit dem Spannknoten lässt sich eine Zeltleine nachspannen: Er lässt sich von Hand verschieben und klemmt, sobald Zug auf die Leine kommt.

Die Leine um den Hering legen. Mit dem losen Ende zwei Windungen um die gespannte Leine machen, innen in der Schlinge. Dann aussen daneben – auf der Zeltseite – einen halben Schlag in derselben Drehrichtung: noch einmal um die Leine und das Ende zwischen gespannter Leine und eigenem Seil hindurch. Festziehen.

Auf glatter oder steifer Leine kann dieser Knoten rutschen – dann eine Windung mehr machen und nach dem Spannen prüfen.

Es gibt mehrere ähnliche Varianten; gezeichnet ist die verbreitete Pfadi-Variante (auf Englisch «taut-line hitch», im Ashley-Knotenbuch Nr. 1855)."""),
  ("Palstek", """Eine feste Schlinge, die sich nicht zuzieht und sich leicht wieder öffnen lässt.

Merksatz: «Die Schlange kommt aus dem Teich, geht um den Baum herum und wieder zurück in den Teich.» Teich = kleine Schlaufe in der Leine, Schlange = loses Ende, Baum = die feste Leine.

Wichtig: Der Teich muss so liegen, dass das Stück, das zur grossen Schlinge weiterläuft, oben auf der festen Leine liegt – sonst gibt es keinen Knoten.

Der Palstek kann sich lockern, wenn kein Zug darauf ist. Zum Sichern von Menschen reicht er allein nicht."""),
  ("Mastwurf", """Zum Festmachen an einem runden Pfosten oder Ast. Mit dem Seilende: einmal um den Pfosten, schräg über die erste Windung kreuzen, noch einmal herum und das Ende unter der Schräge durchstecken.

Schnell gemacht, aber nicht besonders sicher: Bei wechselndem Zug und an eckigen Pfosten kann er rutschen oder aufgehen. Für Wichtiges mit zwei halben Schlägen um die feste Leine sichern."""),
  ("Was ins Taschenmesser gehört", """Klinge, Säge, Schere, Dosenöffner, Ahle, Pinzette. Ein Taschenmesser mit Säge ersetzt draussen viel Werkzeug. Messer immer vom Körper weg führen und nach Gebrauch schliessen."""),
 ]),
 ("nacht", "🌌", "Nachthimmel", [
  ("Das Sommerdreieck", """Im Sommer steht abends hoch im Süden ein grosses Dreieck aus drei hellen Sternen: Wega (Leier), Deneb (Schwan) und Atair (Adler). Bei dunklem Himmel zieht die Milchstrasse genau durch dieses Dreieck."""),
  ("Kassiopeia und der Grosse Wagen", """Die Kassiopeia sieht aus wie ein grosses W und liegt auf der anderen Seite des Polarsterns als der Grosse Wagen. Wenn der eine tief steht, steht der andere hoch – zusammen findet man den Polarstern immer."""),
  ("Sternschnuppen", """Mitte August (Perseiden) und Mitte Dezember (Geminiden) gibt es die meisten Sternschnuppen – in einer dunklen Nacht bis zu einer pro Minute. Am besten nach Mitternacht, liegend, ohne Lampe. Die Augen brauchen etwa 20 Minuten, bis sie sich an die Dunkelheit gewöhnt haben – rotes Licht stört sie am wenigsten."""),
  ("Die Internationale Raumstation sehen", """Die ISS sieht aus wie ein sehr heller Stern, der ohne Blinken in wenigen Minuten über den Himmel zieht. Sie ist nur in der Dämmerung zu sehen, wenn sie noch von der Sonne beschienen wird. Die Zeiten zeigen Apps und Websites der Raumfahrtagenturen."""),
 ]),
 ("abend", "📖", "Abendlektüre", [
  ("Der Drache vom Pilatus", """Man erzählt, in den Höhlen des Pilatus hätten früher Drachen gewohnt. Ein Fassbinder aus Luzern, der im Herbst Holz suchte, stürzte in eine Schlucht und landete mitten zwischen zwei Drachen. Sie taten ihm nichts – den ganzen Winter lebte er bei ihnen und leckte, wie sie, das salzige Wasser von den Felsen.

Im Frühling breiteten die Drachen ihre Flügel aus und flogen davon. Der Fassbinder hielt sich am Schwanz des letzten fest und wurde aus der Schlucht getragen. Zuhause erzählte er alles, starb aber bald darauf. Aus seinem Mantel, so heisst es, liess man ein Messgewand für die Kirche machen.

Später fand ein Bauer einen «Drachenstein», der vom Himmel gefallen sein soll – er liegt heute im Naturmuseum Luzern. (Nacherzählt nach einer alten Innerschweizer Sage.)"""),
  ("Die Teufelsbrücke", """In der Schöllenen bei Andermatt wollten die Urner eine Brücke über die wilde Reuss bauen – aber jede stürzte ein. Da erschien der Teufel und versprach eine Brücke, die hält. Sein Preis: die Seele des ersten, der darüber geht.

Die Urner willigten ein. Als die Brücke fertig war, schickten sie einen Ziegenbock als ersten hinüber. Der Teufel tobte, packte einen haushohen Stein und wollte die Brücke zerschmettern. Doch eine alte Frau ritzte ein Kreuz in den Stein, und der Teufel konnte ihn nicht mehr halten – er fiel ins Tal.

Der «Teufelsstein» liegt noch heute bei Göschenen. (Nacherzählt nach der Urner Sage.)"""),
  ("Warum Füchse in der Nacht bellen", """Wer am Waldrand zeltet, hört manchmal ein heiseres, fast schreiendes Bellen in der Nacht. Das sind Füchse. Im Winter, in der Paarungszeit, rufen sie sich über weite Strecken zu. Im Sommer hört man die Jungen, die vor dem Bau spielen und sich mit kurzen Lauten verständigen.

Füchse sind neugierig und kommen nahe an Zelte, wenn es nach Essen riecht – MoveEye sieht sie dann als kleine, warme Gestalt im Wärmebild. Gefährlich sind sie nicht; sie stehlen höchstens Schuhe oder die Wurst vom Tisch."""),
  ("Glühwürmchen", """In warmen Juninächten leuchten an Waldrändern und in Gärten kleine grüne Lichter: Glühwürmchen. Es sind Käfer; die Weibchen sitzen leuchtend im Gras, die Männchen fliegen suchend darüber. Das Licht entsteht ohne Wärme – fast ohne Energieverlust.

Künstliches Licht stört sie beim Finden ihrer Partner. Darum: Wenn ihr Glühwürmchen seht, löscht die Lampen und schaut einfach zu."""),
 ]),
]
ALMANAC.extend(ALMANAC_WEITER)


def alm_notfall_seite():
    """/almanach without the data zip (the page ALM_PAGE and all other chapters are in the zip): the chapter «Notfall» as
    a plain page without script, with the note that the rest comes back with the data file"""
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = []
    for _key, icon, name, arts in ALMANAC:
        out.append("<h1>%s %s</h1>" % (icon, esc(name)))
        for title, text in arts:
            out.append("<h2>%s</h2>" % esc(title))
            for block in text.split("\n\n"):
                rows = block.split("\n")
                if all(r.startswith("- ") for r in rows):
                    out.append("<ul>" + "".join("<li>%s</li>" % esc(r[2:]) for r in rows) + "</ul>")
                else:
                    out.append("<p>" + "<br>".join(esc(r) for r in rows) + "</p>")
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,'
            'initial-scale=1"><title>Überlebens-Almanach – Notfall</title><style>body{margin:0 auto;max-width:640px;padding:16px;'
            'background:#0e1621;color:#e8eef6;font:17px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}h1{font-size:24px}'
            'h2{font-size:19px;color:#e9a23b;margin:22px 0 4px}.n{color:#8ea0b6;font-size:14px;border:1px solid #24324a;'
            'border-radius:10px;padding:10px 12px}a{color:#58a6ff}</style></head><body>' + "".join(out[:1])
            + '<p class="n">Zusatzdaten fehlen – hier nur das Kapitel «Notfall». Die anderen Kapitel und Bilder kommen mit der '
            'Zusatzdatei zurück (Update / Reparatur: <a href="/hilfe/fehler/DATA_MISSING">Jetzt nachladen</a>).</p>'
            + "".join(out[1:]) + "</body></html>")


ALM_PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Überlebens-Almanach</title><style>
:root{--bg:#0e1621;--panel:#16212f;--line:#24324a;--txt:#e8eef6;--mut:#8ea0b6;--acc:#e9a23b;--fs:17px}
body.light{--bg:#f6f3ec;--panel:#ffffff;--line:#d9d2c3;--txt:#1d232b;--mut:#5d6773;--acc:#b86e0c}
body.night{--bg:#0a0000;--panel:#160404;--line:#3a1010;--txt:#ff6a5a;--mut:#b4453a;--acc:#ff6a5a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:var(--fs)/1.6 Georgia,"Times New Roman",serif;overflow-wrap:anywhere}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 14px;padding-top:max(10px,env(safe-area-inset-top));display:flex;gap:8px;align-items:center;flex-wrap:wrap;z-index:2}
header h1{font:700 19px system-ui,sans-serif;margin:0;flex:1 1 auto}
button,input{font:15px system-ui,sans-serif;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--txt);padding:8px 11px}
button.on{background:var(--acc);color:#111;border-color:var(--acc)}
main{max-width:720px;margin:auto;padding:14px}
.tip{border:1px solid var(--acc);border-radius:14px;padding:12px 14px;margin-bottom:14px}.tip b{font-family:system-ui,sans-serif;color:var(--acc)}
.ch{margin:18px 0 6px;font:700 15px system-ui,sans-serif;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
.it{display:block;width:100%;text-align:left;margin:4px 0;padding:11px 13px;font-size:16px}
.chs{display:grid;grid-template-columns:1fr 1fr;gap:8px}.chp{display:flex;align-items:center;gap:10px;text-align:left;padding:12px;min-height:64px;font-size:16px;line-height:1.25}
.chp i{font-style:normal;font-size:26px;flex:0 0 32px;text-align:center}.chp small{display:block;color:var(--mut);font-size:13px}
article h2{font:700 24px system-ui,sans-serif;margin:6px 0 10px}article p{margin:0 0 12px}article ul{margin:0 0 12px;padding-left:22px}article li{margin:4px 0}
.nav{display:flex;gap:8px;margin-top:18px}.nav button{flex:1}.mut{color:var(--mut);font:14px system-ui,sans-serif}
.box{border:1px solid var(--line);background:var(--panel);border-radius:14px;padding:12px 14px;margin:10px 0;font-family:system-ui,sans-serif}
.box b.h{display:block;font-size:16px;margin-bottom:4px}.box .big{font:700 25px/1.25 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.01em}
.box .mid{font:600 19px/1.3 ui-monospace,Menlo,Consolas,monospace}.box.warn{border:2px solid var(--acc)}.box.warn b.h{color:var(--acc)}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}.row a{color:var(--acc);font-size:15px}
#b-sos{font-weight:700;font-size:17px;padding:12px 16px;border:2px solid var(--acc)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font-size:15px}.kv span:nth-child(odd){color:var(--mut)}
.figs{display:grid;grid-template-columns:1fr;gap:10px;margin:12px 0}@media(min-width:680px){.figs{grid-template-columns:1fr 1fr}}
figure{margin:0;border:1px solid var(--line);background:var(--panel);border-radius:12px;padding:8px;cursor:zoom-in;min-width:0}
figure svg{display:block;width:100%;height:auto}figcaption{font:15px/1.4 system-ui,sans-serif;margin-top:6px}
figcaption{color:var(--txt)}figcaption b{color:var(--acc)}
#b-x{min-height:44px;min-width:44px}#x-tip{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:11;background:var(--panel);color:var(--txt);border:1px solid var(--acc);border-radius:12px;padding:10px 12px;font:600 15px system-ui,sans-serif}#x-tip[hidden]{display:none}
#b-back{min-height:44px;min-width:44px;font-weight:600;color:var(--acc);white-space:nowrap;padding:8px 12px}#b-back[hidden]{display:none}
figure.zoom::before{content:"✕ " attr(data-zu);position:fixed;top:max(10px,env(safe-area-inset-top));right:12px;z-index:10;font:600 15px system-ui,sans-serif;min-height:44px;display:flex;align-items:center;padding:0 14px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--txt)}
figure.zoom{position:fixed;inset:0;z-index:9;border-radius:0;overflow:auto;cursor:zoom-out;display:flex;flex-direction:column;justify-content:center;background:var(--panel)}
svg .s,svg .a,svg .t{fill:none;stroke-linecap:round;stroke-linejoin:round}svg .s{stroke:var(--txt);stroke-width:2.2}svg .a{stroke:var(--acc);stroke-width:2.2}
svg .t{stroke:var(--mut);stroke-width:1.3}svg .f{fill:var(--txt)}svg .af{fill:var(--acc)}svg .m{fill:var(--line)}svg .p{fill:var(--panel);stroke:var(--txt);stroke-width:2;stroke-linejoin:round}
svg text{font:10px system-ui,sans-serif;fill:var(--txt)}svg .tx{font-size:10px}svg .tm{fill:var(--mut);font-size:9px}svg .tb{font-weight:700;font-size:11.5px}svg .c text,svg text.c{text-anchor:middle}
svg .ko,svg .k0,svg .k1,svg .kh{fill:none;stroke-linecap:butt;stroke-linejoin:round}svg .ko{stroke:var(--txt)}svg .k0{stroke:var(--panel)}svg .k1{stroke:var(--acc)}
body.night svg .k0{stroke:#000}svg .kh{stroke:var(--mut);stroke-width:2;stroke-dasharray:4 4}svg .ke{stroke:var(--txt);stroke-width:1.6}svg .k0e{fill:var(--panel)}svg .k1e{fill:var(--acc)}
svg .ka{fill:var(--acc);stroke:var(--txt);stroke-width:1.4;stroke-linejoin:round}svg .kp,svg .kr{fill:var(--line);stroke:var(--mut);stroke-width:1.5}svg .kq{fill:none;stroke:var(--mut);stroke-width:2}
svg .kb{fill:var(--txt)}svg .kt{fill:var(--txt);font-size:10px}svg .kl{stroke:var(--mut);stroke-width:1;fill:none}
@media print{header,.nav,#b-sos,#b-sosx,#b-copy,#mw-exit,#x-tip{display:none!important}body{background:#fff!important;color:#000!important;--bg:#fff;--panel:#fff;--line:#ddd;--txt:#000;--mut:#444;--acc:#777}figure{break-inside:avoid;cursor:auto}.figs{grid-template-columns:1fr 1fr}main{max-width:none}svg .k1{stroke:#888}}
</style></head><body>
<header><button id="b-back" hidden>‹ Zurück</button><h1>📖 Überlebens-Almanach</h1><input id="q" type="search" placeholder="Suchen …" style="flex:1 1 140px">
<button id="b-home" title="Inhalt">☰</button><button id="b-big" title="Grosse Schrift">A+</button><button id="b-theme" title="Hell / Dunkel / Rotlicht (wie überall in MoveEye)">◐</button><button id="b-read" title="Vorlesen">🔊</button><button id="b-x" title="Almanach schliessen" aria-label="Almanach schliessen">✕</button></header>
<div id="x-tip" hidden></div>
<main id="m"></main>
<script>
const A = __DATA__;
const $ = id => document.getElementById(id), m = $("m");
const esc = s => String(s).replace(/[&<>"]/g, c => "&#" + c.charCodeAt(0) + ";");
const all = []; A.forEach((c, ci) => c[3].forEach((a, ai) => all.push({ci, ai, ch: c, t: a[0], x: a[1]})));
const S = {big: false}; try { Object.assign(S, JSON.parse(localStorage.getItem("mw-alm") || "{}")); } catch (e) {}
let PLUS = {bilder: [], quellen: {}, karte: false}, view = 0, timer = 0;
const jget = u => fetch(u).then(r => r.json()).catch(() => null);
function save() { try { localStorage.setItem("mw-alm", JSON.stringify({big: S.big})); } catch (e) {} }
// aufr: no own red-light switch any more - the almanac follows Hell / Dunkel / Rotlicht of MoveEye (toggleTheme, 510 / 530:
// localStorage «mw-theme» = light | dark, «mw-night» = 1 for the red light); the button here is the same switch
function step() { let th = "dark", n = "0"; try { th = localStorage.getItem("mw-theme") || "dark"; n = localStorage.getItem("mw-night") || "0"; } catch (e) {}
  return n === "1" ? "red" : th === "light" ? "light" : "dark"; }
function apply() { document.documentElement.style.setProperty("--fs", S.big ? "21px" : "17px"); const s = step();
  document.body.classList.toggle("night", s === "red"); document.body.classList.toggle("light", s === "light");
  $("b-big").classList.toggle("on", S.big); $("b-theme").textContent = {light: "☾", dark: "◉", red: "☀"}[s]; }
function body(x) { return x.split("\n\n").map(b => b.split("\n").every(l => l.startsWith("- ")) ? "<ul>" + b.split("\n").map(l => "<li>" + esc(l.slice(2)) + "</li>").join("") + "</ul>" : "<p>" + esc(b).replace(/\n/g, "<br>") + "</p>").join(""); }
function tipIdx() { const d = new Date(); return (d.getFullYear() * 400 + d.getMonth() * 31 + d.getDate()) % all.length; }
function go(h) { view++; clearTimeout(timer); window.speechSynthesis && speechSynthesis.cancel(); m.innerHTML = h; scrollTo(0, 0); return view; }
function foot() { return '<p class="mut" style="margin-top:22px">Von MoveEye, offline auf dem Gerät, nur auf Deutsch. Ersetzt keinen Erste-Hilfe-Kurs – im Notfall 112 / 144. Weiterlesen (englisch, gemeinfrei): «US Army Survival Manual FM 21-76».</p>'; }
function home(q) {
  let h = ""; window.cur = undefined;
  sicht = q ? "s" : "h"; back();
  if (!q) { const t = all[tipIdx()]; hash("");
    h += '<div class="tip"><b>🌙 Tipp des Abends</b><div style="margin-top:6px"><a href="#" onclick="show(' + all.indexOf(t) + ');return false" style="color:inherit">' + t.ch[1] + " " + esc(t.t) + "</a></div></div>";
    h += '<div class="chs">' + A.map((c, ci) => '<button class="chp" onclick="chap(' + ci + ')"><i>' + c[1] + "</i><span>" + esc(c[2]) + "<small>" + c[3].length + " Artikel</small></span></button>").join("") + "</div>";
  } else {
    A.forEach((c, ci) => { const items = all.filter(a => a.ci === ci && (a.t + " " + a.x).toLowerCase().includes(q));
      if (!items.length) return; h += '<div class="ch">' + c[1] + " " + esc(c[2]) + "</div>";
      items.forEach(a => { h += '<button class="it" onclick="show(' + all.indexOf(a) + ')">' + esc(a.t) + "</button>"; }); });
    if (!h) h = '<p class="mut">Nichts gefunden.</p>';
  }
  go(h + foot());
}
function chap(ci) {
  const c = A[ci]; hash("c" + ci); window.cur = undefined; sicht = "c"; back();
  let h = '<div class="ch">' + c[1] + " " + esc(c[2]) + '</div><div id="live"></div>';
  all.forEach((a, i) => { if (a.ci === ci) h += '<button class="it" onclick="show(' + i + ')">' + esc(a.t) + (PLUS.bilder.includes(a.t) ? ' <span class="mut">· mit Bildern</span>' : "") + "</button>"; });
  if (PLUS.quellen[c[0]]) h += '<p class="mut" style="margin-top:14px">' + esc(PLUS.quellen[c[0]]) + "</p>";
  h += '<div class="nav"><button onclick="home(\'\')">☰ Inhalt</button></div>';
  const v = go(h);
  if (c[0] === "notfall") live("ort", v); else if (c[0] === "wetter") live("wetter", v); else if (c[0] === "nacht") live("nacht", v);
}
function show(i) {
  const a = all[i]; hash("a" + i); sicht = "a"; back();
  const v = go('<div class="mut"><a href="#" onclick="chap(' + a.ci + ');return false" style="color:inherit">' + a.ch[1] + " " + esc(a.ch[2]) + "</a></div><article><h2>" + esc(a.t) + "</h2>" +
    (a.ch[0] === "essbar" ? '<div class="box warn" id="warn"><b class="h">⚠ Nie nur nach diesem Almanach oder einer App essen</b>Im Zweifel nicht essen. Vergiftung: Tox Info Suisse <b>145</b> · Notfall <b>144</b>.</div>' : "") +
    body(a.x) + '<div id="figs"></div></article>' + (PLUS.quellen[a.t] ? '<p class="mut" id="src">' + esc(PLUS.quellen[a.t]) + "</p>" : "") +
    (a.ch[0] === "spuren" ? '<p class="mut"><a href="/recordings" style="color:var(--acc)">📼 Was hat meine Kamera gesehen? Zu den Aufnahmen</a></p>' : "") +
    (a.ch[0] === "essbar" ? '<p class="mut"><a href="/tausch" style="color:var(--acc)">🌿 Bestimmen (im Datentausch) – ein Hinweis zum Nachschlagen, keine Freigabe zum Essen</a></p>' : "") +
    '<div class="nav"><button onclick="show(' + Math.max(0, i - 1) + ')">‹ Zurück</button><button onclick="chap(' + a.ci + ')">☰ Kapitel</button><button onclick="show(' + Math.min(all.length - 1, i + 1) + ')">Weiter ›</button></div>');
  window.cur = i;
  if (PLUS.bilder.includes(a.t)) jget("/almanach/bilder?t=" + encodeURIComponent(a.t)).then(j => { if (v !== view || !j || !j.f) return;
    $("figs").innerHTML = '<div class="figs">' + j.f.map(f => '<figure data-zu="' + esc(PLUS.t_zu || "Schliessen") + '" onclick="this.classList.toggle(\'zoom\')">' + f.svg +
      (f.cap ? "<figcaption>" + (f.n ? "<b>" + f.n + ".</b> " : "") + esc(f.cap) + "</figcaption>" : "") + "</figure>").join("") + "</div>"; fit(); });
}
// the labels of the pictures on any font (a phone, another computer): the pictures are drawn with room for a font 20 % wider than
// measured; whatever still reaches over the edge of its picture is moved back in, and a label wider than the picture is pressed
function fit() { document.querySelectorAll("#figs svg text").forEach(x => { try { const vb = x.ownerSVGElement.viewBox.baseVal; let b = x.getBBox(), d = 0;
    if (b.width > vb.width - 2) { x.setAttribute("textLength", vb.width - 2); x.setAttribute("lengthAdjust", "spacingAndGlyphs"); b = x.getBBox(); }
    if (b.x < 1) d = 1 - b.x; else if (b.x + b.width > vb.width - 1) d = vb.width - 1 - b.x - b.width;
    if (d) x.setAttribute("transform", "translate(" + d.toFixed(1) + ",0)"); } catch (e) {} }); }
function copy(t, b) { const done = () => { b.textContent = "Kopiert ✓"; setTimeout(() => { b.textContent = "Kopieren"; }, 2000); };
  const old = () => { const x = document.createElement("textarea"); x.value = t; document.body.appendChild(x); x.select(); try { document.execCommand("copy"); done(); } catch (e) {} x.remove(); };
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(done, old); else old(); }
function mmss(s) { return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
function ortBox(d) { const o = d.ort || {}, s = d.sos || {}; let h = '<div class="box" id="ort"><b class="h">📍 Mein Standort für den Notruf</b>';
  if (o.ok) { const txt = (o.lv95 ? "LV95 " + o.lv95 + " · " : "") + "WGS84 " + o.wgs;
    if (o.lv95) h += '<div class="big">' + esc(o.lv95) + '</div><div class="mut">Schweizer Koordinaten (LV95: Ost / Nord)</div>';
    h += '<div class="' + (o.lv95 ? "mid" : "big") + '">' + esc(o.wgs) + '</div><div class="mut">WGS84 (Breite, Länge) · ' + esc(o.dms) + "</div>";
    h += '<div class="mut">' + (o.name ? esc(o.name) + " · " : "") + "Standort von MoveEye, " + ({module: "vom GPS-Modul", phone: "vom Handy übernommen", fixed: "aus den Einstellungen"}[o.src] || "gespeichert") +
      (o.acc ? " (± " + o.acc + " m)" : "") + '. Bist du woanders, gilt dein eigener Standort.</div><div class="row"><button id="b-copy">Kopieren</button>' +
      (PLUS.karte ? '<a href="/karte">🗺 Offline-Karte</a>' : "") + "</div>";
    setTimeout(() => { const b = $("b-copy"); if (b) b.onclick = () => copy(txt, b); }, 0);
  } else if (o.fern) h += '<div class="mut" style="font-size:15px">Der gespeicherte Standort wird nur im WLAN von MoveEye angezeigt (oder auf einem angemeldeten Gerät).</div>';
  else h += '<div class="mut" style="font-size:15px">Kein Standort gespeichert – so setzt du ihn: MoveEye-Seite auf dem Handy über https öffnen und den Standort erlauben, oder in den Einstellungen Breitengrad und Längengrad eintragen.' +
      (PLUS.karte ? ' <a href="/karte" style="color:var(--acc)">🗺 Offline-Karte</a>' : "") + "</div>";
  h += '</div><div class="box" id="sos"><b class="h">🆘 SOS mit der Lampe</b>';
  if (!s.lampe) h += '<div class="mut" style="font-size:15px">keine Lampe angeschlossen – MoveEye kann hier nicht blinken. Alpines Notsignal: sechsmal pro Minute ein Zeichen (blinken, pfeifen, rufen), eine Minute warten, wiederholen.</div>';
  else if (s.on) h += '<div class="mut" style="font-size:15px">MoveEye blinkt · · · — — — · · · und hört in ' + mmss(s.rest) + ' von selbst auf.' + (s.alarm ? " Gerade hat das Alarm-Licht Vorrang." : "") + '</div><div class="row"><button id="b-sosx" class="on">■ Stopp</button></div>';
  else h += '<div class="mut" style="font-size:15px">MoveEye blinkt mit dem weissen Licht · · · — — — · · · (SOS), 5 Minuten lang. Der Besitzer bekommt eine Nachricht. Nur im Notfall.</div><div class="row"><button id="b-sos">🆘 SOS-Lampe starten</button><span class="mut" id="sosmsg"></span></div>';
  return h + "</div>"; }
function sos(act) { fetch("/almanach/sos", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: act})}).then(r => r.json()).then(j => {
    live("ort", view, j && !j.ok ? j.msg : ""); }).catch(() => {}); }
function wetterBox(d) { const w = d.wetter || {};
  if (!w.ok) return '<p class="mut" id="wetter">Kein Luftdruck-Sensor (BME280) angeschlossen – hier stünden sonst Luftdruck und Trend. Die Wolken lesen hilft auch.</p>';
  let sp = ""; const k = w.kurve || [];
  if (k.length > 2) { const lo = Math.min(...k), hi = Math.max(...k), r = Math.max(1, hi - lo);
    sp = '<svg viewBox="0 0 240 46" style="width:100%;height:46px;margin-top:6px"><polyline class="a" points="' + k.map((p, i) => (4 + 232 * i / (k.length - 1)).toFixed(1) + "," + (40 - 34 * (p - lo) / r).toFixed(1)).join(" ") + '"/></svg><div class="mut">Verlauf der letzten ' + String(w.stunden).replace(".", ",") + " Stunden (" + lo.toFixed(1) + "–" + hi.toFixed(1) + " hPa)</div>"; }
  const f = v => v == null ? "–" : (v > 0 ? "+" : "") + String(v).replace(".", ",") + " hPa";
  return '<div class="box' + (w.stufe ? " warn" : "") + '" id="wetter"><b class="h">' + (w.stufe ? "⚠ " : "🌡 ") + 'Luftdruck jetzt</b><div class="big">' + String(w.p).replace(".", ",") + ' hPa</div>' + sp +
    '<div class="kv" style="margin-top:6px"><span>letzte Stunde</span><span>' + f(w.h1) + "</span><span>letzte 3 Stunden</span><span>" + f(w.h3) + "</span>" + (w.t != null ? "<span>Temperatur</span><span>" + String(w.t).replace(".", ",") + " °C</span>" : "") + "</div>" +
    '<p style="margin:8px 0 4px;font-size:16px">' + esc(w.text) + '</p><div class="mut">Erfahrungswerte, keine amtliche Regel: Ein Abfall von mehr als etwa 1 hPa pro Stunde gilt hier als schnell, mehr als 2 hPa pro Stunde als sehr schnell. Das ist ein Hinweis, keine Vorhersage. Sommergewitter kommen oft ohne Vorwarnung im Luftdruck – immer auch den Himmel beobachten. Gemessen am Standort von MoveEye (' + esc(w.src) + ").</div></div>"; }
function nachtBox(d) { const n = d.nacht || {}; if (!n.datum) return "";
  const r = (a, b) => b ? "<span>" + a + "</span><span>" + esc(b) + "</span>" : "";
  return '<div class="box" id="nacht"><b class="h">🌙 Heute Nacht · ' + esc(n.datum) + '</b><div class="kv">' + r("Sonnenuntergang", n.sonne_unter) + r("ganz dunkel ab", n.nacht_ab || "wird nicht ganz dunkel") +
    r("ganz dunkel bis", n.nacht_bis) + r("Sonnenaufgang", n.sonne_auf) + r("Mond", n.mond.icon + " " + n.mond.name + ", " + n.mond.hell + " % beleuchtet") + r("Mondaufgang", n.mond_auf || "heute keiner") + r("Monduntergang", n.mond_unter || "heute keiner") + "</div>" +
    (n.sterne && n.sterne.length ? '<p style="margin:8px 0 4px;font-size:15px">Um 23 Uhr zu sehen: ' + n.sterne.map(s => esc(s.name) + " (im " + s.wo + ")").join(", ") + ".</p>" : "") +
    '<div class="mut">' + (n.mond.hell < 30 ? "Wenig Mondlicht – gut für Sterne und Sternschnuppen. " : n.mond.hell > 70 ? "Heller Mond – schwache Sterne und die Milchstrasse sind schlecht zu sehen. " : "") +
    (n.ort_ok ? "Gerechnet für den Standort von MoveEye." : "Kein Standort gespeichert: gerechnet für die Werkseinstellung (Zürich).") + "</div></div>"; }
function live(w, v, msg) { jget("/almanach/live?w=" + w).then(d => { const el = $("live"); if (v !== view || !el || !d) return;
    el.innerHTML = w === "ort" ? ortBox(d) : w === "wetter" ? wetterBox(d) : nachtBox(d);
    if (w === "ort") { const a = $("b-sos"), x = $("b-sosx"); if (a) a.onclick = () => sos("start"); if (x) x.onclick = () => sos("stop");
      if (msg && $("sosmsg")) $("sosmsg").textContent = msg;
      if (d.sos && d.sos.on) timer = setTimeout(() => live(w, v), 2000); }
    else if (w === "wetter" && d.wetter && d.wetter.ok) timer = setTimeout(() => live(w, v), 60000); }); }
$("q").oninput = () => home($("q").value.trim().toLowerCase());
$("b-home").onclick = () => { $("q").value = ""; home(""); };
$("b-big").onclick = () => { S.big = !S.big; save(); apply(); };
$("b-theme").onclick = () => { const n = {light: "dark", dark: "red", red: "light"}[step()], th = n === "light" ? "light" : "dark";
  try { localStorage.setItem("mw-theme", th); localStorage.setItem("mw-night", n === "red" ? "1" : "0"); } catch (e) {}
  fetch("/api/ui", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({set: {"mw-theme": th}})}).catch(() => {});   // like the other pages (guests: refused, no matter)
  apply(); };
addEventListener("storage", e => { if (e.key === "mw-theme" || e.key === "mw-night") apply(); });   // switched on another page of MoveEye
$("b-read").onclick = () => { if (!window.speechSynthesis) return; if (window.MW_VOICE && window.MW_VOICE !== "on") return;    if (speechSynthesis.speaking) { speechSynthesis.cancel(); return; }
  const a = all[window.cur ?? tipIdx()]; const u = new SpeechSynthesisUtterance(a.t + ". " + a.x.replace(/^- /gm, "")); u.lang = "de-CH"; u.rate = 0.95; speechSynthesis.speak(u); };
// ---- the way back (Besitzer: «es fehlt noch eine Taste um zurückzukommen»): one button, always in the head of the page, that goes
// to the logical parent - article -> chapter -> contents -> MoveEye «Mehr» - and never into an empty history (home-screen app,
// page opened directly). The own «✕ Zurück» of 340 is not used here (window.__mwExit): it steps through the history, and inside
// the almanac that only changed the address. Guests without a login have nothing above the contents: no button there.
window.__mwExit = true;
let sicht = "h", stumm = false;
function hash(h) { if (location.hash.replace(/^#/, "") !== h) { stumm = true; location.hash = h; setTimeout(() => { stumm = false; }, 0); } }
function back() { const b = $("b-back"); b.hidden = sicht === "h" && !PLUS.heim;
  b.textContent = "‹ " + (sicht === "h" ? (PLUS.t_mehr || "Mehr") : (PLUS.t_zurueck || "Zurück")); }
$("b-back").onclick = () => { const z = document.querySelector("figure.zoom"); if (z) { z.classList.remove("zoom"); return; }
  if (sicht === "a" && all[window.cur]) chap(all[window.cur].ci); else if (sicht === "c" || sicht === "s") { $("q").value = ""; home(""); }
  else if (PLUS.heim) location.href = PLUS.heim; };
// «✕» = leave the almanac with one tap, from every view: to MoveEye «Mehr» for a known device. A guest behind a password has no
// page of MoveEye to go to (no guest page links here, and MoveEye sends no referrer): there the tab is closed if the browser
// allows it, and otherwise a line says what to do - as the «✕ Zurück» of 340 does on the other guest pages.
$("b-x").onclick = () => { if (PLUS.heim) { location.href = PLUS.heim; return; }
  try { window.close(); } catch (e) {}
  setTimeout(() => { const t = $("x-tip"); t.textContent = PLUS.t_tab || "Diesen Tab schliessen oder die App wegwischen."; t.hidden = false; setTimeout(() => { t.hidden = true; }, 5000); }, 300); };
addEventListener("hashchange", () => { if (!stumm) start(); });     // the back gesture of the phone / the browser moves through the same views
function start() { const hm = /^#([ac])(\d+)$/.exec(location.hash);
  if (hm && hm[1] === "a" && all[+hm[2]]) show(+hm[2]); else if (hm && hm[1] === "c" && A[+hm[2]]) chap(+hm[2]); else home(""); }
apply(); jget("/almanach/plus").then(j => { if (j && j.ok) PLUS = j; start(); back(); });
</script></body></html>"""


def almanac_tip():
    arts = [(c[1], c[2], a[0], a[1]) for c in ALMANAC for a in c[3]]
    d = datetime.now()
    i = (d.year * 400 + (d.month - 1) * 31 + d.day) % len(arts)
    ic, ch, t, x = arts[i]
    first = " ".join(("• " + l[2:]) if l.startswith("- ") else l for l in x.split("\n\n")[0].split("\n"))
    return {"i": i, "icon": ic, "chapter": ch, "title": t, "text": first[:400]}


