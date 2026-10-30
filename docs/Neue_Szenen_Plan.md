# Neue Simulator-Szenen (Entscheide Daniel, 30.10.2026 09:58)

Ziel: Szenen, die gezielt Schwächen von MoveEye üben; je ein fester **Prüfstand-Lauf** und eine **Spiel-Szene** (Runden liefern schwierige Fälle fürs Lernen).

## Gewählt
1. **Voller Campingplatz** – viele harmlose Nachbarn bewegen sich auf ihren Plätzen und Wegen; nur wer an *deinen* Platz kommt, zählt (übt Zonen / «Dein Platz», Relevanz statt jede Bewegung). Spiel: Schleicher mischen sich unter die Nachbarn.
2. **Tarnen und Kriechen** – Tarnkleidung (Farbe wie Untergrund), Robben am Boden, Schirm / Karton als Versteck (schwierige Haltungen). Spiel: Tarn-Ausrüstung als Werkzeug der Schleicher.
3. **Velodieb** – schnell rein, Velo greifen (Velo-Tag-Sensor), weg (Reaktionszeit). Spiel: Dieb gegen Wächter auf Zeit.

## Einbau
- Prüfstand: je ein fester Testlauf (feste Zufallszahlen), Kennzahlen echte Pushes richtig / falsch und Reaktionszeit.
- Spiel: als Szene wählbar mit passender Spielidee.

## Zurückgestellt (nicht gewählt)
Sturmnacht, Insekten am IR-Licht, Scheinwerfer-Strasse, Hof mit Haustieren, Winter / Nebel, Dämmerung / Spiegelungen.

Reihenfolge: nach Weitwinkel-Kamera; parallel oder nach dem Verfolgungs-Parcours (`docs/Verfolgungs_Parcours.md`).

## Umgesetzt (Branch wt-szenen, 30.10.2026 – Entwurf, Version vergibt der Lead)
- Alle drei Szenen in `simulator3d/scripts/szenenplus.gd` (Details: `simulator3d/UEBERGABE.md`, «NEU (Entwurf): Neue Szenen»).
- Prüfstand: Pläne `camping_voll`, `tarnen`, `velodieb` (eigene Szene, feste Zufallszahlen; Pushes richtig / falsch,
  Reaktion ab Platz bzw. ab Griff, Pushes wegen Nachbarn) – nicht in «quick», sonntags mit den grossen Läufen
  (`.github/workflows/pruefstand.yml`) oder von Hand (`pruefstand/LIESMICH.md`).
- Spiel: im Spiel-Assistenten die Karte «Spiel zur Szene» (Unter den Nachbarn · Tarnen und Kriechen · Velodieb gegen Wächter),
  gleiche Regeln und Werkzeuge wie sonst (gameplus.gd / gamerules.gd / gametools.gd).
- MoveEye: Szenen-Namen in allen Sprachen (Teil 551, Kacheln 139 / 549, Simulator-Seite 470), Anleitung (Erkennung).
