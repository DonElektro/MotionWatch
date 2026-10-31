#!/usr/bin/env python3
"""Versionsnummern von MoveEye und dem 3D-Simulator (Versionierung 3.0.0, Entscheid Daniel 31.10.2026).

Ab 3.0.0 haben beide dieselbe Nummer X.Y.Z («MoveEye 3.0.0» / «MoveEye Sim 3.0.0») und werden zusammen veröffentlicht.
Brücke: alte Simulatoren (bis 3D-4.8x) lesen in simulator3d/version.json nur «version» und vergleichen «3D-A.B» als Zahlen.
Darum steht dort «3D-(X+2).Y.Z» (3.0.0 -> «3D-5.0.0») und die echte Nummer in «ver». Gleiche Regel wie
simulator3d/scripts/versionen.gd und sim_vkey() in quelle/300_werkzeuge_simulator3d.py.

  python3 werkzeuge/versionen.py --test                       # Reihenfolge der Nummern prüfen (ohne Dateien)
  python3 werkzeuge/versionen.py --pruefen                    # passen main.gd, version.json, SIM3D, APP_VERSION zusammen?
  python3 werkzeuge/versionen.py --sim-json 3.0.0 "Notiz"     # simulator3d/version.json aus der ZIP schreiben (beide Felder)
  python3 werkzeuge/versionen.py --neu-data                   # scripts/neu_data.gd aus «Lies mich.txt» (NEU IN …, beide Schemas)
"""
import argparse
import hashlib
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
SIM = os.path.join(REPO, "simulator3d")
ZIP_REL = "simulator3d/MotionWatch3D_Simulator.zip"
SHIFT = 2


def sim_key(v):
    """«3D-4.82» -> (2, 82, 0), «3D-5.0.0» / «3.0.0» / «MoveEye Sim 3.0.0» -> (3, 0, 0); None = keine Nummer"""
    s = str(v or "")
    m = re.search(r"3D-(\d+)\.(\d+)(?:\.(\d+))?", s)
    if m:
        return (int(m.group(1)) - SHIFT, int(m.group(2)), int(m.group(3) or 0))
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", s)
    return tuple(int(x or 0) for x in m.groups()) if m else None


def mw_key(v):
    """wie _vkey() in quelle/380_updates.py (MoveEye-Updates)"""
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


def legacy(v):
    """3.0.0 -> «3D-5.0.0» (was alte Simulatoren in version.json «version» lesen)"""
    s = str(v).strip()
    if "3D-" in s:
        return s
    a, b, c = (int(x) for x in s.split("."))
    return "3D-%d.%d.%d" % (a + SHIFT, b, c)


def alt_sim_newer(a, b):
    """genau der Vergleich der alten Simulatoren (update.gd bis 3D-4.8x): «3D-» weg, an «.» trennen, int() wie Godot
    (Godot nimmt aus «MoveEye Sim 3» die Ziffern: 3)"""
    def num(p):
        d = re.sub(r"[^0-9]", "", p)
        return int(d) if d else 0
    x = [num(p) for p in str(a).replace("3D-", "", 1).split(".")] if str(a).startswith("3D-") else [num(p) for p in str(a).split(".")]
    y = [num(p) for p in str(b).replace("3D-", "", 1).split(".")] if str(b).startswith("3D-") else [num(p) for p in str(b).split(".")]
    for i in range(max(len(x), len(y))):
        p = x[i] if i < len(x) else 0
        q = y[i] if i < len(y) else 0
        if p != q:
            return p > q
    return False


def test():
    fehler = []

    def ok(bed, was):
        print(("ok   " if bed else "FEHLER ") + was)
        if not bed:
            fehler.append(was)
    mw = ["2.98.113", "2.98.114", "3.0.0", "3.0.1", "3.1.0", "3.1.1", "3.10.0", "4.0.0"]
    for a, b in zip(mw, mw[1:]):
        ok(mw_key(a) < mw_key(b), "MoveEye %s < %s" % (a, b))
    vfile = re.compile(r"^webcam_bewegung_(\d{1,3})_(\d{1,3})_(\d{1,3})\.py$")      # VFILE_RE in 380 (auch in alten Geräten)
    for v in mw[2:]:
        ok(bool(vfile.match("webcam_bewegung_%s.py" % v.replace(".", "_"))), "Dateiname webcam_bewegung_%s.py passt zu VFILE_RE" % v.replace(".", "_"))
    sims = ["3D-4.82", "3D-4.83", "3.0.0", "3.0.1", "3.1.0", "3.10.0", "4.0.0"]
    for a, b in zip(sims, sims[1:]):
        ok(sim_key(a) < sim_key(b), "Simulator %s < %s (neuer Vergleich)" % (a, b))
    for cur in ("3D-4.82", "3D-4.83", "3D-4.99"):
        ok(not alt_sim_newer("3.0.0", cur), "ohne Brücke: alter Simulator %s hält «3.0.0» NICHT für neuer (darum die Brücke)" % cur)
        ok(alt_sim_newer(legacy("3.0.0"), cur), "mit Brücke: alter Simulator %s findet %s" % (cur, legacy("3.0.0")))
    for a, b in zip(["3.0.0", "3.0.1", "3.1.0", "3.9.9", "3.10.0", "4.0.0"], ["3.0.1", "3.1.0", "3.9.9", "3.10.0", "4.0.0", "4.0.1"]):
        ok(alt_sim_newer(legacy(b), legacy(a)), "Brücke bleibt in Reihenfolge: %s > %s" % (legacy(b), legacy(a)))
        ok(sim_key(legacy(b)) == sim_key(b), "%s wird wieder als %s gelesen" % (legacy(b), b))
    return 1 if fehler else 0


def lesen(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def pruefen():
    probleme = []
    gd = re.search(r'^const VERSION := "([^"]+)"', lesen(os.path.join(SIM, "scripts", "main.gd")), re.M).group(1)
    vj = json.load(open(os.path.join(SIM, "version.json"), encoding="utf-8"))
    q300 = lesen(os.path.join(REPO, "quelle", "300_werkzeuge_simulator3d.py"))
    s3d = re.search(r'^SIM3D = \{"version": "([^"]+)"', q300, re.M).group(1)
    app = re.search(r'^APP_VERSION = "([^"]+)"', lesen(os.path.join(REPO, "quelle", "010_grundlagen.py")), re.M).group(1)
    ver, alt = str(vj.get("ver") or ""), str(vj.get("version") or "")
    print("main.gd VERSION %s · version.json ver %s / version %s · SIM3D %s · APP_VERSION %s" % (gd, ver or "-", alt, s3d, app))
    if not alt.startswith("3D-"):
        probleme.append("version.json «version» muss «3D-…» bleiben (alte Simulatoren), ist %r" % alt)
    if ver and alt != legacy(ver):
        probleme.append("version.json «version» %s muss %s sein" % (alt, legacy(ver)))
    if (ver or alt) not in (gd,) and sim_key(ver or alt) != sim_key(gd):
        probleme.append("version.json (%s) passt nicht zu main.gd VERSION %s" % (ver or alt, gd))
    if "3D-" not in gd and ver != gd:
        probleme.append("main.gd VERSION %s ist im neuen Schema, dann braucht version.json «ver»: %s" % (gd, gd))
    if s3d not in (ver, alt) or (ver and s3d != ver):
        probleme.append("SIM3D (300) %s sollte %s sein" % (s3d, ver or alt))
    if mw_key(app) >= (3, 0, 0) and not (app == gd == ver == s3d):
        probleme.append("ab 3.0.0 eine Nummer für alles: APP_VERSION %s, main.gd %s, version.json ver %s, SIM3D %s" % (app, gd, ver or "-", s3d))
    if "NEU IN %s\n" % gd not in lesen(os.path.join(SIM, "Lies mich.txt")):
        probleme.append("«Lies mich.txt» hat keinen Block «NEU IN %s»" % gd)
    for p in probleme:
        print("PROBLEM: " + p)
    print("ok" if not probleme else "%d Probleme" % len(probleme))
    return 1 if probleme else 0


def sim_json(v, notes, zip_path=""):
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", v):
        sys.exit("Nummer %s passt nicht zum Schema X.Y.Z" % v)
    z = zip_path or os.path.join(REPO, ZIP_REL)
    with open(z, "rb") as f:
        data = f.read()
    d = {"version": legacy(v), "ver": v, "name": "MoveEye Sim " + v, "file": ZIP_REL, "size": len(data),
         "sha256": hashlib.sha256(data).hexdigest(), "notes": notes}
    with open(os.path.join(SIM, "version.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    print("version.json: ver %s (alte Simulatoren lesen %s), %d Bytes" % (v, d["version"], d["size"]))
    return 0


def neu_data(n=15):
    """wie neugen.py des Integrators, aber für «NEU IN 3D-4.82» und «NEU IN 3.0.0»"""
    s = lesen(os.path.join(SIM, "Lies mich.txt"))
    out = []
    for m in re.finditer(r"^NEU IN ((?:3D-)?[\d.]+)\n(.*?)(?=^NEU IN |\Z)", s, re.S | re.M):
        v = m.group(1).rstrip(".")
        t = re.sub(r"^" + re.escape(v) + r":\s*", "", " ".join(m.group(2).split()))
        out.append((v, t))
    out.sort(key=lambda x: sim_key(x[0]), reverse=True)
    g = ("extends RefCounted\n## generated from «Lies mich.txt» by neugen.py - the NEU IN blocks for the popup «Neu in dieser Version» (news.gd)\n\n"
         "const LOG := [\n")
    for v, t in out[:n]:
        g += '\t["%s", "%s"],\n' % (v, t.replace("\\", "\\\\").replace('"', '\\"'))
    g += "]\n"
    with open(os.path.join(SIM, "scripts", "neu_data.gd"), "w", encoding="utf-8") as f:
        f.write(g)
    print(len(out[:n]), "entries")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Versionsnummern MoveEye / MoveEye Sim (ab 3.0.0 eine Nummer)")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--pruefen", action="store_true")
    ap.add_argument("--sim-json", nargs=2, metavar=("X.Y.Z", "NOTIZ"))
    ap.add_argument("--zip", default="", help="mit --sim-json: diese ZIP statt simulator3d/MotionWatch3D_Simulator.zip")
    ap.add_argument("--neu-data", action="store_true")
    a = ap.parse_args()
    if a.test:
        return test()
    if a.pruefen:
        return pruefen()
    if a.sim_json:
        return sim_json(a.sim_json[0], a.sim_json[1], a.zip)
    if a.neu_data:
        return neu_data()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
