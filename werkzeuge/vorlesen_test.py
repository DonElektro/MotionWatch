#!/usr/bin/env python3
"""Test «📖 Vorlesen» und «👁 Datei-Ansicht» im Digitalen Rucksack (MoveEye Teil 639zzzzv) – ohne echte Stimme, ohne Lautsprecher.

Eigene Probe-Dateien (selbst geschrieben, hier erzeugt): Geschichte als .txt / .md / .epub (EPUB 3 mit Inhaltsverzeichnis, ein
<script> darin) / .docx (Überschriften) / .pdf (echter Text, 2 Seiten), dazu .csv, .json, .xlsx, .html, .dat, ein kaputtes
.epub, eine «Zip-Bombe» und ein .docx mit <!ENTITY. Die Stimme ist erfunden (Sinus-WAV pro Satz), der Lautsprecher ein kleines
Python-Programm, das die Bytes zählt.

  A) im eigenen Prozess (gebaute Datei, Flask-Testclient): Text aus allen Arten (Kapitel, Titel, Sprache, Sätze), Grenzen und
     kaputte Dateien = klare Meldung, Ansicht pro Art (Text / Tabelle / JSON / Code / Buch / Info / gefährlich), PDF-Seite als Bild,
     Rechte (Familie ja, Kind nein, nur ansehen = kein Inhalt, private Datei eines anderen = unbekannt, Lautsprecher nur mit «Sirene»),
     Lesezeichen pro Person und «Weiter», Ton eines Satzes + Vorausrechnen, Lautsprecher Satz für Satz (Bytes kommen), Pause durch
     Sirene / Ansage / Alarm und weiter danach, Stopp ohne Prozesse, Radio und Vorlesen schliessen sich aus (beide Richtungen),
     Löschen der Datei nimmt Text / Ton mit, Selbsttest-Funktion.
  B) --browser: MoveEye im Browser (Handy 390 px dunkel + PC): Rucksack mit «🔊 Vorlesen» und «▶ Weiter», Ansicht (epub, pdf,
     csv, json, txt mit «✎ Bearbeiten», xlsx = Info), /vorlesen: «📱 Handy» liest Satz für Satz (Markierung wandert), Wechsel auf
     eine andere Seite = liest weiter + 📖 im Kopf, Alarm = Pause und weiter, keine JS-Fehler, keine waagrechte Bildlaufleiste.
     --bilder ORDNER: Bildschirmfotos.

  python3 werkzeuge/vorlesen_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.request
import wave
import zipfile
from xml.sax.saxutils import escape

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


# ---- own sample files (written for this test) ---------------------------------------------------------------------------------------
KAP = [("Die Laterne am See", ["Am Rand des kleinen Bergsees stand eine alte Laterne. Niemand wusste mehr, wer sie dort aufgestellt hatte.",
                                "Jeden Abend ging sie von selbst an. Ihr Licht war warm und gelb, wie Honig im Glas."]),
       ("Flin fragt herum", ["Am nächsten Morgen fragte Flin die Murmeltiere. «Für die Wanderer», pfiff das älteste.",
                             "Dann fragte Flin die Eule. Sie dachte lange nach und sagte: «Vielleicht für den, der noch wach ist.»"]),
       ("Das Licht im Zelt", ["In dieser Nacht stand ein kleines Zelt am Ufer. Darin lag ein Kind und konnte nicht schlafen.",
                              "Da verstand Flin. Die Laterne leuchtete für alle, die sich ein bisschen fürchten."])]


def proben():
    P = {}
    P["Fuchs.txt"] = ("Der Fuchs und die Laterne\n\n" + "".join(f"Kapitel {i}: {h}\n\n" + "\n\n".join(ps) + "\n\n" for i, (h, ps) in enumerate(KAP, 1))).encode()
    P["Stern.md"] = ("# Die müde Sternschnuppe\n\nEs war einmal eine Sternschnuppe, die war *so müde*, dass sie langsam fiel.\n\n## Unterwegs\n\n"
                     "Sie flog über den Wald.\n\n```\ncode()\n```\n\n> Wer langsam fällt, sieht mehr.\n").encode()
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                   '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        items, spine, nav = [], [], []
        for i, (h, ps) in enumerate(KAP, 1):
            z.writestr(f"OEBPS/k{i}.xhtml", f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>T</title><script>alert(1)</script>'
                       f'</head><body><h1>{escape(h)}</h1>' + "".join(f"<p>{escape(p)}</p>" for p in ps) + "</body></html>")
            items.append(f'<item id="k{i}" href="k{i}.xhtml" media-type="application/xhtml+xml"/>'); spine.append(f'<itemref idref="k{i}"/>')
            nav.append(f'<li><a href="k{i}.xhtml">Kapitel {i}: {escape(h)}</a></li>')
        z.writestr("OEBPS/nav.xhtml", '<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">'
                   '<body><nav epub:type="toc"><ol>' + "".join(nav) + '</ol></nav></body></html>')
        z.writestr("OEBPS/content.opf", '<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
                   '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">probe</dc:identifier><dc:title>Geschichten vom Bergtal</dc:title>'
                   '<dc:language>de-CH</dc:language></metadata><manifest><item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml"/>'
                   + "".join(items) + '</manifest><spine>' + "".join(spine) + '</spine></package>')
    P["Bergtal.epub"] = b.getvalue()
    W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

    def docx(paras, extra=""):
        doc = f'<?xml version="1.0" encoding="UTF-8"?>{extra}<w:document {W}><w:body>' + "".join(
            (f'<w:p><w:pPr><w:pStyle w:val="{s}"/></w:pPr>' if s else "<w:p>") + f'<w:r><w:t>{escape(t)}</w:t></w:r></w:p>' for s, t in paras) + "</w:body></w:document>"
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", "<Types/>"); z.writestr("word/document.xml", doc)
        return b.getvalue()
    P["Wilma.docx"] = docx([("Heading1", "Die Wolke Wilma"), ("", "Wilma war eine kleine Wolke, die nie regnen wollte."),
                            ("Heading1", "Der Garten"), ("", "Da liess Wilma einen Tropfen los. Und sie wurde nur leichter.")])
    P["Entity.docx"] = docx([("", "x")], '<!DOCTYPE d [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;">]>')
    pages = [["Der Fuchs und die Laterne", "", "Kapitel 1: Die Laterne am See", ""] + [l for p in KAP[0][1] for l in textwrap.wrap(p, 72) + [""]],
             ["Kapitel 2: Flin fragt herum", ""] + [l for p in KAP[1][1] for l in textwrap.wrap(p, 72) + [""]]]
    objs = ["<</Type/Catalog/Pages 2 0 R>>", None, "<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>"]
    kids = []
    for pg in pages:
        st = ("BT /F1 13 Tf 50 760 Td 17 TL\n" + "\n".join("(" + x.replace("(", "\\(").replace(")", "\\)") + ") '" for x in pg) + "\nET").encode("cp1252")
        objs.append(b"<</Length %d>>stream\n" % len(st) + st + b"\nendstream"); cid = len(objs)
        objs.append(f"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Contents {cid} 0 R/Resources<</Font<</F1 3 0 R>>>>>>"); kids.append(len(objs))
    objs[1] = "<</Type/Pages/Kids[" + " ".join(f"{k} 0 R" for k in kids) + f"]/Count {len(kids)}>>"
    b = bytearray(b"%PDF-1.4\n"); offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(b)); b += f"{i} 0 obj\n".encode() + (o if isinstance(o, bytes) else o.encode()) + b"\nendobj\n"
    x = len(b)
    b += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + "".join(f"{o:010d} 00000 n \n" for o in offs).encode()
    b += f"trailer<</Size {len(objs) + 1}/Root 1 0 R>>\nstartxref\n{x}\n%%EOF\n".encode()
    P["Fuchs_Druck.pdf"] = bytes(b)
    P["Etappen.csv"] = "Tag;Von;Nach;km\n1;Luzern;Engelberg;34\n2;Engelberg;\"Trübsee; oben\";9\n3;Trübsee;Sarnen;26\n".encode()
    P["Ausruestung.json"] = json.dumps({"zelt": {"personen": 3}, "kocher": ["Gas"], "fertig": False}).encode()
    P["Tabelle.xlsx"] = b"PK\x03\x04" + b"0" * 500
    P["Seite.html"] = b"<script>alert(1)</script>"
    P["Messung.dat"] = bytes(range(256)) * 8
    P["Kaputt.epub"] = b"PK\x03\x04 nicht wirklich"
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/container.xml", b"<a>" + b" " * (9 * 1024 * 1024) + b"</a>")
    P["Bombe.epub"] = b.getvalue()
    return P


SYNTH = r'''
def _vt_synth(text, lang, speed, out):
    import wave as _w, numpy as _n
    n = int(22050 * min(0.6, 0.12 + 0.004 * len(text)) / max(0.5, float(speed)))
    y = (_n.sin(_n.arange(n) * 2 * _n.pi * 440 / 22050) * 8000).astype("<i2")
    with _w.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(y.tobytes())
    _VT_SAID.append((text, lang))
    return True, ""
_VT_SAID = []
'''

SINK = r'''
import sys, os, time
f = sys.argv[1]; n = 0
while True:
    b = sys.stdin.buffer.read(2205)
    if not b:
        break
    n += len(b)
    with open(f, "w") as o:
        o.write(str(n))
    time.sleep(len(b) / 2 / float(sys.argv[2]) * 0.5)
'''


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei, tmp):
    print("A) im eigenen Prozess", flush=True)
    os.environ["MOTIONWATCH_HOME"] = os.path.join(tmp, "home"); os.makedirs(os.environ["MOTIONWATCH_HOME"])
    ns = {"__name__": "mw_vorlesen_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    exec(SYNTH, ns)
    CFG, TZ, VL, RADIO, SOUND = ns["CFG"], ns["TZ"], ns["VL"], ns["RADIO"], ns["SOUND"]
    root = os.path.join(tmp, "rucksack"); os.makedirs(root)
    TZ["root_test"] = root
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_push=False, audio_out="default", audio_in="")
    ns["tausch_disk_free"] = lambda p: 100 * ns["TZ_GB"]
    VL["synth"] = ns["_vt_synth"]
    sinkf = os.path.join(tmp, "sink.py"); open(sinkf, "w").write(SINK)
    cnt = os.path.join(tmp, "bytes.txt")
    ns["out_cmd"] = lambda rate, connect=True: ([sys.executable, sinkf, cnt, str(rate), "mwvlsink"], "")
    ns["out_selected"] = lambda: True
    PW = "Admin-Pass-123"
    assert ns["web_pw_set"](PW)[0]
    users = {"Anna": "family", "Bob": "friend", "Kim": "kid", "Vera": "view", "Cus": "custom", "Carl": "family"}
    for n_, r in users.items():
        assert ns["users_action"]({"action": "add", "name": n_, "password": n_.lower() + "-pass-1", "role": r})[0]
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live", "files_view"]})
    ws = ns["WebStream"](None); ws._serve = lambda app, ctx: None; ws.start()
    c = ws.app.test_client(use_cookies=False)
    H = {n_: basic(n_, n_.lower() + "-pass-1") for n_ in users}
    H["admin"] = basic("admin", PW)

    def get(who, u):
        r = c.get(u, headers=H[who])
        return r.status_code, (r.get_json(silent=True) if r.mimetype == "application/json" else r.data)

    def post(who, u, d):
        r = c.post(u, json=dict(d, lang="de"), headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def up(who, name, data, area="all"):
        code, j = post(who, "/api/tausch", {"action": "start", "name": name, "size": len(data), "area": area, "folder": ""})
        assert code == 200, (name, code, j)
        off = 0
        while off < len(data):
            r = c.post(f"/api/tausch/chunk?id={j['id']}&off={off}", data=data[off:off + j["chunk"]], headers=dict(H[who], **{"Content-Type": "application/octet-stream"}))
            off = r.get_json()["have"]
        code, k = post(who, "/api/tausch", {"action": "finish", "id": j["id"]})
        assert code == 200, (name, code, k)
        return k["file"]["id"]
    P = proben()
    F = {n_: up("Anna", n_, d) for n_, d in P.items()}
    F["Privat.txt"] = up("Carl", "Privat.txt", b"Nur fuer Carl. Geheim.", area="mine")
    have_pdf = bool(shutil.which("pdftotext") and shutil.which("pdftoppm"))

    # -- text out of every kind
    code, j = get("Anna", f"/api/vorlesen?id={F['Bergtal.epub']}&lang=de")
    ok(code == 200 and j["title"] == "Geschichten vom Bergtal" and j["lang"] == "de" and len(j["ch"]) == 3, f"epub: Titel, Sprache, 3 Kapitel ({code})")
    ok(j and j["ch"][1]["t"] == "Kapitel 2: Flin fragt herum" and "alert" not in json.dumps(j), "epub: Kapiteltitel aus dem Inhaltsverzeichnis, kein <script>")
    ok(j and j["ch"][0]["p"][0] == ["Am Rand des kleinen Bergsees stand eine alte Laterne.", "Niemand wusste mehr, wer sie dort aufgestellt hatte."], "epub: Sätze")
    ok(j and j["voice"]["lang"] == "de" and j["may"]["pi"] and j["bm"] is None, "epub: Stimme de, Lautsprecher erlaubt, noch kein Lesezeichen")
    code, j = get("Anna", f"/api/vorlesen?id={F['Fuchs.txt']}")
    ok(code == 200 and j["title"] == "Der Fuchs und die Laterne" and [c_["t"] for c_ in j["ch"]] == [f"Kapitel {i}: {h}" for i, (h, _p) in enumerate(KAP, 1)], "txt: Titel + Kapitel")
    code, j = get("Anna", f"/api/vorlesen?id={F['Stern.md']}")
    ok(code == 200 and j["ch"][0]["t"] == "Die müde Sternschnuppe" and "code()" not in json.dumps(j) and "*" not in json.dumps(j["ch"]), "md: Überschrift, ohne Code und Sternchen")
    code, j = get("Anna", f"/api/vorlesen?id={F['Wilma.docx']}")
    ok(code == 200 and [c_["t"] for c_ in j["ch"]] == ["Die Wolke Wilma", "Der Garten"], "docx: Überschriften = Kapitel")
    if have_pdf:
        code, j = get("Anna", f"/api/vorlesen?id={F['Fuchs_Druck.pdf']}")
        ok(code == 200 and j["title"] == "Der Fuchs und die Laterne" and any("Flin" in c_["t"] for c_ in j["ch"]), f"pdf: Text und Kapitel ({code})")
    else:
        print("  (pdftotext fehlt – PDF-Text nicht geprüft)")
    for n_, why in (("Kaputt.epub", "kaputtes epub"), ("Bombe.epub", "Zip-Bombe"), ("Entity.docx", "<!ENTITY")):
        code, j = get("Anna", f"/api/vorlesen?id={F[n_]}")
        ok(code == 400 and j.get("error"), f"{why}: klare Meldung statt Absturz ({code})")
    code, j = get("Anna", f"/api/vorlesen?id={F['Etappen.csv']}")
    ok(code == 400, "csv wird nicht vorgelesen")

    # -- the viewer
    def view(n_, who="Anna"):
        return get(who, f"/api/tausch/ansicht?id={F[n_]}&lang=de")
    _c, j = view("Fuchs.txt"); ok(j["type"] == "text" and "Laterne" in j["text"] and not j["md"], "Ansicht: txt = Text")
    _c, j = view("Stern.md"); ok(j["type"] == "text" and j["md"], "Ansicht: md = Text mit Markdown")
    _c, j = view("Etappen.csv"); ok(j["type"] == "table" and "Trübsee; oben" in j["text"], "Ansicht: csv = Tabelle")
    _c, j = view("Ausruestung.json"); ok(j["type"] == "json", "Ansicht: json")
    _c, j = view("Bergtal.epub"); ok(j["type"] == "book" and len(j["ch"]) == 3 and isinstance(j["ch"][0]["p"][0], str), "Ansicht: epub = Buch")
    _c, j = view("Wilma.docx"); ok(j["type"] == "book" and j["ch"][0]["t"] == "Die Wolke Wilma", "Ansicht: docx = Buch")
    _c, j = view("Tabelle.xlsx"); ok(j["type"] == "info", "Ansicht: xlsx = Info-Karte")
    _c, j = view("Seite.html"); ok(j["type"] == "info" and j.get("risky") and "alert" not in json.dumps(j), "Ansicht: html = nur Info (gefährlich)")
    _c, j = view("Messung.dat"); ok(j["type"] == "info", "Ansicht: unbekannt = Info")
    _c, j = view("Kaputt.epub"); ok(j["type"] == "book" and j.get("error"), "Ansicht: kaputtes epub = Meldung")
    if have_pdf:
        _c, j = view("Fuchs_Druck.pdf"); ok(j["type"] == "book" and j["pages"] == 2 and j["tool"], f"Ansicht: pdf = 2 Seiten ({j.get('pages')})")
        code, b = get("Anna", f"/tausch/seite/{F['Fuchs_Druck.pdf']}/1.jpg")
        ok(code == 200 and b[:3] == b"\xff\xd8\xff", "PDF-Seite als JPEG")
        ok(get("Anna", f"/tausch/seite/{F['Fuchs_Druck.pdf']}/9.jpg")[0] == 404, "PDF: Seite, die es nicht gibt = 404")
        ok(get("Anna", f"/tausch/seite/{F['Fuchs.txt']}/1.jpg")[0] == 404, "Seitenbild nur für PDF")
    keep_which = ns["vl_tool"]
    ns["vl_tool"] = lambda n_: ""
    VL["books"].clear(); VL["pdf"].clear()
    try:
        os.remove(os.path.join(root, "vl", F["Fuchs_Druck.pdf"] + ".json"))
    except OSError:
        pass
    _c, j = view("Fuchs_Druck.pdf"); ok(j["type"] == "book" and not j["tool"] and j.get("need") == "poppler" and "poppler" in (j.get("error") or ""), "ohne poppler-utils: Hinweis + Installation anbieten")
    code, j = post("Anna", "/api/vorlesen", {"action": "poppler"}); ok(code == 403, "poppler installieren: nur der Administrator")
    ns["vl_tool"] = keep_which

    # -- rights
    ok(get("Kim", f"/api/vorlesen?id={F['Fuchs.txt']}")[0] == 403 and get("Kim", "/vorlesen")[0] == 403, "Kind: kein Vorlesen")
    ok(get("Kim", f"/api/tausch/ansicht?id={F['Fuchs.txt']}")[0] == 403, "Kind: keine Ansicht")
    ok(get("Cus", f"/api/vorlesen?id={F['Fuchs.txt']}")[0] == 403 and get("Cus", f"/api/tausch/ansicht?id={F['Fuchs.txt']}")[0] == 403, "nur ansehen (ohne Herunterladen): kein Inhalt")
    ok(get("Anna", f"/api/vorlesen?id={F['Privat.txt']}")[0] == 404 and get("Anna", f"/api/vorlesen/audio?id={F['Privat.txt']}&c=0&s=0")[0] == 404, "private Datei eines anderen: unbekannt")
    ok(get("Carl", f"/api/vorlesen?id={F['Privat.txt']}")[0] == 200 and get("admin", f"/api/vorlesen?id={F['Privat.txt']}")[0] == 200, "eigene private Datei / Admin: ja")
    code, j = post("Bob", "/api/vorlesen", {"action": "play", "id": F["Fuchs.txt"]})
    ok(code == 403 and "Sirene" in (j.get("error") or ""), "Freund (ohne «Sirene»): nicht auf dem Lautsprecher")
    ok(get("Bob", f"/api/vorlesen?id={F['Fuchs.txt']}")[1]["may"]["pi"] is False, "Freund: Seite weiss es (may.pi)")

    # -- bookmarks
    ok(post("Anna", "/api/vorlesen", {"action": "bm", "id": F["Bergtal.epub"], "c": 1, "s": 2, "now": 1})[0] == 200, "Lesezeichen speichern")
    ok(get("Anna", f"/api/vorlesen?id={F['Bergtal.epub']}")[1]["bm"]["c"] == 1, "Lesezeichen zurück")
    ok(get("Carl", f"/api/vorlesen?id={F['Bergtal.epub']}")[1]["bm"] is None, "Lesezeichen pro Person")
    _c, j = get("Anna", "/api/vorlesen?last=1"); ok(j["last"] and j["last"]["id"] == F["Bergtal.epub"] and 0 < j["last"]["pct"] < 100, "«Weiter»: das zuletzt Gelesene")
    _c, j = get("Anna", "/api/vorlesen?bms=1"); ok(F["Bergtal.epub"] in j["bms"], "Lesezeichen-Liste")
    ok(os.path.isfile(os.path.join(root, "vl", "lesezeichen.json")), "Lesezeichen auf dem Gerät (beim Rucksack)")

    # -- sound of a sentence + ahead
    r = c.get(f"/api/vorlesen/audio?id={F['Bergtal.epub']}&c=0&s=0&lang=de", headers=H["Anna"])
    ok(r.status_code == 200 and r.mimetype == "audio/wav" and r.data[:4] == b"RIFF", "Ton eines Satzes (WAV)")
    ok(c.get(f"/api/vorlesen/audio?id={F['Bergtal.epub']}&c=9&s=0", headers=H["Anna"]).status_code == 400, "Satz, den es nicht gibt = 400")
    t0 = time.time()
    while time.time() - t0 < 5 and len([x for x in os.listdir(os.path.join(root, "vl", "ton")) if x.startswith(F["Bergtal.epub"]) and x.endswith(".wav") and ".tmp" not in x]) < 3:
        time.sleep(0.1)
    ok(len([x for x in os.listdir(os.path.join(root, "vl", "ton")) if x.startswith(F["Bergtal.epub"])]) >= 3, "die nächsten Sätze werden vorausgerechnet")

    # -- the loudspeaker
    ns["_vt_said"] = ns["_VT_SAID"]; del ns["_VT_SAID"][:]
    code, j = post("Anna", "/api/vorlesen", {"action": "play", "id": F["Fuchs.txt"], "c": 0, "s": 0})
    ok(code == 200 and j["pi"]["on"], f"Lautsprecher: Start ({code} {j.get('error')})")

    def wait(cond, sec=6):
        t1 = time.time()
        while time.time() - t1 < sec:
            if cond():
                return True
            time.sleep(0.05)
        return False

    def nbytes():
        try:
            return int(open(cnt).read() or 0)
        except (OSError, ValueError):
            return 0
    ok(wait(lambda: nbytes() > 2000), "Lautsprecher: Ton kommt an")
    ok(wait(lambda: VL["s"] >= 2 or VL["c"] > 0), "Lautsprecher: Satz für Satz weiter")
    ok(ns["_VT_SAID"] and ns["_VT_SAID"][0][1] == "de", "Stimme der Buchsprache")
    SOUND.update(playing=True, kind="siren")
    ok(wait(lambda: VL["held"] == "siren" and VL["out"] is None), "Sirene: Vorlesen pausiert, Lautsprecher frei")
    st = get("Anna", "/api/vorlesen?on=1&full=1")[1]
    ok(st["hold"] and "Sirene" in st["pi"]["held"], "Pause auch für den Browser gemeldet (hold)")
    pos = (VL["c"], VL["s"]); SOUND["playing"] = False
    ok(wait(lambda: VL["held"] == "" and VL["state"] == "playing"), "nach der Sirene: liest weiter")
    ok((VL["c"], VL["s"]) >= pos, "weiter an derselben Stelle (der Satz nochmals)")
    ns["radio_yield"]("voice")
    ok(wait(lambda: VL["held"] == "voice", 2), "Ansage (radio_yield): Pause")
    ns["is_armed"] = lambda: True
    ns["push_alert"]("person", "person")
    ok(wait(lambda: VL["held"] == "alarm", 3), "Alarm: Pause")
    VL["alarm_t"] = 0.0
    ok(wait(lambda: VL["held"] == ""), "nach dem Alarm: weiter")
    post("Anna", "/api/vorlesen", {"action": "pause"}); ok(wait(lambda: VL["held"] == "pause"), "⏸ Pause")
    post("Anna", "/api/vorlesen", {"action": "resume"}); ok(wait(lambda: VL["held"] == ""), "▶ weiter")
    post("Anna", "/api/vorlesen", {"action": "seek", "c": 2, "s": 0}); ok(wait(lambda: VL["c"] == 2), "⏭ springen")
    post("Anna", "/api/vorlesen", {"action": "volume", "v": 33}); ok(CFG["vl_volume"] == 33, "Lautstärke")
    # radio <-> reading
    keep_rp = ns["_radio_play_vl"]; ns["_radio_play_vl"] = lambda *a, **k: (True, "")
    ns["radio_play"]("pilatus")
    ok(not VL["want"] and VL["state"] == "off", "Radio startet: Vorlesen stoppt")
    ok(wait(lambda: VL["out"] is None and not [d for d in os.listdir("/proc") if d.isdigit() and _cmd(d).endswith("mwvlsink")], 4), "Stopp: kein Lautsprecher-Prozess mehr")
    ns["_radio_play_vl"] = keep_rp
    _c, j = get("Anna", "/api/vorlesen?bms=1"); ok(j["bms"][F["Fuchs.txt"]]["c"] == 2, "Lesezeichen beim Stopp gesichert")
    RADIO["want"] = True
    stopped = []
    keep_rs = ns["radio_stop"]; ns["radio_stop"] = lambda *a, **k: stopped.append(a) or RADIO.update(want=False)
    post("Anna", "/api/vorlesen", {"action": "play", "id": F["Fuchs.txt"]})
    ok(stopped and not RADIO["want"], "Vorlesen auf dem Lautsprecher: Radio stoppt")
    post("Anna", "/api/vorlesen", {"action": "stop"}); ok(not VL["want"], "⏹ Stopp")
    RADIO["want"] = True; del stopped[:]
    post("Anna", "/api/vorlesen", {"action": "bplay", "id": F["Fuchs.txt"]})
    ok(stopped, "Vorlesen im Browser: Radio stoppt")
    ns["radio_stop"] = keep_rs
    # delete = caches go too
    post("Anna", "/api/vorlesen", {"action": "play", "id": F["Bergtal.epub"]})
    ok(wait(lambda: VL["state"] == "playing"), "Lautsprecher liest das E-Book")
    post("Anna", "/api/tausch", {"action": "delete", "id": F["Bergtal.epub"]})
    ok(not VL["want"], "Datei gelöscht: Vorlesen stoppt")
    ok(not [x for x in os.listdir(os.path.join(root, "vl")) + os.listdir(os.path.join(root, "vl", "ton")) if x.startswith(F["Bergtal.epub"])], "Datei gelöscht: Text und Ton weg")
    ok(F["Bergtal.epub"] not in get("Anna", "/api/vorlesen?bms=1")[1]["bms"], "Datei gelöscht: kein Lesezeichen mehr in der Liste")
    try:
        r_ = ns["vorlesen_selftest"](); ok(True, ""); print("  Selbsttest:", r_)
    except Exception as e:
        ok(False, "Selbsttest-Funktion: " + repr(e)[:200])
    print(f"  A: {N['ok']} ok", flush=True)


def _cmd(pid):
    try:
        return open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
    except OSError:
        return ""


# ---------------------------------------------------------------------------------------------------------------------- B
WRAP = r'''
import os, sys, threading, time
d = sys.argv[1]; sys.argv = [d] + sys.argv[2:]
ns = {"__name__": "__main__", "__file__": os.path.abspath(d)}
exec(os.environ["MW_VT_SYNTH"], ns)
def hook():
    while "VL" not in ns or "_vt_synth" not in ns:
        time.sleep(0.05)
    ns["VL"]["synth"] = ns["_vt_synth"]
    flag = os.environ["MW_VT_ALARM"]
    while True:
        if os.path.exists(flag):
            ns["VL"]["alarm_t"] = time.time()
        time.sleep(0.3)
threading.Thread(target=hook, daemon=True).start()
exec(compile(open(d, encoding="utf-8").read(), d, "exec"), ns)
'''


def teil_b(datei, tmp, bilder):
    print("B) Browser", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    cfg = os.path.join(tmp, "b_mw"); os.makedirs(cfg)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "theme": "dark",
          "tausch_free_gb": 0.1, "news_popup": False, "audio_out": ""}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Vorlesen-" + os.urandom(4).hex()
    alarm = os.path.join(tmp, "alarm.flag")
    env = dict(os.environ, HOME=os.path.join(tmp, "bhome"), MOTIONWATCH_HOME=cfg, MW_VT_SYNTH=SYNTH, MW_VT_ALARM=alarm)
    os.makedirs(env["HOME"])
    logf = open(os.path.join(tmp, "b_log.txt"), "w")
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", PW],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    A = basic("admin", PW)

    def req(path, data=None, raw=None, ctype="application/json"):
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None), headers=dict(A, **{"Content-Type": ctype}))
        try:
            with op.open(r, timeout=30) as x:
                return x.status, x.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def up(name, data):
        _c, b = req("/api/tausch", {"action": "start", "name": name, "size": len(data), "area": "all", "folder": ""})
        j = json.loads(b); off = 0
        while off < len(data):
            _c, b = req(f"/api/tausch/chunk?id={j['id']}&off={off}", raw=data[off:off + j["chunk"]], ctype="application/octet-stream")
            off = json.loads(b)["have"]
        return json.loads(req("/api/tausch", {"action": "finish", "id": j["id"]})[1])["file"]["id"]
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "b_log.txt"), errors="replace").read()[-3000:])
            try:
                if req("/manifest.webmanifest")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        P = proben()
        F = {}
        for n_ in ("Ausruestung.json", "Etappen.csv", "Tabelle.xlsx", "Fuchs_Druck.pdf", "Wilma.docx", "Stern.md", "Fuchs.txt", "Bergtal.epub"):
            F[n_] = up(n_, P[n_]); time.sleep(0.2)
        req("/api/vorlesen", {"action": "bm", "id": F["Fuchs.txt"], "c": 1, "s": 0, "now": 1})
        time.sleep(2)
        errs = []
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
            for nm, vp, mob in (("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1366, "height": 860}, False)):
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, extra_http_headers=A, locale="de-CH", color_scheme="dark")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('tausch-view','list')}catch(e){}")
                g = ctx.new_page(); g.on("pageerror", lambda e, nm=nm: errs.append(nm + ": " + str(e)[:200]))
                g.goto(base + "/tausch#dateien"); g.wait_for_selector(".tz-it", timeout=20000); g.wait_for_timeout(1500)
                ok(g.locator("a.vl-chip").count() == 5, f"{nm}: «🔊 Vorlesen» bei 5 Geschichten ({g.locator('a.vl-chip').count()})")
                ok(g.locator("#vl-cont").count() == 1 and ("Fuchs" if mob else "Bergtal") in g.inner_text("#vl-cont"), f"{nm}: «▶ Weiter» oben (das zuletzt Gelesene)")
                ok("Kap. 2" in g.inner_text(f'a.vl-chip[data-vl="{F["Fuchs.txt"]}"]'), f"{nm}: Lesezeichen am Knopf")
                ok(g.evaluate("document.documentElement.scrollWidth") <= vp["width"], f"{nm}: keine waagrechte Bildlaufleiste (Liste)")
                g.screenshot(path=os.path.join(bilder, f"1_rucksack_{nm}.png"), full_page=True)

                def open_(name):
                    g.evaluate("document.querySelectorAll('#tz-viewer,.tz-lb').forEach(x => x.remove())")
                    g.locator(".tz-it", has_text=name).locator(".th").click(); g.wait_for_selector("#tz-viewer", timeout=5000); g.wait_for_timeout(700)
                open_("Bergtal.epub"); ok("Flin" in g.inner_text("#tz-viewer") or "Laterne" in g.inner_text("#tz-viewer"), f"{nm}: Ansicht epub")
                ok(g.evaluate("document.querySelector('#tz-viewer').innerHTML.includes('<script')") is False, f"{nm}: kein Skript aus dem epub")
                g.screenshot(path=os.path.join(bilder, f"4_ansicht_epub_{nm}.png"))
                if shutil.which("pdftoppm"):
                    open_("Fuchs_Druck.pdf"); g.wait_for_function("() => [...document.querySelectorAll('#tz-viewer .vw-pages img')].some(i => i.complete && i.naturalWidth > 100)", timeout=20000)
                    ok(g.locator("#tz-viewer .vw-pages img").count() == 2, f"{nm}: PDF 2 Seiten als Bilder")
                    g.screenshot(path=os.path.join(bilder, f"4_ansicht_pdf_{nm}.png"))
                open_("Etappen.csv"); ok(g.locator("#tz-viewer table.vw-tbl tbody tr").count() == 3 and "Trübsee; oben" in g.inner_text("#tz-viewer"), f"{nm}: CSV-Tabelle (Anführungszeichen)")
                g.locator("#tz-viewer th", has_text="km").click(); g.wait_for_timeout(200)
                ok(g.inner_text("#tz-viewer tbody tr:first-child td:last-child").strip() == "9", f"{nm}: Spalte sortieren (Zahlen)")
                g.screenshot(path=os.path.join(bilder, f"4_ansicht_csv_{nm}.png"))
                open_("Ausruestung.json"); ok(g.locator("#tz-viewer .vw-code .k").count() >= 3, f"{nm}: JSON mit Farben")
                if mob:
                    g.screenshot(path=os.path.join(bilder, f"4_ansicht_json_{nm}.png"))
                open_("Fuchs.txt"); ok(g.locator("#tz-viewer button", has_text="✎").count() == 1 and "Laterne" in g.inner_text("#tz-viewer"), f"{nm}: txt = Lese-Ansicht mit ✎")
                g.locator("#tz-viewer button", has_text="✎").click(); g.wait_for_selector("#tz-editor", timeout=5000)
                ok(g.locator("#tz-ta").count() == 1, f"{nm}: ✎ öffnet den Editor")
                g.evaluate("document.querySelectorAll('#tz-editor').forEach(x => x.remove())")
                open_("Tabelle.xlsx"); ok(g.locator("#tz-viewer .vw-unk").count() == 1, f"{nm}: xlsx = Info-Karte")
                if mob:
                    g.screenshot(path=os.path.join(bilder, f"4_ansicht_info_{nm}.png"))
                    open_("Wilma.docx"); g.screenshot(path=os.path.join(bilder, f"4_ansicht_docx_{nm}.png"))
                g.evaluate("document.querySelectorAll('#tz-viewer').forEach(x => x.remove())")
                # the reader: «📱 Handy»
                g.goto(base + f"/vorlesen?id={F['Bergtal.epub']}"); g.wait_for_selector("#vl-box:not([hidden])", timeout=15000); g.wait_for_timeout(500)
                ok("Geschichten vom Bergtal" in g.inner_text("#vl-title") and g.locator("#vl-txt .s").count() >= 3, f"{nm}: Vorleser zeigt Text")
                g.click("#vl-go")
                ok(_wait(g, "() => { const P = window.mwReadP; return P && P.S.on && (P.S.s >= 2 || P.S.c > 0); }", 15), f"{nm}: liest Satz für Satz im Browser")
                ok(g.locator("#vl-txt .s.cur").count() == 1, f"{nm}: aktueller Satz markiert")
                g.screenshot(path=os.path.join(bilder, f"2_vorleser_{nm}.png"))
                open(alarm, "w").close()
                ok(_wait(g, "() => !!window.mwReadP.S.hold", 8), f"{nm}: Alarm = Pause im Browser")
                g.wait_for_timeout(400); ok(g.locator("#vl-warn:not([hidden])").count() == 1, f"{nm}: Hinweis «Pausiert: Alarm»")
                g.screenshot(path=os.path.join(bilder, f"2b_vorleser_alarm_{nm}.png"))
                os.remove(alarm)
                ok(_wait(g, "() => !window.mwReadP.S.hold && window.mwReadP.S.st === 'playing'", 30), f"{nm}: nach dem Alarm weiter")
                if mob:
                    g.click("#vl-toc"); g.wait_for_timeout(300); g.screenshot(path=os.path.join(bilder, f"2c_vorleser_inhalt_{nm}.png")); g.click("#vl-pan button")
                # another page: it reads on, 📖 in the header
                g.evaluate("() => window.mwReadP.seek(0, 0)")          # the sample book is short: from the start again
                g.locator("header nav a[href='/protect']").first.click()
                g.wait_for_timeout(2500)
                on = g.evaluate("() => { const P = window.mwReadP; return !!(P && P.S.on); }")
                ok(on, f"{nm}: andere Seite – liest weiter (Spieler im Hauptfenster)")
                vis = g.evaluate("() => [document, ...[...document.querySelectorAll('iframe')].map(f => { try { return f.contentDocument; } catch (e) { return null; } })]"
                                 ".some(d => d && d.querySelector('#mwk-read') && !d.querySelector('#mwk-read').hidden)")
                ok(vis, f"{nm}: 📖 im Kopf")
                g.screenshot(path=os.path.join(bilder, f"3_kopf_buch_{nm}.png"))
                ok(g.evaluate("document.documentElement.scrollWidth") <= vp["width"], f"{nm}: keine waagrechte Bildlaufleiste")
                g.evaluate("() => window.mwReadP && window.mwReadP.stop()")
                ctx.close()
            br.close()
        ok(not errs, "keine JS-Fehler: " + "; ".join(errs[:3]))
    finally:
        p.terminate()
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()


def _wait(g, js, sec):
    try:
        g.wait_for_function(js, timeout=sec * 1000)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei"); ap.add_argument("--browser", action="store_true"); ap.add_argument("--bilder")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or neueste())
    tmp = tempfile.mkdtemp(prefix="mw_vorlesen_test_")
    try:
        teil_a(datei, tmp)
        if a.browser:
            teil_b(datei, tmp, a.bilder or os.path.join(tmp, "bilder"))
    finally:
        if not a.bilder:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"{N['ok']} ok, {len(FEHLER)} Fehler")
    if FEHLER:
        print("FEHLER:\n  " + "\n  ".join(FEHLER))
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
