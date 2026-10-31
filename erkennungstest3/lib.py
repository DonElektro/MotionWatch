"""Hilfen für den grossen Erkennungstest (nur Steuer-API, nichts am Simulator / an MoveEye geändert)."""
import json, time, urllib.request, os

SIM = "http://127.0.0.1:9283"
MW = "http://127.0.0.1:5183"
OUT = "/tmp/claude-0/erkt3/out/" + os.environ.get("VARIANT", "x")
SHOTS = "/tmp/claude-0/real_shots/erkennung3/" + os.environ.get("VARIANT", "x")
os.makedirs(OUT, exist_ok=True)
os.makedirs(SHOTS, exist_ok=True)


def http_json(url, data=None, timeout=8):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"} if data is not None else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def ctl(**d):
    return http_json(SIM + "/control", d, timeout=20)


def mw_state():
    return http_json(MW + "/api/state", timeout=6).get("state", {})


def mw_messages():
    try:
        return http_json(MW + "/api/messages?src=local", timeout=6)
    except Exception as e:
        return {"err": str(e)}


def frame(path):
    try:
        with urllib.request.urlopen(MW + "/api/frame.jpg", timeout=6) as r:
            b = r.read()
        with open(path, "wb") as f:
            f.write(b)
        return True
    except Exception:
        return False


def load():
    return float(open("/proc/loadavg").read().split()[0])


def wait_load(limit=5.0, maxwait=600):
    t0 = time.time()
    while load() >= limit and time.time() - t0 < maxwait:
        time.sleep(10)
    return load()


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(OUT + "/driver.log", "a") as f:
        f.write(s + "\n")
