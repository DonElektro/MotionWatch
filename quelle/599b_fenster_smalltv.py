#@ MoveEye – Teil 599b: Zusatz-Bildschirm SmallTV (Teil 552) – Einstellungen (Web und Fenster lesen dieselben Listen), Abschnitt im Fenster (Liste, Testbild, Suche, Einrichtung mit QR-Codes), deutsche Texte der Webseite, Selbsttest mit einem nachgebauten Gerät (Firmware-Macken). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Section «Extra display» in the group «Devices & sensors» (web GROUPS in 530, window TK_GROUPS here) - the place of the
# other devices at MoveEye (lights, loudspeaker, relays). Here (after 570) because TOGGLES / SLIDERS / App live there.
# ----------------------------------------------------------------------------
_STVS = "Extra display"
TOGGLES.extend([
    (_STVS, "stv_on", "Show MoveEye on extra displays (GeekMagic SmallTV)"),
    (_STVS, "stv_animals", "Alarm picture also for animals (picture section with species, certainty and distance)"),
    (_STVS, "stv_person_pic", "Picture also for persons (otherwise only a symbol and text)"),
    (_STVS, "stv_night", "At night dark and red (like the red light view), bright for a moment at an alarm"),
])
SLIDERS.extend([
    (_STVS, "stv_night_brt", "Brightness at night (%)", 0, 100, 5),
    (_STVS, "stv_alarm_s", "Alarm picture stays (s)", 10, 600, 10),
    (_STVS, "stv_bright_s", "At an alarm bright for (s)", 0, 120, 5),
    (_STVS, "stv_gap_s", "At most one picture every (s) - an alarm at once", 5, 120, 5),
    (_STVS, "stv_clock_min", "Status picture: clock new every (minutes, spares the flash)", 1, 60, 1),
])
SECTIONS.append(_STVS)
for _g in TK_GROUPS:
    if _g[0] == "sensors" and _STVS not in _g[2]:
        _g[2].insert(_g[2].index("Loudspeaker") + 1 if "Loudspeaker" in _g[2] else len(_g[2]), _STVS)
TK_SUB_ICONS[_STVS] = "▣"
SIMPLE_IN_USE[_STVS] = lambda: bool(CFG.get("stv_list")) or bool(STV.get("sim_ok"))   # «Simple»: shown when there is a display
SIMPLE_KEYS.update({"stv_on", "stv_person_pic", "stv_night"})

# the German texts of the web panel (552 STV_JS)
_STV_JS_KEYS = ["Virtual SmallTV of the simulator", "free", "not reachable", "reachable", "checking …", "pictures", "Status", "Alarm picture", "Game",
                "Test picture", "On", "Brightness (day)", "Send a test picture", "Test picture on the way (shows 15 s)", "Check", "Remove", "Remove this display?",
                "Set up a SmallTV (step by step)", "Plug the SmallTV in (USB, 5 V). New or reset, it opens its own Wi-Fi «GIFTV».",
                "Join «GIFTV» with the phone and open the setup page", "Setup page of the SmallTV", "Choose the network of MoveEye there", "own Wi-Fi of MoveEye",
                "the Wi-Fi in which MoveEye is", "The SmallTV restarts and shows its new address.",
                "Back here: «Search in the network» or enter the address shown on the SmallTV.", "stv-security", "Name (e.g. Tent)", "Address (e.g. 192.168.1.77)",
                "Add", "Search in the network", "searching … (about 10 s)", "No SmallTV found. Is it in the same network? Otherwise enter the address.",
                "in the list", "Night: the displays are dimmed and red.", "No display yet.", "The simulator has a virtual SmallTV from version 3D-4.19.", "stv-note",
                "Extra display", "Extra display (SmallTV)"]
WEB_PAGE = WEB_PAGE.replace("</body>", STV_JS.replace("/*STVDE*/{}", json.dumps({_k: DE.get(_k, _k) for _k in _STV_JS_KEYS}, ensure_ascii=False), 1) + "</body>", 1)


# ---- window (Tkinter): the same in Settings → Devices & sensors → Extra display -------------------------------------------
def _stv_tk_build_section(self, sec, sbody, settings_parent=None):
    _stv_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != _STVS:
        return
    try:
        stv_start()
        _stv_tk_panel(self, sbody)
    except Exception as e:
        log_event("sys", f"Window: SmallTV section: {e}"[:160])


def _stv_tk_panel(app, sbody):
    ent_kw = dict(bg=C["field"], fg=C["txt"], insertbackground=C["txt"], relief="flat", highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["acc"])
    ttk.Label(sbody, text=tr("stv-note"), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(6, 0))
    _ak_tk_line(sbody, tr("Displays"))
    box = tk.Frame(sbody, bg=C["panel"]); box.pack(fill="x")
    st = {"sig": None, "pics": []}

    def act(d):
        def run():
            try:
                if d.get("action") == "test":
                    ok, err = stv_test(d["id"])
                elif d.get("action") == "check":
                    dv = STV["devs"].get(d["id"]); ok, err = bool(dv), ""
                    if dv:
                        dv.h["t"] = 0.0; dv.ev.set()
                else:
                    ok, err = stv_edit(d["action"], d, "window")
                if not ok:
                    app.root.after(0, lambda: messagebox.showinfo("MoveEye", tr_err(err)))
            except Exception as e:
                log_event("sys", f"Window: SmallTV: {e}"[:160])
            st["sig"] = None
        threading.Thread(target=run, daemon=True).start()

    def paint():
        try:
            if not box.winfo_exists():
                return
        except Exception:
            return
        s = stv_state()
        sig = json.dumps(s["list"], sort_keys=True, default=str)
        if sig != st["sig"]:
            st["sig"] = sig
            for w in box.winfo_children():
                w.destroy()
            st["pics"] = []
            if s["night"]:
                ttk.Label(box, text="☾ " + tr("Night: the displays are dimmed and red."), style="Mut.TLabel").pack(anchor="w")
            if not s["list"]:
                ttk.Label(box, text=tr("No display yet."), style="Mut.TLabel", wraplength=330).pack(anchor="w", pady=(4, 0))
            for e in s["list"]:
                card = tk.Frame(box, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"]); card.pack(fill="x", pady=(6, 0))
                top = tk.Frame(card, bg=C["panel"]); top.pack(fill="x", padx=6, pady=(6, 0))
                jpg = stv_img(e["id"])
                if jpg:
                    try:
                        from PIL import Image, ImageTk
                        import io
                        ph = ImageTk.PhotoImage(Image.open(io.BytesIO(jpg)).resize((72, 72)))
                        st["pics"].append(ph)
                        tk.Label(top, image=ph, bg="#000000").pack(side="left", padx=(0, 8))
                    except Exception:
                        pass
                h = e["health"]
                dot, col = ("●", C.get("grn", "#3fcf6b")) if h.get("ok") else (("●", C.get("red", "#ff4d4d")) if h.get("ok") is False else ("○", C["mut"]))
                tf = tk.Frame(top, bg=C["panel"]); tf.pack(side="left", fill="x", expand=True)
                ln = tk.Frame(tf, bg=C["panel"]); ln.pack(anchor="w")
                tk.Label(ln, text=dot, bg=C["panel"], fg=col, font=("DejaVu Sans", 11)).pack(side="left")
                tk.Label(ln, text=("⚗ " + tr("Virtual SmallTV of the simulator")) if e.get("sim") else e["name"], bg=C["panel"], fg=C["txt"],
                         font=("DejaVu Sans", 10, "bold")).pack(side="left", padx=(4, 0))
                info = e["addr"].replace("http://", "") + (" · " + h["fw"] if h.get("fw") else "") + \
                    (f" · {round(h['free'] / 1024)} KB " + tr("free") if h.get("free") is not None else "")
                info2 = ("⚠ " + (h.get("err") or tr("not reachable")) if h.get("ok") is False else ("✓ " + tr("reachable") if h.get("ok") else tr("checking …"))) + \
                    f" · {e['ups']} " + tr("pictures")
                for t_ in (info, info2):
                    tk.Label(tf, text=t_, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8), wraplength=240, justify="left", anchor="w").pack(anchor="w")
                for f_, lb in (("on", "On"), ("status", "Status"), ("alarm", "Alarm picture"), ("game", "Game")):
                    Toggle(card, tr(lb), e[f_], lambda v, f_=f_, sid=e["id"]: act({"action": "update", "id": sid, "field": f_, "value": v})).pack(fill="x", padx=6, pady=(2, 0))
                bf = tk.Frame(card, bg=C["panel"]); bf.pack(fill="x", padx=6, pady=(4, 0))
                tk.Label(bf, text=tr("Brightness (day)"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 9)).pack(side="left")
                sc = tk.Scale(bf, from_=0, to=100, resolution=5, orient="horizontal", showvalue=True, bg=C["panel"], fg=C["txt"], troughcolor=C["field"],
                              highlightthickness=0, bd=0, length=170)
                sc.set(e["brt"]); sc.pack(side="right")
                sc.bind("<ButtonRelease-1>", lambda _e, sc=sc, sid=e["id"]: act({"action": "update", "id": sid, "field": "brt", "value": sc.get()}))
                bb = ttk.Frame(card); bb.pack(fill="x", padx=6, pady=(4, 6))
                ttk.Button(bb, text="▣ " + tr("Send a test picture"), command=lambda sid=e["id"]: act({"action": "test", "id": sid})).pack(side="left", expand=True, fill="x", padx=(0, 4))
                ttk.Button(bb, text="↻ " + tr("Check"), command=lambda sid=e["id"]: act({"action": "check", "id": sid})).pack(side="left", expand=True, fill="x", padx=(0, 4))
                if not e.get("sim"):
                    ttk.Button(bb, text="✕ " + tr("Remove"), command=lambda sid=e["id"], nm=e["name"]: messagebox.askyesno("MoveEye", tr("Remove this display?") + "\n" + nm)
                               and act({"action": "remove", "id": sid})).pack(side="left", expand=True, fill="x")
        app.root.after(4000, paint)

    # add by hand
    nv, av = tk.StringVar(), tk.StringVar()
    af = tk.Frame(sbody, bg=C["panel"]); af.pack(fill="x", pady=(8, 0))
    tk.Label(af, text=tr("Name (e.g. Tent)"), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8)).grid(row=0, column=0, sticky="w")
    tk.Label(af, text=tr("Address (e.g. 192.168.1.77)"), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8)).grid(row=0, column=1, sticky="w", padx=(6, 0))
    tk.Entry(af, textvariable=nv, width=12, **ent_kw).grid(row=1, column=0, sticky="we")
    tk.Entry(af, textvariable=av, width=18, **ent_kw).grid(row=1, column=1, sticky="we", padx=(6, 0))
    af.columnconfigure(0, weight=1); af.columnconfigure(1, weight=2)

    def add():
        ok, err = stv_edit("add", {"name": nv.get(), "addr": av.get()}, "window")
        if not ok:
            messagebox.showinfo("MoveEye", tr_err(err)); return
        nv.set(""); av.set(""); st["sig"] = None
    ttk.Button(sbody, text="+ " + tr("Add"), command=add).pack(fill="x", pady=(4, 0))
    # search in the network
    res = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
    found = tk.Frame(sbody, bg=C["panel"])

    def scan_paint():
        S = STV["scan"]
        if S["busy"]:
            res.config(text=tr("searching … (about 10 s)")); app.root.after(1500, scan_paint); return
        for w in found.winfo_children():
            w.destroy()
        if not S["found"]:
            res.config(text=tr("No SmallTV found. Is it in the same network? Otherwise enter the address.")); return
        res.config(text="")
        for x in S["found"]:
            r = tk.Frame(found, bg=C["panel"]); r.pack(fill="x", pady=(2, 0))
            tk.Label(r, text=x["addr"].replace("http://", "") + (" · " + x["fw"] if x.get("fw") else ""), bg=C["panel"], fg=C["txt"]).pack(side="left")
            if x.get("known"):
                tk.Label(r, text="✓ " + tr("in the list"), bg=C["panel"], fg=C["mut"]).pack(side="right")
            else:
                ttk.Button(r, text="+ " + tr("Add"), command=lambda a=x["addr"]: (stv_edit("add", {"name": "SmallTV", "addr": a}, "window"), st.update(sig=None))).pack(side="right")
    ttk.Button(sbody, text="⌕ " + tr("Search in the network"), command=lambda: (stv_scan(), app.root.after(500, scan_paint))).pack(fill="x", pady=(6, 0))
    res.pack(anchor="w", pady=(2, 0)); found.pack(fill="x")
    # setup step by step + QR codes
    _ak_tk_line(sbody, tr("Set up a SmallTV (step by step)"))
    s = stv_state()["setup"]
    steps = [tr("Plug the SmallTV in (USB, 5 V). New or reset, it opens its own Wi-Fi «GIFTV»."),
             tr("Join «GIFTV» with the phone and open the setup page") + " " + s["url"],
             tr("Choose the network of MoveEye there") + ": " + (f"«{s['own_wifi']}» (" + tr("own Wi-Fi of MoveEye") + ")" if s["own_on"] else tr("the Wi-Fi in which MoveEye is")) + ". "
             + tr("The SmallTV restarts and shows its new address."),
             tr("Back here: «Search in the network» or enter the address shown on the SmallTV.")]
    for i, t_ in enumerate(steps):
        ttk.Label(sbody, text=f"{i + 1}. {t_}", style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(2, 0))
    qf = ttk.Frame(sbody); qf.pack(fill="x", pady=(4, 0))
    ttk.Button(qf, text="▦ Wi-Fi «GIFTV»", command=lambda: qr_tk_dialog(app.root, s["wifi_qr"], "Wi-Fi «GIFTV» (SmallTV)")).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(qf, text="▦ " + s["url"].replace("http://", ""), command=lambda: qr_tk_dialog(app.root, s["url"], tr("Setup page of the SmallTV"))).pack(side="left", expand=True, fill="x")
    ttk.Label(sbody, text="⚠ " + tr("stv-security"), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(6, 0))
    paint()


_stv_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _stv_tk_build_section


# ---- self-test: the pictures, the plan, a made-up device with the firmware quirks (HTTP 400 although stored, slow) ------
def _stv_fake_server(quirks=True, delay=0.25):
    """a tiny GeekMagic SmallTV on 127.0.0.1 (same API as the device and as the simulator's smalltv.gd) -> (server, base, state)"""
    import http.server
    S = {"files": {}, "img": "", "brt": 50, "theme": 1, "uploads": 0, "reqs": []}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _out(self, code, body, ct="text/plain"):
            time.sleep(delay if quirks else 0)
            b = body.encode() if isinstance(body, str) else body
            self.send_response(code); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b))); self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            from urllib.parse import urlsplit, parse_qs
            u = urlsplit(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
            S["reqs"].append(u.path)
            if u.path == "/v.json":
                return self._out(200, json.dumps({"m": "SmallTV-Ultra", "v": "Ultra-V9.0.40"}), "application/json")
            if u.path == "/space.json":
                return self._out(200, json.dumps({"total": 1048576, "free": 1048576 - sum(len(x) for x in S["files"].values())}), "application/json")
            if u.path == "/filelist":
                return self._out(200, "".join(f'<a href="/image/{n}">{n}</a> {len(b)}<br>' for n, b in S["files"].items()), "text/html")
            if u.path == "/set":
                if "img" in q:
                    n = q["img"].split("/")[-1]
                    if n not in S["files"]:
                        return self._out(404, "no")
                    S["img"] = n
                if "brt" in q:
                    S["brt"] = int(q["brt"])
                if "theme" in q:
                    S["theme"] = int(q["theme"])
                return self._out(200, "OK")
            return self._out(404, "no")

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n)
            m = re.search(rb'filename="([^"]+)"\r\n.*?\r\n\r\n', body, re.S)
            if not m:
                return self._out(400, "no file")
            data = body[m.end():body.rfind(b"\r\n--")]
            S["files"][m.group(1).decode()] = data
            S["uploads"] += 1
            return self._out(400 if quirks else 200, "Bad Request" if quirks else "OK")   # the firmware quirk: stored, still «400»

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}", S


def smalltv_selftest():
    from PIL import Image
    import io
    keep = {k: CFG.get(k) for k in STV_CFG}
    keep_a, keep_g = STV["alarm"], STV["game"]
    srv = None
    try:
        assert stv_norm_addr("192.168.1.77") == "http://192.168.1.77" and stv_norm_addr("http://tv.local:8080/") == "http://tv.local:8080"
        assert stv_norm_addr("javascript:alert(1)") == "" and stv_norm_addr("http://a b") == "" and stv_norm_addr("https://x") == ""
        assert stv_is_geekmagic({"m": "SmallTV-Ultra", "v": "Ultra-V9.0.40"}) and not stv_is_geekmagic({"v": 1, "name": "MW Sim"})
        for jpg in (stv_render_status("de"), stv_render_status("de", True), stv_render_test("Zelt"),
                    stv_render_alarm({"kind": "animal", "label": "fox", "conf": 0.91, "dist": 6, "crop": np.full((90, 120, 3), 90, np.uint8), "clock": "22:14"}, "de"),
                    stv_render_alarm({"kind": "person", "label": "person", "conf": None, "dist": 12, "crop": None, "n": 2, "clock": "01:05"}, "de", True),
                    stv_render_game({"round": "play", "left": 95, "players": [{"n": "Anna 🦊", "pt": 300, "k": 1}, {"n": "Ben", "pt": 120, "k": 0}], "mw": 2}, "Ben", "de")):
            im = Image.open(io.BytesIO(jpg))
            assert im.size == (240, 240) and im.format == "JPEG" and len(jpg) < 60000, (im.size, len(jpg))
        r = np.asarray(Image.open(io.BytesIO(stv_render_status("de", True))).convert("RGB"), np.int32)
        assert (r[..., 1] > r[..., 0] + 24).mean() < 0.002 and r[..., 1].mean() < 0.35 * r[..., 0].mean() and r[..., 0].max() > 120, "night: red only"
        # the plan: alarm before game before status; persons without picture by default; bright at an alarm
        CFG.update(stv_night=False, stv_alarm_s=60, stv_bright_s=20)
        e = {"id": "x", "status": True, "alarm": True, "game": True, "brt": 40}
        STV["alarm"] = None; STV["game"] = None
        assert stv_plan(e)[0] == "status" and stv_plan(e)[3] == 40
        STV["game"] = {"round": "play", "left": 30, "players": []}; STV["game_t"] = time.time()
        assert stv_plan(e)[0] == "game"
        STV["alarm"] = {"t": time.time(), "kind": "person", "label": "person", "conf": None, "dist": None, "crop": None, "n": 1, "clock": "1"}
        k_, _s, _f, brt, now_ = stv_plan(e)
        assert k_ == "game" and brt == 40, (k_, brt)         # during a round the players are the persons: the game stays
        STV["game"] = {"round": "end", "players": []}; STV["end_t"] = time.time()
        k_, _s, _f, brt, now_ = stv_plan(e)
        assert k_ == "alarm" and brt == 100 and now_
        assert stv_plan(dict(e, alarm=False))[0] == "game"
        STV["end_t"] = time.time() - 61
        assert stv_plan(dict(e, alarm=False))[0] == "status"      # the end screen only 60 s
        # the wrappers of 552 reach the parts they wrap; «Erwischt!» from the answer of the simulator
        assert all(callable(f_) for f_ in (_alarm_ctx_note_066, _species_update_180, _simvals_take_285, _msglog_add_065))
        keep_sim = dict(SIM); keep_k = dict(STV["k"]); keep_c = STV["caught"]
        try:
            STV["k"] = {}; STV["caught"] = None
            simvals_take({"game_live": {"round": "play", "players": [{"n": "Anna", "k": 0}]}})
            simvals_take({"game_live": {"round": "play", "players": [{"n": "Anna", "k": 1}]}})
            assert STV["caught"] and STV["caught"][1] == "Anna" and STV["game"]["round"] == "play"
        finally:
            SIM.clear(); SIM.update(keep_sim); STV["k"] = keep_k; STV["caught"] = keep_c
        # the client against the made-up device with the firmware quirks (400 although stored, slow answers)
        srv, base, S = _stv_fake_server(quirks=True, delay=0.2)
        ok, note = stv_upload(base, "me_a.jpg", stv_render_test("t"))
        assert ok and "400" in note and "me_a.jpg" in S["files"], (ok, note)
        assert stv_files(base) == ["me_a.jpg"]
        dv = StvDev.__new__(StvDev)
        dv.id = "t"; dv.shown = ""; dv.theme_t = 0.0; dv.ups = dv.bytes = dv.errs = 0; dv.h = {"ok": None, "t": 0.0}; dv.jpg = None; dv.kind = ""
        w = {"jpg": stv_render_status("de"), "sig": 1, "kind": "status", "brt": 30}
        assert dv.send(base, w) and S["img"] == "me_a.jpg" and S["theme"] == 3, (S["img"], S["theme"])
        assert dv.send(base, dict(w, sig=2)) and S["img"] == "me_b.jpg" and len(S["files"]) == 2      # the other name: complete before it shows
        assert dv.send(base, dict(w, sig=3)) and S["img"] == "me_a.jpg" and sorted(S["files"]) == ["me_a.jpg", "me_b.jpg"]   # only these two files
        dv.check(base, force=True)
        assert dv.h["ok"] and dv.h["fw"] == "Ultra-V9.0.40" and dv.h["free"] > 900000, dv.h
        srv.shutdown()
        srv, base, S = _stv_fake_server(quirks=False, delay=0)
        assert stv_upload(base, "me_a.jpg", b"\xff\xd8x\xff\xd9") == (True, "")
    finally:
        if srv is not None:
            srv.shutdown()
        CFG.update(keep)
        STV["alarm"], STV["game"] = keep_a, keep_g
        STV["renders"].clear()


SELFTEST_EXTRA.append(("Extra display SmallTV: pictures, plan, device with firmware quirks (552)", smalltv_selftest))
