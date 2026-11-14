# Morse-Empfang mit Ton: gemessene Grenzen (synthetisches Mikrofon)

Erzeugt mit `python3 werkzeuge/morse_test.py --quelle --messen-ton --tabelle docs/Morse_Messung_Ton.md`. Text «PARIS QTH BERN 59», 2 Läufe pro Feld.
Ton 660 Hz (der Ton von MoveEye) als 16-kHz-Signal, weisses Rauschen. «dB» = Ton zu Rauschen im Band 300–3000 Hz.
Zahl = Zeichenfehler in % (0 = alles richtig, 100 = nichts gelesen).

**Nicht gemessen: echtes Mikrofon, echter Raum (Hall), echter Wind, echte Stimmen, echtes Funkgerät.**

## Direkt (Ton nahe am Mikrofon)

| Ton zu Rauschen | 5 WPM | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM | 30 WPM |
|---|---|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +10 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +6 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +3 dB | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| +0 dB | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| -3 dB | 100 | 50 | 50 | 7 | 0 | 54 | 21 |
| -6 dB | 100 | 100 | 100 | 100 | 100 | 100 | 100 |

## Pfiff (1500 Hz, Tonhöhe wandert ±6 %, Lautstärke schwankt ±30 %)

| Ton zu Rauschen | 5 WPM | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM | 30 WPM |
|---|---|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| +10 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +6 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +3 dB | 0 | 0 | 57 | 7 | 0 | 0 | 21 |
| +0 dB | 4 | 11 | 61 | 100 | 7 | 18 | 100 |

## Handtastung ±30 %

| Ton zu Rauschen | 5 WPM | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM | 30 WPM |
|---|---|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| +10 dB | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| +6 dB | 0 | 0 | 0 | 0 | 0 | 14 | 18 |
| +3 dB | 0 | 0 | 0 | 0 | 0 | 0 | 21 |

## Über ein FM-Handfunkgerät, Träger bleibt, der Ton (800 Hz) wird getastet

| Ton zu Rauschen | 5 WPM | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM | 30 WPM |
|---|---|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +10 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +6 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +3 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +0 dB | 0 | 0 | 0 | 0 | 0 | 4 | 0 |

## Über ein FM-Handfunkgerät, der Träger wird getastet (Rauschsperre: 40 ms zu spät offen, 120 ms Rauschschwanz)

| Ton zu Rauschen | 5 WPM | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM | 30 WPM |
|---|---|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0 | 100 | 100 | 86 | 86 |
| +10 dB | 0 | 0 | 0 | 100 | 100 | 86 | 86 |
| +6 dB | 0 | 0 | 0 | 100 | 100 | 86 | 86 |
| +3 dB | 0 | 0 | 0 | 100 | 100 | 93 | 86 |
| +0 dB | 0 | 0 | 50 | 100 | 100 | 100 | 86 |

## Mit einem Pieper daneben (1250 Hz, 2 × pro Sekunde)

| Ton zu Rauschen | 5 WPM | 8 WPM | 12 WPM | 15 WPM | 20 WPM | 25 WPM | 30 WPM |
|---|---|---|---|---|---|---|---|
| +20 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +10 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +6 dB | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Funkkanal im Test: Bandpass 300–3000 Hz, die Lautstärke-Regelung hebt in den Pausen das Rauschen an, etwas Empfänger-Rauschen.
Bei getastetem Träger fehlen jedem Zeichen-Element die ersten 40 ms: bei 15 WPM ist ein dit nur 80 ms lang - darum ist dort früher Schluss.

## Daraus: die Grenze für die Anzeige

| | liest fehlerfrei bis |
|---|---|
| direkt, +6 dB | 30 WPM |
| direkt, 0 dB | 25 WPM |
| Funkgerät, Ton getastet, +6 dB | 30 WPM |
| Funkgerät, Träger getastet, +6 dB | 12 WPM |

Die Seite verspricht «liest bis etwa **20 WPM**», wenn der Ton deutlich lauter ist als die Umgebung (ab etwa +6 dB). Die Messung hält das ein (direkt und über das Funkgerät mit getastetem Ton).
Mit getastetem Träger geht es langsamer (siehe Tabelle) - das steht so in der Hilfe nicht, weil ein Funkgerät noch nicht angeschlossen ist.
