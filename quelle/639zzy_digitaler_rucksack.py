#@ MoveEye – Teil 639zzy: «Digitaler Rucksack» – neuer Name des Bereichs «Datentausch» (nur die Anzeige), Prüfung im Selbsttest. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Auftrag des Besitzers (12.11.2026): der Bereich «📁 Datentausch» heisst ab jetzt «Digitaler Rucksack»
# (de «Digitaler Rucksack» / «im Digitalen Rucksack», en «Digital backpack», fr «Sac à dos numérique», it «Zaino digitale»,
# rm «Satgados digital»). Geändert ist NUR, was man liest:
#   * bleibt: Adressen (/tausch/…), Einstellungs-Schlüssel (tausch_on …), Rechte (files_view …), Ordner auf der Karte,
#     Namen von Teilen und Tests – und die englischen Schlüssel der Texte («File exchange» ist auch der Name des
#     Abschnitts in den Einstellungen und der Push-Art; gespeicherte Einstellungen hängen daran).
#   * Darum EN_SHOW (050): {englischer Schlüssel: englischer Text am Bildschirm}. tr() (560) nimmt ihn für Englisch (und für
#     fr / it, wenn dort nichts übersetzt ist); die Web-Seiten bekommen ihn als window.I18NEX, LX() (510) fragt ihn für
#     Englisch / Französisch / Italienisch nach der Sprachdatei.
#   * Deutsch, Französisch, Italienisch, Romanisch stehen dort, wo sie immer standen (639zzc, 639zzd, 639zze, 639zzw, 630,
#     639zzu), Anleitung und Protokoll-Zeilen ebenso.
# Selbsttest (streng, wie i18n_selftest in 395): kein Text des Programms nennt den Bereich noch beim alten Namen, in keiner
# der fünf Sprachen. Erlaubt sind nur: die Liste der Änderungen (Modul-Docstring von 000 – Geschichte bleibt, wie sie
# geschrieben wurde), Kommentare und Docstrings, und die englischen Schlüssel aus EN_SHOW dort, wo sie Schlüssel sind.
# ----------------------------------------------------------------------------
EN_SHOW.update({
    "File exchange": "Digital backpack",
    "File exchange on (Mehr → File exchange)": "Digital backpack on (More → Digital backpack)",
    "The file exchange is switched off.": "The digital backpack is switched off.",
    "Switch it on under Settings → System → File exchange.": "Switch it on under Settings → System → Digital backpack.",
    "Space for the file exchange in total (GB)": "Space for the digital backpack in total (GB)",
    "All files of the file exchange together. Uploads stop with a clear message when it is full.":
        "All files of the digital backpack together. Uploads stop with a clear message when it is full.",
    "The file exchange is full: {a} of {b} used. Delete old files first.": "The digital backpack is full: {a} of {b} used. Delete old files first.",
    "Load it under Datentausch → 🌿 or here.": "Load it under Digital backpack → 🌿 or here.",
    "Saved in Datentausch → «{f}»": "Saved in Digital backpack → «{f}»",
})

# the old name of the area in the five languages (word forms; «Tausch» alone was never used as its name)
RUCKSACK_ALT = re.compile(r"daten[- ]?tausch|file[- ]exchange|data[- ]exchange|[ée]change de (?:fichiers|données)|scambio (?:di )?(?:file|dati)"
                          r"|barat da (?:datotecas|datas)", re.I)
RUCKSACK_NAMEN = {"de": "Digitaler Rucksack", "en": "Digital backpack", "fr": "Sac à dos numérique", "it": "Zaino digitale", "rm": "Satgados digital"}
_RUCKSACK_INTERN = re.compile(r"\b\w*\d\w*_daten" + r"tausch\b")       # names of parts / zip entries («639zzc_datentausch») - not texts


def rucksack_alt_in(text):
    """the old name in a text of the program (a string of the source): the keys of EN_SHOW are allowed where they are keys -
    alone, in data-i18n / t() / tr() / trf(), as a section name of the settings (sec: / title:) or as a JSON key"""
    if text in EN_SHOW:
        return ""
    s = _RUCKSACK_INTERN.sub("", text)
    for k in sorted(EN_SHOW, key=len, reverse=True):
        if k not in s:
            continue
        q = re.escape(k)
        s = re.sub(r"""data-i18n(?:-ph)?=\\?["']""" + q + r"""\\?["']|\b(?:t|tt|tr|trf)\(\s*\\?["']""" + q + r"""\\?["']|\b(?:sec|title):\s*\\?["']"""
                   + q + r"""\\?["']|\\?["']""" + q + r"""\\?["']\s*:""", " ", s)
    m = RUCKSACK_ALT.search(s)
    return s[max(0, m.start() - 40):m.end() + 40] if m else ""


def rucksack_alt_source(src):
    """[(line, piece)]: the strings of a source text that still use the old name. Not judged: comments, docstrings of
    functions and classes (internal notes), and the module docstring = the list of changes (history stays as written)."""
    import ast as _ast
    tree = _ast.parse(src)
    skip = set()
    for nd in _ast.walk(tree):
        if isinstance(nd, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) and nd.body:
            d = nd.body[0]
            if isinstance(d, _ast.Expr) and isinstance(d.value, _ast.Constant) and isinstance(d.value.value, str):
                skip.add(id(d.value))
    out = []
    for nd in _ast.walk(tree):
        if isinstance(nd, _ast.Constant) and isinstance(nd.value, str) and id(nd) not in skip and len(nd.value) > 9:
            hit = rucksack_alt_in(nd.value)
            if hit:
                out.append((nd.lineno, hit.replace("\n", " ")))
    return out


def rucksack_selftest():
    # 1. the mechanism: English on screen differs from the key, placeholders stay, the keys exist
    for k, v in EN_SHOW.items():
        assert k in DE and all(TRX[L].get(k) for L in ("fr", "it", "rm")), f"EN_SHOW: key without translations: {k}"
        assert sorted(re.findall(r"\{\w*\}", k)) == sorted(re.findall(r"\{\w*\}", v)), f"EN_SHOW: placeholders differ: {k}"
        assert not RUCKSACK_ALT.search(v), f"EN_SHOW: the new English text has the old name: {v}"
    assert tr("File exchange", "en") == "Digital backpack" and tr("File exchange", "de") == "Digitaler Rucksack"
    assert [tr("File exchange", L) for L in ("fr", "it", "rm")] == ["Sac à dos numérique", "Zaino digitale", "Satgados digital"]
    assert trf("The file exchange is full: {a} of {b} used. Delete old files first.", "en", a="1 GB", b="5 GB").startswith("The digital backpack is full: 1 GB of 5 GB")
    assert tr("The file exchange is switched off.", "de") == "Der Digitale Rucksack ist ausgeschaltet."
    assert "I18NEX" in i18n_loader() and '"File exchange":"Digital backpack"' in i18n_loader() and "e&&e[s]" in i18n_loader(), "the pages do not get the English names"
    assert "tausch_on" in CFG and "File exchange" in SECTIONS and "File exchange" in PK_TITLES, "keys, section and push kind keep their names"
    # 2. what the tables show: no value in any of the five languages has the old name
    bad = []
    for L, tab in (("de", DE), ("fr", TRX["fr"]), ("it", TRX["it"]), ("rm", TRX["rm"])):
        bad += [f"{L}: {v[:70]}" for v in tab.values() if isinstance(v, str) and RUCKSACK_ALT.search(v)]
    bad += [f"en: {k[:70]}" for k in i18n_used_keys() if RUCKSACK_ALT.search(tr(k, "en"))]
    for L in ("de", "en", "fr", "it", "rm"):
        h = (HELP_X.get(L) or "") if L in ("fr", "it", "rm") else ""
        m = RUCKSACK_ALT.search(h)
        if m:
            bad.append(f"{L} (manual): {h[max(0, m.start() - 40):m.end() + 20]}")
    assert not bad, f"{len(bad)} texts still use the old name of the «Digitaler Rucksack»: " + " · ".join(bad[:8])
    # 3. the judge itself: it finds the old name in every language and lets the allowed places pass
    o = lambda *p: "".join(p)                               # the old names in pieces, so that this list is not found itself
    for s in (o("Mehr → 📁 Daten", "tausch"), o("im Daten-", "Tausch"), o("<h2>File ", "exchange</h2>"), o("the data ", "exchange"), o("L’échange de ", "fichiers"),
              o("Scambio ", "di file"), o("scambio ", "dati"), o("Barat da ", "datotecas"), o('x data-i18n="Chat">File ', 'exchange<')):
        assert rucksack_alt_in(s), f"not found: {s}"
    for s in ("File exchange", '<b data-i18n="File exchange">Digital backpack</b>', 't("The file exchange is switched off.") + x',
              '{sec: "File exchange", title: "File exchange", ic: "📁"}', "Akku tauschen", "Austausch der Zellen", o("639zzc_daten", "tausch/TAUSCH_PAGE"),
              "im Digitalen Rucksack", 'tr(\\"File exchange\\")'):
        assert not rucksack_alt_in(s), f"wrongly found: {s}"
    # 4. every string of the program (all parts, as put together from quelle/ - also parts that come later)
    if ZD_FILE and not ZD["ok"]:
        return "tables and mechanism; the source is not judged without the data file"
    rest = rucksack_alt_source(zd_source())
    assert not rest, (f"{len(rest)} texts still use the old name – the area is called «Digitaler Rucksack» "
                      "(en «Digital backpack», fr «Sac à dos numérique», it «Zaino digitale», rm «Satgados digital»): "
                      + " · ".join(f"line {ln}: …{t}…" for ln, t in rest[:8]))
    return "«Digitaler Rucksack» in 5 languages, " + str(len(EN_SHOW)) + " English names beside their keys, no text with the old name"


SELFTEST_EXTRA.append(("Digitaler Rucksack: the new name of the file area everywhere, keys and addresses unchanged (639zzy)", rucksack_selftest))
