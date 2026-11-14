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

## Mehrton (MFSK): Spezifikation (Besitzer 14.11.2026)

Dritte Art neben Morse und dem 2-Ton-Protokoll, nur über den Ton, auf der Seite (Block `MFSK` in `FUNK_PAGE`) und in MoveEye
(Teil 639zzzh) Bit für Bit gleich (Testvektoren `MFSK_VEKTOREN`, `funk_test.py` Teil M).

| Vorlage | Töne | Frequenzen | Symbol / Schutz | Bit pro Symbol | roh |
|---|---|---|---|---|---|
| 1 | 4 | 800 + i · 250 Hz (800–1550) | 40 ms / 6 ms | 2 | 50 bit/s |
| 2 | 8 | 650 + i · 200 Hz (650–2050) | 50 ms / 8 ms | 3 | 60 bit/s |
| 3 | 16 | 500 + i · 150 Hz (500–2750) | 64 ms / 8 ms | 4 | 62.5 bit/s |
| 0 | Baukasten: 2–32 | Start + Abstand oder Liste, 300–3000 Hz | 10–500 ms (0.5-ms-Schritte) / 0 bis T/2 | floor(log2 n) | |

* **Symbol:** ein Ton für T ms, die Phase läuft durch (keine Klicks); Grenzen bei `round(j · T · Rate)`. Daten nutzen die ersten 2^k Töne,
  Gray-Code (Wert v → Ton `v ^ (v >> 1)`). Der Empfänger misst nur `[Start + Schutz, Start + T)` mit Hann-Fenster (DFT pro Ton).
  Prüfung des Baukastens: Abstand < 1/(T − Schutz) → geht nicht; < 2/(T − Schutz) → Warnung; n keine Zweierpotenz → Warnung.
* **Rahmen:** Vorspann 0.3 s (Ton 0 und Ton n − 1 abwechselnd: öffnet die Rauschsperre, stellt die Lautstärke-Regelung ein) · Sync 12 Symbole
  (Ton `a · n // 16`, a = 0 15 5 10 3 12 8 1 14 6 11 2) · Kopf 5 Bytes `[0x10 | Vorlage, FEC | Schlüssel << 2 | gepackt << 3, Länge,
  Prüfwert Baukasten (CRC-8 von "n|f·10;…|T·10|Schutz·10") oder 0, CRC-8]`, immer Faltungscode 1/2 (92 Bit) · Nutzdaten + CRC-16/CCITT-FALSE
  über Kopf (4 Bytes) und Nutzdaten, mit der gewählten Fehlerkorrektur, verschachtelt (Block: Spalten = ceil(√n), zeilenweise
  geschrieben, spaltenweise gelesen) · auf k Bit mit Nullen aufgefüllt · Nachlauf 3 Symbole Ton 0.
* **Fehlerkorrektur:** aus (roh) · leicht = Faltungscode K = 7 (171, 133 oktal) punktiert auf 3/4 (Muster 110110) · stark = derselbe Code,
  Rate 1/2. 6 Nullbits am Ende, Viterbi mit weichen Entscheidungen: pro Bit (max. Amplitude der Töne mit Bit 1 − mit Bit 0) / max. Amplitude.
* **Text:** nur die 39 Zeichen → gepackt (3 Zeichen in 2 Bytes: `i0·1521 + i1·39 + i2`; 2 Zeichen: `59319 + i0·39 + i1`; 1 Zeichen: 1 Byte),
  sonst UTF-8 (Gross / klein, Umlaute, Emoji). Höchstens 200 Zeichen und 255 Bytes Nutzdaten.
* **Schlüssel (V2 auf Bytes):** dieselben kE / kM (PBKDF2 wie oben); Nonce 4 Bytes zufällig; Strom `HMAC-SHA256(kE, "M" ‖ Nonce ‖ Zähler)`
  XOR; Prüfung `HMAC-SHA256(kM, 0x03 ‖ Kopf 4 Bytes ‖ Nonce ‖ Geheimtext)[0:4]` (32 Bit). Nutzdaten = Nonce ‖ Geheimtext ‖ Prüfung.
* **Empfang:** Energien aller Töne alle T/8; Sync = Mittel über die 12 Symbole von (Energie des Sync-Tons / Energie aller Töne) ≥
  1/n + 0.35 · (1 − 1/n), alle 12 über 1.5 × Rauschboden; das beste von 8 Nachbarn gilt. Takt nachgeführt (früh / spät, ±T/8). Alle
  Vorlagen gleichzeitig (der Kopf sagt, welche), der Baukasten nur, wenn eingestellt. Kopf falsch → weitersuchen; CRC-16 falsch →
  «gestört»; Prüfung falsch → «falscher Schlüssel oder gestört»; anderer Baukasten-Prüfwert → «andere Baukasten-Einstellungen».

<!-- MFSK-MESSUNG -->

## Mehrton (MFSK) – gemessen

Erzeugt mit `python3 werkzeuge/funk_test.py --mfsk-messen --tabelle docs/Funk_Protokoll.md`. Text «TREFFEN UM 15 UHR BEI DER BRUECKE?» (34 Zeichen, gepackt),
3 Läufe pro Feld, ohne Schlüssel. Zeichen/s = Textlänge durch die ganze Sendung (mit Vorspann, Sync, Kopf, CRC). «dB» wie oben
(Ton zu Rauschen im Band 300–3000 Hz). Funk = nachgebautes FM-Handfunkgerät (Sendetaste für die ganze Nachricht: Rauschsperre 40 ms
spät, 120 ms Rauschschwanz). Empfänger: MoveEye (16 kHz); die Seite liest gleich (Teil M der Tests).

| Art | Fehlerkorrektur | Zeichen/s | +10 dB | +5 dB | 0 dB | −6 dB | −10 dB | Funk +10 dB | Funk +3 dB |
|---|---|---|---|---|---|---|---|---|---|
| 4 Töne, 40 ms | aus | 5.0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 4 Töne, 40 ms | leicht | 4.1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 4 Töne, 40 ms | stark | 3.1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 8 Töne, 50 ms | aus | 5.7 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 8 Töne, 50 ms | leicht | 4.7 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 8 Töne, 50 ms | stark | 3.6 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 16 Töne, 64 ms | aus | 5.7 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 16 Töne, 64 ms | leicht | 4.7 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 16 Töne, 64 ms | stark | 3.6 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 Töne (Protokoll), 12 WPM | – | 0.9 | 1 | 1 | 1 | 0 | 0 | 1 | 1 |
| 2 Töne (Protokoll), 20 WPM | – | 1.4 | 1 | 1 | 1 | 0 | 0 | 1 | 1 |

**Was das heisst** (Messung vom 14.11.2026, je 3 Läufe – kleine Stichprobe):
* Mehrton ist bei gleichem Text 3–6 × schneller als das 2-Ton-Protokoll (3.1–5.7 statt 0.9–1.4 Zeichen/s) und liest noch bei −6 dB,
  wo das 2-Ton-Protokoll nichts mehr liest (jeder Ton liegt in einem schmalen Band; der Empfänger misst nur dort).
* Die Fehlerkorrektur kostet Zeit (leicht × 4/3, stark × 2 der Nutzdaten; Vorspann, Sync und Kopf bleiben gleich) und bringt ihren
  Gewinn nahe an der Grenze: bei −10 dB liest «aus» nichts mehr, «leicht» und «stark» alles. Zwischen leicht und stark zeigt diese
  Messung keinen Unterschied (stark sollte mehr einzelne Aussetzer aushalten – nicht gemessen). Vorgabe: 8 Töne, leicht.
* Über das nachgebaute Funkgerät (Sendetaste, Rauschsperre) bei +10 und +3 dB alles fehlerfrei. Nicht gemessen: echte Geräte, Raum, Wind.
<!-- /MFSK-MESSUNG -->
