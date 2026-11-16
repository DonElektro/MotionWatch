#!/usr/bin/env python3
"""Test «Blinki fragen» (MoveEye Teile 639zzzzk_blinki_*) – ohne echtes Modell, ohne Internet.

Ein Ersatz-«llama-server» (dieses Skript mit --fake-llama, liegt als «llama-server» vorne im PATH) spricht wie llama.cpp:
/health und /v1/chat/completions mit «stream» (Server-Sent Events, Wort für Wort). Ein lokaler Ersatz für Hugging Face
liefert ein kleines Test-Modell (GGUF-Kopf) mit fester Grösse und Prüfsumme. MoveEye läuft mit einem Test-Ordner.

  A) im eigenen Prozess (gebaute Datei geladen): Prüfsummen-Tabelle, Laden (gut / falsche Prüfsumme / kein GGUF), Antwort
     Stück für Stück mit «Öffnen»-Zielen aus der Anleitung, ohne Modell nur die Stellen der Anleitung, Pause (SIGSTOP) bei
     Alarm / verfolgter Bewegung / Hitze und weiter danach, Fehlersuche liest Selbstdiagnose + Protokoll, Behebung nur mit
     OK, nie «Schutz aus», Leerlauf-Ende, ohne Daten-ZIP kein Absturz, Rechte, Texte in 5 Sprachen, Selbsttest-Funktion.
  C) MoveEye wird mit kill -9 beendet – der llama-server geht mit (PR_SET_PDEATHSIG).
  D) Pi-Fenster mit nachgebautem tkinter: Frage stellen, Antwort erscheint, Schliessen.
  E) Stufe 2: 🔥 Geschichten (Kinder-Filter, Orte des Platzes), 🦌 Naturführer (Sichtungen), 🎤 Quiz (JSON geprüft, in die Spielecke), Cloud
     (OpenAI-kompatibel + Anthropic Messages, Ersatz-Dienst: Schlüssel nie in Seite / Protokoll / Diagnose / Antwort, Bild nur mit OK, ohne Netz offline).
  F) Stufe 3: Sprechen – Ersatz-«whisper-cli», Erkennung (Aufnahme nie gespeichert), Handy-Aufnahme webm -> Text, 2× klatschen /
     Knopf (ab Werk aus; Klatschschalter, Wecker, Quittieren, Schutz-Knopf wie vorher), QR-Karte, ein Satz am Gerät -> Lautsprecher.
  P) 💬 Plaudern (639zzzzk_blinki_zz_plaudern): Art und Rechte, eigene Vorgabe, Verlauf (4 Runden, 15 min, «Neu», nur im Speicher), Hinweis
     offline, Cloud (OpenAI / Anthropic, mit Verlauf, kein Alarm), Auslöser am Gerät + Handy-Aufnahme, 5 Sprachen.
  B) --browser: MoveEye (Demo) im Browser: Mehr → «💬 Blinki fragen», Frage → Antwort Stück für Stück mit «Öffnen», Fehlersuche
     mit Vorschlag, Karte «Blinki einrichten» ohne Modell, 390 px dunkel + PC 1280; Rechte über HTTP. --bilder ORDNER.

  python3 werkzeuge/ki_test.py [--datei X.py] [--browser] [--bilder ORDNER] [--nur a,c,d,e,f,p,b]
"""
import argparse
import base64
import glob
import hashlib
import http.server
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
QWEN_SIZE = 1066227232
QWEN_SHA = "dcd819ff094852c38faba6873d8ff0c9d51eadb2844539e52042ae5d647bbfdb"


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


# ---- the fake llama-server (started by MoveEye as «llama-server») -----------------------------------------------------------------
def fake_llama(argv):
    a = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("-")}
    model, port = a.get("-m", ""), int(a.get("--port", "0"))
    with open(model, "rb") as f:
        if f.read(4) != b"GGUF":
            sys.exit("not a GGUF model")
    logp = os.environ.get("FAKE_LLAMA_LOG", "")
    if logp:
        with open(logp, "a") as f:
            f.write(json.dumps({"argv": argv, "pid": os.getpid(), "nice": os.nice(0)}) + "\n")
    t0 = time.time()
    delay = float(os.environ.get("FAKE_LLAMA_WORD_S", "0.05"))

    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *x):
            pass

        def do_GET(self):
            ready = time.time() - t0 > 0.6
            b = json.dumps({"status": "ok" if ready else "loading model"}).encode()
            self.send_response(200 if ready else 503); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
            if logp:
                with open(logp, "a") as f:
                    f.write(json.dumps({"req": d}, ensure_ascii=False) + "\n")
            sysm = d["messages"][0]["content"]
            src = re.findall(r"\[([^\]]{4,})\]", sysm)
            q = d["messages"][-1]["content"]
            jf = os.environ.get("FAKE_LLAMA_JSON_FILE", "")
            if jf and os.path.isfile(jf) and "JSON" in sysm:
                ans = open(jf, encoding="utf-8").read()
            elif "chatting with the user" in sysm:            # 💬 Plaudern
                ans = next((v for k, v in CHAT_ANTWORT if re.search(k, q, re.I)), "Gute Frage! Ganz sicher bin ich mir nicht – frag lieber nach, wenn es wichtig ist.")
            else:
                ans = "Das geht so:\n1. **%s** öffnen.\n2. Dort die Einstellung prüfen.\nFrage war: %s" % (src[0] if src else "Anleitung", q[:60])
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            words = re.findall(r"\S+\s*|\n", ans)

            def chunk(s):
                b = s.encode()
                self.wfile.write(b"%x\r\n%s\r\n" % (len(b), b)); self.wfile.flush()
            for w in words:
                chunk("data: " + json.dumps({"choices": [{"delta": {"content": w}}]}) + "\n\n")
                time.sleep(delay)
            chunk("data: [DONE]\n\n")
            self.wfile.write(b"0\r\n\r\n"); self.wfile.flush()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    srv.daemon_threads = True
    srv.serve_forever()


CHAT_ANTWORT = (("abend|rot", "Am Abend steht die Sonne tief. Ihr Licht geht einen langen Weg durch die Luft, das Blau wird unterwegs weggestreut – übrig bleiben **Rot und Orange**."),
                ("himmel|blau", "Das Sonnenlicht besteht aus allen Farben. Die Luft streut das **blaue Licht** viel stärker als das rote – darum sieht der Himmel blau aus."),
                ("witz", "Was macht ein Pirat am Computer? – Er drückt die **Enter**-Taste!"))


def make_bin(tmp):
    b = os.path.join(tmp, "bin"); os.makedirs(b, exist_ok=True)
    p = os.path.join(b, "llama-server")
    with open(p, "w") as f:
        f.write("#!%s\nimport sys\nsys.path.insert(0, %r)\nimport ki_test\nki_test.fake_llama(sys.argv[1:])\n" % (sys.executable, HIER))
    os.chmod(p, 0o755)
    return b


def fake_model(d):
    """the pinned Qwen file as a sparse file (no disk space) with the GGUF head + the marker the download writes"""
    os.makedirs(os.path.join(d, "blinki"), exist_ok=True)
    p = os.path.join(d, "blinki", "qwen2.5-1.5b-instruct-q4_0.gguf")
    with open(p, "wb") as f:
        f.write(b"GGUF\x03\x00\x00\x00"); f.truncate(QWEN_SIZE)
    with open(p + ".ok", "w") as f:
        f.write(QWEN_SHA)
    return p


class HF:
    """a local stand-in for huggingface.co (only /<repo>/resolve/<rev>/<file>, with Range)"""
    def __init__(self, files):
        self.files, self.hits = files, []
        me = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *x):
                pass

            def do_GET(self):
                p = self.path.split("?")[0]
                me.hits.append((p, self.headers.get("Range") or ""))
                data = next((v for k, v in me.files.items() if p.endswith("/" + k)), None)
                if data is None:
                    self.send_response(404); self.end_headers(); return
                rg = re.match(r"bytes=(\d+)-", self.headers.get("Range") or "")
                st = int(rg.group(1)) if rg else 0
                self.send_response(206 if st else 200)
                if st:
                    self.send_header("Content-Range", "bytes %d-%d/%d" % (st, len(data) - 1, len(data)))
                self.send_header("Content-Length", str(len(data) - st)); self.end_headers(); self.wfile.write(data[st:])
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d/" % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


def env_for(tmp, home):
    e = dict(os.environ, MOTIONWATCH_HOME=home, PATH=make_bin(tmp) + os.pathsep + os.environ.get("PATH", ""), PYTHONPATH=HIER,
             FAKE_LLAMA_LOG=os.path.join(tmp, "llama.log"), FAKE_LLAMA_JSON_FILE=os.path.join(tmp, "llama.json"), NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    os.makedirs(home, exist_ok=True)
    return e


def proc_state(pid):
    try:
        return open("/proc/%d/stat" % pid).read().rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        return ""


def llama_kids(pid):
    out = []
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                st = open("/proc/%s/stat" % d).read()
                cmd = open("/proc/%s/cmdline" % d, "rb").read().replace(b"\0", b" ").decode(errors="replace")
            except OSError:
                continue
            if int(st.rsplit(")", 1)[1].split()[1]) == pid and "llama-server" in cmd:
                out.append(int(d))
    return out


TEIL_A = r'''
import json, os, sys, time, hashlib, signal, threading
sys.path.insert(0, os.environ["KI_HIER"])
import ki_test as K
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_ki_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
ok = K.ok
C, B, S = ns["CFG"], ns["BLINKI"], ns["STATE"]
C.update(lang="de")
D = ns["DATA_DIR"]
def wait(f, s):
    t = time.time()
    while time.time() - t < s:
        if f(): return True
        time.sleep(0.05)
    return False
# --- the table
m = ns["BLINKI_MODELS"]["qwen2.5-1.5b-q4_0"]
ok(m["size"] == K.QWEN_SIZE and m["sha256"] == K.QWEN_SHA and m["rev"] == "dd26da440ef0330c47919d1ecae0966d24022222" and ns["blinki_pinned"]("qwen2.5-1.5b-q4_0"),
   "Tabelle: Qwen2.5-1.5B Q4_0 mit Revision, Grösse, SHA-256 (aus dem LFS-Zeiger von Hugging Face)")
ok(ns["BLINKI_LLAMA"]["tag"] == "b12000" and ns["BLINKI_LLAMA"]["commit"] == "68d20b884c3878217de79eade0a249efde96ab38", "Motor: llama.cpp b12000, Commit fest")
# --- the download (local stand-in for Hugging Face)
good = b"GGUF\x03\x00\x00\x00" + os.urandom(300000)
hf = K.HF({"good.gguf": good, "bad.gguf": good[:-1] + b"x", "nogguf.gguf": b"XXXX" + good[4:]})
ns["BLINKI_HF"]["url"] = hf.url
sha = hashlib.sha256(good).hexdigest()
for fid, fn in (("t-good", "good.gguf"), ("t-bad", "bad.gguf"), ("t-nogguf", "nogguf.gguf")):
    ns["BLINKI_MODELS"][fid] = dict(m, file=fn, size=len(good), sha256=sha, rev="a" * 40, ram_mb=1)
r = ns["blinki_download"]("t-good", wait=True)
ok(r[0] and ns["blinki_model_ok"]("t-good") and any(h[0].endswith("/resolve/" + "a" * 40 + "/good.gguf") for h in hf.hits), "Laden: feste Revision, Prüfsumme stimmt -> Modell bereit")
r = ns["blinki_download"]("t-bad", wait=True)
ok(not r[0] and not os.path.exists(ns["blinki_model_path"]("t-bad")) and not os.path.exists(ns["blinki_model_path"]("t-bad") + ".part"), "falsche Prüfsumme: verworfen (%s)" % r[1])
ns["BLINKI_MODELS"]["t-nogguf"]["sha256"] = hashlib.sha256(b"XXXX" + good[4:]).hexdigest()
r = ns["blinki_download"]("t-nogguf", wait=True)
ok(not r[0] and not ns["blinki_model_ok"]("t-nogguf"), "kein GGUF: verworfen (%s)" % r[1])
ns["BLINKI_MODELS"]["t-unpinned"] = dict(m, size=0)
ok(ns["blinki_download"]("t-unpinned")[0] is False, "ohne feste Grösse / Prüfsumme wird nie geladen")
ns["BLINKI_HF"]["url"] = "https://huggingface.co/"
ok(ns["blinki_delete"]("t-good")[0] and not os.path.exists(ns["blinki_model_path"]("t-good")), "Modell löschen")
# --- without the model: the places of the manual
j, e = ns["blinki_ask"]("frag", "Wie laut ist die Sirene?", "de")
ok(j and j["state"] == "done" and j["engine"] == "manual" and j["links"] and "Anleitung" in j["text"], "ohne Modell: Stellen der Anleitung (%s)" % [x["title"] for x in (j or {}).get("links", [])])
# --- with the model (fake engine)
K.fake_model(D)
ok(ns["blinki_offline_ok"]() and ns["blinki_engine"]().endswith("llama-server"), "Modell (Platzhalter mit Marke) + Motor im PATH")
j, e = ns["blinki_ask"]("frag", "Wie richte ich die Piper-Stimme ein?", "de", None, "test", "c1")
ok(j is not None and j["engine"] == "offline", "Frage angenommen (%s)" % e)
seen = []
def col():
    while j["state"] in ("wait", "think", "write"):
        seen.append(len(j["text"])); time.sleep(0.03)
th = threading.Thread(target=col); th.start(); th.join(60)
ok(j["state"] == "done" and "**" in j["text"] and len(set(seen)) > 5, "Antwort Stück für Stück (%d Stände): %s" % (len(set(seen)), j["text"][:70].replace("\n", " / ")))
ok(any(l["href"] == "/help#piper" for l in j["links"]) and all(l["href"].startswith("/") for l in j["links"]), "«Öffnen» aus den gefundenen Stellen: %s" % [l["href"] for l in j["links"]])
log = [json.loads(x) for x in open(os.environ["FAKE_LLAMA_LOG"])]
arg = next(x["argv"] for x in log if "argv" in x)
req = next(x["req"] for x in log if "req" in x)
ok(arg[arg.index("--host") + 1] == "127.0.0.1" and "--no-webui" in arg and arg[arg.index("-t") + 1] == "2" and arg[arg.index("-np") + 1] == "1", "Motor: nur 127.0.0.1, 2 Kerne, ohne Web-Oberfläche: %s" % " ".join(arg[2:]))
ok(next(x["nice"] for x in log if "argv" in x) >= 15, "Motor mit tiefer Priorität (nice %s)" % next(x["nice"] for x in log if "argv" in x))
ok(req["stream"] and "Piper" in req["messages"][0]["content"] and "Never suggest to switch the protection" in req["messages"][0]["content"], "Vorgabe mit Stellen der Anleitung, nie Schutz aus")
pid = B["proc"].pid
# --- the protection goes first: SIGSTOP / SIGCONT
os.environ["FAKE_LLAMA_WORD_S"] = "0.15"
for why, on, off in (("alarm", lambda: ns["LED"].update(alarm=True), lambda: ns["LED"].update(alarm=False)),
                     ("motion", lambda: S.update(persons=1), lambda: S.update(persons=0)),
                     ("heat", lambda: S.update(cpu_temp=84.0), lambda: S.update(cpu_temp=60.0))):
    j2, e = ns["blinki_ask"]("frag", "Was macht der Klatschschalter? " + why, "de", None, "test", "c2")
    wait(lambda: j2["state"] == "write", 20)
    on()
    stopped = wait(lambda: K.proc_state(pid) == "T", 5)
    n0 = len(j2["text"]); time.sleep(1.2); n1 = len(j2["text"])
    v = ns["blinki_job_view"](j2)
    ok(stopped and n1 == n0 and B["held"] == why and v["held"] == why, "%s: Motor angehalten (SIGSTOP), kein Text mehr, Seite sagt warum" % why)
    if why == "heat":
        S.update(cpu_temp=78.0); time.sleep(4.0)
        ok(B["held"] == "heat" and K.proc_state(pid) == "T", "Hitze: bei 78 °C noch Pause (erst unter 75 °C weiter)")
    off()
    ok(wait(lambda: j2["state"] == "done", 40) and K.proc_state(pid) != "T", "%s vorbei: nach 3 s ruhig weiter, Antwort fertig" % why)
os.environ["FAKE_LLAMA_WORD_S"] = "0.05"
# --- stop a question
j3, e = ns["blinki_ask"]("frag", "Wie geht die Zeitraffer-Aufnahme?", "de", None, "test", "c3")
wait(lambda: j3["state"] == "write", 20); j3["stop"] = True
ok(wait(lambda: j3["state"] == "stopped", 10), "Stopp mitten in der Antwort")
j4, e = ns["blinki_ask"]("frag", "Erste Frage", "de", None, "test", "same")
j5, e = ns["blinki_ask"]("frag", "Zweite Frage derselben Seite", "de", None, "test", "same")
ok(j4["stop"] and wait(lambda: j5["state"] == "done", 30), "neue Frage derselben Seite beendet die alte")
# --- troubleshooting: read only, fixes only with OK
j6, e = ns["blinki_ask"]("fehler", "", "de", None, "test", "c4")
wait(lambda: j6["state"] == "done", 30)
sysm = j6["messages"][0]["content"]
ok("SELF-CHECK" in sysm and "LOG (newest first)" in sysm and "Kamera" in sysm, "Fehlersuche: Selbstdiagnose + Protokoll im Vorgabetext")
ok(all(not f["act"] or not ns["BLINKI_FIX_DENY"].search(f["act"]) for f in j6["fixes"]), "Vorschläge: %s" % [(f["fid"], f["act"]) for f in j6["fixes"]])
fx = next((f for f in j6["fixes"] if f["act"]), None)
if fx:
    ok(ns["blinki_fix"](fx["fid"], False) == (False, "needs your OK") and ns["blinki_fix"](fx["fid"], "yes")[0] is False, "Behebung ohne OK: nein")
ok(ns["blinki_fix"]("PROTECT_OFF", True)[0] is False, "unbekannte / verbotene Behebung: nein")
ns["log_event"]("sys", "Test: Push an https://user:geheim@ntfy.example.ch/meinthema123")
facts, _f = ns["blinki_diag_facts"]("de")
ok("geheim" not in facts and "meinthema123" not in facts, "Protokoll für Blinki: Adressen gekürzt (kein Passwort, kein Thema)")
# --- idle: the engine ends
ns["BLINKI_IDLE_S"] = 1
ok(wait(lambda: B["proc"] is None, 10) and wait(lambda: K.proc_state(pid) == "", 10), "Leerlauf: Motor beendet (Speicher frei)")
ns["BLINKI_IDLE_S"] = 900
# --- without the data zip: no crash
hp, hx = ns["HELP_PAGE"], dict(ns["HELP_X"])
ns["HELP_PAGE"] = ""; ns["HELP_X"].clear(); ns["BLINKI_IDX"].clear()
try:
    j7, e = ns["blinki_ask"]("frag", "Wie laut ist die Sirene?", "de", None, "test", "c5")
    st = ns["blinki_page_state"]("de")
    ok(j7 is not None and st["model"]["ok"], "ohne Daten-ZIP (Anleitung leer): kein Absturz, sucht in den Einstellungen")
finally:
    ns["HELP_PAGE"] = hp; ns["HELP_X"].update(hx); ns["BLINKI_IDX"].clear()
wait(lambda: j7["state"] == "done", 30)
# --- rights
ra = ns["role_allows"]
ok(ra("view", "/api/ki/ask", "POST", {"mode": "frag"}) and not ra("view", "/api/ki/ask", "POST", {"mode": "fehler"}) and not ra("kid", "/api/ki/ask", "POST", {"mode": "frag"}),
   "Rechte: Frag MoveEye alle ausser Kinder, Fehlersuche nur Administrator")
ok(not ra("family", "/api/ki/model", "POST", {}) and not ra("family", "/api/ki/fix", "POST", {}) and not ra("family", "/api/ki/set", "POST", {}), "Modell / Behebung / Einstellungen: nur Administrator")
ok("/api/ki/set" in ns["APPKEY_DENY_PATHS"] and "/api/ki/model" in ns["LOCK_DENY_PATHS"], "nie mit App-Schlüssel, nicht im Bedienermodus")
# --- texts, self-test
tx = ns["BKFRAG_TX"]
ok(all(ns["DE"].get(k) and all(ns["TRX"][L].get(k) for L in ("fr", "it", "rm")) for k in tx), "Texte in 5 Sprachen (%d)" % len(tx))
ok(not [k for k in tx if "ß" in ns["DE"].get(k, "")], "Deutsch (Schweiz): nie «ß»")
ok('id="blinki"' in ns["HELP_PAGE"] and all('id="blinki"' in ns["HELP_X"][L] for L in ("fr", "it", "rm")), "Anleitung: Abschnitt «Blinki fragen» in 5 Sprachen")
ok('href="/blinki"' in ns["render_page"](ns["MORE_PAGE"], "more"), "Mehr → Übersicht: Zeile «💬 Blinki fragen»")
f = next(f for n, f in ns["SELFTEST_EXTRA"] if "Blinki fragen" in n)
try:
    ok(bool(f()), "Selbsttest-Funktion")
except AssertionError as e_:
    ok(False, "Selbsttest-Funktion: %s" % e_)
# --- program text as a literal of the data zip (zd_exec): the same checks as for a normal part
import ast as _ast, glob as _glob
lits = []
for f_ in sorted(_glob.glob(os.path.join(os.environ["KI_REPO"], "quelle", "*.py"))):
    for st_ in _ast.parse(open(f_, encoding="utf-8").read()).body:
        if isinstance(st_, _ast.Assign) and len(st_.targets) == 1 and isinstance(st_.targets[0], _ast.Name) and st_.targets[0].id.endswith("_PY") \
                and isinstance(st_.value, _ast.Constant) and isinstance(st_.value.value, str):
            lits.append((os.path.basename(f_), st_.targets[0].id, st_.value.value))
ok(len(lits) >= 3, "Literale mit Programmtext: %s" % [x[1] for x in lits])
others = {}
for f_ in sorted(_glob.glob(os.path.join(os.environ["KI_REPO"], "quelle", "*.py"))):
    for st_ in _ast.parse(open(f_, encoding="utf-8").read()).body:
        if isinstance(st_, (_ast.FunctionDef, _ast.ClassDef)):
            others.setdefault(st_.name, os.path.basename(f_))
for fn, nm, src_ in lits:
    try:
        code_ = compile(src_, fn, "exec"); good = code_.co_filename == fn
    except SyntaxError as e_:
        good = False
    tree_ = _ast.parse(src_)
    defs_ = [st_.name for st_ in tree_.body if isinstance(st_, (_ast.FunctionDef, _ast.ClassDef))]
    alias_ = {st_.value.id for st_ in tree_.body if isinstance(st_, _ast.Assign) and isinstance(st_.value, _ast.Name)}
    dup_ = [d for d in defs_ if d in others and others[d] != fn and d not in alias_]
    miss_ = {L: v for L, v in ns["i18n_missing"](src=src_).items() if v}
    old_ = ns["rucksack_alt_source"](src_) if "rucksack_alt_source" in ns else []
    ok(good and not dup_ and not miss_ and not old_,
       "%s/%s: kompiliert als «%s», keine doppelten Namen ohne Wrapper %s, Texte fr/it/rm %s, alter Name %s" % (fn, nm, fn, dup_, miss_, old_))
ok(ns["linecache"].getline("639zzzzk_blinki_kern.py", 1).startswith("import signal") if "linecache" in ns else __import__("linecache").getline("639zzzzk_blinki_kern.py", 1).startswith("import signal"),
   "Tracebacks zeigen die Zeilen des Teils (linecache)")
EXTRA = os.environ.get("KI_EXTRA_A")
if EXTRA:
    exec(open(EXTRA).read())
print("RESULT " + json.dumps(K.FEHLER))
'''


def teil_a(datei, tmp):
    print("A) im eigenen Prozess", flush=True)
    env = dict(env_for(tmp, os.path.join(tmp, "ahome")), KI_HIER=HIER, KI_REPO=REPO)
    p = subprocess.run([sys.executable, "-c", TEIL_A, datei], capture_output=True, text=True, env=env, cwd=tmp, timeout=900)
    out = p.stdout
    print("\n".join(x for x in out.splitlines() if x.startswith("  ")), flush=True)
    m = re.search(r"^RESULT (.*)$", out, re.M)
    if not m:
        FEHLER.append("Teil A abgebrochen")
        print((p.stderr or "")[-3000:])
        return
    FEHLER.extend(json.loads(m.group(1)))


TEIL_C = r'''
import os, sys, time
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_ki_c", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
sys.path.insert(0, os.environ["KI_HIER"]); import ki_test as K
K.fake_model(ns["DATA_DIR"])
ns["blinki_ensure"]()
t = time.time()
while ns["BLINKI"]["state"] != "ready" and time.time() - t < 30:
    time.sleep(0.1)
print("READY", ns["BLINKI"]["proc"].pid, flush=True)
time.sleep(600)
'''


def teil_c(datei, tmp):
    print("C) kill -9: der Motor geht mit", flush=True)
    env = dict(env_for(tmp, os.path.join(tmp, "chome")), KI_HIER=HIER)
    p = subprocess.Popen([sys.executable, "-c", TEIL_C, datei], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=tmp)
    pid = None
    t = time.time()
    while time.time() - t < 120:
        line = p.stdout.readline()
        if line.startswith("READY"):
            pid = int(line.split()[1]); break
        if not line and p.poll() is not None:
            break
    ok(pid is not None and pid in llama_kids(p.pid), "Motor läuft als Kind von MoveEye")
    os.kill(p.pid, signal.SIGKILL); p.wait()
    gone = False
    for _ in range(50):
        if not pid or proc_state(pid) in ("", "Z"):
            gone = True; break
        time.sleep(0.1)
    ok(gone, "nach kill -9 von MoveEye ist der llama-server weg")
    if pid and not gone:
        os.kill(pid, signal.SIGKILL)


TEIL_D = r'''
import os, sys, time, types
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_ki_d", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
sys.path.insert(0, os.environ["KI_HIER"]); import ki_test as K
AFTER = []
class W:
    def __init__(self, parent=None, **kw): self.kw = dict(kw); self.items = []; self.txt = ""; self.binds = {}; self.val = kw.get("value", "")
    def config(self, **kw): self.kw.update(kw)
    configure = config
    def pack(self, **kw): return self
    def grid(self, **kw): return self
    def bind(self, ev, f): self.binds[ev] = f
    def after(self, ms, f): AFTER.append(f)
    def winfo_exists(self): return not self.kw.get("destroyed")
    def title(self, t): self.kw["title"] = t
    def geometry(self, g): pass
    def lift(self): pass
    def destroy(self): self.kw["destroyed"] = True
    def insert(self, i, s): self.txt += s
    def delete(self, *a): self.val = ""
    def get(self): return self.val
    def see(self, *a): pass
    def index(self, *a): return "1.0" if not self.txt else "2.0"
tk = types.SimpleNamespace(Toplevel=W, Label=W, Frame=W, Text=W, Entry=W, Radiobutton=W, StringVar=W)
part = open(os.environ["KI_PART"], encoding="utf-8").read()
a0 = part.index("if GUI_OK:\n    def _blinki_tk_win"); a1 = part.index("App._blinki_win = _blinki_tk_win", a0) + len("App._blinki_win = _blinki_tk_win")
class App: pass
g = dict(ns); g.update(tk=tk, App=App, GUI_OK=True, C={"bg": "#000", "txt": "#fff", "mut": "#888", "panel": "#111", "field": "#222"})
g["blinki_tk_label"] = lambda *a, **k: W()
exec(part[a0:a1], g)
BTN = {}
class Me:
    root = None
    def _fbtn(self, parent, text, cmd, tip=None, primary=False, **k): BTN[text] = cmd; return W()
    def _open_page(self, p): BTN["opened"] = p
me = Me()
K.fake_model(ns["DATA_DIR"])
App._blinki_win(me)
top = me._blinki_top
ent = [v for v in []]
# the entry is the W with a <Return> binding
import gc
e = next(o for o in gc.get_objects() if isinstance(o, W) and "<Return>" in o.binds)
out = next(o for o in gc.get_objects() if isinstance(o, W) and o.kw.get("wrap") == "word")
e.val = "Wie laut ist die Sirene?"
e.binds["<Return>"]()
t = time.time()
while time.time() - t < 60 and "Das geht so" not in out.txt or "📖" not in out.txt:
    fs = AFTER[:]; AFTER.clear()
    for f in fs: f()
    time.sleep(0.2)
K.ok("Sirene" in out.txt and "Das geht so" in out.txt and "📖" in out.txt, "Fenster: Frage gestellt, Antwort Stück für Stück, Quellen: %s" % out.txt.replace("\n", " / ")[:120])
K.ok(any("Blinki" in k for k in []) or "title" in top.kw and "Blinki" in top.kw["title"], "Fenster-Titel: %s" % top.kw.get("title"))
[v for k, v in BTN.items() if "Browser" in k or "browser" in k][0]()
K.ok(BTN.get("opened") == "/blinki", "Knopf «Im Browser öffnen» -> /blinki")
[v for k, v in BTN.items() if k.endswith("Schliessen") or k == ns["tr"]("Close")][0]()
K.ok(not top.winfo_exists(), "Schliessen")
ns["blinki_stop"]("test")
import json; print("RESULT " + json.dumps(K.FEHLER))
'''


def teil_d(datei, tmp):
    print("D) Pi-Fenster (nachgebautes tkinter)", flush=True)
    env = dict(env_for(tmp, os.path.join(tmp, "dhome")), KI_HIER=HIER, KI_PART=os.path.join(REPO, "quelle", "639zzzzk_blinki_web.py"))
    p = subprocess.run([sys.executable, "-c", TEIL_D, datei], capture_output=True, text=True, env=env, cwd=tmp, timeout=300)
    print("\n".join(x for x in p.stdout.splitlines() if x.startswith("  ")), flush=True)
    m = re.search(r"^RESULT (.*)$", p.stdout, re.M)
    if not m:
        FEHLER.append("Teil D abgebrochen"); print((p.stderr or "")[-3000:]); return
    FEHLER.extend(json.loads(m.group(1)))


WRAP = r'''
import os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
sys.argv = [D] + sys.argv[2:]
exec(compile(src, D, "exec"), {"__name__": "__main__", "__file__": D})
'''
PW = "ki-test-pw-1"


def pwhash(pw):
    salt = os.urandom(16)
    return "pbkdf2$200000$%s$%s" % (salt.hex(), hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200000).hex())


def start_mw(datei, tmp, name, extra_cfg=None, model=True):
    cfg = os.path.join(tmp, name); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "detection_on": False, "track_person": False, "track_motion": False, "patrol": False, "thermal_on": False,
          "users": [{"name": "gast", "hash": pwhash("gast-pw-123"), "role": "view"}, {"name": "kind", "hash": pwhash("kind-pw-123"), "role": "kid"}]}
    st.update(extra_cfg or {})
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    if model:
        fake_model(cfg); fake_stt_model(cfg); make_whisper(tmp)
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, name + ".log"), "w")
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env_for(tmp, os.path.join(tmp, name + "_home")))
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _i in range(240):
        if p.poll() is not None:
            sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, name + ".log"), errors="replace").read()[-3000:])
        try:
            op.open(base + "/manifest.webmanifest", timeout=2); break
        except Exception:
            time.sleep(1)
    return p, base, op


def http_api(op, base, path, data=None, user="admin", pw=PW):
    h = {"Authorization": "Basic " + base64.b64encode((user + ":" + pw).encode()).decode(), "Content-Type": "application/json"}
    r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
    try:
        with op.open(r, timeout=60) as x:
            return x.status, json.loads(x.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def weg(pg):                                              # the coach-mark tour (516): out of the way
    pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); "
                "const b = document.querySelector('header>h1 .badge'); if (b) b.remove(); }")


def teil_b(datei, tmp, bilder, extra=None):
    print("B) Browser (MoveEye Demo)", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    B_TMP["tmp"] = tmp
    p, base, op = start_mw(datei, tmp, "bcfg")
    try:
        c1, a1 = http_api(op, base, "/api/ki/ask", {"mode": "frag", "q": "Wie laut ist die Sirene?"}, "gast", "gast-pw-123")
        c2, _a = http_api(op, base, "/api/ki/ask", {"mode": "fehler", "q": ""}, "gast", "gast-pw-123")
        c3, _a = http_api(op, base, "/api/ki/model", {"action": "load"}, "gast", "gast-pw-123")
        c4, _a = http_api(op, base, "/api/ki/ask", {"mode": "frag", "q": "x"}, "kind", "kind-pw-123")
        c5, s5 = http_api(op, base, "/api/ki/state", None, "gast", "gast-pw-123")
        ok([c1, c2, c3, c4, c5] == [200, 403, 403, 403, 200] and [m["m"] for m in s5["state"]["modes"]] == (["frag", "plaudern", "geschichte", "natur"] if len(s5["state"]["modes"]) > 1 else ["frag"]),
           "Rechte über HTTP: Nur ansehen fragt %d, Fehlersuche %d, Modell %d; Kind %d; Arten für Gast: %s" % (c1, c2, c3, c4, [m["m"] for m in s5["state"]["modes"]]))
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
            for name, vp, mob in (("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 900}, False)):
                ctx = br.new_context(viewport=vp, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob, color_scheme="dark",
                                     http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                ctx.add_init_script("try { if (!sessionStorage.getItem('ki-fx')) localStorage.setItem('mw-sheet', 'full'); } catch (e) {}")   # 639zzzzx: whole page here, the window is checked in b_extra
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(base + "/more", wait_until="domcontentloaded"); pg.wait_for_timeout(1500); weg(pg)
                row = pg.locator("#m-blinki")
                ok(row.count() == 1 and "Blinki fragen" in row.inner_text(), "%s: Mehr → Zeile «%s»" % (name, row.inner_text().replace("\n", " · ") if row.count() else "-"))
                row.click()
                pg.wait_for_function("() => (document.getElementById('bk-chip-t') || {}).textContent.includes('Offline')", timeout=30000)
                weg(pg)
                ok(pg.locator("#bk-face .bk").count() == 1 and pg.locator("#bk-modes button").count() >= 2, "%s: Blinki-Figur und die Arten" % name)
                pg.locator("#bk-modes button", has_text="Frag MoveEye").click()
                pg.locator("#bk-q").fill("Wie lade ich die Piper-Stimme?")
                pg.locator("#bk-go").click()
                pg.wait_for_function("() => document.querySelector('.bkp-say .cur')", timeout=30000)
                mid = pg.evaluate("() => document.querySelector('.bkp-say').innerText")
                pg.wait_for_function("() => document.querySelector('.bkp-open a')", timeout=60000)
                pg.wait_for_timeout(400); weg(pg)
                a = pg.locator(".bkp-open a").first
                ok(len(mid) > 3 and a.get_attribute("href") == "/help#piper" and "Öffnen" in a.inner_text(), "%s: Antwort erscheint Stück für Stück, «%s» → %s" % (name, a.inner_text(), a.get_attribute("href")))
                ok(pg.locator(".bkp-say ol li").count() == 2 and pg.locator(".bkp-say b").count() >= 1, "%s: Liste und Fett aus der Antwort (als Text, kein HTML)" % name)
                w = pg.evaluate("() => document.documentElement.scrollWidth")
                ok(w <= vp["width"], "%s: keine waagrechte Bildlaufleiste (%d)" % (name, w))
                pg.screenshot(path=os.path.join(bilder, "blinki_%s_frag.png" % name), full_page=False)
                pg.locator("#bk-modes button", has_text="Fehlersuche").click()
                pg.locator("#bk-go").click()
                pg.wait_for_function("() => document.querySelectorAll('.bkp-src').length >= 2", timeout=60000)
                pg.wait_for_timeout(500); weg(pg)
                ok(pg.locator(".bkp-fix").count() >= 1 and "Vorschlag" in pg.locator(".bkp-fix").first.inner_text(), "%s: Fehlersuche mit Vorschlag (nur mit OK)" % name)
                pg.screenshot(path=os.path.join(bilder, "blinki_%s_fehlersuche.png" % name), full_page=False)
                if extra:
                    extra(pg, name, base, op, bilder)
                ok(not errs, "%s: keine JS-Fehler %s" % (name, errs[:2]))
                ctx.close()
            # no model: the setup card
            http_api(op, base, "/api/ki/model", {"action": "delete"})
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme="dark",
                                 http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + "/blinki", wait_until="domcontentloaded")
            pg.wait_for_function("() => !document.getElementById('bk-setup').hidden", timeout=30000)
            pg.wait_for_timeout(500); weg(pg)
            ok("Modell laden" in pg.locator("#bk-su-b").inner_text() and "Apache-2.0" in pg.locator("#bk-su-m").inner_text(), "ohne Modell: Karte «Blinki einrichten» mit «%s»" % pg.locator("#bk-su-b").inner_text().replace("\n", " · "))
            pg.locator("#bk-modes button", has_text="Frag MoveEye").click()
            pg.locator("#bk-q").fill("Wie laut ist die Sirene?"); pg.locator("#bk-go").click()
            pg.wait_for_function("() => document.querySelector('.bkp-open a')", timeout=30000); pg.wait_for_timeout(300); weg(pg)
            ok("Anleitung" in pg.locator(".bkp-say").first.inner_text(), "ohne Modell: Blinki zeigt die Stellen der Anleitung")
            pg.screenshot(path=os.path.join(bilder, "blinki_handy_einrichten.png"))
            ok(not errs, "Einrichten: keine JS-Fehler %s" % errs[:2])
            ctx.close(); br.close()
    finally:
        p.terminate()
        try:
            p.wait(20)
        except subprocess.TimeoutExpired:
            p.kill()


# ---- stage 2: stories, nature guide, quiz, cloud ------------------------------------------------------------------------------------
class Cloud:
    """a stand-in for a cloud service: OpenAI-compatible (/v1/chat/completions) and Anthropic Messages (/v1/messages), streaming"""
    def __init__(self):
        self.reqs = []
        me = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *x):
                pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n)
                me.reqs.append({"path": self.path, "h": {k.lower(): v for k, v in self.headers.items()}, "raw": raw})
                if self.path.endswith("/audio/transcriptions"):
                    b = json.dumps({"text": "Wie laut ist die Sirene?"}).encode()
                    self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers()
                    self.wfile.write(b); return
                key = self.headers.get("x-api-key") or (self.headers.get("Authorization") or "")[7:]
                if "WRONG" in key:
                    b = json.dumps({"error": "invalid key " + key}).encode()
                    self.send_response(401); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
                anth = self.path.endswith("/v1/messages")
                self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Transfer-Encoding", "chunked"); self.end_headers()

                def chunk(s):
                    b = s.encode(); self.wfile.write(b"%x\r\n%s\r\n" % (len(b), b)); self.wfile.flush()
                for w in ["Hallo ", "aus ", "der ", "Cloud", "."]:
                    if anth:
                        chunk("event: content_block_delta\ndata: " + json.dumps({"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": w}}) + "\n\n")
                    else:
                        chunk("data: " + json.dumps({"choices": [{"delta": {"content": w}}]}) + "\n\n")
                    time.sleep(0.03)
                chunk("event: message_stop\ndata: {\"type\": \"message_stop\"}\n\n" if anth else "data: [DONE]\n\n")
                self.wfile.write(b"0\r\n\r\n"); self.wfile.flush()
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.httpd.daemon_threads = True
        self.url = "http://127.0.0.1:%d/v1" % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


TEIL_E = r'''
import json, os, sys, time, threading
import numpy as np
sys.path.insert(0, os.environ["KI_HIER"])
import ki_test as K
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_ki_e", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
ok = K.ok
C, B = ns["CFG"], ns["BLINKI"]
C.update(lang="de")
logs = []
_lg = ns["log_event"]
def lg(kind, text):
    logs.append(str(text)); return _lg(kind, text)
ns["log_event"] = lg
def wait(f, s):
    t = time.time()
    while time.time() - t < s:
        if f(): return True
        time.sleep(0.05)
    return False
def run(mode, q="", extra=None, cl="e"):
    j, e = ns["blinki_ask"](mode, q, "de", None, "test", cl + mode, extra)
    assert j is not None, e
    wait(lambda: j["state"] in ("done", "error", "stopped"), 60)
    return j
K.fake_model(ns["DATA_DIR"])
ns["BLINKI_MODE_ICON"]
ok([m["m"] for m in ns["blinki_modes"]("admin")] == ["frag", "plaudern", "fehler", "geschichte", "natur", "quiz"], "Arten: 💬 💬 🔧 🔥 🦌 🎤")
ok([m["m"] for m in ns["blinki_modes"]("kid")] == ["geschichte"] and [m["m"] for m in ns["blinki_modes"]("view")] == ["frag", "plaudern", "geschichte", "natur"]
   and [m["m"] for m in ns["blinki_modes"]("friend")] == ["frag", "plaudern", "geschichte", "quiz"], "Rechte: Kind nur Geschichten, Naturführer = Aufnahmen, Quiz = Spiele")
# stories with places of the own site
ns["ZONES"][:] = [{"name": "Feuerstelle", "mode": "alarm", "points": []}]
ok("Feuerstelle" in ns["blinki_places"](), "Orte des eigenen Platzes: %s" % ns["blinki_places"]())
j = run("geschichte", "", {"kid": True, "place": "Feuerstelle"})
req = [json.loads(x) for x in open(os.environ["FAKE_LLAMA_LOG"]) if '"req"' in x][-1]["req"]
ok(j["state"] == "done" and "children aged 5 to 10" in req["messages"][0]["content"] and "Feuerstelle" in req["messages"][0]["content"] and req["max_tokens"] == 650,
   "🔥 Kinder-Geschichte an der Feuerstelle (Vorgabe für Kinder, längere Antwort)")
j = run("geschichte", "", {"kid": True, "place": "48.1,7.2 geheim"})
req = [json.loads(x) for x in open(os.environ["FAKE_LLAMA_LOG"]) if '"req"' in x][-1]["req"]
ok("geheim" not in req["messages"][0]["content"], "nur Orte der Liste (kein fremder Text in der Vorgabe)")
j = run("geschichte", "Ein Drache mit Blut am Messer", {"kid": True})
v = ns["blinki_job_view"](j)
ok(v["full"] and "Blut" not in v["text"] and "anderen" in v["text"].lower() or "andere" in v["text"], "Kinder-Filter: unpassendes Wort -> freundlich abgebrochen (%s)" % v["text"][:60])
j = run("geschichte", "Ein Drache mit Blut am Messer", {"kid": False})
ok("Blut" in ns["blinki_job_view"](j)["text"], "Erwachsene: kein Kinder-Filter")
# nature guide
ns["SIGHT"].update(loaded=True)
ns["SIGHT"]["list"][:] = [{"id": "s1", "start": (ns["datetime"].now() - ns["timedelta"](hours=5)).isoformat(timespec="seconds"), "label": "fox", "kind": "animal", "dur": 42, "img": "", "conf": 0.8}]
ns["sight_load"] = lambda: None
j = run("natur")
req = [json.loads(x) for x in open(os.environ["FAKE_LLAMA_LOG"]) if '"req"' in x][-1]["req"]
ok(j["state"] == "done" and "SEEN BY MOVEEYE" in req["messages"][0]["content"] and "(42 s)" in req["messages"][0]["content"], "🦌 Naturführer mit den Sichtungen der letzten 7 Tage")
# quiz
open(os.environ["FAKE_LLAMA_JSON_FILE"], "w", encoding="utf-8").write(json.dumps([{"q": "Wie heisst der höchste Berg der Schweiz?", "a": "Dufourspitze"}, {"q": "Welches Tier baut einen Damm?", "a": "Biber"},
                                            {"q": "Wie viele Beine hat ein Käfer?", "a": "6"}, {"q": "x", "a": "zu kurz"}], ensure_ascii=False))
n0 = len(ns["QUIZ"])
j = run("quiz", "", {"n": 5})
v = ns["blinki_job_view"](j)
ok([x["a"] for x in v["quiz"]] == ["Biber", "6"], "🎤 Quiz: JSON geprüft (doppelt / zu kurz weg): %s" % [x["a"] for x in v["quiz"]])
r = ns["blinki_quiz_take"](j["id"], None, "test")
ok(r[0] and r[2] == 2 and len(ns["QUIZ"]) == n0 + 2 and C["blinki_quiz"][-1]["a"] == "6", "«In die Spielecke»: 2 Fragen im Quiz und gemerkt")
ok(ns["role_allows"]("friend", "/api/ki/quiz", "POST", {}) and not ns["role_allows"]("view", "/api/ki/quiz", "POST", {}), "Quiz übernehmen: Recht «Spiele»")
os.remove(os.environ["FAKE_LLAMA_JSON_FILE"])
# the cloud
cl = K.Cloud()
st = ns["blinki_set"]
ok(st("blinki_cloud_on", True)[0] is False, "Cloud ein geht erst mit Adresse, Modell und Schlüssel")
ok(st("blinki_cloud_url", "http://api.example.com/v1")[0] is False and st("blinki_cloud_url", "https://u:p@api.example.com")[0] is False
   and st("blinki_cloud_url", "https://api.example.com/v1")[0], "Adresse: nur https (http nur im eigenen Netz), nie Benutzer:Passwort@")
KEY = "sk-test-GEHEIM-1234567890abcdef"
for k_, v_ in (("blinki_cloud_url", cl.url), ("blinki_cloud_model", "test-model-1"), ("blinki_cloud_key", KEY), ("blinki_cloud_fmt", "openai"), ("blinki_cloud_on", True)):
    ok(st(k_, v_)[0], "einstellen: " + k_)
ok(ns["role_allows"]("family", "/api/ki/set", "POST", {"key": "blinki_cloud_key"}) is False and "blinki_cloud_key" in ns["USER_SETTINGS_DENY"]
   and "blinki_cloud_key" in ns["APPKEY_DENY_KEYS"], "Schlüssel nur vom Administrator")
j = run("frag", "Wie laut ist die Sirene?")
r0 = cl.reqs[-1]; body = json.loads(r0["raw"])
ok(j["engine"] == "cloud" and j["text"] == "Hallo aus der Cloud." and r0["path"] == "/v1/chat/completions" and r0["h"].get("authorization") == "Bearer " + KEY
   and body["model"] == "test-model-1" and body["stream"] and "top_p" not in body and "cache_prompt" not in body, "OpenAI-kompatibel: Stream, Bearer, Modell")
ok(st("blinki_cloud_fmt", "anthropic")[0], "Format Anthropic Messages")
j = run("frag", "Was macht der Klatschschalter?")
r0 = cl.reqs[-1]; body = json.loads(r0["raw"])
ok(j["text"] == "Hallo aus der Cloud." and r0["path"] == "/v1/messages" and r0["h"].get("x-api-key") == KEY and r0["h"].get("anthropic-version") == "2023-06-01"
   and body["system"] and all(m["role"] != "system" for m in body["messages"]), "Anthropic Messages: x-api-key, Version, system getrennt")
# pictures only with the own OK
class Wt: pass
w = Wt(); w.frame_raw = np.full((480, 640, 3), 90, np.uint8); ns["WATCH_REF"]["w"] = w
n_ = len(cl.reqs); j = run("natur", "", {}); b0 = cl.reqs[-1]["raw"]
ok(b"base64" not in b0 and not ns["blinki_job_view"](j)["image"], "Naturführer ohne OK: kein Bild")
j = run("natur", "", {"image_ok": "yes"}); ok(b"base64" not in cl.reqs[-1]["raw"], "image_ok muss genau true sein")
j = run("natur", "Was ist das?", {"image_ok": True}); b1 = cl.reqs[-1]["raw"]
ok(b'"type": "image"' in b1 or b'"type":"image"' in b1, "Naturführer mit OK: genau dieses eine Bild (Anthropic-Form)")
ok(j.get("image") is None and ns["blinki_job_view"](j)["image"], "das Bild wird nicht behalten, die Antwort sagt «Bild gesendet»")
# the key never leaves
st("blinki_cloud_key", "sk-WRONG-" + KEY[8:])
j = run("frag", "Test mit falschem Schlüssel")
WK = "sk-WRONG-" + KEY[8:]
ok(j["state"] == "error" and WK not in j["err"] and "401" in j["err"], "Fehler des Dienstes geschwärzt: %s" % j["err"][:80])
st("blinki_cloud_key", KEY)
ps = json.dumps(ns["blinki_page_state"]("de"))
import zipfile, io
z = zipfile.ZipFile(io.BytesIO(ns["diag_zip"]()))
dz = z.read("settings_without_secrets.json").decode()
ok(KEY not in ps and WK not in ps and '"key_set": true' in ps, "Seite: Schlüssel nie, nur «gesetzt»")
ok(KEY not in dz and json.loads(dz)["blinki_cloud_key"] == "***", "Diagnose-Paket: «***»")
ok(not any(KEY in x or WK in x for x in logs) and not any(KEY in open(f, errors="replace").read() for f in [ns["LOG_FILE"]] if os.path.isfile(f)), "Protokoll: nie der Schlüssel")
ok(all(KEY not in json.dumps(ns["blinki_job_view"](x)) for x in B["jobs"].values()), "Antworten: nie der Schlüssel")
# no network: offline instead
st("blinki_cloud_url", "http://127.0.0.1:9/v1")
j = run("frag", "Ohne Netz?")
ok(j["state"] == "done" and j["engine"] == "offline" and "Das geht so" in j["text"], "Cloud nicht erreichbar -> offline (Modell auf dem Gerät)")
ns["blinki_stop"]("test")
print("RESULT " + json.dumps(K.FEHLER))
'''


def teil_e(datei, tmp):
    print("E) Stufe 2: Geschichten, Naturführer, Quiz, Cloud", flush=True)
    env = dict(env_for(tmp, os.path.join(tmp, "ehome")), KI_HIER=HIER)
    p = subprocess.run([sys.executable, "-c", TEIL_E, datei], capture_output=True, text=True, env=env, cwd=tmp, timeout=900)
    print("\n".join(x for x in p.stdout.splitlines() if x.startswith("  ")), flush=True)
    m = re.search(r"^RESULT (.*)$", p.stdout, re.M)
    if not m:
        FEHLER.append("Teil E abgebrochen"); print((p.stderr or "")[-3000:]); return
    FEHLER.extend(json.loads(m.group(1)))


# ---- stage 3: speaking -----------------------------------------------------------------------------------------------------------
STT_SIZE = 77691713
STT_SHA = "be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21"


def fake_whisper(argv):
    import wave
    import numpy as np
    a = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("-")}
    with wave.open(a["-f"]) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768.0
    logp = os.environ.get("FAKE_WHISPER_LOG", "")
    if logp:
        with open(logp, "a") as f:
            f.write(json.dumps({"argv": argv, "secs": round(x.size / 16000.0, 2)}) + "\n")
    loud = float(np.sqrt(np.mean(x * x))) if x.size else 0.0
    print(" Wie laut ist die Sirene?" if loud > 0.01 else "[BLANK_AUDIO]")


def make_whisper(tmp):
    b = os.path.join(tmp, "bin"); os.makedirs(b, exist_ok=True)
    p = os.path.join(b, "whisper-cli")
    with open(p, "w") as f:
        f.write("#!%s\nimport sys\nsys.path.insert(0, %r)\nimport ki_test\nki_test.fake_whisper(sys.argv[1:])\n" % (sys.executable, HIER))
    os.chmod(p, 0o755)


def fake_stt_model(d):
    os.makedirs(os.path.join(d, "blinki"), exist_ok=True)
    p = os.path.join(d, "blinki", "ggml-tiny.bin")
    with open(p, "wb") as f:
        f.write(b"lmgg"); f.truncate(STT_SIZE)
    with open(p + ".ok", "w") as f:
        f.write(STT_SHA)


TEIL_F = r'''
import json, os, sys, time, threading, glob
import numpy as np
sys.path.insert(0, os.environ["KI_HIER"])
import ki_test as K
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_ki_f", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
ok = K.ok
C = ns["CFG"]; LI = ns["LISTEN"]
C.update(lang="de")
def wait(f, s):
    t = time.time()
    while time.time() - t < s:
        if f(): return True
        time.sleep(0.05)
    return False
m = ns["BLINKI_STT_MODELS"]["whisper-tiny"]
ok(m["size"] == K.STT_SIZE and m["sha256"] == K.STT_SHA and m["rev"] == "98aa99a0a9db05ae2342309f5096248665f7cba3", "Spracherkennung: ggml-tiny mit Revision, Grösse, SHA-256")
ok(ns["BLINKI_WHISPER"]["commit"] == "d1be6fde11ac6e0407606b4e42fe72d34add8037" and ns["BLINKI_STT_MODELS"]["vosk-small-de"]["size"] == 0,
   "whisper.cpp v1.9.5 fest; Vosk ohne geprüfte Prüfsumme = wird nie geladen")
ok(C["blinki_clap"] is False and C["blinki_btn"] is False and ns["DEFAULTS"]["blinki_clap"] is False, "2× klatschen / Knopf für Blinki: ab Werk AUS")
ok("blinki_clap" in ns["USER_SETTINGS_DENY"] and "blinki_btn" in ns["APPKEY_DENY_KEYS"] and not ns["role_allows"]("family", "/api/ki/set", "POST", {"key": "blinki_clap"}),
   "Schalter nur für den Administrator")
K.fake_model(ns["DATA_DIR"]); K.fake_stt_model(ns["DATA_DIR"])
ok(ns["blinki_stt_engine"]()[0] == "whisper", "whisper-cli (Ersatz) + Modell bereit")
sr = 16000
def tone(sec, amp=0.3, f=300.0):
    t = np.arange(int(sec * sr)) / sr
    return (amp * np.sin(2 * np.pi * f * t) * 32767).astype("<i2")
def quiet(sec):
    return (np.random.RandomState(1).randn(int(sec * sr)) * 30).astype("<i2")
shm = ns["_bk_tmpdir"]()
before = set(glob.glob(os.path.join(shm, "bk-*")))
txt, e = ns["blinki_stt_pcm"](np.concatenate([quiet(0.5), tone(1.2), quiet(0.5)]).tobytes(), "de")
ok(txt == "Wie laut ist die Sirene?", "Erkennung: «%s»" % txt)
log = [json.loads(x) for x in open(os.environ["FAKE_WHISPER_LOG"])]
ok(log[-1]["argv"][log[-1]["argv"].index("-l") + 1] == "de" and "-nt" in log[-1]["argv"], "whisper-cli -l de -nt")
ok(set(glob.glob(os.path.join(shm, "bk-*"))) == before, "Aufnahme nie gespeichert (Datei sofort gelöscht)")
txt, e = ns["blinki_stt_pcm"](quiet(2.0).tobytes(), "de")
ok(txt == "" and e == "nothing understood", "Stille: nichts verstanden")
import subprocess
wav = os.path.join(os.environ["KI_TMP"], "rec.webm")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=1.5:sample_rate=48000", "-c:a", "libopus", wav], check=True)
txt, e = ns["blinki_stt_upload"](open(wav, "rb").read(), "de")
ok(txt == "Wie laut ist die Sirene?", "Handy-Aufnahme (webm/opus) -> Text")
ok(ns["blinki_stt_upload"](b"x" * (ns["BLINKI_STT_MAX_BYTES"] + 1), "de")[1] == "the recording is too long" and ns["blinki_stt_upload"](b"junk" * 100, "de")[0] == "",
   "zu lang / kaputt: abgelehnt")
# ---- the triggers: the existing functions stay exactly as they were
calls = {"listen": [], "light": [], "snooze": [], "protect": [], "ack": []}
real_listen = ns["blinki_listen"]
ns["blinki_listen"] = lambda why="": calls["listen"].append(why) or (True, "")
ns["light_set"] = lambda nm, v: calls["light"].append((nm, v)) or (True, "")
ns["wake_snooze"] = lambda why="": calls["snooze"].append(why)
ns["sev_beep"] = lambda *a, **k: None
def reset():
    for v in calls.values(): v.clear()
def clap(n, **cfg):
    reset(); C.update(cfg); ns["clap_action"](n); return {k: list(v) for k, v in calls.items()}
ns["WAKE"]["state"] = "off"
C.update(light_white="off", clap_practice=False, clap_disarmed=False, armed=False)
r = clap(2, blinki_clap=False, clap_on=True, clap_2="light_white"); ok(r["light"] == [("white", "on")] and not r["listen"], "Klatschschalter wie vorher (Blinki aus)")
r = clap(2, blinki_clap=True, clap_on=True, clap_2="light_white"); ok(r["light"] == [("white", "on")] and not r["listen"], "Blinki ein, 2× hat schon eine Aufgabe: der Klatschschalter gewinnt")
r = clap(2, blinki_clap=True, clap_on=True, clap_2="none"); ok(r["listen"] and not r["light"], "Blinki ein, 2× ohne Aufgabe: Blinki hört zu")
r = clap(3, blinki_clap=True, clap_on=True, clap_3="light_white"); ok(r["light"] == [("white", "on")] and not r["listen"], "3× klatschen: wie vorher")
r = clap(2, blinki_clap=True, clap_on=False, clap_2="light_white"); ok(r["listen"] and not r["light"], "Klatschschalter aus, Blinki ein: nur Blinki")
r = clap(3, blinki_clap=True, clap_on=False, clap_3="light_white"); ok(not r["listen"] and not r["light"], "Klatschschalter aus: 3× schaltet nichts (wie vorher)")
r = clap(2, blinki_clap=False, clap_on=False, clap_2="light_white"); ok(not r["listen"] and not r["light"], "beide aus: nichts")
ns["WAKE"]["state"] = "ring"; _ai = C.get("audio_in"); C["audio_in"] = "hw:1"   # the wake-up alarm hears claps only with a microphone
r = clap(2, blinki_clap=True, clap_on=True, clap_2="none"); ok(r["snooze"] and not r["listen"], "Wecker klingelt: 2× klatschen = Schlummern wie vorher, kein Blinki")
C["audio_in"] = _ai
ns["WAKE"]["state"] = "off"
# the microphone path: claps with the clap switch off reach Blinki only with its switch
class A_: mute_until = 0.0; sim_t = 0.0
ns["AUDIO"] = A_()
ns["SOUND"]["playing"] = False
ns["SERVO_MOVE"]["t"] = 0.0
def claps_into(feeder, t0):
    t = t0
    for k in range(40):
        a = (np.random.RandomState(k).randn(1600) * 20).astype(np.int16)
        if k in (10, 14):
            a[300:620] = 20000
        feeder(a, t); t += 0.1
    return t
reset(); C.update(blinki_clap=True, clap_on=False, sneeze_on=False)
se = ns["SoundEvents"](); claps_into(se.feed, 1000.0)
ok(calls["listen"] == ["2× clapped"], "Mikrofon: 2 Klatscher -> Blinki (Klatschschalter aus): %s" % calls["listen"])
reset(); C.update(blinki_clap=False, clap_on=False)
se = ns["SoundEvents"](); claps_into(se.feed, 2000.0)
ok(not calls["listen"] and not ns["SOUNDEV"]["claps"], "Mikrofon: Blinki-Schalter aus -> es wird nicht einmal gezählt (wie vorher)")
# the buttons
ns["protect_set"] = lambda lv, who="": calls["protect"].append(lv)
ns["led_ack"] = lambda who="": calls["ack"].append(who)
ns["LED"]["alarm"] = False
def btn(name, ev, **cfg):
    reset(); C.update(cfg); ns["led_button_event"](name, ev, "GPIO"); return {k: list(v) for k, v in calls.items()}
C.update(armed=False, btn_allow_arm=True, btn_allow_ack=True, btn_allow_siren=True)
r = btn("protect", "short", blinki_btn=True); ok(r["protect"] == ["watch"] and not r["listen"], "Schutz-Knopf unverändert (Blinki-Knopf ein)")
r = btn("protect", "long", blinki_btn=True); ok(r["protect"] == ["full"] and not r["listen"], "Schutz-Knopf lang unverändert")
r = btn("ack", "long", blinki_btn=True); ok(r["ack"] and r["listen"] == ["button"], "Quittieren lang, nichts zu quittieren: quittiert wie immer + Blinki")
r = btn("ack", "short", blinki_btn=True); ok(r["ack"] and not r["listen"], "Quittieren kurz: nur quittieren")
ns["LED"]["alarm"] = True
r = btn("ack", "long", blinki_btn=True); ok(r["ack"] and not r["listen"], "Alarm läuft: der Knopf quittiert, kein Blinki")
ns["LED"]["alarm"] = False
r = btn("ack", "long", blinki_btn=False); ok(r["ack"] and not r["listen"], "Blinki-Knopf aus: wie vorher")
# QR card
card, e = ns["qrk_create"]({"cmd": "B", "name": "Blinki fragen"})
ok(card is not None and ns["qrk_check"](ns["qrk_payload"](card))[0] == "ok", "QR-Karte «💬 Blinki hört zu» erstellt und gültig")
reset(); ns["qrk_exec"](card, None)
ok(calls["listen"] == ["QR card"] and "Blinki" in ns["qrk_what"](card, "de"), "QR-Karte: Blinki hört zu (%s)" % ns["qrk_what"](card, "de"))
# ---- listening at the device: one sentence, then the answer
ns["blinki_listen"] = real_listen
said = []
ns["tts_say"] = lambda t, L=None, save=False: said.append(t) or (True, "")
ns["sound_play"] = lambda *a, **k: True
C.update(audio_in="hw:1", blinki_listen_mode="frag")             # the «Frag MoveEye» path (default «Plaudern»: Teil P)
ns["LED"]["alarm"] = True
ok(real_listen("test")[1] == "not now: alarm", "Alarm: hört nicht zu")
ns["LED"]["alarm"] = False; ns["WAKE"]["state"] = "ring"
ok(real_listen("test")[1] == "not now: wake", "Wecker: hört nicht zu")
ns["WAKE"]["state"] = "off"
ok(real_listen("test")[0], "Auslöser: Blinki hört zu")
t = time.time()
for sec, kind in ((0.8, "q"), (1.2, "t"), (1.6, "q")):
    for _k in range(int(sec * 10)):
        a = tone(0.1) if kind == "t" else quiet(0.1)
        ns["blinki_mic_feed"](a, time.time()); time.sleep(0.1)
ok(wait(lambda: not LI["on"], 60), "ein Satz, dann Ende (Stille-Erkennung)")
j = ns["BLINKI"]["jobs"].get(LI["jid"])
ok(j is not None and j["q"] == "Wie laut ist die Sirene?" and j["who"].startswith("device"), "Frage vom Gerät: %s" % (j or {}).get("q"))
ok(wait(lambda: said and "Sirene" in " ".join(said), 30), "Antwort über den Lautsprecher (%d Stücke): %s" % (len(said), [x[:60] for x in said[:1]]))
ok(not LI["buf"], "Ton nach dem Erkennen weg")
ok(real_listen("test")[0], "nochmals zuhören")
ns["blinki_mic_feed"](quiet(0.1), time.time() + 1); time.sleep(0.3)
ns["LED"]["alarm"] = True
ok(wait(lambda: not LI["on"], 5) and LI["msg"] == "stopped: alarm", "Alarm während des Zuhörens: sofort Schluss")
ns["LED"]["alarm"] = False
ns["blinki_stop"]("test")
print("RESULT " + json.dumps(K.FEHLER))
'''


def teil_f(datei, tmp):
    print("F) Stufe 3: Sprechen (Handy-Aufnahme, Auslöser am Gerät, alte Funktionen unverändert)", flush=True)
    make_whisper(tmp)
    env = dict(env_for(tmp, os.path.join(tmp, "fhome")), KI_HIER=HIER, KI_TMP=tmp, FAKE_WHISPER_LOG=os.path.join(tmp, "whisper.log"))
    p = subprocess.run([sys.executable, "-c", TEIL_F, datei], capture_output=True, text=True, env=env, cwd=tmp, timeout=900)
    print("\n".join(x for x in p.stdout.splitlines() if x.startswith("  ")), flush=True)
    m = re.search(r"^RESULT (.*)$", p.stdout, re.M)
    if not m:
        FEHLER.append("Teil F abgebrochen"); print((p.stderr or "")[-3000:]); return
    FEHLER.extend(json.loads(m.group(1)))


# ---- 💬 Plaudern (639zzzzk_blinki_zz_plaudern) ------------------------------------------------------------------------------------
TEIL_P = r'''
import json, os, sys, time, glob
import numpy as np
sys.path.insert(0, os.environ["KI_HIER"])
import ki_test as K
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_ki_p", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
ok = K.ok
C, B, CH = ns["CFG"], ns["BLINKI"], ns["BLINKI_CHAT"]
C.update(lang="de")
logs = []
_lg = ns["log_event"]
def lg(kind, text):
    logs.append(str(text)); return _lg(kind, text)
ns["log_event"] = lg
def wait(f, s):
    t = time.time()
    while time.time() - t < s:
        if f(): return True
        time.sleep(0.05)
    return False
def reqs():
    return [json.loads(x)["req"] for x in open(os.environ["FAKE_LLAMA_LOG"]) if '"req"' in x]
def run(q, cl="p1", L="de", who="test"):
    j, e = ns["blinki_ask"]("plaudern", q, L, ["ALTFRAGE-X", "ALTANTWORT-Y"], who, cl)
    assert j is not None, e
    wait(lambda: j["state"] in ("done", "error", "stopped"), 60)
    return j
# --- the mode
ok([m["m"] for m in ns["blinki_modes"]("admin")][:2] == ["frag", "plaudern"] and ns["blinki_modes"]("admin")[1]["icon"] == "💬", "Art «💬 Plaudern» gleich nach «Frag MoveEye»")
ra = ns["role_allows"]
ok(ra("view", "/api/ki/ask", "POST", {"mode": "plaudern"}) and ra("family", "/api/ki/ask", "POST", {"mode": "plaudern"}) and not ra("kid", "/api/ki/ask", "POST", {"mode": "plaudern"})
   and ra("view", "/api/ki/new", "POST", {}), "Rechte wie «Frag MoveEye»: alle angemeldeten ausser Kinder; «Neu» darf jeder")
j, e = ns["blinki_ask"]("plaudern", "", "de")
ok(j is None and e == "the text is empty", "Plaudern braucht eine Frage")
j, e = ns["blinki_ask"]("plaudern", "Warum ist der Himmel blau?", "de", None, "test", "p0")
ok(j and j["engine"] == "manual" and "Sprachmodell" in j["text"], "ohne Modell: Hinweis «braucht das Sprachmodell» (%s)" % (j or {}).get("text", "")[:50])
ns["blinki_chat_forget"]()
# --- the prompt (offline)
K.fake_model(ns["DATA_DIR"])
j = run("Warum ist der Himmel blau?")
r = reqs()[-1]; sm = r["messages"][0]["content"]
ok(j["state"] == "done" and j["engine"] == "offline" and "blaue" in j["text"], "offline: Antwort vom Modell auf dem Gerät (%s)" % j["text"][:50])
for need, what in (("at most 8 sentences", "kurz (≤ 8 Sätze)"), ("Answer in German", "in der Sprache des Benutzers"), ("say so honestly", "ehrlich, wenn unsicher"),
                   ("without any internet", "offline: kein Internet"), ("nothing about current events", "keine aktuellen Ereignisse"),
                   ("Never give instructions to switch off", "nie Schutz / Alarm / Kamera aus"), ("Health, law and money: only general information", "keine Arzt- / Rechts- / Geldberatung"),
                   ("children from 10", "familientauglich ab 10"), ("Politely refuse adult", "Erwachsenen- / gefährliche Themen höflich ablehnen"), ("«Frag MoveEye»", "verweist für MoveEye auf «Frag MoveEye»")):
    ok(need in sm, "Vorgabe: %s" % what)
ok(r["max_tokens"] == 420 and len(r["messages"]) == 2 and "FACTS FROM THE MANUAL" not in sm and "ALTFRAGE-X" not in json.dumps(r["messages"]), "erste Frage: nur Vorgabe + Frage (kein «prev» der Seite, keine Anleitung)")
v = ns["blinki_job_view"](j)
ok(v["note"] == "Kleines Offline-Modell – es kann sich irren. Mit der Cloud sind die Antworten besser." and v["turns"] == 1, "offline: Hinweis-Zeile in der Antwort (%s)" % v["note"])
# --- the history: the last 4 turns, per conversation
for k_ in range(2, 7):
    run("Frage %d: Wie weit ist der Mond weg?" % k_)
ms = reqs()[-1]["messages"]
qs = [m["content"] for m in ms if m["role"] == "user"]
ok(len(ms) == 1 + 2 * 4 + 1 and qs[0].startswith("Frage 2") and qs[-1].startswith("Frage 6") and [m["role"] for m in ms[1:3]] == ["user", "assistant"],
   "Verlauf: höchstens 4 frühere Fragen + Antworten (%d Nachrichten, älteste «%s»)" % (len(ms), qs[0][:8]))
ok(len(CH["conv"]["web|test|p1"]["turns"]) == 4, "im Speicher: 4 Runden")
run("Hallo", cl="p2")
ok(len(reqs()[-1]["messages"]) == 2, "anderes Gespräch (andere Seite): kein fremder Verlauf")
run("Hallo", cl="p1", who="anna")
ok(len(reqs()[-1]["messages"]) == 2, "anderer Benutzer mit derselben Seiten-Kennung: kein fremder Verlauf")
# --- idle reset: 15 min without a question
ok(ns["BLINKI_CHAT_IDLE_S"] == 900, "Leerlauf-Grenze 15 min")
CH["conv"]["web|test|p1"]["t"] -= 901
jold = [x for x in B["jobs"].values() if x.get("chat") == "web|test|p1"]
for x in jold:
    x["t_end"] -= 901
n_ = ns["blinki_chat_forget"](None, True)
ok(n_ >= 1 and "web|test|p1" not in CH["conv"] and not any(x.get("chat") == "web|test|p1" for x in B["jobs"].values()),
   "nach 15 min ohne Frage: Verlauf und Antworten weg (%d alte Antworten entfernt)" % len(jold))
run("Und jetzt?")
ok(len(reqs()[-1]["messages"]) == 2, "danach: neues Gespräch ohne Verlauf")
run("Noch eine?")
CH["conv"]["web|test|p1"]["t"] -= 901
run("Nach der Pause")
ok(len(reqs()[-1]["messages"]) == 2, "Leerlauf auch ohne Aufräum-Faden: beim nächsten Fragen vergessen")
ok(CH["sweeper"] is not None and CH["sweeper"].is_alive() and CH["sweeper"].daemon, "Aufräum-Faden läuft (alle 30 s)")
# --- «Neu»
run("Eins"); run("Zwei")
ok(ns["blinki_chat_forget"]("web|test|p1") == 1 and not any(x.get("chat") == "web|test|p1" for x in B["jobs"].values()), "«Neu»: Verlauf und Antworten dieses Gesprächs weg")
ok("web|test|p2" in CH["conv"], "«Neu» lässt andere Gespräche stehen")
run("Drei")
ok(len(reqs()[-1]["messages"]) == 2, "nach «Neu»: ohne Verlauf")
# --- nothing on the disk / in the log
secret = "Mein Geheimnis ist Zitronenkuchen"
run(secret)
D = ns["DATA_DIR"]; hits = []
for root, _d, files in os.walk(D):
    for f in files:
        pth = os.path.join(root, f)
        try:
            if os.path.getsize(pth) < 5e6 and b"Zitronenkuchen" in open(pth, "rb").read():
                hits.append(pth)
        except OSError:
            pass
ok(not any("Zitronenkuchen" in x for x in logs) and not hits, "Frage und Antwort nie im Protokoll, nie auf der Karte (%s)" % hits[:2])
ok(any("question (plaudern, offline)" in x for x in logs), "Protokoll nur die Zeile «Blinki: question (plaudern, offline)» (wie bisher)")
# --- the 5 languages
want = {"de": ("Plaudern", "German", "Frag MoveEye", "Kleines Offline-Modell"), "fr": ("Bavarder", "French", "Demande à MoveEye", "Petit modèle"),
        "it": ("Chiacchierare", "Italian", "Chiedi a MoveEye", "Piccolo modello"), "rm": ("Discurrer", "Romansh", "Dumonda MoveEye", "Pitschen model"),
        "en": ("Chat freely", "English", "Ask MoveEye", "Small offline model")}
for L, (lab, lname, frag, note) in want.items():
    j = run("Erzähl mir einen Witz", cl="lang-" + L, L=L)
    sm = reqs()[-1]["messages"][0]["content"]
    lb = next(m["label"] for m in ns["blinki_modes"]("admin", lang=L) if m["m"] == "plaudern")
    v = ns["blinki_job_view"](j)
    ok(lb == lab and ("Answer in " + lname) in sm and ("«%s»" % frag) in sm and v["note"].startswith(note), "%s: «%s», Antwort auf %s, Hinweis «%s…»" % (L, lb, lname, v["note"][:22]))
tx = ns["BKFRAG_TX"]
neu = ["Chat freely", "Ask Blinki anything - knowledge, ideas, small talk", "Ask me anything …", "New conversation", "Small offline model - it can be wrong. The cloud gives better answers.",
       "Blinki remembers the last %n questions, only in memory - gone after %m min without a question.", "At the device Blinki answers as"]
ok(all(k in tx and ns["DE"].get(k) and all(ns["TRX"][L].get(k) for L in ("fr", "it", "rm")) for k in neu) and not [k for k in tx if "ß" in ns["DE"].get(k, "")],
   "neue Texte in 5 Sprachen, Deutsch ohne «ß»")
ok("Plaudern" in ns["HELP_PAGE"] and "Chat freely" in ns["HELP_PAGE"] and all("💬" in ns["HELP_X"][L].split('id="blinki"')[1][:2000] and ("Bavarder", "Chiacchierare", "Discurrer")[i] in ns["HELP_X"][L]
   for i, L in enumerate(("fr", "it", "rm"))), "Anleitung: Plaudern in 5 Sprachen")
# --- the cloud
cl = K.Cloud()
st = ns["blinki_set"]
for k_, v_ in (("blinki_cloud_url", cl.url), ("blinki_cloud_model", "test-model-1"), ("blinki_cloud_key", "sk-test-PLAUDERN-1234567890"), ("blinki_cloud_fmt", "openai"), ("blinki_cloud_on", True)):
    st(k_, v_)
nl = len(reqs())
j = run("Warum ist der Himmel blau?", cl="c1")
body = json.loads(cl.reqs[-1]["raw"]); sm = body["messages"][0]["content"]
v = ns["blinki_job_view"](j)
ok(j["engine"] == "cloud" and j["text"] == "Hallo aus der Cloud." and len(reqs()) == nl and "cannot browse the web" in sm and "without any internet" not in sm and v["note"] == "",
   "Cloud-Schalter ein: Frage an die Cloud (Vorgabe «kann nicht im Netz suchen», kein Offline-Hinweis), nicht ans Gerät")
j = run("Und am Abend?", cl="c1")
body = json.loads(cl.reqs[-1]["raw"])
ok([m["role"] for m in body["messages"]] == ["system", "user", "assistant", "user"] and body["messages"][2]["content"] == "Hallo aus der Cloud.", "Cloud: mit dem Verlauf")
ok(st("blinki_cloud_fmt", "anthropic")[0], "Format Anthropic")
j = run("Noch was?", cl="c1")
body = json.loads(cl.reqs[-1]["raw"])
ok(cl.reqs[-1]["path"] == "/v1/messages" and "chatting with the user" in body["system"] and [m["role"] for m in body["messages"]] == ["user", "assistant", "user", "assistant", "user"],
   "Anthropic Messages: Vorgabe als «system», Verlauf als Nachrichten")
# no answer during an alarm (the cloud too)
ns["blinki_ensure"]()
ns["LED"]["alarm"] = True
ok(wait(lambda: B["held"] == "alarm", 5), "Alarm: Blinki hält an")
n0 = len(cl.reqs)
j, e = ns["blinki_ask"]("plaudern", "Während des Alarms?", "de", None, "test", "c2")
time.sleep(1.5)
ok(j["state"] == "wait" and len(cl.reqs) == n0 and ns["blinki_job_view"](j)["held"] == "alarm", "Cloud: während des Alarms keine Antwort (wartet)")
ns["LED"]["alarm"] = False
ok(wait(lambda: j["state"] == "done", 30) and len(cl.reqs) == n0 + 1, "nach dem Alarm (3 s ruhig): Antwort kommt")
# no network: offline instead, with the hint
st("blinki_cloud_url", "http://127.0.0.1:9/v1"); st("blinki_cloud_fmt", "openai")
j = run("Ohne Netz?", cl="c3")
ok(j["engine"] == "offline" and j["state"] == "done" and ns["blinki_job_view"](j)["note"], "Cloud nicht erreichbar: offline mit Hinweis-Zeile")
st("blinki_cloud_on", False)
# --- speaking: the device trigger asks «Plaudern» when the administrator chooses it
ok(C["blinki_listen_mode"] == "plaudern" and ns["DEFAULTS"]["blinki_listen_mode"] == "plaudern" and "blinki_listen_mode" in ns["USER_SETTINGS_DENY"] and "blinki_listen_mode" in ns["APPKEY_DENY_KEYS"],
   "Auslöser am Gerät: ab Werk «Plaudern» (Besitzer 16.11.2026), nur der Administrator")
ok(st("blinki_listen_mode", "bogus")[0] is False and C["blinki_listen_mode"] == "plaudern", "Auslöser-Art: nur frag / plaudern")
K.fake_stt_model(ns["DATA_DIR"])
said = []
ns["tts_say"] = lambda t, L=None, save=False: said.append(t) or (True, "")
ns["sound_play"] = lambda *a, **k: True
C.update(audio_in="hw:1")
class A_: mute_until = 0.0; sim_t = 0.0
ns["AUDIO"] = A_(); ns["SOUND"]["playing"] = False; ns["WAKE"]["state"] = "off"
sr = 16000
def tone(sec, amp=0.3, f=300.0):
    t = np.arange(int(sec * sr)) / sr
    return (amp * np.sin(2 * np.pi * f * t) * 32767).astype("<i2")
def quiet(sec):
    return (np.random.RandomState(1).randn(int(sec * sr)) * 30).astype("<i2")
LI = ns["LISTEN"]
def listen_once():
    said.clear()
    ok_, e_ = ns["blinki_listen"]("test")
    if not ok_:
        print("  (listen: %s)" % e_)
    for sec, kind in ((0.8, "q"), (1.2, "t"), (1.6, "q")):
        for _k in range(int(sec * 10)):
            ns["blinki_mic_feed"](tone(0.1) if kind == "t" else quiet(0.1), time.time()); time.sleep(0.1)
    wait(lambda: not LI["on"], 60)
    jj = B["jobs"].get(LI["jid"])
    wait(lambda: bool(said), 30)
    return jj
jd = listen_once()
ok(jd is not None and jd["mode"] == "plaudern" and jd["chat"] == "device" and jd["q"] == "Wie laut ist die Sirene?", "Gerät: gesprochene Frage geht an «Plaudern» (%s)" % (jd or {}).get("mode"))
ok(said and "Hinweis" not in " ".join(said) and "Offline-Modell" not in " ".join(said), "Gerät: Antwort über den Lautsprecher (ohne die Hinweis-Zeile): %s" % [x[:50] for x in said[:1]])
jd2 = listen_once()
ok(jd2 is not None and len(jd2["messages"]) == 4, "Gerät: zweite gesprochene Frage mit Verlauf (%d Nachrichten)" % len((jd2 or {}).get("messages", [])))
st("blinki_listen_mode", "frag")
jd3 = listen_once()
ok(jd3 is not None and jd3["mode"] == "frag", "Administrator stellt um: Auslöser fragt «Frag MoveEye»")
ns["LED"]["alarm"] = True
ok(ns["blinki_listen"]("test")[1] == "not now: alarm", "Alarm: hört nicht zu (unverändert)")
ns["LED"]["alarm"] = False
# phone: the recording (webm) -> text -> the question in «Plaudern»
import subprocess
wav = os.path.join(os.environ["KI_TMP"], "rec_p.webm")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=1.5:sample_rate=48000", "-c:a", "libopus", wav], check=True)
txt, e = ns["blinki_stt_upload"](open(wav, "rb").read(), "de")
j = run(txt, cl="phone")
ok(txt and j["state"] == "done" and j["mode"] == "plaudern" and j["q"] == txt, "Handy: Aufnahme -> Text -> Frage in «Plaudern»")
ok(ns["blinki_say"](j["id"], "browser", 0, "de")[1] != "unknown action", "Handy: Antwort vorlesen (Piper im Browser) kennt die Antwort")
# --- the window (tk) has its own conversation
ok(ns["blinki_chat_key"]("window", "tk") == "tk" and ns["blinki_chat_key"]("x", "device") == "device" and ns["blinki_chat_key"]("gast", "abc").startswith("web|gast|"),
   "Gespräche: Gerät, Fenster, Seite (Benutzer + Seite) getrennt")
f = next(f for n, f in ns["SELFTEST_EXTRA"] if "Blinki fragen" in n)
try:
    ok("chat" in f(), "Selbsttest-Funktion mit Plaudern")
except AssertionError as e_:
    ok(False, "Selbsttest-Funktion: %s" % e_)
ns["blinki_stop"]("test")
print("RESULT " + json.dumps(K.FEHLER))
'''


def teil_p(datei, tmp):
    print("P) 💬 Plaudern: Art, Vorgabe, Verlauf (4 Runden, 15 min, «Neu»), Cloud, Sprechen, 5 Sprachen", flush=True)
    make_whisper(tmp)
    env = dict(env_for(tmp, os.path.join(tmp, "phome")), KI_HIER=HIER, KI_TMP=tmp, FAKE_WHISPER_LOG=os.path.join(tmp, "whisper_p.log"),
               FAKE_LLAMA_LOG=os.path.join(tmp, "llama_p.log"))
    p = subprocess.run([sys.executable, "-c", TEIL_P, datei], capture_output=True, text=True, env=env, cwd=tmp, timeout=900)
    print("\n".join(x for x in p.stdout.splitlines() if x.startswith("  ")), flush=True)
    m = re.search(r"^RESULT (.*)$", p.stdout, re.M)
    if not m:
        FEHLER.append("Teil P abgebrochen"); print((p.stderr or "")[-3000:]); return
    FEHLER.extend(json.loads(m.group(1)))


B_TMP = {}


def b_plaudern(pg, name, base, op, bilder):
    """💬 Plaudern in the browser: the chooser, a short chat with the offline hint, «New conversation»"""
    pg.evaluate("() => window.scrollTo(0, 0)")
    chip = pg.locator("#bk-modes button", has_text="Plaudern")
    ok(chip.count() == 1, "%s: Art «💬 Plaudern» (%s)" % (name, chip.inner_text() if chip.count() else "-"))
    chip.click(); pg.wait_for_timeout(300)
    ok(pg.locator("#bk-new").is_visible() and "Plaudern" in pg.locator("#bk-modes button.sel").inner_text() and "Frag mich" in (pg.locator("#bk-q").get_attribute("placeholder") or ""),
       "%s: Plaudern gewählt, «Neues Gespräch», Platzhalter" % name)
    pg.locator("#bk-new").click(); pg.wait_for_timeout(400); weg(pg)
    if name == "handy":
        pg.evaluate("() => { document.getElementById('bk-modes').scrollLeft = 0; window.scrollTo(0, 0); }"); pg.wait_for_timeout(200)
        pg.screenshot(path=os.path.join(bilder, "plaudern_handy_auswahl.png"))
    logp = os.path.join(B_TMP.get("tmp", ""), "llama.log")
    for q in ("Warum ist der Himmel blau?", "Und warum ist er am Abend rot?"):
        n0 = pg.locator(".bkp-act").count()
        pg.locator("#bk-q").fill(q); pg.locator("#bk-go").click()
        pg.wait_for_function("(n) => document.querySelectorAll('.bkp-act').length > n && !document.querySelector('.bkp-say .cur')", arg=n0, timeout=60000)
    pg.wait_for_timeout(400); weg(pg)
    notes = pg.locator(".bkp-note")
    ok(notes.count() == 2 and "Offline-Modell" in notes.last.inner_text() and "Cloud" in notes.last.inner_text(), "%s: Hinweis-Zeile «%s»" % (name, notes.last.inner_text() if notes.count() else "-"))
    rq = [json.loads(x)["req"] for x in open(logp) if '"req"' in x] if os.path.isfile(logp) else []
    ok(rq and [m["role"] for m in rq[-1]["messages"]] == ["system", "user", "assistant", "user"] and "Himmel" in rq[-1]["messages"][1]["content"],
       "%s: zweite Frage mit dem Verlauf der ersten" % name)
    ok("Rot und Orange" in pg.locator(".bkp-say").last.inner_text(), "%s: Antwort im Chat" % name)
    w = pg.evaluate("() => document.documentElement.scrollWidth")
    ok(w <= pg.viewport_size["width"], "%s: keine waagrechte Bildlaufleiste (%d)" % (name, w))
    if name == "handy":
        pg.screenshot(path=os.path.join(bilder, "plaudern_handy_chat.png"))
        pg.locator(".bkp-note").last.scroll_into_view_if_needed(); pg.wait_for_timeout(300); weg(pg)
        pg.screenshot(path=os.path.join(bilder, "plaudern_handy_hinweis.png"))
        pg.screenshot(path=os.path.join(bilder, "plaudern_handy_ganz.png"), full_page=True)
    pg.locator("#bk-new").click(); pg.wait_for_timeout(500)
    ok(pg.locator(".bkp-say").count() == 0 and pg.locator("#bk-intro").is_visible(), "%s: «Neues Gespräch» leert den Chat" % name)
    pg.locator("#bk-q").fill("Erzähl mir einen Witz"); pg.locator("#bk-go").click()
    pg.wait_for_function("() => document.querySelectorAll('.bkp-act').length > 0 && !document.querySelector('.bkp-say .cur')", timeout=60000)
    rq = [json.loads(x)["req"] for x in open(logp) if '"req"' in x] if os.path.isfile(logp) else []
    ok(rq and len(rq[-1]["messages"]) == 2, "%s: nach «Neu» ohne Verlauf (auch im Speicher von MoveEye)" % name)
    if name == "handy":                                 # 🎙 in «Plaudern»: the spoken question goes to this mode
        mic = pg.locator("#bk-mic"); n0 = pg.locator(".bkp-me").count()
        bb = mic.bounding_box()
        pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2); pg.mouse.down(); pg.wait_for_timeout(2200); pg.mouse.up()
        pg.wait_for_function("(n) => document.querySelectorAll('.bkp-me').length > n", arg=n0, timeout=60000)
        pg.wait_for_function("() => !document.querySelector('.bkp-say .cur') && document.querySelectorAll('.bkp-note').length > 0", timeout=60000)
        rq = [json.loads(x)["req"] for x in open(logp) if '"req"' in x]
        ok("chatting with the user" in rq[-1]["messages"][0]["content"] and rq[-1]["messages"][-1]["content"] == "Wie laut ist die Sirene?" and len(rq[-1]["messages"]) == 4,
           "handy: 🎙 in «Plaudern» → Frage an Plaudern, mit Verlauf")
        pg.evaluate("() => { document.getElementById('bk-adm').open = true; }"); pg.wait_for_timeout(300)
        ok(pg.locator("#bk-lm").count() == 1 and pg.locator("#bk-lm").input_value() == "plaudern", "Einstellung «Am Gerät antwortet Blinki als» (ab Werk Plaudern)")
        pg.locator("#bk-lm").scroll_into_view_if_needed(); pg.evaluate("() => window.scrollBy(0, 200)"); pg.wait_for_timeout(300); weg(pg)
        pg.screenshot(path=os.path.join(bilder, "plaudern_handy_geraet.png"))
        pg.evaluate("() => { document.getElementById('bk-adm').open = false; }")
        pg.locator("#bk-new").click(); pg.wait_for_timeout(300)
    pg.locator("#bk-modes button", has_text="Frag MoveEye").click(); pg.wait_for_timeout(200)


def b_extra(pg, name, base, op, bilder):
    """stage 2 + 3 in the browser: the modes, 🎙 hold to talk (Chromium fake microphone), https hint, settings"""
    n = pg.locator("#bk-modes button").count()
    ok(n == 6, "%s: 6 Arten (%s)" % (name, pg.locator("#bk-modes").inner_text().replace("\n", " · ")))
    b_plaudern(pg, name, base, op, bilder)
    pg.locator("#bk-modes button", has_text="Lagerfeuer").click(); pg.wait_for_timeout(300)
    ok(pg.locator("#bk-opts .seg button").count() == 2, "%s: 🔥 Kinder / Erwachsene" % name)
    n0 = pg.locator(".bkp-act").count()                 # b_plaudern ends with «New conversation»: count from here
    pg.locator("#bk-go").click()
    pg.wait_for_function("(n) => document.querySelectorAll('.bkp-act').length > n && !document.querySelector('.bkp-say .cur')", arg=n0, timeout=60000)
    pg.wait_for_timeout(500); weg(pg)
    pg.screenshot(path=os.path.join(bilder, "blinki_%s_geschichte.png" % name))
    if name != "handy":
        return
    pg.locator("#bk-modes button", has_text="Frag MoveEye").click()
    mic = pg.locator("#bk-mic")
    ok(mic.is_visible(), "handy: 🎙 sichtbar (Spracherkennung bereit)")
    nme = pg.locator(".bkp-me").count()
    bb = mic.bounding_box()
    pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2); pg.mouse.down()
    pg.wait_for_timeout(600)
    rec = "rec" in (mic.get_attribute("class") or "") and "loslassen" in pg.locator("#bk-hint").inner_text()
    pg.wait_for_timeout(1800); pg.mouse.up()
    pg.wait_for_function("(n) => document.querySelectorAll('.bkp-me').length > n", arg=nme, timeout=60000)
    q = pg.locator(".bkp-me").last.inner_text()
    ok(rec and "Sirene" in q, "handy: 🎙 gedrückt halten → Aufnahme → Text «%s»" % q.split("\n")[0])
    pg.wait_for_function("() => !document.querySelector('.bkp-say .cur') && document.querySelectorAll('.bkp-act').length > 0", timeout=60000)
    pg.wait_for_timeout(600); weg(pg)
    pg.screenshot(path=os.path.join(bilder, "blinki_handy_sprechen.png"))
    pg.evaluate("() => Object.defineProperty(window, 'isSecureContext', {get: () => false})")
    pg.locator("#bk-mic").dispatch_event("pointerdown")
    pg.wait_for_timeout(300)
    ok("https" in pg.locator("#bk-hint").inner_text(), "ohne https: klarer Hinweis («%s»)" % pg.locator("#bk-hint").inner_text()[:70])
    pg.evaluate("() => { document.getElementById('bk-adm').open = true; document.getElementById('bk-adm').scrollIntoView(); }")
    pg.wait_for_timeout(500); weg(pg)
    txt = pg.locator("#bk-set").inner_text()
    ok("2× klatschen startet Blinki" in txt and "Quittieren" in txt and "Cloud" in txt, "Einstellungen: Cloud, 2× klatschen, Knopf (ab Werk aus)")
    _c, st = http_api(op, base, "/api/ki/state")
    ok(st["state"]["speech"]["clap"] is False and st["state"]["speech"]["btn"] is False, "Klatschen / Knopf für Blinki ab Werk aus")
    pg.screenshot(path=os.path.join(bilder, "blinki_handy_einstellungen.png"))
    # 639zzzzx (from 4.6.0): from «More» Blinki opens in the window «Middle» (iframe) - the page and 🎙 are there too
    pg.evaluate("() => { sessionStorage.setItem('ki-fx', '1'); localStorage.setItem('mw-sheet', 'mid'); }")
    pg.goto(base + "/more", wait_until="domcontentloaded"); pg.wait_for_timeout(1500); weg(pg)
    pg.locator("#m-blinki").click()
    fr = pg.frame_locator(".fx-win iframe")
    fr.locator("#bk-mic.on").wait_for(state="visible", timeout=30000)
    ok("blinki" in (pg.locator(".fx-win iframe").get_attribute("src") or "") and fr.locator("#bk-mic").is_visible(),
       "handy: aus «Mehr» im Fenster «Mitte» (Rahmen) mit 🎙")
    pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(bilder, "blinki_handy_fenster.png"))
    pg.evaluate("() => { sessionStorage.removeItem('ki-fx'); localStorage.setItem('mw-sheet', 'full'); }")
    pg.goto(base + "/blinki", wait_until="domcontentloaded"); pg.wait_for_timeout(1000)
    pg.evaluate("() => window.scrollTo(0, 0)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "ki_bilder"))
    ap.add_argument("--nur", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("KI-Test (Blinki fragen) · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_ki_")
    nur = set(a.nur.split(",")) if a.nur else set("acdefpb")
    try:
        if "a" in nur:
            teil_a(datei, tmp)
        if "c" in nur:
            teil_c(datei, tmp)
        if "d" in nur:
            teil_d(datei, tmp)
        if "e" in nur:
            teil_e(datei, tmp)
        if "f" in nur:
            teil_f(datei, tmp)
        if "p" in nur:
            teil_p(datei, tmp)
        if a.browser and "b" in nur:
            teil_b(datei, tmp, a.bilder, b_extra)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("KI-Test: " + ("OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
