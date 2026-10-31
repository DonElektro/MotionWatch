#@ MoveEye – Teil 599e: Übersetzungen und Anleitungs-Absatz zum Nacht-Testlauf (Teile 579b / 599d). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_nacht = {
    'Night test run': ('Nacht-Testlauf', 'Test de nuit', 'Test notturno', 'Test da notg'),
    'night test run': ('Nacht-Testlauf', 'test de nuit', 'test notturno', 'test da notg'),
    'Night test run (simulation)': ('Nacht-Testlauf (Simulation)', 'Test de nuit (simulation)', 'Test notturno (simulazione)', 'Test da notg (simulaziun)'),
    'Night test run: report': ('Nacht-Testlauf: Bericht', 'Test de nuit : rapport', 'Test notturno: rapporto', 'Test da notg: rapport'),
    'whole night with truth': ('ganze Nacht mit Wahrheit', 'nuit entière avec la vérité', 'notte intera con la verità', 'notg entira cun la vardad'),
    'Start night test run': ('Nacht-Testlauf starten', 'Lancer le test de nuit', 'Avvia il test notturno', 'Cumenzar il test da notg'),
    'Abort the night test run': ('Nacht-Testlauf abbrechen', 'Interrompre le test de nuit', 'Interrompi il test notturno', 'Interrumper il test da notg'),
    'Night test run is running': ('Nacht-Testlauf läuft', 'Le test de nuit est en cours', 'Il test notturno è in corso', 'Il test da notg è en funcziun'),
    'as now': ('wie jetzt', 'comme maintenant', 'come ora', 'sco ussa'),
    'Liveliness': ('Belebtheit', 'Animation', 'Movimento', 'Moviment'),
    'calm': ('ruhig', 'calme', 'tranquillo', 'quiet'),
    'normal (some going on)': ('normal', 'normal', 'normale', 'normal'),
    'lots going on': ('viel los', 'très animé', 'molto movimento', 'blera activitad'),
    'Tempo': ('Tempo', 'Vitesse', 'Velocità', 'Tempo'),
    'real (1×)': ('echt (1×)', 'réel (1×)', 'reale (1×)', 'real (1×)'),
    'fast (8 h in about 1 h)': ('schnell (8 Std. in etwa 1 Std.)', 'rapide (8 h en env. 1 h)', 'veloce (8 h in circa 1 h)', 'svelt (8 uras en var 1 ura)'),
    'Start time': ('Beginn', 'Début', 'Inizio', 'Entschatta'),
    'End time': ('Ende', 'Fin', 'Fine', 'Fin'),
    'not detected': ('nicht erkannt', 'pas détecté', 'non rilevato', 'betg identifitgà'),
    'Every night by itself': ('Jede Nacht von selbst', 'Chaque nuit automatiquement', 'Ogni notte da solo', 'Mintga notg sez'),
    'nacht-note': ('Eine ganze Nacht im Simulator: WC-Gänge (manche mit Taschenlampe), Katze, Fuchs, Igel, ein spätes Auto, eine Stunde Regen, Wind, Morgennebel und genau ein echter Vorfall zu zufälliger Zeit. Der Simulator kennt die Wahrheit; MoveEye vergleicht seine Alarme damit. Nur in der Simulation: Schutz «Voll» während des Laufs, Handy, Sirene und Relais bleiben still (Test-Postfach) – danach alles wie vorher. Am Morgen kommt der Bericht als Push (🧪 Simulation).',
                   'Une nuit entière dans le simulateur : passages aux WC (certains avec une lampe de poche), chat, renard, hérisson, une voiture tardive, une heure de pluie, du vent, du brouillard le matin et exactement un vrai incident à une heure au hasard. Le simulateur connaît la vérité ; MoveEye y compare ses alarmes. Seulement en simulation : protection «Voll» pendant le test, téléphone, sirène et relais restent muets (boîte de test) – ensuite tout comme avant. Le matin, le rapport arrive en push (🧪 simulation).',
                   'Una notte intera nel simulatore: visite al WC (alcune con la torcia), gatto, volpe, riccio, un’auto tardiva, un’ora di pioggia, vento, nebbia al mattino ed esattamente un vero incidente a un’ora casuale. Il simulatore conosce la verità; MoveEye vi confronta i suoi allarmi. Solo in simulazione: protezione «Voll» durante il test, telefono, sirena e relè restano muti (casella di prova) – poi tutto come prima. Al mattino il rapporto arriva come push (🧪 simulazione).',
                   'Ina notg entira en il simulatur: ir al WC (inqual cun glischina), giat, vulp, gieriun, in auto tard, in’ura plievgia, vent, tschajera la damaun ed exact in incident ver ad in’ura casuala. Il simulatur enconuscha la vardad; MoveEye cumpareglia ses alarms cun quella. Mo en la simulaziun: protecziun «Voll» durant il test, telefonin, sirena e relais restan quiets (chascha da test) – suenter tut sco avant. La damaun vegn il rapport sco push (🧪 simulaziun).'),
    'Open the report': ('Bericht öffnen', 'Ouvrir le rapport', 'Apri il rapporto', 'Avrir il rapport'),
    'No night test run yet.': ('Noch kein Nacht-Testlauf.', 'Encore aucun test de nuit.', 'Ancora nessun test notturno.', 'Anc nagin test da notg.'),
    'Incident detected': ('Vorfall erkannt', 'Incident détecté', 'Incidente rilevato', 'Incident identifitgà'),
    'after {s} s': ('nach {s} s', 'après {s} s', 'dopo {s} s', 'suenter {s} s'),
    'Misses': ('Verpasst', 'Manqués', 'Mancati', 'Mancads'),
    'Alarms in all': ('Alarme insgesamt', 'Alarmes au total', 'Allarmi in totale', 'Alarms en tut'),
    'repeats': ('Wiederholungen', 'répétitions', 'ripetizioni', 'repetiziuns'),
    'Incident': ('Vorfall', 'Incident', 'Incidente', 'Incident'),
    'Incident visible': ('Vorfall sichtbar', 'Incident visible', 'Incidente visibile', 'Incident visibel'),
    'visible for the camera after {s} s': ('für die Kamera sichtbar nach {s} s', 'visible pour la caméra après {s} s', 'visibile per la telecamera dopo {s} s', 'visibel per la camera suenter {s} s'),
    '{s} s visible': ('{s} s sichtbar', '{s} s visible', '{s} s visibile', '{s} s visibel'),
    'never visible for the camera': ('für die Kamera nie sichtbar', 'jamais visible pour la caméra', 'mai visibile per la telecamera', 'mai visibel per la camera'),
    'first detection after {s} s': ('erste Erkennung nach {s} s', 'première détection après {s} s', 'primo rilevamento dopo {s} s', 'emprima identificaziun suenter {s} s'),
    'no detection': ('keine Erkennung', 'aucune détection', 'nessun rilevamento', 'nagina identificaziun'),
    'first alarm after {s} s': ('erster Alarm nach {s} s', 'première alarme après {s} s', 'primo allarme dopo {s} s', 'emprim alarm suenter {s} s'),
    'no alarm': ('kein Alarm', 'aucune alarme', 'nessun allarme', 'nagin alarm'),
    'False alarms by cause': ('Fehlalarme nach Ursache', 'Fausses alarmes par cause', 'Falsi allarmi per causa', 'Fals alarms tenor la chaschun'),
    'none – fine': ('keine – gut', 'aucune – bien', 'nessuno – bene', 'nagins – bun'),
    'Misses (visible, nothing detected)': ('Verpasst (sichtbar, nichts erkannt)', 'Manqués (visible, rien détecté)', 'Mancati (visibile, niente rilevato)', 'Mancads (visibel, nagut identifitgà)'),
    'Pi temperature': ('Pi-Temperatur', 'Température du Pi', 'Temperatura del Pi', 'Temperatura dal Pi'),
    'Pictures per second': ('Bilder pro Sekunde', 'Images par seconde', 'Immagini al secondo', 'Maletgs per secunda'),
    'Key moments': ('Wichtige Momente', 'Moments clés', 'Momenti chiave', 'Muments impurtants'),
    'The night (truth of the simulator)': ('Die Nacht (Wahrheit des Simulators)', 'La nuit (vérité du simulateur)', 'La notte (verità del simulatore)', 'La notg (vardad dal simulatur)'),
    'Event': ('Ereignis', 'Événement', 'Evento', 'Eveniment'),
    'visible (s)': ('sichtbar (s)', 'visible (s)', 'visibile (s)', 'visibel (s)'),
    'Alarms': ('Alarme', 'Alarmes', 'Allarmi', 'Alarms'),
    'Export (JSON)': ('Export (JSON)', 'Export (JSON)', 'Esporta (JSON)', 'Export (JSON)'),
    'Comparison: last 10 runs': ('Vergleich: letzte 10 Läufe', 'Comparaison : 10 derniers tests', 'Confronto: ultimi 10 test', 'Cumparegliaziun: ultims 10 tests'),
    'Person alarm': ('Personen-Alarm', 'Alarme personne', 'Allarme persona', 'Alarm persuna'),
    'Warmth alarm': ('Wärme-Alarm', 'Alarme chaleur', 'Allarme calore', 'Alarm chalur'),
    'Pre-alarm': ('Voralarm', 'Pré-alarme', 'Preallarme', 'Prealarm'),
    'Noise alarm': ('Lärm-Alarm', 'Alarme bruit', 'Allarme rumore', 'Alarm canera'),
    'Sabotage alarm': ('Sabotage-Alarm', 'Alarme sabotage', 'Allarme sabotaggio', 'Alarm sabotascha'),
    'Operator mode: only the owner can start or stop the night test run – the reports can be viewed.': (
        'Bedienermodus: nur der Besitzer kann den Nacht-Testlauf starten oder stoppen – die Berichte kannst du ansehen.',
        'Mode opérateur : seul le propriétaire peut lancer ou arrêter le test de nuit – les rapports sont consultables.',
        'Modalità operatore: solo il proprietario può avviare o fermare il test notturno – i rapporti si possono vedere.',
        'Modus d’operatur: mo il possessur po cumenzar u fermar il test da notg – ils rapports pos ti guardar.'),
    'Only the owner can start or stop the night test run – the reports can be viewed.': (
        'Nur der Besitzer kann den Nacht-Testlauf starten oder stoppen – die Berichte kannst du ansehen.',
        'Seul le propriétaire peut lancer ou arrêter le test de nuit – les rapports sont consultables.',
        'Solo il proprietario può avviare o fermare il test notturno – i rapporti si possono vedere.',
        'Mo il possessur po cumenzar u fermar il test da notg – ils rapports pos ti guardar.'),
    'only the owner (not in operator mode)': ('nur der Besitzer (nicht im Bedienermodus)', 'seulement le propriétaire (pas en mode opérateur)',
                                              'solo il proprietario (non in modalità operatore)', 'mo il possessur (betg en il modus d’operatur)'),
    'a night test run is already running': ('es läuft schon ein Nacht-Testlauf', 'un test de nuit est déjà en cours', 'un test notturno è già in corso', 'in test da notg è gia en funcziun'),
    'the simulator does not know the night test run - update the simulator': ('der Simulator kennt den Nacht-Testlauf nicht – Simulator aktualisieren',
        'le simulateur ne connaît pas le test de nuit – mets à jour le simulateur', 'il simulatore non conosce il test notturno – aggiorna il simulatore',
        'il simulatur n’enconuscha betg il test da notg – actualisescha il simulatur'),
    'the simulator did not start the night test run': ('der Simulator hat den Nacht-Testlauf nicht gestartet', 'le simulateur n’a pas lancé le test de nuit',
                                                       'il simulatore non ha avviato il test notturno', 'il simulatur n’ha betg cumenzà il test da notg'),
    'detected after {s} s': ('erkannt nach {s} s', 'détecté après {s} s', 'rilevato dopo {s} s', 'identifitgà suenter {s} s'),
    'NOT detected': ('NICHT erkannt', 'PAS détecté', 'NON rilevato', 'BETG identifitgà'),
    'Incident: {inc} · false alarms: {fa}{by} · misses: {mi}': ('Vorfall: {inc} · Fehlalarme: {fa}{by} · verpasst: {mi}',
        'Incident : {inc} · fausses alarmes : {fa}{by} · manqués : {mi}', 'Incidente: {inc} · falsi allarmi: {fa}{by} · mancati: {mi}',
        'Incident: {inc} · fals alarms: {fa}{by} · mancads: {mi}'),
    'Toilet trip (own people)': ('WC-Gang (eigene Leute)', 'Passage aux WC (les siens)', 'Visita al WC (i propri)', 'Ir al WC (atgna glieud)'),
    'Toilet trip with torch': ('WC-Gang mit Taschenlampe', 'Passage aux WC avec lampe de poche', 'Visita al WC con torcia', 'Ir al WC cun glischina'),
    'Cat': ('Katze', 'Chat', 'Gatto', 'Giat'),
    'Fox': ('Fuchs', 'Renard', 'Volpe', 'Vulp'),
    'Hedgehog': ('Igel', 'Hérisson', 'Riccio', 'Gieriun'),
    'Headlights (late car)': ('Scheinwerfer (spätes Auto)', 'Phares (voiture tardive)', 'Fari (auto tardiva)', 'Reflectur (auto tard)'),
    'Rain': ('Regen', 'Pluie', 'Pioggia', 'Plievgia'),
    'Wind': ('Wind', 'Vent', 'Vento', 'Vent'),
    'Fog': ('Nebel', 'Brouillard', 'Nebbia', 'Tschajera'),
    'Lynx': ('Luchs', 'Lynx', 'Lince', 'Luf tscherver'),
    'Ibex': ('Steinbock', 'Bouquetin', 'Stambecco', 'Capricorn'),
    'Marmot': ('Murmeltier', 'Marmotte', 'Marmotta', 'Muntanella'),
    'Golden eagle': ('Steinadler', 'Aigle royal', 'Aquila reale', 'Evla'),
    'Bearded vulture': ('Bartgeier', 'Gypaète barbu', 'Gipeto', 'Tschess barbet'),
    'Light on the mountain': ('Licht am Berg', 'Lumière sur la montagne', 'Luce sulla montagna', 'Glisch vi da la muntogna'),
    'Chamois': ('Gämse', 'Chamois', 'Camoscio', 'Chamutsch'),
    'Cow': ('Kuh', 'Vache', 'Mucca', 'Vatga'),
    'Hare': ('Hase', 'Lièvre', 'Lepre', 'Lieur'),
    'Stoat': ('Hermelin', 'Hermine', 'Ermellino', 'Ermelin'),
    'Deer': ('Reh', 'Chevreuil', 'Capriolo', 'Chavriel'),
    'Rockfall': ('Steinschlag', 'Chute de pierres', 'Caduta di massi', 'Crudada da crappa'),
    'Thunderstorm': ('Gewitter', 'Orage', 'Temporale', 'Urizi'),
    'nothing in the plan (unknown)': ('nichts im Ablauf (unbekannt)', 'rien dans le plan (inconnu)', 'niente nel piano (sconosciuto)', 'nagut en il plan (nunenconuschent)'),
    'Somebody sneaks to the tent': ('Jemand schleicht zum Zelt', 'Quelqu’un se faufile vers la tente', 'Qualcuno si avvicina furtivo alla tenda', 'Insatgi sa stgaffa a la tenda'),
    'Somebody sneaks to the bike': ('Jemand schleicht zum Velo', 'Quelqu’un se faufile vers le vélo', 'Qualcuno si avvicina furtivo alla bici', 'Insatgi sa stgaffa al velo'),
    'Somebody sneaks to the caravan / car': ('Jemand schleicht zum Wohnwagen / Auto', 'Quelqu’un se faufile vers la caravane / la voiture',
                                             'Qualcuno si avvicina furtivo alla roulotte / all’auto', 'Insatgi sa stgaffa a la rulotta / a l’auto'),
    'SIMULATION – alarms are not real': ('SIMULATION – Alarme sind nicht echt', 'SIMULATION – alarmes non réelles', 'SIMULAZIONE – allarmi non reali', 'SIMULAZIUN – alarms betg reals'),
}
for _k, _v in _HX_nacht.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the manual (HELP_PAGE of 540): one paragraph in the section «Erkennung», German and English
for _a, _b in (('<section id="detect" data-icon="🎯"><h2>Erkennung</h2>',
                "<p><b>🌙 Nacht-Testlauf (Simulator):</b> In der Simulator-Zentrale (Gruppe «Testen», Kachel 🌙) spielt der Simulator eine ganze "
                "Nacht: WC-Gänge (manche mit Taschenlampe), Katze, Fuchs, Igel, ein spätes Auto, eine Stunde Regen, Wind, Morgennebel und "
                "<b>genau ein echter Vorfall</b> (jemand schleicht zu Zelt, Velo oder Wohnwagen). Wählbar: Szene, Belebtheit (ruhig / normal / "
                "viel los), Tempo (echt oder schnell: 8 Std. in etwa 1 Std.), Start und Ende (20:00–07:00), auf Wunsch jede Nacht von selbst. "
                "Der Simulator schreibt jedes Ereignis mit Zeit und Ort auf (Wahrheit), MoveEye vergleicht seine Alarme damit: Vorfall erkannt "
                "ja / nein und nach wie vielen Sekunden, Fehlalarme nach Ursache, Verpasstes, Akku, Pi-Temperatur, Bilder pro Sekunde und kleine "
                "Bilder der wichtigen Momente. Der Bericht kommt am Morgen als Push (🧪) und steht unter <a href=\"/nacht\">/nacht</a> (die "
                "letzten 10 Läufe zum Vergleichen, JSON-Export). Nur in der Simulation: Schutz «Voll» während des Laufs, Handy, Sirene und Relais "
                "bleiben still; danach ist alles wie vorher. Starten und stoppen darf nur der Besitzer – im Bedienermodus nur Berichte ansehen.</p>"),
               ('<section id="detect" data-icon="🎯"><h2>Detection</h2>',
                "<p><b>🌙 Night test run (simulator):</b> in the Simulator centre (group «Testen», tile 🌙) the simulator plays a whole night: "
                "toilet trips (some with a torch), cat, fox, hedgehog, a late car, an hour of rain, wind, fog in the morning and <b>exactly one "
                "real incident</b> (somebody sneaks to the tent, the bike or the caravan). Choose the scene, the liveliness (calm / normal / lots "
                "going on), the tempo (real or fast: 8 h in about 1 h), start and end (20:00–07:00), and if you like every night by itself. The "
                "simulator writes down every event with time and place (truth), MoveEye compares its alarms with it: incident detected yes / no "
                "and after how many seconds, false alarms by cause, misses, battery, Pi temperature, pictures per second and small pictures of the "
                "key moments. The report comes in the morning as a push (🧪) and is under <a href=\"/nacht\">/nacht</a> (the last 10 runs to "
                "compare, JSON export). Simulation only: protection «Voll» during the run, phone, siren and relays stay quiet; afterwards "
                "everything is as before. Only the owner may start and stop it – in operator mode only the reports.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
