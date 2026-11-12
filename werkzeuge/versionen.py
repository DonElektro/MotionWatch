#!/usr/bin/env python3
"""Versionsnummern der drei Spuren: 📷 MoveEye, 🎮 MoveEye Sim, 🧩 Gehäuse (Drei Spuren, Entscheid des Besitzers 03.11.2026).

Bis zum Zusammenführen hat jede Spur ihre eigene Nummer und wird allein veröffentlicht (Berichte immer mit Vorsilbe, z. B.
«MoveEye 3.56.0 · Sim 3.55.4 · Gehäuse 5.3.0»):
  MoveEye  = APP_VERSION (quelle/010) + Eintrag in versions.json (signiert)
  Sim      = VERSION in simulator3d/scripts/main.gd + simulator3d/version.json («ver», Brücke «version», Block «linux») + «NEU IN»
             in «Lies mich.txt»; signiert als Block «sim» in versions.json (MoveEye prüft /sim damit, Teil 300)
  Gehäuse  = «version» in hardware/gehaeuse/bau.json
Verträglichkeit statt gleicher Nummer: SIM_MIN (MoveEye, Teil 545) und MW_MIN (simulator3d/scripts/abgleich.gd, auch «mw_min»
in version.json). Die alte Regel «eine Nummer für alles» (ab 3.0.0) ist bis zum Zusammenführen ausgesetzt.
Brücke: alte Simulatoren (bis 3D-4.8x) lesen in simulator3d/version.json nur «version» und vergleichen «3D-A.B» als Zahlen.
Darum steht dort «3D-(X+2).Y.Z» (3.0.0 -> «3D-5.0.0») und die echte Nummer in «ver». Gleiche Regel wie
simulator3d/scripts/versionen.gd und sim_vkey() in quelle/300_werkzeuge_simulator3d.py.

  python3 werkzeuge/versionen.py --test                       # Reihenfolge der Nummern prüfen (ohne Dateien)
  python3 werkzeuge/versionen.py --pruefen                    # jede Spur für sich (Exit 1 nur bei Problemen, sonst Warnungen)
  python3 werkzeuge/versionen.py --spuren                     # nur die Nummern: «MoveEye 3.56.0 · Sim 3.55.4 · Gehäuse 5.3.0»
  python3 werkzeuge/versionen.py --sim-json 3.0.0 "Notiz"     # simulator3d/version.json aus der ZIP schreiben (beide Felder)
  python3 werkzeuge/versionen.py --anhang-json 3.68.0 "Notiz" # Block «anhang» (Pakete als Release-Asset, ab der Version nach 3.67.2)
  python3 werkzeuge/versionen.py --pi-json                    # nur den Block «pi» (MoveEyeSim3D_Pi.zip, Release-Asset sim-X.Y.Z)
  python3 werkzeuge/versionen.py --linux-json                 # nur den Block «linux» (MoveEyeSim3D_Linux.zip) in version.json
  python3 werkzeuge/versionen.py --neu-data                   # scripts/neu_data.gd aus «Lies mich.txt» (NEU IN …, beide Schemas)
  python3 werkzeuge/versionen.py --aufraeumen [--nur-zeigen]  # höchstens 10 Hauptversionen X.Y behalten, die Brücke nie löschen

Brücke (Entscheid des Besitzers 31.10.2026): BRUECKE (3.0.2, eine Datei unter 8 MiB, braucht keine Zusatzdatei) bleibt für immer in
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
REPO = os.environ.get("MW_VERSIONEN_REPO") or os.path.dirname(HIER)     # anderer Ordner nur für versionen_spuren_test.py
SIM = os.path.join(REPO, "simulator3d")
ZIP_REL = "simulator3d/MotionWatch3D_Simulator.zip"
LINUX_REL = "simulator3d/MoveEyeSim3D_Linux.zip"   # Paket Linux (werkzeuge/linux_paket.sh, update.gd linux_info)
# Paket Pi (Raspberry Pi 5, arm64, «Simulator intern» Teil 639zx): NICHT im Repository (37 MB), sondern als Release-Asset am
# Tag sim-X.Y.Z. Lokal liegt es beim Packen unter PI_REL (.gitignore); Grösse + Prüfsumme kommen in version.json «pi» und
# signiert in versions.json «sim.pi» (390 sim_manifest_block). MoveEye lädt von «url», prüft die signierte SHA-256.
PI_REL = "simulator3d/MoveEyeSim3D_Pi.zip"
PI_URL = "https://github.com/DonElektro/MotionWatch/releases/download/sim-%s/MoveEyeSim3D_Pi.zip"
# Simulator-Anhang (Besitzer 12.11.2026, «Ablage entlasten»): ab der Version NACH Sim 3.67.2 kommen auch das Windows- und das
# Linux-Paket nicht mehr ins Repository, sondern als Release-Asset an sim-X.Y.Z (Workflow «Sim-Pakete», sim_pi.yml). Die
# Pakete von Sim 3.67.2 bleiben für immer unter ZIP_REL / LINUX_REL liegen (wie die Brücke 3.0.2): alte Simulatoren, alte
# MoveEye und ein alter HP holen sie wie bisher und kommen von dort weiter. In version.json bleiben darum die obersten Felder
# und «linux» EINGEFROREN (= Sim 3.67.2); die neuste Version steht im Block «anhang» {ver, version, notes, mw_min,
# win: {file, ver, size, sha256, url}, linux: {…}} und signiert in versions.json «sim.anhang» (Teil 300 / 390).
# Lokal liegen die geholten Assets unter simulator3d/anhang/ (.gitignore), nur zum Nachrechnen vor dem Signieren.
ANHANG_REL = {"win": "simulator3d/anhang/MotionWatch3D_Simulator.zip", "linux": "simulator3d/anhang/MoveEyeSim3D_Linux.zip"}
ANHANG_URL = "https://github.com/DonElektro/MotionWatch/releases/download/sim-%s/%s"
ANHANG_HINWEIS = (" · Neuere Versionen holt sich der Simulator nach dem Start selbst (zweites Update). "
                  "Für den Download der neusten Version direkt aus MoveEye: bitte zuerst MoveEye aktualisieren.")
SHIFT = 2
BRUECKE = "3.0.2"                   # = UPD_BRIDGE in quelle/397_zusatzdaten_nachladen.py
MAX_ALT = 8 * 1024 * 1024           # Grenze der Geräte bis 2.98.x
ZIEL = 5 * 1024 * 1024              # Schlank (3.59.0): Grenze der Hauptdatei (= bauen.py GROESSE_MAX), darüber Problem
ZIEL_WARN = 4 * 1024 * 1024         # darüber Hinweis (= bauen.py GROESSE_WARN)
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


def git_text(*a):
    """Ausgabe von git im Repository oder None (kein git, keine Geschichte - z. B. flacher Klon)"""
    import subprocess
    try:
        r = subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def geaendert_seit(base, pfade, ohne=()):
    """Dateien unter pfade, die seit Commit base geändert sind (auch nicht committete und neue); None = unbekannt"""
    if not base:
        return None
    a = git_text("diff", "--name-only", base, "--", *pfade)
    b = git_text("ls-files", "--others", "--exclude-standard", "--", *pfade)
    if a is None or b is None:
        return None
    out = sorted({x for x in (a + b).splitlines() if x.strip()})
    return [x for x in out if not any(x == o or (o.endswith("/") and x.startswith(o)) for o in ohne)]


def mw_min_gd():
    """MW_MIN in simulator3d/scripts/abgleich.gd: die älteste MoveEye, mit der dieser Simulator arbeitet ("" = keine Angabe)"""
    try:
        m = re.search(r'^const MW_MIN := "([^"]+)"', lesen(os.path.join(SIM, "scripts", "abgleich.gd")), re.M)
    except OSError:
        m = None
    return m.group(1) if m else ""


def werte():
    """die Nummern aller drei Spuren aus den Dateien (ohne Prüfung)"""
    w = {}
    w["app"] = re.search(r'^APP_VERSION = "([^"]+)"', lesen(os.path.join(REPO, "quelle", "010_grundlagen.py")), re.M).group(1)
    w["gd"] = re.search(r'^const VERSION := "([^"]+)"', lesen(os.path.join(SIM, "scripts", "main.gd")), re.M).group(1)
    w["vj"] = json.load(open(os.path.join(SIM, "version.json"), encoding="utf-8"))
    q300 = lesen(os.path.join(REPO, "quelle", "300_werkzeuge_simulator3d.py"))
    w["s3d"] = re.search(r'^SIM3D = \{"version": "([^"]+)"', q300, re.M).group(1)
    m = re.search(r'^SIM_MIN = "([^"]+)"', lesen(os.path.join(REPO, "quelle", "545_simulator_updates.py")), re.M)
    w["sim_min"] = m.group(1) if m else ""
    w["mw_min"] = mw_min_gd()
    try:
        w["geh"] = str(json.load(open(os.path.join(REPO, "hardware", "gehaeuse", "bau.json"), encoding="utf-8")).get("version") or "")
    except (OSError, ValueError):
        w["geh"] = ""
    return w


def spuren_text(w=None):
    w = w or werte()
    return "MoveEye %s · Sim %s · Gehäuse %s" % (w["app"], sim_stand(w["vj"]) or w["gd"], w["geh"] or "?")


def sim_stand(vj):
    """die veröffentlichte Sim-Nummer: «anhang.ver» (Pakete als Release-Asset), sonst «ver» (Pakete im Repository)"""
    ah = vj.get("anhang") if isinstance(vj, dict) and isinstance(vj.get("anhang"), dict) else {}
    return str(ah.get("ver") or vj.get("ver") or "")


SIM_OHNE = ("simulator3d/version.json", "simulator3d/MotionWatch3D_Simulator.zip", "simulator3d/MoveEyeSim3D_Linux.zip",
            "simulator3d/scripts/neu_data.gd", "simulator3d/Lies mich.txt", "simulator3d/UEBERGABE.md",
            "simulator3d/i18n/abdeckung.txt", "simulator3d/pruefnaechte/", "simulator3d/anhang/")


SIM_HP = ["werkzeuge/test_runner/" + f for f in ("hp_update.sh", "job_start.sh", "job_ende.sh", "runner_dienst.conf",
                                                 "runner_entfernen.sh")] + ["werkzeuge/linux_paket.sh"]


def geh_basis(cur):
    """der Commit, mit dem «version» in bau.json zuletzt auf cur gesetzt wurde (None = unbekannt)"""
    rel = "hardware/gehaeuse/bau.json"
    log = git_text("log", "--format=%H", "-n", "80", "--", rel)
    if log is None:
        return None
    last = None
    for c in log.split():
        try:
            alt = json.loads(git_text("show", c + "^:" + rel) or "{}").get("version")
        except ValueError:
            alt = None
        last = c
        if str(alt) != cur:
            return c
    return last


def pruefen():
    """Drei Spuren: jede Spur für sich. PROBLEM (Exit 1) = so nicht veröffentlichen; WARNUNG = Nummer vergessen?"""
    probleme, warn = [], []
    w = werte()
    app, gd, vj, s3d = w["app"], w["gd"], w["vj"], w["s3d"]
    ver, alt = str(vj.get("ver") or ""), str(vj.get("version") or "")
    stand = sim_stand(vj)                                    # Simulator-Anhang: die veröffentlichte Nummer («anhang.ver», sonst ver)
    print("Spuren: " + spuren_text(w))
    print("  📷 MoveEye: APP_VERSION %s · SIM3D (eingebettet) %s · braucht Sim ≥ %s" % (app, s3d, w["sim_min"] or "-"))
    print("  🎮 Sim: main.gd %s · version.json ver %s / Brücke %s%s · braucht MoveEye ≥ %s"
          % (gd, ver or "-", alt, (" (im Repository, eingefroren) · Anhang %s" % stand) if stand != ver else "", w["mw_min"] or "-"))
    print("  🧩 Gehäuse: bau.json %s" % (w["geh"] or "-"))
    # ---- 📷 MoveEye
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", app):
        probleme.append("APP_VERSION %s passt nicht zum Schema X.Y.Z (je 1-3 Ziffern, VFILE_RE der Geräte)" % app)
    probleme += groesse_bruecke(app)
    try:
        man = json.load(open(os.path.join(REPO, "versions.json"), encoding="utf-8"))
    except (OSError, ValueError):
        man = {}
    if not any(e.get("version") == app for e in man.get("versions") or []):
        warn.append("MoveEye %s steht noch nicht in versions.json (rel_mw.sh signiert)" % app)
    else:                                                    # schon veröffentlicht: quelle/ seither geändert?
        q = geaendert_seit((git_text("log", "-1", "-m", "--format=%H", "-G", '"version": "%s"' % re.escape(app), "--", "versions.json") or "").strip(),
                           ["quelle"])
        if q:
            warn.append("MoveEye geändert seit %s (%d Teile, z. B. %s), Nummer nicht erhöht (bauen.py --neue-version)"
                        % (app, len(q), ", ".join(q[:3])))
    # ---- 🎮 Sim
    if not alt.startswith("3D-"):
        probleme.append("version.json «version» muss «3D-…» bleiben (alte Simulatoren), ist %r" % alt)
    if ver and alt != legacy(ver):
        probleme.append("version.json «version» %s muss %s sein (Brücke aus «ver»)" % (alt, legacy(ver)))
    if "3D-" not in gd and not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", gd):
        probleme.append("main.gd VERSION %s passt nicht zum Schema X.Y.Z" % gd)
    if stand and sim_key(gd) and sim_key(stand):
        if sim_key(gd) < sim_key(stand):
            probleme.append("main.gd VERSION %s ist älter als version.json %s" % (gd, stand))
        elif sim_key(gd) > sim_key(stand):
            warn.append("Sim %s gesetzt, version.json hat noch %s - exportieren und packen (rel_sim.sh)" % (gd, stand))
    if "NEU IN %s\n" % gd not in lesen(os.path.join(SIM, "Lies mich.txt")):
        probleme.append("«Lies mich.txt» hat keinen Block «NEU IN %s»" % gd)
    try:                                                     # die Brücke darf nie kleiner werden (alte Simulatoren)
        alt_vj = json.loads(git_text("show", "HEAD:simulator3d/version.json") or "{}")
    except ValueError:
        alt_vj = {}
    av = str(alt_vj.get("version") or "")
    if av and alt and alt_sim_newer(av, alt):
        probleme.append("Brücke kleiner geworden: %s -> %s (alte Simulatoren fänden kein Update mehr)" % (av, alt))
    if alt_vj.get("ver") and ver and sim_key(str(alt_vj["ver"])) and sim_key(ver) < sim_key(str(alt_vj["ver"])):
        probleme.append("Sim-Nummer kleiner geworden: %s -> %s" % (alt_vj["ver"], ver))
    if sim_stand(alt_vj) and stand and sim_key(sim_stand(alt_vj)) and sim_key(stand) and sim_key(stand) < sim_key(sim_stand(alt_vj)):
        probleme.append("veröffentlichte Sim-Nummer kleiner geworden: %s -> %s" % (sim_stand(alt_vj), stand))
    ap_, aw_ = anhang_pruefen(vj, alt_vj, man)
    probleme += ap_; warn += aw_
    if ver and sim_key(s3d) and sim_key(s3d) > sim_key(ver):
        probleme.append("SIM3D (300) %s ist neuer als version.json ver %s" % (s3d, ver))
    sm = man.get("sim") if isinstance(man.get("sim"), dict) else None
    if ver and sim_key(s3d) != sim_key(ver) and not (sm and sm.get("ver") == ver):
        warn.append("Sim %s steht nicht signiert in versions.json («sim»), MoveEye kennt nur %s - /sim liefert erst nach "
                    "rel_sim.sh (signieren) die neue Fassung" % (ver, s3d))
    elif sm and sm.get("ver") != ver:
        warn.append("versions.json «sim» ist %s, version.json %s - neu signieren (rel_sim.sh)" % (sm.get("ver"), ver))
    if sm:
        for key, e in (("win", vj), ("linux", vj.get("linux") or {})):
            x = sm.get(key) or {}
            if x and (x.get("sha256") != e.get("sha256") or x.get("size") != e.get("size")):
                warn.append("versions.json «sim.%s» passt nicht zu version.json (Grösse/Prüfsumme) - neu signieren" % key)
    if w["mw_min"] and mw_key(w["mw_min"]) > mw_key(app):
        probleme.append("der Simulator braucht MoveEye ≥ %s (abgleich.gd MW_MIN), APP_VERSION ist %s - zuerst MoveEye veröffentlichen" % (w["mw_min"], app))
    if vj.get("mw_min") and w["mw_min"] and str(vj.get("mw_min")) != w["mw_min"] and sim_key(gd) == sim_key(ver) and stand == ver:
        warn.append("version.json «mw_min» %s ≠ abgleich.gd MW_MIN %s - --sim-json neu schreiben" % (vj.get("mw_min"), w["mw_min"]))
    if w["sim_min"] and ver and sim_key(w["sim_min"]) > sim_key(ver):
        probleme.append("MoveEye braucht Sim ≥ %s (545 SIM_MIN), version.json ist %s - zuerst den Simulator veröffentlichen" % (w["sim_min"], ver))
    ch = geaendert_seit((git_text("log", "-1", "--format=%H", "--", "simulator3d/version.json") or "").strip(),
                        ["simulator3d"] + SIM_HP, SIM_OHNE)          # das Linux-Paket bringt auch den HP-Teil mit (linux_paket.sh)
    if sim_stand(alt_vj) != stand:
        ch = []                                              # die Nummer wird gerade erhöht (version.json noch nicht committet)
    if ch and sim_key(gd) == sim_key(stand):
        warn.append("Simulator geändert seit Sim %s (%d Dateien, z. B. %s), Nummer nicht erhöht (main.gd VERSION)"
                    % (stand, len(ch), ", ".join(ch[:3])))
    elif ch is None:
        print("Hinweis: keine git-Geschichte - Änderungen am Simulator nicht geprüft")
    probleme += linux_pruefen(vj)
    pp_, pw_ = pi_pruefen(vj, man)                           # «Simulator intern» auf dem Pi (Release-Asset)
    probleme += pp_; warn += pw_
    # ---- 🧩 Gehäuse
    if w["geh"]:
        if not re.match(r"^\d{1,3}\.\d{1,3}(?:\.\d{1,3})?$", w["geh"]):
            probleme.append("bau.json «version» %s passt nicht zum Schema X.Y[.Z]" % w["geh"])
        try:
            geh_head = str(json.loads(git_text("show", "HEAD:hardware/gehaeuse/bau.json") or "{}").get("version") or "")
        except ValueError:
            geh_head = ""
        gc = geaendert_seit(geh_basis(w["geh"]), ["hardware/gehaeuse"]) if geh_head == w["geh"] else []
        if gc:
            warn.append("Gehäuse geändert seit v%s (%d Dateien, z. B. %s), Nummer nicht erhöht (bau.json «version»)"
                        % (w["geh"], len(gc), ", ".join(gc[:3])))
    else:
        probleme.append("hardware/gehaeuse/bau.json ohne «version»")
    for p in probleme:
        print("PROBLEM: " + p)
    for x in warn:
        print("WARNUNG: " + x)
    print(("ok" if not warn else "ok, %d Warnungen" % len(warn)) if not probleme else "%d Probleme" % len(probleme))
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
        elif n > ZIEL:
            out.append("%s ist %.2f MiB - höchstens 5 MiB (mehr in die Zusatzdatei: bauen.py --groessen, ZD_MIN_KLEIN)"
                       % (os.path.basename(f), n / 1048576))
        elif n > ZIEL_WARN:
            print("Hinweis: über 4 MiB - bald mehr in die Zusatzdatei (bauen.py --groessen, ZD_MIN_KLEIN / ZD_KEEP_NAMES)")
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


def linux_block(v):
    """Block «linux» für version.json - nur wenn die Linux-ZIP da ist und zu Nummer v passt (sonst None: lieber kein
    Update für Linux als eine alte Datei, die der Simulator jedes Mal von Neuem anbietet)"""
    import zipfile
    p = os.path.join(REPO, LINUX_REL)
    if not os.path.isfile(p):
        print("Hinweis: %s fehlt - version.json ohne Linux-Paket" % LINUX_REL)
        return None
    try:
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            lies = z.read("MoveEyeSim3D/Lies mich.txt").decode("utf-8", "replace")
            mode = (z.getinfo("MoveEyeSim3D/MoveEyeSim3D.x86_64").external_attr >> 16) & 0o777
    except (KeyError, zipfile.BadZipFile, OSError) as e:
        print("PROBLEM: %s ist kein Linux-Paket (%s) - version.json ohne Linux-Paket" % (LINUX_REL, e))
        return None
    if "NEU IN %s\n" % v not in lies or "MoveEyeSim3D/installieren.sh" not in names or not mode & 0o100:
        print("PROBLEM: %s passt nicht zu %s (Lies mich, installieren.sh, ausführbar?) - erst neu packen" % (LINUX_REL, v))
        return None
    with open(p, "rb") as f:
        data = f.read()
    return {"file": LINUX_REL, "ver": v, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def linux_json():
    p = os.path.join(SIM, "version.json")
    d = json.load(open(p, encoding="utf-8"))
    lx = linux_block(str(d.get("ver") or ""))
    if lx is None:
        return 1
    d["linux"] = lx
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    print("version.json: linux %s, %d Bytes" % (lx["ver"], lx["size"]))
    return 0


def linux_pruefen(vj):
    lx = vj.get("linux")
    if not isinstance(lx, dict):
        print("Hinweis: version.json ohne Linux-Paket")
        return []
    out = []
    p = os.path.join(REPO, str(lx.get("file", "")))
    if not os.path.isfile(p):
        return ["Linux-Paket %s fehlt" % lx.get("file")]
    with open(p, "rb") as f:
        data = f.read()
    if len(data) != lx.get("size") or hashlib.sha256(data).hexdigest() != lx.get("sha256"):
        out.append("Linux-Paket %s passt nicht zu version.json (Grösse/Prüfsumme) - versionen.py --linux-json" % lx.get("file"))
    try:                                                         # MoveEye offers it at /sim/simulator3d_linux.zip (Teil 300)
        q300 = open(os.path.join(REPO, "quelle", "300_werkzeuge_simulator3d.py"), encoding="utf-8").read()
        m = re.search(r'^SIM3D_LINUX = \{"version": "([^"]+)", "file": "[^"]+", "size": (\d+),\s*"sha256": "([0-9a-f]+)"', q300, re.M)
        # Drei Spuren: der eingebettete Rückfall darf älter sein (Sim-Release allein), aber nie neuer; gleiche Nummer = gleiche Datei
        if m and sim_key(m.group(1)) and sim_key(str(lx.get("ver"))) and sim_key(m.group(1)) > sim_key(str(lx.get("ver"))):
            out.append("SIM3D_LINUX (300) %s ist neuer als das Linux-Paket %s in version.json" % (m.group(1), lx.get("ver")))
        elif m and m.group(1) == str(lx.get("ver")) and (int(m.group(2)) != lx.get("size") or m.group(3) != lx.get("sha256")):
            out.append("SIM3D_LINUX (300) passt nicht zum Linux-Paket %s in version.json - bauen.py --neue-version übernimmt es" % m.group(1))
    except OSError:
        pass
    if str(lx.get("ver")) != str(vj.get("ver")):
        out.append("Linux-Paket ist %s, version.json ver %s - Linux neu exportieren und packen" % (lx.get("ver"), vj.get("ver")))
    return out


def pi_block(v):
    """Block «pi» für version.json - nur wenn die (lokale, nicht eingecheckte) Pi-ZIP da ist und zu Nummer v passt"""
    import zipfile
    p = os.path.join(REPO, PI_REL)
    if not os.path.isfile(p):
        return None
    try:
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            lies = z.read("MoveEyeSim3D/Lies mich.txt").decode("utf-8", "replace")
            mode = (z.getinfo("MoveEyeSim3D/MoveEyeSim3D.arm64").external_attr >> 16) & 0o777
    except (KeyError, zipfile.BadZipFile, OSError) as e:
        print("PROBLEM: %s ist kein Pi-Paket (%s) - version.json ohne Pi-Paket" % (PI_REL, e))
        return None
    if "NEU IN %s\n" % v not in lies or "MoveEyeSim3D/installieren.sh" not in names or not mode & 0o100:
        print("PROBLEM: %s passt nicht zu %s (Lies mich, installieren.sh, ausführbar?) - linux_paket.sh --pi neu packen" % (PI_REL, v))
        return None
    if any(n.startswith("MoveEyeSim3D/hp/") for n in names):
        print("PROBLEM: %s enthält hp/ (nur für den Simulator-PC) - linux_paket.sh --pi neu packen" % PI_REL)
        return None
    with open(p, "rb") as f:
        data = f.read()
    return {"file": PI_REL, "ver": v, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "url": PI_URL % v}


def pi_json():
    p = os.path.join(SIM, "version.json")
    d = json.load(open(p, encoding="utf-8"))
    px = pi_block(sim_stand(d))
    if px is None:
        print("kein passendes %s (zuerst exportieren: Preset «Linux Pi», dann werkzeuge/linux_paket.sh --pi)" % PI_REL)
        return 1
    d["pi"] = px
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    print("version.json: pi %s, %d Bytes - als Release-Asset hochladen: %s" % (px["ver"], px["size"], px["url"]))
    return 0


def pi_pruefen(vj, man):
    """das Pi-Paket ist freiwillig (Release-Asset): nur Warnungen, ausser die lokale Datei passt nicht zu version.json"""
    px = vj.get("pi")
    if not isinstance(px, dict):
        return [], []
    probleme, warn = [], []
    if px.get("file") != PI_REL or not str(px.get("url") or "").startswith("https://github.com/DonElektro/MotionWatch/releases/download/"):
        probleme.append("version.json «pi»: file muss %s sein, url ein Release-Asset von DonElektro/MotionWatch" % PI_REL)
    p = os.path.join(REPO, PI_REL)
    if os.path.isfile(p):
        with open(p, "rb") as f:
            data = f.read()
        if len(data) != px.get("size") or hashlib.sha256(data).hexdigest() != px.get("sha256"):
            probleme.append("%s passt nicht zu version.json «pi» (Grösse/Prüfsumme) - versionen.py --pi-json" % PI_REL)
    if str(px.get("ver")) != sim_stand(vj):
        warn.append("Pi-Paket ist %s, version.json %s - «Simulator intern» bleibt beim älteren (Preset «Linux Pi» neu exportieren)"
                    % (px.get("ver"), sim_stand(vj)))
    sp = ((man.get("sim") or {}) if isinstance(man.get("sim"), dict) else {}).get("pi") or {}
    if sp and (sp.get("sha256") != px.get("sha256") or sp.get("size") != px.get("size")):
        warn.append("versions.json «sim.pi» passt nicht zu version.json «pi» - neu signieren")
    elif not sp:
        warn.append("Pi-Paket %s noch nicht signiert in versions.json «sim.pi» (bauen.py --nur-signieren, Asset %s hochladen)"
                    % (px.get("ver"), px.get("url")))
    return probleme, warn


def paket_inhalt(pfad, key, v):
    """Fehlerliste (leer = ok): ist die ZIP das Paket <key> («win» / «linux») der Sim-Nummer v?"""
    import zipfile
    exe = "MoveEyeSim3D/MoveEyeSim3D.exe" if key == "win" else "MoveEyeSim3D/MoveEyeSim3D.x86_64"
    out = []
    try:
        with zipfile.ZipFile(pfad) as z:
            names = z.namelist()
            lies = z.read("MoveEyeSim3D/Lies mich.txt").decode("utf-8", "replace")
            with z.open(exe) as f:
                kopf = f.read(20)
            mode = (z.getinfo(exe).external_attr >> 16) & 0o777
    except (KeyError, zipfile.BadZipFile, OSError) as e:
        return ["kein Simulator-Paket (%s)" % e]
    if "NEU IN %s\n" % v not in lies:
        out.append("«Lies mich» ohne NEU IN %s" % v)
    if key == "win" and kopf[:2] != b"MZ":
        out.append("MoveEyeSim3D.exe ist keine Windows-Datei")
    if key == "linux":
        if not (kopf[:6] == b"\x7fELF\x02\x01" and kopf[18:20] == b"\x3e\x00"):
            out.append("MoveEyeSim3D.x86_64 ist keine x86_64-ELF-Datei")
        if not mode & 0o100:
            out.append("MoveEyeSim3D.x86_64 nicht ausführbar")
        for n in ("MoveEyeSim3D/installieren.sh", "MoveEyeSim3D/kiosk_sitzung.sh", "MoveEyeSim3D/hp/hp_update.sh"):
            if n not in names:
                out.append("%s fehlt (der HP braucht es)" % n.split("/", 1)[1])
    return out


def anhang_json(v, notes):
    """--anhang-json: Block «anhang» in version.json aus den geholten Assets unter simulator3d/anhang/ (sim_anhang.py holen).
    Die obersten Felder und «linux» (Pakete im Repository, eingefroren) bleiben wie sie sind - nur «notes» bekommt einmal
    den festen Hinweis für alte Simulatoren / alte MoveEye. «pi» wird nachgezogen, wenn die Pi-ZIP lokal liegt."""
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", v):
        sys.exit("Nummer %s passt nicht zum Schema X.Y.Z" % v)
    p = os.path.join(SIM, "version.json")
    d = json.load(open(p, encoding="utf-8"))
    if not sim_key(str(d.get("ver"))) or sim_key(v) <= sim_key(str(d.get("ver"))):
        sys.exit("Anhang %s muss neuer sein als die Pakete im Repository (%s)" % (v, d.get("ver")))
    for key, rel in (("win", ZIP_REL), ("linux", LINUX_REL)):   # die eingefrorenen Pakete müssen da und unverändert sein
        e = d if key == "win" else (d.get("linux") or {})
        fp = os.path.join(REPO, rel)
        if not os.path.isfile(fp) or os.path.getsize(fp) != e.get("size"):
            sys.exit("%s fehlt oder passt nicht zu version.json - die Pakete im Repository bleiben, wie sie sind" % rel)
    ah = {"ver": v, "version": legacy(v), "name": "MoveEye Sim " + v, "notes": notes}
    mm = mw_min_gd()
    if mm:
        ah["mw_min"] = mm
    for key, rel in ANHANG_REL.items():
        fp = os.path.join(REPO, rel)
        if not os.path.isfile(fp):
            sys.exit("%s fehlt - zuerst: python3 werkzeuge/sim_anhang.py holen %s" % (rel, v))
        fehler = paket_inhalt(fp, key, v)
        if fehler:
            sys.exit("%s: %s" % (rel, "; ".join(fehler)))
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        ah[key] = {"file": rel, "ver": v, "size": os.path.getsize(fp), "sha256": h.hexdigest(), "url": ANHANG_URL % (v, os.path.basename(rel))}
    d["anhang"] = ah
    if ANHANG_HINWEIS.strip(" ·") not in str(d.get("notes") or ""):
        d["notes"] = (str(d.get("notes") or "").rstrip() + ANHANG_HINWEIS)[:600]
    px = pi_block(v)
    if px is not None:
        d["pi"] = px
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    print("version.json: Anhang %s (win %d Bytes, linux %d Bytes%s) - im Repository bleibt Sim %s (alte Simulatoren lesen %s)"
          % (v, ah["win"]["size"], ah["linux"]["size"], ", pi" if px is not None else "", d.get("ver"), d.get("version")))
    return 0


def anhang_pruefen(vj, alt_vj, man):
    """Simulator-Anhang: (Probleme, Warnungen)"""
    ah = vj.get("anhang")
    if ah is None:
        return [], []
    probleme, warn = [], []
    if not isinstance(ah, dict) or not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", str(ah.get("ver") or "")):
        return ["version.json «anhang» ohne «ver» X.Y.Z"], []
    v = str(ah["ver"])
    if not sim_key(str(vj.get("ver"))) or sim_key(v) <= sim_key(str(vj.get("ver"))):
        probleme.append("Anhang %s ist nicht neuer als die Pakete im Repository (%s)" % (v, vj.get("ver")))
    if ah.get("version") != legacy(v):
        probleme.append("version.json «anhang.version» muss %s sein" % legacy(v))
    for key, rel in ANHANG_REL.items():
        e = ah.get(key)
        if not isinstance(e, dict):
            warn.append("Anhang %s ohne Paket «%s»" % (v, key))
            continue
        if e.get("file") != rel or e.get("ver") != v or e.get("url") != ANHANG_URL % (v, os.path.basename(rel)) \
                or not re.fullmatch(r"[0-9a-f]{64}", str(e.get("sha256") or "")) or not isinstance(e.get("size"), int):
            probleme.append("version.json «anhang.%s»: file %s, ver %s, url %s, sha256, size" % (key, rel, v, ANHANG_URL % (v, os.path.basename(rel))))
            continue
        fp = os.path.join(REPO, rel)
        if os.path.isfile(fp):
            with open(fp, "rb") as f:
                data = f.read()
            if len(data) != e.get("size") or hashlib.sha256(data).hexdigest() != e.get("sha256"):
                probleme.append("%s passt nicht zu version.json «anhang.%s» (Grösse/Prüfsumme) - sim_anhang.py holen, --anhang-json" % (rel, key))
        sa = (((man.get("sim") or {}) if isinstance(man.get("sim"), dict) else {}).get("anhang") or {}).get(key) or {}
        if sa and (sa.get("sha256") != e.get("sha256") or sa.get("size") != e.get("size") or sa.get("ver") != v):
            warn.append("versions.json «sim.anhang.%s» passt nicht zu version.json - neu signieren" % key)
        elif not sa:
            warn.append("Anhang %s «%s» noch nicht signiert in versions.json «sim.anhang» (bauen.py --nur-signieren)" % (v, key))
    aa = alt_vj.get("anhang") if isinstance(alt_vj.get("anhang"), dict) else None
    if aa:                                                   # schon mit Anhang veröffentlicht: die Pakete im Repository bleiben eingefroren
        for was, neu_, alt_ in (("ver", vj.get("ver"), alt_vj.get("ver")), ("sha256", vj.get("sha256"), alt_vj.get("sha256")),
                                ("linux.sha256", (vj.get("linux") or {}).get("sha256"), (alt_vj.get("linux") or {}).get("sha256"))):
            if neu_ != alt_:
                probleme.append("version.json «%s» geändert, obwohl es einen Anhang gibt - die Pakete im Repository bleiben eingefroren "
                                "(zurück zu Paketen im Repository: Block «anhang» entfernen, siehe CLAUDE.md)" % was)
    return probleme, warn


def sim_json(v, notes, zip_path=""):
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", v):
        sys.exit("Nummer %s passt nicht zum Schema X.Y.Z" % v)
    z = zip_path or os.path.join(REPO, ZIP_REL)
    try:
        alt_d = json.load(open(os.path.join(SIM, "version.json"), encoding="utf-8"))
    except (OSError, ValueError):
        alt_d = {}
    if isinstance(alt_d.get("anhang"), dict) and not os.environ.get("MW_SIM_IM_REPO"):
        sys.exit("version.json hat einen Block «anhang»: neue Simulator-Versionen sind Release-Assets (--anhang-json, rel_sim.sh).\n"
                 "Zurück zu Paketen im Repository (Asset-Weg gestört): MW_SIM_IM_REPO=1 setzen - schreibt version.json ohne «anhang».")
    with open(z, "rb") as f:
        data = f.read()
    d = {"version": legacy(v), "ver": v, "name": "MoveEye Sim " + v, "file": ZIP_REL, "size": len(data),
         "sha256": hashlib.sha256(data).hexdigest(), "notes": notes}
    mm = mw_min_gd()                                          # Drei Spuren: älteste passende MoveEye (abgleich.gd MW_MIN)
    if mm:
        d["mw_min"] = mm
    lx = linux_block(v)
    if lx is not None:
        d["linux"] = lx
    px = pi_block(v)                                          # «Simulator intern» (Pi): nur wenn lokal frisch gepackt
    if px is not None:
        d["pi"] = px
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
    ap = argparse.ArgumentParser(description="Versionsnummern der drei Spuren MoveEye / MoveEye Sim / Gehäuse")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--pruefen", action="store_true")
    ap.add_argument("--spuren", action="store_true", help="nur die Nummern der drei Spuren")
    ap.add_argument("--sim-json", nargs=2, metavar=("X.Y.Z", "NOTIZ"))
    ap.add_argument("--zip", default="", help="mit --sim-json: diese ZIP statt simulator3d/MotionWatch3D_Simulator.zip")
    ap.add_argument("--anhang-json", nargs=2, metavar=("X.Y.Z", "NOTIZ"),
                    help="Block «anhang» in version.json aus den geholten Release-Assets (simulator3d/anhang/); die Pakete im Repository bleiben")
    ap.add_argument("--linux-json", action="store_true", help="nur den Block «linux» in version.json (Linux-ZIP)")
    ap.add_argument("--pi-json", action="store_true", help="nur den Block «pi» in version.json (Pi-ZIP, Release-Asset)")
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
    if a.spuren:
        print(spuren_text())
        return 0
    if a.sim_json:
        return sim_json(a.sim_json[0], a.sim_json[1], a.zip)
    if a.anhang_json:
        return anhang_json(a.anhang_json[0], a.anhang_json[1])
    if a.linux_json:
        return linux_json()
    if a.pi_json:
        return pi_json()
    if a.neu_data:
        return neu_data()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
