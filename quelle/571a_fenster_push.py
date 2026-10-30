#@ MoveEye – Teil 571a: Fenster «Push-Nachrichten» als Karten (Kopf · Wohin · Was · Wann · Erweitert), gleich aufgebaut wie die Web-Seite (531a). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# The window builds the section «Notifications» itself (the generic list of 570 is skipped for it): the same five blocks
# and channel cards as the web page. The sections «Nachrichtentexte» and «SMS (LTE-Stick)» are shown inside it (message
# texts in «Erweitert», SMS in its card) and therefore leave the group «Was passiert bei Alarm?». Logic: 579a.
# The window has no bell: «Alarmton in geöffneten Browsern» stays here in «Erweitert» (web: in the bell 🔔).
# ----------------------------------------------------------------------------
for _g in TK_GROUPS:
    if _g[0] == "notify":
        for _s in ("Messages", "SMS (LTE stick)"):
            if _s in _g[2]:
                _g[2].remove(_s)

_PX_TK_CH = {"ntfy": ("📲", "ntfy", ("notify_url",)), "webpush": ("🌐", "Web push (this device)", ()),
             "telegram": ("✈", "Telegram", ("telegram_token", "telegram_chat")), "pushover": ("🔔", "Pushover", ("pushover_user", "pushover_token", "pushover_emergency")),
             "email": ("✉", "E-mail", ("email_to",)), "webhook": ("🔗", "Webhook", ("notify_url",)), "sms": ("📱", "SMS", ())}
_PX_TK_ORDER = ("ntfy", "webpush", "telegram", "pushover", "email", "webhook", "sms")
_PX_TK_MSG = (("person", "👤", "Person"), ("prealarm", "👀", "Pre-alarm"), ("warm", "🌡", "Thermal alarm"), ("noise", "🔊", "Noise alarm"))


def _px_tk_label(key):
    for lst in (TOGGLES, TEXTS, SLIDERS):
        for x in lst:
            if x[1] == key:
                return x[2]
    return key


def _px_tk_hide(key):
    return simple_hidden(key) or (CFG["lock_on"] and key in LOCK_DENY_KEYS)


class _PxSeg(tk.Frame):
    """segment switch (the active one blue) - like the segments of the web page and the simulator"""
    def __init__(self, parent, choices, value, command):
        super().__init__(parent, bg=C["line"], padx=1, pady=1)
        self.command = command; self.btn = {}; self.value = None
        for i, (v, lab) in enumerate(choices):
            l = tk.Label(self, text=tr(lab), font=("DejaVu Sans", 9, "bold"), padx=8, pady=3, cursor="hand2")
            l.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 1, 0))
            l.bind("<Button-1>", lambda e, vv=v: self._click(vv))
            self.btn[v] = l
        self.set(value)

    def _click(self, v):
        if v != self.value:
            self.set(v); self.command(v)

    def set(self, value):
        self.value = value
        for v, l in self.btn.items():
            l.config(bg=C["acc"] if v == value else C["field"], fg="#ffffff" if v == value else C["mut"])


def _px_tk_field(app, parent, key, err):
    """one text field: label, entry with a small ✕ (secret: clears after a confirmation)"""
    if key not in TEXT_SPECS or _px_tk_hide(key):
        return None
    kind, _x = TEXT_SPECS[key]
    lab = ttk.Label(parent, text=tr(_px_tk_label(key)), style="Mut.TLabel", wraplength=330, justify="left"); lab.pack(anchor="w", pady=(6, 0))
    app._g2_q(lab, key)
    if kind == "enum":
        pairs = text_choice_pairs(key); labs = dict(pairs); back = {l: c for c, l in pairs}
        cb = ttk.Combobox(parent, values=[l for _c, l in pairs], state="readonly"); cb.set(labs.get(CFG[key], CFG[key])); cb.pack(fill="x", pady=(2, 0))
        cb.bind("<<ComboboxSelected>>", lambda e: (app.root.focus_set(), app._text_set(key, back.get(cb.get(), cb.get()), err)))
        return cb
    var = tk.StringVar(value="" if kind == "secret" else str(text_value(key)))
    row = tk.Frame(parent, bg=C["field"], highlightthickness=1, highlightbackground=C["line"]); row.pack(fill="x", pady=(2, 0))
    ent = tk.Entry(row, textvariable=var, show="•" if kind == "secret" else "", bg=C["field"], fg=C["txt"], insertbackground=C["txt"],
                   relief="flat", highlightthickness=0)
    ent.pack(side="left", fill="x", expand=True, padx=(6, 0), pady=3)
    if kind == "secret" and CFG.get(key):
        tk.Label(row, text="(" + tr("set") + ")", bg=C["field"], fg=C["mut"], font=("DejaVu Sans", 8)).pack(side="left", padx=2)
    for ev in ("<Return>", "<FocusOut>"):
        ent.bind(ev, lambda e: app._text_set(key, var.get(), err) if (kind != "secret" or var.get()) else None)

    def clear():
        if kind == "secret":
            if not messagebox.askyesno("MoveEye", tr("Clear the saved value? It cannot be shown again."), parent=app.root):
                return
        var.set(""); app._text_set(key, "", err)
    x = tk.Label(row, text="✕", bg=C["field"], fg=C["mut"], cursor="hand2", font=("DejaVu Sans", 10), padx=6)
    x.pack(side="right"); x.bind("<Button-1>", lambda e: clear())
    return ent


def _px_tk_toggle(app, parent, key):
    if _px_tk_hide(key) or key not in CFG:
        return None
    tg = Toggle(parent, tr(_px_tk_label(key)), CFG[key], lambda val, k=key: app._set(k, val)); tg.pack(fill="x", pady=3)
    app.vars[key] = tg; app._g2_q(tg, key)
    return tg


def _px_tk_slider(app, parent, spec):
    s, key, label, lo, hi, step = spec
    if _px_tk_hide(key):
        return
    row = ttk.Frame(parent); row.pack(fill="x", pady=(6, 0))
    ttk.Label(row, text=tr(label)).pack(side="left")
    vl = ttk.Label(row, text=str(CFG[key]), style="Mut.TLabel"); vl.pack(side="right"); app.value_labels[key] = vl
    app._g2_q(row, key)
    v = tk.DoubleVar(value=CFG[key]); app.vars[key] = v
    sc = ttk.Scale(parent, from_=lo, to=hi, variable=v, orient="horizontal", command=lambda val, k=key, st=step: app._slide(k, float(val), st))
    sc.pack(fill="x")
    sc.bind("<ButtonPress-1>", lambda e, k=key: setattr(app, "dragging", k))
    sc.bind("<ButtonRelease-1>", lambda e: (setattr(app, "dragging", None), app.root.focus_set()))


def _px_tk_head(parent, text):
    tk.Label(parent, text=tr(text).upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").pack(fill="x", pady=(12, 2))


def _px_tk_card(app, parent, ch, err, S):
    ic, nm, keys = _PX_TK_CH[ch]
    box = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"])
    hd = tk.Frame(box, bg=C["panel"], cursor="hand2"); hd.pack(fill="x", padx=6, pady=3)
    ar = tk.Label(hd, text="▸", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), cursor="hand2"); ar.pack(side="left")
    tk.Label(hd, text=ic, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10), width=2, cursor="hand2").pack(side="left")
    nf = tk.Frame(hd, bg=C["panel"], cursor="hand2"); nf.pack(side="left", fill="x", expand=True)
    tk.Label(nf, text=tr(nm), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10), anchor="w", cursor="hand2").pack(fill="x")
    st = tk.Label(nf, text="", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8), anchor="w", cursor="hand2"); st.pack(fill="x")
    sw = Toggle(hd, "", False, lambda v, c=ch: (push_set_channel(c, v), _px_tk_paint(app)))
    sw.pack(side="right")
    tb = ttk.Button(hd, text="▶ " + tr("Test"), width=7, command=lambda c=ch: _px_tk_test(app, c)); tb.pack(side="right", padx=4)
    body = tk.Frame(box, bg=C["panel"])
    def flip(_e=None):
        if body.winfo_ismapped():
            body.pack_forget(); ar.config(text="▸")
        else:
            body.pack(fill="x", padx=10, pady=(0, 8)); ar.config(text="▾")
    for w_ in (hd, ar, nf) + tuple(nf.winfo_children()):
        w_.bind("<Button-1>", flip)
    for k in keys:
        if k == "notify_url":
            continue
        if TEXT_SPECS.get(k):
            _px_tk_field(app, body, k, err)
        else:
            _px_tk_toggle(app, body, k)
    if ch in ("ntfy", "webhook"):
        S["url_" + ch] = body
    if ch in ("ntfy", "telegram", "webhook"):
        ttk.Label(body, text=tr("Only one of ntfy · Telegram · Webhook (the main channel, with repeats and the outbox)."), style="Mut.TLabel",
                  wraplength=320, justify="left").pack(anchor="w", pady=(6, 0))
    if ch == "webpush":
        ttk.Label(body, text=tr("Switch it on in the browser of the phone (Settings → Push messages → Web push)."), style="Mut.TLabel",
                  wraplength=320, justify="left").pack(anchor="w", pady=(4, 0))
        ttk.Button(body, text=tr("Open in the browser"), command=lambda: app._open_page("/protect#sec:Notifications")).pack(fill="x", pady=(4, 0))
    if ch == "email":
        adv = tk.Frame(body, bg=C["panel"])
        lk = tk.Label(body, text="▸ " + tr("Advanced"), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8, "bold"), cursor="hand2", anchor="w")
        lk.pack(fill="x", pady=(8, 0))
        def fa(_e=None):
            if adv.winfo_ismapped():
                adv.pack_forget(); lk.config(text="▸ " + tr("Advanced"))
            else:
                adv.pack(fill="x", after=lk); lk.config(text="▾ " + tr("Advanced"))
        lk.bind("<Button-1>", fa)
        for k in ("email_host", "email_port", "email_user", "email_password", "email_events"):
            _px_tk_field(app, adv, k, err)
    if ch == "sms":
        sec = "SMS (LTE stick)"
        for s_, key_, _l in TOGGLES:
            if s_ == sec and key_ != "sms_on":
                _px_tk_toggle(app, body, key_)
        for spec in SLIDERS:
            if spec[0] == sec:
                _px_tk_slider(app, body, spec)
        app._build_texts(body, sec)
        def sms_t():
            ok, err_ = sms_send(tr("MoveEye: test SMS"), force=True)
            app._status(sec, ("✓ " + tr("SMS sent")) if ok else "⚠ " + tr_err(err_))
        ttk.Button(body, text=tr("Send test SMS"), command=lambda: threading.Thread(target=sms_t, daemon=True).start()).pack(fill="x", pady=(6, 0))
        app.status_labels[sec] = ttk.Label(body, text="", style="Mut.TLabel", wraplength=320, justify="left"); app.status_labels[sec].pack(anchor="w")
    S["cards"][ch] = {"box": box, "sw": sw, "st": st, "tb": tb, "body": body, "flip": flip}
    return box


def _px_tk_test(app, ch):
    S = getattr(app, "_px", None)
    if S:
        S["res"].config(text=tr("testing …"))
    def run():
        res = push_test_one(app.watch, ch) if CFG.get("notify_on") else [{"ch": "–", "ok": False, "msg": tr("Push messages are switched off")}]
        txt = "\n".join(("✓ " if r["ok"] else "✗ ") + r["ch"] + " – " + r["msg"] for r in res) or tr("No channel set up.")
        try:
            app.root.after(0, lambda: (S and S["res"].config(text=txt), _px_tk_paint(app)))
        except Exception:
            pass
    threading.Thread(target=run, daemon=True).start()


def _px_tk_quiet(app, parent, S):
    box = tk.Frame(parent, bg=C["panel"]); box.pack(fill="x")
    S["qbox"] = box
    def draw():
        for w_ in box.winfo_children():
            w_.destroy()
        W = quiet_clean(CFG.get("quiet_windows"))
        def save():
            CFG["quiet_windows"] = quiet_clean(W) or CFG["quiet_windows"]; save_settings()
        for i, w in enumerate(W):
            r = tk.Frame(box, bg=C["panel"]); r.pack(fill="x", pady=2)
            for part in ("from", "to"):
                v = tk.StringVar(value=w[part])
                e = tk.Entry(r, textvariable=v, width=6, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat",
                             highlightthickness=1, highlightbackground=C["line"])
                e.pack(side="left", padx=(0, 2))
                def put(_e=None, ww=w, pp=part, vv=v):
                    if _PX_HM.match(vv.get().strip()):
                        ww[pp] = vv.get().strip(); save()
                    else:
                        vv.set(ww[pp])
                e.bind("<Return>", put); e.bind("<FocusOut>", put)
                if part == "from":
                    tk.Label(r, text="–", bg=C["panel"], fg=C["mut"]).pack(side="left", padx=2)
            for k, dn in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
                on = k in w["days"]
                l = tk.Label(r, text=tr(dn), bg=C["acc"] if on else C["field"], fg="#ffffff" if on else C["mut"], font=("DejaVu Sans", 8, "bold"),
                             padx=3, cursor="hand2")
                l.pack(side="left", padx=(4 if k == 0 else 1, 0))
                def flip(_e=None, ww=w, kk=k):
                    ww["days"] = sorted(set(ww["days"]) ^ {kk}) or [kk]; save(); draw()
                l.bind("<Button-1>", flip)
            def rm(ii=i):
                if len(W) <= 1:
                    messagebox.showinfo("MoveEye", tr("At least one time window - switch the quiet hours off instead."), parent=app.root); return
                W.pop(ii); save(); draw()
            x = tk.Label(r, text="✕", bg=C["panel"], fg=C["mut"], cursor="hand2", padx=6); x.pack(side="right"); x.bind("<Button-1>", lambda e, f=rm: f())
        bf = ttk.Frame(box); bf.pack(fill="x", pady=(4, 0))
        def add():
            W.append({"from": "12:00", "to": "14:00", "days": [0, 1, 2, 3, 4, 5, 6]}); save(); draw()
        def home():
            W[:] = [{"from": "08:00", "to": "%02d:00" % int(CFG.get("report_from") or 20), "days": [0, 1, 2, 3, 4]}]; save(); draw()
        if len(W) < 4:
            ttk.Button(bf, text="+ " + tr("Time window"), command=add).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text="🏠 " + tr("Day at home"), command=home).pack(side="left", expand=True, fill="x")
        S["qinfo"] = ttk.Label(box, text="", style="Mut.TLabel", wraplength=330, justify="left"); S["qinfo"].pack(anchor="w", pady=(4, 0))
    draw()


def _px_tk_msg_dialog(app, kind, nm, S):
    win = tk.Toplevel(app.root); win.title("MoveEye"); win.configure(bg=C["panel"]); win.transient(app.root)
    tk.Label(win, text="✎ " + tr(nm), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
    std = msg_defaults()[kind]
    vs = []
    for i, part in enumerate(("title", "text")):
        key = f"msg_{kind}_{part}"
        tk.Label(win, text=tr("Title" if i == 0 else "Text") + " · " + tr("standard") + ": " + std[i], bg=C["panel"], fg=C["mut"], wraplength=380,
                 justify="left").pack(anchor="w", padx=14, pady=(6, 0))
        v = tk.StringVar(value=str(CFG.get(key) or "")); vs.append((key, v))
        tk.Entry(win, textvariable=v, width=50, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat", highlightthickness=1,
                 highlightbackground=C["line"]).pack(fill="x", padx=14, pady=(2, 0))
    tk.Label(win, text=tr("Empty = standard text. Placeholders:") + " " + MSG_PLACEHOLDERS, bg=C["panel"], fg=C["mut"], wraplength=380,
             justify="left").pack(anchor="w", padx=14, pady=(6, 0))
    err = ttk.Label(win, text="", style="Mut.TLabel", foreground=C["red"]); err.pack(anchor="w", padx=14)
    bf = tk.Frame(win, bg=C["panel"]); bf.pack(fill="x", padx=14, pady=12)
    def save(reset=False):
        for key, v in vs:
            ok, msg = set_text(key, "" if reset else v.get())
            if not ok:
                err.config(text="⚠ " + tr_err(msg)); return
        win.destroy(); _px_tk_msgpaint(S)
    ttk.Button(bf, text=tr("Cancel"), command=win.destroy).pack(side="right")
    ttk.Button(bf, text=tr("Save"), command=save).pack(side="right", padx=(0, 6))
    ttk.Button(bf, text="↺ " + tr("Standard text"), command=lambda: save(True)).pack(side="left")


def _px_tk_msgpaint(S):
    for kind, (l, ic, nm) in S.get("msgs", {}).items():
        own = bool(CFG.get(f"msg_{kind}_title") or CFG.get(f"msg_{kind}_text"))
        try:
            l.config(text=f"{ic} {tr(nm)} ✎   ({tr('own text') if own else tr('standard text')})")
        except Exception:
            pass


def _px_tk_paint(app):
    S = getattr(app, "_px", None)
    if not S:
        return
    try:
        if not S["st"].winfo_exists():
            return
    except Exception:
        return
    P = push_info()
    S["st"].config(text=P["status_line"], fg=C["grn"] if P["on"] and P["ready"] else C["mut"])
    hidden = []
    for c in P["channels"]:
        K = S["cards"].get(c["id"])
        if not K:
            continue
        show = c["used"] or c["on"] or c["id"] in S["added"]
        if show and not K["box"].winfo_ismapped():
            K["box"].pack(fill="x", pady=3, in_=S["cw"])
        elif not show and K["box"].winfo_ismapped():
            K["box"].pack_forget()
        if not show:
            hidden.append(c["id"])
        K["sw"].set(c["on"])
        K["st"].config(text=(tr("switched off") if not c["on"] else ("✓ " + (c["info"] or tr("ready")) if c["ready"] else "⚠ " + tr("not set up yet"))),
                       fg=C["mut"] if not c["on"] else (C["grn"] if c["ready"] else C["yel"]))
    tgt = S.get("url_" + ("webhook" if P["main"] == "webhook" else "ntfy"))
    if tgt is not None and S.get("url_parent") is not tgt:
        for w_ in S.get("url_widgets", []):
            try:
                w_.destroy()
            except Exception:
                pass
        kids = [w_ for w_ in tgt.winfo_children() if w_.winfo_manager() == "pack"]
        fr = tk.Frame(tgt, bg=C["panel"])
        if kids:
            fr.pack(fill="x", before=kids[0])
        else:
            fr.pack(fill="x")
        e = _px_tk_field(app, fr, "notify_url", S["err"])
        lab = fr.winfo_children()[0] if fr.winfo_children() else None
        if lab is not None:
            lab.config(text=tr("Webhook address (JSON POST)" if P["main"] == "webhook" else "Address (server/topic)"))
        S["url_parent"], S["url_widgets"] = tgt, [fr]
    m = S["addm"]["menu"]; m.delete(0, "end")
    for ch in hidden:
        m.add_command(label=_PX_TK_CH[ch][0] + " " + tr(_PX_TK_CH[ch][1]), command=lambda c=ch: _px_tk_add(app, c))
    if hidden and not S["addm"].winfo_ismapped():
        S["addm"].pack(fill="x", pady=(4, 0), after=S["cw"])
    elif not hidden:
        S["addm"].pack_forget()
    S["lvl"].set(P["level"]); S["pics"].set(P["pics"])
    S["lvlnote"].config(text=tr({"persons": "Only person alarms. Warm bodies and noise are only logged.",
                                 "animals": "Persons and warm bodies (thermal camera). Noise is only logged.",
                                 "all": "Persons, warm bodies and noise (as up to now)."}.get(P["level"], "")) + " " + tr("Sabotage, theft and notes always come."))
    if S.get("qinfo") is not None:
        q = P["quiet"]
        S["qinfo"].config(text=(("🌙 " + tr("Quiet hours now - alarms are only logged") + " · ") if q["now"] else "") + tr("Clock") + ": " + q["clock"]
                          + (" (" + tr("sim time") + ")" if q["sim"] else "") + " · " + tr("Night time from") + f" {P['night_from']}:00 (" + tr("night report") + ")")
    if CFG.get("quiet_on") and not S["qbox"].winfo_ismapped():
        S["qbox"].pack(fill="x", after=S["qon"])
    elif not CFG.get("quiet_on") and S["qbox"].winfo_ismapped():
        S["qbox"].pack_forget()
    if app.root.focus_get() is not S["kw_e"]:
        S["kw"].set(P["keyword"])


def _px_tk_add(app, ch):
    S = app._px
    S["added"].add(ch); push_add_card(ch)
    _px_tk_paint(app)
    K = S["cards"][ch]
    if not K["body"].winfo_ismapped():
        K["flip"]()


def _px_tk_panel(app, sbody):
    S = {"cards": {}, "added": set(), "msgs": {}}
    err = ttk.Label(sbody, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330, justify="left")
    S["err"] = err
    # ---- Kopf ----
    _px_tk_toggle(app, sbody, "notify_on")
    hr = tk.Frame(sbody, bg=C["panel"]); hr.pack(fill="x", pady=(2, 0))
    S["st"] = tk.Label(hr, text="", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w"); S["st"].pack(side="left", fill="x", expand=True)
    ttk.Button(hr, text="🧪 " + tr("Test all"), command=lambda: _px_tk_test(app, "all")).pack(side="right")
    S["res"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left"); S["res"].pack(anchor="w")
    app.status_labels["Notifications"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
    app.status_labels["Notifications"].pack(anchor="w")
    # ---- Wohin ----
    _px_tk_head(sbody, "Where to")
    S["cw"] = tk.Frame(sbody, bg=C["panel"]); S["cw"].pack(fill="x")
    for ch in _PX_TK_ORDER:
        _px_tk_card(app, S["cw"], ch, err, S)
    S["addm"] = tk.Menubutton(sbody, text="+ " + tr("Add channel"), bg=C["field"], fg=C["txt"], activebackground=C["line"], relief="flat",
                              highlightthickness=1, highlightbackground=C["line"], cursor="hand2")
    S["addm"]["menu"] = tk.Menu(S["addm"], tearoff=0)
    # ---- Was ----
    _px_tk_head(sbody, "What")
    ttk.Label(sbody, text=tr("What is reported")).pack(anchor="w")
    S["lvl"] = _PxSeg(sbody, [("persons", "Only persons"), ("animals", "Persons + animals"), ("all", "Everything")], CFG.get("push_level", "all"),
                      lambda v: (app._text_set("push_level", v, err), _px_tk_paint(app)))
    S["lvl"].pack(fill="x", pady=(2, 0)); app._g2_q(S["lvl"], "push_level")
    S["lvlnote"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left"); S["lvlnote"].pack(anchor="w", pady=(2, 0))
    _px_tk_toggle(app, sbody, "notify_prealarm")
    ttk.Label(sbody, text=tr("Pictures")).pack(anchor="w", pady=(6, 0))
    S["pics"] = _PxSeg(sbody, [("with", "with picture"), ("small", "small picture"), ("text", "without picture")], CFG.get("push_pics", "with"),
                       lambda v: app._text_set("push_pics", v, err))
    S["pics"].pack(fill="x", pady=(2, 0)); app._g2_q(S["pics"], "push_pics")
    # ---- Wann ----
    _px_tk_head(sbody, "When")
    for spec in SLIDERS:
        if spec[0] == "Notifications":
            _px_tk_slider(app, sbody, spec)
    S["qon"] = _px_tk_toggle(app, sbody, "quiet_on") or tk.Frame(sbody)
    _px_tk_quiet(app, sbody, S)
    _px_tk_toggle(app, S["qbox"], "quiet_persons")
    # ---- Erweitert (closed) ----
    lk = tk.Label(sbody, text="▸ " + tr("Advanced").upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w", cursor="hand2")
    lk.pack(fill="x", pady=(12, 2))
    adv = tk.Frame(sbody, bg=C["panel"])
    def fa(_e=None):
        if adv.winfo_ismapped():
            adv.pack_forget(); lk.config(text="▸ " + tr("Advanced").upper())
        else:
            adv.pack(fill="x", after=lk); lk.config(text="▾ " + tr("Advanced").upper())
    lk.bind("<Button-1>", fa)
    ttk.Label(adv, text=tr("Keyword (empty = off)"), style="Mut.TLabel").pack(anchor="w", pady=(4, 0))
    S["kw"] = tk.StringVar(value=push_keyword())
    kr = tk.Frame(adv, bg=C["field"], highlightthickness=1, highlightbackground=C["line"]); kr.pack(fill="x", pady=(2, 0))
    S["kw_e"] = tk.Entry(kr, textvariable=S["kw"], bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat", highlightthickness=0)
    S["kw_e"].pack(side="left", fill="x", expand=True, padx=(6, 0), pady=3)
    for ev in ("<Return>", "<FocusOut>"):
        S["kw_e"].bind(ev, lambda e: (push_keyword_set(S["kw"].get()), _px_tk_paint(app)))
    kx = tk.Label(kr, text="✕", bg=C["field"], fg=C["mut"], cursor="hand2", padx=6); kx.pack(side="right")
    kx.bind("<Button-1>", lambda e: (S["kw"].set(""), push_keyword_set(""), _px_tk_paint(app)))
    app._g2_q(kr, "msg_keyword_prefix")
    for k in ("push_actions", "msg_icons", "notify_network", "notify_remote", "browser_alarm"):
        _px_tk_toggle(app, adv, k)
    _px_tk_field(app, adv, "public_url", err)
    tk.Label(adv, text="💬 " + tr("Message texts"), bg=C["panel"], fg=C["txt"], anchor="w").pack(fill="x", pady=(10, 2))
    for kind, ic, nm in _PX_TK_MSG:
        if _px_tk_hide(f"msg_{kind}_title"):
            continue
        l = tk.Label(adv, text="", bg=C["field"], fg=C["txt"], anchor="w", cursor="hand2", padx=8, pady=4, highlightthickness=1, highlightbackground=C["line"])
        l.pack(fill="x", pady=1); l.bind("<Button-1>", lambda e, k_=kind, n_=nm: _px_tk_msg_dialog(app, k_, n_, S))
        S["msgs"][kind] = (l, ic, nm)
    _px_tk_msgpaint(S)
    ttk.Button(adv, text="📲 " + tr("iPhone shortcuts") + " (" + tr("browser") + ")", command=lambda: app._open_page("/protect#sec:Notifications")).pack(fill="x", pady=(8, 0))
    err.pack(anchor="w", pady=(4, 0))
    app._px = S
    _px_tk_paint(app)
    def tick():
        try:
            if S["st"].winfo_exists() and getattr(app, "_px", None) is S:
                _px_tk_paint(app); app.root.after(4000, tick)
        except Exception:
            pass
    app.root.after(4000, tick)


def _px_tk_build_section(self, sec, sbody, settings_parent=None):
    if sec != "Notifications":
        return _px_tk_build_section_before(self, sec, sbody, settings_parent)
    fr = tk.Frame(sbody, bg=C["panel"]); fr.pack(fill="x")
    try:
        _px_tk_panel(self, fr)
    except Exception as e:                                  # never an empty section: the old list instead
        log_event("sys", f"Window: push cards: {e}"[:160])
        fr.destroy()
        _px_tk_build_section_before(self, sec, sbody, settings_parent)


_px_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _px_tk_build_section
