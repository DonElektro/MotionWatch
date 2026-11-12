#!/usr/bin/env python3
"""Simulator-Anhang, MoveEye-Seite (/sim): Windows- und Linux-Paket des Simulators als Release-Asset («sim.anhang» in der
signierten versions.json, Teil 300 / 390) - ganze Kette mit lokalen Servern statt GitHub und einem Wegwerf-Schlüssel.

  python3 werkzeuge/sim_anhang_test.py [--behalten]

Aufbau wie ein echter Ablauf, mit kleinen Ersatz-Paketen (nichts Grosses wird kopiert):
  1. Ersatz-Repository: Sim A im Repository (versionen.py --sim-json; A = eingebettete Sim-Nummer + 1, steht für 3.67.2),
     dann Sim B als Anhang (Assets unter simulator3d/anhang/, versionen.py --anhang-json; B = A + 1).
  2. Signieren mit der NEU gebauten MoveEye (--make-manifest, Wegwerf-Schlüssel): «sim.win» / «sim.linux» = A (eingefroren),
     «sim.anhang» = B mit Adresse; ohne die geholten Assets bleibt eine gültige Signatur erhalten, eine ungültige nicht.
  3. Geräte gegen drei Server (1 = Repository, 2 = «Asset-Server» antwortet wie GitHub mit 302, 3 = Ziel der Umleitung):
     M1 ALTE MoveEye (neueste Datei im Repository, die den Anhang noch nicht kennt): holt A aus dem Repository wie immer,
        fragt den Asset-Server nie; in «Neueste Version» steht der Hinweis «bitte zuerst MoveEye aktualisieren».
     M2 NEUE MoveEye: holt B für Windows und Linux über die Umleitung, Prüfsumme wie signiert; merkt sich den Block.
     M3 Asset fehlt (404) · M4 Asset verändert · M6 Asset-Server nicht erreichbar: nichts im Zwischenspeicher, klare Meldung.
     M5 Signatur des Anhangs falsch · M7 fremde Adresse / Adresse einer anderen Nummer: der Anhang wird nicht genommen,
        MoveEye liefert weiter A aus dem Repository.
     M8 Zurück ins Repository: Liste ohne Anhang, neuere Nummer C im Repository -> die neue MoveEye nimmt C von dort.
  4. sim_anhang.py «abruf» (so holen die Workflows das Linux-Paket): gut / fehlt / verändert, nichts Halbes bleibt.
Die echte Umleitung von GitHub ist hier NICHT getestet (dafür: Workflow «Sim-Pakete», Abruf-Probe).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import update_uebergang_test as U  # noqa: E402
import versionen_spuren_test as S  # noqa: E402

ok = U.ok
ECHT_BASIS = "https://github.com/DonElektro/MotionWatch/releases/download/"
NAMEN = {"win": "MotionWatch3D_Simulator.zip", "linux": "MoveEyeSim3D_Linux.zip"}

HOLEN = r'''
import glob, hashlib, time
ns["CFG"]["update_url"] = sys.argv[2]
if sys.argv[3] and "SIM3D_ANHANG_BASE" in ns:
    ns["SIM3D_ANHANG_BASE"] = sys.argv[3]                  # test: the «asset server» instead of github.com
res = {"app": ns["APP_VERSION"], "kennt": "SIM3D_ANHANG" in ns}
if "liste" in sys.argv[4:]:                                # as the device does regularly: look at the update list (390 update_check)
    ns["sim_manifest_load"]()
    ns["update_check"]()
for key, pkg, dl in (("win", ns["SIM3D"], ns["SIM3D_DL"]), ("linux", ns["SIM3D_LINUX"], ns["SIM3D_LINUX_DL"])):
    ns["sim3d_fetch"](pkg, dl)
    t0 = time.time()
    while dl["running"] and time.time() - t0 < 90:
        time.sleep(0.05)
    p = ns["sim3d_path"](pkg)
    res[key] = {"ver": pkg["version"], "url": pkg.get("url", ""), "ready": bool(ns["sim3d_ready"](pkg)), "msg": dl["msg"],
                "sha": hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.isfile(p) else ""}
res["dateien"] = sorted(os.path.basename(x) for x in glob.glob(os.path.join(ns["DATA_DIR"], "sim3d", "*")))
if "latest" in sys.argv[4:]:
    ns["sim_latest_check"](force=True)
    t0 = time.time()
    while ns["SIMLATEST"]["busy"] and time.time() - t0 < 30:
        time.sleep(0.05)
    res["latest"] = ns["SIMLATEST"]["3d"]
print("RES " + json.dumps(res))
'''

PRUEFEN = r'''
man = json.load(open(os.path.join(sys.argv[2], "versions.json"), encoding="utf-8"))
bad, txt = ns["sim_manifest_check"](sys.argv[2], man)
print("RES " + json.dumps({"bad": bad, "txt": txt}))
'''


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--behalten", action="store_true")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="mw_simanhang_")
    srvs = []
    try:
        # ---- numbers: relative to the simulator embedded in quelle/ (never older than what the program already has)
        q300 = U.lesen(os.path.join(REPO, "quelle", "300_werkzeuge_simulator3d.py")).decode("utf-8")
        x, y, z = (int(n) for n in re.search(r'^SIM3D = \{"version": "(\d+)\.(\d+)\.(\d+)"', q300, re.M).groups())
        va, vb, vc = ("%d.%d.%d" % (x, y, z + i) for i in (1, 2, 3))
        print("Sim im Repository (eingefroren) %s · Anhang %s · Zurück ins Repository %s" % (va, vb, vc))

        # ---- the new MoveEye, built from quelle/
        progs = U.programme(REPO)
        nx, ny, _nz = max(U.vkey(v) for v in progs)
        neu_v = "%d.%d.0" % (nx, ny + 1)
        bau = os.path.join(tmp, "bau")
        shutil.copytree(os.path.join(REPO, "quelle"), os.path.join(bau, "quelle"))
        os.makedirs(os.path.join(bau, "werkzeuge"))
        os.makedirs(os.path.join(bau, "simulator3d"))
        shutil.copy(os.path.join(HIER, "bauen.py"), os.path.join(bau, "werkzeuge"))
        for fn in ("ui_gemeinsam.json", "fehler_katalog.json", "version.json"):
            shutil.copy(os.path.join(REPO, "simulator3d", fn), os.path.join(bau, "simulator3d"))
        r = subprocess.run([sys.executable, os.path.join(bau, "werkzeuge", "bauen.py"), "--neue-version", "Test Simulator-Anhang",
                            "--version", neu_v], capture_output=True, text=True, cwd=bau)
        u_ = neu_v.replace(".", "_")
        neu_py, neu_zip = "webcam_bewegung_%s.py" % u_, "moveeye_daten_%s.zip" % u_
        if r.returncode or not os.path.isfile(os.path.join(bau, neu_py)):
            print(r.stdout[-1500:] + r.stderr[-1500:])
            ok(False, "Bau der neuen MoveEye %s" % neu_v)
            return 1
        shutil.rmtree(os.path.join(bau, "quelle"))
        alt_v = next((v for v in sorted(progs, key=U.vkey, reverse=True)
                      if b"SIM3D_ANHANG" not in U.lesen(os.path.join(REPO, progs[v])) and b"def sim_manifest_take" in U.lesen(os.path.join(REPO, progs[v]))), "")
        ok(bool(alt_v), "ALTE MoveEye im Repository gefunden, die den Anhang noch nicht kennt (%s)" % (alt_v or "keine"))
        key = os.path.join(tmp, "test_schluessel.txt")
        open(key, "w").write(os.urandom(32).hex())
        home = os.path.join(tmp, "home")
        res = U.py(os.path.join(bau, neu_py), 'ns["_ED"].extend(ns["_ed25519_impl"]())\n'
                   'print("RES " + json.dumps(ns["_ED"][0](bytes.fromhex(open(sys.argv[2]).read().strip())).hex()))', home + "0", {}, key)
        pub = res if isinstance(res, str) else ""
        ok(len(pub) == 64 and pub != U.ECHT_PUB, "Wegwerf-Schlüssel erzeugt (nicht der echte)")
        if len(pub) != 64:
            return 1

        # ---- 1: a small repository, Sim A in it, Sim B as assets
        print("1  Ersatz-Repository: Sim %s im Repository, Sim %s als Anhang" % (va, vb))
        R = os.path.join(tmp, "repo")
        env_v = dict(os.environ, MW_VERSIONEN_REPO=R)

        def vers(*args, **kw):
            r = subprocess.run([sys.executable, os.path.join(HIER, "versionen.py")] + list(args), env=dict(env_v, **kw), capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr
        S.schreib(R, "simulator3d/scripts/abgleich.gd", 'extends Node\nconst MW_MIN := "3.55.0"\n')
        S.linux_zip(R, va)
        rc, out = vers("--sim-json", va, "Letzte Version im Repository")
        ok(rc == 0, "version.json: Sim %s im Repository" % va)
        S.anhang_zips(R, vb)
        rc, out = vers("--anhang-json", vb, "Erste Version als Release-Asset")
        vj = json.load(open(os.path.join(R, "simulator3d", "version.json"), encoding="utf-8"))
        ok(rc == 0 and vj["ver"] == va and vj["anhang"]["ver"] == vb and vj["anhang"]["win"]["url"] == ECHT_BASIS + "sim-%s/%s" % (vb, NAMEN["win"]),
           "version.json: «anhang» %s, oben bleibt %s (%s)" % (vb, va, out.strip()[:120]))
        asset = {k: U.lesen(os.path.join(R, "simulator3d", "anhang", NAMEN[k])) for k in NAMEN}
        fest = {"win": U.lesen(os.path.join(R, "simulator3d", NAMEN["win"])), "linux": U.lesen(os.path.join(R, "simulator3d", NAMEN["linux"]))}

        # ---- 2: sign with the new MoveEye (throwaway key)
        print("2  Signieren mit der neuen MoveEye %s (--make-manifest, Wegwerf-Schlüssel)" % neu_v)
        shutil.copy(os.path.join(bau, neu_py), R)
        shutil.copy(os.path.join(bau, neu_zip), R)
        U.pub_setzen(os.path.join(R, neu_py), pub)

        def signieren():
            r = subprocess.run([sys.executable, os.path.join(R, neu_py), "--make-manifest", R, "--sign-key", key], capture_output=True,
                               text=True, cwd=R, env=dict(os.environ, MOTIONWATCH_HOME=home + "m"))
            return json.load(open(os.path.join(R, "versions.json"), encoding="utf-8")), r.stdout + r.stderr
        man, out = signieren()
        sim = man.get("sim") or {}
        ah = sim.get("anhang") or {}
        ok(sim.get("ver") == va and (sim.get("win") or {}).get("ver") == va and (sim.get("linux") or {}).get("ver") == va
           and (sim["win"].get("sig") and sim["linux"].get("sig")) and not sim["win"].get("url"),
           "«sim.win» / «sim.linux»: Sim %s im Repository, signiert, ohne Adresse (wie bisher - für alte MoveEye, alten HP)" % va)
        ok(ah.get("ver") == vb and all((ah.get(k) or {}).get("sig") and ah[k]["file"] == "simulator3d/anhang/" + NAMEN[k]
                                       and ah[k]["url"] == ECHT_BASIS + "sim-%s/%s" % (vb, NAMEN[k]) and ah[k]["sha256"] == sha(asset[k]) for k in NAMEN),
           "«sim.anhang»: Sim %s, Windows + Linux signiert, eigener Dateiname, Adresse sim-%s" % (vb, vb))
        r = U.py(os.path.join(R, neu_py), PRUEFEN, home + "p", {}, R)
        ok(r.get("bad") == [] and "asset %s" % vb in r.get("txt", ""), "Selbsttest-Prüfung der Liste: ok (%s)" % r.get("txt", "").strip(", "))
        sig_vor = {k: ah[k]["sig"] for k in NAMEN}
        shutil.rmtree(os.path.join(R, "simulator3d", "anhang"))               # after signing the fetched assets may go
        man2, out = signieren()
        ah2 = (man2.get("sim") or {}).get("anhang") or {}
        ok(all((ah2.get(k) or {}).get("sig") == sig_vor[k] for k in NAMEN),
           "nochmals signieren OHNE die geholten Assets (z. B. bei einer neuen MoveEye): die gültige Signatur bleibt")
        r = U.py(os.path.join(R, neu_py), PRUEFEN, home + "p2", {}, R)
        ok(r.get("bad") == [], "Selbsttest-Prüfung ohne die Asset-Dateien: ok (Signatur und Adresse)")
        gut_text = json.dumps(man2)
        kap = json.loads(gut_text)
        kap["sim"]["anhang"]["win"]["sig"] = "00" * 64
        json.dump(kap, open(os.path.join(R, "versions.json"), "w"))
        r = U.py(os.path.join(R, neu_py), PRUEFEN, home + "p3", {}, R)
        ok(any("asset win" in b for b in r.get("bad") or []), "Selbsttest-Prüfung: falsche Signatur im Anhang gemeldet (%s)" % r.get("bad"))
        man3, out = signieren()
        ah3 = (man3.get("sim") or {}).get("anhang") or {}
        ok("win" not in ah3 and (ah3.get("linux") or {}).get("sig") == sig_vor["linux"] and "not signed before" in out,
           "ohne Datei und ohne gültige Signatur: Windows-Asset wird NICHT signiert (Linux bleibt)")
        open(os.path.join(R, "versions.json"), "w").write(gut_text)

        # ---- 3: devices against three servers
        cp, kp = U.zertifikat(tmp)
        env = {"SSL_CERT_FILE": cp}
        liste = os.path.join(tmp, "liste")
        blob = os.path.join(tmp, "blobs", "blob")
        os.makedirs(os.path.join(liste, "simulator3d"))
        os.makedirs(blob)
        for k in NAMEN:
            open(os.path.join(liste, "simulator3d", NAMEN[k]), "wb").write(fest[k])
        srv1, base1 = U.server(liste, cp, kp)
        srv3, base3 = U.server(os.path.dirname(blob), cp, kp)
        srv2, base2 = U.server(tmp, cp, kp, handler=U.Umleiter)
        srvs += [srv1, srv2, srv3]
        U.Umleiter.ziel = base3
        lokal = base2 + "/DonElektro/MotionWatch/releases/download/"

        def liste_setzen(aendern=None, vjson=None, text=gut_text):
            m = json.loads(text.replace(ECHT_BASIS, lokal))     # the address is not signed - it only has to follow from the number
            if aendern:
                aendern(m)
            json.dump(m, open(os.path.join(liste, "versions.json"), "w"))
            json.dump(vjson or vj, open(os.path.join(liste, "simulator3d", "version.json"), "w"))

        def blob_setzen(**anders):
            for k in NAMEN:
                p = os.path.join(blob, NAMEN[k])
                b = anders.get(k, asset[k])
                if b is None:
                    if os.path.isfile(p):
                        os.remove(p)
                else:
                    open(p, "wb").write(b)
        nr = [0]

        def geraet(datei, heim=""):
            nr[0] += 1
            d = os.path.join(tmp, "geraet_%d" % nr[0])
            p = U.geraet_anlegen(d, datei, pub)
            return p, heim or "%sg%d" % (home, nr[0])

        def wege():
            return sorted(set(("302:" + x.split(" ")[1].rsplit("/", 1)[-1]) if x.startswith("UMLEITUNG") else x.split(" ")[0] for x in U.Leise.log))

        liste_setzen()
        blob_setzen()
        neu_datei = os.path.join(R, neu_py)
        if alt_v:
            print("M1 ALTE MoveEye %s trifft auf die Liste mit Anhang" % alt_v)
            p, h = geraet(os.path.join(REPO, progs[alt_v]))
            U.Leise.log.clear()
            r = U.py(p, HOLEN, h, env, base1 + "/versions.json", lokal, "latest")
            ok(r.get("kennt") is False and all((r.get(k) or {}).get("ver") == va and r[k]["ready"] and r[k]["sha"] == sha(fest[k]) for k in NAMEN),
               "holt Sim %s (Windows + Linux) aus dem Repository wie immer, Prüfsumme wie signiert" % va)
            ok(not any(w.startswith("302:") for w in wege()), "fragt den Asset-Server nie (%s)" % ", ".join(wege()))
            lt = r.get("latest") or {}
            ok(lt.get("version") == va and "bitte zuerst MoveEye aktualisieren" in lt.get("notes", ""),
               "«Neueste Version» %s mit dem Hinweis: «…%s»" % (lt.get("version"), lt.get("notes", "")[-75:]))

        print("M2 NEUE MoveEye %s: Sim %s vom Asset-Server (Umleitung)" % (neu_v, vb))
        p, h_neu = geraet(neu_datei)
        U.Leise.log.clear()
        r = U.py(p, HOLEN, h_neu, env, base1 + "/versions.json", lokal, "latest")
        ok(r.get("kennt") is True and all((r.get(k) or {}).get("ver") == vb and r[k]["ready"] and r[k]["sha"] == sha(asset[k])
                                          and r[k]["url"] == lokal + "sim-%s/%s" % (vb, NAMEN[k]) for k in NAMEN),
           "holt Sim %s für Windows und Linux, Prüfsumme wie signiert (%s)" % (vb, "; ".join((r.get(k) or {}).get("msg", "") for k in NAMEN).strip("; ") or "ok"))
        ok(all("302:" + NAMEN[k] in wege() and "/blob/" + NAMEN[k] in wege() and "/simulator3d/" + NAMEN[k] not in wege() for k in NAMEN),
           "Weg: Asset-Adresse -> Umleitung -> Datei; das Paket im Repository wird nicht geladen")
        ok((r.get("latest") or {}).get("version") == vb, "«Neueste Version»: %s" % (r.get("latest") or {}).get("version"))
        ok("sim_manifest.json" in (r.get("dateien") or []), "geprüfter Block gemerkt (%s)" % ", ".join(r.get("dateien") or []))
        # restart without the list (address where nobody listens): the remembered block is checked again
        r = U.py(p, HOLEN, h_neu, env, "https://127.0.0.1:9/versions.json", lokal)
        ok(all((r.get(k) or {}).get("ver") == vb and r[k]["ready"] and r[k]["url"].startswith(lokal) for k in NAMEN),
           "Neustart ohne Netz: Sim %s bleibt bereit (gemerkter Block neu geprüft)" % vb)

        def nichts(was, teil, **kw):
            p, h = geraet(neu_datei)
            r = U.py(p, HOLEN, h, env, base1 + "/versions.json", kw.get("basis", lokal))
            reste = [x for x in r.get("dateien") or [] if x.endswith((".zip", ".part"))]
            ok(all((r.get(k) or {}).get("ver") == vb and not r[k]["ready"] and teil in r[k]["msg"] for k in NAMEN) and not reste,
               "%s: nichts bereit, nichts im Zwischenspeicher, Meldung «%s»" % (was, (r.get("win") or {}).get("msg", "")[:80]))

        print("M3 Asset fehlt · M4 Asset verändert · M6 Asset-Server nicht erreichbar")
        blob_setzen(win=None, linux=None)
        nichts("Asset fehlt (404)", "404")
        blob_setzen(win=asset["win"][:-1] + bytes([asset["win"][-1] ^ 1]), linux=asset["linux"][:-1] + bytes([asset["linux"][-1] ^ 1]))
        nichts("Asset verändert", "checksum")
        blob_setzen(win=asset["win"] + b"x" * 5000, linux=asset["linux"] + b"x" * 5000)
        nichts("Asset zu gross", "too large")
        blob_setzen()
        U.Umleiter.ziel = "https://127.0.0.1:9"
        nichts("Umleitung ins Leere", "refused")
        U.Umleiter.ziel = base3
        tot = "https://127.0.0.1:9/dl/"
        liste_setzen(lambda m: [m["sim"]["anhang"][k].update(url=tot + "sim-%s/%s" % (vb, NAMEN[k])) for k in NAMEN])
        nichts("Asset-Server antwortet nicht", "refused", basis=tot)

        def bleibt_a(was, aendern):
            liste_setzen(aendern)
            p, h = geraet(neu_datei)
            U.Leise.log.clear()
            r = U.py(p, HOLEN, h, env, base1 + "/versions.json", lokal)
            ok(all((r.get(k) or {}).get("ver") == va and r[k]["ready"] and r[k]["url"] == "" and r[k]["sha"] == sha(fest[k]) for k in NAMEN)
               and not any(w.startswith("302:") for w in wege()),
               "%s: Anhang nicht genommen, Sim %s aus dem Repository" % (was, va))

        print("M5 Signatur falsch · M7 fremde Adresse")
        bleibt_a("Signatur des Anhangs falsch", lambda m: [m["sim"]["anhang"][k].update(sig=m["sim"]["anhang"][k]["sig"][:-2] + "00"
                                                                                              if not m["sim"]["anhang"][k]["sig"].endswith("00") else m["sim"]["anhang"][k]["sig"][:-2] + "11") for k in NAMEN])
        bleibt_a("Prüfsumme im Anhang geändert", lambda m: [m["sim"]["anhang"][k].update(sha256="0" * 64) for k in NAMEN])
        bleibt_a("fremde Adresse", lambda m: [m["sim"]["anhang"][k].update(url=base3 + "/blob/" + NAMEN[k]) for k in NAMEN])
        bleibt_a("Adresse einer anderen Nummer", lambda m: [m["sim"]["anhang"][k].update(url=lokal + "sim-%s/%s" % (va, NAMEN[k])) for k in NAMEN])
        bleibt_a("Anhang mit dem Dateinamen des Repository-Pakets", lambda m: [m["sim"]["anhang"][k].update(file="simulator3d/" + NAMEN[k]) for k in NAMEN])

        # ---- M8: back to packages in the repository
        print("M8 Zurück ins Repository: Sim %s dort, kein Anhang mehr" % vc)
        S.linux_zip(R, vc)
        rc, out = vers("--sim-json", vc, "Zurück ins Repository")
        ok(rc != 0 and "Release-Assets" in out, "--sim-json ohne Absicht: abgelehnt")
        rc, out = vers("--sim-json", vc, "Zurück ins Repository", MW_SIM_IM_REPO="1")
        vjc = json.load(open(os.path.join(R, "simulator3d", "version.json"), encoding="utf-8"))
        manc, out2 = signieren()
        simc = manc.get("sim") or {}
        ok(rc == 0 and "anhang" not in vjc and "anhang" not in simc and simc.get("ver") == vc and simc["win"].get("sig"),
           "version.json und Liste ohne «anhang», «sim.win» / «sim.linux» = %s signiert" % vc)
        for k in NAMEN:
            shutil.copy(os.path.join(R, "simulator3d", NAMEN[k]), os.path.join(liste, "simulator3d", NAMEN[k]))
        liste_setzen(vjson=vjc, text=json.dumps(manc))
        blob_setzen(win=None, linux=None)
        p, _h = geraet(neu_datei)
        U.Leise.log.clear()
        # the device that had taken the asset version before; it sees the new list at its next look for updates (a block
        # remembered from before a restart is trusted for 10 minutes, 300 sim_manifest_refresh)
        r = U.py(p, HOLEN, h_neu, env, base1 + "/versions.json", lokal, "liste")
        ok(all((r.get(k) or {}).get("ver") == vc and r[k]["ready"] and r[k]["url"] == "" for k in NAMEN) and not any(w.startswith("302:") for w in wege()),
           "die neue MoveEye (hatte %s vom Asset) nimmt %s aus dem Repository - nur Liste und Repository geändert" % (vb, vc))

        # ---- 4: the public fetch of the workflows
        print("4  sim_anhang.py abruf (so holen Workflows und Tests das Linux-Paket)")
        blob_setzen()
        env_a = dict(os.environ, SSL_CERT_FILE=cp, NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
        for k_ in [k for k in list(env_a) if "proxy" in k.lower() and k.lower() != "no_proxy"]:
            env_a.pop(k_)
        ziel = os.path.join(tmp, "abruf", "linux.zip")
        url = lokal + "sim-%s/%s" % (vb, NAMEN["linux"])

        def abruf(size, s):
            r = subprocess.run([sys.executable, os.path.join(HIER, "sim_anhang.py"), "abruf", url, str(size), s, "--ziel", ziel],
                               env=env_a, capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()
        rc, out = abruf(len(asset["linux"]), sha(asset["linux"]))
        ok(rc == 0 and U.lesen(ziel) == asset["linux"], "über die Umleitung geholt, Grösse und SHA-256 stimmen")
        os.remove(ziel)
        rc, out = abruf(len(asset["linux"]), "0" * 64)
        ok(rc == 1 and "Prüfsumme" in out and os.listdir(os.path.dirname(ziel)) == [], "falsche Prüfsumme: abgelehnt, nichts bleibt liegen")
        blob_setzen(linux=None)
        rc, out = abruf(len(asset["linux"]), sha(asset["linux"]))
        ok(rc == 1 and "404" in out and os.listdir(os.path.dirname(ziel)) == [], "Asset fehlt: «%s», nichts bleibt liegen" % out[-60:])
    except Exception as e:                                       # a crash of the test is red, never green
        import traceback
        traceback.print_exc()
        ok(False, "Test läuft durch (%s: %s)" % (type(e).__name__, str(e)[:200]))
    finally:
        for s_ in srvs:
            try:
                s_.shutdown()
            except Exception:
                pass
        if a.behalten:
            print("Test-Ordner: " + tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + ("Sim-Anhang-Test OK" if not U.FEHLER else "%d FEHLER:\n  - %s" % (len(U.FEHLER), "\n  - ".join(U.FEHLER))))
    return 1 if U.FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
