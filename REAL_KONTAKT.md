# Kontaktbogen-Prüfung: Fotos aller Orte (Simulator 3D-4.67, MoveEye 2.98.98)

Stand 31.10.2026. Basis `origin/main` (e7e3023). Nur geprüft, **nichts repariert**.

**Ablauf:** Simulator mit `--stream --port 9250` auf Xvfb `:150`, Test-HOME `/tmp/claude-0/kontakt_home`.
Kontaktbogen per `/control {"action":"dev","do":"contact","world":<welt>,"day":true}` Welt für Welt (vorher Last geprüft).
Laufzeit gesamt 22 Min. (Bergtal 13 Min.), keine Welt hing, alle 246 Fotos `ok:true`.
Danach jedes Foto selbst angeschaut (Raster à 6 Bilder, Verdachtsfälle in voller Grösse).
Bilder mit Fehlern: `/tmp/claude-0/real_shots/kontakt/` (86 Dateien).

## Übersicht

| Welt | Orte | ok | Fehler | davon stört Test |
|---|---:|---:|---:|---:|
| camping | 1 | 1 | 0 | 0 |
| bergtal (inkl. Bergdorf, Pfadilager) | 153 | 79 | 74 | 8 |
| ferienpark (inkl. Hofladen) | 72 | 61 | 11 | 0 |
| festival | 13 | 13 | 0 | 0 |
| daheim | 4 | 3 | 1 | 0 |
| ort | 1 | 1 | 0 | 0 |
| zuhause | 1 | 1 | 0 | 0 |
| vorlage | 1 | 1 | 0 | 0 |
| **Total** | **246** | **160** | **86** | **8** |

Keine schwarzen/leeren Bilder durch Renderfehler, keine fehlenden Texturen (rosa/kariert), keine Kästchen in Texten, kein sichtbares Z-Fighting.
Die Fehler sind fast alle **Kamera-Wahl** (55) oder **Geometrie der Welt** (31). Fast alles im Bergtal (steiles Gelände).

Spalte «Ursache»: **Foto-Kamera** = die Welt ist vermutlich in Ordnung, aber die Sprung-Kamera des Entwicklertools steht ungünstig
(im Hang, in der Schlucht, hinter Baum/Tür, auf Wasserhöhe, falsche Blickrichtung). **Welt** = etwas in der Szene selbst ist falsch.
Schwere: **stört Test** = betrifft einen MoveEye-Standort oder Dinge, auf denen sich Personen/Fahrzeuge bewegen; **nur optisch** = sonst.

Hinweise ohne Fehler: `szene.ort` zeigt im frischen Test-HOME dasselbe Bild wie `szene.camping` (keine Karte gewählt) und `szene.vorlage`
ist eine leere Wiese (keine 3D-Vorlage geladen) – erwartet. Die Erlebnis-Vignetten (Ferienpark/Bergtal) zeigen ihre Figuren/Tiere
oft nicht – möglicherweise erscheinen sie erst beim Abspielen; trotzdem gelistet, weil der Ort dann «nicht wie sein Name» aussieht.

## Die 10 wichtigsten

1. `bergdorf.standort.platz` (MoveEye-Standort): graue senkrechte Flächen stehen mitten auf dem Dorfplatz – im Bild von MoveEye. **stört Test**
2. `pfadilager.standort.zelte` (MoveEye-Standort): Tanne direkt vor der Kamera verdeckt ein Drittel. **stört Test**
3. Passstrasse Bergtal schwebt/zerreisst (`bergtal.ort.furggakehren`, `vignette.haarnadel`, `postauto`, `schafstau_pass`, `dohlen_sandwich`, `nordlicht`): Belag und weisse Randstreifen über dem Gelände – Autos/Schafe/Personen darauf schweben. **stört Test**
4. Sprung-Kamera im Gelände/Wasser – Bild einfarbig: `bergtal.ort.riedmoos_wollgras`, `bergtal.ort.schwarzseeli`, `schlafplatz.pass` (70 % weiss), `schlafplatz.schlucht`, `vignette.selfie_kante`.
5. Sprung-Kamera in Schluchten – fast schwarz: `bergtal.ort.tuefelsschlund_wasserfall`, `vignette.echo_schlucht`, `kristallhoehle`, `moorsee`, `wollgras`, `alphorn`.
6. Weisse Platte schwebt frei zwischen den Bergen (`vignette.bartgeier_knochen`, `gipfelbuch`, auch in `schneehase_herbst` sichtbar) – vermutlich Wasserfall-Fläche ohne Fels dahinter.
7. Räume: Baum und Zaun ragen in `raum.militaerbaracke_gufer_innen`; `raum.infanteriewerk_gufer_innen` hat Gras als Boden; `raum.alte_sennerei_chaesgaden_innen` ohne Dach.
8. Gelände-Spalt mit gestreckter Textur bei `bergtal.ort.alp_tschuggen` (V-Riss, weisses Band darin).
9. `szene.tarnen`: Tarnwiese als flaches Rechteck mit scharfer Kante, ragt über den Hügel.
10. «Ort passt nicht zum Namen»: kein Wald bei `ort.steimandli_wald`/`vignette.steinmann_wald`, keine Blumen bei `ort.bluemenmatte`/`vignette.blumenwiese`, kein Gletscher bei `aussicht.vp_gletscher`, keine Steinbrücke bei `bergdorf.ort.steinbruecke`.

## Alle Fehler

| Ort-ID | Beschreibung | Bild (unter `user://kontaktbogen/`) | Schwere | Ursache |
|---|---|---|---|---|
| `bergdorf.ort.passstrasse` | Kamera blickt auf Berghang, keine Strasse sichtbar (Ort passt nicht zum Namen) | `bergtal/bergdorf.ort.passstrasse.jpg` | nur optisch | Foto-Kamera |
| `bergdorf.ort.steinbruecke` | Brücke ist Holzdeck, keine Steinbrücke | `bergtal/bergdorf.ort.steinbruecke.jpg` | nur optisch | Welt |
| `bergdorf.standort.platz` | mehrere graue, senkrechte Flächen (mit Bodentextur) stehen mitten auf dem Dorfplatz - vermutlich Ränder/Schürzen der eingeebneten Platzfläche oder sichtbare Hindernis-Boxen | `bergtal/bergdorf.standort.platz.jpg` | **stört Test** | Welt |
| `bergtal.aussicht.vp_gletscher` | kein Gletscher im Bild, Blick auf Wiesenhang (Ort passt nicht zum Namen) | `bergtal/bergtal.aussicht.vp_gletscher.jpg` | nur optisch | Foto-Kamera |
| `bergtal.aussicht.vp_grat` | Kamera liegt fast im Hang: halbes Bild dunkle Bodenfläche | `bergtal/bergtal.aussicht.vp_grat.jpg` | nur optisch | Foto-Kamera |
| `bergtal.aussicht.vp_moorsee` | kein See sichtbar, Blick steil nach unten in Wald (Name: Schwarzseeli) | `bergtal/bergtal.aussicht.vp_moorsee.jpg` | nur optisch | Foto-Kamera |
| `bergtal.aussicht.vp_seeblick` | kein See sichtbar; weisse flache Bänder (Bach-/Schnee-Mesh?) schweben quer über steilen Hang | `bergtal/bergtal.aussicht.vp_seeblick.jpg` | nur optisch | Welt |
| `bergtal.ort.alp_tschuggen` | tiefer V-Spalt im Gelände mit gestreckter Textur, weisses Band schwebt darin (Gelände-Naht/Schlucht-Mesh) | `bergtal/bergtal.ort.alp_tschuggen.jpg` | nur optisch | Welt |
| `bergtal.ort.fort_chruezli_bunker` | kein Bunker erkennbar, nur grauer Klotz halb im Hang versunken | `bergtal/bergtal.ort.fort_chruezli_bunker.jpg` | nur optisch | Welt |
| `bergtal.ort.furggakehren` | Strasse zerrissen: weisse Randstreifen schweben, Belag-Stücke stehen schräg/im Boden (Strassen-Mesh folgt Gelände nicht) | `bergtal/bergtal.ort.furggakehren.jpg` | **stört Test** | Welt |
| `bergtal.ort.bluemenmatte` | keine Blumen, nur leerer Grashang (fast leerer Ort) | `bergtal/bergtal.ort.bluemenmatte.jpg` | nur optisch | Welt |
| `bergtal.ort.gratspitz` | Kamera liegt am Hang, halbes Bild dunkle Bodenfläche, Gipfel nicht erkennbar | `bergtal/bergtal.ort.gratspitz.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.gumpen_im_tschuggenbach` | kein Bach/Gumpen sichtbar, Baum verdeckt Bildmitte | `bergtal/bergtal.ort.gumpen_im_tschuggenbach.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.gumpifall_mit_hoehle` | kein Wasserfall/keine Höhle sichtbar, Felswand füllt halbes Bild | `bergtal/bergtal.ort.gumpifall_mit_hoehle.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.gumpisee` | Kamera auf/unter Wasserhöhe: Wasserfläche füllt 80 % des Bildes | `bergtal/bergtal.ort.gumpisee.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.riedmoos_wollgras` | Bild einfarbig olivgrün: Kamera im Gelände oder direkt davor (nichts zu sehen) | `bergtal/bergtal.ort.riedmoos_wollgras.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.obri_stafelhuette_seilbahn` | grosse Lärche direkt vor der Kamera verdeckt rechte Bildhälfte | `bergtal/bergtal.ort.obri_stafelhuette_seilbahn.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.schwarzseeli` | Bild einfarbig dunkelblau-grau: Kamera im Boden/unter Wasser | `bergtal/bergtal.ort.schwarzseeli.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.steimandli_wald` | kein Wald, nur Steinmännchen auf kahler Wiese (Name passt nicht) | `bergtal/bergtal.ort.steimandli_wald.jpg` | nur optisch | Welt |
| `bergtal.ort.ruefi_geroellhalde` | Kamera knapp über dem Hang, Vordergrund verschmierte Geländetextur | `bergtal/bergtal.ort.ruefi_geroellhalde.jpg` | nur optisch | Foto-Kamera |
| `bergtal.ort.tuefelsschlund_wasserfall` | Kamera unten in der Schlucht: fast schwarz, gestreckte Felstextur, kein Wasserfall sichtbar | `bergtal/bergtal.ort.tuefelsschlund_wasserfall.jpg` | nur optisch | Foto-Kamera |
| `bergtal.raum.alp_tschuggen_huettenstube_innen` | Holzpfosten/Balken direkt vor der Kamera verdeckt 1/3 des Bildes | `bergtal/bergtal.raum.alp_tschuggen_huettenstube_innen.jpg` | nur optisch | Foto-Kamera |
| `bergtal.raum.alte_sennerei_chaesgaden_innen` | Raum ohne Dach (nur Sparren), Seitenwand fehlt teilweise - Berge sichtbar | `bergtal/bergtal.raum.alte_sennerei_chaesgaden_innen.jpg` | nur optisch | Welt |
| `bergtal.raum.hospiz_eingangshalle_innen` | offene Tür (braunes Türblatt) direkt vor der Kamera, verdeckt linkes Drittel | `bergtal/bergtal.raum.hospiz_eingangshalle_innen.jpg` | nur optisch | Foto-Kamera |
| `bergtal.raum.hospiz_hauskapelle_innen` | Türblatt direkt vor der Kamera am linken Rand | `bergtal/bergtal.raum.hospiz_hauskapelle_innen.jpg` | nur optisch | Foto-Kamera |
| `bergtal.raum.gumpifall_hoehle_innen` | Höhle sieht aus wie eckiger Betongang (Kastenwände), nicht wie Höhle | `bergtal/bergtal.raum.gumpifall_hoehle_innen.jpg` | nur optisch | Welt |
| `bergtal.raum.militaerbaracke_gufer_innen` | Baum und Zaun von draussen ragen durch die Wand in den Raum | `bergtal/bergtal.raum.militaerbaracke_gufer_innen.jpg` | nur optisch | Welt |
| `bergtal.raum.infanteriewerk_gufer_innen` | kein Boden: Geländefläche (Gras) als Bunkerboden, Schild «Kampfstand» halb abgeschnitten | `bergtal/bergtal.raum.infanteriewerk_gufer_innen.jpg` | nur optisch | Welt |
| `bergtal.raum.talstation_materialseilbahn_innen` | Seilwinde direkt vor der Kamera, Raum nicht erkennbar | `bergtal/bergtal.raum.talstation_materialseilbahn_innen.jpg` | nur optisch | Foto-Kamera |
| `bergtal.schlafplatz.biwak` | Biwakschachtel nur am rechten Rand, schräg gekippt (folgt Hang nicht) | `bergtal/bergtal.schlafplatz.biwak.jpg` | nur optisch | Welt |
| `bergtal.schlafplatz.gletschersee` | Blick steil nach unten auf dunklen Hang, kein See; weisses Weg-Stück schwebt, Schild angeschnitten | `bergtal/bergtal.schlafplatz.gletschersee.jpg` | nur optisch | Foto-Kamera |
| `bergtal.schlafplatz.kapelle` | Masten-Gerüst direkt vor der Kamera, keine Kapelle sichtbar, steiler Hang | `bergtal/bergtal.schlafplatz.kapelle.jpg` | nur optisch | Foto-Kamera |
| `bergtal.schlafplatz.moor` | fast leerer Ort: dunkle Fläche, kleine weisse Ellipse (Tümpel?) schwebt | `bergtal/bergtal.schlafplatz.moor.jpg` | nur optisch | Foto-Kamera |
| `bergtal.schlafplatz.pass` | untere 70 % des Bildes reinweiss: Kamera in/vor weisser Wand (Hospiz) oder Schneefläche | `bergtal/bergtal.schlafplatz.pass.jpg` | nur optisch | Foto-Kamera |
| `bergtal.schlafplatz.felsnische` | Gelände als grobe Stufen-Klötze (Felsnische unglaubwürdig, verdeckt halbes Bild) | `bergtal/bergtal.schlafplatz.felsnische.jpg` | nur optisch | Welt |
| `bergtal.schlafplatz.ruine` | keine Ruine sichtbar, leerer dunkler Hang; grünes Objekt schwebt | `bergtal/bergtal.schlafplatz.ruine.jpg` | nur optisch | Foto-Kamera |
| `bergtal.schlafplatz.schlucht` | Kamera am/im Steilhang: Bild fast ganz grüne Geländefläche | `bergtal/bergtal.schlafplatz.schlucht.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.alphorn` | Kamera unten in einer Schlucht, kein Alphornbläser sichtbar, gestreckte Felstexturen | `bergtal/bergtal.vignette.alphorn.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.bartgeier_knochen` | weisses Rechteck (Wasserfall-Fläche?) schwebt frei zwischen den Bergen; kein Bartgeier erkennbar | `bergtal/bergtal.vignette.bartgeier_knochen.jpg` | nur optisch | Welt |
| `bergtal.vignette.blumenwiese` | keine Blumen sichtbar, nur Wiese mit Weg | `bergtal/bergtal.vignette.blumenwiese.jpg` | nur optisch | Welt |
| `bergtal.vignette.echo_schlucht` | fast schwarzes Bild: Kamera tief in der Schlucht, gestreckte Textur | `bergtal/bergtal.vignette.echo_schlucht.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.flaschenpost_laterne` | Kamera am Hang, Geländefläche füllt Bild, kein See/keine Laterne | `bergtal/bergtal.vignette.flaschenpost_laterne.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.fondue_fuchs` | zwei Tannen direkt vor der Kamera, kein Caquelon/Fuchs sichtbar | `bergtal/bergtal.vignette.fondue_fuchs.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.dohlen_sandwich` | weisse Strassen-Randfläche schwebt schräg neben der Strasse | `bergtal/bergtal.vignette.dohlen_sandwich.jpg` | **stört Test** | Welt |
| `bergtal.vignette.geheimer_see` | Kamera auf Wasserhöhe, Wasser füllt 75 % des Bildes | `bergtal/bergtal.vignette.geheimer_see.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.gemse_hospizdach` | Kamera im Hospiz-Dachraum/Gebäude: weisse Fläche mit schwebenden Fensterrahmen, keine Gämse | `bergtal/bergtal.vignette.gemse_hospizdach.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.gipfelbuch` | kein Gipfelkreuz sichtbar; weisse Platte schwebt zwischen den Bergen (wie bartgeier_knochen) | `bergtal/bergtal.vignette.gipfelbuch.jpg` | nur optisch | Welt |
| `bergtal.vignette.gleitschirm` | weder Gleitschirm noch Kuh sichtbar | `bergtal/bergtal.vignette.gleitschirm.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.haarnadel` | Passstrassen-Stücke schweben über dem Gelände (Strasse folgt Hang nicht) | `bergtal/bergtal.vignette.haarnadel.jpg` | **stört Test** | Welt |
| `bergtal.vignette.holzski` | Bild fast nur hellblaue Gletscherfläche, Holzski nur als Punkt erkennbar | `bergtal/bergtal.vignette.holzski.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.huettenwart` | Kamera direkt an der Hüttenwand; offenes Fenster ragt aus der Wand | `bergtal/bergtal.vignette.huettenwart.jpg` | nur optisch | Welt |
| `bergtal.vignette.kristallhoehle` | fast schwarzes Bild: Kamera in enger Schlucht/Felsspalt, keine Höhle sichtbar | `bergtal/bergtal.vignette.kristallhoehle.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.kuh_socke` | weder Kuh noch Zelt sichtbar; Personengruppe am linken Rand angeschnitten (Platz bei MoveEye, sieht aus wie Camping) | `bergtal/bergtal.vignette.kuh_socke.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.kuhglocken_nebel` | leere Wiese, keine Kühe sichtbar (Nebel bei «Tag/klar» aus, Ort wirkt leer) | `bergtal/bergtal.vignette.kuhglocken_nebel.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.labyrinth` | Kamera am Steilhang, Hangfläche füllt halbes Bild, kein Blockfeld erkennbar | `bergtal/bergtal.vignette.labyrinth.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.moorsee` | fast schwarzes Bild: Kamera in Felsspalt/hinter Wand, kein See | `bergtal/bergtal.vignette.moorsee.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.nordlicht` | weisse Streifen (Strassenränder/Leitplanken) schweben in der Luft, Platz leer | `bergtal/bergtal.vignette.nordlicht.jpg` | **stört Test** | Welt |
| `bergtal.vignette.picknick` | Kamera direkt an Felswand/Gelände: 2/3 des Bildes flache braune Fläche | `bergtal/bergtal.vignette.picknick.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.postauto` | kein Postauto; Strassenbelag mit schwebenden weissen Randstreifen, Knick im Belag | `bergtal/bergtal.vignette.postauto.jpg` | **stört Test** | Welt |
| `bergtal.vignette.salamander_prozession` | keine Salamander erkennbar; verzerrtes Gelände im Vordergrund | `bergtal/bergtal.vignette.salamander_prozession.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.schafstau_pass` | Strassen-Randstreifen schweben/zerfranst über dem Gelände | `bergtal/bergtal.vignette.schafstau_pass.jpg` | **stört Test** | Welt |
| `bergtal.vignette.selfie_kante` | leeres Bild aus Gras-Geländefläche: Kamera am Hang, kein Wanderer, keine Schlucht | `bergtal/bergtal.vignette.selfie_kante.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.spalten` | Gletscherspalten als dünne dunkle Balken, die über dem Eis schweben | `bergtal/bergtal.vignette.spalten.jpg` | nur optisch | Welt |
| `bergtal.vignette.schmuggler` | Blick senkrecht nach unten auf Fels, Markierungen kaum erkennbar | `bergtal/bergtal.vignette.schmuggler.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.steinbock_kante` | weisse Felsblöcke schweben neben dem Steilhang, kein Steinbock erkennbar | `bergtal/bergtal.vignette.steinbock_kante.jpg` | nur optisch | Welt |
| `bergtal.vignette.steinmann_wald` | kein Wald, nur Steinmännchen auf kahlen Hügeln (wie bergtal.ort.steimandli_wald) | `bergtal/bergtal.vignette.steinmann_wald.jpg` | nur optisch | Welt |
| `bergtal.vignette.sternschnuppen` | Steilhang füllt 2/3 des Bildes, Block schwebt am Hang | `bergtal/bergtal.vignette.sternschnuppen.jpg` | nur optisch | Welt |
| `bergtal.vignette.strommast` | dunkle Mulde, kein Strommast und keine Strasse sichtbar | `bergtal/bergtal.vignette.strommast.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.wanderer_kreis` | Kamera am Steilhang, Hang/Weg füllt halbe Bildfläche | `bergtal/bergtal.vignette.wanderer_kreis.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.wollgras` | Kamera in einer Geländefalte: Bild aus schrägen dunklen Flächen, kein Moor | `bergtal/bergtal.vignette.wollgras.jpg` | nur optisch | Foto-Kamera |
| `bergtal.vignette.yeti_spuren` | Hang füllt Bild, Gletscher nur am Rand, keine Spuren/kein Schneemann | `bergtal/bergtal.vignette.yeti_spuren.jpg` | nur optisch | Foto-Kamera |
| `pfadilager.ort.forststrasse` | keine Forststrasse sichtbar, Lärche direkt vor der Kamera | `bergtal/pfadilager.ort.forststrasse.jpg` | nur optisch | Foto-Kamera |
| `pfadilager.standort.zelte` | grosse Tanne direkt vor der Kamera verdeckt linkes Drittel (MoveEye-Standort!) | `bergtal/pfadilager.standort.zelte.jpg` | **stört Test** | Welt |
| `szene.tarnen` | Tarnwiese ist ein flaches hellgrünes Rechteck mit scharfer Kante, das über/in den Hügel ragt | `bergtal/szene.tarnen.jpg` | nur optisch | Welt |
| `ferienpark.erlebnis.enten` | keine Enten sichtbar, leere Wiese mit Weg | `ferienpark/ferienpark.erlebnis.enten.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.erlebnis.flaschenpost` | weder Flaschenpost noch Kiste sichtbar; rotes Dreieck am linken Rand angeschnitten | `ferienpark/ferienpark.erlebnis.flaschenpost.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.erlebnis.hoehle` | keine Höhle, nur ein Felsblock auf dunkler Fläche | `ferienpark/ferienpark.erlebnis.hoehle.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.erlebnis.hund_ball` | kein Hund erkennbar, nur Strand mit Schirmen | `ferienpark/ferienpark.erlebnis.hund_ball.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.erlebnis.moewe` | Kamera im/auf dem Restaurant-Dach: weisse Fläche füllt halbes Bild, Schrift spiegelverkehrt (Rückseite des Schilds) | `ferienpark/ferienpark.erlebnis.moewe.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.erlebnis.yoga` | leerer Strand, keine Yoga-Figuren sichtbar | `ferienpark/ferienpark.erlebnis.yoga.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.ort.aussichtspunkt` | grosse Tanne direkt vor der Kamera verdeckt rechtes Drittel | `ferienpark/ferienpark.ort.aussichtspunkt.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.ort.bootshaus` | Steg hinter dem Bootshaus scheint auf Dachhöhe über dem Wasser zu schweben | `ferienpark/ferienpark.ort.bootshaus.jpg` | nur optisch | Welt |
| `ferienpark.ort.dorf_mit_kirche` | Kamera direkt an der Kirchenwand: Kirche füllt 2/3 des Bildes, Dorf kaum sichtbar | `ferienpark/ferienpark.ort.dorf_mit_kirche.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.ort.festwiese_mit_buehne` | Bühne nur angeschnitten am rechten Rand (schwarzer Block) | `ferienpark/ferienpark.ort.festwiese_mit_buehne.jpg` | nur optisch | Foto-Kamera |
| `ferienpark.ort.hochsitz` | Tanne direkt vor der Kamera mitten im Bild, kein Hochsitz sichtbar | `ferienpark/ferienpark.ort.hochsitz.jpg` | nur optisch | Foto-Kamera |
| `szene.daheim` | Heckenstücke liegen kreuz und quer mitten in der Wiese (wirken zufällig verstreut, kein Garten erkennbar); gleich in szene.garten | `daheim/szene.daheim.jpg` | nur optisch | Welt |

## Vorschläge zur Behebung

**A. Sprung-Kamera (55 Fälle, ein Ort im Code) – `simulator3d/scripts/devtool.gd`, `view_at()` (Zeile ~365):**
Die Blickrichtung kommt vom *vorherigen* Blick (`fwd` der aktuellen Kamera), und die Bodenhöhe wird nur am Kamerapunkt geprüft.
Im steilen Bergtal steht die Kamera so oft im Hang, in der Schlucht, hinter einem Baum oder auf Wasserhöhe.
Vorschlag: 8 Richtungen um den Ort probieren und die erste nehmen, bei der ein Raycast Ziel→Kamera frei ist
(`PhysicsDirectSpaceState3D.intersect_ray`, bzw. `main.ground_y` in Schritten entlang der Linie) und die Kamera ≥ 2 m über Gelände **und**
über Wasser steht; bei Seen den Abstand vergrössern. Wo Daten eine eigene Blickrichtung haben (Bergtal `VIEWPOINTS` letztes Feld, vermutlich Blickrichtung in Grad,
`SPOTS`), diese verwenden. Für Räume (`bergtal_orte.gd` `fly()`, Zeile ~1737) die Kamera in die Raummitte statt hinter Pfosten/Türblatt.
Ort ohne sichtbaren Inhalt (Vignetten): im Kontaktbogen die Vignette kurz starten oder ihren Mittelpunkt (nicht Spawn-Punkt) anzielen.

**B. Passstrasse schwebt – `simulator3d/scripts/bergtal.gd`** `_roads_and_trails()` (Zeile ~1381) und `_road_flatten()` (Zeile ~626):
Strassenstücke und Randlinien folgen dem Gelände in Kurven/Kehren nicht (Haarnadel, Furggakehren). Gelände unter der Strasse stärker
einebnen bzw. Strassen-Mesh pro Segment auf `ground_y` setzen; Randlinien mit kleinem Versatz auf den Belag legen statt eigene Höhe.

**C. Dorfplatz Bergdorf – vermutlich `bergtal.gd` (Bergdorf-Teil, Platz-Einebnung) oder die Hindernis-Boxen der Gebäude:**
graue senkrechte Flächen mit Bodentextur – aussehen wie Ränder/Schürzen einer eingeebneten Fläche. Prüfen, welche Mesh-Instanz das ist
(Entwicklertool «Was ist das?» auf die Fläche) und entfernen/absenken. **Wichtig, weil MoveEye-Standort.**

**D. Pfadilager-Standort `pfadilager.standort.zelte`:** Standort-Punkt oder Baum (Bergtal Pfadilager-Teil, `bergtal.gd`/`bergtal_orte.gd`) um
einige Meter verschieben, damit MoveEye frei sieht.

**E. Räume – `simulator3d/scripts/bergtal_orte.gd`** (`INSIDE`): Militärbaracke: Bäume/Zäune um das Haus beim Platzieren aussparen (Abstand
zum Grundriss). Infanteriewerk: Bodenplatte fehlt. Alte Sennerei: Dach/Decke fehlt (falls nicht als Ruine gewollt). Gumpifall-Höhle: eckig wie
ein Betongang, eventuell unregelmässige Felsform.

**F. Freie Flächen in der Luft – `bergtal.gd` / `bergtal_aussicht.gd`:** die weisse Platte zwischen den Bergen (Bartgeier, Gipfelbuch, Schneehase)
– Wasserfall-Fläche, die vor dem Hang hängt; an die Felswand setzen oder Fels dahinter ergänzen. Gletscherspalten (`vignette.spalten`) als
Einschnitte statt Balken über dem Eis. Steinbock-Kante/Sternschnuppen: Felsblöcke auf `ground_y` setzen.

**G. Gelände – `bergtal.gd` (Höhenfeld):** V-Spalt bei Alp Tschuggen, Stufen-Klötze bei Felsnische, gestreckte Texturen in Schluchten
(Triplanar-Mapping für steile Flächen wäre die saubere Lösung, ist aber teuer – im Lite-Modus aus).

**H. Kleinigkeiten:** `szene.tarnen` (Tarnwiese-Rechteck in `bergtal.gd`/Tarnen-Szene: an Gelände anpassen oder Rand weich machen);
`ferienpark.ort.bootshaus` (Steg-Höhe in `ferienpark.gd`); `szene.daheim`/`szene.garten` (verstreute Heckenstücke – falls gewollt als
Verstecke, ok); Namen passend machen oder Inhalt ergänzen (Steinbrücke aus Stein, Wald beim Steimandli, Blumen auf der Bluemenmatte).

## Nicht geprüft / Grenzen
- Nur «bei Tag, klar» (12 Uhr). Nacht, Regen, Nebel nicht fotografiert.
- Software-Grafik unter Xvfb (OpenGL-Compatibility via `--rendering-driver opengl3`); auf Windows mit Forward+ kann es anders aussehen
  (z. B. Z-Fighting, das hier nicht sichtbar ist).
- Ob Vignetten-Figuren nur beim Abspielen erscheinen, habe ich nicht im Code nachgeprüft.
- Eine Auflösung von 640 × 360 – kleine Fehler (Kästchen in kleinen Schildern) können übersehen sein.
