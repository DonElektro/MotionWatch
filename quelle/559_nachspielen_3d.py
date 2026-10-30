#@ MoveEye – Teil 559: «In 3D nachspielen» (Alarm-Rückblick im 3D-Simulator) auch aus der Zeitleiste und den Aufnahmen, ein Knopf-Aussehen überall (Aufräumen 2, Daniel 30.10.2026). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Bisher gab es den Alarm-Rückblick in 3D (180 ALARM_TRACKS, /api/sim «replay», 550) nur auf der Simulator-Seite /sim (Reiter
# Simulator → Werkzeuge: Auswahl der letzten Alarme). Jetzt zeigt jede Aufnahme und jeder Alarm der Zeitleiste, zu dem
# eine Spur gespeichert ist, denselben Knopf «⏪ In 3D nachspielen» (mwR3d unten, gleiche Klasse «r3d» auf allen drei
# Seiten). Die Spur gehört zur Aufnahme, wenn ihr Zeitstempel im Namen steht (person_<stamp>.mp4), sonst die nächste
# Spur höchstens 30 s neben der Zeit.
# ----------------------------------------------------------------------------
def replay3d_for(t=None, name=None):
    """the id of the alarm track (180) for a recording / an alarm, or None"""
    try:
        alarm_tracks_load()
        tracks = [x for x in list(ALARM_TRACKS) if len(x.get("samples") or []) >= 2]
    except Exception:
        return None
    if name:
        for x in tracks:
            if str(x.get("id") or "") and str(x["id"]) in str(name):
                return x["id"]
    if t is None:
        return None
    best = min(tracks, key=lambda x: abs(float(x.get("t") or 0) - float(t)), default=None)
    return best["id"] if best is not None and abs(float(best.get("t") or 0) - float(t)) <= 30.0 else None


_timeline_build_425 = timeline_build


# wraps: timeline_build
def timeline_build(day=None, mode="night", lang=None):    # + 559: «In 3D nachspielen» at recordings and alarms
    r = _timeline_build_425(day, mode, lang)
    try:
        if ALARM_TRACKS or os.path.exists(_atr_file()):
            for it in r.get("items") or []:
                if it.get("type") == "rec" or (it.get("type") == "log" and it.get("alarm")):
                    k = replay3d_for(it.get("t"), it.get("name"))
                    if k:
                        it["r3d"] = k
    except Exception:
        pass
    return r


_list_recordings_430 = list_recordings


# wraps: list_recordings
def list_recordings(args, watch=None):                    # + 559: the same for the page «Aufnahmen»
    r = _list_recordings_430(args, watch)
    try:
        for it in r.get("items") or []:
            if not it.get("timelapse"):
                ts = None
                try:
                    ts = datetime.strptime(it["time"], "%Y-%m-%d %H:%M:%S").timestamp()
                except (KeyError, TypeError, ValueError):
                    pass
                k = replay3d_for(ts, it.get("name"))
                if k:
                    it["r3d"] = k
    except Exception:
        pass
    return r


R3D_JS = r"""<script>
// ---- «⏪ In 3D nachspielen» (559): one button look on the simulator page (tools), in the timeline and in the recordings ----
(function () {
  try { Object.assign(I18N.de, {"Replay in 3D": "In 3D nachspielen", "plays in the window of the simulator": "läuft im Fenster des Simulators",
    "replay-3d-tip": "Zeigt im 3D-Simulator, wer woher kam und wohin MoveEye geschaut hat (15 s vor bis 20 s nach dem Alarm). Braucht den verbundenen Simulator."}); } catch (e) {}
  try { if (I18N.en) Object.assign(I18N.en, {"replay-3d-tip": "Shows in the 3D simulator who came from where and where MoveEye looked (15 s before to 20 s after the alarm). Needs the connected simulator."}); } catch (e) {}
  const tt = k => { try { return t(k); } catch (e) { return k; } };
  if (!document.getElementById("r3d-css")) { const st = document.createElement("style"); st.id = "r3d-css";
    st.textContent = ".r3d{display:inline-flex;align-items:center;gap:6px;background:var(--acc,#388bfd);color:#fff;border:1px solid var(--acc,#388bfd);border-radius:10px;padding:8px 14px;font:inherit;font-weight:600;cursor:pointer}.r3d:disabled{opacity:.6}";
    document.head.appendChild(st); }
  // id: the track id or a function giving it; speed: a function giving 1 / 2 / 4 (optional)
  window.mwR3d = function (id, speed) {
    const b = document.createElement("button"); b.type = "button"; b.className = "r3d"; b.textContent = "⏪ " + tt("Replay in 3D"); b.title = tt("replay-3d-tip");
    b.onclick = async e => { e.stopPropagation(); const k = typeof id === "function" ? id() : id; if (!k) return; b.disabled = true; let r;
      try { r = await (await fetch("/api/sim", {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action: "replay", id: k, speed: speed ? speed() : 1, lang: typeof LANG !== "undefined" ? LANG : "de"})})).json(); }
      catch (x) { r = {ok: false, error: "simulator not reachable"}; }
      b.disabled = false; const m = r.ok ? "✓ " + tt("plays in the window of the simulator") : "⚠ " + (r.error || "error");
      if (typeof toast === "function") toast(m); else b.title = m; };
    return b;
  };
})();
</script>"""

R3D_TL_JS = r"""<script>
// 559: the viewer of the timeline: «In 3D nachspielen» next to the other buttons when a track belongs to it
(function () { if (typeof openIt !== "function") return; const _oi = openIt;
  openIt = function (it) { const p = _oi(it); try { const bx = document.querySelector("#vb .vbtn"); if (it && it.r3d && bx && window.mwR3d) bx.prepend(mwR3d(it.r3d)); } catch (e) {} return p; };
})();
</script>"""

R3D_REC_JS = r"""<script>
// 559: the recording opened in the big view: «In 3D nachspielen» below the picture when a track belongs to it
(function () { if (typeof openAt !== "function") return; const _oa = openAt;
  openAt = function (i, list) { const r = _oa(i, list); try { let w = document.getElementById("m-r3d"); const it = (typeof ML !== "undefined" ? ML : [])[i];
    if (!w) { w = document.createElement("div"); w.id = "m-r3d"; w.style.cssText = "margin:8px 0"; const b = document.getElementById("m-body"); if (b) b.after(w); }
    w.textContent = ""; if (it && it.r3d && window.mwR3d) w.appendChild(mwR3d(it.r3d)); } catch (e) {} return r; };
})();
</script>"""

TL_PAGE = TL_PAGE.replace("</body>", R3D_JS + R3D_TL_JS + "</body>", 1)
REC_PAGE = REC_PAGE.replace("</body>", R3D_JS + R3D_REC_JS + "</body>", 1)
SIM_PAGE = SIM_PAGE.replace("</body>", R3D_JS + "</body>", 1)          # the simulator tools (530 SIMTOOLS_JS on /sim): the CSS of «r3d»


def r3d_selftest():
    """the track of a recording (name) or an alarm (time ± 30 s); the button script on the three pages"""
    keep = list(ALARM_TRACKS); keep_l = _ATR["loaded"]
    try:
        _ATR["loaded"] = True
        ALARM_TRACKS.clear()
        t0 = time.time() - 3600
        ALARM_TRACKS.append({"id": "20261030_202707", "t": t0, "kind": "person", "samples": [{"t": t0}, {"t": t0 + 1}]})
        ALARM_TRACKS.append({"id": "20261030_210000", "t": t0 + 1800, "kind": "person", "samples": [{"t": t0}]})   # one sample: no replay
        assert replay3d_for(None, "person_20261030_202707.mp4") == "20261030_202707"
        assert replay3d_for(t0 + 25) == "20261030_202707" and replay3d_for(t0 + 40) is None and replay3d_for(t0 + 1800) is None
        assert "mwR3d" in TL_PAGE and "mwR3d" in REC_PAGE and "mwR3d" in SIM_PAGE and 'class="r3d"' not in WEB_PAGE
    finally:
        ALARM_TRACKS.clear(); ALARM_TRACKS.extend(keep); _ATR["loaded"] = keep_l
    return "recording by name, alarm by time, one button on timeline / recordings / simulator page"


SELFTEST_EXTRA.append(("Replay in 3D from the timeline and the recordings (559)", r3d_selftest))
