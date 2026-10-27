#!/usr/bin/env python3
"""Setzt Motion Watch aus den Teilen in quelle/ zu der einen Datei webcam_bewegung_X_Y_Z.py zusammen.

Der Pi, die Update-Funktion und die Signatur arbeiten weiter mit dieser einen Datei; bearbeitet wird in quelle/.

  python3 werkzeuge/bauen.py                       # baut die Datei der aktuellen Version (APP_VERSION in quelle/010_grundlagen.py)
  python3 werkzeuge/bauen.py --pruefen             # nur vergleichen: passt die Datei im Repository zu quelle/? (GitHub-Prüfung)
  python3 werkzeuge/bauen.py --neue-version "Text" # nächste Version (X.Y.Z+1): Nummer an allen Stellen, Zeile in der
                                                   #   Änderungsliste, Simulator-Version aus simulator3d/version.json, bauen
  python3 werkzeuge/bauen.py --neue-version "Text" --version 2.96.0     # eine bestimmte Nummer
  python3 werkzeuge/bauen.py --signieren SCHLUESSELDATEI                 # danach: versions.json schreiben, signieren, Selbsttest

Den Schlüssel nie ins Repository legen.
"""
import argparse
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
              .replace("Motion Watch %s" % alt, "Motion Watch %s" % neu).replace("{tr('Build')} %s ·" % alt, "{tr('Build')} %s ·" % neu))
        if name.startswith("300_"):                            # the 3D simulator that belongs to this version
            try:
                d = json.load(open(os.path.join(REPO, "simulator3d", "version.json")))
                t2 = re.sub(r'SIM3D = \{"version": "3D-[0-9.]+".*?"\}', lambda m: 'SIM3D = {"version": "%s", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": %d,\n         "sha256": "%s"}' % (d["version"], d["size"], d["sha256"]), t2, count=1, flags=re.S)
                if "pi" in d:
                    t2 = re.sub(r'SIM3DPI = \{"version": "3D-[0-9.]+".*?"label": "MW Sim · 3D \(Pi\)"\}', lambda m: 'SIM3DPI = {"version": "%s", "file": "%s", "size": %d,\n           "sha256": "%s", "stem": "MotionWatch3D_Pi", "label": "MW Sim · 3D (Pi)"}' % (d["version"], d["pi"]["file"], d["pi"]["size"], d["pi"]["sha256"]), t2, count=1, flags=re.S)
            except (OSError, ValueError, KeyError):
                pass
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
