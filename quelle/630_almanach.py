#@ Motion Watch – Teil 630: Extras: Überlebens-Almanach. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ---- Überlebens-Almanach (2.95.54): tips and tricks for camping in Switzerland, to look up or to read in the evening;
# offline on the device (/almanach/, also for guests in the same Wi-Fi), «Tipp des Abends» on the TV view. ----
# Überlebens-Almanach für MoveEye: Kapitel -> Artikel. Text: Absätze mit Leerzeile, Listenpunkte mit "- ".
ALMANAC = [
 ("notfall", "🆘", "Notfall", [
  ("Notrufnummern Schweiz", """Merk dir diese Nummern – Notrufe sind kostenlos und gehen auch ohne Guthaben:

- 112 – Euro-Notruf (verbindet überall in Europa)
- 144 – Sanität / Rettungsdienst
- 117 – Polizei
- 118 – Feuerwehr
- 1414 – Rega (Rettungshelikopter), oder die Rega-App: sie schickt deinen Standort mit
- 145 – Tox Info Suisse (Vergiftungen, auch Pilze, Pflanzen, Schlangenbisse)

Die 112 nimmt jedes erreichbare Mobilfunknetz, auch ein fremdes. Kommst du mit 1414 oder der Rega-App nicht durch, wähle 112.

Am Telefon: Wer ruft an? Wo genau (Koordinaten – siehe «Mein Standort» oben im Kapitel –, markante Punkte)? Was ist passiert? Wie viele Verletzte? Dann nicht auflegen, bis die Zentrale es sagt."""),
  ("Kein Netz – was jetzt?", """Kein Empfang heisst nicht, dass kein Notruf geht: 112 nimmt jedes verfügbare Netz, auch das eines anderen Anbieters.

- Ein paar Meter höher oder auf eine Kuppe steigen hilft oft.
- Eine SMS geht manchmal durch, wenn ein Anruf scheitert.
- Akku sparen: Flugmodus, nur alle 15 Minuten kurz einschalten.
- Ohne jedes Netz: alpines Notsignal (siehe «Notsignale»), auffällige Kleidung ausbreiten, beim Verletzten bleiben, wenn jemand anderes Hilfe holt."""),
  ("Notsignale", """Alpines Notsignal: sechsmal pro Minute ein Zeichen (Pfiff, Lichtblitz, Rufen), dann eine Minute Pause, wiederholen. Die Antwort: dreimal pro Minute.

Für den Helikopter (Rega): Beide Arme schräg hoch, wie ein Y = «Ja, wir brauchen Hilfe». Ein Arm hoch, einer schräg runter = «Nein, wir brauchen nichts». Nicht winken – das verwechselt der Pilot.

Nachts: Taschenlampe oder Handy-Licht in Richtung Helikopter, aber nie direkt ins Cockpit blenden, wenn er landet."""),
  ("Die stabile Seitenlage", """Für Bewusstlose, die normal atmen:

- Neben die Person knien, den nahen Arm im rechten Winkel nach oben legen.
- Den fernen Arm über die Brust holen, Handrücken an die Wange.
- Das ferne Knie anwinkeln und die Person daran zu dir drehen.
- Kopf leicht nach hinten neigen, Mund ist der tiefste Punkt.
- Notruf 144, Atmung immer wieder kontrollieren, warm halten.

Atmet sie nicht normal: sofort 144 und mit Herzdruckmassage beginnen (30 Mal drücken, Brustmitte, 5–6 cm tief, etwa 2 Mal pro Sekunde). Ein Defibrillator (AED) – oft bei Campingplätzen, Bergbahnen, Gemeindehäusern – führt dich mit Sprache durch alles."""),
  ("Blutungen", """Stark blutende Wunden: sofort Druck darauf – mit einem sauberen Tuch, notfalls mit der Hand. Den Arm oder das Bein hochhalten. Einen Druckverband anlegen: sterile Auflage auf die Wunde, ein Polster darauf (zum Beispiel eine ungeöffnete Verbandrolle), fest umwickeln. Die Finger oder Zehen dahinter müssen warm und rosig bleiben. Blutet es durch, einen zweiten Verband darüber wickeln – den ersten nicht entfernen.

Hört es nicht auf: 144. Zwischen Herz und Wunde mit der Faust auf die Arterie drücken. Einen Gegenstand, der in der Wunde steckt, nie herausziehen – drumherum polstern."""),
  ("Verbrennungen", """Sofort 10–20 Minuten mit lauwarmem (nicht eiskaltem) Wasser kühlen – bei Kindern und grossen Flächen kürzer, sonst kühlen sie aus. Kleidung, die nicht klebt, und Schmuck entfernen. Nie Mehl, Butter, Zahnpasta.

Locker und sauber abdecken (Alufolie aus dem Erste-Hilfe-Set oder sauberes Tuch). Zum Arzt: Blasen grösser als die Handfläche der verletzten Person, Gesicht, Hände, Gelenke, Kinder, oder wenn die Haut weiss oder ledrig ist."""),
  ("Erste-Hilfe-Set für das Camping", """- Pflaster in mehreren Grössen, sterile Kompressen, zwei Gazebinden, elastische Binde
- Desinfektionsmittel, Zeckenzange oder -karte, Pinzette, Schere
- Rettungsdecke, Einweghandschuhe, Dreiecktuch
- Blasenpflaster, Wundsalbe, Sonnencreme, Insektenschutz
- Schmerzmittel und eigene Medikamente (genug für ein paar Tage mehr)
- Stirnlampe mit vollen Akkus, Trillerpfeife

Einmal im Jahr durchsehen: Ablaufdaten, verbrauchte Sachen nachfüllen."""),
 ]),
 ("wetter", "⛈", "Wetter lesen", [
  ("Gewitter: die 30/30-Regel", """Zähle die Sekunden zwischen Blitz und Donner. Durch 3 geteilt ergibt das ungefähr die Entfernung in Kilometern. Unter 30 Sekunden (10 km) bist du in Reichweite – jetzt Schutz suchen. Erst 30 Minuten nach dem letzten Donner wieder hinaus.

Sicher: Auto (geschlossen), feste Gebäude. Unsicher: Zelte, Unterstände, einzelne Bäume, Gipfel, Grate, Wasser, Metallzäune."""),
  ("Draussen vom Gewitter überrascht", """- Weg von Gipfeln, Graten, einzelnen Bäumen und Wasser. Eine Mulde oder ein dichter Wald mit gleich hohen Bäumen ist besser.
- Füsse zusammen, in die Hocke, Kopf einziehen, möglichst wenig Boden berühren (Isomatte oder Rucksack darunter).
- Mindestens 3 m Abstand zu anderen, damit nicht alle getroffen werden.
- Stöcke, Pickel und Metall weglegen.
- Im Zelt: auf die Isomatte kauern, nicht die Zeltstangen berühren."""),
  ("Wolken als Wettervorhersage", """- Schäfchenwolken (Altocumulus) am Morgen: oft Wetterumschwung innert 12–24 Stunden.
- Quellwolken, die schon am Vormittag hoch in die Höhe wachsen: Gewittergefahr am Nachmittag.
- Ein Amboss oben auf einer Wolke (Cumulonimbus): das Gewitter ist da oder kommt.
- Federwolken (Cirren), die dichter werden und in einen Schleier übergehen: Regen in 1–2 Tagen.
- Ein Hof um Sonne oder Mond: Feuchtigkeit kommt, oft Regen.
- Morgenrot mit schnell aufziehenden Wolken: unbeständig. Klarer Abendhimmel: meist ein schöner nächster Tag."""),
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
  ("Unterkühlung", """Anzeichen: Zittern, kalte Haut, ungeschickte Bewegungen, Verwirrung. Hört das Zittern auf, wird es gefährlich.

- Aus Wind und Nässe, nasse Kleider ausziehen, trockene an, in Schlafsack oder Rettungsdecke (silberne Seite nach innen) wickeln, Mütze.
- Warme, süsse Getränke, wenn die Person wach ist und schlucken kann – nie Alkohol.
- Stark unterkühlte Menschen nicht reiben oder herumbewegen, vorsichtig hinlegen. Notruf 144."""),
  ("Hitze und Sonne", """Sonnenstich: roter, heisser Kopf, Kopfschmerzen, Übelkeit. Hitzschlag: heisse, oft trockene Haut, Verwirrung, Bewusstlosigkeit – ein Notfall (144).

- In den Schatten, Kleider öffnen, mit nassen Tüchern kühlen, Luft zufächeln.
- Trinken, wenn die Person wach ist.
- Vorbeugen: Hut, viel trinken, in der Mittagshitze Pause. In der Höhe ist die Sonne viel stärker – Sonnenschutz auch bei Wolken und auf dem Wasser."""),
  ("Schlangen in der Schweiz", """In der Schweiz gibt es zwei Giftschlangen: die Aspisviper (vor allem Jura, Alpensüdseite, Wallis) und die Kreuzotter (Alpen, höhere Lagen). Beide sind scheu und beissen nur, wenn man sie bedrängt oder darauftritt. Die anderen einheimischen Schlangen – etwa Ringelnatter, Würfelnatter und Schlingnatter – sind harmlos, und die Blindschleiche ist eine beinlose Echse.

Vipern haben senkrechte Pupillen und einen kurzen, gedrungenen Körper, Nattern runde Pupillen. Aber so nah geht man nicht heran: Im Zweifel Abstand halten und der Schlange den Weg frei lassen. Alle Schlangen sind in der Schweiz geschützt.

Nach einem Biss: Ruhe bewahren, nicht aussaugen, nicht abbinden, nicht schneiden. Schmuck entfernen, das Glied ruhig halten. 145 (Tox Info) oder 144 anrufen. Die meisten Bisse sind nicht lebensgefährlich, sollten aber ärztlich angeschaut werden.

Auf Wegen bleiben, festes Schuhwerk, beim Holzsammeln nicht blind unter Steine greifen."""),
  ("Wespen und Bienen", """- Nicht wild schlagen, ruhig weggehen.
- Getränke abdecken, aus Flaschen mit Strohhalm trinken – ein Stich in den Mund kann gefährlich anschwellen.
- Stich: Bienenstachel wegkratzen (nicht drücken), kühlen.
- Notfall (144): Schwellung im Mund oder Hals, Atemnot, Schwindel, Ausschlag am ganzen Körper. Allergiker immer das eigene Notfallset dabeihaben."""),
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
  ("Spannknoten für Zeltleinen", """Mit dem Spannknoten (Rollknoten) lässt sich eine Leine nachspannen: Die Leine um den Hering legen, mit dem losen Ende zweimal um die gespannte Leine wickeln (Richtung Hering), dann einmal ausserhalb davon eine halbe Schlinge. Der Knoten lässt sich schieben und hält unter Zug."""),
  ("Palstek", """Eine feste Schlinge, die sich nicht zuzieht und sich trotzdem leicht wieder öffnen lässt – der wichtigste Knoten draussen.

Merksatz: «Die Schlange kommt aus dem Teich, geht um den Baum herum und wieder zurück in den Teich.» Teich = kleine Schlinge in der Leine, Schlange = loses Ende, Baum = die feste Leine.

Wichtig: Der Teich muss so liegen, dass das Stück, das zur grossen Schlinge führt, oben auf der festen Leine liegt – sonst fällt der Knoten auseinander. Das lose Ende soll mindestens eine Handbreit herausschauen."""),
  ("Mastwurf", """Zum Festmachen an einem Pfosten oder Ast. Mit dem Seilende: einmal um den Pfosten, schräg über die erste Windung kreuzen, noch einmal herum und das Ende unter der Schräge durchstecken. Am offenen Pfosten geht es schneller: zwei Schlingen nebeneinander, die zweite über die erste legen, über den Pfosten stülpen und ziehen. Schnell gemacht, hält aber vor allem unter Zug – für Wichtiges mit einem halben Schlag sichern."""),
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


ALM_PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Überlebens-Almanach</title><style>
:root{--bg:#0e1621;--panel:#16212f;--line:#24324a;--txt:#e8eef6;--mut:#8ea0b6;--acc:#e9a23b;--fs:17px}
body.light{--bg:#f6f3ec;--panel:#ffffff;--line:#d9d2c3;--txt:#1d232b;--mut:#5d6773;--acc:#b86e0c}
body.night{--bg:#0a0000;--panel:#160404;--line:#3a1010;--txt:#ff6a5a;--mut:#b4453a;--acc:#ff6a5a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:var(--fs)/1.6 Georgia,"Times New Roman",serif;overflow-wrap:anywhere}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;z-index:2}
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
.figs{display:grid;grid-template-columns:1fr;gap:10px;margin:12px 0}.figs.st{grid-template-columns:1fr 1fr}
figure{margin:0;border:1px solid var(--line);background:var(--panel);border-radius:12px;padding:8px;cursor:zoom-in;min-width:0}
figure svg{display:block;width:100%;height:auto}figcaption{font:14px/1.35 system-ui,sans-serif;color:var(--mut);margin-top:6px}
figcaption b{color:var(--acc)}figure.last{grid-column:1/-1}
figure.zoom{position:fixed;inset:0;z-index:9;border-radius:0;overflow:auto;cursor:zoom-out;display:flex;flex-direction:column;justify-content:center;background:var(--panel)}
svg .s,svg .a,svg .t{fill:none;stroke-linecap:round;stroke-linejoin:round}svg .s{stroke:var(--txt);stroke-width:2.2}svg .a{stroke:var(--acc);stroke-width:2.2}
svg .t{stroke:var(--mut);stroke-width:1.3}svg .f{fill:var(--txt)}svg .af{fill:var(--acc)}svg .m{fill:var(--line)}svg .p{fill:var(--panel);stroke:var(--txt);stroke-width:2;stroke-linejoin:round}
svg text{font:10px system-ui,sans-serif;fill:var(--txt)}svg .tx{font-size:10px}svg .tm{fill:var(--mut);font-size:9px}svg .tb{font-weight:700;font-size:11.5px}svg .c text,svg text.c{text-anchor:middle}
svg .k0,svg .k1,svg .k1i{fill:none;stroke-linecap:round;stroke-linejoin:round}svg .k0{stroke:var(--txt);stroke-width:6}svg .k1{stroke:var(--acc);stroke-width:6}
svg .k1i{stroke:var(--panel);stroke-width:2.2}svg .ka{fill:var(--acc)}svg .kp,svg .kr{fill:var(--line);stroke:var(--mut);stroke-width:1.5}svg .kq{fill:none;stroke:var(--mut);stroke-width:1.5}
svg .kb{fill:var(--txt)}svg .kt{fill:var(--mut);font-size:11px}
@media print{header,.nav,#b-sos,#b-sosx,#b-copy{display:none!important}body{background:#fff!important;color:#000!important;--bg:#fff;--panel:#fff;--line:#bbb;--txt:#000;--mut:#444;--acc:#000}figure{break-inside:avoid}main{max-width:none}}
</style></head><body>
<header><h1>📖 Überlebens-Almanach</h1><input id="q" type="search" placeholder="Suchen …" style="flex:1 1 140px">
<button id="b-home" title="Inhalt">☰</button><button id="b-big" title="Grosse Schrift">A+</button><button id="b-theme" title="Hell / Dunkel / Rotlicht (wie überall in MoveEye)">◐</button><button id="b-read" title="Vorlesen">🔊</button></header>
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
  if (!q) { const t = all[tipIdx()]; location.hash = "";
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
  const c = A[ci]; location.hash = "c" + ci; window.cur = undefined;
  let h = '<div class="ch">' + c[1] + " " + esc(c[2]) + '</div><div id="live"></div>';
  all.forEach((a, i) => { if (a.ci === ci) h += '<button class="it" onclick="show(' + i + ')">' + esc(a.t) + (PLUS.bilder.includes(a.t) ? ' <span class="mut">· mit Bildern</span>' : "") + "</button>"; });
  if (PLUS.quellen[c[0]]) h += '<p class="mut" style="margin-top:14px">' + esc(PLUS.quellen[c[0]]) + "</p>";
  h += '<div class="nav"><button onclick="home(\'\')">☰ Inhalt</button></div>';
  const v = go(h);
  if (c[0] === "notfall") live("ort", v); else if (c[0] === "wetter") live("wetter", v); else if (c[0] === "nacht") live("nacht", v);
}
function show(i) {
  const a = all[i]; location.hash = "a" + i;
  const v = go('<div class="mut"><a href="#" onclick="chap(' + a.ci + ');return false" style="color:inherit">' + a.ch[1] + " " + esc(a.ch[2]) + "</a></div><article><h2>" + esc(a.t) + "</h2>" + body(a.x) + '<div id="figs"></div></article>' +
    (a.ch[0] === "spuren" ? '<p class="mut"><a href="/recordings" style="color:var(--acc)">📼 Was hat meine Kamera gesehen? Zu den Aufnahmen</a></p>' : "") +
    (a.ch[0] === "essbar" ? '<div class="box warn"><b class="h">⚠ Nie nur nach diesem Almanach oder einer App essen</b>Im Zweifel nicht essen. Vergiftung: Tox Info Suisse <b>145</b> · Notfall <b>144</b>.<div class="row"><a href="/tausch">🌿 Bestimmen (im Datentausch)</a></div></div>' : "") +
    '<div class="nav"><button onclick="show(' + Math.max(0, i - 1) + ')">‹ Zurück</button><button onclick="chap(' + a.ci + ')">☰ Kapitel</button><button onclick="show(' + Math.min(all.length - 1, i + 1) + ')">Weiter ›</button></div>');
  window.cur = i;
  if (PLUS.bilder.includes(a.t)) jget("/almanach/bilder?t=" + encodeURIComponent(a.t)).then(j => { if (v !== view || !j || !j.f) return;
    const st = j.f.some(f => f.n);
    $("figs").innerHTML = '<div class="figs' + (st ? " st" : "") + '">' + j.f.map((f, k) => '<figure' + (st && k === j.f.length - 1 ? ' class="last"' : "") + ' onclick="this.classList.toggle(\'zoom\')">' + f.svg +
      (f.cap ? "<figcaption>" + (f.n ? "<b>" + f.n + ".</b> " : "") + esc(f.cap) + "</figcaption>" : "") + "</figure>").join("") + "</div>"; });
}
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
  } else h += '<div class="mut" style="font-size:15px">Kein Standort gespeichert – so setzt du ihn: MoveEye-Seite auf dem Handy über https öffnen und den Standort erlauben, oder in den Einstellungen Breitengrad und Längengrad eintragen.' +
      (PLUS.karte ? ' <a href="/karte" style="color:var(--acc)">🗺 Offline-Karte</a>' : "") + "</div>";
  h += '</div><div class="box" id="sos"><b class="h">🆘 SOS mit der Lampe</b>';
  if (!s.lampe) h += '<div class="mut" style="font-size:15px">keine Lampe angeschlossen – MoveEye kann hier nicht blinken. Alpines Notsignal: sechsmal pro Minute ein Zeichen mit Taschenlampe oder Pfeife.</div>';
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
    '<p style="margin:8px 0 4px;font-size:16px">' + esc(w.text) + '</p><div class="mut">Faustregel: Fällt der Luftdruck um mehr als etwa 1 hPa pro Stunde, zieht meist eine Front auf; bei mehr als 2 hPa pro Stunde kann Sturm oder ein Gewitter folgen. Sommergewitter kommen aber oft ohne Vorwarnung im Luftdruck – immer auch den Himmel beobachten. Gemessen am Standort von MoveEye (' + esc(w.src) + ").</div></div>"; }
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
function start() { const hm = /^#([ac])(\d+)$/.exec(location.hash);
  if (hm && hm[1] === "a" && all[+hm[2]]) show(+hm[2]); else if (hm && hm[1] === "c" && A[+hm[2]]) chap(+hm[2]); else home(""); }
apply(); jget("/almanach/plus").then(j => { if (j && j.ok) PLUS = j; start(); });
</script></body></html>"""


def almanac_tip():
    arts = [(c[1], c[2], a[0], a[1]) for c in ALMANAC for a in c[3]]
    d = datetime.now()
    i = (d.year * 400 + (d.month - 1) * 31 + d.day) % len(arts)
    ic, ch, t, x = arts[i]
    first = " ".join(("• " + l[2:]) if l.startswith("- ") else l for l in x.split("\n\n")[0].split("\n"))
    return {"i": i, "icon": ic, "chapter": ch, "title": t, "text": first[:400]}


