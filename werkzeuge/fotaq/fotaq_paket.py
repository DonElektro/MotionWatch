#!/usr/bin/env python3
"""MoveEye: packs «Flight of the Amazon Queen» (CD version with speech, German and English) with ScummVM (WebAssembly)
for the games port of MoveEye (/g/fotaq/). Runs in the workflow «FOTAQ» (.github/workflows/fotaq.yml).

  python3 werkzeuge/fotaq/fotaq_paket.py --build <scummvm>/build-emscripten --src <scummvm> --de FOTAQ_Ger_talkie-1.0.zip \
      --en FOTAQ_Talkie-1.1.zip --lizenzen <folder with licence files of the libraries> --tag fotaq-1 --commit <sha> --aus <folder>

Result in --aus: fotaq-engine-N.zip (ScummVM, launcher, licences), fotaq-de-N.zip, fotaq-en-N.zip (game data, unchanged)
and pins.txt («PIN <file> size=… sha256=…»). Every ZIP unpacks into the same folder (DATA_DIR/fotaq/ on the device).
The game data are checked against the detection table of ScummVM (engines/queen/detection.cpp): it must be the CD
version (talkie) in the right language. The original readme files stay unchanged next to the data (licence of the game).
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
SPRACHEN = {"de": "DE_DEU", "en": "EN_ANY"}
QUELLE = "https://github.com/scummvm/scummvm"


def erkennung(src):
    """the entries of engines/queen/detection.cpp: (comment, md5 of the first 5000 bytes, size, language)"""
    t = open(os.path.join(src, "engines", "queen", "detection.cpp"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r'//\s*([^\n]+)\n\s*\{\s*\{\s*"queen",\s*"([^"]*)",\s*AD_ENTRY1s\("(queen\.1c?)",\s*"([0-9a-f]{32})",\s*(\d+)\),\s*Common::(\w+)', t):
        out.append({"what": m.group(1).strip(), "extra": m.group(2), "file": m.group(3), "md5": m.group(4), "size": int(m.group(5)), "lang": m.group(6)})
    if len(out) < 8:
        sys.exit("detection.cpp: too few entries found (%d) - format changed?" % len(out))
    return out


def daten(zp, ziel, lang, tab):
    """unpacks one language (flat, no folders from the ZIP) and checks queen.1c against the detection table"""
    os.makedirs(ziel, exist_ok=True)
    texte = []
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            if i.is_dir():
                continue
            n = i.filename.replace("\\", "/")
            if n.startswith("/") or ".." in n.split("/") or n.startswith("__MACOSX/"):
                sys.exit("%s: bad file name %s" % (zp, n))
            b = os.path.basename(n)
            if not re.fullmatch(r"[A-Za-z0-9._ -]{1,80}", b):
                sys.exit("%s: unexpected file name %r" % (zp, b))
            if os.path.exists(os.path.join(ziel, b)):
                sys.exit("%s: file twice: %s" % (zp, b))
            with z.open(i) as f, open(os.path.join(ziel, b), "wb") as o:
                shutil.copyfileobj(f, o, 1 << 20)
            if b.lower().endswith((".txt", ".doc", ".nfo")) or b.lower().startswith(("readme", "copying", "licen")):
                texte.append(b)
    q = [x for x in os.listdir(ziel) if x.lower() == "queen.1c"]
    if not q:
        sys.exit("%s: queen.1c missing (only compressed CD versions are supported)" % zp)
    p = os.path.join(ziel, q[0])
    with open(p, "rb") as f:
        head = f.read(5000)
    md5, size = hashlib.md5(head).hexdigest(), os.path.getsize(p)
    hit = [e for e in tab if e["md5"] == md5 and e["size"] == size]
    if not hit:
        sys.exit("%s: queen.1c (md5 %s, %d bytes) is not in the detection table of ScummVM" % (zp, md5, size))
    e = hit[0]
    if e["extra"] != "CD" or e["lang"] != SPRACHEN[lang]:
        sys.exit("%s: queen.1c is «%s» %s, not the CD version %s" % (zp, e["extra"], e["lang"], SPRACHEN[lang]))
    if not texte:
        sys.exit("%s: no readme / licence text in the ZIP - the licence asks to keep it with the data" % zp)
    return {"detection": e["what"], "queen.1c": {"size": size, "md5_5000": md5}, "texte": sorted(texte),
            "files": sorted(os.listdir(ziel))}


def zip_dir(root, rels, out):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for r in sorted(rels):
            p = os.path.join(root, r)
            # already compressed (game data, ogg/mp3 inside): stored, the rest deflated
            ct = zipfile.ZIP_STORED if r.lower().endswith((".1c", ".zip", ".dat", ".png")) else zipfile.ZIP_DEFLATED
            z.write(p, r, compress_type=ct)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--de", required=True)
    ap.add_argument("--en", required=True)
    ap.add_argument("--lizenzen", default="")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--stv", required=True, help="ScummVM tag, e.g. v2026.4.0")
    ap.add_argument("--stv-commit", required=True)
    ap.add_argument("--commit", required=True, help="MoveEye commit (workflow + patches)")
    ap.add_argument("--quellen", default="", help="«name sha256 url» per line: the game downloads")
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    n = re.fullmatch(r"(?:fotaq|fotaqprobe)-(\d+)", a.tag)
    if not n:
        sys.exit("tag must be fotaq-N or fotaqprobe-N")
    N = a.tag.split("-", 1)[1]
    tab = erkennung(a.src)
    root = os.path.join(a.aus, "fotaq")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    # ScummVM (wasm + js) and its data folder (themes, queen.tbl ...); no HTML shell of ScummVM: our launcher
    for f in ("scummvm.js", "scummvm.wasm"):
        shutil.copy2(os.path.join(a.build, f), root)
    shutil.copytree(os.path.join(a.build, "data"), os.path.join(root, "data"))
    for x in ("games", "gui-icons", "plugins"):
        p = os.path.join(root, "data", x)
        if os.path.isdir(p) and not [y for y in os.listdir(p) if y != "index.json"]:
            shutil.rmtree(p)
    for f in os.listdir(os.path.join(root, "data")):
        if f == "index.json":
            os.remove(os.path.join(root, "data", f))
    if not os.path.isfile(os.path.join(root, "data", "queen.tbl")):
        sys.exit("data/queen.tbl missing (engine data of the Queen engine)")
    for f in ("index.html", "thumb.svg"):
        shutil.copy2(os.path.join(HIER, f), root)
    info = {}
    for L, zp in (("de", a.de), ("en", a.en)):
        info[L] = daten(zp, os.path.join(root, "data", "games", L), L, tab)
    # licences: ScummVM (GPL v3) and the libraries in the build, the game licence (readme of the data, unchanged)
    lz = os.path.join(root, "lizenzen")
    os.makedirs(lz)
    for f in ("COPYING", "COPYRIGHT", "AUTHORS"):
        if os.path.isfile(os.path.join(a.src, f)):
            shutil.copy2(os.path.join(a.src, f), os.path.join(lz, "ScummVM_" + f + ".txt"))
    if not os.path.isfile(os.path.join(lz, "ScummVM_COPYING.txt")) or "GNU GENERAL PUBLIC LICENSE" not in open(os.path.join(lz, "ScummVM_COPYING.txt"), encoding="utf-8", errors="replace").read():
        sys.exit("COPYING of ScummVM missing")
    if os.path.isdir(os.path.join(a.src, "LICENSES")):
        for f in sorted(os.listdir(os.path.join(a.src, "LICENSES"))):
            shutil.copy2(os.path.join(a.src, "LICENSES", f), os.path.join(lz, "ScummVM_LICENSES_" + f + ("" if f.endswith(".txt") else ".txt")))
    if a.lizenzen and os.path.isdir(a.lizenzen):
        for f in sorted(os.listdir(a.lizenzen)):
            shutil.copy2(os.path.join(a.lizenzen, f), os.path.join(lz, f))
    for L in ("de", "en"):
        for t in info[L]["texte"]:
            shutil.copy2(os.path.join(root, "data", "games", L, t), os.path.join(lz, "FOTAQ_%s_%s" % (L, t)))
    quellen = [x.split() for x in a.quellen.splitlines() if x.strip()]
    lic = ["Flight of the Amazon Queen für MoveEye (%s)" % a.tag, "",
           "Spiel: Flight of the Amazon Queen (1995, CD-Fassung mit Sprachausgabe)",
           "  © 1995 John Passfield & Steven Stamatiadis. Freeware: frei weitergeben auf jedem Medium, solange die Readme-Datei",
           "  und alle Copyright-Hinweise und Haftungsausschlüsse erhalten bleiben; das Spiel darf nicht einzeln verkauft werden,",
           "  die Aufnahme in eine grössere Sammlung ist erlaubt. Den vollen Text enthält die Readme-Datei der Spieldaten",
           "  (unverändert in data/games/de/ und data/games/en/, Kopien hier in lizenzen/FOTAQ_*).",
           "  Die Spieldaten sind UNVERÄNDERT, genau so wie von ScummVM als Freeware verteilt:"]
    for q in quellen:
        lic.append("    %s  sha256 %s  %s" % tuple(q[:3]))
    for L in ("de", "en"):
        lic.append("    %s: %s (queen.1c %d Bytes)" % (L, info[L]["detection"], info[L]["queen.1c"]["size"]))
    lic += ["", "Spiel-Engine: ScummVM %s (WebAssembly, nur die Queen-Engine)" % a.stv,
            "  © The ScummVM Team. Lizenz: GNU General Public License Version 3 oder später (lizenzen/ScummVM_COPYING.txt).",
            "  Quellcode genau dieser Fassung: %s/tree/%s (Commit %s)" % (QUELLE, a.stv, a.stv_commit),
            "  Änderungen von MoveEye (Patches) und der Bau-Ablauf: https://github.com/DonElektro/MotionWatch/tree/%s/werkzeuge/fotaq" % a.commit,
            "  und https://github.com/DonElektro/MotionWatch/blob/%s/.github/workflows/fotaq.yml" % a.commit,
            "  Patches: 0001 Spieldaten relativ zur Seite laden (Ordner /g/fotaq/), 0002 Start-Argumente der Seite behalten, keine Web-MIDI-Anfrage,",
            "           0003 Aufruf der Seite nach dem Einbinden des Speichers (IndexedDB), damit der Spielstand-Ordner pro Sprache besteht,",
            "           0004 Spieldaten in Stücken über HTTP («Range», mit Wiederholung) statt ganz im Speicher,",
            "           0005 nach dem Spielende endet ScummVM und meldet es der Seite (kein Launcher), Fehlermeldungen gehen an die Seite.",
            "  Bau-Einstellungen: werkzeuge/fotaq/ios/bauen.sh (Variante b), ios_konfig.py, asyncify_remove.txt.",
            "", "Bibliotheken im WebAssembly-Paket (Lizenztexte in lizenzen/):",
            "  SDL 3 (zlib-Lizenz), libvorbis / libogg (BSD-3-Clause, Xiph.Org), libmad (GPL-2.0 oder später, Underbit Technologies),",
            "  zlib (zlib-Lizenz), libpng (libpng-Lizenz), Emscripten-Laufzeit (MIT / University of Illinois NCSA).",
            "", "Startseite (index.html) und Symbol (thumb.svg): MoveEye, MIT.", ""]
    open(os.path.join(root, "LIZENZEN.txt"), "w", encoding="utf-8").write("\n".join(lic))
    # the index of the HTTP filesystem of ScummVM (index.json in every folder below data/)
    subprocess.run([sys.executable, "-I", os.path.join(a.src, "dists", "emscripten", "build-make_http_index.py"), os.path.join(root, "data")], check=True)
    rels = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            rels.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    man = {"tag": a.tag, "scummvm": a.stv, "scummvm_commit": a.stv_commit, "moveeye_commit": a.commit,
           "langs": {L: {"detection": info[L]["detection"], "files": info[L]["files"]} for L in info}}
    open(os.path.join(root, "fotaq.json"), "w", encoding="utf-8").write(json.dumps(man, indent=1, ensure_ascii=False))
    rels.append("fotaq.json")
    teile = {"engine": [r for r in rels if not r.startswith(("data/games/de/", "data/games/en/"))],
             "de": [r for r in rels if r.startswith("data/games/de/")], "en": [r for r in rels if r.startswith("data/games/en/")]}
    pins = []
    for k, rr in teile.items():
        out = os.path.join(a.aus, "fotaq-%s-%s.zip" % (k, N))
        zip_dir(root, rr, out)
        unz = sum(os.path.getsize(os.path.join(root, r)) for r in rr)
        pins.append("PIN %s size=%d sha256=%s unpacked=%d files=%d" % (os.path.basename(out), os.path.getsize(out), sha(out), unz, len(rr)))
    w = os.path.getsize(os.path.join(root, "scummvm.wasm")); j = os.path.getsize(os.path.join(root, "scummvm.js"))
    pins.append("SIZE scummvm.wasm=%d scummvm.js=%d data_de=%d data_en=%d" % (w, j, sum(os.path.getsize(os.path.join(root, r)) for r in teile["de"]),
                                                                            sum(os.path.getsize(os.path.join(root, r)) for r in teile["en"])))
    open(os.path.join(a.aus, "pins.txt"), "w").write("\n".join(pins) + "\n")
    print("\n".join(pins))
    print(json.dumps(man, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
