"""CONTROL protocol: Motion Watch's web page (tab «Simulator» -> «Simulator-Steuerung») remote-controls this simulator.

The simulator describes its own controls (GET /control); Motion Watch draws them without knowing them and sends back
POST /control {"action": "get" | "scenario" | "delete" | "set" | "press", "id": ..., "value": ...}.
Every answer is the same as GET /control, an error is {"ok": false, "error": "..."}.
The labels are German: they show up on Motion Watch's web page (see EIGENEN_SIMULATOR_ANBINDEN.md, section 4)."""
import os

from simulator import NAME
from simulator.config import SIM
from simulator.scene import maps
from simulator.scene import world as W

WEATHER = [["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["storm", "Sturm"], ["fog", "Nebel"]]
VISITS = [("person", "Personen", "Person", 15), ("dog", "Hunde", "Hund", 6), ("cat", "Katzen", "Katze", 6),
          ("bear", "Bären", "Bär", 3), ("horse", "Rehe", "Reh", 4), ("car", "Autos", "Auto", 6)]
FAULTS = [("cam_connected", "Kamera eingesteckt"), ("lens_cover", "Linse zugehalten (Sabotage)"),
          ("thermal_present", "Wärmebild eingesteckt"), ("hot_stone", "Heisser Stein (Wärmebild)"),
          ("campfire", "Lagerfeuer (Wärmebild)")]


def weather():
    """The weather as one word (also sent in the answer to POST /state)."""
    if SIM["fog"] > 0.4:
        return "fog"
    if SIM["rain"] > 0.1:
        return "storm" if SIM["wind"] > 0.65 else "rain"
    if SIM["wind"] > 0.75:
        return "storm"
    return "cloudy" if SIM["clouds"] > 0.6 else "clear"


def _set_weather(v):
    SIM.update(**{"clear": dict(clouds=0.15, rain=0.0, fog=0.0, wind=0.15), "cloudy": dict(clouds=0.85, rain=0.0, fog=0.0),
                  "rain": dict(clouds=0.9, rain=0.7, fog=0.0, wind=0.35), "storm": dict(clouds=1.0, rain=0.8, fog=0.0, wind=0.9),
                  "fog": dict(clouds=0.7, rain=0.0, fog=0.75, wind=0.05)}[v])


def status(eng):
    h = W.sim_hour()
    light = W.ambient_light()
    part = "Tag" if light > 0.5 else ("Nacht" if light < 0.1 else "Dämmerung")
    people = sum(1 for e in eng.world.snapshot() if e.kind == "person")
    poi = eng.current_poi()
    return (f"{int(h):02d}:{int(h * 60) % 60:02d} · {part} · {people} Person{'' if people == 1 else 'en'} unterwegs · "
            f"{eng.world.map.label}" + (f" – {poi['name']}" if poi else "") + (" · lädt …" if eng.map_loading else ""))


def describe(srv):
    eng = srv.eng
    m = eng.world.map
    ps = maps.pois(m)
    cur = eng.current_poi()
    c = [
        {"type": "select", "id": "place", "label": "Kamera-Platz", "group": "Szene",
         "options": [[str(i), p["name"]] for i, p in enumerate(ps)] + ([["-", "(eigener Platz)"]] if cur is None else []),
         "value": str(ps.index(cur)) if cur in ps else "-"},
        {"type": "slider", "id": "hour", "label": "Uhrzeit", "group": "Szene", "min": 0, "max": 24, "step": 0.25, "unit": "h",
         "value": round(W.sim_hour(), 2)},
        {"type": "toggle", "id": "clock", "label": "Echte Uhrzeit", "group": "Szene", "value": SIM["time_mode"] == "clock"},
        {"type": "toggle", "id": "paused", "label": "Pause (alles steht still)", "group": "Szene", "value": bool(SIM["paused"])},
        {"type": "select", "id": "weather", "label": "Wetter", "group": "Wetter", "options": WEATHER, "value": weather()},
        {"type": "slider", "id": "wind", "label": "Wind", "group": "Wetter", "min": 0, "max": 90, "step": 1, "unit": "km/h",
         "value": round(SIM["wind"] * 90.0)},
        {"type": "slider", "id": "ambient_c", "label": "Lufttemperatur", "group": "Wetter", "min": -20, "max": 40, "step": 0.5,
         "unit": "°C", "value": SIM["ambient_c"]},
        {"type": "toggle", "id": "auto", "label": "Besuch von selbst", "group": "Besuch", "value": bool(SIM["auto_spawn"])},
    ]
    for k, many, _one, hi in VISITS:
        c.append({"type": "slider", "id": "want_" + k, "label": many + " unterwegs", "group": "Besuch", "min": 0, "max": hi,
                  "step": 1, "unit": "", "value": SIM.want(k)})
    for k, _many, one, _hi in VISITS:
        c.append({"type": "button", "id": "spawn_" + k, "label": one + " schicken", "group": "Besuch"})
    c.append({"type": "button", "id": "clear", "label": "Alle wegschicken", "group": "Besuch"})
    for k, lab in FAULTS:
        c.append({"type": "toggle", "id": k, "label": lab, "group": "Störungen", "value": bool(SIM[k])})
    c += [{"type": "button", "id": "door_on", "label": "Tür auf", "group": "Sensoren"},
          {"type": "button", "id": "door_off", "label": "Tür zu", "group": "Sensoren"},
          {"type": "button", "id": "gas", "label": "Gas-Alarm", "group": "Sensoren"},
          {"type": "select", "id": "quality", "label": "Bildqualität", "group": "Bild",
           "options": [["1", "tief"], ["2", "mittel"], ["3", "hoch"], ["4", "sehr hoch"]], "value": str(SIM["quality"])}]
    return {"ok": True, "v": 1, "name": NAME,
            "scenarios": [{"id": n, "name": d.label, "kind": "world", "deletable": bool(d.custom)} for n, d in maps.MAPS.items()],
            "scenario": m.name, "status": status(eng), "controls": c, "upload": None}


def handle(srv, d):
    """POST /control. Returns the new description or {"ok": False, "error": ...}."""
    eng = srv.eng
    a, cid, v = d.get("action", "get"), str(d.get("id", "")), d.get("value")
    try:
        if a == "get":
            pass
        elif a == "scenario":
            if cid not in maps.MAPS:
                return {"ok": False, "error": f"unbekanntes Szenario: {cid}"}
            if cid != eng.world.map.name:
                eng.set_map(cid)
        elif a == "delete":
            m = maps.MAPS.get(cid)
            if m is None or not m.custom:
                return {"ok": False, "error": "nur eigene Karten können gelöscht werden"}
            if cid == eng.world.map.name:
                return {"ok": False, "error": "diese Karte ist gerade in Gebrauch - zuerst eine andere wählen"}
            if maps.CUSTOM_DIR["d"]:
                path = os.path.join(maps.CUSTOM_DIR["d"], cid + ".json")
                if os.path.isfile(path):
                    os.remove(path)
            maps.MAPS.pop(cid, None)
        elif a == "set":
            err = _set(eng, cid, v)
            if err:
                return {"ok": False, "error": err}
        elif a == "press":
            err = _press(srv, cid)
            if err:
                return {"ok": False, "error": err}
        else:
            return {"ok": False, "error": f"unbekannte Aktion: {a}"}
    except (TypeError, ValueError) as e:
        return {"ok": False, "error": f"ungültiger Wert: {e}"}
    return describe(srv)


def _set(eng, cid, v):
    if cid == "place":
        ps = maps.pois(eng.world.map)
        if v == "-":
            return None
        i = int(v)
        if not 0 <= i < len(ps):
            return "unbekannter Platz"
        eng.goto_poi(ps[i])
    elif cid == "hour":
        SIM.update(time_mode="manual", hour=max(0.0, min(24.0, float(v))) % 24.0)
    elif cid == "clock":
        SIM["time_mode"] = "clock" if v else "manual"
    elif cid == "paused":
        SIM["paused"] = bool(v)
    elif cid == "weather":
        if v not in [w[0] for w in WEATHER]:
            return "unbekanntes Wetter"
        _set_weather(v)
    elif cid == "wind":
        SIM["wind"] = max(0.0, min(1.0, float(v) / 90.0))
    elif cid == "ambient_c":
        SIM["ambient_c"] = max(-20.0, min(40.0, float(v)))
    elif cid == "auto":
        SIM["auto_spawn"] = bool(v)
    elif cid.startswith("want_") and cid[5:] in [k for k, *_ in VISITS]:
        hi = next(h for k, _m, _o, h in VISITS if k == cid[5:])
        SIM.want(cid[5:], max(0, min(hi, int(float(v)))))
    elif cid in [k for k, _ in FAULTS]:
        SIM[cid] = bool(v)
    elif cid == "quality":
        SIM["quality"] = max(1, min(4, int(v)))
    else:
        return f"unbekannter Regler: {cid}"
    return None


def _press(srv, cid):
    eng = srv.eng
    if cid.startswith("spawn_") and cid[6:] in [k for k, *_ in VISITS]:
        if eng.world.spawn(cid[6:]) is None:
            return "auf dieser Karte gibt es keine Strasse" if cid == "spawn_car" else "konnte nicht geschickt werden"
    elif cid == "clear":
        for e in eng.world.snapshot():
            if not getattr(e, "bg", False):
                eng.world.send_away(e.id)
    elif cid == "door_on":
        srv.add_event("Door", "door", True)
    elif cid == "door_off":
        srv.add_event("Door", "door", False)
    elif cid == "gas":
        srv.add_event("Gas", "gas", None)                  # a pulse: the gas sensor fires once
    else:
        return f"unbekannter Knopf: {cid}"
    return None
