#@ MoveEye – Teil 582: Fenster «Platz einrichten» (wie /place im Web) und «Blickwinkel der Kamera» im Abschnitt Kamera / Servos. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30: the same three steps as the web page: look around (start, progress, cancel), mark on the panorama (tap a
# suggestion or draw a box with the mouse, kind buttons), apply + walk test. Button in Schutz → «Camping / protection».
# ----------------------------------------------------------------------------
PLACE_TK_KINDS = (("tent", "⛺", "My tent / camper", "#ff5a5a"), ("access", "🚶", "Access / path", "#ffb020"),
                  ("valuable", "🚲", "Valuables", "#3cc8ff"), ("ignore", "🌿", "Ignore", "#8fd18f"))
PLACE_TK_COL = {k: c for k, _i, _n, c in PLACE_TK_KINDS}
PLACE_TK_COL["public_path"] = "#c9a0ff"
PLACE_TK_ICON = {k: i for k, i, _n, _c in PLACE_TK_KINDS}
PLACE_TK_ICON["public_path"] = "🛣"


def _app_place(self):
    win = getattr(self, "_pl_win", None)
    try:
        if win is not None and win.winfo_exists():
            win.lift(); return
    except Exception:
        pass
    win = tk.Toplevel(self.root); self._pl_win = win
    win.title("MoveEye – " + tr("Set up the place")); win.geometry("820x860")
    S = {"items": [], "taken": set(), "tool": tk.StringVar(win, ""), "sel": -1, "scale": 1.0, "geo": None, "img": None, "drag": None,
         "scan_v": None, "busy": False}
    top = ttk.Frame(win); top.pack(fill="x", padx=12, pady=(10, 4))
    intro = ttk.Label(top, text="", wraplength=780, justify="left"); intro.pack(anchor="w")
    of = ttk.Frame(top); of.pack(fill="x", pady=(4, 0))
    v_wide, v_rows, v_ir, v_th = tk.BooleanVar(win, True), tk.BooleanVar(win, False), tk.BooleanVar(win, True), tk.BooleanVar(win, True)
    cb_wide = ttk.Checkbutton(of, variable=v_wide, text="")
    ttk.Checkbutton(of, variable=v_rows, text=tr("Thorough: 3 rows instead of 2 (takes longer)")).pack(anchor="w")
    hfr = ttk.Frame(of); hfr.pack(anchor="w", pady=(4, 0))          # real-reh-fusspunkt: «Höhe der Kamera (m)» (232 cam_height)
    v_camh = tk.StringVar(win, "%.2f" % cam_height_cfg())

    def camh_set(*_a):
        try:
            v_ = round(float(v_camh.get().replace(",", ".")), 2)
        except ValueError:
            return
        if 0.2 <= v_ <= 10.0 and v_ != CFG.get("cam_height"):
            CFG["cam_height"] = v_; save_settings()
            self._status("Camping / protection", "📏 " + tr("Camera height (m)") + f": {v_:.2f}")
    sp = ttk.Spinbox(hfr, from_=0.2, to=10.0, increment=0.05, textvariable=v_camh, width=6, command=camh_set)
    sp.pack(side="left"); sp.bind("<FocusOut>", camh_set); sp.bind("<Return>", camh_set)
    ttk.Label(hfr, text=" " + tr("Camera height (m)")).pack(side="left")
    _ci = cam_height_info()
    ttk.Label(of, style="Mut.TLabel", wraplength=760, justify="left",
              text=tr("Height of the lens above the ground - helps to tell animals from persons at night.")
              + ((" " + trf("Simulator: pole {m} m - counts while connected", m="%.2f" % _ci["sim"])) if _ci["sim"] else "")).pack(anchor="w")
    cb_ir = ttk.Checkbutton(of, variable=v_ir, text=tr("with the infrared light"))
    cb_th = ttk.Checkbutton(of, variable=v_th, text=tr("with the thermal camera too"))
    bf = ttk.Frame(top); bf.pack(fill="x", pady=(6, 0))
    prog = ttk.Progressbar(top, maximum=100); prog.pack(fill="x", pady=(6, 0))
    st = ttk.Label(top, text="", font=("TkDefaultFont", 11, "bold")); st.pack(anchor="w", pady=(4, 0))

    def start():
        ok, err = place_start(v_ir.get(), v_th.get(), v_wide.get() and bool(cam_wide_spec()), 3 if v_rows.get() else 2, "window")
        self._status("Camping / protection", ("📍 " + tr("Set up the place")) if ok else "⚠ " + tr(err))
        if not ok:
            st.config(text="⚠ " + tr(err))
    ttk.Button(bf, text="▶ " + tr("Start looking around"), command=start).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="✕ " + tr("Cancel"), command=place_stop).pack(side="left", expand=True, fill="x")
    # ---- the panorama ----
    tf = ttk.Frame(win); tf.pack(fill="x", padx=12, pady=(8, 2))
    for k, ic, nm, _c in PLACE_TK_KINDS + (("", "✋", "Move / select", ""),):
        ttk.Radiobutton(tf, text=ic + " " + tr(nm), value=k, variable=S["tool"]).pack(side="left", padx=(0, 8))
    cf = ttk.Frame(win); cf.pack(fill="x", padx=12)
    cv = tk.Canvas(cf, height=270, background="#111", highlightthickness=0)
    sx = ttk.Scrollbar(cf, orient="horizontal", command=cv.xview); cv.configure(xscrollcommand=sx.set)
    cv.pack(fill="x"); sx.pack(fill="x")
    lf = ttk.Frame(win); lf.pack(fill="both", expand=True, padx=12, pady=(6, 0))
    lb = tk.Listbox(lf, height=7); lb.pack(side="left", fill="both", expand=True)
    ef = ttk.Frame(lf); ef.pack(side="left", fill="y", padx=(8, 0))
    v_name = tk.StringVar(win, ""); v_pub = tk.BooleanVar(win, False)
    ttk.Label(ef, text=tr("Name")).pack(anchor="w")
    en = ttk.Entry(ef, textvariable=v_name, width=24); en.pack(anchor="w")
    cb_pub = ttk.Checkbutton(ef, variable=v_pub, text=tr("public path = only report"))
    cb_pub.pack(anchor="w", pady=(4, 0))
    note = ttk.Label(ef, text="", style="Mut.TLabel", wraplength=230, justify="left"); note.pack(anchor="w", pady=(4, 0))
    v_pat = tk.BooleanVar(win, bool(CFG.get("place_patrol")))
    af = ttk.Frame(win); af.pack(fill="x", padx=12, pady=(6, 10))
    res = ttk.Label(win, text="", wraplength=780, justify="left"); res.pack(anchor="w", padx=12, pady=(0, 8))
    notes = {"tent": "protection zone, lights / siren aim here, a person close by counts more", "access": "line: a person crossing it is reported + patrol point",
             "public_path": "persons there: only a note, no alarm", "valuable": "guarded: in the morning «Bike missing»", "ignore": "mask: movement there is ignored"}

    def px(a, e):
        g = S["geo"]; x = (a - g["a0"]) * g["k"]
        if g.get("wrap") and x < 0:
            x += 360 * g["k"]
        return x * S["scale"], ((g["e_top"] - e) * g["k"] + g.get("head", 0)) * S["scale"]

    def ang(x, y):
        g = S["geo"]; x, y = cv.canvasx(x) / S["scale"], cv.canvasy(y) / S["scale"]
        return g["a0"] + x / g["k"], g["e_top"] - (y - g.get("head", 0)) / g["k"]

    def redraw():
        cv.delete("box")
        scan = place_scan() or {}
        if not S["geo"]:
            return
        for s_ in scan.get("suggest") or []:
            if s_["id"] in S["taken"]:
                continue
            x0, y0 = px(s_["a0"], s_["e1"]); x1, y1 = px(s_["a1"], s_["e0"])
            cv.create_rectangle(x0, y0, x1, y1, outline=PLACE_TK_COL.get(s_["kind"], "#fff"), dash=(6, 4), width=2, tags="box")
            cv.create_text(x0 + 4, y0 + 4, anchor="nw", text="+ " + tr(s_["name"]), fill="#fff", tags="box")
        for i, it in enumerate(S["items"]):
            x0, y0 = px(it["a0"], it["e1"]); x1, y1 = px(it["a1"], it["e0"])
            cv.create_rectangle(x0, y0, x1, y1, outline=PLACE_TK_COL.get(it["kind"], "#fff"), width=4 if i == S["sel"] else 2, tags="box")
            cv.create_text(x0 + 4, y0 + 4, anchor="nw", text=PLACE_TK_ICON.get(it["kind"], "") + " " + it["name"], fill="#fff", tags="box")
        if S["drag"] and S["drag"].get("b"):
            b = S["drag"]["b"]; x0, y0 = px(b["a0"], b["e1"]); x1, y1 = px(b["a1"], b["e0"])
            cv.create_rectangle(x0, y0, x1, y1, outline="#fff", width=2, tags="box")
        lb.delete(0, "end")
        for it in S["items"]:
            lb.insert("end", PLACE_TK_ICON.get(it["kind"], "") + " " + it["name"])
        if 0 <= S["sel"] < len(S["items"]):
            lb.selection_clear(0, "end"); lb.selection_set(S["sel"])

    def select(i):
        S["sel"] = i
        if 0 <= i < len(S["items"]):
            it = S["items"][i]
            v_name.set(it["name"]); v_pub.set(it["kind"] == "public_path")
            note.config(text=tr(notes.get(it["kind"], "")))
        redraw()

    def take(s_, kind=None):
        if s_["id"] in S["taken"]:
            return
        S["taken"].add(s_["id"])
        S["items"].append({"kind": kind or s_["kind"], "name": tr(s_["name"]), "a0": s_["a0"], "a1": s_["a1"], "e0": s_["e0"], "e1": s_["e1"]})

    def hit(lst, a, e):
        for i in range(len(lst) - 1, -1, -1):
            if _place_in(lst[i], a, e):
                return i
        return -1

    def down(ev):
        if S["geo"]:
            S["drag"] = {"x": ev.x, "y": ev.y, "b": None}
            if not S["tool"].get():
                cv.scan_mark(ev.x, 0)

    def move(ev):
        D = S["drag"]
        if not D:
            return
        if not S["tool"].get():
            cv.scan_dragto(ev.x, 0, gain=1); return
        a0, e1 = ang(min(D["x"], ev.x), min(D["y"], ev.y)); a1, e0 = ang(max(D["x"], ev.x), max(D["y"], ev.y))
        D["b"] = {"a0": a0, "a1": a1, "e0": e0, "e1": e1}; redraw()

    def up(ev):
        D, S["drag"] = S["drag"], None
        if not D:
            return
        tool = S["tool"].get()
        if tool and D.get("b") and abs(ev.x - D["x"]) + abs(ev.y - D["y"]) > 12:
            S["items"].append(dict(D["b"], kind=tool, name=tr(dict((k, n) for k, _i, n, _c in PLACE_TK_KINDS)[tool])))
            select(len(S["items"]) - 1); return
        if abs(ev.x - D["x"]) + abs(ev.y - D["y"]) > 12:
            redraw(); return
        a, e = ang(ev.x, ev.y)
        i = hit(S["items"], a, e)
        if i >= 0:
            if tool:
                S["items"][i]["kind"] = tool
            select(i); return
        sg = [s_ for s_ in (place_scan() or {}).get("suggest") or [] if s_["id"] not in S["taken"]]
        j = hit(sg, a, e)
        if j >= 0:
            take(sg[j], tool or None); select(len(S["items"]) - 1)
    cv.bind("<ButtonPress-1>", down); cv.bind("<B1-Motion>", move); cv.bind("<ButtonRelease-1>", up)
    lb.bind("<<ListboxSelect>>", lambda _e: select(lb.curselection()[0]) if lb.curselection() else None)

    def name_changed(*_a):
        if 0 <= S["sel"] < len(S["items"]):
            S["items"][S["sel"]]["name"] = v_name.get()[:40]; redraw()
    v_name.trace_add("write", name_changed)

    def pub_changed(*_a):
        if 0 <= S["sel"] < len(S["items"]) and S["items"][S["sel"]]["kind"] in ("access", "public_path"):
            S["items"][S["sel"]]["kind"] = "public_path" if v_pub.get() else "access"; select(S["sel"])
    v_pub.trace_add("write", pub_changed)

    def remove():
        if 0 <= S["sel"] < len(S["items"]):
            S["items"].pop(S["sel"]); S["sel"] = -1; redraw()

    def take_all():
        for s_ in (place_scan() or {}).get("suggest") or []:
            take(s_)
        redraw()

    def apply_():
        ok, err, r = place_apply(S["items"], True, v_pat.get(), "window")
        if not ok:
            res.config(text="⚠ " + tr(err)); return
        res.config(text="✓ " + tr("The place is set up") + " · " + " · ".join(x for x in (
            trf("{n} protection zone(s) at the tent", n=r["tent"]) if r["tent"] else "", trf("{n} line(s) at the accesses", n=r["lines"]) if r["lines"] else "",
            trf("{n} public path(s): only reported", n=r["public"]) if r["public"] else "", trf("{n} mask(s): ignored", n=r["masks"]) if r["masks"] else "",
            trf("{n} patrol point(s)", n=r["waypoints"]) if r["waypoints"] else "",
            trf("{n} guarded thing(s) - reported in the morning when missing", n=r["watched"]) if r["watched"] else "") if x)
            + "\n" + tr("Now test it: walk past like a visitor would. MoveEye beeps at every detection."))

    def forget():
        if messagebox.askyesno("MoveEye", tr("Forget the place? Its zones, waypoints and guarded things are removed."), parent=win):
            place_clear("window"); S["items"] = []; S["taken"] = set(); redraw()
    ttk.Button(ef, text="✕ " + tr("Remove"), command=remove).pack(anchor="w", pady=(6, 0))
    ttk.Button(ef, text="✚ " + tr("Take all suggestions"), command=take_all).pack(anchor="w", pady=(4, 0))
    ttk.Checkbutton(af, variable=v_pat, text="🔁 " + tr("Patrol: the head looks at the accesses now and then")).pack(anchor="w")
    ttk.Button(af, text="✓ " + tr("Apply"), command=apply_).pack(side="left", expand=True, fill="x", padx=(0, 4), pady=(4, 0))
    ttk.Button(af, text="🚶 " + tr("Start the walk test"), command=self._walktest).pack(side="left", expand=True, fill="x", padx=(0, 4), pady=(4, 0))
    ttk.Button(af, text="🗑 " + tr("Forget the place"), command=forget).pack(side="left", expand=True, fill="x", pady=(4, 0))

    def load_pano(scan):
        S["geo"] = scan.get("geo"); S["scan_v"] = scan.get("t")
        rec = _place_load() or {}
        S["items"] = [{k: it[k] for k in ("kind", "name", "a0", "a1", "e0", "e1")} for it in rec.get("items") or [] if "a0" in it] \
            if (rec.get("t") or 0) >= (scan.get("t") or 0) - 1 else []
        S["taken"] = set(); S["sel"] = -1
        try:
            im = cv2.imread(place_dir("scan", "pano.jpg"))
            if im is None:
                return
            S["scale"] = 260.0 / im.shape[0]
            im = cv2.resize(im, (int(im.shape[1] * S["scale"]), 260))
            ok, buf = cv2.imencode(".png", im)
            if ok:
                S["img"] = tk.PhotoImage(data=base64.b64encode(buf.tobytes()).decode())
                cv.delete("all"); cv.create_image(0, 0, anchor="nw", image=S["img"]); cv.configure(scrollregion=(0, 0, im.shape[1], 260))
        except Exception:
            pass
        redraw()

    def tick():
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return
        P_ = place_state()
        pl = P_["plan"]
        cov = tr("the whole circle (360°)") if pl["wrap"] else tr("about") + f" {pl['cover']}°"
        intro.config(text=tr("Put MoveEye where it will guard. The head looks around once: it takes a photo in every direction and watches for about 10 seconds what moves and what the AI recognises. Then you only mark your tent, the access, your valuables and what to ignore.")
                     + "\n" + tr("Pan range of the servo {servo}°, with the lens it sees {cover} (camera {hf}°).").replace("{servo}", str(pl["servo"])).replace("{cover}", cov).replace("{hf}", str(round(pl["hf"])))
                     + ("" if pl["wrap"] else " " + tr("No full turn: the head turns only as far as its servo goes."))
                     + "\n" + tr("{n} directions in {rows} rows - about {min} minutes.").replace("{n}", str(pl["n"])).replace("{rows}", str(pl["rows"])).replace("{min}", str(max(1, round(pl["eta"] / 60)))))
        W_ = P_.get("wide")
        if W_:
            cb_wide.config(text=tr("Use the wide-angle camera ({cam}, {deg}°): {n} directions, about {min} min").replace("{cam}", W_["label"]).replace("{deg}", str(round(W_["hf"])))
                           .replace("{n}", str(W_["n"])).replace("{min}", str(max(1, round(W_["eta"] / 60)))))
            if not cb_wide.winfo_ismapped():
                cb_wide.pack(anchor="w")
        for cb, okk in ((cb_ir, P_["dark"] and P_["ir_ok"]), (cb_th, P_["dark"] and P_["thermal_ok"])):
            if okk and not cb.winfo_ismapped():
                cb.pack(anchor="w")
            elif not okk and cb.winfo_ismapped():
                cb.pack_forget()
        if P_["busy"]:
            S["busy"] = True
            prog["value"] = 100.0 * max(0, P_["step"] - 0.5) / max(1, P_["n"])
            st.config(text="🔄 " + tr("Direction {i} of {n}").replace("{i}", str(P_["step"])).replace("{n}", str(P_["n"]))
                      + f" · {tr('about')} {P_['left'] // 60}:{P_['left'] % 60:02d} {tr('left')}")
        else:
            if S["busy"]:
                S["busy"] = False; prog["value"] = 100 if P_["done_msg"] else 0
            st.config(text=P_["msg"] or (P_["why_not"] and "⚠ " + P_["why_not"]) or "")
            scan = place_scan()
            if scan and scan.get("t") != S["scan_v"]:
                load_pano(scan)
        win.after(1000, tick)
    tick()


def _app_fov_box(self, parent):
    """Camera / Servos: the field of view of every camera (list, own value, «sits on the head»)"""
    box = ttk.Frame(parent); box.pack(fill="x", pady=(8, 0))
    ttk.Label(box, text="📐 " + tr("Field of view of the camera")).pack(anchor="w")
    F = cam_fov_list()
    names = [n for _k, n in F["choices"]]; keys = [k for k, _n in F["choices"]]
    for c in F["cams"]:
        r = ttk.Frame(box); r.pack(fill="x", pady=(4, 0))
        ttk.Label(r, text=(tr("Main camera") if c["main"] else tr("Extra camera")) + ": " + str(c["label"]), style="Mut.TLabel").pack(anchor="w")
        rr = ttk.Frame(r); rr.pack(fill="x")
        cb = ttk.Combobox(rr, values=names, state="readonly", width=34)
        cb.current(keys.index(c["model"]) if c["model"] in keys else 0); cb.pack(side="left")
        v_deg = tk.StringVar(rr, str(c["deg"] or round(c["h"])))
        ent = ttk.Entry(rr, textvariable=v_deg, width=6); ent.pack(side="left", padx=(6, 0))
        info = ttk.Label(r, text=f"{round(c['h'])}° × {round(c['v'])}°", style="Mut.TLabel"); info.pack(anchor="w")
        v_head = tk.BooleanVar(r, bool(c["head"]))

        def send(*_a, c=c, cb=cb, v_deg=v_deg, info=info, v_head=v_head):
            ok, err = cam_fov_set(c["spec"], keys[cb.current()], v_deg.get(), None if c["main"] else v_head.get())
            h, v, _s = cam_fov_hv(c["spec"])
            info.config(text=(f"{round(h)}° × {round(v)}°") if ok else "⚠ " + tr(err))
        cb.bind("<<ComboboxSelected>>", send); ent.bind("<Return>", send); ent.bind("<FocusOut>", send)
        if not c["main"]:
            ttk.Checkbutton(r, variable=v_head, text=tr("sits on the head (turns with it) - for the panorama"), command=send).pack(anchor="w")


App._place = _app_place
App._fov_box = _app_fov_box
