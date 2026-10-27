"""The window symbol: Motion Watch's radar eye with a green globe (docs/icons/mw_sim_welt_512.png in Motion Watch's
project, made smaller)."""
import os
import tkinter as tk

_IMG = {}


def set_icon(win):
    """Give a tkinter window (and every window opened from it) the MW Sim · Welt symbol. Without the file: no symbol."""
    try:
        if "img" not in _IMG:
            _IMG["img"] = tk.PhotoImage(master=win, file=os.path.join(os.path.dirname(__file__), "icon.png"))
        win.iconphoto(True, _IMG["img"])
    except (tk.TclError, OSError):
        pass
