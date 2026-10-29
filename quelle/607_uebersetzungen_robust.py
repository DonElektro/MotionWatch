#@ MoveEye – Teil 607: Übersetzungen und Anleitung für Speicherkarte schonen, Selbstheilung, eine Simulator-Sperre (2.98.13). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_ROBUST = {
    # ---- 066 memory card
    'Memory card health': ('Speicherkarte: Zustand', 'Carte mémoire : état', 'Scheda di memoria: stato', 'Carta da memoria: stadi'),
    'not measurable on this computer': ('auf diesem Computer nicht messbar', 'non mesurable sur cet ordinateur', 'non misurabile su questo computer', 'betg mesurabel sin quest computer'),
    '≈ {n} written per day': ('≈ {n} pro Tag geschrieben', '≈ {n} écrits par jour', '≈ {n} scritti al giorno', '≈ {n} scrit per di'),
    'write volume: measuring (20 min)': ('Schreibmenge: wird gemessen (20 Min.)', 'volume écrit : mesure en cours (20 min)', 'quantità scritta: misurazione (20 min)', 'quantitad scritta: vegn mesirada (20 min)'),
    '{n} file system error(s)': ('{n} Dateisystem-Fehler', '{n} erreur(s) du système de fichiers', '{n} errore/i del file system', '{n} errur(s) dal sistem da datotecas'),
    'errors: not readable': ('Fehler: nicht lesbar', 'erreurs : illisibles', 'errori: non leggibili', 'errurs: betg legiblas'),
    'no file system errors': ('keine Dateisystem-Fehler', 'aucune erreur du système de fichiers', 'nessun errore del file system', 'naginas errurs dal sistem da datotecas'),
    'read-only after errors': ('nach Fehlern schreibgeschützt', 'en lecture seule après des erreurs', 'sola lettura dopo errori', 'protegì cunter scriver suenter errurs'),
    'read-only protection on': ('Schreibschutz an', 'protection en écriture active', 'protezione scrittura attiva', 'protecziun cunter scriver activa'),
    'worn {p} %': ('{p} % abgenutzt', 'usée à {p} %', 'usurata al {p} %', '{p} % consumada'),
    'The memory card reports errors: copy the recordings, check the card on a PC (or replace it) and use the read-only protection during the season.':
        ('Die Speicherkarte meldet Fehler: Aufnahmen sichern, die Karte am PC prüfen (oder ersetzen) und während der Saison den Schreibschutz nutzen.',
         'La carte mémoire signale des erreurs : sauvegarder les enregistrements, vérifier la carte sur un PC (ou la remplacer) et utiliser la protection en écriture pendant la saison.',
         'La scheda di memoria segnala errori: salvare le registrazioni, controllare la scheda su un PC (o sostituirla) e usare la protezione scrittura durante la stagione.',
         'La carta da memoria annunzia errurs: segirar las registraziuns, controllar la carta sin in PC (u la remplazzar) e duvrar la protecziun cunter scriver durant la stagiun.'),
    'The system switched the card to read-only (errors). Restart; if it happens again, replace the card.':
        ('Das System hat die Karte schreibgeschützt (Fehler). Neu starten; passiert es wieder, die Karte ersetzen.',
         'Le système a mis la carte en lecture seule (erreurs). Redémarrer ; si cela se reproduit, remplacer la carte.',
         'Il sistema ha messo la scheda in sola lettura (errori). Riavviare; se succede di nuovo, sostituire la scheda.',
         'Il sistem ha protegì la carta cunter scriver (errurs). Reaviar; sch’i capita danovamain, remplazzar la carta.'),
    'Read-only protection is on: recordings and changed settings stay only in the memory (RAM) and are gone after a restart. Put the recordings on a USB drive / SSD (Settings → Recording).':
        ('Der Schreibschutz ist an: Aufnahmen und geänderte Einstellungen bleiben nur im Arbeitsspeicher und sind nach einem Neustart weg. Aufnahmen auf einen USB-Stick / eine SSD legen (Einstellungen → Aufnahme).',
         'La protection en écriture est active : enregistrements et réglages modifiés restent seulement en mémoire vive et disparaissent au redémarrage. Mettre les enregistrements sur une clé USB / un SSD (Réglages → Enregistrement).',
         'La protezione scrittura è attiva: registrazioni e impostazioni modificate restano solo nella memoria RAM e spariscono al riavvio. Mettere le registrazioni su una chiavetta USB / un SSD (Impostazioni → Registrazione).',
         'La protecziun cunter scriver è activa: registraziuns e configuraziuns midadas restan mo en la memoria (RAM) e mancan suenter in reaviament. Metter las registraziuns sin in stick USB / ina SSD (Configuraziuns → Registraziun).'),
    'A lot is written to the card: put the recordings on a USB drive / SSD, switch off continuous recording, or use the read-only protection during the season.':
        ('Es wird viel auf die Karte geschrieben: Aufnahmen auf einen USB-Stick / eine SSD legen, Daueraufnahme ausschalten oder während der Saison den Schreibschutz nutzen.',
         'Beaucoup est écrit sur la carte : mettre les enregistrements sur une clé USB / un SSD, couper l’enregistrement continu ou utiliser la protection en écriture pendant la saison.',
         'Si scrive molto sulla scheda: mettere le registrazioni su una chiavetta USB / un SSD, spegnere la registrazione continua o usare la protezione scrittura durante la stagione.',
         'Igl vegn scrit bler sin la carta: metter las registraziuns sin in stick USB / ina SSD, deactivar la registraziun permanenta u duvrar la protecziun cunter scriver durant la stagiun.'),
    'The memory chip is quite worn: plan a replacement.': ('Der Speicherchip ist ziemlich abgenutzt: einen Ersatz einplanen.', 'La puce mémoire est assez usée : prévoir un remplacement.', 'Il chip di memoria è piuttosto usurato: prevedere una sostituzione.', 'Il chip da memoria è fitg consumà: planisar ina remplazzada.'),
    # ---- 145 self-healing
    'Self-healing': ('Selbstheilung', 'Auto-réparation', 'Autoriparazione', 'Autoguariziun'),
    'The camera loop hung': ('Die Kamera-Schleife hing', 'La boucle caméra était bloquée', 'Il ciclo della telecamera era bloccato', 'La cirquitaziun da la camera pendeva'),
    'No new pictures although the camera is connected': ('Keine neuen Bilder, obwohl die Kamera verbunden ist', 'Plus de nouvelles images bien que la caméra soit connectée', 'Nessuna nuova immagine anche se la telecamera è collegata', 'Nagins novs maletgs, schebain che la camera è colliada'),
    'The AI got stuck again and again': ('Die KI blieb immer wieder hängen', 'L’IA se bloquait encore et encore', 'L’IA si bloccava di continuo', 'L’IA è adina puspè restada pendida'),
    'The web page did not answer': ('Die Webseite antwortete nicht', 'La page web ne répondait pas', 'La pagina web non rispondeva', 'La pagina web na respundeva betg'),
    'The AI was stuck': ('Die KI hing', 'L’IA était bloquée', 'L’IA era bloccata', 'L’IA pendeva'),
    'loaded again': ('neu geladen', 'rechargée', 'ricaricata', 'chargià da nov'),
    'restarted': ('neu gestartet', 'redémarré', 'riavviato', 'reavià'),
    'no restart now (limit)': ('jetzt kein Neustart (Grenze erreicht)', 'pas de redémarrage maintenant (limite)', 'nessun riavvio ora (limite)', 'ussa nagin reaviament (limita)'),
    'MoveEye did not restart again (limit reached). Please look at it.': ('MoveEye hat nicht nochmals neu gestartet (Grenze erreicht). Bitte nachsehen.', 'MoveEye n’a pas redémarré une nouvelle fois (limite atteinte). Merci de vérifier.', 'MoveEye non si è riavviato di nuovo (limite raggiunto). Per favore controllare.', 'MoveEye n’è betg reavià anc ina giada (limita cuntanschida). Per plaschair controllar.'),
    'MoveEye restarted itself': ('MoveEye hat sich selbst neu gestartet', 'MoveEye a redémarré tout seul', 'MoveEye si è riavviato da solo', 'MoveEye è sa reavià sez'),
    'Everything runs again.': ('Alles läuft wieder.', 'Tout fonctionne à nouveau.', 'Tutto funziona di nuovo.', 'Tut funcziuna puspè.'),
    'The AI was stuck and was loaded again.': ('Die KI hing und wurde neu geladen.', 'L’IA était bloquée et a été rechargée.', 'L’IA era bloccata ed è stata ricaricata.', 'L’IA pendeva ed è vegnida chargiada da nov.'),
    'watching camera, AI and web page': ('überwacht Kamera, KI und Webseite', 'surveille caméra, IA et page web', 'sorveglia telecamera, IA e pagina web', 'survegliescha camera, IA e pagina web'),
    'If it happens again: send the diagnosis package (Settings → Help).': ('Passiert es wieder: das Diagnose-Paket senden (Einstellungen → Hilfe).', 'Si cela se reproduit : envoyer le paquet de diagnostic (Réglages → Aide).', 'Se succede di nuovo: inviare il pacchetto di diagnosi (Impostazioni → Aiuto).', 'Sch’i capita danovamain: trametter il pachet da diagnosa (Configuraziuns → Agid).'),
    # ---- 147 one lock with the simulator
    'test bench': ('Prüfstand', 'banc d’essai', 'banco di prova', 'banc da prova'),
    'training pictures': ('Trainingsbilder', 'images d’entraînement', 'immagini di addestramento', 'maletgs da trenament'),
    'playback of a recording': ('Wiedergabe einer Aufnahme', 'lecture d’un enregistrement', 'riproduzione di una registrazione', 'reproducziun d’ina registraziun'),
    'started in the simulator': ('im Simulator gestartet', 'lancé dans le simulateur', 'avviato nel simulatore', 'avià en il simulatur'),
    # ---- names of the settings (570 / web)
    'Simulator: fewer pictures (the simulator draws only what is fetched)': ('Simulator: weniger Bilder (der Simulator zeichnet nur, was abgeholt wird)', 'Simulateur : moins d’images (le simulateur ne dessine que ce qui est demandé)', 'Simulatore: meno immagini (il simulatore disegna solo ciò che viene richiesto)', 'Simulatur: pli paucs maletgs (il simulatur dissegna mo quai che vegn pretendì)'),
    'Simulator: fewer pictures': ('Simulator: weniger Bilder', 'Simulateur : moins d’images', 'Simulatore: meno immagini', 'Simulatur: pli paucs maletgs'),
    'Update the simulator by itself (the setting «Neue Versionen» of the simulator)': ('Simulator von selbst aktualisieren (die Einstellung «Neue Versionen» im Simulator)', 'Mettre à jour le simulateur tout seul (le réglage «Neue Versionen» du simulateur)', 'Aggiornare il simulatore da solo (l’impostazione «Neue Versionen» del simulatore)', 'Actualisar il simulatur sez (la configuraziun «Neue Versionen» dal simulatur)'),
    'upd-owner-note': ('Das ist die Einstellung «Neue Versionen» im Simulator – hier und dort dieselbe.', 'C’est le réglage «Neue Versionen» du simulateur – le même ici et là-bas.', 'È l’impostazione «Neue Versionen» del simulatore – la stessa qui e là.', 'Quai è la configuraziun «Neue Versionen» dal simulatur – la medema qua e là.'),
}
for _k, _v in _HX_ROBUST.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- the manual: «Memory card» and «Self-healing» (before «Tips») ---------------------------------------------------------
_HELP_SD = {
 "de": '<section id="sdcard" data-icon="🪪"><h2>Speicherkarte schonen &amp; Selbstheilung</h2>'
       '<p>Auf dem Campingplatz geht der Strom oft ohne Vorwarnung weg, und eine Speicherkarte, die den ganzen Tag beschrieben wird, nutzt sich ab. '
       'Die <b>🩺 Selbstdiagnose</b> zeigt unter «Speicherkarte: Zustand», wie viel pro Tag auf die Karte geschrieben wird, ob Dateisystem-Fehler da sind und wie viel frei ist.</p>'
       '<h3>Weniger schreiben</h3><ul><li>Aufnahmen auf einen USB-Stick oder eine SSD legen (Einstellungen → Aufnahme) – das schont die Karte am meisten.</li>'
       '<li>Daueraufnahme und Zeitraffer nur einschalten, wenn sie gebraucht werden.</li>'
       '<li>MoveEye selbst schreibt sparsam: Einstellungen höchstens alle 15 Sekunden, das Lebenszeichen für den sicheren Start nach 15 Minuten nur noch einmal pro Minute, dieselbe Fehlermeldung (z. B. «Kamera nicht erreichbar») nur alle 10 Minuten ins Protokoll.</li></ul>'
       '<h3>Während der Saison: Karte schreibgeschützt (Overlay)</h3><ol><li>Zuerst alles fertig einrichten (WLAN, Push-Nachrichten, Zonen, Passwort) und eine Nacht testen.</li>'
       '<li>Aufnahmen auf einen USB-Stick / eine SSD legen – sonst sind sie nach einem Neustart weg.</li>'
       '<li>Am Pi im Terminal: <code>sudo raspi-config</code> → <i>Performance Options</i> → <i>Overlay File System</i> → <i>Yes</i> (Frage nach der Boot-Partition ebenfalls <i>Yes</i>) → neu starten. Das Menü installiert, was es braucht.</li>'
       '<li>Jetzt landet alles, was geschrieben wird, im Arbeitsspeicher: ein Stromausfall kann die Karte nicht mehr beschädigen. Geänderte Einstellungen, das Protokoll und Updates sind nach einem Neustart aber wieder weg.</li>'
       '<li>Für Änderungen oder ein Update: im selben Menü das Overlay ausschalten, neu starten, ändern, wieder einschalten.</li></ol>'
       '<div class="tip">💡 Die Selbstdiagnose zeigt «Schreibschutz an», solange das Overlay läuft. Meldet sie Fehler: Aufnahmen sichern, die Karte am PC prüfen oder ersetzen (Marken-Karte, am besten «High Endurance»).</div>'
       '<h3>Selbstheilung</h3><p>Hängt die Kamera-Schleife, die KI oder die Webseite mehrere Minuten lang, lädt MoveEye die KI neu bzw. startet sich selbst neu (wie bei einem Update: Aufnahme fertig, Einstellungen gespeichert), schreibt es ins Protokoll und schickt eine Info-Nachricht. '
       'Damit es nie dauernd neu startet: frühestens 5 Minuten nach dem Start, höchstens 2 Neustarts pro Stunde und 6 pro Tag – danach meldet es sich nur noch. Die Selbstdiagnose zeigt das letzte Eingreifen.</p></section>\n\n',
 "en": '<section id="sdcard" data-icon="🪪"><h2>Protecting the memory card &amp; self-healing</h2>'
       '<p>On camp sites the power often goes off without warning, and a memory card that is written all day wears out. '
       'The <b>🩺 self-check</b> shows under «Memory card health» how much is written to the card per day, whether there are file system errors and how much is free.</p>'
       '<h3>Write less</h3><ul><li>Put the recordings on a USB drive or an SSD (Settings → Recording) – that spares the card the most.</li>'
       '<li>Switch on continuous recording and time-lapse only when you need them.</li>'
       '<li>MoveEye itself writes sparingly: settings at most every 15 seconds, the sign of life for the safe start once a minute after the first 15 minutes, the same error (e.g. «camera not reachable») only every 10 minutes into the log.</li></ul>'
       '<h3>During the season: read-only card (overlay)</h3><ol><li>First finish the setup (Wi-Fi, push messages, zones, password) and test one night.</li>'
       '<li>Put the recordings on a USB drive / SSD – otherwise they are gone after a restart.</li>'
       '<li>On the Pi in a terminal: <code>sudo raspi-config</code> → <i>Performance Options</i> → <i>Overlay File System</i> → <i>Yes</i> (boot partition read-only: <i>Yes</i> too) → reboot. The menu installs what it needs.</li>'
       '<li>Now everything that is written goes to the memory (RAM): a power cut can no longer damage the card. Changed settings, the log and updates are gone after a restart, though.</li>'
       '<li>For changes or an update: switch the overlay off in the same menu, reboot, change, switch it on again.</li></ol>'
       '<div class="tip">💡 The self-check shows «read-only protection on» while the overlay runs. If it reports errors: save the recordings, check the card on a PC or replace it (a brand card, ideally «High Endurance»).</div>'
       '<h3>Self-healing</h3><p>If the camera loop, the AI or the web page hangs for several minutes, MoveEye loads the AI again or restarts itself (like an update: recording finished, settings saved), notes it in the log and sends one info message. '
       'So that it never restarts again and again: not before 5 minutes after the start, at most 2 restarts per hour and 6 per day – then it only reports. The self-check shows the last intervention.</p></section>\n\n',
 "fr": '<section id="sdcard" data-icon="🪪"><h2>Ménager la carte mémoire &amp; auto-réparation</h2>'
       '<p>Au camping, le courant se coupe souvent sans prévenir, et une carte mémoire écrite toute la journée s’use. L’<b>🩺 autodiagnostic</b> montre sous «Carte mémoire : état» combien est écrit par jour, s’il y a des erreurs du système de fichiers et la place libre.</p>'
       '<h3>Écrire moins</h3><ul><li>Mettre les enregistrements sur une clé USB ou un SSD (Réglages → Enregistrement).</li><li>Enregistrement continu et timelapse seulement si nécessaire.</li>'
       '<li>MoveEye écrit peu : réglages au plus toutes les 15 secondes, signe de vie une fois par minute après 15 minutes, une même erreur seulement toutes les 10 minutes dans le journal.</li></ul>'
       '<h3>Pendant la saison : carte en lecture seule (overlay)</h3><ol><li>Tout configurer d’abord et tester une nuit.</li><li>Enregistrements sur clé USB / SSD – sinon ils disparaissent au redémarrage.</li>'
       '<li>Sur le Pi : <code>sudo raspi-config</code> → <i>Performance Options</i> → <i>Overlay File System</i> → <i>Yes</i> (partition de démarrage aussi) → redémarrer.</li>'
       '<li>Tout ce qui est écrit va en mémoire vive : une coupure de courant n’abîme plus la carte. Réglages modifiés, journal et mises à jour disparaissent au redémarrage.</li>'
       '<li>Pour modifier ou mettre à jour : désactiver l’overlay dans le même menu, redémarrer, modifier, réactiver.</li></ol>'
       '<h3>Auto-réparation</h3><p>Si la boucle caméra, l’IA ou la page web se bloquent plusieurs minutes, MoveEye recharge l’IA ou redémarre (comme une mise à jour), le note dans le journal et envoie un message. Au plus 2 redémarrages par heure et 6 par jour, pas avant 5 minutes après le démarrage.</p></section>\n\n',
 "it": '<section id="sdcard" data-icon="🪪"><h2>Proteggere la scheda di memoria &amp; autoriparazione</h2>'
       '<p>In campeggio la corrente va via spesso senza preavviso, e una scheda di memoria scritta tutto il giorno si consuma. L’<b>🩺 autodiagnosi</b> mostra sotto «Scheda di memoria: stato» quanto viene scritto al giorno, se ci sono errori del file system e lo spazio libero.</p>'
       '<h3>Scrivere meno</h3><ul><li>Registrazioni su una chiavetta USB o un SSD (Impostazioni → Registrazione).</li><li>Registrazione continua e timelapse solo se servono.</li>'
       '<li>MoveEye scrive poco: impostazioni al massimo ogni 15 secondi, segno di vita una volta al minuto dopo 15 minuti, lo stesso errore solo ogni 10 minuti nel protocollo.</li></ul>'
       '<h3>Durante la stagione: scheda in sola lettura (overlay)</h3><ol><li>Prima configurare tutto e provare una notte.</li><li>Registrazioni su chiavetta USB / SSD – altrimenti spariscono al riavvio.</li>'
       '<li>Sul Pi: <code>sudo raspi-config</code> → <i>Performance Options</i> → <i>Overlay File System</i> → <i>Yes</i> (anche la partizione di avvio) → riavviare.</li>'
       '<li>Tutto ciò che viene scritto va nella RAM: un’interruzione di corrente non danneggia più la scheda. Impostazioni modificate, protocollo e aggiornamenti spariscono al riavvio.</li>'
       '<li>Per modifiche o aggiornamenti: disattivare l’overlay nello stesso menu, riavviare, modificare, riattivare.</li></ol>'
       '<h3>Autoriparazione</h3><p>Se il ciclo della telecamera, l’IA o la pagina web restano bloccati per alcuni minuti, MoveEye ricarica l’IA o si riavvia (come un aggiornamento), lo annota nel protocollo e invia un messaggio. Al massimo 2 riavvii all’ora e 6 al giorno, non prima di 5 minuti dall’avvio.</p></section>\n\n',
 "rm": '<section id="sdcard" data-icon="🪪"><h2>Schanegiar la carta da memoria &amp; autoguariziun</h2>'
       '<p>Sin il plazza da campar mancan l’electricitad savens senza avertiment, ed ina carta da memoria che vegn scritta tut il di sa consuma. L’<b>🩺 autodiagnosa</b> mussa sut «Carta da memoria: stadi» quant che vegn scrit per di, sch’i dat errurs dal sistem da datotecas e quant che è liber.</p>'
       '<h3>Scriver main</h3><ul><li>Metter las registraziuns sin in stick USB u ina SSD (Configuraziuns → Registraziun).</li><li>Registraziun permanenta e timelapse mo sch’ins dovra quai.</li>'
       '<li>MoveEye scriva pauc: configuraziuns maximalmain mintga 15 secundas, il segn da vita suenter 15 minutas mo ina giada per minuta, la medema errur mo mintga 10 minutas en il protocol.</li></ul>'
       '<h3>Durant la stagiun: carta protegida cunter scriver (overlay)</h3><ol><li>L’emprim configurar tut ed empruvar ina notg.</li><li>Registraziuns sin stick USB / SSD – uschiglio mancan ellas suenter in reaviament.</li>'
       '<li>Sin il Pi: <code>sudo raspi-config</code> → <i>Performance Options</i> → <i>Overlay File System</i> → <i>Yes</i> (er la partiziun da boot) → reaviar.</li>'
       '<li>Tut quai che vegn scrit va en la memoria (RAM): ina interrupziun da electricitad na po betg pli donnegiar la carta. Configuraziuns midadas, protocol ed actualisaziuns mancan dentant suenter in reaviament.</li>'
       '<li>Per midadas u actualisaziuns: deactivar l’overlay en il medem menu, reaviar, midar, activar puspè.</li></ol>'
       '<h3>Autoguariziun</h3><p>Sche la cirquitaziun da la camera, l’IA u la pagina web pendan pliras minutas, chargia MoveEye da nov l’IA u sa reavia (sco tar ina actualisaziun), nota quai en il protocol e trametta in avis. Maximalmain 2 reaviaments per ura e 6 per di, betg avant 5 minutas suenter l’aviar.</p></section>\n\n',
}


def _help_sd(doc, lang):
    if '<section id="sdcard"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    if i < 0:
        i = doc.find('<section id="privacy"')
    return doc[:i] + _HELP_SD[lang] + doc[i:] if i >= 0 else doc


_hp_en = HELP_PAGE.find('<div lang="en">')
if _hp_en > 0:
    HELP_PAGE = _help_sd(HELP_PAGE[:_hp_en], "de") + _help_sd(HELP_PAGE[_hp_en:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_sd(HELP_X[_L], _L)
