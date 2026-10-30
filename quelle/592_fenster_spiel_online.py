#@ MoveEye – Teil 592: Fenster – im Reiter Simulator die Karte «Spiel: Mensch gegen KI · Online-Einladung» (wie im Web, 543): beide Runden starten, Ergebnis, Einladungslink mit QR-Code erstellen / zurückziehen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
def _gonl_cmp_text(S):
    """the state of «Human vs AI» as plain lines (window)"""
    if not isinstance(S, dict):
        return "–"
    if S.get("ok") is False and S.get("error"):
        return "⚠ " + tr(str(S["error"]))
    st = S.get("state")
    if st in ("r1", "pause", "r2"):
        lab = {"r1": "Round 1 of 2: a person guards", "r2": "Round 2 of 2: MoveEye guards the same round", "pause": "Short break between the rounds"}[st]
        return "⏳ " + tr(lab) + f" · {tr('time left')} {max(1, int(S.get('left_s') or 0) // 60)} {tr('min')}"
    R = S.get("result") or {}
    if R.get("title"):
        g = tr("Human") if R.get("guard_human") else tr("Bot guard")
        out = [f"⚖ {tr('Who caught more?')} {g} {R.get('human', 0)} · MoveEye {R.get('mw', 0)}"]
        for p in R.get("per") or []:
            f = {"human": g + " " + tr("faster"), "mw": "MoveEye " + tr("faster"), "same": tr("same speed")}.get(p.get("faster"), tr("nobody caught him"))
            out.append(f"  {p.get('n')}: {p.get('human')} · {p.get('mw')} – {f}")
        out.append(f"{tr('False alarms')}: {g} {R.get('false_human', 0)} · MoveEye {R.get('false_mw', 0)}")
        if R.get("missed"):
            out.append(f"🧠 {tr('Human saw, MoveEye missed')}: {R['missed']} → {R.get('pics', 0)} {tr('Learning pictures')}, {R.get('ways', 0)} {tr('Test bench ways')}")
        return "\n".join(out)
    return ("" if S.get("mw") else "⚠ " + tr("MoveEye is not connected to the simulator game"))


def _tk_gonl_card(self, inner):
    card = self._panel(inner); card.pack(fill="x", pady=(0, 8))
    tk.Label(card, text="🎮 " + tr("Human vs AI") + " · " + tr("Online beyond the WLAN"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x")
    ttk.Label(card, text=tr("cmp-note"), style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(2, 4))
    cmp_l = ttk.Label(card, text="–", wraplength=520, justify="left"); cmp_l.pack(anchor="w")
    bf = tk.Frame(card, bg=C["panel"]); bf.pack(fill="x", pady=(4, 6))
    nb = tk.StringVar(value="2")
    ttk.Combobox(bf, textvariable=nb, values=["1", "2", "3"], width=3, state="readonly").pack(side="left", padx=(0, 4))
    tk.Label(bf, text=tr("Bots"), bg=C["panel"], fg=C["mut"]).pack(side="left", padx=(0, 8))

    def bg(fn, done):
        def run():
            try:
                r = fn()
            except Exception as e:
                r = {"ok": False, "error": tr("simulator not reachable") + f" ({str(e)[:40]})"}
            try:
                self.root.after(0, lambda: done(r))
            except (tk.TclError, RuntimeError):
                pass
        threading.Thread(target=run, daemon=True, name="gonl").start()

    def start():
        log_event("sys", "Game «Human vs AI» started from the window")
        bg(lambda: sim_control({"action": "game_compare", "op": "start", "bots": int(nb.get() or 2), "minutes": 3}), lambda r: cmp_l.configure(text=_gonl_cmp_text(r)))

    self._fbtn(bf, "▶ " + tr("Start both rounds"), start, primary=True).pack(side="left", padx=(0, 6))
    self._fbtn(bf, tr("Stop the comparison"), lambda: bg(lambda: sim_control({"action": "game_compare", "op": "stop"}), lambda r: cmp_l.configure(text=_gonl_cmp_text(r)))).pack(side="left")
    ttk.Label(card, text=tr("online-note"), style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(6, 2))
    inv_l = ttk.Label(card, text="–", wraplength=520, justify="left"); inv_l.pack(anchor="w")
    bf2 = tk.Frame(card, bg=C["panel"]); bf2.pack(fill="x", pady=(4, 0))
    hv = tk.StringVar(value="3")
    ttk.Combobox(bf2, textvariable=hv, values=[str(h) for h in GINV_HOURS], width=3, state="readonly").pack(side="left", padx=(0, 4))
    tk.Label(bf2, text=tr("h"), bg=C["panel"], fg=C["mut"]).pack(side="left", padx=(0, 8))

    def paint_inv():
        st = ginv_state()
        act = [x for x in st["invites"] if x["active"]]
        lines = [("🟢 " + tr("The game is open - guests can join")) if st["game_open"] else ("⚪ " + tr(st["why"] or "the game is not open in the simulator"))]
        lines += [f"🎟 {x['name'] or tr('Game invitation')} · {tr('valid for another')} {max(1, x['left_s'] // 60)} {tr('min')} · {x['players']}/{x['max']} {tr('players')}" for x in act]
        if not act:
            lines.append(tr("no invitation yet"))
        if not st["public"]:
            lines.append("⚠ " + tr("local-warn"))
        return "\n".join(lines), act, st

    def make():
        inv, err = ginv_create(int(hv.get() or 3), 6, "")
        if inv is None:
            self._status("Simulator", tr(err)); return
        url = ginv_url(inv, ginv_base())
        qr_tk_dialog(self.root, url, tr("Game invitation"), secret=True,
                     note=tr("Only the game: the guest sees no camera picture and no settings. Whoever has the link can play until it expires."))
        refresh()

    def revoke_all():
        ginv_revoke("all"); refresh()

    self._fbtn(bf2, "➕ " + tr("Make the invitation"), make).pack(side="left", padx=(0, 6))
    self._fbtn(bf2, tr("Revoke all"), revoke_all).pack(side="left")

    def refresh():
        def work():
            try:
                c_ = sim_control({"action": "game_compare", "op": "state"})
            except Exception:
                c_ = None
            try:
                i_ = paint_inv()
            except Exception:
                i_ = ("–", [], {})
            def show():
                if not card.winfo_exists():
                    return
                cmp_l.configure(text=_gonl_cmp_text(c_) if c_ else tr("simulator not reachable"))
                inv_l.configure(text=i_[0])
            try:
                self.root.after(0, show)
            except (tk.TclError, RuntimeError):
                pass
        threading.Thread(target=work, daemon=True, name="gonl").start()

    def loop():
        try:
            if not card.winfo_exists():
                return
        except tk.TclError:
            return
        if CFG.get("sim_on"):
            refresh()
        card.after(6000, loop)
    card.after(500, loop)


_tk_sim_head_base = _tk_sim_head


def _tk_sim_head(self, inner):
    """2.98.x: the card «Human vs AI · Online» right under «Improve detection» (the same as on the page Simulator, 543)"""
    _tk_sim_head_base(self, inner)
    _tk_gonl_card(self, inner)


setattr(App, "_tk_sim_head", _tk_sim_head)
setattr(App, "_tk_gonl_card", _tk_gonl_card)
