#!/usr/bin/env python3
"""Übergangs-Test: ein Gerät mit der alten MoveEye (Standard 3.58.0 aus origin/main) holt die neue Version über eine
lokale HTTPS-Update-Quelle (Test-Server mit eigenem Zertifikat) - Programmdatei UND Zusatzdatei, signiert wie echt.

  python3 werkzeuge/update_uebergang_test.py                       # alt = origin/main:webcam_bewegung_3_58_0.py
  python3 werkzeuge/update_uebergang_test.py --alt DATEI.py [--neu-version 3.59.0]

Ablauf (ohne Netz, ohne den echten Schlüssel):
  * baut quelle/ in einem Test-Ordner als --neu-version (bauen.py --neue-version), erzeugt einen Test-Schlüssel und setzt
    dessen öffentlichen Teil in die alte UND die neue Programmdatei (sonst nehmen die Geräte nur den echten Schlüssel);
    versions.json mit make_manifest + Test-Schlüssel (Signatur über Programm und Zusatzdatei «data»).
  A  normal: update_check + update_install der ALTEN Version -> neue .py und ihre ZIP liegen beim Gerät; die neue
     Version lädt, alle Literale aus der ZIP, ihr Daten-Selbsttest (zusatz_selftest) ist grün.
  B  ZIP fehlt zuerst auf dem Server: das Update gelingt trotzdem, die neue Version startet im Kern (kein Absturz),
     holt die ZIP mit zusatz_holen(), sobald sie da ist; eine veränderte ZIP wird nie gespeichert.
  C  Update über einen Ordner (USB): Programm und ZIP kommen aus dem Ordner.
  D  nicht signiert / falsch signiert: die alte Version installiert nicht.
"""
import argparse
import datetime
import functools
import http.server
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
ECHT_PUB = "91d5eab3ab9f6e092d78081ca511144235cb9b22b770c3b1047e011d978bd416"


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text)
    if not bed:
        FEHLER.append(text)


LADEN = r'''
import json, os, sys
ns = {"__name__": "mw_uebergang", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
ns["SIM3D_BASE"] = ""                                      # test: never the internet as second source
'''


def py(datei, code, home, env_extra, *args):
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    env.update(env_extra, MOTIONWATCH_HOME=home, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    r = subprocess.run([sys.executable, "-c", LADEN + code, datei] + list(args), capture_output=True, text=True, env=env,
                       timeout=300, cwd=os.path.dirname(datei))
    out = r.stdout + r.stderr
    for ln in out.splitlines():
        if ln.startswith("RES "):
            return json.loads(ln[4:])
    print(out[-2500:])
    return {}


def zertifikat(ordner):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    import ipaddress
    k = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    c = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(k.public_key())
         .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
         .not_valid_after(now + datetime.timedelta(days=1))
         .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
         .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
         .sign(k, hashes.SHA256()))
    cp, kp = os.path.join(ordner, "cert.pem"), os.path.join(ordner, "key.pem")
    open(cp, "wb").write(c.public_bytes(serialization.Encoding.PEM))
    open(kp, "wb").write(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                         serialization.NoEncryption()))
    return cp, kp


class Leise(http.server.SimpleHTTPRequestHandler):
    log = []

    def log_message(self, fmt, *a):
        Leise.log.append(self.path.split("?")[0] + " " + str(a[1] if len(a) > 1 else ""))


def server(ordner, cp, kp):
    h = functools.partial(Leise, directory=ordner)
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cp, kp)
    s.socket = ctx.wrap_socket(s.socket, server_side=True)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "https://127.0.0.1:%d" % s.server_address[1]


def pub_setzen(pfad, pub):
    t = open(pfad, encoding="utf-8", newline="").read()
    t2, n = re.subn(r'^UPDATE_PUBKEY = "[0-9a-f]{64}"', 'UPDATE_PUBKEY = "%s"' % pub, t, count=1, flags=re.M)
    assert n == 1, pfad
    open(pfad, "w", encoding="utf-8", newline="").write(t2)


UPDATE = r'''
src = sys.argv[2]
ns["CFG"]["update_url"] = src
got = {}
ns["update_restart"] = lambda dst, version: got.update(dst=dst, version=version)    # test: no restart
items, msg = ns["update_check"]()
it = next((x for x in items if x["version"] == sys.argv[3]), {})
res = {"msg": msg, "found": bool(it), "signed": bool(it.get("signed")), "app": ns["APP_VERSION"],
       "new": (ns["STATE"].get("update_new") or {}).get("version")}
res["install"] = list(ns["update_install"](sys.argv[3])) if it else None
res["restart"] = got
print("RES " + json.dumps(res))
'''

NEU_LADEN = r'''
res = {"app": ns["APP_VERSION"], "ok": ns["ZD"]["ok"], "err": ns["ZD"]["err"], "miss": len(ns["ZD"]["miss"]),
       "used": ns["ZD"]["used"], "de": len(ns["DE"]), "fr": len(ns["TRX"].get("fr") or {})}
if ns["ZD"]["ok"]:
    try:
        res["selftest"] = ns["zusatz_selftest"]()
    except AssertionError as e:
        res["selftest"] = "FAIL " + str(e)
elif len(sys.argv) > 2:
    ns["CFG"]["update_url"] = sys.argv[2]
    res["holen"] = ns["zusatz_holen"]()
    res["da"] = os.path.isfile(os.path.join(ns["HERE"], ns["ZD_FILE"]))
print("RES " + json.dumps(res))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alt", default="", help="alte Programmdatei (Standard: origin/main:webcam_bewegung_3_58_0.py)")
    ap.add_argument("--neu-version", default="3.59.0")
    ap.add_argument("--behalten", action="store_true", help="Test-Ordner nicht löschen")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="mw_uebergang_")
    try:
        # ---- old program (+ its zip) ---------------------------------------------------------------------------------
        alt_dir = os.path.join(tmp, "alt")
        os.makedirs(alt_dir)
        if a.alt:
            alt = os.path.abspath(a.alt)
            shutil.copy(alt, alt_dir)
            z = re.search(r'^ZD_FILE = "([^"]+)"', open(alt, encoding="utf-8").read(), re.M)
            if z and os.path.isfile(os.path.join(os.path.dirname(alt), z.group(1))):
                shutil.copy(os.path.join(os.path.dirname(alt), z.group(1)), alt_dir)
        else:
            for fn in ("webcam_bewegung_3_58_0.py", "moveeye_daten_3_58_0.zip"):
                with open(os.path.join(alt_dir, fn), "wb") as f:
                    f.write(subprocess.run(["git", "show", "origin/main:" + fn], cwd=REPO, capture_output=True, check=True).stdout)
        alt_py = sorted(x for x in os.listdir(alt_dir) if x.endswith(".py"))[0]
        alt_v = re.search(r'^APP_VERSION = "([0-9.]+)"', open(os.path.join(alt_dir, alt_py), encoding="utf-8").read(), re.M).group(1)
        print("Alt: %s (%s), neu: %s" % (alt_py, alt_v, a.neu_version))

        # ---- new program: quelle/ built as --neu-version in a copy ----------------------------------------------------
        bau = os.path.join(tmp, "bau")
        shutil.copytree(os.path.join(REPO, "quelle"), os.path.join(bau, "quelle"))
        os.makedirs(os.path.join(bau, "werkzeuge"))
        os.makedirs(os.path.join(bau, "simulator3d"))
        shutil.copy(os.path.join(HIER, "bauen.py"), os.path.join(bau, "werkzeuge"))
        for fn in ("ui_gemeinsam.json", "fehler_katalog.json", "version.json"):
            shutil.copy(os.path.join(REPO, "simulator3d", fn), os.path.join(bau, "simulator3d"))
        r = subprocess.run([sys.executable, os.path.join(bau, "werkzeuge", "bauen.py"), "--neue-version", "Test Übergang",
                            "--version", a.neu_version], capture_output=True, text=True, cwd=bau)
        print("  " + " · ".join(x.strip() for x in r.stdout.strip().splitlines()[-3:]))
        u = a.neu_version.replace(".", "_")
        neu_py, neu_zip = "webcam_bewegung_%s.py" % u, "moveeye_daten_%s.zip" % u
        if r.returncode != 0 or not os.path.isfile(os.path.join(bau, neu_py)):
            print(r.stdout[-2000:] + r.stderr[-2000:])
            sys.exit("Bau der neuen Version fehlgeschlagen")
        shutil.rmtree(os.path.join(bau, "quelle"))

        # ---- test key, server folder, versions.json -------------------------------------------------------------------
        key = os.path.join(tmp, "test_schluessel.txt")
        open(key, "w").write(os.urandom(32).hex())
        home = os.path.join(tmp, "home")
        res = py(os.path.join(bau, neu_py), 'ns["_ED"].extend(ns["_ed25519_impl"]())\n'
                 'print("RES " + json.dumps(ns["_ED"][0](bytes.fromhex(open(sys.argv[2]).read().strip())).hex()))',
                 home + "0", {}, key)
        pub = res if isinstance(res, str) else ""
        ok(len(pub) == 64 and pub != ECHT_PUB, "Test-Schlüssel erzeugt (nicht der echte)")
        srv_dir = os.path.join(tmp, "server")
        os.makedirs(srv_dir)
        shutil.copy(os.path.join(bau, neu_py), srv_dir)
        shutil.copy(os.path.join(bau, neu_zip), srv_dir)
        pub_setzen(os.path.join(srv_dir, neu_py), pub)
        cp, kp = zertifikat(tmp)
        srv, base = server(srv_dir, cp, kp)
        env = {"SSL_CERT_FILE": cp}
        r = subprocess.run([sys.executable, os.path.join(srv_dir, neu_py), "--make-manifest", srv_dir, "--sign-key", key,
                            "--base-url", base], capture_output=True, text=True, cwd=srv_dir,
                           env=dict(os.environ, MOTIONWATCH_HOME=home + "m"))
        man = json.load(open(os.path.join(srv_dir, "versions.json")))
        e = man["versions"][0]
        ok(e["version"] == a.neu_version and e.get("sig") and (e.get("data") or {}).get("sig"),
           "versions.json: %s signiert, Zusatzdatei %s mit Grösse %s und Signatur" % (e["version"], (e.get("data") or {}).get("file"),
                                                                                    (e.get("data") or {}).get("size")))
        sz_alt = os.path.getsize(os.path.join(alt_dir, alt_py))
        print("  Programmdatei alt %d Bytes -> neu %d Bytes" % (sz_alt, os.path.getsize(os.path.join(srv_dir, neu_py))))

        def geraet(name):
            d = os.path.join(tmp, name)
            shutil.copytree(alt_dir, d)
            pub_setzen(os.path.join(d, alt_py), pub)
            return d

        # ---- A: normal ------------------------------------------------------------------------------------------------
        print("A  Update %s -> %s über HTTPS (Programm + Zusatzdatei)" % (alt_v, a.neu_version))
        d = geraet("geraet_a")
        Leise.log.clear()
        r = py(os.path.join(d, alt_py), UPDATE, home + "a", env, base + "/versions.json", a.neu_version)
        ok(r.get("found") and r.get("signed") and r.get("new") == a.neu_version, "alte Version sieht %s, signiert (%s)" % (a.neu_version, r.get("msg") or "ok"))
        ok(r.get("install") == [True, ""] and r.get("restart", {}).get("version") == a.neu_version, "installiert, Neustart in die neue Version (%s)" % r.get("install"))
        ok(open(os.path.join(d, neu_py), "rb").read() == open(os.path.join(srv_dir, neu_py), "rb").read(), "neue Programmdatei beim Gerät")
        ok(os.path.isfile(os.path.join(d, neu_zip)) and open(os.path.join(d, neu_zip), "rb").read() == open(os.path.join(srv_dir, neu_zip), "rb").read(),
           "Zusatzdatei gleich mitgeholt (Teil 397 der alten Version)")
        print("     Server: " + ", ".join(sorted(set(x.split(" ")[0] for x in Leise.log))))
        r = py(os.path.join(d, neu_py), NEU_LADEN, home + "a2", env)
        ok(r.get("app") == a.neu_version and r.get("ok") is True and r.get("miss") == 0, "neue Version lädt alle Literale aus der ZIP (%s)" % r.get("used"))
        ok(str(r.get("selftest", "")).startswith(str(r.get("used"))), "Daten-Selbsttest: %s" % r.get("selftest"))

        # ---- B: zip missing first --------------------------------------------------------------------------------------
        print("B  Zusatzdatei fehlt zuerst auf dem Server")
        d = geraet("geraet_b")
        os.rename(os.path.join(srv_dir, neu_zip), os.path.join(tmp, neu_zip))
        r = py(os.path.join(d, alt_py), UPDATE, home + "b", env, base + "/versions.json", a.neu_version)
        ok(r.get("install") == [True, ""], "Update gelingt ohne Zusatzdatei (%s)" % r.get("install"))
        ok(not os.path.isfile(os.path.join(d, neu_zip)), "keine Zusatzdatei beim Gerät")
        r = py(os.path.join(d, neu_py), NEU_LADEN, home + "b2", env, base + "/versions.json")
        ok(r.get("app") == a.neu_version and r.get("ok") is False and r.get("err") == "missing" and r.get("de", 0) > 1000,
           "neue Version startet im Kern, kein Absturz, Deutsch da (%s Texte)" % r.get("de"))
        ok(r.get("holen") and r.get("da") is False, "Nachladen solange sie fehlt: Meldung «%s», nichts gespeichert" % r.get("holen"))
        kap = bytearray(open(os.path.join(tmp, neu_zip), "rb").read())
        kap[1000] ^= 1
        open(os.path.join(srv_dir, neu_zip), "wb").write(bytes(kap))
        r = py(os.path.join(d, neu_py), NEU_LADEN, home + "b3", env, base + "/versions.json")
        ok("checksum" in str(r.get("holen")) and r.get("da") is False, "veränderte ZIP auf dem Server: abgelehnt (%s)" % r.get("holen"))
        shutil.copy(os.path.join(tmp, neu_zip), os.path.join(srv_dir, neu_zip))
        r = py(os.path.join(d, neu_py), NEU_LADEN, home + "b4", env, base + "/versions.json")
        ok(r.get("holen") == "" and r.get("da") is True, "richtige ZIP nachgeladen und gespeichert")
        r = py(os.path.join(d, neu_py), NEU_LADEN, home + "b5", env)
        ok(r.get("ok") is True and r.get("miss") == 0, "nach dem Neustart: alles da")

        # ---- C: USB folder ---------------------------------------------------------------------------------------------
        print("C  Update über einen Ordner (USB)")
        d = geraet("geraet_c")
        r = py(os.path.join(d, alt_py), UPDATE, home + "c", env, srv_dir, a.neu_version)
        ok(r.get("signed") and r.get("install") == [True, ""], "aus dem Ordner installiert (%s)" % r.get("install"))
        ok(os.path.isfile(os.path.join(d, neu_zip)), "Zusatzdatei aus dem Ordner mitgeholt")

        # ---- D: wrong signature ----------------------------------------------------------------------------------------
        print("D  falsche Signatur")
        d = geraet("geraet_d")
        man2 = json.loads(json.dumps(man))
        man2["versions"][0]["sig"] = man2["versions"][0]["sig"][:-2] + ("00" if not man2["versions"][0]["sig"].endswith("00") else "11")
        json.dump(man2, open(os.path.join(srv_dir, "versions.json"), "w"))
        r = py(os.path.join(d, alt_py), UPDATE, home + "d", env, base + "/versions.json", a.neu_version)
        ok(r.get("found") and not r.get("signed") and r.get("install") and r["install"][0] is False and not os.path.isfile(os.path.join(d, neu_py)),
           "nicht installiert: %s" % (r.get("install") or [None, None])[1])
        srv.shutdown()
    finally:
        if not a.behalten:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print("Test-Ordner: " + tmp)
    print("\n" + ("Übergangs-Test OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
