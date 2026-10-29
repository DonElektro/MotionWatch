#@ MoveEye – Teil 619: Übersetzungen zu Teil 573 (App-Schlüssel, Sicherheit an einem Ort) und zur Rotlicht-Ansicht (578), Anleitung «Sicherheit und App-Schlüssel». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_sicher3 = {
    # ---- app keys (573) ----
    'App keys': ('App-Schlüssel', 'Clés d’app', 'Chiavi app', 'Clavs d’app'),
    'App key': ('App-Schlüssel', 'Clé d’app', 'Chiave app', 'Clav d’app'),
    'ak-note': ('Für andere Programme (Home Assistant, iPhone-Kurzbefehle, ein anderes MoveEye in der Geräte-Übersicht): ein Schlüssel statt des Passworts – geht auch über http. Ein Schlüssel kann nie das Passwort, die Benutzer, die App-Schlüssel oder die Sicherheits-Einstellungen ändern. Geht ein Gerät verloren: «Sperren».',
                'Pour d’autres programmes (Home Assistant, raccourcis iPhone, un autre MoveEye dans la vue des appareils) : une clé au lieu du mot de passe – marche aussi en http. Une clé ne peut jamais changer le mot de passe, les utilisateurs, les clés d’app ni les réglages de sécurité. Appareil perdu : «Bloquer».',
                'Per altri programmi (Home Assistant, comandi rapidi iPhone, un altro MoveEye nella panoramica dei dispositivi): una chiave invece della password – funziona anche in http. Una chiave non può mai cambiare la password, gli utenti, le chiavi app o le impostazioni di sicurezza. Dispositivo perso: «Bloccare».',
                'Per auters programs (Home Assistant, cumonds svelts iPhone, in auter MoveEye en la survista dals apparats): ina clav empè dal pled-clav – funcziuna er sur http. Ina clav na po mai midar il pled-clav, ils utilisaders, las clavs d’app u ils parameters da segirezza. Apparat pers: «Bloccar».'),
    'Make an app key': ('App-Schlüssel erstellen', 'Créer une clé d’app', 'Creare una chiave app', 'Crear ina clav d’app'),
    'Name (e.g. Home Assistant)': ('Name (z. B. Home Assistant)', 'Nom (p. ex. Home Assistant)', 'Nome (p. es. Home Assistant)', 'Num (p. ex. Home Assistant)'),
    'Block': ('Sperren', 'Bloquer', 'Bloccare', 'Bloccar'),
    'Block this key? Programs that use it get no access any more.': ('Diesen Schlüssel sperren? Programme, die ihn brauchen, kommen nicht mehr hinein.', 'Bloquer cette clé ? Les programmes qui l’utilisent n’auront plus accès.', 'Bloccare questa chiave? I programmi che la usano non avranno più accesso.', 'Bloccar questa clav? Programs che la duvran na han betg pli access.'),
    'No app keys yet.': ('Noch keine App-Schlüssel.', 'Pas encore de clé d’app.', 'Ancora nessuna chiave app.', 'Anc naginas clavs d’app.'),
    'made': ('erstellt', 'créée', 'creata', 'creà'),
    'last used': ('zuletzt gebraucht', 'dernière utilisation', 'ultimo uso', 'duvrà l’ultima giada'),
    'never': ('nie', 'jamais', 'mai', 'mai'),
    'Done': ('Fertig', 'Terminé', 'Fatto', 'Finì'),
    'Copy the key now - it is shown only this one time. MoveEye keeps only a fingerprint of it.': ('Den Schlüssel jetzt kopieren – er wird nur dieses eine Mal gezeigt. MoveEye behält nur einen Fingerabdruck davon.', 'Copie la clé maintenant – elle n’est montrée qu’une seule fois. MoveEye n’en garde qu’une empreinte.', 'Copia la chiave adesso – viene mostrata solo questa volta. MoveEye ne tiene solo un’impronta.', 'Copiar la clav ussa – ella vegn mussada mo questa giada. MoveEye tegna mo in stampun dad ella.'),
    'An app key cannot change the password, the users, the app keys or the security settings': ('Ein App-Schlüssel kann das Passwort, die Benutzer, die App-Schlüssel und die Sicherheits-Einstellungen nicht ändern', 'Une clé d’app ne peut pas changer le mot de passe, les utilisateurs, les clés d’app ni les réglages de sécurité', 'Una chiave app non può cambiare la password, gli utenti, le chiavi app o le impostazioni di sicurezza', 'Ina clav d’app na po betg midar il pled-clav, ils utilisaders, las clavs d’app u ils parameters da segirezza'),
    'unknown or blocked app key': ('unbekannter oder gesperrter App-Schlüssel', 'clé d’app inconnue ou bloquée', 'chiave app sconosciuta o bloccata', 'clav d’app nunenconuschenta u bloccada'),
    'For your safety an app key can only be made over the secure page': ('Zu deiner Sicherheit lässt sich ein App-Schlüssel nur über die sichere Seite erstellen', 'Pour ta sécurité, une clé d’app ne peut être créée que sur la page sécurisée', 'Per la tua sicurezza una chiave app si può creare solo sulla pagina sicura', 'Per tia segirezza po ina clav d’app vegnir creada mo sur la pagina segira'),
    'New keys only over the secure page (https) - the key would go unencrypted through the network.': ('Neue Schlüssel nur über die sichere Seite (https) – sonst ginge der Schlüssel unverschlüsselt durchs Netz.', 'Nouvelles clés seulement sur la page sécurisée (https) – sinon la clé passerait en clair sur le réseau.', 'Nuove chiavi solo sulla pagina sicura (https) – altrimenti la chiave passerebbe in chiaro nella rete.', 'Novas clavs mo sur la pagina segira (https) – uschiglio giess la clav betg codada tras la rait.'),
    'Without a web password every program can use MoveEye anyway - keys are needed only with a password.': ('Ohne Web-Passwort kann jedes Programm MoveEye sowieso benutzen – Schlüssel braucht es erst mit Passwort.', 'Sans mot de passe web, chaque programme peut de toute façon utiliser MoveEye – les clés ne servent qu’avec un mot de passe.', 'Senza password web ogni programma può comunque usare MoveEye – le chiavi servono solo con una password.', 'Senza pled-clav web po mintga program tuttina duvrar MoveEye – clavs dovri pir cun in pled-clav.'),
    'Example: Home Assistant and iPhone shortcuts': ('Beispiel: Home Assistant und iPhone-Kurzbefehle', 'Exemple : Home Assistant et raccourcis iPhone', 'Esempio: Home Assistant e comandi rapidi iPhone', 'Exempel: Home Assistant e cumonds svelts iPhone'),
    'iPhone shortcut «Get contents of URL»': ('iPhone-Kurzbefehl «Inhalte von URL abrufen»', 'raccourci iPhone «Obtenir le contenu de l’URL»', 'comando rapido iPhone «Ottieni contenuti dell’URL»', 'cumond svelt iPhone «Retschaiver il cuntegn da l’URL»'),
    'give the key a name (e.g. Home Assistant)': ('dem Schlüssel einen Namen geben (z. B. Home Assistant)', 'donne un nom à la clé (p. ex. Home Assistant)', 'dai un nome alla chiave (p. es. Home Assistant)', 'dar in num a la clav (p. ex. Home Assistant)'),
    'at most 20 app keys': ('höchstens 20 App-Schlüssel', 'au plus 20 clés d’app', 'al massimo 20 chiavi app', 'maximalmain 20 clavs d’app'),
    'unknown app key': ('unbekannter App-Schlüssel', 'clé d’app inconnue', 'chiave app sconosciuta', 'clav d’app nunenconuschenta'),
    'this name exists already': ('diesen Namen gibt es schon', 'ce nom existe déjà', 'questo nome esiste già', 'quest num exista gia'),
    # ---- security in one place (573) ----
    'Security': ('Sicherheit', 'Sécurité', 'Sicurezza', 'Segirezza'),
    'Users': ('Benutzer', 'Utilisateurs', 'Utenti', 'Utilisaders'),
    'Web password': ('Web-Passwort', 'Mot de passe web', 'Password web', 'Pled-clav web'),
    'Set / change the web password': ('Web-Passwort setzen / ändern', 'Définir / changer le mot de passe web', 'Impostare / cambiare la password web', 'Fixar / midar il pled-clav web'),
    'Security check': ('Sicherheits-Check', 'Contrôle de sécurité', 'Controllo di sicurezza', 'Controlla da segirezza'),
    'Check now': ('Jetzt prüfen', 'Vérifier maintenant', 'Controllare ora', 'Controllar ussa'),
    'running…': ('läuft…', 'en cours…', 'in corso…', 'en lavur…'),
    'What can be reached from the network or the internet, and what is risky.': ('Was aus dem Netz oder dem Internet erreichbar ist und was riskant ist.', 'Ce qui est accessible depuis le réseau ou internet, et ce qui est risqué.', 'Cosa è raggiungibile dalla rete o da internet, e cosa è rischioso.', 'Tge ch’è cuntanschibel da la rait u da l’internet e tge ch’è ristgà.'),
    '💾 Settings file': ('💾 Einstellungsdatei', '💾 Fichier de réglages', '💾 File delle impostazioni', '💾 Datoteca da parameters'),
    '🔐 Password, users and app keys: Settings → Security': ('🔐 Passwort, Benutzer und App-Schlüssel: Einstellungen → Sicherheit', '🔐 Mot de passe, utilisateurs et clés d’app : Réglages → Sécurité', '🔐 Password, utenti e chiavi app: Impostazioni → Sicurezza', '🔐 Pled-clav, utilisaders e clavs d’app: Parameters → Segirezza'),
    'Password, users and app keys: Settings → Security': ('Passwort, Benutzer und App-Schlüssel: Einstellungen → Sicherheit', 'Mot de passe, utilisateurs et clés d’app : Réglages → Sécurité', 'Password, utenti e chiavi app: Impostazioni → Sicurezza', 'Pled-clav, utilisaders e clavs d’app: Parameters → Segirezza'),
    'now in Settings → Security': ('jetzt unter Einstellungen → Sicherheit', 'maintenant dans Réglages → Sécurité', 'ora in Impostazioni → Sicurezza', 'ussa sut Parameters → Segirezza'),
    # the lines of the security check (300) - before only in the tools page (German)
    'Web password set': ('Web-Passwort gesetzt', 'Mot de passe web défini', 'Password web impostata', 'Pled-clav web fixà'),
    'Web password missing': ('Web-Passwort fehlt', 'Mot de passe web manquant', 'Manca la password web', 'Il pled-clav web manca'),
    'Everybody in the network can operate MoveEye': ('Jeder im Netz kann MoveEye bedienen', 'Tout le monde dans le réseau peut utiliser MoveEye', 'Chiunque nella rete può usare MoveEye', 'Mintgin en la rait po manischar MoveEye'),
    'Secure page (https) on': ('Sichere Seite (https) ein', 'Page sécurisée (https) activée', 'Pagina sicura (https) attiva', 'Pagina segira (https) activada'),
    'Secure page (https) off': ('Sichere Seite (https) aus', 'Page sécurisée (https) désactivée', 'Pagina sicura (https) spenta', 'Pagina segira (https) deactivada'),
    'Passwords go through the network unencrypted - important in foreign Wi-Fi (camping)': ('Passwörter gehen unverschlüsselt durchs Netz – wichtig in fremden WLANs (Camping)', 'Les mots de passe passent en clair sur le réseau – important dans un Wi-Fi étranger (camping)', 'Le password passano in chiaro nella rete – importante nelle Wi-Fi altrui (campeggio)', 'Ils pleds-clav van betg codads tras la rait – impurtant en WLANs esters (camping)'),
    'Open in the network: port': ('Offen im Netz: Port', 'Ouvert dans le réseau : port', 'Aperto nella rete: porta', 'Avert en la rait: port'),
    'SSH: login with password allowed': ('SSH: Anmelden mit Passwort erlaubt', 'SSH : connexion par mot de passe autorisée', 'SSH: accesso con password consentito', 'SSH: s’annunziar cun pled-clav permess'),
    'SSH: login with password off (keys only)': ('SSH: Anmelden mit Passwort aus (nur Schlüssel)', 'SSH : connexion par mot de passe désactivée (clés seulement)', 'SSH: accesso con password spento (solo chiavi)', 'SSH: s’annunziar cun pled-clav deactivà (mo clavs)'),
    'Use a strong password or keys': ('Starkes Passwort oder Schlüssel verwenden', 'Utilise un mot de passe fort ou des clés', 'Usa una password forte o chiavi', 'Duvrar in pled-clav ferm u clavs'),
    'Public IPv6 address present': ('Öffentliche IPv6-Adresse vorhanden', 'Adresse IPv6 publique présente', 'Indirizzo IPv6 pubblico presente', 'Adressa IPv6 publica avant maun'),
    'Depending on the router the Pi can be reached directly from the internet - keep the web password on': ('Je nach Router ist der Pi direkt aus dem Internet erreichbar – Web-Passwort eingeschaltet lassen', 'Selon le routeur, le Pi est joignable directement depuis internet – garde le mot de passe web', 'A seconda del router il Pi è raggiungibile direttamente da internet – tieni attiva la password web', 'Tenor router è il Pi cuntanschibel directamain da l’internet – laschar activà il pled-clav web'),
    'Router forwards ports to this device:': ('Router leitet Ports an dieses Gerät weiter:', 'Le routeur redirige des ports vers cet appareil :', 'Il router inoltra porte a questo dispositivo:', 'Il router renviescha ports a quest apparat:'),
    'No port forwarding of the router to this device (UPnP)': ('Keine Port-Weiterleitung des Routers an dieses Gerät (UPnP)', 'Pas de redirection de port du routeur vers cet appareil (UPnP)', 'Nessun inoltro di porte del router a questo dispositivo (UPnP)', 'Nagin renviament da ports dal router a quest apparat (UPnP)'),
    'Address in the internet:': ('Adresse im Internet:', 'Adresse sur internet :', 'Indirizzo in internet:', 'Adressa en l’internet:'),
    'shared address of the mobile network - not reachable from outside': ('geteilte Adresse des Handynetzes – von aussen nicht erreichbar', 'adresse partagée du réseau mobile – pas joignable de l’extérieur', 'indirizzo condiviso della rete mobile – non raggiungibile dall’esterno', 'adressa cundividida da la rait mobila – betg cuntanschibla dad ordaifer'),
    'Internet not reachable': ('Internet nicht erreichbar', 'Internet pas joignable', 'Internet non raggiungibile', 'Internet betg cuntanschibel'),
    'Tailscale: access from outside only for your own devices': ('Tailscale: Zugriff von aussen nur für die eigenen Geräte', 'Tailscale : accès de l’extérieur seulement pour tes propres appareils', 'Tailscale: accesso dall’esterno solo per i propri dispositivi', 'Tailscale: access dad ordaifer mo per ils agens apparats'),
    # ---- «Rotlicht-Ansicht» = 3rd step of the theme button (578) ----
    'Red light view': ('Rotlicht-Ansicht', 'Vue lumière rouge', 'Vista luce rossa', 'Vista glisch cotschna'),
    'Light / dark / red light': ('Hell / dunkel / Rotlicht', 'Clair / sombre / lumière rouge', 'Chiaro / scuro / luce rossa', 'Cler / stgir / glisch cotschna'),
    'Light': ('Hell', 'Clair', 'Chiaro', 'Cler'),
    'Dark': ('Dunkel', 'Sombre', 'Scuro', 'Stgir'),
}
for _k, _v in _HX_sicher3.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the German of the web script (573) from here - one place for the texts (fr / it / rm come through /i18n/<lang>.js)
WEB_PAGE = WEB_PAGE.replace("/*AKDE*/{}", json.dumps({_k: DE.get(_k, _v[0]) for _k, _v in _HX_sicher3.items()}, ensure_ascii=False), 1)


# ---- the manual: «Sicherheit und App-Schlüssel» (before «Tipps», like 613) ------------------------------------------------------
_HELP_SICHER3 = {
    "de": '<section id="appkeys" data-icon="🔑"><h2>Sicherheit und App-Schlüssel</h2>'
          '<p>Alles zur Sicherheit steht an einem Ort: <b>Einstellungen → Sicherheit</b> – Web-Passwort, Benutzer, vertrauenswürdige Geräte, '
          '«Anmelden nur verschlüsselt», die App-Schlüssel und der Sicherheits-Check (früher unter Werkzeuge). Im Fenster genauso.</p>'
          '<p><b>🔑 App-Schlüssel</b> sind für andere Programme: Home Assistant, iPhone-Kurzbefehle oder ein älteres MoveEye in der Geräte-Übersicht. '
          'Seit «Anmelden nur verschlüsselt» nimmt MoveEye das Passwort über http von anderen Geräten nicht mehr an – ein Schlüssel geht auch über http. '
          '«App-Schlüssel erstellen» mit einem Namen: der Schlüssel (beginnt mit <code>me_</code>) wird <b>nur einmal</b> ganz gezeigt – gleich kopieren. '
          'MoveEye speichert nur einen Fingerabdruck davon. Die Liste zeigt Name, erstellt und zuletzt gebraucht; «Sperren», wenn ein Gerät verloren geht. '
          'Ein Schlüssel kann alles bedienen, aber <b>nie</b> das Passwort, die Benutzer, die App-Schlüssel oder die Sicherheits-Einstellungen ändern. '
          'Falsche Schlüssel sperren wie falsche Passwörter (8 in 5 Minuten).</p>'
          '<p>So schickt ein Programm den Schlüssel mit: als Kopfzeile <code>X-MoveEye-Key: me_…</code> oder <code>Authorization: Bearer me_…</code>, '
          'für einfache Kurzbefehle als <code>?key=me_…</code> am Ende der Adresse, oder als Passwort (beliebiger Benutzername) – so auch beim älteren MoveEye in der Geräte-Übersicht. '
          'Die Kurzbefehl-Adressen <code>/k/&lt;Schlüssel&gt;/arm</code>, <code>/status</code>, <code>/photo.jpg</code> … nehmen auch einen App-Schlüssel.</p>'
          '<p><b>Beispiel Home Assistant</b> (configuration.yaml, den Schlüssel in secrets.yaml als <code>moveeye_key</code>):</p>'
          '<pre>rest:\n  - resource: http://192.168.1.50:5000/api/state\n    headers:\n      X-MoveEye-Key: !secret moveeye_key\n    sensor:\n'
          '      - name: MoveEye Personen\n        value_template: "{{ value_json.persons }}"</pre>'
          '<p><b>Beispiel iPhone-Kurzbefehl:</b> Aktion «Inhalte von URL abrufen» mit <code>http://192.168.1.50:5000/k/me_…/status</code> '
          '(oder <code>/k/me_…/arm</code> zum Einschalten). Die Adresse oben ist ein Beispiel – deine steht in der Adresszeile des Browsers.</p></section>\n\n',
    "en": '<section id="appkeys" data-icon="🔑"><h2>Security and app keys</h2>'
          '<p>Everything about security is in one place: <b>Settings → Security</b> – web password, users, trusted devices, '
          '«Log in only encrypted», the app keys and the security check (before under Tools). The same in the window.</p>'
          '<p><b>🔑 App keys</b> are for other programs: Home Assistant, iPhone shortcuts or an older MoveEye in the device overview. '
          'Since «Log in only encrypted» MoveEye no longer takes the password over http from other devices – a key works over http too. '
          '«Make an app key» with a name: the key (starts with <code>me_</code>) is shown in full <b>only once</b> – copy it right away. '
          'MoveEye keeps only a fingerprint of it. The list shows name, made and last used; «Block» when a device is lost. '
          'A key can operate everything but <b>never</b> change the password, the users, the app keys or the security settings. '
          'Wrong keys lock like wrong passwords (8 in 5 minutes).</p>'
          '<p>How a program sends the key: as header <code>X-MoveEye-Key: me_…</code> or <code>Authorization: Bearer me_…</code>, '
          'for simple shortcuts as <code>?key=me_…</code> at the end of the address, or as the password (any user name) – also for an older MoveEye in the device overview. '
          'The shortcut addresses <code>/k/&lt;key&gt;/arm</code>, <code>/status</code>, <code>/photo.jpg</code> … take an app key too.</p>'
          '<p><b>Example Home Assistant</b> (configuration.yaml, the key in secrets.yaml as <code>moveeye_key</code>):</p>'
          '<pre>rest:\n  - resource: http://192.168.1.50:5000/api/state\n    headers:\n      X-MoveEye-Key: !secret moveeye_key\n    sensor:\n'
          '      - name: MoveEye persons\n        value_template: "{{ value_json.persons }}"</pre>'
          '<p><b>Example iPhone shortcut:</b> action «Get contents of URL» with <code>http://192.168.1.50:5000/k/me_…/status</code> '
          '(or <code>/k/me_…/arm</code> to arm). The address is an example – yours is in the address bar of the browser.</p></section>\n\n',
    "fr": '<section id="appkeys" data-icon="🔑"><h2>Sécurité et clés d’app</h2>'
          '<p>Tout ce qui touche à la sécurité est à un seul endroit : <b>Réglages → Sécurité</b> – mot de passe web, utilisateurs, appareils de confiance, '
          '«Connexion seulement chiffrée», les clés d’app et le contrôle de sécurité (avant sous Outils). Pareil dans la fenêtre.</p>'
          '<p><b>🔑 Les clés d’app</b> sont pour d’autres programmes : Home Assistant, raccourcis iPhone ou un ancien MoveEye dans la vue des appareils. '
          'Depuis «Connexion seulement chiffrée», MoveEye n’accepte plus le mot de passe en http depuis d’autres appareils – une clé marche aussi en http. '
          '«Créer une clé d’app» avec un nom : la clé (commence par <code>me_</code>) n’est montrée en entier <b>qu’une fois</b> – copie-la tout de suite. '
          'MoveEye n’en garde qu’une empreinte. La liste montre le nom, la création et la dernière utilisation ; «Bloquer» si un appareil est perdu. '
          'Une clé peut tout utiliser mais <b>jamais</b> changer le mot de passe, les utilisateurs, les clés d’app ni les réglages de sécurité. '
          'Les mauvaises clés bloquent comme les mauvais mots de passe (8 en 5 minutes).</p>'
          '<p>Un programme envoie la clé : en en-tête <code>X-MoveEye-Key: me_…</code> ou <code>Authorization: Bearer me_…</code>, '
          'pour des raccourcis simples en <code>?key=me_…</code> à la fin de l’adresse, ou comme mot de passe (nom d’utilisateur quelconque). '
          'Les adresses de raccourci <code>/k/&lt;clé&gt;/arm</code>, <code>/status</code>, <code>/photo.jpg</code> … acceptent aussi une clé d’app.</p>'
          '<p><b>Exemple Home Assistant</b> (configuration.yaml, la clé dans secrets.yaml sous <code>moveeye_key</code>) :</p>'
          '<pre>rest:\n  - resource: http://192.168.1.50:5000/api/state\n    headers:\n      X-MoveEye-Key: !secret moveeye_key\n    sensor:\n'
          '      - name: MoveEye personnes\n        value_template: "{{ value_json.persons }}"</pre>'
          '<p><b>Exemple raccourci iPhone :</b> action «Obtenir le contenu de l’URL» avec <code>http://192.168.1.50:5000/k/me_…/status</code>. '
          'L’adresse est un exemple – la tienne est dans la barre d’adresse du navigateur.</p></section>\n\n',
    "it": '<section id="appkeys" data-icon="🔑"><h2>Sicurezza e chiavi app</h2>'
          '<p>Tutto sulla sicurezza è in un solo posto: <b>Impostazioni → Sicurezza</b> – password web, utenti, dispositivi fidati, '
          '«Accesso solo cifrato», le chiavi app e il controllo di sicurezza (prima sotto Strumenti). Lo stesso nella finestra.</p>'
          '<p><b>🔑 Le chiavi app</b> sono per altri programmi: Home Assistant, comandi rapidi iPhone o un MoveEye più vecchio nella panoramica dei dispositivi. '
          'Da «Accesso solo cifrato» MoveEye non accetta più la password in http da altri dispositivi – una chiave funziona anche in http. '
          '«Creare una chiave app» con un nome: la chiave (inizia con <code>me_</code>) viene mostrata intera <b>una sola volta</b> – copiala subito. '
          'MoveEye ne tiene solo un’impronta. La lista mostra nome, creazione e ultimo uso; «Bloccare» se un dispositivo va perso. '
          'Una chiave può usare tutto ma <b>mai</b> cambiare la password, gli utenti, le chiavi app o le impostazioni di sicurezza. '
          'Le chiavi sbagliate bloccano come le password sbagliate (8 in 5 minuti).</p>'
          '<p>Un programma invia la chiave: come intestazione <code>X-MoveEye-Key: me_…</code> o <code>Authorization: Bearer me_…</code>, '
          'per comandi rapidi semplici come <code>?key=me_…</code> alla fine dell’indirizzo, o come password (nome utente qualsiasi). '
          'Gli indirizzi dei comandi rapidi <code>/k/&lt;chiave&gt;/arm</code>, <code>/status</code>, <code>/photo.jpg</code> … accettano anche una chiave app.</p>'
          '<p><b>Esempio Home Assistant</b> (configuration.yaml, la chiave in secrets.yaml come <code>moveeye_key</code>):</p>'
          '<pre>rest:\n  - resource: http://192.168.1.50:5000/api/state\n    headers:\n      X-MoveEye-Key: !secret moveeye_key\n    sensor:\n'
          '      - name: MoveEye persone\n        value_template: "{{ value_json.persons }}"</pre>'
          '<p><b>Esempio comando rapido iPhone:</b> azione «Ottieni contenuti dell’URL» con <code>http://192.168.1.50:5000/k/me_…/status</code>. '
          'L’indirizzo è un esempio – il tuo è nella barra degli indirizzi del browser.</p></section>\n\n',
    "rm": '<section id="appkeys" data-icon="🔑"><h2>Segirezza e clavs d’app</h2>'
          '<p>Tut davart la segirezza è en in lieu: <b>Parameters → Segirezza</b> – pled-clav web, utilisaders, apparats da confidenza, '
          '«S’annunziar mo codà», las clavs d’app e la controlla da segirezza (pli baud sut Utensils). Medemamain en la fanestra.</p>'
          '<p><b>🔑 Clavs d’app</b> èn per auters programs: Home Assistant, cumonds svelts iPhone u in MoveEye pli vegl en la survista dals apparats. '
          'Dapi «S’annunziar mo codà» na prenda MoveEye betg pli il pled-clav sur http dad auters apparats – ina clav funcziuna er sur http. '
          '«Crear ina clav d’app» cun in num: la clav (cumenza cun <code>me_</code>) vegn mussada entira <b>mo ina giada</b> – copiar dalunga. '
          'MoveEye tegna mo in stampun dad ella. La glista mussa num, creà e duvrà l’ultima giada; «Bloccar», sch’in apparat va a perder. '
          'Ina clav po manischar tut, ma <b>mai</b> midar il pled-clav, ils utilisaders, las clavs d’app u ils parameters da segirezza. '
          'Clavs faussas bloccan sco pleds-clav fauss (8 en 5 minutas).</p>'
          '<p>In program trametta la clav: sco lingia da chau <code>X-MoveEye-Key: me_…</code> u <code>Authorization: Bearer me_…</code>, '
          'per cumonds svelts simpels sco <code>?key=me_…</code> a la fin da l’adressa, u sco pled-clav (num d’utilisader qualunque). '
          'Las adressas da cumonds svelts <code>/k/&lt;clav&gt;/arm</code>, <code>/status</code>, <code>/photo.jpg</code> … prendan er ina clav d’app.</p>'
          '<p><b>Exempel Home Assistant</b> (configuration.yaml, la clav en secrets.yaml sco <code>moveeye_key</code>):</p>'
          '<pre>rest:\n  - resource: http://192.168.1.50:5000/api/state\n    headers:\n      X-MoveEye-Key: !secret moveeye_key\n    sensor:\n'
          '      - name: MoveEye persunas\n        value_template: "{{ value_json.persons }}"</pre>'
          '<p><b>Exempel cumond svelt iPhone:</b> acziun «Retschaiver il cuntegn da l’URL» cun <code>http://192.168.1.50:5000/k/me_…/status</code>. '
          'L’adressa è in exempel – la tia stat en la lingia d’adressa dal navigatur.</p></section>\n\n',
}


def _help_sicher3(doc, lang):
    if '<section id="appkeys"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    if i < 0:
        i = doc.find('<section id="privacy"')
    return doc[:i] + _HELP_SICHER3[lang] + doc[i:] if i >= 0 else doc


_hp_en3 = HELP_PAGE.find('<div lang="en">')
if _hp_en3 > 0:
    HELP_PAGE = _help_sicher3(HELP_PAGE[:_hp_en3], "de") + _help_sicher3(HELP_PAGE[_hp_en3:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_sicher3(HELP_X[_L], _L)
