#@ MoveEye – Teil 318: «Blickwinkel der Kamera» pro Kamera (Hauptkamera und jede Zusatzkamera): Liste der Kamera-Module, eigener Wert, automatisch erkannt (picamera2 / Simulator). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30 (Wunsch Daniel, 29.10.2026 - a second, wide-angle camera comes later: Pi 5 CAM1 -> «pi:1», Camera Module 3 Wide NoIR)
#   CFG["cam_fov"] = {spec: {"model": "auto"|"m3"|"m3wide"|"m2"|"own", "deg": horizontal degrees for "own"}}
#   CFG["cam_head"] = {spec: True} - an extra camera that sits on the head (turns with it) - «Platz einrichten» may use it
#   cam_fov_h(spec=None) -> horizontal degrees (main camera when None) - other parts call it via globals().get("cam_fov_h")
#   cam_fov_hv(spec=None) -> (horizontal, vertical, where it comes from: "sim" | "auto" | "model" | "own" | "default")
# In the simulator the field of view comes from its /info (fov_h / fov_v of that camera). cam_fov() (290) asks here for the
# main camera, so the distance (415), the sleeping place / zones (030) and the panorama (316 / 317) all use the same value.
# ----------------------------------------------------------------------------
for _k, _v in {"cam_fov": {}, "cam_head": {}}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

CAM_FOV_MODELS = (                                   # (id, name, horizontal °, vertical ° at 16:9, picamera2 sensor names)
    ("m3", "Camera Module 3", 66.0, 41.0, ("imx708", "imx708_noir")),
    ("m3wide", "Camera Module 3 Wide", 102.0, 67.0, ("imx708_wide", "imx708_wide_noir")),
    ("m2", "Camera Module 2", 62.2, 48.8, ("imx219", "imx219_noir")),
)
CAM_FOV_CHOICES = [("auto", "Automatic")] + [(m[0], f"{m[1]} ({m[2]:.0f}°)") for m in CAM_FOV_MODELS] + [("own", "HQ / other camera: own value")]
_PICAM_INFO = {"t": 0.0, "list": None}


def _picam_models():
    """the sensor names of the Raspberry Pi cameras (picamera2 global_camera_info, asked once a minute) - [] without picamera2"""
    if _PICAM_INFO["list"] is not None and time.time() - _PICAM_INFO["t"] < 60:
        return _PICAM_INFO["list"]
    out = []
    try:
        from picamera2 import Picamera2
        out = [str(i.get("Model") or "").lower() for i in Picamera2.global_camera_info()]
    except Exception:
        out = []
    _PICAM_INFO.update(t=time.time(), list=out)
    return out


def cam_fov_detect(spec):
    """the model id ("m3", "m3wide", "m2") of a Pi camera from its sensor name, or "" """
    m = re.fullmatch(r"pi:(\d+)", str(spec or ""))
    if not m:
        return ""
    lst = _picam_models()
    n = int(m.group(1))
    name = lst[n] if n < len(lst) else ""
    for mid, _nm, _h, _v, sensors in CAM_FOV_MODELS:
        if name in sensors:
            return mid
    return ""


def _vfov_from_h(h, aspect=16.0 / 9.0):
    return math.degrees(2 * math.atan(math.tan(math.radians(h) / 2.0) / aspect))


def cam_fov_hv(spec=None):
    """(horizontal °, vertical °, source) of a camera: spec None = the main camera (CFG["source"]), "thermal" = the thermal camera"""
    main = spec is None or str(spec) == str(CFG.get("source"))
    spec = str(CFG.get("source") if spec is None else spec)
    if spec in ("thermal", "sim:thermal"):
        try:
            th = (SIM.get("info") or {}).get("thermal") if CFG.get("sim_on") else None
            if th and th.get("fov_h"):
                return float(th["fov_h"]), float(th.get("fov_v") or _vfov_from_h(float(th["fov_h"]), 4 / 3.0)), "sim"
        except (TypeError, ValueError, AttributeError):
            pass
        return 90.0, 67.0, "default"                     # Waveshare Thermal-90
    if spec.startswith("sim:") and CFG.get("sim_on"):
        try:
            info = SIM.get("info") or {}
            cam = next((c for c in info.get("cameras") or [] if str(c.get("id")) == spec[4:]), None)
            if cam and cam.get("fov_h"):
                hf = float(cam["fov_h"])
                vf = float(cam.get("fov_v") or 0) or math.degrees(2 * math.atan(math.tan(math.radians(hf) / 2) * float(cam.get("h") or 9) / float(cam.get("w") or 16)))
                return hf, vf, "sim"
        except (TypeError, ValueError, KeyError, AttributeError):
            pass
    st = (CFG.get("cam_fov") or {}).get(spec) if isinstance(CFG.get("cam_fov"), dict) else None
    st = st if isinstance(st, dict) else {}
    model = st.get("model") or "auto"
    if model == "own":
        try:
            h = max(20.0, min(200.0, float(st.get("deg"))))
            return h, min(160.0, _vfov_from_h(h)), "own"
        except (TypeError, ValueError):
            model = "auto"
    src = "model"
    if model == "auto":
        model = cam_fov_detect(spec); src = "auto"
    for mid, _nm, h, v, _s in CAM_FOV_MODELS:
        if mid == model:
            return h, v, src
    if main:                                             # as before 2.98.30: Camera Module 3 and the setting cam_vfov
        return float(CFG.get("cam_hfov") or 66.0), float(CFG.get("cam_vfov") or 41.0), "default"
    return 66.0, 41.0, "default"


def cam_fov_h(spec=None):
    """horizontal field of view in degrees (main camera when spec is None)"""
    return cam_fov_hv(spec)[0]


def cam_on_head(spec):
    """does this camera turn with the head? The main camera: yes. An extra camera: the simulator knows, else the setting."""
    spec = str(spec or "")
    if not spec or spec == str(CFG.get("source")):
        return True
    if spec.startswith("sim:") and CFG.get("sim_on"):
        cam = next((c for c in (SIM.get("info") or {}).get("cameras") or [] if str(c.get("id")) == spec[4:]), None)
        if cam is not None and "on_head" in cam and not (CFG.get("cam_head") or {}).get(spec):
            return bool(cam.get("on_head"))
    return bool((CFG.get("cam_head") or {}).get(spec))


def cam_fov_set(spec, model, deg=None, head=None):
    spec = str(spec or "")
    if not re.fullmatch(r"[A-Za-z0-9:_./\-@]{1,200}", spec):
        return False, "invalid value"
    if model not in [c[0] for c in CAM_FOV_CHOICES]:
        return False, "invalid value"
    d = dict(CFG.get("cam_fov") or {})
    e = {"model": model}
    if model == "own":
        try:
            e["deg"] = round(max(20.0, min(200.0, float(deg))), 1)
        except (TypeError, ValueError):
            return False, "invalid value"
    d[spec] = e
    CFG["cam_fov"] = dict(list(d.items())[-12:])
    if head is not None:
        hd = dict(CFG.get("cam_head") or {})
        hd[spec] = bool(head)
        CFG["cam_head"] = dict(list(hd.items())[-12:])
    save_settings()
    log_event("sys", f"Field of view of {spec}: {model}" + (f" {e.get('deg')}°" if model == "own" else ""))
    return True, ""


def cam_fov_list(lang=None):
    """all cameras with their field of view (for the web page and the window)"""
    out = []
    specs = [str(CFG.get("source") or "")] + [str(s) for s in (CFG.get("extra_cams") or []) if s]
    for i, s in enumerate(dict.fromkeys(specs)):
        h, v, src = cam_fov_hv(s)
        st = (CFG.get("cam_fov") or {}).get(s) or {}
        det = cam_fov_detect(s)
        out.append({"spec": s, "main": i == 0, "label": source_label(s) if s else s, "h": round(h, 1), "v": round(v, 1), "src": src,
                    "model": st.get("model") or "auto", "deg": st.get("deg"), "detected": det,
                    "detected_name": next((m[1] for m in CAM_FOV_MODELS if m[0] == det), ""), "head": cam_on_head(s)})
    return {"cams": out, "choices": [[c[0], tr(c[1], lang)] for c in CAM_FOV_CHOICES]}


def cam_wide_spec():
    """an extra camera that sits on the head and sees clearly more than the main camera (for the panorama), or "" """
    h0 = cam_fov_h(None)
    best, bh = "", h0 + 15.0
    for c in list(CAMS):
        if c.status == "connected" and cam_on_head(c.spec):
            h = cam_fov_h(c.spec)
            if h > bh:
                best, bh = c.spec, h
    return best


def cam_fov_selftest():
    sv = (dict(CFG.get("cam_fov") or {}), CFG.get("source"), CFG.get("sim_on"))
    try:
        CFG["sim_on"] = False; CFG["source"] = "pi:0"
        CFG["cam_fov"] = {"pi:0": {"model": "m3wide"}, "usb:1": {"model": "own", "deg": 120}}
        assert abs(cam_fov_h() - 102.0) < 0.1 and abs(cam_fov()[0] - 102.0) < 0.1
        h, v, src = cam_fov_hv("usb:1")
        assert src == "own" and abs(h - 120) < 0.1 and 70 < v < 90, (h, v)
        assert cam_fov_hv("usb:7")[0] == 66.0
        _PICAM_INFO.update(t=time.time(), list=["imx708_wide_noir", "imx219"])
        assert cam_fov_detect("pi:0") == "m3wide" and cam_fov_detect("pi:1") == "m2" and cam_fov_detect("usb:0") == ""
        CFG["cam_fov"] = {}
        assert abs(cam_fov_h("pi:1") - 62.2) < 0.1
        return "own value, models, picamera2 names"
    finally:
        CFG["cam_fov"], CFG["source"], CFG["sim_on"] = sv
        _PICAM_INFO.update(t=0.0, list=None)



def _extra_cams_boot():
    """2.98.30: the extra cameras of the settings were only started when one was added or the simulation switched -
    after a restart they stayed off (found while testing «Panorama mit Weitwinkel»). Start them once with the camera loop."""
    for _ in range(600):
        time.sleep(1.0)
        if WATCH_REF.get("w") is not None:
            time.sleep(3.0)
            try:
                main_ = {CFG.get("source"), STATE.get("source_id")}       # 2.98.31: the main camera is never also an extra camera
                if any(x in main_ for x in CFG.get("extra_cams", [])):
                    CFG["extra_cams"] = [x for x in CFG["extra_cams"] if x not in main_]; save_settings()
                    log_event("sys", "Extra cameras: the main camera was also in the list - removed there")
                if CFG.get("extra_cams") and not CAMS and not toolmode_on():
                    cams_apply()
            except Exception as e:
                print(f"extra cameras: {e}")
            return


threading.Thread(target=_extra_cams_boot, daemon=True, name="extracams-boot").start()
