#@ MoveEye – Teil 561: Übersetzungen (DE / FR / IT / RM) und Anleitung DE / EN für «Online-Spiel über Tailscale Funnel» (Teil 556, Web 544, Fenster 592). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_FUNNEL = {
    'Online game over Tailscale Funnel': ('Online-Spiel über Tailscale Funnel', 'Jeu en ligne via Tailscale Funnel', 'Gioco online tramite Tailscale Funnel', 'Gieu online via Tailscale Funnel'),
    'Switch the funnel on': ('Funnel einschalten', 'Activer le Funnel', 'Attivare il Funnel', 'Activar il Funnel'),
    'funnel-note': ('Macht nur das Spiel (/game/…) über Tailscale Funnel im Internet erreichbar – für Freunde ohne Tailscale. Alles andere von MoveEye bleibt privat. Geht von selbst aus, wenn die letzte Einladung abläuft oder zurückgezogen wird, spätestens nach der gewählten Zeit und beim Neustart.',
                    'Rend seulement le jeu (/game/…) accessible sur Internet via Tailscale Funnel – pour des amis sans Tailscale. Tout le reste de MoveEye reste privé. Se coupe tout seul quand la dernière invitation expire ou est retirée, au plus tard après la durée choisie et au redémarrage.',
                    'Rende raggiungibile su Internet solo il gioco (/game/…) tramite Tailscale Funnel – per amici senza Tailscale. Tutto il resto di MoveEye resta privato. Si spegne da solo quando l’ultimo invito scade o viene ritirato, al più tardi dopo il tempo scelto e al riavvio.',
                    'Renda accessibel en l’internet mo il gieu (/game/…) via Tailscale Funnel – per amis senza Tailscale. Tut il auter da MoveEye resta privat. Sa stizza sez, cur che l’ultima invitaziun scada u vegn retratga, il pli tard suenter il temp tschernì e cun reaviar.'),
    'local-warn-funnel': ('Dieser Link geht nur im eigenen Netz. Für Freunde ohne Tailscale: Funnel einschalten – dann ist nur das Spiel öffentlich.',
                          'Ce lien ne marche que dans le réseau local. Pour des amis sans Tailscale : activer le Funnel – seul le jeu devient public.',
                          'Questo link funziona solo nella rete locale. Per amici senza Tailscale: attivare il Funnel – solo il gioco diventa pubblico.',
                          'Questa colliaziun funcziuna mo en la rait locala. Per amis senza Tailscale: activar il Funnel – lura è mo il gieu public.'),
    'switches off at the latest after': ('geht spätestens aus nach', 'se coupe au plus tard après', 'si spegne al più tardi dopo', 'sa stizza il pli tard suenter'),
    'Funnel on': ('Funnel an – öffentlich', 'Funnel actif – public', 'Funnel attivo – pubblico', 'Funnel activ – public'),
    'Funnel off': ('Funnel aus', 'Funnel coupé', 'Funnel spento', 'Funnel deactivà'),
    'Make an invitation now - without one the funnel switches off after 15 minutes.': ('Jetzt eine Einladung erstellen – ohne Einladung geht der Funnel nach 15 Minuten wieder aus.',
        'Crée maintenant une invitation – sans invitation, le Funnel se coupe après 15 minutes.', 'Crea ora un invito – senza invito il Funnel si spegne dopo 15 minuti.',
        'Fa ussa ina invitaziun – senza invitaziun sa stizza il Funnel suenter 15 minutas.'),
    'Only the administrator can switch the funnel on.': ('Nur der Administrator kann den Funnel einschalten.', 'Seul l’administrateur peut activer le Funnel.',
                                                         'Solo l’amministratore può attivare il Funnel.', 'Mo l’administratur po activar il Funnel.'),
    'Not possible in operator mode': ('Im Bedienmodus nicht möglich', 'Impossible en mode opérateur', 'Non possibile in modalità operatore', 'Betg pussaivel en il modus da manaschar'),
    'Online game public': ('Online-Spiel öffentlich', 'Jeu en ligne public', 'Gioco online pubblico', 'Gieu online public'),
    'The online game is public on the internet for {h} h (only the game, through Tailscale Funnel)': (
        'Das Online-Spiel ist für {h} h öffentlich im Internet (nur das Spiel, über Tailscale Funnel)', 'Le jeu en ligne est public sur Internet pendant {h} h (seulement le jeu, via Tailscale Funnel)',
        'Il gioco online è pubblico su Internet per {h} h (solo il gioco, tramite Tailscale Funnel)', 'Il gieu online è public en l’internet per {h} h (mo il gieu, via Tailscale Funnel)'),
    'maximum time over': ('Höchstzeit vorbei', 'durée maximale écoulée', 'tempo massimo scaduto', 'temp maximal passà'),
    'the last invitation expired or was revoked': ('die letzte Einladung ist abgelaufen oder zurückgezogen', 'la dernière invitation a expiré ou a été retirée',
                                                   'l’ultimo invito è scaduto o è stato ritirato', 'l’ultima invitaziun è scadida u retratga'),
    'no invitation within 15 minutes': ('15 Minuten lang keine Einladung', 'aucune invitation pendant 15 minutes', 'nessun invito per 15 minuti', 'naginas invitaziuns durant 15 minutas'),
    'removed in Tailscale': ('in Tailscale entfernt', 'supprimé dans Tailscale', 'rimosso in Tailscale', 'allontanà en Tailscale'),
    # errors with the fix (556 funnel_explain)
    'Tailscale is not installed on this device.': ('Tailscale ist auf diesem Gerät nicht installiert.', 'Tailscale n’est pas installé sur cet appareil.',
                                                   'Tailscale non è installato su questo dispositivo.', 'Tailscale n’è betg installà sin quest apparat.'),
    'Install it on the Pi and log in once:': ('Auf dem Pi installieren und einmal anmelden:', 'L’installer sur le Pi et se connecter une fois :',
                                              'Installarlo sul Pi e accedere una volta:', 'L’installar sin il Pi e s’annunziar ina giada:'),
    'Tailscale is not logged in or stopped.': ('Tailscale ist nicht angemeldet oder gestoppt.', 'Tailscale n’est pas connecté ou est arrêté.',
                                               'Tailscale non ha effettuato l’accesso o è fermo.', 'Tailscale n’è betg annunzià u è fermà.'),
    'On the Pi start Tailscale and log in with your account (it shows a link):': ('Auf dem Pi Tailscale starten und mit deinem Konto anmelden (es zeigt einen Link):',
        'Sur le Pi, démarrer Tailscale et se connecter avec ton compte (un lien s’affiche) :', 'Sul Pi avviare Tailscale e accedere con il tuo account (mostra un link):',
        'Sin il Pi aviar Tailscale e s’annunziar cun tes conto (i cumpara ina colliaziun):'),
    'Funnel is not allowed in your tailnet policy.': ('Funnel ist in den Regeln deines Tailnets nicht erlaubt.', 'Le Funnel n’est pas autorisé dans les règles de ton tailnet.',
                                                      'Il Funnel non è permesso nelle regole del tuo tailnet.', 'Il Funnel n’è betg permess en las reglas da tes tailnet.'),
    'Tailscale admin console → Access controls: add the node attribute «funnel» (lines below) and save.': (
        'Tailscale-Verwaltung (Admin console) → Access controls: das Geräte-Attribut «funnel» eintragen (Zeilen unten) und speichern.',
        'Console d’administration Tailscale → Access controls : ajouter l’attribut «funnel» (lignes ci-dessous) et enregistrer.',
        'Console di amministrazione Tailscale → Access controls: aggiungere l’attributo «funnel» (righe sotto) e salvare.',
        'Console d’administraziun Tailscale → Access controls: agiuntar l’attribut «funnel» (lingias sutvart) e memorisar.'),
    'Also needed: DNS → MagicDNS on and «HTTPS Certificates» enabled.': ('Ebenfalls nötig: DNS → MagicDNS an und «HTTPS Certificates» eingeschaltet.',
        'Aussi nécessaire : DNS → MagicDNS actif et «HTTPS Certificates» activé.', 'Serve anche: DNS → MagicDNS attivo e «HTTPS Certificates» attivato.',
        'Era necessari: DNS → MagicDNS activ e «HTTPS Certificates» activà.'),
    'Then switch the funnel on again here.': ('Dann hier den Funnel nochmals einschalten.', 'Puis réactiver le Funnel ici.', 'Poi riattivare qui il Funnel.', 'Lura activar puspè il Funnel qua.'),
    'Easiest: open this link once – Tailscale enables Funnel for this device:': ('Am einfachsten: diesen Link einmal öffnen – Tailscale erlaubt Funnel für dieses Gerät:',
        'Le plus simple : ouvrir une fois ce lien – Tailscale autorise le Funnel pour cet appareil :', 'Il modo più semplice: aprire una volta questo link – Tailscale abilita il Funnel per questo dispositivo:',
        'Il pli simpel: avrir ina giada questa colliaziun – Tailscale permetta il Funnel per quest apparat:'),
    'Enable Funnel (Tailscale link)': ('Funnel erlauben (Link von Tailscale)', 'Autoriser le Funnel (lien Tailscale)', 'Abilitare il Funnel (link di Tailscale)', 'Permetter il Funnel (colliaziun da Tailscale)'),
    'Enable HTTPS (Tailscale link)': ('HTTPS einschalten (Link von Tailscale)', 'Activer HTTPS (lien Tailscale)', 'Attivare HTTPS (link di Tailscale)', 'Activar HTTPS (colliaziun da Tailscale)'),
    'HTTPS certificates are not enabled in your tailnet.': ('HTTPS-Zertifikate sind in deinem Tailnet nicht eingeschaltet.', 'Les certificats HTTPS ne sont pas activés dans ton tailnet.',
                                                            'I certificati HTTPS non sono attivati nel tuo tailnet.', 'Ils certificats HTTPS n’èn betg activads en tes tailnet.'),
    'Tailscale admin console → DNS: switch on MagicDNS.': ('Tailscale-Verwaltung (Admin console) → DNS: MagicDNS einschalten.', 'Console d’administration Tailscale → DNS : activer MagicDNS.',
                                                           'Console di amministrazione Tailscale → DNS: attivare MagicDNS.', 'Console d’administraziun Tailscale → DNS: activar MagicDNS.'),
    'On the same page under «HTTPS Certificates» click «Enable HTTPS».': ('Auf derselben Seite unter «HTTPS Certificates» auf «Enable HTTPS» klicken.',
        'Sur la même page, sous «HTTPS Certificates», cliquer sur «Enable HTTPS».', 'Nella stessa pagina, sotto «HTTPS Certificates», cliccare «Enable HTTPS».',
        'Sin la medema pagina sut «HTTPS Certificates» cliccar «Enable HTTPS».'),
    'MoveEye may not change the Tailscale settings.': ('MoveEye darf die Tailscale-Einstellungen nicht ändern.', 'MoveEye ne peut pas modifier les réglages de Tailscale.',
                                                       'MoveEye non può modificare le impostazioni di Tailscale.', 'MoveEye na dastga betg midar ils parameters da Tailscale.'),
    'Once on the Pi (as the user MoveEye runs as), then switch on again:': ('Einmal auf dem Pi (als der Benutzer, unter dem MoveEye läuft), dann nochmals einschalten:',
        'Une fois sur le Pi (avec l’utilisateur de MoveEye), puis réactiver :', 'Una volta sul Pi (con l’utente di MoveEye), poi riattivare:',
        'Ina giada sin il Pi (sco l’utilisader da MoveEye), lura activar puspè:'),
    'All three Funnel ports (443, 8443, 10000) are already used by other Tailscale serve settings.': (
        'Alle drei Funnel-Ports (443, 8443, 10000) sind schon von anderen Tailscale-serve-Einstellungen belegt.',
        'Les trois ports Funnel (443, 8443, 10000) sont déjà utilisés par d’autres réglages Tailscale serve.',
        'Tutte e tre le porte Funnel (443, 8443, 10000) sono già usate da altre impostazioni Tailscale serve.',
        'Tut ils trais ports Funnel (443, 8443, 10000) èn gia occupads dad auters parameters Tailscale serve.'),
    'Look at them and switch one off:': ('Anschauen und eine davon ausschalten:', 'Les consulter et en couper une :', 'Controllarle e spegnerne una:', 'Las guardar e stizzar ina:'),
    'The game door of MoveEye could not start.': ('Die Spiel-Tür von MoveEye konnte nicht starten.', 'La porte du jeu de MoveEye n’a pas pu démarrer.',
                                                  'La porta del gioco di MoveEye non è partita.', 'La porta dal gieu da MoveEye n’ha betg pudì cumenzar.'),
    'Restart MoveEye and try again.': ('MoveEye neu starten und nochmals versuchen.', 'Redémarrer MoveEye et réessayer.', 'Riavviare MoveEye e riprovare.', 'Reaviar MoveEye e empruvar anc ina giada.'),
    'Tailscale did not answer in time.': ('Tailscale hat nicht rechtzeitig geantwortet.', 'Tailscale n’a pas répondu à temps.', 'Tailscale non ha risposto in tempo.', 'Tailscale n’ha betg respundì a temp.'),
    'Check «tailscale status» on the Pi and try again.': ('Auf dem Pi «tailscale status» prüfen und nochmals versuchen.', 'Vérifier «tailscale status» sur le Pi et réessayer.',
                                                          'Controllare «tailscale status» sul Pi e riprovare.', 'Controllar «tailscale status» sin il Pi ed empruvar anc ina giada.'),
    'Tailscale refused the funnel.': ('Tailscale hat den Funnel abgelehnt.', 'Tailscale a refusé le Funnel.', 'Tailscale ha rifiutato il Funnel.', 'Tailscale ha refusà il Funnel.'),
    'Message of Tailscale:': ('Meldung von Tailscale:', 'Message de Tailscale :', 'Messaggio di Tailscale:', 'Messadi da Tailscale:'),
    'Install Tailscale (official guide)': ('Tailscale installieren (offizielle Anleitung)', 'Installer Tailscale (guide officiel)', 'Installare Tailscale (guida ufficiale)', 'Installar Tailscale (instrucziun uffiziala)'),
    'Tailscale: log in a device': ('Tailscale: ein Gerät anmelden', 'Tailscale : connecter un appareil', 'Tailscale: collegare un dispositivo', 'Tailscale: annunziar in apparat'),
    'Tailscale admin console → DNS': ('Tailscale-Verwaltung → DNS', 'Console Tailscale → DNS', 'Console Tailscale → DNS', 'Console Tailscale → DNS'),
    'Docs: enabling HTTPS certificates': ('Anleitung: HTTPS-Zertifikate einschalten', 'Doc : activer les certificats HTTPS', 'Guida: attivare i certificati HTTPS', 'Instrucziun: activar ils certificats HTTPS'),
    'Tailscale admin console → Access controls': ('Tailscale-Verwaltung → Access controls', 'Console Tailscale → Access controls', 'Console Tailscale → Access controls', 'Console Tailscale → Access controls'),
    'Docs: Tailscale Funnel': ('Anleitung: Tailscale Funnel', 'Doc : Tailscale Funnel', 'Guida: Tailscale Funnel', 'Instrucziun: Tailscale Funnel'),
    'Docs: tailscale funnel command': ('Anleitung: Befehl tailscale funnel', 'Doc : commande tailscale funnel', 'Guida: comando tailscale funnel', 'Instrucziun: cumond tailscale funnel'),
    'Docs: tailscale set --operator': ('Anleitung: tailscale set --operator', 'Doc : tailscale set --operator', 'Guida: tailscale set --operator', 'Instrucziun: tailscale set --operator'),
}
for _k, _v in _HX_FUNNEL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the manual (HELP_PAGE of 540): one point in «System & Netz» after «Fernzugriff (Tailscale)», German and English
_HELP_FUNNEL = {
    "de": ('<li><b>🌍 Online-Spiel über Tailscale Funnel</b> (Simulator → Karte «Spiel» → «Online über das WLAN hinaus»): für Freunde <i>ohne</i> Tailscale. '
           'Der Schalter macht <b>nur das Spiel</b> (<code>https://NAME.….ts.net/game/…/</code>) im Internet erreichbar; die Einladungslinks nehmen diese Adresse dann von selbst. '
           'Alles andere von MoveEye (Bild, Einstellungen, /api) antwortet über den Funnel mit «nicht gefunden» – auch mit Passwort. Er geht von selbst aus, wenn die letzte '
           'Einladung abläuft oder zurückgezogen wird, ohne Einladung nach 15 Minuten, spätestens nach 6 h (einstellbar 1–24 h) und beim Neustart von MoveEye. '
           'Einschalten darf nur der Administrator; jedes Ein / Aus und jeder Gast steht im Protokoll, beim Einschalten kommt eine Push-Nachricht. '
           '«https über Tailscale» (Port 443) bleibt, der Funnel weicht dann auf Port 8443 aus. Einmal in der Tailscale-Verwaltung nötig: '
           '<i>DNS</i> → MagicDNS und «HTTPS Certificates» einschalten, <i>Access controls</i> → <code>"nodeAttrs": [{"target": ["autogroup:member"], "attr": ["funnel"]}]</code>. '
           'Fehlt etwas, zeigt MoveEye genau, was zu tun ist (Anleitung: <a href="https://tailscale.com/kb/1223/funnel" target="_blank" rel="noopener">tailscale.com/kb/1223/funnel</a>).</li>'),
    "en": ('<li><b>🌍 Online game over Tailscale Funnel</b> (Simulator → card «Game» → «Online beyond the WLAN»): for friends <i>without</i> Tailscale. '
           'The switch makes <b>only the game</b> (<code>https://NAME.….ts.net/game/…/</code>) reachable on the internet; the invitation links then use this address by themselves. '
           'Everything else of MoveEye (picture, settings, /api) answers «not found» through the funnel – even with the password. It switches off by itself when the last '
           'invitation expires or is revoked, without an invitation after 15 minutes, at the latest after 6 h (1–24 h) and when MoveEye restarts. '
           'Only the administrator may switch it on; every on / off and every guest is logged, switching on sends a push message. '
           '«https over Tailscale» (port 443) stays, the funnel then uses port 8443. Needed once in the Tailscale admin console: '
           '<i>DNS</i> → switch on MagicDNS and «HTTPS Certificates», <i>Access controls</i> → <code>"nodeAttrs": [{"target": ["autogroup:member"], "attr": ["funnel"]}]</code>. '
           'If something is missing, MoveEye shows exactly what to do (docs: <a href="https://tailscale.com/kb/1223/funnel" target="_blank" rel="noopener">tailscale.com/kb/1223/funnel</a>).</li>'),
}


def _help_funnel(doc, lang):
    i = doc.find("<li><b>🌐 " + ("Fernzugriff (Tailscale):" if lang == "de" else "Remote access (Tailscale):"))
    j = doc.find("</li>", i) if i >= 0 else -1
    if j < 0 or "Tailscale Funnel</b>" in doc:
        return doc
    return doc[:j + 5] + _HELP_FUNNEL[lang] + doc[j + 5:]


_hp_enfn = HELP_PAGE.find('<div lang="en">')
if _hp_enfn > 0:
    HELP_PAGE = _help_funnel(HELP_PAGE[:_hp_enfn], "de") + _help_funnel(HELP_PAGE[_hp_enfn:], "en")
