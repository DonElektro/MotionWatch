#@ MoveEye – Teil 639s: schneller Zugang zum Entwickler-Bereich – langer Druck (etwa 0,8 s) aufs MoveEye-Logo. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Daniel (1.11.2026, Wahl 2): «schneller Zugriff auf die Entwickler-Werkzeuge, von möglichst überall».
#   * Web: auf jeder Seite mit Kopfzeile (über render_page) - langer Druck aufs Logo (header h1) öffnet Einstellungen → Entwickler
#     (/settings?open=grp:dev, auf der Hauptseite direkt tabOpen). Ist die ganze Kopfzeile ausgeblendet (▴), wirkt der Griff ▾
#     (#hdr-show) gleich. Rückmeldung: das Logo pulsiert während des Haltens, kurzes Vibrieren (navigator.vibrate) beim Auslösen.
#     Auf Touch: kein Kontextmenü, keine Textauswahl, kein iOS-Vorschau-Menü (-webkit-touch-callout) auf dem Logo.
#   * Pi-Fenster: langer Druck auf Logo / Name im Kopf (App._title_box, 570) - Reiter Einstellungen, Gruppe Entwickler offen.
#   * Simulator: devzugang.gd (langer Druck auf Schriftzug / Titel und der Werkzeug-Knopf oben im Bedienfeld).
#   * Nur mit «Entwickler-Bereich» ein (dev_available, 258) UND Besitzer (nacht_may: Rolle admin, nicht im Bedienermodus, 579b).
#     Sonst kommt der Code gar nicht auf die Seite. Der normale Klick bleibt: 7 schnelle Klicks = Murmeltier (510),
#     ein Tipp auf die Versionsnummer = «Über MoveEye» (584). Ein ausgelöster langer Druck schluckt nur den einen Klick danach.

DEVZ_HOLD_MS = 800

# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_DEVZ = {
    'Tip: hold the MoveEye logo (about 1 s) to come here from every page.':
        ('Tipp: Das MoveEye-Logo etwa 1 s gedrückt halten – so kommst du von jeder Seite hierher.',
         'Astuce : maintiens le logo MoveEye (environ 1 s) pour venir ici depuis chaque page.',
         'Suggerimento: tieni premuto il logo MoveEye (circa 1 s) per arrivare qui da ogni pagina.',
         'Tip: tegna smatgà il logo da MoveEye (var 1 s) per vegnir qua da mintga pagina.'),
}
for _k, _v in _HX_DEVZ.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# the hint in Settings → Developer (web 530 devExtras; the main page has its own dictionary)
_DEVZ_A = 'bx.appendChild(el("div", "mut", t("Only for the developer (switch: System → Device & help → Developer area).")));'
if _DEVZ_A in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_DEVZ_A, _DEVZ_A + '\n  bx.appendChild(el("div", "mut", t("Tip: hold the MoveEye logo (about 1 s) to come here from every page.")));', 1)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps({_k: _v[0] for _k, _v in _HX_DEVZ.items()}, ensure_ascii=False)
                            + ");</script></body>", 1)


def devz_ok(role=None):
    """the long press works only with the developer area on and for the owner (admin, not in operator mode)"""
    return bool(dev_available()) and nacht_may(_nacht_role() if role is None else role)


DEVZ_CSS = ("<style id=\"devz-css\">header h1,#hdr-show{-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}"
            "header h1{transform-origin:0 50%}"
            "header h1.devz-hold,#hdr-show.devz-hold{animation:devzp .4s ease-in-out infinite alternate}"
            "header h1.devz-go,#hdr-show.devz-go{animation:devzg .35s ease-out}"
            "@keyframes devzp{from{transform:scale(1);filter:none}to{transform:scale(1.07);filter:drop-shadow(0 0 6px #ff9f43)}}"
            "@keyframes devzg{0%{transform:scale(1.12);filter:drop-shadow(0 0 10px #ff9f43)}100%{transform:scale(1);filter:none}}"
            "@media (prefers-reduced-motion:reduce){header h1.devz-hold,#hdr-show.devz-hold{animation:none;filter:drop-shadow(0 0 6px #ff9f43)}}"
            "</style>")

DEVZ_JS = r"""<script>
(function () {
  if (window._devz) return; window._devz = true;
  const HOLD = __HOLD__;
  function go() {
    if (typeof tabOpen === "function" && document.querySelector('#settings [data-view="grp:dev"]')) { tabOpen("grp:dev"); return; }
    location.href = "/settings?open=grp:dev";
  }
  function arm(elm) {
    if (!elm || elm._devz) return; elm._devz = true;
    let tm = 0, tp = 0, x0 = 0, y0 = 0, holding = false, fired = false;
    const stop = () => { clearTimeout(tm); clearTimeout(tp); holding = false; elm.classList.remove("devz-hold"); };
    elm.addEventListener("pointerdown", e => {
      if (e.button !== 0 || !e.isPrimary) return;
      stop(); fired = false; holding = true; x0 = e.clientX; y0 = e.clientY;
      tp = setTimeout(() => { if (holding) elm.classList.add("devz-hold"); }, 150);     // the logo pulses while it is held
      tm = setTimeout(() => {
        if (!holding) return; stop(); fired = true;
        try { if (navigator.vibrate) navigator.vibrate(25); } catch (er) {}
        elm.classList.remove("devz-go"); void elm.offsetWidth; elm.classList.add("devz-go");
        setTimeout(() => { elm.classList.remove("devz-go"); go(); }, 200);
        setTimeout(() => { fired = false; }, 1500);
      }, HOLD);
    });
    elm.addEventListener("pointermove", e => { if (holding && Math.hypot(e.clientX - x0, e.clientY - y0) > 12) stop(); });
    ["pointerup", "pointercancel", "pointerleave"].forEach(n => elm.addEventListener(n, () => { if (holding) stop(); }));
    // touch: no context menu / callout while held; a right click with the mouse keeps its menu
    elm.addEventListener("contextmenu", e => { if (holding || fired || (e.pointerType && e.pointerType !== "mouse")) e.preventDefault(); });
    elm.addEventListener("selectstart", e => { if (holding) e.preventDefault(); });
    // the click after a long press does nothing (the 7 taps of the little surprise and «About» stay for normal clicks)
    elm.addEventListener("click", e => { if (fired) { fired = false; e.preventDefault(); e.stopImmediatePropagation(); } }, true);
  }
  const start = () => { arm(document.querySelector("header h1")); arm(document.getElementById("hdr-show")); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
  setTimeout(start, 1500);
})();
</script>""".replace("__HOLD__", str(DEVZ_HOLD_MS))


_render_page_before_devz = render_page


# wraps: render_page (after 639o)
def render_page(page, active):
    """+ 639s: long press on the logo = Settings → Developer (only developer area on + owner)"""
    out = _render_page_before_devz(page, active)
    if "<header" not in out or "<h1" not in out:
        return out
    try:
        ok = devz_ok()
    except Exception:
        ok = False
    if not ok:
        return out
    out = out.replace("</head>", DEVZ_CSS + "</head>", 1)
    i = out.rfind("</body>")
    return out[:i] + DEVZ_JS + out[i:] if i >= 0 else out + DEVZ_JS


# the manual (HELP_PAGE of 540): one paragraph in «Tipps & Tricks», German and English
for _a, _b in (('<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>',
                "<p><b>🛠 Schnell zum Entwickler-Bereich:</b> Ist der Entwickler-Bereich eingeschaltet (System → Gerät &amp; Hilfe) und "
                "bist du als Besitzer angemeldet, öffnet ein langer Druck (etwa 1 s) aufs MoveEye-Logo oben links Einstellungen → "
                "Entwickler – auf jeder Seite, im Pi-Fenster und im Simulator (dort auch der Werkzeug-Knopf oben im Bedienfeld). "
                "Ein normaler Klick aufs Logo bleibt wie bisher.</p>"),
               ('<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>',
                "<p><b>🛠 Quick way to the developer area:</b> with the developer area switched on (System → Device &amp; help) and "
                "logged in as the owner, a long press (about 1 s) on the MoveEye logo at the top left opens Settings → Developer – "
                "on every page, in the Pi window and in the simulator (there also the tool button at the top of the panel). "
                "A normal click on the logo stays as before.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


if GUI_OK:                                                # the Pi window: long press on logo / name in the header
    _devz_tk_build_header_base = App._build_header

    def _devz_tk_build_header(self):
        _devz_tk_build_header_base(self)
        tl = getattr(self, "_title_box", None)
        if tl is None:
            return
        try:
            for w_ in tl.winfo_children():
                if isinstance(w_, tk.Label) and str(w_.cget("text")) == APP_VERSION:
                    continue                              # the version: one tap = «About MoveEye» (584) stays
                w_.bind("<ButtonPress-1>", self._devz_press, add="+")
                w_.bind("<ButtonRelease-1>", self._devz_release, add="+")
                w_.bind("<B1-Motion>", self._devz_motion, add="+")
        except Exception:
            pass

    def _devz_press(self, e=None):
        self._devz_release()
        if not devz_ok("admin"):
            return
        self._devz_xy = (getattr(e, "x_root", 0), getattr(e, "y_root", 0))
        self._devz_job = self.root.after(DEVZ_HOLD_MS, self._devz_fire)
        self._devz_n = 0
        self._devz_pulse_job = self.root.after(150, self._devz_pulse)

    def _devz_motion(self, e):
        x0, y0 = getattr(self, "_devz_xy", (0, 0))
        if getattr(self, "_devz_job", None) and abs(e.x_root - x0) + abs(e.y_root - y0) > 14:
            self._devz_release()

    def _devz_paint(self, on):
        lb = getattr(self, "_logo_lbl", None)
        try:
            if lb is not None and lb.winfo_exists():
                lb.config(bg=C["acc"] if on else C["bg"])
        except Exception:
            pass

    def _devz_pulse(self):
        """the logo pulses while it is held (background on / off every 120 ms)"""
        self._devz_n = getattr(self, "_devz_n", 0) + 1
        self._devz_paint(self._devz_n % 2 == 1)
        self._devz_pulse_job = self.root.after(120, self._devz_pulse)

    def _devz_release(self, _e=None):
        for k in ("_devz_job", "_devz_pulse_job"):
            j = getattr(self, k, None)
            if j:
                try:
                    self.root.after_cancel(j)
                except Exception:
                    pass
            setattr(self, k, None)
        self._devz_paint(False)

    def _devz_fire(self):
        self._devz_job = None
        self._devz_release()
        self._devz_paint(True)
        self.root.after(200, lambda: self._devz_open())

    def _devz_open(self):
        """Settings tab, group «Entwickler» and its first part open, then scroll there"""
        self._devz_paint(False)
        self.open_secs.update({"grp:dev", "sub:Developer"})
        self.open_secs.discard("subx:Developer")
        if self.tab != "settings":
            self._tab("settings")
        else:
            self._schedule_rebuild()
        self.root.after(350, self._devz_scroll)

    def _devz_scroll(self):
        try:
            meta = getattr(self, "grp_meta", {}).get("grp:dev")
            cv = getattr(self, "side_canvas", None)
            if not meta or cv is None:
                return
            card = meta[2]
            self.root.update_idletasks()
            h = max(1, card.master.winfo_height())
            cv.yview_moveto(max(0.0, (card.winfo_y() - 8) / h))
        except Exception:
            pass

    # wraps: App._build_header (570)
    App._build_header = _devz_tk_build_header
    for _n in ("_devz_press", "_devz_motion", "_devz_paint", "_devz_pulse", "_devz_release", "_devz_fire", "_devz_open", "_devz_scroll"):
        setattr(App, _n, globals()[_n])


def _devz_selftest():
    keep = {k: CFG.get(k) for k in ("dev_area", "lock_on")}
    pg = "<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>"
    try:
        CFG["dev_area"] = False; CFG["lock_on"] = False
        assert "devz-css" not in render_page(pg, "live"), "639s: long press without the developer area"
        CFG["dev_area"] = True
        p = render_page(pg, "live")
        assert p.count('id="devz-css"') == 1 and p.count("window._devz)") == 1 and "grp:dev" in p, "639s: long press missing / twice"
        assert not devz_ok("view") and not devz_ok("kid") and devz_ok("admin"), "639s: only the owner"
        CFG["lock_on"] = True
        assert not devz_ok("admin") and "devz-css" not in render_page(pg, "live"), "639s: not in operator mode"
        assert "devz-css" not in render_page("<html><head></head><body><main></main></body></html>", "guest"), "639s: page without header"
        assert "Tip: hold the MoveEye logo" in WEB_PAGE and all(TRX[L].get(next(iter(_HX_DEVZ))) for L in ("fr", "it", "rm")), "639s: texts"
        assert "data-view=\"grp:dev\"" in DEVZ_JS or "grp:dev" in DEVZ_JS, "639s: target"
    finally:
        CFG.update(keep)
    return "long press on the logo: developer area + owner only, texts, manual"


SELFTEST_EXTRA.append(("Long press on the logo = developer area (639s)", _devz_selftest))
