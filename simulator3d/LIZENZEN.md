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

## Übrige Inhalte

Gelände, Pflanzen, Gebäude, Tiere, Himmel, Töne und Texturen entstehen ebenfalls im Code (Formen, Rauschen,
Shader in `shaders/`). Kartendaten eines echten Orts kommen beim Laden von swisstopo / OpenStreetMap
(Nachweis in der Karte des Simulators).
