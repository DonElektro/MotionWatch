#!/usr/bin/env python3
"""CI-Läufer: führt die Tests einer Gruppe aus werkzeuge/ci_tests.txt nacheinander aus (Workflow .github/workflows/ci.yml).

  python3 werkzeuge/ci_lauf.py --gruppe kern        # alle Tests der Gruppe, Zeit je Test, Exit 1 wenn einer rot ist
  python3 werkzeuge/ci_lauf.py --pruefen            # die Liste stimmt: jede werkzeuge/*_test.py steht drin, jede Datei gibt es
  python3 werkzeuge/ci_lauf.py --liste              # Gruppen und Tests anzeigen

Pro Test: eigenes Zeitlimit (danach Abbruch = rot), bei «1x» genau EIN zweiter Versuch (ein Erfolg erst im zweiten Versuch
wird als Warnung gemeldet, nie verschwiegen). Nach einem roten Test laufen die übrigen der Gruppe weiter, damit ein Lauf alle
Fehler zeigt. Am Schluss eine Tabelle «Test · Dauer · Ergebnis» im Protokoll und in der Zusammenfassung des Laufs auf GitHub.
Läuft auch lokal (ohne GitHub) genau gleich.
"""
import argparse
import glob
import os
import re
import signal
import subprocess
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
LISTE = os.path.join(HIER, "ci_tests.txt")
GRUPPEN = ["basis", "kern", "rechte", "live", "daten", "spiele-1", "spiele-2", "simlive", "pidienst", "hand"]


def lesen(pfad=LISTE):
    """[{gruppe, limit (min), nochmal (bool), befehl, name, zeile}] - a broken line is an error, never ignored"""
    out = []
    with open(pfad, encoding="utf-8") as f:
        for nr, ln in enumerate(f, 1):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            t = [x.strip() for x in ln.split(" | ", 4)]
            if len(t) != 5 or t[0] not in GRUPPEN or t[2] not in ("1x", "-") or not t[3] or not t[4]:
                sys.exit("%s Zeile %d: erwartet «Gruppe | Limit | Nochmal | Befehl | Name» (Gruppen: %s)" % (os.path.basename(pfad), nr, ", ".join(GRUPPEN)))
            if t[0] != "hand" and not re.fullmatch(r"\d{1,3}", t[1]):
                sys.exit("%s Zeile %d: Limit in Minuten fehlt" % (os.path.basename(pfad), nr))
            out.append({"gruppe": t[0], "limit": int(t[1]) if t[1].isdigit() else 0, "nochmal": t[2] == "1x", "befehl": t[3], "name": t[4], "zeile": nr})
    return out


def neueste_datei():
    """the newest webcam_bewegung_X_Y_Z.py of the repository (by number, as «sort -V»)"""
    best = None
    for p in glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")):
        m = re.search(r"webcam_bewegung_(\d+)_(\d+)_(\d+)\.py$", p)
        if m and (best is None or tuple(map(int, m.groups())) > best[0]):
            best = (tuple(map(int, m.groups())), os.path.basename(p))
    return best[1] if best else ""


def pruefen(tests):
    """the list is complete: no *_test.py outside it (that is how tests dropped out of the CI before), every file exists"""
    fehler = []
    alle = " \n".join(t["befehl"] for t in tests)
    for p in sorted(glob.glob(os.path.join(HIER, "*_test.py"))):
        if not re.search(r"werkzeuge/%s(?![\w.])" % re.escape(os.path.basename(p)), alle):
            fehler.append("werkzeuge/%s steht nicht in werkzeuge/ci_tests.txt (in eine Gruppe eintragen, oder in «hand» mit Grund)" % os.path.basename(p))
    for t in tests:
        for m in re.finditer(r"werkzeuge/[\w./-]+\.(?:py|sh)", t["befehl"]):
            if not os.path.isfile(os.path.join(REPO, m.group(0))):
                fehler.append("Zeile %d: %s gibt es nicht" % (t["zeile"], m.group(0)))
    da = {t["gruppe"] for t in tests}
    for g in GRUPPEN:
        if g != "hand" and g not in da:
            fehler.append("Gruppe «%s» hat keinen Test" % g)
    for f in fehler:
        print("FEHLER: " + f)
        if os.environ.get("GITHUB_ACTIONS"):
            print("::error title=Testliste::" + f)
    n_hand = sum(1 for t in tests if t["gruppe"] == "hand")
    print("Testliste: %d Tests in %d Gruppen, %d nur von Hand – %s" % (len(tests) - n_hand, len(da - {"hand"}), n_hand, "OK" if not fehler else "%d Fehler" % len(fehler)))
    for t in tests:
        if t["gruppe"] == "hand":
            print("  nicht im CI: %s  (%s)" % (t["befehl"], t["name"]))
    return 1 if fehler else 0


def einmal(befehl, limit_min, env):
    """run one command in its own process group; (ok, seconds, reason)"""
    t0 = time.time()
    p = subprocess.Popen(["bash", "-c", befehl], cwd=REPO, env=env, start_new_session=True)
    try:
        rc = p.wait(timeout=limit_min * 60)
        return rc == 0, time.time() - t0, "" if rc == 0 else "Exit-Code %d" % rc
    except subprocess.TimeoutExpired:
        for sig in (signal.SIGTERM, signal.SIGKILL):       # the whole group: the test may have started MoveEye / a browser
            try:
                os.killpg(p.pid, sig)
            except OSError:
                pass
            try:
                p.wait(timeout=10)
                break
            except subprocess.TimeoutExpired:
                pass
        return False, time.time() - t0, "Zeitlimit %d min" % limit_min


def dauer(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def gruppe_laufen(tests, gruppe):
    gh = bool(os.environ.get("GITHUB_ACTIONS"))
    env = dict(os.environ, PYTHONUNBUFFERED="1", MW=neueste_datei())
    env.setdefault("CI_STRENG", "--streng" if os.environ.get("GITHUB_REF") == "refs/heads/main" else "")
    zeilen, rot = [], 0
    t_start = time.time()
    for t in [x for x in tests if x["gruppe"] == gruppe]:
        versuche, gesamt = 0, 0.0
        while True:
            versuche += 1
            print(("::group::" if gh else "\n===== ") + "%s%s" % (t["name"], " (zweiter Versuch)" if versuche == 2 else ""), flush=True)
            print("$ " + t["befehl"], flush=True)
            ok, sek, grund = einmal(t["befehl"], t["limit"], env)
            gesamt += sek
            sys.stdout.flush()
            if gh:
                print("::endgroup::", flush=True)
            print("%s  %s  %s%s" % ("OK    " if ok else "FEHLER", dauer(sek), t["name"], "" if ok else "  (" + grund + ")"), flush=True)
            if ok or not t["nochmal"] or versuche == 2:
                break
            if gh:
                print("::warning title=Zweiter Versuch::%s: erster Versuch rot (%s) - genau ein zweiter Versuch" % (t["name"][:80], grund), flush=True)
        if ok and versuche == 2 and gh:
            print("::warning title=Wackelt::%s: erst im zweiten Versuch grün" % t["name"][:80], flush=True)
        if not ok:
            rot += 1
            if gh:
                print("::error title=Test rot::%s (%s%s) - Befehl: %s" % (t["name"][:80], grund, ", auch im zweiten Versuch" if versuche == 2 else "", t["befehl"]), flush=True)
        zeilen.append((t["name"], gesamt, "✅ grün" if ok and versuche == 1 else "⚠️ grün im 2. Versuch" if ok else "❌ rot (%s)" % grund, t["limit"]))
    if not zeilen:
        sys.exit("Gruppe «%s» hat keinen Test (werkzeuge/ci_tests.txt)" % gruppe)
    kopf = "Gruppe «%s»: %d Tests, %s%s" % (gruppe, len(zeilen), dauer(time.time() - t_start), "" if not rot else " – %d ROT" % rot)
    print("\n" + kopf)
    for name, sek, erg, _lim in zeilen:
        print("  %6s  %-24s %s" % (dauer(sek), erg, name))
    zus = os.environ.get("GITHUB_STEP_SUMMARY")
    if zus:
        with open(zus, "a", encoding="utf-8") as f:
            f.write("### %s\n\n| Test | Dauer | Limit | Ergebnis |\n|---|---:|---:|---|\n" % kopf)
            for name, sek, erg, lim in zeilen:
                f.write("| %s | %s | %d min | %s |\n" % (name.replace("|", "/"), dauer(sek), lim, erg))
            f.write("\n")
    return 1 if rot else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gruppe", default="")
    ap.add_argument("--pruefen", action="store_true")
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    tests = lesen()
    if a.pruefen:
        return pruefen(tests)
    if a.liste or not a.gruppe:
        for g in GRUPPEN:
            print(g)
            for t in tests:
                if t["gruppe"] == g:
                    print("   %s%s  %s" % ("%2d min " % t["limit"] if t["limit"] else "       ", "1x" if t["nochmal"] else "  ", t["befehl"]))
        return 0
    if a.gruppe not in GRUPPEN or a.gruppe == "hand":
        sys.exit("unbekannte Gruppe «%s» (%s)" % (a.gruppe, ", ".join(g for g in GRUPPEN if g != "hand")))
    return gruppe_laufen(tests, a.gruppe)


if __name__ == "__main__":
    sys.exit(main())
