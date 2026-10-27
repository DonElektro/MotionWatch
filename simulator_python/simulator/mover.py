"""The Mover: a tracked vehicle that carries the whole camera head (head camera, thermal camera, lamps).

Motion Watch drives it with its second joystick: every POST /state has "drive": {"l": -1..1, "r": -1..1}.
It moves like in the 3D simulator (simulator/Simulator_Schnittstelle.md in Motion Watch's project, section «Mover»):
    v = (l + r) / 2 * max_speed            forward speed in m/s (default 0.8)
    w = (l - r) / 0.74 m * max_speed       turning in rad/s, left track faster = turns right
It stops when no POST /state came for 2.5 s, does not drive into houses, tents, trees, bushes, water or off the map
(then "blocked"), and drives back to where it started when it is switched off.
Moving changes SIM cam_x / cam_y / mount_yaw: the head camera, the thermal camera and the lamps ride along; panning is
relative to the vehicle. The fixed camera 1 stays at the starting place."""
import math
import time

from simulator import bridge
from simulator.config import SIM
from simulator.scene import maps

TRACK = 0.74            # metres between the two tracks
CLEAR = 0.55            # metres the middle of the vehicle keeps away from obstacles (like the 3D simulator)
STALE = 2.5             # seconds without POST /state: stop
EDGE = 3.0              # metres kept away from the edge of the map


def _is_water(col):
    """Ground layers are drawn in BGR: clearly blue = water (lake, river, pond)."""
    return col[0] > col[1] + 10 and col[0] > col[2] + 30


class Mover:
    def __init__(self):
        self.on = False
        self.max = 0.8                  # m/s
        self.l = self.r = 0.0
        self.drive_t = 0.0
        self.home = None                # (x, y, yaw) where it was switched on
        self.home_view = None           # the renderer of the starting place (for the fixed camera 1)
        self.x = self.y = 0.0           # metres from the start: x = right, y = forward (start direction)
        self.yaw = 0.0                  # degrees from the start direction, + = turned right
        self.odo = 0.0
        self.blocked = False
        self.moving = False
        self._t = None                  # time of the last step (the Mover keeps its own clock)

    # ---- switching ----
    def set_on(self, on, eng=None):
        on = bool(on)
        if on == self.on:
            return
        if on:
            self.home = (float(SIM["cam_x"]), float(SIM["cam_y"]), float(SIM["mount_yaw"]))
            r = eng.renderer if eng is not None else None
            self.home_view = (r.map, r.pano, r.pano_height, r.pano_pos) if r is not None and r.pano is not None else None
            self.x = self.y = self.yaw = self.odo = 0.0
            self.l = self.r = 0.0
            self.blocked = False
            self.on = True
            bridge.log("Mover on")
        else:
            self.on = False
            self.l = self.r = 0.0
            self.moving = False
            if self.home is not None:                    # back to the starting place
                SIM.update(cam_x=self.home[0], cam_y=self.home[1], mount_yaw=self.home[2])
            self.home = None; self.home_view = None
            bridge.log(f"Mover off - back at the start ({self.odo:.1f} m driven)")

    def forget(self):
        """The map or the camera place changed: the Mover is switched off where it is (no driving back)."""
        if self.on:
            self.home = None
            self.set_on(False)

    def drive(self, l, r):
        try:
            self.l = max(-1.0, min(1.0, float(l))); self.r = max(-1.0, min(1.0, float(r)))
        except (TypeError, ValueError):
            self.l = self.r = 0.0
        self.drive_t = time.time()

    # ---- moving ----
    def step(self, world, paused=False, dt=None):
        """Move on by the time since the last step (dt only for tests): the engine loop can be slow while the
        picture is rebuilt, the Mover must still drive at the right speed."""
        now = time.time()
        if dt is None:
            dt = 0.0 if self._t is None else min(STALE, now - self._t)
        self._t = now
        if paused:
            dt = 0.0
        if not self.on or self.home is None:
            return
        if time.time() - self.drive_t > STALE:
            self.l = self.r = 0.0
        v = (self.l + self.r) / 2.0 * self.max
        w = (self.l - self.r) / TRACK * self.max                        # rad/s, + = right
        self.moving = abs(v) > 1e-3 or abs(w) > 1e-3
        if not self.moving:
            return
        hx, hy, hyaw = self.home
        yaw = self.yaw + math.degrees(w * dt)
        h = math.radians(hyaw + yaw)                                    # heading in the world, 0 = +y, + = towards +x
        cx, cy = float(SIM["cam_x"]), float(SIM["cam_y"])
        nx, ny = cx + math.sin(h) * v * dt, cy + math.cos(h) * v * dt
        self.yaw = (yaw + 180.0) % 360.0 - 180.0
        SIM["mount_yaw"] = (hyaw + self.yaw) % 360.0
        if abs(v) < 1e-3:
            return
        if self.free(world, nx, ny) or not self.free(world, cx, cy):    # stuck inside something: let it drive out
            SIM.update(cam_x=nx, cam_y=ny)
            self.odo += abs(v) * dt
            self.blocked = False
        else:
            if not self.blocked:
                bridge.log("Mover blocked by an obstacle")
            self.blocked = True
        dx, dy = float(SIM["cam_x"]) - hx, float(SIM["cam_y"]) - hy
        a = math.radians(hyaw)
        self.x = dx * math.cos(a) - dy * math.sin(a)
        self.y = dx * math.sin(a) + dy * math.cos(a)

    def free(self, world, x, y):
        """Can the middle of the vehicle stand at x, y?"""
        m = world.map
        x0, x1, y0, y1 = m.extent
        if not (x0 + EDGE < x < x1 - EDGE and y0 + EDGE < y < y1 - EDGE):
            return False
        for pr in world.nearby_props(x, y, 40.0):
            if pr.name == "mountain" or pr.h < 0.3:
                continue
            if abs(x - pr.x) < pr.w / 2.0 + CLEAR and abs(y - pr.y) < pr.d / 2.0 + CLEAR:
                return False
        for p in world.nearby_plants(x, y, 8.0):
            r = 0.25 if p.kind == "tree" else p.crown * 0.6
            if math.hypot(x - p.x, y - p.y) < r + CLEAR:
                return False
        return not self._water(m, x, y)

    @staticmethod
    def _water(m, x, y):
        import numpy as np
        gx, gy = np.array([x]), np.array([y])
        wet = False
        for L in m.layers:                                              # the last layer that covers the point counts
            try:
                if bool(maps.layer_mask(L[0], L[1], gx, gy)[0]):
                    wet = _is_water(L[2])
            except Exception:
                continue
        return wet

    def pose(self):
        return {"x": round(self.x, 2), "y": round(self.y, 2), "yaw": round(self.yaw, 1), "odo": round(self.odo, 2),
                "blocked": bool(self.blocked)}
