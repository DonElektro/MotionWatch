"""How loud the simulated world is at the camera, in dB (sent to Motion Watch as sound_db: noise alarm, clap switch test).

About 30 dB = quiet night, 45 = people talking nearby, 60-75 = a car passing, a barking dog, a bear, a thunderstorm.
Every visitor is a sound source with its level at 1 m; it gets 6 dB quieter with every doubling of the distance.
The sources are added like real sound (energies), so two equal sources are 3 dB louder than one."""
import math
import random

from simulator.config import SIM

# level at 1 m (dB), and how often the loud part comes (bark, growl): (quiet level, loud level, share of time loud)
SOURCES = {
    "person":     (50.0, 62.0, 0.25),     # footsteps / talking now and then
    "dog":        (52.0, 88.0, 0.20),     # barks
    "cat":        (35.0, 60.0, 0.05),
    "bear":       (60.0, 85.0, 0.15),     # growls
    "horse":      (48.0, 70.0, 0.10),     # deer / horse: steps, a call now and then
    "sheep":      (45.0, 72.0, 0.15),
    "bird":       (50.0, 70.0, 0.30),
    "car":        (82.0, 82.0, 0.0),
    "truck":      (90.0, 90.0, 0.0),
    "bicycle":    (55.0, 55.0, 0.0),
    "motorcycle": (92.0, 92.0, 0.0),
    "plane":      (130.0, 130.0, 0.0),    # far up: 150-400 m -> about 75-85 dB on the ground
}
_loud = {}                                 # entity id -> loud until (sim time)


def _db_sum(levels):
    return 10.0 * math.log10(sum(10.0 ** (lv / 10.0) for lv in levels)) if levels else 0.0


def level_db(world, t):
    """The sound level at the camera now. world: the World, t: a time in seconds (for the barks)."""
    levels = [26.0 + random.uniform(-0.5, 0.5)]                          # background: a quiet night in the country
    wind = float(SIM["wind"])
    if wind > 0.05:
        levels.append(30.0 + 40.0 * wind)                                 # leaves and wind noise: storm about 70 dB
    rain = float(SIM["rain"])
    if rain > 0.05:
        levels.append(40.0 + 25.0 * rain)                                 # light rain 45 dB, downpour about 65 dB
        if rain > 0.6 and wind > 0.6 and random.random() < 0.004:         # thunderstorm: now and then a thunderclap
            _loud["thunder"] = t + random.uniform(1.0, 3.0)
    if _loud.get("thunder", 0.0) > t:
        levels.append(78.0 + random.uniform(-3.0, 3.0))
    for e in world.snapshot():
        src = SOURCES.get(e.kind)
        if src is None:
            continue
        quiet, loud, share = src
        if share > 0.0:
            if _loud.get(e.id, 0.0) <= t and random.random() < share * 0.05:   # about 10 checks per second
                _loud[e.id] = t + random.uniform(0.4, 1.5)
            lv = loud if _loud.get(e.id, 0.0) > t else quiet
        else:
            lv = quiet if e.moving() or e.kind == "plane" else quiet - 30.0      # a parked car makes no noise
        d = max(1.0, math.hypot(e.dist(), getattr(e, "z", 0.0)))
        lv -= 20.0 * math.log10(d) + 0.005 * d                            # distance (6 dB per doubling) + a little air
        if lv > 0.0:
            levels.append(lv)
    if len(_loud) > 200:                                                  # forget visitors that are gone
        for k in [k for k, v in _loud.items() if v < t]:
            _loud.pop(k, None)
    return round(min(120.0, _db_sum(levels)), 1)
