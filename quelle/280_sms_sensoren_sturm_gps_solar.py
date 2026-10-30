#@ Motion Watch – Teil 280: SMS, Sensoren, Sturmwarnung, GPS, Solar. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# SMS over an LTE / UMTS stick: alarm as a text message - also where there is no internet (only mobile network).
#   Ways: ModemManager (mmcli, most sticks), AT commands on the serial port, or Huawei HiLink sticks (web API, 192.168.8.1).
#   Only alarms (person, sabotage, warm body, noise), at most one SMS every few minutes and 20 a day (costs!).
# ----------------------------------------------------------------------------
SMS_MODES = ("auto", "mmcli", "at", "hilink")
SMS = {"status": "", "sent": [], "last": 0.0}
_PHONE_RE = re.compile(r"^\+?[0-9]{6,16}$")


# ----------------------------------------------------------------------------
# Extra sensors: motion detector (PIR), door / lid contact (reed switch to GND) and gas / smoke module (digital output) on a
#   GPIO; 433 MHz radio sensors (RTL-SDR USB stick + rtl_433), Zigbee sensors (Zigbee2MQTT -> MQTT broker) and Bluetooth tags
#   (RuuviTag: its movement counter, or "out of range"). An alarm when armed (or always: gas); a PIR also wakes power saving.
# ----------------------------------------------------------------------------
SENS_KINDS = ("pir", "door", "gas", "tag", "other")
SENS_ALARMS = ("armed", "always", "off")
SENS_NAMES = {"pir": "Motion detector", "door": "Door", "gas": "Gas / smoke", "tag": "Tag", "other": "Sensor"}
MAX_SENSORS = 16
SENS = {"st": {}, "seen": {}, "pir_t": 0.0, "rf": "off", "ble": "off", "zb": "off", "ruuvi": {}, "lock": threading.Lock()}
_SENS_SRC = re.compile(r"^(sim:[\w .:+\-]{1,60}|gpio:\d{1,2}|rf:[\w .:+\-]{1,60}|zb:[\w .:+\-/]{1,60}|ble:[0-9A-F]{2}(:[0-9A-F]{2}){5})$")


def sens_used_gpios(skip=None):
    """GPIOs taken by servos, 1-Wire, I2C, relays, lights, the thermal camera and the other sensors."""
    used = set(GPIO_RESERVED) | {r["gpio"] for r in RELAYS} | set(thermal_gpios()) | {2, 3}
    for k in ("light_white_out", "light_ir_out"):
        v = str(CFG.get(k, ""))
        if v.startswith("gpio:") and v[5:].isdigit():
            used.add(int(v[5:]))
    for x in CFG.get("sensors", []):
        if x.get("id") != skip and str(x.get("src", "")).startswith("gpio:"):
            used.add(int(x["src"][5:]))
    if str(CFG.get("wind_gpio") or "").isdigit() and skip != "wind":
        used.add(int(CFG["wind_gpio"]))
    return used


def sens_free_gpios(skip=None):
    """Free GPIOs, the usual free pins first (GPIO 4 = 1-Wire temperature sensor comes last)."""
    used = sens_used_gpios(skip)
    order = [g for g in FREE_GPIOS if g != 4] + [g for g in range(5, 28) if g not in FREE_GPIOS] + [4]
    return [g for g in order if g not in used]


def sens_clean(lst):
    out, ids, gp = [], set(), set()
    for x in (lst if isinstance(lst, list) else [])[:MAX_SENSORS]:
        if not isinstance(x, dict):
            continue
        kind = x.get("kind") if x.get("kind") in SENS_KINDS else "other"
        src = str(x.get("src", "")).strip()
        if src[:4].lower() == "ble:":
            src = "ble:" + src[4:].upper()
        if src and not _SENS_SRC.match(src):
            src = ""
        if src.startswith("gpio:"):
            g = int(src[5:])
            if not 2 <= g <= 27 or g in gp:
                src = ""
            else:
                gp.add(g)
        sid = str(x.get("id", ""))
        if not re.fullmatch(r"[a-f0-9]{8}", sid) or sid in ids:
            sid = secrets.token_hex(4)
        ids.add(sid)
        name = re.sub(r"[\x00-\x1f]", "", str(x.get("name", ""))).strip()[:24] or SENS_NAMES[kind]
        alarm = x.get("alarm") if x.get("alarm") in SENS_ALARMS else ("always" if kind == "gas" else "armed")
        out.append({"id": sid, "name": name, "kind": kind, "src": src, "alarm": alarm, "inv": bool(x.get("inv", kind == "gas"))})
    return out


def sens_find(sid):
    return next((x for x in CFG["sensors"] if x["id"] == sid), None)


def sens_action(d, lang=None):
    """Web page / window: add, change, remove or test a sensor."""
    a = d.get("action")
    if a == "add":
        if len(CFG["sensors"]) >= MAX_SENSORS:
            return False, "at most 16 sensors"
        kind = d.get("kind") if d.get("kind") in SENS_KINDS else "other"
        src = str(d.get("src") or "")
        if not src and kind in ("pir", "door", "gas"):
            free = sens_free_gpios()
            src = f"gpio:{free[0]}" if free else ""
        n = sum(1 for x in CFG["sensors"] if x["kind"] == kind) + 1
        name = str(d.get("name") or "")[:24] or (tr(SENS_NAMES[kind], lang) + (f" {n}" if n > 1 else ""))
        CFG["sensors"] = sens_clean(CFG["sensors"] + [{"name": name, "kind": kind, "src": src}])
        CFG["sens_on"] = True
        if src.startswith("rf:"):
            CFG["rf433_on"] = True
        elif src.startswith("zb:"):
            CFG["zigbee_on"] = True
        elif src.startswith("ble:") or kind == "tag":
            CFG["ble_on"] = True
        save_settings(); return True, ""
    x = sens_find(str(d.get("id", "")))
    if x is None:
        return False, "unknown sensor"
    if a == "remove":
        CFG["sensors"] = [y for y in CFG["sensors"] if y["id"] != x["id"]]
        SENS["st"].pop(x["id"], None); save_settings(); return True, ""
    if a == "test":
        sens_fire(x, "test"); return True, ""
    if a != "set":
        return False, "unknown action"
    f, v = d.get("field"), d.get("value")
    if f == "name":
        v = re.sub(r"[\x00-\x1f]", "", str(v or "")).strip()[:24]
        if not v:
            return False, "invalid value"
    elif f == "kind":
        if v not in SENS_KINDS:
            return False, "invalid value"
    elif f == "alarm":
        if v not in SENS_ALARMS:
            return False, "invalid value"
    elif f == "inv":
        v = bool(v)
    elif f == "src":
        v = str(v or "").strip()
        if v[:4].lower() == "ble:":
            v = "ble:" + v[4:].upper()
        if v and not _SENS_SRC.match(v):
            return False, "invalid value"
        if v.startswith("gpio:") and int(v[5:]) not in sens_free_gpios(x["id"]):
            return False, "this GPIO is already in use"
    else:
        return False, "unknown setting"
    x[f] = v
    if f == "src":
        SENS["st"].pop(x["id"], None)
    CFG["sensors"] = sens_clean(CFG["sensors"]); save_settings()
    return True, ""


def sens_text(x, what, lang=None):
    if what == "test":
        return tr("test - it works", lang)
    if what == "missing":
        return tr("out of range (not seen any more)", lang)
    return tr({"pir": "motion detected", "door": "opened", "gas": "gas / smoke detected!", "tag": "moved"}.get(x["kind"], "triggered"), lang)


def sens_fire(x, what):
    """A sensor reported something: diary line, and (armed or 'always') push with the current picture, siren, recording."""
    now = time.time()
    st = SENS["st"].setdefault(x["id"], {"state": "ok", "last": 0.0, "cool": 0.0})
    st["last"] = now; st["what"] = what
    if x["kind"] == "pir" and what != "missing":
        SENS["pir_t"] = now                               # wakes power saving at once
    test = what == "test"
    alarm = test or x["alarm"] == "always" or (x["alarm"] == "armed" and is_armed())
    log_event("sys", f"Sensor «{x['name']}»: {sens_text(x, what, 'en')}" + ("" if alarm else " (no alarm)"))
    if not alarm or (not test and now - st.get("cool", 0.0) < 60):
        return
    st["cool"] = now
    w = WATCH_REF["w"]
    title = "{name}: " + (tr("GAS ALARM") if x["kind"] == "gas" else tr("SENSOR ALARM"))
    if test:
        title = "[Test] " + title
    if w is not None:
        w.notifier.alert(title, f"{x['name']}: {sens_text(x, what)}", w.frame_out)
    if test:
        return
    if not CFG.get("sim_on"):
        QUICK["rec_until"] = max(QUICK["rec_until"], now + 60)    # one minute of video of what happens now
    if x["kind"] == "gas" and not is_armed():
        if out_selected() and not SOUND["playing"] and TALK["proc"] is None:
            sound_play(None, None, None, reason="gas alarm")
    else:
        siren_alarm("sensor")


def sens_event(src, active, info=""):
    """A radio sensor (433 MHz, Zigbee, Bluetooth) sent something. active: True / False (contact closed again) / None = a pulse."""
    for x in CFG["sensors"] if CFG["sens_on"] else []:
        if x["src"] != src:
            continue
        st = SENS["st"].setdefault(x["id"], {"state": "unknown", "last": 0.0, "cool": 0.0})
        st["seen"] = time.time()
        if active is False:
            st["state"] = "ok"; continue
        if st.get("state") == "missing":
            log_event("sys", f"Sensor «{x['name']}»: back in range")
        if active is None:
            st["state"] = "pulse"; sens_fire(x, info or "active")
        elif st.get("state") != "active":                 # radio sensors report changes: every "open" counts
            st["state"] = "active"; sens_fire(x, "active")


def sens_seen(src, label, data=None):
    with SENS["lock"]:
        SENS["seen"][src] = {"label": str(label)[:80], "t": time.time(), "data": data or {}}
        if len(SENS["seen"]) > 60:
            for k in sorted(SENS["seen"], key=lambda k: SENS["seen"][k]["t"])[:len(SENS["seen"]) - 60]:
                SENS["seen"].pop(k, None)


def rf_message(d):
    """One line of rtl_433 (JSON). Contact sensors: closed / state / contact_open; motion detectors: motion / event."""
    model = re.sub(r"[^\w.+\-]", "_", str(d.get("model", "?")))[:30]
    dev = re.sub(r"[^\w.+\-]", "_", str(d.get("id", d.get("channel", d.get("code", "")))))[:20]
    src = f"rf:{model}:{dev}" if dev else f"rf:{model}"
    vals = {k: d[k] for k in ("closed", "state", "contact_open", "motion", "alarm", "tamper", "event", "temperature_C", "battery_ok") if k in d}
    sens_seen(src, f"{model} {dev}".strip(), vals)
    act = None
    if "contact_open" in d:
        act = bool(d["contact_open"])
    elif "closed" in d:
        act = not bool(d["closed"])
    elif str(d.get("state", "")).lower() in ("open", "opened", "closed", "close"):
        act = str(d["state"]).lower().startswith("open")
    elif "motion" in d:
        act = None if d["motion"] else False
    elif "temperature_C" in d and "alarm" not in d and "event" not in d:
        return                                            # a thermometer: only listed, no trigger
    sens_event(src, act)


def zb_message(name, payload):
    """A Zigbee2MQTT message (topic zigbee2mqtt/<name>). contact false = open, occupancy, smoke, gas, water_leak, vibration ..."""
    if name.startswith("bridge") or "/" in name:
        return
    try:
        d = json.loads(payload.decode(errors="replace"))
    except ValueError:
        return
    if not isinstance(d, dict):
        return
    src = "zb:" + name[:60]
    if not _SENS_SRC.match(src):
        return
    keys = ("contact", "occupancy", "smoke", "carbon_monoxide", "gas", "water_leak", "vibration", "tamper", "action")
    sens_seen(src, name, {k: d[k] for k in keys + ("battery", "temperature") if k in d})
    if "contact" in d:
        sens_event(src, not bool(d["contact"]))
    elif any(d.get(k) for k in ("smoke", "carbon_monoxide", "gas", "water_leak", "occupancy")):
        sens_event(src, True)
    elif any(k in d for k in ("smoke", "carbon_monoxide", "gas", "water_leak", "occupancy")):
        sens_event(src, False)
    elif d.get("vibration") or d.get("action"):
        sens_event(src, None)


def ruuvi_parse(b):
    """RuuviTag data format 5 (RAWv2): temperature, humidity, pressure, acceleration, battery, movement counter."""
    import struct
    if not b or len(b) < 18 or b[0] != 5:
        return None
    t, h, p, ax, ay, az, pw, mv, seq = struct.unpack(">hHHhhhHBH", bytes(b[1:18]))
    return {"t": round(t * 0.005, 1), "h": round(h * 0.0025), "p": round((p + 50000) / 100.0, 1), "acc": (ax, ay, az),
            "bat": round(((pw >> 5) + 1600) / 1000.0, 2), "moves": mv, "seq": seq}


def ble_message(mac, name, ruuvi_raw, rssi=None):
    src = "ble:" + str(mac).upper()
    if not _SENS_SRC.match(src):
        return
    r = ruuvi_parse(ruuvi_raw) if ruuvi_raw else None
    known = any(x["src"] == src for x in CFG["sensors"])
    if r is None and not name and not known:
        return                                            # anonymous phones etc. (changing addresses): not listed
    sens_seen(src, ("RuuviTag " + src[-5:].replace(":", "")) if r else (name or src[4:]), dict(r or {}, rssi=rssi))
    if r is not None:
        old = SENS["ruuvi"].get(src); SENS["ruuvi"][src] = r["moves"]
        if old is not None and r["moves"] != old:
            sens_event(src, None); return
    sens_event(src, False)                                # seen = in range (and not moved)


class SensorHub:
    def __init__(self):
        self.gp = {}                  # gpio -> [device or None, pull_up, time of the last try]
        self.rf_proc = None
        threading.Thread(target=self.loop, daemon=True, name="sensors").start()
        threading.Thread(target=self.rf_loop, daemon=True, name="rtl433").start()
        threading.Thread(target=self.ble_loop, daemon=True, name="ble").start()

    def _gpio_sync(self, want):
        for g in list(self.gp):
            if g not in want or self.gp[g][1] != want[g]:
                try:
                    if self.gp[g][0] is not None:
                        self.gp[g][0].close()
                except Exception:
                    pass
                del self.gp[g]
        for g, pu in want.items():
            ent = self.gp.get(g)
            if ent and (ent[0] is not None or time.time() - ent[2] < 30):
                continue
            try:
                from gpiozero import DigitalInputDevice
                self.gp[g] = [DigitalInputDevice(g, pull_up=pu), pu, time.time()]
            except Exception as e:
                if not ent:
                    log_event("sys", f"Sensor GPIO {g}: {e}"[:160])
                self.gp[g] = [None, pu, time.time()]

    def loop(self):
        n = 0
        while True:
            try:
                self.tick(); n += 1
                if n % 10 == 0:
                    self.publish()
            except Exception as e:
                log_event("sys", f"Sensors: {e}"[:160]); time.sleep(5)
            time.sleep(0.1)

    def tick(self):
        now = time.time()
        lst = CFG["sensors"] if CFG["sens_on"] else []
        self._gpio_sync({int(x["src"][5:]): x["kind"] == "door" for x in lst if x["src"].startswith("gpio:")})
        for x in lst:
            st = SENS["st"].setdefault(x["id"], {"state": "unknown", "last": 0.0, "cool": 0.0})
            if x["src"].startswith("gpio:"):
                ent = self.gp.get(int(x["src"][5:]))
                if not ent or ent[0] is None:
                    st["state"] = "error"; continue
                raw = int(ent[0].value) ^ int(ent[1])          # gpiozero inverts with a pull-up: back to the pin level
                act = bool(raw) ^ bool(x["inv"])
                if act and st["state"] != "active":
                    first = st["state"] in ("unknown", "error")
                    st["state"] = "active"
                    if not (first and x["kind"] == "door"):
                        sens_fire(x, "active")
                elif not act and st["state"] != "ok":
                    st["state"] = "ok"
            elif x["src"].startswith("ble:"):
                seen = SENS["seen"].get(x["src"])
                lim = float(CFG["tag_missing"]) * 60.0
                if not CFG["ble_on"]:
                    continue
                if seen and now - seen["t"] > lim and st["state"] not in ("missing", "unknown"):
                    st["state"] = "missing"; sens_fire(x, "missing")
                elif st["state"] == "pulse" and now - st["last"] > 10:
                    st["state"] = "ok"
            elif st.get("state") == "pulse" and now - st["last"] > 10:
                st["state"] = "ok"

    def publish(self):
        lang = None
        sts = {}
        for x in CFG["sensors"]:
            st = SENS["st"].get(x["id"]) or {}
            sts[x["id"]] = {"state": st.get("state", "unknown") if CFG["sens_on"] else "off",
                            "last": datetime.fromtimestamp(st["last"]).strftime("%d.%m. %H:%M") if st.get("last") else "",
                            "what": st.get("what", "")}
        with SENS["lock"]:
            seen = sorted(({"src": k, "label": v["label"], "ago": int(time.time() - v["t"]), "data": v["data"]} for k, v in SENS["seen"].items()),
                          key=lambda e: e["ago"])[:40]
        zb = "off"
        if CFG["sens_on"] and CFG["zigbee_on"]:
            zb = "needs MQTT" if not (CFG["mqtt_on"] and CFG["mqtt_host"].strip()) else ("listening" if MQTT["status"] == "connected" else MQTT["status"])
        STATE["sens"] = {"st": sts, "seen": seen, "rf": SENS["rf"] if CFG["sens_on"] else "off", "ble": SENS["ble"] if CFG["sens_on"] else "off",
                         "zb": zb, "free": sens_free_gpios(), "pir": time.time() - SENS["pir_t"] < 10}

    def rf_loop(self):
        while True:
            if not (CFG["sens_on"] and CFG["rf433_on"]):
                SENS["rf"] = "off"; time.sleep(3); continue
            exe = shutil.which("rtl_433")
            if not exe:
                SENS["rf"] = "rtl_433 missing (sudo apt install rtl-433)"; time.sleep(30); continue
            t0 = time.time()
            try:
                p = subprocess.Popen([exe, "-F", "json", "-M", "level"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
                self.rf_proc = p; SENS["rf"] = "listening"
                for line in p.stdout:
                    if not (CFG["sens_on"] and CFG["rf433_on"]):
                        break
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(d, dict):
                        rf_message(d)
                try:
                    p.terminate(); p.wait(5)
                except Exception:
                    pass
            except Exception as e:
                SENS["rf"] = f"error: {e}"[:100]
            self.rf_proc = None
            if CFG["sens_on"] and CFG["rf433_on"]:
                if time.time() - t0 < 10:
                    SENS["rf"] = "no RTL-SDR stick found"
                time.sleep(20)

    def ble_loop(self):
        while True:
            if not (CFG["sens_on"] and CFG["ble_on"]):
                SENS["ble"] = "off"; time.sleep(3); continue
            try:
                import asyncio
                from bleak import BleakScanner
            except ImportError:
                SENS["ble"] = "python3-bleak missing (sudo apt install python3-bleak)"; time.sleep(30); continue
            try:
                asyncio.run(self._ble(BleakScanner))
            except Exception as e:
                SENS["ble"] = f"error: {e}"[:100]; time.sleep(20)

    async def _ble(self, BleakScanner):
        import asyncio

        def cb(dev, adv):
            try:
                md = adv.manufacturer_data or {}
                ble_message(dev.address, adv.local_name or getattr(dev, "name", "") or "", md.get(0x0499), getattr(adv, "rssi", None))
            except Exception:
                pass
        sc = BleakScanner(detection_callback=cb)
        await sc.start(); SENS["ble"] = "listening"
        try:
            while CFG["sens_on"] and CFG["ble_on"]:
                await asyncio.sleep(1)
        finally:
            await sc.stop()


SENSHUB = None


# ----------------------------------------------------------------------------
# Storm warning: the air pressure of the BME280 falls fast (rule of thumb: 3 hPa in 3 hours = strong wind coming), a wind meter
#   (cup anemometer: a reed contact closes once per turn, between a GPIO and GND) measures strong wind, or the forecast
#   (Open-Meteo, optional) expects gusts in the next 12 hours. Push message, at most every 3 hours per reason.
# ----------------------------------------------------------------------------
STORM = {"p": deque(maxlen=480), "pulses": 0, "win": deque(maxlen=200), "cool": {}, "last": "", "dev": None, "pin": None}


def storm_forecast_gust():
    """The strongest gust (km/h) expected in the next 12 hours, from the stored forecast (None = unknown).
    While the simulator is connected: the gusts of the simulated weather (285), no internet forecast."""
    sf = sim_forecast()
    if sf is not None:
        try:
            return float(sf.get("gust_kmh"))
        except (TypeError, ValueError):
            return None
    now = datetime.now(); best = None
    for k in range(13):
        t = now + timedelta(hours=k)
        d = weather_day(t.strftime("%Y-%m-%d")) or {}
        row = (d.get("hourly") or {}).get(t.strftime("%H"))
        if row and len(row) > 4 and isinstance(row[4], (int, float)):
            best = row[4] if best is None else max(best, row[4])
    return best


def storm_trend():
    """Change of the air pressure in hPa per 3 hours (negative = falling), from at least 1 hour of values."""
    P = list(STORM["p"])
    if len(P) < 2:
        return None
    t1, p1 = P[-1]
    old = [x for x in P if t1 - x[0] >= 3600]
    if not old:
        return None
    t0, p0 = min(old, key=lambda x: abs((t1 - x[0]) - 3 * 3600))
    return round((p1 - p0) * (3 * 3600.0) / (t1 - t0), 1)


def storm_warn(kind, text, test=False):
    now = time.time()
    if not test and now - STORM["cool"].get(kind, 0.0) < 3 * 3600:
        return False
    STORM["cool"][kind] = now
    STORM["last"] = datetime.now().strftime("%d.%m. %H:%M") + " " + text
    log_event("sys", f"STORM WARNING: {text}")
    w = WATCH_REF["w"]
    if w is not None:
        w.notifier.info(text, title="{name}: " + ("[Test] " if test else "") + tr("STORM WARNING"))
    return True


class StormWatch:
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True, name="storm").start()

    def _pin(self):
        g = str(CFG["wind_gpio"] or "")
        want = int(g) if g.isdigit() else None
        if CFG["sim_on"]:
            return                                          # the simulation gives the wind
        if want == STORM["pin"] and (want is None or STORM["dev"] is not None or time.time() - STORM.get("tried", 0) < 30):
            return
        if STORM["dev"] is not None:
            try:
                STORM["dev"].close()
            except Exception:
                pass
        STORM["dev"] = None; STORM["pin"] = want; STORM["tried"] = time.time()
        if want is None:
            return
        try:
            from gpiozero import Button
            b = Button(want, pull_up=True, bounce_time=0.005)
            b.when_pressed = lambda: STORM.__setitem__("pulses", STORM["pulses"] + 1)
            STORM["dev"] = b
        except Exception as e:
            log_event("sys", f"Wind meter GPIO {want}: {e}"[:160])

    def loop(self):
        tp = 0.0
        while True:
            try:
                self.tick(tp); tp = time.time() if time.time() - tp >= 60 else tp
            except Exception as e:
                log_event("sys", f"Storm warning: {e}"[:160]); time.sleep(10)
            time.sleep(3)

    def tick(self, tp):
        now = time.time()
        if GPSMOD["anchor"] is not None and not (CFG["gpsmod_on"] and CFG["gps_theft"] and is_armed()):
            GPSMOD.update(anchor=None, away=0, alarm_t=0.0, dist=None)      # disarmed: theft tracking ends
        self._pin()
        n, STORM["pulses"] = STORM["pulses"], 0
        kmh = n / 3.0 * float(CFG["wind_factor"]) if STORM["pin"] is not None else None
        if CFG["sim_on"] and now - SIM["t"] < 10:
            kmh = float(SIM["wind"]); STORM["pin"] = STORM["pin"] if STORM["pin"] is not None else -1
        if kmh is not None:
            STORM["win"].append((now, kmh))
        env = STATE.get("env") or {}
        if env.get("p") and now - tp >= 60:
            STORM["p"].append((now, float(env["p"])))
        trend = storm_trend()
        win = [v for t, v in STORM["win"] if now - t <= 600]
        avg = round(sum(v for t, v in STORM["win"] if now - t <= 60) / max(1, len([1 for t, v in STORM["win"] if now - t <= 60])), 1) if win else None
        gust = round(max(win), 1) if win else None
        fc = storm_forecast_gust() if CFG["storm_forecast"] else None
        STATE["storm"] = {"p": env.get("p"), "trend": trend, "wind": avg, "gust": gust, "fc": fc, "last": STORM["last"],
                          "meter": STORM["pin"] is not None, "meter_ok": STORM["dev"] is not None or bool(CFG["sim_on"])}
        if not CFG["storm_on"]:
            return
        lim = float(CFG["storm_wind"])
        if trend is not None and trend <= -float(CFG["storm_drop"]):
            storm_warn("pressure", tr("the air pressure falls fast") + f" ({trend:+.1f} hPa / 3 h) - " + tr("strong wind or a thunderstorm may come. Secure the awning and the tent."))
        if gust is not None and gust >= lim:
            storm_warn("wind", tr("strong wind measured") + f": {gust:.0f} km/h - " + tr("secure the awning and the tent."))
        if fc is not None and fc >= lim:
            storm_warn("forecast", tr("gusts expected in the next 12 hours") + f": {fc:.0f} km/h - " + tr("secure the awning and the tent in time."))


STORMWATCH = None


# ----------------------------------------------------------------------------
# Own GPS module: gpsd (if it runs) or the NMEA sentences of a USB / serial receiver (u-blox, VK-162 ...). The position goes
#   into photos / videos and sets the place. Theft tracking: armed + carried away more than gps_theft_m -> alarm, then the
#   position with a map link every 5 minutes (push, and SMS if set up) until disarmed.
# ----------------------------------------------------------------------------
def nmea_ok(line):
    if not line.startswith("$") or "*" not in line:
        return False
    body, _, cs = line[1:].partition("*")
    x = 0
    for ch in body:
        x ^= ord(ch)
    try:
        return x == int(cs[:2], 16)
    except ValueError:
        return False


def _nmea_deg(v, hemi):
    if not v:
        return None
    d = float(v); deg = int(d // 100); val = deg + (d - deg * 100) / 60.0
    return -val if hemi in ("S", "W") else val


def nmea_parse(line):
    """{lat, lon} from RMC (status A), {sats, fix} from GGA - or None."""
    line = line.strip()
    if not nmea_ok(line):
        return None
    f = line.split("*")[0].split(",")
    typ = f[0][3:]
    try:
        if typ == "RMC" and len(f) > 6:
            if f[2] != "A":
                return {"fix": False}
            return {"lat": _nmea_deg(f[3], f[4]), "lon": _nmea_deg(f[5], f[6]), "fix": True}
        if typ == "GGA" and len(f) > 7:
            out = {"sats": int(f[7] or 0), "fix": (f[6] or "0") != "0"}
            if out["fix"]:
                out.update(lat=_nmea_deg(f[2], f[3]), lon=_nmea_deg(f[4], f[5]))
            return out
    except (ValueError, IndexError):
        return None
    return None


def gpsmod_fix(lat, lon, sats=None, via=""):
    if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
        return
    first = GPSMOD["lat"] is None
    GPSMOD.update(lat=round(lat, 6), lon=round(lon, 6), t=time.time(), status="fix", via=via or GPSMOD["via"])
    if sats is not None:
        GPSMOD["sats"] = sats
    if first:
        log_event("sys", f"GPS module: position {lat:.4f}, {lon:.4f}")
    if via != "simulator" and (abs(lat - float(CFG["latitude"])) > 0.01 or abs(lon - float(CFG["longitude"])) > 0.01):   # ~1 km: a new place (never from the simulator)
        CFG["latitude"], CFG["longitude"] = round(lat, 4), round(lon, 4); save_settings()
    gps_theft_check()


def osm_link(lat, lon):
    return f"https://www.openstreetmap.org/?mlat={lat:.5f}&mlon={lon:.5f}#map=17/{lat:.5f}/{lon:.5f}"


def gps_theft_check():
    """Armed: the first position is the anchor. Further away than gps_theft_m twice in a row = carried away."""
    g = GPSMOD; now = time.time()
    if not (CFG["gpsmod_on"] and CFG["gps_theft"] and is_armed()) or g["lat"] is None:
        g["anchor"] = None; g["away"] = 0; g["alarm_t"] = 0.0; return
    if g["anchor"] is None:
        g["anchor"] = (g["lat"], g["lon"]); return
    dist = geo_km(g["anchor"], (g["lat"], g["lon"])) * 1000.0
    g["dist"] = round(dist)
    if dist < float(CFG["gps_theft_m"]):
        g["away"] = 0; return
    g["away"] += 1
    if g["away"] < 2:
        return
    w = WATCH_REF["w"]
    link = osm_link(g["lat"], g["lon"])
    if not g["alarm_t"]:
        g["alarm_t"] = now; g["upd_t"] = now
        txt = tr("the device was carried away") + f" ({dist / 1000.0:.2f} km). " + tr("Position") + ": " + link
        log_event("sys", f"THEFT: device carried away {dist:.0f} m - {g['lat']:.5f}, {g['lon']:.5f}")
        if w is not None:
            w.notifier.alert("{name}: " + tr("THEFT ALARM"), txt, w.frame_out)
        siren_alarm("tamper")
    elif now - g["upd_t"] >= 300:
        g["upd_t"] = now
        log_event("sys", f"THEFT tracking: {g['lat']:.5f}, {g['lon']:.5f}")
        if w is not None:
            w.notifier.alert("{name}: " + tr("THEFT ALARM") + " – " + tr("position"), tr("Position now") + f" ({dist / 1000.0:.2f} km): " + link, None)


def sim_sensor(key):
    """2.98.11: a sensor of the 3D simulator (solar panel, GPS module) while it is connected - instead of the real part"""
    if not CFG.get("sim_on") or time.time() - SIM.get("t", 0.0) > 10:
        return None
    v = SIM.get(key)
    return v if isinstance(v, dict) else None


class GpsModule:
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True, name="gps").start()

    def loop(self):
        while True:
            if not CFG["gpsmod_on"]:
                GPSMOD["status"] = "off"; time.sleep(3); continue
            sg = sim_sensor("gps")
            if sg is not None:
                try:
                    GPSMOD["status"] = "fix"
                    gpsmod_fix(float(sg["lat"]), float(sg["lon"]), int(sg.get("sats") or 0), via="simulator")
                except (KeyError, TypeError, ValueError):
                    pass
                time.sleep(5); continue
            port = str(CFG["gpsmod_port"] or "auto")
            try:
                if port in ("auto", "gpsd") and self.gpsd():
                    pass
                elif port == "gpsd":
                    GPSMOD["status"] = "gpsd not running"; time.sleep(15)
                else:
                    busy = {str(CFG.get("sms_port") or "")}             # the AT port of an LTE stick stays for the SMS
                    ports = [port] if port != "auto" else [p for p in sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*")) + ["/dev/serial0"]
                                                           if os.path.exists(p) and p not in busy]
                    if not ports:
                        GPSMOD["status"] = "no GPS module found"; time.sleep(15); continue
                    for p in ports:
                        if self.serial(p):
                            break
                    else:
                        GPSMOD["status"] = "no GPS module found"; time.sleep(15)
            except Exception as e:
                GPSMOD["status"] = f"error: {e}"[:100]; time.sleep(15)

    def gpsd(self):
        import socket
        try:
            sk = socket.create_connection(("127.0.0.1", 2947), timeout=2)
        except OSError:
            return False
        GPSMOD["via"] = "gpsd"; GPSMOD["status"] = "searching satellites"
        try:
            sk.sendall(b'?WATCH={"enable":true,"json":true};\n'); sk.settimeout(10)
            buf = b""
            while CFG["gpsmod_on"] and str(CFG["gpsmod_port"]) in ("auto", "gpsd"):
                try:
                    chunk = sk.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if d.get("class") == "SKY":
                        GPSMOD["sats"] = sum(1 for x in d.get("satellites") or [] if x.get("used"))
                    elif d.get("class") == "TPV":
                        if (d.get("mode") or 0) >= 2 and "lat" in d and "lon" in d:
                            gpsmod_fix(float(d["lat"]), float(d["lon"]), via="gpsd")
                        elif time.time() - GPSMOD["t"] > 60:
                            GPSMOD["status"] = "searching satellites"
        finally:
            sk.close()
        return True

    def serial(self, port):
        import termios
        try:
            fd = os.open(port, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError:
            return False
        try:
            try:
                at = termios.tcgetattr(fd)
                at[0] = 0; at[1] = 0; at[2] = termios.CS8 | termios.CREAD | termios.CLOCAL; at[3] = 0
                at[4] = at[5] = termios.B9600
                termios.tcsetattr(fd, termios.TCSANOW, at)
            except termios.error:
                pass                                          # USB modules (ttyACM) ignore the speed
            buf, t0, good = b"", time.time(), False
            GPSMOD["via"] = port
            while CFG["gpsmod_on"] and str(CFG["gpsmod_port"]) in ("auto", port):
                try:
                    chunk = os.read(fd, 1024)
                except BlockingIOError:
                    chunk = b""
                except OSError:
                    break
                if not chunk:
                    if not good and time.time() - t0 > 6:
                        return False                          # nothing that looks like GPS: not this port
                    time.sleep(0.2); continue
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    r = nmea_parse(line.decode(errors="replace"))
                    if r is None:
                        continue
                    if not good:
                        good = True; GPSMOD["status"] = "searching satellites"; log_event("sys", f"GPS module found at {port}")
                    if "sats" in r:
                        GPSMOD["sats"] = r["sats"]
                    if r.get("fix") and r.get("lat") is not None:
                        gpsmod_fix(r["lat"], r["lon"], via=port)
                    elif time.time() - GPSMOD["t"] > 60:
                        GPSMOD["status"] = "searching satellites"
                if len(buf) > 4096:
                    buf = b""
            return good
        finally:
            os.close(fd)


GPSMODULE = None


# ----------------------------------------------------------------------------
# Solar panel: an INA219 module (the cheap blue board, shunt 0.1 Ohm, up to 26 V / 3.2 A) between the panel and the charger.
#   Watts, volts and the yield of the day. Night forecast: does the battery last until sunrise at the present consumption?
# ----------------------------------------------------------------------------
SOLAR = {"day": "", "wh": 0.0, "max": 0.0, "t": 0.0, "warned": ""}


def ina219_read(addr, shunt, bus=1):
    """(volts on the panel side, amps) or None."""
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
        return (bus_raw >> 3) * 0.004, sh * 0.00001 / max(0.001, float(shunt))
    except OSError:
        return None
    finally:
        os.close(fd)


def next_sunrise(now=None):
    now = now or sim_now()                                 # the simulated clock and place while connected (285)
    for k in (0, 1):
        d = (now + timedelta(days=k)).date()
        st = sun_times_here(d)
        if isinstance(st, str):
            return None
        t = datetime(d.year, d.month, d.day) + timedelta(minutes=st[0])
        if t > now:
            return t
    return None


def night_forecast():
    """Does the battery last until the next sunrise? {sunrise, need_h, have_h, enough} or None (no battery / unknown)."""
    b = STATE.get("battery") or {}
    if not b.get("on") or b.get("pct") is None or not b.get("cap_wh") or not b.get("use_w"):
        return None
    sr = next_sunrise()
    if sr is None:
        return None
    now = sim_now(); dark = is_dark()
    if dark:
        need = (sr - now).total_seconds() / 3600.0
    else:                                                  # daytime: the coming night (sunset .. sunrise), the sun still charges until then
        st = sun_times_here(now.date())
        ss = datetime(now.year, now.month, now.day) + timedelta(minutes=st[1]) if not isinstance(st, str) else now
        need = max(0.0, (sr - max(ss, now)).total_seconds() / 3600.0)
    have = b["pct"] / 100.0 * float(b["cap_wh"]) / max(0.5, float(b["use_w"]))
    return {"sunrise": sr.strftime("%H:%M"), "need_h": round(need, 1), "have_h": round(have, 1), "enough": have >= need * 1.1, "night": dark}


class SolarMonitor:
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True, name="solar").start()

    def loop(self):
        while True:
            try:
                self.tick()
            except Exception as e:
                log_event("sys", f"Solar: {e}"[:160])
            time.sleep(10)

    def tick(self):
        now = time.time(); day = sim_now().strftime("%Y-%m-%d")      # the day of the simulated scene while connected (285)
        if SOLAR["day"] != day:
            SOLAR.update(day=day, wh=0.0, max=0.0)
        if CFG["solar_on"]:
            try:
                addr = int(str(CFG["solar_addr"]), 16)
            except ValueError:
                addr = 0x41
            try:
                pca_ = int(str(CFG["pca_address"]), 16)
            except ValueError:
                pca_ = -1
            clash = addr == pca_ and str(STATE.get("servo_backend", "")).startswith("pca9685")
            ss = sim_sensor("solar")
            if ss is not None:
                try:
                    r = (float(ss["v"]), float(ss["a"])); clash = False
                except (KeyError, TypeError, ValueError):
                    r = None
            else:
                r = None if clash else ina219_read(addr, CFG["solar_shunt"])
            if r is not None and not (0.0 <= r[0] <= 40.0 and abs(r[1]) <= 20.0):
                r = None                                  # not a plausible solar reading (another chip on that address?)
            if r is None:
                STATE["solar"] = {"on": True, "ok": False, "msg": "same I2C address as the servo board" if clash else ""}
            else:
                v, a = r; w = max(0.0, v * abs(a))
                dt = min(60.0, now - SOLAR["t"]) if SOLAR["t"] else 0.0; SOLAR["t"] = now
                SOLAR["wh"] += w * dt / 3600.0; SOLAR["max"] = max(SOLAR["max"], w)
                STATE["solar"] = {"on": True, "ok": True, "v": round(v, 2), "a": round(abs(a), 2), "w": round(w, 1),
                                  "wh": round(SOLAR["wh"], 1), "max": round(SOLAR["max"], 1)}
        else:
            STATE["solar"] = {"on": False}
        nf = night_forecast(); STATE["night"] = nf
        if nf and CFG["night_warn"] and not nf["enough"] and is_dark() and SOLAR["warned"] != day:
            hh = sim_now().hour
            if hh >= 15:                                       # once in the evening (not again after midnight)
                SOLAR["warned"] = day
                log_event("sys", f"Battery will probably not last until sunrise ({nf['have_h']} h left, {nf['need_h']} h needed)")
                w_ = WATCH_REF["w"]
                if w_ is not None:
                    w_.notifier.info(trf("The battery will probably not last until sunrise ({sr}): about {have} h left, {need} h needed. Charge it or switch on power saving.",
                                         sr=nf["sunrise"], have=nf["have_h"], need=nf["need_h"]), title="{name}: " + tr("Battery"))


SOLARMON = None


