#@ MoveEye – Teil 639zc: Links zu Neuerungen – im Fenster «Neu in …» bei jeder Neuerung ein kleiner Link zur Funktion (Seite, Reiter, Einstellung), Schalter «Links zu Neuerungen» im Entwickler-Bereich, Standard aus dem Projektschalter «projekt_veroeffentlicht». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (01.11.2026): nach einem Update zeigt MoveEye «Neu in …» - neu steht bei jeder Neuerung ein Link, der direkt
# zur neuen Funktion springt. Gilt genauso im Simulator (scripts/news.gd).
#   * Die Ziele: simulator3d/ui_gemeinsam.json «neu_ziele» (Version -> Ziel, für beide Programme). Logik in Teil 137
#     (news_links_on, news_href, news_link_item); Web 530 (newsGo, keyOpen: /settings?setting=<Einstellung> klappt die Karte
#     auf und hebt die Zeile kurz hervor), Pi-Fenster 570 (öffnet die Seite im Browser).
#   * Schalter «Links zu Neuerungen» = news_links auto | on | off, nur im Entwickler-Bereich (Abschnitt «Developer»),
#     mit dem Simulator geteilt (ui_gemeinsam.json «shared» / «sync», Teil 639zb).
#   * «auto» (Standard): Projektschalter «projekt_veroeffentlicht» in ui_gemeinsam.json - false (Entwicklung) = Links an,
#     true (veröffentlicht) = aus. Beim Release umlegen (CLAUDE.md, Abschnitt Release).
# ----------------------------------------------------------------------------
CFG.setdefault("news_links", "auto"); DEFAULTS.setdefault("news_links", "auto")
FACTORY_CFG.setdefault("news_links", "auto")                 # 636 took its copy before this part
TEXTS.append(("Developer", "news_links", "Links to what is new", "enum", "news_links"))
TEXT_SPECS["news_links"] = ("enum", "news_links")
NEWS_LINK_MODES = (("auto", "default (on until the project is published)"), ("on", "on"), ("off", "off"))
SET_HELP["news_links"] = ("In the window «New in …» after an update: a small link at every novelty that jumps straight to it "
                          "(page, tab or setting). «Default» follows the project: on during development, off once it is published. "
                          "Shared with the simulator.", "Default.")

_HX_NEWSLINKS = {
    "Links to what is new": ("Links zu Neuerungen", "Liens vers les nouveautés", "Link alle novità", "Links a las novitads"),
    "default (on until the project is published)": ("Standard (an, bis das Projekt veröffentlicht ist)",
                                                    "par défaut (activé tant que le projet n’est pas publié)",
                                                    "predefinito (attivo finché il progetto non è pubblicato)",
                                                    "standard (activà fin ch’il project è publitgà)"),
    SET_HELP["news_links"][0]:
        ("Im Fenster «Neu in …» nach einem Update: bei jeder Neuerung ein kleiner Link, der direkt dorthin springt (Seite, Reiter "
         "oder Einstellung). «Standard» folgt dem Projekt: während der Entwicklung an, nach dem Veröffentlichen aus. Mit dem "
         "Simulator geteilt.",
         "Dans la fenêtre «Nouveau dans …» après une mise à jour : un petit lien à chaque nouveauté qui y mène directement (page, "
         "onglet ou réglage). «Par défaut» suit le projet : activé pendant le développement, désactivé après la publication. "
         "Partagé avec le simulateur.",
         "Nella finestra «Novità in …» dopo un aggiornamento: per ogni novità un piccolo link che porta direttamente lì (pagina, "
         "scheda o impostazione). «Predefinito» segue il progetto: attivo durante lo sviluppo, spento dopo la pubblicazione. "
         "Condiviso con il simulatore.",
         "En la fanestra «Nov en …» suenter in'actualisaziun: tar mintga novitad in pitschen link che maina directamain là (pagina, "
         "register u parameter). «Standard» suonda il project: activà durant il svilup, stizzà suenter la publicaziun. "
         "Partì cun il simulatur."),
    "Default.": ("Standard.", "Par défaut.", "Predefinito.", "Standard."),
}
for _k, _v in _HX_NEWSLINKS.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

_text_choice_pairs_639zc = text_choice_pairs


# wraps: text_choice_pairs
def text_choice_pairs(key):                               # + 639zc: «Links zu Neuerungen»
    if (TEXT_SPECS.get(key) or (None, None))[1] == "news_links":
        return [(k, tr(l)) for k, l in NEWS_LINK_MODES]
    return _text_choice_pairs_639zc(key)


def news_links_selftest():
    """targets of ui_gemeinsam.json «neu_ziele» are valid, the links follow the project switch and the own choice"""
    U = UI_GEMEINSAM
    assert isinstance(U.get("projekt_veroeffentlicht"), bool), "639zc: ui_gemeinsam.json «projekt_veroeffentlicht» (true / false)"
    zs = U.get("neu_ziele") or {}
    assert zs, "639zc: ui_gemeinsam.json «neu_ziele» empty"
    known = {k for lst in (TOGGLES, SLIDERS, TEXTS) for _s, k, *_r in lst}
    secs = set(SECTIONS)
    allowed = {"seite", "anker", "einstellung", "sim_einstellung", "sim_menue", "sim_aktion"}
    for v, z in zs.items():
        assert re.match(r"^\d+\.\d+\.\d+$", v) and isinstance(z, dict) and z and set(z) <= allowed, f"639zc: target of {v}: {z}"
        if z.get("einstellung"):
            assert z["einstellung"] in known, f"639zc: {v}: unknown setting {z['einstellung']}"
        a = str(z.get("anker") or "")
        if a.startswith("sec:"):
            assert a[4:] in secs, f"639zc: {v}: unknown section {a}"
        if z.get("seite"):
            assert str(z["seite"]).startswith("/"), f"639zc: {v}: page must start with /"
        if z.get("sim_aktion"):
            assert isinstance(z["sim_aktion"], dict) and z["sim_aktion"].get("action"), f"639zc: {v}: sim_aktion needs «action»"
    keep = CFG.get("news_links"), U.get("projekt_veroeffentlicht")
    try:
        CFG["news_links"] = "auto"; U["projekt_veroeffentlicht"] = False
        assert news_links_on(), "639zc: not published -> links on"
        U["projekt_veroeffentlicht"] = True
        assert not news_links_on(), "639zc: published -> links off"
        CFG["news_links"] = "on"
        assert news_links_on(), "639zc: own choice must win"
        it = news_link_item({"v": "3.30.0", "t": "x"})
        assert it.get("href") == "/settings?setting=dev_area", f"639zc: href {it}"
        assert news_link_item({"v": "3.37.0", "t": "x"}).get("where") == "sim", "639zc: only in the simulator"
        assert news_href({"anker": "sec:Backup"}) == "/settings?open=sec%3ABackup" and news_href({"seite": "/case"}) == "/case"
        CFG["news_links"] = "off"
        assert "href" not in news_link_item({"v": "3.30.0", "t": "x"}), "639zc: switched off -> no link"
        assert [k for k, _l in text_choice_pairs("news_links")] == ["auto", "on", "off"], "639zc: choices"
        assert tr("Links to what is new", "fr") != "Links to what is new" and news_hint("neu_link", "de") == "Zur Funktion ›"
        assert any(x[1] == "news_links" and x[0] == "Developer" for x in TEXTS), "639zc: only in the developer area"
        js = WEB_PAGE if isinstance(globals().get("WEB_PAGE"), str) else ""
        assert not js or ("newsGo(" in js and "keyOpen(" in js), "639zc: web page without newsGo / keyOpen"
    finally:
        CFG["news_links"] = keep[0]; U["projekt_veroeffentlicht"] = keep[1]
    return f"{len(zs)} targets, default {'off' if U.get('projekt_veroeffentlicht') else 'on'} (projekt_veroeffentlicht = {str(U.get('projekt_veroeffentlicht')).lower()})"


SELFTEST_EXTRA.append(("Links to what is new («Neu in …», ui_gemeinsam.json «neu_ziele», 639zc)", news_links_selftest))
