#@ MoveEye – Teil 595: Fenster: der Knopf «⏹ Stopp» (Not-Aus der Servos) verschwindet in der Simulation (CFG sim_on) – dort werden die echten Servos nicht benutzt. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): the emergency stop «⏹ Stopp» is hidden while MoveEye runs in simulation mode - the real servos
# are not used then. The web side is in 541 (servo_client_state "sim" → #srv-stop hidden); the setting servo_stop_btn stays for
# the real hardware. Here the window: every «⏹ Stopp» made by App._fbtn with the command _srv_estop_btn (570, all three
# layouts of the camera bar) is remembered and taken off / put back by App._refresh (it runs every few seconds).
# ----------------------------------------------------------------------------

_ss_fbtn_before = App._fbtn


def _ss_fbtn(self, parent, text, cmd, *a, **k):
    b = _ss_fbtn_before(self, parent, text, cmd, *a, **k)
    try:
        if cmd == self._srv_estop_btn:
            self.__dict__.setdefault("_ss_stop_btns", []).append(b)
    except Exception:
        pass
    return b


def _ss_stop_show(self):
    """the «⏹ Stopp» buttons: hidden in the simulation, back with the real hardware"""
    hide = bool(CFG.get("sim_on"))
    keep = []
    for b in getattr(self, "_ss_stop_btns", []):
        try:
            if not b.winfo_exists():
                continue
        except Exception:
            continue
        keep.append(b)
        st = getattr(b, "_ss_gone", None)
        if hide and st is None:
            mgr = b.winfo_manager()
            if mgr == "pack":
                sl = b.master.pack_slaves()
                i = sl.index(b) if b in sl else -1
                nxt = sl[i + 1] if 0 <= i < len(sl) - 1 else None
                b._ss_gone = ("pack", {k_: v_ for k_, v_ in b.pack_info().items() if k_ != "in"}, nxt)
                b.pack_forget()
            elif mgr == "grid":
                b._ss_gone = ("grid", None, None)
                b.grid_remove()
        elif not hide and st is not None:
            b._ss_gone = None
            if st[0] == "pack":
                kw = dict(st[1])
                try:
                    if st[2] is not None and st[2].winfo_exists() and st[2].winfo_manager() == "pack" and st[2].master is b.master:
                        kw["before"] = st[2]
                except Exception:
                    pass
                b.pack(**kw)
            else:
                b.grid()
    self._ss_stop_btns = keep


_ss_refresh_before = App._refresh


def _ss_refresh(self, *a, **k):
    r = _ss_refresh_before(self, *a, **k)
    try:
        _ss_stop_show(self)
    except Exception:
        pass
    return r


# wraps: App._fbtn
App._fbtn = _ss_fbtn
# wraps: App._refresh
App._refresh = _ss_refresh
