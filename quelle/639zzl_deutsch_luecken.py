#@ MoveEye – Teil 639zzl: deutsche Lücken der Web-Seiten – Texte, die es in der Python-Tabelle DE gibt, aber nie in die deutsche Liste einer Seite (I18N.de / TX) kopiert wurden, erscheinen auf der deutschen Seite nicht mehr englisch. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Fund (Prüfung 10.11.2026): im deutschen Web standen «Play area» (zweite Zeile der Reiter unter «Mehr»), «Build yourself» mit
# Beschreibung (Mehr), «STATUS LED & BUTTONS» und «FILE EXCHANGE» (Einstellungen), «Night timeline» (Verlauf) englisch. Die
# deutschen Texte gab es (639i, 639w, 639f, 639zzc …) - aber nur in DE (Fenster + Server) und in der Liste der EINEN Seite,
# zu der der Teil gehört. Jede andere Seite, die denselben Text zeigt (Reiter, Menü «Mehr», Gruppen-Titel), kannte ihn nicht;
# fr / it / rm waren nicht betroffen (die kommen aus TRX über /i18n/<sprache>.js auf jede Seite).
#   * render_page() (ganz aussen, nach allen anderen Teilen) sucht in der fertigen Seite die Texte, die DE kennt und für die
#     die Seite kein eigenes Deutsch hat ("Text": … fehlt), und gibt deren Deutsch als window.I18NDX mit - einmal pro
#     Seiten-Vorlage gesucht, danach aus dem Speicher.
#   * LX() (510, i18n_loader) fragt I18NDX nach der Sprachdatei: Deutsch nach der eigenen Liste der Seite (die gewinnt immer),
#     Romanisch dort, wo nichts übersetzt ist (wie im Fenster: «fehlt ein romanischer Text, erscheint Deutsch»).
#     Englisch, Französisch, Italienisch: unverändert.
# Test: werkzeuge/deutsch_luecken_test.py.
# ----------------------------------------------------------------------------
# German that so far stood only in the list of one page (530) while another page (Simulator) shows the same text
DE.setdefault("missed pictures from the game (hard cases)", "verpasste Bilder aus dem Spiel (schwierige Fälle)")
_I18N_DE_GAPS = {}
# only the opening quote is consumed (the rest is a look-ahead): in HTML + JavaScript the quotes do not pair up from the start
# of the text, so every quote is tried as a beginning - what is no text of DE falls out below
_I18N_STR_RE = re.compile(r'"(?=((?:[^"\\\n]|\\.){2,240})")')
_I18N_ATTR_RE = re.compile(r'data-i18n(?:-title|-ph|-placeholder)?="([^"\n]{2,400})"')
_I18N_PAIR_RE = re.compile(r'"(?=((?:[^"\\\n]|\\.){2,240})"\s*:\s*"((?:[^"\\\n]|\\.){1,400})")')


def _i18n_js_str(k):
    if "\\" not in k:
        return k
    try:
        return json.loads('"' + k + '"')
    except ValueError:
        return None


def i18n_de_gaps(text):
    """{English: German} for the texts in this page that DE knows and the page does not carry with the same German. Only a
    list entry «"text": "the same German"» counts as «has it» - the same text as a key of another table (icons, addresses)
    does not (that hid «Play area»); a page with a German of its own keeps it anyway (its list is asked first).
    Taken are only clear cases: what stands in data-i18n="…" (the page asks for a translation) and whole phrases (two words
    or more). A single word somewhere in the script («left», «home», «back», «light») means something else in every place -
    DE has one German for it, maybe the wrong one here; such a word stays as it was."""
    import html as _h
    attr = {_h.unescape(k) for k in _I18N_ATTR_RE.findall(text)}
    cand = set(attr)
    for m in _I18N_STR_RE.finditer(text):
        k = _i18n_js_str(m.group(1))
        if k and " " in k.strip() and len(k) >= 8:
            cand.add(k)
    cand = {k for k in cand if isinstance(DE.get(k), str) and DE[k] != k}
    for m in _I18N_PAIR_RE.finditer(text):
        k = _i18n_js_str(m.group(1))
        if k in cand and _i18n_js_str(m.group(2)) == DE[k]:
            cand.discard(k)
    return {k: DE[k] for k in cand}


def i18n_de_fill(page, key):
    """puts window.I18NDX into the finished page; the search runs once per page template (key)"""
    if "</head>" not in page:
        return page
    d = _I18N_DE_GAPS.get(key)
    if d is None:
        try:
            d = i18n_de_gaps(page)
        except Exception as e:
            d = {}
            log_event("sys", f"Web: German texts of the page «{key[0]}»: {type(e).__name__}: {e}"[:160])
        if len(_I18N_DE_GAPS) > 120:
            _I18N_DE_GAPS.clear()
        _I18N_DE_GAPS[key] = d
    if not d:
        return page
    return page.replace("</head>", "<script>window.I18NDX=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
                        + ";</script></head>", 1)


_render_page_639zzl = render_page


# wraps: render_page
def render_page(page, active):                              # + 639zzl: the German the page does not have itself
    return i18n_de_fill(_render_page_639zzl(page, active), (active, len(page), hash(page)))


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def deutsch_luecken_selftest():
    g = i18n_de_gaps('<a data-i18n="Play area">Play area</a><script>const I18N = {de: {"Tools": "Werkzeuge"}}; t("Tools"); t("Status LED & buttons"); t("no such text 123"); t("left");</script>')
    assert g.get("Play area") == "Spielen" and g.get("Status LED & buttons") == "Status-LED & Tasten", g
    assert "Tools" not in g and "no such text 123" not in g, "what the page has itself and unknown texts stay out"
    assert "left" in DE and "left" not in g, "a single word in the script is not taken (one German, many meanings)"
    assert i18n_de_gaps('<script>const IC = {"Play area": "🎮"}; t("Play area");</script>').get("Play area") == "Spielen", "a key of another table is no German"
    assert i18n_de_gaps('<b data-i18n="Status LED &amp; buttons"></b>').get("Status LED & buttons"), "HTML attribute with &amp;"
    for nm, tab, need in (("WEB_PAGE", "settings", ("Status LED & buttons", "File exchange")), ("TOOLS_PAGE", "tools", ("Play area",)),
                          ("REC_PAGE", "rec", ("Night timeline",))):
        html = render_page(globals()[nm], tab)
        assert html.count("window.I18NDX=") == 1, nm
        dx = json.loads(html.split("window.I18NDX=", 1)[1].split(";</script>", 1)[0].replace("<\\/", "</"))
        for k in need:
            assert dx.get(k) == DE[k] != k, (nm, k)
    for _k, _h, lb in [x for v in NAV_SUB.values() for x in v] + [(k, h, lb) for k, h, lb, _s in NAV_ITEMS]:
        assert lb in DE, "tab without German: " + lb
    assert "window.I18NDX" in i18n_loader(), "LX asks the German gaps"
    return "German gaps: every page gets the German it lacks (tabs, menu «Mehr», group titles)"


SELFTEST_EXTRA.append(("German gaps of the web pages (639zzl)", deutsch_luecken_selftest))
