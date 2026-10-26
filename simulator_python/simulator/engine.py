"""The simulation loop: moves the world and the servos, renders camera + thermal pictures for the protocol server.
The servos follow what Motion Watch sends (POST /state) - only as far and as fast as real servos can."""
import math
import random
import threading
import time

import numpy as np

from simulator import bridge
from simulator.config import SIM
from simulator.graphics.render import Renderer, environment
from simulator.scene import world as worldmod
from simulator.scene.world import World


class SimServo:
    """A hobby servo: the pulse width sets a target angle, the horn moves there with limited speed."""
    def __init__(self, name):
        self.name = name
        self.angle = 0.0                # degrees, 0 = middle (1500 us)
        self.target = 0.0
        self.pulse = None               # us, None = no signal (limp, holds its place)
        self.attached = False
        self.travel = 0.0               # degrees moved in total
        self.reversals = 0              # direction changes (hunting / oscillation)
        self._dir = 0
        self.last_cmd = 0.0
        self.cmds = 0

    def command(self, pulse_us):
        self.pulse = pulse_us
        self.last_cmd = time.time(); self.cmds += 1
        if pulse_us is None:
            return
        self.attached = True
        half = SIM[f"{self.name}_travel"] / 2.0
        self.target = max(-half, min(half, (pulse_us - 1500.0) / 1000.0 * half))

    def stuck(self):
        return (not SIM["servo_power"]) or SIM[f"{self.name}_stuck"] or self.pulse is None

    def step(self, dt):
        if self.stuck():
            return
        d = self.target - self.angle
        mv = SIM["servo_speed"] * dt
        step = max(-mv, min(mv, d))
        if abs(step) > 1e-4:
            sgn = 1 if step > 0 else -1
            if self._dir and sgn != self._dir and abs(step) > 0.05:
                self.reversals += 1
            self._dir = sgn
        self.angle += step
        self.travel += abs(step)
        j = SIM["servo_jitter"]
        if j > 0:
            self.angle += random.gauss(0, j * 0.3)
            self.angle = 0.85 * self.angle + 0.15 * (self.angle - (self.angle - self.target) * 0.5)


class Engine:
    def __init__(self):
        self.world = World()
        self.renderer = Renderer()
        self.renderer.pano_pos = (float(SIM["cam_x"]), float(SIM["cam_y"]))
        self._building = False
        self.extra = None
        self.servos = {"pan": SimServo("pan"), "tilt": SimServo("tilt")}
        self.cond = threading.Condition()
        self.frame = None; self.frame_seq = 0; self.frame_t = 0.0
        self.tcond = threading.Condition()
        self.thermal = None; self.thermal_seq = 0
        self.thermal_fps = 15.0
        self.truth = []
        self.pose = (0.0, 0.0)
        self.env = None
        self.render_ms = 0.0
        self.sim_t = 0.0
        self.running = False
        self.scoreboard = None
        self.started = time.time()
        self.preview_until = 0.0
        self.proto = None; self.proto_t = 0.0          # last POST /state of Motion Watch
        self.map_loading = ""

    def wait_frame(self, last_seq, timeout=1.5):
        """Next camera frame after last_seq (blocks like a real camera). Returns (ok, frame, seq)."""
        if not SIM["cam_connected"]:
            time.sleep(0.1)
            return False, None, last_seq
        t_end = time.time() + timeout
        with self.cond:
            while self.frame_seq <= last_seq or self.frame is None:
                left = t_end - time.time()
                if left <= 0 or not SIM["cam_connected"]:
                    return False, None, last_seq
                self.cond.wait(left)
            return True, self.frame.copy(), self.frame_seq

    def render_extra(self, yaw):
        """A second, fixed camera (protocol camera 1)."""
        if self.env is None:
            return None
        if self.extra is None or self.extra.pano is not self.renderer.pano:
            r = self.renderer
            self.extra = Renderer()
            self.extra.use_map(r.map, r.pano, r.pano_height, r.pano_pos)
        try:
            px, py = self.renderer.pano_pos
            img, _ = self.extra.render(float(yaw), SIM["mount_pitch"], self.world.snapshot(), self.world.nearby_plants(px, py, 360.0),
                                       self._far_props(px, py), self.env)
            return img
        except Exception:
            return None

    # ---- maps and camera placement ----
    def set_map(self, name, done=None):
        """Switch to another map: camera goes to the map's camera place, panorama built in the background."""
        from simulator.scene import maps
        m = maps.get(name)
        p0 = maps.pois(m)[0]                             # the first place of the map = where the camera starts
        SIM.update(cam_x=p0["x"], cam_y=p0["y"], mount_height=p0["h"], mount_yaw=p0["yaw"], mount_pitch=p0["pitch"])
        if m.ambient is not None:
            SIM["ambient_c"] = m.ambient
        self._rebuild(m, switch_world=True, done=done)

    def _rebuild(self, m, switch_world=False, done=None):
        self._building = True
        self.map_loading = m.label

        def work():
            from simulator.graphics.render import build_panorama
            try:
                pos = (float(SIM["cam_x"]), float(SIM["cam_y"])); h = float(SIM["mount_height"])
                pano = build_panorama(h, m, pos)
                if switch_world:
                    self.world.set_map(m.name)
                    bridge.log(f"map: {m.label}")
                env = self.env or environment(self.sim_t)
                cube = self.renderer.build_cube(self._far_props(*pos), env, m=m, pano=pano, height=h, pos=pos,
                                                plants=self.world.nearby_plants(pos[0], pos[1], 360.0))
                self.renderer.use_map(m, pano, h, pos, cube=cube)
                self.extra = None
            except Exception as e:
                print("[SIM] building the picture failed:", e)
            finally:
                self._building = False
                self.map_loading = ""
            if done:
                done(m)
        threading.Thread(target=work, daemon=True, name="sim-pano").start()

    def goto_poi(self, p):
        """Put the camera head on a place of interest: position, height, facing, look-down angle."""
        SIM.update(cam_x=p["x"], cam_y=p["y"], mount_height=p["h"], mount_yaw=p["yaw"], mount_pitch=p.get("pitch", -4.0))
        self.world.clear()
        bridge.log(f"camera moved to: {p['name']}")

    def current_poi(self):
        from simulator.scene import maps
        for p in maps.pois(self.world.map):
            if math.hypot(p["x"] - SIM["cam_x"], p["y"] - SIM["cam_y"]) < 3 and abs(p["h"] - SIM["mount_height"]) < 0.5                     and abs((p["yaw"] - SIM["mount_yaw"] + 180) % 360 - 180) < 2:
                return p
        return None

    def _placement_check(self):
        """The camera was moved / raised in the editor: build the panorama for the new place."""
        r = self.renderer
        if r.pano is None or self._building:
            return
        from simulator.graphics import render as R
        R.set_quality(SIM["quality"])
        want = (float(SIM["cam_x"]), float(SIM["cam_y"]), float(SIM["mount_height"]))
        have = (r.pano_pos[0], r.pano_pos[1], r.pano_height)
        if any(abs(a - b) > 1e-3 for a, b in zip(want, have)) or r.pano.shape[1] != R.PW:
            self._rebuild(r.map)

    # ---- where the camera looks ----
    def protocol_state(self, st):
        """Servo / light positions sent by Motion Watch (POST /state)."""
        self.proto = st; self.proto_t = time.time()
        if st.sound:                                     # siren / loudspeaker: animals nearby run away (deterrent)
            n = self.world.scare()
            if n:
                bridge.log(f"sound «{st.sound}»: {n} animal(s) run away")
        for name, deg in (("pan", st.servo.pan_deg), ("tilt", st.servo.tilt_deg)):
            half = SIM[f"{name}_travel"] / 2.0
            self.servos[name].command(1500.0 + max(-1.0, min(1.0, float(deg) / half)) * 1000.0)

    def proto_live(self):
        return time.time() - self.proto_t < 3.0

    def servo_angles(self):
        """(pan degrees, tilt degrees, source): where the servos really are (they follow Motion Watch's POST /state)."""
        return self.servos["pan"].angle, self.servos["tilt"].angle, "protocol" if self.proto_live() else "none"

    def camera_pose(self):
        pa, ti, _src = self.servo_angles()
        yaw = (-pa if SIM["pan_reversed"] else pa) + SIM["mount_yaw"]
        pitch = (-ti if SIM["tilt_reversed"] else ti) + SIM["mount_pitch"]
        stop = float(SIM["tilt_stop"])
        pitch = max(-stop, min(stop, pitch))                  # the bracket hits the base: no further, whatever the servo wants
        sh = SIM["shake"]
        if sh > 0:
            yaw += random.gauss(0, sh * 0.8); pitch += random.gauss(0, sh * 0.5)
        return yaw, max(-89.0, min(89.0, pitch))

    def lights(self):
        if self.proto is not None and self.proto_live():
            return {"white": bool(self.proto.lights.white), "ir": bool(self.proto.lights.ir)}
        return {"white": False, "ir": False}

    # ---- the PIR sensor (sent as protocol event) ----
    def pir_near(self):
        """Somebody warm in front of the box within PIR range (the PIR does not turn with the head)."""
        vx, vy = worldmod.VIEW["x"], worldmod.VIEW["y"]
        face = math.radians(SIM["mount_yaw"])
        return any(e.kind not in ("car", "truck", "bird", "plane") and e.dist() < SIM["pir_range"]
                   and abs((math.atan2(e.x - vx, e.y - vy) - face + math.pi) % (2 * math.pi) - math.pi) < math.radians(55)
                   for e in self.world.snapshot())

    # ---- main loop ----
    def start(self):
        self.running = True
        threading.Thread(target=self.loop, daemon=True, name="sim-engine").start()

    def loop(self):
        last = time.time(); next_cam = 0.0; next_th = 0.0; next_sb = 0.0
        while self.running:
            now = time.time()
            dt = min(0.2, now - last); last = now
            sdt = 0.0 if SIM["paused"] else dt * float(SIM["time_scale"])
            self.sim_t += sdt
            try:
                self._placement_check()
                yaw, _p = self.pose
                worldmod.VIEW.update(yaw=yaw, half=max(SIM["cam_hfov"], SIM["thermal_hfov"]) / 2.0,
                                     x=self.renderer.pano_pos[0], y=self.renderer.pano_pos[1])
                self.world.step(sdt)
                for s in self.servos.values():
                    s.step(dt)
                self.env = environment(self.sim_t)
                self.env["lights"] = self.lights()
                fps = float(SIM["cam_fps"])
                if now >= next_cam:
                    next_cam = now + 1.0 / max(1.0, fps)
                    self._render_cam()
                if self._thermal_wanted() and now >= next_th:
                    next_th = now + 1.0 / max(1.0, min(25.0, self.thermal_fps))
                    self._render_thermal()
                if self.scoreboard is not None and now >= next_sb:
                    next_sb = now + 0.2
                    self.scoreboard.update(self, now)
            except Exception as e:                    # the simulator must never stop because of one bad frame
                import traceback
                traceback.print_exc()
                print("[SIM] engine error:", e)
                time.sleep(0.5)
            due = min(next_cam, next_sb, next_th if self._thermal_wanted() else next_cam)
            time.sleep(min(0.01, max(0.001, due - time.time())))

    def _render_cam(self):
        if SIM["cam_frozen"] and self.frame is not None:
            with self.cond:
                self.frame_seq += 1; self.frame_t = time.time(); self.cond.notify_all()
            return
        t0 = time.time()
        yaw, pitch = self.camera_pose()
        ents = self.world.snapshot()
        px, py = self.renderer.pano_pos
        img, truth = self.renderer.render(yaw, pitch, ents, self.world.nearby_plants(px, py, 360.0),
                                          self._far_props(px, py), self.env)
        self.render_ms = self.render_ms * 0.9 + (time.time() - t0) * 1000 * 0.1
        self.truth = truth; self.pose = (yaw, pitch)
        with self.cond:
            self.frame = img; self.frame_seq += 1; self.frame_t = time.time()
            self.cond.notify_all()

    def _render_thermal(self):
        yaw, pitch = self.pose
        px, py = self.renderer.pano_pos
        fr = self.renderer.render_thermal(yaw, pitch, self.world.snapshot(), self.world.nearby_plants(px, py, 260.0),
                                          self._far_props(px, py), self.env)
        with self.tcond:
            self.thermal = fr; self.thermal_seq += 1
            self.tcond.notify_all()

    def _far_props(self, x, y):
        """Props near the camera, the tall ones (towers) from much further away, mountains always."""
        near = self.world.nearby_props(x, y, 1200.0) + [pr for pr in self.world.landmarks() if math.hypot(pr.x - x, pr.y - y) > 1200.0]
        return [pr for pr in near if pr.h > 20 or math.hypot(pr.x - x, pr.y - y) < 700.0] + \
               [pr for pr in self.world.nearby_props(x, y, 3000.0) if pr.h > 40 and math.hypot(pr.x - x, pr.y - y) >= 1200.0]

    def scenery_changed(self):
        """Something static was placed / moved / deleted in the editor: redraw the static scene."""
        self.renderer.cube_dirty = True

    def _thermal_wanted(self):
        return time.time() < self.preview_until

    def thermal_preview(self):
        """The newest thermal picture; rendered only while somebody (Motion Watch, the panel) keeps asking for it."""
        self.preview_until = time.time() + 1.5
        return self.thermal
