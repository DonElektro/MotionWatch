#@ MoveEye – Teil 617: Übersetzungen «KI-Daten aufräumen» (Teil 197) und «Anmelden nur verschlüsselt» (Teil 574). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_KISICHER = {
    # ---- 197: KI-Daten aufräumen ----
    'Training set for an own AI model (YOLO)': ('Trainingspaket für ein eigenes KI-Modell (YOLO)', 'Jeu d’entraînement pour un modèle IA propre (YOLO)',
                                                'Pacchetto di addestramento per un modello IA proprio (YOLO)', 'Pachet da trenament per in agen model IA (YOLO)'),
    'The simulator makes the pictures and saves a ZIP on the desktop of its PC (about 2 s per picture).': (
        'Der Simulator macht die Bilder und legt ein ZIP auf den Schreibtisch seines PCs (etwa 2 s pro Bild).',
        'Le simulateur fait les images et dépose un ZIP sur le bureau de son PC (environ 2 s par image).',
        'Il simulatore fa le immagini e mette uno ZIP sul desktop del suo PC (circa 2 s per immagine).',
        'Il simulatur fa ils maletgs e metta in ZIP sin la scrivania da ses PC (circa 2 s per maletg).'),
    'Variety: normal': ('Vielfalt: normal', 'Variété : normale', 'Varietà: normale', 'Varietad: normala'),
    'Variety: high': ('Vielfalt: hoch', 'Variété : élevée', 'Varietà: alta', 'Varietad: auta'),
    'Variety: high (recommended)': ('Vielfalt: hoch (empfohlen)', 'Variété : élevée (recommandé)', 'Varietà: alta (consigliato)', 'Varietad: auta (recumandà)'),
    'Make the training pack': ('Trainingspaket machen', 'Faire le jeu d’entraînement', 'Crea il pacchetto di addestramento', 'Far il pachet da trenament'),
    'Delete old AI data': ('Alte KI-Daten löschen', 'Supprimer les anciennes données IA', 'Elimina i vecchi dati IA', 'Stizzar las datas IA veglias'),
    'training packs': ('Trainingspakete', 'jeux d’entraînement', 'pacchetti di addestramento', 'pachets da trenament'),
    'no training packs': ('keine Trainingspakete', 'aucun jeu d’entraînement', 'nessun pacchetto di addestramento', 'nagins pachets da trenament'),
    '{n} deleted ({mb} MB)': ('{n} gelöscht ({mb} MB)', '{n} supprimés ({mb} Mo)', '{n} eliminati ({mb} MB)', '{n} stizzads ({mb} MB)'),
    'newest': ('neuestes', 'le plus récent', 'il più recente', 'il pli nov'),
    'Delete all training packs on the PC of the simulator except the newest one? The AI model stays.': (
        'Alle Trainingspakete auf dem PC des Simulators ausser dem neuesten löschen? Das KI-Modell bleibt.',
        'Supprimer tous les jeux d’entraînement sur le PC du simulateur sauf le plus récent ? Le modèle IA reste.',
        'Eliminare tutti i pacchetti di addestramento sul PC del simulatore tranne il più recente? Il modello IA resta.',
        'Stizzar tut ils pachets da trenament sin il PC dal simulatur danor il pli nov? Il model IA resta.'),
    'Cleaned up by itself: after every new pack the newest 3 stay, nothing older than 30 days (the newest always stays). The AI model is never deleted.': (
        'Aufräumen von selbst: nach jedem neuen Paket bleiben die neuesten 3, nichts älter als 30 Tage (das neueste bleibt immer). Das KI-Modell wird nie gelöscht.',
        'Nettoyage automatique : après chaque nouveau jeu, les 3 plus récents restent, rien de plus vieux que 30 jours (le plus récent reste toujours). Le modèle IA n’est jamais supprimé.',
        'Pulizia automatica: dopo ogni nuovo pacchetto restano i 3 più recenti, niente più vecchio di 30 giorni (il più recente resta sempre). Il modello IA non viene mai eliminato.',
        'Rumir sez: suenter mintga nov pachet restan ils 3 ils pli novs, nagut pli vegl che 30 dis (il pli nov resta adina). Il model IA na vegn mai stizzà.'),
    # ---- 574: Anmelden nur verschlüsselt ----
    'Security': ('Sicherheit', 'Sécurité', 'Sicurezza', 'Segirezza'),
    'port': ('Port', 'port', 'porta', 'port'),
    'this connection': ('diese Verbindung', 'cette connexion', 'questa connessione', 'questa connexiun'),
    'encrypted': ('verschlüsselt', 'chiffrée', 'cifrata', 'criptada'),
    'not encrypted': ('nicht verschlüsselt', 'non chiffrée', 'non cifrata', 'betg criptada'),
    'secure page': ('sichere Seite', 'page sécurisée', 'pagina sicura', 'pagina segira'),
    'Open the secure page': ('Sichere Seite öffnen', 'Ouvrir la page sécurisée', 'Apri la pagina sicura', 'Avrir la pagina segira'),
    'To the secure page': ('Zur sicheren Seite', 'Vers la page sécurisée', 'Alla pagina sicura', 'A la pagina segira'),
    'Log in only encrypted': ('Anmelden nur verschlüsselt', 'Connexion uniquement chiffrée', 'Accesso solo cifrato', 'S’annunziar mo criptà'),
    'log in only encrypted': ('Anmelden nur verschlüsselt', 'connexion uniquement chiffrée', 'accesso solo cifrato', 's’annunziar mo criptà'),
    'Log in only encrypted (https): from other devices the password is only accepted over the secure page': (
        'Anmelden nur verschlüsselt (https): von anderen Geräten wird das Passwort nur über die sichere Seite angenommen',
        'Connexion uniquement chiffrée (https) : depuis d’autres appareils, le mot de passe n’est accepté que par la page sécurisée',
        'Accesso solo cifrato (https): da altri dispositivi la password è accettata solo tramite la pagina sicura',
        'S’annunziar mo criptà (https): dad auters apparats vegn il pled-clav acceptà mo sur la pagina segira'),
    'The password is only accepted over the secure page (https://…:port + 1) or from this device itself. Over plain http everybody in the same Wi-Fi (camping!) could read it. The browser warns once about the certificate (it is made by MoveEye itself) - accept it once. Tailscale and «https over Tailscale» are encrypted and work as before. Links with their own key (buttons in the push message, guests, shares) keep working. Programs (Home Assistant, shortcuts) use the https address too.': (
        'Das Passwort wird nur über die sichere Seite (https://…:Port + 1) oder vom Gerät selbst angenommen. Über einfaches http könnte es jeder im gleichen WLAN (Camping!) mitlesen. Der Browser warnt einmal wegen des Zertifikats (MoveEye macht es selbst) – einmal annehmen. Tailscale und «https über Tailscale» sind verschlüsselt und gehen wie bisher. Links mit eigenem Schlüssel (Knöpfe in der Push-Nachricht, Gäste, Teilen) gehen weiter. Programme (Home Assistant, Kurzbefehle) nehmen ebenfalls die https-Adresse.',
        'Le mot de passe n’est accepté que par la page sécurisée (https://…:port + 1) ou depuis l’appareil lui-même. En http simple, tout le monde dans le même Wi-Fi (camping !) pourrait le lire. Le navigateur avertit une fois à cause du certificat (MoveEye le crée lui-même) – l’accepter une fois. Tailscale et «https via Tailscale» sont chiffrés et fonctionnent comme avant. Les liens avec leur propre clé (boutons de la notification, invités, partages) continuent de fonctionner. Les programmes (Home Assistant, raccourcis) utilisent aussi l’adresse https.',
        'La password è accettata solo tramite la pagina sicura (https://…:porta + 1) o dal dispositivo stesso. Con http semplice chiunque nella stessa Wi-Fi (campeggio!) potrebbe leggerla. Il browser avvisa una volta per il certificato (lo crea MoveEye stesso) – accettarlo una volta. Tailscale e «https tramite Tailscale» sono cifrati e funzionano come prima. I link con una propria chiave (pulsanti nella notifica, ospiti, condivisioni) continuano a funzionare. I programmi (Home Assistant, comandi rapidi) usano anche l’indirizzo https.',
        'Il pled-clav vegn acceptà mo sur la pagina segira (https://…:port + 1) u da l’apparat sez. Sur http simpel pudess mintgin en il medem WLAN (camping!) al leger. Il navigatur avertescha ina giada pervi dal certificat (MoveEye al fa sez) – al acceptar ina giada. Tailscale e «https sur Tailscale» èn criptads e funcziunan sco fin ussa. Colliaziuns cun agen clav (buttuns en l’avis push, giasts, parter) funcziunan vinavant. Programs (Home Assistant, cumonds curts) duvran er l’adressa https.'),
    'For your safety MoveEye takes the password only over the secure page (https). Over plain http everybody in the same Wi-Fi could read it.': (
        'Zu deiner Sicherheit nimmt MoveEye das Passwort nur über die sichere Seite (https). Über einfaches http könnte es jeder im gleichen WLAN mitlesen.',
        'Pour ta sécurité, MoveEye n’accepte le mot de passe que par la page sécurisée (https). En http simple, tout le monde dans le même Wi-Fi pourrait le lire.',
        'Per la tua sicurezza MoveEye accetta la password solo tramite la pagina sicura (https). Con http semplice chiunque nella stessa Wi-Fi potrebbe leggerla.',
        'Per tia segirezza accepta MoveEye il pled-clav mo sur la pagina segira (https). Sur http simpel pudess mintgin en il medem WLAN al leger.'),
    'The browser will warn once that the certificate is not trusted: MoveEye made it itself. Choose «Advanced» → «Continue» (iPhone: «Show details» → «visit this website»).': (
        'Der Browser warnt einmal, dass dem Zertifikat nicht vertraut wird: MoveEye hat es selbst gemacht. «Erweitert» → «Weiter» wählen (iPhone: «Details einblenden» → «diese Website besuchen»).',
        'Le navigateur avertit une fois que le certificat n’est pas fiable : MoveEye l’a créé lui-même. Choisir «Paramètres avancés» → «Continuer» (iPhone : «Afficher les détails» → «visiter ce site web»).',
        'Il browser avvisa una volta che il certificato non è attendibile: l’ha creato MoveEye stesso. Scegliere «Avanzate» → «Procedi» (iPhone: «Mostra dettagli» → «visita questo sito web»).',
        'Il navigatur avertescha ina giada ch’il certificat na saja betg fidà: MoveEye l’ha fatg sez. Tscherner «Avanzà» → «Cuntinuar» (iPhone: «Mussar detagls» → «visitar questa website»).'),
    'log in only over the secure page (https)': ('Anmelden nur über die sichere Seite (https)', 'connexion uniquement par la page sécurisée (https)',
                                                 'accesso solo tramite la pagina sicura (https)', 's’annunziar mo sur la pagina segira (https)'),
    'For your safety a password can only be set over the secure page': ('Zu deiner Sicherheit lässt sich ein Passwort nur über die sichere Seite setzen',
                                                                        'Pour ta sécurité, un mot de passe ne peut être défini que par la page sécurisée',
                                                                        'Per la tua sicurezza una password si può impostare solo tramite la pagina sicura',
                                                                        'Per tia segirezza po in pled-clav vegnir definì mo sur la pagina segira'),
    'For your safety a password can only be set over the secure page (https).': (
        'Zu deiner Sicherheit lässt sich ein Passwort nur über die sichere Seite (https) setzen.',
        'Pour ta sécurité, un mot de passe ne peut être défini que par la page sécurisée (https).',
        'Per la tua sicurezza una password si può impostare solo tramite la pagina sicura (https).',
        'Per tia segirezza po in pled-clav vegnir definì mo sur la pagina segira (https).'),
    'The browser warns once about the certificate (MoveEye made it itself): «Advanced» → «Continue».': (
        'Der Browser warnt einmal wegen des Zertifikats (MoveEye hat es selbst gemacht): «Erweitert» → «Weiter».',
        'Le navigateur avertit une fois à cause du certificat (MoveEye l’a créé lui-même) : «Paramètres avancés» → «Continuer».',
        'Il browser avvisa una volta per il certificato (l’ha creato MoveEye stesso): «Avanzate» → «Procedi».',
        'Il navigatur avertescha ina giada pervi dal certificat (MoveEye l’ha fatg sez): «Avanzà» → «Cuntinuar».'),
    'No secure page (https) - the password still goes unencrypted through the network. Install openssl (sudo apt install openssl) and restart MoveEye.': (
        'Keine sichere Seite (https) – das Passwort geht weiterhin unverschlüsselt durchs Netz. openssl installieren (sudo apt install openssl) und MoveEye neu starten.',
        'Pas de page sécurisée (https) – le mot de passe passe encore en clair sur le réseau. Installer openssl (sudo apt install openssl) et redémarrer MoveEye.',
        'Nessuna pagina sicura (https) – la password passa ancora in chiaro nella rete. Installare openssl (sudo apt install openssl) e riavviare MoveEye.',
        'Nagina pagina segira (https) – il pled-clav va vinavant betg criptà tras la rait. Installar openssl (sudo apt install openssl) e reaviar MoveEye.'),
    'Off: the password may go unencrypted through the network (http).': ('Aus: das Passwort kann unverschlüsselt durchs Netz gehen (http).',
                                                                         'Désactivé : le mot de passe peut passer en clair sur le réseau (http).',
                                                                         'Spento: la password può passare in chiaro nella rete (http).',
                                                                         'Deactivà: il pled-clav po ir betg criptà tras la rait (http).'),
}
for _k, _v in _HX_KISICHER.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- guide (Anleitung): one point each in the chapter «System» of every language ----
_HELP_KISICHER = {
    "de": '<li><b>🔒 Anmelden nur verschlüsselt</b> (Einstellungen → Netz &amp; Zugang → Sicherheit, ein): das Web-Passwort wird nur über die sichere Seite (https, Port + 1, z. B. <code>https://&lt;pi&gt;:5001</code>), vom Gerät selbst oder über Tailscale angenommen. Wer im WLAN die normale http-Adresse öffnet, sieht einen kurzen Hinweis und kommt zur sicheren Seite; der Browser warnt einmal wegen des selbst gemachten Zertifikats («Erweitert» → «Weiter»). Knöpfe in der Push-Nachricht, Gäste- und Teilen-Links gehen weiter. Kann die sichere Seite nicht starten (openssl fehlt), geht die Anmeldung über http weiter – mit Warnung im Selbstcheck.</li>'
          '<li><b>🧹 KI-Daten:</b> Reiter Simulator → Werkzeuge: «Trainingspaket für ein eigenes KI-Modell» mit <i>Vielfalt normal / hoch</i>, darunter die Pakete auf dem PC des Simulators. Nach jedem neuen Paket räumt der Simulator selbst auf (die neuesten 3 bleiben, nichts älter als 30 Tage); «Alte KI-Daten löschen» lässt nur das neueste. Das KI-Modell wird nie gelöscht. Die KI-Rechenhilfe auf dem PC nimmt das eigene Modell, sobald es dort heruntergeladen ist.</li>',
    "en": '<li><b>🔒 Log in only encrypted</b> (Settings → Network &amp; access → Security, on): the web password is only accepted over the secure page (https, port + 1, e.g. <code>https://&lt;pi&gt;:5001</code>), from the device itself or over Tailscale. Opening the plain http address in the Wi-Fi shows a short hint and leads to the secure page; the browser warns once about the self-made certificate («Advanced» → «Continue»). Buttons in push messages, guest and share links keep working. If the secure page cannot start (openssl missing), the http login keeps working - with a warning in the self-check.</li>'
          '<li><b>🧹 AI data:</b> tab Simulator → tools: «Training set for an own AI model» with <i>variety normal / high</i>, below it the packs on the PC of the simulator. After every new pack the simulator cleans up by itself (the newest 3 stay, nothing older than 30 days); «Delete old AI data» keeps only the newest. The AI model is never deleted. The AI helper on the PC uses the own model as soon as it is downloaded there.</li>',
    "fr": '<li><b>🔒 Connexion uniquement chiffrée</b> (Réglages → Réseau → Sécurité) : le mot de passe web n’est accepté que par la page sécurisée (https, port + 1), depuis l’appareil lui-même ou via Tailscale. Le navigateur avertit une fois à cause du certificat créé par MoveEye. Les boutons des notifications et les liens invités restent valables. Sans page sécurisée (openssl manquant), la connexion http reste possible, avec un avertissement.</li>'
          '<li><b>🧹 Données IA :</b> onglet Simulateur → outils : jeu d’entraînement avec <i>variété normale / élevée</i> et la liste des jeux ; les 3 plus récents restent, rien de plus vieux que 30 jours ; «Supprimer les anciennes données IA» ne garde que le plus récent. Le modèle IA n’est jamais supprimé.</li>',
    "it": '<li><b>🔒 Accesso solo cifrato</b> (Impostazioni → Rete → Sicurezza): la password web è accettata solo tramite la pagina sicura (https, porta + 1), dal dispositivo stesso o via Tailscale. Il browser avvisa una volta per il certificato creato da MoveEye. I pulsanti delle notifiche e i link ospiti restano validi. Senza pagina sicura (manca openssl) l’accesso http resta possibile, con un avviso.</li>'
          '<li><b>🧹 Dati IA:</b> scheda Simulatore → strumenti: pacchetto di addestramento con <i>varietà normale / alta</i> e l’elenco dei pacchetti; restano i 3 più recenti, niente più vecchio di 30 giorni; «Elimina i vecchi dati IA» tiene solo il più recente. Il modello IA non viene mai eliminato.</li>',
    "rm": '<li><b>🔒 S’annunziar mo criptà</b> (Parameters → Rait → Segirezza): il pled-clav vegn acceptà mo sur la pagina segira (https, port + 1), da l’apparat sez u sur Tailscale. Il navigatur avertescha ina giada pervi dal certificat da MoveEye. Buttuns en ils avis e colliaziuns da giasts funcziunan vinavant. Senza pagina segira (openssl manca) resta l’annunzia sur http pussaivla, cun in avertiment.</li>'
          '<li><b>🧹 Datas IA:</b> register Simulatur → utensils: pachet da trenament cun <i>varietad normala / auta</i> e la glista dals pachets; ils 3 ils pli novs restan, nagut pli vegl che 30 dis; «Stizzar las datas IA veglias» tegna mo il pli nov. Il model IA na vegn mai stizzà.</li>',
}


def _help_kisicher(doc, lang):
    i = doc.find('<section id="system"')
    j = doc.find("</ul>", i) if i >= 0 else -1
    return doc[:j] + _HELP_KISICHER[lang] + doc[j:] if j > 0 else doc


_hp_en2 = HELP_PAGE.find('<div lang="en">')
if _hp_en2 > 0:
    HELP_PAGE = _help_kisicher(HELP_PAGE[:_hp_en2], "de") + _help_kisicher(HELP_PAGE[_hp_en2:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_kisicher(HELP_X[_L], _L)
