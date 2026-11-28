#@ Motion Watch – Teil 080: Treiber Wärmebild-Modul, Klasse Hardware. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Waveshare Thermal-90 / Thermal-44 (80 x 62, Meridian MI48 "SenXor"): SPI for the pictures, I2C (0x40) for the settings,
#   GPIO 23 = reset, 24 = data ready, 7 = chip select. Uses the driver of Waveshare (pysenxor, from their wiki:
#   Thermal_Camera_Hat.zip -> pysenxor-master -> pip install -e ./; MoveEye can install it: 639zzzzzx «Install driver»). /boot/firmware/config.txt: dtparam=spi=on +
#   dtoverlay=spi0-0cs, I2C on. The picture is the temperature in degrees per pixel (float).
# ----------------------------------------------------------------------------
SENXOR_PIN_DEF = {"senxor_cs": "7", "senxor_rst": "23", "senxor_drdy": "24"}     # Waveshare wiki (HAT and single module)
SENXOR_LAST = {"step": "", "err": "", "t": 0.0, "fw": "", "id": "", "frames": 0, "read_err": "", "pins": None}


def senxor_pins():
    """(cs, reset, data ready) as BCM numbers: settings senxor_cs / senxor_rst / senxor_drdy (default 7 / 23 / 24)"""
    out = []
    for k, d in SENXOR_PIN_DEF.items():
        try:
            v = int(str(CFG.get(k, d)).strip())
            out.append(v if 0 <= v <= 27 else int(d))
        except (TypeError, ValueError):
            out.append(int(d))
    return tuple(out)


# 4.25.x (Besitzer, real Pi 5: the status in the settings was English on a German screen): every text of the Thermal-90
#   start is a template (English key with {placeholders}); thermal_status_tr() (below) finds the template again in the
#   status and translates it with tr() / DE / TRX - the numbers and the technical error stay as they are.
SENXOR_TX = {
    "driver": "Waveshare driver pysenxor missing ({e}) - «Install driver» in the thermal camera settings installs it",
    "pkg": "system package {pkg} missing - «Check the thermal camera» installs it",
    "gpio_cs": "GPIO {cs} (CS) busy: the SPI driver holds it - config.txt needs dtoverlay=spi0-0cs below dtparam=spi=on, then restart the Pi",
    "gpio_busy": "a GPIO of the thermal camera is busy (another program or setting): {m}",
    "spi_off": "SPI is off (no /dev/spidev0.0): switch on SPI (raspi-config) and restart the Pi",
    "spi_perm": "no permission for /dev/spidev0.0: the MoveEye user must be in the group spi",
    "i2c_off": "I2C is off (no /dev/i2c-1): switch on I2C (raspi-config) and restart the Pi",
    "i2c_none": "no answer on I2C 0x40 (errno 121): check SDA (GPIO 2), SCL (GPIO 3), 5 V / 3.3 V and GND of the module",
    "frame": "module answers, no picture: DATA READY (GPIO {drdy}) never high - check D_READY, nRESET (GPIO {rst}), CS (GPIO {cs}), MISO 9 / MOSI 10 / CLK 11",
    "nodrdy": "no DATA READY",
    "empty": "empty picture (CRC / SPI)",
    "shape": "picture shape: {e}",
}
SENXOR_DRV_SUB = os.path.join("treiber", "pysenxor")    # 639zzzzzx «Install driver»: DATA_DIR/treiber/pysenxor/senxor


def senxor_driver_path():
    """the folder of a pysenxor installed by MoveEye (DATA_DIR/treiber/pysenxor) on sys.path - also when the user site of
    Python is off (the .pth then does not count); '' when there is none"""
    try:
        d = os.path.join(DATA_DIR, SENXOR_DRV_SUB)
        if os.path.isfile(os.path.join(d, "senxor", "mi48.py")):
            if d not in sys.path:
                sys.path.append(d)
            return d
    except Exception:
        pass
    return ""


def senxor_explain(step, e, pins=None):
    """an error of the Thermal-90 start -> a clear sentence (English key text, translated where it is shown)"""
    cs, rst, drdy = pins or senxor_pins()
    m = f"{type(e).__name__}: {e}" if not isinstance(e, str) else e
    low = m.lower()
    if step == "gpio" and "busy" in low:
        if "BCM%d" % cs in m or step == "gpio" and getattr(e, "_mw_pin", None) == cs:
            return SENXOR_TX["gpio_cs"].format(cs=cs)
        return SENXOR_TX["gpio_busy"].format(m=m[:80])
    if step == "spi" and ("no such file" in low or "errno 2]" in low):
        return SENXOR_TX["spi_off"]
    if step == "spi" and ("permission" in low or "errno 13" in low):
        return SENXOR_TX["spi_perm"]
    if step == "i2c" and ("no such file" in low or "errno 2]" in low):
        return SENXOR_TX["i2c_off"]
    if step == "module" and any(k in low for k in ("errno 121", "remote i/o", "errno 6]", "errno 110", "timed out")):
        return SENXOR_TX["i2c_none"]
    if step == "frame":
        return SENXOR_TX["frame"].format(drdy=drdy, rst=rst, cs=cs)
    return f"{step}: {m[:140]}"


def _senxor_data_to_frame(data, shape, hflip=False):
    """the same as senxor.utils.data_to_frame (used when senxor.utils needs a package that is not there, e.g. cmapy)"""
    nc, nr = shape
    fr = np.asarray(data).reshape(nr, nc)
    return np.flip(fr, 1) if hflip else fr


_THX_RE = []


def _thx_res():
    if not _THX_RE:
        for k, t_ in SENXOR_TX.items():
            pat = re.escape(t_)
            for ph in set(re.findall(r"\{(\w+)\}", t_)):
                pat = pat.replace(re.escape("{" + ph + "}"), "(?P<" + ph + ">.*?)", 1)
            _THX_RE.append((re.compile(pat), t_))
    return _THX_RE


THERMAL_TX_PRE = (("no picture: ", "no picture"), ("not found: ", "not found"), ("error: ", "error"))


def thermal_status_tr(s, lang=None):
    """the thermal status (STATE["thermal"], SENXOR_LAST["err"]) in the language: prefix + template + the rest unchanged"""
    s = str(s or "")
    for pre, key in THERMAL_TX_PRE:
        if s.startswith(pre):
            return tr(key, lang) + ": " + thermal_status_tr(s[len(pre):], lang)
    for rx, t_ in _thx_res():
        m_ = rx.fullmatch(s)
        if m_:
            try:
                return tr(t_, lang).format(**m_.groupdict())
            except (KeyError, IndexError, ValueError):
                return s
    m_ = re.fullmatch(r"(driver|spi|i2c|gpio|module|frame): (.*)", s, re.S)
    if m_:
        return m_.group(1) + ": " + thermal_status_tr(m_.group(2), lang)
    return tr(s, lang)


THERMAL_TX = {"src": None}


def thermal_tx_tick():
    """STATE["thermal_tx"] = the thermal status in all five languages (the web page picks its own; 230 calls it in its loop)"""
    s = str(STATE.get("thermal") or "")
    if THERMAL_TX.get("src") == s:
        return
    try:
        tx = {"src": s}
        for L in ("de", "fr", "it", "rm", "en"):
            tx[L] = thermal_status_tr(s, L)
        STATE["thermal_tx"] = tx; THERMAL_TX["src"] = s
    except Exception:
        pass


class SenxorSource:
    """Waveshare Thermal-90 / 44 (HAT or single module) after the example stream_spi.py of Waveshare (pysenxor). 4.24.x
    (Besitzer, first real module on a Pi 5): every step is checked and named (driver, SPI, I2C, GPIO, module, first picture);
    when a step fails everything opened so far is closed again - before, the GPIO / SPI handles stayed open and every new try
    after 5 s failed with «GPIO busy», even after the cause was gone."""
    size = (80, 62)

    def __init__(self, i2c_addr=0x40, fps=15):
        self._open = []                                   # what must be closed again (in this order, backwards)
        self.mi48 = None; self.pins = senxor_pins(); self.frames = 0; self.read_err = ""
        cs, rst, drdy = self.pins
        SENXOR_LAST.update(step="", err="", t=time.time(), pins=self.pins)
        step = "driver"
        try:
            senxor_driver_path()                              # 639zzzzzx: a driver installed by MoveEye
            try:
                from senxor.mi48 import MI48
                from senxor.interfaces import SPI_Interface, I2C_Interface
            except ImportError as e:
                raise RuntimeError(SENXOR_TX["driver"].format(e=str(e)[:60])) from None
            try:
                from senxor.utils import data_to_frame
            except ImportError:
                data_to_frame = _senxor_data_to_frame         # senxor.utils may need cmapy / matplotlib: not needed here
            try:
                from spidev import SpiDev
            except ImportError:
                raise RuntimeError(SENXOR_TX["pkg"].format(pkg="python3-spidev")) from None
            try:
                from smbus import SMBus
            except ImportError:
                try:
                    from smbus2 import SMBus
                except ImportError:
                    raise RuntimeError(SENXOR_TX["pkg"].format(pkg="python3-smbus")) from None
            try:
                from gpiozero import DigitalInputDevice, DigitalOutputDevice
            except ImportError:
                raise RuntimeError(SENXOR_TX["pkg"].format(pkg="python3-gpiozero")) from None
            self._to_frame = data_to_frame
            step = "spi"
            devd = os.environ.get("MW_TEST_DEV_DIR") or "/dev"          # tests: a folder with made-up device files
            if sys.platform.startswith("linux") and os.path.isdir(devd) and not os.path.exists(os.path.join(devd, "spidev0.0")):
                raise FileNotFoundError(2, "No such file or directory", "/dev/spidev0.0")
            step = "i2c"
            if sys.platform.startswith("linux") and os.path.isdir(devd) and not os.path.exists(os.path.join(devd, "i2c-1")):
                raise FileNotFoundError(2, "No such file or directory", "/dev/i2c-1")
            step = "gpio"
            for pin, attr, mk in ((cs, "cs", lambda p: DigitalOutputDevice("BCM%d" % p, active_high=False, initial_value=False)),
                                  (drdy, "ready", lambda p: DigitalInputDevice("BCM%d" % p, pull_up=False)),
                                  (rst, "rst", lambda p: DigitalOutputDevice("BCM%d" % p, active_high=False, initial_value=True))):
                try:
                    dev = mk(pin)
                except Exception as e:
                    try:
                        e._mw_pin = pin
                    except Exception:
                        pass
                    raise RuntimeError(f"GPIO {pin}: {type(e).__name__}: {e}"[:160] if "busy" not in str(e).lower()
                                       else f"BCM{pin} busy: {e}"[:160]) from None
                setattr(self, attr, dev); self._open.append(dev.close)
            step = "spi"
            dev_ = SpiDev(0, 0); self._open.append(dev_.close)
            spi = SPI_Interface(dev_, xfer_size=160)
            spi.device.mode = 0b00; spi.device.lsbfirst = False; spi.device.bits_per_word = 8
            spi.device.max_speed_hz = 31200000; spi.device.cshigh = True
            step = "i2c"
            bus = SMBus(1); self._open.append(getattr(bus, "close", lambda: None))
            i2c = I2C_Interface(bus, i2c_addr)
            rdev = self.rst

            def reset():
                rdev.on(); time.sleep(0.000035); rdev.off(); time.sleep(0.05)
            step = "module"
            self.mi48 = MI48([i2c, spi], data_ready=self.ready, reset_handler=reset)
            try:
                self.mi48.set_fps(fps)
            except Exception:
                pass
            fw = getattr(self.mi48, "fw_version", None)
            try:
                if int(str(fw[0])) >= 2:
                    self.mi48.enable_filter(f1=True, f2=True, f3=False)
                    self.mi48.set_offset_corr(0.0)
            except Exception:
                pass
            ident = ""
            for a in ("camera_id_hexsn", "sn", "camera_id", "name"):
                v = getattr(self.mi48, a, None)
                if v and not callable(v):
                    ident = str(v)[:40]; break
            SENXOR_LAST.update(fw=".".join(str(x) for x in fw) if isinstance(fw, (tuple, list)) else str(fw or ""), id=ident)
            self.mi48.start(stream=True, with_header=True)
            self._open.append(self.mi48.stop)
            self.shape = getattr(self.mi48, "fpa_shape", (80, 62))
            step = "frame"                                # the first picture within 3 s - else DATA READY / wiring
            ok, fr = False, None
            end = time.time() + 3.0
            while time.time() < end and not ok:
                ok, fr = self.read()
            if not ok:
                raise RuntimeError(self.read_err or SENXOR_TX["nodrdy"])
            self._first = fr
        except Exception as e:
            self.release()
            msg = senxor_explain(step, e, self.pins) if step != "driver" else str(e)
            SENXOR_LAST.update(step=step, err=msg, t=time.time())
            raise RuntimeError(msg) from None
        SENXOR_LAST.update(step="ok", err="", t=time.time())

    def read(self):
        fr0 = getattr(self, "_first", None)
        if fr0 is not None:
            self._first = None
            return True, fr0
        try:
            if not self.ready.wait_for_active(timeout=1.0):
                self.read_err = SENXOR_TX["nodrdy"]
                return False, None
            self.cs.on(); time.sleep(0.0001)
            data, _header = self.mi48.read()
            time.sleep(0.0001); self.cs.off()
        except Exception as e:
            self.read_err = f"{type(e).__name__}: {e}"[:120]
            try:
                self.cs.off()
            except Exception:
                pass
            return False, None
        if data is None:
            self.read_err = SENXOR_TX["empty"]
            return False, None
        try:
            fr = np.asarray(self._to_frame(data, self.shape), dtype=np.float32)
            if fr.ndim != 2:
                fr = fr.reshape(62, 80)
        except Exception as e:
            self.read_err = SENXOR_TX["shape"].format(e=str(e)[:100])
            return False, None
        if fr.size and float(np.median(fr)) > 200:          # deci-Kelvin -> degrees Celsius (older driver versions)
            fr = fr / 10.0 - 273.15
        self.frames += 1; SENXOR_LAST["frames"] = SENXOR_LAST.get("frames", 0) + 1; self.read_err = ""
        STATE["thermal_max"] = round(float(np.max(fr)), 1)
        return True, fr

    def release(self):
        todo, self._open = list(getattr(self, "_open", [])), []
        for f in reversed(todo):
            try:
                f()
            except Exception:
                pass


HW_REINIT = {"want": False}
# 3.44.3 (variants without a head, Besitzer 01.11.2026): «automatic» without a PCA9685 falls back to servos on GPIO 17/27. A
#   hobby servo gives no feedback - nobody can tell whether one hangs there. The self-check says so honestly (a hint, not a
#   green tick: a housing v5.x has a PCA9685, so it is missing or not answering); chosen «GPIO» by hand stays «ok».
SERVO_GPIO_FALLBACK_TEXT = "no servo driver found - GPIO fallback (17 / 27) without feedback"
SERVO_GPIO_FALLBACK_TIP = ("Housing v5.x: the PCA9685 (0x41) does not answer - check its power and I2C, then restart. No head built in: "
                           "nothing to do. Servos really on GPIO 17 / 27: choose the servo driver «GPIO».")


def servo_gpio_fallback(backend=None, driver=None):
    """True: the servos run on GPIO 17/27 only because «automatic» found no PCA9685 (no feedback, maybe nothing connected)"""
    b = str(STATE.get("servo_backend") or "") if backend is None else str(backend)
    d = str(CFG.get("servo_driver") or "auto") if driver is None else str(driver)
    return d == "auto" and b.startswith(("gpiozero", "pigpio"))


class Hardware:
    """Pan/tilt servos + any number of relay outputs + lights. Servo backends: PCA9685 -> gpiozero -> pigpio -> simulation."""
    def __init__(self):
        self.backend = "simulation"; self.io = "none"        # io = what switches the relays / GPIO lights
        self._OutputDevice = None
        self.pan = self.tilt = self.pi = self.pca = None
        self.outs = {}              # gpio -> {"dev": gpiozero device or None, "on": bool, "al": bool}
        self.fail = {}              # gpio -> time of last error (retried after 5 s)
        self._last_servo = None; self._pca_lights = {}
        self._init_backend()
        threading.Thread(target=self.loop, daemon=True).start()

    def _close_backend(self):
        for d in (self.pan, self.tilt):
            try:
                if d is not None:
                    d.close()
            except Exception:
                pass
        if self.pca is not None:
            self.pca.close()
        self.pan = self.tilt = self.pca = None; self._pca_lights = {}; self._last_servo = None

    def _init_backend(self):
        """PCA9685 (if chosen / found) for the servos; relays and GPIO lights always via gpiozero (or pigpio)."""
        self._close_backend(); self.backend = "simulation"
        drv, msg = CFG["servo_driver"], ""
        try:
            addr = int(str(CFG["pca_address"]), 16)
        except ValueError:
            addr = 0x41
        if drv in ("auto", "pca9685"):
            if drv == "auto" and addr == 0x40 and str(CFG["thermal_source"]).startswith("senxor"):
                msg = "PCA9685 on 0x40 = address of the thermal camera - change the PCA9685 to 0x41"
            elif drv == "pca9685" or pca_present(addr):
                try:
                    self.pca = PCA9685(addr)
                except Exception as e:
                    msg = f"PCA9685 0x{addr:02x}: {e}"
        try:
            from gpiozero import Servo, OutputDevice
            self._OutputDevice = OutputDevice
            self.io = "gpiozero"
            if self.pca is None and drv != "pca9685":
                mn, mx = CFG["servo_min_us"] / 1e6, CFG["servo_max_us"] / 1e6
                iv = None if CFG.get("kopf_transport") else 0.0     # 639zzzt: no pulse at the start in the transport mode
                self.pan = Servo(GPIO_PAN, initial_value=iv, min_pulse_width=mn, max_pulse_width=mx)
                self.tilt = Servo(GPIO_TILT, initial_value=iv, min_pulse_width=mn, max_pulse_width=mx)
                self.backend = "gpiozero"
        except Exception as e1:
            try:
                import pigpio
                if self.pi is None:
                    self.pi = pigpio.pi()
                if not self.pi.connected:
                    raise RuntimeError("pigpiod not running")
                self._pigpio = pigpio; self.io = "pigpio"
                if self.pca is None and drv != "pca9685":
                    self.backend = "pigpio"
            except Exception:
                if self.pca is None:
                    log_event("servo", f"No servo hardware ({type(e1).__name__}) - simulation mode")
        if self.pca is not None:
            self.backend = "pca9685"
        elif self.pan is None and self.backend != "pigpio" or drv == "pca9685":
            self.backend = "simulation"
        STATE["servo_backend"] = self.backend + (f" ({msg})" if msg else "")
        where = (f"PCA9685 0x{self.pca.addr:02x} ch {CFG['pca_pan_ch']}/{CFG['pca_tilt_ch']}" if self.pca is not None
                 else f"pan GPIO{GPIO_PAN}, tilt GPIO{GPIO_TILT}")
        log_event("servo", f"Servo backend: {self.backend}  ({where}, relays GPIO {', '.join(str(r['gpio']) for r in RELAYS) or '-'})"
                           + (f" - {msg}" if msg else ""))

    def _us(self, pct):
        return CFG["servo_min_us"] + (CFG["servo_max_us"] - CFG["servo_min_us"]) * pct / 100.0

    def _servos(self, pan, tilt, cont=False):
        # 2.98.35: the software limits once more right here, the lowest level before the PWM (072) - whatever came before
        # (an error, NaN, a wrong value) never drives past them. cont: pan is a speed (continuous servo), not a position.
        lim = self.limits()
        vals = []
        for i, v in enumerate((pan, tilt)):
            v = float(v)
            if not math.isfinite(v):
                raise ValueError("servo value is not a number")
            lo, hi = (0.0, 100.0) if (cont and i == 0) else lim[i]
            vals.append(max(lo, min(hi, max(0.0, min(100.0, v)))))
        pan, tilt = vals
        if CFG["invert_pan"]: pan = 100 - pan
        if CFG["invert_tilt"]: tilt = 100 - tilt
        if self.pca is not None:
            self.pca.pulse_us(int(CFG["pca_pan_ch"]), self._us(pan))
            self.pca.pulse_us(int(CFG["pca_tilt_ch"]), self._us(tilt))
        elif self.backend == "gpiozero":
            self.pan.value = pan / 50.0 - 1.0
            self.tilt.value = tilt / 50.0 - 1.0
        elif self.backend == "pigpio":
            self.pi.set_servo_pulsewidth(GPIO_PAN, self._us(pan))
            self.pi.set_servo_pulsewidth(GPIO_TILT, self._us(tilt))

    def _servos_off(self):
        """639zzzt transport mode: cut the servo pulses (PCA9685 channel fully off, gpiozero detach, pigpio 0) - the head is
        held by the cap only, the servos get no current and do not jitter. The next normal write switches them on again."""
        try:
            if self.pca is not None:
                self.pca.switch(int(CFG["pca_pan_ch"]), False); self.pca.switch(int(CFG["pca_tilt_ch"]), False)
            elif self.backend == "gpiozero":
                self.pan.detach(); self.tilt.detach()
            elif self.backend == "pigpio":
                self.pi.set_servo_pulsewidth(GPIO_PAN, 0); self.pi.set_servo_pulsewidth(GPIO_TILT, 0)
            SRV["tp_off_n"] = int(SRV.get("tp_off_n", 0)) + 1
            log_event("servo", "Transport mode: servo outputs off (" + self.backend + ")")
        except Exception as e:
            log_event("servo", f"Servo outputs off: {e}"[:160])
            if self.pca is not None:
                servo_io_error(e)

    def _write(self, gpio, on, al):
        if gpio in ups_x12_pins():                            # 100: GPIO 6 / 16 belong to a Geekworm X1206 - never driven
            return ups_x12_pin_warn("relay / light", gpio)
        ent = self.outs.get(gpio)
        if self.io == "gpiozero":
            if ent is None or ent["al"] != al:
                if ent is not None and ent["dev"] is not None:
                    ent["dev"].close()
                    self.outs.pop(gpio, None)
                ent = {"dev": self._OutputDevice(gpio, active_high=not al, initial_value=False), "on": False, "al": al}
                self.outs[gpio] = ent
            ent["dev"].on() if on else ent["dev"].off()
        else:
            if ent is None:
                if self.io == "pigpio":
                    self.pi.set_mode(gpio, self._pigpio.OUTPUT)
                ent = {"dev": None, "on": False, "al": al}
                self.outs[gpio] = ent
            if self.io == "pigpio":
                self.pi.write(gpio, int(bool(on)) ^ int(bool(al)))
        ent["on"], ent["al"] = on, al

    def _release(self, gpio):
        ent = self.outs.pop(gpio, None)
        if not ent:
            return
        try:
            if self.io == "gpiozero" and ent["dev"] is not None:
                ent["dev"].off(); ent["dev"].close()
            elif self.io == "pigpio":
                self.pi.write(gpio, 1 if ent["al"] else 0)          # inactive level
        except Exception:
            pass

    @staticmethod
    def limits():
        """(lo, hi) in percent for pan and tilt from the limits in degrees (middle = 50 %, 0..100 % = servo_range degrees)."""
        out = []
        for k in ("pan_limit", "tilt_limit"):
            half = servo_half("pan" if k == "pan_limit" else "tilt")
            d = max(0.0, min(50.0, float(CFG[k]) / half * 50.0))
            out.append((50.0 - d, 50.0 + d))
        return out

    def _lights(self, wanted):
        """Lights: PCA9685 channel (switched here) or GPIO (added to the outputs like a relay)."""
        res = lights_tick()
        for n in ("white", "ir"):
            out, on = CFG[f"light_{n}_out"], res[n]
            prev = self._pca_lights.get(n)
            if prev and prev[0] != out and self.pca is not None:          # output changed: switch the old channel off
                try:
                    self.pca.switch(int(prev[0][4:]), False)
                except Exception:
                    pass
                self._pca_lights.pop(n, None); prev = None
            if out.startswith("pca:"):
                pct = light_pct(n) if on else 0.0                 # 639zzzzz: dimmed as a percentage (100 % = on as before)
                if self.pca is not None and prev != (out, on, pct):
                    try:
                        if 0.0 < pct < 100.0 and hasattr(self.pca, "dim"):
                            self.pca.dim(int(out[4:]), pct)
                        else:
                            self.pca.switch(int(out[4:]), on)         # 100 % / off: exactly as before
                        self._pca_lights[n] = (out, on, pct)
                    except Exception as e:
                        log_event("servo", f"Light error: {e}")
            elif out.startswith("gpio:"):
                g = int(out[5:])
                if g not in wanted:
                    wanted[g] = (on, False)

    def _cont_pan(self, pan):
        """2.98.30: a continuous rotation («360° endless») pan servo knows no position: the pulse is a speed (50 % = stop).
        The position is ESTIMATED from speed x time (cont_dps = degrees per second at full speed) - «set the middle» when
        the head looks straight ahead. Positional servos: unchanged."""
        if CFG.get("servo_kind") != "continuous" or CFG.get("sim_on"):
            self._ct = None
            return pan
        now = time.monotonic()
        dt = 0.0 if getattr(self, "_ct", None) is None else max(0.0, min(0.1, now - self._ct))
        self._ct = now
        if CFG.get("cont_set_mid"):
            CFG["cont_set_mid"] = False; CFG["cont_est"] = 50.0; CFG["pan"] = 50.0; pan = 50.0
            log_event("servo", "Continuous servo: the middle is set here (the head looks straight ahead)")
            save_settings()
        est = float(CFG.get("cont_est", 50.0))
        pct_s = max(5.0, float(CFG.get("cont_dps") or 120.0)) * 100.0 / (2.0 * servo_half("pan"))
        diff = pan - est
        sp = 0.0 if abs(diff) < 0.4 else max(-1.0, min(1.0, diff / (pct_s * 0.25)))    # slower in the last quarter second
        if sp == 0.0 and getattr(self, "_csp", 0.0) != 0.0:
            save_settings()                                    # stands again: remember the estimate
        self._csp = sp
        CFG["cont_est"] = round(est + sp * pct_s * dt, 2)
        return 50.0 + sp * 50.0

    def _pca_check(self):
        """2.98.35: every 10 s - does the PCA9685 still have its settings? After a brown-out (servos draw too much current)
        it starts again asleep with outputs off: that is a latched fault (072) - set up again, outputs only after «Freigeben»"""
        now = time.monotonic()
        if self.pca is None or now - getattr(self, "_pca_t", 0.0) < 10.0:
            return
        self._pca_t = now
        try:
            ok = self.pca.healthy()
        except OSError as e:
            servo_io_error(e); return
        if not ok:
            servo_fault("pca_reset", "MODE1 / prescaler lost")
            HW_REINIT["want"] = True

    def loop(self):
        """50 Hz: push pan/tilt, all relay states and the lights to the hardware when they change."""
        servo_watchdog_start()                             # 2.98.35: the watchdog of this loop (072)
        while True:
            if HW_REINIT["want"]:
                HW_REINIT["want"] = False
                try:
                    self._init_backend()
                except Exception as e:
                    log_event("servo", f"Servo driver: {e}")
            (plo, phi), (tlo, thi) = self.limits()
            try:
                want = (float(CFG["pan"]), float(CFG["tilt"]))
                if not all(math.isfinite(x) for x in want):
                    raise ValueError
            except (TypeError, ValueError):
                want = servo_pos(); CFG["pan"], CFG["tilt"] = want    # 2.98.35: nonsense as target -> stays where it is
            pan = max(plo, min(phi, want[0]))
            tilt = max(tlo, min(thi, want[1]))
            servo_limit_note(0, abs(pan - want[0]) > 0.05); servo_limit_note(1, abs(tilt - want[1]) > 0.05)
            if abs(pan - CFG["pan"]) > 0.05:
                CFG["pan"] = round(pan, 2)                # the page / window shows where the camera really is
            if abs(tilt - CFG["tilt"]) > 0.05:
                CFG["tilt"] = round(tilt, 2)
            # 2.98.35: the motion planner (072) - ramps instead of jumps; only its position reaches the servos
            mono = time.monotonic(); dt_ = mono - getattr(self, "_plan_t", mono - 0.02); self._plan_t = mono
            try:
                pan, tilt = servo_plan_tick(dt_)
            except Exception as e:
                pan, tilt = servo_pos()
                log_event("servo", f"Motion planner: {type(e).__name__}: {e}"[:160])
            pan = self._cont_pan(pan)                      # 2.98.30: continuous rotation servo: speed instead of position (162)
            cur = (round(pan, 2), round(tilt, 2))
            if servo_detached():                           # 639zzzt transport mode: no pulse at all (limp, no holding torque)
                if not getattr(self, "_detached", False) and cur != self._last_servo:
                    # 3.94.0: the planner arrives in the same tick in which it reports «home» - first send that home pulse
                    # and hold it for one tick, only then cut the outputs (before, the head stopped one step short)
                    try:
                        self._servos(pan, tilt, cont=CFG.get("servo_kind") == "continuous" and not CFG.get("sim_on"))
                    except Exception as e:
                        log_event("servo", f"Servo error: {e}")
                    self._last_servo = cur
                else:
                    if not getattr(self, "_detached", False):
                        self._detached = True; self._servos_off()
                    self._last_servo = None
            elif servo_outputs_off():
                self._last_servo = None                    # 2.98.35: latched driver fault: outputs stay off until «Freigeben»
            elif cur != self._last_servo:
                self._detached = False
                try:
                    self._servos(pan, tilt, cont=CFG.get("servo_kind") == "continuous" and not CFG.get("sim_on"))
                    if self.pca is not None:
                        servo_io_ok()
                except Exception as e:
                    log_event("servo", f"Servo error: {e}")
                    if self.pca is not None:
                        servo_io_error(e)                  # 2.98.35: 3 in a row = fault, safe state (072)
                self._last_servo = cur; SERVO_MOVE["t"] = time.time()
            self._pca_check()
            wanted = {g: (on, al) for g, on, al in STATE["relay_out"]}
            try:
                self._lights(wanted)
            except Exception as e:
                log_event("servo", f"Light error: {e}")
            for g in [g for g in self.outs if g not in wanted]:
                self._release(g)
            now = time.time()
            for g, (on, al) in wanted.items():
                ent = self.outs.get(g)
                if ent is not None and ent["on"] == on and ent["al"] == al:
                    continue
                if now - self.fail.get(g, 0.0) < 5.0:
                    continue
                try:
                    self._write(g, on, al); self.fail.pop(g, None)
                except Exception as e:
                    self.fail[g] = now
                    log_event("servo", f"Relay GPIO{g} error: {e}")
            time.sleep(0.02)




