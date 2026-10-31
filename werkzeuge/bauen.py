#!/usr/bin/env python3
"""Setzt Motion Watch aus den Teilen in quelle/ zu der einen Datei webcam_bewegung_X_Y_Z.py zusammen.

Der Pi, die Update-Funktion und die Signatur arbeiten weiter mit dieser einen Datei; bearbeitet wird in quelle/.

  python3 werkzeuge/bauen.py                       # baut die Datei der aktuellen Version (APP_VERSION in quelle/010_grundlagen.py)
  python3 werkzeuge/bauen.py --pruefen             # nur vergleichen: passt die Datei im Repository zu quelle/? (GitHub-Prüfung)
                                                   # Beide prüfen auch: keine Funktion / Klasse in zwei Teilen (doppelte())
  python3 werkzeuge/bauen.py --neue-version "Text" # nächste Version (X.Y.Z+1): Nummer an allen Stellen, Zeile in der
                                                   #   Änderungsliste, Simulator-Version aus simulator3d/version.json, bauen
  python3 werkzeuge/bauen.py --neue-version "Text" --version 2.96.0     # eine bestimmte Nummer
  python3 werkzeuge/bauen.py --neue-version "Text" --stufe funktion      # ab 3.0.0: neue Funktion X.Y+1.0 (fehler = X.Y.Z+1,
                                                                         #   gross = X+1.0.0), siehe CLAUDE.md «Versionierung»
  python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI                 # danach: versions.json schreiben, signieren, Selbsttest
  python3 werkzeuge/bauen.py --groessen                                  # was braucht am meisten Platz? (Teile, Literale)

Zusatzdaten (31.10.2026, Paket «MoveEye-Datei verkleinern»): grosse Literale (Web-Seiten, JavaScript, Bilder als base64,
Übersetzungen) und der ältere Teil der Änderungsliste kommen beim Bauen in moveeye_daten_X_Y_Z.zip neben der Datei
(Geräte bis 2.98.x nehmen nur Programmdateien bis 8 MiB an). quelle/ bleibt unverändert; die grosse Datei lädt die ZIP
beim Start (Teil 012) und kennt ihre Prüfsumme (ZD_SHA256). Beide Dateien gehören zusammen ins Repository.

Den Schlüssel nie ins Repository legen.
"""
import argparse
import ast
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
QUELLE = os.path.join(REPO, "quelle")


def teile():
    return sorted(f for f in os.listdir(QUELLE) if f.endswith(".py") and f[:3].isdigit())


def lesen(name):
    with open(os.path.join(QUELLE, name), encoding="utf-8", newline="") as f:
        t = f.read()
    while t.startswith("#@"):                                  # the head line of the part is not part of the program
        t = t.split("\n", 1)[1] if "\n" in t else ""
    return t


def schreiben(name, text):
    with open(os.path.join(QUELLE, name), encoding="utf-8", newline="") as f:
        alt = f.read()
    head = ""
    while alt.startswith("#@"):
        line, alt = alt.split("\n", 1)
        head += line + "\n"
    with open(os.path.join(QUELLE, name), "w", encoding="utf-8", newline="") as f:
        f.write(head + text)


WRAPS_RE = re.compile(r"#\s*wraps:\s*([A-Za-z_][A-Za-z0-9_.]*)")


def _namen(name, text):
    """the top-level names of one part: [(name, line, kind, marked)] - def / class, and assignments to a name
    (only the ones that rebind a function: checked by the caller). marked = an intended wrapper (see doppelte())."""
    tree = ast.parse(text, name)
    lines = text.split("\n")
    alias = {}                                                  # _x_base = x  -> x may be redefined below in this part
    out = []

    def nodes(body, inner):
        for nd in body:
            if isinstance(nd, (ast.If, ast.Try)) and not inner:     # try: def a ... except: def a  (one part, one choice)
                subs = list(nd.body) + list(getattr(nd, "orelse", [])) + list(getattr(nd, "finalbody", []))
                for h in getattr(nd, "handlers", []):
                    subs += h.body
                yield from ((x, True) for x, _i in nodes(subs, True))
            else:
                yield nd, inner

    seen_inner = set()
    for nd, inner in nodes(tree.body, False):
        first = min([nd.lineno] + [d.lineno for d in getattr(nd, "decorator_list", [])])
        above = ""
        for j in range(first - 2, -1, -1):
            if lines[j].strip():
                above = lines[j].strip()
                break
        m = WRAPS_RE.search(above) or WRAPS_RE.search(lines[nd.lineno - 1])
        if isinstance(nd, ast.ClassDef):                         # its methods (Klasse.methode = … later replaces one)
            for m_ in nd.body:
                if isinstance(m_, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append((nd.name + "." + m_.name, m_.lineno, "method", False))
        if (isinstance(nd, ast.Assign) and len(nd.targets) == 1 and isinstance(nd.targets[0], ast.Attribute)
                and isinstance(nd.targets[0].value, ast.Name)):
            out.append((nd.targets[0].value.id + "." + nd.targets[0].attr, nd.lineno, "=",
                        bool(m and m.group(1) in (nd.targets[0].attr, nd.targets[0].value.id + "." + nd.targets[0].attr))))
            continue
        if isinstance(nd, ast.Assign) and len(nd.targets) == 1 and isinstance(nd.targets[0], ast.Name):
            tg = nd.targets[0].id
            if isinstance(nd.value, ast.Name) and tg.startswith("_") and nd.value.id in tg:
                alias[nd.value.id] = nd.lineno
                continue
            out.append((tg, nd.lineno, "=", bool(m and m.group(1) == tg)))
        elif isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if inner:
                if nd.name in seen_inner:
                    continue
                seen_inner.add(nd.name)
            kind = "class" if isinstance(nd, ast.ClassDef) else "def"
            marked = bool(m and m.group(1) == nd.name) or alias.get(nd.name, 10 ** 9) < nd.lineno
            out.append((nd.name, nd.lineno, kind, marked))
    return out


def doppelte():
    """2.98.18: every top-level function / class defined in more than one part (or twice in one part) - the later one silently
    replaces the earlier one (2.98.17: bt_scan of 300 replaced the loudspeaker search of 250). Allowed only for an intended
    wrapper, marked in the later part by
        _<name>_base = <name>        (any name with a leading «_» that contains <name>, above the new def), or
        # wraps: <name>              (comment on the line before the def / its decorator, or at the end of the def line)
    Also a plain assignment «<name> = …» to a function of another part, or «Klasse.methode = …» to a method the class
    already has, needs «# wraps: <name>».
    Returns the list of problems (empty = ok)."""
    defs, probs = {}, []
    alle = [(n, _namen(n, lesen(n))) for n in teile()]
    funcs = {nm for _n, xs in alle for nm, _l, k, _m in xs if k != "="}
    for n, xs in alle:
        for nm, ln, kind, marked in xs:
            if kind == "=" and nm not in funcs:
                continue
            if kind == "method":
                if nm not in defs:
                    defs[nm] = (n, ln)
                continue
            if nm in defs and not marked:
                tip = ("«# wraps: %s» davor" % nm) if "." in nm else ("«_%s_base = %s» oder «# wraps: %s» davor" % (nm, nm, nm))
                probs.append("%s:%d %s %s – schon in %s:%d (Wrapper? %s)" % (n, ln, kind, nm, defs[nm][0], defs[nm][1], tip))
            if kind != "=" and not (kind == "method" and nm in defs):
                defs.setdefault(nm, (n, ln))
    return probs


def doppelte_melden():
    p = doppelte()
    for x in p:
        print("DOPPELT: " + x)
    if p:
        print("%d doppelte Namen: der spätere Teil ersetzt den früheren still. Umbenennen oder als Wrapper markieren." % len(p))
    return not p


def zusammensetzen():
    return "".join(lesen(n) for n in teile())


# ---------------------------------------------------------------------------- Zusatzdaten (moveeye_daten_X_Y_Z.zip)
ZD_MIN = 4096                       # literals from this size (bytes of source) are moved out
ZD_NEU = 30                         # the list of changes in the file keeps the entries of the newest 30 versions
ZD_KEEP_PARTS = ("000_", "010_", "012_", "020_")   # head, basics, loader, settings: always in the file
# tables the core needs (settings schema, German texts, menu structure, guides with index access) stay in the file
ZD_KEEP_NAMES = {"CFG", "TOGGLES", "SLIDERS", "TEXTS", "SECTIONS", "DE", "QUICK_GUIDE", "MENU_SHORT", "GUIDE_TIPS", "_DETAIL",
                 "G2_UI", "SET_HELP", "GONL_DE", "ALMANAC", "PAUSE_PAGE", "LANGS"}
ZD_DATE = (2026, 1, 1, 0, 0, 0)     # fixed time stamp in the zip


def zd_name(v):
    return "moveeye_daten_%s.zip" % v.replace(".", "_")


def zd_pfad(v):
    return os.path.join(REPO, zd_name(v))


def _zd_lit(n):
    if isinstance(n, ast.Constant):
        return True
    if isinstance(n, ast.Dict):
        return all(k is not None and _zd_lit(k) for k in n.keys) and all(_zd_lit(v) for v in n.values)
    if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
        return all(_zd_lit(e) for e in n.elts)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)) and isinstance(n.operand, ast.Constant):
        return True
    return False


def _zd_ctx(st):
    if isinstance(st, ast.Assign):
        return ast.unparse(st.targets[0])
    if isinstance(st, (ast.AugAssign, ast.AnnAssign)):
        return ast.unparse(st.target)
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
        return ast.unparse(st.value.func)
    return type(st).__name__


def _zd_fallback(nd, ctx):
    if isinstance(nd, ast.Dict):
        return "_ZDDict()"
    if isinstance(nd, ast.List):
        return "[]"
    if isinstance(nd, ast.Tuple):
        return "()"
    if isinstance(nd, ast.Set):
        return "set()"
    if isinstance(nd.value, bytes):
        return 'b""'
    if isinstance(nd.value, str):
        return "ZD_PAGE" if re.search(r"_(PAGE|HTML)$", ctx) else '""'
    return repr(nd.value)


def _zd_kopf(text):
    """the head part: the module docstring keeps the entries of the newest ZD_NEU versions -> (new text, [(key, ph, seg)])"""
    tree = ast.parse(text)
    st = tree.body[0] if tree.body else None
    if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str)):
        return text, []
    nd = st.value
    lines = text.split("\n")
    a = sum(len(x) + 1 for x in lines[:nd.lineno - 1]) + len(lines[nd.lineno - 1].encode()[:nd.col_offset].decode())
    e = sum(len(x) + 1 for x in lines[:nd.end_lineno - 1]) + len(lines[nd.end_lineno - 1].encode()[:nd.end_col_offset].decode())
    seg = text[a:e]
    rx = re.compile(r"^  \* (\d+\.\d+\.\d+): ")
    vers = sorted({tuple(int(x) for x in m.group(1).split(".")) for m in map(rx.match, seg.split("\n")) if m}, reverse=True)
    keep = set(vers[:ZD_NEU])
    out, cur, gone, note = [], None, 0, False
    for ln in seg.split("\n"):
        m = rx.match(ln)
        if m:
            cur = tuple(int(x) for x in m.group(1).split(".")) in keep
        elif not ln.startswith("    ") or not ln.strip():
            cur = None
        if cur is False:
            gone += 1
            if not note:
                out.append("  (Ältere Einträge: in der Zusatzdatei moveeye_daten_X_Y_Z.zip; vollständig in quelle/000_kopf_aenderungen.py)")
                note = True
            continue
        out.append(ln)
    if not gone:
        return text, []
    ph = "\n".join(out)
    return text[:a] + ph + text[e:], [("000_kopf_aenderungen/__doc__", ph, seg)]


def auslagern(name, text):
    """one part -> (text with _zd() calls, [(key, placeholder, original source)]) - see the head of this file"""
    if name.startswith("000_"):
        return _zd_kopf(text)
    if name.startswith(ZD_KEEP_PARTS):
        return text, []
    tree = ast.parse(text, name)
    b = text.encode()
    off = [0]
    for ln in b.split(b"\n"):
        off.append(off[-1] + len(ln) + 1)
    found = []
    stop = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.ListComp, ast.DictComp, ast.SetComp,
            ast.GeneratorExp, ast.For, ast.AsyncFor, ast.While, ast.JoinedStr, ast.FormattedValue)

    def walk(nd, ctx):
        if isinstance(nd, stop):
            return
        if isinstance(nd, ast.expr) and _zd_lit(nd) and not isinstance(nd, ast.UnaryOp):
            a = off[nd.lineno - 1] + nd.col_offset
            e = off[nd.end_lineno - 1] + nd.end_col_offset
            base = re.split(r"[.\[]", ctx, maxsplit=1)[0]
            if e - a >= ZD_MIN and base not in ZD_KEEP_NAMES:
                found.append((a, e, nd, ctx))
            return
        for c in ast.iter_child_nodes(nd):
            walk(c, ctx)

    def body(stmts):
        for st in stmts:
            if isinstance(st, (ast.If, ast.Try, ast.With)):
                if isinstance(st, ast.If):
                    walk(st.test, _zd_ctx(st))
                body(st.body); body(getattr(st, "orelse", []))
                for h in getattr(st, "handlers", []):
                    body(h.body)
                body(getattr(st, "finalbody", []))
            else:
                walk(st, _zd_ctx(st))
    body(tree.body)
    if not found:
        return text, []
    stem = name[:-3]
    out, ents, pos, used = [], [], 0, {}
    for a, e, nd, ctx in sorted(found, key=lambda x: x[0]):
        k = re.sub(r"[^A-Za-z0-9_]+", "_", ctx).strip("_") or "x"
        used[k] = used.get(k, 0) + 1
        key = "%s/%s" % (stem, k) + ("~%d" % used[k] if used[k] > 1 else "")
        ph = "_zd(%r, %s)" % (key, _zd_fallback(nd, ctx))
        out.append(b[pos:a]); out.append(ph.encode()); pos = e
        ents.append((key, ph, b[a:e].decode()))
    out.append(b[pos:])
    return b"".join(out).decode(), ents


def zusammensetzen_klein(zd_sha=None):
    """(program text, entries of the data zip, version). zd_sha: the checksum written into the program (None = of the
    zip that these entries give, see zd_bytes)"""
    teile_ = teile()
    v = version()
    texts, ents = [], []
    for n in teile_:
        t, e = auslagern(n, lesen(n))
        texts.append(t); ents += e
    if ents:
        if zd_sha is None:
            zd_sha = hashlib.sha256(zd_bytes(v, ents)).hexdigest()
        for i, n in enumerate(teile_):
            if n.startswith("012_"):
                texts[i] = (texts[i].replace('ZD_FILE = ""', 'ZD_FILE = "%s"' % zd_name(v), 1)
                            .replace('ZD_SHA256 = ""', 'ZD_SHA256 = "%s"' % zd_sha, 1))
    return "".join(texts), ents, v


def zd_json(v, ents):
    return json.dumps({"app": "MoveEye", "version": v, "file": os.path.basename(dateiname(v)),
                       "entries": [list(x) for x in ents]}, ensure_ascii=False, indent=0)


def zd_bytes(v, ents):
    import io
    import zipfile
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        zi = zipfile.ZipInfo("daten.json", ZD_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        z.writestr(zi, zd_json(v, ents).encode("utf-8"), compresslevel=9)
    return bio.getvalue()


def zd_inhalt(path):
    """daten.json of an existing zip (None if missing / unreadable)"""
    import zipfile
    try:
        with zipfile.ZipFile(path) as z:
            return z.read("daten.json").decode("utf-8")
    except (OSError, KeyError, zipfile.BadZipFile):
        return None


def groessen(n=15):
    """--groessen: what needs the most room - parts and the biggest literals"""
    roh = zusammensetzen()
    print("Ohne Auslagern: %d Bytes (%.2f MiB)" % (len(roh.encode()), len(roh.encode()) / 1048576))
    print("\nGrösste Teile:")
    for sz, nm in sorted(((len(lesen(x).encode()), x) for x in teile()), reverse=True)[:n]:
        print("  %8d  %s" % (sz, nm))
    rows = []
    for nm in teile():
        _t, es = auslagern(nm, lesen(nm))
        rows += [(len(seg.encode()), k) for k, _p, seg in es]
    print("\nGrösste ausgelagerte Literale:")
    for sz, k in sorted(rows, reverse=True)[:n]:
        print("  %8d  %s" % (sz, k))
    text, ents, v = zusammensetzen_klein()
    print("\nAusgelagert: %d Literale, %d Bytes · Hauptdatei %d Bytes (%.2f MiB) · ZIP %d Bytes"
          % (len(ents), sum(len(x[2].encode()) for x in ents), len(text.encode()), len(text.encode()) / 1048576,
             len(zd_bytes(v, ents))))
    return 0


def version(text=None):
    m = re.search(r'^APP_VERSION = "([0-9.]+)"', text or lesen("010_grundlagen.py"), re.M)
    if not m:
        sys.exit("APP_VERSION nicht gefunden")
    return m.group(1)


def dateiname(v):
    return os.path.join(REPO, "webcam_bewegung_%s.py" % v.replace(".", "_"))


def naechste(alt, stufe="fehler"):
    """die nächste Nummer nach Daniels Regeln (31.10.2026): fehler = X.Y.Z+1, funktion = X.Y+1.0, gross = X+1.0.0"""
    a = [int(x) for x in alt.split(".")]
    if stufe == "gross":
        return "%d.0.0" % (a[0] + 1)
    if stufe == "funktion":
        return "%d.%d.0" % (a[0], a[1] + 1)
    return "%d.%d.%d" % (a[0], a[1], a[2] + 1)


def neue_version(text_aenderung, ziel="", stufe="fehler"):
    alt = version()
    neu = ziel or naechste(alt, stufe)
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", neu):              # VER_RE / VFILE_RE of the update (380): else no device finds it
        sys.exit("Nummer %s passt nicht zum Schema X.Y.Z (je 1-3 Ziffern)" % neu)
    for name in teile():                                       # the number at every place (title, build, help, file name)
        t = lesen(name)
        # Versionierung 3.0.0: only these exact places - with short numbers (3.1.0) a plain «3_1_0» / «MoveEye 3.1.0» could
        # also be a word or a note about an older version («ab MoveEye 3.1.0») and must stay
        t2 = (t.replace("webcam_bewegung_" + alt.replace(".", "_") + ".py", "webcam_bewegung_" + neu.replace(".", "_") + ".py")
              .replace('APP_VERSION = "%s"' % alt, 'APP_VERSION = "%s"' % neu)
              .replace('root.title("MoveEye %s")' % alt, 'root.title("MoveEye %s")' % neu).replace('root.title("Motion Watch %s")' % alt, 'root.title("Motion Watch %s")' % neu)
              .replace("{tr('Build')} %s ·" % alt, "{tr('Build')} %s ·" % neu))
        if name.startswith("300_"):                            # the 3D simulator that belongs to this version
            try:
                d = json.load(open(os.path.join(REPO, "simulator3d", "version.json")))
                sv = d.get("ver") or d["version"]               # Versionierung 3.0.0: «ver» = X.Y.Z, «version» = for old simulators
                t2 = re.sub(r'SIM3D = \{"version": "(?:3D-)?[0-9.]+".*?"\}', lambda m: 'SIM3D = {"version": "%s", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": %d,\n         "sha256": "%s"}' % (sv, d["size"], d["sha256"]), t2, count=1, flags=re.S)
            except (OSError, ValueError, KeyError):
                pass
        t2 = re.sub(r"^INFO_PARTS = \d+", "INFO_PARTS = %d" % len(teile()), t2, count=1, flags=re.M)   # «About MoveEye» (584)
        if name.startswith("000_"):                            # the line in the list of changes (above the newest one)
            words, lines, cur = text_aenderung.split(), [], "  * %s:" % neu
            for w in words:
                if len(cur) + 1 + len(w) > 128:
                    lines.append(cur)
                    cur = "    " + w
                else:
                    cur += " " + w
            lines.append(cur)
            i = t2.find("\n  * %s:" % alt)
            if i < 0:
                sys.exit("Änderungsliste: Zeile der Version %s nicht gefunden" % alt)
            t2 = t2[:i + 1] + "\n".join(lines) + "\n" + t2[i + 1:]
        if t2 != t:
            schreiben(name, t2)
    return alt, neu


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(description="Motion Watch aus quelle/ zusammensetzen")
    ap.add_argument("--pruefen", action="store_true", help="nur prüfen, ob die Datei im Repository zu quelle/ passt")
    ap.add_argument("--neue-version", metavar="TEXT", default=None, help="nächste Version mit dieser Zeile in der Änderungsliste")
    ap.add_argument("--version", default="", help="mit --neue-version: diese Nummer statt X.Y.Z+1")
    ap.add_argument("--stufe", choices=("fehler", "funktion", "gross"), default="fehler",
                    help="mit --neue-version: fehler = X.Y.Z+1 (Standard), funktion = X.Y+1.0, gross = X+1.0.0")
    ap.add_argument("--groessen", action="store_true", help="was braucht am meisten Platz?")
    ap.add_argument("--signieren", metavar="SCHLUESSEL", default="", help="versions.json schreiben und signieren, Selbsttest")
    a = ap.parse_args()
    if a.groessen:
        return groessen()
    if a.pruefen:
        if not doppelte_melden():
            return 1
        v = version()
        f, zf = dateiname(v), zd_pfad(v)
        if not os.path.isfile(f):
            print("FEHLT: %s – zuerst bauen" % os.path.basename(f))
            return 1
        sha = hashlib.sha256(open(zf, "rb").read()).hexdigest() if os.path.isfile(zf) else ""
        text, ents, _v = zusammensetzen_klein(sha)
        if ents and zd_inhalt(zf) != zd_json(v, ents):
            print("UNTERSCHIED: %s fehlt oder passt nicht zu quelle/ – werkzeuge/bauen.py laufen lassen" % os.path.basename(zf))
            return 1
        if open(f, encoding="utf-8", newline="").read() != text:
            print("UNTERSCHIED: %s passt nicht zu quelle/ – werkzeuge/bauen.py laufen lassen (nie die grosse Datei von Hand ändern)" % os.path.basename(f))
            return 1
        print("ok: %s = quelle/ (%d Teile)%s" % (os.path.basename(f), len(teile()),
                                              (" + %s (%d Literale)" % (os.path.basename(zf), len(ents))) if ents else ""))
        return 0
    if a.neue_version is not None:
        alt, neu = neue_version(a.neue_version, a.version, a.stufe)
        print("Version %s → %s" % (alt, neu))
        fa, fn = dateiname(alt), dateiname(neu)
        if os.path.isfile(fa) and alt.split(".")[:2] == neu.split(".")[:2]:   # only the newest file of a main version stays
            if git("rm", "-q", os.path.basename(fa)).returncode != 0:
                os.remove(fa)
            za = zd_pfad(alt)
            if os.path.isfile(za) and git("rm", "-q", os.path.basename(za)).returncode != 0:
                os.remove(za)
    if not doppelte_melden():
        return 1
    v = version()
    f, zf = dateiname(v), zd_pfad(v)
    text, ents, _v = zusammensetzen_klein("")
    if ents:
        if zd_inhalt(zf) != zd_json(v, ents):              # only a changed content gives a new zip (stable checksum)
            with open(zf, "wb") as fh:
                fh.write(zd_bytes(v, ents))
        sha = hashlib.sha256(open(zf, "rb").read()).hexdigest()
        text, ents, _v = zusammensetzen_klein(sha)
    with open(f, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        return 1
    print("gebaut: %s (%d Zeilen aus %d Teilen, %.2f MiB)" % (os.path.basename(f), text.count("\n"), len(teile()),
                                                             len(text.encode()) / 1048576))
    if ents:
        print("        %s (%d Literale ausgelagert, %.2f MiB)" % (os.path.basename(zf), len(ents), os.path.getsize(zf) / 1048576))
    if len(text.encode()) > 8 * 1024 * 1024:
        print("WARNUNG: über 8 MiB – Geräte bis 2.98.x nehmen diese Datei beim Update nicht an")
    if a.signieren:
        for cmd in ([sys.executable, f, "--make-manifest", ".", "--sign-key", a.signieren], [sys.executable, f, "--self-test", "."]):
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            print((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "")
            if r.returncode != 0:
                return 1
    for d in glob.glob(os.path.join(REPO, "__pycache__")):
        subprocess.run(["rm", "-rf", d])
    return 0


if __name__ == "__main__":
    sys.exit(main())
