#!/usr/bin/env python3
"""MoveEye Dauerrechnen (3.55.0) - der Simulator-PC (HP, Test-Runner «moveeye-hp») rechnet rund um die Uhr, solange niemand
spielt. Läuft als Benutzer des Runners (mwrunner) in den Workflows .github/workflows/dauer_hp.yml und erkennung_hp.yml.

  dauer.py waehlen --kandidaten JSON [--arbeit auto|erkennung|ki|langzeit] [--ausgabe $GITHUB_OUTPUT]
      nächstes Arbeitspaket: zuerst ein angefangenes, sonst reihum (1) Erkennung messen (Stände vergleichen, 3 Läufe pro
      Fall), (2) KI-Trainingsbilder aus dem Simulator, (3) Langzeittest. «nichts», wenn gespielt wird, alles erledigt ist
      oder das HP-Update an der Reihe ist (seit 20 Std. nicht mehr geprüft: dann bleibt der HP frei, bis es gelaufen ist).
  dauer.py rechnen --paket ID --stand DIR --sim-bin BIN [--ki-ordner K] [--stunden 3] [--anzeige xvfb] [--ausgabe …]
      das Paket rechnen, bis es fertig ist, die Zeit um ist oder jemand spielt. Stand gesichert wird pro Fall (Erkennung:
      results.jsonl), pro Bildpaket (KI) bzw. pro Minute (Langzeittest) - ein Neustart rechnet genau dort weiter.
  dauer.py halten [--warten-max S] -- BEFEHL …
      einen Test betreuen (Erkennung (HP) von Hand): spielt jemand, den Test anhalten (SIGTERM, er sichert selbst), den
      Bildschirm freigeben, warten, bis 15 Min. lang niemand mehr spielt, Bildschirm wieder nehmen und den Test mit
      demselben Ergebnis-Ordner neu starten (er überspringt, was schon gemessen ist).
  dauer.py status     Zustand zeigen (angefangenes Paket, erledigte Messungen)

Spielen erkennt die Kiosk-Sitzung (simulator3d/beilagen_linux/hp_wache.py, testbild.py): Datei MW_SPIEL
(/run/moveeye-spiel/spielen), ihr Änderungsdatum ist die letzte Aktivität; älter als 15 Min. = niemand spielt mehr.
Sie gilt nur als Daten (normale Datei, keine Verknüpfung; nur das Datum zählt). Der Bildschirm gehört dem Test, solange die
Pause-Datei MW_KIOSK_PAUSE da ist (job_start.sh legt sie an, job_ende.sh nimmt sie weg; dieses Skript nimmt sie beim
Spielen weg und legt sie danach wieder an). Test-Simulator und Kiosk-Simulator laufen nie gleichzeitig (4 GB RAM).
Zustand: MW_RUNNER_HOME/dauer/zustand.json, Pakete in dauer/pakete/<ID>/ (die letzten 12 bleiben; Ergebnisse gehen als
Actions-Artefakt hinaus - nichts Geheimes, öffentliches Repository).
"""
import argparse
import http.client
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time

HIER = os.path.dirname(os.path.abspath(__file__))
ERK = os.path.normpath(os.path.join(HIER, "..", "erkennungstest"))
HOME = os.environ.get("MW_RUNNER_HOME") or os.path.expanduser("~")
DAUER = os.environ.get("MW_DAUER") or os.path.join(HOME, "dauer")
PAUSE = os.environ.get("MW_KIOSK_PAUSE") or "/run/moveeye-test/kiosk_pause"
SPIEL = os.environ.get("MW_SPIEL") or "/run/moveeye-spiel/spielen"
RUHE_S = int(os.environ.get("MW_SPIEL_RUHE_S") or 900)
HPU_STEMPEL = os.environ.get("MW_HPU_STEMPEL") or "/var/lib/moveeye-hp-update/letzter_lauf"
HPU_FAELLIG_S = 20 * 3600
TAKT = float(os.environ.get("MW_DAUER_TAKT") or 1.0)          # wie oft geschaut wird, ob jemand spielt (s)
ERSATZ = os.environ.get("MW_DAUER_ERSATZ") or ""              # nur für dauer_test.sh: Ersatz-Programm statt der echten Arbeit

ARTEN = ("erkennung", "ki", "langzeit")
NAMEN = {"erkennung": "Erkennung messen", "ki": "KI-Trainingsbilder", "langzeit": "Langzeittest"}
ERK_PLAENE = ("ursache", "kriechen", "nacht", "tier", "wind")  # reihum, je Plan alle Stände (so lassen sie sich vergleichen)
ERK_LAEUFE = 3
KI_PAKETE, KI_BILDER = 6, 150                                  # ein Paket = 6 × 150 Bilder (je Bildpaket gesichert)
KI_PRO_STAND = 2                                               # so viele Pakete pro MoveEye-Stand (main)
LZ_MINUTEN = 180                                               # ein Langzeittest: 3 Std. (in Abschnitten zu 30 Min.)
LZ_BEDINGUNGEN = ("nacht", "tag", "nachtregen", "daemmerung")
BEHALTEN = 12
NAME_RE = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[0-9]{8}-[0-9]{6}-(erkennung|ki|langzeit)$")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------ Spielen, Pause, HP-Update
def datei_alter(p):
    try:
        st = os.lstat(p)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    return max(0.0, time.time() - st.st_mtime)


def spielt():
    al = datei_alter(SPIEL)
    return al is not None and al < RUHE_S


def pause_nehmen(grund):
    """den Bildschirm für den Test nehmen (Kiosk-Simulator aus) und warten, bis der Kiosk-Simulator wirklich zu ist"""
    try:
        with open(PAUSE + ".neu", "w") as f:
            f.write("Dauerrechnen %s %s\n" % (grund[:40], time.strftime("%F %T")))
        os.chmod(PAUSE + ".neu", 0o644)
        os.replace(PAUSE + ".neu", PAUSE)
    except OSError as e:
        log("Hinweis: Pause-Datei nicht geschrieben (%s) - Kiosk läuft weiter" % (e.strerror or e))
        return
    t = time.time() + 60
    while kiosk_sim() and time.time() < t:
        time.sleep(1)
    if kiosk_sim():
        log("Hinweis: der Kiosk-Simulator läuft noch")


def pause_freigeben():
    for p in (PAUSE, os.path.join(os.path.dirname(PAUSE), "fortschritt.json")):
        try:
            os.unlink(p)
        except OSError:
            pass


def kiosk_sim():
    """läuft ein Simulator eines anderen Benutzers (der Kiosk)?"""
    me = os.getuid()
    try:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                if os.stat("/proc/" + pid).st_uid == me:
                    continue
                with open("/proc/%s/comm" % pid) as f:
                    if f.read().startswith("MoveEyeSim3D"):
                        return True
            except OSError:
                continue
    except OSError:
        pass
    return False


def update_faellig():
    """moveeye-hp-update seit HPU_FAELLIG_S nicht mehr gelaufen? (fehlt der Stempel ganz: nicht eingerichtet -> nein)"""
    al = datei_alter(HPU_STEMPEL)
    return al is not None and al > HPU_FAELLIG_S


def ausgabe(pfad, **kw):
    for k, v in kw.items():
        log("  %s=%s" % (k, v))
    if pfad:
        with open(pfad, "a") as f:
            for k, v in kw.items():
                f.write("%s=%s\n" % (k, str(v).replace("\n", " ")))


# ------------------------------------------------------------------ Zustand
def zustand_lesen():
    try:
        with open(os.path.join(DAUER, "zustand.json"), encoding="utf-8") as f:
            z = json.load(f)
        if isinstance(z, dict):
            z.setdefault("erledigt", {})
            z.setdefault("rotation", 0)
            return z
    except (OSError, ValueError):
        pass
    return {"v": 1, "aktiv": None, "rotation": 0, "erledigt": {}}


def zustand_schreiben(z):
    os.makedirs(DAUER, exist_ok=True)
    tmp = os.path.join(DAUER, "zustand.json.neu")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(z, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(DAUER, "zustand.json"))


def paket_ordner(pid):
    if not ID_RE.match(pid or ""):
        raise SystemExit("Paket-ID ungültig")
    return os.path.join(DAUER, "pakete", pid)


def aufraeumen(z):
    """nur die letzten BEHALTEN Paket-Ordner behalten (nur Ordner mit genau diesem Namensmuster, nie das angefangene)"""
    d = os.path.join(DAUER, "pakete")
    try:
        alle = sorted(n for n in os.listdir(d) if ID_RE.match(n))
    except OSError:
        return
    aktiv = (z.get("aktiv") or {}).get("id")
    for n in alle[:-BEHALTEN]:
        if n != aktiv:
            shutil.rmtree(os.path.join(d, n), ignore_errors=True)


def kandidaten_lesen(txt):
    """{"main": {"name", "sha"}, "vorher": {...}, "zweige": [{...}]} (von der Vorprüfung auf GitHub; nur Stände dieses Repositorys)"""
    try:
        k = json.loads(txt or "{}")
    except ValueError:
        raise SystemExit("Kandidaten: kein JSON")
    out = []
    for rolle, e in [("main", k.get("main")), ("vorher", k.get("vorher"))] + [("zweig", e) for e in (k.get("zweige") or [])[:4]]:
        if isinstance(e, dict) and SHA_RE.match(str(e.get("sha", ""))) and NAME_RE.match(str(e.get("name", ""))):
            if not any(x["sha"] == e["sha"] for x in out):
                out.append({"rolle": rolle, "name": e["name"], "sha": e["sha"]})
    if not out or out[0]["rolle"] != "main":
        raise SystemExit("Kandidaten: main fehlt")
    return out


def naechstes(z, kand, art, jetzt):
    """(art, Angaben) der nächsten Arbeit dieser Art oder None"""
    main = kand[0]
    if art == "erkennung":
        for plan in ERK_PLAENE:
            for k in kand:
                if "erkennung|%s|%s" % (k["sha"], plan) not in z["erledigt"]:
                    return {"art": art, "sha": k["sha"], "stand": k["name"], "plan": plan, "laeufe": ERK_LAEUFE}
        return None
    if art == "ki":
        n = sum(1 for key in z["erledigt"] if key.startswith("ki|%s|" % main["sha"]))
        if n < KI_PRO_STAND:
            return {"art": art, "sha": main["sha"], "stand": main["name"], "plan": "hoch", "laeufe": KI_PAKETE}
        return None
    if art == "langzeit":
        tag = time.strftime("%Y-%m-%d", time.localtime(jetzt))
        if not any(key.startswith("langzeit|") and key.endswith("|" + tag) for key in z["erledigt"]):
            return {"art": art, "sha": main["sha"], "stand": main["name"], "plan": "leer", "laeufe": LZ_MINUTEN}
        return None
    return None


def waehlen(a):
    jetzt = time.time()
    z = zustand_lesen()
    if spielt():
        ausgabe(a.ausgabe, art="nichts", grund="Am HP wird gespielt - Rechnen pausiert")
        return 0
    if update_faellig():
        ausgabe(a.ausgabe, art="nichts", grund="HP-Update ist an der Reihe (seit 20 Std. nicht geprüft) - der HP bleibt kurz frei")
        return 0
    kand = kandidaten_lesen(a.kandidaten)
    shas = {k["sha"] for k in kand}
    ak = z.get("aktiv")
    if ak and ak.get("art") in ARTEN and (a.arbeit in ("auto", ak["art"])):
        if ak.get("sha") in shas:
            ausgabe(a.ausgabe, art=ak["art"], grund="angefangenes Paket", paket=ak["id"], sha=ak["sha"], stand=ak["stand"],
                    plan=ak["plan"], laeufe=ak["laeufe"], name=NAMEN[ak["art"]])
            return 0
        log("Angefangenes Paket %s: Stand %s ist nicht mehr dabei - abgeschlossen (Teilergebnis bleibt)" % (ak["id"], ak.get("stand")))
        z["erledigt"][ak["key"]] = {"t": int(jetzt), "status": "abgebrochen (Stand nicht mehr aktuell)", "paket": ak["id"]}
        z["aktiv"] = None
    arten = list(ARTEN) if a.arbeit == "auto" else [a.arbeit]
    r0 = int(z.get("rotation", 0)) % len(ARTEN)
    if a.arbeit == "auto":
        arten = [ARTEN[(r0 + i) % len(ARTEN)] for i in range(len(ARTEN))]
    for art in arten:
        n = naechstes(z, kand, art, jetzt)
        if not n:
            continue
        pid = time.strftime("%Y%m%d-%H%M%S", time.localtime(jetzt)) + "-" + art
        key = {"erkennung": "erkennung|%s|%s" % (n["sha"], n["plan"]), "ki": "ki|%s|%s" % (n["sha"], pid),
               "langzeit": "langzeit|%s|%s" % (n["sha"], time.strftime("%Y-%m-%d", time.localtime(jetzt)))}[art]
        z["aktiv"] = dict(n, id=pid, key=key, start=int(jetzt), versuche=0, rechenzeit_s=0)
        if a.arbeit == "auto":
            z["rotation"] = (ARTEN.index(art) + 1) % len(ARTEN)
        os.makedirs(paket_ordner(pid), exist_ok=True)
        zustand_schreiben(z)
        aufraeumen(z)
        ausgabe(a.ausgabe, art=art, grund="neues Paket", paket=pid, sha=n["sha"], stand=n["stand"], plan=n["plan"],
                laeufe=n["laeufe"], name=NAMEN[art])
        return 0
    zustand_schreiben(z)
    ausgabe(a.ausgabe, art="nichts", grund="alles erledigt (bis main sich ändert bzw. bis morgen)")
    return 0


# ------------------------------------------------------------------ betreuen: Test laufen lassen, beim Spielen anhalten
class Kind:
    def __init__(self, cmd, env=None, log_datei=None):
        self.out = open(log_datei, "a") if log_datei else None
        self.p = subprocess.Popen(cmd, env=env, stdout=self.out, stderr=subprocess.STDOUT if self.out else None,
                                  start_new_session=True)

    def laeuft(self):
        return self.p.poll() is None

    def stoppen(self, warten=25):
        """SIGTERM an die ganze Gruppe (der Test beendet Simulator und MoveEye selbst und sichert), dann SIGKILL"""
        if self.p.poll() is None:
            try:
                os.killpg(self.p.pid, signal.SIGTERM)
            except OSError:
                pass
            t = time.time() + warten
            while self.p.poll() is None and time.time() < t:
                time.sleep(0.2)
        try:
            os.killpg(self.p.pid, signal.SIGKILL)           # auch was übrig blieb (Xvfb, Simulator)
        except OSError:
            pass
        self.p.wait()
        if self.out:
            self.out.close()
        return self.p.returncode


def betreuen(cmd, env=None, frist=None, warten_max=0, log_datei=None, grund="Test"):
    """-> ("fertig", rc) | ("gespielt", None) | ("zeit", None). Läuft in einer Schleife, bis der Befehl fertig ist."""
    while True:
        if spielt():
            pause_freigeben()
            if warten_max <= 0:
                return "gespielt", None
            log("Am HP wird gespielt - warte, bis 15 Min. lang niemand mehr spielt (höchstens %d Min.)" % (warten_max // 60))
            t_ende = time.time() + warten_max
            while spielt():
                if time.time() > t_ende:
                    return "gespielt", None
                if frist and time.time() > frist:
                    return "zeit", None
                time.sleep(TAKT * 5)
            log("Niemand spielt mehr - weiter, wo es stand")
        if frist and time.time() > frist:
            return "zeit", None
        if datei_alter(PAUSE) is None and os.path.isdir(os.path.dirname(PAUSE)):
            pause_nehmen(grund)
        k = Kind(cmd, env, log_datei)
        stopp = None
        while k.laeuft():
            if spielt():
                stopp = "gespielt"
            elif frist and time.time() > frist:
                stopp = "zeit"
            if stopp:
                log("Spielen gewünscht - Test wird angehalten und gesichert" if stopp == "gespielt" else "Zeit um - Stand wird gesichert")
                t0 = time.time()
                k.stoppen()
                log("angehalten nach %.1f s" % (time.time() - t0))
                if stopp == "gespielt":
                    pause_freigeben()
                break
            time.sleep(TAKT)
        if not stopp:
            return "fertig", k.p.wait()
        if stopp == "zeit":
            return "zeit", None
        if warten_max <= 0:
            return "gespielt", None
        # sonst: warten (oben) und neu starten


def halten(a):
    cmd = a.befehl[1:] if a.befehl and a.befehl[0] == "--" else a.befehl
    if not cmd:
        raise SystemExit("halten: Befehl fehlt")
    st, rc = betreuen(cmd, warten_max=a.warten_max, grund="Test")
    if st == "gespielt":
        log("Es wird zu lange gespielt - der Test hört hier auf (Stand ist gesichert)")
        return 0
    return rc or 0


# ------------------------------------------------------------------ rechnen
def erledigen(z, ak, status):
    z["erledigt"][ak["key"]] = {"t": int(time.time()), "status": status, "paket": ak["id"], "stand": ak.get("stand")}
    z["aktiv"] = None


def erk_vergleich(z, ak):
    """fertige Messung: Bericht mit Vergleich zu derselben Messung (gleicher Plan) des anderen Stands"""
    sys.path.insert(0, ERK)
    try:
        import bericht as B
    except ImportError:
        return
    o = paket_ordner(ak["id"])
    R = B.lesen(os.path.join(o, "results.jsonl"))
    for key, e in sorted(z["erledigt"].items(), key=lambda kv: -kv[1].get("t", 0)):
        p = key.split("|")
        if len(p) == 3 and p[0] == "erkennung" and p[2] == ak["plan"] and p[1] != ak["sha"] and e.get("paket"):
            alt = os.path.join(DAUER, "pakete", e["paket"], "results.jsonl")
            if os.path.exists(alt):
                with open(os.path.join(o, "vergleich.md"), "w", encoding="utf-8") as f:
                    f.write("# %s gegen %s (Plan %s, %d Läufe pro Fall)\n\n" % (ak["stand"], e.get("stand", p[1][:10]), ak["plan"], ak["laeufe"]))
                    f.write(B.markdown(R, {"plan": ak["plan"], "stand": ak["stand"], "commit": ak["sha"]}, B.lesen(alt)))
                log("Vergleich geschrieben: gegen", e.get("stand", p[1][:10]))
                return


def rechnen(a):
    z = zustand_lesen()
    ak = z.get("aktiv")
    if not ak or ak.get("id") != a.paket:
        raise SystemExit("Paket %s ist nicht das angefangene" % a.paket)
    o = paket_ordner(ak["id"])
    os.makedirs(o, exist_ok=True)
    t0 = time.time()
    frist = t0 + a.stunden * 3600
    fo = os.path.join(os.path.dirname(PAUSE), "fortschritt.json") if os.path.isdir(os.path.dirname(PAUSE)) else ""
    py = sys.executable
    art = ak["art"]
    if ERSATZ:
        cmd = [py, ERSATZ, "--art", art, "--aus", o]
    elif art == "erkennung":
        cmd = [py, os.path.join(ERK, "erkennungstest.py"), "--repo", a.stand, "--plan", ak["plan"], "--laeufe", str(ak["laeufe"]),
               "--sim-bin", a.sim_bin, "--anzeige", a.anzeige, "--grafik", "lite", "--aus", o,
               "--rechner", "HP EliteDesk 800 G1 (%d Kerne)" % (os.cpu_count() or 0), "--stand", ak["stand"], "--commit", ak["sha"],
               "--fortschritt", fo, "--arbeit", NAMEN[art]] + (["--ki-ordner", a.ki_ordner] if a.ki_ordner else [])
    else:
        cmd = [py, os.path.abspath(__file__), art + "-teil", "--repo", a.stand, "--sim-bin", a.sim_bin, "--aus", o,
               "--anzeige", a.anzeige, "--fortschritt", fo, "--menge", str(ak["laeufe"]), "--stand-name", ak["stand"]] + \
              (["--ki-ordner", a.ki_ordner] if a.ki_ordner else [])
    log("Paket %s: %s, Stand %s (%s), %s" % (ak["id"], NAMEN[art], ak["stand"], ak["sha"][:10], ak["plan"]))
    dlog = os.path.join(o, "dauer.log")
    try:
        os.unlink(os.path.join(o, FEHLER_DATEI))
    except OSError:
        pass
    try:
        log_ab = os.path.getsize(dlog)
    except OSError:
        log_ab = 0
    st, rc = betreuen(cmd, frist=frist, warten_max=0, log_datei=dlog, grund=NAMEN[art])
    z = zustand_lesen()
    ak = z.get("aktiv") or ak
    ak["rechenzeit_s"] = int(ak.get("rechenzeit_s", 0) + time.time() - t0)
    weiter = 0
    if st == "fertig" and rc == 0 and fertig_pruefen(art, o, ak):
        erledigen(z, ak, "fertig")
        if art == "erkennung":
            erk_vergleich(z, ak)
        log("Paket fertig")
        weiter = 1
    elif st == "fertig":
        ak["versuche"] = int(ak.get("versuche", 0)) + 1
        grund = fehler_melden(art, o, dlog, log_ab, rc)
        log("Paket nicht fertig (Code %s, Versuch %d): %s" % (rc, ak["versuche"], grund))
        if ak["versuche"] >= 3:
            erledigen(z, ak, "abgebrochen nach 3 Versuchen (Code %s: %s)" % (rc, grund[:200]))
            log("Drei Versuche ohne Erfolg - Paket abgeschlossen, das nächste kommt dran")
        else:
            z["aktiv"] = ak
        weiter = 1
    elif st == "zeit":
        z["aktiv"] = ak
        weiter = 1
        log("Zeit für diesen Lauf um - der nächste Lauf rechnet dort weiter")
    else:
        z["aktiv"] = ak
        log("Pausiert fürs Spielen - nach 15 Min. ohne Spielen geht es dort weiter (Zeitplan alle 30 Min.)")
    zustand_schreiben(z)
    if update_faellig():
        weiter = 0                                             # das HP-Update ist dran: der HP bleibt frei
    if weiter and st == "fertig" and rc != 0 and time.time() - t0 < 600:
        weiter = 0                                             # schnell gescheitert: nicht im Kreis neu starten (Zeitplan genügt)
    ausgabe(a.ausgabe, status=st, weiter=weiter, ordner=o, name=NAMEN[art])
    return 0


def fehler_melden(art, o, dlog, ab, rc):
    """warum ist das Paket nicht fertig? Grund aus fehler.txt (vom Teil geschrieben), sonst die letzte Fehlerzeile aus
    dauer.log; dazu das Ende von dauer.log (nur dieser Versuch) ins Job-Protokoll und eine ::error::-Zeile -> Grund"""
    grund = ""
    try:
        with open(os.path.join(o, FEHLER_DATEI), encoding="utf-8", errors="replace") as f:
            grund = " ".join(f.read().split())
    except OSError:
        pass
    zeilen = []
    try:
        with open(dlog, "rb") as f:
            f.seek(ab)
            zeilen = f.read()[-200_000:].decode("utf-8", "replace").splitlines()
    except OSError:
        pass
    if not grund:
        for ln in reversed(zeilen):
            t = ln.strip()
            if t and (re.match(r"^[A-Za-z_.]*(Error|Exception|Exit)\b", t) or "FEHLER" in t or "Fehler" in t):
                grund = t
                break
    if not grund:
        grund = ("rc %s ohne Meldung" % rc) if zeilen else "keine Ausgabe (dauer.log leer)"
    rest = [ln for ln in zeilen if ln.strip()][-40:]
    if rest:
        print("::group::Ende von dauer.log (%s, dieser Versuch)" % NAMEN.get(art, art), flush=True)
        for ln in rest:
            print("    " + ln[:400], flush=True)
        print("::endgroup::", flush=True)
    print("::error title=Dauerrechnen %s::%s (Code %s)" % (NAMEN.get(art, art), grund.replace("\n", " ")[:900], rc), flush=True)
    return grund


def fertig_pruefen(art, o, ak):
    if art == "erkennung":
        try:
            sys.path.insert(0, ERK)
            import erkennungstest as E
            import fortschritt as FS
            soll = FS.faelle_zaehlen([ak["plan"]], lambda p: E.PLAENE[p][1], ak["laeufe"])
        except Exception:
            return True
        return FS.zeilen(os.path.join(o, "results.jsonl")) >= soll * 0.9 or ERSATZ != ""
    if art == "ki":
        return len(ki_fertig(o)) >= ak["laeufe"]
    if art == "langzeit":
        return lz_minuten(o) >= ak["laeufe"] - 0.5
    return True


# ------------------------------------------------------------------ Teile: KI-Bilder und Langzeittest (eigene Prozesse)
class Bild(threading.Thread):
    """alle ~5 s ein Bild für das Testbild (bild.png 960 px / bild_klein.png 640 px), wie fortschritt.py"""

    def __init__(self, url, ordner):
        super().__init__(daemon=True)
        self.url, self.ordner, self.an = url, ordner, True

    def run(self):
        try:
            import urllib.request
            import cv2
            import numpy as np
        except ImportError:
            return
        while self.an:
            try:
                with urllib.request.urlopen(self.url, timeout=6) as r:
                    roh = r.read(8_000_000)
                img = cv2.imdecode(np.frombuffer(roh, np.uint8), cv2.IMREAD_COLOR)
                if img is not None and img.size:
                    for name, b in (("bild.png", 960), ("bild_klein.png", 640)):
                        h, w = img.shape[:2]
                        k = cv2.resize(img, (b, max(1, round(h * b / w))), interpolation=cv2.INTER_AREA) if w > b else img
                        ok, buf = cv2.imencode(".png", k, [cv2.IMWRITE_PNG_COMPRESSION, 1])
                        if ok:
                            tmp = os.path.join(self.ordner, name + ".neu")
                            with open(tmp, "wb") as f:
                                f.write(buf.tobytes())
                            os.chmod(tmp, 0o644)
                            os.replace(tmp, os.path.join(self.ordner, name))
            except Exception:
                pass
            time.sleep(5)


def fortschritt(pfad, **d):
    if not pfad:
        return
    try:
        d["v"], d["t"] = 1, int(time.time())
        with open(pfad + ".neu", "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.chmod(pfad + ".neu", 0o644)
        os.replace(pfad + ".neu", pfad)
    except OSError:
        pass


def _angehalten(sig, frm):
    raise SystemExit("angehalten (Signal %d)" % sig)


def anzeige_starten(P, E, a, tmp):
    """Display für den Test-Simulator: der echte Bildschirm (wenn freigegeben und erreichbar), sonst ein eigenes Xvfb;
    «keine» nur für dauer_test.sh (Ersatz-Simulator ohne Fenster). -> (env, art) mit art "bildschirm" | "xvfb" | "keine" """
    import shutil as sh
    env = dict(os.environ)
    if a.anzeige == "keine":
        env.pop("DISPLAY", None)
        return env, "keine"
    if a.anzeige not in ("", "xvfb") and E.bildschirm_ok(a.anzeige):
        env["DISPLAY"] = a.anzeige
        return env, "bildschirm"
    if not sh.which("Xvfb"):
        raise TeilFehler(6, "Xvfb fehlt auf dem HP (sudo apt install xvfb, runner_einrichten.sh)")
    disp = E.freies_display()
    P.start("Xvfb", ["Xvfb", disp, "-screen", "0", "1280x720x24", "-nolisten", "tcp"], log_file=os.path.join(tmp, "xvfb.log"))
    time.sleep(2)
    env["DISPLAY"] = disp
    return env, "xvfb"


def start_sim(P, E, a, tmp, port, env=None, log_name="simulator.log"):
    """den Test-Simulator mit eigenem HOME starten (Display über anzeige_starten, beim Neustart dasselbe) -> (env, sim_home)"""
    if env is None:
        env, _ = anzeige_starten(P, E, a, tmp)
    home = os.path.join(tmp, "sim_home")
    os.makedirs(home, exist_ok=True)
    sargs = ["--no-update", "--stream", "--scene", "camping", "--hour", "12", "--port", str(port), "--quality", "simple"]
    if getattr(a, "grafik", ""):
        sargs += ["--grafik", a.grafik]
    P.start("Simulator", [os.path.abspath(a.sim_bin), "--max-fps", "8", "--"] + sargs, dict(env, HOME=home),
            os.path.join(tmp, log_name))
    return env, home


def warte_sim(F, P, sek=300):
    t = time.time() + sek
    while time.time() < t and P.laeuft("Simulator"):
        try:
            F.ctl(action="get")
            return True
        except Exception:
            time.sleep(3)
    return False


def ki_fertig(o):
    d = os.path.join(o, "pakete")
    try:
        return sorted(n for n in os.listdir(d) if re.match(r"^ki_\d{2}\.zip$", n))
    except OSError:
        return []


# Fehler der Teile: Code + klarer Text (fehler.txt im Paket-Ordner; rechnen zeigt ihn im Job-Protokoll als ::error::)
FEHLER_DATEI = "fehler.txt"
KI_ANTWORT_S = float(os.environ.get("MW_KI_ANTWORT_S") or 60)   # eine Anfrage an den Simulator darf so lange dauern
KI_STILL_S = float(os.environ.get("MW_KI_STILL_S") or 300)      # so lange darf er schweigen, solange er läuft (Szenenwechsel)
KI_NEUSTARTS = 2                                               # so oft hintereinander ohne gesicherte Bilder neu gestartet
KI_ABSTUERZE_MAX = 20                                          # und höchstens so viele Abstürze pro Lauf
KI_TEIL_MIN = int(os.environ.get("MW_KI_TEIL_MIN") or 10)      # so viele fertige Bilder retten ein abgebrochenes Bildpaket
SIGNALE = {-11: "Speicherzugriffsfehler (SIGSEGV)", -6: "abgebrochen (SIGABRT)", -9: "abgeschossen (SIGKILL, Speicher voll?)",
           -7: "Busfehler (SIGBUS)", 139: "Speicherzugriffsfehler (SIGSEGV)", 134: "abgebrochen (SIGABRT)"}


class TeilFehler(Exception):
    """ein Teil (KI-Bilder, Langzeittest) kann nicht weiter: code = Exit-Code, text = Grund für das Protokoll"""

    def __init__(self, code, text):
        super().__init__(text)
        self.code, self.text = code, text


def sim_code(pr):
    rc = pr.poll() if pr is not None else None
    if rc is None:
        return "läuft"
    return "Code %s%s" % (rc, (" = " + SIGNALE[rc]) if rc in SIGNALE else "")


def fehler_schreiben(o, text):
    try:
        with open(os.path.join(o, FEHLER_DATEI), "w", encoding="utf-8") as f:
            f.write(text.strip()[:1500] + "\n")
    except OSError:
        pass


def ki_grafik():
    """Grafik-Modus der Trainingsbilder: normal (lite wäre zu einfach); MW_KI_GRAFIK=lite|normal auf dem HP zum Ausprobieren.
    Hinweis: bis Simulator 3.55.0 stürzte er bei «Vielfalt hoch» ab (SIGSEGV, Morgen im Bergtal in einer Welt, bergtal.gd
    _rank_add) - ab 3.55.1 behoben; das Retten der Teilpakete bleibt für andere Abstürze."""
    g = (os.environ.get("MW_KI_GRAFIK") or "").strip()
    return g if g in ("lite", "normal") else "normal"


def ki_klassen(repo):
    """Klassennamen der Trainingsbilder aus dataset.gd des Stands (EXPORT_CLASSES) - für data.yaml eines Teilpakets"""
    try:
        with open(os.path.join(repo, "simulator3d", "scripts", "dataset.gd"), encoding="utf-8") as f:
            m = re.search(r"const EXPORT_CLASSES := \[(.*?)\]", f.read(), re.S)
        return re.findall(r'"([a-z_]+)"', m.group(1)) if m else []
    except OSError:
        return []


def ki_retten(home, t1, ziel, repo, grund):
    """der Simulator ist mitten im Bildpaket abgestürzt: die schon fertigen Bilder (Bild + Rahmen-Datei) aus seinem
    Export-Ordner als Teilpaket (YOLO wie sonst, data.yaml aus dataset.gd des Stands) sichern -> Anzahl Bilder (0 = nichts)"""
    import zipfile
    namen = ki_klassen(repo) if repo else []
    if not namen:
        return 0
    best, best_n = None, []
    for wurzel, dirs, _ in os.walk(home):
        if os.path.basename(wurzel) != "trainingsbilder":
            continue
        for d in dirs:
            e = os.path.join(wurzel, d)
            if os.path.islink(e) or os.path.getmtime(e) < t1 - 2:
                continue
            fertig = []
            for teil in ("train", "val"):
                bd = os.path.join(e, "images", teil)
                for n in sorted(os.listdir(bd)) if os.path.isdir(bd) else []:
                    stem = n[:-4]
                    if n.endswith(".jpg") and os.path.isfile(os.path.join(e, "labels", teil, stem + ".txt")) and \
                            os.path.getsize(os.path.join(bd, n)) > 0:
                        fertig.append((teil, stem))
            if len(fertig) > len(best_n):
                best, best_n = e, fertig
    if not best or len(best_n) < KI_TEIL_MIN:
        if best:
            log("Teilpaket: nur %d fertige Bilder (mindestens %d) - nicht gesichert" % (len(best_n), KI_TEIL_MIN))
        return 0
    yaml = "# Trainingsbilder (Teilpaket: %s) - YOLO-Format\npath: .\ntrain: images/train\nval: images/val\nnames:\n" % grund
    yaml += "".join("  %d: %s\n" % (i, n) for i, n in enumerate(namen))
    info = {"made": len(best_n), "teilpaket": True, "grund": grund, "vielfalt": "hoch",
            "note": "Abgebrochenes Bildpaket (Dauerrechnen): nur fertige Bilder mit Rahmen-Datei"}
    with zipfile.ZipFile(ziel + ".neu", "w", zipfile.ZIP_DEFLATED) as z:
        for teil, stem in best_n:
            z.write(os.path.join(best, "images", teil, stem + ".jpg"), "images/%s/%s.jpg" % (teil, stem))   # wie dataset.gd: flach
            z.write(os.path.join(best, "labels", teil, stem + ".txt"), "labels/%s/%s.txt" % (teil, stem))
            mj = os.path.join(best, "labels_meta", teil, stem + ".json")
            if os.path.isfile(mj):
                z.write(mj, "labels_meta/%s/%s.json" % (teil, stem))
        z.writestr("data.yaml", yaml)
        z.writestr("info.json", json.dumps(info, ensure_ascii=False, indent=1))
    os.replace(ziel + ".neu", ziel)
    shutil.rmtree(best, ignore_errors=True)                    # Platz: die Bilder sind jetzt im Teilpaket
    return len(best_n)


def ki_teil(a):
    """KI-Trainingsbilder: Simulator macht Bildpakete (YOLO, Vielfalt hoch, alle Szenen); jedes fertige Paket ist gesichert.
    Exit: 0 fertig, 2 Simulator startet nicht, 3 Bildpakete ohne ZIP, 4 Simulator stürzt immer wieder ab, 5 Simulator hängt,
    6 sonstiger Fehler. Der Grund steht in fehler.txt (und im Job-Protokoll)."""
    o = a.aus
    os.makedirs(os.path.join(o, "pakete"), exist_ok=True)
    try:
        os.unlink(os.path.join(o, FEHLER_DATEI))
    except OSError:
        pass
    try:
        return _ki_teil(a, o)
    except TeilFehler as e:
        log("FEHLER: " + e.text)
        fehler_schreiben(o, e.text)
        return e.code
    except Exception as e:                                     # unerwartet: Grund + Ort statt nur «Code 1»
        import traceback
        traceback.print_exc()
        t = traceback.extract_tb(e.__traceback__)
        wo = ("%s:%d" % (os.path.basename(t[-1].filename), t[-1].lineno)) if t else "?"
        text = "Unerwarteter Fehler beim KI-Export: %s: %s (%s)" % (type(e).__name__, e, wo)
        log("FEHLER: " + text)
        fehler_schreiben(o, text)
        return 6


def _ki_teil(a, o):
    sys.path.insert(0, ERK)
    import erkennungstest as E
    import faelle as F
    import tempfile
    tmp = tempfile.mkdtemp(prefix="mw_erk_lauf_")
    P = E.Prozesse()
    signal.signal(signal.SIGTERM, _angehalten)
    port = int(os.environ.get("MW_KI_PORT") or 8797)
    F.K["sim"] = "http://127.0.0.1:%d" % port
    F.K["out"] = o
    t_start = time.time()
    bild = None
    leer = 0
    st = {"starts": 0, "abstuerze": 0, "ohne": 0, "pr": None, "home": "", "env": None}

    def sim_log():
        return os.path.join(tmp, "simulator_%d.log" % st["starts"])

    def sim_start():
        st["starts"] += 1
        env, st["home"] = start_sim(P, E, a, tmp, port, st["env"], os.path.basename(sim_log()))
        st["env"] = env
        st["pr"] = [pr for n, pr in P.p if n == "Simulator"][-1]
        if not warte_sim(F, P):
            E.ende_protokoll(sim_log(), os.path.join(o, "simulator_start.log"), 300_000)
            raise TeilFehler(2, "Simulator %s (%s, Grafik %s, Anzeige %s) - siehe simulator_start.log im Artefakt"
                             % ("antwortet nach 5 Min. nicht" if P.laeuft("Simulator") else "startet nicht",
                                sim_code(st["pr"]), a.grafik, anzeige))

    def frage(**d):
        """eine Anfrage an den Simulator. Unter Xvfb (ohne Grafikkarte) braucht ein Szenenwechsel oft über 20 s: so lange
        er läuft, wird bis KI_STILL_S weiter gefragt. Abgestürzt -> SimWeg."""
        t0 = time.time()
        letzter = None
        while True:
            if not P.laeuft("Simulator"):
                raise SimWeg()
            try:
                return F.http_json(F.K["sim"] + "/control", d, timeout=KI_ANTWORT_S) or {}
            except (OSError, ValueError, http.client.HTTPException) as e:
                letzter = e
            if not P.laeuft("Simulator"):
                raise SimWeg()
            if time.time() - t0 > KI_STILL_S:
                raise TeilFehler(5, "Simulator hängt: %.0f s keine Antwort auf «%s» (%s: %s, Grafik %s, Anzeige %s)"
                                 % (time.time() - t0, d.get("op") or d.get("action"), type(letzter).__name__, letzter,
                                    a.grafik, anzeige))
            time.sleep(min(3.0, TAKT * 3))

    try:
        st["env"], anzeige = anzeige_starten(P, E, a, tmp)
        a.grafik = ki_grafik()
        log("KI-Trainingsbilder: Anzeige %s, Grafik %s, %d Bildpakete à %d Bilder" % (anzeige, a.grafik, a.menge, KI_BILDER))
        sim_start()
        if a.fortschritt:
            bild = Bild(F.K["sim"] + "/view.jpg", os.path.dirname(a.fortschritt))
            bild.start()
        while len(ki_fertig(o)) < a.menge:
            k = len(ki_fertig(o))
            t1 = time.time()
            try:
                r = frage(action="dataset", op="export", n=KI_BILDER, scenes=True, vielfalt="hoch")
                log("Bildpaket %d/%d gestartet: %s" % (k + 1, a.menge, r.get("msg", "")))
                time.sleep(TAKT * 4)
                while True:
                    s = frage(action="dataset", op="get")
                    bilder = len(ki_fertig(o)) * KI_BILDER
                    fortschritt(a.fortschritt, titel="Dauerrechnen", arbeit="KI-Trainingsbilder", fall=k + 1, faelle=a.menge,
                                fall_name="Bildpaket", start=int(t_start), status="laeuft",
                                plan_text="Trainingsbilder (YOLO) für das eigene KI-Modell, Vielfalt hoch, alle Szenen",
                                name=str(s.get("msg") or "")[:60],
                                kacheln=[["Bilder fertig", "%d" % bilder, ""], ["Bildpakete", "%d / %d" % (k, a.menge), ""],
                                         ["Vielfalt", "hoch", ""], ["Simulator", "MoveEye Sim " + a.stand_name[:12], ""]])
                    if not s.get("busy"):
                        break
                    time.sleep(min(3.0, TAKT * 3))
            except SimWeg:
                st["abstuerze"] += 1
                code = sim_code(st["pr"])
                E.ende_protokoll(sim_log(), os.path.join(o, "simulator_absturz_%d.log" % st["abstuerze"]), 300_000)
                log("Simulator abgestürzt (%s) bei Bildpaket %d, Grafik %s - Protokoll: simulator_absturz_%d.log"
                    % (code, k + 1, a.grafik, st["abstuerze"]))
                ziel = os.path.join(o, "pakete", "ki_%02d.zip" % (k + 1))
                n_teil = ki_retten(st["home"], t1, ziel, a.repo, "Simulator abgestürzt (%s)" % code)
                if n_teil:
                    st["ohne"] = 0
                    log("Bildpaket %d als Teilpaket gesichert: %d Bilder (%d kB)" % (k + 1, n_teil, os.path.getsize(ziel) // 1024))
                else:
                    st["ohne"] += 1
                if st["ohne"] > KI_NEUSTARTS or st["abstuerze"] > KI_ABSTUERZE_MAX:
                    raise TeilFehler(4, "Simulator %d-mal abgestürzt (zuletzt %s, Grafik %s, Anzeige %s) - siehe "
                                     "simulator_absturz_*.log im Artefakt" % (st["abstuerze"], code, a.grafik, anzeige))
                P.p = [(n, pr) for n, pr in P.p if pr.poll() is None]
                if len(ki_fertig(o)) >= a.menge:
                    continue                                   # das war das letzte Bildpaket: kein Neustart mehr
                sim_start()
                log("Simulator neu gestartet - %s" % ("weiter mit Bildpaket %d" % (k + 2) if n_teil else
                                                     "Bildpaket %d beginnt von vorn" % (k + 1)))
                continue
            neu = []
            for wurzel, _, dateien in os.walk(st["home"]):
                for n in dateien:
                    p = os.path.join(wurzel, n)
                    if re.match(r"^(MoveEye|MW)-Trainingsbilder_.*\.zip$", n) and os.path.getmtime(p) >= t1 - 2:
                        neu.append(p)
            if not neu:
                leer += 1
                log("Bildpaket ohne ZIP (%s)" % s.get("msg"))
                if leer >= 2:
                    raise TeilFehler(3, "Simulator meldet fertig, schreibt aber kein ZIP (zweimal): %s" % s.get("msg"))
                continue
            ziel = os.path.join(o, "pakete", "ki_%02d.zip" % (k + 1))
            shutil.move(max(neu, key=os.path.getmtime), ziel + ".neu")
            os.replace(ziel + ".neu", ziel)
            log("Bildpaket %d fertig: %d kB in %.0f s" % (k + 1, os.path.getsize(ziel) // 1024, time.time() - t1))
        return 0
    finally:
        if bild:
            bild.an = False
        P.stop()
        if st["starts"]:
            E.ende_protokoll(sim_log(), os.path.join(o, "simulator.log"), 300_000)
        shutil.rmtree(tmp, ignore_errors=True)


class SimWeg(Exception):
    """der Test-Simulator läuft nicht mehr (abgestürzt)"""


def lz_proben(o):
    out = []
    try:
        with open(os.path.join(o, "proben.jsonl"), encoding="utf-8") as f:
            for ln in f:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def lz_minuten(o):
    return sum(float(p.get("dt", 0)) for p in lz_proben(o)) / 60.0


def rss_mb(pid):
    try:
        with open("/proc/%d/status" % pid) as f:
            for ln in f:
                if ln.startswith("VmRSS:"):
                    return round(int(ln.split()[1]) / 1024.0, 1)
    except (OSError, ValueError):
        pass
    return None


def lz_bericht(o, stand=""):
    """Zusammenfassung des Langzeittests (auch für Teilstände): Abstürze, Speicher, Fehlalarme pro Nacht, Bilder/s"""
    pr = lz_proben(o)
    if not pr:
        return {}
    std = sum(p.get("dt", 0) for p in pr) / 3600.0
    nacht_std = sum(p.get("dt", 0) for p in pr if p.get("bed") in ("nacht", "nachtregen")) / 3600.0
    fehl = sum(p.get("fehl", 0) for p in pr)
    fehl_n = sum(p.get("fehl", 0) for p in pr if p.get("bed") in ("nacht", "nachtregen"))
    mw = [(p["t"], p["mw_mb"]) for p in pr if p.get("mw_mb")]
    wachs = None
    if len(mw) > 10:
        n = len(mw)
        mx = sum(t for t, _ in mw) / n
        my = sum(v for _, v in mw) / n
        q = sum((t - mx) ** 2 for t, _ in mw)
        wachs = round(sum((t - mx) * (v - my) for t, v in mw) / q * 3600, 1) if q else None
    fps = [p["fps"] for p in pr if p.get("fps") is not None]
    k = {"stunden": round(std, 2), "abstuerze_moveeye": sum(p.get("crash_mw", 0) for p in pr),
         "abstuerze_simulator": sum(p.get("crash_sim", 0) for p in pr), "fehlalarme": fehl, "pushes": sum(p.get("push", 0) for p in pr),
         "fehlalarme_pro_nacht": round(fehl_n / nacht_std * 8, 2) if nacht_std > 0.2 else None,
         "speicher_mw_max_mb": max((v for _, v in mw), default=None), "speicher_mw_wachstum_mb_pro_std": wachs,
         "speicher_sim_max_mb": max((p.get("sim_mb") or 0 for p in pr), default=None),
         "fps_mittel": round(sum(fps) / len(fps), 2) if fps else None}
    with open(os.path.join(o, "zusammenfassung.json"), "w", encoding="utf-8") as f:
        json.dump({"stand": stand, "kennzahlen": k}, f, ensure_ascii=False, indent=1)
    zeilen = ["# Langzeittest %s" % stand, "", "MoveEye und Simulator ohne Besucher (Leerlauf), Bedingungen reihum: %s." %
              ", ".join(LZ_BEDINGUNGEN), "", "| Grösse | Wert |", "|---|---|"]
    for name, key, fmt in (("Dauer (Std.)", "stunden", "%s"), ("Abstürze MoveEye", "abstuerze_moveeye", "%s"),
                           ("Abstürze Simulator", "abstuerze_simulator", "%s"), ("Fehlalarme (Person gemeldet)", "fehlalarme", "%s"),
                           ("Fehlalarme pro Nacht (8 Std.)", "fehlalarme_pro_nacht", "%s"), ("Pushes", "pushes", "%s"),
                           ("Speicher MoveEye max. (MB)", "speicher_mw_max_mb", "%s"),
                           ("Speicher MoveEye Zunahme (MB/Std.)", "speicher_mw_wachstum_mb_pro_std", "%s"),
                           ("Speicher Simulator max. (MB)", "speicher_sim_max_mb", "%s"), ("Bilder/s (Mittel)", "fps_mittel", "%s")):
        zeilen.append("| %s | %s |" % (name, "–" if k[key] is None else fmt % k[key]))
    with open(os.path.join(o, "bericht.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")
    return k


def langzeit_teil(a):
    """Langzeittest: MoveEye und Simulator stundenlang im Leerlauf (Bedingungen reihum je 30 Min.), Probe jede Minute"""
    sys.path.insert(0, ERK)
    import erkennungstest as E
    import faelle as F
    import tempfile
    o = a.aus
    os.makedirs(o, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="mw_erk_lauf_")
    P = E.Prozesse()
    signal.signal(signal.SIGTERM, _angehalten)
    sport, mport = 8798, 5098
    F.K.update(sim="http://127.0.0.1:%d" % sport, mw="http://127.0.0.1:%d" % mport, out=o)
    mw = E.neueste_mw(os.path.abspath(a.repo))
    mwver = ".".join(re.findall(r"\d+", os.path.basename(mw))) if mw else "?"
    if not mw:
        log("MoveEye fehlt im Stand")
        return 2
    t_start = time.time()
    bild = None
    menv = None

    def mw_start():
        cfg = os.path.join(tmp, "mw")
        if not os.path.isdir(cfg):
            os.makedirs(os.path.join(cfg, "models"), exist_ok=True)
            st = {"sim_on": True, "source": "sim:0", "thermal_source": "sim:thermal", "sim_url": F.K["sim"], "sim_auto": False,
                  "sim_autostart": False, "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de",
                  "desktop_notice": False, "setup_done": True, "thermal_on": True, "show_hud": False}
            with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
                json.dump({"cfg": st}, f)
            if a.ki_ordner:
                for fn in os.listdir(a.ki_ordner):
                    shutil.copy(os.path.join(a.ki_ordner, fn), os.path.join(cfg, "models", fn))
        return P.start("MoveEye", [sys.executable, mw, "--headless", "--port", str(mport), "--bind", "127.0.0.1", "--config", cfg],
                       menv, os.path.join(tmp, "motionwatch_%d.log" % int(time.time())))

    try:
        a.grafik = "lite"
        env, home = start_sim(P, E, a, tmp, sport)
        menv = dict(env, HOME=os.path.join(tmp, "mw_home"))
        os.makedirs(menv["HOME"], exist_ok=True)
        if not warte_sim(F, P):
            log("Simulator antwortet nicht")
            return 2
        pm = mw_start()
        ps = [pr for n, pr in P.p if n == "Simulator"][-1]
        for _ in range(100):
            try:
                if str(F.mw_state().get("source_status", "")).startswith("connected"):
                    break
            except Exception:
                pass
            time.sleep(3)
        if a.fortschritt:
            bild = Bild(F.K["mw"] + "/snapshot.jpg", os.path.dirname(a.fortschritt))
            bild.start()
        seg_alt = None
        n_msg = None
        pers_alt = 0
        while lz_minuten(o) < a.menge:
            minuten = lz_minuten(o)
            seg = int(minuten // 30)
            bed = LZ_BEDINGUNGEN[seg % len(LZ_BEDINGUNGEN)]
            if seg != seg_alt:
                try:
                    F.ctl(action="set", id="auto", value=False)
                    F.set_cond(bed)
                    F.clear()
                except Exception as e:
                    log("Bedingung %s: %r" % (bed, e))
                seg_alt = seg
                log("Abschnitt %d: %s" % (seg + 1, F.COND[bed][0]))
            probe = {"t": int(time.time()), "dt": 0, "bed": bed, "fehl": 0, "push": 0, "crash_mw": 0, "crash_sim": 0}
            t_p = time.time()
            fps = []
            while time.time() - t_p < 60:
                try:
                    s = F.mw_state()
                    fps.append(float(s.get("fps") or 0))
                    pers = int(s.get("persons") or 0)
                    if pers > 0 and pers_alt == 0:
                        probe["fehl"] += 1                    # niemand ist da: jede gemeldete Person ist ein Fehlalarm
                    pers_alt = pers
                except Exception:
                    pass
                time.sleep(5)
            try:
                m = F.mw_messages()
                n = len(m.get("items") or []) if isinstance(m, dict) else 0
                if n_msg is not None and n > n_msg:
                    probe["push"] = n - n_msg
                n_msg = n
            except Exception:
                pass
            if pm.poll() is not None:
                probe["crash_mw"] = 1
                log("MoveEye beendet (Code %s) - Neustart" % pm.returncode)
                pm = mw_start()
                n_msg = None
            if ps.poll() is not None:
                probe["crash_sim"] = 1
                log("Simulator beendet (Code %s) - Neustart" % ps.returncode)
                start_sim(P, E, a, tmp, sport, env)            # dasselbe Display (kein zweites Xvfb)
                ps = [pr for n_, pr in P.p if n_ == "Simulator"][-1]
                warte_sim(F, P)
                seg_alt = None
            probe.update(dt=round(time.time() - t_p, 1), fps=round(sum(fps) / len(fps), 2) if fps else None,
                         mw_mb=rss_mb(pm.pid) if pm.poll() is None else None, sim_mb=rss_mb(ps.pid) if ps.poll() is None else None)
            with open(os.path.join(o, "proben.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(probe) + "\n")
            k = lz_bericht(o, "MoveEye %s (%s)" % (mwver, a.stand_name))
            fortschritt(a.fortschritt, titel="Dauerrechnen", arbeit="Langzeittest", fall=int(lz_minuten(o)), faelle=a.menge,
                        fall_name="Minute", start=int(t_start), status="laeuft", name=F.COND[bed][0],
                        plan_text="MoveEye %s im Leerlauf: Abstürze, Speicher, Fehlalarme" % mwver,
                        kacheln=[["Abstürze", "%d" % (k["abstuerze_moveeye"] + k["abstuerze_simulator"]),
                                  "gruen" if not (k["abstuerze_moveeye"] + k["abstuerze_simulator"]) else "rot"],
                                 ["Fehlalarme", "%d" % k["fehlalarme"], "gruen" if not k["fehlalarme"] else "orange"],
                                 ["Speicher MoveEye", "%s MB" % (probe.get("mw_mb") or "–"), ""],
                                 ["Bilder/s", "%s" % (probe.get("fps") if probe.get("fps") is not None else "–"), ""]])
        return 0
    finally:
        if bild:
            bild.an = False
        P.stop()
        for fn in sorted(os.listdir(tmp)) if os.path.isdir(tmp) else []:
            if fn.startswith("motionwatch_") or fn == "simulator.log":
                E.ende_protokoll(os.path.join(tmp, fn), os.path.join(o, fn), 500_000)
        shutil.rmtree(tmp, ignore_errors=True)


def status(a):
    z = zustand_lesen()
    print(json.dumps({"aktiv": z.get("aktiv"), "rotation": z.get("rotation"), "erledigt": len(z.get("erledigt", {})),
                      "spielt": spielt(), "update_faellig": update_faellig()}, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description="MoveEye Dauerrechnen auf dem HP")
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("waehlen")
    w.add_argument("--kandidaten", required=True)
    w.add_argument("--arbeit", default="auto", choices=("auto",) + ARTEN)
    w.add_argument("--ausgabe", default=os.environ.get("GITHUB_OUTPUT", ""))
    r = sub.add_parser("rechnen")
    r.add_argument("--paket", required=True)
    r.add_argument("--stand", default="")
    r.add_argument("--sim-bin", default="")
    r.add_argument("--ki-ordner", default="")
    r.add_argument("--stunden", type=float, default=3.0)
    r.add_argument("--anzeige", default="xvfb")
    r.add_argument("--ausgabe", default=os.environ.get("GITHUB_OUTPUT", ""))
    h = sub.add_parser("halten")
    h.add_argument("--warten-max", type=int, default=6 * 3600)
    h.add_argument("befehl", nargs=argparse.REMAINDER)
    for name in ("ki-teil", "langzeit-teil"):
        t = sub.add_parser(name)
        t.add_argument("--repo", default="")
        t.add_argument("--sim-bin", required=True)
        t.add_argument("--aus", required=True)
        t.add_argument("--anzeige", default="xvfb", help="xvfb | :0 (Bildschirm) | keine (nur dauer_test.sh)")
        t.add_argument("--fortschritt", default="")
        t.add_argument("--menge", type=int, default=1)
        t.add_argument("--stand-name", default="")
        t.add_argument("--ki-ordner", default="")
    sub.add_parser("status")
    a = ap.parse_args()
    if a.cmd == "rechnen":
        a.stunden = max(0.0003, min(24.0, a.stunden))
    if a.cmd == "langzeit-teil":
        try:
            return langzeit_teil(a)
        except TeilFehler as e:
            log("FEHLER: " + e.text)
            fehler_schreiben(a.aus, e.text)
            return e.code
    return {"waehlen": waehlen, "rechnen": rechnen, "halten": halten, "ki-teil": ki_teil, "status": status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
