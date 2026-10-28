#!/usr/bin/env python3
"""Prüfstand für die Erkennung von Motion Watch.

Startet den 3D-Simulator und Motion Watch ohne Bildschirm, lässt feste Testläufe laufen (immer dieselben Besucher auf
denselben Wegen, siehe simulator3d/scripts/testrun.gd) und schreibt die Zahlen auf:
Personen erkannt (%), Reaktionszeit, Tiere gemeldet, Fehlalarme. Jeder Lauf kommt als JSON nach pruefstand/ergebnisse/,
die Tabelle pruefstand/VERLAUF.md wird daraus neu geschrieben und der Lauf mit dem vorherigen verglichen.

Beispiele:
  python3 pruefstand/pruefstand.py --godot /pfad/Godot_v4.3-stable_linux.x86_64          # aus dem Godot-Projekt
  python3 pruefstand/pruefstand.py --sim-bin /pfad/MotionWatch3D.x86_64 --plaene quick,night
  python3 pruefstand/pruefstand.py --nur-verlauf                                            # nur VERLAUF.md neu schreiben

Der Rückgabewert ist 0, wenn alles lief; 2, wenn ein Lauf nicht zu Ende kam; 3 mit --streng, wenn die Erkennung
schlechter ist als beim letzten vergleichbaren Lauf.
"""
import argparse
import glob
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
ERGEBNISSE = os.path.join(HIER, "ergebnisse")
VERLAUF = os.path.join(HIER, "VERLAUF.md")
PLAN_DAUER = {"quick": 150, "standard": 300, "night": 230, "hard": 520}     # Sekunden, ungefähr (Simulator in Echtzeit)
PLAN_NAME = {"quick": "Kurz (Tag + Nacht)", "standard": "Standard (Tag, Wind, Nacht, Regen)", "night": "Nacht", "hard": "Schwierige Bedingungen"}


def log(*a):
    print("[pruefstand]", *a, flush=True)
    if os.environ.get("GITHUB_ACTIONS"):                       # on GitHub: also as a note on the page of the run
        print("::notice title=Prüfstand::" + " ".join(str(x) for x in a).replace("%", "%25").replace("\n", "%0A"), flush=True)


def log_tail(path, title, n=25):
    """the end of a log file (when something went wrong) - on GitHub as a warning on the page of the run"""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            tail = "".join(f.readlines()[-n:])
    except OSError:
        tail = "(keine Datei)"
    print("----- %s -----\n%s" % (title, tail), flush=True)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning title=%s::%s" % (title, tail.replace("%", "%25").replace("\r", "").replace("\n", "%0A")), flush=True)


def http_json(url, data=None, timeout=8.0):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"} if body else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def newest_mw():
    fs = glob.glob(os.path.join(REPO, "webcam_bewegung_*.py"))
    key = lambda f: [int(x) for x in os.path.basename(f)[16:-3].split("_") if x.isdigit()]
    return max(fs, key=key) if fs else ""


def mw_version(path):
    return os.path.basename(path)[16:-3].replace("_", ".")


class Prozesse:
    """starts the programs and stops them again at the end (also on Ctrl+C)"""

    def __init__(self):
        self.p = []

    def start(self, name, cmd, env=None, log_file=None):
        out = open(log_file, "w") if log_file else subprocess.DEVNULL
        pr = subprocess.Popen(cmd, env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        self.p.append((name, pr))
        return pr

    def stop(self):
        for name, pr in reversed(self.p):
            if pr.poll() is None:
                try:
                    os.killpg(pr.pid, signal.SIGTERM)
                except OSError:
                    pass
        t = time.time() + 6
        for name, pr in self.p:
            while pr.poll() is None and time.time() < t:
                time.sleep(0.2)
            if pr.poll() is None:
                try:
                    os.killpg(pr.pid, signal.SIGKILL)
                except OSError:
                    pass


def run(a):
    mw = a.mw or newest_mw()
    if not mw or not os.path.isfile(mw):
        sys.exit("Motion Watch nicht gefunden (--mw)")
    if not a.sim_bin and not a.godot:
        sys.exit("Simulator fehlt: --sim-bin (exportiertes Programm) oder --godot (Godot 4.3) angeben")
    tmp = tempfile.mkdtemp(prefix="mw_pruefstand_")
    P = Prozesse()
    env = dict(os.environ)
    try:
        if not env.get("DISPLAY") and not a.ohne_xvfb:              # no screen: a virtual one
            if not shutil.which("Xvfb"):
                sys.exit("Kein Bildschirm und kein Xvfb (sudo apt install xvfb)")
            disp = ":%d" % (90 + os.getpid() % 9)
            P.start("Xvfb", ["Xvfb", disp, "-screen", "0", "1280x720x24"])
            env["DISPLAY"] = disp
            time.sleep(2)
        # --- the simulator: own home folder, so its settings and reports do not mix with the normal ones
        senv = dict(env, HOME=os.path.join(tmp, "home"))
        os.makedirs(senv["HOME"], exist_ok=True)
        sim_args = ["--no-update", "--stream", "--scene", a.szene, "--hour", "12", "--port", str(a.sim_port), "--quality", a.qualitaet]
        if a.sim_bin:
            cmd = [a.sim_bin, "--"] + sim_args
        else:
            cmd = [a.godot, "--path", os.path.join(REPO, "simulator3d"), "--"] + sim_args
        log("Simulator:", " ".join(cmd[:3]), "…")
        P.start("Simulator", cmd, senv, os.path.join(tmp, "simulator.log"))
        # --- Motion Watch: fresh settings, simulation on, no updates, no automatic simulator search
        cfg = os.path.join(tmp, "mw")
        os.makedirs(cfg, exist_ok=True)
        st = {"sim_on": True, "source": "sim:0", "thermal_source": "sim:thermal", "sim_url": "http://127.0.0.1:%d" % a.sim_port,
              "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_auto": False,
              "lang": "de", "desktop_notice": False, "setup_done": True}
        with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        if a.ki_ordner:                                          # the AI model next to the program (from GitHub Actions)
            for fn in os.listdir(a.ki_ordner):
                os.makedirs(os.path.join(cfg, "models"), exist_ok=True)
                shutil.copy(os.path.join(a.ki_ordner, fn), os.path.join(cfg, "models", fn))
        log("Motion Watch:", os.path.basename(mw))
        P.start("Motion Watch", [sys.executable, mw, "--headless", "--port", str(a.mw_port), "--bind", "127.0.0.1", "--config", cfg],
                env, os.path.join(tmp, "motionwatch.log"))
        sim = "http://127.0.0.1:%d" % a.sim_port
        web = "http://127.0.0.1:%d" % a.mw_port
        # --- wait: both running and connected, pictures coming
        t_end = time.time() + a.start_zeit
        ok = False
        while time.time() < t_end:
            try:
                s = http_json(web + "/api/state", timeout=4)["state"]
                c = http_json(sim + "/control", {"action": "get"}, timeout=4)
                if str(s.get("source_status", "")).startswith("connected") and float(s.get("fps") or 0) > 0 and "nicht verbunden" not in str(c.get("status", "")):
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(2)
        if not ok:
            log("Simulator und Motion Watch kamen nicht zusammen. Protokolle:", tmp)
            try:
                s = http_json(web + "/api/state", timeout=4)["state"]
                log("Motion Watch: Quelle «%s», %s Bilder/s, KI: %s" % (s.get("source_status"), s.get("fps"), s.get("ai_status")))
            except Exception as e:
                log("Motion Watch antwortet nicht:", e)
            try:
                log("Simulator:", http_json(sim + "/control", {"action": "get"}, timeout=4).get("status"))
            except Exception as e:
                log("Simulator antwortet nicht:", e)
            log_tail(os.path.join(tmp, "simulator.log"), "Simulator-Protokoll")
            log_tail(os.path.join(tmp, "motionwatch.log"), "Motion-Watch-Protokoll")
            return 2, None
        log("verbunden - %d s eingewöhnen" % a.eingewoehnen)
        time.sleep(a.eingewoehnen)
        s = http_json(web + "/api/state", timeout=4)["state"]
        info = {"datum": time.strftime("%Y-%m-%d %H:%M"), "mw_version": mw_version(mw), "ki": s.get("ai_status", "?"),
                "rechner": a.rechner or ("%s %s, %d Kerne" % (platform.system(), platform.machine(), os.cpu_count() or 0)),
                "qualitaet": a.qualitaet, "szene": a.szene, "kameras": "Kopfkamera" if a.kameras == [0] else "Kopf- und feste Kamera", "plaene": {}}
        try:
            info["sim_version"] = str(http_json(sim + "/info", timeout=4).get("name", "?")).split()[-1]
        except Exception:
            info["sim_version"] = "?"
        rc = 0
        for plan in a.plaene:
            for rep in range(a.wiederholungen):
                log("Testlauf «%s» (%d/%d) …" % (PLAN_NAME.get(plan, plan), rep + 1, a.wiederholungen))
                r = http_json(sim + "/control", {"action": "test_start", "plan": plan, "cams": a.kameras}, timeout=10)
                if not r.get("ok"):
                    log("  startet nicht:", r.get("error") or r.get("info"))
                    rc = 2
                    continue
                t0 = time.time()
                fps = []
                rep_ = None
                while time.time() - t0 < PLAN_DAUER.get(plan, 400) * 3 + 120:
                    time.sleep(5)
                    try:
                        fps.append(float(http_json(web + "/api/state", timeout=4)["state"].get("fps") or 0))
                        r = http_json(sim + "/control", {"action": "test_report"}, timeout=6)
                    except Exception:
                        continue
                    if not r.get("running"):
                        rep_ = r.get("report") or None
                        break
                if not rep_ or not rep_.get("persons"):
                    log("  kein Bericht (Zeit abgelaufen?)")
                    rc = 2
                    try:
                        http_json(sim + "/control", {"action": "test_stop"}, timeout=6)
                    except Exception:
                        pass
                    continue
                rep_["dauer_s"] = round(time.time() - t0)
                rep_["mw_fps"] = round(sum(fps) / len(fps), 1) if fps else 0
                info["plaene"].setdefault(plan, []).append(rep_)
                gb = kennzahlen([rep_])["groessen"]
                if gb:
                    log("  nach Grösse: " + ", ".join("%s %d/%d" % (b, gb[b][1], gb[b][0]) for b in ("nah", "mittel", "weit") if b in gb))
                log("  Personen %d/%d (%.0f %%), Reaktion %s s, Tiere %d/%d, Fehlalarme %d" % (
                    rep_["persons_detected"], rep_["persons"], rep_["rate"], rep_.get("latency_s", "–"),
                    sum(p.get("animals_reported", 0) for p in rep_.get("phases", [])), sum(p.get("animals", 0) for p in rep_.get("phases", [])),
                    rep_["false_alarms"]))
        if not info["plaene"]:
            return 2, None
        os.makedirs(ERGEBNISSE, exist_ok=True)
        fn = os.path.join(ERGEBNISSE, time.strftime("%Y-%m-%d_%H%M") + "_" + info["mw_version"] + ".json")
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=1)
        log("gespeichert:", os.path.relpath(fn, REPO))
        return rc, info
    finally:
        P.stop()
        if not a.behalten:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            log("Protokolle und Einstellungen:", tmp)


# ---------------------------------------------------------------------------------------------------------------------
def kennzahlen(reps):
    """the numbers of one plan (several runs: added up)"""
    P = sum(r["persons"] for r in reps)
    D = sum(r["persons_detected"] for r in reps)
    A = sum(p.get("animals", 0) for r in reps for p in r.get("phases", []))
    AR = sum(p.get("animals_reported", 0) for r in reps for p in r.get("phases", []))
    F = sum(r["false_alarms"] for r in reps)
    lat = [r["latency_s"] for r in reps if float(r.get("latency_s", -1)) >= 0]
    bands = {}                                                  # by size in the picture (simulator 3D-3.48 and newer)
    for r in reps:
        for v in r.get("visitors", []):
            if not v.get("person"):
                continue
            b = "nah" if v["px"] >= 100 else ("mittel" if v["px"] >= 60 else "weit")
            n, d = bands.get(b, (0, 0))
            bands[b] = (n + 1, d + (1 if float(v.get("det_s", -1)) >= 0 else 0))
    return {"groessen": bands, "personen": P, "erkannt": D, "quote": round(100.0 * D / max(1, P), 1), "reaktion": round(sum(lat) / len(lat), 1) if lat else None,
            "tiere": A, "tiere_gemeldet": AR, "fehlalarme": F, "fehlalarme_pro_lauf": round(F / max(1, len(reps)), 2), "laeufe": len(reps),
            "fps": round(sum(r.get("mw_fps", 0) for r in reps) / max(1, len(reps)), 1)}


def alle_ergebnisse():
    out = []
    for fn in sorted(glob.glob(os.path.join(ERGEBNISSE, "*.json"))):
        try:
            with open(fn, encoding="utf-8") as f:
                d = json.load(f)
            d["_datei"] = os.path.basename(fn)
            out.append(d)
        except (OSError, ValueError):
            pass
    return out


def vergleich(info):
    """this run against the last comparable one (same plan, same computer, AI the same): lines of text, worse?"""
    zeilen, schlechter = [], False
    alte = [d for d in alle_ergebnisse() if d.get("_datei") and d.get("datum") != info.get("datum")]
    for plan, reps in info["plaene"].items():
        k = kennzahlen(reps)
        vor = [d for d in alte if plan in d.get("plaene", {}) and d.get("rechner") == info.get("rechner") and d.get("ki") == info.get("ki")]
        if not vor:
            zeilen.append("%s: erster Lauf auf diesem Rechner – noch kein Vergleich." % PLAN_NAME.get(plan, plan))
            continue
        v = vor[-1]
        kv = kennzahlen(v["plaene"][plan])
        dq, df = k["quote"] - kv["quote"], k["fehlalarme_pro_lauf"] - kv["fehlalarme_pro_lauf"]
        urteil = "gleich"
        if dq <= -10 or df >= 1:
            urteil, schlechter = "SCHLECHTER", True
        elif dq >= 10 or df <= -1:
            urteil = "besser"
        zeilen.append("%s gegen %s: Personen %.0f %% (%+.0f), Fehlalarme pro Lauf %.1f (%+.1f) → %s" % (
            PLAN_NAME.get(plan, plan), v.get("mw_version"), k["quote"], dq, k["fehlalarme_pro_lauf"], df, urteil))
    return zeilen, schlechter


def verlauf_schreiben():
    rows = alle_ergebnisse()
    L = ["# Prüfstand – Verlauf der Erkennung", "",
         "Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.", "",
         "Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann",
         "für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom",
         "gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).", "",
         "Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).", "",
         "| Datum | Motion Watch | Simulator | Testlauf | Personen erkannt | nah / mittel / weit | Reaktion | Tiere gemeldet | Fehlalarme | Bilder/s | KI | Rechner |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in reversed(rows):
        for plan, reps in d.get("plaene", {}).items():
            k = kennzahlen(reps)
            gb = k["groessen"]
            gt = " / ".join(("%d/%d" % (gb[b][1], gb[b][0])) if b in gb else "–" for b in ("nah", "mittel", "weit")) if gb else "–"
            L.append("| %s | %s | %s | %s%s | %d / %d (**%.0f %%**) | %s | %s | %d / %d | %d | %s | %s | %s |" % (
                d.get("datum", "?"), d.get("mw_version", "?"), d.get("sim_version", "?"), PLAN_NAME.get(plan, plan),
                " ×%d" % k["laeufe"] if k["laeufe"] > 1 else "", k["erkannt"], k["personen"], k["quote"], gt,
                ("%.1f s" % k["reaktion"]) if k["reaktion"] is not None else "–", k["tiere_gemeldet"], k["tiere"], k["fehlalarme"],
                k["fps"], d.get("ki", "?"), d.get("rechner", "?")))
    if not rows:
        L.append("| – | noch kein Lauf | | | | | | | | | | |")
    L += ["", "## Einzelheiten pro Phase (letzter Lauf)", ""]
    if rows:
        d = rows[-1]
        for plan, reps in d.get("plaene", {}).items():
            L += ["**%s** – %s, Motion Watch %s" % (PLAN_NAME.get(plan, plan), d.get("datum"), d.get("mw_version")), "",
                  "| Phase | Personen | Reaktion | Tiere | Fehlalarme | verpasst, weil … |", "|---|---|---|---|---|---|"]
            for p in reps[-1].get("phases", []):
                why = p.get("missed_why") or {}
                WHY = {"dark": "zu dunkel", "small": "zu klein / weit weg", "fast": "zu schnell", "crouch": "geduckt"}
                why_t = ", ".join("%d× %s" % (v, WHY.get(k, k)) for k, v in why.items() if v) if isinstance(why, dict) else str(why)
                L.append("| %s | %d / %d | %s | %d / %d | %d | %s |" % (p.get("name"), p.get("persons_detected", 0), p.get("persons", 0),
                         ("%.1f s" % p["latency_s"]) if float(p.get("latency_s", -1)) >= 0 else "–", p.get("animals_reported", 0), p.get("animals", 0),
                         p.get("false_alarms", 0), why_t or "–"))
            L.append("")
    with open(VERLAUF, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Prüfstand für die Erkennung von Motion Watch (3D-Simulator)")
    ap.add_argument("--mw", default="", help="die Motion-Watch-Datei (Standard: die neuste im Repository)")
    ap.add_argument("--sim-bin", default="", help="das exportierte Simulator-Programm (Linux)")
    ap.add_argument("--godot", default="", help="Godot 4.3 (startet das Projekt simulator3d/ direkt)")
    ap.add_argument("--plaene", default="quick,night", help="quick, standard, night, hard (mit Komma)")
    ap.add_argument("--wiederholungen", type=int, default=1, help="jeden Testlauf so oft (mehr = verlässlichere Zahlen)")
    ap.add_argument("--szene", default="camping")
    ap.add_argument("--qualitaet", default="simple", help="Grafik des Simulators: simple, medium, nice")
    ap.add_argument("--sim-port", type=int, default=8795)
    ap.add_argument("--mw-port", type=int, default=5095)
    ap.add_argument("--start-zeit", type=int, default=240, help="so lange auf die Verbindung warten (s)")
    ap.add_argument("--eingewoehnen", type=int, default=25, help="Zeit für Motion Watch, sich auf das Bild einzustellen (s)")
    ap.add_argument("--kameras", default="kopf", help="welche Kameras für die Wahrheit zählen: kopf (nur sie erkennt Personen) oder beide")
    ap.add_argument("--ki-ordner", default="", help="Ordner mit dem KI-Modell (frozen_inference_graph.pb + .pbtxt)")
    ap.add_argument("--rechner", default="", help="Name des Rechners in der Tabelle (Standard: System, Kerne)")
    ap.add_argument("--ohne-xvfb", action="store_true", help="keinen virtuellen Bildschirm starten")
    ap.add_argument("--behalten", action="store_true", help="Protokolle und Einstellungen nicht löschen")
    ap.add_argument("--streng", action="store_true", help="Rückgabewert 3, wenn die Erkennung schlechter geworden ist")
    ap.add_argument("--nur-verlauf", action="store_true", help="nur VERLAUF.md aus den gespeicherten Ergebnissen schreiben")
    a = ap.parse_args()
    a.plaene = [p.strip() for p in a.plaene.split(",") if p.strip()]
    a.kameras = [0] if a.kameras == "kopf" else [0, 1]
    if a.nur_verlauf:
        verlauf_schreiben()
        log("VERLAUF.md geschrieben")
        return 0
    rc, info = run(a)
    if info:
        zeilen, schlechter = vergleich(info)
        for z in zeilen:
            log(z)
        tab = verlauf_schreiben()
        summ = os.environ.get("GITHUB_STEP_SUMMARY")
        if summ:                                                  # the page of the run on GitHub
            with open(summ, "a", encoding="utf-8") as f:
                f.write("## Prüfstand Motion Watch %s\n\n" % info["mw_version"] + "\n".join("- " + z for z in zeilen) + "\n\n" + tab.split("## Einzelheiten")[0])
        if a.streng and schlechter:
            return 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
