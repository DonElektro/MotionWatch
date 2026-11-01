#@ MoveEye – Teil 639q: Schalter aufräumen (Daniel 01.11.2026, review_schalter): Test-Postfach in der Simulation immer an, Simulation immer mit eigenen Einstellungen, Anmelden immer verschlüsselt (vom Gerät selbst weiter ohne https), «Auch nicht signierte Versionen annehmen» nur im Entwickler-Bereich und nach 24 h von selbst aus. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entfernt (nur diese Schalter, die Funktion bleibt immer an):
#   * notify_sandbox  -> sandbox_active() (141) ist in der Simulation immer wahr; Info-Meldungen gehen mit sim_info_push
#                        oder bei echten Pi-Warnungen weiter aufs Handy (sandbox_lets_through, 141 / 060)
#   * sim_separate    -> simprof_on / simprof_off (340) immer
#   * login_https_only-> seclogin_mode (574) immer «on» (oder «fallback» ohne https-Seite, nie ausgesperrt)
# Ein gespeicherter alter Wert dieser Schlüssel wird beim Laden still übergangen (apply_settings kennt sie nicht mehr).
# update_unsigned: Abschnitt «Developer» (639c _MENU_MOVES), Ablauf in update_unsigned_ok (380), Zeit update_unsigned_t (020).
# ----------------------------------------------------------------------------
_HX_SCHALTER = {
    "Only for your own builds: MoveEye also installs versions without the developer's signature. Switches itself off after 24 hours.":
        ("Nur für eigene Fassungen: MoveEye installiert auch Versionen ohne die Signatur des Entwicklers. Schaltet sich nach 24 Stunden selbst aus.",
         "Uniquement pour vos propres versions : MoveEye installe aussi des versions sans la signature du développeur. Se désactive tout seul après 24 heures.",
         "Solo per versioni proprie: MoveEye installa anche versioni senza la firma dello sviluppatore. Si spegne da solo dopo 24 ore.",
         "Mo per atgnas versiuns: MoveEye installescha er versiuns senza la signatura dal sviluppader. Sa stizza sez suenter 24 uras."),
    "Off.": ("Aus.", "Désactivé.", "Spento.", "Stizzà."),
    "Unsigned versions: switched off by itself after 24 hours":
        ("Nicht signierte Versionen: nach 24 Stunden von selbst ausgeschaltet",
         "Versions non signées : désactivé tout seul après 24 heures",
         "Versioni non firmate: spento da solo dopo 24 ore",
         "Versiuns betg signadas: stizzà sez suenter 24 uras"),
}
for _k, _v in _HX_SCHALTER.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

SET_HELP["update_unsigned"] = ("Only for your own builds: MoveEye also installs versions without the developer's signature. Switches itself off after 24 hours.",
                               "Off.")


# ---- 3.23 Schritt 2 -------------------------------------------------------------------------------------------------------
# * Updates (Daniel: «4 Schalter werden zu einer Auswahl wie im Simulator»): update_mode off | auto | dev statt update_auto /
#   update_install / update_fast / update_install_armed (MIGRATE_ONLY, 020). Alte Dateien: update_fast -> dev, update_install -> auto,
#   sonst off. «auto» installiert nur bei «Aus» (das alte «auch bei Schutz an» = update_install_armed fällt weg; dev tut es immer).
# * «Bewegung reduzieren» (reduce_motion auto | on | off, Gerät & Hilfe): Logo, Radar-Symbol, Blinki, Status-LED-Blinki im Web;
#   auto folgt dem Betriebssystem (prefers-reduced-motion), on / off überschreiben es (render_page unten, html.mwrm / html.mwrm0).
# * «Stimme» (voice_mode on | off | subtitles, Licht & Ton → Lautsprecher): die Stimme im Browser (Trailer, Vorführung,
#   Almanach, Spiele). Die Ansage beim Einschalten und «Gesundheit!» sind Lautsprecher-Funktionen und bleiben eigene Schalter.
# * Rundgang, Tipp des Tages, Blinki: nur noch unter Einstellungen → System → Gerät & Hilfe; Einrichtung, Hilfe-Karte, Tipp-
#   Fenster (Web 516, Fenster 585) zeigen einen Link dorthin.
TEXTS.extend([
    ("Updates", "update_mode", "New versions", "enum", "update_modes"),
    ("Device & help", "reduce_motion", "Reduce motion (logo, radar, Blinki)", "enum", "reduce_motion"),
    ("Loudspeaker", "voice_mode", "Voice (narrator, demo, trailer, browser)", "enum", "voice_modes"),
])
TEXT_SPECS.update({k: (kind, extra) for s, k, l, kind, extra in TEXTS if k in ("update_mode", "reduce_motion", "voice_mode")})
SIMPLE_KEYS.update({"update_mode", "reduce_motion", "voice_mode"})
UPDATE_MODES = (("off", "only by hand: look and report, install with the button"),
                ("auto", "install automatically (in the update hour, when the protection is off)"),
                ("dev", "development phase: every minute, at once (also while protected)"))
REDUCE_MOTION = (("auto", "like the operating system"), ("on", "on: still pictures"), ("off", "off: everything moves"))
VOICE_MODES = (("on", "on"), ("off", "off"), ("subtitles", "only subtitles"))
SET_HELP.update({
    "update_mode": ("«Only by hand»: MoveEye looks every 3 hours and reports a new version; you install it with «Update now». «Automatically»: "
                    "in the update hour, only while the protection is off. «Development phase»: looks every minute and installs at once. Like the simulator.",
                    "Automatically."),
    "reduce_motion": ("Less movement on the pages: the walking person of the logo, the radar symbol and Blinki stand still. «Like the operating "
                      "system» follows the setting of the phone or PC (reduce motion / animations).", "Like the operating system."),
    "voice_mode": ("One switch for the voice: the narrator of the trailers and the demo, the almanac and the games in the browser. «Only "
                   "subtitles» shows the text without speaking.", "On."),
})
_HX_SCHALTER2 = {
    "New versions": ("Neue Versionen", "Nouvelles versions", "Nuove versioni", "Novas versiuns"),
    "only by hand: look and report, install with the button":
        ("nur von Hand: nachschauen und melden, installieren mit dem Knopf", "seulement à la main : chercher et signaler, installer avec le bouton",
         "solo a mano: cercare e segnalare, installare con il pulsante", "mo a maun: tschertgar ed annunziar, installar cun il buttun"),
    "install automatically (in the update hour, when the protection is off)":
        ("automatisch installieren (in der Update-Stunde, wenn der Schutz aus ist)", "installer automatiquement (à l’heure des mises à jour, protection désactivée)",
         "installare automaticamente (nell’ora degli aggiornamenti, con la protezione spenta)", "installar automaticamain (en l’ura d’actualisaziun, cura che la protecziun è stizzada)"),
    "development phase: every minute, at once (also while protected)":
        ("Entwicklungsphase: jede Minute, sofort (auch bei Schutz an)", "phase de développement : chaque minute, tout de suite (aussi sous protection)",
         "fase di sviluppo: ogni minuto, subito (anche con la protezione attiva)", "fasa da svilup: mintga minuta, immediat (er cun protecziun)"),
    "Reduce motion (logo, radar, Blinki)": ("Bewegung reduzieren (Logo, Radar, Blinki)", "Réduire les animations (logo, radar, Blinki)",
                                            "Ridurre il movimento (logo, radar, Blinki)", "Reducir il moviment (logo, radar, Blinki)"),
    "like the operating system": ("wie das Betriebssystem", "comme le système", "come il sistema operativo", "sco il sistem operativ"),
    "on: still pictures": ("an: ruhige Bilder", "activé : images fixes", "attivo: immagini ferme", "activà: maletgs quiets"),
    "off: everything moves": ("aus: alles bewegt sich", "désactivé : tout bouge", "spento: tutto si muove", "stizzà: tut sa mova"),
    "Voice (narrator, demo, trailer, browser)": ("Stimme (Erzähler, Vorführung, Trailer, Browser)", "Voix (narrateur, démonstration, bande-annonce, navigateur)",
                                                 "Voce (narratore, dimostrazione, trailer, browser)", "Vusch (narratur, preschentaziun, trailer, navigatur)"),
    "only subtitles": ("nur Untertitel", "seulement les sous-titres", "solo sottotitoli", "mo sutitels"),
    "⚙ Tour, tip of the day, Blinki: Settings → System → Device & help":
        ("⚙ Rundgang, Tipp des Tages, Blinki: Einstellungen → System → Gerät & Hilfe", "⚙ Visite, astuce du jour, Blinki : Réglages → Système → Appareil et aide",
         "⚙ Tour, consiglio del giorno, Blinki: Impostazioni → Sistema → Dispositivo e aiuto", "⚙ Gir, cussegl dal di, Blinki: Parameters → Sistem → Apparat & agid"),
    SET_HELP["update_mode"][0]:
        ("«Nur von Hand»: MoveEye schaut alle 3 Stunden nach und meldet eine neue Version; installiert wird mit «Jetzt aktualisieren». «Automatisch»: "
         "in der Update-Stunde, nur wenn der Schutz aus ist. «Entwicklungsphase»: schaut jede Minute nach und installiert sofort. Wie im Simulator.",
         "«Seulement à la main» : MoveEye cherche toutes les 3 heures et signale une nouvelle version ; vous l’installez avec «Mettre à jour». «Automatiquement» : "
         "à l’heure des mises à jour, seulement protection désactivée. «Phase de développement» : cherche chaque minute et installe tout de suite. Comme le simulateur.",
         "«Solo a mano»: MoveEye controlla ogni 3 ore e segnala una nuova versione; la installi con «Aggiorna ora». «Automaticamente»: "
         "nell’ora degli aggiornamenti, solo con la protezione spenta. «Fase di sviluppo»: controlla ogni minuto e installa subito. Come il simulatore.",
         "«Mo a maun»: MoveEye tschertga mintga 3 uras ed annunzia ina nova versiun; ti l’installeschas cun «Actualisar ussa». «Automaticamain»: "
         "en l’ura d’actualisaziun, mo cura che la protecziun è stizzada. «Fasa da svilup»: tschertga mintga minuta ed installescha immediat. Sco il simulatur."),
    "Automatically.": ("Automatisch.", "Automatiquement.", "Automaticamente.", "Automaticamain."),
    SET_HELP["reduce_motion"][0]:
        ("Weniger Bewegung auf den Seiten: die gehende Person im Logo, das Radar-Symbol und Blinki stehen still. «Wie das Betriebssystem» "
         "folgt der Einstellung des Handys oder PCs (Bewegung / Animationen reduzieren).",
         "Moins de mouvement sur les pages : la personne qui marche du logo, le symbole radar et Blinki restent immobiles. «Comme le système» "
         "suit le réglage du téléphone ou du PC (réduire les animations).",
         "Meno movimento nelle pagine: la persona che cammina nel logo, il simbolo radar e Blinki stanno fermi. «Come il sistema operativo» "
         "segue l’impostazione del telefono o del PC (ridurre il movimento / le animazioni).",
         "Main moviment sin las paginas: la persuna che chamina en il logo, il simbol radar e Blinki stattan quiet. «Sco il sistem operativ» "
         "suonda il parameter dal telefonin u dal PC (reducir moviment / animaziuns)."),
    "Like the operating system.": ("Wie das Betriebssystem.", "Comme le système.", "Come il sistema operativo.", "Sco il sistem operativ."),
    SET_HELP["voice_mode"][0]:
        ("Ein Schalter für die Stimme: der Erzähler der Trailer und der Vorführung, der Almanach und die Spiele im Browser. «Nur Untertitel» "
         "zeigt den Text, ohne zu sprechen.",
         "Un seul réglage pour la voix : le narrateur des bandes-annonces et de la démonstration, l’almanach et les jeux dans le navigateur. «Seulement les sous-titres» "
         "affiche le texte sans parler.",
         "Un solo interruttore per la voce: il narratore dei trailer e della dimostrazione, l’almanacco e i giochi nel browser. «Solo sottotitoli» "
         "mostra il testo senza parlare.",
         "In sulet interruptur per la vusch: il narratur dals trailers e da la preschentaziun, l’almanac ed ils gieus en il navigatur. «Mo sutitels» "
         "mussa il text senza discurrer."),
    "On.": ("An.", "Activé.", "Attivo.", "Activà."),
}
for _k, _v in _HX_SCHALTER2.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
G2_UI.append("⚙ Tour, tip of the day, Blinki: Settings → System → Device & help")

_text_choice_pairs_639q = text_choice_pairs


# wraps: text_choice_pairs
def text_choice_pairs(key):                               # + 639q: updates, reduce motion, voice
    extra = (TEXT_SPECS.get(key) or (None, None))[1]
    if extra == "update_modes":
        return [(k, tr(l)) for k, l in UPDATE_MODES]
    if extra == "reduce_motion":
        return [(k, tr(l)) for k, l in REDUCE_MOTION]
    if extra == "voice_modes":
        return [(k, tr(l)) for k, l in VOICE_MODES]
    return _text_choice_pairs_639q(key)


def update_mode_migrate(cfg_in):
    """an older file with the four update switches -> update_mode (only when the file has no update_mode yet)"""
    for k in ("update_auto", "update_install", "update_fast", "update_install_armed"):
        CFG.pop(k, None)
    if not isinstance(cfg_in, dict) or "update_mode" in cfg_in:
        return ""
    if not any(k in cfg_in for k in ("update_auto", "update_install", "update_fast", "update_install_armed")):
        return ""
    m = "dev" if cfg_in.get("update_fast") is True else "auto" if cfg_in.get("update_install") is True else "off"
    CFG["update_mode"] = m
    return m


_settings_migrations_before_639q = _settings_migrations


# wraps: _settings_migrations
def _settings_migrations(cfg_in):                         # + 639q (3.23): the four update switches -> update_mode
    _settings_migrations_before_639q(cfg_in)
    try:
        m = update_mode_migrate(cfg_in)
        if m:
            log_event("sys", f"Settings of an older version taken over: updates «{m}»")
    except Exception as e:
        log_event("sys", f"Settings migration (639q): {e}"[:150])


# ---- web: reduce motion and the voice on every page ------------------------------------------------------------------------
_RM_BLOCK = re.compile(r"@media \(prefers-reduced-motion:\s*reduce\)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}")


def rm_css(css):
    """every «@media (prefers-reduced-motion:reduce){…}»: only when not switched off (html.mwrm0), and the same rules with
    html.mwrm (switched on, or «auto» and the system says so - set by the script in the head)"""
    def one(m):
        body = m.group(1)
        if "mwrm" in body:
            return m.group(0)
        rules = re.findall(r"([^{}]+)\{([^{}]*)\}", body)
        pre = lambda p: ",".join(p + " " + x.strip() for x in sel.split(",") if x.strip())
        a, b = [], []
        for sel, decl in rules:
            a.append(pre("html:not(.mwrm0)") + "{" + decl + "}")
            b.append(pre("html.mwrm") + "{" + decl + "}")
        return "@media (prefers-reduced-motion:reduce){" + "".join(a) + "}" + "".join(b)
    return _RM_BLOCK.sub(one, css)


try:
    BLINKI_CSS = rm_css(BLINKI_CSS)                       # 589: Blinki comes with /g2/ui.js, not in the page
except NameError:
    pass


def motion_head():
    m = str(CFG.get("reduce_motion") or "auto")
    m = m if m in ("auto", "on", "off") else "auto"
    v = str(CFG.get("voice_mode") or "on")
    v = v if v in ("on", "off", "subtitles") else "on"
    js = ("(function(){var m=%s,d=document.documentElement,r=m==='on';try{if(m==='auto')r=matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){}"
          "d.classList.toggle('mwrm',r);d.classList.toggle('mwrm0',m==='off');window.MW_MOTION=r?'reduce':'full';window.MW_VOICE=%s;})();") % (json.dumps(m), json.dumps(v))
    css = ("html.mwrm header h1::before{background-image:url(/icon-192.png?i=%s)!important}"
           "html.mwrm header h1.wm *{animation:none!important}html.mwrm header h1.wm .wmp{transform:none!important}") % app_icon_id()
    return "<script>" + js + "</script><style>" + css + "</style>"


_render_page_before_639q = render_page


# wraps: render_page
def render_page(page, active):
    """+ 639q: «Reduce motion» (class on <html> before anything is drawn) and the voice setting for the speaking pages"""
    out = _render_page_before_639q(page, active)
    if "prefers-reduced-motion" in out:
        out = rm_css(out)
    return out.replace("<head>", "<head>" + motion_head(), 1) if "<head>" in out else motion_head() + out


def voice_say_ok():
    """the browser may speak (voice_mode «on»)"""
    return str(CFG.get("voice_mode") or "on") == "on"


def schalter_selftest():
    """the removed switches stay removed, the functions are always on, unsigned versions expire after 24 hours"""
    lists = {x[1] for x in TOGGLES + SLIDERS + TEXTS}
    for k in ("notify_sandbox", "sim_separate", "login_https_only"):
        assert k not in CFG and k not in lists, f"{k} is back"
    assert any(x[1] == "update_unsigned" and x[0] == "Developer" for x in TOGGLES), "update_unsigned not in the developer section"
    keep = {k: CFG.get(k) for k in ("sim_on", "update_unsigned", "update_unsigned_t")}
    G = globals(); keep_save = G["save_settings"]; keep_log = G["log_event"]
    try:
        G["save_settings"] = lambda *a, **k: None; G["log_event"] = lambda *a, **k: None
        CFG["sim_on"] = True
        assert sandbox_active(), "test inbox not on in the simulation"
        CFG.update(update_unsigned=True, update_unsigned_t=0.0)
        assert update_unsigned_ok() and CFG["update_unsigned_t"] > 0, "time not started"
        CFG["update_unsigned_t"] = time.time() - 25 * 3600
        assert not update_unsigned_ok() and not CFG["update_unsigned"], "not switched off after 24 h"
    finally:
        G["save_settings"] = keep_save; G["log_event"] = keep_log
        CFG.update(keep)
    for k in ("update_auto", "update_install", "update_fast", "update_install_armed", "sim_basis_show"):
        assert k not in CFG and k not in lists, f"{k} is back"
    keep2 = CFG.get("update_mode")
    try:
        assert update_mode_migrate({"update_auto": True, "update_install": True}) == "auto" and CFG["update_mode"] == "auto"
        assert update_mode_migrate({"update_fast": True, "update_install": True}) == "dev"
        assert update_mode_migrate({"update_auto": False}) == "off"
        assert update_mode_migrate({"update_mode": "auto", "update_fast": True}) == "" and CFG["update_mode"] == "off"
    finally:
        CFG["update_mode"] = keep2
    assert [c for c, _ in text_choice_pairs("update_mode")] == ["off", "auto", "dev"]
    css = rm_css("@media (prefers-reduced-motion:reduce){.bk *,.bk.hop .bk-all{animation:none}#x{transition:none}}")
    assert "html:not(.mwrm0) .bk *" in css and "html.mwrm .bk.hop .bk-all{animation:none}" in css and "html.mwrm #x" in css, css
    assert rm_css(css) == css, "not twice"
    pg = render_page("<html><head></head><body><header><h1>MoveEye</h1></header></body></html>", "live")
    assert "mwrm" in pg and "MW_VOICE" in pg and "SIM_ZIP_B64" not in globals()
    return ("test inbox always on in the simulation, login always encrypted, unsigned versions 24 h, updates one choice, "
            "reduce motion + voice on the pages, no basic simulator")


SELFTEST_EXTRA.append(("Switches tidied up (639q)", schalter_selftest))
