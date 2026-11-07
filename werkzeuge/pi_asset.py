#!/usr/bin/env python3
"""Pi-Paket (Sim 3.57.0+, «Simulator intern», Teil 639zx) vom Release holen und prüfen - Schritt 3 nach dem Workflow
«Pi-Paket» (.github/workflows/sim_pi.yml).

  python3 werkzeuge/pi_asset.py holen X.Y.Z                 # Release sim-X.Y.Z -> simulator3d/MoveEyeSim3D_Pi.zip
  python3 werkzeuge/pi_asset.py holen X.Y.Z --tag simprobe-X.Y.Z-7 --aus /tmp/probe.zip   # Probelauf (Vorabversion)

Holt das Asset MoveEyeSim3D_Pi.zip über die GitHub-REST-API (gh api, nur lesen), rechnet SHA-256 und Grösse selbst nach und
vergleicht mit der Release-Notiz (pi-size / pi-sha256, vom Workflow) und mit dem «digest» von GitHub. Prüft den Inhalt
(arm64-ELF ausführbar, installieren.sh, «Lies mich» mit NEU IN X.Y.Z, kein hp/). Danach (echt):
  python3 werkzeuge/versionen.py --pi-json        (Block «pi» in version.json, aus der eben geholten Datei)
  python3 werkzeuge/bauen.py --nur-signieren …    (signiert «sim.pi» in versions.json - der Schlüssel bleibt lokal)
Beides macht `PI_NUR=1 rel_sim.sh X.Y.Z` in einem Zug. Die ZIP selbst kommt nie ins Repository (.gitignore).
Exit 0 = geholt und alles stimmt, sonst 1.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile

REPO_GH = "DonElektro/MotionWatch"
ASSET = "MoveEyeSim3D_Pi.zip"
HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("MW_VERSIONEN_REPO") or os.path.dirname(HIER)
PI_REL = "simulator3d/MoveEyeSim3D_Pi.zip"
PI_URL = "https://github.com/%s/releases/download/sim-%%s/%s" % (REPO_GH, ASSET)
MAX = 200 * 1024 * 1024


def gh_json(pfad):
    r = subprocess.run(["gh", "api", pfad], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise SystemExit("gh api %s: %s" % (pfad, (r.stderr or r.stdout).strip()[:300]))
    return json.loads(r.stdout)


def inhalt_pruefen(p, v):
    """Fehlerliste (leer = ok)"""
    out = []
    try:
        with zipfile.ZipFile(p) as z:
            n = z.namelist()
            if z.testzip() is not None:
                out.append("ZIP beschädigt")
            lies = z.read("MoveEyeSim3D/Lies mich.txt").decode("utf-8", "replace")
            b = z.read("MoveEyeSim3D/MoveEyeSim3D.arm64")[:20]
            mode = (z.getinfo("MoveEyeSim3D/MoveEyeSim3D.arm64").external_attr >> 16) & 0o777
    except (KeyError, zipfile.BadZipFile, OSError) as e:
        return ["kein Pi-Paket (%s)" % e]
    if "MoveEyeSim3D/installieren.sh" not in n:
        out.append("installieren.sh fehlt")
    if any(x.startswith("MoveEyeSim3D/hp/") for x in n):
        out.append("enthält hp/ (gehört nur zum Simulator-PC)")
    if not (b[:6] == b"\x7fELF\x02\x01" and b[18:20] == b"\xb7\x00"):
        out.append("MoveEyeSim3D.arm64 ist keine arm64-ELF-Datei")
    if not mode & 0o100:
        out.append("MoveEyeSim3D.arm64 nicht ausführbar")
    if "NEU IN %s\n" % v not in lies:
        out.append("«Lies mich» ohne NEU IN %s" % v)
    return out


def holen(v, tag, aus, probe):
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", v):
        raise SystemExit("Nummer %s passt nicht zu X.Y.Z" % v)
    rel = gh_json("repos/%s/releases/tags/%s" % (REPO_GH, tag))
    if rel.get("draft"):
        raise SystemExit("Release %s ist noch ein Entwurf" % tag)
    if bool(rel.get("prerelease")) != probe:
        raise SystemExit("Release %s ist %s - %s" % (tag, "eine Vorabversion" if rel.get("prerelease") else "keine Vorabversion",
                                                     "für echt nur sim-X.Y.Z ohne Vorabversion" if not probe else "Probe erwartet"))
    notiz = rel.get("body") or ""
    m_v = re.search(r"^pi-ver: (\S+)$", notiz, re.M)
    m_s = re.search(r"^pi-size: (\d+)$", notiz, re.M)
    m_h = re.search(r"^pi-sha256: ([0-9a-f]{64})$", notiz, re.M)
    if not (m_v and m_s and m_h):
        raise SystemExit("Release-Notiz von %s ohne pi-ver / pi-size / pi-sha256 (nicht vom Workflow «Pi-Paket»?)" % tag)
    if m_v.group(1) != v:
        raise SystemExit("Release %s ist für %s, nicht %s" % (tag, m_v.group(1), v))
    a = [x for x in rel.get("assets") or [] if x.get("name") == ASSET]
    if len(a) != 1:
        raise SystemExit("Release %s: Asset %s fehlt" % (tag, ASSET))
    a = a[0]
    if a.get("state") != "uploaded" or not 0 < int(a.get("size") or 0) <= MAX:
        raise SystemExit("Asset %s: Zustand %s, Grösse %s" % (ASSET, a.get("state"), a.get("size")))
    if not probe and a.get("browser_download_url") != PI_URL % v:
        raise SystemExit("Asset-Adresse %s, erwartet %s" % (a.get("browser_download_url"), PI_URL % v))
    tmp = aus + ".laden"
    with open(tmp, "wb") as f:
        r = subprocess.run(["gh", "api", "-H", "Accept: application/octet-stream",
                            "repos/%s/releases/assets/%d" % (REPO_GH, a["id"])], stdout=f, stderr=subprocess.PIPE, timeout=900)
    if r.returncode:
        os.remove(tmp)
        raise SystemExit("Laden fehlgeschlagen: %s" % r.stderr.decode("utf-8", "replace").strip()[:300])
    data = open(tmp, "rb").read()
    sha, size = hashlib.sha256(data).hexdigest(), len(data)
    fehler = []
    if size != int(m_s.group(1)) or size != int(a["size"]):
        fehler.append("Grösse %d, Notiz %s, GitHub %s" % (size, m_s.group(1), a["size"]))
    if sha != m_h.group(1):
        fehler.append("SHA-256 passt nicht zur Release-Notiz")
    dg = str(a.get("digest") or "")
    if dg and dg != "sha256:" + sha:
        fehler.append("SHA-256 passt nicht zum digest von GitHub (%s)" % dg[:20])
    fehler += inhalt_pruefen(tmp, v)
    if fehler:
        os.remove(tmp)
        print("PROBLEM %s:\n  - %s" % (tag, "\n  - ".join(fehler)))
        return 1
    os.replace(tmp, aus)
    print("Pi-Paket %s von %s: %d Bytes, sha256 %s -> %s" % (v, tag, size, sha, aus))
    print("  nachgerechnet = Release-Notiz = GitHub-digest%s; Inhalt arm64 ok" % ("" if dg else " (kein digest)"))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("holen")
    h.add_argument("ver")
    h.add_argument("--tag", default="", help="Standard sim-X.Y.Z; simprobe-… = Probelauf (Vorabversion)")
    h.add_argument("--aus", default="", help="Ziel (Standard %s)" % PI_REL)
    a = ap.parse_args()
    tag = a.tag or "sim-" + a.ver
    probe = tag.startswith("simprobe-")
    if not probe and tag != "sim-" + a.ver:
        raise SystemExit("Tag %s passt nicht zu %s" % (tag, a.ver))
    aus = a.aus or os.path.join(REPO, PI_REL)
    if probe and os.path.abspath(aus) == os.path.abspath(os.path.join(REPO, PI_REL)):
        raise SystemExit("Probelauf nie nach %s (sonst könnte versionen.py --pi-json ihn eintragen) - --aus angeben" % PI_REL)
    return holen(a.ver, tag, aus, probe)


if __name__ == "__main__":
    sys.exit(main())
