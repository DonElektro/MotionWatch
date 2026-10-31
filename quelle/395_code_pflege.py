#@ MoveEye – Teil 395: Code-Pflege im Selbsttest – fehlende Übersetzungen (fr / it / rm), alte Einstellungen nur zum Übernehmen (MIGRATE_ONLY). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.18 (Wunsch Daniel, Code-Pflege):
#   - Übersetzungen: welche sichtbaren Texte (tr() / trf() im Programm, t() und data-i18n in den Webseiten, die Beschriftungen
#     der Einstellungen) haben auf Französisch / Italienisch / Romanisch noch keine Übersetzung? Nur eine Warnung im Selbsttest
#     (Anzahl + die ersten 20), kein Fehler: es erscheint dann Englisch (fr / it) bzw. Deutsch (rm).
#   - MIGRATE_ONLY (020): alte Schlüssel, die nur noch aus Dateien älterer Versionen gelesen werden, stehen nirgends sonst
#     (nicht in CFG, nicht in den Einstellungs-Listen, nicht in der Sicherung / dem Diagnose-Paket).
# Zusätzliche Prüfungen des Selbsttests stehen in SELFTEST_EXTRA (self_test in 390 ruft sie nach den eigenen auf).
# ----------------------------------------------------------------------------
SELFTEST_EXTRA = []                                         # [(name, function)] - like chk() in self_test (390)

_I18N_PY = re.compile(r"""(?<![\w.])(?:tr|trf)\(\s*((?:"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'))\s*[,)]""")
_I18N_JS = re.compile(r"""(?<![\w.$])t\(\s*((?:"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'))\s*[,)]""")
_I18N_ATTR = re.compile(r"""data-i18n(?:-ph)?=\\?"([^"\\]+)\\?\"""")


def i18n_used_keys(src=None):
    """the English texts the program shows: tr() / trf() (Python), t() and data-i18n (web pages), the settings labels"""
    import ast as _ast
    import html as _html
    if src is None:
        src = zd_source()                                   # with the literals of the data zip (012)
    keys = set()
    for rx in (_I18N_PY, _I18N_JS):
        for m in rx.finditer(src):
            try:
                s = _ast.literal_eval(m.group(1))
            except (ValueError, SyntaxError):
                continue
            if isinstance(s, str):
                keys.add(s)
    for m in _I18N_ATTR.finditer(src):
        keys.add(_html.unescape(m.group(1)))
    for lst in (TOGGLES, SLIDERS, TEXTS):
        keys.update(x[2] for x in lst)
    keys.update(SECTIONS)
    return {k for k in keys if re.search(r"[A-Za-z]{2}", k) and "{" not in k[:1]}


def i18n_missing(langs=("fr", "it", "rm"), src=None):
    """{lang: sorted list of the used texts without a translation in TRX[lang]}"""
    keys = i18n_used_keys(src)
    return {L: sorted(k for k in keys if not TRX.get(L, {}).get(k)) for L in langs}


def i18n_selftest():
    miss = i18n_missing()
    n = len(i18n_used_keys())
    if not any(miss.values()):
        return f"{n} texts, all translated"
    out = [f"{n} texts; warning only - without translation:"]
    for L, ks in miss.items():
        out.append(f"   {L}: {len(ks)} – " + " · ".join(repr(k[:50]) for k in ks[:20]))
    return "\n".join(out)


def migrate_only_selftest():
    """the keys only taken over from old files are nowhere else; and an old file is still taken over"""
    lists = {x[1] for x in TOGGLES + SLIDERS + TEXTS}
    bad = [k for k in MIGRATE_ONLY if k in CFG or k in DEFAULTS or k in lists or k in SIMPLE_KEYS]
    assert not bad, f"MIGRATE_ONLY keys still in CFG / the settings lists: {bad}"
    assert not any(k in settings_data()["cfg"] for k in MIGRATE_ONLY), "MIGRATE_ONLY key in the saved settings"
    keep = {k: CFG.get(k) for k in ("weekrep_sim", "presence_back")}
    try:
        CFG["weekrep_sim"] = True; CFG["presence_back"] = "ask"
        nachlauf_migrate({"simweek_on": False, "back_ask": False, "presence_auto": False})
        assert CFG["weekrep_sim"] is False and CFG["presence_back"] == "none", "old file not taken over"
    finally:
        CFG.update(keep)
    return f"{len(MIGRATE_ONLY)} old keys only for taking over: " + ", ".join(sorted(MIGRATE_ONLY))


SELFTEST_EXTRA.append(("Old settings only for taking over (MIGRATE_ONLY)", migrate_only_selftest))
SELFTEST_EXTRA.append(("Translations fr / it / rm (texts in use)", i18n_selftest))
