"""The "Region" map, built from tiles: every place is a 160 x 160 m tile and the tiles TOUCH each other in a tight
grid around the campsite. Which places exist is chosen in the start window / the World tab (SIM["tiles"]); the
remaining tiles always close up, so there are never gaps.

Two roads with traffic run along the tile borders next to the camp (left-right and front-back)."""
import math
import random

import numpy as np

from simulator.config import SIM
from simulator.scene.maps import MapDef, poi

T = 160.0                      # tile size (metres)
H = T / 2.0
ASPH, WATER, CONC = (80, 80, 86), (120, 92, 58), (150, 150, 155)
FOREST = (35, 75, 55)
CROPS = [(60, 150, 170), (70, 120, 90), (70, 160, 190), (55, 140, 120), (90, 170, 200), (60, 110, 75)]
HOUSE_COLS = [(170, 190, 205), (150, 160, 200), (190, 200, 210), (140, 170, 190), (200, 190, 170), (175, 175, 160)]
TOWER_COLS = [(150, 140, 120), (170, 165, 160), (120, 110, 95), (190, 185, 175), (140, 150, 165), (110, 120, 135), (95, 100, 110)]
CAR_COLS = [(40, 40, 200), (200, 200, 200), (30, 30, 30), (150, 90, 30), (60, 140, 60), (120, 120, 130)]

# name: (label, size in tiles (w, h), preferred direction from the camp, description)
TILES = {
    "camp":       ("Campsite", (1, 1), (0, 0), "Tents, caravans, the camera's start."),
    "lake":       ("Lake & beach", (1, 1), (0, 1), "Water, sand beach, boats and a jetty."),
    "city":       ("City (skyscrapers)", (1, 1), (1, 0), "Street crossing between towers up to 215 m."),
    "suburbs":    ("Suburbs", (1, 1), (1, 1), "Two streets with houses and parked cars."),
    "village":    ("Village & church", (1, 1), (-1, 0), "Village road, houses and a church tower."),
    "forest":     ("Forest", (1, 1), (-1, 1), "Dense trees - deer, bears and dogs hide here."),
    "industrial": ("Industrial zone", (1, 1), (1, -1), "Warehouses, a chimney and a car park."),
    "airfield":   ("Airfield", (2, 1), (0, -1), "Runway, hangars and a control tower."),
    "farmland":   ("Farmland", (1, 1), (-1, -1), "Fields, a barn and a silo."),
    "park":       ("Park", (1, 1), (1, 2), "Lawn, pond, paths, benches and old trees."),
    "parking":    ("Parking lot", (1, 1), (2, 0), "Rows of parked cars, lamp posts - car filter test."),
    "hill":       ("Hill", (1, 1), (-1, 2), "A 70 m hill with rocks on top."),
}
ORDER = ["camp", "lake", "city", "village", "airfield", "forest", "suburbs", "industrial", "farmland", "park", "parking", "hill"]
DEFAULT_TILES = list(ORDER)


def layout(selected):
    """Grid cells for the selected tiles: camp in the middle, every other tile placed next to tiles already placed,
    as close as possible to its preferred direction - so they always touch, whatever is switched off."""
    sel = ["camp"] + [t for t in ORDER if t in selected and t != "camp"]
    used = {}
    for name in sel:
        w, h = TILES[name][1]
        pref = np.array(TILES[name][2], float)
        if name == "camp":
            cells = [(0, 0)]
        else:
            best, bs = None, 1e9
            for i in range(-6, 7):
                for j in range(-6, 7):
                    cells = [(i + a, j + b) for a in range(w) for b in range(h)]
                    if any(c in used for c in cells):
                        continue
                    touch = sum((c[0] + dx, c[1] + dy) in used for c in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if not touch:
                        continue
                    centre = np.mean(np.array(cells, float), axis=0)
                    d = float(np.linalg.norm(centre))
                    direction = float(np.dot(centre / max(d, 1e-6), pref / max(np.linalg.norm(pref), 1e-6))) if d else 0.0
                    score = -2.0 * direction + 0.6 * d + 0.4 * float(np.linalg.norm(centre - pref)) - 0.6 * touch   # snug: no holes
                    if score < bs:
                        best, bs = cells, score
            cells = best
        for c in cells:
            used[c] = name
    tiles = {}
    for c, name in used.items():
        tiles.setdefault(name, []).append(c)
    return tiles


class Builder:
    def __init__(self, seed=77):
        self.rng = random.Random(seed)
        self.L, self.props, self.plants, self.pois = [], [], [], []

    # ---- helpers in world coordinates ----
    def layer(self, shape, params, col, tex, td, tn):
        self.L.append((shape, params, col, tex, td, tn))

    def rect(self, x0, y0, x1, y1, col, tex=0.3, td=3.0, tn=0.5, deco=None):
        self.layer("rect", (x0, y0, x1, y1, {"deco": deco} if deco else {}), col, tex, td, tn)

    def plate(self, ox, oy, col, w_tiles=1, tex=0.45):
        """The tile's own ground, filling the whole square (so neighbouring tiles visibly touch)."""
        hw = w_tiles * H
        self.layer("rect", (ox - hw, oy - H, ox + hw, oy + H, {}), col, tex, 2.0, 0.0)

    def P(self, *a):
        self.props.append(a)

    def tree(self, x, y, size=None, kind="tree"):
        r = self.rng
        self.plants.append((round(x, 1), round(y, 1), kind, size or (r.uniform(6, 11) if kind == "tree" else r.uniform(0.9, 1.8))))

    def house(self, x, y, w=None, d=None, h=None):
        r = self.rng
        self.P("house", round(x, 1), round(y, 1), w or round(r.uniform(9, 13), 1), d or round(r.uniform(8, 10), 1),
               h or round(r.uniform(5.5, 8.0), 1), r.choice(HOUSE_COLS), True, 0.0)

    def car(self, x, y, along_x=True):
        r = self.rng
        w, d = (4.4, 1.8) if along_x else (1.8, 4.4)
        self.P("car", round(x, 1), round(y, 1), w, d, 1.45, r.choice(CAR_COLS), False, 0.0)

    def view(self, name, x, y, h, yaw, pitch, desc):
        self.pois.append(poi(name, x, y, h, yaw, pitch, desc))

    # ---- the tiles (ox, oy = tile centre; content stays 8 m inside the border, roads run along borders) ----
    def camp(self, ox, oy, face):
        b = oy - 40.0
        self.plate(ox, oy, (58, 118, 92))
        self.layer("ellipse", (ox + 2, b + 14, 18.0, 12.0, {}), (70, 115, 105), 0.6, 1.0, 0.0)
        self.layer("line", (ox - 1, b + 0.5, ox + 9, b + 45, 0.8, {}), (150, 172, 185), 0.3, 3.0, 0.5)
        for t in (("tent", 5.0, 8.0, 2.4, 2.0, 1.25, (40, 120, 230), True), ("tent", 11.0, 12.5, 2.2, 1.8, 1.2, (60, 170, 70), True),
                  ("tent", -4.0, 15.0, 2.6, 2.1, 1.3, (200, 80, 60), True), ("tent", -14.0, 30.0, 2.4, 2.0, 1.25, (50, 200, 230), True),
                  ("caravan", -9.0, 14.0, 5.2, 2.2, 2.5, (225, 225, 220), False), ("caravan", 17.0, 22.0, 5.6, 2.3, 2.6, (210, 220, 230), False),
                  ("caravan", 26.0, 30.0, 5.6, 2.3, 2.6, (200, 210, 225), False), ("table", 1.2, 4.5, 1.6, 0.8, 0.75, (60, 100, 150), False),
                  ("shed", -22.0, 24.0, 6.0, 4.0, 3.2, (90, 120, 150), True)):
            self.P(t[0], ox + t[1], b + t[2], t[3], t[4], t[5], t[6], t[7], 0.0)
        for x, y, k, s in ((-6.5, 9.5, "bush", 1.3), (7.5, 12.0, "bush", 1.6), (-12.5, 19.0, "tree", 7.5), (13.5, 24.0, "tree", 9.0),
                           (-3.0, 20.0, "bush", 1.1), (21.0, 13.0, "tree", 6.5), (-40, 50, "tree", 9.0), (45, 55, "tree", 8.0)):
            self.tree(ox + x, b + y, s, k)
        self.view("Campsite (start)", ox, b, 1.8, face, -4, "Tents and caravans; the neighbouring places all around.")
        self.view("Camp on a pole", ox, b - 10, 12.0, face, -8, "12 m pole at the camp: all the touching places in view.")

    def lake(self, ox, oy):
        self.plate(ox, oy, (140, 190, 215), tex=0.35)                     # sand all round the water
        self.layer("ellipse", (ox, oy + 8, 78.0, 66.0, {}), WATER, 0.15, -5.0, 3.0)
        self.P("boat", ox - 15, oy - 58, 1.5, 4.5, 0.7, (40, 60, 160), False, 0.0)
        self.P("boat", ox - 28, oy - 56, 1.5, 4.0, 0.7, (200, 200, 200), False, 0.0)
        self.P("wall", ox + 10, oy - 45, 2.0, 26.0, 0.6, (60, 90, 120), False, 0.0)
        self.view("Lake & beach", ox - 50, oy - 64, 2.0, 30, -3, "On the beach: boats, jetty, the water.")

    def city(self, ox, oy):
        self.rect(ox - H, oy - H, ox + H, oy + H, CONC, 0.25, 6.0, 2.0)
        self.layer("vband", (ox - 4.5, ox + 4.5, oy - H + 3, oy + H - 3, {"deco": "road"}), ASPH, 0.2, 6.0, 1.5)
        self.rect(ox - H + 3, oy - 4.5, ox + H - 3, oy + 4.5, ASPH, 0.2, 6.0, 1.5)
        r = self.rng
        tallest = None
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx, cy = ox + sx * 41, oy + sy * 41
                n = r.choice([1, 2, 2])
                for k in range(n):
                    w = 58.0 / n
                    bx = cx - 29 + w * (k + 0.5)
                    h = round(r.uniform(60, 215) if k == 0 else r.uniform(25, 120), 1)
                    self.P("tower" if h > 35 else "block", round(bx, 1), round(cy, 1), round(w - r.uniform(4, 8), 1),
                           round(r.uniform(38, 52), 1), h, r.choice(TOWER_COLS), False, 0.0)
                    if tallest is None or h > tallest[2]:
                        tallest = (bx, cy, h, sx, sy)
        for k in range(-3, 4):
            self.P("post", ox + k * 22.0, oy - 8.0, 0.15, 0.15, 7.0, (110, 110, 115), False, 0.0)
        self.view("City crossing", ox, oy - 2, 2.5, 0, 10, "In the middle of the street crossing, towers all around.")
        if tallest:
            bx, by, h, sx, sy = tallest                                  # roof edge on the camp side, looking over everything
            a = math.atan2(0.0 - bx, -40.0 - by)
            self.view("Skyscraper rooftop", bx + math.sin(a) * 30.0, by + math.cos(a) * 30.0, h + 3.0, math.degrees(a), -18,
                      f"Edge of the tallest tower's roof ({h:.0f} m): the touching places below.")

    def suburbs(self, ox, oy):
        r = self.rng
        self.plate(ox, oy, (62, 145, 92))
        for sy in (-35.0, 35.0):
            self.rect(ox - H + 3, oy + sy - 4, ox + H - 3, oy + sy + 4, ASPH, 0.2, 6.0, 1.5)
            x = ox - H + 12
            while x < ox + H - 12:
                for side in (-1, 1):
                    self.house(x, oy + sy + side * 13.0)
                    if r.random() < 0.4:
                        self.car(x + 8, oy + sy + side * 2.5)
                x += r.uniform(22, 28)
        for k in range(8):
            self.tree(ox + r.uniform(-70, 70), oy + r.choice((-70, 0, 70)) + r.uniform(-4, 4))
        self.view("Suburbs", ox - H + 6, oy - 35, 2.0, 90, -3, "Street with houses and parked cars.")

    def village(self, ox, oy):
        r = self.rng
        self.plate(ox, oy, (60, 128, 100))
        self.rect(ox - H + 3, oy - 3.5, ox + H - 3, oy + 3.5, ASPH, 0.2, 6.0, 1.5, deco=None)
        x = ox - H + 12
        while x < ox + H - 12:
            for side in (-1, 1):
                if not (side > 0 and abs(x - (ox + 30)) < 16):
                    self.house(x, oy + side * 13.0)
            x += r.uniform(20, 26)
        self.P("house", ox + 30, oy + 40, 12.0, 24.0, 14.0, (200, 205, 215), True, 0.0)
        self.P("tower", ox + 30, oy + 57, 6.0, 6.0, 36.0, (190, 195, 205), False, 0.0)
        for k in range(10):
            self.tree(ox + r.uniform(-70, 70), oy + r.choice((-1, 1)) * r.uniform(30, 70))
        self.view("Village & church", ox + H - 6, oy, 2.5, -90, -3, "Village road, church on the right.")

    def forest(self, ox, oy):
        r = self.rng
        self.rect(ox - H, oy - H, ox + H, oy + H, FOREST, 0.7, -1.0, 1.0)
        for _ in range(260):
            self.tree(ox + r.uniform(-H + 4, H - 4), oy + r.uniform(-H + 4, H - 4), r.uniform(8, 16))
        for _ in range(30):
            self.tree(ox + r.uniform(-H + 4, H - 4), oy + r.uniform(-H + 4, H - 4), kind="bush")
        self.view("Forest edge", ox + H + 2, oy - 20, 2.0, -90, -2, "Looking into the forest.")

    def industrial(self, ox, oy):
        r = self.rng
        self.rect(ox - H, oy - H, ox + H, oy + H, CONC, 0.3, 6.0, 2.0)
        self.rect(ox - H + 6, oy - H + 6, ox - 10, oy - 25, ASPH, 0.2, 7.0, 2.0, deco="parking")
        for (x, y) in ((25, 45), (-35, 40), (40, -5), (-25, 5), (45, -50)):
            self.P("block", ox + x, oy + y, round(r.uniform(28, 40), 1), round(r.uniform(18, 26), 1), round(r.uniform(8, 13), 1),
                   r.choice([(150, 150, 155), (110, 120, 130), (90, 110, 140)]), False, 0.0)
        self.P("tower", ox + 5, oy + 60, 6.0, 6.0, 65.0, (130, 130, 140), False, 0.0)
        for k in range(10):
            if r.random() < 0.75:
                self.car(ox - H + 10 + k * 6.5, oy - H + 15, along_x=False)
        self.view("Industrial zone", ox - H + 6, oy + 20, 3.0, 90, -5, "Warehouses, chimney and car park.")

    def airfield(self, ox, oy, w_tiles):
        r = self.rng
        half_w = w_tiles * T / 2.0
        self.rect(ox - half_w, oy - H, ox + half_w, oy + H, (55, 140, 90), 0.5, 2.0, -1.0)
        self.rect(ox - half_w + 12, oy - 35, ox + half_w - 12, oy - 5, ASPH, 0.15, 7.0, 2.0)
        for k in range(3):
            self.P("block", ox - half_w + 40 + k * 55, oy + 45, 45.0, 30.0, 13.0, (150, 160, 170), False, 0.0)
        self.P("tower", ox + half_w - 40, oy + 40, 8.0, 8.0, 26.0, (200, 200, 205), False, 0.0)
        self.view("Airfield", ox - half_w + 14, oy - 20, 3.0, 90, -2, "End of the runway, hangars on the left.")

    def farmland(self, ox, oy):
        r = self.rng
        self.plate(ox, oy, (70, 115, 120))                                 # dirt tracks between the fields
        for sx in (-1, 1):
            for sy in (-1, 1):
                self.rect(ox + 2 if sx > 0 else ox - H, oy + 2 if sy > 0 else oy - H,
                          ox + H if sx > 0 else ox - 2, oy + H if sy > 0 else oy - 2, r.choice(CROPS), 0.6, 3.0, -1.0)
        self.P("house", ox + 30, oy + 30, 22.0, 14.0, 11.0, r.choice([(40, 50, 150), (60, 70, 120)]), True, 0.0)
        self.P("block", ox + 50, oy + 30, 5.0, 5.0, 15.0, (170, 170, 175), False, 0.0)
        self.view("Farmland", ox + H - 6, oy - 4, 2.5, -90, -4, "Fields, barn and silo.")

    def park(self, ox, oy):
        r = self.rng
        self.rect(ox - H, oy - H, ox + H, oy + H, (70, 150, 85), 0.6, 1.0, 0.0)
        self.layer("ellipse", (ox + 20, oy + 15, 28.0, 18.0, {}), WATER, 0.15, -5.0, 3.0)
        self.layer("line", (ox - H + 5, oy - 40, ox + H - 5, oy + 50, 1.5, {}), (150, 172, 185), 0.3, 3.0, 0.5)
        self.layer("line", (ox - 50, oy + H - 5, ox - 10, oy - H + 5, 1.5, {}), (150, 172, 185), 0.3, 3.0, 0.5)
        for _ in range(28):
            self.tree(ox + r.uniform(-70, 70), oy + r.uniform(-70, 70), r.uniform(8, 13))
        for k in range(4):
            self.P("table", ox - 30 + k * 18, oy - 30, 1.6, 0.6, 0.6, (60, 100, 150), False, 0.0)
            self.P("post", ox - 40 + k * 25, oy - 36, 0.15, 0.15, 5.0, (110, 110, 115), False, 0.0)
        self.view("Park", ox - H + 6, oy - 40, 2.0, 70, -3, "Path through the park, pond ahead.")

    def parking(self, ox, oy):
        r = self.rng
        self.rect(ox - H, oy - H, ox + H, oy + H, ASPH, 0.2, 7.0, 2.0, deco="parking")
        for row in (-50.0, -20.0, 20.0, 50.0):
            x = ox - H + 10
            while x < ox + H - 10:
                if r.random() < 0.65:
                    self.car(x, oy + row, along_x=False)
                x += 2.7
        for k in (-40, 0, 40):
            self.P("post", ox + k, oy, 0.15, 0.15, 6.0, (110, 110, 115), False, 0.0)
        self.view("Parking lot", ox - H + 6, oy, 3.0, 90, -6, "Rows of parked cars.")

    def hill(self, ox, oy):
        self.plate(ox, oy, (90, 120, 110))
        self.P("mountain", ox, oy, 150.0, 150.0, 70.0, (95, 105, 115), False, 0.0)
        self.view("Hill", ox, oy - H - 6, 2.0, 0, 6, "At the foot of the hill.")


def build():
    sel = [t for t in (SIM.get("tiles") or DEFAULT_TILES) if t in TILES]
    cells = layout(sel)
    b = Builder()
    centre = lambda name: (np.mean([c[0] for c in cells[name]]) * T, np.mean([c[1] for c in cells[name]]) * T)
    # the camp looks towards the lake if there is one, otherwise towards its nearest neighbour
    face = 0.0
    for want in ("lake", "city", "village"):
        if want in cells:
            cx, cy = centre(want)
            face = math.degrees(math.atan2(cx, cy + 40.0)); break
    for name in ["camp"] + [t for t in ORDER if t in cells and t != "camp"]:
        ox, oy = centre(name)
        if name == "camp":
            b.camp(ox, oy, face)
        elif name == "airfield":
            b.airfield(ox, oy, TILES[name][1][0])
        else:
            getattr(b, name)(ox, oy)
    # roads along the tile borders next to the camp (traffic), on top of everything
    b.layer("hband", (-H - 3.5, -H + 3.5, {"deco": "road"}), ASPH, 0.2, 6.0, 1.5)
    b.layer("vband", (H - 3.5, H + 3.5, -2000.0, 2000.0, {"deco": "road"}), ASPH, 0.2, 6.0, 1.5)
    # a few trees on the meadow around the tiles
    xs = [c[0] for v in cells.values() for c in v]; ys = [c[1] for v in cells.values() for c in v]
    x0, x1, y0, y1 = (min(xs) - 0.5) * T, (max(xs) + 0.5) * T, (min(ys) - 0.5) * T, (max(ys) + 0.5) * T
    r = b.rng
    for _ in range(140):
        x, y = r.uniform(x0 - 250, x1 + 250), r.uniform(y0 - 250, y1 + 250)
        if not (x0 - 5 < x < x1 + 5 and y0 - 5 < y < y1 + 5) and abs(y + H) > 8 and abs(x - H) > 8:
            b.tree(x, y)
    # the big mountain behind the world (drawn only when "Mountain behind the world" is on)
    b.P("mountain", (x0 + x1) / 2 - 200, y1 + 1500, 2000.0, 2000.0, 900.0, (95, 105, 115), False, 0.0)
    labels = ", ".join(TILES[t][0] for t in ORDER if t in cells)
    m = MapDef("region", "Region (touching places)",
               f"Every place is a 160 m tile, all touching: {labels}. Choose which ones in the World tab or the start window.",
               ground=(55, 130, 80), layers=b.L,
               horizon={"mountains": 0.8, "treeline": 0.7, "treeline_col": (45, 75, 50), "buildings": False},
               plants=b.plants, props=b.props, road_y=-H, area=(-14.0, 14.0, 4.0, 22.0), ambient=16.0,
               roads=[("h", -H), ("v", H)], extent=(x0 - 400, x1 + 400, y0 - 400, y1 + 2600))
    m.pois = b.pois
    m.tiles = cells
    return m
