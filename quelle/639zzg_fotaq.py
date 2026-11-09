#@ MoveEye – Teil 639zzg: «Flight of the Amazon Queen» (1995, CD-Fassung mit Sprachausgabe, Deutsch und Englisch) in der Spielecke – ScummVM als WebAssembly im Browser, Paket einmal laden (Admin, feste Grösse + sha256, Fortschritt, 2 GB frei), Kachel «👆 Touch», Spiele-Port /g/fotaq/. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (09.11.2026, Entscheide fest): CD-Fassung mit Sprache, Deutsch UND Englisch vor dem Start wählbar.
#   * Gebaut im Workflow «FOTAQ» (.github/workflows/fotaq.yml, werkzeuge/fotaq/) auf einem GitHub-Rechner: ScummVM (offizieller
#     Emscripten-Port, Tag + Commit dort, nur die Queen-Engine, Vorbis für Deutsch, libmad für Englisch) + die Freeware-Daten
#     von ScummVM (DE FOTAQ_Ger_talkie-1.0.zip, EN FOTAQ_Talkie-1.1.zip, unverändert, sha256 fest im Workflow, gegen die
#     Erkennungstabelle von ScummVM geprüft). Drei Release-Assets an «FOTAQ_TAG» (nie «latest»): engine (ScummVM, Startseite,
#     Lizenzen), de, en. Grösse + sha256 jeder Datei stehen hier in der (signierten) Hauptdatei – die Signatur bürgt für das
#     Paket. Nicht im Spiele-ZIP im Repository (das ist im Git, ~15 MB; FOTAQ ist rund 10-mal so gross).
#   * Laden nur durch den Admin (Mehr → Spielecke → «⬇ Installieren», Frage mit Grösse), mit Fortsetzen, Fortschritt, freiem
#     Platz (immer tausch_free_gb frei, Standard 2 GB, wie Datentausch und BioCLIP) und harter Grösse; danach offline.
#     Entpackt nach DATA_DIR/fotaq (nicht in games/: «Spielesammlung installieren» ersetzt jenen Ordner ganz).
#   * Sprachen wählbar (Besitzer 09.11.2026): Deutsch, Englisch oder beide; die Engine kommt immer mit. Jede Sprache später einzeln
#     dazu oder weg (die letzte weg = alles weg). fotaq.ok (JSON) nennt jeden geprüften Teil; data/games/index.json nur die
#     installierten Sprachen – die Startseite bietet nur diese an.
#   * Gespielt über den Spiele-Port wie die anderen Spiele (/g/fotaq/, eigener «origin»), Kachel in der Gruppe «👆 Touch»:
#     Antippen = Klick, lange drücken / «🖱 Rechts» = Rechtsklick, «☰ Menü» = Tagebuch des Spiels (Speichern, Laden, Optionen),
#     «⏭ Weiter» = überspringen; die Leiste liegt neben dem Spiel, «✕ Zurück» von MoveEye ist durch den eigenen «‹» ersetzt.
#     Spielstände: IndexedDB des Browsers (ScummVM-IDBFS, pro Sprache ein Ordner), bleiben nach dem Neuladen.
#   * Lizenz: Freeware (Readme + Copyright bei den Daten, nicht einzeln verkaufen), ScummVM GPL v3+ (Quelle: Tag + Patches +
#     Workflow, öffentlich), Zeile auf der Startseite und in games/LIZENZEN.txt, Lizenztexte im Paket (lizenzen/, LIZENZEN.txt).
# Selbsttest fotaq_selftest; Tests werkzeuge/spiele_test.py --fotaq-moveeye (Laden, Prüfsumme, Platz, Port, Kachel) und
# --nur-fotaq (das Spiel im Browser, Handy / iPad / PC, DE und EN).
# ----------------------------------------------------------------------------
FOTAQ_TAG = "fotaq-1"
FOTAQ_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + FOTAQ_TAG + "/"}   # Tests: lokaler Server
# Werte aus dem Workflow «FOTAQ» (pins.txt / Release-Notiz von FOTAQ_TAG); size 0 = noch nicht freigegeben (kommt mit einem Update).
FOTAQ_FILES = {
    "engine": {"name": "fotaq-engine-1.zip", "size": 0, "sha256": "", "unpacked": 0},
    "de": {"name": "fotaq-de-1.zip", "size": 0, "sha256": "", "unpacked": 0},
    "en": {"name": "fotaq-en-1.zip", "size": 0, "sha256": "", "unpacked": 0},
}
FOTAQ_MAX_BYTES = 400 * 1024 * 1024      # harte Obergrenze für die drei ZIP und für das Entpackte (je)
FOTAQ_GAME = {"dir": "fotaq", "start": "index.html", "icon": "thumb.svg", "input": "touch",
              "name": "Flight of the Amazon Queen",
              "desc": "Abenteuer-Klassiker (1995) mit Sprachausgabe – Deutsch oder Englisch.",
              "names": {L: "Flight of the Amazon Queen" for L in ("de", "en", "fr", "it", "rm")},
              "descs": {"de": "Abenteuer-Klassiker (1995) mit Sprachausgabe – Deutsch oder Englisch.",
                        "en": "Classic adventure (1995) with speech – German or English.",
                        "fr": "Jeu d’aventure classique (1995) avec voix – allemand ou anglais.",
                        "it": "Avventura classica (1995) con voci – tedesco o inglese.",
                        "rm": "Gieu d’aventura classic (1995) cun vusch – tudestg u englais."}}
FOTAQ_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}


def fotaq_dir():
    return os.path.join(DATA_DIR, "fotaq")


def fotaq_dl_dir():
    return os.path.join(DATA_DIR, "fotaq_dl")


def fotaq_pinned():
    """every file has an exact size and a sha256 - nothing else is ever downloaded"""
    for f in FOTAQ_FILES.values():
        if not isinstance(f.get("size"), int) or not 0 < f["size"] <= FOTAQ_MAX_BYTES or not re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or "")):
            return False
        if not isinstance(f.get("unpacked"), int) or not 0 < f["unpacked"] <= FOTAQ_MAX_BYTES:
            return False
        if not re.fullmatch(r"fotaq-[a-z]+-\d{1,3}\.zip", f.get("name") or ""):
            return False
    return True


def fotaq_total():
    return sum(int(f.get("size") or 0) for f in FOTAQ_FILES.values())


def fotaq_unpacked():
    return sum(int(f.get("unpacked") or 0) for f in FOTAQ_FILES.values())


FOTAQ_LANGS = ("de", "en")
FOTAQ_LANG_NAMES = {"de": "Deutsch", "en": "English"}


def _fotaq_ok_read():
    """marker fotaq.ok (JSON): tag + sha256 of every part that was unpacked and checked ({"engine": …, "de": …})"""
    try:
        with open(os.path.join(fotaq_dir(), "fotaq.ok"), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) and d.get("tag") == FOTAQ_TAG and isinstance(d.get("parts"), dict) else {}
    except (OSError, ValueError):
        return {}


def _fotaq_ok_write(parts):
    with open(os.path.join(fotaq_dir(), "fotaq.ok.new"), "w", encoding="utf-8") as fh:
        json.dump({"tag": FOTAQ_TAG, "parts": parts}, fh)
    os.replace(os.path.join(fotaq_dir(), "fotaq.ok.new"), os.path.join(fotaq_dir(), "fotaq.ok"))


def _fotaq_part_ok(parts, k):
    return parts.get(k) == FOTAQ_FILES[k]["sha256"] and (k == "engine" or os.path.isdir(os.path.join(fotaq_dir(), "data", "games", k)))


def fotaq_langs():
    """the installed languages (checked once after the download)"""
    if not fotaq_pinned():
        return []
    parts = _fotaq_ok_read().get("parts") or {}
    if not _fotaq_part_ok(parts, "engine"):
        return []
    return [L for L in FOTAQ_LANGS if _fotaq_part_ok(parts, L)]


def fotaq_installed():
    """engine + at least one language unpacked and checked (then the tile is there)"""
    d = fotaq_dir()
    return bool(fotaq_langs()) and all(os.path.isfile(os.path.join(d, f)) for f in ("index.html", "scummvm.js", "scummvm.wasm", "thumb.svg"))


def _fotaq_games_index(root, langs):
    """data/games/index.json of the HTTP filesystem of ScummVM: only the languages that are there (the start page reads it too)"""
    p = os.path.join(root, "data", "games", "index.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".new", "w", encoding="utf-8") as fh:
        json.dump({L: {} for L in langs}, fh)
    os.replace(p + ".new", p)


def _fotaq_unzip(zp, dest, limit, prefix=""):
    """one ZIP of the package into dest: only plain names below the folder (and below «prefix»), no links, at most «limit» bytes"""
    tot = 0
    with zipfile.ZipFile(zp) as z:
        infos = z.infolist()
        for i in infos:
            n = i.filename
            if n.startswith("/") or "\\" in n or ".." in n.split("/") or not re.fullmatch(r"[A-Za-z0-9._ /+-]{1,200}", n):
                raise ValueError("bad file name in the package")
            if prefix and not n.startswith(prefix):
                raise ValueError("unexpected file in the package")
            if (i.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("link in the package")
            tot += i.file_size
        if tot > limit + 1024:
            raise ValueError("package larger than announced")
        for i in infos:
            if i.is_dir():
                continue
            p = os.path.join(dest, *i.filename[len(prefix):].split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with z.open(i) as src, open(p, "wb") as out:
                while True:
                    if FOTAQ_DL.get("stop"):
                        raise InterruptedError("cancelled")
                    b = src.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
    return tot


def fotaq_need(langs):
    """the parts a choice still needs (engine only when it is not there yet): (parts, download bytes, unpacked bytes)"""
    have = fotaq_langs()
    eng = bool(have)
    parts = ([] if eng else ["engine"]) + [L for L in FOTAQ_LANGS if L in langs and L not in have]
    return parts, sum(FOTAQ_FILES[k]["size"] for k in parts), sum(FOTAQ_FILES[k]["unpacked"] for k in parts)


def fotaq_download(langs=FOTAQ_LANGS, wait=False):
    """load and unpack the engine (when missing) and the chosen languages (background); (ok, error)"""
    if not fotaq_pinned():
        return False, "comes with an update"
    langs = [L for L in FOTAQ_LANGS if L in (langs or ())]
    if not langs:
        return False, "choose at least one language"
    if FOTAQ_DL["running"]:
        return True, ""
    parts, size, unz = fotaq_need(langs)
    if not [k for k in parts if k != "engine"]:
        return True, ""                                          # all chosen languages are there already
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 1 << 40
    dd = fotaq_dl_dir()
    have = sum(os.path.getsize(p) for p in (os.path.join(dd, FOTAQ_FILES[k]["name"] + x) for k in parts for x in ("", ".part")) if os.path.isfile(p))
    if free - (size - have + unz) < bio_free_need():
        return False, "not enough free space on the memory card"
    FOTAQ_DL.update(running=True, got=0, total=size, msg="", stop=False, done=False, phase="load")

    def work():
        new_root = "engine" in parts
        tmp = fotaq_dir() + ".new"
        done = []
        try:
            os.makedirs(dd, exist_ok=True)
            for k in parts:
                f = FOTAQ_FILES[k]
                dest = os.path.join(dd, f["name"])
                if os.path.isfile(dest) and piper_check_file(dest, f)[0]:
                    FOTAQ_DL["got"] += f["size"]; continue
                bio_fetch(FOTAQ_BASE["url"] + f["name"], dest, f, FOTAQ_DL)      # 639zzd: resume, exact size + sha256
            FOTAQ_DL["phase"] = "unpack"
            if new_root:                                          # first time: everything in a new folder, then swapped in
                shutil.rmtree(tmp, ignore_errors=True)
                os.makedirs(tmp)
                _fotaq_unzip(os.path.join(dd, FOTAQ_FILES["engine"]["name"]), tmp, FOTAQ_FILES["engine"]["unpacked"])
                with open(os.path.join(tmp, "fotaq.json"), encoding="utf-8") as fh:
                    man = json.load(fh)
                if man.get("tag") != FOTAQ_TAG:
                    raise ValueError("the package is not " + FOTAQ_TAG)
                for L in FOTAQ_LANGS:                             # a language only comes from its own ZIP
                    shutil.rmtree(os.path.join(tmp, "data", "games", L), ignore_errors=True)
                shutil.rmtree(fotaq_dir(), ignore_errors=True)
                os.replace(tmp, fotaq_dir())
                _fotaq_ok_write({"engine": FOTAQ_FILES["engine"]["sha256"]})
            for L in [k for k in parts if k != "engine"]:          # each language: own folder, swapped in when complete
                g = os.path.join(fotaq_dir(), "data", "games")
                lt = os.path.join(g, L + ".new")
                shutil.rmtree(lt, ignore_errors=True)
                os.makedirs(lt)
                _fotaq_unzip(os.path.join(dd, FOTAQ_FILES[L]["name"]), lt, FOTAQ_FILES[L]["unpacked"], prefix="data/games/%s/" % L)
                shutil.rmtree(os.path.join(g, L), ignore_errors=True)
                os.replace(lt, os.path.join(g, L))
                pr = _fotaq_ok_read().get("parts") or {}
                pr[L] = FOTAQ_FILES[L]["sha256"]
                _fotaq_ok_write(pr)
                done.append(L)
                try:
                    os.remove(os.path.join(dd, FOTAQ_FILES[L]["name"]))
                except OSError:
                    pass
            _fotaq_games_index(fotaq_dir(), fotaq_langs())
            if fotaq_langs():
                shutil.rmtree(dd, ignore_errors=True)             # the ZIP are not needed any more
            FOTAQ_DL["done"] = True
            log_event("sys", f"Flight of the Amazon Queen: {', '.join(FOTAQ_LANG_NAMES[L] for L in done)} installed ({FOTAQ_TAG})")
        except InterruptedError:
            FOTAQ_DL["msg"] = "cancelled"
        except Exception as e:
            FOTAQ_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Flight of the Amazon Queen not installed: {FOTAQ_DL['msg']}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            for L in FOTAQ_LANGS:
                shutil.rmtree(os.path.join(fotaq_dir(), "data", "games", L + ".new"), ignore_errors=True)
            if os.path.isdir(fotaq_dir()) and not fotaq_langs():   # engine without any language: nothing to play, nothing kept
                shutil.rmtree(fotaq_dir(), ignore_errors=True)
            FOTAQ_DL.update(running=False, phase="")
    if wait:
        work()
        return (not FOTAQ_DL["msg"]), FOTAQ_DL["msg"]
    threading.Thread(target=work, daemon=True, name="fotaq-dl").start()
    return True, ""


def fotaq_cancel():
    if FOTAQ_DL["running"]:
        FOTAQ_DL["stop"] = True
    return True, ""


def fotaq_delete():
    if FOTAQ_DL["running"]:
        return False, "busy right now - try again in a moment"
    for p in (fotaq_dir(), fotaq_dir() + ".new", fotaq_dl_dir()):
        shutil.rmtree(p, ignore_errors=True)
    log_event("sys", "Flight of the Amazon Queen deleted")
    return True, ""


def fotaq_remove_lang(L):
    """remove one language; the last one removes everything (the engine alone is no game)"""
    if FOTAQ_DL["running"]:
        return False, "busy right now - try again in a moment"
    have = fotaq_langs()
    if L not in have:
        return True, ""
    if have == [L]:
        return fotaq_delete()
    pr = _fotaq_ok_read().get("parts") or {}
    pr.pop(L, None)
    _fotaq_ok_write(pr)
    shutil.rmtree(os.path.join(fotaq_dir(), "data", "games", L), ignore_errors=True)
    _fotaq_games_index(fotaq_dir(), fotaq_langs())
    log_event("sys", f"Flight of the Amazon Queen: {FOTAQ_LANG_NAMES[L]} removed")
    return True, ""


def fotaq_state():
    """for the admin tab (Mehr → Spielecke): parts with sizes, installed languages, free space"""
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 0
    have = fotaq_langs()
    return {"pinned": fotaq_pinned(), "installed": fotaq_installed(), "langs": have, "tag": FOTAQ_TAG,
            "parts": {k: {"size": f["size"], "unpacked": f["unpacked"]} for k, f in FOTAQ_FILES.items()},
            "engine": bool(have), "size": fotaq_total(), "unpacked": fotaq_unpacked(), "free": free, "free_need": bio_free_need(),
            "dl": {k: FOTAQ_DL[k] for k in ("running", "got", "total", "msg", "done", "phase")}}


def fotaq_action(a, d=None):
    """the admin buttons: install (languages) / cancel / delete / remove one language; (ok, error)"""
    d = d or {}
    if a == "fotaq_install":
        ls = d.get("langs")
        return fotaq_download(ls if isinstance(ls, list) else list(FOTAQ_LANGS))
    if a == "fotaq_cancel":
        return fotaq_cancel()
    if a == "fotaq_delete":
        return fotaq_delete()
    if a == "fotaq_remove":
        return fotaq_remove_lang(str(d.get("lang") or ""))
    return False, "unknown action"


# ---- the game collection: FOTAQ as one more game (own folder, games port /g/fotaq/) ------------------------------------------------
_games_list_639zzg = games_list


# wraps: games_list
def games_list(extra=True):                                 # + 639zzg: FOTAQ when installed (extra=False: only the collection)
    gl = _games_list_639zzg()
    if extra and fotaq_installed():
        gl = [x for x in gl if x.get("dir") != FOTAQ_GAME["dir"]] + [dict(FOTAQ_GAME)]
    return gl


_games_file_639zzg = games_file


# wraps: games_file
def games_file(game, fn):                                   # + 639zzg: the files of FOTAQ come from DATA_DIR/fotaq
    if game != FOTAQ_GAME["dir"]:
        return _games_file_639zzg(game, fn)
    if not fotaq_installed():
        return None
    base = os.path.realpath(fotaq_dir())
    p_ = os.path.realpath(os.path.join(base, fn or FOTAQ_GAME["start"]))
    if not p_.startswith(base + os.sep) or not os.path.isfile(p_) or os.path.basename(p_) in ("fotaq.ok", "fotaq.ok.new") or ".new" + os.sep in p_[len(base):] + os.sep:
        return None
    return p_


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -----------------------------------------------------------------
_HX_FOTAQ = {
    "comes with an update": ("kommt mit einem Update", "arrive avec une mise à jour", "arriva con un aggiornamento", "vegn cun in update"),
    "Adventure with speech, German or English. Loaded once from GitHub (fixed checksum), then it runs offline in the browser (ScummVM).": (
        "Abenteuer mit Sprachausgabe, Deutsch oder Englisch. Wird einmal von GitHub geladen (feste Prüfsumme), läuft danach offline im Browser (ScummVM).",
        "Aventure avec voix, allemand ou anglais. Chargé une fois depuis GitHub (somme de contrôle fixe), puis il tourne hors ligne dans le navigateur (ScummVM).",
        "Avventura con voci, tedesco o inglese. Caricata una volta da GitHub (somma di controllo fissa), poi funziona offline nel browser (ScummVM).",
        "Aventura cun vusch, tudestg u englais. Vegn chargiada ina giada da GitHub (summa da controlla fixa), lura funcziuna offline en il navigatur (ScummVM)."),
    "Install": ("Installieren", "Installer", "Installa", "Installar"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "installed": ("installiert", "installé", "installato", "installà"),
    "unpacking …": ("entpacken …", "décompression …", "estrazione …", "decumprimer …"),
    "cancelled": ("abgebrochen", "annulé", "annullato", "interrut"),
    "not enough free space on the memory card": ("zu wenig Platz auf der Speicherkarte", "pas assez de place sur la carte mémoire",
                                                 "spazio insufficiente sulla scheda di memoria", "memia pauc plaz sin la carta da memoria"),
    "choose at least one language": ("mindestens eine Sprache wählen", "choisir au moins une langue", "scegliere almeno una lingua", "tscherner almain ina lingua"),
    "Add": ("Dazu laden", "Ajouter", "Aggiungi", "Agiuntar"),
    "Languages:": ("Sprachen:", "Langues :", "Lingue:", "Linguas:"),
    "fotaq-ask": ("«Flight of the Amazon Queen» jetzt laden? %s MB von GitHub (danach %s MB auf der Speicherkarte, 2 GB bleiben frei).",
                  "Charger «Flight of the Amazon Queen» maintenant ? %s Mo depuis GitHub (ensuite %s Mo sur la carte, 2 Go restent libres).",
                  "Caricare «Flight of the Amazon Queen» adesso? %s MB da GitHub (poi %s MB sulla scheda, 2 GB restano liberi).",
                  "Chargiar «Flight of the Amazon Queen» uss? %s MB da GitHub (lura %s MB sin la carta, 2 GB restan libers)."),
    "fotaq-del-lang": ("Diese Sprache entfernen? Die Spielstände bleiben in den Browsern.", "Supprimer cette langue ? Les sauvegardes restent dans les navigateurs.",
                       "Rimuovere questa lingua? I salvataggi restano nei browser.", "Allontanar questa lingua? Ils stadis da gieu restan en ils navigaturs."),
    "fotaq-del": ("«Flight of the Amazon Queen» entfernen? Die Spielstände bleiben in den Browsern.",
                  "Supprimer «Flight of the Amazon Queen» ? Les sauvegardes restent dans les navigateurs.",
                  "Rimuovere «Flight of the Amazon Queen»? I salvataggi restano nei browser.",
                  "Allontanar «Flight of the Amazon Queen»? Ils stadis da gieu restan en ils navigaturs."),
}
for _k, _v in _HX_FOTAQ.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
FOTAQ_JS_DE = {_k: _v[0] for _k, _v in _HX_FOTAQ.items()}
FOTAQ_JS_EN = {"fotaq-ask": "Load «Flight of the Amazon Queen» now? %s MB from GitHub (then %s MB on the memory card, 2 GB stay free).",
               "fotaq-del": "Remove «Flight of the Amazon Queen»? The saved games stay in the browsers.",
               "fotaq-del-lang": "Remove this language? The saved games stay in the browsers."}
TOOLS_PAGE = TOOLS_PAGE.replace("/*FOTAQ_I18N*/", "Object.assign(I18N.de," + json.dumps(FOTAQ_JS_DE, ensure_ascii=False) + ");"
                                "I18N.en=I18N.en||{};Object.assign(I18N.en," + json.dumps(FOTAQ_JS_EN, ensure_ascii=False) + ");", 1)

# ---- the manual: one point in the section «Spiele freigeben» (5 languages), with the licences -------------------------------------
_HELP_FOTAQ = {
    "de": '<li><b>🛩 Flight of the Amazon Queen</b> (Abenteuer von 1995, CD-Fassung mit Sprachausgabe, Deutsch oder Englisch): einmal laden unter Mehr → Spielecke: Sprache wählen (Deutsch etwa 120 MB, Englisch etwa 63 MB, beide 172 MB von GitHub, feste Prüfsumme, 2 GB bleiben frei), jede Sprache später einzeln dazu oder weg, danach als Kachel in der Spielesammlung, auch ohne Internet. Antippen = Klick, lange drücken oder «🖱 Rechts» = Rechtsklick, «☰ Menü» = Speichern, Laden, Lautstärke. Spielstände bleiben im Browser des Geräts. Am Handy quer halten. Auf dem Handy braucht das Spiel viel Speicher (Deutsch ~110 MB Daten), ältere Geräte schaffen es eventuell nicht. <b>Lizenz:</b> Spiel © 1995 John Passfield &amp; Steven Stamatiadis, Freeware (Readme bei den Daten); ScummVM © The ScummVM Team, GPL v3 – Quellcode und Bau-Ablauf: Link auf der Startseite des Spiels.</li>',
    "en": '<li><b>🛩 Flight of the Amazon Queen</b> (adventure from 1995, CD version with speech, German or English): load it once under More → Game corner: choose the languages (German about 120 MB, English about 63 MB, both 172 MB from GitHub, fixed checksum, 2 GB stay free), add or remove each language later, then it is a tile in the game collection, also without internet. Tap = click, long press or «🖱 Right» = right click, «☰ Menu» = save, load, volume. Saved games stay in the browser of the device. Hold the phone sideways. On phones the game needs a lot of memory (German ~110 MB of data), older devices may not manage. <b>Licence:</b> game © 1995 John Passfield &amp; Steven Stamatiadis, freeware (readme with the data); ScummVM © The ScummVM Team, GPL v3 – source code and build: link on the start page of the game.</li>',
    "fr": '<li><b>🛩 Flight of the Amazon Queen</b> (aventure de 1995, version CD avec voix, allemand ou anglais) : charger une fois sous Plus → Coin jeux → « ⬇ Installer » (env. 170 Mo depuis GitHub, somme fixe, 2 Go restent libres), ensuite une tuile de la collection, aussi sans Internet. Toucher = clic, appui long ou « 🖱 Droite » = clic droit, « ☰ Menu » = sauvegarder, charger. <b>Licence :</b> jeu © 1995 John Passfield &amp; Steven Stamatiadis, freeware ; ScummVM © The ScummVM Team, GPL v3 (source : lien sur la page du jeu).</li>',
    "it": '<li><b>🛩 Flight of the Amazon Queen</b> (avventura del 1995, versione CD con voci, tedesco o inglese): caricare una volta sotto Altro → Angolo giochi → «⬇ Installa» (circa 170 MB da GitHub, somma fissa, 2 GB restano liberi), poi è una tessera della raccolta, anche senza Internet. Toccare = clic, pressione lunga o «🖱 Destro» = clic destro, «☰ Menu» = salvare, caricare. <b>Licenza:</b> gioco © 1995 John Passfield &amp; Steven Stamatiadis, freeware; ScummVM © The ScummVM Team, GPL v3 (sorgente: link sulla pagina del gioco).</li>',
    "rm": '<li><b>🛩 Flight of the Amazon Queen</b> (aventura da 1995, versiun CD cun vusch, tudestg u englais): chargiar ina giada sut Dapli → Chantun da gieus → «⬇ Installar» (var 170 MB da GitHub, summa fixa, 2 GB restan libers), lura ina cachel da la collecziun, er senza internet. Tutgar = clic, smatgar ditg u «🖱 Dretg» = clic dretg, «☰ Menu» = memorisar, chargiar. <b>Licenza:</b> gieu © 1995 John Passfield &amp; Steven Stamatiadis, freeware; ScummVM © The ScummVM Team, GPL v3 (code: link sin la pagina dal gieu).</li>',
}


def _help_fotaq(doc, lang):
    i = doc.find('<section id="games"')
    if i < 0 or "Amazon Queen" in doc[i:doc.find("</section>", i)]:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + _HELP_FOTAQ[lang] + doc[j:] if j > 0 else doc


_hp_en_fotaq = HELP_PAGE.find('<div lang="en">')
if _hp_en_fotaq > 0:
    HELP_PAGE = _help_fotaq(HELP_PAGE[:_hp_en_fotaq], "de") + _help_fotaq(HELP_PAGE[_hp_en_fotaq:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_fotaq(HELP_X[_L], _L)


# ---- self-test (without the package; werkzeuge/spiele_test.py --fotaq-moveeye tests loading, the port and the tile) ---------------
def fotaq_selftest():
    assert FOTAQ_BASE["url"] == "https://github.com/DonElektro/MotionWatch/releases/download/" + FOTAQ_TAG + "/"
    assert re.fullmatch(r"fotaq-\d{1,3}", FOTAQ_TAG)
    n = FOTAQ_TAG.split("-")[1]
    assert all(f["name"] == "fotaq-%s-%s.zip" % (k, n) for k, f in FOTAQ_FILES.items()), "FOTAQ_FILES: names fit FOTAQ_TAG"
    assert fotaq_pinned() or all(not f["size"] and not f["sha256"] for f in FOTAQ_FILES.values()), "FOTAQ_FILES: either all pins or none"
    assert fotaq_total() <= 3 * FOTAQ_MAX_BYTES
    assert FOTAQ_GAME["input"] in GAME_GROUPS and FOTAQ_GAME["icon"] == "thumb.svg"
    assert all(FOTAQ_GAME["names"].get(L) and FOTAQ_GAME["descs"].get(L) for L in ("de", "en", "fr", "it", "rm"))
    assert FOTAQ_GAME["desc"] == FOTAQ_GAME["descs"]["de"]
    assert "Amazon Queen" in HELP_PAGE and all("Amazon Queen" in HELP_X.get(L, "Amazon Queen") for L in ("fr", "it", "rm"))
    assert "fotaqPaint" in TOOLS_PAGE and "/*FOTAQ_I18N*/" not in TOOLS_PAGE
    if not fotaq_installed():
        assert all(x.get("dir") != "fotaq" for x in games_list()) and games_file("fotaq", "index.html") is None
    assert games_file("fotaq", "../settings.json") is None and games_file("fotaq", "/etc/passwd") is None
    return True


SELFTEST_EXTRA.append(("Flight of the Amazon Queen in the game corner (ScummVM, 639zzg)", fotaq_selftest))
