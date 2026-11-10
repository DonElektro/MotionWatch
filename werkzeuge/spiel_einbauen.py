#!/usr/bin/env python3
"""Ein eigenes Spiel aus einem Ordner (z. B. games/wasnun/) in die Spielesammlung games/MotionWatch_Spiele.zip einbauen.

Der Ordner enthält das Spiel so, wie es in der ZIP liegen soll, dazu «kachel.json»: der Eintrag für games.json
(dir, name, desc, icon, start, input, names / descs in de/en/fr/it/rm) und unter "lizenz" die Zeilen für LIZENZEN.txt.
kachel.json selbst kommt nicht in die ZIP.

  python3 werkzeuge/spiel_einbauen.py games/wasnun                       # in die ZIP des Repositorys, Nummer bleibt
  python3 werkzeuge/spiel_einbauen.py games/wasnun --version GS-1.8      # dazu die Nummer der Sammlung setzen
  python3 werkzeuge/spiel_einbauen.py games/wasnun --nach /tmp/test.zip  # nur eine Test-ZIP schreiben (Repository bleibt)
  python3 werkzeuge/spiel_einbauen.py games/schach --entfernen chess --probe   # nur zeigen, was geschähe (schreibt nichts)
  python3 werkzeuge/spiel_einbauen.py games/schach --entfernen chess --version GS-1.12   # neues Spiel an den Platz des alten
  python3 werkzeuge/spiel_einbauen.py --entfernen chess --probe          # nur ein Spiel herausnehmen (hier: Probelauf)

Was geschieht: alle anderen Einträge der ZIP bleiben Byte für Byte; der Ordner des Spiels wird ersetzt; games.json
bekommt den Eintrag (neu: hinter --hinter, Standard «memory», sonst am Schluss; vorhanden: ersetzt); LIZENZEN.txt (in der ZIP
und games/LIZENZEN.txt) bekommt den Block; ohne --nach wird GAMES_PKG in quelle/320_spielecke.py (version, size, sha256)
nachgeführt. Mehrmals laufen lassen ist harmlos. Danach: python3 werkzeuge/spiele_test.py

--entfernen ORDNER nimmt ein Spiel heraus: alle Dateien des Ordners in der ZIP, seinen Eintrag in games.json und seinen
Block in LIZENZEN.txt (ZIP und games/LIZENZEN.txt). Zusammen mit einem neuen Spiel (und ohne ausdrückliches --hinter)
übernimmt das neue den Platz des alten in der Kachel-Reihenfolge und in LIZENZEN.txt. --probe schreibt nichts und listet
genau auf, was entfernt und was eingebaut würde. Entfernen nur nach Entscheid des Besitzers. Gespeicherte Spielstände im
Browser (localStorage) rührt das Werkzeug nicht an.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZEIT = (2026, 11, 10, 12, 0, 0)          # feste Zeit: gleiche Eingabe -> gleiche ZIP


def lizenz_einsetzen(text, d, block, hinter):
    """den Block des Spiels in LIZENZEN.txt ersetzen oder hinter dem Block von «hinter» einfügen"""
    teile = text.split("\n\n")
    neu = "\n".join(block)
    for i, t in enumerate(teile):
        if f"({d}/)" in t.split("\n")[0]:
            teile[i] = neu
            return "\n\n".join(teile)
    for i, t in enumerate(teile):
        if f"({hinter}/)" in t.split("\n")[0]:
            teile.insert(i + 1, neu)
            return "\n\n".join(teile)
    return text.rstrip("\n") + "\n\n" + neu + "\n"


def lizenz_entfernen(text, d):
    """den Block eines Spiels aus LIZENZEN.txt nehmen -> (Text ohne Block, Block oder None, Ordner des Blocks davor oder "")"""
    teile = text.split("\n\n")
    for i, t in enumerate(teile):
        if f"({d}/)" in t.split("\n")[0]:
            m = re.search(r"\(([A-Za-z0-9_\-]{1,40})/\)", teile[i - 1].split("\n")[0]) if i else None
            return "\n\n".join(teile[:i] + teile[i + 1:]), t, m.group(1) if m else ""
    return text, None, ""


def main():
    ap = argparse.ArgumentParser(description="eigenes Spiel in die Spielesammlung einbauen (und / oder eines herausnehmen)")
    ap.add_argument("ordner", nargs="?", default="", help="Ordner des neuen Spiels mit kachel.json (darf mit --entfernen fehlen)")
    ap.add_argument("--zip", default=os.path.join(REPO, "games", "MotionWatch_Spiele.zip"))
    ap.add_argument("--nach", default="", help="Ziel-ZIP (sonst wird --zip ersetzt und GAMES_PKG nachgeführt)")
    ap.add_argument("--version", default="", help="neue Nummer der Sammlung, z. B. GS-1.8 (sonst bleibt sie)")
    ap.add_argument("--hinter", default=None, help="neuer Eintrag hinter diesem Spiel (Ordnername; Standard «memory» bzw. der Platz des entfernten Spiels)")
    ap.add_argument("--entfernen", default="", metavar="ORDNER", help="dieses Spiel aus ZIP, games.json und LIZENZEN.txt nehmen")
    ap.add_argument("--probe", action="store_true", help="nichts schreiben, nur auflisten, was geschähe")
    a = ap.parse_args()
    weg = a.entfernen
    if not a.ordner and not weg:
        ap.error("Ordner des Spiels oder --entfernen ORDNER angeben")
    if (weg and not re.fullmatch(r"[A-Za-z0-9_\-]{1,40}", weg)) or (a.version and not re.fullmatch(r"GS-\d+\.\d+", a.version)):
        sys.exit("Ordnername oder --version passt nicht")
    k, block, d, dateien = None, None, "", []
    if a.ordner:
        ordner = os.path.abspath(a.ordner)
        k = json.load(open(os.path.join(ordner, "kachel.json"), encoding="utf-8"))
        block = k.pop("lizenz")
        d = k["dir"]
        if not re.fullmatch(r"[A-Za-z0-9_\-]{1,40}", d):
            sys.exit("Ordnername passt nicht")
        if d == weg:
            sys.exit("--entfernen nennt das Spiel, das gerade eingebaut wird")
        for wurzel, _, namen in os.walk(ordner):
            for n in sorted(namen):
                p = os.path.join(wurzel, n)
                rel = os.path.relpath(p, ordner).replace(os.sep, "/")
                if rel != "kachel.json" and not n.startswith("."):
                    dateien.append((d + "/" + rel, p))
        dateien.sort()
        if not any(n == d + "/" + k.get("start", "index.html") for n, _ in dateien):
            sys.exit("Startdatei fehlt im Ordner")
    ziel = a.nach or a.zip
    tmp = ziel + ".neu"
    hinter = a.hinter
    with zipfile.ZipFile(a.zip) as z:
        gj = json.loads(z.read("games.json"))
        lic = z.read("LIZENZEN.txt").decode("utf-8")
        alt = gj.get("version", "")
        version = a.version or alt
        gj["version"] = version
        spiele = gj["games"]
        weg_dateien, weg_eintrag, weg_block = [], None, None
        if weg:
            weg_dateien = [zi for zi in z.infolist() if zi.filename.startswith(weg + "/")]
            j = next((j for j, g in enumerate(spiele) if g.get("dir") == weg), None)
            if j is not None:
                weg_eintrag = spiele.pop(j)
                if hinter is None and j > 0:
                    hinter = spiele[j - 1].get("dir")              # the new game takes the place of the removed one
            lic, weg_block, davor = lizenz_entfernen(lic, weg)
            if not weg_dateien and weg_eintrag is None and weg_block is None:
                sys.exit(f"«{weg}» ist nicht in der ZIP (kein Ordner, kein Eintrag, kein Lizenzblock) - nichts zu entfernen")
        lic_hinter = (davor if weg and weg_block and a.hinter is None else None) or hinter or "memory"
        if hinter is None:
            hinter = "memory"
        if k is not None:
            i = next((i for i, g in enumerate(spiele) if g.get("dir") == d), None)
            if i is not None:
                spiele[i] = k
            else:
                j = next((j for j, g in enumerate(spiele) if g.get("dir") == hinter), len(spiele) - 1)
                spiele.insert(j + 1, k)
            lic = lizenz_einsetzen(lic, d, block, lic_hinter)
        lic = lic.replace(f"Spielesammlung {alt}", f"Spielesammlung {version}", 1)
        if weg:
            print(f"Entfernen «{weg}»:")
            print(f"  Dateien in der ZIP: {len([x for x in weg_dateien if not x.filename.endswith('/')])} "
                  f"({sum(x.file_size for x in weg_dateien)} Bytes, gepackt {sum(x.compress_size for x in weg_dateien)})")
            for zi in weg_dateien:
                print(f"    {zi.filename}  {zi.file_size}")
            print("  Eintrag in games.json: " + (json.dumps(weg_eintrag, ensure_ascii=False) if weg_eintrag else "keiner"))
            print("  Block in LIZENZEN.txt: " + ("" if weg_block else "keiner"))
            for zl in (weg_block or "").split("\n"):
                if zl:
                    print("    " + zl)
        if k is not None:
            n = next(i for i, g in enumerate(spiele) if g.get("dir") == d)
            print(f"Einbauen «{d}»: {len(dateien)} Dateien ({sum(os.path.getsize(p) for _, p in dateien)} Bytes), Kachel Nr. {n + 1} von {len(spiele)}"
                  + (f" (hinter «{spiele[n - 1].get('dir')}»)" if n else ""))
        if a.probe:
            print(f"Probelauf: nichts geschrieben. Die ZIP bliebe {version}" + ("" if a.version else " (Nummer mit --version erhöhen)")
                  + f" mit {len(spiele)} Spielen.")
            return
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as o:
            def schreibe(name, daten):
                zi = zipfile.ZipInfo(name, ZEIT)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                o.writestr(zi, daten)
            for zi in z.infolist():
                if zi.filename in ("games.json", "LIZENZEN.txt") or (d and zi.filename.startswith(d + "/")) or (weg and zi.filename.startswith(weg + "/")):
                    continue
                o.writestr(zi, z.read(zi.filename), compress_type=zi.compress_type)     # the other games: unchanged content
            for name, p in dateien:
                schreibe(name, open(p, "rb").read())
            schreibe("games.json", (json.dumps(gj, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
            schreibe("LIZENZEN.txt", lic.encode("utf-8"))
    os.replace(tmp, ziel)
    b = open(ziel, "rb").read()
    print(f"{ziel}: {version}, {len(gj['games'])} Spiele" + (f", {len(dateien)} Dateien in {d}/" if d else "") + f", size {len(b)}, sha256 {hashlib.sha256(b).hexdigest()}")
    if not a.nach:
        lp = os.path.join(REPO, "games", "LIZENZEN.txt")
        t = open(lp, encoding="utf-8").read()
        if weg:
            t = lizenz_entfernen(t, weg)[0]
        if d:
            t = lizenz_einsetzen(t, d, block, lic_hinter)
        open(lp, "w", encoding="utf-8").write(t.replace(f"Spielesammlung {alt}", f"Spielesammlung {version}", 1))
        q = os.path.join(REPO, "quelle", "320_spielecke.py")
        t = open(q, encoding="utf-8").read()
        n = re.sub(r'GAMES_PKG = \{"version": "[^"]+", "file": "([^"]+)", "size": \d+, "sha256": "[0-9a-f]+"\}',
                   lambda m: f'GAMES_PKG = {{"version": "{version}", "file": "{m.group(1)}", "size": {len(b)}, "sha256": "{hashlib.sha256(b).hexdigest()}"}}', t, count=1)
        if n == t and version == alt and f'"size": {len(b)},' in t:
            print("GAMES_PKG: unverändert")
        else:
            open(q, "w", encoding="utf-8").write(n)
            print("GAMES_PKG in quelle/320_spielecke.py und games/LIZENZEN.txt nachgeführt")


if __name__ == "__main__":
    main()
