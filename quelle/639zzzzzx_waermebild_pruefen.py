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
                 fix="senxor" if venvs else "senxor_install", lang=lang)
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
            _tc_step(steps, "module", False, "Module answers (ID, firmware)", f"{L.get('step')}: " + thermal_status_tr(L.get("err"), lang), lang=lang)
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
             thermal_status_tr(st, lang) + (f" · {fps:.1f} " + tr("pictures/s", lang) if fps or st == "connected" else "")
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
    return [k for k in ("overlay", "senxor", "senxor_install", "pip") if d.get(k)]


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
    if action == "senxor_install":
        return tc_senxor_install(lang)
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
        elif what == "senxor_install":
            ok_, msg_ = tc_senxor_uninstall(x)
            if not ok_:
                return False, msg_
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

# ---- «Install driver» (4.25.x, Besitzer: «no picture: Waveshare driver missing (pysenxor)» on the real Pi; he types nothing) ----
# Source: the Waveshare wiki «Thermal Camera HAT» / «Thermal-Camera-Module», section Raspberry Pi Bookworm: demo
#   https://files.waveshare.com/wiki/common/Thermal_Camera_Hat.zip -> pysenxor-master (the Meridian MI48 driver «senxor»).
#   Waveshare publishes no checksum and no version; there is no official git repository with tags. So: only exactly this
#   address, only HTTPS with a checked certificate, no redirect to another host, at most 150 MB; the SHA-256 is written to the
#   log and kept in the undo note (TC_SENXOR_SHA256 = a fixed value would be checked - empty = not pinned, said in the report).
#   From the ZIP only the package folder senxor/ (*.py and data, no setup.py, nothing is run) goes to DATA_DIR/treiber/pysenxor;
#   a .pth in the user folder of Python + 080 senxor_driver_path() make it visible; NO pip (Bookworm: numpy / OpenCV from apt
#   only - pip numpy breaks picamera2). Dependencies only from apt (python3-numpy, -spidev, -smbus, -crcmod, -gpiozero, -lgpio,
#   -serial; more when the import names one, TC_APT_MAP). Undo = the .pth and the folder away.
TC_SENXOR_URL = "https://files.waveshare.com/wiki/common/Thermal_Camera_Hat.zip"
TC_SENXOR_HOST = "files.waveshare.com"
TC_SENXOR_SHA256 = ""                                    # Waveshare gives none: not pinned (the report says so)
TC_SENXOR_MAX = 150 * 1024 * 1024
TC_PTH2 = "moveeye-pysenxor-treiber.pth"
TC_APT_MAP = {"numpy": "python3-numpy", "spidev": "python3-spidev", "smbus": "python3-smbus", "smbus2": "python3-smbus2",
              "crcmod": "python3-crcmod", "gpiozero": "python3-gpiozero", "lgpio": "python3-lgpio", "serial": "python3-serial",
              "cv2": "python3-opencv", "matplotlib": "python3-matplotlib", "scipy": "python3-scipy", "PIL": "python3-pil",
              "imageio": "python3-imageio", "yaml": "python3-yaml", "usb": "python3-usb"}
TC_SENXOR_PROBE = r"""
import json, sys
out = {}
for n in ("numpy", "spidev", "smbus", "smbus2", "crcmod", "gpiozero", "lgpio", "serial"):
    try:
        __import__(n); out[n] = True
    except BaseException:
        out[n] = False
try:
    import senxor, senxor.mi48, senxor.interfaces
    out["senxor"] = str(getattr(senxor, "__file__", "") or "?")
except ModuleNotFoundError as e:
    out["senxor"] = False; out["missing"] = str(getattr(e, "name", "") or "")
except BaseException as e:
    out["senxor"] = False; out["err"] = (type(e).__name__ + ": " + str(e))[:160]
print(json.dumps(out))
"""


def tc_job_view(lang=None):
    j = dict(TC.get("job") or {})
    j["lines"] = list(j.get("lines") or [])
    return j


def _tc_say(line):
    j = TC.get("job")
    if isinstance(j, dict) and j.get("state") == "running":
        j.setdefault("lines", []).append(str(line)[:300])


def _tc_senxor_url():
    """the one official address; tests may name a local server (MW_TEST_SENXOR_URL, only http://127.0.0.1)"""
    t_ = os.environ.get("MW_TEST_SENXOR_URL") or ""
    if t_.startswith("http://127.0.0.1:"):
        return t_, True
    return TC_SENXOR_URL, False


class _TcNoOtherHost(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import urlsplit
        u = urlsplit(newurl)
        if u.scheme != "https" or u.hostname != TC_SENXOR_HOST:
            raise urllib.error.URLError("redirect to another address refused: " + newurl[:120])
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def tc_senxor_download(dest, lang=None):
    """-> (ok, sha256 or error). HTTPS with the system certificates, exactly TC_SENXOR_URL, size limit"""
    import ssl
    from urllib.parse import urlsplit
    url, test = _tc_senxor_url()
    u = urlsplit(url)
    if not test and (u.scheme != "https" or u.hostname != TC_SENXOR_HOST):
        return False, "address not allowed"
    hs = [urllib.request.HTTPSHandler(context=ssl.create_default_context()), _TcNoOtherHost()]
    if test:
        hs.append(urllib.request.ProxyHandler({}))
    op = urllib.request.build_opener(*hs)
    h = hashlib.sha256(); n = 0
    try:
        with op.open(urllib.request.Request(url, headers={"User-Agent": "MoveEye/" + APP_VERSION}), timeout=60) as r, open(dest, "wb") as f:
            fu = urlsplit(r.geturl())
            if not test and (fu.scheme != "https" or fu.hostname != TC_SENXOR_HOST):
                return False, "redirect to another address refused"
            while True:
                c = r.read(256 * 1024)
                if not c:
                    break
                n += len(c)
                if n > TC_SENXOR_MAX:
                    return False, tr("the download is too big", lang)
                h.update(c); f.write(c)
    except Exception as e:
        return False, tr("download failed", lang) + f": {type(e).__name__}: {e}"[:200]
    dig = h.hexdigest()
    if TC_SENXOR_SHA256 and dig != TC_SENXOR_SHA256:
        return False, tr("the checksum does not match", lang) + ": " + dig[:16] + "…"
    _tc_say(f"✓ {tr('downloaded', lang)}: {n // 1024} KiB · SHA-256 {dig}")
    return True, dig


def _tc_zip_find(zf):
    """the prefix of the folder senxor/ in a ZIP (the one with mi48.py, pysenxor-master preferred) or None"""
    names = [i.filename.replace("\\", "/") for i in zf.infolist()]
    cands = [n[:-len("senxor/__init__.py")] for n in names if n.endswith("senxor/__init__.py")
             and (n == "senxor/__init__.py" or n.endswith("/senxor/__init__.py"))]
    cands = [c for c in cands if c + "senxor/mi48.py" in names]
    cands.sort(key=lambda c: (0 if "pysenxor" in c.lower() else 1, len(c)))
    return cands[0] if cands else None


def tc_senxor_unpack(zpath, target, lang=None):
    """only the package senxor/ from the ZIP (or from a ZIP inside it) to target/senxor; safe names, regular files, 30 MB"""
    import io
    zf = zipfile.ZipFile(zpath)
    pre = _tc_zip_find(zf)
    if pre is None:
        for i in zf.infolist():
            if i.filename.lower().endswith(".zip") and i.file_size < 80 * 1024 * 1024:
                try:
                    inner = zipfile.ZipFile(io.BytesIO(zf.read(i)))
                except (zipfile.BadZipFile, OSError):
                    continue
                p_ = _tc_zip_find(inner)
                if p_ is not None:
                    zf, pre = inner, p_; break
    if pre is None:
        return False, tr("no folder senxor (pysenxor) in the download", lang)
    base = pre + "senxor/"; total = 0; nfiles = 0
    os.makedirs(os.path.join(target, "senxor"), exist_ok=True)
    for i in zf.infolist():
        n = i.filename.replace("\\", "/")
        if not n.startswith(base) or n.endswith("/") or "/__pycache__/" in n or n.endswith((".pyc", ".pyo")):
            continue
        rel = n[len(base):]
        parts = rel.split("/")
        if not rel or any(x in ("", ".", "..") for x in parts) or rel.startswith("/") or ":" in rel:
            continue
        if (i.external_attr >> 16) & 0o170000 not in (0, 0o100000):      # links or devices: never
            continue
        total += i.file_size
        if total > 30 * 1024 * 1024:
            return False, tr("the download is too big", lang)
        out = os.path.join(target, "senxor", *parts)
        if not os.path.realpath(out).startswith(os.path.realpath(target) + os.sep):
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with zf.open(i) as src_, open(out, "wb") as dst:
            shutil.copyfileobj(src_, dst)
        nfiles += 1
    if not os.path.isfile(os.path.join(target, "senxor", "mi48.py")):
        return False, tr("no folder senxor (pysenxor) in the download", lang)
    _tc_say(f"✓ {tr('unpacked', lang)}: senxor ({nfiles})")
    return True, pre.rstrip("/") or "/"


def _tc_apt(pk, lang=None):
    """apt-get install of the packages (tests: MW_TEST_APT_LOG writes the list instead) -> (ok, text)"""
    if not pk:
        return True, ""
    tl = os.environ.get("MW_TEST_APT_LOG")
    if tl:
        with open(tl, "a") as f:
            f.write(" ".join(pk) + "\n")
        return True, ""
    cmd = _tc_root(["apt-get", "install", "-y", "--no-install-recommends"] + list(pk))
    rc, o, e = _tc_run(cmd, 900)
    if rc != 0 and "Unable to locate package" in (e + o):
        _tc_run(_tc_root(["apt-get", "update"]), 600)
        rc, o, e = _tc_run(cmd, 900)
    log_event("sys", f"Thermal camera: apt install {' '.join(pk)} -> {rc}")
    if rc == 0:
        return True, ""
    return False, (tr("no permission (sudo)", lang) + ": " if "sudo" in e or "password" in e else "") + (e or o)[-200:]


def _tc_senxor_probe():
    rc, out, err = _tc_run([sys.executable, "-c", TC_SENXOR_PROBE], 60)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {"senxor": False, "err": (err or out or str(rc))[-200:]}


def tc_senxor_install(lang=None):
    """download -> unpack -> apt -> .pth -> import check -> thermal camera opened again. -> (ok, message)"""
    t0 = time.time()
    base = os.path.join(DATA_DIR, "treiber"); target = os.path.join(DATA_DIR, SENXOR_DRV_SUB)
    url, _test = _tc_senxor_url()
    os.makedirs(base, exist_ok=True)
    _tc_say(f"⏳ {tr('download', lang)}: {url}")
    dl = os.path.join(base, ".pysenxor-download.zip"); new = target + ".neu"
    try:
        ok, dig = tc_senxor_download(dl, lang)
        if not ok:
            return False, dig
        if os.path.isdir(new):
            shutil.rmtree(new)
        try:
            ok, where = tc_senxor_unpack(dl, new, lang)
        except (zipfile.BadZipFile, OSError) as e:
            ok, where = False, tr("the download is not a ZIP", lang) + f": {e}"[:120]
        if not ok:
            shutil.rmtree(new, ignore_errors=True)
            return False, where
        if os.path.isdir(target):
            shutil.rmtree(target)
        os.replace(new, target)
        _tc_say("→ " + target)
    finally:
        try:
            os.remove(dl)
        except OSError:
            pass
    # dependencies from apt only (never pip)
    pr = _tc_senxor_probe()
    want = ["numpy", "spidev", "crcmod", "gpiozero", "serial"]
    if os.path.exists("/proc/device-tree/model") or os.environ.get("MW_TEST_APT_LOG"):
        want.append("lgpio")                                # Pi 5: gpiozero needs lgpio
    pk = [TC_APT_MAP[n] for n in want if not pr.get(n)]
    if not (pr.get("smbus") or pr.get("smbus2")):
        pk.append("python3-smbus")
    apt_ok, apt_msg = _tc_apt(pk, lang)
    _tc_say(("✓ " + tr("system packages", lang) + ": " + (", ".join(pk) if pk else tr("all there", lang))) if apt_ok
            else ("⚠ " + tr("system packages", lang) + " (" + ", ".join(pk) + "): " + apt_msg))
    # visible for MoveEye's Python: .pth in the user folder (+ 080 senxor_driver_path for the running program)
    us = _tc_user_site(); pth = os.path.join(us, TC_PTH2) if us else ""
    if pth:
        try:
            os.makedirs(us, exist_ok=True)
            with open(pth, "w") as f:
                f.write(target + "\n")
        except OSError as e:
            pth = ""; _tc_say("⚠ .pth: " + str(e)[:120])
    d = _tc_undo_load()
    d["senxor_install"] = {"dir": target, "pth": pth, "url": url, "sha256": dig, "pinned": bool(TC_SENXOR_SHA256),
                           "from": where, "t": datetime.now().strftime("%Y-%m-%d %H:%M")}
    _tc_undo_save(d)
    log_event("sys", f"Thermal camera: pysenxor installed from {url} ({where}, SHA-256 {dig}"
                     + (", pinned" if TC_SENXOR_SHA256 else ", no fixed checksum from Waveshare") + f") -> {target}")
    # a package that the import still asks for: from apt, once
    pr = _tc_senxor_probe()
    if not pr.get("senxor") and pr.get("missing") in TC_APT_MAP:
        more = TC_APT_MAP[pr["missing"]]
        ok2, m2 = _tc_apt([more], lang)
        _tc_say(("✓ " if ok2 else "⚠ ") + tr("system packages", lang) + ": " + more + ("" if ok2 else " · " + m2))
        pr = _tc_senxor_probe()
    if pr.get("senxor"):
        _tc_say("✓ " + tr("Driver pysenxor for MoveEye's Python", lang) + ": " + str(pr["senxor"])[:120])
    else:
        _tc_say("⚠ " + tr("Driver pysenxor for MoveEye's Python", lang) + ": "
                + (("No module named '" + pr["missing"] + "'") if pr.get("missing") else str(pr.get("err") or "?")))
    # the running program: path, then open the thermal camera again and show what happens
    senxor_driver_path()
    try:
        import importlib
        importlib.invalidate_caches()
    except Exception:
        pass
    th = THERMAL
    if th is not None:
        th.last_err = None; th.retry_at = 0.0
    res = ""
    if str(CFG.get("thermal_source") or "").startswith("senxor") and th is not None:
        end = time.time() + 15.0
        while time.time() < end:
            st = str(STATE.get("thermal") or "")
            if float(SENXOR_LAST.get("t") or 0) > t0 and st not in ("connecting…", "") and not th.opening:
                if st == "connected" or time.time() > end - 9.0:
                    break
            time.sleep(0.5)
        res = str(STATE.get("thermal") or "")
        _tc_say(("✓ " if res == "connected" else "⚠ ") + tr("Thermal camera", lang) + ": " + thermal_status_tr(res, lang))
    note = "" if TC_SENXOR_SHA256 else " · " + tr("Waveshare publishes no checksum: loaded without a fixed checksum (SHA-256 in the log)", lang)
    if res == "connected":
        return True, tr("driver installed - the thermal camera is connected", lang) + note
    if pr.get("senxor"):
        return True, tr("driver installed", lang) + (" · " + thermal_status_tr(res, lang) if res else "") + note
    return False, tr("driver unpacked, but MoveEye's Python cannot load it yet", lang) + (" · " + apt_msg if not apt_ok else "")


def tc_senxor_uninstall(x):
    """undo of «Install driver»: the .pth and the folder DATA_DIR/treiber/pysenxor away (nothing else)"""
    base = os.path.realpath(os.path.join(DATA_DIR, "treiber")) + os.sep
    pth = x.get("pth") or ""
    try:
        if pth and os.path.basename(pth) == TC_PTH2 and os.path.isfile(pth):
            os.remove(pth)
        d_ = x.get("dir") or ""
        if d_ and os.path.realpath(d_).startswith(base) and os.path.isdir(d_):
            shutil.rmtree(d_)
        if d_ in sys.path:
            sys.path.remove(d_)
    except OSError as e:
        return False, str(e)[:160]
    log_event("sys", "Thermal camera: pysenxor of MoveEye removed (undo)")
    return True, ""



TC_ACTIONS = ("overlay", "senxor", "senxor_install", "apt", "pip", "reboot", "restart", "undo:overlay", "undo:senxor", "undo:senxor_install", "undo:pip")


def thermal_check_routes(app, reply, body):
    from flask import request, g

    @app.route("/api/thermal_check", methods=["GET", "POST"])
    def api_thermal_check():
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "GET" and request.args.get("job"):
            return reply({"ok": True, "job": tc_job_view(lang)})
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or lang); a = str(d.get("action") or "")
            if a not in TC_ACTIONS:
                return reply({"ok": False, "error": "unknown action"}, 400)
            if TC["busy"]:
                return reply({"ok": False, "error": tr("busy - please wait", lang)}, 409)
            if a == "senxor_install":                       # takes minutes (download, apt): in the background, the page asks ?job=1
                TC["busy"] = True
                TC["job"] = {"action": a, "state": "running", "ok": None, "msg": "", "lines": [], "t": time.time()}

                def work():
                    try:
                        ok_, msg_ = tc_fix(a, lang)
                    except Exception as e:
                        ok_, msg_ = False, f"{type(e).__name__}: {e}"[:200]
                    finally:
                        TC["busy"] = False
                    TC["job"].update(state="done", ok=bool(ok_), msg=msg_)
                threading.Thread(target=work, daemon=True).start()
                return reply({"ok": True, "started": True, "msg": tr("working…", lang)})
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
    <div id="tc-msg" class="mut" style="margin:6px 0;white-space:pre-wrap"></div>
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
               senxor_install: ["Install driver", "tc-q-install"],
               apt: ["Install the missing system packages", "tc-q-apt"],
               pip: ["Remove the pip packages that cover the system", "tc-q-pip"]};
  const UNDO = {overlay: "Undo: config.txt back", senxor: "Undo: pysenxor link away", senxor_install: "Undo: remove the installed driver", pip: "Undo: pip packages back"};
  let REP = "";
  const say = s => { $i("tc-msg").textContent = s || ""; };
  const req = (m, b) => fetch("/api/thermal_check?lang=" + L(), m === "GET" ? {cache: "no-store"} :
      {method: "POST", headers: {"Content-Type": "application/json", "X-Requested-With": "mw"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))})
    .then(r => r.json()).catch(e => ({ok: false, error: String(e)}));
  function doFix(a, q) {
    if (q && !confirm(tt(q))) return;
    say("⏳ " + tt("working…"));
    req("POST", {action: a}).then(r => {
      if (r.started) { const poll = () => fetch("/api/thermal_check?job=1&lang=" + L(), {cache: "no-store"}).then(x => x.json()).catch(() => ({})).then(j => {
          const jb = (j && j.job) || {}; say("⏳ " + tt("working…") + "\n" + (jb.lines || []).join("\n"));
          if (jb.state === "running") { setTimeout(poll, 2000); return; }
          const tail = (jb.lines || []).join("\n"); run().then(() => say((jb.ok ? "✓ " : "⚠ ") + (jb.msg || "") + (tail ? "\n" + tail : ""))); });
        setTimeout(poll, 1500); return; }
      say((r.ok ? "✓ " : "⚠ ") + (r.msg || r.error || "")); if (a !== "reboot" && a !== "restart") setTimeout(run, 400); });
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
_HX_TC.update({
    "Install driver": ("Treiber installieren", "Installer le pilote", "Installare il driver", "Installar il driver"),
    "Check and repair": ("Prüfen und reparieren", "Vérifier et réparer", "Controllare e riparare", "Controllar e reparar"),
    "Undo: remove the installed driver": ("Rückgängig: installierten Treiber entfernen", "Annuler : retirer le pilote installé", "Annulla: rimuovere il driver installato", "Revocar: allontanar il driver installà"),
    "tc-q-install": ("Den Waveshare-Treiber pysenxor jetzt auf dem Pi installieren? MoveEye lädt ihn von der offiziellen Waveshare-Seite (files.waveshare.com) und installiert fehlende Systempakete mit apt. Braucht Internet, rückgängig machbar.",
                     "Installer maintenant le pilote Waveshare pysenxor sur le Pi ? MoveEye le télécharge depuis le site officiel de Waveshare (files.waveshare.com) et installe les paquets système manquants avec apt. Internet nécessaire, annulable.",
                     "Installare ora il driver Waveshare pysenxor sul Pi? MoveEye lo scarica dal sito ufficiale di Waveshare (files.waveshare.com) e installa con apt i pacchetti di sistema mancanti. Serve Internet, annullabile.",
                     "Installar ussa il driver Waveshare pysenxor sin il Pi? MoveEye al chargia giu da la pagina uffiziala da Waveshare (files.waveshare.com) ed installescha ils pachets dal sistem che mancan cun apt. Dovra internet, revocabel."),
    "download": ("Herunterladen", "Téléchargement", "Download", "Chargiar giu"),
    "downloaded": ("heruntergeladen", "téléchargé", "scaricato", "chargià giu"),
    "download failed": ("Herunterladen fehlgeschlagen", "échec du téléchargement", "download non riuscito", "chargiar giu n’è betg reussì"),
    "the download is too big": ("der Download ist zu gross", "le téléchargement est trop volumineux", "il download è troppo grande", "la chargiada è memia gronda"),
    "the checksum does not match": ("die Prüfsumme stimmt nicht", "la somme de contrôle ne correspond pas", "il checksum non corrisponde", "la summa da controlla na correspunda betg"),
    "the download is not a ZIP": ("der Download ist kein ZIP", "le téléchargement n’est pas un ZIP", "il download non è uno ZIP", "la chargiada n’è nagin ZIP"),
    "no folder senxor (pysenxor) in the download": ("kein Ordner senxor (pysenxor) im Download", "pas de dossier senxor (pysenxor) dans le téléchargement", "nessuna cartella senxor (pysenxor) nel download", "nagin ordinatur senxor (pysenxor) en la chargiada"),
    "unpacked": ("entpackt", "décompressé", "estratto", "decumprimì"),
    "system packages": ("Systempakete", "paquets système", "pacchetti di sistema", "pachets dal sistem"),
    "all there": ("alle vorhanden", "tous présents", "tutti presenti", "tuts avant maun"),
    "Thermal camera": ("Wärmebildkamera", "Caméra thermique", "Termocamera", "Camera termica"),
    "Waveshare publishes no checksum: loaded without a fixed checksum (SHA-256 in the log)": (
        "Waveshare veröffentlicht keine Prüfsumme: ohne feste Prüfsumme geladen (SHA-256 im Protokoll)",
        "Waveshare ne publie pas de somme de contrôle : chargé sans somme fixe (SHA-256 dans le journal)",
        "Waveshare non pubblica un checksum: scaricato senza checksum fisso (SHA-256 nel registro)",
        "Waveshare na publitgescha nagina summa da controlla: chargià senza summa fixa (SHA-256 en il protocol)"),
    "driver installed - the thermal camera is connected": ("Treiber installiert – die Wärmebildkamera ist verbunden", "pilote installé – la caméra thermique est connectée", "driver installato – la termocamera è collegata", "driver installà – la camera termica è colliada"),
    "driver installed": ("Treiber installiert", "pilote installé", "driver installato", "driver installà"),
    "driver unpacked, but MoveEye's Python cannot load it yet": ("Treiber entpackt, aber MoveEyes Python kann ihn noch nicht laden", "pilote décompressé, mais le Python de MoveEye ne peut pas encore le charger", "driver estratto, ma il Python di MoveEye non riesce ancora a caricarlo", "driver decumprimì, ma il Python da MoveEye na po anc betg al chargiar"),
})
# the status texts of the Thermal-90 (080 SENXOR_TX, 230): same keys, placeholders stay
_HX_THX = {
    SENXOR_TX["driver"]: ("Waveshare-Treiber pysenxor fehlt ({e}) – «Treiber installieren» in den Wärmebild-Einstellungen installiert ihn",
                          "Le pilote Waveshare pysenxor manque ({e}) – «Installer le pilote» dans les réglages de la caméra thermique l’installe",
                          "Manca il driver Waveshare pysenxor ({e}) – «Installare il driver» nelle impostazioni della termocamera lo installa",
                          "Il driver Waveshare pysenxor manca ({e}) – «Installar il driver» en las configuraziuns da la camera termica al installescha"),
    SENXOR_TX["pkg"]: ("Systempaket {pkg} fehlt – «Wärmebild prüfen und reparieren» installiert es",
                       "Paquet système {pkg} manquant – «Vérifier et réparer la caméra thermique» l’installe",
                       "Manca il pacchetto di sistema {pkg} – «Controllare e riparare la termocamera» lo installa",
                       "Il pachet dal sistem {pkg} manca – «Controllar e reparar la camera termica» al installescha"),
    SENXOR_TX["gpio_cs"]: ("GPIO {cs} (CS) belegt: der SPI-Treiber hält ihn – config.txt braucht dtoverlay=spi0-0cs unter dtparam=spi=on, dann den Pi neu starten",
                           "GPIO {cs} (CS) occupé : le pilote SPI le tient – config.txt a besoin de dtoverlay=spi0-0cs sous dtparam=spi=on, puis redémarrer le Pi",
                           "GPIO {cs} (CS) occupato: lo tiene il driver SPI – config.txt richiede dtoverlay=spi0-0cs sotto dtparam=spi=on, poi riavviare il Pi",
                           "GPIO {cs} (CS) occupà: il driver SPI al tegna – config.txt dovra dtoverlay=spi0-0cs sut dtparam=spi=on, lura reaviar il Pi"),
    SENXOR_TX["gpio_busy"]: ("ein GPIO der Wärmebildkamera ist belegt (anderes Programm oder Einstellung): {m}",
                             "un GPIO de la caméra thermique est occupé (autre programme ou réglage) : {m}",
                             "un GPIO della termocamera è occupato (altro programma o impostazione): {m}",
                             "in GPIO da la camera termica è occupà (auter program u configuraziun): {m}"),
    SENXOR_TX["spi_off"]: ("SPI ist aus (kein /dev/spidev0.0): SPI einschalten (raspi-config) und den Pi neu starten",
                           "SPI est désactivé (pas de /dev/spidev0.0) : activer SPI (raspi-config) et redémarrer le Pi",
                           "SPI è spento (nessun /dev/spidev0.0): attivare SPI (raspi-config) e riavviare il Pi",
                           "SPI è deactivà (nagin /dev/spidev0.0): activar SPI (raspi-config) e reaviar il Pi"),
    SENXOR_TX["spi_perm"]: ("keine Berechtigung für /dev/spidev0.0: der MoveEye-Benutzer muss in der Gruppe spi sein",
                            "pas d’autorisation pour /dev/spidev0.0 : l’utilisateur MoveEye doit être dans le groupe spi",
                            "nessuna autorizzazione per /dev/spidev0.0: l’utente MoveEye deve essere nel gruppo spi",
                            "nagin permiss per /dev/spidev0.0: l’utilisader MoveEye sto esser en la gruppa spi"),
    SENXOR_TX["i2c_off"]: ("I2C ist aus (kein /dev/i2c-1): I2C einschalten (raspi-config) und den Pi neu starten",
                           "I2C est désactivé (pas de /dev/i2c-1) : activer I2C (raspi-config) et redémarrer le Pi",
                           "I2C è spento (nessun /dev/i2c-1): attivare I2C (raspi-config) e riavviare il Pi",
                           "I2C è deactivà (nagin /dev/i2c-1): activar I2C (raspi-config) e reaviar il Pi"),
    SENXOR_TX["i2c_none"]: ("keine Antwort auf I2C 0x40 (errno 121): SDA (GPIO 2), SCL (GPIO 3), 5 V / 3,3 V und GND des Moduls prüfen",
                            "pas de réponse sur I2C 0x40 (errno 121) : vérifier SDA (GPIO 2), SCL (GPIO 3), 5 V / 3,3 V et GND du module",
                            "nessuna risposta su I2C 0x40 (errno 121): controllare SDA (GPIO 2), SCL (GPIO 3), 5 V / 3,3 V e GND del modulo",
                            "nagina resposta sin I2C 0x40 (errno 121): controllar SDA (GPIO 2), SCL (GPIO 3), 5 V / 3,3 V e GND dal modul"),
    SENXOR_TX["frame"]: ("Modul antwortet, kein Bild: DATA READY (GPIO {drdy}) nie hoch – D_READY, nRESET (GPIO {rst}), CS (GPIO {cs}), MISO 9 / MOSI 10 / CLK 11 prüfen",
                         "le module répond, pas d’image : DATA READY (GPIO {drdy}) jamais haut – vérifier D_READY, nRESET (GPIO {rst}), CS (GPIO {cs}), MISO 9 / MOSI 10 / CLK 11",
                         "il modulo risponde, nessuna immagine: DATA READY (GPIO {drdy}) mai alto – controllare D_READY, nRESET (GPIO {rst}), CS (GPIO {cs}), MISO 9 / MOSI 10 / CLK 11",
                         "il modul respunda, nagin maletg: DATA READY (GPIO {drdy}) mai aut – controllar D_READY, nRESET (GPIO {rst}), CS (GPIO {cs}), MISO 9 / MOSI 10 / CLK 11"),
    SENXOR_TX["nodrdy"]: ("kein DATA READY", "pas de DATA READY", "nessun DATA READY", "nagin DATA READY"),
    SENXOR_TX["empty"]: ("leeres Bild (CRC / SPI)", "image vide (CRC / SPI)", "immagine vuota (CRC / SPI)", "maletg vid (CRC / SPI)"),
    SENXOR_TX["shape"]: ("Bildform: {e}", "forme de l’image : {e}", "forma dell’immagine: {e}", "furma dal maletg: {e}"),
    "no picture": ("kein Bild", "pas d’image", "nessuna immagine", "nagin maletg"),
    "not found": ("nicht gefunden", "introuvable", "non trovato", "betg chattà"),
    "error": ("Fehler", "erreur", "errore", "errur"),
}
for _k, _v in list(_HX_TC.items()) + list(_HX_THX.items()):
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_tc_tl_status_text_base = tl_status_text


def tl_status_text(text):                                  # + 639zzzzzx: the composed thermal status (080) in the language too
    s = str(text or "")
    if s.startswith(tuple(p_ for p_, _k in THERMAL_TX_PRE)) or any(rx.fullmatch(s) for rx, _t in _thx_res()):
        return thermal_status_tr(s)
    return _tc_tl_status_text_base(text)


USER_UI_ADMIN = USER_UI_ADMIN + ",#th-fix"                 # the buttons «Install driver» / «Check and repair»: admin only
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


TC_HELP = (
    ('<section id="thermal" data-icon="🌡"><h2>Wärmebild</h2>',
     "<p><b>🩺 Wärmebild prüfen und reparieren</b> (Mehr → Werkzeuge, nur Administrator; im Fenster: Einstellungen → Wärmebild): "
     "MoveEye prüft der Reihe nach config.txt (SPI, I2C, <code>dtoverlay=spi0-0cs</code>), die Geräte /dev/spidev0.0 und /dev/i2c-1, "
     "die Gruppen, die I2C-Adressen (0x40 Wärmebild, 0x41 PCA9685, 0x36 X1206), den Treiber pysenxor (auch wenn er nur in einer venv "
     "liegt), numpy / OpenCV / picamera2, die Pins (CS GPIO 7, nRESET GPIO 23, D_READY GPIO 24 – einstellbar), das Kopfbild und das "
     "Wärmebild mit Bildrate. Wo es geht, repariert ein Knopf (mit Rückfrage und Rückgängig). Fehlt der Treiber, installiert "
     "<b>«Treiber installieren»</b> (auch direkt unter der Statuszeile in den Wärmebild-Einstellungen) pysenxor von der offiziellen "
     "Waveshare-Seite (files.waveshare.com, nur HTTPS) in den MoveEye-Ordner und fehlende Systempakete mit apt – kein pip; Waveshare "
     "veröffentlicht keine Prüfsumme, MoveEye schreibt die SHA-256 ins Protokoll. Der Bericht lässt sich kopieren und enthält "
     "keine Passwörter. Kommt kein Wärmebild, läuft das Kopfbild trotzdem weiter; die Ansicht «Wärmebild» zeigt «⚠ kein Wärmebild».</p>"),
    ('<section id="thermal" data-icon="🌡"><h2>Thermal camera</h2>',
     "<p><b>🩺 Check and repair the thermal camera</b> (More → Tools, administrator only; in the window: Settings → Thermal camera): "
     "MoveEye checks config.txt (SPI, I2C, <code>dtoverlay=spi0-0cs</code>), the devices /dev/spidev0.0 and /dev/i2c-1, the groups, the "
     "I2C addresses (0x40 thermal, 0x41 PCA9685, 0x36 X1206), the driver pysenxor (also when it is only in a venv), numpy / OpenCV / "
     "picamera2, the pins (CS GPIO 7, nRESET GPIO 23, D_READY GPIO 24 – adjustable), the head picture and the thermal picture with its "
     "rate. Where possible a button repairs it (with a question and undo). Without the driver, <b>«Install driver»</b> (also right below "
     "the status line in the thermal camera settings) installs pysenxor from the official Waveshare site (files.waveshare.com, HTTPS "
     "only) into the MoveEye folder and missing system packages with apt - no pip; Waveshare publishes no checksum, MoveEye writes the "
     "SHA-256 to the log. The report can be copied and holds no passwords. Without a "
     "thermal picture the head picture keeps running; the view «Thermal» shows «⚠ no thermal picture».</p>"),
)
for _a, _b in TC_HELP:
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


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
    # 4.25.x: the status of the Thermal-90 in German / French, not English; the official address of the driver
    st_ = "no picture: " + SENXOR_TX["driver"].format(e="No module named 'senxor'")
    de_, fr_ = thermal_status_tr(st_, "de"), thermal_status_tr(st_, "fr")
    assert de_.startswith("kein Bild: Waveshare-Treiber pysenxor fehlt (No module named 'senxor')"), de_
    assert fr_.replace("’", "'").startswith("pas d'image") and "pilote Waveshare pysenxor manque" in fr_, fr_
    assert "Treiber installieren" in de_ and "missing" not in de_, de_
    assert "GPIO 24" in thermal_status_tr("no picture: " + SENXOR_TX["frame"].format(drdy=24, rst=23, cs=7), "de")
    assert thermal_status_tr("connected", "de") == "verbunden"
    assert TC_SENXOR_URL.startswith("https://" + TC_SENXOR_HOST + "/") and "senxor_install" in TC_ACTIONS
    assert "#th-fix" in USER_UI_ADMIN
    for k in _HX_THX:
        assert all(_HX_THX[k]) and set(re.findall(r"\{(\w+)\}", k)) == set(re.findall(r"\{(\w+)\}", _HX_THX[k][0])), k
    for k in _HX_TC:
        assert all(_HX_TC[k]), k
    return True


SELFTEST_EXTRA.append(("Thermal camera check: config.txt, start errors in clear words, pins, tools page (639zzzzzx)", thermal_check_selftest))
