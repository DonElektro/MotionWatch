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
  python3 werkzeuge/versionen.py --aufraeumen [--nur-zeigen]  # höchstens 10 Hauptversionen X.Y behalten, die Brücke nie löschen

Brücke (Entscheid Daniel 31.10.2026): BRUECKE (3.0.2, eine Datei unter 8 MiB, braucht keine Zusatzdatei) bleibt für immer in
versions.json und im Repository. Geräte bis 2.98.x nehmen nur Dateien bis 8 MiB an. Die neueste Hauptdatei bleibt darum
auch unter 8 MiB (grosse Teile in moveeye_daten_X_Y_Z.zip, bauen.py) - dann gehen alte Geräte direkt auf die neueste.
Wäre eine Datei je grösser, schreibt --make-manifest «needs»: "3.0.0" in ihren Eintrag; Geräte ab dem Verkleinern-Paket
nehmen dann zuerst die Brücke (update_pick, Teil 397); ältere Geräte (2.98.x bis zur letzten Version ohne Zusatzdatei) wählen 3.0.2 von Hand.
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
BRUECKE = "3.0.2"                   # = UPD_BRIDGE in quelle/397_zusatzdaten_nachladen.py
MAX_ALT = 8 * 1024 * 1024           # Grenze der Geräte bis 2.98.x
ZIEL = 5 * 1024 * 1024              # Ziel für die Hauptdatei (Platz für Wachstum)
MAX_HAUPT = 10                      # höchstens 10 Hauptversionen X.Y im Repository
VFILE = re.compile(r"^webcam_bewegung_(\d{1,3})_(\d{1,3})_(\d{1,3})\.py$")


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
    probleme += groesse_bruecke(app)
    for p in probleme:
        print("PROBLEM: " + p)
    print("ok" if not probleme else "%d Probleme" % len(probleme))
    return 1 if probleme else 0


def groesse_bruecke(app):
    """Hauptdatei unter 8 MiB (alte Geräte) mit ihrer Zusatzdatei; die Brücke ist da, unter 8 MiB und in versions.json"""
    out = []
    f = os.path.join(REPO, "webcam_bewegung_%s.py" % app.replace(".", "_"))
    if os.path.isfile(f):
        n = os.path.getsize(f)
        print("Hauptdatei %s: %d Bytes (%.2f MiB)" % (os.path.basename(f), n, n / 1048576))
        if n >= MAX_ALT:
            out.append("%s ist %.2f MiB - Geräte bis 2.98.x nehmen höchstens 8 MiB an" % (os.path.basename(f), n / 1048576))
        elif n >= ZIEL:
            print("Hinweis: über dem Ziel von 5 MiB - mehr in die Zusatzdatei (bauen.py ZD_MIN / ZD_KEEP_NAMES)")
        txt = lesen(f)
        m = re.search(r'^ZD_FILE = "([^"]+)"', txt, re.M)
        if m and not os.path.isfile(os.path.join(REPO, m.group(1))):
            out.append("Zusatzdatei %s fehlt neben %s" % (m.group(1), os.path.basename(f)))
    b = os.path.join(REPO, "webcam_bewegung_%s.py" % BRUECKE.replace(".", "_"))
    if not os.path.isfile(b):
        out.append("Brücke %s fehlt (darf nie gelöscht werden)" % os.path.basename(b))
    elif os.path.getsize(b) >= MAX_ALT:
        out.append("Brücke %s ist nicht unter 8 MiB" % os.path.basename(b))
    try:
        vs = json.load(open(os.path.join(REPO, "versions.json"), encoding="utf-8")).get("versions") or []
        if not any(e.get("version") == BRUECKE for e in vs):
            out.append("Brücke %s fehlt in versions.json" % BRUECKE)
    except (OSError, ValueError):
        out.append("versions.json nicht lesbar")
    return out


def aufraeumen(nur_zeigen=False):
    """höchstens MAX_HAUPT Hauptversionen X.Y (je die neueste Datei); die Brücke bleibt immer (zählt mit)"""
    import subprocess
    files = sorted((tuple(int(x) for x in m.groups()), n) for n in os.listdir(REPO) for m in [VFILE.match(n)] if m)
    neu = {}
    for k, n in files:
        neu[k[:2]] = (k, n)                                  # pro X.Y die neueste
    weg = [n for k, n in files if neu[k[:2]][1] != n]         # ältere Dateien derselben Hauptversion
    haupt = sorted(neu.values(), reverse=True)
    br = tuple(int(x) for x in BRUECKE.split("."))
    rest = [x for x in haupt if x[0] != br]
    platz = MAX_HAUPT - (1 if any(x[0] == br for x in haupt) else 0)
    weg += [n for _k, n in rest[platz:]]
    weg = [n for n in weg if n != "webcam_bewegung_%s.py" % BRUECKE.replace(".", "_")]   # nie die Brücke
    for n in weg:
        z = "moveeye_daten_" + n[len("webcam_bewegung_"):-3] + ".zip"
        for x in (n, z):
            if not os.path.isfile(os.path.join(REPO, x)):
                continue
            print(("würde löschen: " if nur_zeigen else "gelöscht: ") + x)
            if not nur_zeigen and subprocess.run(["git", "rm", "-q", x], cwd=REPO).returncode != 0:
                os.remove(os.path.join(REPO, x))
    print("%d Hauptversionen, Brücke %s bleibt" % (min(len(haupt), MAX_HAUPT), BRUECKE))
    return 0


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
    ap.add_argument("--aufraeumen", action="store_true", help="höchstens 10 Hauptversionen, die Brücke bleibt")
    ap.add_argument("--nur-zeigen", action="store_true", help="mit --aufraeumen: nur anzeigen")
    a = ap.parse_args()
    if a.aufraeumen:
        return aufraeumen(a.nur_zeigen)
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
