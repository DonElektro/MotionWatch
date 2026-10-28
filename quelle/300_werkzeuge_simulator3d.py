#@ Motion Watch – Teil 300: Werkzeuge, 3D-Simulator für Windows und den Pi, Simulator-Suche. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Tools (page /tools): network scanner, Wi-Fi surroundings, internet test, security check, Bluetooth scanner with
# tracker warning and presence, focus assistant, servo test, speaker / microphone test, memory card test,
# diagnosis package, power calculator.
# ----------------------------------------------------------------------------
TOOLS = {"net": {"running": False, "t": 0.0, "devices": [], "net": "", "secs": 0.0, "msg": ""},
         "wifi": {"running": False, "t": 0.0, "nets": [], "channels": {}, "best": None, "own": None, "msg": ""},
         "speed": {"running": False, "msg": "", "hist": []},
         "sec": {"running": False, "t": 0.0, "items": []},
         "bt": {"running": False, "t": 0.0, "devices": [], "msg": "", "trackers": {}},
         "focus": {"t": 0.0, "val": None, "best": 0.0, "hist": []},
         "servo": {"running": False, "steps": [], "msg": ""},
         "sd": {"running": False, "t": 0.0, "res": {}, "msg": ""},
         "presence": {"here": None, "since": 0.0, "who": ""}}
OUI_BUILTIN = {"B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi", "E45F01": "Raspberry Pi", "28CDC1": "Raspberry Pi", "2CCF67": "Raspberry Pi",
               "D83ADD": "Raspberry Pi", "240AC4": "Espressif (ESP32)", "30AEA4": "Espressif (ESP32)", "84CCA8": "Espressif (ESP32)",
               "A4CF12": "Espressif (ESP32)", "246F28": "Espressif (ESP32)", "3C71BF": "Espressif (ESP32)", "001132": "Synology"}
_OUI = {"loaded": False, "map": {}}


def oui_vendor(mac):
    """Maker of a network device from the first half of its address (MAC). A random address = a phone with privacy mode."""
    m = re.sub(r"[^0-9A-Fa-f]", "", mac or "").upper()
    if len(m) < 6:
        return ""
    if int(m[1], 16) & 2:
        return "private address (phone / tablet)"
    if not _OUI["loaded"]:
        _OUI["loaded"] = True
        for p in ("/usr/share/ieee-data/oui.txt", "/usr/share/arp-scan/ieee-oui.txt", "/usr/share/nmap/nmap-mac-prefixes"):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        mm = re.match(r"^([0-9A-F]{2})[-:]?([0-9A-F]{2})[-:]?([0-9A-F]{2})\s+(?:\(hex\)\s+)?(.+)$", line.strip(), re.I)
                        if mm:
                            _OUI["map"][(mm.group(1) + mm.group(2) + mm.group(3)).upper()] = mm.group(4).strip()[:40]
                if _OUI["map"]:
                    break
            except OSError:
                continue
    return _OUI["map"].get(m[:6]) or OUI_BUILTIN.get(m[:6], "")


def _arp_table():
    out = {}
    try:
        with open("/proc/net/arp") as f:
            next(f)
            for line in f:
                p = line.split()
                if len(p) >= 6 and p[2] != "0x0" and p[3] != "00:00:00:00:00:00":
                    out[p[0]] = p[3].lower()
    except (OSError, StopIteration):
        pass
    return out


def net_scan(alert=False):
    """All devices in the own network: wake every address (ping), read the address table, names and makers."""
    T = TOOLS["net"]
    if T["running"]:
        return False
    from concurrent.futures import ThreadPoolExecutor
    import socket
    T.update(running=True, msg="")
    t0 = time.time()
    try:
        ip = _local_ipv4(); base = ".".join(ip.split(".")[:3])
        mine_ips = {ip}; bases = [] if ip.startswith("127.") else [base]
        code_, out_, _e = _run(["ip", "-4", "-o", "addr", "show"], 5)
        hs_if = DUAL.get("ap") or (WIFI.get("iface") if STATE["hotspot"].get("on") else "")
        hs_base = ""
        for ln in (out_ or "").splitlines():
            m_ = re.search(r"^\d+:\s+(\S+)\s+inet (\d+\.\d+\.\d+\.\d+)/(\d+)", ln)
            if not m_ or m_.group(1) == "lo" or m_.group(1).startswith(("docker", "tailscale", "veth", "br-")):
                continue
            a_ = m_.group(2)
            if not ipaddress.ip_address(a_).is_private or a_.startswith("127."):
                continue
            mine_ips.add(a_); b_ = ".".join(a_.split(".")[:3])
            if m_.group(1) == hs_if:
                hs_base = b_
            if b_ not in bases and len(bases) < 3:
                bases.append(b_)
        if not bases:
            T.update(msg="no network"); return False
        base = bases[0]
        hosts = [f"{b_}.{i}" for b_ in bases for i in range(1, 255)]
        ping = shutil.which("ping")
        alive = set()

        def poke(h):
            if ping:
                try:
                    if subprocess.run([ping, "-c", "1", "-W", "1", h], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode == 0:
                        alive.add(h)
                except (OSError, subprocess.SubprocessError):
                    pass
            else:
                try:
                    s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s_.sendto(b"", (h, 9)); s_.close()
                except OSError:
                    pass
        with ThreadPoolExecutor(max_workers=64) as ex:
            list(ex.map(poke, hosts))
        time.sleep(0.5)
        arp = _arp_table()
        addrs = sorted(set(arp) | alive | {ip}, key=lambda a: [int(x) for x in a.split(".")])
        addrs = [a for a in addrs if ".".join(a.split(".")[:3]) in bases]

        def name_of(a):
            try:
                socket.setdefaulttimeout(1.0)
                return socket.gethostbyaddr(a)[0][:50]
            except (OSError, UnicodeError):
                return ""
            finally:
                socket.setdefaulttimeout(None)
        with ThreadPoolExecutor(max_workers=32) as ex:
            names = dict(zip(addrs, ex.map(name_of, addrs)))
        known = CFG.get("net_known") or {}
        gw = ""
        try:
            with open("/proc/net/route") as f:
                for line in list(f)[1:]:
                    p = line.split()
                    if p[1] == "00000000":
                        gw = socket.inet_ntoa(bytes.fromhex(p[2])[::-1]); break
        except (OSError, ValueError, IndexError):
            pass
        devs = []
        noinet = set(CFG.get("net_noinet") or [])
        for a in addrs:
            mac = arp.get(a, "")
            kn = known.get(mac) if mac else None
            role = "this device" if a in mine_ips else ("router" if a == gw else "")
            hs_ = bool(hs_base) and a.startswith(hs_base + ".")
            devs.append({"ip": a, "mac": mac, "name": names.get(a, ""), "vendor": oui_vendor(mac), "known": kn, "role": role,
                         "hs": hs_, "noinet": mac in noinet,
                         "new": bool(mac) and kn is None and a not in mine_ips and bool(T.get("first_done")) and mac not in (T.get("seen") or {})})
        seen = T.setdefault("seen", {})
        for d_ in devs:
            if d_["mac"]:
                seen[d_["mac"]] = time.time()
        newbies = [d_ for d_ in devs if d_["new"] and d_["mac"] not in (CFG.get("net_known") or {})]
        T.update(devices=devs, net=" + ".join(f"{b_}.0/24" for b_ in bases), t=time.time(), secs=round(time.time() - t0, 1))
        presence_update(devs)
        if alert and CFG.get("net_watch") and newbies and T.get("first_done"):
            txt = ", ".join(f"{d_['ip']} ({d_['vendor'] or d_['name'] or d_['mac']})" for d_ in newbies[:5])
            log_event("sys", f"New device in the network: {txt}")
            w = WATCH_REF.get("w")
            if w is not None:
                w.notifier.alert("{name}: " + tr("new device in the network"), txt, None)
        T["first_done"] = True
        return True
    finally:
        T["running"] = False


def net_known_set(mac, name):
    mac = (mac or "").lower()
    if not re.fullmatch(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}", mac):
        return False
    k = dict(CFG.get("net_known") or {})
    if name is None:
        k.pop(mac, None)
    else:
        k[mac] = str(name)[:40] or "?"
    CFG["net_known"] = k; save_settings()
    for d_ in TOOLS["net"]["devices"]:
        if d_["mac"] == mac:
            d_["known"] = k.get(mac); d_["new"] = False
    return True


def presence_update(devs):
    """«My phone is here»: one of the marked devices is in the network. Optional: disarm when it comes, arm when it is gone."""
    mine = set(CFG.get("presence_macs") or [])
    if not mine:
        return
    P = TOOLS["presence"]
    here = [d_ for d_ in devs if d_["mac"] in mine]
    if here:
        P["last"] = time.time(); P["who"] = ", ".join((d_.get("known") or d_["ip"]) for d_ in here)
    presence_eval()


def wifi_survey():
    """Wi-Fi networks around (name, channel, signal) and the best channel for the own hotspot. With two adapters the one that
    is not the own Wi-Fi searches - the own Wi-Fi is not interrupted."""
    T = TOOLS["wifi"]
    if T["running"]:
        return False
    T.update(running=True, msg="")
    try:
        nets = []
        nm = shutil.which("nmcli")
        if nm:
            r = subprocess.run([nm, "-t", "-f", "IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"]
                               + (["ifname", DUAL["up"]] if DUAL["on"] else []),
                               capture_output=True, text=True, timeout=30)
            for line in r.stdout.splitlines():
                p = re.split(r"(?<!\\):", line)
                if len(p) < 7:
                    continue
                p = [x.replace("\\:", ":") for x in p]
                try:
                    nets.append({"own": p[0] == "*", "ssid": p[1][:32] or "(" + tr("hidden") + ")", "bssid": p[2], "ch": int(p[3] or 0),
                                 "mhz": int(re.sub(r"\D", "", p[4]) or 0), "signal": int(p[5] or 0), "sec": p[6][:20]})
                except ValueError:
                    continue
        if not nets:
            T["msg"] = "no Wi-Fi scan possible (NetworkManager / nmcli missing or no Wi-Fi)"
        ch = {}
        for n in nets:
            if 1 <= n["ch"] <= 14:
                ch[n["ch"]] = ch.get(n["ch"], 0) + max(1, n["signal"])
        load = {c: sum(v * max(0, 1 - abs(c - k) / 5.0) for k, v in ch.items()) for c in (1, 6, 11)}     # channels overlap
        best = min(load, key=load.get) if nets else None
        nets.sort(key=lambda n: -n["signal"])
        T.update(nets=nets[:60], channels={str(k): v for k, v in sorted(ch.items())}, best=best, load={str(k): round(v) for k, v in load.items()},
                 own=next((n for n in nets if n["own"]), None), t=time.time())
        return True
    except (OSError, subprocess.SubprocessError) as e:
        T["msg"] = str(e)[:120]; return False
    finally:
        T["running"] = False


def speed_test():
    """Internet: ping, name lookup and a small download / upload (about 6 MB in total - mind the volume of a mobile contract)."""
    T = TOOLS["speed"]
    if T["running"]:
        return False
    import socket
    T.update(running=True, msg="testing")
    res = {"t": time.time()}
    try:
        ping = shutil.which("ping")
        if ping:
            r = subprocess.run([ping, "-c", "4", "-W", "2", "1.1.1.1"], capture_output=True, text=True, timeout=15)
            m = re.search(r"= [\d.]+/([\d.]+)/", r.stdout)
            res["ping_ms"] = round(float(m.group(1)), 1) if m else None
            m2 = re.search(r"(\d+)% packet loss", r.stdout)
            res["loss"] = int(m2.group(1)) if m2 else None
        t0 = time.time()
        try:
            socket.getaddrinfo("speed.cloudflare.com", 443); res["dns_ms"] = round((time.time() - t0) * 1000, 1)
        except OSError:
            res["dns_ms"] = None
        t0 = time.time()
        with urllib.request.urlopen("https://speed.cloudflare.com/__down?bytes=5000000", timeout=30) as r:
            n = len(r.read())
        res["down_mbit"] = round(n * 8 / 1e6 / max(0.01, time.time() - t0), 1)
        data = os.urandom(1000000); t0 = time.time()
        req = urllib.request.Request("https://speed.cloudflare.com/__up", data=data, headers={"Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        res["up_mbit"] = round(len(data) * 8 / 1e6 / max(0.01, time.time() - t0), 1)
        T["msg"] = ""
    except Exception as e:
        res["error"] = str(e)[:100]; T["msg"] = res["error"]
    finally:
        T["hist"] = (T["hist"] + [res])[-20:]
        T["running"] = False
        log_event("sys", "Internet test: " + (f"{res.get('down_mbit')} / {res.get('up_mbit')} Mbit/s, ping {res.get('ping_ms')} ms" if "error" not in res else res["error"]))
    return True


def security_check():
    """What is open and what could be risky: password, https, open ports, router (UPnP), IPv6, SSH."""
    T = TOOLS["sec"]
    items = []

    def add(level, text, tip="", arg=""):
        items.append({"level": level, "text": text, "tip": tip, "arg": arg})
    add("ok" if CFG["web_password"] else "bad", "Web password " + ("set" if CFG["web_password"] else "missing"),
        "" if CFG["web_password"] else "Everybody in the network can operate Motion Watch")
    add("ok" if WEB_OPTS.get("https") else "warn", "Secure page (https) " + ("on" if WEB_OPTS.get("https") else "off"),
        "" if WEB_OPTS.get("https") else "Passwords go through the network unencrypted - important in foreign Wi-Fi (camping)")
    ports = set()
    try:
        for fn in ("/proc/net/tcp", "/proc/net/tcp6"):
            with open(fn) as f:
                for line in list(f)[1:]:
                    p = line.split()
                    if p[3] == "0A":                                  # listening
                        la, lp = p[1].split(":")
                        if la not in ("0100007F", "00000000000000000000000001000000"):
                            ports.add(int(lp, 16))
    except (OSError, ValueError, IndexError):
        pass
    names = {22: "SSH", 80: "web", 443: "https", 5000: "Motion Watch", 5001: "Motion Watch https", 8554: "RTSP (camera stream)", 1883: "MQTT",
             8765: "simulator", 5900: "VNC", 3389: "remote desktop", 139: "Windows share", 445: "Windows share", 53: "DNS"}
    for p in sorted(ports)[:30]:
        lvl = "warn" if p in (5900, 3389, 139, 445, 1883) else "info"
        add(lvl, "Open in the network: port", "", f"{p}" + (f" ({names[p]})" if p in names else ""))
    try:
        sshd = open("/etc/ssh/sshd_config").read()
        if 22 in ports:
            pw = re.search(r"^\s*PasswordAuthentication\s+no", sshd, re.M) is None
            add("warn" if pw else "ok", "SSH: login with password " + ("allowed" if pw else "off (keys only)"),
                "Use a strong password or keys" if pw else "")
    except OSError:
        pass
    v6 = []
    try:
        with open("/proc/net/if_inet6") as f:
            for line in f:
                a = line.split()[0]
                if a.startswith(("2", "3")):
                    v6.append(a)
    except OSError:
        pass
    if v6:
        add("warn", "Public IPv6 address present", "Depending on the router the Pi can be reached directly from the internet - keep the web password on")
    up = shutil.which("upnpc")
    if up:
        try:
            r = subprocess.run([up, "-l"], capture_output=True, text=True, timeout=15)
            maps = [l for l in r.stdout.splitlines() if re.match(r"\s*\d+\s+(TCP|UDP)", l)]
            mine = [l for l in maps if _local_ipv4() in l]
            add("bad" if mine else "ok", "Router forwards ports to this device:" if mine else "No port forwarding of the router to this device (UPnP)", "", str(len(mine)) if mine else "")
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        with urllib.request.urlopen("https://1.1.1.1/cdn-cgi/trace", timeout=8) as r:
            tr_ = r.read().decode(errors="replace")
        pub = re.search(r"^ip=(.+)$", tr_, re.M)
        if pub:
            ip_ = pub.group(1).strip()
            cg = ip_.startswith("100.") and 64 <= int(ip_.split(".")[1]) <= 127
            add("info", "Address in the internet:", "shared address of the mobile network - not reachable from outside" if cg else "", ip_)
    except Exception:
        add("info", "Internet not reachable")
    if (STATE.get("remote_ts") or {}).get("state") == "Running":
        add("ok", "Tailscale: access from outside only for your own devices")
    T.update(items=items, t=time.time())
    return True


def bt_scan(secs=10):
    """Bluetooth devices around. Trackers (Apple Find My, Samsung SmartTag, Tile) that stay near for a long time = warning."""
    T = TOOLS["bt"]
    if T["running"]:
        return False
    T.update(running=True, msg="")

    async def go():
        from bleak import BleakScanner
        found = await BleakScanner.discover(timeout=secs, return_adv=True)
        out = []
        for addr, (dev, adv) in found.items():
            md = adv.manufacturer_data or {}; uu = [u.lower() for u in (adv.service_uuids or [])]
            kind = ""
            if 0x004C in md and len(md[0x004C]) > 1 and md[0x004C][0] == 0x12:
                kind = "Apple Find My (AirTag or a lost Apple device)"
            elif any(u.startswith("0000fd5a") for u in uu):
                kind = "Samsung SmartTag"
            elif any(u.startswith("0000feed") for u in uu):
                kind = "Tile"
            elif 0x004C in md:
                kind = "Apple device"
            elif 0x0075 in md:
                kind = "Samsung device"
            elif 0x0006 in md:
                kind = "Microsoft device"
            elif 0x0499 in md:
                kind = "RuuviTag"
            out.append({"addr": addr, "name": (adv.local_name or dev.name or "")[:40], "rssi": adv.rssi, "kind": kind,
                        "tracker": kind.startswith(("Apple Find", "Samsung SmartTag", "Tile"))})
        return out
    try:
        import asyncio
        devs = asyncio.run(go())
        devs.sort(key=lambda d_: -(d_["rssi"] or -200))
        now = time.time(); tk = T["trackers"]
        for d_ in devs:
            if d_["tracker"]:
                x = tk.setdefault(d_["addr"], {"first": now, "kind": d_["kind"]}); x["last"] = now
        for a in [a for a, x in tk.items() if now - x["last"] > 1800]:
            tk.pop(a, None)
        for a, x in tk.items():
            stay = (x["last"] - x["first"]) / 60.0
            if stay >= float(CFG.get("bt_tracker_min", 30)) and not x.get("warned") and CFG.get("bt_tracker_warn"):
                x["warned"] = True
                log_event("sys", f"Unknown tracker near for {stay:.0f} min: {x['kind']} ({a})")
                w = WATCH_REF.get("w")
                if w is not None:
                    w.notifier.alert("{name}: " + tr("unknown tracker nearby"), f"{x['kind']} · {stay:.0f} min", None)
        mine = set(CFG.get("presence_bt") or [])
        if mine and any(d_["addr"].lower() in mine for d_ in devs):
            TOOLS["presence"]["last"] = now
        T.update(devices=devs[:80], t=now)
        return True
    except ImportError:
        T["msg"] = "Bluetooth scanner needs: sudo apt install python3-bleak"; return False
    except Exception as e:
        T["msg"] = str(e)[:120]; return False
    finally:
        T["running"] = False


def focus_value():
    """Sharpness of the middle of the picture (variance of the Laplace filter): higher = sharper."""
    w = WATCH_REF.get("w")
    if w is None:
        return None
    w.raw_until = time.time() + 3                    # the picture without boxes and text (they would count as "sharp")
    f = w.frame_raw if w.frame_raw is not None else w.frame_out
    if f is None:
        return None
    h, w_ = f.shape[:2]
    c = cv2.cvtColor(f[h // 4: 3 * h // 4, w_ // 4: 3 * w_ // 4], cv2.COLOR_BGR2GRAY)
    v = float(cv2.Laplacian(c, cv2.CV_64F).var())
    F = TOOLS["focus"]; F["val"] = round(v, 1); F["best"] = max(F["best"], v) if time.time() - F["t"] < 120 else v; F["t"] = time.time()
    F["hist"] = (F["hist"] + [round(v, 1)])[-60:]
    return F


def servo_test():
    """Drive pan and tilt slowly over the whole range; after every step: did the picture change? (moved or blocked)"""
    S = TOOLS["servo"]
    if S["running"]:
        return False
    w = WATCH_REF.get("w")
    if w is None:
        return False
    S.update(running=True, steps=[], msg="", bad=0)

    def grab():
        f = getattr(w, "frame_out", None)
        return None if f is None else cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (160, 90)).astype(np.float32)

    def run():
        p0, t0 = CFG["pan"], CFG["tilt"]
        MANUAL["until"] = time.time() + 3600
        try:
            plan = [("pan", v) for v in (50, 30, 10, 0, 25, 50, 75, 90, 100, 50)] + [("tilt", v) for v in (50, 30, 15, 0, 50, 70, 85, 100, 50)]
            prev = grab()
            for axis, v in plan:
                CFG[axis] = float(v)
                time.sleep(1.2)
                cur = grab()
                diff = None if prev is None or cur is None else round(float(np.mean(np.abs(cur - prev))), 1)
                S["steps"].append({"axis": axis, "to": v, "real": round(CFG[axis], 1), "diff": diff})
                prev = cur
            still = []
            for i, s_ in enumerate(S["steps"]):
                prev_to = S["steps"][i - 1]["to"] if i and S["steps"][i - 1]["axis"] == s_["axis"] else 50
                s_["ok"] = s_["diff"] is None or abs(s_["to"] - prev_to) < 5 or s_["diff"] >= 1.0
                if not s_["ok"]:
                    still.append(s_)
            S["msg"] = "ok" if not still else "steps without a change of the picture - blocked, at the end or camera not on the head?"
            S["bad"] = len(still)
            log_event("servo", "Servo test: " + ("ok" if not still else f"{len(still)} {S['msg']}"))
        finally:
            CFG["pan"], CFG["tilt"] = p0, t0
            MANUAL["until"] = 0.0
            S["running"] = False
    threading.Thread(target=run, daemon=True, name="servotest").start()
    return True


def sd_test():
    """Memory card: write / read speed (64 MB), kind of card, data written since the start, errors in the system log."""
    S = TOOLS["sd"]
    if S["running"]:
        return False
    S.update(running=True, msg="")
    res = {}
    try:
        p = os.path.join(DATA_DIR, ".speedtest.bin"); blk = os.urandom(1 << 20); n = 64
        if shutil.disk_usage(DATA_DIR).free < (n + 500) * (1 << 20):
            raise OSError("not enough free space for the test (64 MB + 500 MB reserve)")
        t0 = time.time()
        with open(p, "wb") as f:
            for _ in range(n):
                f.write(blk)
            f.flush(); os.fsync(f.fileno())
        res["write_mb_s"] = round(n / max(0.01, time.time() - t0), 1)
        try:
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("1")
        except OSError:
            pass
        t0 = time.time()
        with open(p, "rb") as f:
            while f.read(1 << 22):
                pass
        res["read_mb_s"] = round(n / max(0.01, time.time() - t0), 1)
        os.remove(p)
        dev = None
        for d_ in ("mmcblk0", "nvme0n1", "sda"):
            if os.path.isdir(f"/sys/block/{d_}"):
                dev = d_; break
        if dev:
            res["device"] = dev
            for k in ("name", "manfid", "oemid", "date", "type"):
                try:
                    res[k] = open(f"/sys/block/{dev}/device/{k}").read().strip()[:30]
                except OSError:
                    pass
            try:
                st_ = open(f"/sys/block/{dev}/stat").read().split()
                res["written_gb"] = round(int(st_[6]) * 512 / 1024 ** 3, 2)
            except (OSError, IndexError, ValueError):
                pass
            try:
                res["size_gb"] = round(int(open(f"/sys/block/{dev}/size").read()) * 512 / 1e9, 1)
            except (OSError, ValueError):
                pass
        errs = 0
        for cmd in (["dmesg"], ["journalctl", "-k", "-n", "3000", "--no-pager"]):
            if shutil.which(cmd[0]):
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if r.returncode == 0 and r.stdout:
                        errs = sum(1 for l in r.stdout.splitlines() if re.search(r"(mmc\d|mmcblk|EXT4-fs error|I/O error)", l) and re.search(r"error|timeout|fail", l, re.I))
                        break
                except (OSError, subprocess.SubprocessError):
                    pass
        res["errors"] = errs
        res["verdict"] = "bad" if errs or res["write_mb_s"] < 3 else ("warn" if res["write_mb_s"] < 8 else "ok")
        S["msg"] = ""
        log_event("sys", f"Memory card test: write {res['write_mb_s']} MB/s, read {res['read_mb_s']} MB/s, errors {errs}")
    except Exception as e:
        S["msg"] = str(e)[:120]
    finally:
        try:
            os.remove(os.path.join(DATA_DIR, ".speedtest.bin"))   # 2.95.33: also after an error (full card)
        except OSError:
            pass
        S.update(res=res, t=time.time(), running=False)
    return True


_SECRET_RE = re.compile(r"pass|token|secret|key|pin|topic|ntfy|webhook|sms_|phone|mail|user|telegram|chat|url|mqtt_|wifi|psk|feedback|mac|known|ssid|lat|lon|gps"
                        r"|pw|hash|trusted|fleet|source|cams|lock_snap|backup|host|addr|ip_|presence|pushover|shortcut|guest", re.I)
_URL_SECRET = re.compile(r"\b([a-z][a-z0-9+.-]*://)([^\s/@'\"]+@)?([^\s/'\"?#]+)[^\s'\"]*", re.I)


def _scrub_text(t):
    """addresses in texts: only scheme + server stay (no user:password@, no ntfy topic / path)"""
    return _URL_SECRET.sub(lambda m: m.group(1) + m.group(3) + "/…", str(t))


def diag_zip():
    """Everything for finding a fault in one ZIP: log, settings WITHOUT passwords / addresses, system values. No pictures."""
    import io as _io
    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        cfg = {k: ("***" if _SECRET_RE.search(k) and v not in ("", None, [], {}) else v) for k, v in CFG.items() if k not in VOLATILE}
        z.writestr("settings_without_secrets.json", json.dumps(cfg, indent=1, ensure_ascii=False, default=str))
        z.writestr("events.txt", _scrub_text("\n".join(f"{e.get('t', '')} [{e.get('kind', '')}] {e.get('text', '')}" for e in reversed(STATE["events"]))))
        info = {"version": APP_VERSION, "project": project_info(), "health": None, "sim": {k: v for k, v in sim_status().items() if k != "found"},
                "state": {k: STATE.get(k) for k in ("fps", "cpu", "cpu_temp", "source_label", "source_status", "web_status", "ai_status", "eco",
                                                    "disk", "supply", "battery", "audio", "thermal_res")}}
        try:
            info["health"] = health_check() if "health_check" in globals() else None
        except Exception:
            pass
        z.writestr("system.json", json.dumps(info, indent=1, ensure_ascii=False, default=str))
        for name, cmd in (("journal.txt", ["journalctl", "-u", SERVICE_NAME, "-n", "800", "--no-pager"]), ("kernel.txt", ["dmesg"]),
                          ("uname.txt", ["uname", "-a"]), ("disk.txt", ["df", "-h"]), ("usb.txt", ["lsusb"])):
            if shutil.which(cmd[0]):
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    z.writestr(name, _scrub_text((r.stdout or r.stderr)[-400000:]))
                except (OSError, subprocess.SubprocessError):
                    pass
    return buf.getvalue()


def power_calc():
    """Present consumption and what the main consumers cost - for the calculator on the tools page."""
    w = WATCH_REF.get("w"); bm = getattr(w, "battmon", None) if w is not None else None
    try:
        p, src = bm.watts() if bm is not None else (4.0, "estimate")
    except Exception:
        p, src = 4.0, "estimate"
    parts = [("AI detection", 1.2 if CFG.get("ai_enabled") else 0.0, "ai_enabled"),
             ("Thermal camera", 0.4 if CFG.get("thermal_on") else 0.0, "thermal_on"),
             ("Power saving (when quiet)", -0.9 if CFG.get("eco_on") else 0.0, "eco_on"),
             ("Infrared light", 0.6 if (STATE.get("lights") or {}).get("ir") else 0.0, None),
             ("White light", 0.6 if (STATE.get("lights") or {}).get("white") else 0.0, None),
             ("Own Wi-Fi (hotspot)", 0.3 if (STATE.get("hotspot") or {}).get("on") else 0.0, None),
             ("Patrol (servos)", 0.5 if CFG.get("patrol") else 0.0, "patrol")]
    b = STATE.get("battery") or {}
    cap = None
    if b.get("on") and b.get("pct") is not None and b.get("cap_wh"):
        cap = float(b["cap_wh"]) * float(b["pct"]) / 100.0
    elif float(CFG.get("batt_mah") or 0) > 0:
        cap = float(CFG["batt_mah"]) * 3.7 / 1000.0 * 0.85
    return {"watts": round(p, 2), "src": src, "parts": [{"name": n, "w": w_, "key": k} for n, w_, k in parts],
            "cap_wh": round(cap, 1) if cap else None, "battery": b}


def tools_state():
    T = TOOLS
    return {"net": {k: v for k, v in T["net"].items() if k not in ("seen",)}, "wifi": T["wifi"], "speed": T["speed"], "sec": T["sec"],
            "bt": {"running": T["bt"]["running"], "t": T["bt"]["t"], "devices": T["bt"]["devices"], "msg": T["bt"]["msg"],
                   "trackers": [{"addr": a, "kind": x["kind"], "min": round((x["last"] - x["first"]) / 60.0)} for a, x in T["bt"]["trackers"].items()]},
            "servo": T["servo"], "sd": T["sd"], "presence": {"here": T["presence"]["here"], "since": T["presence"]["since"], "who": T["presence"]["who"]},
            "cfg": {k: CFG.get(k) for k in ("net_watch", "net_known", "presence_macs", "presence_auto", "presence_gone_min", "bt_tracker_warn",
                                            "bt_tracker_min", "presence_bt")},
            "dual": dual_state(), "toolmode": toolmode_state(), "power": power_calc(), "has": {"nmcli": bool(shutil.which("nmcli")), "ping": bool(shutil.which("ping")), "bleak": _has_bleak()}}


def _has_bleak():
    try:
        import importlib.util
        return importlib.util.find_spec("bleak") is not None
    except Exception:
        return False


class ToolsWatch:
    """In the background: every 10 minutes look for new devices in the network (when wanted), and for trackers."""
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True, name="toolswatch").start()

    def loop(self):
        time.sleep(60)
        n = 0
        while True:
            try:
                if CFG.get("net_watch") or CFG.get("presence_macs"):
                    net_scan(alert=True)
                if CFG.get("bt_tracker_warn") and n % 2 == 0 and _has_bleak():
                    bt_scan(8)
            except Exception as e:
                log_event("sys", f"Tools: {e}"[:160])
            n += 1
            time.sleep(300 if CFG.get("presence_macs") else 600)



def tools_cfg(key, value, mac=None):
    try:
        if key in ("net_watch", "presence_auto", "bt_tracker_warn"):
            CFG[key] = bool(value)
        elif key == "presence_gone_min":
            CFG[key] = float(min(120.0, max(2.0, float(value))))
        elif key == "bt_tracker_min":
            CFG[key] = float(min(180.0, max(10.0, float(value))))
        elif key in ("presence_macs", "presence_bt"):
            mac = str(mac or "").lower()
            if not re.fullmatch(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}", mac):
                return False, "bad address"
            L = [m for m in (CFG.get(key) or []) if m != mac]
            if value:
                L.append(mac)
            CFG[key] = L[-10:]
            if key == "presence_macs":
                TOOLS["presence"]["here"] = None if not L else TOOLS["presence"]["here"]
        else:
            return False, "unknown setting"
    except (TypeError, ValueError):
        return False, "bad value"
    save_settings()
    return True, ""

# ---- 3D simulator for Windows: the Pi offers it at /sim/simulator3d.zip. It is too big to be part of this program file, so the
# Pi fetches it once from the project storage (next to the updates) and checks it with the checksum below (this program file is
# signed, so the checksum can be trusted). ----
SIM3D = {"version": "3D-3.50", "file": "simulator3d/MotionWatch3D_Simulator.zip", "size": 30882539,
         "sha256": "fb4061dd4e73a7890b11ee6991a0ec3863441285296d1327c8b2335eed1fe562"}
SIM3D_DL = {"running": False, "got": 0, "msg": ""}
# The Python world simulator (second simulator, own folder simulator_python/ in the project): fetched and checked the same way.
SIMPY = {"version": "PY-1.2", "file": "simulator_python/MotionWatchSimulator_PY-1.2.zip", "size": 138432,
         "sha256": "7e278179dc8f1c79b964248ad0a5cb500cc42f2010587a07b7641fe9f0577385", "stem": "MotionWatch_PythonSimulator",
         "label": "MW Sim · Welt (Kevin)"}
SIMPY_DL = {"running": False, "got": 0, "msg": ""}
SIMLATEST = {"t": 0.0, "busy": False, "3d": None, "py": None, "err": ""}   # newest simulator versions in the project (2.95.8)


def sim_latest_check(force=False):
    """look up the newest simulator versions (simulator3d/version.json, simulator_python/MotionWatchSimulator.json) - at
    most once an hour, in the background; only shown, nothing is installed"""
    if SIMLATEST["busy"] or (not force and time.time() - SIMLATEST["t"] < 3600):
        return
    SIMLATEST["busy"] = True; SIMLATEST["t"] = time.time()

    def work():
        try:
            src = CFG["update_url"].strip()
            base = src.rsplit("/", 1)[0] + "/" if src.startswith("https://") else SIM3D_BASE
            for key, path in (("3d", "simulator3d/version.json"), ("py", "simulator_python/MotionWatchSimulator.json")):
                try:
                    with urllib.request.urlopen(_upd_request(base + path), timeout=15) as r:
                        d = json.loads(r.read(65536))
                    SIMLATEST[key] = {"version": str(d.get("version") or "")[:20], "notes": str(d.get("notes") or "")[:400]}
                    SIMLATEST["err"] = ""
                except Exception as e:
                    SIMLATEST["err"] = _upd_error(e)[:120] if "_upd_error" in globals() else str(e)[:120]
        finally:
            SIMLATEST["busy"] = False
    threading.Thread(target=work, daemon=True, name="simlatest").start()


def _vnum(v):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(v or ""))
    return tuple(int(x or 0) for x in m.groups()) if m else None


SIM_AUTOUPD = {}                   # (address, newest version) -> time the update was started (once per version)


def sim_auto_update_check():
    """Motion Watch knows a newer simulator than the one connected: let it update itself (it starts again as it was)"""
    try:
        v = sim_versions()
        if not v.get("newer") or (SIMPI["proc"] is not None and SIMPI["proc"].poll() is None):   # the Pi build comes with Motion Watch
            return
        key = (sim_base(), v["latest"])
        if key in SIM_AUTOUPD:
            return
        d = sim_control()
        if not any(c.get("id") == "update_now" for c in (d.get("controls") or [])):
            return
        SIM_AUTOUPD[key] = time.time()
        sim_control({"action": "press", "id": "update_now"})
        log_event("sys", f"Simulator: update {v['current']} -> {v['latest']} started by itself")
    except Exception:
        pass


def sim_versions():
    """installed version of the simulator in use and the newest one in the project (for the tab Simulator)"""
    sim_latest_check()
    info = SIM.get("info") or {}
    name = str(info.get("name") or "")
    cur, kind = "", ""
    m = re.search(r"3D-\d+\.\d+", name)
    if m:
        cur, kind = m.group(0), "3d"
    else:
        u = sim_base().split("//")[-1]
        f = SIMFOUND.get(u) or SIMFOUND.get(u.replace("localhost", "127.0.0.1")) or {}
        v = str(f.get("version") or "")
        if v.startswith("PY-") or "Python" in name:
            kind = "py"; cur = v if v.startswith("PY-") else ("PY-" + (re.search(r"\d+\.\d+", name) or [""])[0] if re.search(r"\d+\.\d+", name) else "")
    lat = SIMLATEST.get(kind) if kind else None
    newer = bool(lat and cur and _vnum(lat["version"]) and _vnum(cur) and _vnum(lat["version"]) > _vnum(cur))
    return {"kind": kind, "current": cur, "latest": (lat or {}).get("version", ""), "notes": (lat or {}).get("notes", ""), "newer": newer,
            "checked": int(time.time() - SIMLATEST["t"]) if SIMLATEST["t"] else None, "err": SIMLATEST["err"]}
SIM3D["stem"] = "MotionWatch3D_Simulator"; SIM3D["label"] = "MW Sim · 3D"
SIM3D_BASE = "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/"


def sim3d_path(pkg=None):
    pkg = pkg or SIM3D
    return os.path.join(DATA_DIR, "sim3d", pkg["stem"] + "_" + pkg["version"] + ".zip")


def sim3d_ready(pkg=None):
    pkg = pkg or SIM3D
    p = sim3d_path(pkg)
    return os.path.isfile(p) and os.path.getsize(p) == pkg["size"]


def sim3d_fetch(pkg=None, dl=None):
    """fetch a simulator package once from the project storage and check its checksum (3D simulator or Python world simulator)"""
    SIM3D_ = pkg or SIM3D; SIM3D_DL_ = dl if dl is not None else SIM3D_DL
    if SIM3D_DL_["running"] or sim3d_ready(SIM3D_):
        return
    SIM3D_DL_.update(running=True, got=0, msg="")

    def work(SIM3D=SIM3D_, SIM3D_DL=SIM3D_DL_):
        import hashlib
        p = sim3d_path(SIM3D); tmp = p + ".part"
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            src = CFG["update_url"].strip()
            base = src.rsplit("/", 1)[0] + "/" if src.startswith("https://") else SIM3D_BASE
            h = hashlib.sha256()
            with urllib.request.urlopen(_upd_request(base + SIM3D["file"]), timeout=30) as r, open(tmp, "wb") as f:
                while True:
                    b = r.read(1 << 16)
                    if not b:
                        break
                    f.write(b); h.update(b); SIM3D_DL["got"] += len(b)
                    if SIM3D_DL["got"] > SIM3D["size"] + 1024:
                        raise ValueError("file too large")
            if h.hexdigest() != SIM3D["sha256"]:
                raise ValueError("checksum wrong - the file was changed or is damaged")
            os.replace(tmp, p)
            for old in glob.glob(os.path.join(os.path.dirname(p), SIM3D["stem"] + "_*.zip")):
                if old != p:
                    os.remove(old)
            log_event("sys", f"{SIM3D['label']} {SIM3D['version']} ready for download")
        except Exception as e:
            SIM3D_DL["msg"] = _upd_error(e)[:160]
            log_event("sys", f"{SIM3D['label']} could not be fetched: " + SIM3D_DL["msg"])
            try:
                os.remove(tmp)
            except OSError:
                pass
        finally:
            SIM3D_DL["running"] = False
    threading.Thread(target=work, daemon=True, name="simpkg").start()


# ---- the 3D simulator right on the Pi (2.95.51): the build for ARM64, shown on the HDMI (television). Fetched and checked like
# the Windows package, unpacked into the data folder and started on the desktop of the Pi; Motion Watch connects to it. ----
SIM3DPI = {"version": "3D-3.50", "file": "simulator3d/MotionWatch3D_Pi.zip", "size": 24004157,
           "sha256": "4ca70773a59946c9f0686b557004a4f31018f3772b7bdfd7f9ef8c28e3cd9faf", "stem": "MotionWatch3D_Pi", "label": "MW Sim · 3D (Pi)"}
SIM3DPI_DL = {"running": False, "got": 0, "msg": ""}
SIMPI = {"proc": None, "msg": "", "want": False}


def _desktop_env():
    """the environment for a window on the HDMI of the Pi (Wayland or X11) - or None without a desktop"""
    env = dict(os.environ)
    uid = os.getuid() if hasattr(os, "getuid") else 1000
    rt = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    if env.get("WAYLAND_DISPLAY") or env.get("DISPLAY"):
        return env
    way = next((os.path.basename(x) for x in sorted(glob.glob(os.path.join(rt, "wayland-*"))) if not x.endswith(".lock")), "")
    if way:
        env["WAYLAND_DISPLAY"] = way; env["XDG_RUNTIME_DIR"] = rt
        if os.path.exists("/tmp/.X11-unix/X0"):
            env["DISPLAY"] = ":0"                              # Xwayland: Godot opens its window through it
        return env
    if os.path.exists("/tmp/.X11-unix/X0"):
        env["DISPLAY"] = ":0"
        return env
    return None


def simpi_possible():
    import platform
    return sys.platform.startswith("linux") and platform.machine().lower() in ("aarch64", "arm64") and bool(SIM3DPI.get("size"))


def simpi_dir():
    return os.path.join(DATA_DIR, "sim3d", "pi_" + SIM3DPI["version"])


def simpi_state():
    on = SIMPI["proc"] is not None and SIMPI["proc"].poll() is None
    pct = int(100 * SIM3DPI_DL["got"] / SIM3DPI["size"]) if SIM3DPI.get("size") else 0
    return {"possible": simpi_possible(), "on": on, "version": SIM3DPI["version"], "loading": SIM3DPI_DL["running"], "pct": pct,
            "msg": SIM3DPI_DL["msg"] or SIMPI["msg"], "ready": sim3d_ready(SIM3DPI) if SIM3DPI.get("size") else False}


def simpi_start(who="web"):
    """fetch (once), unpack and start the 3D simulator on the Pi; Motion Watch then uses it"""
    if not simpi_possible():
        return False, "only on a Raspberry Pi (64 bit)"
    if SIMPI["proc"] is not None and SIMPI["proc"].poll() is None:
        return True, ""
    if not sim3d_ready(SIM3DPI):
        SIMPI["want"] = True
        sim3d_fetch(SIM3DPI, SIM3DPI_DL)
        return True, ""
    env = _desktop_env()
    if env is None:
        SIMPI["msg"] = "no desktop on the HDMI (Raspberry Pi OS with desktop needed)"
        return False, SIMPI["msg"]
    d_ = simpi_dir(); exe = os.path.join(d_, "MotionWatch3D", "MotionWatch3D.arm64")
    try:
        if not os.path.isfile(exe):
            os.makedirs(d_, exist_ok=True)
            with zipfile.ZipFile(sim3d_path(SIM3DPI)) as z:
                for n in z.namelist():
                    if n.startswith("/") or ".." in n.split("/"):
                        raise ValueError("bad file name in the package")
                z.extractall(d_)
            for old in glob.glob(os.path.join(DATA_DIR, "sim3d", "pi_*")):
                if old != d_:
                    shutil.rmtree(old, ignore_errors=True)
        os.chmod(exe, 0o755)
        port = 8765
        SIMPI["proc"] = subprocess.Popen([exe, "--", "--no-update", "--stream", "--quality", "simple",
                                          "--port", str(port)], cwd=os.path.dirname(exe), env=env, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception as e:
        SIMPI["msg"] = "start: " + str(e)[:100]
        return False, SIMPI["msg"]
    SIMPI["msg"] = ""; SIMPI["want"] = False
    CFG["sim_url"] = f"http://127.0.0.1:{port}"; save_settings()
    if not CFG.get("sim_on"):
        sim_set(True, who)
    log_event("sys", f"{SIM3DPI['label']} {SIM3DPI['version']} started on the HDMI ({who})")
    return True, ""


def simpi_stop(who="web"):
    pr = SIMPI["proc"]; SIMPI["want"] = False
    if pr is not None and pr.poll() is None:
        try:
            pr.terminate()
        except Exception:
            pass
    SIMPI["proc"] = None
    log_event("sys", f"{SIM3DPI['label']} stopped ({who})")
    return True, ""


def simpi_tick():
    """after the download: start by itself (called from the health thread)"""
    if SIMPI["want"] and not SIM3DPI_DL["running"] and sim3d_ready(SIM3DPI):
        simpi_start("download")
    elif SIMPI["want"] and SIM3DPI_DL["msg"]:
        SIMPI["want"] = False


def sim3d_wait_page(lang, pkg=None, dl=None, url="/sim/simulator3d.zip"):
    SIM3D = pkg or globals()["SIM3D"]; SIM3D_DL = dl if dl is not None else globals()["SIM3D_DL"]
    pct = int(100 * SIM3D_DL["got"] / SIM3D["size"])
    err = SIM3D_DL["msg"]
    title = tr("3D simulator for Windows" if pkg is None else "Python world simulator", lang)
    body = (f"<p>⚠ {html_escape(tr('could not be prepared', lang))}: {html_escape(tr(err, lang))}</p><p><a href='{url}?retry=1'>"
            f"{html_escape(tr('Try again', lang))}</a></p>") if err else (
        f"<p>{html_escape(tr('The Pi prepares the download once (about 30 MB) …' if pkg is None else 'The Pi prepares the download once …', lang))}</p>"
        f"<div style='height:14px;border-radius:7px;background:#1f2a38;overflow:hidden'><div style='height:100%;width:{pct}%;background:#2f81f7'></div></div>"
        f"<p>{pct} %</p><p style='color:#8b9bb0'>{html_escape(tr('The download starts by itself.', lang))}</p>")
    refresh = "" if err else '<meta http-equiv="refresh" content="2">'
    return (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>{refresh}"
            f"<title>{html_escape(title)}</title></head><body style='font-family:system-ui,sans-serif;background:#0b0f14;color:#e6edf3;max-width:520px;"
            f"margin:40px auto;padding:0 16px'><h2>🎮 {html_escape(title)} {SIM3D['version']}</h2>{body}</body></html>")


SIM_BEACON_PORT = 8764
SIMFOUND = {}                        # "ip:port" -> {"ip", "port", "name", "version", "t"}: simulators that announce themselves


class SimDiscovery:
    """The simulators (Python on the Pi or a PC, 3D on a PC) send a small UDP message every 2 s into the network
    ("I am a Motion Watch simulator on port 8765"). Here they are collected; when the simulation has no working connection
    (and «find automatically» is on), the address of a found simulator is taken over."""
    def __init__(self):
        threading.Thread(target=self.listen, daemon=True, name="simfind").start()
        threading.Thread(target=self.adopt_loop, daemon=True, name="simadopt").start()

    def listen(self):
        import socket
        try:
            s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s_.bind(("0.0.0.0", SIM_BEACON_PORT))
        except OSError as e:
            log_event("sys", f"Simulator search: port {SIM_BEACON_PORT}/udp not usable ({e})"[:160]); return
        while True:
            try:
                data, (ip, _p) = s_.recvfrom(2048)
                d = json.loads(data.decode("utf-8", "replace"))
                if not isinstance(d, dict) or d.get("mwsim") != 1:
                    continue
                port = int(d.get("port") or 8765)
                if not (1 <= port <= 65535) or not re.fullmatch(r"[0-9.]{7,15}", ip):
                    continue
                if ip.startswith("127."):
                    ip = "127.0.0.1"
                k = f"{ip}:{port}"
                new = k not in SIMFOUND
                old = SIMFOUND.get(k) or {}
                SIMFOUND[k] = {"ip": ip, "port": port, "name": str(d.get("name") or "Simulator")[:60],
                               "version": str(d.get("version") or "")[:20], "t": time.time(), "first": old.get("first") or time.time(),
                               "count": int(old.get("count") or 0) + 1, "via": "beacon", "ms": old.get("ms"),
                               "host_told": str(d.get("host") or old.get("host_told") or "")[:40],
                               # CPU of the PC and of the simulator, told in every message (3D-3.29) - seen before the simulation is on
                               "pc_cpu": d.get("pc_cpu") if isinstance(d.get("pc_cpu"), (int, float)) else old.get("pc_cpu"),
                               "sim_cpu": d.get("sim_cpu") if isinstance(d.get("sim_cpu"), (int, float)) else old.get("sim_cpu")}
                if new:
                    log_event("sys", f"Simulator found in the network: {SIMFOUND[k]['name']} on {k}")
            except (ValueError, OSError):
                continue

    def adopt_loop(self):
        while True:
            time.sleep(5)
            try:
                sim_auto_adopt()
                sim_autostart_tick()
            except Exception:
                pass


SIMSCAN = {"running": False, "t": 0.0, "hosts": 0, "found": 0, "secs": 0.0, "net": "", "done": 0}
SIMHOST = {}                       # ip -> computer name (from the simulator itself, or asked once from the router's name service)


def _host_clean(h):
    h = re.sub(r"[^\w .\-]", "", str(h or "")).strip()[:40]
    if re.fullmatch(r"[0-9.]+", h):
        return ""
    for dom in (".local", ".lan", ".home", ".fritz.box", ".box", ".localdomain", ".internal"):   # «PC-DANIEL.fritz.box» -> «PC-DANIEL»
        if h.lower().endswith(dom):
            h = h[: -len(dom)]
    return h


def sim_host(ip, told=""):
    """the computer name of a simulator: what it says itself, else this device's name, else asked once in the background"""
    import socket
    told = _host_clean(told)
    if told:
        SIMHOST[ip] = told; return told
    if ip.startswith("127."):
        return _host_clean(socket.gethostname())
    if ip in SIMHOST:
        return SIMHOST[ip]
    SIMHOST[ip] = ""

    def ask():
        try:
            SIMHOST[ip] = _host_clean(socket.gethostbyaddr(ip)[0]) or SIMHOST.get(ip, "")
        except (OSError, UnicodeError):
            pass
    threading.Thread(target=ask, daemon=True, name="simhost").start()
    return ""


def _local_ipv4():
    import socket
    s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s_.connect(("10.255.255.255", 1))                  # nothing is sent: only finds the own address in the network
        return s_.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s_.close()


def sim_scan():
    """Active search: ask every address of the own network (x.x.x.1 - 254) on the simulator ports for /info.
    Finds simulators also where the little UDP messages do not get through (some routers / Wi-Fi)."""
    if SIMSCAN["running"]:
        return False
    from concurrent.futures import ThreadPoolExecutor
    ip = _local_ipv4(); base = ".".join(ip.split(".")[:3])
    hosts = ["127.0.0.1"] + ([f"{base}.{i}" for i in range(1, 255)] if not ip.startswith("127.") else [])
    ports = sorted({8765, 8766, 8767, 8768, int(urllib.parse.urlsplit(sim_base()).port or 8765)})   # 8767 / 8768: further simulators
    SIMSCAN.update(running=True, t=time.time(), hosts=len(hosts) * len(ports), found=0, secs=0.0, net=f"{base}.0/24", done=0)

    def probe(hp):
        h, p = hp
        t0 = time.time()
        try:
            with _SIM_OPENER.open(urllib.request.Request(f"http://{h}:{p}/info", headers={"User-Agent": "MotionWatch"}), timeout=0.8) as r:
                d = json.loads(r.read(65536))
            if not isinstance(d, dict) or "cameras" not in d:
                return
            ms = round((time.time() - t0) * 1000.0, 1)
            k = f"{'127.0.0.1' if h.startswith('127.') else h}:{p}"
            old = SIMFOUND.get(k) or {}
            SIMFOUND[k] = dict(old, ip=k.split(":")[0], port=p, name=str(d.get("name") or "Simulator")[:60], t=time.time(),
                               first=old.get("first") or time.time(), count=int(old.get("count") or 0), via=old.get("via") or "scan", ms=ms,
                               version=old.get("version") or "", host_told=str(d.get("host") or old.get("host_told") or "")[:40])
            SIMSCAN["found"] += 1
        except Exception:
            pass
        finally:
            SIMSCAN["done"] += 1

    def run():
        t0 = time.time()
        try:
            with ThreadPoolExecutor(max_workers=64) as ex:
                list(ex.map(probe, [(h, p) for h in hosts for p in ports
                                    if not (p == TUN_PORT and CFG.get("tunnel_on") and h in ("127.0.0.1", ip))]))   # 2.95.66: not the own tunnel
        finally:
            SIMSCAN.update(running=False, secs=round(time.time() - t0, 1), t=time.time())
            SIMSCAN["found"] = len(sim_found())             # simulators, not addresses (this device is reached twice: 127.0.0.1 and its own address)
            log_event("sys", f"Simulator search in {SIMSCAN['net']}: {SIMSCAN['found']} found ({SIMSCAN['hosts']} addresses in {SIMSCAN['secs']} s)")
    threading.Thread(target=run, daemon=True, name="simscan").start()
    return True


def sim_stats():
    now = time.time(); w = WATCH_REF.get("w"); cam = None
    try:
        if w is not None and CFG["sim_on"] and len(w.frame_gaps) > 3:
            g = [x for x in list(w.frame_gaps)[-20:] if x > 0]
            cam = round(1.0 / (sum(g) / len(g)), 1) if g else None
    except Exception:
        cam = None
    tt = list(SIM["th_times"]); th = None
    if len(tt) > 3 and now - tt[-1] < 3:
        th = round((len(tt) - 1) / max(0.01, tt[-1] - tt[0]), 1)
    ok = SIM["ok"] and now - SIM["t"] < 5
    return {"since": int(now - SIM["since"]) if ok and SIM["since"] else None, "rtt": round(SIM["rtt"], 1) if ok else None,
            "sent": SIM["sent"], "errs": SIM["errs"], "events": SIM["events_n"], "cam_fps": cam if ok else None, "th_fps": th if ok else None,
            "pc_cpu": SIM.get("pc_cpu") if ok else None,
            "name": (SIM.get("info") or {}).get("name") if ok else None}


def sim_found():
    now = time.time()
    if len(SIMFOUND) > 50:                              # 2.95.33: old / flooded entries go
        for k in sorted(SIMFOUND, key=lambda k_: SIMFOUND[k_].get("t", 0))[:len(SIMFOUND) - 30]:
            SIMFOUND.pop(k, None)
    live = [dict(v, age=int(now - v["t"]), host=sim_host(v["ip"], v.get("host_told", ""))) for v in SIMFOUND.values()
            if now - v["t"] < (15 if v.get("via") == "beacon" else 180)]
    local = {(v["port"], v["name"]) for v in live if v["ip"] == "127.0.0.1"}
    live = [v for v in live if v["ip"] == "127.0.0.1" or (v["port"], v["name"]) not in local]   # this device seen twice: once
    return sorted(live, key=lambda v: (v["ip"] == "127.0.0.1", v["ip"], v["port"]))


_SIMGONE = {"t": 0.0}


def sim_autostart_tick():
    """2.95.25: «Simulation on by itself»: a simulator is online -> on; it was switched on that way and no simulator is
    online for 60 s -> off again (back to the real cameras and sensors). Switched by hand: nothing happens by itself."""
    if not CFG.get("sim_autostart"):
        return
    f = sim_found()
    if not f:
        _SIMGONE["block"] = False                       # switched off by hand: on again only with the next simulator
    if f and not CFG["sim_on"]:
        if is_armed() or CFG["armed"]:                  # 2.95.33: an armed camera keeps its real picture
            return
        if not _SIMGONE.get("block"):
            sim_auto_adopt()
            sim_set(True, "automatic (a simulator is online)")
            CFG["sim_auto_on"] = True; save_settings()
            try:
                WATCH_REF["w"].notifier.info(tr("Simulation switched on automatically (a simulator is online)") + f": {f[0].get('name', '')} {f[0].get('ip', '')}")
            except Exception:
                pass
        _SIMGONE["t"] = 0.0
    elif CFG["sim_on"] and CFG.get("sim_auto_on"):
        if f or (SIM["ok"] and time.time() - SIM["t"] < 5):
            _SIMGONE["t"] = 0.0
        elif not _SIMGONE["t"]:
            _SIMGONE["t"] = time.time()
        elif time.time() - _SIMGONE["t"] > 60:
            _SIMGONE["t"] = 0.0
            sim_set(False, "automatic (no simulator online any more)")
            CFG["sim_auto_on"] = False; save_settings()


def sim_auto_adopt():
    """no working simulator connection, but one announces itself -> take its address (the PC one before the Pi's own)"""
    if not CFG.get("sim_auto") or (SIM["ok"] and time.time() - SIM["t"] < 5):
        return
    if tunnel_active() and sim_base().startswith("http://127.0.0.1:18765"):
        return                                     # 2.95.68: the simulator comes through the tunnel - keep it
    f = sim_found()
    if not f:
        return
    cur = sim_base()
    if any(cur == f"http://{x['ip']}:{x['port']}" for x in f):
        return                                     # the address is already one that announces itself
    best = sorted(f, key=lambda v: v["ip"] == "127.0.0.1")[0]
    CFG["sim_url"] = f"http://{best['ip']}:{best['port']}"; save_settings()
    log_event("sys", f"Simulator found automatically: {best['name']} - address {CFG['sim_url']} taken over")
    if CFG["sim_on"]:                               # the cameras come from the new address
        w = WATCH_REF.get("w")
        if w is not None and str(CFG["source"]).startswith("sim:"):
            w._open_gen += 1; w._start_opener(CFG["source"])

