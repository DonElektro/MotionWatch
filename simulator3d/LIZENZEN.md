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

## Figuren-Paket (ab 3D-4.56) – `pakete/figuren_v1.zip`, `scripts/figur_paket.gd`

Das nachladbare Figuren-Paket (nicht im Simulator-ZIP; Download aus dem Repository oder neben die .exe legen) ist aus
Figuren von **Quaternius** gebaut (`werkzeuge/figuren_paket.py`). Lizenz **CC0 1.0 Universal** (gemeinfrei,
<https://creativecommons.org/publicdomain/zero/1.0/>) – Nutzung und Weitergabe ohne Namensnennung erlaubt; wir nennen die
Quelle trotzdem: Quaternius (<https://quaternius.com>) «Universal Base Characters», «Modular Outfits Fantasy»,
«Universal Animation Library» 1 und 2.

## Maggie (Hund der Geschichte «Maggie und der Bergkristall») – `modelle/maggie_hund_glb.bin`, `scripts/maggie_modell.gd`

Ab Grafik «mittel» ist Maggie ein Modell mit Skelett. Grundlage: **Quaternius «Ultimate Animated Animals»** (Juli 2021),
Modell «ShibaInu» (`glTF/ShibaInu.gltf`, SHA-256 `3236979b…0f6b`), Lizenz **CC0 1.0 Universal** (gemeinfrei,
<https://creativecommons.org/publicdomain/zero/1.0/>) – Nutzung, Änderung und Weitergabe ohne Namensnennung erlaubt; wir
nennen die Quelle trotzdem: Quaternius (<https://quaternius.com>). Bezogen am 01.11.2026 aus einer öffentlichen
GitHub-Kopie des Pakets (laoniutoushx/TD-demo-2024-04-03; Prüfsumme gleich wie die Git-LFS-Datei in anderen Kopien, die
Lizenzdatei des Pakets liegt z. B. in francisb1996/brave-chicken-assets). Angepasst mit `werkzeuge/maggie_modell.py`
(Proportionen eines Jack Russell, Kippohren, Schwanz, Glätten, Maggies Muster, ohne Animationen). Fellstruktur und
Randlicht: `shaders/maggie_fell.gdshader` (selbst geschrieben). Mit Grafik «einfach» (Lite) baut `scripts/maggie_einfach.gd`
sie aus eigenen Grundformen (keine fremde Datei). Andere Hunde und Tiere sind unverändert.

## Übrige Inhalte

Gelände, Pflanzen, Gebäude, Tiere, Himmel, Töne und Texturen entstehen ebenfalls im Code (Formen, Rauschen,
Shader in `shaders/`). Kartendaten eines echten Orts kommen beim Laden von swisstopo / OpenStreetMap
(Nachweis in der Karte des Simulators).
