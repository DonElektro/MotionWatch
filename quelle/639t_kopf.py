#@ MoveEye – Teil 639t: der gemeinsame Kopf (ein Baustein für jede Web-Seite, das Pi-Fenster und den Simulator): feste Knöpfe ? · 🔔 · ↻ · DE · ☰ · ⛶ · ▲ · 🛠 in fester Reihenfolge, seiteneigene Knöpfe im ☰-Menü («Diese Seite»), und die Ein-/Ausblenden-Listen als Chips mit Symbol in Gruppen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Besitzer (01.11.2026, Screenshot): «oben rechts im Kopf stehen je nach Reiter andere Knöpfe in anderer Reihenfolge» -> Entscheid: ein
# gemeinsamer Kopf, überall gleich. Die Liste der Knöpfe steht in simulator3d/ui_gemeinsam.json («kopf», eingebettet als UI_GEMEINSAM, 639p):
#   ? Hilfe (Rundgang der Seite 516, sonst die Anleitung) · 🔔 Ton (Alarmton 510) · ↻ zuerst Live, dann neu laden (510, jetzt immer da)
#   · DE Sprache · ☰ Menü · ⛶ Vollbild · ▲ Kopf einklappen (510) · 🛠 Entwickler (nur Entwickler-Bereich an UND Besitzer, wie 639s)
# Gleiche Grösse (38 × 34 px, Handy 34 × 30), gleicher Abstand, gleiche gezeichnete Symbole. Schmal (bis 760 px): ab «Sprache» wandern die
# Knöpfe ins ☰-Menü, in derselben Reihenfolge (Abschnitt «Kopf»). Alles andere, was eine Seite in ihren Kopf legt (🖨 Drucken, ◉ Hell /
# Dunkel / Rotlicht, 💬 Rückmeldung, …), kommt ins ☰-Menü: «Diese Seite» bzw. «Allgemein» - es geht nichts verloren, die Knöpfe bleiben
# mit ihrer Id auf der Seite (nur unsichtbar), ihre Funktionen laufen unverändert.
# Die Häkchen-Listen (☰ «Kopfzeile / Bereiche / Einstellungen», «◫ Ansicht der Live-Seite → Karten», Pi-Fenster ☰) zeigt derselbe Baustein:
# MWK.toggles(box, gruppen) - Gruppen mit Symbol und Überschrift, pro Gruppe «alle an / aus», Chips mit Symbol und Namen, zwei Spalten
# auf breiten Bildschirmen, eine auf dem Handy (Besitzer 01.11.2026, zweiter Screenshot).
# Pi-Fenster: App._kopf_tk() (Knöpfe) und App._view_menu() (Liste) unten; Simulator: simulator3d/scripts/kopf.gd.

MWK_KOPF = UI_GEMEINSAM["kopf"]
KOPF_IDS = [b["id"] for b in MWK_KOPF["knoepfe"]]

# the chips of the status line: id -> (symbol of the chip, group of the list) - the same table for web (b-…) and Pi window (b_…)
KOPF_CHIPS = {
    "title": ("🏷", "other"), "hdr_buttons": ("🔘", "other"),
    "b-arm": ("🛡", "protect"), "b-person": ("🧍", "protect"), "b-count": ("🔢", "protect"), "b-obj": ("📦", "protect"),
    "b-pres": ("🏠", "protect"), "b-sched": ("🗓", "protect"), "b-lock": ("🔐", "protect"), "b-sec": ("⚠", "protect"),
    "b-mode": ("🎛", "protect"), "b-camp": ("⛺", "protect"),
    "b-rec": ("⏺", "camera"), "b-tl": ("⏱", "camera"), "b-src": ("🎞", "camera"), "b-therm": ("🌡", "camera"), "b-pat": ("🔄", "camera"),
    "b-audio": ("🎤", "camera"), "b-fps": ("🎬", "camera"), "b-auto": ("🎚", "camera"),
    "b-batt": ("🔋", "power"), "b-eco": ("🍃", "power"), "b-turbo": ("🚀", "power"), "b-pwr": ("⚡", "power"), "b-cpu": ("🖥", "power"),
    "b-lights": ("💡", "env"), "b-env": ("🌡", "env"), "b-rain": ("🌧", "env"), "b-wind": ("💨", "env"), "b-light": ("☀", "env"),
    "b-hs": ("📡", "net"), "b-remote": ("🌐", "net"), "b-conn": ("🔗", "net"), "b-wifi": ("📶", "net"), "b-view": ("👁", "net"),
    "b-relay": ("🔌", "other"), "b-health": ("🩺", "other"), "b-update": ("⬆", "other"),
}
KOPF_CHIP_ALIAS = {"b_objects": "b-obj", "b_patrol": "b-pat", "b_relays": "b-relay"}   # Pi window keys that differ
KOPF_PANELS = {      # the cards / panels (☰ «Bereiche», ◫ Ansicht → Karten, Pi window «Panels»)
    "controls": "🎮", "simctl": "🧪", "sidebar": "⚙", "protect": "⛺", "tune": "🎯", "health": "🩺", "system": "🖥", "log": "📜",
    "wifi": "📶", "source": "🎞", "schedule": "🗓", "relayset": "🔌", "report": "🌙", "guest": "👋", "batt": "🔋", "walktest": "🚶",
    "lvsetup": "🧰", "whatwas": "❓", "simtile": "🧪", "weather": "🌦", "cpu": "🖥", "settings_line": "⚙",
}


def kopf_chip(key):
    """(symbol, group) of a chip; the Pi window writes b_arm, the web b-arm"""
    k = KOPF_CHIP_ALIAS.get(key, key)
    return KOPF_CHIPS.get(k) or KOPF_CHIPS.get(k.replace("_", "-")) or ("•", "other")


# key = English text: (Deutsch, Français, Italiano, Rumantsch) - the names in the lists (before: «Armed / disarmed» English in German)
_HX_KOPF = {
    "Title": ("Titel", "Titre", "Titolo", "Titel"),
    "Armed / disarmed": ("Schutz-Zustand", "État de la protection", "Stato della protezione", "Stadi da la protecziun"),
    "Persons": ("Personen", "Personnes", "Persone", "Persunas"),
    "Persons total": ("Personen gesamt", "Personnes au total", "Persone in totale", "Persunas en total"),
    "Objects": ("Objekte", "Objets", "Oggetti", "Objects"),
    "Recording": ("Aufnahme", "Enregistrement", "Registrazione", "Registraziun"),
    "Camping profile": ("Camping-Profil", "Profil camping", "Profilo campeggio", "Profil da camping"),
    "Power saving": ("Stromsparmodus", "Économie d’énergie", "Risparmio energetico", "Spargnar energia"),
    "Mode": ("Modus", "Mode", "Modalità", "Modus"),
    "Power mode": ("Powermodus", "Mode puissance", "Modalità potenza", "Modus da forza"),
    "Battery": ("Akku", "Batterie", "Batteria", "Accu"),
    "Operator mode": ("Bedienmodus", "Mode opérateur", "Modalità operatore", "Modus d’operatur"),
    "Timelapse": ("Zeitraffer", "Accéléré", "Timelapse", "Accelerà"),
    "Lights": ("Licht", "Éclairage", "Luci", "Glisch"),
    "Outside temperature": ("Aussentemperatur", "Température extérieure", "Temperatura esterna", "Temperatura dadora"),
    "Self-check": ("Selbstcheck", "Autodiagnostic", "Autodiagnosi", "Autocontroll"),
    "Thermal camera": ("Wärmebild", "Caméra thermique", "Termocamera", "Camera termica"),
    "Patrol / tracking": ("Patrouille / Verfolgen", "Patrouille / suivi", "Pattuglia / inseguimento", "Patrulla / persequitar"),
    "Patrol": ("Patrouille", "Patrouille", "Pattuglia", "Patrulla"),
    "Own Wi-Fi (hotspot)": ("Eigenes WLAN (Hotspot)", "Wi-Fi propre (hotspot)", "Wi-Fi proprio (hotspot)", "Agen WLAN (hotspot)"),
    "Remote access": ("Fernzugriff", "Accès à distance", "Accesso remoto", "Access a distanza"),
    "Schedule": ("Zeitplan", "Horaire", "Orario", "Urari"),
    "Relays": ("Relais", "Relais", "Relè", "Relais"),
    "Microphone": ("Mikrofon", "Microphone", "Microfono", "Microfon"),
    "Rain": ("Regen", "Pluie", "Pioggia", "Plievgia"),
    "Wind": ("Wind", "Vent", "Vento", "Vent"),
    "Light level": ("Helligkeit", "Luminosité", "Luminosità", "Clerezza"),
    "Presence": ("Anwesenheit", "Présence", "Presenza", "Preschientscha"),
    "Security warning": ("Sicherheitswarnung", "Avertissement de sécurité", "Avviso di sicurezza", "Avertiment da segirezza"),
    "Power supply / memory": ("Stromversorgung / Speicher", "Alimentation / mémoire", "Alimentazione / memoria", "Alimentaziun / memoria"),
    "Video source": ("Videoquelle", "Source vidéo", "Sorgente video", "Funtauna da video"),
    "Connection": ("Verbindung", "Connexion", "Connessione", "Connexiun"),
    "Wi-Fi": ("WLAN", "Wi-Fi", "Wi-Fi", "WLAN"),
    "Viewers": ("Zuschauer", "Spectateurs", "Spettatori", "Aspectaturs"),
    "CPU": ("CPU", "CPU", "CPU", "CPU"),
    "FPS": ("Bilder/s", "Images/s", "Fotogrammi/s", "Maletgs/s"),
    "New version": ("Neue Version", "Nouvelle version", "Nuova versione", "Nova versiun"),
    "Auto-tune": ("Auto-Abgleich", "Réglage automatique", "Regolazione automatica", "Adattaziun automatica"),
    "Header buttons": ("Kopf-Knöpfe", "Boutons de l’en-tête", "Pulsanti dell’intestazione", "Buttuns dal chau"),
    "Header": ("Kopfzeile", "En-tête", "Intestazione", "Lingia dal chau"),
    "Panels": ("Bereiche", "Panneaux", "Pannelli", "Secziuns"),
    "Settings": ("Einstellungen", "Réglages", "Impostazioni", "Parameters"),
    "Settings sections": ("Einstellungs-Abschnitte", "Sections des réglages", "Sezioni delle impostazioni", "Secziuns dals parameters"),
    "Controls": ("Steuerung", "Commandes", "Comandi", "Commonds"),
    "Simulator control": ("Simulator-Steuerung", "Commande du simulateur", "Controllo del simulatore", "Commond dal simulatur"),
    "Settings panel": ("Einstellungsbereich", "Panneau des réglages", "Pannello impostazioni", "Secziun dals parameters"),
    "Camping / protection": ("Camping / Schutz", "Camping / protection", "Campeggio / protezione", "Camping / protecziun"),
    "Improve detection": ("Erkennung verbessern", "Améliorer la détection", "Migliorare il rilevamento", "Meglierar l’identificaziun"),
    "System": ("System", "Système", "Sistema", "Sistem"),
    "Event log": ("Ereignisprotokoll", "Journal des événements", "Registro eventi", "Protocol dals eveniments"),
    "Wi-Fi / hotspot": ("WLAN / Hotspot", "Wi-Fi / hotspot", "Wi-Fi / hotspot", "WLAN / hotspot"),
    "Relay settings": ("Relais-Einstellungen", "Réglages des relais", "Impostazioni relè", "Parameters dals relais"),
    "Night report": ("Nachtbericht", "Rapport de nuit", "Rapporto notturno", "Rapport da notg"),
    "Guest access": ("Gastzugang", "Accès invité", "Accesso ospite", "Access per giasts"),
    "Walk test": ("Gehtest", "Test de marche", "Test di camminata", "Test da chaminar"),
    "Set up": ("Einrichten", "Configurer", "Configurare", "Configurar"),
    "What was that?": ("Was war das?", "C’était quoi ?", "Cos’era?", "Tge era quai?"),
    "Simulator tile": ("Simulator-Kachel", "Tuile du simulateur", "Riquadro del simulatore", "Plattina dal simulatur"),
    "Weather": ("Wetter", "Météo", "Meteo", "Aura"),
    "System · CPU": ("System · CPU", "Système · CPU", "Sistema · CPU", "Sistem · CPU"),
    "Settings status": ("Einstellungs-Status", "État des réglages", "Stato delle impostazioni", "Stadi dals parameters"),
    "Cards": ("Karten", "Cartes", "Schede", "Cartas"),
    "Full screen is not possible in this browser – tip: add MoveEye to the home screen.":
        ("Vollbild geht in diesem Browser nicht – Tipp: MoveEye zum Home-Bildschirm hinzufügen.",
         "Le plein écran n’est pas possible dans ce navigateur – astuce : ajoute MoveEye à l’écran d’accueil.",
         "Lo schermo intero non è possibile in questo browser – suggerimento: aggiungi MoveEye alla schermata Home.",
         "Maletg entir n’è betg pussaivel en quest navigatur – tip: agiuntar MoveEye al visur da partenza."),
    "Show the header": ("Kopf ausklappen", "Afficher l’en-tête", "Mostra l’intestazione", "Mussar il chau"),
    "Light / dark / red light": ("Hell / Dunkel / Rotlicht", "Clair / sombre / lumière rouge", "Chiaro / scuro / luce rossa", "Cler / stgir / glisch cotschna"),
    "Feedback to the developer": ("Rückmeldung an den Entwickler", "Retour au développeur", "Feedback allo sviluppatore", "Resposta al sviluppader"),
    "Print": ("Drucken", "Imprimer", "Stampa", "Stampar"),
}
for _b in MWK_KOPF["knoepfe"] + MWK_KOPF["listen"]:
    _x = _b["texts"]
    _HX_KOPF.setdefault(_x["en"], (_x["de"], _x["fr"], _x["it"], _x["rm"]))
for _k, _x in list(MWK_KOPF["menue"].items()) + list(MWK_KOPF["alle"].items()):
    _HX_KOPF.setdefault(_x["en"], (_x["de"], _x["fr"], _x["it"], _x["rm"]))
for _k, _v in _HX_KOPF.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the main page has its own German dictionary (I18N.de): the names of the lists there too (only what it does not know yet)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>(function(){var X=" + json.dumps({_k: _v[0] for _k, _v in _HX_KOPF.items()}, ensure_ascii=False)
                            + ";for(var k in X)if(!(k in I18N.de))I18N.de[k]=X[k];})();</script></body>", 1)


# the manual (HELP_PAGE of 540): one paragraph in «Tipps & Tricks», German and English
for _a, _b in (('<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>',
                "<p><b>Der Kopf ist überall gleich:</b> Oben rechts stehen auf jeder Seite dieselben Knöpfe in derselben Reihenfolge: "
                "? Hilfe · 🔔 Ton · ↻ zurück zu Live und neu laden · DE Sprache · ☰ Menü · ⛶ Vollbild · ▲ Kopf einklappen · 🛠 Entwickler "
                "(nur für den Besitzer mit eingeschaltetem Entwickler-Bereich). Auf dem Handy stehen die Knöpfe ab «Sprache» im ☰-Menü. "
                "Was nur eine Seite hat (z. B. 🖨 Drucken) und Hell / Dunkel / Rotlicht findest du im ☰-Menü unter «Diese Seite» bzw. "
                "«Allgemein». Ein- und Ausblenden: Chips mit Symbol, nach Gruppen geordnet, pro Gruppe «alle an / aus».</p>"),
               ('<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>',
                "<p><b>The header is the same everywhere:</b> at the top right every page has the same buttons in the same order: "
                "? help · 🔔 sound · ↻ back to Live and reload · DE language · ☰ menu · ⛶ full screen · ▲ fold the header · 🛠 developer "
                "(only for the owner with the developer area on). On a phone the buttons from «language» on are in the ☰ menu. "
                "What only one page has (e.g. 🖨 print) and light / dark / red light are in the ☰ menu under «This page» or «General». "
                "Show and hide: chips with a symbol, sorted in groups, «all on / off» per group.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


def kopf_dev_ok(role=None):
    """🛠 only with the developer area on and for the owner (admin, not in operator mode) - the same rule as the long press (639s)"""
    try:
        return bool(dev_available()) and nacht_may(_nacht_role() if role is None else role)
    except Exception:
        return False


def kopf_tx():
    """texts of the header and the lists in de / fr / it / rm (English = the key)"""
    keys = set(_HX_KOPF)
    out = {"de": {k: DE.get(k, k) for k in keys}}
    for L in ("fr", "it", "rm"):
        out[L] = {k: TRX[L].get(k) or (DE.get(k, k) if L == "rm" else k) for k in keys}
    return out


def kopf_web_data():
    gems = {g["id"]: g.get("emoji", "") for g in UI_GEMEINSAM.get("groups", [])}
    return {"ids": KOPF_IDS, "texts": {b["id"]: b["texts"]["en"] for b in MWK_KOPF["knoepfe"]}, "px": MWK_KOPF.get("schmal_px", 760),
            "menu": {k: v["en"] for k, v in MWK_KOPF["menue"].items()}, "all": {k: v["en"] for k, v in MWK_KOPF["alle"].items()},
            "lists": [[b["id"], b["sym"], b["texts"]["en"]] for b in MWK_KOPF["listen"]],
            "chips": {k: list(v) for k, v in KOPF_CHIPS.items()}, "panels": KOPF_PANELS, "groups": gems}


# the drawn symbols (same stroke as the other header buttons of 450: 24 × 24, stroke 2)
_KSVG = lambda d: '<svg viewBox="0 0 24 24" aria-hidden="true">' + d + '</svg>'
KOPF_SVG = {
    "menu": _KSVG('<path d="M4 7h16M4 12h16M4 17h16"/>'),
    "fs": _KSVG('<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>'),
    "dev": _KSVG('<path d="M14.5 6.5a4 4 0 0 0 5 5L21 13l-8 8-3-3 8-8z" transform="translate(-2 -2)"/><path d="M4 20l6-6"/>'),
}

KOPF_CSS = r"""<style id="mwk-css">
/* 639t: the one header - the fixed buttons always in the same order and size; everything else of a page is in the ☰ menu */
.hdr-ctl.mwk{gap:6px;flex-wrap:nowrap}
.hdr-ctl.mwk>*{order:50}
.hdr-ctl.mwk>#mwk-help,.hdr-ctl.mwk>#g2-help{order:1}.hdr-ctl.mwk>#btn-sound{order:2}.hdr-ctl.mwk>#btn-reload{order:3}
.hdr-ctl.mwk>#btn-lang{order:4}.hdr-ctl.mwk>#btn-view,.hdr-ctl.mwk>#mwk-menu-btn{order:5}.hdr-ctl.mwk>#btn-fs,.hdr-ctl.mwk>#mwk-fs{order:6}
.hdr-ctl.mwk>#btn-hdr{order:7}.hdr-ctl.mwk>#mwk-dev{order:8}
.hdr-ctl.mwk>button,.hdr-ctl.mwk>a.btn{width:38px;height:34px;min-width:38px;padding:0!important;display:inline-flex;align-items:center;justify-content:center;
  flex:none;font-size:14px;font-weight:700;line-height:1;text-decoration:none;box-sizing:border-box}
.hdr-ctl.mwk>button svg,.hdr-ctl.mwk>a.btn svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
.hdr-ctl.mwk>#btn-lang{font-size:13px;letter-spacing:.02em}
.hdr-ctl.mwk:has(#g2-help)>#mwk-help{display:none}
.hdr-ctl.mwk>#btn-side,.hdr-ctl.mwk>#btn-theme{display:none!important}
#mwk-hold{display:none!important}
/* phone: the buttons next to the name on every page (like Live, 530); own badges of a page in their own line below */
@media(max-width:760px){header>h1{order:-2}header>.hdr-ctl.mwk{order:-1}
  header>.chips.mwk-chips{display:flex;flex:1 1 100%;flex-wrap:wrap;align-items:center;gap:6px;order:30;min-width:0}}
/* 3.88 (Klar stage 1): touch targets 44 px on the phone (before 34 × 30) - four buttons and the one-line mark fit into 360 px */
@media(max-width:700px){.hdr-ctl.mwk>button,.hdr-ctl.mwk>a.btn{width:44px;min-width:44px;height:44px;border-radius:12px}.hdr-ctl.mwk>button svg,.hdr-ctl.mwk>a.btn svg{width:20px;height:20px}
  .hdr-ctl.mwk{gap:2px}}
@media(max-width:359px){.hdr-ctl.mwk>button,.hdr-ctl.mwk>a.btn{width:40px;min-width:40px}}
/* narrow: from «Language» on, the buttons are in the ☰ menu (section «Header»), in the same order */
@media(max-width:760px){.hdr-ctl.mwk>#btn-lang,.hdr-ctl.mwk>#btn-fs,.hdr-ctl.mwk>#mwk-fs,.hdr-ctl.mwk>#btn-hdr,.hdr-ctl.mwk>#mwk-dev{display:none!important}}
@media(min-width:761px){.mwk-ovf{display:none!important}}
/* the ☰ menu of a page without its own (the main page puts the same sections on top of its #viewmenu) */
#mwk-pop{position:fixed;top:58px;right:12px;z-index:85;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 14px 12px;
  box-shadow:var(--shadow);max-height:calc(100dvh - 76px);overflow:auto;width:min(340px,calc(100vw - 24px));box-sizing:border-box}
#mwk-pop[hidden]{display:none}
.mwk-sec h3{margin:10px 0 6px;font-size:11px;color:var(--mut);letter-spacing:.08em;text-transform:uppercase}
.mwk-rows{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px}
.mwk-row{display:flex!important;align-items:center;gap:8px;padding:7px 10px!important;font-size:13.5px;text-align:left;min-height:38px;width:100%;box-sizing:border-box}
.mwk-row .mwk-i{flex:none;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-weight:700}
.mwk-row .mwk-i svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.mwk-row .mwk-l{flex:1;min-width:0;overflow-wrap:anywhere;line-height:1.25}
.mwk-row.on{border-color:var(--acc)}
/* MWK.toggles: the lists to show / hide (chips with the symbol of the chip, groups with «all on / off», 2 columns when wide) */
.mwt{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px 14px;margin:4px 0}
.mwt-g{border:1px solid var(--line);border-radius:12px;padding:8px 10px 10px;background:var(--field);min-width:0}
.mwt-gh{display:flex;align-items:center;gap:8px;margin:0 0 8px}
.mwt-gh .mwt-gi{font-size:17px;line-height:1}.mwt-gh b{flex:1;min-width:0;font-size:13px}
.mwt-gh button{padding:3px 9px!important;font-size:11.5px;min-height:0;line-height:1.4;white-space:nowrap}
.mwt-cs{display:flex;flex-wrap:wrap;gap:6px}
.mwt-c{display:inline-flex!important;align-items:center;gap:6px;padding:5px 11px 5px 8px!important;border-radius:99px!important;font-size:12.5px;font-weight:600;
  min-height:32px;line-height:1.2;border:1px solid var(--line);background:var(--panel);color:var(--mut);text-align:left;max-width:100%}
.mwt-c .mwt-ci{font-size:15px;line-height:1;flex:none;filter:grayscale(1);opacity:.6}
.mwt-c .mwt-cl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mwt-c.on{background:var(--acc);border-color:transparent!important;color:#fff}.mwt-c.on .mwt-ci{filter:none;opacity:1}
.mwt-c:not(.on) .mwt-cl{text-decoration:line-through;text-decoration-color:rgba(127,127,127,.5)}
#viewmenu.mwk-wide,#lv-menu.mwk-wide{width:min(640px,calc(100vw - 24px))!important;box-sizing:border-box}
@media(max-width:560px){.mwt{grid-template-columns:minmax(0,1fr)}}
</style>"""

KOPF_JS = r"""<script>
(function () {
  if (window.MWK) return;
  const D = window.MWK_DATA || {}, TX = window.MWK_TX || {}, B = document.body;
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "de"; } catch (e) { return "de"; } };
  const tr = k => ((TX[L()] || {})[k]) || (typeof t === "function" && t(k) !== k ? t(k) : "") || (window.LX && LX(k)) || k;
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const H = document.querySelector("header"), C = H && H.querySelector(".hdr-ctl.mwk");
  // ---- the lists: MWK.toggles(box, [{icon, title, items: [{icon, label, on, set(v)}]}], after) ----
  function toggles(box, groups, after) {
    const wrap = E("div", "mwt");
    groups.filter(g => g.items && g.items.length).forEach(g => {
      const sec = E("section", "mwt-g"), hd = E("div", "mwt-gh"), cs = E("div", "mwt-cs");
      hd.append(E("span", "mwt-gi", g.icon || "•"), E("b", "", g.title || ""));
      const all = E("button", "sec"); all.type = "button";
      const paintAll = () => { const on = g.items.every(i => i.on()); all.textContent = tr(on ? D.all.off : D.all.on); all.dataset.v = on ? "0" : "1"; };
      all.onclick = e => { e.stopPropagation(); const v = all.dataset.v === "1"; g.items.forEach(i => { if (i.on() !== v) i.set(v); }); paint(); if (after) after(); };
      hd.appendChild(all);
      const chips = g.items.map(i => { const c = E("button", "mwt-c"); c.type = "button";
        c.append(E("span", "mwt-ci", i.icon || "•"), E("span", "mwt-cl", i.label)); c.title = i.label;
        c.onclick = e => { e.stopPropagation(); i.set(!i.on()); paint(); if (after) after(); }; cs.appendChild(c); return [c, i]; });
      function paint() { chips.forEach(([c, i]) => { const on = !!i.on(); c.classList.toggle("on", on); c.setAttribute("aria-pressed", on ? "true" : "false"); }); paintAll(); }
      sec.append(hd, cs); wrap.appendChild(sec); paint(); g._paint = paint;
    });
    box.appendChild(wrap); return wrap;
  }
  const emo = s => { const m = String(s || "").match(/^\s*((?:\p{Extended_Pictographic}|[☀-➿])️?)/u); return m ? m[1] : ""; };
  function chip(id) { return (D.chips || {})[id] || ["•", "other"]; }
  // the ☰ «Kopfzeile» (Header) of the main page: the chips in groups (Schutz & Erkennung · Kamera & Aufnahme · Strom & Akku · Umgebung · Netz · Sonstiges)
  function headerGroups(els, isOn, set) {
    const G = {}; (D.lists || []).forEach(([id, sym, en]) => { G[id] = {icon: sym, title: tr(en), items: []}; });
    els.forEach(e => { const [ic, g] = chip(e.dataset.view); (G[g] || G.other).items.push({icon: ic, label: tr(e.dataset.vlabel), on: () => isOn(e.dataset.view), set: v => set(e.dataset.view, v)}); });
    return (D.lists || []).map(([id]) => G[id]);
  }
  function panelIcon(e) {
    const v = e.dataset.view || ""; if (v.startsWith("grp:")) return (D.groups || {})[v.slice(4)] || "▦";
    return (D.panels || {})[v] || emo((e.querySelector("summary, h2, h3") || {}).textContent) || "▦";
  }
  function menuLists(m, els, isOn, set, after) {   // ☰ of the main page: Header / Panels / Settings - same component as everywhere
    const by = {}; els.forEach(e => (by[e.dataset.vgroup] = by[e.dataset.vgroup] || []).push(e));
    if (by.Header) { m.appendChild(E("h3", "", tr("Header"))); toggles(m, headerGroups(by.Header, isOn, set), after); }
    if (by.Panels) {
      const P = by.Panels.filter(e => !(e.dataset.view || "").startsWith("grp:")), Gs = by.Panels.filter(e => (e.dataset.view || "").startsWith("grp:"));
      m.appendChild(E("h3", "", tr("Panels")));
      toggles(m, [{icon: "▦", title: tr("Cards"), items: P.map(e => ({icon: panelIcon(e), label: tr(e.dataset.vlabel), on: () => isOn(e.dataset.view), set: v => set(e.dataset.view, v)}))}]
        .concat(Gs.length ? [{icon: "⚙", title: tr("Settings"), items: Gs.map(e => ({icon: panelIcon(e), label: tr(e.dataset.vlabel), on: () => isOn(e.dataset.view), set: v => set(e.dataset.view, v)}))}] : []), after);
    }
    if (by.Settings) {                       // the sections, grouped by their settings group (symbol of the group)
      const G = new Map();
      by.Settings.forEach(e => { const g = e.parentElement && e.parentElement.closest("[data-view^='grp:']"), k = g ? g.dataset.view : "";
        if (!G.has(k)) G.set(k, {icon: g ? panelIcon(g) : "⚙", title: g ? tr(g.dataset.vlabel) : tr("Settings"), items: []});
        G.get(k).items.push({icon: emo(e.dataset.vlabel) || (g ? panelIcon(g) : "⚙"), label: tr(e.dataset.vlabel), on: () => isOn(e.dataset.view), set: v => set(e.dataset.view, v)}); });
      m.appendChild(E("h3", "", tr("Settings sections"))); toggles(m, [...G.values()], after);
    }
  }
  if (!C) { window.MWK = {toggles: toggles, menuLists: menuLists, chip: chip, tr: tr}; return; }
  // ---- the header ----
  const hold = E("div"); hold.id = "mwk-hold"; hold.hidden = true; B.appendChild(hold);
  const KNOWN = new Set(["mwk-help", "g2-help", "btn-sound", "btn-reload", "btn-lang", "btn-view", "mwk-menu-btn", "btn-fs", "mwk-fs", "btn-hdr", "mwk-dev", "btn-side", "btn-theme"]);
  const GENERAL = ["btn-theme", "fbx-b"];
  function tidy() {                          // a page (or a script later) put something else into the header: into the ☰ menu
    [...C.children].forEach(x => { if (!KNOWN.has(x.id)) hold.appendChild(x); });
    const th = C.querySelector("#btn-theme"); if (th) hold.appendChild(th);
    const lg = C.querySelector("#btn-lang"); if (lg) lg.classList.add("ic");
  }
  new MutationObserver(tidy).observe(C, {childList: true}); tidy();
  const btn = id => document.getElementById(id);
  const help = btn("mwk-help"); if (help) help.onclick = () => { const g = btn("g2-help"); if (g) g.click(); else if (window.g2Tour && window.g2Tour()) return; else location.href = "/help"; };
  // ⛶: the page's own (main page: video full screen), else the browser's full screen of the page
  const fs = btn("mwk-fs"); if (fs) fs.onclick = () => { const d = document, el = d.documentElement, cur = d.fullscreenElement || d.webkitFullscreenElement;
    try { if (cur) (d.exitFullscreen || d.webkitExitFullscreen).call(d); else if (el.requestFullscreen || el.webkitRequestFullscreen) { const r = (el.requestFullscreen || el.webkitRequestFullscreen).call(el); if (r && r.catch) r.catch(() => {}); }
      else if (typeof toast === "function") toast(tr("Full screen is not possible in this browser – tip: add MoveEye to the home screen.")); } catch (e) {} };
  const dv = btn("mwk-dev"); if (dv) dv.addEventListener("click", e => { if (typeof tabOpen === "function" && document.querySelector('[data-view="grp:dev"]')) { e.preventDefault(); tabOpen("grp:dev"); } });
  // the ☰ menu: own popup, or the main page's #viewmenu (it calls MWK.fill at its top)
  let pop = null;
  const mb = btn("mwk-menu-btn");
  if (mb) { pop = E("div", "pop"); pop.id = "mwk-pop"; pop.hidden = true; pop.setAttribute("role", "menu"); B.appendChild(pop);
    mb.onclick = e => { e.stopPropagation(); pop.hidden = !pop.hidden; if (!pop.hidden) { pop.textContent = ""; fill(pop); } };
    document.addEventListener("click", e => { if (!pop.hidden && !pop.contains(e.target) && e.target !== mb && document.body.contains(e.target)) pop.hidden = true; });
    document.addEventListener("keydown", e => { if (e.key === "Escape") pop.hidden = true; }); }
  const closeAll = () => { if (pop) pop.hidden = true; const vm = btn("viewmenu"); if (vm) vm.hidden = true; };
  function label(x) { return x.dataset.mwkLabel || x.getAttribute("aria-label") || x.title || (x.textContent || "").trim() || x.id; }
  function row(x, lab, keep, ic) {           // a menu row that does what the (hidden) original does
    const r = E("button", "sec mwk-row"); r.type = "button";
    const i = E("span", "mwk-i"); if (ic) i.textContent = ic; else i.innerHTML = x.innerHTML;
    r.append(i, E("span", "mwk-l", lab || label(x)));
    r.onclick = e => { e.stopPropagation(); if (!keep) closeAll(); x.click(); if (keep) setTimeout(() => { const m = r.closest("#mwk-pop,#viewmenu"); if (m && !m.hidden) { if (m.id === "viewmenu" && typeof buildViewMenu === "function") buildViewMenu(); else { m.textContent = ""; fill(m); } } }, 30); };
    return r;
  }
  function section(m, key, rows, cls) { if (!rows.length) return; const s = E("div", "mwk-sec" + (cls ? " " + cls : "")); s.appendChild(E("h3", "", tr(D.menu[key])));
    const g = E("div", "mwk-rows"); rows.forEach(r => g.appendChild(r)); s.appendChild(g); m.appendChild(s); }
  const themeLab = () => { const s = typeof themeStep === "function" ? themeStep() : ""; return tr("Light / dark / red light") + (s ? " · " + tr({light: "Light theme", dark: "Dark theme", red: "Red light view"}[s] || s) : ""); };
  function fill(m) {
    // 1. narrow: the fixed buttons from «Language» on, in the same order
    const ov = [];
    const lg = btn("btn-lang"); if (lg) { const r = E("button", "sec mwk-row"); r.type = "button"; r.append(E("span", "mwk-i", lg.textContent), E("span", "mwk-l", tr(D.texts.lang)));
      r.onclick = e => { e.stopPropagation(); const a = btn("btn-view") || mb; closeAll(); setTimeout(() => langMenu(a), 0); }; ov.push(r); }
    const f = btn("btn-fs") || btn("mwk-fs"); if (f) ov.push(row(f, tr(D.texts.fs)));
    const hd = btn("btn-hdr"); if (hd) ov.push(row(hd, tr(D.texts.fold)));
    const d = btn("mwk-dev"); if (d) ov.push(row(d, tr(D.texts.dev)));
    section(m, "head", ov, "mwk-ovf");
    // 2. what this page put into its header (🖨 …) and 3. general (◉ Hell / Dunkel / Rotlicht, 💬)
    const page = [], gen = [];
    [...hold.children].forEach(x => { if (x.hidden && !GENERAL.includes(x.id)) return;
      if (x.id === "btn-theme") gen.unshift(row(x, themeLab(), true)); else (GENERAL.includes(x.id) ? gen : page).push(row(x)); });
    section(m, "page", page); section(m, "general", gen);
  }
  function titles() {
    const set = (id, k) => { const x = btn(id); if (x) { x.title = tr(D.texts[k]); x.setAttribute("aria-label", x.title); } };
    set("mwk-help", "help"); set("btn-reload", "reload"); set("btn-lang", "lang"); set("mwk-menu-btn", "menu"); set("btn-view", "menu");
    set("mwk-fs", "fs"); set("btn-fs", "fs"); set("btn-hdr", "fold"); set("mwk-dev", "dev");
  }
  titles(); [800, 2000].forEach(ms => setTimeout(titles, ms));
  window.MWK = {toggles: toggles, menuLists: menuLists, fill: fill, chip: chip, tr: tr, tidy: tidy};
})();
</script>"""


def _kopf_ctl(inner, active):
    """the inside of <span class="hdr-ctl">: the page's buttons stay (the script sorts them), plus ?, ☰, ⛶ and 🛠 where missing"""
    tx = {b["id"]: b["texts"]["en"] for b in MWK_KOPF["knoepfe"]}
    inner = inner.replace('id="btn-view"', 'id="btn-view" data-mwk="menu"', 1)
    out = '<button class="sec ic" type="button" id="mwk-help" title="' + tx["help"] + '">?</button>' + inner
    if 'id="btn-view"' not in inner:
        out += '<button class="sec ic" type="button" id="mwk-menu-btn" title="' + tx["menu"] + '">' + KOPF_SVG["menu"] + '</button>'
    if 'id="btn-fs"' not in inner:
        out += '<button class="sec ic" type="button" id="mwk-fs" title="' + tx["fs"] + '">' + KOPF_SVG["fs"] + '</button>'
    if kopf_dev_ok():
        out += '<a class="btn sec ic" id="mwk-dev" href="/settings?open=grp:dev" title="' + tx["dev"] + '">' + KOPF_SVG["dev"] + '</a>'
    return out


_KOPF_RE = re.compile(r'(<header\b.*?<span class="hdr-ctl)(">)(.*?)(</span>\s*</header>)', re.S)
_KOPF_BADGES = re.compile(r'(?:\s*<span class="badge[^"]*"[^>]*>[^<]*</span>)+')
_render_page_before_kopf = render_page


# wraps: render_page
def render_page(page, active):
    """+ 639t: the one header (fixed buttons, ☰ with the page's own buttons, the lists as chips) on every page with a header"""
    out = _render_page_before_kopf(page, active)
    m = _KOPF_RE.search(out)
    if not m:
        return out
    head = m.group(1)
    if 'class="chips"' not in head:          # a page with its own badges (Aufnahmen: count, memory, ● REC): into the status line like Live,
        head = _KOPF_BADGES.sub(lambda b: '<span class="chips mwk-chips">' + b.group(0) + '</span>', head, count=1)   # the buttons stay in line 1
    out = out[:m.start()] + head + ' mwk' + m.group(2) + _kopf_ctl(m.group(3), active) + m.group(4) + out[m.end():]
    out = out.replace("</head>", KOPF_CSS + "</head>", 1)
    tag = ("<script>window.MWK_DATA=" + json.dumps(kopf_web_data(), ensure_ascii=False).replace("</", "<\\/")
           + ";window.MWK_TX=" + json.dumps(kopf_tx(), ensure_ascii=False).replace("</", "<\\/") + ";</script>" + KOPF_JS)
    i = out.rfind("</body>")
    return out[:i] + tag + out[i:] if i >= 0 else out + tag


# ---- Pi window (Tkinter): the same buttons in the same order, the lists as chips ---------------------------------------------
def _kopf_tk(self, top):
    """the buttons on the right of the header: ? · ♪ · ↻ · DE · ☰ · ⇱ · ▲ · ⚒ (left to right, «tk» of ui_gemeinsam.json); the buttons
    of the page (✉ messages, ◷ timeline, ? manual, ◐ light / dark / red light) are in ☰"""
    tx = {b["id"]: tr(b["texts"]["en"]) for b in MWK_KOPF["knoepfe"]}
    sy = {b["id"]: b.get("tk", b["sym"]) for b in MWK_KOPF["knoepfe"]}
    ctl = tk.Frame(top, bg=C["bg"]); ctl.pack(side="right")
    self._kopf_ctl = ctl
    small = bool(self._lay[0]) and self._win_w() < MWK_KOPF.get("schmal_px", 760)
    row = []
    row.append(("help", self._ibtn(ctl, sy["help"], lambda: self._g2_tour(self.tab, True), tx["help"] + " – " + tr("Tour of this page"))))
    snd = CFG.get("siren_on") not in (False, "off", None)
    row.append(("sound", self._ibtn(ctl, sy["sound"], self._kopf_sound, tx["sound"] + " – " + tr("Loudspeaker"), on=snd)))
    row.append(("reload", self._ibtn(ctl, sy["reload"], self._kopf_reload, tx["reload"])))
    if not small:
        lb = self._ibtn(ctl, cur_lang().upper(), lambda: None, tx["lang"] + " (Ctrl+L)")
        lb.bind("<Button-1>", lambda e: self.toggle_lang(lb.winfo_rootx(), lb.winfo_rooty() + lb.winfo_height()))
        lb.config(font=("DejaVu Sans", 9, "bold")); row.append(("lang", lb))
    vb = self._ibtn(ctl, sy["menu"], lambda: None, tx["menu"])
    vb.bind("<Button-1>", lambda e: self._view_menu(vb.winfo_rootx(), vb.winfo_rooty() + vb.winfo_height()))
    row.append(("menu", vb))
    if not small:
        self.b_fs = self._ibtn(ctl, sy["fs"], self.toggle_fullscreen, tx["fs"] + " (F11)", on=self.is_fullscreen); row.append(("fs", self.b_fs))
        row.append(("fold", self._ibtn(ctl, "▼" if getattr(self, "_kopf_folded", False) else sy["fold"], self._kopf_fold, tx["fold"])))
        if kopf_dev_ok("admin"):
            row.append(("dev", self._ibtn(ctl, sy["dev"], self._kopf_dev, tx["dev"])))
    for i, (_k, b) in enumerate(row):              # left to right in the order of ui_gemeinsam.json, all the same size
        b.config(width=3); b.pack(side="left", padx=(0 if i == 0 else 6, 0))
    self._kopf_row = [k for k, _b in row]
    return ctl


def _kopf_open(self, secs):
    """Settings tab with these groups / parts open (like the long press on the logo, 639s)"""
    self.open_secs.update(secs)
    if self.tab != "settings":
        self._tab("settings")
    else:
        self._rebuild()


def _kopf_sound(self):
    """♪ sound: the window has no own alarm sound - it opens Settings → Light & sound (loudspeaker, siren), no switch changes"""
    self._kopf_open({"grp:lightsound", "sub:Loudspeaker"})


def _kopf_reload(self):
    """↻ first the tab Live, then build the window anew (like the web: Live first, then reload)"""
    self.tab = "live"
    self._rebuild()


def _kopf_fold(self):
    """▲ fold the header: tabs and status line away (one line); ▼ opens it again"""
    self._kopf_folded = not getattr(self, "_kopf_folded", False)
    self._rebuild()


def _kopf_dev(self):
    """⚒ Settings → Developer (same target as the long press on the logo, 639s)"""
    self._kopf_open({"grp:dev", "sub:Developer"})


def _kopf_overflow(self):
    """the fixed buttons that went into ☰ on a small window (from «Language» on, same order)"""
    have = set(getattr(self, "_kopf_row", []))
    tx = {b["id"]: tr(b["texts"]["en"]) for b in MWK_KOPF["knoepfe"]}
    out = []
    if "lang" not in have:
        out.append((cur_lang().upper(), tx["lang"], lambda: self.toggle_lang()))
    if "fs" not in have:
        out.append(("⇱", tx["fs"], self.toggle_fullscreen))
    if "fold" not in have:
        out.append(("▲", tx["fold"], self._kopf_fold))
    if "dev" not in have and kopf_dev_ok("admin"):
        out.append(("⚒", tx["dev"], self._kopf_dev))
    return out


def _kopf_view_menu(self, x=None, y=None):
    """☰ of the window: header buttons that did not fit, this page's buttons, general - and the lists to show / hide as chips
    in groups with symbol and «all on / off» (the same look as the web page)"""
    old = getattr(self, "_kopf_pop", None)
    if old is not None:
        try:
            old.destroy()
        except Exception:
            pass
        self._kopf_pop = None
        return
    w = tk.Toplevel(self.root); w.wm_overrideredirect(True); w.configure(bg=C["line"]); self._kopf_pop = w
    outer = tk.Frame(w, bg=C["panel"]); outer.pack(fill="both", expand=True, padx=1, pady=1)
    cv = tk.Canvas(outer, bg=C["panel"], highlightthickness=0, width=600)
    sb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview); cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
    body = tk.Frame(cv, bg=C["panel"], padx=12, pady=8); cv.create_window(0, 0, window=body, anchor="nw")

    def close(_e=None):
        try:
            w.destroy()
        except Exception:
            pass
        self._kopf_pop = None

    def h3(txt):
        tk.Label(body, text=txt.upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8, "bold")).pack(anchor="w", pady=(8, 4))

    def rows(items):
        f = tk.Frame(body, bg=C["panel"]); f.pack(fill="x")
        for i, (ic, lab, fn) in enumerate(items):
            b = tk.Label(f, text=f"{ic}  {lab}", bg=C["field"], fg=C["txt"], font=("DejaVu Sans", 10), anchor="w", padx=10, pady=6,
                         cursor="hand2", highlightthickness=1, highlightbackground=C["line"])
            b.grid(row=i // 2, column=i % 2, sticky="ew", padx=(0, 6), pady=(0, 6)); f.columnconfigure(i % 2, weight=1)
            b.bind("<Button-1>", lambda e, c=fn: (close(), c()))
    mn = {k: tr(v["en"]) for k, v in MWK_KOPF["menue"].items()}
    ov = self._kopf_overflow()
    if ov:
        h3(mn["head"]); rows(ov)
    page = [("✉", tr("Message list"), self._messages_win), ("◷", tr("Night timeline"), lambda: tk_timeline_win(self)),
            ("?", tr("Manual"), self._open_help), ("⚙", tr("Settings") + "   (Ctrl+B)", self.toggle_sidebar)]
    if self.tab == "live":
        page.append(("◫", tr("View of the live page …"), self._tkv_dialog))
    h3(mn["page"]); rows(page)
    h3(mn["general"]); rows([("◐", tr("Light / dark / red light"), self.toggle_theme), ("◉", tr("Show all"), self.show_all)])
    # the lists: the chips of the header in groups, then the panels, then the settings sections
    lists = {lid: (sym, tr(en)) for lid, sym, en in ((b["id"], b["sym"], b["texts"]["en"]) for b in MWK_KOPF["listen"])}
    grp = {lid: [] for lid in lists}
    for g, key, label in VIEW_ITEMS:
        if g == "Header":
            ic, gid = kopf_chip(key)
            grp.setdefault(gid, []).append((ic, key, label))
    blocks = [(lists[g][0], lists[g][1], grp[g]) for g in lists if grp.get(g)]
    blocks.append(("▦", tr("Panels"), [(KOPF_PANELS.get(k, "▦"), k, l) for g, k, l in VIEW_ITEMS if g == "Panels"]))
    blocks.append(("⚙", tr("Settings sections"), [("⚙", k, l) for g, k, l in VIEW_ITEMS if g == "Settings sections"]))
    h3(tr("Header") + " · " + tr("Panels") + " · " + tr("Settings"))
    grid = tk.Frame(body, bg=C["panel"]); grid.pack(fill="x")
    for n, (gic, gtitle, items) in enumerate(blocks):
        box = tk.Frame(grid, bg=C["field"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
        box.grid(row=n // 2, column=n % 2, sticky="nsew", padx=(0, 8), pady=(0, 8)); grid.columnconfigure(n % 2, weight=1, uniform="k")
        hd = tk.Frame(box, bg=C["field"]); hd.pack(fill="x")
        tk.Label(hd, text=gic, bg=C["field"], fg=C["txt"], font=("DejaVu Sans", 12)).pack(side="left")
        tk.Label(hd, text=gtitle, bg=C["field"], fg=C["txt"], font=("DejaVu Sans", 9, "bold")).pack(side="left", padx=(6, 0))
        allb = tk.Label(hd, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 8), padx=8, pady=2, cursor="hand2",
                        highlightthickness=1, highlightbackground=C["line"]); allb.pack(side="right")
        cs = tk.Frame(box, bg=C["field"]); cs.pack(fill="x", pady=(6, 0))
        chips = []

        def paint(chips=chips, allb=allb):
            for c, k in chips:
                on = self.is_shown(k)
                c.config(bg=C["acc"] if on else C["panel"], fg="#ffffff" if on else C["mut"])
            allon = all(self.is_shown(k) for _c, k in chips)
            allb.config(text=tr(MWK_KOPF["alle"]["off" if allon else "on"]["en"]))
        for i, (ic, k, lab) in enumerate(items):
            c = tk.Label(cs, text=f"{ic} {tr(lab)}", font=("DejaVu Sans", 9, "bold"), padx=8, pady=3, cursor="hand2",
                         highlightthickness=1, highlightbackground=C["line"])
            c.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 5), pady=(0, 5))
            c.bind("<Button-1>", lambda e, k=k, p=paint: (self.set_hidden(k, self.is_shown(k)), p()))
            chips.append((c, k))

        def all_(_e=None, chips=chips, paint=paint):
            v = not all(self.is_shown(k) for _c, k in chips)
            for _c, k in chips:
                if self.is_shown(k) != v:
                    self.set_hidden(k, not v)
            paint()
        allb.bind("<Button-1>", all_)
        paint()
    body.update_idletasks()
    hh = min(body.winfo_reqheight(), max(240, self.root.winfo_height() - 80))
    cv.configure(height=hh, scrollregion=(0, 0, body.winfo_reqwidth(), body.winfo_reqheight()), width=body.winfo_reqwidth())
    if x is None:
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
    wx = max(0, min(int(x) - body.winfo_reqwidth() + 40, self.root.winfo_rootx() + self.root.winfo_width() - body.winfo_reqwidth() - 20))
    w.geometry(f"+{wx}+{int(y) + 4}")
    cv.bind_all("<MouseWheel>", lambda e: cv.yview_scroll(-1 if e.delta > 0 else 1, "units") if w.winfo_exists() else None)
    w.bind("<Escape>", close); w.focus_set()
    w.bind("<FocusOut>", lambda e: w.after(150, lambda: close() if w.winfo_exists() and w.focus_get() is None else None))


App._kopf_tk = _kopf_tk
App._kopf_sound = _kopf_sound
App._kopf_reload = _kopf_reload
App._kopf_fold = _kopf_fold
App._kopf_dev = _kopf_dev
App._kopf_open = _kopf_open
App._kopf_overflow = _kopf_overflow
App._view_menu_alt = App._view_menu              # the old cascade menu (570) - everything of it is in the new ☰ too
# wraps: App._view_menu
App._view_menu = _kopf_view_menu


def _kopf_selftest():
    ids = [b["id"] for b in MWK_KOPF["knoepfe"]]
    assert ids == ["help", "sound", "reload", "lang", "menu", "fs", "fold", "dev"], "639t: order of the header buttons"
    assert MWK_KOPF["schmal_ab"] in ids, "639t: schmal_ab"
    for b in MWK_KOPF["knoepfe"] + MWK_KOPF["listen"]:
        assert all(b["texts"].get(L) for L in ("en", "de", "fr", "it", "rm")), "639t: text missing " + b["id"]
    pg = "<html><head></head><body><header><h1>MoveEye</h1><!--NAV--><span class=\"hdr-ctl\">\n<button class=\"sec\" onclick=\"window.print()\" title=\"Print\">🖨</button>\n" \
         "<button class=\"sec\" id=\"btn-theme\">x</button><button class=\"sec\" id=\"btn-lang\">DE</button>\n</span>\n</header><main></main></body></html>"
    p = render_page(pg, "rec")
    assert 'class="hdr-ctl mwk"' in p and 'id="mwk-help"' in p and 'id="mwk-menu-btn"' in p and 'id="mwk-fs"' in p, "639t: fixed buttons missing"
    assert p.count('id="mwk-css"') == 1 and "window.MWK_DATA=" in p and "🖨" in p, "639t: page button lost"
    m = render_page(WEB_PAGE, "live")
    assert 'id="mwk-menu-btn"' not in m and 'id="btn-view"' in m and 'id="mwk-fs"' not in m, "639t: main page keeps its ☰ and ⛶"
    assert "mwbar" in p, "639t: the bar of 639o stays"
    for k, (de, fr, it, rm) in _HX_KOPF.items():
        assert DE.get(k) and TRX["fr"].get(k) and TRX["it"].get(k) and TRX["rm"].get(k), "639t: text missing: " + k
    keep = {k: CFG.get(k) for k in ("dev_area", "lock_on")}
    try:
        CFG["dev_area"] = False
        assert 'id="mwk-dev"' not in render_page(pg, "rec"), "639t: 🛠 without the developer area"
        CFG["dev_area"] = True; CFG["lock_on"] = False
        assert 'id="mwk-dev"' in render_page(pg, "rec") and not kopf_dev_ok("view"), "639t: 🛠 only for the owner"
    finally:
        CFG.update(keep)
    for g, k, _l in VIEW_ITEMS:
        if g == "Header":
            assert kopf_chip(k)[0] != "•", "639t: no symbol for " + k
    return "%d buttons, %d list groups" % (len(ids), len(MWK_KOPF["listen"]))


SELFTEST_EXTRA.append(("One header (639t)", _kopf_selftest))
