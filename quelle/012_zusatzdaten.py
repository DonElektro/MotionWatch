#@ MoveEye – Teil 012: Zusatzdaten laden (moveeye_daten_X_Y_Z.zip neben dem Programm: grosse Web-Seiten, Bilder, Übersetzungen, ältere Änderungen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Zusatzdaten (Paket «MoveEye-Datei verkleinern», Entscheid Besitzer 31.10.2026): devices up to 2.98.x accept program files of
# at most 8 MiB. werkzeuge/bauen.py therefore moves the big literals of quelle/ (web pages, JavaScript, icons as base64,
# translations, the older part of the list of changes) into moveeye_daten_X_Y_Z.zip next to the program file and writes
# _zd("<key>", <fallback>) in their place. The sources in quelle/ stay unchanged; only the built file differs.
#   * The zip belongs to exactly one program file: its SHA-256 is written into the program (ZD_SHA256). The program file
#     is signed (versions.json), so the signature vouches for the zip too - a foreign or damaged zip is never used.
#   * Without the zip (an old device fetched only the .py) MoveEye starts in the core mode: camera, detection, alarms,
#     push and the window work; web pages show «Zusatzdaten fehlen – Update», texts fall back to English / German.
#     Part 397 fetches the zip over the same update source and restarts once (zusatz_start()).
#   * Schlank (3.59.0): the translation tables _HX… {English: (de, fr, it, rm)} keep only German in the file (_zd_hx below),
#     fr / it / rm come from the zip. Comments and the docstrings of functions / classes are not in the program file and
#     it is indented with tabs (same line numbers); the zip keeps the original lines ("zeilen"), zd_source() puts them back.
#   * Prüf-Code (Nov. 2026): the functions «…_selftest» that only «--self-test» uses are in the zip as source (_zd_fn below);
#     the file keeps one line per function and empty lines (same line numbers). The running device never needs them.
#     Second round (13.11.2026): also the helpers that only these checks use; French / Italian / Romansh from 256 bytes
#     on (German stays), tables _HX… with names as keys (_zd_hxk below), the pairs of the supplements of the manual.
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
<div class="m" style="margin-top:14px"><a href="/hilfe/fehler/DATA_MISSING" style="color:#58a6ff">Jetzt nachladen · Download now</a></div>
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


def _zd_fn(key):
    """Prüf-Code (Hauptdatei kleiner, Nov. 2026): the stand-in for a function «…_selftest» whose source bauen.py moved into
    the data zip (entry «part/name()»). Only «--self-test» calls these. The first call compiles the source with the line
    numbers of this file (the lines below the stand-in are empty), as a function of this program; the name keeps pointing
    to the stand-in (the same object as in SELFTEST_EXTRA), the function itself is stand_in.__wrapped__. The zip is only
    ever used when its SHA-256 is the one written into this signed program (ZD_SHA256).
    Without the zip the call fails with a clear text - the self-test then shows this check as failed."""
    name = key.rsplit("/", 1)[-1][:-2]
    line = sys._getframe(1).f_lineno
    box = []

    def stand_in(*a, **k):
        if not box:
            data = ZD["data"]
            if not (ZD["ok"] and ZD_SHA256 and data and key in data):
                if key not in ZD["miss"]:
                    ZD["miss"].append(key)
                raise RuntimeError("Zusatzdaten fehlen – additional data missing: the check %s() is in %s (update / repair)"
                                   % (name, ZD_FILE or "moveeye_daten_….zip"))
            g = stand_in.__globals__
            keep = g.get(name)
            exec(compile("\n" * (line - 1) + data.pop(key), os.path.abspath(__file__), "exec"), g)
            box.append(g[name])                            # (ZD["used"] counts the literals only)
            g[name] = keep                                 # the name stays the stand-in: one object everywhere
            stand_in.__wrapped__ = box[0]
        return box[0](*a, **k)
    stand_in.__name__ = stand_in.__qualname__ = name
    return stand_in


def _zd_hx(de, as_list=False):
    """Schlank: the stand-in for a moved-out table {English: (de, fr, it, rm)} while the zip is missing: German stays,
    French / Italian show English, Romansh German (the same as for a missing translation)"""
    return {k: ([v, k, k, v] if as_list else (v, k, k, v)) for k, v in de.items()}


def _zd_hxk(key, rows, as_list=False):
    """Hauptdatei kleiner, zweite Runde (13.11.2026): a table _HX… whose keys are names (PL_HEIC_MSG: (de, fr, it, rm), …).
    The file keeps the keys (evaluated here, in the program) and the German texts: rows = [(key, de), …] in the order of the
    source. The zip keeps the whole table as source; only its VALUES are read (ast.literal_eval of each value - the keys in
    the zip are never evaluated, nothing in the zip runs). They must match the rows (same number, same German), else - and
    without the zip - the table is the same as from _zd_hx (German, French / Italian English, Romansh German)."""
    data = ZD["data"]
    if data and key in data:
        import ast as _ast
        seg = data.pop(key)
        try:
            nd = _ast.parse("(" + seg + "\n)", mode="eval").body
            vals = [_ast.literal_eval(v) for v in nd.values] if isinstance(nd, _ast.Dict) else []
            if len(vals) == len(rows) and all(isinstance(v, (tuple, list)) and len(v) == 4 and v[0] == de
                                              for v, (_k, de) in zip(vals, rows)):
                ZD["used"] += 1
                out = {}
                for (k, _de), v in zip(rows, vals):
                    out[k] = list(v) if as_list else tuple(v)
                return out
        except (ValueError, SyntaxError, MemoryError, TypeError, RecursionError):
            pass
    ZD["miss"].append(key)
    out = {}
    for k, de in rows:
        out[k] = [de, k, k, de] if as_list else (de, k, k, de)
    return out


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
    if d.get("zeilen"):                                    # Schlank: indentation, comments and docstrings back (same lines)
        lines = []
        for ln in text.split("\n"):
            n = len(ln) - len(ln.lstrip("\t"))
            lines.append("    " * n + ln[n:] if n else ln)
        try:
            for row, orig in d["zeilen"]:
                lines[row - 1] = orig
        except (IndexError, TypeError, ValueError):
            return text
        text = "\n".join(lines)
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
