#@ Motion Watch – Teil 200: Video-Quellen (USB, Pi-Kamera, Netz). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Main detector
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Video sources
#   usb:<n>   USB / V4L2 webcams (/dev/video<n>)        pi:<n>   Raspberry Pi CSI cameras (picamera2)
#   url:<id>  network cameras: RTSP / HTTP-MJPEG (IP cams, Wi-Fi cams) saved in the settings
#   auto      first working USB camera (the behaviour of the older versions)
# Every source object offers read() -> (ok, BGR frame) and release(), so the main loop does not care where the picture comes from.
# ----------------------------------------------------------------------------
SRC_RE = re.compile(r"^(auto|demo|usb:\d{1,2}|pi:\d{1,2}|url:[0-9a-f]{8}|senxor:0|sim:\d|sim:thermal)$")
MAX_IP_SOURCES = 16
V4L_SKIP = ("bcm2835-codec", "bcm2835-isp", "rpivid", "pispbe", "rp1-cfe", "hevc", "-decoder", "-encoder")   # Pi internal nodes, no cameras
SOURCES = {"items": [], "time": 0.0, "scanning": False, "hints": []}      # result of the last scan
_SCAN_LOCK = threading.Lock()


def _url_ok(u):
    return isinstance(u, str) and len(u) <= 500 and re.match(r"^(rtsp|rtsps|http|https)://[^\s]+$", u, re.I) is not None


def mask_url(u):
    """rtsp://user:secret@host/x -> rtsp://user:***@host/x  (passwords are never shown or sent to the browser)."""
    return re.sub(r"(://[^/@:\s]+):[^/@\s]*@", r"\1:***@", u or "")


def _clean_ip_sources(lst):
    out, seen = [], set()
    for s in (lst if isinstance(lst, list) else [])[:MAX_IP_SOURCES]:
        if not isinstance(s, dict):
            continue
        sid, url = str(s.get("id", "")), str(s.get("url", "")).strip()
        if not re.fullmatch(r"[0-9a-f]{8}", sid) or sid in seen or not _url_ok(url):
            continue
        seen.add(sid)
        out.append({"id": sid, "name": str(s.get("name") or "").strip()[:40] or "Network camera", "url": url})
    return out


def find_ip_source(sid):
    for s in CFG["ip_sources"]:
        if s["id"] == sid:
            return s
    return None


_ROT = {"90": cv2.ROTATE_90_CLOCKWISE, "180": cv2.ROTATE_180, "270": cv2.ROTATE_90_COUNTERCLOCKWISE}


def cam_orient(frame):
    """Turn / mirror the camera picture as set (camera mounted sideways or upside down). Everything after sees it upright."""
    r = _ROT.get(str(CFG.get("cam_rotate", "0")))
    if r is not None:
        frame = cv2.rotate(frame, r)
    if CFG.get("cam_mirror"):
        frame = cv2.flip(frame, 1)
    return frame


class CvSource:
    """A camera read through OpenCV (USB webcam or network stream)."""
    def __init__(self, cap, size=None):
        self.cap = cap; self.size = size; self.full_fps = None

    def read(self):
        return self.cap.read()

    def set_fps(self, fps):
        """fps=None: full speed again. Many USB cameras can go slower; if not, nothing happens."""
        try:
            if self.full_fps is None:
                self.full_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
            self.cap.set(cv2.CAP_PROP_FPS, float(fps or self.full_fps))
        except Exception:
            pass

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass


class PiCamSource:
    """Raspberry Pi camera (CSI) through picamera2 / libcamera."""
    def __init__(self, index):
        from picamera2 import Picamera2                     # ImportError -> "not installed" message
        self.cam = Picamera2(index)
        self.cam.configure(self.cam.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"}))
        self.cam.start()
        self.size = (1280, 720)

    def read(self):
        try:
            return True, self.cam.capture_array("main")     # "RGB888" is delivered in B,G,R order = what OpenCV expects
        except Exception:
            return False, None

    def set_fps(self, fps):
        try:
            self.cam.set_controls({"FrameRate": float(fps or 30.0)})
        except Exception:
            pass

    def release(self):
        for fn in ("stop", "close"):
            try:
                getattr(self.cam, fn)()
            except Exception:
                pass


def _v4l_internal(idx):
    """2.98.24: /dev/video<idx> is an internal node of the Raspberry Pi (on a Pi 5 the CSI camera itself shows up as rp1-cfe
    nodes video0 … video7): no USB camera - opening it with OpenCV hangs or blocks the Pi camera."""
    try:
        name = _v4l_name(idx).lower()
    except NameError:
        return False
    return any(b in name for b in V4L_SKIP)


def _pi_cams():
    """numbers of the Raspberry Pi cameras (CSI) that libcamera sees, [] without picamera2"""
    try:
        from picamera2 import Picamera2
        return [int(i.get("Num", n)) for n, i in enumerate(Picamera2.global_camera_info()) if "usb" not in str(i.get("Id", "")).lower()]
    except Exception:
        return []


def _open_usb(idx, raw=False):
    """raw=True for thermal cameras: they have their own small resolution and formats, so nothing is forced on them."""
    if _v4l_internal(idx):
        return None
    for backend, name in ((cv2.CAP_V4L2, "V4L2"), (cv2.CAP_ANY, "default")):
        cap = cv2.VideoCapture(idx, backend)
        if cap.isOpened():
            if not raw:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ok, frame = cap.read()
            if ok:
                return CvSource(cap, (frame.shape[1], frame.shape[0]))
        cap.release()
    return None


def _open_url(url):
    if url.lower().startswith("rtsp"):
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")     # TCP is far more reliable over Wi-Fi
    cap = None
    try:                                                    # connect / read time-outs (OpenCV >= 4.5.2)
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 8000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 8000])
    except Exception:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    ok, frame = cap.read() if cap.isOpened() else (False, None)
    if not ok:
        cap.release()
        return None
    return CvSource(cap, (frame.shape[1], frame.shape[0]))


def source_label(spec):
    kind, _, arg = spec.partition(":")
    if kind == "usb":
        return f"USB camera {arg}"
    if kind == "pi":
        return f"Pi camera {arg}"
    if kind == "url":
        s = find_ip_source(arg)
        return s["name"] if s else "Network camera"
    if kind == "senxor":
        return "Waveshare Thermal-90 (SPI)"
    if kind == "sim":
        return "Simulator thermal camera" if arg == "thermal" else f"Simulator camera {arg}"
    if spec == "demo":
        return "Demo"
    return "Automatic"


