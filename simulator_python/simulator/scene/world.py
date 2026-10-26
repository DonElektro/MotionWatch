"""The simulated world: a camp site seen from the camera head. People, animals and vehicles move on the ground.

Coordinates in metres: x = right (east), y = forward (north, where the camera looks with the pan servo centred),
z = up. The camera head stands at (0, 0, mount_height). Headings are radians, 0 = +y, positive = turning right."""
import itertools
import math
import random
import threading
import time
from datetime import datetime

from simulator.scene import maps
from simulator.config import SIM

ROAD_Y = 32.0                 # nearest road (kept for old callers) - set by the map
ROADS = [("h", 32.0)]         # roads with traffic: ("h", y) runs left-right, ("v", x) runs front-back
OUTER_R = 42.0                # entities appear / disappear on this circle
AREA = (-14.0, 14.0, 4.0, 22.0)   # where walkers pass through (x0, x1, y0, y1) - set by the map

# COCO class ids of the SSD MobileNet label map the program uses
COCO = {"person": 1, "bicycle": 2, "car": 3, "motorcycle": 4, "airplane": 5, "plane": 5, "truck": 8, "bird": 16, "cat": 17, "dog": 18,
        "horse": 19, "sheep": 20, "cow": 21, "bear": 23}

KINDS = ("person", "dog", "cat", "bear", "horse", "sheep", "bird", "car", "truck", "bicycle", "motorcycle", "plane")
KIND_LABEL = {"person": "People", "dog": "Dogs", "cat": "Cats", "bear": "Bears", "horse": "Deer / horses",
              "sheep": "Sheep", "bird": "Birds", "car": "Cars", "truck": "Trucks", "bicycle": "Cyclists",
              "motorcycle": "Motorcycles", "plane": "Planes (sky)"}
PERSON_BEHAVIORS = ("mixed", "walk", "wander", "stand", "loiter", "run", "approach", "sneak")
VEHICLES = ("car", "truck", "motorcycle")
ANIMALS = ("dog", "cat", "bear", "horse", "sheep", "bird")

SHIRTS = [(40, 40, 170), (160, 70, 40), (50, 140, 60), (30, 30, 30), (200, 200, 200), (30, 160, 220), (120, 50, 120),
          (90, 90, 90), (20, 90, 200), (180, 140, 60)]
PANTS = [(60, 50, 40), (110, 70, 40), (40, 40, 40), (90, 100, 110), (40, 60, 90)]
SKIN = [(150, 180, 220), (110, 150, 200), (80, 110, 160), (60, 80, 120)]
CAR_COLS = [(40, 40, 200), (200, 200, 200), (30, 30, 30), (150, 90, 30), (60, 140, 60), (180, 180, 60), (120, 120, 130)]

_ids = itertools.count(1)


def _rand_point_in_area(rng=random):
    """A point where something passes by, 4 .. 14 m from the camera: mostly inside what the camera sees right now
    (so people walk through the picture), sometimes elsewhere in what the pan servo can reach."""
    if rng.random() < 0.75:
        half = SIM["cam_hfov"] / 2.0 * 0.8
        a = math.radians(VIEW["yaw"] + rng.uniform(-half, half))
    else:
        half = min(75.0, SIM["pan_travel"] / 2.0 + 15.0)
        a = math.radians(SIM["mount_yaw"] + rng.uniform(-half, half))
    r = rng.uniform(4.0, 14.0)
    return VIEW["x"] + math.sin(a) * r, VIEW["y"] + math.cos(a) * r


def _circle_exit(x, y, hd):
    """Where a straight line from (x, y) in direction hd leaves the outer circle around the camera."""
    cx, cy = VIEW["x"], VIEW["y"]
    x, y = x - cx, y - cy
    dx, dy = math.sin(hd), math.cos(hd)
    b = x * dx + y * dy
    c = x * x + y * y - OUTER_R * OUTER_R
    t = -b + math.sqrt(max(0.0, b * b - c))
    return cx + x + dx * t, cy + y + dy * t


def _line_through(px, py, hd):
    """Start and end on the outer circle of a straight line through (px, py) in direction hd."""
    sx, sy = _circle_exit(px, py, hd + math.pi)
    ex, ey = _circle_exit(px, py, hd)
    return (sx, sy), (ex, ey)


class Entity:
    def __init__(self, kind, x, y, **kw):
        self.id = next(_ids)
        self.kind = kind
        self.x, self.y, self.z = float(x), float(y), 0.0
        self.heading = 0.0
        self.speed = 0.0                   # current speed m/s
        self.tasks = []                    # [("goto", x, y, speed) | ("wait", seconds) | ("remove",)]
        self.task_t = 0.0
        self.behavior = kw.get("behavior", "")
        self.phase = random.uniform(0, 6.28)
        self.alive = True
        self.pinned = False                # placed by hand: stays until removed
        self.born = time.time()
        self.crouch = 1.0
        self.label = kind
        self.coco = COCO.get(kind, 0)
        rnd = random.Random(self.id * 7919)
        # body
        if kind == "person":
            self.height = rnd.uniform(1.55, 1.92); self.length = 0.35; self.width = 0.5
            self.shirt = rnd.choice(SHIRTS); self.pants = rnd.choice(PANTS); self.skin = rnd.choice(SKIN)
            self.temp = 31.0
        elif kind == "dog":
            self.height = rnd.uniform(0.45, 0.7); self.length = self.height * 1.5; self.width = 0.3
            self.color = rnd.choice([(40, 70, 120), (30, 30, 30), (120, 160, 200), (60, 90, 140)]); self.temp = 31.0
        elif kind == "cat":
            self.height = 0.28; self.length = 0.5; self.width = 0.18
            self.color = rnd.choice([(60, 100, 160), (40, 40, 40), (160, 160, 170), (40, 80, 130)]); self.temp = 30.0
        elif kind == "bear":
            self.height = 1.05; self.length = 1.9; self.width = 0.8; self.color = (30, 45, 70); self.temp = 30.0
        elif kind == "horse":                # stands in for deer: the COCO model has no deer
            self.height = 1.25; self.length = 1.6; self.width = 0.4; self.color = (50, 90, 140); self.temp = 31.0
        elif kind == "sheep":
            self.height = 0.75; self.length = 1.1; self.width = 0.5; self.color = (200, 210, 215); self.temp = 27.0
        elif kind == "bird":
            self.height = 0.25; self.length = 0.4; self.width = 0.6; self.color = (40, 40, 50); self.temp = 36.0
            self.z = rnd.uniform(2.5, 8.0)
        elif kind == "car":
            self.height = 1.45; self.length = 4.4; self.width = 1.8; self.color = rnd.choice(CAR_COLS); self.temp = 0.0
        elif kind == "truck":
            self.height = 3.1; self.length = 8.5; self.width = 2.5; self.color = rnd.choice(CAR_COLS); self.temp = 0.0
        elif kind == "motorcycle":
            self.height = 1.4; self.length = 2.1; self.width = 0.8; self.color = rnd.choice(CAR_COLS); self.temp = 0.0
            self.shirt = (30, 30, 30); self.pants = (40, 40, 40); self.skin = (40, 40, 40)
        elif kind == "plane":
            self.height = 4.5; self.length = 36.0; self.width = 34.0; self.color = rnd.choice([(235, 235, 238), (225, 228, 232)])
            self.temp = 0.0; self.z = rnd.uniform(150.0, 400.0)
        elif kind == "bicycle":
            self.height = 1.7; self.length = 1.75; self.width = 0.6; self.color = rnd.choice(CAR_COLS); self.temp = 31.0
            self.shirt = rnd.choice(SHIRTS); self.pants = rnd.choice(PANTS); self.skin = rnd.choice(SKIN)
        else:
            self.height = 1.0; self.length = 1.0; self.width = 1.0; self.color = (128, 128, 128); self.temp = 20.0

    # ---- what other parts ask ----
    def dist(self):
        return math.hypot(self.x - VIEW["x"], self.y - VIEW["y"])

    def moving(self):
        return self.speed > 0.05

    def has_rider(self):
        return self.kind in ("bicycle", "motorcycle")

    def describe(self):
        t = self.tasks[0][0] if self.tasks else "idle"
        b = f" {self.behavior}" if self.behavior else ""
        return f"#{self.id} {self.kind}{b} ({self.x:.1f}, {self.y:.1f}) {self.speed:.1f} m/s [{t}]"

    # ---- movement ----
    def step(self, dt):
        if not self.tasks:
            self.speed = 0.0
            if not self.pinned:
                self.alive = False
            return
        task = self.tasks[0]
        kind = task[0]
        if kind == "goto":
            _, tx, ty, sp = task[:4]
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy)
            sp *= SIM["speed_mult"]
            if self.kind not in VEHICLES and self.kind != "plane" and not in_view(self.x, self.y, 4):
                sp *= 4.0                         # nobody sees it: hurry on to / off the stage
            if d < max(0.05, sp * dt):
                self.x, self.y = tx, ty
                self.tasks.pop(0); self.task_t = 0.0
            else:
                want = math.atan2(dx, dy)
                diff = (want - self.heading + math.pi) % (2 * math.pi) - math.pi
                turn = 3.5 * dt                                    # rad/s: no instant 180 degree turns
                self.heading += max(-turn, min(turn, diff))
                k = max(0.0, math.cos(diff))                        # slow down while turning
                self.speed = sp * (0.3 + 0.7 * k)
                self.x += math.sin(self.heading) * self.speed * dt
                self.y += math.cos(self.heading) * self.speed * dt
        elif kind == "wait":
            self.speed = 0.0
            self.task_t += dt
            if task[1] is not None and self.task_t >= task[1]:
                self.tasks.pop(0); self.task_t = 0.0
        elif kind == "exit":                      # walk out of the scene, away from the camera (target decided now)
            self.tasks.pop(0)
            away = math.atan2(self.x - VIEW["x"], self.y - VIEW["y"])
            if abs((self.heading - away + math.pi) % (2 * math.pi) - math.pi) > math.radians(80):
                self.heading = away + random.uniform(-0.7, 0.7)       # would walk towards the camera: turn round
            ex, ey = _circle_exit(self.x, self.y, self.heading)
            self.tasks[0:0] = [("goto", ex, ey, task[1], "out"), ("vanish", task[1], 0)]
        elif kind == "vanish":                    # only disappear where the camera cannot see it
            _, sp, n = task
            self.tasks.pop(0)
            if in_view(self.x, self.y) and n < 4:
                hd = math.atan2(self.x - VIEW["x"], self.y - VIEW["y"])      # keep going away from the camera
                self.tasks[0:0] = [("goto", self.x + math.sin(hd) * 40, self.y + math.cos(hd) * 40, sp), ("vanish", sp, n + 1)]
            else:
                self.alive = False
        elif kind == "remove":
            self.alive = False
        # walking / trotting / flapping cycle
        if self.kind == "bird":
            self.phase += dt * 14.0
        elif self.kind in VEHICLES:
            self.phase += self.speed * dt / 0.35
        else:
            stride = max(0.3, self.height * 0.45)
            self.phase += self.speed * dt / stride * math.pi

    def leave(self, speed):
        if not self.moving():
            self.heading = math.atan2(self.x - VIEW["x"], self.y - VIEW["y"]) + random.uniform(-0.8, 0.8)
        self.tasks.append(("exit", speed))


# ---------------------------------------------------------------------------------------------------------------------
# where the camera stands and what it sees right now (set by the engine every frame):
# nothing may appear or vanish inside the picture
# ---------------------------------------------------------------------------------------------------------------------
VIEW = {"yaw": 0.0, "half": 45.0, "x": 0.0, "y": 0.0}


def in_view(x, y, margin=10.0):
    b = math.degrees(math.atan2(x - VIEW["x"], y - VIEW["y"]))
    d = (b - VIEW["yaw"] + 180.0) % 360.0 - 180.0
    return abs(d) < VIEW["half"] + margin


def _entry(target=None):
    """Where a newcomer starts: just outside what the camera (and the thermal camera) sees, as close to its
    target as possible - so it walks into the picture after a few seconds instead of popping up."""
    cx, cy = VIEW["x"], VIEW["y"]
    if target is None:
        target = _rand_point_in_area()
    tx, ty = target
    td = math.hypot(tx - cx, ty - cy)
    for r in (max(8.0, td), td + 8.0, OUTER_R):        # just outside the picture, about as far as the target: arrives fast
        cand = []
        for a in range(-180, 180, 3):
            ar = math.radians(a)
            px, py = cx + math.sin(ar) * r, cy + math.cos(ar) * r
            if in_view(px, py, 16):
                continue
            d = math.hypot(px - tx, py - ty)
            if d >= 6.0:
                cand.append((d, px, py))
        if cand:
            cand.sort()
            _d, px, py = random.choice(cand[:6])
            return px, py
    a = random.uniform(-math.pi, math.pi)
    return cx + math.sin(a) * OUTER_R, cy + math.cos(a) * OUTER_R


def _start(e, target):
    sx, sy = _entry(target)
    e.x, e.y = sx, sy
    e.heading = math.atan2(target[0] - sx, target[1] - sy)


SPEED = {"dog": (1.4, 3.2), "cat": (0.6, 1.2), "bear": (0.9, 1.5), "horse": (1.2, 2.2), "sheep": (0.4, 0.8),
         "bird": (5.0, 9.0), "person": (1.15, 1.55), "car": (6.0, 9.0), "truck": (5.0, 7.0), "motorcycle": (6.0, 9.0),
         "bicycle": (3.0, 5.0)}


def _speed(kind):
    a, b = SPEED.get(kind, (1.0, 1.5))
    return random.uniform(a, b)


# ---------------------------------------------------------------------------------------------------------------------
# spawning: everything walks in from outside the picture, crosses / visits, and walks out of it again
# ---------------------------------------------------------------------------------------------------------------------
def make_person(behavior=None, at=None):
    beh = behavior or SIM["person_behavior"]
    if beh == "mixed":
        beh = random.choices(("walk", "wander", "stand", "loiter", "run", "approach", "sneak"),
                             weights=(40, 18, 8, 10, 6, 8, 4))[0]
    px, py = at if at else _rand_point_in_area()
    p = Entity("person", 0, 0, behavior=beh)
    _start(p, (px, py))
    walk = _speed("person")
    if beh == "walk":
        p.tasks = [("goto", px, py, walk), ("exit", walk)]
    elif beh == "run":
        sp = random.uniform(3.2, 4.5)
        p.tasks = [("goto", px, py, sp), ("exit", sp)]
    elif beh == "sneak":
        p.crouch = 0.62
        p.tasks = [("goto", px, py, 0.55), ("exit", 0.55)]
    elif beh == "wander":
        p.tasks = [("goto", px, py, walk)]
        for _ in range(random.randint(2, 4)):
            wx, wy = _rand_point_in_area()
            p.tasks += [("goto", wx, wy, random.uniform(0.8, 1.3)), ("wait", random.uniform(1.0, 4.0))]
        p.tasks += [("exit", walk)]
    elif beh == "stand":
        p.tasks = [("goto", px, py, walk), ("wait", random.uniform(12, 30)), ("exit", walk)]
    elif beh == "loiter":
        p.tasks = [("goto", px, py, walk)]
        for _ in range(random.randint(3, 5)):
            p.tasks += [("goto", px + random.uniform(-1.5, 1.5), py + random.uniform(-1.5, 1.5), 0.6),
                        ("wait", random.uniform(1.5, 5))]
        p.tasks += [("exit", walk)]
    elif beh == "approach":                       # walks up to the camera head, looks, goes away
        a = math.radians(VIEW["yaw"] + random.uniform(-10, 10))
        nx, ny = VIEW["x"] + math.sin(a) * 3.2, VIEW["y"] + math.cos(a) * 3.2
        mx, my = VIEW["x"] + math.sin(a) * 9.0 + random.uniform(-3, 3), VIEW["y"] + math.cos(a) * 9.0
        p.tasks = [("goto", mx, my, walk), ("goto", nx, ny, 0.9), ("wait", random.uniform(2, 6)), ("exit", walk)]
    else:
        p.tasks = [("exit", walk)]
    return p


def make_animal(kind, at=None):
    px, py = at if at else _rand_point_in_area()
    a = Entity(kind, 0, 0, behavior="cross")
    _start(a, (px, py))
    sp = _speed(kind)
    a.tasks = [("goto", px, py, sp)]
    if kind in ("dog", "horse", "sheep", "bear") and random.random() < 0.7:          # sniffs / grazes a while
        for _ in range(random.randint(1, 2)):
            a.tasks += [("wait", random.uniform(1.0, 3.5)),
                        ("goto", px + random.uniform(-3, 3), py + random.uniform(-3, 3), sp * 0.6)]
    a.tasks += [("exit", sp)]
    return a


def make_vehicle(kind, nearest_road=False):
    """Traffic on the road nearest to the camera. It starts at the end the camera does not see."""
    cx, cy = VIEW["x"], VIEW["y"]
    roads = sorted(ROADS, key=lambda r: abs((cy if r[0] == "h" else cx) - r[1]))
    if not roads or abs((cy if roads[0][0] == "h" else cx) - roads[0][1]) > 900:
        return None
    if not nearest_road and len(roads) > 1 and random.random() < 0.3 and abs((cy if roads[1][0] == "h" else cx) - roads[1][1]) < 250:
        roads = roads[1:] + roads[:1]                    # sometimes the second road, if it is close too
    kind_o, pos = roads[0]
    sides = [True, False]
    random.shuffle(sides)
    sp = {"car": random.uniform(10.0, 16.0), "truck": random.uniform(8.0, 12.0),
          "motorcycle": random.uniform(13.0, 20.0), "bicycle": random.uniform(4.0, 6.5)}[kind]
    off = 1.6 * (2.25 if kind == "bicycle" else 1.0)
    for reach in (75.0, 120.0, 200.0):
        for forward in sides:
            if kind_o == "h":
                x0 = cx + (-reach if forward else reach); x1 = cx + (reach if forward else -reach)
                lane = pos + (-off if forward else off)
                a, b = (x0, lane), (x1, lane)
                hd = math.pi / 2 if forward else -math.pi / 2
            else:
                y0 = cy + (-reach if forward else reach); y1 = cy + (reach if forward else -reach)
                lane = pos + (off if forward else -off)
                a, b = (lane, y0), (lane, y1)
                hd = 0.0 if forward else math.pi
            if not in_view(a[0], a[1], 12):
                v = Entity(kind, a[0], a[1], behavior="drive")
                v.heading = hd
                v.speed = sp
                v.tasks = [("goto", b[0], b[1], sp), ("vanish", sp, 0)]
                return v
    return None


def make_plane():
    """A plane crossing the sky high above, far from start to end (it is tiny when it appears)."""
    hd = random.uniform(-math.pi, math.pi)
    cx, cy = VIEW["x"] + random.uniform(-600, 600), VIEW["y"] + random.uniform(-300, 900)
    dx, dy = math.sin(hd), math.cos(hd)
    p = Entity("plane", cx - dx * 4500, cy - dy * 4500, behavior="fly")
    p.heading = hd
    sp = random.uniform(60.0, 85.0)
    p.speed = sp
    p.tasks = [("goto", cx + dx * 4500, cy + dy * 4500, sp), ("remove",)]
    return p


def make(kind, behavior=None, at=None):
    if kind == "plane":
        return make_plane()
    if kind == "person":
        return make_person(behavior, at)
    if kind in VEHICLES or kind == "bicycle":
        if not ROADS:
            return None                       # this map has no road
        return make_vehicle(kind)
    return make_animal(kind, at)


def make_visit(kind, x, y, wait=None, stay=None):
    """Sent to a clicked point: comes in from outside the picture, goes there, stays a while, walks off again."""
    wait = SIM["visit_wait"] if wait is None else wait
    stay = SIM["visit_stay"] if stay is None else stay
    e = Entity(kind, 0, 0, behavior="visit")
    if kind == "bird":
        e.z = random.uniform(2.5, 5.0)
    _start(e, (x, y))
    sp = _speed(kind)
    e.tasks = [("goto", x, y, sp)]
    if stay:
        e.pinned = True
        e.tasks.append(("wait", None))
    else:
        e.tasks += [("wait", wait), ("exit", sp)]
    return e


def make_pinned(kind, x, y):
    """Stands at (x, y) right away (only for previews / scripted tests that need a fixed start)."""
    e = Entity(kind, x, y, behavior="placed")
    if kind == "bird":
        e.z = 3.0
    e.pinned = True
    e.heading = math.atan2(VIEW["x"] - x, VIEW["y"] - y)
    e.tasks = [("wait", None)]
    return e


def make_path(kind, points, speed, end="exit", crouch=1.0):
    """Scripted walk: starts at points[0] (should be outside the view), walks the points, then leaves."""
    e = Entity(kind, points[0][0], points[0][1], behavior="script")
    e.crouch = crouch
    if kind == "bird":
        e.z = 3.0
    if len(points) > 1:
        e.heading = math.atan2(points[1][0] - points[0][0], points[1][1] - points[0][1])
    e.tasks = [("goto", x, y, speed) for x, y in points[1:]]
    if end == "exit":
        e.tasks.append(("exit", speed))
    elif end == "stay":
        e.pinned = True; e.tasks.append(("wait", None))
    else:
        e.tasks.append(("wait", float(end))); e.tasks.append(("exit", speed))
    return e


# ---------------------------------------------------------------------------------------------------------------------
# static scenery: swaying trees / bushes (drawn every frame) and solid props (tent, caravan, table)
# ---------------------------------------------------------------------------------------------------------------------
class Plant:
    def __init__(self, x, y, kind, size, seed):
        self.x, self.y, self.kind, self.size = x, y, kind, size
        r = random.Random(seed)
        self.phase = r.uniform(0, 6.28); self.freq = r.uniform(0.6, 1.1)
        if kind == "tree":
            self.height = size; self.crown = size * 0.32; self.color = (r.randint(30, 50), r.randint(85, 115), r.randint(40, 60))
        else:
            self.height = size; self.crown = size * 0.7; self.color = (r.randint(30, 50), r.randint(100, 135), r.randint(50, 75))
        self.blobs = [(r.uniform(-0.6, 0.6), r.uniform(-0.4, 0.5), r.uniform(0.45, 0.75)) for _ in range(7)]

    def dist(self):
        return math.hypot(self.x - VIEW["x"], self.y - VIEW["y"])


class Prop:
    """A box-shaped thing standing on the ground (tent = box with a ridge)."""
    def __init__(self, name, x, y, w, d, h, color, ridge=False, temp_add=0.0):
        self.name, self.x, self.y, self.w, self.d, self.h, self.color, self.ridge = name, x, y, w, d, h, color, ridge
        self.temp_add = temp_add

    def dist(self):
        return math.hypot(self.x - VIEW["x"], self.y - VIEW["y"])


def make_scenery(m):
    plants = [Plant(x, y, kind, size, i + 1) for i, (x, y, kind, size) in enumerate(m.plants)]
    if m.horizon.get("snow"):
        for p in plants:
            p.color = tuple(int(c * 0.45 + 215 * 0.55) for c in p.color)        # snow on the leaves / needles
    props = [Prop(n, x, y, w, d, h, col, ridge=ridge, temp_add=ta) for (n, x, y, w, d, h, col, ridge, ta) in m.props]
    return plants, props


# ---------------------------------------------------------------------------------------------------------------------
# sun, light, temperatures
# ---------------------------------------------------------------------------------------------------------------------
def sim_hour():
    if SIM["time_mode"] == "manual":
        return float(SIM["hour"]) % 24.0
    n = datetime.now()
    return n.hour + n.minute / 60.0 + n.second / 3600.0


def sun(hour=None):
    """(elevation degrees, azimuth radians in world heading terms). Sunrise ~6, sunset ~18 (simple model)."""
    h = sim_hour() if hour is None else hour
    elev = 58.0 * math.sin(math.pi * (h - 6.0) / 12.0)
    az = math.pi / 2 + math.pi * (h - 6.0) / 12.0          # east (90 deg) -> south (180) -> west (270)
    return elev, az


def ambient_light(hour=None):
    """Brightness of the scene, 1 = full day. Twilight between +8 and -8 degrees sun elevation."""
    elev, _ = sun(hour)
    night = 0.004 + 0.025 * SIM["moon"]
    if elev >= 8:
        day = 1.0
    elif elev <= -8:
        day = 0.0
    else:
        k = (elev + 8) / 16.0
        day = k * k
    L = night + (1.0 - night) * day
    L *= 1.0 - 0.45 * SIM["clouds"] * day
    L *= 1.0 - 0.35 * SIM["rain"]
    return max(0.002, L)


BUILDINGS = {"house", "tower", "block", "caravan", "shed", "hut", "wall"}


def drawn(pr):
    """Is this prop switched on in 'what is drawn'?"""
    if pr.name == "mountain":
        return SIM["draw_backdrop"] or pr.w < 1000             # the hill tile always, the big backdrop by switch
    if pr.name in BUILDINGS:
        return SIM["draw_buildings"]
    return SIM["draw_small"]


def _leaving(e):
    """Already on its way out of the scene."""
    t = e.tasks[0] if e.tasks else None
    return t is None or t[0] in ("exit", "vanish", "remove") or (t[0] == "goto" and len(t) > 4)


class World:
    def __init__(self):
        self.lock = threading.RLock()
        self.entities = []
        self.map = maps.get(maps.DEFAULT)
        self.set_map(self.map.name)
        self.last_spawn = {}
        self.t = 0.0
        self.counts = {k: 0 for k in KINDS}       # how many have been spawned in total

    # ---- spatial grid: big maps have thousands of trees / buildings, a frame only needs the nearby ones ----
    CELL = 100.0

    def _grid(self):
        key = (id(self.plants), len(self.plants), id(self.props), len(self.props))
        if getattr(self, "_gkey", None) != key:
            gp, gq = {}, {}
            for p in self.plants:
                gp.setdefault((int(p.x // self.CELL), int(p.y // self.CELL)), []).append(p)
            for pr in self.props:
                gq.setdefault((int(pr.x // self.CELL), int(pr.y // self.CELL)), []).append(pr)
            self._gp, self._gq, self._gkey = gp, gq, key
        return self._gp, self._gq

    def _near(self, grid, x, y, r):
        c = self.CELL
        out = []
        for i in range(int((x - r) // c), int((x + r) // c) + 1):
            for j in range(int((y - r) // c), int((y + r) // c) + 1):
                cell = grid.get((i, j))
                if cell:
                    out.extend(cell)
        return out

    def landmarks(self):
        """Huge things (mountains) that are seen from everywhere."""
        key = (id(self.props), len(self.props))
        if getattr(self, "_lmkey", None) != key:
            self._lm = [pr for pr in self.props if pr.name == "mountain"]
            self._lmkey = key
        return [pr for pr in self._lm if drawn(pr)]

    def nearby_plants(self, x, y, r):
        if not SIM["draw_trees"]:
            return []
        return self._near(self._grid()[0], x, y, r)

    def nearby_props(self, x, y, r):
        return [pr for pr in self._near(self._grid()[1], x, y, r) if drawn(pr)]

    def set_map(self, name):
        """Switch the place: new scenery, road and walking area; everything that moves is cleared."""
        global ROAD_Y, AREA, ROADS
        m = maps.get(name)
        with self.lock:
            self.map = m
            ROADS = list(m.roads) if m.vehicles else []
            ROAD_Y = next((p for o, p in ROADS if o == "h"), None)
            AREA = m.area
            self.plants, self.props = make_scenery(m)
            self.entities = []
        return m

    def add(self, e):
        if e is None:
            return None
        with self.lock:
            self.entities.append(e)
            self.counts[e.kind] = self.counts.get(e.kind, 0) + 1
        return e

    def spawn(self, kind, behavior=None, at=None):
        return self.add(make(kind, behavior, at))

    def remove(self, eid):
        with self.lock:
            self.entities = [e for e in self.entities if e.id != eid]

    def send_away(self, eid):
        with self.lock:
            for e in self.entities:
                if e.id == eid:
                    e.pinned = False
                    e.tasks = []
                    e.leave(_speed(e.kind))

    def scare(self, r=60.0):
        """A siren / loud sound at the camera head: the animals nearby run away (tests Motion Watch's deterrent)."""
        n = 0
        with self.lock:
            for e in self.entities:
                if e.kind in ANIMALS and not getattr(e, "fleeing", False) and e.dist() < r:
                    e.fleeing = True; e.pinned = False
                    e.heading = math.atan2(e.x - VIEW["x"], e.y - VIEW["y"]) + random.uniform(-0.4, 0.4)
                    e.speed = 0.0
                    e.tasks = [("exit", max(_speed(e.kind), 1.5) * 2.2)]
                    n += 1
        return n

    def clear(self, kinds=None):
        with self.lock:
            self.entities = [e for e in self.entities if kinds is not None and e.kind not in kinds]

    def find(self, eid):
        with self.lock:
            return next((e for e in self.entities if e.id == eid), None)

    def snapshot(self):
        with self.lock:
            return list(self.entities)

    def alive_count(self, kind):
        with self.lock:
            return sum(1 for e in self.entities if e.kind == kind and not e.pinned)

    def step(self, dt):
        self.t += dt
        with self.lock:
            for e in self.entities:
                e.step(dt)
                t = e.tasks[0] if e.tasks else None
                if t and t[0] == "goto" and len(t) > 4 and e.dist() > 14 and not in_view(e.x, e.y, 18):
                    e.alive = False                  # on its way out and nobody can see it any more
            self.entities = [e for e in self.entities if e.alive]
            if SIM["bg_traffic"]:                       # background life: a few cars on the roads, a plane now and then
                now = self.t
                cars = sum(1 for e in self.entities if e.kind in VEHICLES and getattr(e, "bg", False))
                if cars < 3 and ROADS and now - self.last_spawn.get("_bgcar", -1e9) > 4.0:
                    self.last_spawn["_bgcar"] = now
                    v = self.add(make_vehicle(random.choice(("car", "car", "car", "truck", "motorcycle"))))
                    if v is not None:
                        v.bg = True                         # background: the sliders leave it alone
                planes = sum(1 for e in self.entities if e.kind == "plane" and getattr(e, "bg", False))
                if planes < 1 and now - self.last_spawn.get("_bgplane", -1e9) > 25.0:
                    self.last_spawn["_bgplane"] = now
                    self.add(make_plane()).bg = True
            if SIM["auto_spawn"]:
                now = self.t
                for kind in KINDS:
                    want = SIM.want(kind)
                    staying = [e for e in self.entities if e.kind == kind and not e.pinned and not _leaving(e) and not getattr(e, "bg", False)]
                    if len(staying) > want:                     # slider turned down: the extra ones walk away
                        staying.sort(key=lambda e: -e.born)
                        for e in staying[:len(staying) - want]:
                            e.tasks = []
                            e.heading = math.atan2(e.x - VIEW["x"], e.y - VIEW["y"]) + random.uniform(-0.5, 0.5)
                            e.speed = 0.0
                            e.leave(_speed(e.kind) * 1.2)
                    if want <= 0:
                        continue
                    have = min(len(staying), want)
                    gap = SIM["spawn_gap"] * (0.5 + random.random())
                    if have < want and now - self.last_spawn.get(kind, -1e9) > gap:
                        self.last_spawn[kind] = now
                        self.add(make(kind))            # None (no road on this map) is ignored
