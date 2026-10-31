#@ MoveEye – Teil 599f: Fenster: Karte «Hier steht etwas, das wie eine Person aussieht – ignorieren?» (feste Fehl-Personen, 418), gleicher Text und gleiche Knöpfe wie im Web. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheid Daniel (31.10.2026): the card comes into the desktop window too. App._refresh (every few seconds) looks at
# fixp_state(); a new card opens a small window (like the walk test, 575) with the picture of the spot and the buttons
# «Ignorieren (Maske übernehmen)» / «Ist eine Person» / «Später» - the same answer as the web card (fixp_answer, 418).
# ----------------------------------------------------------------------------
def _app_fixp_card(self, f):
    import base64
    old = getattr(self, "_fx_win", None)
    try:
        if old is not None and old.winfo_exists():
            old.destroy()
    except Exception:
        pass
    win = tk.Toplevel(self.root); self._fx_win = win
    win.title("MoveEye – " + tr("Something here looks like a person - ignore it?"))
    ttk.Label(win, text="🌲 " + tr("Something here looks like a person - ignore it?"), font=("TkDefaultFont", 12, "bold"),
              wraplength=520, justify="left").pack(anchor="w", padx=12, pady=(12, 6))
    o = next((o for o in FIXP["offers"] if o["id"] == f["id"]), None)
    if o and o.get("jpg"):
        try:
            im = cv2.imdecode(np.frombuffer(o["jpg"], np.uint8), cv2.IMREAD_COLOR)
            if im is not None and im.shape[1] > 520:
                im = cv2.resize(im, (520, int(im.shape[0] * 520 / im.shape[1])))
            ok, buf = cv2.imencode(".png", im)
            if ok:
                ph_ = tk.PhotoImage(data=base64.b64encode(buf.tobytes()).decode())
                lb = ttk.Label(win, image=ph_); lb.image = ph_; lb.pack(padx=12, pady=4)
        except Exception:
            pass
    ttk.Label(win, text=tr("It has not moved for minutes. MoveEye treats it as a thing for now (no alarm, the head does not follow); a mask keeps it so."
                           if f.get("auto") else "It has not moved for minutes. It still counts as a person (alarm, the head follows) until you tap «Ignore»."),
              style="Mut.TLabel", wraplength=520, justify="left").pack(anchor="w", padx=12, pady=(4, 8))
    bf = ttk.Frame(win); bf.pack(fill="x", padx=12, pady=(0, 12))

    def ans(op):
        ok, err = fixp_answer(f["id"], op)
        try:
            self._status("Detection", ("✓ " + tr("Mask made")) if ok and op == "mask" else ("" if ok else "⚠ " + tr(err or "error")))
        except Exception:
            pass
        try:
            win.destroy()
        except Exception:
            pass
    ttk.Button(bf, text=tr("Ignore (make a mask)"), command=lambda: ans("mask")).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text=tr("It is a person"), command=lambda: ans("person")).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text=tr("Later"), command=lambda: ans("later")).pack(side="left", expand=True, fill="x")


App._fixp_card = _app_fixp_card
_fx_tk_refresh_before = App._refresh


def _fx_tk_refresh(self, *a, **k):
    r = _fx_tk_refresh_before(self, *a, **k)
    try:
        offs = fixp_state()["offers"]
        f = offs[0] if offs else None
        if f and getattr(self, "_fx_shown", None) != f["id"]:
            self._fx_shown = f["id"]
            self._fixp_card(f)
    except Exception:
        pass
    return r


# wraps: App._refresh
App._refresh = _fx_tk_refresh


def fixp_tk_selftest():
    """the window card has the same texts and the same three answers as the web card (418)"""
    import inspect
    src = inspect.getsource(_app_fixp_card)
    for k in FIXP_MAIN_KEYS:
        assert k in src and k in FIXP_MAIN_JS, k
    for op in ("mask", "person", "later"):
        assert f'ans("{op}")' in src and f'ans("{op}")' in FIXP_MAIN_JS, op
    return True


SELFTEST_EXTRA.append(("Card «ignore it?» in the window = web (599f / 418)", fixp_tk_selftest))
