#@ MoveEye – Teil 604: Übersetzungen für Gehtest, Entfernung, Wärmebild-Personen und Akku-Sparen (2.98.13). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_ERKENNUNG = {
    # distance / direction (415)
    'Person': ('Person', 'Personne', 'Persona', 'Persuna'),
    'Person (thermal picture)': ('Person (Wärmebild)', 'Personne (image thermique)', 'Persona (immagine termica)', 'Persuna (maletg termic)'),
    'about {m} m': ('ca. {m} m', 'env. {m} m', 'circa {m} m', 'ca. {m} m'),
    'coming closer': ('kommt näher', 's’approche', 'si avvicina', 's’avischina'),
    'moving away': ('entfernt sich', 's’éloigne', 'si allontana', 's’allontanescha'),
    # walk test (415, 535, 575)
    'Walk test': ('Gehtest', 'Test de passage', 'Test di passaggio', 'Test da passar'),
    '🚶 Walk test': ('🚶 Gehtest', '🚶 Test de passage', '🚶 Test di passaggio', '🚶 Test da passar'),
    'Start walk test': ('Gehtest starten', 'Démarrer le test', 'Avviare il test', 'Cumenzar il test'),
    '▶ Start walk test': ('▶ Gehtest starten', '▶ Démarrer le test', '▶ Avviare il test', '▶ Cumenzar il test'),
    'Stop': ('Beenden', 'Arrêter', 'Terminare', 'Terminar'),
    '■ Stop': ('■ Beenden', '■ Arrêter', '■ Terminare', '■ Terminar'),
    'Walk test started': ('Gehtest gestartet', 'Test de passage démarré', 'Test di passaggio avviato', 'Test da passar cumenzà'),
    'Walk past the camera like a visitor would: MoveEye beeps at every detection and draws where you were recognised (and where only movement was seen). 3 minutes, no alarms meanwhile.': (
        'Geh an der Kamera vorbei, wie es ein Besucher tun würde: MoveEye piepst bei jeder Erkennung und zeichnet auf, wo du erkannt wurdest (und wo nur Bewegung zu sehen war). 3 Minuten, in dieser Zeit keine Alarme.',
        'Passe devant la caméra comme le ferait un visiteur : MoveEye bipe à chaque détection et note où tu as été reconnu (et où seul un mouvement a été vu). 3 minutes, sans alarme pendant ce temps.',
        'Passa davanti alla telecamera come farebbe un visitatore: MoveEye emette un bip a ogni rilevamento e segna dove sei stato riconosciuto (e dove si è visto solo un movimento). 3 minuti, nel frattempo nessun allarme.',
        'Va sper la camera vi sco in visitader: MoveEye pipa tar mintga identificaziun e marca, nua che ti es vegnì identifitgà (e nua ch’i sa vesa mo in moviment). 3 minutas, durant quel temp nagins alarms.'),
    'Test the range: walk past the camera': ('Reichweite testen: an der Kamera vorbeigehen', 'Tester la portée : passer devant la caméra', 'Provare la portata: passare davanti alla telecamera', 'Testar la distanza: ir sper la camera vi'),
    'Person recognised': ('Person erkannt', 'Personne reconnue', 'Persona riconosciuta', 'Persuna identifitgada'),
    'Movement, no person': ('Bewegung, keine Person', 'Mouvement, pas de personne', 'Movimento, nessuna persona', 'Moviment, nagina persuna'),
    'only in the thermal picture': ('nur im Wärmebild', 'seulement dans l’image thermique', 'solo nell’immagine termica', 'mo en il maletg termic'),
    'last': ('zuletzt', 'dernier', 'ultimo', 'l’ultim'),
    'Last walk test': ('Letzter Gehtest', 'Dernier test de passage', 'Ultimo test di passaggio', 'Ultim test da passar'),
    'Distance': ('Entfernung', 'Distance', 'Distanza', 'Distanza'),
    'recognised': ('erkannt', 'reconnu', 'riconosciuto', 'identifitgà'),
    'only movement': ('nur Bewegung', 'seulement mouvement', 'solo movimento', 'mo moviment'),
    'distance estimated from the height (person 1.7 m)': ('Entfernung geschätzt aus der Höhe (Person 1,7 m)', 'distance estimée d’après la hauteur (personne 1,7 m)', 'distanza stimata dall’altezza (persona 1,7 m)', 'distanza stimada tenor l’autezza (persuna 1,7 m)'),
    'No loudspeaker on the Pi - this page beeps (keep it open).': ('Kein Lautsprecher am Pi – diese Seite piepst (offen lassen).', 'Pas de haut-parleur sur le Pi – cette page bipe (la laisser ouverte).', 'Nessun altoparlante sul Pi – questa pagina emette il bip (lasciarla aperta).', 'Nagin autpledader al Pi – questa pagina pipa (laschar averta).'),
    'Walk test running - no alarms': ('Gehtest läuft – keine Alarme', 'Test de passage en cours – pas d’alarme', 'Test di passaggio in corso – nessun allarme', 'Test da passar en lavur – nagins alarms'),
    'green': ('grün', 'vert', 'verde', 'verd'), 'orange': ('orange', 'orange', 'arancione', 'oransch'), 'violet': ('violett', 'violet', 'viola', 'violet'),
    'Left part': ('Linker Teil', 'Partie gauche', 'Parte sinistra', 'Part sanestra'),
    'Middle part': ('Mittlerer Teil', 'Partie centrale', 'Parte centrale', 'Part dal mez'),
    'Right part': ('Rechter Teil', 'Partie droite', 'Parte destra', 'Part dretga'),
    'No person was recognised. Walk upright across the picture, 3 to 15 m from the camera; check the light, the zones and the AI.': (
        'Es wurde keine Person erkannt. Aufrecht quer durchs Bild gehen, 3 bis 15 m von der Kamera; Licht, Zonen und KI prüfen.',
        'Aucune personne n’a été reconnue. Marcher debout à travers l’image, à 3 à 15 m de la caméra ; vérifier la lumière, les zones et l’IA.',
        'Nessuna persona è stata riconosciuta. Camminare eretti attraverso l’immagine, da 3 a 15 m dalla telecamera; controllare luce, zone e IA.',
        'Nagina persuna n’è vegnida identifitgada. Ir dretg tras il maletg, 3 fin 15 m da la camera; controllar la glisch, las zonas e l’IA.'),
    'Person recognised {n}x - from about {lo} m to about {hi} m.': ('Person {n}× erkannt – von ca. {lo} m bis ca. {hi} m.', 'Personne reconnue {n}× – d’env. {lo} m à env. {hi} m.', 'Persona riconosciuta {n}× – da circa {lo} m a circa {hi} m.', 'Persuna identifitgada {n}× – da ca. {lo} m fin ca. {hi} m.'),
    '{n}x only in the thermal picture.': ('{n}× nur im Wärmebild.', '{n}× seulement dans l’image thermique.', '{n}× solo nell’immagine termica.', '{n}× mo en il maletg termic.'),
    '{where}: movement seen {m}x, but a person only {d}x - you are hardly recognised there (too far, covered, too dark or outside the zones?).': (
        '{where}: {m}× Bewegung gesehen, aber nur {d}× eine Person – dort wirst du kaum erkannt (zu weit, verdeckt, zu dunkel oder ausserhalb der Zonen?).',
        '{where} : mouvement vu {m}×, mais une personne seulement {d}× – là, tu es à peine reconnu (trop loin, caché, trop sombre ou hors des zones ?).',
        '{where}: movimento visto {m}×, ma una persona solo {d}× – lì vieni riconosciuto a stento (troppo lontano, coperto, troppo buio o fuori dalle zone?).',
        '{where}: {m}× moviment vis, ma mo {d}× ina persuna – là vegns ti strusch identifitgà (memia lontan, cuvert, memia stgir u ordaifer las zonas?).'),
    '{where}: nothing seen - did you walk there?': ('{where}: nichts gesehen – bist du dort gegangen?', '{where} : rien vu – es-tu passé par là ?', '{where}: niente visto – sei passato di lì?', '{where}: nagut vis – es ti ì là?'),
    'From about {lo} m on movement is seen more often than a person: the range for persons ends there.': (
        'Ab ca. {lo} m wird öfter Bewegung als eine Person gesehen: dort endet die Reichweite für Personen.',
        'À partir d’env. {lo} m, on voit plus souvent un mouvement qu’une personne : la portée pour les personnes s’arrête là.',
        'Da circa {lo} m in poi si vede più spesso un movimento che una persona: lì finisce la portata per le persone.',
        'A partir da ca. {lo} m sa vesa pli savens in moviment ch’ina persuna: là finescha la distanza per persunas.'),
    'the detection is switched off': ('die Erkennung ist ausgeschaltet', 'la détection est désactivée', 'il rilevamento è spento', 'l’identificaziun è deactivada'),
    # battery saver (105)
    'battery saver': ('Akku-Sparen', 'économie de batterie', 'risparmio batteria', 'spargnar accu'),
    'saver': ('Sparen', 'économie', 'risparmio', 'spargnar'),
    'Battery saver off': ('Akku-Sparen aus', 'Économie de batterie désactivée', 'Risparmio batteria spento', 'Spargnar accu deactivà'),
    'Battery saver active: {pct} % (below {thr} %) - at most {fps} pictures per second, the AI less often': (
        'Akku-Sparen aktiv: {pct} % (unter {thr} %) – höchstens {fps} Bilder pro Sekunde, die KI seltener',
        'Économie de batterie active : {pct} % (sous {thr} %) – au plus {fps} images par seconde, l’IA moins souvent',
        'Risparmio batteria attivo: {pct} % (sotto {thr} %) – al massimo {fps} immagini al secondo, l’IA meno spesso',
        'Spargnar accu activ: {pct} % (sut {thr} %) – maximalmain {fps} maletgs per secunda, l’IA pli darar'),
    'Battery saver: below {thr} % fewer pictures and the AI less often': (
        'Akku-Sparen: unter {thr} % weniger Bilder und die KI seltener', 'Économie de batterie : sous {thr} %, moins d’images et l’IA moins souvent',
        'Risparmio batteria: sotto {thr} % meno immagini e l’IA meno spesso', 'Spargnar accu: sut {thr} % damain maletgs e l’IA pli darar'),
    'Battery saver active: fewer pictures, the AI less often': ('Akku-Sparen aktiv: weniger Bilder, die KI seltener', 'Économie de batterie active : moins d’images, l’IA moins souvent',
                                                              'Risparmio batteria attivo: meno immagini, l’IA meno spesso', 'Spargnar accu activ: damain maletgs, l’IA pli darar'),
    'Battery {pct} %: the battery saver is on - fewer pictures per second, the AI less often. Back to normal when charging.': (
        'Akku {pct} %: Akku-Sparen ist eingeschaltet – weniger Bilder pro Sekunde, die KI seltener. Beim Laden wieder normal.',
        'Batterie {pct} % : l’économie de batterie est active – moins d’images par seconde, l’IA moins souvent. Retour à la normale à la recharge.',
        'Batteria {pct} %: il risparmio batteria è attivo – meno immagini al secondo, l’IA meno spesso. Torna normale durante la ricarica.',
        'Accu {pct} %: spargnar accu è activà – damain maletgs per secunda, l’IA pli darar. Cun chargiar puspè normal.'),
    # settings (575)
    'Thermal picture: an upright warm body counts as a person (at night, when the camera sees nobody)': (
        'Wärmebild: ein aufrechter warmer Körper zählt als Person (nachts, wenn die Kamera niemanden sieht)',
        'Image thermique : un corps chaud debout compte comme une personne (la nuit, quand la caméra ne voit personne)',
        'Immagine termica: un corpo caldo in piedi conta come persona (di notte, quando la telecamera non vede nessuno)',
        'Maletg termic: in corp chaud en pe dumbra sco persuna (la notg, cur che la camera na vesa nagin)'),
    '… by day too': ('… auch am Tag', '… aussi de jour', '… anche di giorno', '… er di'),
    'Battery saver: below the threshold fewer pictures and the AI less often (by itself)': (
        'Akku-Sparen: unter der Schwelle weniger Bilder und die KI seltener (von selbst)',
        'Économie de batterie : sous le seuil, moins d’images et l’IA moins souvent (automatiquement)',
        'Risparmio batteria: sotto la soglia meno immagini e l’IA meno spesso (da solo)',
        'Spargnar accu: sut il limit damain maletgs e l’IA pli darar (da sasez)'),
    'Battery saver from (% battery; back to normal at +5 % or when charging)': (
        'Akku-Sparen ab (% Akku; wieder normal bei +5 % oder beim Laden)', 'Économie de batterie dès (% batterie ; normal à +5 % ou à la recharge)',
        'Risparmio batteria da (% batteria; normale a +5 % o in ricarica)', 'Spargnar accu a partir da (% accu; puspè normal tar +5 % u cun chargiar)'),
    'Battery saver: at most pictures per second': ('Akku-Sparen: höchstens Bilder pro Sekunde', 'Économie de batterie : au plus images par seconde',
                                                   'Risparmio batteria: al massimo immagini al secondo', 'Spargnar accu: maximalmain maletgs per secunda'),
    'Camera: vertical field of view (°) - for the distance of a person (Camera Module 3: 41)': (
        'Kamera: senkrechter Bildwinkel (°) – für die Entfernung einer Person (Camera Module 3: 41)',
        'Caméra : angle de vue vertical (°) – pour la distance d’une personne (Camera Module 3 : 41)',
        'Telecamera: angolo di campo verticale (°) – per la distanza di una persona (Camera Module 3: 41)',
        'Camera: angul da vista vertical (°) – per la distanza d’ina persuna (Camera Module 3: 41)'),
}
for _k, _v in _HX_ERKENNUNG.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- the manual: four lines in the chapter «detect» of every language (2.98.13) ----
_HELP_ERK = {
    "de": '<li><b>🚶 Gehtest</b> (Live oder Schutz): beim Einrichten 3 Minuten an der Kamera vorbeigehen. MoveEye piepst bei jeder Erkennung (Lautsprecher und offene Seite) und zeichnet ins Bild, wo du erkannt wurdest (grün) und wo nur Bewegung zu sehen war (orange) – mit geschätzter Entfernung. In dieser Zeit gibt es keine Alarme.</li>'
          '<li><b>📏 Entfernung:</b> aus der Höhe einer Person (etwa 1,7 m) und dem Bildwinkel der Kamera schätzt MoveEye, wie weit sie weg ist und ob sie näher kommt – im Livebild und in der Push-Nachricht («Person, ca. 12 m, kommt näher»).</li>'
          '<li><b>🌡 Person im Wärmebild:</b> nachts, wenn die Kamera niemanden sieht, zählt ein aufrechter warmer Körper in passender Grösse als Person (Alarm «Person (Wärmebild)»). Einstellung unter Wärmebild; braucht eine Wärmebildkamera.</li>'
          '<li><b>🐢 Akku-Sparen:</b> unter 25 % Akku (einstellbar) weniger Bilder pro Sekunde und die KI seltener; beim Laden oder 5 % darüber wieder normal. Eine Info-Nachricht, sichtbar unter Schutz und in der Akku-Anzeige.</li>',
    "en": '<li><b>🚶 Walk test</b> (Live or Protection): when setting up, walk past the camera for 3 minutes. MoveEye beeps at every detection (loudspeaker and the open page) and draws where you were recognised (green) and where only movement was seen (orange) – with the estimated distance. No alarms meanwhile.</li>'
          '<li><b>📏 Distance:</b> from the height of a person (about 1.7 m) and the field of view of the camera MoveEye estimates how far away it is and whether it comes closer – on the live picture and in the push message («Person, about 12 m, coming closer»).</li>'
          '<li><b>🌡 Person in the thermal picture:</b> at night, when the camera sees nobody, an upright warm body of the right size counts as a person (alarm «Person (thermal picture)»). Setting under Thermal camera; needs a thermal camera.</li>'
          '<li><b>🐢 Battery saver:</b> below 25 % battery (adjustable) fewer pictures per second and the AI less often; back to normal when charging or 5 % above. One info message, shown under Protection and in the battery display.</li>',
    "fr": '<li><b>🚶 Test de passage</b> (Direct ou Protection) : à l’installation, passer devant la caméra pendant 3 minutes. MoveEye bipe à chaque détection et dessine où tu as été reconnu (vert) et où seul un mouvement a été vu (orange) – avec la distance estimée. Pas d’alarme pendant ce temps.</li>'
          '<li><b>📏 Distance :</b> d’après la hauteur d’une personne (env. 1,7 m) et l’angle de vue, MoveEye estime sa distance et si elle s’approche – dans l’image en direct et dans la notification («Personne, env. 12 m, s’approche»).</li>'
          '<li><b>🌡 Personne dans l’image thermique :</b> la nuit, quand la caméra ne voit personne, un corps chaud debout de taille plausible compte comme personne. Réglage sous Caméra thermique.</li>'
          '<li><b>🐢 Économie de batterie :</b> sous 25 % (réglable), moins d’images par seconde et l’IA moins souvent ; normal à la recharge ou 5 % au-dessus.</li>',
    "it": '<li><b>🚶 Test di passaggio</b> (Live o Protezione): durante l’installazione passare davanti alla telecamera per 3 minuti. MoveEye emette un bip a ogni rilevamento e disegna dove sei stato riconosciuto (verde) e dove si è visto solo un movimento (arancione) – con la distanza stimata. Nel frattempo nessun allarme.</li>'
          '<li><b>📏 Distanza:</b> dall’altezza di una persona (circa 1,7 m) e dall’angolo di campo MoveEye stima quanto è lontana e se si avvicina – nell’immagine live e nella notifica («Persona, circa 12 m, si avvicina»).</li>'
          '<li><b>🌡 Persona nell’immagine termica:</b> di notte, quando la telecamera non vede nessuno, un corpo caldo in piedi di grandezza plausibile conta come persona. Impostazione sotto Telecamera termica.</li>'
          '<li><b>🐢 Risparmio batteria:</b> sotto il 25 % (regolabile) meno immagini al secondo e l’IA meno spesso; normale in ricarica o 5 % sopra.</li>',
    "rm": '<li><b>🚶 Test da passar</b> (Live u Protecziun): cun installar ir 3 minutas sper la camera vi. MoveEye pipa tar mintga identificaziun e dissegna, nua che ti es vegnì identifitgà (verd) e nua ch’i sa vesa mo in moviment (oransch) – cun la distanza stimada. Durant quel temp nagins alarms.</li>'
          '<li><b>📏 Distanza:</b> tenor l’autezza d’ina persuna (ca. 1,7 m) e l’angul da vista stima MoveEye, quant lontan ch’ella è e sch’ella s’avischina – en il maletg live ed en l’avis push.</li>'
          '<li><b>🌡 Persuna en il maletg termic:</b> la notg, cur che la camera na vesa nagin, dumbra in corp chaud en pe da grondezza adattada sco persuna. Parameter sut Camera termica.</li>'
          '<li><b>🐢 Spargnar accu:</b> sut 25 % (reglabel) damain maletgs per secunda e l’IA pli darar; puspè normal cun chargiar u 5 % sur il limit.</li>',
}


def _help_erk(doc, lang):
    i = doc.find('<section id="detect"')
    j = doc.find("</ul>", i) if i >= 0 else -1
    return doc[:j] + _HELP_ERK[lang] + doc[j:] if j > 0 and "🚶" not in doc[i:j] else doc


_hp_en = HELP_PAGE.find('<div lang="en">')
if _hp_en > 0:
    HELP_PAGE = _help_erk(HELP_PAGE[:_hp_en], "de") + _help_erk(HELP_PAGE[_hp_en:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_erk(HELP_X[_L], _L)
