#!/usr/bin/env python3
"""Test «Was war das?» mit vergrösserten Rahmen (Teil 066, Wunsch des Besitzers 15.11.2026).

Startet MoveEye ohne Fenster (Demo-Bild) mit zwei gespeicherten Alarmbildern und schaut mit Playwright zu:

  A  vier kleine Rahmen (einer 3 % × 12 % am linken Rand): genau 3 Ausschnitte (die grössten), neben dem Bild – rechts,
     wenn Platz ist, sonst darunter (PC: rechts); dünner Rand in der Farbe des Rahmens; geschnitten aus dem Original-Alarmfoto
     in voller Auflösung (person_<zeit>.jpg, im Test grün an den Rahmen) und nicht aus dem gespeicherten Bild (dort blau);
     antippen = gross mit «✕» (Schliessen); ohne das Foto: aus dem gespeicherten Bild.
  B  ein grosser Rahmen (über einem Viertel des Bilds): kein Ausschnitt, die Karte wie bisher (Bild + Knöpfe).
  C  zuklappbar auf Live (Wunsch Besitzer 15.11.2026): ab Werk offen, Pfeil; antippen = zu, nur die Titelzeile mit der Zahl
     der offenen Alarme; ein neuer Alarm klappt sie nicht auf (Zahl + 1); neu laden: bleibt zu; «⇕» Alle aufklappen / Alle
     zuklappen / Meine Ansicht wirken auf die Karte (Bildschirmfotos waswar_offen.png / waswar_zu.png).

  python3 werkzeuge/wasdas_zoom_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos wasdas_zoom_*.png
"""
import argparse
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta

import cv2
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
FULL = (1920, 1080)                                         # the original alarm photo
STORED = (640, 360)                                         # the picture kept for «What was it?»
BOXES_A = [[0.02, 0.40, 0.03, 0.12], [0.50, 0.50, 0.05, 0.10], [0.70, 0.30, 0.04, 0.08], [0.85, 0.70, 0.02, 0.04]]
ZOOM_A = [1, 0, 2]                                          # by size; the smallest (3) is left out
BOXES_B = [[0.20, 0.10, 0.60, 0.80]]


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def bild_malen(size, boxes, farbe):
    """grey scene; every box filled with «farbe» and a fine pattern (only sharp in full resolution)"""
    w, h = size
    img = np.full((h, w, 3), 70, np.uint8)
    cv2.rectangle(img, (0, int(h * 0.8)), (w, h), (40, 90, 40), -1)
    for b in boxes:
        x0, y0, x1, y1 = int(b[0] * w), int(b[1] * h), int((b[0] + b[2]) * w), int((b[1] + b[3]) * h)
        cv2.rectangle(img, (x0, y0), (x1, y1), farbe, -1)
        for yy in range(y0, y1, 4):
            cv2.line(img, (x0, yy), (x1, yy), (255, 255, 255), 1)
    return img


def anlegen(cfg, rec):
    d = os.path.join(cfg, "alarm_labels"); os.makedirs(d); os.makedirs(rec)
    t = datetime.now()
    ids = []
    for n, (boxes, snap) in enumerate(((BOXES_A, True), (BOXES_B, False))):
        stamp = (t - timedelta(minutes=5 * n)).strftime("%Y%m%d_%H%M%S")
        ids.append(stamp)
        cv2.imwrite(os.path.join(d, stamp + ".jpg"), bild_malen(STORED, boxes, (255, 60, 0)), [cv2.IMWRITE_JPEG_QUALITY, 88])  # blue
        if snap:
            cv2.imwrite(os.path.join(rec, "person_%s.jpg" % stamp), bild_malen(FULL, boxes, (0, 220, 0)), [cv2.IMWRITE_JPEG_QUALITY, 92])  # green
        with open(os.path.join(d, stamp + ".json"), "w") as f:
            json.dump({"id": stamp, "t": time.time() - 300 * n - 60, "stamp": stamp, "kind": "person", "count": len(boxes), "boxes": boxes,
                       "label": "", "snap": "person_%s.jpg" % stamp, "src": "Test", "sim": False, "w": STORED[0], "h": STORED[1]}, f)
    return ids


class Geraet:
    """ein MoveEye ohne Fenster mit eigenem Einstellungs-Ordner und den zwei Alarmbildern"""

    def __init__(self, datei):
        self.tmp = tempfile.mkdtemp(prefix="mw_wasdas_")
        cfg = self.cfg = os.path.join(self.tmp, "mw"); os.makedirs(cfg)
        self.rec = os.path.join(self.tmp, "recordings")     # the standard «recordings» beside the working folder
        self.ids = anlegen(cfg, self.rec)
        st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
              "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "https_extra": False,
              "setup_done": True, "armed": False}       # not armed: the demo picture gives no own person alarm in between
        with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0)); self.port = sk.getsockname()[1]
        self.logf = open(os.path.join(self.tmp, "log.txt"), "w")
        self.p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(self.port), "--bind", "127.0.0.1", "--config", cfg],
                                  stdout=self.logf, stderr=subprocess.STDOUT, cwd=self.tmp)
        self.base = "http://127.0.0.1:%d" % self.port
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _i in range(240):
            if self.p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(self.tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                self.op.open(self.base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)

    def get(self, path):
        with self.op.open(self.base + path, timeout=15) as r:
            return json.loads(r.read())

    def roh(self, path):
        """(status, X-Crop-Src, picture or None)"""
        try:
            with self.op.open(self.base + path, timeout=15) as r:
                data = r.read()
                return r.status, r.headers.get("X-Crop-Src", ""), cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        except urllib.error.HTTPError as e:
            return e.code, "", None

    def zu(self):
        self.p.terminate()
        try:
            self.p.wait(15)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.logf.close()
        log = open(os.path.join(self.tmp, "log.txt"), errors="replace").read()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:]); FEHLER.append("Traceback im Protokoll von MoveEye")
        shutil.rmtree(self.tmp, ignore_errors=True)


def mitte(img):
    h, w = img.shape[:2]
    return [int(v) for v in img[h // 2 - 3:h // 2 + 3, w // 2 - 3:w // 2 + 3].reshape(-1, 3).mean(axis=0)]


def gruen(c):
    return c[1] > 150 and c[0] < 120 and c[2] < 120


def blau(c):
    return c[0] > 150 and c[1] < 140 and c[2] < 120


LAGE = """() => { const R = e => e.getBoundingClientRect(), row = document.querySelector('#alx-what .aw-i');
  if (!row) return null;
  const p = row.querySelector('.aw-p'), z = row.querySelector('.aw-z'), i = p.querySelector('i');
  const t = [...row.querySelectorAll('.aw-zc')].map(b => { const r = R(b), im = b.querySelector('img');
    return {l: r.left, t: r.top, r: r.right, b: r.bottom, h: r.height, w: r.width, src: im.getAttribute('src'), nh: im.naturalHeight,
            ok: im.complete && im.naturalWidth > 0, col: getComputedStyle(b).borderTopColor, bw: parseFloat(getComputedStyle(b).borderTopWidth)}; });
  const pr = R(p), rr = R(row);
  return {p: {l: pr.left, t: pr.top, r: pr.right, b: pr.bottom}, row: {l: rr.left, r: rr.right}, kids: row.children.length,
          z: z ? {l: R(z).left, w: R(z).width} : null, boxcol: i ? getComputedStyle(i).borderTopColor : '', tiles: t,
          over: document.documentElement.scrollWidth > window.innerWidth + 1}; }"""


def seite(br, breite, hoehe, dunkel):
    ctx = br.new_context(viewport={"width": breite, "height": hoehe}, is_mobile=breite < 600, has_touch=breite < 600, device_scale_factor=2,
                         locale="de-CH", color_scheme="dark" if dunkel else "light")
    ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-tours-seen','[\"live\"]')}catch(e){}")
    pg = ctx.new_page()
    pg.jsf = []
    pg.on("pageerror", lambda e: pg.jsf.append(str(e)[:300]))
    return ctx, pg


def karte(pg, g, ms=40000):
    """open Live and wait for «What was it?» (a banner «Platz einrichten» before it: «Später»)"""
    pg.goto(g.base + "/")
    t_ = time.time() + ms / 1000.0
    while time.time() < t_:
        if pg.evaluate("() => !!document.querySelector('#alx-what .aw-i img')"):
            pg.wait_for_timeout(1500)
            return True
        pg.evaluate("""() => { const b = [...document.querySelectorAll('#pl-offer button, #g2-bub button, .nws button, #gd-card button.ok')]
            .find(x => /Später|Überspringen|^OK$/.test(x.textContent.trim())); if (b) b.click(); }""")
        pg.wait_for_timeout(300)
    return False


def pruef_a(pg, name, pc):
    q = pg.evaluate(LAGE)
    pruef(q is not None, "%s: «Was war das?» ist da" % name)
    if q is None:
        return q
    t = q["tiles"]
    pruef(len(t) == 3, "%s: 3 Ausschnitte bei 4 kleinen Rahmen (%d)" % (name, len(t)))
    nrn = [int(x["src"].rsplit("/", 1)[1]) for x in t]
    pruef(nrn == ZOOM_A, "%s: die 3 grössten Rahmen, der grösste zuerst (%s)" % (name, nrn))
    pruef(all(x["ok"] for x in t), "%s: die Ausschnitte sind geladen" % name)
    pruef(all(abs(x["h"] - 160 - 2 * x["bw"]) < 1.5 for x in t), "%s: mindestens 160 px hoch (%s)" % (name, [round(x["h"]) for x in t]))
    pruef(all(x["nh"] >= 480 for x in t), "%s: scharf (Bild %s px hoch)" % (name, [x["nh"] for x in t]))
    pruef(all(x["col"] == q["boxcol"] and 0 < x["bw"] <= 2 for x in t),
          "%s: dünner Rand in der Farbe des Rahmens (%s / %s)" % (name, t[0]["col"], q["boxcol"]))
    z, p = q["z"], q["p"]
    rechts = all(x["l"] >= p["r"] - 0.5 and x["t"] < p["b"] for x in t)
    unten = all(x["t"] >= p["b"] - 0.5 for x in t)
    platz = p["r"] + 10 + z["w"] <= q["row"]["r"] + 0.5
    pruef(rechts if platz else unten, "%s: %s (Platz rechts: %s)" % (name, "rechts vom Bild" if platz else "unter dem Bild", platz))
    if pc is not None:
        pruef(platz == pc and (rechts if pc else unten), "%s: %s erwartet" % (name, "rechts" if pc else "unten"))
    pruef(not q["over"], "%s: nichts ragt seitlich aus der Seite" % name)
    return q


def lightbox(pg, name):
    pg.locator("#alx-what .aw-zc").first.click()
    pg.wait_for_selector("#alx-what-lb img", timeout=3000)
    pg.wait_for_timeout(500)
    q = pg.evaluate("""() => { const lb = document.getElementById('alx-what-lb'), im = lb.querySelector('img'), x = lb.querySelector('button');
        const r = im.getBoundingClientRect(), xr = x.getBoundingClientRect();
        return {h: r.height, nh: im.naturalHeight, src: im.getAttribute('src'), lab: x.getAttribute('aria-label'),
                frei: document.elementFromPoint(xr.left + xr.width / 2, xr.top + xr.height / 2) === x}; }""")
    pruef(q["nh"] >= 480 and q["h"] > 300, "%s: antippen = gross (%d px)" % (name, q["h"]))
    pruef(q["lab"] == "Schliessen" and q["frei"], "%s: Knopf «✕» mit «Schliessen», frei (%s)" % (name, q["lab"]))
    return q


FALT = """() => { const d = document.querySelector('#alx-what details.aw'); if (!d) return null; const s = d.querySelector(':scope > summary'),
  n = d.querySelector('.aw-n'), i = d.querySelector('.aw-i'), r = s.getBoundingClientRect();
  let ls = null; try { ls = localStorage.getItem('mw-open:alx-what'); } catch (e) {}
  return {open: d.open, pfeil: getComputedStyle(s, '::after').content, titel: s.firstChild.textContent, n: n ? n.textContent : '',
          nsicht: !!n && n.getClientRects().length > 0, bild: !!i && i.checkVisibility(), h: r.height, kh: d.getBoundingClientRect().height, ls: ls}; }"""


def falt_menu(pg, k):
    pg.locator("#mwb-fold").click(); pg.wait_for_timeout(200)
    pg.locator("#all-" + k).click(); pg.wait_for_timeout(600)
    return pg.evaluate(FALT)


def pruef_c(br, g, bilder):
    """C: the card folds like the other Live cards (one unanswered alarm left: B)"""
    print("C) zuklappbar (Handy 390 dunkel)", flush=True)
    ctx, pg = seite(br, 390, 844, True)
    pruef(karte(pg, g), "C: Live zeigt «Was war das?»")
    pg.evaluate("() => document.getElementById('alx-what').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(300)
    q = pg.evaluate(FALT)
    pruef(q and q["open"] and q["bild"] and "▾" in q["pfeil"] and not q["nsicht"], "C: ab Werk offen, mit Pfeil (%s)" % q)
    if bilder:
        pg.locator("#alx-what .aw").screenshot(path=os.path.join(bilder, "waswar_offen.png"))
    pg.locator("#alx-what summary").click(); pg.wait_for_timeout(400)
    q = pg.evaluate(FALT)
    n0 = int(q["n"]) if q and q["n"].isdigit() else 0
    pruef(q and not q["open"] and not q["bild"] and q["nsicht"] and n0 >= 1 and q["ls"] == "0" and "Was war das?" in q["titel"] and q["kh"] < 70,
          "C: antippen = zu, nur die Titelzeile mit der Zahl, gemerkt (%s)" % q)
    if bilder:
        pg.locator("#alx-what .aw").screenshot(path=os.path.join(bilder, "waswar_zu.png"))
    # a new unanswered alarm while collapsed: the number grows, the card stays closed
    d = os.path.join(g.cfg, "alarm_labels"); stamp = (datetime.now() + timedelta(minutes=1)).strftime("%Y%m%d_%H%M%S")
    cv2.imwrite(os.path.join(d, stamp + ".jpg"), bild_malen(STORED, BOXES_B, (255, 60, 0)))
    with open(os.path.join(d, stamp + ".json"), "w") as f:
        json.dump({"id": stamp, "t": time.time(), "stamp": stamp, "kind": "person", "count": 1, "boxes": BOXES_B, "label": "",
                   "src": "Test", "sim": False, "w": STORED[0], "h": STORED[1]}, f)
    t_ = time.time() + 30
    while time.time() < t_ and (pg.evaluate(FALT) or {}).get("n") != str(n0 + 1):
        pg.wait_for_timeout(500)
    q = pg.evaluate(FALT)
    pruef(q and q["n"] == str(n0 + 1) and not q["open"] and q["nsicht"], "C: neuer Alarm – bleibt zu, Zahl %d (%s)" % (n0 + 1, q))
    pg.reload(); pg.wait_for_selector("#alx-what details.aw", state="attached", timeout=30000); pg.wait_for_timeout(1500)
    q = pg.evaluate(FALT)
    pruef(q and not q["open"], "C: neu laden – bleibt zu (%s)" % q)
    q = falt_menu(pg, "open")
    pruef(q and q["open"], "C: «⇕» Alle aufklappen öffnet sie")
    q = falt_menu(pg, "close")
    pruef(q and not q["open"], "C: «⇕» Alle zuklappen schliesst sie")
    q = falt_menu(pg, "mine")
    pruef(q and not q["open"], "C: «⇕» Meine Ansicht – so wie selbst gelassen (zu)")
    pg.locator("#alx-what summary").click(); pg.wait_for_timeout(1500)   # open again (also kept in «My view»)
    q = pg.evaluate(FALT)
    pruef(q and q["open"] and q["ls"] == "1", "C: wieder auf (%s)" % q)
    pruef(not pg.jsf, "C: keine JavaScript-Fehler %s" % pg.jsf[:3])
    ctx.close()


def main():
    ap = argparse.ArgumentParser(description="«Was war das?» mit vergrösserten Rahmen (066)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (wasdas_zoom_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    g = Geraet(datei)
    try:
        ida, idb = g.ids
        # the server: list, crop from the full resolution photo, nothing for big boxes
        it = {m["id"]: m for m in g.get("/api/alarmlabel?n=3&lang=de")["items"]}
        pruef([z[0] for z in it[ida]["zoom"]] == ZOOM_A and it[idb]["zoom"] == [], "Liste: Ausschnitte A %s, B %s"
              % (it[ida]["zoom"], it[idb]["zoom"]))
        st, src, im = g.roh("/api/alarmlabel/crop/%s/0" % ida)
        pruef(st == 200 and src == "full" and im is not None and gruen(mitte(im)),
              "Ausschnitt aus dem Original in voller Auflösung (%s, %s, Mitte %s)" % (st, src, mitte(im) if im is not None else "-"))
        # 20 % margin on each side = 1.4 x the box: 0.03 x 0.12 of 1920 x 1080 = 58 x 130 px -> 81 x 181, narrower than 1:2 -> 91 x 181
        if im is not None:
            pruef(im.shape[0] >= 480 and abs(im.shape[1] / im.shape[0] - 0.5) < 0.03, "Seitenverhältnis und Grösse (%s)" % (im.shape[:2],))
        st, _s, _i = g.roh("/api/alarmlabel/crop/%s/3" % ida)
        pruef(st == 404, "der kleinste (vierte) Rahmen: kein Ausschnitt (%s)" % st)
        st, _s, _i = g.roh("/api/alarmlabel/crop/%s/0" % idb)
        pruef(st == 404, "grosser Rahmen: kein Ausschnitt (%s)" % st)
        st, _s, _i = g.roh("/api/alarmlabel/crop/..%2f/0")
        pruef(st == 404, "falsche Nummer: nicht gefunden (%s)" % st)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            # Live on the PC: the card stands in the narrow column beside the picture - there is no room right of it, so below
            for name, (bw, bh, dunkel, pc) in (("Handy 390 dunkel", (390, 844, True, False)), ("PC", (1280, 860, False, None))):
                print("A) %s: vier kleine Rahmen" % name, flush=True)
                ctx, pg = seite(br, bw, bh, dunkel)
                pruef(karte(pg, g), "%s: Live zeigt «Was war das?»" % name)
                pg.evaluate("() => document.getElementById('alx-what').scrollIntoView({block: 'center'})")
                pg.wait_for_timeout(400)
                pruef_a(pg, name, pc)
                if a.bilder:
                    pg.locator("#alx-what .aw").screenshot(path=os.path.join(a.bilder, "wasdas_zoom_%s.png" % ("handy" if bw < 600 else "pc")))
                    pg.screenshot(path=os.path.join(a.bilder, "wasdas_zoom_%s_seite.png" % ("handy" if bw < 600 else "pc")))
                lightbox(pg, name)
                if a.bilder:
                    pg.screenshot(path=os.path.join(a.bilder, "wasdas_zoom_%s_gross.png" % ("handy" if bw < 600 else "pc")))
                pg.locator("#alx-what-lb button").click()
                pg.wait_for_timeout(300)
                pruef(pg.evaluate("() => !document.getElementById('alx-what-lb')"), "%s: «✕» schliesst" % name)
                pg.locator("#alx-what .aw-zc").nth(1).click(); pg.wait_for_selector("#alx-what-lb", timeout=3000)
                pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
                pruef(pg.evaluate("() => !document.getElementById('alx-what-lb')"), "%s: Esc schliesst" % name)
                pruef(not pg.jsf, "%s: keine JavaScript-Fehler %s" % (name, pg.jsf[:3]))
                ctx.close()
            # a wide card (Verlauf -> Nachrichten on the PC, the same script): room on the right -> the crops right of the picture
            print("A) PC breit: Verlauf → Nachrichten", flush=True)
            ctx, pg = seite(br, 1280, 860, False)
            pg.goto(g.base + "/messages"); pg.wait_for_selector("#alx-what .aw-zc img", timeout=20000); pg.wait_for_timeout(1500)
            pruef_a(pg, "PC breit", True)
            if a.bilder:
                pg.locator("#alx-what .aw-i").first.screenshot(path=os.path.join(a.bilder, "wasdas_zoom_pc_breit.png"))
            pruef(not pg.jsf, "PC breit: keine JavaScript-Fehler %s" % pg.jsf[:3])
            ctx.close()
            # without the original photo: from the stored picture
            for f in glob.glob(os.path.join(g.rec, "person_*.jpg")):
                os.remove(f)
            st, src, im = g.roh("/api/alarmlabel/crop/%s/1" % ida)
            pruef(st == 200 and src == "stored" and im is not None and blau(mitte(im)),
                  "ohne Original-Foto: aus dem gespeicherten Bild (%s, %s, Mitte %s)" % (st, src, mitte(im) if im is not None else "-"))
            # B: answer A, the card shows the alarm with the big box - no zoom, the card as before
            print("B) grosser Rahmen", flush=True)
            ctx, pg = seite(br, 390, 844, True)
            pruef(karte(pg, g), "B: Live zeigt «Was war das?»")
            pg.locator("#alx-what .aw-b button").first.click()
            t_ = time.time() + 10
            while time.time() < t_ and not pg.evaluate("() => { const im = document.querySelector('#alx-what .aw-p img'); return !!im && im.src.indexOf('%s') > 0; }" % idb):
                pg.wait_for_timeout(200)
            pg.wait_for_timeout(800)
            q = pg.evaluate(LAGE)
            pruef(q is not None and not q["tiles"] and q["z"] is None and q["kids"] == 2,
                  "B: grosser Rahmen – kein Ausschnitt, Bild + Knöpfe wie bisher (%s)" % (q and {"tiles": len(q["tiles"]), "kids": q["kids"]}))
            if a.bilder:
                pg.locator("#alx-what .aw").screenshot(path=os.path.join(a.bilder, "wasdas_zoom_gross_kein.png"))
            pruef(g.get("/api/alarmlabel?n=3")["items"][0]["label"] == "person", "A beantwortet: «Person» gespeichert")
            pruef(not pg.jsf, "B: keine JavaScript-Fehler %s" % pg.jsf[:3])
            ctx.close()
            pruef_c(br, g, a.bilder)
            br.close()
    finally:
        g.zu()
    print("Was-war-das-Zoom-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)) + " (%.0f s)" % (time.time() - t0))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
