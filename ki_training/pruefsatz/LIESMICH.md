# Echtbild-Prüfsatz

Ein **fester Satz Bilder mit der richtigen Antwort** (Person / Tier / Fahrzeug / Nichts). GitHub misst damit MoveEyes KI
ohne Simulator und ohne Godot: Actions → **«Prüfsatz»** (läuft auch nach jeder neuen Version und wenn sich hier etwas
ändert). In der Zusammenfassung des Laufs steht je Modell (Standard-Modell SSD und, falls veröffentlicht, das eigene
Modell aus dem Release «ki-modell»):

| Modell | Bilder | Personen gefunden | verpasst | Fehlalarme (Bilder ohne Person) |
|---|---|---|---|---|

Getrennt nach **echt** und **Simulator**. Eine Person zählt als gefunden, wenn ein KI-Rahmen die wahre Person trifft
(Überlappung mindestens 30 % oder die Mitte des KI-Rahmens liegt in ihr). Ein Fehlalarm ist ein Bild ohne Person
(Tier, Nichts), in dem die KI eine Person sieht. Die KI sieht das Bild in derselben Grösse wie im Kamera-Ablauf (480 px breit).

Zurzeit liegen hier nur **30 Bilder aus dem 3D-Simulator** (9 Personen, 21 Tiere) (`sim_*.jpg`, Tag, Abend, Nacht mit Infrarot, Regen, Nebel) –
zum Ausprobieren, bis es echte Bilder gibt.

## Echte Bilder dazugeben (Daniel)

1. In MoveEye nach einem Alarm **«Was war das?»** beantworten (Person / Tier / Nichts). Die Bilder liegen auf dem Pi in
   `~/.config/motionwatch/alarm_labels/`.
2. Auf dem Pi (oder auf dem PC mit einer Kopie dieses Ordners):
   ```
   python3 pruefsatz.py exportieren --nach ~/MoveEye_Pruefsatz
   ```
   Es entstehen der Ordner `~/MoveEye_Pruefsatz/` (Bilder + `labels.json`) und `~/MoveEye_Pruefsatz.zip`.
   `pruefsatz.py` liegt im Repository unter `ki_training/` (braucht nur Python, kein MoveEye).
3. Wohin damit – **Datenschutz** (wie beim Training, siehe `ki_training/README.md`):
   * Ist das Repository öffentlich, kann **jeder** die Bilder sehen. **Echte Bilder mit fremden Personen gehören nicht
     hierher** (auch nicht in ein Release).
   * **Privat (empfohlen):** die ZIP auf einen eigenen Speicher legen (z. B. Nextcloud-Freigabe-Link, der direkt die ZIP
     liefert) und den Link auf GitHub als Secret hinterlegen: Settings → Secrets and variables → Actions →
     «New repository secret», Name **`PRUEFSATZ_URL`** (mehrere Links mit Komma). Der Lauf lädt die Bilder nur zum Messen;
     als Ergebnis bleibt nur die Zahlen-Datei (ohne Bilder).
   * Tiere und leere Fehlalarme dürfen hierher:
     `python3 pruefsatz.py exportieren --nach ki_training/pruefsatz --ohne-personen` (klein halten, höchstens 20 MB).
     Liegt das Ziel in einem Git-Repository und sind echte Personen dabei, bricht das Exportieren ab.

Der Prüfsatz bleibt **fest**: nur dazugeben, nichts austauschen – nur so sind die Zahlen von Version zu Version vergleichbar.
Die gleiche `labels.json` versteht auch das Training (`ki_training/trainieren.py --echt …`); Bilder, mit denen gemessen
wird, sollten aber nicht auch trainiert werden.

## Für Entwickler

```
python3 ki_training/pruefsatz.py aus-simulator --sim http://127.0.0.1:8765 --n 16      # Simulator-Bilder dazu
python3 ki_training/pruefsatz.py messen --ki ORDNER_MIT_MODELLEN [--json ergebnis.json]
```
`--ki`: `frozen_inference_graph.pb` + `ssd_mobilenet_v2_coco.pbtxt` (SSD) und / oder `moveeye_model.onnx` +
`moveeye_model.json` (eigenes Modell). Gemessen wird mit MoveEyes eigener Erkennung (`AIDetector.infer` aus der gebauten
Datei), mit den Standard-Schwellen der Einstellungen. Die «KI-Lupe» (zweiter Blick auf kleine Bewegungen) läuft hier nicht,
weil es keine Bewegung gibt.
