"""What the start window remembers (data/start_choices.json) - without tkinter, so the simulator also starts on a
Raspberry Pi without python3-tk (--no-panel). The window itself is simulator/ui/start.py."""
import json
import os

from simulator.config import SIM

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
