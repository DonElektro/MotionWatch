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
