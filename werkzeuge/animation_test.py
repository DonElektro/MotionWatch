#!/usr/bin/env python3
"""Test «Animationen und CPU-Chip» (Teil 639zzze).

Startet MoveEye ohne Fenster mit der Demo (eigener Ordner, freier Port) und prüft mit Playwright (iPhone 13 und PC):

  1. CPU-Chip im Live-Bild: Text «CPU 42 % · 61 °C» (oder ohne Temperatur), oben rechts im Bild, wird alle 2 s neu gemalt;
     liegt nie auf den Knöpfen im Bild (sichtbar gemacht), den Kacheln, «LIVE» oder dem Kompass; Gast-Seite hat ihn auch.
  2. Kopf-Kompass: mit Kopf (Joystick «immer») sichtbar, Schwenk 75 % -> der Pfeil steht auf +45°.
  3. Bewachen: der Punkt im Schutz-Chip atmet (Animation mwBreath); aus bei prefers-reduced-motion, beim Schalter
     «Bewegung reduzieren» (html.mwrm) und im Rotlicht (html.sxnight); ebenso das Einblenden der Seite.
  4. Warten auf das Bild: das Auge blinzelt (mwEye), der Text darunter bleibt.
  5. Keine JavaScript-Fehler.

  python3 werkzeuge/animation_test.py [--datei X.py] [--bilder ORDNER]
"""
import argparse
import base64
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

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "Anim-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


ANIM = """sel => { const e = document.querySelector(sel); if (!e) return null; const c = getComputedStyle(e, '::before'), a = getComputedStyle(e, '::after');
  return {before: c.animationName, after: a.animationName, afterBg: a.backgroundImage.slice(0, 40), main: getComputedStyle(document.querySelector('main')).animationName}; }"""
LAGE = """() => { const seen = e => { for (let n = e; n && n !== document.body; n = n.parentElement) { const c = getComputedStyle(n); if (n.hidden || c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) return false; } return true; };
  const R = e => { if (!e || !e.getClientRects().length || !seen(e)) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  const chip = R(document.getElementById('lv-cpu')), vw = R(document.querySelector('#vcard .vwrap'));
  const others = [...document.querySelectorAll('#lv-tools button, #kw-row .kw-t, .vtag, #lv-comp, #v3-mini')].map(R).filter(Boolean);
  const hit = chip ? others.filter(o => !(o[2] <= chip[0] + 0.5 || o[0] >= chip[2] - 0.5 || o[3] <= chip[1] + 0.5 || o[1] >= chip[3] - 0.5)).length : -1;
  const c = document.getElementById('lv-cpu');
  return {chip, vw, hit, text: c ? c.textContent : null, t: c ? +c.dataset.t : 0, inside: !!(chip && vw && chip[0] >= vw[0] && chip[2] <= vw[2] && chip[1] >= vw[1] && chip[3] <= vw[3])}; }"""
CHIP_RE = re.compile(r"^CPU (\d+ %|–)( · \d+ °C)?$")


def seite(pg, base, name, a):
    pg.goto(base + "/", wait_until="domcontentloaded")
    t_ = time.time() + 20
    l = None
    while time.time() < t_:
        l = pg.evaluate(LAGE)
        if l["text"]:
            break
        pg.wait_for_timeout(300)
    pruef(bool(l["text"]) and bool(CHIP_RE.match(l["text"] or "")), "%s: CPU-Chip im Live-Bild «%s»" % (name, l["text"]))
    # 3.95.0: right after loading the buttons of the live picture fade out (opacity in between counts as visible) -
    # measure again for up to 6 s; a lasting overlap stays red (on GitHub 3 of 5 runs red only in the fade)
    t_ = time.time() + 6
    while l["text"] and l["hit"] != 0 and time.time() < t_:
        pg.wait_for_timeout(400)
        l = pg.evaluate(LAGE)
    pruef(l["inside"] and l["hit"] == 0, "%s: Chip im Bild, auf nichts anderem (%s)" % (name, l))
    vw, ch = l["vw"], l["chip"]
    pruef(bool(vw and ch) and ch[2] > vw[2] - 40 and ch[1] < vw[1] + 40, "%s: Chip oben rechts im Bild" % name)
    t1 = l["t"]; pg.wait_for_timeout(4500); t2 = pg.evaluate(LAGE)["t"]
    pruef(t2 > t1 and 1500 <= (t2 - t1) <= 6000, "%s: der Chip wird alle 2 s neu gemalt (%d ms)" % (name, t2 - t1))
    pg.evaluate("document.body.classList.add('lvc-show')"); pg.wait_for_timeout(400)     # the buttons in the picture shown (639zzj)
    l2 = pg.evaluate(LAGE)
    pruef(l2["inside"] and l2["hit"] == 0, "%s: Knöpfe im Bild sichtbar - der Chip weicht aus, liegt auf nichts (%s)" % (name, l2))
    if a.bilder:
        pg.locator("#vcard").screenshot(path=os.path.join(a.bilder, "anim_%s_knoepfe.png" % name))
    pg.evaluate("document.body.classList.remove('lvc-show')")
    comp = pg.evaluate("""async () => { const j = await (await fetch('/api/state', {cache: 'no-store'})).json(); await new Promise(r => setTimeout(r, 1500));
        const j2 = await (await fetch('/api/state', {cache: 'no-store'})).json(); const k = document.getElementById('lv-comp');
        const m = k && !k.hidden && getComputedStyle(k).display !== 'none' ? /rotate\(([-\d.]+)deg\)/.exec(k.querySelector('svg').style.transform) : null;
        return {deg: m ? +m[1] : null, pan: j2.cfg.pan, range: j2.cfg.servo_range || 180}; }""")
    want = (comp["pan"] - 50) / 100 * comp["range"]
    pruef(comp["deg"] is not None and abs(comp["deg"] - want) < 3, "%s: Kompass sichtbar, folgt dem Schwenk (%s, erwartet %.1f°)" % (name, comp, want))
    an = pg.evaluate(ANIM, "#b-arm")
    pruef(an and an["before"] == "mwBreath" and an["main"] == "mwPageIn", "%s: Bewachen - der Punkt atmet, die Seite blendet ein (%s)" % (name, an))
    pg.evaluate("() => { const w = document.querySelector('#vcard .vwrap'); w.classList.add('vlost'); w.dataset.lost = 'x'; }")
    an = pg.evaluate(ANIM, "#vcard .vwrap")
    pruef(an and an["after"] == "mwEye" and "svg" in an["afterBg"], "%s: Bild kommt - das Auge blinzelt (%s)" % (name, an))
    pg.evaluate("() => document.querySelector('#vcard .vwrap').classList.remove('vlost')")
    for cls in ("mwrm", "sxnight"):
        pg.evaluate("c => document.documentElement.classList.add(c)", cls)
        an = pg.evaluate(ANIM, "#b-arm")
        pruef(an and an["before"] == "none" and an["main"] == "none", "%s: html.%s - keine Animation (%s)" % (name, cls, an))
        pg.evaluate("c => document.documentElement.classList.remove(c)", cls)
    if a.bilder:
        pg.screenshot(path=os.path.join(a.bilder, "anim_%s.png" % name))


def main():
    ap = argparse.ArgumentParser(description="Animationen und CPU-Chip")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5171)
    ap.add_argument("--bilder", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_anim_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False, "pan": 75.0, "patrol": False, "track_person": False, "track_motion": False,
          "tausch_guest": True}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        H = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode(), "Content-Type": "application/json"}
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        req = lambda path, d=None: json.loads(op.open(urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None,
                                                                              headers=H), timeout=10).read() or b"{}")
        req("/api/arm", {"action": "arm_now"})                  # guarding: the breathing dot
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            cred = {"username": "admin", "password": PASSWORT}
            init = "try{localStorage.setItem('mw-live-view','{\"joy\":\"on\"}');localStorage.setItem('mw-lang','de')}catch(e){}"
            dev = dict(pw.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            for name, kw in (("handy", dict(dev)), ("pc", {"viewport": {"width": 1280, "height": 800}})):
                ctx = br.new_context(http_credentials=cred, **kw); ctx.add_init_script(init)
                pg = ctx.new_page(); jsf = []
                pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
                seite(pg, base, name, a)
                pruef(not jsf, "%s: keine JavaScript-Fehler %s" % (name, jsf[:3]))
                ctx.close()
            # prefers-reduced-motion of the system
            ctx = br.new_context(http_credentials=cred, reduced_motion="reduce", **dict(dev)); ctx.add_init_script(init)
            pg = ctx.new_page(); pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_timeout(3000)
            an = pg.evaluate(ANIM, "#b-arm")
            pruef(an and an["before"] == "none" and an["main"] == "none", "prefers-reduced-motion: keine Animation (%s)" % an)
            pg.evaluate("() => { const w = document.querySelector('#vcard .vwrap'); w.classList.add('vlost'); }")
            an = pg.evaluate(ANIM, "#vcard .vwrap")
            pruef(an and an["after"] == "none" and "svg" in an["afterBg"], "prefers-reduced-motion: das Auge steht still, ist aber da (%s)" % an)
            ctx.close()
            # the guest page: the same chip
            req("/api/guest", {"action": "create", "hours": 1})
            g = req("/api/guest").get("path", "")
            ctx = br.new_context(**dict(dev)); pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pg.goto(base + g, wait_until="domcontentloaded")
            t_ = time.time() + 15; txt = None
            while time.time() < t_ and not txt:
                txt = pg.evaluate("() => { const c = document.getElementById('lv-cpu'); return c && !c.hidden ? c.textContent : null; }"); pg.wait_for_timeout(300)
            pruef(bool(txt) and bool(CHIP_RE.match(txt or "")), "Gast-Seite: CPU-Chip «%s»" % txt)
            pruef(not jsf, "Gast-Seite: keine JavaScript-Fehler %s" % jsf[:3])
            if a.bilder:
                pg.screenshot(path=os.path.join(a.bilder, "anim_gast.png"))
            ctx.close()
            br.close()
        if p.poll() is not None:
            FEHLER.append("MoveEye ist während des Tests abgestürzt")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("Animations-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
