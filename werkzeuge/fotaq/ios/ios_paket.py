#!/usr/bin/env python3
"""MoveEye: packs «Queen – iPhone-Test» - the test variants of the engine with their own start page, WITHOUT game data
(on the device they come from the installed game, DATA_DIR/fotaq/data/games). Runs in the workflow «FOTAQ» (job «ios»).

  python3 ios_paket.py --ios <folder of bauen.sh: a/, b/, a.txt, b.txt> --paket <package of fotaq_paket.py: fotaq/> \
      --tag fotaqios-N --stv v2026.4.0 --stv-commit <sha> --commit <sha> --aus <folder>

Result in --aus: fotaqtest/ (unpacked, for the test), fotaq-iostest-N.zip, pins.txt («PIN <file> size=… sha256=… unpacked=…»).
The start page is the one of the game (werkzeuge/fotaq/index.html) with a few exact changes: title, choice of the variant,
diagnostics line (iostest.js), the engine comes from the folder of the variant.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
VARIANTEN = {       # what the owner reads on the test page
    "a": ("Spieldaten in Stücken, wenig Speicher – Programm sonst wie bisher", "game data in pieces, little memory – program otherwise as before"),
    "b": ("wie A, dazu kleines Programm (kleine Funktionen)", "like A, plus a small program (small functions)"),
}
CSS = """
#vars{display:grid;gap:8px;margin:0 0 12px}
a.var{display:block;color:var(--txt);text-decoration:none;background:var(--panel);border:2px solid var(--line);border-radius:12px;padding:10px 12px}
a.var.on{border-color:var(--blue)}a.var b{display:block}a.var span{font-size:13px;color:var(--mut)}
#hist{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:10px 12px;font-size:13px;margin:0 0 14px;overflow-wrap:anywhere}
#hist div{margin-top:4px;color:var(--mut)}#hist div.bad{color:#ff8a8e;font-weight:600}
#dz{position:absolute;left:4px;top:4px;z-index:3;font:10px/1.25 ui-monospace,Menlo,monospace;color:#fff;background:rgba(0,0,0,.6);padding:2px 5px;
  border-radius:5px;pointer-events:none;max-width:96%;overflow-wrap:anywhere}
"""


def seite():
    t = open(os.path.join(HIER, "..", "index.html"), encoding="utf-8").read()

    def tausch(alt, neu):
        nonlocal t
        if t.count(alt) != 1:
            sys.exit("index.html: %r is there %d times, expected once" % (alt[:50], t.count(alt)))
        t = t.replace(alt, neu)
    tausch("<title>Flight of the Amazon Queen</title>", "<title>Queen – iPhone-Test</title>")
    tausch("<div><h1>Flight of the Amazon Queen</h1>", "<div><h1>Queen – iPhone-Test</h1>")
    tausch("</style></head><body>", CSS + "</style></head><body>")
    tausch('  <div class="langs">', '  <div id="vars"></div>\n  <div class="langs">')
    tausch('  <div class="help" id="help"></div>', '  <div id="hist"></div>\n  <div class="help" id="help"></div>')
    tausch('<div id="tip" class="hidden"></div></div>', '<div id="tip" class="hidden"></div><div id="dz"></div></div>')
    tausch('s.src = "scummvm.js";', 's.src = (window.FOTAQ_VAR || "a") + "/scummvm.js";')
    tausch('<script>\n(function () {\n  "use strict";', '<script src="iostest.js"></script>\n<script>\n(function () {\n  "use strict";')
    return t


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ios", required=True)
    ap.add_argument("--paket", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--stv", required=True)
    ap.add_argument("--stv-commit", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    if not re.fullmatch(r"fotaqios-\d{1,4}", a.tag):
        sys.exit("tag must be fotaqios-N")
    N = a.tag.split("-")[1]
    root = os.path.join(a.aus, "fotaqtest")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    open(os.path.join(root, "index.html"), "w", encoding="utf-8").write(seite())
    shutil.copy2(os.path.join(HIER, "iostest.js"), root)
    shutil.copy2(os.path.join(HIER, "..", "thumb.svg"), root)
    var = []
    for v in sorted(VARIANTEN):
        src = os.path.join(a.ios, v)
        if not os.path.isfile(os.path.join(src, "scummvm.wasm")):
            continue
        os.makedirs(os.path.join(root, v))
        for f in ("scummvm.js", "scummvm.wasm"):
            shutil.copy2(os.path.join(src, f), os.path.join(root, v))
        k = json.loads(subprocess.run([sys.executable, "-I", os.path.join(HIER, "wasm_funktionen.py"), os.path.join(src, "scummvm.wasm"), "--json"],
                                      check=True, capture_output=True, text=True).stdout)
        fl = ""
        if os.path.isfile(os.path.join(a.ios, v + ".txt")):
            fl = open(os.path.join(a.ios, v + ".txt"), encoding="utf-8", errors="replace").read().splitlines()[0][:300]
        var.append({"id": v, "de": VARIANTEN[v][0], "en": VARIANTEN[v][1], "wasm": k["file"], "js": os.path.getsize(os.path.join(src, "scummvm.js")),
                    "largest": k["largest"], "from_40000_to_160000": k["from_40000_to_160000"][0], "over_10000": k["over_10000"][0],
                    "memory_pages": k["memory_pages"], "flags": fl, "sha256": sha(os.path.join(src, "scummvm.wasm"))})
    if not var:
        sys.exit("no variant built")
    # the data folder of ScummVM (themes, queen.tbl ...) of the last variant - without the game data
    shutil.copytree(os.path.join(a.paket, "data"), os.path.join(root, "data"), ignore=lambda d_, n: ["games"] if os.path.abspath(d_) == os.path.abspath(os.path.join(a.paket, "data")) else [])
    if not os.path.isfile(os.path.join(root, "data", "queen.tbl")) or not os.path.isfile(os.path.join(root, "data", "index.json")):
        sys.exit("data/queen.tbl or data/index.json missing")
    if "games" not in json.load(open(os.path.join(root, "data", "index.json"))):
        sys.exit("data/index.json does not list games/ (the game data of the installed game)")
    shutil.copytree(os.path.join(a.paket, "lizenzen"), os.path.join(root, "lizenzen"))
    lic = open(os.path.join(a.paket, "LIZENZEN.txt"), encoding="utf-8").read()
    kopf = ["«Queen – iPhone-Test» für MoveEye (%s): Test-Fassungen der Spiel-Engine von «Flight of the Amazon Queen»." % a.tag,
            "Dieses Paket enthält KEINE Spieldaten (sie kommen aus dem installierten Spiel) und ersetzt das Spiel nicht.",
            "Zusätzlich zu den unten genannten Patches: werkzeuge/fotaq/ios/0101 (Spieldaten in Stücken über HTTP statt ganz im Speicher),",
            "andere Bau-Einstellungen je Variante (werkzeuge/fotaq/ios/bauen.sh, ios_konfig.py), Seite iostest.js (MoveEye, MIT).",
            "Quelle dieser Fassung: https://github.com/DonElektro/MotionWatch/tree/%s/werkzeuge/fotaq" % a.commit, "", "---- Angaben des Spiel-Pakets ----", ""]
    open(os.path.join(root, "LIZENZEN.txt"), "w", encoding="utf-8").write("\n".join(kopf) + lic)
    man = {"tag": a.tag, "scummvm": a.stv, "scummvm_commit": a.stv_commit, "moveeye_commit": a.commit, "varianten": var}
    open(os.path.join(root, "fotaqtest.json"), "w", encoding="utf-8").write(json.dumps(man, indent=1, ensure_ascii=False))
    rels = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            rels.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    out = os.path.join(a.aus, "fotaq-iostest-%s.zip" % N)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for r in sorted(rels):
            z.write(os.path.join(root, r), r, compress_type=zipfile.ZIP_STORED if r.lower().endswith((".zip", ".dat", ".png")) else zipfile.ZIP_DEFLATED)
    unz = sum(os.path.getsize(os.path.join(root, r)) for r in rels)
    pins = ["PIN %s size=%d sha256=%s unpacked=%d files=%d" % (os.path.basename(out), os.path.getsize(out), sha(out), unz, len(rels))]
    for v in var:
        pins.append("VARIANTE %s wasm=%d js=%d largest=%d from_40000_to_160000=%d over_10000=%d sha256=%s" % (v["id"], v["wasm"], v["js"], v["largest"], v["from_40000_to_160000"], v["over_10000"], v["sha256"]))
    open(os.path.join(a.aus, "pins.txt"), "w").write("\n".join(pins) + "\n")
    print("\n".join(pins))


if __name__ == "__main__":
    main()
