#!/usr/bin/env python3
"""Inhalts-Paket für den 3D-Simulator bauen (Fotorealismus F2, 31.10.2026).

Die freien Inhalte (CC0: HDRI-Himmel und PBR-Texturen von Poly Haven / ambientCG) liegen NICHT im Repository.
Der Simulator lädt sie beim ersten Start der Szene «Camping-Platz» nach (scripts/inhalte.gd):
  1. das ganze Paket als ZIP (katalog.json → paket.url, z. B. ein Anhang eines GitHub-Release), sonst
  2. jede Datei einzeln von Poly Haven / ambientCG (katalog.json → inhalte[].laden).
Fehlt etwas, nimmt der Simulator für diese Fläche die bisherigen Code-Materialien.

Dieses Werkzeug baut das ZIP:

    python3 werkzeuge/inhalte_paket.py --liste                  # was gehört dazu, woher (Name, URL, Auflösung)
    python3 werkzeuge/inhalte_paket.py --laden ORDNER            # alles von Poly Haven / ambientCG in ORDNER laden
    python3 werkzeuge/inhalte_paket.py --zip ORDNER [--eintragen]
            # ZIP aus den Dateien in ORDNER bauen (fehlende werden gemeldet, das Paket geht trotzdem);
            # --eintragen schreibt Grösse und SHA-256 in simulator3d/inhalte/katalog.json (paket.size / paket.sha256)

Danach das ZIP als Anhang eines GitHub-Release hochladen (Tag «inhalte-f2», Dateiname wie paket.name) – oder den Ordner
(ohne ZIP) neben die MoveEyeSim3D.exe in «inhalte/» legen. Gepackte Terrain3D-Demo-Texturen (…_alb_ht.png /
…_nrm_rgh.png, gleiche ambientCG-Quelle) werden mit --zip / --laden automatisch in die ambientCG-Dateinamen zerlegt.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KATALOG = os.path.join(ROOT, "simulator3d", "inhalte", "katalog.json")
CREDITS = os.path.join(ROOT, "simulator3d", "CREDITS.md")
UA = "MoveEye-Inhalte/1 (+https://github.com/DonElektro/MotionWatch)"


def katalog() -> dict:
    with open(KATALOG, encoding="utf-8") as f:
        return json.load(f)


def liste(k: dict, ordner: str = "") -> int:
    fehlt = 0
    for e in k["inhalte"]:
        da = [n for n in e["dateien"].values() if ordner and os.path.exists(os.path.join(ordner, n))]
        stand = "" if not ordner else ("  [da]" if len(da) == len(e["dateien"]) else "  [FEHLT %d]" % (len(e["dateien"]) - len(da)))
        print("%-18s %-4s %-10s %-26s %s%s" % (e["id"], e["aufloesung"], e["quelle"], e["asset"], e["seite"], stand))
        for u in e["laden"]:
            print("    " + u)
        if stand.startswith("  [FEHLT"):
            fehlt += 1
    return fehlt


def _get(u: str) -> bytes:
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def laden(k: dict, ordner: str) -> None:
    os.makedirs(ordner, exist_ok=True)
    for e in k["inhalte"]:
        if all(os.path.exists(os.path.join(ordner, n)) for n in e["dateien"].values()):
            continue
        for u in e["laden"]:
            try:
                data = _get(u)
            except Exception as ex:                       # noqa: BLE001 - weitermachen, am Schluss melden
                print("FEHLER %s: %s" % (u, ex))
                continue
            if u.endswith(".zip") or data[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for n in z.namelist():
                        if os.path.basename(n) in e["dateien"].values():
                            with open(os.path.join(ordner, os.path.basename(n)), "wb") as f:
                                f.write(z.read(n))
            else:
                with open(os.path.join(ordner, u.rsplit("/", 1)[-1]), "wb") as f:
                    f.write(data)
            print("geladen: " + u)


def terrain3d_zerlegen(ordner: str) -> None:
    """ground037_alb_ht.png / ground037_nrm_rgh.png (Terrain3D-Demo) -> Ground037_1K-JPG_Color / NormalGL / Roughness.jpg"""
    try:
        from PIL import Image
    except ImportError:
        return
    for t3d, acg in (("ground037", "Ground037"), ("rock023", "Rock023")):
        a, n = os.path.join(ordner, t3d + "_alb_ht.png"), os.path.join(ordner, t3d + "_nrm_rgh.png")
        if not (os.path.exists(a) and os.path.exists(n)) or os.path.exists(os.path.join(ordner, acg + "_1K-JPG_Color.jpg")):
            continue
        ia, inn = Image.open(a).convert("RGBA"), Image.open(n).convert("RGBA")
        ia.convert("RGB").save(os.path.join(ordner, acg + "_1K-JPG_Color.jpg"), quality=90)
        inn.convert("RGB").save(os.path.join(ordner, acg + "_1K-JPG_NormalGL.jpg"), quality=92)
        inn.getchannel("A").save(os.path.join(ordner, acg + "_1K-JPG_Roughness.jpg"), quality=90)
        print("zerlegt: %s -> %s_1K-JPG_*.jpg" % (t3d, acg))


def bauen(k: dict, ordner: str, eintragen: bool) -> str:
    terrain3d_zerlegen(ordner)
    name = k["paket"]["name"]
    ziel = os.path.join(ordner, name)
    inhalt = {"version": k["version"], "dateien": {}, "fehlt": []}
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_STORED) as z:     # JPG / HDR sind schon gepackt
        for e in k["inhalte"]:
            for rolle, n in e["dateien"].items():
                p = os.path.join(ordner, n)
                if not os.path.exists(p):
                    inhalt["fehlt"].append(n)
                    continue
                with open(p, "rb") as f:
                    data = f.read()
                z.writestr(n, data)
                inhalt["dateien"][n] = {"id": e["id"], "rolle": rolle, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        if os.path.exists(CREDITS):
            z.write(CREDITS, "CREDITS.md")
        z.writestr("inhalt.json", json.dumps(inhalt, indent=1, ensure_ascii=False))
    with open(ziel, "rb") as f:
        data = f.read()
    sha, size = hashlib.sha256(data).hexdigest(), len(data)
    print("Paket: %s  %.1f MB  sha256 %s" % (ziel, size / 1048576.0, sha))
    if inhalt["fehlt"]:
        print("Fehlt (Simulator nimmt dafür die Code-Materialien): " + ", ".join(inhalt["fehlt"]))
    if eintragen:
        with open(KATALOG, encoding="utf-8") as f:
            txt = f.read()
        d = json.loads(txt)
        old = json.dumps(d["paket"], ensure_ascii=False)
        d["paket"]["sha256"], d["paket"]["size"] = sha, size
        txt = txt.replace('"sha256": "%s"' % k["paket"]["sha256"], '"sha256": "%s"' % sha, 1)
        txt = txt.replace('"size": %d' % k["paket"]["size"], '"size": %d' % size, 1)
        with open(KATALOG, "w", encoding="utf-8") as f:
            f.write(txt)
        print("katalog.json: paket %s -> sha256/size eingetragen" % old)
    return ziel


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--liste", nargs="?", const="", metavar="ORDNER", help="Inhalte auflisten (mit ORDNER: was fehlt)")
    ap.add_argument("--laden", metavar="ORDNER", help="alles von Poly Haven / ambientCG laden")
    ap.add_argument("--zip", metavar="ORDNER", help="Paket-ZIP aus ORDNER bauen")
    ap.add_argument("--eintragen", action="store_true", help="Grösse / SHA-256 in katalog.json schreiben")
    a = ap.parse_args()
    k = katalog()
    if a.laden:
        laden(k, a.laden)
        terrain3d_zerlegen(a.laden)
        return 1 if liste(k, a.laden) else 0
    if a.zip:
        bauen(k, a.zip, a.eintragen)
        return 0
    return 1 if liste(k, a.liste or "") else 0


if __name__ == "__main__":
    sys.exit(main())
