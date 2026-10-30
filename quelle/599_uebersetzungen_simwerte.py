#@ MoveEye – Teil 599: Übersetzungen der Simulator-Werte (Teile 285 und 598). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_SIMWERTE = {
    'from the simulator': ('vom Simulator', 'du simulateur', 'dal simulatore', 'dal simulatur'),
    'Values from the simulator': ('Werte aus dem Simulator', 'Valeurs du simulateur', 'Valori dal simulatore', 'Valurs dal simulatur'),
    'Clock': ('Uhrzeit', 'Heure', 'Ora', 'Ura'),
    'Place': ('Ort', 'Lieu', 'Luogo', 'Lieu'),
    'Weather': ('Wetter', 'Météo', 'Meteo', 'Aura'),
    'Pi temperature': ('Pi-Temperatur', 'Température du Pi', 'Temperatura del Pi', 'Temperatura dal Pi'),
    'Network': ('Netz', 'Réseau', 'Rete', 'Rait'),
    'time-lapse': ('Zeitraffer', 'accéléré', 'accelerato', 'accelerà'),
    'Wi-Fi gone': ('WLAN weg', 'Wi-Fi coupé', 'Wi-Fi assente', 'WLAN davent'),
    'Internet gone': ('Internet weg', 'Internet coupé', 'Internet assente', 'Internet davent'),
    'Simulator test: push messages wait and are sent later': (
        'Simulator-Test: Push-Nachrichten warten und werden nachgeschickt',
        'Test du simulateur : les messages push attendent et sont envoyés plus tard',
        'Test del simulatore: i messaggi push aspettano e vengono inviati più tardi',
        'Test dal simulatur: ils messadis push spetgan e vegnan tramess pli tard'),
    'Battery empty – the device would be off now': (
        'Akku leer – das Gerät wäre jetzt aus', 'Batterie vide – l’appareil serait éteint maintenant',
        'Batteria scarica – l’apparecchio ora sarebbe spento', 'Accu vid – l’apparat fiss ussa stiz'),
    'Pi temperature from the simulator': ('Pi-Temperatur vom Simulator', 'température du Pi du simulateur', 'temperatura del Pi dal simulatore',
                                          'temperatura dal Pi dal simulatur'),
    'weather and forecast from the simulator': ('Wetter und Prognose vom Simulator', 'météo et prévision du simulateur',
                                                'meteo e previsione dal simulatore', 'aura e prognosa dal simulatur'),
    'Battery': ('Akku', 'Batterie', 'Batteria', 'Accu'),
    'Solar panel': ('Solarpanel', 'Panneau solaire', 'Pannello solare', 'Panel solar'),
    'GPS module': ('GPS-Modul', 'Module GPS', 'Modulo GPS', 'Modul GPS'),
    'night': ('Nacht', 'nuit', 'notte', 'notg'),
    'day': ('Tag', 'jour', 'giorno', 'di'),
    'Schedule': ('Zeitplan', 'Horaire', 'Orario', 'Plan da temp'),
    'clear': ('klar', 'dégagé', 'sereno', 'serein'),
    'cloudy': ('bewölkt', 'nuageux', 'nuvoloso', 'nivlus'),
    'fog': ('Nebel', 'brouillard', 'nebbia', 'tschajera'),
    'rain': ('Regen', 'pluie', 'pioggia', 'plievgia'),
    'snow': ('Schnee', 'neige', 'neve', 'naiv'),
    'simulator': ('Simulator', 'simulateur', 'simulatore', 'simulatur'),
    'sent later': ('nachgeschickt', 'envoyé plus tard', 'inviato più tardi', 'tramess pli tard'),
    'sv-note': ('Antwortet der Simulator 10 Sekunden nicht, gelten wieder die echten Sensoren und die echte Uhr. Protokoll, Dateinamen und '
                'Updates bleiben auf der echten Uhr.',
                'Si le simulateur ne répond pas pendant 10 secondes, les vrais capteurs et la vraie horloge s’appliquent à nouveau. Le journal, '
                'les noms de fichiers et les mises à jour restent sur l’heure réelle.',
                'Se il simulatore non risponde per 10 secondi valgono di nuovo i sensori veri e l’orologio vero. Protocollo, nomi dei file e '
                'aggiornamenti restano sull’ora vera.',
                'Sch’il simulatur na respunda betg durant 10 secundas, valan puspè ils sensurs vairs e l’ura vaira. Protocol, nums da datotecas '
                'ed actualisaziuns restan sin l’ura vaira.'),
}
for _k, _v in _HX_SIMWERTE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the German texts into the pages (main page and Simulator page, only where they have no own text yet - see 598)
_SVDE = json.dumps({_k: DE.get(_k, _v[0]) for _k, _v in _HX_SIMWERTE.items()}, ensure_ascii=False)
WEB_PAGE = WEB_PAGE.replace("/*SVDE*/{}", _SVDE, 1)
SIM_PAGE = SIM_PAGE.replace("/*SVDE*/{}", _SVDE, 1)
