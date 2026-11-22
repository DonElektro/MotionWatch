#@ MoveEye – Teil 639zzzzf: «🏞 Startseite: Bilder» (Karte «Homepage», nur Administrator) – eigene Fotos für die öffentliche Startseite (index.html auf dem Webspace): Variante A «Bildgeschichte» oder B «Panorama + Bildleiste», Fokuspunkt, EXIF / GPS weg, Bilder nur auf dem Gerät, hochgeladen als Startbilder/… mit dem Schalter «Startseite». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026, freigegeben): die Startseite des Webspace (639zzzh, index.html) mit eigenen Fotos.
#   * SB_SLOTS: die Bildplätze. «titel» gilt für beide Varianten (grosses Titelbild mit «MoveEye», in A zugleich Kapitel 1
#     «Unterwegs»); A: grat (PC / quer), grat_hoch (Handy / hochkant, freiwillig), lager, abend, nacht; B: pano (Panorama zum
#     Umsehen) und leiste1 … leiste6 (kleine wischbare Bildleiste). Gespeichert als DATA_DIR/startseite/<platz>.webp (+ <platz>-k.webp
#     klein), dazu startseite/bilder.json {"slots": {platz: {v, w, h, kw, kh, fx, fy}}, "texts": {platz: {feld: Text}}}.
#     NIE im Repository, nie in einem Paket: die Fotos gehören dem Besitzer und liegen nur auf seinem MoveEye.
#   * sb_make(): Hochladen (JPEG, PNG, WebP; HEIC nur mit «pillow_heif») → Drehung aus EXIF anwenden, auf die Grösse des
#     Platzes verkleinern (SB_SPEC: Breite oder – Bildleiste – Höhe), WebP mit sinkender Qualität, wenn nötig kleiner, bis
#     zum Byte-Limit (Panorama höchstens 400 KB, andere 250–300 KB, Leiste 160 KB). Das neue Bild wird aus den Bildpunkten
#     gebaut: EXIF, GPS, XMP und ICC gehen nie mit. Kein Zuschnitt: der Fokuspunkt (fx / fy in %, «object-position») sagt,
#     welcher Teil auf dem Handy sichtbar bleibt (z. B. der Rucksack unten rechts).
#   * Texte: jede Zeile pro Platz änderbar (Kapitelname, Satz auf dem Bild, Titelzeile, Bildbeschreibung). Leer = Standard in
#     5 Sprachen (SB_TX, nach der Sprache des Browsers); ein eigener Text gilt für alle Sprachen.
#   * Variante: hp_start_variant «A» / «B» (ab Werk B, leichter), nur der Admin; Umschalter auf /startbilder und in der Karte
#     «Homepage». Die zwei Knöpfe (📡 Funkgerät, 🎮 Simulator) stehen in beiden Varianten direkt unter dem Titelbild.
#   * Webspace (639zzzh): hp_fixed_items() bekommt mit «Startseite» und mindestens einem eigenen Bild der gewählten Variante
#     die Seite aus sb_page_html() und die Bilder als Startbilder/<platz>-<sha10>.webp (Name ändert mit dem Inhalt: kein altes
#     Bild aus dem Zwischenspeicher; das alte wird als eigene Datei gelöscht). Ohne eigene Bilder bleibt die schlichte Seite
#     hp_index_html(). Fehlt nur das Titelbild, zeigt die Seite einen gezeichneten Platzhalter (kein Foto). hp_part / _hp_ours
#     kennen Startbilder/ (Teil «start»: aus = nie hochgeladen, nie gelöscht), die Prüfung erwartet image/webp.
#   * /startbilder (Seite), /startbilder/vorschau?v=A|B (die Seite mit den Bildern von MoveEye), /api/startbilder (Zustand,
#     Hochladen mit dem Bild als Körper, Fokus, Texte, Entfernen, Variante), /api/startbilder/bild/<platz>. Nur Rolle admin
#     ohne App-Schlüssel; andere: 403.
# Tests: werkzeuge/startbilder_test.py (hochladen, EXIF weg, Grössen, 403, Webspace A / B / ohne Bilder, Seite 390 px).
# ----------------------------------------------------------------------------
SB_LEISTE = ("leiste1", "leiste2", "leiste3", "leiste4", "leiste5", "leiste6")
SB_SLOTS = ("titel", "grat", "grat_hoch", "lager", "abend", "nacht", "pano") + SB_LEISTE
# place: (big, small, bytes of the big one, axis of the limit "w" / "h", at least px on that axis)
SB_SPEC = {"titel": (1600, 900, 250000, "w", 600), "grat": (2400, 1200, 400000, "w", 900), "grat_hoch": (1050, 675, 300000, "w", 500),
           "lager": (1600, 900, 250000, "w", 600), "abend": (1600, 900, 250000, "w", 600), "nacht": (1600, 900, 250000, "w", 600),
           "pano": (2600, 1200, 400000, "w", 1200)}
SB_SPEC.update({k: (360, 0, 160000, "h", 300) for k in SB_LEISTE})
SB_VARIANTS = {"A": ("titel", "grat", "grat_hoch", "lager", "abend", "nacht"), "B": ("titel", "pano") + SB_LEISTE}
SB_FIELDS = {"titel": ("line", "kick", "say"), "grat": ("kick", "say"), "lager": ("kick", "say"), "abend": ("kick", "say"),
             "nacht": ("kick", "say"), "pano": ("kick",)}
SB_CHAPTERS = ("grat", "lager", "abend", "nacht")             # A: the chapters 2 … 5 after the title picture
SB_UPLOAD_MAX = 25 << 20
SB_DIR = "Startbilder"
_SB_LOCK = threading.Lock()
_SB_CFG = {"hp_start_variant": "B"}
for _k, _v in _SB_CFG.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update(_SB_CFG)
APPKEY_DENY_KEYS.update(_SB_CFG)
LOCK_DENY_KEYS.update(_SB_CFG)
APPKEY_DENY_PATHS.update({"/api/startbilder", "/startbilder"})
LOCK_DENY_PATHS.add("/api/startbilder")
if isinstance(_HP_TYPES, dict):
    _HP_TYPES.setdefault("webp", ("image/webp",))             # the check of the public addresses (639zzzh)

# the texts of the public page: key: (Deutsch, English, français, italiano, rumantsch) - fr / it / rm: still to be checked
SB_TX = {
    "titel.line": ("Dein Wächter fürs Lager draussen.", "Your guard for camp outdoors.", "Ton gardien pour le camp en plein air.",
                   "Il tuo guardiano per il campo all’aperto.", "Tes guardian per il champ a l’aviert."),
    "titel.kick": ("Unterwegs", "On the way", "En route", "In cammino", "Sin via"),
    "titel.say": ("Du gehst los – MoveEye kommt mit.", "You set off – MoveEye comes along.", "Tu pars – MoveEye t’accompagne.",
                  "Parti – MoveEye viene con te.", "Ti partas – MoveEye vegn cun tai."),
    "grat.kick": ("Über den Grat", "Along the ridge", "Sur l’arête", "Sulla cresta", "Sur la cresta"),
    "grat.say": ("Klein und leicht, im Rucksack immer dabei.", "Small and light, always in the backpack.", "Petit et léger, toujours dans le sac.",
                 "Piccolo e leggero, sempre nello zaino.", "Pitschen e lev, adina en il sac."),
    "lager.kick": ("Lagerplatz", "Camp", "Campement", "Accampamento", "Champ"),
    "lager.say": ("Lager aufschlagen, Kopf aufstellen, Schutz an.", "Pitch camp, set up the head, protection on.",
                  "Monter le camp, poser la tête, protection activée.", "Montare il campo, piazzare la testa, protezione attiva.",
                  "Far champ, metter si il chau, protecziun activa."),
    "abend.kick": ("Abend", "Evening", "Soir", "Sera", "Saira"),
    "abend.say": ("Die Sonne geht. MoveEye schaut sich um.", "The sun goes down. MoveEye looks around.", "Le soleil se couche. MoveEye regarde autour.",
                  "Il sole tramonta. MoveEye si guarda intorno.", "Il sulegl va da rendiu. MoveEye guarda enturn."),
    "nacht.kick": ("Nacht", "Night", "Nuit", "Notte", "Notg"),
    "nacht.say": ("Du schläfst. MoveEye wacht.", "You sleep. MoveEye keeps watch.", "Tu dors. MoveEye veille.", "Tu dormi. MoveEye veglia.",
                  "Ti dormas. MoveEye fa la guardia."),
    "pano.kick": ("Umsehen", "Look around", "Regarder autour", "Guardati intorno", "Guardar enturn"),
    "hint.swipe": ("↔ wischen zum Umsehen", "↔ swipe to look around", "↔ glisser pour regarder autour", "↔ scorri per guardarti intorno",
                   "↔ stritgar per guardar enturn"),
    "hint.drag": ("↔ ziehen zum Umsehen", "↔ drag to look around", "↔ tirer pour regarder autour", "↔ trascina per guardarti intorno",
                  "↔ trair per guardar enturn"),
    "alt.photo": ("Foto", "Photo", "Photo", "Foto", "Fotografia"),
    "alt.pano": ("Panorama zum Umsehen", "Panorama to look around", "Panorama à regarder", "Panorama da esplorare", "Panorama per guardar enturn"),
    "alt.drawn": ("Zeichnung: Berge und ein Zelt", "Drawing: mountains and a tent", "Dessin : montagnes et une tente",
                  "Disegno: montagne e una tenda", "Dissegn: muntognas ed ina tenda"),
    "lab.strip": ("Weitere Bilder", "More pictures", "Autres images", "Altre immagini", "Ulteriurs maletgs"),
}
_SB_LANGS = ("de", "en", "fr", "it", "rm")


def sb_dir():
    return os.path.join(DATA_DIR, "startseite")


def _sb_num(v, d=50.0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return d
    return round(min(max(x, 0.0), 100.0), 1) if x == x else d


def _sb_clean(t, n=90):
    return re.sub(r"[\x00-\x1f<>]", "", str(t or "")).strip()[:n]


def sb_meta():
    """{"slots": {place: {...}}, "texts": {place: {field: text}}} - only places whose picture is there"""
    try:
        with open(os.path.join(sb_dir(), "bilder.json"), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    s = d.get("slots") if isinstance(d, dict) and isinstance(d.get("slots"), dict) else {}
    t = d.get("texts") if isinstance(d, dict) and isinstance(d.get("texts"), dict) else {}
    s = {k: v for k, v in s.items() if k in SB_SLOTS and isinstance(v, dict) and os.path.isfile(os.path.join(sb_dir(), k + ".webp"))}
    t = {k: {f: _sb_clean(x) for f, x in v.items() if f in SB_FIELDS.get(k, ()) + ("alt",) and _sb_clean(x)}
         for k, v in t.items() if k in SB_SLOTS and isinstance(v, dict)}
    return {"slots": s, "texts": {k: v for k, v in t.items() if v}}


def _sb_write(name, data):
    os.makedirs(sb_dir(), exist_ok=True)
    p = os.path.join(sb_dir(), name); t = p + ".tmp"
    with open(t, "wb") as f:
        f.write(data)
    os.replace(t, p)


def _sb_save(m):
    _sb_write("bilder.json", json.dumps(m, ensure_ascii=False).encode("utf-8"))


def sb_make(raw, slot):
    """the uploaded picture -> (big WebP, size, small WebP or b"", size) without any metadata; raises ValueError(English text)"""
    from PIL import Image, ImageOps
    big, small, limit, axis, least = SB_SPEC[slot]
    if len(raw) > SB_UPLOAD_MAX:
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
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, (17, 20, 24, 255)); bg.alpha_composite(im); im = bg
        im = im.convert("RGB")
    except ValueError:
        raise
    except Exception:
        raise ValueError("This picture cannot be read. Please choose a JPEG or PNG.")
    if (im.size[0] if axis == "w" else im.size[1]) < least:
        raise ValueError("The picture is too small (at least {n} px wide)." if axis == "w" else "The picture is too small (at least {n} px high).")
    clean = Image.new("RGB", im.size)                          # only the picture points: no EXIF / GPS / XMP / ICC
    clean.paste(im)

    def fit(img, lim):
        w, h = img.size
        f = lim / float(w if axis == "w" else h)
        return img.resize((max(1, round(w * f)), max(1, round(h * f))), Image.LANCZOS) if f < 1 else img

    def enc(img, maxb):
        for _round in range(8):
            for q in (80, 74, 68, 62, 56, 50):
                b = io.BytesIO(); img.save(b, "WEBP", quality=q, method=4); out = b.getvalue()
                if len(out) <= maxb:
                    return out, img.size
            img = img.resize((max(1, round(img.size[0] * .85)), max(1, round(img.size[1] * .85))), Image.LANCZOS)
        return out, img.size
    B, bs = enc(fit(clean, big), limit)
    S, ss = enc(fit(clean, small), int(limit * .4)) if small else (b"", (0, 0))
    return B, bs, S, ss


def sb_set(slot, raw, fx=50, fy=50):
    if slot not in SB_SLOTS:
        raise ValueError("Unknown picture.")
    B, bs, S, ss = sb_make(raw, slot)
    with _SB_LOCK:
        m = sb_meta()
        _sb_write(slot + ".webp", B)
        if S:
            _sb_write(slot + "-k.webp", S)
        else:
            try:
                os.remove(os.path.join(sb_dir(), slot + "-k.webp"))
            except OSError:
                pass
        m["slots"][slot] = {"v": int(time.time() * 1000), "w": bs[0], "h": bs[1], "kw": ss[0], "kh": ss[1], "fx": _sb_num(fx), "fy": _sb_num(fy)}
        _sb_save(m)
    log_event("sys", f"Start page: own picture «{slot}» ({len(B) // 1024} KB)")
    return m["slots"][slot]


def sb_focus(slot, fx, fy):
    with _SB_LOCK:
        m = sb_meta()
        if slot not in m["slots"]:
            raise ValueError("Unknown picture.")
        m["slots"][slot].update(fx=_sb_num(fx), fy=_sb_num(fy))
        _sb_save(m)
    return m["slots"][slot]


def sb_texts(slot, d):
    if slot not in SB_SLOTS or not isinstance(d, dict):
        raise ValueError("Unknown picture.")
    with _SB_LOCK:
        m = sb_meta()
        t = {f: _sb_clean(d.get(f)) for f in SB_FIELDS.get(slot, ()) + ("alt",)}
        t = {f: v for f, v in t.items() if v}
        if t:
            m["texts"][slot] = t
        else:
            m["texts"].pop(slot, None)
        _sb_save(m)


def sb_reset(slot):
    if slot not in SB_SLOTS:
        raise ValueError("Unknown picture.")
    with _SB_LOCK:
        m = sb_meta(); m["slots"].pop(slot, None); _sb_save(m)
        for n in (slot + ".webp", slot + "-k.webp"):
            try:
                os.remove(os.path.join(sb_dir(), n))
            except OSError:
                pass
    log_event("sys", f"Start page: picture «{slot}» removed")


def sb_variant():
    return "A" if str(CFG.get("hp_start_variant") or "B").upper() == "A" else "B"


def sb_read(slot, small=False):
    p = os.path.join(sb_dir(), slot + ("-k" if small else "") + ".webp")
    if small and not os.path.isfile(p):
        p = os.path.join(sb_dir(), slot + ".webp")
    with open(p, "rb") as f:
        return f.read()


# ---- the public page ----------------------------------------------------------------------------------------------------------
SB_CSS = r""":root{--bg:#111418;--card:#1d2229;--line:#2c333c;--fg:#e8eaed;--mut:#9aa3ad;--kick:#f3c37a}
*{box-sizing:border-box}html{background:var(--bg)}
body{margin:0;font:17px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--fg)}
.first{display:flex;flex-direction:column;min-height:100vh;min-height:100svh}
.hero{position:relative;flex:1 1 auto;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;background:#0b0d10;
 min-height:calc(34*var(--vh,1vh))}
.hero>img,.hero>svg{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover}
.hero::before,.hero::after{content:"";position:absolute;left:0;right:0;pointer-events:none;z-index:1}
.hero::before{top:0;height:min(70%,calc(34*var(--vh,1vh)) + 60px);background:linear-gradient(to bottom,rgba(8,10,13,.75) 0%,rgba(8,10,13,.4) 55%,rgba(8,10,13,0) 100%)}
.hero::after{bottom:0;height:min(75%,calc(30*var(--vh,1vh)) + 60px);background:linear-gradient(to top,rgba(8,10,13,.88) 0%,rgba(8,10,13,.5) 50%,rgba(8,10,13,0) 100%)}
.top,.cap1{position:relative;z-index:2;padding-left:clamp(16px,4vw,32px);padding-right:clamp(16px,4vw,32px)}
.top{padding-top:calc(clamp(10px,calc(3*var(--vh,1vh)),28px) + env(safe-area-inset-top));margin-bottom:clamp(12px,calc(5*var(--vh,1vh)),80px)}
.top h1{margin:0;font-size:clamp(30px,min(8vw,calc(8.5*var(--vh,1vh))),64px);line-height:1.08;color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.5)}
.top p{margin:clamp(2px,calc(.8*var(--vh,1vh)),6px) 0 0;font-size:clamp(15px,min(3.8vw,calc(3*var(--vh,1vh))),22px);color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.7);max-width:36ch}
.cap1{padding-bottom:clamp(8px,calc(2.4*var(--vh,1vh)),26px)}
.kick{display:block;margin:0 0 clamp(2px,calc(.8*var(--vh,1vh)),6px);font-size:clamp(12px,calc(2*var(--vh,1vh)),15px);font-weight:600;letter-spacing:.08em;
 text-transform:uppercase;color:var(--kick);text-shadow:0 1px 6px rgba(0,0,0,.7)}
.line{display:block;font-size:clamp(20px,min(6vw,calc(5.6*var(--vh,1vh))),46px);font-weight:700;line-height:1.15;letter-spacing:-.01em;color:#fff;
 text-shadow:0 2px 12px rgba(0,0,0,.6);text-wrap:balance}
h2.lab{margin:0;padding:22px 20px 10px;font-size:15px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--kick)}
@media (min-width:900px){
 .top,.cap1{padding-left:max(32px,calc((100vw - 1100px)/2));padding-right:max(32px,calc((100vw - 1100px)/2))}
 h2.lab{padding:28px max(32px,calc((100vw - 1100px)/2)) 12px}
}
"""
SB_CSS_A = r""".story{position:relative;margin-top:24px}
.band{position:relative;margin:0;height:82svh;min-height:420px;overflow:hidden;background:#0b0d10}
.band img{display:block;width:100%;height:100%;object-fit:cover}
.band figcaption{position:absolute;left:0;right:0;bottom:0;padding:110px 20px calc(30px + env(safe-area-inset-bottom));
 background:linear-gradient(to top,rgba(8,10,13,.85) 0%,rgba(8,10,13,.55) 45%,rgba(8,10,13,0) 100%)}
.fx .story{height:calc(var(--n,4) * 100svh + 40svh)}
.fx .stage{position:sticky;top:0;height:100svh;overflow:hidden;background:#0b0d10}
.fx .stage::after{content:"";position:absolute;left:0;right:0;bottom:0;height:min(50svh,440px);pointer-events:none;z-index:2;
 background:linear-gradient(to top,rgba(8,10,13,.86) 0%,rgba(8,10,13,.55) 40%,rgba(8,10,13,0) 100%)}
.fx .band{position:absolute;inset:0;height:auto;min-height:0;opacity:0;will-change:opacity}
.fx .band.first{opacity:1}.fx .band.wait{display:none}
.fx .band img{transform:scale(var(--z,1.08)) translateY(var(--y,0));will-change:transform}
.fx .band figcaption{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.caps{display:none}
.fx .caps{display:block;position:absolute;inset:0;pointer-events:none;z-index:3}
.fx .cap{position:relative;height:100svh;display:flex;flex-direction:column;justify-content:flex-end;
 padding:0 max(20px,calc((100vw - 900px)/2)) calc(56px + env(safe-area-inset-bottom));opacity:var(--o,0);transform:translateY(var(--t,24px))}
.end{height:40px}
@media (min-width:900px){.band{height:min(82vh,760px)}}
"""
SB_CSS_B = r""".pano{position:relative;height:52svh;min-height:300px;max-height:760px;background:#0b0d10}
.scroller{height:100%;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;scroll-snap-type:none;overscroll-behavior-x:contain;
 scrollbar-width:none;cursor:grab;touch-action:pan-x pan-y}
.scroller::-webkit-scrollbar,.strip::-webkit-scrollbar{display:none}
.scroller.drag,.strip.drag{cursor:grabbing}
.scroller:focus-visible,.strip:focus-visible{outline:3px solid #e8a54b;outline-offset:-3px}
.scroller img{display:block;height:100%;width:auto;max-width:none;user-select:none;-webkit-user-drag:none}
.hint{position:absolute;z-index:2;left:50%;bottom:16px;transform:translateX(-50%);pointer-events:none;padding:8px 14px;border-radius:999px;
 background:rgba(8,10,13,.75);color:#fff;font-size:15px;white-space:nowrap;transition:opacity .8s ease;animation:nudge 2.4s ease-in-out 2}
.hint.weg{opacity:0}
@keyframes nudge{0%,100%{transform:translateX(-50%)}50%{transform:translateX(calc(-50% + 10px))}}
.strip{display:flex;gap:10px;overflow-x:auto;-webkit-overflow-scrolling:touch;scroll-snap-type:none;scrollbar-width:none;cursor:grab;
 padding:4px 20px calc(40px + env(safe-area-inset-bottom))}
.strip figure{margin:0;flex:none;height:180px;border-radius:12px;overflow:hidden;border:1px solid var(--line);background:#0b0d10}
.strip img{display:block;height:100%;width:auto;user-select:none;-webkit-user-drag:none}
@media (prefers-reduced-motion:reduce){.hint{animation:none;transition:none}}
@media (min-width:900px){.pano{height:min(62vh,640px)}
 .strip{padding-left:max(32px,calc((100vw - 1100px)/2));padding-right:max(32px,calc((100vw - 1100px)/2));padding-top:24px}.strip figure{height:220px}}
"""
SB_JS_LANG = r"""(function(){var T=/*T*/,l=(navigator.language||"de").slice(0,2).toLowerCase(),t=T[l];if(!t)return;document.documentElement.lang=l;
document.querySelectorAll("[data-t]").forEach(function(e){var v=t[e.getAttribute("data-t")];if(v)e.textContent=v;});
document.querySelectorAll("[data-a]").forEach(function(e){var v=t[e.getAttribute("data-a")];if(v)e.setAttribute("alt",v);});})();"""
SB_JS_A = r"""(function(){var mq=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)");if(!mq||mq.matches)return;
var story=document.getElementById("story");if(!story)return;var bands=story.querySelectorAll(".band"),caps=story.querySelectorAll(".cap"),n=bands.length,tick=false;
document.documentElement.classList.add("fx");story.style.setProperty("--n",n);for(var k=1;k<n;k++)bands[k].classList.add("wait");
function cl(x){return x<0?0:x>1?1:x;}
function draw(){tick=false;var p=-story.getBoundingClientRect().top/innerHeight;
 for(var i=0;i<n;i++){var b=bands[i],d=p-i;if(d>-1.6)b.classList.remove("wait");b.style.opacity=i===0?1:cl((d+0.4)/0.32);
  b.style.setProperty("--y",(-d*4).toFixed(2)+"%");b.style.setProperty("--z",(1.08-cl(d+1)*0.03).toFixed(4));
  var v=1-Math.abs(d)*2.2;caps[i].style.setProperty("--o",cl(v).toFixed(3));caps[i].style.setProperty("--t",((1-cl(v))*24).toFixed(1)+"px");}}
function req(){if(!tick){tick=true;requestAnimationFrame(draw);}}
addEventListener("scroll",req,{passive:true});addEventListener("resize",req);
if(mq.addEventListener)mq.addEventListener("change",function(){location.reload();});draw();})();"""
SB_JS_B = r"""(function(){var $=function(i){return document.getElementById(i);},sc=$("sc"),hint=$("hint");
function dragger(el,onMove){var down=false,x0=0,s0=0,v=0,lx=0,lt=0,raf=0;
 el.addEventListener("pointerdown",function(e){if(e.pointerType!=="mouse")return;down=true;x0=lx=e.clientX;s0=el.scrollLeft;lt=performance.now();v=0;cancelAnimationFrame(raf);el.classList.add("drag");el.setPointerCapture(e.pointerId);});
 el.addEventListener("pointermove",function(e){if(!down)return;var n=performance.now();el.scrollLeft=s0-(e.clientX-x0);v=(lx-e.clientX)/Math.max(1,n-lt);lx=e.clientX;lt=n;if(onMove)onMove();});
 function up(){if(!down)return;down=false;el.classList.remove("drag");if(matchMedia("(prefers-reduced-motion: reduce)").matches)return;
  (function glide(){v*=0.94;if(Math.abs(v)<0.02)return;el.scrollLeft+=v*16;raf=requestAnimationFrame(glide);})();}
 el.addEventListener("pointerup",up);el.addEventListener("pointercancel",up);
 el.addEventListener("keydown",function(e){var k=e.key==="ArrowRight"?1:e.key==="ArrowLeft"?-1:0;if(k){el.scrollBy({left:k*el.clientWidth*0.4,behavior:"smooth"});if(onMove)onMove();e.preventDefault();}});}
var st=document.querySelector(".strip");if(st)dragger(st);if(!sc)return;
var img=sc.querySelector("img"),start=0,gone=false,fx=+(sc.getAttribute("data-fx")||50)/100;
if(window.matchMedia&&matchMedia("(pointer:fine)").matches&&hint)hint.setAttribute("data-t","hint.drag"),hint.textContent=hint.getAttribute("data-d")||hint.textContent;
function bye(){if(!gone&&hint){gone=true;hint.classList.add("weg");}}
function center(){if(sc.scrollWidth>sc.clientWidth){sc.scrollLeft=(sc.scrollWidth-sc.clientWidth)*fx;start=sc.scrollLeft;}else bye();}
if(img.complete&&img.naturalWidth)center();else img.addEventListener("load",center);
if("IntersectionObserver" in window){var io=new IntersectionObserver(function(e){if(e[0].isIntersecting){setTimeout(bye,4500);io.disconnect();}},{threshold:.6});io.observe(sc);}else setTimeout(bye,4500);
sc.addEventListener("scroll",function(){if(Math.abs(sc.scrollLeft-start)>30)bye();},{passive:true});dragger(sc,bye);})();"""
SB_DRAWN = ('<svg viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" role="img" aria-label="{alt}" data-a="alt.drawn">'
            '<defs><linearGradient id="sbs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2a44"/><stop offset=".6" stop-color="#46607f"/>'
            '<stop offset="1" stop-color="#c98b5a"/></linearGradient></defs><rect width="1600" height="1000" fill="url(#sbs)"/>'
            '<path d="M0 700 L260 430 L420 560 L640 300 L900 600 L1100 420 L1320 610 L1600 380 L1600 1000 L0 1000Z" fill="#2a3a4c"/>'
            '<path d="M0 820 L300 640 L560 760 L820 600 L1080 780 L1400 640 L1600 720 L1600 1000 L0 1000Z" fill="#1c2733"/>'
            '<path d="M1060 860 L1160 740 L1260 860Z" fill="#c4762f"/><path d="M1160 740 L1160 860" stroke="#111418" stroke-width="6"/>'
            '<circle cx="1180" cy="230" r="46" fill="#f3d9a4" opacity=".85"/></svg>')


def _sb_btn_tx():
    """4.19.1: the texts of the buttons come from HP_LINKS (639zzzh) - the same links as the simple start page (22.11.2026: + the
    chips of the game, HP_GV_TX)"""
    return hp_tiles_tx()


def _sb_tx(key, L):
    v = SB_TX.get(key) or (_sb_btn_tx().get(key) if key.startswith(("btn.", "gv.")) else None) or ()
    i = _SB_LANGS.index(L) if L in _SB_LANGS else 0
    return v[i] if len(v) > i and v[i] else (v[0] if v else "")


def sb_page_html(variant=None, url=None, meta=None, kap=None):
    """the start page with the own pictures: url(place, small) -> address of the picture; None without any own picture of the variant;
    kap: the chapters of the game tile (default hp_gv_kapitel(), 639zzzh)"""
    import html as _h
    m = meta if meta is not None else sb_meta()
    v = variant if variant in SB_VARIANTS else sb_variant()
    S, TXT = m["slots"], m["texts"]
    if url is None or not any(k in S for k in SB_VARIANTS[v]):
        return None
    e = lambda x: _h.escape(str(x), quote=True)
    own = set()                                                  # text keys the owner changed: the same in every language

    def tx(slot, field):
        c = (TXT.get(slot) or {}).get(field)
        if c:
            own.add(slot + "." + field)
            return c
        return _sb_tx(slot + "." + field, "de")

    def alt(slot, key):
        c = (TXT.get(slot) or {}).get("alt")
        if c:
            return 'alt="%s"' % e(c)
        if "kick" in SB_FIELDS.get(slot, ()):
            return 'alt="%s" data-a="%s.kick"' % (e(tx(slot, "kick")), slot)
        return 'alt="%s" data-a="%s"' % (e(_sb_tx(key, "de")), key)

    def pos(slot):
        return "object-position:%s%% %s%%" % (S[slot].get("fx", 50), S[slot].get("fy", 50))

    def img(slot, vh, lazy=True, alt_of=None, key="alt.photo"):
        s = S[slot]
        sizes = "(orientation:portrait) %dvh, 100vw" % max(30, round(vh * s["w"] / max(1, s["h"])))
        srcset = (' srcset="%s %dw, %s %dw" sizes="%s"' % (e(url(slot, True)), s["kw"], e(url(slot, False)), s["w"], sizes)) if s.get("kw") else ""
        return '<img src="%s"%s width="%d" height="%d" %s decoding="async" style="%s" %s>' % (
            e(url(slot, False)), srcset, s["w"], s["h"], 'loading="lazy"' if lazy else 'fetchpriority="high"', pos(slot), alt(alt_of or slot, key))

    css = HP_TILES_CSS + SB_CSS + (SB_CSS_A if v == "A" else SB_CSS_B) + HP_EYE_CSS          # 4.19.1: the animated eye at the title
    hero = '<div class="first"><header class="hero">' + (img("titel", 72, lazy=False) if "titel" in S else SB_DRAWN.replace("{alt}", e(_sb_tx("alt.drawn", "de"))))
    hero += ('<div class="top"><h1>' + HP_EYE_SVG + 'MoveEye</h1><p data-t="titel.line">%s</p></div><div class="cap1"><span class="kick" data-t="titel.kick">%s</span>'
             '<span class="line" data-t="titel.say">%s</span></div></header>' % (e(tx("titel", "line")), e(tx("titel", "kick")), e(tx("titel", "say"))))
    btn = hp_links_html("de", kap) + '</div>'                    # 4.19.1: all links of HP_LINKS (22.11.2026: + chapters, Info/; one screen with the title)
    body, pre, post = "", "", ""
    if v == "A":
        ch = [k for k in SB_CHAPTERS if k in S or (k == "grat" and "grat_hoch" in S)]
        bands, caps = [], []
        for i, k in enumerate(ch):
            kick, say = e(tx(k, "kick")), e(tx(k, "say"))
            if k == "grat" and "grat" in S and "grat_hoch" in S:     # phone (portrait): the portrait picture with its own focus point
                hs = S["grat_hoch"]
                pic = ('<picture><source media="(orientation:portrait)" srcset="%s %dw, %s %dw" sizes="100vw">%s</picture>'
                       % (e(url("grat_hoch", True)), hs["kw"], e(url("grat_hoch", False)), hs["w"], img("grat", 100)))
                css += "@media (orientation:portrait){.band picture img{%s!important}}" % pos("grat_hoch")
            elif k == "grat" and "grat" not in S:
                pic = img("grat_hoch", 100, alt_of="grat")
            else:
                pic = img(k, 100)
            bands.append('<figure class="band%s">%s<figcaption><span class="kick" data-t="%s.kick">%s</span><span class="line" data-t="%s.say">%s</span>'
                         '</figcaption></figure>' % (" first" if i == 0 else "", pic, k, kick, k, say))
            caps.append('<div class="cap"><span class="kick" data-t="%s.kick">%s</span><span class="line" data-t="%s.say">%s</span></div>' % (k, kick, k, say))
        if ch:
            body = ('<div class="story" id="story"><div class="stage">' + "".join(bands) + '</div><div class="caps" aria-hidden="true">'
                    + "".join(caps) + '</div></div><div class="end"></div>')
            post = SB_JS_A
    else:
        if "pano" in S:
            s = S["pano"]
            r = s["w"] / max(1, s["h"])
            body += ('<h2 class="lab" id="lab" data-t="pano.kick">%s</h2><section class="pano" aria-labelledby="lab">'
                     '<div class="scroller" id="sc" tabindex="0" role="region" aria-labelledby="lab" data-fx="%s">'
                     '<img src="%s" srcset="%s %dw, %s %dw" sizes="(orientation:portrait) %dvh, %dvh" width="%d" height="%d" loading="lazy" '
                     'decoding="async" draggable="false" %s></div><div class="hint" id="hint" aria-hidden="true" data-t="hint.swipe" data-d="%s">%s</div></section>'
                     % (e(tx("pano", "kick")), s.get("fx", 50), e(url("pano", False)), e(url("pano", True)), s["kw"], e(url("pano", False)), s["w"],
                        max(60, round(52 * r)), max(60, round(62 * r)), s["w"], s["h"], alt("pano", "alt.pano"),
                        e(_sb_tx("hint.drag", "de")), e(_sb_tx("hint.swipe", "de"))))
        strip = [k for k in SB_LEISTE if k in S]
        if strip:
            body += '<div class="strip" tabindex="0" role="region" aria-label="%s">' % e(_sb_tx("lab.strip", "de")) + "".join(
                '<figure><img src="%s" width="%d" height="%d" loading="lazy" decoding="async" draggable="false" style="%s" %s></figure>'
                % (e(url(k, False)), S[k]["w"], S[k]["h"], pos(k), alt(k, "alt.photo")) for k in strip) + "</div>"
        pre = SB_JS_B                                                # first: the drag hint gets its key, then the language
    T = {L: {k: _sb_tx(k, L) for k in list(SB_TX) + list(_sb_btn_tx()) if k not in own} for L in _SB_LANGS[1:]}
    lang = SB_JS_LANG.replace("/*T*/", json.dumps(T, ensure_ascii=False, sort_keys=True).replace("</", "<\\/"), 1)
    head = ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>MoveEye</title><meta name="color-scheme" content="dark"><meta name="theme-color" content="#111418"><style>' + css + "</style></head><body>")
    return head + hero + btn + body + "<script>" + "\n".join(x for x in (pre, lang, post) if x) + "</script></body></html>\n"


def sb_publish_files(meta=None):
    """[(path on the web space, bytes)] for the start page with the own pictures, or [] (then the simple page stays)"""
    import hashlib
    m = meta if meta is not None else sb_meta()
    v = sb_variant()
    names, files = {}, []
    for k in SB_VARIANTS[v]:
        if k not in m["slots"]:
            continue
        try:
            big = sb_read(k)
            sm = sb_read(k, True) if m["slots"][k].get("kw") else b""
        except OSError:
            continue
        h = hashlib.sha256(big + sm).hexdigest()[:10]
        names[(k, False)] = "%s/%s-%s.webp" % (SB_DIR, k.replace("_", "-"), h)
        files.append((names[(k, False)], big))
        if sm:
            names[(k, True)] = "%s/%s-k-%s.webp" % (SB_DIR, k.replace("_", "-"), h)
            files.append((names[(k, True)], sm))
    if not files:
        return []
    m = {"slots": {k: v2 for k, v2 in m["slots"].items() if (k, False) in names}, "texts": m["texts"]}
    page = sb_page_html(v, lambda slot, small: names.get((slot, small)) or names[(slot, False)], m)
    return [(HP_START, page.encode("utf-8"))] + files if page else []


_hp_fixed_items_639zzzzf = hp_fixed_items


# wraps: hp_fixed_items
def hp_fixed_items():                                         # + 639zzzzf: the start page with the own pictures
    out = _hp_fixed_items_639zzzzf()
    if not hp_part_on("start"):
        return out
    try:
        files = sb_publish_files()
    except Exception as e:
        log_event("sys", "Start page pictures: " + e.__class__.__name__)
        files = []
    if not files:
        return out
    return [_hp_item(p, b) for p, b in files] + [it for it in out if it["path"] != HP_START]


_hp_part_639zzzzf = hp_part


# wraps: hp_part
def hp_part(p):                                               # + 639zzzzf: Startbilder/ belongs to the start page
    return "start" if str(p or "").startswith(SB_DIR + "/") else _hp_part_639zzzzf(p)


__hp_ours_639zzzzf = _hp_ours


# wraps: _hp_ours
def _hp_ours(p):                                              # + 639zzzzf
    return str(p or "").startswith(SB_DIR + "/") or __hp_ours_639zzzzf(p)


_hp_status_639zzzzf = hp_status


# wraps: hp_status
def hp_status():                                              # + 639zzzzf: variant and own pictures of the start page
    d = _hp_status_639zzzzf()
    S = sb_meta()["slots"]
    d.update(start_variant=sb_variant(), start_pics=sum(1 for k in SB_VARIANTS[sb_variant()] if k in S))
    return d


_hp_action_639zzzzf = hp_action


# wraps: hp_action
def hp_action(d, lang=None):                                  # + 639zzzzf: «start_variant» A / B
    if str(d.get("action") or "") == "start_variant":
        return sb_set_variant(d.get("v"))
    return _hp_action_639zzzzf(d, lang)


def sb_set_variant(v):
    v = str(v or "").upper()
    if v not in SB_VARIANTS:
        return False, "Unknown variant."
    if v != CFG.get("hp_start_variant"):
        CFG["hp_start_variant"] = v
        save_settings()
        log_event("sys", "Start page: variant " + v)
    return True, ""


def sb_state(lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    m = sb_meta()
    names = {"titel": "Title picture (A and B)", "grat": "A · chapter 2: ridge (computer, landscape)", "grat_hoch": "A · chapter 2: ridge (phone, portrait)",
             "lager": "A · chapter 3: camp", "abend": "A · chapter 4: evening", "nacht": "A · chapter 5: night", "pano": "B · panorama to look around"}
    notes = {"titel": "Large at the top with «MoveEye», the two buttons below. In A also chapter 1.",
             "grat": "Landscape or panorama.", "grat_hoch": "Optional: a portrait picture just for phones.",
             "pano": "A wide panorama (at least 1200 pixels wide).", "leiste": "Small, swipe sideways."}
    fl = {"line": "Title line", "kick": "Chapter name", "say": "Line on the picture", "alt": "Picture description (for screen readers)"}
    out = []
    for k in SB_SLOTS:
        s = m["slots"].get(k) or {}
        t = m["texts"].get(k) or {}
        if k in SB_LEISTE:
            name = tr("B · strip, picture {n}", L).replace("{n}", k[-1]); note = tr(notes["leiste"], L)
        else:
            name = tr(names[k], L); note = tr(notes[k], L) if k in notes else ""
        LL = L if L in _SB_LANGS else "en"
        fields = [{"f": f, "label": tr(fl[f], L), "value": t.get(f, ""), "def": _sb_tx(k + "." + f, LL)} for f in SB_FIELDS.get(k, ())]
        fields.append({"f": "alt", "label": tr(fl["alt"], L), "value": t.get("alt", ""), "def": ""})
        big, small, limit, axis, least = SB_SPEC[k]
        out.append({"id": k, "name": name, "note": note, "custom": bool(s), "v": s.get("v") or 0, "fx": s.get("fx", 50), "fy": s.get("fy", 50),
                    "w": s.get("w") or 0, "h": s.get("h") or 0, "fields": fields, "use": "".join(x for x in "AB" if k in SB_VARIANTS[x]),
                    "limit": "%d px · ≤ %d KB" % (big, limit // 1000)})
    return {"ok": True, "slots": out, "variant": sb_variant(), "start_on": hp_part_on("start"),
            "count": {x: sum(1 for k in SB_VARIANTS[x] if k in m["slots"]) for x in SB_VARIANTS}}


_smalltv_routes_639zzzzf = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzzf: page, preview, API and the pictures (only the administrator)
    _smalltv_routes_639zzzzf(app, reply, body)
    from flask import Response, request, g

    def no_(lang):
        return reply({"ok": False, "error": tr("Only the administrator can change the pictures of the start page.", lang)}, 403)

    @app.route("/startbilder")
    def sb_page_():
        if not pbild_admin(g):
            return no_(norm_lang(request.args.get("lang")))
        return Response(render_page(SB_UI_PAGE, "more"), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/startbilder/vorschau")
    def sb_preview_():
        if not pbild_admin(g):
            return no_(norm_lang(request.args.get("lang")))
        v = str(request.args.get("v") or sb_variant()).upper()
        m = sb_meta()
        h = sb_page_html(v if v in SB_VARIANTS else sb_variant(), lambda s, k: "/api/startbilder/bild/%s?k=%d&v=%s" % (s, 1 if k else 0, m["slots"][s].get("v")), m)
        return Response(h or hp_index_html(), mimetype="text/html", headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})

    @app.route("/api/startbilder", methods=["GET", "POST"])
    def api_sb():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if not pbild_admin(g):
            if (request.content_length or 0) < 1 << 20:
                request.get_data()
            return no_(lang)
        if request.method == "GET":
            return reply(sb_state(lang))
        a = request.args.get("action") or ""
        try:
            if a == "set":
                n = request.content_length or 0
                if n > SB_UPLOAD_MAX:
                    raise ValueError("The picture is too big (at most 25 MB).")
                slot = request.args.get("slot") or ""
                if slot not in SB_SLOTS:
                    raise ValueError("Unknown picture.")
                sb_set(slot, request.get_data(cache=False), request.args.get("fx", 50), request.args.get("fy", 50))
            else:
                d = body(); a = a or str(d.get("action") or ""); slot = str(d.get("slot") or "")
                if a == "focus":
                    sb_focus(slot, d.get("fx"), d.get("fy"))
                elif a == "texts":
                    sb_texts(slot, d.get("texts"))
                elif a == "reset":
                    sb_reset(slot)
                elif a == "variant":
                    okv, err = sb_set_variant(d.get("v"))
                    if not okv:
                        raise ValueError(err)
                else:
                    raise ValueError("Unknown picture.")
        except ValueError as e:
            least = SB_SPEC.get(request.args.get("slot") or "", (0, 0, 0, "w", 0))[4]
            return reply(dict(sb_state(lang), ok=False, error=tr(str(e), lang).replace("{n}", str(least))), 400)
        return reply(sb_state(lang))

    @app.route("/api/startbilder/bild/<slot>")
    def api_sb_img(slot):
        if not pbild_admin(g):
            return no_(norm_lang(request.args.get("lang")))
        if slot not in SB_SLOTS or slot not in sb_meta()["slots"]:
            return Response("not found", 404)
        return Response(sb_read(slot, request.args.get("k") == "1"), mimetype="image/webp", headers={"Cache-Control": "no-store"})


# ---- the entry: card «Homepage» (639zzzh), right under the switch «Start page»: variant A / B and the button -------------------------
_SB_HP_AT = '<label class="hp-chk"><input type="checkbox" id="hp-start"><span id="hp-start-l"></span></label>'
_SB_HP_ROW = ('<div class="hp-row" id="hp-sb-row" style="margin:0 0 6px"><select id="hp-sb-var" aria-label="Variant" style="font:inherit;font-size:15px;min-height:44px;'
              'border-radius:10px;border:1px solid var(--line);background:var(--field);color:var(--txt);padding:0 8px"><option value="B" data-i18n="B · panorama and strip of pictures">B</option>'
              '<option value="A" data-i18n="A · picture story (day to night)">A</option></select><a class="btn sec" id="hp-sbild" href="/startbilder" style="display:inline-flex;align-items:center;'
              'justify-content:center;gap:6px;text-decoration:none;box-sizing:border-box">🏞 <span data-i18n="Start page: pictures">Start page: pictures</span></a></div>')
if 'id="hp-sbild"' not in HP_PAGE and HP_PAGE.count(_SB_HP_AT) == 1:
    HP_PAGE = HP_PAGE.replace(_SB_HP_AT, _SB_HP_AT + _SB_HP_ROW, 1)
SB_HP_JS = r"""(function(){const s=document.getElementById("hp-sb-var");if(!s)return;
document.querySelectorAll("#hp-sb-row [data-i18n]").forEach(e=>e.textContent=t(e.dataset.i18n));
const L=()=>{try{return LANG||"de";}catch(e){return "de";}};
fetch("/api/startbilder?lang="+L(),{cache:"no-store"}).then(r=>r.json()).then(j=>{if(j&&j.variant)s.value=j.variant;}).catch(()=>{});
s.onchange=()=>fetch("/api/startbilder?lang="+L(),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"variant",v:s.value})}).catch(()=>{});})();"""

# ---- texts (English key: Deutsch, français, italiano, rumantsch) - fr / it / rm: still to be checked ----------------------------------
_HX_SB = {
    "Start page: pictures": ("Startseite: Bilder", "Page d’accueil : images", "Pagina iniziale: immagini", "Pagina d’entrada: maletgs"),
    "A · picture story (day to night)": ("A · Bildgeschichte (Tag bis Nacht)", "A · histoire en images (du jour à la nuit)",
                                         "A · storia per immagini (dal giorno alla notte)", "A · istorgia en maletgs (dal di a la notg)"),
    "B · panorama and strip of pictures": ("B · Panorama und Bildleiste", "B · panorama et bande d’images", "B · panorama e striscia di immagini",
                                           "B · panorama e strivla da maletgs"),
    "Variant of the start page": ("Variante der Startseite", "Variante de la page d’accueil", "Variante della pagina iniziale", "Varianta da la pagina d’entrada"),
    "Your photos for the start page of your homepage. They stay on MoveEye and go to the web space as Startbilder/ when «Start page» is switched on.": (
        "Deine Fotos für die Startseite deiner Homepage. Sie bleiben auf MoveEye und kommen als Startbilder/ auf den Webspace, wenn «Startseite» eingeschaltet ist.",
        "Tes photos pour la page d’accueil de ton site. Elles restent sur MoveEye et vont sur l’espace web dans Startbilder/ quand «Page d’accueil» est activée.",
        "Le tue foto per la pagina iniziale del tuo sito. Restano su MoveEye e vanno sullo spazio web in Startbilder/ quando «Pagina iniziale» è attiva.",
        "Tias fotografias per la pagina d’entrada da tia pagina d’internet. Ellas restan sin MoveEye e van sin il spazi web en Startbilder/, sche «Pagina d’entrada» è activada."),
    "No people, number plates, house numbers or place signs.": ("Keine Personen, Kennzeichen, Hausnummern oder Ortsschilder.",
                                                                "Pas de personnes, de plaques, de numéros de maison ni de panneaux de lieu.",
                                                                "Niente persone, targhe, numeri civici o cartelli di località.",
                                                                "Naginas persunas, numers da vehichels, numers da chasa u tavlas da lieu."),
    "Location data (EXIF, GPS) is removed and the picture is made smaller. Tap the picture: that point stays visible on phones.": (
        "Standortdaten (EXIF, GPS) werden entfernt und das Bild verkleinert. Tippe aufs Bild: dieser Punkt bleibt auf dem Handy sichtbar.",
        "Les données de position (EXIF, GPS) sont supprimées et l’image est réduite. Touche l’image : ce point reste visible sur le téléphone.",
        "I dati di posizione (EXIF, GPS) vengono rimossi e l’immagine ridotta. Tocca l’immagine: quel punto resta visibile sul telefono.",
        "Las datas da lieu (EXIF, GPS) vegnan allontanadas ed il maletg vegn pli pitschen. Tutga il maletg: quest punct resta visibel sin il telefonin."),
    "The start page is switched off on the homepage – it is not uploaded at the moment.": (
        "Die Startseite ist auf der Homepage ausgeschaltet – sie wird im Moment nicht hochgeladen.",
        "La page d’accueil est désactivée sur le site – elle n’est pas envoyée pour le moment.",
        "La pagina iniziale è disattivata sulla homepage – al momento non viene caricata.",
        "La pagina d’entrada è deactivada sin la pagina d’internet – ella na vegn per il mument betg chargiada."),
    "Without own pictures the simple start page stays.": ("Ohne eigene Bilder bleibt die schlichte Startseite.",
                                                          "Sans images personnelles, la page d’accueil simple reste.",
                                                          "Senza immagini proprie resta la pagina iniziale semplice.",
                                                          "Senza agens maletgs resta la pagina d’entrada simpla."),
    "Preview": ("Vorschau", "Aperçu", "Anteprima", "Prevista"),
    "Both variants": ("Beide Varianten", "Les deux variantes", "Entrambe le varianti", "Omaduas variantas"),
    "Variant A · picture story": ("Variante A · Bildgeschichte", "Variante A · histoire en images", "Variante A · storia per immagini",
                                  "Varianta A · istorgia en maletgs"),
    "Variant B · panorama and strip": ("Variante B · Panorama und Bildleiste", "Variante B · panorama et bande", "Variante B · panorama e striscia",
                                       "Varianta B · panorama e strivla"),
    "Title picture (A and B)": ("Titelbild (A und B)", "Image de titre (A et B)", "Immagine del titolo (A e B)", "Maletg da titel (A e B)"),
    "A · chapter 2: ridge (computer, landscape)": ("A · Kapitel 2: Grat (PC, quer)", "A · chapitre 2 : arête (ordinateur, paysage)",
                                                   "A · capitolo 2: cresta (computer, orizzontale)", "A · chapitel 2: cresta (computer, per traviers)"),
    "A · chapter 2: ridge (phone, portrait)": ("A · Kapitel 2: Grat (Handy, hochkant)", "A · chapitre 2 : arête (téléphone, portrait)",
                                               "A · capitolo 2: cresta (telefono, verticale)", "A · chapitel 2: cresta (telefonin, per lung)"),
    "A · chapter 3: camp": ("A · Kapitel 3: Lagerplatz", "A · chapitre 3 : campement", "A · capitolo 3: accampamento", "A · chapitel 3: champ"),
    "A · chapter 4: evening": ("A · Kapitel 4: Abend", "A · chapitre 4 : soir", "A · capitolo 4: sera", "A · chapitel 4: saira"),
    "A · chapter 5: night": ("A · Kapitel 5: Nacht", "A · chapitre 5 : nuit", "A · capitolo 5: notte", "A · chapitel 5: notg"),
    "B · panorama to look around": ("B · Panorama zum Umsehen", "B · panorama à regarder", "B · panorama da esplorare", "B · panorama per guardar enturn"),
    "B · strip, picture {n}": ("B · Bildleiste, Bild {n}", "B · bande, image {n}", "B · striscia, immagine {n}", "B · strivla, maletg {n}"),
    "Large at the top with «MoveEye», the two buttons below. In A also chapter 1.": (
        "Gross oben mit «MoveEye», darunter die zwei Knöpfe. In A auch Kapitel 1.",
        "En grand en haut avec «MoveEye», les deux boutons en dessous. Dans A aussi le chapitre 1.",
        "Grande in alto con «MoveEye», sotto i due pulsanti. In A anche capitolo 1.",
        "Grond sisum cun «MoveEye», sutvart ils dus buttuns. En A er chapitel 1."),
    "Landscape or panorama.": ("Querformat oder Panorama.", "Paysage ou panorama.", "Orizzontale o panorama.", "Per traviers u panorama."),
    "Optional: a portrait picture just for phones.": ("Freiwillig: ein Hochformat nur für Handys.", "Facultatif : une image portrait seulement pour les téléphones.",
                                                      "Facoltativo: un’immagine verticale solo per i telefoni.", "Facultativ: in maletg per lung mo per telefonins."),
    "A wide panorama (at least 1200 pixels wide).": ("Ein breites Panorama (mindestens 1200 Pixel breit).", "Un large panorama (au moins 1200 pixels de large).",
                                                     "Un panorama largo (almeno 1200 pixel di larghezza).", "In panorama lad (almain 1200 pixels lad)."),
    "Small, swipe sideways.": ("Klein, seitwärts wischen.", "Petite, glisser sur le côté.", "Piccola, scorrere di lato.", "Pitschen, stritgar da la vart."),
    "Title line": ("Titelzeile", "Ligne de titre", "Riga del titolo", "Lingia da titel"),
    "Chapter name": ("Kapitelname", "Nom du chapitre", "Nome del capitolo", "Num dal chapitel"),
    "Line on the picture": ("Zeile auf dem Bild", "Ligne sur l’image", "Riga sull’immagine", "Lingia sin il maletg"),
    "Picture description (for screen readers)": ("Bildbeschreibung (für Bildschirmleser)", "Description de l’image (pour lecteurs d’écran)",
                                                 "Descrizione dell’immagine (per lettori di schermo)", "Descripziun dal maletg (per lecturs da visur)"),
    "Empty = standard text (in 5 languages). Your own text is shown in every language.": (
        "Leer = Standardtext (in 5 Sprachen). Ein eigener Text erscheint in jeder Sprache.",
        "Vide = texte standard (en 5 langues). Ton propre texte apparaît dans chaque langue.",
        "Vuoto = testo standard (in 5 lingue). Il tuo testo appare in ogni lingua.",
        "Vid = text da standard (en 5 linguas). In agen text cumpara en mintga lingua."),
    "Save the texts": ("Texte speichern", "Enregistrer les textes", "Salva i testi", "Memorisar ils texts"),
    "Choose a picture": ("Bild wählen", "Choisir une image", "Scegli un’immagine", "Tscherner in maletg"),
    "Remove the picture": ("Bild entfernen", "Retirer l’image", "Rimuovi l’immagine", "Allontanar il maletg"),
    "Remove this picture from MoveEye?": ("Dieses Bild von MoveEye entfernen?", "Retirer cette image de MoveEye ?", "Rimuovere questa immagine da MoveEye?",
                                          "Allontanar quest maletg da MoveEye?"),
    "No own picture": ("Kein eigenes Bild", "Pas d’image personnelle", "Nessuna immagine propria", "Nagin agen maletg"),
    "Focus point saved.": ("Fokuspunkt gespeichert.", "Point de mire enregistré.", "Punto focale salvato.", "Punct da focus memorisà."),
    "Uploading …": ("Hochladen …", "Envoi …", "Caricamento …", "Chargiar …"),
    "used in": ("verwendet in", "utilisée dans", "usata in", "duvrà en"),
    "Only the administrator can change the pictures of the start page.": (
        "Nur der Administrator kann die Bilder der Startseite ändern.", "Seul l’administrateur peut changer les images de la page d’accueil.",
        "Solo l’amministratore può cambiare le immagini della pagina iniziale.", "Mo l’administratur po midar ils maletgs da la pagina d’entrada."),
    "The picture is too small (at least {n} px wide).": ("Das Bild ist zu klein (mindestens {n} px breit).", "L’image est trop petite (au moins {n} px de large).",
                                                         "L’immagine è troppo piccola (almeno {n} px di larghezza).", "Il maletg è memia pitschen (almain {n} px lad)."),
    "The picture is too small (at least {n} px high).": ("Das Bild ist zu klein (mindestens {n} px hoch).", "L’image est trop petite (au moins {n} px de haut).",
                                                         "L’immagine è troppo piccola (almeno {n} px di altezza).", "Il maletg è memia pitschen (almain {n} px aut)."),
    "Unknown variant.": ("Unbekannte Variante.", "Variante inconnue.", "Variante sconosciuta.", "Varianta nunenconuschenta."),
}
for _k, _v in _HX_SB.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_SB_DE = {_k: DE.get(_k, _v[0]) for _k, _v in _HX_SB.items()}
_SB_UI_KEYS = tuple(_HX_SB) + ("Saved.", "Saving …", "Cancel", "No connection to MoveEye.", "Homepage", "Own picture", "Replace",
                               "This picture cannot be read. Please choose a JPEG or PNG.", "The picture is too big (at most 25 MB).", "Unknown picture.")

_render_page_639zzzzf = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzzzf: the German texts of the page and of the entry
    out = _render_page_639zzzzf(page, active)
    if 'id="hp-sbild"' in out:
        de_ = {k: _SB_DE[k] for k in ("Start page: pictures", "A · picture story (day to night)", "B · panorama and strip of pictures")}
        out = out.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps(de_, ensure_ascii=False) + ");" + SB_HP_JS + "</script></body>", 1)
    if "/*SBDE*/" in out:
        de_ = {k: DE.get(k, k) for k in _SB_UI_KEYS}
        out = out.replace("/*SBDE*/", "Object.assign(I18N.de, " + json.dumps(de_, ensure_ascii=False).replace("</", "<\\/") + ");", 1)
    return out


SB_UI_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Start page: pictures</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:760px;margin:0 auto;box-sizing:border-box}
.sb-back{display:inline-flex;align-items:center;min-height:40px;text-decoration:none;color:var(--acc);font-weight:600;margin:0 0 4px}
#sb-title{margin:0 0 10px;font-size:20px}
.sb-box{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px 14px;margin:0 0 14px;display:grid;gap:8px;font-size:14px}
.sb-box .warn{color:var(--yel);font-weight:700}.sb-box .mut{color:var(--mut);font-size:13px}.sb-off{color:var(--yel);font-size:13px}
.sb-var{display:grid;gap:6px}.sb-var label{display:flex;gap:10px;align-items:center;min-height:44px;border:1px solid var(--line);border-radius:10px;padding:0 12px;cursor:pointer}
.sb-var label.on{border-color:var(--acc);box-shadow:inset 0 0 0 1px var(--acc)}
.sb-var small{color:var(--mut);margin-left:auto;font-size:12px}
.sb-pv{display:flex;flex-wrap:wrap;gap:8px}.sb-pv a{min-height:40px;display:inline-flex;align-items:center;padding:0 14px;border-radius:10px;border:1px solid var(--line);
color:var(--txt);text-decoration:none;font-size:14px}
.sb-g{margin:18px 0 8px;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
.sb-list{display:grid;gap:12px}
.sb-c{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px;display:grid;grid-template-columns:minmax(0,220px) minmax(0,1fr);gap:12px;align-items:start}
.sb-img{position:relative;aspect-ratio:4/3;border-radius:10px;overflow:hidden;background:#000;border:1px solid var(--line);display:flex;align-items:center;justify-content:center}
.sb-img img{max-width:100%;max-height:100%;display:block;-webkit-user-drag:none;user-select:none;cursor:crosshair;touch-action:manipulation}
.sb-img .none{color:var(--mut);font-size:13px;padding:10px;text-align:center}
.sb-dot{position:absolute;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 2px #e8a54b,0 1px 6px rgba(0,0,0,.6);pointer-events:none}
.sb-b{display:grid;gap:6px;min-width:0}.sb-b b{font-size:15px}.sb-b small{color:var(--mut);font-size:12px}
.sb-st{font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}.sb-st.own{color:var(--grn)}
.sb-a{display:flex;flex-wrap:wrap;gap:8px}.sb-a button,.sb-a label{min-height:40px;font:inherit;font-size:14px;display:inline-flex;align-items:center;cursor:pointer}
.sb-a label{padding:0 14px;border-radius:10px;background:var(--acc);color:#fff;font-weight:600;position:relative}
.sb-a label input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.sb-t{grid-column:1/-1;display:grid;gap:6px;border-top:1px solid var(--line);padding-top:10px}
.sb-t label{display:grid;gap:4px;font-size:12px;color:var(--mut)}
.sb-t input{font:inherit;font-size:16px;min-height:44px;width:100%;box-sizing:border-box;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:6px 10px}
.sb-t button{justify-self:start;min-height:40px}
.sb-msg{font-size:13px;min-height:1.2em}.sb-msg.err{color:var(--red)}.sb-msg.ok{color:var(--grn)}
@media(max-width:560px){.sb-c{grid-template-columns:minmax(0,1fr)}}
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
  <a class="sb-back" href="/homepage" id="sb-back">‹ Homepage</a>
  <h2 id="sb-title">🏞 Start page: pictures</h2>
  <section class="sb-box"><span id="sb-h1"></span><span class="warn" id="sb-h2"></span><span class="mut" id="sb-h3"></span>
    <span class="sb-off" id="sb-off" hidden></span></section>
  <section class="sb-box"><b id="sb-var-t"></b><div class="sb-var" id="sb-var"></div><div class="mut" id="sb-plain"></div>
    <div class="sb-pv"><a id="sb-pv-a" href="/startbilder/vorschau?v=A" target="_blank" rel="noopener"></a><a id="sb-pv-b" href="/startbilder/vorschau?v=B" target="_blank" rel="noopener"></a></div></section>
  <div id="sb-list"></div>
</main>
<script>
/*COMMON*/
/*SBDE*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  document.title = "MoveEye – " + t("Start page: pictures");
  $i("sb-back").textContent = "‹ " + t("Homepage"); $i("sb-title").textContent = "🏞 " + t("Start page: pictures");
  $i("sb-h1").textContent = t("Your photos for the start page of your homepage. They stay on MoveEye and go to the web space as Startbilder/ when «Start page» is switched on.");
  $i("sb-h2").textContent = "⚠ " + t("No people, number plates, house numbers or place signs.");
  $i("sb-h3").textContent = t("Location data (EXIF, GPS) is removed and the picture is made smaller. Tap the picture: that point stays visible on phones.");
  $i("sb-var-t").textContent = t("Variant of the start page"); $i("sb-plain").textContent = t("Without own pictures the simple start page stays.");
  $i("sb-pv-a").textContent = "👁 " + t("Preview") + " A"; $i("sb-pv-b").textContent = "👁 " + t("Preview") + " B";
  let J = null;
  const get = async () => { try { const r = await fetch("/api/startbilder?lang=" + L(), {cache: "no-store"}); return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  const post = async (q, data, json) => {
    try { const r = await fetch("/api/startbilder?lang=" + L() + (q ? "&" + q : ""), {method: "POST", body: data,
        headers: {"Content-Type": json ? "application/json" : "application/octet-stream"}}); return await r.json(); }
    catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  const say = (el, j, okText) => { el.className = "sb-msg " + (j && j.ok ? "ok" : "err"); el.textContent = j && j.ok ? okText : ((j && j.error) || ""); };
  function card(s) {
    const c = E("section", "sb-c"), box = E("div", "sb-img"), b = E("div", "sb-b"), msg = E("div", "sb-msg");
    c.id = "sb-" + s.id;
    if (s.custom) {
      const im = E("img"), dot = E("div", "sb-dot"); im.src = "/api/startbilder/bild/" + s.id + "?k=1&v=" + s.v; im.alt = s.name;
      const place = () => { dot.style.left = (im.offsetLeft + im.offsetWidth * s.fx / 100) + "px"; dot.style.top = (im.offsetTop + im.offsetHeight * s.fy / 100) + "px"; };
      im.onload = place; addEventListener("resize", place);
      im.onclick = async ev => { const r = im.getBoundingClientRect(); s.fx = Math.round((ev.clientX - r.left) / r.width * 1000) / 10; s.fy = Math.round((ev.clientY - r.top) / r.height * 1000) / 10;
        place(); const j = await post("", JSON.stringify({action: "focus", slot: s.id, fx: s.fx, fy: s.fy}), true); say(msg, j, t("Focus point saved.")); };
      box.appendChild(im); box.appendChild(dot);
    } else box.appendChild(E("div", "none", t("No own picture")));
    b.appendChild(E("b", "", s.name));
    b.appendChild(E("span", "sb-st" + (s.custom ? " own" : ""), s.custom ? "✓ " + t("Own picture") + (s.w ? " · " + s.w + " × " + s.h : "") : t("No own picture")));
    if (s.note) b.appendChild(E("small", "", s.note));
    b.appendChild(E("small", "", t("used in") + ": " + s.use.split("").join(" + ") + " · " + s.limit));
    const a = E("div", "sb-a"), up = E("label"), inp = E("input");
    inp.type = "file"; inp.accept = "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif";
    up.appendChild(document.createTextNode("⬆ " + (s.custom ? t("Replace") : t("Choose a picture")))); up.appendChild(inp); a.appendChild(up);
    inp.onchange = async () => { const f = inp.files && inp.files[0]; inp.value = ""; if (!f) return;
      msg.className = "sb-msg"; msg.textContent = t("Uploading …");
      const j = await post("action=set&slot=" + s.id + "&fx=" + s.fx + "&fy=" + s.fy, f);
      if (j.ok) { J = j; paint(); } else say(msg, j, ""); };
    if (s.custom) { const rb = E("button", "sec", "✕ " + t("Remove the picture")); rb.type = "button";
      rb.onclick = async () => { if (!confirm(t("Remove this picture from MoveEye?"))) return; rb.disabled = true;
        const j = await post("", JSON.stringify({action: "reset", slot: s.id}), true); if (j.ok) { J = j; paint(); } else { rb.disabled = false; say(msg, j, ""); } };
      a.appendChild(rb); }
    b.appendChild(a); b.appendChild(msg);
    const tb = E("div", "sb-t"), ins = {};
    s.fields.forEach(f => { const l = E("label"), i = E("input"); l.appendChild(document.createTextNode(f.label)); i.type = "text"; i.maxLength = 90;
      i.value = f.value || ""; i.placeholder = f.def || ""; l.appendChild(i); tb.appendChild(l); ins[f.f] = i; });
    tb.appendChild(E("small", "mut", t("Empty = standard text (in 5 languages). Your own text is shown in every language.")));
    const sv = E("button", "sec", "✓ " + t("Save the texts")), tm = E("div", "sb-msg"); sv.type = "button";
    sv.onclick = async () => { const tx = {}; Object.keys(ins).forEach(k => tx[k] = ins[k].value.trim()); sv.disabled = true;
      const j = await post("", JSON.stringify({action: "texts", slot: s.id, texts: tx}), true); sv.disabled = false; say(tm, j, t("Saved.")); };
    tb.appendChild(sv); tb.appendChild(tm);
    c.appendChild(box); c.appendChild(b); c.appendChild(tb);
    return c;
  }
  function paint() {
    const list = $i("sb-list"); list.textContent = "";
    if (!J || !J.ok) { list.appendChild(E("div", "sb-msg err", (J && J.error) || "")); return; }
    $i("sb-off").hidden = !!J.start_on; $i("sb-off").textContent = t("The start page is switched off on the homepage – it is not uploaded at the moment.");
    const vv = $i("sb-var"); vv.textContent = "";
    [["A", t("A · picture story (day to night)")], ["B", t("B · panorama and strip of pictures")]].forEach(([k, n]) => {
      const l = E("label", J.variant === k ? "on" : ""), r = E("input"); r.type = "radio"; r.name = "sbv"; r.value = k; r.checked = J.variant === k;
      l.appendChild(r); l.appendChild(E("span", "", n)); l.appendChild(E("small", "", "📷 " + (J.count[k] || 0)));
      r.onchange = async () => { const j = await post("", JSON.stringify({action: "variant", v: k}), true); if (j.ok) { J = j; paint(); } };
      vv.appendChild(l); });
    const groups = [["AB", t("Both variants")], ["A", t("Variant A · picture story")], ["B", t("Variant B · panorama and strip")]];
    groups.forEach(([u, n]) => { list.appendChild(E("div", "sb-g", n)); const g = E("div", "sb-list");
      J.slots.filter(s => s.use === u).forEach(s => g.appendChild(card(s))); list.appendChild(g); });
  }
  J = await get(); paint();
})();
</script>
</body></html>"""

# ---- the manual: one point after «🌐 Homepage» in the section «Morse-Modus» -----------------------------------------------------------
SB_HELP_HTML = r"""
de|<li><b>🏞 Startseite: Bilder</b> (Karte «Homepage», nur der Administrator): eigene Fotos für die Startseite deiner Homepage – Variante A «Bildgeschichte» (Titelbild, dann Grat, Lagerplatz, Abend, Nacht, sanft überblendet) oder B «Panorama zum Umsehen» mit einer kleinen Bildleiste; ab Werk B. Die zwei Knöpfe (Funkgerät, Simulator) stehen immer direkt unter dem Titelbild. Tippe aufs Bild für den Fokuspunkt (bleibt auf dem Handy sichtbar); jede Zeile ist änderbar, leer = Standardtext in 5 Sprachen. Standortdaten (EXIF, GPS) werden entfernt, die Bilder verkleinert (Panorama höchstens 400 KB) und nur auf MoveEye gespeichert; hochgeladen werden sie als <code>Startbilder/</code>, wenn «Startseite» an ist. Ohne eigene Bilder bleibt die schlichte Startseite.</li>
en|<li><b>🏞 Start page: pictures</b> (card «Homepage», administrator only): your own photos for the start page of your homepage – variant A «picture story» (title picture, then ridge, camp, evening, night, gently cross-faded) or B «panorama to look around» with a small strip of pictures; B by default. The two buttons (radio, simulator) are always right under the title picture. Tap the picture for the focus point (stays visible on phones); every line can be changed, empty = standard text in 5 languages. Location data (EXIF, GPS) is removed, the pictures are made smaller (panorama at most 400 KB) and stored on MoveEye only; they are uploaded as <code>Startbilder/</code> when «Start page» is on. Without own pictures the simple start page stays.</li>
fr|<li><b>🏞 Page d’accueil : images</b> (carte «Page d’accueil», administrateur seulement) : tes propres photos pour la page d’accueil de ton site – variante A «histoire en images» (image de titre, puis arête, campement, soir, nuit, en fondu doux) ou B «panorama à regarder» avec une petite bande d’images ; B par défaut. Les deux boutons (radio, simulateur) sont toujours juste sous l’image de titre. Touche l’image pour le point de mire (reste visible sur le téléphone) ; chaque ligne est modifiable, vide = texte standard en 5 langues. Les données de position (EXIF, GPS) sont supprimées, les images réduites (panorama 400 Ko au plus) et enregistrées seulement sur MoveEye ; elles sont envoyées dans <code>Startbilder/</code> quand «Page d’accueil» est activée. Sans images personnelles, la page d’accueil simple reste.</li>
it|<li><b>🏞 Pagina iniziale: immagini</b> (scheda «Homepage», solo l’amministratore): le tue foto per la pagina iniziale del tuo sito – variante A «storia per immagini» (immagine del titolo, poi cresta, accampamento, sera, notte, in dissolvenza) o B «panorama da esplorare» con una piccola striscia di immagini; B di fabbrica. I due pulsanti (radio, simulatore) sono sempre subito sotto l’immagine del titolo. Tocca l’immagine per il punto focale (resta visibile sul telefono); ogni riga si può cambiare, vuoto = testo standard in 5 lingue. I dati di posizione (EXIF, GPS) vengono rimossi, le immagini ridotte (panorama al massimo 400 KB) e salvate solo su MoveEye; vengono caricate in <code>Startbilder/</code> quando «Pagina iniziale» è attiva. Senza immagini proprie resta la pagina iniziale semplice.</li>
rm|<li><b>🏞 Pagina d’entrada: maletgs</b> (carta «Pagina d’entrada», mo l’administratur): tias atgnas fotografias per la pagina d’entrada da tia pagina d’internet – varianta A «istorgia en maletgs» (maletg da titel, lura cresta, champ, saira, notg, surglischads plaun) u B «panorama per guardar enturn» cun ina pitschna strivla da maletgs; da fabrica B. Ils dus buttuns (radio, simulatur) èn adina directamain sut il maletg da titel. Tutga il maletg per il punct da focus (resta visibel sin il telefonin); mintga lingia è midabla, vid = text da standard en 5 linguas. Las datas da lieu (EXIF, GPS) vegnan allontanadas, ils maletgs fatgs pli pitschens (panorama maximalmain 400 KB) e memorisads mo sin MoveEye; els vegnan chargiads en <code>Startbilder/</code>, sche «Pagina d’entrada» è activada. Senza agens maletgs resta la pagina d’entrada simpla.</li>
"""


def _help_sb(doc, lang):
    try:
        li = dict(x.split("|", 1) for x in SB_HELP_HTML.strip().split("\n") if "|" in x).get(lang)
    except ValueError:
        li = None
    i = doc.find('<section id="morse"')
    j = doc.find("</ul></section>", i)
    return doc if not li or i < 0 or j < 0 or "🏞 " in doc[i:j] else doc[:j] + li + doc[j:]


_sb_en_hp = HELP_PAGE.find('<div lang="en">')
if _sb_en_hp > 0:
    HELP_PAGE = _help_sb(HELP_PAGE[:_sb_en_hp], "de") + _help_sb(HELP_PAGE[_sb_en_hp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_sb(HELP_X[_L], _L)


# ---- self-test (only for --self-test) ----------------------------------------------------------------------------------------------
def startbilder_selftest():
    from PIL import Image
    import tempfile as _tf
    global DATA_DIR
    old, c0 = DATA_DIR, {k: CFG.get(k) for k in ("hp_start_on", "hp_start_variant", "hp_funk_on", "hp_sim_on", "hp_info_on")}
    d = _tf.mkdtemp(prefix="mw_sb_")
    try:
        DATA_DIR = d
        CFG.update(hp_start_on=True, hp_start_variant="B", hp_funk_on=False, hp_sim_on=False, hp_info_on=False)
        b = io.BytesIO(); ex = Image.Exif(); ex[0x010F] = "TestCam"; ex[0x8825] = {1: "N", 2: (47.0, 3.0, 0.0)}
        Image.new("RGB", (2400, 1800), (40, 120, 60)).save(b, "JPEG", exif=ex.tobytes()); raw = b.getvalue()
        assert b"TestCam" in raw
        assert [(it["path"], it["sha"]) for it in hp_fixed_items()] == [(it["path"], it["sha"]) for it in _hp_fixed_items_639zzzzf()] == [
            ("index.html", hashlib.sha256(hp_index_html().encode("utf-8")).hexdigest())], "without pictures: simple page"
        sb_set("titel", raw, 82, 70)
        data = open(os.path.join(sb_dir(), "titel.webp"), "rb").read(); im = Image.open(io.BytesIO(data))
        assert im.size == (1600, 1200) and b"TestCam" not in data and b"EXIF" not in data and b"Exif" not in data and not im.getexif(), "1600 px, no EXIF"
        assert len(data) <= SB_SPEC["titel"][2] and os.path.isfile(os.path.join(sb_dir(), "titel-k.webp")), "byte limit, small copy"
        nb = io.BytesIO(); Image.effect_noise((3200, 800), 60).convert("RGB").save(nb, "PNG")
        sb_set("pano", nb.getvalue())
        assert os.path.getsize(os.path.join(sb_dir(), "pano.webp")) <= 400000 and sb_meta()["slots"]["pano"]["w"] <= 2600, "panorama at most 400 KB"
        lb = io.BytesIO(); Image.new("RGB", (1200, 900), (10, 60, 160)).save(lb, "JPEG"); sb_set("leiste3", lb.getvalue())
        assert sb_meta()["slots"]["leiste3"]["h"] == 360, "strip: 360 px high"
        for bad, slot in ((b"no picture", "titel"), (raw, "nix")):
            try:
                sb_set(slot, bad); raise AssertionError("bad picture accepted")
            except ValueError:
                pass
        sm = io.BytesIO(); Image.new("RGB", (500, 400)).save(sm, "JPEG")
        try:
            sb_set("titel", sm.getvalue()); raise AssertionError("too small accepted")
        except ValueError as e:
            assert "{n}" in str(e)
        sb_texts("titel", {"line": "Mein <b>Lager</b>", "nix": "x"}); sb_focus("titel", 150, -3)
        m = sb_meta()
        assert m["texts"]["titel"] == {"line": "Mein bLager/b"} and (m["slots"]["titel"]["fx"], m["slots"]["titel"]["fy"]) == (100.0, 0.0)
        items = hp_fixed_items(); paths = [it["path"] for it in items]
        assert paths[0] == "index.html" and any(p.startswith("Startbilder/titel-") for p in paths) and any(p.startswith("Startbilder/pano-k-") for p in paths)
        assert all(_HP_NAME_RE.match(p.rsplit("/", 1)[-1]) for p in paths) and all(hp_part(p) == "start" and _hp_ours(p) for p in paths)
        h = items[0]["get"]().read().decode("utf-8")
        assert 'href="Funk/"' in h and 'href="Sim/"' in h and "📡 Handy-Funkgerät" in h and "Mein bLager/b" in h and 'class="strip"' in h
        assert [h.index('href="%s"' % x) for x in ("demo/", "Sim/?grossvater=1", "Funk/", "Sim/")] == sorted(h.index('href="%s"' % x) for x in ("demo/", "Sim/?grossvater=1", "Funk/", "Sim/")), "4.19.1: MoveEye · Karte · Funk · Sim"
        assert "📷 MoveEye" in h and "🗺️ Die Karte des Grossvaters" in h and '"btn.g": "🗺️ La carte du grand-père"' in h, "4.19.1: the links of HP_LINKS in 5 languages"
        assert 'class="mweye"' in h and "mwe-blink" in h and "prefers-reduced-motion" in h, "4.19.1: animated eye at the title"
        assert not re.search(r'(?:src|href|srcset)="(?:https?:)?//', h) and "@import" not in h and "fonts.g" not in h, "no external resources"
        assert h.index('href="Funk/"') < h.index('id="sc"'), "the buttons right under the title picture"
        assert '"titel.line"' not in h.split("var T=", 1)[1].split(",l=", 1)[0], "own text: in every language"
        CFG["hp_start_variant"] = "A"
        pa = [it["path"] for it in hp_fixed_items()]
        assert not any("pano" in p or "leiste" in p for p in pa) and any("titel" in p for p in pa), "A: only the pictures of A"
        sb_reset("titel")
        ha = hp_fixed_items()[0]["get"]().read()
        assert ha == hp_index_html().encode("utf-8"), "A without own pictures: simple page"
        CFG["hp_start_variant"] = "B"
        hb = hp_fixed_items()[0]["get"]().read().decode()
        assert "<svg" in hb and 'data-a="alt.drawn"' in hb, "B without title picture: drawn placeholder"
        CFG["hp_start_on"] = False
        assert not any(it["path"].startswith("Startbilder/") or it["path"] == "index.html" for it in hp_fixed_items()), "start page off: nothing"
        for k in SB_SLOTS:
            sb_reset(k)
        assert not sb_meta()["slots"] and not [f for f in os.listdir(sb_dir()) if f.endswith(".webp")], "removed"
        assert all(DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")) for k in _HX_SB), "texts in 5 languages"
        assert all(len(v) == 5 and all(v) for v in SB_TX.values()), "page texts in 5 languages"
        assert DEFAULTS.get("hp_start_variant") == "B" and "hp_start_variant" in USER_SETTINGS_DENY and "/api/startbilder" in APPKEY_DENY_PATHS
        assert not HP_PAGE or ('id="hp-sbild" href="/startbilder"' in HP_PAGE and 'id="hp-sb-var"' in HP_PAGE), "entry in the card Homepage"
    finally:
        DATA_DIR = old
        CFG.update(c0)
        shutil.rmtree(d, ignore_errors=True)
    return True


SELFTEST_EXTRA.append(("Start page: own pictures (A / B, focus, without EXIF, Startbilder/ on the web space) (639zzzzf)", startbilder_selftest))
