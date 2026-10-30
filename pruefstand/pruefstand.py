#!/usr/bin/env python3
"""Prüfstand für die Erkennung von Motion Watch.

Startet den 3D-Simulator und Motion Watch ohne Bildschirm, lässt feste Testläufe laufen (immer dieselben Besucher auf
denselben Wegen, siehe simulator3d/scripts/testrun.gd) und schreibt die Zahlen auf:
Pushes (richtig / falsch), Personen erkannt (%), Reaktionszeit, Tiere gemeldet, Flackern. Jeder Lauf kommt als JSON nach
pruefstand/ergebnisse/, die Tabelle pruefstand/VERLAUF.md wird daraus neu geschrieben und der Lauf mit dem vorherigen verglichen.

Beispiele:
  python3 pruefstand/pruefstand.py --godot /pfad/Godot_v4.3-stable_linux.x86_64          # aus dem Godot-Projekt
  python3 pruefstand/pruefstand.py --sim-bin /pfad/MotionWatch3D.x86_64 --plaene quick,night
  python3 pruefstand/pruefstand.py --godot … --plaene nacht --seeds 3                      # ganze Nacht, 3 Zufallsstarts
  python3 pruefstand/pruefstand.py --nur-verlauf                                            # nur VERLAUF.md neu schreiben
  python3 pruefstand/pruefstand.py --wege-einlesen                                          # Schleichwege aus feedback/ übernehmen
  python3 pruefstand/pruefstand.py --fall-aus-spur alarm_tracks.json [--spur-id ID]        # echte Nacht als Prüfstand-Fall

Der Rückgabewert ist 0, wenn alles lief; 2, wenn ein Lauf nicht zu Ende kam; 3 mit --streng, wenn die Erkennung
schlechter ist als beim letzten vergleichbaren Lauf.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
ERGEBNISSE = os.path.join(HIER, "ergebnisse")
VERLAUF = os.path.join(HIER, "VERLAUF.md")
PLAN_DAUER = {"quick": 150, "standard": 300, "night": 230, "hard": 520, "nacht": 650}   # Sekunden, ungefähr (Simulator in Echtzeit)
# Neue Szenen (Simulator 3D-4.x, szenenplus.gd): jeder Plan lädt seine eigene Szene (--szene gilt dafür nicht) - nicht in «quick»
PLAN_DAUER.update({"camping_voll": 290, "tarnen": 270, "velodieb": 230})
PLAN_NAME = {"quick": "Kurz (Tag + Nacht)", "standard": "Standard (Tag, Wind, Nacht, Regen)", "night": "Nacht", "hard": "Schwierige Bedingungen",
             "nacht": "Ganze Nacht (20–6 Uhr, Zeitraffer)", "spielwege": "Schleichwege aus dem Spiel", "echtenaechte": "Echte Nächte nachgespielt"}
PLAN_NAME.update({"camping_voll": "Voller Campingplatz", "tarnen": "Tarnen und Kriechen", "velodieb": "Velodieb"})
FIX_PLAENE = ("spielwege", "echtenaechte", "nacht")      # Prüfstand 2: realistic numbers - --mal does not multiply, no run without effects
WEGE = os.path.join(REPO, "simulator3d", "spielwege")
NAECHTE = os.path.join(REPO, "simulator3d", "pruefnaechte")
ROH = "~roh"                  # 2.98.13: the same plan without the camera effects of the simulator (blur, colours, grain)


def plan_name(key):
    base = key[:-len(ROH)] if key.endswith(ROH) else key
    return PLAN_NAME.get(base, base) + (" · ohne Kamera-Effekte" if key.endswith(ROH) else "")


def log(*a, wichtig=False):
    print("[pruefstand]", *a, flush=True)
    if wichtig and os.environ.get("GITHUB_ACTIONS"):                       # on GitHub: also as a note on the page of the run
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


def cpu_modell():
    """the processor (e.g. «AMD EPYC 7763»): on GitHub the runners differ and with them the frame rate of the simulator"""
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as f:
            for z in f:
                if z.lower().startswith("model name"):
                    return re.sub(r"\s+(\d+-Core )?Processor\s*$", "", z.split(":", 1)[1].strip())[:40]
    except OSError:
        pass
    return platform.processor()[:40]


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
              "lang": "de", "desktop_notice": False, "setup_done": True,
              # Prüfstand 2: the pushes go into the test inbox of the simulation and are counted (MoveEye part 068);
              # the thermal camera is on - at night without light it sees the persons (part 232)
              "notify_sandbox": True, "thermal_on": a.waermebild == "an"}
        if a.weitwinkel:                                         # «Übersicht → Kopf findet Ziel»: the wide camera as extra camera,
            st.update(extra_cams=["sim:1"], pan_servo_range=360, pan_limit=170)   # a pan servo that can look back (cable limit ± 170°)
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
            log("Simulator und Motion Watch kamen nicht zusammen. Protokolle:", tmp, wichtig=True)
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
        try:                                                     # 2.98.13: the simulator must not start its own quick test now
            http_json(sim + "/control", {"action": "pruefstand", "do": "auto", "on": False}, timeout=6)
        except Exception:
            pass
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
        info["cpu"] = cpu_modell()                       # GitHub gives different processors: the frame rate depends on it
        info["besucher_mal"] = a.mal
        info["seeds"] = a.seeds
        info["waermebild"] = a.waermebild
        laeufe = [(p, m) for m in a.realismus for p in a.plaene
                  if not (m == "aus" and (p in FIX_PLAENE or (a.roh_plaene and p not in a.roh_plaene)))]
        for plan0, modus in laeufe:
          try:                                                   # 2.98.13: camera effects of the simulator on / off
              http_json(sim + "/control", {"action": "set", "id": "real_fx", "value": modus == "an"}, timeout=6)
              http_json(sim + "/control", {"action": "set", "id": "real_look", "value": False}, timeout=6)
          except Exception:
              pass
          plan = plan0 + ("" if modus == "an" else ROH)
          for seed_n, rep in [(sd, rp) for sd in range(1, a.seeds + 1) for rp in range(a.wiederholungen)]:
                log("Testlauf «%s» (Zufall %d, %d/%d) …" % (plan_name(plan), seed_n, rep + 1, a.wiederholungen))
                try:
                    st_ = http_json(sim + "/control", {"action": "test_report"}, timeout=6)
                    if st_.get("running"):
                        log("  (es lief schon ein Testlauf: %s – gestoppt)" % st_.get("info"))
                        http_json(sim + "/control", {"action": "test_stop"}, timeout=6)
                except Exception:
                    pass
                r = http_json(sim + "/control", {"action": "test_start", "plan": plan0, "cams": a.kameras, "mult": a.mal, "seed": seed_n}, timeout=10)
                if not r.get("ok"):
                    log("  startet nicht:", r.get("error") or r.get("info"))
                    rc = 2
                    continue
                t0 = time.time()
                fps = []
                rep_ = None
                soll = float(r.get("total_s") or PLAN_DAUER.get(plan0, 400) * a.mal)       # the simulator knows how long it takes
                log("  dauert etwa %d Min." % round(soll / 60.0))
                while time.time() - t0 < soll * 2.5 + 180:
                    time.sleep(5)
                    try:
                        fps.append(float(http_json(web + "/api/state", timeout=4)["state"].get("fps") or 0))
                        r = http_json(sim + "/control", {"action": "test_report"}, timeout=6)
                    except Exception:
                        continue
                    if not r.get("running"):
                        rep_ = r.get("report") or None
                        break
                if not rep_ or not rep_.get("phases") or rep_.get("plan") != plan0:      # (0 visible persons is a valid result)
                    log("%s: kein Bericht – %s" % (plan_name(plan), (r.get("info") if isinstance(r, dict) else "") or "Zeit abgelaufen"), wichtig=True)
                    rep_ = None
                    rc = 2
                    try:
                        http_json(sim + "/control", {"action": "test_stop"}, timeout=6)
                    except Exception:
                        pass
                    continue
                rep_["dauer_s"] = round(time.time() - t0)
                rep_["mw_fps"] = round(sum(fps) / len(fps), 1) if fps else 0
                rep_.setdefault("seed", seed_n)
                info["plaene"].setdefault(plan, []).append(rep_)
                gb = kennzahlen([rep_])["groessen"]
                if gb:
                    log("  nach Grösse: " + ", ".join("%s %d/%d" % (b, gb[b][1], gb[b][0]) for b in ("nah", "mittel", "weit") if b in gb))
                pu = rep_.get("pushes") or {}
                log("%s: Pushes %s, Personen %d/%d (%.0f %%, davon nur Wärmebild %d/%d), Reaktion %s s, Tiere %d/%d, Flackern %d, %.1f Bilder/s" % (
                    plan_name(plan), ("richtig %d / falsch %d" % (pu.get("ok", 0), pu.get("false", 0))) if pu else "unbekannt",
                    rep_["persons_detected"], rep_["persons"], rep_["rate"], rep_.get("persons_thermal_detected", 0), rep_.get("persons_thermal", 0),
                    rep_.get("latency_s", "–"),
                    sum(p.get("animals_reported", 0) for p in rep_.get("phases", [])), sum(p.get("animals", 0) for p in rep_.get("phases", [])),
                    rep_.get("flicker", rep_.get("false_alarms", 0)), rep_["mw_fps"]), wichtig=True)
                sz = rep_.get("szene") or {}                     # the numbers of the new scenes (reaction from the pitch / the grab)
                if sz.get("art") == "camping_voll":
                    log("  Voller Platz: an deinem Platz %d, mit Push %d, ohne %d, Reaktion ab Platz %s s, falsche Pushes wegen Nachbarn %d" % (
                        sz.get("auf_platz", 0), sz.get("push", 0), sz.get("ohne_push", 0), sz.get("reaktion_platz_s", "–"), sz.get("push_falsch_nachbar", 0)), wichtig=True)
                elif sz.get("art") == "velodieb":
                    log("  Velodieb: Griffe %d, Push vor dem Griff %d, danach %d, ohne %d, Reaktion ab Griff %s s" % (
                        sz.get("griffe", 0), sz.get("push_vor_griff", 0), sz.get("push_nach_griff", 0), sz.get("ohne_push", 0), sz.get("reaktion_griff_s", "–")), wichtig=True)
                elif sz.get("art") == "tarnen":
                    log("  Tarnen: " + ", ".join("%s %d/%d erkannt, %d Push" % (k[5:], v.get("erkannt", 0), v.get("sichtbar", 0), v.get("push", 0))
                                                for k, v in sorted((sz.get("arten") or {}).items())), wichtig=True)
                for q in rep_.get("push_list", []):
                    log("    Push %5.0f s  %-8s %s%s" % (q.get("t", 0), q.get("ev", ""), ("richtig: " if q.get("ok") else "FALSCH: ") + str(q.get("who", "")),
                                                     "  (gleicher Besuch innert 10 s)" if q.get("dup") else ""))
        if a.weitwinkel:
            info["weitwinkel"] = weitwinkel_messung(a, sim, web)
        if not info["plaene"] and info.get("weitwinkel"):        # only the wide-angle measurement: its own file, not in VERLAUF.md
            os.makedirs(ERGEBNISSE, exist_ok=True)
            fn = os.path.join(ERGEBNISSE, "weitwinkel_" + time.strftime("%Y-%m-%d_%H%M") + "_" + info["mw_version"] + ".json")
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=1)
            log("gespeichert:", os.path.relpath(fn, REPO))
            return 0, None
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
    """the numbers of one plan (several runs: added up; «streuung» = min / max over the runs - seeds and repetitions)"""
    P = sum(r["persons"] for r in reps)
    D = sum(r["persons_detected"] for r in reps)
    A = sum(p.get("animals", 0) for r in reps for p in r.get("phases", []))
    AR = sum(p.get("animals_reported", 0) for r in reps for p in r.get("phases", []))
    F = sum(r.get("flicker", r.get("false_alarms", 0)) for r in reps)          # «Flackern» (before Prüfstand 2: «Fehlalarme»)
    lat = [r["latency_s"] for r in reps if float(r.get("latency_s", -1)) >= 0]
    bands = {}                                                  # by size in the picture (simulator 3D-3.48 and newer)
    for r in reps:
        for v in r.get("visitors", []):
            if not v.get("person") or v.get("thermal_only"):      # only seen in the thermal picture: own column «Wärmebild»
                continue
            b = "nah" if v["px"] >= 100 else ("mittel" if v["px"] >= 60 else "weit")
            n, d = bands.get(b, (0, 0))
            bands[b] = (n + 1, d + (1 if float(v.get("det_s", -1)) >= 0 else 0))
    mit_push = [r for r in reps if r.get("pushes")]               # Prüfstand 2: the real pushes (MoveEye part 068)
    po = sum(r["pushes"].get("ok", 0) for r in mit_push)
    pf = sum(r["pushes"].get("false", 0) for r in mit_push)
    quoten = [100.0 * r["persons_detected"] / r["persons"] for r in reps if r.get("persons")]
    return {"groessen": bands, "personen": P, "erkannt": D, "quote": round(100.0 * D / max(1, P), 1), "reaktion": round(sum(lat) / len(lat), 1) if lat else None,
            "tiere": A, "tiere_gemeldet": AR, "flackern": F, "fehlalarme": F, "fehlalarme_pro_lauf": round(F / max(1, len(reps)), 2), "laeufe": len(reps),
            "fps": round(sum(r.get("mw_fps", 0) for r in reps) / max(1, len(reps)), 1),
            "pushes": bool(mit_push), "push_richtig": po, "push_falsch": pf,
            "push_falsch_pro_lauf": round(pf / max(1, len(mit_push)), 2), "push_richtig_pro_lauf": round(po / max(1, len(mit_push)), 2),
            "waerme": sum(r.get("persons_thermal", 0) for r in reps), "waerme_erkannt": sum(r.get("persons_thermal_detected", 0) for r in reps),
            "seeds": sorted({int(r.get("seed", 1)) for r in reps}),
            "streuung_quote": (round(min(quoten)), round(max(quoten))) if len(quoten) > 1 else None,
            "streuung_falsch": (min(r["pushes"].get("false", 0) for r in mit_push), max(r["pushes"].get("false", 0) for r in mit_push)) if len(mit_push) > 1 else None,
            "streuung_richtig": (min(r["pushes"].get("ok", 0) for r in mit_push), max(r["pushes"].get("ok", 0) for r in mit_push)) if len(mit_push) > 1 else None}


def alle_ergebnisse():
    out = []
    for fn in sorted(glob.glob(os.path.join(ERGEBNISSE, "*.json"))):
        if os.path.basename(fn).startswith("weitwinkel_"):        # the wide-angle measurement alone is not a test run
            continue
        try:
            with open(fn, encoding="utf-8") as f:
                d = json.load(f)
            d["_datei"] = os.path.basename(fn)
            out.append(d)
        except (OSError, ValueError):
            pass
    return out


def ki_art(d):
    """«mit KI» / «ohne KI» - the status text also has the time per picture, that must not prevent a comparison"""
    k = str(d.get("ki", ""))
    return "mit KI" if k.startswith(("running", "ready")) else ("ohne KI" if k else "?")


def vergleich(info):
    """this run against the last comparable one (same plan, same computer, AI the same): lines of text, worse?
    Prüfstand 2: when both runs have real pushes, one false push more per run (or 15 points fewer persons) is worse;
    otherwise the flicker as before."""
    zeilen, schlechter = [], False
    alte = [d for d in alle_ergebnisse() if d.get("_datei") and d.get("datum") != info.get("datum")]
    for plan, reps in info["plaene"].items():
        k = kennzahlen(reps)
        vor = [d for d in alte if plan in d.get("plaene", {}) and d.get("rechner") == info.get("rechner") and ki_art(d) == ki_art(info)]
        if not vor:
            zeilen.append("%s: erster Lauf auf diesem Rechner – noch kein Vergleich." % plan_name(plan))
            continue
        v = vor[-1]
        kv = kennzahlen(v["plaene"][plan])
        pushes = k["pushes"] and kv["pushes"]
        dq = k["quote"] - kv["quote"]
        df = (k["push_falsch_pro_lauf"] - kv["push_falsch_pro_lauf"]) if pushes else (k["fehlalarme_pro_lauf"] - kv["fehlalarme_pro_lauf"])
        was = "falsche Pushes" if pushes else "Flackern"
        urteil = "gleich"
        if min(k["personen"], kv["personen"]) < 8:              # 2.98.13: too few persons - one miss would be 20 %+
            if pushes and df >= 1:
                urteil, schlechter = "SCHLECHTER", True
            zeilen.append("%s: zu wenige Personen für einen Vergleich (%d / %d) – Personen %.0f %%, %s pro Lauf %.1f (%+.1f)%s." % (
                plan_name(plan), k["personen"], kv["personen"], k["quote"], was,
                k["push_falsch_pro_lauf"] if pushes else k["fehlalarme_pro_lauf"], df, " → SCHLECHTER" if urteil == "SCHLECHTER" else ""))
            continue
        if dq <= -15 or df >= 1:
            urteil, schlechter = "SCHLECHTER", True
        elif dq >= 15 or df <= -1:
            urteil = "besser"
        zeilen.append("%s gegen %s: Personen %.0f %% (%+.0f), %s pro Lauf %.1f (%+.1f) → %s" % (
            plan_name(plan), v.get("mw_version"), k["quote"], dq, was, k["push_falsch_pro_lauf"] if pushes else k["fehlalarme_pro_lauf"], df, urteil))
    return zeilen, schlechter


def _spanne(t):
    return ("%d–%d" % t) if t and t[0] != t[1] else (("%d" % t[0]) if t else "")


def verlauf_schreiben():
    rows = alle_ergebnisse()
    L = ["# Prüfstand – Verlauf der Erkennung", "",
         "Automatisch geschrieben von `pruefstand/pruefstand.py` aus den Dateien in `pruefstand/ergebnisse/`. Nicht von Hand ändern.", "",
         "Jeder Testlauf schickt immer dieselben Besucher auf denselben Wegen durch den 3D-Simulator. Der Simulator weiss, wer wann",
         "für eine Kamera sichtbar war, und vergleicht das mit den Meldungen von Motion Watch. Vergleichbar sind nur Zeilen vom",
         "gleichen Rechner und mit gleichem KI-Stand (ein langsamer Rechner liefert weniger Bilder pro Sekunde).", "",
         "**Pushes richtig / falsch** (ab Prüfstand 2): die Push-Nachrichten, die MoveEye wirklich verschickt hat (Test-Postfach der",
         "Simulation). Richtig = eine Person war sichtbar oder im Bild; derselbe Besuch nochmals innert 10 s zählt einmal.",
         "Bei «Ganze Nacht» ist das die Zahl pro Nacht. **Flackern** = jede kurze Personen-Meldung ohne sichtbare Person (hiess",
         "vorher «Fehlalarme»; ein Dachs gab so 3–5 «Fehlalarme» in Sekunden, aber höchstens einen Push).",
         "**Wärmebild**: Personen, die nachts nur die Wärmebildkamera sah (ohne Licht, zu weit fürs Infrarot) – erkannt / sichtbar.",
         "Mehrere Läufe (Zufall 1, 2, 3 … oder Wiederholungen): in Klammern die Streuung (kleinster–grösster Wert pro Lauf).", "",
         "Spalten nah / mittel / weit: Personen nach Grösse im Bild (Höhe ≥ 100 Bildpunkte ≈ näher als 6 m, 60–100, 30–60 bei 540 Zeilen).", "",
         "| Datum | Motion Watch | Simulator | Testlauf | Pushes richtig / falsch | Personen erkannt | Wärmebild | nah / mittel / weit | Reaktion | Tiere gemeldet | Flackern | Bilder/s | KI | Rechner |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in reversed(rows):
        for plan, reps in d.get("plaene", {}).items():
            k = kennzahlen(reps)
            gb = k["groessen"]
            gt = " / ".join(("%d/%d" % (gb[b][1], gb[b][0])) if b in gb else "–" for b in ("nah", "mittel", "weit")) if gb else "–"
            if k["pushes"]:
                pt = "**%d** / **%d**" % (k["push_richtig"], k["push_falsch"])
                if k["laeufe"] > 1:
                    pt += " (falsch %s pro Lauf)" % _spanne(k["streuung_falsch"]) if k["streuung_falsch"] else ""
                if plan.split("~")[0] == "nacht":
                    pt += " pro Nacht" if k["laeufe"] == 1 else " in %d Nächten (Ø %.1f / %.1f pro Nacht)" % (
                        k["laeufe"], k["push_richtig_pro_lauf"], k["push_falsch_pro_lauf"])
            else:
                pt = "–"
            st = (" (%s %%)" % _spanne(k["streuung_quote"])) if k["streuung_quote"] else ""
            zl = (" ×%d" % k["laeufe"] if k["laeufe"] > 1 else "") + ((" · Zufall %s" % ",".join(str(x) for x in k["seeds"])) if k["seeds"] != [1] else "")
            L.append("| %s | %s | %s | %s%s | %s | %d / %d (**%.0f %%**)%s | %s | %s | %s | %d / %d | %d | %s | %s | %s |" % (
                d.get("datum", "?"), d.get("mw_version", "?"), d.get("sim_version", "?"), plan_name(plan),
                zl + (" – *%s*" % d["bemerkung"] if d.get("bemerkung") else ""), pt,
                k["erkannt"], k["personen"], k["quote"], st, ("%d / %d" % (k["waerme_erkannt"], k["waerme"])) if k["waerme"] else "–", gt,
                ("%.1f s" % k["reaktion"]) if k["reaktion"] is not None else "–", k["tiere_gemeldet"], k["tiere"], k["flackern"],
                k["fps"], ki_art(d), d.get("rechner", "?") + (" · " + d["cpu"] if d.get("cpu") else "")))
    if not rows:
        L.append("| – | noch kein Lauf | | | | | | | | | | | | |")
    L += ["", "## Einzelheiten pro Phase (letzter Lauf)", ""]
    if rows:
        d = rows[-1]
        for plan, reps in d.get("plaene", {}).items():
            L += ["**%s** – %s, Motion Watch %s" % (plan_name(plan), d.get("datum"), d.get("mw_version")), "",
                  "| Phase | Pushes richtig / falsch | Personen | Wärmebild | Reaktion | Tiere | Flackern | verpasst, weil … |", "|---|---|---|---|---|---|---|---|"]
            for p in reps[-1].get("phases", []):
                why = p.get("missed_why") or {}
                WHY = {"dark": "zu dunkel", "small": "zu klein / weit weg", "fast": "zu schnell", "crouch": "geduckt"}
                why_t = ", ".join("%d× %s" % (v, WHY.get(k, k)) for k, v in why.items() if v) if isinstance(why, dict) else str(why)
                L.append("| %s | %s | %d / %d | %s | %s | %d / %d | %d | %s |" % (p.get("name"),
                         ("%d / %d" % (p.get("pushes_ok", 0), p.get("pushes_false", 0))) if reps[-1].get("pushes") else "–",
                         p.get("persons_detected", 0), p.get("persons", 0),
                         ("%d / %d" % (p.get("persons_thermal_detected", 0), p.get("persons_thermal", 0))) if p.get("persons_thermal") else "–",
                         ("%.1f s" % p["latency_s"]) if float(p.get("latency_s", -1)) >= 0 else "–", p.get("animals_reported", 0), p.get("animals", 0),
                         p.get("flicker", p.get("false_alarms", 0)), why_t or "–"))
            L.append("")
    with open(VERLAUF, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return "\n".join(L)


# ---- Prüfstand 2: sneaking ways from the game and real nights as bench cases ----------------------------------------
def _gd_round(x):
    """round like GDScript (half away from zero) - the key of a way must be the same as in gamelearn.gd way_key()"""
    return int(math.floor(abs(x) + 0.5)) * (1 if x >= 0 else -1)


def weg_schluessel(w):
    t = str(w.get("scene", ""))
    for q in w.get("points", []):
        if isinstance(q, list) and len(q) >= 3:
            t += ";%d,%d" % (_gd_round(float(q[1]) * 10.0), _gd_round(float(q[2]) * 10.0))
    return hashlib.md5(t.encode("utf-8")).hexdigest()[:12]


def _weg_ok(w):
    return isinstance(w, dict) and isinstance(w.get("points"), list) and len(w["points"]) >= 6 and w.get("scene")


def wege_einlesen():
    """unseen ways from game reports (feedback/**/*.zip, feedback/**/schleichweg_*.json, also from the simulator button)
    → simulator3d/spielwege/schleichweg_<key>.json; the same way (same scene, same points) only once"""
    os.makedirs(WEGE, exist_ok=True)
    da = {}
    for fn in glob.glob(os.path.join(WEGE, "schleichweg_*.json")):
        try:
            with open(fn, encoding="utf-8") as f:
                da[weg_schluessel(json.load(f))] = fn
        except (OSError, ValueError):
            pass
    gefunden = []
    for fn in glob.glob(os.path.join(REPO, "feedback", "**", "*"), recursive=True):
        b = os.path.basename(fn)
        try:
            if b.startswith("schleichweg") and b.endswith(".json"):
                with open(fn, encoding="utf-8") as f:
                    gefunden.append(json.load(f))
            elif b.endswith(".zip"):
                with zipfile.ZipFile(fn) as z:
                    for n in z.namelist():
                        if os.path.basename(n).startswith("schleichweg") and n.endswith(".json"):
                            gefunden.append(json.loads(z.read(n).decode("utf-8", "replace")))
        except (OSError, ValueError, zipfile.BadZipFile):
            continue
    neu = 0
    for w in gefunden:
        if not _weg_ok(w):
            continue
        k = weg_schluessel(w)
        if k in da:
            continue
        w.pop("file", None)
        w.pop("key", None)
        ziel = os.path.join(WEGE, "schleichweg_%s.json" % k)
        with open(ziel, "w", encoding="utf-8") as f:
            json.dump(w, f, ensure_ascii=False)
        da[k] = ziel
        neu += 1
    if neu:
        log("%d neue Schleichwege nach simulator3d/spielwege/ übernommen" % neu, wichtig=True)
    return neu


def fall_aus_spur(pfad, spur_id="", wetter="", wind=None, titel=""):
    """an alarm track of MoveEye (alarm_tracks.json in its settings folder, or one track as JSON) → a real night for the
    test bench: simulator3d/pruefnaechte/nacht_<date>.json (format: pruefstand/LIESMICH.md)"""
    with open(pfad, encoding="utf-8") as f:
        d = json.load(f)
    spuren = d if isinstance(d, list) else ([d] if isinstance(d, dict) and "samples" in d else d.get("tracks", []))
    spuren = [t for t in spuren if isinstance(t, dict) and len(t.get("samples") or []) >= 3]
    if spur_id:
        spuren = [t for t in spuren if str(t.get("id")) == spur_id]
    if not spuren:
        sys.exit("keine Alarm-Spur mit mindestens 3 Punkten gefunden" + (" (Kennung %s)" % spur_id if spur_id else ""))
    t = spuren[-1]
    sm = sorted(t["samples"], key=lambda x: float(x.get("t", 0)))
    t0 = float(t.get("t") or sm[0].get("t") or time.time())
    lt = time.localtime(t0)
    fall = {"v": 1, "title": titel or ("Alarm %s" % time.strftime("%d.%m. %H:%M", lt)), "date": time.strftime("%Y-%m-%d %H:%M", lt),
            "hour": round(lt.tm_hour + lt.tm_min / 60.0, 1), "weather": wetter or "clear", "wind": float(wind if wind is not None else 10),
            "quelle": "MoveEye-Alarm %s (%s)" % (t.get("id", "?"), "Simulation" if t.get("sim") else "echt"),
            "samples": [{"t": x.get("t", 0), "pan": x.get("pan", 0), "tilt": x.get("tilt", 0), "objs": x.get("objs", [])} for x in sm]}
    os.makedirs(NAECHTE, exist_ok=True)
    ziel = os.path.join(NAECHTE, "nacht_%s.json" % time.strftime("%Y%m%d_%H%M", lt))
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(fall, f, ensure_ascii=False, indent=1)
    log("Prüfstand-Fall geschrieben:", os.path.relpath(ziel, REPO), "(%d Punkte, %.0f s)" % (len(sm), float(sm[-1]["t"]) - float(sm[0]["t"])))
    return ziel


# ---- «Übersicht → Kopf findet Ziel» (Plan Daniel 30.10.2026, docs/Gehaeuse_Variante2_Weitwinkel.md) ---------------------
WW_MONTAGEN = {"scene": "Mast (Szene)", "base": "Unterteil vorne, fest", "head_front": "Kopf vorne", "head_rear": "Kopf hinten"}


def _ww_probe(sim):
    return http_json(sim + "/control", {"action": "weit", "do": "probe"}, timeout=6).get("probe") or {}


def weitwinkel_messung(a, sim, web):
    """per mount of the wide camera: a person enters the wide picture OUTSIDE the picture of the head camera (front mounts:
    beside the head, rear: behind it) - how long until the head camera has it in its picture (the head turned, simulator
    geometry), and until MoveEye reports a person. The simulator knows where everybody is (control weit/probe)."""
    res = {}
    try:
        http_json(sim + "/control", {"action": "set", "id": "auto", "value": False}, timeout=6)       # only our visitors
        http_json(web + "/api/arm", {"action": "arm_now"}, timeout=6)
    except Exception as e:
        log("Weitwinkel: Vorbereitung ging nicht:", e, wichtig=True)
        return res
    for m in a.weitwinkel:
        http_json(sim + "/control", {"action": "weit", "mount": m}, timeout=6)
        zeiten, ki, verpasst = [], [], 0
        for k in range(max(1, a.ww_versuche)):
            try:
                http_json(sim + "/control", {"action": "press", "id": "clear"}, timeout=6)
            except Exception:
                pass
            t_end = time.time() + 40                          # the head at home (it may still come back from before)
            while time.time() < t_end:
                try:
                    if abs(float(_ww_probe(sim).get("head_deg") or 0)) < 6:
                        break
                except Exception:
                    pass
                time.sleep(1)
            time.sleep(6 if k else 15)                        # the picture of the overview settles (background)
            seite = 1 if k % 2 == 0 else -1
            if m == "head_rear":                              # behind the head: across, 9 m away
                b0, b1, d0, d1 = 180 - seite * 30, 180 + seite * 35, 9, 9
            else:                                             # beside the head: in the wide picture (±51°) but not in the head's
                b0, b1, d0, d1 = seite * 42, seite * 42, 14, 6   # (±33°) - it walks straight towards the device and stays there
            http_json(sim + "/control", {"action": "weit", "do": "spawn", "kind": "person", "bearing": b0, "dist": d0,
                                         "to_bearing": b1, "to_dist": d1, "speed": 0.3}, timeout=6)
            t_wide = t_head = t_mw = None
            t0 = time.time()
            while time.time() - t0 < 50:
                time.sleep(0.5)
                try:
                    pr = _ww_probe(sim)
                    vs = [v for v in pr.get("visitors") or [] if v.get("kind") == "person"]
                    now = time.time()
                    if t_wide is None and any(v.get("wide") and not v.get("head") for v in vs):
                        t_wide = now
                    if t_wide is not None and t_head is None and any(v.get("head") for v in vs):
                        t_head = now
                    if t_wide is not None and t_mw is None and int(http_json(web + "/api/state", timeout=4)["state"].get("persons") or 0) > 0:
                        t_mw = now
                    if t_head is not None and (t_mw is not None or now - t_head > 10):
                        break
                except Exception:
                    continue
            if t_wide is None:
                log("  %s, Besucher %d: kam nicht ins Weitwinkel-Bild (ausserhalb der Kopfkamera)" % (WW_MONTAGEN[m], k + 1))
                verpasst += 1
                continue
            if t_head is None:
                verpasst += 1
                log("  %s, Besucher %d: Kopf fand ihn nicht (50 s)" % (WW_MONTAGEN[m], k + 1))
            else:
                zeiten.append(round(t_head - t_wide, 1))
                if t_mw is not None:
                    ki.append(round(t_mw - t_wide, 1))
                log("  %s, Besucher %d: Kopfkamera sieht ihn nach %.1f s%s" % (WW_MONTAGEN[m], k + 1, t_head - t_wide,
                    (", MoveEye meldet eine Person nach %.1f s" % (t_mw - t_wide)) if t_mw is not None else ", MoveEye meldete keine Person"))
        med = round(sorted(zeiten)[len(zeiten) // 2] if len(zeiten) % 2 else sum(sorted(zeiten)[len(zeiten) // 2 - 1:len(zeiten) // 2 + 1]) / 2.0, 1) if zeiten else None
        res[m] = {"versuche": max(1, a.ww_versuche), "gefunden": len(zeiten), "verpasst": verpasst, "zeiten_s": zeiten,
                  "median_s": med, "moveeye_person_s": ki}
        log("Übersicht → Kopf findet Ziel · %s: %d/%d gefunden%s" % (WW_MONTAGEN[m], len(zeiten), max(1, a.ww_versuche),
            (", Median %.1f s" % med) if med is not None else ""), wichtig=True)
    try:
        http_json(sim + "/control", {"action": "press", "id": "clear"}, timeout=6)
        http_json(sim + "/control", {"action": "weit", "mount": "scene"}, timeout=6)
    except Exception:
        pass
    return res


def main():
    ap = argparse.ArgumentParser(description="Prüfstand für die Erkennung von Motion Watch (3D-Simulator)")
    ap.add_argument("--mw", default="", help="die Motion-Watch-Datei (Standard: die neuste im Repository)")
    ap.add_argument("--sim-bin", default="", help="das exportierte Simulator-Programm (Linux)")
    ap.add_argument("--godot", default="", help="Godot 4.3 (startet das Projekt simulator3d/ direkt)")
    ap.add_argument("--plaene", default="quick,night", help="quick, standard, night, hard, nacht (ganze Nacht), camping_voll, tarnen, velodieb – mit Komma")
    ap.add_argument("--wiederholungen", type=int, default=1, help="jeden Testlauf so oft (mehr = verlässlichere Zahlen)")
    ap.add_argument("--seeds", type=int, default=1, help="so viele Zufallsstarts (1 = die festen Besucher von früher, 4711; 2, 3 … andere Wege)")
    ap.add_argument("--mal", type=int, default=2, help="jede Besucherliste so oft, 1–5 (mehr Personen pro Lauf = verlässlichere Zahlen)")
    ap.add_argument("--realismus", default="an", help="Kamera-Effekte des Simulators: an, aus oder an,aus (beides messen)")
    ap.add_argument("--roh-plaene", default="", help="nur diese Testläufe auch ohne Kamera-Effekte (Standard: alle, wenn --realismus an,aus)")
    ap.add_argument("--waermebild", default="an", choices=["an", "aus"], help="Wärmebildkamera von MoveEye an (Standard) oder aus")
    ap.add_argument("--szene", default="stellplatz", help="Szene (2.98.13: Stellplatz - freie Sicht wie auf einem Camping-Platz; camping verdeckt viel)")
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
    ap.add_argument("--wege-einlesen", action="store_true", help="nur die Schleichwege aus feedback/ nach simulator3d/spielwege/ übernehmen")
    ap.add_argument("--ohne-extras", action="store_true", help="Schleichwege und echte Nächte nicht automatisch mitlaufen lassen")
    ap.add_argument("--fall-aus-spur", default="", help="eine Alarm-Spur von MoveEye (alarm_tracks.json) als echte Nacht speichern")
    ap.add_argument("--spur-id", default="", help="welche Spur aus der Datei (Standard: die neuste)")
    ap.add_argument("--weitwinkel", default="", help="Messung «Übersicht → Kopf findet Ziel» pro Montage der Weitwinkel-Kamera: scene, base, head_front, head_rear (mit Komma)")
    ap.add_argument("--ww-versuche", type=int, default=3, help="Weitwinkel-Messung: so viele Besucher pro Montage")
    ap.add_argument("--spur-wetter", default="", help="Wetter der echten Nacht (clear, cloudy, rain, fog, snow)")
    a = ap.parse_args()
    a.plaene = [p.strip() for p in a.plaene.split(",") if p.strip()]
    a.realismus = [m.strip() for m in a.realismus.split(",") if m.strip() in ("an", "aus")] or ["an"]
    a.roh_plaene = [p.strip() for p in a.roh_plaene.split(",") if p.strip()]
    a.mal = max(1, min(5, a.mal))
    a.weitwinkel = [m.strip() for m in a.weitwinkel.split(",") if m.strip() in WW_MONTAGEN]
    a.seeds = max(1, min(9, a.seeds))
    if a.fall_aus_spur:
        fall_aus_spur(a.fall_aus_spur, a.spur_id, a.spur_wetter)
        return 0
    if a.wege_einlesen:
        wege_einlesen()
        return 0
    if not a.nur_verlauf:
        wege_einlesen()                                        # Prüfstand 2: new ways from the game reports in feedback/
    # the sneaking ways of the game (simulator3d/spielwege/schleichweg_*.json, from 3D-3.53) always run along: did a change
    # close a known blind spot? The same for the real nights (simulator3d/pruefnaechte/*.json, Prüfstand 2).
    if not a.nur_verlauf and not a.ohne_extras:
        if glob.glob(os.path.join(WEGE, "schleichweg_*.json")) and "spielwege" not in a.plaene:
            a.plaene.append("spielwege")
        if glob.glob(os.path.join(NAECHTE, "*.json")) and "echtenaechte" not in a.plaene:
            a.plaene.append("echtenaechte")
    a.kameras = [0] if a.kameras == "kopf" else [0, 1]
    if a.nur_verlauf:
        verlauf_schreiben()
        log("VERLAUF.md geschrieben")
        return 0
    rc, info = run(a)
    if info:
        zeilen, schlechter = vergleich(info)
        for z in zeilen:
            log(z, wichtig=True)
        tab = verlauf_schreiben()
        warn = os.path.join(REPO, "pruefstand", "WARNUNG.md")          # 2.98.9: a worse detection is reported (GitHub issue)
        if schlechter:
            with open(warn, "w", encoding="utf-8") as f:
                f.write("Die Erkennung ist mit MoveEye %s schlechter geworden (Prüfstand %s, %s):\n\n" % (
                    info["mw_version"], info.get("datum", "?"), info.get("rechner", "?")) + "\n".join("- " + z for z in zeilen)
                        + "\n\nEinzelheiten: pruefstand/VERLAUF.md\n")
        elif os.path.exists(warn):
            os.remove(warn)
        summ = os.environ.get("GITHUB_STEP_SUMMARY")
        if summ:                                                  # the page of the run on GitHub
            with open(summ, "a", encoding="utf-8") as f:
                f.write("## Prüfstand Motion Watch %s\n\n" % info["mw_version"] + "\n".join("- " + z for z in zeilen) + "\n\n" + tab.split("## Einzelheiten")[0])
        if a.streng and schlechter:
            return 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
