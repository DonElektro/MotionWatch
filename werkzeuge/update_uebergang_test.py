#!/usr/bin/env python3
"""Übergangs-Test: ein Gerät mit einer alten MoveEye holt die neue Version über eine lokale HTTPS-Update-Quelle
(Test-Server mit eigenem Zertifikat) - Programmdatei UND Zusatzdatei, signiert wie echt. Läuft im CI (Job «moveeye»).

  python3 werkzeuge/update_uebergang_test.py                 # beide Teile: «uebergang» und «stand»
  python3 werkzeuge/update_uebergang_test.py --nur uebergang [--alt DATEI.py] [--neu-version X.Y.Z]
  python3 werkzeuge/update_uebergang_test.py --nur stand [--streng] [--ordner ORDNER] [--ohne-netz]

«Alt» wird berechnet, nichts ist fest eingetragen: die älteste Version mit Zusatzdatei, die noch im Repository liegt
(volle Fälle A-D), und die Brücke (Datei des Eintrags «bridge» in versions.json, heute 3.0.2 - eine Datei ohne Zusatzdatei,
eigener Fall Br). «Neu» ist die Nummer nach der neuesten Datei im Repository.

Teil «uebergang» (ohne Netz, ohne den echten Schlüssel - der Test erzeugt einen Wegwerf-Schlüssel):
  * baut quelle/ in einem Test-Ordner als --neu-version (bauen.py --neue-version), setzt den öffentlichen Teil des
    Wegwerf-Schlüssels in die alte UND die neue Programmdatei (sonst nehmen die Geräte nur den echten Schlüssel);
    versions.json mit make_manifest + Wegwerf-Schlüssel (Signatur über Programm und Zusatzdatei «data»).
  A  normal: update_check + update_install der ALTEN Version -> neue .py und ihre ZIP liegen beim Gerät; die neue
     Version lädt, alle Literale aus der ZIP, ihr Daten-Selbsttest (zusatz_selftest) ist grün.
  B  ZIP fehlt zuerst auf dem Server: das Update gelingt trotzdem, die neue Version startet im Kern (kein Absturz),
     holt die ZIP mit zusatz_holen(), sobald sie da ist; eine veränderte ZIP wird nie gespeichert.
  C  Update über einen Ordner (USB): Programm und ZIP kommen aus dem Ordner.
  D  nicht signiert / falsch signiert: die alte Version installiert nicht.
  Br Brücke: sie holt nur die Programmdatei (kennt keine Zusatzdatei); die neue Version startet im Kern und holt ihre
     ZIP selbst neben versions.json; falsche Signatur: nicht installiert.
  U  Ablage «url» (Review Nov. 2026, heute NICHT in Gebrauch - zeigt, was die Geräte im Feld können, bevor je eine
     Version als Release-Asset abgelegt wird): versions.json liegt auf Server 1, die neue Programmdatei und ihre ZIP nur
     auf einem zweiten Server («Asset-Server»), der wie GitHub auf einen dritten umleitet (302). Dazwischen stehen alle
     Versionen des Repositorys in der Liste (das Gerät hat mehrere Versionen übersprungen).
     U1 ältestes Gerät: nimmt die neueste, Programm + ZIP vom Asset-Server.  U2 Brücke: Programm vom Asset-Server, die
     neue Version findet ihre ZIP über ihren Eintrag in versions.json (Teil 397 _zd_entry_urls).
     U3 Asset fehlt (404) · U4 Asset verändert (Prüfsumme) · U5 falsche Signatur · U6 Asset-Server nicht erreichbar:
     nichts wird installiert, das Gerät bleibt auf seiner Version. Die echte Umleitung von GitHub ist hier NICHT getestet.

Teil «stand» (der veröffentlichte Stand, mit dem ECHTEN öffentlichen Schlüssel - der geheime wird nie gebraucht):
  S1 jeder Eintrag in versions.json: Programmdatei da (im Ordner, sonst über «url»), Grösse, SHA-256, Signatur gültig;
     ebenso die Zusatzdatei («data») und sie ist die, die in der signierten Programmdatei steht (ZD_FILE / ZD_SHA256);
     die Zusatzdatei liegt dort, wo die Geräte sie suchen (neben der Programmdatei UND neben versions.json); der
     Brücken-Eintrag ist da; jede Programmdatei trägt den echten öffentlichen Schlüssel.
  S2 das älteste Gerät und die Brücke (unverändert, echter Schlüssel) holen die neueste Version aus genau diesem Stand.
  Ohne --streng (Arbeitszweige): ist die neueste Programmdatei nach dem letzten Release neu gebaut (anderer Inhalt als in
  versions.json), wird NUR dieser eine Eintrag übersprungen und das laut gemeldet. Mit --streng (CI auf main) ist das ein
  Fehler - auf main gibt es kein «grün durch Überspringen».
"""
import argparse
import datetime
import functools
import hashlib
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
import urllib.request

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


class Umleiter(Leise):
    """stands in for github.com/…/releases/download/<tag>/<file>: answers 302 to an other server (ziel), like GitHub does"""
    ziel = ""

    def do_GET(self):
        Leise.log.append("UMLEITUNG " + self.path.split("?")[0])
        if not Umleiter.ziel:
            self.send_error(404)
            return
        self.send_response(302)
        self.send_header("Location", Umleiter.ziel + "/blob/" + self.path.split("?")[0].rsplit("/", 1)[-1] + "?sig=test")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_HEAD = do_GET


def server(ordner, cp, kp, port=0, handler=None):
    h = functools.partial(handler or Leise, directory=ordner)
    s = http.server.ThreadingHTTPServer(("127.0.0.1", port), h)
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


SIGS = r'''
rows = json.load(open(sys.argv[2], encoding="utf-8"))
print("RES " + json.dumps({"pub": ns["UPDATE_PUBKEY"], "ok": [bool(ns["sig_ok"](*r)) for r in rows]}))
'''

VFILE = re.compile(r"^webcam_bewegung_(\d{1,3})_(\d{1,3})_(\d{1,3})\.py$")
ZFILE = re.compile(r"^moveeye_daten_\d{1,3}_\d{1,3}_\d{1,3}\.zip$")
MAX_BYTES = 64 * 1024 * 1024


def vkey(v):
    return tuple(int(x) for x in str(v).split("."))


def lesen(pfad):
    with open(pfad, "rb") as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def hinweis(text):
    """a skipped / weaker check is never silent: line in the log and a warning in the GitHub summary"""
    print("  HINWEIS " + text)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning title=Update-Test::" + text)


def programme(ordner):
    """{version: file name} of the program files in a folder"""
    out = {}
    for n in os.listdir(ordner):
        m = VFILE.match(n)
        if m:
            out[".".join(str(int(x)) for x in m.groups())] = n
    return out


def zd_von(text):
    """(ZD_FILE, ZD_SHA256) written into a program text - ("", "") for a file without data zip (as _zd_name_of, part 397)"""
    m = re.search(r'^ZD_FILE = "(moveeye_daten_\d{1,3}_\d{1,3}_\d{1,3}\.zip)"\s*\nZD_SHA256 = "([0-9a-f]{64})"', text, re.M)
    return (m.group(1), m.group(2)) if m else ("", "")


def alte_geraete(ordner, ausser=""):
    """(oldest program file with a data zip, bridge file) of a folder - computed, nothing is written down here.
    The bridge is the entry «bridge» of versions.json; without such an entry: the oldest file without data zip."""
    progs = programme(ordner)
    mit, ohne = [], []
    for v in sorted(progs, key=vkey):
        if v == ausser:
            continue
        name = zd_von(lesen(os.path.join(ordner, progs[v])).decode("utf-8", "replace"))[0]
        (mit if name and os.path.isfile(os.path.join(ordner, name)) else ohne if not name else []).append(v)
    br = ""
    try:
        man = json.load(open(os.path.join(ordner, "versions.json"), encoding="utf-8"))
        br = next((str(e.get("version")) for e in man.get("versions", []) if e.get("bridge") and str(e.get("version")) in ohne), "")
    except (OSError, ValueError):
        pass
    br = br or (ohne[0] if ohne else "")
    return (os.path.join(ordner, progs[mit[0]]) if mit else ""), (os.path.join(ordner, progs[br]) if br else "")


def geraet_anlegen(ziel, alt_pfad, pub=""):
    """a device folder: the old program file and its data zip (if it has one); pub = throwaway key instead of the real one"""
    os.makedirs(ziel)
    shutil.copy(alt_pfad, ziel)
    name = zd_von(lesen(alt_pfad).decode("utf-8", "replace"))[0]
    if name and os.path.isfile(os.path.join(os.path.dirname(alt_pfad), name)):
        shutil.copy(os.path.join(os.path.dirname(alt_pfad), name), ziel)
    p = os.path.join(ziel, os.path.basename(alt_pfad))
    if pub:
        pub_setzen(p, pub)
    return p


def version_von(pfad):
    return re.search(r'^APP_VERSION = "([0-9.]+)"', lesen(pfad).decode("utf-8", "replace"), re.M).group(1)


def kennt_zusatz(pfad):
    """does this old program fetch the data zip together with the program (part 397)? The bridge does not."""
    return "def zusatz_mitholen" in lesen(pfad).decode("utf-8", "replace")


def ca_buendel(tmp, cp):
    """the test certificate plus the CAs of the system (only needed when versions.json names an outside «url»)"""
    ziel = os.path.join(tmp, "ca.pem")
    teile = [lesen(cp)]
    for kand in (ssl.get_default_verify_paths().cafile, "/etc/ssl/certs/ca-certificates.crt"):
        if kand and os.path.isfile(kand):
            teile.append(lesen(kand))
            break
    open(ziel, "wb").write(b"\n".join(teile))
    return ziel


# ======================================================================================================================
# part «uebergang»: old device -> freshly built new version, throwaway key
# ======================================================================================================================
def uebergang(a, tmp):
    progs = programme(REPO)
    if a.alt:
        alte = [os.path.abspath(a.alt)]
    else:
        voll, br = alte_geraete(REPO)
        alte = [x for x in (voll, br) if x]
        ok(bool(voll), "älteste Version mit Zusatzdatei im Repository gefunden")
        ok(bool(br), "Brücke im Repository gefunden")
    if not alte:
        return
    neu_v = a.neu_version
    if not neu_v:                                           # the number after the newest file in the repository
        x, y, _z = max((vkey(v) for v in progs), default=(3, 0, 0))
        neu_v = "%d.%d.0" % ((x, y + 1) if y < 999 else (x + 1, 0))
    print("Alt: %s · neu: %s (aus quelle/ gebaut)" % (", ".join("%s (%s)" % (os.path.basename(p), version_von(p)) for p in alte), neu_v))

    # ---- new program: quelle/ built as neu_v in a copy ------------------------------------------------------------------
    bau = os.path.join(tmp, "bau")
    shutil.copytree(os.path.join(REPO, "quelle"), os.path.join(bau, "quelle"))
    os.makedirs(os.path.join(bau, "werkzeuge"))
    os.makedirs(os.path.join(bau, "simulator3d"))
    shutil.copy(os.path.join(HIER, "bauen.py"), os.path.join(bau, "werkzeuge"))
    for fn in ("ui_gemeinsam.json", "fehler_katalog.json", "version.json"):
        shutil.copy(os.path.join(REPO, "simulator3d", fn), os.path.join(bau, "simulator3d"))
    r = subprocess.run([sys.executable, os.path.join(bau, "werkzeuge", "bauen.py"), "--neue-version", "Test Übergang",
                        "--version", neu_v], capture_output=True, text=True, cwd=bau)
    print("  " + " · ".join(x.strip() for x in r.stdout.strip().splitlines()[-3:]))
    u = neu_v.replace(".", "_")
    neu_py, neu_zip = "webcam_bewegung_%s.py" % u, "moveeye_daten_%s.zip" % u
    if r.returncode != 0 or not os.path.isfile(os.path.join(bau, neu_py)) or not os.path.isfile(os.path.join(bau, neu_zip)):
        print(r.stdout[-2000:] + r.stderr[-2000:])
        ok(False, "Bau der neuen Version %s (bauen.py --neue-version)" % neu_v)
        return
    shutil.rmtree(os.path.join(bau, "quelle"))
    import zipfile
    with zipfile.ZipFile(os.path.join(bau, neu_zip)) as z:  # Ablage: stored, so that git keeps only the difference per version
        zi = z.getinfo("daten.json")
    ok(zi.compress_type == zipfile.ZIP_STORED and os.path.getsize(os.path.join(bau, neu_zip)) < 32 * 1024 * 1024,
       "neue Zusatzdatei ungepackt (%.1f MB, Geräte nehmen bis 64 MiB) - alte Geräte mit gepackter ZIP holen sie in A / B / C"
       % (os.path.getsize(os.path.join(bau, neu_zip)) / 1e6))

    # ---- throwaway key, server folder, versions.json --------------------------------------------------------------------
    key = os.path.join(tmp, "test_schluessel.txt")
    open(key, "w").write(os.urandom(32).hex())
    home = os.path.join(tmp, "home")
    res = py(os.path.join(bau, neu_py), 'ns["_ED"].extend(ns["_ed25519_impl"]())\n'
             'print("RES " + json.dumps(ns["_ED"][0](bytes.fromhex(open(sys.argv[2]).read().strip())).hex()))',
             home + "0", {}, key)
    pub = res if isinstance(res, str) else ""
    ok(len(pub) == 64 and pub != ECHT_PUB, "Wegwerf-Schlüssel erzeugt (nicht der echte)")
    if len(pub) != 64:
        return
    srv_dir = os.path.join(tmp, "server")
    os.makedirs(srv_dir)
    shutil.copy(os.path.join(bau, neu_py), srv_dir)
    shutil.copy(os.path.join(bau, neu_zip), srv_dir)
    pub_setzen(os.path.join(srv_dir, neu_py), pub)
    cp, kp = zertifikat(tmp)
    srv, base = server(srv_dir, cp, kp)
    env = {"SSL_CERT_FILE": cp}
    try:
        r = subprocess.run([sys.executable, os.path.join(srv_dir, neu_py), "--make-manifest", srv_dir, "--sign-key", key,
                            "--base-url", base], capture_output=True, text=True, cwd=srv_dir,
                           env=dict(os.environ, MOTIONWATCH_HOME=home + "m"))
        try:
            man = json.load(open(os.path.join(srv_dir, "versions.json")))
            e = man["versions"][0]
        except (OSError, ValueError, LookupError):
            print(r.stdout[-1500:] + r.stderr[-1500:])
            ok(False, "versions.json mit --make-manifest und dem Wegwerf-Schlüssel")
            return
        ok(e["version"] == neu_v and e.get("sig") and (e.get("data") or {}).get("sig"),
           "versions.json: %s signiert, Zusatzdatei %s mit Grösse %s und Signatur" % (e["version"], (e.get("data") or {}).get("file"),
                                                                                    (e.get("data") or {}).get("size")))
        man_txt = json.dumps(man)
        zip_gut = lesen(os.path.join(srv_dir, neu_zip))
        nr = [0]

        def geraet(alt_pfad):
            nr[0] += 1
            d = os.path.join(tmp, "geraet_%d" % nr[0])
            return d, geraet_anlegen(d, alt_pfad, pub), "%s%d" % (home, nr[0])

        def zuruecksetzen():                                # every case starts from the same server
            open(os.path.join(srv_dir, "versions.json"), "w").write(man_txt)
            open(os.path.join(srv_dir, neu_zip), "wb").write(zip_gut)

        def falsche_signatur(alt_pfad, alt_v):
            d, p, h = geraet(alt_pfad)
            man2 = json.loads(man_txt)
            s = man2["versions"][0]["sig"]
            man2["versions"][0]["sig"] = s[:-2] + ("00" if not s.endswith("00") else "11")
            json.dump(man2, open(os.path.join(srv_dir, "versions.json"), "w"))
            r = py(p, UPDATE, h, env, base + "/versions.json", neu_v)
            ok(bool(r.get("found") and not r.get("signed") and r.get("install") and r["install"][0] is False
                    and not os.path.isfile(os.path.join(d, neu_py))),
               "%s: falsche Signatur -> nicht installiert: %s" % (alt_v, (r.get("install") or [None, None])[1]))
            zuruecksetzen()

        for alt_pfad in alte:
            alt_v = version_von(alt_pfad)
            ok(vkey(alt_v) < vkey(neu_v), "%s ist älter als %s" % (alt_v, neu_v))
            print("  Programmdatei %s %d Bytes -> neu %d Bytes" % (alt_v, os.path.getsize(alt_pfad), os.path.getsize(os.path.join(srv_dir, neu_py))))
            zuruecksetzen()
            if not kennt_zusatz(alt_pfad):
                # ---- Br: bridge - one file, knows no data zip --------------------------------------------------------
                print("Br Brücke %s -> %s über HTTPS (holt nur das Programm, die neue Version holt ihre Zusatzdatei selbst)" % (alt_v, neu_v))
                d, p, h = geraet(alt_pfad)
                Leise.log.clear()
                r = py(p, UPDATE, h, env, base + "/versions.json", neu_v)
                ok(bool(r.get("found") and r.get("signed") and r.get("new") == neu_v), "Brücke sieht %s, signiert (%s)" % (neu_v, r.get("msg") or "ok"))
                ok(r.get("install") == [True, ""] and r.get("restart", {}).get("version") == neu_v, "installiert, Neustart in die neue Version (%s)" % r.get("install"))
                ok(os.path.isfile(os.path.join(d, neu_py)) and lesen(os.path.join(d, neu_py)) == lesen(os.path.join(srv_dir, neu_py)), "neue Programmdatei beim Gerät")
                ok(not os.path.isfile(os.path.join(d, neu_zip)), "Zusatzdatei kommt nicht mit (die Brücke kennt sie nicht)")
                print("     Server: " + ", ".join(sorted(set(x.split(" ")[0] for x in Leise.log))))
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b", env, base + "/versions.json")
                ok(r.get("app") == neu_v and r.get("ok") is False and r.get("de", 0) > 1000, "neue Version startet im Kern, kein Absturz (%s Texte)" % r.get("de"))
                ok(r.get("holen") == "" and r.get("da") is True, "sie holt ihre Zusatzdatei selbst neben versions.json (%s)" % (r.get("holen") or "ok"))
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "c", env)
                ok(r.get("ok") is True and r.get("miss") == 0, "nach dem Neustart: alles da")
                falsche_signatur(alt_pfad, alt_v)
                continue

            # ---- A: normal ----------------------------------------------------------------------------------------------
            print("A  Update %s -> %s über HTTPS (Programm + Zusatzdatei)" % (alt_v, neu_v))
            d, p, h = geraet(alt_pfad)
            Leise.log.clear()
            r = py(p, UPDATE, h, env, base + "/versions.json", neu_v)
            ok(bool(r.get("found") and r.get("signed") and r.get("new") == neu_v), "alte Version sieht %s, signiert (%s)" % (neu_v, r.get("msg") or "ok"))
            ok(r.get("install") == [True, ""] and r.get("restart", {}).get("version") == neu_v, "installiert, Neustart in die neue Version (%s)" % r.get("install"))
            ok(os.path.isfile(os.path.join(d, neu_py)) and lesen(os.path.join(d, neu_py)) == lesen(os.path.join(srv_dir, neu_py)), "neue Programmdatei beim Gerät")
            ok(os.path.isfile(os.path.join(d, neu_zip)) and lesen(os.path.join(d, neu_zip)) == zip_gut,
               "Zusatzdatei gleich mitgeholt (Teil 397 der alten Version)")
            print("     Server: " + ", ".join(sorted(set(x.split(" ")[0] for x in Leise.log))))
            r = py(os.path.join(d, neu_py), NEU_LADEN, h + "n", env)
            ok(r.get("app") == neu_v and r.get("ok") is True and r.get("miss") == 0, "neue Version lädt alle Literale aus der ZIP (%s)" % r.get("used"))
            ok(str(r.get("selftest", "")).startswith(str(r.get("used"))), "Daten-Selbsttest: %s" % r.get("selftest"))

            # ---- B: zip missing first ---------------------------------------------------------------------------------
            print("B  Zusatzdatei fehlt zuerst auf dem Server")
            d, p, h = geraet(alt_pfad)
            os.remove(os.path.join(srv_dir, neu_zip))
            r = py(p, UPDATE, h, env, base + "/versions.json", neu_v)
            ok(r.get("install") == [True, ""], "Update gelingt ohne Zusatzdatei (%s)" % r.get("install"))
            ok(not os.path.isfile(os.path.join(d, neu_zip)), "keine Zusatzdatei beim Gerät")
            r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b2", env, base + "/versions.json")
            ok(r.get("app") == neu_v and r.get("ok") is False and r.get("err") == "missing" and r.get("de", 0) > 1000,
               "neue Version startet im Kern, kein Absturz, Deutsch da (%s Texte)" % r.get("de"))
            ok(bool(r.get("holen")) and r.get("da") is False, "Nachladen solange sie fehlt: Meldung «%s», nichts gespeichert" % r.get("holen"))
            kap = bytearray(zip_gut)
            kap[1000] ^= 1
            open(os.path.join(srv_dir, neu_zip), "wb").write(bytes(kap))
            r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b3", env, base + "/versions.json")
            ok("checksum" in str(r.get("holen")) and r.get("da") is False, "veränderte ZIP auf dem Server: abgelehnt (%s)" % r.get("holen"))
            zuruecksetzen()
            r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b4", env, base + "/versions.json")
            ok(r.get("holen") == "" and r.get("da") is True, "richtige ZIP nachgeladen und gespeichert")
            r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b5", env)
            ok(r.get("ok") is True and r.get("miss") == 0, "nach dem Neustart: alles da")

            # ---- C: USB folder ----------------------------------------------------------------------------------------
            print("C  Update über einen Ordner (USB)")
            d, p, h = geraet(alt_pfad)
            r = py(p, UPDATE, h, env, srv_dir, neu_v)
            ok(bool(r.get("signed")) and r.get("install") == [True, ""], "aus dem Ordner installiert (%s)" % r.get("install"))
            ok(os.path.isfile(os.path.join(d, neu_zip)), "Zusatzdatei aus dem Ordner mitgeholt")

            # ---- D: wrong signature -----------------------------------------------------------------------------------
            print("D  falsche Signatur")
            falsche_signatur(alt_pfad, alt_v)
        if not a.alt or a.ablage:
            ablage_url(tmp, alte, neu_v, neu_py, neu_zip, srv_dir, key, pub, cp, kp, env, home)
    finally:
        srv.shutdown()


def ablage_url(tmp, alte, neu_v, neu_py, neu_zip, srv_dir, key, pub, cp, kp, env, home):
    """part U (see the head): the newest version only as «Release asset» (second server behind a redirect), named by «url»"""
    print("U  Ablage «url»: neueste Version nur auf dem Asset-Server (mit Umleitung), versions.json auf Server 1")
    liste = os.path.join(tmp, "u_liste")                    # server 1: versions.json + the older versions of the repository
    blob = os.path.join(tmp, "u_blob", "blob")              # server 3: where the redirect ends
    bau_m = os.path.join(tmp, "u_manifest")                 # only to write the list: every program file in one folder
    for d in (liste, blob, bau_m):
        os.makedirs(d)
    progs = programme(REPO)
    zwischen = []
    for v in sorted(progs, key=vkey):                       # the versions in between (signed with the throwaway key, no «url»)
        zn = zd_von(lesen(os.path.join(REPO, progs[v])).decode("utf-8", "replace"))[0]
        if vkey(v) >= vkey(neu_v) or not zn or not os.path.isfile(os.path.join(REPO, zn)):
            continue
        shutil.copy(os.path.join(REPO, progs[v]), bau_m)
        pub_setzen(os.path.join(bau_m, progs[v]), pub)
        shutil.copy(os.path.join(bau_m, progs[v]), liste)
        os.symlink(os.path.join(REPO, zn), os.path.join(liste, zn))
        zwischen.append(v)
    shutil.copy(os.path.join(srv_dir, neu_py), bau_m)
    shutil.copy(os.path.join(srv_dir, neu_zip), bau_m)
    prog_gut, zip_gut = lesen(os.path.join(srv_dir, neu_py)), lesen(os.path.join(srv_dir, neu_zip))

    def blob_setzen(prog=prog_gut, zp=zip_gut):
        for n, b in ((neu_py, prog), (neu_zip, zp)):
            if b is None:
                if os.path.isfile(os.path.join(blob, n)):
                    os.remove(os.path.join(blob, n))
            else:
                open(os.path.join(blob, n), "wb").write(b)

    blob_setzen()
    srv1, base1 = server(liste, cp, kp)
    srv3, base3 = server(os.path.dirname(blob), cp, kp)
    srv2, base2 = server(tmp, cp, kp, handler=Umleiter)     # the «asset host»: every address answers with a redirect
    Umleiter.ziel = base3
    asset = "%s/DonElektro/MotionWatch/releases/download/mw-%s/" % (base2, neu_v)
    try:
        r = subprocess.run([sys.executable, os.path.join(bau_m, neu_py), "--make-manifest", bau_m, "--sign-key", key],
                           capture_output=True, text=True, cwd=bau_m, env=dict(os.environ, MOTIONWATCH_HOME=home + "um"))
        try:
            man = json.load(open(os.path.join(bau_m, "versions.json")))
            e = next(x for x in man["versions"] if x["version"] == neu_v)
        except (OSError, ValueError, LookupError):
            print(r.stdout[-1500:] + r.stderr[-1500:])
            ok(False, "U: versions.json mit allen Versionen dazwischen")
            return
        e["url"] = asset + neu_py                           # «url» is not signed: the signature covers version, file name, checksum
        e["data"]["url"] = asset + neu_zip
        man_txt = json.dumps(man)
        ok(len(man["versions"]) == len(zwischen) + 1 and all(x.get("sig") for x in man["versions"]) and not any(x.get("url") for x in man["versions"] if x is not e),
           "Liste: %d Versionen signiert, nur %s mit «url» (Asset-Server), %d dazwischen ohne" % (len(man["versions"]), neu_v, len(zwischen)))
        nr = [0]

        def geraet(alt_pfad):
            nr[0] += 1
            d = os.path.join(tmp, "u_geraet_%d" % nr[0])
            return d, geraet_anlegen(d, alt_pfad, pub), "%su%d" % (home, nr[0])

        def liste_setzen(aendern=None):
            m2 = json.loads(man_txt)
            if aendern:
                aendern(next(x for x in m2["versions"] if x["version"] == neu_v))
            json.dump(m2, open(os.path.join(liste, "versions.json"), "w"))

        def nicht_installiert(alt_pfad, was, teil):
            d, p, h = geraet(alt_pfad)
            r = py(p, UPDATE, h, env, base1 + "/versions.json", neu_v)
            inst = r.get("install") or [None, ""]
            ok(bool(r.get("found")) and inst[0] is False and teil in str(inst[1]) and not os.path.isfile(os.path.join(d, neu_py))
               and not os.path.isfile(os.path.join(d, neu_py + ".part")) and not r.get("restart"),
               "%s %s: nicht installiert, kein Neustart, keine Datei beim Gerät (%s)" % (version_von(alt_pfad), was, str(inst[1])[:90]))

        for alt_pfad in alte:
            alt_v = version_von(alt_pfad)
            liste_setzen(); blob_setzen()
            d, p, h = geraet(alt_pfad)
            Leise.log.clear()
            r = py(p, UPDATE, h, env, base1 + "/versions.json", neu_v)
            wege = sorted(set(x.split(" ")[0] if not x.startswith("UMLEITUNG") else "302:" + x.split(" ")[1].rsplit("/", 1)[-1] for x in Leise.log))
            if kennt_zusatz(alt_pfad):
                print("U1 %s -> %s (%d Versionen übersprungen)" % (alt_v, neu_v, len([v for v in zwischen if vkey(v) > vkey(alt_v)])))
                ok(bool(r.get("found") and r.get("signed")) and r.get("new") == neu_v, "sieht %s als neueste, signiert (angeboten: %s)" % (neu_v, r.get("new")))
                ok(r.get("install") == [True, ""] and r.get("restart", {}).get("version") == neu_v, "installiert, Neustart in %s (%s)" % (neu_v, r.get("install")))
                ok(os.path.isfile(os.path.join(d, neu_py)) and lesen(os.path.join(d, neu_py)) == prog_gut, "Programmdatei vom Asset-Server (über die Umleitung)")
                ok(os.path.isfile(os.path.join(d, neu_zip)) and lesen(os.path.join(d, neu_zip)) == zip_gut, "Zusatzdatei gleich mitgeholt - neben der Programmdatei auf dem Asset-Server")
                ok("302:" + neu_py in wege and "302:" + neu_zip in wege and "/" + neu_py not in wege, "Weg: " + ", ".join(wege))
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "n", env)
                ok(r.get("app") == neu_v and r.get("ok") is True and r.get("miss") == 0, "neue Version lädt alle Literale (%s)" % r.get("used"))
                # ---- U3 / U4 / U6 for a device that fetches both files
                print("U3 Asset fehlt")
                blob_setzen(prog=None)
                nicht_installiert(alt_pfad, "Programmdatei fehlt auf dem Asset-Server (404)", "404")
                blob_setzen(zp=None)
                d, p, h = geraet(alt_pfad)
                r = py(p, UPDATE, h, env, base1 + "/versions.json", neu_v)
                ok(r.get("install") == [True, ""] and not os.path.isfile(os.path.join(d, neu_zip)), "nur die ZIP fehlt: Programm installiert, keine ZIP (%s)" % r.get("install"))
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b", env, base1 + "/versions.json")
                ok(r.get("ok") is False and r.get("de", 0) > 1000 and bool(r.get("holen")) and r.get("da") is False,
                   "neue Version startet im Kern und meldet: «%s»" % r.get("holen"))
                blob_setzen()
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b2", env, base1 + "/versions.json")
                ok(r.get("holen") == "" and r.get("da") is True, "sobald das Asset da ist: ZIP über den eigenen Eintrag in versions.json geholt")
                print("U4 Asset verändert")
                blob_setzen(prog=prog_gut + b"\n# x\n")
                nicht_installiert(alt_pfad, "veränderte Programmdatei", "checksum")
                kap = bytearray(zip_gut)
                kap[2000] ^= 1
                blob_setzen(zp=bytes(kap))
                d, p, h = geraet(alt_pfad)
                r = py(p, UPDATE, h, env, base1 + "/versions.json", neu_v)
                ok(r.get("install") == [True, ""] and not os.path.isfile(os.path.join(d, neu_zip)), "veränderte ZIP: nie gespeichert (das Programm selbst ist echt und wird installiert)")
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "c", env, base1 + "/versions.json")
                ok("checksum" in str(r.get("holen")) and r.get("da") is False, "die neue Version lehnt sie auch ab (%s)" % r.get("holen"))
                blob_setzen()
                print("U5 falsche Signatur")
                liste_setzen(lambda x: x.update(sig=x["sig"][:-2] + ("00" if not x["sig"].endswith("00") else "11")))
                nicht_installiert(alt_pfad, "falsche Signatur", "not signed")
                print("U6 Asset-Server nicht erreichbar")
                Umleiter.ziel = "https://127.0.0.1:9"       # the redirect ends where nobody listens
                liste_setzen()
                nicht_installiert(alt_pfad, "Umleitung ins Leere", "update failed")
                Umleiter.ziel = base3
                liste_setzen(lambda x: x.update(url="https://127.0.0.1:9/mw/" + neu_py))
                nicht_installiert(alt_pfad, "Asset-Server antwortet nicht", "update failed")
                liste_setzen()
            else:
                print("U2 Brücke %s -> %s" % (alt_v, neu_v))
                ok(bool(r.get("found") and r.get("signed")) and r.get("new") == neu_v, "sieht %s als neueste, signiert (angeboten: %s)" % (neu_v, r.get("new")))
                ok(r.get("install") == [True, ""] and lesen(os.path.join(d, neu_py)) == prog_gut, "Programmdatei vom Asset-Server (über die Umleitung): %s" % ", ".join(wege))
                ok(not os.path.isfile(os.path.join(d, neu_zip)), "keine ZIP (die Brücke kennt sie nicht)")
                Leise.log.clear()
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "b", env, base1 + "/versions.json")
                ok(r.get("app") == neu_v and r.get("ok") is False and r.get("de", 0) > 1000, "neue Version startet im Kern (%s Texte)" % r.get("de"))
                ok(r.get("holen") == "" and r.get("da") is True and lesen(os.path.join(d, neu_zip)) == zip_gut,
                   "ZIP nicht neben versions.json - über den eigenen Eintrag («url») vom Asset-Server geholt (%s)" % (r.get("holen") or "ok"))
                ok(any(x.startswith("/" + neu_zip + " 404") for x in Leise.log) and "UMLEITUNG " + asset[len(base2):] + neu_zip in Leise.log,
                   "Reihenfolge: zuerst neben versions.json (404), dann der Asset-Server")
                r = py(os.path.join(d, neu_py), NEU_LADEN, h + "c", env)
                ok(r.get("ok") is True and r.get("miss") == 0, "nach dem Neustart: alles da")
                blob_setzen(prog=None)
                nicht_installiert(alt_pfad, "Programmdatei fehlt auf dem Asset-Server (404)", "404")
                blob_setzen()
    finally:
        for s_ in (srv1, srv2, srv3):
            s_.shutdown()


# ======================================================================================================================
# part «stand»: the published state (versions.json + files as they lie in the repository), real public key
# ======================================================================================================================
def stand(a, tmp):
    ordner = os.path.abspath(a.ordner or REPO)
    print("Stand: %s%s" % (ordner, " (streng)" if a.streng else ""))
    try:
        man = json.load(open(os.path.join(ordner, "versions.json"), encoding="utf-8"))
        ents = [e for e in man["versions"] if isinstance(e, dict)]
    except (OSError, ValueError, LookupError, TypeError) as e:
        ok(False, "versions.json lesbar (%s)" % e)
        return
    ok(len(ents) > 0, "versions.json: %d Einträge" % len(ents))
    if not ents:
        return
    progs = programme(ordner)
    cp, kp = zertifikat(tmp)
    ca = ca_buendel(tmp, cp)
    ctx = ssl.create_default_context(cafile=ca)
    srv_dir = os.path.join(tmp, "stand_server")
    os.makedirs(srv_dir)
    for n in os.listdir(ordner):                           # what raw.githubusercontent would serve; folders only of a throwaway copy
        p = os.path.join(ordner, n)
        if n == "versions.json" or VFILE.match(n) or ZFILE.match(n) or (a.ordner and os.path.isdir(p) and not n.startswith(".")):
            os.symlink(p, os.path.join(srv_dir, n))
    srv, base = server(srv_dir, cp, kp, a.port)
    try:
        stand_pruefen(a, tmp, ordner, ents, progs, ca, ctx, base)
    finally:
        srv.shutdown()


def stand_pruefen(a, tmp, ordner, ents, progs, ca, ctx, base):
    def holen(url):
        if a.ohne_netz and not url.startswith("https://127.0.0.1"):
            raise OSError("--ohne-netz")
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MoveEye-Update-Test"}), timeout=90, context=ctx) as r:
            return r.read(MAX_BYTES + 1)

    # ---- released state or work in progress? ------------------------------------------------------------------------------
    top = max(ents, key=lambda e: vkey(e.get("version", "0")))
    tv, tf = str(top.get("version")), str(top.get("file"))
    neueste_datei = max(progs, key=vkey) if progs else ""
    lokal = os.path.join(ordner, tf)
    grund = ""
    if neueste_datei and vkey(neueste_datei) > vkey(tv):
        grund = "die neueste Programmdatei %s steht nicht in versions.json (neuester Eintrag: %s)" % (progs[neueste_datei], tv)
    elif not top.get("url") and not os.path.isfile(lokal):
        grund = "die Datei %s des neuesten Eintrags fehlt" % tf
    elif os.path.isfile(lokal) and sha(lesen(lokal)) != str(top.get("sha256")):
        grund = "%s hat einen anderen Inhalt als in versions.json (nach dem Release neu gebaut)" % tf
    aus = set()
    if grund and a.streng:
        ok(False, "veröffentlichter Stand stimmt: " + grund)
    elif grund:
        if not (neueste_datei and vkey(neueste_datei) > vkey(tv) and os.path.isfile(lokal) and sha(lesen(lokal)) == str(top.get("sha256"))):
            aus.add(tv)
        hinweis("Arbeitsstand, nicht veröffentlicht: %s. Übersprungen, weil dieser Stand noch nicht signiert sein kann: "
                "%s - auf main (--streng) ist das ein Fehler." % (grund, ("Eintrag " + tv) if aus else "nichts (nur der Hinweis)"))
    else:
        print("  ok   veröffentlichter Stand: %s ist die neueste Datei und passt zu versions.json" % tf)

    # ---- S1: every entry ----------------------------------------------------------------------------------------------------
    print("S1 jeder Eintrag in versions.json (Datei, Grösse, Prüfsumme, Signatur mit dem echten Schlüssel)")
    sigs, sig_text, nicht_neben = [], [], []
    for e in ents:
        v, fn, url = str(e.get("version")), str(e.get("file")), str(e.get("url") or "")
        if v in aus:
            print("  ----  %s: übersprungen (Arbeitsstand, siehe Hinweis)" % v)
            continue
        m = VFILE.match(fn)
        if not (m and ".".join(str(int(x)) for x in m.groups()) == v):
            ok(False, "%s: Dateiname %s passt zur Version" % (v, fn))
            continue
        fehl = []
        try:
            data = lesen(os.path.join(ordner, fn)) if os.path.isfile(os.path.join(ordner, fn)) else holen(url) if url else None
        except Exception as ex:
            data = None
            fehl.append("nicht erreichbar über «url» (%s)" % str(ex)[:80])
        if data is None:
            ok(False, "%s: Programmdatei %s da%s" % (v, fn, " - " + fehl[0] if fehl else " (fehlt im Ordner, keine «url»)"))
            continue
        text = data.decode("utf-8", "replace")
        if e.get("size") is not None and int(e["size"]) != len(data):
            fehl.append("Grösse %d statt %s" % (len(data), e["size"]))
        if sha(data) != str(e.get("sha256")):
            fehl.append("SHA-256 anders als in versions.json")
        if ('UPDATE_PUBKEY = "%s"' % ECHT_PUB) not in text:
            fehl.append("trägt nicht den echten öffentlichen Schlüssel")
        sigs.append([v, fn, str(e.get("sha256")), str(e.get("sig") or "")])
        sig_text.append("%s: Signatur der Programmdatei" % v)
        zn, zsha = zd_von(text)
        dz = e.get("data") or {}
        wo = ""
        if zn:
            if str(dz.get("file")) != zn or str(dz.get("sha256")) != zsha:
                fehl.append("«data» (%s) ist nicht die Zusatzdatei aus der signierten Programmdatei (%s)" % (dz.get("file"), zn))
            neben_liste = os.path.isfile(os.path.join(ordner, zn))
            zb = None
            try:                                           # devices look next to the program file (397 _zd_fetch_bytes), never at data.url
                zb = holen(url.rsplit("/", 1)[0] + "/" + zn) if url else lesen(os.path.join(ordner, zn)) if neben_liste else None
            except Exception as ex:
                fehl.append("Zusatzdatei nicht neben der Programmdatei (%s)" % str(ex)[:80])
            if zb is None and not url:
                fehl.append("Zusatzdatei %s fehlt" % zn)
            if zb is not None:
                if sha(zb) != zsha:
                    fehl.append("Zusatzdatei: SHA-256 anders als in der Programmdatei")
                if dz.get("size") is not None and int(dz["size"]) != len(zb):
                    fehl.append("Zusatzdatei: Grösse %d statt %s" % (len(zb), dz["size"]))
                sigs.append([v, zn, zsha, str(dz.get("sig") or "")])
                sig_text.append("%s: Signatur der Zusatzdatei" % v)
            if not neben_liste:
                nicht_neben.append(v)
            wo = ", Zusatzdatei %s" % zn
        elif dz:
            fehl.append("«data» eingetragen, aber die Programmdatei kennt keine Zusatzdatei")
        ok(not fehl, "%s: %s%s%s%s" % (v, fn, wo, " über «url»" if url else "", " -> " + "; ".join(fehl) if fehl else ""))
    if nicht_neben:                                        # S2 judges it for the newest version (real behaviour of the devices)
        hinweis("Zusatzdatei nicht neben versions.json bei %s - dort sucht eine neue Version ihre fehlende Zusatzdatei "
                "(zusatz_holen, Teil 397; nach einem Update von der Brücke aus geht es nur so)" % ", ".join(nicht_neben))
    br = [e for e in ents if e.get("bridge")]
    ok(len(br) >= 1 and all(os.path.isfile(os.path.join(ordner, str(e.get("file")))) for e in br),
       "Brücken-Eintrag da und ihre Datei liegt im Ordner (%s)" % ", ".join(str(e.get("version")) for e in br))
    fremd = sorted(n for v, n in progs.items() if v not in {str(e.get("version")) for e in ents} and v != neueste_datei)
    if fremd:
        hinweis("Programmdateien ohne Eintrag in versions.json: " + ", ".join(fremd))

    voll, bruecke = alte_geraete(ordner)
    pruefer = bruecke or voll                              # any untouched program file checks the signatures (real public key)
    if sigs and pruefer:
        lst = os.path.join(tmp, "sigs.json")
        json.dump(sigs, open(lst, "w"))
        r = py(geraet_anlegen(os.path.join(tmp, "pruefer"), pruefer), SIGS, os.path.join(tmp, "home_s"), {}, lst)   # a copy: nothing is ever written into the repository
        ok(isinstance(r, dict) and r.get("pub") == ECHT_PUB, "Prüfer %s trägt den echten öffentlichen Schlüssel" % os.path.basename(pruefer))
        res = (r.get("ok") if isinstance(r, dict) else None) or [False] * len(sigs)
        schlecht = [t for t, g in zip(sig_text, res) if not g]
        ok(not schlecht, "%d Signaturen gültig (Ed25519, echter öffentlicher Schlüssel)%s" % (len(sigs), " -> UNGÜLTIG: " + "; ".join(schlecht) if schlecht else ""))
    else:
        ok(False, "Signaturen prüfbar (keine Programmdatei im Ordner)")

    # ---- S2: real devices fetch the newest version from exactly this state --------------------------------------------------
    ziele = [e for e in ents if str(e.get("version")) not in aus]
    if not ziele:
        return
    ziel = max(ziele, key=lambda e: vkey(e.get("version", "0")))
    zv, zf = str(ziel.get("version")), str(ziel.get("file"))
    print("S2 alte Geräte (unverändert, echter Schlüssel) holen %s aus diesem Stand" % zv)
    env = {"SSL_CERT_FILE": ca}
    if True:
        voll, bruecke = alte_geraete(ordner, ausser=zv)
        geraete = [x for x in (voll, bruecke) if x and vkey(version_von(x)) < vkey(zv)]
        ok(len(geraete) >= 1, "mindestens ein älteres Gerät im Ordner (%s)" % ", ".join(os.path.basename(x) for x in geraete))
        ziel_bytes = lesen(os.path.join(ordner, zf)) if os.path.isfile(os.path.join(ordner, zf)) else None
        zzip = zd_von((ziel_bytes or b"").decode("utf-8", "replace"))[0] if ziel_bytes else str((ziel.get("data") or {}).get("file") or "")
        for i, alt_pfad in enumerate(geraete):
            alt_v = version_von(alt_pfad)
            d = os.path.join(tmp, "stand_geraet_%d" % i)
            p = geraet_anlegen(d, alt_pfad)
            h = os.path.join(tmp, "stand_home_%d" % i)
            Leise.log.clear()
            r = py(p, UPDATE, h, env, base + "/versions.json", zv)
            ok(bool(r.get("found") and r.get("signed")), "%s sieht %s, signiert mit dem echten Schlüssel (%s)" % (alt_v, zv, r.get("msg") or "ok"))
            if not aus:
                ok(r.get("new") == zv, "%s bekommt %s angeboten (angeboten: %s)" % (alt_v, zv, r.get("new")))
            ok(r.get("install") == [True, ""] and r.get("restart", {}).get("version") == zv, "%s: installiert, Neustart in %s (%s)" % (alt_v, zv, r.get("install")))
            neu = os.path.join(d, zf)
            ok(os.path.isfile(neu) and sha(lesen(neu)) == str(ziel.get("sha256")), "%s: Programmdatei %s beim Gerät, Prüfsumme wie signiert" % (alt_v, zf))
            if not os.path.isfile(neu):
                continue
            if zzip and kennt_zusatz(alt_pfad):
                ok(os.path.isfile(os.path.join(d, zzip)), "%s: Zusatzdatei %s gleich mitgeholt" % (alt_v, zzip))
            r = py(neu, NEU_LADEN, h + "n", env, base + "/versions.json")
            if zzip and r.get("ok") is False:               # bridge (or the zip did not come along): the new version fetches it itself
                ok(r.get("holen") == "" and r.get("da") is True, "%s -> %s holt ihre Zusatzdatei selbst neben versions.json (%s)" % (alt_v, zv, r.get("holen") or "ok"))
                r = py(neu, NEU_LADEN, h + "n2", env)
            ok(r.get("app") == zv and (r.get("ok") is True and r.get("miss") == 0 if zzip else True),
               "%s -> %s: die neue Version lädt, alle Literale da (%s)" % (alt_v, zv, r.get("used")))
            print("     Server: " + ", ".join(sorted(set(x.split(" ")[0] for x in Leise.log))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", choices=["uebergang", "stand"], default="", help="nur einen Teil (Standard: beide)")
    ap.add_argument("--alt", default="", help="uebergang: diese alte Programmdatei (Standard: die älteste mit Zusatzdatei im Repository + die Brücke)")
    ap.add_argument("--ablage", action="store_true", help="uebergang mit --alt: auch Teil U (Ablage «url», Asset-Server mit Umleitung)")
    ap.add_argument("--neu-version", default="", help="uebergang: Nummer der gebauten neuen Version (Standard: nach der neuesten Datei)")
    ap.add_argument("--streng", action="store_true", help="stand: ein Arbeitsstand (neueste Datei passt nicht zu versions.json) ist ein Fehler - CI auf main")
    ap.add_argument("--ordner", default="", help="stand: dieser Ordner statt des Repositorys (Wegwerf-Kopie zum Nachstellen)")
    ap.add_argument("--ohne-netz", action="store_true", help="stand: Dateien mit «url» nicht aus dem Internet holen (dann Fehler)")
    ap.add_argument("--port", type=int, default=0, help="stand: fester Port des Test-Servers (zum Nachstellen von «url» in einer Wegwerf-Kopie)")
    ap.add_argument("--behalten", action="store_true", help="Test-Ordner nicht löschen")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="mw_uebergang_")
    teile = []
    try:
        for name, fn in (("uebergang", uebergang), ("stand", stand)):
            if a.nur in ("", name):
                n0 = len(FEHLER)
                print("=== Teil «%s»" % name)
                try:
                    os.makedirs(os.path.join(tmp, name))
                    fn(a, os.path.join(tmp, name))
                except Exception as e:                      # a crash of the test is red, never green
                    import traceback
                    traceback.print_exc()
                    ok(False, "Teil «%s» läuft durch (%s: %s)" % (name, type(e).__name__, str(e)[:200]))
                teile.append((name, len(FEHLER) - n0))
    finally:
        if not a.behalten:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print("Test-Ordner: " + tmp)
    print("\n" + ("Übergangs-Test OK (%s)" % ", ".join(n for n, _f in teile) if not FEHLER else "%d FEHLER:\n  - %s" % (len(FEHLER), "\n  - ".join(FEHLER))))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
