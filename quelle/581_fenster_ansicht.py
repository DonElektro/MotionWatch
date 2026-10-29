#@ MoveEye – Teil 581: Fenster – «Ansicht» des Reiters Live wie auf der Webseite (Vorlagen, Anordnung, Bildgrösse, Grösse, Lieblingsknöpfe, Karten, Joystick). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.29 (Wunsch Daniel «Fenster nachziehen»): the window gets the same «Ansicht» as the live page of the web (536):
#   presets Nur schauen / Bedienen / Einrichten, layout automatic / portrait / landscape, picture size, «Grösse» (UI scale,
#   Tk scaling: all fonts + joystick + tiles), favourites (max. 8) + «… mehr», order and hidden quick switches, cards
#   (Bedienung, Einrichten), joystick only with a pan / tilt head (option always / never). Stored in the settings of the
#   window (CFG tk_live_view = this device). «Für alle Geräte übernehmen» = the same default on MoveEye as the web
#   (CFG qs_layout, 290). The window had its own «✎ Anpassen» before - it is gone (one way to arrange).
# ----------------------------------------------------------------------------
TKV_DEF = {"layout": "auto", "size": 60, "ui": "auto", "joy": "auto", "favs": None, "qorder": None, "qhide": None,
           "more": False, "preset": "", "hide": None}
TKV_FAV = ["rec", "photo", "track", "patrol", "white", "ir", "therm", "sim"]       # like the web (listening is only in the browser)
CFG.setdefault("tk_live_view", dict(TKV_DEF))


def tkv():
    """the «Ansicht» of the window, checked (old or broken values = the standard)"""
    d = CFG.get("tk_live_view") if isinstance(CFG.get("tk_live_view"), dict) else {}
    v = dict(TKV_DEF)
    ids = lambda x: [str(i) for i in x if isinstance(i, str) and re.fullmatch(r"[a-z0-9_]{1,20}", i)][:60] if isinstance(x, list) else None
    v["layout"] = d.get("layout") if d.get("layout") in ("auto", "port", "land") else "auto"
    try:
        v["size"] = max(0, min(100, int(d.get("size", 60))))
    except (TypeError, ValueError):
        pass
    try:
        v["ui"] = "auto" if d.get("ui", "auto") == "auto" else max(60, min(160, int(d.get("ui"))))
    except (TypeError, ValueError):
        v["ui"] = "auto"
    v["joy"] = d.get("joy") if d.get("joy") in ("auto", "on", "off") else "auto"
    for k in ("favs", "qorder", "qhide", "hide"):
        v[k] = ids(d.get(k))
    v["more"] = bool(d.get("more")); v["preset"] = d.get("preset") if d.get("preset") in ("look", "operate", "setup") else ""
    return v


def tkv_set(**kw):
    v = tkv(); v.update(kw); CFG["tk_live_view"] = v; save_settings()
    return v


def _tkv_shared():
    return qs_layout_clean(CFG.get("qs_layout"))


def tkv_qs_state(items):
    """(order of the ids, hidden ids, favourites) - own of the window, else the default for all devices, else the standard"""
    v, sh = tkv(), _tkv_shared()
    ids = [q["id"] for q in items]
    hid = v["qhide"] if v["qhide"] is not None else list(sh.get("hidden") or [])
    favs = v["favs"] if v["favs"] is not None else (list(sh["favs"]) if sh.get("favs") else list(TKV_FAV))
    favs = [f for f in favs if f not in hid and f in ids][:8]
    order = v["qorder"] if v["qorder"] is not None else (list(sh.get("order") or []) or list(favs))
    pos = {k: i for i, k in enumerate(order)}
    ids = [x for _i, x in sorted(enumerate(ids), key=lambda p: pos.get(p[1], len(order) + p[0]))]
    return ids, hid, favs


def tkv_hidden_cards():
    v = tkv()
    if v["hide"] is not None:
        return v["hide"]
    ch = _tkv_shared().get("chide")
    return [k for k in ch if k in ("controls", "lvsetup")] if isinstance(ch, list) else ["lvsetup"]


def _tkv_qs_list(self):
    """the quick switches of the window + «Kalibrieren» when there is no pan / tilt head (it needs none; with a head it is
    in the controls beside the joystick)"""
    q = App._tkv_qs_list_orig(self)
    if not self._tk_head():
        q.append(dict(id="recal", ic="↻", lb=tr("Calibrate"), tip=tr("Learn the picture again (after moving the camera)"),
                      on=lambda: False, go=self._recal, flash=True))
    return q


def _tkv_tiles(self, head):
    """the tiles in the controls: favourites (in the order of the list), «… mehr» opens the others"""
    items = {q["id"]: q for q in self._qs_list() if head or q["id"] not in ("track", "patrol")}
    ids, hid, favs = tkv_qs_state(list(items.values()))
    more = tkv()["more"]
    out = [items[i] for i in ids if i in items and i not in hid and (more or i in favs)]
    rest = [i for i in ids if i in items and i not in hid and i not in favs]
    if rest or more:
        out.append(dict(id="more", ic="…", lb=tr("less" if more else "more"), tip=tr("Show only the favourites" if more else "Show all quick switches"),
                        on=lambda: False, go=self._tkv_more))
    return out


def _tkv_more(self):
    tkv_set(more=not tkv()["more"]); self._tkv_redraw()


def _tk_head(self):
    j = tkv()["joy"]
    return True if j == "on" else False if j == "off" else live_has_head()


def _tk_ui(self):
    u = tkv()["ui"]
    if u != "auto":
        return u / 100.0
    try:
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
    except Exception:
        return 1.0
    return 1.15 if w >= 2400 and h >= 1300 else 1.0      # a big screen (4K, 1440p) a bit bigger


def _tkv_card(self, key):
    return key not in tkv_hidden_cards()


def _tkv_pic_weight(self):
    """portrait: how much of the spare height the picture gets (Bildgrösse 0 … 100 → 30 … 100 %)"""
    return int(30 + tkv()["size"] * 0.7)


def _tkv_side_w(self):
    """landscape: width of the controls column (Bildgrösse: larger picture = narrower column; «Grösse» makes it wider)"""
    W = self._win_w() - 40
    share = 0.5 + tkv()["size"] / 100 * 0.35
    return int(max(300, min(W * 0.6, (1 - share) * W * self._tk_ui())))


def _tkv_live_land(self, w=None, h=None):
    lay = tkv()["layout"]
    if lay == "port":
        return False
    if lay == "land":
        try:
            ww = w or self.root.winfo_width()
            ww = ww if ww > 50 else self.root.winfo_screenwidth()
        except Exception:
            return True
        return ww >= 700
    return App._tkv_land_orig(self, w, h)


def _tkv_setup_card(self, parent):
    """«Einrichten» (preset «Einrichten»): only links, no second copy of a control - like the web card"""
    c = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=8)
    tk.Label(c, text="🛠 " + tr("Set up"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
    tk.Label(c, text=tr("Draw where MoveEye should watch, then check the range with the walk test."), bg=C["panel"], fg=C["mut"],
             font=("DejaVu Sans", 8), wraplength=340, justify="left", anchor="w").pack(fill="x", pady=(2, 6))
    r = tk.Frame(c, bg=C["panel"]); r.pack(fill="x")
    self._fbtn(r, "✏️ " + tr("Draw the zones"), lambda: self._open_page("/zones")).pack(side="left", fill="x", expand=True)
    self._fbtn(r, "🚶 " + tr("Walk test"), self._walktest).pack(side="left", fill="x", expand=True, padx=(6, 0))
    return c


def _tkv_redraw(self, full=False):
    if full:
        self._schedule_rebuild(); return
    if self.tab == "live" and self.left_f is not None and self.left_f.winfo_exists():
        tid, self.tab = self.tab, None
        self._tab(tid)


def _tkv_build(self):
    """«Grösse»: tk scaling = all fonts (in points) bigger or smaller; the joystick and the tiles follow (570)"""
    try:
        if not hasattr(self, "_tk_base_scaling"):
            self._tk_base_scaling = float(self.root.tk.call("tk", "scaling"))
        self.root.tk.call("tk", "scaling", self._tk_base_scaling * self._tk_ui())
    except Exception:
        pass
    return App._tkv_build_orig(self)


TKV_PRESETS = {"look": ("👁", "Just watching", "big picture"), "operate": ("🕹", "Operating", "everything"), "setup": ("🛠", "Setting up", "walk test, zones")}


def _tkv_preset(self, k):
    if k == "look":
        v = dict(size=100, more=False, hide=["lvsetup"]); fold = True
    elif k == "operate":
        v = dict(size=60, hide=["lvsetup"]); fold = False
    else:
        v = dict(size=40, hide=[]); fold = False
    v["preset"] = k; tkv_set(**v)
    self.open_secs.discard("ctl:folded"); self.open_secs.discard("ctl:open"); self.open_secs.add("ctl:folded" if fold else "ctl:open")
    if "controls" in CFG["ui_hidden"]:
        CFG["ui_hidden"] = [x for x in CFG["ui_hidden"] if x != "controls"]
    CFG["ui_open"] = sorted(self.open_secs); save_settings()
    self._status_line(("✓ " + TKV_PRESETS[k][0] + " " + tr(TKV_PRESETS[k][1])))
    self._tkv_redraw()


def _tkv_status_line(self, txt):
    try:
        if getattr(self, "_tkv_msg", None) is not None and self._tkv_msg.winfo_exists():
            self._tkv_msg.config(text=txt)
    except Exception:
        pass


def _tkv_share(self):
    if not messagebox.askyesno("MoveEye", tr("Use this arrangement (favourites, order, hidden switches and cards) for all devices that have no own arrangement?")):
        return
    items = self._qs_list()
    ids, hid, favs = tkv_qs_state(items)
    sh = _tkv_shared()
    order = ids + [x for x in (sh.get("order") or []) if x not in ids]          # switches only the web has (listen, talk …) keep their place
    hidden = hid + [x for x in (sh.get("hidden") or []) if x not in ids and x not in hid]
    chide = [x for x in (sh.get("chide") or ["lvsetup"]) if x not in ("controls", "lvsetup")] + tkv_hidden_cards()
    qs_layout_set(order, hidden, favs, sh.get("cards"), chide)
    tkv_set(favs=None, qorder=None, qhide=None, hide=None)              # the window follows the default from now on
    self._status_line("✓ " + tr("Saved on MoveEye for all devices")); self._tkv_redraw()


def _tkv_reset(self):
    if not messagebox.askyesno("MoveEye", tr("Back to the standard view of the live page?")):
        return
    ui = tkv()["ui"]; CFG["tk_live_view"] = dict(TKV_DEF, ui=ui); save_settings()
    self._tkv_redraw()


def _tkv_dialog(self):
    """the «Ansicht» window: everything at once, each change is shown right away"""
    old = getattr(self, "_tkv_top", None)
    try:
        if old is not None and old.winfo_exists():
            old.lift(); return
    except Exception:
        pass
    top = tk.Toplevel(self.root); self._tkv_top = top
    top.title(tr("View of the live page")); top.configure(bg=C["panel"]); top.transient(self.root)
    P = dict(bg=C["panel"])
    cv = tk.Canvas(top, bg=C["panel"], highlightthickness=0, bd=0, width=440, height=min(760, max(420, self.root.winfo_screenheight() - 140)))
    sb = ttk.Scrollbar(top, orient="vertical", command=cv.yview); cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
    body = tk.Frame(cv, **P); cv.create_window((0, 0), window=body, anchor="nw")
    body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))

    def h(txt):
        tk.Label(body, text=txt.upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", padx=12, pady=(10, 3))

    def note(txt):
        tk.Label(body, text=txt, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8), anchor="w", justify="left", wraplength=410).pack(fill="x", padx=12)

    def seg(opts, cur, fn):
        f = tk.Frame(body, **P); f.pack(fill="x", padx=12)
        for i, (val, lb) in enumerate(opts):
            on = cur == val
            b = self._fbtn(f, tr(lb), lambda val=val: (fn(val), redraw()), primary=on)
            b.grid(row=0, column=i, sticky="ew", padx=(0, 6)); f.columnconfigure(i, weight=1)
        return f

    def redraw(full=False):
        try:
            top.destroy()
        except Exception:
            pass
        self._tkv_redraw(full)
        self.root.after(300 if full else 60, self._tkv_dialog)

    v = tkv()
    h(tr("Ready-made views"))
    pf = tk.Frame(body, **P); pf.pack(fill="x", padx=12)
    for i, (k, (ic, lb, d)) in enumerate(TKV_PRESETS.items()):
        b = self._fbtn(pf, f"{ic} {tr(lb)}\n{tr(d)}", lambda k=k: (self._tkv_preset(k), redraw()), primary=v["preset"] == k)
        b.grid(row=0, column=i, sticky="ew", padx=(0, 6)); pf.columnconfigure(i, weight=1)
    h(tr("Layout"))
    seg([("auto", "Automatic"), ("port", "Portrait"), ("land", "Landscape")], v["layout"], lambda x: tkv_set(layout=x, preset=""))
    note(tr("Now") + ": " + tr("picture left, cards right" if self._tk_live_land() else "picture on top, cards below"))
    h(tr("Picture size"))
    sz = tk.Scale(body, from_=0, to=100, resolution=5, orient="horizontal", showvalue=False, bg=C["panel"], fg=C["txt"], troughcolor=C["line"],
                  highlightthickness=0, bd=0)
    sz.set(v["size"]); sz.pack(fill="x", padx=12)
    sz.bind("<ButtonRelease-1>", lambda e: (tkv_set(size=int(sz.get()), preset=""), self._tkv_redraw()))
    note(tr("Landscape: how wide the picture is next to the cards (it never gets higher than the window)." if self._tk_live_land() else "Portrait: how high the picture may be."))
    h(tr("Size of text and buttons"))
    uis = [("auto", "Automatic")] + [(n, f"{n} %") for n in (60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160)]
    cb = ttk.Combobox(body, values=[tr(lb) if val == "auto" else lb for val, lb in uis], state="readonly", width=14)
    cb.current(next((i for i, (val, _l) in enumerate(uis) if val == v["ui"]), 0)); cb.pack(anchor="w", padx=12)
    cb.bind("<<ComboboxSelected>>", lambda e: (tkv_set(ui=uis[cb.current()][0]), redraw(True)))
    note(tr("Like a resolution: everything except the picture gets smaller or bigger (only on this device)."))
    h(tr("Joystick"))
    seg([("auto", "Automatic"), ("on", "Always"), ("off", "Never")], v["joy"], lambda x: tkv_set(joy=x))
    if v["joy"] == "auto":
        note(tr("Automatic") + ": " + tr("pan / tilt head found" if live_has_head() else "no pan / tilt head found"))
    h(tr("Quick switches") + " · " + tr("Favourite buttons (4–8)"))
    items = [q for q in self._qs_list()]
    names = {q["id"]: f"{q['ic']}  {q['lb']}" for q in items}
    ids, hid, favs = tkv_qs_state(items)
    qf = tk.Frame(body, **P); qf.pack(fill="x", padx=12)

    def fav(i):
        F = list(favs)
        if i in F:
            F.remove(i)
        elif len(F) >= 8:
            messagebox.showinfo("MoveEye", "★ " + tr("At most 8 favourites")); return
        else:
            F.append(i)
        tkv_set(favs=F, qhide=[x for x in hid if x != i], preset=""); redraw()

    def hide(i):
        H = [x for x in hid if x != i] + ([] if i in hid else [i])
        tkv_set(qhide=H, favs=[x for x in favs if x not in H], preset=""); redraw()

    def mv(i, d):
        L = list(ids); a = L.index(i); b = a + d
        if 0 <= b < len(L):
            L[a], L[b] = L[b], L[a]; tkv_set(qorder=L, preset=""); redraw()
    for n, i in enumerate(ids):
        row = tk.Frame(qf, **P); row.pack(fill="x", pady=1)
        self._fbtn(row, "★" if i in favs else "☆", lambda i=i: fav(i), tr("Favourite (shown without «… more»)"),
                   font=("DejaVu Sans", 11)).pack(side="left")
        tk.Label(row, text=names[i], bg=C["panel"], fg=C["mut"] if i in hid else C["txt"], font=("DejaVu Sans", 9, "overstrike" if i in hid else "normal"),
                 anchor="w").pack(side="left", fill="x", expand=True, padx=6)
        self._fbtn(row, "✕" if i not in hid else "👁", lambda i=i: hide(i), tr("Hide / show")).pack(side="right")
        self._fbtn(row, "▼", lambda i=i: mv(i, 1), tr("Down")).pack(side="right", padx=(0, 4))
        self._fbtn(row, "▲", lambda i=i: mv(i, -1), tr("Up")).pack(side="right", padx=(0, 4))
    note(tr("★ = always visible, the others behind «… more». ✕ hides a switch on this device."))
    h(tr("Cards"))
    ch = tkv_hidden_cards()
    for key, lb in (("controls", "Controls"), ("lvsetup", "Set up")):
        bv = tk.BooleanVar(value=key not in ch and (key != "controls" or self.is_shown("controls")))

        def tog(key=key, bv=bv):
            H = [x for x in tkv_hidden_cards() if x != key] + ([] if bv.get() else [key])
            if key == "controls" and bv.get() and "controls" in CFG["ui_hidden"]:
                CFG["ui_hidden"] = [x for x in CFG["ui_hidden"] if x != "controls"]
            tkv_set(hide=H, preset=""); redraw()
        tk.Checkbutton(body, text=tr(lb), variable=bv, command=tog, bg=C["panel"], fg=C["txt"], selectcolor=C["field"], activebackground=C["panel"],
                       anchor="w").pack(fill="x", padx=12)
    bf = tk.Frame(body, **P); bf.pack(fill="x", padx=12, pady=(14, 4))
    self._fbtn(bf, "📲 " + tr("Use for all devices"), lambda: (self._tkv_share(), redraw()), tr("Store this arrangement on MoveEye as the default for devices without an own arrangement")).pack(side="left", fill="x", expand=True)
    self._fbtn(bf, tr("Reset"), lambda: (self._tkv_reset(), redraw())).pack(side="left", padx=(6, 0))
    self._fbtn(bf, tr("Close"), top.destroy, primary=True).pack(side="left", padx=(6, 0))
    own = any(v[k] is not None for k in ("favs", "qorder", "qhide", "hide"))
    sh = _tkv_shared(); shon = bool(sh.get("order") or sh.get("hidden") or sh.get("favs"))
    note(tr("This window has its own arrangement. «Reset» = back to the arrangement for all devices." if own else
            "This window uses the arrangement for all devices (stored on MoveEye). A change makes it its own." if shon else
            "Stored in the settings of this window."))
    self._tkv_msg = tk.Label(body, text="", bg=C["panel"], fg=C["grn"], font=("DejaVu Sans", 9), anchor="w"); self._tkv_msg.pack(fill="x", padx=12, pady=(4, 10))


App._tkv_qs_list_orig = App._qs_list
# wraps: App._qs_list
App._qs_list = _tkv_qs_list
App._tkv_land_orig = App._tk_live_land
# wraps: App._tk_live_land
App._tk_live_land = _tkv_live_land
App._tkv_build_orig = App._build
# wraps: App._build
App._build = _tkv_build
for _n, _f in (("_tkv_tiles", _tkv_tiles), ("_tkv_more", _tkv_more), ("_tk_head", _tk_head), ("_tk_ui", _tk_ui), ("_tkv_card", _tkv_card),
               ("_tkv_pic_weight", _tkv_pic_weight), ("_tkv_side_w", _tkv_side_w), ("_tkv_setup_card", _tkv_setup_card),
               ("_tkv_redraw", _tkv_redraw), ("_tkv_preset", _tkv_preset), ("_status_line", _tkv_status_line), ("_tkv_share", _tkv_share),
               ("_tkv_reset", _tkv_reset), ("_tkv_dialog", _tkv_dialog)):
    setattr(App, _n, _f)
