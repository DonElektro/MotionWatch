#!/usr/bin/env python3
"""Ein eigenes Spiel aus einem Ordner (z. B. games/wasnun/) in die Spielesammlung games/MotionWatch_Spiele.zip einbauen.

Der Ordner enthält das Spiel so, wie es in der ZIP liegen soll, dazu «kachel.json»: der Eintrag für games.json
(dir, name, desc, icon, start, input, names / descs in de/en/fr/it/rm) und unter "lizenz" die Zeilen für LIZENZEN.txt.
kachel.json selbst kommt nicht in die ZIP.

  python3 werkzeuge/spiel_einbauen.py games/wasnun                       # in die ZIP des Repositorys, Nummer bleibt
  python3 werkzeuge/spiel_einbauen.py games/wasnun --version GS-1.8      # dazu die Nummer der Sammlung setzen
  python3 werkzeuge/spiel_einbauen.py games/wasnun --nach /tmp/test.zip  # nur eine Test-ZIP schreiben (Repository bleibt)

Was geschieht: alle anderen Einträge der ZIP bleiben Byte für Byte; der Ordner des Spiels wird ersetzt; games.json
bekommt den Eintrag (neu: hinter --hinter, Standard «memory», sonst am Schluss; vorhanden: ersetzt); LIZENZEN.txt (in der ZIP
und games/LIZENZEN.txt) bekommt den Block; ohne --nach wird GAMES_PKG in quelle/320_spielecke.py (version, size, sha256)
nachgeführt. Mehrmals laufen lassen ist harmlos. Danach: python3 werkzeuge/spiele_test.py
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


def main():
    ap = argparse.ArgumentParser(description="eigenes Spiel in die Spielesammlung einbauen")
    ap.add_argument("ordner")
    ap.add_argument("--zip", default=os.path.join(REPO, "games", "MotionWatch_Spiele.zip"))
    ap.add_argument("--nach", default="", help="Ziel-ZIP (sonst wird --zip ersetzt und GAMES_PKG nachgeführt)")
    ap.add_argument("--version", default="", help="neue Nummer der Sammlung, z. B. GS-1.8 (sonst bleibt sie)")
    ap.add_argument("--hinter", default="memory", help="neuer Eintrag hinter diesem Spiel (Ordnername)")
    a = ap.parse_args()
    ordner = os.path.abspath(a.ordner)
    k = json.load(open(os.path.join(ordner, "kachel.json"), encoding="utf-8"))
    block = k.pop("lizenz")
    d = k["dir"]
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,40}", d) or (a.version and not re.fullmatch(r"GS-\d+\.\d+", a.version)):
        sys.exit("Ordnername oder --version passt nicht")
    dateien = []
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
    with zipfile.ZipFile(a.zip) as z, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as o:
        gj = json.loads(z.read("games.json"))
        lic = z.read("LIZENZEN.txt").decode("utf-8")
        alt = gj.get("version", "")
        version = a.version or alt
        gj["version"] = version
        spiele = gj["games"]
        i = next((i for i, g in enumerate(spiele) if g.get("dir") == d), None)
        if i is not None:
            spiele[i] = k
        else:
            j = next((j for j, g in enumerate(spiele) if g.get("dir") == a.hinter), len(spiele) - 1)
            spiele.insert(j + 1, k)
        lic = lizenz_einsetzen(lic, d, block, a.hinter).replace(f"Spielesammlung {alt}", f"Spielesammlung {version}", 1)

        def schreibe(name, daten):
            zi = zipfile.ZipInfo(name, ZEIT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            o.writestr(zi, daten)
        for zi in z.infolist():
            if zi.filename in ("games.json", "LIZENZEN.txt") or zi.filename.startswith(d + "/"):
                continue
            o.writestr(zi, z.read(zi.filename), compress_type=zi.compress_type)     # the other games: unchanged content
        for name, p in dateien:
            schreibe(name, open(p, "rb").read())
        schreibe("games.json", (json.dumps(gj, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        schreibe("LIZENZEN.txt", lic.encode("utf-8"))
    os.replace(tmp, ziel)
    b = open(ziel, "rb").read()
    print(f"{ziel}: {version}, {len(gj['games'])} Spiele, {len(dateien)} Dateien in {d}/, size {len(b)}, sha256 {hashlib.sha256(b).hexdigest()}")
    if not a.nach:
        lp = os.path.join(REPO, "games", "LIZENZEN.txt")
        t = open(lp, encoding="utf-8").read()
        open(lp, "w", encoding="utf-8").write(lizenz_einsetzen(t, d, block, a.hinter).replace(f"Spielesammlung {alt}", f"Spielesammlung {version}", 1))
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
