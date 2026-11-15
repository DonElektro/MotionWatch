#!/usr/bin/env python3
"""«Blinki fragen» am echten Pi messen (für den Besitzer, freiwillig) – wie schnell, wie heiss, wie gut auf Deutsch.

Startet llama-server genau wie MoveEye (nur 127.0.0.1, nice 15, -t N, -np 1) mit dem geladenen Modell und stellt einen
deutschen Fragenkatalog – mit denselben Vorgaben und Textstellen der Anleitung wie MoveEye (die gebaute Datei wird geladen,
nur gelesen). Pro Frage: Zeit bis zum ersten Wort, ganze Zeit, Wörter-Stücke pro Sekunde, Temperatur, Drosselung, Speicher.
Mit --url (und --passwort) wird nebenher gemessen, wie viele Bilder/s MoveEye in Ruhe und während Blinki schreibt schafft.
Die Antworten stehen im Bericht – bitte lesen und benoten (Deutsch, richtig, hilfreich). Bericht: feedback/ki_messung_*.md/.json.

  python3 werkzeuge/ki_messen.py [--kerne 2,4] [--url http://127.0.0.1:8080 --passwort …] [--fragen 10]

Läuft MoveEye mit eigenem Blinki-Motor, vorher in MoveEye «Blinki» ruhen lassen (sonst rechnen zwei Modelle gleichzeitig).
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
FRAGEN = ["Wie laut ist die Sirene und wo stelle ich das ein?", "Was macht der Klatschschalter?", "Wie richte ich Push-Nachrichten mit ntfy ein?",
          "Warum gibt es nachts Fehlalarme und was hilft dagegen?", "Wie lade ich die Piper-Stimme?", "Was ist der Unterschied zwischen Wachsam und Voll?",
          "Wie schalte ich den Zeitraffer ein?", "Wie verbinde ich ein zweites MoveEye?", "Was bedeutet die violette LED?", "Wie mache ich ein Backup der Einstellungen?",
          "Kann ich MoveEye ohne Internet benutzen?", "Wie stelle ich den Wecker?"]


def mw_laden(datei):
    """the built MoveEye file (read only, temporary data folder): for the same prompts as on the device"""
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_kimess_")
    src = open(datei, encoding="utf-8").read()
    i = src.rfind('\nif __name__ == "__main__":')
    ns = {"__name__": "mw_ki_messen", "__file__": datei}
    exec(compile(src[:i], datei, "exec"), ns)
    return ns


def temp_c():
    try:
        return int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000.0
    except (OSError, ValueError):
        return None


def gedrosselt():
    if not shutil.which("vcgencmd"):
        return None
    try:
        return subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def rss_mb(pid):
    try:
        for line in open("/proc/%d/status" % pid):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) // 1024
    except OSError:
        pass
    return None


def fps(url, pw):
    if not url:
        return None
    h = {"Authorization": "Basic " + base64.b64encode(("admin:" + (pw or "")).encode()).decode()} if pw else {}
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(urllib.request.Request(url.rstrip("/") + "/api/state", headers=h), timeout=5) as r:
            return float(json.loads(r.read()).get("fps") or 0)
    except Exception:
        return None


def frage(port, msgs, url, pw):
    body = json.dumps({"messages": msgs, "stream": True, "max_tokens": 380, "temperature": 0.3, "top_p": 0.9, "cache_prompt": True}).encode()
    req = urllib.request.Request("http://127.0.0.1:%d/v1/chat/completions" % port, data=body, headers={"Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    t0, t1, n, txt, f_ = time.time(), None, 0, "", []
    with op.open(req, timeout=900) as r:
        for line in r:
            line = line.strip()
            if not line.startswith(b"data:"):
                continue
            d = line[5:].strip()
            if d == b"[DONE]":
                break
            try:
                ev = json.loads(d)
            except ValueError:
                continue
            p = ((ev.get("choices") or [{}])[0].get("delta") or {}).get("content") or ""
            if p:
                t1 = t1 or time.time(); n += 1; txt += p
                if n % 20 == 0:
                    f_.append(fps(url, pw))
    t2 = time.time()
    return {"erstes_wort_s": round((t1 or t2) - t0, 1), "ganz_s": round(t2 - t0, 1), "stuecke": n,
            "stuecke_pro_s": round(n / max(0.1, t2 - (t1 or t2)), 1) if n else 0, "fps_waehrend": [x for x in f_ if x is not None], "antwort": txt}


def main():
    ap = argparse.ArgumentParser()
    home = os.path.expanduser("~/.config/motionwatch")
    ap.add_argument("--modell", default=os.path.join(home, "blinki", "qwen2.5-1.5b-instruct-q4_0.gguf"))
    ap.add_argument("--motor", default="")
    ap.add_argument("--datei", default="")
    ap.add_argument("--kerne", default="2,4")
    ap.add_argument("--fragen", type=int, default=8)
    ap.add_argument("--url", default="")
    ap.add_argument("--passwort", default="")
    a = ap.parse_args()
    motor = a.motor or (os.path.join(home, "blinki", "bin", "llama-server") if os.path.isfile(os.path.join(home, "blinki", "bin", "llama-server")) else shutil.which("llama-server") or "")
    if not os.path.isfile(a.modell) or not motor:
        sys.exit("Modell oder Motor fehlt – zuerst in MoveEye: Mehr → Blinki fragen → «Modell laden» / «Motor einrichten».")
    datei = a.datei or (sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")) + glob.glob(os.path.expanduser("~/webcam_bewegung_*.py")),
                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))]) or [""])[-1]
    ns = mw_laden(datei) if datei else None
    print("Motor %s · Modell %s · Prompts %s" % (motor, os.path.basename(a.modell), "wie MoveEye" if ns else "einfach"), flush=True)
    fps_ruhe = fps(a.url, a.passwort)
    res = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "modell": os.path.basename(a.modell), "motor": motor, "fps_ruhe": fps_ruhe,
           "uname": " ".join(os.uname()), "laeufe": []}
    for kerne in [int(x) for x in a.kerne.split(",") if x.strip()]:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
        t0 = time.time()
        p = subprocess.Popen(["nice", "-n", "15", motor, "-m", a.modell, "--host", "127.0.0.1", "--port", str(port), "-c", "4096", "-t", str(kerne),
                              "-tb", str(kerne), "-np", "1", "--no-webui"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        while time.time() - t0 < 300:
            try:
                if op.open("http://127.0.0.1:%d/health" % port, timeout=2).status == 200:
                    break
            except Exception:
                time.sleep(0.5)
        lauf = {"kerne": kerne, "start_s": round(time.time() - t0, 1), "fragen": []}
        try:
            for q in FRAGEN[:a.fragen]:
                msgs = ns["blinki_messages"]("frag", q, "de")[0] if ns else [{"role": "system", "content": "Antworte kurz auf Deutsch (Schweiz, ss statt ß)."},
                                                                            {"role": "user", "content": q}]
                tv = temp_c()
                r = frage(port, msgs, a.url, a.passwort)
                r.update(frage=q, temp_vor=tv, temp_nach=temp_c(), gedrosselt=gedrosselt(), ram_mb=rss_mb(p.pid), prompt_zeichen=sum(len(m["content"]) for m in msgs))
                lauf["fragen"].append(r)
                print("  %d Kerne · %-48s erstes Wort %5.1f s · ganz %5.1f s · %4.1f/s · %s °C" % (kerne, q[:48], r["erstes_wort_s"], r["ganz_s"], r["stuecke_pro_s"], r["temp_nach"]), flush=True)
        finally:
            p.terminate(); p.wait(20)
        res["laeufe"].append(lauf)
    os.makedirs(os.path.join(REPO, "feedback"), exist_ok=True)
    stamm = os.path.join(REPO, "feedback", "ki_messung_" + time.strftime("%Y%m%d_%H%M"))
    json.dump(res, open(stamm + ".json", "w"), indent=1, ensure_ascii=False)
    with open(stamm + ".md", "w", encoding="utf-8") as f:
        f.write("# Blinki-Messung %s\n\nModell %s · Bilder/s in Ruhe: %s\n\n" % (res["zeit"], res["modell"], fps_ruhe))
        for l_ in res["laeufe"]:
            f.write("## %d Kerne (Start %.1f s)\n\n| Frage | erstes Wort | ganz | Stücke/s | °C | Bilder/s |\n|---|---|---|---|---|---|\n" % (l_["kerne"], l_["start_s"]))
            for r in l_["fragen"]:
                f.write("| %s | %.1f s | %.1f s | %.1f | %s | %s |\n" % (r["frage"], r["erstes_wort_s"], r["ganz_s"], r["stuecke_pro_s"], r["temp_nach"],
                                                                   min(r["fps_waehrend"]) if r["fps_waehrend"] else "-"))
            f.write("\n")
            for r in l_["fragen"]:
                f.write("**%s**\n\n%s\n\nNote (1–6): …\n\n" % (r["frage"], r["antwort"]))
    print("Bericht: " + stamm + ".md")


if __name__ == "__main__":
    main()
