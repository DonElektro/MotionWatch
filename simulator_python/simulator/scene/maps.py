"""The places the camera can stand in. A map is plain data: ground layers (painted into the panorama and used for the
thermal picture), the horizon, trees / bushes, solid props, the road for traffic and the area where people walk."""
import random

# a ground layer: (shape, params, BGR colour, texture strength, thermal offset by day, thermal offset at night)
#   shapes: "hband" (y0, y1)  "vband" (x0, x1, y0, y1)  "rect" (x0, y0, x1, y1)  "ellipse" (cx, cy, rx, ry)
#           "line" (ax, ay, bx, by, half width)  "beyond" (y0)  everything farther than y0
#   extras in params["deco"]: "road" (edge + dashed middle line), "parking" (white bays), "tiles" (terrace joints)


class MapDef:
    def __init__(self, name, label, desc, ground, layers, horizon, plants, props, road_y, area, ambient=None,
                 vehicles=True, spawn_angle=120, camera=None, base=None, custom=False, roads=None, extent=None):
        self.name, self.label, self.desc = name, label, desc
        self.ground = ground                  # base colour of the open ground (BGR)
        self.layers = layers
        self.horizon = horizon                # {"mountains": 0..1, "treeline": deg, "treeline_col": BGR, "buildings": bool}
        self.plants = plants                  # [(x, y, "tree" | "bush", size)]
        self.props = props                    # [(name, x, y, w, d, h, BGR, ridge, thermal_add)]
        self.road_y = road_y                  # traffic drives along y = road_y (None = no traffic)
        self.roads = roads if roads is not None else ([("h", road_y)] if road_y is not None else [])
        self.area = area                      # (x0, x1, y0, y1) where walkers pass through
        self.ambient = ambient                # suggested air temperature
        self.vehicles = vehicles
        self.spawn_angle = spawn_angle
        self.camera = camera                  # (x, y, height or None, facing degrees) where the camera head stands
        self.base = base or name              # custom maps keep the ground / horizon of a built-in map
        self.custom = custom
        self.extent = extent or (-260.0, 260.0, -260.0, 260.0)     # (x0, x1, y0, y1) metres covered by the ground raster
        self.pois = []                        # places to put the camera: dicts name, x, y, h, yaw, pitch, desc


def _hedge(x0, x1, y, size=1.3, step=1.6):
    out = []
    x = x0
    while x <= x1:
        out.append((x, y, "bush", size + random.Random(int(x * 10 + y)).uniform(-0.15, 0.15)))
        x += step
    return out


def _forest(seed, n, r0, r1, a0=-150, a1=150, keep_out=None):
    import math
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        a = math.radians(rng.uniform(a0, a1)); r = rng.uniform(r0, r1)
        x, y = r * math.sin(a), r * math.cos(a)
        if keep_out and keep_out(x, y):
            continue
        out.append((round(x, 1), round(y, 1), "tree", rng.uniform(6.0, 13.0)))
    return out


def _parked_row(x0, x1, y, step=2.7, skip=()):
    cols = [(40, 40, 200), (200, 200, 200), (30, 30, 30), (150, 90, 30), (60, 140, 60), (120, 120, 130), (180, 180, 60)]
    out = []
    i = 0
    x = x0
    while x <= x1:
        if i not in skip:
            out.append(("car", x, y, 1.8, 4.4, 1.45, cols[(i * 5 + int(y)) % len(cols)], False, 0.0))
        x += step; i += 1
    return out


MAPS = {}


def _add(m):
    MAPS[m.name] = m


_add(MapDef(
    "camp", "Camp site", "Meadow below the mountains, tent and caravan, a road behind the field.",
    ground=(55, 128, 78),
    layers=[("line", (-1.0, 0.5, 9.2, 29.0, 0.75), (150, 172, 185), 0.3, 3.0, 0.5),
            ("ellipse", (2.0, 9.0, 7.7, 5.0), (70, 115, 105), 0.6, 1.0, 0.0),
            ("hband", (28.8, 35.2, {"deco": "road"}), (78, 78, 84), 0.2, 6.0, 1.5)],
    horizon={"mountains": 1.0, "treeline": 0.55, "treeline_col": (48, 78, 52), "buildings": False},
    plants=[(-12.5, 19.0, "tree", 7.5), (13.5, 24.0, "tree", 9.0), (-24.0, 30.0, "tree", 8.0), (21.0, 13.0, "tree", 6.5),
            (-19.0, 6.0, "tree", 6.0), (28.0, 35.0, "tree", 10.0), (-6.5, 9.5, "bush", 1.3), (7.5, 12.0, "bush", 1.6),
            (-3.0, 17.0, "bush", 1.1), (10.5, 6.5, "bush", 1.2), (-15.5, 11.0, "bush", 1.8), (3.5, 25.0, "bush", 1.5),
            (-9.5, 25.5, "bush", 1.4), (16.0, 18.0, "bush", 1.0)],
    props=[("tent", 5.0, 8.0, 2.4, 2.0, 1.25, (40, 120, 230), True, 0.0),
           ("caravan", -9.0, 14.0, 5.2, 2.2, 2.5, (225, 225, 220), False, 0.0)],
    road_y=32.0, area=(-14.0, 14.0, 4.0, 22.0), ambient=16.0))

_add(MapDef(
    "garden", "Garden behind the house", "Lawn with a terrace, shed, hedge and fence; a quiet street behind the fence.",
    ground=(50, 140, 70),
    layers=[("rect", (-6.0, 0.0, 6.0, 4.0, {"deco": "tiles"}), (140, 150, 160), 0.25, 5.0, 1.0),
            ("line", (0.0, 4.0, 2.5, 17.5, 0.55), (120, 150, 170), 0.3, 3.0, 0.5),
            ("ellipse", (-7.0, 9.0, 3.0, 1.2), (40, 70, 110), 0.7, 1.0, 0.5),
            ("ellipse", (8.0, 13.0, 2.5, 1.0), (40, 70, 110), 0.7, 1.0, 0.5),
            ("hband", (19.0, 21.0, {}), (150, 165, 175), 0.2, 5.0, 1.0),
            ("hband", (21.0, 27.0, {"deco": "road"}), (80, 80, 86), 0.2, 6.0, 1.5)],
    horizon={"mountains": 0.0, "treeline": 0.9, "treeline_col": (55, 85, 60), "buildings": True},
    plants=_hedge(-16.0, -7.0, 18.0) + [(-13.0, 7.0, "tree", 6.5), (12.0, 16.0, "tree", 8.0), (-3.5, 12.5, "bush", 1.0),
                                       (5.5, 9.0, "bush", 1.2), (14.0, 6.0, "bush", 1.6), (-10.0, 30.0, "tree", 9.0), (9.0, 31.0, "tree", 10.0)],
    props=[("shed", 9.0, 11.0, 3.0, 2.5, 2.3, (60, 90, 120), True, 0.0),
           ("fence", 4.5, 18.0, 23.0, 0.08, 1.2, (90, 120, 150), False, 0.0),
           ("fence", -16.5, 10.0, 0.08, 16.0, 1.2, (90, 120, 150), False, 0.0),
           ("fence", 16.0, 10.0, 0.08, 16.0, 1.2, (90, 120, 150), False, 0.0),
           ("table", -2.5, 2.4, 1.6, 0.8, 0.75, (60, 100, 150), False, 0.0),
           ("house", -10.0, 34.0, 9.0, 7.0, 6.0, (170, 190, 205), True, 0.0),
           ("house", 6.0, 33.0, 8.0, 6.0, 5.5, (150, 160, 200), True, 0.0)],
    road_y=24.0, area=(-12.0, 12.0, 3.0, 16.0), ambient=17.0))

_add(MapDef(
    "parking", "Parking lot", "Asphalt car park with parked cars and lamp posts next to a busy street - the car filter test.",
    ground=(82, 82, 88),
    layers=[("rect", (-40.0, 0.0, 40.0, 19.0, {"deco": "parking"}), (85, 85, 90), 0.25, 7.0, 2.0),
            ("hband", (19.0, 21.0, {}), (55, 128, 78), 0.6, 2.0, -1.0),
            ("hband", (21.0, 28.0, {"deco": "road"}), (75, 75, 80), 0.2, 7.0, 2.0),
            ("beyond", (31.0,), (55, 120, 75), 0.6, 2.0, -1.0)],
    horizon={"mountains": 0.25, "treeline": 0.6, "treeline_col": (50, 80, 55), "buildings": True},
    plants=[(-20.0, 20.0, "tree", 7.0), (-6.0, 20.0, "tree", 6.0), (8.0, 20.0, "tree", 7.0), (22.0, 20.0, "tree", 6.5),
            (-14.0, 20.0, "bush", 1.0), (1.0, 20.0, "bush", 1.1), (15.0, 20.0, "bush", 1.0)],
    props=_parked_row(-16.0, 16.0, 9.5, skip=(2, 5, 6, 7, 9)) + _parked_row(-16.0, 16.0, 16.0, skip=(0, 6, 11)) +
          [("post", -10.0, 10.5, 0.15, 0.15, 5.0, (110, 110, 115), False, 0.0),
           ("post", 10.0, 10.5, 0.15, 0.15, 5.0, (110, 110, 115), False, 0.0),
           ("house", 0.0, 40.0, 26.0, 10.0, 8.0, (180, 175, 170), False, 0.0)],
    road_y=24.5, area=(-14.0, 14.0, 3.0, 13.0), ambient=18.0))

_add(MapDef(
    "forest", "Forest clearing", "A clearing in the woods with a trail - deer, bears and dogs, no traffic, lots of swaying leaves.",
    ground=(45, 105, 75),
    layers=[("line", (-30.0, 6.0, 30.0, 14.0, 0.9), (70, 110, 135), 0.5, 2.0, 0.5),
            ("ellipse", (4.0, 10.0, 3.0, 2.0), (55, 90, 110), 0.7, 1.0, 0.0),
            ("beyond", (26.0,), (35, 75, 55), 0.7, -1.0, 1.0)],
    horizon={"mountains": 0.5, "treeline": 2.5, "treeline_col": (35, 60, 40), "buildings": False},
    plants=_forest(41, 46, 17.0, 40.0, keep_out=lambda x, y: abs((y - 6) - (x + 30) * 8 / 60) < 2.0) +
           [(-9.0, 12.0, "tree", 9.0), (11.0, 16.0, "tree", 11.0), (-4.0, 8.0, "bush", 1.4), (7.0, 6.0, "bush", 1.2),
            (-12.0, 6.0, "bush", 1.7), (13.0, 9.0, "bush", 1.5), (2.0, 17.0, "bush", 1.3), (-15.0, 15.0, "bush", 1.9)],
    props=[("stump", -2.0, 6.5, 0.6, 0.6, 0.5, (40, 70, 100), False, 0.0),
           ("woodpile", 6.5, 13.0, 2.5, 1.0, 1.0, (50, 90, 140), False, 0.0)],
    road_y=None, area=(-13.0, 13.0, 4.0, 17.0), ambient=12.0, vehicles=False))

_add(MapDef(
    "lake", "Lakeside", "Sand beach at a lake, a boat on the shore; a road passes right in front of the camera (close, fast cars).",
    ground=(60, 135, 85),
    layers=[("hband", (2.0, 6.0, {"deco": "road"}), (75, 80, 88), 0.2, 6.0, 1.5),
            ("rect", (-40.0, 6.0, 40.0, 22.0, {}), (140, 190, 215), 0.35, 8.0, -1.0),
            ("beyond", (22.0,), (120, 95, 60), 0.15, -5.0, 3.0)],
    horizon={"mountains": 0.8, "treeline": 0.4, "treeline_col": (55, 85, 60), "buildings": False},
    plants=[(-18.0, 3.0, "tree", 9.0), (15.0, 2.0, "tree", 8.0), (-24.0, 8.0, "tree", 10.0), (-10.0, 7.0, "bush", 1.2),
            (12.0, 8.0, "bush", 1.4)],
    props=[("boat", 6.0, 19.0, 1.4, 4.0, 0.7, (40, 60, 160), False, 0.0),
           ("umbrella", -4.0, 13.0, 0.1, 0.1, 2.2, (60, 60, 220), False, 0.0),
           ("towel", -3.0, 12.0, 0.9, 1.8, 0.03, (200, 120, 40), False, 0.0),
           ("hut", 18.0, 9.0, 3.0, 3.0, 2.6, (70, 110, 150), True, 0.0)],
    road_y=4.0, area=(-14.0, 14.0, 7.0, 20.0), ambient=22.0, spawn_angle=100))

_add(MapDef(
    "winter", "Winter camp", "The camp site under snow - bright ground, long cold nights, people in dark clothes.",
    ground=(235, 235, 238),
    layers=[("line", (-1.0, 0.5, 9.2, 29.0, 0.75), (190, 195, 200), 0.3, 1.0, 0.5),
            ("hband", (28.8, 35.2, {"deco": "road"}), (95, 95, 100), 0.2, 4.0, 1.0)],
    horizon={"mountains": 1.0, "treeline": 0.55, "treeline_col": (60, 70, 60), "buildings": False, "snow": True},
    plants=[(-12.5, 19.0, "tree", 7.5), (13.5, 24.0, "tree", 9.0), (-24.0, 30.0, "tree", 8.0), (21.0, 13.0, "tree", 6.5),
            (-6.5, 9.5, "bush", 1.3), (7.5, 12.0, "bush", 1.6), (-15.5, 11.0, "bush", 1.8)],
    props=[("tent", 5.0, 8.0, 2.4, 2.0, 1.25, (40, 120, 230), True, 0.0),
           ("caravan", -9.0, 14.0, 5.2, 2.2, 2.5, (225, 225, 220), False, 0.0)],
    road_y=32.0, area=(-14.0, 14.0, 4.0, 22.0), ambient=-4.0))

# =====================================================================================================================
# the big one: a whole valley, about 700 x 700 m - campsite, village, farm, river, lake, forests and a downtown with
# skyscrapers. The camera starts at the campsite; put it anywhere with the 📷 tool.
# =====================================================================================================================
def _valley():
    import math
    rng = random.Random(2026)
    asphalt, water, field1, field2 = (80, 80, 86), (125, 95, 60), (60, 150, 170), (70, 120, 90)
    layers = [
        ("ellipse", (-170.0, 170.0, 75.0, 48.0, {}), (115, 90, 55), 0.15, -5.0, 3.0),                  # lake
        ("line", (-350.0, 250.0, -60.0, 185.0, 7.0, {}), water, 0.15, -5.0, 3.0),                       # river
        ("line", (-60.0, 185.0, 140.0, 150.0, 7.0, {}), water, 0.15, -5.0, 3.0),
        ("line", (140.0, 150.0, 380.0, 175.0, 7.0, {}), water, 0.15, -5.0, 3.0),
        ("rect", (-190.0, -130.0, -60.0, -50.0, {}), field1, 0.6, 3.0, -1.0),                           # fields
        ("rect", (-190.0, -220.0, -60.0, -135.0, {}), field2, 0.6, 3.0, -1.0),
        ("rect", (-55.0, -220.0, 60.0, -135.0, {}), (70, 160, 190), 0.6, 3.0, -1.0),
        ("rect", (150.0, 40.0, 340.0, 320.0, {}), (150, 150, 155), 0.25, 6.0, 2.0),                     # downtown paving
        ("rect", (60.0, -60.0, 115.0, -15.0, {"deco": "parking"}), asphalt, 0.2, 7.0, 2.0),             # car park
        ("ellipse", (2.0, 9.0, 9.0, 6.0, {}), (70, 115, 105), 0.6, 1.0, 0.0),                          # camp pitch
        ("line", (-1.0, 0.5, 9.0, 36.0, 0.75, {}), (150, 172, 185), 0.3, 3.0, 0.5),                     # paths
        ("line", (-90.0, -45.0, -10.0, 36.0, 1.0, {}), (110, 150, 175), 0.4, 3.0, 0.5),
        ("line", (-60.0, 46.0, -150.0, 125.0, 1.0, {}), (110, 150, 175), 0.4, 3.0, 0.5),
        ("hband", (36.0, 43.0, {"deco": "road"}), asphalt, 0.2, 6.0, 1.5),                             # main road
        ("hband", (-150.0, -139.0, {"deco": "road"}), asphalt, 0.2, 7.0, 2.0),                          # highway
        ("vband", (118.0, 125.0, -400.0, 400.0, {"deco": "road"}), asphalt, 0.2, 6.0, 1.5),            # roads front-back
        ("vband", (-212.0, -205.0, -400.0, 400.0, {"deco": "road"}), asphalt, 0.2, 6.0, 1.5),
    ]
    for gy in (110.0, 180.0, 250.0):                                                                    # downtown streets
        layers.append(("rect", (150.0, gy, 340.0, gy + 7.0, {}), asphalt, 0.2, 6.0, 1.5))
    for gx in (205.0, 270.0):
        layers.append(("rect", (gx, 40.0, gx + 7.0, 320.0, {}), asphalt, 0.2, 6.0, 1.5))

    def on_layer(x, y, pad=0.0):
        import numpy as np
        gx, gy = np.array([[x]], float), np.array([[y]], float)
        for sh, pr, *_ in layers:
            if sh in ("rect", "vband", "hband", "line", "ellipse") and layer_mask(sh, pr, gx, gy)[0, 0]:
                return True
        return False

    plants, props = [], []
    # campsite (around the camera's start)
    props += [("tent", 5.0, 8.0, 2.4, 2.0, 1.25, (40, 120, 230), True, 0.0), ("tent", 11.0, 12.5, 2.2, 1.8, 1.2, (60, 170, 70), True, 0.0),
              ("tent", -4.0, 15.0, 2.6, 2.1, 1.3, (200, 80, 60), True, 0.0),
              ("caravan", -9.0, 14.0, 5.2, 2.2, 2.5, (225, 225, 220), False, 0.0), ("caravan", 17.0, 22.0, 5.6, 2.3, 2.6, (210, 220, 230), False, 0.0),
              ("table", 1.2, 4.5, 1.6, 0.8, 0.75, (60, 100, 150), False, 0.0), ("shed", -18.0, 25.0, 6.0, 4.0, 3.2, (90, 120, 150), True, 0.0)]
    plants += [(-6.5, 9.5, "bush", 1.3), (7.5, 12.0, "bush", 1.6), (-12.5, 19.0, "tree", 7.5), (13.5, 24.0, "tree", 9.0),
               (-3.0, 20.0, "bush", 1.1), (21.0, 13.0, "tree", 6.5)]
    # village along the main road
    x = -150.0
    while x < 100.0:
        for side, y in ((1, 52.0), (-1, 25.0)):
            if rng.random() < 0.75 and not (-25 < x < 25 and side < 0):
                w, d, h = rng.uniform(8, 13), rng.uniform(7, 10), rng.uniform(5.5, 8.5)
                col = rng.choice([(170, 190, 205), (150, 160, 200), (190, 200, 210), (140, 170, 190), (200, 190, 170)])
                props.append(("house", x, y + side * d / 2, w, d, h, col, True, 0.0))
                if rng.random() < 0.6:
                    props.append(("car", x + w / 2 + 3.0, y - side * 2.0, 1.8, 4.4, 1.45, rng.choice([(40, 40, 200), (200, 200, 200), (30, 30, 30)]), False, 0.0))
                plants.append((x + rng.uniform(-6, 6), y + side * (d + rng.uniform(3, 8)), "tree", rng.uniform(6, 10)))
        x += rng.uniform(16, 24)
    props.append(("house", -40.0, 66.0, 10.0, 22.0, 14.0, (200, 205, 215), True, 0.0))                # church
    props.append(("tower", -40.0, 80.0, 5.0, 5.0, 32.0, (190, 195, 205), False, 0.0))                # church tower
    # farm
    props += [("house", -120.0, -95.0, 22.0, 14.0, 11.0, (40, 50, 150), True, 0.0),                  # barn
              ("house", -95.0, -100.0, 11.0, 9.0, 7.0, (190, 200, 210), True, 0.0),
              ("block", -135.0, -110.0, 5.0, 5.0, 14.0, (170, 170, 175), False, 0.0),                # silo
              ("woodpile", -105.0, -80.0, 4.0, 1.5, 1.2, (50, 90, 140), False, 0.0)]
    for k in range(10):
        props.append(("fence", -190.0 + k * 13.0, -50.0, 13.0, 0.08, 1.1, (90, 120, 150), False, 0.0))
    # downtown: skyscrapers on the blocks between the streets
    xs = [(150.0, 205.0), (212.0, 270.0), (277.0, 340.0)]
    ys = [(40.0, 110.0), (117.0, 180.0), (187.0, 250.0), (257.0, 320.0)]
    for (x0, x1) in xs:
        for (y0, y1) in ys:
            n = rng.choice([1, 2, 2, 3])
            for k in range(n):
                w = (x1 - x0 - 10) / n
                cx = x0 + 5 + w * (k + 0.5)
                cy = (y0 + y1) / 2 + rng.uniform(-8, 8)
                dist_c = math.hypot(cx - 245, cy - 180)
                h = max(18.0, rng.uniform(60, 140) * (1.2 - dist_c / 200.0))               # tallest in the middle
                col = rng.choice([(150, 140, 120), (170, 165, 160), (120, 110, 95), (190, 185, 175), (140, 150, 165), (110, 120, 135)])
                props.append(("tower" if h > 35 else "block", cx, cy, min(w - 4, rng.uniform(16, 26)), rng.uniform(16, 30), round(h, 1), col, False, 0.0))
    for k in range(12):                                                                              # street trees + lamps
        plants.append((150.0 + k * 16.0, 113.5, "tree", 6.0))
        props.append(("post", 152.0 + k * 16.0, 108.0, 0.15, 0.15, 6.0, (110, 110, 115), False, 0.0))
    # car park + filling station
    for row, y in enumerate((-50.0, -30.0)):
        for k in range(10):
            if rng.random() < 0.7:
                props.append(("car", 64.0 + k * 5.0, y, 1.8, 4.4, 1.45, rng.choice([(40, 40, 200), (200, 200, 200), (30, 30, 30), (60, 140, 60)]), False, 0.0))
    props.append(("block", 90.0, 0.0, 18.0, 10.0, 5.0, (70, 70, 200), False, 0.0))
    # boats on the lake shore, a jetty
    props += [("boat", -110.0, 150.0, 1.5, 4.5, 0.7, (40, 60, 160), False, 0.0), ("boat", -118.0, 160.0, 1.5, 4.0, 0.7, (200, 200, 200), False, 0.0),
              ("wall", -105.0, 170.0, 2.0, 18.0, 0.6, (60, 90, 120), False, 0.0)]
    # forests: west, north beyond the river, south-east
    def forest(n, x0, x1, y0, y1):
        k = 0
        while k < n:
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if not on_layer(x, y):
                plants.append((round(x, 1), round(y, 1), "tree", rng.uniform(7, 15))); k += 1
    forest(260, -360.0, -220.0, -260.0, 120.0)
    forest(200, -300.0, 120.0, 215.0, 330.0)
    forest(120, 140.0, 360.0, -300.0, -160.0)
    # loose trees + bushes everywhere else (not on roads, water, fields, paving)
    k = 0
    while k < 220:
        x, y = rng.uniform(-220, 360), rng.uniform(-300, 210)
        if math.hypot(x, y) < 18 or on_layer(x, y):
            continue
        if any(abs(x - p[1]) < p[3] / 2 + 3 and abs(y - p[2]) < p[4] / 2 + 3 for p in props):
            continue
        plants.append((round(x, 1), round(y, 1), "bush" if rng.random() < 0.45 else "tree", rng.uniform(1.0, 1.9) if rng.random() < 0.45 else rng.uniform(6, 11)))
        k += 1
    return MapDef("valley", "Valley (big, 700 m, skyscrapers)",
                  "A whole valley: campsite, village with church, farm, river, lake, forests, car park and a downtown with "
                  "skyscrapers. Several roads with traffic. Put the camera anywhere with the 📷 tool.",
                  ground=(55, 130, 80), layers=layers,
                  horizon={"mountains": 1.0, "treeline": 0.9, "treeline_col": (45, 75, 50), "buildings": True},
                  plants=plants, props=props, road_y=39.5, area=(-14.0, 14.0, 4.0, 22.0), ambient=16.0,
                  roads=[("h", 39.5), ("h", -144.5), ("v", 121.5), ("v", -208.5)], extent=(-420.0, 440.0, -420.0, 420.0))


def _fill(m, trees, bushes, r0=38.0, r1=190.0, seed=5):
    """Make a map bigger: scatter trees and bushes far out (not on its roads / water / paving, not on props)."""
    import math
    import numpy as np
    rng = random.Random(seed)
    k, tries = 0, 0
    while k < trees + bushes and tries < (trees + bushes) * 30:
        tries += 1
        a = rng.uniform(-math.pi, math.pi); r = r0 + (r1 - r0) * math.sqrt(rng.random())
        x, y = r * math.sin(a), r * math.cos(a)
        gx, gy = np.array([[x]]), np.array([[y]])
        if any(layer_mask(sh, pr, gx, gy)[0, 0] for sh, pr, *_ in m.layers):
            continue
        if any(abs(x - p[1]) < p[3] / 2 + 3 and abs(y - p[2]) < p[4] / 2 + 3 for p in m.props):
            continue
        if k < trees:
            m.plants.append((round(x, 1), round(y, 1), "tree", rng.uniform(6.0, 12.0)))
        else:
            m.plants.append((round(x, 1), round(y, 1), "bush", rng.uniform(0.9, 2.0)))
        k += 1


DEFAULT = "camp"


def get(name):
    m = MAPS.get(name) or MAPS[DEFAULT]
    if isinstance(m, _Lazy):                     # big generated maps are only built when somebody picks them
        m = m.build()
        MAPS[name] = m
    return m


class _Lazy:
    def __init__(self, name, label, desc, builder):
        self.name, self.label, self.desc, self.builder = name, label, desc, builder
        self.custom = False

    def build(self):
        return self.builder()


def layer_mask(shape, params, gx, gy):
    """Boolean mask of a ground layer for world coordinates gx, gy (arrays)."""
    import numpy as np
    p = params
    if shape == "hband":
        return (gy >= p[0]) & (gy < p[1])
    if shape == "vband":
        return (gx >= p[0]) & (gx < p[1]) & (gy >= p[2]) & (gy < p[3])
    if shape == "rect":
        return (gx >= p[0]) & (gx < p[2]) & (gy >= p[1]) & (gy < p[3])
    if shape == "ellipse":
        return ((gx - p[0]) / p[2]) ** 2 + ((gy - p[1]) / p[3]) ** 2 < 1.0
    if shape == "beyond":
        return gy >= p[0]
    if shape == "line":
        ax, ay, bx, by, w = p[:5]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / L2, 0, 1)
        return np.hypot(gx - (ax + t * dx), gy - (ay + t * dy)) < w
    return np.zeros(gx.shape, bool)


def layer_deco(params):
    for p in params:
        if isinstance(p, dict):
            return p.get("deco", "")
    return ""


# ---------------------------------------------------------------------------------------------------------------------
# own maps made in the editor: a built-in map's ground + your own trees, props, camera place (json files)
# ---------------------------------------------------------------------------------------------------------------------
import json as _json
import os as _os
import re as _re

CUSTOM_DIR = {"d": None}


def load_custom(folder):
    CUSTOM_DIR["d"] = folder
    _os.makedirs(folder, exist_ok=True)
    for fn in sorted(_os.listdir(folder)):
        if fn.endswith(".json"):
            try:
                with open(_os.path.join(folder, fn), encoding="utf-8") as f:
                    _register(_json.load(f))
            except Exception as e:
                print(f"[SIM] map {fn} could not be loaded: {e}")


def _register(d):
    b = get(d.get("base", DEFAULT))
    m = MapDef(d["name"], d.get("label", d["name"]), d.get("desc", "Own map (map editor)"), b.ground, b.layers, b.horizon,
               [tuple(x) for x in d.get("plants", [])],
               [(x[0], x[1], x[2], x[3], x[4], x[5], tuple(x[6]), bool(x[7]), float(x[8])) for x in d.get("props", [])],
               d.get("road_y", b.road_y), tuple(d.get("area", b.area)), d.get("ambient", b.ambient),
               d.get("vehicles", b.vehicles), camera=tuple(d["camera"]) if d.get("camera") else None, base=b.name, custom=True,
               roads=b.roads, extent=b.extent)
    MAPS[m.name] = m
    return m


def save_custom(label, base_name, plants, props, camera, area=None):
    """Write an own map and add it to the list. Returns its MapDef."""
    folder = CUSTOM_DIR["d"]
    name = "my_" + (_re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "map")
    b = get(base_name)
    b = get(b.base)
    d = {"name": name, "label": label, "base": b.name,
         "plants": [[round(p.x, 2), round(p.y, 2), p.kind, round(p.size, 2)] for p in plants],
         "props": [[pr.name, round(pr.x, 2), round(pr.y, 2), pr.w, pr.d, pr.h, list(pr.color), pr.ridge, pr.temp_add] for pr in props],
         "camera": [round(camera[0], 2), round(camera[1], 2), round(camera[2], 2), round(camera[3], 1)],
         "area": list(area or b.area)}
    if folder:
        with open(_os.path.join(folder, name + ".json"), "w", encoding="utf-8") as f:
            _json.dump(d, f, indent=1)
    return _register(d)


# the big map and the bigger surroundings of the small maps (needs layer_mask above)
_add(_valley())
for _n, _t, _b in (("camp", 140, 90), ("garden", 70, 40), ("parking", 50, 30), ("forest", 380, 80), ("lake", 70, 40), ("winter", 140, 60)):
    _fill(MAPS[_n], _t, _b, seed=len(_n))


# what the editor can place: name -> (w, d, h, colour, ridge)
PROP_TYPES = {
    "tent": (2.4, 2.0, 1.25, (40, 120, 230), True), "caravan": (5.2, 2.2, 2.5, (225, 225, 220), False),
    "shed": (3.0, 2.5, 2.3, (60, 90, 120), True), "house": (9.0, 7.0, 6.0, (170, 190, 205), True),
    "car": (1.8, 4.4, 1.45, (40, 40, 200), False), "fence": (6.0, 0.08, 1.2, (90, 120, 150), False),
    "table": (1.6, 0.8, 0.75, (60, 100, 150), False), "post": (0.15, 0.15, 5.0, (110, 110, 115), False),
    "umbrella": (0.1, 0.1, 2.2, (60, 60, 220), False), "woodpile": (2.5, 1.0, 1.0, (50, 90, 140), False),
    "boat": (1.4, 4.0, 0.7, (40, 60, 160), False), "wall": (8.0, 0.3, 2.0, (150, 150, 160), False),
    "tower": (22.0, 22.0, 90.0, (150, 140, 120), False), "block": (18.0, 14.0, 15.0, (170, 165, 160), False),
}


def _build_region():
    from simulator.scene.region import build
    return build()


def rebuild_region():
    """The Region map is built from the chosen places (SIM['tiles']): build it again after a change."""
    MAPS["region"] = _Lazy("region", "Region (touching places)", "Every place a 160 m tile, all touching.", _build_region)


rebuild_region()



# ---------------------------------------------------------------------------------------------------------------------
# places of interest: where the camera can be put with one click (📍 selector)
# ---------------------------------------------------------------------------------------------------------------------
def poi(name, x, y, h=1.8, yaw=0.0, pitch=-4.0, desc=""):
    return {"name": name, "x": float(x), "y": float(y), "h": float(h), "yaw": float(yaw), "pitch": float(pitch), "desc": desc}


def pois(m):
    """The places of a map; every map has at least its start."""
    if m.pois:
        return m.pois
    c = m.camera or (0.0, 0.0, None, 0.0)
    return [poi("Start", c[0], c[1], c[2] or 1.8, c[3], -4.0, "Where the camera stands when the map is loaded."),
            poi("Start, high on a pole", c[0], c[1], 6.0, c[3], -12.0, "Same place, camera 6 m high looking down."),
            poi("Look back", c[0], c[1], c[2] or 1.8, c[3] + 180.0, -4.0, "Same place, turned round.")]


MAPS["valley"].props.append(("mountain", 100.0, 2300.0, 2400.0, 2400.0, 650.0, (95, 105, 115), False, 0.0))
MAPS["valley"].pois = [
    poi("Campsite (start)", 0, 0, 1.8, 0, -4, "Tents and caravans, the village road behind them."),
    poi("Village & church", -60, 39.5, 2.5, 90, -3, "On the main road through the village."),
    poi("Downtown", 160, 113.5, 2.5, 90, 4, "Street between the skyscrapers."),
    poi("Farm", -80, -60, 2.5, 220, -4, "Barn, silo and fields."),
    poi("Lake shore", -170, 115, 2.0, 0, -3, "South shore of the lake, boats on the left."),
    poi("Car park", 90, -10, 3.0, 180, -8, "Car park and filling station - car filter test."),
    poi("Front-back road", 121.5, -100, 2.5, 0, -3, "On the road towards downtown."),
]
