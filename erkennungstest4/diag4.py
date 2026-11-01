"""Erkennung 4 - Nebenfunde nachstellen (Scheinwerfer, Wind im leeren Bild). Aufruf: VARIANT=... python3 diag4.py
  Stellplatz Nacht: 2 Autos mit Scheinwerfern direkt auf die Kamera zu (leer); Garten Nacht+Regen: Auto 20 m quer mit
  Scheinwerfern; Wildbeobachtung Nacht: Auto 20 m quer mit Scheinwerfern; Camping Dämmerung: leer, Wind 55;
  Garten Tag: leer, Wind 12."""
import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver as D
import extra as X
from lib import *

done = D.done_keys()


def car_lights():
    ctl(action="set", id="cond_headlights", value=True)
    return ctl(action="spawn_at", kind="car", **dict(zip(("from", "to"), D.cross(20.0))))


def toward2():
    r = ctl(action="fahrzeuge", do="toward")
    threading.Timer(22.0, lambda: ctl(action="fahrzeuge", do="toward")).start()
    return r


X.NAMES.update({"nacht_blend": "Nacht, Scheinwerfer direkt in die Kamera", "nachtregen": "Nacht, Regen, Infrarot",
                "nacht": "Nacht, klar, Infrarot", "daemmerung": "Dämmerung, klar", "tag": "Tag, klar"})
for place, ck, ev, want, secs, act, info, wind in (
        ("stellplatz", "nacht_blend", "leer", "none", 45.0, toward2, "2 Autos mit Scheinwerfern auf die Kamera zu, niemand da", 12),
        ("garten", "nachtregen", "fahrzeug", "vehicle", 16.0, car_lights, "Auto 20 m + Scheinwerfer", 12),
        ("wild", "nacht", "fahrzeug", "vehicle", 16.0, car_lights, "Auto 20 m + Scheinwerfer", 12),
        ("camping", "daemmerung", "leer", "none", 45.0, None, "nichts, Wind 55 km/h", 55),
        ("garten", "tag", "leer", "none", 45.0, None, "nichts, Wind 12 km/h", 12)):
    if "%s|%s|%s" % (place, ck, ev) in done:
        continue
    D.CUR_KEY[0] = "%s|%s|%s" % (place, ck, ev)
    D.wait_ok(D.LOADMAX, D.LOADWAIT)
    D.goto_place(place)
    D.set_cond("nacht" if ck == "nacht_blend" else ck)
    time.sleep(15)
    X.case(place, ck, ev, want, secs, act, info, done, wind=wind)
    ctl(action="set", id="cond_headlights", value=False)
log("diag fertig")
