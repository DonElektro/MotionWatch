#!/usr/bin/env python3
"""Simulator im Browser: aus dem Godot-Web-Export (Vorlage «Web», 8 Dateien) das Paket sim-web.zip für den Release sim-X.Y.Z.

Warum ein eigenes Paket: der Webspace des Besitzers (MoveEye → Mehr → Homepage, Teil 639zzzh) ersetzt beim Hochladen jeden
Punkt im Dateinamen ausser dem letzten durch «_» (beobachtet: «index.audio.worklet.js» → «index_audio_worklet.js»). Darum hat
im Paket jede Datei genau einen Punkt, und die Verweise darauf sind angepasst:
  index.audio.worklet.js      → index_audio_worklet.js       (index.js: `${loadPath}.audio.worklet.js` → `${loadPath}_audio_worklet.js`)
  index.icon.png              → index_icon.png               (index.html: href)
  index.apple-touch-icon.png  → index_apple-touch-icon.png   (index.html: href)
Die Dateien liegen ohne Ordner in der ZIP (so lädt MoveEye sie nach Sim/ hoch). Nur der Release-Workflow «Sim-Pakete»
(.github/workflows/sim_pi.yml, Paket «web») und die Tests rufen das auf; MoveEye nimmt das Paket nur mit der signierten
Prüfsumme aus versions.json «sim.anhang.web» an (Teil 300).

  python3 werkzeuge/sim_web_paket.py packen EXPORTORDNER ZIEL.zip
  python3 werkzeuge/sim_web_paket.py pruefen PAKET.zip            # Exit 0 = gut (auch für versionen.paket_inhalt «web»)
"""
import os
import re
import sys
import zipfile

PFLICHT = ("index.html", "index.js", "index.wasm", "index.pck", "index_audio_worklet.js")
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}\.[a-z0-9]{1,12}$")        # genau ein Punkt: der Webspace ändert nichts mehr
MAX_DATEI = 100 * 1024 * 1024                                         # Grenze des Webspace pro Datei
MAX_SUMME = 400 * 1024 * 1024                                         # Platz: 500 MB, dazu Startseite / Funk
WORKLET_ALT = "`${loadPath}.audio.worklet.js`"
WORKLET_NEU = "`${loadPath}_audio_worklet.js`"


def neuer_name(n):
    a, _, e = n.rpartition(".")
    return a.replace(".", "_") + "." + e if a else n


def packen(ordner, ziel):
    namen = sorted(n for n in os.listdir(ordner) if os.path.isfile(os.path.join(ordner, n)))
    umben = {n: neuer_name(n) for n in namen}
    daten = {}
    for alt, neu in umben.items():
        with open(os.path.join(ordner, alt), "rb") as f:
            daten[neu] = f.read()
    js = daten.get("index.js", b"").decode("utf-8")
    if js.count(WORKLET_ALT) != 1:
        raise SystemExit("index.js: %s nicht genau einmal (andere Godot-Fassung?)" % WORKLET_ALT)
    daten["index.js"] = js.replace(WORKLET_ALT, WORKLET_NEU).encode("utf-8")
    html = daten.get("index.html", b"").decode("utf-8")
    for alt, neu in umben.items():
        if alt != neu and alt.endswith(".png"):
            html = html.replace('"%s"' % alt, '"%s"' % neu)
    daten["index.html"] = html.encode("utf-8")
    tmp = ziel + ".neu"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for n in sorted(daten):
            zi = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))   # feste Zeit: gleicher Export = gleiche ZIP
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, daten[n])
    fehler = pruefen(tmp)
    if fehler:
        os.remove(tmp)
        raise SystemExit("sim-web.zip: " + "; ".join(fehler))
    os.replace(tmp, ziel)
    print("sim-web.zip: %d Dateien, %d Bytes -> %s" % (len(daten), os.path.getsize(ziel), ziel))
    return 0


def pruefen(pfad):
    """[] = gut, sonst die Gründe (dieselben Regeln wie MoveEye hp_sim_files, Teil 639zzzh)"""
    f = []
    try:
        with zipfile.ZipFile(pfad) as z:
            inf = z.infolist()
            namen = [i.filename for i in inf]
            if len(inf) > 16:
                f.append("zu viele Dateien (%d)" % len(inf))
            for i in inf:
                if not NAME_RE.match(i.filename):
                    f.append("Name %r: genau ein Punkt, ohne Ordner" % i.filename[:80])
                if i.file_size > MAX_DATEI:
                    f.append("%s grösser als 100 MB" % i.filename)
            if sum(i.file_size for i in inf) > MAX_SUMME:
                f.append("zusammen grösser als 400 MB")
            for p in PFLICHT:
                if p not in namen:
                    f.append("%s fehlt" % p)
            if not f:
                js = z.read("index.js").decode("utf-8", "replace")
                if WORKLET_NEU not in js or WORKLET_ALT in js:
                    f.append("index.js lädt nicht index_audio_worklet.js")
                html = z.read("index.html").decode("utf-8", "replace")
                if "index.js" not in html or re.search(r'(?:href|src)="index\.[^".]+\.[a-z]+"', html):
                    f.append("index.html verweist auf einen Namen mit zwei Punkten")
                if z.read("index.wasm")[:4] != b"\0asm":
                    f.append("index.wasm ist kein WebAssembly")
    except (OSError, zipfile.BadZipFile, KeyError) as e:
        f.append("keine gültige ZIP (%s)" % e.__class__.__name__)
    return f


def main(a):
    if len(a) == 3 and a[0] == "packen":
        return packen(a[1], a[2])
    if len(a) == 2 and a[0] == "pruefen":
        f = pruefen(a[1])
        print("sim-web.zip:", "; ".join(f) if f else "ok")
        return 1 if f else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
