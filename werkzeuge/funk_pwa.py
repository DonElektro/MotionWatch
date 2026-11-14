#!/usr/bin/env python3
"""Die Seite «Handy-Funkgerät» als PWA für GitHub Pages (Ordner funk/): eine HTML-Datei, Manifest, Service Worker, Symbole.

Quelle ist FUNK_PAGE in quelle/639zzzf_funk.py (dieselbe Seite, die MoveEye unter /morse/funk zeigt) - funk/ nie von Hand ändern.
Keine Anfragen nach aussen, keine Schlüssel, keine persönlichen Daten. Nach dem ersten Laden geht die Seite ohne Internet
(Service Worker: zuerst aus dem Speicher). Veröffentlicht vom Workflow .github/workflows/funk_pages.yml.

  python3 werkzeuge/funk_pwa.py            # funk/ neu schreiben
  python3 werkzeuge/funk_pwa.py --pruefen  # passt funk/ zu quelle/? (Test, CI)
"""
import ast
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(REPO, "quelle", "639zzzf_funk.py")
ZIEL = os.path.join(REPO, "funk")


def seite():
    tree = ast.parse(open(QUELLE, encoding="utf-8").read())
    for st in tree.body:
        if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FUNK_PAGE" for t in st.targets):
            return st.value.value
    raise SystemExit("FUNK_PAGE nicht gefunden")


def symbol(n):
    """das Symbol: dunkler Grund, oranger Kreis, Funkwellen (gezeichnet, gleich bei jedem Lauf)"""
    import cv2
    import numpy as np
    k = 4                                                     # gross zeichnen, dann verkleinern (glatte Kanten)
    m = n * k
    img = np.zeros((m, m, 3), np.uint8); img[:] = (0x18, 0x14, 0x11)
    c = (m // 2, int(m * 0.56))
    cv2.circle(img, c, int(m * 0.30), (0x3a, 0xa3, 0xf2), -1, cv2.LINE_AA)
    cv2.circle(img, c, int(m * 0.09), (0x18, 0x14, 0x11), -1, cv2.LINE_AA)
    for r in (0.18, 0.25):
        cv2.ellipse(img, c, (int(m * r), int(m * r)), 0, 215, 325, (0x18, 0x14, 0x11), int(m * 0.035), cv2.LINE_AA)
    for r in (0.36, 0.44):
        cv2.ellipse(img, c, (int(m * r), int(m * r)), 0, 220, 320, (0xff, 0xa9, 0x5a), int(m * 0.03), cv2.LINE_AA)
    img = cv2.resize(img, (n, n), interpolation=cv2.INTER_AREA)
    ok, png = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return png.tobytes()


def dateien():
    html = seite()
    assert "window.MW_FUNK=" not in html and "/*MWFUNK*/" in html
    ver = hashlib.sha256(html.encode("utf-8")).hexdigest()[:12]
    manifest = {"name": "Handy-Funkgerät", "short_name": "Funk", "description": "Morse und das eigene Protokoll mit zwei Tönen über ein Handfunkgerät (MoveEye)",
                "lang": "de", "start_url": "./", "scope": "./", "display": "standalone", "background_color": "#111418", "theme_color": "#111418",
                "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                          {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}
    teile = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"]
    sw = ("// Service Worker der Seite «Handy-Funkgerät» (erzeugt von werkzeuge/funk_pwa.py): alles aus dem Speicher, damit die Seite\n"
          "// nach dem ersten Laden ohne Internet geht. Eine neue Seite = ein neuer Name des Speichers (die alte wird gelöscht).\n"
          "const C = 'funk-" + ver + "';\n"
          "const TEILE = " + json.dumps(teile) + ";\n"
          "self.addEventListener('install', e => { e.waitUntil(caches.open(C).then(c => c.addAll(TEILE)).then(() => self.skipWaiting())); });\n"
          "self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k))))\n"
          "  .then(() => self.clients.claim())); });\n"
          "self.addEventListener('fetch', e => {\n"
          "  const r = e.request; if (r.method !== 'GET' || new URL(r.url).origin !== self.location.origin) return;\n"
          "  e.respondWith(caches.match(r, {ignoreSearch: true}).then(h => h || fetch(r).catch(() => r.mode === 'navigate' ? caches.match('index.html') : Response.error())));\n"
          "});\n")
    return {"index.html": html.encode("utf-8"), "manifest.webmanifest": (json.dumps(manifest, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
            "sw.js": sw.encode("utf-8"), "icon-192.png": symbol(192), "icon-512.png": symbol(512), "apple-touch-icon.png": symbol(180)}


def main():
    pruefen = "--pruefen" in sys.argv
    falsch = []
    for name, data in dateien().items():
        p = os.path.join(ZIEL, name)
        alt = open(p, "rb").read() if os.path.exists(p) else None
        if pruefen:
            if alt != data:
                falsch.append(name)
        elif alt != data:
            os.makedirs(ZIEL, exist_ok=True)
            open(p, "wb").write(data)
            print("geschrieben:", os.path.relpath(p, REPO))
    if pruefen:
        print("funk/ passt zu quelle/" if not falsch else "funk/ veraltet: " + ", ".join(falsch) + " - python3 werkzeuge/funk_pwa.py")
        return 1 if falsch else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
