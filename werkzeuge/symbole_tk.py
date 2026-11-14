#!/usr/bin/env python3
"""Die Linien-Symbole des Kopfs (Teil 639zzzc, MWI) für das Pi-Fenster: Tk kann kein SVG zeichnen - darum Alpha-Masken
20 × 20 (Chromium zeichnet das SVG, PIL liest den Alpha-Kanal), zlib + base64, geschrieben nach
quelle/639zzzd_daten_symbole_tk.py (MWI_TK). Zur Laufzeit färbt tk_icon() (639zzzc) die Maske in der Farbe des Themas.

  python3 werkzeuge/symbole_tk.py            # nach einer Änderung an MWI, dann bauen
"""
import ast
import base64
import io
import os
import zlib

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.path.join(os.path.dirname(HIER), "quelle")
N = 20


def mwi():
    src = open(os.path.join(QUELLE, "639zzzc_klar_kopf.py"), encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "MWI":
            return ast.literal_eval(node.value)
    raise SystemExit("MWI nicht gefunden")


def main():
    from PIL import Image
    from playwright.sync_api import sync_playwright
    icons, out = mwi(), {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": N, "height": N}, device_scale_factor=1)
        for k, body in icons.items():
            pg.set_content('<html><body style="margin:0;background:transparent"><svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="#000" '
                           'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">%s</svg></body></html>' % (N, N, body))
            im = Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert("RGBA")
            out[k] = base64.b64encode(zlib.compress(im.getchannel("A").tobytes(), 9)).decode()
        br.close()
    lines = ['#@ MoveEye – Teil 639zzzd: Daten – die Linien-Symbole des Kopfs für das Pi-Fenster (Alpha-Masken 20 × 20, erzeugt mit '
             'werkzeuge/symbole_tk.py aus MWI in 639zzzc). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.',
             "# Nicht von Hand ändern: python3 werkzeuge/symbole_tk.py", "MWI_TK = {"]
    lines += ['    "%s": "%s",' % (k, v) for k, v in out.items()]
    lines += ["}", ""]
    open(os.path.join(QUELLE, "639zzzd_daten_symbole_tk.py"), "w", encoding="utf-8").write("\n".join(lines))
    print("%d Symbole -> quelle/639zzzd_daten_symbole_tk.py" % len(out))


if __name__ == "__main__":
    main()
