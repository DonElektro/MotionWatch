#@ MoveEye – Teil 639zzo: Spiele unter «Mehr» aufgeräumt – EIN Einstieg: Unterreiter «Spielen», dort oben die Kachel «Spielecke» (/party); «Spiele freigeben» nur noch auf der Seite der Spielecke; Unterreiter «Spielecke» und Listeneintrag «Spielecke» in der Übersicht entfallen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (10.11.2026). Vorher gab es unter «Mehr» vier Stellen für Spiele: Unterreiter «Spielen» (/play), Unterreiter
# «Spielecke» (/party), Listeneintrag «Spielecke» in der Übersicht (dieselbe Seite) und die Karte «Spiele freigeben» (/more).
#   * Jetzt: Unterreiter «Spielen» → oben die Kachel «🎲 Spielecke» → /party. Auf /party steht «Spiele freigeben» wie bisher
#     zuoberst (Knopf + Dauer, 460 partyPaint) – dieselbe Aktion (/api/party «all»), dieselben Rechte: nur der Administrator
#     (550: POST /api/party verlangt die Rolle «admin»). Die Karte auf /more und der Unterreiter «Spielecke» sind weg.
#   * Nichts geht verloren: /party, /api/party, /p/<key>/…, /spiele/…, /games/… sind unverändert (alte Lesezeichen gehen),
#     die Gästeseite ist unverändert; auf /party leuchtet der Unterreiter «Spielen».
#   * Benutzer ohne Administrator-Rolle mit dem Recht «Spiele» (Kind, Freund, Familie) dürfen /party öffnen, aber nicht
#     /play (das war schon so). Damit sie die Spielecke weiter finden, bleibt für sie – und nur für sie – der Eintrag
#     «Spielecke» in der Übersicht (er erscheint, wenn /play für diesen Benutzer nicht erreichbar ist). Keine Rechte geändert.
#   * Die Anleitung nennt den neuen Weg («Mehr → Spielen → Spielecke»), in allen fünf Sprachen.
# Hier (nach 639i / 525 / 470) per Ersetzen, damit die geteilten Teile unberührt bleiben. Selbsttest spiele_ordnen_selftest,
# Test werkzeuge/spiele_ordnen_test.py (Browser: ein Einstieg, Kachel öffnet /party, Freigeben von der Spielecke aus).
# ----------------------------------------------------------------------------
NAV_SUB["more"] = [x for x in NAV_SUB["more"] if x[0] != "party"]      # NAV_OF["party"] bleibt «more»
_nav_html_639zzo = nav_html


# wraps: nav_html
def nav_html(active):                                       # + 639zzo: on /party the sub tab «Spielen» is lit
    h_ = _nav_html_639zzo(active)
    if active == "party":
        h_ = h_.replace('<a href="/play" data-i18n=', '<a href="/play" class=on data-i18n=', 1)
    return h_


# ---- /more: no card «Spiele freigeben», the entry «Spielecke» only for users who cannot open «Spielen» ----------------------------
_SO_CARD = '  <div id="games"><div class="gt"><b>🎮 <span data-i18n="Games">Games</span></b><div class="mut" id="g-txt"></div><div id="g-btn"></div></div></div>\n'
_SO_ENTRY = '<a class="mi" href="/party"><i>🎲</i>'
_SO_LOAD = "(async () => { await initAppearance(); gmLoad(); })();"
SO_MORE_OK = MORE_PAGE.count(_SO_CARD) == 1 and MORE_PAGE.count(_SO_ENTRY) == 1 and MORE_PAGE.count(_SO_LOAD) == 1
if SO_MORE_OK:
    MORE_PAGE = (MORE_PAGE.replace(_SO_CARD, "", 1)
                 .replace(_SO_ENTRY, '<a class="mi" href="/party" id="m-party" hidden><i>🎲</i>', 1)
                 .replace(_SO_LOAD, "(async () => { await initAppearance(); })();\n"
                          "// 639zzo: the games live under «Spielen»; who may not open that page (users without the administrator role) keeps the entry «Spielecke»\n"
                          'fetch("/play", {method: "HEAD"}).then(r => { if (!r.ok) document.getElementById("m-party").hidden = false; }).catch(() => {});', 1))

# ---- /play: the tile «Spielecke» on top ----------------------------------------------------------------------------------------------
SO_TILE_TXT = "Quiz, werewolf, connect four and the game collection – «Open all games» for the guests is there too"
_HX_SO = {SO_TILE_TXT: ("Quiz, Werwolf, Vier gewinnt und die Spielesammlung – dort auch «Spiele freigeben» für die Gäste",
                        "Quiz, loup-garou, puissance 4 et la collection de jeux – avec « Ouvrir tous les jeux » pour les invités",
                        "Quiz, lupo mannaro, forza quattro e la raccolta di giochi – lì anche «Aprire tutti i giochi» per gli ospiti",
                        "Quiz, luf-uman, quatter en lingia e la collecziun da gieus – là er «Avrir tut ils gieus» per ils giasts")}
for _k, _v in _HX_SO.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_SO_MAIN = '<main>\n  <div class="pl-card" id="pl-lv" hidden></div>'
_SO_TILE = ('<main>\n  <a class="pl-party" id="pl-party" href="/party"><i>🎲</i><span><b data-i18n="Game corner">Game corner</b>'
            '<small data-i18n="' + SO_TILE_TXT + '">' + SO_TILE_TXT + '</small></span><span class="ar">›</span></a>\n'
            '  <div class="pl-card" id="pl-lv" hidden></div>')
_SO_CSS = (".pl-party{display:flex;align-items:center;gap:12px;padding:14px;margin:0 0 12px;border:1px solid var(--acc);border-radius:14px;background:var(--panel);"
           "color:var(--txt);text-decoration:none}.pl-party:hover{filter:brightness(1.08)}.pl-party i{font-style:normal;font-size:30px;width:40px;text-align:center}"
           ".pl-party b{display:block;font-size:16px}.pl-party small{color:var(--mut);font-size:12px}.pl-party .ar{margin-left:auto;color:var(--mut);font-size:20px}\n")
SO_PLAY_OK = PLAY_PAGE.count(_SO_MAIN) == 1 and PLAY_PAGE.count("</style></head><body>") == 1 and 'id="pl-party"' not in PLAY_PAGE
if SO_PLAY_OK:
    PLAY_PAGE = PLAY_PAGE.replace(_SO_MAIN, _SO_TILE, 1).replace("</style></head><body>", _SO_CSS + "</style></head><body>", 1)
_play_page_639zzo = play_page


# wraps: play_page
def play_page():                                            # + 639zzo: the German texts of the tile
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in ("Game corner", SO_TILE_TXT)}, ensure_ascii=False) + ");"
    return _play_page_639zzo().replace("const ST = ", js + "\nconst ST = ", 1)


# ---- the manual: the new way («Mehr → Spielen → Spielecke»), five languages ---------------------------------------------------------
def _so_help(doc, lang):
    m_, p_, g_, o_ = (tr(x, lang) for x in ("More", "Play area", "Game corner", "Open all games"))
    if not doc or p_ in ("", "Play area") and lang != "en":
        return doc
    way = f"{m_} → {p_} → {g_}"
    doc = doc.replace(way, "\x00").replace(f"{m_} → {g_}", way).replace("\x00", way)
    for a_, b_ in (("«", "»"), ("“", "”"), ("« ", " »")):
        doc = doc.replace(f"{m_} → {a_}{o_}{b_}", f"{way} → {a_}{o_}{b_}")
    return doc


_hp_en_so = HELP_PAGE.find('<div lang="en">')
if _hp_en_so > 0:
    HELP_PAGE = _so_help(HELP_PAGE[:_hp_en_so], "de") + _so_help(HELP_PAGE[_hp_en_so:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _so_help(HELP_X[_L], _L)


def spiele_ordnen_selftest():
    assert SO_MORE_OK and SO_PLAY_OK, "MORE_PAGE / PLAY_PAGE look different - adjust part 639zzo"
    assert [k for k, *_r in NAV_SUB["more"]] == ["more", "play", "help", "tools"] and NAV_OF.get("party") == "more"
    n_ = nav_html("party")
    assert 'href="/party"' not in n_ and '<a href="/play" class=on' in n_ and n_.count("class=on") == 1
    assert nav_html("play").count("class=on") == 1 and 'href="/party"' not in nav_html("more")
    assert 'id="games"' not in MORE_PAGE and MORE_PAGE.count('href="/party"') == 1 and 'href="/party" id="m-party" hidden' in MORE_PAGE
    assert "gmLoad(); })" not in MORE_PAGE
    assert PLAY_PAGE.count('href="/party"') == 1 and PLAY_PAGE.index('id="pl-party"') < PLAY_PAGE.index('id="pl-lv"')
    assert "Open all games" in TOOLS_PAGE and 'partyDo({action: "all"' in TOOLS_PAGE, "«Spiele freigeben» is on the page of the game corner"
    assert "ß" not in _HX_SO[SO_TILE_TXT][0] and all(TRX[L].get(SO_TILE_TXT) for L in ("fr", "it", "rm"))
    assert "Mehr → Spielen → Spielecke" in HELP_PAGE and "Mehr → Spielecke" not in HELP_PAGE and "Mehr → «Spiele freigeben»" not in HELP_PAGE
    assert role_allows("kid", "/party", "GET", {}) and not role_allows("kid", "/play", "GET", {}) and not role_allows("family", "/api/party", "POST", {"action": "all"})
    return True


SELFTEST_EXTRA.append(("Games under «Mehr»: one entry point (639zzo)", spiele_ordnen_selftest))
