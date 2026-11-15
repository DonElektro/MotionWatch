#!/usr/bin/env python3
"""Test für simulator3d/scripts/web_moveeye.gd («Demo beim Host»): der Simulator verbindet sich über EINE WebSocket-Leitung
mit dem Demo-MoveEye (Protokoll MWTUN2, MoveEye Teil 639zzzzw) und beantwortet darüber HTTP wie sonst als Server (net.gd).

Ein kleines Godot-Projekt im Wegwerf-Ordner (web_moveeye.gd + net.gd, Platzhalter für main und die Vorlade-Skripte) gegen ein
nachgemachtes MoveEye in Python (WebSocket-Server):
  Anmeldung «MWTUN2 demo <instanz>» -> «OK», stream_on an; «OPEN 1» + GET /nichts -> Antwort von net.gd (404 JSON) durch die
  Leitung; zwei Kanäle gleichzeitig; «CLOSE»; «TAKEN» -> Zustand «besetzt», keine neue Verbindung, stream_on wie vorher.
python3 werkzeuge/web_moveeye_test.py [--godot BIN]     (ohne Godot: übersprungen)
"""
import argparse, base64, hashlib, os, shutil, socket, subprocess, sys, tempfile, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = []


def ok(c, what):
    print(("  ok  " if c else "  FEHLER  ") + what, flush=True)
    if not c:
        FAIL.append(what)


class Peer:
    def __init__(self, s):
        self.s = s

    def exact(self, n):
        b = b""
        while len(b) < n:
            ch = self.s.recv(n - len(b))
            if not ch:
                raise OSError("zu")
            b += ch
        return b

    def msg(self):
        b0, b1 = self.exact(2)
        n = b1 & 0x7F
        if n == 126:
            n = int.from_bytes(self.exact(2), "big")
        elif n == 127:
            n = int.from_bytes(self.exact(8), "big")
        m = self.exact(4) if b1 & 0x80 else b""
        d = self.exact(n)
        if m:
            d = bytes(x ^ m[i % 4] for i, x in enumerate(d))
        return b0 & 0x0F, d

    def send(self, op, d):
        n = len(d)
        h = bytes([0x80 | op]) + (bytes([n]) if n < 126 else bytes([126]) + n.to_bytes(2, "big"))
        self.s.sendall(h + d)


def server(port, res, ready):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port)); srv.listen(4); srv.settimeout(60)
    ready.set()
    try:
        c, _a = srv.accept()
    except OSError:
        res["accept"] = False; return
    c.settimeout(20)
    h = b""
    while b"\r\n\r\n" not in h:
        h += c.recv(4096)
    lines = h.decode("latin-1").split("\r\n")
    res["path"] = lines[0].split(" ")[1]
    key = next(x.split(":", 1)[1].strip() for x in lines if x.lower().startswith("sec-websocket-key:"))
    acc = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
    c.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + acc + "\r\n\r\n").encode())
    p = Peer(c)
    op, d = p.msg()
    res["hello"] = d.decode()
    p.send(1, b"OK\n")
    time.sleep(1.0)
    p.send(1, b"OPEN 1 8765"); p.send(1, b"OPEN 2 8765")
    p.send(2, (1).to_bytes(4, "big") + b"GET /nichts HTTP/1.1\r\nHost: x\r\n\r\n")
    p.send(2, (2).to_bytes(4, "big") + b"GET /auch_nicht HTTP/1.1\r\nHost: x\r\n\r\n")
    got = {1: b"", 2: b""}
    t0 = time.time()
    while time.time() - t0 < 15 and not all(b"unknown path" in v for v in got.values()):
        op, d = p.msg()
        if op == 2 and len(d) >= 4:
            got[int.from_bytes(d[:4], "big")] = got.get(int.from_bytes(d[:4], "big"), b"") + d[4:]
    res["resp1"], res["resp2"] = got[1].decode("latin-1"), got[2].decode("latin-1")
    p.send(1, b"CLOSE 1")
    time.sleep(1.0)
    p.send(1, b"TAKEN\n")
    time.sleep(1.0)
    try:
        c.settimeout(3)
        op, d = p.msg()
        res["after_taken"] = op
    except OSError:
        res["after_taken"] = "zu"
    srv.settimeout(4)
    try:
        c2, _a = srv.accept(); res["reconnect"] = True; c2.close()
    except OSError:
        res["reconnect"] = False
    c.close(); srv.close()


GD_MAIN = r'''extends SceneTree
var main
var wm
var t := 0.0
var log := []

func _initialize():
	main = Node.new()
	main.set_script(load("res://scripts/main_stub.gd"))
	root.add_child(main)
	main.net = load("res://scripts/net.gd").new()
	main.net.main = main
	main.add_child(main.net)
	wm = load("res://scripts/web_moveeye.gd").new()
	wm.main = main
	main.add_child(wm)
	wm._url = "ws://127.0.0.1:%s/demo/simtun" % OS.get_environment("WM_PORT")

func _process(dt):
	t += dt
	if wm == null or main.net == null:
		print("ZUSTAND kaputt")
		quit()
		return false
	var s = wm.state()
	var line = "%s|%s|%s" % [s["status"], s["kanaele"], main.stream_on]
	if log.is_empty() or log[-1] != line:
		log.append(line)
		print("ZUSTAND " + line)
	if t > 14.0:
		quit()
	return false
'''

GD_STUB_MAIN = '''extends Node
var net
var stream_on := false
var smalltv = null
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--godot", default=os.environ.get("GODOT") or shutil.which("godot") or "")
    a = ap.parse_args()
    if not a.godot or not os.path.exists(a.godot):
        print("Godot fehlt - übersprungen"); return 0
    tmp = tempfile.mkdtemp(prefix="webmoveeye_")
    try:
        sd = os.path.join(tmp, "scripts"); os.makedirs(sd)
        open(os.path.join(tmp, "project.godot"), "w").write('config_version=5\n[application]\nconfig/name="t"\n')
        for f in ("web_moveeye.gd", "net.gd"):
            shutil.copy(os.path.join(ROOT, "simulator3d", "scripts", f), sd)
        for f in ("abgleich.gd", "trailer.gd", "versionen.gd"):
            open(os.path.join(sd, f), "w").write("extends Node\nstatic func label(_v) -> String:\n\treturn \"x\"\n"
                                                 "static func wav_bytes(_a = null, _b = null, _c = null) -> PackedByteArray:\n\treturn PackedByteArray()\n")
        open(os.path.join(sd, "main_stub.gd"), "w").write(GD_STUB_MAIN)
        open(os.path.join(tmp, "t.gd"), "w").write(GD_MAIN)
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        res, ready = {}, threading.Event()
        th = threading.Thread(target=server, args=(port, res, ready), daemon=True); th.start(); ready.wait(5)
        try:
            r = subprocess.run([a.godot, "--headless", "--path", tmp, "-s", "res://t.gd"], capture_output=True, text=True, timeout=90,
                               env=dict(os.environ, WM_PORT=str(port)))
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace") + (e.stderr or b"").decode("utf-8", "replace")
            ok(False, "Godot endet von selbst (nach 90 s abgebrochen)")
        th.join(20)
        zs = [l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("ZUSTAND ")]
        print("   Zustände:", " -> ".join(zs))
        if FAIL:
            print(out[:2500])
        ok("SCRIPT ERROR" not in out and "Parse Error" not in out, "Skripte laden ohne Fehler" + ("" if "SCRIPT ERROR" not in out else ": " + out[-800:]))
        ok(res.get("path") == "/demo/simtun", f"Adresse {res.get('path')}")
        ok(str(res.get("hello", "")).startswith("MWTUN2 demo "), f"Anmeldung: {res.get('hello')}")
        ok(any(z.startswith("verbunden|") and z.endswith("|true") for z in zs), "verbunden, stream_on an")
        ok("404" in res.get("resp1", "") and "unknown path" in res.get("resp1", ""), "Kanal 1: Antwort von net.gd durch die Leitung")
        ok("unknown path" in res.get("resp2", ""), "Kanal 2 gleichzeitig")
        ok(any(z.startswith("verbunden|2") for z in zs), "zwei Kanäle offen")
        ok(zs and zs[-1] == "besetzt|0|false", f"TAKEN -> besetzt, Kanäle zu, stream_on wie vorher ({zs[-1] if zs else '-'})")
        ok(res.get("reconnect") is False, "nach TAKEN keine neue Verbindung von selbst")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FEHLER: " + "; ".join(FAIL) if FAIL else "web_moveeye: alles gut")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
