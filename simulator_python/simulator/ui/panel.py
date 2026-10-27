"""The simulator's window: map views with tools on the left, settings / live view / tests on the right."""
import math
import os
import random
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox, simpledialog, ttk

import cv2
from PIL import Image, ImageTk

from simulator import bridge
from simulator.scene import maps
from simulator.scene import world as W
from simulator.config import SIM
from simulator.graphics.render import thermal_colour
from simulator.checks.scenarios import SCENARIOS
from simulator.graphics.views import TopView, View3D, nearest

VISITORS = [("person", "🚶 Person"), ("dog", "🐕 Dog"), ("cat", "🐈 Cat"), ("bear", "🐻 Bear"), ("horse", "🦌 Deer"),
            ("sheep", "🐑 Sheep"), ("bird", "🐦 Bird"), ("car", "🚗 Car"), ("truck", "🚚 Truck"), ("bicycle", "🚲 Cyclist"),
            ("motorcycle", "🏍 Moto")]
EDIT_TOOLS = [("move", "✋ Move"), ("delete", "🗑 Delete"), ("camera", "📷 Camera"), ("tree", "🌳 Tree"), ("bush", "🌿 Bush"),
              ("prop", "🏠 Prop")]
SLIDER_MAX = {"plane": 3, "person": 15, "dog": 6, "cat": 6, "bear": 3, "horse": 4, "sheep": 8, "bird": 6, "car": 6, "truck": 3,
              "bicycle": 4, "motorcycle": 3}
GOOD, BAD, MID, DIM = "#5fd38d", "#ff6b6b", "#ffb347", "#8b93a1"
BG, CARD, FIELD, TXT, ACC, LINE = "#16181d", "#1f2229", "#121419", "#e7e9ee", "#ff8c42", "#2c313b"
FONT = ("Segoe UI", 9)
MONO = ("Cascadia Mono", 9)


TIPS = {
    "bg_traffic": "Cars keep driving on the roads and now and then a plane flies over - background life for the camera.",
    "draw_trees": "Off = no trees or bushes anywhere.", "draw_buildings": "Houses, skyscrapers, warehouses, caravans, sheds.",
    "draw_small": "Parked cars, tents, tables, lamp posts, boats.", "draw_backdrop": "The big mountain on the horizon.",
    "visit_wait": "How long somebody you sent with a click stays at that spot before walking away.",
    "visit_stay": "Ticked: people / animals you send stay at the spot until you remove them (right-click in the top view).",
    "speed_mult": "Everybody walks / drives this much faster or slower.",
    "spawn_gap": "Automatic traffic: at least this many seconds between two newcomers of the same kind.",
    "auto_spawn": "On: the sliders above are kept - somebody new comes when somebody leaves. Off: only what you send by hand.",
    "person_behavior": "How automatic people move. 'mixed' picks a random behaviour for every person.",
    "paused": "Freezes everything that moves. The camera keeps sending (still) pictures to Motion Watch.",
    "time_scale": "Run the world slower or faster than real time.",
    "hour": "Time of day for the light (moving it switches to slider mode). Night = dark picture, IR / thermal matter.",
    "moon": "How bright the night is.", "clouds": "Clouds: softer shadows, darker day, warmer night sky in the thermal picture.",
    "rain": "Rain streaks in the picture - the program should switch to its rain mode.",
    "fog": "Fog: far things fade away.", "wind": "Wind: bushes and trees sway (the program should not alarm); Motion Watch also gets the wind speed.",
    "ambient_c": "Air temperature - the thermal camera sees everything relative to it.",
    "shadows": "Shadows of people, trees and buildings in the sun (the program has a shadow filter).",
    "cam_fps": "Pictures per second the camera delivers.", "cam_hfov": "Field of view of the camera (Pi Camera Module 3 = 66°).",
    "cam_noise": "Grain of the sensor (more at night through the gain).", "auto_exposure": "The camera makes dark scenes brighter by itself.",
    "mount_height": "How high the camera head stands. Changing it rebuilds the background picture.",
    "mount_yaw": "Which way the whole mount faces (the pan servo turns on top of that).",
    "mount_pitch": "How far the head looks down when the tilt servo is in the middle.",
    "cam_connected": "Untick = the camera cable is pulled. The program should notice and reconnect when you tick it again.",
    "cam_frozen": "The camera sends the same picture again and again (driver hang).",
    "lens_cover": "Somebody holds a hand over the lens - the sabotage check should report 'covered'.",
    "lens_blur": "Dew or dirt on the lens - the picture gets blurred and flat (lens check).",
    "shake": "The mount wobbles (wind on a tripod).",
    "pan_travel": "How far the pan servo really turns between 500 and 2500 µs (180° servo, 270°, or a 360° one).\n"
                  "If Motion Watch says its servo turns further (up to ±180°), the simulated one follows it.",
    "tilt_travel": "Same for the tilt servo.", "tilt_stop": "The tilt bracket hits the base here, whatever the servo is told.",
    "servo_speed": "How fast the servos turn. Real servos with the camera on them: about 60 - 120 °/s (SG90 unloaded ~600 °/s).",
    "servo_jitter": "Random twitching of cheap servos.", "pan_reversed": "Servo built in the other way round: the program must use 'invert pan'.",
    "tilt_reversed": "Same for tilt (program setting 'invert tilt').", "servo_power": "Untick = servo power supply off: the head stays where it is.",
    "pan_stuck": "The pan servo is blocked.", "tilt_stuck": "The tilt servo is blocked.",
    "thermal_present": "Untick = thermal camera unplugged (the program should report it).",
    "thermal_hfov": "Field of view of the thermal camera (Thermal-90 = 90°).", "thermal_noise": "Noise of the thermal sensor in °C.",
    "hot_stone": "A sun-warmed stone: hot but never moves - should NOT cause a thermal alarm.",
    "campfire": "A camp fire: very hot and flickering.",
    "pir_range": "How far the PIR sees. It sends an event to Motion Watch when somebody comes near the box.",
}


class Tip:
    """Little yellow-ish help text when the mouse rests on a control."""
    def __init__(self, w, text):
        self.w, self.text, self.tw, self.job = w, text, None, None
        w.bind("<Enter>", self._enter, add="+"); w.bind("<Leave>", self._leave, add="+"); w.bind("<ButtonPress>", self._leave, add="+")

    def _enter(self, e):
        self.job = self.w.after(450, self._show)

    def _show(self):
        if self.tw or not self.text:
            return
        x, y = self.w.winfo_rootx() + 12, self.w.winfo_rooty() + self.w.winfo_height() + 4
        self.tw = tk.Toplevel(self.w); self.tw.wm_overrideredirect(True); self.tw.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tw, text=self.text, justify="left", wraplength=360, bg="#2b2f38", fg="#f1f1f1", padx=8, pady=5,
                 font=("Segoe UI", 9), relief="solid", borderwidth=1).pack()

    def _leave(self, e=None):
        if self.job:
            self.w.after_cancel(self.job); self.job = None
        if self.tw:
            self.tw.destroy(); self.tw = None


GUIDE = """QUICK START

1  Connect Motion Watch: it runs as its own program (on the Pi or a PC). Switch "📡 Send to Motion Watch"
   on (top right), then in Motion Watch: tab «Simulator» → «Simulatoren im Netz» → «Verwenden».
   The left side shows the map: the yellow wedge is what the camera sees right now, orange the
   thermal camera. Motion Watch gets exactly that picture.

2  Send somebody: pick 🚶 Person / 🐕 Dog / 🐈 Cat … below the map, then click a spot on the map.
   It walks in from outside the picture, stays a few seconds, then leaves again.

3  Keep traffic going: tab 👥 People - one slider per kind ("keep 3 people walking through").
   Turn a slider down and the extra ones walk away.

4  Change the world: tab 🗺 World - 7 maps (Valley = big one with skyscrapers),
   day / night, rain, fog, wind.  📷 Camera - servo travel (180° / 270° / 360°), faults.

5  MOVE THE CAMERA: press "📷 Move camera" (top right), then click on the map where it should stand -
   keep the button pressed and drag to turn it. Or: 📍 Place (top right) jumps to a ready-made spot,
   and box ③ under the map has arrow buttons (10 m steps, turn 15°, higher / lower).

6  Edit the map: tab "3D map editor" on the left. ✋ Move, 🗑 Delete, 📷 Camera (click = put the
   camera there, drag = which way it faces), 🌳 🌿 🏠 place things. 💾 Save as own map.

7  Check Motion Watch: tab ▶ Live shows what it reports next to what is really there
   (scoreboard). Tab ✅ Tests runs automatic checks.

Mouse: wheel = zoom.  Top view: right-drag = move the map, right-click a thing = menu.
3D view: right-drag = turn, middle-drag (or shift + right-drag) = move.
Rest the mouse on any button or slider for a short explanation.  Quality slider: top right."""


def _photo(bgr):
    return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))


class Panel:
    def __init__(self, root, eng, runner, proto, opts, own_root=False):
        self.eng, self.runner, self.proto, self.opts = eng, runner, proto, opts
        self.win = root if own_root else tk.Toplevel(root)
        from simulator import NAME
        from simulator.ui.icon import set_icon
        self.win.title(NAME)
        set_icon(self.win)
        try:
            self.win.geometry("1360x880+20+20")
        except tk.TclError:
            pass
        self.tool = tk.StringVar(value="person")
        self.count = tk.IntVar(value=1)
        self.prop_kind = tk.StringVar(value="tent")
        self.top = TopView(560, 500); self.v3d = View3D(560, 500)
        self.sel = None; self.hover = None; self.drag = None; self._imgs = {}
        self._runs_seen = -1
        self._style()
        self._build()
        self.win.after(300, self._tick)

    # =================================================================================================================
    # layout
    # =================================================================================================================
    def _style(self):
        """Dark theme in the colours of the app icon (orange accent)."""
        w = self.win
        w.configure(bg=BG)
        st = ttk.Style(w)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=BG, foreground=TXT, fieldbackground=FIELD, bordercolor=LINE, darkcolor=BG, lightcolor=BG,
                     troughcolor=FIELD, selectbackground=ACC, selectforeground="#111", insertcolor=TXT, font=FONT)
        st.configure("TFrame", background=BG)
        st.configure("Card.TFrame", background=CARD)
        st.configure("TLabel", background=BG, foreground=TXT)
        st.configure("Card.TLabel", background=CARD)
        st.configure("Head.TLabel", background=CARD, foreground=TXT, font=("Segoe UI Semibold", 13))
        st.configure("Pill.TLabel", background="#2a2f39", foreground=TXT, padding=(8, 2), font=("Segoe UI", 9))
        st.configure("TLabelframe", background=BG, bordercolor=LINE, relief="solid", borderwidth=1)
        st.configure("TLabelframe.Label", background=BG, foreground=ACC, font=("Segoe UI Semibold", 9))
        st.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 4, 0, 0))
        st.configure("TNotebook.Tab", background=CARD, foreground=DIM, padding=(7, 4), borderwidth=0, font=("Segoe UI Semibold", 9))
        st.map("TNotebook.Tab", background=[("selected", "#2a2f39"), ("active", "#262a33")],
               foreground=[("selected", ACC), ("active", TXT)])
        st.configure("TButton", background="#2a2f39", foreground=TXT, borderwidth=0, focusthickness=0, padding=(9, 4))
        st.map("TButton", background=[("pressed", ACC), ("active", "#353b47")], foreground=[("pressed", "#111")])
        st.configure("Accent.TButton", background=ACC, foreground="#111")
        st.map("Accent.TButton", background=[("active", "#ffa266")])
        st.configure("Toolbutton", background="#2a2f39", foreground=TXT, padding=(8, 4), borderwidth=0, font=("Segoe UI", 9))
        st.map("Toolbutton", background=[("selected", ACC), ("active", "#353b47")], foreground=[("selected", "#111")])
        st.configure("TCheckbutton", background=BG, foreground=TXT, indicatorbackground=FIELD, indicatorforeground=ACC)
        st.map("TCheckbutton", background=[("active", BG)], indicatorbackground=[("selected", ACC)], indicatorforeground=[("selected", "#111")])
        st.configure("TRadiobutton", background=BG, foreground=TXT, indicatorbackground=FIELD)
        st.map("TRadiobutton", background=[("active", BG)], indicatorbackground=[("selected", ACC)])
        st.configure("Horizontal.TScale", background=ACC, troughcolor="#2a2f39", bordercolor=BG, lightcolor=ACC, darkcolor=ACC)
        st.configure("TCombobox", fieldbackground=FIELD, background="#2a2f39", foreground=TXT, arrowcolor=TXT, bordercolor=LINE)
        st.map("TCombobox", fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TXT)], selectbackground=[("readonly", FIELD)])
        st.configure("TSpinbox", fieldbackground=FIELD, background="#2a2f39", foreground=TXT, arrowcolor=TXT, bordercolor=LINE)
        st.configure("Treeview", background=FIELD, fieldbackground=FIELD, foreground=TXT, bordercolor=LINE, rowheight=22)
        st.configure("Treeview.Heading", background=CARD, foreground=ACC, borderwidth=0, font=("Segoe UI Semibold", 9))
        st.map("Treeview", background=[("selected", "#3a2a1e")], foreground=[("selected", ACC)])
        w.option_add("*TCombobox*Listbox.background", FIELD)
        w.option_add("*TCombobox*Listbox.foreground", TXT)
        w.option_add("*TCombobox*Listbox.selectBackground", ACC)
        w.option_add("*Menu.background", CARD); w.option_add("*Menu.foreground", TXT)
        w.option_add("*Menu.activeBackground", ACC); w.option_add("*Menu.activeForeground", "#111")

    def _text(self, parent, **kw):
        t = tk.Text(parent, font=MONO, relief="flat", bg=FIELD, fg=TXT, insertbackground=TXT, padx=8, pady=6,
                    highlightthickness=1, highlightbackground=LINE, highlightcolor=LINE, **kw)
        return t

    def _header(self):
        h = ttk.Frame(self.win, style="Card.TFrame", padding=(12, 8)); h.pack(side="top", fill="x")
        logo = tk.Canvas(h, width=28, height=28, bg=CARD, highlightthickness=0)
        logo.create_oval(2, 2, 26, 26, fill=ACC, outline="")
        logo.create_rectangle(9, 10, 20, 18, fill="#16181d", outline=""); logo.create_oval(17, 11, 23, 17, fill="#16181d", outline="")
        logo.pack(side="left")
        ttk.Label(h, text="Motion Watch Simulator", style="Head.TLabel").pack(side="left", padx=(8, 16))
        self.pills = {}
        for k in ("net", "prog", "armed", "map", "time", "persons", "cam", "servo"):
            lb = ttk.Label(h, style="Pill.TLabel"); lb.pack(side="left", padx=3)
            self.pills[k] = lb
        hb = ttk.Button(h, text="❓ Help", command=self._guide, style="Accent.TButton"); hb.pack(side="right", padx=(8, 0))
        self.stream_var = tk.BooleanVar(value=bool(SIM["stream"]))
        sb = ttk.Checkbutton(h, text="📡 Send to Motion Watch", variable=self.stream_var, style="Toolbutton",
                             command=lambda: SIM.__setitem__("stream", bool(self.stream_var.get())))
        sb.pack(side="right", padx=(8, 0))
        Tip(sb, "On: the simulator announces itself in the local network every 2 s. Motion Watch then lists it under "
                "tab «Simulator» → «Simulatoren im Netz» → «Verwenden» → «Simulation einschalten».\n"
                "Off (at start): the simulator stays silent. Start option --stream switches it on at once.")
        mvb = ttk.Button(h, text="📷 Move camera", style="Accent.TButton", command=self._camera_mode); mvb.pack(side="right", padx=(8, 0))
        Tip(mvb, "Move the camera: click this, then click on the map where the camera should stand. Keep the mouse button "
                 "pressed and drag to choose which way it looks. Or use the arrows in box ③ under the map.")
        pf = ttk.Frame(h, style="Card.TFrame"); pf.pack(side="right", padx=(6, 14))
        ttk.Label(pf, text="📍 Place", style="Card.TLabel").pack(side="left", padx=(0, 4))
        self.poi_var = tk.StringVar()
        self.poi_cb = ttk.Combobox(pf, textvariable=self.poi_var, width=26, state="readonly")
        self.poi_cb.pack(side="left")
        self.poi_cb.bind("<<ComboboxSelected>>", lambda e: self._goto_poi(self.poi_cb.current()))
        Tip(self.poi_cb, "Jump the camera to a place of interest on this map (campsite, city, rooftop, village, airfield ...). "
                         "The picture is rebuilt for the new place in a few seconds. All places: tab World.")
        self._poi_map = None
        Tip(hb, "Quick start: what you can do with the simulator.")
        self.q_lbl = ttk.Label(h, style="Card.TLabel", width=6); self.q_lbl.pack(side="right")
        qs = ttk.Scale(h, from_=1, to=4, length=110, command=self._quality); qs.pack(side="right", padx=4)
        ttk.Label(h, text="Quality", style="Card.TLabel").pack(side="right")
        qs.set(SIM["quality"]); self._quality(SIM["quality"])
        Tip(qs, "Sharpness of the camera's background picture and of the map views. Higher = sharper but slower "
                "(the background is rebuilt for a few seconds). The camera resolution itself is under 📷 Camera & servos.")

    def _quality(self, v):
        q = int(round(float(v)))
        self.q_lbl.config(text=("Low", "Medium", "High", "Ultra")[q - 1])
        if q != SIM["quality"]:
            SIM["quality"] = q
            self.hint.config(text=f"Quality {q}: building the sharper background picture (a few seconds) …")

    def _guide(self):
        g = tk.Toplevel(self.win); g.title("MW Sim · Welt - quick start"); g.configure(bg=CARD)
        g.transient(self.win)
        tk.Label(g, text=GUIDE, justify="left", bg=CARD, fg=TXT, font=("Segoe UI", 10), padx=22, pady=18).pack()
        ttk.Button(g, text="Got it", style="Accent.TButton", command=g.destroy).pack(pady=(0, 16))
        g.update_idletasks()
        x = self.win.winfo_rootx() + (self.win.winfo_width() - g.winfo_width()) // 2
        y = self.win.winfo_rooty() + (self.win.winfo_height() - g.winfo_height()) // 3
        g.geometry(f"+{max(0, x)}+{max(0, y)}")
        g.grab_set()

    def _camera_mode(self):
        self.tool.set("camera")
        self.hint.config(text="📷 CLICK ON THE MAP where the camera should stand. Keep the button pressed and drag to choose "
                              "which way it looks. (The 3D map editor tab works the same way.)")

    def _nudge(self, right, forward):
        a = math.radians(SIM["mount_yaw"])
        SIM.update(cam_x=round(SIM["cam_x"] + math.cos(a) * right + math.sin(a) * forward, 2),
                   cam_y=round(SIM["cam_y"] - math.sin(a) * right + math.cos(a) * forward, 2))
        self.top.cx, self.top.cy = SIM["cam_x"], SIM["cam_y"] + 14
        self.hint.config(text="Camera moved - the picture is rebuilt for the new place (a few seconds).")

    def _turn(self, deg):
        SIM["mount_yaw"] = round((SIM["mount_yaw"] + deg + 180) % 360 - 180, 1)

    def _raise(self, dh):
        SIM["mount_height"] = round(max(0.3, min(300.0, SIM["mount_height"] + dh)), 2)
        self.hint.config(text=f"Camera height {SIM['mount_height']:.1f} m - the picture is rebuilt (a few seconds).")

    def _goto_poi(self, i):
        ps = maps.pois(self.eng.world.map)
        if not 0 <= i < len(ps):
            return
        p = ps[i]
        self.sel = None
        self.eng.goto_poi(p)
        self.top.cx, self.top.cy = p["x"], p["y"] + 14
        self.v3d.tx, self.v3d.ty = p["x"], p["y"] + 12
        self.hint.config(text=f"📍 {p['name']}: {p['desc']}  - building the picture for this place ...")
        self._sync_pois(force=True)

    def _sync_pois(self, force=False):
        """Fill the 📍 selector + the Places list for the current map and show which place is active."""
        m = self.eng.world.map
        ps = maps.pois(m)
        if force or self._poi_map != (m.name, len(ps)):
            self._poi_map = (m.name, len(ps))
            self.poi_cb.config(values=[p["name"] for p in ps])
            if hasattr(self, "poi_list"):
                self.poi_list.delete(0, "end")
                for p in ps:
                    self.poi_list.insert("end", f"{p['name']}  -  {p['desc']}")
        cur = self.eng.current_poi()
        txt = cur["name"] if cur else "(your own spot)"
        if self.poi_var.get() != txt:
            self.poi_var.set(txt)
        if hasattr(self, "poi_list") and cur in ps:
            idx = ps.index(cur)
            sel = self.poi_list.curselection()
            if not sel or sel[0] != idx:
                self.poi_list.selection_clear(0, "end"); self.poi_list.selection_set(idx); self.poi_list.see(idx)

    def _pill(self, k, text, col=None):
        lb = self.pills[k]
        lb.config(text=text, foreground=col or TXT)

    def _build(self):
        w = self.win
        self._header()
        body = ttk.Panedwindow(w, orient="horizontal"); body.pack(fill="both", expand=True, padx=8, pady=8)
        self._body = body
        self.win.after(400, lambda: body.sashpos(0, max(520, int(self.win.winfo_width() * 0.44))))
        left = ttk.Frame(body); right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=3); body.add(right, weight=2)

        # ---- map views ----
        bottom = ttk.Frame(left); bottom.pack(side="bottom", fill="x")
        self.vnb = ttk.Notebook(left); self.vnb.pack(side="top", fill="both", expand=True)
        self.c2d = tk.Canvas(self.vnb, width=560, height=500, bg=FIELD, highlightthickness=0, cursor="crosshair")
        self.c3d = tk.Canvas(self.vnb, width=560, height=500, bg=FIELD, highlightthickness=0, cursor="crosshair")
        self.vnb.add(self.c2d, text="  Map (from above)  "); self.vnb.add(self.c3d, text="  3D map editor  ")
        for c, v in ((self.c2d, "2d"), (self.c3d, "3d")):
            c.bind("<ButtonPress-1>", lambda e, v=v: self._press(e, v))
            c.bind("<B1-Motion>", lambda e, v=v: self._motion(e, v))
            c.bind("<ButtonRelease-1>", lambda e, v=v: self._release(e, v))
            c.bind("<ButtonPress-3>", lambda e, v=v: self._rpress(e, v))
            c.bind("<B3-Motion>", lambda e, v=v: self._rmotion(e, v))
            c.bind("<ButtonRelease-3>", lambda e, v=v: self._rrelease(e, v))
            c.bind("<ButtonPress-2>", lambda e, v=v: self._rpress(e, v, pan=True))
            c.bind("<B2-Motion>", lambda e, v=v: self._rmotion(e, v))
            c.bind("<MouseWheel>", lambda e, v=v: self._wheel(e, v))
            c.bind("<Motion>", lambda e, v=v: self._hover(e, v))
            c.bind("<Configure>", lambda e, v=v: self._resize(e, v))

        # ---- tools ----
        tf = ttk.LabelFrame(bottom, text="①  Send somebody: pick who, then click a spot on the map")
        tf.pack(fill="x", pady=(6, 0))
        row = None
        for i, (k, lab) in enumerate(VISITORS):
            if i % 6 == 0:
                row = ttk.Frame(tf); row.pack(fill="x")
            rb = ttk.Radiobutton(row, text=lab, value=k, variable=self.tool, style="Toolbutton"); rb.pack(side="left", padx=1, pady=1)
            Tip(rb, f"Then click on the map: {lab.split(' ', 1)[1].lower()} comes in from outside the picture, goes to that spot, "
                    f"stays a few seconds and walks away again. 'How many' sends a group.")
        opt = ttk.Frame(tf); opt.pack(fill="x", pady=2)
        ttk.Label(opt, text="How many:").pack(side="left")
        ttk.Spinbox(opt, from_=1, to=12, width=3, textvariable=self.count).pack(side="left", padx=(2, 10))
        ttk.Label(opt, text="Stays (s):").pack(side="left")
        self._spin(opt, "visit_wait", 0, 300, 4)
        self._check(opt, "stays until removed", "visit_stay").pack(side="left", padx=8)
        ef = ttk.LabelFrame(bottom, text="②  Change the map: pick a tool, then click / drag on the map (works in both views)")
        ef.pack(fill="x", pady=(6, 0))
        row = ttk.Frame(ef); row.pack(fill="x")
        edit_tips = {"move": "Drag anything on the map: people, animals, trees, buildings - or the camera itself.",
                     "delete": "Click a person, animal, tree or building to remove it.",
                     "camera": "Click = put the camera head there. Click and drag = also turn it the way you drag.",
                     "tree": "Click = plant a tree.", "bush": "Click = plant a bush.",
                     "prop": "Click = place the thing chosen in the list on the right (tent, house, skyscraper …)."}
        for k, lab in EDIT_TOOLS:
            rb = ttk.Radiobutton(row, text=lab, value=k, variable=self.tool, style="Toolbutton"); rb.pack(side="left", padx=1, pady=1)
            Tip(rb, edit_tips[k])
        ttk.Combobox(row, textvariable=self.prop_kind, values=sorted(maps.PROP_TYPES), width=9, state="readonly").pack(side="left", padx=4)
        row2 = ttk.Frame(ef); row2.pack(fill="x", pady=2)
        ttk.Button(row2, text="💾 Save as own map…", command=self._save_map).pack(side="left")
        ttk.Button(row2, text="↺ Reload map", command=lambda: self._set_map(self.eng.world.map.name)).pack(side="left", padx=4)
        ttk.Button(row2, text="Clear everything that moves", command=lambda: self.eng.world.clear()).pack(side="left", padx=4)
        cf = ttk.LabelFrame(bottom, text="③  Move the camera: 📷 Move camera + click the map  -  or use these buttons")
        cf.pack(fill="x", pady=(6, 0))
        r3 = ttk.Frame(cf); r3.pack(fill="x"); r4 = ttk.Frame(cf); r4.pack(fill="x")
        for n_, (lab, cmd, tip) in enumerate((("📷 Click on map", self._camera_mode, "Then click where the camera should stand (drag = direction)."),
                              ("◀ 10 m", lambda: self._nudge(-10, 0), "Camera 10 m to the left (as seen from the camera)."),
                              ("▶ 10 m", lambda: self._nudge(10, 0), "Camera 10 m to the right."),
                              ("▲ 10 m", lambda: self._nudge(0, 10), "Camera 10 m forward (the way it looks)."),
                              ("▼ 10 m", lambda: self._nudge(0, -10), "Camera 10 m back."),
                              ("⟲ 15°", lambda: self._turn(-15), "Turn the whole camera 15° to the left."),
                              ("⟳ 15°", lambda: self._turn(15), "Turn the whole camera 15° to the right."),
                              ("⬆ higher", lambda: self._raise(1.0), "Camera 1 m higher (on a pole / roof)."),
                              ("⬇ lower", lambda: self._raise(-1.0), "Camera 1 m lower."))):
            b = ttk.Button(r3 if n_ < 5 else r4, text=lab, command=cmd); b.pack(side="left", padx=1, pady=1); Tip(b, tip)
        self.campos = ttk.Label(cf, foreground=DIM); self.campos.pack(anchor="w")
        self.hint = ttk.Label(bottom, text="", foreground=ACC, wraplength=700, justify="left", font=("Segoe UI", 9))
        self.hint.pack(fill="x", pady=(4, 0))

        # ---- right side ----
        nb = ttk.Notebook(right); nb.pack(fill="both", expand=True)
        self.nb = nb
        self._tab_live(nb); self._tab_population(nb); self._tab_env(nb); self._tab_camera(nb)
        self._tab_thermal_ai(nb); self._tab_gpio(nb); self._tab_tests(nb); self._tab_log(nb); self._tab_help(nb)
        try:
            import os
            flag = os.path.join(os.path.dirname(maps.CUSTOM_DIR["d"] or "."), "data", ".guide_seen")
            os.makedirs(os.path.dirname(flag), exist_ok=True)
            if not os.path.exists(flag):
                self.win.after(1200, self._guide)
                open(flag, "w").close()
        except OSError:
            pass

    # ---- small widget helpers bound to SIM ----
    def _scale(self, parent, label, key, lo, hi, res=0.01, fmt="{:.2f}", cb=None, length=260):
        f = ttk.Frame(parent); f.pack(fill="x", pady=1)
        ttk.Label(f, text=label, width=26 if length > 150 else 22).pack(side="left")
        val = ttk.Label(f, width=8)
        var = tk.DoubleVar(value=float(SIM[key]))

        def changed(*_):
            v = round(var.get() / res) * res
            SIM[key] = int(v) if isinstance(SIM[key], int) and not isinstance(SIM[key], bool) else v
            val.config(text=fmt.format(v))
            if cb:
                cb(v)
        s = ttk.Scale(f, from_=lo, to=hi, variable=var, command=changed, length=length)
        s.pack(side="left"); val.pack(side="left", padx=4)
        if key in TIPS:
            Tip(f, TIPS[key])
        val.config(text=fmt.format(var.get()))
        f._var = var; f._key = key
        self._bound.append((var, key))
        return f

    def _check(self, parent, label, key, cb=None):
        var = tk.BooleanVar(value=bool(SIM[key]))

        def changed():
            SIM[key] = bool(var.get())
            if cb:
                cb(var.get())
        self._bound.append((var, key))
        cb_ = ttk.Checkbutton(parent, text=label, variable=var, command=changed)
        if key in TIPS:
            Tip(cb_, TIPS[key])
        return cb_

    def _spin(self, parent, key, lo, hi, width=5):
        var = tk.DoubleVar(value=float(SIM[key]))

        def changed(*_):
            try:
                SIM[key] = float(var.get())
            except (tk.TclError, ValueError):
                pass
        var.trace_add("write", changed)
        ttk.Spinbox(parent, from_=lo, to=hi, width=width, textvariable=var).pack(side="left")

    def _combo(self, parent, label, key, values, width=12, conv=str):
        f = ttk.Frame(parent); f.pack(fill="x", pady=1)
        ttk.Label(f, text=label, width=26).pack(side="left")
        var = tk.StringVar(value=str(SIM[key]))
        cb = ttk.Combobox(f, textvariable=var, values=[str(v) for v in values], width=width, state="readonly")
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: SIM.__setitem__(key, conv(var.get())))
        if key in TIPS:
            Tip(f, TIPS[key])
        return f

    _bound = []

    # =================================================================================================================
    # tabs
    # =================================================================================================================
    def _tab_live(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" ▶ Live ")
        ttk.Label(t, text='What the camera and the thermal camera deliver, what Motion Watch makes of it, and how that compares to what is really there.', foreground=DIM, wraplength=760, justify='left').pack(anchor='w', pady=(4, 6))
        top = ttk.Frame(t); top.pack(fill="x")
        self.cam_lbl = ttk.Label(top); self.cam_lbl.pack(side="left")
        rt = ttk.Frame(top); rt.pack(side="left", padx=6, anchor="n")
        self.th_lbl = ttk.Label(rt); self.th_lbl.pack()
        ttk.Label(rt, text="camera (left) / thermal (above) - what the\nsimulator sends to Motion Watch", foreground=DIM).pack()
        mid = ttk.Frame(t); mid.pack(fill="both", expand=True, pady=4)
        pf = ttk.LabelFrame(mid, text="Motion Watch (over the network)"); pf.pack(side="left", fill="both", expand=True)
        bf = ttk.Frame(pf); bf.pack(fill="x")
        ttk.Button(bf, text="Arm now", command=bridge.arm).pack(side="left")
        ttk.Button(bf, text="Disarm", command=bridge.disarm).pack(side="left", padx=2)
        ttk.Button(bf, text="Open web page", command=self._open_web).pack(side="left", padx=2)
        ttk.Button(bf, text="Centre camera", command=bridge.centre).pack(side="left", padx=2)
        self.prog_checks = ttk.Frame(pf); self.prog_checks.pack(fill="x", pady=2)
        self._pvars = {}
        for i, (k, lab) in enumerate((("detection_on", "Detection"), ("track_person", "Follow person"), ("patrol", "Patrol"),
                                      ("record", "Record"), ("ai_enabled", "AI"), ("thermal_on", "Thermal overlay"),
                                      ("thermal_alarm", "Thermal alarm"), ("tamper_on", "Sabotage check"), ("eco_on", "Power saving"))):
            v = tk.BooleanVar(value=False); self._pvars[k] = v
            ttk.Checkbutton(self.prog_checks, text=lab, variable=v, command=lambda k=k, v=v: bridge.set_cfg(k, bool(v.get()))).grid(
                row=i // 5, column=i % 5, sticky="w", padx=2)
        self.prog_txt = self._text(pf, height=16, width=58)
        self.prog_txt.pack(fill="both", expand=True)
        sf = ttk.LabelFrame(mid, text="Truth vs. program (scoreboard)"); sf.pack(side="left", fill="both", padx=(6, 0))
        self.score_frame = ttk.Frame(sf); self.score_frame.pack(fill="x")
        self.score_lbls = []
        ttk.Button(sf, text="Reset scoreboard", command=lambda: self.eng.scoreboard.reset()).pack(anchor="w", pady=4)
        self.timeline = tk.Canvas(sf, width=330, height=70, bg=FIELD, highlightthickness=1, highlightbackground=LINE)
        self.timeline.pack(pady=2)
        ttk.Label(sf, text="last 2 min: grey = persons really in view, orange = reported,\nblue band = tracking, red band = recording",
                  foreground=DIM).pack(anchor="w")

    def _tab_population(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" 👥 People ")
        ttk.Label(t, text='Sliders = how many of each kind keep walking through the picture. Or send single ones with a click on the map.', foreground=DIM, wraplength=760, justify='left').pack(anchor='w', pady=(4, 6))
        f = ttk.LabelFrame(t, text="Keep this many walking through (they come in from outside the picture and leave again)")
        f.pack(fill="x", pady=4)
        self._want_vars = {}
        for kind in W.KINDS:
            r = ttk.Frame(f); r.pack(fill="x")
            ttk.Label(r, text=W.KIND_LABEL[kind], width=16).pack(side="left")
            var = tk.IntVar(value=SIM.want(kind)); self._want_vars[kind] = var
            lab = ttk.Label(r, width=4, text=str(var.get()))
            ttk.Scale(r, from_=0, to=SLIDER_MAX[kind], length=330,
                      command=lambda v, k=kind, var=var, lab=lab: (var.set(int(round(float(v)))), SIM.want(k, var.get()), lab.config(text=str(var.get())))
                      ).pack(side="left")
            r.winfo_children()[-1].set(var.get())
            lab.pack(side="left")
            ttk.Button(r, text="one now", width=8, command=lambda k=kind: self.eng.world.spawn(k)).pack(side="left", padx=4)
            self._now_lbl = getattr(self, "_now_lbl", {})
            nl = ttk.Label(r, width=12, foreground=DIM); nl.pack(side="left"); self._now_lbl[kind] = nl
        g = ttk.LabelFrame(t, text="How they move"); g.pack(fill="x", pady=4)
        self._check(g, "Automatic traffic (keeps the numbers above)", "auto_spawn").pack(anchor="w")
        self._combo(g, "People behaviour", "person_behavior", W.PERSON_BEHAVIORS)
        ttk.Label(g, text="  mixed = all of them · walk = straight across · wander = here and there · stand = stops for a long time\n"
                          "  loiter = hangs around one spot · run · approach = walks up to the camera · sneak = crouched and slow",
                  foreground=DIM).pack(anchor="w")
        self._scale(g, "Speed factor", "speed_mult", 0.2, 3.0, 0.05, "{:.2f}x")
        self._scale(g, "Seconds between arrivals", "spawn_gap", 0.5, 30, 0.5, "{:.1f} s")
        h = ttk.LabelFrame(t, text="Simulation time"); h.pack(fill="x", pady=4)
        self._check(h, "Pause (everything freezes, the camera keeps sending pictures)", "paused").pack(anchor="w")
        self._scale(h, "Time speed", "time_scale", 0.1, 4.0, 0.1, "{:.1f}x")

    def _tab_env(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" 🗺 World ")
        ttk.Label(t, text="Pick the place, the time of day and the weather. 'Region' (7 km) is the huge one with the city, villages and the mountain; 📍 places jump the camera around.", foreground=DIM, wraplength=760, justify='left').pack(anchor='w', pady=(4, 6))
        mf = ttk.LabelFrame(t, text="Map"); mf.pack(fill="x", pady=4)
        r = ttk.Frame(mf); r.pack(fill="x")
        self.map_var = tk.StringVar()
        self.map_cb = ttk.Combobox(r, textvariable=self.map_var, width=34, state="readonly")
        self.map_cb.pack(side="left")
        self.map_cb.bind("<<ComboboxSelected>>", lambda e: self._set_map(self._map_names[self.map_cb.current()]))
        self.map_status = ttk.Label(r, foreground=MID); self.map_status.pack(side="left", padx=8)
        self.map_desc = ttk.Label(mf, foreground=DIM, wraplength=760, justify="left"); self.map_desc.pack(anchor="w")
        self._fill_maps()
        pf = ttk.LabelFrame(t, text="📍 Places on this map - pick one: the camera goes there (also in the top bar)")
        pf.pack(fill="x", pady=4)
        self.poi_list = tk.Listbox(pf, height=9, bg=FIELD, fg=TXT, selectbackground=ACC, selectforeground="#111", relief="flat",
                                   highlightthickness=1, highlightbackground=LINE, font=FONT, activestyle="none", exportselection=False)
        self.poi_list.pack(fill="x")
        go = lambda e=None: self._goto_poi(self.poi_list.curselection()[0]) if self.poi_list.curselection() else None
        self.poi_list.bind("<Double-Button-1>", go)
        r2 = ttk.Frame(pf); r2.pack(fill="x", pady=2)
        ttk.Button(r2, text="📍 Go there", style="Accent.TButton", command=go).pack(side="left")
        ttk.Label(r2, text="  or double-click a place. Orange pins on the map views show where they are.", foreground=DIM).pack(side="left")
        # ---- which places exist (Region map) + what is drawn ----
        from simulator.scene.region import ORDER, TILES
        both = ttk.Frame(t); both.pack(fill="x", pady=4)
        tf = ttk.LabelFrame(both, text="🧩 Places in the Region map (they always touch)"); tf.pack(side="left", fill="both", expand=True)
        chosen = set(SIM["tiles"] or ORDER)
        self._tile_vars = {}
        g = ttk.Frame(tf); g.pack(anchor="w")
        for i, name in enumerate(ORDER):
            v = tk.BooleanVar(value=name in chosen or name == "camp"); self._tile_vars[name] = v
            cb = ttk.Checkbutton(g, text=TILES[name][0], variable=v); cb.grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 10))
            Tip(cb, TILES[name][3])
            if name == "camp":
                cb.state(["disabled"])
        ab = ttk.Button(tf, text="🔁 Apply - rebuild the world", style="Accent.TButton", command=self._apply_tiles)
        ab.pack(anchor="w", pady=4)
        Tip(ab, "Builds the Region map again with the ticked places, all touching. Takes a few seconds.")
        dfr = ttk.LabelFrame(both, text="👁 What is drawn (at once)"); dfr.pack(side="left", fill="both", padx=(8, 0))
        for k, lab in (("draw_trees", "Trees and bushes"), ("draw_buildings", "Buildings"), ("draw_small", "Small things (cars, tents …)"),
                       ("draw_backdrop", "Mountain behind the world"), ("shadows", "Shadows"),
                       ("bg_traffic", "Background traffic (cars, planes)")):
            self._check(dfr, lab, k, cb=lambda _v: self.eng.scenery_changed()).pack(anchor="w")
        lf = ttk.LabelFrame(t, text="Time of day"); lf.pack(fill="x", pady=4)
        r = ttk.Frame(lf); r.pack(fill="x")
        self.tmode = tk.StringVar(value=SIM["time_mode"])
        for v, lab in (("clock", "real clock"), ("manual", "slider")):
            ttk.Radiobutton(r, text=lab, value=v, variable=self.tmode, command=lambda: SIM.__setitem__("time_mode", self.tmode.get())).pack(side="left")
        self._scale(lf, "Hour (slider mode)", "hour", 0, 24, 0.05, "{:05.2f} h", cb=lambda v: (self.tmode.set("manual"), SIM.__setitem__("time_mode", "manual")))
        self._scale(lf, "Moonlight", "moon", 0, 1)
        wf = ttk.LabelFrame(t, text="Weather"); wf.pack(fill="x", pady=4)
        self._scale(wf, "Clouds", "clouds", 0, 1)
        self._scale(wf, "Rain", "rain", 0, 1)
        self._scale(wf, "Fog", "fog", 0, 1)
        self._scale(wf, "Wind (bushes, trees, wind meter)", "wind", 0, 1)
        self._scale(wf, "Air temperature", "ambient_c", -20, 40, 0.5, "{:.1f} °C")
        self._check(wf, "Shadows", "shadows").pack(anchor="w")

    def _tab_camera(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" 📷 Camera ")
        ttk.Label(t, text='The camera, the pan / tilt servos and things that can go wrong. Servos only do what their pulses and their travel allow.', foreground=DIM, wraplength=760, justify='left').pack(anchor='w', pady=(4, 6))
        cols = ttk.Frame(t); cols.pack(fill="both", expand=True)
        a = ttk.Frame(cols); a.pack(side="left", fill="both", expand=True)
        b = ttk.Frame(cols); b.pack(side="left", fill="both", expand=True, padx=(8, 0))
        cf = ttk.LabelFrame(a, text="Camera"); cf.pack(fill="x", pady=4)
        f = ttk.Frame(cf); f.pack(fill="x")
        ttk.Label(f, text="Resolution", width=26).pack(side="left")
        rv = tk.StringVar(value=f"{SIM['cam_width']}x{SIM['cam_height']}")
        rc = ttk.Combobox(f, textvariable=rv, values=["640x360", "960x540", "1280x720", "1920x1080"], width=12, state="readonly")
        rc.pack(side="left")
        rc.bind("<<ComboboxSelected>>", lambda e: SIM.update(cam_width=int(rv.get().split("x")[0]), cam_height=int(rv.get().split("x")[1])))
        self._scale(cf, "Frames per second", "cam_fps", 2, 30, 1, "{:.0f}", length=200)
        self._scale(cf, "Field of view", "cam_hfov", 30, 120, 1, "{:.0f}°", length=200)
        self._scale(cf, "Sensor noise", "cam_noise", 0, 4, 0.1, "{:.1f}", length=200)
        self._check(cf, "Automatic exposure", "auto_exposure").pack(anchor="w")
        mf = ttk.LabelFrame(a, text="Where the head stands (also: 📷 tool on the map)"); mf.pack(fill="x", pady=4)
        self._scale(mf, "Height above ground", "mount_height", 0.3, 8.0, 0.05, "{:.2f} m", length=200)
        self._scale(mf, "Facing (turn the whole mount)", "mount_yaw", -180, 180, 1, "{:.0f}°", length=200)
        self._scale(mf, "Head looks down by", "mount_pitch", -30, 30, 0.5, "{:.1f}°", length=200)
        self.pos_lbl = ttk.Label(mf, foreground=DIM); self.pos_lbl.pack(anchor="w")
        ff = ttk.LabelFrame(a, text="Faults (test how the program copes)"); ff.pack(fill="x", pady=4)
        self._check(ff, "Camera cable pulled", "cam_connected").pack(anchor="w")
        ff.winfo_children()[-1].config(text="Camera connected (untick = cable pulled)")
        self._check(ff, "Picture frozen (driver hangs)", "cam_frozen").pack(anchor="w")
        self._check(ff, "Lens covered (hand / cloth)", "lens_cover").pack(anchor="w")
        self._scale(ff, "Dew / dirt on the lens", "lens_blur", 0, 1, length=200)
        self._scale(ff, "Mount wobbles", "shake", 0, 1, length=200)
        r = ttk.Frame(ff); r.pack(fill="x")
        ttk.Button(r, text="Kick the head 70° round", command=lambda: SIM.__setitem__("mount_yaw", SIM["mount_yaw"] + 70)).pack(side="left")
        ttk.Button(r, text="Turn it back", command=lambda: SIM.__setitem__("mount_yaw", SIM["mount_yaw"] - 70)).pack(side="left", padx=4)

        sf = ttk.LabelFrame(b, text="Servos (only go where their pulses and their travel allow)"); sf.pack(fill="x", pady=4)
        self._combo(sf, "Pan servo travel", "pan_travel", (90.0, 120.0, 180.0, 270.0, 360.0), 8, float)
        self._combo(sf, "Tilt servo travel", "tilt_travel", (90.0, 120.0, 180.0, 270.0, 360.0), 8, float)
        ttk.Label(sf, text="travel = degrees between 500 and 2500 µs. A 360° servo turns all the way round.", foreground=DIM,
                  wraplength=330).pack(anchor="w")
        self._scale(sf, "Tilt bracket stops at ±", "tilt_stop", 10, 89, 1, "{:.0f}°", length=130)
        self._scale(sf, "Speed", "servo_speed", 20, 900, 10, "{:.0f} °/s", length=130)
        self._scale(sf, "Jitter", "servo_jitter", 0, 3, 0.05, "{:.2f}°", length=130)
        self._check(sf, "Pan servo mounted the other way round", "pan_reversed").pack(anchor="w")
        self._check(sf, "Tilt servo mounted the other way round", "tilt_reversed").pack(anchor="w")
        self._check(sf, "Servo power on", "servo_power").pack(anchor="w")
        self._check(sf, "Pan servo stuck", "pan_stuck").pack(anchor="w")
        self._check(sf, "Tilt servo stuck", "tilt_stuck").pack(anchor="w")
        self.servo_txt = self._text(b, height=9, width=52)
        self.servo_txt.pack(fill="x", pady=4)

    def _tab_thermal_ai(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" 🌡 Thermal ")
        ttk.Label(t, text="The thermal camera (Thermal-90). People and animals are warm, the ground is not.", foreground=DIM,
                  wraplength=760, justify="left").pack(anchor="w", pady=(4, 6))
        tf = ttk.LabelFrame(t, text="Thermal camera (Waveshare Thermal-90 on the head, 80 x 62)"); tf.pack(fill="x", pady=4)
        self._check(tf, "Thermal camera plugged in", "thermal_present").pack(anchor="w")
        self._scale(tf, "Field of view", "thermal_hfov", 30, 120, 1, "{:.0f}°")
        self._scale(tf, "Noise", "thermal_noise", 0, 1, 0.01, "{:.2f} °C")
        self._check(tf, "Sun-warmed stone (hot but never moves)", "hot_stone").pack(anchor="w")
        self._check(tf, "Camp fire (very hot, flickers)", "campfire").pack(anchor="w")
        ttk.Label(tf, text="Motion Watch reads it from the simulator (/thermal.bin). Its AI works on the camera picture, as on the Pi.",
                  foreground=DIM).pack(anchor="w")

    def _tab_gpio(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" 🔗 Motion Watch ")
        ttk.Label(t, text="Motion Watch is not part of the simulator: it runs as its own program (on the Pi or a PC) and talks "
                          "to the simulator over the network.", foreground=DIM, wraplength=760, justify="left").pack(anchor="w", pady=(4, 6))
        xf = ttk.LabelFrame(t, text="① The simulator (Motion Watch connects to this)"); xf.pack(fill="x", pady=4)
        r = ttk.Frame(xf); r.pack(fill="x", pady=2)
        ttk.Checkbutton(r, text="📡 Send to Motion Watch (announce in the network)", variable=self.stream_var,
                        command=lambda: SIM.__setitem__("stream", bool(self.stream_var.get()))).pack(side="left")
        ttk.Label(xf, text="In Motion Watch: tab «Simulator» → «Simulatoren im Netz» → this simulator → «Verwenden» → "
                           "«Simulation einschalten». Its web page then also shows this simulator's controls (scenario, time, "
                           "weather, visitors, faults). The Windows firewall must allow the port (private networks).",
                  foreground=DIM, wraplength=760, justify="left").pack(anchor="w")
        self.proto_lbl = ttk.Label(xf, justify="left"); self.proto_lbl.pack(anchor="w", pady=(4, 0))
        r = ttk.Frame(xf); r.pack(fill="x", pady=2)
        ttk.Button(r, text="Copy camera address", command=self._copy_url).pack(side="left")
        for name, kind in (("Door", "door"), ("Gas", "gas")):
            ttk.Button(r, text=f"{name} on", command=lambda n=name, k=kind: self.proto and self.proto.add_event(n, k, True)).pack(side="left", padx=(8, 0))
            ttk.Button(r, text=f"{name} off", command=lambda n=name, k=kind: self.proto and self.proto.add_event(n, k, False)).pack(side="left")
        mf = ttk.LabelFrame(t, text="② Motion Watch's web page (the simulator reads what it reports: scoreboard, tests)"); mf.pack(fill="x", pady=4)
        r = ttk.Frame(mf); r.pack(fill="x", pady=2)
        ttk.Label(r, text="Address").pack(side="left")
        self.mw_url = tk.StringVar(value=bridge.LINK["url"])
        e = ttk.Entry(r, textvariable=self.mw_url, width=30); e.pack(side="left", padx=4)
        Tip(e, "Empty = automatic: the device that sends its servo positions to the simulator - it also tells http or https\n"
               "and the port of its web page. Or type it, e.g. 192.168.1.50:5000, https://192.168.1.50:5000 or 127.0.0.1:5000.")
        ttk.Label(r, text="Password").pack(side="left", padx=(8, 0))
        self.mw_pw = tk.StringVar(value=bridge.LINK["password"])
        ttk.Entry(r, textvariable=self.mw_pw, width=16, show="•").pack(side="left", padx=4)
        ttk.Button(r, text="Connect", style="Accent.TButton",
                   command=lambda: bridge.configure(self.mw_url.get(), self.mw_pw.get())).pack(side="left")
        self.link_lbl = ttk.Label(mf, justify="left"); self.link_lbl.pack(anchor="w", pady=2)
        self.cert_btn = ttk.Button(mf, text="Accept Motion Watch's new certificate", command=bridge.accept_new_cert)
        Tip(self.cert_btn, "https: the simulator remembers Motion Watch's certificate at the first contact and then accepts only that one.\n"
                           "Press this only if you know Motion Watch made a new certificate (new install, new Pi) - otherwise somebody\n"
                           "else may pretend to be Motion Watch.")
        sf = ttk.LabelFrame(t, text="③ What Motion Watch sends (POST /state)"); sf.pack(fill="x", pady=4)
        self.mw_txt = self._text(sf, height=8, width=90); self.mw_txt.pack(fill="x")
        pf = ttk.LabelFrame(t, text="Motion detector (PIR) at the box"); pf.pack(fill="x", pady=4)
        self._scale(pf, "PIR range", "pir_range", 1, 15, 0.5, "{:.1f} m")
        ttk.Label(pf, text="When somebody comes near, the simulator sends the event «PIR» (in Motion Watch: sensor source sim:PIR).",
                  foreground=DIM).pack(anchor="w")

    def _tab_tests(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" ✅ Tests ")
        ttk.Label(t, text='Automatic checks: pick one or more on the left and press Run. Green = the program reacted correctly.', foreground=DIM, wraplength=760, justify='left').pack(anchor='w', pady=(4, 6))
        top = ttk.Frame(t); top.pack(fill="x")
        self.test_list = tk.Listbox(top, selectmode="extended", height=17, width=40, exportselection=False, bg=FIELD, fg=TXT,
                                    selectbackground=ACC, selectforeground="#111", relief="flat", highlightthickness=1,
                                    highlightbackground=LINE, font=FONT, activestyle="none")
        for _k, lab, fn in SCENARIOS:
            self.test_list.insert("end", lab)
        self.test_list.pack(side="left")
        bf = ttk.Frame(top); bf.pack(side="left", padx=6, anchor="n")
        ttk.Button(bf, text="▶ Run selected", command=self._run_sel, style="Accent.TButton").pack(fill="x")
        ttk.Button(bf, text="▶▶ Run all", command=lambda: self.runner.run([s[0] for s in SCENARIOS])).pack(fill="x", pady=2)
        ttk.Button(bf, text="■ Stop", command=self.runner.stop).pack(fill="x")
        self.test_doc = ttk.Label(bf, wraplength=340, foreground=DIM, justify="left"); self.test_doc.pack(fill="x", pady=8)
        self.test_list.bind("<<ListboxSelect>>", lambda e: self._show_doc())
        ttk.Label(bf, text="Each test empties the scene, sets daylight, centres the camera, does its thing and checks the program. "
                           "Afterwards everything it changed is put back.", wraplength=340, foreground=DIM, justify="left").pack(fill="x")
        self.test_txt = self._text(t, height=18)
        self.test_txt.pack(fill="both", expand=True, pady=4)
        for tag, col in (("PASS", GOOD), ("FAIL", BAD), ("ERROR", BAD), ("SKIP", MID), ("INFO", DIM), ("HEAD", ACC)):
            self.test_txt.tag_config(tag, foreground=col)
        self.test_txt.tag_config("HEAD", font=(MONO[0], 9, "bold"))

    def _tab_log(self, nb):
        t = ttk.Frame(nb); nb.add(t, text=" 📜 Log ")
        ttk.Label(t, text="Newest first. Left: Motion Watch's event log (its web page) and what the simulator did. Right: what the scoreboard noticed.",
                  foreground=DIM).pack(anchor="w")
        f = ttk.Frame(t); f.pack(fill="both", expand=True)
        self.log_txt = self._text(f, width=70); self.log_txt.pack(side="left", fill="both", expand=True)
        self.sb_txt = self._text(f, width=50); self.sb_txt.pack(side="left", fill="both", expand=True, padx=(4, 0))

    # =================================================================================================================
    # actions
    # =================================================================================================================
    def _fill_maps(self):
        self._map_names = list(maps.MAPS)
        self.map_cb.config(values=[("★ " if maps.MAPS[n].custom else "") + maps.MAPS[n].label for n in self._map_names])
        cur = self.eng.world.map.name
        if cur in self._map_names:
            self.map_cb.current(self._map_names.index(cur))
        self.map_desc.config(text=self.eng.world.map.desc)

    def _set_map(self, name):
        self.sel = None
        self.eng.set_map(name, done=lambda m: self.win.after(0, self._map_done))
        self.map_status.config(text="building the picture …")

    def _map_done(self):
        self._fill_maps(); self.map_status.config(text="")
        self._sync_pois(force=True)
        self.top.cx, self.top.cy = SIM["cam_x"], SIM["cam_y"] + 14
        self.v3d.tx, self.v3d.ty = SIM["cam_x"], SIM["cam_y"] + 12

    def _apply_tiles(self):
        SIM["tiles"] = [n for n, v in self._tile_vars.items() if v.get()]
        maps.rebuild_region()
        self.hint.config(text="Rebuilding the Region map with " + str(len(SIM["tiles"])) + " places (a few seconds) …")
        self._set_map("region")
        try:                                                           # the start window remembers it too
            from simulator.ui import start as startwin
            path = os.path.join(os.path.dirname(maps.CUSTOM_DIR["d"] or "."), "data", "start_choices.json")
            d = startwin.load(path); d["tiles"] = SIM["tiles"]; startwin.save(path, d)
        except Exception:
            pass

    def _save_map(self):
        label = simpledialog.askstring("Save map", "Name of your map:", parent=self.win)
        if not label:
            return
        m = maps.save_custom(label, self.eng.world.map.name, self.eng.world.plants, self.eng.world.props,
                             (SIM["cam_x"], SIM["cam_y"], SIM["mount_height"], SIM["mount_yaw"]), self.eng.world.map.area)
        self.eng.world.map = m
        self.eng.renderer.map = m; self.eng.renderer.pano_map = m.name
        self._fill_maps()
        messagebox.showinfo("Save map", f"Saved as «{m.label}» ({maps.CUSTOM_DIR['d']}).", parent=self.win)

    def _open_web(self):
        if bridge.address():
            webbrowser.open(bridge.address() + "/")
        else:
            messagebox.showinfo("Motion Watch", "No Motion Watch connected yet - see tab 🔗 Motion Watch.", parent=self.win)

    def _copy_url(self):
        if self.proto:
            from simulator.hardware.protocol import lan_ip
            self.win.clipboard_clear(); self.win.clipboard_append(f"http://{lan_ip()}:{self.proto.port}/cam/0/video.mjpg")

    def _run_sel(self):
        keys = [SCENARIOS[i][0] for i in self.test_list.curselection()]
        if keys:
            self.runner.run(keys)

    def _show_doc(self):
        sel = self.test_list.curselection()
        if sel:
            self.test_doc.config(text=(SCENARIOS[sel[0]][2].__doc__ or "").strip())

    # ---- mouse on the map views ----
    def _resize(self, e, v):
        if v == "2d":
            if (e.width, e.height) != (self.top.W, self.top.H) and e.width > 50 and e.height > 50:
                self.top.W, self.top.H = e.width, e.height; self.top._key = None
        else:
            self.v3d.set_size(e.width, e.height)

    def _ground(self, e, v):
        return self.top.to_world(e.x, e.y) if v == "2d" else self.v3d.pick(e.x, e.y)

    def _press(self, e, v):
        p = self._ground(e, v)
        if p is None:
            return
        x, y = p
        tool = self.tool.get()
        world = self.eng.world
        if tool in W.KINDS:
            n = max(1, int(self.count.get() or 1))
            for i in range(n):
                jx, jy = (random.uniform(-1.2, 1.2), random.uniform(-1.2, 1.2)) if n > 1 else (0.0, 0.0)
                world.add(W.make_visit(tool, x + jx, y + jy))
            self.hint.config(text=f"{n} x {tool} on the way to ({x:.1f}, {y:.1f}) m")
        elif tool == "move":
            it = nearest(self.eng, x, y, 2.5)
            self.drag = ("move", it, x, y) if it else None
            self.sel = it
        elif tool == "delete":
            it = nearest(self.eng, x, y, 2.5, what=("ent", "plant", "prop"))
            if it:
                self._delete(it)
        elif tool == "camera":
            self.drag = ("camera", x, y)
        elif tool in ("tree", "bush"):
            size = random.uniform(6, 10) if tool == "tree" else random.uniform(1.0, 1.8)
            world.plants = world.plants + [W.Plant(x, y, tool, size, random.randint(1, 99999))]
            self.eng.scenery_changed()
        elif tool == "prop":
            k = self.prop_kind.get()
            w_, d_, h_, col, ridge = maps.PROP_TYPES[k]
            world.props = world.props + [W.Prop(k, x, y, w_, d_, h_, col, ridge=ridge)]
            self.eng.scenery_changed()

    def _motion(self, e, v):
        if not self.drag:
            return
        p = self._ground(e, v)
        if p is None:
            return
        x, y = p
        if self.drag[0] == "move" and self.drag[1]:
            kind, o = self.drag[1]
            if kind == "camera":
                self.hint.config(text=f"camera to ({x:.1f}, {y:.1f}) m - release to rebuild the picture there")
                self.drag = ("move", self.drag[1], x, y)
            else:
                o.x, o.y = x, y
                if kind == "ent":
                    o.speed = 0.0
        elif self.drag[0] == "camera":
            sx, sy = self.drag[1], self.drag[2]
            if math.hypot(x - sx, y - sy) > 0.8:
                SIM["mount_yaw"] = round(math.degrees(math.atan2(x - sx, y - sy)), 1)
                self.hint.config(text=f"camera at ({sx:.1f}, {sy:.1f}) facing {SIM['mount_yaw']:.0f}°")

    def _release(self, e, v):
        if not self.drag:
            return
        if self.drag[0] == "camera":
            SIM.update(cam_x=round(self.drag[1], 2), cam_y=round(self.drag[2], 2))
            self.hint.config(text="camera moved - building the picture for the new place (a few seconds) …")
        elif self.drag[0] == "move" and self.drag[1] and self.drag[1][0] == "camera":
            SIM.update(cam_x=round(self.drag[2], 2), cam_y=round(self.drag[3], 2))
        elif self.drag[0] == "move" and self.drag[1] and self.drag[1][0] in ("prop", "plant"):
            self.eng.scenery_changed()
        self.drag = None

    def _delete(self, it):
        kind, o = it
        world = self.eng.world
        if kind == "ent":
            world.remove(o.id)
        elif kind == "plant":
            world.plants = [p for p in world.plants if p is not o]
        elif kind == "prop":
            world.props = [p for p in world.props if p is not o]
        self.sel = None
        self.eng.scenery_changed()

    def _rpress(self, e, v, pan=False):
        self._r = (e.x, e.y, pan or bool(e.state & 0x0001), False)

    def _rmotion(self, e, v):
        if not getattr(self, "_r", None):
            return
        x0, y0, pan, _moved = self._r
        dx, dy = e.x - x0, e.y - y0
        if abs(dx) + abs(dy) < 2:
            return
        self._r = (e.x, e.y, pan, True)
        if v == "2d":
            self.top.cx -= dx * self.top.mpp; self.top.cy += dy * self.top.mpp
        elif pan:
            a = math.radians(self.v3d.yaw); k = self.v3d.dist / 400.0
            self.v3d.tx -= (math.cos(a) * dx - math.sin(a) * dy) * k
            self.v3d.ty -= (-math.sin(a) * dx - math.cos(a) * dy) * k
        else:
            self.v3d.yaw += dx * 0.4
            self.v3d.pitch = max(5.0, min(89.0, self.v3d.pitch + dy * 0.3))

    def _rrelease(self, e, v):
        r = getattr(self, "_r", None); self._r = None
        if r and not r[3] and v == "2d":
            p = self.top.to_world(e.x, e.y)
            it = nearest(self.eng, p[0], p[1], 2.5)
            if it:
                self._menu(e, it)

    def _menu(self, e, it):
        kind, o = it
        m = tk.Menu(self.win, tearoff=0)
        if kind == "ent":
            m.add_command(label=f"{o.describe()}", state="disabled")
            m.add_command(label="Walk away now", command=lambda: self.eng.world.send_away(o.id))
            m.add_command(label="Stay here", command=lambda: (setattr(o, "tasks", [("wait", None)]), setattr(o, "pinned", True)))
            m.add_command(label="Remove at once", command=lambda: self.eng.world.remove(o.id))
        elif kind in ("plant", "prop"):
            m.add_command(label=(o.kind if kind == "plant" else o.name), state="disabled")
            m.add_command(label="Delete", command=lambda: self._delete(it))
        else:
            m.add_command(label=f"Camera at ({SIM['cam_x']:.1f}, {SIM['cam_y']:.1f}), facing {SIM['mount_yaw']:.0f}°", state="disabled")
        m.tk_popup(e.x_root, e.y_root)

    def _wheel(self, e, v):
        f = 0.88 if e.delta > 0 else 1.0 / 0.88
        if v == "2d":
            self.top.zoom(f, e.x, e.y)
        else:
            self.v3d.dist = max(4.0, min(1500.0, self.v3d.dist * f))

    def _hover(self, e, v):
        p = self._ground(e, v)
        if p is None:
            self.hover = None; return
        self.hover = nearest(self.eng, p[0], p[1], 2.0) if self.tool.get() in ("move", "delete") else None
        tool = self.tool.get()
        txt = f"({p[0]:.1f}, {p[1]:.1f}) m   "
        if tool in W.KINDS:
            txt += f"click: a {tool} comes here from outside the picture, stays {SIM['visit_wait']:.0f} s, then leaves"
        elif tool == "camera":
            txt += "click = put the camera here, drag = which way it faces"
        elif tool in ("move", "delete"):
            txt += "click / drag something (people, animals, trees, props, the camera)"
        else:
            txt += f"click = place a {self.prop_kind.get() if tool == 'prop' else tool}"
        if not self.drag:
            self.hint.config(text=txt)

    # =================================================================================================================
    # refresh
    # =================================================================================================================
    def _tick(self):
        try:
            self._refresh()
        except Exception as e:                        # never let the window die
            import traceback
            traceback.print_exc()
            self.hint.config(text=f"panel error: {e}")
        self.win.after(150, self._tick)

    def _pills(self):
        from simulator.scene.world import sim_hour
        if bool(self.stream_var.get()) != bool(SIM["stream"]):
            self.stream_var.set(bool(SIM["stream"]))
        if not SIM["stream"]:
            self._pill("net", "📡 silent", DIM)
        elif self.proto and self.proto.announce_error and not self.proto.announced:
            self._pill("net", "📡 cannot announce", BAD)
        else:
            self._pill("net", "📡 announced", GOOD)
        if bridge.ready():
            self._pill("prog", "● Motion Watch running", GOOD)
            armed = bridge.state("arm_state", "")
            self._pill("armed", f"{'🔒' if 'armed' == armed else '🔓'} {armed}", BAD if armed == "armed" else TXT)
            p = int(bridge.state("persons", 0) or 0)
            tru = self.eng.scoreboard.now.get("truth_persons", 0)
            self._pill("persons", f"persons: {p} reported / {tru} real", GOOD if p == tru else MID)
            self._pill("cam", f"cam: {bridge.state('source_status', '-')}"[:34])
        else:
            self._pill("prog", "○ waiting for Motion Watch", MID)
            self._pill("armed", "-"); self._pill("persons", f"in view: {self.eng.scoreboard.now.get('truth_persons', 0)}")
            self._pill("cam", "protocol: " + (f"{self.proto.posts} states" if self.proto else "off"))
        h = sim_hour()
        self._pill("map", "🗺 " + self.eng.world.map.label + (" (building …)" if self.eng.map_loading else ""))
        self._pill("time", f"🕑 {int(h):02d}:{int(h * 60) % 60:02d}{' ⏸' if SIM['paused'] else ''}")
        pa, ti, src = self.eng.servo_angles()
        self._pill("servo", f"pan {pa:+.0f}°  tilt {ti:+.0f}°  ({src})")

    def _refresh(self):
        now = time.time()
        eng = self.eng
        SIM._d["_camera_tool"] = self.tool.get() == "camera"
        vi = self.vnb.index(self.vnb.select())
        if vi == 0:
            self._show(self.c2d, "2d", self.top.render(eng, self.sel, self.hover))
        else:
            self._show(self.c3d, "3d", self.v3d.render(eng, self.sel, self.hover))
        if eng.map_loading:
            self.map_status.config(text=f"building «{eng.map_loading}» …")
        tab = self.nb.index(self.nb.select())
        slow = now - getattr(self, "_slow_t", 0) > 0.5
        if tab == 0:
            if eng.frame is not None:
                fr = eng.frame
                h = int(fr.shape[0] * 480 / fr.shape[1])
                self.cam_lbl.config(image=self._keep("cam", _photo(cv2.resize(fr, (480, h), interpolation=cv2.INTER_AREA))))
            th = eng.thermal_preview()
            if th is not None:
                self.th_lbl.config(image=self._keep("th", _photo(thermal_colour(th, (240, 186)))))
            if slow:
                self._program_status(); self._score()
        if not slow:
            return
        self._slow_t = now
        if getattr(self, "_shown_map", None) != eng.world.map.name and not eng.map_loading:
            self._shown_map = eng.world.map.name                   # also when it was switched from Motion Watch's web page
            self._map_done()
        self._pills()
        self._sync_pois()
        self.campos.config(text=f"Camera now: x {SIM['cam_x']:.1f} m, y {SIM['cam_y']:.1f} m, {SIM['mount_height']:.1f} m high, "
                                f"facing {SIM['mount_yaw']:.0f}°" + ("   (building the picture …)" if self.eng._building else ""))
        if tab == 1:
            for k, lab in self._now_lbl.items():
                lab.config(text=f"now: {sum(1 for e in eng.world.snapshot() if e.kind == k)}")
        elif tab == 3:
            self._servo_status()
        elif tab == 5:
            self._link_status()
        elif tab == 6:
            self._tests_status()
        elif tab == 7:
            self._log_status()
        self._sync_bound()

    def _keep(self, k, img):
        self._imgs[k] = img
        return img

    def _show(self, canvas, k, bgr):
        ph = self._keep(k, _photo(bgr))
        if getattr(canvas, "_item", None) is None:
            canvas._item = canvas.create_image(0, 0, anchor="nw", image=ph)
        else:
            canvas.itemconfig(canvas._item, image=ph)

    def _sync_bound(self):
        """Settings changed elsewhere (a test, the map editor) show up in the sliders."""
        for var, key in self._bound:
            try:
                cur = SIM[key]
                if isinstance(var, tk.BooleanVar):
                    if bool(var.get()) != bool(cur):
                        var.set(bool(cur))
                elif abs(float(var.get()) - float(cur)) > 1e-6:
                    var.set(float(cur))
            except (tk.TclError, TypeError, ValueError):
                pass
        if self.tmode.get() != SIM["time_mode"]:
            self.tmode.set(SIM["time_mode"])

    def _program_status(self):
        if not bridge.ready():
            self.prog_txt.delete("1.0", "end")
            self.prog_txt.insert("end", "Waiting for Motion Watch: " + bridge.status() + "\n\nTab 🔗 Motion Watch shows how to connect it.")
            return
        for k, v in self._pvars.items():
            v.set(bool(bridge.cfg(k)))
        st = bridge.state
        lights = st("lights", {}) or {}
        tamper = st("tamper", {}) or {}
        lines = [
            f"Armed           {st('arm_state')}" + (f" (in {st('arm_left')} s)" if st("arm_left") else ""),
            f"Camera          {st('source_label')} {st('source_res')} - {st('source_status')}",
            f"FPS / CPU       {st('fps')}   cpu {st('cpu')}%",
            f"Persons         {st('persons')}   moving things {st('candidates')}   objects: {st('object_summary') or '-'}",
            f"In view         {', '.join(st('present', []) or []) or '-'}",
            f"Tracking        {'YES' if st('tracking') else 'no'}" + (f"   pan {self.eng.proto.servo.pan:.1f}%  tilt {self.eng.proto.servo.tilt:.1f}%"
                                                                   if self.eng.proto is not None else ""),
            f"Patrol          {st('patrol_status')}",
            f"Recording       {'● ' + str(st('rec_name')) if st('recording') else 'no'}",
            f"Rain / wind     {'RAIN MODE' if st('rain_mode') else 'no rain'} ({st('rain_score')})  wind {st('wind_level')} x{st('wind_boost')}",
            f"Light           brightness {st('brightness')}  low-light {'ON' if st('lowlight') else 'off'}  "
            f"lights: {'white ' if lights.get('white') else ''}{'IR' if lights.get('ir') else ''}{'-' if not (lights.get('white') or lights.get('ir')) else ''}",
            f"AI              {st('ai_status')}",
            f"Thermal         {st('thermal')}  max {st('thermal_max')}°C  warm bodies {st('warm')}",
            f"Sabotage        {tamper.get('state', '-')}   last: {tamper.get('last') or '-'}",
            f"Servos          {st('servo_backend')}",
            f"Power saving    {st('eco')}",
        ]
        self.prog_txt.delete("1.0", "end"); self.prog_txt.insert("end", "\n".join(lines))

    def _score(self):
        rows = self.eng.scoreboard.rows()
        while len(self.score_lbls) < len(rows):
            r = ttk.Frame(self.score_frame); r.pack(fill="x")
            a = ttk.Label(r, width=30, foreground=DIM); a.pack(side="left")
            b = tk.Label(r, anchor="w", width=26, bg=BG, fg=TXT, font=("Segoe UI Semibold", 9)); b.pack(side="left")
            self.score_lbls.append((a, b))
        for (a, b), (lab, val, col) in zip(self.score_lbls, rows):
            a.config(text=lab); b.config(text=val, fg=col or TXT)
        c = self.timeline
        c.delete("all")
        hist = list(self.eng.scoreboard.hist)
        if hist:
            t1 = hist[-1][0]; W_, H_ = 330, 70
            mx = max(2, max(max(h[1], h[2]) for h in hist))
            for i in range(1, len(hist)):
                t, tru, prog, trk, rec = hist[i]
                x = W_ - (t1 - t) / 120.0 * W_
                xp = W_ - (t1 - hist[i - 1][0]) / 120.0 * W_
                if trk:
                    c.create_rectangle(xp, 0, x, 6, fill="#4ea1ff", width=0)
                if rec:
                    c.create_rectangle(xp, 7, x, 12, fill=BAD, width=0)
                c.create_line(xp, H_ - 2 - hist[i - 1][1] / mx * 52, x, H_ - 2 - tru / mx * 52, fill="#59606d", width=4)
                c.create_line(xp, H_ - 2 - hist[i - 1][2] / mx * 52, x, H_ - 2 - prog / mx * 52, fill=ACC, width=2)

    def _servo_status(self):
        eng = self.eng
        pa, ti, src = eng.servo_angles()
        lines = [f"driven by:  {'Motion Watch (POST /state)' if src == 'protocol' else 'nothing - no Motion Watch sends servo positions'}"]
        for n in ("pan", "tilt"):
            s = eng.servos[n]
            lines.append(f"{n:4}: angle {s.angle:7.1f}°  target {s.target:7.1f}°  pulse "
                         f"{'-' if s.pulse is None else f'{s.pulse:.0f} us'}  moved {s.travel:6.0f}°  turns back {s.reversals}")
        yaw, pitch = eng.pose
        lines.append(f"camera looks: {yaw:.1f}° (facing {SIM['mount_yaw']:.0f}° + pan), {pitch:.1f}° up/down")
        if eng.proto is not None:
            sv = eng.proto.servo
            lines.append(f"Motion Watch says: pan {sv.pan:.1f}% ({sv.pan_deg:+.1f}°)  tilt {sv.tilt:.1f}% ({sv.tilt_deg:+.1f}°)  "
                         f"limits ±{sv.pan_limit:.0f}° / ±{sv.tilt_limit:.0f}°")
        lines.append(f"render {eng.render_ms:.0f} ms/frame")
        self.servo_txt.delete("1.0", "end"); self.servo_txt.insert("end", "\n".join(lines))
        self.pos_lbl.config(text=f"camera at x {SIM['cam_x']:.1f} m, y {SIM['cam_y']:.1f} m (📷 tool or ✋ Move on the map)")

    def _link_status(self):
        if self.proto:
            from simulator.hardware.protocol import lan_ip
            st = "running" if self.proto.running else ("ERROR " + self.proto.error if self.proto.error else "starting")
            ip = lan_ip()
            ann = ("silent - switch «Send to Motion Watch» on" if not SIM["stream"] else
                   f"every 2 s on UDP port 8764 ({self.proto.announced} sent)"
                   + (f" - problem: {self.proto.announce_error}" if self.proto.announce_error else ""))
            self.proto_lbl.config(text=f"«{self.proto.name}»   server {st} on port {self.proto.port}   address http://{ip}:{self.proto.port}\n"
                                       f"announced: {ann}\n"
                                       f"camera http://{ip}:{self.proto.port}/cam/0/video.mjpg   (cam 1 = fixed camera, /thermal.bin, /events, /control)\n"
                                       f"POST /state received: {self.proto.posts}   events sent: {len(self.proto.events)}   "
                                       f"sound at the camera: {self.proto.sound_db:.0f} dB")
        else:
            self.proto_lbl.config(text="protocol server off (--no-protocol)")
        ok = bridge.ready()
        self.link_lbl.config(text=("● " if ok else "○ ") + bridge.status(), foreground=GOOD if ok else MID)
        if bool(bridge.LINK["cert_new"]) != bool(self.cert_btn.winfo_manager()):
            if bridge.LINK["cert_new"]:
                self.cert_btn.pack(anchor="w", pady=2)
            else:
                self.cert_btn.pack_forget()
        pr = self.eng.proto
        if pr is None:
            text = "nothing yet - Motion Watch has not sent its state to the simulator"
        else:
            age = time.time() - self.eng.proto_t
            sv, li, mv = pr.servo, pr.lights, self.eng.mover
            text = "\n".join([
                f"from            {pr.device}   {age:.1f} s ago" + ("" if age < 3 else "   (no longer sending!)"),
                f"servos          pan {sv.pan:.1f}% ({sv.pan_deg:+.1f}°)   tilt {sv.tilt:.1f}% ({sv.tilt_deg:+.1f}°)   "
                f"limits ±{sv.pan_limit:.0f}° / ±{sv.tilt_limit:.0f}°   {'moving' if sv.moving else 'still'}",
                f"lights          white {'ON' if li.white else 'off'}   IR {'ON' if li.ir else 'off'}",
                "relays          " + (", ".join(f"{r.name} {'ON' if r.on else 'off'}" for r in pr.relays) or "-"),
                f"sound           {pr.sound or '-'}",
                ("mover           " + (f"ON  x {mv.x:+.1f} m  y {mv.y:+.1f} m  turned {mv.yaw:+.0f}°  driven {mv.odo:.1f} m"
                                       + ("  BLOCKED" if mv.blocked else "") + f"  tracks {mv.l:+.2f} / {mv.r:+.2f}"
                                       if mv.on else "off (Motion Watch switches it on with its second joystick)")),
                f"armed           {'yes' if pr.armed else 'no'}   picture {pr.picture_mode}",
            ])
        self.mw_txt.delete("1.0", "end"); self.mw_txt.insert("end", text)

    def _tests_status(self):
        r = self.runner
        if r.changed == self._runs_seen:
            return
        self._runs_seen = r.changed
        t = self.test_txt
        t.delete("1.0", "end")
        items = list(r.history)
        if r.current is not None:
            items.append((None, r.current.name, list(r.current.results), "running …"))
        if not items:
            t.insert("end", "No test run yet. Select tests on the left and press Run (Motion Watch must be connected - tab 🔗 Motion Watch).\n", "INFO")
        npass = sum(1 for h in r.history if h[3] == "PASS"); nfail = sum(1 for h in r.history if h[3] in ("FAIL", "ERROR"))
        if r.history:
            t.insert("end", f"Done: {len(r.history)}   passed {npass}   failed {nfail}\n\n", "HEAD")
        for _k, label, res, status in reversed(items):
            t.insert("end", f"{label}  —  {status}\n", "HEAD")
            for x in res:
                t.insert("end", f"   {x['status']:5} {x['label']}", x["status"])
                t.insert("end", f"   {x['detail']}\n" if x["detail"] else "\n", "INFO")
            t.insert("end", "\n")

    def _log_status(self):
        self.log_txt.delete("1.0", "end")
        for ev in bridge.events(150):
            self.log_txt.insert("end", f"{ev.get('t')} [{ev.get('kind')}] {ev.get('text')}\n")
        if bridge.LOG:
            self.log_txt.insert("end", "\n--- simulator ---\n" + "\n".join(bridge.LOG))
        self.sb_txt.delete("1.0", "end")
        self.sb_txt.insert("end", "\n".join(self.eng.scoreboard.log))


def _tab_help(self, nb):
    t = ttk.Frame(nb); nb.add(t, text=" ❓ Help ")
    txt = self._text(t, wrap="word")
    txt.pack(fill="both", expand=True, pady=4)
    txt.insert("end", GUIDE + """


WHAT EACH TAB IS FOR
▶ Live                camera + thermal picture, the program's state, Arm / Disarm, open the web page, scoreboard
👥 People             how many of each kind keep walking through, how people behave, pause / time speed
🗺 World              7 maps, time of day, clouds, rain, fog, wind, air temperature
📷 Camera             resolution, field of view, where the head stands, servo travel / speed / faults, camera faults
🌡 Thermal            thermal camera plugged in or not, hot stone / camp fire
🔗 Motion Watch       how Motion Watch connects, its web page address, what it sends (servos, lights, relays)
✅ Tests              18 automatic checks of Motion Watch
📜 Log                Motion Watch's event log + what the scoreboard noticed

MOTION WATCH AND THE SIMULATOR
• Motion Watch runs as its own program - on the Pi or on any PC in the same network.
• Switch "📡 Send to Motion Watch" on: the simulator announces itself in the network. In Motion Watch:
  tab «Simulator» → «Simulatoren im Netz» → «Verwenden» → «Simulation einschalten».
• Motion Watch's web page can also run this simulator: scenario (map), time, weather, visitors, faults.
• A siren / sound from Motion Watch makes the animals nearby run away (tests the deterrent).
• It reads the camera pictures and the thermal picture from the simulator and sends its servo, light and
  relay positions back - the simulated head turns exactly like the real servos would.
• The simulator reads Motion Watch's web page for the scoreboard and the tests. If it has a web password,
  enter it in tab 🔗 Motion Watch.
""")
    txt.config(state="disabled")


Panel._tab_help = _tab_help
