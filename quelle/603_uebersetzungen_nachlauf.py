#@ MoveEye – Teil 603: Übersetzungen zum Nachlauf des Konzept-Checks (Teil 577 und die kleinen Änderungen in 135, 460, 470, 523, 530, 540). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_NACHLAUF = {
    # ---- 1: one weekly report ----
    'Week in the simulator: {v} visits. Animals: {an}': ('Woche im Simulator: {v} Besuche. Tiere: {an}', 'Semaine dans le simulateur : {v} visites. Animaux : {an}', 'Settimana nel simulatore: {v} visite. Animali: {an}', 'Emna en il simulatur: {v} visitas. Animals: {an}'),
    'Weekly report: with the week in the simulator (visits, animals, recognised persons)': ('Wochenbericht: mit der Woche im Simulator (Besuche, Tiere, erkannte Personen)', 'Rapport hebdomadaire : avec la semaine dans le simulateur (visites, animaux, personnes reconnues)', 'Rapporto settimanale: con la settimana nel simulatore (visite, animali, persone riconosciute)', 'Rapport d’emna: cun l’emna en il simulatur (visitas, animals, persunas renconuschidas)'),
    # ---- 2: one timeline ----
    'Open the timeline of this day': ('Zeitleiste dieses Tages öffnen', 'Ouvrir la chronologie de ce jour', 'Apri la cronologia di questo giorno', 'Avrir la cronologia da quest di'),
    # ---- 4: battery thresholds together ----
    '🐢 Battery saver below (% battery): fewer pictures, the AI less often - normal again at +5 % or when charging': ('🐢 Akku-Sparen unter (% Akku): weniger Bilder, die KI seltener – wieder normal ab +5 % oder beim Laden', '🐢 Économie de batterie en dessous de (% de batterie) : moins d’images, l’IA moins souvent – normal à nouveau à +5 % ou en charge', '🐢 Risparmio batteria sotto (% batteria): meno immagini, l’IA meno spesso – di nuovo normale a +5 % o in carica', '🐢 Spargnar accu sut (% accu): main maletgs, la IA pli darar – puspè normal a partir da +5 % u cun chargiar'),
    '🔥 Campfire games end below (% battery): back to the camping guard (0 = never)': ('🔥 Lagerfeuer-Spiele enden unter (% Akku): zurück zur Camping-Wache (0 = nie)', '🔥 Les jeux du feu de camp s’arrêtent en dessous de (% de batterie) : retour à la garde camping (0 = jamais)', '🔥 I giochi al falò finiscono sotto (% batteria): ritorno alla guardia campeggio (0 = mai)', '🔥 Ils gieus al fieu da campadi finan sut (% accu): enavos a la guardia da campadi (0 = mai)'),
    'Also under Settings → Battery, next to the battery saver': ('Auch unter Einstellungen → Akku, neben dem Akku-Sparen', 'Aussi sous Réglages → Batterie, à côté de l’économie de batterie', 'Anche in Impostazioni → Batteria, accanto al risparmio batteria', 'Er sut Parameters → Accu, sper il spargnar accu'),
    # ---- 5: return of the phone ----
    'When my phone comes back': ('Wenn mein Handy zurückkommt', 'Quand mon téléphone revient', 'Quando il mio telefono torna', 'Cur che mes telefonin returna'),
    'When my phone comes back:': ('Wenn mein Handy zurückkommt:', 'Quand mon téléphone revient :', 'Quando il mio telefono torna:', 'Cur che mes telefonin returna:'),
    'When my phone comes back?': ('Wenn mein Handy zurückkommt?', 'Quand mon téléphone revient ?', 'Quando il mio telefono torna?', 'Cur che mes telefonin returna?'),
    'switch the protection off': ('Schutz ausschalten', 'désactiver la protection', 'spegnere la protezione', 'deactivar la protecziun'),
    'ask «Is it you?» (person alarms wait)': ('fragen «Bist du\'s?» (Personen-Alarme warten)', 'demander «C’est toi ?» (les alarmes personne attendent)', 'chiedere «Sei tu?» (gli allarmi persona aspettano)', 'dumandar «Es ti?» (ils alarms da persunas spetgan)'),
    'nothing (the protection stays on)': ('nichts (der Schutz bleibt an)', 'rien (la protection reste active)', 'niente (la protezione resta attiva)', 'nagut (la protecziun resta activa)'),
    'Automatic: on when my phone is gone': ('Automatisch an, wenn mein Handy weg ist', 'Automatique : active quand mon téléphone est parti', 'Automatico: attiva quando il mio telefono non c’è', 'Automatic: activ, cur che mes telefonin è davent'),
    'Protection on automatically when my phone is gone (choose the phone: Tools → Am I at home?)': ('Schutz automatisch an, wenn mein Handy weg ist (Handy wählen: Werkzeuge → Bin ich zu Hause?)', 'Protection automatiquement active quand mon téléphone est parti (choisir le téléphone : Outils → Suis-je à la maison ?)', 'Protezione attiva automaticamente quando il mio telefono non c’è (scegliere il telefono: Strumenti → Sono a casa?)', 'Protecziun activa automaticamain, cur che mes telefonin è davent (tscherner il telefonin: Utensils → Sun jau a chasa?)'),
    # ---- 7: walk test ----
    'Walk test running: no alarms until it ends (afterwards the protection is as before).': ('Gehtest läuft: keine Alarme, bis er fertig ist (danach ist der Schutz wie vorher).', 'Test de passage en cours : pas d’alarme jusqu’à la fin (ensuite la protection est comme avant).', 'Test di passaggio in corso: nessun allarme fino alla fine (poi la protezione è come prima).', 'Test da passar en curs: nagins alarms fin ch’el è a fin (suenter è la protecziun sco avant).'),
}
for _k, _v in _HX_NACHLAUF.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
