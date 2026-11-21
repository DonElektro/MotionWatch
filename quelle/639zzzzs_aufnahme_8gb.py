#@ MoveEye – Teil 639zzzzs: Aufnahmeordner ab Werk 8 GB (vorher 2 GB), höchstens die Hälfte des Laufwerks; einmal beim Update 2 GB -> 8 GB (Laufwerk ab 16 GB) mit Hinweis. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer 21.11.2026 (4.18.1, Karte 32 GB): record_max_gb ab Werk 8.0 (020). Schutz: 420 rec_limit_gb() - höchstens die Hälfte
# des Laufwerks der Aufnahmen (das Aufräumen 410 und der Chip im Verlauf 430 nehmen diesen Wert; Einstellungen → Aufnahme sagt
# «Das Laufwerk ist klein: höchstens n GB für Aufnahmen»).
# Einmal beim Update (rec8_migrate, aus load_settings 040): steht noch genau der alte Standard 2.0 und hat das Laufwerk mindestens
# 16 GB (nominal: ab 14.5 GiB), wird 8.0 gesetzt - mit einem Hinweis in «Neu in dieser Version» (Web und Fenster, 5 Sprachen).
# Ein anderer Wert (vom Benutzer) bleibt; der Host-Modus (639zzzzw: fest 0.5) wird nie angefasst. Test: werkzeuge/aufnahme_8gb_test.py.
# ----------------------------------------------------------------------------
for _k, _v in (("rec8_mig", False), ("rec8_note", ""), ("rec8_seen", [])):
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)
REC8_MIN_DRIVE = 14.5 * 1024 ** 3        # a «16 GB» card has about 14.8 GiB
REC8_NOTE = "New: recordings may now use up to 8 GB (before 2 GB) – the oldest are still deleted first. Change it: Settings → Recording → «Max recordings folder (GB)»."


def rec8_migrate(cfg_in):
    """once per settings file: the old default 2 GB -> 8 GB on a drive from 16 GB (never a value of the user, never the host)"""
    if not isinstance(cfg_in, dict) or cfg_in.get("rec8_mig") or HOST.get("on"):
        return []
    CFG["rec8_mig"] = True
    try:
        old = float(cfg_in["record_max_gb"])
    except (KeyError, TypeError, ValueError):
        return []                                         # a new device: the new default is there already
    if abs(old - 2.0) > 1e-9:
        return []
    try:
        total = shutil.disk_usage(rec_dir() if os.path.isdir(rec_dir()) else os.path.dirname(rec_dir()) or "/").total
    except OSError:
        return []
    if total < REC8_MIN_DRIVE:
        return []
    CFG["record_max_gb"] = 8.0; CFG["rec8_note"] = "pending"; CFG["rec8_seen"] = []
    return [f"recordings folder 2 GB -> 8 GB (drive {total / 1024 ** 3:.0f} GB)"]


_news_state_639zzzzs = news_state
_news_seen_639zzzzs = news_seen


# wraps: news_state
def news_state(who="web", lang=None):                     # + 639zzzzs: the one-time notice of the 8 GB
    st = _news_state_639zzzzs(who, lang)
    if CFG.get("rec8_note") == "pending" and who not in (CFG.get("rec8_seen") or []):
        it = {"v": APP_VERSION, "t": "🗄 " + tr(REC8_NOTE, lang), "href": "/settings?setting=record_max_gb"}
        st = dict(st, items=[it] + list(st.get("items") or []), show=True)
    return st


# wraps: news_seen
def news_seen(who="web"):                                 # + 639zzzzs
    if CFG.get("rec8_note") == "pending":
        CFG["rec8_seen"] = sorted(set(CFG.get("rec8_seen") or []) | {who})
    return _news_seen_639zzzzs(who)


_HX_REC8 = {
    REC8_NOTE: ("Neu: Aufnahmen dürfen jetzt bis 8 GB brauchen (vorher 2 GB) – die ältesten werden weiterhin zuerst gelöscht. "
                "Ändern: Einstellungen → Aufnahme → «Max. Aufnahmeordner (GB)».",
                "Nouveau : les enregistrements peuvent maintenant utiliser jusqu’à 8 Go (avant 2 Go) – les plus anciens sont toujours "
                "effacés en premier. Modifier : Réglages → Enregistrement → «Dossier d’enregistrements max. (Go)».",
                "Novità: le registrazioni possono ora usare fino a 8 GB (prima 2 GB) – le più vecchie vengono sempre cancellate per "
                "prime. Modificare: Impostazioni → Registrazione → «Cartella registrazioni max. (GB)».",
                "Nov: las registraziuns dastgan ussa duvrar fin 8 GB (avant 2 GB) – las pli veglias vegnan anc adina stizzadas "
                "l'emprim. Midar: Parameters → Registraziun → «Ordinatur da registraziuns max. (GB)»."),
    "The drive is small: at most {n} GB for recordings (half of the drive)": (
        "Das Laufwerk ist klein: höchstens {n} GB für Aufnahmen (die Hälfte des Laufwerks)",
        "Le disque est petit : au plus {n} Go pour les enregistrements (la moitié du disque)",
        "L’unità è piccola: al massimo {n} GB per le registrazioni (metà dell’unità)",
        "Il disc è pitschen: al pli {n} GB per registraziuns (la mesadad dal disc)"),
}
for _k, _v in _HX_REC8.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
