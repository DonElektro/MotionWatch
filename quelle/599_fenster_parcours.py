#@ MoveEye – Teil 599: Verfolgungs-Parcours im Fenster (Regler «Vorausschauen» bei Kamera / Servos, Karte im Reiter Simulator mit dem letzten Lauf, Start, Vorschlag des Auto-Tunings übernehmen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Plan Daniel 30.10.2026 (docs/Verfolgungs_Parcours.md). Here (not in 416) because SLIDERS (570) and the tab Simulator of the
# window (572 / 592) come after 416. The full tile (A/B side by side, auto-tuning, game) is the web page; the window shows
# the short form and opens the tile in the browser (like the other single tools of the Simulator centre).
# ----------------------------------------------------------------------------
_pi = max([i for i, s_ in enumerate(SLIDERS) if s_[1] == "track_deadzone"] or [len(SLIDERS) - 1])
SLIDERS.insert(_pi + 1, ("Camera / Servos", "track_lead", "Tracking: look ahead (seconds, 0 = off)", 0.0, 1.0, 0.05))
_tk_sim_head_599 = _tk_sim_head


def _tk_parc_txt():
    runs = parc_runs()
    out = []
    if PARC["busy"]:
        out.append("⏳ " + str(PARC.get("step") or ""))
    if runs:
        r = runs[-1]["report"]
        out.append("🎯 " + tr("Last run") + " (" + runs[-1]["t"] + "): " + tr("grade") + " %.1f" % float(r.get("note") or 0) + " · "
                   + " · ".join("%s %.1f" % (l.get("id"), float(l.get("note") or 0)) for l in r.get("lessons") or []))
    tu = PARC.get("tune") or {}
    if tu.get("cands"):
        b = tu["cands"][int(tu.get("best") or 0)]
        out.append("🤖 " + tr("Auto-tuning") + ": ★ " + ", ".join("%s %s" % (k, b["params"].get(k)) for k in PARC_KEYS) + " · " + tr("grade") + " %.1f" % float(b["note"])
                   + (" · ✓ " + tr("taken over") if tu.get("applied") else ""))
    return "\n".join(out) or tr("Train the following")


def _tk_sim_head(self, inner):
    """+ 599: a short card «Verfolgungs-Parcours» under the cards of 572 / 592"""
    _tk_sim_head_599(self, inner)
    card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
    tk.Label(card, text="🎯 " + tr("Tracking parcours"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
    ttk.Label(card, text=tr("Train following in the simulator: lessons, A/B comparison, auto-tuning (proposal only)."), style="Mut.TLabel",
              wraplength=520, justify="left").pack(anchor="w", pady=(2, 4))
    lab = ttk.Label(card, text=_tk_parc_txt(), style="Mut.TLabel", wraplength=520, justify="left"); lab.pack(anchor="w", pady=(0, 6))
    bf = tk.Frame(card, bg=C["panel"]); bf.pack(fill="x")

    def start():
        ok, err = parc_start([1, 5, 6])
        if not ok:
            messagebox.showinfo(tr("Tracking parcours"), tr_err(err), parent=card)
        lab.config(text=_tk_parc_txt())

    def take():
        ok, err = parc_apply()
        if not ok:
            messagebox.showinfo(tr("Tracking parcours"), tr_err(err), parent=card)
        lab.config(text=_tk_parc_txt())
    # the same buttons and order as on the page / in the simulator window: ▶ Start · ⏹ Stopp, then the tile
    self._fbtn(bf, "▶ " + tr("Start") + " (1, 5, 6)", start, primary=True).pack(side="left", padx=(0, 6))
    self._fbtn(bf, "⏹ " + tr("Stop"), lambda: sim_hub_do("parc", {"do": "stop"})).pack(side="left", padx=(0, 6))
    self._fbtn(bf, "✓ " + tr("take over proposal ★"), take).pack(side="left", padx=(0, 6))
    self._fbtn(bf, "🎯 " + tr("Tracking parcours") + " (" + tr("browser") + ")", lambda: self._open_page("/sim#c-parc")).pack(side="left")

    def loop():
        try:
            if not card.winfo_exists():
                return
            lab.config(text=_tk_parc_txt())
        except tk.TclError:
            return
        card.after(5000, loop)
    card.after(5000, loop)


setattr(App, "_tk_sim_head", _tk_sim_head)
