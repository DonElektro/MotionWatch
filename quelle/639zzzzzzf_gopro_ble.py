#@ MoveEye – Teil 639zzzzzzf: GoPro Hero 9 und neuer über Bluetooth (Open GoPro) – Suche, Koppeln, ein / aus, wach halten, Akku, Livestream (RTMP an MoveEye), Kamera-WLAN, Heim-WLAN mit COHN (Hero 12+), Wiederverbinden. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Freigabe Besitzer 28.11.2026 19:24 (Fragebogen GoPro #44, Komplettpaket), gemeinsame Schnittstelle: Helfer-Datei
# gopro_schnittstelle.md (G1 Kern «mw-gopro-kern», G2 dieser Teil, G3 Hero 8 über Bluetooth).
# Quelle aller Nummern: die offizielle Open-GoPro-Spezifikation (gopro.github.io/OpenGoPro, BLE-Teil + die .proto-Dateien im
# Repository gopro/OpenGoPro, nachgesehen 28.11.2026):
#   Dienste      Werbung 0xFEA6; GP-XXXX = b5f9XXXX-aa8d-11e3-9046-0002a5d5c51b. Befehl 0072 -> Antwort 0073, Einstellung 0074 ->
#                0075, Abfrage 0076 -> 0077, Netz 0091 -> 0092; Kamera-WLAN: 0002 SSID, 0003 Passwort, 0004 Strom, 0005 Zustand.
#   Pakete       höchstens 20 Bytes; Start mit 13-bit-Kopf (0b001LLLLL LLLLLLLL, «immer beim Senden»), danach Fortsetzung
#                0b1000CCCC. Empfang auch 5-bit (0b000LLLLL) und 16-bit (0b010xxxxx + 2 Bytes).
#   TLV          [ID, Länge, Wert …]; Antwort [ID, Status (0 = gut), …]. Abfrage 0x13 = Status-Werte [ID, Länge, Wert]…
#   Protobuf     [Feature, Action, Nachricht] (Protocol Buffers 2): 0x02 Netz (0x04 Connect, 0x05 ConnectNew, 0x0C Meldung
#                Provisioning, 0x78 ReleaseNetwork), 0xF1 Befehl (0x79 SetLiveStreamMode, 0x67 CreateCOHNCert, 0x65 COHN an),
#                0xF5 Abfrage (0x74 LiveStreamStatus, 0x6E COHN-Zertifikat, 0x6F COHN-Status); Antwort = Action | 0x80,
#                Meldung Livestream 0xF5 0xF5.
#   Befehle      Auslöser 0x01 (1 an / 0 aus; startet / stoppt den Livestream), Schlaf 0x05, Kamera-WLAN 0x17, Wachhalten
#                Einstellung 0x5B = 0x42 alle 3 s, Gerätedaten 0x3C. Status 70 Akku %, 2 Akku-Balken, 8 beschäftigt,
#                10 nimmt auf, 6 zu heiss, 82 bereit.
# Ablauf Strom  koppeln (BlueZ «Just Works», die Kamera im Kopplungsmodus) -> Kamera ins WLAN (MoveEye-WLAN, Heim-WLAN; das
#               Passwort geht nur einmal an die Kamera und wird nie gespeichert) -> SetLiveStreamMode mit der RTMP-Adresse von
#               MoveEye (G1: Empfänger) -> warten auf «bereit» -> Auslöser an -> Quelle gopro_quelle(id) für die Zusatzkamera.
#               Kamera-WLAN (Vorschau-Strom udp://@:8554) nur mit einem zweiten WLAN-Stick (sonst wäre das Handy weg).
# Wache         ein Faden «gopro-ble»: wach halten (3 s), Akku (15 s), Strom weg / Verbindung weg -> stille Meldung im Protokoll und
#               neu verbinden / neu starten mit Pausen 5 / 15 / 30 / 60 / 120 s.
# Geheimnisse   Kopplungsdaten (Adresse, Modell, bekannte WLAN-Namen, COHN-Zertifikat + Zugang) nur in DATA_DIR/gopro_ble.json
#               (Rechte 600; die Bluetooth-Schlüssel selbst verwaltet BlueZ). Nie ein Passwort im Protokoll, in der Seite oder im
#               Bericht. Steuern darf nur der Administrator (nie mit App-Schlüssel, nicht im Bedienermodus).
# Für G3 (Hero 8): gopro_ble_client(addr) -> .connect(timeout, pair=True), .write("0072", bytes) -> Antwort (ohne Kopf, zusammengesetzt)
#               | b"" (Characteristic ohne Antwort) | None (keine Antwort / Fehler), .read("0002") -> bytes | None, .close();
#               gopro_ble_scan(timeout) -> [{"addr", "name", "rssi"}] (nur Werbung mit 0xFEA6 oder Name «GoPro …»).
# Test: werkzeuge/gopro_ble_test.py (nachgestellte Kamera als Ersatz für bleak, nie echtes Bluetooth).
# ----------------------------------------------------------------------------
# Der Programmtext steht in EINEM Literal (Hauptdatei klein): werkzeuge/bauen.py legt es in die Zusatz-ZIP, beim Start läuft es
# hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es die GoPro über Bluetooth nicht - sie gehört nicht zu
# Start, Schutz, Alarm oder Update.

GOPRO_BLE_PY = r'''import asyncio

GPB_BASE = "b5f9%s-aa8d-11e3-9046-0002a5d5c51b"
GPB_FEA6 = "0000fea6-0000-1000-8000-00805f9b34fb"
GPB_RESP = {"0072": "0073", "0074": "0075", "0076": "0077", "0091": "0092"}      # write -> notify with the answer
GPB_FRAMED = set(GPB_RESP)                                                      # these speak in packets with a header
GPB_PB_FEATURES = {0x02, 0xF1, 0xF5}
GPB_ST = {"batt": 70, "bars": 2, "busy": 8, "enc": 10, "hot": 6, "ready": 82}   # status IDs (Open GoPro)
GPB_LS = {0: "idle", 1: "config", 2: "ready", 3: "streaming", 4: "complete", 5: "failed", 6: "reconnecting", 7: "unavailable"}
GPB_PROV_OK = (5, 6)                                                            # PROVISIONING_SUCCESS_NEW_AP / _OLD_AP
GPB_PROV_ERR = {3: "the GoPro could not join the WLAN", 4: "the GoPro could not join the WLAN",
                7: "the GoPro could not join the WLAN", 8: "wrong WLAN password", 9: "the GoPro could not join the WLAN",
                10: "the GoPro could not join the WLAN", 11: "the GoPro could not join the WLAN"}
GPB_RES = {"480": 4, "720": 7, "1080": 12}                                      # EnumWindowSize
GPB_BACKOFF = (5, 15, 30, 60, 120)
GPB_KEEPALIVE_S, GPB_STATUS_S = 3.0, 15.0
GPB_FILE = "gopro_ble.json"
GPB_FATAL = {"bleak missing - install it on this page", "no Bluetooth adapter", "wrong WLAN password", "enter the WLAN name",
             "the GoPro does not know this WLAN yet - enter the password once", "MoveEye's own WLAN is off - switch it on first",
             "the camera WLAN needs a second WLAN adapter (it would cut off your phone)", "live stream not possible with the current lens setting",
             "unknown device", "pairing failed - put the GoPro into pairing mode"}
GPB_ID_RE = re.compile(r"^[0-9a-f]{8}$")
GPB_ADDR_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$|^[0-9A-Fa-f-]{36}$")   # Linux MAC, macOS UUID

for _k, _v in {"gopro_ble_ap_iface": "wlan1"}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)
    if "FACTORY_CFG" in globals():
        FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update({"gopro_ble_ap_iface"})

GPB = {"lock": threading.Lock(), "loop": None, "bleak": None, "dev": {}, "wd": None, "pairing": "", "last_pair": "", "scan": {"running": False, "found": [], "err": "", "t": 0.0},
       "install": {"running": False, "msg": "", "ok": None}, "secrets": []}


class GpbError(Exception):
    pass


# ---- G1 (639zzzzzze_gopro_kern): GOPRO, gopro_add / gopro_dev / gopro_start / gopro_stop, the receiver -----------------------
GPB_MODELLE = ["hero9", "hero10", "hero11", "hero12", "hero13"]
_gpb_rx_paths_before = _rx_paths


# wraps: _rx_paths (G1: the receiver takes only the paths of the way «rtmp»; Bluetooth GoPros send there too)
def _rx_paths():
    p = set(_gpb_rx_paths_before())
    for gid, d in list(GPB["dev"].items()):
        g = GOPRO.get(gid)
        if g and g.get("weg") == "ble" and g.get("aktiv") and d["net"] != "ap":
            p.add(gopro_rtmp_path(g))
    return sorted(p)


# ---- packets (Open GoPro data protocol) ----------------------------------------------------------------------------------------
def gpb_uuid(short):
    return GPB_BASE % short.lower()


def gpb_frames(payload):
    """one message -> BLE packets of at most 20 bytes: start with the 13-bit header, then continuation packets (counter 0..F)"""
    payload = bytes(payload)
    n = len(payload)
    if n > 8191:
        raise GpbError("message too long")
    out = [bytes([0x20 | (n >> 8), n & 0xFF]) + payload[:18]]
    rest, c = payload[18:], 0
    while rest:
        out.append(bytes([0x80 | (c & 0x0F)]) + rest[:19])
        rest, c = rest[19:], c + 1
    return out


class GpbAssembler:
    """packets -> messages (5-bit, 13-bit, 16-bit header; continuation)"""

    def __init__(self):
        self.buf, self.need = b"", None

    def feed(self, pkt):
        pkt = bytes(pkt or b"")
        if not pkt:
            return None
        h = pkt[0]
        if h & 0x80:
            if self.need is None:
                return None                                  # a continuation without a start: ignore
            self.buf += pkt[1:]
        else:
            kind = (h >> 5) & 0x03
            if kind == 0:
                self.need, self.buf = h & 0x1F, pkt[1:]
            elif kind == 1 and len(pkt) >= 2:
                self.need, self.buf = ((h & 0x1F) << 8) | pkt[1], pkt[2:]
            elif kind == 2 and len(pkt) >= 3:
                self.need, self.buf = (pkt[1] << 8) | pkt[2], pkt[3:]
            else:
                self.need, self.buf = None, b""
                return None
        if len(self.buf) >= self.need:
            out, self.buf, self.need = self.buf[:self.need], b"", None
            return out
        return None


# ---- protobuf 2 (only what Open GoPro needs: varint + length-delimited) ---------------------------------------------------------
def _pb_varint(n):
    n &= (1 << 64) - 1
    out = bytearray()
    while True:
        b, n = n & 0x7F, n >> 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _pb_rv(data, i):
    n = shift = 0
    while True:
        if i >= len(data):
            raise GpbError("bad protobuf")
        b = data[i]; i += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, i
        shift += 7


def pb_enc(fields):
    """[(number, "v" | "s", value)] -> bytes ("v" = int / bool / enum, "s" = string / bytes); None is left out"""
    out = b""
    for num, kind, val in fields:
        if val is None:
            continue
        if kind == "v":
            out += _pb_varint(num << 3) + _pb_varint(int(val))
        else:
            b = val.encode("utf-8") if isinstance(val, str) else bytes(val)
            out += _pb_varint((num << 3) | 2) + _pb_varint(len(b)) + b
    return out


def pb_dec(data):
    """bytes -> {number: [values]} (varint as int, length-delimited as bytes)"""
    data, i, out = bytes(data), 0, {}
    while i < len(data):
        key, i = _pb_rv(data, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _pb_rv(data, i)
        elif wt == 2:
            ln, i = _pb_rv(data, i)
            v, i = data[i:i + ln], i + ln
        elif wt == 5:
            v, i = data[i:i + 4], i + 4
        elif wt == 1:
            v, i = data[i:i + 8], i + 8
        else:
            raise GpbError("bad protobuf")
        out.setdefault(num, []).append(v)
    return out


def _pb1(d, num, default=None):
    v = d.get(num)
    return v[0] if v else default


def _pbs(d, num):
    v = _pb1(d, num, b"")
    return v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else ""


def gpb_tlv(data):
    """[ID, length, value]… -> {ID: bytes}"""
    out, i = {}, 0
    data = bytes(data or b"")
    while i + 2 <= len(data):
        k, ln = data[i], data[i + 1]
        out[k] = data[i + 2:i + 2 + ln]
        i += 2 + ln
    return out


def gpb_lv(data):
    """[length, value]… -> [bytes] (Get Hardware Info)"""
    out, i = [], 0
    while i < len(data):
        ln = data[i]
        out.append(bytes(data[i + 1:i + 1 + ln]))
        i += 1 + ln
    return out


def gpb_is_pb(uuid_short, payload):
    return uuid_short == "0091" or (len(payload) >= 2 and payload[0] in (0xF1, 0xF5))


def gpb_match(uuid_short, payload):
    """which answer belongs to this request (protobuf: same feature, action | 0x80; TLV: same ID)"""
    payload = bytes(payload)
    if gpb_is_pb(uuid_short, payload):
        f, a = payload[0], payload[1] | 0x80
        return lambda r: len(r) >= 2 and r[0] == f and r[1] == a
    k = payload[0]
    return lambda r: len(r) >= 1 and r[0] == k


# ---- bleak (one asyncio loop in its own thread) --------------------------------------------------------------------------------
def gpb_bleak():
    """the bleak module (tests put a stand-in into GPB["bleak"]) or None"""
    if GPB["bleak"] is not None:
        return GPB["bleak"]
    try:
        import bleak as _b
        GPB["bleak"] = _b
        return _b
    except Exception:
        return None


def gpb_adapter():
    if GPB["bleak"] is not None and getattr(GPB["bleak"], "FAKE_ADAPTER", None) is not None:
        return bool(GPB["bleak"].FAKE_ADAPTER)
    try:
        return bool(os.listdir("/sys/class/bluetooth"))
    except OSError:
        return sys.platform in ("darwin", "win32")


def _gpb_loop():
    with GPB["lock"]:
        L = GPB["loop"]
        if L is None or L.is_closed():
            L = asyncio.new_event_loop()
            threading.Thread(target=L.run_forever, name="gopro-ble-io", daemon=True).start()
            GPB["loop"] = L
    return L


def _gpb_run(coro, timeout):
    fut = asyncio.run_coroutine_threadsafe(coro, _gpb_loop())
    try:
        return fut.result(timeout)
    except Exception:
        fut.cancel()
        raise


def _gpb_secret(s):
    """remember a secret for the log filter (only in memory)"""
    if isinstance(s, str) and len(s) >= 4 and s not in GPB["secrets"]:
        GPB["secrets"].append(s)
        del GPB["secrets"][:-20]


def _gpb_log(text):
    text = str(text)
    for s in GPB["secrets"]:
        text = text.replace(s, "•••")
    log_event("gopro", text)


class GoProBleClient:
    """a connection to one GoPro (G2, also used by G3 for the Hero 8). All calls block; never call them from the BLE thread."""

    def __init__(self, addr, on_notify=None, on_disconnect=None):
        self.addr, self.on_notify, self.on_disconnect = addr, on_notify, on_disconnect
        self._c, self._asm, self._wait, self.last_err = None, {}, {}, ""

    @property
    def connected(self):
        c = self._c
        return bool(c is not None and getattr(c, "is_connected", False))

    def connect(self, timeout=20.0, pair=True):
        try:
            return bool(_gpb_run(self._aconnect(float(timeout), pair), float(timeout) + 20))
        except Exception as e:
            self.last_err = str(e) or type(e).__name__
            return False

    async def _aconnect(self, timeout, pair):
        B = gpb_bleak()
        if B is None:
            raise GpbError("bleak missing - install it on this page")
        if self.connected:
            return True

        def gone(_c=None):
            self._c = None
            for lst in self._wait.values():
                for _m, f in lst:
                    if not f.done():
                        f.set_result(None)
            if self.on_disconnect:
                threading.Thread(target=self.on_disconnect, name="gopro-ble-gone", daemon=True).start()

        c = B.BleakClient(self.addr, disconnected_callback=gone, timeout=timeout)
        try:
            await c.connect()
        except Exception as e:
            raise GpbError("GoPro not found - is it switched on and near?") from e
        if pair:
            try:
                await c.pair()
            except Exception as e:
                if "already" not in str(e).lower():
                    try:
                        await c.disconnect()
                    except Exception:
                        pass
                    raise GpbError("pairing failed - put the GoPro into pairing mode") from e
        self._c = c
        self._asm = {r: GpbAssembler() for r in GPB_RESP.values()}
        for r in GPB_RESP.values():
            await c.start_notify(gpb_uuid(r), self._cb(r))
        return True

    def _cb(self, r):
        def cb(_sender, data):
            msg = self._asm[r].feed(data)
            if msg is None:
                return
            for m, f in list(self._wait.get(r, ())):
                if not f.done() and m(msg):
                    f.set_result(msg)
                    return
            if self.on_notify:
                try:
                    self.on_notify(r, msg)
                except Exception:
                    pass
        return cb

    def write(self, uuid_short, payload, timeout=8.0, frame=True):
        """send one message; the answer of the matching notify characteristic (header removed), b"" if it has none, None if
        nothing came / not connected. frame=False (G3, old Hero 8 commands): payload goes out unchanged in one packet (it already
        carries its header, e.g. 03 17 01 01); the answer is still put together from the notify characteristic."""
        try:
            return _gpb_run(self._awrite(str(uuid_short).lower(), bytes(payload), float(timeout), bool(frame)), float(timeout) + 5)
        except Exception as e:
            self.last_err = str(e) or type(e).__name__
            return None

    async def _awrite(self, u, payload, timeout, frame=True):
        c = self._c
        if c is None:
            raise GpbError("not connected")
        r, fut = GPB_RESP.get(u), None
        body = payload
        if not frame and len(payload) >= 2 and payload[0] >> 5 == 0 and payload[0] == len(payload) - 1:
            body = payload[1:]                               # the message behind its own 5-bit header
        if r and body:
            fut = asyncio.get_running_loop().create_future()
            self._wait.setdefault(r, []).append((gpb_match(u, body), fut))
        try:
            for fr in (gpb_frames(payload) if (u in GPB_FRAMED and frame) else [payload]):
                await c.write_gatt_char(gpb_uuid(u), fr, response=True)
            if fut is None:
                return b""
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            if fut is not None:
                self._wait[r] = [x for x in self._wait.get(r, []) if x[1] is not fut]

    def read(self, uuid_short, timeout=8.0):
        try:
            return _gpb_run(self._aread(str(uuid_short).lower()), float(timeout))
        except Exception as e:
            self.last_err = str(e) or type(e).__name__
            return None

    async def _aread(self, u):
        c = self._c
        if c is None:
            raise GpbError("not connected")
        return bytes(await c.read_gatt_char(gpb_uuid(u)))

    def close(self):
        c, self._c = self._c, None
        if c is None:
            return
        self.on_disconnect = None                            # our own goodbye is no «connection lost»
        try:
            _gpb_run(c.disconnect(), 10)
        except Exception:
            pass


def gopro_ble_client(addr, on_notify=None, on_disconnect=None):
    return GoProBleClient(addr, on_notify, on_disconnect)


def gopro_ble_scan(timeout=8.0):
    """GoPro cameras nearby: [{"addr", "name", "rssi"}], strongest first (advertising 0xFEA6 or named «GoPro …»)"""
    B = gpb_bleak()
    if B is None:
        raise GpbError("bleak missing - install it on this page")

    async def go():
        r = await B.BleakScanner.discover(timeout=float(timeout), return_adv=True)
        out = []
        for _k, (dev, adv) in (r or {}).items():
            uu = [str(x).lower() for x in (getattr(adv, "service_uuids", None) or [])]
            name = getattr(adv, "local_name", None) or getattr(dev, "name", None) or ""
            if GPB_FEA6 in uu or name.startswith("GoPro"):
                out.append({"addr": dev.address, "name": name[:40], "rssi": getattr(adv, "rssi", None)})
        return sorted(out, key=lambda x: -(x["rssi"] if isinstance(x["rssi"], int) else -999))
    return _gpb_run(go(), float(timeout) + 15)


# ---- the pairing file (DATA_DIR, rights 600) -----------------------------------------------------------------------------------
def _gpb_path():
    return os.path.join(DATA_DIR, GPB_FILE)


def gpb_load():
    try:
        with open(_gpb_path(), encoding="utf-8") as f:
            d = json.load(f)
        return d.get("devices", {}) if isinstance(d, dict) and isinstance(d.get("devices"), dict) else {}
    except (OSError, ValueError):
        return {}


def gpb_save():
    devs = {i: dict(d["rec"]) for i, d in GPB["dev"].items()}
    p = _gpb_path()
    tmp = p + ".tmp"
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"devices": devs}, f, ensure_ascii=False, indent=1)
        os.chmod(tmp, 0o600)
        os.replace(tmp, p)
        os.chmod(p, 0o600)
    except OSError as e:
        _gpb_log("GoPro: could not save the pairing file (%s)" % type(e).__name__)


def gpb_model_no(name):
    m = re.search(r"HERO\s*(\d+)", str(name or ""), re.I)
    if m:
        return int(m.group(1))
    return 11 if re.search(r"\bMAX\b", str(name or ""), re.I) else 0


def _gpb_new(rec):
    return {"rec": rec, "client": None, "lock": threading.Lock(), "awake": False, "want": False, "zustand": "off", "akku": None,
            "bars": None, "busy": False, "hot": False, "ls": None, "ls_err": 0, "prov": None, "fehler": "", "quelle": "", "step": "",
            "net": rec.get("net") or "hotspot", "t_keep": 0.0, "t_stat": 0.0, "retry": 0, "next": 0.0, "job": False, "cohn_live": {},
            "ap_con": ""}


for _i, _r in gpb_load().items():
    if GPB_ID_RE.match(_i) and isinstance(_r, dict) and GPB_ADDR_RE.match(str(_r.get("addr") or "")):
        GPB["dev"][_i] = _gpb_new(_r)


# ---- one camera ----------------------------------------------------------------------------------------------------------------
def _gpb_dev(i, paired=True):
    """the Bluetooth part of a GoPro of G1 with the way «ble» (created on first use)"""
    i = str(i or "")
    d = GPB["dev"].get(i)
    if d is None:
        g = gopro_dev(i) if GPB_ID_RE.match(i) else None
        if not g or g.get("weg") != "ble":
            raise GpbError("unknown device")
        d = GPB["dev"][i] = _gpb_new({})
    if paired and not d["rec"].get("addr"):
        raise GpbError("not paired yet - search and pair first")
    return d


def _gpb_set(d, **kw):
    d.update(kw)


def _gpb_notify(d):
    def on(r, msg):                                          # runs in the BLE thread: only note it down
        if len(msg) >= 2 and msg[0] == 0xF5 and msg[1] == 0xF5:
            p = pb_dec(msg[2:])
            d["ls"], d["ls_err"] = _pb1(p, 1, d["ls"]), _pb1(p, 2, 0)
        elif len(msg) >= 2 and msg[0] == 0x02 and msg[1] == 0x0C:
            d["prov"] = _pb1(pb_dec(msg[2:]), 1)
        elif len(msg) >= 2 and msg[0] == 0xF5 and msg[1] == 0xEF:
            d["cohn_live"] = pb_dec(msg[2:])
        elif msg[:1] == b"\x93" and len(msg) >= 2 and msg[1] == 0:
            _gpb_status_vals(d, gpb_tlv(msg[2:]))
    return on


def _gpb_gone(d):
    def on():
        if d["zustand"] not in ("off", "asleep"):
            _gpb_set(d, zustand="reconnecting" if (d["awake"] or d["want"]) else "off",
                     fehler="connection lost - reconnecting" if (d["awake"] or d["want"]) else "")
            _gpb_log("GoPro %s: Bluetooth connection lost" % (d["rec"].get("name") or "?"))
    return on


def _gpb_status_vals(d, v):
    def num(k):
        b = v.get(GPB_ST[k])
        return int.from_bytes(b, "big") if b else None
    a = num("batt")
    if a is not None:
        d["akku"] = max(0, min(100, a))
    for k in ("bars", "busy", "hot"):
        x = num(k)
        if x is not None:
            d[k] = x if k == "bars" else bool(x)


def _gpb_conn(d, pair=False, timeout=20.0):
    """connected client (connects, pairs the first time, says hello); raises GpbError"""
    c = d["client"]
    if c is not None and c.connected:
        return c
    if gpb_bleak() is None:
        raise GpbError("bleak missing - install it on this page")
    if not gpb_adapter():
        raise GpbError("no Bluetooth adapter")
    c = gopro_ble_client(d["rec"]["addr"], _gpb_notify(d), _gpb_gone(d))
    if not c.connect(timeout, pair=True):
        e = c.last_err or "GoPro not found - is it switched on and near?"
        raise GpbError(e if e in GPB_TXT_ERRS else ("pairing failed - put the GoPro into pairing mode" if pair else "GoPro not found - is it switched on and near?"))
    d["client"] = c
    c.write("0072", b"\x50", 4.0)                             # Set Analytics: «third-party client» (Open GoPro asks for it)
    _gpb_set(d, zustand="connected", fehler="", retry=0)
    return c


def _gpb_cmd(c, u, payload, timeout=8.0, want_ok=True):
    r = c.write(u, payload, timeout)
    if r is None:
        raise GpbError("no answer from the GoPro")
    if want_ok and not gpb_is_pb(u, payload) and len(r) >= 2 and r[1] != 0:
        raise GpbError("the GoPro refused the command")
    return r


def _gpb_pb(c, u, f, a, msg=b"", timeout=8.0):
    r = c.write(u, bytes([f, a]) + msg, timeout)
    if r is None:
        raise GpbError("no answer from the GoPro")
    return pb_dec(r[2:])


def gpb_hwinfo(c):
    r = _gpb_cmd(c, "0072", b"\x3c")
    f = gpb_lv(r[2:])
    s = lambda k: f[k].decode("utf-8", "replace").strip("\x00") if len(f) > k else ""
    return {"model_no": int.from_bytes(f[0], "big") if f else 0, "modell": s(1), "fw": s(3), "ap_ssid": s(5)}


def gpb_status(dev):
    """G1: {"verbunden", "akku", "streamt", "fehler"}; «streamt» only when the camera streams AND the receiver has the picture"""
    i = dev.get("id") if isinstance(dev, dict) else dev
    d = GPB["dev"].get(str(i or ""))
    if d is None or not d["rec"].get("addr"):
        return {"verbunden": False, "akku": None, "streamt": False, "fehler": "not paired yet - search and pair first"}
    c = d["client"]
    on = d["zustand"] == "streaming"
    if on and d["net"] != "ap" and isinstance(dev, dict) and callable(globals().get("_rtmp_status")):
        try:
            on = bool(_rtmp_status(dev).get("streamt"))
        except Exception:
            on = False
    f = d["fehler"] or ("" if on or d["zustand"] != "streaming" else "waiting for the GoPro stream")
    return {"verbunden": bool(c is not None and c.connected), "akku": d["akku"], "streamt": on, "fehler": f}


def gpb_faehig_ok():
    """can Bluetooth be used here? (ok, english reason)"""
    if gpb_bleak() is None:
        return False, "bleak missing - install it on this page"
    if not gpb_adapter():
        return False, "no Bluetooth adapter"
    return True, ""


GPB_FAEHIG = {"titel": "HERO9 and newer: Bluetooth (Open GoPro)", "modelle": list(GPB_MODELLE), "akku": True, "steuern": True}


def gpb_model_id(name):
    n = gpb_model_no(name)
    ids = [m for m, _n in GOPRO_MODELLE]
    return "hero%d" % n if "hero%d" % n in ids else ids[-1]


def gpb_pair(addr, name="", gid=None):
    """first connection: pair (the GoPro must be in pairing mode), check the model, keep the pairing data; gid = the GoPro of G1
    with the way «ble» (none: a new one is added). Returns the id."""
    addr = str(addr or "").strip()
    if not GPB_ADDR_RE.match(addr):
        raise GpbError("unknown device")
    if gid:
        _gpb_dev(gid, paired=False)
    d = _gpb_new({"addr": addr, "name": str(name or "GoPro")[:40], "known": [], "t": int(time.time())})
    with d["lock"]:
        try:
            c = _gpb_conn(d, pair=True, timeout=25.0)
            hw = gpb_hwinfo(c)
            if gpb_model_no(hw["modell"]) < 9:
                c.close(); d["client"] = None
                raise GpbError("not a Hero 9 or newer - for a Hero 8 use the Hero 8 way")
            d["rec"].update(modell=hw["modell"], fw=hw["fw"], name=d["rec"].get("name") or hw["ap_ssid"] or "GoPro")
            if not gid:
                ok_, err, gid = gopro_add(d["rec"]["name"], gpb_model_id(hw["modell"]), "ble")
                if not ok_:
                    c.close(); d["client"] = None
                    raise GpbError(err)
            old = GPB["dev"].get(gid)
            if old is not None and old["client"] is not None and old["client"] is not c:
                old["client"].close()
            if old is not None:
                d["net"] = old["net"]; d["rec"]["net"] = old["rec"].get("net") or old["net"]
            GPB["dev"][gid] = d
            gpb_save()
            d["awake"] = True
            _gpb_set(d, zustand="connected", step="", fehler="")
            _gpb_refresh(d)
            _gpb_log("GoPro %s (%s, %s): paired over Bluetooth" % (d["rec"]["name"], hw["modell"], hw["fw"]))
            gpb_watch()
            return gid
        except GpbError:
            c = d["client"]
            if c is not None:
                c.close()
            raise


def gpb_forget(i):
    """only the Bluetooth pairing (the GoPro itself stays at G1 until «Remove»)"""
    d = GPB["dev"].get(str(i or ""))
    if d is None:
        return
    d["want"] = d["awake"] = False
    c = d["client"]
    if c is not None:
        if c.connected and d["zustand"] == "streaming":
            c.write("0072", b"\x01\x01\x00", 4.0)
        c.close()
    GPB["dev"].pop(i, None)
    gpb_save()
    _gpb_log("GoPro %s: pairing data removed" % (d["rec"].get("name") or "?"))


def gpb_power(i, on):
    """«on» = connect (wakes the camera, it then stays awake), «off» = stop the stream, sleep, disconnect"""
    d = _gpb_dev(i)
    with d["lock"]:
        if on:
            d["awake"] = True
            _gpb_set(d, zustand="connecting", fehler="")
            try:
                _gpb_conn(d)
                _gpb_refresh(d)
            except GpbError as e:
                _gpb_set(d, zustand="error", fehler=str(e)); raise
            gpb_watch()
            return
        d["awake"] = d["want"] = False
        c = d["client"]
        if c is not None and c.connected:
            if d["zustand"] == "streaming":
                c.write("0072", b"\x01\x01\x00", 5.0)
            c.write("0072", b"\x05", 5.0)                       # Sleep (the camera still advertises for 8 h)
            c.close()
        d["client"] = None
        _gpb_set(d, zustand="asleep", quelle="", fehler="")


def _gpb_refresh(d):
    c = d["client"]
    if c is None or not c.connected:
        return False
    r = c.write("0076", bytes([0x13] + list(GPB_ST.values())), 5.0)
    if r and len(r) >= 2 and r[1] == 0:
        _gpb_status_vals(d, gpb_tlv(r[2:]))
        d["t_stat"] = time.time()
        _gpb_set(d)
        return True
    return False


def _gpb_wait(f, secs, step=0.2):
    t = time.time()
    while time.time() - t < secs:
        if f():
            return True
        time.sleep(step)
    return bool(f())


def _gpb_host(net):
    if net == "hotspot":
        hs = STATE.get("hotspot") if isinstance(STATE.get("hotspot"), dict) else {}
        if not hs.get("on"):
            raise GpbError("MoveEye's own WLAN is off - switch it on first")
        return hs.get("ip") or "10.42.0.1"
    try:
        ip = wifi_ip(WIFI.get("iface") or None)
    except Exception:
        ip = ""
    if not ip:
        raise GpbError("MoveEye has no address in this WLAN")
    return ip.split("/")[0]


def _gpb_join(d, c, ssid, pw):
    """the camera joins a WLAN as a station: known name -> RequestConnect, else RequestConnectNew (password only this once)"""
    known = d["rec"].setdefault("known", [])
    d["prov"] = None
    res = None
    if ssid in known or not pw:
        p = _gpb_pb(c, "0091", 0x02, 0x04, pb_enc([(1, "s", ssid)]), 10.0)
        res = p
        if _pb1(p, 1) != 1 and not pw:
            raise GpbError("the GoPro does not know this WLAN yet - enter the password once")
    if res is None or _pb1(res, 1) != 1:
        _gpb_secret(pw)
        res = _gpb_pb(c, "0091", 0x02, 0x05, pb_enc([(1, "s", ssid), (2, "s", pw), (10, "v", 1)]), 10.0)
        pw = None
        if _pb1(res, 1) != 1:
            raise GpbError("the GoPro could not join the WLAN")
    st = _pb1(res, 2)
    if st in GPB_PROV_OK:
        d["prov"] = st
    wait = max(10, min(90, int(_pb1(res, 3, 30) or 30) + 5))
    _gpb_wait(lambda: d["prov"] in GPB_PROV_OK or d["prov"] in GPB_PROV_ERR, wait, 0.25)
    if d["prov"] not in GPB_PROV_OK:
        raise GpbError(GPB_PROV_ERR.get(d["prov"], "the GoPro could not join the WLAN"))
    if ssid not in known:
        known.append(ssid)
        del known[:-5]
        gpb_save()


def gpb_push_url(gid, host):
    """where the GoPro sends its picture: the receiver of G1 (port and path with the key of this GoPro)"""
    g = gopro_dev(gid)
    if not g:
        raise GpbError("unknown device")
    return gopro_rtmp_url(g, host)


def gpb_start(dev):
    """G1 (gopro_quelle, from the camera thread): never blocks. Streaming -> the address; otherwise the start runs in the
    background (once, with pauses after errors) and "" comes back - G1 asks again."""
    i = dev.get("id") if isinstance(dev, dict) else dev
    try:
        d = _gpb_dev(i)
    except GpbError:
        return ""
    if d["zustand"] == "streaming" and d["quelle"]:
        return d["quelle"]
    d["want"] = d["awake"] = True
    if not d["job"] and time.time() >= d["next"]:
        _gpb_job(i, lambda: gpb_start_now(i))
    gpb_watch()
    return ""


def gpb_start_now(i, net=None, ssid="", password=""):
    """start the stream now (blocks up to ~2 min); the video source or '' (the reason in fehler)"""
    d = _gpb_dev(i)
    net = net if net in ("hotspot", "home", "ap") else d["net"]
    with d["lock"]:
        d["want"], d["awake"], d["net"] = True, True, net
        if net != d["rec"].get("net"):
            d["rec"]["net"] = net; gpb_save()
        if ssid and net == "home":
            d["rec"]["home_ssid"] = str(ssid)[:32]; gpb_save()
        _gpb_set(d, zustand="starting", fehler="", step="connect")
        try:
            src = _gpb_start_ap(d) if net == "ap" else _gpb_start_rtmp(d, i, net, password)
            password = None
            if not d["want"]:                                # «stop» came meanwhile
                raise GpbError("stopped")
            _gpb_set(d, zustand="streaming", quelle=src, step="", retry=0)
            _gpb_log("GoPro %s: stream started (%s)" % (d["rec"].get("name") or "?", {"hotspot": "MoveEye WLAN", "home": "home WLAN", "ap": "camera WLAN"}[net]))
            gpb_watch()
            return src
        except GpbError as e:
            password = None
            if str(e) == "stopped":
                _gpb_halt(d)
                return ""
            if str(e) in GPB_FATAL:                          # needs the user (password, WLAN, adapter): no retry
                d["want"] = False
            d["next"] = time.time() + GPB_BACKOFF[min(d["retry"], len(GPB_BACKOFF) - 1)]
            c = d["client"]
            _gpb_set(d, zustand="connected" if (c is not None and c.connected and not d["want"]) else "error", quelle="", step="", fehler=str(e))
            _gpb_log("GoPro %s: stream not started - %s" % (d["rec"].get("name") or "?", e))
            gpb_watch()
            return ""


def gpb_wlan(i, net, ssid="", password=""):
    """bring the GoPro into a WLAN now (the password goes to the camera once, never saved); afterwards «Start» needs no password"""
    d = _gpb_dev(i)
    with d["lock"]:
        _gpb_set(d, step="wlan", fehler="")
        try:
            c = _gpb_conn(d)
            if net == "hotspot":
                _gpb_host("hotspot")
                ssid, password = CFG.get("hotspot_ssid") or "MoveEye", hotspot_password()
            ssid = str(ssid or d["rec"].get("home_ssid") or "")[:32]
            if not ssid:
                raise GpbError("enter the WLAN name")
            if net == "home":
                d["rec"]["home_ssid"] = ssid
            d["net"] = d["rec"]["net"] = net if net in ("hotspot", "home") else d["net"]
            _gpb_secret(password)
            _gpb_join(d, c, ssid, password or "")
            password = None
            c.write("0091", bytes([0x02, 0x78]), 5.0)          # leave it again until the stream starts
            gpb_save()
            _gpb_set(d, step="", fehler="")
            _gpb_log("GoPro %s: knows the WLAN «%s» now" % (d["rec"].get("name") or "?", ssid))
        except GpbError as e:
            _gpb_set(d, step="", fehler=str(e)); raise


def _gpb_start_rtmp(d, i, net, password):
    c = _gpb_conn(d)
    if net == "hotspot":
        ssid, pw = CFG.get("hotspot_ssid") or "MoveEye", hotspot_password()
    else:
        ssid, pw = d["rec"].get("home_ssid") or "", password or ""
        if not ssid:
            raise GpbError("enter the WLAN name")
    host = _gpb_host(net)
    url = gpb_push_url(i, host)
    g = gopro_dev(i) or {}
    d["step"] = "wlan"; _gpb_set(d)
    _gpb_join(d, c, ssid, pw)
    pw = None
    if not d["want"]:
        raise GpbError("stopped")
    d["step"] = "config"; d["ls"] = None; _gpb_set(d)
    p = _gpb_pb(c, "0076", 0xF5, 0x74, pb_enc([(1, "v", 1), (1, "v", 2)]))
    d["ls"] = _pb1(p, 1, d["ls"])
    res = GPB_RES.get(str(g.get("res") or "720"), 7)
    p = _gpb_pb(c, "0072", 0xF1, 0x79, pb_enc([(1, "s", url), (2, "v", 1 if g.get("copy") else 0), (3, "v", res),
                                                (7, "v", 800), (8, "v", 4000), (9, "v", 2500)]), 10.0)
    if _pb1(p, 1) not in (None, 1):
        raise GpbError("the GoPro did not get ready for the stream")

    def ready():
        if d["ls"] in (2, 3) or not d["want"]:
            return True
        q = c.write("0076", bytes([0xF5, 0x74]), 4.0)
        if q:
            x = pb_dec(q[2:])
            d["ls"], d["ls_err"] = _pb1(x, 1, d["ls"]), _pb1(x, 2, 0)
        return d["ls"] in (2, 3, 5, 7)
    _gpb_wait(ready, 40, 1.0)
    if not d["want"]:
        raise GpbError("stopped")
    if d["ls"] == 7:
        raise GpbError("live stream not possible with the current lens setting")
    if d["ls"] not in (2, 3):
        raise GpbError("the GoPro did not get ready for the stream")
    d["step"] = "shutter"; _gpb_set(d)
    if d["ls"] != 3:
        _gpb_cmd(c, "0072", b"\x01\x01\x01")
    _gpb_wait(lambda: d["ls"] in (3, 5), 25, 0.5)
    if d["ls"] == 5:
        raise GpbError("live stream failed on the GoPro")
    return _rx_local_url(g) if g else ""


def _gpb_start_ap(d):
    """camera WLAN: only with a second WLAN adapter (MoveEye keeps its own WLAN / the phone); preview stream udp://@:8554"""
    iface = str(CFG.get("gopro_ble_ap_iface") or "wlan1")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", iface) or iface == (WIFI.get("iface") or "wlan0") or iface == WIFI.get("ap_iface"):
        raise GpbError("the camera WLAN needs a second WLAN adapter (it would cut off your phone)")
    c = _gpb_conn(d)
    d["step"] = "ap"; _gpb_set(d)
    _gpb_cmd(c, "0072", b"\x17\x01\x01")
    ssid = (c.read("0002") or b"").decode("utf-8", "replace").strip("\x00")
    pw = (c.read("0003") or b"").decode("utf-8", "replace").strip("\x00")
    _gpb_secret(pw)
    if not ssid or not pw:
        raise GpbError("could not join the camera WLAN")
    ok_ = _gpb_nm_join(ssid, pw, iface)
    pw = None
    if not ok_:
        raise GpbError("could not join the camera WLAN")
    d["ap_con"] = ssid
    if not _gpb_http("http://10.5.5.9:8080/gopro/camera/stream/start"):
        raise GpbError("preview stream did not start")
    return "udp://@:8554"


def _gpb_nm_join(ssid, pw, iface):
    f = GPB.get("nm_join")                                   # tests: stand-in (no nmcli)
    if callable(f):
        return f(ssid, pw, iface)
    nm = shutil.which("nmcli")
    if not nm:
        return False
    try:
        r = subprocess.run([nm, "--ask", "--wait", "40", "device", "wifi", "connect", ssid, "ifname", iface], input=pw + "\n",
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _gpb_http(url, timeout=5.0):
    f = GPB.get("http")                                      # tests: stand-in
    if callable(f):
        return f(url)
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def _gpb_halt(d):
    """stop the stream on the camera (lock held)"""
    c = d["client"]
    if c is not None and c.connected:
        if d["net"] == "ap":
            _gpb_http("http://10.5.5.9:8080/gopro/camera/stream/stop")
            c.write("0072", b"\x17\x01\x00", 5.0)
        else:
            c.write("0072", b"\x01\x01\x00", 5.0)
            c.write("0091", bytes([0x02, 0x78]), 5.0)        # RequestReleaseNetwork: the camera leaves the WLAN
    if d["ap_con"] and not callable(GPB.get("nm_join")) and shutil.which("nmcli"):
        try:
            subprocess.run(["nmcli", "connection", "down", "id", d["ap_con"]], capture_output=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            pass
    d["ap_con"] = ""
    _gpb_set(d, zustand="connected" if (c is not None and c.connected) else "off", quelle="", fehler="", step="")


def gpb_stop(dev):
    """G1: stop the stream (the camera stays connected and awake). Never waits long: a running start sees «want» and stops."""
    i = dev.get("id") if isinstance(dev, dict) else dev
    d = GPB["dev"].get(str(i or ""))
    if d is None:
        return
    d["want"] = False
    if not d["lock"].acquire(timeout=3.0):
        return
    try:
        _gpb_halt(d)
    finally:
        d["lock"].release()
    _gpb_log("GoPro %s: stream stopped" % (d["rec"].get("name") or "?"))


# ---- COHN (camera on the home network, Hero 12 and newer): certificate + access only in the pairing file ------------------------
def gpb_cohn_setup(i, ssid="", password=""):
    d = _gpb_dev(i)
    if gpb_model_no(d["rec"].get("modell")) < 12:
        raise GpbError("COHN needs a Hero 12 or newer")
    with d["lock"]:
        _gpb_set(d, step="cohn", fehler="")
        try:
            c = _gpb_conn(d)
            ssid = str(ssid or d["rec"].get("home_ssid") or "")[:32]
            if not ssid:
                raise GpbError("enter the WLAN name")
            d["rec"]["home_ssid"] = ssid
            _gpb_join(d, c, ssid, password or "")
            password = None
            _gpb_pb(c, "0072", 0xF1, 0x67, pb_enc([(1, "v", 0)]), 15.0)
            p = _gpb_pb(c, "0076", 0xF5, 0x6E, b"", 10.0)
            cert = _pbs(p, 2)
            if "BEGIN CERTIFICATE" not in cert:
                raise GpbError("COHN setup failed")
            _gpb_pb(c, "0072", 0xF1, 0x65, pb_enc([(1, "v", 1)]), 10.0)
            d["cohn_live"] = _gpb_pb(c, "0076", 0xF5, 0x6F, pb_enc([(1, "v", 1)]), 10.0)

            def done():
                x = d["cohn_live"]
                return _pb1(x, 1) == 1 and _pb1(x, 2) == 27 and _pbs(x, 5) and _pbs(x, 3)
            if not _gpb_wait(done, 45, 0.5):
                raise GpbError("COHN setup failed")
            x = d["cohn_live"]
            _gpb_secret(_pbs(x, 4))
            d["rec"]["cohn"] = {"cert": cert, "user": _pbs(x, 3), "pass": _pbs(x, 4), "ip": _pbs(x, 5), "ssid": _pbs(x, 7) or ssid}
            gpb_save()
            _gpb_set(d, step="")
            _gpb_log("GoPro %s: COHN ready on the home WLAN (IP %s)" % (d["rec"].get("name") or "?", _pbs(x, 5)))
        except GpbError as e:
            _gpb_set(d, step="", fehler=str(e)); raise


def gpb_cohn_get(d, path, timeout=5.0):
    """HTTPS to the camera on the home WLAN with its own root certificate and basic auth (COHN); (status, body) or (0, b"")"""
    co = d["rec"].get("cohn") or {}
    if not (co.get("cert") and co.get("ip") and co.get("user")):
        return 0, b""
    f = GPB.get("cohn_http")                                 # tests: stand-in
    if callable(f):
        return f(co, path)
    import ssl, http.client, base64 as _b64
    try:
        ctx = ssl.create_default_context(cadata=co["cert"])
        ctx.check_hostname = False                               # the camera's certificate names no host; the chain is checked
        h = http.client.HTTPSConnection(co["ip"], 443, timeout=timeout, context=ctx)
        h.request("GET", path, headers={"Authorization": "Basic " + _b64.b64encode(("%s:%s" % (co["user"], co["pass"])).encode()).decode()})
        r = h.getresponse(); body = r.read(); h.close()
        return r.status, body
    except Exception:
        return 0, b""


# ---- the watch: keep awake, battery, lost connection / stream -> reconnect / restart ---------------------------------------------
def gpb_watch():
    with GPB["lock"]:
        t = GPB["wd"]
        if t is not None and t.is_alive():
            return
        GPB["wd"] = threading.Thread(target=_gpb_watch_loop, name="gopro-ble", daemon=True)
        GPB["wd"].start()


def _gpb_watch_loop():
    while True:
        busy = False
        for i, d in list(GPB["dev"].items()):
            try:
                busy = _gpb_watch_one(i, d) or busy
            except Exception as e:
                _gpb_log("GoPro watch: %s" % type(e).__name__)
        if not busy and not GPB["dev"]:
            with GPB["lock"]:
                GPB["wd"] = None
            return
        time.sleep(GPB.get("tick") or 1.0)


def _gpb_watch_one(i, d):
    if not (d["awake"] or d["want"]) or not d["rec"].get("addr"):
        return False
    now = time.time()
    if d["job"] or not d["lock"].acquire(blocking=False):    # a start / stop is running
        return True
    try:
        c = d["client"]
        if c is not None and c.connected:
            if now - d["t_keep"] >= GPB_KEEPALIVE_S:
                d["t_keep"] = now
                c.write("0074", b"\x5b\x01\x42", 4.0)            # Keep Alive
            if now - d["t_stat"] >= GPB_STATUS_S:
                _gpb_refresh(d)
            lost = d["want"] and d["zustand"] == "streaming" and d["net"] != "ap" and d["ls"] in (4, 5, 7)
            if not lost and not (d["want"] and d["zustand"] in ("error", "reconnecting", "connected")):
                return True
            if lost and d["fehler"] != "stream lost - restarting":
                _gpb_log("GoPro %s: stream lost - restarting" % (d["rec"].get("name") or "?"))
                _gpb_set(d, zustand="reconnecting", quelle="", fehler="stream lost - restarting", next=now + GPB_BACKOFF[0], retry=0)
                return True
        else:
            if d["rec"].get("cohn") and now - d["t_stat"] >= GPB_STATUS_S:   # out of Bluetooth range: battery over COHN
                d["t_stat"] = now
                st, body = gpb_cohn_get(d, "/gopro/camera/state")
                try:
                    v = json.loads(body.decode()).get("status", {}) if st == 200 else {}
                    if "70" in v:
                        _gpb_set(d, akku=int(v["70"]))
                except (ValueError, AttributeError):
                    pass
        if now < d["next"]:
            return True
        n = d["retry"]
        d["retry"], d["next"] = n + 1, now + GPB_BACKOFF[min(n, len(GPB_BACKOFF) - 1)]
        if d["zustand"] != "reconnecting":
            _gpb_set(d, zustand="reconnecting", quelle="" if d["want"] else d["quelle"])
    finally:
        d["lock"].release()
    if d["want"]:
        _gpb_log("GoPro %s: restarting the stream (try %d)" % (d["rec"].get("name") or "?", d["retry"]))
        g = GOPRO.get(i)
        if g is not None:
            g["quelle"] = ""                                 # G1 asks gpb_start again for the address
        _gpb_job(i, lambda: gpb_start_now(i))
    else:
        def again():
            try:
                with d["lock"]:
                    _gpb_conn(d)
                    _gpb_refresh(d)
            except GpbError as e:
                _gpb_set(d, zustand="reconnecting", fehler=str(e))
        _gpb_job(i, again)
    return True


# ---- install bleak (only after «yes» on the page) --------------------------------------------------------------------------------
def gpb_install(confirm=False):
    if not confirm:
        return False, "install refused - confirm first"
    st = GPB["install"]
    if st["running"]:
        return True, ""
    st.update(running=True, msg="installing …", ok=None)

    def run():
        ok_, msg = False, ""
        try:
            pre = [] if (hasattr(os, "geteuid") and os.geteuid() == 0) else (["sudo", "-n"] if shutil.which("sudo") else None)
            apt = shutil.which("apt-get")
            if apt and pre is not None:
                env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
                r = subprocess.run(pre + [apt, "install", "-y", "--no-install-recommends", "python3-bleak"], capture_output=True, text=True,
                                   timeout=900, env=env, stdin=subprocess.DEVNULL)
                ok_, msg = r.returncode == 0, ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-1:] or [""]
                msg = msg[0][:140]
            if not ok_:
                r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "bleak"], capture_output=True,
                                   text=True, timeout=900, stdin=subprocess.DEVNULL)
                ok_ = r.returncode == 0
                msg = (((r.stdout or "") + (r.stderr or "")).strip().splitlines() or [""])[-1][:140]
            if ok_:
                import importlib, site
                importlib.invalidate_caches()
                try:
                    if site.getusersitepackages() not in sys.path:
                        sys.path.append(site.getusersitepackages())
                except Exception:
                    pass
                GPB["bleak"] = None
                ok_ = gpb_bleak() is not None
        except (OSError, subprocess.SubprocessError) as e:
            msg = type(e).__name__
        st.update(running=False, ok=ok_, msg="installed" if ok_ else ("installation failed: " + msg))
        _gpb_log("GoPro: bleak " + ("installed" if ok_ else "not installed (%s)" % msg))
    threading.Thread(target=run, name="gopro-ble-install", daemon=True).start()
    return True, ""


# ---- what the page / the window gets ---------------------------------------------------------------------------------------------
def gpb_scan_start():
    s = GPB["scan"]
    if s["running"]:
        return True, ""
    ok_, why = gpb_faehig_ok()
    if not ok_:
        return False, why
    s.update(running=True, err="")

    def run():
        try:
            found = gopro_ble_scan(8.0)
            s["found"] = found[:12]
            s["err"] = "" if found else "no GoPro found - is it in pairing mode and near?"
        except Exception as e:
            s["found"], s["err"] = [], str(e) if str(e) in GPB_TXT_ERRS else "Bluetooth search failed"
        s.update(running=False, t=time.time())
    threading.Thread(target=run, name="gopro-ble-scan", daemon=True).start()
    return True, ""


def gpb_state(lang=None):
    L = norm_lang(lang)
    T = lambda s: tr_err(s, L) if s else ""
    gopro_sync()
    for gid in [k for k, d in GPB["dev"].items() if (GOPRO.get(k) or {}).get("weg") != "ble"]:   # removed at G1: forget the pairing
        gpb_forget(gid)
    devs = []
    for gid, g in GOPRO.items():
        if g.get("weg") != "ble":
            continue
        d = GPB["dev"].get(gid) or _gpb_new({})
        r = d["rec"]
        devs.append({"id": gid, "name": g.get("name") or "GoPro", "paired": bool(r.get("addr")), "bt_name": r.get("name") or "",
                     "modell": r.get("modell") or "", "fw": r.get("fw") or "", "zustand": d["zustand"], "akku": d["akku"], "bars": d["bars"],
                     "hot": d["hot"], "fehler": T(d["fehler"]), "net": d["net"], "home_ssid": r.get("home_ssid") or "", "step": d["step"],
                     "want": d["want"], "job": d["job"], "aktiv": bool(g.get("aktiv")),
                     "cohn_ok": gpb_model_no(r.get("modell")) >= 12, "cohn": bool(r.get("cohn")), "cohn_ip": (r.get("cohn") or {}).get("ip", ""),
                     "known": list(r.get("known") or [])})
    s = GPB["scan"]
    known = {d["rec"]["addr"].upper() for d in GPB["dev"].values() if d["rec"].get("addr")}
    hs = STATE.get("hotspot") if isinstance(STATE.get("hotspot"), dict) else {}
    ok_, why = gpb_faehig_ok()
    return {"bleak": gpb_bleak() is not None, "adapter": gpb_adapter(), "ok": ok_, "why": T(why), "install": dict(GPB["install"], msg=T(GPB["install"]["msg"])),
            "scan": {"running": s["running"], "found": [dict(f, known=f["addr"].upper() in known) for f in s["found"]], "err": T(s["err"])},
            "devices": devs, "pairing": bool(GPB["pairing"]), "hotspot": {"on": bool(hs.get("on")), "ssid": CFG.get("hotspot_ssid") or ""}}


def _gpb_job(i, fn):
    """long actions run in the background, the page follows the state"""
    d = _gpb_dev(i, paired=False)
    if d["job"]:
        return False, "the GoPro is busy - try again in a moment"
    d["job"] = True

    def run():
        try:
            fn()
        except GpbError as e:
            _gpb_set(d, fehler=str(e))
        except Exception as e:
            _gpb_set(d, fehler="no answer from the GoPro")
            _gpb_log("GoPro: %s" % type(e).__name__)
        finally:
            d["job"] = False
    threading.Thread(target=run, name="gopro-ble-job", daemon=True).start()
    return True, ""


def gpb_action(a, d):
    """one action of the page / the window (administrator only); (ok, english error)"""
    i = str(d.get("id") or "")
    if a == "install":
        return gpb_install(d.get("confirm") is True)
    if a == "scan":
        return gpb_scan_start()
    if a == "pair":                                           # with id: this GoPro of G1; without: a new GoPro is added
        addr = str(d.get("addr") or "")
        if not GPB_ADDR_RE.match(addr):
            return False, "unknown device"
        if i:
            _gpb_dev(i, paired=False)
        if GPB["pairing"]:
            return False, "the GoPro is busy - try again in a moment"
        GPB["pairing"] = addr
        GPB["scan"]["err"] = ""

        def pair():
            try:
                gid = gpb_pair(addr, d.get("name"), i or None)
                GPB["scan"]["found"] = [f for f in GPB["scan"]["found"] if f["addr"].upper() != addr.upper()]
                GPB["last_pair"] = gid
            except GpbError as e:
                GPB["scan"]["err"] = str(e)
                if i and i in GPB["dev"]:
                    _gpb_set(GPB["dev"][i], fehler=str(e))
            finally:
                GPB["pairing"] = ""
        threading.Thread(target=pair, name="gopro-ble-pair", daemon=True).start()
        return True, ""
    try:
        x = _gpb_dev(i, paired=a not in ("forget", "net"))
    except GpbError as e:
        return False, str(e)
    if a == "forget":
        gpb_forget(i); return True, ""
    if a == "power":
        on = d.get("on") is True
        return _gpb_job(i, lambda: gpb_power(i, on))
    if a == "net":
        net = d.get("net")
        if net not in ("hotspot", "home", "ap"):
            return False, "invalid value"
        x["net"] = x["rec"]["net"] = net
        if d.get("ssid") is not None:
            x["rec"]["home_ssid"] = str(d.get("ssid") or "")[:32]
        if x["rec"].get("addr"):
            gpb_save()
        return True, ""
    if a == "wlan":
        net, ssid, pw = d.get("net") or x["net"], str(d.get("ssid") or "")[:32], str(d.get("password") or "")[:63]
        d["password"] = None
        _gpb_secret(pw)
        return _gpb_job(i, lambda: gpb_wlan(i, net, ssid, pw))
    if a == "stream":                                         # the window: start / stop through G1 (extra camera)
        if d.get("on") is not True:
            return gopro_stop(i)
        net, ssid, pw = d.get("net"), str(d.get("ssid") or "")[:32], str(d.get("password") or "")[:63]
        d["password"] = None
        _gpb_secret(pw)

        def go():
            gopro_start(i)
            gpb_start_now(i, net, ssid, pw)
        return _gpb_job(i, go)
    if a == "cohn":
        ssid, pw = str(d.get("ssid") or "")[:32], str(d.get("password") or "")[:63]
        d["password"] = None
        _gpb_secret(pw)
        return _gpb_job(i, lambda: gpb_cohn_setup(i, ssid, pw))
    return False, "unknown action"


gopro_register_weg("ble", start=gpb_start, stop=gpb_stop, status=gpb_status, faehig=GPB_FAEHIG)


# ---- web: /api/gopro/ble (administrator only; never with an app key, not in operator mode) ------------------------------------
ADMIN_GET = ADMIN_GET + ("/api/gopro/ble",)
APPKEY_DENY_PATHS.update({"/api/gopro/ble"})
LOCK_DENY_PATHS.update({"/api/gopro/ble"})
_gpb_sx_routes_before = sx_routes


# wraps: sx_routes
def sx_routes(app, watch, reply, body):                    # + /api/gopro/ble (called once by 550)
    _gpb_sx_routes_before(app, watch, reply, body)
    from flask import request, g as g_

    @app.route("/api/gopro/ble", methods=["GET", "POST"])
    def api_gopro_ble():
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if getattr(g_, "role", "admin") != "admin":
            return reply({"ok": False, "error": tr_err("not allowed", L)}, 403)
        if request.method == "POST":
            d = body()
            d = d if isinstance(d, dict) else {}
            L = norm_lang(d.get("lang") or L)
            try:
                ok_, err = gpb_action(str(d.get("action") or ""), d)
            except GpbError as e:
                ok_, err = False, str(e)
            d.pop("password", None)
            if not ok_:
                return reply({"ok": False, "error": tr_err(err, L), "state": gpb_state(L)}, 400)
        return reply({"ok": True, "state": gpb_state(L)})


# ---- the window (Tk): Mehr -> «📷 GoPro (Bluetooth)» ---------------------------------------------------------------------------
if GUI_OK:
    def _gpb_tk_win(self):
        w = getattr(self, "_gpb_top", None)
        if w is not None and w.winfo_exists():
            w.lift(); return
        w = self._gpb_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("GoPro over Bluetooth (Hero 9 and newer)"))
        w.configure(bg=C["bg"]); w.geometry("560x520")
        tk.Label(w, text="📷 " + tr("GoPro over Bluetooth (Hero 9 and newer)"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 13, "bold"),
                 anchor="w").pack(fill="x", padx=12, pady=(10, 2))
        st = tk.Label(w, text="", bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), wraplength=520, justify="left", anchor="w")
        st.pack(fill="x", padx=12)
        lb = tk.Listbox(w, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10), height=8, bd=0, activestyle="none", exportselection=False)
        lb.pack(fill="both", expand=True, padx=12, pady=8)
        net = tk.StringVar(value="hotspot")
        nf = tk.Frame(w, bg=C["bg"]); nf.pack(fill="x", padx=12)
        for k, n in (("hotspot", "MoveEye's own WLAN"), ("home", "Home WLAN"), ("ap", "Camera WLAN (second WLAN adapter)")):
            tk.Radiobutton(nf, text=tr(n), variable=net, value=k, bg=C["bg"], fg=C["txt"], selectcolor=C["panel"], activebackground=C["bg"],
                           font=("DejaVu Sans", 9), anchor="w").pack(side="left", padx=(0, 8))
        ef = tk.Frame(w, bg=C["bg"]); ef.pack(fill="x", padx=12, pady=(4, 0))
        tk.Label(ef, text=tr("WLAN name"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9)).pack(side="left")
        e_ssid = tk.Entry(ef, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], width=16); e_ssid.pack(side="left", padx=4)
        tk.Label(ef, text=tr("WLAN password"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9)).pack(side="left")
        e_pw = tk.Entry(ef, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], width=14, show="•"); e_pw.pack(side="left", padx=4)
        rows = {"ids": []}

        def sel():
            s = lb.curselection()
            return rows["ids"][s[0]] if s and s[0] < len(rows["ids"]) else None

        def do(a, **kw):
            sid = sel()
            if sid is None and a not in ("scan", "install"):
                return
            if sid and sid.startswith("scan:"):
                if a != "pair":
                    return
                f = GPB["scan"]["found"][int(sid[5:])]
                kw.update(addr=f["addr"], name=f["name"])
                free = [x["id"] for x in gpb_state()["devices"] if not x["paired"]]
                if free:
                    kw["id"] = free[0]                        # a GoPro added on /gopro without pairing yet
            elif sid:
                kw["id"] = sid
            if a == "stream" and kw.get("on"):
                kw.update(net=net.get(), ssid=e_ssid.get().strip(), password=e_pw.get())
                e_pw.delete(0, "end")
            if a == "install":
                from tkinter import messagebox
                if not messagebox.askyesno("MoveEye", tr("Install the Bluetooth package «bleak» now?"), parent=w):
                    return
                kw["confirm"] = True
            try:
                ok_, err = gpb_action(a, kw)
            except GpbError as e:
                ok_, err = False, str(e)
            kw.pop("password", None)
            st.config(text=("⚠ " + tr_err(err)) if not ok_ else "…")
        bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=12, pady=6)
        for txt, a, kw in (("🔍 " + tr("Bluetooth search"), "scan", {}), ("🔗 " + tr("Pair"), "pair", {}), ("⏻ " + tr("On"), "power", {"on": True}),
                           ("⏾ " + tr("Off"), "power", {"on": False}), ("▶ " + tr("Start stream"), "stream", {"on": True}),
                           ("⏹ " + tr("Stop stream"), "stream", {"on": False})):
            self._fbtn(bf, txt, lambda a=a, kw=kw: do(a, **dict(kw))).pack(side="left", padx=(0, 4))
        b_inst = self._fbtn(w, "⬇ " + tr("Install «bleak»"), lambda: do("install"))
        self._fbtn(w, tr("Close"), w.destroy, primary=True).pack(side="bottom", anchor="e", padx=12, pady=(0, 10))

        def tick():
            try:
                if not w.winfo_exists():
                    return
                s = gpb_state(CFG.get("lang"))
                keep = sel()
                lb.delete(0, "end"); rows["ids"] = []
                for x in s["devices"]:
                    lb.insert("end", "%s · %s · %s%s%s" % (x["name"], x["modell"], tr(GPB_ZUSTAND.get(x["zustand"], x["zustand"])),
                                                         (" · 🔋 %d %%" % x["akku"]) if x["akku"] is not None else "", ("  ⚠ " + x["fehler"]) if x["fehler"] else ""))
                    rows["ids"].append(x["id"])
                for n, f in enumerate(s["scan"]["found"]):
                    if not f.get("known"):
                        lb.insert("end", "🔗 %s (%s)" % (f["name"] or "GoPro", f["rssi"])); rows["ids"].append("scan:%d" % n)
                if keep in rows["ids"]:
                    lb.selection_set(rows["ids"].index(keep))
                why = ("⚠ " + tr_err("bleak missing - install it on this page")) if not s["bleak"] else ("⚠ " + tr_err("no Bluetooth adapter")) if not s["adapter"] else ""
                if s["install"]["msg"]:
                    why = s["install"]["msg"]
                if s["scan"]["running"]:
                    why = "🔍 " + tr("searching …")
                elif s["scan"]["err"] and not s["devices"]:
                    why = "⚠ " + s["scan"]["err"]
                if why:
                    st.config(text=why)
                if not s["bleak"]:
                    b_inst.pack(anchor="w", padx=12)
                else:
                    b_inst.pack_forget()
                w.after(1500, tick)
            except Exception:
                pass
        tick()

    App._gpb_win = _gpb_tk_win
    _gpb_tk_more_base = App._tk_more_bar

    def _gpb_tk_more_bar(self, parent):
        f = _gpb_tk_more_base(self, parent)
        row = max([int(x.grid_info().get("row", 0)) for x in f.grid_slaves()] + [-1]) + 1
        self._fbtn(f, "📷 " + tr("GoPro (Bluetooth)"), self._gpb_win).grid(row=row, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639zzzzk Blinki)
    App._tk_more_bar = _gpb_tk_more_bar


# ---- self-test (no Bluetooth, no network) ---------------------------------------------------------------------------------------
def gopro_ble_selftest():
    msg = bytes(range(45))
    fr = gpb_frames(msg)
    assert all(len(x) <= 20 for x in fr) and fr[0][:2] == b"\x20\x2d" and fr[1][0] == 0x80 and fr[2][0] == 0x81, fr
    a = GpbAssembler()
    assert [a.feed(x) for x in fr][-1] == msg
    assert GpbAssembler().feed(b"\x03\x13\x00\x00") == b"\x13\x00\x00"
    p = pb_enc([(1, "s", "rtmp://10.42.0.1:1935/gopro/x"), (2, "v", 0), (3, "v", 7), (10, "v", 1)])
    q = pb_dec(p)
    assert _pbs(q, 1).startswith("rtmp://") and _pb1(q, 3) == 7 and _pb1(q, 2) == 0
    assert gpb_match("0072", b"\xf1\x79")(b"\xf1\xf9\x08\x01") and not gpb_match("0072", b"\xf1\x79")(b"\xf5\xf5")
    assert gpb_match("0076", b"\x13\x46")(b"\x13\x00") and gpb_model_no("HERO12 Black") == 12 and gpb_model_no("HERO8 Black") == 8
    assert gpb_tlv(b"\x46\x01\x55\x02\x01\x03") == {70: b"\x55", 2: b"\x03"}
    return True


SELFTEST_EXTRA.append(("GoPro over Bluetooth: packets, protobuf, answers (639zzzzzzf)", gopro_ble_selftest))
'''
zd_exec(GOPRO_BLE_PY, '639zzzzzzf_gopro_ble.py')

# ---- texts (en = key; de, fr, it, rm) - outside the literal, so that the German stays in the main file -------------------------
GPB_ZUSTAND = {"off": "off", "connecting": "connecting …", "connected": "connected", "asleep": "asleep", "starting": "starting …",
               "streaming": "streaming", "reconnecting": "reconnecting …", "error": "error"}
_HX_GPB = {
    "HERO9 and newer: Bluetooth (Open GoPro)": ("HERO9 und neuer: Bluetooth (Open GoPro)", "HERO9 et plus récente : Bluetooth (Open GoPro)",
                                                "HERO9 e successive: Bluetooth (Open GoPro)", "HERO9 e pli nov: Bluetooth (Open GoPro)"),
    "Bluetooth (Open GoPro)": ("Bluetooth (Open GoPro)", "Bluetooth (Open GoPro)", "Bluetooth (Open GoPro)", "Bluetooth (Open GoPro)"),
    "pairing …": ("koppelt …", "appairage …", "associazione …", "cuppla …"),
    "Forget pairing": ("Kopplung vergessen", "Oublier l'appairage", "Dimentica l'associazione", "Emblidar la cuppladura"),
    "Bring the GoPro into the WLAN": ("GoPro ins WLAN bringen", "Connecter la GoPro au Wi-Fi", "Connetti la GoPro al Wi-Fi", "Colliar la GoPro cun il WLAN"),
    "not paired yet - search and pair first": ("noch nicht gekoppelt – zuerst suchen und koppeln", "pas encore appairée – d'abord rechercher et appairer",
                                               "non ancora associata – prima cerca e associa", "anc betg cupplada – l'emprim tschertgar e cupplar"),
    "waiting for the GoPro stream": ("wartet auf den Strom der GoPro", "attente du flux de la GoPro", "in attesa dello stream della GoPro",
                                     "spetga il flux da la GoPro"),
    "stopped": ("gestoppt", "arrêté", "fermato", "fermà"),
    "GoPro over Bluetooth (Hero 9 and newer)": ("GoPro über Bluetooth (Hero 9 und neuer)", "GoPro par Bluetooth (Hero 9 et plus récente)",
                                                "GoPro via Bluetooth (Hero 9 e successive)", "GoPro via Bluetooth (Hero 9 e pli nov)"),
    "GoPro (Bluetooth)": ("GoPro (Bluetooth)", "GoPro (Bluetooth)", "GoPro (Bluetooth)", "GoPro (Bluetooth)"),
    "Bluetooth search": ("Bluetooth-Suche", "Recherche Bluetooth", "Ricerca Bluetooth", "Tschertga Bluetooth"),
    "searching …": ("sucht …", "recherche …", "ricerca …", "tschertga …"),
    "Pair": ("Koppeln", "Appairer", "Associa", "Cupplar"),
    "On": ("Ein", "Allumer", "Accendi", "En"),
    "Off": ("Aus", "Éteindre", "Spegni", "Ora"),
    "Start stream": ("Strom starten", "Démarrer le flux", "Avvia lo stream", "Cumenzar il flux"),
    "Stop stream": ("Strom stoppen", "Arrêter le flux", "Ferma lo stream", "Fermar il flux"),
    "Reconnect": ("Neu verbinden", "Reconnecter", "Riconnetti", "Colliar danovamain"),
    "Forget": ("Vergessen", "Oublier", "Dimentica", "Emblidar"),
    "Forget this GoPro? It must be paired again afterwards.": ("Diese GoPro vergessen? Danach muss sie neu gekoppelt werden.",
                                                               "Oublier cette GoPro ? Elle devra ensuite être appairée à nouveau.",
                                                               "Dimenticare questa GoPro? Dopo andrà associata di nuovo.",
                                                               "Emblidar questa GoPro? Suenter sto ella vegnir cupplada danovamain."),
    "Install «bleak»": ("«bleak» installieren", "Installer « bleak »", "Installa «bleak»", "Installar «bleak»"),
    "Install the Bluetooth package «bleak» now?": ("Das Bluetooth-Paket «bleak» jetzt installieren?", "Installer maintenant le paquet Bluetooth « bleak » ?",
                                                    "Installare ora il pacchetto Bluetooth «bleak»?", "Installar ussa il pachet Bluetooth «bleak»?"),
    "For Bluetooth MoveEye needs the package «bleak» (apt python3-bleak, otherwise pip).": (
        "Für Bluetooth braucht MoveEye das Paket «bleak» (apt python3-bleak, sonst pip).",
        "Pour le Bluetooth, MoveEye a besoin du paquet « bleak » (apt python3-bleak, sinon pip).",
        "Per il Bluetooth MoveEye ha bisogno del pacchetto «bleak» (apt python3-bleak, altrimenti pip).",
        "Per Bluetooth dovra MoveEye il pachet «bleak» (apt python3-bleak, uschiglio pip)."),
    "On the GoPro: Preferences → Wireless connections → Connect device → GoPro Quik app (pairing mode).": (
        "An der GoPro: Einstellungen → Drahtlosverbindungen → Gerät verbinden → GoPro-Quik-App (Kopplungsmodus).",
        "Sur la GoPro : Préférences → Connexions sans fil → Connecter un appareil → app GoPro Quik (mode appairage).",
        "Sulla GoPro: Preferenze → Connessioni wireless → Connetti dispositivo → app GoPro Quik (modalità associazione).",
        "Sin la GoPro: Preferenzas → Colliaziuns senza fil → Colliar in apparat → app GoPro Quik (modus da cuppladura)."),
    "Search, then pair. MoveEye keeps the camera awake and restarts a lost stream by itself.": (
        "Suchen, dann koppeln. MoveEye hält die Kamera wach und startet einen abgebrochenen Strom selbst neu.",
        "Rechercher, puis appairer. MoveEye garde la caméra éveillée et relance tout seul un flux interrompu.",
        "Cerca, poi associa. MoveEye tiene sveglia la telecamera e riavvia da solo uno stream interrotto.",
        "Tschertgar, lura cupplar. MoveEye tegna la camera dasditga e cumenza sez danovamain in flux interrut."),
    "Network for the stream": ("Netz für den Strom", "Réseau pour le flux", "Rete per lo stream", "Rait per il flux"),
    "MoveEye's own WLAN": ("Eigenes WLAN von MoveEye", "Wi-Fi propre de MoveEye", "Wi-Fi proprio di MoveEye", "WLAN agen da MoveEye"),
    "Home WLAN": ("Heim-WLAN", "Wi-Fi de la maison", "Wi-Fi di casa", "WLAN da chasa"),
    "Camera WLAN (second WLAN adapter)": ("Kamera-WLAN (zweiter WLAN-Stick)", "Wi-Fi de la caméra (deuxième adaptateur Wi-Fi)",
                                          "Wi-Fi della telecamera (secondo adattatore Wi-Fi)", "WLAN da la camera (segund adapter WLAN)"),
    "WLAN name": ("WLAN-Name", "Nom du Wi-Fi", "Nome del Wi-Fi", "Num dal WLAN"),
    "WLAN password": ("WLAN-Passwort", "Mot de passe du Wi-Fi", "Password del Wi-Fi", "Pled-clav dal WLAN"),
    "The password goes to the camera only once and is never saved.": ("Das Passwort geht nur einmal an die Kamera und wird nie gespeichert.",
                                                                     "Le mot de passe n'est envoyé qu'une fois à la caméra et n'est jamais enregistré.",
                                                                     "La password va alla telecamera una sola volta e non viene mai salvata.",
                                                                     "Il pled-clav va mo ina giada a la camera e na vegn mai memorisà."),
    "Set up COHN (home network, Hero 12+)": ("COHN einrichten (Heimnetz, Hero 12+)", "Configurer COHN (réseau domestique, Hero 12+)",
                                             "Configura COHN (rete di casa, Hero 12+)", "Installar COHN (rait da chasa, Hero 12+)"),
    "COHN ready": ("COHN bereit", "COHN prêt", "COHN pronto", "COHN pront"),
    "Resolution": ("Auflösung", "Résolution", "Risoluzione", "Resoluziun"),
    "Battery": ("Akku", "Batterie", "Batteria", "Accu"),
    "too hot": ("zu heiss", "trop chaude", "troppo calda", "memia chaud"),
    "Source": ("Quelle", "Source", "Sorgente", "Funtauna"),
    "known WLANs": ("bekannte WLANs", "Wi-Fi connus", "Wi-Fi noti", "WLANs enconuschents"),
    "No GoPro paired yet.": ("Noch keine GoPro gekoppelt.", "Aucune GoPro appairée.", "Nessuna GoPro associata.", "Anc nagina GoPro cupplada."),
    "off": ("aus", "éteinte", "spenta", "ora"),
    "connecting …": ("verbindet …", "connexion …", "connessione …", "colliescha …"),
    "connected": ("verbunden", "connectée", "connessa", "colliada"),
    "asleep": ("schläft", "en veille", "in standby", "dorma"),
    "starting …": ("startet …", "démarre …", "avvio …", "cumenza …"),
    "streaming": ("Strom läuft", "flux en cours", "stream attivo", "flux en funcziun"),
    "reconnecting …": ("verbindet neu …", "reconnexion …", "riconnessione …", "colliescha danovamain …"),
    "error": ("Fehler", "erreur", "errore", "errur"),
    "bleak missing - install it on this page": ("«bleak» fehlt – auf dieser Seite installieren", "« bleak » manque – l'installer sur cette page",
                                                "manca «bleak» – installalo in questa pagina", "«bleak» manca – installar sin questa pagina"),
    "no Bluetooth adapter": ("kein Bluetooth-Adapter", "pas d'adaptateur Bluetooth", "nessun adattatore Bluetooth", "nagin adapter Bluetooth"),
    "GoPro not found - is it switched on and near?": ("GoPro nicht gefunden – ist sie eingeschaltet und in der Nähe?",
                                                      "GoPro introuvable – est-elle allumée et à proximité ?",
                                                      "GoPro non trovata – è accesa e vicina?", "GoPro betg chattada – è ella en e datiers?"),
    "pairing failed - put the GoPro into pairing mode": ("Koppeln fehlgeschlagen – die GoPro in den Kopplungsmodus bringen",
                                                         "Échec de l'appairage – mets la GoPro en mode appairage",
                                                         "Associazione non riuscita – metti la GoPro in modalità associazione",
                                                         "Cuppladura betg reussida – metter la GoPro en il modus da cuppladura"),
    "not a Hero 9 or newer - for a Hero 8 use the Hero 8 way": ("keine Hero 9 oder neuer – für eine Hero 8 den Hero-8-Weg nehmen",
                                                                "pas une Hero 9 ou plus récente – pour une Hero 8, prends la voie Hero 8",
                                                                "non è una Hero 9 o successiva – per una Hero 8 usa la via Hero 8",
                                                                "betg ina Hero 9 u pli nova – per ina Hero 8 prender la via Hero 8"),
    "no answer from the GoPro": ("keine Antwort von der GoPro", "pas de réponse de la GoPro", "nessuna risposta dalla GoPro",
                                 "nagina resposta da la GoPro"),
    "the GoPro refused the command": ("die GoPro hat den Befehl abgelehnt", "la GoPro a refusé la commande", "la GoPro ha rifiutato il comando",
                                      "la GoPro ha refusà il cumond"),
    "MoveEye's own WLAN is off - switch it on first": ("Das eigene WLAN von MoveEye ist aus – zuerst einschalten",
                                                       "Le Wi-Fi propre de MoveEye est éteint – l'allumer d'abord",
                                                       "Il Wi-Fi proprio di MoveEye è spento – accendilo prima",
                                                       "Il WLAN agen da MoveEye è ora – l'emprima enviar"),
    "MoveEye has no address in this WLAN": ("MoveEye hat in diesem WLAN keine Adresse", "MoveEye n'a pas d'adresse dans ce Wi-Fi",
                                            "MoveEye non ha un indirizzo in questo Wi-Fi", "MoveEye n'ha nagina adressa en quest WLAN"),
    "enter the WLAN name": ("WLAN-Namen eingeben", "saisis le nom du Wi-Fi", "inserisci il nome del Wi-Fi", "endatar il num dal WLAN"),
    "the GoPro does not know this WLAN yet - enter the password once": ("die GoPro kennt dieses WLAN noch nicht – einmal das Passwort eingeben",
                                                                        "la GoPro ne connaît pas encore ce Wi-Fi – saisis une fois le mot de passe",
                                                                        "la GoPro non conosce ancora questo Wi-Fi – inserisci una volta la password",
                                                                        "la GoPro na enconuscha anc betg quest WLAN – endatar ina giada il pled-clav"),
    "the GoPro could not join the WLAN": ("die GoPro kam nicht ins WLAN", "la GoPro n'a pas pu rejoindre le Wi-Fi",
                                          "la GoPro non è riuscita a entrare nel Wi-Fi", "la GoPro n'ha betg pudì entrar en il WLAN"),
    "wrong WLAN password": ("falsches WLAN-Passwort", "mauvais mot de passe Wi-Fi", "password Wi-Fi errata", "fauss pled-clav dal WLAN"),
    "the GoPro did not get ready for the stream": ("die GoPro wurde nicht bereit für den Strom", "la GoPro n'a pas été prête pour le flux",
                                                   "la GoPro non è stata pronta per lo stream", "la GoPro n'è betg daventada pronta per il flux"),
    "live stream failed on the GoPro": ("Livestream auf der GoPro fehlgeschlagen", "le direct a échoué sur la GoPro",
                                        "la diretta non è riuscita sulla GoPro", "il stream live n'è betg reussì sin la GoPro"),
    "live stream not possible with the current lens setting": ("Livestream mit der jetzigen Objektiv-Einstellung nicht möglich",
                                                               "direct impossible avec le réglage d'objectif actuel",
                                                               "diretta non possibile con l'impostazione attuale dell'obiettivo",
                                                               "stream live betg pussaivel cun l'ajustament actual da l'objectiv"),
    "the camera WLAN needs a second WLAN adapter (it would cut off your phone)": (
        "das Kamera-WLAN braucht einen zweiten WLAN-Stick (sonst wäre das Handy getrennt)",
        "le Wi-Fi de la caméra demande un deuxième adaptateur Wi-Fi (sinon le portable serait coupé)",
        "il Wi-Fi della telecamera richiede un secondo adattatore Wi-Fi (altrimenti il telefono verrebbe scollegato)",
        "il WLAN da la camera dovra in segund adapter WLAN (uschiglio fiss il telefonin separà)"),
    "could not join the camera WLAN": ("Kamera-WLAN nicht erreicht", "impossible de rejoindre le Wi-Fi de la caméra",
                                       "impossibile entrare nel Wi-Fi della telecamera", "betg pussaivel d'entrar en il WLAN da la camera"),
    "preview stream did not start": ("Vorschau-Strom startete nicht", "le flux d'aperçu n'a pas démarré", "lo stream di anteprima non è partito",
                                     "il flux da prevista n'ha betg cumenzà"),
    "COHN needs a Hero 12 or newer": ("COHN braucht eine Hero 12 oder neuer", "COHN demande une Hero 12 ou plus récente",
                                      "COHN richiede una Hero 12 o successiva", "COHN dovra ina Hero 12 u pli nova"),
    "COHN setup failed": ("COHN einrichten fehlgeschlagen", "échec de la configuration COHN", "configurazione COHN non riuscita",
                          "l'installaziun da COHN n'è betg reussida"),
    "install refused - confirm first": ("Installation abgelehnt – zuerst bestätigen", "installation refusée – confirme d'abord",
                                        "installazione rifiutata – conferma prima", "installaziun refusada – l'emprim confermar"),
    "installing …": ("installiert …", "installation …", "installazione …", "installescha …"),
    "installed": ("installiert", "installé", "installato", "installà"),
    "installation failed: ": ("Installation fehlgeschlagen: ", "échec de l'installation : ", "installazione non riuscita: ", "installaziun betg reussida: "),
    "the GoPro is busy - try again in a moment": ("die GoPro ist beschäftigt – gleich nochmals versuchen", "la GoPro est occupée – réessaie dans un instant",
                                                  "la GoPro è occupata – riprova tra poco", "la GoPro è occupada – empruvar danovamain en in mument"),
    "unknown device": ("unbekanntes Gerät", "appareil inconnu", "dispositivo sconosciuto", "apparat nunenconuschent"),
    "unknown action": ("unbekannte Aktion", "action inconnue", "azione sconosciuta", "acziun nunenconuschenta"),
    "connection lost - reconnecting": ("Verbindung weg – verbindet neu", "connexion perdue – reconnexion", "connessione persa – riconnessione",
                                       "colliaziun interrutta – colliescha danovamain"),
    "stream lost - restarting": ("Strom abgebrochen – startet neu", "flux interrompu – redémarrage", "stream interrotto – riavvio",
                                 "flux interrut – cumenza danovamain"),
    "no GoPro found - is it in pairing mode and near?": ("keine GoPro gefunden – ist sie im Kopplungsmodus und in der Nähe?",
                                                         "aucune GoPro trouvée – est-elle en mode appairage et à proximité ?",
                                                         "nessuna GoPro trovata – è in modalità associazione e vicina?",
                                                         "nagina GoPro chattada – è ella en il modus da cuppladura e datiers?"),
    "Bluetooth search failed": ("Bluetooth-Suche fehlgeschlagen", "échec de la recherche Bluetooth", "ricerca Bluetooth non riuscita",
                                "la tschertga Bluetooth n'è betg reussida"),
    "not allowed": ("nicht erlaubt", "non autorisé", "non consentito", "betg permess"),
    "invalid value": ("ungültiger Wert", "valeur non valable", "valore non valido", "valur nunvalaivla"),
    "Close": ("Schliessen", "Fermer", "Chiudi", "Serrar"),
}
for _k, _v in _HX_GPB.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
GPB_TXT_ERRS = {k for k in _HX_GPB if k[:1].islower()}
GPB_KEYS = [k for k in _HX_GPB if k not in ("Close",)]

# ---- web: on G1's page /gopro («GoPro hinzufügen») a step box in the card of every GoPro with the way «ble»: Bluetooth search,
#      pair, on / off, WLAN for the stream, COHN, battery. Start / Stop / Remove stay G1's buttons. Only the administrator.
GOPRO_BLE_JS = r"""
<script>
Object.assign(I18N.de, /*GPBDE*/{});
(function () {
  const Z = /*GPBZ*/{};
  const T = s => (typeof t === "function" ? t(s) : s);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const LG = () => (typeof LANG !== "undefined" && LANG) || "en";
  let S = null;
  const F = {};                                            // per GoPro: WLAN name / password typed so far (only in this page)
  async function get() {
    try { const r = await fetch("/api/gopro/ble?lang=" + LG(), {cache: "no-store"}); if (!r.ok && r.status !== 400) return null; return (await r.json()).state || null; }
    catch (e) { return null; }
  }
  async function act(a, b) {
    const q = await post("/api/gopro/ble?lang=" + LG(), Object.assign({action: a, lang: LG()}, b || {}));
    if (q && q.state) S = q.state;
    if (!q || !q.ok) toast("⚠ " + ((q && q.error) || T("error")));
    draw(true); return q;
  }
  function btn(txt, cls, fn, dis) { const b = E("button", cls || "sec", txt); b.type = "button"; b.disabled = !!dis; b.onclick = fn; return b; }
  function row() { return E("div", "gp-row"); }
  function box(x) {
    const f = F[x.id] = F[x.id] || {ssid: x.home_ssid || "", pw: ""};
    const c = E("div", "gp-step gpb-box"); c.dataset.id = x.id;
    c.appendChild(E("b", "", "📶 " + T("Bluetooth (Open GoPro)")));
    if (!S.bleak) {
      c.appendChild(E("p", "", T("For Bluetooth MoveEye needs the package «bleak» (apt python3-bleak, otherwise pip).")));
      const r = row(); r.appendChild(btn("⬇ " + T("Install «bleak»"), "sec", () => { if (confirm(T("Install the Bluetooth package «bleak» now?"))) act("install", {confirm: true}); }, S.install.running));
      c.appendChild(r);
      if (S.install.msg) c.appendChild(E("div", S.install.ok === false ? "gp-warn" : "gp-sec", S.install.msg));
      return c;
    }
    if (!S.adapter) c.appendChild(E("div", "gp-warn", "⚠ " + T("no Bluetooth adapter")));
    if (!x.paired) {
      const ol = E("ol");
      ol.append(E("li", "", T("On the GoPro: Preferences → Wireless connections → Connect device → GoPro Quik app (pairing mode).")),
                E("li", "", T("Search, then pair. MoveEye keeps the camera awake and restarts a lost stream by itself.")));
      c.appendChild(ol);
      const r = row(); r.appendChild(btn("🔍 " + (S.scan.running ? T("searching …") : T("Bluetooth search")), "sec", () => act("scan"), S.scan.running || !S.adapter));
      c.appendChild(r);
      (S.scan.found || []).filter(g => !g.known).forEach(g => {
        const r2 = row(); r2.className = "gp-row gpb-found";
        r2.append(E("span", "", "📡 " + (g.name || "GoPro") + (g.rssi != null ? " (" + g.rssi + " dBm)" : "")), btn("🔗 " + T("Pair"), "", () => act("pair", {id: x.id, addr: g.addr, name: g.name}), !!S.pairing));
        c.appendChild(r2);
      });
      if (S.pairing) c.appendChild(E("div", "gp-sec", "🔗 " + T("pairing …")));
      if (S.scan.err) c.appendChild(E("div", "gp-warn", "⚠ " + S.scan.err));
      return c;
    }
    const st = [T(Z[x.zustand] || x.zustand), x.modell];
    if (x.akku != null) st.push("🔋 " + T("Battery") + " " + x.akku + " %");
    if (x.hot) st.push("🔥 " + T("too hot"));
    if (x.cohn) st.push("🏠 " + T("COHN ready") + (x.cohn_ip ? " · " + x.cohn_ip : ""));
    c.appendChild(E("div", "gp-sec gpb-st", st.filter(Boolean).join(" · ")));
    if (x.fehler) c.appendChild(E("div", "gp-warn", "⚠ " + x.fehler));
    const s = E("select"); s.setAttribute("aria-label", T("Network for the stream"));
    [["hotspot", T("MoveEye's own WLAN")], ["home", T("Home WLAN")], ["ap", T("Camera WLAN (second WLAN adapter)")]]
      .forEach(([k, n]) => { const o = E("option", "", n); o.value = k; s.appendChild(o); });
    s.value = x.net; s.onchange = () => act("net", {id: x.id, net: s.value});
    const r1 = row(); r1.append(E("span", "mut", T("Network for the stream")), s); c.appendChild(r1);
    if (x.net === "home" || x.cohn_ok) {
      const a = E("input"); a.type = "text"; a.maxLength = 32; a.placeholder = T("WLAN name"); a.value = f.ssid; a.autocomplete = "off";
      a.setAttribute("aria-label", T("WLAN name")); a.oninput = () => { f.ssid = a.value; };
      const p = E("input"); p.type = "password"; p.maxLength = 63; p.placeholder = T("WLAN password"); p.value = f.pw; p.autocomplete = "new-password";
      p.setAttribute("aria-label", T("WLAN password")); p.oninput = () => { f.pw = p.value; };
      const r2 = row(); r2.append(a, p); c.appendChild(r2);
      c.appendChild(E("div", "gp-sec", T("The password goes to the camera only once and is never saved.") +
                    (x.known.length ? " · " + T("known WLANs") + ": " + x.known.join(", ") : "")));
    }
    const off = ["off", "asleep"].includes(x.zustand);
    const r3 = row();
    r3.appendChild(btn(off ? "⏻ " + T("On") : "⏾ " + T("Off"), "sec", () => act("power", {id: x.id, on: off}), x.job));
    if (x.net !== "ap") r3.appendChild(btn("📶 " + T("Bring the GoPro into the WLAN"), "sec", () => { const pw = f.pw; f.pw = ""; act("wlan", {id: x.id, net: x.net, ssid: f.ssid, password: pw}); }, x.job));
    r3.appendChild(btn("🔄 " + T("Reconnect"), "sec", () => act("power", {id: x.id, on: true}), x.job));
    if (x.cohn_ok) r3.appendChild(btn("🏠 " + T("Set up COHN (home network, Hero 12+)"), "sec", () => { const pw = f.pw; f.pw = ""; act("cohn", {id: x.id, ssid: f.ssid, password: pw}); }, x.job));
    r3.appendChild(btn("✂ " + T("Forget pairing"), "sec", () => { if (confirm(T("Forget this GoPro? It must be paired again afterwards."))) act("forget", {id: x.id}); }, x.job));
    c.appendChild(r3);
    return c;
  }
  function busy(c) { const a = document.activeElement; return c && a && c.contains(a) && /^(INPUT|SELECT)$/.test(a.tagName); }
  function draw(force) {
    if (!S) return;
    S.devices.forEach(x => {
      const card = document.querySelector('.gp-card[data-id="' + x.id + '"]'); if (!card) return;
      const old = card.querySelector(".gpb-box");
      if (old && !force && busy(old)) return;
      const nb = box(x);
      if (old) old.replaceWith(nb);
      else { const rows = card.querySelectorAll(":scope > .gp-row"); const last = rows[rows.length - 1]; if (last) card.insertBefore(nb, last); else card.appendChild(nb); }
    });
  }
  async function tick() {
    if (!document.hidden) { const s = await get(); if (s) { S = s; draw(false); } }
    setTimeout(tick, S && (S.scan.running || S.pairing || S.devices.some(d => d.job || /ing$/.test(d.zustand))) ? 1000 : 2000);
  }
  new MutationObserver(() => { if (S) draw(false); }).observe(document.getElementById("gp-devs") || document.body, {childList: true});
  setTimeout(tick, 300);
})();
</script>
"""
GOPRO_PAGE = GOPRO_PAGE.replace("/*ALERTS*/\n</script></body>", "/*ALERTS*/\n</script>" + GOPRO_BLE_JS.replace("/*GPBDE*/{}", json.dumps({k: DE.get(k, k) for k in GPB_KEYS}, ensure_ascii=False), 1)
                                .replace("/*GPBZ*/{}", json.dumps(GPB_ZUSTAND, ensure_ascii=False), 1) + "</body>", 1)


# ---- manual (HELP_PAGE de / en, HELP_X fr / it / rm): end of the section «Kamera & Servos» ------------------------------------
HELP_GPB = {
    "de": '<p id="gpb-help"><b>📷 GoPro über Bluetooth (Hero 9 und neuer, Open GoPro):</b> <i>Kameras → GoPro hinzufügen</i>, Weg «HERO9 und neuer: '
          'Bluetooth (Open GoPro)» (nur Administrator). Einmal «bleak» installieren (MoveEye fragt vorher). An der GoPro <i>Einstellungen → Drahtlosverbindungen → Gerät '
          'verbinden → GoPro Quik</i>, dann «Bluetooth-Suche» und «Koppeln» im Kasten «Bluetooth» der Karte. Danach: ⏻ Ein / ⏾ Aus (schlafen), 🔋 Akku, «GoPro ins WLAN bringen», ▶ Start: die '
          'GoPro geht ins <b>eigene WLAN von MoveEye</b> oder ins <b>Heim-WLAN</b> und schickt ihr Bild per RTMP an MoveEye – es erscheint wie '
          'eine weitere Kamera. Das WLAN-Passwort geht nur einmal an die Kamera und wird nie gespeichert. <b>Kamera-WLAN</b> (Vorschau-Strom) '
          'nur mit einem zweiten WLAN-Stick. Ab Hero 12: «COHN einrichten» – die Kamera bleibt im Heimnetz, Zertifikat und Zugang liegen nur '
          'in <code>~/.config/motionwatch/gopro_ble.json</code> (Rechte 600). MoveEye hält die Kamera wach (alle 3 s) und startet einen '
          'abgebrochenen Strom oder eine verlorene Verbindung selbst neu (stille Meldung im Protokoll, kein Alarm).</p>',
    "en": '<p id="gpb-help"><b>📷 GoPro over Bluetooth (Hero 9 and newer, Open GoPro):</b> <i>Cameras → Add GoPro</i>, way «HERO9 and newer: Bluetooth '
          '(Open GoPro)» (administrator only). Install «bleak» once (MoveEye asks first). On the GoPro <i>Preferences → Wireless connections → Connect device '
          '→ GoPro Quik</i>, then «Bluetooth search» and «Pair» in the box «Bluetooth» of the card. Then: ⏻ On / ⏾ Off (sleep), 🔋 battery, «Bring the GoPro into the WLAN», ▶ Start: the GoPro joins '
          '<b>MoveEye\'s own WLAN</b> or the <b>home WLAN</b> and sends its picture to MoveEye over RTMP – it appears like another camera. '
          'The WLAN password goes to the camera only once and is never saved. <b>Camera WLAN</b> (preview stream) only with a second WLAN '
          'adapter. From Hero 12: «Set up COHN» – the camera stays on the home network, certificate and access are kept only in '
          '<code>~/.config/motionwatch/gopro_ble.json</code> (rights 600). MoveEye keeps the camera awake (every 3 s) and restarts a lost '
          'stream or connection by itself (quiet note in the log, no alarm).</p>',
    "fr": '<p id="gpb-help"><b>📷 GoPro par Bluetooth (Hero 9 et plus récente, Open GoPro) :</b> <i>Caméras → Ajouter une GoPro</i>, voie « HERO9 et plus '
          'récente : Bluetooth (Open GoPro) » (administrateur seulement). Installer une fois « bleak » (MoveEye demande avant). Sur la GoPro <i>Préférences → Connexions sans fil → '
          'Connecter un appareil → GoPro Quik</i>, puis « Recherche Bluetooth » et « Appairer ». Ensuite : ⏻ allumer / ⏾ éteindre (veille), '
          '🔋 batterie, ▶ démarrer le flux : la GoPro rejoint le <b>Wi-Fi propre de MoveEye</b> ou le <b>Wi-Fi de la maison</b> et envoie son '
          'image en RTMP – elle apparaît comme une autre caméra. Le mot de passe Wi-Fi n\'est envoyé qu\'une fois et n\'est jamais enregistré. '
          '<b>Wi-Fi de la caméra</b> seulement avec un deuxième adaptateur Wi-Fi. Dès la Hero 12 : « Configurer COHN » (certificat et accès '
          'seulement dans <code>~/.config/motionwatch/gopro_ble.json</code>, droits 600). MoveEye garde la caméra éveillée et relance tout seul '
          'un flux ou une connexion perdus (note discrète dans le journal, pas d\'alarme).</p>',
    "it": '<p id="gpb-help"><b>📷 GoPro via Bluetooth (Hero 9 e successive, Open GoPro):</b> <i>Telecamere → Aggiungi GoPro</i>, via «HERO9 e successive: '
          'Bluetooth (Open GoPro)» (solo amministratore). Installa una volta «bleak» (MoveEye chiede prima). Sulla GoPro <i>Preferenze → Connessioni wireless → '
          'Connetti dispositivo → GoPro Quik</i>, poi «Ricerca Bluetooth» e «Associa». Poi: ⏻ accendi / ⏾ spegni (standby), 🔋 batteria, '
          '▶ avvia lo stream: la GoPro entra nel <b>Wi-Fi proprio di MoveEye</b> o nel <b>Wi-Fi di casa</b> e invia l\'immagine via RTMP – '
          'appare come un\'altra telecamera. La password del Wi-Fi va alla telecamera una sola volta e non viene mai salvata. <b>Wi-Fi della '
          'telecamera</b> solo con un secondo adattatore Wi-Fi. Dalla Hero 12: «Configura COHN» (certificato e accesso solo in '
          '<code>~/.config/motionwatch/gopro_ble.json</code>, permessi 600). MoveEye tiene sveglia la telecamera e riavvia da solo uno stream '
          'o una connessione persi (nota discreta nel registro, nessun allarme).</p>',
    "rm": '<p id="gpb-help"><b>📷 GoPro via Bluetooth (Hero 9 e pli nov, Open GoPro):</b> <i>Cameras → Agiuntar ina GoPro</i>, via «HERO9 e pli nov: '
          'Bluetooth (Open GoPro)» (mo administratur). Installar ina giada «bleak» (MoveEye dumonda avant). Sin la GoPro <i>Preferenzas → Colliaziuns senza fil → '
          'Colliar in apparat → GoPro Quik</i>, lura «Tschertga Bluetooth» e «Cupplar». Suenter: ⏻ en / ⏾ ora (durmir), 🔋 accu, ▶ cumenzar '
          'il flux: la GoPro entra en il <b>WLAN agen da MoveEye</b> u en il <b>WLAN da chasa</b> e trametta ses maletg via RTMP – el cumpara '
          'sco ina ulteriura camera. Il pled-clav dal WLAN va mo ina giada a la camera e na vegn mai memorisà. <b>WLAN da la camera</b> mo cun '
          'in segund adapter WLAN. A partir da la Hero 12: «Installar COHN» (certificat ed access mo en '
          '<code>~/.config/motionwatch/gopro_ble.json</code>, dretgs 600). MoveEye tegna la camera dasditga e cumenza sez danovamain in flux u '
          'ina colliaziun persa (notizia quieta en il protocol, nagin alarm).</p>',
}


def _help_gpb(doc, lang):
    i = doc.find('<section id="camera"')
    if i < 0 or 'id="gpb-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_GPB[lang] + doc[j:] if j >= 0 else doc


_hp_en_gpb = HELP_PAGE.find('<div lang="en">') if isinstance(HELP_PAGE, str) else -1
if _hp_en_gpb > 0:
    HELP_PAGE = _help_gpb(HELP_PAGE[:_hp_en_gpb], "de") + _help_gpb(HELP_PAGE[_hp_en_gpb:], "en")
for _L in ("fr", "it", "rm"):
    if isinstance(HELP_X, dict) and HELP_X.get(_L):
        HELP_X[_L] = _help_gpb(HELP_X[_L], _L)
