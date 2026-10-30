# Eigenes KI-Modell für MoveEye

Hier entsteht MoveEyes eigenes KI-Modell: ein kleiner YOLO-Detektor (YOLOv8n oder YOLO11n), der nur drei Dinge kennt:
**person**, **animal** (Tier), **vehicle** (Fahrzeug). Er wird auf GitHub trainiert – du brauchst dafür keinen eigenen
Rechner – und MoveEye lädt ihn danach selbst herunter.

## Training starten (Daniel)

1. Auf GitHub das Repository öffnen → oben **Actions** → links **«KI-Modell»** → rechts **«Run workflow»**.
2. Einstellungen lassen (60 Epochen, yolov8n.pt, «veröffentlichen» angehakt) → grüner Knopf **«Run workflow»**.
3. Warten (etwa 30 Minuten bis 2 Stunden, je nach Anzahl Bilder). Ist der Lauf grün, steht in der Zusammenfassung
   des Laufs der Bericht: wie viele Bilder, und die **Güte (mAP50)** – 1,0 wäre perfekt, ab etwa 0,6 ist es brauchbar.
4. In MoveEye: **Einstellungen → KI-Erkennung → «Eigenes Modell herunterladen»**. Es schaltet danach selbst auf
   «KI-Modell: Eigenes (MoveEye-Modell)». Zurück zum alten Modell: «KI-Modell: Standard (SSD)».

Das Modell liegt danach im Release **«ki-modell»** (immer das neueste) und zusätzlich als «ki-modell-NR» (jede Fassung
für sich, falls eine ältere besser war). Ist «veröffentlichen» nicht angehakt, liegt das Ergebnis nur unter
dem Lauf bei «Artifacts» (30 Tage) – zum Ausprobieren: die zwei Dateien in den Ordner `~/.config/motionwatch/models/`
auf dem Pi kopieren.

Automatisch trainieren (z. B. jeden Sonntag): in `.github/workflows/ki_modell.yml` vor den zwei Zeilen
`schedule:` und `- cron:` das `#` entfernen. Standardmässig ist das aus.

## Am einfachsten: Knopf «KI trainieren» im Simulator

Im 3D-Simulator: Karte **«Testen»** → **«Trainingsbilder für eine eigene KI»** → Anzahl und **«Vielfalt: normal / hoch»**
wählen → **«KI trainieren»**. Der Simulator macht das Paket, legt die ZIP-Datei ins Release **«ki-daten»** und startet
hier das Training. MoveEye holt das neue Modell danach **von selbst** (einmal am Tag, Einstellung «Eigenes Modell von selbst
aktualisieren»), aber nur, wenn seine Messung nicht schlechter ist als die des laufenden Modells (mAP50, Trefferquote,
«Personen gefunden», je 0,02 Spielraum). Zum ersten Mal holt man das eigene Modell von Hand («Eigenes Modell herunterladen»).

* Der **GitHub-Schlüssel** ist derselbe wie beim Prüfstand (Feld im Simulator, gespeichert in `user://pruefstand/schluessel.txt`).
  Er braucht: *Contents: Read and write* **und** *Actions: Read and write*, nur dieses Repository (fein abgestufter Schlüssel,
  github.com → Settings → Developer settings → Fine-grained tokens).
* **Ohne Schlüssel**: die ZIP liegt auf dem Schreibtisch; von Hand ins Release «ki-daten» ziehen (siehe unten) und unter
  Actions → «KI-Modell» → «Run workflow» starten.
* **Vielfalt hoch** (empfohlen fürs Training): zufällige Kleider (Farben, Muster), Haltungen (stehend, geduckt, kriechend),
  Dinge in der Hand, Lampen mit verschiedener Lichtfarbe, Sonnenstand (Monat), Wetter, alle Szenen (auch der echte Ort von
  der Karte und «Meine Vorlage», wenn vorhanden), Personen bis 50 m, teils hinter Hecke/Zaun/Auto, Kamera-Fehler (Rauschen,
  Unschärfe, Bewegungsunschärfe, Weissabgleich, JPEG-Qualität 30–90 %), leere Bilder mit Fallen (Ast vor der Linse, Fahne,
  Lichter, Insekten, Schatten). Tiere: etwas grösser/kleiner, Fell heller/dunkler.

## Was über jedes Bild gespeichert wird (labels_meta)

Neben dem YOLO-Text (`labels/…/bild.txt`, unverändert) legt der Simulator `labels_meta/<train|val>/bild.json` ab:
pro Bild Szene, Uhrzeit, Wetter, Licht (0…1), Infrarot, Kopf (Schwenk/Neigung), Kamera-Fehler, Fallen; pro Objekt
(`"line"` = Zeile im YOLO-Text) Klasse, Art, **Abstand (m)**, **Haltung**, **Verdeckung** (0…1, geschätzt aus den Hindernissen
des Simulators), Anschnitt am Bildrand, **Helligkeit im Rahmen**, **Unschärfe**, getragenes Ding, Kleider. Objekte, die nicht
beschriftet wurden (ganz verdeckt, ausserhalb, zu klein), stehen unter `"dropped"`. Bilder, auf denen jemand *fast* ganz
verdeckt ist (80–97 %), werden gar nicht gespeichert – dort gäbe es keine klare richtige Antwort.

## Auswertung «Wo versagt die KI?»

Nach dem Training sucht das neue Modell auf den zurückgehaltenen Bildern. Ein echter Rahmen gilt als gefunden, wenn ein Fund
derselben Klasse ihn mit IoU ≥ 0,5 trifft. `auswertung.md` (im Release und in der Zusammenfassung des Laufs) zeigt die
Trefferquote nach Abstand, Grösse im Bild, Haltung, Licht, Helligkeit, Verdeckung, Unschärfe, Wetter, Art, Szene – dazu die
Fehlalarme auf leeren Bildern je Falle. Die Kurzfassung steht im Manifest (`"summary"`, `"summary_en"`, `"eval"`) und
erscheint in MoveEye im Kasten «Eigenes Modell». Test ohne ultralytics: `--probe-auswertung` (erfundene Funde).

## Bilder dazugeben

### 1. Trainingspakete aus dem Simulator

Im 3D-Simulator der Knopf **«Trainingspaket (YOLO) machen»** (oder in MoveEye, Reiter Simulator: «Trainingspaket für ein eigenes KI-Modell (YOLO)»; etwa 2 s pro Bild). Es
entsteht eine ZIP-Datei `MoveEye-Trainingsbilder_….zip` (bis 3D-4.21: `MW-Trainingsbilder_….zip`) auf dem Schreibtisch (YOLO-Format: `data.yaml`, `images/`, `labels/`).

* **Kleine Pakete** (bis etwa 200 Bilder, rund 10 MB) direkt in den Ordner `ki_training/pakete/` hochladen
  (GitHub: Ordner öffnen → «Add file» → «Upload files»). Das ganze Repository soll klein bleiben:
  **höchstens 30 MB Bilder** in diesem Ordner.
* **Grosse Pakete** (500–2000 Bilder) nicht ins Repository, sondern an ein Release hängen: GitHub → **Releases** →
  Release **«ki-daten»** (beim ersten Mal anlegen: «Draft a new release», Tag `ki-daten`, Titel «KI-Trainingsdaten»)
  → «Edit» → ZIP-Dateien hineinziehen → «Update release». Ein Release-Anhang darf bis 2 GB gross sein und macht das
  Repository nicht grösser. Das Training holt alle ZIPs von dort selbst.

Die Tierarten des Simulators (Fuchs, Reh, Wildschwein, Hund, Katze …) werden beim Training zu «animal» zusammengefasst.
Die Simulator-Pakete haben einen eigenen Teil `val` (jedes 7. Bild) – diese Bilder werden nie trainiert, nur gemessen.

### 2. Echte Alarmbilder («Was war das?»)

Echte Bilder sind am wertvollsten, besonders **Fehlalarme** («Nichts»): daraus lernt das Modell, Schatten, Äste und
Zeltwände nicht für Personen zu halten.

Format: ein Ordner oder eine ZIP-Datei mit den Bildern (JPEG/PNG) und einer Datei **`labels.json`**:

```json
{
  "format": "moveeye-labels-1",
  "items": [
    {"file": "2026-10-28_23-14-05.jpg", "label": "person", "boxes": [[0.41, 0.22, 0.10, 0.45]]},
    {"file": "2026-10-29_02-40-11.jpg", "label": "animal"},
    {"file": "2026-10-29_03-02-57.jpg", "label": "nothing"}
  ]
}
```

* `label`: `person` / `animal` / `vehicle` / `nothing` – auch Deutsch: `Person`, `Tier`, `Fahrzeug`, `Nichts`.
  Statt `file` gehen auch `image` oder `jpg`, statt `label` auch `answer` oder `kind`.
  Auch die Kurzform `{"bild.jpg": "Person", …}` wird gelesen.
* `boxes` (freiwillig): Rahmen als `[x, y, Breite, Höhe]`, Werte 0…1 relativ zum Bild, `x, y` = linke obere Ecke
  (so speichert MoveEye Rahmen). Fehlen die Rahmen, sucht ein vortrainiertes Modell (YOLOv8s, COCO) die Person bzw.
  das Tier; findet es nichts, wird das Bild ausgelassen (steht im Bericht als «übersprungen»).
* Bei `nothing` lernt das Modell: hier ist keine Person und kein Tier (nur sicher erkannte Fahrzeuge werden markiert).
* Jedes 5. Bild (fest nach Dateiname) wird zurückgehalten und nur zum Messen benutzt.

Wohin damit:

* **Achtung Datenschutz:** Ist das Repository öffentlich, kann **jeder** Bilder im Repository und in Releases sehen.
  Echte Bilder mit fremden Personen darum **nicht** dort ablegen.
* **Privat (empfohlen):** die ZIP-Datei auf einen eigenen Speicher legen (z. B. Nextcloud-Freigabe-Link, der direkt die
  ZIP liefert) und den Link auf GitHub als Secret hinterlegen: Settings → Secrets and variables → Actions →
  «New repository secret», Name **`KI_DATEN_URL`**, Wert = der Link (mehrere mit Komma trennen). Das Training lädt die
  Bilder nur für den Lauf; sie kommen nicht ins Modell-Release.
* Bilder ohne Personen (Tiere, leere Fehlalarme) dürfen auch nach `ki_training/echt/` (klein halten, höchstens 20 MB)
  oder als ZIP mit einem Namen, der mit `echt` beginnt, ins Release «ki-daten».

### 3. Echtbild-Prüfsatz (messen statt trainieren)

Ein fester Satz beantworteter Bilder, gegen den GitHub MoveEyes KI misst (Actions → «Prüfsatz»: Personen gefunden /
verpasst / Fehlalarme je Modell, ohne Simulator). Export auf dem Pi: `python3 ki_training/pruefsatz.py exportieren`.
Gleicher Datenschutz wie oben (echte Personen nur privat über das Secret `PRUEFSATZ_URL`). Siehe
[`pruefsatz/LIESMICH.md`](pruefsatz/LIESMICH.md). Bilder, mit denen gemessen wird, nicht auch zum Trainieren verwenden.

## Was dabei herauskommt

* `moveeye_model.onnx` – das Netz (Eingang 1 × 3 × 320 × 320, RGB 0…1, mit grauem Rand auf ein Quadrat gebracht;
  Ausgabe 1 × 7 × 2100 = 4 Rahmen-Werte + 3 Klassen für 2100 Ankerpunkte). Etwa 12 MB.
* `moveeye_model.json` – das Manifest:
  `{"format": "moveeye-model-1", "version", "classes": ["person","animal","vehicle"], "input": 320, "file", "sha256",
  "size", "conf": {"person": 0.31, …}, "metrics": {"map50", "map50_95", "precision", "recall", "per_class", "val_images"},
  "made", "base", "epochs", "images", "check"}`.
  MoveEye lädt zuerst das Manifest, dann die ONNX-Datei, und nimmt sie nur, wenn die **sha256** stimmt.
  `conf` ist die Schwelle mit dem besten F1-Wert je Klasse; MoveEye setzt sie dem Regler-Wert 0,5 gleich.
* `bericht.md` – die Zusammenfassung (auch im Lauf auf GitHub zu sehen).
* `auswertung.md` – «Wo versagt die KI?» (siehe oben), auch als Datei im Release.

Vor dem Veröffentlichen prüft das Training die ONNX-Datei mit OpenCV (`cv2.dnn.readNetFromONNX`) – genau so, wie der Pi
sie lädt. Export mit ONNX-Opset 12, damit auch ältere OpenCV-Versionen (ab 4.5) sie lesen können.

## Lokal ausprobieren (für Entwickler)

```
pip install ultralytics opencv-python-headless onnx onnxslim
python3 ki_training/trainieren.py --pakete ki_training/pakete --echt ki_training/echt --epochen 5 --aus ausgabe
python3 ki_training/trainieren.py --nur-daten      # nur den Datensatz zusammenstellen (ohne ultralytics)
python3 ki_training/trainieren.py --probe-auswertung   # Datensatz + Auswertung mit erfundenen Funden (ohne ultralytics)
```
