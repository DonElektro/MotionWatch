#!/usr/bin/env python3
"""HP-Testweg: Helfer lassen ihre Tests auf dem HP (self-hosted Runner «moveeye-hp») rechnen statt im lokalen Container.
Workflow .github/workflows/hp_helfer.yml (Push auf hp-test/** -> Lauf vom Stand main). Nur Standardbibliothek.

  hp_helfer.py frist --bis 2026-11-16T06:00+01:00      # Exit 0 = im erlaubten Fenster (zeigt die Rest-Minuten), sonst 1
  hp_helfer.py plan --datei hp_test.txt                # Testliste des Zweigs prüfen -> JSON {"befehle": [...], "godot": bool}
  hp_helfer.py plan --auswahl AUSGABE                  # ohne hp_test.txt: Gruppen aus ci_auswahl.py --auswahl (GITHUB_OUTPUT-Datei)
  hp_helfer.py laufen --befehle JSON --stand DIR --aus DIR --bis ISO [--godot BIN] [--max-min 52]
  hp_helfer.py aufraeumen --marke M --pfad P [--bilder-aus DIR --bilder-nach DIR]
  hp_helfer.py --selbsttest

hp_test.txt (im Wurzelordner des gepushten Zweigs, eine Zeile pro Befehl, «#» = Kommentar, höchstens 40 Zeilen). Erlaubt
ist NUR (keine Shell - die Zeile wird in Wörter zerlegt und ohne Shell gestartet):
  python3 werkzeuge/ci_lauf.py --gruppe basis|kern|rechte|live|daten|spiele-1|spiele-2   (auch --pruefen, --liste)
  python3 [-W ignore] [-u] werkzeuge/<pfad>.py [Argumente]       (nicht werkzeuge/test_runner/)
  godot werkzeuge/<name>_test.gd                                  (Godot 4.3 headless wie im CI, Import vorher)
  davor erlaubt: Variablen MW_…=…, CI_…=…, SIM_…=…, TEST_…=…
Argumente und Werte nur aus  A-Z a-z 0-9 _ . , = : / + @ % -  (keine Anführungszeichen, kein $, ;, |, &, >, <, `, *, ~).
"""
import argparse
import datetime
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

GRUPPEN_HP = ["basis", "kern", "rechte", "live", "daten", "spiele-1", "spiele-2"]   # not simlive (needs a running sim), pidienst (sudo/systemd)
WEB = ["kern", "rechte", "live", "daten", "spiele-1", "spiele-2"]
SICHER = re.compile(r"[A-Za-z0-9_.,=:/+@%-]+")
VAR = re.compile(r"(MW|CI|SIM|TEST)_[A-Z0-9_]{1,40}=[A-Za-z0-9_.,:/+@%-]{0,200}")
SKRIPT = re.compile(r"werkzeuge/[A-Za-z0-9_][A-Za-z0-9_-]*(/[A-Za-z0-9_][A-Za-z0-9_-]*)*\.py")
GD = re.compile(r"werkzeuge/[a-z0-9_]{1,60}_test\.gd")
MAX_ZEILEN = 40
SPIEL = os.environ.get("MW_SPIEL", "/run/moveeye-spiel/spielen")


def gh():
    return bool(os.environ.get("GITHUB_ACTIONS"))


def zusammenfassung(text):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(text + "\n")


# ------------------------------------------------------------------ Zeitfenster
def zeit_lesen(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    d = datetime.datetime.fromisoformat(s)                  # raises on garbage - never «no limit»
    if d.tzinfo is None:
        raise ValueError("Zeit ohne Zeitzone: %s" % s)
    return d


def rest_sekunden(bis, jetzt=None):
    jetzt = jetzt or datetime.datetime.now(datetime.timezone.utc)
    return (zeit_lesen(bis) - jetzt).total_seconds()


def frist(a):
    try:
        r = rest_sekunden(a.bis)
    except ValueError as e:
        print("::error::HP_HELFER_BIS unlesbar (%s) - nichts gestartet" % e)
        return 1
    if r < a.mindestens * 60:
        msg = ("HP-Testweg geschlossen: erlaubt nur bis %s (HP_HELFER_BIS in .github/workflows/hp_helfer.yml auf main). "
               "Nichts gestartet - bitte lokal testen oder den Integrator fragen." % a.bis)
        print("::error title=HP-Testweg geschlossen::" + msg)
        zusammenfassung("### ⛔ " + msg)
        return 1
    print("HP-Testweg offen: noch %d Min. (bis %s)" % (r // 60, a.bis))
    return 0


# ------------------------------------------------------------------ Testliste prüfen
def zeile_pruefen(z):
    """-> (argv, None) or (None, reason). argv[0] is 'python3' or 'godot'; leading VAR=wert words stay in front."""
    if len(z) > 300:
        return None, "Zeile länger als 300 Zeichen"
    if not re.fullmatch(r"[ -~]*", z):
        return None, "nur einfache Zeichen (ASCII, Leerzeichen als Trenner, kein Tabulator)"
    w = z.split(" ")
    w = [x for x in w if x]
    if not w:
        return None, "leer"
    for x in w:
        if not SICHER.fullmatch(x):
            return None, "unerlaubtes Zeichen in «%s» (erlaubt: A-Z a-z 0-9 _ . , = : / + @ %% -)" % x[:40]
    i = 0
    while i < len(w) and "=" in w[i] and not w[i].startswith("-"):
        if not VAR.fullmatch(w[i]):
            return None, "Variable «%s»: nur MW_…, CI_…, SIM_…, TEST_… erlaubt" % w[i][:40]
        i += 1
    rest = w[i:]
    if not rest:
        return None, "kein Befehl"
    if rest[0] == "godot":
        if len(rest) != 2 or not GD.fullmatch(rest[1]):
            return None, "godot: nur «godot werkzeuge/<name>_test.gd»"
        return w, None
    if rest[0] != "python3":
        return None, "nur «python3 werkzeuge/….py …» oder «godot werkzeuge/…_test.gd»"
    j = 1
    while j < len(rest) and rest[j] in ("-W", "-u"):
        if rest[j] == "-W":
            if j + 1 >= len(rest) or rest[j + 1] != "ignore":
                return None, "python3: nur «-W ignore» und «-u» als Optionen"
            j += 2
        else:
            j += 1
    if j >= len(rest) or not SKRIPT.fullmatch(rest[j]):
        return None, "python3: das Skript muss werkzeuge/<pfad>.py sein (ohne «..»)"
    skript, args = rest[j], rest[j + 1:]
    if skript.startswith("werkzeuge/test_runner/"):
        return None, "werkzeuge/test_runner/ läuft nicht über den HP-Testweg (das ist der Runner selbst)"
    if skript == "werkzeuge/hp_helfer.py":
        return None, "hp_helfer.py nicht über sich selbst"
    if skript == "werkzeuge/ci_lauf.py":
        ok = args in (["--pruefen"], ["--liste"]) or (len(args) == 2 and args[0] == "--gruppe" and args[1] in GRUPPEN_HP)
        if not ok:
            return None, "ci_lauf.py: nur --pruefen, --liste oder --gruppe %s (simlive, pidienst nicht auf dem HP)" % "|".join(GRUPPEN_HP)
    return w, None


def liste_pruefen(text):
    """-> (befehle, fehler)"""
    befehle, fehler = [], []
    for nr, ln in enumerate(text.splitlines(), 1):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        argv, grund = zeile_pruefen(ln)
        if grund:
            fehler.append("hp_test.txt Zeile %d: %s" % (nr, grund))
        else:
            befehle.append(" ".join(argv))
    if len(befehle) > MAX_ZEILEN:
        fehler.append("hp_test.txt: höchstens %d Befehle (jetzt %d)" % (MAX_ZEILEN, len(befehle)))
    if not befehle and not fehler:
        fehler.append("hp_test.txt enthält keinen Befehl (Datei löschen = Standard: die Gruppen wie im CI)")
    return befehle, fehler


def aus_auswahl(text):
    """lines key=value of ci_auswahl.py --auswahl -> commands: list check, basis, then the selected web groups"""
    werte = dict(ln.split("=", 1) for ln in text.splitlines() if "=" in ln)
    try:
        gruppen = json.loads(werte.get("gruppen", "null"))
    except ValueError:
        gruppen = None
    if not isinstance(gruppen, list):
        gruppen = WEB[:4]                                   # selection broken: like ci.yml, every web group but the games
    befehle = ["python3 werkzeuge/ci_lauf.py --pruefen", "python3 werkzeuge/ci_lauf.py --gruppe basis"]
    befehle += ["python3 werkzeuge/ci_lauf.py --gruppe %s" % g for g in gruppen if g in WEB]
    return befehle


def plan(a):
    if a.datei:
        with open(a.datei, encoding="utf-8", errors="replace") as f:
            befehle, fehler = liste_pruefen(f.read(64 * 1024))
        for x in fehler:
            print("::error title=hp_test.txt abgelehnt::" + x, file=sys.stderr)
        if fehler:
            zusammenfassung("### ⛔ hp_test.txt abgelehnt\n\n" + "\n".join("- " + x for x in fehler) +
                            "\n\nErlaubt: siehe `werkzeuge/hp_helfer.py` (Kopf) bzw. CLAUDE.md «HP-Testweg».")
            return 1
        quelle = "hp_test.txt"
    else:
        with open(a.auswahl, encoding="utf-8") as f:
            befehle = aus_auswahl(f.read())
        quelle = "Standard (Gruppen nach ci_auswahl.py)"
    godot = any(ist_godot(b) for b in befehle)
    print(json.dumps({"befehle": befehle, "godot": godot, "quelle": quelle}, ensure_ascii=False, separators=(",", ":")))
    return 0


# ------------------------------------------------------------------ laufen (auf dem HP)
def spielt():
    try:
        if os.path.islink(SPIEL) or not os.path.isfile(SPIEL):
            return False
        return time.time() - os.stat(SPIEL).st_mtime < 900
    except OSError:
        return False


def gruppe_beenden(p):
    for sig, warten in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
        try:
            os.killpg(p.pid, sig)
        except OSError:
            return
        t = time.time() + warten
        while p.poll() is None and time.time() < t:
            time.sleep(0.2)


def ist_godot(befehl):
    return [x for x in befehl.split() if not VAR.fullmatch(x)][:1] == ["godot"]


def godot_home(marke, n):
    return "/tmp/mw_hphelfer_%s_%d" % (re.sub(r"[^0-9A-Za-z-]", "", marke) or "x", n)


def argv_fuer(befehl, py, godot, stand):
    w = befehl.split()
    env = {}
    while "=" in w[0] and not w[0].startswith("-"):
        k, v = w[0].split("=", 1)
        env[k] = v
        w = w[1:]
    if w[0] == "python3":
        return [py] + w[1:], env, stand
    gd = os.path.join(stand, w[1])                         # godot werkzeuge/x_test.gd (like ci.yml «Simulator · <test>»)
    return [godot, "--headless", "--path", ".", "-s", gd, "--", "--no-update", "--no-tour"], env, os.path.join(stand, "simulator3d")


def laufen(a):
    befehle = json.loads(a.befehle)
    os.makedirs(os.path.join(a.aus, "logs"), exist_ok=True)
    ende = min(time.time() + a.max_min * 60, time.time() + rest_sekunden(a.bis) - 30)
    basis_env = dict(os.environ, PYTHONUNBUFFERED="1", CI_STRENG="", HP_HELFER_MARKE=a.marke)
    zeilen, rot, abbruch = [], 0, ""
    for n, b in enumerate(befehle, 1):
        if not abbruch and spielt():
            abbruch = "am HP wird gespielt (der Besitzer hat Vorrang)"
        if not abbruch and time.time() > ende - 20:
            abbruch = "Zeit um (Job-Limit bzw. Fenster bis %s)" % a.bis
        if abbruch:
            zeilen.append((b, 0, "⏭️ nicht gelaufen (%s)" % abbruch))
            continue
        if ist_godot(b) and not a.godot:
            zeilen.append((b, 0, "❌ Godot fehlt"))
            rot += 1
            continue
        argv, extra, cwd = argv_fuer(b, a.python, a.godot, a.stand)
        env = dict(basis_env, **extra)
        if argv[0] == a.godot:                             # Godot tests insist on a test HOME below /tmp (hospiz_test.gd)
            env["HOME"] = godot_home(a.marke, n)
            os.makedirs(env["HOME"], exist_ok=True)
        log = os.path.join(a.aus, "logs", "%02d_%s.log" % (n, re.sub(r"[^A-Za-z0-9_.-]+", "_", b)[-80:]))
        print("\n===== [%d/%d] %s" % (n, len(befehle), b), flush=True)   # no ::group:: - ci_lauf.py opens its own
        t0 = time.time()
        with open(log, "wb") as lf:
            p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)

            def tee():
                for chunk in iter(lambda: p.stdout.readline(), b""):
                    lf.write(chunk)
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.flush()
            th = threading.Thread(target=tee, daemon=True)
            th.start()
            grund = ""
            while p.poll() is None:
                if time.time() > ende:
                    grund = "Zeit um"
                elif spielt():
                    grund = "am HP wird gespielt"
                if grund:
                    gruppe_beenden(p)
                    break
                time.sleep(0.5)
            rc = p.wait()
            gruppe_beenden(p)                               # whatever the command left in its group
            th.join(timeout=10)
        sek = time.time() - t0
        if grund:
            abbruch = grund
            erg = "❌ abgebrochen (%s)" % grund
            rot += 1
        elif rc == 0:
            erg = "✅ grün"
        else:
            erg = "❌ rot (Exit-Code %d)" % rc
            rot += 1
        print("%s  %d:%02d  %s" % ("OK    " if rc == 0 and not grund else "FEHLER", sek // 60, sek % 60, b), flush=True)
        if erg.startswith("❌") and gh():
            print("::error title=HP-Test rot::%s - %s (Protokoll im Artefakt: logs/%s)" % (b[:120], erg[2:], os.path.basename(log)), flush=True)
        zeilen.append((b, sek, erg))
    kopf = "HP-Testweg: %d Befehle, %d rot%s" % (len(zeilen), rot, (" – " + abbruch) if abbruch else "")
    print("\n" + kopf)
    tab = ["### %s" % kopf, "", "| # | Befehl | Dauer | Ergebnis |", "|---:|---|---:|---|"]
    for i, (b, sek, erg) in enumerate(zeilen, 1):
        print("  %5s  %-26s %s" % ("%d:%02d" % (sek // 60, sek % 60), erg, b))
        tab.append("| %d | `%s` | %d:%02d | %s |" % (i, b.replace("|", "/"), sek // 60, sek % 60, erg))
    zusammenfassung("\n".join(tab) + "\n")
    with open(os.path.join(a.aus, "ergebnis.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(tab) + "\n")
    return 1 if rot or abbruch else 0


# ------------------------------------------------------------------ aufräumen
def eigene_vorfahren():
    out, pid = set(), os.getpid()
    while pid > 1:
        out.add(pid)
        try:
            with open("/proc/%d/stat" % pid) as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return out


def reste(marke, pfad):
    """own processes (same uid) that carry the marker in their environment or the job temp path in their command line"""
    uid, ich, out = os.getuid(), eigene_vorfahren(), []
    m = ("HP_HELFER_MARKE=%s" % marke).encode()
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) in ich:
            continue
        try:
            if os.stat("/proc/" + d).st_uid != uid:
                continue
            with open("/proc/%s/cmdline" % d, "rb") as f:
                cmd = f.read()
            try:
                with open("/proc/%s/environ" % d, "rb") as f:
                    envb = f.read()
            except OSError:
                envb = b""
        except OSError:
            continue
        if not cmd:                                         # zombie / kernel thread
            continue
        if (marke and m in envb.split(b"\0")) or (pfad and pfad.encode() in cmd):
            out.append((int(d), cmd.replace(b"\0", b" ").decode("utf-8", "replace")[:120]))
    return out


def bilder_sammeln(von, nach, max_mb=150):
    """screenshots and small reports the tests left in TMPDIR / the checkout -> artifact folder (newest first, size cap)"""
    endungen = (".png", ".jpg", ".jpeg", ".webp", ".html", ".log")
    funde = []
    for quelle in von:
        if not os.path.isdir(quelle):
            continue
        for wurzel, dirs, files in os.walk(quelle):
            dirs[:] = [x for x in dirs if x not in (".git", ".godot", "__pycache__", "node_modules", "venv", "ms-playwright")]
            for fn in files:
                if fn.lower().endswith(endungen):
                    p = os.path.join(wurzel, fn)
                    try:
                        st = os.lstat(p)
                    except OSError:
                        continue
                    if os.path.isfile(p) and not os.path.islink(p) and st.st_size < 20 * 1024 * 1024:
                        funde.append((st.st_mtime, st.st_size, quelle, p))
    budget, n = max_mb * 1024 * 1024, 0
    for _mt, size, quelle, p in sorted(funde, reverse=True):
        if size > budget:
            continue
        ziel = os.path.join(nach, os.path.basename(quelle.rstrip("/")), os.path.relpath(p, quelle))
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        try:
            with open(p, "rb") as s, open(ziel, "wb") as t:
                t.write(s.read())
        except OSError:
            continue
        budget -= size
        n += 1
    return n


def aufraeumen(a):
    for sig, warten in ((signal.SIGTERM, 10), (signal.SIGKILL, 3)):
        r = reste(a.marke, a.pfad)
        if not r:
            break
        print("Reste des Jobs beenden (%s): %s" % (sig.name, "; ".join("%d %s" % x for x in r)))
        for pid, _ in r:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        t = time.time() + warten
        while reste(a.marke, a.pfad) and time.time() < t:
            time.sleep(0.3)
    if a.marke:                                             # Godot test homes of THIS job only (exact prefix, own files)
        vor = os.path.basename(godot_home(a.marke, 0))[:-1]
        for d in os.listdir("/tmp"):
            p = os.path.join("/tmp", d)
            if d.startswith(vor) and d[len(vor):].isdigit() and os.path.isdir(p) and not os.path.islink(p) \
                    and os.lstat(p).st_uid == os.getuid():
                shutil.rmtree(p, ignore_errors=True)
    uebrig = reste(a.marke, a.pfad)
    print("Keine Reste des Jobs mehr." if not uebrig else "::warning::nicht beendet: %s" % uebrig)
    if a.bilder_nach:
        n = bilder_sammeln(a.bilder_aus, a.bilder_nach)
        print("%d Bilder / Berichte ins Artefakt" % n)
    return 0


# ------------------------------------------------------------------ Selbsttest
def selbsttest():
    gut = ["python3 werkzeuge/ci_lauf.py --gruppe kern", "python3 werkzeuge/ci_lauf.py --pruefen",
           "python3 -W ignore werkzeuge/karten_test.py", "python3 werkzeuge/bauen.py --pruefen",
           "MW_SELFTEST_NO_SIG=1 python3 werkzeuge/web_rauchtest.py --browser --url=http://127.0.0.1:8080/",
           "godot werkzeuge/gelenke_test.gd", "python3 -u werkzeuge/erkennungstest/bericht.py --x=1"]
    schlecht = ["bash -c id", "python3 werkzeuge/x.py; rm -rf ~", "python3 werkzeuge/../../etc/x.py",
                "python3 werkzeuge/x.py $(id)", "python3 werkzeuge/x.py `id`", "python3 werkzeuge/x.py | sh",
                "python3 werkzeuge/x.py > /etc/x", "python3 -c print(1)", "python3 werkzeuge/ci_lauf.py --gruppe pidienst",
                "python3 werkzeuge/ci_lauf.py --gruppe simlive", "python3 werkzeuge/test_runner/dauer.py status",
                "PATH=/tmp python3 werkzeuge/x.py", "LD_PRELOAD=/tmp/x.so python3 werkzeuge/x.py",
                "python3 werkzeuge/x.py 'a b'", "python3 werkzeuge/x.py ~/geheim", "godot --script /tmp/x.gd",
                "godot werkzeuge/x.gd", "python3 /tmp/x.py", "python3 -m pip install x", "sudo python3 werkzeuge/x.py",
                "python3 werkzeuge/x.py *", "python3 werkzeuge/hp_helfer.py laufen", "python3 -W error werkzeuge/x.py",
                "python3 werkzeuge/x.py\tid", "MW_X=$HOME python3 werkzeuge/x.py"]
    fehler = 0
    for z in gut:
        argv, g = zeile_pruefen(z)
        if g:
            print("FEHLER: abgelehnt, sollte gehen: %s (%s)" % (z, g))
            fehler += 1
    for z in schlecht:
        argv, g = zeile_pruefen(z)
        if not g:
            print("FEHLER: angenommen, sollte abgelehnt werden: %s" % z)
            fehler += 1
    b, f = liste_pruefen("# Kommentar\n\npython3 werkzeuge/ci_lauf.py --gruppe live\n")
    if b != ["python3 werkzeuge/ci_lauf.py --gruppe live"] or f:
        print("FEHLER: liste_pruefen", b, f)
        fehler += 1
    if not liste_pruefen("# nur Kommentar\n")[1] or not liste_pruefen("\n".join(["python3 werkzeuge/a.py"] * 41))[1]:
        print("FEHLER: leere / zu lange Liste angenommen")
        fehler += 1
    std = aus_auswahl('web=true\ngruppen=["kern", "rechte", "live", "daten"]\nsim=true\n')
    if std != ["python3 werkzeuge/ci_lauf.py --pruefen", "python3 werkzeuge/ci_lauf.py --gruppe basis"] + \
            ["python3 werkzeuge/ci_lauf.py --gruppe %s" % g for g in ("kern", "rechte", "live", "daten")]:
        print("FEHLER: aus_auswahl", std)
        fehler += 1
    if aus_auswahl('gruppen=["keine"]\n')[-1] != "python3 werkzeuge/ci_lauf.py --gruppe basis":
        print("FEHLER: aus_auswahl keine")
        fehler += 1
    for z in std:
        if zeile_pruefen(z)[1]:
            print("FEHLER: Standard-Befehl nicht erlaubt: " + z)
            fehler += 1
    j = datetime.datetime(2026, 11, 16, 4, 59, tzinfo=datetime.timezone.utc)
    if not (rest_sekunden("2026-11-16T06:00+01:00", j) == 60 and rest_sekunden("2026-11-16T06:00+01:00", j + datetime.timedelta(minutes=2)) < 0):
        print("FEHLER: Zeitfenster")
        fehler += 1
    for kaputt in ("", "morgen", "2026-11-16T06:00"):
        try:
            rest_sekunden(kaputt)
            print("FEHLER: Zeit «%s» angenommen" % kaputt)
            fehler += 1
        except ValueError:
            pass
    argv, env, cwd = argv_fuer("MW_X=1 python3 -W ignore werkzeuge/a.py --b", "/v/bin/python", "", "/s")
    if argv != ["/v/bin/python", "-W", "ignore", "werkzeuge/a.py", "--b"] or env != {"MW_X": "1"} or cwd != "/s":
        print("FEHLER: argv_fuer", argv, env, cwd)
        fehler += 1
    argv, env, cwd = argv_fuer("godot werkzeuge/a_test.gd", "/py", "/g/godot", "/s")
    if argv[:2] != ["/g/godot", "--headless"] or "/s/werkzeuge/a_test.gd" not in argv or cwd != "/s/simulator3d":
        print("FEHLER: argv_fuer godot", argv, cwd)
        fehler += 1
    print("Selbsttest hp_helfer.py: %s" % ("OK" if not fehler else "%d Fehler" % fehler))
    return 1 if fehler else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selbsttest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("frist")
    f.add_argument("--bis", required=True)
    f.add_argument("--mindestens", type=int, default=3, help="so viele Minuten müssen noch übrig sein")
    p = sub.add_parser("plan")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--datei")
    g.add_argument("--auswahl")
    l = sub.add_parser("laufen")
    l.add_argument("--befehle", required=True, help="JSON-Liste")
    l.add_argument("--stand", required=True)
    l.add_argument("--aus", required=True)
    l.add_argument("--bis", required=True)
    l.add_argument("--python", default=sys.executable)
    l.add_argument("--godot", default="")
    l.add_argument("--max-min", type=int, default=52)
    l.add_argument("--marke", default="")
    r = sub.add_parser("aufraeumen")
    r.add_argument("--marke", default="")
    r.add_argument("--pfad", default="")
    r.add_argument("--bilder-aus", nargs="*", default=[])
    r.add_argument("--bilder-nach", default="")
    a = ap.parse_args()
    if a.selbsttest:
        return selbsttest()
    if a.cmd == "laufen":
        a.stand, a.aus = os.path.abspath(a.stand), os.path.abspath(a.aus)
        liste = json.loads(a.befehle)                       # checked again right before running: never anything else
        if not isinstance(liste, list):
            liste = [None]
        schlecht = [x for x in liste if not isinstance(x, str) or zeile_pruefen(x)[1]]
        if schlecht or len(liste) > MAX_ZEILEN:
            print("::error::Befehlsliste enthält Unerlaubtes: %s" % schlecht[:3])
            return 1
    return {"frist": frist, "plan": plan, "laufen": laufen, "aufraeumen": aufraeumen}.get(a.cmd, lambda _a: ap.print_help() or 2)(a)


if __name__ == "__main__":
    sys.exit(main())
