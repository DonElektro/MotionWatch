#@ MoveEye – Teil 639zzzze: «🖼 Produktseite: Bilder» (Mehr → Homepage, neben dem Upload-Schlüssel; nur Administrator) – die Bilder der Gäste-Seite /info/ (Live-Bild im Handy, «Sieh selbst» Tag / Nacht, Zeitfenster damals / jetzt) durch eigene Fotos ersetzen: zuschneiden auf 16:9, WebP, ohne EXIF / GPS, Markierung mit Text, «Zurück zum Beispiel». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (11/2026): auf der Produktseite stehen ruhige Beispielbilder (Teil 620, Bildplätze data-pb="…");
# der Besitzer will später eigene Fotos nehmen. Hier:
#   * PB_SLOTS: die Bildplätze (4.22.x: neun – dazu die Karten von «Ein Blick in die App»: Kamerabild im Live-Bild-Handy,
#     ganzer Bildschirm Live, Tagebuch, Nachts am Zelt). 16:9, ausser PB_SIZE (Handy hochkant, Film-Karte quer); gespeichert als DATA_DIR/produktseite/<platz>.webp (nie im Repository),
#     dazu produktseite/bilder.json {platz: {"v": Zeit, "box": [x, y, b, h] in %, "label": Text}}.
#   * pbild_make(): Hochladen (JPEG, PNG, WebP; HEIC nur, wenn «pillow_heif» da ist) → Drehung aus EXIF anwenden, Mitte
#     zuschneiden auf 16:9 (Regler «Ausschnitt» 0–100 = Lage auf der freien Achse, wie object-position im Browser),
#     höchstens 1280 × 720, WebP mit sinkender Qualität bis PB_BYTES. Das neue Bild wird aus den Bildpunkten gebaut:
#     EXIF, GPS, XMP und ICC gehen nie mit (Privatsphäre).
#   * info_html() (620) bekommt die eigenen Bilder: src → /info/bild/<platz>.webp?v=…, Text des Bildes neutral
#     («Kamerabild», alt_cam), und window.PB mit Markierung / Text im <head> (die Seite liest es vor den Texten).
#   * /produktbilder (Seite), /api/produktbilder (Zustand, Hochladen mit dem Bild als Körper, Markierung, zurück),
#     /api/produktbilder/bild/<platz> (Vorschau, auch die Beispiele), /info/bild/<platz>.webp (öffentlich wie /info/,
#     nur wenn die Produktseite eingeschaltet ist). Ändern nur Rolle admin ohne App-Schlüssel; andere: 403.
#   * Einstieg: Knopf in der Karte «Homepage» (639zzzh) neben dem Upload-Schlüssel (Elektro 11/2026; vorher Mehr → Werkzeuge).
# Tests: werkzeuge/produktbilder_test.py (hochladen, EXIF weg, zurück, 403, /info/ zeigt das neue Bild, Seite 390 px).
# ----------------------------------------------------------------------------

# Programmtext in der ZIP (Hauptdatei kleiner, 22.11.2026; Muster 639zzzzk / 639zzzzm): ab Zeile 41 steht der Teil in EINEM
# Literal PB_PY - bauen.py legt es in die Zusatz-ZIP (über ZD_SHA256 mit signiert), zd_exec führt es hier aus (Zeilennummern wie
# in dieser Datei). Keine Start-, Schutz-, Alarm-, Update- oder Reparatur-Funktion: ohne ZIP fehlt der Teil einfach. Was ohne
# ZIP gelten muss (Einstellungen, Sperrlisten), steht oben ausserhalb des Literals.


if "zd_exec" not in globals():                              # only without 639zzzzk (Blinki defines it first)
    # wraps: zd_exec
    def zd_exec(src, name):
        """run the program text of a part that bauen.py moved into the data zip (same as 639zzzzk): src comes from _zd (Teil
        012), i.e. only from a zip whose SHA-256 matched ZD_SHA256 of this signed program. Real file name for compile +
        linecache (tracebacks show the lines of the part). Only for functions outside start, protection, alarm, update, repair."""
        if not src:
            return False
        import linecache
        linecache.cache[name] = (len(src), None, src.splitlines(True), name)
        exec(compile(src, name, "exec"), globals())
        return True


PB_PY = r'''
import io
import shutil

PB_SLOTS = ("live", "tag", "nacht", "damals", "jetzt", "app_kamera", "app_live", "app_tagebuch", "zelt")
PB_SIZE = {"app_live": ((520, 1125), (360, 780)), "app_tagebuch": ((520, 1125), (360, 780)), "zelt": ((1280, 592), (640, 296))}   # (size, minimum)
PB_BOXED = ("tag", "nacht", "jetzt")                           # these places can have a mark with a text
PB_W, PB_H, PB_BYTES, PB_UPLOAD_MAX, PB_MIN = 1280, 720, 220000, 25 << 20, (640, 360)
PB_DEFAULT_BOX = {"jetzt": [58, 75.5, 16, 17]}
PB_APP = ("app_live", "app_tagebuch")                          # screenshots of the app: no «Kamerabild» text                 # the mark of the example (stones), as in the page
_PB_LOCK = threading.Lock()
_PB_DEF = {}


def pbild_dir():
    return os.path.join(DATA_DIR, "produktseite")


def pbild_meta():
    try:
        with open(os.path.join(pbild_dir(), "bilder.json"), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in d.items() if k in PB_SLOTS and isinstance(v, dict) and os.path.isfile(os.path.join(pbild_dir(), k + ".webp"))}


def _pb_write(name, data):
    os.makedirs(pbild_dir(), exist_ok=True)
    p = os.path.join(pbild_dir(), name); t = p + ".tmp"
    with open(t, "wb") as f:
        f.write(data)
    os.replace(t, p)


def _pb_save_meta(m):
    _pb_write("bilder.json", json.dumps(m, ensure_ascii=False).encode("utf-8"))


def pbild_box_clean(box, label):
    """[x, y, w, h] in % (inside the picture, at least 2 %) and a short text without markup - or (None, "")"""
    try:
        x, y, w, h = [float(v) for v in (box or [])][:4]
    except (TypeError, ValueError):
        return None, ""
    x, y = min(max(x, 0.0), 98.0), min(max(y, 0.0), 98.0)
    w, h = min(max(w, 2.0), 100.0 - x), min(max(h, 2.0), 100.0 - y)
    lab = re.sub(r"[\x00-\x1f<>]", "", str(label or "")).strip()[:40]
    return [round(x, 1), round(y, 1), round(w, 1), round(h, 1)], lab


def pbild_make(raw, pos=50, slot=""):
    """the uploaded picture -> WebP bytes in the shape of its place (16:9 or PB_SIZE) without any metadata; raises ValueError(English text)"""
    (PW_, PH_), mn = PB_SIZE.get(slot, ((PB_W, PB_H), PB_MIN))
    from PIL import Image, ImageOps
    if len(raw) > PB_UPLOAD_MAX:
        raise ValueError("The picture is too big (at most 25 MB).")
    if raw[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftyphevc", b"ftypmsf1"):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:
            raise ValueError("HEIC cannot be read on this MoveEye. Please choose a JPEG or PNG.")
    try:
        im = Image.open(io.BytesIO(raw))
        if im.size[0] * im.size[1] > 80_000_000:
            raise ValueError("The picture is too big (at most 25 MB).")
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
    except ValueError:
        raise
    except Exception:
        raise ValueError("This picture cannot be read. Please choose a JPEG or PNG.")
    w, h = im.size
    if w < mn[0] or h < mn[1]:
        if mn == PB_MIN:
            raise ValueError("The picture is too small (at least 640 × 360).")
        raise ValueError("The picture is too small (at least %d × %d)." % mn)
    p = min(max(float(pos), 0.0), 100.0) / 100.0
    if w * PH_ > h * PW_:                                      # wider than the place: the free axis is x
        cw = h * PW_ // PH_; box = (int((w - cw) * p), 0, int((w - cw) * p) + cw, h)
    else:
        ch = w * PH_ // PW_; box = (0, int((h - ch) * p), w, int((h - ch) * p) + ch)
    im = im.crop(box)
    if im.size[0] > PW_:
        im = im.resize((PW_, PH_), Image.LANCZOS)
    clean = Image.new("RGB", im.size)                          # only the picture points: no EXIF / GPS / XMP / ICC
    clean.paste(im)
    out = b""
    for q in (80, 72, 64, 56, 48, 40):
        b = io.BytesIO(); clean.save(b, "WEBP", quality=q, method=4); out = b.getvalue()
        if len(out) <= PB_BYTES:
            break
    return out


def pbild_set(slot, raw, pos=50, box=None, label=""):
    if slot not in PB_SLOTS:
        raise ValueError("Unknown picture.")
    data = pbild_make(raw, pos, slot)
    with _PB_LOCK:
        m = pbild_meta()
        b, lab = pbild_box_clean(box, label) if slot in PB_BOXED else (None, "")
        _pb_write(slot + ".webp", data)
        m[slot] = {"v": int(time.time() * 1000), "box": b, "label": lab if b else ""}
        _pb_save_meta(m)
    log_event("sys", f"Product page: own picture «{slot}» ({len(data) // 1024} KB)")
    return m[slot]


def pbild_box(slot, box, label):
    with _PB_LOCK:
        m = pbild_meta()
        if slot not in m or slot not in PB_BOXED:
            raise ValueError("Unknown picture.")
        b, lab = pbild_box_clean(box, label) if box else (None, "")
        m[slot].update(box=b, label=lab if b else "")
        _pb_save_meta(m)
    return m[slot]


def pbild_reset(slot):
    if slot not in PB_SLOTS:
        raise ValueError("Unknown picture.")
    with _PB_LOCK:
        m = pbild_meta(); m.pop(slot, None); _pb_save_meta(m)
        try:
            os.remove(os.path.join(pbild_dir(), slot + ".webp"))
        except OSError:
            pass
    log_event("sys", f"Product page: picture «{slot}» back to the example")


def pbild_default(slot):
    """the example picture of a place (from the page in 620): bytes, mime"""
    key = id(INFO_HTML_GZ)
    if _PB_DEF.get("_k") != key:
        import gzip as _gz, base64 as _b64
        h = _gz.decompress(_b64.b64decode(INFO_HTML_GZ)).decode("utf-8")
        tags = {m.group(1): m.group(0) for m in re.finditer(r'<(?:img|video)\b[^>]*\bdata-pb="(\w+)"[^>]*>', h)}
        ids = {m.group(2): m.group(1) for m in re.finditer(r'<img\b[^>]*\bsrc="(data:[^"]+)"[^>]*\bid="([\w-]+)"', h)}
        _PB_DEF.clear(); _PB_DEF["_k"] = key
        for k, t in tags.items():
            s = re.search(r'\b(?:src|poster)="(data:[^"]+)"', t); same = re.search(r'\bdata-same="([\w-]+)"', t)
            u = s.group(1) if s else ids.get(same.group(1), "") if same else ""
            m = re.match(r"data:(image/[a-z]+);base64,(.*)", u)
            if m:
                _PB_DEF[k] = (_b64.b64decode(m.group(2)), m.group(1))
    return _PB_DEF.get(slot)


def pbild_apply(h, base="/info/bild/"):
    """the product page with the own pictures of the admin (src, neutral text, window.PB); base: where the pictures are
    (/info/bild/ on MoveEye, «bild/» next to Info/index.html on the web space, 639zzzh)"""
    m = pbild_meta()
    if not m:
        return h
    for k, v in m.items():
        url = "%s%s.webp?v=%s" % (base, k, int(v.get("v") or 0))

        def tag_(mt, url=url, k=k):
            t = re.sub(r'\s(?:src|data-same|data-alt|alt)="[^"]*"', "", mt.group(0))
            return t.replace("<img", '<img src="%s" %s' % (url, 'alt=""' if k in PB_APP else 'alt="Kamerabild" data-alt="alt_cam"'), 1)
        h = re.sub(r'<img\b[^>]*\bdata-pb="%s"[^>]*>' % k, tag_, h, count=1)
        h = re.sub(r'<video\b[^>]*\bdata-pb="%s"[^>]*>.*?</video>' % k,          # 4.22.x: a film card -> the own picture
                   lambda mt, url=url, k=k: '<img data-pb="%s" src="%s" alt="Kamerabild" data-alt="alt_cam" loading="lazy">' % (k, url), h, count=1, flags=re.S)
    pb = {k: {"box": v.get("box"), "label": v.get("label") or ""} for k, v in m.items()}
    js = "<script>window.PB=" + json.dumps(pb, ensure_ascii=False).replace("</", "<\\/") + ";</script>"
    return h.replace("</head>", js + "</head>", 1)


_info_html_639zzzze = info_html


# wraps: info_html
def info_html():                                             # + 639zzzze: the own pictures of the admin
    return pbild_apply(_info_html_639zzzze())


def pbild_state(lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    m = pbild_meta()
    names = {"live": "Live picture (phone)", "tag": "See for yourself: day", "nacht": "See for yourself: night",
             "damals": "Window to the past: then", "jetzt": "Window to the past: now", "app_kamera": "App: camera picture in the phone",
             "app_live": "App: whole live screen", "app_tagebuch": "App: diary", "zelt": "At the tent at night"}
    notes = {"nacht": "Night: ideally an infrared picture of MoveEye.", "damals": "Then and now: twice the same view, a little changed.",
             "jetzt": "Then and now: twice the same view, a little changed.",
             "app_kamera": "Only the camera picture inside the phone - the app around it stays.",
             "app_live": "A screenshot of the MoveEye app on the phone (portrait). Replaces the whole phone screen.",
             "app_tagebuch": "A screenshot of the MoveEye app on the phone (portrait).", "zelt": "Your own picture replaces the short film."}
    out = []
    for k in PB_SLOTS:
        v = m.get(k) or {}
        out.append({"id": k, "name": tr(names[k], L), "note": tr(notes[k], L) if k in notes else "", "custom": bool(v), "v": v.get("v") or 0,
                    "box": v.get("box") if v else PB_DEFAULT_BOX.get(k), "label": v.get("label") or "", "boxable": k in PB_BOXED,
                    "ratio": "%d/%d" % PB_SIZE.get(k, ((PB_W, PB_H),))[0]})
    return {"ok": True, "slots": out, "info_on": bool(CFG.get("info_page"))}


def pbild_admin(g_):
    return getattr(g_, "role", "admin") == "admin" and not getattr(g_, "appkey", None)


_smalltv_routes_639zzzze = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzze: page, API and the pictures of /info/
    _smalltv_routes_639zzzze(app, reply, body)
    from flask import Response, request, g

    def no_(lang):
        return reply({"ok": False, "error": tr("Only the administrator can change the pictures of the product page.", lang)}, 403)

    @app.route("/produktbilder")
    def pbild_page_():
        if not pbild_admin(g):
            return no_(norm_lang(request.args.get("lang")))
        return Response(render_page(PB_PAGE, "tools"), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/produktbilder", methods=["GET", "POST"])
    def api_pb():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if not pbild_admin(g):
            if (request.content_length or 0) < 1 << 20:
                request.get_data()
            return no_(lang)
        if request.method == "GET":
            return reply(pbild_state(lang))
        a = request.args.get("action") or ""
        try:
            if a == "set":
                if (request.content_length or 0) > PB_UPLOAD_MAX:
                    raise ValueError("The picture is too big (at most 25 MB).")
                raw = request.get_data(cache=False)
                box = [v for v in (request.args.get("box") or "").split(",") if v.strip()]
                pbild_set(request.args.get("slot"), raw, request.args.get("pos") or 50, box if len(box) == 4 else None, request.args.get("label") or "")
            else:
                d = body(); slot = str(d.get("slot") or "")
                if a == "reset" or d.get("action") == "reset":
                    pbild_reset(slot)
                elif a == "box" or d.get("action") == "box":
                    pbild_box(slot, d.get("box"), d.get("label"))
                else:
                    raise ValueError("Unknown picture.")
        except ValueError as e:
            return reply(dict(pbild_state(lang), ok=False, error=tr(str(e), lang)), 400)
        return reply(pbild_state(lang))

    @app.route("/api/produktbilder/bild/<slot>")
    def api_pb_img(slot):
        if not pbild_admin(g):
            return no_(norm_lang(request.args.get("lang")))
        p = os.path.join(pbild_dir(), slot + ".webp")
        if slot in PB_SLOTS and slot in pbild_meta():
            with open(p, "rb") as f:
                return Response(f.read(), mimetype="image/webp", headers={"Cache-Control": "no-store"})
        d = pbild_default(slot) if slot in PB_SLOTS else None
        return Response(d[0], mimetype=d[1], headers={"Cache-Control": "no-store"}) if d else Response("not found", 404)

    @app.route("/info/bild/<name>")
    def info_pb_img(name):
        slot = name[:-5] if name.endswith(".webp") else ""
        if not CFG.get("info_page") or slot not in PB_SLOTS or slot not in pbild_meta():
            return Response("not found", 404)
        with open(os.path.join(pbild_dir(), slot + ".webp"), "rb") as f:
            return Response(f.read(), mimetype="image/webp", headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"})


# ---- the entry: in the card «Homepage» (639zzzh, only the admin) next to the upload key (Elektro, 11/2026) ------------------------
_PB_HP_ROW = '<div class="hp-row"><button type="button" id="hp-key-b"></button><button type="button" class="sec" id="hp-key-d"></button></div>'
_PB_HP_LINK = ('<a class="btn sec" id="hp-pbild" href="/produktbilder" style="display:inline-flex;align-items:center;justify-content:center;gap:6px;'
               'text-decoration:none;box-sizing:border-box">🖼 <span data-i18n="Product page: pictures">Product page: pictures</span></a>')
if 'id="hp-pbild"' not in HP_PAGE and HP_PAGE.count(_PB_HP_ROW) == 1:
    HP_PAGE = HP_PAGE.replace(_PB_HP_ROW, _PB_HP_ROW[:-len("</div>")] + _PB_HP_LINK + "</div>", 1)

# ---- texts (English key: Deutsch, français, italiano, rumantsch) -----------------------------------------------------------------
_HX_PB = {
    "Product page: pictures": ("Produktseite: Bilder", "Page produit : images", "Pagina prodotto: immagini", "Pagina da product: maletgs"),
    "These pictures are shown to guests on the product page (/info/). Your own photos replace the examples.": (
        "Diese Bilder sehen Gäste auf der Produktseite (/info/). Eigene Fotos ersetzen die Beispiele.",
        "Ces images apparaissent aux invités sur la page produit (/info/). Tes propres photos remplacent les exemples.",
        "Queste immagini le vedono gli ospiti sulla pagina prodotto (/info/). Le tue foto sostituiscono gli esempi.",
        "Quests maletgs vesan ils giasts sin la pagina da product (/info/). Atgnas fotografias remplazzan ils exempels."),
    "No people, number plates or house numbers.": ("Keine Personen, Kennzeichen oder Hausnummern.",
                                                   "Pas de personnes, de plaques d'immatriculation ni de numéros de maison.",
                                                   "Niente persone, targhe o numeri civici.", "Naginas persunas, numers da vehichels u numers da chasa."),
    "Location data (EXIF, GPS) is removed. The picture is cut to 16:9 and stored on MoveEye.": (
        "Standortdaten (EXIF, GPS) werden entfernt. Das Bild wird auf 16:9 zugeschnitten und auf MoveEye gespeichert.",
        "Les données de position (EXIF, GPS) sont supprimées. L'image est recadrée en 16:9 et enregistrée sur MoveEye.",
        "I dati di posizione (EXIF, GPS) vengono rimossi. L'immagine viene ritagliata in 16:9 e salvata su MoveEye.",
        "Las datas da lieu (EXIF, GPS) vegnan allontanadas. Il maletg vegn taglià sin 16:9 e memorisà sin MoveEye."),
    "The product page is switched off - guests do not see it at the moment.": (
        "Die Produktseite ist ausgeschaltet – Gäste sehen sie im Moment nicht.", "La page produit est désactivée – les invités ne la voient pas pour le moment.",
        "La pagina prodotto è disattivata – al momento gli ospiti non la vedono.", "La pagina da product è deactivada – ils giasts na la vesan per il mument betg."),
    "Live picture (phone)": ("Live-Bild (Handy)", "Image en direct (téléphone)", "Immagine dal vivo (telefono)", "Maletg live (telefonin)"),
    "See for yourself: day": ("Sieh selbst: Tag", "Vois toi-même : jour", "Guarda tu stesso: giorno", "Guarda sez: di"),
    "See for yourself: night": ("Sieh selbst: Nacht", "Vois toi-même : nuit", "Guarda tu stesso: notte", "Guarda sez: notg"),
    "Window to the past: then": ("Zeitfenster: damals", "Fenêtre sur le passé : avant", "Finestra sul passato: prima", "Fanestra en il passà: avant"),
    "Window to the past: now": ("Zeitfenster: jetzt", "Fenêtre sur le passé : maintenant", "Finestra sul passato: adesso", "Fanestra en il passà: ussa"),
    "Night: ideally an infrared picture of MoveEye.": ("Nacht: am besten ein Infrarot-Bild von MoveEye.", "Nuit : idéalement une image infrarouge de MoveEye.",
                                                       "Notte: idealmente un'immagine all'infrarosso di MoveEye.", "Notg: il meglier in maletg infracotschen da MoveEye."),
    "Then and now: twice the same view, a little changed.": ("Damals und jetzt: zweimal derselbe Blick, etwas verändert.",
                                                             "Avant et maintenant : deux fois la même vue, un peu changée.",
                                                             "Prima e adesso: due volte la stessa vista, un po' cambiata.",
                                                             "Avant ed ussa: duas giadas la medema vista, in pau midada."),
    "Location data (EXIF, GPS) is removed. The picture is cut to the shape of its place and stored on MoveEye.": (
        "Standortdaten (EXIF, GPS) werden entfernt. Das Bild wird passend zu seinem Platz zugeschnitten und auf MoveEye gespeichert.",
        "Les données de position (EXIF, GPS) sont supprimées. L'image est recadrée selon sa place et enregistrée sur MoveEye.",
        "I dati di posizione (EXIF, GPS) vengono rimossi. L'immagine viene ritagliata secondo il suo posto e salvata su MoveEye.",
        "Las datas da lieu (EXIF, GPS) vegnan allontanadas. Il maletg vegn taglià tenor ses plaz e memorisà sin MoveEye."),
    "App: camera picture in the phone": ("App: Kamerabild im Handy", "App : image de la caméra dans le téléphone",
                                         "App: immagine della telecamera nel telefono", "App: maletg da la camera en il telefonin"),
    "App: whole live screen": ("App: ganzer Bildschirm Live", "App : écran direct entier", "App: schermo live intero", "App: entir visur live"),
    "App: diary": ("App: Tagebuch", "App : journal", "App: diario", "App: diari"),
    "At the tent at night": ("Nachts am Zelt", "La nuit près de la tente", "Di notte vicino alla tenda", "La notg tar la tenda"),
    "Only the camera picture inside the phone - the app around it stays.": (
        "Nur das Kamerabild im Handy – die App rundherum bleibt.", "Seulement l'image de la caméra dans le téléphone – l'app autour reste.",
        "Solo l'immagine della telecamera nel telefono – l'app intorno resta.", "Mo il maletg da la camera en il telefonin – l'app enturn resta."),
    "A screenshot of the MoveEye app on the phone (portrait). Replaces the whole phone screen.": (
        "Ein Bildschirmfoto der MoveEye-App auf dem Handy (hochkant). Ersetzt den ganzen Handy-Bildschirm.",
        "Une capture d'écran de l'app MoveEye sur le téléphone (vertical). Remplace tout l'écran du téléphone.",
        "Uno screenshot dell'app MoveEye sul telefono (verticale). Sostituisce l'intero schermo del telefono.",
        "In maletg dal visur da l'app MoveEye sin il telefonin (en autezza). Remplazza l'entir visur dal telefonin."),
    "A screenshot of the MoveEye app on the phone (portrait).": (
        "Ein Bildschirmfoto der MoveEye-App auf dem Handy (hochkant).", "Une capture d'écran de l'app MoveEye sur le téléphone (vertical).",
        "Uno screenshot dell'app MoveEye sul telefono (verticale).", "In maletg dal visur da l'app MoveEye sin il telefonin (en autezza)."),
    "Your own picture replaces the short film.": ("Dein eigenes Bild ersetzt den kurzen Film.", "Ta propre image remplace le court film.",
                                                  "La tua immagine sostituisce il breve filmato.", "Tes atgen maletg remplazza il curt film."),
    "The picture is too small (at least 360 × 780).": ("Das Bild ist zu klein (mindestens 360 × 780).", "L'image est trop petite (au moins 360 × 780).",
                                              "L'immagine è troppo piccola (almeno 360 × 780).", "Il maletg è memia pitschen (almain 360 × 780)."),
    "The picture is too small (at least 640 × 296).": ("Das Bild ist zu klein (mindestens 640 × 296).", "L'image est trop petite (au moins 640 × 296).",
                                              "L'immagine è troppo piccola (almeno 640 × 296).", "Il maletg è memia pitschen (almain 640 × 296)."),
    "Example": ("Beispiel", "Exemple", "Esempio", "Exempel"),
    "Own picture": ("Eigenes Bild", "Image personnelle", "Immagine propria", "Atgen maletg"),
    "Replace": ("Ersetzen", "Remplacer", "Sostituisci", "Remplazzar"),
    "Back to the example": ("Zurück zum Beispiel", "Revenir à l'exemple", "Torna all'esempio", "Enavos a l'exempel"),
    "Save picture": ("Bild speichern", "Enregistrer l'image", "Salva immagine", "Memorisar il maletg"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "Section": ("Ausschnitt", "Cadrage", "Inquadratura", "Extract"),
    "Mark (optional): draw a box on the picture": ("Markierung (freiwillig): ein Rechteck aufs Bild ziehen", "Repère (facultatif) : trace un rectangle sur l'image",
                                                   "Segno (facoltativo): traccia un rettangolo sull'immagine", "Marcaziun (facultativ): tirar in rectangul sin il maletg"),
    "Text of the mark, e.g. «new: …»": ("Text der Markierung, z. B. «neu: …»", "Texte du repère, p. ex. «nouveau : …»", "Testo del segno, ad es. «nuovo: …»",
                                        "Text da la marcaziun, p.ex. «nov: …»"),
    "Remove the mark": ("Markierung löschen", "Supprimer le repère", "Rimuovi il segno", "Stizzar la marcaziun"),
    "Change the mark": ("Markierung ändern", "Modifier le repère", "Modifica il segno", "Midar la marcaziun"),
    "Saving …": ("Speichern …", "Enregistrement …", "Salvataggio …", "Memorisar …"),
    "Saved.": ("Gespeichert.", "Enregistré.", "Salvato.", "Memorisà."),
    "Only the administrator can change the pictures of the product page.": (
        "Nur der Administrator kann die Bilder der Produktseite ändern.", "Seul l'administrateur peut changer les images de la page produit.",
        "Solo l'amministratore può cambiare le immagini della pagina prodotto.", "Mo l'administratur po midar ils maletgs da la pagina da product."),
    "This picture cannot be read. Please choose a JPEG or PNG.": (
        "Dieses Bild kann nicht gelesen werden. Bitte ein JPEG oder PNG wählen.", "Cette image ne peut pas être lue. Choisis un JPEG ou un PNG.",
        "Questa immagine non può essere letta. Scegli un JPEG o un PNG.", "Quest maletg na po betg vegnir legì. Tscherna per plaschair in JPEG u PNG."),
    "HEIC cannot be read on this MoveEye. Please choose a JPEG or PNG.": (
        "HEIC kann dieses MoveEye nicht lesen. Bitte ein JPEG oder PNG wählen.", "Ce MoveEye ne peut pas lire le HEIC. Choisis un JPEG ou un PNG.",
        "Questo MoveEye non può leggere HEIC. Scegli un JPEG o un PNG.", "Quest MoveEye na po betg leger HEIC. Tscherna per plaschair in JPEG u PNG."),
    "The picture is too big (at most 25 MB).": ("Das Bild ist zu gross (höchstens 25 MB).", "L'image est trop grande (25 Mo au maximum).",
                                                "L'immagine è troppo grande (al massimo 25 MB).", "Il maletg è memia grond (maximalmain 25 MB)."),
    "The picture is too small (at least 640 × 360).": ("Das Bild ist zu klein (mindestens 640 × 360).", "L'image est trop petite (au moins 640 × 360).",
                                                       "L'immagine è troppo piccola (almeno 640 × 360).", "Il maletg è memia pitschen (almain 640 × 360)."),
    "Unknown picture.": ("Unbekanntes Bild.", "Image inconnue.", "Immagine sconosciuta.", "Maletg nunenconuschent."),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione a MoveEye.", "Nagina connexiun cun MoveEye."),
}
for _k, _v in _HX_PB.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_PB_DE = {_k: DE.get(_k, _v[0]) for _k, _v in _HX_PB.items()}

_render_page_639zzzze = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzzze: the German texts of the page
    out = _render_page_639zzzze(page, active)
    if 'id="hp-pbild"' in out:                              # the German name of the entry on /homepage
        out = out.replace("</body>", "<script>Object.assign(I18N.de, {\"Product page: pictures\": " + json.dumps(_PB_DE["Product page: pictures"], ensure_ascii=False)
                          + "});document.querySelectorAll('#hp-pbild [data-i18n]').forEach(e => e.textContent = t(e.dataset.i18n));</script></body>", 1)
    if "/*PBDE*/" in out:
        out = out.replace("/*PBDE*/", "Object.assign(I18N.de, " + json.dumps(_PB_DE, ensure_ascii=False).replace("</", "<\\/") + ");", 1)
    return out


PB_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Product page: pictures</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:760px;margin:0 auto;box-sizing:border-box}
.pb-back{display:inline-flex;align-items:center;min-height:40px;text-decoration:none;color:var(--acc);font-weight:600;margin:0 0 4px}
#pb-title{margin:0 0 10px;font-size:20px}
.pb-hint{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px 14px;margin:0 0 14px;display:grid;gap:6px;font-size:14px}
.pb-hint .warn{color:var(--yel);font-weight:700}.pb-hint .mut{color:var(--mut);font-size:13px}.pb-off{color:var(--yel);font-size:13px}
.pb-list{display:grid;gap:12px}
.pb-c{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px;display:grid;grid-template-columns:minmax(0,200px) minmax(0,1fr);gap:12px;align-items:start}
.pb-pv{position:relative;aspect-ratio:16/9;border-radius:10px;overflow:hidden;background:#000;border:1px solid var(--line)}
.pb-pv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;-webkit-user-drag:none;user-select:none}
.pb-mk{position:absolute;border:2px dashed #f0a540;border-radius:6px;pointer-events:none}.pb-mk:empty{display:block}
.pb-mk span{position:absolute;left:-2px;bottom:100%;margin-bottom:3px;white-space:nowrap;background:#f0a540;color:#1a1205;font:600 11px/1 system-ui,sans-serif;padding:3px 5px;border-radius:4px}
.pb-mk span:empty{display:none}
.pb-b{display:grid;gap:6px;min-width:0}.pb-b b{font-size:15px}.pb-b small{color:var(--mut);font-size:12px}
.pb-st{font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}.pb-st.own{color:var(--grn)}
.pb-a{display:flex;flex-wrap:wrap;gap:8px}.pb-a button,.pb-a label{min-height:40px;font:inherit;font-size:14px;display:inline-flex;align-items:center;cursor:pointer}
.pb-a label{padding:0 14px;border-radius:10px;background:var(--acc);color:#fff;font-weight:600}
.pb-a label input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.pb-ed{grid-column:1/-1;display:grid;gap:10px;border-top:1px solid var(--line);padding-top:12px}
.pb-ed .pb-pv{cursor:crosshair;touch-action:none}
.pb-sl{display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:center;font-size:13px;color:var(--mut)}.pb-sl input{width:100%;min-height:36px}
.pb-ed input[type=text]{font:inherit;font-size:16px;min-height:44px;width:100%;box-sizing:border-box;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:6px 10px}
.pb-msg{font-size:13px;min-height:1.2em}.pb-msg.err{color:var(--red)}.pb-msg.ok{color:var(--grn)}
@media(max-width:560px){.pb-c{grid-template-columns:minmax(0,1fr)}}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <a class="pb-back" href="/homepage" id="pb-back">‹ Homepage</a>
  <h2 id="pb-title">🖼 Product page: pictures</h2>
  <section class="pb-hint"><span id="pb-h1"></span><span class="warn" id="pb-h2"></span><span class="mut" id="pb-h3"></span><span class="pb-off" id="pb-off" hidden></span></section>
  <div class="pb-list" id="pb-list"></div>
</main>
<script>
/*COMMON*/
/*PBDE*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  document.title = "MoveEye – " + t("Product page: pictures");
  $i("pb-back").textContent = "‹ " + t("Homepage"); $i("pb-title").textContent = "🖼 " + t("Product page: pictures");
  $i("pb-h1").textContent = t("These pictures are shown to guests on the product page (/info/). Your own photos replace the examples.");
  $i("pb-h2").textContent = "⚠ " + t("No people, number plates or house numbers.");
  $i("pb-h3").textContent = t("Location data (EXIF, GPS) is removed. The picture is cut to the shape of its place and stored on MoveEye.");
  let J = null;
  const get = async () => { try { const r = await fetch("/api/produktbilder?lang=" + L()); return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  const post = async (q, data, json) => {
    try { const r = await fetch("/api/produktbilder?lang=" + L() + "&" + q, {method: "POST", body: data,
        headers: {"Content-Type": json ? "application/json" : "application/octet-stream"}}); return await r.json(); }
    catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  function shape(pv, s) {                                     // 4.22.x: the shape of the place (phone portrait, film card)
    if (!s.ratio || s.ratio === "1280/720") return;
    pv.style.aspectRatio = s.ratio; const [w, h] = s.ratio.split("/").map(Number);
    if (h > w) { pv.style.maxWidth = "140px"; pv.style.width = "100%"; }
  }
  function mark(pv, box, label) {
    pv.querySelectorAll(".pb-mk").forEach(x => x.remove()); if (!box) return;
    const m = E("div", "pb-mk"); m.style.left = box[0] + "%"; m.style.top = box[1] + "%"; m.style.width = box[2] + "%"; m.style.height = box[3] + "%";
    m.appendChild(E("span", "", label || "")); pv.appendChild(m);
  }
  function editor(card, s, file) {
    card.querySelectorAll(".pb-ed").forEach(x => x.remove());
    const ed = E("div", "pb-ed"), pv = E("div", "pb-pv"), im = E("img"), msg = E("div", "pb-msg");
    let url = file ? URL.createObjectURL(file) : "/api/produktbilder/bild/" + s.id + "?v=" + s.v, pos = 50, box = s.custom ? s.box : null;
    im.src = url; im.alt = ""; pv.appendChild(im); ed.appendChild(pv); shape(pv, s);
    if (file) {
      const sl = E("label", "pb-sl"), r = E("input"); r.type = "range"; r.min = 0; r.max = 100; r.value = 50;
      sl.appendChild(E("span", "", t("Section"))); sl.appendChild(r); ed.appendChild(sl);
      r.oninput = () => { pos = +r.value; im.style.objectPosition = pos + "% " + pos + "%"; };
    }
    let lab = null;
    if (s.boxable) {
      ed.appendChild(E("small", "", t("Mark (optional): draw a box on the picture")));
      lab = E("input"); lab.type = "text"; lab.maxLength = 40; lab.placeholder = t("Text of the mark, e.g. «new: …»"); lab.value = s.custom ? (s.label || "") : "";
      ed.appendChild(lab); lab.oninput = () => mark(pv, box, lab.value);
      let st = null;                                           // drag = a new box (in % of the picture)
      const at = ev => { const r = pv.getBoundingClientRect(); return [Math.min(100, Math.max(0, (ev.clientX - r.left) / r.width * 100)), Math.min(100, Math.max(0, (ev.clientY - r.top) / r.height * 100))]; };
      pv.onpointerdown = ev => { st = at(ev); try { pv.setPointerCapture(ev.pointerId); } catch (x) {} ev.preventDefault(); };
      pv.onpointermove = ev => { if (!st) return; const p = at(ev); box = [Math.min(st[0], p[0]), Math.min(st[1], p[1]), Math.abs(p[0] - st[0]), Math.abs(p[1] - st[1])]; mark(pv, box, lab.value); };
      pv.onpointerup = () => { st = null; if (box && (box[2] < 2 || box[3] < 2)) { box = null; mark(pv, null); } };
      mark(pv, box, lab.value);
    }
    const a = E("div", "pb-a"), ok = E("button", "", "✓ " + t("Save picture")), no = E("button", "sec", t("Cancel"));
    ok.type = no.type = "button"; a.appendChild(ok);
    if (s.boxable) { const rm = E("button", "sec", t("Remove the mark")); rm.type = "button"; rm.onclick = () => { box = null; mark(pv, null); }; a.appendChild(rm); }
    a.appendChild(no); ed.appendChild(a); ed.appendChild(msg); card.appendChild(ed);
    no.onclick = () => { ed.remove(); if (file) URL.revokeObjectURL(url); };
    ok.onclick = async () => {
      ok.disabled = true; msg.className = "pb-msg"; msg.textContent = t("Saving …");
      const b = box ? box.map(v => v.toFixed(1)).join(",") : "", l = lab ? lab.value.trim() : "";
      const j = file ? await post("action=set&slot=" + s.id + "&pos=" + pos + "&box=" + b + "&label=" + encodeURIComponent(l), file)
                     : await post("action=box", JSON.stringify({slot: s.id, box: box, label: l}), true);
      ok.disabled = false;
      if (j.ok) { msg.className = "pb-msg ok"; msg.textContent = t("Saved."); J = j; setTimeout(paint, 500); }
      else { msg.className = "pb-msg err"; msg.textContent = j.error || ""; }
    };
  }
  function paint() {
    const list = $i("pb-list"); list.textContent = "";
    if (!J || !J.ok) { list.appendChild(E("div", "pb-msg err", (J && J.error) || "")); return; }
    $i("pb-off").hidden = !!J.info_on; $i("pb-off").textContent = t("The product page is switched off - guests do not see it at the moment.");
    J.slots.forEach(s => {
      const c = E("section", "pb-c"), pv = E("div", "pb-pv"), im = E("img"), b = E("div", "pb-b");
      c.id = "pb-" + s.id; shape(pv, s); im.src = "/api/produktbilder/bild/" + s.id + "?v=" + s.v; im.alt = s.name; pv.appendChild(im); mark(pv, s.box, s.custom ? s.label : (s.box ? "" : ""));
      b.appendChild(E("b", "", s.name));
      const st = E("span", "pb-st" + (s.custom ? " own" : ""), s.custom ? "✓ " + t("Own picture") : t("Example")); b.appendChild(st);
      if (s.note) b.appendChild(E("small", "", s.note));
      const a = E("div", "pb-a"), up = E("label"), inp = E("input");
      inp.type = "file"; inp.accept = "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif";
      up.appendChild(document.createTextNode("⬆ " + t("Replace"))); up.appendChild(inp); a.appendChild(up);
      inp.onchange = () => { if (inp.files && inp.files[0]) editor(c, s, inp.files[0]); inp.value = ""; };
      if (s.custom && s.boxable) { const mb = E("button", "sec", t("Change the mark")); mb.type = "button"; mb.onclick = () => editor(c, s, null); a.appendChild(mb); }
      if (s.custom) { const rb = E("button", "sec", "↺ " + t("Back to the example")); rb.type = "button";
        rb.onclick = async () => { rb.disabled = true; const j = await post("action=reset", JSON.stringify({slot: s.id}), true); if (j.ok) { J = j; paint(); } else rb.disabled = false; }; a.appendChild(rb); }
      b.appendChild(a); c.appendChild(pv); c.appendChild(b); list.appendChild(c);
    });
  }
  J = await get(); paint();
})();
</script>
</body></html>"""


def produktbilder_selftest():
    from PIL import Image
    import tempfile as _tf
    global DATA_DIR
    old = DATA_DIR
    d = _tf.mkdtemp(prefix="mw_pb_")
    try:
        DATA_DIR = d
        b = io.BytesIO(); ex = Image.Exif(); ex[0x010F] = "TestCam"; ex[0x8825] = {2: (47.0, 3.0, 0.0), 1: "N"}
        Image.new("RGB", (1600, 1200), (40, 120, 60)).save(b, "JPEG", exif=ex.tobytes()); raw = b.getvalue()
        assert b"TestCam" in raw
        pbild_set("jetzt", raw, 30, [10, 20, 30, 40], "neu: <b>Bank</b>")
        p = os.path.join(pbild_dir(), "jetzt.webp"); data = open(p, "rb").read()
        im = Image.open(p)
        assert im.size == (1280, 720) and b"TestCam" not in data and b"EXIF" not in data and not im.getexif(), "16:9, without EXIF"
        assert pbild_meta()["jetzt"]["box"] == [10.0, 20.0, 30.0, 40.0] and pbild_meta()["jetzt"]["label"] == "neu: bBank/b", "box and clean text"
        h = pbild_apply('<html><head></head><body><img src="data:image/webp;base64,AA" alt="x" data-alt="zf_alt_now" data-pb="jetzt" data-same="img-day"></body></html>')
        assert '<img src="/info/bild/jetzt.webp?v=' in h and "data-same" not in h and 'data-alt="alt_cam"' in h and "window.PB=" in h, "page gets the own picture"
        pbild_box("jetzt", None, ""); assert pbild_meta()["jetzt"]["box"] is None
        pbild_reset("jetzt"); assert not pbild_meta() and not os.path.exists(p), "back to the example"
        for bad in (b"no picture", b"\x00\x00\x00\x18ftypheic" + b"\0" * 40):
            try:
                pbild_make(bad); raise AssertionError("bad picture accepted")
            except ValueError:
                pass
        for k in PB_SLOTS:
            assert pbild_default(k) and pbild_default(k)[0][:4] == b"RIFF", "example picture in the page: " + k
        b2 = io.BytesIO(); Image.new("RGB", (1170, 2532), (30, 40, 60)).save(b2, "PNG")      # 4.22.x: a phone screenshot (portrait)
        pbild_set("app_tagebuch", b2.getvalue()); pbild_set("zelt", raw)
        assert Image.open(os.path.join(pbild_dir(), "app_tagebuch.webp")).size == (520, 1125), "phone portrait 520 × 1125"
        assert Image.open(os.path.join(pbild_dir(), "zelt.webp")).size == (1280, 592), "film card 1280 × 592"
        h = pbild_apply('<html><head></head><body><img id="app-tagebuch" data-pb="app_tagebuch" src="data:image/webp;base64,AA" alt="">'
                        '<video id="clip" data-pb="zelt" poster="data:image/webp;base64,AA" data-src="x"></video></body></html>')
        assert re.search(r'<img src="/info/bild/app_tagebuch\.webp\?v=\d+" alt="" id="app-tagebuch"', h), "app screenshot: own picture, no camera text"
        assert "<video" not in h and '<img data-pb="zelt" src="/info/bild/zelt.webp?v=' in h, "film card -> own picture"
        pbild_reset("app_tagebuch"); pbild_reset("zelt")
        assert all(DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")) for k in _HX_PB), "texts in 5 languages"
        assert 'class="pb-back" href="/homepage"' in PB_PAGE and 'id="hp-pbild" href="/produktbilder"' in HP_PAGE and 'href="/produktbilder"' not in TOOLS_PAGE, "entry in the card Homepage"
    finally:
        DATA_DIR = old
        shutil.rmtree(d, ignore_errors=True)


SELFTEST_EXTRA.append(("Product page: own pictures (16:9, without EXIF, back to the example) (639zzzze)", produktbilder_selftest))
'''
zd_exec(PB_PY and "\n" * 39 + PB_PY, "639zzzze_produktbilder.py")   # line 1 of PB_PY = line 40: the line numbers are those of this file
