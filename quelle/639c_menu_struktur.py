#@ MoveEye – Teil 639c: Menü-Struktur 2 (Daniel 30.10.2026): Gruppen neu geteilt, Entwickler-Gruppe, Einfach = Hauptschalter + zugeklappte Feineinstellungen, kurze Beschriftungen mit «?». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Here (after all the parts that add settings, before 640) so it sees every TOGGLES / SLIDERS / TEXTS entry:
#   * moves a few settings to new sections (no CFG key changes - only where they are shown):
#       Night time (report_from / report_hour) -> group «Zonen, Zeitplan, Anwesenheit»
#       Presence (protection on when my phone is gone, the phones, «Is it you?») -> same group
#       Setup -> «Ort & Uhr» (Setup) + «Gerätewarnungen» + «Gerät & Hilfe»; log status line -> «Entwickler»
#   * the window groups (TK_GROUPS) = the web groups (GROUPS in 530): Diebstahlschutz, Licht & Ton, Zusatzgeräte, Mover,
#     Entwickler (only with dev_area). «Kopf (Servos)» = Camera / Servos + Automatic head movement + Servo motion & safety
#   * «Simple» (Einfach): the main switches of a part stay, the rest is in a closed «Feineinstellungen» (web and window);
#     the old per-key list SIMPLE_KEYS decides what counts as main switch (fallback), MENU_MAIN adds a few
#   * long labels: the short text is the label, the long one the «?» help (g2_help) - texts in 639b
#   * the language of choices on the web page follows the page (web_texts), English texts of a few note keys
# ----------------------------------------------------------------------------
_MENU_MOVES = {
    "Night time": ("report_from", "report_hour"),
    "Presence": ("presence_auto", "presence_hosts", "presence_back", "back_hold_s", "away_after"),
    "Setup": ("time_from_browser",),
    "Device warnings": ("temp_alarm_on", "env_on", "temp_hot", "temp_cold", "env_offset", "temp_warn", "disk_warn_mb"),
    "Device & help": ("device_name", "use_case", "tips_level", "tours_auto", "tip_of_day", "blinki_on", "desktop_notice", "log_keep_days", "dev_area"),
    "Developer": ("log_status_min",),
}
for _ms, _mk in _MENU_MOVES.items():
    for _lst in (TOGGLES, SLIDERS, TEXTS):
        for _i, _x in enumerate(_lst):
            if _x[1] in _mk:
                _lst[_i] = (_ms,) + tuple(_x[1:])
    if _ms not in SECTIONS:
        SECTIONS.append(_ms)
TEXT_SPECS.update({k: (kind, extra) for s, k, l, kind, extra in TEXTS})
MENU_DEV_SECTIONS = ("Developer", "Servo driver")          # only with «Developer area» (dev_area) on
SIMPLE_SECTIONS.update({"Theft protection", "Reference scan", "Night time", "Presence", "Device warnings", "Device & help", "Developer"})
SIMPLE_KEYS.update({"presence_auto", "presence_hosts", "device_name", "refscan_on_arm", "deter_big_act", "deter_small_act", "deter_warm_act",
                    "deter_big_sound", "deter_small_sound", "deter_warm_sound"})
# main switch of a part that has no key in SIMPLE_KEYS (shown in «Simple», the rest is folded)
MENU_MAIN = {"refscan_on_arm", "kopf_on", "servo_stop_btn", "log_status_min", "dev_area", "tours_auto", "report_from", "report_hour",
             "time_from_browser", "gps_phone", "temp_warn", "disk_warn_mb", "deter_always"}
MENU_NO_FOLD = {"Reference scan"}                          # «Simple»: only the link to the assistant (the rest in «Expert» / tools)
MENU_TITLES = {"Setup": "Place & clock", "Camera / Servos": "Head (servos)", "Camping / protection": "Arming and own Wi-Fi",
               "Notifications": "Push messages", "Device & help": "Device & help", "Night time": "Night time", "Presence": "Presence"}
MENU_LONG = {}                                             # key -> the long label (now the «?» help)

# ---- the window: the same groups as the web page ----------------------------------------------------------------------
TK_GROUPS[:] = [
    ("alarm", "Protection", ["Camping / protection"]),
    ("notify", "What happens at an alarm?", ["Notifications", "Deterrence", "Recording", "Night report"]),     # messages / SMS: in the push panel (571a)
    ("theft", "Theft protection", ["Theft protection", "Reference scan", "Backup"]),
    ("sched", "Zones, schedule, presence", ["Schedule", "Night time", "Presence"]),
    ("detect", "Detection", ["Improve detection", "Detection", "AI detection", "Thermal camera", None, "Walking recognition", "Vehicle filter", "Rain", "Wind", "Low light", "Auto-tune"]),
    ("camera", "Cameras & head", ["Camera / Servos", "Patrol", "Video source", "Timelapse"]),
    ("mover", "Mover", ["Mover"]),
    ("lightsound", "Light & sound", ["Lights", "Loudspeaker", "Microphone", "Clap switch", "Bless you", "Wake-up alarm"]),
    ("extras", "Extra devices", ["Relays", "Extra sensors", "Storm warning", "GPS module", _STVS]),
    ("power", "Power supply", ["Battery", "Power saving", "Solar panel"]),
    ("net", "Network & access", ["Wi-Fi / hotspot", "Web stream", "Guest access", "MQTT / Home Assistant"]),
    ("security", "Security", ["Security"]),
    ("sys", "System", ["Setup", "Device warnings", "Device & help", "Updates"]),
    ("dev", "Developer", ["Developer", "Servo driver"]),
]
TK_GROUP_TAB.update({"alarm": "protect", "notify": "protect", "theft": "protect", "sched": "protect"})
TK_GROUP_ICONS.update({"theft": "⚷", "mover": "⇕", "lightsound": "☀", "extras": "◉", "dev": "⚒"})
TK_SUB_ICONS.update({"Night time": "☾", "Presence": "⌂", "Device warnings": "⚠", "Device & help": "?", "Developer": "⚒"})
TK_MENU_MERGE = {"Camera / Servos": [_KS, _SVS]}
TK_INSIDE = {_KS, _SVS, "Messages", "SMS (LTE stick)"}      # window: inside «Kopf (Servos)» / «Push-Nachrichten»          # «Kopf (Servos)»: one part, the two others in its «Feineinstellungen»


# ---- «Simple»: developer sections only with dev_area; folded fine-tuning --------------------------------------------
_MENU_TL = threading.local()
_simple_hidden_menu_base = simple_hidden


def simple_hidden(key, sec=None):                           # + 639c: developer sections, forced hiding (window table)
    if sec is not None and sec in MENU_DEV_SECTIONS and not CFG.get("dev_area"):
        return True
    if sec is not None and getattr(_MENU_TL, "tk", False) and sec in TK_INSIDE:
        return True                                         # the window shows them inside another part (not again under the last group)
    if key is not None and key in getattr(_MENU_TL, "hide", ()):
        return True
    if key is not None and getattr(_MENU_TL, "all", False):
        return False
    return _simple_hidden_menu_base(key, sec)


def menu_fine(key):
    """«Simple»: this setting is in the closed «Feineinstellungen» of its part (not a main switch)"""
    return key not in MENU_MAIN and _simple_hidden_menu_base(key)


_cur_lang_menu_base = cur_lang


def cur_lang(lang=None):                                    # + 639c: the language of the page while its schema is made
    return norm_lang(lang or getattr(_MENU_TL, "lang", None) or CFG.get("lang") or "en")


_web_texts_menu_base = web_texts


def web_texts(lang=None):                                   # + 639c: the choices («nur Alarme …») in the language of the page
    old = getattr(_MENU_TL, "lang", None)
    _MENU_TL.lang = lang or old
    try:
        return _web_texts_menu_base(lang)
    finally:
        _MENU_TL.lang = old


_web_schema_menu_base = web_schema


def web_schema(lang=None, only=None):
    """+ 639c: «Simple» sends every setting of a shown part; the ones that are not main switches carry fine=True (the page
    puts them into a closed «Feineinstellungen»). Long labels: «help» = the long text (search + tooltip)."""
    simple = only is None and ui_simple_now()
    if simple:
        vis = {s for s in SECTIONS if not simple_hidden(None, s)}
        old = getattr(_MENU_TL, "all", False)
        _MENU_TL.all = True
        try:
            out = _web_schema_menu_base(lang, only)
        finally:
            _MENU_TL.all = old
        out = [s for s in out if s["id"] in vis]
    else:
        out = _web_schema_menu_base(lang, only)
    for s in out:
        s["title"] = tr(MENU_TITLES[s["id"]], lang) if s["id"] in MENU_TITLES else s["name"]
        for k_ in ("toggles", "sliders", "texts"):
            for x in s.get(k_) or []:
                if simple and menu_fine(x["key"]) and s["id"] not in ("Notifications",):
                    x["fine"] = True
                if x["key"] in MENU_LONG:
                    x["help"] = tr(MENU_LONG[x["key"]], lang)
        if simple and s["id"] in MENU_NO_FOLD:
            for k_ in ("toggles", "sliders", "texts"):
                s[k_] = [x for x in s.get(k_) or [] if not x.get("fine")]
    return out


# ---- short labels (639b: MENU_SHORT {long English label: short English label}) --------------------------------------
def _menu_short_apply():
    for lst in (TOGGLES, SLIDERS, TEXTS):
        for i, x in enumerate(lst):
            sh = MENU_SHORT.get(x[2])
            if sh and sh != x[2]:
                MENU_LONG[x[1]] = x[2]
                lst[i] = (x[0], x[1], sh) + tuple(x[3:])


_menu_short_apply()
_g2_help_menu_base = g2_help


def g2_help(lang=None):                                     # + 639c: the long label of a shortened setting is its explanation
    L = cur_lang(lang)
    out = _g2_help_menu_base(lang)
    for k, long_ in MENU_LONG.items():
        x = out.get(k)
        lt = tr(long_, L)
        if x is None:
            out[k] = {"x": lt, "r": "", "d": _g2_default_txt(k, L)}
        elif lt not in x["x"]:
            x["x"] = lt + "\n\n" + x["x"] if x["x"] else lt
    return out


# ---- a few note keys: English text (tr() returns the key in English) -------------------------------------------------
_tr_menu_base = tr


def tr(text, lang=None):                                    # + 639c: English of the note keys (MENU_EN in 639b)
    if cur_lang(lang) == "en" and text in MENU_EN:
        return MENU_EN[text]
    return _tr_menu_base(text, lang)


# ---- window: «Kopf (Servos)», folded fine-tuning, deterrence as a table, developer part ------------------------------
if GUI_OK:
    _tk_sub_menu_base = App._sub
    _tk_sidebar_menu_base = App._build_sidebar

    def _menu_tk_sidebar(self, body, tab="settings"):
        _MENU_TL.tk = True
        try:
            return _tk_sidebar_menu_base(self, body, tab)
        finally:
            _MENU_TL.tk = False
    _tk_build_section_menu_base = App._build_section

    def _menu_tk_fold(self, parent, title, n, key):
        """a closed line «Feineinstellungen (n) ▸» with its body (the state is kept like the parts)"""
        h = tk.Frame(parent, bg=C["panel"], cursor="hand2"); h.pack(fill="x", pady=(8, 0))
        al = tk.Label(h, text="▸", bg=C["panel"], fg=C["acc"], font=("DejaVu Sans", 9), cursor="hand2"); al.pack(side="right")
        tl = tk.Label(h, text=tr(title).upper() + (f" ({n})" if n else ""), bg=C["panel"], fg=C["acc"], font=("DejaVu Sans", 7, "bold"),
                      anchor="w", cursor="hand2")
        tl.pack(side="left", fill="x", expand=True)
        body = tk.Frame(parent, bg=C["panel"])
        k = "fine:" + key

        def paint(open_):
            al.config(text="▾" if open_ else "▸")
            if open_:
                body.pack(fill="x", pady=(2, 0), after=h)
            else:
                body.pack_forget()

        def click(_e=None):
            o = k not in self.open_secs
            (self.open_secs.add if o else self.open_secs.discard)(k)
            CFG["ui_open"] = sorted(self.open_secs); save_settings(); paint(o)
        for w_ in (h, al, tl):
            w_.bind("<Button-1>", click)
        paint(k in self.open_secs)
        return body

    def _menu_tk_sub(self, parent, sec, default_open=False):
        _tk_sub_menu_base(self, parent, sec, default_open)
        _MENU_TL.tk = False
        try:
            merged = [s for s in TK_MENU_MERGE.get(sec, ()) if s in SECTIONS and not simple_hidden(None, s)]
        finally:
            _MENU_TL.tk = True
        if not merged or ("sub:" + sec) not in self.subs:
            return
        body = self.subs["sub:" + sec][1]
        fb = _menu_tk_fold(self, body, "Fine-tuning", 0, "merge:" + sec)
        for i, s in enumerate(merged):
            self._sub_block(fb, s, i == 0, True)

    def _menu_tk_build_section(self, sec, sbody, settings_parent=None):
        if sec == "Developer":
            ttk.Label(sbody, text=tr("Only for the developer (switch: System → Device & help → Developer area)."), style="Mut.TLabel",
                      wraplength=330, justify="left").pack(anchor="w")
            for ic, lab, path in (("🧪", "Test bench and test run", "/sim#c-test"), ("⚖", "A/B comparison", "/sim#c-hub"),
                                  ("📈", "Statistics & versions", "/sim#c-hub"), ("🩺", "Diagnosis package", "/tools#diag"),
                                  ("⚗", "Settings of the simulation", "/sim"), ("🛠", "Developer area", "/dev")):
                ttk.Button(sbody, text=ic + " " + tr(lab) + " ›", command=lambda p=path: self._open_page(p)).pack(fill="x", pady=(4, 0))
        if sec == "Deterrence":                     # 4 classes × reaction + sound as a small table (like the web page)
            _MENU_TL.hide = {f"deter_{g}_{w}" for g in ("person", "big", "small", "warm") for w in ("act", "sound")}
        try:
            _tk_build_section_menu_base(self, sec, sbody, settings_parent)
        finally:
            _MENU_TL.hide = ()
        sp = settings_parent if settings_parent is not None else sbody
        if sec == "Deterrence":
            _menu_tk_deter(self, sp)
        if sec == "Presence":
            ttk.Button(sbody, text="📱 " + tr("Choose the phone") + " ›", command=lambda: self._open_page("/tools#pres")).pack(fill="x", pady=(6, 0))
        if not ui_simple_now() or sec in MENU_NO_FOLD or sec in ("Notifications",) or sec not in SECTIONS:
            return
        fine = [x for x in TOGGLES + SLIDERS + TEXTS if x[0] == sec and menu_fine(x[1]) and not (CFG["lock_on"] and x[1] in LOCK_DENY_KEYS)
                and x[1] not in TK_AI_MODEL_KEYS + TK_SPECIES_KEYS and not (sec == "Deterrence" and x[1].startswith("deter_") and x[1][-4:] in ("_act", "ound"))]
        if not fine:
            return
        fb = _menu_tk_fold(self, sp, "Fine-tuning", len(fine), sec)
        keys = {x[1] for x in fine}
        for s, key, label in TOGGLES:
            if s == sec and key in keys:
                tg = Toggle(fb, tr(label), CFG[key], lambda val, k=key: self._set(k, val)); tg.pack(fill="x", pady=3)
                self.vars[key] = tg; self._g2_q(tg, key)
        for s, key, label, lo, hi, step in SLIDERS:
            if s == sec and key in keys:
                row = ttk.Frame(fb); row.pack(fill="x", pady=(6, 0))
                ttk.Label(row, text=tr(label)).pack(side="left")
                vl = ttk.Label(row, text=str(CFG[key]), style="Mut.TLabel"); vl.pack(side="right"); self.value_labels[key] = vl
                self._g2_q(row, key)
                v = tk.DoubleVar(value=CFG[key]); self.vars[key] = v
                sc = ttk.Scale(fb, from_=lo, to=hi, variable=v, orient="horizontal", command=lambda val, k=key, st=step: self._slide(k, float(val), st))
                sc.pack(fill="x")
                sc.bind("<ButtonPress-1>", lambda e, k=key: setattr(self, "dragging", k))
                sc.bind("<ButtonRelease-1>", lambda e: (setattr(self, "dragging", None), self.root.focus_set()))
        tk_ = [x[1] for x in TEXTS if x[0] == sec and x[1] in keys]
        if tk_:
            _MENU_TL.all = True
            try:
                self._build_texts(fb, sec, only=tk_)
            finally:
                _MENU_TL.all = False

    def _menu_tk_deter(self, parent):
        """Abschreckung: Person / grosses Tier / kleines Tier / warmer Körper × Reaktion + Klang"""
        f = tk.Frame(parent, bg=C["panel"]); f.pack(fill="x", pady=(8, 0))
        err = ttk.Label(parent, text="", style="Mut.TLabel", foreground=C["red"], wraplength=330, justify="left")
        for c_, h_ in enumerate(("", "Reaction", "Sound")):
            tk.Label(f, text=tr(h_).upper() if h_ else "", bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").grid(row=0, column=c_, sticky="w")
        for r_, (g, lab) in enumerate((("person", "Person"), ("big", "Big animal"), ("small", "Small animal"), ("warm", "Warm body")), 1):
            tk.Label(f, text=tr(lab), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 9), anchor="w").grid(row=r_, column=0, sticky="w", padx=(0, 6), pady=2)
            for c_, w in ((1, "act"), (2, "sound")):
                key = f"deter_{g}_{w}"
                pairs = text_choice_pairs(key); lab_ = dict(pairs); back = {l: c for c, l in pairs}
                cb = ttk.Combobox(f, values=[l for _c, l in pairs], state="readonly", width=14); cb.set(lab_.get(CFG[key], CFG[key]))
                cb.grid(row=r_, column=c_, sticky="ew", padx=(0, 4), pady=2)
                cb.bind("<<ComboboxSelected>>", lambda e, k=key, c=cb, bk=back: (self.root.focus_set(), self._text_set(k, bk.get(c.get(), c.get()), err)))
        f.columnconfigure(1, weight=1); f.columnconfigure(2, weight=1)
        err.pack(anchor="w")

    # wraps: App._sub
    App._sub = _menu_tk_sub
    # wraps: App._build_sidebar
    App._build_sidebar = _menu_tk_sidebar
    # wraps: App._build_section
    App._build_section = _menu_tk_build_section


def menu_selftest():
    """every section is in a group of the window and of the web page, the developer sections hide without dev_area,
    «Simple» keeps every setting of a shown part (folded), short labels have German"""
    listed = {x for g in TK_GROUPS + TK_SIM_GROUPS for x in g[2] if x} | {s for v in TK_MENU_MERGE.values() for s in v} \
        | {"Messages", "SMS (LTE stick)"}                   # the window shows them inside «Push-Nachrichten» (571a)
    miss = [s for s in SECTIONS if s not in listed]
    assert not miss, f"sections without a window group: {miss}"
    page = WEB_PAGE
    for s in SECTIONS:
        if s in SECTIONS_ON_SIM_PAGE:
            continue
        assert ('sec: "' + s + '"') in page or ("also: [" in page and '"' + s + '"' in page), f"section not in the web GROUPS: {s}"
    old = CFG.get("dev_area")
    try:
        CFG["dev_area"] = False
        assert simple_hidden(None, "Developer") and simple_hidden(None, "Servo driver"), "developer sections visible without dev_area"
        CFG["dev_area"] = True
        assert not simple_hidden(None, "Developer"), "developer section hidden with dev_area"
    finally:
        CFG["dev_area"] = old
    _G2_SIMPLE.v = True
    try:
        sch = web_schema("de")
        keys = {x["key"] for s in sch for k_ in ("toggles", "sliders", "texts") for x in s[k_]}
        assert "tamper_tilt" in keys and "report_from" in keys, "«Simple» lost settings of a shown part"
        assert any(x.get("fine") for s in sch for x in s["sliders"]), "no folded fine-tuning in «Simple»"
    finally:
        _G2_SIMPLE.v = None
    nde = [x[2] for x in TOGGLES + SLIDERS + TEXTS if x[1] in MENU_LONG and x[2] not in DE]
    assert not nde, f"short labels without German: {nde[:5]}"
    long_ = [x[1] for x in TOGGLES + SLIDERS + TEXTS if x[0] != "Simulator" and len(DE.get(x[2], x[2])) > 44]
    return f"{len(MENU_LONG)} short labels, {len(long_)} German labels still over 44 characters" if long_ else f"{len(MENU_LONG)} short labels"


SELFTEST_EXTRA.append(("Menu structure 2 (groups, Simple, developer, short labels)", menu_selftest))
