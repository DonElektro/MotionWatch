#!/usr/bin/env python3
"""MoveEye: packs the ready-made, freely licensed browser games («Fertige Spiele», part 639zzn) for the game corner.

Every game becomes ONE ZIP (release asset at the tag «fspiele-N», never in the Git repository: together they are far
bigger than the game collection games/MotionWatch_Spiele.zip). The ZIP unpacks into DATA_DIR/fspiele/<id>/ on the device.
The sources come from the public repositories at a FIXED commit (QUELLEN below); nothing of their build scripts is run -
files are only copied, the few changes of MoveEye are made here and listed in LIZENZEN.txt of every package.

  python3 -I werkzeuge/fertigspiele/paket.py --quellen <folder with the checkouts> --aus <folder> [--nur fs-angst,…] [--holen]

  --holen   clone the sources into --quellen first (git, fixed commit; in the workflow «Fertige Spiele»)
Result in --aus: fspiele-<id>-N.zip, pins.txt («PIN <file> size=… sha256=… unpacked=… files=…»), <id>/ (unpacked, for tests).
The ZIPs are reproducible: files sorted, stored without compression (pictures and music are compressed already), fixed
time stamps - the same sources give the same sha256 on every computer. Size + sha256 stand in quelle/639zzn (FS_GAMES).
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
TAG = "fspiele-1"
NAME_OK = re.compile(r"[A-Za-z0-9._ /+-]{1,200}")
QUELLEN = {
    "fs-angst": {"repo": "https://github.com/jonasreich/anxiety", "commit": "2148ce8e9f1d72574e73a22876295b107864bae7", "ordner": "jonasreich_anxiety"},
    "fs-heroine": {"repo": "https://github.com/clintbellanger/heroine-dusk", "commit": "2a1f01deff724212a7843e363f9c656fd0b13430", "ordner": "clintbellanger_heroine-dusk"},
    "fs-hexgl": {"repo": "https://github.com/BKcore/HexGL", "commit": "6addc95a2fce3bf05f4d751823cc054c61a16d68", "ordner": "BKcore_HexGL"},
}


def lies(p):
    with open(p, encoding="utf-8-sig") as f:
        return f.read()


def schreib(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)


def ersetze(t, alt, neu, was, n=1):
    """exactly n times - a changed source must not pass silently"""
    if t.count(alt) != n:
        sys.exit("%s: «%s» %d-mal statt %d-mal gefunden - Quelle geändert?" % (was, alt[:60], t.count(alt), n))
    return t.replace(alt, neu)


def kopiere(src, dst, teile, ohne=()):
    for t in teile:
        s = os.path.join(src, t)
        if os.path.isdir(s):
            for dp, dn, fn in os.walk(s):
                dn.sort()
                for f in sorted(fn):
                    r = os.path.relpath(os.path.join(dp, f), src).replace(os.sep, "/")
                    if any(r == o or r.startswith(o.rstrip("/") + "/") or (o.startswith("*") and r.endswith(o[1:])) for o in ohne):
                        continue
                    if os.path.islink(os.path.join(dp, f)):
                        sys.exit("Link in der Quelle: " + r)
                    os.makedirs(os.path.dirname(os.path.join(dst, r)), exist_ok=True)
                    shutil.copyfile(os.path.join(dp, f), os.path.join(dst, r))
        elif os.path.isfile(s):
            os.makedirs(os.path.dirname(os.path.join(dst, t)) or dst, exist_ok=True)
            shutil.copyfile(s, os.path.join(dst, t))
        else:
            sys.exit("fehlt in der Quelle: " + s)


# ---- Abenteuer mit Angst (Adventures With Anxiety, deutsche Fassung) ---------------------------------------------------------------
def bau_angst(src, dst, q):
    kopiere(src, dst, ["index.html", "favicon.png", "LICENSE.txt", "README.md", "scenes", "scripts", "sounds", "sprites", "styles"])
    # two sounds are NOT free (README: «Copyrighted Sounds That I Really Hope Count As Fair Use»): replaced by silence
    for rel, stille in (("sounds/music/pokemon.mp3", "stille_23s.mp3"), ("sounds/sfx/hadouken.mp3", "stille_1s.mp3")):
        if not os.path.isfile(os.path.join(dst, rel)):
            sys.exit("fs-angst: %s fehlt - Quelle geändert?" % rel)
        shutil.copyfile(os.path.join(HIER, "angst", stille), os.path.join(dst, rel))
    shutil.copyfile(os.path.join(HIER, "angst", "thumb.png"), os.path.join(dst, "thumb.png"))
    return ["Abenteuer mit Angst! (Adventures With Anxiety, deutsche Fassung) für MoveEye (%s)" % TAG, "",
            "Spiel: «Adventures With Anxiety» von Nicky Case (Grafik, Code, Text), Musik von Monplaisir, zusätzlicher Code von Spacie.",
            "  Deutsche Übersetzung: Jonas Reich.",
            "  Lizenz: Creative Commons Zero (CC0 1.0, gemeinfrei) für Grafik, Code und Musik - LICENSE.txt und README.md liegen",
            "  unverändert bei (README.md: alle Mitwirkenden und die Liste der Geräusche von freesound.org, Creative Commons, mit",
            "  Urhebern und Links; Geräusche von Kenney.nl, CC0).",
            "  Bibliotheken im Spiel: Howler.js (MIT, James Simpson / GoldFire Studios), MinPubSub (MIT, Daniel Lamb), RSVP.js (MIT, Tilde Inc.).",
            "  Quelle: %s (Commit %s), abgeleitet von https://github.com/ncase/anxiety" % (q["repo"], q["commit"]),
            "", "Änderungen von MoveEye (werkzeuge/fertigspiele/paket.py):",
            "  * sounds/music/pokemon.mp3 (Ausschnitt der Pokémon-Titelmelodie, © The Pokémon Company) und sounds/sfx/hadouken.mp3",
            "    («Hadouken!», © Capcom) sind NICHT frei (im README als «hoffentlich Fair Use» genannt) und wurden durch Stille ersetzt.",
            "  * Nicht im Paket (für das Spiel nicht nötig): misc/, sharing/, COMMON_TERMS.",
            "  * Neu: thumb.png (Kachelbild für die Spielecke, aus einem Bild des Spiels).",
            "  * Sonst ist nichts verändert. MoveEye setzt beim Ausliefern den Knopf «✕ Zurück» auf die Seite.",
            "", "Hinweis: Das Spiel handelt von Angst und psychischer Gesundheit und enthält Kraftausdrücke (abschaltbar in den",
            "Einstellungen des Spiels: «ohne Fluchen»), Alkohol und Sexualität als Themen - ab etwa 12 Jahren.", ""]


# ---- Heroine Dusk ------------------------------------------------------------------------------------------------------------------
def bau_heroine(src, dst, q):
    # the game itself («release/») byte for byte as the author made it (trademark note in the README) - in the folder spiel/
    kopiere(os.path.join(src, "release"), os.path.join(dst, "spiel"), ["."])
    kopiere(src, dst, ["README.md"])
    idx = lies(os.path.join(src, "release", "index.html"))
    skripte = re.findall(r'<script type="text/javascript" src="(js/[a-z]+\.js)"></script>', idx)
    if len(skripte) != 25 or 'onload="init()"' not in idx or '<canvas id="gamecanvas" width="160" height="120">' not in idx or 'id="bgmusic"' not in idx:
        sys.exit("fs-heroine: release/index.html sieht anders aus (%d Skripte) - Startseite von MoveEye anpassen" % len(skripte))
    start = lies(os.path.join(HIER, "heroine", "start.html"))
    start = ersetze(start, "<!--SKRIPTE-->", "\n".join('    <script type="text/javascript" src="%s"></script>' % s for s in skripte), "start.html")
    schreib(os.path.join(dst, "start.html"), start)
    shutil.copyfile(os.path.join(HIER, "heroine", "thumb.png"), os.path.join(dst, "thumb.png"))
    shutil.copyfile(os.path.join(HIER, "heroine", "GPL-3.0.txt"), os.path.join(dst, "GPL-3.0.txt"))
    return ["Heroine Dusk für MoveEye (%s)" % TAG, "",
            "Heroine Dusk is created by Clint Bellanger http://clintbellanger.net",
            "Heroine Dusk features music by Yubatake http://opengameart.org/users/yubatake",
            "",
            "Lizenzen (README.md des Spiels, unverändert im Paket):",
            "  * Code: GNU General Public License Version 3 oder später (Text: GPL-3.0.txt). Der Quellcode ist das Spiel selbst",
            "    (JavaScript, Ordner spiel/js/), vollständig und unverändert.",
            "  * Grafik: Creative Commons Attribution-ShareAlike 3.0 (CC-BY-SA 3.0, spätere Fassungen erlaubt),",
            "    https://creativecommons.org/licenses/by-sa/3.0/ - Clint Bellanger.",
            "  * Musik: Yubatake, Creative Commons Attribution 3.0 (CC-BY 3.0), https://creativecommons.org/licenses/by/3.0/",
            "  * Optionen-Menü: Justin Jacobs (WTFPL). Farbpalette: DawnBringer. Weitere Danksagungen im README.md.",
            "  Quelle: %s (Commit %s), Ordner release/" % (q["repo"], q["commit"]),
            "",
            "Marke: «Heroine Dusk» ist eine Marke (™) von Clint Bellanger. Dies ist KEINE offizielle Quelle des Spiels und MoveEye",
            "ist nicht sein Urheber; offizielle Seite: http://heroinedusk.com. Das Spiel ist inhaltlich UNVERÄNDERT: der Ordner",
            "spiel/ ist Byte für Byte der Ordner release/ der Quelle.",
            "",
            "Von MoveEye dazu (werkzeuge/fertigspiele/, nichts am Spiel geändert):",
            "  * start.html: Startseite für Handys (Angabe «viewport», Platz für den Knopf «✕ Zurück»). Sie lädt dieselben Skripte in",
            "    derselben Reihenfolge wie spiel/index.html und ist wie der Code des Spiels unter der GPL v3 oder später.",
            "  * thumb.png: Kachelbild (verkleinertes Bild aus dem Spiel, ohne das Logo; CC-BY-SA 3.0, Clint Bellanger).",
            "  * LIZENZEN.txt (diese Datei), GPL-3.0.txt (Lizenztext).", ""]


# ---- HexGL -------------------------------------------------------------------------------------------------------------------------
def bau_hexgl(src, dst, q):
    kopiere(src, dst, ["index.html", "launch.js", "favicon.png", "LICENSE", "README.md", "audio", "bkcore", "bkcore.coffee", "css", "geometries", "libs",
                       "textures", "textures.full"],
            ohne=("libs/Editor.html", "libs/Editor_files", "libs/Three.r53.js", "libs/leap-0.4.1.min.js", "bkcore.coffee/tests.html", "*.coffee",
                  "textures/particles/cloud - Copie.png", "textures/particles/spark - Copie.png",
                  "textures.full/particles/cloud - Copie.png", "textures.full/particles/spark - Copie.png"))
    t = lies(os.path.join(src, "index.html"))
    a, b = t.index('    <script type="text/javascript">\n    //analytics'), t.index("  </head>")
    if "google-analytics.com/ga.js" not in t[a:b] or t[a:b].count("</script>") != 1:
        sys.exit("fs-hexgl: der Analytics-Block in index.html sieht anders aus")
    t = t[:a] + t[b:]                                          # Google Analytics: gone
    for alt in ('    <meta property="og:url" content="http://hexgl.bkcore.com/" />\n', '    <meta property="og:image" content="http://hexgl.bkcore.com/image.png" />\n',
                '    <meta property="fb:admins" content="1482017639" />\n', '    <link rel="shortcut icon" href="http://hexgl.bkcore.com/favicon.png" type="image/png">\n'):
        t = ersetze(t, alt, "", "index.html")
    t = ersetze(t, '<link rel="icon" href="http://hexgl.bkcore.com/favicon.png" type="image/png">', '<link rel="icon" href="favicon.png" type="image/png">', "index.html")
    t = ersetze(t, '    <script src="libs/leap-0.4.1.min.js"></script>\n', "", "index.html")     # Leap Motion: would open a WebSocket
    schreib(os.path.join(dst, "index.html"), t)
    # the menu offers «Leap Motion Controller» as third kind of control - without the library: skip it (touch / keyboard / gamepad stay)
    l = lies(os.path.join(src, "launch.js"))
    l = ersetze(l, "return f(a[3] = (a[3] + 1) % a[1].length);",
                "a[3] = (a[3] + 1) % a[1].length;\n      if (a[0] === 'controlType' && a[3] === 2) a[3] = 3;   /* MoveEye: no Leap Motion */\n      return f();", "launch.js")
    l = ersetze(l, "return window.location.href = 'http://get.webgl.org/';", "return false;   /* MoveEye: no link to the outside */", "launch.js")
    schreib(os.path.join(dst, "launch.js"), l)
    shutil.copyfile(os.path.join(HIER, "hexgl", "thumb.png"), os.path.join(dst, "thumb.png"))
    shutil.copyfile(os.path.join(HIER, "hexgl", "OFL-1.1.txt"), os.path.join(dst, "css", "BebasNeue-OFL-1.1.txt"))
    return ["HexGL für MoveEye (%s)" % TAG, "",
            "Spiel: HexGL, futuristisches Rennspiel (HTML5 / WebGL) von Thibaut Despoulain (BKcore), http://bkcore.com",
            "  Mitwirkende: townxelliot, mahesh.kk. Schiffsmodell «HexMKI»: Charnel. Streckentextur: Nobiax.",
            "  Quelle: %s (Commit %s)" % (q["repo"], q["commit"]),
            "",
            "Lizenz - ACHTUNG, ZWEI ANGABEN IN DER QUELLE:",
            "  * README.md: «Unless specified in the file, HexGL's code and resources are now licensed under the MIT License.»",
            "    Der MIT-Text liegt bei (LICENSE, Copyright (c) 2015 Thibaut Despoulain).",
            "  * Die neun Dateien in bkcore/hexgl/ (der Kern des Spiels) tragen im Kopf noch den Vermerk «Creative Commons",
            "    Attribution-NonCommercial 3.0 Unported» (https://creativecommons.org/licenses/by-nc/3.0/). Nach dem Wortlaut des",
            "    README («unless specified in the file») gilt für diese Dateien CC BY-NC 3.0: Weitergabe und Änderung mit",
            "    Namensnennung sind erlaubt, aber NICHT für kommerzielle Zwecke. Die Vermerke sind unverändert im Paket.",
            "  * Klänge (audio/LICENSE, unverändert im Paket): boost.ogg von IFartInUrGeneralDirection (CC BY 3.0), wind.ogg von",
            "    kangaroovindaloo (CC BY 3.0, bearbeitet von Licson), destroyed.ogg von beman87 (CC BY 3.0, bearbeitet von Licson),",
            "    crash.ogg von qubodup (gemeinfrei), bg.ogg von mu6k (gemeinfrei, bearbeitet von Licson); nach OGG gewandelt von baleboy.",
            "    CC BY 3.0: https://creativecommons.org/licenses/by/3.0/",
            "  * Schrift «Bebas Neue» (css/BebasNeue-webfont.*): Ryoichi Tsunekawa (Dharma Type), SIL Open Font License 1.1",
            "    (css/BebasNeue-OFL-1.1.txt). Die Quelle selbst nennt für die Schrift keine Lizenz.",
            "  * Bibliotheken: three.js (MIT, mrdoob und Mitwirkende; ShaderExtras, Detector, postprocessing gehören dazu),",
            "    stats.js (MIT, mrdoob), dat.GUI (Apache License 2.0, Data Arts Team, Google Creative Lab).",
            "",
            "Änderungen von MoveEye (werkzeuge/fertigspiele/paket.py):",
            "  * index.html: Google Analytics entfernt; Verweise auf hexgl.bkcore.com entfernt (Symbol = favicon.png im Paket);",
            "    Leap-Motion-Bibliothek nicht mehr geladen.",
            "  * launch.js: die Steuerung «Leap Motion Controller» wird im Menü übersprungen; kein Link zu get.webgl.org.",
            "  * Nicht im Paket: package.zip, Editor (libs/Editor*), libs/Three.r53.js, libs/leap-0.4.1.min.js, CoffeeScript-Quellen",
            "    (*.coffee, die erzeugten .js sind dabei), Manifest-Dateien, doppelte Bilder «… - Copie.png».",
            "  * Neu: thumb.png (Kachelbild, aus einem Bild des Spiels), css/BebasNeue-OFL-1.1.txt, diese Datei.",
            "  * MoveEye setzt beim Ausliefern den Knopf «✕ Zurück» auf die Seite.", ""]


BAU = {"fs-angst": bau_angst, "fs-heroine": bau_heroine, "fs-hexgl": bau_hexgl}


def holen(ordner, q):
    """the source at the fixed commit (no build script of the source is run, only git)"""
    if os.path.isdir(os.path.join(ordner, ".git")):
        c = subprocess.run(["git", "-C", ordner, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        if c == q["commit"]:
            return
        shutil.rmtree(ordner)
    os.makedirs(ordner)
    for cmd in (["init", "-q"], ["remote", "add", "origin", q["repo"]], ["fetch", "-q", "--depth", "1", "origin", q["commit"]],
                ["-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"]):
        subprocess.run(["git", "-C", ordner] + cmd, check=True)


def pruefe_quelle(ordner, q, holte):
    c = subprocess.run(["git", "-C", ordner, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if c != q["commit"]:
        sys.exit("%s: Commit %s statt %s" % (ordner, c, q["commit"]))
    st = subprocess.run(["git", "-C", ordner, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    if st:
        sys.exit("%s: Quelle ist verändert:\n%s" % (ordner, st[:400]))


def zip_stabil(root, out):
    rels = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            rels.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    rels.sort()
    unz = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for r in rels:
            if not NAME_OK.fullmatch(r) or r.startswith("/") or ".." in r.split("/"):
                sys.exit("Dateiname passt nicht ins Paket: %r" % r)
            zi = zipfile.ZipInfo(r, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED
            zi.create_system = 3
            zi.external_attr = 0o100644 << 16
            with open(os.path.join(root, r), "rb") as f:
                b = f.read()
            unz += len(b)
            z.writestr(zi, b)
    return unz, len(rels)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quellen", required=True)
    ap.add_argument("--aus", required=True)
    ap.add_argument("--nur", default="")
    ap.add_argument("--holen", action="store_true")
    a = ap.parse_args()
    N = TAG.split("-")[1]
    nur = [x for x in a.nur.split(",") if x] or list(BAU)
    os.makedirs(a.aus, exist_ok=True)
    pins = []
    for gid in nur:
        q = QUELLEN[gid]
        src = os.path.join(a.quellen, q["ordner"])
        if a.holen:
            holen(src, q)
        pruefe_quelle(src, q, a.holen)
        dst = os.path.join(a.aus, gid)
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst)
        lic = BAU[gid](src, dst, q)
        schreib(os.path.join(dst, "LIZENZEN.txt"), "\n".join(lic))
        schreib(os.path.join(dst, "fspiel.json"), json.dumps({"id": gid, "tag": TAG, "quelle": q["repo"], "commit": q["commit"]}, indent=1) + "\n")
        out = os.path.join(a.aus, "fspiele-%s-%s.zip" % (gid[3:], N))
        unz, n = zip_stabil(dst, out)
        pins.append("PIN %s size=%d sha256=%s unpacked=%d files=%d" % (os.path.basename(out), os.path.getsize(out), sha(out), unz, n))
    mode = "a" if a.nur and os.path.isfile(os.path.join(a.aus, "pins.txt")) else "w"
    with open(os.path.join(a.aus, "pins.txt"), mode) as f:
        f.write("\n".join(pins) + "\n")
    print("\n".join(pins))


if __name__ == "__main__":
    main()
