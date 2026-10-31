# Erkennungstest 3 – Zwischenstand (gedrosselt, 31.10.2026 21:15)

Auf Wunsch von Daniel angehalten. Alle eigenen Prozesse (Simulator :9283, MoveEye :5183, Xvfb :183, Monitore) sind beendet.
Zweig: `real-erkennung-personen` (Worktree `/tmp/claude-0/wt_erk3`). Werkzeuge im Zweig unter `erkennungstest3/`.

## Was schon gemessen ist

- **Noch keine Messung mit Ergebnis.** Die Ursachen-Läufe (Varianten a / c / alle) waren aufgesetzt und gestartet. Sie warteten
  aber an der Lastschwelle 3, weil andere Simulatoren liefen (Last 5–9). Darum gibt es noch keinen einzigen gemessenen Fall.
- Fertig vorbereitet:
  - Testbau mit Regel-Schaltern (nur Test, nicht im Zweig-Code): `/tmp/claude-0/wt_erk3t` (main 3.13.0 + `testschalter.patch`).
    Umgebungsvariable `MW_ERK_AUS=fixp,tier,veto,strict,zoom,nebel,kriech,m3,tveh` oder `alle`.
  - Referenz 2.98.110: `/tmp/claude-0/erkt3/v298/webcam_bewegung_2_98_110.py`
  - Gleiche Start-Einstellungen für jede Variante: `/tmp/claude-0/erkt3/mw_tpl` (Test-2-Einstellungen, aber Auto-Tune auf
    Werkswerte: sensitivity 50, min_area 1500, speed_consistency 0.4, walk_frames 6; Test-Postfach an).
  - Fälle: `sel_ursache.txt` = die 14 in Test 1 erkannten, in Test 2 verpassten Personenfälle + 6 Gegenproben (Tier/Auto),
    je Bedingung zuerst «leer» mit Wind 55 wie in Test 2. Richtung je Fall fest (gleich in allen Varianten).
  - Simulator: derselbe wie Test 2 (wt_erk2, Sim 3.8.0).

## Welche Ursache sich abzeichnet (aus Code und Rohdaten von Test 1/2, noch nicht gemessen)

1. **Test 1 und Test 2 starteten nicht gleich.** Test 2 übernahm die End-Einstellungen von Test 1 (Auto-Tune). Dadurch:
   min_area nach der Kalibrierung 2400–3400 statt ~600 (4–5× grösser), speed_consistency 0.6–0.7 statt 0.4–0.5,
   später sensitivity bis 28. Bewegungs-Spuren einer Person zählen dann kaum noch («zu klein», «nicht stetig»).
   Der Tuner zieht speed_consistency bei jeder erkannten Person an («persons detected, tightening», bis 0.7) und nie zurück –
   das passiert auch auf einem echten Gerät mit vielen Besuchern.
2. **Strenge Regel «Wind» (E2, Teil 411) bleibt 10 Min. an:** `wind_strong()` nimmt die stärkste Böe der letzten 10 Min.
   (Teil 280). Nach dem Leerlauf mit 55 km/h ist jede folgende Person 10 Min. lang «Wind» (Stellplatz-Fälle: strict n=2,
   why=wind, obwohl Wind 12 km/h). Bei 2–3 Bildern/s und KI alle ~3 s schafft eine Person die «2 Treffer in Folge»
   oft nicht (eine Lücke zurücksetzt nach 2 Bildern ohne Treffer).
3. In mehreren verpassten Fällen sah die KI eine Person («person» in present), aber keine Spur wurde Person –
   Verdacht: 2. (strict) oder «Tier vor Person» (E1, `animal_track_decide`); zu prüfen mit Variante tier/strict.
4. Last: Test 2 lief bei 2–5 Bildern/s, KI-Lauf ~1.2 s → weniger KI-Treffer. Anteil noch offen (Variante a bei Last < 3).

## Nebenfunde (Abklärung)

- **Tier-Pushes (4):** gewollt ist es so nicht ausdrücklich, aber es gibt kein Ereignis «Tier». «Was wird gemeldet:
  Personen + Tiere» (`push_level`, Teil 579a) lässt nur «warm» (Wärmebild-Alarm, `thermal_alarm`, ab Werk aus) durch.
  Ein von der KI erkanntes Tier erzeugt nie einen Push. Vorschlag (nicht gebaut): neues Ereignis «animal» (KI-Tier
  oder Wärmebild-Tier) mit eigener Pause, nur bei Stufe «Personen + Tiere» / «Alles».
- Kopf-Verfolgung (2): im Test-2-Fall wurde die Person gar nicht erkannt (fps 2, Last 6) → nichts zu verfolgen; erneut prüfen.
- Scheinwerfer (1) und Wind-Fehlalarme (3): noch nicht untersucht (Plan: Fall mit `MW_DEBUG_TRACKS` nachstellen).

## So geht es später weiter

```bash
cd /tmp/claude-0/erkt3/tools
# Testbau neu, falls main weiter ist: Worktree wt_erk3t auf main, testschalter.patch anwenden, python3 werkzeuge/bauen.py
VARIANTS="a c alle" bash all.sh run_ursache.sh          # danach z. B. VARIANTS="strict tier fixp zoom veto"
```
Ergebnisse: `/tmp/claude-0/erkt3/out/<variante>/results.jsonl` (Driver ist fortsetzbar). Lastschwelle 3 (`LOADMAX`).
Danach: Fix (Ideen: Wind-Regel nur bei aktuellem Wind 60 s statt 10-Min.-Böe; strict als «Person?» melden statt verwerfen;
Tuner-Anziehen begrenzen/zurückstellen), dann Test 3 mit allen 72 Fällen + neue Orte.
