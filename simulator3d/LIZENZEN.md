# Lizenzen der Inhalte im 3D-Simulator

Stand: 3D-4.12 (Oktober 2026)

## Figuren (Menschen) – `scripts/figur.gd`

Die Figuren mit Skelett (ab Grafik «mittel») sind **selbst gebaut**: Knochen (Skeleton3D), gehäuteter Körper und
Wärmebild-Temperaturen werden beim Start im Programmcode erzeugt. Es gibt **keine fremde Modell- oder Animationsdatei**,
also auch keine fremde Lizenz und keinen Namensnachweis. Die Bewegungen (Gehen, Rennen, Ducken, Kriechen, Stehen, Tragen)
kommen wie bisher aus `scripts/actor.gd`. Teil von MoveEye, gleiche Bedingungen wie der übrige Programmcode.

Geprüft und **nicht** verwendet (30.10.2026):

| Quelle | Lizenz | Warum nicht |
|---|---|---|
| Khronos glTF Sample Assets «CesiumMan», «RiggedFigure» | CC-BY 4.0 (Cesium, Markenhinweis) | nur ein Gang, kein Ducken / Kriechen / Tragen; Namensnachweis nötig |
| Quaternius «Universal Animation Library» | CC0 | nur über quaternius.com / itch.io – von diesem Rechner aus nicht erreichbar |
| three.js-Beispiele (Soldier, Xbot, Michelle) | Mixamo | Weitergabe der Modelle nicht frei erlaubt |

Wer später ein fertiges CC0-Modell (glTF/GLB) einbauen will: hier mit Quelle, Autor und Lizenz eintragen;
bei CC-BY zusätzlich den Namensnachweis in «Über MoveEye» und «Lies mich» aufnehmen.

## Klänge der Trailer (ab 01.11.2026) – `klang/`, `scripts/trailer_ton.gd`

Musik und Geräusche der beiden Trailer sind aus freien Aufnahmen gebaut (`werkzeuge/klang_bauen.py`): Streicher, Pauken,
Blech und Glockenspiel aus **VSCO-2 Community Edition** (Versilian Studios, CC0), Regen, Bach und Donner von **rubberduck**
(OpenGameArt, CC0) und **Fugue State Audio** (gemeinfrei), Schritte, Holz und Glocke von **Kenney** (CC0), Papier und Luftzug
von **Ben Burnes** (CC0); dazu eigene Synthese. Alles CC0 bzw. gemeinfrei, keine Namensnennung nötig. Datei für Datei mit
Repository und Commit: `klang/LIZENZEN.txt`.

## Spielton (ab 01.11.2026) – `klang/sp_*.ogg`, `scripts/klang.gd`

Klänge in Spielen und Geschichten (`werkzeuge/spielton_bauen.py`): Glockenspiel, Trompeten, Harfe, Flöte, Marimba, Streicher
und Pauke aus **VSCO-2 Community Edition** (CC0), Kleine Trommel und Becken aus der **Versilian Community Sample Library**
(VCSL, CC0), Schritte und Klick von **Kenney** (CC0), Knistern von **Ben Burnes** (CC0), Holz von **rubberduck** (CC0);
dazu eigene Synthese. Alles CC0, keine Namensnennung nötig. Datei für Datei: `klang/LIZENZEN.txt`, Abschnitt «Spielton».

## Figuren-Paket (ab 3D-4.56) – `pakete/figuren_v1.zip`, `scripts/figur_paket.gd`

Das nachladbare Figuren-Paket (nicht im Simulator-ZIP; Download aus dem Repository oder neben die .exe legen) ist aus
Figuren von **Quaternius** gebaut (`werkzeuge/figuren_paket.py`). Lizenz **CC0 1.0 Universal** (gemeinfrei,
<https://creativecommons.org/publicdomain/zero/1.0/>) – Nutzung und Weitergabe ohne Namensnennung erlaubt; wir nennen die
Quelle trotzdem: Quaternius (<https://quaternius.com>) «Universal Base Characters», «Modular Outfits Fantasy»,
«Universal Animation Library» 1 und 2.

## Übrige Inhalte

Gelände, Pflanzen, Gebäude, Tiere, Himmel, Töne und Texturen entstehen ebenfalls im Code (Formen, Rauschen,
Shader in `shaders/`). Kartendaten eines echten Orts kommen beim Laden von swisstopo / OpenStreetMap
(Nachweis in der Karte des Simulators).
