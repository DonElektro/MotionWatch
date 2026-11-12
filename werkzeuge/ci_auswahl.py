#!/usr/bin/env python3
"""CI-Auswahl: welche Teile des CI für einen Stand laufen müssen - und der Torwächter am Schluss.

  python3 werkzeuge/ci_auswahl.py --auswahl               # im CI (Job «Auswahl»): schreibt die Ausgaben für ci.yml
  python3 werkzeuge/ci_auswahl.py --ergebnis              # im CI (Job «Ergebnis»): Tabelle, rot wenn etwas fehlt
  python3 werkzeuge/ci_auswahl.py --dateien a b c         # lokal: was liefe bei genau diesen geänderten Dateien?
  python3 werkzeuge/ci_auswahl.py --simulieren 20 [REF]   # lokal: die letzten 20 Commits (Standard origin/main), je ein Push
  python3 werkzeuge/ci_auswahl.py --selbsttest            # die Regeln an festen Beispielen
  Auf GitHub von Hand (Run workflow, nicht auf main): Feld «probe» = Dateien -> der Lauf tut so, als wären nur sie geändert.

Grundsatz: im Zweifel laufen lassen. MoveEye wird aus vielen Teilen zu EINER Datei gebaut - darum gibt es für die
Web-Gruppen keine feinen Pfad-Filter. Übersprungen wird nur, was sicher unbeteiligt ist:

  main, von Hand mit «alles»      -> immer ALLES, nichts wird übersprungen (der Torwächter prüft das noch einmal)
  Änderung an den CI-Dateien      -> alles
  nur Ergebnisse / Notizen        -> nur die Grundprüfungen          (NICHTS: Prüfstand-Verlauf, feedback/, ki_training/ …)
  nur der USB-Installer           -> nur dessen Prüfungen            (er wird mit nichts anderem zusammen gebaut)
  nur Spiele-Dateien (games/ …)   -> Grundprüfungen + Spiele-Tests
  alles andere                    -> alles ausser: Spiele-Tests (nur wenn Spiele-Dateien dabei sind) und USB-Installer
  derselbe Commit läuft auf main  -> auf integration nur die Grundprüfungen (der Lauf auf main prüft alles)

Verglichen wird der ganze Zweig mit main (nicht nur der letzte Push): ein Zweig mit einer Spiele-Änderung prüft die Spiele
bei jedem Push, bis er in main ist. Kann der Vergleich nicht gemacht werden (GitHub antwortet nicht, über 250 Dateien),
läuft alles.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.request

WEB = ["kern", "rechte", "live", "daten"]                   # groups of werkzeuge/ci_tests.txt, one job each
SPIELE = ["spiele-1", "spiele-2"]
EINHEITEN = ["web", "spiele", "sim", "hp", "usb"]            # what can be skipped (the basic checks never)
NAME = {"web": "Web-Gruppen (%s)" % ", ".join(WEB), "spiele": "Spiele-Tests (%s)" % ", ".join(SPIELE),
        "sim": "Simulator (Godot-Tests, Simulator läuft)", "hp": "HP-Update", "usb": "USB-Installer"}

# ---- path classes (fnmatch, «*» also crosses «/») -----------------------------------------------------------------------
CI_DATEIEN = [".github/workflows/ci.yml", "werkzeuge/ci_*"]
NICHTS = ["pruefstand/VERLAUF.md", "pruefstand/ergebnisse/*", "feedback/*", "ki_training/*", "README.md",
          ".github/workflows/*"]                             # other workflows (ci.yml is caught before)
USB = ["werkzeuge/usb_installer/*"]
SPIELE_REIN = ["games/*", "werkzeuge/spiele_test.py", "werkzeuge/spiele_ordnen_test.py", "werkzeuge/spiel_einbauen.py",
               "werkzeuge/schach_fern_test.py", "werkzeuge/fertigspiele*", ".github/workflows/fertigspiele.yml",
               ".github/workflows/fotaq.yml", "werkzeuge/fotaq*"]
# parts of the program that belong to the games (a change runs the games tests AND everything else: it is program code)
SPIELE_QUELLE = [r"quelle/(32\d|33\d|34[0-3])[a-z]*_", r"quelle/639zz[ghnor]_", r"quelle/[^/]*(spiele|fertigspiele|fotaq|schach|wasnun)[^/]*$"]


def passt(pfad, muster):
    return any(fnmatch.fnmatchcase(pfad, m) for m in muster)


def klasse(pfad):
    if passt(pfad, CI_DATEIEN):
        return "ci"
    if passt(pfad, SPIELE_REIN):
        return "spiele_rein"
    if any(re.match(m, pfad) for m in SPIELE_QUELLE):
        return "spiele_quelle"
    if passt(pfad, USB):
        return "usb"
    if passt(pfad, NICHTS):
        return "nichts"
    return "sonst"


def entscheiden(ref, ereignis="push", alles=False, dateien=None, doppelt=""):
    """-> {"laeuft": {einheit: bool}, "grund": {einheit: text}, "kurz": text}
    dateien None = unknown (then everything runs); doppelt = address of the run of the same commit on main"""
    alle = {e: True for e in EINHEITEN}
    if ref == "refs/heads/main":
        return {"laeuft": alle, "grund": {}, "kurz": "main: immer alles"}
    if ereignis == "workflow_dispatch" and alles:
        return {"laeuft": alle, "grund": {}, "kurz": "von Hand mit «alles»"}
    if doppelt:
        g = "derselbe Commit läuft vollständig auf main (%s)" % doppelt
        return {"laeuft": {e: False for e in EINHEITEN}, "grund": {e: g for e in EINHEITEN}, "kurz": "gleicher Commit wie main"}
    if dateien is None:
        return {"laeuft": alle, "grund": {}, "kurz": "Vergleich mit main nicht möglich: alles"}
    kl = {}
    for d in dateien:
        kl.setdefault(klasse(d), []).append(d)
    bsp = lambda k: ", ".join(kl[k][:3]) + (" …" if len(kl[k]) > 3 else "")
    if "ci" in kl:
        return {"laeuft": alle, "grund": {}, "kurz": "CI-Dateien geändert (%s): alles" % bsp("ci")}
    sonst = "sonst" in kl or "spiele_quelle" in kl           # program, simulator, tools, docs … : everything but games / usb
    spiele = "spiele_rein" in kl or "spiele_quelle" in kl
    usb = "usb" in kl
    laeuft = {"web": sonst, "sim": sonst, "hp": sonst, "spiele": spiele, "usb": usb}
    n = len(dateien)
    if not dateien:
        warum = "keine Datei gegenüber main geändert"
    elif not (sonst or spiele or usb):
        warum = "nur Ergebnisse / Notizen geändert (%s)" % bsp("nichts")
    else:
        warum = "%d Dateien gegenüber main geändert, keine davon betrifft diesen Teil" % n
    fest = {"spiele": "keine Spiele-Datei geändert (games/, Spiele-Teile in quelle/, Spiele-Tests) – läuft auf main immer",
            "usb": "werkzeuge/usb_installer/ nicht geändert – läuft auf main immer"}
    grund = {e: fest.get(e, warum + " – läuft auf main immer") for e in EINHEITEN if not laeuft[e]}
    kurz = "%d Dateien gegenüber main" % n + (": " + ", ".join("%d× %s" % (len(v), k) for k, v in sorted(kl.items())) if kl else "")
    return {"laeuft": laeuft, "grund": grund, "kurz": kurz}


# ---- GitHub ------------------------------------------------------------------------------------------------------------
def api(pfad):
    req = urllib.request.Request("https://api.github.com/repos/%s/%s" % (os.environ["GITHUB_REPOSITORY"], pfad),
                                 headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "moveeye-ci"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def api_mehrmals(pfad, mal=3):
    import time
    for i in range(mal):
        try:
            return api(pfad)
        except Exception as e:
            print("GitHub antwortet nicht (%s): %s" % (pfad.split("?")[0], str(e)[:120]))
            time.sleep(3 * (i + 1))
    return None


def geaendert_github(sha):
    """(files changed between main and this commit, True when the commit is already in main) - (None, False) = unknown"""
    d = api_mehrmals("compare/main...%s?per_page=1" % sha)
    if not isinstance(d, dict) or "files" not in d:
        return None, False
    if d.get("status") in ("identical", "behind"):
        return [], True
    files = d.get("files") or []
    if len(files) >= 250:                                    # the answer is cut at 300 files: do not trust a long list
        return None, False
    out = []
    for f in files:
        out.append(f["filename"])
        if f.get("previous_filename"):
            out.append(f["previous_filename"])
    return out, False


def lauf_auf_main(sha):
    """address of a CI run of exactly this commit on main that is running or green ("" = none)"""
    d = api_mehrmals("actions/workflows/ci.yml/runs?branch=main&head_sha=%s&per_page=20" % sha, mal=2)
    for r in (d or {}).get("workflow_runs", []):
        if str(r.get("id")) != os.environ.get("GITHUB_RUN_ID") and r.get("head_sha") == sha and \
                (r.get("status") != "completed" or r.get("conclusion") == "success"):
            return r.get("html_url") or ""
    return ""


def ausgeben(e):
    l = e["laeuft"]
    gruppen = (WEB if l["web"] else []) + (SPIELE if l["spiele"] else [])
    aus = {"web": "true" if gruppen else "false", "gruppen": json.dumps(gruppen or ["keine"]), "sim": str(l["sim"]).lower(),
           "hp": str(l["hp"]).lower(), "usb": str(l["usb"]).lower(), "laeuft": json.dumps(l), "grund": json.dumps(e["grund"], ensure_ascii=False)}
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            for k, v in aus.items():
                f.write("%s=%s\n" % (k, v))
    zeilen = ["| Teil | läuft | |", "|---|---|---|", "| Grundprüfungen (Bau, Selbsttest, Update, Versionen, Simulator-Texte) | ✅ ja | immer |"]
    for x in EINHEITEN:
        zeilen.append("| %s | %s | %s |" % (NAME[x], "✅ ja" if l[x] else "⏭️ übersprungen", "" if l[x] else "übersprungen, weil " + e["grund"].get(x, "?")))
    text = "## CI-Auswahl: %s\n\n%s\n" % (e["kurz"], "\n".join(zeilen))
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(text + "\n")
    for x in EINHEITEN:
        if not l[x] and os.environ.get("GITHUB_ACTIONS"):
            print("::notice title=Übersprungen: %s::übersprungen, weil %s" % (NAME[x], e["grund"].get(x, "?")))
    return aus


def auswahl():
    """job «Auswahl». Never fails on its own trouble: when something cannot be found out, everything runs."""
    ref, ereignis, sha = os.environ.get("GITHUB_REF", ""), os.environ.get("GITHUB_EVENT_NAME", "push"), os.environ.get("GITHUB_SHA", "")
    alles = os.environ.get("CI_ALLES", "true").lower() != "false"
    dateien, doppelt = None, ""
    probe = [x for x in re.split(r"[\s,]+", os.environ.get("CI_PROBE", "")) if x]
    if probe and ereignis == "workflow_dispatch" and ref != "refs/heads/main":
        # by hand, never on main: «as if only these files had changed» - to see / measure what a change would run
        e = entscheiden(ref, ereignis, False, probe)
        e["kurz"] = "PROBE (von Hand, als wären nur diese Dateien geändert): " + e["kurz"]
        ausgeben(e)
        return 0
    try:
        if ref != "refs/heads/main" and not (ereignis == "workflow_dispatch" and alles):
            dateien, in_main = geaendert_github(sha)
            if in_main:
                doppelt = lauf_auf_main(sha)
                if not doppelt:
                    dateien = None                           # in main, but no run there to lean on: everything
    except Exception as e:
        print("Auswahl: %s - es läuft alles" % str(e)[:200])
        dateien, doppelt = None, ""
    ausgeben(entscheiden(ref, ereignis, alles, dateien, doppelt))
    return 0


# ---- gate ------------------------------------------------------------------------------------------------------------------
JOB_EINHEIT = {"moveeye": "", "sim-texte": "", "web": "web+spiele", "sim-liste": "sim", "sim": "sim", "sim-live": "sim",
               "hp-update": "hp", "usb-installer": "usb", "export": "export"}


def ergebnis():
    """job «Ergebnis» (the one check a release waits for): red when a job is red, when a job was skipped that the
    selection wanted, and on main when anything at all was skipped."""
    needs = json.loads(os.environ.get("NEEDS") or "{}")
    ref, ereignis = os.environ.get("GITHUB_REF", ""), os.environ.get("GITHUB_EVENT_NAME", "push")
    aw = needs.get("auswahl", {})
    try:
        laeuft = json.loads((aw.get("outputs") or {}).get("laeuft") or "")
        grund = json.loads((aw.get("outputs") or {}).get("grund") or "{}")
    except ValueError:
        laeuft, grund = {e: True for e in EINHEITEN}, {}     # no selection = everything had to run
    main = ref == "refs/heads/main"
    export_soll = main or ref == "refs/heads/integration" or (ereignis == "workflow_dispatch" and os.environ.get("CI_EXPORT", "true") != "false") \
        or "[export]" in os.environ.get("CI_NACHRICHT", "")
    fehler, zeilen = [], []
    if aw.get("result") != "success":
        fehler.append("Job «Auswahl» ist %s" % aw.get("result"))
    for job, einheit in JOB_EINHEIT.items():
        res = (needs.get(job) or {}).get("result", "fehlt")
        if einheit == "":
            soll = True
        elif einheit == "web+spiele":
            soll = laeuft.get("web") or laeuft.get("spiele")
        elif einheit == "export":
            soll = export_soll
        else:
            soll = bool(laeuft.get(einheit))
        if res == "success":
            text = "✅ grün"
        elif res == "skipped" and not soll:
            g = "Export nur auf integration / main / von Hand / «[export]»" if einheit == "export" else \
                grund.get("web" if einheit == "web+spiele" else einheit, "nicht gewählt")
            text = "⏭️ übersprungen, weil " + g
        else:
            text = "❌ %s" % {"failure": "rot", "cancelled": "abgebrochen", "skipped": "übersprungen, obwohl er laufen musste", "fehlt": "fehlt"}.get(res, res)
            fehler.append("Job «%s»: %s" % (job, text[2:]))
        zeilen.append("| %s | %s |" % (job, text))
    teil = [NAME[e] for e in EINHEITEN if not laeuft.get(e)]
    if laeuft.get("web") and not laeuft.get("spiele"):
        zeilen.append("| web: Gruppen spiele-1, spiele-2 | ⏭️ übersprungen, weil %s |" % grund.get("spiele", "?"))
    elif laeuft.get("spiele") and not laeuft.get("web"):
        zeilen.append("| web: Gruppen %s | ⏭️ übersprungen, weil %s |" % (", ".join(WEB), grund.get("web", "?")))
    if main and teil:
        fehler.append("auf main darf nichts übersprungen sein, übersprungen: " + ", ".join(teil))
    if main and any((needs.get(j) or {}).get("result") != "success" for j in JOB_EINHEIT):
        if not fehler:
            fehler.append("auf main müssen alle Jobs grün sein")
    kopf = "## CI-Ergebnis: %s" % ("❌ ROT" if fehler else "✅ grün" + (" – mit übersprungenen Teilen (%s)" % ", ".join(teil) if teil else " – alles gelaufen"))
    text = kopf + "\n\n| Job | Ergebnis |\n|---|---|\n" + "\n".join(zeilen) + "\n"
    if fehler:
        text += "\n" + "\n".join("- ❌ " + f for f in fehler) + "\n"
    text += zeiten()
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(text + "\n")
    for f in fehler:
        print("::error title=CI-Ergebnis::" + f)
    return 1 if fehler else 0


def zeiten():
    """table «job · waited · ran» of this run (best effort - no table when GitHub does not answer)"""
    import datetime
    try:
        jobs, seite = [], 1
        while seite <= 3:
            d = api("actions/runs/%s/jobs?per_page=100&page=%d" % (os.environ["GITHUB_RUN_ID"], seite))
            jobs += d.get("jobs", [])
            if len(d.get("jobs", [])) < 100:
                break
            seite += 1
        p = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        rows, summe, ende = [], 0.0, None
        for j in jobs:
            if not (j.get("started_at") and j.get("completed_at")) or j.get("conclusion") == "skipped":
                continue
            lauf = (p(j["completed_at"]) - p(j["started_at"])).total_seconds()
            warte = max(0.0, (p(j["started_at"]) - p(j["created_at"])).total_seconds())
            summe += lauf
            ende = max(ende, p(j["completed_at"])) if ende else p(j["completed_at"])
            rows.append((lauf, "| %s | %d:%02d | %d:%02d | %s |" % (j["name"], warte // 60, warte % 60, lauf // 60, lauf % 60, j.get("conclusion"))))
        if not rows:
            return ""
        start = min(p(j["created_at"]) for j in jobs)
        wand = (ende - start).total_seconds()
        rows.sort(key=lambda r: -r[0])
        return ("\n### Zeiten\n\nBis hierher %d:%02d (Wanduhr), Summe der Jobs %d:%02d.\n\n| Job | gewartet | gelaufen | |\n|---|---:|---:|---|\n" %
                (wand // 60, wand % 60, summe // 60, summe % 60)) + "\n".join(r[1] for r in rows) + "\n"
    except Exception as e:
        return "\n(Zeiten: GitHub antwortet nicht – %s)\n" % str(e)[:100]


# ---- local ------------------------------------------------------------------------------------------------------------------
def zeigen(e):
    l = e["laeuft"]
    return "%-58s  %s" % (" ".join(("+" if l[x] else "-") + x for x in EINHEITEN), e["kurz"])


def simulieren(n, ref):
    """the last n commits of ref, each as if it had been pushed alone to a work branch (changes against its first parent)"""
    r = subprocess.run(["git", "log", "--first-parent", "-%d" % n, "--format=%h %s", ref], capture_output=True, text=True, check=True)
    zahl = {x: 0 for x in EINHEITEN}
    print("%-9s %-58s  %s" % ("Commit", "läuft (+) / übersprungen (-)", "Grund · Titel"))
    for ln in r.stdout.splitlines():
        h, titel = ln.split(" ", 1)
        d = subprocess.run(["git", "diff", "--name-only", h + "^1", h], capture_output=True, text=True)
        dateien = [x for x in d.stdout.splitlines() if x] if d.returncode == 0 else None
        e = entscheiden("refs/heads/real-x", "push", False, dateien)
        for x in EINHEITEN:
            zahl[x] += 1 if e["laeuft"][x] else 0
        print("%-9s %s · %s" % (h, zeigen(e), titel[:60]))
    print("\nvon %d Commits liefen: %s (Grundprüfungen: immer; auf main: immer alles)" % (n, ", ".join("%s %d" % (x, zahl[x]) for x in EINHEITEN)))
    return 0


def selbsttest():
    f = []

    def t(was, e, **soll):
        ist = e["laeuft"]
        if any(ist[k] != v for k, v in soll.items()):
            f.append("%s: %s statt %s" % (was, ist, soll))
    alle = dict(web=True, spiele=True, sim=True, hp=True, usb=True)
    keins = {k: False for k in alle}
    R = "refs/heads/real-x"
    t("main", entscheiden("refs/heads/main", "push", False, ["README.md"]), **alle)
    t("main ohne Liste", entscheiden("refs/heads/main", "push", False, None), **alle)
    t("main trotz doppelt", entscheiden("refs/heads/main", "push", False, [], "https://x"), **alle)
    t("von Hand alles", entscheiden(R, "workflow_dispatch", True, ["README.md"]), **alle)
    t("von Hand ohne alles", entscheiden(R, "workflow_dispatch", False, ["README.md"]), **keins)
    t("unbekannt", entscheiden(R, "push", False, None), **alle)
    t("Text in einem Teil", entscheiden(R, "push", False, ["quelle/560_uebersetzungen_de.py", "webcam_bewegung_3_77_0.py", "moveeye_daten_3_77_0.zip"]),
      web=True, spiele=False, sim=True, hp=True, usb=False)
    t("Spiel", entscheiden(R, "push", False, ["games/wasnun/spiel.js", "games/MotionWatch_Spiele.zip"]), web=False, spiele=True, sim=False, hp=False, usb=False)
    t("Spiele-Teil", entscheiden(R, "push", False, ["quelle/320_spielecke.py"]), web=True, spiele=True, sim=True, hp=True, usb=False)
    for q in ("quelle/340_spiele_seiten.py", "quelle/343_spiel_vergleich_online.py", "quelle/639zzn_fertigspiele.py", "quelle/639zzo_spiele_ordnen.py",
              "quelle/639zzr_schach_fern.py", "quelle/639zzg_fotaq.py", "quelle/330_usb_geraete.py"):
        t(q, entscheiden(R, "push", False, [q]), web=True, spiele=True)
    for q in ("werkzeuge/spiele_test.py", "werkzeuge/spiel_einbauen.py", "werkzeuge/schach_fern_test.py", "werkzeuge/fertigspiele/paket.py",
              "werkzeuge/fertigspiele_test.py", "games/schach/kachel.json"):
        t(q, entscheiden(R, "push", False, [q]), web=False, spiele=True, sim=False)
    t("Prüfstand-Ergebnis", entscheiden("refs/heads/integration", "push", False, ["pruefstand/VERLAUF.md", "pruefstand/ergebnisse/a.json"]), **keins)
    t("Prüfstand-Programm", entscheiden(R, "push", False, ["pruefstand/pruefstand.py"]), web=True, sim=True, spiele=False)
    t("USB", entscheiden(R, "push", False, ["werkzeuge/usb_installer/pruefen.sh"]), web=False, usb=True, sim=False, hp=False, spiele=False)
    t("CI", entscheiden(R, "push", False, [".github/workflows/ci.yml"]), **alle)
    t("CI-Liste", entscheiden(R, "push", False, ["werkzeuge/ci_tests.txt"]), **alle)
    t("anderer Workflow", entscheiden(R, "push", False, [".github/workflows/pruefstand.yml"]), **keins)
    t("Simulator", entscheiden(R, "push", False, ["simulator3d/scripts/main.gd"]), web=True, sim=True, hp=True, spiele=False, usb=False)
    t("Doku", entscheiden(R, "push", False, ["docs/Merkliste.md"]), web=True, sim=True, spiele=False)
    t("Gehäuse", entscheiden(R, "push", False, ["hardware/gehaeuse/bau.json"]), web=True, sim=True)
    t("versions.json", entscheiden(R, "push", False, ["versions.json"]), web=True, hp=True)
    t("leer", entscheiden(R, "push", False, []), **keins)
    t("doppelt", entscheiden("refs/heads/integration", "push", False, [], "https://x"), **keins)
    t("gemischt", entscheiden(R, "push", False, ["pruefstand/VERLAUF.md", "games/a", "werkzeuge/usb_installer/x", "quelle/010_grundlagen.py"]), **alle)
    for x in f:
        print("FEHLER: " + x)
    print("ci_auswahl Selbsttest: %s" % ("OK" if not f else "%d Fehler" % len(f)))
    return 1 if f else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auswahl", action="store_true")
    ap.add_argument("--ergebnis", action="store_true")
    ap.add_argument("--selbsttest", action="store_true")
    ap.add_argument("--dateien", nargs="*", default=None)
    ap.add_argument("--simulieren", type=int, default=0)
    ap.add_argument("ref", nargs="?", default="origin/main")
    a = ap.parse_args()
    if a.auswahl:
        return auswahl()
    if a.ergebnis:
        return ergebnis()
    if a.selbsttest:
        return selbsttest()
    if a.simulieren:
        return simulieren(a.simulieren, a.ref)
    if a.dateien is not None:
        ausgeben(entscheiden("refs/heads/real-x", "push", False, a.dateien))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
