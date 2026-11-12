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
  python3 werkzeuge/bauen.py --nur-signieren SCHLUESSELDATEI             # Drei Spuren: OHNE zu bauen (Sim- oder Gehäuse-Release:
                                                                         #   die veröffentlichte MoveEye-Datei bleibt Byte für Byte)
                                                                         #   versions.json mit Block «sim» neu signieren, Selbsttest
  python3 werkzeuge/bauen.py --groessen                                  # was braucht am meisten Platz? (Teile, Literale)

Zusatzdaten (31.10.2026, Paket «MoveEye-Datei verkleinern»): grosse Literale (Web-Seiten, JavaScript, Bilder als base64,
Übersetzungen) und der ältere Teil der Änderungsliste kommen beim Bauen in moveeye_daten_X_Y_Z.zip neben der Datei
(Geräte bis 2.98.x nehmen nur Programmdateien bis 8 MiB an). quelle/ bleibt unverändert; die grosse Datei lädt die ZIP
beim Start (Teil 012) und kennt ihre Prüfsumme (ZD_SHA256). Beide Dateien gehören zusammen ins Repository.

Schlank (07.11.2026, für 3.59.0): zusätzlich kommen kleinere statische Inhalte ab 1 KiB (Übersetzungen, Anleitung, Web-Seiten /
JS / CSS) in die ZIP, die Tabellen _HX… behalten nur Deutsch, und die Hauptdatei hat keine Kommentare und Docstrings von
Funktionen / Klassen und ist mit Tabs eingerückt (gleiche Zeilennummern; die Originalzeilen stehen in der ZIP, zd_source()
setzt sie wieder ein). Grenze der Hauptdatei: Warnung ab 4 MiB, Abbruch ab 5 MiB.

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


UIG_TEIL = "639p_ui_gemeinsam.py"                         # P1: die gemeinsame Menü-Datei, eingebettet als UI_GEMEINSAM
UIG_JSON = os.path.join(REPO, "simulator3d", "ui_gemeinsam.json")
UIG_RE = re.compile(r'(UI_GEMEINSAM = json\.loads\(r""")(.*?)("""\))', re.S)


def ui_gemeinsam_einbetten(nur_pruefen=False):
    """P1 (Besitzer 31.10.2026): simulator3d/ui_gemeinsam.json als UI_GEMEINSAM in quelle/639p_ui_gemeinsam.py schreiben (eine
    Quelle für MoveEye und den Simulator; die Signatur der Hauptdatei deckt sie mit ab). nur_pruefen: nur melden, ob es passt."""
    if not os.path.isfile(os.path.join(QUELLE, UIG_TEIL)) or not os.path.isfile(UIG_JSON):
        return True
    with open(UIG_JSON, encoding="utf-8") as f:
        neu = json.dumps(json.load(f), ensure_ascii=False, indent=1)
    if '"""' in neu or neu.endswith("\\"):
        print("FEHLER: simulator3d/ui_gemeinsam.json enthält \"\"\" – so nicht einbettbar")
        return False
    t = lesen(UIG_TEIL)
    m = UIG_RE.search(t)
    if not m:
        print("FEHLER: %s ohne «UI_GEMEINSAM = json.loads(r\"\"\"…\"\"\")»" % UIG_TEIL)
        return False
    if m.group(2) == neu:
        return True
    if nur_pruefen:
        print("UNTERSCHIED: quelle/%s passt nicht zu simulator3d/ui_gemeinsam.json – werkzeuge/bauen.py laufen lassen" % UIG_TEIL)
        return False
    schreiben(UIG_TEIL, t[:m.start(2)] + neu + t[m.end(2):])
    print("eingebettet: simulator3d/ui_gemeinsam.json -> quelle/%s" % UIG_TEIL)
    return True


FXK_TEIL = "639u_fehler_hilfe.py"                          # Fehler-QR: der gemeinsame Fehler-Katalog, eingebettet als FEHLER_KATALOG
FXK_JSON = os.path.join(REPO, "simulator3d", "fehler_katalog.json")
FXK_RE = re.compile(r'(FEHLER_KATALOG = json\.loads\(r""")(.*?)("""\))', re.S)


def fehler_katalog_einbetten(nur_pruefen=False):
    """Fehler-QR (Besitzer 01.11.2026): simulator3d/fehler_katalog.json als FEHLER_KATALOG in quelle/639u_fehler_hilfe.py (wie
    ui_gemeinsam_einbetten). Bleibt in der Hauptdatei (ZD_KEEP_NAMES): die Hilfe zu Fehlern geht auch ohne Zusatzdaten."""
    if not os.path.isfile(os.path.join(QUELLE, FXK_TEIL)) or not os.path.isfile(FXK_JSON):
        return True
    with open(FXK_JSON, encoding="utf-8") as f:
        neu = json.dumps(json.load(f), ensure_ascii=False, indent=1)
    if '"""' in neu or neu.endswith("\\"):
        print("FEHLER: simulator3d/fehler_katalog.json enthält \"\"\" – so nicht einbettbar")
        return False
    t = lesen(FXK_TEIL)
    m = FXK_RE.search(t)
    if not m:
        print("FEHLER: %s ohne «FEHLER_KATALOG = json.loads(r\"\"\"…\"\"\")»" % FXK_TEIL)
        return False
    if m.group(2) == neu:
        return True
    if nur_pruefen:
        print("UNTERSCHIED: quelle/%s passt nicht zu simulator3d/fehler_katalog.json – werkzeuge/bauen.py laufen lassen" % FXK_TEIL)
        return False
    schreiben(FXK_TEIL, t[:m.start(2)] + neu + t[m.end(2):])
    print("eingebettet: simulator3d/fehler_katalog.json -> quelle/%s" % FXK_TEIL)
    return True


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
ZD_MIN_KLEIN = 1024                 # 3.59.0: pure static content (translations, manual, web pages / JS / CSS) from this size
ZD_NEU = 30                         # the list of changes in the file keeps the entries of the newest 30 versions
ZD_KEEP_PARTS = ("000_", "010_", "012_", "020_")   # head, basics, loader, settings: always in the file
# tables the core needs (settings schema, German texts, menu structure, guides with index access) stay in the file
ZD_KEEP_NAMES = {"CFG", "TOGGLES", "SLIDERS", "TEXTS", "SECTIONS", "DE", "QUICK_GUIDE", "MENU_SHORT", "GUIDE_TIPS", "_DETAIL",
                 "G2_UI", "SET_HELP", "GONL_DE", "ALMANAC", "PAUSE_PAGE", "LANGS",
                 "FEHLER_KATALOG",                 # Fehler-QR: die Hilfe zu Fehlern geht auch ohne Zusatzdaten (639u)
                 "UI_GEMEINSAM"}                   # Schlank: Menü-Datei (Fenster, Kopf 639t) - ohne Zusatzdaten startete 3.58.0 nicht
ZD_KEEP_PREFIX = ("_HX",)          # the translation tables _HX… also carry the German texts (DE) that the start needs
# Schlank (3.59.0): a table _HX… {English: (de, fr, it, rm)} keeps only {English: de} in the file (fallback _zd_hx, 012);
# the whole table with fr / it / rm goes to the zip. Tables {English: (fr, it, rm)} (no German) go to the zip as a whole.
ZD_DATE = (2026, 1, 1, 0, 0, 0)     # fixed time stamp in the zip
# Ablage entlasten (Review Nov. 2026): daten.json steht UNGEPACKT in der ZIP (ZIP_STORED). Der Inhalt ändert sich von Version
# zu Version nur zu wenigen Prozent; ungepackt speichert git dafür nur den Unterschied (gemessen 3.69.2 - 3.77.0: 0.06 - 0.11 MB
# pro Version statt 4.9 MB), gepackt war jede ZIP für git ein ganz neuer Block. Preis: die Geräte laden rund 10 MB statt
# 4.9 MB (Grenze der Geräte: 64 MiB, ZD_MAX_BYTES in Teil 397 seit der ersten Zusatzdatei; die Programme lesen jede ZIP,
# gepackt oder nicht). Abbruch weit vor der Grenze der Geräte: ZD_GRENZE. Zurück auf gepackt: ZD_GEPACKT = True - eine schon
# gebaute ZIP wird nur bei anderem INHALT neu geschrieben (veröffentlichte Dateien bleiben Byte für Byte).
ZD_GEPACKT = False
ZD_GRENZE = 32 * 1024 * 1024        # the data zip never gets bigger than half of what the devices accept


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


def _zd_hx_art(nd):
    """a translation table _HX…: 4 = {English: (de, fr, it, rm)} (tuple or list), 3 = {English: (fr, it, rm)}, else 0 (stays)"""
    if not isinstance(nd, ast.Dict) or not nd.values:
        return 0
    lens = set()
    for k, v in zip(nd.keys, nd.values):
        if not (isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, (ast.Tuple, ast.List))
                and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in v.elts)):
            return 0
        lens.add((len(v.elts), type(v)))
    return 4 if lens in ({(4, ast.Tuple)}, {(4, ast.List)}) else 3 if lens in ({(3, ast.Tuple)}, {(3, ast.List)}) else 0


def _zd_statisch(nd, base, hx):
    """pure static content that the core does not need (moved out from ZD_MIN_KLEIN on): a translation table _HX…, a table
    TRX[…] / HELP_… (fr / it / rm, manual), a text <NAME>_PAGE / _HTML / _JS / _CSS (web). Never a list / dict of other
    data (labels of the AI, menu groups of the window, keys for the factory reset …): those stay from ZD_MIN on."""
    if hx:
        return True
    if base == "TRX" or base.startswith("HELP_"):
        return isinstance(nd, ast.Dict)
    return isinstance(nd, ast.Constant) and isinstance(nd.value, str) and bool(re.search(r"_(PAGE|HTML|JS|CSS)$", base))


def _zd_hx_fallback(seg):
    """the German part of a table {English: (de, fr, it, rm)} as source: _zd_hx({English: de, …}, list?) (012)"""
    d = ast.literal_eval("(" + seg + "\n)")
    rows = "".join("    %r: %r,\n" % (k, v[0]) for k, v in d.items())
    return "_zd_hx({\n%s}%s)" % (rows, ", True" if isinstance(next(iter(d.values())), list) else "")


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
    if isinstance(nd.value, str) and getattr(nd, "_zd_json", False):
        return repr("[]" if nd.value.lstrip().startswith("[") else "{}")
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
            hx = _zd_hx_art(nd) if base.startswith(ZD_KEEP_PREFIX) else 0
            if e - a >= (ZD_MIN_KLEIN if _zd_statisch(nd, base, hx) else ZD_MIN) and base not in ZD_KEEP_NAMES and (
                    hx or not base.startswith(ZD_KEEP_PREFIX)):
                found.append((a, e, nd, ctx, hx))
            return
        js = isinstance(nd, ast.Call) and ast.unparse(nd.func) == "json.loads"
        for c in ast.iter_child_nodes(nd):
            if js and isinstance(c, ast.Constant) and isinstance(c.value, str):
                c._zd_json = True                          # json.loads(<text>): without the zip an empty JSON, never ""
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
    for a, e, nd, ctx, hx in sorted(found, key=lambda x: x[0]):
        k = re.sub(r"[^A-Za-z0-9_]+", "_", ctx).strip("_") or "x"
        used[k] = used.get(k, 0) + 1
        key = "%s/%s" % (stem, k) + ("~%d" % used[k] if used[k] > 1 else "")
        fb = _zd_hx_fallback(b[a:e].decode()) if hx == 4 else _zd_fallback(nd, ctx)
        ph = "_zd(%r, %s)" % (key, fb)
        out.append(b[pos:a]); out.append(ph.encode()); pos = e
        ents.append((key, ph, b[a:e].decode()))
    out.append(b[pos:])
    return b"".join(out).decode(), ents


ZD_SCHLANK = True                   # 3.59.0: comments, docstrings of functions / classes, indentation as tabs (_schlank)
ZD_FOLGEZEILEN = True               # Hauptdatei kleiner: also the continuation lines with tabs (_schlank)


def _schlank(text):
    """Schlank (3.59.0): the program without comments and without the docstrings of functions and classes - every line
    stays at its place (same line numbers in tracebacks and logs), only its text gets shorter. -> (new text, [[line,
    original line], …]); the original lines go into the zip ("zeilen"), zd_source() (012) puts them back. Kept: the first
    line (#!), the module docstring (list of changes), every string literal that is not a docstring."""
    import io
    import tokenize
    lines = text.split("\n")
    new = list(lines)

    def put(row, a, e, rep):                               # row 1-based; a / e = character columns on that row
        ln = new[row - 1]
        new[row - 1] = ln[:a] + rep + ln[e:]

    tree = ast.parse(text)
    docs = []
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and nd.body:
            st = nd.body[0]
            if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
                docs.append(st.value)
    for c in sorted(docs, key=lambda c: (c.lineno, c.col_offset), reverse=True):
        a = len(lines[c.lineno - 1].encode()[:c.col_offset].decode())          # ast: byte offsets -> characters
        e = len(lines[c.end_lineno - 1].encode()[:c.end_col_offset].decode())
        if c.lineno == c.end_lineno:
            put(c.lineno, a, e, '""')
        else:                                              # «"""» … «"""»: the empty lines keep the line numbers
            put(c.end_lineno, 0, e, '"""')
            for r in range(c.lineno + 1, c.end_lineno):
                new[r - 1] = ""
            put(c.lineno, a, len(new[c.lineno - 1]), '"""')
    mid = "\n".join(new)
    # indentation: a level of four more spaces becomes one tab, any other step stays spaces (the new indentation of a
    # level always starts with the one of its parent - Python sees the same blocks with tabs of any width)
    cm, starts, stack, prev_end, at_start = {}, [], [("", "")], 0, True
    im_text, fs_tief, fs_start = set(), 0, 0               # rows that begin inside a string of several lines: never touched
    t_fs_a, t_fs_e = getattr(tokenize, "FSTRING_START", -1), getattr(tokenize, "FSTRING_END", -1)
    for tok in tokenize.generate_tokens(io.StringIO(mid).readline):
        tt = tok.type
        if tt == tokenize.STRING:
            im_text.update(range(tok.start[0] + 1, tok.end[0] + 1))
        elif tt == t_fs_a:                                 # Python 3.12+: an f-string comes in pieces - the same rows as before
            fs_tief += 1
            if fs_tief == 1:
                fs_start = tok.start[0]
        elif tt == t_fs_e:
            fs_tief -= 1
            if fs_tief == 0:
                im_text.update(range(fs_start + 1, tok.end[0] + 1))
        if tt == tokenize.COMMENT:
            if not (tok.start[0] == 1 and tok.string.startswith("#!")):
                cm[tok.start[0]] = tok.start[1]
            continue
        if tt == tokenize.INDENT:
            old, neu = stack[-1]
            d = tok.string[len(old):]
            if not tok.string.startswith(old) or d.strip(" "):
                raise SystemExit("Schlank: Einrückung mit Tabs in quelle/ (Zeile %d) – nur Leerzeichen verwenden" % tok.start[0])
            stack.append((tok.string, neu + ("\t" if d == "    " else d)))
            continue
        if tt == tokenize.DEDENT:
            stack.pop()
            continue
        if tt in (tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER):
            at_start = at_start or tt == tokenize.NEWLINE
            prev_end = tok.end[0]
            continue
        if at_start:                                       # the first token of a logical line
            if len(stack) > 1 and prev_end < tok.start[0]:
                starts.append((tok.start[0], tok.start[1]) + stack[-1])
            at_start = False
        prev_end = tok.end[0]
    for row, col in cm.items():
        new[row - 1] = new[row - 1][:col].rstrip()
    kopf = set()
    for row, col, old, neu in starts:
        ln = new[row - 1]
        kopf.add(row)
        if ln[:col] == old:
            new[row - 1] = neu + ln[col:]
    if ZD_FOLGEZEILEN:
        # Hauptdatei kleiner (Nov. 2026): continuation lines (inside brackets, aligned with spaces) - every four leading
        # spaces become one tab, the rest stays. Python ignores the indentation of such a line; zd_source() (012) turns
        # leading tabs back into four spaces each, so these lines need no entry in "zeilen". Lines that begin inside a
        # string of several lines are content and stay as they are.
        for i, ln in enumerate(new):
            if (i + 1) in im_text or (i + 1) in kopf or not ln.startswith("    "):
                continue
            n = len(ln) - len(ln.lstrip(" "))
            if n < len(ln):
                new[i] = "\t" * (n // 4) + ln[n - n % 4:]
    out = "\n".join(new)
    if len(new) != len(lines):
        raise SystemExit("Schlank: Zeilenzahl geändert – Fehler in bauen.py")
    compile(out, "schlank", "exec")                        # TabError / SyntaxError: stop here, never write such a file
    return out, [[i + 1, a] for i, (a, b) in enumerate(zip(lines, new)) if _zd_tabs_aus(b) != a]


def _zd_tabs_aus(line):
    """the leading tabs of a line back to four spaces each (the same as zd_source() in 012)"""
    n = len(line) - len(line.lstrip("\t"))
    return "    " * n + line[n:] if n else line


def zusammensetzen_klein(zd_sha=None):
    """(program text, entries of the data zip, version, original lines). zd_sha: the checksum written into the program
    (None = of the zip that these entries give, see zd_bytes)"""
    teile_ = teile()
    v = version()
    texts, ents = [], []
    for n in teile_:
        t, e = auslagern(n, lesen(n))
        texts.append(t); ents += e
    if not ents:
        return "".join(texts), ents, v, []
    for i, n in enumerate(teile_):
        if n.startswith("012_"):
            texts[i] = texts[i].replace('ZD_FILE = ""', 'ZD_FILE = "%s"' % zd_name(v), 1)
    text, zeilen = _schlank("".join(texts)) if ZD_SCHLANK else ("".join(texts), [])
    if zd_sha is None:
        zd_sha = hashlib.sha256(zd_bytes(v, ents, zeilen)).hexdigest()
    text, n = re.subn(r'^ZD_SHA256 = ""$', 'ZD_SHA256 = "%s"' % zd_sha, text, count=1, flags=re.M)
    if not n:
        raise SystemExit("Teil 012: Zeile «ZD_SHA256 = \"\"» fehlt")
    return text, ents, v, zeilen


def zd_json(v, ents, zeilen=()):
    d = {"app": "MoveEye", "version": v, "file": os.path.basename(dateiname(v)), "entries": [list(x) for x in ents]}
    if zeilen:
        d["zeilen"] = [list(x) for x in zeilen]            # 3.59.0: original lines (comments, docstrings) for zd_source()
    return json.dumps(d, ensure_ascii=False, indent=0)


def zd_bytes(v, ents, zeilen=()):
    import io
    import zipfile
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        zi = zipfile.ZipInfo("daten.json", ZD_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED if ZD_GEPACKT else zipfile.ZIP_STORED
        zi.external_attr = 0o644 << 16
        if ZD_GEPACKT:
            z.writestr(zi, zd_json(v, ents, zeilen).encode("utf-8"), compresslevel=9)
        else:
            z.writestr(zi, zd_json(v, ents, zeilen).encode("utf-8"))
    out = bio.getvalue()
    if len(out) > ZD_GRENZE:
        raise SystemExit("Zusatzdatei zu gross: %d Bytes (Grenze %d, die Geräte nehmen höchstens 64 MiB)" % (len(out), ZD_GRENZE))
    return out


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
    text, ents, v, zeilen = zusammensetzen_klein()
    print("\nGrösste Teile in der Hauptdatei (nach Auslagern und Schlank):")
    rows, pos = [], 0
    lines = text.split("\n")
    for nm in teile():                                     # every part starts on a new line: count its lines in the file
        t, _e = auslagern(nm, lesen(nm))
        k = t.count("\n")
        rows.append((len("\n".join(lines[pos:pos + k]).encode()) + 1, nm)); pos += k
    for sz, nm in sorted(rows, reverse=True)[:n]:
        print("  %8d  %s" % (sz, nm))
    print("\nAusgelagert: %d Literale, %d Bytes · %d Zeilen ohne Kommentare / Docstrings · Hauptdatei %d Bytes (%.2f MiB) · ZIP %d Bytes"
          % (len(ents), sum(len(x[2].encode()) for x in ents), len(zeilen), len(text.encode()), len(text.encode()) / 1048576,
             len(zd_bytes(v, ents, zeilen))))
    groesse_pruefen(text)
    return 0


def version(text=None):
    m = re.search(r'^APP_VERSION = "([0-9.]+)"', text or lesen("010_grundlagen.py"), re.M)
    if not m:
        sys.exit("APP_VERSION nicht gefunden")
    return m.group(1)


def dateiname(v):
    return os.path.join(REPO, "webcam_bewegung_%s.py" % v.replace(".", "_"))


def naechste(alt, stufe="fehler"):
    """die nächste Nummer nach den Regeln des Besitzers (31.10.2026): fehler = X.Y.Z+1, funktion = X.Y+1.0, gross = X+1.0.0"""
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
                lx = d.get("linux")                              # the Linux package (versionen.py --linux-json) - same way
                if isinstance(lx, dict) and lx.get("sha256"):
                    t2 = re.sub(r'(SIM3D_LINUX = \{"version": )"[0-9.]+"(, "file": "[^"]+", "size": )\d+(,\s*"sha256": )"[0-9a-f]+"',
                                lambda m: '%s"%s"%s%d%s"%s"' % (m.group(1), lx.get("ver") or sv, m.group(2), lx["size"], m.group(3), lx["sha256"]),
                                t2, count=1)
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


# Code-Prüfung K9: Geräte bis 2.98.x nehmen nur Programmdateien bis 8 MiB an (UPD_MAX_BYTES damals, Teil 390) und holen die
# NEUESTE Version aus versions.json - darum muss jede angebotene Version darunter bleiben, solange es solche Geräte gibt.
# Schlank (3.59.0): die Hauptdatei bleibt klein (Platz für neue Pakete, schnelleres Update): Warnung ab 4 MiB, Abbruch ab
# 5 MiB - dann mehr in die Zusatzdatei (ZD_MIN_KLEIN / _zd_statisch, ZD_KEEP_NAMES). Die 8 MiB der alten Geräte bleiben die
# äussere Grenze (versionen.py MAX_ALT).
GROESSE_MAX = 5 * 1024 * 1024                 # darüber: Abbruch (die Datei wird nicht geschrieben)
GROESSE_WARN = 4 * 1024 * 1024                # darüber: Warnung


def groesse_pruefen(text):
    """False = zu gross (Meldung ausgegeben); Warnung ab GROESSE_WARN"""
    n = len(text.encode("utf-8"))
    mib = n / 1048576.0
    if n > GROESSE_MAX:
        print("ZU GROSS: Hauptdatei %.2f MiB (%d Bytes) – höchstens 5 MiB. Mehr in die Zusatzdatei auslagern (bauen.py "
              "ZD_MIN_KLEIN / _zd_statisch) oder Teile verkleinern; «bauen.py --groessen» zeigt, was Platz braucht." % (mib, n))
        return False
    if n > GROESSE_WARN:
        print("WARNUNG: Hauptdatei %.2f MiB (%d Bytes) – noch %d KiB bis zur 5-MiB-Grenze («bauen.py --groessen»)"
              % (mib, n, (GROESSE_MAX - n) // 1024))
    return True


def main():
    ap = argparse.ArgumentParser(description="Motion Watch aus quelle/ zusammensetzen")
    ap.add_argument("--pruefen", action="store_true", help="nur prüfen, ob die Datei im Repository zu quelle/ passt")
    ap.add_argument("--neue-version", metavar="TEXT", default=None, help="nächste Version mit dieser Zeile in der Änderungsliste")
    ap.add_argument("--version", default="", help="mit --neue-version: diese Nummer statt X.Y.Z+1")
    ap.add_argument("--stufe", choices=("fehler", "funktion", "gross"), default="fehler",
                    help="mit --neue-version: fehler = X.Y.Z+1 (Standard), funktion = X.Y+1.0, gross = X+1.0.0")
    ap.add_argument("--groessen", action="store_true", help="was braucht am meisten Platz?")
    ap.add_argument("--signieren", metavar="SCHLUESSEL", default="", help="versions.json schreiben und signieren, Selbsttest")
    ap.add_argument("--nur-signieren", metavar="SCHLUESSEL", default="",
                    help="Drei Spuren: nicht bauen, nur versions.json (mit «sim») mit der vorhandenen Datei signieren, Selbsttest")
    a = ap.parse_args()
    if a.nur_signieren:
        f = dateiname(version())
        if not os.path.isfile(f):
            print("FEHLT: %s – zuerst die MoveEye-Spur veröffentlichen" % os.path.basename(f))
            return 1
        sha = hashlib.sha256(open(zd_pfad(version()), "rb").read()).hexdigest() if os.path.isfile(zd_pfad(version())) else ""
        if open(f, encoding="utf-8", newline="").read() != zusammensetzen_klein(sha)[0]:
            print("Hinweis: quelle/ ist weiter als %s (unveröffentlichte MoveEye-Änderungen) – signiert wird die Datei, wie sie ist"
                  % os.path.basename(f))
        for cmd in ([sys.executable, f, "--make-manifest", ".", "--sign-key", a.nur_signieren], [sys.executable, f, "--self-test", "."]):
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            print((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "")
            if r.returncode != 0:
                return 1
        return 0
    if a.groessen:
        return groessen()
    if a.pruefen:
        if not doppelte_melden() or not ui_gemeinsam_einbetten(nur_pruefen=True) or not fehler_katalog_einbetten(nur_pruefen=True):
            return 1
        v = version()
        f, zf = dateiname(v), zd_pfad(v)
        if not os.path.isfile(f):
            print("FEHLT: %s – zuerst bauen" % os.path.basename(f))
            return 1
        sha = hashlib.sha256(open(zf, "rb").read()).hexdigest() if os.path.isfile(zf) else ""
        text, ents, _v, zeilen = zusammensetzen_klein(sha)
        if not groesse_pruefen(text):                      # the program file (without the data zip) counts
            return 1
        if ents and zd_inhalt(zf) != zd_json(v, ents, zeilen):
            print("UNTERSCHIED: %s fehlt oder passt nicht zu quelle/ – werkzeuge/bauen.py laufen lassen" % os.path.basename(zf))
            return 1
        if open(f, encoding="utf-8", newline="").read() != text:
            print("UNTERSCHIED: %s passt nicht zu quelle/ – werkzeuge/bauen.py laufen lassen (nie die grosse Datei von Hand ändern)" % os.path.basename(f))
            return 1
        print("ok: %s = quelle/ (%d Teile)%s" % (os.path.basename(f), len(teile()),
                                              (" + %s (%d Literale)" % (os.path.basename(zf), len(ents))) if ents else ""))
        return 0
    if a.neue_version is not None:
        if not groesse_pruefen(zusammensetzen_klein("")[0]):   # vor dem Hochzählen: nichts ändern, wenn es zu gross wird
            return 1
        alt, neu = neue_version(a.neue_version, a.version, a.stufe)
        print("Version %s → %s" % (alt, neu))
        fa, fn = dateiname(alt), dateiname(neu)
        brucke = alt == "3.0.2"                          # Brücke (versionen.py BRUECKE): never removed
        if os.path.isfile(fa) and alt.split(".")[:2] == neu.split(".")[:2] and not brucke:   # only the newest file of a main version stays
            if git("rm", "-q", os.path.basename(fa)).returncode != 0:
                os.remove(fa)
            za = zd_pfad(alt)
            if os.path.isfile(za) and git("rm", "-q", os.path.basename(za)).returncode != 0:
                os.remove(za)
    if not doppelte_melden() or not ui_gemeinsam_einbetten() or not fehler_katalog_einbetten():
        return 1
    v = version()
    f, zf = dateiname(v), zd_pfad(v)
    text, ents, _v, zeilen = zusammensetzen_klein("")
    if ents:
        if zd_inhalt(zf) != zd_json(v, ents, zeilen):      # only a changed content gives a new zip (stable checksum)
            with open(zf, "wb") as fh:
                fh.write(zd_bytes(v, ents, zeilen))
        sha = hashlib.sha256(open(zf, "rb").read()).hexdigest()
        text, ents, _v, zeilen = zusammensetzen_klein(sha)
    if not groesse_pruefen(text):
        return 1
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
