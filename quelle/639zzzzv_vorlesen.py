#@ MoveEye – Teil 639zzzzv: «📖 Vorlesen» und «👁 Datei-Ansicht» im Digitalen Rucksack – Geschichten (.txt, .md, .epub, .docx, .pdf) mit der Piper-Stimme vorlesen, im Browser oder auf dem Lautsprecher, Lesezeichen pro Person, 📖 im Kopf, Pause bei Alarm; dazu eine Ansicht für fast jede Datei (Text, E-Book, Word, PDF-Seiten, Bilder, Tabellen, JSON, Code). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026, freigegeben): «Dateien im digitalen Rucksack vorlesen lassen – Geschichten für den Abend
# herunterladen und von meiner KI-Stimme vorlesen lassen» + «allgemein eine Art Datei-Ansicht».
# Entscheide: eigene Seite /vorlesen · Radio und Vorlesen schliessen sich aus (startet das eine, stoppt das andere) · Lesezeichen
# pro Person und Datei, auf dem Gerät · PDF-Seiten als Bilder vom MoveEye (pdftoppm), fehlt poppler-utils: Installation per Tipp
# (nur der Administrator, wie Samba) · Stimme nach der Sprache des Buchs (epub-Feld / Text), wenn deren Piper-Stimme geladen ist,
# sonst die Sprache der Oberfläche mit Hinweis · Pause bei jedem Alarm, auch auf dem Handy · Tipp auf .txt / .md öffnet die
# Lese-Ansicht mit «✎ Bearbeiten» · .xlsx / .odt / .pptx nur Info-Karte · kein Einschlaf-Timer · Almanach bleibt (Ideenliste).
#
#  Text      vl_book(m): .txt / .md (Kapitel an «Kapitel 3», «Chapter», «# …»), .epub (Reihenfolge aus spine, Titel aus dem
#            Inhaltsverzeichnis nav / ncx), .docx (word/document.xml, Überschrift 1/2 = Kapitel), .pdf (pdftotext, Absätze nach
#            Zeilenlänge, sonst je Seite ein Abschnitt). Nur Standardbibliothek; Grenzen gegen Zip-Bomben (Teil 8 MB, zusammen
#            40 MB, keine <!ENTITY), höchstens VL_MAX_CHARS Zeichen. Sätze für die Stimme (lange an , ; : geteilt).
#            Zwischenspeicher <Rucksack>/vl/<id>.json (Grösse + Zeit + Version der Datei); wird die Datei gelöscht, geht er mit
#            (auch Seitenbilder und Ton dieser Datei).
#  Stimme    vl_synth: Piper (639zzb piper_synth) der Buchsprache, sonst der Oberfläche, sonst die alte Stimme. Ton pro Satz
#            <Rucksack>/vl/ton/<id>_<schlüssel>.wav (höchstens VL_TON_MB), ein Arbeiter rechnet die nächsten Sätze voraus.
#  Browser   /api/vorlesen/audio?id&c&s → WAV eines Satzes (Tempo im Browser: playbackRate, gleicher Ton für jedes Tempo). Der
#            Spieler (window.mwReadP) läuft wie das Radio im Hauptfenster (mwRadioHost-Muster: window.top gleicher Herkunft),
#            spielt also über andere Seiten weiter; 639zzzzx (Fenster) behandelt /vorlesen wie /radio. 📖 im Kopf jeder Seite.
#            Alle 2 s fragt er /api/vorlesen?on=1: Alarm / Sirene / Ansage / Wecker / Morse → Pause, danach der Satz nochmals.
#  Lautsprecher  ein Faden wie das Radio: Satz für Satz über out_cmd (250), Lautstärke vl_volume; radio_yield (gewickelt) und
#            vl_held() = radio_held() + eigene Pause + Alarm der letzten VL_ALARM_S s: die anderen Töne gehen vor.
#  Lesezeichen  <Rucksack>/vl/lesezeichen.json {person: {datei: [kapitel, satz, zeit, prozent]}}, höchstens 300 pro Person.
#  Rechte    lesen / ansehen = herunterladen dürfen (tausch_can_down), Lautsprecher = Recht «Sirene» (wie das Radio); Gäste nichts Neues.
#  Ansicht   /api/tausch/ansicht?id → Text / Tabelle / JSON / Code / Buch / Info; /tausch/seite/<id>/<n>.jpg = PDF-Seite als Bild
#            (neu gerechnet, wie die Vorschaubilder). Die Seite rendert nur mit textContent (Markdown: das sichere tzMd von 639zzc).
# Test: werkzeuge/vorlesen_test.py (Text aus allen Arten, Grenzen, Rechte, Lesezeichen, Lautsprecher mit falscher Stimme und
# falschem aplay, Vorrang Sirene / Alarm, Radio-Ausschluss, Seiten im Browser).
# ----------------------------------------------------------------------------
import html as _vl_html
import html.parser as _vl_hp
import posixpath as _vl_pp
import zipfile as _vl_zip
import xml.etree.ElementTree as _vl_et

for _k, _v in {"vl_volume": 60}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
VL_READ_EXT = ("txt", "md", "epub", "docx", "pdf")
VL_CODE_EXT = {"json", "log", "yaml", "yml", "ini", "toml", "cfg", "conf", "c", "h", "cpp", "hpp", "cc", "java", "kt", "swift", "go", "rs",
               "css", "scss", "sql", "tex", "gpx", "kml", "geojson", "srt", "vtt", "diff", "patch", "properties", "env", "tsv"}
VL_MAX_CHARS = 1_500_000
VL_ZIP_PART, VL_ZIP_ALL = 8 * 1024 * 1024, 40 * 1024 * 1024
VL_VIEW_MAX = 2 * 1024 * 1024                              # text for the viewer
VL_PDF_PAGES = 300
VL_TON_MB, VL_TON_N = 150, 4000
VL_ALARM_S = 20.0                                          # an alarm pauses the reading this long
VL_GAP_S = 2.0                                             # after another sound: this long quiet, then the sentence again
VL_SPEEDS = (0.8, 0.9, 1.0, 1.15, 1.3)
TZ_TYPES.setdefault("epub", ("application/epub+zip", "doc"))
for _e in VL_CODE_EXT:
    TZ_TYPES.setdefault(_e, ("text/plain", "doc"))
TZ_TYPES["json"] = ("application/json", "doc")
for _p in TZ_PERMS:                                        # the page and its API: whoever sees files (the routes check the file)
    PERM_GET[_p] = tuple(PERM_GET.get(_p, ())) + ("/vorlesen", "/api/vorlesen")
    PERM_POST[_p] = set(PERM_POST.get(_p, ())) | {"/api/vorlesen"}
VL = {"lock": threading.RLock(), "gen": 0, "want": False, "id": "", "name": "", "who": "", "key": "", "c": 0, "s": 0, "state": "off", "msg": "",
      "pause": False, "held": "", "hold_t": 0.0, "hold_why": "", "alarm_t": 0.0, "speed": 1.0, "lang": "", "out": None, "olock": threading.Lock(),
      "t0": 0.0, "radio_t": 0.0, "bm": None, "bm_t": 0.0, "q": deque(), "qrun": False, "prune_t": 0.0, "inst": "", "synth": None, "pdf": {}, "books": {}}
_VL_KAP = re.compile(r"^\s*(kapitel|chapter|chapitre|capitolo|chapitel|teil|part|buch|book)\s+[\w.]{1,8}\b.{0,80}$|^\s*#{1,3}\s+\S.{0,80}$", re.I)
_VL_SATZ = re.compile(r"([.!?…][»«\"'”’)]*)\s+(?=[«»\"'„“‚(\-–A-ZÄÖÜÀ-ÝÉÈ0-9])")
_VL_ABK = re.compile(r"\b(z\.\s?B|d\.\s?h|u\.\s?a|bzw|ca|Nr|Dr|Prof|St|usw|etc|vgl|evtl|ggf|Hr|Fr|Mr|Mrs|Ms|M|Mme|Sig|ecc)\.")
_VL_STOP = {"de": "der die und das ist nicht ein eine ich sie er es mit auf den dem zu sich auch wie", "fr": "le la les et est des une un pas que qui dans pour il elle sur au",
            "it": "il la che di non una per sono è con del della gli le lo si ma", "en": "the and is of to you that it was he she with for on as at his her",
            "rm": "il la e da per cun ina in betg ch'el ils las è sco era dal"}


# ---- text out of the files ------------------------------------------------------------------------------------------------------
def vl_saetze(p):
    """a paragraph -> its sentences (abbreviations kept together; very long ones split at , ; : for a quick first sound)"""
    p = re.sub(r"\s+", " ", str(p or "")).strip()
    if not p:
        return []
    p2 = _VL_ABK.sub(lambda m: m.group(0).replace(".", "\x00"), p)
    res = []
    for s in (x.replace("\x00", ".").strip() for x in _VL_SATZ.sub(lambda m: m.group(1) + "\x01", p2).split("\x01")):
        while len(s) > 280:
            k = max(s.rfind(c, 0, 240) for c in ",;:–")
            if k < 60:
                k = s.rfind(" ", 0, 240)
            if k < 20:
                k = 240
            res.append(s[:k + 1].strip()); s = s[k + 1:].strip()
        if s:
            res.append(s)
    return res


def vl_decode(b):
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16", "replace")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", "replace")


def vl_from_text(text, md=False):
    """[{t, p: [paragraph]}] from plain text / Markdown"""
    kap, cur = [], {"t": "", "p": []}
    for a in re.split(r"\n\s*\n", str(text).replace("\r\n", "\n").replace("\r", "\n")):
        a = a.strip("\n")
        if not a.strip():
            continue
        first = a.strip().split("\n", 1)[0].strip()
        if _VL_KAP.match(first):
            if cur["p"] or cur["t"]:
                kap.append(cur)
            cur = {"t": re.sub(r"^#+\s*|[*_`]+", "", first).strip(), "p": []}
            a = a.strip().split("\n", 1)[1] if "\n" in a.strip() else ""
            if not a.strip():
                continue
        if md:
            if re.match(r"^\s*(```|~~~|\|)", a):           # code / tables: not read aloud
                continue
            a = re.sub(r"^\s{0,3}(>\s?|[-*+]\s+|\d+[.)]\s+|#{4,6}\s+)", "", a, flags=re.M)
            a = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", a); a = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", a); a = re.sub(r"[*_`]{1,3}", "", a)
        a = re.sub(r"\s*\n\s*", " ", a).strip()
        if a:
            cur["p"].append(a)
    if cur["p"] or cur["t"]:
        kap.append(cur)
    return kap


class _VlHtml(_vl_hp.HTMLParser):
    BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "tr", "blockquote", "section", "dd", "dt", "pre", "hr"}
    SKIP = {"script", "style", "head", "title", "svg", "math", "noscript", "rt", "rp"}

    def __init__(self):
        super().__init__(convert_charrefs=True); self.out, self.buf, self.skip, self.head = [], [], 0, ""

    def handle_starttag(self, tag, a):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.flush()

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            t = self.flush()
            if tag in ("h1", "h2", "h3") and t and not self.head and len(self.out) == 1:
                self.head = self.out.pop()

    def handle_data(self, d):
        if not self.skip:
            self.buf.append(d)

    def flush(self):
        t = re.sub(r"\s+", " ", "".join(self.buf)).strip(); self.buf = []
        if t:
            self.out.append(t)
        return t


class _VlZip:
    """reads parts of a zip with limits (zip bomb): one part VL_ZIP_PART, all together VL_ZIP_ALL, no entity declarations"""
    def __init__(self, path):
        self.z = _vl_zip.ZipFile(path); self.n = 0

    def read(self, name, xml=True):
        i = self.z.getinfo(name)
        if i.file_size > VL_ZIP_PART or self.n + i.file_size > VL_ZIP_ALL:
            raise ValueError("too big")
        b = self.z.read(i); self.n += len(b)
        if len(b) > i.file_size:
            raise ValueError("too big")
        if xml and b"<!ENTITY" in b[:4096].upper():
            raise ValueError("entity")
        return b


def _vl_tag(e):
    return e.tag.rsplit("}", 1)[-1]


def vl_from_epub(path):
    """(title, lang, [{t, p}]) of an e-book (EPUB 2 / 3)"""
    z = _VlZip(path)
    c = _vl_et.fromstring(z.read("META-INF/container.xml"))
    opf = next((e.get("full-path") for e in c.iter() if _vl_tag(e) == "rootfile" and e.get("full-path")), "")
    base = _vl_pp.dirname(opf)
    o = _vl_et.fromstring(z.read(opf))
    man = {e.get("id"): e for e in o.iter() if _vl_tag(e) == "item"}
    meta = {_vl_tag(e): (e.text or "").strip() for e in o.iter() if _vl_tag(e) in ("title", "language") and (e.text or "").strip()}
    spine = [e.get("idref") for e in o.iter() if _vl_tag(e) == "itemref"][:2000]
    toc = {}
    for it in man.values():                                  # titles: EPUB 3 nav or EPUB 2 ncx
        props, mt = (it.get("properties") or "").split(), it.get("media-type") or ""
        if "nav" not in props and mt != "application/x-dtbncx+xml":
            continue
        p_ = _vl_pp.normpath(_vl_pp.join(base, it.get("href") or ""))
        try:
            raw = z.read(p_).decode("utf-8", "replace")
        except (KeyError, ValueError):
            continue
        if mt == "application/x-dtbncx+xml":
            for m_ in re.finditer(r"<navLabel>\s*<text>(.*?)</text>.*?<content[^>]*src=\"([^\"#]+)", raw, re.S):
                toc.setdefault(_vl_pp.normpath(_vl_pp.join(_vl_pp.dirname(p_), m_.group(2))), _vl_html.unescape(re.sub(r"\s+", " ", m_.group(1))).strip())
        else:
            for m_ in re.finditer(r"<a[^>]*href=\"([^\"#]+)[^\"]*\"[^>]*>(.*?)</a>", raw, re.S):
                toc.setdefault(_vl_pp.normpath(_vl_pp.join(_vl_pp.dirname(p_), m_.group(1))),
                               _vl_html.unescape(re.sub(r"<[^>]+>|\s+", " ", m_.group(2))).strip())
    kap, n = [], 0
    for rid in spine:
        it = man.get(rid)
        if it is None or "html" not in (it.get("media-type") or "") or "nav" in (it.get("properties") or "").split():
            continue
        p_ = _vl_pp.normpath(_vl_pp.join(base, it.get("href") or ""))
        try:
            h = _VlHtml(); h.feed(z.read(p_, xml=False).decode("utf-8", "replace")); h.flush()
        except (KeyError, ValueError):
            continue
        if h.out:
            kap.append({"t": (toc.get(p_) or h.head or "")[:120], "p": h.out}); n += sum(len(x) for x in h.out)
            if n > VL_MAX_CHARS:
                break
    return meta.get("title", "")[:160], meta.get("language", "")[:2].lower(), kap


def vl_from_docx(path):
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    d = _vl_et.fromstring(_VlZip(path).read("word/document.xml"))
    kap, cur, n = [], {"t": "", "p": []}, 0
    for p in d.iter(W + "p"):
        st = p.find(f"{W}pPr/{W}pStyle")
        s = (st.get(W + "val") if st is not None else "") or ""
        t = "".join((x.text or "") if x.tag == W + "t" else "\t" if x.tag == W + "tab" else " " for x in p.iter() if x.tag in (W + "t", W + "tab", W + "br")).strip()
        if not t:
            continue
        n += len(t)
        if n > VL_MAX_CHARS:
            break
        if re.match(r"(?i)^(heading|berschrift|titre|titolo|title|titel)\s*[12]?$", re.sub(r"^.*?(heading|berschrift|titre|titolo|title|titel)", r"\1", s)) and len(t) < 120:
            if cur["p"] or cur["t"]:
                kap.append(cur)
            cur = {"t": t, "p": []}
        else:
            cur["p"].append(t)
    if cur["p"] or cur["t"]:
        kap.append(cur)
    return kap


def _vl_pdf_absatz(s):
    """pdftotext knows no paragraphs: a short line (heading / end of a paragraph) ends one; hyphen at the line end joined"""
    ln = s.split("\n")
    lens = sorted(len(x.rstrip()) for x in ln if x.strip())
    med = lens[len(lens) * 3 // 4] if lens else 0
    out = []
    for x in ln:
        out.append(x)
        if x.strip() and len(x.rstrip()) < med * 0.8:
            out.append("")
    return re.sub(r"(\w)-\n(\w)", r"\1\2", "\n".join(out))


def vl_tool(name):
    return shutil.which(name) or ""


def vl_from_pdf(path):
    exe = vl_tool("pdftotext")
    if not exe:
        raise LookupError("pdftotext is missing (poppler-utils)")
    r = subprocess.run([exe, "-enc", "UTF-8", "-eol", "unix", path, "-"], capture_output=True, timeout=90)
    if r.returncode != 0:
        raise ValueError("the PDF cannot be read")
    pages = [_vl_pdf_absatz(x) for x in r.stdout[:VL_MAX_CHARS * 2].decode("utf-8", "replace").split("\f")]
    kap = vl_from_text("\n\n".join(pages))
    if len(kap) <= 1:
        kap = [{"t": "", "p": [re.sub(r"\s*\n\s*", " ", a).strip() for a in re.split(r"\n\s*\n", s) if a.strip()], "pg": i}
               for i, s in enumerate(pages, 1) if s.strip()]
    return kap


def vl_lang_guess(text, default=""):
    words = re.findall(r"[a-zàâäçéèêëîïôöùûüß']+", str(text)[:6000].lower())
    best, n = default, 4
    for L, sw in _VL_STOP.items():
        s = set(sw.split())
        k = sum(1 for w in words if w in s)
        if k > n:
            best, n = L, k
    return best


def vl_root():
    r = _tz_load()
    if r is None:
        return None
    d = os.path.join(r, "vl")
    os.makedirs(os.path.join(d, "ton"), exist_ok=True)
    return d


def vl_sig(m):
    return f"{m.get('size')}|{m.get('t')}|{m.get('ver', 1)}|{m.get('ed_t', '')}|3"


def vl_book(m):
    """the book of a backpack file: {title, lang, ch: [{t, p: [[sentence]]}], n: [sentences per chapter], total} (cached)"""
    d = vl_root()
    if d is None:
        raise LookupError("the storage (USB stick / SSD) is not there")
    cp = os.path.join(d, m["id"] + ".json")
    sig = vl_sig(m)
    mem = VL["books"].get(m["id"])
    if mem and mem["sig"] == sig:
        return mem
    try:
        with open(cp, encoding="utf-8") as f:
            b = json.load(f)
        if b.get("sig") == sig:
            return _vl_keep(m["id"], b)
    except (OSError, ValueError):
        pass
    vl_prune()
    src = os.path.join(TZ["root"], "f", m["id"] + ".bin")
    e = tausch_ext(m["name"])
    title, lang = "", ""
    if e in ("txt", "md"):
        with open(src, "rb") as f:
            kap = vl_from_text(vl_decode(f.read(VL_MAX_CHARS * 3))[:VL_MAX_CHARS], md=e == "md")
    elif e == "epub":
        title, lang, kap = vl_from_epub(src)
    elif e == "docx":
        kap = vl_from_docx(src)
    elif e == "pdf":
        kap = vl_from_pdf(src)
    else:
        raise ValueError("this kind of file cannot be read aloud")
    kap = [k for k in kap if k["p"] or k["t"]]
    if len(kap) > 1 and not kap[0]["t"] and len(kap[0]["p"]) == 1 and len(kap[0]["p"][0]) < 90:   # a first line alone = the title
        title = title or kap[0]["p"][0]; kap = kap[1:]
    ch, total = [], 0
    for i, k in enumerate(kap):
        ps = [s for s in (vl_saetze(p) for p in k["p"]) if s]
        if not ps:
            continue
        t = k["t"] or (("p. %d" % k["pg"]) if k.get("pg") else "")
        ch.append({"t": t[:120], "p": ps}); total += sum(len(x) for x in ps)
    if not total:
        raise ValueError("no text found (a scanned PDF? pictures are not read)")
    allt = " ".join(x for c in ch[:3] for p in c["p"][:8] for x in p)
    b = {"sig": sig, "title": (title or os.path.splitext(m["name"])[0].replace("_", " "))[:160], "lang": norm_lang(lang) if lang in LANGS else vl_lang_guess(allt),
         "ch": ch, "n": [sum(len(x) for x in c["p"]) for c in ch], "total": total}
    try:
        tmp = cp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(b, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, cp)
    except OSError:
        pass
    return _vl_keep(m["id"], b)


def _vl_keep(fid, b):
    """the last few books in memory (the reader asks for sentences and bookmarks often)"""
    with VL["lock"]:
        VL["books"].pop(fid, None); VL["books"][fid] = b
        while len(VL["books"]) > 3:
            VL["books"].pop(next(iter(VL["books"])))
    return b


def vl_sentence(b, c, s):
    """the text of sentence s (counted through the chapter) and whether it ends a paragraph"""
    for p in b["ch"][c]["p"]:
        if s < len(p):
            return p[s], s == len(p) - 1
        s -= len(p)
    return "", True


def vl_prune(force=False):
    """caches of files that are gone (text, page pictures, sound): away - at most every 10 min."""
    now = time.time()
    if not force and now - VL["prune_t"] < 600:
        return
    VL["prune_t"] = now
    d = vl_root()
    if d is None:
        return
    with TZ["lock"]:
        have = set(TZ["files"] or {})
    for sub in ("", "ton"):
        p_ = os.path.join(d, sub)
        try:
            names = os.listdir(p_)
        except OSError:
            continue
        for nm in names:
            fid = nm[:16]
            if TZ_ID.match(fid) and fid not in have:
                try:
                    os.remove(os.path.join(p_, nm))
                except OSError:
                    pass


def vl_forget(fid):
    VL["books"].pop(fid, None)
    d = vl_root()
    if d is None or not TZ_ID.match(str(fid or "")):
        return
    for sub in ("", "ton"):
        try:
            for nm in os.listdir(os.path.join(d, sub)):
                if nm.startswith(fid):
                    os.remove(os.path.join(d, sub, nm))
        except OSError:
            pass


_tausch_delete_vl = tausch_delete


# wraps: tausch_delete
def tausch_delete(who, fid, lang=None):                     # + 639zzzzv: the text, page pictures and sound of the file go with it
    r = _tausch_delete_vl(who, fid, lang)
    if tausch_file(fid) is None:
        vl_forget(fid)
        if VL["id"] == fid:
            vl_stop("file deleted")
    return r


# ---- PDF pages as pictures ------------------------------------------------------------------------------------------------------
def vl_pdf_pages(m):
    k = (m["id"], vl_sig(m))
    if k in VL["pdf"]:
        return VL["pdf"][k]
    n = 0
    exe = vl_tool("pdfinfo")
    src = os.path.join(TZ["root"], "f", m["id"] + ".bin")
    try:
        if exe:
            r = subprocess.run([exe, src], capture_output=True, timeout=20)
            mm = re.search(rb"^Pages:\s+(\d+)", r.stdout, re.M)
            n = int(mm.group(1)) if mm else 0
        if not n:
            with open(src, "rb") as f:
                n = len(re.findall(rb"/Type\s*/Page[^s]", f.read(60 * TZ_MB)))
    except (OSError, subprocess.SubprocessError, ValueError):
        n = 0
    VL["pdf"][k] = n
    return n


def vl_pdf_page(m, n):
    """path of page n (1 ..) as a JPEG, computed anew (no bytes of the PDF go to the browser)"""
    d = vl_root()
    exe = vl_tool("pdftoppm")
    if d is None or not exe or not 1 <= n <= VL_PDF_PAGES or m["size"] > 200 * TZ_MB:
        return ""
    p_ = os.path.join(d, f"{m['id']}_p{n}.jpg")
    if os.path.isfile(p_) and os.path.getmtime(p_) >= float(m.get("ed_t") or m.get("t") or 0):
        return p_
    tmpd = tempfile.mkdtemp(prefix="mw_vl_")
    try:
        r = subprocess.run([exe, "-f", str(n), "-l", str(n), "-scale-to", "1400", "-jpeg", "-singlefile",
                            os.path.join(TZ["root"], "f", m["id"] + ".bin"), os.path.join(tmpd, "s")], capture_output=True, timeout=40)
        img = cv2.imread(os.path.join(tmpd, "s.jpg"), cv2.IMREAD_COLOR) if r.returncode == 0 else None
        if img is None or not _tz_jpg_write(img, p_, 1400, 82):
            return ""
        return p_
    except (OSError, subprocess.SubprocessError):
        return ""
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)


def vl_poppler_install():
    """poppler-utils (pdftotext, pdftoppm, pdfinfo) once with apt - as root or «sudo -n», like espeak-ng (639zzb) / Samba"""
    if VL["inst"] == "running":
        return False, "already running"
    apt = shutil.which("apt-get")
    if not apt:
        return False, "no apt-get on this system - install poppler-utils by hand"
    VL["inst"] = "running"

    def work():
        pre = [] if _is_root() else ["sudo", "-n"]
        env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", APT_LISTCHANGES_FRONTEND="none")
        out, rc = "", -1
        for args in (["install", "-y", "--no-install-recommends", "poppler-utils"], ["update"], ["install", "-y", "--no-install-recommends", "poppler-utils"]):
            if args[0] == "update" and (rc == 0 or not re.search(r"Unable to locate|no installation candidate|Failed to fetch", out)):
                continue
            try:
                r = subprocess.run(pre + [apt] + args, capture_output=True, text=True, timeout=600, env=env, stdin=subprocess.DEVNULL)
                rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
            except (OSError, subprocess.SubprocessError) as e:
                rc, out = -1, str(e)
        ok = bool(vl_tool("pdftoppm") and vl_tool("pdftotext"))
        low = out.lower()
        VL["inst"] = "done" if ok else ("MoveEye has no rights for apt (sudo asks for a password) - in a terminal: sudo apt install poppler-utils"
                                        if "password is required" in low or "terminal is required" in low else
                                        "apt is busy right now (another installation or update) - try again in a few minutes"
                                        if "lock" in low else "no internet for apt - try again with internet" if "resolv" in low or "fetch" in low else
                                        (out.strip().splitlines() or ["?"])[-1][:120])
        log_event("sys", "Read aloud: poppler-utils " + ("installed" if ok else "not installed: " + VL["inst"])[:140])
    threading.Thread(target=work, daemon=True, name="vl-poppler").start()
    return True, ""


# ---- the viewer: what a file looks like ----------------------------------------------------------------------------------------
def vl_view(m, lang=None):
    """{type, …} for /api/tausch/ansicht"""
    e = tausch_ext(m["name"])
    src = os.path.join(TZ["root"], "f", m["id"] + ".bin")
    mime, kind, risky = tausch_type(m["name"])
    if risky:
        return {"type": "info", "risky": True}
    if e in ("txt", "md", "csv", "tsv") or e in VL_CODE_EXT:
        with open(src, "rb") as f:
            raw = f.read(VL_VIEW_MAX + 1)
        if b"\x00" in raw[:8192]:
            return {"type": "info", "binary": True}
        t = vl_decode(raw[:VL_VIEW_MAX])
        typ = "text" if e in ("txt", "md") else "table" if e in ("csv", "tsv") else "json" if e in ("json", "geojson") else "code"
        return {"type": typ, "text": t, "md": e == "md", "cut": len(raw) > VL_VIEW_MAX, "ext": e}
    if e in ("epub", "docx", "pdf"):
        out = {"type": "book", "ext": e, "tool": bool(vl_tool("pdftoppm")) if e == "pdf" else True}
        if e == "pdf":
            out["pages"] = min(vl_pdf_pages(m), VL_PDF_PAGES) if out["tool"] else 0
        try:
            b = vl_book(m)
            out.update(title=b["title"], lang=b["lang"], ch=[{"t": c["t"], "p": [" ".join(p) for p in c["p"]]} for c in b["ch"]], total=b["total"])
        except LookupError as x:
            out.update(error=tr_err(str(x), lang), need="poppler" if "pdftotext" in str(x) else "")
        except (ValueError, KeyError, OSError, _vl_zip.BadZipFile, _vl_et.ParseError, subprocess.SubprocessError, StopIteration):
            out["error"] = tr("This file cannot be read (damaged or protected).", lang)
        return out
    if kind == "image":
        return {"type": "image"}
    return {"type": "info"}


# ---- voice and sound -------------------------------------------------------------------------------------------------------------
def vl_voice(book_lang, ui_lang):
    """(language to speak, hint): the language of the book if its Piper voice is ready, else the language of the page"""
    bl, ul = norm_lang(book_lang or ui_lang), norm_lang(ui_lang)
    if VL["synth"] is not None:
        return bl, ""
    if piper_ready(bl):
        return bl, ""
    if bl != ul and piper_ready(ul):
        return ul, "No Piper voice loaded for the language of the book - read with the voice of the page."
    return bl, "No Piper voice loaded - the old voice reads (Settings › Light & sound › Loudspeaker)."


def vl_synth(text, lang, speed, out):
    """(ok, error): one sentence into the WAV file out"""
    f = VL["synth"]
    if f is not None:                                        # tests: a made-up voice
        return f(text, lang, speed, out)
    vid = piper_voice_for(lang)
    if vid and piper_ready(lang):
        ok, err, _i = piper_synth(text, vid, out, speed)
        if ok:
            return True, ""
    return _tts_make_639zzb(text, lang, out)


def vl_ton(m, b, c, s, lang, speed=1.0):
    """path of the sound of a sentence (computed once)"""
    d = vl_root()
    text, _end = vl_sentence(b, c, s)
    if d is None or not text:
        return "", "unknown sentence"
    k = hashlib.sha256(f"{lang}|{piper_voice_for(lang)}|{float(speed):.2f}|{text}".encode("utf-8")).hexdigest()[:20]
    p_ = os.path.join(d, "ton", f"{m['id']}_{k}.wav")
    if os.path.isfile(p_) and os.path.getsize(p_) > 100:
        return p_, ""
    tmp = p_ + f".{threading.get_ident()}.tmp.wav"
    try:
        ok, err = vl_synth(re.sub(r"[\x00-\x1f]", " ", text), lang, speed, tmp)
        if not ok or not os.path.isfile(tmp) or os.path.getsize(tmp) <= 100:
            return "", err or "no voice"
        os.replace(tmp, p_)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    vl_ton_trim(d)
    return p_, ""


def vl_ton_trim(d):
    try:
        fs = [(e.stat().st_mtime, e.stat().st_size, e.path) for e in os.scandir(os.path.join(d, "ton")) if e.name.endswith(".wav")]
    except OSError:
        return
    tot = sum(x[1] for x in fs)
    if len(fs) <= VL_TON_N and tot <= VL_TON_MB * TZ_MB:
        return
    for _t, sz, p_ in sorted(fs)[:max(len(fs) - VL_TON_N, len(fs) // 5)]:
        try:
            os.remove(p_); tot -= sz
        except OSError:
            pass


def vl_next(b, c, s, n=1):
    """the position n sentences later (None at the end)"""
    s += n
    while c < len(b["n"]) and s >= b["n"][c]:
        s -= b["n"][c]; c += 1
    return (c, s) if c < len(b["n"]) else None


def vl_ahead(m, b, c, s, lang, speed=1.0, n=2):
    """compute the next sentences in the background (one worker, a short queue)"""
    for i in range(1, n + 1):
        nx = vl_next(b, c, s, i)
        if nx is None:
            break
        with VL["lock"]:
            job = (m["id"], nx[0], nx[1], lang, speed)
            if job in VL["q"]:
                continue
            VL["q"].append(job)
            while len(VL["q"]) > 6:
                VL["q"].popleft()
    with VL["lock"]:
        if VL["qrun"]:
            return
        VL["qrun"] = True

    def work():
        try:
            while True:
                with VL["lock"]:
                    if not VL["q"]:
                        VL["qrun"] = False
                        return
                    fid, c_, s_, L_, sp = VL["q"].popleft()
                m_ = tausch_file(fid)
                if m_ is not None:
                    try:
                        vl_ton(m_, vl_book(m_), c_, s_, L_, sp)
                    except Exception:
                        pass
        except Exception:
            VL["qrun"] = False
    threading.Thread(target=work, daemon=True, name="vl-ahead").start()


# ---- bookmarks (per person and file) --------------------------------------------------------------------------------------------
def vl_bms():
    if VL["bm"] is None:
        d = vl_root()
        try:
            with open(os.path.join(d, "lesezeichen.json"), encoding="utf-8") as f:
                VL["bm"] = json.load(f)
        except (OSError, ValueError, TypeError):
            VL["bm"] = {}
    return VL["bm"]


def vl_bm_save(key, fid, c, s, now=None, force=False):
    m = tausch_file(fid)
    if m is None or not key:
        return False
    try:
        b = vl_book(m)
        c, s = max(0, min(int(c), len(b["n"]) - 1)), int(s)
        s = max(0, min(s, b["n"][c] - 1))
        pct = round(100.0 * (sum(b["n"][:c]) + s) / max(1, b["total"]))
    except (LookupError, ValueError, KeyError, OSError, TypeError):
        return False
    now = time.time() if now is None else now
    with VL["lock"]:
        bm = vl_bms()
        mine = bm.setdefault(str(key), {})
        mine[fid] = [c, s, int(now), pct]
        if len(mine) > 300:
            for k in sorted(mine, key=lambda x: mine[x][2])[:len(mine) - 300]:
                mine.pop(k, None)
        if not force and now - VL["bm_t"] < 8:
            return True
        VL["bm_t"] = now
        d = vl_root()
        try:
            _tz_write_json(os.path.join(d, "lesezeichen.json"), bm)
        except (OSError, TypeError):
            return False
    return True


def vl_bm_get(key, fid):
    x = vl_bms().get(str(key), {}).get(fid)
    return {"c": x[0], "s": x[1], "t": x[2], "pct": x[3]} if x else None


def vl_bm_list(who):
    """{file: {c, pct, t}} of this person (only files that are still there and that he may read)"""
    out = {}
    for fid, x in list(vl_bms().get(who["key"], {}).items()):
        m = tausch_file(fid)
        if m is not None and tausch_can_down(m, who):
            out[fid] = {"c": x[0], "pct": x[3], "t": x[2], "name": m["name"]}
    return out


# ---- the loudspeaker: one thread, sentence by sentence --------------------------------------------------------------------------
def vl_held(now=None):
    """why the reading on the loudspeaker (and in the browser) must be quiet now ("" = it may read)"""
    now = time.time() if now is None else now
    try:
        why = radio_held(now)                                # siren, sounds, announcement, talking, Morse, microphone, wake-up alarm
    except Exception:
        why = ""
    if not why and now - VL["hold_t"] < VL_GAP_S:
        why = VL["hold_why"] if VL["hold_why"] in _VL_HELD_TXT else "sound"
    if not why and now - VL["alarm_t"] < VL_ALARM_S:
        why = "alarm"
    return why


_VL_HELD_TXT = {"siren": "Paused: the siren / an alarm sound plays", "sound": "Paused: MoveEye plays a sound", "voice": "Paused: announcement",
                "talk": "Paused: somebody talks through the loudspeaker", "morse": "Paused: Morse / radio signal is being sent",
                "mic": "Paused: the microphone receives Morse / radio signals (no feedback)", "wake": "Paused: the wake-up alarm rings",
                "alarm": "Paused: alarm - it reads on when it is quiet"}

_radio_yield_vl = radio_yield


# wraps: radio_yield (250 / 370 / 639zzz call it before they open the loudspeaker)
def radio_yield(why="sound"):                              # + 639zzzzv: the reading lets the loudspeaker go as well
    VL["hold_t"] = time.time(); VL["hold_why"] = why
    if VL["want"]:
        got = VL["olock"].acquire(timeout=0.3)
        try:
            p = VL["out"]; VL["out"] = None
        finally:
            if got:
                VL["olock"].release()
        _radio_kill(p)
    return _radio_yield_vl(why)


_push_alert_vl = push_alert


# wraps: push_alert
def push_alert(kind, text="", **extra):                    # + 639zzzzv: an alarm pauses the reading (loudspeaker and browser)
    try:
        if kind in ("person", "warm", "noise") and is_armed():
            VL["alarm_t"] = time.time()
    except Exception:
        pass
    return _push_alert_vl(kind, text, **extra)


_radio_play_vl = radio_play


# wraps: radio_play
def radio_play(sid=None, who="web", wake=False, vol=None):   # + 639zzzzv: radio and reading exclude each other
    if VL["want"]:
        vl_stop("radio")
    VL["radio_t"] = time.time()
    return _radio_play_vl(sid, who, wake, vol)


_radio_bplay_vl = radio_bplay


# wraps: radio_bplay
def radio_bplay(sid=None):                                  # + 639zzzzv: the radio in a browser: the reading on the loudspeaker stops
    if VL["want"]:
        vl_stop("radio")
    VL["radio_t"] = time.time()
    return _radio_bplay_vl(sid)


def vl_stop(why="button", quiet=False):
    with VL["lock"]:
        was = VL["want"]
        VL["want"] = False; VL["gen"] += 1
        p = VL["out"]; VL["out"] = None
    _radio_kill(p)
    if was:
        if VL["key"] and VL["id"]:
            vl_bm_save(VL["key"], VL["id"], VL["c"], VL["s"], force=True)
        VL.update(state="off", held="", pause=False)
        if not quiet:
            log_event("sys", f"Read aloud off ({why})"[:160])
    return was


def vl_pi_play(who, m, c=0, s=0, speed=1.0, lang=None):
    """read a file on the loudspeaker -> (ok, English error)"""
    if not out_selected():
        return False, "no loudspeaker selected"
    try:
        b = vl_book(m)
    except LookupError as e:
        return False, str(e)
    except Exception:
        return False, "This file cannot be read (damaged or protected)."
    vl_stop("another file", quiet=True)
    if RADIO["want"]:
        radio_stop("read aloud")
    BR["sid"] = ""
    c = max(0, min(int(c or 0), len(b["n"]) - 1)); s = max(0, min(int(s or 0), b["n"][c] - 1))
    L, _hint = vl_voice(b["lang"], lang or CFG.get("lang"))
    with VL["lock"]:
        VL["gen"] += 1; gen = VL["gen"]
        VL.update(want=True, id=m["id"], name=b["title"], who=who["name"], key=who["key"], c=c, s=s, state="starting", msg="", pause=False,
                  held="", speed=max(0.5, min(2.0, float(speed or 1.0))), lang=L, t0=time.time())
    threading.Thread(target=_vl_session, args=(gen,), daemon=True, name="vorlesen").start()
    log_event("sys", f"Read aloud: «{m['name']}» on the loudspeaker ({who['name']})"[:160])
    return True, ""


def _vl_wav(p_):
    import wave
    with wave.open(p_, "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError("wav")
        rate, ch, data = w.getframerate(), w.getnchannels(), w.readframes(w.getnframes())
    y = np.frombuffer(data, dtype="<i2")
    if ch > 1:
        y = y.reshape(-1, ch).mean(axis=1).astype("<i2")
    return rate, y


def _vl_session(gen):
    alive = lambda: VL["gen"] == gen and VL["want"]
    mine, o, rate = [], None, 0
    try:
        while alive():
            m = tausch_file(VL["id"])
            if m is None:
                VL.update(want=False, state="error", msg="unknown file"); break
            b = vl_book(m)
            c, s = VL["c"], VL["s"]
            vl_ahead(m, b, c, s, VL["lang"], VL["speed"], 1)
            p_, err = vl_ton(m, b, c, s, VL["lang"], VL["speed"])
            if not alive():
                break
            if not p_:
                VL.update(want=False, state="error", msg=err or "no voice"); break
            r_, y = _vl_wav(p_)
            vol = (max(0.0, min(100.0, float(CFG.get("vl_volume", 60)))) / 100.0) ** 2
            i, step, done = 0, max(1, r_ // 10), False
            while alive():
                why = "pause" if VL["pause"] else vl_held()
                if why:
                    VL["held"] = why; VL["state"] = "paused"
                    with VL["olock"]:
                        k_ = VL["out"]; VL["out"] = None
                    _radio_kill(k_); o = None
                    i = 0                                    # after the pause: the sentence again from its start
                    time.sleep(0.2); continue
                VL["held"] = ""; VL["state"] = "playing"
                if o is None or o.poll() is not None or rate != r_:
                    _radio_kill(o)
                    ocmd, oerr = out_cmd(r_)
                    if ocmd is None:
                        VL.update(want=False, state="error", msg=oerr); return
                    with VL["olock"]:
                        if vl_held() or not alive():
                            continue
                        o = subprocess.Popen(ocmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=_radio_pre)
                        VL["out"] = o; mine.append(o); rate = r_
                if i >= y.size:
                    done = True; break
                ch = (y[i:i + step].astype(np.float32) * vol)
                try:
                    o.stdin.write(np.clip(ch, -32768, 32767).astype("<i2").tobytes()); o.stdin.flush()
                except (BrokenPipeError, OSError, ValueError):
                    with VL["olock"]:
                        if VL["out"] is o:
                            VL["out"] = None
                    o = None; continue
                i += step
                if AUDIO is not None:
                    AUDIO.mute_until = time.time() + 2.0     # the noise alarm does not hear the reading
            if not done or not alive():
                continue
            _t, end = vl_sentence(b, c, s)
            gap = np.zeros(int(r_ * (0.55 if end else 0.22) / max(0.5, VL["speed"])), dtype="<i2")
            try:
                if o is not None:
                    o.stdin.write(gap.tobytes()); o.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                o = None
            with VL["lock"]:
                if VL["gen"] != gen or (VL["c"], VL["s"]) != (c, s):
                    continue                                 # somebody jumped meanwhile
                nx = vl_next(b, c, s)
                if nx is None:
                    VL.update(want=False, state="done", c=0, s=0)
                    vl_bm_save(VL["key"], m["id"], 0, 0, force=True)
                    break
                VL["c"], VL["s"] = nx
            vl_bm_save(VL["key"], m["id"], nx[0], nx[1])
    except Exception as e:                                   # never let the thread die silently
        VL.update(want=False, state="error", msg=str(e)[:160])
    finally:
        with VL["olock"]:
            if VL["out"] in mine:
                VL["out"] = None
        for p in mine:
            try:
                p.stdin.close()
            except Exception:
                pass
            _radio_kill(p)


# ---- state and actions (web and window) ----------------------------------------------------------------------------------------
def vl_pi_may(role, perms):
    return role == "admin" or "siren" in set(perms or ())


def vl_pi_state(lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    h = VL["held"]
    return {"on": VL["want"], "id": VL["id"], "name": VL["name"], "who": VL["who"], "c": VL["c"], "s": VL["s"], "state": VL["state"],
            "pause": VL["pause"], "held": tr(_VL_HELD_TXT[h], L) if VL["want"] and h in _VL_HELD_TXT else "",
            "msg": tr_err(VL["msg"], L) if VL["msg"] else "", "vol": int(CFG.get("vl_volume", 60)), "speed": VL["speed"],
            "spk": bool(out_selected())}


def vl_get(who, fid, lang=None, role="admin", perms=None):
    """(code, answer) for /api/vorlesen?id=: the book with sentences, the bookmark, the voice"""
    L = norm_lang(lang or CFG.get("lang"))
    m = tausch_file(fid)
    if m is None or not tausch_can_see(m, who):
        return 404, {"ok": False, "error": tr("unknown file", L)}
    if not tausch_can_down(m, who):
        return 403, {"ok": False, "error": tr("You may not download files.", L)}
    if tausch_ext(m["name"]) not in VL_READ_EXT:
        return 400, {"ok": False, "error": tr("this kind of file cannot be read aloud", L)}
    try:
        b = vl_book(m)
    except LookupError as e:
        return 400, {"ok": False, "error": tr_err(str(e), L), "need": "poppler" if "pdftotext" in str(e) else ""}
    except Exception:
        return 400, {"ok": False, "error": tr("This file cannot be read (damaged or protected).", L)}
    vl_, hint = vl_voice(b["lang"], L)
    vid = piper_voice_for(vl_)
    vname = (PIPER_VOICES.get(vid) or {}).get("name", "") if vid and (VL["synth"] is not None or piper_ready(vl_)) else ""
    return 200, {"ok": True, "id": fid, "name": m["name"], "title": b["title"], "lang": b["lang"], "ch": [{"t": c["t"], "p": c["p"]} for c in b["ch"]],
                 "n": b["n"], "total": b["total"], "bm": vl_bm_get(who["key"], fid), "dl": True,
                 "voice": {"lang": vl_, "name": vname or tr("old voice", L), "piper": bool(vname), "hint": tr(hint, L) if hint else ""},
                 "may": {"pi": vl_pi_may(role, perms)}, "pi": vl_pi_state(L), "speeds": list(VL_SPEEDS)}


def vl_do(who, d, lang=None, role="admin", perms=None):
    """POST /api/vorlesen -> (code, answer)"""
    d = d if isinstance(d, dict) else {}
    L = norm_lang(lang or d.get("lang") or CFG.get("lang"))
    a = str(d.get("action") or "")
    fid = str(d.get("id") or "")

    def out(ok, err="", code=None, **kw):
        return (code or (200 if ok else 400)), dict({"ok": ok, "error": tr_err(err, L) if err else None, "pi": vl_pi_state(L)}, **kw)
    if a == "poppler":
        if role != "admin":
            return out(False, "Only for the administrator", 403)
        return out(*vl_poppler_install())
    if a in ("bm", "play", "bplay"):
        m = tausch_file(fid)
        if m is None or not tausch_can_down(m, who) or tausch_ext(m["name"]) not in VL_READ_EXT:
            return out(False, "unknown file", 404)
        try:
            c, s = int(d.get("c") or 0), int(d.get("s") or 0)
        except (TypeError, ValueError):
            return out(False, "invalid value")
        if a == "bm":
            return out(vl_bm_save(who["key"], fid, c, s, force=bool(d.get("now"))))
        if a == "bplay":                                     # the browser reads: the radio stops (both ways: decision of the owner)
            if RADIO["want"]:
                radio_stop("read aloud")
            BR["sid"] = ""
            vl_bm_save(who["key"], fid, c, s)
            return out(True, t0=time.time())
        if not vl_pi_may(role, perms):
            return out(False, "Reading on the loudspeaker needs the right «Siren / sounds».", 403)
        return out(*vl_pi_play(who, m, c, s, d.get("speed") or 1.0, L))
    if a in ("stop", "pause", "resume", "seek", "speed", "volume"):
        if not vl_pi_may(role, perms):
            return out(False, "Reading on the loudspeaker needs the right «Siren / sounds».", 403)
        if a == "stop":
            vl_stop("button")
        elif a in ("pause", "resume"):
            VL["pause"] = a == "pause"
            if VL["key"] and VL["id"]:
                vl_bm_save(VL["key"], VL["id"], VL["c"], VL["s"], force=True)
        elif a == "seek":
            m = tausch_file(VL["id"])
            if not VL["want"] or m is None:
                return out(False, "nothing is being read")
            try:
                b = vl_book(m)
                c = max(0, min(int(d.get("c") or 0), len(b["n"]) - 1)); s = max(0, min(int(d.get("s") or 0), b["n"][c] - 1))
            except (TypeError, ValueError, LookupError):
                return out(False, "invalid value")
            with VL["lock"]:
                VL["c"], VL["s"] = c, s
                p = VL["out"]; VL["out"] = None
            _radio_kill(p)
        elif a == "speed":
            try:
                VL["speed"] = max(0.5, min(2.0, float(d.get("v"))))
            except (TypeError, ValueError):
                return out(False, "invalid value")
        else:
            try:
                CFG["vl_volume"] = int(max(0, min(100, float(d.get("v")))))
            except (TypeError, ValueError):
                return out(False, "invalid value")
            save_settings()
        return out(True)
    return 400, {"ok": False, "error": "unknown action"}


# ---- the web: /vorlesen, /api/vorlesen, the sound, the viewer -------------------------------------------------------------------
_smalltv_routes_vl = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzzv: read aloud and the viewer of the backpack
    _smalltv_routes_vl(app, reply, body)
    from flask import Response, request, g, send_file

    def ctx():
        role = getattr(g, "role", "admin")
        return tausch_who(g), role, (None if role == "admin" else user_req_perms(g)), norm_lang(request.args.get("lang") or CFG.get("lang"))

    def fil(who, fid, L):
        m = tausch_file(fid)
        if m is None or not tausch_can_see(m, who):
            return None, reply({"ok": False, "error": tr("unknown file", L)}, 404)
        if not tausch_can_down(m, who):
            return None, reply({"ok": False, "error": tr("You may not download files.", L)}, 403)
        return m, None

    @app.route("/vorlesen")
    def vl_page():
        who = tausch_who(g)
        if "files_view" not in who["perms"]:
            return sx_err(403, "error")
        return Response(render_page(VL_PAGE, "more"), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/vorlesen", methods=["GET", "POST"])
    def vl_api():
        who, role, perms, L = ctx()
        if request.method == "POST":
            code, ans = vl_do(who, body(), L, role, perms)
            return reply(ans, code)
        a = request.args
        if a.get("on"):                                      # 📖 in the header and the player of the browser (alarm = pause)
            st = vl_pi_state(L)
            h = vl_held()
            return reply({"ok": True, "on": VL["want"], "pi": {"on": st["on"], "id": st["id"], "name": st["name"], "c": st["c"], "s": st["s"], "state": st["state"],
                          "held": st["held"], "pause": st["pause"], "msg": st["msg"], "vol": st["vol"]} if a.get("full") else {"on": st["on"]},
                          "hold": tr(_VL_HELD_TXT[h], L) if h in _VL_HELD_TXT else "", "radio_t": VL["radio_t"], "now": time.time(), "inst": VL["inst"]})
        if a.get("bms"):
            return reply({"ok": True, "bms": vl_bm_list(who)})
        if a.get("last"):
            bl = vl_bm_list(who)
            k = max(bl, key=lambda x: bl[x]["t"]) if bl else ""
            return reply({"ok": True, "last": dict(bl[k], id=k) if k else None})
        code, ans = vl_get(who, str(a.get("id") or ""), L, role, perms)
        return reply(ans, code)

    @app.route("/api/vorlesen/audio")
    def vl_audio():
        who, role, perms, L = ctx()
        m, bad = fil(who, str(request.args.get("id") or ""), L)
        if bad is not None:
            return bad
        try:
            b = vl_book(m)
            c, s = int(request.args.get("c") or 0), int(request.args.get("s") or 0)
            if not (0 <= c < len(b["n"]) and 0 <= s < b["n"][c]):
                raise ValueError
        except (TypeError, ValueError, LookupError):
            return reply({"ok": False, "error": tr("invalid value", L)}, 400)
        vl_, _h = vl_voice(b["lang"], L)
        p_, err = vl_ton(m, b, c, s, vl_)
        if not p_:
            return reply({"ok": False, "error": tr_err(err, L)}, 503)
        vl_ahead(m, b, c, s, vl_, 1.0, 3)
        r = send_file(p_, mimetype="audio/wav", conditional=True, max_age=0)
        r.headers["Cache-Control"] = "private, max-age=3600"
        r.headers["X-Content-Type-Options"] = "nosniff"
        return r

    @app.route("/api/tausch/ansicht")
    def vl_ansicht():
        who, role, perms, L = ctx()
        m, bad = fil(who, str(request.args.get("id") or ""), L)
        if bad is not None:
            return bad
        try:
            v = vl_view(m, L)
        except OSError:
            return reply({"ok": False, "error": tr("unknown file", L)}, 404)
        return reply(dict(v, ok=True, id=m["id"], name=m["name"], inst=VL["inst"], admin=role == "admin"))

    @app.route("/tausch/seite/<fid>/<int:n>.jpg")
    def vl_seite(fid, n):
        who, role, perms, L = ctx()
        m, bad = fil(who, fid, L)
        if bad is not None:
            return bad
        if tausch_ext(m["name"]) != "pdf":
            return reply({"ok": False}, 404)
        p_ = vl_pdf_page(m, n)
        if not p_:
            return reply({"ok": False, "error": tr("no preview for this file", L)}, 404)
        return _tz_send(p_, "image/jpeg", False, cache="private, max-age=600")


_tausch_page_html_vl = tausch_page_html


# wraps: tausch_page_html
def tausch_page_html():                                     # + 639zzzzv: «🔊 Vorlesen», «▶ Weiter», the viewer
    out = _tausch_page_html_vl()
    i = out.rfind("</body>")
    if i < 0 or "window.tzCard = function" in out or "tzCard = function" not in VL_TZ_JS:
        return out
    js = VL_TZ_JS.replace("/*VLDE*/{}", json.dumps(_VL_DE, ensure_ascii=False).replace("</", "<\\/"), 1)
    return out[:i] + js + out[i:]


# ---- 📖 in the header (like 📻): while something is read, left of ?; a tap = the reader ---------------------------------------------
VL_SYM_BTN = ('<a class="btn sec ic" id="mwk-read" href="/vorlesen" hidden><span aria-hidden="true">📖</span>'
              '<i class="mwr-eq" aria-hidden="true"><b></b><b></b><b></b></i></a>')
if isinstance(KOPF_JS, str) and KOPF_JS.count('const KNOWN = new Set(["mwk-radio", ') == 1:     # the header keeps 📖 (not into ☰)
    KOPF_JS = KOPF_JS.replace('const KNOWN = new Set(["mwk-radio", ', 'const KNOWN = new Set(["mwk-read", "mwk-radio", ', 1)


def vl_sym(out):
    if 'id="mwk-read"' in out or out.count(RADIO_SYM_AT) != 1 or "</body>" not in out or "mwk-read" not in VL_SYM_JS:
        return out
    k = "Reading aloud - to the reader"
    tx = {L: (DE if L == "de" else TRX.get(L, {})).get(k) or k for L in ("de", "fr", "it", "rm")}
    tx["en"] = k.replace(" - ", " – ")
    out = out.replace(RADIO_SYM_AT, VL_SYM_BTN + RADIO_SYM_AT, 1)
    i = out.rfind("</body>")
    return out[:i] + VL_SYM_JS.replace("/*VSTX*/{}", json.dumps(tx, ensure_ascii=False).replace("</", "<\\/"), 1) + out[i:]


_render_page_vl = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzzzv: German texts of the reader, 📖 in the header
    out = _render_page_vl(page, active)
    if "/*VLDE*/" in out:
        out = out.replace("/*VLDE*/{}", json.dumps(_VL_DE, ensure_ascii=False).replace("</", "<\\/"), 1)
        out = out.replace("/*VLPLAYER*/", VL_PLAYER_JS, 1)
    return vl_sym(out)


# ---- the window (Tk): Mehr -> «📖 Vorlesen»: what is read on the loudspeaker, pause / stop, volume ---------------------------------
if GUI_OK:
    def _vl_tk_win(self):
        w = getattr(self, "_vl_top", None)
        if w is not None and w.winfo_exists():
            w.lift(); return
        w = self._vl_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Read aloud")); w.configure(bg=C["bg"]); w.geometry("420x250")
        st = tk.Label(w, text="", bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"), wraplength=390, justify="left", anchor="w")
        st.pack(fill="x", padx=12, pady=(10, 2))
        sub = tk.Label(w, text="", bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), wraplength=390, justify="left", anchor="w")
        sub.pack(fill="x", padx=12)
        bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=12, pady=8)
        adm = {"key": "admin", "name": "Admin", "admin": True, "perms": set(TZ_PERMS), "is_admin": True}
        self._fbtn(bf, "⏯ " + tr("Pause"), lambda: vl_do(adm, {"action": "resume" if VL["pause"] else "pause"}), primary=True).pack(side="left", padx=(0, 6))
        self._fbtn(bf, "⏹ " + tr("Stop"), lambda: vl_do(adm, {"action": "stop"})).pack(side="left")
        vf = tk.Frame(w, bg=C["bg"]); vf.pack(fill="x", padx=12)
        tk.Label(vf, text="🔈 " + tr("Volume"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 10)).pack(side="left")
        vol = tk.Scale(vf, from_=0, to=100, orient="horizontal", showvalue=True, bg=C["bg"], fg=C["txt"], highlightthickness=0, troughcolor=C["panel"],
                       command=lambda v: CFG.update(vl_volume=int(float(v))))
        vol.set(int(CFG.get("vl_volume", 60))); vol.bind("<ButtonRelease-1>", lambda _e: save_settings())
        vol.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._fbtn(w, "🌐 " + tr("Choose a story (browser)"), lambda: self._open_page("/tausch")).pack(anchor="w", padx=12, pady=6)
        self._fbtn(w, tr("Close"), w.destroy, primary=True).pack(side="bottom", anchor="e", padx=12, pady=(0, 10))

        def tick():
            try:
                if not w.winfo_exists():
                    return
                s = vl_pi_state()
                st.config(text=("📖 " + s["name"]) if s["on"] else tr("Nothing is being read on the loudspeaker."))
                sub.config(text=s["held"] or s["msg"] or (tr("Chapter") + f" {s['c'] + 1}" if s["on"] else ""))
                w.after(1000, tick)
            except Exception:
                pass
        tick()

    App._vl_win = _vl_tk_win
    _vl_tk_more_base = App._tk_more_bar

    def _vl_tk_more_bar(self, parent):
        f = _vl_tk_more_base(self, parent)
        row = max([int(x.grid_info().get("row", 0)) for x in f.grid_slaves()] + [-1]) + 1
        self._fbtn(f, "📖 " + tr("Read aloud"), self._vl_win).grid(row=row, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (after 639zzzzd «Radio»)
    App._tk_more_bar = _vl_tk_more_bar


# ---- the player of the browser: runs in the main window (window.top of the same origin), like the radio (mwRadioHost) ------------
VL_PLAYER_JS = r"""
// «📱 Handy»: the reader of the browser. It runs in the window of mwRadioHost() (the main page, or /vorlesen itself), so it reads on
// over the other pages; the page /vorlesen only shows it (P.cb). window.mwReadP = {A, S, book, play, pause, resume, stop, seek, speed}
(function () {
  if (window.mwReadP) return;
  const A = new Audio(); A.preload = "auto";
  const S = {on: false, id: "", name: "", c: 0, s: 0, st: "off", speed: 1, err: "", hold: "", paused: false, lang: "de", n: [], t0: 0};
  const P = window.mwReadP = {A: A, S: S, book: null, cb: null, tx: {}};
  const tx = k => P.tx[k] || k;
  const emit = () => { if (P.cb) try { P.cb(); } catch (e) { P.cb = null; } };
  const post = b => fetch("/api/vorlesen", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: S.lang}, b))})
    .then(r => r.json()).catch(() => ({ok: false}));
  const url = (c, s) => "/api/vorlesen/audio?id=" + encodeURIComponent(S.id) + "&c=" + c + "&s=" + s + "&lang=" + S.lang;
  P.next = (c, s, k) => { s += k || 1; while (c < S.n.length && s >= S.n[c]) { s -= S.n[c]; c++; } return c < S.n.length ? [c, s] : null; };
  P.paraEnd = (c, s) => { const ch = P.book && P.book.ch[c]; if (!ch) return true; for (const p of ch.p) { if (s < p.length) return s === p.length - 1; s -= p.length; } return true; };
  let gen = 0, bmT = 0, bad = 0, gap = 0;
  function bm(now) { if (!S.id) return; if (!now && Date.now() - bmT < 8000) return; bmT = Date.now(); post({action: "bm", id: S.id, c: S.c, s: S.s, now: now ? 1 : 0}); }
  function say() {                                         // the current sentence
    const g = ++gen; clearTimeout(gap);
    if (!S.on || S.paused || S.hold) { emit(); return; }
    S.st = "loading"; A.src = url(S.c, S.s); A.defaultPlaybackRate = A.playbackRate = S.speed;
    try { A.preservesPitch = true; } catch (e) {}
    const p = A.play();
    if (p && p.catch) p.catch(e => { if (g !== gen || !S.on) return; if (e && e.name === "NotAllowedError") { S.paused = true; S.st = "paused"; P.ms(); emit(); } });
    emit();
  }
  A.addEventListener("playing", () => { bad = 0; S.st = "playing"; A.playbackRate = S.speed; emit(); });
  A.addEventListener("ended", () => {
    if (!S.on || S.paused || S.hold) return;
    const nx = P.next(S.c, S.s);
    if (!nx) { S.c = 0; S.s = 0; bm(true); P.stop(); S.st = "done"; emit(); return; }
    const pe = P.paraEnd(S.c, S.s); S.c = nx[0]; S.s = nx[1]; bm(false); emit();
    gap = setTimeout(say, (pe ? 450 : 120) / Math.max(.5, S.speed));
  });
  A.addEventListener("error", () => {
    if (!S.on || !A.getAttribute("src")) return;
    const g = gen;
    fetch(url(S.c, S.s)).then(r => r.ok ? null : r.json()).then(j => {
      if (g !== gen || !S.on) return;
      if (++bad > 2 || (j && j.error)) { const e = (j && j.error) || tx("The voice does not answer."); P.stop(); S.err = e; S.st = "error"; emit(); return; }
      setTimeout(() => { if (g === gen) say(); }, 1500);
    }).catch(() => { if (g === gen && ++bad <= 2) setTimeout(say, 2500); else if (g === gen) { P.stop(); S.err = tx("No connection to MoveEye."); emit(); } });
  });
  P.play = function (id, c, s, book) {                      // called in the tap itself (iPhone: sound only after a tap)
    try { const R = window.mwRadioP; if (R && R.S && R.S.on) R.stop(); } catch (e) {}   // radio and reading exclude each other
    Object.assign(S, {on: true, id: id, name: book.title || book.name || "", c: c | 0, s: s | 0, paused: false, hold: "", err: "", n: book.n || []});
    P.book = book; S.t0 = Date.now() / 1000; bad = 0;
    say(); P.ms();
    post({action: "bplay", id: id, c: S.c, s: S.s}).then(j => { if (j && j.t0) S.t0 = j.t0; });
  };
  P.pause = () => { if (!S.on) return; S.paused = true; gen++; clearTimeout(gap); A.pause(); S.st = "paused"; bm(true); P.ms(); emit(); };
  P.resume = () => { if (!S.on) return; S.paused = false; say(); P.ms(); };
  P.stop = () => { const was = S.on; if (was) bm(true); S.on = false; S.paused = false; S.hold = ""; S.st = "off"; gen++; clearTimeout(gap);
    A.pause(); A.removeAttribute("src"); try { A.load(); } catch (e) {} P.ms(); emit(); };
  P.seek = (c, s) => { S.c = c; S.s = s; bm(true); if (S.on && !S.paused && !S.hold) say(); else emit(); };
  P.speed = v => { S.speed = Math.max(.5, Math.min(2, +v || 1)); A.playbackRate = S.speed; emit(); };
  setInterval(async () => {                                // alarms, sounds of MoveEye, the radio: pause / stop
    if (!S.on) return;
    try { const R = window.mwRadioP; if (R && R.S && R.S.on) { P.stop(); return; } } catch (e) {}
    let j = null; try { j = await (await fetch("/api/vorlesen?on=1&lang=" + S.lang, {cache: "no-store"})).json(); } catch (e) { return; }
    if (!j || !S.on) return;
    if (j.radio_t && j.radio_t > S.t0 + 1) { P.stop(); return; }
    if (j.hold && !S.hold) { S.hold = j.hold; gen++; clearTimeout(gap); A.pause(); S.st = "paused"; emit(); }
    else if (!j.hold && S.hold) { S.hold = ""; say(); }
    else if (j.hold && S.hold !== j.hold) { S.hold = j.hold; emit(); }
  }, 2000);
  let msSet = false;
  P.ms = function () {                                     // lock screen (iPhone / Android): title and buttons
    if (!("mediaSession" in navigator)) return;
    try {
      const ch = P.book && P.book.ch[S.c];
      navigator.mediaSession.metadata = S.on && window.MediaMetadata ? new MediaMetadata({title: S.name, artist: (ch && ch.t) || "MoveEye", album: "MoveEye · " + tx("Read aloud"),
        artwork: [{src: "/icon-192.png", sizes: "192x192", type: "image/png"}]}) : null;
      navigator.mediaSession.playbackState = S.on ? (S.paused ? "paused" : "playing") : "none";
      if (!msSet) {
        msSet = true;
        navigator.mediaSession.setActionHandler("play", () => P.resume());
        navigator.mediaSession.setActionHandler("pause", () => P.pause());
        try { navigator.mediaSession.setActionHandler("stop", () => P.stop()); } catch (e) {}
        try { navigator.mediaSession.setActionHandler("nexttrack", () => { if (S.c + 1 < S.n.length) P.seek(S.c + 1, 0); }); } catch (e) {}
        try { navigator.mediaSession.setActionHandler("previoustrack", () => P.seek(S.s > 2 ? S.c : Math.max(0, S.c - 1), 0)); } catch (e) {}
      }
    } catch (e) {}
  };
  addEventListener("pagehide", () => { if (S.on) bm(true); });
})();
"""

VL_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Read aloud</title>
<style>
/*BASECSS*/
main{padding:12px 16px 0;max-width:820px;margin:0 auto;box-sizing:border-box}
.vl-back{display:inline-flex;align-items:center;min-height:40px;text-decoration:none;color:var(--acc);font-weight:600}
.vl-top{display:flex;align-items:center;gap:8px;margin:2px 0 4px}.vl-top h2{flex:1;min-width:0;margin:0;font-size:20px;overflow-wrap:anywhere}
.vl-top button,.vl-top a{min-height:40px;min-width:42px;padding:2px 8px;flex:none;text-decoration:none;display:inline-flex;align-items:center;justify-content:center}
.vl-sub{font-size:13px;color:var(--mut);display:flex;gap:6px;flex-wrap:wrap}.vl-sub b{color:var(--txt)}
.vl-bm{margin:8px 0 0;padding:6px 10px;border:1px dashed var(--line);border-radius:10px;font-size:12.5px;color:var(--mut);display:flex;gap:8px;align-items:center}
.vl-bm span{flex:1;min-width:0}.vl-bm button{min-height:32px;padding:2px 10px;font-size:12.5px;flex:none}
.vl-warn{margin:8px 0 0;padding:8px 12px;border-radius:10px;border:1px solid var(--yel);color:var(--yel);font-size:13px;font-weight:600}
.vl-note{margin:8px 0 0;font-size:12.5px;color:var(--mut)}.vl-note:empty{display:none}
.vl-txt{padding:10px 2px 18px;font:18px/1.65 Georgia,"Iowan Old Style","Times New Roman",serif;overflow-wrap:anywhere}
.vl-txt.f1{font-size:16px}.vl-txt.f3{font-size:22px}
.vl-txt h3{font:600 14px/1.3 system-ui,-apple-system,sans-serif;color:var(--mut);margin:10px 0 8px;letter-spacing:.03em;text-transform:uppercase}
.vl-txt p{margin:0 0 .9em}.vl-txt .s{cursor:pointer;border-radius:4px}.vl-txt .s.done{opacity:.55}
.vl-txt .s.cur{background:color-mix(in srgb,var(--acc) 30%,transparent);box-shadow:0 0 0 3px color-mix(in srgb,var(--acc) 30%,transparent);-webkit-box-decoration-break:clone;box-decoration-break:clone}
.vl-more{display:flex;justify-content:center;margin:0 0 14px}
.vl-dock{position:sticky;bottom:0;z-index:5;margin:0 -16px;border-top:1px solid var(--line);background:var(--panel);padding:8px 16px;padding-bottom:max(10px,env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:8px}
.vl-prog{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--mut)}.vl-prog input{flex:1;min-width:0;accent-color:var(--acc)}
.vl-ctl{display:flex;align-items:center;justify-content:center;gap:10px}
.vl-ctl button{min-width:54px;min-height:48px;padding:2px 6px;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1.05;font-size:19px}
.vl-ctl button small{font-size:10px;color:var(--mut);margin-top:2px}
.vl-ctl .vl-go{width:64px;height:64px;min-width:64px;border-radius:50%;font-size:26px;background:var(--acc);color:#fff;border:0}
.vl-row{display:flex;align-items:center;gap:6px;font-size:12.5px}.vl-row>span{color:var(--mut);min-width:48px}
.vl-seg{display:flex;gap:3px;background:var(--field);border:1px solid var(--line);border-radius:10px;padding:3px;flex:1;min-width:0}
.vl-seg button{flex:1;border:0;background:transparent;color:var(--mut);font:inherit;font-weight:600;min-height:36px;padding:2px 4px;border-radius:7px;white-space:nowrap;box-shadow:none}
.vl-seg button.on{background:var(--acc);color:#fff}
.vl-row input[type=range]{flex:1;min-width:0;accent-color:var(--acc)}
.vl-foot{font-size:11.5px;color:var(--mut);text-align:center}
.vl-err{color:var(--red);font-size:13px;text-align:center}.vl-err:empty{display:none}
#vl-pan{position:fixed;left:0;right:0;bottom:0;max-height:70vh;overflow:auto;z-index:60;background:var(--panel);border-top:1px solid var(--line);border-radius:16px 16px 0 0;
  padding:12px 16px max(14px,env(safe-area-inset-bottom));box-shadow:0 -8px 30px #0008}
#vl-pan h3{margin:0 0 8px;font-size:15px;display:flex;align-items:center;gap:8px}#vl-pan h3 span{flex:1}
#vl-pan .row{display:flex;gap:8px;align-items:center;padding:9px 4px;border-bottom:1px solid var(--line);cursor:pointer}
#vl-pan .row span{flex:1;min-width:0;font-size:14px}#vl-pan .row small{color:var(--mut);white-space:nowrap}#vl-pan .row.on span{font-weight:700;color:var(--acc)}
.vl-empty{padding:30px 0;text-align:center;color:var(--mut)}.vl-empty .ic{font-size:56px}
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
  <a class="vl-back" href="/tausch" id="vl-back">‹ Digital backpack</a>
  <div class="vl-empty" id="vl-empty" hidden><div class="ic">📖</div><p id="vl-empty-t"></p><a class="btn" href="/tausch" id="vl-empty-a"></a></div>
  <section id="vl-box" hidden>
    <div class="vl-top"><h2 id="vl-title">📖</h2><button type="button" class="sec" id="vl-toc">☰</button><button type="button" class="sec" id="vl-aa">Aa</button><a class="btn sec" id="vl-dl" download>⬇</a></div>
    <div class="vl-sub" id="vl-sub"></div>
    <div class="vl-warn" id="vl-warn" hidden></div>
    <div class="vl-bm"><span id="vl-bmt"></span><button type="button" class="sec" id="vl-zero"></button></div>
    <div class="vl-note" id="vl-note"></div>
    <div class="vl-txt" id="vl-txt"></div>
    <div class="vl-more"><button type="button" class="sec" id="vl-nextch" hidden></button></div>
  </section>
  <div class="vl-dock" id="vl-dock" hidden>
    <div class="vl-prog"><span id="vl-pa"></span><input type="range" id="vl-pos" min="0" max="1" value="0"><span id="vl-pb"></span></div>
    <div class="vl-ctl">
      <button type="button" class="sec" id="vl-pc">⏮<small></small></button><button type="button" class="sec" id="vl-pp">↶<small></small></button>
      <button type="button" class="vl-go" id="vl-go">▶</button>
      <button type="button" class="sec" id="vl-np">↷<small></small></button><button type="button" class="sec" id="vl-nc">⏭<small></small></button>
    </div>
    <div class="vl-row"><span id="vl-l-sp"></span><div class="vl-seg" id="vl-sp"></div></div>
    <div class="vl-row"><span id="vl-l-wo"></span><div class="vl-seg"><button type="button" id="vl-w-br"></button><button type="button" id="vl-w-pi"></button></div></div>
    <div class="vl-row" id="vl-vr" hidden><span>🔈</span><input type="range" id="vl-vol" min="0" max="100"><b id="vl-vv"></b></div>
    <div class="vl-err" id="vl-err"></div>
    <div class="vl-foot" id="vl-foot"></div>
  </div>
</main>
<div id="vl-pan" hidden></div>
<script type="text/plain" id="vl-player">/*VLPLAYER*/</script>
<script>
/*COMMON*/
Object.assign(I18N.de, /*VLDE*/{});
window.mwRadioHost = window.mwRadioHost || function () {   // the window that keeps the player: the main page (same origin) or this one
  try { const w = window.top; if (w !== window && w.location.origin === location.origin && w.document) return w; } catch (e) {}
  return window;
};
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const LS = {get: (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} }};
  const H = mwRadioHost();
  if (!H.mwReadP) { const sc = H.document.createElement("script"); sc.textContent = $i("vl-player").textContent; H.document.head.appendChild(sc); }
  const P = H.mwReadP, B = P.S;
  ["Read aloud", "The voice does not answer.", "No connection to MoveEye."].forEach(k => { P.tx[k] = t(k); }); B.lang = L();
  document.title = "MoveEye – " + t("Read aloud");
  $i("vl-back").textContent = "‹ " + t("Digital backpack");
  const api = b => fetch("/api/vorlesen", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b))})
    .then(r => r.json()).catch(() => ({ok: false, error: t("No connection to MoveEye.")}));
  const getJ = async u => { try { return await (await fetch(u, {cache: "no-store"})).json(); } catch (e) { return null; } };
  let W = LS.get("mw-read-where", "br") === "pi" ? "pi" : "br", J = null, PI = {}, cur = {c: 0, s: 0}, chShown = -1, size = +LS.get("mw-read-size", 2) || 2, userScroll = 0, busy = false;
  let speed = +LS.get("mw-read-speed", 1) || 1;
  if (!B.on) B.speed = speed;
  const id0 = new URLSearchParams(location.search).get("id") || "";
  async function start() {
    let id = id0;
    const st = await getJ("/api/vorlesen?on=1&full=1&lang=" + L()); PI = (st && st.pi) || {};
    if (!id) id = B.on ? B.id : PI.on ? PI.id : "";
    if (!id) { const l = await getJ("/api/vorlesen?last=1"); id = l && l.last ? l.last.id : ""; }
    if (!id) { $i("vl-empty").hidden = false; $i("vl-empty-t").textContent = t("Nothing to read yet. Choose a story in the Digital backpack: «🔊 Read aloud»."); $i("vl-empty-a").textContent = "🎒 " + t("Digital backpack"); return; }
    J = await getJ("/api/vorlesen?id=" + encodeURIComponent(id) + "&lang=" + L());
    if (!J || !J.ok) { $i("vl-empty").hidden = false; $i("vl-empty-t").textContent = (J && J.error) || t("No connection to MoveEye."); $i("vl-empty-a").textContent = "🎒 " + t("Digital backpack"); return; }
    if (B.on && B.id === J.id) { cur = {c: B.c, s: B.s}; W = "br"; }
    else if (J.pi.on && J.pi.id === J.id) { cur = {c: J.pi.c, s: J.pi.s}; W = "pi"; }
    else if (J.bm) cur = {c: Math.min(J.bm.c, J.n.length - 1), s: J.bm.s};
    if (!J.may.pi) W = "br";
    $i("vl-box").hidden = false; $i("vl-dock").hidden = false;
    $i("vl-dl").href = "/tausch/dl/" + J.id; $i("vl-dl").title = t("Download");
    $i("vl-toc").title = t("Contents"); $i("vl-aa").title = t("Text size");
    const sp = $i("vl-sp"); (J.speeds || [1]).forEach(v => { const b = E("button", "", String(v).replace(".", L() === "en" ? "." : ",") + "×"); b.type = "button"; b.dataset.v = v;
      b.onclick = () => setSpeed(v); sp.appendChild(b); });
    $i("vl-l-sp").textContent = t("Speed"); $i("vl-l-wo").textContent = t("Where");
    $i("vl-w-br").textContent = "📱 " + t("Phone"); $i("vl-w-pi").textContent = "🔈 MoveEye";
    $i("vl-pc").querySelector("small").textContent = $i("vl-nc").querySelector("small").textContent = t("Chapter");
    $i("vl-pp").querySelector("small").textContent = $i("vl-np").querySelector("small").textContent = t("Paragraph");
    $i("vl-zero").textContent = "⟲ " + t("From the start");
    P.cb = mine; addEventListener("pagehide", () => { if (P.cb === mine) P.cb = null; });
    paint(true); poll();
  }
  const mine = () => { if (W === "br" && B.id === (J && J.id) && B.on) cur = {c: B.c, s: B.s}; paint(); };
  const playingHere = () => W === "br" ? (B.on && B.id === J.id) : (PI.on && PI.id === J.id);
  const pausedHere = () => W === "br" ? (B.paused || !!B.hold) : (PI.pause || !!PI.held);
  const chars = (c, from) => { let n = 0, k = 0; J.ch[c].p.forEach(p => p.forEach(x => { if (k++ >= (from || 0)) n += x.length; })); return n; };
  const mins = n => Math.max(1, Math.round(n / 14 / (W === "br" ? B.speed : (PI.speed || speed)) / 60));
  function renderChapter() {
    const box = $i("vl-txt"); box.textContent = ""; chShown = cur.c;
    const ch = J.ch[cur.c]; if (ch.t) box.appendChild(E("h3", "", ch.t));
    let k = 0;
    ch.p.forEach(p => { const pe = E("p"); p.forEach(x => { const sp = E("span", "s", x); sp.dataset.s = k++; pe.append(sp, " "); }); box.appendChild(pe); });
    const nb = $i("vl-nextch"); nb.hidden = cur.c + 1 >= J.ch.length; nb.textContent = t("Next chapter") + " ›";
  }
  function paint(scroll) {
    if (!J) return;
    if (chShown !== cur.c) { renderChapter(); scroll = true; }
    const on = playingHere();
    $i("vl-title").textContent = "📖 " + J.title;
    const ch = J.ch[cur.c]; const sub = $i("vl-sub"); sub.textContent = "";
    sub.append(E("span", "", t("Chapter") + " " + (cur.c + 1) + " / " + J.ch.length + (ch.t ? " ·" : "")), E("b", "", ch.t || ""));
    let cs = null;
    $i("vl-txt").querySelectorAll(".s").forEach(x => { const k = +x.dataset.s; x.classList.toggle("done", k < cur.s); x.classList.toggle("cur", k === cur.s);
      if (k === cur.s) cs = x; });
    if (cs && (scroll || on) && Date.now() - userScroll > 6000) { const r = cs.getBoundingClientRect(), dh = $i("vl-dock").offsetHeight;
      if (scroll || r.top < 70 || r.bottom > innerHeight - dh - 30) cs.scrollIntoView({block: "center", behavior: scroll ? "auto" : "smooth"}); }
    const hold = W === "br" ? B.hold : PI.held;
    $i("vl-warn").hidden = !hold; $i("vl-warn").textContent = hold ? "⏸ " + hold : "";
    const bm = J.bm; $i("vl-bmt").textContent = "🔖 " + (bm ? t("Bookmark") + ": " + t("Chapter") + " " + (bm.c + 1) + " · " + bm.pct + " % · " + new Date(bm.t * 1000).toLocaleString([], {dateStyle: "short", timeStyle: "short"})
      : t("MoveEye remembers where you stop - for you, on every device."));
    $i("vl-note").textContent = "🗣 " + J.voice.name + (J.voice.piper ? " (Piper)" : "") + (J.voice.hint ? " – " + J.voice.hint : "");
    const n = J.n[cur.c], pos = $i("vl-pos"); pos.max = Math.max(1, n - 1); if (document.activeElement !== pos) pos.value = cur.s;
    $i("vl-pa").textContent = t("Chapter") + " " + Math.round(100 * cur.s / Math.max(1, n)) + " %";
    let rest = chars(cur.c, cur.s); for (let c = cur.c + 1; c < J.ch.length; c++) rest += chars(c);
    $i("vl-pb").textContent = "≈ " + mins(rest) + " min";
    const go = $i("vl-go"); go.textContent = on && !pausedHere() ? "⏸" : "▶"; go.title = on && !pausedHere() ? t("Pause") : t("Read aloud");
    $i("vl-w-br").classList.toggle("on", W === "br"); $i("vl-w-pi").classList.toggle("on", W === "pi"); $i("vl-w-pi").disabled = !J.may.pi;
    const v = W === "br" ? B.speed : (PI.on && PI.id === J.id ? PI.speed || speed : speed);
    $i("vl-sp").querySelectorAll("button").forEach(b => b.classList.toggle("on", Math.abs(+b.dataset.v - v) < .01));
    $i("vl-vr").hidden = W !== "pi"; const vo = $i("vl-vol"); if (document.activeElement !== vo && PI.vol != null) vo.value = PI.vol; $i("vl-vv").textContent = vo.value + "%";
    const err = W === "br" ? B.err : (PI.on || PI.state === "error" ? PI.msg : "");
    $i("vl-err").textContent = err || (!J.may.pi && W === "pi" ? t("Reading on the loudspeaker needs the right «Siren / sounds».") : "");
    $i("vl-foot").textContent = W === "br" ? t("Plays in this browser - also on the other pages (📖 at the top).") : t("Plays on the loudspeaker of MoveEye.") + (PI.on && PI.id !== J.id && PI.name ? " ▶ " + PI.name : "");
    $i("vl-txt").classList.toggle("f1", size === 1); $i("vl-txt").classList.toggle("f3", size === 3);
  }
  async function piDo(b) { if (busy) return; busy = true; const j = await api(b); busy = false; if (j && j.pi) PI = j.pi; if (j && !j.ok && j.error) $i("vl-err").textContent = j.error; paint(); poll(true); }
  function seek(c, s) {
    c = Math.max(0, Math.min(c, J.ch.length - 1)); s = Math.max(0, Math.min(s, J.n[c] - 1)); cur = {c, s};
    if (W === "br" && B.on && B.id === J.id) P.seek(c, s);
    else if (W === "pi" && PI.on && PI.id === J.id) piDo({action: "seek", c, s});
    else api({action: "bm", id: J.id, c, s, now: 1});
    paint(true);
  }
  function play() {
    if (W === "br") {
      if (B.on && B.id === J.id) { if (B.paused) P.resume(); else P.pause(); return; }
      if (PI.on && PI.id === J.id) api({action: "stop"});
      P.speed(speed); P.play(J.id, cur.c, cur.s, J); return;
    }
    if (PI.on && PI.id === J.id) { piDo({action: PI.pause ? "resume" : "pause"}); return; }
    if (B.on) P.stop();
    piDo({action: "play", id: J.id, c: cur.c, s: cur.s, speed});
  }
  function setSpeed(v) { speed = v; LS.set("mw-read-speed", String(v)); if (W === "br") P.speed(v); else if (PI.on) piDo({action: "speed", v}); paint(); }
  function where(w) {
    if (w === W) return;
    const was = playingHere() && !pausedHere(); W = w; LS.set("mw-read-where", w);
    if (w === "pi") { if (B.on && B.id === J.id) P.stop(); if (was) piDo({action: "play", id: J.id, c: cur.c, s: cur.s, speed}); }
    else { if (PI.on && PI.id === J.id) api({action: "stop"}); if (was) { P.speed(speed); P.play(J.id, cur.c, cur.s, J); } }
    paint();
  }
  function paraStart(dir) {                                 // ↶ / ↷: the start of this / the previous / the next paragraph
    const ps = []; let k = 0; J.ch[cur.c].p.forEach(p => { ps.push(k); k += p.length; });
    let i = ps.length - 1; while (i > 0 && ps[i] > cur.s) i--;
    if (dir < 0) { if (cur.s - ps[i] < 2 && i > 0) i--; else if (cur.s - ps[i] < 2 && cur.c > 0) return seek(cur.c - 1, J.n[cur.c - 1] - 1); return seek(cur.c, ps[i]); }
    if (i + 1 < ps.length) return seek(cur.c, ps[i + 1]);
    if (cur.c + 1 < J.ch.length) seek(cur.c + 1, 0);
  }
  $i("vl-go").onclick = play;
  $i("vl-pc").onclick = () => seek(cur.s > 2 ? cur.c : cur.c - 1, 0);
  $i("vl-nc").onclick = () => { if (cur.c + 1 < J.ch.length) seek(cur.c + 1, 0); };
  $i("vl-nextch").onclick = () => { if (cur.c + 1 < J.ch.length) seek(cur.c + 1, 0); };
  $i("vl-pp").onclick = () => paraStart(-1); $i("vl-np").onclick = () => paraStart(1);
  $i("vl-pos").onchange = () => seek(cur.c, +$i("vl-pos").value);
  $i("vl-w-br").onclick = () => where("br"); $i("vl-w-pi").onclick = () => where("pi");
  $i("vl-zero").onclick = () => seek(0, 0);
  $i("vl-aa").onclick = () => { size = size % 3 + 1; LS.set("mw-read-size", String(size)); paint(); };
  $i("vl-txt").addEventListener("click", e => { const x = e.target.closest && e.target.closest(".s"); if (x) seek(cur.c, +x.dataset.s); });
  let vt = 0; $i("vl-vol").oninput = () => { $i("vl-vv").textContent = $i("vl-vol").value + "%"; clearTimeout(vt); vt = setTimeout(() => piDo({action: "volume", v: +$i("vl-vol").value}), 250); };
  ["wheel", "touchmove"].forEach(k => addEventListener(k, () => { userScroll = Date.now(); }, {passive: true}));
  $i("vl-toc").onclick = () => {
    const pan = $i("vl-pan"); if (!pan.hidden) { pan.hidden = true; return; }
    pan.textContent = ""; const h = E("h3"), x = E("button", "sec", "✕"); x.type = "button"; x.onclick = () => { pan.hidden = true; };
    h.append(E("span", "", "☰ " + t("Contents") + " · " + J.title), x); pan.appendChild(h);
    J.ch.forEach((c, i) => { const r = E("div", "row" + (i === cur.c ? " on" : ""));
      r.append(E("span", "", (i + 1) + ". " + (c.t || t("Chapter") + " " + (i + 1))), E("small", "", i < cur.c ? "✓" : i === cur.c ? "🔖 " + Math.round(100 * cur.s / J.n[i]) + " %" : "≈ " + mins(chars(i)) + " min"));
      r.onclick = () => { pan.hidden = true; seek(i, 0); }; pan.appendChild(r); });
    pan.hidden = false;
  };
  let pt = 0;
  async function poll(soon) {
    clearTimeout(pt);
    if (!soon) { const st = await getJ("/api/vorlesen?on=1&full=1&lang=" + L()); if (st && st.pi) { PI = st.pi;
      if (W === "pi" && PI.on && J && PI.id === J.id && (PI.c !== cur.c || PI.s !== cur.s)) cur = {c: PI.c, s: PI.s}; paint(); } }
    pt = setTimeout(poll, soon ? 600 : (W === "pi" && PI.on ? 1200 : 5000));
  }
  start();
})();
</script>
</body></html>
"""

VL_SYM_JS = r"""<style>.hdr-ctl.mwk>#mwk-read{order:0;position:relative;font-size:17px}#mwk-read[hidden]{display:none!important}
#mwk-read .mwr-eq{position:absolute;right:5px;bottom:7px;display:flex;align-items:flex-end;gap:1px;height:7px}
@media(max-width:700px){.hdr-ctl.mwk>#mwk-read{width:34px;min-width:34px}#mwk-read .mwr-eq{right:2px}}
#mwk-read .mwr-eq b{width:2px;height:100%;background:var(--grn);border-radius:1px;transform-origin:bottom;transform:scaleY(.7);animation:mwv-eq 1.8s ease-in-out infinite}
#mwk-read .mwr-eq b:nth-child(2){animation-delay:-.6s}#mwk-read .mwr-eq b:nth-child(3){animation-delay:-1.2s}#mwk-read.pz .mwr-eq b{animation:none;background:var(--yel)}
@keyframes mwv-eq{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}@media(prefers-reduced-motion:reduce){#mwk-read .mwr-eq b{animation:none}}</style>
<script>(function () {
  const a = document.getElementById("mwk-read"), TX = /*VSTX*/{};
  if (!a || window.mwReadSym) return; window.mwReadSym = 1;
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "de"; } catch (e) { return "de"; } };
  window.mwRadioHost = window.mwRadioHost || function () {
    try { const w = window.top; if (w !== window && w.location.origin === location.origin && w.document) return w; } catch (e) {}
    return window;
  };
  const H = mwRadioHost(), home = location.pathname === "/vorlesen";
  let pi = false;
  function paint() {
    let br = false, pz = false; try { const S = H.mwReadP && H.mwReadP.S; br = !!(S && S.on); pz = !!(S && (S.paused || S.hold)); } catch (e) {}
    const lab = TX[L()] || TX.en; if (a.title !== lab) { a.title = lab; a.setAttribute("aria-label", lab); }
    a.hidden = home || !(br || pi); a.classList.toggle("pz", br && pz);
  }
  async function poll() { if (home || document.hidden) return;
    try { const r = await fetch("/api/vorlesen?on=1", {cache: "no-store"}); if (r.ok) { const j = await r.json(); pi = !!(j && j.on); } } catch (e) {} paint(); }
  paint(); setTimeout(poll, 400); setInterval(poll, 15000); setInterval(paint, 1000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
})();</script>"""

# ---- the Digital backpack: «🔊 Vorlesen» on each story, «▶ Weiter» at the top, the viewer (a tap on a file) --------------------------
VL_TZ_JS = r"""<style>
.vl-chip{display:inline-flex;align-items:center;gap:6px;margin:2px 9px 7px;padding:3px 10px;min-height:30px;max-width:calc(100% - 18px);box-sizing:border-box;border-radius:15px;
  border:1px solid var(--acc);background:color-mix(in srgb,var(--acc) 16%,transparent);color:var(--txt);font-size:12.5px;font-weight:600;text-decoration:none;white-space:nowrap;overflow:hidden}
.tz-list .tz-it .vl-chip{margin:2px 10px 6px}.vl-chip i{font-style:normal;font-weight:400;color:var(--mut);font-size:11.5px}
.vl-cont{display:flex;gap:10px;align-items:center}.vl-cont .ic{font-size:30px}.vl-cont .tx{flex:1;min-width:0}
.vl-cont b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.vl-cont .mut{font-size:12.5px}
.vl-cont a.btn{min-height:40px;white-space:nowrap;text-decoration:none;display:inline-flex;align-items:center}
.vl-pbar{height:4px;border-radius:2px;background:var(--field);margin-top:6px;overflow:hidden}.vl-pbar i{display:block;height:100%;background:var(--acc)}
.vw{background:var(--bg);color:var(--txt)}.vw .bar{color:var(--txt);border-bottom:1px solid var(--line)}
.vw .bar button,.vw .bar a{min-height:38px;padding:4px 10px;flex:none;text-decoration:none;display:inline-flex;align-items:center}
.vw-info{padding:6px 14px;font-size:12.5px;color:var(--mut);border-bottom:1px solid var(--line);display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.vw-info .tz-tabs{margin:0;flex:1 1 220px}.vw-info .tz-tabs button{min-height:34px;padding:4px 8px}
.vw-bd{flex:1;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch;position:relative}
.vw-pages{display:flex;flex-direction:column;align-items:center;gap:14px;padding:14px;background:#2a2f38;min-height:100%;box-sizing:border-box}
.vw-pages figure{margin:0;display:flex;flex-direction:column;align-items:center;gap:4px;width:100%}
.vw-pages img{width:min(100%,900px);min-height:120px;background:#fff;box-shadow:0 4px 18px #0007;border-radius:2px}
.vw-pages figcaption{font-size:11.5px;color:#aab}
.vw-book{display:flex;min-height:100%}
.vw-toc{flex:none;width:250px;border-right:1px solid var(--line);padding:12px;font-size:13.5px;background:var(--panel);box-sizing:border-box}
.vw-toc a{display:block;padding:7px 9px;border-radius:8px;color:var(--txt);text-decoration:none;cursor:pointer}.vw-toc a.on{background:var(--acc);color:#fff}
.vw-toc h4{margin:0 0 8px;font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
.vw-read{flex:1;min-width:0;margin:0 auto;padding:14px 20px 30px;font:17px/1.6 Georgia,"Times New Roman",serif;max-width:760px;overflow-wrap:anywhere}
.vw-read h2{font:700 20px/1.3 system-ui,-apple-system,sans-serif;margin:8px 0 12px}.vw-read p{margin:0 0 .9em}
.vw-read.plain{white-space:pre-wrap;font:15px/1.55 system-ui,-apple-system,sans-serif}
.vw-sel{margin:10px 14px 0;width:calc(100% - 28px)}
.vw-tbl{border-collapse:separate;border-spacing:0;font-size:13.5px;min-width:100%}
.vw-tbl th{position:sticky;top:0;background:var(--panel);text-align:left;font-weight:700;border-bottom:2px solid var(--line);padding:8px 10px;white-space:nowrap;cursor:pointer}
.vw-tbl td{padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap;max-width:420px;overflow:hidden;text-overflow:ellipsis}.vw-tbl td.n{text-align:right;font-variant-numeric:tabular-nums}
.vw-tbl td.i{color:var(--mut);text-align:right;font-size:11.5px}
.vw-code{margin:0;padding:12px 14px;font:13px/1.55 ui-monospace,Menlo,Consolas,monospace;white-space:pre;tab-size:4}
.vw-code .k{color:#7cc4ff}.vw-code .s{color:#9fe08a}.vw-code .n{color:#f5b971}.vw-code .b{color:#ff8fb1}
.vw-code .ln{color:var(--mut);opacity:.6;display:inline-block;min-width:2.6em;padding-right:.8em;text-align:right;user-select:none;-webkit-user-select:none}
body.light .vw-code .k{color:#0b5cad}body.light .vw-code .s{color:#2d7a17}body.light .vw-code .n{color:#a35a00}body.light .vw-code .b{color:#b0124d}
.vw-unk{max-width:440px;margin:30px auto;padding:20px;text-align:center}.vw-unk .ic{font-size:64px}
.vw-unk dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;text-align:left;font-size:13.5px;margin:16px 0}.vw-unk dt{color:var(--mut)}.vw-unk dd{margin:0;overflow-wrap:anywhere}
.vw-hint{margin:10px 14px;padding:8px 12px;border-radius:10px;background:var(--field);font-size:12.5px;color:var(--mut)}
.vw-hint button{margin-top:8px}
</style>
<script>
Object.assign(I18N.de, /*VLDE*/{});
(function () {
  const RD = new Set(["txt", "md", "epub", "docx", "pdf"]), OFFICE = new Set(["xlsx", "xls", "odt", "ods", "odp", "pptx", "ppt", "doc", "rtf", "pages", "numbers", "key"]);
  const IC = {epub: "📖", json: "{ }", csv: "📊", tsv: "📊", pdf: "📕", docx: "📄", md: "📝", txt: "📝"};
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const getJ = async u => { try { return await (await fetch(u, {cache: "no-store"})).json(); } catch (e) { return null; } };
  const wide = () => innerWidth >= 900;
  const fmt = n => n >= 1048576 ? (n / 1048576).toFixed(1).replace(".0", "") + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
  const when = s => { const d = new Date(s * 1000); return d.toLocaleDateString() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); };
  let BMS = {};
  const chipTxt = (a, id) => { a.textContent = "🔊 " + t("Read aloud"); const b = BMS[id]; if (b) a.appendChild(E("i", "", "🔖 " + t("Ch.") + " " + (b.c + 1) + " · " + b.pct + " %")); };
  // Hooks chained (also «Eigene Orte» 639zzzzo): a part that holds the hook as getter / setter calls this one itself,
  // otherwise an earlier plain hook is called first (tzCard) or when this one does not open the file (tzOpen).
  const acc = n => { const d = Object.getOwnPropertyDescriptor(window, n); return !!(d && d.get); };
  const pc = !acc("tzCard") && typeof window.tzCard === "function" ? window.tzCard : null;
  const po = !acc("tzOpen") && typeof window.tzOpen === "function" ? window.tzOpen : null;
  window.tzCard = function (f, it, tx, th) {
    if (pc) { try { pc(f, it, tx, th); } catch (e) {} }
    if (f.ext === "epub" && !f.thumb && th && !th.querySelector("img")) th.textContent = "📖";
    if (!RD.has(f.ext) || !f.dl) return;
    const a = E("a", "vl-chip"); a.href = "/vorlesen?id=" + f.id; a.dataset.vl = f.id; chipTxt(a, f.id); tx.appendChild(a);
  };
  getJ("/api/vorlesen?bms=1").then(j => { BMS = (j && j.bms) || {}; document.querySelectorAll("a.vl-chip").forEach(a => chipTxt(a, a.dataset.vl)); });
  (async function cont() {                                // «▶ Weiter»: the story read last
    const j = await getJ("/api/vorlesen?last=1"); const l = j && j.last, tabs = document.querySelector(".tz-tabs");
    if (!l || !tabs || document.getElementById("vl-cont")) return;
    const k = E("div", "tz-card vl-cont"); k.id = "vl-cont";
    const tx = E("div", "tx"); tx.append(E("b", "", l.name), E("div", "mut", t("Last read") + " " + when(l.t) + " · " + t("Chapter") + " " + (l.c + 1) + " · " + l.pct + " %"));
    const pb = E("div", "vl-pbar"), pi = E("i"); pi.style.width = Math.max(2, l.pct) + "%"; pb.appendChild(pi); tx.appendChild(pb);
    const b = E("a", "btn", "▶ " + t("Continue")); b.href = "/vorlesen?id=" + l.id;
    k.append(E("div", "ic", "📖"), tx, b); tabs.parentNode.insertBefore(k, tabs);
  })();
  // ---- the viewer ------------------------------------------------------------------------------------------------------------------
  function shell(f, info) {
    const ov = E("div", "tz-lb vw"), bar = E("div", "bar"), inf = E("div", "vw-info"), bd = E("div", "vw-bd");
    ov.id = "tz-viewer"; bar.appendChild(E("b", "", (IC[f.ext] || {image: "🖼", text: "📝", doc: "📄", pdf: "📕"}[f.kind] || "📦") + " " + f.name));
    const x = E("button", "sec", "✕"); x.type = "button"; x.title = t("Close");
    const close = () => { ov.remove(); document.removeEventListener("keydown", esc); };
    const esc = e => { if (e.key === "Escape") close(); }; document.addEventListener("keydown", esc); x.onclick = close;
    if (info) inf.appendChild(E("span", "", info));
    ov.append(bar, inf, bd); document.body.appendChild(ov);
    return {ov, bar, inf, bd, close, add: (el) => bar.insertBefore(el, x), x: bar.appendChild(x)};
  }
  const meta = f => [f.by, when(f.t), fmt(f.size)].filter(Boolean).join(" · ");
  function dlBtn(V, f) { if (!f.dl) return; const a = E("a", "btn sec", wide() ? "⬇ " + t("Download") : "⬇"); a.href = "/tausch/dl/" + f.id; a.setAttribute("download", ""); a.title = t("Download"); V.add(a); }
  function readBtn(V, f) { if (!RD.has(f.ext) || !f.dl) return; const a = E("a", "btn", "🔊 " + (wide() ? t("Read aloud") : "")); a.href = "/vorlesen?id=" + f.id; a.title = t("Read aloud");
    a.onclick = () => setTimeout(V.close, 50); V.add(a); }
  function tabs(V, names, on, cb) {
    const tb = E("div", "tz-tabs"); names.forEach((n, i) => { const b = E("button", i === on ? "on" : "", n); b.type = "button";
      b.onclick = () => { tb.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b)); cb(i); }; tb.appendChild(b); }); V.inf.appendChild(tb);
  }
  function lines(pre, text, hl) {                          // monospace with line numbers (and JSON colours), only text nodes
    const re = /("(?:\\.|[^"\\])*")(\s*:)?|(-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b)|\b(true|false|null)\b/g;
    String(text).split("\n").slice(0, 20000).forEach((l, i) => {
      pre.appendChild(E("span", "ln", String(i + 1)));
      if (!hl) { pre.appendChild(document.createTextNode(l + "\n")); return; }
      let k = 0, m; re.lastIndex = 0;
      while ((m = re.exec(l))) { if (m.index > k) pre.appendChild(document.createTextNode(l.slice(k, m.index)));
        if (m[1]) { pre.appendChild(E("span", m[2] ? "k" : "s", m[1])); if (m[2]) pre.appendChild(document.createTextNode(m[2])); }
        else pre.appendChild(E("span", m[3] ? "n" : "b", m[0])); k = re.lastIndex; }
      pre.appendChild(document.createTextNode(l.slice(k) + "\n"));
    });
  }
  function csv(text) {                                     // a small CSV reader: quotes, ; , or tab
    const first = text.split("\n", 1)[0], seps = [";", ",", "\t"], sep = seps.reduce((a, b) => (first.split(b).length > first.split(a).length ? b : a), ",");
    const rows = []; let row = [], cell = "", q = false;
    for (let i = 0; i < text.length && rows.length < 5001; i++) {
      const ch = text[i];
      if (q) { if (ch === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += ch; continue; }
      if (ch === '"') q = true; else if (ch === sep) { row.push(cell); cell = ""; } else if (ch === "\n") { row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = ""; } else cell += ch;
    }
    if (cell || row.length) { row.push(cell.replace(/\r$/, "")); rows.push(row); }
    return {rows, sep};
  }
  function table(V, text, cut) {
    const {rows, sep} = csv(text); if (!rows.length) return;
    const head = rows[0], body = rows.slice(1, 5001);
    V.inf.appendChild(E("span", "", t("Data table") + " · " + body.length + " " + t("rows") + " · " + head.length + " " + t("columns") + " · «" + (sep === "\t" ? "Tab" : sep) + "»" + (cut || rows.length > 5000 ? " · " + t("only the start") : "")));
    const tb = E("table", "vw-tbl"), hr = E("tr"); hr.appendChild(E("th", "", "#")); const tbody = E("tbody");
    let by = -1, up = true;
    const num = s => /^\s*-?[\d'’ ]*[.,]?\d+\s*%?\s*$/.test(s);
    const fill = () => { tbody.textContent = ""; body.forEach((r, j) => { const tr = E("tr"); tr.appendChild(E("td", "i", String(j + 1)));
      head.forEach((_h, k) => { const c = r[k] || ""; const td = E("td", num(c) ? "n" : "", c); td.title = c; tr.appendChild(td); }); tbody.appendChild(tr); }); };
    head.forEach((h, k) => { const th = E("th", "", h); th.onclick = () => { up = by === k ? !up : true; by = k;
      const v = s => { const x = parseFloat(String(s).replace(/['’ ]/g, "").replace(",", ".")); return isNaN(x) ? null : x; };
      body.sort((a, b) => { const x = v(a[k]), y = v(b[k]); const r = x != null && y != null ? x - y : String(a[k] || "").localeCompare(String(b[k] || ""), undefined, {numeric: true});
        return up ? r : -r; });
      hr.querySelectorAll("th").forEach((z, i) => { z.textContent = i ? head[i - 1] + (i - 1 === by ? (up ? " ▴" : " ▾") : "") : "#"; }); fill(); }; hr.appendChild(th); });
    const th0 = E("thead"); th0.appendChild(hr); tb.append(th0, tbody); fill(); V.bd.appendChild(tb);
  }
  function book(V, f, j) {
    if (j.error) {
      const h = E("div", "vw-hint", "⚠ " + j.error); V.bd.appendChild(h);
      if (j.need === "poppler") poppler(h, j);
      return;
    }
    let ci = 0; const rd = E("div", "vw-read");
    const show = i => { ci = i; rd.textContent = ""; const c = j.ch[i]; rd.appendChild(E("h2", "", c.t || (j.ch.length > 1 ? t("Chapter") + " " + (i + 1) : j.title)));
      c.p.forEach(p => rd.appendChild(E("p", "", p))); V.bd.scrollTop = 0;
      if (toc) toc.querySelectorAll("a").forEach((a, k) => a.classList.toggle("on", k === i)); if (sel) sel.value = String(i); };
    let toc = null, sel = null;
    const wrap = E("div");
    if (j.ch.length > 1 && wide()) { const bk = E("div", "vw-book"); toc = E("div", "vw-toc"); toc.appendChild(E("h4", "", t("Contents")));
      j.ch.forEach((c, i) => { const a = E("a", "", (i + 1) + ". " + (c.t || t("Chapter") + " " + (i + 1))); a.onclick = () => show(i); toc.appendChild(a); }); bk.append(toc, rd); wrap.appendChild(bk); }
    else { if (j.ch.length > 1) { sel = E("select", "vw-sel"); j.ch.forEach((c, i) => { const o = E("option", "", (i + 1) + ". " + (c.t || t("Chapter") + " " + (i + 1))); o.value = String(i); sel.appendChild(o); });
      sel.onchange = () => show(+sel.value); wrap.appendChild(sel); } wrap.appendChild(rd); }
    show(0);
    if (j.ext === "docx") V.bd.appendChild(E("div", "vw-hint", "📄 " + t("Word file as text: headings and paragraphs - without pictures, tables and fonts. The original: ⬇")));
    if (j.ext !== "pdf") { V.bd.appendChild(wrap); return; }
    const pages = E("div", "vw-pages");
    if (j.tool && j.pages) for (let n = 1; n <= j.pages; n++) { const fg = E("figure"), im = E("img"); im.loading = "lazy"; im.alt = t("Page") + " " + n; im.src = "/tausch/seite/" + f.id + "/" + n + ".jpg";
      fg.append(im, E("figcaption", "", t("Page") + " " + n + " / " + j.pages)); pages.appendChild(fg); }
    const pv = E("div"); pv.appendChild(pages);
    if (!j.tool) { const h = E("div", "vw-hint", "⚠ " + t("Showing PDF pages needs poppler-utils on MoveEye.")); pv.appendChild(h); poppler(h, j); }
    else pv.appendChild(E("div", "vw-hint", "🔒 " + t("MoveEye draws the pages as pictures - the PDF itself never runs in the browser.")));
    tabs(V, ["📄 " + t("Pages"), "📝 " + t("Text only")], 0, i => { V.bd.textContent = ""; V.bd.appendChild(i ? wrap : pv); });
    V.bd.appendChild(pv);
  }
  function poppler(box, j) {
    if (!j.admin) { box.appendChild(E("div", "", t("The administrator can install it here with one tap."))); return; }
    const b = E("button", "", "⬇ " + t("Install poppler-utils (about 2 MB)")); b.type = "button"; box.appendChild(E("br")); box.appendChild(b);
    const st = E("div", "mut"); box.appendChild(st);
    b.onclick = async () => { b.disabled = true; const r = await post("/api/vorlesen", {action: "poppler", lang: LANG}); if (!r.ok) { st.textContent = r.error || "?"; b.disabled = false; return; }
      st.textContent = t("installing …");
      const iv = setInterval(async () => { const s = await getJ("/api/vorlesen?on=1&lang=" + LANG); const x = s && s.inst;
        if (x && x !== "running") { clearInterval(iv); st.textContent = x === "done" ? "✓ " + t("Installed - open the file again.") : "⚠ " + x; b.disabled = x === "done"; } }, 3000); };
  }
  function info(V, f, j) {
    const u = E("div", "vw-unk"); u.append(E("div", "ic", IC[f.ext] || "📦"), E("b", "", f.risky || (j && j.risky) ? t("No preview for this kind of file (for safety only as download).")
      : OFFICE.has(f.ext) ? t("No view for this kind of file yet - open it with an app on your phone or computer.") : t("No view for this kind of file.")));
    const dl = E("dl"); [[t("Name"), f.name], [t("Kind"), "." + (f.ext || "?") + (j && j.binary ? " · " + t("no readable text") : "")], [t("Size"), fmt(f.size)],
      [t("Uploaded"), [f.by, when(f.t)].filter(Boolean).join(" · ")]].forEach(([a, b]) => dl.append(E("dt", "", a), E("dd", "", b)));
    u.appendChild(dl);
    if (f.dl) { const a = E("a", "btn", "⬇ " + t("Download")); a.href = "/tausch/dl/" + f.id; a.setAttribute("download", ""); u.appendChild(a); }
    V.bd.appendChild(u);
  }
  window.tzOpen = function (f, H) { if (vlOpen(f, H)) return true; return po ? po(f, H) : false; };
  const vlOpen = function (f, H) {
    if (f.kind === "video" || f.kind === "audio" || f.kind === "chat") return false;
    if (f.kind === "image") return false;                // pictures: the preview of 639zzc (with 🌿 Bestimmen) stays
    if (!f.dl || f.risky || (!RD.has(f.ext) && f.kind !== "text" && !["csv", "tsv", "json"].includes(f.ext) && f.kind !== "doc") || OFFICE.has(f.ext)) {
      const V = shell(f, meta(f)); dlBtn(V, f); info(V, f, null); return true;
    }
    const V = shell(f, meta(f)); readBtn(V, f); dlBtn(V, f);
    if (f.kind === "text" && f.edit) { const b = E("button", "sec", "✎ " + (wide() ? t("Edit") : "")); b.type = "button"; b.title = t("Edit"); b.onclick = () => { V.close(); H.openText(f); }; V.add(b); }
    const ld = E("div", "vw-hint", t("loading …")); V.bd.appendChild(ld);
    getJ("/api/tausch/ansicht?id=" + f.id + "&lang=" + LANG).then(j => {
      ld.remove();
      if (!j || !j.ok) { V.bd.appendChild(E("div", "vw-hint", "⚠ " + ((j && j.error) || t("No connection to MoveEye.")))); return; }
      if (j.type === "text") { const d = E("div", j.md ? "vw-read tz-md" : "vw-read plain"); if (j.md && window.tzMd) d.innerHTML = tzMd(j.text); else d.textContent = j.text; V.bd.appendChild(d); }
      else if (j.type === "table") table(V, j.text, j.cut);
      else if (j.type === "json") { let s = j.text, ok = true; try { s = JSON.stringify(JSON.parse(j.text), null, 2); } catch (e) { ok = false; }
        V.inf.appendChild(E("span", "", "JSON · " + (ok ? t("valid") : "⚠ " + t("not valid - shown as it is")))); const pre = E("pre", "vw-code"); lines(pre, s, true); V.bd.appendChild(pre); }
      else if (j.type === "code") { const pre = E("pre", "vw-code"); lines(pre, j.text, false); V.bd.appendChild(pre); }
      else if (j.type === "book") book(V, f, j);
      else info(V, f, j);
      if (j.cut) V.bd.appendChild(E("div", "vw-hint", t("Only the start is shown - download the file for all of it.")));
    });
    return true;
  };
})();
</script>"""


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_VL = {
    "Read aloud": ("Vorlesen", "Lecture à voix haute", "Lettura ad alta voce", "Leger ad auta vusch"),
    "Reading aloud - to the reader": ("Vorlesen läuft – zum Vorleser", "Lecture en cours – vers le lecteur", "Lettura in corso – al lettore", "Leger en curs – tar il lectur"),
    "Digital backpack": ("Digitaler Rucksack", "Sac à dos numérique", "Zaino digitale", "Satgados digital"),
    "The voice does not answer.": ("Die Stimme antwortet nicht.", "La voix ne répond pas.", "La voce non risponde.", "La vusch na respunda betg."),
    "Nothing to read yet. Choose a story in the Digital backpack: «🔊 Read aloud».": (
        "Noch nichts zum Vorlesen. Wähle im Digitalen Rucksack eine Geschichte: «🔊 Vorlesen».",
        "Rien à lire pour l’instant. Choisis une histoire dans le Sac à dos numérique : «🔊 Lecture à voix haute».",
        "Ancora niente da leggere. Scegli una storia nello Zaino digitale: «🔊 Lettura ad alta voce».",
        "Anc nagut da leger. Tscherna ina istorgia en il Satgados digital: «🔊 Leger ad auta vusch»."),
    "Contents": ("Inhalt", "Sommaire", "Indice", "Cuntegn"),
    "Text size": ("Schriftgrösse", "Taille du texte", "Dimensione del testo", "Grondezza da la scrittira"),
    "Speed": ("Tempo", "Vitesse", "Velocità", "Tempo"),
    "Where": ("Wo", "Où", "Dove", "Nua"),
    "Phone": ("Handy", "Téléphone", "Telefono", "Telefonin"),
    "Chapter": ("Kapitel", "Chapitre", "Capitolo", "Chapitel"),
    "Ch.": ("Kap.", "Chap.", "Cap.", "Chap."),
    "Paragraph": ("Absatz", "Paragraphe", "Paragrafo", "Alinea"),
    "From the start": ("Von vorn", "Depuis le début", "Dall’inizio", "Da l’entschatta"),
    "Next chapter": ("Nächstes Kapitel", "Chapitre suivant", "Capitolo successivo", "Proxim chapitel"),
    "Bookmark": ("Lesezeichen", "Marque-page", "Segnalibro", "Segnapagina"),
    "MoveEye remembers where you stop - for you, on every device.": (
        "MoveEye merkt sich, wo du aufhörst – für dich, auf jedem Gerät.", "MoveEye retient où tu t’arrêtes – pour toi, sur chaque appareil.",
        "MoveEye ricorda dove ti fermi – per te, su ogni dispositivo.", "MoveEye sa regorda nua che ti chalas – per tai, sin mintga apparat."),
    "Pause": ("Pause", "Pause", "Pausa", "Pausa"),
    "Reading on the loudspeaker needs the right «Siren / sounds».": (
        "Vorlesen auf dem Lautsprecher braucht das Recht «Sirene / Töne».", "La lecture sur le haut-parleur nécessite le droit «Sirène / sons».",
        "La lettura sull’altoparlante richiede il diritto «Sirena / suoni».", "Leger sin l’autpledader dovra il dretg «Sirena / tuns»."),
    "Plays in this browser - also on the other pages (📖 at the top).": (
        "Spielt in diesem Browser – auch auf den anderen Seiten (📖 oben).", "Joue dans ce navigateur – aussi sur les autres pages (📖 en haut).",
        "Suona in questo browser – anche sulle altre pagine (📖 in alto).", "Suna en quest navigatur – er sin las autras paginas (📖 survart)."),
    "Plays on the loudspeaker of MoveEye.": ("Spielt auf dem Lautsprecher von MoveEye.", "Joue sur le haut-parleur de MoveEye.",
                                             "Suona sull’altoparlante di MoveEye.", "Suna sin l’autpledader da MoveEye."),
    "Last read": ("Zuletzt vorgelesen", "Dernière lecture", "Ultima lettura", "L’ultima giada legì"),
    "Continue": ("Weiter", "Continuer", "Continua", "Vinavant"),
    "Data table": ("Tabelle", "Tableau", "Tabella", "Tabella"),
    "rows": ("Zeilen", "lignes", "righe", "lingias"),
    "columns": ("Spalten", "colonnes", "colonne", "colonnas"),
    "only the start": ("nur der Anfang", "seulement le début", "solo l’inizio", "mo l’entschatta"),
    "Word file as text: headings and paragraphs - without pictures, tables and fonts. The original: ⬇": (
        "Word-Datei als Text: Überschriften und Absätze – ohne Bilder, Tabellen und Schriften. Das Original: ⬇",
        "Fichier Word en texte : titres et paragraphes – sans images, tableaux ni polices. L’original : ⬇",
        "File Word come testo: titoli e paragrafi – senza immagini, tabelle e caratteri. L’originale: ⬇",
        "Datoteca Word sco text: titels ed alineas – senza maletgs, tabellas e scrittiras. L’original: ⬇"),
    "Page": ("Seite", "Page", "Pagina", "Pagina"),
    "Pages": ("Seiten", "Pages", "Pagine", "Paginas"),
    "Text only": ("Nur Text", "Texte seul", "Solo testo", "Mo text"),
    "Showing PDF pages needs poppler-utils on MoveEye.": ("Für PDF-Seiten braucht MoveEye poppler-utils.", "Pour afficher les pages PDF, MoveEye a besoin de poppler-utils.",
                                                          "Per mostrare le pagine PDF MoveEye ha bisogno di poppler-utils.", "Per mussar paginas PDF dovra MoveEye poppler-utils."),
    "MoveEye draws the pages as pictures - the PDF itself never runs in the browser.": (
        "MoveEye zeichnet die Seiten als Bilder – das PDF selbst läuft nie im Browser.", "MoveEye dessine les pages en images – le PDF lui-même ne s’exécute jamais dans le navigateur.",
        "MoveEye disegna le pagine come immagini – il PDF stesso non viene mai eseguito nel browser.", "MoveEye dissegna las paginas sco maletgs – il PDF sez na vegn mai exequì en il navigatur."),
    "The administrator can install it here with one tap.": ("Der Administrator kann es hier mit einem Tipp installieren.", "L’administrateur peut l’installer ici d’un toucher.",
                                                            "L’amministratore può installarlo qui con un tocco.", "L’administratur po l’installar qua cun in tip."),
    "Install poppler-utils (about 2 MB)": ("poppler-utils installieren (ca. 2 MB)", "Installer poppler-utils (env. 2 Mo)", "Installa poppler-utils (circa 2 MB)",
                                           "Installar poppler-utils (ca. 2 MB)"),
    "installing …": ("wird installiert …", "installation …", "installazione …", "vegn installà …"),
    "Installed - open the file again.": ("Installiert – die Datei nochmals öffnen.", "Installé – rouvre le fichier.", "Installato – apri di nuovo il file.", "Installà – avra danovamain la datoteca."),
    "No view for this kind of file yet - open it with an app on your phone or computer.": (
        "Für diese Art Datei gibt es noch keine Ansicht – öffne sie mit einer App auf dem Handy oder Computer.",
        "Pas encore d’affichage pour ce type de fichier – ouvre-le avec une app sur ton téléphone ou ordinateur.",
        "Per questo tipo di file non c’è ancora una vista – aprilo con un’app sul telefono o sul computer.",
        "Per quest tip da datoteca na datti anc nagina vista – avra ella cun ina app sin il telefonin u il computer."),
    "No view for this kind of file.": ("Für diese Art Datei gibt es keine Ansicht.", "Pas d’affichage pour ce type de fichier.", "Nessuna vista per questo tipo di file.",
                                       "Nagina vista per quest tip da datoteca."),
    "Kind": ("Art", "Type", "Tipo", "Tip"),
    "no readable text": ("keine lesbare Schrift", "pas de texte lisible", "nessun testo leggibile", "nagin text legibel"),
    "Uploaded": ("Hochgeladen", "Téléversé", "Caricato", "Chargià si"),
    "loading …": ("lädt …", "chargement …", "caricamento …", "chargia …"),
    "valid": ("gültig", "valide", "valido", "valid"),
    "not valid - shown as it is": ("nicht gültig – so gezeigt, wie es ist", "non valide – affiché tel quel", "non valido – mostrato così com’è", "betg valid – mussà sco ch’el è"),
    "Only the start is shown - download the file for all of it.": ("Nur der Anfang wird gezeigt – für alles die Datei herunterladen.",
                                                                    "Seul le début est affiché – télécharge le fichier pour tout voir.",
                                                                    "Si vede solo l’inizio – scarica il file per vedere tutto.",
                                                                    "Mo l’entschatta vegn mussada – chargia giu la datoteca per tut."),
    "this kind of file cannot be read aloud": ("diese Art Datei kann nicht vorgelesen werden", "ce type de fichier ne peut pas être lu à voix haute",
                                               "questo tipo di file non può essere letto ad alta voce", "quest tip da datoteca na po betg vegnir legì ad auta vusch"),
    "This file cannot be read (damaged or protected).": ("Diese Datei lässt sich nicht lesen (beschädigt oder geschützt).", "Ce fichier ne peut pas être lu (endommagé ou protégé).",
                                                         "Questo file non può essere letto (danneggiato o protetto).", "Questa datoteca na po betg vegnir legida (donnegiada u protegida)."),
    "old voice": ("alte Stimme", "ancienne voix", "voce vecchia", "vusch veglia"),
    "No Piper voice loaded for the language of the book - read with the voice of the page.": (
        "Keine Piper-Stimme für die Sprache des Buchs geladen – gelesen mit der Stimme der Seite.",
        "Aucune voix Piper chargée pour la langue du livre – lu avec la voix de la page.",
        "Nessuna voce Piper caricata per la lingua del libro – letto con la voce della pagina.",
        "Nagina vusch Piper chargiada per la lingua dal cudesch – legì cun la vusch da la pagina."),
    "No Piper voice loaded - the old voice reads (Settings › Light & sound › Loudspeaker).": (
        "Keine Piper-Stimme geladen – die alte Stimme liest (Einstellungen › Licht & Ton › Lautsprecher).",
        "Aucune voix Piper chargée – l’ancienne voix lit (Réglages › Lumière et son › Haut-parleur).",
        "Nessuna voce Piper caricata – legge la voce vecchia (Impostazioni › Luce e suono › Altoparlante).",
        "Nagina vusch Piper chargiada – la vusch veglia legia (Parameters › Glisch e tun › Autpledader)."),
    "Paused: alarm - it reads on when it is quiet": ("Pausiert: Alarm – es liest weiter, sobald es ruhig ist", "En pause : alarme – la lecture reprend quand c’est calme",
                                                     "In pausa: allarme – riprende quando è tranquillo", "En pausa: alarm – i legia vinavant uschè gartg ch’igl è quiet"),
    "the storage (USB stick / SSD) is not there": ("der Speicher (USB-Stick / SSD) ist nicht da", "le stockage (clé USB / SSD) n’est pas là",
                                                   "la memoria (chiavetta USB / SSD) non c’è", "la memoria (stick USB / SSD) n’è betg qua"),
    "pdftotext is missing (poppler-utils)": ("pdftotext fehlt (poppler-utils)", "pdftotext manque (poppler-utils)", "manca pdftotext (poppler-utils)", "pdftotext manca (poppler-utils)"),
    "no text found (a scanned PDF? pictures are not read)": ("kein Text gefunden (ein gescanntes PDF? Bilder werden nicht gelesen)",
                                                             "aucun texte trouvé (un PDF scanné ? les images ne sont pas lues)",
                                                             "nessun testo trovato (un PDF scansionato? le immagini non vengono lette)",
                                                             "nagin text chattà (in PDF scannà? maletgs na vegnan betg legids)"),
    "nothing is being read": ("es wird nichts vorgelesen", "rien n’est lu", "non si sta leggendo nulla", "i na vegn legì nagut"),
    "no apt-get on this system - install poppler-utils by hand": ("kein apt-get auf diesem System – poppler-utils von Hand installieren",
                                                                  "pas d’apt-get sur ce système – installe poppler-utils à la main",
                                                                  "nessun apt-get su questo sistema – installa poppler-utils a mano",
                                                                  "nagin apt-get sin quest sistem – installar poppler-utils a maun"),
    "MoveEye has no rights for apt (sudo asks for a password) - in a terminal: sudo apt install poppler-utils": (
        "MoveEye hat keine Rechte für apt (sudo will ein Passwort) – im Terminal: sudo apt install poppler-utils",
        "MoveEye n’a pas les droits pour apt (sudo demande un mot de passe) – dans un terminal : sudo apt install poppler-utils",
        "MoveEye non ha i diritti per apt (sudo chiede una password) – in un terminale: sudo apt install poppler-utils",
        "MoveEye n’ha nagins dretgs per apt (sudo dumonda in pled-clav) – en in terminal: sudo apt install poppler-utils"),
    "no voice": ("keine Stimme", "pas de voix", "nessuna voce", "nagina vusch"),
    "unknown sentence": ("unbekannter Satz", "phrase inconnue", "frase sconosciuta", "frasa nunenconuschenta"),
    "Choose a story (browser)": ("Geschichte wählen (Browser)", "Choisir une histoire (navigateur)", "Scegli una storia (browser)", "Tscherner ina istorgia (navigatur)"),
    "Nothing is being read on the loudspeaker.": ("Auf dem Lautsprecher wird nichts vorgelesen.", "Rien n’est lu sur le haut-parleur.",
                                                  "Sull’altoparlante non si legge nulla.", "Sin l’autpledader na vegn legì nagut."),
}
for _k, _v in _HX_VL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_VL_DE = {_k: DE.get(_k, _v[0]) for _k, _v in _HX_VL.items()}
_VL_DE.update({k: DE[k] for k in ("Download", "Close", "Edit", "Name", "Size", "Stop", "Volume", "No connection to MoveEye.",
                                  "No preview for this kind of file (for safety only as download).") if DE.get(k)})

# ---- the manual: a section «Vorlesen und Datei-Ansicht» ----------------------------------------------------------------------------
_HELP_VL = {
    "de": ('<section id="vorlesen" data-icon="📖"><h2>Vorlesen und Datei-Ansicht</h2><ul>'
           '<li><b>Vorlesen:</b> im Digitalen Rucksack bei Texten (.txt, .md), E-Books (.epub), Word (.docx) und PDF (nur der Text) «🔊 Vorlesen». '
           'Die Piper-Stimme liest Satz für Satz, der Satz ist im Text markiert; ein Tipp auf einen Satz liest ab dort. Tempo 0,8× bis 1,3×, '
           '⏮ / ⏭ Kapitel, ↶ / ↷ Absatz, ☰ Inhalt, Aa Schriftgrösse.</li>'
           '<li><b>Wo:</b> «📱 Handy» spielt im Browser und liest weiter, wenn du andere Seiten öffnest (📖 oben im Kopf führt zurück; Sperrbildschirm: '
           'Titel und Knöpfe). «🔈 MoveEye» liest auf dem Lautsprecher (Recht «Sirene / Töne»), mit eigener Lautstärke; im Pi-Fenster: Mehr → «📖 Vorlesen».</li>'
           '<li><b>Lesezeichen:</b> MoveEye merkt sich pro Person und Datei, wo du aufhörst – auf jedem Gerät. Oben im Rucksack: «▶ Weiter».</li>'
           '<li><b>Vorrang:</b> Alarm, Sirene, Ansagen, Gegensprechen, Morse und der Wecker gehen vor – das Vorlesen pausiert (auch auf dem Handy) '
           'und liest danach den Satz nochmals. Radio und Vorlesen schliessen sich aus: startet das eine, stoppt das andere.</li>'
           '<li><b>Stimme:</b> nach der Sprache des Buchs, wenn deren Piper-Stimme geladen ist, sonst die Sprache der Seite (mit Hinweis). '
           'Stimmen laden: Einstellungen → Licht &amp; Ton → Lautsprecher.</li>'
           '<li><b>Datei-Ansicht:</b> ein Tipp auf eine Datei zeigt sie: Text und Markdown (mit «✎ Bearbeiten»), E-Book mit Inhalt, Word als Text, '
           'PDF als Seitenbilder oder nur Text, Bilder mit Zoom, CSV als Tabelle (Spalte antippen = sortieren), JSON und Code mit Zeilennummern. '
           'Andere Dateien (auch Excel, PowerPoint, OpenOffice): Info-Karte mit Download. Videos und Ton wie bisher.</li>'
           '<li><b>PDF:</b> MoveEye rechnet Seiten und Text selbst (poppler-utils); fehlt es, installiert es der Administrator mit einem Tipp. '
           'Ein gescanntes PDF hat keinen Text zum Vorlesen.</li>'
           '<li><b>Rechte:</b> ansehen und vorlesen darf, wer die Datei herunterladen darf. Gäste sehen weiter nur Vorschaubilder.</li>'
           '</ul></section>\n'),
    "en": ('<section id="vorlesen" data-icon="📖"><h2>Read aloud and file view</h2><ul>'
           '<li><b>Read aloud:</b> in the Digital backpack, for texts (.txt, .md), e-books (.epub), Word (.docx) and PDF (text only): «🔊 Read aloud». '
           'The Piper voice reads sentence by sentence, the sentence is marked in the text; tap a sentence to read from there. Speed 0.8× to 1.3×, '
           '⏮ / ⏭ chapter, ↶ / ↷ paragraph, ☰ contents, Aa text size.</li>'
           '<li><b>Where:</b> «📱 Phone» plays in the browser and keeps reading while you open other pages (📖 in the header leads back; lock screen: '
           'title and buttons). «🔈 MoveEye» reads on the loudspeaker (right «siren / sounds»), with its own volume; Pi window: More → «📖 Read aloud».</li>'
           '<li><b>Bookmark:</b> MoveEye remembers per person and file where you stop – on every device. At the top of the backpack: «▶ Continue».</li>'
           '<li><b>Priority:</b> alarm, siren, announcements, talking, Morse and the wake-up alarm go first – the reading pauses (also on the phone) '
           'and reads the sentence again afterwards. Radio and reading exclude each other: starting one stops the other.</li>'
           '<li><b>Voice:</b> by the language of the book if its Piper voice is loaded, otherwise the language of the page (with a hint). '
           'Load voices: Settings → Light &amp; sound → Loudspeaker.</li>'
           '<li><b>File view:</b> tap a file to see it: text and Markdown (with «✎ Edit»), e-book with contents, Word as text, PDF as page pictures or '
           'text only, pictures with zoom, CSV as a table (tap a column = sort), JSON and code with line numbers. Other files (also Excel, PowerPoint, '
           'OpenOffice): info card with download. Videos and sound as before.</li>'
           '<li><b>PDF:</b> MoveEye computes pages and text itself (poppler-utils); if it is missing, the administrator installs it with one tap. '
           'A scanned PDF has no text to read.</li>'
           '<li><b>Rights:</b> whoever may download the file may view it and have it read. Guests still see only preview pictures.</li>'
           '</ul></section>\n'),
    "fr": ('<section id="vorlesen" data-icon="📖"><h2>Lecture à voix haute et affichage des fichiers</h2><ul>'
           '<li>Dans le Sac à dos numérique, pour les textes (.txt, .md), livres numériques (.epub), Word (.docx) et PDF (texte seul) : «🔊 Lecture à voix haute». '
           'La voix Piper lit phrase par phrase, la phrase est marquée ; vitesse, chapitres, paragraphes, sommaire.</li>'
           '<li>«📱 Téléphone» joue dans le navigateur, aussi sur les autres pages (📖 en haut) ; «🔈 MoveEye» lit sur le haut-parleur (droit «sirène / sons»).</li>'
           '<li>Marque-page par personne et fichier, sur chaque appareil ; «▶ Continuer» en haut du sac à dos.</li>'
           '<li>Alarme, sirène, annonces, morse et réveil passent avant : la lecture fait une pause. Radio et lecture s’excluent.</li>'
           '<li>Toucher un fichier l’affiche : texte, livre, Word, pages PDF (poppler-utils), images, tableaux CSV, JSON et code ; autres fichiers : fiche et téléchargement.</li>'
           '</ul></section>\n'),
    "it": ('<section id="vorlesen" data-icon="📖"><h2>Lettura ad alta voce e vista dei file</h2><ul>'
           '<li>Nello Zaino digitale, per testi (.txt, .md), e-book (.epub), Word (.docx) e PDF (solo testo): «🔊 Lettura ad alta voce». '
           'La voce Piper legge frase per frase, la frase è evidenziata; velocità, capitoli, paragrafi, indice.</li>'
           '<li>«📱 Telefono» suona nel browser, anche sulle altre pagine (📖 in alto); «🔈 MoveEye» legge sull’altoparlante (diritto «sirena / suoni»).</li>'
           '<li>Segnalibro per persona e file, su ogni dispositivo; «▶ Continua» in cima allo zaino.</li>'
           '<li>Allarme, sirena, annunci, Morse e sveglia hanno la precedenza: la lettura fa una pausa. Radio e lettura si escludono.</li>'
           '<li>Toccare un file lo mostra: testo, libro, Word, pagine PDF (poppler-utils), immagini, tabelle CSV, JSON e codice; altri file: scheda e download.</li>'
           '</ul></section>\n'),
    "rm": ('<section id="vorlesen" data-icon="📖"><h2>Leger ad auta vusch e vista da datotecas</h2><ul>'
           '<li>En il Satgados digital, per texts (.txt, .md), e-books (.epub), Word (.docx) e PDF (mo text): «🔊 Leger ad auta vusch». '
           'La vusch Piper legia frasa per frasa, la frasa è marcada; tempo, chapitels, alineas, cuntegn.</li>'
           '<li>«📱 Telefonin» suna en il navigatur, er sin autras paginas (📖 survart); «🔈 MoveEye» legia sin l’autpledader (dretg «sirena / tuns»).</li>'
           '<li>Segnapagina per persuna e datoteca, sin mintga apparat; «▶ Vinavant» survart en il satgados.</li>'
           '<li>Alarm, sirena, annunzias, morse e svegliarin han la precedenza: il leger fa pausa. Radio e leger s’excludan.</li>'
           '<li>Tutgar ina datoteca la mussa: text, cudesch, Word, paginas PDF (poppler-utils), maletgs, tabellas CSV, JSON e code; autras datotecas: carta e download.</li>'
           '</ul></section>\n'),
}


def _help_vl(doc, lang):
    if 'id="vorlesen"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_VL[lang] + doc[i:] if i >= 0 else doc


_hp_en_vl = HELP_PAGE.find('<div lang="en">')
if _hp_en_vl > 0:
    HELP_PAGE = _help_vl(HELP_PAGE[:_hp_en_vl], "de") + _help_vl(HELP_PAGE[_hp_en_vl:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_vl(HELP_X[_L], _L)


# ---- self-test (no network, no process) -------------------------------------------------------------------------------------------
def vorlesen_selftest():
    assert vl_saetze("Er kam um ca. 8 Uhr. «Hallo!» Dann ging er, z. B. nach Hause.") == ["Er kam um ca. 8 Uhr.", "«Hallo!»", "Dann ging er, z. B. nach Hause."]
    long_ = "Wort, " * 80 + "Ende."
    assert all(len(x) <= 281 for x in vl_saetze(long_)) and len(vl_saetze(long_)) >= 2, "long sentences are split"
    k = vl_from_text("Titel\n\nKapitel 1: Anfang\n\nEins zwei.\nDrei.\n\nKapitel 2\n\nVier.")
    assert [x["t"] for x in k] == ["", "Kapitel 1: Anfang", "Kapitel 2"] and k[1]["p"] == ["Eins zwei. Drei."], k
    k = vl_from_text("# Titel\n\n**Fett** und [Link](http://x.example)\n\n```\ncode\n```\n\n- Punkt", md=True)
    assert k[0]["t"] == "Titel" and k[0]["p"] == ["Fett und Link", "Punkt"], k
    assert vl_decode("Grüsse".encode("cp1252")) == "Grüsse" and vl_decode("﻿ä".encode("utf-8")) == "ä"
    assert vl_lang_guess("the cat and the dog is in the house of the king and the queen") == "en"
    assert vl_lang_guess("der Hund und die Katze ist nicht mit dem Fuchs auf der Wiese") == "de"
    h = _VlHtml(); h.feed("<html><head><title>x</title><script>alert(1)</script></head><body><h1>Kap</h1><p>A <b>b</b>.</p><p>C</p></body></html>"); h.flush()
    assert h.head == "Kap" and h.out == ["A b.", "C"], (h.head, h.out)
    b = {"ch": [{"t": "", "p": [["a", "b"], ["c"]]}, {"t": "", "p": [["d"]]}], "n": [3, 1], "total": 4}
    assert vl_next(b, 0, 2) == (1, 0) and vl_next(b, 1, 0) is None and vl_sentence(b, 0, 1) == ("b", True) and vl_sentence(b, 0, 0) == ("a", False)
    keep = {k_: VL[k_] for k_ in ("hold_t", "hold_why", "alarm_t", "want")}
    snd = dict(SOUND)
    try:
        VL.update(hold_t=0.0, alarm_t=0.0, want=False); SOUND["playing"] = False
        SOUND.update(playing=True, kind="siren"); assert vl_held() == "siren", "the siren goes first"
        SOUND["playing"] = False; VL["alarm_t"] = time.time(); assert vl_held() == "alarm", "an alarm pauses the reading"
        VL["alarm_t"] = 0.0; radio_yield("voice"); assert vl_held() == "voice", "after an announcement: a short gap"
    finally:
        SOUND.clear(); SOUND.update(snd); VL.update(keep)
    for p_ in ("/vorlesen", "/api/vorlesen", "/api/vorlesen/audio", "/api/tausch/ansicht", "/tausch/seite/0123456789abcdef/1.jpg"):
        assert role_allows("friend", p_, "GET", {}) and not role_allows("kid", p_, "GET", {}), "rights: " + p_
    assert role_allows("family", "/api/vorlesen", "POST", {"action": "bm"}) and not role_allows("kid", "/api/vorlesen", "POST", {"action": "bm"})
    assert vl_pi_may("admin", None) and vl_pi_may("custom", ["siren"]) and not vl_pi_may("friend", ROLE_PERMS.get("friend"))
    assert TZ_TYPES["epub"][1] == "doc" and TZ_TYPES["json"][0] == "application/json" and tausch_type("a.epub")[1] == "doc"
    assert all(DE.get(k_) and all(TRX[L].get(k_) for L in ("fr", "it", "rm")) for k_ in _HX_VL), "texts in 5 languages"
    assert "window.mwReadP = " in VL_PLAYER_JS and "/*VLPLAYER*/" in VL_PAGE and "window.tzOpen" in VL_TZ_JS and "mwk-read" in VL_SYM_JS
    h_ = render_page(MORE_PAGE, "more")
    assert h_.count('id="mwk-read"') == 1 and h_.count('id="mwk-radio"') == 1, "📖 and 📻 in the header"
    p_ = render_page(VL_PAGE, "more")
    assert "/*VLDE*/" not in p_ and "/*VLPLAYER*/" not in p_ and "window.mwReadP = " in p_ and DE["Read aloud"] in p_
    assert "getOwnPropertyDescriptor(window, n)" in VL_TZ_JS and "if (pc) { try { pc(" in VL_TZ_JS and "po ? po(f, H) : false" in VL_TZ_JS, "hooks chained"
    assert tausch_page_html().count("window.tzCard = function") == 1 and "/*VLDE*/" not in tausch_page_html(), "the viewer in /tausch"
    assert HELP_PAGE.count('id="vorlesen"') == 2 or '<section id="tips"' not in HELP_PAGE, "manual de / en"
    return "sentences, chapters, Markdown, epub HTML, priority (siren / alarm / announcement), rights, texts, pages"


SELFTEST_EXTRA.append(("Read aloud and file view in the Digital backpack (639zzzzv)", vorlesen_selftest))
