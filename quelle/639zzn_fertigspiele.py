#@ MoveEye – Teil 639zzn: Fertige freie Spiele zum Nachladen in der Spielecke (Abenteuer mit Angst, Heroine Dusk …) – jedes Spiel ein eigenes Paket (Release-Asset, feste Grösse + sha256), einzeln durch den Admin geladen und entfernt, Kachel wie die anderen Spiele, Spiele-Port /g/<id>/. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (10.11.2026): fertige, frei lizenzierte Browserspiele in die Spielecke.
#   * Sie sind zusammen weit grösser als die Spielesammlung im Repository (games/MotionWatch_Spiele.zip, ~15 MB): darum der Weg
#     von «Flight of the Amazon Queen» (639zzg) – jedes Spiel ist EIN ZIP an einem Release «FS_TAG» (nie «latest»), nicht im Git.
#     Gebaut von werkzeuge/fertigspiele/paket.py (Workflow «Fertige Spiele»): Quelle = öffentliches Repository an einem festen
#     Commit, nur kopiert (kein Bau-Skript der Quelle läuft), die wenigen Änderungen stehen in LIZENZEN.txt jedes Pakets.
#     Die ZIP sind reproduzierbar (gleiche Quelle = gleiche sha256). Grösse + sha256 stehen hier in der (signierten) Hauptdatei.
#   * Laden nur durch den Admin (Mehr → Spielecke → «Weitere Spiele zum Nachladen» → «⬇ Installieren», Frage mit Grösse), mit
#     Fortsetzen, Fortschritt, freiem Platz (tausch_free_gb, Standard 2 GB) und harter Grösse; danach offline. Ein Spiel aufs Mal.
#     Entpackt nach DATA_DIR/fspiele/<id>/ (nicht in games/: «Spielesammlung installieren» ersetzt jenen Ordner ganz).
#   * Gespielt wie die anderen Spiele: Kachel in /spiele, auf der Gästeseite und im Reiter Spielecke, Dateien über games_file
#     (Spiele-Port /g/<id>/ = eigener «origin»), Knopf «✕ Zurück» von MoveEye (GAME_BACK). Der Spiel-Code bekommt keinen neuen
#     Zugriff: keine neue Schnittstelle, kein neues Recht – nur Dateien aus dem eigenen Ordner.
#   * Keine Änderung an den geteilten Teilen 320 / 340 / 460 / 550: die Aktionen laufen über die Aktionen von 639zzg
#     («fotaq_install» / «fotaq_cancel» / «fotaq_delete» mit dem Feld «fs»: <id>), der Zustand steht in fotaq_state()["fs"],
#     die Zeilen im Reiter Spielecke kommen per TOOLS_PAGE.replace dazu.
#   * Lizenzen: pro Spiel in games/LIZENZEN.txt und im Paket (LIZENZEN.txt + die Lizenz- und README-Dateien des Spiels).
# Selbsttest fs_selftest; Tests werkzeuge/spiele_test.py --fspiele-moveeye (Laden, Prüfsumme, Platz, Port, Kachel, Entfernen)
# und --nur-fspiele (die Spiele im Browser: Handy und PC, Start per Tipp, keine Fehler, nichts von aussen).
# ----------------------------------------------------------------------------
FS_TAG = "fspiele-1"
FS_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + FS_TAG + "/"}   # Tests: lokaler Server
FS_MAX_BYTES = 150 * 1024 * 1024         # harte Obergrenze pro ZIP und für das Entpackte
FS_LANGS5 = ("de", "en", "fr", "it", "rm")


def _fs_tile(gid, start, inp, name, descs, notes=None):
    """one tile like in games.json (names / descs / notes: de, en, fr, it, rm)"""
    g_ = {"dir": gid, "start": start, "icon": "thumb.png", "input": inp, "name": name, "desc": descs[0],
          "names": {L: name for L in FS_LANGS5}, "descs": dict(zip(FS_LANGS5, descs))}
    if notes:
        g_["note"] = notes[0]
        g_["notes"] = dict(zip(FS_LANGS5, notes))
    return g_


# Werte aus werkzeuge/fertigspiele/paket.py (pins.txt; der Workflow «Fertige Spiele» prüft sie vor dem Release);
# size 0 = noch nicht freigegeben (kommt mit einem Update).
FS_GAMES = {
    "fs-angst": {
        "file": {"name": "fspiele-angst-1.zip", "size": 37087772, "sha256": "ddd557dde9326dc1e0ddb1e072cfd07950a716c3338ab164fe8e7dc103319d1c", "unpacked": 37063450},
        "licence": "CC0 · Nicky Case, Monplaisir · Deutsch: Jonas Reich",
        "tile": _fs_tile("fs-angst", "index.html", "touch", "Abenteuer mit Angst", (
            "Interaktive Geschichte: Du spielst die Angst eines Menschen. Deutsch, etwa 30 Minuten, mit Ton.",
            "Interactive story: you play a human’s anxiety. In German, about 30 minutes, with sound.",
            "Histoire interactive : tu joues l’anxiété d’un humain. En allemand, env. 30 minutes, avec son.",
            "Storia interattiva: interpreti l’ansia di una persona. In tedesco, circa 30 minuti, con audio.",
            "Istorgia interactiva: ti giogas la tema d’in uman. Tudestg, var 30 minutas, cun tun."), (
            "Ab ca. 12 Jahren, mit Kraftausdrücken", "From about age 12, with swearing", "Dès 12 ans env., avec des gros mots",
            "Da circa 12 anni, con parolacce", "A partir da ca. 12 onns, cun pleds groppos"))},
}
FS_DL = {"running": False, "id": "", "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
FS_HIDE = ("fspiel.ok", "fspiel.ok.new")


def fs_root():
    return os.path.join(DATA_DIR, "fspiele")


def fs_dir(gid):
    return os.path.join(fs_root(), gid)


def fs_dl_dir():
    return os.path.join(DATA_DIR, "fspiele_dl")


def fs_pinned(gid):
    """exact size and sha256 - nothing else is ever downloaded"""
    f = (FS_GAMES.get(gid) or {}).get("file") or {}
    return (isinstance(f.get("size"), int) and 0 < f["size"] <= FS_MAX_BYTES and bool(re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or "")))
            and isinstance(f.get("unpacked"), int) and 0 < f["unpacked"] <= FS_MAX_BYTES
            and bool(re.fullmatch(r"fspiele-[a-z0-9]+-\d{1,3}\.zip", f.get("name") or "")))


def fs_installed(gid):
    """unpacked and checked once after the download (marker fspiel.ok: tag + sha256 of the ZIP), start page and picture there"""
    if not fs_pinned(gid):
        return False
    d_ = fs_dir(gid)
    try:
        with open(os.path.join(d_, "fspiel.ok"), encoding="utf-8") as fh:
            ok_ = json.load(fh)
    except (OSError, ValueError):
        return False
    g_ = FS_GAMES[gid]
    return (isinstance(ok_, dict) and ok_.get("tag") == FS_TAG and ok_.get("sha256") == g_["file"]["sha256"]
            and all(os.path.isfile(os.path.join(d_, f)) for f in (g_["tile"]["start"], g_["tile"]["icon"])))


def _fs_unzip(zp, dest, limit):
    """the ZIP into dest: only plain names below the folder, no links, at most «limit» bytes"""
    tot = 0
    with zipfile.ZipFile(zp) as z:
        infos = z.infolist()
        for i in infos:
            n = i.filename
            if n.startswith("/") or "\\" in n or ".." in n.split("/") or not re.fullmatch(r"[A-Za-z0-9._ /+-]{1,200}", n) or os.path.basename(n) in FS_HIDE:
                raise ValueError("bad file name in the package")
            if (i.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("link in the package")
            tot += i.file_size
        if tot > limit + 1024:
            raise ValueError("package larger than announced")
        for i in infos:
            if i.is_dir():
                continue
            p = os.path.join(dest, *i.filename.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with z.open(i) as src, open(p, "wb") as out:
                while True:
                    if FS_DL.get("stop"):
                        raise InterruptedError("cancelled")
                    b = src.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
    return tot


def fs_download(gid, wait=False):
    """load and unpack one game (background); (ok, error)"""
    if gid not in FS_GAMES:
        return False, "unknown action"
    if not fs_pinned(gid):
        return False, "comes with an update"
    if FS_DL["running"]:
        return (True, "") if FS_DL["id"] == gid else (False, "busy right now - try again in a moment")
    if fs_installed(gid):
        return True, ""
    f = FS_GAMES[gid]["file"]
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 1 << 40
    dd = fs_dl_dir()
    dest = os.path.join(dd, f["name"])
    have = sum(os.path.getsize(p) for p in (dest, dest + ".part") if os.path.isfile(p))
    if free - (f["size"] - have + f["unpacked"]) < bio_free_need():
        return False, "not enough free space on the memory card"
    FS_DL.update(running=True, id=gid, got=0, total=f["size"], msg="", stop=False, done=False, phase="load")

    def work():
        tmp = fs_dir(gid) + ".new"
        try:
            os.makedirs(dd, exist_ok=True)
            if os.path.isfile(dest) and piper_check_file(dest, f)[0]:
                FS_DL["got"] = f["size"]
            else:
                bio_fetch(FS_BASE["url"] + f["name"], dest, f, FS_DL)     # 639zzd: resume, exact size + sha256
            FS_DL["phase"] = "unpack"
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            _fs_unzip(dest, tmp, f["unpacked"])
            with open(os.path.join(tmp, "fspiel.json"), encoding="utf-8") as fh:
                man = json.load(fh)
            if man.get("tag") != FS_TAG or man.get("id") != gid:
                raise ValueError("the package is not " + gid + " of " + FS_TAG)
            with open(os.path.join(tmp, "fspiel.ok"), "w", encoding="utf-8") as fh:
                json.dump({"tag": FS_TAG, "sha256": f["sha256"]}, fh)
            shutil.rmtree(fs_dir(gid), ignore_errors=True)
            os.replace(tmp, fs_dir(gid))
            shutil.rmtree(dd, ignore_errors=True)                      # the ZIP is not needed any more
            FS_DL["done"] = True
            log_event("sys", f"Game «{FS_GAMES[gid]['tile']['name']}» installed ({FS_TAG})")
        except InterruptedError:
            FS_DL["msg"] = "cancelled"
        except Exception as e:
            FS_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Game «{FS_GAMES[gid]['tile']['name']}» not installed: {FS_DL['msg']}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            FS_DL.update(running=False, phase="")
    if wait:
        work()
        return (not FS_DL["msg"]), FS_DL["msg"]
    threading.Thread(target=work, daemon=True, name="fspiele-dl").start()
    return True, ""


def fs_cancel():
    if FS_DL["running"]:
        FS_DL["stop"] = True
    return True, ""


def fs_delete(gid):
    if gid not in FS_GAMES:
        return False, "unknown action"
    if FS_DL["running"]:
        return False, "busy right now - try again in a moment"
    for p in (fs_dir(gid), fs_dir(gid) + ".new", fs_dl_dir()):
        shutil.rmtree(p, ignore_errors=True)
    log_event("sys", f"Game «{FS_GAMES[gid]['tile']['name']}» deleted")
    return True, ""


def fs_state():
    """for the admin tab (Mehr → Spielecke): every game with size, licence line, installed or not; free space"""
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 0
    gl = []
    for gid, g_ in FS_GAMES.items():
        t_ = g_["tile"]
        gl.append({"id": gid, "name": t_["name"], "names": t_["names"], "desc": t_["desc"], "descs": t_["descs"], "note": t_.get("note", ""),
                   "notes": t_.get("notes", {}), "licence": g_["licence"], "pinned": fs_pinned(gid), "installed": fs_installed(gid),
                   "size": g_["file"]["size"], "unpacked": g_["file"]["unpacked"]})
    return {"tag": FS_TAG, "games": gl, "free": free, "free_need": bio_free_need(),
            "dl": {k: FS_DL[k] for k in ("running", "id", "got", "total", "msg", "done", "phase")}}


# ---- the actions and the state ride on those of 639zzg (no change in the web server, part 550) ------------------------------------
_fotaq_action_639zzn = fotaq_action


# wraps: fotaq_action
def fotaq_action(a, d=None):                                # + 639zzn: with «fs»: <id> the action is for a ready-made game
    d = d or {}
    gid = d.get("fs")
    if gid is None:
        return _fotaq_action_639zzn(a, d)
    gid = str(gid)
    if a == "fotaq_install":
        return fs_download(gid)
    if a == "fotaq_cancel":
        return fs_cancel()
    if a == "fotaq_delete":
        return fs_delete(gid)
    return False, "unknown action"


_fotaq_state_639zzn = fotaq_state


# wraps: fotaq_state
def fotaq_state():                                          # + 639zzn: the ready-made games in the same answer of /api/party
    s_ = _fotaq_state_639zzn()
    s_["fs"] = fs_state()
    return s_


# ---- the game collection: every installed game as one more tile (own folder, games port /g/<id>/) ---------------------------------
_games_list_639zzn = games_list


# wraps: games_list
def games_list(extra=True):                                 # + 639zzn (extra=False: only the collection)
    gl = _games_list_639zzn(extra)
    if extra:
        mine = [dict(g_["tile"]) for gid, g_ in FS_GAMES.items() if fs_installed(gid)]
        if mine:
            gl = [x for x in gl if x.get("dir") not in FS_GAMES] + mine
    return gl


_games_file_639zzn = games_file


# wraps: games_file
def games_file(game, fn):                                   # + 639zzn: the files come from DATA_DIR/fspiele/<id>
    if game not in FS_GAMES:
        return _games_file_639zzn(game, fn)
    if not fs_installed(game):
        return None
    base = os.path.realpath(fs_dir(game))
    p_ = os.path.realpath(os.path.join(base, fn or FS_GAMES[game]["tile"]["start"]))
    if not p_.startswith(base + os.sep) or not os.path.isfile(p_) or os.path.basename(p_) in FS_HIDE:
        return None
    return p_


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -----------------------------------------------------------------
_HX_FS = {
    "More games to load": ("Weitere Spiele zum Nachladen", "Autres jeux à charger", "Altri giochi da caricare", "Ulteriurs gieus per chargiar"),
    "Ready-made free games. Each one is loaded once from GitHub (fixed checksum), then it runs offline in the browser.": (
        "Fertige freie Spiele. Jedes wird einmal von GitHub geladen (feste Prüfsumme) und läuft danach offline im Browser.",
        "Jeux libres tout prêts. Chacun est chargé une fois depuis GitHub (somme de contrôle fixe), puis il tourne hors ligne dans le navigateur.",
        "Giochi liberi già pronti. Ognuno viene caricato una volta da GitHub (somma di controllo fissa), poi funziona offline nel browser.",
        "Gieus libers gia pronts. Mintgin vegn chargià ina giada da GitHub (summa da controlla fixa) e funcziuna lura offline en il navigatur."),
    "busy right now - try again in a moment": ("gerade beschäftigt – gleich nochmals versuchen", "occupé – réessayer dans un instant",
                                               "occupato – riprovare tra un momento", "occupà – empruvar anc ina giada en in mument"),
    "fs-ask": ("«%s» jetzt laden? %s MB von GitHub (danach %s MB auf der Speicherkarte, 2 GB bleiben frei).",
               "Charger «%s» maintenant ? %s Mo depuis GitHub (ensuite %s Mo sur la carte, 2 Go restent libres).",
               "Caricare «%s» adesso? %s MB da GitHub (poi %s MB sulla scheda, 2 GB restano liberi).",
               "Chargiar «%s» uss? %s MB da GitHub (lura %s MB sin la carta, 2 GB restan libers)."),
    "fs-del": ("«%s» entfernen? Die Spielstände bleiben in den Browsern.", "Supprimer «%s» ? Les sauvegardes restent dans les navigateurs.",
               "Rimuovere «%s»? I salvataggi restano nei browser.", "Allontanar «%s»? Ils stadis da gieu restan en ils navigaturs."),
}
for _k, _v in _HX_FS.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
FS_JS_DE = {_k: _v[0] for _k, _v in _HX_FS.items()}
FS_JS_EN = {"fs-ask": "Load «%s» now? %s MB from GitHub (then %s MB on the memory card, 2 GB stay free).",
            "fs-del": "Remove «%s»? The saved games stay in the browsers."}

# ---- admin tab Mehr → Spielecke (TOOLS_PAGE, part 460): one box with a row per game, below the box of FOTAQ -----------------------
FS_TOOLS_JS = r"""// 639zzn: ready-made free games - each its own package (release asset), loaded one by one by the administrator
function fsPaint(box, S) {
  if (!S || !S.games || !S.games.length) return;
  const MB = n => Math.max(1, Math.round((n || 0) / 1e6)), D = S.dl || {};
  const w = el("div", "adp"); w.id = "fs-box"; w.style.cssText = "margin:14px 0 4px;padding:12px;border:1px solid var(--line);border-radius:12px";
  w.appendChild(el("b", "", "🎁 " + t("More games to load")));
  w.appendChild(el("div", "mut", t("Ready-made free games. Each one is loaded once from GitHub (fixed checksum), then it runs offline in the browser.")));
  S.games.forEach(x => {
    const nm = (x.names || {})[LANG] || x.name, ds = (x.descs || {})[LANG] || x.desc, nt = (x.notes || {})[LANG] || x.note;
    const r = el("div", ""); r.id = "fs-" + x.id; r.style.cssText = "margin-top:12px;padding-top:10px;border-top:1px solid var(--line)";
    const hd = el("div", ""); hd.style.cssText = "display:flex;gap:10px;align-items:center";
    if (x.installed) { const im = document.createElement("img"); im.src = "/party/thumb/" + x.id; im.alt = ""; im.style.cssText = "width:40px;height:40px;border-radius:9px;flex:none"; hd.appendChild(im); }
    hd.appendChild(el("b", "", nm)); r.appendChild(hd);
    r.appendChild(el("div", "mut", ds)); r.appendChild(el("div", "mut", "© " + x.licence));
    if (nt) { const n = el("div", "", "⚠️ " + nt); n.style.cssText = "font-weight:600;color:var(--warn,#e9a23b);margin-top:4px"; r.appendChild(n); }
    const row = el("div", "trow"); row.style.marginTop = "8px";
    if (D.running && D.id === x.id) {
      row.appendChild(el("span", "", D.phase === "unpack" ? "⏳ " + t("unpacking …") : "⏳ " + MB(D.got) + " / " + MB(D.total) + " MB"));
      const pr = document.createElement("progress"); pr.max = D.total || 1; pr.value = D.phase === "unpack" ? D.total || 1 : D.got || 0; pr.style.cssText = "flex:1 1 120px";
      const cb = el("button", "sec", t("Cancel")); cb.type = "button"; cb.onclick = () => partyDo({action: "fotaq_cancel", fs: x.id}); row.append(pr, cb);
    } else if (!x.pinned) {
      row.appendChild(el("span", "mut", t("comes with an update")));
    } else if (x.installed) {
      const pl = el("a", "btn", "▶ " + t("Play myself")); pl.href = "/games/" + x.id + "/"; pl.target = "_blank";
      const db = el("button", "sec", "🗑 " + t("Remove")); db.type = "button"; db.className = "sec fs-del";
      db.onclick = () => { if (confirm(t("fs-del").replace("%s", nm))) partyDo({action: "fotaq_delete", fs: x.id}); };
      row.append(el("span", "", "✓ " + t("installed")), pl, db);
    } else {
      const ib = el("button", "", "⬇ " + t("Install") + " (" + MB(x.size) + " MB)"); ib.type = "button"; ib.className = "fs-install"; ib.disabled = !!D.running;
      ib.onclick = () => { if (confirm(t("fs-ask").replace("%s", nm).replace("%s", MB(x.size)).replace("%s", MB(x.unpacked)))) partyDo({action: "fotaq_install", fs: x.id}); };
      row.appendChild(ib);
      if (S.free - x.size - x.unpacked < S.free_need) row.appendChild(el("span", "mut", "⚠ " + t("not enough free space on the memory card")));
    }
    r.appendChild(row);
    if (D.msg && !D.running && D.id === x.id) r.appendChild(el("div", "mut", "⚠ " + t(D.msg)));
    w.appendChild(r);
  });
  box.appendChild(w);
}
"""
_FS_HOOK = "  fotaqPaint(box, P.fotaq);\n}\n"
if TOOLS_PAGE.count(_FS_HOOK) == 1 and "function fsPaint" not in TOOLS_PAGE:
    TOOLS_PAGE = TOOLS_PAGE.replace(_FS_HOOK, "  fotaqPaint(box, P.fotaq);\n  fsPaint(box, (P.fotaq || {}).fs);\n}\n" + FS_TOOLS_JS
                                    + "Object.assign(I18N.de," + json.dumps(FS_JS_DE, ensure_ascii=False) + ");"
                                    "I18N.en=I18N.en||{};Object.assign(I18N.en," + json.dumps(FS_JS_EN, ensure_ascii=False) + ");\n", 1)

# ---- the manual: one point in the section «Spiele freigeben» (5 languages), with the licences -------------------------------------
_HELP_FS = {
    "de": ("🎁 Weitere Spiele zum Nachladen", "(Mehr → Spielecke, ganz unten): fertige freie Spiele, jedes einzeln mit «⬇ Installieren» von GitHub geladen (feste Prüfsumme, 2 GB bleiben frei) und mit «🗑 Entfernen» wieder gelöscht; danach eine Kachel der Sammlung, auch ohne Internet. Urheber, Lizenzen und Änderungen stehen in jedem Paket (LIZENZEN.txt)."),
    "en": ("🎁 More games to load", "(More → Game corner, at the bottom): ready-made free games, each loaded on its own with “⬇ Install” from GitHub (fixed checksum, 2 GB stay free) and deleted again with “🗑 Remove”; then it is a tile of the collection, also without Internet. Authors, licences and changes are in every package (LIZENZEN.txt)."),
    "fr": ("🎁 Autres jeux à charger", "(Plus → Coin jeux, tout en bas) : jeux libres tout prêts, chacun chargé séparément avec « ⬇ Installer » depuis GitHub (somme de contrôle fixe, 2 Go restent libres) et supprimé avec « 🗑 Supprimer » ; ensuite une tuile de la collection, aussi sans Internet. Auteurs, licences et modifications dans chaque paquet (LIZENZEN.txt)."),
    "it": ("🎁 Altri giochi da caricare", "(Altro → Angolo giochi, in fondo): giochi liberi già pronti, ognuno caricato separatamente con «⬇ Installa» da GitHub (somma di controllo fissa, 2 GB restano liberi) e rimosso con «🗑 Rimuovi»; poi è una tessera della raccolta, anche senza Internet. Autori, licenze e modifiche in ogni pacchetto (LIZENZEN.txt)."),
    "rm": ("🎁 Ulteriurs gieus per chargiar", "(Dapli → Chantun da gieus, giusut): gieus libers gia pronts, mintgin chargià separadamain cun «⬇ Installar» da GitHub (summa da controlla fixa, 2 GB restan libers) ed allontanà cun «🗑 Allontanar»; lura ina cachel da la collecziun, er senza internet. Auturs, licenzas e midadas en mintga pachet (LIZENZEN.txt)."),
}


def _help_fs_item(lang):
    """the point of the manual: the fixed text and one sentence per game (name, size, description, note, licence line)"""
    from html import escape as _e
    h_, x_ = _HELP_FS[lang]
    out = f"<li><b>{h_}</b> {_e(x_, quote=False)}"
    for g_ in FS_GAMES.values():
        t_ = g_["tile"]
        mb = f" (~{max(1, round(g_['file']['size'] / 1e6))} MB)" if g_["file"]["size"] else ""
        nt = " ⚠️ " + _e(t_["notes"][lang], quote=False) + "." if t_.get("notes") else ""
        out += f" <b>{_e(t_['names'][lang])}</b>{mb}: {_e(t_['descs'][lang], quote=False)}{nt} © {_e(g_['licence'], quote=False)}."
    return out + "</li>"


def _help_fs(doc, lang):
    i = doc.find('<section id="games"')
    if i < 0 or _HELP_FS[lang][0] in doc[i:doc.find("</section>", i)]:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + _help_fs_item(lang) + doc[j:] if j > 0 else doc


_hp_en_fs = HELP_PAGE.find('<div lang="en">')
if _hp_en_fs > 0:
    HELP_PAGE = _help_fs(HELP_PAGE[:_hp_en_fs], "de") + _help_fs(HELP_PAGE[_hp_en_fs:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_fs(HELP_X[_L], _L)


# ---- self-test (without the packages; werkzeuge/spiele_test.py --fspiele-moveeye tests loading, the port and the tiles) -----------
def fs_selftest():
    assert FS_BASE["url"] == "https://github.com/DonElektro/MotionWatch/releases/download/" + FS_TAG + "/"
    assert re.fullmatch(r"fspiele-\d{1,3}", FS_TAG)
    n = FS_TAG.split("-")[1]
    for gid, g_ in FS_GAMES.items():
        f, t_ = g_["file"], g_["tile"]
        assert re.fullmatch(r"fs-[a-z0-9]{2,20}", gid) and t_["dir"] == gid and f["name"] == "fspiele-%s-%s.zip" % (gid[3:], n), gid
        assert fs_pinned(gid) or (not f["size"] and not f["sha256"] and not f["unpacked"]), gid + ": either all pins or none"
        assert t_["input"] in GAME_GROUPS and t_["icon"] in GAME_THUMBS and t_["start"].endswith(".html")
        assert all(t_["names"].get(L) and t_["descs"].get(L) for L in FS_LANGS5) and t_["desc"] == t_["descs"]["de"]
        assert "ß" not in json.dumps(t_, ensure_ascii=False) and g_["licence"]
        assert not t_.get("note") or all(t_["notes"].get(L) for L in FS_LANGS5)
        if not fs_installed(gid):
            assert all(x.get("dir") != gid for x in games_list()) and games_file(gid, t_["start"]) is None
        assert games_file(gid, "../settings.json") is None and games_file(gid, "/etc/passwd") is None and games_file(gid, "fspiel.ok") is None
    assert "12 Jahren" in FS_GAMES["fs-angst"]["tile"]["note"]
    assert fotaq_action("fotaq_install", {"fs": "nope"}) == (False, "unknown action") and fotaq_action("nope", {"fs": next(iter(FS_GAMES))}) == (False, "unknown action")
    assert fotaq_action("nope") == (False, "unknown action"), "without «fs» the actions of FOTAQ stay as they are"
    s_ = fotaq_state()
    assert "pinned" in s_ and [x["id"] for x in s_["fs"]["games"]] == list(FS_GAMES)
    assert all(x.get("dir") not in FS_GAMES for x in games_list(extra=False))
    assert "function fsPaint" in TOOLS_PAGE and "fsPaint(box, (P.fotaq || {}).fs);" in TOOLS_PAGE and '"fs-ask"' in TOOLS_PAGE
    assert _HELP_FS["de"][0] in HELP_PAGE and _HELP_FS["en"][0] in HELP_PAGE and all(_HELP_FS[L][0] in HELP_X.get(L, _HELP_FS[L][0]) for L in ("fr", "it", "rm"))
    assert all(g_["tile"]["name"] in HELP_PAGE for g_ in FS_GAMES.values())
    return True


SELFTEST_EXTRA.append(("Ready-made free games in the game corner (639zzn)", fs_selftest))
