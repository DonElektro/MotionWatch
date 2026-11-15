#!/usr/bin/env python3
"""MoveEye «Demo beim Host» – fester Startpunkt auf dem Webspace des Besitzers (moveeye.kevlaschef.com/demo/).

Der Host startet nur diese Datei (Startzeile:  python3 demo_start.py ). Sie
  1. sucht in ihrem eigenen Ordner die neueste veröffentlichte, richtig signierte webcam_bewegung_X_Y_Z.py samt
     moveeye_daten_X_Y_Z.zip (Signatur Ed25519 über «MotionWatch|ver|file|sha256» mit dem öffentlichen Schlüssel von
     MoveEye, Teil 380; die ZIP über ZD_SHA256 in der signierten Datei) – fehlt sie, holt sie sie von GitHub;
  2. startet sie mit  --demo --headless --bind 127.0.0.1 --port $PORT --host-modus --url-prefix /demo --config demo_daten
     (MoveEye sperrt dann alles, was nach aussen oder ins System greift: Teil 639zzzzw);
  3. setzt die Demo jede Nacht um 03:30 (Schweizer Zeit) auf Werkseinstellungen zurück (Ordner demo_daten wird geleert,
     MoveEye neu gestartet) – ebenso, wenn der Ordner grösser als 1 GB wird;
  4. schaut alle 6 Stunden nach einer neueren signierten Version, lädt sie NUR in den eigenen Ordner, prüft sie und
     beendet sich dann (der Host startet nach 5 s neu, dann läuft die neue Version). Nie etwas Unsigniertes.
Nur Python-Standardbibliothek. Endet MoveEye von selbst, endet auch diese Datei (der Host startet beides neu).

  python3 demo_start.py            Demo starten und überwachen (das macht der Host)
  python3 demo_start.py --pruefen  nur zeigen, welche Version starten würde (holt sie, wenn nötig), dann Ende
Umgebung: PORT (5000), MW_DEMO_PREFIX (/demo), MW_DEMO_TZ (Europe/Zurich).
Tests: werkzeuge/demo_start_test.py
"""
import hashlib, json, os, re, shutil, signal, subprocess, sys, time, urllib.request
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "demo_daten")
MANIFEST_COPY = os.path.join(HERE, "demo_versions.json")
MANIFEST_URL = "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json"
GH_HOSTS = ("raw.githubusercontent.com", "objects.githubusercontent.com", "github.com")
# the public key of the update signatures - the same as UPDATE_PUBKEY in quelle/380_updates.py (checked by the test)
UPDATE_PUBKEY = "91d5eab3ab9f6e092d78081ca511144235cb9b22b770c3b1047e011d978bd416"
VFILE_RE = re.compile(r"^webcam_bewegung_(\d{1,3})_(\d{1,3})_(\d{1,3})\.py$")
ZFILE_RE = re.compile(r"^moveeye_daten_(\d{1,3})_(\d{1,3})_(\d{1,3})\.zip$")
VER_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$")
UPD_MAX_BYTES = 32 * 1024 * 1024               # like UPD_MAX_BYTES (390)
ZIP_MAX_BYTES = 64 * 1024 * 1024               # like _zd_read (012)
CHECK_EVERY = 6 * 3600
RESET_AT = (3, 30)
DATA_MAX_BYTES = 1024 ** 3                     # the folder of the host has 1.5 GB
KEEP_VERSIONS = 2                              # the running one and the one before


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S") + " demo_start: " + msg, flush=True)


def _ed25519_impl():
    """Ed25519 (RFC 8032, reference algorithm) in pure Python - no extra package needed. Only used for update signatures."""
    p = 2 ** 255 - 19
    q = 2 ** 252 + 27742317777372353535851937790883648493
    d = -121665 * pow(121666, p - 2, p) % p
    I = pow(2, (p - 1) // 4, p)
    H = lambda m: hashlib.sha512(m).digest()

    def add(P, Q):
        A = (P[1] - P[0]) * (Q[1] - Q[0]) % p; B = (P[1] + P[0]) * (Q[1] + Q[0]) % p
        C = 2 * P[3] * Q[3] * d % p; D = 2 * P[2] * Q[2] % p
        E, F, G, Hh = B - A, D - C, D + C, B + A
        return (E * F % p, G * Hh % p, F * G % p, E * Hh % p)

    def mul(s, P):
        Q = (0, 1, 1, 0)
        while s > 0:
            if s & 1:
                Q = add(Q, P)
            P = add(P, P); s >>= 1
        return Q

    def eq(P, Q):
        return (P[0] * Q[2] - Q[0] * P[2]) % p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % p == 0

    def recover_x(y, sign):
        if y >= p:
            return None
        x2 = (y * y - 1) * pow(d * y * y + 1, p - 2, p)
        if x2 == 0:
            return None if sign else 0
        x = pow(x2, (p + 3) // 8, p)
        if (x * x - x2) % p != 0:
            x = x * I % p
        if (x * x - x2) % p != 0:
            return None
        if (x & 1) != sign:
            x = p - x
        return x

    gy = 4 * pow(5, p - 2, p) % p
    gx = recover_x(gy, 0)
    G = (gx, gy, 1, gx * gy % p)

    def compress(P):
        zi = pow(P[2], p - 2, p); x = P[0] * zi % p; y = P[1] * zi % p
        return int.to_bytes(y | ((x & 1) << 255), 32, "little")

    def decompress(s):
        if len(s) != 32:
            return None
        y = int.from_bytes(s, "little"); sign = y >> 255; y &= (1 << 255) - 1
        x = recover_x(y, sign)
        return None if x is None else (x, y, 1, x * y % p)

    def expand(seed):
        h = H(seed); a = int.from_bytes(h[:32], "little")
        a &= (1 << 254) - 8; a |= 1 << 254
        return a, h[32:]

    def public(seed):
        return compress(mul(expand(seed)[0], G))

    def sign(seed, msg):
        a, prefix = expand(seed); A = compress(mul(a, G))
        r = int.from_bytes(H(prefix + msg), "little") % q
        R = compress(mul(r, G))
        h = int.from_bytes(H(R + A + msg), "little") % q
        return R + int.to_bytes((r + h * a) % q, 32, "little")

    def verify(pub, msg, sig):
        if len(pub) != 32 or len(sig) != 64:
            return False
        A = decompress(pub); R = decompress(sig[:32])
        if A is None or R is None:
            return False
        s = int.from_bytes(sig[32:], "little")
        if s >= q:
            return False
        h = int.from_bytes(H(sig[:32] + pub + msg), "little") % q
        return eq(mul(s, G), add(R, mul(h, A)))
    return public, sign, verify


_ED = []


def _sig_msg(version, fname, sha):
    return ("MotionWatch|" + str(version) + "|" + str(fname) + "|" + str(sha).lower()).encode()


def sig_ok(version, fname, sha, sig, pub=None):
    """True when `sig` (hex) is a valid signature of this version / file / checksum."""
    try:
        if not _ED:
            _ED.extend(_ed25519_impl())
        return bool(sha) and _ED[2](bytes.fromhex(pub or UPDATE_PUBKEY), _sig_msg(version, fname, sha), bytes.fromhex(str(sig or "")))
    except (ValueError, TypeError):
        return False


def vkey(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


def sha256_file(path, limit):
    h = hashlib.sha256(); n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
            if n > limit:
                raise ValueError("too big")
            h.update(b)
    return h.hexdigest()


def signed_entries(data):
    """the entries of a versions.json that are correctly signed (bridge entries excluded: the demo needs host mode)"""
    out = {}
    for e in (data.get("versions") or [])[:300] if isinstance(data, dict) else []:
        if not isinstance(e, dict):
            continue
        v, fn, sha = str(e.get("version", "")), str(e.get("file", "")), str(e.get("sha256", "")).lower()[:64]
        if e.get("bridge") or not VER_RE.match(v) or not VFILE_RE.match(fn) or fn != "webcam_bewegung_%s.py" % v.replace(".", "_"):
            continue
        if sig_ok(v, fn, sha, e.get("sig")):
            out[fn] = dict(e, version=v, file=fn, sha256=sha)
    return out


def local_manifests():
    """signed entries from the copy of the last list and (in a checkout of the repository) versions.json next to this file"""
    out = {}
    for p in (os.path.join(HERE, "versions.json"), MANIFEST_COPY):
        try:
            with open(p, encoding="utf-8") as f:
                out.update(signed_entries(json.load(f)))
        except (OSError, ValueError):
            pass
    return out


def file_info(path):
    """APP_VERSION, ZD_FILE, ZD_SHA256 and whether the file knows the host mode"""
    with open(path, encoding="utf-8", errors="replace") as f:
        head = f.read(UPD_MAX_BYTES + 1)
    m = re.search(r'^APP_VERSION = "(\d+\.\d+\.\d+)"', head, re.M)
    zf = re.search(r'^ZD_FILE = "([^"]*)"', head, re.M)
    zs = re.search(r'^ZD_SHA256 = "([0-9a-f]{64}|)"', head, re.M)
    return {"version": m.group(1) if m else "", "zd_file": zf.group(1) if zf else "", "zd_sha": zs.group(1) if zs else "",
            "host": '"--host-modus"' in head and "host_mode_start" in head}


def verify(entry, folder=HERE):
    """'' when the program file of this signed entry and its data zip are in `folder` exactly as released, else the reason"""
    p = os.path.join(folder, entry["file"])
    if not os.path.isfile(p):
        return "missing"
    try:
        if sha256_file(p, UPD_MAX_BYTES) != entry["sha256"]:
            return "checksum of the program file does not match the signed list"
        if not sig_ok(entry["version"], entry["file"], entry["sha256"], entry.get("sig")):
            return "signature not valid"
        fi = file_info(p)
    except (OSError, ValueError) as e:
        return f"cannot read the program file: {e}"
    if fi["version"] != entry["version"]:
        return "version in the file does not match"
    if not fi["host"]:
        return "this version has no host mode (--host-modus)"
    if fi["zd_file"]:
        if not ZFILE_RE.match(fi["zd_file"]):
            return "unexpected name of the data zip"
        zp = os.path.join(folder, fi["zd_file"])
        if not os.path.isfile(zp):
            return "data zip missing"
        try:
            if sha256_file(zp, ZIP_MAX_BYTES) != fi["zd_sha"]:
                return "checksum of the data zip does not match the program"
        except (OSError, ValueError) as e:
            return f"cannot read the data zip: {e}"
    return ""


def pick_local():
    """the newest version in this folder that is signed and complete (entry, path) or (None, reasons)"""
    why = []
    for fn, e in sorted(local_manifests().items(), key=lambda x: vkey(x[1]["version"]), reverse=True):
        w = verify(e)
        if not w:
            return e, os.path.join(HERE, fn)
        if w != "missing":
            why.append(f"{e['version']}: {w}")
    return None, why


def _https_ok(url):
    m = re.match(r"^https://([^/:?#]+)/", str(url))
    return bool(m) and m.group(1).lower() in GH_HOSTS


def http_get(url, limit, dest=None, timeout=60):
    """bytes of an https address of GitHub (at most `limit`), or written to dest"""
    if not _https_ok(url):
        raise ValueError("only https addresses of GitHub")
    req = urllib.request.Request(url, headers={"User-Agent": "MoveEye-demo-start", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if not _https_ok(r.geturl()):
            raise ValueError("redirected away from GitHub")
        n = 0; out = [] if dest is None else None
        f = open(dest, "wb") if dest else None
        try:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                n += len(b)
                if n > limit:
                    raise ValueError("too big")
                if f:
                    f.write(b)
                else:
                    out.append(b)
        finally:
            if f:
                f.close()
    return b"".join(out) if dest is None else n


def fetch_manifest():
    raw = http_get(MANIFEST_URL + "?t=" + str(int(time.time())), 1024 * 1024)
    data = json.loads(raw.decode("utf-8"))
    ents = signed_entries(data)
    if not ents:
        raise ValueError("the list has no signed version")
    tmp = MANIFEST_COPY + ".part"
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, MANIFEST_COPY)
    return data, ents


def _download(url, name, limit, want_sha):
    tmp = os.path.join(HERE, "." + name + ".part")
    try:
        http_get(url, limit, dest=tmp, timeout=300)
        if want_sha and sha256_file(tmp, limit) != want_sha:
            raise ValueError(f"{name}: checksum does not match")
        os.replace(tmp, os.path.join(HERE, name))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def update(current=""):
    """the newest signed version from GitHub into this folder (program file + data zip, both checked). Returns its
    version when a newer one than `current` is ready, else ''."""
    data, ents = fetch_manifest()
    base = MANIFEST_URL.rsplit("/", 1)[0] + "/"
    for fn, e in sorted(ents.items(), key=lambda x: vkey(x[1]["version"]), reverse=True):
        if current and vkey(e["version"]) <= vkey(current):
            return ""
        if not verify(e):
            return e["version"]                          # already here and complete
        url = str(e.get("url") or base + fn)
        log(f"fetching {e['version']} ...")
        _download(url, fn, UPD_MAX_BYTES, e["sha256"])
        fi = file_info(os.path.join(HERE, fn))
        if not fi["host"]:                               # older versions have none either: stop here
            log(f"{e['version']} has no host mode (--host-modus) - not used")
            os.remove(os.path.join(HERE, fn))
            break
        if fi["zd_file"]:
            dz = e.get("data") if isinstance(e.get("data"), dict) else {}
            zurl = str(dz.get("url") or "") if dz.get("file") == fi["zd_file"] else ""
            _download(zurl or url.rsplit("/", 1)[0] + "/" + fi["zd_file"], fi["zd_file"], ZIP_MAX_BYTES, fi["zd_sha"])
        w = verify(e)
        if w:
            log(f"{e['version']} not usable: {w}"); continue
        cleanup(e["version"])
        return e["version"]
    return ""


def cleanup(keep_newest):
    """keep the newest KEEP_VERSIONS program files (+ zips) up to `keep_newest`; only files of this pattern in this folder"""
    vs = sorted({".".join(m.groups()) for m in (VFILE_RE.match(n) for n in os.listdir(HERE)) if m}, key=vkey, reverse=True)
    keep = [v for v in vs if vkey(v) <= vkey(keep_newest)][:KEEP_VERSIONS] + [v for v in vs if vkey(v) > vkey(keep_newest)]
    for v in vs:
        if v in keep:
            continue
        for n in ("webcam_bewegung_%s.py" % v.replace(".", "_"), "moveeye_daten_%s.zip" % v.replace(".", "_")):
            try:
                os.remove(os.path.join(HERE, n)); log(f"removed old {n}")
            except OSError:
                pass


def child_cmd(path):
    return [sys.executable, path, "--demo", "--headless", "--bind", "127.0.0.1", "--port", str(int(os.environ.get("PORT") or 5000)),
            "--host-modus", "--url-prefix", os.environ.get("MW_DEMO_PREFIX", "/demo"), "--config", DATA]


def reset_data():
    """factory settings: the demo folder emptied (only that folder, never anything else)"""
    if os.path.basename(DATA) != "demo_daten" or os.path.dirname(DATA) != HERE:
        raise RuntimeError("unexpected demo folder")
    if os.path.isdir(DATA) and not os.path.islink(DATA):
        shutil.rmtree(DATA, ignore_errors=True)
    os.makedirs(DATA, exist_ok=True)


def dir_bytes(path):
    n = 0
    for root, _d, files in os.walk(path):
        for f in files:
            try:
                n += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return n


def next_reset(now=None):
    """the next 03:30 in Swiss time (or the local time of the host without the time zone data) as a unix time"""
    tz = None
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(os.environ.get("MW_DEMO_TZ", "Europe/Zurich"))
    except Exception:
        pass
    t = datetime.fromtimestamp(now if now is not None else time.time(), tz)
    n = t.replace(hour=RESET_AT[0], minute=RESET_AT[1], second=0, microsecond=0)
    if n <= t:
        n = (n + timedelta(days=1)).replace(hour=RESET_AT[0], minute=RESET_AT[1])
    return n.timestamp()


class Child:
    def __init__(self, path):
        self.path = path; self.p = None

    def start(self):
        os.makedirs(DATA, exist_ok=True)
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        self.p = subprocess.Popen(child_cmd(self.path), cwd=HERE, env=env)
        log(f"MoveEye started: {os.path.basename(self.path)} (PID {self.p.pid})")

    def stop(self):
        if self.p is None or self.p.poll() is not None:
            return
        self.p.terminate()
        try:
            self.p.wait(25)
        except subprocess.TimeoutExpired:
            self.p.kill(); self.p.wait(10)


def main(argv):
    only_check = "--pruefen" in argv
    entry, path = pick_local()
    if entry is None:
        log("no complete signed version here" + (" (" + "; ".join(path) + ")" if path else "") + " - fetching from GitHub")
        for i in range(3):
            try:
                if update():
                    entry, path = pick_local()
                    break
            except Exception as e:
                log(f"fetching failed: {e}"[:300])
            time.sleep(10 * (i + 1))
    if entry is None:
        log("no signed version available - trying again in a minute"); time.sleep(60)
        return 1
    log(f"version {entry['version']} - signature and data zip checked")
    if only_check:
        print(" ".join(child_cmd(path)))
        return 0
    child = Child(path)
    stop = {"now": False}

    def on_term(*_):
        stop["now"] = True
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    t_reset = next_reset(); t_check = time.time() + CHECK_EVERY; t_size = 0.0
    child.start()
    while True:
        time.sleep(1.0)
        if stop["now"]:
            child.stop(); return 0
        rc = child.p.poll()
        if rc is not None:
            log(f"MoveEye ended (code {rc}) - the host starts it again")
            return 0 if rc == 0 else 1
        now = time.time()
        if now >= t_size:
            t_size = now + 600
            if dir_bytes(DATA) > DATA_MAX_BYTES:
                log("demo folder over 1 GB - back to factory settings")
                t_reset = now
        if now >= t_reset:
            log("back to factory settings (every night)")
            child.stop(); reset_data(); child.start()
            t_reset = next_reset(now + 60)
        if now >= t_check:
            t_check = now + CHECK_EVERY
            try:
                new = update(entry["version"])
            except Exception as e:
                new = ""; log(f"update check failed: {e}"[:300])
            if new:
                log(f"new signed version {new} ready - ending, the host starts it")
                child.stop(); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
