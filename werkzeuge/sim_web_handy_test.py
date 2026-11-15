#!/usr/bin/env python3
"""Test «Browser-Demo auf dem Handy» (Besitzer 15.11.2026): ein fertiger Godot-Web-Export des Simulators in Chromium
(Playwright, WebGL 2 über SwiftShader) als Handy hoch (390 × 844) und quer (844 × 390), Pixeldichte 2.

Geprüft (über die Testbrücke ?test=1, scripts/web_bruecke.gd):
  1. die 3D-Ansicht zeichnet Körper: webdiag «objects» > 50, und ein roter Würfel 2 m vor der Kamera ist im Bild der
     Kamera zu sehen (Fehler bis Sim 3.70: ab 1000 Dingen in der Welt blieb nur Himmel und Boden - Godot sortierte im
     Browser ohne Threads alles aus; project.godot «threaded_cull_minimum_instances.web»)
  2. Handy-Modus an (handy.gd), quer = Leiste rechts
  3. Schärfe: die 3D-Ansicht in voller Auflösung bis 2× Pixeldichte (scaling_3d_scale = min(1, 2 / Pixeldichte))
  4. die Oberfläche in Punkten des Handys (390 × 844 bzw. 844 × 390)

  python3 werkzeuge/sim_web_handy_test.py --ordner EXPORTORDNER     # Ende: «Sim-Web-Handy-Test OK» (Exit 0)
Den Export macht: cd simulator3d && godot --headless --path . --export-release Web /pfad/index.html
Dauert mit SwiftShader einige Minuten (1–4 Bilder pro Sekunde). Ein echtes iPhone (WebKit) prüft das NICHT.
"""
import argparse
import functools
import http.server
import json
import sys
import threading
import time

FEHLER = []


def ok(bed, was):
    print(("  ok: " if bed else "  FEHLER: ") + was)
    if not bed:
        FEHLER.append(was)


def lauf(url, w, h, dpr, name):
    from playwright.sync_api import sync_playwright
    print("%s (%d × %d, Pixeldichte %g)" % (name, w, h, dpr))
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                                    "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr, is_mobile=True, has_touch=True)
        pg.set_default_timeout(240000)
        fehler = []
        pg.on("pageerror", lambda e: fehler.append(str(e)))
        pg.goto(url + "?test=1", wait_until="domcontentloaded")
        pg.wait_for_function("() => typeof window.mwControl === 'function'", timeout=240000)

        def ctl(d, warte=0.5):
            pg.evaluate("(s) => window.mwControl(s)", json.dumps(d))
            pg.wait_for_timeout(int(warte * 1000))
            return json.loads(pg.evaluate("() => window.mwLast"))
        pg.wait_for_timeout(25000)                       # Szene aufbauen
        d = ctl({"action": "webdiag"})
        print("   ", {k: d.get(k) for k in ("objects", "draw_calls", "scale3d", "window", "content_scale", "dpr", "fps")})
        ok(int(d.get("objects", 0)) > 50, "%s: 3D zeichnet Körper (%s Dinge im Bild)" % (name, d.get("objects")))
        ok(abs(float(d.get("scale3d", 0)) - min(1.0, 2.0 / dpr)) < 0.02, "%s: 3D-Ansicht scharf (%.2f)" % (name, float(d.get("scale3d", 0))))
        pg.evaluate("(s) => window.mwControl(s)", json.dumps({"action": "webbisect", "nur_probe": True}))
        t0 = time.time()
        txt = ""
        while time.time() - t0 < 120:
            pg.wait_for_timeout(2000)
            txt = pg.evaluate("() => window.mwProbe || ''")
            if txt:
                break
        ok(txt == "true", "%s: roter Würfel vor der Kamera zu sehen (%s)" % (name, txt or "keine Antwort"))
        hd = ctl({"action": "handy", "do": "info"})
        ok(bool(hd.get("on")), "%s: Handy-Modus an" % name)
        ok(bool(hd.get("landscape")) == (w > h), "%s: Leiste %s" % (name, "rechts" if w > h else "unten"))
        ok([round(x) for x in hd.get("view", [0, 0])] == [w, h], "%s: Oberfläche in Punkten %s" % (name, hd.get("view")))
        hd = ctl({"action": "handy", "do": "sheet", "id": "scene"}, 3)
        ok(hd.get("sheet") == "scene", "%s: Blatt «Szene» offen" % name)
        ctl({"action": "handy", "do": "close"})
        ok(not fehler, "%s: keine JavaScript-Fehler %s" % (name, fehler[:2]))
        b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", required=True, help="Godot-Web-Export (index.html, index.wasm, index.pck …)")
    ap.add_argument("--nur", choices=["hoch", "quer"])
    a = ap.parse_args()
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.ordner)
    h.log_message = lambda *x: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/index.html" % srv.server_address[1]
    if a.nur in (None, "hoch"):
        lauf(url, 390, 844, 2, "hoch")
    if a.nur in (None, "quer"):
        lauf(url, 844, 390, 2, "quer")
    srv.shutdown()
    if FEHLER:
        print("Sim-Web-Handy-Test: %d Fehler" % len(FEHLER))
        sys.exit(1)
    print("Sim-Web-Handy-Test OK")


if __name__ == "__main__":
    main()
