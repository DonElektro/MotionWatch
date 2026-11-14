#@ MoveEye – Teil 639zzzb: Design «Klar», Etappe 1 (Besitzer 13.11.2026) – Texte der Etappe in fünf Sprachen, «Mehr» in vier Gruppen (Unterwegs · Spielen · Hilfe & Drucken · Gerät), Statuszeile im Live-Bild übersetzt. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer (13.11.2026): «Das Design wirkt auf einigen Seiten sehr unübersichtlich» -> Richtung A «Klar», in Etappen. Etappe 1 =
# die Schnellgewinne aus dem Vorschlag (scratchpad design/): die Bausteine selbst sind in ihren Teilen geändert (639o Leiste und
# Statuszeile, 144 Schriftzug, 639t Kopf 44 px, 450 / 530 Überschriften und Zustand als Wort, 536 Live-Knöpfe mit Namen, 515 / 516
# Karten in der Seite, 540 Verlauf «Filter», 520 / 639zzc / 639zzw / 639zzx eine Leiste für die Gäste-Seiten, 572 / 570 Fenster).
# Hier: was mehrere Teile brauchen und was neu ist:
#   * _HX_KLAR: die neuen Texte (Englisch = Schlüssel; Deutsch, Französisch, Italienisch, Rätoromanisch).
#   * more_grouped(): die Seite «Mehr» (525) in vier Gruppen; die Einträge, die andere Teile einfügen (Karte, Morse,
#     Karten-Werkstatt, QR-Codes, Rucksack, Bauen, Spielecke …), finden ihren Platz über die Adresse. Unbekanntes kommt ans Ende
#     von «Gerät». «Einrichtung» und «Werkseinstellungen» stehen unter Einstellungen → System (530, Besitzer: verschieben ok).
#   * hud_tr(): die Zeile oben im Kamerabild (410: «No rain | Wind … | Persons …») in der Sprache des Geräts - nur ASCII, weil
#     OpenCV keine Umlaute zeichnen kann (ä -> ae, é -> e).
# ----------------------------------------------------------------------------
import unicodedata as _ud

# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_KLAR = {
    "On the go": ("Unterwegs", "En route", "In viaggio", "Sin viadi"),
    "Help & print": ("Hilfe & Drucken", "Aide et impression", "Aiuto e stampa", "Agid e stampar"),
    "Device": ("Gerät", "Appareil", "Apparecchio", "Apparat"),
    "Play area": ("Spielen", "Jouer", "Giocare", "Giugar"),
    "Games": ("Spiele", "Jeux", "Giochi", "Gieus"),
    "Digital backpack": ("Digitaler Rucksack", "Sac à dos numérique", "Zaino digitale", "Satgados digital"),   # the guest page (639zzc, g_ by English)
    "Game collection, game corner, open the games for guests": (
        "Spielesammlung, Spielecke, Spiele für Gäste freigeben", "Collection de jeux, coin jeux, ouvrir les jeux aux invités",
        "Raccolta di giochi, angolo giochi, aprire i giochi agli ospiti", "Collecziun da gieus, chantun da gieus, avrir ils gieus per giasts"),
    "Setup, tours and factory settings: Settings › System": (
        "Einrichtung, Rundgänge und Werkseinstellungen: Einstellungen › System", "Configuration, visites et réglages d’usine : Réglages › Système",
        "Configurazione, giri e impostazioni di fabbrica: Impostazioni › Sistema", "Configuraziun, visitas e parameters da fabrica: Parameters › Sistem"),
    "Setup & factory settings": ("Einrichtung & Werkseinstellungen", "Configuration et réglages d’usine", "Configurazione e impostazioni di fabbrica",
                                 "Configuraziun e parameters da fabrica"),
    "Only to look at (no download)": ("Nur ansehen (kein Download)", "Seulement à regarder (pas de téléchargement)", "Solo da guardare (nessun download)",
                                      "Mo per guardar (nagin download)"),
    "Filter": ("Filter", "Filtre", "Filtro", "Filter"),
    "No recordings yet. MoveEye records as soon as it detects something.": (
        "Noch keine Aufnahmen. MoveEye nimmt auf, sobald es etwas erkennt.", "Pas encore d’enregistrements. MoveEye enregistre dès qu’il détecte quelque chose.",
        "Ancora nessuna registrazione. MoveEye registra appena rileva qualcosa.", "Anc naginas registraziuns. MoveEye registrescha uschespert ch’el identifitgescha insatge."),
    "MANUAL": ("MANUELL", "MANUEL", "MANUALE", "MANUAL"),
    "TIMELAPSE": ("ZEITRAFFER", "ACCÉLÉRÉ", "TIMELAPSE", "ACCELERÀ"),
    "Pan": ("Schwenk", "Pan", "Pan", "Pan"),
    "Tilt": ("Neigung", "Tilt", "Tilt", "Tilt"),
}
for _k, _v in _HX_KLAR.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the German of the page «Mehr» (its own list, 525 more_page)
MORE_GROUPS_DE = {k: DE.get(k, _HX_KLAR[k][0]) for k in ("On the go", "Help & print", "Device", "Play area", "Games",
                                                        "Game collection, game corner, open the games for guests",
                                                        "Setup, tours and factory settings: Settings › System")}

# ---- «Mehr» in four groups ----------------------------------------------------------------------------------------------------------
# (id, English title, the marks of the entries in this group in their order)
MORE_GROUPS = (
    ("travel", "On the go", ('href="/tausch"', 'href="/karte"', 'href="/almanach"', 'href="/morse"')),
    ("play", "Play area", ('href="/play"', 'href="/party"')),
    ("help", "Help & print", ('href="/help"', 'href="/quick"', 'href="/qr"', 'href="/karten"', 'href="/info"')),
    ("device", "Device", ('href="/tools"', 'href="/build"', 'id="m-fb"', 'id="m-about"')),
)
_MG_ITEM_RE = re.compile(r'[ \t]*<(a|button)\b[^>]*\bclass="mi"[^>]*>.*?</\1>[ \t]*\n?', re.S)
_MG_SCRIPT_RE = re.compile(r'[ \t]*<script\b[^>]*>.*?</script>[ \t]*\n?', re.S)
MORE_PLAY_ITEM = ('  <a class="mi" href="/play" id="m-play"><i>⭐</i><span><b data-i18n="Games">Games</b>'
                  '<small data-i18n="Game collection, game corner, open the games for guests">Game collection, game corner, open the games for guests</small>'
                  '</span><span class="ar">›</span></a>\n')
MORE_GROUP_CSS = r"""<style id="mg-css">
/* 3.88 (Klar stage 1): «Mehr» in four groups - a heading, then one card with rows; «Unterwegs» as tiles */
.mg{margin:20px 0 0}.mg:first-of-type{margin-top:8px}
.mgh{font-size:17px;font-weight:700;margin:0 4px 8px;letter-spacing:0;text-transform:none;color:var(--txt)}
.mgl{border:1px solid var(--line);border-radius:14px;background:var(--panel);overflow:hidden}
.mgl>.mi{margin:0!important;border:0!important;border-radius:0!important;background:transparent!important;min-height:58px;box-shadow:none}
.mgl>.mi:not([hidden])~.mi{border-top:1px solid var(--line)!important}
/* wide screens: «Unterwegs» as four tiles; phones: rows like the other groups (long names - fr «Sac à dos numérique» - stay on one line) */
@media(min-width:700px){.mg-travel .mgl{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;border:0;background:none;overflow:visible}
  .mg-travel .mgl>.mi{flex-direction:column;align-items:flex-start;gap:8px;min-height:112px;padding:14px!important;border:1px solid var(--line)!important;
    border-radius:14px!important;background:var(--panel)!important}
  .mg-travel .mgl>.mi .ar{display:none}.mg-travel .mgl>.mi b{font-size:15px;overflow-wrap:anywhere;hyphens:auto}}
.mg-hint{margin:18px 4px 6px;font-size:13px;color:var(--mut)}.mg-hint a{color:var(--acc2);text-decoration:none;font-weight:600}
</style>"""
MORE_GROUP_JS = """<script>(function () {                    // a group whose entries are all hidden (rights, switched off) is hidden too
  const go = () => document.querySelectorAll("main .mg").forEach(g => { g.hidden = ![...g.querySelectorAll(".mi")].some(x => !x.hidden); });
  go(); [600, 2000, 5000].forEach(ms => setTimeout(go, ms));
  new MutationObserver(go).observe(document.querySelector("main") || document.body, {subtree: true, attributes: true, attributeFilter: ["hidden"]});
})();</script>"""


def more_grouped(html):
    """the page «Mehr»: the entries (a.mi / button.mi) of <main> in the four groups of MORE_GROUPS; the rest of <main> (Tipps &
    Tricks) stays on top, the scripts that were between the entries go to the end of <main>"""
    i = html.find("<main>")
    j = html.find("</main>", i)
    if i < 0 or j < 0:
        return html
    body = html[i + 6:j]
    if 'href="/play"' not in body and 'class="mi"' in body:
        body = body + MORE_PLAY_ITEM
    items = [m.group(0) for m in _MG_ITEM_RE.finditer(body)]
    if not items:
        return html
    scripts = [m.group(0) for m in _MG_SCRIPT_RE.finditer(body)]
    rest = _MG_SCRIPT_RE.sub("", _MG_ITEM_RE.sub("", body))
    used, parts = set(), []
    for gid, title, marks in MORE_GROUPS:
        mine = []
        for mk in marks:
            for n, it in enumerate(items):
                head = it[:it.find(">") + 1]
                if n not in used and mk in head:
                    used.add(n); mine.append(it)
        if gid == "device":
            mine += [it for n, it in enumerate(items) if n not in used]
            used.update(range(len(items)))
        if mine:
            parts.append('<section class="mg mg-%s"><h2 class="mgh" data-i18n="%s">%s</h2><div class="mgl">\n%s</div></section>\n'
                         % (gid, title, title, "".join(mine)))
    hint = ('<p class="mg-hint"><a href="/settings?open=grp:sys" data-i18n="Setup, tours and factory settings: Settings › System">'
            'Setup, tours and factory settings: Settings › System</a></p>\n')
    out = html[:i + 6] + rest.rstrip() + "\n" + "".join(parts) + hint + "".join(scripts) + MORE_GROUP_JS + html[j:]
    return out.replace("</head>", MORE_GROUP_CSS + "</head>", 1)


# ---- the line on top of the camera picture (410) in the language of the device -----------------------------------------------------
_HUD_TR = {}


def hud_tr(s):
    """a word of the picture line, translated, as ASCII (OpenCV draws no umlauts)"""
    L = CFG.get("lang") or "de"
    k = (L, s)
    v = _HUD_TR.get(k)
    if v is None:
        try:
            v = tr(s, L) if L != "en" else s
        except Exception:
            v = s
        v = str(v)
        for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ß", "ss"), ("’", "'"), ("–", "-"), ("·", "|")):
            v = v.replace(a, b)
        v = _ud.normalize("NFKD", v).encode("ascii", "ignore").decode("ascii")
        if len(_HUD_TR) > 600:
            _HUD_TR.clear()
        _HUD_TR[k] = v
    return v


def klar_selftest():
    for k, v in _HX_KLAR.items():
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), "639zzzb: text " + k
    page = ('<html><head></head><body><main><details id="g2-tt"></details>\n'
            '  <a class="mi" href="/help"><i>📖</i><span><b>A</b></span></a>\n  <a class="mi" href="/qr" id="m-qr"><b>Q</b></a>\n'
            '<script>x()</script>\n  <a class="mi" href="/tausch" id="m-tausch"><b>R</b></a>\n'
            '  <button type="button" class="mi" id="m-fb"><b>F</b></button>\n  <a class="mi" href="/neu"><b>N</b></a>\n</main></body></html>')
    out = more_grouped(page)
    assert out.find('href="/tausch"') < out.find('href="/play"') < out.find('href="/help"') < out.find('href="/qr"') < out.find('id="m-fb"') < out.find('href="/neu"'), out
    assert out.count('class="mi"') == 6 and out.index("<script>x()</script>") > out.index('href="/neu"') and 'id="g2-tt"' in out and "mg-css" in out
    assert MORE_PAGE.count('class="mi"') >= 8 and 'id="g2-more"' not in MORE_PAGE, "639zzb: «Mehr» template"
    assert all('"sec:%s"' % s in WEB_PAGE.split("const MN_NO_FINE = [", 1)[1].split("]", 1)[0] for s in MENU_NO_FINE), "639zzzb: MN_NO_FINE (530) = MENU_NO_FINE (639c)"
    keep = CFG.get("lang")
    try:
        CFG["lang"] = "de"; _HUD_TR.clear()
        assert hud_tr("No rain") == "Kein Regen" and hud_tr("Persons") == "Personen" and hud_tr("breezy") == "boeig", hud_tr("breezy")
        CFG["lang"] = "fr"; _HUD_TR.clear()
        assert hud_tr("storm") == "tempete" and all(ord(c) < 128 for c in hud_tr("RAIN MODE"))
    finally:
        CFG["lang"] = keep; _HUD_TR.clear()
    return "texts in 5 languages, «Mehr» in 4 groups, picture line translated (ASCII)"


SELFTEST_EXTRA.append(("Design «Klar» stage 1 (639zzzb)", klar_selftest))
