#@ Motion Watch – Teil 100: Akku / USV, Systemüberwachung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# UPS HAT (Waveshare, 2 x 18650 in series = 2S, 6.0 ... 8.4 V): an INA219 on I2C (0x42) measures the battery voltage and
# the current (shunt 0.1 ohm). Only reads - nothing is written to the chip. Negative current = the battery delivers.
# ----------------------------------------------------------------------------
_CELL_CURVE = [(3.00, 0), (3.30, 5), (3.50, 15), (3.60, 28), (3.70, 45), (3.80, 60), (3.90, 72), (4.00, 83), (4.10, 93), (4.20, 100)]


def cell_pct(v):
    if v <= _CELL_CURVE[0][0]:
        return 0
    for (v0, p0), (v1, p1) in zip(_CELL_CURVE, _CELL_CURVE[1:]):
        if v <= v1:
            return int(round(p0 + (p1 - p0) * (v - v0) / (v1 - v0)))
    return 100


def ups_read(addr, bus=1):
    """(battery voltage V, current A) from the INA219, or None (no chip / no I2C)."""
    import fcntl
    try:
        fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        def reg(r):
            os.write(fd, bytes([r])); b = os.read(fd, 2)
            return (b[0] << 8) | b[1]
        bus_raw, sh = reg(0x02), reg(0x01)
        if sh & 0x8000:
            sh -= 0x10000
        volt = (bus_raw >> 3) * 0.004
        amps = sh * 0.00001 / 0.1
        if not (2.0 <= volt <= 9.5):                      # not a battery pack (or another chip at this address)
            return None
        return volt, (-amps if CFG["ups_invert"] else amps)
    except OSError:
        return None
    finally:
        os.close(fd)


def ups_read_e(addr=0x2D, bus=1):
    """Waveshare UPS HAT (E): a battery chip at I2C 0x2D (16-bit values, low byte first). None = not there / implausible.
    0x00 ID (0x0A), 0x02 state (0x80 charging, 0x40 fast charging, 0x20 power at the input, bits 0-2: 5 = full),
    0x10 USB-C input mV / mA, 0x20 battery mV, mA (signed, + = charging, - = discharging),
    %, remaining mAh, minutes left (discharging), minutes to full (charging), 0x30 the four cell voltages (mV)."""
    import fcntl
    try:
        fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        def blk(reg, n):
            os.write(fd, bytes([reg])); return os.read(fd, n)
        u = lambda b, i: b[i] | (b[i + 1] << 8)
        if blk(0x00, 1)[0] != 0x0A:
            return None                                       # not the UPS HAT (E)
        st = blk(0x02, 1)[0]; vb = blk(0x10, 6); bt = blk(0x20, 12); cl = blk(0x30, 8)
        cur = u(bt, 2)
        if cur > 0x7FFF:
            cur -= 0x10000
        r = {"state": st, "vbus": u(vb, 0) / 1000.0, "vbus_a": u(vb, 2) / 1000.0, "v": u(bt, 0) / 1000.0, "a": cur / 1000.0,
             "pct": u(bt, 4), "mah": u(bt, 6), "min_left": u(bt, 8), "min_full": u(bt, 10), "cells": [u(cl, i) / 1000.0 for i in (0, 2, 4, 6)]}
        if not (6.0 <= r["v"] <= 17.6) or r["pct"] > 100:
            return None                                       # another chip at this address
        return r
    except (OSError, IndexError):
        return None
    finally:
        os.close(fd)


class BatteryMonitor:
    """Estimates what is left in the powerbank: capacity (mAh on the label) x 3.7 V x 85 % usable, minus what the Pi used
    since 'Battery full' was pressed. Power = Pi power chip (or an estimate from the CPU load) + extra devices + lights."""
    def __init__(self):
        self.hist = deque(maxlen=60)     # watts, last 10 minutes (every 10 s)
        self.uhist = deque(maxlen=6)     # UPS: voltage / current, last minute
        self._t = time.time(); self._save_t = time.time()
        threading.Thread(target=self.loop, daemon=True).start()

    def watts(self):
        p = _pmic_watts()
        src = "pmic"
        if p is None:
            cpu = STATE.get("cpu") or 0.0
            p = 2.7 + 3.3 * min(100.0, cpu) / 100.0; src = "estimate"
        else:
            p *= 1.15                    # the power chip does not see USB devices, losses
        L = STATE.get("lights") or {}
        p += float(CFG["batt_extra_w"]) + (0.6 if L.get("white") else 0.0) + (0.6 if L.get("ir") else 0.0)
        return p, src

    def loop(self):
        while True:
            time.sleep(10)
            try:
                self.tick()
            except Exception as e:
                log_event("sys", f"Battery estimate: {e}")

    def ups_tick(self):
        """UPS HAT found: charge from the battery voltage, time left from the measured power. Power cut / back,
        warning at 20 %, shutdown at <ups_shutdown_pct> % so the memory card is not damaged."""
        model = CFG["ups_model"]
        if model in ("auto", "e"):
            e = ups_read_e()
            if e is not None:
                return self.ups_e(e)
            if model == "e":
                r = None
        if model != "e":
            try:
                addr = int(str(CFG["ups_addr"]), 16)
            except ValueError:
                addr = 0x42
            r = ups_read(addr)
        if r is None:
            self._ups_miss = getattr(self, "_ups_miss", 0) + 1
            return self._ups_miss < 3 and getattr(self, "_ups_seen", False)      # keep the last values for a short hiccup
        self._ups_miss = 0
        if not getattr(self, "_ups_seen", False):
            self._ups_seen = True; log_event("sys", f"UPS HAT found (I2C {CFG['ups_addr']}): battery {r[0]:.2f} V")
        volt, amps = r
        self.uhist.append((volt, amps))
        v = sum(x[0] for x in self.uhist) / len(self.uhist); a = sum(x[1] for x in self.uhist) / len(self.uhist)
        on_batt = a < -0.10; charging = a > 0.05
        pct = cell_pct(v / 2.0)
        watts = v * abs(a)
        cap_wh = float(CFG["ups_mah"]) / 1000.0 * 7.4 * 0.9
        hours = (pct / 100.0 * cap_wh / max(0.8, watts)) if on_batt else None
        STATE["battery"] = {"on": True, "src": "ups", "model": "ina", "pct": pct, "hours": None if hours is None else round(hours, 1),
                            "cap_wh": round(cap_wh, 1), "use_w": round(watts if on_batt else self.watts()[0], 1), "watts": round(watts, 1), "volt": round(v, 2), "amps": round(a, 2), "on_battery": on_batt,
                            "charging": charging}
        return self.ups_events(v, pct, hours, on_batt, 5.5 <= v <= 8.9)

    def ups_e(self, r):
        """UPS HAT (E): its battery chip knows the charge, the time left and whether it charges."""
        if not getattr(self, "_ups_seen", False):
            self._ups_seen = True
            log_event("sys", f"UPS HAT (E) found (I2C 0x2D): battery {r['v']:.2f} V, {r['pct']} %, cells " + " / ".join(f"{c:.2f}" for c in r["cells"]) + " V")
        self._ups_miss = 0
        st = r["state"]
        charging = bool(st & 0x80) and (st & 0x07) != 5
        on_batt = not (st & 0x20) and r["a"] <= 0.05             # no power at the input: the Pi runs on the cells
        v, a, pct = r["v"], r["a"], int(r["pct"])
        watts = v * abs(a)
        cap_wh = (r["mah"] / max(1.0, pct) * 100.0 / 1000.0 * v * 0.9) if r["mah"] and pct else 0.0
        hours = round(r["min_left"] / 60.0, 1) if on_batt and r["min_left"] and r["min_left"] < 0xFFFF else (
            round(pct / 100.0 * cap_wh / max(0.8, watts), 1) if on_batt and cap_wh else None)
        STATE["battery"] = {"on": True, "src": "ups", "model": "e", "pct": pct, "hours": hours, "cap_wh": round(cap_wh, 1),
                            "use_w": round(watts if on_batt else self.watts()[0], 1), "watts": round(watts, 1), "volt": round(v, 2),
                            "amps": round(a, 2), "on_battery": on_batt, "charging": charging, "fast": bool(st & 0x40), "full": (st & 0x07) == 5,
                            "cells": [round(c, 2) for c in r["cells"]], "vbus": round(r["vbus"], 2), "mah": r["mah"],
                            "full_min": r["min_full"] if charging and r["min_full"] < 0xFFFF else None}
        cl = [c for c in r["cells"] if c > 0.5]
        if cl and max(cl) - min(cl) > 0.3 and not getattr(self, "_cell_warn", False):
            self._cell_warn = True
            log_event("sys", "UPS HAT (E): the cells are uneven (" + " / ".join(f"{c:.2f}" for c in r["cells"]) + " V) - check the batteries")
        return self.ups_events(v, pct, hours, on_batt, 9.0 <= v <= 17.6)

    def ups_events(self, v, pct, hours, on_batt, volt_ok):
        """Power cut / back, almost empty, clean shutdown - the same for every UPS HAT."""
        w = WATCH_REF["w"]; de = CFG["lang"] == "de"
        def push(text_en, **kw):
            if w is not None and CFG["ups_push"]:
                w.notifier.info(trf(text_en, **kw), title="{name}: " + tr("power"))
        was = getattr(self, "_on_batt", None)
        if was is not None and on_batt != was:
            if on_batt:
                log_event("sys", f"Power cut - running on the battery ({pct} %, {v:.2f} V)")
                if CFG["tamper_power"] and is_armed() and TAMPER is not None:
                    TAMPER.alarm("power")                    # armed: a cut cable can mean theft
                else:
                    push("Power cut – running on the battery ({pct} %)", pct=pct)
            else:
                log_event("sys", f"Mains power back - battery {pct} %")
                push("Power back – battery {pct} %", pct=pct)
                CFG["batt_warned"] = False
        self._on_batt = on_batt
        if on_batt and pct <= 20 and not CFG["batt_warned"]:
            CFG["batt_warned"] = True; save_settings()
            log_event("sys", f"Battery almost empty (about {pct} %, {hours or 0:.1f} h left)")
            push("Battery almost empty: about {pct} % ({hours:.1f} h)", pct=pct, hours=hours or 0)
        lim = int(CFG["ups_shutdown_pct"])
        plausible = volt_ok and time.time() - RUNGUARD["t0"] > 180            # a real battery value; never in the first 3 minutes
        self._low = (getattr(self, "_low", 0) + 1) if (on_batt and lim > 0 and pct <= lim and plausible) else 0
        if getattr(self, "_shut", False) and not POWER.get("pending") and time.time() - getattr(self, "_shut_t", 0) > 300:
            self._shut = False                           # 2.95.34: the shutdown did not happen (rights?) - try again
        if self._low >= 3 and not POWER.get("pending") and not getattr(self, "_shut", False):   # 30 s below the limit
            self._shut = True; self._shut_t = time.time()
            log_event("sys", f"Battery empty ({pct} %, {v:.2f} V) - shutting down the Pi to protect the memory card")
            push("Battery empty – the Pi shuts down cleanly")
            power_action("poweroff", source="battery")
        return True

    def tick(self):
        now = time.time(); dt = min(60.0, now - self._t); self._t = now
        if CFG["ups_on"] and self.ups_tick():
            return
        cap_wh = float(CFG["batt_mah"]) * 3.7 / 1000.0 * 0.85
        if cap_wh <= 0:
            STATE["battery"] = {"on": False}
            return
        p, src = self.watts(); self.hist.append(p)
        if CFG["batt_full_t"]:
            CFG["batt_used_wh"] = float(CFG["batt_used_wh"]) + p * dt / 3600.0
            sw = (STATE.get("solar") or {}).get("w") if CFG["solar_on"] else None
            if sw:                                        # the panel charges the powerbank (about 85 % arrives)
                CFG["batt_used_wh"] = max(0.0, float(CFG["batt_used_wh"]) - sw * 0.85 * dt / 3600.0)
        avg = sum(self.hist) / len(self.hist)
        left = max(0.0, cap_wh - float(CFG["batt_used_wh"])) if CFG["batt_full_t"] else None
        pct = None if left is None else int(round(100.0 * left / cap_wh))
        hours = None if left is None else left / max(0.5, avg)
        STATE["battery"] = {"on": True, "watts": round(avg, 1), "use_w": round(avg, 1), "src": src, "pct": pct,
                            "hours": None if hours is None else round(hours, 1), "since": CFG["batt_full_t"], "cap_wh": round(cap_wh, 1)}
        if now - self._save_t > 300:
            self._save_t = now; save_settings()
        if pct is not None and pct <= 15 and not CFG["batt_warned"]:
            CFG["batt_warned"] = True; save_settings()
            log_event("sys", f"Battery almost empty (about {pct} %, {hours:.1f} h left)")
            w = WATCH_REF["w"]
            if w is not None:
                de = CFG["lang"] == "de"
                w.notifier.info(trf("Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap", pct=pct, hours=hours),
                                title="{name}: " + tr("battery"))


def battery_full():
    CFG["batt_full_t"] = time.time(); CFG["batt_used_wh"] = 0.0; CFG["batt_warned"] = False
    save_settings(); log_event("sys", "Battery marked as full")
    return True, ""


class SysMonitor:
    def __init__(self):
        self.hist = deque(maxlen=60)          # last 60 seconds
        self._prev = None
        try:
            import psutil
            self.ps = psutil
            psutil.cpu_percent(percpu=True)   # first call only primes the counters
        except ImportError:
            self.ps = None
            log_event("sys", "psutil not installed - using /proc/stat (pip install psutil recommended)")
        STATE["cpu_count"] = os.cpu_count() or 1
        threading.Thread(target=self.loop, daemon=True).start()

    def _cpu(self):
        if self.ps:
            per = self.ps.cpu_percent(percpu=True)
            return sum(per) / len(per) if per else 0.0
        try:                                   # Linux fallback without psutil
            with open("/proc/stat") as f:
                vals = [int(v) for v in f.readline().split()[1:]]
        except Exception:
            return None
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals[:8])
        prev, self._prev = self._prev, (idle, total)
        if prev is None or total <= prev[1]:
            return 0.0
        return max(0.0, min(100.0, 100.0 * (1.0 - (idle - prev[0]) / (total - prev[1]))))

    def _shares(self):
        """CPU of Motion Watch itself and of the 3D simulator (when it runs on the same computer), in % of the whole
        computer like «cpu» - shown in the small box of the simulator (sim_state «cpu»)."""
        if not self.ps:
            STATE["cpu_mw"] = STATE["cpu_sim"] = None
            return
        n = max(1, STATE.get("cpu_count") or 1)
        try:
            if getattr(self, "me", None) is None:
                self.me = self.ps.Process()
                self.me.cpu_percent(None)
            STATE["cpu_mw"] = round(self.me.cpu_percent(None) / n, 1)
        except Exception:
            STATE["cpu_mw"] = None
        pid = int(SIM.get("pid") or 0) if CFG.get("sim_on") else 0
        if pid <= 0:
            self.sim_p = None
            STATE["cpu_sim"] = None
            return
        try:
            p = getattr(self, "sim_p", None)
            if p is None or p.pid != pid:
                p = self.ps.Process(pid)
                if "motionwatch3d" not in p.name().lower():      # same number on another computer: not our simulator
                    raise ValueError("other process")
                self.sim_p = p
                p.cpu_percent(None)
                STATE["cpu_sim"] = None
                return
            STATE["cpu_sim"] = round(p.cpu_percent(None) / n, 1)
        except Exception:
            self.sim_p = None
            STATE["cpu_sim"] = None
            SIM["pid"] = 0                     # the simulator runs elsewhere (or ended): do not try again

    def _temp(self):
        try:                                   # Raspberry Pi / most Linux boards
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return int(f.read().strip()) / 1000.0
        except Exception:
            pass
        if self.ps and hasattr(self.ps, "sensors_temperatures"):
            try:
                for entries in self.ps.sensors_temperatures().values():
                    if entries:
                        return float(entries[0].current)
            except Exception:
                pass
        return None

    # ---- power supply (Pi: under-voltage) + free space on the memory card ----
    def _read_supply(self):
        out = {"volt": None, "uv_now": False, "uv_boot": False, "throttled": False, "known": False}
        if shutil.which("vcgencmd"):
            rc, txt, _e = _run(["vcgencmd", "get_throttled"], timeout=5)
            m = re.search(r"0x([0-9a-fA-F]+)", txt or "")
            if rc == 0 and m:
                v = int(m.group(1), 16)
                out.update(known=True, uv_now=bool(v & 0x1), throttled=bool(v & 0x6), uv_boot=bool(v & 0x10000))
            rc, txt, _e = _run(["vcgencmd", "pmic_read_adc", "EXT5V_V"], timeout=5)        # Pi 5: voltage at the USB-C input
            m = re.search(r"=\s*([0-9.]+)\s*V", txt or "")
            if rc == 0 and m:
                out["volt"] = round(float(m.group(1)), 2)
        if not out["known"]:
            for d in glob.glob("/sys/class/hwmon/hwmon*"):
                try:
                    with open(os.path.join(d, "name")) as f:
                        if f.read().strip() != "rpi_volt":
                            continue
                    with open(os.path.join(d, "in0_lcrit_alarm")) as f:
                        out.update(known=True, uv_now=f.read().strip() == "1")
                except OSError:
                    pass
        return out

    def _supply_disk(self):
        now = time.time()
        if now - getattr(self, "_sd_t", 0.0) < 10.0:
            return
        self._sd_t = now
        w = WATCH_REF["w"]; de = CFG["lang"] == "de"
        sup = self._read_supply(); STATE["supply"] = sup
        if sup["uv_now"]:
            self._uv_last = now
            if not getattr(self, "uv_warned", False):
                self.uv_warned = True
                log_event("sys", "UNDER-VOLTAGE: the power bank / cable delivers too little" + (f" ({sup['volt']} V)" if sup["volt"] else ""))
                if w is not None:
                    w.notifier.info(tr("Under-voltage: power bank almost empty or cable too weak") + (f" ({sup['volt']} V)" if sup["volt"] else ""),
                                    title="{name}: " + tr("power"))
        elif getattr(self, "uv_warned", False) and now - getattr(self, "_uv_last", 0.0) > 600:
            self.uv_warned = False
        try:
            du = shutil.disk_usage(rec_dir() if os.path.isdir(rec_dir()) else DATA_DIR)
            free = int(du.free / 1024 ** 2); STATE["disk"] = {"free_mb": free, "total_mb": int(du.total / 1024 ** 2)}
            try:
                dk = _dev_kind(_mount_of(rec_dir() if os.path.isdir(rec_dir()) else DATA_DIR)[0])
            except Exception:
                dk = "other"
            STATE["disk"]["kind"] = dk
        except OSError:
            return
        lim = float(CFG["disk_warn_mb"])
        if free < lim and not getattr(self, "disk_warned", False):
            self.disk_warned = True
            log_event("sys", f"Memory card almost full: {free} MB free")
            if w is not None:
                w.notifier.info(trf("Memory card almost full: {free} MB free - the oldest recordings are deleted", free=free),
                                title="{name}: " + tr("memory"))
        elif free > lim * 1.5:
            self.disk_warned = False
        if free < 300 and w is not None and now - getattr(self, "_clean_t", 0.0) > 60:
            self._clean_t = now
            w.cleanup_recordings()                  # makes room: oldest recordings first (never favourites)

    def loop(self):
        while True:
            time.sleep(1.0)
            cpu = self._cpu()
            temp = self._temp()
            if cpu is not None:
                self.hist.append(round(cpu, 1))
            STATE["mem"] = mem_info()
            STATE.update(cpu=None if cpu is None else round(cpu, 1),
                         cpu_temp=None if temp is None else round(temp, 1),
                         cpu_hist=list(self.hist))
            self._shares()
            self._supply_disk()
            if time.time() - MODE_RT["checked"] > 10.0:
                MODE_RT["checked"] = time.time()
                try:
                    mode_tick()
                    simpi_tick()
                    helper_tick()
                except Exception as e:
                    log_event("sys", "mode check: " + str(e)[:80])
            if temp is not None:
                lim = float(CFG["temp_warn"])
                if temp >= lim and not getattr(self, "warned", False):
                    self.warned = True
                    log_event("sys", f"CPU hot: {temp:.0f} °C (limit {lim:.0f} °C) - check the cooling / ventilation")
                    w = WATCH_REF["w"]
                    if w is not None:
                        de = CFG["lang"] == "de"
                        w.notifier.info(trf("Pi too hot: {temp:.0f} °C (limit {lim:.0f} °C) - check the cooling / ventilation", temp=temp, lim=lim),
                                        title="{name}: " + tr("temperature"))
                elif temp < lim - 5:
                    self.warned = False


