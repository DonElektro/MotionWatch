#!/usr/bin/env python3
"""Erkennungstest: MoveEye gegen den 3D-Simulator, Fall für Fall – Personen gehen, kriechen (dunkle Kleidung), Kinder, Tiere,
Autos und Leerlauf an mehreren Orten (Camping, Bergtal, Ferienpark, Zuhause, Festival) bei Tag, Dämmerung, Nacht mit
Infrarot, Regen, Nebel, Schnee und Nacht ohne Licht. Ergänzt den Prüfstand (pruefstand/): dort feste Testläufe mit vielen
Besuchern, hier einzelne Fälle mit Ursache («als Tier gemeldet», «nur Bewegung» …).

Startet selbst: Xvfb (ohne Bildschirm), den Simulator (Export oder Godot 4.3), MoveEye mit leeren Einstellungen (Simulation an,
keine Updates, Test-Postfach), wartet auf die Verbindung und rechnet dann den Plan.

  python3 werkzeuge/erkennungstest/erkennungstest.py --sim-bin /pfad/MoveEyeSim3D.x86_64 --plan kurz
  python3 werkzeuge/erkennungstest/erkennungstest.py --godot /pfad/Godot_v4.3-stable_linux.x86_64 --plan test3 --laeufe 2
  python3 werkzeuge/erkennungstest/bericht.py ERGEBNIS/results.jsonl --vergleich ALT/results.jsonl

Auf dem Simulator-PC (HP, self-hosted Runner) läuft das über GitHub: Actions → «Erkennung (HP)» (werkzeuge/test_runner/).
Ergebnis im Ordner --aus: results.jsonl (ein Fall pro Zeile), ergebnis.json (Kennzahlen + Angaben), bericht.md, Protokolle,
Bilder. Mit demselben --aus fortsetzbar (gemessene Fälle werden übersprungen).
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import faelle as F          # noqa: E402
import bericht as B         # noqa: E402

BASIS = "camping,wald,stellplatz"                                      # die 3 Orte × 4 Bedingungen von Test 1–3 (72 Fälle)
NEU = "festival:tag+nacht,garten:tag+nachtregen,baustelle:nacht,wild:tag+nacht,camping:dunkel"
ALLE_NEU = "festival,garten,wild,parkplatz,baustelle,camping:dunkel"
ORTE_BED = [(p, c) for p in ("camping", "wald", "stellplatz") for c in F.PLAN[p][1]] + [
    ("festival", "tag"), ("festival", "nacht"), ("garten", "tag"), ("garten", "nachtregen"), ("baustelle", "nacht"),
    ("wild", "tag"), ("wild", "nacht"), ("camping", "dunkel")]
NACHT = ("nacht", "nachtregen", "dunkel")


def _sel(events, conds=None):
    return {"%s|%s|%s" % (p, c, e) for p, c in ORTE_BED for e in events if conds is None or c in conds}


# Ursache (Erkennung 4): 16 Fälle, die zwischen zwei Fassungen verloren gingen, plus Tiere / Autos als Gegenprobe
SEL_URSACHE = set("""camping|tag|gehen camping|tag|kind camping|daemmerung|kind camping|nacht|gehen camping|regen|gehen camping|regen|kind
wald|tag|gehen wald|tag|kriechen wald|tag|kind wald|daemmerung|kriechen wald|daemmerung|kind
stellplatz|tag|kriechen stellplatz|daemmerung|kind stellplatz|schnee|kriechen
camping|tag|fahrzeug camping|daemmerung|tier camping|daemmerung|fahrzeug wald|tag|tier wald|nacht|tier stellplatz|nacht|tier
camping|tag|kriechen camping|nacht|kind""".split())

# Plan -> Schritte: ("orte", Orte, Optionen) | ("extra", "blend,kopf…")
PLAENE = {
    "kurz": ("Kurzprobe: Camping, Tag – Leerlauf, Person geht, Tier (etwa 5 Min.; zum Prüfen des Runners)",
             [("orte", "camping:tag", {"leerwind": 12, "sel": {"camping|tag|leer", "camping|tag|gehen", "camping|tag|tier"}})]),
    "test3": ("Test 3: 3 Orte × 4 Bedingungen × 6 Fälle, dazu neue Orte, Schlafzimmer, Kopf-Verfolgung, Blendung",
              [("orte", BASIS, {"leerwind": 55}), ("orte", NEU, {"leerwind": 12}), ("orte", "schlafzimmer", {}),
               ("extra", "kopf,blend")]),
    "alle": ("Alles: alle Orte und Bedingungen, Schlafzimmer, alle Sonderfälle",
             [("orte", BASIS, {"leerwind": 55}), ("orte", ALLE_NEU, {"leerwind": 12}), ("orte", "schlafzimmer", {}),
              ("extra", "kopf,blend,linse,ruhig,nebenfunde")]),
    "wind": ("Wind: Leerlauf an allen Orten (alte Orte mit Sturm 55 km/h), Spinnennetz und Vogel vor der Linse, Gegenprobe ohne Sturm",
             [("orte", BASIS, {"leerwind": 55, "sel": _sel(["leer"])}), ("orte", NEU, {"leerwind": 12, "sel": _sel(["leer"])}),
              ("extra", "linse,ruhig")]),
    "tier": ("Tiere und Autos: als Person gemeldet? (alle Orte), Schlafzimmer, Scheinwerfer",
             [("orte", BASIS, {"leerwind": 55, "sel": _sel(["tier", "fahrzeug"])}),
              ("orte", NEU, {"leerwind": 12, "sel": _sel(["tier", "fahrzeug"])}), ("orte", "schlafzimmer", {}), ("extra", "nebenfunde")]),
    "kriechen": ("Kriechen (dunkle Kleidung) und Tiere an allen Orten, mit Leerlauf",
                 [("orte", BASIS, {"leerwind": 55, "sel": _sel(["kriechen", "tier"]), "sel_leer": True}),
                  ("orte", NEU, {"leerwind": 12, "sel": _sel(["kriechen", "tier"]), "sel_leer": True})]),
    "nacht": ("Nacht: alle Fälle bei Nacht (Infrarot, Regen, ohne Licht), mit Leerlauf",
              [("orte", BASIS, {"leerwind": 55, "sel": _sel(F.EVENTS[1:], NACHT), "sel_leer": True}),
               ("orte", NEU, {"leerwind": 12, "sel": _sel(F.EVENTS[1:], NACHT), "sel_leer": True})]),
    "ursache": ("Ursache: die 16 heiklen Fälle aus Erkennung 4 plus Tiere / Autos, mit Leerlauf",
                [("orte", BASIS, {"leerwind": 55, "sel": SEL_URSACHE, "sel_leer": True})]),
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def http_json(url, data=None, timeout=6.0):
    return F.http_json(url, data, timeout)


class Prozesse:
    """startet die Programme und beendet sie am Schluss wieder (auch bei Abbruch)"""

    def __init__(self):
        self.p = []

    def start(self, name, cmd, env=None, log_file=None):
        out = open(log_file, "w") if log_file else subprocess.DEVNULL
        pr = subprocess.Popen(cmd, env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        self.p.append((name, pr))
        return pr

    def laeuft(self, name):
        return any(n == name and pr.poll() is None for n, pr in self.p)

    def stop(self):
        for name, pr in reversed(self.p):
            if pr.poll() is None:
                try:
                    os.killpg(pr.pid, signal.SIGTERM)
                except OSError:
                    pass
        t = time.time() + 8
        for name, pr in self.p:
            while pr.poll() is None and time.time() < t:
                time.sleep(0.2)
            if pr.poll() is None:
                try:
                    os.killpg(pr.pid, signal.SIGKILL)
                except OSError:
                    pass


def neueste_mw(repo):
    def vkey(f):
        return [int(x) for x in re.findall(r"\d+", f)]
    fs = [f for f in os.listdir(repo) if re.match(r"webcam_bewegung_\d+_\d+_\d+\.py$", f)]
    return os.path.join(repo, sorted(fs, key=vkey)[-1]) if fs else ""


def freies_display():
    for n in range(140, 200):
        if not os.path.exists("/tmp/.X11-unix/X%d" % n) and not os.path.exists("/tmp/.X%d-lock" % n):
            return ":%d" % n
    return ":%d" % (140 + os.getpid() % 50)


def bildschirm_ok(disp):
    if not shutil.which("xset"):
        return False
    try:
        return subprocess.run(["xset", "-display", disp, "q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=10).returncode == 0
    except Exception:
        return False


def cpu_modell():
    try:
        for ln in open("/proc/cpuinfo"):
            if ln.startswith("model name"):
                return ln.split(":", 1)[1].strip()
    except Exception:
        pass
    return ""


def ende_protokoll(pfad, ziel, max_bytes=2_000_000):
    """die letzten max_bytes eines Protokolls in den Ergebnis-Ordner"""
    try:
        with open(pfad, "rb") as f:
            f.seek(0, 2)
            n = f.tell()
            f.seek(max(0, n - max_bytes))
            data = f.read()
        with open(ziel, "wb") as g:
            g.write(data)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="Erkennungstest: MoveEye gegen den 3D-Simulator, Fall für Fall")
    ap.add_argument("--plan", default="kurz", help="|".join(PLAENE) + " (mehrere mit Komma)")
    ap.add_argument("--laeufe", type=int, default=1, help="Personenfälle so oft (1–5; der Simulator wählt die Richtung neu)")
    ap.add_argument("--repo", default=os.path.normpath(os.path.join(HIER, "..", "..")), help="Repository-Stand (MoveEye + simulator3d)")
    ap.add_argument("--mw", default="", help="MoveEye-Datei (Standard: die neuste webcam_bewegung_*.py im --repo)")
    ap.add_argument("--sim-bin", default="", help="exportierter Simulator (MoveEyeSim3D.x86_64, z. B. aus simulator3d/MoveEyeSim3D_Linux.zip)")
    ap.add_argument("--godot", default="", help="Godot 4.3 (startet --repo/simulator3d direkt)")
    ap.add_argument("--ki-ordner", default="", help="KI-Modell (frozen_inference_graph.pb + .pbtxt); ohne: nur Bewegung und Gehmuster")
    ap.add_argument("--aus", default="", help="Ergebnis-Ordner (Standard: neuer Ordner unter /tmp)")
    ap.add_argument("--anzeige", default="xvfb", help="xvfb (eigener virtueller Bildschirm) oder ein X-Display wie :0 (Grafikkarte)")
    ap.add_argument("--grafik", default="lite", help="Grafik des Simulators (--grafik): lite, normal, auto")
    ap.add_argument("--max-fps", default="8", help="Bilder/s des Simulators (spart Rechenzeit)")
    ap.add_argument("--sim-port", type=int, default=8796)
    ap.add_argument("--mw-port", type=int, default=5096)
    ap.add_argument("--fpsmin", type=float, default=2.4, help="vor jedem Fall warten, bis MoveEye so viele Bilder/s hat")
    ap.add_argument("--fpswait", type=float, default=180, help="… höchstens so lange (s)")
    ap.add_argument("--blindmap", action="store_true", help="auch die blinden Flecken messen (Tag / Nacht, dauert)")
    ap.add_argument("--start-zeit", type=int, default=300, help="so lange auf die Verbindung Simulator ↔ MoveEye warten (s)")
    ap.add_argument("--rechner", default="", help="Name des Rechners im Bericht")
    ap.add_argument("--stand", default="", help="Zweig / Stand (nur für den Bericht)")
    ap.add_argument("--commit", default="", help="Commit (nur für den Bericht)")
    ap.add_argument("--liste", action="store_true", help="nur die Pläne zeigen")
    a = ap.parse_args()
    if a.liste:
        for k, (txt, _) in PLAENE.items():
            print("%-9s %s" % (k, txt))
        return 0
    plaene = [p.strip() for p in a.plan.split(",") if p.strip()]
    for p in plaene:
        if p not in PLAENE:
            sys.exit("unbekannter Plan «%s» (%s)" % (p, ", ".join(PLAENE)))
    a.laeufe = max(1, min(5, a.laeufe))
    repo = os.path.abspath(a.repo)
    mw = os.path.abspath(a.mw) if a.mw else neueste_mw(repo)
    if not mw or not os.path.isfile(mw):
        sys.exit("MoveEye nicht gefunden (--mw oder --repo)")
    if not a.sim_bin and not a.godot:
        sys.exit("Simulator fehlt: --sim-bin (Export) oder --godot (Godot 4.3)")
    aus = os.path.abspath(a.aus or tempfile.mkdtemp(prefix="mw_erkennung_"))
    os.makedirs(aus, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="mw_erk_lauf_")
    t_start = time.time()

    def _stop(sig, frm):
        raise SystemExit("abgebrochen (Signal %d)" % sig)
    signal.signal(signal.SIGTERM, _stop)

    try:
        simver = json.load(open(os.path.join(repo, "simulator3d", "version.json"))).get("ver", "")
    except Exception:
        simver = ""
    mwver = ".".join(re.findall(r"\d+", os.path.basename(mw))) or os.path.basename(mw)
    lauf = {"plan": ",".join(plaene), "laeufe": a.laeufe, "moveeye": mwver, "simulator": simver + (" (Godot)" if a.godot else ""),
            "stand": a.stand, "commit": a.commit, "rechner": a.rechner or ("%s, %d Kerne" % (cpu_modell(), os.cpu_count() or 0)),
            "anzeige": a.anzeige, "grafik": a.grafik, "ki": bool(a.ki_ordner), "start": time.strftime("%Y-%m-%d %H:%M:%S")}
    P = Prozesse()
    env = dict(os.environ)
    fehler = ""
    try:
        # --- Bildschirm: eigener Xvfb, oder ein vorhandenes Display (Grafikkarte), sonst doch Xvfb
        disp = ""
        if a.anzeige not in ("", "xvfb"):
            if bildschirm_ok(a.anzeige):
                disp = a.anzeige
                log("Bildschirm", disp, "(Grafikkarte)")
            else:
                log("Display", a.anzeige, "nicht erreichbar (Freigabe fehlt?) – nehme Xvfb")
                lauf["hinweis"] = "Display %s nicht erreichbar – mit Xvfb gerechnet" % a.anzeige
        if not disp:
            if not shutil.which("Xvfb"):
                sys.exit("Xvfb fehlt (sudo apt install xvfb)")
            disp = freies_display()
            P.start("Xvfb", ["Xvfb", disp, "-screen", "0", "1280x720x24", "-nolisten", "tcp"], log_file=os.path.join(tmp, "xvfb.log"))
            time.sleep(2)
            lauf["anzeige"] = "xvfb"
        env["DISPLAY"] = disp
        # --- Simulator: eigener HOME (Einstellungen und Berichte mischen sich nicht mit dem Kiosk)
        senv = dict(env, HOME=os.path.join(tmp, "sim_home"))
        os.makedirs(senv["HOME"], exist_ok=True)
        sargs = ["--no-update", "--stream", "--scene", "camping", "--hour", "12", "--port", str(a.sim_port), "--quality", "simple",
                 "--grafik", a.grafik, "--mini-tiny"]
        if a.sim_bin:
            cmd = [os.path.abspath(a.sim_bin), "--max-fps", a.max_fps, "--"] + sargs
        else:
            cmd = [a.godot, "--max-fps", a.max_fps, "--path", os.path.join(repo, "simulator3d"), "--"] + sargs
        log("Simulator:", os.path.basename(cmd[0]), simver)
        P.start("Simulator", cmd, senv, os.path.join(tmp, "simulator.log"))
        # --- MoveEye: leere Einstellungen, Simulation an, keine Updates, keine automatische Simulator-Suche
        cfg = os.path.join(tmp, "mw")
        os.makedirs(cfg, exist_ok=True)
        st = {"sim_on": True, "source": "sim:0", "thermal_source": "sim:thermal", "sim_url": "http://127.0.0.1:%d" % a.sim_port,
              "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "",
              "lang": "de", "desktop_notice": False, "setup_done": True, "thermal_on": True}
        with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        if a.ki_ordner:
            os.makedirs(os.path.join(cfg, "models"), exist_ok=True)
            for fn in os.listdir(a.ki_ordner):
                shutil.copy(os.path.join(a.ki_ordner, fn), os.path.join(cfg, "models", fn))
        menv = dict(env, HOME=os.path.join(tmp, "mw_home"))
        os.makedirs(menv["HOME"], exist_ok=True)
        log("MoveEye:", os.path.basename(mw))
        P.start("MoveEye", [sys.executable, mw, "--headless", "--port", str(a.mw_port), "--bind", "127.0.0.1", "--config", cfg],
                menv, os.path.join(tmp, "motionwatch.log"))
        sim = "http://127.0.0.1:%d" % a.sim_port
        web = "http://127.0.0.1:%d" % a.mw_port
        t_end = time.time() + a.start_zeit
        ok = False
        while time.time() < t_end:
            if not P.laeuft("Simulator") or not P.laeuft("MoveEye"):
                break
            try:
                s = http_json(web + "/api/state", timeout=4)["state"]
                c = http_json(sim + "/control", {"action": "get"}, timeout=4)
                if str(s.get("source_status", "")).startswith("connected") and float(s.get("fps") or 0) > 0 \
                        and "nicht verbunden" not in str(c.get("status", "")):
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(3)
        if not ok:
            fehler = "Simulator und MoveEye nicht verbunden nach %d s (Simulator läuft: %s, MoveEye läuft: %s)" % (
                a.start_zeit, P.laeuft("Simulator"), P.laeuft("MoveEye"))
            log("FEHLER:", fehler)
            return 2
        log("verbunden – 30 s eingewöhnen")
        time.sleep(30)
        F.konfig(sim=sim, mw=web, out=aus, shots=os.path.join(aus, "bilder"), variant=lauf["plan"], fpsmin=a.fpsmin,
                 fpswait=a.fpswait)
        for p in plaene:
            log("Plan", p, "–", PLAENE[p][0])
            for schritt in PLAENE[p][1]:
                done = F.done_keys()
                try:
                    if schritt[0] == "orte":
                        o = dict(schritt[2])
                        F.orte(schritt[1], done, rep=a.laeufe, leerwind=o.get("leerwind", 55), sel=o.get("sel"),
                               sel_leer=o.get("sel_leer", False), blindmap=a.blindmap)
                    else:
                        for w in schritt[1].split(","):
                            F.EXTRAS[w](done)
                except SystemExit:
                    raise
                except Exception as e:                      # ein Schritt bricht nicht den ganzen Test ab
                    log("Schritt", schritt[:2], "Fehler:", repr(e))
                    fehler = (fehler + "; " if fehler else "") + "%s: %r" % (schritt[1], e)
                if not P.laeuft("Simulator") or not P.laeuft("MoveEye"):
                    fehler = (fehler + "; " if fehler else "") + "Simulator oder MoveEye beendet"
                    log("FEHLER: Simulator oder MoveEye läuft nicht mehr")
                    return 3
        log("fertig")
        return 0
    except SystemExit as e:
        if e.code not in (None, 0) and not isinstance(e.code, int):
            fehler = str(e.code)
        raise
    finally:
        P.stop()
        lauf["dauer_min"] = round((time.time() - t_start) / 60.0)
        if fehler:
            lauf["fehler"] = fehler
            lauf["hinweis"] = (lauf.get("hinweis", "") + " · " if lauf.get("hinweis") else "") + "Fehler: " + fehler
        for fn in ("simulator.log", "motionwatch.log", "xvfb.log"):
            ende_protokoll(os.path.join(tmp, fn), os.path.join(aus, fn))
        R = B.lesen(os.path.join(aus, "results.jsonl"))
        with open(os.path.join(aus, "ergebnis.json"), "w", encoding="utf-8") as f:
            json.dump({"lauf": lauf, "kennzahlen": B.kennzahlen(R)}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(aus, "bericht.md"), "w", encoding="utf-8") as f:
            f.write(B.markdown(R, lauf))
        shutil.rmtree(tmp, ignore_errors=True)
        log("Ergebnis:", aus)


if __name__ == "__main__":
    sys.exit(main())
