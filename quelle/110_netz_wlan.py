#@ Motion Watch – Teil 110: Netz, WLAN suchen und verbinden, QR-Codes. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Network: Wi-Fi signal (e.g. a phone hotspot) and whether the internet can be reached (push messages need it)
#   /proc/net/wireless every 2 s (signal level), "iw dev <if> link" every 15 s (network name, speed), internet check every 30 s
# ----------------------------------------------------------------------------
def _proc_wireless():
    out = {}
    try:
        with open("/proc/net/wireless") as f:
            lines = f.read().splitlines()[2:]
    except OSError:
        return out
    for ln in lines:
        if ":" not in ln:
            continue
        iface, rest = ln.split(":", 1); parts = rest.split()
        try:
            link, level = float(parts[1].rstrip(".")), float(parts[2].rstrip("."))
        except (IndexError, ValueError):
            continue
        if level > 63:                                   # some drivers report an unsigned byte (200 = -56 dBm)
            level -= 256
        out[iface.strip()] = (link, level)
    return out


def _wifi_ifaces():
    names = sorted(set(_proc_wireless()) | {os.path.basename(os.path.dirname(p)) for p in glob.glob("/sys/class/net/*/wireless")})
    return names


def _iw_link(iface):
    """-> dict(ssid, dbm, rate, connected) from 'iw', or None when iw is missing."""
    if shutil.which("iw") is None:
        return None
    try:
        r = subprocess.run(["iw", "dev", iface, "link"], capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.SubprocessError):
        return None
    txt = r.stdout
    if "Not connected" in txt or not txt.strip():
        return {"ssid": "", "dbm": None, "rate": "", "connected": False}
    m_ss = re.search(r"SSID:\s*(.+)", txt); m_sig = re.search(r"signal:\s*(-?\d+)", txt); m_rate = re.search(r"tx bitrate:\s*([\d.]+\s*\S+)", txt)
    return {"ssid": m_ss.group(1).strip()[:40] if m_ss else "", "dbm": int(m_sig.group(1)) if m_sig else None,
            "rate": m_rate.group(1) if m_rate else "", "connected": True}


def wifi_pct(dbm):
    return int(max(0, min(100, 2 * (dbm + 100)))) if dbm is not None else 0


class NetMonitor:
    def __init__(self):
        self.iw = {}; self.weak = False; self.was = None; self.ip = ""; self.announced = None; self.t_start = time.time()
        self.key = None; self.changed_at = 0.0; self.recheck = False
        self.hist = deque(maxlen=150)                    # one value every 2 s = the last 5 minutes (None = no connection)
        threading.Thread(target=self.loop, daemon=True).start()
        threading.Thread(target=self.online_loop, daemon=True).start()

    def sample(self, n):
        if n % 8 == 0 or WIFI.get("refresh") or WIFI.get("hs_busy"):
            try:
                hotspot_refresh()
            except Exception:
                pass
        if STATE["hotspot"].get("on") and not DUAL["on"]:   # the Pi is the access point itself: no signal to measure
            STATE["wifi"] = {"iface": WIFI["iface"], "ssid": STATE["hotspot"]["ssid"], "dbm": None, "pct": 0, "rate": "", "connected": False,
                             "ip": STATE["hotspot"]["ip"], "ap": True}
            self.was = None; WIFI["refresh"] = False
            return
        ifaces = _wifi_ifaces()
        if not ifaces:
            STATE["wifi"] = None; return
        proc = _proc_wireless()
        iface = next((i for i in ifaces if i in proc and proc[i][1] < 0), ifaces[0])
        if DUAL["on"] and DUAL["up"] in ifaces:
            iface = DUAL["up"]
        refresh = WIFI.get("refresh") or WIFI.get("busy")
        if refresh:
            WIFI["refresh"] = False
        if n % 8 == 0 or iface not in self.iw or refresh:
            info = _iw_link(iface)
            if info is not None:
                self.iw[iface] = info
        iw = self.iw.get(iface) or {}
        dbm = int(proc[iface][1]) if iface in proc and proc[iface][1] < 0 else iw.get("dbm")
        connected = (dbm is not None) if not iw else bool(iw.get("connected")) and dbm is not None
        if connected and (n % 8 == 0 or not self.ip or refresh):
            self.ip = wifi_ip(iface)
        elif not connected:
            self.ip = ""
        STATE["wifi"] = {"iface": iface, "ssid": iw.get("ssid", "") if connected else "", "dbm": dbm if connected else None,
                         "pct": wifi_pct(dbm) if connected else 0, "rate": iw.get("rate", "") if connected else "", "connected": connected,
                         "ip": self.ip}
        self.hist.append(dbm if connected else None)
        STATE["wifi_hist"] = list(self.hist)
        self.announce(connected, iw.get("ssid", ""))
        if connected != self.was:
            if self.was is not None:
                log_event("sys", f"Wi-Fi {iface}: " + (f"connected ({dbm} dBm)" if connected else "connection lost"))
            self.was = connected
        if connected:
            if not self.weak and dbm < -77:
                self.weak = True; log_event("sys", f"Wi-Fi signal weak: {dbm} dBm")
            elif self.weak and dbm > -72:
                self.weak = False; log_event("sys", f"Wi-Fi signal ok again: {dbm} dBm")

    def announce(self, connected, ssid):
        """Push message with the address of the page when the Pi is in a (new) network - on a phone hotspot nobody knows
        the address otherwise. Waits until the internet works, because the message needs it."""
        key = (ssid, self.ip)
        if key != self.key:                              # new network / address: check the internet again right away
            self.key = key; self.changed_at = time.time(); self.recheck = True
        net = STATE["net"]
        if not (connected and self.ip and CFG["notify_network"]) or net.get("online") is not True or net.get("t", 0) < self.changed_at:
            return
        if key == self.announced or time.time() - self.t_start < 8:
            return
        w = WATCH_REF.get("w")
        if w is None:
            return
        addr = page_address(self.ip)
        de = CFG["lang"] == "de"
        txt = trf("MoveEye is online in Wi-Fi {ssid}: {addr}", ssid=ssid or "?", addr=addr)
        if w.notifier.info(txt, addr):
            self.announced = key
            log_event("sys", f"Address sent as push message: {addr}")

    def loop(self):
        n = 0
        while True:
            try:
                self.sample(n)
            except Exception as e:
                STATE["wifi"] = None; log_event("sys", f"Wi-Fi monitor error: {e}"); time.sleep(30)
            n += 1
            time.sleep(2.0)

    def online_loop(self):
        import socket
        while True:
            res = {"online": False, "ms": None}
            # several ways out: some routers / filters block port 53 to outside servers, but never normal web traffic (443)
            targets = []
            try:
                from urllib.parse import urlparse
                h = urlparse(CFG["notify_url"].strip()).hostname if CFG["notify_url"].strip() else ""
                if h:
                    targets.append((h, 443))                 # the push server itself: exactly what matters
            except ValueError:
                pass
            targets += [("1.1.1.1", 443), ("8.8.8.8", 443), ("1.1.1.1", 53), ("8.8.8.8", 53)]
            for host, port in targets:
                t0 = time.time()
                try:
                    socket.create_connection((host, port), timeout=3).close()
                    res = {"online": True, "ms": int((time.time() - t0) * 1000)}
                    break
                except Exception:                      # 2.95.33: also UnicodeError (mistyped push address) - must not end the loop
                    pass
            try:
                if drill_active("net"):                  # 2.96.6: drill «Wi-Fi / internet gone» (141)
                    res = {"online": False, "ms": None, "drill": True}
            except NameError:
                pass
            if STATE["net"].get("online") is not None and res["online"] != STATE["net"]["online"]:
                log_event("sys", "Internet reachable again" if res["online"] else "Internet not reachable (push messages cannot be sent)")
            res["t"] = time.time()
            STATE["net"] = res
            beat("online", 120, "Internet check")
            self.recheck = False
            for _ in range(30 if res["online"] else 10):     # every 30 s (10 s while offline), at once after a network change
                if self.recheck:
                    break
                time.sleep(1.0)


# ----------------------------------------------------------------------------
# Wi-Fi management: search networks (phone hotspots), connect, save for automatic connection, forget.
#   NetworkManager (nmcli, Raspberry Pi OS Bookworm and newer) - or wpa_supplicant (wpa_cli, older systems).
#   "Connect now" falls back to the previous network when the new one does not work.
# ----------------------------------------------------------------------------
WIFI = {"backend": None, "iface": "", "scan": [], "scan_time": 0.0, "job": "", "job_ok": None, "busy": False, "refresh": False}
_WIFI_LOCK = threading.Lock()


def _run(cmd, timeout=30, inp=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=inp)
        return r.returncode, r.stdout, (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as e:
        return 127, "", str(e)


def _nm_split(line):
    """nmcli -t output: fields separated by ':', a literal ':' is written as '\\:'."""
    out, cur, esc = [], [], False
    for ch in line:
        if esc:
            cur.append(ch); esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            out.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def wifi_backend():
    if WIFI["backend"] is None:
        if shutil.which("nmcli"):
            code, out, _e = _run(["nmcli", "-t", "-f", "RUNNING", "general"], 8)
            if code == 0 and "running" in out:
                WIFI["backend"] = "nm"
        if WIFI["backend"] is None and shutil.which("wpa_cli"):
            WIFI["backend"] = "wpa"
        if WIFI["backend"] is None:
            WIFI["backend"] = ""
    if not WIFI["iface"]:
        ifs = _wifi_ifaces()
        WIFI["iface"] = ifs[0] if ifs else "wlan0"
    return WIFI["backend"]


def _perm_hint(err):
    e = (err or "").lower()
    if "not authorized" in e or "permission" in e or "insufficient privileges" in e or "access denied" in e:
        return ("no permission to change Wi-Fi - start the program with sudo, or allow it once with: "
                f"sudo python3 {os.path.basename(__file__)} --allow-wifi")
    return err or "error"


def _bars_from_pct(p):
    return 4 if p >= 75 else 3 if p >= 50 else 2 if p >= 25 else 1 if p > 0 else 0


def wifi_ip(iface=None):
    iface = iface or WIFI["iface"] or "wlan0"
    code, out, _e = _run(["ip", "-4", "-o", "addr", "show", "dev", iface], 5)
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out or "")
    return m.group(1) if m else ""


def local_ip():
    """Address of this computer in the local network (no packet is sent)."""
    import socket
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sk.connect(("10.255.255.255", 1)); return sk.getsockname()[0]
        finally:
            sk.close()
    except OSError:
        return wifi_ip()


# ---- QR codes (setup: scan the address / the own Wi-Fi with the phone camera) ----
def qr_matrix(text, ecl="M"):
    """QR code (byte mode) as a list of rows of True (dark) / False. Small own encoder after the standard
    (ISO 18004), so no extra package is needed on the Pi. ecl: L / M / Q / H."""
    E = {"L": 0, "M": 1, "Q": 2, "H": 3}[ecl]
    FMT = (1, 0, 3, 2)[E]
    ECW = ((-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
           (-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28),
           (-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
           (-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30))
    NBL = ((-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25),
           (-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49),
           (-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68),
           (-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81))

    def raw_modules(v):
        r = (16 * v + 128) * v + 64
        if v >= 2:
            na = v // 7 + 2
            r -= (25 * na - 10) * na - 55
            if v >= 7:
                r -= 36
        return r

    def data_cw(v):
        return raw_modules(v) // 8 - ECW[E][v] * NBL[E][v]
    data = text.encode("utf-8")
    for ver in range(1, 41):
        if 4 + (8 if ver < 10 else 16) + 8 * len(data) <= data_cw(ver) * 8:
            break
    else:
        raise ValueError("text too long for a QR code")
    bits = []
    put = lambda val, n: bits.extend((val >> i) & 1 for i in range(n - 1, -1, -1))
    put(4, 4); put(len(data), 8 if ver < 10 else 16)
    for b in data:
        put(b, 8)
    cap = data_cw(ver) * 8
    put(0, min(4, cap - len(bits)))
    put(0, (-len(bits)) % 8)
    pad = 0xEC
    while len(bits) < cap:
        put(pad, 8); pad ^= 0xEC ^ 0x11
    cws = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]

    def gmul(x, y):
        z = 0
        for i in range(7, -1, -1):
            z = (z << 1) ^ ((z >> 7) * 0x11D)
            z ^= ((y >> i) & 1) * x
        return z & 0xFF
    nb, el = NBL[E][ver], ECW[E][ver]
    rawcw = raw_modules(ver) // 8
    nshort = nb - rawcw % nb; slen = rawcw // nb
    div = [0] * (el - 1) + [1]; root = 1
    for _ in range(el):
        for j in range(el):
            div[j] = gmul(div[j], root)
            if j + 1 < el:
                div[j] ^= div[j + 1]
        root = gmul(root, 0x02)
    blocks, k = [], 0
    for i in range(nb):
        dat = cws[k:k + slen - el + (0 if i < nshort else 1)]; k += len(dat)
        rem = [0] * el
        for b in dat:
            f = b ^ rem.pop(0); rem.append(0)
            for j, c in enumerate(div):
                rem[j] ^= gmul(c, f)
        if i < nshort:
            dat = dat + [0]
        blocks.append(dat + rem)
    allcw = [blk[i] for i in range(len(blocks[0])) for j, blk in enumerate(blocks) if i != slen - el or j >= nshort]
    size = ver * 4 + 17
    M = [[False] * size for _ in range(size)]
    F = [[False] * size for _ in range(size)]

    def setf(x, y, dark):
        M[y][x] = dark; F[y][x] = True
    for i in range(size):
        setf(6, i, i % 2 == 0); setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    setf(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    if ver > 1:
        na = ver // 7 + 2
        step = 26 if ver == 32 else (ver * 4 + na * 2 + 1) // (na * 2 - 2) * 2
        pos = [6] + [size - 7 - i * step for i in range(na - 1)][::-1]
        for i, a in enumerate(pos):
            for j, b in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setf(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)

    def draw_format(mask):
        d = FMT << 3 | mask; rem = d
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        b = (d << 10 | rem) ^ 0x5412
        g = lambda i: (b >> i) & 1 == 1
        for i in range(6):
            setf(8, i, g(i))
        setf(8, 7, g(6)); setf(8, 8, g(7)); setf(7, 8, g(8))
        for i in range(9, 15):
            setf(14 - i, 8, g(i))
        for i in range(8):
            setf(size - 1 - i, 8, g(i))
        for i in range(8, 15):
            setf(8, size - 15 + i, g(i))
        setf(8, size - 8, True)
    draw_format(0)
    if ver >= 7:
        rem = ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        b = ver << 12 | rem
        for i in range(18):
            bit = (b >> i) & 1 == 1; a, c = size - 11 + i % 3, i // 3
            setf(a, c, bit); setf(c, a, bit)
    i = 0; right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j; up = ((right + 1) & 2) == 0
                y = size - 1 - vert if up else vert
                if not F[y][x] and i < len(allcw) * 8:
                    M[y][x] = (allcw[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        right -= 2
    MASKS = (lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0)

    def apply(m):
        for y in range(size):
            for x in range(size):
                if not F[y][x] and MASKS[m](x, y):
                    M[y][x] = not M[y][x]

    def penalty():
        p = 0
        lines = ["".join("1" if c else "0" for c in row) for row in M]
        lines += ["".join("1" if M[y][x] else "0" for y in range(size)) for x in range(size)]
        for ln in lines:
            run, last = 0, ""
            for ch in ln + "x":
                if ch == last:
                    run += 1
                else:
                    if run >= 5:
                        p += 3 + run - 5
                    run, last = 1, ch
            p += 40 * (ln.count("10111010000") + ln.count("00001011101"))
        for y in range(size - 1):
            for x in range(size - 1):
                if M[y][x] == M[y][x + 1] == M[y + 1][x] == M[y + 1][x + 1]:
                    p += 3
        dark = sum(map(sum, M)); tot = size * size
        p += ((abs(dark * 20 - tot * 10) + tot - 1) // tot - 1) * 10
        return p
    best, bm = None, 0
    for m in range(8):
        apply(m); draw_format(m)
        pen = penalty()
        if best is None or pen < best:
            best, bm = pen, m
        apply(m)
    apply(bm); draw_format(bm)
    return M


from html import escape as html_escape


def qr_svg(text, dark="#000", light="#fff"):
    M = qr_matrix(text); n = len(M); q = 4
    path = "".join(f"M{x + q},{y + q}h1v1h-1z" for y in range(n) for x in range(n) if M[y][x])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n + 2 * q} {n + 2 * q}" shape-rendering="crispEdges">'
            f'<rect width="100%" height="100%" fill="{light}"/><path d="{path}" fill="{dark}"/></svg>')


def qr_png(text, scale=6):
    M = qr_matrix(text); n = len(M); q = 4
    a = np.full((n + 2 * q, n + 2 * q), 255, np.uint8)
    a[q:q + n, q:q + n][np.array(M, bool)] = 0
    a = cv2.resize(a, ((n + 2 * q) * scale,) * 2, interpolation=cv2.INTER_NEAREST)
    ok, buf = cv2.imencode(".png", a)
    return buf.tobytes() if ok else b""


def wifi_qr_text(ssid, pw):
    esc = lambda v: re.sub(r'([\\;,:"])', r"\\\1", str(v))
    return f"WIFI:T:WPA;S:{esc(ssid)};P:{esc(pw)};;"


def setup_addresses():
    """Addresses to open the page: home / hotspot network, own Wi-Fi of the Pi, Tailscale."""
    out = []
    ip = wifi_ip()
    if ip:
        out.append({"kind": "lan", "url": page_address(ip)})
    if CFG["hotspot_on"] and ip != "10.42.0.1":
        out.append({"kind": "hotspot", "url": page_address("10.42.0.1")})
    try:
        ts = tailscale_status()
        if ts.get("state") == "Running" and ts.get("ip"):
            out.append({"kind": "tailscale", "url": page_address(ts["ip"])})
    except Exception:
        pass
    return out


def page_address(ip=None):
    ip = ip or wifi_ip()
    scheme = "https" if WEB_OPTS.get("https") else "http"
    return f"{scheme}://{ip}:{CFG['web_port']}/" if ip else ""


# ---- NetworkManager ----------------------------------------------------------
def _nm_saved():
    code, out, err = _run(["nmcli", "-t", "-f", "NAME,UUID,TYPE,AUTOCONNECT,AUTOCONNECT-PRIORITY,ACTIVE", "connection", "show"], 15)
    res = []
    if code != 0:
        return res
    for ln in out.splitlines():
        f = _nm_split(ln)
        if len(f) < 6 or f[2] not in ("802-11-wireless", "wifi"):
            continue
        c2, ss, _e = _run(["nmcli", "-t", "-g", "802-11-wireless.ssid,802-11-wireless.mode", "connection", "show", "uuid", f[1]], 10)
        lines = ss.splitlines() if c2 == 0 else []
        ssid = lines[0] if lines else f[0]
        mode = lines[1] if len(lines) > 1 else ""
        if mode == "ap":                                   # a hotspot the Pi itself offers - not a network to join
            continue
        try:
            prio = int(f[4])
        except ValueError:
            prio = 0
        res.append({"name": f[0], "id": f[1], "ssid": ssid, "auto": f[3] == "yes", "prio": prio, "active": f[5] == "yes"})
    return res


def _nm_scan():
    code, out, err = _run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,CHAN", "device", "wifi", "list", "--rescan", "yes"], 40)
    if code != 0:                                          # rescanning may need more rights: use the cached list
        code, out, err = _run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,CHAN", "device", "wifi", "list", "--rescan", "no"], 20)
    if code != 0:
        raise RuntimeError(_perm_hint(err))
    nets = {}
    for ln in out.splitlines():
        f = _nm_split(ln)
        if len(f) < 5 or not f[1]:
            continue
        try:
            sig = int(f[2])
        except ValueError:
            sig = 0
        sec = f[3].strip() if f[3].strip() not in ("", "--") else ""
        cur = nets.get(f[1]); act = f[0].strip() == "*"
        if cur is None or sig > cur["signal"]:            # 2.4 + 5 GHz of the same network: show the stronger one
            nets[f[1]] = {"ssid": f[1], "signal": sig, "secure": bool(sec), "security": sec, "chan": f[4],
                          "active": act or bool(cur and cur["active"])}
        elif act:
            cur["active"] = True
    return list(nets.values())


def _nm_connect_now(ssid, password):
    saved = next((s for s in _nm_saved() if s["ssid"] == ssid), None)
    if saved:
        old = ""
        if password:
            c0, o0, _e0 = _run(["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", "uuid", saved["id"]], 15)
            old = o0.strip() if c0 == 0 else ""
            _run(["nmcli", "connection", "modify", "uuid", saved["id"], "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password], 15)
        code, out, err = _run(["nmcli", "--wait", "40", "connection", "up", "uuid", saved["id"]], 50)
        if code and old and old != password:           # 2.95.33: wrong new password - the saved (working) one comes back
            _run(["nmcli", "connection", "modify", "uuid", saved["id"], "wifi-sec.psk", old], 15)
    else:
        cmd = ["nmcli", "--wait", "40", "device", "wifi", "connect", ssid] + (["password", password] if password else []) + ["ifname", WIFI["iface"]]
        code, out, err = _run(cmd, 50)
    return code == 0, _perm_hint(err) if code else ""


def _nm_save(ssid, password, preferred):
    prio = "20" if preferred else "0"
    saved = next((s for s in _nm_saved() if s["ssid"] == ssid), None)
    if saved:
        cmd = ["nmcli", "connection", "modify", "uuid", saved["id"], "connection.autoconnect", "yes", "connection.autoconnect-priority", prio]
        if password:
            cmd += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password]
    else:
        cmd = ["nmcli", "connection", "add", "type", "wifi", "ifname", WIFI["iface"], "con-name", ssid, "ssid", ssid,
               "connection.autoconnect", "yes", "connection.autoconnect-priority", prio]
        if password:
            cmd += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password]
    code, out, err = _run(cmd, 20)
    return code == 0, _perm_hint(err) if code else ""


def _nm_forget(sid):
    code, out, err = _run(["nmcli", "connection", "delete", "uuid", sid], 20)
    return code == 0, _perm_hint(err) if code else ""


def _nm_up(sid):
    code, out, err = _run(["nmcli", "--wait", "40", "connection", "up", "uuid", sid], 50)
    return code == 0


# ---- wpa_supplicant (older Raspberry Pi OS) ------------------------------------
def _wpa(*args, timeout=15):
    return _run(["wpa_cli", "-i", WIFI["iface"]] + list(args), timeout)


def _wpa_saved():
    code, out, err = _wpa("list_networks")
    res = []
    for ln in out.splitlines()[1:]:
        f = ln.split("\t")
        if len(f) >= 2 and f[0].isdigit():
            res.append({"name": f[1], "id": f[0], "ssid": f[1], "auto": "[DISABLED]" not in (f[3] if len(f) > 3 else ""),
                        "prio": 0, "active": "[CURRENT]" in (f[3] if len(f) > 3 else "")})
    return res


def _wpa_scan():
    _wpa("scan"); time.sleep(4)
    code, out, err = _wpa("scan_results")
    if code != 0:
        raise RuntimeError(_perm_hint(err))
    cur = next((s["ssid"] for s in _wpa_saved() if s["active"]), "")
    nets = {}
    for ln in out.splitlines()[1:]:
        f = ln.split("\t")
        if len(f) < 5 or not f[4]:
            continue
        try:
            pct = wifi_pct(int(f[2]))
        except ValueError:
            pct = 0
        if f[4] not in nets or pct > nets[f[4]]["signal"]:
            sec = "WPA" if ("WPA" in f[3] or "RSN" in f[3]) else ("WEP" if "WEP" in f[3] else "")
            nets[f[4]] = {"ssid": f[4], "signal": pct, "secure": bool(sec), "security": sec, "chan": f[1], "active": f[4] == cur}
    return list(nets.values())


def _wpa_q(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _wpa_save(ssid, password, preferred, select=False):
    saved = next((s for s in _wpa_saved() if s["ssid"] == ssid), None)
    if saved:
        nid = saved["id"]
    else:
        code, out, err = _wpa("add_network")
        nid = out.strip().splitlines()[-1] if out.strip() else ""
        if not nid.isdigit():
            return False, _perm_hint(err or out)
        _wpa("set_network", nid, "ssid", _wpa_q(ssid))
    if password:
        _wpa("set_network", nid, "psk", _wpa_q(password))
    elif not saved:
        _wpa("set_network", nid, "key_mgmt", "NONE")
    _wpa("set_network", nid, "priority", "20" if preferred else "0")
    code, out, err = _wpa("select_network" if select else "enable_network", nid)
    _wpa("save_config")
    return code == 0 and "FAIL" not in out, _perm_hint(err) if code else ("" if "FAIL" not in out else "wpa_supplicant refused it")


# ---- common entry points ---------------------------------------------------------
def wifi_status():
    b = wifi_backend()
    saved = []
    try:
        saved = _nm_saved() if b == "nm" else (_wpa_saved() if b == "wpa" else [])
    except Exception:
        saved = []
    w = STATE["wifi"] or {}
    ip = wifi_ip() if b else ""
    act = next((x for x in saved if x["active"]), None)            # the network manager knows best which network is in use
    import socket
    host = socket.gethostname()
    names = {x["ssid"] for x in saved}
    scan = [dict(n, active=(n["ssid"] == act["ssid"]) if act else n["active"], saved=n["ssid"] in names) for n in WIFI["scan"]]
    scan.sort(key=lambda n: (not n["active"], -n["signal"]))
    return {"backend": b, "iface": WIFI["iface"], "saved": saved, "scan": scan, "scan_time": WIFI["scan_time"],
            "job": WIFI["job"], "job_ok": WIFI["job_ok"], "busy": WIFI["busy"], "ssid": act["ssid"] if act else w.get("ssid", ""),
            "connected": bool(act) or w.get("connected", False),
            "ip": ip, "address": page_address(ip), "local_name": f"{host}.local", "port": CFG["web_port"],
            "https": bool(WEB_OPTS.get("https"))}


def wifi_scan():
    b = wifi_backend()
    if not b:
        return False, "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)"
    if not _WIFI_LOCK.acquire(blocking=False):
        return False, "busy"
    try:
        nets = _nm_scan() if b == "nm" else _wpa_scan()
        saved = {s["ssid"] for s in (_nm_saved() if b == "nm" else _wpa_saved())}
        for n in nets:
            n["saved"] = n["ssid"] in saved; n["bars"] = _bars_from_pct(n["signal"])
        nets.sort(key=lambda n: (not n["active"], -n["signal"]))
        WIFI["scan"] = nets[:40]; WIFI["scan_time"] = time.time()
        log_event("sys", f"Wi-Fi scan: {len(nets)} network(s)")
        return True, ""
    except Exception as e:
        return False, str(e)[:200]
    finally:
        _WIFI_LOCK.release()


def _valid(ssid, password):
    if not isinstance(ssid, str) or not ssid or len(ssid.encode()) > 32 or any(ord(c) < 32 for c in ssid):
        return "invalid network name"
    if password and (not isinstance(password, str) or not 8 <= len(password) <= 63 or any(ord(c) < 32 for c in password)):
        return "the password must have 8 to 63 characters"
    return ""


def wifi_save(ssid, password="", preferred=True):
    err = _valid(ssid, password)
    if err:
        return False, err
    b = wifi_backend()
    if not b:
        return False, "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)"
    with _WIFI_LOCK:
        ok, msg = _nm_save(ssid, password, preferred) if b == "nm" else _wpa_save(ssid, password, preferred)
    if ok:
        log_event("sys", f"Wi-Fi network saved: {ssid} (connects automatically{', preferred' if preferred else ''})")
    return ok, msg


def wifi_forget(sid):
    b = wifi_backend()
    if not b or not isinstance(sid, str) or not re.fullmatch(r"[0-9A-Za-z\-]{1,40}", sid):
        return False, "unknown network"
    with _WIFI_LOCK:
        if b == "nm":
            ok, msg = _nm_forget(sid)
        else:
            code, out, err = _wpa("remove_network", sid); _wpa("save_config")
            ok, msg = code == 0 and "FAIL" not in out, _perm_hint(err)
    if ok:
        log_event("sys", "Wi-Fi network removed")
    return ok, msg


def wifi_connect(ssid, password="", preferred=True):
    """Switch to another network in the background. If it does not work within ~45 s, go back to the previous one."""
    err = _valid(ssid, password)
    if err:
        return False, err
    b = wifi_backend()
    if not b:
        return False, "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)"
    if WIFI["busy"]:
        return False, "busy"
    WIFI["busy"] = True; WIFI["job"] = f"connecting to {ssid}…"; WIFI["job_ok"] = None

    def work():
        try:
            hs_was = bool(b == "nm" and HOTSPOT_CON in _nm_active_names())
            with _WIFI_LOCK:
                prev = next((s for s in (_nm_saved() if b == "nm" else _wpa_saved()) if s["active"]), None)
                log_event("sys", f"Wi-Fi: switching to {ssid}" + (f" (from {prev['ssid']})" if prev else ""))
                if b == "nm":
                    ok, msg = _nm_connect_now(ssid, password)
                    if ok:
                        _nm_save(ssid, "", preferred)          # keep it for automatic connection later
                else:
                    ok, msg = _wpa_save(ssid, password, preferred, select=True)
                    if ok:                                   # wpa_cli returns at once: wait for the association
                        ok = False
                        for _ in range(30):
                            time.sleep(1.5)
                            st = _wpa("status")[1]
                            if f"ssid={ssid}" in st and "wpa_state=COMPLETED" in st:
                                ok = True; break
                        msg = "" if ok else "could not connect (wrong password or too far away?)"
                if ok:
                    for _ in range(10):                      # wait for an address
                        ip = wifi_ip()
                        if ip:
                            break
                        time.sleep(1)
                    WIFI["job"] = f"connected to {ssid}" + (f" · {page_address(ip)}" if ip else ""); WIFI["job_ok"] = True
                    log_event("sys", WIFI["job"])
                else:
                    back = ""
                    if prev and prev["ssid"] != ssid:
                        if b == "nm":
                            back = " - back on " + prev["ssid"] if _nm_up(prev["id"]) else " - previous network did not come back"
                        else:
                            _wpa("select_network", prev["id"]); [_wpa("enable_network", s["id"]) for s in _wpa_saved()]; _wpa("save_config")
                            back = " - back on " + prev["ssid"]
                    WIFI["job"] = f"failed: {msg or 'could not connect'}{back}"; WIFI["job_ok"] = False
                    log_event("sys", f"Wi-Fi: {ssid} failed ({msg}){back}")
            if not ok and hs_was and b == "nm" and HOTSPOT_CON not in _nm_active_names():
                hok, _herr = hotspot_set(True, persist=False)    # 2.95.33: the Pi stays reachable over its own Wi-Fi
                log_event("sys", "Own Wi-Fi switched on again" if hok else "Own Wi-Fi could not be switched on again")
        except Exception as e:
            WIFI["job"] = "failed: " + str(e)[:150]; WIFI["job_ok"] = False
        finally:
            WIFI["busy"] = False; WIFI["refresh"] = True
    threading.Thread(target=work, daemon=True).start()
    return True, ""


POLKIT_RULE = """// MoveEye: allow user "{user}" to manage Wi-Fi / the own hotspot (NetworkManager), the clock (timedated)
// and to shut down / restart the Pi (logind)
polkit.addRule(function(action, subject) {{
    if ((action.id.indexOf("org.freedesktop.NetworkManager.") == 0 || action.id.indexOf("org.freedesktop.timedate1.") == 0
         || action.id == "org.freedesktop.login1.set-self-linger" || action.id.indexOf("org.freedesktop.login1.power-off") == 0
         || action.id.indexOf("org.freedesktop.login1.reboot") == 0) && subject.user == "{user}") {{
        return polkit.Result.YES;
    }}
}});
"""


def allow_wifi():
    """--allow-wifi: one-time permission so MoveEye may change Wi-Fi without running as root."""
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "pi"
    path = "/etc/polkit-1/rules.d/50-motionwatch-wifi.rules"
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        print(f"Needs root. Run:  sudo {sys.executable} {os.path.abspath(__file__)} --allow-wifi"); return 1
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(POLKIT_RULE.format(user=user))
    except OSError as e:
        print(f"Could not write {path}: {e}"); return 1
    subprocess.run(["systemctl", "restart", "polkit"], capture_output=True)
    subprocess.run(["loginctl", "enable-linger", user], capture_output=True)       # autostart without login
    try:                                     # hardware watchdog: if the whole Pi freezes, it restarts by itself after 15 s
        os.makedirs("/etc/systemd/system.conf.d", exist_ok=True)
        with open("/etc/systemd/system.conf.d/90-motionwatch-watchdog.conf", "w") as f:
            f.write("# MoveEye: restart the Pi if it freezes\n[Manager]\nRuntimeWatchdogSec=15s\n")
        subprocess.run(["systemctl", "daemon-reexec"], capture_output=True)
        print("Hardware watchdog on: a frozen Pi restarts by itself.")
    except OSError as e:
        print(f"Hardware watchdog not set: {e}")
    print(f"User '{user}' may now manage Wi-Fi, the own hotspot, the clock, the autostart and shut down / restart the Pi ({path}).")
    return 0


