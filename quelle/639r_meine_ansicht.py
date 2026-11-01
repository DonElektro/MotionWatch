#@ MoveEye – Teil 639r: «Meine Ansicht» – der mittlere Knopf der Bedienleiste (639o, Fenster 570, Simulator bedienleiste.gd): die Menüs / Karten auf- und zugeklappt, wie der Benutzer sie selbst eingestellt hat; gespeichert pro Benutzer und Seite auf dem Pi (CFG ui_ansicht, /api/ansicht), auf allen Geräten gleich. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Daniel (1.11.2026): «der mittlere der 3 Knöpfe wird Meine Ansicht».
#   * aktiv: jedes Auf- / Zuklappen einer Gruppe / Karte durch den Benutzer wird gemerkt (die Seite schreibt gebündelt, 1 s).
#   * «Alle zuklappen» / «Alle aufklappen»: Meine Ansicht ist aus, das Gemerkte bleibt; die Mitte stellt es wieder her.
#   * beim Start ist Meine Ansicht der Standard. «Nur Gruppen» und der Schalter «Beim Start: Nur Gruppen» bleiben (Daniel:
#     nichts entfernen ohne Zustimmung): «Nur Gruppen» = langer Druck / Rechtsklick auf die Mitte; ist der Schalter ein, startet
#     die Seite wie bisher mit «Nur Gruppen» (Meine Ansicht aus). Übernahme einmal (ui_ansicht_mig): wer «Beim Start: Nur Gruppen»
#     hatte, bekommt als erste Meine Ansicht «Nur Gruppen offen» und der Schalter geht aus (sonst wäre Meine Ansicht nie der Start).
#   * pro Benutzer (der Besitzer ohne Benutzername = «admin», auch das Pi-Fenster) und pro Seite (der Reiter: live, protect,
#     settings, sim, rec …). Ids = stabile Kennungen der Karten (data-view «grp:…» / «sec:…», id, data-k …), dieselben wie im Fenster
#     (grp:<gruppe>, sec:<teil>) – passend zu den Gruppen-Ids von ui_gemeinsam (P1).
#   * ohne Pi (keine Verbindung / kein Recht): die Seite merkt es sich im Browser (localStorage «mwa:…», nicht über web_ui geteilt).
#   * Simulator: lokal (fold_mem, simulator_settings.json); der Abgleich Simulator ↔ MoveEye kommt mit P2 (eine Funktion pro Änderung:
#     web ansichtMerken(id, offen), Fenster App._mine_change, Simulator _mine_change).

ANSICHT_MAX_SEITEN = 40
ANSICHT_MAX_IDS = 400
_ANSICHT_SEITE = re.compile(r"^[a-z0-9_\-]{1,40}$")

# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_MINE = {
    'My view': ('Meine Ansicht', 'Ma vue', 'La mia vista', 'Mia vista'),
    'My view: the menus open and close the way you left them (kept for you on every device). Long press or right click: groups only.':
        ('Meine Ansicht: Die Menüs sind auf- und zugeklappt, wie du sie selbst eingestellt hast (für dich auf allen Geräten gleich). '
         'Lange drücken oder Rechtsklick: Nur Gruppen.',
         'Ma vue : les menus s’ouvrent et se ferment comme tu les as laissés (pareil sur tous tes appareils). Appui long ou clic droit : '
         'seulement les groupes.',
         'La mia vista: i menu sono aperti e chiusi come li hai lasciati (uguale su tutti i tuoi dispositivi). Pressione lunga o clic '
         'destro: solo i gruppi.',
         'Mia vista: ils menus èn averts e serrads sco che ti als has laschads (uschia sin tut tes apparats). Smatgar ditg u clic dretg: '
         'mo las gruppas.'),
    'My view: the menus open and close the way you left them. Long press or right click: groups only.':   # the simulator (local until P2)
        ('Meine Ansicht: Die Menüs sind auf- und zugeklappt, wie du sie selbst eingestellt hast. Lange drücken oder Rechtsklick: Nur Gruppen.',
         'Ma vue : les menus s’ouvrent et se ferment comme tu les as laissés. Appui long ou clic droit : seulement les groupes.',
         'La mia vista: i menu sono aperti e chiusi come li hai lasciati. Pressione lunga o clic destro: solo i gruppi.',
         'Mia vista: ils menus èn averts e serrads sco che ti als has laschads. Smatgar ditg u clic dretg: mo las gruppas.'),
    'My view – saved only on this device (no connection)': ('Meine Ansicht – nur auf diesem Gerät gemerkt (keine Verbindung)',
        'Ma vue – gardée seulement sur cet appareil (pas de connexion)', 'La mia vista – salvata solo su questo dispositivo (nessuna connessione)',
        'Mia vista – memorisada mo sin quest apparat (nagina connexiun)'),
}
for _k, _v in _HX_MINE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
MWB_KEYS = sorted(set(MWB_KEYS) | set(_HX_MINE))

VIEW_GET = VIEW_GET + ("/api/ansicht",)            # every user has his own view (also «Nur ansehen»)
VIEW_POST.add("/api/ansicht")
LOCK_KEEP.update({"ui_ansicht", "ui_ansicht_mig", "ui_ansicht_sg0"})   # operator mode: the own view is no setting of the device


def ansicht_user(g_=None):
    """the key of the user: the logged-in name; the owner (web password with any name, no password, app key, Pi window) = «admin»"""
    if g_ is None or getattr(g_, "role", "admin") == "admin":   # the owner: the web password takes any user name, app keys too
        return "admin"
    return str(getattr(g_, "user", "") or "")[:60] or "admin"


def _ansicht_ids(v):
    return [x[:120] for x in v if isinstance(x, str) and x.strip()][:ANSICHT_MAX_IDS] if isinstance(v, list) else []


def ansicht_clean(d):
    """CFG ui_ansicht: {user: {seite: {"o": [ids open], "z": [ids closed], "t": time}}} - only sane values"""
    out = {}
    if not isinstance(d, dict):
        return out
    for u, pages in list(d.items())[:60]:
        if not isinstance(u, str) or not isinstance(pages, dict):
            continue
        pp = {}
        for s, v in pages.items():
            if isinstance(s, str) and _ANSICHT_SEITE.match(s) and isinstance(v, dict):
                pp[s] = {"o": _ansicht_ids(v.get("o")), "z": _ansicht_ids(v.get("z")), "t": int(v.get("t") or 0) if isinstance(v.get("t"), (int, float)) else 0}
        if pp:
            out[u[:60]] = dict(sorted(pp.items(), key=lambda kv: -kv[1]["t"])[:ANSICHT_MAX_SEITEN])
    return out


def ansicht_mig():
    """once: «Beim Start: Nur Gruppen» -> the first «Meine Ansicht» is «Nur Gruppen offen» (ui_ansicht_sg0), the switch goes off
    so that «Meine Ansicht» is the start (the switch stays and can be switched on again)"""
    if CFG.get("ui_ansicht_mig"):
        return False
    CFG["ui_ansicht_sg0"] = bool(CFG.get("ui_start_groups", True))
    CFG["ui_start_groups"] = False
    CFG["ui_ansicht_mig"] = True
    return True


def ansicht_get(user, seite):
    """{"known": bool, "offen": [...], "zu": [...], "start_groups": the switch, "first_groups": the first view = «Nur Gruppen»}"""
    seite = str(seite or "")[:40]
    e = (CFG.get("ui_ansicht") or {}).get(user, {}).get(seite) if _ANSICHT_SEITE.match(seite) else None
    return {"known": e is not None, "offen": list(e["o"]) if e else [], "zu": list(e["z"]) if e else [],
            "start_groups": bool(CFG.get("ui_start_groups", False)), "first_groups": bool(CFG.get("ui_ansicht_sg0", False))}


def ansicht_set(user, seite, offen, zu):
    """the whole view of ONE page of ONE user (the page sends it bundled); False = bad page key"""
    seite = str(seite or "")[:40]
    if not _ANSICHT_SEITE.match(seite):
        return False
    o, z = _ansicht_ids(offen), _ansicht_ids(zu)
    zs = set(o)
    z = [x for x in z if x not in zs]
    allv = dict(CFG.get("ui_ansicht") or {})
    pages = dict(allv.get(user) or {})
    old = pages.get(seite)
    if old and old["o"] == o and old["z"] == z:
        return True
    pages[seite] = {"o": o, "z": z, "t": int(time.time())}
    allv[str(user)[:60]] = pages
    CFG["ui_ansicht"] = ansicht_clean(allv)            # re-assign: DEFAULTS share the old dict
    save_settings()
    return True


def ansicht_api(request, reply, body, g_):
    """GET /api/ansicht?seite=settings · POST {seite, offen: [...], zu: [...]} (550)"""
    user = ansicht_user(g_)
    if request.method == "POST":
        d = body()
        ok = ansicht_set(user, d.get("seite"), d.get("offen"), d.get("zu"))
        return reply({"ok": ok, "user": user}, 200 if ok else 400)
    return reply(dict(ansicht_get(user, request.args.get("seite")), ok=True, user=user))


_settings_migrations_before_ansicht = _settings_migrations


def _settings_migrations(cfg_in):                         # + 639r: «Beim Start: Nur Gruppen» -> the first «Meine Ansicht»
    _settings_migrations_before_ansicht(cfg_in)
    try:
        CFG["ui_ansicht"] = ansicht_clean(CFG.get("ui_ansicht"))
        if ansicht_mig():
            log_event("sys", "«My view» is the start view now (the folds you set yourself, on every device)")
    except Exception as e:
        log_event("sys", f"Settings migration (639r): {e}"[:150])


# the manual (HELP_PAGE of 540): one paragraph in «Tipps & Tricks», German and English
for _a, _b in (('<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>',
                "<p><b>★ Meine Ansicht:</b> Der mittlere der drei Klapp-Knöpfe zeigt die Menüs so auf- und zugeklappt, wie du sie selbst "
                "eingestellt hast. Solange er blau ist, merkt sich MoveEye jedes Auf- und Zuklappen – pro Seite und für deinen Benutzer, "
                "auf Handy, iPad, PC und im Pi-Fenster gleich. «Alle zuklappen» oder «Alle aufklappen» schalten Meine Ansicht aus, ohne "
                "das Gemerkte zu ändern; ein Druck auf die Mitte bringt es zurück. Lange drücken (oder Rechtsklick) auf die Mitte zeigt "
                "«Nur Gruppen». Ist «Beim Start: Nur Gruppen» ein, startet jede Seite mit «Nur Gruppen».</p>"),
               ('<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>',
                "<p><b>★ My view:</b> the middle of the three fold buttons shows the menus open and closed the way you set them yourself. "
                "While it is blue, MoveEye remembers every fold – per page and for your user, the same on phone, iPad, PC and the Pi "
                "window. «Collapse all» or «Expand all» switch My view off without changing what was kept; press the middle to get it "
                "back. A long press (or right click) on the middle shows «Groups only». With «On start: groups only» on, every page "
                "starts with «Groups only».</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


def _ansicht_selftest():
    keep = {k: CFG.get(k) for k in ("ui_ansicht", "ui_ansicht_mig", "ui_ansicht_sg0", "ui_start_groups")}
    _ss = globals()["save_settings"]
    globals()["save_settings"] = lambda: None
    try:
        CFG["ui_ansicht"] = {}; CFG["ui_ansicht_mig"] = False; CFG["ui_start_groups"] = True
        assert ansicht_mig() and CFG["ui_ansicht_sg0"] and not CFG["ui_start_groups"] and not ansicht_mig(), "639r: migration"
        g0 = ansicht_get("admin", "settings")
        assert not g0["known"] and g0["first_groups"], "639r: first view"
        assert ansicht_set("anna", "settings", ["grp:alarm", "sec:push", 5], ["grp:alarm", "grp:sys"])
        g1 = ansicht_get("anna", "settings")
        assert g1["known"] and g1["offen"] == ["grp:alarm", "sec:push"] and g1["zu"] == ["grp:sys"], "639r: set / get"
        assert not ansicht_get("admin", "settings")["known"], "639r: per user"
        assert not ansicht_set("anna", "../x", [], []) and not ansicht_get("anna", "<b>")["known"], "639r: page key"
        assert ansicht_user(None) == "admin" and "/api/ansicht" in VIEW_POST and role_allows("view", "/api/ansicht", "GET", {}), "639r: rights"
        assert role_allows("kid", "/api/ansicht", "POST", {}), "639r: every user keeps his view"
        tx = mwb_tx()
        assert all(tx[L].get("My view") for L in ("de", "fr", "it", "rm")) and tx["de"]["My view"] == "Meine Ansicht", "639r: texts"
    finally:
        globals()["save_settings"] = _ss
        CFG.update(keep)


SELFTEST_EXTRA.append(("My view (639r)", _ansicht_selftest))
