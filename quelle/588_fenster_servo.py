#@ MoveEye – Teil 588: Einstellungen «Servo-Bewegung & Sicherheit» (Web und Fenster), Fenster «Servos» (Not-Aus / Freigeben, wer steuert, Teach-in-Positionen, Diagnose mit Export), Not-Aus in der Kamerasteuerung des Fensters. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.35: the same as the web page /servo (539) in the window. The settings section sits in «Cameras & head» after
#   «Automatic head movement» (web GROUPS in 530, window TK_GROUPS here).
# ----------------------------------------------------------------------------
_SVS = "Servo motion & safety"
SLIDERS.extend([
    (_SVS, "servo_vmax_pan", "Pan: max. speed (°/s)", 10, 400, 5),
    (_SVS, "servo_acc_pan", "Pan: acceleration and braking (°/s²)", 50, 2000, 10),
    (_SVS, "servo_vmax_tilt", "Tilt: max. speed (°/s)", 10, 400, 5),
    (_SVS, "servo_acc_tilt", "Tilt: acceleration and braking (°/s²)", 50, 2000, 10),
    (_SVS, "servo_wd_s", "Watchdog: stop the servos when the camera loop hangs longer than (s)", 3, 60, 1),
    (_SVS, "servo_service_h", "Maintenance hint after (hours of movement per servo)", 10, 1000, 10),
])
TOGGLES.extend([
    (_SVS, "servo_estop_park", "Emergency stop: brake, then drive slowly to the parking position (otherwise: hold where it stopped)"),
    (_SVS, "servo_uv_stop", "Under-voltage: stop the servos (they move again by themselves 30 s after it is over)"),
])
TEXTS.extend([
    (_KS, "kopf_park_point", "Parking position: a taught point (instead of pan / tilt above)", "enum", "kopf_park_point"),
    (_KS, "kopf_home_point", "Home position: a taught point (the head comes back there)", "enum", "kopf_home_point"),
])
for _k in ("kopf_park_point", "kopf_home_point"):
    TEXT_SPECS[_k] = ("enum", _k)
SECTIONS.append(_SVS)
for _g in TK_GROUPS:
    if _g[0] == "camera" and _SVS not in _g[2]:
        _g[2].insert(_g[2].index(_KS) + 1 if _KS in _g[2] else 1, _SVS)
TK_SUB_ICONS[_SVS] = "⛔"
SIMPLE_IN_USE[_SVS] = lambda: live_has_head()

_text_choice_pairs_servo_base = text_choice_pairs


# wraps: text_choice_pairs
def text_choice_pairs(key):                                 # + 2.98.35: taught points as parking / home position (076)
    if key in ("kopf_park_point", "kopf_home_point"):
        out = teach_choice_pairs()
        cur = str(CFG.get(key) or "")
        if cur and cur not in [p[0] for p in out]:
            out.append((cur, cur))
        return out
    return _text_choice_pairs_servo_base(key)


def servo_tk_line(app):
    """one line for the camera controls of the window: stopped / who steers; a notice when another panel takes the head"""
    if servo_blocked():
        return ("⛔ " + tr("EMERGENCY STOP") + " – " + trf("pressed by {who}", who=CFG.get("servo_estop_by") or "?")) if servo_blocked() == "estop" else "⚠ " + servo_blocked_text()
    d = servo_driver()
    n_old = getattr(app, "_srv_n", None); app._srv_n = d.get("n")
    if n_old is not None and d.get("n") != n_old and d.get("kind") == "manual" and d.get("key") != "window":
        app._srv_note = (time.time() + 5.0, "🎮 " + trf("Now steered by {who}", who=d["label"]))
    nt = getattr(app, "_srv_note", None)
    if nt and time.time() < nt[0]:
        return nt[1]
    if d.get("kind") == "manual" and d.get("key") != "window":
        return "🎮 " + trf("The head is steered by: {who}", who=d["label"])
    return ""


def _app_srv_estop_btn(self):
    """the red button of the camera controls: stop - or, while stopped, release (with a question)"""
    if servo_blocked() in ("estop", "fault"):
        if messagebox.askyesno("MoveEye", tr("Release the servos? The head may move again (also by itself)."), parent=self.root):
            ok, err = servo_release(("window", tr("Window") + " (" + tr("this computer") + ")"))
            if not ok:
                messagebox.showinfo("MoveEye", tr(err), parent=self.root)
    else:
        servo_estop(("window", tr("Window") + " (" + tr("this computer") + ")"))


def _app_srv_win(self, page="teach"):
    win = getattr(self, "_srv_w", None)
    try:
        if win is not None and win.winfo_exists():
            win.lift(); return
    except Exception:
        pass
    who = ("window", tr("Window") + " (" + tr("this computer") + ")")
    win = tk.Toplevel(self.root); self._srv_w = win
    win.title("MoveEye – " + tr("Servos: safety, positions, test, diagnosis")); win.geometry("720x820")
    top = ttk.Frame(win); top.pack(fill="x", padx=12, pady=(10, 4))
    st = tk.Label(top, text="", font=("DejaVu Sans", 13, "bold"), anchor="w", justify="left", wraplength=680, padx=8, pady=6)
    st.pack(fill="x")
    drv = ttk.Label(top, text="", style="Mut.TLabel", wraplength=680, justify="left"); drv.pack(anchor="w", pady=(4, 0))
    bf = ttk.Frame(top); bf.pack(fill="x", pady=(6, 0))
    b_stop = tk.Button(bf, text="⏹ " + tr("Emergency stop"), bg="#d1242f", fg="#ffffff", activebackground="#a40e26", font=("DejaVu Sans", 13, "bold"),
                       command=lambda: (servo_estop(who), refresh()))
    b_stop.pack(side="left", expand=True, fill="x", padx=(0, 6))

    def rel():
        if messagebox.askyesno("MoveEye", tr("Release the servos? The head may move again (also by itself)."), parent=win):
            ok, err = servo_release(who)
            if not ok:
                messagebox.showinfo("MoveEye", tr(err), parent=win)
        refresh()
    b_rel = tk.Button(bf, text="✅ " + tr("Release"), bg="#2ea043", fg="#ffffff", font=("DejaVu Sans", 13, "bold"), command=rel)
    # drive: arrows + step
    pf = ttk.Frame(top); pf.pack(fill="x", pady=(8, 0))
    v_step = tk.StringVar(win, "3")
    for txt, cmd in (("◀", "left"), ("▲", "up"), ("▼", "down"), ("▶", "right"), ("◎", "center")):
        ttk.Button(pf, text=txt, width=4, command=lambda c=cmd: move_camera(c, float(v_step.get() or 3), who)).pack(side="left", padx=(0, 4))
    ttk.Label(pf, text=tr("Step")).pack(side="left", padx=(8, 4))
    ttk.Combobox(pf, textvariable=v_step, values=("0.5", "1", "3", "10"), width=5, state="readonly").pack(side="left")
    pos = ttk.Label(pf, text=""); pos.pack(side="left", padx=(10, 0))
    nb = ttk.Notebook(win); nb.pack(fill="both", expand=True, padx=12, pady=(6, 10))
    # ---- positions (teach-in) ----
    tp = ttk.Frame(nb); nb.add(tp, text="📍 " + tr("Positions"))
    ttk.Label(tp, text=tr("teach-note"), style="Mut.TLabel", wraplength=660, justify="left").pack(anchor="w", pady=(6, 4))
    af = ttk.Frame(tp); af.pack(fill="x")
    v_name = tk.StringVar(win, "")
    ttk.Entry(af, textvariable=v_name).pack(side="left", fill="x", expand=True, padx=(0, 6))

    def add():
        ok, err, _i = teach_add(v_name.get(), "window")
        if not ok:
            messagebox.showinfo("MoveEye", tr(err), parent=win)
        v_name.set(""); refresh(True)
    ttk.Button(af, text="📍 " + tr("Save position"), command=add).pack(side="left")
    cols = ("n", "name", "pan", "tilt", "flags")
    tv = ttk.Treeview(tp, columns=cols, show="headings", height=10, selectmode="browse")
    for c, w_, lab in (("n", 40, "#"), ("name", 220, tr("Name")), ("pan", 80, tr("Pan") + " °"), ("tilt", 80, tr("Tilt") + " °"), ("flags", 200, "")):
        tv.heading(c, text=lab); tv.column(c, width=w_, anchor="w")
    tv.pack(fill="both", expand=True, pady=(6, 4))

    def sel():
        try:
            s = tv.selection()
            return int(s[0]) if s else None
        except (TypeError, ValueError, IndexError):
            return None

    def ed(op_, val=None):
        i = sel()
        if i is None:
            return
        ok, err = teach_edit(op_, i, val, "window")
        if not ok:
            messagebox.showinfo("MoveEye", tr(err), parent=win)
        refresh(True, i - 1 if op_ == "up" else i + 1 if op_ == "down" else i)

    def go():
        i = sel()
        if i is not None:
            ok, err = teach_goto(i, who)
            if not ok and err:
                messagebox.showinfo("MoveEye", tr(err), parent=win)

    def ren():
        i = sel()
        if i is None:
            return
        from tkinter import simpledialog
        v = simpledialog.askstring("MoveEye", tr("New name"), initialvalue=wp_name(WAYPOINTS[i]), parent=win)
        if v is not None:
            ed("rename", v)
    tb = ttk.Frame(tp); tb.pack(fill="x")
    for txt, f in (("▶ " + tr("Go"), go), ("✏️ " + tr("Rename"), ren), ("⤓ " + tr("Here"), lambda: ed("update")),
                   ("▲", lambda: ed("up")), ("▼", lambda: ed("down")),
                   ("🔄 " + tr("in the round"), lambda: ed("patrol", not wp_patrol(WAYPOINTS[sel()])) if sel() is not None else None),
                   ("🅿", lambda: ed("park")), ("🏠", lambda: ed("home")),
                   ("🗑", lambda: ed("delete") if sel() is not None and messagebox.askyesno("MoveEye", tr("Delete this position?"), parent=win) else None)):
        ttk.Button(tb, text=txt, command=f).pack(side="left", padx=(0, 4), pady=(0, 4))
    ttk.Button(tp, text="📍 " + tr("Take over from «Set up the place»"), command=lambda: (teach_from_place("window"), refresh(True))).pack(anchor="w", pady=(4, 0))
    # ---- test (aufr: before Mehr → Werkzeuge «Servo test» of the web page; the same servo_test() of part 300) ----
    xp = ttk.Frame(nb); nb.add(xp, text="🛠 " + tr("Test"))
    ttk.Label(xp, text=tr("servo-note"), style="Mut.TLabel", wraplength=660, justify="left").pack(anchor="w", pady=(6, 4))
    xb = ttk.Frame(xp); xb.pack(fill="x")
    x_msg = ttk.Label(xb, text="", wraplength=520, justify="left")

    def x_start():
        if not servo_test():
            messagebox.showinfo("MoveEye", tr("not possible now"), parent=win)
        refresh(True)
    ttk.Button(xb, text="▶ " + tr("Start the servo test"), command=x_start).pack(side="left")
    x_msg.pack(side="left", padx=(10, 0))
    x_txt = tk.Text(xp, height=20, wrap="none", font=("DejaVu Sans Mono", 9)); x_txt.pack(fill="both", expand=True, pady=(6, 4))

    def test_text():
        V = TOOLS["servo"]
        out = [f"{tr('Axis'):8} {tr('To'):>6} {tr('Picture change'):>16}  {tr('Result')}"] if V["steps"] else []
        for s_ in V["steps"]:
            out.append(f"{tr('Pan' if s_['axis'] == 'pan' else 'Tilt'):8} {str(s_['to']) + ' %':>6} {('–' if s_['diff'] is None else str(s_['diff'])):>16}  "
                       + ("⚠ " + tr("no change") if s_.get("ok") is False else "✓" if s_.get("ok") else "…"))
        return "\n".join(out)
    # ---- diagnosis ----
    dp = ttk.Frame(nb); nb.add(dp, text="🩺 " + tr("Diagnosis"))
    txt = tk.Text(dp, height=24, wrap="word", font=("DejaVu Sans Mono", 9)); txt.pack(fill="both", expand=True, pady=(6, 4))
    db = ttk.Frame(dp); db.pack(fill="x")

    def export(fmt):
        from tkinter import filedialog
        data, _mt, fn = servo_diag_export(fmt)
        p = filedialog.asksaveasfilename(parent=win, initialfile=fn, defaultextension="." + fmt, filetypes=[(fmt.upper(), "*." + fmt)])
        if p:
            try:
                with open(p, "wb") as f:
                    f.write(data)
            except OSError as e:
                messagebox.showinfo("MoveEye", str(e), parent=win)
    ttk.Button(db, text="⬇ JSON", command=lambda: export("json")).pack(side="left", padx=(0, 4))
    ttk.Button(db, text="⬇ CSV", command=lambda: export("csv")).pack(side="left", padx=(0, 4))
    ttk.Button(db, text="🔧 " + tr("Maintenance done"), command=lambda: (servo_diag_service_done("", "window"), refresh(True))
               if messagebox.askyesno("MoveEye", tr("Maintenance of both servos done? The maintenance counters start again."), parent=win) else None).pack(side="left", padx=(0, 4))
    ttk.Button(db, text="🗑 " + tr("Clear fault memory"), command=lambda: (servo_diag_clear_faults("window"), refresh(True))
               if messagebox.askyesno("MoveEye", tr("Clear the fault memory?"), parent=win) else None).pack(side="left")
    S = {"sig": None, "dsig": None}

    def diag_text():
        D = servo_diag_state()
        out = []
        for h in D["hints"]:
            out.append(("⚠ " if h["level"] == "warn" else "ℹ ") + h["text"])
        if not D["hints"]:
            out.append("✅ " + tr("No maintenance hints."))
        for k, nm in (("hw", "Real servos"), ("sim", "Simulation")):
            b = D[k]
            out += ["", f"{tr(nm)} · {trf('{h} h switched on', h=b['on_h'])}" + (f" · ⚡ {trf('{n} min with under-voltage', n=b['uv_min'])}" if b["uv_min"] else "")]
            for ax, an in (("pan", "Pan"), ("tilt", "Tilt")):
                a = b["axes"][ax]
                out.append(f"  {tr(an):8} {a['deg']:>8}° ({a['turns']} {tr('turns')}) · {a['move_h']} h {tr('moving')} · {a['moves']} {tr('moves')}"
                           + (f" · {tr('since maintenance')}: {a['service_h']} / {D['service_h']:.0f} h" if k == "hw" else ""))
        out += ["", tr("Fault memory") + f" ({D['n_faults']}):"]
        for f in D["faults"]:
            out.append(f"  {'⛔' if f['level'] == 'error' else '⚠' if f['level'] == 'warn' else 'ℹ'} {datetime.fromtimestamp(f['last']).strftime('%d.%m. %H:%M')} "
                       f"{f['what']}{' ×' + str(f['n']) if f['n'] > 1 else ''}{' · ' + tr('simulation') if f['sim'] else ''}{' – ' + f['text'] if f['text'] else ''}")
        if not D["faults"]:
            out.append("  " + tr("The fault memory is empty."))
        return "\n".join(out)

    def refresh(force=False, select=None):
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return
        b = servo_blocked()
        if b:
            st.config(text=("⛔ " + tr("EMERGENCY STOP") + " – " + trf("pressed by {who}", who=CFG.get("servo_estop_by") or "?")) if b == "estop" else "⚠ " + servo_blocked_text(),
                      bg="#5c1515", fg="#ffffff")
        else:
            st.config(text="✅ " + tr("Ready - the servos may move"), bg="#16361f", fg="#ffffff")
        if b in ("estop", "fault"):
            b_rel.pack(side="left", expand=True, fill="x")
        else:
            b_rel.pack_forget()
        b_stop.config(state="disabled" if b == "estop" else "normal")
        d = servo_driver()
        drv.config(text=("🎮 " + trf("The head is steered by: {who}", who=d["label"]) + (" (" + tr("you") + ")" if d["key"] == "window" else "")) if d["kind"] == "manual"
                   else ("🤖 " + trf("The head moves by itself: {what}", what=d["label"])) if d["kind"] == "auto" else "")
        pd, td = servo_pos_deg()
        pos.config(text=trf("Pan {p}° · tilt {t}°", p=f"{pd:.1f}", t=f"{td:.1f}"))
        L = teach_list()
        sig = json.dumps(L)
        if force or sig != S["sig"]:
            S["sig"] = sig
            keep = sel() if select is None else select
            tv.delete(*tv.get_children())
            for p in L:
                fl = " ".join(x for x, on in (("🔄", p["patrol"]), ("🅿", p["park"]), ("🏠", p["home"])) if on)
                tv.insert("", "end", iid=str(p["i"]), values=(p["i"] + 1, p["name"] or (tr("Waypoint") + f" {p['i'] + 1}"), p["deg"][0], p["deg"][1], fl))
            if keep is not None and 0 <= keep < len(L):
                tv.selection_set(str(keep))
        if nb.index("current") == 1:
            V = TOOLS["servo"]
            x_msg.config(text=tr("running…") if V["running"] else ("✓ " + tr("ok")) if V["msg"] == "ok" else ("⚠ " + str(V.get("bad") or "") + " " + tr(V["msg"])) if V["msg"] else "")
            tt_ = test_text()
            if force or tt_ != S.get("tsig"):
                S["tsig"] = tt_
                x_txt.config(state="normal"); x_txt.delete("1.0", "end"); x_txt.insert("1.0", tt_); x_txt.config(state="disabled")
        if nb.index("current") == 2:
            dt_ = diag_text()
            if force or dt_ != S["dsig"]:
                S["dsig"] = dt_
                txt.config(state="normal"); txt.delete("1.0", "end"); txt.insert("1.0", dt_); txt.config(state="disabled")

    def loop():
        try:
            if not win.winfo_exists():
                return
            refresh()
        except Exception:
            return
        win.after(1000, loop)
    nb.bind("<<NotebookTabChanged>>", lambda e: S.update(dsig=None, tsig=None))
    if page == "diag":
        nb.select(2)
    elif page == "test":
        nb.select(1)
    refresh(True); win.after(1000, loop)


_qr_tk_build_section_servo_base = App._build_section


def _servo_tk_build_section(self, sec, sbody, settings_parent=None):
    _qr_tk_build_section_servo_base(self, sec, sbody, settings_parent)
    if sec == _SVS:
        try:
            bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(6, 0))
            ttk.Button(bf, text="📍 " + tr("Positions") + " …", command=lambda: self._srv_win("teach")).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ttk.Button(bf, text="🛠 " + tr("Test") + " …", command=lambda: self._srv_win("test")).pack(side="left", expand=True, fill="x", padx=(0, 4))   # aufr
            ttk.Button(bf, text="🩺 " + tr("Diagnosis") + " …", command=lambda: self._srv_win("diag")).pack(side="left", expand=True, fill="x")
        except Exception as e:
            log_event("sys", f"Window: servo buttons: {e}"[:160])


# wraps: App._build_section
App._build_section = _servo_tk_build_section
App._srv_win = _app_srv_win
App._srv_estop_btn = _app_srv_estop_btn


def servo_web_selftest():
    """the page renders, the JS of the live page is filled in, the API ops are known"""
    assert "/servo#test" in TOOLS_PAGE and "pick('servo')" not in TOOLS_PAGE and "Servo diagnosis" not in TOOLS_PAGE   # aufr: ONE entry «Servos»
    assert 'id="p-test"' in SERVO_PAGE and "servoPaint" in WEB_PAGE and "<!--SERVOJS-->" not in WEB_PAGE
    html = servo_page()
    assert "/*SERVODE*/" not in html and "sv-estop" in html
    assert servo_api_op({"op": "nonsense"}, ("k", "x"), True)[1] == 400 and servo_api_op({"op": "release"}, ("k", "x"), False)[1] == 403
    return "page /servo (positions, test, diagnosis), live page script, one Tools entry"


SELFTEST_EXTRA.append(("Servo motion planner (ramps, limits)", servo_planner_selftest))
SELFTEST_EXTRA.append(("Servo fault memory and maintenance hints", servo_diag_selftest))
SELFTEST_EXTRA.append(("Taught points (teach-in)", teach_selftest))
SELFTEST_EXTRA.append(("Servo page and Not-Aus on the live page", servo_web_selftest))
