# A1 MoveEye im Abenteuer: Lager, Wildkamera, seltene Tiere

Neu (scripts/abenteuer_moveeye.gd, kleine Einhänge-Punkte in bergtal_abenteuer.gd):
- Lager: MoveEye «Lager bewachen» (Alarm weckt) oder «Wildkamera am Wildwechsel» (still, mehr Tiere). Proviant: beim Rucksack / ins Zelt / aufhängen.
- Nacht: Fuchs an den Proviant. Ungesichert und kein Alarm = Proviant weg (weniger Kraft am Morgen). Meldet MoveEye den Fuchs vorher, wachst du auf und verscheuchst ihn.
- Tiere vor der Kamera: Foto, wenn sichtbar (testrun.visible / thermal_visible) und MoveEye gleichzeitig etwas meldet (mw_det). Ohne MoveEye: geschätzt.
- Hinweis-Aufnahme: blinkendes Licht am Berg in Richtung des nächsten Kapitels.
- Morgen: «MoveEye tagsüber als Wildkamera stehen lassen» (Murmeltier, Adler, Bartgeier, Gämse, Steinbock). Aufnahmen auswerten (Tier selbst bestimmen).
- Sammlung 7 Tiere (Kapitel-Seite), Wildkamera-Aufgaben, foto_wertung() für A5.
- bergtal.gd: Luchs («berg_lynx»); waerme.gd: Murmeltier, Steinadler, Bartgeier.

So testest du:
1. Bergtal-Abenteuer starten, Kapitel 1 bis zum Nachtlager.
2. «Wildkamera am Wildwechsel», Proviant «Beim Rucksack lassen», Lager aufschlagen, Nacht starten (MoveEye verbunden).
3. Am Morgen: Fuchs-Zeile und Hinweis-Bild ansehen, «MoveEye tagsüber als Wildkamera …», danach Aufnahmen auswerten.
4. Nächstes Kapitel: Sammlung auf der Kapitel-Seite.

Nicht getestet: der ganze Ablauf live (der Testlauf blieb auf dem überlasteten Rechner unterwegs hängen, Lager/Nacht nie erreicht); mit echtem MoveEye; Bilder; Lite.
Getestet: Parse-Check (mit und ohne A4-Inventar), foto_wertung, Laplace, Antworten, Richtung (headless).

Konzept-Check: MoveEye kennt keine Tierart und keine Schärfe. Das Tier kommt aus der Simulator-Wahrheit, die Schärfe aus einem Kamera-Modell im Simulator. Die neuen Ursachen lynx/ibex/marmot/eagle/vulture/light fehlen in NACHT_CAUSES (579b) und erscheinen dort roh. Vorschlag: dort ergänzen. Kein neues Menü (nur Abenteuer-Fenster).
