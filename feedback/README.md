# Rückmeldungen aus den Testläufen

Hier landen die Berichte der Testläufe aus Motion Watch (Reiter **Simulator → Testlauf und Optimierung →
«📦 Bericht für die Entwicklung»**). Die ZIP-Datei enthält:

- `testlauf_bericht.json`: Versionen (Motion Watch, Simulator), Erkennungs-Einstellungen, Ergebnisse pro Phase,
  Fehlalarme mit Ursache, verpasste Personen mit Grund, Vergleich mit der vorherigen Version
- `bilder/`: was Motion Watch im Moment jedes Fehlers gesehen hat (klein, mit den Markierungen)

Keine Passwörter, Schlüssel, Adressen oder Aufnahmen.

**Hochladen:** auf GitHub in diesen Ordner ziehen («Add file → Upload files»), Name so lassen.
Oder einfach im Chat mit Claude anhängen.

**Für Claude:** Vor Änderungen an der Erkennung die neuesten Berichte hier lesen (`git pull`), die Bilder ansehen und
die Vorschläge in `opt_suggest()` bzw. die Filter danach ausrichten. Erledigte Berichte nach `feedback/erledigt/`
verschieben und in der Commit-Nachricht kurz sagen, was daraus geworden ist.

## Spielberichte aus dem 3D-Simulator (ab 3D-3.52)

`feedback/spiel/spielbericht_*.zip` kommt aus dem Simulator (Spiel → Erkennung lernen → «Spielberichte senden»).
Pro Runde ein Ordner mit `spielbericht.json` (wie lange ein sichtbarer Spieler bis zur Meldung brauchte: Abstand,
Haltung, Licht; Treffer und Fehlschüsse des Jägers), `verpasst_NN.jpg` (Bild der Kopfkamera, Rahmen des Spielers in
`verpasst[].box` als 0..1) und `schleichweg_*.json` (Weg eines unerkannten Spielers). Gute Schleichwege nach
`simulator3d/spielwege/` kopieren: dann laufen sie im Prüfstand (Plan «spielwege») bei allen mit.
