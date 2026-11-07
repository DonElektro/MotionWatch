#!/usr/bin/env python3
"""Test der Zusatzdatei moveeye_daten_X_Y_Z.zip und der schlanken Hauptdatei (Paket «Schlank», für 3.59.0).

  python3 werkzeuge/zusatzdaten_test.py                  # neuste gebaute webcam_bewegung_*.py im Repository (mit ihrer ZIP)
  python3 werkzeuge/zusatzdaten_test.py --datei X.py

Prüft (ohne Netz, ohne den echten Schlüssel - ein Test-Schlüssel wird jedes Mal neu erzeugt):
  1. Quelle: zd_source() der gebauten Datei + ZIP ergibt Byte für Byte das Programm aus quelle/ (bauen.zusammensetzen()).
  2. Gleiches Programm: der Syntaxbaum der schlanken Datei = der ohne «Schlank» (nur die Docstrings sind leer).
  3. ZIP gültig / verändert / fehlt / andere Version: nur die richtige wird genommen (ZD_SHA256 in der Hauptdatei).
  4. Signatur in versions.json (make_manifest mit Test-Schlüssel): Programm und ZIP richtig signiert; eine veränderte
     ZIP, ein fremder Schlüssel und ein fehlender Eintrag fallen durch.
  5. Ohne ZIP: MoveEye lädt (Kern), Deutsch bleibt, die Web-Seite zeigt den Hinweis mit «Jetzt nachladen», die
     Fehler-Hilfe DATA_MISSING ist da.
  6. Grössen-Grenze von bauen.py: Warnung ab 4 MiB, Abbruch ab 5 MiB.
"""
import argparse
import ast
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import bauen  # noqa: E402

FEHLER = []


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text)
    if not bed:
        FEHLER.append(text)


LADEN = r'''
import json, os, sys
ns = {"__name__": "mw_zd_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
'''


def im_programm(datei, code, home, extra=()):
    """run <code> after loading <datei> as a module (namespace ns) in an own Python; -> (returncode, stdout+stderr)"""
    env = dict(os.environ, MOTIONWATCH_HOME=home)
    r = subprocess.run([sys.executable, "-c", LADEN + code, datei] + list(extra), capture_output=True, text=True, env=env,
                       timeout=300, cwd=os.path.dirname(datei))
    return r.returncode, r.stdout + r.stderr


def zeile(out, name):
    for ln in out.splitlines():
        if ln.startswith(name + " "):
            return json.loads(ln[len(name) + 1:])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    text = open(datei, encoding="utf-8", newline="").read()
    zf_name, zsha = re.search(r'^ZD_FILE = "([^"]*)"\s*\nZD_SHA256 = "([0-9a-f]*)"', text, re.M).groups()
    v = bauen.version(text)
    print("Datei %s (%d Bytes), ZIP %s" % (os.path.basename(datei), len(text.encode()), zf_name))
    tmp = tempfile.mkdtemp(prefix="mw_zd_test_")
    try:
        geraet = os.path.join(tmp, "geraet")
        os.makedirs(geraet)
        shutil.copy(datei, geraet)
        shutil.copy(os.path.join(os.path.dirname(datei), zf_name), geraet)
        prog = os.path.join(geraet, os.path.basename(datei))
        zpfad = os.path.join(geraet, zf_name)
        zbytes = open(zpfad, "rb").read()

        print("1. Quelle (zd_source)")
        rc, out = im_programm(prog, 'print("ZD " + json.dumps([ns["ZD"]["ok"], ns["ZD"]["miss"][:5]]))\n'
                                    'open(sys.argv[2], "w", encoding="utf-8", newline="").write(ns["zd_source"]())',
                              os.path.join(tmp, "h1"), [os.path.join(tmp, "quelle.py")])
        zd = zeile(out, "ZD")
        ok(rc == 0 and zd == [True, []], "Programm lädt mit ZIP, alle Literale da (%s)" % (zd if zd is not None else out[-800:]))
        if rc == 0 and bauen.version() == v:
            q = open(os.path.join(tmp, "quelle.py"), encoding="utf-8", newline="").read()
            soll = bauen.zusammensetzen().replace('ZD_FILE = ""', 'ZD_FILE = "%s"' % zf_name, 1).replace(
                'ZD_SHA256 = ""', 'ZD_SHA256 = "%s"' % zsha, 1)
            ok(q == soll, "zd_source() = quelle/ Byte für Byte (%d Bytes)" % len(q.encode()))
        else:
            print("  (übersprungen: quelle/ hat eine andere Version als die Datei)")

        print("2. Gleiches Programm (Syntaxbaum)")
        if bauen.version() == v:
            alt = bauen.ZD_SCHLANK
            bauen.ZD_SCHLANK = False
            try:
                voll = bauen.zusammensetzen_klein(zsha)[0]
            finally:
                bauen.ZD_SCHLANK = alt

            def baum(t):
                tr = ast.parse(t)
                for nd in ast.walk(tr):
                    if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and nd.body:
                        st = nd.body[0]
                        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
                            st.value.value = ""
                return ast.dump(tr)
            ok(baum(voll) == baum(text), "gleicher Syntaxbaum wie ohne Schlank (ausser Docstrings)")
            ok(voll.count("\n") == text.count("\n"), "gleiche Zeilenzahl (%d) – Zeilennummern bleiben" % text.count("\n"))
            ok(len(text.encode()) < len(voll.encode()), "schlanker: %d statt %d Bytes" % (len(text.encode()), len(voll.encode())))

        print("3. ZIP gültig / verändert / fehlt / andere Version")
        chk = ('r = {}\nfor nm in sys.argv[2:]:\n    r[nm] = ns["_zd_check_bytes"](open(nm, "rb").read() if os.path.isfile(nm) else b"", '
               'ns["ZD_SHA256"], ns["APP_VERSION"])\nprint("CHK " + json.dumps(r))')
        kaputt = bytearray(zbytes)
        kaputt[len(kaputt) // 2] ^= 0x55
        open(os.path.join(tmp, "kaputt.zip"), "wb").write(bytes(kaputt))
        bio = io.BytesIO()                                   # a zip with right content shape but an other version
        with zipfile.ZipFile(io.BytesIO(zbytes)) as z, zipfile.ZipFile(bio, "w") as z2:
            d = json.loads(z.read("daten.json"))
            d["version"] = "0.0.1"
            z2.writestr("daten.json", json.dumps(d))
        open(os.path.join(tmp, "fremd.zip"), "wb").write(bio.getvalue())
        rc, out = im_programm(prog, chk, os.path.join(tmp, "h3"),
                              [zpfad, os.path.join(tmp, "kaputt.zip"), os.path.join(tmp, "fremd.zip"), os.path.join(tmp, "fehlt.zip")])
        r = zeile(out, "CHK") or {}
        ok(r.get(zpfad) == "", "richtige ZIP wird genommen")
        ok("checksum" in str(r.get(os.path.join(tmp, "kaputt.zip"))), "veränderte ZIP abgelehnt (%s)" % r.get(os.path.join(tmp, "kaputt.zip")))
        ok(bool(r.get(os.path.join(tmp, "fremd.zip"))), "ZIP mit anderem Inhalt / anderer Version abgelehnt (%s)" % r.get(os.path.join(tmp, "fremd.zip")))
        ok(r.get(os.path.join(tmp, "fehlt.zip")) == "no data file", "fehlende ZIP erkannt")
        shutil.copy(os.path.join(tmp, "kaputt.zip"), zpfad)          # the program itself with a tampered zip next to it
        rc, out = im_programm(prog, 'print("ZD " + json.dumps([ns["ZD"]["ok"], ns["ZD"]["err"][:60], len(ns["DE"])]))', os.path.join(tmp, "h3b"))
        zd = zeile(out, "ZD")
        ok(rc == 0 and zd and zd[0] is False and "checksum" in zd[1], "Programm mit veränderter ZIP: nimmt sie nicht, läuft im Kern (%s)" % (zd or out[-500:]))
        open(zpfad, "wb").write(zbytes)

        print("4. Signatur (versions.json, Test-Schlüssel)")
        key = os.path.join(tmp, "test_schluessel.txt")
        open(key, "w").write(os.urandom(32).hex())
        code = r'''
ns["make_manifest"](sys.argv[2], "https://example.invalid/mw", sys.argv[3])
if not ns["_ED"]:
    ns["_ED"].extend(ns["_ed25519_impl"]())
pub = ns["_ED"][0](bytes.fromhex(open(sys.argv[3]).read().strip())).hex()
m = json.load(open(os.path.join(sys.argv[2], "versions.json")))
e = m["versions"][0]
d = e.get("data") or {}
so = ns["sig_ok"]
res = {"prog": so(e["version"], e["file"], e["sha256"], e.get("sig"), pub),
       "data": bool(d) and so(e["version"], d["file"], d["sha256"], d.get("sig"), pub),
       "data_size": d.get("size"), "data_file": d.get("file"),
       "tampered": so(e["version"], d.get("file"), ns["hashlib"].sha256(open(sys.argv[4], "rb").read()).hexdigest(), d.get("sig"), pub),
       "other_key": so(e["version"], d.get("file"), d.get("sha256"), d.get("sig")),
       "missing": so(e["version"], d.get("file"), d.get("sha256"), None, pub),
       "swap": so(e["version"], e["file"], d.get("sha256"), d.get("sig"), pub)}
print("SIG " + json.dumps(res))
'''
        rc, out = im_programm(prog, code, os.path.join(tmp, "h4"), [geraet, key, os.path.join(tmp, "kaputt.zip")])
        r = zeile(out, "SIG") or {}
        ok(r.get("prog") is True, "Programmdatei richtig signiert")
        ok(r.get("data") is True and r.get("data_file") == zf_name and r.get("data_size") == len(zbytes),
           "ZIP mit eigener Signatur, Grösse und SHA-256 unter «data» (%s)" % ({k: r.get(k) for k in ("data", "data_file", "data_size")}))
        ok(r.get("tampered") is False, "veränderte ZIP: Signatur passt nicht")
        ok(r.get("other_key") is False, "fremder Schlüssel (der echte öffentliche): Signatur passt nicht")
        ok(r.get("missing") is False, "fehlende Signatur: abgelehnt")
        ok(r.get("swap") is False, "Signatur der ZIP gilt nicht für eine andere Datei")
        if not r:
            print(out[-1500:])

        print("5. Ohne ZIP (Kern)")
        os.remove(zpfad)
        code = r'''
ws = ns["WebStream"](None)
ns["GAMESRV"]["port"] = 1
ns["CFG"]["https_extra"] = False
ws._serve = lambda app, ctx: None
ws.start()
c = ws.app.test_client()
hx = ns["_zd_hx"]({"Tour of this page": "Rundgang durch diese Seite"})
fx = c.get("/hilfe/fehler/DATA_MISSING")
res = {"ok": ns["ZD"]["ok"], "err": ns["ZD"]["err"], "de": ns["DE"].get("Tour of this page"),
       "fr": ns["TRX"].get("fr", {}).get("Tour of this page"), "hx": list(hx["Tour of this page"]),
       "page": "/hilfe/fehler/DATA_MISSING" in ns["ZD_PAGE"], "fx": fx.status_code,
       "fx_text": "moveeye_daten" in fx.get_data(as_text=True) or "Zusatz" in fx.get_data(as_text=True),
       "health": [x.get("id") for x in (lambda h: h.get("items") if isinstance(h, dict) else h)(ns["health_check"]("de"))
                  if isinstance(x, dict) and x.get("id") == "zusatz"],
       "cfg": len(ns["CFG"]), "de_n": len(ns["DE"])}
print("KERN " + json.dumps(res, ensure_ascii=False))
'''
        rc, out = im_programm(prog, code, os.path.join(tmp, "h5"))
        r = zeile(out, "KERN") or {}
        ok(rc == 0 and r.get("ok") is False and r.get("err") == "missing", "lädt ohne ZIP, kein Absturz (%s)" % (r.get("err") if r else out[-1200:]))
        ok(r.get("de") == "Rundgang durch diese Seite", "Deutsch aus den Tabellen _HX… bleibt in der Hauptdatei")
        ok(r.get("fr") == "Tour of this page" and r.get("hx") == ["Rundgang durch diese Seite", "Tour of this page",
                                                                    "Tour of this page", "Rundgang durch diese Seite"],
           "Französisch / Italienisch zeigen Englisch, Romanisch Deutsch")
        ok(r.get("page") is True, "Hinweis-Seite mit «Jetzt nachladen» (/hilfe/fehler/DATA_MISSING)")
        ok(r.get("fx") == 200 and r.get("fx_text"), "Fehler-Hilfe DATA_MISSING erreichbar (%s)" % r.get("fx"))
        ok(r.get("health") == ["zusatz"], "Selbst-Check meldet die fehlende Zusatzdatei")

        print("6. Grössen-Grenze (bauen.py)")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            a1 = bauen.groesse_pruefen("x" * int(3.9 * 1048576))
            o1 = buf.getvalue(); buf.truncate(0); buf.seek(0)
            a2 = bauen.groesse_pruefen("x" * int(4.5 * 1048576))
            o2 = buf.getvalue(); buf.truncate(0); buf.seek(0)
            a3 = bauen.groesse_pruefen("x" * (5 * 1048576 + 1))
            o3 = buf.getvalue()
        finally:
            sys.stdout = old
        ok(a1 and not o1, "3.9 MiB: ok, keine Meldung")
        ok(a2 and "WARNUNG" in o2, "4.5 MiB: Warnung")
        ok(not a3 and "ZU GROSS" in o3, "über 5 MiB: Abbruch")
        n_ = len(text.encode())                     # gleiche Grenze wie bauen.py / versionen.py: Warnung ab 4 MiB, Abbruch ab 5 MiB
        if n_ > 4 * 1048576:
            print("  Hinweis: Hauptdatei %.2f MiB - über 4 MiB (Warnung), mehr in die Zusatzdatei" % (n_ / 1048576))
        ok(n_ < 5 * 1048576, "Hauptdatei unter 5 MiB (%d Bytes, %.2f MiB)" % (n_, n_ / 1048576))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + ("Zusatzdaten-Test OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
