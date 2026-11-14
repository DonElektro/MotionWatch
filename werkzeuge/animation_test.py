#!/usr/bin/env python3
"""Test «Animationen und CPU-Chip» (Teil 639zzze).

Startet MoveEye ohne Fenster mit der Demo (eigener Ordner, freier Port) und prüft mit Playwright (iPhone 13 und PC):

  1. CPU- und Akku-Chip in der Kopfzeile der Karte «Bedienung» (nicht mehr im Bild): «CPU 42 % · 61 °C» und «🔋 82 %» /
     «🔌 97 %», rechts vom Titel, links vom ▾, alle 2 s neu gemalt, auch bei zugeklappter Karte sichtbar; Farben (CPU ab 70 / 85,
     Akku unter 30 / 15 %), kein Akku = kein Chip; eng (390 px, langer Titel) = «· °C» fällt weg, der Titel bricht nie um;
     nach dem Sprachwechsel wieder da. Wer die Karte nicht sieht (Zuschauer: body.role-view): die Chips rechts in der
     Statuszeile oben, ganz sichtbar (wie 041: die Karte per CSS ausgeblendet). Gast-Seite: die Chips in der oberen Zeile.
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
LAGE = """() => { const su = document.querySelector('details[data-view="controls"]>summary'), k = document.getElementById('lv-chips'), c = document.getElementById('lv-cpu'),
    b = document.getElementById('lv-batt'), R = e => e && e.getClientRects().length ? e.getBoundingClientRect().toJSON() : null;
  const tn = su ? [...su.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()) : [], rg = document.createRange();
  let lines = 0, tright = 0; if (tn.length) { rg.setStart(tn[0], 0); rg.setEnd(tn[tn.length - 1], tn[tn.length - 1].length); const q = [...rg.getClientRects()]; lines = q.length; tright = Math.max(...q.map(x => x.right)); }
  const s = R(su), kr = R(k), a = su ? getComputedStyle(su, '::after') : null;
  const cs = e => e && getComputedStyle(e);
  return {in_sum: !!(k && su && k.parentNode === su), in_pic: !!document.querySelector('.vwrap #lv-cpu, .vwrap #lv-chips'), lines, sum: s, chips: kr,
    right_of_title: !!(kr && kr.left >= tright + 4), left_of_arrow: !!(kr && s && kr.right <= s.right - 8), arrow: a ? a.content : null,
    text: c && !c.hidden ? c.textContent : null, temp_shown: !!(c && c.lastChild && cs(c.lastChild).display !== 'none' && c.lastChild.textContent),
    nc: !!(k && k.classList.contains('nc')), cls: c ? c.className : '', t: c ? +c.dataset.t : 0,
    batt: b && !b.hidden && cs(b).display !== 'none' ? b.textContent : null, bcls: b ? b.className : '', open: !!(su && su.parentNode.open)}; }"""
CHIP_RE = re.compile(r"^CPU (\d+ %|–)( · \d+ °C)?$")
PAINT = "s => window.mwAnim({force: 1, state: s})"


def seite(pg, base, name, a):
    pg.goto(base + "/", wait_until="domcontentloaded")
    t_ = time.time() + 20
    l = None
    while time.time() < t_:
        l = pg.evaluate(LAGE)
        if l["text"]:
            break
        pg.wait_for_timeout(300)
    pruef(bool(l["text"]) and bool(CHIP_RE.match(l["text"] or "")), "%s: CPU-Chip «%s»" % (name, l["text"]))
    pruef(l["in_sum"] and not l["in_pic"], "%s: die Chips sind in der Kopfzeile «Bedienung», nicht im Bild" % name)
    pruef(l["lines"] == 1 and l["right_of_title"] and l["left_of_arrow"], "%s: rechts vom Titel, links vom ▾, der Titel in einer Zeile (%s)" % (name, l))
    t1 = l["t"]; pg.wait_for_timeout(4500); t2 = pg.evaluate(LAGE)["t"]
    pruef(t2 > t1 and 1500 <= (t2 - t1) <= 6000, "%s: die Chips werden alle 2 s neu gemalt (%d ms)" % (name, t2 - t1))
    # the states (the demo has no battery and no temperature: painted directly, as the page does with /api/state)
    for st, want, bwant, cc, bc in (({"cpu": 42.4, "cpu_temp": 61.2, "battery": {"on": True, "pct": 82}}, "CPU 42 % · 61 °C", "🔋 82 %", "", ""),
                                    ({"cpu": 71, "cpu_temp": 50, "battery": {"on": True, "pct": 29}}, "CPU 71 % · 50 °C", "🔋 29 %", "warn", "warn"),
                                    ({"cpu": 50, "cpu_temp": 81, "battery": {"on": True, "pct": 14}}, "CPU 50 % · 81 °C", "🔋 14 %", "hot", "hot"),
                                    ({"cpu": 86, "battery": {"on": True, "pct": 97, "src": "ups", "on_battery": False}}, "CPU 86 %", "🔌 97 %", "hot", ""),
                                    ({"cpu": 30, "battery": {"on": True, "pct": 10, "charging": True}}, "CPU 30 %", "🔌 10 %", "", ""),
                                    ({"cpu": 30, "battery": {"on": False}}, "CPU 30 %", None, "", None)):
        pg.evaluate(PAINT, st); l = pg.evaluate(LAGE)
        lv = lambda cls: "hot" if " hot" in cls else ("warn" if " warn" in cls else "")
        txt_ok = l["text"] == want or (l["nc"] and l["text"] and want.startswith(l["text"].split(" · ")[0]))
        pruef(txt_ok and l["batt"] == bwant and lv(l["cls"]) == cc and (bc is None or lv(l["bcls"]) == bc) and l["lines"] == 1,
              "%s: %s -> «%s» «%s» %s/%s, eine Zeile" % (name, json.dumps(st, ensure_ascii=False), l["text"], l["batt"], l["cls"], l["bcls"]))
    pg.evaluate(PAINT, {"cpu": 57, "cpu_temp": 67, "battery": {"on": True, "pct": 82}})
    l = pg.evaluate(LAGE)
    pruef(l["temp_shown"] == (not l["nc"]) and l["lines"] == 1 and l["left_of_arrow"], "%s: mit Temperatur und Akku passt es (°C %s)" % (name, "weg" if l["nc"] else "da"))
    if a.bilder:
        pg.locator('details[data-view="controls"]').screenshot(path=os.path.join(a.bilder, "chips_%s_offen.png" % name))
    pg.locator('details[data-view="controls"]>summary').click(); pg.wait_for_timeout(400)
    l = pg.evaluate(LAGE)
    pruef(not l["open"] and l["batt"] == "🔋 82 %" and bool(l["text"]), "%s: Karte zu - die Chips bleiben sichtbar (%s / %s)" % (name, l["text"], l["batt"]))
    if a.bilder:
        pg.locator('details[data-view="controls"]').screenshot(path=os.path.join(a.bilder, "chips_%s_zu.png" % name))
    pg.locator('details[data-view="controls"]>summary').click(); pg.wait_for_timeout(300)
    # tight: a long title - «· °C» goes first, the title stays in one line
    pg.evaluate("() => { const su = document.querySelector('details[data-view=\"controls\"]>summary'); su.dataset.keep = su.firstChild.textContent; su.firstChild.textContent = 'Bedienung und Ka'; }")
    pg.evaluate(PAINT, {"cpu": 57, "cpu_temp": 67, "battery": {"on": True, "pct": 82}}); l = pg.evaluate(LAGE)
    pruef(l["nc"] and not l["temp_shown"] and l["lines"] == 1, "%s: eng - «· °C» fällt weg, der Titel bleibt in einer Zeile (%s)" % (name, l))
    pg.evaluate("() => { const su = document.querySelector('details[data-view=\"controls\"]>summary'); su.firstChild.textContent = su.dataset.keep; }")
    # a viewer (no card «Controls»): the chips go right into the status line at the top
    pg.evaluate("() => { const s = document.createElement('style'); s.id = 't-view'; s.textContent = 'details[data-view=\"controls\"]{display:none!important}'; document.head.appendChild(s); }")
    pg.wait_for_timeout(2400)
    v = pg.evaluate("""() => { const k = document.getElementById('lv-chips'), h = document.querySelector('header>.chips'); const r = k && k.getBoundingClientRect(), hr = h && h.getBoundingClientRect();
        const e = r && document.elementFromPoint(r.left + 4, r.top + r.height / 2);
        return {in_header: !!(k && k.parentNode === h), alt: !!(k && k.classList.contains('alt')), text: (document.getElementById('lv-cpu') || {}).textContent,
                inside: !!(r && hr && r.width > 20 && r.left >= hr.left - 1 && r.right <= Math.min(hr.right, innerWidth) + 1), right: !!(r && hr && hr.right - r.right < 30),
                top: !!(e && k.contains(e)), card: !!document.querySelector('details[data-view="controls"]>summary').getClientRects().length}; }""")
    pruef(v["in_header"] and v["alt"] and v["inside"] and v["right"] and v["top"] and not v["card"] and bool(v["text"]),
          "%s: Zuschauer ohne Karte «Bedienung» - die Chips rechts in der Statuszeile, ganz sichtbar (%s)" % (name, v))
    if a.bilder:
        pg.screenshot(path=os.path.join(a.bilder, "chips_%s_zuschauer.png" % name))
    pg.evaluate("() => document.getElementById('t-view').remove()"); pg.wait_for_timeout(2400)
    pruef(pg.evaluate(LAGE)["in_sum"], "%s: Karte wieder sichtbar - die Chips zurück in «Bedienung»" % name)
    pg.evaluate("() => langSet('fr')"); pg.wait_for_timeout(2600); l = pg.evaluate(LAGE)
    pruef(l["in_sum"] and bool(l["text"]) and l["lines"] == 1, "%s: nach dem Sprachwechsel (fr) sind die Chips wieder da (%s)" % (name, l["text"]))
    pg.evaluate("() => langSet('de')"); pg.wait_for_timeout(800)
    for _try in range(4):                                     # the head may still be on its way to 75 %
      comp = pg.evaluate(r"""async () => { const j = await (await fetch('/api/state', {cache: 'no-store'})).json(); await new Promise(r => setTimeout(r, 1500));
        const j2 = await (await fetch('/api/state', {cache: 'no-store'})).json(); const k = document.getElementById('lv-comp');
        const m = k && !k.hidden && getComputedStyle(k).display !== 'none' ? /rotate\(([-\d.]+)deg\)/.exec(k.querySelector('svg').style.transform) : null;
        return {deg: m ? +m[1] : null, pan: j2.cfg.pan, range: j2.cfg.servo_range || 180}; }""")
      want = (comp["pan"] - 50) / 100 * comp["range"]
      if comp["deg"] is not None and abs(comp["deg"] - want) < 3:
          break
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
            # the guest page: the same chips in the top row
            req("/api/guest", {"action": "create", "hours": 1})
            g = req("/api/guest").get("path", "")
            ctx = br.new_context(**dict(dev)); pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pg.goto(base + g, wait_until="domcontentloaded")
            t_ = time.time() + 15; txt = None
            while time.time() < t_ and not txt:
                txt = pg.evaluate("() => { const c = document.getElementById('lv-cpu'); return c && !c.hidden ? c.textContent : null; }"); pg.wait_for_timeout(300)
            pruef(bool(txt) and bool(CHIP_RE.match(txt or "")), "Gast-Seite: CPU-Chip «%s»" % txt)
            g2 = pg.evaluate("""() => { gAnim({cpu: 57, cpu_temp: 67, battery: {on: true, pct: 12}}); const k = document.getElementById('lv-chips'), t = document.querySelector('.gtop');
                return {top: !!(k && k.parentNode === t), pic: !!document.querySelector('.vwrap #lv-cpu'), batt: document.getElementById('lv-batt').textContent,
                        hot: document.getElementById('lv-batt').classList.contains('hot'), over: t.scrollWidth > t.clientWidth + 1,
                        title1: (() => { const h = document.querySelector('.gtop .gtt'); return h.getClientRects().length === 1 && h.offsetHeight < 30; })()}; }""")
            pruef(g2["top"] and not g2["pic"] and g2["batt"] == "🔋 12 %" and g2["hot"] and not g2["over"] and g2["title1"],
                  "Gast-Seite: Chips oben (am Handy eine eigene kurze Zeile), Akku rot unter 15 %%, der Titel in einer Zeile (%s)" % g2)
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
