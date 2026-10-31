#@ MoveEye – Teil 012: Zusatzdaten laden (moveeye_daten_X_Y_Z.zip neben dem Programm: grosse Web-Seiten, Bilder, Übersetzungen, ältere Änderungen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Zusatzdaten (Paket «MoveEye-Datei verkleinern», Entscheid Daniel 31.10.2026): devices up to 2.98.x accept program files of
# at most 8 MiB. werkzeuge/bauen.py therefore moves the big literals of quelle/ (web pages, JavaScript, icons as base64,
# translations, the older part of the list of changes) into moveeye_daten_X_Y_Z.zip next to the program file and writes
# _zd("<key>", <fallback>) in their place. The sources in quelle/ stay unchanged; only the built file differs.
#   * The zip belongs to exactly one program file: its SHA-256 is written into the program (ZD_SHA256). The program file
#     is signed (versions.json), so the signature vouches for the zip too - a foreign or damaged zip is never used.
#   * Without the zip (an old device fetched only the .py) MoveEye starts in the core mode: camera, detection, alarms,
#     push and the window work; web pages show «Zusatzdaten fehlen – Update», texts fall back to English / German.
#     Part 397 fetches the zip over the same update source and restarts once (zusatz_start()).
# ZD_FILE / ZD_SHA256 are filled in by bauen.py (empty = nothing was moved out).
# ----------------------------------------------------------------------------
ZD_FILE = ""
ZD_SHA256 = ""
ZD = {"ok": False, "err": "", "path": "", "data": None, "miss": [], "used": 0}


class _ZDDict(dict):
    """the stand-in for a moved-out table while the zip is missing: empty, and a missing key gives "" (no crash)"""
    def __missing__(self, key):
        return ""


ZD_PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30"><title>MoveEye</title><style>body{margin:0;min-height:100vh;display:flex;align-items:center;
justify-content:center;background:#0b0f14;color:#e6edf3;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
text-align:center;padding:20px;box-sizing:border-box}.c{max-width:440px}.big{font-size:52px}.t{font-size:21px;font-weight:700;margin:6px 0}
.m{color:#8b9bb0}</style></head><body><div class="c"><div class="big">🛡</div>
<div class="t">Zusatzdaten fehlen – Update</div>
<div class="m">MoveEye läuft und schützt (Kamera, Erkennung, Alarm, Push). Die Web-Seiten, Bilder und Übersetzungen stecken in
der Zusatzdatei <b>moveeye_daten_….zip</b> neben dem Programm. MoveEye holt sie selbst über die Update-Quelle und startet
dann einmal neu. Ohne Internet: die Datei aus dem Update-Ordner (USB) neben das Programm legen.</div>
<div class="m" style="margin-top:14px">Additional data missing – update. MoveEye runs and protects; the web pages come back
by themselves once the data file is there. This page reloads every 30 s.</div></div></body></html>"""


def _zd_read(path, want_sha):
    """the entries {key: source text} of a data zip, or raises ValueError with the reason"""
    import zipfile as _zf
    with open(path, "rb") as f:
        raw = f.read(64 * 1024 * 1024 + 1)
    if want_sha and hashlib.sha256(raw).hexdigest() != want_sha:
        raise ValueError("checksum does not match this program (an other version or damaged)")
    import io as _io
    with _zf.ZipFile(_io.BytesIO(raw)) as z:
        d = json.loads(z.read("daten.json").decode("utf-8"))
    if str(d.get("version")) != APP_VERSION:
        raise ValueError("belongs to version %s" % d.get("version"))
    return d


def _zd_open():
    if not ZD_FILE:                                        # nothing moved out (built without data file)
        ZD.update(ok=True, data={})
        return
    p = os.path.join(HERE, ZD_FILE)
    ZD["path"] = p
    try:
        d = _zd_read(p, ZD_SHA256)
        ZD["data"] = {e[0]: e[2] for e in d["entries"]}
        ZD["ok"] = True
    except FileNotFoundError:
        ZD["err"] = "missing"
    except Exception as e:                                 # damaged / foreign zip: never used, the core runs
        ZD["err"] = ("%s: %s" % (e.__class__.__name__, e))[:200]


def _zd(key, fallback):
    """the moved-out literal <key> (evaluated exactly like the original source), or <fallback> without the zip"""
    data = ZD["data"]
    if data and key in data:
        import ast as _ast
        seg = data.pop(key)                                # used once - frees the memory
        try:
            v = _ast.literal_eval("(" + seg + "\n)")       # in brackets: implicit "a" "b" over several lines stays one literal
            ZD["used"] += 1
            return v
        except (ValueError, SyntaxError, MemoryError):
            pass
    ZD["miss"].append(key)
    return fallback


def zd_source():
    """the program text exactly as put together from quelle/ (the moved-out literals back in their place) - for the checks
    that read their own source (i18n keys 395, interface 558). Without the zip: the program file as it is."""
    with open(os.path.abspath(__file__), encoding="utf-8") as f:
        text = f.read()
    if not ZD_FILE:
        return text
    try:
        d = _zd_read(os.path.join(HERE, ZD_FILE), ZD_SHA256)
    except Exception:
        return text
    out, pos = [], 0
    for _k, ph, seg in d["entries"]:
        i = text.find(ph, pos)
        if i < 0:
            return text
        out.append(text[pos:i]); out.append(seg); pos = i + len(ph)
    out.append(text[pos:])
    return "".join(out)


_zd_open()
if ZD_FILE:
    __doc__ = _zd("000_kopf_aenderungen/__doc__", __doc__)   # the whole list of changes (the file keeps only the newest)
