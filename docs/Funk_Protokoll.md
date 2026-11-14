# Eigenes Protokoll (2 Töne): Verträglichkeit mit der Seite «Morse-Funk» des Besitzers - gemessen

Erzeugt mit `python3 werkzeuge/funk_test.py --messen --tabelle docs/Funk_Protokoll.md`. Text «TREFFEN UM 15 UHR BEI DER BRUECKE?» (34 Zeichen), 2 Läufe pro Feld,
mit Schlüssel «geheim» (Tabelle vom 14.11.2026, noch mit dem alten Schlüssel V1 gemessen; V2 hat dieselben Töne und 13 Zeichen mehr). Zahl = Anteil fehlerfrei gelesener Nachrichten (1 = alle, 0 = keine). «dB» = Ton zu Rauschen im Band 300–3000 Hz.
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
* **Mit Schlüssel (V2) zählt jedes Zeichen:** fehlt eines oder ist eines falsch, stimmen die Prüfzeichen nicht – die Nachricht heisst dann
  «falscher Schlüssel oder gestört» (statt Unsinn). Ohne Schlüssel bleibt es ein einzelner falscher Buchstabe. V2 ist 13 Zeichen länger.
* Im Amateurfunk ist Verschlüsselung verboten (ITU-Vollzugsordnung Funk Nr. 25.2A; BAKOM: digitale Übertragungen nur unverschlüsselt).
  Mit Schlüssel nie über Amateurfunk senden.

## V2: Nachrichten mit Schlüssel (Besitzer 14.11.2026: «nur noch V2»)

Ohne Schlüssel ändert sich nichts (Bit für Bit seine Seite «Morse-Funk»). Mit Schlüssel geht **jede** Nachricht so (V1, der feste
SHA-256-Strom seiner Seite, ist weg):

| Teil | Zeichen | Inhalt |
|---|---|---|
| Version | 1 | Code `.-.-` (kommt in den 39 Zeichen nicht vor; seine alte Seite zeigt «□») |
| Nonce | 6 | zufällig aus den 39 Zeichen (Seite: `crypto.getRandomValues`, Bytes < 234 → Byte mod 39; MoveEye: `secrets`) – rund 31.7 Bit |
| Text | n ≤ 200 | Klartext (nur die 39 Zeichen, vorne / hinten ohne Leerzeichen), Zeichen i um s<sub>i</sub> verschoben |
| Prüfung | 6 | aus den 38 Zeichen ohne Leerzeichen (der Empfänger kürzt das Ende) – rund 31.5 Bit |

* Schlüssel: `dk = PBKDF2-HMAC-SHA256(Schlüssel als UTF-8, Salz "MoveEye-Funk-v2", 200 000 Runden, 64 Bytes)`, `kE = dk[0:32]`,
  `kM = dk[32:64]`. Einmal pro Schlüssel gerechnet (Seite: beim Einstellen, MoveEye: im Speicher, nur der SHA-256 als Merkzeichen).
* Strom: für Zähler c = 0, 1, …: `HMAC-SHA256(kE, Nonce als ASCII ‖ c als 4 Bytes big endian)`; jedes Byte b < 234 gibt `b mod 39`.
  Geheimtext-Zeichen i = `ALPHA[(Index(Klar i) + s_i) mod 39]`.
* Prüfung: `h = HMAC-SHA256(kM, 0x02 ‖ Nonce ‖ Geheimtext)` (ASCII); jedes Byte b < 228 gibt `TAG[b mod 38]` (`TAG` = die 39 Zeichen ohne
  Leerzeichen), bis 6 Zeichen da sind (sonst `h = HMAC-SHA256(kM, h)` und weiter).
* Empfang: erstes Zeichen = Versionszeichen → Nonce, Geheimtext, Prüfung trennen; Prüfung falsch → «falscher Schlüssel oder gestört»;
  kein Schlüssel eingestellt → «verschlüsselt – hier ist kein Schlüssel eingestellt». Derselbe Text klingt jedes Mal anders (Nonce).
* Testvektoren (Seite in node = MoveEye, `funk_test.py` Teil B, Selbsttest `FUNK_V2_VEKTOREN`): Schlüssel `geheim`, Nonce `ABC12.`,
  Text `TREFFEN UM 15 UHR` → `ABC12.N?.4R8USIXLEETRJ1VONQ0F` (nach dem Versionszeichen).
* Grenzen: kein geprüftes Verfahren; 6 Prüfzeichen sind rund 32 Bit – genug gegen Störungen und Raten, nicht gegen einen grossen Angriff.
  Die Nonce ist kurz (31.7 Bit): bei vielen tausend Nachrichten mit demselben Schlüssel kann sie sich wiederholen.

## Audiodateien

* **Als Audiodatei:** die Nachricht als WAV (Mono, 16 Bit, 22 050 Hz, 0.5 s Vorlauf, 0.6 s Nachlauf), genau die Töne von transmit
  (Seite: `beepsOf` = transmit, geprüft) bzw. von MoveEyes Lautsprecher (`funk_wav_bytes`). iPhone: Teilen-Blatt (`navigator.share`),
  sonst Herunterladen; in MoveEye der übliche Download (in der App das Teilen-Blatt).
* **Audiodatei einlesen:** Seite: der Browser dekodiert (`decodeAudioData`, auf 48 kHz umgerechnet; Safari: WAV, M4A/AAC, MP3 –
  Ogg/Opus meist nicht), dann sein Decoder schneller als Echtzeit (`decodeSamples`). MoveEye: WAV selbst, M4A/MP3/Ogg mit ffmpeg,
  16 kHz, `FunkRx` bzw. `MorseAudio` wie am Mikrofon. Höchstens 10 Minuten. Im Verlauf mit 📁.
