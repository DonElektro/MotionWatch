#@ MoveEye – Teil 639zzzzr: «🎒 Rucksack bei Import/Export» – überall, wo MoveEye etwas importiert oder exportiert, kann man auch eine Datei aus dem Digitalen Rucksack wählen bzw. dort speichern (ein gemeinsames Skript /rk/io.js, Export-Adressen nur aus einer festen Liste, Privates nur in «Meine Dateien»). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026): «Wo MoveEye etwas importieren oder exportieren kann, kann man auch Dateien im Digitalen
# Rucksack wählen oder ablegen.» Plan vom Koordinator freigegeben (15.11.2026).
#   * Ein Skript für alle Seiten mit Reitern (render_page, nicht Gast-Seiten, nicht die eigenständige Funk-Seite 639zzzf):
#     /rk/io.js?v=<Prüfsumme> (das Literal RK_IO_JS geht in die Zusatzdatei). Es fragt zuerst GET /api/tausch/io, was der
#     Benutzer darf (ansehen / herunterladen / hochladen); ohne Rechte oder mit ausgeschaltetem Rucksack zeigt es nichts.
#   * Import: neben dem Knopf, der ein verstecktes <input type=file> öffnet (das Element davor oder danach), kommt
#     «🎒 Aus dem Rucksack» mit denselben Klassen (so gelten dieselben Regeln fürs Ausblenden); ein sichtbares Datei-Feld
#     bekommt den Knopf direkt dahinter. Ohne erkennbaren Knopf (Feld erst beim Antippen gebaut, z. B. Foto der Packliste,
#     «Untersuchen», Alarm-Ton) fragt ein kleines Blatt «📱 Von diesem Gerät / 🎒 Aus dem Rucksack». Die gewählte Datei kommt
#     über DataTransfer ins Feld und löst «change» aus – die Seite liest sie wie eine Datei vom Gerät (keine Zeile in den
#     anderen Teilen). Gezeigt werden nur Dateien, die man herunterladen darf; Filter aus «accept» (bzw. RK_TYPES im Skript).
#   * Export: neben jedem Download-Link, dessen Adresse in RK_EXPORTS steht, kommt «🎒 In den Rucksack». MoveEye holt den
#     Export dann selbst (POST /api/tausch/io {action:"save", url}) – die Datei geht nicht übers Handy. Links mit blob:-Adresse
#     (im Browser gerechnet: Gehäuse-Einkaufsliste, Bild mit Botschaft …) und Downloads, die eine Seite per Skript auslöst,
#     bekommen den Knopf bzw. einen kurzen Hinweis unten «⬇ Name · 🎒 In den Rucksack»; diese Dateien lädt der Browser in
#     Stücken hoch wie auf /tausch.
#   * RK_EXPORTS ist eine feste Liste (Pfad-Muster ganz, erlaubte Parameter, Art): keine anderen Adressen, keine fremden
#     Rechner, kein «..», nie /tausch selbst. Der Export läuft als derselbe Benutzer: alle Wächter der Anfrage (Rolle,
#     Bedienermodus, Funnel, Demo …) ausser der Anmeldung selbst laufen nochmals für die Export-Adresse; App-Schlüssel nie.
#   * Privat (Einstellungen, Diagnose, Nacht-Testlauf, Werkseinstellungs- und Simulator-Sicherungen, Testbericht): nur in
#     «Meine Dateien» – das Gerät setzt es durch, egal was die Seite schickt. Aufnahmen, Tagebuch-Bilder, Berichte und
#     Trainingsbilder: ab Werk «Meine Dateien», wählbar. Grenzen (Datei, Benutzer, gesamt, 2 GB frei) wie beim Hochladen (639zzc).
#   * Live-Reiter unverändert (kein Hinweis auf body[data-tab=live]); die Funk-Seite (639zzzf) bekommt das Skript nicht.
#   * Zusammenspiel mit Vorlesen (639zzzzv) / Eigene Orte (639zzzzo): nur über die verkettbaren Haken window.tzCard /
#     window.tzOpen der Rucksack-Seite, falls vorhanden – hier nicht gebraucht, 639zzc bleibt unverändert.
# Tests: werkzeuge/rucksack_io_test.py (Liste, Rechte, Privat, Grenzen, Wächter; --browser: Knöpfe, Wählen, Speichern, 390 px).
# ----------------------------------------------------------------------------
from urllib.parse import urlsplit as _rk_urlsplit, unquote as _rk_unquote, parse_qsl as _rk_parse_qsl

# (path pattern - matched in full on the decoded path, allowed query keys, mode, kind)
# mode: "private" = only «My files» (enforced on the device), "mine" = «My files» preselected, "all" = «For everyone» preselected
_RK_N = r"[^/?#\\\x00-\x1f]{1,160}"                         # one file name (decoded)
RK_EXPORTS = (
    (r"/api/settings/export", (), "private", "data"),
    (r"/tools/diag\.zip", (), "private", "archive"),
    (r"/api/nacht/export/[A-Za-z0-9_.-]{1,80}", (), "private", "data"),
    (r"/api/factory/backup/[A-Za-z0-9_.-]{1,120}", (), "private", "data"),
    (r"/api/sim/sicherung/[A-Za-z0-9_.-]{1,120}", (), "private", "data"),
    (r"/api/simtest/report\.zip", ("lang",), "private", "archive"),
    (r"/api/servo/export", ("fmt",), "all", "data"),
    (r"/api/dataset\.zip", (), "mine", "archive"),
    (r"/touren/x/[A-Za-z0-9_-]{1,40}\.(gpx|kml|zip)", ("lang",), "all", "route"),
    (r"/tausch/pack/x/[A-Za-z0-9_-]{1,40}\.(csv|json|zip|txt|md|pdf)", ("lang",), "all", "doc"),
    (r"/api/qrk/card/[A-Za-z0-9_-]{1,40}\.(png|svg|pdf)", ("dl", "lang", "t", "size"), "all", "image"),
    (r"/build/datei/[A-Za-z0-9_. ()+-]{1,120}(/[A-Za-z0-9_. ()+-]{1,120}){0,3}", (), "all", "doc"),
    (r"/build/(alle|transport|platten)\.zip", (), "all", "archive"),
    (r"/diary/img/[A-Za-z0-9_.-]{1,120}", (), "mine", "image"),
    (r"/rec/file/" + _RK_N, ("dl",), "mine", "video"),
    (r"/rec/report/" + _RK_N, ("lang",), "mine", "pdf"),
    (r"/rec/zip", ("names",), "mine", "archive"),
)
_RK_RE = tuple((re.compile(p), frozenset(q), m, k) for p, q, m, k in RK_EXPORTS)
RK_QV_MAX = 4000                                           # one query value (the names of a recordings ZIP)


def rk_export_find(url):
    """the RK_EXPORTS entry of a same-site address (path + query as the page has it) -> (path_raw, query, mode, kind) or None"""
    try:
        s = str(url or "")
        if len(s) > 6000 or any(c in s for c in "\\\r\n\t\x00"):
            return None
        u = _rk_urlsplit(s)
    except ValueError:
        return None
    if u.scheme or u.netloc or u.fragment or not u.path.startswith("/") or u.path.startswith("//"):
        return None
    path = _rk_unquote(u.path)
    if ".." in path or "//" in path or path.startswith(("/tausch/dl", "/api/tausch", "/g/")):
        return None
    try:
        q = _rk_parse_qsl(u.query, keep_blank_values=True, strict_parsing=bool(u.query))
    except ValueError:
        return None
    for rx, keys, mode, kind in _RK_RE:
        if rx.fullmatch(path):
            if all(k in keys and len(v) <= RK_QV_MAX and not any(ord(c) < 32 for c in v) for k, v in q):
                return u.path, u.query, mode, kind
            return None
    return None


def rk_disp_name(cd, path):
    """the file name from Content-Disposition (filename*=UTF-8'' first), else the last part of the address"""
    cd = str(cd or "")
    m = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", cd, re.I)
    if m:
        n = _rk_unquote(m.group(1).strip().strip('"'))
    else:
        m = re.search(r'filename\s*=\s*"([^"]*)"', cd, re.I) or re.search(r"filename\s*=\s*([^;]+)", cd, re.I)
        n = m.group(1).strip() if m else _rk_unquote(path.rstrip("/").rsplit("/", 1)[-1])
    return n or "datei"


def rk_probe(who, lang=None):
    lim = tausch_limits()
    return {"ok": True, "on": bool(CFG.get("tausch_on", True)), "view": "files_view" in who["perms"],
            "down": "files_down" in who["perms"], "up": "files_up" in who["perms"] and bool(CFG.get("tausch_on", True)),
            "max": lim["file"], "exports": [[p, sorted(q), m, k] for p, q, m, k in RK_EXPORTS]}


def rk_fetch_export(app, req, g_, path, query, spool, cap, lang=None):
    """run the export address as the same user (all request guards except the login itself, which already happened for this
    request) and write its answer into «spool». -> (ok, error, name, size)"""
    from flask import request as _req
    if getattr(g_, "appkey", None):
        return False, tr("not allowed for your user", lang), "", 0
    hdr = {k: v for k, v in req.headers.items() if k.lower() not in ("content-length", "content-type", "transfer-encoding", "origin",
                                                                    "range", "if-none-match", "if-modified-since", "accept-encoding")}
    env = {"REMOTE_ADDR": req.remote_addr or "127.0.0.1"}
    if req.environ.get("mw.funnel"):
        env["mw.funnel"] = req.environ["mw.funnel"]
    resp = None
    with app.test_request_context(path, method="GET", query_string=query, headers=hdr, environ_base=env):
        try:
            for f in app.before_request_funcs.get(None, ()):
                if getattr(f, "__name__", "") == "auth":          # the login: already done for this request (g is the same)
                    continue
                rv = f()
                if rv is not None:
                    return False, tr("not allowed for your user", lang), "", 0
            resp = app.make_response(app.dispatch_request())
            if resp.status_code != 200:
                return False, tr("The download did not work.", lang) + f" (HTTP {resp.status_code})", "", 0
            name = rk_disp_name(resp.headers.get("Content-Disposition"), _req.path)
            n = 0
            resp.direct_passthrough = False
            with open(spool, "wb") as f:
                for part in resp.iter_encoded():
                    n += len(part)
                    if n > cap:
                        return False, tr("The file is too big for the backpack.", lang), name, n
                    f.write(part)
            return True, "", name, n
        except Exception as e:
            log_event("web", f"Backpack: export {path[:60]} failed ({e.__class__.__name__})")
            return False, tr("The download did not work.", lang), "", 0
        finally:
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass


def rk_save_export(app, req, g_, d, lang=None):
    """POST /api/tausch/io {action: "save", url, name?, area, folder} -> (ok, error, extra)"""
    who = tausch_who(g_)
    if "files_up" not in who["perms"] or not CFG.get("tausch_on", True):
        return False, tr("You may not upload files.", lang), {}
    hit = rk_export_find(d.get("url"))
    if hit is None:
        return False, tr("This download cannot be saved in the backpack.", lang), {}
    path, query, mode, kind = hit
    area = "mine" if mode == "private" or d.get("area") == "mine" else "all"
    folder = str(d.get("folder") or "")[:80] if area == "all" else ""
    root = _tz_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), {}
    spool = os.path.join(root, "up", "rk_" + secrets.token_hex(8) + ".tmp")
    try:
        ok, err, name, size = rk_fetch_export(app, req, g_, path, query, spool, tausch_limits()["file"], lang)
        if not ok:
            return False, err, {}
        want = str(d.get("name") or "").strip()[:200]
        ok, err, st = tausch_up_start(who, {"name": want or name, "size": size, "area": area, "folder": folder,
                                            "lastmod": int(time.time())}, lang)
        if not ok:
            return False, err, {}
        uid, off = st["id"], st.get("have", 0)
        with open(spool, "rb") as f:
            f.seek(off)
            while off < size:
                data = f.read(TZ_CHUNK)
                if not data:
                    break
                ok, err, off, code = tausch_up_chunk(who, uid, off, data, lang)
                if not ok:
                    tausch_up_abort(who, uid, lang)
                    return False, err, {}
        ok, err, res = tausch_up_finish(who, uid, lang)
        if ok:
            res["private"] = mode == "private"
        return ok, err, res
    finally:
        try:
            os.remove(spool)
        except OSError:
            pass


_RK_TX = {   # english key: (de, fr, it, rm)
    "From the backpack": ("Aus dem Rucksack", "Depuis le sac à dos", "Dallo zaino", "Ord il satgados"),
    "Into the backpack": ("In den Rucksack", "Dans le sac à dos", "Nello zaino", "En il satgados"),
    "Choose from the backpack": ("Aus dem Rucksack wählen", "Choisir dans le sac à dos", "Scegli dallo zaino", "Tscherner ord il satgados"),
    "Save in the backpack": ("In den Rucksack speichern", "Enregistrer dans le sac à dos", "Salva nello zaino", "Memorisar en il satgados"),
    "Saved in the backpack": ("Im Rucksack gespeichert", "Enregistré dans le sac à dos", "Salvato nello zaino", "Memorisà en il satgados"),
    "For everyone": ("Für alle", "Pour tous", "Per tutti", "Per tuts"),
    "My files": ("Meine Dateien", "Mes fichiers", "I miei file", "Mias datotecas"),
    "Search": ("Suchen", "Rechercher", "Cerca", "Tschertgar"),
    "All": ("Alle", "Tous", "Tutti", "Tuts"),
    "Pictures": ("Bilder", "Images", "Immagini", "Maletgs"),
    "Documents": ("Dokumente", "Documents", "Documenti", "Documents"),
    "Sound": ("Ton", "Son", "Audio", "Tun"),
    "files": ("Dateien", "fichiers", "file", "datotecas"),
    "Choose": ("Wählen", "Choisir", "Scegli", "Tscherner"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "Save": ("Speichern", "Enregistrer", "Salva", "Memorisar"),
    "Name": ("Name", "Nom", "Nome", "Num"),
    "Where": ("Wohin", "Où", "Dove", "Nua"),
    "Back": ("Zurück", "Retour", "Indietro", "Enavos"),
    "Open": ("Öffnen", "Ouvrir", "Apri", "Avrir"),
    "free": ("frei", "libre", "libero", "liber"),
    "No matching files.": ("Keine passenden Dateien.", "Aucun fichier correspondant.", "Nessun file adatto.", "Naginas datotecas adattadas."),
    "Only files that fit here are shown": ("Nur Dateien, die hier passen", "Seuls les fichiers adaptés sont affichés",
                                           "Solo i file adatti sono mostrati", "Mo datotecas che s’adattan èn mussadas"),
    "Choose a file": ("Datei wählen", "Choisir un fichier", "Scegli un file", "Tscherner ina datoteca"),
    "From this device": ("Von diesem Gerät", "Depuis cet appareil", "Da questo dispositivo", "Da quest apparat"),
    "Name of the download": ("Name des Downloads", "Nom du téléchargement", "Nome del download", "Num dal download"),
    "Downloaded": ("Heruntergeladen", "Téléchargé", "Scaricato", "Telechargià"),
    "Private data – saved only in «My files».": ("Private Daten – nur in «Meine Dateien».", "Données privées – seulement dans «Mes fichiers».",
                                                 "Dati privati – solo in «I miei file».", "Datas privatas – mo en «Mias datotecas»."),
    "A file with this name is there – it is saved as": ("Eine Datei mit diesem Namen gibt es schon – gespeichert als",
                                                        "Un fichier de ce nom existe déjà – il sera enregistré sous",
                                                        "Esiste già un file con questo nome – sarà salvato come",
                                                        "Ina datoteca cun quest num exista gia – memorisada sco"),
    "The file could not be loaded.": ("Die Datei liess sich nicht laden.", "Le fichier n’a pas pu être chargé.",
                                      "Impossibile caricare il file.", "La datoteca n’ha betg pudì vegnir chargiada."),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione a MoveEye.",
                                  "Nagina connexiun cun MoveEye."),
    "This download cannot be saved in the backpack.": ("Dieser Download lässt sich nicht im Rucksack speichern.",
                                                       "Ce téléchargement ne peut pas être enregistré dans le sac à dos.",
                                                       "Questo download non può essere salvato nello zaino.",
                                                       "Quest download na po betg vegnir memorisà en il satgados."),
    "The download did not work.": ("Der Download hat nicht geklappt.", "Le téléchargement n’a pas fonctionné.", "Il download non ha funzionato.",
                                   "Il download n’ha betg funcziunà."),
    "The file is too big for the backpack.": ("Die Datei ist zu gross für den Rucksack.", "Le fichier est trop grand pour le sac à dos.",
                                              "Il file è troppo grande per lo zaino.", "La datoteca è memia gronda per il satgados."),
}
for _k, _v in _RK_TX.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

for _p in TZ_PERMS:                                         # GET /api/tausch/io is already under /api/tausch (perm_get_ok)
    PERM_POST[_p] = set(PERM_POST.get(_p, ())) | {"/api/tausch/io"}
VIEW_GET_PAGES.add("/rk/io.js")                             # the script itself is no data (the probe says what the user may)

RK = {"js": None, "v": ""}


def rk_js():
    """the script with the texts of all languages (built once)"""
    if RK["js"] is None:
        tx = {L: {k: (v[0] if L == "de" else v[1 + ("fr", "it", "rm").index(L)]) for k, v in _RK_TX.items()} for L in ("de", "fr", "it", "rm")}
        js = RK_IO_JS.replace("/*RKTX*/{}", json.dumps(tx, ensure_ascii=False), 1)
        RK["v"] = hashlib.sha256(js.encode("utf-8")).hexdigest()[:12]
        RK["js"] = js
    return RK["js"]


_render_page_before_rk = render_page


# wraps: render_page
def render_page(page, active):
    """+ 639zzzzr: the backpack script on every page with tabs (not the guest pages)"""
    out = _render_page_before_rk(page, active)
    if '<nav class="nav">' not in out or "</body>" not in out or "/rk/io.js" in out:
        return out
    rk_js()
    i = out.rfind("</body>")
    return out[:i] + '<script src="/rk/io.js?v=' + RK["v"] + '" defer></script>' + out[i:]


_smalltv_routes_639zzzzr = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzzr: /rk/io.js, /api/tausch/io
    _smalltv_routes_639zzzzr(app, reply, body)
    from flask import request, Response, g

    @app.route("/rk/io.js")
    def rk_io_js():
        js = rk_js()
        cache = "private, max-age=86400" if request.args.get("v") == RK["v"] else "no-cache"
        return Response(js, mimetype="text/javascript", headers={"Cache-Control": cache, "X-Content-Type-Options": "nosniff"})

    @app.route("/api/tausch/io", methods=["GET", "POST"])
    def api_tausch_io():
        who = tausch_who(g)
        if request.method == "GET":
            L = norm_lang(request.args.get("lang") or CFG.get("lang"))
            if not who["perms"] or getattr(g, "appkey", None):
                return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
            return reply(rk_probe(who, L))
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if d.get("action") != "save":
            return reply({"ok": False, "error": tr("unknown action", L)}, 400)
        if not tausch_rate(who["key"], "io", 60):
            return reply({"ok": False, "error": tr("Too many uploads in a short time - wait a few minutes.", L)}, 429)
        ok, err, res = rk_save_export(app, request, g, d, L)
        return reply(dict(res, ok=ok, error=err or None), 200 if ok else 400)


RK_IO_JS = r"""/* MoveEye 639zzzzr – «🎒 Rucksack bei Import/Export»: pick files from the Digital backpack into any file field, save exports there */
(function () {
"use strict";
if (window.mwRucksack) return;
const TXA = /*RKTX*/{};
const L = () => (document.documentElement.lang || "de").slice(0, 2);
const t = k => (TXA[L()] || {})[k] || k;
const KIC = {image: "🖼", video: "🎬", audio: "🎵", pdf: "📕", text: "📝", doc: "📄", archive: "🗜", chat: "💬", route: "🥾", data: "🧾"};
const TYPES = {image: ["jpg", "jpeg", "png", "webp", "heic", "heif", "gif", "bmp"], audio: ["wav", "m4a", "mp3", "ogg", "opus", "aac", "flac"],
  video: ["mp4", "mov", "webm", "m4v"], json: ["json"]};
const NO_PICK = ["tz-file"];                                                    // the upload of the backpack page itself
const RK_TYPES = {"kt-file": ["gpx", "kml", "zip"], "imp-file": ["json"]};     // file fields without (or with a too wide) «accept»
const ext = n => ((n || "").toLowerCase().match(/\.([a-z0-9]{1,8})$/) || [, ""])[1];
const kindOf = f => ["gpx", "kml"].includes(ext(f.name)) ? "route" : ext(f.name) === "json" ? "data" : f.kind;
const fmt = n => n >= 1073741824 ? (n / 1073741824).toFixed(1).replace(".0", "") + " GB" : n >= 1048576 ? (n / 1048576).toFixed(n >= 10485760 ? 0 : 1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
const when = s => { const d = new Date(s * 1000), now = new Date(), loc = L() === "en" ? "en-GB" : L() + "-CH";
  const hm = d.toLocaleTimeString(loc, {hour: "2-digit", minute: "2-digit"});
  return d.toDateString() === now.toDateString() ? hm : d.toLocaleDateString(loc, {day: "2-digit", month: "2-digit"}) + " " + hm; };
const E = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const B = (cls, txt) => { const b = E("button", cls, txt); b.type = "button"; return b; };

const CSS = `
#rk-ov{position:fixed;inset:0;z-index:1300;display:flex;align-items:flex-end;justify-content:center;background:rgba(0,0,0,.5);animation:rkf .18s ease-out}
@media(min-width:700px){#rk-ov{align-items:center}}
@keyframes rkf{from{opacity:0}}@keyframes rku{from{transform:translateY(40px);opacity:.4}}
#rk-ov .rk{width:100%;max-width:560px;max-height:min(86vh,720px);display:flex;flex-direction:column;background:var(--panel,#111822);color:var(--txt,#e8eef5);
  border:1px solid var(--line,#1f2b3a);border-radius:20px 20px 0 0;box-shadow:0 18px 60px rgba(0,0,0,.55);animation:rku .22s cubic-bezier(.2,.8,.2,1);
  padding-bottom:env(safe-area-inset-bottom,0px);font-size:15px;text-align:left}
@media(min-width:700px){#rk-ov .rk{border-radius:20px}}
@media(prefers-reduced-motion:reduce){#rk-ov,#rk-ov .rk,#rk-toast{animation:none}}
#rk-ov button{font:inherit;cursor:pointer;border:0}
.rk-hd{display:flex;align-items:center;gap:10px;padding:10px 8px 10px 16px;border-bottom:1px solid var(--line,#1f2b3a);min-height:60px}
.rk-hd b{flex:1;min-width:0;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#rk-ov .rk-x{flex:none;width:44px;height:44px;padding:0;border-radius:50%;background:rgba(127,140,160,.18);color:var(--txt,#e8eef5);font-size:18px}
.rk-tabs{display:flex;gap:4px;margin:12px 16px 0;padding:3px;border:1px solid var(--line,#1f2b3a);border-radius:12px;background:var(--field,#0c121a)}
#rk-ov .rk-tabs button{flex:1;min-height:44px;background:none;color:var(--mut,#8a9bb0);border-radius:9px;font-weight:600}
#rk-ov .rk-tabs button.on{background:var(--acc,#3b8cff);color:#fff}
.rk-tools{display:flex;gap:8px;padding:10px 16px 0}
.rk-q{flex:1;min-width:0;min-height:44px;padding:0 12px 0 38px;border:1px solid var(--line,#1f2b3a);border-radius:11px;background:var(--field,#0c121a) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%238a9bb0' stroke-width='2'%3E%3Ccircle cx='8' cy='8' r='6'/%3E%3Cpath d='m13 13 4 4'/%3E%3C/svg%3E") 12px 50% no-repeat;color:var(--txt,#e8eef5);font:inherit;font-size:16px;box-sizing:border-box}
.rk-chips{display:flex;gap:6px;overflow-x:auto;padding:10px 16px 2px;scrollbar-width:none}.rk-chips::-webkit-scrollbar{display:none}
#rk-ov .rk-chips button{flex:none;min-height:36px;padding:0 13px;border-radius:99px;border:1px solid var(--line,#1f2b3a);background:var(--field,#0c121a);color:var(--mut,#8a9bb0);font-size:13px;font-weight:600}
#rk-ov .rk-chips button.on{border-color:var(--acc,#3b8cff);color:var(--txt,#e8eef5);background:color-mix(in srgb,var(--acc,#3b8cff) 22%,var(--field,#0c121a))}
.rk-crumb{display:flex;align-items:center;gap:8px;padding:8px 16px 0;color:var(--mut,#8a9bb0);font-size:13px;min-height:44px}
#rk-ov .rk-crumb button{min-height:44px;padding:0 12px;border-radius:10px;background:var(--btn2,#1a2433);color:var(--txt,#e8eef5)}
.rk-list{flex:1;min-height:120px;overflow:auto;padding:6px 8px 8px;overscroll-behavior:contain}
#rk-ov .rk-row{display:flex;align-items:center;gap:12px;width:100%;min-height:60px;padding:6px 10px;border-radius:12px;background:none;color:var(--txt,#e8eef5);text-align:left;font-weight:400}
#rk-ov .rk-row:hover{background:var(--field,#0c121a)}#rk-ov .rk-row[aria-selected=true]{background:color-mix(in srgb,var(--acc,#3b8cff) 20%,transparent);outline:1px solid var(--acc,#3b8cff)}
.rk-th{flex:none;width:46px;height:46px;border-radius:9px;background:var(--field,#0c121a);display:grid;place-items:center;font-size:22px;overflow:hidden}
.rk-th img{width:100%;height:100%;object-fit:cover}
.rk-tx{flex:1;min-width:0}.rk-tx b{display:block;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk-tx small{display:block;color:var(--mut,#8a9bb0);font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk-go{flex:none;color:var(--mut,#8a9bb0);font-size:18px}
.rk-empty{padding:28px 16px;text-align:center;color:var(--mut,#8a9bb0)}
.rk-ft{display:flex;gap:10px;align-items:center;padding:12px 16px;border-top:1px solid var(--line,#1f2b3a)}
.rk-ft .rk-info{flex:1;min-width:0;color:var(--mut,#8a9bb0);font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rk-ov .rk-ft button{min-height:44px;min-width:96px;padding:0 16px;border-radius:12px;background:var(--acc,#3b8cff);color:#fff;font-weight:600}
#rk-ov .rk-ft button.sec{background:var(--btn2,#1a2433);color:var(--txt,#e8eef5)}
#rk-ov .rk-ft button:disabled{opacity:.5;cursor:default}
.rk-form{padding:14px 16px 4px;display:grid;grid-template-columns:minmax(0,1fr);gap:12px;overflow:auto}
.rk-form>*{min-width:0}
.rk-form label{display:grid;gap:6px;font-weight:600;font-size:13px;color:var(--mut,#8a9bb0)}
.rk-form input,.rk-form select{min-height:44px;padding:0 12px;border:1px solid var(--line,#1f2b3a);border-radius:11px;background:var(--field,#0c121a);color:var(--txt,#e8eef5);font:inherit;font-size:16px;min-width:0;width:100%;box-sizing:border-box}
.rk-file{display:flex;gap:12px;align-items:center;padding:10px 12px;border:1px solid var(--line,#1f2b3a);border-radius:12px;background:var(--field,#0c121a)}
.rk-note{font-size:12.5px;color:var(--yel,#e0a526)}
.rk-err{font-size:13px;color:var(--red,#ff6b6b)}
.rk-ch{display:grid;gap:10px;padding:14px 16px 16px}
#rk-ov .rk-ch button{display:flex;align-items:center;gap:12px;min-height:56px;padding:0 16px;border-radius:14px;background:var(--btn2,#1a2433);color:var(--txt,#e8eef5);font-weight:600;font-size:16px;text-align:left}
#rk-ov .rk-ch button span{font-size:22px}
.rk-mini{display:inline-flex;align-items:center;justify-content:center;min-width:44px;min-height:44px;padding:0 8px;margin-left:4px;border:0;border-radius:10px;background:var(--btn2,#1a2433);color:var(--txt,#e8eef5);font-size:17px;vertical-align:middle;cursor:pointer}
#rk-toast{position:fixed;left:50%;bottom:calc(22px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:1400;display:flex;align-items:center;gap:10px;
  width:max-content;max-width:calc(100% - 32px);box-sizing:border-box;padding:6px 8px 6px 16px;border-radius:12px;background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--grn,#3fcf6b);
  box-shadow:0 10px 30px rgba(0,0,0,.45);font-weight:600;animation:rku .2s ease-out}
#rk-toast.off{border-color:var(--line,#1f2b3a)}
#rk-toast span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rk-toast a,#rk-toast button{color:var(--acc2,#6aa9ff);font:inherit;font-weight:600;white-space:nowrap;min-height:44px;display:inline-flex;align-items:center;padding:0 8px;background:none;border:0;cursor:pointer}
`;
function css() { if (document.getElementById("rk-css")) return; const s = E("style"); s.id = "rk-css"; s.textContent = CSS; document.head.appendChild(s); }

let CAP = null, EX = [];
const probe = fetch("/api/tausch/io?lang=" + L(), {cache: "no-store", credentials: "same-origin"}).then(r => r.ok ? r.json() : null).catch(() => null).then(j => {
  if (!j || !j.ok || !j.on) return null;
  CAP = j; CAP.pick = j.view && j.down;
  EX = (j.exports || []).map(([p, q, m, k]) => { try { return {re: new RegExp("^(?:" + p + ")$"), q, m, k}; } catch (e) { return null; } }).filter(Boolean);
  return CAP;
});
async function api(q) { const r = await fetch("/api/tausch?" + q, {cache: "no-store"}); return r.json(); }
function post(u, b) { return fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b))})
  .then(r => r.json()).catch(() => ({ok: false, error: t("No connection to MoveEye.")})); }

// ---- an export address of this MoveEye that the device may copy itself (RK_EXPORTS) ----
function exportOf(href) {
  let u; try { u = new URL(href, location.href); } catch (e) { return null; }
  if (u.origin !== location.origin) return null;
  let p; try { p = decodeURIComponent(u.pathname); } catch (e) { return null; }
  if (p.includes("..")) return null;
  for (const e of EX) if (e.re.test(p)) { for (const k of u.searchParams.keys()) if (!e.q.includes(k)) return null; return {url: u.pathname + u.search, mode: e.m, kind: e.k}; }
  return null;
}
const nameOf = (a, href) => a && a.getAttribute("download") || decodeURIComponent(((href || "").split("?")[0].split("/").pop()) || "datei");

function dialog(title) {
  css(); const old = document.getElementById("rk-toast"); if (old) old.remove();
  const ov = E("div"); ov.id = "rk-ov"; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", title);
  const box = E("div", "rk"), hd = E("div", "rk-hd"), x = B("rk-x", "✕"); x.setAttribute("aria-label", t("Cancel"));
  hd.append(E("b", "", title), x); box.appendChild(hd); ov.appendChild(box); document.body.appendChild(ov);
  const back = document.activeElement; let open = true;
  const close = () => { if (!open) return; open = false; ov.remove(); document.removeEventListener("keydown", esc, true); try { back && back.focus && back.focus({preventScroll: true}); } catch (e) {} };
  const cancel = () => { close(); ov.dispatchEvent(new Event("rk-cancel")); };
  const esc = e => { if (e.key === "Escape") { e.stopPropagation(); e.preventDefault(); cancel(); } };
  document.addEventListener("keydown", esc, true);
  x.onclick = cancel; ov.onclick = e => { if (e.target === ov) cancel(); };
  return {ov, box, close};
}

// ---- pick: -> Promise<null | {id, name, size, kind, file()}> ----
function pick(opt) {
  opt = opt || {};
  const want = [].concat(opt.types || []).flatMap(x => TYPES[x] || [String(x).replace(/^\./, "").toLowerCase()]);
  return new Promise(res => {
    const D = dialog("🎒 " + t("Choose from the backpack")), S = {area: "all", folder: "", q: "", f: want.length ? "want" : "", sel: null, data: null};
    const tabs = E("div", "rk-tabs"), tA = B("on", t("For everyone")), tM = B("", t("My files")); tabs.append(tA, tM);
    const tools = E("div", "rk-tools"), q = E("input", "rk-q"); q.type = "search"; q.placeholder = t("Search"); q.setAttribute("aria-label", t("Search")); tools.appendChild(q);
    const chips = E("div", "rk-chips"), crumb = E("div", "rk-crumb"), list = E("div", "rk-list"); list.setAttribute("role", "listbox");
    const ft = E("div", "rk-ft"), info = E("div", "rk-info"), bC = B("sec", t("Cancel")), bO = B("", t("Choose")); bO.disabled = true; ft.append(info, bC, bO);
    D.box.append(tabs, tools, chips, crumb, list, ft);
    const CH = [["", t("All")]].concat(want.length ? [["want", opt.label || want.slice(0, 3).map(x => x.toUpperCase()).join(" · ")]] : [],
      [["image", "🖼 " + t("Pictures")], ["doc", "📄 " + t("Documents")], ["audio", "🎵 " + t("Sound")]]);
    CH.forEach(([k, n]) => { const b = B(k === S.f ? "on" : "", n); b.onclick = () => { S.f = k; [...chips.children].forEach(c => c.classList.toggle("on", c === b)); paint(); }; chips.appendChild(b); });
    let busy = false;
    const done = v => { D.close(); res(v); }; D.ov.addEventListener("rk-cancel", () => res(null)); bC.onclick = () => done(null);
    bO.onclick = () => { if (S.sel) done(wrap(S.sel)); };
    tA.onclick = () => { S.area = "all"; S.folder = ""; tA.classList.add("on"); tM.classList.remove("on"); load(); };
    tM.onclick = () => { S.area = "mine"; S.folder = ""; tM.classList.add("on"); tA.classList.remove("on"); load(); };
    q.oninput = () => { S.q = q.value.trim().toLowerCase(); paint(); };
    async function load() { if (busy) return; busy = true; list.textContent = "…";
      try { S.data = await api("area=" + S.area + "&folder=" + encodeURIComponent(S.folder) + "&lang=" + L()); } catch (e) { S.data = {files: [], folders: [], error: t("No connection to MoveEye.")}; }
      busy = false; S.sel = null; paint(); }
    function ok(f) { const e = ext(f.name);
      if (S.f === "want") return want.includes(e); if (S.f === "image") return f.kind === "image"; if (S.f === "doc") return ["doc", "pdf", "text"].includes(f.kind) || ["json", "gpx", "kml", "csv"].includes(e);
      if (S.f === "audio") return f.kind === "audio"; return true; }
    function paint() {
      const J = S.data || {files: [], folders: []}; list.textContent = ""; crumb.textContent = ""; bO.disabled = !S.sel;
      if (S.folder) { const b = B("", "‹ " + t("Back")); b.onclick = () => { S.folder = ""; load(); }; crumb.append(b, E("span", "", "📁 " + S.folder)); }
      else crumb.append(E("span", "", S.area === "all" ? "🎒 " + t("For everyone") : "🔒 " + t("My files")));
      if (!S.folder && S.area === "all") (J.folders || []).filter(d => !S.q || d.name.toLowerCase().includes(S.q)).forEach(d => {
        const r = B("rk-row"), th = E("div", "rk-th", "📁"), tx = E("div", "rk-tx");
        tx.append(E("b", "", d.name), E("small", "", d.n + " " + t("files") + " · " + fmt(d.size || 0))); r.append(th, tx, E("span", "rk-go", "›"));
        r.onclick = () => { S.folder = d.name; load(); }; list.appendChild(r); });
      const fs = (J.files || []).filter(f => f.kind !== "chat" && f.dl !== false && ok(f) && (!S.q || f.name.toLowerCase().includes(S.q)));
      fs.forEach(f => {
        const r = B("rk-row"); r.setAttribute("role", "option"); r.setAttribute("aria-selected", S.sel === f ? "true" : "false");
        const th = E("div", "rk-th"); if (f.thumb) { const im = E("img"); im.alt = ""; im.loading = "lazy"; im.src = "/tausch/thumb/" + f.id + ".jpg"; im.onerror = () => { im.remove(); th.textContent = KIC[kindOf(f)] || "📦"; }; th.appendChild(im); } else th.textContent = KIC[kindOf(f)] || "📦";
        const tx = E("div", "rk-tx"); tx.append(E("b", "", f.name), E("small", "", (ext(f.name) || "?").toUpperCase() + " · " + fmt(f.size) + " · " + when(f.t) + (f.by && !f.mine ? " · " + f.by : "")));
        r.append(th, tx); r.onclick = () => { S.sel = f; paint(); }; r.ondblclick = () => done(wrap(f)); list.appendChild(r); });
      if (!list.children.length) list.appendChild(E("div", J.error ? "rk-empty rk-err" : "rk-empty", J.error || t("No matching files.")));
      info.textContent = S.sel ? S.sel.name : (S.f === "want" ? t("Only files that fit here are shown") : "");
    }
    load(); if (matchMedia("(pointer:fine)").matches) setTimeout(() => q.focus({preventScroll: true}), 60);
  });
}
function wrap(f) {
  const url = "/tausch/dl/" + f.id;
  return {id: f.id, name: f.name, size: f.size, kind: f.kind,
    file: () => fetch(url, {cache: "no-store"}).then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.blob(); })
      .then(b => new File([b], f.name, {type: b.type || "application/octet-stream", lastModified: (f.t || 0) * 1000}))};
}
// the chosen file into a file field: the page reads it like a file from the device
async function into(inp, f) {
  let file; try { file = await f.file(); } catch (e) { toast("⚠ " + t("The file could not be loaded.") + " (" + (e.message || e) + ")", null, true); return false; }
  const dt = new DataTransfer(); dt.items.add(file); inp.files = dt.files;
  inp.dispatchEvent(new Event("input", {bubbles: true})); inp.dispatchEvent(new Event("change", {bubbles: true})); return true;
}
function typesOf(inp) {
  if (RK_TYPES[inp.id]) return RK_TYPES[inp.id];
  const out = []; (inp.getAttribute("accept") || "").split(",").map(s => s.trim().toLowerCase()).filter(Boolean).forEach(a => {
    if (a.startsWith(".")) out.push(a.slice(1)); else if (a.endsWith("/*") && TYPES[a.slice(0, -2)]) out.push(...TYPES[a.slice(0, -2)]);
    else if (a === "application/json") out.push("json"); else if (a.startsWith("image/")) out.push(a.slice(6) === "jpeg" ? "jpg" : a.slice(6)); });
  return [...new Set(out)];
}
async function pickInto(inp) { const f = await pick({types: typesOf(inp)}); if (f) await into(inp, f); }

// ---- save: {name, url | blob, mode, kind} -> Promise<null | file> ----
function save(opt) {
  opt = opt || {};
  return new Promise(async res => {
    const priv = opt.mode === "private", D = dialog("🎒 " + t("Save in the backpack"));
    let J = {}; try { J = await api("area=all&lang=" + L()); } catch (e) {}
    const F = E("div", "rk-form"), fl = E("div", "rk-file"), th = E("div", "rk-th", KIC[opt.kind] || "📄"), tx = E("div", "rk-tx");
    const tN = E("b", "", opt.name || "…"); tx.append(tN, E("small", "", opt.what || "")); fl.append(th, tx);
    const lN = E("label", "", t("Name")), iN = E("input"); iN.value = opt.name || ""; iN.placeholder = t("Name of the download");
    if (opt.nameP) opt.nameP.then(n => { if (n && !iN.value) { iN.value = n; tN.textContent = n; chk(); } }); iN.maxLength = 200; iN.setAttribute("autocomplete", "off"); lN.appendChild(iN);
    const lW = E("label", "", t("Where")), sW = E("select");
    const opts = priv ? [["mine|", "🔒 " + t("My files")]] : [["all|", "🎒 " + t("For everyone")]].concat((J.folders || []).map(d => ["all|" + d.name, "🎒 " + t("For everyone") + " › 📁 " + d.name]), [["mine|", "🔒 " + t("My files")]]);
    opts.forEach(([v, n]) => { const o = E("option", "", n); o.value = v; sW.appendChild(o); });
    sW.value = priv || opt.mode === "mine" ? "mine|" : "all|"; sW.disabled = priv; lW.appendChild(sW);
    F.append(fl, lN, lW); if (priv) F.appendChild(E("div", "rk-note", "🔒 " + t("Private data – saved only in «My files».")));
    const taken = new Set((J.files || []).map(f => f.name.toLowerCase())), nt = E("div", "rk-note"), er = E("div", "rk-err"); nt.hidden = er.hidden = true; F.append(nt, er);
    const chk = () => { const n = iN.value.trim(); if (sW.value !== "all|" || !taken.has(n.toLowerCase())) { nt.hidden = true; return; }
      const m = n.match(/^(.*?)(\.[^.]+)?$/); let i = 2; while (taken.has((m[1] + " (" + i + ")" + (m[2] || "")).toLowerCase())) i++;
      nt.hidden = false; nt.textContent = "ⓘ " + t("A file with this name is there – it is saved as") + " «" + m[1] + " (" + i + ")" + (m[2] || "") + "»"; };
    iN.oninput = chk; sW.onchange = chk; chk();
    const ft = E("div", "rk-ft"), info = E("div", "rk-info"), Q = J.quota || {}, bC = B("sec", t("Cancel")), bS = B("", "🎒 " + t("Save"));
    info.textContent = Q.total ? fmt(Math.max(0, Math.min(Q.total - Q.used, Q.user_max ? Q.user_max - (Q.user_used || 0) : Infinity))) + " " + t("free") : ""; ft.append(info, bC, bS);
    D.box.append(F, ft); D.ov.addEventListener("rk-cancel", () => res(null)); bC.onclick = () => { D.close(); res(null); };
    const fail = m => { bS.disabled = false; bS.textContent = "🎒 " + t("Save"); er.hidden = false; er.textContent = "⚠ " + (m || "?"); };
    bS.onclick = async () => {
      bS.disabled = true; bS.textContent = "…"; er.hidden = true;
      const [area, folder] = sW.value.split("|"), name = iN.value.trim() || opt.name;
      let fin;
      if (opt.url) fin = await post("/api/tausch/io", {action: "save", url: opt.url, name, area, folder});
      else {
        let blob; try { blob = opt.blob instanceof Blob ? opt.blob : await opt.blob; } catch (e) { blob = null; }
        if (!blob) { fail(t("The file could not be loaded.")); return; }
        const st = await post("/api/tausch", {action: "start", name, size: blob.size, area, folder, lastmod: Date.now() / 1000 | 0});
        if (!st.ok) { fail(st.error); return; }
        let off = st.have || 0; const cs = st.chunk || 2097152;
        while (off < blob.size) {
          let j; try { const r = await fetch("/api/tausch/chunk?id=" + st.id + "&off=" + off + "&lang=" + L(), {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: await blob.slice(off, off + cs).arrayBuffer()}); j = await r.json(); }
          catch (e) { j = {ok: false, error: t("No connection to MoveEye.")}; }
          if (!j.ok) { post("/api/tausch", {action: "abort", id: st.id}); fail(j.error); return; }
          off = j.have; bS.textContent = Math.round(100 * off / Math.max(1, blob.size)) + " %";
        }
        fin = await post("/api/tausch", {action: "finish", id: st.id});
      }
      if (!fin.ok) { fail(fin.error); return; }
      D.close(); toast("🎒 " + t("Saved in the backpack") + ": " + fin.file.name, {txt: t("Open") + " ›", href: "/tausch"}); res(fin.file);
    };
    if (matchMedia("(pointer:fine)").matches) setTimeout(() => iN.focus({preventScroll: true}), 60);
  });
}
function toast(msg, act, off) {
  css(); let e = document.getElementById("rk-toast"); if (e) e.remove(); e = E("div", off ? "off" : ""); e.id = "rk-toast"; e.setAttribute("role", "status");
  e.appendChild(E("span", "", msg));
  if (act) { const a = act.href ? E("a", "", act.txt) : B("", act.txt); if (act.href) a.href = act.href; else a.onclick = () => { e.remove(); act.run(); }; e.appendChild(a); }
  document.body.appendChild(e); clearTimeout(toast.tm); toast.tm = setTimeout(() => e.remove(), act && act.run ? 9000 : 6000);
}

// ---- the places: buttons next to file fields and download links ----
const hiddenEl = el => el.hidden || el.style.display === "none" || (el.offsetParent === null && getComputedStyle(el).display === "none");
const isTrigger = el => el && /^(BUTTON|A|LABEL)$/.test(el.tagName) && !el.classList.contains("rk-btn") && !el.classList.contains("rk-mini");
function pickBtn(inp, like) {
  const b = B(((like && like.className) || "sec") + " rk-btn", "🎒 " + t("From the backpack")); b.dataset.rkFor = inp.id || ""; b.dataset.rkT = "From the backpack";
  b.onclick = e => { e.preventDefault(); pickInto(inp); }; return b;
}
function saveBtn(a) {
  const big = /(^|\s)btn(\s|$)/.test(a.className), b = B(big ? a.className.replace(/\bmain\b/, "sec") + " rk-btn" : "rk-mini", big ? "🎒 " + t("Into the backpack") : "🎒");
  if (big) b.dataset.rkT = "Into the backpack";
  b.title = t("Save in the backpack"); b.setAttribute("aria-label", t("Save in the backpack") + ": " + nameOf(a, a.href));
  b.onclick = e => { e.preventDefault(); e.stopPropagation(); saveFrom(a); }; return b;
}
// the name the download would get (Content-Disposition) - asked with HEAD only for small exports (no ZIP, no video)
function cdName(cd) { const m = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(cd || "") || /filename\s*=\s*"?([^";]+)"?/i.exec(cd || "");
  if (!m) return ""; try { return decodeURIComponent(m[1].trim()); } catch (e) { return m[1].trim(); } }
function saveFrom(a, blobP) {
  const href = a.href, ex = exportOf(href), name = nameOf(a, href);
  if (ex) { const own = a.getAttribute && a.getAttribute("download");
    const np = own ? null : ["archive", "video"].includes(ex.kind) ? Promise.resolve("") :
      fetch(ex.url, {method: "HEAD", cache: "no-store"}).then(r => r.ok ? cdName(r.headers.get("Content-Disposition")) : "").catch(() => "");
    return save({url: ex.url, name: own ? name : "", nameP: np, mode: ex.mode, kind: ex.kind}); }
  return save({name, blob: blobP || fetch(href).then(r => r.blob()), kind: ext(name) in {png: 1, jpg: 1, jpeg: 1, webp: 1} ? "image" : "doc"});
}
let lastL = "";
function scan() {
  if (!CAP) return;
  if (L() !== lastL) { lastL = L(); document.querySelectorAll(".rk-btn[data-rk-t]").forEach(b => { b.textContent = "🎒 " + t(b.dataset.rkT); });
    document.querySelectorAll(".rk-mini").forEach(b => { b.title = t("Save in the backpack"); }); }
  if (CAP.up) document.querySelectorAll("a[href]").forEach(a => {
    if (a.closest("#rk-ov,#rk-toast,nav,header")) return;
    const fit = !!(exportOf(a.href) || (a.hasAttribute("download") && a.href.startsWith("blob:")));
    let b = a.__rkB;
    if (!b && fit) { b = a.__rkB = saveBtn(a); a.after(b); }
    if (b) { if (!b.isConnected && fit) a.after(b); const h = !fit || a.hidden || a.style.display === "none"; if (b.hidden !== h) b.hidden = h; }
  });
  if (CAP.pick) document.querySelectorAll("input[type=file]:not([data-rk])").forEach(inp => {
    if (inp.closest("#rk-ov") || NO_PICK.includes(inp.id)) { inp.dataset.rk = "no"; return; }
    if (!hiddenEl(inp)) { inp.dataset.rk = "btn"; inp.after(pickBtn(inp, {className: "sec"})); return; }
    const tr = [inp.previousElementSibling, inp.nextElementSibling].find(isTrigger);
    if (tr) { inp.dataset.rk = "btn"; tr.after(pickBtn(inp, tr)); } else inp.dataset.rk = "chooser";
  });
}
let sch = 0; const later = () => { if (!sch) sch = requestAnimationFrame(() => { sch = 0; try { scan(); } catch (e) {} }); };

// a file field opened by a script without a button next to it: ask first «from this device / from the backpack»
const oClick = HTMLInputElement.prototype.click;
HTMLInputElement.prototype.click = function () {
  if (this.type === "file" && CAP && CAP.pick && !["btn", "no"].includes(this.dataset.rk) && !NO_PICK.includes(this.id) && !this.closest("#rk-ov")) { chooser(this); return; }
  return oClick.apply(this, arguments);
};
function chooser(inp) {
  const D = dialog("📂 " + t("Choose a file")), w = E("div", "rk-ch"), d1 = B(""), d2 = B("");
  d1.append(E("span", "", "📱"), document.createTextNode(t("From this device"))); d2.append(E("span", "", "🎒"), document.createTextNode(t("From the backpack")));
  w.append(d1, d2); D.box.appendChild(w);
  d1.onclick = () => { D.close(); oClick.call(inp); };          // still inside the tap: the browser opens its picker
  d2.onclick = () => { D.close(); pickInto(inp); };
  setTimeout(() => d1.focus({preventScroll: true}), 30);
}
// a download a page starts by script (a.click()): a short note «⬇ name · 🎒 Into the backpack» (not on the Live tab)
let lastUser = 0;
document.addEventListener("click", e => { const a = e.target.closest && e.target.closest("a[href]"); if (a && a.__rkB) lastUser = Date.now(); }, true);
const aClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () {
  let blobP = null; const a = this;
  try { if (CAP && CAP.up && a.hasAttribute("download") && a.href.startsWith("blob:")) blobP = fetch(a.href).then(r => r.blob()).catch(() => null); } catch (e) {}
  const r = aClick.apply(this, arguments);
  try {
    if (CAP && CAP.up && a.hasAttribute("download") && !a.__rkB && Date.now() - lastUser > 4000 && (document.body.dataset.tab || "") !== "live"
        && (blobP || exportOf(a.href))) {
      const name = nameOf(a, a.href);
      toast("⬇ " + t("Downloaded") + ": " + name, {txt: "🎒 " + t("Into the backpack"), run: () => saveFrom({href: a.href, getAttribute: () => name}, blobP)}, true);
    }
  } catch (e) {}
  return r;
};

window.mwRucksack = {pick, save, toast, pickInto, ver: 1};
probe.then(c => { if (!c) return; scan(); new MutationObserver(later).observe(document.documentElement, {childList: true, subtree: true, attributes: true, attributeFilter: ["href", "hidden", "download", "lang"]}); });
})();
"""


# ---- the manual: one point in the section «Digitaler Rucksack» (639zzc), 5 languages ---------------------------------------------
RK_HELP_HTML = r"""
de|<li><b>🎒 Bei Import und Export</b>: Wo MoveEye eine Datei liest (Einstellungen laden, Tour importieren, Packliste, Bild, Ton …), steht «🎒 Aus dem Rucksack» – oder es fragt «Von diesem Gerät / Aus dem Rucksack». Neben Downloads (Einstellungen sichern, Touren, Servo-Daten, Aufnahmen, Berichte, Gehäuse-Dateien …) steht «🎒 In den Rucksack»: MoveEye legt die Datei selbst dort ab. Einstellungen, Diagnose, Nacht-Testlauf und Sicherungen enthalten Privates und kommen nur in «Meine Dateien».</li>
en|<li><b>🎒 For import and export</b>: where MoveEye reads a file (load settings, import a tour, packing list, picture, sound …) there is «🎒 From the backpack» – or it asks «From this device / From the backpack». Next to downloads (save settings, tours, servo data, recordings, reports, case files …) there is «🎒 Into the backpack»: MoveEye puts the file there itself. Settings, diagnosis, night test run and backups contain private data and go only into «My files».</li>
fr|<li><b>🎒 Pour l’import et l’export</b> : là où MoveEye lit un fichier (charger les réglages, importer un parcours, liste de bagages, image, son …), il y a «🎒 Depuis le sac à dos» – ou MoveEye demande «Depuis cet appareil / Depuis le sac à dos». À côté des téléchargements (sauvegarder les réglages, parcours, données servo, enregistrements, rapports, fichiers du boîtier …), il y a «🎒 Dans le sac à dos» : MoveEye y dépose le fichier lui-même. Réglages, diagnostic, test de nuit et sauvegardes contiennent des données privées et vont seulement dans «Mes fichiers».</li>
it|<li><b>🎒 Per importare ed esportare</b>: dove MoveEye legge un file (caricare le impostazioni, importare un percorso, lista bagagli, immagine, audio …) c’è «🎒 Dallo zaino» – oppure chiede «Da questo dispositivo / Dallo zaino». Accanto ai download (salvare le impostazioni, percorsi, dati servo, registrazioni, rapporti, file della custodia …) c’è «🎒 Nello zaino»: MoveEye vi deposita il file da solo. Impostazioni, diagnosi, test notturno e backup contengono dati privati e vanno solo in «I miei file».</li>
rm|<li><b>🎒 Per importar ed exportar</b>: nua che MoveEye legia ina datoteca (chargiar las configuraziuns, importar ina tura, glista da bagascha, maletg, tun …) stat «🎒 Ord il satgados» – u MoveEye dumonda «Da quest apparat / Ord il satgados». Sper ils downloads (memorisar las configuraziuns, turas, datas dal servo, registraziuns, rapports, datotecas da la chascha …) stat «🎒 En il satgados»: MoveEye metta sez la datoteca là. Configuraziuns, diagnosa, test da notg e copias da segirezza cuntegnan datas privatas e van mo en «Mias datotecas».</li>
"""
_HELP_RK = dict(x.split("|", 1) for x in RK_HELP_HTML.strip().split("\n") if "|" in x)


def _help_rk(doc, lang):
    i = doc.find('<section id="tausch"')
    j = doc.find("</ul></section>", i)
    return doc if i < 0 or j < 0 or "<li><b>🎒 " in doc[i:j] or lang not in _HELP_RK else doc[:j] + _HELP_RK[lang] + doc[j:]


try:                                                           # (without the data zip the pages are short stand-ins - nothing to do)
    _hp_en_rk = HELP_PAGE.find('<div lang="en">')
    if _hp_en_rk > 0:
        HELP_PAGE = _help_rk(HELP_PAGE[:_hp_en_rk], "de") + _help_rk(HELP_PAGE[_hp_en_rk:], "en")
    for _L in ("fr", "it", "rm"):
        if HELP_X.get(_L):
            HELP_X[_L] = _help_rk(HELP_X[_L], _L)
except Exception as _e:
    print(f"639zzzzr help: {_e}")


# ---- self-test (only for --self-test) ----------------------------------------------------------------------------------------------
def rucksack_io_selftest():
    F = rk_export_find
    for u, mode in (("/api/settings/export", "private"), ("/tools/diag.zip", "private"), ("/api/nacht/export/20261115_2200", "private"),
                    ("/api/factory/backup/x_1.json", "private"), ("/api/sim/sicherung/a.json", "private"), ("/api/servo/export?fmt=csv", "all"),
                    ("/touren/x/alle.zip", "all"), ("/touren/x/abc123.gpx?lang=de", "all"), ("/rec/file/2026-11-15%20a.mp4?dl=1", "mine"),
                    ("/build/datei/v5-2/Deckel.stl", "all"), ("/diary/img/a_1.jpg", "mine"), ("/rec/zip?names=a.mp4,b.jpg", "mine")):
        h = F(u)
        assert h is not None and h[2] == mode, "639zzzzr: " + u
    for u in ("https://evil.example/api/settings/export", "//evil.example/api/settings/export", "/api/settings/export?x=1",
              "/tausch/dl/0123456789abcdef", "/api/tausch?area=all", "/build/datei/../../etc/passwd", "/build/datei/%2e%2e/x",
              "/api/settings/export#x", "/api/settings", "/api/settings/exportX", "/rec/file/a.mp4?dl=1&x=2", "/g/abc/tausch", "",
              "/api/settings/export\\", "/touren/x/a.exe", "javascript:alert(1)", "/rec/file/a%0d.mp4"):
        assert F(u) is None, "639zzzzr refused: " + repr(u)
    priv = {p for p, q, m, k in RK_EXPORTS if m == "private"}
    for p in (r"/api/settings/export", r"/tools/diag\.zip", r"/api/nacht/export/[A-Za-z0-9_.-]{1,80}"):
        assert p in priv, "639zzzzr: private " + p
    for p, q, m, k in RK_EXPORTS:
        assert p.startswith("/") and ".*" not in p and "tausch/dl" not in p and m in ("private", "mine", "all") and isinstance(q, tuple), p
        re.compile(p)
    assert rk_disp_name("attachment; filename*=UTF-8''Gipfel%20Ost.gpx", "/x") == "Gipfel Ost.gpx"
    assert rk_disp_name('attachment; filename="moveeye_einstellungen.json"', "/x") == "moveeye_einstellungen.json"
    assert rk_disp_name("", "/touren/x/alle.zip") == "alle.zip"
    for k, v in _RK_TX.items():
        assert len(v) == 4 and all(v), "639zzzzr: text " + k
    for L in ("de", "en", "fr", "it", "rm"):
        assert "🎒" in _HELP_RK.get(L, ""), "639zzzzr: manual " + L
    for k in ("/*RKTX*/{}", "DataTransfer", "HTMLInputElement.prototype.click", "/api/tausch/io", '"live"', "innerHTML"):
        assert (k in RK_IO_JS) == (k != "innerHTML"), "639zzzzr script: " + k
    p = render_page("<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>", "settings")
    assert p.count("/rk/io.js?v=") == 1, "639zzzzr: script missing / twice"
    assert "/rk/io.js" not in render_page("<html><head></head><body><main></main></body></html>", "guest"), "639zzzzr: on a guest page"
    assert "/api/tausch/io" in PERM_POST["files_up"] and "/rk/io.js" in VIEW_GET_PAGES


SELFTEST_EXTRA.append(("Backpack for import / export: export list, private, script (639zzzzr)", rucksack_io_selftest))
