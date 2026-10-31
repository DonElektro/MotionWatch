#@ Motion Watch – Teil 060: Sicherung, Diebstahlschutz, Linse, Klima, Wetter, Postausgang, Notifier. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Backup: copy finished alarm recordings away from the device (if it is stolen or broken the clips are safe):
#   WebDAV (Nextcloud, Synology / QNAP NAS, many clouds), a folder (USB stick, mounted NAS) or Telegram (video).
#   Waits until the recording is complete (also the sound), tries 3 times. One sub-folder per day.
# ----------------------------------------------------------------------------
class Backup:
    def __init__(self):
        self.q = queue.Queue(maxsize=200)
        threading.Thread(target=self.loop, daemon=True).start()

    def add(self, path, meta=None):
        if CFG.get("sim_on"):
            return
        if CFG["backup_type"] == "off" or not path:
            return
        try:
            self.q.put_nowait((path, dict(meta or {}), 0))
            STATE["backup_status"] = f"{tr('waiting')}: {os.path.basename(path)}"
        except queue.Full:
            log_event("rec", "Backup: too many recordings waiting - one skipped")

    def loop(self):
        while True:
            path, meta, tries = self.q.get()
            if not self._wait_ready(path):
                continue
            ok, err = backup_copy(path, meta)
            name = os.path.basename(path)
            if ok:
                STATE["backup_status"] = f"✓ {datetime.now().strftime('%H:%M')} {name}"
                log_event("rec", f"Backup: {name} copied ({CFG['backup_type']})")
            else:
                STATE["backup_status"] = f"⚠ {err}"[:200]
                log_event("rec", f"Backup of {name} failed: {err}"[:220])
                if tries < 2:
                    threading.Timer(60 * (1 + 4 * tries), lambda p_=path, m_=meta, t_=tries + 1: self._retry(p_, m_, t_)).start()

    def _retry(self, path, meta, tries):
        try:
            self.q.put_nowait((path, meta, tries))
        except queue.Full:
            pass

    @staticmethod
    def _wait_ready(path, limit=240):
        """The sound is added after the recording ends (the file is replaced) - wait until the file does not change for 6 s."""
        end = time.time() + limit; last = None; same = 0.0
        while time.time() < end:
            try:
                st = os.stat(path); cur = (st.st_size, st.st_mtime)
            except OSError:
                cur = None
            if cur and cur == last and time.time() - cur[1] > 4:
                same += 1
                if same >= 3:
                    return True
            else:
                same = 0
            last = cur; time.sleep(2)
        return os.path.isfile(path)


def _dav_request(url, method, data=None, length=None):
    import base64
    h = {}
    if CFG["backup_user"] or CFG["backup_password"]:
        h["Authorization"] = "Basic " + base64.b64encode(f"{CFG['backup_user']}:{CFG['backup_password']}".encode()).decode()
    if length is not None:
        h["Content-Length"] = str(length); h["Content-Type"] = "application/octet-stream"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _shrink_video(path):
    """A smaller copy (640 px wide, lower quality) for services with a size limit. Returns the path or None."""
    if not shutil.which("ffmpeg"):
        return None
    dst = os.path.join(tempfile.gettempdir(), "mw_small_" + os.path.basename(path))
    try:
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-vf", "scale=640:-2", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "32", "-c:a", "aac", "-b:a", "48k", "-movflags", "+faststart", dst], capture_output=True, timeout=900)
        if r.returncode == 0 and os.path.isfile(dst) and 0 < os.path.getsize(dst) < 49 * 1024 * 1024:
            return dst
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        os.remove(dst)
    except OSError:
        pass
    return None


def backup_copy(path, meta=None, test=False):
    """Copy one file to the chosen place. test=True: a small text file to check the settings."""
    kind = CFG["backup_type"]
    day = datetime.now().strftime("%Y-%m-%d")
    name = os.path.basename(path) if path else "motionwatch_test.txt"
    dev = (CFG["device_name"] or "MoveEye").strip()
    try:
        if test:
            data = f"MoveEye {APP_VERSION} - backup test {datetime.now().isoformat(timespec='seconds')} ({dev})\n".encode()
        if kind == "folder":
            base = CFG["backup_folder"].strip()
            if not base.startswith("/"):
                return False, "no folder set"
            if not os.path.isdir(os.path.dirname(base.rstrip("/")) or "/"):
                return False, "folder not found (USB stick / NAS connected?)"
            if base.startswith(("/media/", "/mnt/")):          # 2.95.33: never fill the SD card when the stick is missing
                q = os.path.abspath(base)
                while q not in ("/", "/media", "/mnt") and not os.path.ismount(q):
                    q = os.path.dirname(q)
                if q in ("/", "/media", "/mnt"):
                    return False, "folder not found (USB stick / NAS connected?)"
            dst = os.path.join(base, day); os.makedirs(dst, exist_ok=True)
            if test:
                with open(os.path.join(dst, name), "wb") as f:
                    f.write(data)
            else:
                shutil.copy2(path, os.path.join(dst, name) + ".part"); os.replace(os.path.join(dst, name) + ".part", os.path.join(dst, name))
            return True, ""
        if kind == "webdav":
            base = CFG["backup_url"].strip()
            if not base:
                return False, "no WebDAV folder set"
            base = base.rstrip("/") + "/"
            code = _dav_request(base, "MKCOL")
            if code in (401, 403):
                return False, f"login refused (HTTP {code}) - user name / app password?"
            code = _dav_request(base + day + "/", "MKCOL")
            if code not in (201, 405, 301, 200):
                return False, f"cannot create the day folder (HTTP {code})"
            if test:
                code = _dav_request(base + day + "/" + name, "PUT", data, len(data))
            else:
                size = os.path.getsize(path)
                with open(path, "rb") as f:
                    code = _dav_request(base + day + "/" + urllib.request.quote(name), "PUT", f, size)
            return (True, "") if code in (200, 201, 204) else (False, f"upload refused (HTTP {code})")
        if kind == "telegram":
            if not (CFG["telegram_token"] and CFG["telegram_chat"]):
                return False, "Telegram bot token / chat id missing (Notifications)"
            base = f"{TELEGRAM_API}/bot{CFG['telegram_token']}"
            b = uuid.uuid4().hex
            cap = f"{dev}: " + (("Test" if test else tr("recording") + " " + name))
            if test:
                req = urllib.request.Request(base + "/sendMessage", data=json.dumps({"chat_id": CFG["telegram_chat"], "text": cap + " ✓"}).encode(),
                                             headers={"Content-Type": "application/json"})
            else:
                is_pic = name.lower().endswith(".jpg")
                src, small = path, None
                if not is_pic and os.path.getsize(path) > 45 * 1024 * 1024:     # too big for Telegram: a smaller copy
                    small = _shrink_video(path)
                    if not small:
                        return False, "too big for Telegram (max. 50 MB) and could not be made smaller (ffmpeg?)"
                    src = small
                try:
                    with open(src, "rb") as f:
                        vid = f.read()
                finally:
                    if small:
                        try:
                            os.remove(small)
                        except OSError:
                            pass
                field, ctype, ep = ("photo", "image/jpeg", "/sendPhoto") if is_pic else ("video", "video/mp4", "/sendVideo")
                parts = [f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                         for k, v in (("chat_id", CFG["telegram_chat"]), ("caption", cap), ("supports_streaming", "true"))]
                parts.append((f'--{b}\r\nContent-Disposition: form-data; name="{field}"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n').encode()
                             + vid + b"\r\n")
                parts.append(f"--{b}--\r\n".encode())
                req = urllib.request.Request(base + ep, data=b"".join(parts), headers={"Content-Type": "multipart/form-data; boundary=" + b})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    return (True, "") if r.status == 200 else (False, f"Telegram HTTP {r.status}")
            except urllib.error.HTTPError as e:
                return False, f"Telegram HTTP {e.code}"
        return False, "backup is off"
    except Exception as e:
        msg = str(e)
        for sec_ in (CFG["telegram_token"], CFG["backup_password"]):
            if sec_:
                msg = msg.replace(sec_, "***")
        return False, msg[:200]


BACKUP = None


# ----------------------------------------------------------------------------
# Theft / sabotage protection: camera covered or turned away (picture), device moved / knocked over (optional motion
#   sensor MPU-6050 / 6500 on I2C 0x68), power cut while armed. When armed: push message (high priority) + siren.
#   While the camera head moves itself (patrol, tracking, joystick, timelapse) the picture check waits and learns anew.
# ----------------------------------------------------------------------------
class TamperGuard:
    def __init__(self):
        self.ref = None; self.ref_mean = 0.0; self.t_last = 0.0; self.settle = time.time() + 15
        self.pos = None; self.n_cov = 0; self.n_mov = 0; self.cool = 0.0
        self.acc = None; self.base = None; self.n_tilt = 0; self.armed_was = None
        STATE["tamper"] = {"sensor": False, "last": "", "state": "learning"}
        threading.Thread(target=self.sensor_loop, daemon=True, name="tamper").start()

    # ---- picture: covered / turned ----
    def feed(self, small, t0):
        if not CFG["tamper_on"] or t0 - self.t_last < 1.0:
            return
        self.t_last = t0
        pos = (round(CFG["pan"], 1), round(CFG["tilt"], 1))
        if pos != self.pos or manual_active() or STATE.get("tracking") or STATE.get("patrol_moving") or TL_HOLD.get("on"):
            self.pos = pos; self.settle = t0 + 8; self.ref = None; self.n_cov = self.n_mov = 0
            STATE["tamper"]["state"] = "learning"; return
        if t0 < self.settle:
            return
        g = cv2.resize(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if small.ndim == 3 else small, (80, 60), interpolation=cv2.INTER_AREA).astype(np.float32)
        mean, std = float(g.mean()), float(g.std())
        e = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
        if self.ref is None:
            self.ref, self.ref_e, self.ref_mean, self.ref_std = g, e, mean, std
            STATE["tamper"]["state"] = "watching"; return
        covered = mean < 18 and std < 7 and self.ref_mean > 35 and self.ref_std > 8
        # 2.98.30: a cloth over the lens is not always black - the camera brightens it (auto exposure, the simulator too):
        # a flat picture without edges where there were many is covered as well
        # (411: in fog the edges fade to ~25 % - then only a picture with almost no edges left (< 8 %) is a cloth)
        fogq = fog_tamper_quiet(t0)
        if not covered and std < 7 and self.ref_std > 12 and float(e.mean()) < (0.08 if fogq else 0.25) * max(1e-3, float(self.ref_e.mean())):
            covered = True
        a, b = e - e.mean(), self.ref_e - self.ref_e.mean()
        corr = float((a * b).sum() / (math.sqrt(float((a * a).sum()) * float((b * b).sum())) + 1e-6))
        # 411: fog takes the edges away, so they no longer match the reference - no «camera turned» in fog (detection test,
        # Schattwald: a false sabotage push). The reference stays as it was before the fog.
        moved = (not covered) and not fogq and self.ref_std > 10 and std > 8 and corr < 0.3 and not STATE.get("persons")
        self.n_cov = self.n_cov + 1 if covered else 0
        self.n_mov = self.n_mov + 1 if moved else 0
        if self.n_cov >= 3:
            self.alarm("covered"); self.ref = None; self.n_cov = 0; self.settle = t0 + 10
        elif self.n_mov >= 5:
            self.alarm("turned"); self.ref = None; self.n_mov = 0; self.settle = t0 + 10
        elif not covered and corr > 0.6 and not fogq:         # slowly follow the light of the day (not the fog, 411)
            self.ref = self.ref * 0.9 + g * 0.1; self.ref_e = self.ref_e * 0.9 + e * 0.1
            self.ref_mean = self.ref_mean * 0.9 + mean * 0.1; self.ref_std = self.ref_std * 0.9 + std * 0.1

    # ---- motion sensor (MPU-6050 / 6500 / 9250 at I2C 0x68) ----
    @staticmethod
    def _mpu_open():
        import fcntl
        try:
            fd = os.open("/dev/i2c-1", os.O_RDWR)
        except OSError:
            return None
        try:
            fcntl.ioctl(fd, I2C_SLAVE, 0x68)
            os.write(fd, bytes([0x75])); who = os.read(fd, 1)[0]
            if who not in (0x68, 0x70, 0x71, 0x73):             # not a motion sensor (e.g. a clock chip at 0x68)
                os.close(fd); return None
            os.write(fd, bytes([0x6B, 0x00]))                    # wake up
            os.write(fd, bytes([0x1C, 0x00]))                    # +-2 g
            return fd
        except OSError:
            os.close(fd); return None

    @staticmethod
    def _mpu_read(fd):
        os.write(fd, bytes([0x3B])); b = os.read(fd, 6)
        v = [((b[i] << 8) | b[i + 1]) for i in (0, 2, 4)]
        return [(x - 65536 if x > 32767 else x) / 16384.0 for x in v]

    def sensor_loop(self):
        while True:                                     # 2.95.34: an error must not end the motion sensor watch
            try:
                self._sensor_loop()
            except Exception as e:
                log_event("sys", f"Motion sensor error (restarted): {type(e).__name__}: {e}"[:200])
                time.sleep(10)

    def _sensor_loop(self):
        fd = None; tried = 0.0
        while True:
            time.sleep(0.5)
            beat("tamper", 120, "Motion sensor")
            if not CFG["tamper_motion"]:
                continue
            if fd is None:
                if time.time() - tried < 60:
                    continue
                tried = time.time(); fd = self._mpu_open()
                if fd is None:
                    STATE["tamper"]["sensor"] = False; continue
                STATE["tamper"]["sensor"] = True; self.base = None
                log_event("sys", "Motion sensor found (I2C 0x68) - alarm when the device is moved")
            try:
                a = self._mpu_read(fd)
            except OSError:
                try:
                    os.close(fd)
                except OSError:
                    pass
                fd = None; continue
            self.check_motion(a)

    def check_motion(self, a):
        armed = is_armed()
        n = math.sqrt(sum(x * x for x in a)) or 1.0
        if self.base is None or not armed or self.armed_was is False:
            self.base = [x / n for x in a]; self.armed_was = armed; self.n_tilt = 0; return
        self.armed_was = armed
        cos = sum(x / n * y for x, y in zip(a, self.base))
        ang = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        shake = abs(n - 1.0) > 0.45
        self.n_tilt = self.n_tilt + 1 if (ang > float(CFG["tamper_tilt"]) or shake) else 0
        if self.n_tilt >= 2:
            self.alarm("knocked" if ang > 60 else "moved"); self.n_tilt = 0
            self.base = [x / n for x in a]

    # ---- alarm ----
    def alarm(self, what, looked=None):
        now = time.time()
        txt = {"covered": ("Kamera abgedeckt", "camera covered"), "turned": ("Kamera verdreht / Bild verändert", "camera turned / picture changed"),
               "moved": ("Gerät bewegt", "device moved"), "knocked": ("Gerät umgeworfen", "device knocked over"),
               "power": ("Strom getrennt (Schutz an)", "power cut while armed")}[what]
        # 2.98.30: covered or turned? The head looks briefly in other directions first (162) - then the push says which
        if looked is None and what in ("covered", "turned") and is_armed() and now - self.cool >= 120 and kopf_tamper_wanted():
            self.cool = now - 115                          # no second look-around meanwhile
            ref = None if self.ref is None else self.ref.copy()

            def look():
                extra = ""
                try:
                    extra = kopf_tamper_look(what, ref)
                except Exception as e:
                    log_event("sys", f"Sabotage look-around: {e}"[:160])
                self.cool = 0.0; self.pos = None
                self.alarm(what, looked=extra)
            threading.Thread(target=look, daemon=True, name="tamper-look").start()
            return
        full = tr(txt[1]) + (" – " + looked if looked else "")
        STATE["tamper"]["last"] = datetime.now().strftime("%H:%M") + " " + full
        log_event("sys", f"SABOTAGE: {txt[1]}" + (f" - {looked}" if looked else "") + ("" if is_armed() else " (disarmed - no alarm)"))
        if not is_armed() or now - self.cool < 120:
            return
        self.cool = now
        if what in ("moved", "knocked", "power"):           # the device itself moves: + its position, if the GPS has a fix (280)
            try:
                mp_ = gps_map_link()
            except NameError:
                mp_ = ""
            if mp_:
                full += " · " + tr("Position") + ": " + mp_   # 635b sends the map link complete (never cut)
        w = WATCH_REF["w"]
        if w is not None:
            w.notifier.tamper(full, w.frame_out)
        siren_alarm("tamper")


TAMPER = None


# ----------------------------------------------------------------------------
# Lens check: dew at night, dust or a spider web make the picture blurred and flat. Every 15 s the sharpness (variance of the
#   Laplacian) and the contrast of a small grey picture; compared with what is normal for day or night (the best 20 % of the
#   last 24 hours). Clearly worse for 15 minutes = push message (at most every 6 hours).
# ----------------------------------------------------------------------------
class LensCheck:
    def __init__(self):
        self.t_last = 0.0; self.base = {True: deque(maxlen=6000), False: deque(maxlen=6000)}; self.recent = deque(maxlen=60)
        self.bad_since = 0.0; self.warned = 0.0; self.state = "learning"
        STATE["lens"] = {"state": "learning", "pct": None}

    def feed(self, small, t0):
        if not CFG["lens_check"]:
            STATE["lens"] = {"state": "off", "pct": None}; return
        if t0 - self.t_last < 15:
            return
        self.t_last = t0
        if manual_active() or STATE.get("tracking") or STATE.get("patrol_moving") or STATE.get("persons"):
            return
        g = cv2.resize(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if small.ndim == 3 else small, (160, 120), interpolation=cv2.INTER_AREA)
        if float(g.mean()) < 12:
            return                                        # black: covered (theft protection) or no light at all
        if fog_on() and fog_weather():
            return                                        # 411: the weather says fog too - the blur is the fog, not the lens
        sharp = float(cv2.Laplacian(g, cv2.CV_32F).var()); con = float(g.std())
        self.add(t0, sharp, con, bool(is_dark()))

    def add(self, t0, sharp, con, dark):
        b = self.base[dark]; b.append((t0, sharp, con))
        while b and t0 - b[0][0] > 86400:
            b.popleft()
        self.recent.append((t0, sharp, con, dark))
        rec = [x for x in self.recent if t0 - x[0] <= 600 and x[3] == dark]
        if len(b) < 240 or len(rec) < 20:                 # one hour of pictures before it judges
            STATE["lens"] = {"state": "learning", "pct": None}; return
        ss = sorted(x[1] for x in b); cs = sorted(x[2] for x in b)
        ref_s, ref_c = ss[int(len(ss) * 0.8)], cs[int(len(cs) * 0.8)]
        cur_s = sorted(x[1] for x in rec)[len(rec) // 2]; cur_c = sorted(x[2] for x in rec)[len(rec) // 2]
        pct = int(round(100.0 * cur_s / max(ref_s, 1e-3)))
        bad = cur_s < 0.35 * ref_s and cur_c < 0.8 * ref_c
        if bad:
            self.bad_since = self.bad_since or t0
            if t0 - self.bad_since >= 900 and self.state != "fogged":
                self.state = "fogged"
                log_event("sys", f"Lens fogged or dirty? Sharpness {pct} % of normal for 15 minutes")
                if t0 - self.warned > 6 * 3600:
                    self.warned = t0
                    w = WATCH_REF["w"]
                    if w is not None:
                        w.notifier.info(trf("The picture has been blurred for 15 minutes (sharpness {p} % of normal). Wipe the lens and look for dew or a spider web.", p=pct),
                                        title="{name}: " + tr("Lens fogged or dirty"))
        else:
            self.bad_since = 0.0
            if self.state == "fogged" and cur_s > 0.6 * ref_s:
                log_event("sys", "Lens: the picture is clear again")
            if self.state != "fogged" or cur_s > 0.6 * ref_s:
                self.state = "clear"
        STATE["lens"] = {"state": self.state, "pct": pct}


LENS = None


# ---- temperature alarm (the temperature sensor; e.g. a pet in the caravan) ----
TEMPA = {"state": "ok", "t": 0.0}


def temp_check(env):
    if not CFG["temp_alarm_on"]:
        TEMPA["state"] = "ok"; return
    if not env or env.get("t") is None:                  # 2.95.34: a lost sensor is not «all fine»
        TEMPA["miss"] = TEMPA.get("miss", 0) + 1
        if TEMPA["miss"] == 10:
            log_event("sys", "Temperature alarm: the sensor gives no values any more")
            w_ = WATCH_REF.get("w")
            if w_ is not None:
                w_.notifier.alert("{name}: " + tr("TEMPERATURE ALARM"), tr("The temperature sensor gives no values any more - the alarm cannot work."), None)
        return
    TEMPA["miss"] = 0
    t, hot, cold = float(env["t"]), float(CFG["temp_hot"]), float(CFG["temp_cold"])
    prev = TEMPA["state"]
    st = "hot" if t >= hot else "cold" if t <= cold else ("ok" if cold + 1.0 < t < hot - 1.0 else prev)   # 1 °C hysteresis
    now = time.time(); w = WATCH_REF["w"]
    if st in ("hot", "cold") and (st != prev or now - TEMPA["t"] >= 2 * 3600):
        TEMPA["t"] = now
        txt = trf("Too hot: {t:.1f} °C (limit {l:.0f} °C)", t=t, l=hot) if st == "hot" else trf("Too cold: {t:.1f} °C (limit {l:.0f} °C)", t=t, l=cold)
        log_event("sys", f"TEMPERATURE ALARM: {t:.1f} °C ({st})")
        if w is not None:
            w.notifier.alert("{name}: " + tr("TEMPERATURE ALARM"), txt, None)
    elif st == "ok" and prev in ("hot", "cold"):
        log_event("sys", f"Temperature fine again: {t:.1f} °C")
        if w is not None:
            w.notifier.info(trf("Temperature fine again: {t:.1f} °C", t=t), title="{name}: " + tr("Temperature"))
    TEMPA["state"] = st


# ----------------------------------------------------------------------------
# Climate: temperature / humidity / air pressure sensor (BME280 / BMP280 at I2C 0x76 / 0x77, or DS18B20 on 1-Wire GPIO 4).
#   Read every 30 s; every 10 minutes one line goes into <data>/climate/YYYY-MM-DD.json (also CPU temperature and battery)
#   - the day overview of the diary draws its curves from there. The sensor must sit outside the warm housing.
# ----------------------------------------------------------------------------
class EnvSensor:
    def __init__(self):
        self.fd = None; self.addr = None; self.cal = None; self.bmp = False; self.tried = 0.0; self.last_log = 0.0
        STATE["env"] = None
        threading.Thread(target=self.loop, daemon=True, name="climate").start()

    # ---- BME280 / BMP280 ----
    def _rd(self, reg, n):
        os.write(self.fd, bytes([reg])); return os.read(self.fd, n)

    def _open(self):
        import fcntl, struct
        try:
            fd = os.open("/dev/i2c-1", os.O_RDWR)
        except OSError:
            return False
        for addr in (0x76, 0x77):
            try:
                fcntl.ioctl(fd, I2C_SLAVE, addr)
                os.write(fd, bytes([0xD0])); cid = os.read(fd, 1)[0]
                if cid not in (0x60, 0x58):
                    continue
                self.fd, self.addr, self.bmp = fd, addr, cid == 0x58
                c = self._rd(0x88, 24)
                T1, T2, T3, P1, P2, P3, P4, P5, P6, P7, P8, P9 = struct.unpack("<HhhHhhhhhhhh", c)
                H1 = H2 = H3 = H4 = H5 = H6 = 0
                if not self.bmp:
                    H1 = self._rd(0xA1, 1)[0]
                    h = self._rd(0xE1, 7)
                    H2 = struct.unpack("<h", h[0:2])[0]; H3 = h[2]
                    H4 = (struct.unpack("b", h[3:4])[0] << 4) | (h[4] & 0x0F)
                    H5 = (struct.unpack("b", h[5:6])[0] << 4) | (h[4] >> 4)
                    H6 = struct.unpack("b", h[6:7])[0]
                self.cal = (T1, T2, T3, P1, P2, P3, P4, P5, P6, P7, P8, P9, H1, H2, H3, H4, H5, H6)
                log_event("sys", f"Climate sensor {'BMP280' if self.bmp else 'BME280'} found (I2C 0x{addr:02x})")
                return True
            except OSError:
                continue
        os.close(fd)
        return False

    def _bme(self):
        T1, T2, T3, P1, P2, P3, P4, P5, P6, P7, P8, P9, H1, H2, H3, H4, H5, H6 = self.cal
        if not self.bmp:
            os.write(self.fd, bytes([0xF2, 0x01]))                       # humidity x1
        os.write(self.fd, bytes([0xF4, 0x25]))                           # temperature x1, pressure x1, one measurement
        time.sleep(0.05)
        d = self._rd(0xF7, 8)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4); adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4); adc_h = (d[6] << 8) | d[7]
        v1 = (adc_t / 16384.0 - T1 / 1024.0) * T2
        v2 = ((adc_t / 131072.0 - T1 / 8192.0) ** 2) * T3
        tf = v1 + v2; t = tf / 5120.0
        v1 = tf / 2.0 - 64000.0; v2 = v1 * v1 * P6 / 32768.0 + v1 * P5 * 2.0; v2 = v2 / 4.0 + P4 * 65536.0
        v1 = (P3 * v1 * v1 / 524288.0 + P2 * v1) / 524288.0; v1 = (1.0 + v1 / 32768.0) * P1
        pr = None
        if v1:
            pp = 1048576.0 - adc_p; pp = (pp - v2 / 4096.0) * 6250.0 / v1
            v1 = P9 * pp * pp / 2147483648.0; v2 = pp * P8 / 32768.0; pr = (pp + (v1 + v2 + P7) / 16.0) / 100.0
        hum = None
        if not self.bmp:
            h = tf - 76800.0
            h = (adc_h - (H4 * 64.0 + H5 / 16384.0 * h)) * (H2 / 65536.0 * (1.0 + H6 / 67108864.0 * h * (1.0 + H3 / 67108864.0 * h)))
            hum = max(0.0, min(100.0, h * (1.0 - H1 * h / 524288.0)))
        return t, hum, pr

    # ---- DS18B20 ----
    @staticmethod
    def _ds18b20():
        out = []
        for path in sorted(glob.glob("/sys/bus/w1/devices/28-*")):
            try:
                with open(os.path.join(path, "w1_slave")) as f:
                    txt = f.read()
                if "YES" in txt and "t=" in txt:
                    v = int(txt.rsplit("t=", 1)[1]) / 1000.0
                    if -55 < v < 125 and v != 85.0:                   # 85.0 = the power-on value, not a measurement
                        out.append(round(v, 2))
            except (OSError, ValueError):
                continue
        return out

    def read(self):
        if CFG.get("sim_on") and time.time() - SIM["t"] < 10:
            hs_ = SIM.get("humidity")                     # Aufräumen 2: the humidity of the scene (world_reply «humidity»)
            return {"t": round(float(SIM["ambient"]), 1), "h": round(float(hs_)) if isinstance(hs_, (int, float)) else None,
                    "p": round(float(SIM["pressure"]), 1), "src": "Simulator", "ds": [], "time": time.time()}
        if self.fd is None and time.time() - self.tried > 120:
            self.tried = time.time(); self._open()
        t = hum = pr = None; src = ""
        if self.fd is not None:
            try:
                t, hum, pr = self._bme(); src = "BMP280" if self.bmp else "BME280"
            except (OSError, ZeroDivisionError):
                try:
                    os.close(self.fd)
                except OSError:
                    pass
                self.fd = None
        ds = self._ds18b20()
        if t is None and ds:
            t, src = ds[0], "DS18B20"
        if t is None:
            return None
        off = float(CFG["env_offset"])
        return {"t": round(t + off, 1), "h": round(hum) if hum is not None else None, "p": round(pr, 1) if pr else None,
                "src": src, "ds": [round(x + off, 1) for x in ds], "time": time.time()}

    def loop(self):
        while True:
            try:
                STATE["env"] = self.read() if CFG["env_on"] else None
                temp_check(STATE["env"])
                if time.time() - self.last_log >= 600:
                    self.last_log = time.time(); climate_log(STATE["env"])
            except Exception as e:
                log_event("sys", f"Climate sensor: {e}"[:160])
            time.sleep(30)


def climate_dir():
    return os.path.join(DATA_DIR, "climate")


def climate_log(env):
    """One line every 10 minutes: time, temperature, humidity, pressure, CPU temperature, battery (%)."""
    bt = STATE.get("battery") or {}
    row = [datetime.now().strftime("%H:%M"), env["t"] if env else None, env["h"] if env else None, env["p"] if env else None,
           STATE.get("cpu_temp"), bt.get("pct") if bt.get("on") else None]
    path = os.path.join(climate_dir(), datetime.now().strftime("%Y-%m-%d") + ".json")
    try:
        os.makedirs(climate_dir(), exist_ok=True)
        try:
            with open(path) as f:
                rows = json.load(f)
        except (OSError, ValueError):
            rows = []
        rows.append(row)
        with open(path + ".tmp", "w") as f:
            json.dump(rows, f, separators=(",", ":"))
        os.replace(path + ".tmp", path)
        keep = max(30, int(CFG["diary_keep_days"]))
        cut = (datetime.now() - timedelta(days=keep)).strftime("%Y-%m-%d")
        for p_ in glob.glob(os.path.join(climate_dir(), "*.json")):
            if os.path.basename(p_)[:10] < cut:
                os.remove(p_)
    except OSError:
        pass


def climate_day(day):
    try:
        with open(os.path.join(climate_dir(), day + ".json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


ENV = None


# ---- weather from the internet (Open-Meteo, free, no account) for the day overview of the diary ----
WMO = [((0,), "☀️", "clear"), ((1, 2), "🌤", "partly cloudy"), ((3,), "☁️", "cloudy"), ((45, 48), "🌫", "fog"), ((51, 53, 55, 56, 57), "🌦", "drizzle"),
       ((61, 63, 65, 66, 67), "🌧", "rain"), ((71, 73, 75, 77, 85, 86), "🌨", "snow"), ((80, 81, 82), "🌦", "showers"), ((95, 96, 99), "⛈", "thunderstorm")]
WEATHER = {"t": 0.0, "status": "off"}


def wmo_text(code):
    for codes, icon, key in WMO:
        if code in codes:
            return icon, key
    return "·", ""


def weather_dir():
    return os.path.join(DATA_DIR, "weather")


def weather_fetch():
    """The last 7 days and today, hour by hour, one file per day (kept like the diary)."""
    g = gps_now()
    if not g:
        WEATHER["status"] = "no location"; return False
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%.3f&longitude=%.3f&timezone=auto&past_days=7&forecast_days=2"
           "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max"
           "&hourly=temperature_2m,precipitation,relative_humidity_2m,weather_code,wind_gusts_10m" % (g[0], g[1]))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MotionWatch/" + APP_VERSION})
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read().decode())
    except Exception as e:
        WEATHER["status"] = f"failed: {e}"[:120]; return False
    weather_store(j)
    WEATHER["t"] = time.time(); WEATHER["status"] = "ok"
    return True


def weather_store(j):
    dl, hl = j.get("daily") or {}, j.get("hourly") or {}
    days = {}
    for i, day in enumerate(dl.get("time") or []):
        days[day] = {"daily": {k: (dl.get(k) or [None] * (i + 1))[i] for k in dl if k != "time"}, "hourly": {}}
    for i, ts in enumerate(hl.get("time") or []):
        day, hh = ts[:10], ts[11:13]
        if day in days:
            days[day]["hourly"][hh] = [(hl.get(k) or [None] * (i + 1))[i] for k in ("temperature_2m", "precipitation", "relative_humidity_2m", "weather_code", "wind_gusts_10m")]
    os.makedirs(weather_dir(), exist_ok=True)
    for day, v in days.items():
        with open(os.path.join(weather_dir(), day + ".json"), "w") as f:
            json.dump(v, f, separators=(",", ":"))


def weather_day(day):
    try:
        with open(os.path.join(weather_dir(), day + ".json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def weather_loop():
    time.sleep(90)
    while True:
        if (CFG["weather_on"] or (CFG["storm_on"] and CFG["storm_forecast"])) and simval_live():
            WEATHER["status"] = "simulator"              # the weather of the simulated scene - no internet call (285)
        elif CFG["weather_on"] or (CFG["storm_on"] and CFG["storm_forecast"]):
            if time.time() - WEATHER["t"] > 3 * 3600:
                weather_fetch()
        else:
            WEATHER["status"] = "off"
        time.sleep(120)


def moon_phase(d):
    """(emoji, name) of the moon phase on a date (mean lunar month since a known new moon)."""
    age = ((datetime(d.year, d.month, d.day, 12) - datetime(2000, 1, 6, 18, 14)).total_seconds() / 86400.0) % 29.530588853
    names = ((1.84, "🌑", "new moon"), (5.53, "🌒", "waxing crescent"), (9.23, "🌓", "first quarter"), (12.92, "🌔", "waxing gibbous"),
             (16.61, "🌕", "full moon"), (20.30, "🌖", "waning gibbous"), (23.99, "🌗", "last quarter"), (27.68, "🌘", "waning crescent"), (30, "🌑", "new moon"))
    for lim, icon, name in names:
        if age < lim:
            return icon, name


def day_summary(day, lang="en"):
    """Everything about one day for the diary: visits, recordings, climate curve, weather, sun, moon, place, night report."""
    try:
        d = datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        return None
    sight_load()
    with SIGHT_LOCK:
        ev = [dict(e) for e in SIGHT["list"] if e["start"][:10] == day]
    ev.sort(key=lambda e: e["start"])
    counts = {}
    for e in ev:
        counts[e["label"]] = counts.get(e["label"], 0) + 1
    animals = sorted(((k, c) for k, c in counts.items() if k in ANIMALS), key=lambda x: -x[1])
    best = sorted((e for e in ev if e.get("img") and e["kind"] == "animal"), key=lambda e: (e.get("fav", False), e.get("conf", 0)), reverse=True)[:4]
    stamp = d.strftime("%Y%m%d"); recs = 0; mb = 0.0; photos = 0; alarm_recs = 0
    try:
        for n in os.listdir(rec_dir()):
            if stamp in n:
                if n.endswith(".mp4"):
                    recs += 1
                    try:
                        mb += os.path.getsize(os.path.join(rec_dir(), n)) / 1048576.0
                        with open(os.path.join(rec_dir(), n[:-4] + ".json")) as f:
                            alarm_recs += 1 if json.load(f).get("persons") else 0
                    except (OSError, ValueError):
                        pass
                elif n.endswith(".jpg"):
                    photos += 1
    except OSError:
        pass
    g = next((e["gps"] for e in ev if e.get("gps")), None)
    if g is None:
        gg = gps_now(); g = [gg[0], gg[1]] if gg else None
    lat, lon = (g[0], g[1]) if g else (float(CFG["latitude"]), float(CFG["longitude"]))
    sim_day = simval_live() and day == sim_now().strftime("%Y-%m-%d")      # the day of the simulated scene: its place and weather (285)
    st = sun_times_here(d.date()) if sim_day else sun_times(d.date(), lat, lon)
    sun = {"rise": f"{int(st[0] // 60):02d}:{int(st[0] % 60):02d}", "set": f"{int(st[1] // 60):02d}:{int(st[1] % 60):02d}",
           "len": f"{int((st[1] - st[0]) // 60)} h {int((st[1] - st[0]) % 60):02d}"} if isinstance(st, tuple) else {"polar": st}
    mi, mn = moon_phase(d)
    w = weather_day(day) if CFG["weather_on"] or weather_day(day) else None
    if sim_day:
        w = None; sw_ = sim_weather_day(lang)
    if w:
        dd = w.get("daily") or {}
        icon, key = wmo_text(dd.get("weather_code"))
        w = {"icon": icon, "text": tr(key, lang) if key else "", "tmax": dd.get("temperature_2m_max"), "tmin": dd.get("temperature_2m_min"),
             "rain": dd.get("precipitation_sum"), "wind": dd.get("wind_speed_10m_max"), "gust": dd.get("wind_gusts_10m_max"), "hourly": w.get("hourly") or {}}
    if sim_day and sw_:
        w = sw_
    rep_txt = ""
    if d.date() <= datetime.now().date():
        hr, fr = int(CFG["report_hour"]) % 24, int(CFG["report_from"]) % 24
        end = d.replace(hour=hr); start = end - timedelta(hours=((hr - fr) % 24) or 24)
        if end > datetime.now():
            end = datetime.now()
        if start < end:
            rep_txt = report_build(lang, start, end)["text"]
    clim = climate_day(day)
    temps = [r[1] for r in clim if r[1] is not None]
    hums = [r[2] for r in clim if r[2] is not None]
    press = [r[3] for r in clim if r[3] is not None]
    return {"day": day, "weekday": d.weekday(),
            "counts": {"persons": counts.get("person", 0), "animals": sum(c for _k, c in animals), "warm": counts.get("warm", 0),
                       "noise": counts.get("noise", 0), "sneezes": (sneeze_count() and _SNEEZE_DAYS["days"].get(day, 0)) or _SNEEZE_DAYS["days"].get(day, 0), "recordings": recs, "alarm_recordings": alarm_recs, "photos": photos, "mb": round(mb, 1)},
            "animals": [{"key": k, "label": tr_trigger(k, lang), "count": c} for k, c in animals],
            "best": [{"img": e["img"], "label": tr_trigger(e["label"], lang), "t": e["start"][11:16]} for e in best],
            "events": [{"t": e["start"][11:16], "kind": e["kind"], "label": tr_trigger(e["label"], lang) if e["kind"] in ("animal", "person", "object") else tr(e["label"], lang)} for e in ev][:400],
            "climate": clim,
            "climate_sum": {"tmin": min(temps) if temps else None, "tmax": max(temps) if temps else None, "hmin": min(hums) if hums else None,
                            "hmax": max(hums) if hums else None, "pmin": min(press) if press else None, "pmax": max(press) if press else None},
            "weather": w, "weather_on": bool(CFG["weather_on"]), "weather_status": WEATHER["status"],
            "sun": sun, "moon": {"icon": mi, "name": tr(mn, lang)}, "gps": g, "report": rep_txt,
            "sim": bool(sim_day), "sim_place": (sim_place() or (0, 0, ""))[2] if sim_day else ""}


MSG_KEYWORDS = {"person": "ALARM", "warm": "WAERME", "noise": "LAERM", "tamper": "SABOTAGE", "prealarm": "VORALARM",
                "info": "INFO", "test": "TEST"}


def msg_keyword(ev):
    """«MoveEye-ALARM» etc. at the start of a message - a shortcut automation on the iPhone reacts to this word (2.95.27;
    up to 2.98.50 the default was «MW»)"""
    if not CFG.get("msg_keyword_on", True):
        return ""
    pre = re.sub(r"[^A-Za-z0-9]", "", str(CFG.get("msg_keyword_prefix") or "MoveEye"))[:12] or "MoveEye"
    return f"{pre}-{MSG_KEYWORDS.get(ev, 'INFO')}"


def email_ready():
    return bool(CFG.get("email_on") and CFG.get("email_host", "").strip() and _EMAIL_RE.fullmatch(CFG.get("email_to", "").strip() or "-"))


_EMAIL_RE = re.compile(r"[^@\s,;]{1,64}@[A-Za-z0-9.\-]{1,190}\.[A-Za-z]{2,24}")


def email_send(subject, text, jpg=None, fname="photo.jpg"):
    """send one e-mail (SMTP: port 465 = SSL, else STARTTLS); returns (ok, message)"""
    import smtplib, ssl
    from email.message import EmailMessage
    to_ = CFG["email_to"].strip(); frm = (CFG.get("email_from") or CFG.get("email_user") or to_).strip()
    m = EmailMessage(); m["Subject"] = subject[:200]; m["From"] = frm; m["To"] = to_
    m.set_content(text or subject)
    if jpg:
        m.add_attachment(jpg, maintype="image", subtype="jpeg", filename=fname)
    host = CFG["email_host"].strip(); port = int(CFG.get("email_port") or 587)
    ctx = ssl.create_default_context()
    try:
        if port == 465:
            srv = smtplib.SMTP_SSL(host, port, timeout=20, context=ctx)
        else:
            srv = smtplib.SMTP(host, port, timeout=20)
            srv.starttls(context=ctx)
        with srv:
            if CFG.get("email_user"):
                srv.login(CFG["email_user"], CFG.get("email_password", ""))
            srv.send_message(m)
        return True, ""
    except Exception as e:
        msg = str(e)
        for sec_ in (CFG.get("email_password"),):
            if sec_:
                msg = msg.replace(sec_, "***")
        return False, msg[:200]


def pushover_ready():
    return bool(CFG.get("pushover_on") and re.fullmatch(r"[A-Za-z0-9]{30}", CFG.get("pushover_user", "").strip())
                and re.fullmatch(r"[A-Za-z0-9]{30}", CFG.get("pushover_token", "").strip()))


def _url_host(u):
    """only the server of an address (the ntfy topic / webhook path is a secret and does not belong in the log)"""
    try:
        from urllib.parse import urlparse
        return (urlparse(str(u).strip()).hostname or "?")
    except ValueError:
        return "?"


# ---- outbox (2.95.35): alarms that could not be sent are kept on the card and sent later (also after a restart) ----
OUTBOX = {"n": 0, "lock": threading.Lock()}


def _outbox_dir():
    return os.path.join(DATA_DIR, "outbox")


def outbox_add(p, jpg, fname):
    try:
        d = _outbox_dir(); os.makedirs(d, exist_ok=True)
        files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        for f in files[:max(0, len(files) - 49)]:        # at most 50 waiting
            for e in (".json", ".jpg"):
                try:
                    os.remove(os.path.join(d, f[:-5] + e))
                except OSError:
                    pass
        k = f"{time.time():.3f}"
        meta = {"p": {x: v for x, v in p.items() if isinstance(v, (str, int, float, bool, type(None)))}, "fname": fname, "t": time.time(), "tries": 0}
        if jpg:
            with open(os.path.join(d, k + ".jpg"), "wb") as f:
                f.write(jpg)
        with open(os.path.join(d, k + ".json"), "w") as f:
            json.dump(meta, f)
        log_event("web", "Alarm message kept in the outbox - it is sent as soon as the connection works")
    except OSError as e:
        log_event("web", f"Outbox: {e}"[:160])


def outbox_count():
    try:
        return sum(1 for f in os.listdir(_outbox_dir()) if f.endswith(".json"))
    except OSError:
        return 0


def outbox_loop():
    """every minute (at once when the internet is back): send what is waiting, oldest first; given up after 24 h"""
    time.sleep(30)
    while True:
        try:
            w = WATCH_REF.get("w"); d = _outbox_dir()
            files = sorted(f for f in os.listdir(d) if f.endswith(".json")) if os.path.isdir(d) else []
            OUTBOX["n"] = len(files)
            real_ok = Notifier.main_configured() and STATE.get("net", {}).get("online") is not False
            if files and w is not None and not sim_net_down():
                for f in files:
                    pj = os.path.join(d, f); pi = pj[:-5] + ".jpg"
                    try:
                        with open(pj) as fh:
                            m = json.load(fh)
                    except (OSError, ValueError):
                        m = None
                    if not m or time.time() - float(m.get("t", 0)) > 86400:
                        for x in (pj, pi):
                            try:
                                os.remove(x)
                            except OSError:
                                pass
                        continue
                    jpg = None
                    if os.path.isfile(pi):
                        with open(pi, "rb") as fh:
                            jpg = fh.read()
                    if m["p"].get("sandbox"):                # kept during a network test of the simulator: into the test inbox (285)
                        p_ = dict(m["p"], late=True)
                        sandbox_add(w.notifier._title(p_), w.notifier._text(p_), jpg, w.notifier._event(p_))
                        msglog_add(w.notifier._title(p_), w.notifier._text(p_), w.notifier._event(p_), jpg, "test", "Test-Postfach · " + tr("sent later"))
                        log_event("web", "Alarm from the outbox sent later into the test inbox")
                        for x in (pj, pi):
                            try:
                                os.remove(x)
                            except OSError:
                                pass
                        continue
                    if not real_ok:
                        continue
                    try:
                        code, where = w.notifier._send_main(dict(m["p"], late=True), jpg, m.get("fname") or "alarm.jpg")
                        log_event("web", f"Alarm from the outbox sent to {where} (HTTP {code})")
                        for x in (pj, pi):
                            try:
                                os.remove(x)
                            except OSError:
                                pass
                    except Exception:
                        break                            # still not possible - next round
            beat("outbox", 600, "Message outbox")
        except Exception as e:
            print(f"outbox: {e}")
        for _ in range(60):                              # every minute - at once when the network is back (285 sets «kick»)
            if OUTBOX.get("kick"):
                break
            time.sleep(1.0)
        OUTBOX["kick"] = False


class Notifier:
    """Alarm message when a person is detected (with cooldown). Three kinds:
         webhook   JSON POST to a URL (Home Assistant, IFTTT, ...)
         ntfy      push to the ntfy app: the snapshot is attached, a tap opens the recordings page
         telegram  photo + caption to a Telegram chat (bot token + chat id)"""
    def __init__(self):
        self.last = 0.0; self.last_pre = 0.0; self.last_warm = 0.0; self.last_noise = 0.0

    @staticmethod
    def main_configured():
        if CFG["notify_type"] == "telegram":
            return bool(CFG["telegram_token"] and CFG["telegram_chat"])
        return bool(CFG["notify_url"].strip())

    @staticmethod
    def configured():
        try:
            if sandbox_active():                         # 2.96.6: the test inbox counts as a channel (141)
                return True
        except NameError:
            pass
        return (Notifier.main_configured() or bool(CFG["webpush_on"] and webpush_subs()) or bool(CFG["sms_on"] and sms_numbers())
                or pushover_ready() or email_ready())

    def person(self, count, snapshot_path=None, frame=None):
        if count and not is_armed():
            STATE["notify_status"] = "disarmed"; return
        if not self.configured():
            STATE["notify_status"] = "off"; return
        if not CFG["notify_on"]:
            STATE["notify_status"] = "paused"; return
        now = time.time()
        if now - self.last < CFG["notify_cooldown"]:
            if count:
                self.more = getattr(self, "more", 0) + 1      # 2.95.35: counted, told with the next message
            return
        self.last = now
        more, self.more = getattr(self, "more", 0), 0
        jpg, fname = None, "snapshot.jpg"
        try:
            if snapshot_path and os.path.isfile(snapshot_path) and os.path.getsize(snapshot_path) < 8 * 1024 * 1024:
                with open(snapshot_path, "rb") as f:
                    jpg = f.read()
                fname = os.path.basename(snapshot_path)
            elif frame is not None:
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                jpg = buf.tobytes() if ok else None
        except OSError:
            jpg = None
        pub = CFG["public_url"].strip().rstrip("/")
        payload = {"event": "person" if count else "test", "persons": int(count), "time": datetime.now().isoformat(timespec="seconds"),
                   "snapshot": snapshot_path, "rain": bool(STATE["rain_mode"]), "wind": STATE["wind_level"],
                   "source": STATE["source_label"], "link": pub + "/recordings" if pub else "", "more": more}
        if count:
            payload["dist"] = person_dist_text()              # 2.98.13: «Person, ca. 12 m, kommt näher» (415)
        threading.Thread(target=self._dispatch, args=(payload, jpg, fname), daemon=True).start()

    def test(self, frame):
        self.last = 0.0
        self.person(0, None, frame)

    def prealarm(self, frame, event="prealarm"):
        """Pre-alarm push: something moves in the picture. Own cooldown; skipped right after a person alarm (that one says more).
        The picture is small (640 px) so it costs little mobile data. event="warm": the thermal camera saw a warm body,
        event="noise": the microphone heard a noise."""
        want = {"warm": True, "noise": CFG["noise_push"]}.get(event, CFG["notify_prealarm"])
        if not (want and CFG["notify_on"] and self.configured() and is_armed()):
            return False
        now = time.time()
        if event == "warm":
            if now - self.last_warm < CFG["notify_cooldown"]:
                return False
            self.last_warm = now
        elif event == "noise":
            if now - self.last_noise < CFG["notify_cooldown"]:
                return False
            self.last_noise = now
        else:
            if now - self.last_pre < CFG["prealarm_cooldown"] or now - self.last < CFG["prealarm_cooldown"]:
                return False
            self.last_pre = now
        jpg = None
        if CFG["prealarm_photo"] and frame is not None:
            h, w = frame.shape[:2]
            small = cv2.resize(frame, (640, int(h * 640 / w)), interpolation=cv2.INTER_AREA) if w > 640 else frame
            ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])
            jpg = buf.tobytes() if ok else None
        pub = CFG["public_url"].strip().rstrip("/")
        payload = {"event": event, "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "snapshot": None,
                   "rain": bool(STATE["rain_mode"]), "wind": STATE["wind_level"], "source": STATE["source_label"],
                   "link": pub + "/" if pub else ""}
        if event == "noise" and AUDIO is not None and AUDIO.level is not None:
            payload["db"] = int(round(AUDIO.level))
        threading.Thread(target=self._dispatch, args=(payload, jpg, "prealarm.jpg"), daemon=True).start()
        return True

    def tamper(self, text, frame=None):
        """Sabotage / theft alarm: always sent (no cooldown of the person alarm), high priority, with the current picture."""
        if not (self.configured() and CFG["notify_on"]):
            return False
        jpg = None
        if frame is not None:
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75]); jpg = buf.tobytes() if ok else None
        pub = CFG["public_url"].strip().rstrip("/")
        payload = {"event": "tamper", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text,
                   "info_title": "{name}: " + tr("TAMPER ALARM"),
                   "snapshot": None, "rain": False, "wind": "", "source": STATE["source_label"], "link": pub + "/" if pub else ""}
        threading.Thread(target=self._dispatch, args=(payload, jpg, "tamper.jpg"), daemon=True).start()
        return True

    def alert(self, title, text, frame=None):
        """Urgent alarm with a custom title (extra sensors): like the sabotage alarm."""
        if not (self.configured() and CFG["notify_on"]):
            return False
        jpg = None
        if frame is not None:
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75]); jpg = buf.tobytes() if ok else None
        pub = CFG["public_url"].strip().rstrip("/")
        payload = {"event": "tamper", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text, "info_title": title,
                   "snapshot": None, "rain": False, "wind": "", "source": STATE["source_label"], "link": pub + "/" if pub else ""}
        threading.Thread(target=self._dispatch, args=(payload, jpg, "alarm.jpg"), daemon=True).start()
        return True

    def info(self, text, link="", title="", jpg=None, fname="info.jpg"):
        """Short information message (e.g. the new address of the page, the night report). Not limited by the alarm cooldown."""
        if not (self.configured() and CFG["notify_on"]):
            return False
        if jpg is None and push_kind({"event": "info", "text": text, "info_title": title}).get("pic"):
            jpg = push_frame_jpg(); fname = "info.jpg"     # 635b: «Protection off» with the current camera picture
        payload = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text, "info_title": title,
                   "snapshot": None, "rain": False, "wind": "", "source": STATE["source_label"], "link": link}
        threading.Thread(target=self._dispatch, args=(payload, jpg, fname if jpg else ""), daemon=True).start()
        return True

    @staticmethod
    def _event(p):
        return p.get("event") if p.get("event") in ("person", "prealarm", "info", "warm", "noise", "tamper") else "test"

    @staticmethod
    def _title(p):
        t_ = push_short(p)["title"]                       # 635b: short, with the symbol (2.96.4: the same symbols everywhere)
        t_ = ("[SIM] " + t_) if CFG.get("sim_on") else t_
        kw = msg_keyword(Notifier._event(p))
        return (kw + " · " + t_) if kw else t_

    @staticmethod
    def _text(p):
        return push_short(p)["text"]                      # 635b: at most one line (distance, «+n», «late» included)

    @staticmethod
    def _sms(p):
        return push_sms_text(Notifier._title(p), Notifier._text(p), p)    # 635b: with the complete map link (theft, position)

    def _dispatch(self, p, jpg, fname):
        if sim_net_down():                               # Simulator-Werte: «WLAN weg» / «Internet weg» test - nothing goes out (285)
            return simnet_hold(self, p, jpg, fname)
        if sandbox_active() or p.get("_test"):           # 2.96.6: simulator test inbox - nobody is disturbed (141); 2.97.0: per message
            sandbox_add(self._title(p), push_with_map(self._text(p), p), jpg, self._event(p) if self._event(p) != "tamper" else "tamper")
            msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), self._event(p), jpg, "test", "Test-Postfach")    # 2.98.13: list «Nachrichten»
            return
        if push_sim_hold(p):                             # 635b: in the simulation only alarms to the phone (switch sim_info_push)
            msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), "info", jpg, "none", "🧪 Simulator")
            return
        if CFG["webpush_on"] and webpush_subs():
            threading.Thread(target=self._webpush, args=(p,), daemon=True).start()
        if CFG["users"]:                                 # 2.98.42: own ntfy topics of the users (041)
            mp_ = push_map(p)                            # 635b: the map - Click + a short line (like ntfy)
            users_push_dispatch(self._title(p), self._text(p) + ("\n" + push_map_line() if mp_ else ""), push_cat("mw-" + self._event(p)), mp_)
        if pushover_ready():
            threading.Thread(target=self._pushover, args=(p, jpg, fname), daemon=True).start()
        ev = self._event(p)
        if email_ready() and (CFG.get("email_events") == "all" or ev in ("person", "warm", "noise", "tamper", "test")):
            def _mail():
                ok, err = email_send(self._title(p), push_long(p) + (("\n" + p["link"]) if p.get("link") else ""), jpg, fname)   # 635b: e-mail complete
                log_event("web", "E-mail sent" if ok else f"E-mail failed: {err}"[:200])
            threading.Thread(target=_mail, daemon=True).start()
        if CFG["sms_on"] and ev in ("person", "tamper", "warm", "noise", "test") and sms_numbers():
            offline = STATE.get("net", {}).get("online") is False
            if not CFG["sms_only_offline"] or offline or not self.main_configured() or ev == "test":
                threading.Thread(target=lambda: sms_send(self._sms(p), force=ev == "test"), daemon=True).start()
        if not self.main_configured():
            msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), ev, jpg, "none", "")
            return
        kind, secret = CFG["notify_type"], CFG["telegram_token"]
        alarm = ev in ("person", "tamper", "warm", "noise")
        tries = 3 if alarm else 1                       # 2.95.33: an alarm is tried 3 times (now, after 5 s, after 15 s)
        for k_ in range(tries):
            try:
                code, where = self._send_main(p, jpg, fname)
                STATE["notify_status"] = f"sent {datetime.now().strftime('%H:%M:%S')} (HTTP {code})"
                log_event("web", f"Notification sent to {where} (HTTP {code})" + (f" - attempt {k_ + 1}" if k_ else ""))
                msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), ev, jpg, "sent", where.split(" ")[0])
                return
            except Exception as e:
                msg = str(e).replace(secret, "***") if secret else str(e)
                msg = msg.replace(CFG["notify_url"].strip(), _url_host(CFG["notify_url"])) if CFG["notify_url"].strip() else msg
                STATE["notify_status"] = f"error: {msg}"[:200]
                log_event("web", f"Notification failed (attempt {k_ + 1}/{tries}): {msg}"[:200])
                try:
                    WATCH_REF["w"].netmon.recheck = True
                except Exception:
                    pass
                if k_ + 1 < tries:
                    time.sleep(5 if k_ == 0 else 10)
        msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), ev, jpg, "failed", kind)
        # all attempts failed: the SMS (if it was held back for "only when offline") goes out now
        if alarm and CFG["sms_on"] and CFG["sms_only_offline"] and sms_numbers() and STATE.get("net", {}).get("online") is not False:
            log_event("web", "Push message could not be sent - SMS instead")
            sms_send(self._sms(p))
        if alarm and not p.get("late"):
            outbox_add(p, jpg, fname)                    # 2.95.35: kept on the card and sent as soon as it works

    def _send_main(self, p, jpg, fname):
        """the main channel (ntfy / Telegram / webhook) once; raises on failure; returns (HTTP code, where)"""
        kind = CFG["notify_type"]
        jpg = sx_push_jpg(jpg)                           # «text only» - the picture stays in MoveEye (578)
        if kind == "telegram":
            return self._telegram(p, jpg, fname), "Telegram"
        if kind == "ntfy":
            return self._ntfy(p, jpg, fname), "ntfy " + _url_host(CFG["notify_url"])
        url = CFG["notify_url"].strip()
        if push_url_is_ntfy(url):                        # 635b: an ntfy address in the webhook card - as ntfy, not as JSON
            return self._ntfy(p, jpg, fname), "ntfy " + _url_host(url)
        body_ = dict(p, title=self._title(p), text=self._text(p), info_title=self._title(p) if p.get("info_title") else "",
                     text_full=push_long(p), map=push_map(p))    # K2: the short form in «text», the complete text for own automations
        req = urllib.request.Request(url, data=json.dumps(body_, ensure_ascii=False).encode(),
                                     headers={"Content-Type": "application/json", "Title": _hdr(self._title(p))})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, _url_host(url)

    def _pushover(self, p, jpg, fname):
        jpg = sx_push_jpg(jpg)                           # (578)
        ev = self._event(p)
        alarm = ev in ("person", "warm", "noise", "tamper")
        prio = 2 if alarm and CFG["pushover_emergency"] else (1 if alarm or ev == "test" else (-1 if ev == "info" else 0))
        f = {"token": CFG["pushover_token"].strip(), "user": CFG["pushover_user"].strip(), "title": self._title(p)[:250],
             "message": push_with_map(self._text(p), p)[:1000] or self._title(p), "priority": str(prio)}
        if prio == 2:
            f.update(retry="60", expire="1800")                 # every minute again, at most 30 minutes, until confirmed
        if push_map(p):                                         # 635b: the map is the link of a message with a position
            f.update(url=push_map(p)[:500], url_title=push_map_line()[:100])
        elif p.get("link"):
            f.update(url=p["link"][:500], url_title="MoveEye")
        b = uuid.uuid4().hex; parts = []
        for k, v in f.items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        if jpg and len(jpg) < 2_500_000:
            parts.append((f'--{b}\r\nContent-Disposition: form-data; name="attachment"; filename="{fname}"\r\n'
                          f'Content-Type: image/jpeg\r\n\r\n').encode() + jpg + b"\r\n")
        parts.append(f"--{b}--\r\n".encode())
        try:
            req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=b"".join(parts),
                                         headers={"Content-Type": "multipart/form-data; boundary=" + b, "User-Agent": "MotionWatch"})
            with urllib.request.urlopen(req, timeout=15) as r:
                log_event("web", f"Pushover sent (priority {prio}, HTTP {r.status})")
                return True, f"HTTP {r.status}"
        except urllib.error.HTTPError as e:
            try:
                why = ", ".join(json.loads(e.read(4000)).get("errors") or [])[:150]
            except Exception:
                why = ""
            log_event("web", f"Pushover failed: HTTP {e.code} {why}"[:200])
            return False, f"HTTP {e.code} {why}"[:150]
        except Exception as e:
            msg = str(e)
            for sec_ in (CFG["pushover_token"], CFG["pushover_user"]):
                if sec_:
                    msg = msg.replace(sec_, "***")
            log_event("web", f"Pushover failed: {msg}"[:200])
            return False, msg[:150]

    def test_all(self, frame=None):
        """2.95.35: every channel on its own, with its result (✓ / ✗ and why) - for «Test all channels»"""
        jpg = None
        if frame is not None:
            ok_, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]); jpg = buf.tobytes() if ok_ else None
        pub = CFG["public_url"].strip().rstrip("/")
        p = {"event": "test", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "snapshot": None, "rain": False, "wind": "",
             "source": STATE["source_label"], "link": pub + "/recordings" if pub else ""}
        res = []
        def run(name, fn):
            try:
                ok, msg = fn()
            except Exception as e:
                ok, msg = False, str(e)
            for sec_ in (CFG["telegram_token"], CFG["pushover_token"], CFG["pushover_user"], CFG.get("email_password", ""), CFG["notify_url"].strip()):
                if sec_ and isinstance(msg, str):
                    msg = msg.replace(sec_, "***")
            res.append({"ch": name, "ok": bool(ok), "msg": str(msg)[:160]})
        if self.main_configured():
            def main_():
                code, where = self._send_main(p, jpg, "test.jpg"); return True, f"{where} · HTTP {code}"
            run({"telegram": "Telegram", "ntfy": "ntfy"}.get(CFG["notify_type"], "Webhook"), main_)
        if pushover_ready():
            run("Pushover", lambda: self._pushover(p, jpg, "test.jpg"))
        if email_ready():
            run("E-Mail", lambda: email_send(self._title(p), push_long(p), jpg, "test.jpg"))
        if CFG["sms_on"] and sms_numbers():
            run("SMS", lambda: sms_send(self._sms(p), force=True))
        if CFG["webpush_on"] and webpush_subs():
            def wp_():
                n = webpush_all(self._title(p), self._text(p), "/", tag="mw-test", urgent=True); return n > 0, f"{n} device(s)"
            run("Web-Push", wp_)
        if CFG.get("mqtt_on"):
            def mq_():
                c_ = MQTT.get("client")
                if c_ is None:
                    return False, MQTT.get("status") or "not connected"
                c_.publish(f"motionwatch/{mqtt_id()}/test" if "mqtt_id" in globals() else "motionwatch/test", "test"); return True, MQTT.get("status") or "connected"
            run("MQTT", mq_)
        log_event("web", "Test of all channels: " + ", ".join(f"{r['ch']} {'ok' if r['ok'] else 'FAILED'}" for r in res))
        return res

    def _webpush(self, p):
        ev = self._event(p)
        try:
            n = webpush_all(self._title(p), push_with_map(self._text(p), p), push_map(p) or ("/" if ev != "info" else (p.get("link") or "/")), tag="mw-" + ev,
                            urgent=ev in ("person", "warm", "noise", "test", "tamper"))
            log_event("web", f"Web push sent to {n} device(s)")
        except Exception as e:
            log_event("web", f"Web push failed: {str(e)[:150]}")

    def _ntfy(self, p, jpg, fname):
        ev = self._event(p)
        h = {"Title": _hdr(self._title(p)), "Tags": {"person": "warning,camera", "prealarm": "eyes,camera", "info": "signal_strength", "warm": "fire,camera",
                                   "noise": "loud_sound,ear", "tamper": "rotating_light,warning"}.get(ev, "camera"),
             "Priority": {"person": "high", "warm": "high", "noise": "high", "prealarm": "default", "tamper": "urgent"}.get(ev, "default")}
        if CFG.get("msg_icons", True):                   # 635b: the symbol is in the title - no second emoji from the tags
            h.pop("Tags")
        mp_ = push_map(p)
        if mp_ or p["link"]:
            h["Click"] = mp_ or p["link"]                # 635b: a message with a position opens the map
        try:
            acts = alx_ntfy_actions(p)                   # 2.98.13: buttons «False alarm · Siren · Off» (066)
        except Exception:
            acts = ""
        if acts:
            h["Actions"] = _hdr(acts)
        text = self._text(p)
        if mp_:                                          # 635b: + a short line «📍 Open map» (in the header: one line, « · »)
            text += (" · " if jpg else "\n") + push_map_line()
        if jpg:
            h["Filename"] = fname; h["Message"] = _hdr(text); h["Content-Type"] = "image/jpeg"
            req = urllib.request.Request(CFG["notify_url"].strip(), data=jpg, headers=h, method="PUT")
        else:
            req = urllib.request.Request(CFG["notify_url"].strip(), data=text.encode(), headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status

    def _telegram(self, p, jpg, fname):
        base = f"{TELEGRAM_API}/bot{CFG['telegram_token']}"
        body_txt = push_with_map(self._text(p), p)        # 635b: the complete map link of a message with a position
        text = self._title(p) + "\n" + body_txt + (("\n" + p["link"]) if p["link"] and p["link"] not in body_txt else "")
        try:
            mk = None if p.get("_no_kb") else alx_telegram_markup(p)    # 2.98.13: link buttons (066)
        except Exception:
            mk = None
        if mk:
            try:
                return self._telegram_send(base, p, jpg, fname, text, mk)
            except urllib.error.HTTPError as e:
                if e.code != 400:
                    raise
                log_event("web", "Telegram refused the buttons (address of the page?) - sent without")
        return self._telegram_send(base, p, jpg, fname, text, None)

    def _telegram_send(self, base, p, jpg, fname, text, mk):
        if jpg:
            b = uuid.uuid4().hex
            parts = []
            for k, v in (("chat_id", CFG["telegram_chat"]), ("caption", text)) + ((("reply_markup", json.dumps(mk)),) if mk else ()):
                parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
            parts.append((f'--{b}\r\nContent-Disposition: form-data; name="photo"; filename="{fname}"\r\n'
                          f'Content-Type: image/jpeg\r\n\r\n').encode() + jpg + b"\r\n")
            parts.append(f"--{b}--\r\n".encode())
            req = urllib.request.Request(base + "/sendPhoto", data=b"".join(parts), headers={"Content-Type": "multipart/form-data; boundary=" + b})
        else:
            req = urllib.request.Request(base + "/sendMessage", data=json.dumps(dict({"chat_id": CFG["telegram_chat"], "text": text}, **({"reply_markup": mk} if mk else {}))).encode(),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status


