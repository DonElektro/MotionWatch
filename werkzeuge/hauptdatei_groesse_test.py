#!/usr/bin/env python3
"""Test «Hauptdatei-Grösse» (Paket «Hauptdatei kleiner», 12.11.2026): die Programmdatei webcam_bewegung_X_Y_Z.py bleibt klar
unter der Warnung von bauen.py (4 MiB), und was dafür in die Zusatzdatei kam, verhält sich richtig.

  python3 werkzeuge/hauptdatei_groesse_test.py                  # quelle/ + neuste gebaute Datei im Repository (mit ihrer ZIP)
  python3 werkzeuge/hauptdatei_groesse_test.py --datei X.py

Prüft (ohne Netz, ohne Schlüssel):
  1. Luft: aus quelle/ gebaut bleiben mindestens GROESSE_LUFT (150 KiB) bis zur Warnung. Rot heisst: die letzte Änderung
     hat grosse Daten in die Hauptdatei gebracht - die Meldung sagt, was zu tun ist.
  2. Bericht von bauen.py: Grösse, Luft, die grössten Literale, die bleiben; Hinweis, wenn die Luft knapp wird.
  3. Prüf-Code («…_selftest» in der ZIP): nur Funktionen, die allein der Selbsttest benutzt; gleiche Zeilennummern; der
     Platzhalter lädt die echte Funktion; ohne / mit veränderter ZIP eine klare Meldung statt eines Absturzes.
  4. Almanach: mit ZIP alle Kapitel in der alten Reihenfolge; ohne ZIP bleibt das Kapitel «Notfall» (Liste, Tipp des
     Abends, Seite /almanach mit Notrufnummern und dem Hinweis «Zusatzdaten fehlen»).
  5. Folgezeilen mit Tabs: keine Zeile ausserhalb von Texten beginnt noch mit vier Leerzeichen.
  6. Zweite Runde (13.11.2026): Hilfsfunktionen nur des Prüf-Codes in der ZIP (nicht, wenn ein Werkzeug oder ein Text sie
     nennt oder der Betrieb sie braucht); Tabellen _HX… mit Namen als Schlüssel (_zd_hxk: mit ZIP fr / it / rm, ohne ZIP
     Deutsch, eine veränderte ZIP wird nie benutzt); kleine Übersetzungen fr / it / rm; Ergänzungen der Anleitung.
"""
import argparse
import ast
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import bauen  # noqa: E402

FEHLER = []

WAS_TUN = """
  Was tun (CLAUDE.md «Zusatzdatei»):
    * «python3 werkzeuge/bauen.py --groessen» zeigt die grössten Teile und die grössten Literale, die in der Hauptdatei
      bleiben, je mit dem Grund.
    * Grosse Daten (Web-Seiten, JS, CSS, SVG, Tabellen, Texte) als EIN Literal auf oberster Ebene schreiben
      (NAME_PAGE / _HTML / _JS / _CSS = \"\"\"…\"\"\" ab 1 KiB, andere Literale ab 4 KiB) - nicht in einer Funktion, nicht
      mit «+» oder f-Text zusammengesetzt. bauen.py lagert sie dann von selbst in die Zusatzdatei aus.
    * Was ohne Zusatzdatei gebraucht wird (Start, Anmelden, Schutz, Alarm, Update, Reparatur), bleibt in der Hauptdatei.
    * GROESSE_LUFT nicht einfach senken - die Hauptdatei war im November 2026 unbemerkt bis 2.6 KB an die Warnung gewachsen."""


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text)
    if not bed:
        FEHLER.append(text)


LADEN = r'''
import json, os, sys
ns = {"__name__": "mw_gr_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
'''


def im_programm(datei, code, home, extra=()):
    env = dict(os.environ, MOTIONWATCH_HOME=home)
    r = subprocess.run([sys.executable, "-c", LADEN + code, datei] + list(extra), capture_output=True, text=True, env=env,
                       timeout=300, cwd=os.path.dirname(datei))
    return r.returncode, r.stdout + r.stderr


def zeile(out, name):
    for ln in out.splitlines():
        if ln.startswith(name + " "):
            try:
                return json.loads(ln[len(name) + 1:])
            except ValueError:
                return None
    return None


def aufgefangen(fn, *a, **k):
    buf, old = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        r = fn(*a, **k)
    finally:
        sys.stdout = old
    return r, buf.getvalue()


def kunst_quelle(teile):
    """bauen.py for a moment on made-up parts {name: text} -> restore()"""
    alt = (bauen.teile, bauen.lesen)
    bauen.teile = lambda: sorted(teile)
    bauen.lesen = lambda n: teile[n]

    def restore():
        bauen.teile, bauen.lesen = alt
        bauen.pruefcode_namen(neu=True)
    return restore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    text = open(datei, encoding="utf-8", newline="").read()
    zf_name = re.search(r'^ZD_FILE = "([^"]*)"', text, re.M).group(1)
    print("Datei %s (%d Bytes), ZIP %s" % (os.path.basename(datei), len(text.encode()), zf_name))

    print("1. Luft bis zur Warnung")
    q_text = bauen.zusammensetzen_klein("")[0]
    for was, n in (("quelle/ (so würde jetzt gebaut)", len(q_text.encode())), (os.path.basename(datei), len(text.encode()))):
        luft = bauen.GROESSE_WARN - n
        gut = luft >= bauen.GROESSE_LUFT
        ok(gut, "%s: %d Bytes (%.2f MiB), Luft bis zur Warnung %d KiB (mindestens %d KiB)"
           % (was, n, n / 1048576.0, luft // 1024, bauen.GROESSE_LUFT // 1024))
        if not gut:
            print(WAS_TUN)
    ok(bauen.GROESSE_WARN == 4 * 1048576 and bauen.GROESSE_MAX == 5 * 1048576 and 100 * 1024 <= bauen.GROESSE_LUFT <= 512 * 1024,
       "Grenzen von bauen.py: Warnung 4 MiB, Abbruch 5 MiB, Luft %d KiB" % (bauen.GROESSE_LUFT // 1024))

    print("2. Bericht von bauen.py")
    luft, out = aufgefangen(bauen.groessen_bericht, q_text)
    ok(luft == bauen.GROESSE_WARN - len(q_text.encode()) and "Luft bis zur Warnung" in out and "WENIGER" not in out,
       "Bericht nennt Grösse und Luft (%s)" % out.splitlines()[0].strip())
    rows = [ln for ln in out.splitlines()[2:] if ln.strip()]
    ok(len(rows) == 5 and all(" – " in r for r in rows), "die fünf grössten Literale, die bleiben, je mit Grund")
    luft2, out2 = aufgefangen(bauen.groessen_bericht, "x" * (bauen.GROESSE_WARN - bauen.GROESSE_LUFT + 1), False)
    ok(luft2 < bauen.GROESSE_LUFT and "WENIGER ALS" in out2 and "--groessen" in out2, "knapp: der Bericht sagt, was zu tun ist")

    print("3. Prüf-Code in der Zusatzdatei")
    kunst = {
        "100_a.py": ("SELFTEST_EXTRA = []\n\n\ndef a_selftest():\n    # Kommentar\n    return b_selftest() + 1\n\n\n"
                     "def b_selftest(x=1):\n    return x\n\n\nSELFTEST_EXTRA.append((\"a\", a_selftest))\n"),
        "200_b.py": ("def c_selftest():\n    return 3\n\n\ndef betrieb():\n    return c_selftest()\n\n\n"
                     "def d_selftest(x=[]):\n    return 4\n\n\nKNOPF = {\"test\": e_selftest} if 0 else {}\n\n\n"
                     "def e_selftest():\n    return 5\n\n\ndef self_test():\n    return f_selftest()\n\n\n"
                     "def f_selftest():\n    return 6\n"),
    }
    zurueck = kunst_quelle(kunst)
    try:
        namen = bauen.pruefcode_namen(neu=True)
        ok(namen == {"a_selftest", "b_selftest", "f_selftest"},
           "nur was allein der Selbsttest benutzt (im Betrieb benutzt, veränderliche Vorgabe, in einer Tabelle: bleibt) – %s" % sorted(namen))
        neu, ents = bauen.auslagern("100_a.py", kunst["100_a.py"])
        ok(neu.count("\n") == kunst["100_a.py"].count("\n") and [e[0] for e in ents] == ["100_a/a_selftest()", "100_a/b_selftest()"],
           "Platzhalter auf der Zeile des «def», gleiche Zeilenzahl")
        ok(neu.split("\n")[3] == "a_selftest = _zd_fn('100_a/a_selftest()')" and "Kommentar" in ents[0][2], "Quelltext samt Kommentar im Eintrag")
        pos, back = 0, []
        for _k, ph, seg in ents:
            i = neu.find(ph, pos)
            back.append(neu[pos:i]); back.append(seg); pos = i + len(ph)
        ok("".join(back) + neu[pos:] == kunst["100_a.py"], "zurück eingesetzt = Quelle Byte für Byte")
        alt = bauen.ZD_PRUEFCODE
        bauen.ZD_PRUEFCODE = False
        try:
            ok(not bauen.pruefcode_namen(neu=True) and bauen.auslagern("100_a.py", kunst["100_a.py"])[1] == [], "Schalter ZD_PRUEFCODE = False: alles bleibt")
        finally:
            bauen.ZD_PRUEFCODE = alt
    finally:
        zurueck()
    # zweite Runde: Hilfsfunktionen nur des Prüf-Codes (die Werkzeuge hier aussen vor: dieser Test nennt die Namen selbst)
    kunst2 = {
        "100_a.py": ("SELFTEST_EXTRA = []\n\n\ndef h1(x=2):\n    return h2() + x\n\n\ndef h2():\n    return 1\n\n\n"
                     "def a_selftest():\n    return h1() + h_text() + h_betrieb() + h_rek(1)\n\n\ndef h_text():\n    return 0\n\n\n"
                     "ROUTE = {'f': 'h_text'}\n\n\ndef h_betrieb():\n    return 0\n\n\ndef betrieb():\n    return h_betrieb()\n\n\n"
                     "def h_rek(n):\n    return h_rek(n - 1) if n else 0\n\n\nSELFTEST_EXTRA.append(('a', a_selftest))\n"),
    }
    zurueck = kunst_quelle(kunst2)
    alt_w = bauen.ZD_WERKZEUG_ORDNER
    try:
        bauen.ZD_WERKZEUG_ORDNER = ()
        namen = bauen.pruefcode_namen(neu=True)
        ok(namen == {"a_selftest", "h1", "h2", "h_rek"},
           "Hilfsfunktionen nur des Prüf-Codes kommen mit (auch über zwei Stufen); im Betrieb benutzt oder in einem Text genannt: bleibt – %s" % sorted(namen))
        neu, ents = bauen.auslagern("100_a.py", kunst2["100_a.py"])
        ok(neu.count("\n") == kunst2["100_a.py"].count("\n") and "h1 = _zd_fn('100_a/h1()')" in neu and "def h_betrieb" in neu,
           "Platzhalter auch für die Hilfsfunktionen, gleiche Zeilenzahl")
        bauen.ZD_WERKZEUG_ORDNER = alt_w
        ok("h1" not in bauen.pruefcode_namen(neu=True), "ein Name, den ein Werkzeug nennt (hier dieser Test), bleibt in der Hauptdatei")
    finally:
        bauen.ZD_WERKZEUG_ORDNER = alt_w
        zurueck()
    echt = bauen.pruefcode_namen(neu=True)
    ok("sim_manifest_check" not in echt and "geh_offline_html" not in echt and "ui_gem_check" in echt,
       "echte Teile: was Werkzeuge rufen (sim_manifest_check, geh_offline_html) bleibt, ui_gem_check (nur ui_gem_selftest) kommt mit")
    kunst3 = {
        "100_a.py": ("NAME = 'Packing'\nHELP_PAGE = 'x' * 5000 + 'A'\nTRX = {'fr': {}, 'it': {}, 'rm': {}}\n"
                     "_HX_T = {\n    NAME: ('Packen', 'Bagages', 'Bagagli', 'Pachetar'),\n    'Plain key': ('Deutsch', 'Français long text here', 'Italiano', 'Rumantsch'),\n"
                     "    'Third key with a longer English text': ('Dritter Schlüssel', 'Troisième clé avec un texte', 'Terza chiave con un testo', 'Terza clav cun in text'),\n}\n"
                     "TRX['fr'].update({'Some text that is a bit longer': 'Un texte un peu plus long', 'Another one': 'Un autre texte encore plus long ' * 5})\n"
                     "TRX['fr'].update({'Some text that is a bit longer than before': 'Un texte un peu plus long que avant', 'Another one again': 'Un autre texte encore plus long, et encore plus long, et encore plus long, et encore plus long, et encore plus long, et encore plus', 'A third text': 'Un troisième texte'})\n"
                     "for _a, _b in (('A', '" + "B" * 1100 + "'),):\n    if _a in HELP_PAGE:\n        HELP_PAGE = HELP_PAGE.replace(_a, _b)\n"
                     "for _a, _b in (('A', '" + "C" * 1100 + "'),):\n    print(_a)\n"
                     "_PAARE = (('A', '" + "D" * 1100 + "'),)\nfor _a, _b in _PAARE:\n    HELP_PAGE = HELP_PAGE.replace(_a, _b)\n"),
    }
    zurueck = kunst_quelle(kunst3)
    try:
        bauen.anleitung_namen(neu=True)
        neu, ents = bauen.auslagern("100_a.py", kunst3["100_a.py"])
        keys = [e[0] for e in ents]
        ok("_zd_hxk('100_a/HX_T', [\n    (NAME, 'Packen'),\n    ('Plain key', 'Deutsch'),\n    ('Third key with a longer English text', 'Dritter Schlüssel'),\n])" in neu and "Bagages" not in neu,
           "_HX… mit Namen als Schlüssel: Schlüssel und Deutsch bleiben, fr / it / rm in die ZIP")
        ok("100_a/TRX_fr_update" in keys and "' * 5})" in neu, "kleine Tabelle TRX['fr'].update ab %d Bytes in die ZIP (nur fr / it / rm), mit Ausdruck: bleibt" % bauen.ZD_MIN_TR)
        ok("100_a/anleitung_HELP_PAGE" in keys and "C" * 1100 in neu and "100_a/PAARE" in keys and "D" * 1100 not in neu,
           "Ergänzungen der Anleitung (Schleife, benannte Paare) in die ZIP; eine Schleife, die mehr tut, bleibt")
        pos, back = 0, []
        for _k, ph, seg in ents:
            i = neu.find(ph, pos)
            back.append(neu[pos:i]); back.append(seg); pos = i + len(ph)
        ok("".join(back) + neu[pos:] == kunst3["100_a.py"], "zurück eingesetzt = Quelle Byte für Byte (auch _zd_hxk)")
    finally:
        zurueck()
        bauen.anleitung_namen(neu=True)

    tmp = tempfile.mkdtemp(prefix="mw_gr_test_")
    try:
        geraet = os.path.join(tmp, "geraet")
        os.makedirs(geraet)
        shutil.copy(datei, geraet)
        shutil.copy(os.path.join(os.path.dirname(datei), zf_name), geraet)
        prog = os.path.join(geraet, os.path.basename(datei))
        zpfad = os.path.join(geraet, zf_name)
        code = r'''
import types
src = ns["zd_source"]().split("\n")
own = open(sys.argv[1], encoding="utf-8").read().split("\n")
keys = [k for k in ns["ZD"]["data"] if k.endswith("()")]
bad = []
for k in keys:
    nm = k.rsplit("/", 1)[1][:-2]
    row = [i for i, ln in enumerate(own) if ln.startswith(nm + " = _zd_fn(")]
    seg = ns["ZD"]["data"][k]
    n = seg.count("\n")
    if (len(row) != 1 or not seg.startswith("def " + nm + "(") or any(own[row[0] + 1:row[0] + n]) or seg not in "\n".join(src)
            or own[row[0] + n].strip().startswith(("return", "assert"))):
        bad.append(nm)
k_ = ns["PL_HEIC_MSG"]
hk = ns["_HX_PACK"][k_]
st = ns["zusatz_selftest"]
before = [st.__name__, type(st).__name__, "zusatz_selftest" in "".join(own[i] for i in range(len(own)) if own[i].startswith("def "))]
res = st()
real = getattr(st, "__wrapped__", None)
same = ns["zusatz_selftest"] is st and any(fn is st for _n, fn in ns["SELFTEST_EXTRA"])
row = [i for i, ln in enumerate(own) if ln.startswith("zusatz_selftest = _zd_fn(")][0] + 1
print("PC " + json.dumps({"n": len(keys), "bad": bad[:5], "before": before, "res": str(res)[:60], "real": real is not None and real is not st and same,
                          "line": real.__code__.co_firstlineno == row, "file": os.path.basename(real.__code__.co_filename),
                          "again": str(st())[:20] == str(res)[:20], "miss": ns["ZD"]["miss"][:3],
                          "alm": [c[0] for c in ns["ALMANAC"]], "tip": bool(ns["almanac_tip"]()["title"]),
                          "hxk": [len(hk), hk[0][:12], hk[1] != k_, hk[3] != hk[0]], "trx": "Zermatt" in ns["TRX"]["fr"].get("Search a place (e.g. Zermatt)", ""),
                          "anl": "KI-Hilfe am Auslöser" in ns["HELP_PAGE"], "helfer": type(ns["ui_gem_check"]).__name__ == "function"
                                 and "_zd_fn('639p_ui_gemeinsam/ui_gem_check()')" in "".join(own)}))
'''
        rc, out = im_programm(prog, code, os.path.join(tmp, "h1"))
        r = zeile(out, "PC") or {}
        ok(rc == 0 and r.get("n", 0) >= 50 and r.get("bad") == [],
           "%s Prüfungen in der ZIP; jeder Platzhalter steht auf der Zeile seines «def», darunter leere Zeilen (%s)" % (r.get("n"), r.get("bad") if r else out[-800:]))
        ok(r.get("before") == ["zusatz_selftest", "function", False], "in der Hauptdatei steht nur der Platzhalter")
        ok(r.get("real") is True and r.get("line") is True and r.get("file") == os.path.basename(datei) and "literals" in str(r.get("res")),
           "erster Aufruf lädt die echte Funktion (Zeilennummer und Dateiname der Hauptdatei; der Name bleibt derselbe Platzhalter wie in SELFTEST_EXTRA): %s" % r.get("res"))
        ok(r.get("again") is True and r.get("miss") == [], "der Platzhalter ruft weiter die echte Funktion, nichts fehlt")
        print("6. Zweite Runde (mit ZIP)")
        ok(r.get("hxk") == [4, "Dieses Foto ", True, True], "_HX_PACK[PL_HEIC_MSG]: Deutsch aus der Datei, fr / it / rm aus der ZIP (%s)" % r.get("hxk"))
        ok(r.get("trx") is True, "kleine Übersetzung (TRX['fr'], Ortssuche) kommt aus der ZIP")
        ok(r.get("anl") is True, "Ergänzung der Anleitung (KI-Hilfe am Auslöser) steht in HELP_PAGE")
        ok(r.get("helfer") is True, "Hilfsfunktion ui_gem_check: in der Hauptdatei nur der Platzhalter")
        alm_mit = r.get("alm") or []

        zbytes = open(zpfad, "rb").read()
        kaputt = bytearray(zbytes)
        kaputt[len(kaputt) // 2] ^= 0x55
        code = r'''
res = {"ok": ns["ZD"]["ok"]}
try:
    ns["zusatz_selftest"]()
    res["call"] = "kein Fehler"
except RuntimeError as e:
    res["call"] = str(e)
ws = ns["WebStream"](None)
ns["GAMESRV"]["port"] = 1
ns["CFG"]["https_extra"] = False
ws._serve = lambda app, ctx: None
ws.start()
c = ws.app.test_client()
p = c.get("/almanach/")
t = p.get_data(as_text=True)
res.update(alm=[c_[0] for c_ in ns["ALMANAC"]], arts=[a[0] for a in ns["ALMANAC"][0][3]], tip=ns["almanac_tip"]()["chapter"],
           page=p.status_code, p144="144" in t and "Notrufnummern Schweiz" in t and "Seitenlage" in t,
           note="Zusatzdaten fehlen" in t and "/hilfe/fehler/DATA_MISSING" in t, n=len(t))
k_ = ns["PL_HEIC_MSG"]
hk = ns["_HX_PACK"][k_]
try:
    ns["ui_gem_check"]()
    res["helfer"] = "kein Fehler"
except RuntimeError as e:
    res["helfer"] = str(e)[:60]
except Exception as e:
    res["helfer"] = "anderer Fehler " + type(e).__name__
res.update(hxk=list(hk) == [hk[0], k_, k_, hk[0]] and hk[0].startswith("Dieses Foto"), de=ns["DE"].get(k_, "")[:12],
           trx=ns["TRX"]["fr"].get("Search a place (e.g. Zermatt)", ""), anl="KI-Hilfe am Auslöser" in ns["HELP_PAGE"])
print("OZ " + json.dumps(res, ensure_ascii=False))
'''
        for was, vorbereiten in (("ohne ZIP", lambda: os.remove(zpfad)), ("veränderte ZIP", lambda: open(zpfad, "wb").write(bytes(kaputt)))):
            vorbereiten()
            rc, out = im_programm(prog, code, os.path.join(tmp, "h2"))
            r = zeile(out, "OZ") or {}
            ok(rc == 0 and r.get("ok") is False and "Zusatzdaten fehlen" in str(r.get("call")) and "zusatz_selftest()" in str(r.get("call")),
               "%s: das Programm lädt, eine Prüfung meldet klar «Zusatzdaten fehlen» (%s)" % (was, (r.get("call") or out[-600:])[:90]))
            ok(str(r.get("helfer")).startswith("Zusatzdaten fehlen"), "%s: Hilfsfunktion des Prüf-Codes meldet «Zusatzdaten fehlen», führt nichts aus (%s)" % (was, r.get("helfer")))
            ok(r.get("hxk") is True and r.get("de") == "Dieses Foto " and r.get("trx") == "" and r.get("anl") is False,
               "%s: _zd_hxk gibt Deutsch (fr / it = Englisch), DE hat den Text; keine kleine Übersetzung, keine Ergänzung der Anleitung aus der ZIP" % was)
            if was == "ohne ZIP":
                print("4. Almanach")
                ok(len(alm_mit) >= 10 and alm_mit[0] == "notfall" and alm_mit[1] == "wetter", "mit ZIP: alle Kapitel, «Notfall» zuerst (%s)" % ", ".join(alm_mit))
            ok(r.get("alm") == ["notfall"] and "Notrufnummern Schweiz" in (r.get("arts") or []) and r.get("tip") == "Notfall",
               "%s: das Kapitel «Notfall» bleibt (%d Artikel), der Tipp des Abends kommt daraus" % (was, len(r.get("arts") or [])))
            ok(r.get("page") == 200 and r.get("p144") and r.get("note"),
               "%s: /almanach zeigt Notrufnummern und Erste Hilfe als einfache Seite mit dem Hinweis (%s Zeichen)" % (was, r.get("n")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("5. Folgezeilen mit Tabs")
    im_text = set()
    tief = start = 0
    fs_a, fs_e = getattr(tokenize, "FSTRING_START", -1), getattr(tokenize, "FSTRING_END", -1)
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.STRING:
            im_text.update(range(tok.start[0] + 1, tok.end[0] + 1))
        elif tok.type == fs_a:
            tief += 1
            start = tok.start[0] if tief == 1 else start
        elif tok.type == fs_e:
            tief -= 1
            if not tief:
                im_text.update(range(start + 1, tok.end[0] + 1))
    rest = [i for i, ln in enumerate(text.split("\n"), 1) if ln.startswith("    ") and ln.strip() and i not in im_text]
    ok(not rest, "keine Zeile ausserhalb von Texten beginnt mit vier Leerzeichen (%s)" % (rest[:5] or "0"))
    ast.parse(text)

    print("\n" + ("Hauptdatei-Grösse OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
