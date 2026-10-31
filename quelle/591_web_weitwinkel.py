#@ MoveEye – Teil 591: Weitwinkel-Kamera des Simulators auf den Seiten (Kachel in der Simulator-Zentrale und in Sim-Kompakt, Bild antippen = gross, Montage wählen), Zustand an den Simulator (IR-Licht breit), Selbsttest von Teil 163. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Plan Daniel 30.10.2026: the wide picture as a tile on /sim (Simulator-Zentrale, 139) and in Sim-Kompakt (549). No new
# stream: the picture is the extra camera sim:1 that MoveEye already fetches (440), shown through /cam_feed/<n> only while
# its sheet is open (the stream stops when the sheet closes). The tile sheet: the picture (tap = big, tap again / Esc =
# back), the four mounts (simulator control wide_mount), whether it steers the head as overview (163).
# Here (not in 163) because sim_state (290), sim_hub (139), SELFTEST_EXTRA (395) and simhub_head come before this part.
# Translations: part 598.
# ----------------------------------------------------------------------------
# «IR-Licht breit (Kanal 4)» next to the infrared light in «Licht» (web and window read the same list)
_wi = max([i for i, t_ in enumerate(TOGGLES) if t_[0] == "Lights"] or [len(TOGGLES) - 1])
TOGGLES.insert(_wi + 1, ("Lights", "light_ir_wide", "Wide infrared light (channel 4): second IR LED 120° on PCA9685 channel 4, on / off with the infrared light"))
_sim_state_290 = sim_state


def sim_state():                                          # + 163: the simulator switches its wide infrared light
    d = _sim_state_290()
    try:
        d["lights"]["ir_wide"] = bool((STATE.get("lights") or {}).get("ir_wide"))
    except (KeyError, TypeError):
        pass
    return d


_sim_hub_139 = sim_hub


def sim_hub(force=False):                                 # + 591: the wide camera for its tile
    d = _sim_hub_139(force)
    if d.get("on"):
        d = dict(d, wide=weit_state())
    return d


_sim_hub_do_139 = sim_hub_do


def sim_hub_do(a, v=None):                                # + 591: «wide_mount» = the mount of the wide camera
    if a != "wide_mount":
        return _sim_hub_do_139(a, v)
    m = str(v or "")
    if m not in ("scene", "none") + WEIT_DEVICE_MOUNTS:
        return False, "invalid value"
    try:
        r = sim_control({"action": "set", "id": "wide_mount", "value": m})
    except Exception:
        return False, "simulator not reachable"
    if r.get("ok", True):
        c = weit_sim_cam()
        if c is not None:                                  # the next state reply says it too - but the tile shows it at once
            c.update(mount=m, on_head=m.startswith("head_"), yaw_offset=180.0 if m == "head_rear" else 0.0, installed=m != "none")
            weit_auto()
    _SIMHUB["t"] = 0.0
    return bool(r.get("ok", True)), str(r.get("error") or "")


_open_source_210 = open_source


def open_source(spec, thermal=False):                     # + 591 (P9): blind cover - say so instead of «not reachable»
    if not thermal and str(spec) == "sim:1" and weit_missing():
        return None, spec, source_label(spec), "wide camera not installed (blind cover)"
    return _open_source_210(spec, thermal)


_source_label_200 = source_label


def source_label(spec):                                   # + 591: the wide camera of the simulator has its own name
    if str(spec) == "sim:1" and weit_sim_cam() and "mount" in (weit_sim_cam() or {}):
        return "Simulator wide camera"
    return _source_label_200(spec)


WIDE_JS = r"""
<style>
.mwwide{position:relative;width:100%;max-width:640px;border-radius:12px;overflow:hidden;background:#000;aspect-ratio:16/9;cursor:zoom-in}
.mwwide img{display:block;width:100%;height:100%;object-fit:contain}
.mwwide .mwwl{position:absolute;left:6px;bottom:6px;font:600 11px/1.3 system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.55);padding:2px 7px;border-radius:8px}
.mwwide .mwww{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#9aa7b8;font-size:13px}
.mwwide.big{position:fixed;inset:0;z-index:9990;border-radius:0;aspect-ratio:auto;max-width:none;cursor:zoom-out}
.shsheet .mwwide{flex:1 1 100%}
.mwwnote{flex:1 1 100%;font-size:12px}
</style>
<script>
(function () {
  const DE = /*WDE*/{};
  const M = [["case", "In the case (v5.2)"], ["scene", "Mast (scene)"], ["base", "Base front, fixed"], ["head_front", "Head front"], ["head_rear", "Head rear"],
             ["none", "Not installed (blind cover)"]];
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) { return "de"; } };
  let merged = false;
  const merge = () => { if (merged) return; try { if (typeof I18N !== "undefined" && I18N.de) { for (const k in DE) if (!(k in I18N.de)) I18N.de[k] = DE[k]; merged = true; } } catch (e) {} };
  const tt = k => { merge(); try { if (typeof t === "function" && t(k) !== k) return t(k); } catch (e) {} return L() === "en" ? k : (DE[k] || k); };
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  let BOX = null, IMG = null, LAB = null, WAIT = null, N = null;
  function pic() {
    if (!BOX) {
      BOX = E("div", "mwwide"); IMG = E("img"); IMG.alt = ""; LAB = E("span", "mwwl"); WAIT = E("div", "mwww", "…");
      IMG.addEventListener("load", () => { WAIT.hidden = true; });
      BOX.append(WAIT, IMG, LAB);
      BOX.onclick = e => { e.stopPropagation(); BOX.classList.toggle("big"); };
      addEventListener("keydown", e => { if (e.key === "Escape" && BOX.classList.contains("big")) BOX.classList.remove("big"); });
    }
    return BOX;
  }
  let CUR = "";
  function feed() {                                     // the stream only while the picture is on the page
    if (!IMG) return;
    const vis = document.contains(BOX) && !document.hidden && (BOX.offsetParent !== null || BOX.classList.contains("big"));
    const src = N != null && vis ? "/cam_feed/" + N : "";
    if (src === CUR) return;
    CUR = src;
    if (src) { WAIT.hidden = false; IMG.src = src; } else IMG.src = "data:,";      // (data: stops the running stream)
  }
  setInterval(feed, 1000);
  document.addEventListener("visibilitychange", feed);
  const name = m => tt((M.find(x => x[0] === m) || [0, m])[1]);
  window.mwWide = {
    tt: tt, name: name,
    sub: H => { merge(); return H && H.wide ? name(H.wide.mount) : ""; },
    sheet: (s, H, act) => {                            // 139 sheet(): the picture, the mounts, the overview
      const w = H && H.wide;
      if (!w) { s.appendChild(E("div", "mut", tt("not supported - update the simulator"))); return; }
      N = w.n; s.appendChild(pic());
      LAB.textContent = "🔭 " + tt("Wide camera") + " · " + name(w.mount);
      if (w.missing) { WAIT.textContent = tt("Not installed (blind cover) - no wide picture"); WAIT.hidden = false; N = null; }
      else if (N == null) WAIT.textContent = tt("The wide camera is not an extra camera of MoveEye");
      M.forEach(([k, lb]) => { const b = E("button", k === w.mount ? "" : "sec", tt(lb)); b.type = "button"; b.onclick = () => act("wide_mount", k); s.appendChild(b); });
      s.appendChild(E("div", "mut mwwnote", w.missing ? tt("Not installed (blind cover) - no wide picture")
        : w.mount === "scene" ? tt("On the mast: not part of the device - it does not steer the head by itself.")
        : w.ov ? "⟲ " + tt("Steers the head as overview («The overview camera steers the head»)") + (w.ov_on ? "" : " – " + tt("off"))
        : tt("Overview chosen by hand - not changed.")));
      setTimeout(feed, 30);
    }
  };
})();
</script>
"""
WIDE_KEYS = ("Wide camera", "In the case (v5.2)", "Not installed (blind cover)", "Not installed (blind cover) - no wide picture",
             "Mast (scene)", "Base front, fixed", "Head front", "Head rear",
             "The wide camera is not an extra camera of MoveEye", "On the mast: not part of the device - it does not steer the head by itself.",
             "Steers the head as overview («The overview camera steers the head»)", "Overview chosen by hand - not changed.")
_simhub_head_139 = simhub_head


def simhub_head():                                        # + 591: the wide picture (139 tile «wide», 549 Sim-Kompakt)
    return _simhub_head_139() + WIDE_JS.replace("/*WDE*/{}", json.dumps({k: DE[k] for k in WIDE_KEYS if k in DE}, ensure_ascii=False), 1)


def weit_selftest():
    keep = {k: CFG.get(k) for k in ("sim_on", "kopf_ov", "kopf_ov_simauto", "extra_cams", "kopf_ov_offset", "light_ir_wide", "light_white_out")}
    keep_info, keep_head, keep_m = SIM.get("info"), SIM.get("head"), WEIT["mount"]
    _ss = save_settings
    try:
        globals()["save_settings"] = lambda *a, **k: None
        CFG.update(sim_on=True, kopf_ov="", kopf_ov_simauto=False, extra_cams=["sim:1"], kopf_ov_offset=0.0)
        SIM["info"] = {"cameras": [{"id": 0, "fov_h": 66}, {"id": 1, "fov_h": 102.0, "fov_v": 67.0, "w": 640, "h": 360, "mount": "scene", "on_head": False}]}
        WEIT["mount"] = None; weit_auto()
        assert CFG["kopf_ov"] == "", "mast: not the overview by itself"
        weit_from_sim({"mount": "head_rear", "yaw_offset": 180.0, "on_head": True, "pan_follow": True})
        assert CFG["kopf_ov"] == "sim:1" and CFG["kopf_ov_simauto"]
        SIM["head"] = [30.0, 0.0]
        assert abs(kopf_ov_deg(0.5) - (-150.0)) < 0.01, kopf_ov_deg(0.5)          # 30 + 180 = 210 = -150
        assert abs(kopf_ov_deg(1.0) - (-99.0)) < 0.01                              # + 51° right in the picture
        CFG["kopf_ov"] = ""                                                         # by hand: stays as long as the mount stays
        weit_from_sim({"mount": "head_rear"}); assert CFG["kopf_ov"] == ""
        weit_from_sim({"mount": "base", "yaw_offset": 0.0, "on_head": False})
        assert CFG["kopf_ov"] == "sim:1" and abs(kopf_ov_deg(0.25) + 25.5) < 0.01
        weit_from_sim({"mount": "case", "yaw_offset": 0.0, "on_head": False, "installed": True})      # P9: case v5.2
        assert CFG["kopf_ov"] == "sim:1" and abs(kopf_ov_deg(1.0) - 51.0) < 0.01 and not weit_missing()
        weit_from_sim({"mount": "none", "yaw_offset": 0.0, "on_head": False, "installed": False})    # P9: blind cover
        assert CFG["kopf_ov"] == "" and weit_missing() and "blind cover" in open_source("sim:1")[3]
        weit_from_sim({"mount": "case", "installed": True}); assert CFG["kopf_ov"] == "sim:1"
        weit_from_sim({"mount": "scene", "yaw_offset": 0.0, "on_head": False})
        assert CFG["kopf_ov"] == "" and not CFG["kopf_ov_simauto"]
        CFG.update(light_ir_wide=True, light_white_out="pca:4")
        assert not weit_ir_ch_free()
        assert "ir_wide" in sim_state()["lights"]
        assert "mwWide" in simhub_head()
    finally:
        globals()["save_settings"] = _ss
        CFG.update(keep); SIM["info"] = keep_info; SIM["head"] = keep_head; WEIT["mount"] = keep_m


SELFTEST_EXTRA.append(("Wide camera of the simulator: mount, overview by itself, head direction (163 / 591)", weit_selftest))
