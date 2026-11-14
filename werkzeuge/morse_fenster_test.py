#!/usr/bin/env python3
"""Test «Morse-Modus» im Pi-Fenster (Teil 639zzz, Schritt 2) - mit einem nachgebauten tkinter, läuft also auch ohne Bildschirm
und ohne tkinter: das Fenster wird gebaut, die Anzeige (tick) läuft, Knöpfe werden gedrückt. Prüft in allen 5 Sprachen:
Schalter «mit dem Mikrofon», «Testsignal per Infrarot senden» (nur IR), Text mit Ton, Ergebnis der Gegenstelle, «Schliessen».
Nicht geprüft: wie das echte Tk-Fenster aussieht.

  python3 werkzeuge/morse_fenster_test.py [--datei webcam_bewegung_X.py]
"""
import glob, os, re, subprocess, sys, tempfile, types, shutil
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


if len(sys.argv) < 3 or sys.argv[1] != "--eine":                  # Aufruf von aussen: jede Sprache in einem eigenen Prozess
    datei = sys.argv[sys.argv.index("--datei") + 1] if "--datei" in sys.argv else neueste()
    bad = 0
    for L in ("de", "en", "fr", "it", "rm"):
        print("== " + L, flush=True)
        bad += subprocess.call([sys.executable, os.path.abspath(__file__), "--eine", datei, L], timeout=300) != 0
    print("Fenster: " + ("alle 5 Sprachen ok" if not bad else "%d Sprachen mit Fehlern" % bad))
    sys.exit(1 if bad else 0)
datei, lang = sys.argv[2], sys.argv[3]
home = tempfile.mkdtemp(prefix="mw_morse_w_")
os.environ["MOTIONWATCH_HOME"] = home
ns = {"__name__": "mw_win_test", "__file__": os.path.abspath(datei)}
exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
W = []; AFTER = []


class Wd:
    def __init__(self, parent=None, **kw):
        self.kw = dict(kw); self.parent = parent; self.binds = {}; self.packed = False; self.body = ""; self.cls = type(self).__name__
        W.append(self)
    def config(self, **kw): self.kw.update(kw)
    configure = config
    def cget(self, k): return self.kw.get(k, "")
    def pack(self, **kw): self.packed = True
    grid = pack
    def bind(self, ev, f): self.binds[ev] = f
    def after(self, ms, f): AFTER.append(f)
    def winfo_exists(self): return True
    def title(self, t): self.kw["title"] = t
    def geometry(self, g): self.kw["geometry"] = g
    def lift(self): pass
    def destroy(self): self.kw["destroyed"] = True
    def delete(self, *a): self.body = ""
    def insert(self, i, s): self.body += s
    def get(self, *a): return self.body


class Var:
    def __init__(self, value=False): self.v = value
    def get(self): return self.v
    def set(self, v): self.v = v


tk = types.SimpleNamespace(Toplevel=type("Toplevel", (Wd,), {}), Label=type("Label", (Wd,), {}), Frame=type("Frame", (Wd,), {}),
                           Entry=type("Entry", (Wd,), {}), Text=type("Text", (Wd,), {}), Checkbutton=type("Checkbutton", (Wd,), {}), BooleanVar=Var)
ns["tk"] = tk
src = open(os.path.join(REPO, "quelle", "639zzz_morse.py"), encoding="utf-8").read()
i = src.index("if GUI_OK:\n    def _morse_tk_win"); e = src.index("App._morse_win = _morse_tk_win", i) + len("App._morse_win = _morse_tk_win")
ns["GUI_OK"] = True
exec(compile(src[i:e], "639zzz(fenster)", "exec"), ns)
for f in ("_fbtn", "_morse_tk_win"):
    fn = getattr(ns["App"], f, None)
    if fn is not None and hasattr(fn, "__globals__"):
        fn.__globals__["tk"] = tk
CFG = ns["CFG"]; ns["set_lang"](lang) if "set_lang" in ns else None
CFG["lang"] = lang
App = ns["App"]
a = App.__new__(App); a.root = Wd(); a._open_page = lambda p: None
a._morse_win()
FAIL = []
def ok(c, m): print(("  ✓ " if c else "  ✗ ") + m, flush=True); c or FAIL.append(m)
def texts(): return [w.kw.get("text", "") for w in W if w.packed] + [w.body for w in W if w.cls == "Text"]
def click(sub):
    b = [w for w in W if sub in str(w.kw.get("text", "")) and "<Button-1>" in w.binds]
    assert b, sub
    b[0].binds["<Button-1>"](None)
def tick():
    f = AFTER.pop(0); f()

tr = ns["tr"]
ok(any(tr("Read a tone or a whistle with the microphone") == t for t in texts()), "Schalter «mit dem Mikrofon»: " + tr("Read a tone or a whistle with the microphone"))
ok(any(tr("Close") == t for t in texts()), "Knopf «%s» (Weg zurück)" % tr("Close"))
ns["morse_start"](5, "test")
ns["morse_rx_text"]("CQ TEST DE HB9", "sound", {"wpm": 12})
tick()
body = [w.body for w in W if w.cls == "Text"][0]
ok(tr("sound") + ": CQ TEST DE HB9" in body, "Text mit Ton im Fenster: " + body.splitlines()[0])
peer = [t for t in texts() if tr("No test signal of the other MoveEye read yet.") in t]
ok(bool(peer), "noch kein Testsignal: " + (peer[0] if peer else ""))
ns["morse_rx_text"](ns["MORSE_TEST_TEXT"], "camera", {"wpm": 6})
tick()
ok(any(t.startswith("✓ " + tr("Test signal of the other MoveEye read")) for t in texts()), "Testsignal gelesen: " + str([t for t in texts() if t.startswith("✓")][:1]))
cb = [w for w in W if w.cls == "Checkbutton"][0]
cb.kw["variable"].set(True); cb.kw["command"]()
ok(CFG["morse_rx_sound"] is True, "Schalter Mikrofon an -> morse_rx_sound")
cb.kw["variable"].set(False); cb.kw["command"]()
ok(CFG["morse_rx_sound"] is False, "Schalter Mikrofon aus")
CFG["light_ir_out"] = "gpio:27"; ns["MORSE"]["tx_starts"] = []
click(tr("Send the test signal by infrared"))
tx = ns["MORSE"]["tx"]
ok(tx is not None and tx["outs"] == {"ir"} and tx["shown"] == ns["MORSE_TEST_TEXT"], "Testsignal per Infrarot gesendet (nur IR)")
msg = [w for w in W if w.cls == "Label" and "WPM" in str(w.kw.get("text", ""))]
ok(bool(msg), "Fenster zeigt den Plan: " + (msg[0].kw["text"] if msg else ""))
ns["morse_tx_stop"]("test"); ns["morse_end"]("test")
click(tr("Close"))
ok(a._morse_top.kw.get("destroyed"), "Schliessen schliesst das Fenster")
shutil.rmtree(home, ignore_errors=True)
print(("FEHLER: %d" % len(FAIL)) if FAIL else "alles ok", flush=True)
os._exit(1 if FAIL else 0)
