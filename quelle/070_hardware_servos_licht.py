#@ Motion Watch – Teil 070: Servos, PCA9685, Mover, Licht, Disco-Licht. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Hardware: servos + relays  (gpiozero -> pigpio -> simulation)
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# PCA9685: 16-channel PWM chip on I2C (Adafruit board). Drives the two servos (50 Hz, no jitter - the Pi 5 can only make
#   servo pulses in software) and switches the lights (channel fully on / off: no flicker in the video).
#   Talks to /dev/i2c-1 directly, no extra library. I2C must be on (sudo raspi-config -> Interface Options -> I2C).
# ----------------------------------------------------------------------------
I2C_SLAVE = 0x0703
SERVO_MOVE = {"t": 0.0}            # time of the last servo movement (the noise alarm ignores the servo motors)


class PCA9685:
    def __init__(self, addr, bus=1, freq=50.0):
        import fcntl
        self.addr, self.freq = addr, float(freq)
        self.fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
        try:
            fcntl.ioctl(self.fd, I2C_SLAVE, addr)
            # read-only check first: MODE2 bits 7..5 are always 0 and ALLCALLADR is 0xE0 after power-on. Anything else at
            # this address (e.g. the thermal camera on 0x40) must not get our register writes.
            if self._r(0x01) & 0xE0 or self._r(0x05) != 0xE0:
                raise OSError(f"the chip at 0x{addr:02x} is not a PCA9685")
            pre = int(round(25e6 / (4096 * self.freq))) - 1
            self._w(0x00, 0x10)                    # sleep: needed to change the prescaler
            self._w(0xFE, pre)
            self._w(0x01, 0x04)                    # MODE2: totem-pole outputs
            self._w(0x00, 0x20)                    # wake up, register auto-increment
            time.sleep(0.005)
            self._w(0x00, 0xA0)                    # restart the PWM
            if self._r(0xFE) != pre:
                raise OSError("PCA9685 does not answer correctly")
        except Exception:
            os.close(self.fd); raise

    def _w(self, reg, val):
        os.write(self.fd, bytes([reg, val & 0xFF]))

    def _r(self, reg):
        os.write(self.fd, bytes([reg]))
        return os.read(self.fd, 1)[0]

    def _set(self, ch, on, off):
        os.write(self.fd, bytes([0x06 + 4 * ch, on & 0xFF, (on >> 8) & 0xFF, off & 0xFF, (off >> 8) & 0xFF]))

    def pulse_us(self, ch, us):
        self._set(ch, 0, max(0, min(4095, int(round(us * 4096 * self.freq / 1e6)))))

    def switch(self, ch, on):
        self._set(ch, 0x1000, 0) if on else self._set(ch, 0, 0x1000)       # bit 12 = fully on / fully off

    def close(self):
        try:
            os.write(self.fd, bytes([0xFA, 0, 0, 0, 0x10]))                    # all channels off (servos go limp)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass


def pca_present(addr, bus=1):
    try:
        p = PCA9685.__new__(PCA9685)
        import fcntl
        p.fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
        try:
            fcntl.ioctl(p.fd, I2C_SLAVE, addr)
            return not (p._r(0x01) & 0xE0) and p._r(0x05) == 0xE0
        finally:
            os.close(p.fd)
    except Exception:
        return False


# ----------------------------------------------------------------------------
# Mover (from 2.94.0): an optional tracked vehicle under Motion Watch - forward, back, turn on the spot with a second stick.
#   Motor driver: a «Motor HAT» with a PCA9685 and two TB6612 motor bridges on I2C (Adafruit DC & Stepper Motor HAT, default
#   0x60, or the Waveshare Motor Driver HAT). Found by itself (setting «automatic»); not found = no second stick anywhere.
#   In the simulation the 3D simulator says whether it has a mover («Mover simulieren»); the tracks are driven there.
#   Safety: without a new command for 0.6 s (page closed, Wi-Fi gone) both tracks stop; starting and stopping are gentle.
# ----------------------------------------------------------------------------
MOVER = {"test": False, "avail": False, "hw": False, "sim": False, "v": 0.0, "w": 0.0, "l": 0.0, "r": 0.0, "cmd_t": 0.0, "by": "", "msg": "off"}
MOVER_MAP = {"adafruit": ((8, 10, 9), (13, 11, 12)),      # (PWM, IN1, IN2) of the left and the right motor (M1, M2)
             "waveshare": ((0, 1, 2), (5, 3, 4))}          # (PWMA, AIN1, AIN2), (PWMB, BIN1, BIN2)
MOVERCTL = None


def mover_drive(v, w, who="web"):
    """the second stick: v = forward (+) / back (-), w = turn right (+) / left (-), both -1 … 1"""
    try:
        v = max(-1.0, min(1.0, float(v))); w = max(-1.0, min(1.0, float(w)))
    except (TypeError, ValueError):
        return False
    if not MOVER["avail"]:
        return False
    MOVER.update(v=v, w=w, cmd_t=time.monotonic(), by=who)
    if abs(v) > 0.05 or abs(w) > 0.05:
        MANUAL["until"] = time.time() + CFG["manual_hold"]          # driving pauses tracking and patrol like the camera stick
        mover_sim_wake()
    return True


_MOVER_WAKE = {"t": 0.0}


def _mover_pose(p):
    """optional answer field of a simulator with a mover (2.95.43): {"x", "y" in m, "yaw" in degrees (0 = start direction,
    + = turned right), "odo" = metres driven, "blocked" = it stands at an obstacle}; anything else -> None"""
    if not isinstance(p, dict):
        return None
    try:
        out = {k: round(float(p[k]), 2) for k in ("x", "y", "yaw", "odo") if k in p and math.isfinite(float(p[k]))}
    except (TypeError, ValueError):
        return None
    if "blocked" in p:
        out["blocked"] = bool(p.get("blocked"))
    return out or None


def mover_sim_wake():
    """driving in the simulation, but the simulator's vehicle is off: switch it on there (3D simulator: «Mover simulieren»)"""
    now = time.time()
    if not (CFG.get("sim_on") and SIM.get("ok")) or SIM.get("mover") or now - _MOVER_WAKE["t"] < 8.0:
        return
    _MOVER_WAKE["t"] = now

    def work():
        try:
            d = sim_control()
            if any(c.get("id") == "mover_on" for c in (d.get("controls") or [])):
                sim_control({"action": "set", "id": "mover_on", "value": True})
                log_event("sys", "Simulation: vehicle switched on in the simulator (driven with the second stick)")
        except Exception:
            pass
    threading.Thread(target=work, daemon=True, name="mover-wake").start()


def mover_choice_pairs(extra):
    if extra == "mover_mode":
        return [("auto", tr("automatic: on when the motor driver is found")), ("off", tr("off"))]
    if extra == "mover_driver":
        return [("adafruit", tr("Motor HAT (Adafruit or compatible): M1 left, M2 right")),
                ("waveshare", tr("Waveshare Motor Driver HAT: A left, B right"))]
    if extra == "mover_addr":
        return [(f"0x{a:02x}", f"0x{a:02x}") for a in list(range(0x60, 0x70)) + list(range(0x40, 0x48))]
    return []


class MoverControl:
    def __init__(self):
        self.pca = None; self.addr = None; self.next_look = 0.0
        threading.Thread(target=self.loop, daemon=True, name="mover").start()

    def _close(self):
        if self.pca is not None:
            try:
                self.pca.close()
            except Exception:
                pass
        self.pca = None; self.addr = None

    def _find(self):
        """the motor driver at its address (not the one of the servos)"""
        try:
            a = int(str(CFG["mover_addr"]), 16)
        except ValueError:
            a = 0x60
        if self.pca is not None and self.addr == a:
            return True
        self._close()
        try:
            if str(CFG.get("pca_address", "")).lower() == f"0x{a:02x}" and CFG.get("servo_driver") != "gpio":
                MOVER["msg"] = "the address is the one of the servo driver"; return False
        except Exception:
            pass
        if not pca_present(a):
            MOVER["msg"] = "no motor driver found"; return False
        try:
            self.pca = PCA9685(a, freq=1600.0); self.addr = a
            MOVER["msg"] = "motor driver found"
            return True
        except Exception as e:
            MOVER["msg"] = "motor driver: " + str(e)[:60]; self.pca = None
            return False

    def _motor(self, pins, s):
        pwm, in1, in2 = pins
        s = max(-1.0, min(1.0, s))
        if abs(s) < 0.02:
            self.pca.switch(in1, False); self.pca.switch(in2, False); self.pca._set(pwm, 0, 0x1000)
            return
        self.pca.switch(in1, s > 0); self.pca.switch(in2, s < 0)
        self.pca._set(pwm, 0, max(0, min(4095, int(abs(s) * 4095))))

    def stop_now(self):
        """motors off at once (error, program end) - the PCA9685 keeps its last value by itself otherwise"""
        MOVER.update(v=0.0, w=0.0, l=0.0, r=0.0)
        if self.pca is not None:
            try:
                pins = MOVER_MAP.get(CFG["mover_driver"], MOVER_MAP["adafruit"])
                self._motor(pins[0], 0.0); self._motor(pins[1], 0.0)
            except Exception:
                pass

    def loop(self):
        atexit.register(self.stop_now)
        while True:                                     # 2.95.34: an error stops the motors, then the loop goes on
            try:
                self._loop()
            except Exception as e:
                self.stop_now()
                log_event("sys", f"Mover error - motors stopped: {type(e).__name__}: {e}"[:200])
                time.sleep(2)

    def _loop(self):
        last = time.monotonic()
        while True:
            time.sleep(0.05)
            # 2.95.34: monotonic clock - a clock set back (phone time) made a negative step = full speed ahead
            now = time.monotonic(); dt = max(0.0, min(0.2, now - last)); last = now
            sim = bool(CFG.get("sim_on"))
            if CFG["mover_mode"] == "off":
                self._close(); MOVER.update(avail=False, hw=False, test=False, msg="off")
            elif sim:
                self._close(); MOVER["hw"] = False
                real = bool(SIM.get("ok")) and bool(SIM.get("mover"))
                MOVER["avail"] = real or bool(CFG.get("mover_sim_show"))        # stick for a look even without a mover (2.94.4)
                MOVER["test"] = MOVER["avail"] and not real
                MOVER["msg"] = "simulated" if real else ("stick shown for testing (the simulator has no mover)" if MOVER["avail"] else "the simulator has no mover")
            else:
                MOVER["test"] = False
                if self.pca is None and time.time() >= self.next_look:
                    self.next_look = time.time() + 15.0
                    self._find()
                MOVER["hw"] = self.pca is not None; MOVER["avail"] = MOVER["hw"]
            MOVER["sim"] = sim and MOVER["avail"]
            # target from the stick (stops by itself without new commands), gentle change
            fresh = now - MOVER["cmd_t"] < 0.6
            tv = MOVER["v"] if fresh and MOVER["avail"] else 0.0
            tw = MOVER["w"] if fresh and MOVER["avail"] else 0.0
            sp = float(CFG["mover_speed"]) / 100.0; tu = float(CFG["mover_turn"]) / 100.0
            tl, trr = tv * sp + tw * tu, tv * sp - tw * tu
            m = max(1.0, abs(tl), abs(trr)); tl /= m; trr /= m
            ramp = float(CFG["mover_ramp"])
            k = 1.0 if ramp <= 0.01 else dt / ramp
            stop_fast = not fresh                                  # connection gone: stop quickly (4 × faster)
            k2 = max(0.0, min(1.0, k * (4.0 if stop_fast else 1.0)))
            l = MOVER["l"] + max(-k2, min(k2, tl - MOVER["l"]))
            r = MOVER["r"] + max(-k2, min(k2, trr - MOVER["r"]))
            MOVER["l"], MOVER["r"] = round(l, 3), round(r, 3)
            if self.pca is not None and not sim:
                ml, mr = l, r
                if CFG["mover_swap"]:
                    ml, mr = mr, ml
                if CFG["mover_inv_l"]:
                    ml = -ml
                if CFG["mover_inv_r"]:
                    mr = -mr
                pins = MOVER_MAP.get(CFG["mover_driver"], MOVER_MAP["adafruit"])
                try:
                    self._motor(pins[0], ml); self._motor(pins[1], mr)
                except OSError as e:
                    MOVER["msg"] = "motor driver: " + str(e)[:60]; self._close()


# ----------------------------------------------------------------------------
# Lights: white + infrared (850 nm), each on a PCA9685 channel or a GPIO (with a MOSFET). Off / On / Auto.
#   Auto: "dark" = the whole night (sunset - sunrise from latitude / longitude), "alarm_dark" = after an alarm, only at night,
#   "alarm" = after an alarm, day and night. An alarm = person, warm body or noise while armed; the light stays on light_hold s.
# ----------------------------------------------------------------------------
LIGHTS = {"alarm_t": 0.0, "dark": False, "dark_t": 0.0, "strobe_until": 0.0}
# ---- Disco light (2.95.54): the white light flashes with the music - the beats from the microphone (music of a Bluetooth box
# or a phone nearby) or a fixed tempo. At most 3 flashes a second (flashing light can trigger seizures), alarms always first,
# ends by itself after the set time. ----
DISCO = {"on": False, "until": 0.0, "mode": "music", "bpm": 120, "avg": None, "last": 0.0, "flash_until": 0.0, "beats": 0, "t0": 0.0}


def disco_set(on, mode=None, bpm=None, minutes=None, who="web"):
    if mode in ("music", "tempo"):
        DISCO["mode"] = mode
    if bpm is not None:
        DISCO["bpm"] = int(max(60, min(170, int(bpm))))
    if on:
        DISCO.update(on=True, until=time.time() + 60 * max(5, min(480, int(minutes or 120))), avg=None, beats=0, t0=time.time())
        log_event("relay", f"Disco light on ({DISCO['mode']}, {who})")
    elif DISCO["on"]:
        DISCO["on"] = False
        log_event("relay", f"Disco light off ({who})")


def _disco_white(now):
    """True / False while the disco light runs, None = not running"""
    if not DISCO["on"]:
        return None
    if now > DISCO["until"]:
        DISCO["on"] = False
        return None
    gap = 1.0 / 3.0                                       # never faster than 3 flashes a second
    if DISCO["mode"] == "tempo":
        per = max(gap, 60.0 / max(60, DISCO["bpm"]))
        ph = ((now - DISCO["t0"]) % per) / per
        return ph < 0.35
    lv = (STATE.get("audio") or {}).get("level")
    if lv is None:                                        # no microphone: the tempo instead
        per = 60.0 / max(60, DISCO["bpm"])
        return ((now - DISCO["t0"]) % per) / per < 0.35
    a = DISCO["avg"]
    DISCO["avg"] = lv if a is None else a * 0.96 + lv * 0.04
    if a is not None and lv > a + 4.0 and now - DISCO["last"] > gap:
        DISCO["last"] = now; DISCO["flash_until"] = now + 0.14; DISCO["beats"] += 1
    return now < DISCO["flash_until"]


def disco_state():
    return {"on": DISCO["on"], "mode": DISCO["mode"], "bpm": DISCO["bpm"], "left": max(0, int(DISCO["until"] - time.time())) if DISCO["on"] else 0,
            "beats": DISCO["beats"], "mic": (STATE.get("audio") or {}).get("level") is not None, "white": bool(CFG.get("light_white_out")) or bool(CFG.get("sim_on"))}
LIGHT_MODES = ("off", "on", "auto")
LIGHT_NAMES = {"white": "White light", "ir": "Infrared light"}


def is_dark():
    if CFG.get("sim_on") and time.time() - SIM["t"] < 10:
        return bool(SIM["dark"])                           # the simulated world decides day and night
    now = time.time()
    if now - LIGHTS["dark_t"] > 60:
        LIGHTS["dark_t"] = now
        try:
            d = datetime.now()
            st = sun_times(d.date(), float(CFG["latitude"]), float(CFG["longitude"]))
            if isinstance(st, str):
                LIGHTS["dark"] = st == "dark"
            else:
                m = d.hour * 60 + d.minute
                LIGHTS["dark"] = m < st[0] or m > st[1]
        except Exception:
            pass
    return LIGHTS["dark"]


def light_alarm():
    LIGHTS["alarm_t"] = time.time()


def lights_tick():
    now = time.time(); dark = is_dark()
    alarm = LIGHTS["alarm_t"] > 0 and now - LIGHTS["alarm_t"] < float(CFG["light_hold"])
    res = {}
    for n in ("white", "ir"):
        if PAUSING["on"]:
            res[n] = False; continue
        m, a = CFG["light_" + n], CFG[f"light_{n}_auto"]
        res[n] = (bool(CFG[f"light_{n}_out"]) or bool(CFG["sim_on"])) and (m == "on" or (m == "auto" and (
            (a == "dark" and dark) or (a == "alarm_dark" and alarm and dark) or (a == "alarm" and alarm))))
    strobe = now < LIGHTS.get("strobe_until", 0.0) and not PAUSING["on"]
    dw = _disco_white(now)
    disco = dw is not None and not alarm and not strobe and not PAUSING["on"] and (CFG["light_white_out"] or CFG["sim_on"])
    if disco:
        res["white"] = dw                                  # disco: the white light with the music (alarms first)
    if strobe and CFG["light_white_out"]:
        res["white"] = int(now * 5) % 2 == 0                 # deterrence: white light flashes 2.5 times a second
    prev = STATE.get("lights") or {}
    for n in ("white", "ir"):
        if bool(prev.get(n)) != res[n] and not ((strobe or disco) and n == "white"):
            log_event("relay", f"{LIGHT_NAMES[n]} {'ON' if res[n] else 'OFF'}")
    STATE["lights"] = dict(res, dark=dark)
    return res


def light_set(name, mode):
    if name not in ("white", "ir") or mode not in LIGHT_MODES:
        return False, "invalid value"
    CFG["light_" + name] = mode
    save_settings()
    return True, ""


def light_out_pairs(name):
    """Where a light is connected: a free PCA9685 channel or a free GPIO (not a servo, relay or thermal camera pin)."""
    other = CFG["light_ir_out" if name == "white" else "light_white_out"]
    pairs = [("", "– " + tr("not connected") + " –")]
    used_ch = {int(CFG["pca_pan_ch"]), int(CFG["pca_tilt_ch"])}
    pairs += [(f"pca:{c}", f"PCA9685 {tr('channel')} {c}") for c in range(16) if c not in used_ch and f"pca:{c}" != other]
    used = {r["gpio"] for r in RELAYS} | set(GPIO_RESERVED) | set(thermal_gpios())
    pairs += [(f"gpio:{g}", f"GPIO {g}") for g in sorted(FREE_GPIOS) if g not in used and f"gpio:{g}" != other]
    cur = CFG[f"light_{name}_out"]
    if cur and cur not in [p[0] for p in pairs]:
        pairs.append((cur, cur.replace("pca:", "PCA9685 ").replace("gpio:", "GPIO ")))
    return pairs


def thermal_gpios():
    """GPIOs of the Waveshare thermal camera (reset, data ready, chip select) while it is selected."""
    return (23, 24, 7) if str(CFG.get("thermal_source", "")).startswith("senxor") else ()


