#!/usr/bin/env python3
"""Tests der Piper-Stimme (MoveEye Teil 639zzb) ohne Internet und ohne echte Stimme.

Lädt die gebaute MoveEye-Datei (ohne sie zu starten) und prüft:
  1. Laden einer Stimme von einem lokalen Testserver (statt Hugging Face): gültig, verändert (Prüfsumme), fehlt (404),
     zu gross, Fortsetzen nach Abbruch (Range), nicht freigegebene Stimme wird nie geladen.
  2. Den Rechen-Prozess (nice, onnxruntime) mit einem kleinen, hier gebauten ONNX-Modell mit derselben Schnittstelle wie
     Piper (input / input_lengths / scales -> Ton) und einer Ersatz-Lautschrift (MW_PIPER_FAKE_PHON=1; espeak-ng muss
     nicht da sein): WAV entsteht, Tempo wirkt nicht falsch, Zwischenspeicher (zweites Mal ohne Rechnen).
  3. Die Ersatz-Kette: Piper fehlt / Fehler -> alte Stimme; «nur Piper» -> Fehler; «alte Stimme» -> nie Piper.
  4. Die Adresse /api/tts_audio/<id>.wav (Flask-Testclient): liefert die WAV, sonst 404; /api/piper GET / POST.
  5. Lautsprecher-Pfad: sound_play «tts» meldet die Ansage an die Browser (Ereignis «speech») und schickt sie an den Simulator.
  --browser: dazu MoveEye ohne Fenster starten und im Browser (Playwright, iPhone-Grösse) prüfen: Schalter «Ton im Browser»
     (localStorage), ein «speech»-Ereignis holt /api/tts_audio/<id>.wav; --bilder ORDNER legt Bildschirmfotos ab.
  --modell DATEI.onnx --config DATEI.json: zusätzlich eine echte Piper-Stimme rechnen (braucht espeak-ng), Zeit messen.

  python3 werkzeuge/piper_test.py [--datei webcam_bewegung_X_Y_Z.py] [--browser] [--bilder ORDNER]
"""
import argparse
import atexit
import glob
import hashlib
import http.server
import json
import os
import re
import shutil
import struct
import sys
import tempfile
import threading
import time
import wave

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- a tiny ONNX model (protobuf by hand: no «onnx» package needed) ------------------------------------------------------
def _vi(n):
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def _f(num, wt, val):
    key = _vi((num << 3) | wt)
    if wt == 0:
        return key + _vi(val)
    return key + _vi(len(val)) + val


def _s(num, txt):
    return _f(num, 2, txt.encode())


def _tensor(name, dt, dims, raw):
    return b"".join(_f(1, 0, d) for d in dims) + _f(2, 0, dt) + _s(8, name) + _f(9, 2, raw)


def _valinfo(name, elem, dims):
    shape = b"".join(_f(1, 2, (_f(1, 0, d) if isinstance(d, int) else _s(2, d))) for d in dims)
    return _s(1, name) + _f(2, 2, _f(1, 2, _f(1, 0, elem) + _f(2, 2, shape)))


def _node(op, ins, outs, attrs=b""):
    return b"".join(_s(1, i) for i in ins) + b"".join(_s(2, o) for o in outs) + _s(4, op) + attrs


def fake_model():
    """input int64 [1, N] -> sin(0.37 · id) repeated 64 × -> output float [1, 1, 64 N]; input_lengths and scales unused"""
    nodes = [_node("Cast", ["input"], ["xf"], _f(5, 2, _s(1, "to") + _f(20, 0, 2) + _f(3, 0, 1))),
             _node("Mul", ["xf", "k"], ["xm"]), _node("Sin", ["xm"], ["xs"]),
             _node("Unsqueeze", ["xs", "ax"], ["xu"]), _node("Tile", ["xu", "rep"], ["output"])]
    inits = [_tensor("k", 1, [1], struct.pack("<f", 0.37)), _tensor("ax", 7, [1], struct.pack("<q", 1)),
             _tensor("rep", 7, [3], struct.pack("<3q", 1, 1, 64))]
    g = b"".join(_f(1, 2, n) for n in nodes) + _s(2, "fakepiper") + b"".join(_f(5, 2, t) for t in inits)
    g += _f(11, 2, _valinfo("input", 7, [1, "n"])) + _f(11, 2, _valinfo("input_lengths", 7, [1])) + _f(11, 2, _valinfo("scales", 1, [3]))
    g += _f(12, 2, _valinfo("output", 1, [1, 1, "t"]))
    return _f(1, 0, 8) + _s(2, "piper_test") + _f(7, 2, g) + _f(8, 2, _s(1, "") + _f(2, 0, 13))


def fake_config():
    m = {"_": [0], "^": [1], "$": [2], " ": [3], ",": [4], ".": [5], "!": [6], "?": [7]}
    for i, c in enumerate("abcdefghijklmnopqrstuvwxyzäöü"):
        m[c] = [8 + i]
    return json.dumps({"audio": {"sample_rate": 16000}, "espeak": {"voice": "de"}, "phoneme_id_map": m,
                       "inference": {"noise_scale": 0.667, "length_scale": 1, "noise_w": 0.8}, "num_speakers": 1}).encode()


# ---- a local test server (Range like Hugging Face / the CDN) --------------------------------------------------------------
class Srv:
    def __init__(self):
        self.files, self.tamper, self.hits, self.extra = {}, set(), [], b""
        me = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                path = self.path.split("?")[0]
                me.hits.append((path, self.headers.get("Range") or ""))
                data = me.files.get(path)
                if data is None:
                    self.send_response(404); self.end_headers(); return
                if path in me.tamper:
                    data = data[:-1] + bytes([data[-1] ^ 1])
                data = data + me.extra
                start = 0
                m = re.match(r"bytes=(\d+)-", self.headers.get("Range") or "")
                if m and int(m.group(1)) < len(data):
                    start = int(m.group(1))
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
                else:
                    self.send_response(200)
                self.send_header("Content-Length", str(len(data) - start)); self.end_headers()
                self.wfile.write(data[start:])
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d/" % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--modell", default="", help="echte Piper-Stimme (.onnx) zum Rechnen und Zeit messen (braucht espeak-ng)")
    ap.add_argument("--config", default="")
    ap.add_argument("--wav", default="", help="mit --modell: den Beispielsatz hier ablegen")
    a = ap.parse_args()
    mw = a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                           key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    tmp = tempfile.mkdtemp(prefix="mw_piper_test_")
    atexit.register(shutil.rmtree, tmp, True)                   # also after a failed check
    os.environ["MOTIONWATCH_HOME"] = tmp
    g = {"__name__": "piper_test", "__file__": mw}               # the real globals (runpy would hand out a copy)
    with open(mw, encoding="utf-8") as f:
        exec(compile(f.read(), mw, "exec"), g)
    g["DATA_DIR"] = tmp
    g["log_event"] = lambda *x, **k: None
    fails = 0

    def ok(cond, text):
        nonlocal fails
        print(("✓ " if cond else "✗ ") + text, flush=True)
        fails += 0 if cond else 1

    srv = Srv()
    model, config = fake_model(), fake_config()
    vid = "de_DE-test-medium"
    pin = lambda b: {"size": len(b), "sha256": hashlib.sha256(b).hexdigest(), "md5": hashlib.md5(b).hexdigest()}
    g["PIPER_VOICES"][vid] = {"lang": "de", "name": "Test", "quality": "medium", "rev": "r1", "path": "de/test/",
                              "licence": "test", "model": pin(model), "config": {"size": len(config), "md5": hashlib.md5(config).hexdigest()}}
    g["PIPER_BASE"]["url"] = srv.url
    srv.files["/r1/de/test/" + vid + ".onnx"] = model
    srv.files["/r1/de/test/" + vid + ".onnx.json"] = config
    DL = g["PIPER_DL"]

    def dl():
        DL.update(running=False, msg="", got=0)
        return g["piper_download"](vid, wait=True)

    # 1. download -------------------------------------------------------------------------------------------------------------
    ok(not g["piper_installed"](vid), "vorher: nicht geladen")
    srv.tamper.add("/r1/de/test/" + vid + ".onnx")
    r = dl()
    ok(not r[0] and "checksum" in r[1] and not g["piper_installed"](vid) and not os.path.exists(g["piper_paths"](vid)[0] + ".part"),
       f"verändertes Modell abgelehnt, .part gelöscht ({r[1]})")
    srv.tamper.clear()
    srv.files["/r1/de/test/" + vid + ".onnx.json"] = None
    del srv.files["/r1/de/test/" + vid + ".onnx.json"]
    for p_ in g["piper_paths"](vid):
        if os.path.exists(p_):
            os.remove(p_)
    r = dl()
    ok(not r[0] and "404" in r[1] or "Not Found" in r[1], f"fehlende Datei (404) -> nicht geladen ({r[1]})")
    srv.files["/r1/de/test/" + vid + ".onnx.json"] = config
    srv.extra = b"x" * 100
    r = dl()
    ok(not r[0] and ("too large" in r[1] or "size" in r[1]), f"zu grosse Datei abgelehnt ({r[1]})")
    srv.extra = b""
    mp = g["piper_paths"](vid)[0]
    with open(mp + ".part", "wb") as f:
        f.write(model[:len(model) // 2])
    srv.hits.clear()
    r = dl()
    rng = [h for h in srv.hits if h[0].endswith(".onnx")]
    ok(r[0] and g["piper_installed"](vid) and rng and rng[-1][1] == f"bytes={len(model) // 2}-",
       f"Fortsetzen mit Range ({rng[-1][1] if rng else '-'}), danach geladen und geprüft")
    ok(g["piper_check_file"](mp, g["PIPER_VOICES"][vid]["model"])[0], "Prüfung der fertigen Datei: Grösse + sha256 + md5")
    ok(not g["piper_download"]("fr_FR-siwis-medium")[0] or g["piper_pinned"]("fr_FR-siwis-medium"),
       "nicht freigegebene Stimme (ohne Grösse / Prüfsumme) wird nie geladen")
    g["PIPER_VOICES"]["xx_XX-bad-medium"] = {"lang": "de", "name": "x", "quality": "medium", "rev": "r1", "path": "x/", "licence": "-",
                                             "model": {"size": 10, "sha256": ""}, "config": {"size": 10, "md5": "0" * 32}}
    ok(not g["piper_pinned"]("xx_XX-bad-medium") and not g["piper_download"]("xx_XX-bad-medium")[0], "Modell ohne sha256: nie geladen")
    del g["PIPER_VOICES"]["xx_XX-bad-medium"]

    # 2. the worker with the fake model -------------------------------------------------------------------------------------------
    os.environ["MW_PIPER_FAKE_PHON"] = "1"
    g["piper_runtime"] = lambda: (True, True)
    g["CFG"].update(tts_engine="auto", tts_voice_de=vid, lang="de", tts_speed=1.0)
    out = os.path.join(tmp, "a.wav")
    t0 = time.time()
    r = g["piper_synth"]("Achtung, Sie werden gefilmt.", vid, out)
    t1 = time.time() - t0
    n = 0
    if r[0]:
        with wave.open(out) as w:
            n = w.getnframes(); rate = w.getframerate()
    ok(r[0] and n > 1000 and rate == 16000, f"Rechen-Prozess (nice, onnxruntime): WAV {n} Bilder, {t1:.2f} s kalt ({r[1] or r[2]})")
    t0 = time.time()
    r2 = g["piper_synth"]("Hallo.", vid, out)
    ok(r2[0], f"warm: zweiter Satz {time.time() - t0:.2f} s (Rechnen {r2[2].get('ms')} ms)")
    import subprocess
    ps = subprocess.run(["ps", "-o", "ni=", "-p", str(g["PIPER"]["proc"].pid)], capture_output=True, text=True).stdout.strip()
    ok(ps in ("10", "") or int(ps or 0) >= 10, f"Rechen-Prozess läuft mit niedriger Priorität (nice {ps or '?'})")

    # 3. fallback chain + cache ---------------------------------------------------------------------------------------------------
    calls = []
    sample = os.path.join(tmp, "sample.wav")
    shutil.copyfile(out, sample)

    def old(text, lang, path):
        calls.append(text)
        shutil.copyfile(sample, path)
        return True, ""
    g["_tts_make_639zzb"] = old
    t0 = time.time()
    r = g["tts_make"]("Guten Tag, hier ist MoveEye.", "de", out)
    ok(r[0] and g["TTS"]["engine"] == "piper" and not calls, f"auto: spricht mit Piper ({time.time() - t0:.2f} s)")
    sid = g["TTS"]["id"]
    t0 = time.time()
    r = g["tts_make"]("Guten Tag, hier ist MoveEye.", "de", out)
    dt = time.time() - t0
    ok(r[0] and g["TTS"]["id"] == sid and dt < 0.05, f"Zwischenspeicher: gleicher Text ohne Rechnen ({dt * 1000:.1f} ms)")
    g["CFG"]["tts_speed"] = 1.2
    g["tts_make"]("Guten Tag, hier ist MoveEye.", "de", out)
    ok(g["TTS"]["id"] != sid, "anderes Tempo -> neuer Eintrag im Zwischenspeicher")
    g["CFG"]["tts_speed"] = 1.0
    keep = g["piper_synth"]
    g["piper_synth"] = lambda *x, **k: (False, "Piper stopped", {})
    r = g["tts_make"]("Ein neuer Satz.", "de", out)
    ok(r[0] and calls == ["Ein neuer Satz."] and g["TTS"]["engine"] == "old", "Fehler in Piper -> alte Stimme (auto)")
    g["CFG"]["tts_engine"] = "piper"
    r = g["tts_make"]("Noch ein neuer Satz.", "de", out)
    ok(not r[0] and len(calls) == 1, f"«nur Piper»: Fehler statt alter Stimme ({r[1]})")
    g["CFG"]["tts_engine"] = "old"
    g["piper_synth"] = keep
    r = g["tts_make"]("Guten Tag, hier ist MoveEye.", "de", out)
    ok(r[0] and g["TTS"]["engine"] == "old" and len(calls) == 2, "«alte Stimme»: nie Piper (auch nicht aus dem Zwischenspeicher)")
    g["CFG"].update(tts_engine="auto", tts_voice_de="old")
    g["tts_make"]("Test", "de", out)
    ok(g["TTS"]["engine"] == "old", "Stimme «alte Stimme» für Deutsch -> alte Stimme")
    g["CFG"]["tts_voice_de"] = vid
    g["_tts_make_639zzb"] = lambda *x: (False, "no speech program")
    g["piper_runtime"] = lambda: (False, True)
    r = g["tts_make"]("Ganz neu.", "de", out)
    ok(not r[0] and r[1] == "no speech program", "ohne onnxruntime und ohne alte Stimme: klare Meldung")
    g["piper_runtime"] = lambda: (True, True)

    # 4. web addresses ------------------------------------------------------------------------------------------------------------
    from flask import Flask, Response, request
    app = Flask("t")
    g["_smalltv_routes_639zzb"] = lambda *x: None
    reply = lambda o, c=200: Response(json.dumps(o, default=str), status=c, mimetype="application/json")
    body = lambda: request.get_json(force=True, silent=True) or {}
    g["smalltv_routes"](app, reply, body)
    c = app.test_client()
    rr = c.get(f"/api/tts_audio/{sid}.wav")
    ok(rr.status_code == 200 and rr.data[:4] == b"RIFF" and "audio/wav" in rr.content_type, f"/api/tts_audio/<id>.wav liefert die WAV ({len(rr.data)} B)")
    ok(c.get("/api/tts_audio/0123456789abcdef0123.wav").status_code == 404 and c.get("/api/tts_audio/..%2Fx.wav").status_code == 404,
       "unbekannte / falsche Namen: 404")
    j = c.get("/api/piper?lang=de").get_json()
    ok(j["voice"] == vid and any(v["id"] == vid and v["installed"] for v in j["voices"]), "/api/piper: Zustand mit der geladenen Stimme")
    j = c.post("/api/piper", json={"action": "nonsense"}).get_json()
    ok(j["ok"] is False, "/api/piper: unbekannte Aktion abgelehnt")

    # 5. loudspeaker path: browser event + simulator --------------------------------------------------------------------------------
    sent = []
    g["sim_speaker"] = lambda: True
    keep_sp = g["_sound_play_639zzb"]
    g["_sound_play_639zzb"] = lambda *x, **k: (True, "")
    g["speech_to_sim"] = lambda path: sent.append(path) or True
    g["tts_make"]("Guten Tag, hier ist MoveEye.", "de", g["TTS"]["file"])
    n0 = g["ALERTS"]["seq"]
    g["sound_play"]("tts", 2.0, None, reason="test")
    it = g["ALERTS"]["items"][-1]
    ok(g["ALERTS"]["seq"] == n0 + 1 and it["kind"] == "speech" and it["id"] == g["TTS"]["id"] and sent,
       "sound_play «tts»: Ereignis «speech» für die Browser und die WAV an den Simulator")
    g["_sound_play_639zzb"] = keep_sp
    with g["PIPER"]["lock"]:
        g["piper_worker_stop"]()

    # 5b. «Install Piper» installs espeak-ng itself (3.62.1): fake apt-get / sudo in an own PATH -----------------------------------
    fb = os.path.join(tmp, "fakebin"); os.makedirs(fb)
    alog = os.path.join(tmp, "apt.log")
    for tool in ("chmod",):
        w_ = shutil.which(tool)
        if w_:
            os.symlink(w_, os.path.join(fb, tool))
    with open(os.path.join(fb, "apt-get"), "w") as f:
        f.write(f"""#!/bin/sh
printf '%s FRONTEND=%s\\n' "$*" "$DEBIAN_FRONTEND" >> {alog}
case "$FAKE_APT" in
  lock) echo "E: Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 42 (apt)" >&2; exit 100 ;;
  locate) if [ "$1" = update ]; then : > {tmp}/apt_updated; exit 0; fi
          [ -f {tmp}/apt_updated ] || {{ echo "E: Unable to locate package espeak-ng" >&2; exit 100; }} ;;
esac
[ "$1" = install ] && {{ printf '#!/bin/sh\\nexit 0\\n' > {fb}/espeak-ng; chmod 755 {fb}/espeak-ng; }}
exit 0
""")
    with open(os.path.join(fb, "sudo"), "w") as f:
        f.write(f"""#!/bin/sh
printf 'SUDO %s\\n' "$*" >> {alog}
[ "$FAKE_SUDO" = pw ] && {{ echo "sudo: a password is required" >&2; exit 1; }}
[ "$1" = -n ] && shift
exec "$@"
""")
    for x in ("apt-get", "sudo"):
        os.chmod(os.path.join(fb, x), 0o755)
    keep_path, keep_euid = os.environ.get("PATH", ""), getattr(os, "geteuid", None)

    def espeak_case(apt="", sudo_="", root=False):
        for x in ("espeak-ng", "../apt_updated"):
            if os.path.exists(os.path.join(fb, x)):
                os.remove(os.path.join(fb, x))
        if os.path.exists(alog):
            os.remove(alog)
        os.environ.update(PATH=fb, FAKE_APT=apt, FAKE_SUDO=sudo_)
        os.geteuid = (lambda: 0) if root else (lambda: 1000)
        r = g["piper_espeak_install"]()
        lg = open(alog).read() if os.path.exists(alog) else ""
        return r, lg

    def apt_calls(lg):                                     # what apt-get itself was asked (not the lines of the fake sudo)
        return [x for x in lg.splitlines() if not x.startswith("SUDO ")]
    try:
        r, lg = espeak_case()
        ok(r[0] and "SUDO -n " in lg and "install -y --no-install-recommends" in lg and "FRONTEND=noninteractive" in lg
           and os.path.exists(os.path.join(fb, "espeak-ng")),
           "espeak-ng fehlt -> sudo -n apt-get install -y (ohne Rückfrage, noninteractive), danach da")
        r, lg = espeak_case(root=True)
        ok(r[0] and "SUDO" not in lg and "install -y" in lg, "als root: apt-get direkt, ohne sudo")
        r, lg = espeak_case(apt="locate")
        ok(r[0] and sum(x.startswith("install -y") for x in apt_calls(lg)) == 2 and any(x.startswith("update") for x in apt_calls(lg)), "«Unable to locate package» -> einmal apt-get update, dann geht es")
        r, lg = espeak_case(sudo_="pw")
        ok(not r[0] and "password" in r[1] and "sudo apt install espeak-ng" in r[1] and not apt_calls(lg),
           f"sudo will ein Passwort -> nie fragen, klare Meldung ({r[1]})")
        r, lg = espeak_case(apt="lock")
        ok(not r[0] and "busy" in r[1], f"apt beschäftigt -> klare Meldung ({r[1]})")
        os.environ.update(FAKE_SUDO="pw")
        if os.path.exists(os.path.join(fb, "espeak-ng")):
            os.remove(os.path.join(fb, "espeak-ng"))
        g["CFG"]["lang"] = "de"
        keep_rt = g["piper_runtime"]
        g["piper_runtime"] = lambda: (True, False)
        g["PIPER"]["install"] = ""
        g["piper_install"]()
        t_ = time.time() + 20
        while g["PIPER"]["install"] == "running" and time.time() < t_:
            time.sleep(0.1)
        st_ = g["PIPER"]["install"]
        ok(st_.startswith("espeak-ng konnte nicht installiert werden – ") and "Passwort" in st_,
           f"«Piper installieren»: Fehler als klare Meldung im Zustand ({st_})")
        j = g["piper_state"]("de")
        ok(j.get("install") == st_ and "install_step" in j, "/api/piper zeigt die Meldung (install, install_step)")
        g["piper_runtime"] = keep_rt; g["PIPER"]["install"] = ""
    finally:
        os.environ["PATH"] = keep_path
        for x in ("FAKE_APT", "FAKE_SUDO"):
            os.environ.pop(x, None)
        if keep_euid:
            os.geteuid = keep_euid

    # 6. optional: a real Piper voice --------------------------------------------------------------------------------------------
    if a.modell:
        os.environ.pop("MW_PIPER_FAKE_PHON", None)
        rv = "de_DE-real-medium"
        with open(a.modell, "rb") as f:
            mb = f.read()
        with open(a.config, "rb") as f:
            cb = f.read()
        g["PIPER_VOICES"][rv] = {"lang": "de", "name": "real", "quality": "medium", "rev": "-", "path": "-/", "licence": "-",
                                 "model": {"size": len(mb), "sha256": hashlib.sha256(mb).hexdigest()}, "config": {"size": len(cb), "md5": hashlib.md5(cb).hexdigest()}}
        del mb, cb
        m_, c_ = g["piper_paths"](rv)
        os.symlink(os.path.abspath(a.modell), m_); os.symlink(os.path.abspath(a.config), c_)
        with open(os.path.join(tmp, "piper", rv + ".ok"), "w") as f:
            f.write(g["PIPER_VOICES"][rv]["model"]["sha256"])
        wav = a.wav or os.path.join(tmp, "echt.wav")
        t0 = time.time()
        r = g["piper_synth"]("Achtung, Sie werden gefilmt.", rv, wav)
        t_kalt = time.time() - t0
        t0 = time.time()
        r2 = g["piper_synth"]("Bitte Abstand halten.", rv, os.path.join(tmp, "b.wav"))
        ok(r[0] and r2[0], f"echte Stimme: kalt {t_kalt:.2f} s (Dauer {r[2].get('dur')} s), warm {time.time() - t0:.2f} s "
                           f"(Rechnen {r2[2].get('ms')} ms für {r2[2].get('dur')} s Ton) {r[1]}")
        with g["PIPER"]["lock"]:
            g["piper_worker_stop"]()

    if a.browser:
        fails += browser(mw, sid, g["piper_cache_path"](sid), a.bilder, ok)
    shutil.rmtree(tmp, ignore_errors=True)
    print("OK" if not fails else f"{fails} Fehler")
    sys.exit(1 if fails else 0)


def browser(mw, sid, wav, bilder, ok):
    """MoveEye ohne Fenster + Playwright (iPhone 390 × 844): Schalter, Ereignis «speech» -> /api/tts_audio/<id>.wav"""
    import base64
    import socket
    import subprocess
    import urllib.request
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="mw_piper_web_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "ui_simple": False,
          "tours_auto": False, "tips_level": "off"}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    for d_ in (cfg, tmp):                                           # the announcement of the first part, ready for the browser
        os.makedirs(os.path.join(d_, "piper", "cache"), exist_ok=True)
        shutil.copyfile(wav, os.path.join(d_, "piper", "cache", sid + ".wav"))
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    pw_ = "Piper-" + base64.b16encode(os.urandom(4)).decode().lower()
    log = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, mw, "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", pw_], stdout=log, stderr=subprocess.STDOUT, cwd=tmp,
                         env=dict(os.environ, MOTIONWATCH_HOME=tmp))
    base = "http://127.0.0.1:%d" % port
    fails = 0
    try:
        for _i in range(240):
            try:
                urllib.request.urlopen(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": pw_})
            pg = ctx.new_page()
            errs, req = [], []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.on("response", lambda r: req.append((r.url, r.status)) if "/api/tts_audio/" in r.url else None)
            pg.goto(base + "/settings?open=sec%3ALoudspeaker", wait_until="domcontentloaded")
            pg.wait_for_timeout(3500)
            pg.evaluate("() => document.querySelectorAll('#g2-ov, .g2-ov, .prt-wiz').forEach(x => { let o = x; while (o.parentElement && o.parentElement !== document.body) o = o.parentElement; o.remove(); })")
            box = pg.locator("#piper-box")
            n_box = box.count()
            if not n_box:
                pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
                pg.evaluate("""() => { const h = [...document.querySelectorAll('h2,h3,summary,.sec-h,button')].find(x => /Lautsprecher/.test(x.textContent));
                               if (h) h.click(); }""")
                pg.wait_for_timeout(1500); n_box = box.count()
            ok(n_box == 1, "Karte «Piper-Stimme» unter Lautsprecher da")
            if n_box:
                box.scroll_into_view_if_needed()
                pg.evaluate("() => document.querySelectorAll('#g2-ov, .g2-ov, .prt-wiz').forEach(x => { let o = x; while (o.parentElement && o.parentElement !== document.body) o = o.parentElement; o.remove(); })")   # a tour over the page
                pg.locator("#piper-browser").click()
                pg.wait_for_timeout(300)
                ls = pg.evaluate("() => JSON.parse(localStorage.getItem('mw-sound') || '{}').speak")
                ok(ls is True, "Schalter «🔊 Ton im Browser» gespeichert (localStorage mw-sound.speak)")
                if bilder:
                    os.makedirs(bilder, exist_ok=True)
                    pg.wait_for_timeout(400)
                    box.screenshot(path=os.path.join(bilder, "piper_karte.png"))
                    tx = pg.locator("#piper-box").locator("xpath=..")          # the announcement box with the card
                    tx.screenshot(path=os.path.join(bilder, "piper_ansage.png"))
                    sel = pg.locator('select[data-key="tts_engine"]')
                    if sel.count():
                        sel.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                        pg.screenshot(path=os.path.join(bilder, "piper_einstellungen.png"))
            pg.mouse.click(10, 300)                                   # a tap: Web Audio may play
            pg.evaluate("id => window.mwSpeak && mwSpeak(id)", sid)
            pg.wait_for_timeout(800)
            ok(any(sid in u and c == 200 for u, c in req), f"Ansage im Browser: holt /api/tts_audio/<id>.wav ({req[-1][1] if req else '-'})")
            dec = pg.evaluate("""async id => { const c = new (window.AudioContext || window.webkitAudioContext)();
                const b = await (await fetch('/api/tts_audio/' + id + '.wav')).arrayBuffer(); const a = await c.decodeAudioData(b); return a.duration; }""", sid)
            ok(dec and dec > 0.1, f"der Browser kann die WAV abspielen (Web Audio: {dec:.2f} s)")
            if bilder:
                pg.locator("#btn-sound").click(); pg.wait_for_timeout(500)
                pg.screenshot(path=os.path.join(bilder, "piper_glocke.png"))
            ok(not errs, "keine JavaScript-Fehler" + (": " + "; ".join(errs[:3]) if errs else ""))
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(timeout=20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    return fails


if __name__ == "__main__":
    main()
