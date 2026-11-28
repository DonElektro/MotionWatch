#@ MoveEye – Teil 639zzzzzx: «Wärmebild prüfen und reparieren» (Mehr → Werkzeuge, nur Admin; Fenster: Einstellungen → Wärmebild): prüft Schritt für Schritt config.txt, /dev/spidev*, /dev/i2c-1, Gruppen, I2C-Scan, Treiber pysenxor (auch in einer venv), numpy / cv2 / picamera2 in einem eigenen Prozess, Pins, Kopfbild, Wärmebild; Reparaturen mit Bestätigung und Rückgängig; Pins der Thermal-90 wählbar. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer 28.11.2026 (MoveEye 4.24.0, erstes echtes Modul «Long-wave IR Thermal Imaging Camera Module 44°» an Jumper-Kabeln,
#   Pi 5 mit Geekworm X1206): Live-Ansicht «Wärmebild» zeigte nur den Spinner, Kopfzeile «Wärme ⚠». Er will keine Befehle tippen:
#   alles prüft MoveEye selbst und zeigt es mit Häkchen / Klartext; was sich reparieren lässt, hat einen Knopf (Bestätigung,
#   Rückgängig). Pinbelegung nach dem Waveshare-Wiki (HAT und Einzelmodul gleich): SS = GPIO 7 (Pin 26), nRESET = GPIO 23 (Pin 16),
#   D_READY = GPIO 24 (Pin 18), MOSI / MISO / CLK = GPIO 10 / 9 / 11, SDA / SCL = GPIO 2 / 3, I2C 0x40;
#   /boot/firmware/config.txt: dtparam=spi=on und darunter dtoverlay=spi0-0cs (gibt GPIO 7 frei), I2C ein.
# Reparaturen (nur mit sudo -n oder als root; ohne Rechte sagt der Bericht es):
#   overlay  – config.txt sichern (config.txt.moveeye-<Zeit>), fehlende Zeilen ergänzen; Rückgängig = Sicherung zurück. Danach Neustart.
#   senxor   – pysenxor aus einer venv / pysenxor-master für MoveEyes Python sichtbar machen (eine .pth-Datei im Benutzer-Ordner,
#              nur der Ordner senxor, nicht die ganze venv); Rückgängig = Datei löschen. Danach MoveEye neu starten.
#   apt      – fehlende Systempakete (python3-spidev / -smbus2 / -crcmod / -gpiozero / -lgpio); kein Rückgängig nötig.
#   pip      – numpy / opencv-python aus pip (~/.local oder /usr/local), die die apt-Pakete überdecken und picamera2 / cv2 brechen,
#              entfernen; Rückgängig = dieselben Versionen wieder installieren (braucht Internet).
# Test: werkzeuge/waermebild_pruefen_test.py (falscher pysenxor / spidev / smbus / gpiozero, Fehlerfälle, Kopfbild läuft weiter).
# ----------------------------------------------------------------------------
for _k, _v in SENXOR_PIN_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
TC_GPIO_CHOICES = (4, 5, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27)
for _k, _lb in (("senxor_cs", "Thermal-90: CS / SS (chip select) GPIO"), ("senxor_rst", "Thermal-90: nRESET GPIO"),
                ("senxor_drdy", "Thermal-90: D_READY (data ready) GPIO")):
    if not any(t_[1] == _k for t_ in TEXTS):
        TEXTS.append(("Thermal camera", _k, _lb, "enum", "senxor_gpio"))
    TEXT_SPECS[_k] = ("enum", "senxor_gpio")
_tc_text_choice_pairs_base = text_choice_pairs


def text_choice_pairs(key):                               # + 639zzzzzx: the pins of the Thermal-90 (never GPIO 6 / 16 of an X1206)
    if (TEXT_SPECS.get(key) or (None, None))[1] != "senxor_gpio":
        return _tc_text_choice_pairs_base(key)
    try:
        bad = ups_x12_pins()
    except Exception:
        bad = set()
    cur = str(CFG.get(key) or "")
    gs = [g for g in TC_GPIO_CHOICES if g not in bad] + ([int(cur)] if cur.isdigit() else [])
    std = {"senxor_cs": 7, "senxor_rst": 23, "senxor_drdy": 24}.get(key)
    return [(str(g), f"GPIO {g}" + (" (" + tr("standard") + ")" if g == std else "")) for g in sorted(set(gs))]


TC = {"busy": False, "last": None}
TC_PTH = "moveeye-pysenxor.pth"
TC_PROBE = r'''
import json, sys
out = {}
for n in ("numpy", "cv2", "picamera2", "simplejpeg", "senxor", "spidev", "smbus", "smbus2", "gpiozero", "lgpio", "crcmod"):
    try:
        m = __import__(n)
        if n == "senxor":
            __import__("senxor.mi48"); __import__("senxor.interfaces"); __import__("senxor.utils")
        out[n] = {"ok": True, "ver": str(getattr(m, "__version__", "") or ""), "file": str(getattr(m, "__file__", "") or "")}
    except BaseException as e:
        out[n] = {"ok": False, "err": (type(e).__name__ + ": " + str(e))[:160]}
print(json.dumps(out))
'''


def _tc_run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except FileNotFoundError:
        return 127, "", "not installed: " + str(cmd[0])
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)[:160]


def _tc_root(cmd):
    """the command as root: directly when MoveEye is root, else sudo -n (never asks for a password)"""
    return list(cmd) if hasattr(os, "geteuid") and os.geteuid() == 0 else ["sudo", "-n"] + list(cmd)


def tc_config_path():
    for p in ("/boot/firmware/config.txt", "/boot/config.txt"):
        if os.path.isfile(p):
            return p
    return ""


def tc_config_flags(text):
    """active (not commented) lines of config.txt: spi on, i2c on, overlay spi0-0cs"""
    spi = i2c = cs0 = False
    for ln in str(text or "").splitlines():
        s = ln.split("#", 1)[0].strip().replace(" ", "")
        if not s:
            continue
        if re.match(r"^dtparam=(.*,)?spi(=on)?(,|$)", s):
            spi = True
        if re.match(r"^dtparam=(.*,)?i2c(_arm)?(=on)?(,|$)", s):
            i2c = True
        if s.startswith("dtoverlay=spi0-0cs"):
            cs0 = True
    return {"spi": spi, "i2c": i2c, "spi0_0cs": cs0}


def tc_config_fixed(text):
    """config.txt with the missing lines (after dtparam=spi=on, else at the end under [all]); None = nothing to add"""
    f = tc_config_flags(text)
    if f["spi"] and f["i2c"] and f["spi0_0cs"]:
        return None
    lines = str(text or "").splitlines()
    add_spi = [] if f["spi"] else ["dtparam=spi=on"]
    add_cs = [] if f["spi0_0cs"] else ["dtoverlay=spi0-0cs"]
    add_i2c = [] if f["i2c"] else ["dtparam=i2c_arm=on"]
    at = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*dtparam=(.*,)?spi(=on)?(,|$)", ln.split("#", 1)[0].replace(" ", "")):
            at = i
            break
    if at is not None and add_cs:
        lines.insert(at + 1, "dtoverlay=spi0-0cs   # MoveEye: GPIO 7 for the thermal camera (Waveshare)")
        add_cs = []
    rest = add_spi + add_cs + add_i2c
    if rest:
        lines += ["", "[all]", "# MoveEye: thermal camera (Waveshare Thermal-90 / 44)"] + rest
    return "\n".join(lines) + "\n"


def _tc_kind(path):
    p = str(path or "")
    if not p:
        return ""
    try:
        import site
        us = site.getusersitepackages()
    except Exception:
        us = ""
    if us and p.startswith(us) or "/.local/lib/" in p:
        return "pip-user"
    if p.startswith("/usr/local/lib/"):
        return "pip-system"
    if p.startswith("/usr/lib/python3/dist-packages/"):
        return "apt"
    if "/site-packages/" in p and "/lib/python3" in p:
        return "venv"
    return "other"


def tc_probe():
    """imports in a fresh process with MoveEye's own Python (broken pip packages show up there, not in the running program)"""
    rc, out, err = _tc_run([sys.executable, "-c", TC_PROBE], 60)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {"_err": (err or out or str(rc))[-200:]}


def tc_find_senxor():
    """pysenxor somewhere in the home folder (a venv as in the Waveshare guide, or the unpacked pysenxor-master): the folder
    that holds the package «senxor» - [] when there is none"""
    home = os.path.expanduser("~"); found = []
    pats = [os.path.join(home, "*", "lib", "python3*", "site-packages"), os.path.join(home, "*", "*", "lib", "python3*", "site-packages"),
            os.path.join(home, "*pysenxor*"), os.path.join(home, "*", "*pysenxor*"), os.path.join(home, "*", "*", "*pysenxor*")]
    for pat in pats:
        for d in sorted(glob.glob(pat))[:40]:
            if os.path.isfile(os.path.join(d, "senxor", "__init__.py")) and os.path.isfile(os.path.join(d, "senxor", "mi48.py")):
                if d not in found:
                    found.append(d)
            if d.endswith("site-packages"):
                for pth in glob.glob(os.path.join(d, "*.pth")) + glob.glob(os.path.join(d, "*.egg-link")):
                    try:
                        for ln in open(pth, errors="replace").read().splitlines()[:5]:
                            ln = ln.strip()
                            if ln and not ln.startswith(("import", "#")) and os.path.isfile(os.path.join(ln, "senxor", "mi48.py")) and ln not in found:
                                found.append(ln)
                    except OSError:
                        pass
    return found[:5]


def tc_i2c_scan(addrs=(0x2d, 0x36, 0x40, 0x41, 0x42, 0x44)):
    try:
        try:
            from smbus import SMBus
        except ImportError:
            from smbus2 import SMBus
    except ImportError:
        return None, "python3-smbus missing"
    try:
        bus = SMBus(1)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"[:120]
    seen = []
    try:
        for a in addrs:
            try:
                bus.read_byte(a); seen.append(a)
            except Exception:
                pass
    finally:
        try:
            bus.close()
        except Exception:
            pass
    return seen, ""


def tc_pin_conflicts(pins=None):
    """other users of the pins of the Thermal-90 (X1206, buttons, LEDs, relays, lights, servos on GPIO, I2C, SPI)"""
    cs, rst, drdy = pins or senxor_pins()
    own = {}
    try:
        for g_ in ups_x12_pins():
            own[g_] = "Geekworm X1206"
    except Exception:
        pass
    for k, v in CFG.items():
        if (k.startswith("btn_gpio") or k in ("charge_led_gpio", "wind_gpio", "led_gpio")) and str(v or "").isdigit():
            own.setdefault(int(v), k)
    for r in RELAYS:
        own.setdefault(int(r.get("gpio", -1)), "relay")
    for k in ("light_white_out", "light_ir_out"):
        v = str(CFG.get(k, ""))
        if v.startswith("gpio:") and v[5:].isdigit():
            own.setdefault(int(v[5:]), k)
    if str(STATE.get("servo_backend") or "").startswith(("gpiozero", "pigpio")):
        own.setdefault(GPIO_PAN, "servo pan"); own.setdefault(GPIO_TILT, "servo tilt")
    for g_, n in ((2, "I2C SDA"), (3, "I2C SCL"), (9, "SPI MISO"), (10, "SPI MOSI"), (11, "SPI CLK")):
        own[g_] = n
    out = []
    for nm, p in (("CS", cs), ("nRESET", rst), ("D_READY", drdy)):
        if p in own:
            out.append(f"{nm} GPIO {p} = {own[p]}")
    if len({cs, rst, drdy}) < 3:
        out.append("two functions on the same GPIO")
    return out


def tc_pinctrl(pins):
    """Pi 5: what the kernel says about the pins (pinctrl get N) - e.g. «SPI0_CE1_N» on GPIO 7 without spi0-0cs"""
    if not shutil.which("pinctrl"):
        return {}
    out = {}
    for p in pins:
        rc, o, _e = _tc_run(["pinctrl", "get", str(p)], 5)
        if rc == 0 and o.strip():
            out[p] = o.strip().splitlines()[0][:80]
    return out


def _tc_groups():
    try:
        import grp
        import pwd
        u = pwd.getpwuid(os.getuid()).pw_name
        gs = {grp.getgrgid(x).gr_name for x in os.getgroups()} | {grp.getgrgid(os.getgid()).gr_name}
        return u, gs
    except Exception:
        return "", set()


def _tc_step(steps, sid, ok, title, detail="", fix=None, lang=None):
    steps.append({"id": sid, "ok": ok, "title": tr(title, lang), "detail": str(detail or "")[:400], "fix": fix})


def thermal_check(lang=None, wait=2.0):
    """all checks, in the order of the way of a picture; ok: True = fine, False = error, None = hint"""
    steps = []
    spec = str(CFG.get("thermal_source") or "")
    senx = spec.startswith("senxor")
    pins = senxor_pins()
    devd = os.environ.get("MW_TEST_DEV_DIR") or "/dev"                # tests: a folder with made-up device files
    linux = sys.platform.startswith("linux") and os.path.isdir(devd)
    model = ""
    try:
        model = open("/proc/device-tree/model", errors="replace").read().strip("\x00\n ")[:60]
    except OSError:
        pass
    _tc_step(steps, "source", bool(spec), "Thermal camera chosen",
             (source_label(spec) if spec else tr("none", lang)) + (" · " + model if model else "")
             + (" · " + tr("on", lang) if CFG.get("thermal_on") else ""), lang=lang)
    # --- config.txt
    cp = tc_config_path()
    if cp:
        try:
            flags = tc_config_flags(open(cp, errors="replace").read())
        except OSError as e:
            flags = None
            _tc_step(steps, "config", False, "config.txt", f"{cp}: {e}"[:160], lang=lang)
        if flags is not None:
            miss = [n for n, k in (("dtparam=spi=on", "spi"), ("dtparam=i2c_arm=on", "i2c"), ("dtoverlay=spi0-0cs", "spi0_0cs")) if not flags[k]]
            _tc_step(steps, "config", not miss, "config.txt: SPI, I2C and dtoverlay=spi0-0cs",
                     cp + (" · " + tr("missing", lang) + ": " + ", ".join(miss) if miss else " · ok"),
                     fix="overlay" if miss else None, lang=lang)
    else:
        _tc_step(steps, "config", None, "config.txt: SPI, I2C and dtoverlay=spi0-0cs", tr("not found (not a Raspberry Pi?)", lang), lang=lang)
    # --- devices and groups
    spis = sorted("/dev/" + os.path.basename(x) for x in glob.glob(os.path.join(devd, "spidev*"))) if linux else []
    _tc_step(steps, "spidev", "/dev/spidev0.0" in spis, "SPI device /dev/spidev0.0", ", ".join(spis) or tr("none", lang), lang=lang)
    if "/dev/spidev0.1" in spis and pins[0] == 7:
        _tc_step(steps, "spice1", False, "GPIO 7 belongs to the SPI driver",
                 "/dev/spidev0.1 = CE1 = GPIO 7 · dtoverlay=spi0-0cs", fix="overlay" if cp else None, lang=lang)
    _tc_step(steps, "i2cdev", os.path.exists(os.path.join(devd, "i2c-1")) if linux else False, "I2C bus /dev/i2c-1",
             "ok" if linux and os.path.exists(os.path.join(devd, "i2c-1")) else tr("missing", lang), lang=lang)
    u, gs = _tc_groups()
    need = [x for x in ("spi", "i2c", "gpio") if x not in gs]
    _tc_step(steps, "groups", (not need) or u == "root", "Groups of the MoveEye user",
             (u or "?") + ": " + (", ".join(sorted(g_ for g_ in gs if g_ in ("spi", "i2c", "gpio", "video", "root"))) or "-")
             + (" · " + tr("missing", lang) + ": " + ", ".join(need) if need and u != "root" else ""), lang=lang)
    # --- I2C scan
    seen, err = tc_i2c_scan()
    if seen is None:
        _tc_step(steps, "i2c", False, "I2C scan", err, lang=lang)
    else:
        names = {0x40: "0x40 " + tr("thermal camera", lang), 0x41: "0x41 PCA9685", 0x36: "0x36 X1206", 0x2d: "0x2D UPS HAT (E)",
                 0x42: "0x42 INA219", 0x44: "0x44 INA219 Solar"}
        th_drv = STATE.get("thermal") == "connected" and senx
        _tc_step(steps, "i2c", (0x40 in seen) or th_drv, "I2C scan: thermal camera on 0x40",
                 ", ".join(names.get(a, hex(a)) for a in seen) or tr("nothing answers", lang), lang=lang)
    # --- Python packages (own process)
    pr = tc_probe()
    if "_err" in pr:
        _tc_step(steps, "python", False, "Python packages", pr["_err"], lang=lang)
        pr = {}
    bad_pip = []
    for n in ("numpy", "cv2", "picamera2", "simplejpeg"):
        x = pr.get(n) or {}
        k = _tc_kind(x.get("file"))
        if x.get("ok") and n in ("numpy", "cv2") and k in ("pip-user", "pip-system") and os.path.isdir("/usr/lib/python3/dist-packages/" + n):
            bad_pip.append((n, x.get("ver", ""), k))
    broken = [n for n in ("numpy", "cv2", "picamera2") if pr and not (pr.get(n) or {}).get("ok")]
    det = " · ".join(f"{n} {(pr.get(n) or {}).get('ver', '')} ({_tc_kind((pr.get(n) or {}).get('file')) or tr('missing', lang)})".replace(" ()", "")
                     for n in ("numpy", "cv2", "picamera2") if pr)
    if broken:
        det += " · " + "; ".join(f"{n}: {(pr.get(n) or {}).get('err', '')[:90]}" for n in broken)
    _tc_step(steps, "python", (not broken and not bad_pip) if pr else None, "numpy, OpenCV and picamera2 (own process)",
             det + (" · " + tr("pip packages cover the system packages", lang) + ": " + ", ".join(f"{n} {v} ({k})" for n, v, k in bad_pip) if bad_pip else ""),
             fix="pip" if bad_pip else None, lang=lang)
    sx = pr.get("senxor") or {}
    venvs = [] if sx.get("ok") else tc_find_senxor()
    if sx.get("ok"):
        _tc_step(steps, "senxor", True, "Driver pysenxor for MoveEye's Python", (sx.get("file") or "")[:120], lang=lang)
    else:
        _tc_step(steps, "senxor", False if senx else None, "Driver pysenxor for MoveEye's Python",
                 (sx.get("err") or "")[:120] + (" · " + tr("found, but only in", lang) + ": " + ", ".join(venvs) if venvs else
                                                " · " + tr("not found in the home folder", lang)),
                 fix="senxor" if venvs else None, lang=lang)
    miss_apt = [p for n, p in (("spidev", "python3-spidev"), ("crcmod", "python3-crcmod"), ("gpiozero", "python3-gpiozero"), ("lgpio", "python3-lgpio"))
                if pr and not (pr.get(n) or {}).get("ok")]
    if pr and not ((pr.get("smbus") or {}).get("ok") or (pr.get("smbus2") or {}).get("ok")):
        miss_apt.append("python3-smbus2")
    if pr:
        _tc_step(steps, "apt", not miss_apt, "System packages spidev, smbus, crcmod, gpiozero, lgpio",
                 (tr("missing", lang) + ": " + ", ".join(miss_apt)) if miss_apt else "ok", fix="apt" if miss_apt else None, lang=lang)
    # --- pins
    conf = tc_pin_conflicts(pins)
    pc = tc_pinctrl(pins) if linux else {}
    held = [f"GPIO {p}: {v}" for p, v in pc.items() if "SPI0" in v.upper() or "CE" in v.upper().split("//")[-1]]
    _tc_step(steps, "pins", not conf and not held, "Pins CS / nRESET / D_READY",
             f"CS GPIO {pins[0]} · nRESET GPIO {pins[1]} · D_READY GPIO {pins[2]}" + (" · " + "; ".join(conf + held) if conf or held else ""),
             fix="overlay" if held and cp else None, lang=lang)
    # --- module and pictures
    if senx:
        L = SENXOR_LAST
        if L.get("step") == "ok":
            _tc_step(steps, "module", True, "Module answers (ID, firmware)",
                     " · ".join(x for x in (L.get("id"), ("FW " + L["fw"]) if L.get("fw") else "") if x) or "ok", lang=lang)
        elif L.get("err"):
            _tc_step(steps, "module", False, "Module answers (ID, firmware)", f"{L.get('step')}: {L.get('err')}", lang=lang)
        else:
            _tc_step(steps, "module", None, "Module answers (ID, firmware)", tr("not tried yet", lang), lang=lang)
    w_ = WATCH_REF.get("w")
    hb = time.time() - float(HEART.get("t") or 0)
    head_ok = STATE.get("source_status") == "connected" and hb < 5.0
    _tc_step(steps, "head", head_ok, "Head camera delivers pictures",
             f"{STATE.get('source_label', '')}: {STATE.get('source_status', '')} · " + tr("loop", lang) + f" {hb:.1f} s", lang=lang)
    th = THERMAL
    n0 = getattr(th, "n", 0) if th is not None else 0
    if wait:
        time.sleep(wait)
    n1 = getattr(th, "n", 0) if th is not None else 0
    fps = (n1 - n0) / wait if wait else 0.0
    st = str(STATE.get("thermal") or "")
    age = time.time() - th.t if th is not None and th.t else None
    _tc_step(steps, "frame", st == "connected" and fps > 0, "Thermal picture arrives (picture rate)",
             st + (f" · {fps:.1f} " + tr("pictures/s", lang) if fps or st == "connected" else "")
             + (f" · {STATE.get('thermal_res', '')}" if STATE.get("thermal_res") else "")
             + (f" · max {STATE.get('thermal_max')} °C" if st == "connected" and STATE.get("thermal_max") is not None else "")
             + (f" · " + tr("last picture", lang) + f" {age:.0f} s" if age is not None and age > 3 else ""), lang=lang)
    logs = [f"{e.get('t', '')} {e.get('text', '')}"[:200] for e in list(STATE.get("events") or [])
            if re.search(r"camera|thermal|video source|wärme", str(e.get("text", "")), re.I)][:20]
    undo = tc_undo_list()
    res = {"ok": True, "steps": steps, "log": logs, "undo": undo, "admin_fix": True,
           "pins": {"cs": pins[0], "rst": pins[1], "drdy": pins[2]}, "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    res["report"] = tc_report(res, lang)
    TC["last"] = res
    return res


def tc_report(res, lang=None):
    """the result as plain text to copy (no passwords, no addresses: only what the checks show)"""
    ic = {True: "✓", False: "✗", None: "!"}
    out = [f"MoveEye {APP_VERSION} · " + tr("Check the thermal camera", lang) + " · " + res.get("t", "")]
    for s in res.get("steps", []):
        out.append(f"{ic.get(s['ok'], '?')} {s['title']}: {s['detail']}")
    if res.get("log"):
        out.append("")
        out.append(tr("Log (camera / thermal)", lang) + ":")
        out += ["  " + x for x in res["log"]]
    return "\n".join(out)


# ---- repairs ----------------------------------------------------------------------------------------------------------------
def _tc_undo_load():
    try:
        with open(os.path.join(DATA_DIR, "thermal_fix_undo.json")) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _tc_undo_save(d):
    try:
        with open(os.path.join(DATA_DIR, "thermal_fix_undo.json") + ".tmp", "w") as f:
            json.dump(d, f)
        os.replace(os.path.join(DATA_DIR, "thermal_fix_undo.json.tmp"), os.path.join(DATA_DIR, "thermal_fix_undo.json"))
    except OSError:
        pass


def tc_undo_list():
    d = _tc_undo_load()
    return [k for k in ("overlay", "senxor", "pip") if d.get(k)]


def _tc_user_site():
    import site
    if not getattr(site, "ENABLE_USER_SITE", True):
        return ""
    return site.getusersitepackages()


def tc_fix(action, lang=None):
    """-> (ok, message). Every repair that changes something notes how to undo it (thermal_fix_undo.json)."""
    d = _tc_undo_load()
    if action == "overlay":
        cp = tc_config_path()
        if not cp:
            return False, tr("config.txt not found", lang)
        try:
            text = open(cp, errors="replace").read()
        except OSError as e:
            return False, str(e)[:160]
        new = tc_config_fixed(text)
        if new is None:
            return True, tr("nothing to do", lang)
        bak = cp + ".moveeye-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        rc, _o, e = _tc_run(_tc_root(["cp", "-p", cp, bak]), 20)
        if rc != 0:
            return False, tr("no permission (sudo)", lang) + ": " + (e.strip() or str(rc))[:120]
        fd, tmp = tempfile.mkstemp(prefix="moveeye-config-", suffix=".txt")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(new)
            rc, _o, e = _tc_run(_tc_root(["cp", tmp, cp]), 20)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
        if rc != 0:
            return False, tr("no permission (sudo)", lang) + ": " + (e.strip() or str(rc))[:120]
        d["overlay"] = {"file": cp, "backup": bak}; _tc_undo_save(d)
        log_event("sys", f"Thermal camera check: config.txt completed (backup {os.path.basename(bak)}) - restart the Pi")
        return True, tr("config.txt completed - restart the Pi so that it takes effect", lang) + " · " + os.path.basename(bak)
    if action == "senxor":
        src = tc_find_senxor()
        us = _tc_user_site()
        if not src:
            return False, tr("pysenxor not found in the home folder", lang)
        if not us:
            return False, tr("the user folder of Python is switched off", lang)
        link_dir = os.path.join(DATA_DIR, "pysenxor")
        try:
            os.makedirs(us, exist_ok=True); os.makedirs(link_dir, exist_ok=True)
            ln = os.path.join(link_dir, "senxor")
            if os.path.islink(ln):
                os.remove(ln)
            if not os.path.exists(ln):
                os.symlink(os.path.join(src[0], "senxor"), ln)
            with open(os.path.join(us, TC_PTH), "w") as f:
                f.write(link_dir + "\n")
        except OSError as e:
            return False, str(e)[:160]
        d["senxor"] = {"pth": os.path.join(us, TC_PTH), "link": os.path.join(link_dir, "senxor"), "from": src[0]}; _tc_undo_save(d)
        log_event("sys", f"Thermal camera check: pysenxor taken over from {src[0]} - restart MoveEye")
        return True, tr("pysenxor is now visible for MoveEye - restart MoveEye", lang)
    if action == "apt":
        pr = tc_probe()
        pk = [p for n, p in (("spidev", "python3-spidev"), ("crcmod", "python3-crcmod"), ("gpiozero", "python3-gpiozero"), ("lgpio", "python3-lgpio"))
              if not (pr.get(n) or {}).get("ok")]
        if not ((pr.get("smbus") or {}).get("ok") or (pr.get("smbus2") or {}).get("ok")):
            pk.append("python3-smbus2")
        if not pk:
            return True, tr("nothing to do", lang)
        rc, o, e = _tc_run(_tc_root(["apt-get", "install", "-y", "--no-install-recommends"] + pk), 600)
        log_event("sys", f"Thermal camera check: apt install {' '.join(pk)} -> {rc}")
        return rc == 0, ("ok: " + ", ".join(pk)) if rc == 0 else (tr("no permission (sudo)", lang) if "sudo" in e else "") + (e or o)[-160:]
    if action == "pip":
        pr = tc_probe(); done = []
        names = {"numpy": ["numpy"], "cv2": ["opencv-python", "opencv-contrib-python", "opencv-python-headless", "opencv-contrib-python-headless"]}
        for n in ("numpy", "cv2"):
            x = pr.get(n) or {}
            k = _tc_kind(x.get("file"))
            if not (x.get("ok") and k in ("pip-user", "pip-system") and os.path.isdir("/usr/lib/python3/dist-packages/" + n)):
                continue
            cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "--break-system-packages"] + names[n]
            rc, o, e = _tc_run(_tc_root(cmd) if k == "pip-system" else cmd, 300)
            if rc != 0:
                return False, f"pip uninstall {n}: " + (e or o)[-160:]
            done.append([names[n][0] if n == "numpy" else "opencv-python", x.get("ver", ""), k])
        if not done:
            return True, tr("nothing to do", lang)
        d["pip"] = (d.get("pip") or []) + done; _tc_undo_save(d)
        log_event("sys", "Thermal camera check: pip packages removed: " + ", ".join(f"{a} {b}" for a, b, _c in done) + " - restart MoveEye")
        return True, tr("removed - the system packages apply again; restart MoveEye", lang) + ": " + ", ".join(f"{a} {b}" for a, b, _c in done)
    if action == "reboot":
        try:
            ok, msg = power_action("reboot", source="thermal check")
            return ok, msg or tr("the Pi restarts", lang)
        except Exception as e:
            return False, str(e)[:160]
    if action == "restart":
        ok = selfheal_restart("thermal", "thermal camera check: restart by hand")
        return ok, tr("MoveEye restarts", lang) if ok else tr("busy - please wait", lang)
    if action.startswith("undo:"):
        what = action[5:]
        x = d.get(what)
        if not x:
            return False, tr("nothing to undo", lang)
        if what == "overlay":
            rc, _o, e = _tc_run(_tc_root(["cp", "-p", x["backup"], x["file"]]), 20)
            if rc != 0:
                return False, tr("no permission (sudo)", lang) + ": " + (e.strip() or str(rc))[:120]
        elif what == "senxor":
            for p in (x.get("pth"), x.get("link")):
                try:
                    if p and (os.path.islink(p) or os.path.exists(p)):
                        os.remove(p)
                except OSError as e:
                    return False, str(e)[:160]
        elif what == "pip":
            for name, ver, k in x:
                cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages"] + (["--user"] if k == "pip-user" else []) + [f"{name}=={ver}" if ver else name]
                rc, o, e = _tc_run(_tc_root(cmd) if k == "pip-system" else cmd, 900)
                if rc != 0:
                    return False, f"pip install {name}: " + (e or o)[-160:]
        d.pop(what, None); _tc_undo_save(d)
        log_event("sys", f"Thermal camera check: undone ({what})")
        return True, tr("undone - restart so that it takes effect", lang)
    return False, "unknown action"


TC_ACTIONS = ("overlay", "senxor", "apt", "pip", "reboot", "restart", "undo:overlay", "undo:senxor", "undo:pip")


def thermal_check_routes(app, reply, body):
    from flask import request, g

    @app.route("/api/thermal_check", methods=["GET", "POST"])
    def api_thermal_check():
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang); a = str(d.get("action") or "")
            if a not in TC_ACTIONS:
                return reply({"ok": False, "error": "unknown action"}, 400)
            if TC["busy"]:
                return reply({"ok": False, "error": tr("busy - please wait", lang)}, 409)
            TC["busy"] = True
            try:
                ok, msg = tc_fix(a, lang)
            finally:
                TC["busy"] = False
            return reply({"ok": bool(ok), "msg": msg, "error": "" if ok else msg})
        return reply(thermal_check(lang))


_servo_routes_tc = servo_routes


def servo_routes(app, reply, body):                       # + 639zzzzzx: the route of the thermal check (550 calls servo_routes)
    _servo_routes_tc(app, reply, body)
    thermal_check_routes(app, reply, body)


# ---- Mehr → Werkzeuge: the entry and its pane ---------------------------------------------------------------------------
TC_TOOL_HTML = ('<button type="button" class="tli" data-k="thcheck" onclick="pick(\'thcheck\')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true">'
                '<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/><path d="M12 9v7"/><path d="M17 4l3 3M20 4l-3 3"/></svg>'
                '<span class="tln"><b data-i18n="Check the thermal camera">Check the thermal camera</b><span class="tsum" data-i18n="and repair: SPI, I2C, driver, pins">and repair: SPI, I2C, driver, pins</span></span><i class="tdot" id="d-thcheck"></i></button>\n  ')
TC_SECTION_HTML = '''<section class="tool" id="c-thcheck" data-k="thcheck" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><h2 data-i18n="Check the thermal camera">Check the thermal camera</h2></div><div class="tact"><button id="tc-run" type="button" data-i18n="Check">Check</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="tc-note">tc-note</div>
    <div id="tc-msg" class="mut" style="margin:6px 0"></div>
    <ul id="tc-list" style="list-style:none;padding:0;margin:6px 0"></ul>
    <div id="tc-undo" class="trow"></div>
    <details id="tc-logw" hidden><summary data-i18n="Log (camera / thermal)">Log (camera / thermal)</summary><pre id="tc-log" style="white-space:pre-wrap;font-size:12px"></pre></details>
    <div class="trow"><button type="button" class="sec" id="tc-copy" data-i18n="Copy the report">Copy the report</button><button type="button" class="sec" id="tc-share" data-i18n="Share" hidden>Share</button><button type="button" class="sec" id="tc-restart" data-i18n="Restart MoveEye">Restart MoveEye</button><button type="button" class="sec" id="tc-reboot" data-i18n="Restart the Pi">Restart the Pi</button></div>
    </div>
  </section>
'''
TC_PAGE_JS = r'''
(function () {
  const $i = id => document.getElementById(id);
  if (!$i("c-thcheck")) return;
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) { return "de"; } };
  const tt = k => { try { return typeof t === "function" ? t(k) : k; } catch (e) { return k; } };
  const FIX = {overlay: ["Add the missing lines to config.txt (a backup is kept)", "tc-q-overlay"],
               senxor: ["Make pysenxor visible for MoveEye", "tc-q-senxor"],
               apt: ["Install the missing system packages", "tc-q-apt"],
               pip: ["Remove the pip packages that cover the system", "tc-q-pip"]};
  const UNDO = {overlay: "Undo: config.txt back", senxor: "Undo: pysenxor link away", pip: "Undo: pip packages back"};
  let REP = "";
  const say = s => { $i("tc-msg").textContent = s || ""; };
  const req = (m, b) => fetch("/api/thermal_check?lang=" + L(), m === "GET" ? {cache: "no-store"} :
      {method: "POST", headers: {"Content-Type": "application/json", "X-Requested-With": "mw"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))})
    .then(r => r.json()).catch(e => ({ok: false, error: String(e)}));
  function doFix(a, q) {
    if (q && !confirm(tt(q))) return;
    say("⏳ " + tt("working…"));
    req("POST", {action: a}).then(r => { say((r.ok ? "✓ " : "⚠ ") + (r.msg || r.error || "")); if (a !== "reboot" && a !== "restart") setTimeout(run, 400); });
  }
  function paint(r) {
    const ul = $i("tc-list"); ul.textContent = "";
    if (!r || !r.ok) { say("⚠ " + ((r && r.error) || "error")); return; }
    REP = r.report || "";
    let bad = 0;
    (r.steps || []).forEach(s => {
      const li = document.createElement("li"); li.style.cssText = "padding:6px 0;border-bottom:1px solid rgba(128,128,128,.25)";
      const ic = s.ok === true ? "✅" : s.ok === false ? "❌" : "⚠️"; if (s.ok === false) bad++;
      const b = document.createElement("b"); b.textContent = ic + " " + s.title; li.appendChild(b);
      const d = document.createElement("div"); d.className = "mut"; d.style.cssText = "font-size:13px;overflow-wrap:anywhere"; d.textContent = s.detail || ""; li.appendChild(d);
      if (s.fix && FIX[s.fix]) { const x = document.createElement("button"); x.type = "button"; x.textContent = "🔧 " + tt(FIX[s.fix][0]); x.style.marginTop = "4px";
        x.onclick = () => doFix(s.fix, FIX[s.fix][1]); li.appendChild(x); }
      ul.appendChild(li);
    });
    const u = $i("tc-undo"); u.textContent = "";
    (r.undo || []).forEach(k => { const x = document.createElement("button"); x.type = "button"; x.className = "sec"; x.textContent = "↩ " + tt(UNDO[k] || k);
      x.onclick = () => doFix("undo:" + k, "tc-q-undo"); u.appendChild(x); });
    $i("tc-logw").hidden = !(r.log || []).length; $i("tc-log").textContent = (r.log || []).join("\n");
    const dot = $i("d-thcheck"); if (dot) dot.className = "tdot " + (bad ? "bad" : "ok");
    if (!$i("tc-msg").textContent.startsWith("✓")) say(bad ? "❌ " + bad + " " + tt("problems found") : "✅ " + tt("everything fine"));
  }
  function run() { say("⏳ " + tt("checking… (about 5 s)")); return req("GET").then(paint); }
  $i("tc-run").onclick = run;
  $i("tc-copy").onclick = () => { const done = () => say("📋 " + tt("Report copied"));
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(REP).then(done, () => fb()); else fb();
    function fb() { const a = document.createElement("textarea"); a.value = REP; document.body.appendChild(a); a.select(); try { document.execCommand("copy"); done(); } catch (e) {} a.remove(); } };
  if (navigator.share) { $i("tc-share").hidden = false; $i("tc-share").onclick = () => navigator.share({title: "MoveEye", text: REP}).catch(() => {}); }
  $i("tc-restart").onclick = () => doFix("restart", "tc-q-restart");
  $i("tc-reboot").onclick = () => doFix("reboot", "tc-q-reboot");
  const sec = $i("c-thcheck"); let once = false;
  new MutationObserver(() => { if (!sec.hidden && !once) { once = true; run(); } }).observe(sec, {attributes: true, attributeFilter: ["hidden"]});
})();
'''
_HX_TC = {
    "Check the thermal camera": ("Wärmebild prüfen und reparieren", "Vérifier et réparer la caméra thermique", "Controllare e riparare la termocamera", "Controllar e reparar la camera termica"),
    "and repair: SPI, I2C, driver, pins": ("SPI, I2C, Treiber, Pins", "SPI, I2C, pilote, broches", "SPI, I2C, driver, pin", "SPI, I2C, driver, pins"),
    "Check": ("Prüfen", "Vérifier", "Controllare", "Controllar"),
    "tc-note": ("MoveEye prüft der Reihe nach, was das Wärmebild braucht, und zeigt bei jedem Schritt ✅ oder ❌ mit dem Grund. Wo es geht, repariert ein Knopf den Fehler (mit Rückfrage, rückgängig machbar). Der Bericht enthält keine Passwörter.",
                "MoveEye vérifie dans l’ordre ce dont l’image thermique a besoin et affiche ✅ ou ❌ avec la raison pour chaque étape. Si possible, un bouton répare l’erreur (avec confirmation, annulable). Le rapport ne contient aucun mot de passe.",
                "MoveEye controlla in ordine ciò che serve all’immagine termica e mostra per ogni passo ✅ o ❌ con il motivo. Dove possibile, un pulsante ripara l’errore (con conferma, annullabile). Il rapporto non contiene password.",
                "MoveEye controllescha a la retscha tge che il maletg termic dovra e mussa per mintga pass ✅ u ❌ cun il motiv. Nua ch’i va, repara in buttun la sbaglia (cun dumonda, revocabel). Il rapport na cuntegna nagins pleds-clav."),
    "Log (camera / thermal)": ("Protokoll (Kamera / Wärmebild)", "Journal (caméra / thermique)", "Registro (camera / termica)", "Protocol (camera / termic)"),
    "Copy the report": ("Bericht kopieren", "Copier le rapport", "Copiare il rapporto", "Copiar il rapport"),
    "Share": ("Teilen", "Partager", "Condividere", "Parter"),
    "Restart MoveEye": ("MoveEye neu starten", "Redémarrer MoveEye", "Riavviare MoveEye", "Reaviar MoveEye"),
    "Restart the Pi": ("Pi neu starten", "Redémarrer le Pi", "Riavviare il Pi", "Reaviar il Pi"),
    "Add the missing lines to config.txt (a backup is kept)": ("Fehlende Zeilen in config.txt ergänzen (mit Sicherung)", "Ajouter les lignes manquantes à config.txt (avec sauvegarde)", "Aggiungere le righe mancanti a config.txt (con copia)", "Agiuntar las lingias che mancan en config.txt (cun copia)"),
    "Make pysenxor visible for MoveEye": ("pysenxor für MoveEye sichtbar machen", "Rendre pysenxor visible pour MoveEye", "Rendere pysenxor visibile per MoveEye", "Render pysenxor visibel per MoveEye"),
    "Install the missing system packages": ("Fehlende Systempakete installieren", "Installer les paquets système manquants", "Installare i pacchetti di sistema mancanti", "Installar ils pachets dal sistem che mancan"),
    "Remove the pip packages that cover the system": ("pip-Pakete entfernen, die das System überdecken", "Supprimer les paquets pip qui masquent le système", "Rimuovere i pacchetti pip che coprono il sistema", "Allontanar ils pachets pip che cuvran il sistem"),
    "Undo: config.txt back": ("Rückgängig: config.txt zurück", "Annuler : remettre config.txt", "Annulla: ripristinare config.txt", "Revocar: config.txt enavos"),
    "Undo: pysenxor link away": ("Rückgängig: pysenxor-Verweis weg", "Annuler : retirer le lien pysenxor", "Annulla: togliere il collegamento pysenxor", "Revocar: allontanar la colliaziun pysenxor"),
    "Undo: pip packages back": ("Rückgängig: pip-Pakete zurück", "Annuler : remettre les paquets pip", "Annulla: ripristinare i pacchetti pip", "Revocar: pachets pip enavos"),
    "tc-q-overlay": ("config.txt ändern? MoveEye legt zuerst eine Sicherung an. Danach muss der Pi neu starten.", "Modifier config.txt ? MoveEye fait d’abord une sauvegarde. Ensuite le Pi doit redémarrer.", "Modificare config.txt? MoveEye fa prima una copia. Poi il Pi deve riavviarsi.", "Midar config.txt? MoveEye fa l’emprim ina copia. Lura sto il Pi reaviar."),
    "tc-q-senxor": ("pysenxor aus dem gefundenen Ordner übernehmen? Danach MoveEye neu starten.", "Reprendre pysenxor du dossier trouvé ? Ensuite redémarrer MoveEye.", "Prendere pysenxor dalla cartella trovata? Poi riavviare MoveEye.", "Surprender pysenxor ord l’ordinatur chattà? Lura reaviar MoveEye."),
    "tc-q-apt": ("Fehlende Systempakete mit apt installieren (braucht Internet)?", "Installer les paquets manquants avec apt (Internet nécessaire) ?", "Installare i pacchetti mancanti con apt (serve Internet)?", "Installar ils pachets che mancan cun apt (dovra internet)?"),
    "tc-q-pip": ("Die pip-Pakete entfernen, damit die Systempakete wieder gelten? Rückgängig installiert dieselben Versionen wieder (braucht Internet).", "Supprimer les paquets pip pour que les paquets système s’appliquent de nouveau ? Annuler réinstalle les mêmes versions (Internet nécessaire).", "Rimuovere i pacchetti pip perché valgano di nuovo quelli di sistema? Annulla reinstalla le stesse versioni (serve Internet).", "Allontanar ils pachets pip per che ils pachets dal sistem valian puspè? Revocar installescha las medemas versiuns (dovra internet)."),
    "tc-q-undo": ("Diese Reparatur rückgängig machen?", "Annuler cette réparation ?", "Annullare questa riparazione?", "Revocar questa reparatura?"),
    "tc-q-restart": ("MoveEye jetzt neu starten?", "Redémarrer MoveEye maintenant ?", "Riavviare MoveEye adesso?", "Reaviar MoveEye ussa?"),
    "tc-q-reboot": ("Den Pi jetzt neu starten?", "Redémarrer le Pi maintenant ?", "Riavviare il Pi adesso?", "Reaviar il Pi ussa?"),
    "working…": ("läuft …", "en cours…", "in corso…", "en lavur…"),
    "problems found": ("Probleme gefunden", "problèmes trouvés", "problemi trovati", "problems chattads"),
    "everything fine": ("alles in Ordnung", "tout est en ordre", "tutto in ordine", "tut en urden"),
    "checking… (about 5 s)": ("prüfe … (etwa 5 s)", "vérification… (environ 5 s)", "controllo… (circa 5 s)", "controll… (circa 5 s)"),
    "Report copied": ("Bericht kopiert", "Rapport copié", "Rapporto copiato", "Rapport copià"),
    "Thermal camera chosen": ("Wärmebildkamera gewählt", "Caméra thermique choisie", "Termocamera scelta", "Camera termica tschernida"),
    "config.txt: SPI, I2C and dtoverlay=spi0-0cs": ("config.txt: SPI, I2C und dtoverlay=spi0-0cs", "config.txt : SPI, I2C et dtoverlay=spi0-0cs", "config.txt: SPI, I2C e dtoverlay=spi0-0cs", "config.txt: SPI, I2C e dtoverlay=spi0-0cs"),
    "not found (not a Raspberry Pi?)": ("nicht gefunden (kein Raspberry Pi?)", "introuvable (pas un Raspberry Pi ?)", "non trovato (non è un Raspberry Pi?)", "betg chattà (nagin Raspberry Pi?)"),
    "SPI device /dev/spidev0.0": ("SPI-Gerät /dev/spidev0.0", "Périphérique SPI /dev/spidev0.0", "Dispositivo SPI /dev/spidev0.0", "Apparat SPI /dev/spidev0.0"),
    "GPIO 7 belongs to the SPI driver": ("GPIO 7 gehört dem SPI-Treiber", "Le GPIO 7 appartient au pilote SPI", "Il GPIO 7 appartiene al driver SPI", "GPIO 7 appartegna al driver SPI"),
    "I2C bus /dev/i2c-1": ("I2C-Bus /dev/i2c-1", "Bus I2C /dev/i2c-1", "Bus I2C /dev/i2c-1", "Bus I2C /dev/i2c-1"),
    "Groups of the MoveEye user": ("Gruppen des MoveEye-Benutzers", "Groupes de l’utilisateur MoveEye", "Gruppi dell’utente MoveEye", "Gruppas da l’utilisader MoveEye"),
    "I2C scan": ("I2C-Suche", "Recherche I2C", "Ricerca I2C", "Tschertga I2C"),
    "I2C scan: thermal camera on 0x40": ("I2C-Suche: Wärmebildkamera auf 0x40", "Recherche I2C : caméra thermique sur 0x40", "Ricerca I2C: termocamera su 0x40", "Tschertga I2C: camera termica sin 0x40"),
    "thermal camera": ("Wärmebildkamera", "caméra thermique", "termocamera", "camera termica"),
    "nothing answers": ("nichts antwortet", "rien ne répond", "nessuno risponde", "nagut na respunda"),
    "Python packages": ("Python-Pakete", "Paquets Python", "Pacchetti Python", "Pachets Python"),
    "numpy, OpenCV and picamera2 (own process)": ("numpy, OpenCV und picamera2 (eigener Prozess)", "numpy, OpenCV et picamera2 (processus séparé)", "numpy, OpenCV e picamera2 (processo separato)", "numpy, OpenCV e picamera2 (agen process)"),
    "pip packages cover the system packages": ("pip-Pakete überdecken die Systempakete", "des paquets pip masquent les paquets système", "pacchetti pip coprono quelli di sistema", "pachets pip cuvran ils pachets dal sistem"),
    "Driver pysenxor for MoveEye's Python": ("Treiber pysenxor für MoveEyes Python", "Pilote pysenxor pour le Python de MoveEye", "Driver pysenxor per il Python di MoveEye", "Driver pysenxor per il Python da MoveEye"),
    "found, but only in": ("gefunden, aber nur in", "trouvé, mais seulement dans", "trovato, ma solo in", "chattà, ma mo en"),
    "not found in the home folder": ("im Benutzerordner nicht gefunden", "introuvable dans le dossier personnel", "non trovato nella cartella utente", "betg chattà en l’ordinatur da l’utilisader"),
    "System packages spidev, smbus, crcmod, gpiozero, lgpio": ("Systempakete spidev, smbus, crcmod, gpiozero, lgpio", "Paquets système spidev, smbus, crcmod, gpiozero, lgpio", "Pacchetti di sistema spidev, smbus, crcmod, gpiozero, lgpio", "Pachets dal sistem spidev, smbus, crcmod, gpiozero, lgpio"),
    "missing": ("fehlt", "manque", "manca", "manca"),
    "Pins CS / nRESET / D_READY": ("Pins CS / nRESET / D_READY", "Broches CS / nRESET / D_READY", "Pin CS / nRESET / D_READY", "Pins CS / nRESET / D_READY"),
    "Module answers (ID, firmware)": ("Modul antwortet (ID, Firmware)", "Le module répond (ID, micrologiciel)", "Il modulo risponde (ID, firmware)", "Il modul respunda (ID, firmware)"),
    "not tried yet": ("noch nicht versucht", "pas encore essayé", "non ancora provato", "anc betg empruvà"),
    "Head camera delivers pictures": ("Kopfkamera liefert Bilder", "La caméra de tête fournit des images", "La camera della testa fornisce immagini", "La camera dal chau furnescha maletgs"),
    "loop": ("Schleife", "boucle", "ciclo", "cirquit"),
    "Thermal picture arrives (picture rate)": ("Wärmebild kommt an (Bildrate)", "L’image thermique arrive (cadence)", "L’immagine termica arriva (frequenza)", "Il maletg termic arriva (frequenza)"),
    "pictures/s": ("Bilder/s", "images/s", "immagini/s", "maletgs/s"),
    "last picture": ("letztes Bild vor", "dernière image il y a", "ultima immagine", "ultim maletg avant"),
    "config.txt not found": ("config.txt nicht gefunden", "config.txt introuvable", "config.txt non trovato", "config.txt betg chattà"),
    "nothing to do": ("nichts zu tun", "rien à faire", "niente da fare", "nagut da far"),
    "no permission (sudo)": ("keine Berechtigung (sudo)", "pas d’autorisation (sudo)", "nessuna autorizzazione (sudo)", "nagin permiss (sudo)"),
    "config.txt completed - restart the Pi so that it takes effect": ("config.txt ergänzt – den Pi neu starten, damit es gilt", "config.txt complété – redémarrer le Pi pour l’appliquer", "config.txt completato – riavviare il Pi perché valga", "config.txt cumplettà – reaviar il Pi per che quai valia"),
    "pysenxor not found in the home folder": ("pysenxor im Benutzerordner nicht gefunden", "pysenxor introuvable dans le dossier personnel", "pysenxor non trovato nella cartella utente", "pysenxor betg chattà en l’ordinatur da l’utilisader"),
    "the user folder of Python is switched off": ("der Benutzerordner von Python ist ausgeschaltet", "le dossier utilisateur de Python est désactivé", "la cartella utente di Python è disattivata", "l’ordinatur d’utilisader da Python è deactivà"),
    "pysenxor is now visible for MoveEye - restart MoveEye": ("pysenxor ist jetzt für MoveEye sichtbar – MoveEye neu starten", "pysenxor est maintenant visible pour MoveEye – redémarrer MoveEye", "pysenxor ora è visibile per MoveEye – riavviare MoveEye", "pysenxor è ussa visibel per MoveEye – reaviar MoveEye"),
    "removed - the system packages apply again; restart MoveEye": ("entfernt – die Systempakete gelten wieder; MoveEye neu starten", "supprimés – les paquets système s’appliquent de nouveau ; redémarrer MoveEye", "rimossi – valgono di nuovo i pacchetti di sistema; riavviare MoveEye", "allontanads – ils pachets dal sistem valan puspè; reaviar MoveEye"),
    "the Pi restarts": ("der Pi startet neu", "le Pi redémarre", "il Pi si riavvia", "il Pi reavia"),
    "MoveEye restarts": ("MoveEye startet neu", "MoveEye redémarre", "MoveEye si riavvia", "MoveEye reavia"),
    "nothing to undo": ("nichts rückgängig zu machen", "rien à annuler", "niente da annullare", "nagut da revocar"),
    "undone - restart so that it takes effect": ("rückgängig gemacht – neu starten, damit es gilt", "annulé – redémarrer pour l’appliquer", "annullato – riavviare perché valga", "revocà – reaviar per che quai valia"),
    "busy - please wait": ("beschäftigt – bitte warten", "occupé – veuillez patienter", "occupato – attendere", "occupà – per plaschair spetgar"),
    "standard": ("Standard", "standard", "standard", "standard"),
    "Thermal-90: CS / SS (chip select) GPIO": ("Thermal-90: CS / SS (Chip-Select) GPIO", "Thermal-90 : GPIO CS / SS (sélection de puce)", "Thermal-90: GPIO CS / SS (chip select)", "Thermal-90: GPIO CS / SS (chip select)"),
    "Thermal-90: nRESET GPIO": ("Thermal-90: nRESET GPIO", "Thermal-90 : GPIO nRESET", "Thermal-90: GPIO nRESET", "Thermal-90: GPIO nRESET"),
    "Thermal-90: D_READY (data ready) GPIO": ("Thermal-90: D_READY (Daten bereit) GPIO", "Thermal-90 : GPIO D_READY (données prêtes)", "Thermal-90: GPIO D_READY (dati pronti)", "Thermal-90: GPIO D_READY (datas prontas)"),
    "Check the thermal camera …": ("Wärmebild prüfen …", "Vérifier la caméra thermique …", "Controllare la termocamera …", "Controllar la camera termica …"),
    "no thermal picture": ("kein Wärmebild", "pas d’image thermique", "nessuna immagine termica", "nagin maletg termic"),
}
for _k, _v in _HX_TC.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
SET_HELP["senxor_cs"] = ("Where SS / CS of the Waveshare thermal camera is wired. Waveshare (HAT and single module): GPIO 7 (pin 26) - "
                         "then config.txt needs dtoverlay=spi0-0cs. nRESET: GPIO 23 (pin 16), D_READY: GPIO 24 (pin 18).", "GPIO 7.")
_HX_TC_HELP = {SET_HELP["senxor_cs"][0]: (
    "Wo SS / CS der Waveshare-Wärmebildkamera angeschlossen ist. Waveshare (HAT und Einzelmodul): GPIO 7 (Pin 26) – dann braucht "
    "config.txt dtoverlay=spi0-0cs. nRESET: GPIO 23 (Pin 16), D_READY: GPIO 24 (Pin 18).",
    "Où SS / CS de la caméra thermique Waveshare est branché. Waveshare (HAT et module seul) : GPIO 7 (broche 26) – config.txt a alors "
    "besoin de dtoverlay=spi0-0cs. nRESET : GPIO 23 (broche 16), D_READY : GPIO 24 (broche 18).",
    "Dove è collegato SS / CS della termocamera Waveshare. Waveshare (HAT e modulo singolo): GPIO 7 (pin 26) – allora config.txt "
    "richiede dtoverlay=spi0-0cs. nRESET: GPIO 23 (pin 16), D_READY: GPIO 24 (pin 18).",
    "Nua che SS / CS da la camera termica Waveshare è colliada. Waveshare (HAT e modul singul): GPIO 7 (pin 26) – lura dovra "
    "config.txt dtoverlay=spi0-0cs. nRESET: GPIO 23 (pin 16), D_READY: GPIO 24 (pin 18)."), "GPIO 7.": ("GPIO 7.", "GPIO 7.", "GPIO 7.", "GPIO 7.")}
for _k, _v in _HX_TC_HELP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
if 'data-k="thcheck"' not in TOOLS_PAGE and '<a class="tli" data-k="servo"' in TOOLS_PAGE:
    TOOLS_PAGE = TOOLS_PAGE.replace('<a class="tli" data-k="servo"', TC_TOOL_HTML + '<a class="tli" data-k="servo"', 1)
    TOOLS_PAGE = TOOLS_PAGE.replace('  <section class="tool" id="c-diag"', TC_SECTION_HTML + '  <section class="tool" id="c-diag"', 1)
    TOOLS_PAGE = TOOLS_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps({k: v[0] for k, v in _HX_TC.items()}, ensure_ascii=False)
                                    + ");</script><script>" + TC_PAGE_JS + "</script></body>", 1)


# ---- the window (Tkinter): the same check as text, the repairs on the web page ------------------------------------------
def _tc_tk_win(app):
    win = getattr(app, "_tc_w", None)
    try:
        if win is not None and win.winfo_exists():
            win.lift(); return
    except Exception:
        pass
    win = tk.Toplevel(app.root); app._tc_w = win
    win.title("MoveEye – " + tr("Check the thermal camera")); win.geometry("640x560")
    txt = tk.Text(win, wrap="word"); txt.pack(fill="both", expand=True, padx=8, pady=8)
    bar = ttk.Frame(win); bar.pack(fill="x", padx=8, pady=(0, 8))

    def show(s):
        try:
            txt.delete("1.0", "end"); txt.insert("1.0", s)
        except Exception:
            pass

    def run():
        show(tr("checking… (about 5 s)"))

        def work():
            try:
                r = thermal_check()
                s = r["report"] + "\n\n" + tr("Repairs: More → Tools → «Check the thermal camera» on the web page.")
            except Exception as e:
                s = f"{type(e).__name__}: {e}"
            try:
                win.after(0, lambda: show(s))
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()

    def copy():
        try:
            win.clipboard_clear(); win.clipboard_append(txt.get("1.0", "end"))
        except Exception:
            pass
    ttk.Button(bar, text=tr("Check"), command=run).pack(side="left")
    ttk.Button(bar, text=tr("Copy the report"), command=copy).pack(side="left", padx=6)
    run()


_HX_TC["Repairs: More → Tools → «Check the thermal camera» on the web page."] = (
    "Reparaturen: auf der Webseite Mehr → Werkzeuge → «Wärmebild prüfen und reparieren».",
    "Réparations : sur la page web Plus → Outils → «Vérifier et réparer la caméra thermique».",
    "Riparazioni: sulla pagina web Altro → Strumenti → «Controllare e riparare la termocamera».",
    "Reparaturas: sin la pagina web Dapli → Utensils → «Controllar e reparar la camera termica».")
for _k in ("Repairs: More → Tools → «Check the thermal camera» on the web page.",):
    DE.setdefault(_k, _HX_TC[_k][0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _HX_TC[_k][_i + 1])
_tc_tk_build_section_base = App._build_section


def _tc_tk_build_section(self, sec, sbody, settings_parent=None):
    _tc_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec == "Thermal camera":
        try:
            ttk.Button(sbody, text="🩺 " + tr("Check the thermal camera …"), command=lambda: _tc_tk_win(self)).pack(fill="x", pady=(6, 0))
        except Exception as e:
            log_event("sys", f"Window: thermal check button: {e}"[:160])


# wraps: App._build_section (the button «Check the thermal camera» in the section Thermal camera)
App._build_section = _tc_tk_build_section


def thermal_check_selftest():
    """config.txt lines, explanations of the start errors, pins, the check runs without hardware, the tools page has the entry"""
    t = "# x\ndtparam=audio=on\n#dtparam=spi=on\n"
    f = tc_config_flags(t)
    assert not f["spi"] and not f["spi0_0cs"] and not f["i2c"], f
    n = tc_config_fixed(t)
    assert tc_config_flags(n) == {"spi": True, "i2c": True, "spi0_0cs": True}, n
    t2 = "[all]\ndtparam=spi=on\ndtparam=i2c_arm=on\n"
    n2 = tc_config_fixed(t2)
    assert n2.splitlines()[2].startswith("dtoverlay=spi0-0cs"), n2
    assert tc_config_fixed(n2) is None
    assert "dtoverlay=spi0-0cs" in senxor_explain("gpio", "BCM7 busy: GPIO busy", (7, 23, 24))
    assert "SPI is off" in senxor_explain("spi", FileNotFoundError(2, "No such file or directory", "/dev/spidev0.0"))
    assert "0x40" in senxor_explain("module", OSError(121, "Remote I/O error"))
    assert "DATA READY (GPIO 24)" in senxor_explain("frame", "no DATA READY", (7, 23, 24))
    keep = {k: CFG.get(k) for k in SENXOR_PIN_DEF}
    try:
        CFG["senxor_cs"] = "8"; CFG["senxor_drdy"] = "x"
        assert senxor_pins() == (8, 23, 24)
        assert "senxor_cs" in TEXT_SPECS and any(p[0] == "8" for p in text_choice_pairs("senxor_cs"))
    finally:
        CFG.update(keep)
    assert 'data-k="thcheck"' in TOOLS_PAGE and 'id="c-thcheck"' in TOOLS_PAGE
    for k in _HX_TC:
        assert all(_HX_TC[k]), k
    return True


SELFTEST_EXTRA.append(("Thermal camera check: config.txt, start errors in clear words, pins, tools page (639zzzzzx)", thermal_check_selftest))
