#@ MoveEye – Teil 163: Weitwinkel-Kamera (Camera Module 3 Wide NoIR) als Übersicht – Montage aus dem Simulator (/info cameras[1]), «Übersicht lenkt den Kopf» von selbst, Kopf-Montage (Richtung = Kopf + Versatz, Eigenbewegung ausblenden), zweites IR-Licht breit auf PCA9685 Kanal 4. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Plan Daniel 30.10.2026 (docs/Gehaeuse_Variante2_Weitwinkel.md, «Simulator-Einbindung der Weitwinkel-Kamera»):
#  - The simulator (3D-4.17, weitwinkel.gd) has ONE wide camera (sim:1, 102° x 67°) with a mount: scene (mast, as before),
#    base (lower part of the device, fixed), head_front / head_rear (turns with the pan, rear = yaw offset 180°).
#    /info cameras[1] and the reply to every POST /state («wide») tell the mount, tilt_deg, yaw_offset, pan_follow,
#    tilt_follow, fov_h / fov_v, on_head.
#  - On the device (base / head_*): «Übersicht lenkt den Kopf» (162: kopf_ov) is set to sim:1 by itself - only when the
#    mount changes (or at the first contact), so a choice by hand stays. Mast = not part of the device: not by itself
#    (as before); when it was set by itself, it is cleared again.
#  - Head mounts: the direction of a box = where the head REALLY is (the simulated head, else servo_pos) + yaw offset +
#    the angle in the picture (instead of the fixed kopf_ov_offset). While the head turns (and a short settle time after),
#    the extra camera on the head ignores its movement (the same signals the main camera uses: SRV moving, SERVO_MOVE,
#    a change of the position) - 440 asks weit_cam_turning().
#  - Rear mount: movement behind -> the head turns there (162 _kopf_ov_tick, same rank as «turn to the alarm»), then the
#    AI of the main camera checks.
#  - P9 (31.10.2026, simulator: weitwinkel.gd): mount «case» = built into case v5.2 (front wall above the PIR, fixed, 12°
#    down, the head turns above it) - a device mount like «base"; «none» = not built in, blind cover: no picture (the
#    simulator answers /cam/1 with 404), not the overview; 591 says «not installed» instead of «simulator not reachable».
#    The picture is an equidistant fisheye (angle linear in the picture) - kopf_ov_deg's (cx - 0.5) * fov is exact for it.
#  - Second infrared LED 120° on PCA9685 channel 4 («IR-Licht breit (Kanal 4)»): on / off together with the infrared
#    light (070 lights_tick); the simulator gets lights.ir_wide.
# ----------------------------------------------------------------------------
for _k, _v in {"light_ir_wide": False, "kopf_ov_simauto": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
WEIT = {"mount": None, "seen": False, "hd": None, "hd_t": 0.0, "pt": None, "pt_t": 0.0}
WEIT_DEVICE_MOUNTS = ("case", "base", "head_front", "head_rear")   # P9: + «case» (case v5.2)
WEIT_IR_CH = 4                                            # PCA9685 channel of the wide infrared LED (white 2, IR 3 by convention)


# ---- what the simulator says about its wide camera -------------------------------------------------------------------
def weit_sim_cam():
    """cameras[1] of the simulator (dict) or None"""
    if not CFG.get("sim_on"):
        return None
    try:
        return next((c for c in (SIM.get("info") or {}).get("cameras") or [] if str(c.get("id")) == "1"), None)
    except (AttributeError, TypeError):
        return None


def weit_mount():
    c = weit_sim_cam()
    return str(c.get("mount") or "scene") if c else ""


def weit_on_device():
    return weit_mount() in WEIT_DEVICE_MOUNTS


def weit_missing():
    """P9: the simulator says its wide camera is not built in (blind cover)"""
    c = weit_sim_cam()
    return bool(c) and (str(c.get("mount") or "") == "none" or c.get("installed") is False)


def weit_from_sim(w):
    """350: the reply to POST /state carries «wide» - a new mount is known at once (no new /info needed)"""
    if not isinstance(w, dict) or not CFG.get("sim_on"):
        return
    c = weit_sim_cam()
    if c is not None:
        for k in ("mount", "tilt_deg", "yaw_offset", "pan_follow", "tilt_follow", "on_head", "fov_h", "fov_v", "pan_limit", "installed"):
            if k in w:
                c[k] = w[k]
    weit_auto()


def weit_auto():
    """«Übersicht lenkt den Kopf» by itself when the wide camera is on the device - only at a change of the mount"""
    m = weit_mount()
    if not m or m == WEIT["mount"]:
        return
    first = WEIT["mount"] is None
    WEIT["mount"] = m
    cur = str(CFG.get("kopf_ov") or "")
    changed = False
    if m in WEIT_DEVICE_MOUNTS:
        if cur in ("", "sim:1") and "sim:1" in (CFG.get("extra_cams") or []):
            if cur != "sim:1" or not CFG.get("kopf_ov_simauto"):
                log_event("servo", f"Simulator: the wide camera sits on the device ({m}) - it steers the head as overview")
            CFG["kopf_ov"] = "sim:1"; CFG["kopf_ov_simauto"] = True; changed = True
    elif cur == "sim:1" and CFG.get("kopf_ov_simauto"):
        CFG["kopf_ov"] = ""; CFG["kopf_ov_simauto"] = False; changed = True
        if not first:
            log_event("servo", "Simulator: the wide camera is not built in (blind cover) - no overview of the head" if m == "none"
                      else "Simulator: the wide camera is on the mast again - no longer the overview of the head")
    if changed:
        save_settings()


def weit_ov_geom():
    """(yaw_offset, on_head) when the overview is the simulator's wide camera on the device, else None"""
    if str(CFG.get("kopf_ov") or "") != "sim:1":
        return None
    c = weit_sim_cam()
    if not c or str(c.get("mount") or "scene") not in WEIT_DEVICE_MOUNTS:
        return None
    try:
        return float(c.get("yaw_offset") or 0.0), bool(c.get("on_head"))
    except (TypeError, ValueError):
        return None


def weit_head_deg():
    """where the head really looks (degrees, + = right): the simulated head, else the planned position"""
    h = SIM.get("head") if CFG.get("sim_on") else None
    if isinstance(h, list) and h:
        try:
            return float(h[0])
        except (TypeError, ValueError):
            pass
    return servo_pos_deg()[0]


_kopf_ov_deg_162 = kopf_ov_deg


def kopf_ov_deg(cx):                                      # + 163: the wide camera on the device (base: fixed, head: turns)
    g = weit_ov_geom()
    if g is None:
        return _kopf_ov_deg_162(cx)
    d = g[0] + (float(cx) - 0.5) * kopf_ov_fov() + (weit_head_deg() if g[1] else 0.0)
    return (d + 180.0) % 360.0 - 180.0


# ---- the camera on the head moves itself: no movement while it turns ------------------------------------------------
def weit_cam_turning(spec):
    """440: True while an extra camera that sits on the head turns (and a short settle time after) - the whole picture
    «moves» then. Same signals as the main camera (410 foreground): SRV moving, SERVO_MOVE, a change of the position;
    in the simulation also the simulated head (it follows a moment later)."""
    try:
        if not cam_on_head(spec):
            return False
    except NameError:
        return False
    now = time.time()
    settle = 1.2 if CFG.get("sim_on") else 0.8
    pt = (round(float(CFG["pan"]), 1), round(float(CFG["tilt"]), 1))
    if pt != WEIT["pt"]:
        WEIT["pt"] = pt; WEIT["pt_t"] = now
    h = SIM.get("head") if CFG.get("sim_on") else None
    if isinstance(h, list) and len(h) >= 2:
        hd = (round(float(h[0]), 1), round(float(h[1]), 1))
        if hd != WEIT["hd"]:
            WEIT["hd"] = hd; WEIT["hd_t"] = now
    moving = bool(SRV.get("moving")) or now - float(SERVO_MOVE.get("t") or 0.0) < settle
    return moving or now - WEIT["pt_t"] < settle or now - WEIT["hd_t"] < settle


# ---- the wide infrared light on channel 4 -----------------------------------------------------------------------------
def weit_ir_ch_free():
    """channel 4 is not taken by the white / infrared light or a servo"""
    used = {str(CFG.get("light_white_out") or ""), str(CFG.get("light_ir_out") or "")}
    return f"pca:{WEIT_IR_CH}" not in used and WEIT_IR_CH not in (int(CFG.get("pca_pan_ch", 0)), int(CFG.get("pca_tilt_ch", 1)))


_lights_tick_070 = lights_tick


def lights_tick():                                        # + 163: the wide infrared light follows the infrared light
    prev = bool((STATE.get("lights") or {}).get("ir_wide"))
    res = _lights_tick_070()
    on = bool(res.get("ir")) and bool(CFG.get("light_ir_wide"))
    if on != prev:
        log_event("relay", f"Wide infrared light {'ON' if on else 'OFF'}")
    res["ir_wide"] = on
    STATE["lights"] = dict(STATE.get("lights") or {}, ir_wide=on)
    return res


_hw_lights_070 = Hardware._lights


def _weit_hw_lights(self, wanted):
    _hw_lights_070(self, wanted)
    if self.pca is None:
        return
    on = bool((STATE.get("lights") or {}).get("ir_wide")) and weit_ir_ch_free()
    if getattr(self, "_weit_ir", None) != on:
        try:
            self.pca.switch(WEIT_IR_CH, on); self._weit_ir = on
        except Exception as e:
            log_event("servo", f"Light error (channel {WEIT_IR_CH}): {e}")


# wraps: Hardware._lights
Hardware._lights = _weit_hw_lights
_light_out_pairs_070 = light_out_pairs


def light_out_pairs(name):                                # + 163: channel 4 belongs to the wide infrared light when it is on
    p = _light_out_pairs_070(name)
    if CFG.get("light_ir_wide"):
        p = [x for x in p if x[0] != f"pca:{WEIT_IR_CH}" or x[0] == CFG.get(f"light_{name}_out")]
    return p


def weit_state(lang=None):
    """for pages: the wide camera of the simulator (mount, overview, its extra camera number)"""
    c = weit_sim_cam()
    if not c or "mount" not in c:
        return None
    n = next((x.idx for x in CAMS if str(x.spec) == "sim:1"), None)
    return {"mount": str(c.get("mount")), "on_head": bool(c.get("on_head")), "tilt": c.get("tilt_deg"), "n": n, "missing": weit_missing(),
            "ov": str(CFG.get("kopf_ov") or "") == "sim:1", "ov_on": bool(CFG.get("kopf_ov_on")), "fov": [c.get("fov_h"), c.get("fov_v")]}
