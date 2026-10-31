#@ MoveEye – Teil 599d: Nacht-Testlauf im Fenster (Karte im Reiter Simulator: Stand, letzter Bericht, Start / Abbrechen nur für den Besitzer, Bericht im Browser). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «Nacht-Testlauf» (579b). Like the tracking parcours (599a): the window shows the short form, the full report with
# pictures, curves and the comparison of the last 10 runs is the page /nacht (browser). The window on the Pi counts as the
# owner - but in operator mode (390) only the report is shown (no start / stop), like on the page.
# ----------------------------------------------------------------------------
_tk_sim_head_nacht_base = _tk_sim_head


def _tk_nacht_txt():
    out = []
    if NACHT["busy"]:
        out.append("⏳ " + tr("Night test run is running") + " · " + str(NACHT.get("step") or ""))
    runs = nacht_runs()
    if runs:
        r = runs[-1]
        out.append("🌙 " + tr("Last run") + " (" + str(r.get("t")) + ", MoveEye " + str(r.get("mw_version")) + "): " + nacht_push_text(r))
    if NACHT.get("err"):
        out.append("⚠ " + tr_err(NACHT["err"]))
    return "\n".join(out) or tr("whole night with truth")


def _tk_sim_head(self, inner):
    """+ 599d: a short card «Nacht-Testlauf» under the other cards of the tab Simulator"""
    _tk_sim_head_nacht_base(self, inner)
    card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
    tk.Label(card, text="🌙 " + tr("Night test run"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
    ttk.Label(card, text=tr("nacht-note"), style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(2, 4))
    lab = ttk.Label(card, text=_tk_nacht_txt(), style="Mut.TLabel", wraplength=520, justify="left"); lab.pack(anchor="w", pady=(0, 6))
    bf = tk.Frame(card, bg=C["panel"]); bf.pack(fill="x")

    def start():
        ok, err = nacht_start(None)
        if not ok:
            messagebox.showinfo(tr("Night test run"), tr_err(err), parent=card)
        lab.config(text=_tk_nacht_txt())

    def stop():
        nacht_stop()
        lab.config(text=_tk_nacht_txt())
    if nacht_may("admin"):                                 # the same buttons and order as on the page: start / abort, then the report
        self._fbtn(bf, "🌙 " + tr("Start night test run"), start, primary=True).pack(side="left", padx=(0, 6))
        self._fbtn(bf, "⏹ " + tr("Abort the night test run"), stop).pack(side="left", padx=(0, 6))
    else:
        ttk.Label(bf, text="🔒 " + tr("Operator mode: only the owner can start or stop the night test run – the reports can be viewed."),
                  style="Mut.TLabel", wraplength=360, justify="left").pack(side="left", padx=(0, 6))
    self._fbtn(bf, "📄 " + tr("Open the report") + " (" + tr("browser") + ")", lambda: self._open_page("/nacht")).pack(side="left")

    def loop():
        try:
            if not card.winfo_exists():
                return
            lab.config(text=_tk_nacht_txt())
        except tk.TclError:
            return
        card.after(5000, loop)
    card.after(5000, loop)


setattr(App, "_tk_sim_head", _tk_sim_head)
