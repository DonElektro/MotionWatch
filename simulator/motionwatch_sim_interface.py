#!/usr/bin/env python3
"""
Motion Watch – simulator interface  (protocol version 1)
=========================================================

One file for BOTH sides:
  * the separate simulation program (it derives from `SimServer` and draws the pictures),
  * Motion Watch (it uses `SimClient`: reads the pictures, sends the servo and light positions).

Transport: plain HTTP on one port (default 8765), only the Python standard library (+ numpy / OpenCV for pictures).

    Simulator  <──  POST /state        Motion Watch sends what it does: servos, lights, relays, sound, armed …
               ──>  (answer)           the simulator answers with its world: day / night, sensor events
               ──>  GET /info          what the simulator offers (cameras, thermal camera, sensors)
               ──>  GET /cam/<n>/video.mjpg     camera n as MJPEG stream  (Motion Watch: video source = this URL)
               ──>  GET /cam/<n>/snapshot.jpg   one picture of camera n
               ──>  GET /thermal.bin             thermal picture: float32 °C, row by row (header X-Width / X-Height)
               ──>  GET /thermal.json            the same as JSON (slower, for testing)
               ──>  GET /events?since=<id>       sensor events (PIR, door, …) since an event id

Coordinate rules (the same as in Motion Watch):
  * pan / tilt in PERCENT 0 … 100, 50 = middle. pan 100 = right, tilt 100 = up.
  * also sent in DEGREES from the middle: pan_deg = (pan - 50) / 50 * pan_limit  (pan_limit / tilt_limit in degrees).
  * camera 0 = the camera on the pan / tilt head, further cameras are fixed unless /info says otherwise.
  * the thermal camera sits on the pan / tilt head next to camera 0 (smaller field of view, see /info).

Run this file directly for a small DEMO simulator (a drawn camping scene that moves with the servos, lights,
a warm walking person in the thermal picture):

    python3 motionwatch_sim_interface.py --port 8765

Then in Motion Watch: Settings → Video source → add «http://<pc>:8765/cam/0/video.mjpg».
"""
import json
import math
import threading
import time
from dataclasses import dataclass, field, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional
from urllib import request as _rq

PROTOCOL = 1
DEFAULT_PORT = 8765
BOUNDARY = "mwsimframe"


# ----------------------------------------------------------------------------------------------------------------------
# Messages (JSON). Unknown fields must be ignored by both sides - new fields can be added without a new protocol version.
# ----------------------------------------------------------------------------------------------------------------------
@dataclass
class Servo:
    pan: float = 50.0                 # percent 0..100 (50 = middle, 100 = right)
    tilt: float = 50.0                # percent 0..100 (50 = middle, 100 = up)
    pan_deg: float = 0.0              # degrees from the middle (+ = right)
    tilt_deg: float = 0.0             # degrees from the middle (+ = up)
    pan_limit: float = 90.0           # max. degrees from the middle (setting of Motion Watch)
    tilt_limit: float = 60.0
    moving: bool = False              # the head is moving right now (patrol, tracking, joystick)


@dataclass
class Lights:
    white: bool = False               # white light / floodlight
    ir: bool = False                  # infrared light (only visible for a NoIR camera and in the grey night picture)
    white_level: float = 1.0          # 0..1 (for later: dimmed light); on/off uses 1.0
    ir_level: float = 1.0


@dataclass
class Relay:
    name: str = ""
    on: bool = False


@dataclass
class MWState:
    """POST /state  - Motion Watch -> simulator, about 10 x per second and at every change."""
    v: int = PROTOCOL
    t: float = 0.0                    # time of Motion Watch (epoch seconds)
    servo: Servo = field(default_factory=Servo)
    lights: Lights = field(default_factory=Lights)
    relays: List[Relay] = field(default_factory=list)
    sound: str = ""                   # "" or what plays now: "siren", "two-tone", "tts", "file:<name>" …
    armed: bool = False
    picture_mode: str = "color"       # color | night_grey | grey  (what Motion Watch makes of the picture)
    device: str = "Motion Watch"

    @staticmethod
    def from_dict(d: dict) -> "MWState":
        s = MWState()
        for k, v in (d or {}).items():
            if k == "servo" and isinstance(v, dict):
                s.servo = Servo(**{x: v[x] for x in v if x in Servo.__dataclass_fields__})
            elif k == "lights" and isinstance(v, dict):
                s.lights = Lights(**{x: v[x] for x in v if x in Lights.__dataclass_fields__})
            elif k == "relays" and isinstance(v, list):
                s.relays = [Relay(**{x: r[x] for x in r if x in Relay.__dataclass_fields__}) for r in v if isinstance(r, dict)]
            elif k in MWState.__dataclass_fields__ and k not in ("servo", "lights", "relays"):
                setattr(s, k, v)
        return s


@dataclass
class SimEvent:
    """A sensor event of the simulated world. kind: pir | door | gas | tag | other; active True / False / None (= pulse)."""
    id: int = 0
    t: float = 0.0
    sensor: str = ""                  # name, e.g. "Wohnwagen-Tür" - in Motion Watch the sensor source "sim:<name>"
    kind: str = "other"
    active: Optional[bool] = None


@dataclass
class SimReply:
    """Answer to POST /state - simulator -> Motion Watch."""
    v: int = PROTOCOL
    ok: bool = True
    sim_time: float = 0.0             # time in the simulated world (epoch seconds) - may run faster than real time
    dark: bool = False                # night in the simulation (Motion Watch can use it instead of sunrise / sunset)
    ambient_c: float = 15.0           # air temperature °C (for the thermal picture and the temperature sensor)
    pressure_hpa: float = 1013.0      # for the storm warning
    wind_kmh: float = 0.0
    last_event: int = 0               # id of the newest sensor event -> GET /events?since=…


@dataclass
class CamInfo:
    id: int = 0
    name: str = "Camera"
    w: int = 1280
    h: int = 720
    fps: float = 15.0
    fov_h: float = 62.0               # horizontal field of view in degrees (Pi camera module 3: about 66)
    fov_v: float = 37.0
    on_head: bool = True              # True = turns with the pan / tilt head
    noir: bool = False                # sees infrared light


@dataclass
class SimInfo:
    """GET /info"""
    v: int = PROTOCOL
    name: str = "Motion Watch simulator"
    cameras: List[CamInfo] = field(default_factory=lambda: [CamInfo(0, "Head camera"), CamInfo(1, "Fixed camera", on_head=False)])
    thermal: Optional[dict] = field(default_factory=lambda: {"w": 80, "h": 62, "fps": 8.0, "fov_h": 45.0, "fov_v": 35.0, "unit": "C", "on_head": True})
    sensors: List[dict] = field(default_factory=list)     # [{"name": "Wohnwagen-Tür", "kind": "door"}, …]


# ----------------------------------------------------------------------------------------------------------------------
# Simulator side: derive from SimServer and fill in render_camera() / render_thermal() (and add events with add_event()).
# ----------------------------------------------------------------------------------------------------------------------
class SimServer:
    def __init__(self, info: Optional[SimInfo] = None, host: str = "0.0.0.0", port: int = DEFAULT_PORT):
        self.info = info or SimInfo()
        self.host, self.port = host, port
        self.state = MWState()
        self.state_t = 0.0                # when Motion Watch last sent its state
        self.reply = SimReply()
        self.events: List[SimEvent] = []
        self.lock = threading.Lock()
        self._httpd = None

    # ---- to be written by the simulation ------------------------------------------------------------------------
    def render_camera(self, cam: int, state: MWState, t: float):
        """Return the picture of camera `cam` as numpy array H x W x 3, uint8, BGR (OpenCV order)."""
        raise NotImplementedError

    def render_thermal(self, state: MWState, t: float):
        """Return the thermal picture as numpy array h x w, float32, degrees Celsius (or None = no thermal camera)."""
        return None

    def on_state(self, state: MWState):
        """Called for every POST /state (e.g. to log or to move a 3D model). The default does nothing."""

    def world(self, t: float) -> SimReply:
        """The answer to POST /state. The default: time = real time, day / night from the clock."""
        h = time.localtime(t).tm_hour
        return SimReply(sim_time=t, dark=not (7 <= h < 19), last_event=self.events[-1].id if self.events else 0)

    # ---- helpers -------------------------------------------------------------------------------------------------
    def add_event(self, sensor: str, kind: str = "other", active: Optional[bool] = None):
        with self.lock:
            ev = SimEvent(id=(self.events[-1].id + 1) if self.events else 1, t=time.time(), sensor=sensor, kind=kind, active=active)
            self.events.append(ev); del self.events[:-500]
        return ev

    def serve_forever(self):
        srv = self

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def _send(self, code, body: bytes, ctype="application/json", extra=None):
                self.send_response(code)
                self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                for k, v in (extra or {}).items():
                    self.send_header(k, str(v))
                self.end_headers(); self.wfile.write(body)

            def _json(self, obj, code=200):
                self._send(code, json.dumps(obj).encode())

            def do_POST(self):
                if self.path.split("?")[0] != "/state":
                    return self._json({"ok": False, "error": "unknown path"}, 404)
                n = int(self.headers.get("Content-Length") or 0)
                try:
                    st = MWState.from_dict(json.loads(self.rfile.read(n) or b"{}"))
                except (ValueError, TypeError) as e:
                    return self._json({"ok": False, "error": f"bad state: {e}"}, 400)
                with srv.lock:
                    srv.state, srv.state_t = st, time.time()
                srv.on_state(st)
                self._json(asdict(srv.world(time.time())))

            def do_GET(self):
                path, _, q = self.path.partition("?")
                args = dict(x.split("=", 1) for x in q.split("&") if "=" in x)
                if path == "/info":
                    return self._json(asdict(srv.info))
                if path == "/events":
                    since = int(args.get("since", 0) or 0)
                    with srv.lock:
                        evs = [asdict(e) for e in srv.events if e.id > since]
                    return self._json({"v": PROTOCOL, "events": evs})
                if path in ("/thermal.bin", "/thermal.json"):
                    a = srv.render_thermal(srv.state, time.time())
                    if a is None:
                        return self._json({"ok": False, "error": "no thermal camera"}, 404)
                    import numpy as np
                    a = np.ascontiguousarray(a, dtype="<f4")
                    if path.endswith(".json"):
                        return self._json({"v": PROTOCOL, "w": a.shape[1], "h": a.shape[0], "unit": "C", "data": [round(float(x), 2) for x in a.ravel()]})
                    return self._send(200, a.tobytes(), "application/octet-stream", {"X-Width": a.shape[1], "X-Height": a.shape[0], "X-Unit": "C"})
                parts = path.strip("/").split("/")
                if len(parts) == 3 and parts[0] == "cam" and parts[1].isdigit():
                    cam = int(parts[1])
                    if cam >= len(srv.info.cameras):
                        return self._json({"ok": False, "error": "no such camera"}, 404)
                    if parts[2] == "snapshot.jpg":
                        return self._send(200, srv._jpg(cam), "image/jpeg")
                    if parts[2] == "video.mjpg":
                        return srv._mjpeg(self, cam)
                return self._json({"ok": False, "error": "unknown path"}, 404)

        self._httpd = ThreadingHTTPServer((self.host, self.port), H)
        self._httpd.daemon_threads = True
        print(f"Motion Watch simulator (protocol {PROTOCOL}) on http://{self.host}:{self.port}/  -  cameras: "
              + ", ".join(f"/cam/{c.id}/video.mjpg" for c in self.info.cameras))
        self._httpd.serve_forever()

    def _jpg(self, cam):
        import cv2
        with self.lock:
            st = self.state
        img = self.render_camera(cam, st, time.time())
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes() if ok else b""

    def _mjpeg(self, h, cam):
        h.send_response(200)
        h.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
        h.send_header("Cache-Control", "no-store"); h.send_header("Connection", "close"); h.end_headers()
        gap = 1.0 / max(1.0, float(self.info.cameras[cam].fps))
        try:
            while True:
                t0 = time.time(); jpg = self._jpg(cam)
                h.wfile.write(f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpg)}\r\n\r\n".encode() + jpg + b"\r\n")
                h.wfile.flush()
                time.sleep(max(0.0, gap - (time.time() - t0)))
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


# ----------------------------------------------------------------------------------------------------------------------
# Motion Watch side: the client. Sends the state, reads the reply, the thermal picture and the events.
# ----------------------------------------------------------------------------------------------------------------------
class SimClient:
    def __init__(self, base_url: str, timeout: float = 2.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.last_event = 0

    def _get(self, path):
        with _rq.urlopen(self.base + path, timeout=self.timeout) as r:
            return r.read(), r.headers

    def info(self) -> dict:
        return json.loads(self._get("/info")[0])

    def send_state(self, state: MWState) -> dict:
        body = json.dumps(asdict(state)).encode()
        req = _rq.Request(self.base + "/state", data=body, headers={"Content-Type": "application/json"})
        with _rq.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    def camera_url(self, cam: int = 0) -> str:
        """The URL to enter as video source in Motion Watch (it reads MJPEG streams like a network camera)."""
        return f"{self.base}/cam/{cam}/video.mjpg"

    def thermal(self):
        """Thermal picture as numpy float32 array (°C) or None."""
        import numpy as np
        try:
            data, hd = self._get("/thermal.bin")
        except Exception:
            return None
        return np.frombuffer(data, dtype="<f4").reshape(int(hd["X-Height"]), int(hd["X-Width"]))

    def events(self) -> List[dict]:
        evs = json.loads(self._get(f"/events?since={self.last_event}")[0]).get("events", [])
        if evs:
            self.last_event = max(e["id"] for e in evs)
        return evs

    @staticmethod
    def state_from(pan, tilt, pan_limit=90.0, tilt_limit=60.0, white=False, ir=False, relays=None, sound="", armed=False,
                   picture_mode="color", moving=False, device="Motion Watch") -> MWState:
        """Build the state from the values Motion Watch has (pan / tilt in percent)."""
        return MWState(t=time.time(), servo=Servo(pan, tilt, (pan - 50) / 50 * pan_limit, (tilt - 50) / 50 * tilt_limit, pan_limit, tilt_limit, moving),
                       lights=Lights(bool(white), bool(ir)), relays=[Relay(n, bool(o)) for n, o in (relays or [])],
                       sound=sound, armed=armed, picture_mode=picture_mode, device=device)


# ----------------------------------------------------------------------------------------------------------------------
# DEMO simulator: a wide drawn panorama; camera 0 looks at a part of it depending on pan / tilt, camera 1 is fixed.
#   Night after 19:00 (or --night): dark, the white light lights up a cone, IR makes the picture grey-bright (NoIR).
#   A person walks across now and then (warm in the thermal picture). Every 45 s the door sensor opens.
# ----------------------------------------------------------------------------------------------------------------------
class DemoSim(SimServer):
    PANO_W, PANO_H = 4000, 1500                # the world: 1 pixel ~ 0.06 degrees

    def __init__(self, port=DEFAULT_PORT, night=None):
        super().__init__(SimInfo(sensors=[{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"}]), port=port)
        self.night = night
        self._pano = None
        threading.Thread(target=self._doors, daemon=True).start()

    def world(self, t):
        r = super().world(t)
        if self.night is not None:
            r.dark = self.night
        return r

    def _doors(self):
        while True:
            time.sleep(45); self.add_event("Wohnwagen-Tür", "door", True)
            time.sleep(5); self.add_event("Wohnwagen-Tür", "door", False)

    def _panorama(self):
        import numpy as np, cv2
        if self._pano is None:
            W, H = self.PANO_W, self.PANO_H
            p = np.zeros((H, W, 3), np.uint8)
            p[: H // 2] = (235, 200, 140)                                   # sky
            p[H // 2:] = (60, 140, 70)                                      # meadow
            rng = np.random.default_rng(1)
            for x in range(0, W, 260):                                      # mountains, trees, tents
                h = int(rng.integers(150, 420))
                cv2.fillPoly(p, [np.array([[x - 300, H // 2], [x, H // 2 - h], [x + 300, H // 2]])], (120, 115, 105))
            for x in rng.integers(0, W, 30):
                cv2.rectangle(p, (int(x) - 6, H // 2 + 40), (int(x) + 6, H // 2 + 110), (40, 60, 90), -1)
                cv2.circle(p, (int(x), H // 2 + 20), 45, (40, 100, 40), -1)
            for x in (900, 2100, 3300):
                cv2.fillPoly(p, [np.array([[x - 160, 1150], [x, 900], [x + 160, 1150]])], (60, 140, 235))
            self._pano = p
        return self._pano

    def _person_x(self, t):
        return (t * 120) % (self.PANO_W + 400) - 200                    # walks across the world every ~35 s

    def render_camera(self, cam, st, t):
        import numpy as np, cv2
        info = self.info.cameras[cam]; W, H = info.w, info.h
        pano = self._panorama()
        ppd = self.PANO_W / 240.0                                           # pixels per degree (the world is 240° wide)
        if info.on_head:
            cx = self.PANO_W / 2 + st.servo.pan_deg * ppd; cy = self.PANO_H / 2 - st.servo.tilt_deg * ppd
        else:
            cx, cy = self.PANO_W / 2, self.PANO_H / 2
        vw, vh = info.fov_h * ppd, info.fov_v * ppd
        x0, y0 = int(max(0, min(self.PANO_W - vw, cx - vw / 2))), int(max(0, min(self.PANO_H - vh, cy - vh / 2)))
        world = pano.copy()
        px = int(self._person_x(t))
        if -100 < px < self.PANO_W + 100:                                   # the walking person
            cv2.rectangle(world, (px - 25, 1000), (px + 25, 1200), (50, 50, 160), -1); cv2.circle(world, (px, 970), 28, (140, 170, 220), -1)
        img = cv2.resize(world[y0:y0 + int(vh), x0:x0 + int(vw)], (W, H), interpolation=cv2.INTER_AREA)
        dark = self.world(t).dark
        if dark:
            light = np.full((H, W), 0.08, np.float32)                      # night: almost black
            if st.lights.white and info.on_head:                            # floodlight cone in the middle of the head camera
                yy, xx = np.mgrid[0:H, 0:W]
                light += 0.9 * np.exp(-(((xx - W / 2) / (W * 0.35)) ** 2 + ((yy - H * 0.6) / (H * 0.45)) ** 2)) * st.lights.white_level
            if st.lights.ir:                                                # the demo cameras see infrared (NoIR)
                light += 0.55 * st.lights.ir_level
            img = np.clip(img.astype(np.float32) * np.minimum(light, 1.2)[..., None], 0, 255).astype(np.uint8)
            if st.lights.ir and not st.lights.white:
                g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
        noise = np.random.default_rng().normal(0, 6 if dark else 2, img.shape)
        img = np.clip(img + noise, 0, 255).astype(np.uint8)
        cv2.putText(img, f"SIM cam {cam}  pan {st.servo.pan:.0f}% tilt {st.servo.tilt:.0f}%  "
                         f"{'night' if dark else 'day'}{'  LIGHT' if st.lights.white else ''}{'  IR' if st.lights.ir else ''}",
                    (10, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        return img

    def render_thermal(self, st, t):
        import numpy as np, cv2
        th = self.info.thermal; w, h = th["w"], th["h"]
        amb = self.world(t).ambient_c
        a = np.full((h, w), amb, np.float32) + np.random.default_rng().normal(0, 0.15, (h, w)).astype(np.float32)
        ppd = self.PANO_W / 240.0
        cx = self.PANO_W / 2 + st.servo.pan_deg * ppd
        vw = th["fov_h"] * ppd
        px = self._person_x(t)
        rel = (px - (cx - vw / 2)) / vw                                     # where the person is in the thermal picture
        if 0 <= rel <= 1:
            x = int(rel * w); cv2.ellipse(a, (x, int(h * 0.62)), (3, 9), 0, 0, 360, 33.5, -1); cv2.circle(a, (x, int(h * 0.42)), 3, 34.5, -1)
        if st.lights.white:                                                 # the floodlight gets warm
            cv2.circle(a, (w // 2, 4), 2, amb + 25, -1)
        return a


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Motion Watch demo simulator")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--night", action="store_true", help="always night (to try the lights)")
    ap.add_argument("--day", action="store_true", help="always day")
    a = ap.parse_args()
    DemoSim(a.port, True if a.night else (False if a.day else None)).serve_forever()
