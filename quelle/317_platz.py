#@ MoveEye – Teil 317: «Platz einrichten» – ein Assistent nach dem Hinstellen: Rundblick, Vorschläge, Zelt / Zugang / Wertsachen / Ignorieren, Platz-Datensatz (place_items / place_info). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30 (Wunsch Daniel, 29.10.2026): «MoveEye hinstellen → Platz einrichten». One assistant that only DRIVES the parts that
# exist already - it duplicates none of them:
#   * the scan: the head drives its whole pan range in 2-3 tilt rows (the grid of the reference scan 315, its grab
#     function), per direction a photo + ~10 s observation (what moves, what the AI sees) -> suggestions
#   * the photos become the reference of the reference scan (315, day or night) - so «Velo fehlt» in the morning works
#   * the result screen: the panorama of 316 (pano_canvas) with the suggestions; the operator marks
#     «Mein Zelt / Wohnmobil», «Zugang / Weg», «Wertsachen», «Ignorieren»
#   * apply: zones (030; anchored by direction, they stay on their place when the head turns), patrol waypoints (020 / 160),
#     guarded things of the reference scan (315), then the walk test (415)
#   * the result is kept as the «place» record: place_items() / place_info() below - read by other parts (head automation).
# Directions: pan / tilt in percent of the servos like CFG["pan"] / CFG["tilt"] (0 … 100, 50 = middle); a box on the panorama
# is kept as its middle (pan, tilt) and its size (w_pan, h_tilt) in the same percent.
# ----------------------------------------------------------------------------
PLACE_KINDS = ("tent", "access", "public_path", "valuable", "ignore")
PLACE = {"busy": "", "step": 0, "n": 0, "phase": "", "msg": "", "stop": False, "t0": 0.0, "eta": 0.0, "night": False,
         "scan": None, "rec": None, "loaded": False}
_PLACE_LOCK = threading.Lock()


def place_dir(*p):
    return os.path.join(DATA_DIR, "place", *p)


def _place_load():
    """the place record from the data folder (once; later from memory)"""
    if PLACE["loaded"]:
        return PLACE["rec"]
    PLACE["loaded"] = True
    try:
        with open(place_dir("place.json"), encoding="utf-8") as f:
            d = json.load(f)
        PLACE["rec"] = d if isinstance(d, dict) else None
    except (OSError, ValueError):
        PLACE["rec"] = None
    return PLACE["rec"]


def _place_save(rec):
    os.makedirs(place_dir(), exist_ok=True)
    tmp = place_dir("place.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False)
    os.replace(tmp, place_dir("place.json"))
    PLACE["rec"] = rec; PLACE["loaded"] = True


def place_items():
    """the marked things of the place: [{"kind": "tent"|"access"|"public_path"|"valuable"|"ignore", "pan": %, "tilt": %,
    "w_pan": %, "h_tilt": %, "name": str}] - pan / tilt = the middle of the box in servo percent (like CFG["pan"]),
    w_pan / h_tilt = its size in the same percent. [] when the place was never set up. A copy: changing it changes nothing."""
    rec = _place_load() or {}
    out = []
    for it in rec.get("items") or []:
        try:
            out.append({"kind": str(it["kind"]), "pan": float(it["pan"]), "tilt": float(it["tilt"]), "w_pan": float(it["w_pan"]),
                        "h_tilt": float(it["h_tilt"]), "name": str(it.get("name") or "")})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def place_info():
    """a summary of the place for other parts: {"done": bool, "t": time it was set up (or None), "n": number of items,
    "kinds": {kind: count}, "tent": the first tent item or None, "home": {"pan", "tilt"} (where the head should rest:
    towards the tent, else the middle of the scan), "pan_range_deg": what the head can see (servo + lens), "servo_deg",
    "fov": [h, v] degrees, "lat", "lon" (when known), "public_path_report_only": bool, "night_ref": bool,
    "new_position": True when MoveEye stands somewhere else than when the place was set up (GPS ~1 km)}"""
    rec = _place_load() or {}
    items = place_items()
    kinds = {}
    for it in items:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    tent = next((dict(it) for it in items if it["kind"] == "tent"), None)
    home = {"pan": tent["pan"], "tilt": tent["tilt"]} if tent else dict(rec.get("home") or {"pan": 50.0, "tilt": float(CFG.get("refscan_tilt_mid", 50))})
    try:
        hf, vf = cam_fov()
    except Exception:
        hf, vf = 66.0, 41.0
    sd = 2.0 * servo_half("pan")
    return {"done": bool(rec.get("t")), "t": rec.get("t"), "n": len(items), "kinds": kinds, "tent": tent, "home": home,
            "pan_range_deg": round(min(360.0, sd + hf)), "servo_deg": round(sd), "fov": [round(hf, 1), round(vf, 1)],
            "lat": rec.get("lat"), "lon": rec.get("lon"), "public_path_report_only": bool(rec.get("public_report", True)),
            "night_ref": bool(rec.get("night_ref")), "new_position": place_new_position()}


def place_new_position():
    """the device stands somewhere else than when the place was set up (GPS / the location from the phone, ~1 km)"""
    rec = _place_load() or {}
    try:
        lat, lon = float(rec.get("lat")), float(rec.get("lon"))
        if not (lat or lon):
            return False
        return abs(lat - float(CFG["latitude"])) > 0.01 or abs(lon - float(CFG["longitude"])) > 0.01
    except (TypeError, ValueError, KeyError):
        return False
