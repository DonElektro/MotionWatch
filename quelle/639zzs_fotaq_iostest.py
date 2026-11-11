#@ MoveEye – Teil 639zzs: «Queen – iPhone-Test»: Test-Varianten der Engine von «Flight of the Amazon Queen» für iPhone / iPad (Spieldaten in Stücken, kleine Funktionen), als eigener Eintrag nur für den Admin neben dem Spiel – ersetzt nichts. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (11.11.2026): «das Game Queen noch einmal reparieren … zerstückeln». Auf iPhone / iPad stürzt Safari
# nach etwa einer Minute ab (3.70.2: Warnseite). Vermutete Ursachen, beide nie auf einem Gerät geprüft:
#   1. Speicher für die Daten: ScummVM lud queen.1c ganz (Deutsch 108 MB) – einmal im Browser, einmal im Speicher des
#      Programms, einmal im Datei-Speicher: rund das Dreifache.
#   2. WebKit-Fehler 304810: Safaris zweiter Übersetzer (OMG) braucht für grosse, von Asyncify umgebaute Funktionen
#      Gigabytes; die Seite wird beendet. In fotaq-1 sind 7 Funktionen zwischen 40 und 160 KB.
# Das Testpaket (Workflow «FOTAQ», Job «ios», werkzeuge/fotaq/ios/, Varianten in bauen.sh) enthält die Engine in Varianten und
# eine Startseite mit Diagnose-Zeile (Gerät, Variante, Schritt 1–3, Speicher, Laufzeit; der letzte Lauf bleibt stehen, auch
# nach einem Absturz). Es hat KEINE Spieldaten: die kommen aus dem installierten Spiel (DATA_DIR/fotaq/data/games), in
# Stücken über den Spiele-Port (340: «Range»).
#   * Ein Release-Asset an «FQT_TAG» (Vorabversion «fotaqios-N», nie «latest»), Grösse + sha256 hier in der (signierten)
#     Hauptdatei. Laden nur durch den Admin (Mehr → Spielecke, im Kasten des Spiels), nur wenn das Spiel installiert ist.
#     Entpackt nach DATA_DIR/fotaqtest.
#   * Keine Kachel: nur der Admin sieht den Eintrag und den Knopf «▶ Test öffnen» (Spiele-Port /g/fotaqtest/). Die Warnseite
#     des Spiels (start.html, 639zzg) bleibt; der Test geht daran vorbei. Spielstände: dieselben wie im Spiel (gleicher Ursprung).
#   * Rückbau: diese Datei löschen (und den «Range»-Abschnitt in 340 – der schadet aber nicht).
# Selbsttest fqt_selftest; Tests werkzeuge/fotaq_iostest.py (--moveeye: Laden, Pins, Port, Stücke; --paket: die Varianten im Browser).
# ----------------------------------------------------------------------------
FQT_TAG = "fotaqios-0"                   # the probe release of the workflow «FOTAQ» (job «ios»); N of the file = N of the tag
FQT_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + FQT_TAG + "/"}   # tests: local server
# values from pins.txt of the probe release; size 0 = not released yet («comes with an update»)
FQT_FILE = {"name": "fotaq-iostest-0.zip", "size": 0, "sha256": "", "unpacked": 0}
FQT_MAX_BYTES = 80 * 1024 * 1024
FQT_GAME = "fotaqtest"
FQT_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
FQT_HIDE = ("fotaqtest.ok", "fotaqtest.ok.new")


def fqt_dir():
    return os.path.join(DATA_DIR, "fotaqtest")


def fqt_pinned():
    f = FQT_FILE
    return (isinstance(f.get("size"), int) and 0 < f["size"] <= FQT_MAX_BYTES and bool(re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or "")))
            and isinstance(f.get("unpacked"), int) and 0 < f["unpacked"] <= FQT_MAX_BYTES
            and f.get("name") == "fotaq-iostest-%s.zip" % FQT_TAG.split("-")[1])


def fqt_installed():
    """the test package is unpacked and checked (marker fotaqtest.ok) - and the game itself is there (it has the data)"""
    if not fqt_pinned() or not fotaq_installed():
        return False
    try:
        with open(os.path.join(fqt_dir(), "fotaqtest.ok"), encoding="utf-8") as fh:
            ok_ = json.load(fh)
    except (OSError, ValueError):
        return False
    return (isinstance(ok_, dict) and ok_.get("tag") == FQT_TAG and ok_.get("sha256") == FQT_FILE["sha256"]
            and os.path.isfile(os.path.join(fqt_dir(), "index.html")))


def fqt_download(wait=False):
    """load and unpack the test package (background); (ok, error)"""
    if not fqt_pinned():
        return False, "comes with an update"
    if not fotaq_installed():
        return False, "install the game first"
    if FQT_DL["running"] or fqt_installed():
        return True, ""
    f = FQT_FILE
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 1 << 40
    if free - (f["size"] + f["unpacked"]) < bio_free_need():
        return False, "not enough free space on the memory card"
    FQT_DL.update(running=True, got=0, total=f["size"], msg="", stop=False, done=False, phase="load")

    def work():
        tmp = fqt_dir() + ".new"
        dest = os.path.join(DATA_DIR, f["name"])
        try:
            bio_fetch(FQT_BASE["url"] + f["name"], dest, f, FQT_DL)        # 639zzd: resume, exact size + sha256
            FQT_DL["phase"] = "unpack"
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            _fotaq_unzip(dest, tmp, f["unpacked"])
            with open(os.path.join(tmp, "fotaqtest.json"), encoding="utf-8") as fh:
                man = json.load(fh)
            if man.get("tag") != FQT_TAG or os.path.exists(os.path.join(tmp, "data", "games")):
                raise ValueError("the package is not " + FQT_TAG)
            with open(os.path.join(tmp, "fotaqtest.ok"), "w", encoding="utf-8") as fh:
                json.dump({"tag": FQT_TAG, "sha256": f["sha256"]}, fh)
            shutil.rmtree(fqt_dir(), ignore_errors=True)
            os.replace(tmp, fqt_dir())
            FQT_DL["done"] = True
            log_event("sys", f"Flight of the Amazon Queen: iPhone test installed ({FQT_TAG})")
        except Exception as e:
            FQT_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Flight of the Amazon Queen: iPhone test not installed: {FQT_DL['msg']}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            for p in (dest, dest + ".part"):
                if FQT_DL["done"] or FQT_DL["msg"]:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            FQT_DL.update(running=False, phase="")
    if wait:
        work()
        return (not FQT_DL["msg"]), FQT_DL["msg"]
    threading.Thread(target=work, daemon=True, name="fotaqtest-dl").start()
    return True, ""


def fqt_delete():
    if FQT_DL["running"]:
        return False, "busy right now - try again in a moment"
    for p in (fqt_dir(), fqt_dir() + ".new"):
        shutil.rmtree(p, ignore_errors=True)
    log_event("sys", "Flight of the Amazon Queen: iPhone test deleted")
    return True, ""


def fqt_state():
    return {"tag": FQT_TAG, "pinned": fqt_pinned(), "installed": fqt_installed(), "game": fotaq_installed(), "size": FQT_FILE["size"],
            "unpacked": FQT_FILE["unpacked"], "dl": {k: FQT_DL[k] for k in ("running", "got", "total", "msg", "done", "phase")}}


# ---- actions and state ride on those of 639zzg (field «iostest»), like the ready-made games (639zzn, field «fs») ------------------
_fotaq_action_639zzs = fotaq_action


# wraps: fotaq_action
def fotaq_action(a, d=None):                                # + 639zzs: with «iostest»: true the action is for the test package
    d = d or {}
    if not d.get("iostest"):
        return _fotaq_action_639zzs(a, d)
    if a == "fotaq_install":
        return fqt_download()
    if a == "fotaq_delete":
        return fqt_delete()
    return False, "unknown action"


_fotaq_state_639zzs = fotaq_state


# wraps: fotaq_state
def fotaq_state():                                          # + 639zzs: the test package in the same answer of /api/party
    s_ = _fotaq_state_639zzs()
    s_["iostest"] = fqt_state()
    return s_


_games_file_639zzs = games_file


# wraps: games_file
def games_file(game, fn):                                   # + 639zzs: /g/fotaqtest/ = the test package, its game data = those of the game
    if game != FQT_GAME:
        return _games_file_639zzs(game, fn)
    if not fqt_installed():
        return None
    fn = fn or "index.html"
    if fn.startswith("data/games/"):                        # the data of the installed game (639zzg checks the path)
        return _games_file_639zzs(FOTAQ_GAME["dir"], fn)
    base = os.path.realpath(fqt_dir())
    p_ = os.path.realpath(os.path.join(base, fn))
    if not p_.startswith(base + os.sep) or not os.path.isfile(p_) or os.path.basename(p_) in FQT_HIDE:
        return None
    return p_


# ---- texts ------------------------------------------------------------------------------------------------------------------------
_HX_FQT = {
    "iPhone test": ("iPhone-Test", "Test iPhone", "Test iPhone", "Test iPhone"),
    "Test versions of the game for iPhone/iPad (game data in pieces, smaller program). They do not replace the game. Open the test on the iPhone, try A and B, and send a picture of the line at the bottom.": (
        "Test-Fassungen des Spiels für iPhone/iPad (Spieldaten in Stücken, kleineres Programm). Sie ersetzen das Spiel nicht. Den Test am iPhone öffnen, A und B probieren und ein Bild der Zeile unten schicken.",
        "Versions de test du jeu pour iPhone/iPad (données en morceaux, programme plus petit). Elles ne remplacent pas le jeu. Ouvrir le test sur l’iPhone, essayer A et B et envoyer une image de la ligne du bas.",
        "Versioni di prova del gioco per iPhone/iPad (dati a pezzi, programma più piccolo). Non sostituiscono il gioco. Aprire la prova sull’iPhone, provare A e B e inviare un’immagine della riga in basso.",
        "Versiuns da test dal gieu per iPhone/iPad (datas en tocs, program pli pitschen). Ellas na remplazzan betg il gieu. Avrir il test sin l’iPhone, empruvar A e B e trametter in maletg da la lingia giusut."),
    "Open the test": ("Test öffnen", "Ouvrir le test", "Apri la prova", "Avrir il test"),
    "install the game first": ("zuerst das Spiel installieren", "installer d’abord le jeu", "installare prima il gioco", "l’emprim installar il gieu"),
    "fqt-ask": ("Den iPhone-Test laden? %s MB von GitHub. Das Spiel selbst bleibt unverändert.", "Charger le test iPhone ? %s Mo depuis GitHub. Le jeu reste inchangé.",
                "Caricare la prova per iPhone? %s MB da GitHub. Il gioco resta invariato.", "Chargiar il test iPhone? %s MB da GitHub. Il gieu resta senza midadas."),
}
for _k, _v in _HX_FQT.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
FQT_JS_DE = {_k: _v[0] for _k, _v in _HX_FQT.items()}
FQT_JS_EN = {"fqt-ask": "Load the iPhone test? %s MB from GitHub. The game itself stays unchanged."}

# ---- admin tab Mehr → Spielecke: one more block in the box of the game (only when the game is installed) -------------------------
FQT_TOOLS_JS = r"""// 639zzs: «Queen – iPhone-Test» (test versions of the engine, only for the administrator; replaces nothing)
function fqtPaint(S) {
  const box = document.getElementById("fotaq-box");
  if (!box || !S || !S.game) return;
  const MB = n => Math.max(1, Math.round((n || 0) / 1e6)), D = S.dl || {};
  const r = el("div", ""); r.id = "fqt-box"; r.style.cssText = "margin-top:12px;padding-top:10px;border-top:1px solid var(--line)";
  r.appendChild(el("b", "", "🧪 Queen – " + t("iPhone test")));
  r.appendChild(el("div", "mut", t("Test versions of the game for iPhone/iPad (game data in pieces, smaller program). They do not replace the game. Open the test on the iPhone, try A and B, and send a picture of the line at the bottom.")));
  const row = el("div", "trow"); row.style.marginTop = "8px";
  if (D.running) {
    row.appendChild(el("span", "", D.phase === "unpack" ? "⏳ " + t("unpacking …") : "⏳ " + MB(D.got) + " / " + MB(D.total) + " MB"));
  } else if (!S.pinned) {
    row.appendChild(el("span", "mut", t("comes with an update")));
  } else if (S.installed) {
    const pl = el("a", "btn", "▶ " + t("Open the test")); pl.id = "fqt-open"; pl.href = "/games/fotaqtest/"; pl.target = "_blank";
    const db = el("button", "sec", "🗑 " + t("Remove")); db.type = "button"; db.id = "fqt-del"; db.onclick = () => partyDo({action: "fotaq_delete", iostest: true});
    row.append(el("span", "", "✓ " + t("installed") + " (" + S.tag + ")"), pl, db);
  } else {
    const ib = el("button", "", "⬇ " + t("Install") + " (" + MB(S.size) + " MB)"); ib.type = "button"; ib.id = "fqt-install";
    ib.onclick = () => { if (confirm(t("fqt-ask").replace("%s", MB(S.size)))) partyDo({action: "fotaq_install", iostest: true}); };
    row.appendChild(ib);
  }
  r.appendChild(row);
  if (D.msg && !D.running) r.appendChild(el("div", "mut", "⚠ " + t(D.msg)));
  box.appendChild(r);
}
"""
_FQT_HOOK = "  fotaqPaint(box, P.fotaq);\n"
if TOOLS_PAGE.count(_FQT_HOOK) == 1 and "function fqtPaint" not in TOOLS_PAGE:
    TOOLS_PAGE = TOOLS_PAGE.replace(_FQT_HOOK, _FQT_HOOK + "  fqtPaint((P.fotaq || {}).iostest);\n", 1)
    _i = TOOLS_PAGE.find("function fotaqPaint(")
    TOOLS_PAGE = (TOOLS_PAGE[:_i] + FQT_TOOLS_JS + "Object.assign(I18N.de," + json.dumps(FQT_JS_DE, ensure_ascii=False) + ");"
                  "I18N.en=I18N.en||{};Object.assign(I18N.en," + json.dumps(FQT_JS_EN, ensure_ascii=False) + ");\n" + TOOLS_PAGE[_i:])


# ---- self-test (without the package; werkzeuge/fotaq_iostest.py --moveeye tests loading, the port and the pieces) -----------------
def fqt_selftest():
    assert FQT_BASE["url"] == "https://github.com/DonElektro/MotionWatch/releases/download/" + FQT_TAG + "/"
    assert re.fullmatch(r"fotaqios-\d{1,4}", FQT_TAG) and FQT_FILE["name"] == "fotaq-iostest-%s.zip" % FQT_TAG.split("-")[1]
    assert fqt_pinned() or (not FQT_FILE["size"] and not FQT_FILE["sha256"] and not FQT_FILE["unpacked"]), "either all pins or none"
    assert all(x.get("dir") != FQT_GAME for x in games_list()), "the test is never a tile"
    if not fqt_installed():
        assert games_file(FQT_GAME, "index.html") is None and games_file(FQT_GAME, "data/games/index.json") is None
    assert games_file(FQT_GAME, "../settings.json") is None and games_file(FQT_GAME, "fotaqtest.ok") is None
    assert fotaq_action("nope", {"iostest": True}) == (False, "unknown action") and fotaq_action("nope") == (False, "unknown action")
    s_ = fotaq_state()
    assert "pinned" in s_ and "fs" in s_ and s_["iostest"]["tag"] == FQT_TAG
    assert "function fqtPaint" in TOOLS_PAGE and "fqtPaint((P.fotaq || {}).iostest);" in TOOLS_PAGE and '"fqt-ask"' in TOOLS_PAGE
    assert "Trotzdem starten" in fotaq_start_html(), "the warning page of the game stays"
    return True


SELFTEST_EXTRA.append(("Flight of the Amazon Queen: iPhone test next to the game (639zzs)", fqt_selftest))
