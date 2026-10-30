#@ MoveEye – Teil 593: Aufräumen im Fenster – Gruppe «Tierart» in der KI-Erkennung (wie «KI-Modell»). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# aufr (Konzept-Check): the settings of the animal species (second AI model, part 180) stood scattered between the other
#   switches of «KI-Erkennung» - now ONE framed group «🦊 Tierart» below «🧠 KI-Modell» (the web page: spGroup in 530).
#   570 leaves the keys TK_SPECIES_KEYS out of its loops and calls App._tk_species_group.
# ----------------------------------------------------------------------------
def _app_tk_species_group(self, parent, sec):
    keys = [k for k in TK_SPECIES_KEYS if not simple_hidden(k) and not (CFG["lock_on"] and k in LOCK_DENY_KEYS)]
    if not keys:
        return
    box = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
    box.pack(fill="x", pady=(10, 0))
    tk.Label(box, text="🦊 " + tr("Animal species"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
    for s, key, label in TOGGLES:
        if s == sec and key in keys:
            tg = Toggle(box, tr(label), CFG[key], lambda val, k=key: self._set(k, val)); tg.pack(fill="x", pady=3)
            self.vars[key] = tg; self._g2_q(tg, key)
    self._build_texts(box, sec, only=tuple(k for k in keys if k in ("species_model", "species_norm")))
    for s, key, label, lo, hi, step in SLIDERS:
        if s != sec or key not in keys:
            continue
        row = ttk.Frame(box); row.pack(fill="x", pady=(6, 0))
        ttk.Label(row, text=tr(label)).pack(side="left")
        vl = ttk.Label(row, text=str(CFG[key]), style="Mut.TLabel"); vl.pack(side="right"); self.value_labels[key] = vl
        self._g2_q(row, key)
        v = tk.DoubleVar(value=CFG[key]); self.vars[key] = v
        sc = ttk.Scale(box, from_=lo, to=hi, variable=v, orient="horizontal", command=lambda val, k=key, st=step: self._slide(k, float(val), st))
        sc.pack(fill="x")
        sc.bind("<ButtonPress-1>", lambda e, k=key: setattr(self, "dragging", k))
        sc.bind("<ButtonRelease-1>", lambda e: (setattr(self, "dragging", None), self.root.focus_set()))
    ttk.Label(box, text=tr("Install the model: web page, Settings → AI detection → «Animal species» (address of an .onnx or .zip)"),
              style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(6, 0))


App._tk_species_group = _app_tk_species_group
