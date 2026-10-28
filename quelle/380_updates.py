#@ Motion Watch – Teil 380: Updates. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Updates: choose a version and switch to it. Source = the URL of a versions.json (e.g. in a GitHub repository) or a folder
#   (e.g. a USB stick). Downloaded versions are kept next to this file, so you can always go back (also without internet).
#   versions.json: {"versions": [{"version": "1.8.7", "file": "webcam_bewegung_2_95_98.py", "url": "https://...", "sha256": "...",
#   "date": "2026-10-22", "notes": "..."}]}  - made with:  python3 webcam_bewegung_X.py --make-manifest <folder> --base-url <url>
# ----------------------------------------------------------------------------
UPD = {"items": [], "msg": "", "busy": False, "time": 0.0, "list_time": ""}
UPD_PROG = {"phase": "", "got": 0, "size": 0, "t0": 0.0, "tp": 0.0}   # progress of an update for the bar on the page (2.95.30)
_RESTART_M = {"todo": True}


def _restart_file():
    return os.path.join(DATA_DIR, "restart_time.json")


def restart_est():
    """how long the last restarts took (from «update» to the first answer of the new program), in seconds"""
    try:
        with open(_restart_file()) as f:
            return max(5.0, min(300.0, float(json.load(f).get("avg") or 25)))
    except (OSError, ValueError, TypeError, AttributeError):
        return 25.0


def restart_measure():
    """called by the first request of a new program: how long did the restart take?"""
    _RESTART_M["todo"] = False
    try:
        with open(_restart_file()) as f:
            d = json.load(f)
        t0 = float(d.get("pending") or 0)
        if not t0:
            return
        dur = time.time() - t0
        d.pop("pending", None)
        if 3 < dur < 300:
            d["avg"] = round(dur if not d.get("avg") else 0.5 * float(d["avg"]) + 0.5 * dur, 1); d["last"] = round(dur, 1)
        with open(_restart_file(), "w") as f:
            json.dump(d, f)
    except (OSError, ValueError, TypeError, AttributeError):
        pass


def _restart_mark():
    try:
        try:
            with open(_restart_file()) as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = {}
        d["pending"] = time.time()
        with open(_restart_file(), "w") as f:
            json.dump(d, f)
    except (OSError, TypeError, AttributeError):
        pass
# Signed updates: every version in versions.json carries a signature made with the developer's secret key (kept offline).
# The program only installs versions whose signature fits this public key - so nobody who gets into the GitHub account can
# push a program onto the devices. (Setting «Also accept unsigned versions» switches the check off, e.g. for own builds.)
UPDATE_PUBKEY = "91d5eab3ab9f6e092d78081ca511144235cb9b22b770c3b1047e011d978bd416"

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


def _installable(it):
    """May this list entry be installed? (already on the Pi, or signed, or unsigned ones are allowed)"""
    return bool(it.get("installed") or it.get("signed") or CFG["update_unsigned"])

VFILE_RE = re.compile(r"^webcam_bewegung_(\d{1,3})_(\d{1,3})_(\d{1,3})\.py$")
VER_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$")


def _vkey(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


def file_version(text):
    """Version of a program file: APP_VERSION (from 1.8.5), else the window title (older versions)."""
    m = (re.search(r'^APP_VERSION = "(\d+\.\d+\.\d+)"', text, re.M)
         or re.search(r'root\.title\("Motion Watch (\d+\.\d+\.\d+)"\)', text))
    return m.group(1) if m else ""


def file_notes(text, ver):
    m = re.search(r"^  \* " + re.escape(ver) + r": (.*?)(?=^  \* \d|^\S|\n\s*\n)", text, re.M | re.S)
    return " ".join(m.group(1).split())[:600] if m else ""


def local_versions(folder):
    out = []
    try:
        names = os.listdir(folder)
    except OSError:
        return out
    for n in names:
        m = VFILE_RE.match(n)
        if not m:
            continue
        p = os.path.join(folder, n)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                head = f.read(400000)
            st = os.stat(p)
        except OSError:
            continue
        v = file_version(head) or ".".join(m.groups())
        out.append({"version": v, "file": n, "path": p, "date": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "notes": file_notes(head, v), "size": st.st_size})
    return out


def _upd_source_ok(src):
    return src == "" or re.match(r"^https://[^\s]{4,400}$", src) is not None or (src.startswith("/") and len(src) < 300)


