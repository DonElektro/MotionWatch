#!/usr/bin/env python3
"""Musik-Vorschau (Grossvater K2, Besitzer 21.11.2026): lädt die Kandidaten aus kandidaten.json (auf dem Runner - der lokale
Proxy sperrt die Musikseiten), schneidet je 25 s Vorschau (Ogg, ein-/ausgeblendet) und schreibt LIESMICH.md mit Zustand,
Titel, Autor, Lizenz, Quelle und ob es geklappt hat. Nichts davon kommt ins Repository; ERST nach Freigabe durch den Besitzer.

    python3 werkzeuge/musik/vorschau.py <ausgabe-ordner> [--ganz]
--ganz: auch die vollen Stücke (Ogg, für den späteren Einbau) in <ausgabe>/ganz/.
"""
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) sim-musik-vorschau"}


def holen(url, ziel=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if ziel:
        with open(ziel, "wb") as f:
            f.write(data)
    return data


def oga_datei(seite, muster):
    """the first audio attachment of an OpenGameArt page whose name contains <muster>; plus the licence field"""
    h = holen(seite).decode("utf-8", "replace")
    links = re.findall(r'href="([^"]+\.(?:mp3|ogg|wav))"', h, re.I)
    links = [urllib.parse.urljoin(seite, x) for x in links]
    wahl = [x for x in links if muster.lower() in urllib.parse.unquote(x).lower()] or links
    m = re.search(r"License\(s\):.*?</div>\s*</div>", h, re.S)
    lic = re.sub(r"<[^>]+>", " ", m.group(0)) if m else ""
    lic = " ".join(html.unescape(lic).split())
    return (wahl[0] if wahl else None), lic


def dauer(p):
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                           capture_output=True, text=True, timeout=60)
        return float(o.stdout.strip())
    except Exception:
        return 0.0


def main():
    out = sys.argv[1]
    ganz = "--ganz" in sys.argv
    os.makedirs(out, exist_ok=True)
    if ganz:
        os.makedirs(os.path.join(out, "ganz"), exist_ok=True)
    K = json.load(open(os.path.join(HIER, "kandidaten.json"), encoding="utf-8"))["kandidaten"]
    if ganz:                                               # the full pieces: only the ones the owner chose
        K = [k for k in K if k.get("gewaehlt")]
    zeilen = ["# Musik-Kandidaten – Vorschau (je 25 s)", "",
              "Zur Freigabe durch den Besitzer. Lizenz: CC BY = Namensnennung (kommt in «Über» / Lizenzen des Simulators).", "",
              "| Zustand | Datei | Titel | Autor | Lizenz | Quelle | Länge | Status |", "|---|---|---|---|---|---|---|---|"]
    ok_n = 0
    for i, k in enumerate(K):
        slug = re.sub(r"[^a-z0-9]+", "_", k["titel"].lower()).strip("_")
        name = "%s_%02d_%s.ogg" % (k["zustand"], i + 1, slug)
        roh = os.path.join(out, "roh_%02d" % i)
        status = ""
        lic = k["lizenz"]
        quelle = k.get("seite", "")
        try:
            url = k.get("url")
            if not url:
                url, lic_seite = oga_datei(k["seite"], k.get("datei", ""))
                if lic_seite:
                    lic = "%s (Seite: %s)" % (k["lizenz"], lic_seite[:80])
                if not url:
                    raise RuntimeError("keine Audiodatei auf der Seite")
            holen(url, roh)
            d = dauer(roh)
            ab = float(k.get("ab", 0))
            if d and ab + 25 > d:
                ab = max(0.0, d - 25)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ab), "-t", "25", "-i", roh, "-af",
                            "afade=t=in:d=1,afade=t=out:st=23:d=2,loudnorm=I=-18:TP=-1.5", "-ac", "2", "-ar", "44100",
                            "-c:a", "libvorbis", "-q:a", "4", os.path.join(out, name)], check=True, timeout=120)
            if ganz:                                       # compact for the web: ~96 kbit/s, long pieces cut with a fade
                mx = float(k.get("max", 0)) or d
                mx = min(mx, d) if d else mx
                af = "loudnorm=I=-18:TP=-1.5"
                if d and mx < d - 1:
                    af = "afade=t=out:st=%.1f:d=4,%s" % (mx - 4, af)
                ziel = os.path.join(out, "ganz", "kit_%s.ogg" % k["zustand"])
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "%.1f" % mx, "-i", roh, "-af", af, "-ac", "2", "-ar", "44100",
                                "-c:a", "libvorbis", "-b:a", "96k", ziel], check=True, timeout=300)
            status = "ok"
            ok_n += 1
            laenge = "%d:%02d" % (int(d) // 60, int(d) % 60) if d else "?"
            quelle = "%s (Datei: %s)" % (quelle, url)
        except Exception as e:  # noqa: BLE001
            status = "FEHLT: %s" % str(e)[:80]
            laenge = ""
            name = "-"
        finally:
            if os.path.exists(roh):
                os.remove(roh)
        zeilen.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (k["zustand"], name, k["titel"], k["autor"], lic, quelle, laenge, status))
        print(k["zustand"], k["titel"], status, flush=True)
    zeilen += ["", "Lizenzen: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ · CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ ·",
               "Kevin MacLeod: https://incompetech.com/music/royalty-free/licenses/"]
    with open(os.path.join(out, "LIESMICH.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")
    print("Vorschauen: %d von %d" % (ok_n, len(K)))
    return 0 if ok_n >= min(6, len(K)) else 1


if __name__ == "__main__":
    sys.exit(main())
