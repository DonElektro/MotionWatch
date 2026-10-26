"""The start window: before the simulation starts, choose the map, which places exist (Region map) and what is drawn.
Everything can be changed later in the World tab. The choices are remembered in data/start_choices.json."""
import json
import os
import tkinter as tk
import types
from tkinter import ttk

from simulator.config import SIM
from simulator.scene import maps
from simulator.scene.region import ORDER, TILES, layout

KEYS = ("map", "tiles", "draw_trees", "draw_buildings", "draw_small", "draw_backdrop", "shadows", "bg_traffic", "quality", "time_mode",
        "hour", "people", "start_window")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return {k: d[k] for k in KEYS if k in d}
    except (OSError, ValueError):
        return {}


def save(path, d):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except OSError:
        pass


def apply(d):
    """Put saved / chosen values into the simulator settings."""
    for k in ("draw_trees", "draw_buildings", "draw_small", "draw_backdrop", "shadows", "bg_traffic", "quality", "time_mode", "hour",
              "start_window"):
        if k in d:
            SIM[k] = d[k]
    if "tiles" in d:
        SIM["tiles"] = list(d["tiles"])
    if "people" in d:
        SIM.want("person", int(d["people"]))


def ask(path, default_map):
    """Show the window. Returns the chosen map name, or None when the window was closed without starting."""
    from simulator.ui.panel import ACC, BG, CARD, DIM, FIELD, TXT, Panel, Tip
    saved = load(path)
    root = tk.Tk()
    root.title("Motion Watch Simulator - start")
    Panel._style(types.SimpleNamespace(win=root))
    root.configure(bg=BG)
    result = {"map": None}

    head = ttk.Frame(root, style="Card.TFrame", padding=(14, 10)); head.pack(fill="x")
    ttk.Label(head, text="Motion Watch Simulator", style="Head.TLabel").pack(side="left")
    ttk.Label(head, text="   choose what the world contains - you can change all of it later (tab 🗺 World)",
              style="Card.TLabel", foreground=DIM).pack(side="left")
    body = ttk.Frame(root, padding=10); body.pack(fill="both", expand=True)

    # ---- map ----
    mf = ttk.LabelFrame(body, text="Map", padding=8); mf.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    names = ["region"] + [n for n in maps.MAPS if n != "region"]
    map_var = tk.StringVar(value=saved.get("map", default_map) if saved.get("map", default_map) in names else "region")
    for n in names:
        ttk.Radiobutton(mf, text=maps.MAPS[n].label, value=n, variable=map_var, command=lambda: redraw()).pack(anchor="w")

    # ---- places (Region) ----
    pf = ttk.LabelFrame(body, text="Places on the Region map - they all touch each other", padding=8)
    pf.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
    chosen = set(saved.get("tiles") or ORDER)
    tvars = {}
    grid = ttk.Frame(pf); grid.pack(anchor="w")
    for i, t in enumerate(ORDER):
        v = tk.BooleanVar(value=t in chosen or t == "camp"); tvars[t] = v
        cb = ttk.Checkbutton(grid, text=TILES[t][0], variable=v, command=lambda: redraw())
        cb.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 14), pady=1)
        Tip(cb, TILES[t][3])
        if t == "camp":
            cb.state(["disabled"])
    rb = ttk.Frame(pf); rb.pack(anchor="w", pady=4)
    ttk.Button(rb, text="All", command=lambda: (_set_all(True), redraw())).pack(side="left")
    ttk.Button(rb, text="Only the camp", command=lambda: (_set_all(False), redraw())).pack(side="left", padx=4)
    prev = tk.Canvas(pf, width=330, height=250, bg=FIELD, highlightthickness=0); prev.pack(pady=(4, 0))

    def _set_all(on):
        for t, v in tvars.items():
            v.set(on or t == "camp")

    colours = {"camp": "#d9822b", "lake": "#3d6fa3", "city": "#8a8f99", "suburbs": "#b7a27a", "village": "#c9b48a",
               "forest": "#2f5d3a", "industrial": "#7d7d85", "airfield": "#5b8f62", "farmland": "#b9a24a", "park": "#5aa36a",
               "parking": "#55565c", "hill": "#8b7d6b"}

    def redraw():
        prev.delete("all")
        if map_var.get() != "region":
            prev.create_text(165, 125, text="(places are only for the Region map)", fill=DIM)
            return
        cells = layout([t for t, v in tvars.items() if v.get()])
        allc = [c for cs in cells.values() for c in cs]
        xs = [c[0] for c in allc]; ys = [c[1] for c in allc]
        n = max(max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
        s = min(60, int(230 / n))
        ox = 165 - (min(xs) + max(xs) + 1) * s / 2; oy = 125 + (min(ys) + max(ys) + 1) * s / 2
        for name, cs in cells.items():
            x0 = min(c[0] for c in cs); x1 = max(c[0] for c in cs) + 1
            y0 = min(c[1] for c in cs); y1 = max(c[1] for c in cs) + 1
            prev.create_rectangle(ox + x0 * s, oy - y1 * s, ox + x1 * s, oy - y0 * s, fill=colours.get(name, "#777"), outline="#16181d", width=2)
            prev.create_text(ox + (x0 + x1) * s / 2, oy - (y0 + y1) * s / 2, text=TILES[name][0].split(" ")[0], fill="#fff",
                             font=("Segoe UI", 8 if s < 50 else 9))
        prev.create_text(165, 244, text="each square = 160 m", fill=DIM, font=("Segoe UI", 8))

    # ---- what is drawn ----
    df = ttk.LabelFrame(body, text="What is drawn", padding=8); df.grid(row=0, column=2, sticky="nsew")
    dvars = {}
    for k, lab, tip in (("draw_trees", "Trees and bushes", "Off = no trees anywhere (faster, open view)."),
                        ("draw_buildings", "Buildings", "Houses, skyscrapers, warehouses, caravans, sheds."),
                        ("draw_small", "Small things", "Parked cars, tents, tables, lamp posts, boats."),
                        ("draw_backdrop", "Mountain behind the world", "The big snow-capped mountain on the horizon."),
                        ("shadows", "Shadows", "Shadows in the sun."),
                        ("bg_traffic", "Background traffic (cars, planes)", "Cars keep driving on the roads, now and then a plane overhead.")):
        v = tk.BooleanVar(value=bool(saved.get(k, SIM[k]))); dvars[k] = v
        cb = ttk.Checkbutton(df, text=lab, variable=v); cb.pack(anchor="w"); Tip(cb, tip)
    ttk.Label(df, text="Quality").pack(anchor="w", pady=(10, 0))
    q_var = tk.IntVar(value=int(saved.get("quality", SIM["quality"])))
    qf = ttk.Frame(df); qf.pack(anchor="w")
    for q, lab in ((1, "Low"), (2, "Medium"), (3, "High"), (4, "Ultra")):
        ttk.Radiobutton(qf, text=lab, value=q, variable=q_var).pack(side="left")
    ttk.Label(df, text="Light").pack(anchor="w", pady=(10, 0))
    t_var = tk.StringVar(value=saved.get("time_mode", "manual"))
    ttk.Radiobutton(df, text="Daylight (13:00)", value="manual", variable=t_var).pack(anchor="w")
    ttk.Radiobutton(df, text="Real clock (dark at night)", value="clock", variable=t_var).pack(anchor="w")
    pr = ttk.Frame(df); pr.pack(anchor="w", pady=(10, 0))
    ttk.Label(pr, text="People walking through:").pack(side="left")
    p_var = tk.IntVar(value=int(saved.get("people", SIM.want("person"))))
    ttk.Spinbox(pr, from_=0, to=15, width=4, textvariable=p_var).pack(side="left", padx=4)
    show_var = tk.BooleanVar(value=bool(saved.get("start_window", True)))

    foot = ttk.Frame(root, padding=(10, 0, 10, 10)); foot.pack(fill="x")
    ttk.Checkbutton(foot, text="Show this window at every start", variable=show_var).pack(side="left")

    def start():
        d = {"map": map_var.get(), "tiles": [t for t, v in tvars.items() if v.get()], "quality": q_var.get(),
             "time_mode": t_var.get(), "hour": 13.0, "people": p_var.get(), "start_window": show_var.get()}
        d.update({k: v.get() for k, v in dvars.items()})
        save(path, d); apply(d)
        result["map"] = d["map"]
        root.destroy()
    ttk.Button(foot, text="Cancel", command=root.destroy).pack(side="right")
    ttk.Button(foot, text="▶  Start", style="Accent.TButton", command=start).pack(side="right", padx=6)
    root.bind("<Return>", lambda e: start())
    redraw()
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    root.geometry(f"+{max(0, (root.winfo_screenwidth() - w) // 2)}+{max(0, (root.winfo_screenheight() - h) // 3)}")
    root.mainloop()
    return result["map"]
