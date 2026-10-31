#@ MoveEye – Teil 589: «Blinki», die kleine Figur aus dem MoveEye-Logo (Auge, Füsse; ohne Sichtfächer, Stimmung kurz in einer Sprechblase) für die Einrichtung und die Rundgänge – Web (SVG + CSS, Skript vor /g2/ui.js) und Fenster (kleines Bild, mit cv2 gezeichnet). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): an own, ABSTRACT mascot «Blinki» - only in the guide (setup assistant) and the tours.
# Built from the shapes of the logo (144 / simulator mw_logo.gd): the orange field-of-view fan is the body, the eye at the
# bottom (orange iris, dark pupil) is the face, the four detection corners float in the fan and show the mood.
#   * blinks every few seconds (the name), looks left / right, hops when a step is done, «talks» when a new text comes
#   * moods: normal · point (explains, looks at the text) · happy (eye smiles, heart) · think (looks up, three dots)
# Daniel 31.10.2026: Blinki everywhere WITHOUT the orange fan - eye, rim, feet; the mood shows in the eye and the hop.
#   The mood signs (corners, arrow, heart, dots) appear for ~2 s in a small speech bubble above / right of Blinki, only when
#   the mood changes (MWBlinki.mood), then fade out; same bubble in the simulator (mehr_icons.gd blinki_bubble). Window: no
#   bubble. viewBox now 26 59 48 52 (the old coordinates stay). The logo (144 / mw_logo.gd) is separate and keeps its fan.
#   * prefers-reduced-motion: no animation; light / dark / Rotlicht (html.sxnight: dim colours)
#   * setting «blinki_on» (Setup; also in the guide step «Tours and tips» and under More); off = the plain boxes as before
# Web: window.MWBlinki (make / mood / hop / talk / row) is put in front of the script /g2/ui.js (516), which uses it in the
# tour bubble and in the guide. Window: blinki_tk_image() draws the same figure with cv2 into a PNG (585 uses it).
# ----------------------------------------------------------------------------
CFG.setdefault("blinki_on", True); DEFAULTS.setdefault("blinki_on", True)
TOGGLES.append(("Setup", "blinki_on", "Show Blinki (the little figure that explains the setup and the tours)"))
SIMPLE_KEYS.add("blinki_on")
SET_HELP["blinki_on"] = ("Blinki is the little figure made of the MoveEye logo: it speaks the texts of the setup and the tours.",
                         "On - switch it off if you prefer plain text boxes.")
BLINKI_TX = ["Hello, I am Blinki!", "I am the eye of MoveEye. I show you everything step by step - and when I blink, all is well.", "Show Blinki"]

# the figure (viewBox 26 59 48 52, coordinates of the old 100 x 112 figure): eye = face, feet; __I__ = unique id
BLINKI_SVG = (
    '<svg viewBox="26 59 48 52" class="bk-svg" focusable="false" aria-hidden="true"><defs>'
    '<clipPath id="bkc__I__"><circle cx="50" cy="80" r="16.6"/></clipPath></defs>'
    '<g class="bk-all">'
    '<ellipse class="bk-ft" cx="39" cy="105.5" rx="7.5" ry="3.8"/><ellipse class="bk-ft" cx="61" cy="105.5" rx="7.5" ry="3.8"/>'
    '<g class="bk-eye"><circle class="bk-scl" cx="50" cy="80" r="17"/>'
    '<g clip-path="url(#bkc__I__)"><g class="bk-pup"><circle class="bk-iris" cx="50" cy="80" r="10.5"/><circle class="bk-pupil" cx="50" cy="80" r="5.2"/>'
    '<circle class="bk-hl" cx="53.2" cy="76.6" r="2"/></g>'
    '<path class="bk-hap" d="M40.5 83.5 Q50 71 59.5 83.5"/>'
    '<rect class="bk-lid" x="32" y="62" width="36" height="36"/></g>'
    '<circle class="bk-rim" cx="50" cy="80" r="17"/></g></g></svg>')

# the mood bubble (own viewBox 28 19 44 47 with the old corner coordinates): put next to the figure by MWBlinki.make (not
# part of BLINKI_SVG, so the status LED of 599c, which uses BLINKI_SVG, stays without it). Same shape as mehr_icons.gd.
BLINKI_BUB = (
    '<svg viewBox="28 19 44 47" class="bk-bub" focusable="false" aria-hidden="true">'
    '<path class="bk-bb" d="M39 21 H61 A8 8 0 0 1 69 29 V49 A8 8 0 0 1 61 57 H47 L30 64 L39 57 A8 8 0 0 1 31 49 V29 A8 8 0 0 1 39 21 Z"/>'
    '<path class="bk-br" d="M37 33 V27 H43 M57 27 H63 V33 M63 45 V51 H57 M43 51 H37 V45"/>'
    '<path class="bk-i bk-ip" d="M46 33.5 L54.5 39 L46 44.5"/>'
    '<path class="bk-i bk-ih" d="M50 46 C42 40.5 42.5 33.5 46.5 33.5 C48.6 33.5 49.6 35 50 36.4 C50.4 35 51.4 33.5 53.5 33.5 C57.5 33.5 58 40.5 50 46 Z"/>'
    '<g class="bk-i bk-it"><circle cx="43.5" cy="39" r="2.4"/><circle cx="50" cy="39" r="2.4"/><circle cx="56.5" cy="39" r="2.4"/></g></svg>')

BLINKI_CSS = r"""
.bk{--bk-o:#ff9f43;--bk-o2:#e8590c;--bk-w:#fff;--bk-d:#0a0e14;--bk-hl:#fff;color:var(--txt,#e8eef5);width:56px;flex:none;align-self:flex-start;line-height:0;position:relative}
body.light .bk{--bk-o2:#d9530a}
html.sxnight .bk{--bk-o:#7a160e;--bk-o2:#5a0f0a;--bk-w:#2a0606;--bk-d:#000;--bk-hl:#3a0a08}
.bk svg{display:block;width:100%;height:auto;overflow:visible}
.bk .bk-ft{fill:var(--bk-o2)}
.bk .bk-br{fill:none;stroke:currentColor;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
.bk .bk-i{display:none}.bk .bk-ip{fill:none;stroke:currentColor;stroke-width:3.2;stroke-linecap:round;stroke-linejoin:round}
.bk .bk-ih{fill:var(--bk-o2)}.bk .bk-it circle{fill:currentColor}
.bk .bk-scl{fill:var(--bk-w)}.bk .bk-rim{fill:none;stroke:var(--bk-o2);stroke-width:2.6}
.bk .bk-iris{fill:var(--bk-o)}.bk .bk-pupil{fill:var(--bk-d)}.bk .bk-hl{fill:var(--bk-hl)}
.bk .bk-hap{display:none;fill:none;stroke:var(--bk-d);stroke-width:3.6;stroke-linecap:round}
.bk .bk-all,.bk .bk-pup,.bk .bk-eye{transform-box:view-box}
.bk .bk-pup{transition:transform .35s ease}
.bk .bk-all{transform-origin:50px 110px}
.bk .bk-lid{fill:var(--bk-o2);transform-box:fill-box;transform-origin:50% 0;transform:scaleY(0);animation:bk-blink 4.8s infinite}
.bk .bk-pup{animation:bk-look 7s ease-in-out infinite}
@keyframes bk-blink{0%,90%,100%{transform:scaleY(0)}93%,94.5%{transform:scaleY(1)}}
@keyframes bk-look{0%,8%,100%{transform:translate(0,0)}20%,36%{transform:translate(-5px,0)}52%,70%{transform:translate(5px,0)}84%{transform:translate(0,0)}}
.bk[data-m=point] .bk-pup{animation:none;transform:translate(5px,-1px)}
.bk[data-m=point] .bk-ip{display:inline}
.bk[data-m=happy] .bk-pup{display:none}.bk[data-m=happy] .bk-hap{display:inline}.bk[data-m=happy] .bk-lid{animation:none}.bk[data-m=happy] .bk-ih{display:inline}
.bk[data-m=think] .bk-pup{animation:none;transform:translate(-4px,-5px)}.bk[data-m=think] .bk-it{display:inline}
.bk[data-m=think] .bk-it circle{animation:bk-dot 1.2s infinite}.bk[data-m=think] .bk-it circle:nth-child(2){animation-delay:.2s}.bk[data-m=think] .bk-it circle:nth-child(3){animation-delay:.4s}
@keyframes bk-dot{0%,60%,100%{opacity:.25}30%{opacity:1}}
.bk.hop .bk-all{animation:bk-hop .75s ease-out}
@keyframes bk-hop{0%{transform:translateY(0) scale(1,1)}15%{transform:translateY(0) scale(1.08,.9)}40%{transform:translateY(-8px) scale(.95,1.06)}62%{transform:translateY(0) scale(1.06,.93)}80%{transform:translateY(-2px) scale(1,1)}100%{transform:translateY(0) scale(1,1)}}
.bk.talk .bk-eye{animation:bk-talk .32s ease-in-out 4}
.bk .bk-eye{transform-origin:50px 80px}
@keyframes bk-talk{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
.bk .bk-bub{position:absolute;left:63.54%;top:-57.2%;width:68.75%;height:auto;z-index:3;pointer-events:none;opacity:0;transform:scale(.8);transform-origin:4.5% 95.7%;transition:opacity .3s ease,transform .3s ease;color:var(--txt,#e8eef5)}
.bk.say .bk-bub{opacity:1;transform:scale(1);transition:opacity .2s ease,transform .2s ease}
.bk .bk-bb{fill:var(--bg,#0b1016);stroke:var(--line,#2a3646);stroke-width:1.4;stroke-linejoin:round}
body.light .bk .bk-bb{fill:var(--panel2,#f3f5f8)}
html.sxnight .bk .bk-bb{fill:#120202;stroke:#5a0f0a}html.sxnight .bk .bk-bub{color:#7d1f1a}
@media (prefers-reduced-motion:reduce){.bk *,.bk.hop .bk-all,.bk.talk .bk-eye{animation:none!important;transition:none!important}}
.bk-row{display:flex;gap:10px;align-items:flex-start;margin:6px 0 4px}
.bk-say{position:relative;flex:1;min-width:0;background:var(--bg,#0b1016);border:1px solid var(--line,#2a3646);border-radius:14px;padding:9px 12px;box-sizing:border-box}
body.light .bk-say{background:var(--panel2,#f3f5f8)}
.bk-say::before{content:"";position:absolute;left:-8px;top:18px;width:14px;height:14px;background:inherit;border-left:1px solid var(--line,#2a3646);border-bottom:1px solid var(--line,#2a3646);transform:rotate(45deg);border-radius:0 0 0 3px}
.bk-say>b{display:block;font-size:16px;margin:0 0 3px}.bk-say>p{margin:0 0 4px!important;line-height:1.45}.bk-say>p:last-child{margin-bottom:0!important}
.bk-say .bk-hi{color:var(--txt,#e8eef5);font-weight:600}
.g2m .bk-row h2{margin:0 0 4px;font-size:18px}
#g2-bub.bk-on{width:min(380px,calc(100vw - 24px))}
#g2-bub.bk-on .bk-row{margin:0 0 10px}#g2-bub.bk-on .bk-say>b{font-size:15px}
@media (max-width:420px){.bk{width:46px}.bk-row{gap:8px}}
"""

BLINKI_JS = r"""
(function () {                                    // 589: Blinki - the little figure of the guide and the tours
  if (window.MWBlinki) return;
  const K = window.MW_BK || {on: true, tx: {}, svg: ""};
  let n = 0, on = !!K.on;
  const st = document.createElement("style"); st.textContent = K.css || ""; (document.head || document.documentElement).appendChild(st);
  const t = k => (K.tx || {})[k] || k;
  function make(mood) {
    const w = document.createElement("div"); w.className = "bk"; w.dataset.m = mood || "normal"; w.setAttribute("aria-hidden", "true");
    w.innerHTML = String(K.svg || "").split("__I__").join("x" + (++n) + "_" + Math.random().toString(36).slice(2, 7)) + String(K.bub || ""); return w;
  }
  const again = (el, cls, ms) => { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); clearTimeout(el["_" + cls]); el["_" + cls] = setTimeout(() => el.classList.remove(cls), ms); };
  // a new mood shows its sign for ~2 s in the small bubble (class «say»); the same mood again = no bubble
  const mood = (el, m) => { if (!el) return; m = m || "normal"; if (el.dataset.m === m) return; el.dataset.m = m; again(el, "say", 2000); };
  const hop = el => again(el, "hop", 800), talk = el => again(el, "talk", 1350);
  function happyHop(el, after) { mood(el, "happy"); hop(el); setTimeout(() => mood(el, after || "point"), 1100); }
  // a row: Blinki + a speech bubble with the title (b or h2) and the texts (strings or nodes)
  function row(m, title, texts, h2) {
    const r = document.createElement("div"); r.className = "bk-row"; const f = make(m); const s = document.createElement("div"); s.className = "bk-say";
    if (title) { const b = document.createElement(h2 ? "h2" : "b"); b.textContent = title; s.appendChild(b); }
    (texts || []).forEach(x => { if (x == null || x === "") return; if (typeof x === "string") { const p = document.createElement("p"); p.textContent = x; s.appendChild(p); } else s.appendChild(x); });
    r.append(f, s); r.fig = f; talk(f); return r;
  }
  const seenHi = () => { try { return localStorage.getItem("mw-bk-hi") === "1"; } catch (e) { return false; } };
  const markHi = () => { try { localStorage.setItem("mw-bk-hi", "1"); } catch (e) {} };
  window.MWBlinki = {on: () => on, set: v => { on = !!v; }, make, mood, hop, talk, happyHop, row, t, seenHi, markHi};
})();
"""


def blinki_js(L):
    data = {"on": bool(CFG.get("blinki_on", True)), "tx": {s: tr(s, L) for s in BLINKI_TX}, "svg": BLINKI_SVG, "bub": BLINKI_BUB, "css": BLINKI_CSS}
    return "window.MW_BK=" + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";\n" + BLINKI_JS


_g2_js_plain = g2_js


def _g2_js_blinki(L):
    """the script /g2/ui.js: Blinki first (window.MWBlinki), then the guide / tours (516)"""
    return blinki_js(L) + _g2_js_plain(L)


# wraps: g2_js
g2_js = _g2_js_blinki


# ---- the window: the same figure as a small PNG, drawn with cv2 (no SVG library needed) --------------------------------
_BLINKI_TK = {}


def _bk_hex(c, d=(232, 238, 245)):
    try:
        c = str(c).lstrip("#")
        return (int(c[4:6], 16), int(c[2:4], 16), int(c[0:2], 16))           # BGR for cv2
    except (ValueError, IndexError):
        return d[::-1]


def blinki_png(height=72, mood="normal", line="#e8eef5", red=False):
    """Blinki as PNG bytes (RGBA, transparent background). mood: normal / point / happy / think (in the eye only: the
    window shows no fan and no mood bubble). Old coordinates (100 x 112), cut out: x 26 ... 74, y 59 ... 111"""
    S = 8                                                    # draw 8 x bigger, then scale down (smooth edges)
    X0, Y0, W, H = 26, 59, 48, 52
    k = height / float(H) * S
    w, h = max(8, int(round(W * k))), max(8, int(round(H * k)))
    O, O2, WH, DK = ((14, 22, 122), (10, 15, 90), (6, 6, 42), (0, 0, 0)) if red else ((67, 159, 255), (12, 89, 232), (255, 255, 255), (20, 14, 10))
    rgb = np.zeros((h, w, 3), np.float32); a = np.zeros((h, w), np.float32)

    def P(x, y):
        return [int(round((x - X0) * k)), int(round((y - Y0) * k))]

    def put(mask, col, alpha=1.0):
        m = (mask > 0).astype(np.float32) * (alpha if np.isscalar(alpha) else alpha)
        for i in range(3):
            rgb[..., i] = rgb[..., i] * (1 - m) + col[i] * m
        a[:] = a * (1 - m) + m
    for fx in (39, 61):                                      # feet
        m = np.zeros((h, w), np.uint8); cv2.ellipse(m, tuple(P(fx, 105.5)), (int(7.5 * k), int(3.8 * k)), 0, 0, 360, 255, -1); put(m, O2)
    m = np.zeros((h, w), np.uint8); cv2.circle(m, tuple(P(50, 80)), int(17 * k), 255, -1); put(m, WH)   # the eye
    if mood == "happy":
        m = np.zeros((h, w), np.uint8)
        q = [(40.5 + 19 * t_, 83.5 - 25 * t_ * (1 - t_)) for t_ in np.linspace(0, 1, 16)]
        cv2.polylines(m, [np.array([P(x, y) for x, y in q], np.int32)], False, 255, max(1, int(3.6 * k)), cv2.LINE_AA); put(m, DK)
    else:
        px, py = {"point": (5, -1), "think": (-4, -5)}.get(mood, (0, 0))
        for r_, col in ((10.5, O), (5.2, DK)):
            m = np.zeros((h, w), np.uint8); cv2.circle(m, tuple(P(50 + px, 80 + py)), int(r_ * k), 255, -1)
            put(m, col)
        if not red:
            m = np.zeros((h, w), np.uint8); cv2.circle(m, tuple(P(53.2 + px, 76.6 + py)), int(2 * k), 255, -1); put(m, (255, 255, 255))
    m = np.zeros((h, w), np.uint8); cv2.circle(m, tuple(P(50, 80)), int(17 * k), 255, max(1, int(2.6 * k)), cv2.LINE_AA); put(m, O2)
    pm = rgb                                                 # rgb is premultiplied: scale down without dark edges
    tw, th = int(round(W * height / float(H))), int(height)
    pm = cv2.resize(pm, (tw, th), interpolation=cv2.INTER_AREA); a2 = cv2.resize(a, (tw, th), interpolation=cv2.INTER_AREA)
    out = np.dstack([np.clip(pm / np.maximum(a2[..., None], 1e-4), 0, 255), np.clip(a2 * 255, 0, 255)]).astype(np.uint8)
    ok, buf = cv2.imencode(".png", out)
    return buf.tobytes() if ok else b""


def blinki_tk_image(height=64, mood="normal"):
    """a tk.PhotoImage of Blinki in the colours of the window (cached); None when off or not possible"""
    if not CFG.get("blinki_on", True):
        return None
    try:
        red = tk_theme_step() == "red"
    except Exception:
        red = False
    key = (height, mood, C.get("txt"), red)
    if key not in _BLINKI_TK:
        try:
            import base64
            _BLINKI_TK[key] = tk.PhotoImage(data=base64.b64encode(blinki_png(height, mood, C.get("txt") or "#e8eef5", red)).decode("ascii"))
        except Exception:
            _BLINKI_TK[key] = None
    return _BLINKI_TK[key]


def blinki_tk_label(parent, height=64, mood="normal", bg=None):
    """a label with Blinki (or None when it is switched off)"""
    img = blinki_tk_image(height, mood)
    if img is None:
        return None
    lb = tk.Label(parent, image=img, bg=bg or parent.cget("bg"), bd=0, highlightthickness=0)
    lb.image = img
    return lb


def blinki_selftest():
    for md in ("normal", "point", "happy", "think"):
        png = blinki_png(64, md)
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 300, "Blinki PNG " + md
        im = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
        assert im is not None and im.shape[2] == 4 and im[0, 0, 3] == 0 and im[int(im.shape[0] * 0.40), im.shape[1] // 2, 3] > 200, "Blinki: transparent + eye"
        assert abs(im.shape[1] / float(im.shape[0]) - 48 / 52.0) < 0.05, "Blinki: the size without the fan"
    js = _g2_js_blinki("de")
    assert js.index("window.MWBlinki") < js.index("function g2()") and "Hallo, ich bin Blinki" in js and "__I__" in js
    assert "bk-fan" not in BLINKI_SVG and "A64 64" not in BLINKI_SVG and "bk-bub" in js and '"say", 2000' in js, "Blinki: no fan, mood bubble"
    assert "MWBlinki" in G2_JS and "blinki_on" in DEFAULTS and tr("Show Blinki", "fr") != "Show Blinki"
    return True


SELFTEST_EXTRA.append(("Blinki (guide figure: web script, window picture)", blinki_selftest))


def blinki_tk_say(parent, mood, title, text="", bg=None):
    """window: Blinki and its words (title bold, text below) in one row; False when Blinki is off (then the caller writes the title)"""
    bg = bg or parent.cget("bg")
    try:
        fr = tk.Frame(parent, bg=bg)
        lb = blinki_tk_label(fr, 60, mood, bg)
        if lb is None:
            fr.destroy(); return False
        lb.pack(side="left", anchor="n", padx=(0, 10))
        tf = tk.Frame(fr, bg=C["panel"], padx=10, pady=6, highlightthickness=1, highlightbackground=C["line"]); tf.pack(side="left", fill="x", expand=True, anchor="n")
        tk.Label(tf, text=title, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 12, "bold"), anchor="w", justify="left", wraplength=400).pack(fill="x")
        if text:
            tk.Label(tf, text=text, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w", justify="left", wraplength=400).pack(fill="x", pady=(2, 0))
        fr.pack(fill="x", pady=(6, 4))
        return True
    except Exception:
        return False
