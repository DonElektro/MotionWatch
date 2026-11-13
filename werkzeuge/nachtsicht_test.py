#!/usr/bin/env python3
"""Test «🌙 Nachtsicht» – die Kachel schaltet die Nachtsicht wirklich aus (Fehler 3.86.1, iPhone, 13.11.2026).

Der Fehler: «Heute Nacht bewachen» (NIGHT_SET, Teil 130) schaltet «Nachtsicht automatisch» (nightvision_auto) ein und
speichert es. Die Kachel zeigte, ob die Nachtsicht läuft (STATE «nightvision»), schaltete aber nur die Hand-Einstellung
«nightvision» um - im Dunkeln blieb die Nachtsicht an, auch nach «Aus» und nach einem Neustart.

  A) im eigenen Prozess (gebaute Datei): die Hüllen um MotionWatch._lowlight_decide (Almanach 639zzt, Morse 639zzz) sind
     ohne Morse-Modus / SOS durchsichtig (gleiche Entscheidungen wie 410 über eine Dämmerung), Reihenfolge der Hüllen,
     mit laufendem Morse-Modus hält sie; nightvision_tile (Fenster) an -> aus -> an; Recht «arm» darf nightvision_auto.
  B) MoveEye ohne Fenster mit der Demo-Kamera, eigener Datenordner, Ort in der Polarnacht (immer dunkel):
     Nachtsicht aus -> «Heute Nacht bewachen» -> an (automatisch) -> «Aus» -> Kachel (das JavaScript der Seite, mit node
     gegen den laufenden Server) -> aus und bleibt aus über viele Bilder, auch nach einem Neustart; Kachel -> an -> aus.

  python3 werkzeuge/nachtsicht_test.py [--datei X.py] [--port N]
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
PASSWORT = "Nachtsicht-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


# ---------------------------------------------------------------------------------------------------- A) im Prozess
def teil_a(datei):
    print("== A) Hüllen und Kachel im Prozess", flush=True)
    os.environ["MOTIONWATCH_HOME"] = home = tempfile.mkdtemp(prefix="mw_nv_home_")
    try:
        ns = {"__name__": "mw_nachtsicht_test", "__file__": os.path.abspath(datei)}
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
        MW, CFG, STATE, MORSE = ns["MotionWatch"], ns["CFG"], ns["STATE"], ns["MORSE"]
        pruef(MW._lowlight_decide is ns["_morse_lowlight"] and ns["_morse_lowlight_410"] is ns["_alm_lowlight"],
              "Reihenfolge: Morse (639zzz) hüllt Almanach (639zzt) hüllt 410")
        base = ns["_alm_lowlight_410"]
        CFG.update(lowlight_auto=True, lowlight_threshold=60, lowlight_gap=15, lowlight_hold=30.0)
        seq, t = [], 1000.0
        for b in [120] * 50 + [x for x in range(120, 20, -1) for _ in range(6)] + [25] * 400 + [140] * 300 + [30] * 400:
            seq.append((t, float(b))); t += 0.1

        def lauf(f):
            w = object.__new__(MW); STATE["lowlight"] = False; out = []
            for t0, b in seq:
                v = f(w, b, t0); STATE["lowlight"] = v; out.append(v)
            return out
        MORSE["until"] = 0.0
        a, b = lauf(base), lauf(MW._lowlight_decide)
        pruef(a == b and any(a) and not all(a), "ohne Morse-Modus / SOS: Hüllen durchsichtig (%d Bilder, %d Wechsel)"
              % (len(a), sum(1 for i in range(1, len(a)) if a[i] != a[i - 1])))
        MORSE["until"] = time.time() + 60.0
        try:
            if ns["morse_on"]():
                w = object.__new__(MW); STATE["lowlight"] = False
                held = [MW._lowlight_decide(w, 5.0, 2000.0 + i) for i in range(50)]
                pruef(not any(held), "Morse-Modus an: die Entscheidung hält (dunkel zählt nicht)")
        finally:
            MORSE["until"] = 0.0
        pruef(not ns["morse_on"](), "Morse-Modus wieder aus")
        # the window tile
        L, NV, tile = ns["LIGHTS"], ns["NIGHTVISION"], ns.get("nightvision_tile")
        pruef(tile is not None, "Fenster: nightvision_tile (230) vorhanden")
        if tile is None:
            return ns["sun_times"]
        L["dark"] = True; L["dark_t"] = time.time() + 3600
        CFG.update(nightvision=False, nightvision_auto=True)
        gesetzt = []

        def set_(k, v):
            gesetzt.append((k, v)); CFG[k] = v
        pruef(NV.active(), "Fenster: automatisch + dunkel = Nachtsicht an")
        r = tile(set_)
        pruef(r is False and not NV.active() and not CFG["nightvision_auto"] and not CFG["nightvision"],
              "Fenster: Kachel -> aus (auch automatisch aus) %s" % gesetzt)
        pruef(not any(NV.active() for _ in range(500)), "Fenster: bleibt aus im Dunkeln")
        pruef(tile(set_) is True and CFG["nightvision"] and not CFG["nightvision_auto"], "Fenster: Kachel -> an (von Hand)")
        pruef(tile(set_) is False and not NV.active(), "Fenster: Kachel -> wieder aus")
        ra = ns["role_allows"]
        pruef(ra("custom", "/api/set", "POST", {"key": "nightvision_auto"}, perms=["arm"]) and
              ra("custom", "/api/set", "POST", {"key": "nightvision"}, perms=["arm"]),
              "Recht «arm» (ohne Einstellungen) darf beide Schlüssel der Kachel")
        sun = ns["sun_times"]
        return sun
    finally:
        shutil.rmtree(home, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------- B) Demo-Kamera
NODE_TILE = r"""
const [base, auth, jsQS, cfgJ, stJ] = process.argv.slice(1);   // node -e: argv[1] is the first argument
const post = (u, b) => fetch(base + u, {method: "POST", headers: {"Content-Type": "application/json", "Authorization": auth},
  body: JSON.stringify(b || {})});
const q = eval("(" + jsQS + ")");
(async () => { const r = await q.go(JSON.parse(cfgJ), JSON.parse(stJ));
  console.log(JSON.stringify({ok: !!(r && r.ok), status: r && r.status})); })().catch(e => { console.log(JSON.stringify({err: String(e)})); });
"""


def teil_b(datei, port, sun):
    print("== B) MoveEye mit der Demo-Kamera, immer dunkel", flush=True)
    from datetime import date
    lat = next((x for x in (89.0, -89.0) if sun(date.today(), x, 0.0) == "dark"), None)
    if lat is None:
        lat = next((x for x in (80.0, -80.0) if sun(date.today(), x, 0.0) == "dark"), 89.0)
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_nachtsicht_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "kopf_ov": "", "thermal_source": "", "thermal_on": False,
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False,
          "latitude": lat, "longitude": 0.0, "nightvision": False, "nightvision_auto": False, "arm_delay": 0}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    base = "http://127.0.0.1:%d" % port
    auth = "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode()
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    logf = open(os.path.join(tmp, "log.txt"), "a")
    P = {"p": None}

    def start():
        P["p"] = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1",
                                   "--config", cfg, "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp,
                                  env={k: v for k, v in os.environ.items() if k != "MOTIONWATCH_HOME"})
        for _i in range(300):
            if P["p"].poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                if get("/api/state")["state"].get("frames", 0) > 5:
                    return
            except Exception:
                pass
            time.sleep(1)
        sys.exit("MoveEye antwortet nicht (300 s)")

    def stop():
        p = P["p"]
        if p is None:
            return
        p.terminate()
        try:
            p.wait(20)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(10)
        P["p"] = None

    def req(path, body=None):
        r = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                   headers={"Authorization": auth, "Content-Type": "application/json"})
        with op.open(r, timeout=20) as f:
            return f.read()

    def get(path):
        return json.loads(req(path))

    def post(path, body):
        return json.loads(req(path, body))

    def warte(cond, s):
        end = time.time() + s
        while time.time() < end:
            j = get("/api/state")
            if cond(j):
                return j
            time.sleep(0.5)
        return get("/api/state")

    node = shutil.which("node")
    page = {}

    def kachel(text):
        j = get("/api/state")
        if node:
            if "js" not in page:
                html = req("/").decode("utf-8", "replace")
                m = re.search(r'\{id: "nv", ic: .*?(?=\n  \{id: )', html, re.S)     # up to the next tile
                page["js"] = m.group(0).rstrip().rstrip(",") if m else ""
                pruef(bool(page["js"]), "Seite: Kachel «nv» im JavaScript gefunden")
            out = subprocess.run([node, "-e", NODE_TILE, base, auth, page["js"], json.dumps(j["cfg"]), json.dumps(j["state"])],
                                 capture_output=True, text=True, timeout=60).stdout.strip()
            pruef('"ok":true' in out, "%s: Kachel angetippt (JavaScript der Seite, node) %s" % (text, out[-120:]))
        else:                                                  # without node: the same two steps as the page (530)
            print("  (kein node: die Schritte der Kachel in Python)")
            if not j["state"].get("nightvision"):
                post("/api/set", {"key": "nightvision", "value": True})
            else:
                if j["cfg"].get("nightvision_auto"):
                    post("/api/set", {"key": "nightvision_auto", "value": False})
                post("/api/set", {"key": "nightvision", "value": False})

    def bleibt_aus(text, sekunden):
        f0 = get("/api/state")["state"].get("frames", 0); an = 0; n = 0
        end = time.time() + sekunden
        while time.time() < end:
            j = get("/api/state"); n += 1
            an += bool(j["state"].get("nightvision"))
            time.sleep(0.5)
        f1 = j["state"].get("frames", 0)
        pruef(an == 0 and f1 - f0 >= 20 and not j["cfg"].get("nightvision") and not j["cfg"].get("nightvision_auto"),
              "%s: bleibt aus (%d Abfragen, %d Bilder, an: %d)" % (text, n, f1 - f0, an))

    try:
        start()
        j = warte(lambda j: j["state"].get("frames", 0) > 10, 30)
        pruef(not j["state"].get("nightvision"), "Start (Breite %+.0f°, dunkel): Nachtsicht aus" % lat)
        post("/api/night", {"lang": "de"})
        j = warte(lambda j: j["state"].get("nightvision"), 20)
        pruef(j["state"].get("nightvision") and j["cfg"].get("nightvision_auto") and not j["cfg"].get("nightvision"),
              "«Heute Nacht bewachen»: Nachtsicht automatisch an (wie vorgesehen)")
        post("/api/arm", {"action": "disarm"})
        j = warte(lambda j: not j["cfg"].get("armed"), 10)
        pruef(not j["cfg"].get("armed"), "Schutz «Aus»")
        kachel("Kachel 1 (an -> aus)")
        j = warte(lambda j: not j["state"].get("nightvision"), 10)
        pruef(not j["state"].get("nightvision"), "Kachel: Nachtsicht aus")
        bleibt_aus("nach der Kachel", 15)
        stop(); start()
        bleibt_aus("nach einem Neustart", 10)
        kachel("Kachel 2 (aus -> an)")
        j = warte(lambda j: j["state"].get("nightvision"), 10)
        pruef(j["state"].get("nightvision") and j["cfg"].get("nightvision") and not j["cfg"].get("nightvision_auto"),
              "Kachel: Nachtsicht an (von Hand, nicht automatisch)")
        kachel("Kachel 3 (an -> aus)")
        j = warte(lambda j: not j["state"].get("nightvision"), 10)
        bleibt_aus("nach Kachel 3", 5)
    finally:
        stop()
        logf.close()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Nachtsicht-Kachel")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5141)
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else neueste()
    print("Teste " + datei, flush=True)
    sun = teil_a(datei)
    teil_b(datei, a.port, sun)
    print("Nachtsicht-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
