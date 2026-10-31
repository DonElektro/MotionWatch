#@ MoveEye – Teil 639j: «Beim Start: Nur Gruppen» – Übersetzungen (DE/FR/IT/RM) und Anleitungs-Absatz (Tipps, DE/EN) zum Schalter ui_start_groups (020, 530, 470, 550, 570). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# nurgruppen (Daniel, 31.10.2026): on every start the settings show «Groups only» (web, phone, Pi window, simulator page); the
# own open / closed state is kept (web: mw-open:… through web_ui, window: CFG ui_open) and comes back when the switch is off.
# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_NG = {
    'On start: groups only': ('Beim Start: Nur Gruppen', 'Au démarrage : seulement les groupes', 'All’avvio: solo i gruppi', 'Al start: mo las gruppas'),
    'On every start the settings show only the groups. Off: the menus open as you left them.':
        ('Bei jedem Start zeigen die Einstellungen nur die Gruppen. Aus: Die Menüs sind auf- und zugeklappt, wie du sie verlassen hast.',
         'À chaque démarrage, les réglages n’affichent que les groupes. Désactivé : les menus restent ouverts ou fermés comme vous les avez laissés.',
         'A ogni avvio le impostazioni mostrano solo i gruppi. Spento: i menu restano aperti o chiusi come li hai lasciati.',
         'A mintga start mussan ils parameters mo las gruppas. Deactivà: ils menus èn averts u serrads sco che ti als has laschads.'),
}
for _k, _v in _HX_NG.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the main page has its own dictionary (German); fr / it / rm come through /i18n/<lang>.js (TRX)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps({_k: _v[0] for _k, _v in _HX_NG.items()}, ensure_ascii=False)
                            + ");</script></body>", 1)

# the manual (HELP_PAGE of 540): one paragraph in «Tipps & Tricks», German and English
for _a, _b in (('<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>',
                "<p><b>☰ Beim Start: Nur Gruppen:</b> Bei jedem Öffnen der Seite (Handy, PC, Pi-Fenster) stehen die Einstellungen in der "
                "Ansicht «Nur Gruppen»: alle Gruppen offen, die Themen darin zu. Was du selbst auf- und zuklappst, merkt sich MoveEye trotzdem. "
                "Schaltest du den Schalter «Beim Start: Nur Gruppen» (neben «Einfach / Experte») aus, sind alle Menüs sofort wieder so, wie du "
                "sie zuletzt verlassen hast. Ab Werk: ein. Auf der Seite Simulator sind beim Start die Karten und die Gruppen der "
                "Simulator-Steuerung zu (nur «Steuerung» bleibt offen).</p>"),
               ('<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>',
                "<p><b>☰ On start: groups only:</b> every time a page opens (phone, PC, Pi window) the settings show «Groups only»: "
                "all groups open, the topics inside closed. MoveEye still remembers what you open and close yourself. Switch «On start: "
                "groups only» (next to «Simple / Expert») off and every menu is back the way you left it. Factory setting: on. On the "
                "page Simulator the cards and the groups of the simulator control start closed (only «Controls» stays open).</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
