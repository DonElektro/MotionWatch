"""All simulator settings in one place. The control panel changes them live, the engine reads them every tick."""
import threading

DEFAULTS = {
    # ---- camera (main picture) ----
    "cam_width": 1280, "cam_height": 720,
    "cam_fps": 15.0,
    "cam_hfov": 66.0,             # Raspberry Pi Camera Module 3 = 66 degrees
    "cam_noise": 1.0,             # sensor noise factor (more at night through the gain)
    "cam_connected": True,        # unplug -> the program has to reconnect
    "cam_frozen": False,          # picture stops changing (driver hang)
    "lens_cover": False,          # something covers the lens -> sabotage alarm
    "lens_blur": 0.0,             # 0..1 dew / dirt on the lens -> lens check
    "mount_yaw": 0.0,             # the whole head turned on its mount (degrees) -> "camera turned" alarm
    "mount_pitch": -4.0,          # the head looks a little down when the tilt servo is centred
    "mount_height": 1.8,          # metres above the ground
    "cam_x": 0.0, "cam_y": 0.0,   # where the camera head stands on the map (metres; the map editor moves it)
    "shake": 0.0,                 # 0..1 the mount wobbles (wind on a tripod)
    "auto_exposure": True,
    # ---- thermal camera (Waveshare Thermal-90 on the same head) ----
    "thermal_present": True,
    "thermal_hfov": 90.0,
    "thermal_noise": 0.1,         # degrees C (Thermal-90: NETD < 0.1 K)
    "hot_stone": False,           # a sun-warmed stone that never moves (thermal_need_motion test)
    "campfire": False,            # a very hot, flickering, static spot
    # ---- servos ----
    "servo_speed": 120.0,         # degrees per second: real servos under load ~ 60 .. 120 (SG90 unloaded ~ 600)
    "pan_travel": 180.0,          # physical degrees the pan servo turns for 500 .. 2500 us (180 / 270 / 360)
    "tilt_travel": 180.0,         # same for the tilt servo
    "tilt_stop": 75.0,            # the head itself cannot look further up / down than this (bracket hits the base)
    "pan_reversed": False,        # servo mounted / wired the other way round
    "tilt_reversed": False,
    "servo_jitter": 0.0,          # degrees of random jitter (cheap servo / noisy PWM)
    "pan_stuck": False, "tilt_stuck": False,
    "servo_power": True,          # servo supply on (off = servos hold where they are, no reaction)
    # ---- environment ----
    "time_mode": "manual",        # "clock" = the real time, "manual" = the hour slider
    "hour": 13.0,
    "clouds": 0.3,                # 0 clear .. 1 overcast (soft shadows, warmer night sky in thermal)
    "rain": 0.0,                  # 0..1
    "fog": 0.0,                   # 0..1
    "wind": 0.15,                 # 0..1 (0.15 = light breeze, 1 = storm)
    "shadows": True,
    "ambient_c": 16.0,            # air temperature
    "moon": 0.3,                  # 0..1 moonlight at night
    # ---- population ("keep N in the scene") ----
    "auto_spawn": True,
    "want": {"person": 1, "dog": 0, "cat": 0, "bear": 0, "horse": 0, "sheep": 0, "bird": 0,
             "car": 0, "truck": 0, "bicycle": 0, "motorcycle": 0},
    "spawn_gap": 3.0,             # seconds between two spawns of the same kind
    "visit_wait": 1.5,            # seconds a visitor sent to a clicked point stays there before it walks away
    "visit_stay": False,          # visitors stay at the clicked point until removed
    "person_behavior": "mixed",   # mixed / walk / wander / stand / loiter / run / approach / sneak
    "speed_mult": 1.0,
    # ---- PIR sensor at the box (sent to Motion Watch as protocol event "PIR") ----
    "pir_range": 8.0,             # metres
    # ---- simulation ----
    "stream": False,              # «Send to Motion Watch»: announce this simulator in the network (off at start, --stream = on)
    "quality": 3,                # 1 low .. 4 ultra: sharpness of the background picture and of the map views
    # ---- what is drawn (start window / World tab) ----
    "draw_trees": True,           # trees and bushes
    "draw_buildings": True,       # houses, towers, warehouses, caravans, sheds
    "draw_small": True,           # cars, tents, tables, lamp posts, boats ...
    "draw_backdrop": True,        # the big mountain behind the world
    "bg_traffic": True,           # background life: cars keep driving on the roads, now and then a plane overhead
    "tiles": None,                # Region map: which places exist (None = all), see simulator/scene/region.py
    "start_window": True,         # show the start window before the simulation
    "paused": False,
    "time_scale": 1.0,
}


class Settings:
    def __init__(self):
        import copy
        self._d = copy.deepcopy(DEFAULTS)
        self.lock = threading.RLock()

    def __getitem__(self, k):
        return self._d[k]

    def __setitem__(self, k, v):
        with self.lock:
            self._d[k] = v

    def get(self, k, default=None):
        return self._d.get(k, default)

    def update(self, **kw):
        with self.lock:
            self._d.update(kw)

    def want(self, kind, n=None):
        with self.lock:
            if n is not None:
                self._d["want"][kind] = max(0, int(n))
            return self._d["want"].get(kind, 0)

    def snapshot(self):
        import copy
        with self.lock:
            return copy.deepcopy(self._d)


SIM = Settings()
