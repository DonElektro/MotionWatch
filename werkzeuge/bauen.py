#!/usr/bin/env python3
"""Setzt Motion Watch aus den Teilen in quelle/ zu der einen Datei webcam_bewegung_X_Y_Z.py zusammen.

Der Pi, die Update-Funktion und die Signatur arbeiten weiter mit dieser einen Datei; bearbeitet wird in quelle/.

  python3 werkzeuge/bauen.py                       # baut die Datei der aktuellen Version (APP_VERSION in quelle/010_grundlagen.py)
  python3 werkzeuge/bauen.py --pruefen             # nur vergleichen: passt die Datei im Repository zu quelle/? (GitHub-Prüfung)
                                                   # Beide prüfen auch: keine Funktion / Klasse in zwei Teilen (doppelte())
  python3 werkzeuge/bauen.py --neue-version "Text" # nächste Version (X.Y.Z+1): Nummer an allen Stellen, Zeile in der
                                                   #   Änderungsliste, Simulator-Version aus simulator3d/version.json, bauen
  python3 werkzeuge/bauen.py --neue-version "Text" --version 2.96.0     # eine bestimmte Nummer
  python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI                 # danach: versions.json schreiben, signieren, Selbsttest

Den Schlüssel nie ins Repository legen.
"""
import argparse
import ast
import glob
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


def version(text=None):
    m = re.search(r'^APP_VERSION = "([0-9.]+)"', text or lesen("010_grundlagen.py"), re.M)
    if not m:
        sys.exit("APP_VERSION nicht gefunden")
    return m.group(1)


def dateiname(v):
    return os.path.join(REPO, "webcam_bewegung_%s.py" % v.replace(".", "_"))


def neue_version(text_aenderung, ziel=""):
    alt = version()
    a = [int(x) for x in alt.split(".")]
    neu = ziel or "%d.%d.%d" % (a[0], a[1], a[2] + 1)
    for name in teile():                                       # the number at every place (title, build, help, file name)
        t = lesen(name)
        t2 = (t.replace(alt.replace(".", "_"), neu.replace(".", "_")).replace('APP_VERSION = "%s"' % alt, 'APP_VERSION = "%s"' % neu)
              .replace("Motion Watch %s" % alt, "Motion Watch %s" % neu).replace("MoveEye %s" % alt, "MoveEye %s" % neu).replace("{tr('Build')} %s ·" % alt, "{tr('Build')} %s ·" % neu))
        if name.startswith("300_"):                            # the 3D simulator that belongs to this version
            try:
                d = json.load(open(os.path.join(REPO, "simulator3d", "version.json")))
                t2 = re.sub(r'SIM3D = \{"version": "3D-[0-9.]+".*?"\}', lambda m: 'SIM3D = {"version": "%s", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": %d,\n         "sha256": "%s"}' % (d["version"], d["size"], d["sha256"]), t2, count=1, flags=re.S)
                if "pi" in d:
                    t2 = re.sub(r'SIM3DPI = \{"version": "3D-[0-9.]+".*?"label": "MW Sim · 3D \(Pi\)"\}', lambda m: 'SIM3DPI = {"version": "%s", "file": "%s", "size": %d,\n           "sha256": "%s", "stem": "MotionWatch3D_Pi", "label": "MW Sim · 3D (Pi)"}' % (d["version"], d["pi"]["file"], d["pi"]["size"], d["pi"]["sha256"]), t2, count=1, flags=re.S)
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
    ap.add_argument("--signieren", metavar="SCHLUESSEL", default="", help="versions.json schreiben und signieren, Selbsttest")
    a = ap.parse_args()
    if a.pruefen:
        if not doppelte_melden():
            return 1
        text = zusammensetzen()
        f = dateiname(version(text))
        if not os.path.isfile(f):
            print("FEHLT: %s – zuerst bauen" % os.path.basename(f))
            return 1
        if open(f, encoding="utf-8", newline="").read() != text:
            print("UNTERSCHIED: %s passt nicht zu quelle/ – werkzeuge/bauen.py laufen lassen (nie die grosse Datei von Hand ändern)" % os.path.basename(f))
            return 1
        print("ok: %s = quelle/ (%d Teile)" % (os.path.basename(f), len(teile())))
        return 0
    if a.neue_version is not None:
        alt, neu = neue_version(a.neue_version, a.version)
        print("Version %s → %s" % (alt, neu))
        fa, fn = dateiname(alt), dateiname(neu)
        if os.path.isfile(fa) and alt.split(".")[:2] == neu.split(".")[:2]:   # only the newest file of a main version stays
            if git("rm", "-q", os.path.basename(fa)).returncode != 0:
                os.remove(fa)
    if not doppelte_melden():
        return 1
    text = zusammensetzen()
    f = dateiname(version(text))
    with open(f, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        return 1
    print("gebaut: %s (%d Zeilen aus %d Teilen)" % (os.path.basename(f), text.count("\n"), len(teile())))
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
