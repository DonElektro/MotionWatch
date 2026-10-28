#@ Motion Watch – Teil 420: Web-Zugang, Aufnahmen, Speicher, Bild für andere Programme. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Web access options (set on the command line) + self-signed certificate + systemd unit
# ----------------------------------------------------------------------------
WEB_OPTS = {"bind": "0.0.0.0", "https": False, "cert": "", "key": ""}


def ensure_cert():
    """Use the given certificate, or create (once) a self-signed one next to the script. Returns (cert, key) or (None, None)."""
    if WEB_OPTS["cert"] and WEB_OPTS["key"]:
        return WEB_OPTS["cert"], WEB_OPTS["key"]
    cert, key = os.path.join(DATA_DIR, "motionwatch_cert.pem"), os.path.join(DATA_DIR, "motionwatch_key.pem")
    if os.path.isfile(cert) and os.path.isfile(key):
        return cert, key
    if shutil.which("openssl") is None:
        return None, None
    import socket
    host = socket.gethostname()
    for san in (f"subjectAltName=DNS:localhost,DNS:{host},DNS:{host}.local,IP:127.0.0.1", None):
        cmd = ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "3650", "-subj", f"/CN={host}"]
        if san:
            cmd += ["-addext", san]
        try:
            if subprocess.run(cmd, capture_output=True, timeout=60).returncode == 0:
                os.chmod(key, 0o600)
                log_event("web", "Self-signed certificate created (browsers will show a warning once; import the .pem to remove it)")
                return cert, key
        except (OSError, subprocess.SubprocessError):
            pass
    return None, None


def service_text():
    import shlex
    args = [a for a in sys.argv[1:] if a not in ("--print-service", "--install-service")]
    if "--headless" not in args:
        args.append("--headless")
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "pi"
    exe = " ".join(shlex.quote(x) for x in [sys.executable, os.path.abspath(__file__)] + args)
    return f"""[Unit]
Description=MoveEye (camera motion / person detection)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={HERE}
ExecStart={exe}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""


def install_service():
    path = "/etc/systemd/system/motionwatch.service"
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        print("Installing a system service needs root. Run the same command again with sudo, e.g.:\n"
              f"   sudo {sys.executable} {os.path.abspath(__file__)} --install-service {' '.join(a for a in sys.argv[1:] if a != '--install-service')}\n"
              "or print the unit file with --print-service and install it yourself."); return 1
    with open(path, "w") as f:
        f.write(service_text())
    for cmd in (["systemctl", "daemon-reload"], ["systemctl", "enable", "--now", "motionwatch.service"]):
        print("$", " ".join(cmd)); subprocess.run(cmd)
    print(f"Service installed ({path}). Status: systemctl status motionwatch   Log: journalctl -u motionwatch -f")
    return 0


# ----------------------------------------------------------------------------
# Recordings backend (used by the preview page /recordings)
#   person_YYYYmmdd_HHMMSS.mp4   video          person_YYYYmmdd_HHMMSS.jpg   snapshot of the same event
#   person_YYYYmmdd_HHMMSS.json  info file (source, schedules, duration, codec) written when a recording ends
#   snapshot_*.jpg               manual snapshots
# Thumbnails are cached in recordings/.thumbs, browser-playable copies in recordings/.cache
# ----------------------------------------------------------------------------
REC_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,120}$")
REC_EXTS = {".mp4": "video", ".jpg": "image"}
_STAMP_RE = re.compile(r"(\d{8})_(\d{6})")
BROWSER_CODECS = {"avc1", "h264", "x264"}                   # what <video> can play everywhere (MPEG-4 part 2 "mp4v" cannot)
class _ExpiringSet(dict):
    """«x in s» is true for 10 minutes after s.add(x) (2.95.33: a removed USB disk must not disable the encoders for good)"""
    def add(self, k):
        self[k] = time.time()

    def __contains__(self, k):
        t = self.get(k)
        return t is not None and time.time() - t < 600


_BAD_CODECS = _ExpiringSet()                                # encoders that failed lately (avc1 is missing in many OpenCV builds)
_REC_META = {}                                              # name -> [mtime, size, meta, probed]
_TRANSCODE = {}                                             # name -> "running" | "done" | "error: ..."
_TRANSCODE_LOCK = threading.Lock()
_TRANSCODE_SEM = threading.Semaphore(1)                     # one conversion at a time, the detection must keep running


# ---- encoder: ffmpeg pipe (hardware H.264 on Pi 3/4, x264 elsewhere) ------------------------------------------
_ENC = {"hw": None}


def _ffmpeg_hw_ok():
    if _ENC["hw"] is None:
        try:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
                                "-frames:v", "5", "-c:v", "h264_v4l2m2m", "-pix_fmt", "yuv420p", "-f", "null", "-"],
                               capture_output=True, timeout=20)
            _ENC["hw"] = r.returncode == 0
        except Exception:
            _ENC["hw"] = False
    return _ENC["hw"]


class FfmpegWriter:
    """Looks like cv2.VideoWriter, but pipes the frames into ffmpeg from a background thread, so the detection never waits
    for the encoder. Fragmented MP4: a recording survives a power loss up to the last few seconds."""
    def __init__(self, path, fps, size, hw):
        w, h = size
        enc = ["-c:v", "h264_v4l2m2m", "-b:v", "4M"] if hw else ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "25"]
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-framerate", f"{fps:.2f}",
               "-i", "-", "-an", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"] + enc + \
              ["-movflags", "+frag_keyframe+empty_moov+default_base_moof", path]
        if shutil.which("nice"):
            cmd = ["nice", "-n", "5"] + cmd
        self.size = (w, h); self.failed = False; self.dropped = 0; self.hw = hw; self.t_open = time.time()
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.q = queue.Queue(maxsize=max(4, min(60, int(150e6 / max(1, w * h * 3)))))   # 2.95.33: at most ~150 MB of frames
        self.th = threading.Thread(target=self._pump, daemon=True); self.th.start()

    def _pump(self):
        while True:
            item = self.q.get()
            if item is None:
                break
            try:
                self.proc.stdin.write(item)
            except (BrokenPipeError, OSError, ValueError):
                self.failed = True
                break
        try:
            self.proc.stdin.close()
        except Exception:
            pass

    def isOpened(self):
        return self.proc.poll() is None and not self.failed

    def write(self, frame):
        if self.failed or self.proc.poll() is not None:
            self.failed = True; return
        try:
            self.q.put_nowait(frame.tobytes())
        except queue.Full:
            self.dropped += 1                                   # encoder too slow: drop a frame instead of stalling the detection

    def release(self):
        try:
            self.q.put(None, timeout=5)
        except queue.Full:
            self.proc.kill()
        self.th.join(30)
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def open_writer(path, fps, size):
    """Open a video writer. H.264 plays in every browser. Order: ffmpeg (hardware, then x264) -> OpenCV 'avc1' -> OpenCV 'mp4v'
    (mp4v is the last resort; the preview page converts such files on first play). Returns (writer or None, codec)."""
    d_ = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(d_, exist_ok=True)
    except OSError:
        pass
    if not os.access(d_, os.W_OK):
        return None, ""                                       # the folder (USB disk?) is missing / read-only: not the encoders' fault
    if CFG["record_encoder"] == "auto" and "ffmpeg" not in _BAD_CODECS and shutil.which("ffmpeg"):
        for hw in ((True, False) if _ffmpeg_hw_ok() else (False,)):
            if hw and ("ffmpeg_hw" in _BAD_CODECS or size[0] > 1920 or size[1] > 1088):
                continue                                      # the Pi hardware encoder: max 1920x1088, or it died lately
            try:
                w = FfmpegWriter(path, fps, size, hw)
                time.sleep(0.2)
                if w.isOpened():
                    STATE["recording_enc"] = "ffmpeg h264_v4l2m2m (hardware)" if hw else "ffmpeg x264"
                    return w, "h264"
                w.release()
            except Exception:
                pass
            try:
                os.remove(path)
            except OSError:
                pass
        _BAD_CODECS.add("ffmpeg")
    for cc in ("avc1", "mp4v"):
        if cc in _BAD_CODECS:
            continue
        try:
            w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*cc), fps, size)
        except Exception:
            w = None
        if w is not None and w.isOpened():
            STATE["recording_enc"] = "OpenCV " + cc
            return w, cc
        _BAD_CODECS.add(cc)
        if w is not None:
            w.release()
        try:
            os.remove(path)
        except OSError:
            pass
    return None, ""


# ---- storage: SD card / SSD / USB drive -------------------------------------------------------------------------------
STORE = {"fallback": False, "moving": False, "msg": ""}
_FS_OK = {"ext4", "ext3", "ext2", "btrfs", "xfs", "f2fs", "vfat", "exfat", "ntfs", "ntfs3", "fuseblk"}


def _mounts():
    out = []
    try:
        with open("/proc/mounts") as f:
            for line in f:
                p = line.split()
                if len(p) >= 3:
                    out.append((p[0], p[1].replace("\\040", " "), p[2]))
    except OSError:
        pass
    return out


def _dev_kind(dev):
    d = os.path.basename(dev or "")
    if d.startswith("mmcblk"):
        return "sd"
    if d.startswith("nvme"):
        return "ssd"
    if d.startswith("sd"):
        return "usb"
    return "other"


def _mount_of(path):
    """(device, mount point, fs type) that holds this path."""
    path = os.path.realpath(path); best = ("", "/", "")
    for dev, mp, fs in _mounts():
        if (path == mp or path.startswith(mp.rstrip("/") + "/")) and len(mp) >= len(best[1]):
            best = (dev, mp, fs)
    return best


def storage_candidates():
    """Drives the recordings can be put on: SSD / USB mounted somewhere else than the system."""
    root_dev = _mount_of("/")[0]
    out = []
    for dev, mp, fs in _mounts():
        if fs not in _FS_OK or not dev.startswith("/dev/") or mp in ("/", "/boot", "/boot/firmware") or dev == root_dev:
            continue
        if not (mp.startswith(("/media/", "/mnt/", "/srv/")) or _dev_kind(dev) in ("ssd", "usb")):
            continue
        try:
            du = shutil.disk_usage(mp)
        except OSError:
            continue
        out.append({"path": mp, "kind": _dev_kind(dev), "fs": fs, "free_gb": round(du.free / 1024 ** 3, 1),
                    "total_gb": round(du.total / 1024 ** 3, 1), "writable": os.access(mp, os.W_OK), "fat": fs == "vfat"})
    return out


def storage_info():
    sysdev, _mp, _fs = _mount_of("/")
    rdev, rmp, rfs = _mount_of(rec_dir() if os.path.isdir(rec_dir()) else os.path.dirname(rec_dir()) or "/")
    return {"system": _dev_kind(sysdev), "rec": _dev_kind(rdev), "rec_mount": rmp, "rec_fs": rfs, "rec_dir": rec_dir(),
            "want": CFG["storage_path"], "fallback": STORE["fallback"], "moving": STORE["moving"], "msg": STORE["msg"],
            "candidates": storage_candidates()}


def storage_apply(start=False):
    """Set the recordings folder from the chosen drive. Missing drive: the memory card next to the program."""
    want = CFG["storage_path"].strip()
    if not want:
        CFG["record_dir"] = "recordings"; STORE["fallback"] = False; return True
    target = os.path.join(want, "MotionWatch", "recordings")
    ok = os.path.ismount(want) or os.path.isdir(want)
    if ok and want.startswith(("/media/", "/mnt/")):           # 2.95.34: the folder of an unplugged drive is the SD card
        q = os.path.abspath(want)
        while q not in ("/", "/media", "/mnt") and not os.path.ismount(q):
            q = os.path.dirname(q)
        ok = q not in ("/", "/media", "/mnt")
    if ok:
        try:
            os.makedirs(target, exist_ok=True)
            probe = os.path.join(target, ".mw_probe")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
        except OSError:
            ok = False
    if ok:
        CFG["record_dir"] = target; STORE["fallback"] = False
        return True
    CFG["record_dir"] = "recordings"; STORE["fallback"] = True
    log_event("sys", f"Storage: drive {want} not found or not writable - recordings go to the memory card for now")
    return False


def storage_set(path, move=True):
    """Choose where the recordings go ('' = memory card). Moves the existing recordings in the background."""
    path = str(path or "").strip()
    if path and not any(c["path"] == path for c in storage_candidates()):
        return False, "drive not found"
    if STORE["moving"]:
        return False, "already moving recordings - wait a moment"
    old = rec_dir()
    CFG["storage_path"] = path
    if not storage_apply():
        CFG["storage_path"] = ""; storage_apply()
        return False, "the drive cannot be written to"
    save_settings()
    new = rec_dir()
    log_event("sys", f"Storage: recordings now in {new}")
    if move and os.path.isdir(old) and os.path.realpath(old) != os.path.realpath(new):
        def run():
            STORE.update(moving=True, msg="moving recordings …"); n = 0
            try:
                for nm in os.listdir(old):
                    src, dst = os.path.join(old, nm), os.path.join(new, nm)
                    if nm.startswith(".") or os.path.exists(dst) or _is_live(nm, WATCH_REF.get("w")) or (nm == "loop" and LOOPREC is not None and LOOPREC.cur):
                        continue
                    try:
                        shutil.move(src, dst); n += 1
                    except (OSError, shutil.Error):
                        pass
                STORE["msg"] = f"{n} files moved"
                log_event("sys", f"Storage: {n} files moved to {new}")
            finally:
                STORE["moving"] = False
        threading.Thread(target=run, daemon=True, name="storage-move").start()
    return True, ""


LOOP_RE = re.compile(r"^loop/(\d{4}-\d{2}-\d{2})/(\d{2})-(\d{2})\.mp4$")


def loop_dir():
    return os.path.join(rec_dir(), "loop")


class LoopRecorder:
    """Continuous recording: every picture-per-second interval one picture into 10-minute files loop/<day>/<HH-MM>.mp4,
    kept for loop_hours. Runs in its own thread (the camera loop only hands over a copy now and then)."""
    SEG = 600

    def __init__(self):
        self.q = queue.Queue(maxsize=8); self.next_t = 0.0; self.wr = None; self.cur = ""; self.seg_end = 0.0
        self.size = None; self.last_clean = 0.0
        threading.Thread(target=self.loop, daemon=True, name="looprec").start()

    def feed(self, frame, t0):
        if not CFG["loop_on"] or frame is None or t0 < self.next_t:
            return
        self.next_t = t0 + 1.0 / max(1, int(CFG["loop_fps"]))
        try:
            self.q.put_nowait((frame.copy(), time.time()))
        except queue.Full:
            pass

    def _close(self):
        if self.wr is not None:
            try:
                self.wr.release()
            except Exception:
                pass
            LIVE_RECS.discard(self.cur)
        self.wr = None; self.cur = ""

    def loop(self):
        while True:
            try:
                self._step()
            except Exception as e:                         # 2.95.33: e.g. the USB disk was removed - try again later
                log_event("rec", f"Continuous recording: {type(e).__name__}: {e}"[:200])
                try:
                    self._close()
                except Exception:
                    self.wr = None
                time.sleep(30)

    def _step(self):
        beat("looprec", 120, "Continuous recording")
        if True:
            try:
                frame, t = self.q.get(timeout=5)
            except queue.Empty:
                if not CFG["loop_on"]:
                    self._close()
                self._clean()
                return
            if not CFG["loop_on"]:
                self._close(); return
            h, w = frame.shape[:2]
            if w > 1280:
                frame = cv2.resize(frame, (1280, int(h * 1280 / w))); h, w = frame.shape[:2]
            if self.wr is None or t >= self.seg_end or self.size != (w, h):
                self._close()
                dt = datetime.fromtimestamp(t)
                start = dt.replace(minute=dt.minute - dt.minute % 10, second=0, microsecond=0)
                self.seg_end = start.timestamp() + self.SEG
                name = f"loop/{start:%Y-%m-%d}/{start:%H-%M}.mp4"
                path = os.path.join(rec_dir(), name)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                k_ = 1
                while os.path.exists(path):                       # restarted / clock change: a new piece, never overwrite
                    name = f"loop/{start:%Y-%m-%d}/{start:%H-%M}_{k_}.mp4"; path = os.path.join(rec_dir(), name); k_ += 1
                wr, _codec = open_writer(path, max(1, int(CFG["loop_fps"])), (w, h))
                if wr is None:
                    time.sleep(10); return
                self.wr, self.cur, self.size = wr, name, (w, h); LIVE_RECS.add(name)
            try:
                self.wr.write(frame)
            except Exception:
                self._close()
            self._clean()

    def _clean(self):
        now = time.time()
        if now - self.last_clean < 60:
            return
        self.last_clean = now
        keep = float(CFG["loop_hours"]) * 3600
        base = loop_dir()
        try:
            days = sorted(os.listdir(base))
        except OSError:
            return
        for d in days:
            dp = os.path.join(base, d)
            try:
                for n in os.listdir(dp):
                    p = os.path.join(dp, n)
                    if f"loop/{d}/{n}" != self.cur and now - os.path.getmtime(p) > keep:
                        os.remove(p)
                if not os.listdir(dp) and not self.cur.startswith(f"loop/{d}/"):
                    os.rmdir(dp)
            except OSError:
                pass
        try:                                                      # memory almost full: the oldest pieces go first
            while shutil.disk_usage(base).free < 1024 ** 3:
                files = sorted(glob.glob(os.path.join(base, "*", "*.mp4")))
                files = [f for f in files if not f.endswith(self.cur.split("/", 1)[-1])]
                if not files:
                    break
                os.remove(files[0])
        except OSError:
            pass


LOOPREC = None


def loop_day(day):
    """Pieces of one day and the alarm recordings of that day (for the timeline)."""
    out = {"day": day, "segments": [], "events": [], "days": []}
    try:
        out["days"] = sorted(os.listdir(loop_dir()), reverse=True)[:60]
    except OSError:
        pass
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or ""):
        return out
    dp = os.path.join(loop_dir(), day)
    try:
        names = sorted(os.listdir(dp))
    except OSError:
        names = []
    for n in names:
        m = re.fullmatch(r"(\d{2})-(\d{2})\.mp4", n)
        if not m:
            continue
        try:
            st = os.stat(os.path.join(dp, n))
        except OSError:
            continue
        name = f"loop/{day}/{n}"
        out["segments"].append({"name": name, "start": f"{m.group(1)}:{m.group(2)}", "size": st.st_size, "live": name in LIVE_RECS,
                                "min": int(m.group(1)) * 60 + int(m.group(2))})
    stamp = day.replace("-", "")
    try:
        for n in os.listdir(rec_dir()):
            if stamp in n and n.endswith((".mp4", ".jpg")):
                dt = parse_stamp(n)
                if dt is not None and dt.strftime("%Y-%m-%d") == day:
                    out["events"].append(dt.hour * 60 + dt.minute)
    except OSError:
        pass
    out["events"] = sorted(set(out["events"]))
    return out


# ---- picture for other programs: MJPEG + still picture under a secret address, optional RTSP (mediamtx + ffmpeg) ----
EXT = {"proc": None, "ff": None, "msg": "", "port": None}


def ext_token():
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,64}", CFG["ext_token"] or ""):
        CFG["ext_token"] = secrets.token_urlsafe(18); save_settings()
    return CFG["ext_token"]


def ext_new_token():
    CFG["ext_token"] = secrets.token_urlsafe(18); save_settings(); rtsp_restart()
    log_event("web", "Address for other programs renewed - the old one no longer works")


def ext_links(host=None):
    if not CFG["ext_on"]:
        return {"on": False}
    base = page_address(host).rstrip("/") if host or page_address() else f"http://<pi-ip>:{CFG['web_port']}"
    tok = ext_token()
    out = {"on": True, "mjpeg": f"{base}/x/{tok}/video.mjpg", "jpg": f"{base}/x/{tok}/snapshot.jpg", "rtsp": "", "rtsp_msg": EXT["msg"]}
    if CFG["rtsp_on"]:
        h = base.split("://", 1)[-1].split("/", 1)[0].rsplit(":", 1)[0]
        out["rtsp"] = f"rtsp://motionwatch:{tok}@{h}:{int(CFG['rtsp_port'])}/motionwatch"
    return out


def _mediamtx_bin():
    for p in (shutil.which("mediamtx"), os.path.join(DATA_DIR, "mediamtx", "mediamtx"), os.path.expanduser("~/mediamtx/mediamtx"), "/usr/local/bin/mediamtx"):
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def rtsp_stop():
    for k in ("ff", "proc"):
        p = EXT.get(k)
        if p is not None:
            try:
                p.terminate(); p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        EXT[k] = None


def rtsp_restart():
    rtsp_stop()
    if CFG["rtsp_on"] and CFG["ext_on"]:
        threading.Thread(target=rtsp_start, daemon=True, name="rtsp").start()


def rtsp_start():
    """mediamtx serves RTSP (reading needs the secret, publishing only from this Pi); ffmpeg turns the MJPEG into H.264."""
    mtx = _mediamtx_bin()
    if not mtx:
        EXT["msg"] = "mediamtx is not installed (see the manual: RTSP)"; return
    if not shutil.which("ffmpeg"):
        EXT["msg"] = "ffmpeg is missing (sudo apt install ffmpeg)"; return
    tok = ext_token(); port = int(CFG["rtsp_port"])
    cfg_dir = os.path.join(DATA_DIR, "mediamtx"); os.makedirs(cfg_dir, exist_ok=True)
    yml = os.path.join(cfg_dir, "motionwatch.yml")
    with open(yml, "w") as f:
        f.write("logLevel: warn\nrtspAddress: :%d\nrtmp: no\nhls: no\nwebrtc: no\nsrt: no\napi: no\nmetrics: no\npprof: no\nplayback: no\n"
                "authInternalUsers:\n- user: any\n  pass:\n  ips: ['127.0.0.1/32', '::1/128']\n  permissions:\n  - action: publish\n"
                "- user: motionwatch\n  pass: %s\n  ips: []\n  permissions:\n  - action: read\n    path: motionwatch\n"
                "paths:\n  motionwatch:\n" % (port, tok))
    os.chmod(yml, 0o600)
    try:
        EXT["proc"] = subprocess.Popen([mtx, yml], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=cfg_dir)
    except OSError as e:
        EXT["msg"] = f"mediamtx: {e}"[:120]; return
    time.sleep(2)
    if EXT["proc"].poll() is not None:
        err = (EXT["proc"].stderr.read() or b"").decode(errors="replace").strip().splitlines()
        EXT["msg"] = ("mediamtx: " + (err[-1] if err else "stopped"))[:160]; EXT["proc"] = None; return
    src = f"http://127.0.0.1:{CFG['web_port']}/x/{tok}/video.mjpg"
    if WEB_OPTS.get("https"):
        src = src.replace("http://", "https://")
    cmd = ["ffmpeg", "-loglevel", "error", "-tls_verify", "0", "-f", "mjpeg", "-i", src, "-an", "-c:v", "libx264", "-preset", "ultrafast",
           "-tune", "zerolatency", "-g", "30", "-pix_fmt", "yuv420p", "-f", "rtsp", "-rtsp_transport", "tcp", f"rtsp://127.0.0.1:{port}/motionwatch"]
    if not WEB_OPTS.get("https"):
        cmd.remove("-tls_verify"); cmd.remove("0")
    try:
        EXT["ff"] = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        EXT["msg"] = "running"
        log_event("web", f"RTSP video on port {port} (for recorders)")
    except OSError as e:
        EXT["msg"] = f"ffmpeg: {e}"[:120]


def rtsp_watch():
    """Keeps RTSP running while it is switched on (restarts ffmpeg / mediamtx when they stop)."""
    while True:
        time.sleep(15)
        want = CFG["rtsp_on"] and CFG["ext_on"]
        alive = EXT["proc"] is not None and EXT["proc"].poll() is None and EXT["ff"] is not None and EXT["ff"].poll() is None
        if want and not alive:
            rtsp_restart()
        elif not want and (EXT["proc"] or EXT["ff"]):
            rtsp_stop(); EXT["msg"] = ""


atexit.register(rtsp_stop)


def mem_info():
    """RAM of the Pi from /proc/meminfo (MB): total, used (without cache), percent; swap used."""
    m = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1); m[k] = int(v.split()[0]) // 1024
    except (OSError, ValueError):
        return None
    tot = m.get("MemTotal") or 0; avail = m.get("MemAvailable", m.get("MemFree", 0))
    if not tot:
        return None
    return {"total": tot, "used": tot - avail, "pct": round((tot - avail) * 100.0 / tot, 1), "swap": (m.get("SwapTotal", 0) - m.get("SwapFree", 0))}


def rec_dir():
    return os.path.abspath(CFG["record_dir"])


