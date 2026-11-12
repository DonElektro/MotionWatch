#!/usr/bin/env python3
"""Ablage-Test: das Repository wächst pro MoveEye-Version nicht mehr um die ganze Zusatzdatei (Review Nov. 2026).

  python3 werkzeuge/ablage_test.py

Hintergrund: moveeye_daten_X_Y_Z.zip war EIN gepacktes daten.json (rund 4.9 MB). Gepackte Daten kann git nicht mit der
vorigen Version vergleichen - jede Version legte die ganzen 4.9 MB neu ab. Ab jetzt steht daten.json ungepackt in der ZIP
(bauen.py ZD_GEPACKT = False): der Inhalt ändert sich pro Version nur zu wenigen Prozent, git speichert nur den Unterschied.

Geprüft wird (ohne Netz, ohne Schlüssel, nichts im Repository wird angefasst):
  1. bauen.py schreibt die ZIP ungepackt, zweimal gebaut = Byte für Byte gleich, weit unter der Grenze der Geräte
     (64 MiB, ZD_MAX_BYTES in Teil 397) und unter ZD_GRENZE; der Leser der Geräte (zipfile) liest sie.
  2. Wachstum: in einem Wegwerf-Repository (eigener Ordner im Temp-Verzeichnis, nie das Projekt) kommt nach der Zusatzdatei
     der vorletzten Version die der neuesten dazu (beide ungepackt, anderer Dateiname wie im Projekt), danach die aus
     quelle/ frisch gebaute. Nach «git repack» darf das Paket pro Version um höchstens GRENZE_MB wachsen
     (gemessen 3.69.2 - 3.77.0: 0.06 - 0.11 MB). Zum Vergleich wird gemeldet, was dieselbe Datei gepackt gekostet hätte.
  3. .gitattributes schaltet den Vergleich für ZIP nicht ab («-delta») und die Zusatzdateien liegen nicht in Git LFS.
"""
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import bauen  # noqa: E402

FEHLER = []
GRENZE_MB = 1.0                     # growth per version in the pack (measured 0.06 - 0.11 MB; the whole zip was 4.9 MB)
GERAETE_MAX = 64 * 1024 * 1024      # ZD_MAX_BYTES in part 397 since the first data zip (926d265)


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text)
    if not bed:
        FEHLER.append(text)


def vkey(name):
    return tuple(int(x) for x in re.findall(r"\d+", name))


def ungepackt(daten_json):
    """a data zip exactly as bauen.py writes it now (stored)"""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        zi = zipfile.ZipInfo("daten.json", bauen.ZD_DATE)
        zi.compress_type = zipfile.ZIP_STORED
        zi.external_attr = 0o644 << 16
        z.writestr(zi, daten_json)
    return bio.getvalue()


def gepackt(daten_json):
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        zi = zipfile.ZipInfo("daten.json", bauen.ZD_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        z.writestr(zi, daten_json, compresslevel=9)
    return bio.getvalue()


def git(ordner, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CEILING_DIRECTORIES=os.path.dirname(ordner), GIT_CONFIG_NOSYSTEM="1", HOME=ordner,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    r = subprocess.run(["git", "-C", ordner] + list(args), capture_output=True, text=True, env=env, timeout=300)
    if r.returncode:
        raise RuntimeError("git %s: %s" % (" ".join(args), (r.stderr or r.stdout).strip()[:300]))
    return r.stdout


def paket_bytes(ordner):
    return sum(os.path.getsize(p) for p in glob.glob(os.path.join(ordner, ".git", "objects", "pack", "*.pack")))


def wachstum(tmp, name, folge):
    """[(file name, bytes of the file, growth of the pack in bytes)] for a row of files committed one after the other"""
    d = os.path.join(tmp, name)
    os.makedirs(d)
    assert os.path.abspath(d) != REPO and not os.path.exists(os.path.join(d, ".git"))
    git(d, "init", "-q")
    git(d, "config", "gc.auto", "0")
    out, vor = [], 0
    for fn, daten in folge:
        with open(os.path.join(d, fn), "wb") as f:
            f.write(daten)
        git(d, "add", "-A")
        git(d, "commit", "-q", "-m", fn)
        git(d, "repack", "-a", "-d", "-q")                 # the throwaway repository only - never the project
        n = paket_bytes(d)
        out.append((fn, len(daten), n - vor))
        vor = n
    shutil.rmtree(d, ignore_errors=True)
    return out


def main():
    tmp = tempfile.mkdtemp(prefix="mw_ablage_")
    try:
        # ---- 1: what bauen.py writes ------------------------------------------------------------------------------------
        print("1  bauen.py: Zusatzdatei ungepackt, gleich bei jedem Bau, unter den Grenzen")
        ok(bauen.ZD_GEPACKT is False, "bauen.py ZD_GEPACKT = False (daten.json ungepackt in der ZIP)")
        text, ents, v, zeilen = bauen.zusammensetzen_klein("")
        ok(len(ents) > 50, "quelle/ %s: %d Literale ausgelagert" % (v, len(ents)))
        neu = bauen.zd_bytes(v, ents, zeilen)
        ok(neu == bauen.zd_bytes(v, ents, zeilen), "zweimal gebaut: Byte für Byte gleich (%d Bytes, sha256 %s…)" % (len(neu), hashlib.sha256(neu).hexdigest()[:12]))
        with zipfile.ZipFile(io.BytesIO(neu)) as z:
            info = z.getinfo("daten.json")
            d = json.loads(z.read("daten.json").decode("utf-8"))
            ok(z.namelist() == ["daten.json"] and z.testzip() is None, "ZIP gültig, genau eine Datei daten.json")
        ok(info.compress_type == zipfile.ZIP_STORED and info.compress_size == info.file_size, "daten.json steht ungepackt in der ZIP")
        ok(str(d.get("version")) == v and len(d.get("entries") or []) == len(ents), "Inhalt: Version %s, %d Einträge" % (d.get("version"), len(d.get("entries") or [])))
        ok(len(neu) <= bauen.ZD_GRENZE < GERAETE_MAX, "Grösse %.1f MB: unter ZD_GRENZE (%d MiB) und unter der Grenze der Geräte (64 MiB)"
           % (len(neu) / 1e6, bauen.ZD_GRENZE // 1048576))
        m = re.search(r"^ZD_MAX_BYTES = (\d+) \* 1024 \* 1024", open(os.path.join(REPO, "quelle", "397_zusatzdaten_nachladen.py"), encoding="utf-8").read(), re.M)
        ok(bool(m) and int(m.group(1)) * 1048576 == GERAETE_MAX, "Teil 397: ZD_MAX_BYTES weiter 64 MiB")
        alt_json = bauen.zd_json(v, ents, zeilen).encode("utf-8")
        ok(neu == ungepackt(alt_json), "dieser Test baut die ZIP gleich wie bauen.py")

        # ---- 2: growth in a throwaway repository ------------------------------------------------------------------------
        print("2  Wachstum pro Version (Wegwerf-Repository, git repack)")
        zips = sorted((n for n in os.listdir(REPO) if re.match(r"^moveeye_daten_\d{1,3}_\d{1,3}_\d{1,3}\.zip$", n)), key=vkey)[-2:]
        folge_u, folge_g = [], []
        for n in zips:
            with zipfile.ZipFile(os.path.join(REPO, n)) as z:
                dj = z.read("daten.json")
            if json.loads(dj.decode("utf-8")).get("version") == v:
                continue                                    # the zip of the version in quelle/ comes freshly built below
            folge_u.append((n, ungepackt(dj)))
            folge_g.append((n, gepackt(dj)))
        nn = bauen.zd_name(v)
        folge_u.append((nn, neu))
        folge_g.append((nn, gepackt(alt_json)))
        ok(len(folge_u) >= 2, "mindestens eine ältere Zusatzdatei im Repository zum Vergleichen (%s)" % ", ".join(n for n, _d in folge_u))
        if len(folge_u) >= 2:
            wu = wachstum(tmp, "ungepackt", folge_u)
            wg = wachstum(tmp, "gepackt", folge_g)
            for (fn, sz, plus), (_fn, szg, plusg) in list(zip(wu, wg))[1:]:
                ok(plus <= GRENZE_MB * 1e6, "%s: +%.2f MB im Repository (Datei %.1f MB ungepackt; Grenze %.1f MB)" % (fn, plus / 1e6, sz / 1e6, GRENZE_MB))
                print("       zum Vergleich gepackt wie bisher: +%.2f MB (Datei %.1f MB)" % (plusg / 1e6, szg / 1e6))
            ok(all(g[2] > 4 * u[2] for u, g in list(zip(wu, wg))[1:]), "ungepackt wächst das Repository mindestens 4-mal weniger als gepackt")

        # ---- 3: nothing switches the comparison off ---------------------------------------------------------------------
        print("3  .gitattributes")
        attr = ""
        try:
            attr = open(os.path.join(REPO, ".gitattributes"), encoding="utf-8").read()
        except OSError:
            pass
        zeilen_ = [ln for ln in attr.splitlines() if ln.strip() and not ln.startswith("#") and re.search(r"zip|moveeye_daten", ln.split()[0])]
        ok(not any(re.search(r"(^|\s)(-delta|filter=lfs)(\s|$)", ln) for ln in zeilen_), "kein «-delta» / LFS für ZIP (%s)" % (zeilen_ or "kein Eintrag"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + ("Ablage-Test OK" if not FEHLER else "%d FEHLER:\n  - %s" % (len(FEHLER), "\n  - ".join(FEHLER))))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
