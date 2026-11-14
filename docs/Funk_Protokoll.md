# Eigenes Protokoll (2 Töne): Verträglichkeit mit der Seite «Morse-Funk» des Besitzers - gemessen

Erzeugt mit `python3 werkzeuge/funk_test.py --messen --tabelle docs/Funk_Protokoll.md`. Text «TREFFEN UM 15 UHR BEI DER BRUECKE?» (34 Zeichen), 2 Läufe pro Feld,
mit Schlüssel «geheim». Zahl = Anteil fehlerfrei gelesener Nachrichten (1 = alle, 0 = keine). «dB» = Ton zu Rauschen im Band 300–3000 Hz.
MoveEye → Seite: Ton aus MoveEyes Lautsprecher-Code → **sein Decoder** (node, 48 kHz). Seite → MoveEye: Ton nach **seiner Funktion transmit** → MoveEye (16 kHz).

**Nicht gemessen: echte Handys, echte Lautsprecher und Mikrofone, echtes Funkgerät, Raum, Wind.**

## Direkt (Handy-Lautsprecher nahe am Mikrofon) – MoveEye → seine Seite

| Ton zu Rauschen | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| +20 dB | 1 | 1 | 1 | 1 | 1 |
| +10 dB | 1 | 1 | 1 | 1 | 1 |
| +6 dB | 1 | 1 | 1 | 1 | 1 |
| +3 dB | 1 | 1 | 1 | 1 | 1 |
| +0 dB | 1 | 1 | 1 | 1 | 1 |

## Direkt (Handy-Lautsprecher nahe am Mikrofon) – seine Seite → MoveEye

| Ton zu Rauschen | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| +20 dB | 1 | 1 | 1 | 1 | 1 |
| +10 dB | 1 | 1 | 1 | 1 | 1 |
| +6 dB | 1 | 1 | 1 | 1 | 1 |
| +3 dB | 1 | 1 | 1 | 1 | 1 |
| +0 dB | 1 | 1 | 1 | 1 | 1 |

## Über ein FM-Handfunkgerät, Träger bleibt (Ton getastet) – MoveEye → seine Seite

| Ton zu Rauschen | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| +20 dB | 0 | 1 | 1 | 0.5 | 1 |
| +10 dB | 1 | 1 | 1 | 1 | 1 |
| +6 dB | 1 | 1 | 1 | 1 | 1 |
| +3 dB | 0.5 | 1 | 1 | 1 | 1 |
| +0 dB | 0.5 | 1 | 1 | 1 | 1 |

## Über ein FM-Handfunkgerät, Träger bleibt (Ton getastet) – seine Seite → MoveEye

| Ton zu Rauschen | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| +20 dB | 0 | 0.5 | 1 | 1 | 0.5 |
| +10 dB | 1 | 1 | 1 | 1 | 1 |
| +6 dB | 1 | 1 | 1 | 1 | 1 |
| +3 dB | 1 | 1 | 1 | 1 | 1 |
| +0 dB | 1 | 0 | 1 | 1 | 1 |

## Über ein FM-Handfunkgerät, Sendetaste für die ganze Nachricht (Rauschsperre 40 ms spät, 120 ms Rauschschwanz) – MoveEye → seine Seite

| Ton zu Rauschen | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| +20 dB | 0 | 0.5 | 1 | 1 | 1 |
| +10 dB | 1 | 0.5 | 1 | 1 | 1 |
| +6 dB | 0.5 | 0.5 | 1 | 1 | 1 |
| +3 dB | 0.5 | 0.5 | 1 | 1 | 1 |
| +0 dB | 0.5 | 0.5 | 1 | 1 | 1 |

## Über ein FM-Handfunkgerät, Sendetaste für die ganze Nachricht (Rauschsperre 40 ms spät, 120 ms Rauschschwanz) – seine Seite → MoveEye

| Ton zu Rauschen | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0.5 | 1 | 1 |
| +10 dB | 1 | 1 | 1 | 0.5 | 1 |
| +6 dB | 1 | 1 | 1 | 0.5 | 1 |
| +3 dB | 1 | 1 | 1 | 0.5 | 1 |
| +0 dB | 1 | 1 | 1 | 0.5 | 1 |

## Tempo nicht gleich eingestellt (Empfänger steht auf 12 WPM, direkt, +20 dB)

| Sender | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM |
|---|---|---|---|---|---|
| MoveEye → Seite | 1 | 1 | 1 | 0 | 0 |
| Seite → MoveEye | 1 | 1 | 1 | 0 | 0 |

## Was das heisst

* **Direkt** (Handy-Lautsprecher am Mikrofon): beide Richtungen, mit und ohne Schlüssel, 8–25 WPM bis 0 dB fehlerfrei.
* **Tempo gleich einstellen.** Seine Seite (und MoveEye, das genau so liest) schätzt den Anfang nach dem eingestellten Tempo und lernt
  das wirkliche Tempo erst aus den ersten Zeichen. Ist der Sender viel schneller als eingestellt, sind die ersten Zeichen falsch, und
  MoveEye erkennt den Start-Ton nicht (siehe Tabelle «Tempo nicht gleich»). Auf beiden Seiten dasselbe Tempo wählen.
* **Über das Funkgerät** (nachgebaut, mit einer Lautstärke-Regelung, die das Rauschen in den Pausen anhebt – eher schlechter als ein echtes
  Gerät): 15–25 WPM fast immer fehlerfrei; bei 8–12 WPM einzelne falsche Zeichen (lange Pausen: das angehobene Rauschen liegt nahe bei
  einem der Töne und täuscht seinen Ton-Erkenner). Das ist sein Decoder – MoveEye liest absichtlich gleich.
* **Mit Schlüssel geht ein verlorenes Zeichen weiter:** der Schlüsselstrom zählt die Zeichen; fehlt eines (oder kommt eines dazu), ist der
  Rest der Nachricht Unsinn. Ohne Schlüssel bleibt es ein einzelner Fehler. Für eine spätere Fassung: Zeichen nummerieren oder neu
  ansetzen.
* **Später: echte Verschlüsselung.** Platz dafür, ohne das jetzige Protokoll zu brechen: das erste Zeichen einer Nachricht mit dem Code
  `.-.-` (kommt in den 39 Zeichen nicht vor) heisst «neueres Format, danach ein Versionsbyte». Seine Seite zeigt dann «□» und Unsinn (kein
  Absturz), MoveEye zeigt «neueres Format – dieses MoveEye kann es nicht lesen».
* Der Schlüssel **verschleiert** nur (jede Nachricht nutzt dieselbe Folge) – keine starke Verschlüsselung. Im Amateurfunk ist
  Verschlüsselung verboten (ITU-Vollzugsordnung Funk Nr. 25.2A; BAKOM: digitale Übertragungen nur unverschlüsselt).

