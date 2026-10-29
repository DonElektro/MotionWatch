#@ MoveEye – Teil 575: Fenster: Zeitleiste der Nacht als einfache Liste, dazu der Wochenbericht. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14: wie Verlauf → Zeitleiste auf der Webseite (523), im Fenster als Liste: Tag wählen (◀ ▶), Nacht / ganzer Tag,
# die Ereignisse nach Stunden; Doppelklick auf eine Aufnahme oder ein Tagebuch-Bild öffnet die Datei. Unten der
# Wochenbericht (426) mit «Jetzt als Push senden». Knopf ◷ oben rechts im Fenster.
# ----------------------------------------------------------------------------
def tk_timeline_win(app):
    w = getattr(app, "_tl_top", None)
    if w is not None and w.winfo_exists():
        w.lift(); _tk_tl_fill(app); return
    w = app._tl_top = tk.Toplevel(app.root); w.title("MoveEye – " + tr("Night timeline")); w.configure(bg=C["bg"]); w.geometry("660x640")
    app._tl_state = {"day": datetime.now().strftime("%Y-%m-%d"), "mode": "night", "lines": {}}
    top = tk.Frame(w, bg=C["bg"]); top.pack(fill="x", padx=12, pady=(10, 4))

    def shift(n):
        d = datetime.strptime(app._tl_state["day"], "%Y-%m-%d") + timedelta(days=n)
        if d.date() <= datetime.now().date():
            app._tl_state["day"] = d.strftime("%Y-%m-%d"); _tk_tl_fill(app)

    def mode():
        app._tl_state["mode"] = "day" if app._tl_state["mode"] == "night" else "night"; _tk_tl_fill(app)
    tk.Button(top, text="◀", command=lambda: shift(-1)).pack(side="left")
    app._tl_lab = tk.Label(top, text="", bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"))
    app._tl_lab.pack(side="left", expand=True)
    tk.Button(top, text="▶", command=lambda: shift(1)).pack(side="left")
    app._tl_mode = tk.Button(top, text="", command=mode); app._tl_mode.pack(side="left", padx=(8, 0))
    tk.Button(top, text=tr("↻ Refresh"), command=lambda: _tk_tl_fill(app)).pack(side="left", padx=(6, 0))
    app._tl_sum = tk.Label(w, text="", bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w", justify="left", wraplength=620)
    app._tl_sum.pack(fill="x", padx=12)
    t_ = app._tl_txt = tk.Text(w, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10), wrap="word", bd=0, padx=10, pady=8, cursor="arrow")
    t_.pack(fill="both", expand=True, padx=12, pady=(4, 6))
    t_.tag_configure("hr", foreground=C["mut"], font=("DejaVu Sans", 9, "bold"), spacing1=6)
    t_.tag_configure("tm", foreground=C["mut"])
    t_.tag_configure("alarm", foreground=C.get("red", "#ff453a"))
    t_.tag_configure("rec", foreground=C.get("acc", "#3b8cff"))
    t_.tag_configure("sight", foreground=C.get("grn", "#3fcf6b"))
    t_.tag_configure("log", foreground=C["mut"])
    t_.tag_configure("wrh", font=("DejaVu Sans", 10, "bold"), spacing1=10)
    t_.tag_configure("tip", foreground=C.get("org", "#f59a4a"))
    t_.bind("<Double-Button-1>", lambda e: _tk_tl_open(app, t_.index(f"@{e.x},{e.y}")))
    bot = tk.Frame(w, bg=C["bg"]); bot.pack(fill="x", padx=12, pady=(0, 10))
    tk.Label(bot, text=tr("Double click: open the recording / the picture"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 8)).pack(side="left")

    def send():
        r, ok = weekrep_send(manual=True)
        try:
            messagebox.showinfo("MoveEye", (("✓ " + tr("sent")) if ok else ("⚠ " + tr("notification is not configured"))) + "\n\n" + r["text"], parent=w)
        except Exception:
            pass
    tk.Button(bot, text=tr("Weekly report: send as push now"), command=send).pack(side="right")
    _tk_tl_fill(app)


def _tk_tl_fill(app):
    t_ = getattr(app, "_tl_txt", None)
    if t_ is None or not t_.winfo_exists():
        return
    st = app._tl_state
    tl = timeline_build(st["day"], st["mode"])
    d = datetime.strptime(tl["day"], "%Y-%m-%d")
    lab = (d.strftime("%a %d.%m.%Y") if st["mode"] == "day" else
           tr("Night") + " " + (d - timedelta(days=1)).strftime("%a") + " → " + d.strftime("%a %d.%m.%Y"))
    app._tl_lab.config(text=lab)
    app._tl_mode.config(text=tr("Whole day") if st["mode"] == "night" else tr("Night 18–09"))
    c = tl["count"]
    s = f"🎬 {c['rec']} {tr('recordings')} · 🦊 {c['animal']} {tr('animals')} · ✉ {c['msg']} {tr('messages')} · 🚨 {c['alarm']} {tr('alarms')}"
    if tl.get("bat"):
        s += f" · 🔋 {tl['bat']['first']:.0f} → {tl['bat']['last']:.0f} %"
    if tl.get("temp"):
        s += f" · 🌡 {tl['temp']['min']:.0f}…{tl['temp']['max']:.0f} °C"
    app._tl_sum.config(text=s)
    t_.config(state="normal"); t_.delete("1.0", "end")
    st["lines"] = {}
    last_h = None
    rows = timeline_text(tl)
    if not rows:
        t_.insert("end", tr("Nothing happened in this night.") if st["mode"] == "night" else tr("Nothing happened on this day."), "tm")
    for hm, kind, text, it in rows:
        if hm[:2] != last_h:
            last_h = hm[:2]; t_.insert("end", f"{last_h}:00\n", "hr")
        line = int(t_.index("end-1c").split(".")[0])
        st["lines"][line] = it
        t_.insert("end", hm + "  ", "tm"); t_.insert("end", text + "\n", kind)
    try:
        wr = weekrep_build()
        t_.insert("end", "\n📈 " + tr("Weekly detection report") + f" ({wr['from']} – {wr['to']})\n", "wrh")
        for ln in wr["lines"]:
            t_.insert("end", "• " + ln + "\n")
        t_.insert("end", "💡 " + wr["tip"] + "\n", "tip")
    except Exception as e:
        t_.insert("end", f"\n{tr('Weekly detection report')}: {e}\n", "tm")
    t_.config(state="disabled")


def _tk_tl_open(app, index):
    it = app._tl_state["lines"].get(int(str(index).split(".")[0]))
    if not it:
        return
    p = None
    if it["type"] == "rec":
        p = rec_path(it["name"])
    elif it["type"] == "sight" and it.get("img"):
        p = os.path.join(diary_dir(), it["img"])
    elif it["type"] == "msg" and it.get("img"):
        p = msglog_img(it.get("id"))
    if not p or not os.path.isfile(p):
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(p)                                     # noqa (Windows only)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, AttributeError) as e:
        app._status("Night report", f"⚠ {e}"[:120])
