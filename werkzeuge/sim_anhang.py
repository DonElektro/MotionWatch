#!/usr/bin/env python3
"""Simulator-Anhang: Windows- und Linux-Paket des Simulators als Release-Asset (ab der Version NACH Sim 3.67.2) holen und
prüfen. Die Pakete baut der Workflow «Sim-Pakete» (.github/workflows/sim_pi.yml) und hängt sie an den Release sim-X.Y.Z;
im Repository liegen sie nicht mehr (103 MB pro Version). Das Pi-Paket desselben Releases holt weiter werkzeuge/pi_asset.py.

  python3 werkzeuge/sim_anhang.py holen X.Y.Z                # Release sim-X.Y.Z -> simulator3d/anhang/*.zip (für das Signieren)
  python3 werkzeuge/sim_anhang.py holen X.Y.Z --tag simprobe-X.Y.Z-7 --ordner /tmp/probe     # Probelauf (Vorabversion)
  python3 werkzeuge/sim_anhang.py pfad linux [--ziel DATEI]  # für Workflows / Tests: das neuste Linux-Paket dieses Stands -
                                                             # aus «anhang» in version.json (öffentlich geladen, Grösse +
                                                             # SHA-256 geprüft), sonst das Paket im Repository. Letzte Zeile = Pfad.
  python3 werkzeuge/sim_anhang.py abruf URL GROESSE SHA256   # eine Adresse genau so abrufen wie «pfad» (Probe der Umleitung)

«holen» nimmt die GitHub-REST-API (gh api, nur lesen), rechnet SHA-256 und Grösse selbst nach und vergleicht mit der
Release-Notiz (win-size / win-sha256 / linux-size / linux-sha256 / sim-ver, vom Workflow) und mit dem «digest» von GitHub;
prüft den Inhalt (Programmdatei, «Lies mich» mit NEU IN X.Y.Z, beim Linux-Paket der HP-Teil). Danach (echt):
  python3 werkzeuge/versionen.py --anhang-json X.Y.Z "Notiz"   (Block «anhang» in version.json, aus den geholten Dateien)
  python3 werkzeuge/bauen.py --nur-signieren …                 (signiert «sim.anhang» in versions.json - der Schlüssel bleibt lokal)
Die geholten ZIP kommen nie ins Repository (simulator3d/anhang/ steht in .gitignore) und dürfen nach dem Signieren weg:
make_manifest (Teil 390) behält eine schon gültige Signatur, wenn die Datei nicht mehr da ist.
Exit 0 = geholt und alles stimmt, sonst 1.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("MW_VERSIONEN_REPO") or os.path.dirname(HIER)
sys.path.insert(0, HIER)
import versionen  # noqa: E402

REPO_GH = "DonElektro/MotionWatch"
PAKETE = {"win": "MotionWatch3D_Simulator.zip", "linux": "MoveEyeSim3D_Linux.zip"}
MAX = 300 * 1024 * 1024


def gh_json(pfad):
    r = subprocess.run(["gh", "api", pfad], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise SystemExit("gh api %s: %s" % (pfad, (r.stderr or r.stdout).strip()[:300]))
    return json.loads(r.stdout)


def sha_von(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def holen(v, tag, ordner, probe, pakete):
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", v):
        raise SystemExit("Nummer %s passt nicht zu X.Y.Z" % v)
    rel = gh_json("repos/%s/releases/tags/%s" % (REPO_GH, tag))
    if rel.get("draft"):
        raise SystemExit("Release %s ist noch ein Entwurf" % tag)
    if bool(rel.get("prerelease")) != probe:
        raise SystemExit("Release %s ist %s - %s" % (tag, "eine Vorabversion" if rel.get("prerelease") else "keine Vorabversion",
                                                     "für echt nur sim-X.Y.Z ohne Vorabversion" if not probe else "Probe erwartet"))
    notiz = rel.get("body") or ""
    m_v = re.search(r"^sim-ver: (\S+)$", notiz, re.M)
    if not m_v or m_v.group(1) != v:
        raise SystemExit("Release %s: Notiz ohne «sim-ver: %s» (nicht vom Workflow «Sim-Pakete»?)" % (tag, v))
    os.makedirs(ordner, exist_ok=True)
    fehler = []
    for key in pakete:
        name = PAKETE[key]
        m_s = re.search(r"^%s-size: (\d+)$" % key, notiz, re.M)
        m_h = re.search(r"^%s-sha256: ([0-9a-f]{64})$" % key, notiz, re.M)
        a = [x for x in rel.get("assets") or [] if x.get("name") == name]
        if not (m_s and m_h) or len(a) != 1:
            fehler.append("%s: Asset %s oder %s-size / %s-sha256 in der Notiz fehlt" % (key, name, key, key))
            continue
        a = a[0]
        if a.get("state") != "uploaded" or not 0 < int(a.get("size") or 0) <= MAX:
            fehler.append("%s: Zustand %s, Grösse %s" % (name, a.get("state"), a.get("size")))
            continue
        if not probe and a.get("browser_download_url") != versionen.ANHANG_URL % (v, name):
            fehler.append("%s: Adresse %s, erwartet %s" % (name, a.get("browser_download_url"), versionen.ANHANG_URL % (v, name)))
            continue
        ziel = os.path.join(ordner, name)
        tmp = ziel + ".laden"
        with open(tmp, "wb") as f:
            r = subprocess.run(["gh", "api", "-H", "Accept: application/octet-stream", "repos/%s/releases/assets/%d" % (REPO_GH, a["id"])],
                               stdout=f, stderr=subprocess.PIPE, timeout=1800)
        if r.returncode:
            os.remove(tmp)
            fehler.append("%s: Laden fehlgeschlagen: %s" % (name, r.stderr.decode("utf-8", "replace").strip()[:200]))
            continue
        sha, size = sha_von(tmp), os.path.getsize(tmp)
        f2 = []
        if size != int(m_s.group(1)) or size != int(a["size"]):
            f2.append("Grösse %d, Notiz %s, GitHub %s" % (size, m_s.group(1), a["size"]))
        if sha != m_h.group(1):
            f2.append("SHA-256 passt nicht zur Release-Notiz")
        dg = str(a.get("digest") or "")
        if dg and dg != "sha256:" + sha:
            f2.append("SHA-256 passt nicht zum digest von GitHub")
        f2 += versionen.paket_inhalt(tmp, key, v)
        if f2:
            os.remove(tmp)
            fehler += ["%s: %s" % (name, x) for x in f2]
            continue
        os.replace(tmp, ziel)
        print("%s %s von %s: %d Bytes, sha256 %s -> %s" % (key, v, tag, size, sha, ziel))
        print("  nachgerechnet = Release-Notiz = GitHub-digest%s; Inhalt ok" % ("" if dg else " (kein digest)"))
    if fehler:
        print("PROBLEM %s:\n  - %s" % (tag, "\n  - ".join(fehler)))
        return 1
    return 0


def abruf(url, size, sha, ziel):
    """eine öffentliche Adresse laden (folgt Umleitungen wie die Geräte: urllib), Grösse und SHA-256 prüfen; nichts
    Halbes bleibt liegen. "" = gut, sonst der Grund"""
    if not url.startswith("https://"):
        return "nur https (%s)" % url[:60]
    tmp = ziel + ".laden"
    h, n = hashlib.sha256(), 0
    try:
        os.makedirs(os.path.dirname(os.path.abspath(ziel)), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "MoveEye-Sim-Anhang"})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            while True:
                b = r.read(1 << 16)
                if not b:
                    break
                n += len(b)
                if n > size + 1024:
                    raise ValueError("Datei zu gross")
                f.write(b)
                h.update(b)
        if n != size:
            raise ValueError("Grösse %d statt %d" % (n, size))
        if h.hexdigest() != sha:
            raise ValueError("Prüfsumme stimmt nicht")
        os.replace(tmp, ziel)
        return ""
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return "%s: %s" % (url, str(e)[:200])


def pfad(key, ziel):
    vj = json.load(open(os.path.join(REPO, "simulator3d", "version.json"), encoding="utf-8"))
    ah = vj.get("anhang") if isinstance(vj.get("anhang"), dict) else {}
    e = ah.get(key) if isinstance(ah.get(key), dict) else None
    im_repo = os.path.join(REPO, versionen.ZIP_REL if key == "win" else versionen.LINUX_REL)
    if not e:
        print("kein Anhang in version.json - Paket im Repository (Sim %s)" % vj.get("ver"))
        print(im_repo)
        return 0
    v = str(ah.get("ver") or "")
    if e.get("url") != versionen.ANHANG_URL % (v, PAKETE[key]) or not isinstance(e.get("size"), int) \
            or not re.fullmatch(r"[0-9a-f]{64}", str(e.get("sha256") or "")):
        print("PROBLEM: version.json «anhang.%s» unvollständig" % key)
        return 1
    ziel = ziel or os.path.join(REPO, versionen.ANHANG_REL[key])
    if os.path.isfile(ziel) and os.path.getsize(ziel) == e["size"] and sha_von(ziel) == e["sha256"]:
        print("Anhang Sim %s (%s) liegt schon da" % (v, key))
        print(ziel)
        return 0
    grund = abruf(e["url"], e["size"], e["sha256"], ziel)
    if grund:
        print("PROBLEM: Anhang Sim %s (%s) nicht geholt - %s" % (v, key, grund))
        return 1
    print("Anhang Sim %s (%s): %d Bytes, SHA-256 wie in version.json" % (v, key, e["size"]))
    print(ziel)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("holen")
    h.add_argument("ver")
    h.add_argument("--tag", default="", help="Standard sim-X.Y.Z; simprobe-… = Probelauf (Vorabversion)")
    h.add_argument("--ordner", default="", help="Ziel-Ordner (Standard simulator3d/anhang)")
    h.add_argument("--pakete", default="win,linux")
    p = sub.add_parser("pfad")
    p.add_argument("paket", choices=sorted(PAKETE))
    p.add_argument("--ziel", default="")
    b = sub.add_parser("abruf")
    b.add_argument("url")
    b.add_argument("groesse", type=int)
    b.add_argument("sha256")
    b.add_argument("--ziel", default="")
    a = ap.parse_args()
    if a.cmd == "pfad":
        return pfad(a.paket, a.ziel)
    if a.cmd == "abruf":
        import tempfile
        ziel = a.ziel or os.path.join(tempfile.mkdtemp(prefix="sim_abruf_"), "datei")
        grund = abruf(a.url, a.groesse, a.sha256, ziel)
        print("PROBLEM: " + grund if grund else "ok: %d Bytes, SHA-256 stimmt (%s)" % (a.groesse, a.url))
        if not a.ziel and os.path.isfile(ziel):
            os.remove(ziel)
        return 1 if grund else 0
    tag = a.tag or "sim-" + a.ver
    probe = tag.startswith("simprobe-")
    if not probe and tag != "sim-" + a.ver:
        raise SystemExit("Tag %s passt nicht zu %s" % (tag, a.ver))
    standard = os.path.join(REPO, "simulator3d", "anhang")
    ordner = a.ordner or standard
    if probe and os.path.abspath(ordner) == os.path.abspath(standard):
        raise SystemExit("Probelauf nie nach simulator3d/anhang (sonst könnte --anhang-json ihn eintragen) - --ordner angeben")
    pakete = [x for x in a.pakete.split(",") if x]
    if any(x not in PAKETE for x in pakete):
        raise SystemExit("--pakete: nur win, linux")
    return holen(a.ver, tag, ordner, probe, pakete)


if __name__ == "__main__":
    sys.exit(main())
