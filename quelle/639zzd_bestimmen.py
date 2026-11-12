#@ MoveEye – Teil 639zzd: «🌿 Bestimmen» im Datentausch – die Art auf einem Foto erkennen (Pflanze, Tier, Pilz, Insekt) mit BioCLIP 1 ganz auf dem Pi: die drei wahrscheinlichsten Arten mit deutschem und lateinischem Namen und Prozent, sonst die sichere Gattung / Familie; Modell einmal laden mit fester Prüfsumme, Rechnen in einem eigenen Prozess, Zwischenspeicher pro Datei, auch für Gäste. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (08.11.2026, Entscheide fest):
#   * Modell BioCLIP 1 (imageomics/bioclip, ViT-B/16, MIT) – nicht BioCLIP 2. Alles: Pflanzen, Tiere, Pilze, Insekten.
#   * Wer das Bild sehen darf, darf es bestimmen – auch Gäste (Gast-Link, nur «Für alle», wie die Vorschaubilder).
#   * Ganz lokal: kein Cloud-Dienst, das Bild verlässt das Gerät nie.
# Motor wie die Piper-Stimme (639zzb): onnxruntime (MIT, dieselbe feste Fassung PIPER_ORT), kein torch auf dem Pi.
#   * Bild-Teil (ViT-B/16) als ONNX (fp32, siehe BIO_FILES); der Text-Teil läuft nie auf dem Pi: die Einbettungen einer Auswahl von
#     Arten sind fertig gerechnet (BIO_FILES «emb» + «labels»). Gebaut und geprüft im Workflow «BioCLIP»
#     (.github/workflows/bioclip.yml, werkzeuge/bioclip_bauen.py) auf einem GitHub-Rechner, veröffentlicht als Release-Assets
#     (Tag BIO_TAG, nicht «latest»). Grösse + sha256 jeder Datei stehen hier in der (signierten) Hauptdatei – die Signatur
#     bürgt für das Modell (wie ZD_SHA256 / PIPER_VOICES). Laden erst beim ersten «Bestimmen» (Frage mit Grösse), mit Fortsetzen,
#     Fortschritt, freiem Platz (immer tausch_free_gb frei, wie der Datentausch) und harter Grösse; danach offline.
#   * Auswahl der Arten: die in der Schweiz (und Liechtenstein, Deutschland, Österreich) am häufigsten gemeldeten Arten
#     (GBIF.org) + Haustiere, Nutztiere, Garten- und Kulturpflanzen, nur Arten, die BioCLIP kennt (Einbettungen wie
#     pybioclip: die TreeOfLife-Taxonomie als Text, 80 Vorlagen). Höhere Stufen: Wahrscheinlichkeiten zusammengezählt (pybioclip
#     «rank»). Namen: Wikidata (CC0).
#   * Rechnen in einem eigenen Python-Prozess mit «nice 10» (BIO_WORKER, 2 Threads): die Erkennung behält den Vorrang, der
#     Webserver wartet nie (Auftrag im Hintergrund, die Seite fragt nach). Immer nur ein Bild auf einmal (sonst «gleich weiter»),
#     Zeitlimit BIO_TIMEOUT_S, nach BIO_IDLE_S ohne Auftrag beendet sich der Prozess (Speicher wieder frei).
#   * Zwischenspeicher pro Datei-Inhalt (sha256 der Datei + BIO_TAG) unter DATA_DIR/bioclip/cache: dasselbe Foto (auch
#     nochmals hochgeladen) wird nicht nochmals gerechnet. Höchstens BIO_CACHE_N Ergebnisse.
#   * Eingabe ist das Vorschaubild (t/<id>_p.jpg, 1280 px, von 639zzc neu gerechnet): nie die Original-Bytes, keine
#     Pixel-Bomben, dasselbe, was Gäste sehen.
#   * Artinfo-Karte (Wunsch Besitzer 08.11.2026): zu jeder der drei Arten eine aufklappbare Karte – Einleitung der deutschen
#     Wikipedia (gekürzt auf ganze Sätze, sonst englisch «(englisch)»), ☠️ «Giftig» gut sichtbar, «essbar» NUR wenn Wikipedia
#     es ausdrücklich sagt und NUR zusammen mit der Warnung BIO_EDIBLE_WARN (_bio_edible ist die einzige Stelle, die «essbar»
#     erzeugt), Verwechslungs-Arten, Wikidata-Fakten (Höhe, Rote Liste IUCN, Lebensraum), Link zum Artikel + Autoren
#     (CC BY-SA 4.0); unter jedem Ergebnis BIO_FOOT. Nichts erfunden oder übersetzt: gebaut im Workflow «BioCLIP-Infos»
#     (werkzeuge/bioclip_info_bauen.py, Regeln «giftig» / «essbar» dort in REGELN), eine SQLite-Datei als Release-Asset
#     (BIO_INFO, feste Grösse + sha256), geladen mit dem Modell oder einzeln («📖 Artinfos laden»), danach offline.
# Selbsttest bio_selftest; Tests werkzeuge/bioclip_test.py (Ersatz-Modell, Rechte, Gäste, Zwischenspeicher, besetzt, Laden,
# Artinfo, «essbar» nie ohne Warnung, Browser) und im Workflow «BioCLIP» mit dem echten Modell (--echt).
# ----------------------------------------------------------------------------
BIO_TAG = "bioclip-3"
BIO_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + BIO_TAG + "/"}   # Tests: lokaler Server
# Werte aus dem Workflow «BioCLIP» (Release bioclip-3, Lauf 42502560598, 08.11.2026; = «digest» von GitHub); size 0 = nicht freigegeben.
# (bioclip-1 / -2: gleiches Modell; die Namen dort noch schlechter gewählt - Mundart wie «Bettsaier», Sorten wie «fiaschello».)
# fp32 statt int8: auf 74 echten Fotos (iNaturalist) trifft fp32 genau wie torch (Art top-1 70 %, top-3 81 %), int8 nur 61 % /
# 80 % (gleiche Art wie fp32 bei 84 %; Lauf zu bioclip-1) - die Genauigkeit hält bei int8 nicht. int8 (schneller, 90 MB) liegt im selben Release:
#   "model": {"name": "bioclip-1-bild-int8.onnx", "size": 89759048,
#             "sha256": "a9e05a3b77a329ea898b60f8fd8e6f0e97938e35efbc39b157151910aac5d4d6"}
BIO_FILES = {
    "model": {"name": "bioclip-1-bild-fp32.onnx", "size": 345124167,
              "sha256": "c88a6b554da4f11caa29887bbbb3b02f2aeed891c49ede400ac1706c64e45687"},
    "emb": {"name": "bioclip-1-arten.npy", "size": 10568832,
            "sha256": "d170bb9363f33a6524f6bef666df09b66c137c5f5c410af9d84d5aedc88c6663"},
    "labels": {"name": "bioclip-1-arten.json", "size": 1523047,
               "sha256": "d8cb52c4f9bae2f51147579bc71c1b65e0dfd66133115c3f9ca204423e6ec699"},
}
# Artinfos (Workflow «BioCLIP-Infos»); size 0 = noch nicht freigegeben (dann zeigt MoveEye nur die Taxonomie + den Hinweis)
# Release bioclip-info-1, Lauf 42540619256, 09.11.2026 (= «digest» von GitHub): 10'321 Arten, de 6'495 / en 1'733 Texte
BIO_INFO = {"tag": "bioclip-info-1", "name": "bioclip-info-1.sqlite", "size": 2744320,
            "sha256": "cc2c1fb599b8517dd4bbed1aa5762c8d173736907b6fc28186f0bbcdb8611990"}
BIO_INFO_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + BIO_INFO["tag"] + "/"}   # Tests: lokal
BIO_INFO_MAX = 40 * 1024 * 1024
BIO_EDIBLE_WARN = ("Edible according to Wikipedia – risk of confusion with poisonous species, never eat based only on an app "
                   "identification. Emergency: Tox Info Suisse 145")
BIO_FOOT = "For orientation only – not for identifying edible species. Suspected poisoning: Tox Info Suisse 145."
BIO_EDIBLE_WORDS = re.compile(r"essbar|Speisepilz|genießbar|geniessbar|Wildgemüse|gegessen|verzehr|\bedible\b|\beaten\b|culinary", re.I)
BIO_MAX_BYTES = 400 * 1024 * 1024        # harte Obergrenze für alle Dateien zusammen (ein falscher Eintrag lädt nie mehr)
BIO_IDLE_S = 10 * 60
BIO_IDLE_TICK = 20                       # how often the idle watch looks
BIO_TIMEOUT_S = 120.0                    # ein Bild inkl. Modell laden (Pi 5, geschätzt: kalt ~3-5 s laden, ~1-2 s rechnen)
BIO_CACHE_N = 3000
BIO_THREADS = 2
BIO_TOPK = 3
BIO_SURE = 0.60                          # «sicher ist: Gattung …» ab 60 % zusammengezählt
BIO_FALLBACK_BELOW = 0.50                # … wenn die beste Art darunter liegt
BIO_UNSURE = 0.12                        # darunter: «unsicher»
BIO_RATE = (30, 90)                      # new jobs per 10 minutes: a guest address, a person
BIO_RANKS = ("kingdom", "phylum", "class", "order", "family", "genus", "species")

for _k, _v in {"tausch_bio": True}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)   # 636 took its copy before this part
USER_SETTINGS_DENY.update({"tausch_bio"})
for _p in TZ_PERMS:                                        # the start of a job is a POST: every file right may (see = may identify)
    PERM_POST[_p] = set(PERM_POST.get(_p, ())) | {"/api/tausch/bio"}

BIO = {"lock": threading.Lock(), "proc": None, "q": None, "last": 0.0, "err": "", "ms": None, "load_ms": None, "job": "",
       "install": "", "jobs": {}, "sha": {}, "mem": {}, "idle_thread": False}
BIO_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False}
BIO_DB = {"lock": threading.Lock(), "con": None}


def bio_dir():
    return os.path.join(DATA_DIR, "bioclip")


def bio_path(which):
    return os.path.join(bio_dir(), BIO_FILES[which]["name"])


def bio_pinned():
    """every file has an exact size and a sha256 - nothing else is ever downloaded"""
    tot = 0
    for f in BIO_FILES.values():
        if not isinstance(f.get("size"), int) or f["size"] <= 0 or not re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or "")):
            return False
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", f.get("name") or ""):
            return False
        tot += f["size"]
    return tot <= BIO_MAX_BYTES


def bio_total():
    return sum(int(f.get("size") or 0) for f in BIO_FILES.values())


def bio_installed():
    """all files there with the pinned size and checked once after the download (marker bioclip.ok = the three sha256)"""
    if not bio_pinned():
        return False
    try:
        for w, f in BIO_FILES.items():
            if os.path.getsize(bio_path(w)) != f["size"]:
                return False
        with open(os.path.join(bio_dir(), "bioclip.ok"), encoding="utf-8") as fh:
            return fh.read().strip() == bio_ok_mark()
    except OSError:
        return False


def bio_ok_mark():
    return ",".join(BIO_FILES[w]["sha256"] for w in sorted(BIO_FILES))


def bio_runtime():
    import importlib.util
    try:
        return importlib.util.find_spec("onnxruntime") is not None and importlib.util.find_spec("numpy") is not None
    except (ImportError, ValueError):
        return False


# ---- species info (SQLite, read only) --------------------------------------------------------------------------------------------
def bio_info_pinned():
    f = BIO_INFO
    return (isinstance(f.get("size"), int) and 0 < f["size"] <= BIO_INFO_MAX and bool(re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or "")))
            and bool(re.fullmatch(r"[A-Za-z0-9._-]{1,80}", f.get("name") or "")))


def bio_info_path():
    return os.path.join(bio_dir(), BIO_INFO["name"])


def bio_info_installed():
    if not bio_info_pinned():
        return False
    try:
        if os.path.getsize(bio_info_path()) != BIO_INFO["size"]:
            return False
        with open(os.path.join(bio_dir(), "info.ok"), encoding="utf-8") as fh:
            return fh.read().strip() == BIO_INFO["sha256"]
    except OSError:
        return False


def bio_info_close():
    with BIO_DB["lock"]:
        if BIO_DB["con"] is not None:
            try:
                BIO_DB["con"].close()
            except Exception:
                pass
        BIO_DB["con"] = None


def bio_info_get(sci):
    """the raw entry of a species (dict) or None"""
    import sqlite3
    import zlib
    if not bio_info_installed():
        return None
    with BIO_DB["lock"]:
        try:
            if BIO_DB["con"] is None:
                BIO_DB["con"] = sqlite3.connect("file:" + urllib.parse.quote(bio_info_path()) + "?mode=ro&immutable=1", uri=True,
                                                check_same_thread=False)
            row = BIO_DB["con"].execute("SELECT z FROM info WHERE sci = ?", (str(sci)[:120],)).fetchone()
        except Exception:
            BIO_DB["con"] = None
            return None
    if not row:
        return None
    try:
        e = json.loads(zlib.decompress(row[0]).decode("utf-8"))
    except (zlib.error, ValueError):
        return None
    return e if isinstance(e, dict) else None


def _bio_edible(sents, L):
    """the ONLY place that creates «edible» - always with the warning (owner: never «essbar» without it)"""
    s = [str(x)[:400] for x in (sents or []) if str(x).strip()][:2]
    return {"warn": tr(BIO_EDIBLE_WARN, L), "s": s} if s else None


def _bio_wiki_url(lang, title, rev=None, hist=False):
    from urllib.parse import quote
    host = "https://%s.wikipedia.org" % ("en" if lang == "en" else "de")
    if hist:
        return host + "/w/index.php?title=" + quote(title.replace(" ", "_")) + "&action=history"
    return host + "/wiki/" + quote(title.replace(" ", "_"))


def bio_card(e, tax, L):
    """one species card for the page (texts of the interface in L; the content stays German, else English)"""
    L = norm_lang(L)
    tax = [str(x) for x in (tax or []) if x]
    c = {"tax": " › ".join(tax[:6] + ([tax[5] + " " + tax[6]] if len(tax) >= 7 else [])), "empty": True}
    if not isinstance(e, dict):
        return c
    if e.get("x") and e.get("t"):
        lang = "en" if e.get("l") == "en" else "de"
        c.update(empty=False, lang=lang, text=str(e["x"])[:900], title=str(e["t"])[:120], url=_bio_wiki_url(lang, e["t"]),
                 hist=_bio_wiki_url(lang, e["t"], hist=True))
        if lang == "en":
            c["en_t"] = tr("(English)", L)
    tox = [str(x)[:400] for x in (e.get("tox") or [])][:2]
    if tox or e.get("toxwd"):
        c["tox"] = {"s": tox, "src": "Wikipedia" if tox else "Wikidata"}
        if not tox:
            c["tox"]["s"] = [tr("Marked as poisonous in Wikidata.", L)]
    elif e.get("ed"):
        ed = _bio_edible(e["ed"], L)
        if ed:
            c["edible"] = ed
    look = []
    for x in (e.get("look") or [])[:6]:
        if isinstance(x, (list, tuple)) and x:
            look.append({"name": str(x[0])[:80], "tox": bool(len(x) > 1 and x[1]), "url": _bio_wiki_url("de", str(x[0]))})
    if look:
        c["look"] = look
    facts = []
    for k, lab in (("h", "Height"), ("iucn", "Red List (IUCN)"), ("hab", "Habitat")):
        if e.get(k):
            facts.append([tr(lab, L), str(e[k])[:120]])
    if facts:
        c["facts"] = facts
    if not c.get("tox") and not c.get("edible") and BIO_EDIBLE_WORDS.search(c.get("text") or ""):
        c["note_ed"] = tr(BIO_EDIBLE_WARN, L)                # the text itself speaks of eating: never without the warning
    c["empty"] = not (c.get("text") or c.get("tox") or c.get("edible") or look or facts)
    return c


# ---- the worker (own process, nice 10): ONNX image encoder + the ready text embeddings, numpy only ------------------------------
BIO_WORKER = r'''
import json, os, sys, time
def out(d):
    sys.stdout.write(json.dumps(d) + "\n"); sys.stdout.flush()
try:
    import numpy as np
    import onnxruntime as ort
    import cv2
except Exception as e:
    out({"ready": False, "error": "runtime: " + str(e)[:160]}); sys.exit(0)
S = {}
def load(q):
    key = (q["model"], q["emb"], q["labels"])
    if S.get("key") == key:
        return 0
    t0 = time.time()
    S.clear()
    so = ort.SessionOptions(); so.intra_op_num_threads = int(q.get("threads") or 2); so.inter_op_num_threads = 1
    sess = ort.InferenceSession(q["model"], so, providers=["CPUExecutionProvider"])
    with open(q["labels"], encoding="utf-8") as f:
        L = json.load(f)
    E = np.load(q["emb"], allow_pickle=False).astype(np.float32)
    taxa = L["taxa"]
    if E.ndim != 2 or E.shape[0] != len(taxa):
        raise ValueError("labels and embeddings do not fit together")
    E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-6)
    gid = []
    for r in range(6):                                   # kingdom … genus: one group number per row (for summing up)
        m = {}
        gid.append((np.array([m.setdefault("|".join(t[:r + 1]), len(m)) for t in taxa], dtype=np.int64), m))
    S.update(key=key, sess=sess, inp=sess.get_inputs()[0].name, E=E, L=L, gid=gid,
             scale=float(L.get("logit_scale") or 100.0), size=int(L.get("size") or 224),
             mean=np.array(L.get("mean") or (0.48145466, 0.4578275, 0.40821073), np.float32),
             std=np.array(L.get("std") or (0.26862954, 0.26130258, 0.27577711), np.float32))
    return int((time.time() - t0) * 1000)
def prep(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise ValueError("picture not readable")
    n = S["size"]; h, w = im.shape[:2]; s = n / float(min(h, w))
    nw, nh = max(n, round(w * s)), max(n, round(h * s))
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y, x = (nh - n) // 2, (nw - n) // 2
    im = im[y:y + n, x:x + n, ::-1].astype(np.float32) / 255.0
    return ((im - S["mean"]) / S["std"]).transpose(2, 0, 1)[None].copy()
def run(q):
    lm = load(q)
    t0 = time.time()
    e = np.asarray(S["sess"].run(None, {S["inp"]: prep(q["img"])})[0], dtype=np.float32).reshape(-1)
    e /= max(float(np.linalg.norm(e)), 1e-6)
    lg = S["scale"] * (S["E"] @ e)
    p = np.exp(lg - lg.max()); p /= p.sum()
    k = int(q.get("k") or 3)
    taxa, names = S["L"]["taxa"], S["L"].get("names") or {}
    top = [{"tax": taxa[i], "p": round(float(p[i]), 5)} for i in np.argsort(-p)[:k]]
    ranks = {}
    for r, (g, m) in enumerate(S["gid"]):
        s = np.bincount(g, weights=p, minlength=len(m))
        b = int(np.argmax(s))
        i = int(np.argmax(g == b))
        ranks[["kingdom", "phylum", "class", "order", "family", "genus"][r]] = {"tax": taxa[i][:r + 1], "p": round(float(s[b]), 5)}
    want = set()
    for t in top:
        want.update([t["tax"][5] + " " + t["tax"][6], t["tax"][4], t["tax"][5]])
    for v in ranks.values():
        want.add(v["tax"][-1])
    return {"ok": True, "top": top, "ranks": ranks, "names": {n: names[n] for n in want if n in names},
            "ms": int((time.time() - t0) * 1000), "load_ms": lm, "n": len(taxa)}
out({"ready": True, "ort": getattr(ort, "__version__", "?")})
for line in sys.stdin:
    try:
        out(run(json.loads(line)))
    except Exception as e:
        out({"ok": False, "error": (e.__class__.__name__ + ": " + str(e))[:200]})
'''


def _bio_reader(p, q):
    try:
        for line in p.stdout:
            try:
                q.put(json.loads(line))
            except ValueError:
                pass
    except Exception:
        pass
    q.put(None)


def bio_worker_start():
    """the worker process (called with BIO["lock"]); (ok, error)"""
    import queue
    p = BIO["proc"]
    if p is not None and p.poll() is None:
        return True, ""
    os.makedirs(bio_dir(), exist_ok=True)
    cmd = [sys.executable, "-E"] + (["-P"] if sys.version_info >= (3, 11) else []) + ["-c", BIO_WORKER]
    if shutil.which("nice"):
        cmd = ["nice", "-n", "10"] + cmd                 # the detection keeps the priority
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
                             cwd=bio_dir(), env={k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "USER",
                                                                                              "OMP_NUM_THREADS")})
    except OSError as e:
        return False, str(e)[:160]
    q = queue.Queue()
    threading.Thread(target=_bio_reader, args=(p, q), daemon=True, name="bio-read").start()
    try:
        r = q.get(timeout=40)
    except queue.Empty:
        r = None
    if not r or not r.get("ready"):
        try:
            p.kill()
        except OSError:
            pass
        return False, (r or {}).get("error") or "the identification did not start"
    BIO.update(proc=p, q=q, last=time.time())
    _bio_idle_watch()
    return True, ""


def bio_worker_stop():
    p = BIO.get("proc")
    BIO["proc"] = None
    if p is not None:
        try:
            p.stdin.close()
        except Exception:
            pass
        try:
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except OSError:
                pass


def _bio_idle_watch():
    if BIO.get("idle_thread"):
        return
    BIO["idle_thread"] = True

    def run():
        while True:
            time.sleep(BIO_IDLE_TICK)
            with BIO["lock"]:
                if BIO.get("proc") is not None and not BIO["job"] and time.time() - BIO["last"] > BIO_IDLE_S:
                    bio_worker_stop()                    # frees the model (~200 MB) after the idle time
    threading.Thread(target=run, daemon=True, name="bio-idle").start()


def bio_infer(img):
    """identify one picture (path of a JPEG); (ok, error, raw result)"""
    import queue
    if not bio_installed():
        return False, "the identification is not loaded yet", {}
    with BIO["lock"]:
        ok, err = bio_worker_start()
        if not ok:
            BIO["err"] = err
            return False, err, {}
        req = {"model": bio_path("model"), "emb": bio_path("emb"), "labels": bio_path("labels"), "img": os.path.abspath(img),
               "k": BIO_TOPK, "threads": BIO_THREADS}
        try:
            BIO["proc"].stdin.write(json.dumps(req) + "\n"); BIO["proc"].stdin.flush()
            r = BIO["q"].get(timeout=BIO_TIMEOUT_S)
        except (OSError, ValueError, queue.Empty) as e:
            bio_worker_stop()                            # a hanging worker is killed: the next job starts a new one
            r = {"ok": False, "error": "timeout" if isinstance(e, queue.Empty) else str(e)[:100]}
        if r is None:
            bio_worker_stop(); r = {"ok": False, "error": "the identification stopped"}
        BIO["last"] = time.time()
    if not r.get("ok"):
        BIO["err"] = str(r.get("error") or "failed")[:200]
        return False, BIO["err"], {}
    BIO.update(err="", ms=r.get("ms"), load_ms=r.get("load_ms") or BIO.get("load_ms"))
    return True, "", r


# ---- cache: per file content ----------------------------------------------------------------------------------------------------
def bio_cache_dir():
    return os.path.join(bio_dir(), "cache")


def bio_key(sha):
    return hashlib.sha256((BIO_TAG + "|" + bio_ok_mark() + "|" + sha).encode()).hexdigest()[:32]


def bio_cache_get(sha):
    k = bio_key(sha)
    if k in BIO["mem"]:
        return BIO["mem"][k]
    try:
        with open(os.path.join(bio_cache_dir(), k + ".json"), encoding="utf-8") as f:
            r = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(r, dict) or not isinstance(r.get("top"), list):
        return None
    BIO["mem"][k] = r
    return r


def bio_cache_put(sha, raw):
    k = bio_key(sha)
    r = {x: raw.get(x) for x in ("top", "ranks", "names", "ms", "n")}
    BIO["mem"][k] = r
    if len(BIO["mem"]) > 400:
        BIO["mem"].pop(next(iter(BIO["mem"])), None)
    try:
        os.makedirs(bio_cache_dir(), exist_ok=True)
        p = os.path.join(bio_cache_dir(), k + ".json")
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(p + ".tmp", p)
        fs = sorted(glob.glob(os.path.join(bio_cache_dir(), "*.json")), key=lambda x: os.path.getmtime(x))
        for x in fs[:max(0, len(fs) - BIO_CACHE_N)]:
            os.remove(x)
    except OSError:
        pass
    return r


def bio_file_sha(root, m):
    """sha256 of the stored file (memo per id + size + time of change)"""
    src = os.path.join(root, "f", m["id"] + ".bin")
    try:
        st = os.stat(src)
    except OSError:
        return ""
    memo = BIO["sha"].get(m["id"])
    if memo and memo[0] == st.st_size and memo[1] == st.st_mtime:
        return memo[2]
    h = hashlib.sha256()
    with open(src, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    BIO["sha"][m["id"]] = (st.st_size, st.st_mtime, h.hexdigest())
    if len(BIO["sha"]) > 6000:
        BIO["sha"].pop(next(iter(BIO["sha"])), None)
    return h.hexdigest()


# ---- the result for people: names in the language, kind (plant / animal / fungus / insect), rank, percent ---------------------------
BIO_GROUPS = {"plant": ("🌿", "Plant"), "animal": ("🐾", "Animal"), "insect": ("🐞", "Insect"), "fungus": ("🍄", "Fungus"),
              "other": ("🔬", "Other living thing")}
BIO_RANK_T = {"species": "Species", "genus": "Genus", "family": "Family", "order": "Order", "class": "Class", "phylum": "Phylum",
              "kingdom": "Kingdom"}


def bio_group(tax):
    k = str((tax or [""])[0] or "")
    if k == "Plantae":
        return "plant"
    if k == "Fungi":
        return "fungus"
    if k == "Animalia":
        return "insect" if len(tax) > 2 and tax[2] == "Insecta" else "animal"
    return "other"


def bio_name(names, sci, L):
    d = (names or {}).get(sci) or {}
    n = (d.get("de") if L in ("de", "rm") else d.get(L)) or ""
    return n.replace("ß", "ss") if L in ("de", "rm") else n          # Schweiz: «Grosse Brennnessel»


def bio_pct(p, L):
    v = 100.0 * float(p or 0)
    s = "<1" if v < 1 else ("%.0f" % v if v >= 10 else ("%.1f" % v).rstrip("0").rstrip("."))
    return (s if L == "en" else s.replace(".", ",")) + "\u00a0%"          # no line break before %


def bio_format(raw, L):
    """the raw result of the worker (or the cache) -> what the page shows (all texts in the language L)"""
    L = norm_lang(L)
    names = raw.get("names") or {}
    top = []
    info_ok = bio_info_installed()
    for t in raw.get("top") or []:
        tax = list(t.get("tax") or [])[:7]
        if len(tax) < 7:
            continue
        sci = tax[5] + " " + tax[6]
        grp = bio_group(tax)
        ic, gt = BIO_GROUPS[grp]
        fam = tax[4]
        top.append({"sci": sci, "name": bio_name(names, sci, L), "p": float(t.get("p") or 0), "pct": bio_pct(t.get("p"), L),
                    "group": grp, "icon": ic, "group_t": tr(gt, L), "rank": "species", "rank_t": tr("Species", L),
                    "family": fam, "family_name": bio_name(names, fam, L)})
        if info_ok:
            card = bio_card(bio_info_get(sci), tax, L)
            top[-1]["info"] = card
            top[-1]["tox"] = bool(card.get("tox"))
    ms = raw.get("ms")
    sec = ("%.1f s" % (ms / 1000.0)) if isinstance(ms, (int, float)) else ""
    out = {"top": top, "sure": None, "unsure": False, "ms": ms, "n": raw.get("n"), "sec": sec if L == "en" else sec.replace(".", ",")}
    best = top[0]["p"] if top else 0.0
    if best < BIO_FALLBACK_BELOW:
        rk = raw.get("ranks") or {}
        for r in ("genus", "family", "order", "class"):
            v = rk.get(r) or {}
            if float(v.get("p") or 0) >= BIO_SURE and v.get("tax"):
                sci = v["tax"][-1]
                grp = bio_group(v["tax"])
                out["sure"] = {"rank": r, "rank_t": tr(BIO_RANK_T[r], L), "sci": sci, "name": bio_name(names, sci, L),
                               "p": float(v["p"]), "pct": bio_pct(v["p"], L), "icon": BIO_GROUPS[grp][0], "group_t": tr(BIO_GROUPS[grp][1], L)}
                break
    if best < BIO_UNSURE and not out["sure"]:
        out["unsure"] = True
        out["note"] = tr("Unsure - maybe no plant, animal or fungus in the picture, or a species MoveEye does not know.", L)
    elif best < BIO_FALLBACK_BELOW:
        out["note"] = tr("Not sure about the species - compare with the pictures in a field guide.", L)
    out["foot"] = tr(BIO_FOOT, L)                          # under every result, always
    out["info"] = "ok" if info_ok else ("missing" if bio_info_pinned() else "none")
    out["lbl"] = {k: tr(v, L) for k, v in (("info", "Species info"), ("tox", "☠️ Poisonous"), ("look", "Risk of confusion with:"),
                                           ("art", "Whole article"), ("lic", "Text: Wikipedia, CC BY-SA 4.0, abridged –"),
                                           ("auth", "authors"), ("none", "No species info for this species."),
                                           ("wd", "Facts: Wikidata (CC0)"), ("load", "Load species info"))}
    out["line"] = (" · ".join(
        "%s – %s – %s" % (x["name"], x["sci"], x["pct"]) if x["name"] else "%s – %s" % (x["sci"], x["pct"]) for x in top))
    return out


# ---- download: pinned size + sha256, resume, progress, free space ------------------------------------------------------------------
def bio_url(which):
    return BIO_BASE["url"] + BIO_FILES[which]["name"]


def bio_fetch(url, dest, pin, dl):
    """one file with resume (.part + Range); a plain request (public release asset, no key); raises on any problem"""
    part = dest + ".part"
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    if have > pin["size"]:
        os.remove(part); have = 0
    if have < pin["size"]:
        hdr = {"User-Agent": "MoveEye/" + APP_VERSION}
        if have:
            hdr["Range"] = f"bytes={have}-"
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30) as r:
            code = getattr(r, "status", 200)
            if have and (code != 206 or not str(r.headers.get("Content-Range") or "").startswith(f"bytes {have}-")):
                have = 0                                     # the server does not resume: from the start
            n = r.headers.get("Content-Length")
            if n and n.isdigit() and have + int(n) > pin["size"]:
                raise ValueError("file too large")
            dl["got"] += have
            with open(part, "ab" if have else "wb") as f:
                while True:
                    if dl.get("stop"):
                        raise InterruptedError("cancelled")
                    b = r.read(1 << 16)
                    if not b:
                        break
                    have += len(b)
                    if have > pin["size"]:
                        raise ValueError("file too large")
                    f.write(b); dl["got"] += len(b)
    ok, err = piper_check_file(part, pin)                      # 639zzb: exact size + sha256
    if not ok:
        try:
            os.remove(part)
        except OSError:
            pass
        raise ValueError(err)
    os.replace(part, dest)


def bio_free_need():
    """bytes that must stay free besides the download (the same rule as the file exchange: tausch_free_gb)"""
    return int(float(CFG.get("tausch_free_gb", 2.0)) * TZ_GB)


def bio_download(wait=False, model=True):
    """load the model and the species info once (background; model=False: only the species info); (ok, error)"""
    want_m = model and not bio_installed()
    want_i = bio_info_pinned() and not bio_info_installed()
    if want_m and not bio_pinned():
        return False, "The identification comes with an update"
    if not want_m and not want_i:
        return True, ""
    if BIO_DL["running"]:
        return True, ""
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 1 << 40
    need = (bio_total() - sum(os.path.getsize(bio_path(w)) for w in BIO_FILES if os.path.isfile(bio_path(w)))) if want_m else 0
    need += BIO_INFO["size"] if want_i else 0
    if free - need < bio_free_need():
        return False, "not enough free space on the memory card"
    BIO_DL.update(running=True, got=0, total=(bio_total() if want_m else 0) + (BIO_INFO["size"] if want_i else 0), msg="",
                  stop=False, done=False)

    def work():
        try:
            os.makedirs(bio_dir(), exist_ok=True)
            if want_i:                                       # the species info first: small, useful at once
                bio_info_close()
                try:
                    os.remove(os.path.join(bio_dir(), "info.ok"))
                except OSError:
                    pass
                pin = {"size": BIO_INFO["size"], "sha256": BIO_INFO["sha256"]}
                if not (os.path.isfile(bio_info_path()) and piper_check_file(bio_info_path(), pin)[0]):
                    bio_fetch(BIO_INFO_BASE["url"] + BIO_INFO["name"], bio_info_path(), pin, BIO_DL)
                else:
                    BIO_DL["got"] += pin["size"]
                import sqlite3
                con = sqlite3.connect("file:" + urllib.parse.quote(bio_info_path()) + "?mode=ro", uri=True)
                try:
                    n = con.execute("SELECT count(*) FROM info").fetchone()[0]
                finally:
                    con.close()
                if not n:
                    raise ValueError("the species info is empty")
                with open(os.path.join(bio_dir(), "info.ok"), "w", encoding="utf-8") as f:
                    f.write(BIO_INFO["sha256"])
                log_event("sys", f"Species info loaded and checked ({n} species)")
            if not want_m:
                BIO_DL["done"] = True
                return
            try:
                os.remove(os.path.join(bio_dir(), "bioclip.ok"))
            except OSError:
                pass
            for w in ("labels", "emb", "model"):
                pin, dest = BIO_FILES[w], bio_path(w)
                if os.path.isfile(dest) and piper_check_file(dest, pin)[0]:
                    BIO_DL["got"] += pin["size"]; continue
                bio_fetch(bio_url(w), dest, pin, BIO_DL)
            with open(bio_path("labels"), encoding="utf-8") as f:
                lj = json.load(f)
            if not isinstance(lj.get("taxa"), list) or not lj["taxa"]:
                raise ValueError("the list of species is not a BioCLIP list")
            with open(os.path.join(bio_dir(), "bioclip.ok"), "w", encoding="utf-8") as f:
                f.write(bio_ok_mark())
            BIO_DL["done"] = True
            log_event("sys", f"Species identification (BioCLIP) loaded and checked ({len(lj['taxa'])} species)")
        except InterruptedError:
            BIO_DL["msg"] = "cancelled"
        except Exception as e:
            BIO_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Species identification not loaded: {BIO_DL['msg']}")
        finally:
            BIO_DL["running"] = False
    if wait:
        work()
        return (not BIO_DL["msg"]), BIO_DL["msg"]
    threading.Thread(target=work, daemon=True, name="bio-dl").start()
    return True, ""


def bio_delete():
    if BIO_DL["running"] or BIO["job"]:
        return False, "busy right now - try again in a moment"
    with BIO["lock"]:
        bio_worker_stop()
    bio_info_close()
    for p in [x for w in BIO_FILES for x in (bio_path(w), bio_path(w) + ".part")] + [bio_info_path(), bio_info_path() + ".part"]:
        try:
            os.remove(p)
        except OSError:
            pass
    for m in ("bioclip.ok", "info.ok"):
        try:
            os.remove(os.path.join(bio_dir(), m))
        except OSError:
            pass
    log_event("sys", f"Species identification deleted (frees about {bio_total() // 1048576} MB)")
    return True, ""


def bio_install():
    """onnxruntime with pip (MIT, the same pinned version as Piper) - only the administrator"""
    if BIO["install"] == "running" or PIPER.get("install") == "running":
        return False, "already running"
    BIO["install"] = "running"

    def work():
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", PIPER_ORT], capture_output=True,
                               text=True, timeout=1500)
            BIO["install"] = "done" if r.returncode == 0 else ("onnxruntime: " + ((r.stderr or r.stdout).strip().splitlines() or ["?"])[-1][:140])
            log_event("sys", "Species identification: runtime " + ("installed (" + PIPER_ORT + ")" if r.returncode == 0 else BIO["install"]))
        except Exception as e:
            BIO["install"] = "failed: " + str(e)[:120]
    threading.Thread(target=work, daemon=True, name="bio-install").start()
    return True, ""


# ---- jobs: one picture at a time, in the background ------------------------------------------------------------------------------
def bio_job_run(fid, root, m):
    J = BIO["jobs"][fid]
    try:
        sha = bio_file_sha(root, m)
        c = bio_cache_get(sha) if sha else None
        if c is None:
            prev = os.path.join(root, "t", fid + "_p.jpg")
            if not os.path.isfile(prev):
                raise ValueError("no preview for this file")
            ok, err, raw = bio_infer(prev)
            if not ok:
                raise RuntimeError(err)
            c = bio_cache_put(sha, raw) if sha else raw
            J["cached"] = False
        else:
            J["cached"] = True
        J.update(st="done", raw=c, t=time.time())
    except Exception as e:
        J.update(st="err", err=str(e)[:200], t=time.time())
    finally:
        with BIO["lock"]:
            BIO["job"] = ""


def bio_file(fid, who):
    """the meta of a picture this person (or a guest: who None) may see, else None"""
    if not TZ_ID.match(fid or "") or _tz_load() is None:
        return None
    with TZ["lock"]:
        m = TZ["files"].get(fid)
    if m is None:
        return None
    if who is None:
        if m["area"] != "all" or tausch_type(m["name"])[2]:
            return None
    elif not tausch_can_see(m, who):
        return None
    return m


def bio_can(m):
    return tausch_type(m["name"])[1] == "image" and m.get("thumb") is not False


def bio_state(fid, who, L, action="state", rate_key=None):
    """what the panel shows for this picture; who None = guest. Actions: state, start, download, info, cancel, install, delete.
    rate_key: only real work counts (a job, a download), never a look at the state or a result from the cache"""
    L = norm_lang(L)
    guest = who is None
    admin = bool(who and who.get("is_admin"))
    m = bio_file(fid, who)
    info_need = BIO_INFO["size"] if bio_info_pinned() and not bio_info_installed() else 0
    base = {"ok": True, "mb": max(1, round((bio_total() + info_need) / 1048576.0)), "info_mb": max(1, round(info_need / 1048576.0)),
            "can_dl": not guest, "can_install": admin, "can_delete": admin}
    if not CFG.get("tausch_bio", True) or not CFG.get("tausch_on", True):
        return dict(base, ok=False, st="off", msg=tr("Identifying species is switched off.", L))
    if m is None:
        return dict(base, ok=False, st="err", msg=tr("not found", L))
    if not bio_can(m):
        return dict(base, ok=False, st="err", msg=tr("Only pictures can be identified.", L))
    if action == "delete" and admin:
        ok, err = bio_delete()
        return dict(base, ok=ok, st="load" if ok else "err", msg=tr(err, L) if err else tr("deleted", L))
    if action == "cancel" and not guest:
        BIO_DL["stop"] = True
    if action == "install" and admin and not bio_runtime():
        if rate_key and not tausch_rate(rate_key, "bio", BIO_RATE[1]):
            return dict(base, ok=False, st="err", msg=tr("Too many requests in a short time - wait a few minutes.", L))
        ok, err = bio_install()
        if not ok and err != "already running":
            return dict(base, ok=False, st="err", msg=tr(err, L))
    if BIO["install"] == "running":
        return dict(base, st="installing", msg=tr("Installing the runtime (onnxruntime, about 15 MB) …", L))
    if not bio_runtime():
        msg = tr("The runtime onnxruntime is missing (about 15 MB).", L) + " " + (
            tr("Install it here once (needs internet).", L) if admin else tr("The administrator can install it here.", L))
        if BIO["install"] and BIO["install"] != "done":
            msg += " ⚠ " + BIO["install"]
        return dict(base, st="runtime", msg=msg)
    if not bio_pinned():
        return dict(base, ok=False, st="err", msg=tr("The identification comes with an update", L))
    if action == "info" and not guest and not BIO_DL["running"] and bio_installed() and info_need:
        if rate_key and not tausch_rate(rate_key, "bio", BIO_RATE[1]):
            return dict(base, ok=False, st="err", msg=tr("Too many requests in a short time - wait a few minutes.", L))
        ok, err = bio_download(model=False)
        if not ok:
            return dict(base, ok=False, st="err", msg=tr(err, L))
    if BIO_DL["running"]:
        pct = int(100 * BIO_DL["got"] / max(1, BIO_DL["total"]))
        return dict(base, st="loading", pct=pct, msg=trf("Loading BioCLIP … {p} % of {mb} MB", L, p=pct,
                                                          mb=max(1, round(BIO_DL["total"] / 1048576.0))))
    if not bio_installed():
        if action == "download" and not guest:
            if rate_key and not tausch_rate(rate_key, "bio", BIO_RATE[1]):
                return dict(base, ok=False, st="err", msg=tr("Too many requests in a short time - wait a few minutes.", L))
            ok, err = bio_download()
            if not ok:
                return dict(base, ok=False, st="err", msg=tr(err, L))
            return dict(base, st="loading", pct=0, msg=trf("Loading BioCLIP … {p} % of {mb} MB", L, p=0, mb=base["mb"]))
        if guest:
            return dict(base, st="load", msg=tr("Identifying is not set up on this MoveEye yet.", L))
        msg = trf("For identifying, MoveEye loads BioCLIP once ({mb} MB). After that it works without internet, on the device.", L, mb=base["mb"])
        if BIO_DL["msg"]:
            msg += " ⚠ " + tr_err(BIO_DL["msg"], L)
        return dict(base, st="load", msg=msg)
    J = BIO["jobs"].get(fid)
    if J and J["st"] == "done" and J.get("raw") is not None:
        cached = bool(J.get("cached") or J.get("shown"))         # «computed now» only for the first answer
        J["shown"] = True
        return dict(base, st="done", res=dict(bio_format(J["raw"], L), cached=cached))
    sha = (BIO["sha"].get(fid) or (0, 0, ""))[2]
    c = bio_cache_get(sha) if sha else None
    if c is not None:
        return dict(base, st="done", res=dict(bio_format(c, L), cached=True))
    if J and J["st"] == "run":
        return dict(base, st="run", msg=tr("Identifying … (on the device, a few seconds)", L))
    if J and J["st"] == "err" and action != "start":
        return dict(base, ok=False, st="err", msg=tr("Identifying did not work:", L) + " " + tr_err(J.get("err") or "", L))
    if action != "start":
        return dict(base, st="idle", msg="")
    if m.get("thumb") is None:
        return dict(base, st="wait", msg=tr("The preview is still being made …", L))
    root = TZ["root"]
    if J and J["st"] == "run":
        return dict(base, st="run", msg=tr("Identifying … (on the device, a few seconds)", L))
    if BIO["job"] and BIO["job"] != fid:
        return dict(base, st="wait", msg=tr("Another picture is being identified - it continues right after …", L))
    if rate_key and not tausch_rate(rate_key, "bio", BIO_RATE[0 if guest else 1]):
        return dict(base, ok=False, st="err", msg=tr("Too many requests in a short time - wait a few minutes.", L))
    with BIO["lock"]:
        if BIO["job"] and BIO["job"] != fid:
            return dict(base, st="wait", msg=tr("Another picture is being identified - it continues right after …", L))
        BIO["job"] = fid
        BIO["jobs"][fid] = {"st": "run", "t": time.time()}
        if len(BIO["jobs"]) > 300:
            for k in sorted(BIO["jobs"], key=lambda k: BIO["jobs"][k].get("t", 0))[:100]:
                if k != fid:
                    BIO["jobs"].pop(k, None)
    threading.Thread(target=bio_job_run, args=(fid, root, m), daemon=True, name="bio-job").start()
    return dict(base, st="run", msg=tr("Identifying … (on the device, a few seconds)", L))


# ---- web: /api/tausch/bio (logged in), /g/<token>/tausch/bio/<id> (guests) ------------------------------------------------------
_tausch_list_639zzd = tausch_list


# wraps: tausch_list
def tausch_list(who, area="all", folder="", lang=None):    # + 639zzd: «bio» = the button «Bestimmen» is shown
    out = _tausch_list_639zzd(who, area, folder, lang)
    out["bio"] = bool(CFG.get("tausch_bio", True))
    return out


_tausch_guest_list_639zzd = tausch_guest_list


# wraps: tausch_guest_list
def tausch_guest_list(folder=""):                           # + 639zzd
    out = _tausch_guest_list_639zzd(folder)
    out["bio"] = bool(CFG.get("tausch_bio", True))
    return out


_smalltv_routes_639zzd = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzd
    _smalltv_routes_639zzd(app, reply, body)
    from flask import request, g

    def answer(fid, who, L, action, rate_key):
        r = bio_state(fid, who, L, action, rate_key)
        if r.get("msg"):
            r["msg"] = r["msg"].replace(" MB", "\u00a0MB").replace(" Mo", "\u00a0Mo").replace(" %", "\u00a0%")
        code = 200 if r.get("ok") or r.get("st") in ("load", "runtime") else (404 if r.get("msg") == tr("not found", L) else (
            429 if r.get("msg") == tr("Too many requests in a short time - wait a few minutes.", L) else 400))
        return reply(r, code)

    @app.route("/api/tausch/bio", methods=["GET", "POST"])
    def api_tausch_bio():
        who = tausch_who(g)
        if request.method == "GET":
            d = request.args
            act = "state"
        else:
            d = body()
            act = str(d.get("action") or "state")
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if "files_view" not in who["perms"]:
            return reply({"ok": False, "st": "err", "msg": tr("not allowed for your user", L)}, 403)
        return answer(str(d.get("id") or ""), who, L, act if act in ("state", "start", "download", "info", "cancel", "install", "delete") else "state",
                      who["key"])

    @app.route("/g/<token>/tausch/bio/<fid>", methods=["GET", "POST"])
    def tausch_guest_bio(token, fid):
        if not tausch_guest_ok(token):
            return reply({"ok": False}, 404)
        L = sx_req_lang()
        act = "state"
        if request.method == "POST":
            act = "start" if str(body().get("action") or "") == "start" else "state"
        if not tausch_rate("guest|" + (request.remote_addr or "?"), "g", 2000):
            return reply({"ok": False}, 404)
        return answer(fid, None, L, act, "guest|" + (request.remote_addr or "?"))


# ---- settings: one switch under Einstellungen → System → Datentausch ------------------------------------------------------------
TOGGLES.append((_TZS, "tausch_bio", "🌿 Identify species in pictures (BioCLIP, on the device)"))
SET_HELP.update({"tausch_bio": ("The button «🌿 Identify» at every picture: the three most likely species with name and percent. "
                                "Runs only on this MoveEye (the picture never leaves the device); BioCLIP is loaded once (about 340 MB).", "")})

# ---- the page /tausch and the guest page: button + panel ------------------------------------------------------------------------
BIO_CSS = r"""
.tz-biob{min-height:36px;padding:4px 12px;white-space:nowrap}
@media (max-width:340px){.tz-biob .lbl{display:none}}
.tz-bio{position:absolute;left:0;right:0;bottom:0;max-height:64%;overflow:auto;z-index:4;background:var(--panel,#111822);color:var(--txt,#e6edf3);
  border-top:1px solid var(--line,#1f2b3a);border-radius:16px 16px 0 0;padding:12px 16px;padding-bottom:max(14px,env(safe-area-inset-bottom));box-shadow:0 -10px 30px #0009}
@media (min-width:900px){.tz-bio{left:auto;right:18px;bottom:18px;width:400px;border:1px solid var(--line,#1f2b3a);border-radius:16px;max-height:calc(100% - 90px)}}
.tz-bio .hd{display:flex;align-items:center;gap:8px;margin:0 0 6px}.tz-bio .hd b{flex:1;font-size:16px}
.tz-bio .hd button{min-height:32px;padding:2px 10px}
.tz-bio .row{display:block;padding:9px 0;border-bottom:1px solid var(--line,#1f2b3a)}.tz-bio .row:last-of-type{border-bottom:0}
.tz-bio .k{font-size:12px;color:var(--mut,#8b9bb0);display:flex;gap:6px;flex-wrap:wrap}
.tz-bio .n{display:flex;gap:10px;align-items:baseline;margin-top:2px}.tz-bio .n span{flex:1;min-width:0;overflow-wrap:anywhere}
.tz-bio .n i{color:var(--mut,#8b9bb0)}.tz-bio .n b.p{font-variant-numeric:tabular-nums;white-space:nowrap}
.tz-bio .row.first .n span{font-size:17px}.tz-bio .row.first .n b.p{font-size:17px;color:var(--acc,#3b82f6)}
.tz-bio .pb{height:6px;border-radius:4px;background:var(--field,#0c121a);margin-top:6px;overflow:hidden}.tz-bio .pb i{display:block;height:100%;background:var(--acc,#3b82f6)}
.tz-bio .row:not(.first) .pb i{opacity:.55}
.tz-bio .sure{border:1px solid var(--grn,#3fcf6b);border-radius:10px;padding:8px 10px;margin:8px 0 2px;font-size:14px}
.tz-bio .note{font-size:13px;color:var(--yel,#e3b341);margin:8px 0 0}
.tz-bio .msg{font-size:14px;margin:6px 0}.tz-bio .msg.bad{color:var(--red,#ff6b6b)}
.tz-bio .act{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 2px}.tz-bio .act button{min-height:38px;padding:4px 14px}
.tz-bio .ft{font-size:11.5px;color:var(--mut,#8b9bb0);margin-top:10px;line-height:1.4}
.tz-bio .toxb{color:#fff;background:var(--red,#d93636);border-radius:6px;padding:0 6px;font-weight:700}
.tz-bio details.info{margin-top:6px;border:1px solid var(--line,#1f2b3a);border-radius:10px;background:var(--panel2,#0f1620)}
.tz-bio details.info summary{cursor:pointer;padding:6px 10px;font-size:13px;color:var(--acc2,#8ab4f8);list-style-position:inside}
.tz-bio .ib{padding:2px 10px 10px;font-size:13.5px;line-height:1.45}.tz-bio .ib q{display:block;margin:4px 0 0;font-style:italic;quotes:"„" "“"}
.tz-bio .itox{border:2px solid var(--red,#d93636);border-radius:8px;padding:6px 9px;margin:6px 0}.tz-bio .itox b{color:var(--red,#ff6b6b);font-size:15px}
.tz-bio .ied{border:2px solid var(--yel,#e3b341);border-radius:8px;padding:6px 9px;margin:6px 0}.tz-bio .iwarn{color:var(--yel,#e3b341);display:block}
.tz-bio .itx{margin:6px 0}.tz-bio .ilook{margin:6px 0}.tz-bio .ifa{margin:6px 0;display:grid;gap:2px}.tz-bio .ifa span{color:var(--mut,#8b9bb0)}
.tz-bio .itax,.tz-bio .isrc{font-size:11.5px;color:var(--mut,#8b9bb0);margin-top:6px;overflow-wrap:anywhere}
.tz-bio .ib a{color:var(--acc2,#8ab4f8)}.tz-bio .foot{font-size:12.5px;margin:10px 0 0;padding:7px 9px;border-radius:8px;background:var(--field,#0c121a)}
.tz-bio .spin{display:inline-block;animation:tzbs 1.2s linear infinite}@keyframes tzbs{to{transform:rotate(360deg)}}
"""

# one panel for both pages: T(key) = the text in the language, url = the address for this picture, body() = the request data
BIO_PANEL_JS = r"""
function tzBioPanel(f, ov, url, extra, T, pre) {               // pre: a ready result (639zze «Untersuchen»)
  const mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x !== undefined) e.textContent = x; return e; };
  let pan = ov.querySelector(".tz-bio"); if (pan) pan.remove();
  pan = mk("div", "tz-bio"); pan.setAttribute("role", "dialog"); pan.setAttribute("aria-label", T("Identify"));
  const hd = mk("div", "hd"), x = mk("button", "sec", "✕"), bd = mk("div", "bdy"), ft = mk("div", "ft");
  x.type = "button"; x.title = T("Close"); x.onclick = e => { e.stopPropagation(); pan.remove(); };
  hd.append(mk("b", "", "🌿 " + T("Identify")), x); pan.append(hd, bd, ft); ov.appendChild(pan);
  pan.addEventListener("click", e => e.stopPropagation());
  ft.textContent = T("Computed on this MoveEye - the picture never leaves the device.") + " BioCLIP (MIT) · " + T("Names: Wikidata");
  let last = "", timer = 0;
  async function call(action) {
    try { const r = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({action}, extra))});
      const j = await r.json(); return j && j.st ? j : {st: "err", msg: (j && (j.msg || j.error)) || ("error " + r.status)}; }
    catch (e) { return {st: "err", msg: T("No connection to MoveEye.")}; }
  }
  function link(txt, href) { const a = mk("a", "", txt); a.href = href; a.target = "_blank"; a.rel = "noopener noreferrer"; return a; }
  // one species card: «essbar» only together with its warning (never alone); content as text, never as HTML
  function card(c, lb, open) {
    const d = mk("details", "info"), sm = mk("summary", "", "📖 " + (lb.info || "") + (c.en_t ? " " + c.en_t : "")), b = mk("div", "ib");
    d.appendChild(sm); d.appendChild(b); if (open) d.open = true;
    if (c.tox) { const x = mk("div", "itox"); x.appendChild(mk("b", "", lb.tox || "☠️")); (c.tox.s || []).forEach(t => x.appendChild(mk("q", "", t))); b.appendChild(x); }
    if (c.edible && c.edible.warn) { const x = mk("div", "ied"); x.appendChild(mk("b", "iwarn", "⚠️ " + c.edible.warn)); (c.edible.s || []).forEach(t => x.appendChild(mk("q", "", t))); b.appendChild(x); }
    if (c.note_ed && !c.edible && !c.tox) b.appendChild(mk("div", "ied", "")).appendChild(mk("b", "iwarn", "⚠️ " + c.note_ed));
    if (c.text) b.appendChild(mk("p", "itx", c.text));
    if (c.look) { const x = mk("div", "ilook"); x.appendChild(document.createTextNode((lb.look || "") + " "));
      c.look.forEach((l, j) => { if (j) x.appendChild(document.createTextNode(", ")); x.appendChild(link((l.tox ? "☠️ " : "") + l.name, l.url)); }); b.appendChild(x); }
    if (c.facts) { const x = mk("div", "ifa"); c.facts.forEach(f => { const r_ = mk("div"); r_.append(mk("span", "", f[0] + ": "), mk("b", "", f[1])); x.appendChild(r_); }); b.appendChild(x); }
    if (c.empty) b.appendChild(mk("p", "itx", lb.none || ""));
    b.appendChild(mk("div", "itax", c.tax || ""));
    if (c.url) { const x = mk("div", "isrc"); x.append(link(lb.art + " ↗", c.url), document.createTextNode(" · " + lb.lic + " "), link(lb.auth, c.hist));
      if (c.facts) x.appendChild(document.createTextNode(" · " + lb.wd)); b.appendChild(x); }
    else if (c.facts) b.appendChild(mk("div", "isrc", lb.wd));
    return d;
  }
  function btn(txt, action, cls) { const b = mk("button", cls || "", txt); b.type = "button"; b.onclick = () => step(action); return b; }
  function show(r) {
    bd.textContent = "";
    if (r.st === "done") {
      const res = r.res || {};
      (res.top || []).forEach((t_, i) => {
        const row = mk("div", "row" + (i === 0 ? " first" : "")), k = mk("div", "k"), n = mk("div", "n"), sp = mk("span"), pb = mk("div", "pb"), pi = mk("i");
        k.append(mk("span", "", t_.icon + " " + t_.group_t), mk("span", "", "· " + t_.rank_t));
        if (t_.family) k.append(mk("span", "", "· " + (t_.family_name ? t_.family_name + " (" + t_.family + ")" : t_.family)));
        if (t_.tox) k.prepend(mk("span", "toxb", (res.lbl || {}).tox || "☠️"));
        if (t_.name) { sp.append(mk("b", "", t_.name), document.createTextNode(" – ")); }
        sp.append(mk("i", "", t_.sci));
        n.append(sp, mk("b", "p", t_.pct)); pi.style.width = Math.max(1, Math.round(100 * t_.p)) + "%"; pb.appendChild(pi);
        row.append(k, n, pb); if (t_.info) row.appendChild(card(t_.info, res.lbl || {}, i === 0 && !!t_.tox)); bd.appendChild(row);
      });
      if (res.sure) { const s = mk("div", "sure"); s.append(document.createTextNode("✔ " + T("Sure is:") + " " + res.sure.rank_t + " "));
        if (res.sure.name) s.append(mk("b", "", res.sure.name), document.createTextNode(" – "));
        s.append(mk("i", "", res.sure.sci), document.createTextNode(" – " + res.sure.pct)); bd.appendChild(s); }
      if (res.note) bd.appendChild(mk("div", "note", "⚠ " + res.note));
      if (res.info === "missing" && r.can_dl) { const a = mk("div", "act"); a.appendChild(btn("📖 " + ((res.lbl || {}).load || "") + " (" + (r.info_mb || 1) + "\u00a0MB)", "info", "sec")); bd.appendChild(a); }
      if (res.foot) bd.appendChild(mk("div", "foot", "⚠️ " + res.foot));
      if (!(res.top || []).length) bd.appendChild(mk("div", "msg", T("Nothing found.")));
      const sec = res.sec || "";
      ft.textContent = (res.cached ? "↺ " : (sec ? "⏱ " + sec + " · " : "")) + T("Computed on this MoveEye - the picture never leaves the device.") + " BioCLIP (MIT) · " + T("Names: Wikidata");
      return;
    }
    const m = mk("div", "msg" + (r.st === "err" ? " bad" : ""));
    if (["run", "wait", "installing"].includes(r.st)) m.append(mk("span", "spin", "⏳"), document.createTextNode(" " + (r.msg || "")));
    else m.textContent = r.msg || "";
    bd.appendChild(m);
    const act = mk("div", "act");
    if (r.st === "load" && r.can_dl) act.appendChild(btn("⬇ " + T("Load") + (r.mb ? " (" + r.mb + "\u00a0MB)" : ""), "download"));
    if (r.st === "loading") { const pb = mk("div", "pb"), pi = mk("i"); pi.style.width = (r.pct || 0) + "%"; pb.appendChild(pi); bd.appendChild(pb); act.appendChild(btn(T("Cancel"), "cancel", "sec")); }
    if (r.st === "runtime" && r.can_install) act.appendChild(btn("⬇ " + T("Install"), "install"));
    if (r.st === "err") act.appendChild(btn(T("Try again"), "start", "sec"));
    if (act.children.length) bd.appendChild(act);
  }
  async function step(action) {
    clearTimeout(timer);
    if (!document.body.contains(pan)) return;
    const r = await call(action);
    if (!document.body.contains(pan)) return;
    if (r.st === "idle") { last = r.st; return step("start"); }
    show(r);
    const prev = last; last = r.st;
    if (r.st === "run") timer = setTimeout(() => step("state"), 900);
    else if (r.st === "wait") timer = setTimeout(() => step("start"), 2500);
    else if (r.st === "loading" || r.st === "installing") timer = setTimeout(() => step("state"), 1500);
    else if ((prev === "loading" || prev === "installing") && r.st !== "err" && r.st !== "done") step("start");
  }
  if (pre) { show(pre); return pan; }
  bd.appendChild(mk("div", "msg", "⏳ …"));
  step("start");
  return pan;
}
"""

# the page /tausch: a 🌿 on the card (opens the picture and starts) and «🌿 Bestimmen» in the bar of the picture
BIO_PAGE_JS = r"""
  const bioOk = f => !!(S.j && S.j.bio && f.kind === "image" && f.thumb);
  function bioCard(f, ac) { if (!bioOk(f)) return; const b = el("button", "sec", "🌿"); b.type = "button"; b.title = t("Identify");
    b.onclick = () => { S.bioAuto = f.id; preview(f); }; ac.insertBefore(b, ac.firstChild); }
  function bioBar(f, bar, ov) {
    if (!bioOk(f)) return;
    const b = el("button", "tz-biob", ""); b.type = "button"; b.title = t("Identify"); b.append("🌿 ", el("span", "lbl", t("Identify")));
    const dl = bar.querySelector("a.btn");          // phone: the download only as ⬇, so «🌿 Bestimmen» fits
    if (dl && matchMedia("(max-width:480px)").matches) { dl.title = dl.textContent.replace("⬇", "").trim(); dl.textContent = "⬇"; }
    const go = () => tzBioPanel(f, ov, "/api/tausch/bio", {id: f.id, lang: LANG}, t);
    b.onclick = e => { e.stopPropagation(); go(); }; bar.appendChild(b);
    if (S.bioAuto === f.id) { S.bioAuto = ""; setTimeout(go, 0); }
  }
"""

_BIO_HOOKS = (
    ('/*TZEDIT*/', '/*TZEDIT*/\n  /*TZBIO*/'),
    ('    it.append(th, tx); if (ac.children.length) it.appendChild(ac);\n    return it;',
     '    bioCard(f, ac);\n    it.append(th, tx); if (ac.children.length) it.appendChild(ac);\n    return it;'),
    ('    bar.appendChild(x);\n    if (f.inline && f.dl)', '    bioBar(f, bar, ov);\n    bar.appendChild(x);\n    if (f.inline && f.dl)'),
    ('</style></head><body>', '/*BIOCSS*/\n</style></head><body>'),
    ('Object.assign(I18N.de, /*TZDE*/{});', 'Object.assign(I18N.de, /*TZDE*/{});\nObject.assign(I18N.de, /*BIODE*/{});\n/*BIOPANEL*/'),
)
for _a, _b in _BIO_HOOKS:
    if _a in TAUSCH_PAGE and _b not in TAUSCH_PAGE:
        TAUSCH_PAGE = TAUSCH_PAGE.replace(_a, _b, 1)

_BIO_GHOOKS = (
    ('    bd.appendChild(el("div", "mut", TX.only));\n', '    bd.appendChild(el("div", "mut", TX.only));\n'
     '    if (BTX.on && f.kind === "image" && f.thumb) { const b = el("button", "tz-biob", "🌿 " + BTX.t["Identify"]); b.onclick = e => { e.stopPropagation();'
     ' tzBioPanel(f, ov, "__BASE__/tausch/bio/" + f.id, {}, k => BTX.t[k] || k); }; bar.insertBefore(b, x); }\n'),
    ('</style></head><body>', '/*BIOCSS*/\n</style></head><body>'),
    ('/*TZMD*/\n', '/*TZMD*/\nconst BTX = /*BIOTX*/{};\n/*BIOPANEL*/\n'),
    ('  (j.files || []).forEach(f => { const it', '  BTX.on = !!j.bio;\n  (j.files || []).forEach(f => { const it'),
)
for _a, _b in _BIO_GHOOKS:
    if _a in TAUSCH_GUEST_HTML and _b not in TAUSCH_GUEST_HTML:
        TAUSCH_GUEST_HTML = TAUSCH_GUEST_HTML.replace(_a, _b, 1)

_tausch_page_html_639zzd = tausch_page_html


# wraps: tausch_page_html
def tausch_page_html():                                    # + 639zzd
    return (_tausch_page_html_639zzd().replace("/*TZBIO*/", BIO_PAGE_JS, 1).replace("/*BIOCSS*/", BIO_CSS, 1)
            .replace("/*BIOPANEL*/", BIO_PANEL_JS, 1).replace("/*BIODE*/{}", json.dumps(_BIO_DE, ensure_ascii=False), 1))


_tausch_guest_html_639zzd = tausch_guest_html


# wraps: tausch_guest_html
def tausch_guest_html(token):                              # + 639zzd
    L = sx_req_lang()
    tx = {"on": False, "t": {k: tr(k, L) for k in BIO_JS_KEYS}}
    return (_tausch_guest_html_639zzd(token).replace("/*BIOCSS*/", BIO_CSS, 1).replace("/*BIOPANEL*/", BIO_PANEL_JS, 1)
            .replace("/*BIOTX*/{}", json.dumps(tx, ensure_ascii=False).replace("</", "<\\/"), 1))


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -----------------------------------------------------------------
BIO_JS_KEYS = ("Identify", "Close", "Load", "Cancel", "Install", "Try again", "Sure is:", "Nothing found.", "No connection to MoveEye.",
               "Computed on this MoveEye - the picture never leaves the device.", "Names: Wikidata")
_HX_BIO = {
    BIO_EDIBLE_WARN: ("Essbar laut Wikipedia – Verwechslungsgefahr mit giftigen Arten, nie nur nach App-Bestimmung essen. Notfall: Tox Info Suisse 145",
                      "Comestible selon Wikipédia – risque de confusion avec des espèces toxiques, ne jamais manger sur la seule base d’une identification par application. Urgence : Tox Info Suisse 145",
                      "Commestibile secondo Wikipedia – rischio di confusione con specie velenose, non mangiare mai solo in base a un’identificazione con l’app. Emergenza: Tox Info Suisse 145",
                      "Mangiabel tenor Wikipedia – privel da confusiun cun spezias tissientas, mai mangiar mo tenor ina determinaziun cun l’app. Urgenza: Tox Info Suisse 145"),
    BIO_FOOT: ("Nur zur Orientierung – nicht zum Bestimmen von Essbarem. Vergiftungsverdacht: Tox Info Suisse 145.",
               "Seulement pour s’orienter – pas pour identifier ce qui est comestible. Suspicion d’intoxication : Tox Info Suisse 145.",
               "Solo per orientarsi – non per identificare ciò che è commestibile. Sospetto di avvelenamento: Tox Info Suisse 145.",
               "Mo per s’orientar – betg per determinar quai ch’è mangiabel. Suspect d’intoxicaziun: Tox Info Suisse 145."),
    "Species info": ("Artinfo", "Infos sur l’espèce", "Info sulla specie", "Infurmaziuns davart la spezia"),
    "☠️ Poisonous": ("☠️ Giftig", "☠️ Toxique", "☠️ Velenoso", "☠️ Tissient"),
    "Risk of confusion with:": ("Verwechslungsgefahr mit:", "Risque de confusion avec :", "Rischio di confusione con:", "Privel da confusiun cun:"),
    "Whole article": ("Ganzer Artikel", "Article complet", "Articolo completo", "Artitgel cumplet"),
    "Text: Wikipedia, CC BY-SA 4.0, abridged –": ("Text: Wikipedia, CC BY-SA 4.0, gekürzt –", "Texte : Wikipédia, CC BY-SA 4.0, abrégé –",
                                                 "Testo: Wikipedia, CC BY-SA 4.0, abbreviato –", "Text: Wikipedia, CC BY-SA 4.0, scurznì –"),
    "authors": ("Autoren", "auteurs", "autori", "auturs"),
    "No species info for this species.": ("Zu dieser Art gibt es keine Artinfo.", "Pas d’infos pour cette espèce.",
                                          "Nessuna info per questa specie.", "Per questa spezia na datti nagina infurmaziun."),
    "Facts: Wikidata (CC0)": ("Fakten: Wikidata (CC0)", "Faits : Wikidata (CC0)", "Dati: Wikidata (CC0)", "Fatgs: Wikidata (CC0)"),
    "Load species info": ("Artinfos laden", "Charger les infos des espèces", "Caricare le info sulle specie", "Chargiar las infurmaziuns da spezias"),
    "(English)": ("(englisch)", "(en anglais)", "(in inglese)", "(englais)"),
    "Marked as poisonous in Wikidata.": ("In Wikidata als giftig vermerkt.", "Indiqué comme toxique dans Wikidata.",
                                         "Indicato come velenoso in Wikidata.", "Notà sco tissientà en Wikidata."),
    "Height": ("Höhe", "Hauteur", "Altezza", "Autezza"),
    "Red List (IUCN)": ("Rote Liste (IUCN)", "Liste rouge (UICN)", "Lista rossa (IUCN)", "Glista cotschna (IUCN)"),
    "Habitat": ("Lebensraum", "Habitat", "Habitat", "Spazi da viver"),
    "Identify": ("Bestimmen", "Identifier", "Identificare", "Determinar"),
    "Close": ("Schliessen", "Fermer", "Chiudi", "Serrar"),
    "Load": ("Laden", "Charger", "Caricare", "Chargiar"),
    "Install": ("Installieren", "Installer", "Installare", "Installar"),
    "Try again": ("Nochmals", "Réessayer", "Riprova", "Anc ina giada"),
    "Sure is:": ("Sicher ist:", "Sûr :", "Sicuro:", "Segir è:"),
    "Computed on this MoveEye - the picture never leaves the device.": (
        "Gerechnet auf diesem MoveEye – das Bild verlässt das Gerät nie.", "Calculé sur ce MoveEye – l’image ne quitte jamais l’appareil.",
        "Calcolato su questo MoveEye – l’immagine non lascia mai il dispositivo.", "Calculà sin quest MoveEye – il maletg na banduna mai l’apparat."),
    "Names: Wikidata": ("Namen: Wikidata", "Noms : Wikidata", "Nomi: Wikidata", "Nums: Wikidata"),
    "Plant": ("Pflanze", "Plante", "Pianta", "Planta"),
    "Animal": ("Tier", "Animal", "Animale", "Animal"),
    "Insect": ("Insekt", "Insecte", "Insetto", "Insect"),
    "Fungus": ("Pilz", "Champignon", "Fungo", "Bulieu"),
    "Other living thing": ("Anderes Lebewesen", "Autre être vivant", "Altro essere vivente", "Auter esser vivent"),
    "Species": ("Art", "Espèce", "Specie", "Spezia"),
    "Genus": ("Gattung", "Genre", "Genere", "Gener"),
    "Family": ("Familie", "Famille", "Famiglia", "Famiglia"),
    "Order": ("Ordnung", "Ordre", "Ordine", "Urden"),
    "Class": ("Klasse", "Classe", "Classe", "Classa"),
    "Phylum": ("Stamm", "Embranchement", "Phylum", "Tribu"),
    "Kingdom": ("Reich", "Règne", "Regno", "Reginam"),
    "Unsure - maybe no plant, animal or fungus in the picture, or a species MoveEye does not know.": (
        "Unsicher – vielleicht keine Pflanze, kein Tier und kein Pilz im Bild, oder eine Art, die MoveEye nicht kennt.",
        "Incertain – peut-être ni plante, ni animal, ni champignon sur l’image, ou une espèce que MoveEye ne connaît pas.",
        "Incerto – forse nessuna pianta, animale o fungo nell’immagine, o una specie che MoveEye non conosce.",
        "Malsegir – forsa nagina planta, nagin animal e nagin bulieu sin il maletg, u ina spezia che MoveEye na enconuscha betg."),
    "Not sure about the species - compare with the pictures in a field guide.": (
        "Bei der Art nicht sicher – mit den Bildern in einem Bestimmungsbuch vergleichen.",
        "Pas sûr de l’espèce – compare avec les images d’un guide.", "Specie non sicura – confronta con le immagini di una guida.",
        "La spezia n’è betg segira – cumparegliar cun ils maletgs d’in cudesch da determinaziun."),
    "Identifying species is switched off.": ("Das Bestimmen ist ausgeschaltet.", "L’identification est désactivée.",
                                             "L’identificazione è disattivata.", "La determinaziun è deactivada."),
    "Only pictures can be identified.": ("Nur Bilder lassen sich bestimmen.", "Seules les images peuvent être identifiées.",
                                         "Si possono identificare solo immagini.", "Mo maletgs sa laschan determinar."),
    "Installing the runtime (onnxruntime, about 15 MB) …": ("Laufzeit wird installiert (onnxruntime, etwa 15 MB) …",
                                                            "Installation du moteur (onnxruntime, env. 15 Mo) …",
                                                            "Installazione del motore (onnxruntime, circa 15 MB) …",
                                                            "Il motor vegn installà (onnxruntime, var 15 MB) …"),
    "The runtime onnxruntime is missing (about 15 MB).": ("Die Laufzeit onnxruntime fehlt (etwa 15 MB).", "Le moteur onnxruntime manque (env. 15 Mo).",
                                                          "Manca il motore onnxruntime (circa 15 MB).", "Il motor onnxruntime manca (var 15 MB)."),
    "Install it here once (needs internet).": ("Hier einmal installieren (braucht Internet).", "L’installer ici une fois (internet nécessaire).",
                                               "Installalo qui una volta (serve internet).", "Installar qua ina giada (basegna internet)."),
    "The administrator can install it here.": ("Der Administrator kann sie hier installieren.", "L’administrateur peut l’installer ici.",
                                               "L’amministratore può installarlo qui.", "L’administratur po l’installar qua."),
    "The identification comes with an update": ("Das Bestimmen kommt mit einem Update", "L’identification arrive avec une mise à jour",
                                                "L’identificazione arriva con un aggiornamento", "La determinaziun vegn cun in update"),
    "Loading BioCLIP … {p} % of {mb} MB": ("BioCLIP wird geladen … {p} % von {mb} MB", "Chargement de BioCLIP … {p} % de {mb} Mo",
                                           "Caricamento di BioCLIP … {p} % di {mb} MB", "BioCLIP vegn chargià … {p} % da {mb} MB"),
    "Identifying is not set up on this MoveEye yet.": ("Das Bestimmen ist auf diesem MoveEye noch nicht eingerichtet.",
                                                       "L’identification n’est pas encore installée sur ce MoveEye.",
                                                       "L’identificazione non è ancora configurata su questo MoveEye.",
                                                       "La determinaziun n’è anc betg installada sin quest MoveEye."),
    "For identifying, MoveEye loads BioCLIP once ({mb} MB). After that it works without internet, on the device.": (
        "Zum Bestimmen lädt MoveEye einmal BioCLIP ({mb} MB). Danach geht es ohne Internet, auf dem Gerät.",
        "Pour identifier, MoveEye charge une fois BioCLIP ({mb} Mo). Ensuite ça marche sans internet, sur l’appareil.",
        "Per identificare, MoveEye carica una volta BioCLIP ({mb} MB). Poi funziona senza internet, sul dispositivo.",
        "Per determinar chargia MoveEye ina giada BioCLIP ({mb} MB). Lura funcziuna quai senza internet, sin l’apparat."),
    "Identifying … (on the device, a few seconds)": ("Wird bestimmt … (auf dem Gerät, einige Sekunden)", "Identification … (sur l’appareil, quelques secondes)",
                                                    "Identificazione … (sul dispositivo, alcuni secondi)", "Vegn determinà … (sin l’apparat, intgins secunds)"),
    "Identifying did not work:": ("Bestimmen ging nicht:", "L’identification n’a pas marché :", "L’identificazione non è riuscita:",
                                  "La determinaziun n’ha betg funcziunà:"),
    "The preview is still being made …": ("Das Vorschaubild wird noch gerechnet …", "L’aperçu est encore en cours …",
                                          "L’anteprima è ancora in preparazione …", "La prevista vegn anc calculada …"),
    "Another picture is being identified - it continues right after …": (
        "Gerade wird ein anderes Bild bestimmt – es geht gleich weiter …", "Une autre image est en cours d’identification – ça continue juste après …",
        "Si sta identificando un’altra immagine – si continua subito dopo …", "Ussa vegn in auter maletg determinà – i cuntinuescha immediat …"),
    "Too many requests in a short time - wait a few minutes.": ("Zu viele Anfragen in kurzer Zeit – ein paar Minuten warten.",
                                                                "Trop de demandes en peu de temps – attends quelques minutes.",
                                                                "Troppe richieste in poco tempo – aspetta qualche minuto.",
                                                                "Memia bleras dumondas en curt temp – spetgar in pèr minutas."),
    "busy right now - try again in a moment": ("gerade beschäftigt – gleich nochmals versuchen", "occupé – réessaie dans un instant",
                                               "occupato – riprova tra un attimo", "occupà – empruvar puspè en in mument"),
    "the identification is not loaded yet": ("das Bestimmen ist noch nicht geladen", "l’identification n’est pas encore chargée",
                                             "l’identificazione non è ancora caricata", "la determinaziun n’è anc betg chargiada"),
    "timeout": ("Zeitüberschreitung", "délai dépassé", "tempo scaduto", "temp surpassà"),
    "no preview for this file": ("kein Vorschaubild für diese Datei", "pas d’aperçu pour ce fichier", "nessuna anteprima per questo file",
                                 "nagina prevista per questa datoteca"),
    "deleted": ("gelöscht", "supprimé", "eliminato", "stizzà"),
    "🌿 Identify species in pictures (BioCLIP, on the device)": ("🌿 Arten auf Bildern bestimmen (BioCLIP, auf dem Gerät)",
                                                                "🌿 Identifier les espèces sur les images (BioCLIP, sur l’appareil)",
                                                                "🌿 Identificare le specie nelle immagini (BioCLIP, sul dispositivo)",
                                                                "🌿 Determinar spezias sin maletgs (BioCLIP, sin l’apparat)"),
    "The button «🌿 Identify» at every picture: the three most likely species with name and percent. Runs only on this MoveEye (the picture never leaves the device); BioCLIP is loaded once (about 340 MB).": (
        "Der Knopf «🌿 Bestimmen» bei jedem Bild: die drei wahrscheinlichsten Arten mit Name und Prozent. Läuft nur auf diesem MoveEye (das Bild verlässt das Gerät nie); BioCLIP wird einmal geladen (etwa 340 MB).",
        "Le bouton «🌿 Identifier» à chaque image : les trois espèces les plus probables avec nom et pourcentage. Uniquement sur ce MoveEye (l’image ne quitte jamais l’appareil) ; BioCLIP est chargé une fois (env. 340 Mo).",
        "Il pulsante «🌿 Identificare» su ogni immagine: le tre specie più probabili con nome e percentuale. Solo su questo MoveEye (l’immagine non lascia mai il dispositivo); BioCLIP viene caricato una volta (circa 340 MB).",
        "Il buttun «🌿 Determinar» tar mintga maletg: las trais spezias las pli probablas cun num e pertschient. Mo sin quest MoveEye (il maletg na banduna mai l’apparat); BioCLIP vegn chargià ina giada (var 340 MB)."),
}
for _k, _v in _HX_BIO.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_BIO_DE = {_k: _HX_BIO[_k][0] if _k in _HX_BIO else DE.get(_k, _k) for _k in BIO_JS_KEYS}

# ---- the manual: one point in the section «Datentausch» (5 languages), with the licences ----------------------------------------------
_HELP_BIO = {
    "de": ('<li><b>🌿 Bestimmen</b> (bei jedem Bild, auch für Gäste): MoveEye nennt die drei wahrscheinlichsten Arten mit deutschem und lateinischem Namen und Prozent '
           '(Pflanzen, Tiere, Pilze, Insekten), ist die Art unsicher, die sichere Gattung oder Familie. Gerechnet wird nur auf dem Gerät – das Bild verlässt MoveEye nie. '
           'Beim ersten Mal lädt MoveEye das Modell einmal (etwa 340 MB, feste Prüfsumme), danach geht es ohne Internet; ein Bild braucht auf dem Pi 5 wenige Sekunden. '
           'Bekannt sind rund 10\'000 Arten, die in der Schweiz und in Mitteleuropa am häufigsten gemeldet werden, dazu Haustiere, Nutztiere, Garten- und Kulturpflanzen. '
           'Ausschalten: Einstellungen → System → Digitaler Rucksack. <b>Modell und Lizenzen:</b> BioCLIP (Stevens et al., CVPR 2024, Imageomics Institute), MIT; '
           'Auswahl der Arten nach den Fundmeldungen auf GBIF.org; Namen von Wikidata (CC0); Rechnung mit onnxruntime (MIT). Bitte Ergebnisse vor dem Essen von Pilzen oder Pflanzen nie als sicher nehmen.</li><li><b>📖 Artinfo</b> (aufklappen bei jeder Art): die Einleitung des Wikipedia-Artikels (deutsch, sonst englisch), gekürzt, ☠️ <b>Giftig</b>, wenn der Artikel es ausdrücklich sagt, Verwechslungs-Arten, Höhe / Rote Liste / Lebensraum aus Wikidata und der Link zum ganzen Artikel. «Essbar» steht nur, wenn Wikipedia es ausdrücklich sagt, und immer mit der Warnung. Nichts davon ist von MoveEye erfunden oder übersetzt; die Artinfos werden einmal geladen (wenige MB) und gehen danach offline. <b>Nur zur Orientierung – nicht zum Bestimmen von Essbarem. Vergiftungsverdacht: Tox Info Suisse 145.</b> <b>Lizenzen:</b> Texte aus Wikipedia, CC BY-SA 4.0 (Autoren: die Versionsgeschichte des jeweiligen Artikels, Link in jeder Karte; Texte gekürzt); Fakten aus Wikidata (CC0).</li>'),
    "en": ('<li><b>🌿 Identify</b> (at every picture, also for guests): MoveEye names the three most likely species with common and Latin name and percent '
           '(plants, animals, fungi, insects); when the species is unsure, the sure genus or family. It is computed only on the device – the picture never leaves MoveEye. '
           'The first time MoveEye loads the model once (about 340 MB, fixed checksum), after that it works without internet; a picture takes a few seconds on the Pi 5. '
           'It knows about 10,000 species most often reported in Switzerland and Central Europe, plus pets, farm animals, garden and crop plants. '
           'Switch off: Settings → System → Digital backpack. <b>Model and licences:</b> BioCLIP (Stevens et al., CVPR 2024, Imageomics Institute), MIT; '
           'species chosen after the occurrence records on GBIF.org; names from Wikidata (CC0); inference with onnxruntime (MIT). Never rely on it before eating mushrooms or plants.</li><li><b>📖 Species info</b> (unfold at each species): the lead of the Wikipedia article (German, else English), abridged, ☠️ <b>Poisonous</b> when the article says so explicitly, species it can be confused with, height / Red List / habitat from Wikidata and the link to the whole article. «Edible» only appears when Wikipedia says so explicitly, and always with the warning. Nothing is invented or translated by MoveEye; the species info is loaded once (a few MB), then offline. <b>For orientation only – not for identifying edible species. Suspected poisoning: Tox Info Suisse 145.</b> <b>Licences:</b> texts from Wikipedia, CC BY-SA 4.0 (authors: the history of each article, linked in every card; texts abridged); facts from Wikidata (CC0).</li>'),
    "fr": ('<li><b>🌿 Identifier</b> (à chaque image, aussi pour les invités) : MoveEye donne les trois espèces les plus probables avec nom et nom latin et pourcentage '
           '(plantes, animaux, champignons, insectes) ; si l’espèce est incertaine, le genre ou la famille sûrs. Calcul uniquement sur l’appareil – l’image ne quitte jamais MoveEye. '
           'La première fois, MoveEye charge le modèle (env. 340 Mo, somme de contrôle fixe), ensuite sans internet. Environ 10 000 espèces de Suisse et d’Europe centrale, animaux domestiques et plantes cultivées. '
           '<b>Modèle et licences :</b> BioCLIP (Stevens et al., CVPR 2024), MIT ; sélection d’après GBIF.org ; noms : Wikidata (CC0) ; calcul : onnxruntime (MIT). Ne jamais s’y fier avant de manger champignons ou plantes.</li><li><b>📖 Infos sur l’espèce</b> : début de l’article Wikipédia (en allemand, sinon en anglais), abrégé, ☠️ <b>Toxique</b> si l’article le dit expressément, confusions possibles, faits de Wikidata, lien vers l’article. «Comestible» seulement si Wikipédia le dit expressément, toujours avec l’avertissement. <b>Seulement pour s’orienter – pas pour identifier ce qui est comestible. Suspicion d’intoxication : Tox Info Suisse 145.</b> <b>Licences :</b> textes de Wikipédia, CC BY-SA 4.0 (auteurs : historique de chaque article, lien dans chaque fiche) ; faits de Wikidata (CC0).</li>'),
    "it": ('<li><b>🌿 Identificare</b> (su ogni immagine, anche per gli ospiti): MoveEye indica le tre specie più probabili con nome, nome latino e percentuale '
           '(piante, animali, funghi, insetti); se la specie è incerta, il genere o la famiglia sicuri. Calcolo solo sul dispositivo – l’immagine non lascia mai MoveEye. '
           'La prima volta MoveEye carica il modello (circa 340 MB, somma di controllo fissa), poi senza internet. Circa 10 000 specie di Svizzera ed Europa centrale, animali domestici e piante coltivate. '
           '<b>Modello e licenze:</b> BioCLIP (Stevens et al., CVPR 2024), MIT; selezione secondo GBIF.org; nomi: Wikidata (CC0); calcolo: onnxruntime (MIT). Mai fidarsi prima di mangiare funghi o piante.</li><li><b>📖 Info sulla specie</b>: inizio dell’articolo di Wikipedia (in tedesco, altrimenti in inglese), abbreviato, ☠️ <b>Velenoso</b> se l’articolo lo dice espressamente, specie confondibili, dati di Wikidata, link all’articolo. «Commestibile» solo se Wikipedia lo dice espressamente, sempre con l’avvertenza. <b>Solo per orientarsi – non per identificare ciò che è commestibile. Sospetto di avvelenamento: Tox Info Suisse 145.</b> <b>Licenze:</b> testi da Wikipedia, CC BY-SA 4.0 (autori: cronologia di ogni articolo, link in ogni scheda); dati da Wikidata (CC0).</li>'),
    "rm": ('<li><b>🌿 Determinar</b> (tar mintga maletg, er per giasts): MoveEye num las trais spezias las pli probablas cun num, num latin e pertschient '
           '(plantas, animals, bulieus, insects); sche la spezia è malsegira, il gener u la famiglia segira. Calculà mo sin l’apparat – il maletg na banduna mai MoveEye. '
           'L’emprima giada chargia MoveEye il model (var 340 MB, summa da controlla fixa), lura senza internet. Var 10 000 spezias da la Svizra e da l’Europa centrala, animals da chasa e plantas cultivadas. '
           '<b>Model e licenzas:</b> BioCLIP (Stevens et al., CVPR 2024), MIT; selecziun tenor GBIF.org; nums: Wikidata (CC0); calculaziun: onnxruntime (MIT). Mai sa fidar avant che mangiar bulieus u plantas.</li><li><b>📖 Infurmaziuns davart la spezia</b>: l’entschatta da l’artitgel da Wikipedia (tudestg, uschiglio englais), scurznida, ☠️ <b>Tissient</b> sche l’artitgel di quai expressivamain, spezias da confusiun, fatgs da Wikidata, link a l’artitgel. «Mangiabel» mo sche Wikipedia di quai expressivamain, adina cun l’avertiment. <b>Mo per s’orientar – betg per determinar quai ch’è mangiabel. Suspect d’intoxicaziun: Tox Info Suisse 145.</b> <b>Licenzas:</b> texts da Wikipedia, CC BY-SA 4.0 (auturs: istorgia da mintga artitgel, link en mintga carta); fatgs da Wikidata (CC0).</li>'),
}


def _help_bio(doc, lang):
    i = doc.find('<section id="tausch"')
    if i < 0 or "🌿" in doc[i:doc.find("</section>", i)]:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + _HELP_BIO[lang] + doc[j:] if j > 0 else doc


_hp_en_bio = HELP_PAGE.find('<div lang="en">')
if _hp_en_bio > 0:
    HELP_PAGE = _help_bio(HELP_PAGE[:_hp_en_bio], "de") + _help_bio(HELP_PAGE[_hp_en_bio:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_bio(HELP_X[_L], _L)


# ---- self-test (without a model; werkzeuge/bioclip_test.py tests the worker, the web side and the browser) ---------------------------
def bio_selftest():
    assert BIO_TAG and BIO_BASE["url"] == "https://github.com/DonElektro/MotionWatch/releases/download/" + BIO_TAG + "/"
    assert all(re.fullmatch(r"bioclip-1-[a-z0-9-]+\.(onnx|npy|json)", f["name"]) for f in BIO_FILES.values())
    assert bio_pinned() or all(not f["size"] for f in BIO_FILES.values()), "BIO_FILES: either all pins or none (comes with an update)"
    assert bio_total() <= BIO_MAX_BYTES
    tx = ["Plantae", "Tracheophyta", "Magnoliopsida", "Asterales", "Asteraceae", "Taraxacum", "officinale"]
    raw = {"top": [{"tax": tx, "p": 0.871}, {"tax": tx[:6] + ["erythrospermum"], "p": 0.06},
                   {"tax": ["Animalia", "Arthropoda", "Insecta", "Coleoptera", "Coccinellidae", "Coccinella", "septempunctata"], "p": 0.004}],
           "ranks": {"genus": {"tax": tx[:6], "p": 0.95}}, "names": {"Taraxacum officinale": {"de": "Gemeiner Löwenzahn", "en": "Common dandelion"},
                                                                     "Asteraceae": {"de": "Korbblütler"}}, "ms": 812}
    r = bio_format(raw, "de")
    assert r["line"].startswith("Gemeiner Löwenzahn – Taraxacum officinale – 87\u00a0%") and r["sec"] == "0,8 s", r["line"]
    assert r["top"][0]["group_t"] == "Pflanze" and r["top"][0]["family_name"] == "Korbblütler" and r["top"][2]["group_t"] == "Insekt"
    assert [x["pct"].replace("\u00a0", " ") for x in r["top"]] == ["87 %", "6 %", "<1 %"], r["top"]
    assert bio_pct(0.0123, "de") == "1,2\u00a0%" and bio_pct(0.0123, "en") == "1.2\u00a0%"
    assert not r["sure"] and not r.get("note")
    assert bio_format(raw, "rm")["top"][0]["name"] == "Gemeiner Löwenzahn" and bio_format(raw, "fr")["top"][0]["name"] == ""
    assert bio_name({"Urtica dioica": {"de": "Große Brennnessel"}}, "Urtica dioica", "de") == "Grosse Brennnessel"
    raw["top"][0]["p"] = 0.31
    r = bio_format(raw, "de")
    assert r["sure"] and r["sure"]["rank_t"] == "Gattung" and r["sure"]["sci"] == "Taraxacum" and r["note"], r
    raw["top"][0]["p"], raw["ranks"]["genus"]["p"] = 0.05, 0.2
    assert bio_format(raw, "de")["unsure"]
    assert bio_group(["Fungi"]) == "fungus" and bio_group(["Animalia", "Chordata", "Aves"]) == "animal" and bio_group(["Chromista"]) == "other"
    assert bio_key("a" * 64) != bio_key("b" * 64) and len(bio_key("a" * 64)) == 32
    for k in BIO_JS_KEYS:
        assert k in DE or k in _TZ_DE or k in ("Cancel", "Nothing found.", "No connection to MoveEye."), k
    assert "/*TZBIO*/" in TAUSCH_PAGE and "bioCard(f, ac);" in TAUSCH_PAGE and "bioBar(f, bar, ov);" in TAUSCH_PAGE, "hooks in /tausch"
    assert "/*BIOTX*/" in TAUSCH_GUEST_HTML and "tzBioPanel(f, ov" in TAUSCH_GUEST_HTML, "hooks in the guest page"
    assert "🌿" in HELP_PAGE and "BioCLIP" in HELP_PAGE
    assert role_allows("view", "/api/tausch/bio", "POST", {}) and role_allows("view", "/api/tausch/bio", "GET", {})
    assert not role_allows("kid", "/api/tausch/bio", "POST", {})
    # species info: «essbar» only with the warning, «giftig» wins, footer always, nothing when there is nothing
    assert bio_info_pinned() or not BIO_INFO["size"], "BIO_INFO: either a full pin or none"
    c = bio_card({"l": "de", "t": "Bärlauch", "x": "Der Bärlauch …", "ed": ["Alle Pflanzenteile des Bärlauchs sind essbar."],
                  "look": [["Maiglöckchen", 1], ["Herbstzeitlose", 1]]}, ["Plantae", "", "", "", "Amaryllidaceae", "Allium", "ursinum"], "de")
    assert c["edible"]["warn"].startswith("Essbar laut Wikipedia – Verwechslungsgefahr") and "Tox Info Suisse 145" in c["edible"]["warn"], c
    assert c["look"][0] == {"name": "Maiglöckchen", "tox": True, "url": "https://de.wikipedia.org/wiki/Maigl%C3%B6ckchen"} and not c.get("tox")
    c = bio_card({"l": "de", "t": "Eibe", "x": "…", "tox": ["Alle Teile sind stark giftig."], "ed": ["Der Samenmantel ist essbar."]}, tx, "de")
    assert c["tox"]["s"] == ["Alle Teile sind stark giftig."] and "edible" not in c, "giftig: nie zusätzlich essbar"
    c = bio_card({"q": "Q1", "toxwd": ["poisonous mushroom"]}, tx, "fr")
    assert c["tox"]["src"] == "Wikidata" and c["empty"] is False and "text" not in c
    c = bio_card(None, tx, "de")
    assert c["empty"] and c["tax"].endswith("Taraxacum officinale") and "edible" not in c and "tox" not in c
    assert bio_card({"l": "en", "t": "X", "x": "…"}, tx, "it")["en_t"] == "(in inglese)"
    for L_ in LANGS:
        assert "145" in tr(BIO_EDIBLE_WARN, L_) and "145" in tr(BIO_FOOT, L_), L_
    assert _bio_edible([], "de") is None
    c = bio_card({"l": "de", "t": "X", "x": "Der Samenmantel ist essbar und ungiftig."}, tx, "de")
    assert "edible" not in c and c["note_ed"].startswith("Essbar laut Wikipedia"), "Text spricht von essbar: Warnung trotzdem"
    r = bio_format(dict(raw, top=raw["top"][:1]), "de")
    assert r["foot"].startswith("Nur zur Orientierung") and r["info"] in ("ok", "missing", "none")
    return "pins, result «Gemeiner Löwenzahn – Taraxacum officinale – 87 %», plant / insect, genus when unsure, cache key, hooks, rights, species card («essbar» only with the warning)"


SELFTEST_EXTRA.append(("Species identification «🌿 Bestimmen» (BioCLIP, 639zzd)", bio_selftest))
