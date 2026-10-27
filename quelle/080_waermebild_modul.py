#@ Motion Watch – Teil 080: Treiber Wärmebild-Modul, Klasse Hardware. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Waveshare Thermal-90 / Thermal-44 (80 x 62, Meridian MI48 "SenXor"): SPI for the pictures, I2C (0x40) for the settings,
#   GPIO 23 = reset, 24 = data ready, 7 = chip select. Uses the driver of Waveshare (pysenxor, from their wiki:
#   Thermal_Camera_Hat.zip -> pysenxor-master -> pip install -e ./). /boot/firmware/config.txt: dtparam=spi=on +
#   dtoverlay=spi0-0cs, I2C on. The picture is the temperature in degrees per pixel (float).
# ----------------------------------------------------------------------------
class SenxorSource:
    size = (80, 62)

    def __init__(self, i2c_addr=0x40, fps=15):
        try:
            from senxor.mi48 import MI48
            from senxor.interfaces import SPI_Interface, I2C_Interface
            from senxor.utils import data_to_frame
        except ImportError:
            raise RuntimeError("Waveshare driver missing: Thermal_Camera_Hat.zip from the Waveshare wiki, "
                               "then in pysenxor-master: pip install -e ./")
        try:
            from smbus import SMBus
        except ImportError:
            from smbus2 import SMBus
        from spidev import SpiDev
        from gpiozero import DigitalInputDevice, DigitalOutputDevice
        self._to_frame = data_to_frame
        self.cs = DigitalOutputDevice("BCM7", active_high=False, initial_value=False)
        self.ready = DigitalInputDevice("BCM24", pull_up=False)
        self.rst = DigitalOutputDevice("BCM23", active_high=False, initial_value=True)
        spi = SPI_Interface(SpiDev(0, 0), xfer_size=160)
        spi.device.mode = 0b00; spi.device.lsbfirst = False; spi.device.bits_per_word = 8
        spi.device.max_speed_hz = 31200000; spi.device.cshigh = True
        i2c = I2C_Interface(SMBus(1), i2c_addr)
        rst = self.rst

        def reset():
            rst.on(); time.sleep(0.000035); rst.off(); time.sleep(0.05)
        self.mi48 = MI48([i2c, spi], data_ready=self.ready, reset_handler=reset)
        try:
            self.mi48.set_fps(fps)
        except Exception:
            pass
        try:
            if int(str(self.mi48.fw_version[0])) >= 2:
                self.mi48.enable_filter(f1=True, f2=True, f3=False)
                self.mi48.set_offset_corr(0.0)
        except Exception:
            pass
        self.mi48.start(stream=True, with_header=True)
        self.shape = getattr(self.mi48, "fpa_shape", (80, 62))

    def read(self):
        try:
            if not self.ready.wait_for_active(timeout=1.0):
                return False, None
            self.cs.on(); time.sleep(0.0001)
            data, _header = self.mi48.read()
            time.sleep(0.0001); self.cs.off()
        except Exception:
            try:
                self.cs.off()
            except Exception:
                pass
            return False, None
        if data is None:
            return False, None
        fr = np.asarray(self._to_frame(data, self.shape), dtype=np.float32)
        if fr.size and float(np.median(fr)) > 200:          # deci-Kelvin -> degrees Celsius (older driver versions)
            fr = fr / 10.0 - 273.15
        STATE["thermal_max"] = round(float(np.max(fr)), 1)
        return True, fr

    def release(self):
        for f in (lambda: self.mi48.stop(), self.cs.close, self.ready.close, self.rst.close):
            try:
                f()
            except Exception:
                pass


HW_REINIT = {"want": False}


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
                self.pan = Servo(GPIO_PAN, min_pulse_width=mn, max_pulse_width=mx)
                self.tilt = Servo(GPIO_TILT, min_pulse_width=mn, max_pulse_width=mx)
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

    def _servos(self, pan, tilt):
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

    def _write(self, gpio, on, al):
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
                if self.pca is not None and prev != (out, on):
                    try:
                        self.pca.switch(int(out[4:]), on); self._pca_lights[n] = (out, on)
                    except Exception as e:
                        log_event("servo", f"Light error: {e}")
            elif out.startswith("gpio:"):
                g = int(out[5:])
                if g not in wanted:
                    wanted[g] = (on, False)

    def loop(self):
        """50 Hz: push pan/tilt, all relay states and the lights to the hardware when they change."""
        while True:
            if HW_REINIT["want"]:
                HW_REINIT["want"] = False
                try:
                    self._init_backend()
                except Exception as e:
                    log_event("servo", f"Servo driver: {e}")
            (plo, phi), (tlo, thi) = self.limits()
            pan = max(plo, min(phi, float(CFG["pan"])))
            tilt = max(tlo, min(thi, float(CFG["tilt"])))
            if abs(pan - CFG["pan"]) > 0.05:
                CFG["pan"] = round(pan, 2)                # the page / window shows where the camera really is
            if abs(tilt - CFG["tilt"]) > 0.05:
                CFG["tilt"] = round(tilt, 2)
            cur = (round(pan, 1), round(tilt, 1))
            if cur != self._last_servo:
                try:
                    self._servos(pan, tilt)
                except Exception as e:
                    log_event("servo", f"Servo error: {e}")
                self._last_servo = cur; SERVO_MOVE["t"] = time.time()
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




