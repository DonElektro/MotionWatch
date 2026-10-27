"""Motion Watch simulator interface, protocol 1 (motionwatch_sim_interface.py), served by THIS simulator.

  GET  /info                    what the simulator offers
  GET  /cam/0/video.mjpg?fps=6  the camera on the pan / tilt head (?fps = fewer pictures per second)
  GET  /cam/1/video.mjpg        a fixed camera (looks along the mount direction + fixed_cam_yaw)
  GET  /thermal.bin             the Thermal-90 picture in degrees C
  GET  /events                  sensor events: PIR (when somebody is near), door / gas buttons
  POST /state                   servo + light positions from Motion Watch (it runs as its own program, on the Pi or a PC)
  GET  /control, POST /control  remote control from Motion Watch's web page (control.py)
  UDP  port 8764, every 2 s     "here is a simulator" - only while «Send to Motion Watch» is on

See EIGENEN_SIMULATOR_ANBINDEN.md next to this file."""
import io
import json
import os
import socket
import threading
import time
from dataclasses import dataclass
from http.server import ThreadingHTTPServer

from simulator import NAME, VERSION, bridge
from simulator.config import SIM
from simulator.hardware import control
from simulator.scene import sound
from simulator.scene.world import ambient_light

from simulator.hardware import motionwatch_sim_interface as msi
from simulator.hardware.motionwatch_sim_interface import CamInfo, SimInfo, SimReply, SimServer

DISCOVERY_PORT = 8764
_peer = threading.local()
_SERVER = {"s": None}                  # the ProtocolServer, for the request additions below


def _lang(handler, d=None):
    """The language Motion Watch shows: "lang" in POST /control, else the Accept-Language header."""
    v = (d or {}).get("lang") or handler.headers.get("Accept-Language") or ""
    return str(v).split(",")[0].split(";")[0].split("-")[0].strip().lower()


def _extend(base):
    """The protocol file's request handler plus what Motion Watch 2.93+ asks for: /control, ?fps= on the video, and the
    fields of POST /state that the protocol file drops (mw_scheme, mw_port, det)."""
    class Handler(base):
        def do_GET(self):
            srv = _SERVER["s"]
            path, _, q = self.path.partition("?")
            args = dict(x.split("=", 1) for x in q.split("&") if "=" in x)
            if srv is not None and path == "/control":
                return self._json(control.describe(srv, _lang(self)))
            parts = path.strip("/").split("/")
            if (srv is not None and "fps" in args and len(parts) == 3 and parts[0] == "cam" and parts[1].isdigit()
                    and parts[2] == "video.mjpg" and int(parts[1]) < len(srv.info.cameras)):
                try:
                    fps = float(args["fps"])
                except ValueError:
                    fps = None
                return srv._mjpeg(self, int(parts[1]), fps)
            return super().do_GET()

        def do_POST(self):
            srv = _SERVER["s"]
            path = self.path.split("?")[0]
            if srv is not None and path == "/control":
                n = int(self.headers.get("Content-Length") or 0)
                try:
                    d = json.loads(self.rfile.read(n) or b"{}")
                except ValueError:
                    return self._json({"ok": False, "error": "kein gültiges JSON"})
                d = d if isinstance(d, dict) else {}
                return self._json(control.handle(srv, d, _lang(self, d)))
            if path == "/state":
                # MWState.from_dict drops fields it does not know: read the raw JSON first, then hand the same bytes on
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                try:
                    raw = json.loads(body or b"{}")
                except ValueError:
                    raw = None
                _peer.raw = raw if isinstance(raw, dict) else {}
                self.rfile = io.BytesIO(body)
            return super().do_POST()
    return Handler


class _Http(ThreadingHTTPServer):
    """Remembers who sent the request (POST /state tells us where Motion Watch is) and adds the handler extensions -
    the protocol file itself stays as it is."""
    def __init__(self, addr, handler, bind_and_activate=True):
        super().__init__(addr, _extend(handler), bind_and_activate)

    def process_request_thread(self, request, client_address):
        _peer.ip = client_address[0]; _peer.raw = {}
        super().process_request_thread(request, client_address)


msi.ThreadingHTTPServer = _Http


@dataclass
class Info(SimInfo):
    """GET /info plus the computer's name (Motion Watch 2.95.1+ shows it next to each simulator)."""
    host: str = ""


@dataclass
class Reply(SimReply):
    """Answer to POST /state with the fields Motion Watch 2.93+ reads as well."""
    humidity: float = 60.0
    weather: str = "clear"
    pid: int = 0                       # this process: Motion Watch shows the simulator's CPU share if it runs on the same computer
    sound_db: float = 30.0             # how loud the world is at the camera (noise alarm, clap switch test)


def lan_ip():
    """This PC's address in the local network (what Motion Watch on the Pi has to use)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as so:
            so.connect(("10.255.255.255", 1))          # no packet is sent - it only picks the network card
            return so.getsockname()[0]
    except OSError:
        return "127.0.0.1"


try:
    HOST = socket.gethostname()[:40]   # this computer's name, as Motion Watch shows it in «Simulators in the network»
except OSError:
    HOST = ""

SENSORS = [{"name": "PIR", "kind": "pir"}, {"name": "Door", "kind": "door"}, {"name": "Gas", "kind": "gas"}]


class ProtocolServer(SimServer):
    def __init__(self, eng, port, host="0.0.0.0", name=NAME):
        self.name = name
        super().__init__(self._make_info(), host=host, port=port)
        self.eng = eng
        self.clients = 0
        self.posts = 0
        self.running = False
        self.error = ""
        self.announced = 0                 # UDP announcements sent
        self.announce_error = ""
        self.sound_db = 0.0                # the last level sent to Motion Watch (shown in the window)
        self._pir = False
        threading.Thread(target=self._sensor_loop, daemon=True, name="sim-events").start()
        threading.Thread(target=self._announce_loop, daemon=True, name="sim-announce").start()

    def _make_info(self):
        w, h, hf = int(SIM["cam_width"]), int(SIM["cam_height"]), float(SIM["cam_hfov"])
        import math
        vf = math.degrees(2 * math.atan(math.tan(math.radians(hf) / 2) * h / w))
        th = float(SIM["thermal_hfov"])
        tv = math.degrees(2 * math.atan(math.tan(math.radians(th) / 2) * 62 / 80))
        return Info(name=self.name, host=HOST,
                       cameras=[CamInfo(0, "Head camera", w, h, float(SIM["cam_fps"]), hf, round(vf, 1), True, True),
                                CamInfo(1, "Fixed camera", 960, 540, 6.0, 70.0, 42.0, False, False)],
                       thermal={"w": 80, "h": 62, "fps": 15.0, "fov_h": th, "fov_v": round(tv, 1), "unit": "C", "on_head": True},
                       sensors=list(SENSORS))

    # ---- what the protocol asks for ----
    def render_camera(self, cam, state, t):
        self.info = self._make_info()
        if cam == 0:
            ok, fr, _seq = self.eng.wait_frame(-1, timeout=1.0)
            if ok:
                return fr
            import numpy as np
            return np.zeros((int(SIM["cam_height"]), int(SIM["cam_width"]), 3), np.uint8)    # camera unplugged: black
        fr = self.eng.render_extra(SIM["mount_yaw"] + float(SIM.get("fixed_cam_yaw", 35.0)))
        if fr is None:
            import numpy as np
            return np.zeros((540, 960, 3), np.uint8)
        import cv2
        return cv2.resize(fr, (960, 540)) if fr.shape[1] != 960 else fr

    def _mjpeg(self, h, cam, fps=None):
        """The video stream; Motion Watch may ask for fewer pictures per second (?fps=6) - that saves computing power."""
        h.send_response(200)
        h.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={msi.BOUNDARY}")
        h.send_header("Cache-Control", "no-store"); h.send_header("Connection", "close"); h.end_headers()
        full = max(1.0, float(self.info.cameras[cam].fps))
        gap = 1.0 / max(0.2, min(full, float(fps))) if fps else 1.0 / full
        try:
            while True:
                t0 = time.time(); jpg = self._jpg(cam)
                h.wfile.write(f"--{msi.BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpg)}\r\n\r\n".encode() + jpg + b"\r\n")
                h.wfile.flush()
                time.sleep(max(0.0, gap - (time.time() - t0)))
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def render_thermal(self, state, t):
        if not SIM["thermal_present"]:
            return None
        fr = self.eng.thermal_preview()           # keeps the engine rendering thermal pictures while somebody reads them
        t_end = time.time() + 2.0
        while fr is None and time.time() < t_end:  # first request: the first picture is still being made
            time.sleep(0.05)
            fr = self.eng.thermal
        return fr

    def on_state(self, state):
        self.posts += 1
        bridge.note_client(getattr(_peer, "ip", ""), getattr(_peer, "raw", None))
        self.eng.protocol_state(state)

    def world(self, t):
        humid = min(100.0, 55.0 + 40.0 * max(float(SIM["rain"]), float(SIM["fog"])) + 10.0 * float(SIM["clouds"]))
        try:
            db = sound.level_db(self.eng.world, time.time())
        except Exception:
            db = 30.0
        self.sound_db = db
        return Reply(sim_time=t, dark=ambient_light() < 0.15, ambient_c=float(SIM["ambient_c"]),
                     pressure_hpa=1013.0 - 25.0 * float(SIM["wind"]) ** 2, wind_kmh=round(float(SIM["wind"]) * 90.0, 1),
                     last_event=self.events[-1].id if self.events else 0, humidity=round(humid), weather=control.weather(),
                     pid=os.getpid(), sound_db=db)

    # ---- sensor events ----
    def _sensor_loop(self):
        while True:
            time.sleep(0.3)
            try:
                near = self.eng.pir_near()
                if near != self._pir:
                    self._pir = near
                    self.add_event("PIR", "pir", near)
            except Exception:
                pass

    # ---- found in the network: "here is a simulator" every 2 s, but only while the user wants it ----
    def _announce_loop(self):
        so = None
        while True:
            time.sleep(2.0)
            if not (SIM["stream"] and self.running):
                continue
            msg = json.dumps({"mwsim": 1, "name": self.name, "port": self.port, "version": VERSION, "host": HOST}).encode()
            try:
                if so is None:
                    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    so.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                errors = []
                for addr in ("255.255.255.255", "127.0.0.1"):
                    try:
                        so.sendto(msg, (addr, DISCOVERY_PORT))
                    except OSError as e:
                        errors.append(f"{addr}: {e}")
                self.announced += 1
                self.announce_error = "; ".join(errors)
            except OSError as e:
                self.announce_error = str(e)
                so = None

    def start(self):
        _SERVER["s"] = self

        def run():
            try:
                self.running = True
                self.serve_forever()
            except OSError as e:
                self.error = f"port {self.port}: {e}"
                print(f"[SIM] protocol server could not start on port {self.port}: {e}")
            finally:
                self.running = False
        threading.Thread(target=run, daemon=True, name="sim-protocol").start()
        return self
