#@ MoveEye – Teil 639d: Angleichen MoveEye ↔ Simulator (Daniel 30.10.2026): Entwickler-Schalter geteilt (dev_area an den Simulator), Fenster «Strom» und Teil «System» mit Ausschalten / Neustart / Pause wie im Web. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
#   * sim_state + «dev_area»: the 3D simulator shows its group «Entwickler» when the «Entwickler-Bereich» of MoveEye is on
#     (simulator3d/schnittstelle.json, main.gd on_state) - no longer tied to «Experte»
#   * window: the group «Stromversorgung» is called «Strom» (like the web page); «Pi ausschalten / neu starten / Programm
#     pausieren» are in the first part «System» of the group System (the web page: card «System»), no longer under «Ort & Uhr»
#   * the group «Entwickler» (web 530 devExtras, window 639c) links «Störungen» to the simulator control (/sim#c-stoer)
# ----------------------------------------------------------------------------
_sim_state_639d = sim_state


def sim_state():                                          # + 639d: the developer switch of MoveEye (the simulator shows «Entwickler»)
    d = _sim_state_639d()
    d["dev_area"] = bool(CFG.get("dev_area"))
    return d


ANGL_SYS = "_System"                                      # a part of the window without settings (TK_PSEUDO): power off, restart, pause
TK_PSEUDO.add(ANGL_SYS)
MENU_TITLES[ANGL_SYS] = "System"
TK_SUB_ICONS[ANGL_SYS] = "◉"
for _g in TK_GROUPS:
    if _g[0] == "sys" and ANGL_SYS not in _g[2]:
        _g[2].insert(0, ANGL_SYS)
ANGL_GROUP_DE = {"power": "Strom"}                         # the window group = the web group (530 I18N.de «Power supply»: «Strom»)


if GUI_OK:
    _angl_build_section_base = App._build_section
    _angl_sidebar_base = App._build_sidebar

    def _angl_build_section(self, sec, sbody, settings_parent=None):
        if sec != ANGL_SYS:
            return _angl_build_section_base(self, sec, sbody, settings_parent)
        ttk.Label(sbody, text=tr("Switch off, restart, pause"), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w")
        bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))
        ttk.Button(bf, text="⏻ " + tr("Shut down Pi"), command=lambda: self._power("poweroff")).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text="↻ " + tr("Restart Pi"), command=lambda: self._power("reboot")).pack(side="left", expand=True, fill="x")
        pf = ttk.Frame(sbody); pf.pack(fill="x", pady=(6, 0))
        ttk.Label(pf, text=tr("Pause the program for")).pack(side="left")
        self.pause_cb = ttk.Combobox(pf, state="readonly", width=8, values=[f"{m} min" if m < 60 else f"{m // 60} h" for m in PAUSE_CHOICES])
        self.pause_cb.current(2); self.pause_cb.pack(side="left", padx=(6, 0))
        ttk.Button(sbody, text="⏸ " + tr("Pause program"), command=self._pause).pack(fill="x", pady=(4, 0))
        self.status_labels["Power"] = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left")
        self.status_labels["Power"].pack(anchor="w", pady=(4, 0))

    def _angl_sidebar(self, body, tab="settings"):
        r = _angl_sidebar_base(self, body, tab)
        if cur_lang() == "de":
            for gid, name in ANGL_GROUP_DE.items():
                k = "grp:" + gid
                if k in getattr(self, "group_titles", {}) and k in self.sections:
                    self.group_titles[k] = name
                    self._set_section(k, self._shown.get(k, k in self.open_secs), save=False)   # nurgruppen: as shown
        return r

    # wraps: App._build_section (after 639c)
    App._build_section = _angl_build_section
    # wraps: App._build_sidebar (after 639c)
    App._build_sidebar = _angl_sidebar


def angl_selftest():
    """dev_area goes to the simulator; the window part «System» holds power off / restart / pause"""
    assert "dev_area" in sim_state(), "dev_area missing in sim_state"
    assert any(g[0] == "sys" and g[2] and g[2][0] == ANGL_SYS for g in TK_GROUPS), "window: part «System» missing"
    for k in ("Switch off, restart, pause", "Faults (servos, under-voltage)", "Photo of the place"):
        assert k in DE, f"no German for {k}"
    return "dev_area to the simulator, window part «System», «Strom»"


SELFTEST_EXTRA.append(("Align MoveEye / simulator (developer switch, «Strom», System)", angl_selftest))
