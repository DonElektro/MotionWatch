#@ MoveEye – Teil 572: Fenster – die Reiter Verlauf, Mehr und Simulator und der Assistent «Erkennung verbessern» im Fenster. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Konzept): das Fenster hat dieselben 6 Reiter wie die Webseite (Live · Schutz · Verlauf · Einstellungen · Simulator
# · Mehr). Die Teile hier hängen sich an die Klasse App (570): Knopfleisten für Verlauf und Mehr, der Kopf des Reiters
# Simulator und das Fenster des Assistenten (dieselben 5 Schritte wie im Web, 312).
# ----------------------------------------------------------------------------
def _tk_bar(self, parent, items):
    f = tk.Frame(parent, bg=C["bg"])
    for i, (txt, cmd) in enumerate(items):
        self._fbtn(f, txt, cmd).grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 6), pady=(0, 6))
        f.columnconfigure(i % 3, weight=1)
    return f


def _tk_history_bar(self, parent):
    return self._tk_bar(parent, [("⏺ " + tr("Recordings"), lambda: self._open_page("/recordings")),
                                 ("📔 " + tr("Diary"), lambda: self._open_page("/diary")),
                                 ("✉ " + tr("Messages"), self._messages_win)])


def _tk_more_bar(self, parent):
    def setup():                                     # 586 / 584: the one guide (start again or continue)
        g_ = g2_state()
        g2_action({"action": "again"} if g_["finished"] or not g_["mode"] else {"action": "resume"}, "window"); self._g2_wizard()
    f = self._tk_bar(parent, [("? " + tr("Manual"), self._open_help), ("🎲 " + tr("Game corner"), lambda: self._open_page("/party")),
                              ("🛠 " + tr("Tools"), lambda: self._open_page("/tools")), ("💬 " + tr("Feedback to the developer"), self._feedback),
                              ("🌐 " + tr("Overview"), lambda: self._open_page("/more")), ("ℹ " + tr("About MoveEye"), self._about_win), ("🧭 " + tr("Setup"), setup),
                              ("↺ " + tr("Reset all tours"), lambda: (g2_action({"action": "tours_reset"}, "window"), self._status("Setup", tr("All tours will show again.")))),
                              (tr("⚠ Reset to factory settings …"), self._g2_factory)])
    self._g2_more_bar = f
    return f


def _tk_sim_head(self, inner):
    card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
    tk.Label(card, text="🎯 " + tr("Improve detection"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
    ttk.Label(card, text=tr("One guided flow: check, measure, improve, see the result. Replaces the single tools (they stay in «Expert»)."),
              style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(2, 6))
    bf = tk.Frame(card, bg=C["panel"]); bf.pack(fill="x")
    self._fbtn(bf, "🎯 " + tr("Improve detection") + " …", self._tune_win, primary=True).pack(side="left", padx=(0, 6))
    self._fbtn(bf, "🎛 " + tr("Simulator centre") + " (" + tr("browser") + ")", lambda: self._open_page("/sim#c-hub")).pack(side="left")


def _tune_txt(st):
    """the state of the assistant as plain text lines (window)"""
    def pl(p):
        return ("🌙 " + tr("Night")) if p == "night" else ("☀ " + tr("Day"))
    def res(last):
        out = []
        for r in last.get("plans") or []:
            kept = ", ".join(tr(x["title"]) for x in r.get("kept") or [])
            out.append(f"{pl(r['plan'])}: {tr('Score')} {r.get('base', '–')} → {r.get('best', '–')} · " + ((tr("kept") + ": " + kept) if kept else tr("nothing was clearly better - everything stays as it was")))
        if not out:
            out.append(("⚠ " + tr(last["msg"])) if last.get("msg") else tr("nothing was clearly better - everything stays as it was"))
        if last.get("undone"):
            out.append("↩ " + tr("Undone - the values from before are back."))
        elif last.get("changed"):
            out.append(f"{len(last['changed'])} {tr('values changed')}: " + " · ".join(f"{k} {a} → {b}" for k, a, b in last["changed"]))
        return "\n".join(out)
    if st["busy"]:
        N = st["now"]
        t_ = "⏳ " + tr("Running") + ": " + (f"{st['i'] + 1}/{st['n']} · " if st["n"] > 1 else "") + pl(st["step"] or "quick")
        t_ += "\n" + ((f"🤖 {tr('Try')} {N['try']}/{N['tries']} · " + (tr(N["what"]) if N["what"] else tr("first a test run as it is now"))) if N["tries"] else tr("starting …"))
        if N.get("running") and N.get("left") is not None:
            t_ += f"\n{tr('still about')} {max(1, round(float(N['left']) / 60))} {tr('min')}"
        return t_
    return res(st["last"]) if st.get("last") else "–"


def _tune_win(self):
    """the assistant «Erkennung verbessern» in the window: the same 5 steps as on the web page, one below the other"""
    w = getattr(self, "_tune_top", None)
    if w is not None and w.winfo_exists():
        w.lift(); return
    w = self._tune_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Improve detection")); w.configure(bg=C["bg"])
    w.geometry("560x640" if self.root.winfo_screenheight() >= 700 else "520x" + str(max(380, self.root.winfo_screenheight() - 60)))
    cv = tk.Canvas(w, bg=C["bg"], bd=0, highlightthickness=0); sb = ttk.Scrollbar(w, orient="vertical", command=cv.yview)
    cv.configure(yscrollcommand=sb.set); sb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
    f = tk.Frame(cv, bg=C["bg"], padx=14, pady=10); win = cv.create_window((0, 0), window=f, anchor="nw")
    f.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all"))); cv.bind("<Configure>", lambda e: cv.itemconfigure(win, width=e.width))
    def head(n, txt):
        tk.Label(f, text=f"{n}  {tr(txt)}".upper(), bg=C["bg"], fg=C["acc"], font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", pady=(12, 2))
    def lab(txt="", mut=True):
        l_ = tk.Label(f, text=txt, bg=C["bg"], fg=C["mut"] if mut else C["txt"], font=("DejaVu Sans", 9 if mut else 10), wraplength=500, justify="left", anchor="w")
        l_.pack(fill="x"); return l_
    tk.Label(f, text="🎯 " + tr("Improve detection"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 13, "bold"), anchor="w").pack(fill="x")
    lab(tr("MoveEye tests itself in the 3D simulator: people and animals walk past, and the simulator knows exactly what MoveEye should have reported. The assistant tries changes and keeps only what is clearly better."))
    head(1, "Check"); l_chk = lab(mut=False)
    head(2, "How thorough?")
    dv = tk.StringVar(value="quick")
    for v, ic, n, note in (("quick", "⚡", "Quick", "only the day test, up to 3 tries - about 10 to 20 minutes"),
                           ("thorough", "🔬", "Thorough", "day and night, up to 4 tries each - about 40 to 60 minutes")):
        tk.Radiobutton(f, text=f"{ic} {tr(n)} – {tr(note)}", variable=dv, value=v, bg=C["bg"], fg=C["txt"], selectcolor=C["field"],
                       activebackground=C["bg"], activeforeground=C["txt"], anchor="w", justify="left", wraplength=480).pack(fill="x")
    bf = tk.Frame(f, bg=C["bg"]); bf.pack(fill="x", pady=(6, 0))
    def start():
        ok, err = tune_assist_start(dv.get())
        if not ok:
            messagebox.showinfo(tr("Improve detection"), tr_err(err), parent=w)
        paint()
    b_start = self._fbtn(bf, "▶ " + tr("Start"), start, primary=True); b_start.pack(side="left", padx=(0, 6))
    b_stop = self._fbtn(bf, "⏹ " + tr("Stop"), lambda: (tune_assist_stop(), paint())); b_stop.pack(side="left")
    lab(tr("You can close the page - the assistant keeps running. The auto-tuner pauses meanwhile."))
    head(3, "Improving"); l_run = lab(mut=False)
    head(4, "Result"); l_res = lab(mut=False)
    bu = tk.Frame(f, bg=C["bg"]); bu.pack(fill="x", pady=(4, 0))
    def undo():
        ok, err = tune_assist_undo()
        if not ok:
            messagebox.showinfo(tr("Improve detection"), tr_err(err), parent=w)
        paint()
    b_undo = self._fbtn(bu, "↩ " + tr("Undo"), undo)
    head(5, "Keep it up")
    togs = {}
    # 2.98.24 («Sim-Schalter nur einmal»): Trainings-Nacht, Wochen-Check, Fehlalarm-Lernen only once - in the window under
    # «Einstellungen der Simulation» (web: the tiles of the Simulator centre)
    for key, title, note in (("auto_tune", "Auto-tuner at the real place", "adapts the sensitivity to the place all the time (wind, light); starts from the measured values"),):
        row = tk.Frame(f, bg=C["panel"], padx=10, pady=6, highlightthickness=1, highlightbackground=C["line"]); row.pack(fill="x", pady=(0, 4))
        tg = Toggle(row, tr(title), bool(CFG.get(key)), lambda v, k=key: (tune_assist_set(k, v), paint())); tg.pack(fill="x")
        tk.Label(row, text=tr(note), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8), wraplength=460, justify="left", anchor="w").pack(fill="x")
        togs[key] = tg
    lab("🧰 " + tr("Single tools (Expert)") + ": " + tr("Test run, A/B comparison, thresholds automatic … in the tab Simulator, Simulator centre (view «Expert»)."))
    lab("🎛 " + tr("Training night, weekly check, false alarm learning: tab Simulator, «Settings of the simulation» (web: tiles of the Simulator centre)."))
    def paint():
        if not w.winfo_exists():
            return
        st = tune_assist_state()
        miss = st["missing"]
        l_chk.config(text=("✅ " + tr("Everything ready.")) if not miss else tr("Still missing:") + "\n" + "\n".join("⚠ " + m["text"] for m in miss))
        l_run.config(text=_tune_txt(st) if st["busy"] else "–")
        l_res.config(text=_tune_txt(dict(st, busy=False)) if st.get("last") else "–")
        if st.get("last") and st["last"].get("can_undo"):
            b_undo.pack(side="left")
        else:
            b_undo.pack_forget()
        if st["busy"]:
            b_start.pack_forget(); b_stop.pack(side="left")
        else:
            b_stop.pack_forget(); b_start.pack(side="left", padx=(0, 6))
        for k, tg in togs.items():
            if tg.get() != bool(CFG.get(k)):
                tg.set(bool(CFG.get(k)))
    def loop():
        if w.winfo_exists():
            paint(); w.after(2500, loop)
    loop()


for _n, _f in (("_tk_bar", _tk_bar), ("_tk_history_bar", _tk_history_bar), ("_tk_more_bar", _tk_more_bar), ("_tk_sim_head", _tk_sim_head),
               ("_tune_win", _tune_win)):
    setattr(App, _n, _f)
