# Gameplay ausfeilen (Entscheide Daniel, 30.10.2026 21:35 – ergänzt 31.10.2026 01:58)

Reihenfolge: **nach** «Gegenstände + Umgebung» (wt-objekte) und den Angleichungen MoveEye ↔ Simulator
(Entwickler-Schalter teilen, «Dein Platz» klären, /sim zuklappen statt ausblenden, Fenster angleichen, gezeichnete Symbole).

## Gewählt (alle, Daniel 31.10. 01:58)
1. **Probe-Runde mit Blinki (30 s):** Ducken, Verstecken, 🎯 üben, bevor die echte Runde beginnt (überspringbar).
2. **Wiederholung beim Erwischen:** 3 s aus der Wächter-Sicht (nutzt «In 3D nachspielen» / Aufzeichnung der Runde).
3. **Höhepunkte am Schluss:** knappster Moment, längste Zeit unentdeckt, bester Schuss – kurzer Film.
4. **Missionen mit den neuen Gegenständen:** z. B. Portemonnaie vom Tisch holen, 5 Früchte sammeln, Paket wegbringen.
5. **Nacht-Spiel:** IR-Kegel / Wärmebild als Spielregel – nachts sieht der Wächter nur im Infrarot-Kegel oder im Wärmebild.
6. **Geräusche zählen:** Rennen und Schritte auf Kies machen Lärm, den der Wächter hört → Richtungs-Ping.
7. **Neue Werkzeuge** (mit Energie, eine Regel wie bisher): Schleicher – Lockmittel (Tiere lenken ab), in Gegenständen
   verstecken (Wäscheleine, Zelt); Wächter – kurzer Licht-Schwenk, Geräusch-Ping.
8. **Spielabend-Turnier · Fairness automatisch · «Bring MoveEye ins Schwitzen»:** mehrere Spieler nacheinander auf einem
   Gerät mit Punktetabelle und Siegerbild · Ausgleich, wenn eine Seite zu leicht gewinnt (offen angezeigt) · Spielziel,
   bei dem MoveEye möglichst viel zu tun bekommt, ohne dass man erwischt wird (nur Simulation, keine echten Alarme).
9. **KI-Turm:** Runde um Runde gegen den KI-Wächter, Stufe für Stufe schwerer; eigene Rangliste «gegen die KI».
10. **Abzeichen pro Szene:** kleine Ziele je Szene (z. B. «Unsichtbar im vollen Campingplatz», «Velodieb-Profi»).

(Früher «Nicht gewählt (vorerst)»: Nacht-Spiel, Geräusche zählen, Spielabend-Turnier, Fairness automatisch, «Bring MoveEye
ins Schwitzen» – am 31.10. 01:58 ebenfalls gewählt; Daniel hatte sie zuerst aus Versehen übersprungen.)

Umsetzung: Zweig `gameplay` (Bericht `REAL_GAMEPLAY.md` im Worktree). Code: `simulator3d/scripts/gamemore.gd` (Knoten für
alles Neue) und die Teile `gamemission.gd`, `gamenacht.gd`, `gameturnier.gd`, `gameturm.gd`, `gameziele.gd`.
