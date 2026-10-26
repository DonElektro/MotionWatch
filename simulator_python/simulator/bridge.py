"""The connection to Motion Watch over the network.

Motion Watch is not part of the simulator: it runs as its own program (on the Pi or on any PC) and
  * reads the pictures from the simulator (protocol, port 8765) and sends its servo / light positions (POST /state),
  * shows what it sees on its own web page. The simulator reads that page (/api/state) for the scoreboard and the
    tests, and switches things like a user would (/api/set, /api/arm, /api/move).

Which Motion Watch: the address set in the panel / with --mw, otherwise the device that sends POST /state to the
simulator (its web page on port 5000)."""
import base64
import json
import threading
import time
from collections import deque
from urllib import error as _er
from urllib import request as _rq

DEFAULT_WEB_PORT = 5000

LINK = {"url": "", "password": "", "client_ip": "", "data": None, "t": 0.0, "error": "no Motion Watch yet", "busy": False}
LOG = deque(maxlen=300)                 # what the simulator did (the program's own log is on its web page)
_lock = threading.Lock()


def configure(url=None, password=None):
    """url "" = automatic (the device that sends its state to the simulator)."""
    with _lock:
        if url is not None:
            url = url.strip().rstrip("/")
            if url and "://" not in url:
                url = "http://" + url
            if url and url.count(":") == 1:            # no port given: Motion Watch's default web port
                url += f":{DEFAULT_WEB_PORT}"
            LINK["url"] = url
        if password is not None:
            LINK["password"] = password
        LINK["data"] = None; LINK["t"] = 0.0


def note_client(ip):
    """The protocol server got POST /state from this address."""
    if ip and ip != LINK["client_ip"]:
        LINK["client_ip"] = ip
        log(f"Motion Watch sends its state from {ip}")


def address():
    if LINK["url"]:
        return LINK["url"]
    if LINK["client_ip"]:
        return f"http://{LINK['client_ip']}:{DEFAULT_WEB_PORT}"
    return ""


def _request(path, body=None, timeout=3.0):
    base = address()
    if not base:
        raise OSError("no Motion Watch address yet")
    data = json.dumps(body).encode() if body is not None else None
    req = _rq.Request(base + path, data=data, headers={"Content-Type": "application/json"} if data else {})
    if LINK["password"]:
        req.add_header("Authorization", "Basic " + base64.b64encode(("mw:" + LINK["password"]).encode()).decode())
    with _rq.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def _poll():
    while True:
        if address():
            try:
                d = _request("/api/state")
                with _lock:
                    LINK["data"] = d; LINK["t"] = time.time(); LINK["error"] = ""
            except _er.HTTPError as e:
                LINK["error"] = "wrong or missing password" if e.code == 401 else f"web page answered {e.code}"
            except (OSError, ValueError) as e:
                LINK["error"] = f"not reachable ({getattr(e, 'reason', e)})"
        else:
            LINK["error"] = "no Motion Watch yet - it connects by itself, or enter its address"
        time.sleep(0.25)


def start():
    if not LINK["busy"]:
        LINK["busy"] = True
        threading.Thread(target=_poll, daemon=True, name="sim-mw-link").start()


def ready():
    return LINK["data"] is not None and time.time() - LINK["t"] < 4.0


def status():
    if ready():
        return f"connected: {address()}  (Motion Watch {state('version', '?')})"
    return LINK["error"]


def _part(name):
    d = LINK["data"]
    return d.get(name) if ready() and isinstance(d, dict) else None


def cfg(key, default=None):
    c = _part("cfg") or {}
    return c.get(key, default)


def state(key, default=None):
    s = _part("state") or {}
    return s.get(key, default)


def relays():
    """Motion Watch's relays with their current on / off state."""
    rs = [dict(r) for r in (_part("relays") or [])]
    on = state("relay_states", []) or []
    for i, r in enumerate(rs):
        r["on"] = bool(on[i]) if i < len(on) else False
    return rs


def waypoints():
    return [list(w) for w in (_part("waypoints") or [])]


def events(n=40):
    return list(_part("events") or [])[:n]


def is_armed():
    return state("arm_state") in ("armed", "arming")


def set_cfg(key, value, note=True):
    """Change a Motion Watch setting like its web page does. Returns True when it was taken."""
    if cfg(key) == value:
        return True
    try:
        r = _request("/api/set", {"key": key, "value": value})
    except (OSError, ValueError) as e:
        log(f"setting {key} failed: {e}")
        return False
    if r.get("ok"):
        c = _part("cfg")
        if c is not None:
            c[key] = value
        if note:
            log(f"setting {key} -> {value!r}")
        return True
    log(f"setting {key} refused: {r.get('error')}")
    return False


def arm(now=True):
    return _post("/api/arm", {"action": "arm_now" if now else "arm"})


def disarm():
    return _post("/api/arm", {"action": "disarm"})


def centre():
    return _post("/api/move", {"dir": "center"})


def _post(path, body):
    try:
        return bool(_request(path, body).get("ok"))
    except (OSError, ValueError) as e:
        log(f"{path} failed: {e}")
        return False


def log(text):
    LOG.appendleft(time.strftime("%H:%M:%S ") + text)
