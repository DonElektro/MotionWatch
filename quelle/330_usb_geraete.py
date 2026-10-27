#@ Motion Watch – Teil 330: USB-Geräte, Spielesammlung, Seite verlassen (✕ Zurück). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# USB devices (2.95.30): what is plugged in, with maker, model, speed, power and what Linux made of it
#   (network card wlan1, drive sda, camera /dev/video0, serial port …). Read from /sys - no extra program needed.
# ----------------------------------------------------------------------------
USB_SYS = "/sys"
USB_CLASSES = {0x01: "Audio", 0x02: "Communication", 0x03: "Input device (keyboard, mouse …)", 0x05: "Physical", 0x06: "Image (photo camera)",
               0x07: "Printer", 0x08: "Mass storage", 0x09: "Hub", 0x0a: "CDC data", 0x0b: "Smart card", 0x0d: "Content security",
               0x0e: "Video (webcam)", 0x0f: "Health", 0x10: "Audio/video", 0x11: "Billboard", 0xdc: "Diagnostic",
               0xe0: "Wireless (Bluetooth, Wi-Fi …)", 0xef: "Miscellaneous", 0xfe: "Application specific", 0xff: "Vendor specific"}
_USB_IDS = {}


def _srd(p):
    try:
        with open(p, errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""


def _usb_ids():
    """names from the usb.ids list (comes with usbutils / hwdata); empty if it is not there"""
    if _USB_IDS:
        return _USB_IDS
    _USB_IDS["-"] = {}
    for fn in ("/usr/share/hwdata/usb.ids", "/usr/share/misc/usb.ids", "/var/lib/usbutils/usb.ids", "/usr/share/usb.ids"):
        try:
            with open(fn, encoding="utf-8", errors="replace") as f:
                ven = None
                for ln in f:
                    if not ln.strip() or ln.startswith("#"):
                        continue
                    if ln[:2] == "C ":
                        break                               # the class lists follow: done
                    if ln[0] != "\t" and len(ln) > 6 and ln[4:6] == "  ":
                        ven = ln[:4].lower(); _USB_IDS[ven] = (ln[6:].strip(), {})
                    elif ln[0] == "\t" and ln[1] != "\t" and ven and ln[5:7] == "  ":
                        _USB_IDS[ven][1][ln[1:5].lower()] = ln[7:].strip()
            break
        except OSError:
            continue
    return _USB_IDS


def _usb_links(real):
    """what Linux made of the device: network interfaces, drives, cameras, serial ports, sound cards"""
    out = []
    base = os.path.join(USB_SYS, "class")
    def under(p):
        try:
            return os.path.realpath(p).startswith(real + "/")
        except OSError:
            return False
    for kind, cls, pat in (("net", "net", None), ("video", "video4linux", None), ("serial", "tty", ("ttyUSB", "ttyACM")), ("sound", "sound", ("card",))):
        try:
            names = sorted(os.listdir(os.path.join(base, cls)))
        except OSError:
            continue
        for n in names:
            if pat and not n.startswith(pat):
                continue
            if under(os.path.join(base, cls, n, "device")):
                x = {"kind": kind, "name": n if kind == "net" else "/dev/" + n if kind != "sound" else n}
                if kind == "net":
                    x["mac"] = _srd(os.path.join(base, cls, n, "address"))
                    x["state"] = _srd(os.path.join(base, cls, n, "operstate"))
                elif kind == "video":
                    x["label"] = _srd(os.path.join(base, cls, n, "name"))
                out.append(x)
    try:
        blocks = sorted(os.listdir(os.path.join(USB_SYS, "block")))
    except OSError:
        blocks = []
    mounts = {}
    try:
        with open("/proc/mounts") as f:
            for ln in f:
                a = ln.split()
                if len(a) > 2 and a[0].startswith("/dev/"):
                    mounts.setdefault(a[0][5:], a[1].replace("\\040", " "))
    except OSError:
        pass
    for b in blocks:
        if under(os.path.join(USB_SYS, "block", b)):
            try:
                size = int(_srd(os.path.join(USB_SYS, "block", b, "size")) or 0) * 512
            except ValueError:
                size = 0
            mp = [mounts[k] for k in sorted(mounts) if k == b or (k.startswith(b) and k[len(b):].lstrip("p").isdigit())]
            out.append({"kind": "disk", "name": "/dev/" + b, "size": size, "mounts": mp[:4]})
    return out


def usb_list():
    devs = []
    root = os.path.join(USB_SYS, "bus", "usb", "devices")
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    ids = _usb_ids()
    for d in names:
        if ":" in d:
            continue                                      # an interface, not a device
        p = os.path.join(root, d)
        vid = _srd(os.path.join(p, "idVendor")).lower()
        if not vid:
            continue
        pid = _srd(os.path.join(p, "idProduct")).lower()
        try:
            dcls = int(_srd(os.path.join(p, "bDeviceClass")) or "0", 16)
        except ValueError:
            dcls = 0
        ifc, drv = [], []
        try:
            for i in sorted(os.listdir(p)):
                if i.startswith(d + ":"):
                    try:
                        c_ = int(_srd(os.path.join(p, i, "bInterfaceClass")) or "0", 16)
                    except ValueError:
                        c_ = 0
                    if c_ not in ifc:
                        ifc.append(c_)
                    dl = os.path.join(p, i, "driver")
                    if os.path.islink(dl):
                        n_ = os.path.basename(os.readlink(dl))
                        if n_ not in drv:
                            drv.append(n_)
        except OSError:
            pass
        cls = [dcls] if dcls not in (0, 0xef) else []
        cls += [c_ for c_ in ifc if c_ not in cls]
        vname, prods = ids.get(vid, ("", {}))
        try:
            speed = float(_srd(os.path.join(p, "speed")) or 0)
        except ValueError:
            speed = 0
        try:
            ma = int(re.sub(r"[^0-9]", "", _srd(os.path.join(p, "bMaxPower"))) or 0)
        except ValueError:
            ma = 0
        real = os.path.realpath(p)
        leaf = dcls != 9 and not d.startswith("usb")      # hubs and controllers would show everything behind them
        devs.append({"port": d, "bus": _srd(os.path.join(p, "busnum")), "dev": _srd(os.path.join(p, "devnum")),
                     "vid": vid, "pid": pid, "maker": _srd(os.path.join(p, "manufacturer")) or vname, "product": _srd(os.path.join(p, "product")) or prods.get(pid, ""),
                     "maker_db": vname, "product_db": prods.get(pid, ""), "serial": _srd(os.path.join(p, "serial")),
                     "usb": _srd(os.path.join(p, "version")), "speed": speed, "ma": ma, "classes": [USB_CLASSES.get(c_, "class %02x" % c_) for c_ in cls],
                     "hub": dcls == 9, "root": d.startswith("usb"), "drivers": drv, "links": _usb_links(real) if leaf else [],
                     "depth": 0 if d.startswith("usb") else d.count(".") + 1})

    def order(x):                                      # controller first, then the devices behind it (tree order)
        try:
            return (int(x["bus"] or 0), [] if x["root"] else [int(n_) for n_ in x["port"].split("-", 1)[1].split(".")])
        except ValueError:
            return (999, [])
    return sorted(devs, key=order)


def lan_guest_ip(ip, fwd=""):
    """True for a device in the own home network (no login needed for /spiele). Not for tunnels or Tailscale."""
    if fwd:
        return False                                # came through a proxy/tunnel: treat as outside
    try:
        a = ipaddress.ip_address((ip or "").split("%")[0])
        if getattr(a, "ipv4_mapped", None):
            a = a.ipv4_mapped
        return a.is_private and not a.is_loopback and not is_remote_ip(str(a))
    except ValueError:
        return False


