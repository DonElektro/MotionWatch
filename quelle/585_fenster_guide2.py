#@ MoveEye – Teil 584: Fenster: Guide 2 – Einrichtung schnell / ausgiebig, Rundgang pro Reiter (Rahmen + Textfeld), «?» bei Einstellungen, Tipp des Tages, «Auf Werkseinstellungen zurücksetzen». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# The same guide as on the web page (516): the state is on the Pi (CFG guide2, 586), so a setup begun in the window can be
# continued on the phone and the other way round. The tour of a tab is simpler than on the web page: a coloured frame
# round the control and a text box with «Next» / «Skip» (Tk cannot dim the rest of the window).
# ----------------------------------------------------------------------------
TK_G2_TOURS = {   # tab -> [(attribute or callable(self) -> widget, English title, English text)]
    "live": [("video", "The live picture", "What the camera sees right now. Double-click = only the picture."),
             (lambda s: getattr(s, "stick", None), "Turn the head", "With the joystick you turn the camera head."),
             (lambda s: next((w.master for w in (s.qs_tiles or {}).values() if hasattr(w, "master")), None), "Quick switches", "Recording, photo, follow, patrol, light, infrared and thermal picture - one click each."),
             (lambda s: getattr(s, "_tabs_row", None), "The six tabs", "Live · Protection · History · Settings · Simulator · More. The «?» at the top shows this tour again.")],
    "protect": [(lambda s: s.tab_btns.get("protect"), "Protection", "Off, Watchful (only messages) or Full (light, siren) - and everything that protects, in groups."),
                (lambda s: getattr(s, "right_f", None), "Topics", "Open a group to change it. Changes are saved at once."),
                (lambda s: s.tab_btns.get("settings"), "Settings", "All other settings, sorted by topic.")],
    "history": [(lambda s: getattr(s, "log", None), "Event log", "What MoveEye did and why - the important events."),
                (lambda s: s.tab_btns.get("history"), "More history", "Recordings, animal diary and the message list: the buttons below the log.")],
    "settings": [(lambda s: getattr(s, "right_f", None), "Topics", "Open a topic to change it. Changes are saved at once."),
                 (lambda s: s.tab_btns.get("settings"), "Simple or Expert", "«Simple» shows only the important settings - for this tab. «Expert» shows all."),
                 (lambda s: s.tab_btns.get("more"), "The «?»", "Next to a setting: what it does and what we recommend.")],
    "sim": [(lambda s: getattr(s, "right_f", None), "Simulator", "The 3D simulator on the PC: connection, «Improve detection», settings of the simulation."),
            (lambda s: s.tab_btns.get("sim"), "Simulator centre", "Tests, «Improve detection», training night - MoveEye learns without the real place.")],
    "more": [(lambda s: getattr(s, "h_text", None), "Self-check", "What works and what is missing - with a hint what to do."),
             (lambda s: getattr(s, "_g2_more_bar", None), "Setup and help", "Start or continue the setup, show the tours again, reset to factory settings.")],
}


def _g2_tk_widget(self, g):
    try:
        w = g(self) if callable(g) else getattr(self, g, None)
        return w if w is not None and w.winfo_exists() and w.winfo_ismapped() else None
    except Exception:
        return None


def _g2_tk_tour(self, tab=None, force=False):
    """the tour of a tab: a frame round the control and a text box (Next / Skip)"""
    tab = tab or self.tab
    if getattr(self, "_g2_tw", None) is not None:
        return
    try:
        seen = json.loads((CFG.get("web_ui") or {}).get("mw-tours-seen") or "[]")
    except (TypeError, ValueError):
        seen = []
    if not force and (tab in seen or not CFG.get("tours_auto", True) or not CFG["setup_done"]):
        return
    steps = [(w, tr(t), tr(x)) for w, t, x in ((self._g2_tk_widget(g), t, x) for g, t, x in TK_G2_TOURS.get(tab, [])) if w is not None]
    if not steps:
        return
    frames = []
    box = tk.Toplevel(self.root); box.overrideredirect(True); box.configure(bg=C["acc"]); box.attributes("-topmost", True)
    self._g2_tw = box
    inner = tk.Frame(box, bg=C["panel"], padx=12, pady=10); inner.pack(padx=2, pady=2)
    bk = blinki_tk_label(inner, 58, "normal", C["panel"])            # 589: Blinki next to the text
    if bk is not None:
        bk.pack(side="left", anchor="n", padx=(0, 10)); inner = tk.Frame(inner, bg=C["panel"]); inner.pack(side="left", fill="both")
    l_t = tk.Label(inner, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"), anchor="w", justify="left"); l_t.pack(fill="x")
    l_x = tk.Label(inner, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w", justify="left", wraplength=300); l_x.pack(fill="x", pady=(2, 8))
    bf = tk.Frame(inner, bg=C["panel"]); bf.pack(fill="x")
    l_n = tk.Label(bf, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8)); l_n.pack(side="left")
    st = {"i": 0}

    def end():
        for f in frames:
            try:
                f.destroy()
            except Exception:
                pass
        try:
            box.destroy()
        except Exception:
            pass
        self._g2_tw = None
        s_ = set(seen); s_.add(tab)
        web_ui_update({"mw-tours-seen": json.dumps(sorted(s_))})

    def show():
        for f in frames:
            f.destroy()
        frames.clear()
        w, t, x = steps[st["i"]]
        try:
            X, Y, W, H = w.winfo_rootx(), w.winfo_rooty(), w.winfo_width(), w.winfo_height()
        except Exception:
            nxt(); return
        for (fx, fy, fw, fh) in ((X - 4, Y - 4, W + 8, 4), (X - 4, Y + H, W + 8, 4), (X - 4, Y, 4, H), (X + W, Y, 4, H)):
            f = tk.Toplevel(self.root); f.overrideredirect(True); f.configure(bg=C["acc"]); f.attributes("-topmost", True)
            f.geometry(f"{max(1, fw)}x{max(1, fh)}+{fx}+{fy}"); frames.append(f)
        l_t.config(text=t); l_x.config(text=x); l_n.config(text=f"{st['i'] + 1} / {len(steps)}")
        im = blinki_tk_image(58, "normal" if st["i"] == 0 else "happy" if st["i"] == len(steps) - 1 else "point") if bk is not None else None
        if im is not None:
            bk.config(image=im); bk.image = im
        b_n.config(text=(tr("Done") if st["i"] == len(steps) - 1 else tr("Next") + " ›"))
        box.update_idletasks()
        bw, bh = box.winfo_reqwidth(), box.winfo_reqheight()
        sw_, sh_ = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        by = Y + H + 10 if Y + H + 10 + bh < sh_ else max(0, Y - bh - 10)
        bx = max(0, min(sw_ - bw, X))
        box.geometry(f"+{bx}+{by}"); box.lift()

    def nxt():
        st["i"] += 1
        if st["i"] >= len(steps):
            end()
        else:
            show()
    b_n = self._fbtn(bf, tr("Next"), nxt, primary=True); b_n.pack(side="right")
    self._fbtn(bf, tr("Skip"), end).pack(side="right", padx=(0, 6))
    box.bind("<Escape>", lambda e: end())
    self.root.after(50, show)


def _g2_tk_q(self, parent, key, side="right"):
    """the «?» next to a setting (window): explanation, recommendation, default"""
    h = getattr(self, "_g2_help_cache", None)
    if h is None or h[0] != cur_lang():
        h = self._g2_help_cache = (cur_lang(), g2_help())
    x = h[1].get(key)
    if not x:
        return
    bg = parent.cget("bg") if isinstance(parent, tk.Frame) else C["panel"]
    q = tk.Label(parent, text="?", bg=bg, fg=C["mut"], font=("DejaVu Sans", 8, "bold"), cursor="hand2", padx=4,
                 highlightthickness=1, highlightbackground=C["line"])
    q.pack(side=side, padx=(4, 4))

    def show(_e=None):
        txt = x["x"] + (("\n\n👍 " + tr("Recommended") + ": " + x["r"]) if x["r"] else "") + (("\n" + x["d"]) if x["d"] else "")
        w = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Help")); w.configure(bg=C["bg"]); w.transient(self.root)
        tk.Label(w, text=txt, bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 10), wraplength=380, justify="left").pack(padx=14, pady=(12, 8))
        ttk.Button(w, text=tr("Close"), command=w.destroy).pack(pady=(0, 12))
        w.geometry(f"+{q.winfo_rootx() - 40}+{q.winfo_rooty() + 20}")
    q.bind("<Button-1>", show)
    return q


def _g2_tk_factory(self):
    """«Reset to factory settings» in the window: password / PIN, the typed word, then the backup copy and the setup"""
    from tkinter import messagebox
    if CFG.get("lock_on"):
        messagebox.showinfo("MoveEye", tr_err("not possible in operator mode"), parent=self.root); return
    w = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Reset to factory settings")); w.configure(bg=C["bg"]); w.transient(self.root)
    f = tk.Frame(w, bg=C["bg"], padx=16, pady=12); f.pack(fill="both", expand=True)
    tk.Label(f, text="⚠ " + tr("Reset to factory settings"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 13, "bold"), anchor="w").pack(fill="x")
    for t1, t2, col in ((tr("Back to the factory settings:"), tr("all settings, zones, schedules, waypoints, password, users, PIN, the place"), C["txt"]),
                        (tr("These stay:"), tr("Wi-Fi and own Wi-Fi, remote access (Tailscale), the push channel (ntfy), the update settings, the own AI model and what it learned"), C["grn"]),
                        (tr("These are deleted:"), tr("all recordings and photos, the animal diary, the log"), C["red"])):
        tk.Label(f, text=t1, bg=C["bg"], fg=col, font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x", pady=(8, 0))
        tk.Label(f, text=t2, bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w", justify="left", wraplength=420).pack(fill="x")
    tk.Label(f, text=tr("First a copy of the old settings is saved - you can download it below."), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 9),
             anchor="w", justify="left", wraplength=420).pack(fill="x", pady=(8, 0))
    pw = tk.StringVar(); word = tk.StringVar()
    if web_pw_active():
        ttk.Label(f, text=tr("Your password")).pack(anchor="w", pady=(10, 0)); ttk.Entry(f, textvariable=pw, show="•").pack(fill="x")
    elif CFG.get("protect_pin"):
        ttk.Label(f, text=tr("Your PIN")).pack(anchor="w", pady=(10, 0)); ttk.Entry(f, textvariable=pw, show="•").pack(fill="x")
    ttk.Label(f, text=tr("Type {w} to confirm").replace("{w}", "«" + factory_word() + "»")).pack(anchor="w", pady=(10, 0))
    e = ttk.Entry(f, textvariable=word); e.pack(fill="x"); e.focus_set()
    l_err = tk.Label(f, text="", bg=C["bg"], fg=C["red"], font=("DejaVu Sans", 9), anchor="w"); l_err.pack(fill="x", pady=(4, 0))
    bf = tk.Frame(f, bg=C["bg"]); bf.pack(fill="x", pady=(8, 0))

    def go():
        ok, err = factory_check(pw.get(), pw.get(), word.get())
        if not ok:
            l_err.config(text="⚠ " + tr_err(err)); return
        ok, err, name = factory_reset("window")
        if not ok:
            l_err.config(text="⚠ " + tr_err(err)); return
        w.destroy()
        messagebox.showinfo("MoveEye", tr("Reset done.") + "\n\n" + tr("Copy of the old settings:") + "\n" + os.path.join(DATA_DIR, name), parent=self.root)
        self._schedule_rebuild()
        self.root.after(800, lambda: self._g2_wizard())
    ttk.Button(bf, text=tr("Reset now"), command=go).pack(side="right")
    ttk.Button(bf, text=tr("Close"), command=w.destroy).pack(side="right", padx=(0, 6))
    bk = factory_backups()
    if bk:
        tk.Label(f, text=tr("Copies of the old settings") + ":\n" + "\n".join(f"{x['when']} · {x['name']}" for x in bk[:5]) + "\n" + DATA_DIR,
                 bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 8), anchor="w", justify="left").pack(fill="x", pady=(10, 0))


def _g2_tk_wizard(self, force=False):
    """the guide in the window: the same steps as on the web page (state on the Pi, 586)"""
    from tkinter import messagebox
    w = getattr(self, "_g2_wz", None)
    if w is not None and w.winfo_exists():
        w.lift(); return
    w = self._g2_wz = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Setup")); w.configure(bg=C["bg"])
    w.geometry("560x620" if self.root.winfo_screenheight() >= 700 else "520x" + str(max(380, self.root.winfo_screenheight() - 60)))
    g = g2_state()
    st = {"cur": (g["left"][0] if g["left"] else "done") if g["mode"] and not g["finished"] else "choose", "after": []}
    top = tk.Frame(w, bg=C["bg"], padx=14, pady=8); top.pack(fill="x")
    l_head = tk.Label(top, bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 8, "bold"), anchor="w"); l_head.pack(side="left")
    l_later = tk.Label(top, text=tr("Continue later"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 8, "underline"), cursor="hand2")
    l_later.pack(side="right"); l_later.bind("<Button-1>", lambda e: (g2_action({"action": "pause"}, "window"), close()))
    pb = ttk.Progressbar(w, maximum=100); pb.pack(fill="x", padx=14)
    body = tk.Frame(w, bg=C["bg"], padx=14, pady=8); body.pack(fill="both", expand=True)
    foot = tk.Frame(w, bg=C["bg"], padx=14, pady=10); foot.pack(fill="x")

    def close():
        for a in st["after"]:
            try:
                w.after_cancel(a)
            except Exception:
                pass
        w.destroy()
    w.protocol("WM_DELETE_WINDOW", lambda: (g2_action({"action": "pause"}, "window"), close()))

    def order():
        return [s["id"] for s in g2_state()["steps"] if not s["auto_skip"]]

    def move(d):
        o = order(); c = st["cur"]
        i = o.index(c) if c in o else -1
        st["cur"] = (o[i + 1] if i + 1 < len(o) else "done") if d > 0 else ("choose" if i <= 0 else o[i - 1])
        if st["cur"] not in ("done", "choose"):
            g2_action({"action": "step", "id": st["cur"]}, "window")
        render()

    def lab(txt, mut=True, bold=False, col=None):
        l_ = tk.Label(body, text=txt, bg=C["bg"], fg=col or (C["mut"] if mut else C["txt"]), font=("DejaVu Sans", 12 if bold else 9, "bold" if bold else "normal"),
                      wraplength=500, justify="left", anchor="w")
        l_.pack(fill="x", pady=(6 if bold else 2, 2)); return l_

    def row():
        r = tk.Frame(body, bg=C["bg"]); r.pack(fill="x", pady=4); return r

    def toggle(text, key):
        f_ = tk.Frame(body, bg=C["panel"], padx=8, pady=4); f_.pack(fill="x", pady=2)
        Toggle(f_, text, bool(CFG.get(key)), lambda v, k=key: self._set(k, v)).pack(fill="x")

    def entry(label, value="", show=None):
        ttk.Label(body, text=label).pack(anchor="w", pady=(6, 0))
        v = tk.StringVar(value=str(value)); ttk.Entry(body, textvariable=v, show=show).pack(fill="x"); return v

    def render():
        for a in st["after"]:
            try:
                w.after_cancel(a)
            except Exception:
                pass
        st["after"] = []
        for x in body.winfo_children() + foot.winfo_children():
            x.destroy()
        G = g2_state(); o = [s["id"] for s in G["steps"] if not s["auto_skip"]]; c = st["cur"]
        l_head.config(text="🧭 " + tr("Setup") + (" · " + tr("In depth" if G["mode"] == "full" else "Quick") if G["mode"] else "")
                      + (f" · {tr('Step')} {o.index(c) + 1} {tr('of')} {len(o)}" if c in o else ""))
        pb.config(value=0 if c == "choose" else (100 if c == "done" else 100 * (o.index(c) if c in o else 0) / max(1, len(o))))
        meta = next((s for s in G["steps"] if s["id"] == c), {"icon": "", "title": ""})
        nxt = {"fn": None}
        if c == "choose":
            if not blinki_tk_say(body, "normal", "👋 " + tr("Welcome to MoveEye"), tr("Hello, I am Blinki!") + " " + tr("I am the eye of MoveEye. I show you everything step by step - and when I blink, all is well.")):
                lab("👋 " + tr("Welcome to MoveEye"), False, True)
            lab(tr("Every step can be skipped. You can stop at any time and continue later (More → Setup)."))
            lab(tr("Quick (about 5 min.) or thorough?"), False)
            for mode, ic, n, dur, txt in (("quick", "⚡", "Quick", "about 5 minutes", "Basics, push messages to the phone, camera test and place, protection and walk test."),
                                          ("full", "🔬", "In depth", "about 20 to 30 minutes", "Everything of «Quick» plus zones, night time, light and siren, head, AI model, thermal camera, battery, simulator - each step can be skipped.")):
                def pick(m=mode):
                    g2_action({"action": "start", "mode": m}, "window"); o_ = order(); st["cur"] = o_[0] if o_ else "done"; render()
                b = self._fbtn(body, f"{ic} {tr(n)} · {tr(dur)}\n{tr(txt)}", pick, primary=mode == "quick", font=("DejaVu Sans", 9, "bold"))
                b.config(justify="left", anchor="w", wraplength=480, pady=8); b.pack(fill="x", pady=4)
            self._fbtn(foot, tr("Later"), lambda: (g2_action({"action": "pause"}, "window"), close())).pack(side="right")
            return
        if c == "done":
            if not blinki_tk_say(body, "happy", "✅ " + tr("Done!")):
                lab("✅ " + tr("Done!"), False, True)
            for s in G["steps"]:
                d_ = s["id"] in G["done"]
                lab(("✓ " if d_ else "⤼ ") + s["icon"] + " " + s["title"] + ("" if d_ else " · " + (tr("skipped automatically") + f" ({s['auto_skip']})" if s["auto_skip"] else tr("skipped"))),
                    not d_, col=C["grn"] if d_ else None)
            r = row(); self._fbtn(r, "📱 " + tr("QR code for the phone"), lambda: self._qr_window(False)).pack(side="left")
            if G["mode"] != "full":
                def more():
                    g2_action({"action": "start", "mode": "full"}, "window"); st["cur"] = g2_state()["left"][0] if g2_state()["left"] else "done"; render()
                self._fbtn(foot, tr("➕ Set up more (thorough)"), more).pack(side="left")
            self._fbtn(foot, tr("Let's go"), lambda: (g2_action({"action": "finish"}, "window"), close(), self.root.after(500, lambda: self._g2_tour(self.tab))), primary=True).pack(side="right")
            self._fbtn(foot, "‹ " + tr("Back"), lambda: move(-1)).pack(side="right", padx=(0, 6))
            return
        if not blinki_tk_say(body, "point", meta["icon"] + " " + meta["title"]):
            lab(meta["icon"] + " " + meta["title"], False, True)
        if c == "basics":
            ttk.Label(body, text=tr("Language")).pack(anchor="w", pady=(6, 0))
            lv = tk.StringVar(value=cur_lang())
            cb = ttk.Combobox(body, state="readonly", values=list(LANGS), textvariable=lv); cb.pack(fill="x")
            nm = entry(tr("Name of this device (optional)"), CFG.get("device_name") or "")
            lab(tr("Time on MoveEye") + ": " + datetime.now().strftime("%d.%m.%Y %H:%M"))
            la = entry(tr("Latitude"), CFG.get("latitude")); lo = entry(tr("Longitude"), CFG.get("longitude"))
            toggle("⚡ " + tr("Fast updates (development)"), "update_fast")
            lab("🔒 " + tr("Password for this page"), False)
            lab(tr("Without a password everybody in the same network (and with the link) can watch and switch everything."))
            p1 = entry(tr("Password (6-64 characters)"), "", "•"); p2 = entry(tr("Repeat password"), "", "•")
            if web_pw_active():
                lab("✓ " + tr("A password is set already. Enter a new one only to change it."), col=C["grn"])

            def fn():
                if p1.get() != p2.get():
                    messagebox.showinfo("MoveEye", tr("The passwords are not the same"), parent=w); return False
                if lv.get() in LANGS:
                    CFG["lang"] = lv.get()
                ok, err = set_text("device_name", nm.get().strip()[:40])
                if not ok:
                    messagebox.showinfo("MoveEye", tr_err(err), parent=w); return False
                ok, err = g2_action({"action": "place_time", "lat": la.get(), "lon": lo.get()}, "window")
                if not ok:
                    messagebox.showinfo("MoveEye", tr_err(err), parent=w); return False
                if p1.get():
                    ok, err = web_pw_set(p1.get())
                    if not ok:
                        messagebox.showinfo("MoveEye", tr_err(err), parent=w); return False
                save_settings(); return True
            nxt["fn"] = fn
        elif c == "push":
            lab(tr("1. Install the free app «ntfy» (App Store / Play Store)."), False)
            lab(tr("2. In the app: + → enter the topic below (and the server, if it is not the default one) - or open this code with the phone camera."), False)
            u = CFG.get("notify_url") or ""
            ok_ = CFG.get("notify_type") == "ntfy" and re.match(r"^https://[^/]+/[^/]+$", u)
            if ok_:
                lab("✓ " + tr("The push channel is set up already:") + " " + u.replace("https://", ""), col=C["grn"])
            sv = entry(tr("Server"), u.rsplit("/", 1)[0] if ok_ else "https://ntfy-me.com")
            tv = entry(tr("Topic (like a secret channel name)"), u.rsplit("/", 1)[1] if ok_ else "mw-" + secrets.token_hex(5))
            res = lab("")

            def save():
                url = sv.get().strip().rstrip("/") + "/" + re.sub(r"[^A-Za-z0-9_-]", "", tv.get())
                ok, err = set_text("notify_url", url)
                if ok:
                    ok, err = set_text("notify_type", "ntfy"); CFG["notify_on"] = True; save_settings()
                if not ok:
                    res.config(text="⚠ " + tr_err(err), fg=C["red"])
                return ok

            def test():
                if save():
                    try:
                        self.watch.notifier.test(self.watch.frame_out); res.config(text="✓ " + tr("Sent - did it arrive on the phone?"), fg=C["grn"])
                    except Exception as e_:
                        res.config(text="⚠ " + str(e_)[:80], fg=C["red"])
            r = row(); self._fbtn(r, tr("📨 Send test message"), test).pack(side="left")
            nxt["fn"] = lambda: save() if len(tv.get()) >= 3 else True
        elif c == "camera":
            lab(tr("Is the picture right? Upright, sharp, the place in view?"))
            l_s = lab("", False)

            def tick():
                if not w.winfo_exists():
                    return
                l_s.config(text=f"{STATE.get('source_status', '')} · {float(STATE.get('fps') or 0):.1f} {tr('frames/s')}"
                           + ("" if float(STATE.get("fps") or 0) > 0 else "\n⚠ " + tr("No picture yet.")))
                st["after"].append(w.after(2000, tick))
            tick()
            lab(tr("MoveEye looks round once and suggests zones, paths and the things to guard (a few minutes). Then come back here."))
            r = row(); self._fbtn(r, tr("📐 Set up the place"), self._place, primary=True).pack(side="left")
            self._fbtn(r, tr("📷 Choose the camera"), lambda: self._open_page("/cams")).pack(side="left", padx=(6, 0))
        elif c == "view":
            lab(tr("Who should see «Simple» - and what is MoveEye for?"))
            sv_ = tk.BooleanVar(value=bool(CFG.get("ui_simple")))
            for v_, n_ in ((True, "Simple"), (False, "Expert")):
                tk.Radiobutton(body, text=tr(n_), variable=sv_, value=v_, bg=C["bg"], fg=C["txt"], selectcolor=C["field"], activebackground=C["bg"], anchor="w").pack(fill="x")
            lab(tr("Default of every page (each page can switch by itself)."))
            uses = [("camping", "Camping: tent, caravan"), ("home", "House and garden"), ("wild", "Watching animals"), ("holiday", "Holiday house, alpine hut"),
                    ("room", "In the room: wake-up alarm"), ("", "everything (not chosen)")]
            ttk.Label(body, text=tr("What is MoveEye for?")).pack(anchor="w", pady=(6, 0))
            uc = ttk.Combobox(body, state="readonly", values=[tr(n_) for _v, n_ in uses]); uc.pack(fill="x")
            uc.current(next((i for i, (v_, _n) in enumerate(uses) if v_ == (CFG.get("use_case") or "")), 5))
            nxt["fn"] = lambda: g2_action({"action": "view", "simple": sv_.get(), "use": uses[uc.current()][0]}, "window")[0]
        elif c == "zones":
            lab(tr("Draw areas into the picture: ignore the road, privacy, the sleeping place for the wake-up alarm, a line."))
            r = row(); self._fbtn(r, tr("✏ Draw the zones"), lambda: self._open_page("/zones"), primary=True).pack(side="left")
        elif c == "protect":
            l_p = lab("", False)
            l_w = lab("")

            def ptick():
                if not w.winfo_exists():
                    return
                v = protect_status()
                bad = [x["text"] for x in v.get("items", []) if not x.get("ok")]
                l_p.config(text=tr("State of the protection") + ": " + (tr("Still missing:") + "\n• " + "\n• ".join(bad) if bad else tr("Everything ready.")))
                ws = walktest_state()
                l_w.config(text=(f"⏱ {ws['left'] // 60}:{ws['left'] % 60:02d} {tr('left')} · {ws['n_det']} × {tr('recognised')}" if ws["on"]
                                 else ("✓ " + ws["result"]["text"] if ws.get("result") else "")))
                st["after"].append(w.after(1500, ptick))
            lab(tr("Walk past the camera like a visitor - MoveEye beeps at every detection. 3 minutes, no alarms meanwhile."))
            r = row()
            self._fbtn(r, tr("🚶 Start walk test"), lambda: walktest_start("window"), primary=True).pack(side="left")
            self._fbtn(r, tr("■ Stop"), lambda: walktest_stop("button")).pack(side="left", padx=(6, 0))
            lab(tr("Switch on now?") + " (" + tr("switches on at once (with the countdown)") + ")", False)
            r = row()
            for k, n in (("off", "Leave it off"), ("watch", "Watchful"), ("full", "Full")):
                self._fbtn(r, tr(n), lambda k=k: self._protect(k)).pack(side="left", padx=(0, 6))
            ptick()
        elif c == "schedules":
            toggle(tr("Night report in the morning"), "report_on")
            ttk.Label(body, text=tr("End of the night time") + " (" + tr("o'clock") + ")").pack(anchor="w", pady=(6, 0))
            hv = tk.IntVar(value=int(CFG.get("report_hour", 7)))
            sp_ = ttk.Spinbox(body, from_=3, to=12, textvariable=hv, width=5, command=lambda: self._set("report_hour", int(hv.get()))); sp_.pack(anchor="w")
            lab(tr("Schedules switch features by themselves, e.g. the protection every night."))
            r = row(); self._fbtn(r, tr("🕘 Schedules"), lambda: self._tab("protect")).pack(side="left")
        elif c == "lightsiren":
            hw = G["hw"]; r = row()
            if hw.get("light"):
                for nm_, txt in (("white", "💡 Light 3 s"), ("ir", "🌙 Infrared 3 s")):
                    self._fbtn(r, tr(txt), lambda n=nm_: (light_set(n, "on"), w.after(3000, lambda: light_set(n, "auto")))).pack(side="left", padx=(0, 6))
            if hw.get("speaker"):
                self._fbtn(r, tr("🔊 Test sound"), lambda: sound_play(None, 2.5, None, "test")).pack(side="left", padx=(0, 6))
                self._fbtn(r, tr("🚨 Siren 2 s"), lambda: (sound_play(None, None, None, reason="by hand (window)"), w.after(2000, sound_stop))).pack(side="left")
                lab(tr("Loud! Warn the neighbours first."))
        elif c == "servos":
            r = row()
            self._fbtn(r, tr("◎ Centre"), lambda: move_camera("center")).pack(side="left", padx=(0, 6))
            self._fbtn(r, tr("◀ ▶ Turn a little"), lambda: (move_camera("left", 8), w.after(900, lambda: move_camera("right", 8)), w.after(1800, lambda: move_camera("center")))).pack(side="left")
            lab(tr("Direction of turning wrong? Swap it:"))
            toggle(tr("Invert pan direction"), "invert_pan"); toggle(tr("Invert tilt direction"), "invert_tilt")
            r = row(); self._fbtn(r, tr("🛠 Servos: test and positions"), lambda: self._srv_win("test")).pack(side="left")
        elif c == "ai":
            lab(tr("The AI says «person», «animal», «car». It runs on the Pi or on a helper PC."))
            toggle(tr("AI detection"), "ai_enabled"); lab("🤖 " + str(STATE.get("ai_status") or ""))
        elif c == "thermal":
            toggle(tr("Thermal picture over the live picture"), "thermal_on"); toggle(tr("Alarm from the thermal camera"), "thermal_alarm")
            lab("🌡 " + str(STATE.get("thermal") or ""))
        elif c == "battery":
            b = STATE.get("battery") or {}
            if b.get("on"):
                lab(f"🔋 {b.get('pct', '–')} % {tr('charge')}", False)
            if b.get("src") != "ups":                    # no UPS HAT: a powerbank? (it cannot be detected)
                ttk.Label(body, text=tr("Powerbank capacity") + " (mAh, 0 = " + tr("no battery") + ")").pack(anchor="w", pady=(6, 0))
                mv = tk.IntVar(value=int(CFG.get("batt_mah") or 0))
                ttk.Spinbox(body, from_=0, to=60000, increment=1000, textvariable=mv, width=8,
                            command=lambda: self._set("batt_mah", int(mv.get()))).pack(anchor="w")
                r = row(); self._fbtn(r, tr("🔋 Charged full now"), battery_full).pack(side="left")
            toggle(tr("Battery saving automatic"), "batt_save_on")
        elif c == "sim":
            lab(tr("The 3D simulator on the PC tests MoveEye without the real place. Optional."))
            su = entry(tr("Address of the simulator"), CFG.get("sim_url") or "")
            res = lab("")

            def conn():
                ok, err = set_text("sim_url", su.get().strip())
                if ok:
                    ok, err = sim_set(True, "window", True)
                res.config(text=("✓ " + tr("Connecting …")) if ok else "⚠ " + tr_err(err))
            r = row(); self._fbtn(r, tr("🔌 Connect"), conn).pack(side="left")
        elif c == "tours":
            toggle(tr("Tour of a page on its first visit"), "tours_auto"); toggle(tr("Tip of the day"), "tip_of_day"); toggle(tr("Show Blinki"), "blinki_on")
            r = row(); self._fbtn(r, tr("↺ Reset all tours"), lambda: g2_action({"action": "tours_reset"}, "window")).pack(side="left")

        def go_next():
            if nxt["fn"] is not None and nxt["fn"]() is False:
                return
            g2_action({"action": "done", "id": c}, "window"); move(1)
        self._fbtn(foot, tr("Next") + " ›", go_next, primary=True).pack(side="right")
        self._fbtn(foot, tr("Skip"), lambda: (g2_action({"action": "skip", "id": c}, "window"), move(1))).pack(side="right", padx=(0, 6))
        self._fbtn(foot, "‹ " + tr("Back"), lambda: move(-1)).pack(side="left")
    render()


def _g2_tk_first(self):
    """the first start (not set up yet): the guide; the QR codes for the phone come at its end"""
    if not CFG["setup_done"] and not CFG["lock_on"]:
        self._g2_wizard()


def _g2_tk_tip(self):
    """tip of the day in the window (once a day, a function not used yet)"""
    x = g2_tip_today()
    if not x:
        return
    g2_tip_seen(x["id"])
    w = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Tip of the day")); w.configure(bg=C["bg"]); w.transient(self.root)
    tk.Label(w, text="☀ " + tr("Tip of the day").upper(), bg=C["bg"], fg=C["yel"], font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 0))
    tk.Label(w, text=x["icon"] + " " + x["title"], bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 12, "bold"), anchor="w").pack(fill="x", padx=14)
    tk.Label(w, text=x["text"], bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), wraplength=380, justify="left", anchor="w").pack(fill="x", padx=14, pady=(4, 8))
    bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=14, pady=(0, 12))
    self._fbtn(bf, tr("Show me") + " ›", lambda: (w.destroy(), self._open_page(x["href"])), primary=True).pack(side="left")
    self._fbtn(bf, tr("Not now"), w.destroy).pack(side="left", padx=(6, 0))
    self._fbtn(bf, tr("Tip of the day off"), lambda: (self._set("tip_of_day", False), w.destroy())).pack(side="left", padx=(6, 0))


_g2_tab_before = App._tab
# wraps: App._tab


def _g2_tk_tab(self, tid):
    _g2_tab_before(self, tid)
    self.root.after(900, lambda: self._g2_tour(tid))


_g2_run_before = App.run
# wraps: App.run


def _g2_tk_run(self):
    self.root.after(4000, lambda: self._g2_tour(self.tab))
    self.root.after(25000, self._g2_tip)
    _g2_run_before(self)


for _n, _f in (("_g2_tk_widget", _g2_tk_widget), ("_g2_tour", _g2_tk_tour), ("_g2_q", _g2_tk_q), ("_g2_factory", _g2_tk_factory),
               ("_g2_wizard", _g2_tk_wizard), ("_g2_first", _g2_tk_first), ("_g2_tip", _g2_tk_tip),
               ("_tab", _g2_tk_tab), ("run", _g2_tk_run)):
    setattr(App, _n, _f)
