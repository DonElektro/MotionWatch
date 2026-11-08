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
  python3 werkzeuge/erkennungstest/erkennungstest.py … --variante bestaetigung2      # Einstellungen der Variante (siehe --liste)
  python3 werkzeuge/erkennungstest/erkennungstest.py --plan ursache --variante bestaetigung2 --trocken   # nur zeigen, nichts starten
  python3 werkzeuge/erkennungstest/bericht.py --varianten standard=A/results.jsonl bestaetigung2=B/results.jsonl   # nebeneinander

Auf dem Simulator-PC (HP, self-hosted Runner) läuft das über GitHub: Actions → «Erkennung (HP)» (werkzeuge/test_runner/).
Ergebnis im Ordner --aus: results.jsonl (ein Fall pro Zeile), ergebnis.json (Kennzahlen + Angaben), bericht.md, Protokolle,
Bilder. Mit demselben --aus fortsetzbar (gemessene Fälle werden übersprungen).

Stürzt der Simulator (oder MoveEye) ab, sichert der Test dessen Protokoll (simulator_absturz_N.log), startet ihn neu und rechnet
beim selben Fall weiter; stürzt er beim selben Fall zweimal ab, wird dieser Fall übersprungen (uebersprungen.jsonl, im Bericht).
Exit-Codes (Grund in fehler.txt im --aus-Ordner, das Dauerrechnen zeigt ihn im Job-Protokoll):
  0 fertig · 1 Abbruch (Signal) / unerwartet · 2 Simulator und MoveEye beim Start nicht verbunden ·
  3 zu viele Abstürze bzw. Neustart gescheitert · 7 Stand nicht brauchbar (MoveEye oder Simulator fehlt, MoveEye des Stands
  kennt die Start-Optionen nicht) - das Dauerrechnen versucht ihn nicht noch einmal
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
import fortschritt as FS    # noqa: E402

BASIS = "camping,wald,stellplatz"                                      # die 3 Orte × 4 Bedingungen von Test 1–3 (72 Fälle)
NEU = "festival:tag+nacht,garten:tag+nachtregen,baustelle:nacht,wild:tag+nacht,camping:dunkel"
ALLE_NEU = "festival,garten,wild,parkplatz,baustelle,camping:dunkel"
ORTE_BED = [(p, c) for p in ("camping", "wald", "stellplatz") for c in F.PLAN[p][1]] + [
    ("festival", "tag"), ("festival", "nacht"), ("garten", "tag"), ("garten", "nachtregen"), ("baustelle", "nacht"),
    ("wild", "tag"), ("wild", "nacht"), ("camping", "dunkel")]
NACHT = ("nacht", "nachtregen", "dunkel")
RC_START, RC_ABSTURZ, RC_STAND = 2, 3, 7
FEHLER_DATEI = "fehler.txt"
ABSTURZ_MAX = int(os.environ.get("MW_ERK_ABSTUERZE") or 8)    # so viele Abstürze pro Lauf, dann Schluss (Exit 3)
ABSTURZ_FALL = 2                                               # so oft beim selben Fall -> Fall übersprungen
EINGEWOEHNEN_S = float(os.environ.get("MW_ERK_EINGEWOEHNEN_S") or 30)
SIGNALE = {-11: "Speicherzugriffsfehler (SIGSEGV)", -6: "abgebrochen (SIGABRT)", -9: "abgeschossen (SIGKILL, Speicher voll?)",
           -7: "Busfehler (SIGBUS)", -15: "beendet (SIGTERM)", 139: "Speicherzugriffsfehler (SIGSEGV)", 134: "abgebrochen (SIGABRT)",
           137: "abgeschossen (SIGKILL, Speicher voll?)"}


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
    "alle": ("Alles: alle Orte und Bedingungen, Schlafzimmer, alle Sonderfälle, echte Situationen",
             [("orte", BASIS, {"leerwind": 55}), ("orte", ALLE_NEU, {"leerwind": 12}), ("orte", "schlafzimmer", {}),
              ("extra", "kopf,blend,linse,ruhig,nebenfunde,real")]),
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
    "real": ("Echte Situationen: nachts lange ums Zelt schleichen und stehlen, Velo-Diebstahl (Camping, Stellplatz; Soll: Person)",
             [("extra", "real")]),
    "ursache": ("Ursache: die 16 heiklen Fälle aus Erkennung 4 plus Tiere / Autos, mit Leerlauf",
                [("orte", BASIS, {"leerwind": 55, "sel": SEL_URSACHE, "sel_leer": True})]),
}

# Varianten (Paket «Fehlalarme und Pushes», 3.60): derselbe Plan mit anderen Einstellungen von MoveEye - so lassen sich ein
# Schalter an / aus vergleichen (Erkennung und Pushes pro Stunde nebeneinander: bericht.py --varianten, das Dauerrechnen
# schreibt varianten.md). Nur Schlüssel, die MoveEye kennt (ältere Stände übergehen unbekannte).
VARIANTEN = {
    "standard": ("Einstellungen ab Werk", {}),
    "bestaetigung2": ("Doppelte Bestätigung an (alarm_confirm2: Personen-Alarm nur, wenn KI und Wärmebild übereinstimmen oder "
                      "die KI zweimal nacheinander sieht)", {"alarm_confirm2": True}),
    "bestaetigung2_aus": ("Doppelte Bestätigung aus (Gegenprobe, falls sie einmal ab Werk an ist)", {"alarm_confirm2": False}),
    "windschutz_aus": ("Windschutz für Pflanzen-Bereiche aus (wind_guard, 639zy)", {"wind_guard": False}),
    # Flora Paket 4 B: dieselben Fälle mit den Tieren als Grundformen bzw. als Modelle mit Skelett (Simulator-Umgebung
    # MW_TIERE, SIM_UMGEBUNG unten); MoveEye-Einstellungen ab Werk. Das Dauerrechnen misst beide abwechselnd mehrmals.
    "tiere_grundformen": ("Simulator: Tiere als Grundformen (MW_TIERE=alt, Gegenstück zu tiere_modelle)", {}),
    "tiere_modelle": ("Simulator: Tiere als Modelle mit Skelett (MW_TIERE=modell, Flora Paket 3)", {}),
}
SIM_UMGEBUNG = {"tiere_grundformen": {"MW_TIERE": "alt"}, "tiere_modelle": {"MW_TIERE": "modell"}}


def variante_einstellungen(name):
    """(Name, Einstellungen) der Variante; unbekannt -> SystemExit"""
    n = (name or "standard").strip() or "standard"
    if n not in VARIANTEN:
        sys.exit("unbekannte Variante «%s» (%s)" % (n, ", ".join(VARIANTEN)))
    return n, dict(VARIANTEN[n][1])


def mw_einstellungen(sim_port, variante="standard", testbild=False):
    """die Einstellungen, mit denen MoveEye startet: leer, Simulation an, keine Updates, plus die der Variante"""
    st = {"sim_on": True, "source": "sim:0", "thermal_source": "sim:thermal", "sim_url": "http://127.0.0.1:%d" % sim_port,
          "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "",
          "lang": "de", "desktop_notice": False, "setup_done": True, "thermal_on": True}
    if testbild:
        st["show_hud"] = False                          # Testbild: Bild ohne Textleiste oben (nur Anzeige, ändert die Erkennung nicht)
    st.update(variante_einstellungen(variante)[1])
    return st


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

    def letzter(self, name):
        for n, pr in reversed(self.p):
            if n == name:
                return pr
        return None

    def laeuft(self, name):
        pr = self.letzter(name)
        return pr is not None and pr.poll() is None

    def code(self, name):
        """«läuft» | «Code -11 = Speicherzugriffsfehler (SIGSEGV)» | «nicht gestartet»"""
        pr = self.letzter(name)
        if pr is None:
            return "nicht gestartet"
        rc = pr.poll()
        if rc is None:
            return "läuft"
        return "Code %s%s" % (rc, (" = " + SIGNALE[rc]) if rc in SIGNALE else "")

    def stoppe(self, name):
        pr = self.letzter(name)
        if pr is not None and pr.poll() is None:
            try:
                os.killpg(pr.pid, signal.SIGTERM)
                pr.wait(10)
            except Exception:
                try:
                    os.killpg(pr.pid, signal.SIGKILL)
                except OSError:
                    pass

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


def letzte_zeilen(pfad, n=12):
    """die letzten n nicht leeren Zeilen eines Protokolls (für den Grund im Job-Protokoll)"""
    try:
        with open(pfad, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 64_000))
            z = [ln.rstrip() for ln in f.read().decode("utf-8", "replace").splitlines() if ln.strip()]
        return z[-n:]
    except OSError:
        return []


def fehler_schreiben(aus, text):
    try:
        with open(os.path.join(aus, FEHLER_DATEI), "w", encoding="utf-8") as f:
            f.write(text.strip()[:1500] + "\n")
    except OSError:
        pass


def plan_rechnen(schritte, schritt_rechnen, tote, neustart, log=print, nachsehen_s=6.0):
    """alle Schritte rechnen und Abstürze überstehen. schritt_rechnen(schritt) rechnet einen Schritt (überspringt Gemessenes);
    tote() -> [(Name, Code-Text)] der beendeten Programme; neustart(tote, n) -> "" (wieder verbunden) oder Grund.
    Stürzt etwas ab: neu starten und den Schritt wiederholen (beim selben Fall weiter); derselbe Fall ABSTURZ_FALL-mal ->
    übersprungen (F.ueberspringen); ABSTURZ_MAX Abstürze -> Schluss. -> (rc, Grund, [Schritt-Fehler])"""
    n_abst, pro_fall, fehler = 0, {}, []
    for schritt in schritte:
        while True:
            F.ST["fall"] = ""
            err = None
            try:
                schritt_rechnen(schritt)
            except SystemExit:
                raise
            except Exception as e:                      # ein Schritt bricht nicht den ganzen Test ab
                err = e
            t = tote()
            t_bis = time.time() + nachsehen_s
            while not t and err is not None and time.time() < t_bis:   # Verbindung weg: beendet er sich gerade?
                time.sleep(0.5)
                t = tote()
            if not t:
                if err is not None:
                    log("Schritt", schritt[:2], "Fehler:", repr(err))
                    fehler.append("%s: %r" % (schritt[1], err))
                break
            n_abst += 1
            fall = F.ST.get("fall") or ""
            was = ", ".join("%s %s" % x for x in t)
            log("ABSTURZ %d: %s%s" % (n_abst, was, (" - beim Fall " + fall) if fall else ""))
            if fall:
                pro_fall[fall] = pro_fall.get(fall, 0) + 1
                if pro_fall[fall] >= ABSTURZ_FALL:
                    F.ueberspringen(fall, "%d-mal abgestürzt (%s)" % (pro_fall[fall], was))
                    log("Fall", fall, "übersprungen (%d-mal abgestürzt)" % pro_fall[fall])
            if n_abst >= ABSTURZ_MAX:
                return RC_ABSTURZ, "%d-mal abgestürzt, zuletzt %s%s" % (n_abst, was, (" beim Fall " + fall) if fall else ""), fehler
            g = neustart(t, n_abst)
            if g:
                return RC_ABSTURZ, "Neustart nach Absturz (%s%s) gescheitert: %s" % (was, (" beim Fall " + fall) if fall else "", g), fehler
    return 0, "", fehler


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
    ap.add_argument("--fortschritt", default="", help="Fortschritt + Bild fürs Testbild des Kiosks (JSON, z. B. "
                    "/run/moveeye-test/fortschritt.json; daneben bild.png); leer = aus")
    ap.add_argument("--arbeit", default="", help="Name der Arbeit fürs Testbild (Dauerrechnen: «Erkennung messen»)")
    ap.add_argument("--variante", default="standard", help="Einstellungen von MoveEye: " + " | ".join(VARIANTEN) + " (siehe --liste)")
    ap.add_argument("--trocken", action="store_true", help="nur zeigen, was gerechnet würde (Plan, Variante, Einstellungen, Fälle)")
    ap.add_argument("--liste", action="store_true", help="nur die Pläne und Varianten zeigen")
    a = ap.parse_args()
    if a.liste:
        for k, (txt, _) in PLAENE.items():
            print("%-9s %s" % (k, txt))
        print("\nVarianten (--variante):")
        for k, (txt, st) in VARIANTEN.items():
            print("%-18s %s%s" % (k, txt, (" · " + json.dumps(st)) if st else ""))
        return 0
    plaene = [p.strip() for p in a.plan.split(",") if p.strip()]
    for p in plaene:
        if p not in PLAENE:
            sys.exit("unbekannter Plan «%s» (%s)" % (p, ", ".join(PLAENE)))
    a.variante, _vst = variante_einstellungen(a.variante)
    if a.trocken:
        print(json.dumps({"plan": ",".join(plaene), "variante": a.variante, "laeufe": max(1, min(5, a.laeufe)),
                          "faelle": FS.faelle_zaehlen(plaene, lambda p: PLAENE[p][1], max(1, min(5, a.laeufe))),
                          "einstellungen": mw_einstellungen(a.sim_port, a.variante)}, ensure_ascii=False, indent=1))
        return 0
    a.laeufe = max(1, min(5, a.laeufe))
    repo = os.path.abspath(a.repo)
    aus = os.path.abspath(a.aus or tempfile.mkdtemp(prefix="mw_erkennung_"))
    os.makedirs(aus, exist_ok=True)
    try:
        os.unlink(os.path.join(aus, FEHLER_DATEI))
    except OSError:
        pass

    def unbrauchbar(text):                              # Stand nicht brauchbar: Grund, Exit 7 (kein neuer Versuch)
        log("FEHLER:", text)
        fehler_schreiben(aus, text)
        return RC_STAND
    mw = os.path.abspath(a.mw) if a.mw else (neueste_mw(repo) if os.path.isdir(repo) else "")
    if not mw or not os.path.isfile(mw):
        return unbrauchbar("Stand %s nicht brauchbar: MoveEye (webcam_bewegung_X_Y_Z.py) fehlt in %s" % (a.stand or "?", repo))
    if not a.sim_bin and not a.godot:
        return unbrauchbar("Stand %s nicht brauchbar: Simulator fehlt (--sim-bin bzw. --godot; Paket "
                           "simulator3d/MoveEyeSim3D_Linux.zip im Stand?)" % (a.stand or "?"))
    if a.sim_bin and not (os.path.isfile(a.sim_bin) and os.access(a.sim_bin, os.X_OK)):
        return unbrauchbar("Stand %s nicht brauchbar: Simulator %s fehlt oder ist nicht ausführbar" % (a.stand or "?", a.sim_bin))
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
    lauf = {"plan": ",".join(plaene), "variante": a.variante, "laeufe": a.laeufe, "moveeye": mwver, "simulator": simver + (" (Godot)" if a.godot else ""),
            "stand": a.stand, "commit": a.commit, "rechner": a.rechner or ("%s, %d Kerne" % (cpu_modell(), os.cpu_count() or 0)),
            "anzeige": a.anzeige, "grafik": a.grafik, "ki": bool(a.ki_ordner), "start": time.strftime("%Y-%m-%d %H:%M:%S")}
    P = Prozesse()
    env = dict(os.environ)
    fehler = ""
    fs = None
    if a.fortschritt and os.path.isdir(os.path.dirname(os.path.abspath(a.fortschritt))):
        try:
            gesamt = FS.faelle_zaehlen(plaene, lambda p: PLAENE[p][1], a.laeufe)
            fs = FS.Fortschritt(os.path.abspath(a.fortschritt), lauf["plan"], " + ".join(PLAENE[p][0] for p in plaene)[:90],
                                gesamt, t_start, schon=FS.zeilen(os.path.join(aus, "results.jsonl")), arbeit=a.arbeit)
            log("Fortschritt fürs Testbild:", a.fortschritt, "·", gesamt, "Fälle")
        except Exception as e:                              # der Test geht vor
            log("Fortschritt aus:", repr(e))
            fs = None
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
        senv.update(SIM_UMGEBUNG.get(a.variante, {}))              # Flora Paket 4: Umgebung des Simulators je Variante
        if a.variante in SIM_UMGEBUNG:
            log("Simulator-Umgebung:", " ".join("%s=%s" % kv for kv in SIM_UMGEBUNG[a.variante].items()))
        os.makedirs(senv["HOME"], exist_ok=True)
        sargs = ["--no-update", "--stream", "--scene", "camping", "--hour", "12", "--port", str(a.sim_port), "--quality", "simple",
                 "--grafik", a.grafik, "--mini-tiny"]
        if a.sim_bin:
            scmd = [os.path.abspath(a.sim_bin), "--max-fps", a.max_fps, "--"] + sargs
        else:
            scmd = [a.godot, "--max-fps", a.max_fps, "--path", os.path.join(repo, "simulator3d"), "--"] + sargs
        log("Simulator:", os.path.basename(scmd[0]), simver)

        def sim_start():
            P.start("Simulator", scmd, senv, os.path.join(tmp, "simulator.log"))
        sim_start()
        # --- MoveEye: leere Einstellungen, Simulation an, keine Updates, keine automatische Simulator-Suche
        cfg = os.path.join(tmp, "mw")
        os.makedirs(cfg, exist_ok=True)
        st = mw_einstellungen(a.sim_port, a.variante, testbild=bool(fs))   # + die Einstellungen der Variante (--variante)
        if a.variante != "standard":
            log("Variante", a.variante, "–", VARIANTEN[a.variante][0])
        with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        if a.ki_ordner:
            os.makedirs(os.path.join(cfg, "models"), exist_ok=True)
            for fn in os.listdir(a.ki_ordner):
                shutil.copy(os.path.join(a.ki_ordner, fn), os.path.join(cfg, "models", fn))
        menv = dict(env, HOME=os.path.join(tmp, "mw_home"))
        os.makedirs(menv["HOME"], exist_ok=True)
        log("MoveEye:", os.path.basename(mw))

        def mw_start():
            P.start("MoveEye", [sys.executable, mw, "--headless", "--port", str(a.mw_port), "--bind", "127.0.0.1", "--config", cfg],
                    menv, os.path.join(tmp, "motionwatch.log"))
        mw_start()
        sim = "http://127.0.0.1:%d" % a.sim_port
        web = "http://127.0.0.1:%d" % a.mw_port
        protokolle = {"Simulator": "simulator.log", "MoveEye": "motionwatch.log", "Xvfb": "xvfb.log"}

        def verbunden(sek):
            """True, sobald MoveEye Bilder vom Simulator hat; False nach sek oder wenn eines beendet ist"""
            t_end = time.time() + sek
            while time.time() < t_end:
                if not P.laeuft("Simulator") or not P.laeuft("MoveEye"):
                    return False
                try:
                    s = http_json(web + "/api/state", timeout=4)["state"]
                    c = http_json(sim + "/control", {"action": "get"}, timeout=4)
                    if str(s.get("source_status", "")).startswith("connected") and float(s.get("fps") or 0) > 0 \
                            and "nicht verbunden" not in str(c.get("status", "")):
                        return True
                except Exception:
                    pass
                time.sleep(3)
            return False

        def ende_von(name):                             # die letzten Zeilen eines Protokolls (für den Grund)
            z = letzte_zeilen(os.path.join(tmp, protokolle[name]), 6)
            return (" · Ende %s: %s" % (protokolle[name], " | ".join(x[:160] for x in z))) if z else ""

        if not verbunden(a.start_zeit):
            sl, ml = P.code("Simulator"), P.code("MoveEye")
            mz = " ".join(letzte_zeilen(os.path.join(tmp, "motionwatch.log"), 40))
            if ml != "läuft" and re.search(r"unrecognized arguments|error: argument|usage: ", mz):
                fehler = "Stand %s nicht brauchbar: MoveEye %s kennt die Start-Optionen des Tests nicht (%s)%s" % (
                    a.stand or "?", mwver, ml, ende_von("MoveEye"))
                return unbrauchbar(fehler)
            fehler = "Simulator und MoveEye nicht verbunden nach %d s (Simulator: %s, MoveEye: %s)" % (a.start_zeit, sl, ml)
            fehler += ende_von("Simulator") if sl != "läuft" or ml == "läuft" else ""
            fehler += ende_von("MoveEye") if ml != "läuft" else ""
            log("FEHLER:", fehler)
            for name in ("Simulator", "MoveEye"):
                for ln in letzte_zeilen(os.path.join(tmp, protokolle[name]), 15):
                    log("  [%s] %s" % (protokolle[name], ln[:300]))
            fehler_schreiben(aus, fehler)
            return RC_START
        log("verbunden – %.0f s eingewöhnen" % EINGEWOEHNEN_S)
        time.sleep(EINGEWOEHNEN_S)
        F.konfig(sim=sim, mw=web, out=aus, shots=os.path.join(aus, "bilder"), variant=lauf["plan"] + ("" if a.variante == "standard" else "@" + a.variante), fpsmin=a.fpsmin,
                 fpswait=a.fpswait, laeufe=a.laeufe)
        if fs:
            FS.einhaengen(fs)
            fs.setze(status="laeuft")
            fs.bild_faden(web)

        def schritt_rechnen(schritt):
            done = F.done_keys()
            if schritt[0] == "orte":
                o = dict(schritt[2])
                F.orte(schritt[1], done, rep=a.laeufe, leerwind=o.get("leerwind", 55), sel=o.get("sel"),
                       sel_leer=o.get("sel_leer", False), blindmap=a.blindmap)
            else:
                for w in schritt[1].split(","):
                    F.EXTRAS[w](done)

        def tote():
            return [(n, P.code(n)) for n in ("Xvfb", "Simulator", "MoveEye") if P.letzter(n) is not None and not P.laeuft(n)]

        def neustart(t, n):
            """Protokolle sichern (<name>_absturz_N.log, ins Artefakt), Beendetes neu starten, wieder verbinden"""
            namen = [x[0] for x in t]
            for name in namen:
                q = os.path.join(tmp, protokolle[name])
                ende_protokoll(q, os.path.join(aus, protokolle[name].replace(".log", "_absturz_%d.log" % n)), 500_000)
                for ln in letzte_zeilen(q, 12):
                    log("  [%s] %s" % (protokolle[name], ln[:300]))
            if "Xvfb" in namen:
                return "Xvfb beendet (virtueller Bildschirm)"
            if "Simulator" in namen:
                log("Simulator neu starten")
                sim_start()
            if "MoveEye" in namen:
                log("MoveEye neu starten")
                mw_start()
            if not verbunden(a.start_zeit):
                if P.laeuft("Simulator") and P.laeuft("MoveEye") and "MoveEye" not in namen:
                    log("MoveEye verbindet nicht wieder - MoveEye auch neu starten")
                    P.stoppe("MoveEye")
                    mw_start()
                    if verbunden(a.start_zeit):
                        time.sleep(EINGEWOEHNEN_S)
                        return ""
                return "nicht wieder verbunden (Simulator: %s, MoveEye: %s)%s" % (P.code("Simulator"), P.code("MoveEye"),
                                                                                  ende_von("Simulator"))
            log("wieder verbunden – %.0f s eingewöhnen, weiter beim selben Fall" % EINGEWOEHNEN_S)
            time.sleep(EINGEWOEHNEN_S)
            return ""

        schritte = []
        for p in plaene:
            schritte += PLAENE[p][1]
        log("Plan", lauf["plan"], "–", " + ".join(PLAENE[p][0] for p in plaene)[:200])
        rc, grund, sfehler = plan_rechnen(schritte, schritt_rechnen, tote, neustart, log)
        if sfehler:
            fehler = "; ".join(sfehler)
        if rc:
            fehler = (fehler + "; " if fehler else "") + grund
            log("FEHLER:", grund)
            fehler_schreiben(aus, grund + ende_von("Simulator"))
            return rc
        log("fertig")
        return 0
    except SystemExit as e:
        if e.code not in (None, 0) and not isinstance(e.code, int):
            fehler = str(e.code)
        raise
    finally:
        if fs:
            fs.fertig("fertig" if not fehler else "fehler")
        P.stop()
        lauf["dauer_min"] = round((time.time() - t_start) / 60.0)
        if fehler:
            lauf["fehler"] = fehler
            lauf["hinweis"] = (lauf.get("hinweis", "") + " · " if lauf.get("hinweis") else "") + "Fehler: " + fehler
        try:
            ueb = F.uebersprungene(aus)
        except Exception:
            ueb = []
        if ueb:
            lauf["uebersprungen"] = ueb
            lauf["hinweis"] = (lauf.get("hinweis", "") + " · " if lauf.get("hinweis") else "") + \
                "Übersprungen (Simulator / MoveEye stürzt dort immer ab): " + ", ".join(u.get("key", "?") for u in ueb)
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
