"""The connection to Motion Watch over the network.

Motion Watch is not part of the simulator: it runs as its own program (on the Pi or on any PC) and
  * reads the pictures from the simulator (protocol, port 8767) and sends its servo / light positions (POST /state),
  * shows what it sees on its own web page. The simulator reads that page (/api/state) for the scoreboard and the
    tests, and switches things like a user would (/api/set, /api/arm, /api/move).

Which Motion Watch: the address set in the panel / with --mw, otherwise the device that sends POST /state to the
simulator - with the scheme (http / https) and port of its web page, which Motion Watch sends along (mw_scheme, mw_port).

https: Motion Watch has a self-signed certificate. The simulator remembers its fingerprint at the first contact
(data/mw_certs.json) and from then on accepts only that certificate. If it changes, the link stops until the user
accepts the new one (tab 🔗 Motion Watch)."""
import base64
import hashlib
import http.client
import json
import os
import ssl
import threading
import time
from collections import deque
from urllib import error as _er
from urllib.parse import urlsplit

DEFAULT_WEB_PORT = 5000

LINK = {"url": "", "password": "", "client_ip": "", "scheme": "http", "port": DEFAULT_WEB_PORT, "data": None, "t": 0.0,
        "error": "no Motion Watch yet", "busy": False, "det": None, "det_t": 0.0, "cert_new": ""}
LOG = deque(maxlen=300)                 # what the simulator did (the program's own log is on its web page)
CERTS = {"file": "", "pins": None}      # host:port -> sha256 of the certificate (trust on first use)
_lock = threading.Lock()
_NO_CA = ssl.create_default_context()   # self-signed: no CA check - the fingerprint check below replaces it
_NO_CA.check_hostname = False
_NO_CA.verify_mode = ssl.CERT_NONE


class CertChanged(OSError):
    pass


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


def note_client(ip, raw=None):
    """The protocol server got POST /state from this address. raw = the JSON as sent: where Motion Watch's web page is
    (mw_scheme, mw_port) and what it detects right now (det)."""
    raw = raw if isinstance(raw, dict) else {}
    scheme = raw.get("mw_scheme") if raw.get("mw_scheme") in ("http", "https") else LINK["scheme"]
    try:
        port = int(raw.get("mw_port") or LINK["port"])
    except (TypeError, ValueError):
        port = LINK["port"]
    if isinstance(raw.get("det"), dict):
        LINK["det"] = raw["det"]; LINK["det_t"] = time.time()
    if ip and (ip, scheme, port) != (LINK["client_ip"], LINK["scheme"], LINK["port"]):
        LINK.update(client_ip=ip, scheme=scheme, port=port)
        log(f"Motion Watch sends its state from {ip} - web page {scheme}://{ip}:{port}")


def address():
    if LINK["url"]:
        return LINK["url"]
    if LINK["client_ip"]:
        return f"{LINK['scheme']}://{LINK['client_ip']}:{LINK['port']}"
    return ""


def use_cert_file(path):
    CERTS["file"] = path; CERTS["pins"] = None


def _pins():
    if CERTS["pins"] is None:
        try:
            with open(CERTS["file"], encoding="utf-8") as f:
                CERTS["pins"] = dict(json.load(f))
        except (OSError, ValueError, TypeError):
            CERTS["pins"] = {}
    return CERTS["pins"]


def _check_cert(where, der):
    """Trust on first use: remember the fingerprint, afterwards accept only that certificate."""
    fp = hashlib.sha256(der or b"").hexdigest()
    pins = _pins()
    if where not in pins:
        pins[where] = fp
        log(f"https: certificate of Motion Watch {where} remembered (sha256 {fp[:16]}…)")
        if CERTS["file"]:
            try:
                os.makedirs(os.path.dirname(CERTS["file"]), exist_ok=True)
                with open(CERTS["file"], "w", encoding="utf-8") as f:
                    json.dump(pins, f, indent=1)
            except OSError:
                pass
    elif pins[where] != fp:
        LINK["cert_new"] = where
        raise CertChanged("the certificate of Motion Watch has changed - if Motion Watch made a new one, accept it in tab "
                          "🔗 Motion Watch")
    LINK["cert_new"] = ""


def accept_new_cert():
    """The user confirmed: Motion Watch really has a new certificate. Forget the old one (remembered at the next contact)."""
    where = LINK["cert_new"]
    if where:
        _pins().pop(where, None)
        if CERTS["file"]:
            try:
                with open(CERTS["file"], "w", encoding="utf-8") as f:
                    json.dump(_pins(), f, indent=1)
            except OSError:
                pass
        log(f"https: new certificate of Motion Watch {where} accepted")
        LINK["cert_new"] = ""


def _request(path, body=None, timeout=3.0):
    base = address()
    if not base:
        raise OSError("no Motion Watch address yet")
    u = urlsplit(base)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    if LINK["password"]:
        headers["Authorization"] = "Basic " + base64.b64encode(("mw:" + LINK["password"]).encode()).decode()
    if u.scheme == "https":
        conn = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=timeout, context=_NO_CA)
        conn.connect()
        _check_cert(f"{u.hostname}:{u.port or 443}", conn.sock.getpeercert(binary_form=True))
    else:
        conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    try:
        conn.request("POST" if data is not None else "GET", (u.path or "") + path, body=data, headers=headers)
        r = conn.getresponse()
        raw = r.read()
        if r.status >= 400:
            raise _er.HTTPError(base + path, r.status, r.reason, r.headers, None)
        return json.loads(raw or b"{}")
    except http.client.HTTPException as e:
        raise OSError(f"bad answer: {e!r}") from e
    finally:
        conn.close()


def _poll():
    while True:
        if address():
            try:
                d = _request("/api/state")
                with _lock:
                    LINK["data"] = d; LINK["t"] = time.time(); LINK["error"] = ""
            except _er.HTTPError as e:
                LINK["error"] = "wrong or missing password" if e.code == 401 else f"web page answered {e.code}"
            except CertChanged as e:
                LINK["error"] = str(e)
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
    if key in ("persons", "present") and detected() is not None:      # fresher: sent with every POST /state
        return detected().get(key, default)
    s = _part("state") or {}
    return s.get(key, default)


def detected():
    """What Motion Watch detects right now (persons, present, armed, noise), sent along with POST /state - or None."""
    return LINK["det"] if LINK["det"] is not None and time.time() - LINK["det_t"] < 1.5 else None


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
