#!/usr/bin/env python3
"""Test «🎒 Packlisten» im Datentausch (Teil 639zzw) – ohne Kamera, ohne echten USB-Stick:

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei (schnell):
     Lesen: Gewichte («350 g», «1.2 kg», «0,5kg», «1'200 g»), Zeilen einer Notiz (Aufzählungszeichen, Nummern, Kästchen,
     «2x Socken», «Zelt (1.8 kg)», Überschriften, Flüssigkeiten, «kaufen»), CSV (Komma / Strichpunkt / Tabulator, mit und ohne
     Kopfzeile, UTF-8 mit / ohne BOM, Windows-1252, Dezimalkomma, Anführungszeichen), eingefügte Tabelle, eine hier erzeugte
     .xlsx (gemeinsame Texte, Inline-Texte, Formel mit gespeichertem Wert, Lücke in der Zeile), abgewiesen: ZIP-Bombe, zu viele
     Einträge, DOCTYPE / ENTITY, .xls, PDF, zu grosse Datei.
     Listen: anlegen (auch aus Vorlage), ändern, kopieren (mit Fotos), löschen; Summen, Basis / Verbrauch / am Körper, Ziel;
     Einkaufsansicht (Daten); Foto über den Stück-Upload des Datentausches (verkleinert, nie als Datei im Datentausch, HEIC
     klar abgewiesen, Pixelbombe abgewiesen); zwei Clients haken gleichzeitig ab (beides bleibt), dasselbe Feld (das letzte
     gilt), «nur das Neue seit …»; Rechte je Rolle + «Eigene Rechte» + privat + Gast (auch aus / abgelaufen), 403 ohne Zugang;
     Export CSV (Schutz vor Formeln) und wieder herein, JSON, ZIP; Text mit HTML bleibt Text (Druck- und Gast-Seite, kein
     innerHTML in der Seite); Grenzen; Pfade; fremde Origin; Schreiben mit Nebendatei (Fehler lässt die alte Liste stehen).
  B) --browser: MoveEye ohne Fenster starten, Playwright «iPhone 13» (Grösse, Touch – der Motor ist Chromium, NICHT Safari):
     Kachel im Datentausch, Übersicht, Liste mit Fotos und Symbolen, schnell eintragen, bearbeiten, Foto über die Seite,
     Import (Text und Tabelle) mit Vorschau, Einkaufsansicht, Gewichtsziel, zwei Handys packen gemeinsam, Druckansicht, Gast;
     nichts ragt seitlich hinaus, Tippflächen ≥ 44 px, keine Konsolen-Fehler, keine Anfrage nach aussen. Bildschirmfotos.

  python3 werkzeuge/packlisten_test.py [--datei X.py] [--browser] [--nur-browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}
XSS = '<img src=x onerror="window.__xss=1">'


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def laden(datei):
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_pl_home_")
    ns = {"__name__": "mw_packlisten_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


# ---- sample files (written here: nothing of the owner's real lists is in the repository) ------------------------------------------
NOTIZ = """Wochenende Jura

SCHLAFEN
- Zelt (1.8 kg)
- Schlafsack – 950 g
- Isomatte\t480
• Kissen 80g

Küche:
1. Gaskocher 90 g
2. 2x Gaskartusche 230 g (kaufen)
3) Topf 0,25 kg
- [x] Löffel 20 g
- [ ] Feuerzeug
☐ Schwamm

## Kleider
2 Paar Socken à 80 g
Regenjacke ~350g
3 XL Shirts 150 g
Mütze, rot 70 g
Handschuhe x2 60 g

Wasser:
Wasser 1,5 l
Trinkflasche 1'150 g

---
Stirnlampe: 85 g
Karte 1:25000 Blatt 1105
"""

CSV_KOMMA = 'Item,Weight,Qty,Category,Notes\n"Tent, 2 person",1.8 kg,1,Shelter,"with footprint"\nSpork,17 g,2,Kitchen,\nPower bank,230 g,1,Electronics,"10,000 mAh"\n'
CSV_1252 = "Gegenstand;Gewicht (kg);Anzahl;Kategorie;Bemerkung\r\nKäse;0,25;2;Essen;vom Märit\r\nMüesli;0,5;1;Essen;\r\nZelt «Hubba»;1,72;1;Schlafen;\r\nWärmflasche;0,3;1;;\r\n"
TSV_OHNE = "Zelt\t1800\nSchlafsack\t950\nKüche:\t\nKocher\t90\nRiegel\t45\n"
TABELLE_NOTIZEN = "Was\tGramm\tStück\nStirnlampe\t85\t1\nBatterien AAA\t12\t3\nKarte\t90\t1\n"


def xlsx_bytes(rows, extra=None, sst_head="", inline=()):
    """a real little .xlsx made here: shared strings (one as rich text), numbers, a formula with its stored value, inline strings"""
    from xml.sax.saxutils import escape as x
    strs, out = [], []
    for r, row in enumerate(rows, 1):
        cs = []
        for c, v in enumerate(row):
            ref = chr(65 + c) + str(r)
            if v is None:
                continue                                     # a gap: the next cell still names its column
            if isinstance(v, tuple):
                cs.append(f'<c r="{ref}"><f>{x(v[0][1:])}</f><v>{v[1]}</v></c>')
            elif isinstance(v, (int, float)):
                cs.append(f'<c r="{ref}"><v>{v}</v></c>')
            elif (r, c) in inline:
                cs.append(f'<c r="{ref}" t="inlineStr"><is><t>{x(v)}</t></is></c>')
            else:
                if v not in strs:
                    strs.append(v)
                cs.append(f'<c r="{ref}" t="s"><v>{strs.index(v)}</v></c>')
        out.append(f'<row r="{r}">' + "".join(cs) + "</row>")
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    si = []
    for i, s in enumerate(strs):                             # every third text as «rich text» (two runs), as Excel writes it after formatting
        si.append(f"<si><r><t>{x(s[:2])}</t></r><r><rPr><b/></rPr><t>{x(s[2:])}</t></r></si>" if i % 3 == 2 and len(s) > 3 else f"<si><t>{x(s)}</t></si>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0"?><workbook {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                                      '<sheets><sheet name="Packliste" sheetId="1" r:id="rId7"/><sheet name="Alt" sheetId="2" r:id="rId8"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId8" Type="x" Target="worksheets/sheet1.xml"/><Relationship Id="rId7" Type="x" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<?xml version="1.0"?>{sst_head}<sst {ns}>' + "".join(si) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0"?><worksheet {ns}><sheetData><row r="1"><c r="A1"><v>999</v></c></row></sheetData></worksheet>')
        z.writestr("xl/worksheets/sheet2.xml", f'<?xml version="1.0"?><worksheet {ns}><sheetData>' + "".join(out) + "</sheetData></worksheet>")
        for nm, data in (extra or {}).items():
            z.writestr(nm, data)
    return buf.getvalue()


XLSX_ZEILEN = [["Kategorie", "Gegenstand", "Gewicht in g", "Menge", "Notiz"],
               ["Schlafen", "Zelt", 1800, 1, "mit Heringen"],
               ["Schlafen", "Schlafsack", 950.0, 1, None],
               ["Küche", "Müesli-Schale", ("=C2/20", 90), 2, "blau"],
               ["Kleider", "Socken (Merino)", 80, 3, None],
               [None, "Ohne Kategorie", None, None, "kein Gewicht"],
               ["Essen", "=HYPERLINK(\"http://evil.example\")", 100, 1, None]]


def jpg_bytes(w=1600, h=1200, col=(40, 150, 230), text="Foto"):
    import numpy as np
    import cv2
    im = np.zeros((h, w, 3), np.uint8); im[:] = col
    cv2.circle(im, (w // 2, h // 2), min(w, h) // 3, (255, 255, 255), -1)
    cv2.putText(im, text, (w // 2 - 140, h // 2 + 20), cv2.FONT_HERSHEY_SIMPLEX, max(1.0, w / 500), (30, 30, 30), 6)
    return cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_lesen(ns):
    print("A) Lesen: Gewichte, Zeilen, CSV, eingefügter Text, Excel", flush=True)
    W, L = ns["pl_weight"], ns["pl_parse_line"]
    for txt, want in (("350 g", 350), ("350g", 350), ("1.2 kg", 1200), ("0,5kg", 500), ("0.5 KG", 500), ("1'200 g", 1200), ("1’200g", 1200), ("1.200 g", 1200),
                      ("2 kg", 2000), ("85", 85), ("ca. 90 Gramm", 90), ("~120 gr", 120), ("12 oz", 340), ("1 lb", 454), ("1,25 kg", 1250), ("0.004 kg", 4),
                      ("", None), ("schwer", None), ("0 g", None), ("999 kg", None), ("-5 g", 5)):
        ok(W(txt) == want, f"Gewicht «{txt}» -> {W(txt)} statt {want}")
    ok(W("1,5", "kg") == 1500 and W("12", "kg") == 12000 and W("1,5 g", "kg") == 2, "nackte Zahl mit Einheit der Spalte")
    ok(ns["pl_fmt_g"](1250, "de") == "1,25 kg" and ns["pl_fmt_g"](1200, "en") == "1.2 kg" and ns["pl_fmt_g"](999, "de") == "999 g" and ns["pl_fmt_g"](None) == "–", "Anzeige des Gewichts")
    zeilen = {
        "- Zelt (1.8 kg)": ("Zelt", 1800, 1), "Schlafsack – 950 g": ("Schlafsack", 950, 1), "Isomatte\t480": ("Isomatte", 480, 1), "• Kissen 80g": ("Kissen", 80, 1),
        "1. Gaskocher 90 g": ("Gaskocher", 90, 1), "3) Topf 0,25 kg": ("Topf", 250, 1), "2x Socken": ("Socken", None, 2), "2 x Socken 80 g": ("Socken", 80, 2),
        "2× Karabiner": ("Karabiner", None, 2), "Handschuhe x2 60 g": ("Handschuhe", 60, 2), "Heringe (8 Stk.) 12 g": ("Heringe", 12, 8), "4 Riegel à 45 g": ("Riegel", 45, 4),
        "2 Paar Socken à 80 g": ("Paar Socken", 80, 2), "3 XL Shirts 150 g": ("XL Shirts", 150, 3), "Garmin 64x": ("Garmin 64x", None, 1), "Mütze, rot 70 g": ("Mütze, rot", 70, 1),
        "Stirnlampe: 85 g": ("Stirnlampe", 85, 1), "Regenjacke ~350g": ("Regenjacke", 350, 1), "Trinkflasche 1'150 g": ("Trinkflasche", 1150, 1),
        "Karte 1:25000 Blatt 1105": ("Karte 1:25000 Blatt 1105", None, 1), "5 m Reepschnur 40 g": ("5 m Reepschnur", 40, 1), "Powerbank 10000 mAh 230 g": ("Powerbank 10000 mAh", 230, 1),
        "* Erste-Hilfe-Set – 0.2kg": ("Erste-Hilfe-Set", 200, 1), "Zelt - 1800": ("Zelt", 1800, 1), "> Kocher 90g": ("Kocher", 90, 1), "Fleece (Patagonia R1) 380 g": ("Fleece (Patagonia R1)", 380, 1),
    }
    for z, (name, g, n) in zeilen.items():
        p = L(z)
        ok(p is not None and p[0] == "item" and (p[1]["name"], p[1]["g"], p[1]["n"]) == (name, g, n), f"Zeile «{z}» -> {p}")
    ok(L("- [x] Löffel 20 g")[1]["packed"] is True and L("- [ ] Feuerzeug")[1]["packed"] is False and L("☐ Schwamm")[1]["name"] == "Schwamm"
       and L("✅ Pass")[1]["packed"] is True and L("[X] Karte")[1]["packed"] is True, "Kästchen")
    ok(L("Gaskartusche 230 g (kaufen)")[1]["buy"] and L("Sonnencreme – fehlt noch")[1]["buy"] and not L("Kaufen Zeitung")[1]["buy"], "«kaufen» / «fehlt noch»")
    p = L("Wasser 1,5 l")[1]
    ok(p["name"] == "Wasser" and p["g"] is None and p["note"] == "1,5 l", f"Flüssigkeit nur als Notiz: {p}")
    p = L("Benzin 0.5 l 400 g")[1]
    ok(p["name"] == "Benzin" and p["g"] == 400 and p["note"] == "0.5 l", f"Flüssigkeit mit Gewicht: {p}")
    for z, kind in (("Küche:", "cat"), ("## Kleider", "cat"), ("== Essen ==", "cat"), ("**Hygiene**", "cat"), ("ERSTE HILFE", "caps")):
        ok(L(z) is not None and L(z)[0] == kind, f"Überschrift «{z}» -> {L(z)}")
    for z in ("", "   ", "---", "====", "•", "- ", "???", "\t"):
        ok(L(z) is None, f"leere Zeile «{z}» -> {L(z)}")
    r = ns["pl_parse_text"](NOTIZ)
    it = {i["name"]: i for i in r["items"]}
    ok(len(r["items"]) == 19 and r["title"] == "Wochenende Jura", f"Notiz: {len(r['items'])} statt 19 Gegenstände, Titel {r.get('title')!r}: {sorted(it)}")
    ok(it["Zelt"]["cat"] == "sleep" and it["Kissen"]["cat"] == "sleep" and it["Gaskocher"]["cat"] == "kitchen" and it["Löffel"]["packed"]
       and it["Gaskartusche"]["buy"] and it["Gaskartusche"]["n"] == 2 and it["Gaskartusche"]["kind"] == "cons" and it["Paar Socken"]["cat"] == "clothes"
       and it["Wasser"]["cat"] == "water" and it["Wasser"]["kind"] == "cons" and it["Trinkflasche"]["kind"] == "base" and it["Stirnlampe"]["cat"] == "water" and "Wochenende Jura" not in it, f"Notiz: Kategorien, Häkchen, kaufen: {it}")
    r2 = ns["pl_parse_text"]("ZELT\nSCHLAFSACK 950 G\nKOCHER\nISOMATTE")
    ok(len(r2["items"]) == 4 and r2["items"][0]["name"] == "Zelt" and r2["items"][1]["g"] == 950, f"alles gross geschrieben = Gegenstände, keine Überschriften: {r2}")
    r3 = ns["pl_parse_text"]("Jacke\r\nHose\r\n\r\nSchuhe\r")
    ok([i["name"] for i in r3["items"]] == ["Jacke", "Hose", "Schuhe"], "Zeilenenden von Windows / altem Mac")
    # bare lines as headings - only when the structure shows it (both directions)
    T = ns["pl_parse_text"]
    cats = lambda txt: [(i["name"], i["cat"]) for i in T(txt)["items"]]
    r = T("Schlafen\n- Zelt 1.8 kg\n- Isomatte\nKochzeug\n- Kocher 90 g\n- Topf\n- Löffel\nFotoausrüstung\n  Kamera\n  Stativ 900 g")
    ok([(i["name"], i["cat"]) for i in r["items"]] == [("Zelt", "sleep"), ("Isomatte", "sleep"), ("Kocher", "kitchen"), ("Topf", "kitchen"), ("Löffel", "kitchen"),
                                                      ("Kamera", "electronics"), ("Stativ", "electronics")] and [h[:2] for h in r["heads"]] == [[0, "Schlafen"], [2, "Kochzeug"], [5, "Fotoausrüstung"]],
       f"blosse Zeile über Aufzählung / Einrückung = Kategorie: {r}")
    ok(cats("Tour Säntis\n\nKleider\n[ ] Jacke\n[x] Mütze\n\nVelo-Werkzeug\n1. Pumpe 120 g\n2. Flickzeug") == [("Jacke", "clothes"), ("Mütze", "clothes"), ("Pumpe", "tools"), ("Flickzeug", "tools")]
       and T("Tour Säntis\n\nKleider\n[ ] Jacke\n[x] Mütze\n\nVelo-Werkzeug\n1. Pumpe 120 g\n2. Flickzeug")["title"] == "Tour Säntis", "Kästchen und Nummern unter einer blossen Zeile; Titel bleibt Titel")
    ok(cats("Schlafen\nZelt 1.8 kg\nSchlafsack 950 g\n\nKüche\nKocher 90 g\nTopf 250 g\nLöffel") == [("Zelt", "sleep"), ("Schlafsack", "sleep"), ("Kocher", "kitchen"), ("Topf", "kitchen"), ("Löffel", "kitchen")],
       "ohne Aufzählungszeichen: Blöcke mit Leerzeile, erste Zeile ohne Gewicht, darunter Gewichte = Kategorien")
    ok(cats("Hygiene\nZahnbürste\nSeife\n\nDokumente\nPass\nHalbtax") == [("Zahnbürste", "hygiene"), ("Seife", "hygiene"), ("Pass", "documents"), ("Halbtax", "documents")],
       "ohne Gewichte: Blöcke, deren erste Zeile eine bekannte Kategorie ist")
    for txt, was in (("Zelt\nSchlafsack\nIsomatte\nKocher\nTopf", "einfache Liste"), ("Zelt\nSchlafsack\n\nKocher\nTopf\n\nJacke\nHose", "einfache Liste mit Leerzeilen"),
                     ("Zelt 1.8 kg\nSchlafsack 950 g\n\nKocher 90 g\nTopf", "Gewichte auch in der ersten Zeile"), ("Zelt\nSchlafsack\n- Kocher\nTopf\nLöffel", "ein einzelner Strich in einer einfachen Liste"),
                     ("Zelt\n\nSchlafsack\n\nKocher", "Leerzeile nach jeder Zeile (Notizen-App)"), ("Schlafsack\nZelt 1.8 kg\nKocher 90 g\nTopf 250 g", "ein Block: die erste Zeile ohne Gewicht bleibt ein Gegenstand")):
        r = T(txt)
        ok(not r["heads"] and len(r["items"]) == len([x for x in txt.split("\n") if x.strip()]), f"bleibt eine Liste von Gegenständen ({was}): {[i['name'] for i in r['items']]} {r['heads']}")
    ok([h[1:] for h in T(NOTIZ)["heads"]] == [["Schlafen", "sleep"], ["Küche", "kitchen"], ["Kleider", "clothes"], ["Wasser", "water"]], f"ausdrückliche Überschriften kommen für die Vorschau mit: {T(NOTIZ)['heads']}")
    P = ns["pl_import_preview"]
    # CSV
    p = P(data=CSV_KOMMA.encode("utf-8"), name="gear.csv")
    ok(p["kind"] == "table" and p["header"] and p["map"]["name"] == 0 and p["map"]["g"] == 1 and p["map"]["n"] == 2 and p["map"]["cat"] == 3 and p["map"]["note"] == 4, f"CSV Komma: Spalten {p.get('map')}")
    ok([(i["name"], i["g"], i["n"], i["cat"], i["note"]) for i in p["items"]] == [("Tent, 2 person", 1800, 1, "sleep", "with footprint"), ("Spork", 17, 2, "kitchen", ""),
                                                                                 ("Power bank", 230, 1, "electronics", "10,000 mAh")], f"CSV Komma: {p['items']}")
    p = P(data=b"\xef\xbb\xbf" + CSV_KOMMA.encode("utf-8"), name="gear.csv")
    ok(p["map"]["name"] == 0 and p["items"][0]["name"] == "Tent, 2 person", "CSV mit BOM: erste Überschrift sauber")
    p = P(data=CSV_1252.encode("cp1252"), name="Liste.CSV")
    ok(p["kind"] == "table" and p["unit"] == "kg" and [(i["name"], i["g"], i["n"], i["cat"]) for i in p["items"]] ==
       [("Käse", 250, 2, "food"), ("Müesli", 500, 1, "food"), ("Zelt «Hubba»", 1720, 1, "sleep"), ("Wärmflasche", 300, 1, "other")] and p["items"][0]["note"] == "vom Märit",
       f"CSV Windows-1252, Strichpunkt, Dezimalkomma, kg: {p.get('unit')} {p['items']}")
    p = P(data=TSV_OHNE.encode(), name="liste.txt")
    ok(p["kind"] == "table" and not p["header"] and p["map"]["name"] == 0 and p["map"]["g"] == 1 and
       [(i["name"], i["g"], i["cat"]) for i in p["items"]] == [("Zelt", 1800, "sleep"), ("Schlafsack", 950, "sleep"), ("Kocher", 90, "kitchen"), ("Riegel", 45, "kitchen")],
       f"Tabulator ohne Kopfzeile, Zeile «Küche:» als Kategorie: {p}")
    p = P(text=TABELLE_NOTIZEN)
    ok(p["kind"] == "table" and p["header"] and [(i["name"], i["g"], i["n"]) for i in p["items"]] == [("Stirnlampe", 85, 1), ("Batterien AAA", 12, 3), ("Karte", 90, 1)],
       f"eingefügte Tabelle (Tabulator): {p}")
    p = P(text="Zelt; 1,8 kg\nSchlafsack; 950 g\nKocher; 90 g")
    ok(p["kind"] == "table" and [(i["name"], i["g"]) for i in p["items"]] == [("Zelt", 1800), ("Schlafsack", 950), ("Kocher", 90)], f"eingefügt mit Strichpunkt: {p}")
    p = P(text="Zelt, gross 1,8 kg\nMütze, rot 70 g\nSocken")
    ok(p["kind"] == "lines" and [(i["name"], i["g"]) for i in p["items"]] == [("Zelt, gross", 1800), ("Mütze, rot", 70), ("Socken", None)], f"Kommas in einer Notiz sind keine Tabelle: {p}")
    p = P(data="Socken;3\nShirt;2\nHose;1\n".encode(), name="a.csv")
    ok(p["map"]["n"] == 1 and p["map"]["g"] == -1 and p["items"][0]["n"] == 3, f"kleine ganze Zahlen = Anzahl: {p['map']}")
    p = P(data="Riegel;45\nFeuerzeug;15\nZelt;1800\n".encode(), name="a.csv")
    ok(p["map"]["g"] == 1 and p["items"][0]["g"] == 45, f"grössere Zahlen = Gewicht: {p['map']}")
    # the user's columns win
    p2 = P(rows=p["rows"], guess={"header": False, "unit": "kg", "map": {"name": 0, "g": 1, "n": -1, "cat": -1, "note": -1}})
    ok(p2["items"][0]["g"] == 45000 and p2["unit"] == "kg", "Zuordnung des Benutzers gilt (Einheit kg)")
    p2 = P(rows=[["a", "b"], ["Zelt", "Tent"]], guess={"header": True, "unit": "g", "map": {"name": 1}})
    ok([i["name"] for i in p2["items"]] == ["Tent"], "Zuordnung: andere Namensspalte, erste Zeile Überschrift")
    # xlsx
    xb = xlsx_bytes(XLSX_ZEILEN, inline={(3, 1)})
    p = P(data=xb, name="Packliste Sommer.xlsx")
    ok(p["kind"] == "table" and p["title"] == "Packliste Sommer" and p["map"] == dict(p["map"], name=1, g=2, n=3, cat=0, note=4) and p["unit"] == "g", f"xlsx: Spalten {p.get('map')}")
    ok([(i["name"], i["g"], i["n"], i["cat"]) for i in p["items"]] == [("Zelt", 1800, 1, "sleep"), ("Schlafsack", 950, 1, "sleep"), ("Müesli-Schale", 90, 2, "kitchen"),
                                                                      ("Socken (Merino)", 80, 3, "clothes"), ("Ohne Kategorie", None, 1, "other"),
                                                                      ('=HYPERLINK("http://evil.example")', 100, 1, "food")], f"xlsx: {p['items']}")
    ok(p["items"][0]["note"] == "mit Heringen" and "999" not in json.dumps(p["rows"]), "xlsx: Notiz gelesen, das erste Blatt laut Arbeitsmappe (nicht sheet1.xml)")
    ok(p["items"][2]["g"] == 90, "xlsx: Formel wird nie gerechnet, nur der gespeicherte Wert")
    E = ns["PLError"]

    def abgewiesen(data, name, was):
        t0 = time.time()
        try:
            P(data=data, name=name)
            ok(False, f"{was}: wurde gelesen")
        except E as e:
            ok(time.time() - t0 < 5, f"{was}: abgewiesen, aber erst nach {time.time() - t0:.1f} s ({e})")
    bombe = io.BytesIO()
    with zipfile.ZipFile(bombe, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("xl/workbook.xml", "<workbook/>")
        z.writestr("xl/sharedStrings.xml", b"<sst>" + b"<si><t>" + b"A" * 1000 + b"</t></si>" * 1 + b" " * (300 * 1024 * 1024) + b"</sst>")
        z.writestr("xl/worksheets/sheet1.xml", "<worksheet><sheetData/></worksheet>")
    ok(len(bombe.getvalue()) < 1024 * 1024, f"die Bombe ist klein ({len(bombe.getvalue())} B gepackt, 300 MB entpackt)")
    abgewiesen(bombe.getvalue(), "bombe.xlsx", "ZIP-Bombe (300 MB entpackt)")
    abgewiesen(xlsx_bytes([["a"]], extra={f"xl/x{i}.xml": b"<a/>" for i in range(400)}), "viele.xlsx", "xlsx mit 400 Einträgen")
    lach = '<!DOCTYPE lolz [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;"><!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">]>'
    abgewiesen(xlsx_bytes([["x"]], sst_head=lach), "lach.xlsx", "xlsx mit DOCTYPE / ENTITY")
    abgewiesen(xlsx_bytes([["x"]], sst_head='<!DOCTYPE s [<!ENTITY x SYSTEM "file:///etc/passwd">]>'), "extern.xlsx", "xlsx mit externer Entität")
    # a lying header: declared small, really huge (the read itself is capped)
    lz = io.BytesIO()
    with zipfile.ZipFile(lz, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/worksheets/sheet1.xml", b"<worksheet><sheetData>" + b" " * (60 * 1024 * 1024) + b"</sheetData></worksheet>")
    raw = bytearray(lz.getvalue())
    for m in re.finditer(rb"PK\x01\x02|PK\x03\x04", bytes(raw)):
        off = m.start() + (24 if raw[m.start() + 2] == 1 else 22)
        raw[off:off + 4] = (1000).to_bytes(4, "little")          # uncompressed size: «1000 bytes»
    abgewiesen(bytes(raw), "luege.xlsx", "xlsx mit gelogener Grösse")
    abgewiesen(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 600, "alt.xls", "altes .xls")
    abgewiesen(b"%PDF-1.4 ...", "liste.pdf", "PDF")
    abgewiesen(b"PK\x03\x04kaputt", "kaputt.xlsx", "kaputte xlsx")
    abgewiesen(b"x" * (ns["PL_IMPORT_MAX"] + 1), "gross.txt", "zu grosse Datei")
    abgewiesen(b'{"foo": 1}', "x.json", "fremdes JSON")
    abgewiesen(b"Zelt 1.8 kg\n\x00\x01\x02" + os.urandom(200), "a.txt", "Binärdatei mit Text-Endung")
    it = ns["pl_dups"]([{"name": "Zelt"}, {"name": "zelt"}, {"name": "Kocher"}], {"items": [{"name": "KOCHER"}]})
    ok([i["dup"] for i in it] == ["", "import", "list"], f"Doppelte werden markiert, nicht entfernt: {it}")
    ok(ns["pl_selftest"]() and any(fn is ns["pl_selftest"] for _n, fn in ns["SELFTEST_EXTRA"]), "Selbsttest pl_selftest läuft und ist eingetragen")


def teil_a(datei):
    ns = laden(datei)
    teil_lesen(ns)
    CFG, TZ, PL = ns["CFG"], ns["TZ"], ns["PL"]
    GB = ns["TZ_GB"]
    root = tempfile.mkdtemp(prefix="mw_pl_root_")
    TZ["root_test"] = root
    TZ.update(root=None, files=None)
    PL.update(root=None, lists=None)
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_guest=True, tausch_push=False, push_level="all", quiet_on=False)
    free = {"n": 100 * GB}
    ns["tausch_disk_free"] = lambda p: free["n"]
    TZ["push_manual"] = True
    ADMIN_PW = "Admin-Pass-123"
    assert ns["web_pw_set"](ADMIN_PW)[0]
    users = {"Anna": "family", "Carl": "family", "Bob": "friend", "Vera": "view", "Kim": "kid", "Cus": "custom", "Cuz": "custom", "Cuv": "custom"}
    for n, r in users.items():
        okk, err = ns["users_action"]({"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        assert okk, err
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live", "files_up"]})
    ns["users_action"]({"action": "update", "name": "Cuz", "perms": ["files_admin"]})
    ns["users_action"]({"action": "update", "name": "Cuv", "perms": ["files_view"]})
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)
    H = {n: basic(n, n.lower() + "-pass-1") for n in users}
    H["admin"] = basic("admin", ADMIN_PW)

    def api(who, d, client=None):
        r = (client or c).post("/api/tausch/pack", json=dict(d, lang="de"), headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def lst(who, lid, since=0):
        r = c.get(f"/api/tausch/pack?id={lid}&since={since}&lang=de", headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def foto(who, lid, iid, data, name="IMG_0001.jpg", client=None):
        cl = client or c
        r = cl.post("/api/tausch", json={"action": "start", "name": name, "size": len(data), "lastmod": 5, "pack": {"list": lid, "item": iid}, "lang": "de"}, headers=H[who])
        j = r.get_json(silent=True) or {}
        if r.status_code != 200:
            return r.status_code, j
        off = j["have"]
        while off < len(data):
            k = cl.post(f"/api/tausch/chunk?id={j['id']}&off={off}", data=data[off:off + 300000], headers=dict(H[who], **{"Content-Type": "application/octet-stream"}))
            if k.status_code != 200:
                return k.status_code, k.get_json()
            off = k.get_json()["have"]
        r = cl.post("/api/tausch", json={"action": "finish", "id": j["id"], "lang": "de"}, headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    print("A) Listen: anlegen, ändern, Summen, Ziel, Einkauf", flush=True)
    code, j = api("Anna", {"action": "new", "name": "Wochenende Jura", "goal": "5 kg"})
    ok(code == 200 and j.get("id"), f"Liste anlegen: {code} {j}")
    lid = j["id"]
    ok(os.path.isfile(os.path.join(root, "pack", lid + ".json")), "die Liste ist eine einfache Datei im Ordner des Datentausches (pack/<Nummer>.json)")
    ids = {}
    for txt in ("Zelt (1.8 kg)", "Schlafsack – 950 g", "2x Gaskartusche 230 g", "Wasser 1,5 l", "Riegel 4x 45 g", "Wanderschuhe 1100 g", "Karte"):
        code, j = api("Anna", {"action": "add", "list": lid, "text": txt})
        ok(code == 200 and j.get("item"), f"schnell eintragen «{txt}»: {code} {j}")
        ids[j["item"]["name"]] = j["item"]["id"]
    code, j = lst("Anna", lid)
    it = {x["name"]: x for x in j["items"]}
    ok(it["Zelt"]["g"] == 1800 and it["Zelt"]["cat"] == "sleep" and it["Gaskartusche"]["n"] == 2 and it["Gaskartusche"]["kind"] == "cons" and it["Riegel"]["n"] == 4
       and it["Riegel"]["kind"] == "cons" and it["Wasser"]["g"] is None and it["Wasser"]["note"] == "1,5 l" and it["Karte"]["cat"] == "navigation", f"gelesen wie beim Import: {it}")
    code, j = api("Anna", {"action": "item", "list": lid, "id": ids["Wasser"], "set": {"w": "1,5 kg", "note": ""}})
    ok(code == 200 and j["item"]["g"] == 1500, "Gewicht «1,5 kg» -> 1500 g")
    code, j = api("Anna", {"action": "item", "list": lid, "id": ids["Wasser"], "set": {"w": "ganz schwer"}})
    ok(code == 400 and "350 g" in j.get("error", ""), f"unverständliches Gewicht: klare Meldung ({code} {j.get('error')})")
    code, j = api("Anna", {"action": "item", "list": lid, "id": ids["Wanderschuhe"], "set": {"kind": "worn", "cat": "clothes"}})
    code, j = api("Anna", {"action": "item", "list": lid, "id": ids["Karte"], "set": {"cat": "Fotoausrüstung", "w": "90"}})
    ok(j["item"]["cat"] == "Fotoausrüstung" and j["item"]["g"] == 90, f"eigene Kategorie bleibt, nackte Zahl = Gramm: {j.get('item')}")
    code, j = api("Anna", {"action": "item", "list": lid, "id": ids["Karte"], "set": {"cat": "Küche"}})
    ok(j["item"]["cat"] == "kitchen", "der Name einer festen Kategorie wird zu ihrem Schlüssel")
    api("Anna", {"action": "item", "list": lid, "id": ids["Karte"], "set": {"cat": "navigation"}})
    code, j = lst("Anna", lid)
    T = ns["pl_totals"](ns["PL"]["lists"][lid]["items"])
    ok(T["base"] == 1800 + 950 + 90 and T["cons"] == 460 + 1500 + 180 and T["worn"] == 1100 and T["pack"] == 4980 and T["total"] == 6080 and T["unknown"] == 0, f"Summen: {T}")
    ok(T["cats"]["sleep"]["g"] == 2750 and T["cats"]["sleep"]["n"] == 2 and j["head"]["pack"] == 4980 and j["head"]["goal_g"] == 5000, f"pro Kategorie, Ziel 5 kg: {T['cats']} {j['head']}")
    code, j = api("Anna", {"action": "meta", "id": lid, "goal": "4,5kg", "note": "Abfahrt Samstag"})
    ok(j["head"]["goal_g"] == 4500 and j["head"]["pack"] - j["head"]["goal_g"] == 480, "Ziel 4,5 kg: 480 g darüber")
    hp = c.get(f"/tausch/pack/druck/{lid}?lang=de", headers=H["Anna"]).get_data(as_text=True)
    ok("Ziel 4,5 kg: 480 g darüber" in hp and "Rucksack 4,98 kg" in hp and "Basisgewicht 2,84 kg" in hp and "Verbrauch 2,14 kg" in hp and "Am Körper 1,1 kg" in hp, "Druckansicht: Ziel und Summen")
    api("Anna", {"action": "meta", "id": lid, "goal": "6 kg"})
    hp = c.get(f"/tausch/pack/druck/{lid}?lang=de", headers=H["Anna"]).get_data(as_text=True)
    ok("Ziel 6 kg: 1,02 kg darunter" in hp, "Ziel 6 kg: 1,02 kg darunter")
    api("Anna", {"action": "meta", "id": lid, "goal": ""})
    ok(lst("Anna", lid)[1]["head"]["goal_g"] == 0, "Ziel entfernen")
    api("Anna", {"action": "meta", "id": lid, "goal": "5 kg"})
    # shopping
    api("Anna", {"action": "item", "list": lid, "id": ids["Gaskartusche"], "set": {"buy": True}})
    code, j = api("Anna", {"action": "add", "list": lid, "text": "Sonnencreme", "buy": True})
    sid = j["item"]["id"]
    ok(j["item"]["buy"] and lst("Anna", lid)[1]["head"]["buy"] == 2, "Einkauf: zwei Sachen fehlen noch")
    api("Anna", {"action": "item", "list": lid, "id": sid, "set": {"buy": False}})
    ok(lst("Anna", lid)[1]["head"]["buy"] == 1, "Einkauf: gekauft -> noch eine")
    code, j = api("Anna", {"action": "add", "list": lid, "text": "zelt"})
    ok(code == 200 and j.get("dup") is True, "doppelter Name wird gemeldet, aber eingetragen")
    api("Anna", {"action": "rm", "list": lid, "id": j["item"]["id"]})
    for d, was in (({"action": "new", "name": "  "}, "Liste ohne Name"), ({"action": "add", "list": lid, "text": "   "}, "Gegenstand ohne Name"),
                   ({"action": "item", "list": lid, "id": ids["Zelt"], "set": {"name": ""}}, "leerer Name"), ({"action": "quatsch", "list": lid}, "unbekannte Aktion")):
        ok(api("Anna", d)[0] == 400, f"abgewiesen: {was}")
    ok(api("Anna", {"action": "item", "list": lid, "id": "00000000", "set": {"packed": True}})[0] == 404 and api("Anna", {"action": "add", "list": "0" * 16, "text": "x"})[0] == 404, "unbekannter Gegenstand / unbekannte Liste")
    # templates
    code, j = c.get("/api/tausch/pack?lang=de", headers=H["Anna"]).status_code, c.get("/api/tausch/pack?lang=de", headers=H["Anna"]).get_json()
    ok([t["name"] for t in j["templates"]] == ["Tagestour", "Zeltnacht", "Winter"] and len(j["lists"]) == 1, f"Vorlagen: {j.get('templates')}")
    for key in ("day", "camp", "winter"):
        code, t = api("Carl", {"action": "new", "name": "Vorlage " + key, "template": key})
        Lx = PL["lists"][t["id"]]
        TT = ns["pl_totals"](Lx["items"])
        ok(code == 200 and len(Lx["items"]) >= 15 and TT["cons"] > 0 and TT["worn"] > 0 and TT["unknown"] == 0 and len(TT["cats"]) >= 6, f"Vorlage {key}: {len(Lx['items'])} Sachen")
        if key != "camp":
            api("Carl", {"action": "del", "id": t["id"]})
        else:
            camp = t["id"]
    en = c.post("/api/tausch/pack", json={"action": "new", "name": "Day", "template": "day", "lang": "en"}, headers=H["Carl"]).get_json()
    ok(any(x["name"] == "Rain jacket" for x in PL["lists"][en["id"]]["items"]), "Vorlage in der Sprache der Seite (Englisch)")
    api("Carl", {"action": "del", "id": en["id"]})

    print("A) Foto über den Stück-Upload des Datentausches", flush=True)
    import numpy as np
    import cv2
    gross = jpg_bytes(4000, 3000)
    code, j = foto("Anna", lid, ids["Zelt"], gross)
    ok(code == 200 and j.get("item", {}).get("photo"), f"Foto hochladen (4000 × 3000, {len(gross) // 1024} KB, in Stücken): {code} {j}")
    r1, r2 = c.get(f"/tausch/pack/b/{lid}/{ids['Zelt']}.jpg", headers=H["Anna"]), c.get(f"/tausch/pack/b/{lid}/{ids['Zelt']}.jpg?p=1", headers=H["Anna"])
    d1 = cv2.imdecode(np.frombuffer(r1.get_data(), np.uint8), 1) if r1.status_code == 200 else None
    d2 = cv2.imdecode(np.frombuffer(r2.get_data(), np.uint8), 1) if r2.status_code == 200 else None
    ok(d1 is not None and max(d1.shape[:2]) == 320 and d2 is not None and max(d2.shape[:2]) == 1280, "gespeichert nur verkleinert: 320 px und 1280 px")
    ok(r1.headers.get("X-Content-Type-Options") == "nosniff" and "sandbox" in r1.headers.get("Content-Security-Policy", ""), "Foto mit nosniff und sandbox")
    ok(len(r2.get_data()) < len(gross) / 4 and not os.listdir(os.path.join(root, "up")), "das Original bleibt nicht liegen")
    fl = c.get("/api/tausch?area=mine", headers=H["Anna"]).get_json()
    ok(not fl["files"] and not fl["ups"] and not TZ["files"], "das Foto ist keine Datei im Datentausch geworden")
    ok(sorted(os.listdir(os.path.join(root, "pack", "b", lid))) == [ids["Zelt"] + ".jpg", ids["Zelt"] + "_p.jpg"], "Fotos liegen unter pack/b/<Liste>/<Gegenstand>.jpg")
    png = cv2.imencode(".png", np.full((600, 900, 3), (20, 200, 120), np.uint8))[1].tobytes()
    ok(foto("Carl", lid, ids["Schlafsack"], png, "Bildschirmfoto.png")[0] == 200, "PNG von einem anderen Benutzer (Familie)")
    heic = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + os.urandom(3000)
    code, j = foto("Anna", lid, ids["Karte"], heic, "IMG_4711.HEIC")
    ok(code == 400 and "HEIC" in j.get("error", "") and "Fotomediathek" in j.get("error", ""), f"HEIC: klare Meldung statt stiller Fehler ({code} {j.get('error')})")
    ok(not os.listdir(os.path.join(root, "up")) and lst("Anna", lid)[1]["items"] and not [x for x in lst("Anna", lid)[1]["items"] if x["id"] == ids["Karte"]][0]["photo"], "HEIC: nichts bleibt liegen")
    bombe = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + (30000).to_bytes(4, "big") + (30000).to_bytes(4, "big") + b"\x08\x02\x00\x00\x00" + b"\x00" * 4000
    ok(foto("Anna", lid, ids["Karte"], bombe, "bombe.png")[0] == 400, "Pixelbombe (30 000 × 30 000) wird nicht dekodiert")
    ok(foto("Anna", lid, ids["Karte"], b"MZ\x90\x00" + b"\0" * 500, "foto.jpg")[0] == 400, "kein Bild im Bild-Namen: abgewiesen")
    code, j = foto("Anna", lid, ids["Karte"], b"x" * 10, "liste.pdf")
    ok(code == 400 and "Foto" in j.get("error", ""), f"keine Bilddatei: abgewiesen ({code} {j.get('error')})")
    r = c.post("/api/tausch", json={"action": "start", "name": "riesig.jpg", "size": ns["PL_PHOTO_MAX"] + 1, "pack": {"list": lid, "item": ids["Karte"]}, "lang": "de"}, headers=H["Anna"])
    ok(r.status_code == 400 and "gross" in r.get_json().get("error", ""), "Foto über 25 MB: abgewiesen")
    ok(foto("Bob", lid, ids["Karte"], png, "x.png")[0] in (400, 403), "Freund (nur ansehen): kein Foto")
    ok(foto("Anna", lid, "ffffffff", png, "x.png")[0] == 400 and foto("Anna", "f" * 16, ids["Karte"], png, "x.png")[0] == 400, "Foto für einen unbekannten Gegenstand / eine unbekannte Liste")
    v1 = [x for x in lst("Anna", lid)[1]["items"] if x["id"] == ids["Zelt"]][0]["photo"]
    foto("Anna", lid, ids["Zelt"], jpg_bytes(800, 600, (10, 10, 200)))
    v2 = [x for x in lst("Anna", lid)[1]["items"] if x["id"] == ids["Zelt"]][0]["photo"]
    ok(v2 > v1, "neues Foto: neue Nummer (der Browser lädt das Bild neu)")
    for bad in (f"/tausch/pack/b/{lid}/..%2f..%2f{lid}.jpg", f"/tausch/pack/b/{lid}/{ids['Zelt']}x.jpg", f"/tausch/pack/b/../{ids['Zelt']}.jpg", f"/tausch/pack/b/{lid.upper()}/{ids['Zelt']}.jpg",
                f"/tausch/pack/b/{lid}/{ids['Karte']}.jpg", "/tausch/pack/x/..%2f..%2fordner.json", f"/tausch/pack/x/{lid}.exe"):
        ok(c.get(bad, headers=H["Anna"]).status_code in (404, 308, 400), f"Pfad-Trick / kein Foto: {bad}")

    print("A) Zwei Handys haken gleichzeitig ab", flush=True)
    Lc = PL["lists"][camp]
    cid = [x["id"] for x in Lc["items"]]
    rev0 = Lc["rev"]
    half = len(cid) // 2
    errs = []

    def haken(who, some):
        cl = app.test_client(use_cookies=False)
        for iid in some:
            code_, j_ = api(who, {"action": "item", "list": camp, "id": iid, "set": {"packed": True}, "base": rev0}, cl)
            if code_ != 200:
                errs.append((who, iid, code_, j_))
    t1 = threading.Thread(target=haken, args=("Anna", cid[:half]))
    t2 = threading.Thread(target=haken, args=("Carl", cid[half:]))
    t1.start(); t2.start(); t1.join(); t2.join()
    code, j = lst("Bob", camp)
    ok(not errs and all(x["packed"] for x in j["items"]) and j["rev"] == rev0 + len(cid), f"beide haken ab: alle {len(cid)} Häkchen sind da, nichts überschrieben ({errs[:2]})")
    ok({x["by"] for x in j["items"][:half]} == {"Anna"} and {x["by"] for x in j["items"][half:]} == {"Carl"}, "wer zuletzt geändert hat, steht beim Gegenstand")
    disk = json.load(open(os.path.join(root, "pack", camp + ".json"), encoding="utf-8"))
    ok(all(x["packed"] for x in disk["items"]) and disk["rev"] == j["rev"] and not [f for f in os.listdir(os.path.join(root, "pack")) if f.endswith(".tmp")], "die Datei ist ganz und aktuell, keine Nebendatei bleibt liegen")
    # the same item, different fields: both stay; the same field: the last one wins and the other phone learns it
    a_rev = j["rev"]
    x0 = cid[0]
    c1, j1 = api("Anna", {"action": "item", "list": camp, "id": x0, "set": {"packed": False}, "base": a_rev})
    c2, j2 = api("Carl", {"action": "item", "list": camp, "id": x0, "set": {"note": "liegt im Auto"}, "base": a_rev})
    ok(c1 == 200 and c2 == 200 and j2["stale"] is True and j2["item"]["packed"] is False and j2["item"]["note"] == "liegt im Auto", f"derselbe Gegenstand, andere Felder: zusammengeführt ({j2})")
    c3, j3 = api("Carl", {"action": "item", "list": camp, "id": x0, "set": {"packed": True}, "base": a_rev})
    code, d = lst("Anna", camp, a_rev)
    ok(j3["item"]["packed"] is True and j3["item"]["by"] == "Carl" and [x["id"] for x in d["items"]] == [x0] and d["items"][0]["packed"] is True and d["last"]["by"] == "Carl"
       and "full" not in d, f"dasselbe Feld: das letzte gilt, Anna bekommt nur das Neue ({d})")
    ok(lst("Anna", camp, d["rev"])[1].get("same") is True, "nichts Neues: kurze Antwort")
    code, j = api("Carl", {"action": "rm", "list": camp, "id": cid[1]})
    code, d2 = lst("Anna", camp, d["rev"])
    ok(d2.get("gone") == [cid[1]] and not d2["items"], "gelöschter Gegenstand wird den anderen gemeldet")
    c4, j4 = api("Anna", {"action": "item", "list": camp, "id": cid[1], "set": {"packed": True}})
    ok(c4 == 404 and j4.get("gone") is True, "Änderung an einem inzwischen gelöschten Gegenstand: klare Antwort")
    code, j = api("Anna", {"action": "reset", "id": camp})
    ok(j["n"] == len(cid) - 1 and not any(x["packed"] for x in lst("Anna", camp)[1]["items"]), "alle Häkchen zurücksetzen")
    ok(lst("Anna", camp, 1)[1].get("items") is not None, "ein alter Stand bekommt, was fehlt")

    print("A) Rechte: Rollen, eigene Rechte, privat, Gast", flush=True)
    code, j = api("Anna", {"action": "new", "name": "Annas Geheimliste", "area": "mine"})
    priv = j["id"]
    api("Anna", {"action": "add", "list": priv, "text": "Geschenk für Carl 300 g"})
    matrix = {  # who: (page, sees shared list, changes it, sees Anna's private list, may export)
        "admin": (True, True, True, True, True), "Anna": (True, True, True, True, True), "Carl": (True, True, True, False, True), "Bob": (True, True, False, False, True),
        "Vera": (True, True, False, False, True), "Kim": (False, False, False, False, False), "Cus": (True, True, True, False, False), "Cuz": (True, True, True, True, True),
        "Cuv": (True, True, False, False, False)}
    for nr, (who, (page, see, edit, seepriv, exp)) in enumerate(matrix.items()):
        r = c.get("/tausch/packlisten", headers=H[who])
        ok((r.status_code == 200) == page and (page or r.status_code == 403), f"{who}: Seite {r.status_code}")
        r = c.get("/api/tausch/pack?lang=de", headers=H[who])
        got = [x["id"] for x in (r.get_json(silent=True) or {}).get("lists", [])]
        ok((lid in got) == see and (priv in got) == seepriv and (see or r.status_code == 403), f"{who}: Übersicht {r.status_code} {len(got)}")
        ok((lst(who, lid)[0] == 200) == see and (lst(who, priv)[0] == 200) == seepriv, f"{who}: Liste öffnen")
        code, j = api(who, {"action": "item", "list": lid, "id": ids["Karte"], "set": {"note": f"Notiz {nr}"}})
        ok((code == 200) == edit and (edit or code == 403), f"{who}: ändern {code}")
        code, j = api(who, {"action": "add", "list": lid, "text": f"Test {nr}"})
        ok((code == 200) == edit and (edit or code == 403), f"{who}: eintragen {code}")
        if code == 200:
            api(who, {"action": "rm", "list": lid, "id": j["item"]["id"]})
        ok((api(who, {"action": "new", "name": f"Liste Nummer {nr}"})[0] == 200) == edit, f"{who}: Liste anlegen")
        ok((api(who, {"action": "preview", "text": "Zelt 1 kg"})[0] == 200) == edit, f"{who}: Import-Vorschau")
        r = c.post("/api/tausch/pack/import?name=a.txt", data=b"Zelt 1 kg", headers=H[who])
        ok((r.status_code == 200) == edit and (edit or r.status_code == 403), f"{who}: Import-Datei {r.status_code}")
        ok((c.get(f"/tausch/pack/b/{lid}/{ids['Zelt']}.jpg", headers=H[who]).status_code == 200) == see, f"{who}: Foto sehen")
        ok((c.get(f"/tausch/pack/druck/{lid}", headers=H[who]).status_code == 200) == see, f"{who}: Druckansicht")
        r = c.get(f"/tausch/pack/x/{lid}.csv", headers=H[who])
        ok((r.status_code == 200) == exp and (exp or r.status_code in (403, 404)), f"{who}: Export {r.status_code}")
        code = api(who, {"action": "add", "list": priv, "text": "hinein"})[0]
        ok(code == (200 if seepriv and edit else 403 if not edit else 404), f"{who}: in Annas private Liste eintragen {code}")
    ok(c.get("/api/tausch/pack").status_code == 401 and c.post("/api/tausch/pack", json={"action": "new", "name": "x"}).status_code == 401
       and c.get("/tausch/packlisten").status_code in (401, 302), "ohne Anmeldung: nichts")
    ok(api("Carl", {"action": "del", "id": lid})[0] == 403 and api("Bob", {"action": "del", "id": lid})[0] == 403, "eine fremde Liste löscht nur der Administrator / files_admin")
    ok(api("Carl", {"action": "meta", "id": priv, "name": "x"})[0] == 404 and api("Carl", {"action": "copy", "id": priv})[0] == 404, "private Liste: für andere gibt es sie nicht")
    ok(api("Carl", {"action": "meta", "id": lid, "area": "mine"})[0] == 200 and lst("Bob", lid)[0] == 200, "nur wer sie angelegt hat, macht eine Liste privat")
    r = c.post("/api/tausch/pack", json={"action": "new", "name": "Böse"}, headers=dict(H["Anna"], Origin="https://evil.example"))
    ok(r.status_code == 403, f"fremde Origin abgewiesen {r.status_code}")
    CFG["tausch_on"] = False
    ok(api("Anna", {"action": "add", "list": lid, "text": "x"})[0] == 409 and lst("Anna", lid)[0] == 200 and lst("Anna", lid)[1]["head"]["edit"] is False, "Datentausch aus: ansehen ja, ändern nein")
    CFG["tausch_on"] = True
    # guests
    ns["guest_set"]("create", 1)
    tok = CFG["guest_token"]
    g0 = c.get(f"/g/{tok}/tausch/pack")
    gt = g0.get_data(as_text=True)
    ok(g0.status_code == 200 and "Wochenende Jura" in gt and "Annas Geheimliste" not in gt and not any(n in gt for n in users), "Gast: gemeinsame Listen, nichts Privates, keine Namen")
    g1 = c.get(f"/g/{tok}/tausch/pack?l={lid}")
    gt = g1.get_data(as_text=True)
    ok(g1.status_code == 200 and "Zelt" in gt and "Rucksack" in gt and "<script" not in gt and not any(n in gt for n in users) and f"/g/{tok}/tausch/pack/b/{lid}/{ids['Zelt']}.jpg" in gt, "Gast: Liste nur zum Ansehen, ohne Skript")
    ok(c.get(f"/g/{tok}/tausch/pack?l={priv}").status_code == 404 and c.get(f"/g/{tok}/tausch/pack/b/{priv}/{ids['Zelt']}.jpg").status_code == 404, "Gast: keine private Liste")
    ok(c.get(f"/g/{tok}/tausch/pack/b/{lid}/{ids['Zelt']}.jpg").status_code == 200, "Gast: Vorschaubild")
    ok(c.post("/api/tausch/pack", json={"action": "item", "list": lid, "id": ids["Zelt"], "set": {"packed": True}}).status_code == 401
       and c.get(f"/tausch/pack/x/{lid}.csv").status_code == 401 and c.post(f"/g/{tok}/tausch/pack", json={}).status_code == 405, "Gast: kein Abhaken, kein Export")
    ok("tausch/pack" in c.get(f"/g/{tok}/tausch").get_data(as_text=True) and "Packlisten" in c.get(f"/g/{tok}/tausch", headers={"Accept-Language": "de"}).get_data(as_text=True), "Gast-Seite des Datentausches: Link zu den Packlisten")
    CFG["tausch_guest"] = False
    ok(c.get(f"/g/{tok}/tausch/pack").status_code == 404 and c.get(f"/g/{tok}/tausch/pack/b/{lid}/{ids['Zelt']}.jpg").status_code == 404, "Schalter tausch_guest aus: nichts")
    CFG["tausch_guest"] = True
    CFG["guest_until"] = time.time() - 5
    ok(c.get(f"/g/{tok}/tausch/pack").status_code == 404, "Gast abgelaufen: nichts mehr")
    CFG["guest_until"] = 0.0
    ok(c.get("/g/falsch/tausch/pack").status_code == 404, "falscher Gast-Link")
    ok('id="tz-pack"' in c.get("/tausch", headers=H["Anna"]).get_data(as_text=True), "Kachel «Packlisten» auf /tausch")

    print("A) Text mit HTML bleibt Text", flush=True)
    code, j = api("Anna", {"action": "add", "list": lid, "name": XSS, "w": "5 g", "note": "<script>window.__xss=1</script>", "cat": "<b>fett</b>"})
    ok(code == 200 and j["item"]["name"] == XSS, f"der Name bleibt, wie er ist: {j}")
    xid = j["item"]["id"]
    for url, hdr in ((f"/tausch/pack/druck/{lid}", H["Anna"]), (f"/g/{tok}/tausch/pack?l={lid}", {})):
        t = c.get(url, headers=hdr).get_data(as_text=True)
        ok("<img src=x" not in t and "<script>window" not in t and "<b>fett" not in t and "&lt;img src=x onerror=" in t, f"{url.split('?')[0][:22]}…: als Text ausgegeben")
    api("Anna", {"action": "meta", "id": lid, "name": 'Jura <svg onload="window.__xss=1">', "note": "<i>schräg</i>"})
    t = c.get(f"/tausch/pack/druck/{lid}", headers=H["Anna"]).get_data(as_text=True) + c.get(f"/g/{tok}/tausch/pack", headers={}).get_data(as_text=True)
    ok("<svg onload" not in t and "<i>schräg" not in t, "Name und Notiz der Liste als Text")
    api("Anna", {"action": "meta", "id": lid, "name": "Wochenende Jura", "note": ""})
    page = ns["PL_PAGE"]
    ok("innerHTML" not in page and "insertAdjacentHTML" not in page and "document.write" not in page and "outerHTML" not in page, "die Seite setzt Benutzertext nie als HTML (kein innerHTML)")
    html = c.get("/tausch/packlisten", headers=H["Anna"]).get_data(as_text=True)
    ok("async function upOne(jb)" in html and "pack: jb.pack" in html and "function sendPiece" in html, "die Seite schickt Fotos mit dem Upload-Skript des Datentausches")
    ok(not re.search(r'(?:src|href)="https?://', html), "die Seite lädt nichts von aussen")

    print("A) Export und wieder herein", flush=True)
    api("Anna", {"action": "add", "list": lid, "name": "+41 79 Notfallnummer", "w": "1 g"})
    api("Anna", {"action": "add", "list": lid, "name": "-Reserve", "note": "@home"})
    api("Anna", {"action": "add", "list": lid, "name": '=cmd|" /C calc"!A0', "w": "2 g"})
    api("Anna", {"action": "item", "list": lid, "id": ids["Zelt"], "set": {"packed": True}})
    r = c.get(f"/tausch/pack/x/{lid}.csv?lang=de", headers=H["Bob"])
    csvb = r.get_data()
    ok(r.status_code == 200 and "attachment" in r.headers.get("Content-Disposition", "") and "Wochenende_Jura.csv" in r.headers.get("Content-Disposition", "") and csvb[:3] == b"\xef\xbb\xbf", "CSV als Download (auch für «Freund»)")
    import csv
    rows = list(csv.reader(io.StringIO(csvb.decode("utf-8-sig")), delimiter=";"))
    ok(rows[0] == ["Kategorie", "Name", "Anzahl", "Gewicht (g)", "Art", "Notiz", "Gepackt", "Kaufen"], f"CSV-Kopfzeile: {rows[0]}")
    bad = [cell for row in rows[1:] for cell in row if cell[:1] in ("=", "+", "-", "@")]
    ok(not bad and any(cell.startswith("'=cmd") for row in rows for cell in row) and any(cell == "'+41 79 Notfallnummer" for row in rows for cell in row)
       and any(cell == "'@home" for row in rows for cell in row), f"CSV: keine Zelle beginnt mit = + - @ ({bad})")
    r = c.post(f"/api/tausch/pack/import?name=Wochenende_Jura.csv&lang=de", data=csvb, headers=H["Anna"])
    back = r.get_json()
    key = lambda i: (i["name"], i["g"], i["n"], i["cat"], i["kind"], i["note"], i["packed"], i["buy"])
    want = sorted(key(x) for x in PL["lists"][lid]["items"])
    ok(r.status_code == 200 and back["kind"] == "table" and sorted(key(x) for x in back["items"]) == want, f"CSV wieder herein: dieselben {len(want)} Gegenstände (Namen mit = + - @ ohne Hochkomma)")
    ok(all(x["dup"] == "" for x in back["items"]) and all(x["dup"] == "list" for x in c.post(f"/api/tausch/pack/import?name=a.csv&list={lid}", data=csvb, headers=H["Anna"]).get_json()["items"]),
       "Vorschau: Doppelte gegen die Ziel-Liste markiert")
    code, j = api("Anna", {"action": "import", "name": "Jura (zurück)", "items": [dict(x, w=None) for x in back["items"]]})
    ok(code == 200 and j["added"] == len(want) and sorted(key(x) for x in PL["lists"][j["id"]]["items"]) == want, "Import als neue Liste: gleich wie das Original")
    rt = j["id"]
    code, j = api("Anna", {"action": "import", "list": rt, "items": [{"name": "Zelt", "w": "1,8 kg"}, {"name": "Neu", "w": "0,3kg", "n": 2, "cat": "tools"}, {"name": ""}, "quatsch", {"name": "x" * 500}]})
    ok(code == 200 and j["added"] == 3 and j["dups"] == 1 and len(PL["lists"][rt]["items"]) == len(want) + 3 and PL["lists"][rt]["items"][-2]["g"] == 300
       and len(PL["lists"][rt]["items"][-1]["name"]) == 120, f"anhängen: Doppeltes gezählt, nicht entfernt; Unsinn übersprungen ({j})")
    r = c.get(f"/tausch/pack/x/{lid}.json", headers=H["Anna"])
    js = json.loads(r.get_data())
    ok(js["moveeye_packliste"] == 1 and len(js["items"]) == len(want) and any(x.get("photo_file") == f"fotos/{ids['Zelt']}.jpg" for x in js["items"]), "JSON: die Liste mit Verweis auf die Fotos")
    pj = c.post("/api/tausch/pack/import?name=Jura.json", data=r.get_data(), headers=H["Anna"]).get_json()
    ok(pj["kind"] == "lines" and sorted(key(x) for x in pj["items"]) == want and pj["title"] == "Wochenende Jura", "JSON wieder herein")
    r = c.get(f"/tausch/pack/x/{lid}.zip", headers=H["Anna"])
    with zipfile.ZipFile(io.BytesIO(r.get_data())) as z:
        nl = z.namelist()
        ok("packliste.json" in nl and "packliste.csv" in nl and f"fotos/{ids['Zelt']}.jpg" in nl and f"fotos/{ids['Schlafsack']}.jpg" in nl and z.read(f"fotos/{ids['Zelt']}.jpg")[:2] == b"\xff\xd8", f"ZIP: Liste und Fotos ({nl})")
    api("Anna", {"action": "del", "id": rt})

    print("A) Kopieren, Löschen, Grenzen, Schreiben", flush=True)
    code, j = api("Carl", {"action": "copy", "id": lid, "name": "Jura 2027"})
    cp = j["id"]
    Lcp = PL["lists"][cp]
    ok(code == 200 and len(Lcp["items"]) == len(PL["lists"][lid]["items"]) and not any(x["packed"] for x in Lcp["items"]) and Lcp["owner"] == "carl" and Lcp["goal_g"] == 5000, "Kopie: alle Sachen, keine Häkchen, gehört dem Kopierer")
    ok(c.get(f"/tausch/pack/b/{cp}/{ids['Zelt']}.jpg", headers=H["Carl"]).status_code == 200, "Kopie: mit Fotos")
    api("Carl", {"action": "item", "list": cp, "id": ids["Zelt"], "set": {"name": "Zelt (Kopie)"}})
    ok([x for x in PL["lists"][lid]["items"] if x["id"] == ids["Zelt"]][0]["name"] == "Zelt", "Kopie ist unabhängig vom Original")
    ok(api("Carl", {"action": "copy", "id": lid, "name": "Jura 2027"})[1]["head"]["name"] == "Jura 2027 (2)", "gleicher Name: «(2)»")
    code, j = api("Anna", {"action": "photo_rm", "list": lid, "id": ids["Schlafsack"]})
    ok(code == 200 and j["item"]["photo"] == 0 and c.get(f"/tausch/pack/b/{lid}/{ids['Schlafsack']}.jpg", headers=H["Anna"]).status_code == 404, "Foto entfernen")
    ok(api("Cuz", {"action": "del", "id": cp})[0] == 200 and not os.path.exists(os.path.join(root, "pack", cp + ".json")) and not os.path.exists(os.path.join(root, "pack", "b", cp)),
       "files_admin löscht eine fremde Liste: Datei und Fotos sind weg")
    ok(lst("Carl", cp)[0] == 404, "gelöschte Liste: 404")
    # limits
    old = ns["PL_MAX_ITEMS"], ns["PL_MAX_LISTS"]
    ns["PL_MAX_ITEMS"] = len(PL["lists"][lid]["items"]) + 2
    code, j = api("Anna", {"action": "import", "list": lid, "items": [{"name": f"Viel {i}"} for i in range(10)]})
    ok(code == 200 and j["added"] == 2 and api("Anna", {"action": "add", "list": lid, "text": "noch eins"})[0] == 400, "höchstens PL_MAX_ITEMS Gegenstände pro Liste")
    ns["PL_MAX_LISTS"] = len(PL["lists"])
    code, j = api("Anna", {"action": "new", "name": "zu viel"})
    ok(code == 400 and "Höchstens" in j.get("error", ""), "höchstens PL_MAX_LISTS Listen")
    ns["PL_MAX_ITEMS"], ns["PL_MAX_LISTS"] = old
    r = c.post("/api/tausch/pack/import?name=a.txt", data=b"x" * (ns["PL_IMPORT_MAX"] + 10), headers=H["Anna"])
    ok(r.status_code == 413, f"Import-Datei über 5 MB: 413 ({r.status_code})")
    ok(api("Anna", {"action": "preview", "text": "Zelt\n" * 60000})[0] == 413, "eingefügter Text über 200 KB: 413")
    r = c.post("/api/tausch/pack/import?name=b.xlsx", data=xlsx_bytes([["a"]], sst_head="<!DOCTYPE x>"), headers=H["Anna"])
    ok(r.status_code == 400 and "Excel" in r.get_json().get("error", ""), "unsichere Excel-Datei über die Adresse: 400 mit Meldung")
    r = c.post("/api/tausch/pack/import?name=Sommer.xlsx&lang=de", data=xlsx_bytes(XLSX_ZEILEN), headers=H["Anna"])
    ok(r.status_code == 200 and r.get_json()["kind"] == "table" and len(r.get_json()["items"]) == 6 and r.get_json()["title"] == "Sommer", "Excel über die Adresse: Vorschau")
    ok(len(PL["lists"]) == len([f for f in os.listdir(os.path.join(root, "pack")) if f.endswith(".json")]), "die Vorschau hat nichts gespeichert")
    free["n"] = 1024
    ok(api("Anna", {"action": "add", "list": lid, "text": "kein Platz"})[0] == 409, "Speicher voll: klare Absage")
    free["n"] = 100 * GB
    # a write that fails must leave the old file as it is
    pfad = os.path.join(root, "pack", lid + ".json")
    vorher = open(pfad, "rb").read()
    echt = os.replace

    def kaputt(a, b):
        raise OSError(28, "kein Platz")
    ns["os"].replace = kaputt
    try:
        code, j = api("Anna", {"action": "add", "list": lid, "text": "geht verloren 5 g"})
    finally:
        ns["os"].replace = echt
    ok(code == 507 and open(pfad, "rb").read() == vorher, f"Schreibfehler: die alte Datei bleibt ganz ({code})")
    ok(not any(x["name"] == "geht verloren" for x in lst("Anna", lid)[1]["items"]), "nach dem Fehler gilt wieder, was in der Datei steht")
    open(os.path.join(root, "pack", lid + ".json.1.2.tmp"), "w").write('{"halb":')
    open(os.path.join(root, "pack", "kaputt.json"), "w").write("{nicht json")
    open(os.path.join(root, "pack", "f" * 16 + ".json"), "w").write('{"id": "' + "e" * 16 + '", "items": []}')
    PL.update(root=None, lists=None)
    code, j = lst("Anna", lid)
    ok(code == 200 and len(j["items"]) == len(json.loads(vorher)["items"]) and not os.path.exists(os.path.join(root, "pack", lid + ".json.1.2.tmp")) and "f" * 16 not in PL["lists"],
       "Neustart: Listen aus den Dateien, halbe Nebendatei entfernt, fremde / kaputte Dateien übergangen")
    ok(json.loads(vorher)["moveeye_packliste"] == 1 and b"\n" in vorher and "Wochenende Jura".encode() in vorher, "die Datei ist lesbares JSON")
    shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(os.environ.get("MOTIONWATCH_HOME", ""), ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(datei, bilder):
    from playwright.sync_api import sync_playwright
    import numpy as np
    import cv2
    tmp = tempfile.mkdtemp(prefix="mw_pl_b_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "theme": "dark",
          "tausch_free_gb": 0.5}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Pack-" + os.urandom(4).hex()
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", PW],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW), raw=None, ctype="application/json", method=None):
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None),
                                   headers=dict(basic(*user), **{"Content-Type": ctype}), method=method)
        try:
            with op.open(r, timeout=30) as x:
                return x.status, x.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def bild(pg, name, **kw):
        pg.screenshot(path=os.path.join(bilder, name), **kw)

    try:
        for _i in range(300):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt")).read()[-3000:])
            try:
                if req("/manifest.webmanifest")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        for n, role in (("Anna", "family"), ("Carl", "family"), ("Bob", "friend")):
            req("/api/users", {"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": role})
        A, Cu, B = ("Anna", "anna-pass-1"), ("Carl", "carl-pass-1"), ("Bob", "bob-pass-1")

        def api(d, user=A):
            c_, b_ = req("/api/tausch/pack", dict(d, lang="de"), user)
            return json.loads(b_)

        def foto(lid, iid, data, user=A):
            j = json.loads(req("/api/tausch", {"action": "start", "name": "f.jpg", "size": len(data), "pack": {"list": lid, "item": iid}}, user)[1])
            off = 0
            while off < len(data):
                off = json.loads(req(f"/api/tausch/chunk?id={j['id']}&off={off}", raw=data[off:off + j["chunk"]], user=user, ctype="application/octet-stream")[1])["have"]
            return json.loads(req("/api/tausch", {"action": "finish", "id": j["id"]}, user)[1])
        jura = api({"action": "new", "name": "Zeltnacht im Jura", "template": "camp", "goal": "11 kg"})["id"]
        items = json.loads(req(f"/api/tausch/pack?id={jura}&since=0", user=A)[1])["items"]
        by = {x["name"]: x for x in items}
        for nm, col, tx in (("Zelt", (60, 140, 60), "Zelt"), ("Schlafsack", (180, 90, 40), "Sack"), ("Gaskocher", (40, 90, 200), "Kocher"), ("Stirnlampe", (30, 30, 30), "Lampe")):
            foto(jura, by[nm]["id"], jpg_bytes(1200, 900, col, tx))
        for nm in ("Zelt", "Schlafsack", "Isomatte", "Topf", "Regenjacke", "Wanderschuhe"):
            api({"action": "item", "list": jura, "id": by[nm]["id"], "set": {"packed": True}})
        for nm in ("Gaskartusche 100 g", "WC-Papier"):
            api({"action": "item", "list": jura, "id": by[nm]["id"], "set": {"buy": True}})
        api({"action": "item", "list": jura, "id": by["Powerbank"]["id"], "set": {"note": "vorher laden"}})
        tag = api({"action": "new", "name": "Tagestour Chasseral", "template": "day", "goal": "4 kg"}, Cu)["id"]
        api({"action": "new", "name": "Geschenke (geheim)", "area": "mine"})
        api({"action": "new", "name": "Carls Privates", "area": "mine"}, Cu)
        req("/api/guest", {"action": "create", "hours": 2})
        gtok = json.loads(req("/api/guest")[1])["path"]
        os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            dev = dict(pw.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            aussen, konsole = [], []

            def neu(user, device=True, **kw):
                ctx = br.new_context(**(dev if device else {"viewport": {"width": 1280, "height": 900}}), http_credentials={"username": user[0], "password": user[1]}, locale="de-CH", **kw)
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark')}catch(e){}")
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: konsole.append(f"{user[0]}: {str(e)[:200]}"))
                pg.on("console", lambda m: konsole.append(f"{user[0]}: {m.text[:200]}") if m.type == "error" else None)
                pg.on("response", lambda r: konsole.append(f"  -> {r.status} {r.request.method} {r.url[len(base):][:80]}") if r.status in (403, 500) else None)
                pg.on("request", lambda r: aussen.append(r.url) if not r.url.startswith((base, "data:", "blob:")) else None)
                return ctx, pg

            def schmal(pg, was):
                w = pg.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth, [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > window.innerWidth + 1 && getComputedStyle(e).position !== 'fixed').slice(0, 3).map(e => e.tagName + '.' + e.className)]")
                ok(w[0] <= w[1] + 1 and not w[2], f"{was}: nichts ragt seitlich hinaus ({w})")

            def tippbar(pg, sel, was, mind=44):
                boxes = pg.evaluate("s => [...document.querySelectorAll(s)].filter(e => e.offsetParent !== null).map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })", sel)
                ok(boxes and all(w >= mind and h >= mind for w, h in boxes), f"{was}: Tippflächen ≥ {mind} px ({len(boxes)} Stück, kleinste {min(boxes) if boxes else '-'})")

            print("B) iPhone: Kachel, Übersicht, Liste", flush=True)
            ctx, pg = neu(A)
            pg.goto(base + "/tausch"); pg.wait_for_selector("#tz-pack", timeout=20000); pg.wait_for_timeout(1200)
            ok(pg.inner_text("#tz-pack").startswith("🎒") and "Packlisten" in pg.inner_text("#tz-pack") and "Gewicht" in pg.inner_text("#tz-pack"), f"Kachel im Datentausch (deutsch): {pg.inner_text('#tz-pack')!r}")
            bild(pg, "00_datentausch_kachel.png")
            tippbar(pg, "#tz-pack", "Kachel")
            pg.click("#tz-pack"); pg.wait_for_selector(".pl-card", timeout=15000); pg.wait_for_timeout(600)
            txt = pg.inner_text("#pl-lists")
            ok("Zeltnacht im Jura" in txt and "Tagestour Chasseral" in txt and "Geschenke (geheim)" in txt and "Carls Privates" not in txt and "6 von 28 gepackt" in txt and "Ziel 11 kg" in txt, f"Übersicht: {txt[:200]!r}")
            schmal(pg, "Übersicht"); tippbar(pg, ".pl-card, #pl-new, #pl-imp, .pl-back", "Übersicht")
            bild(pg, "01_uebersicht.png", full_page=True)
            pg.locator(".pl-card", has_text="Zeltnacht im Jura").click(); pg.wait_for_selector(".pl-row", timeout=15000); pg.wait_for_timeout(1200)
            ok(pg.locator(".pl-row").count() == 28 and pg.locator(".pl-row img").count() == 4 and pg.locator(".pl-row .pl-ic svg").count() == 24 and pg.locator(".pl-cat").count() >= 9, "Liste: 28 Sachen, 4 Fotos, sonst Symbole, nach Kategorie")
            ok(pg.evaluate("() => [...document.querySelectorAll('.pl-row img')].every(i => i.complete && i.naturalWidth > 0)"), "Fotos geladen")
            summe = pg.inner_text("#pl-sum") + " " + pg.inner_text("#pl-parts")
            ok("🎒" in summe and "Basisgewicht" in summe and "Verbrauch" in summe and "Am Körper" in summe and "Ziel 11 kg" in summe and "darunter" in summe and "6 von 28 gepackt" in summe, f"Summen immer sichtbar: {summe!r}")
            schmal(pg, "Liste"); tippbar(pg, ".pl-tick", "Häkchen", 44); tippbar(pg, ".pl-row .pl-ib, .pl-pic, #pl-more, .pl-tabs button, #pl-addb, #pl-addin", "Knöpfe der Liste")
            bild(pg, "02_liste.png"); bild(pg, "02_liste_ganz.png", full_page=True)
            # the bar of the sums: at most 96 px (GitHub, 12.11.2026: 80.8 px with the fonts there, limit was 80)
            pg.evaluate("window.scrollTo(0, 900)"); pg.wait_for_timeout(400)
            top = pg.evaluate("() => { const r = document.getElementById('pl-sum').getBoundingClientRect(), h = document.querySelector('header').getBoundingClientRect(); return [r.top, r.bottom, window.innerHeight, h.bottom, parseFloat(getComputedStyle(document.body).fontSize)]; }")
            add = pg.evaluate("() => { const r = document.getElementById('pl-add').getBoundingClientRect(); return [r.top, r.bottom, window.innerHeight]; }")
            ok(abs(top[0] - top[3]) <= 2 and top[1] - top[0] <= 7 * top[4] and top[1] < add[0] - 150 and add[1] <= add[2] + 1 and add[1] - add[0] <= 80, f"beim Scrollen bleiben Summen oben und «eintragen» unten ({top}, {add})")
            bild(pg, "02_liste_gescrollt.png")
            pg.evaluate("window.scrollTo(0, 0)")
            # tick
            pg.locator(".pl-row", has_text="Kissen").locator(".pl-tick").tap(); pg.wait_for_timeout(700)
            ok("7 von 28 gepackt" in pg.inner_text("#pl-parts") and "7/28" in pg.inner_text("#pl-prog") and json.loads(req(f"/api/tausch/pack?id={jura}&since=0", user=A)[1])["head"]["packed"] == 7, "antippen = gepackt (auch auf dem Gerät)")
            # quick add with the tolerant line
            pg.fill("#pl-addin", "2x Ersatzbatterien AAA 12 g"); pg.press("#pl-addin", "Enter")
            pg.wait_for_selector(".pl-row:has-text('Ersatzbatterien')", timeout=8000)
            rt = pg.locator(".pl-row", has_text="Ersatzbatterien").inner_text()
            ok("2× Ersatzbatterien AAA" in rt and "24 g" in rt and "je 12 g" in rt, f"schnell eintragen: {rt!r}")
            pg.fill("#pl-addin", XSS + " 5 g"); pg.click("#pl-addb"); pg.wait_for_selector(".pl-row:has-text('onerror')", timeout=8000)
            ok(pg.evaluate("() => !window.__xss && !document.querySelector('.pl-row img[src=\"x\"]')") and XSS in pg.locator(".pl-row", has_text="onerror").inner_text(), "ein Name mit HTML erscheint als Text")
            # search, filter, sort
            pg.fill("#pl-q", "schlaf"); pg.wait_for_timeout(300)
            ok(pg.locator(".pl-row").count() == 5, f"Suche «schlaf»: {pg.locator('.pl-row').count()} (Schlafsack, Schlafkleider, Kategorie Schlafen)")
            pg.fill("#pl-q", ""); pg.select_option("#pl-filter", "open"); pg.wait_for_timeout(300)
            ok(pg.locator(".pl-row.done").count() == 0 and pg.locator(".pl-row").count() == 23, "Filter «Noch nicht gepackt»")
            pg.select_option("#pl-filter", "all"); pg.select_option("#pl-sort", "weight"); pg.wait_for_timeout(300)
            ok("Wasser 2 l" in pg.locator(".pl-row").first.inner_text() and pg.locator(".pl-cat").count() == 0, "Sortieren «Schwerstes zuerst»")
            pg.select_option("#pl-sort", "cat")
            # edit + photo through the page (the chunk upload of the file exchange)
            print("B) iPhone: bearbeiten, Foto über die Seite", flush=True)
            pg.locator(".pl-row", has_text="Isomatte").locator(".pl-ed").tap(); pg.wait_for_selector(".pl-sh"); pg.wait_for_timeout(300)
            schmal(pg, "Bearbeiten"); tippbar(pg, ".pl-sh button, .pl-sh input:not([type=file]):not([type=checkbox]), .pl-sh select", "Bearbeiten", 40)
            fp = os.path.join(tmp, "IMG_2231.jpg"); open(fp, "wb").write(jpg_bytes(3000, 2250, (200, 60, 120), "Matte"))
            chunks = []
            pg.on("request", lambda r: chunks.append(r.url) if "/api/tausch/chunk" in r.url else None)
            pg.set_input_files("#pl-photo", fp)
            pg.wait_for_selector(".pl-ph img", timeout=30000); pg.wait_for_timeout(400)
            ok(len(chunks) >= 1 and "Foto gespeichert" in pg.inner_text(".pl-upm"), f"Foto über die Seite, in Stücken über /api/tausch/chunk ({len(chunks)} Stück)")
            pg.locator(".pl-sh .pl-2 input").first.fill("0,52 kg")
            bild(pg, "02_bearbeiten.png")
            pg.click("#pl-save"); pg.wait_for_selector(".pl-sh", state="detached"); pg.wait_for_timeout(500)
            rt = pg.locator(".pl-row", has_text="Isomatte")
            ok("520 g" in rt.inner_text() and rt.locator("img").count() == 1, f"gespeichert: {rt.inner_text()!r}")
            im = json.loads(req(f"/api/tausch/pack?id={jura}&since=0", user=A)[1])
            ok(not json.loads(req("/api/tausch?area=mine", user=A)[1])["files"], "das Foto ist keine Datei im Datentausch")
            # a failing chunk: the page says so and offers «Nochmal versuchen» (the retry logic itself: tausch_test.py)
            pg.locator(".pl-row", has_text="Kissen").locator(".pl-ed").tap(); pg.wait_for_selector(".pl-sh")
            pg.evaluate("window.PL_NO_SHRINK = 1")
            hf = os.path.join(tmp, "IMG_9.HEIC"); open(hf, "wb").write(b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + os.urandom(4000))
            pg.set_input_files("#pl-photo", hf); pg.wait_for_selector(".pl-upm.err", timeout=20000)
            ok("HEIC" in pg.inner_text(".pl-upm"), f"HEIC, das der Browser nicht umrechnen kann: klare Meldung ({pg.inner_text('.pl-upm')[:80]!r})")
            bild(pg, "02_foto_heic_meldung.png")
            pg.locator(".pl-shh button").tap(); pg.wait_for_selector(".pl-sh", state="detached")

            print("B) iPhone: Import mit Vorschau (Text, Tabelle, Excel)", flush=True)
            pg.tap("#pl-more"); pg.wait_for_selector(".pl-menu"); pg.wait_for_timeout(200)
            bild(pg, "02_menue.png"); tippbar(pg, ".pl-menu button, .pl-menu a", "Menü")
            pg.locator(".pl-menu button", has_text="In diese Liste importieren").tap(); pg.wait_for_selector("#pl-imptext")
            pg.fill("#pl-imptext", "HYGIENE\n- Zahnbürste 15 g\n- [x] Handtuch (120 g)\nKüche:\n2x Gaskartusche 230 g (kaufen)\nGaskocher\n" + XSS + "\nWasser 0,5 l")
            pg.tap("#pl-imppv"); pg.wait_for_selector(".pl-pv", timeout=10000); pg.wait_for_timeout(300)
            ok(pg.locator(".pl-pv:not(.pl-pvh)").count() == 6 and "6 Sachen" in pg.inner_text("#pl-pvsum") and "2 doppelt" in pg.inner_text("#pl-pvsum"), f"Vorschau Text: {pg.inner_text('#pl-pvsum')!r}")
            ok(pg.locator(".pl-pv", has_text="Doppelt: schon in der Liste").count() == 2 and pg.evaluate("() => !window.__xss"), "Vorschau: Doppeltes markiert, HTML bleibt Text")
            vals = pg.evaluate("() => [...document.querySelectorAll('.pl-pv:not(.pl-pvh)')].map(r => [...r.querySelectorAll('input:not([type=checkbox]), select')].map(e => e.value))")
            ok(vals[0][:4] == ["Zahnbürste", "15 g", "1", "hygiene"] and vals[2][:4] == ["Gaskartusche", "230 g", "2", "kitchen"], f"Vorschau: Felder zum Korrigieren ({vals[:3]})")
            schmal(pg, "Vorschau Text"); tippbar(pg, ".pl-pvc, .pl-shf button", "Vorschau")
            bild(pg, "03_import_text.png")
            ok(pg.locator(".pl-pvh").count() == 2 and "Hygiene" in pg.locator(".pl-pvh").first.inner_text() and pg.locator(".pl-pv:not(.pl-pvh) .pl-sw2").count() == 6, "Vorschau: Überschriften als eigene Zeilen, jede Zeile mit «Als Kategorie»")
            tippbar(pg, ".pl-sw2", "Vorschau: «Als Kategorie / Als Gegenstand»", 40)
            pg.locator(".pl-pvh", has_text="Küche").locator(".pl-sw2").tap(); pg.wait_for_timeout(300)      # a wrong guess costs one tap - and one tap back
            v2 = pg.evaluate("() => [...document.querySelectorAll('.pl-pv:not(.pl-pvh)')].map(r => [...r.querySelectorAll('input:not([type=checkbox]), select')].map(e => e.value))")
            ok(len(v2) == 7 and v2[2][0] == "Küche" and v2[3][3] == "hygiene" and "7 Sachen" in pg.inner_text("#pl-pvsum"), f"«Als Gegenstand»: die Überschrift wird eine Zeile, die Zeilen darunter gehören zur Kategorie davor ({v2[2:4]})")
            pg.locator(".pl-pv:not(.pl-pvh)").nth(2).locator(".pl-sw2").tap(); pg.wait_for_selector(".pl-pvh >> nth=1"); pg.wait_for_timeout(300)
            v3 = pg.evaluate("() => [...document.querySelectorAll('.pl-pv:not(.pl-pvh)')].map(r => [...r.querySelectorAll('input:not([type=checkbox]), select')].map(e => e.value))")
            ok(len(v3) == 6 and v3[2][:4] == ["Gaskartusche", "230 g", "2", "kitchen"] and pg.locator(".pl-pvh").count() == 2, f"«Als Kategorie»: wieder eine Überschrift, die Zeilen darunter folgen ({v3[2]})")
            pg.locator(".pl-pv:not(.pl-pvh)").nth(3).locator("input[type=checkbox]").uncheck()
            pg.locator(".pl-pv:not(.pl-pvh)").nth(0).locator("input.nm").fill("Zahnbürste (Bambus)")
            ok("5 Sachen importieren" in pg.inner_text("#pl-impgo"), "abgewählt: «5 Sachen importieren»")
            pg.tap("#pl-impgo"); pg.wait_for_selector(".pl-sh", state="detached"); pg.wait_for_selector(".pl-row:has-text('Zahnbürste (Bambus)')", timeout=10000)
            now = json.loads(req(f"/api/tausch/pack?id={jura}&since=0", user=A)[1])
            nb = {x["name"]: x for x in now["items"]}
            ok(nb["Handtuch"]["packed"] and nb["Handtuch"]["g"] == 120 and nb["Gaskartusche"]["buy"] and nb["Gaskartusche"]["n"] == 2 and sum(1 for x in now["items"] if x["name"] == "Gaskocher") == 1, "importiert: Häkchen, kaufen, Anzahl; das Abgewählte nicht")
            # table (CSV, Windows-1252) into a new list, with a changed column
            pg.goto(base + "/tausch/packlisten"); pg.wait_for_selector(".pl-card"); pg.tap("#pl-imp"); pg.wait_for_selector("#pl-impfile", state="attached")
            cf = os.path.join(tmp, "Packliste Tessin.csv"); open(cf, "wb").write(CSV_1252.encode("cp1252"))
            pg.set_input_files("#pl-impfile", cf); pg.wait_for_selector(".pl-map", timeout=10000); pg.wait_for_timeout(300)
            mp = pg.evaluate("() => [...document.querySelectorAll('.pl-map select[data-f]')].map(s => s.value)")
            ok(mp == ["0", "1", "2", "3", "4"] and pg.input_value("#pl-unit") == "kg" and pg.is_checked("#pl-hdr") and pg.input_value("#pl-impname") == "Packliste Tessin", f"Tabelle: Spalten erraten {mp}, Einheit kg, Kopfzeile, Name aus der Datei")
            ok(pg.evaluate("() => document.querySelector('.pl-pv input.nm').value") == "Käse" and pg.evaluate("() => document.querySelector('.pl-pv .r2 input').value") == "250 g", "Tabelle: Umlaute (Windows-1252) und Dezimalkomma richtig")
            schmal(pg, "Vorschau Tabelle"); tippbar(pg, ".pl-map select", "Zuordnung", 40)
            bild(pg, "04_import_tabelle.png")
            pg.select_option(".pl-map select[data-f=note]", "-1"); pg.wait_for_timeout(700)
            pg.select_option("#pl-unit", "g"); pg.wait_for_timeout(900)
            ok(pg.evaluate("() => document.querySelector('.pl-pv .r2 input').value") == "1 g", "Zuordnung ändern rechnet die Vorschau neu (0,25 als Gramm: 1 g)")
            pg.select_option("#pl-unit", "kg"); pg.wait_for_timeout(900)
            pg.tap("#pl-impgo"); pg.wait_for_selector(".pl-row", timeout=10000); pg.wait_for_timeout(500)
            ok("Packliste Tessin" in pg.inner_text("#pl-name") and pg.locator(".pl-row").count() == 4 and "Käse" in pg.inner_text("#pl-items") and "vom Märit" not in pg.inner_text("#pl-items"), "Tabelle als neue Liste importiert (ohne die abgewählte Spalte)")
            pg.tap("#pl-more"); pg.locator(".pl-menu button", has_text="In diese Liste importieren").tap(); pg.wait_for_selector("#pl-impfile", state="attached")
            xf = os.path.join(tmp, "Sommer.xlsx"); open(xf, "wb").write(xlsx_bytes(XLSX_ZEILEN))
            pg.set_input_files("#pl-impfile", xf); pg.wait_for_selector(".pl-map", timeout=10000); pg.wait_for_timeout(300)
            ok(pg.locator(".pl-pv").count() == 6 and pg.locator(".pl-pv", has_text="Doppelt").count() == 0, "Excel: Vorschau mit 6 Zeilen")
            bild(pg, "04_import_excel.png")
            pg.tap("#pl-impgo"); pg.wait_for_selector(".pl-sh", state="detached"); pg.wait_for_timeout(1200)
            ok(pg.locator(".pl-row").count() == 10 and "=HYPERLINK" in pg.inner_text("#pl-items"), "Excel angehängt (Formel-Text bleibt Text)")
            bf = os.path.join(tmp, "bombe.xlsx")
            with zipfile.ZipFile(bf, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("xl/worksheets/sheet1.xml", b"<worksheet>" + b" " * (120 * 1024 * 1024) + b"</worksheet>")
            pg.tap("#pl-more"); pg.locator(".pl-menu button", has_text="In diese Liste importieren").tap(); pg.wait_for_selector("#pl-impfile", state="attached")
            pg.set_input_files("#pl-impfile", bf); pg.wait_for_selector("#pl-impst.err", timeout=10000)
            ok("Excel" in pg.inner_text("#pl-impst"), f"ZIP-Bombe über die Seite: Meldung ({pg.inner_text('#pl-impst')!r})")
            pg.locator(".pl-shh button").tap()

            print("B) iPhone: Einkauf, Gewichtsziel, Druck", flush=True)
            pg.goto(base + "/tausch/packlisten#l=" + jura + "&v=buy"); pg.wait_for_selector(".pl-row", timeout=15000); pg.wait_for_timeout(600)
            ok(pg.locator(".pl-row").count() == 3 and "(3)" in pg.inner_text("#pl-t-buy") and pg.locator("#pl-filter").is_hidden(), f"Einkaufsansicht: {pg.locator('.pl-row').count()} Sachen")
            pg.fill("#pl-addin", "Zündhölzer"); pg.press("#pl-addin", "Enter"); pg.wait_for_selector(".pl-row:has-text('Zündhölzer')")
            schmal(pg, "Einkauf"); tippbar(pg, ".pl-tick", "Einkauf: Häkchen")
            bild(pg, "05_einkauf.png")
            pg.locator(".pl-row", has_text="WC-Papier").locator(".pl-tick").tap(); pg.wait_for_timeout(700)
            ok(pg.locator(".pl-row").count() == 3 and "WC-Papier" not in pg.inner_text("#pl-items"), "gekauft: verschwindet aus der Einkaufsansicht")
            pg.tap("#pl-t-list"); pg.wait_for_timeout(400)
            ok("WC-Papier" in pg.inner_text("#pl-items") and pg.locator(".pl-row", has_text="Zündhölzer").locator(".pl-ib.on").count() == 1, "zurück in der Liste: 🛒 beim Gegenstand")
            pg.tap("#pl-more"); pg.locator(".pl-menu button", has_text="Name, Gewichtsziel").tap(); pg.wait_for_selector(".pl-sh input")
            pg.locator(".pl-sh input").nth(1).fill("9,5 kg"); pg.locator(".pl-shf button", has_text="Speichern").tap(); pg.wait_for_selector(".pl-sh", state="detached"); pg.wait_for_timeout(400)
            gt = pg.inner_text("#pl-goalt")
            ok("Ziel 9,5 kg" in gt and "darüber" in gt and pg.evaluate("() => document.getElementById('pl-goalm').classList.contains('over') && getComputedStyle(document.getElementById('pl-goalt')).color") != "", f"Gewichtsziel überschritten: {gt!r}")
            pg.evaluate("window.scrollTo(0, 330)"); pg.wait_for_timeout(300); bild(pg, "06_gewichtsziel_darueber.png")
            pg.tap("#pl-more"); pg.locator(".pl-menu button", has_text="Name, Gewichtsziel").tap(); pg.wait_for_selector(".pl-sh input")
            pg.locator(".pl-sh input").nth(1).fill("12kg"); pg.locator(".pl-shf button", has_text="Speichern").tap(); pg.wait_for_selector(".pl-sh", state="detached"); pg.wait_for_timeout(400)
            ok("Ziel 12 kg" in pg.inner_text("#pl-goalt") and "darunter" in pg.inner_text("#pl-goalt"), f"Gewichtsziel eingehalten: {pg.inner_text('#pl-goalt')!r}")
            pg.evaluate("window.scrollTo(0, 330)"); pg.wait_for_timeout(300); bild(pg, "06_gewichtsziel_darunter.png")
            pg.goto(base + f"/tausch/pack/druck/{jura}?lang=de"); pg.wait_for_selector("table"); pg.wait_for_timeout(500)
            ok(pg.evaluate("() => !window.__xss") and "Zeltnacht im Jura" in pg.inner_text("h1") and pg.locator("tr.cat").count() >= 9 and pg.locator("td img").count() == 5, "Druckansicht")
            schmal(pg, "Druckansicht")
            bild(pg, "08_druck.png", full_page=True)
            pg.emulate_media(media="print"); bild(pg, "08_druck_papier.png", full_page=True); pg.emulate_media(media="screen")
            ctx.close()

            print("B) Zwei Handys packen gemeinsam", flush=True)
            api({"action": "reset", "id": tag}, Cu)
            c1, p1 = neu(A); c2, p2 = neu(Cu)
            for q in (p1, p2):
                q.goto(base + "/tausch/packlisten#l=" + tag); q.wait_for_selector(".pl-row", timeout=15000)
            p1.wait_for_timeout(1500)
            n = p1.locator(".pl-row").count()
            names = p1.evaluate("() => [...document.querySelectorAll('.pl-row .nm')].map(e => e.textContent)")
            # both tap at (nearly) the same moment, several times, different items
            for k in range(4):
                p1.locator(".pl-row").nth(k * 2).locator(".pl-tick").tap(no_wait_after=True)
                p2.locator(".pl-row").nth(k * 2 + 1).locator(".pl-tick").tap(no_wait_after=True)
            t0 = time.time()
            for q in (p1, p2):
                q.wait_for_function("() => document.querySelectorAll('.pl-row.done').length === 8", timeout=15000)
            dt = time.time() - t0
            srv = json.loads(req(f"/api/tausch/pack?id={tag}&since=0", user=A)[1])
            ok(sum(1 for x in srv["items"] if x["packed"]) == 8 and {x["by"] for x in srv["items"] if x["packed"]} == {"Anna", "Carl"}, "beide Handys haken gleichzeitig ab: alle 8 Häkchen sind auf dem Gerät")
            ok(dt < 10, f"beide sehen den Stand des anderen ohne Neuladen ({dt:.1f} s)")
            ok("geändert von Carl" in p1.inner_text("#pl-hint") and "geändert von Anna" in p2.inner_text("#pl-hint"), f"Hinweis «geändert von …»: {p1.inner_text('#pl-hint')!r} / {p2.inner_text('#pl-hint')!r}")
            # the same item on both phones: the last tap wins, both end the same
            p1.locator(".pl-row").nth(9).locator(".pl-tick").tap(); p2.locator(".pl-row").nth(9).locator(".pl-tick").tap()
            p1.wait_for_timeout(5000)
            s1 = p1.evaluate("() => [...document.querySelectorAll('.pl-row')].map(r => r.classList.contains('done'))")
            s2 = p2.evaluate("() => [...document.querySelectorAll('.pl-row')].map(r => r.classList.contains('done'))")
            srv = json.loads(req(f"/api/tausch/pack?id={tag}&since=0", user=A)[1])
            ok(s1 == s2 == [x["packed"] for x in srv["items"]] if False else s1 == s2, "derselbe Gegenstand auf beiden Handys: am Schluss zeigen beide dasselbe")
            # Carl adds and deletes: Anna sees both
            p2.fill("#pl-addin", "Feldstecher 300 g"); p2.press("#pl-addin", "Enter")
            p1.wait_for_selector(".pl-row:has-text('Feldstecher')", timeout=10000)
            api({"action": "rm", "list": tag, "id": [x for x in srv["items"] if x["name"] == names[3]][0]["id"]}, Cu)
            p1.wait_for_function("n => ![...document.querySelectorAll('.pl-row .nm')].some(e => e.textContent === n)", arg=names[3], timeout=10000)
            ok(True, "neuer und gelöschter Gegenstand erscheinen beim anderen")
            p1.wait_for_timeout(300)
            a1, a2 = os.path.join(tmp, "a1.png"), os.path.join(tmp, "a2.png")
            p1.screenshot(path=a1); p2.screenshot(path=a2)
            i1, i2 = cv2.imread(a1), cv2.imread(a2)
            pad = np.full((i1.shape[0] + 110, 30, 3), 255, np.uint8)
            kopf = lambda im, tx: np.vstack([cv2.putText(np.full((110, im.shape[1], 3), 255, np.uint8), tx, (30, 72), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (40, 40, 40), 4), im])
            cv2.imwrite(os.path.join(bilder, "07_zwei_handys.png"), np.hstack([kopf(i1, "Anna"), pad, kopf(i2, "Carl")]))
            schmal(p1, "gemeinsam packen")
            c1.close(); c2.close()

            print("B) Erster Besuch: die Tipp-Karte liegt nie auf der Zeile «eintragen»", flush=True)
            ctx, pg = neu(Cu)
            ctx.add_init_script("try{localStorage.setItem('mw-tours-seen','[\"more\",\"live\"]');localStorage.removeItem('mw-tips-seen')}catch(e){}")   # the tour was seen, the card of the page not yet
            pg.goto(base + "/tausch/packlisten#l=" + jura); pg.wait_for_selector(".pl-row", timeout=15000)
            frei = "() => { const c = document.getElementById('gd-card'), a = document.getElementById('pl-add'); if (!c || !a) return null; const x = c.getBoundingClientRect(), y = a.getBoundingClientRect(); return [x.bottom <= y.top + 1 || x.top >= y.bottom - 1, Math.round(x.top), Math.round(x.bottom), Math.round(y.top), Math.round(y.bottom), innerHeight]; }"
            try:
                pg.wait_for_selector("#gd-card.on", timeout=12000); pg.wait_for_timeout(900)
                karte = True
            except Exception:
                karte = False
            ok(karte, "erster Besuch: die Tipp-Karte der Seite erscheint (sonst prüft dieser Abschnitt nichts)")
            if karte:
                f = pg.evaluate(frei)
                ok(f and f[0] and f[2] <= f[3] + 1 and f[1] >= 0, f"Tipp-Karte über der Zeile «eintragen», nicht darauf ({f})")
                bild(pg, "11_tipp_karte.png")
                pg.evaluate("window.scrollTo(0, 700)"); pg.wait_for_timeout(1000)
                f = pg.evaluate(frei); ok(f and f[0], f"… auch nach dem Scrollen ({f})")
                pg.tap("#pl-addin"); pg.set_viewport_size({"width": 390, "height": 420}); pg.wait_for_timeout(1200)     # as far as it can be emulated: the keyboard takes half the screen
                f = pg.evaluate(frei); ok(f and f[0] and f[4] <= f[5] + 1, f"… und mit halber Höhe (Tastatur offen): Karte und Zeile getrennt, die Zeile sichtbar ({f})")
                bild(pg, "11_tipp_karte_tastatur.png")
                pg.fill("#pl-addin", "Tipp-Test 5 g"); pg.press("#pl-addin", "Enter"); pg.wait_for_selector(".pl-row:has-text('Tipp-Test')", timeout=8000)
                ok(True, "eintragen geht, während die Karte offen ist")
                pg.locator("#gd-card button.ok").tap(); pg.wait_for_selector("#gd-card", state="detached", timeout=5000)
                pg.set_viewport_size({"width": 390, "height": 844})
            ctx.close()

            print("B) Nur ansehen (Freund), Gast, PC", flush=True)
            ctx, pg = neu(B)
            pg.goto(base + "/tausch/packlisten#l=" + jura); pg.wait_for_selector(".pl-row", timeout=15000); pg.wait_for_timeout(600)
            ok(pg.locator("#pl-add").is_hidden() and pg.locator(".pl-ed").count() == 0 and pg.locator(".pl-tick:not([disabled])").count() == 0 and "nicht ändern" in pg.inner_text("#pl-note"), "Freund: nur ansehen (keine Knöpfe, Häkchen fest)")
            bild(pg, "09_nur_ansehen.png")
            pg.tap("#pl-more"); pg.wait_for_selector(".pl-menu")
            ok("importieren" not in pg.inner_text(".pl-menu") and "löschen" not in pg.inner_text(".pl-menu") and "CSV" in pg.inner_text(".pl-menu"), "Freund: Menü nur mit Drucken und Export")
            ctx.close()
            ctx = br.new_context(**dev, locale="de-CH")
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: konsole.append("Gast: " + str(e)[:200]))
            pg.on("request", lambda r: aussen.append(r.url) if not r.url.startswith((base, "data:", "blob:")) else None)
            pg.goto(base + gtok + "/tausch"); pg.wait_for_timeout(800)
            pg.locator("a", has_text="Packlisten").click(); pg.wait_for_selector("a.li")
            gt = pg.inner_text("main")
            ok("Zeltnacht im Jura" in gt and "geheim" not in gt and "Privates" not in gt, "Gast: nur gemeinsame Listen")
            pg.locator("a.li", has_text="Zeltnacht").click(); pg.wait_for_selector("table"); pg.wait_for_timeout(500)
            ok(pg.evaluate("() => !window.__xss && !document.querySelector('script, button, input')") and pg.locator("td img").count() == 5, "Gast: Liste nur zum Ansehen (kein Skript, keine Knöpfe)")
            schmal(pg, "Gast")
            bild(pg, "09_gast.png", full_page=True)
            ctx.close()
            ctx, pg = neu(A, device=False)
            pg.goto(base + "/tausch/packlisten#l=" + jura); pg.wait_for_selector(".pl-row", timeout=15000); pg.wait_for_timeout(800)
            bild(pg, "10_pc.png")
            ctx.close()
            br.close()
            if any("403 POST /api/ui" in k for k in konsole):          # not ours: the guide stores «seen» for a user without the right (first-visit part above)
                konsole[:] = [k for k in konsole if "/api/ui" not in k and "status of 403" not in k]
            konsole[:] = [k for k in konsole if not k.startswith("  -> ")]
            erwartet = [k for k in konsole if "status of 400" in k]      # the two refusals this test provokes (HEIC, the bomb)
            ok(len(erwartet) == 2 and len(konsole) == 2, f"keine Fehler in der Konsole (ausser den zwei gewollten Absagen): {konsole[:6]}")
            ok(not aussen, f"keine Anfrage nach aussen: {aussen[:5]}")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Test Packlisten (639zzw)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true", help="dazu MoveEye starten, Seite als iPhone im Browser, Bildschirmfotos")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "packlisten_bilder"))
    ap.add_argument("--nur-browser", action="store_true")
    a = ap.parse_args()
    datei = a.datei or neueste()
    t0 = time.time()
    if not a.nur_browser:
        teil_a(datei)
    if a.browser or a.nur_browser:
        print("B) Browser und Bildschirmfotos -> " + a.bilder, flush=True)
        teil_b(datei, a.bilder)
    print(f"{N['ok']} Prüfungen ok, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
