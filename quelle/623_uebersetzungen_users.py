#@ MoveEye – Teil 623: Übersetzungen und Anleitung «Benutzer und Handys» (Rollen, Zeitfenster, Handy verknüpfen, Push pro Benutzer; Teile 040, 041, 547, 573). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_USERS = {
    # ---- roles and rights ----
    'Child': ('Kind', 'Enfant', 'Bambino', 'Uffant'),
    'Friend': ('Freund', 'Ami', 'Amico', 'Ami'),
    'Family': ('Familie', 'Famille', 'Famiglia', 'Famiglia'),
    'View only': ('Nur ansehen', 'Voir seulement', 'Solo guardare', 'Mo guardar'),
    'Own rights': ('Eigene Rechte', 'Droits propres', 'Diritti propri', 'Agens dretgs'),
    'Live picture': ('Livebild', 'Image en direct', 'Immagine live', 'Maletg live'),
    'Recordings': ('Aufnahmen', 'Enregistrements', 'Registrazioni', 'Registraziuns'),
    'Protection on / off': ('Schutz an / aus', 'Protection on / off', 'Protezione on / off', 'Protecziun en / ora'),
    'Switch the light': ('Licht schalten', 'Allumer la lumière', 'Accendere la luce', 'Envidar la glisch'),
    'Siren': ('Sirene', 'Sirène', 'Sirena', 'Sirena'),
    'Games / game corner': ('Spiele / Spielecke', 'Jeux / coin jeux', 'Giochi / angolo giochi', 'Gieus / chantun da gieus'),
    'Talk (intercom)': ('Gegensprechen', 'Interphone', 'Citofono', 'Intercom'),
    'Steer the head': ('Kopf steuern', 'Diriger la tête', 'Guidare la testa', 'Guidar il chau'),
    'Alarms': ('Alarme', 'Alarmes', 'Allarmi', 'Alarms'),
    'Infos': ('Infos', 'Infos', 'Info', 'Infos'),
    'Game invitations': ('Spiel-Einladungen', 'Invitations aux jeux', 'Inviti ai giochi', 'Invitaziuns da gieu'),
    # ---- the card «Users» (547) ----
    'Each person gets an own access: a role decides what they may do, a phone is linked with a QR code (no password needed). The web password stays the administrator. The log shows who switched what.':
        ('Jede Person bekommt einen eigenen Zugang: die Rolle bestimmt, was sie darf, ein Handy wird mit einem QR-Code verknüpft (kein Passwort nötig). Das Web-Passwort bleibt der Administrator. Im Protokoll steht, wer was geschaltet hat.',
         'Chaque personne reçoit son propre accès : le rôle décide de ce qu’elle peut faire, un téléphone est lié avec un code QR (pas de mot de passe). Le mot de passe web reste l’administrateur. Le journal montre qui a changé quoi.',
         'Ogni persona riceve un accesso proprio: il ruolo decide cosa può fare, un telefono viene collegato con un codice QR (senza password). La password web resta l’amministratore. Il registro mostra chi ha cambiato cosa.',
         'Mintga persuna survegn in agen access: la rolla decida tge ch’ella dastga far, in telefonin vegn collià cun in code QR (nagin pled-clav). Il pled-clav web resta l’administratur. Il protocol mussa tgi ch’ha midà tge.'),
    'For short visits the guest link is enough (Live → Guest access). For people who come again and again, better create a user here.':
        ('Für kurze Besuche reicht der Gastlink (Live → Gastzugang). Für feste Personen lieber hier einen Benutzer anlegen.',
         'Pour de courtes visites, le lien invité suffit (Direct → Accès invité). Pour les personnes qui reviennent, mieux vaut créer un utilisateur ici.',
         'Per visite brevi basta il link ospite (Live → Accesso ospite). Per persone fisse meglio creare qui un utente.',
         'Per curtas visitas basta la colliaziun da giast (Live → Access da giast). Per persunas fixas meglier crear qua in utilisader.'),
    'For short visits the guest link is enough. For people who come again and again, better create a user here.':
        ('Für kurze Besuche reicht der Gastlink. Für feste Personen lieber hier einen Benutzer anlegen.',
         'Pour de courtes visites, le lien invité suffit. Pour les personnes qui reviennent, mieux vaut créer un utilisateur ici.',
         'Per visite brevi basta il link ospite. Per persone fisse meglio creare qui un utente.',
         'Per curtas visitas basta la colliaziun da giast. Per persunas fixas meglier crear qua in utilisader.'),
    'For people who come again and again, better create a user (Settings → Security → Users).':
        ('Für feste Personen lieber einen Benutzer anlegen (Einstellungen → Sicherheit → Benutzer).',
         'Pour les personnes qui reviennent, mieux vaut créer un utilisateur (Réglages → Sécurité → Utilisateurs).',
         'Per persone fisse meglio creare un utente (Impostazioni → Sicurezza → Utenti).',
         'Per persunas fixas meglier crear in utilisader (Parameters → Segirezza → Utilisaders).'),
    'active': ('aktiv', 'actif', 'attivo', 'activ'),
    'not active right now': ('gerade nicht aktiv', 'pas actif en ce moment', 'non attivo al momento', 'gist betg activ'),
    'Access time and messages': ('Zugangszeit und Nachrichten', 'Horaires d’accès et messages', 'Orari di accesso e messaggi', 'Temp d’access e messadis'),
    'Only at certain times': ('Nur zu bestimmten Zeiten', 'Seulement à certaines heures', 'Solo in certi orari', 'Mo a tschertas uras'),
    'no end': ('kein Ende', 'pas de fin', 'nessuna fine', 'nagina fin'),
    'Valid until': ('Gültig bis', 'Valable jusqu’au', 'Valido fino al', 'Valaivel fin'),
    'Push messages for this person:': ('Push-Nachrichten für diese Person:', 'Notifications pour cette personne :', 'Notifiche per questa persona:', 'Messadis push per questa persuna:'),
    'Browser push': ('Browser-Push', 'Push du navigateur', 'Push del browser', 'Push dal navigatur'),
    'device(s)': ('Gerät(e)', 'appareil(s)', 'dispositivo/i', 'apparat(s)'),
    'none yet - the person switches it on in their own browser (Settings → Notifications)':
        ('noch keiner – die Person schaltet es im eigenen Browser ein (Einstellungen → Benachrichtigungen)',
         'aucun encore – la personne l’active dans son propre navigateur (Réglages → Notifications)',
         'ancora nessuno – la persona lo attiva nel proprio browser (Impostazioni → Notifiche)',
         'anc nagin – la persuna l’activescha en ses agen navigatur (Parameters → Avis)'),
    'own ntfy topic (optional)': ('eigenes ntfy-Thema (freiwillig)', 'propre sujet ntfy (facultatif)', 'argomento ntfy proprio (facoltativo)', 'agen tema ntfy (facultativ)'),
    'Remove own ntfy topic': ('Eigenes ntfy-Thema entfernen', 'Retirer le sujet ntfy propre', 'Rimuovere l’argomento ntfy proprio', 'Allontanar l’agen tema ntfy'),
    'Link a phone': ('Handy verknüpfen', 'Lier un téléphone', 'Collegare un telefono', 'Colliar in telefonin'),
    'Scan with the camera of the phone of': ('Mit der Kamera des Handys scannen von', 'Scanner avec l’appareil photo du téléphone de', 'Scansionare con la fotocamera del telefono di', 'Scannar cun la camera dal telefonin da'),
    'Valid 10 minutes, only once. The phone is then logged in without a password.':
        ('Gültig 10 Minuten, nur einmal. Das Handy ist danach ohne Passwort angemeldet.',
         'Valable 10 minutes, une seule fois. Le téléphone est ensuite connecté sans mot de passe.',
         'Valido 10 minuti, una sola volta. Il telefono è poi connesso senza password.',
         'Valaivel 10 minutas, mo ina giada. Il telefonin è lura annunzià senza pled-clav.'),
    'Without the secure page (https) the link goes unencrypted through the Wi-Fi.':
        ('Ohne sichere Seite (https) geht der Link unverschlüsselt durchs WLAN.',
         'Sans la page sécurisée (https), le lien passe non chiffré par le Wi-Fi.',
         'Senza la pagina sicura (https) il link passa non cifrato nel Wi-Fi.',
         'Senza la pagina segira (https) va la colliaziun betg codada tras il WLAN.'),
    'No own password - logs in only with a linked phone.': ('Kein eigenes Passwort – meldet sich nur mit einem verknüpften Handy an.', 'Pas de mot de passe propre – se connecte seulement avec un téléphone lié.', 'Nessuna password propria – accede solo con un telefono collegato.', 'Nagin agen pled-clav – s’annunzia mo cun in telefonin collià.'),
    'Remove this device? It is logged out at once.': ('Dieses Gerät entfernen? Es wird sofort abgemeldet.', 'Retirer cet appareil ? Il est déconnecté tout de suite.', 'Rimuovere questo dispositivo? Viene disconnesso subito.', 'Allontanar quest apparat? El vegn deconnectà immediatamain.'),
    'Password (optional, 6–64)': ('Passwort (freiwillig, 6–64)', 'Mot de passe (facultatif, 6–64)', 'Password (facoltativa, 6–64)', 'Pled-clav (facultativ, 6–64)'),
    'New user': ('Neuer Benutzer', 'Nouvel utilisateur', 'Nuovo utente', 'Nov utilisader'),
    'Without a password the person logs in only with a linked phone (QR code).':
        ('Ohne Passwort meldet sich die Person nur mit einem verknüpften Handy an (QR-Code).',
         'Sans mot de passe, la personne se connecte seulement avec un téléphone lié (code QR).',
         'Senza password la persona accede solo con un telefono collegato (codice QR).',
         'Senza pled-clav s’annunzia la persuna mo cun in telefonin collià (code QR).'),
    'Own rights, time window and push per person: on the web page (Settings → Security → Users).':
        ('Eigene Rechte, Zeitfenster und Push pro Person: auf der Webseite (Einstellungen → Sicherheit → Benutzer).',
         'Droits propres, plage horaire et push par personne : sur la page web (Réglages → Sécurité → Utilisateurs).',
         'Diritti propri, fascia oraria e push per persona: sulla pagina web (Impostazioni → Sicurezza → Utenti).',
         'Agens dretgs, fanestra da temp e push per persuna: sin la pagina web (Parameters → Segirezza → Utilisaders).'),
    'Mo': ('Mo', 'Lu', 'Lu', 'Gli'), 'Tu': ('Di', 'Ma', 'Ma', 'Ma'), 'We': ('Mi', 'Me', 'Me', 'Me'), 'Th': ('Do', 'Je', 'Gi', 'Gie'),
    'Fr': ('Fr', 'Ve', 'Ve', 'Ve'), 'Sa': ('Sa', 'Sa', 'Sa', 'So'), 'Su': ('So', 'Di', 'Do', 'Du'),
    'daily': ('täglich', 'chaque jour', 'ogni giorno', 'mintga di'),
    'until': ('bis', 'jusqu’au', 'fino al', 'fin'),
    # ---- server (041 / 040) ----
    'Access not active right now': ('Zugang gerade nicht aktiv', 'Accès pas actif en ce moment', 'Accesso non attivo al momento', 'Access gist betg activ'),
    'Your access is not active right now.': ('Dein Zugang ist gerade nicht aktiv.', 'Ton accès n’est pas actif en ce moment.', 'Il tuo accesso non è attivo al momento.', 'Tes access n’è gist betg activ.'),
    'This access has expired.': ('Dieser Zugang ist abgelaufen.', 'Cet accès a expiré.', 'Questo accesso è scaduto.', 'Quest access è scadì.'),
    'Hello': ('Hallo', 'Bonjour', 'Ciao', 'Allegra'),
    'Access': ('Zugang', 'Accès', 'Accesso', 'Access'),
    'Ask the owner of MoveEye if you need it now.': ('Frag die Besitzerin oder den Besitzer von MoveEye, wenn du es jetzt brauchst.', 'Demande au propriétaire de MoveEye si tu en as besoin maintenant.', 'Chiedi al proprietario di MoveEye se ti serve adesso.', 'Dumonda la possessura u il possessur da MoveEye, sche ti dovras quai ussa.'),
    'Try again': ('Nochmals versuchen', 'Réessayer', 'Riprova', 'Empruvar anc ina giada'),
    'Link not valid': ('Link ungültig', 'Lien pas valable', 'Link non valido', 'Colliaziun betg valaivla'),
    'This link is not valid any more (10 minutes, only once). Ask for a new QR code.':
        ('Dieser Link gilt nicht mehr (10 Minuten, nur einmal). Bitte einen neuen QR-Code zeigen lassen.',
         'Ce lien n’est plus valable (10 minutes, une seule fois). Demande un nouveau code QR.',
         'Questo link non è più valido (10 minuti, una sola volta). Chiedi un nuovo codice QR.',
         'Questa colliaziun na vala betg pli (10 minutas, mo ina giada). Dumonda in nov code QR.'),
    'Link blocked': ('Link gesperrt', 'Lien bloqué', 'Link bloccato', 'Colliaziun bloccada'),
    'This link was opened without encryption (http) and is blocked now for safety. Make a new QR code and scan it - it leads to the secure page (https).':
        ('Dieser Link wurde unverschlüsselt (http) geöffnet und ist zur Sicherheit jetzt gesperrt. Einen neuen QR-Code erzeugen und scannen – er führt auf die sichere Seite (https).',
         'Ce lien a été ouvert sans chiffrement (http) et est maintenant bloqué par sécurité. Crée un nouveau code QR et scanne-le – il mène à la page sécurisée (https).',
         'Questo link è stato aperto senza cifratura (http) ed è ora bloccato per sicurezza. Crea un nuovo codice QR e scansionalo – porta alla pagina sicura (https).',
         'Questa colliaziun è vegnida averta senza codaziun (http) ed è ussa bloccada per segirezza. Crear in nov code QR e scannar – el maina a la pagina segira (https).'),
    'This user does not exist any more.': ('Diesen Benutzer gibt es nicht mehr.', 'Cet utilisateur n’existe plus.', 'Questo utente non esiste più.', 'Quest utilisader n’exista betg pli.'),
    'Phone linked': ('Handy verknüpft', 'Téléphone lié', 'Telefono collegato', 'Telefonin collià'),
    'This phone is now logged in as': ('Dieses Handy ist jetzt angemeldet als', 'Ce téléphone est maintenant connecté comme', 'Questo telefono è ora connesso come', 'Quest telefonin è ussa annunzià sco'),
    'No password needed. The owner can remove it at any time.': ('Kein Passwort nötig. Der Besitzer kann es jederzeit entfernen.', 'Pas de mot de passe. Le propriétaire peut le retirer à tout moment.', 'Nessuna password. Il proprietario può rimuoverlo in ogni momento.', 'Nagin pled-clav. Il possessur al po allontanar da tut temp.'),
    'Open MoveEye': ('MoveEye öffnen', 'Ouvrir MoveEye', 'Aprire MoveEye', 'Avrir MoveEye'),
    '🎲 Games are open': ('🎲 Die Spiele sind offen', '🎲 Les jeux sont ouverts', '🎲 I giochi sono aperti', '🎲 Ils gieus èn averts'),
    'Come to the game corner - scan the QR code there or open MoveEye.': ('Komm in die Spielecke – dort den QR-Code scannen oder MoveEye öffnen.', 'Viens au coin jeux – scanne le code QR là-bas ou ouvre MoveEye.', 'Vieni nell’angolo giochi – scansiona lì il codice QR o apri MoveEye.', 'Vegn en il chantun da gieus – scannar là il code QR u avrir MoveEye.'),
    'unknown user': ('unbekannter Benutzer', 'utilisateur inconnu', 'utente sconosciuto', 'utilisader nunenconuschent'),
    'unknown device': ('unbekanntes Gerät', 'appareil inconnu', 'dispositivo sconosciuto', 'apparat nunenconuschent'),
    'too many open links - wait 10 minutes': ('zu viele offene Links – 10 Minuten warten', 'trop de liens ouverts – attendre 10 minutes', 'troppi link aperti – aspettare 10 minuti', 'memia bleras colliaziuns avertas – spetgar 10 minutas'),
    'no network address of MoveEye': ('keine Netzadresse von MoveEye', 'pas d’adresse réseau de MoveEye', 'nessun indirizzo di rete di MoveEye', 'nagina adressa da rait da MoveEye'),
    'time: hh:mm': ('Zeit: hh:mm', 'heure : hh:mm', 'ora: hh:mm', 'temp: hh:mm'),
    'date: yyyy-mm-dd': ('Datum: jjjj-mm-tt', 'date : aaaa-mm-jj', 'data: aaaa-mm-gg', 'data: oooo-mm-dd'),
    'ntfy: a topic (6 to 64 letters, digits, - _) or https://server/topic': ('ntfy: ein Thema (6 bis 64 Buchstaben, Ziffern, - _) oder https://server/thema', 'ntfy : un sujet (6 à 64 lettres, chiffres, - _) ou https://serveur/sujet', 'ntfy: un argomento (da 6 a 64 lettere, cifre, - _) o https://server/argomento', 'ntfy: in tema (6 fin 64 bustabs, cifras, - _) u https://server/tema'),
}
for _k, _v in _HX_USERS.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the German of the web card (547): one place for the texts (fr / it / rm come through /i18n/<lang>.js)
WEB_PAGE = WEB_PAGE.replace("/*USRDE*/{}", json.dumps({_k: DE.get(_k, _v[0]) for _k, _v in _HX_USERS.items()}, ensure_ascii=False), 1)
SELFTEST_EXTRA.append(("Users: rights, time window, push filter", users_selftest))


# ---- the manual: «Benutzer und Handys» (before «Tipps», like 621) ------------------------------------------------------------
_HELP_USERS = {
    "de": '<section id="users" data-icon="👥"><h2>Benutzer und Handys</h2>'
          '<p>Für Personen, die immer wieder kommen (Familie, Kinder, Freunde), gibt es eigene Zugänge: <b>Einstellungen → Sicherheit → Benutzer</b>. '
          'Das Web-Passwort bleibt der Administrator – nur er sieht Einstellungen, Benutzer und Schlüssel. Für einen kurzen Besuch reicht weiterhin der Gastlink.</p>'
          '<ul><li><b>🧒 Kind:</b> Livebild und Spiele / Spielecke – keine Aufnahmen, kein Schutz-Schalter, keine Einstellungen. Bekommt keine Alarme, nur Spiel-Einladungen.</li>'
          '<li><b>🤝 Freund:</b> Livebild, Spiele, Gegensprechen, Licht – keine Aufnahmen, keine Einstellungen.</li>'
          '<li><b>🏠 Familie:</b> wie früher «Bedienen»: Schutz an / aus, Licht, Sirene, Aufnahmen ansehen, Kopf steuern, Gegensprechen, Spiele – keine Einstellungen.</li>'
          '<li><b>👁 Nur ansehen:</b> Livebild und Aufnahmen.</li>'
          '<li><b>⚙ Eigene Rechte:</b> selbst ankreuzen – Livebild, Aufnahmen, Schutz an / aus, Licht, Sirene, Spiele, Gegensprechen, Kopf steuern, Einstellungen '
          '(Passwort, Benutzer, Schlüssel und Zugangs-Einstellungen bleiben auch dann beim Administrator).</li></ul>'
          '<p>MoveEye prüft jedes Recht selbst (ein nicht erlaubter Befehl wird abgelehnt), und die Seite zeigt nur, was die Person darf.</p>'
          '<p><b>📱 Handy verknüpfen:</b> beim Benutzer antippen – ein QR-Code erscheint. Mit der Kamera des Handys scannen: das Handy ist als diese Person angemeldet, '
          'ohne Passwort. Der Code gilt 10 Minuten und nur einmal. Ist «Anmelden nur verschlüsselt» an, führt er auf die sichere Seite (https; einmal die Zertifikats-Warnung bestätigen). '
          'Wird der Link trotzdem unverschlüsselt (http) von einem anderen Gerät geöffnet, sperrt MoveEye ihn sofort – dann einen neuen Code zeigen. '
          'Ein Benutzer ohne Passwort meldet sich nur über verknüpfte Handys an.</p>'
          '<p><b>Geräte:</b> unter jedem Benutzer stehen seine Geräte (Handy und Browser, zuletzt gesehen). «✕» meldet das Gerät sofort ab – auch ein laufendes Livebild endet.</p>'
          '<p><b>⏰ Zugangszeit:</b> z. B. «Kind täglich 08:00–20:00» oder «Freund gültig bis 15.8.». Ausserhalb sieht die Person nur «Zugang gerade nicht aktiv» – keine Bilder, keine Daten, keine Nachrichten.</p>'
          '<p><b>Nachrichten pro Person:</b> Alarme, Infos und Spiel-Einladungen einzeln wählbar. Die Person schaltet die Browser-Nachrichten im eigenen Browser ein '
          '(Einstellungen → Benachrichtigungen) – MoveEye merkt sich, wem der Browser gehört. Oder ein eigenes ntfy-Thema eintragen. '
          'Der Haupt-Kanal (ntfy) bleibt beim Administrator. Beim «Spiele freigeben» bekommen Personen mit Spiel-Einladungen eine Nachricht.</p></section>\n\n',
    "en": '<section id="users" data-icon="👥"><h2>Users and phones</h2>'
          '<p>People who come again and again (family, children, friends) get their own access: <b>Settings → Security → Users</b>. '
          'The web password stays the administrator – only they see settings, users and keys. For a short visit the guest link is still enough.</p>'
          '<ul><li><b>🧒 Child:</b> live picture and games / game corner – no recordings, no protection switch, no settings. Gets no alarms, only game invitations.</li>'
          '<li><b>🤝 Friend:</b> live picture, games, intercom, light – no recordings, no settings.</li>'
          '<li><b>🏠 Family:</b> like the former «Operate»: protection on / off, light, siren, view recordings, steer the head, intercom, games – no settings.</li>'
          '<li><b>👁 View only:</b> live picture and recordings.</li>'
          '<li><b>⚙ Own rights:</b> tick them yourself – live picture, recordings, protection on / off, light, siren, games, intercom, steer the head, settings '
          '(password, users, keys and access settings stay with the administrator even then).</li></ul>'
          '<p>MoveEye checks every right itself (a command that is not allowed is refused), and the page shows only what the person may do.</p>'
          '<p><b>📱 Link a phone:</b> tap it at the user – a QR code appears. Scan it with the phone camera: the phone is logged in as this person, '
          'without a password. The code is valid 10 minutes and only once. With «Log in only encrypted» on it leads to the secure page (https; accept the certificate warning once). '
          'If the link is opened unencrypted (http) from another device anyway, MoveEye blocks it at once – then show a new code. '
          'A user without a password logs in only through linked phones.</p>'
          '<p><b>Devices:</b> each user lists their devices (phone and browser, last seen). «✕» logs the device out at once – a running live picture ends too.</p>'
          '<p><b>⏰ Access time:</b> e.g. «Child daily 08:00–20:00» or «Friend valid until 15 Aug». Outside the person only sees «Access not active right now» – no pictures, no data, no messages.</p>'
          '<p><b>Messages per person:</b> alarms, infos and game invitations each on / off. The person switches browser messages on in their own browser '
          '(Settings → Notifications) – MoveEye remembers whose browser it is. Or enter an own ntfy topic. '
          'The main channel (ntfy) stays with the administrator. «Open games» sends a message to people with game invitations.</p></section>\n\n',
    "fr": '<section id="users" data-icon="👥"><h2>Utilisateurs et téléphones</h2>'
          '<p>Les personnes qui reviennent (famille, enfants, amis) reçoivent leur propre accès : <b>Réglages → Sécurité → Utilisateurs</b>. '
          'Le mot de passe web reste l’administrateur. Pour une courte visite, le lien invité suffit.</p>'
          '<ul><li><b>🧒 Enfant :</b> image en direct et jeux – pas d’enregistrements, pas de protection, pas de réglages ; pas d’alarmes, seulement des invitations aux jeux.</li>'
          '<li><b>🤝 Ami :</b> image en direct, jeux, interphone, lumière.</li>'
          '<li><b>🏠 Famille :</b> protection on / off, lumière, sirène, enregistrements, tête, interphone, jeux – pas de réglages.</li>'
          '<li><b>👁 Voir seulement :</b> image en direct et enregistrements.</li>'
          '<li><b>⚙ Droits propres :</b> à cocher soi-même (mot de passe, utilisateurs et clés restent à l’administrateur).</li></ul>'
          '<p><b>📱 Lier un téléphone :</b> un code QR valable 10 minutes et une seule fois ; le téléphone est ensuite connecté sans mot de passe. '
          'Ouvert sans chiffrement (http) depuis un autre appareil, le lien est bloqué. «✕» à côté d’un appareil le déconnecte tout de suite.</p>'
          '<p><b>⏰ Horaires d’accès</b> et <b>date d’expiration</b> : en dehors, seulement «Accès pas actif en ce moment». '
          '<b>Messages par personne :</b> alarmes, infos, invitations aux jeux ; push du navigateur ou propre sujet ntfy.</p></section>\n\n',
    "it": '<section id="users" data-icon="👥"><h2>Utenti e telefoni</h2>'
          '<p>Le persone che tornano (famiglia, bambini, amici) ricevono un accesso proprio: <b>Impostazioni → Sicurezza → Utenti</b>. '
          'La password web resta l’amministratore. Per una visita breve basta il link ospite.</p>'
          '<ul><li><b>🧒 Bambino:</b> immagine live e giochi – niente registrazioni, protezione o impostazioni; niente allarmi, solo inviti ai giochi.</li>'
          '<li><b>🤝 Amico:</b> immagine live, giochi, citofono, luce.</li>'
          '<li><b>🏠 Famiglia:</b> protezione on / off, luce, sirena, registrazioni, testa, citofono, giochi – niente impostazioni.</li>'
          '<li><b>👁 Solo guardare:</b> immagine live e registrazioni.</li>'
          '<li><b>⚙ Diritti propri:</b> da spuntare (password, utenti e chiavi restano all’amministratore).</li></ul>'
          '<p><b>📱 Collegare un telefono:</b> un codice QR valido 10 minuti e una sola volta; il telefono è poi connesso senza password. '
          'Aperto senza cifratura (http) da un altro dispositivo, il link viene bloccato. «✕» accanto a un dispositivo lo disconnette subito.</p>'
          '<p><b>⏰ Orari di accesso</b> e <b>data di scadenza</b>: fuori solo «Accesso non attivo al momento». '
          '<b>Messaggi per persona:</b> allarmi, info, inviti ai giochi; push del browser o argomento ntfy proprio.</p></section>\n\n',
    "rm": '<section id="users" data-icon="👥"><h2>Utilisaders e telefonins</h2>'
          '<p>Persunas che vegnan adina puspè (famiglia, uffants, amis) survegnan in agen access: <b>Parameters → Segirezza → Utilisaders</b>. '
          'Il pled-clav web resta l’administratur. Per ina curta visita basta la colliaziun da giast.</p>'
          '<ul><li><b>🧒 Uffant:</b> maletg live e gieus – naginas registraziuns, nagina protecziun, nagins parameters; nagins alarms, mo invitaziuns da gieu.</li>'
          '<li><b>🤝 Ami:</b> maletg live, gieus, intercom, glisch.</li>'
          '<li><b>🏠 Famiglia:</b> protecziun en / ora, glisch, sirena, registraziuns, chau, intercom, gieus – nagins parameters.</li>'
          '<li><b>👁 Mo guardar:</b> maletg live e registraziuns.</li>'
          '<li><b>⚙ Agens dretgs:</b> sez marcar (pled-clav, utilisaders e clavs restan tar l’administratur).</li></ul>'
          '<p><b>📱 Colliar in telefonin:</b> in code QR valaivel 10 minutas e mo ina giada; il telefonin è lura annunzià senza pled-clav. '
          'Avert senza codaziun (http) dad in auter apparat, vegn la colliaziun bloccada. «✕» sper in apparat al deconnectescha immediatamain.</p>'
          '<p><b>⏰ Temp d’access</b> e <b>data da scadenza</b>: ordaifer mo «Access gist betg activ». '
          '<b>Messadis per persuna:</b> alarms, infos, invitaziuns da gieu; push dal navigatur u agen tema ntfy.</p></section>\n\n',
}


def _help_users(doc, lang):
    if '<section id="users"' in doc:
        return doc
    i = doc.find('<section id="appkeys"')
    if i < 0:
        i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_USERS[lang] + doc[i:] if i >= 0 else doc


_hp_en_us = HELP_PAGE.find('<div lang="en">')
if _hp_en_us > 0:
    HELP_PAGE = _help_users(HELP_PAGE[:_hp_en_us], "de") + _help_users(HELP_PAGE[_hp_en_us:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_users(HELP_X[_L], _L)
