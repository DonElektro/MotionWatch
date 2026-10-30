#@ MoveEye – Teil 564: Übersetzungen (DE / FR / IT / RM) zum Aufräumen 2 (Schnittstelle, Übungen mit dem Simulator, Akku-Grösse von MoveEye, Spiel-Anzeigen, «In 3D nachspielen»). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_AUFR2 = {
    'Replay in 3D': ('In 3D nachspielen', 'Rejouer en 3D', 'Rivivere in 3D', 'Reproducir en 3D'),
    'replay-3d-tip': ('Zeigt im 3D-Simulator, wer woher kam und wohin MoveEye geschaut hat (15 s vor bis 20 s nach dem Alarm). Braucht den verbundenen Simulator.',
                      'Montre dans le simulateur 3D qui est venu d’où et où MoveEye regardait (15 s avant à 20 s après l’alarme). Il faut le simulateur connecté.',
                      'Mostra nel simulatore 3D chi è arrivato da dove e dove guardava MoveEye (da 15 s prima a 20 s dopo l’allarme). Serve il simulatore collegato.',
                      'Mussa en il simulatur 3D tgi è vegnì danunder e nua che MoveEye ha guardà (15 s avant fin 20 s suenter l’alarm). Dovra il simulatur collià.'),
    'plays in the window of the simulator': ('läuft im Fenster des Simulators', 'joue dans la fenêtre du simulateur', 'in riproduzione nella finestra del simulatore', 'gira en la fanestra dal simulatur'),
    'from MoveEye (setting of MoveEye, only shown here)': ('von MoveEye (Einstellung von MoveEye, hier nur angezeigt)', 'de MoveEye (réglage de MoveEye, seulement affiché ici)',
                                                           'da MoveEye (impostazione di MoveEye, qui solo mostrata)', 'da MoveEye (parameter da MoveEye, qua mo mussà)'),
    'at the goal': ('im Ziel', 'à l’arrivée', 'al traguardo', 'en la finamira'),
    'in jail': ('gefangen', 'en prison', 'in prigione', 'en praschun'),
    'on the way': ('unterwegs', 'en route', 'in cammino', 'en viadi'),
    'points': ('Punkte', 'points', 'punti', 'puncts'),
    'Get ready': ('Macht euch bereit', 'Préparez-vous', 'Preparatevi', 'Pinai vus'),
}
for _k, _v in _HX_AUFR2.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- the manual (HELP_PAGE of 540): one paragraph in «System & network» (after the one of 598), German and English ----
_AUFR2_HELP = {
    "de": "<p><b>🧪 Simulator: ein Weg für jeden Wert (Aufräumen 2):</b> Die Übungen «Akku leer» und «WLAN / Internet weg» stellen bei "
          "verbundenem Simulator nur noch dessen Regler (Ladung, Netzteil, «Internet weg») – MoveEye liest die Werte wie sonst; ohne diese "
          "Werte rechnet die Übung wie bisher selbst. Die <b>Akku-Grösse</b> kommt aus MoveEye (Einstellung «USV-Akku: Kapazität EINER 18650-Zelle»): "
          "der Simulator zeigt sie bei Verbindung nur an («von MoveEye»). <b>Einfach / Experte</b> der Simulator-Steuerung gilt jetzt für alle "
          "Geräte (in den Einstellungen von MoveEye gespeichert, wie auf der Hauptseite). Die Luftfeuchtigkeit der Szene geht in den Klima-Sensor; "
          "Schutz an / aus und die Relais von MoveEye stehen in der Statuszeile des Simulators. <b>Spiel-Anzeigen:</b> TV-Anzeige am HDMI, "
          "TV-Modus des Simulators und die SmallTV-Seite «Spiel» zeigen dieselben Zahlen aus einer Quelle (Runde, Zeit, Spieler, Punkte, "
          "Rangliste, Sieger). <b>⏪ In 3D nachspielen</b> gibt es jetzt auch in der Zeitleiste und bei den Aufnahmen, wenn zum Alarm eine Spur "
          "gespeichert ist. Für Entwickler: alle Felder zwischen MoveEye und Simulator stehen in <code>simulator3d/schnittstelle.json</code>; "
          "der Selbsttest und der Simulator prüfen beim Start, dass beide Seiten dazu passen.</p>",
    "en": "<p><b>🧪 Simulator: one way for every value (clean-up 2):</b> with the simulator connected, the drills «battery empty» and "
          "«Wi-Fi / internet gone» only set its controls (charge, mains adapter, «internet gone») – MoveEye reads the values as usual; without "
          "these values the drill calculates by itself as before. The <b>battery size</b> comes from MoveEye (setting «UPS HAT: capacity of ONE 18650 "
          "cell»): the simulator only shows it while connected («von MoveEye»). <b>Simple / Expert</b> of the simulator control now counts for "
          "every device (stored in the settings of MoveEye, like on the main page). The humidity of the scene goes into the climate sensor; "
          "protection on / off and the relays of MoveEye are in the status line of the simulator. <b>Game displays:</b> the TV view on the HDMI, "
          "the TV mode of the simulator and the SmallTV page «Game» show the same numbers from one source (round, time, players, points, "
          "ranking, winner). <b>⏪ Replay in 3D</b> is now also in the timeline and the recordings when a track was saved for the alarm. For "
          "developers: every field between MoveEye and the simulator is listed in <code>simulator3d/schnittstelle.json</code>; the self-test "
          "and the simulator check at the start that both sides match.</p>",
}
for _a, _b in (('<section id="system" data-icon="⚙"><h2>System &amp; Netz</h2>', _AUFR2_HELP["de"]),
               ('<section id="system" data-icon="⚙"><h2>System &amp; network</h2>', _AUFR2_HELP["en"])):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
