#@ MoveEye – Teil 575: Fenster und Einstellungen für Gehtest, Entfernung, Wärmebild-Personen, Akku-Sparen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13: the settings of parts 105 / 232 / 415 in the schema (web and window show them by themselves), and the window
# «Gehtest» of the desktop program (button in «Camping / protection»).
# ----------------------------------------------------------------------------
TOGGLES += [
    ("Thermal camera", "thermal_person", "Thermal picture: an upright warm body counts as a person (at night, when the camera sees nobody)"),
    ("Thermal camera", "thermal_person_day", "… by day too"),
    ("Battery", "batt_save_on", "Battery saver: below the threshold fewer pictures and the AI less often (by itself)"),
]
SLIDERS += [
    ("Battery", "batt_save_pct", "Battery saver from (% battery; back to normal at +5 % or when charging)", 5, 60, 1),
    ("Battery", "batt_save_fps", "Battery saver: at most pictures per second", 1, 10, 1),
    ("Camera / Servos", "cam_vfov", "Camera: vertical field of view (°) - for the distance of a person (Camera Module 3: 41)", 20, 120, 1),
]
SIMPLE_KEYS.update({"thermal_person", "batt_save_on", "batt_save_pct"})


def _app_walktest(self):
    """the window «Gehtest»: start / stop, time left, what was seen, the result picture"""
    win = getattr(self, "_wt_win", None)
    try:
        if win is not None and win.winfo_exists():
            win.lift(); return
    except Exception:
        pass
    win = tk.Toplevel(self.root); self._wt_win = win
    win.title("MoveEye – " + tr("Walk test")); win.geometry("680x720")
    ttk.Label(win, text=tr("Walk past the camera like a visitor would: MoveEye beeps at every detection and draws where you were recognised (and where only movement was seen). 3 minutes, no alarms meanwhile."),
              wraplength=640, justify="left").pack(anchor="w", padx=12, pady=(12, 6))
    bf = ttk.Frame(win); bf.pack(fill="x", padx=12)
    st_lbl = ttk.Label(win, text="", font=("TkDefaultFont", 12, "bold")); st_lbl.pack(anchor="w", padx=12, pady=(8, 2))
    pic = ttk.Label(win); pic.pack(padx=12, pady=6)
    txt = ttk.Label(win, text="", wraplength=640, justify="left"); txt.pack(anchor="w", padx=12)
    leg = ttk.Label(win, text="● " + tr("Person recognised") + " (" + tr("green") + ")   ○ " + tr("Movement, no person") + " (" + tr("orange") + ")   ● "
                    + tr("only in the thermal picture") + " (" + tr("violet") + ")", style="Mut.TLabel", wraplength=640)
    leg.pack(anchor="w", padx=12, pady=(4, 8))
    ttk.Button(bf, text="▶ " + tr("Start walk test"), command=lambda: self._status("Walk test", "" if walktest_start("window")[0] else "⚠")).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="■ " + tr("Stop"), command=lambda: walktest_stop("button")).pack(side="left", expand=True, fill="x")
    seen = {"img_t": None, "beeps": -1}

    def show_img(res):
        p = walktest_img()
        if not p or not res or seen["img_t"] == res.get("t"):
            return
        seen["img_t"] = res.get("t")
        try:
            im = cv2.imread(p)
            if im is None:
                return
            if im.shape[1] > 640:
                im = cv2.resize(im, (640, int(im.shape[0] * 640 / im.shape[1])))
            ok, buf = cv2.imencode(".png", im)
            if ok:
                ph_ = tk.PhotoImage(data=base64.b64encode(buf.tobytes()).decode())
                pic.config(image=ph_); pic.image = ph_
        except Exception:
            pass

    def tick():
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return
        S = walktest_state()
        if S["on"]:
            st_lbl.config(text=f"🚶 {S['left'] // 60}:{S['left'] % 60:02d} {tr('left')} · {tr('Person recognised')} {S['n_det']}× · "
                               f"{tr('Movement, no person')} {S['n_mot']}×" + (f" · {tr('last')}: {tr('about')} {S['last_m']} m" if S.get("last_m") else ""))
            if seen["beeps"] >= 0 and S["beeps"] > seen["beeps"] and not S["speaker"]:
                try:
                    win.bell()                                    # no loudspeaker at the Pi: the window beeps
                except Exception:
                    pass
            seen["beeps"] = S["beeps"]
            txt.config(text="🔕 " + tr("Walk test running - no alarms"))
        else:
            seen["beeps"] = -1
            R = S.get("result")
            st_lbl.config(text=(tr("Last walk test") + " · " + R["when"]) if R else "")
            txt.config(text="\n".join("• " + x for x in (R or {}).get("text") or []))
            show_img(R)
        win.after(1000, tick)
    tick()


App._walktest = _app_walktest
