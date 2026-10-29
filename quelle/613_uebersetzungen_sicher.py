#@ MoveEye – Teil 613: Übersetzungen zu Teil 578 («Sicher»: Aus nur mit PIN, Push nach Stromausfall, Fehlerseiten, Rotlicht-Ansicht, Bildschirmleser, Aufnahmen nach Tagen löschen, Push ohne Bild) und die Anleitung dazu. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_SICHER = {
    # settings
    'Delete recordings after … days (0 = never)': ('Aufnahmen nach … Tagen löschen (0 = nie)', 'Supprimer les enregistrements après … jours (0 = jamais)', 'Eliminare le registrazioni dopo … giorni (0 = mai)', 'Stizzar las registraziuns suenter … dis (0 = mai)'),
    'Pictures in push messages': ('Bilder in Push-Nachrichten', 'Images dans les notifications push', 'Immagini nelle notifiche push', 'Maletgs en ils avis push'),
    'send along': ('mitschicken', 'les envoyer', 'inviarle', 'trametter cun'),
    'text only (picture only in MoveEye)': ('nur Text (Bild nur in MoveEye)', 'texte seulement (image seulement dans MoveEye)', 'solo testo (immagine solo in MoveEye)', 'mo text (maletg mo en MoveEye)'),
    # 1: «Off» with the PIN
    'Please set a protection PIN first': ('Bitte zuerst eine Schutz-PIN setzen', 'Définis d’abord un PIN de protection', 'Imposta prima un PIN di protezione', 'Fixescha l’emprim in PIN da protecziun'),
    'MoveEye → Protection → PIN. Until then «Off» works only on the page of MoveEye.': ('MoveEye → Schutz → PIN. Bis dahin geht «Aus» nur auf der Seite von MoveEye.', 'MoveEye → Protection → PIN. D’ici là, «Arrêt» ne fonctionne que sur la page de MoveEye.', 'MoveEye → Protezione → PIN. Fino ad allora «Spento» funziona solo sulla pagina di MoveEye.', 'MoveEye → Protecziun → PIN. Fin lura funcziuna «Ora» mo sin la pagina da MoveEye.'),
    'Protection PIN': ('Schutz-PIN', 'PIN de protection', 'PIN di protezione', 'PIN da protecziun'),
    'Switch the protection off': ('Schutz ausschalten', 'Désactiver la protection', 'Disattivare la protezione', 'Stizzar la protecziun'),
    'Switch the protection off?': ('Schutz ausschalten?', 'Désactiver la protection ?', 'Disattivare la protezione?', 'Stizzar la protecziun?'),
    'Off needs the protection PIN - open the message and tap «Off» there.': ('«Aus» braucht die Schutz-PIN – Nachricht öffnen und dort «Aus» antippen.', '«Arrêt» demande le PIN de protection – ouvre la notification et touche «Arrêt».', '«Spento» richiede il PIN di protezione – apri la notifica e tocca «Spento».', '«Ora» basegna il PIN da protecziun – avrir l’avis e smatgar là «Ora».'),
    'too many wrong passwords - try again in 10 minutes': ('zu viele falsche Passwörter – in 10 Minuten nochmals', 'trop de mots de passe erronés – réessaie dans 10 minutes', 'troppe password errate – riprova tra 10 minuti', 'memia bleras pleds-clav sbagliads – empruvar danovamain en 10 minutas'),
    'wrong password': ('falsches Passwort', 'mot de passe erroné', 'password errata', 'pled-clav sbaglià'),
    # 2: after a power cut
    'MoveEye was off for {dur} (power cut / crash) – now {state} again': ('MoveEye war {dur} aus (Strom/Absturz) – jetzt wieder {state}', 'MoveEye était éteint pendant {dur} (courant / plantage) – maintenant de nouveau {state}', 'MoveEye è stato spento per {dur} (corrente / arresto) – ora di nuovo {state}', 'MoveEye era {dur} stizzà (current / collaps) – ussa puspè {state}'),
    'MoveEye was off (power cut / crash) – now {state} again': ('MoveEye war aus (Strom/Absturz) – jetzt wieder {state}', 'MoveEye était éteint (courant / plantage) – maintenant de nouveau {state}', 'MoveEye era spento (corrente / arresto) – ora di nuovo {state}', 'MoveEye era stizzà (current / collaps) – ussa puspè {state}'),
    'Back on': ('Wieder da', 'De retour', 'Di nuovo attivo', 'Puspè cò'),
    'less than a minute': ('weniger als eine Minute', 'moins d’une minute', 'meno di un minuto', 'main ch’ina minuta'),
    '{m} min.': ('{m} Min.', '{m} min', '{m} min', '{m} min.'),
    '{h} h {m} min.': ('{h} Std. {m} Min.', '{h} h {m} min', '{h} h {m} min', '{h} uras {m} min.'),
    # 3: error pages
    'Login required': ('Anmeldung nötig', 'Connexion nécessaire', 'Accesso richiesto', 'Annunzia necessaria'),
    'This MoveEye is protected with a password. Reload the page and enter the password (any user name).': ('Dieses MoveEye ist mit einem Passwort geschützt. Seite neu laden und das Passwort eingeben (Benutzername beliebig).', 'Ce MoveEye est protégé par un mot de passe. Recharge la page et saisis le mot de passe (nom d’utilisateur au choix).', 'Questo MoveEye è protetto da una password. Ricarica la pagina e inserisci la password (nome utente a piacere).', 'Quest MoveEye è protegì cun in pled-clav. Chargiar danovamain la pagina ed endatar il pled-clav (num d’utilisader a piacer).'),
    'Too many wrong passwords': ('Zu viele falsche Passwörter', 'Trop de mots de passe erronés', 'Troppe password errate', 'Memia bleras pleds-clav sbagliads'),
    'For safety the login is blocked for a few minutes. Please wait 5 minutes and try again.': ('Zur Sicherheit ist die Anmeldung ein paar Minuten gesperrt. Bitte 5 Minuten warten und nochmals versuchen.', 'Par sécurité, la connexion est bloquée quelques minutes. Attends 5 minutes et réessaie.', 'Per sicurezza l’accesso è bloccato per qualche minuto. Attendi 5 minuti e riprova.', 'Per segirezza è l’annunzia bloccada in pèr minutas. Spetgar 5 minutas ed empruvar danovamain.'),
    'Request blocked': ('Anfrage gesperrt', 'Requête bloquée', 'Richiesta bloccata', 'Dumonda bloccada'),
    'This action came from another web page and was refused for your safety. Open MoveEye directly and try again.': ('Diese Aktion kam von einer anderen Webseite und wurde zu deiner Sicherheit abgelehnt. MoveEye direkt öffnen und nochmals versuchen.', 'Cette action venait d’une autre page web et a été refusée pour ta sécurité. Ouvre MoveEye directement et réessaie.', 'Questa azione proveniva da un’altra pagina web ed è stata rifiutata per la tua sicurezza. Apri MoveEye direttamente e riprova.', 'Questa acziun è vegnida d’in’autra pagina d’internet ed è vegnida refusada per tia segirezza. Avrir MoveEye directamain ed empruvar danovamain.'),
    'Guest link not valid': ('Gast-Link nicht gültig', 'Lien d’invité non valable', 'Link ospite non valido', 'Link da giast betg valaivel'),
    'This guest link is not valid (any more). Ask the owner for a new link.': ('Dieser Gast-Link ist nicht (mehr) gültig. Bitte beim Besitzer einen neuen Link verlangen.', 'Ce lien d’invité n’est (plus) valable. Demande un nouveau lien au propriétaire.', 'Questo link ospite non è (più) valido. Chiedi un nuovo link al proprietario.', 'Quest link da giast n’è betg (pli) valaivel. Dumandar il possessur per in nov link.'),
    'Too many wrong keys': ('Zu viele falsche Schlüssel', 'Trop de clés erronées', 'Troppe chiavi errate', 'Memia bleras clavs sbagliadas'),
    'Too many wrong keys from this device. Please wait 10 minutes.': ('Zu viele falsche Schlüssel von diesem Gerät. Bitte 10 Minuten warten.', 'Trop de clés erronées depuis cet appareil. Attends 10 minutes.', 'Troppe chiavi errate da questo apparecchio. Attendi 10 minuti.', 'Memia bleras clavs sbagliadas da quest apparat. Spetgar 10 minutas.'),
    'Page not found': ('Seite nicht gefunden', 'Page introuvable', 'Pagina non trovata', 'Pagina betg chattada'),
    'This address does not exist on MoveEye.': ('Diese Adresse gibt es bei MoveEye nicht.', 'Cette adresse n’existe pas sur MoveEye.', 'Questo indirizzo non esiste su MoveEye.', 'Questa adressa n’exista betg tar MoveEye.'),
    'Something went wrong': ('Etwas ist schiefgegangen', 'Quelque chose n’a pas marché', 'Qualcosa è andato storto', 'Insatge n’è betg ì bain'),
    'MoveEye could not answer this request. Please try again in a moment.': ('MoveEye konnte diese Anfrage nicht beantworten. Bitte gleich nochmals versuchen.', 'MoveEye n’a pas pu répondre à cette requête. Réessaie dans un instant.', 'MoveEye non ha potuto rispondere a questa richiesta. Riprova tra un momento.', 'MoveEye n’ha betg pudì respunder a questa dumonda. Empruvar danovamain en in mument.'),
    'To the start page': ('Zur Startseite', 'Vers la page d’accueil', 'Alla pagina iniziale', 'A la pagina da partenza'),
    # 4: dark view (until 2.98.22 «night view»)
    # 5: names for screen readers
    'Full screen': ('Vollbild', 'Plein écran', 'Schermo intero', 'Visur entir'),
    'Light / dark': ('Hell / dunkel', 'Clair / sombre', 'Chiaro / scuro', 'Cler / stgir'),
    'Exit full screen': ('Vollbild verlassen', 'Quitter le plein écran', 'Esci dallo schermo intero', 'Bandunar il visur entir'),
    'Up': ('Nach oben', 'Vers le haut', 'Su', 'Ensi'),
    'Down': ('Nach unten', 'Vers le bas', 'Giù', 'Engiu'),
    'Remove': ('Entfernen', 'Supprimer', 'Rimuovi', 'Allontanar'),
    'Refresh': ('Aktualisieren', 'Actualiser', 'Aggiorna', 'Actualisar'),
    'Help': ('Hilfe', 'Aide', 'Aiuto', 'Agid'),
    'Menu': ('Menü', 'Menu', 'Menu', 'Menu'),
    'Pause': ('Pause', 'Pause', 'Pausa', 'Pausa'),
    'Previous': ('Vorherige', 'Précédent', 'Precedente', 'Precedent'),
    'Live picture': ('Livebild', 'Image en direct', 'Immagine live', 'Maletg live'),
    'Main navigation': ('Hauptnavigation', 'Navigation principale', 'Navigazione principale', 'Navigaziun principala'),
    'Sub navigation': ('Unternavigation', 'Sous-navigation', 'Sottonavigazione', 'Sutnavigaziun'),
    'Search': ('Suchen', 'Rechercher', 'Cerca', 'Tschertgar'),
    'Listen': ('Zuhören', 'Écouter', 'Ascolta', 'Tadlar'),
    'Other side': ('Andere Seite', 'Autre côté', 'Altro lato', 'Autra vart'),
    'Favourite': ('Favorit', 'Favori', 'Preferito', 'Favurit'),
    'Download': ('Herunterladen', 'Télécharger', 'Scarica', 'Telechargiar'),
    'Share': ('Teilen', 'Partager', 'Condividi', 'Parter'),
    'Zoom in': ('Vergrössern', 'Agrandir', 'Ingrandisci', 'Engrondir'),
    'Zoom out': ('Verkleinern', 'Réduire', 'Riduci', 'Empitschnir'),
    'Mute': ('Ton aus', 'Couper le son', 'Silenzia', 'Tun ora'),
    'Sound on': ('Ton an', 'Son activé', 'Audio attivo', 'Tun en'),
    'Protection state': ('Schutz-Zustand', 'État de la protection', 'Stato della protezione', 'Stadi da la protecziun'),
    'Operate with the finger (otherwise the page scrolls)': ('Bedienen mit dem Finger (sonst scrollt die Seite)', 'Utiliser avec le doigt (sinon la page défile)', 'Usare con il dito (altrimenti la pagina scorre)', 'Manar cun il det (uschiglio sa mova la pagina)'),
    'Finger: rotate instead of move': ('Finger: drehen statt verschieben', 'Doigt : tourner au lieu de déplacer', 'Dito: ruotare invece di spostare', 'Det: volver empè da spustar'),
    'Large picture': ('Grosses Bild', 'Grande image', 'Immagine grande', 'Maletg grond'),
    # 6: recordings
    'Holiday over: delete all recordings': ('Ferien vorbei: alle Aufnahmen löschen', 'Vacances finies : supprimer tous les enregistrements', 'Vacanze finite: eliminare tutte le registrazioni', 'Vacanzas finidas: stizzar tut las registraziuns'),
    'Also delete the favourites ⭐': ('Auch die Favoriten ⭐ löschen', 'Supprimer aussi les favoris ⭐', 'Eliminare anche i preferiti ⭐', 'Stizzar er ils favurits ⭐'),
    'Delete ALL recordings now? This cannot be undone.': ('Jetzt ALLE Aufnahmen löschen? Das lässt sich nicht rückgängig machen.', 'Supprimer TOUS les enregistrements maintenant ? Impossible d’annuler.', 'Eliminare TUTTE le registrazioni ora? Non si può annullare.', 'Stizzar ussa TUT las registraziuns? Quai na sa lascha betg revocar.'),
    'Favourites ⭐ are kept.': ('Favoriten ⭐ bleiben.', 'Les favoris ⭐ sont conservés.', 'I preferiti ⭐ restano.', 'Ils favurits ⭐ restan.'),
    'favourites': ('Favoriten', 'favoris', 'preferiti', 'favurits'),
    'Deleting …': ('Löschen …', 'Suppression …', 'Eliminazione …', 'Stizzar …'),
    '{n} recordings deleted, {k} kept': ('{n} Aufnahmen gelöscht, {k} behalten', '{n} enregistrements supprimés, {k} conservés', '{n} registrazioni eliminate, {k} conservate', '{n} registraziuns stizzadas, {k} tegnidas'),
    'please confirm': ('bitte bestätigen', 'merci de confirmer', 'conferma per favore', 'per plaschair confermar'),
}
for _k, _v in _HX_SICHER.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- the manual: one short section in every language (before «Tipps») ----------------------------------------------------
_HELP_SICHER = {
    "de": '<section id="sicher" data-icon="🔐"><h2>Sicher unterwegs</h2><ul>'
          '<li><b>«Aus» in der Push-Nachricht</b> öffnet eine kleine Seite mit dem PIN-Feld: ausgeschaltet wird erst mit der Schutz-PIN '
          '(ohne PIN mit dem Web-Passwort). Ist beides nicht gesetzt, geht «Aus» nur auf der Seite von MoveEye. Falsche PINs sperren wie im Web '
          '(ab 3 kommt ein Diebstahl-Alarm). «Fehlalarm» und «Sirene» gehen weiterhin mit einem Tipp.</li>'
          '<li><b>Nach einem Stromausfall oder Absturz</b> kommt eine Push-Nachricht, wie lange MoveEye aus war und ob der Schutz wieder läuft. '
          'Nach einem Update oder Neustart nicht.</li>'
          '<li><b>◉ Rotlicht-Ansicht</b> (die 3. Stufe des Knopfs «Hell / dunkel» oben: Hell → Dunkel → Rotlicht): die ganze Seite sehr dunkel und rot, das Livebild gedimmt – für einen kurzen Blick '
          'im Zelt, ohne die Augen zu blenden. Jeder Browser merkt es sich selbst. Im Fenster derselbe Knopf ◐.</li>'
          '<li><b>Aufnahmen nach … Tagen löschen</b> (Einstellungen → Aufnahme, 0 = nie) – zusätzlich zur Grössen-Grenze. '
          '«🧹 Ferien vorbei: alle Aufnahmen löschen» fragt nach; ⭐ Favoriten bleiben, ausser man hakt sie an.</li>'
          '<li><b>Bilder in Push-Nachrichten</b> (Benachrichtigungen): «nur Text» schickt kein Bild an ntfy, Telegram oder Pushover – das Bild bleibt in MoveEye.</li>'
          '</ul></section>\n\n',
    "en": '<section id="sicher" data-icon="🔐"><h2>Safe on the road</h2><ul>'
          '<li><b>«Off» in the push message</b> opens a small page with a PIN field: the protection goes off only with the protection PIN '
          '(without a PIN: the web password). With neither, «Off» works only on the page of MoveEye. Wrong PINs lock as on the web page '
          '(from 3 on a theft alarm). «False alarm» and «Siren» still work with one tap.</li>'
          '<li><b>After a power cut or a crash</b> a push message says how long MoveEye was off and whether the protection runs again. Not after an update or restart.</li>'
          '<li><b>◉ Red light view</b> (the 3rd step of the button «light / dark» at the top: light → dark → red light): the whole page very dark and red, the live picture dimmed – for a short look in the tent '
          'without dazzling your eyes. Every browser remembers it itself. In the window the same button ◐.</li>'
          '<li><b>Delete recordings after … days</b> (Settings → Recording, 0 = never) – in addition to the size limit. '
          '«🧹 Holiday over: delete all recordings» asks first; ⭐ favourites stay unless you tick them.</li>'
          '<li><b>Pictures in push messages</b> (Notifications): «text only» sends no picture to ntfy, Telegram or Pushover – the picture stays in MoveEye.</li>'
          '</ul></section>\n\n',
    "fr": '<section id="sicher" data-icon="🔐"><h2>En sécurité en route</h2><ul>'
          '<li><b>«Arrêt» dans la notification</b> ouvre une petite page avec un champ PIN : la protection ne s’arrête qu’avec le PIN de protection '
          '(sans PIN : le mot de passe web). Sans les deux, «Arrêt» ne marche que sur la page de MoveEye. Les PIN erronés bloquent comme sur la page web '
          '(dès 3, alarme vol). «Fausse alarme» et «Sirène» marchent toujours d’un toucher.</li>'
          '<li><b>Après une coupure de courant ou un plantage</b>, une notification dit combien de temps MoveEye était éteint et si la protection tourne à nouveau. Pas après une mise à jour ou un redémarrage.</li>'
          '<li><b>◉ Vue lumière rouge</b> (3e étape du bouton «clair / sombre» en haut : clair → sombre → lumière rouge) : toute la page très sombre et rouge, l’image en direct atténuée – pour un bref coup d’œil dans la tente. '
          'Chaque navigateur s’en souvient. Dans la fenêtre le même bouton ◐.</li>'
          '<li><b>Supprimer les enregistrements après … jours</b> (Réglages → Enregistrement, 0 = jamais) – en plus de la limite de taille. '
          '«🧹 Vacances finies : supprimer tous les enregistrements» demande confirmation ; les favoris ⭐ restent, sauf si tu les coches.</li>'
          '<li><b>Images dans les notifications push</b> : «texte seulement» n’envoie aucune image à ntfy, Telegram ou Pushover – l’image reste dans MoveEye.</li>'
          '</ul></section>\n\n',
    "it": '<section id="sicher" data-icon="🔐"><h2>Sicuri in viaggio</h2><ul>'
          '<li><b>«Spento» nella notifica</b> apre una piccola pagina con il campo PIN: la protezione si spegne solo con il PIN di protezione '
          '(senza PIN: la password web). Senza entrambi, «Spento» funziona solo sulla pagina di MoveEye. I PIN errati bloccano come sulla pagina web '
          '(da 3 allarme furto). «Falso allarme» e «Sirena» funzionano sempre con un tocco.</li>'
          '<li><b>Dopo un’interruzione di corrente o un arresto</b> una notifica dice per quanto tempo MoveEye è stato spento e se la protezione è di nuovo attiva. Non dopo un aggiornamento o un riavvio.</li>'
          '<li><b>◉ Vista luce rossa</b> (3° passo del pulsante «chiaro / scuro» in alto: chiaro → scuro → luce rossa): tutta la pagina molto scura e rossa, l’immagine live attenuata – per un breve sguardo nella tenda. '
          'Ogni browser se lo ricorda. Nella finestra lo stesso pulsante ◐.</li>'
          '<li><b>Eliminare le registrazioni dopo … giorni</b> (Impostazioni → Registrazione, 0 = mai) – oltre al limite di dimensione. '
          '«🧹 Vacanze finite: eliminare tutte le registrazioni» chiede conferma; i preferiti ⭐ restano, a meno di spuntarli.</li>'
          '<li><b>Immagini nelle notifiche push</b>: «solo testo» non invia immagini a ntfy, Telegram o Pushover – l’immagine resta in MoveEye.</li>'
          '</ul></section>\n\n',
    "rm": '<section id="sicher" data-icon="🔐"><h2>Segir sin viadi</h2><ul>'
          '<li><b>«Ora» en l’avis push</b> avra ina pitschna pagina cun il champ PIN: la protecziun vegn stizzada mo cun il PIN da protecziun '
          '(senza PIN: il pled-clav web). Senza omadus funcziuna «Ora» mo sin la pagina da MoveEye. PINs sbagliads bloccan sco en il web '
          '(a partir da 3 in alarm da ladranaria). «Fauss alarm» e «Sirena» funcziunan vinavant cun in tip.</li>'
          '<li><b>Suenter ina interrupziun da current u in collaps</b> di in avis push quant ditg che MoveEye era stizzà e sche la protecziun funcziuna puspè. Betg suenter in update u in restart.</li>'
          '<li><b>◉ Vista glisch cotschna</b> (3. stgalim dal buttun «cler / stgir» sisura: cler → stgir → glisch cotschna): tut la pagina fitg stgira e cotschna, il maletg live stgirentà – per in curt sguard en la tenda. '
          'Mintga navigatur sa regorda sez. En la fanestra il medem buttun ◐.</li>'
          '<li><b>Stizzar las registraziuns suenter … dis</b> (Parameters → Registraziun, 0 = mai) – ultra dal limit da grondezza. '
          '«🧹 Vacanzas finidas: stizzar tut las registraziuns» dumonda l’emprim; ils favurits ⭐ restan, auter che sch’ins als marca.</li>'
          '<li><b>Maletgs en ils avis push</b>: «mo text» na trametta nagin maletg a ntfy, Telegram u Pushover – il maletg resta en MoveEye.</li>'
          '</ul></section>\n\n',
}


def _help_sicher(doc, lang):
    if '<section id="sicher"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    if i < 0:
        i = doc.find('<section id="privacy"')
    return doc[:i] + _HELP_SICHER[lang] + doc[i:] if i >= 0 else doc


_hp_en = HELP_PAGE.find('<div lang="en">')
if _hp_en > 0:
    HELP_PAGE = _help_sicher(HELP_PAGE[:_hp_en], "de") + _help_sicher(HELP_PAGE[_hp_en:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_sicher(HELP_X[_L], _L)
