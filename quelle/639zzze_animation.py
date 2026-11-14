#@ MoveEye – Teil 639zzze: Animationen (Besitzer 2026-11, leicht, nur CSS / wenige Zeilen) und der CPU-Chip im Live-Bild. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer: «Animationen, alles leicht, billig für Chromium auf dem Pi, aus bei ‹Bewegung reduzieren› und ruhig im Rotlicht»:
#   1. Bewachen: der Schutz-Chip (#b-arm, die Statuszeile am Handy) hat einen Punkt, der langsam atmet (3 s, nur Deckkraft / Schein)
#   2. Bewegung erkannt: der Zonen-Rahmen im Bild leuchtet einmal kurz auf; die Rahmen um Mensch / Tier / Fahrzeug / Wärme
#      blenden ein statt aufzuspringen (im Bild selbst, 410: anim_box / anim_flash - nur das kleine Stück um den Rahmen
#      wird gemischt, 0.4 s, danach wie bisher; aus bei CFG reduce_motion = on)
#   3. Kopf-Kompass im Live-Bild: ein kleiner Pfeil dreht sich weich mit dem Kopf (Schwenk; servo_range), nur mit Kopf
#   4. Warten auf das Bild: das Auge aus dem Logo blinzelt statt der Sanduhr (der Text darunter bleibt; echte Fehler wie bisher)
#   5. Verlauf: neue Aufnahmen gleiten oben herein (alle 15 s nachgefragt, nur sichtbar, nur «Neueste zuerst»), die Zahl im
#      Chip «N Aufnahmen» hüpft kurz
#   6. Reiterwechsel: der Inhalt blendet sanft ein (180 ms)
#   Das Logo-Animation (144) bleibt wie sie ist.
# CPU-Chip: oben rechts im Live-Bild «CPU 42 % · 61 °C», halbdurchsichtig, alle 2 s neu (aus STATE cpu / cpu_temp, die der
# Systemwächter 100 schon misst - kein neuer Faden, keine neue Adresse; Gäste: /g/<token>/state hat jetzt cpu / cpu_temp);
# orange ab 70 % / 70 °C, rot ab 85 % / 80 °C. Sind die Knöpfe im Bild sichtbar (639zzj) oder das kleine Bild der drei
# Ansichten (639zv), rutscht der Chip nach unten rechts. Fenster: ein kleines Etikett oben rechts im Bild (570).
# ----------------------------------------------------------------------------
_HX_ANIM = {
    "Processor load and temperature": ("Prozessor-Last und Temperatur", "Charge et température du processeur",
                                       "Carico e temperatura del processore", "Chargia e temperatura dal processur"),
    "Head direction": ("Richtung des Kopfs", "Direction de la tête", "Direzione della testa", "Direcziun dal chau"),
    "Picture is coming …": ("Bild kommt …", "L’image arrive …", "L’immagine arriva …", "Il maletg vegn …"),
}
for _k, _v in _HX_ANIM.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

CPU_WARN = (70, 70)                 # % / °C: orange from here
CPU_HOT = (85, 80)                  # % / °C: red from here

# the eye of the logo (ring + pupil, colours of the wordmark 144) - blinks while the picture is on its way
_EYE_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="20" fill="none" stroke="#ff9f43" stroke-width="9"/>'
            '<circle cx="32" cy="32" r="8.5" fill="#e8eef5"/></svg>')
ANIM_EYE_URI = "data:image/svg+xml," + _EYE_SVG.replace("<", "%3C").replace(">", "%3E").replace("#", "%23").replace('"', "'")

ANIM_CSS = r"""<style id="anim-css">
/* 639zzze: small animations - one property each (opacity / transform), off with «reduce motion» and in the red light view */
@keyframes mwBreath{0%,100%{opacity:.45;box-shadow:0 0 0 0 rgba(63,207,107,.0)}50%{opacity:1;box-shadow:0 0 0 4px rgba(63,207,107,.22)}}
@keyframes mwEye{0%,42%,50%,100%{transform:scaleY(1)}45%,47%{transform:scaleY(.08)}}
@keyframes mwSlideIn{from{opacity:0;transform:translateY(-14px)}to{opacity:1;transform:none}}
@keyframes mwPop{0%{transform:scale(1)}40%{transform:scale(1.18)}100%{transform:scale(1)}}
@keyframes mwPageIn{from{opacity:0;transform:translateY(6px)}}
/* 1. guarding: a slowly breathing dot in the protection chip */
#b-arm.guard::before,.mwb-sum .mws-st.guard::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--grn);
  margin-right:6px;vertical-align:1px;animation:mwBreath 3s ease-in-out infinite}
/* 4. waiting for the picture: the eye of the logo blinks (the text below stays) */
.vwrap.vlost::after{content:""!important;background:url("__EYE__") center/64px 64px no-repeat;animation:mwEye 3.2s ease-in-out infinite!important;
  transform-origin:50% 50%}
/* 3. head compass + CPU chip, inside the live picture */
.lv-cpu{position:absolute;top:8px;right:8px;z-index:4;padding:3px 9px;border-radius:999px;background:rgba(0,0,0,.5);color:#fff;
  font:600 12px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,"DejaVu Sans",sans-serif;white-space:nowrap;pointer-events:none;
  -webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px);font-variant-numeric:tabular-nums;transition:opacity .2s}
.lv-cpu[hidden]{display:none}
.lv-cpu.warn{background:rgba(245,154,74,.88);color:#111}.lv-cpu.hot{background:rgba(255,77,77,.92);color:#fff}
.lv-comp{position:absolute;right:8px;bottom:8px;z-index:4;width:34px;height:34px;border-radius:50%;background:rgba(0,0,0,.5);color:#fff;
  display:flex;align-items:center;justify-content:center;pointer-events:none;-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.lv-comp[hidden]{display:none}
.lv-comp svg{width:24px;height:24px;transition:transform .6s cubic-bezier(.3,.7,.3,1);fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.lv-comp svg .tip{fill:#ff9f43;stroke:#ff9f43}
body.lv-nohead .lv-comp{display:none}
/* the buttons in the picture are shown (tap / mouse, 639zzj) or the small picture of the three views (639zv): the chip goes
   down to the right, next to the compass - it never lies on the buttons, the magnifier or the small picture */
body.lvc-show .lv-cpu,.vwrap:has(#v3-mini:not([hidden])) .lv-cpu,.vwrap:has(#vo-lupe.on) .lv-cpu{top:auto;bottom:8px;right:50px}
body.lv-nohead.lvc-show .lv-cpu,body.lv-nohead .vwrap:has(#v3-mini:not([hidden])) .lv-cpu{right:8px}
/* 5. history: new recordings slide in, the count hops */
#grid>.mw-new{animation:mwSlideIn .35s ease-out both}
.badge.mw-pop{animation:mwPop .45s ease-out}
/* 6. a new tab: the content comes in gently (no fill afterwards - fixed menus inside keep their place) */
body:has(nav.nav) main{animation:mwPageIn .18s ease-out backwards}
/* off: «reduce motion» (system or the switch of MoveEye) and the red light view (motion would disturb the eyes in the dark) */
@media (prefers-reduced-motion:reduce){#b-arm.guard::before,.mwb-sum .mws-st.guard::before,.vwrap.vlost::after,#grid>.mw-new,.badge.mw-pop,
  body:has(nav.nav) main{animation:none!important}.lv-comp svg,.lv-cpu{transition:none}}
html.mwrm #b-arm.guard::before,html.mwrm .mwb-sum .mws-st.guard::before,html.mwrm .vwrap.vlost::after,html.mwrm #grid>.mw-new,html.mwrm .badge.mw-pop,
html.mwrm body:has(nav.nav) main,html.sxnight #b-arm.guard::before,html.sxnight .mwb-sum .mws-st.guard::before,html.sxnight .vwrap.vlost::after,
html.sxnight #grid>.mw-new,html.sxnight .badge.mw-pop,html.sxnight body:has(nav.nav) main{animation:none!important}
html.mwrm .lv-comp svg,html.mwrm .lv-cpu{transition:none}
html.sxnight #b-arm.guard::before,html.sxnight .mwb-sum .mws-st.guard::before{opacity:.8}
</style>""".replace("__EYE__", ANIM_EYE_URI)

ANIM_TX_KEYS = tuple(_HX_ANIM)

ANIM_JS = r"""<script>
(function () {
  if (window.mwAnim) return;
  const TX = window.ANIM_TX || {};
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "de"; } catch (e) { return "de"; } };
  const tr = k => ((TX[L()] || {})[k]) || k;
  const W = window.ANIM_LIM || {warn: [70, 70], hot: [85, 80]};
  let chip = null, comp = null, lastCpu = 0;
  function els() {
    const box = document.querySelector("#vcard .vwrap"); if (!box) return false;
    if (!chip || !chip.isConnected) { chip = document.createElement("div"); chip.id = "lv-cpu"; chip.className = "lv-cpu"; chip.hidden = true;
      chip.setAttribute("role", "status"); box.appendChild(chip); }
    if (!comp || !comp.isConnected) { comp = document.createElement("div"); comp.id = "lv-comp"; comp.className = "lv-comp"; comp.hidden = true;
      comp.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9.5" opacity=".45"/><path class="tip" d="M12 4.5l3 7.5h-6z"/><path d="M12 12v6"/></svg>';
      box.appendChild(comp); }
    chip.title = tr("Processor load and temperature"); comp.title = tr("Head direction"); comp.setAttribute("aria-label", comp.title);
    return true;
  }
  // the CPU chip: «CPU 42 % · 61 °C», at most every 2 s
  function cpuPaint(s, force) {
    const now = Date.now(); if (!force && now - lastCpu < 1900) return; lastCpu = now;
    if (!els()) return;
    const c = typeof s.cpu === "number" ? s.cpu : null, tt = typeof s.cpu_temp === "number" ? s.cpu_temp : null;
    if (c === null && tt === null) { chip.hidden = true; return; }
    chip.hidden = false; chip.dataset.t = String(now);           // when it was painted last (tests: every 2 s)
    chip.textContent = "CPU " + (c === null ? "–" : Math.round(c) + " %") + (tt === null ? "" : " · " + Math.round(tt) + " °C");
    const hot = (c !== null && c >= W.hot[0]) || (tt !== null && tt >= W.hot[1]), warn = !hot && ((c !== null && c >= W.warn[0]) || (tt !== null && tt >= W.warn[1]));
    chip.classList.toggle("hot", hot); chip.classList.toggle("warn", warn);
    chip.setAttribute("aria-label", tr("Processor load and temperature") + ": " + chip.textContent);
  }
  // the compass: the arrow turns with the pan of the head (0 % = left, 100 % = right, over the servo range)
  function compPaint(c) {
    if (!els()) return;
    const pan = typeof c.pan === "number" ? c.pan : null; if (pan === null) { comp.hidden = true; return; }
    const range = typeof c.servo_range === "number" && c.servo_range > 0 ? c.servo_range : 180;
    comp.hidden = false;
    const a = Math.max(-180, Math.min(180, (pan - 50) / 100 * range));
    comp.querySelector("svg").style.transform = "rotate(" + a.toFixed(1) + "deg)";
  }
  // one call per poll of the page (530 refresh); the guest page calls it with its own small state
  window.mwAnim = function (j) {
    try { const s = (j && j.state) || {}, c = (j && j.cfg) || {};
      cpuPaint(s); if (j && j.cfg) compPaint(c); } catch (e) {}
  };
  window.mwAnim.chip = () => chip; window.mwAnim.comp = () => comp;
})();
</script>"""


def anim_tx():
    out = {"de": {k: DE.get(k, k) for k in ANIM_TX_KEYS}}
    for L in ("fr", "it", "rm"):
        out[L] = {k: TRX[L].get(k) or k for k in ANIM_TX_KEYS}
    return out


_render_page_639zzze = render_page


# wraps: render_page
def render_page(page, active):                                 # + 639zzze: the animations and the CPU chip on the pages with tabs
    out = _render_page_639zzze(page, active)
    if '<nav class="nav">' not in out or "</head>" not in out:
        return out
    out = out.replace("</head>", ANIM_CSS + "</head>", 1)
    i = out.rfind("</body>")
    tag = ("<script>window.ANIM_TX=" + json.dumps(anim_tx(), ensure_ascii=False).replace("</", "<\\/") + ";window.ANIM_LIM="
           + json.dumps({"warn": list(CPU_WARN), "hot": list(CPU_HOT)}) + ";</script>" + ANIM_JS)
    return out[:i] + tag + out[i:] if i >= 0 else out + tag


# ---- 5. history: new recordings slide in (the page asks every 15 s while it is seen; only «newest first», nothing selected) ------
REC_PAGE = REC_PAGE.replace("</body>", r"""<script>
(function () {                                              // 639zzze
  let busy = false;
  const pop = b => { if (!b) return; b.classList.remove("mw-pop"); void b.offsetWidth; b.classList.add("mw-pop"); };
  async function newer() {
    if (busy || document.hidden || typeof F === "undefined" || F.sort !== "new" || selecting || !document.getElementById("modal").hidden) return;
    busy = true;
    try {
      const p = new URLSearchParams(); Object.entries(F).forEach(([k, v]) => { if (v) p.set(k, v); }); p.set("offset", 0); p.set("limit", 12);
      const j = await (await fetch("/api/recordings?" + p, {cache: "no-store"})).json();
      const have = new Set(items.map(x => x.name)), add = (j.items || []).filter(x => !have.has(x.name));
      if (add.length) {
        const g = document.getElementById("grid");
        add.slice().reverse().forEach(it => { items.unshift(it); const c = card(it); c.classList.add("mw-new"); g.insertBefore(c, g.firstChild); });
        const b = document.getElementById("b-count"); if (b && j.disk) { b.textContent = j.disk.files + " " + t("recordings"); pop(b); }
        const e = document.getElementById("empty"); if (e) e.hidden = true;
      }
    } catch (e) {}
    busy = false;
  }
  setInterval(newer, 15000);
})();
</script></body>""", 1)


# ---- the picture (410): boxes fade in, the zone frame lights up once when movement starts ---------------------------------------------
ANIM = {"seen": {}, "mv": False, "mv_end": 0.0, "flash_until": 0.0}
ANIM_FADE_S = 0.4
ANIM_FLASH_S = 0.35


def anim_on():
    return str(CFG.get("reduce_motion") or "auto") != "on"


def anim_motion(moving, t0):
    """movement in the picture now? A start after ≥ 1 s of calm lights the zone frame once"""
    if moving and not ANIM["mv"] and t0 - ANIM["mv_end"] > 1.0 and anim_on():
        ANIM["flash_until"] = t0 + ANIM_FLASH_S
    if not moving and ANIM["mv"]:
        ANIM["mv_end"] = t0
    ANIM["mv"] = bool(moving)


def anim_flash(t0):
    """0 … 1: how strong the zone frame lights up right now (0 = normal)"""
    left = ANIM["flash_until"] - t0
    return max(0.0, min(1.0, left / ANIM_FLASH_S)) if left > 0 else 0.0


def anim_box(frame, key, t0, p1, p2, col, th, label=None, lpos=None, lscale=0.45, lth=1):
    """a rectangle (and its label) that fades in during the first 0.4 s of a new box - only the small piece around it is mixed"""
    seen = ANIM["seen"]
    first = seen.get(key)
    if first is None or t0 - first[1] > 1.5:              # new (or back after 1.5 s): starts again
        first = (t0, t0)
    seen[key] = (first[0], t0)
    if len(seen) > 200:
        for k_ in [k_ for k_, v_ in seen.items() if t0 - v_[1] > 5.0]:
            seen.pop(k_, None)
    a = (t0 - first[0]) / ANIM_FADE_S if anim_on() else 1.0
    if a >= 1.0:
        cv2.rectangle(frame, p1, p2, col, th)
        if label:
            cv2.putText(frame, label, lpos, cv2.FONT_HERSHEY_SIMPLEX, lscale, col, lth, cv2.LINE_AA)
        return
    a = max(0.25, a)
    H_, W_ = frame.shape[:2]
    x0, y0 = max(0, min(p1[0], p2[0]) - th - 2), max(0, min(p1[1], p2[1], lpos[1] - 16 if lpos else p1[1]) - th - 2)
    x1, y1 = min(W_, max(p1[0], p2[0], (lpos[0] + 120) if lpos else 0) + th + 2), min(H_, max(p1[1], p2[1]) + th + 2)
    if x1 <= x0 or y1 <= y0:
        return
    roi = frame[y0:y1, x0:x1]
    ov = roi.copy()
    cv2.rectangle(ov, (p1[0] - x0, p1[1] - y0), (p2[0] - x0, p2[1] - y0), col, th)
    if label:
        cv2.putText(ov, label, (lpos[0] - x0, lpos[1] - y0), cv2.FONT_HERSHEY_SIMPLEX, lscale, col, lth, cv2.LINE_AA)
    cv2.addWeighted(ov, a, roi, 1.0 - a, 0, roi)


def anim_selftest():
    for k in _HX_ANIM:
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), "639zzze: text " + k
    f = np.zeros((120, 160, 3), np.uint8)
    keep = dict(ANIM["seen"]), CFG.get("reduce_motion")
    try:
        CFG["reduce_motion"] = "auto"; ANIM["seen"].clear()
        anim_box(f, "t1", 100.0, (20, 20), (60, 60), (0, 0, 255), 3, "PERSON", (20, 14))
        mid = int(f[20, 40, 2])
        f2 = np.zeros_like(f); anim_box(f2, "t1", 100.5, (20, 20), (60, 60), (0, 0, 255), 3)
        assert 0 < mid < 255 and int(f2[20, 40, 2]) == 255, "639zzze: the box fades in (%d, %d)" % (mid, f2[20, 40, 2])
        CFG["reduce_motion"] = "on"; f3 = np.zeros_like(f); anim_box(f3, "t9", 200.0, (20, 20), (60, 60), (0, 0, 255), 3)
        assert int(f3[20, 40, 2]) == 255, "639zzze: «reduce motion» = no fade"
        CFG["reduce_motion"] = "auto"; ANIM.update(mv=False, mv_end=0.0, flash_until=0.0)
        anim_motion(True, 300.0); assert anim_flash(300.1) > 0 and anim_flash(301.0) == 0, "639zzze: zone flash once"
        anim_motion(True, 300.2); anim_motion(False, 300.3); anim_motion(True, 300.5); assert anim_flash(300.6) == 0, "639zzze: no flash after < 1 s calm"
    finally:
        ANIM["seen"].clear(); ANIM["seen"].update(keep[0]); CFG["reduce_motion"] = keep[1]; ANIM.update(mv=False, flash_until=0.0)
    p = render_page("<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>", "live")
    assert "anim-css" in p and "window.mwAnim" in p and "prefers-reduced-motion" in p and "html.sxnight" in p, "639zzze: css / js"
    assert "mw-new" in REC_PAGE and "mwAnim" in WEB_PAGE and "gAnim(j)" in GUEST_PAGE, "639zzze: hooks (history, live page, guest page)"
    assert anim_cpu_text(42.4, 61.2) == ("CPU 42 % · 61 °C", "") and anim_cpu_text(71, 50)[1] == "warn" and anim_cpu_text(50, 81)[1] == "hot"
    assert anim_cpu_text(None, None) == ("", "") and anim_cpu_text(None, 40)[0] == "CPU – · 40 °C"
    return "boxes fade in, zone frame flashes once, off with «reduce motion»; CPU chip and compass on Live"


SELFTEST_EXTRA.append(("Animations and the CPU chip (639zzze)", anim_selftest))


# ---- the guest page (520): the same CPU chip and the blinking eye while the picture is on its way ------------------------------------
ANIM_GUEST_CSS = (".vwrap{position:relative}.lv-cpu{position:absolute;top:8px;right:8px;z-index:4;padding:3px 9px;border-radius:999px;background:rgba(0,0,0,.5);"
                  "color:#fff;font:600 12px/1.4 system-ui,-apple-system,sans-serif;white-space:nowrap;pointer-events:none;font-variant-numeric:tabular-nums}"
                  ".lv-cpu[hidden]{display:none}.lv-cpu.warn{background:rgba(245,154,74,.88);color:#111}.lv-cpu.hot{background:rgba(255,77,77,.92)}"
                  "@keyframes mwEye{0%,42%,50%,100%{transform:scaleY(1)}45%,47%{transform:scaleY(.08)}}"
                  ".vwrap.vlost::after{content:''!important;background:url(\"" + ANIM_EYE_URI + "\") center/64px 64px no-repeat;animation:mwEye 3.2s ease-in-out infinite}"
                  "@media (prefers-reduced-motion:reduce){.vwrap.vlost::after{animation:none}}")
ANIM_GUEST_JS = ("window.gAnim=function(j){var w=document.querySelector('.vwrap');if(!w)return;var c=document.getElementById('lv-cpu');"
                 "if(!c){c=document.createElement('div');c.id='lv-cpu';c.className='lv-cpu';c.hidden=true;w.appendChild(c);}"
                 "var u=typeof j.cpu==='number'?j.cpu:null,t=typeof j.cpu_temp==='number'?j.cpu_temp:null;if(u===null&&t===null){c.hidden=true;return;}"
                 "c.hidden=false;c.textContent='CPU '+(u===null?'–':Math.round(u)+' %')+(t===null?'':' · '+Math.round(t)+' °C');"
                 "var h=(u!==null&&u>=" + str(CPU_HOT[0]) + ")||(t!==null&&t>=" + str(CPU_HOT[1]) + "),wa=!h&&((u!==null&&u>=" + str(CPU_WARN[0])
                 + ")||(t!==null&&t>=" + str(CPU_WARN[1]) + "));c.classList.toggle('hot',h);c.classList.toggle('warn',wa);};")
if "gAnim" not in GUEST_PAGE and "const j = await r.json();" in GUEST_PAGE:
    GUEST_PAGE = (GUEST_PAGE.replace("</style>", ANIM_GUEST_CSS + "</style>", 1)
                  .replace("const j = await r.json();", "const j = await r.json(); if (window.gAnim) gAnim(j);", 1)
                  .replace("<script>", "<script>" + ANIM_GUEST_JS + "\n", 1))


# ---- the window (Tkinter): a small label «CPU 42 % · 61 °C» top right on the picture, every 2 s -----------------------------------
def _anim_cpu_chip_start(self):
    if getattr(self, "_cpu_chip_job", None) is None:
        self._cpu_chip_job = self.root.after(800, self._anim_cpu_chip_tick)


def anim_cpu_text(c, t):
    """(text, level) of the chip: level "" | "warn" | "hot" (the same limits as the web page)"""
    if c is None and t is None:
        return "", ""
    txt = "CPU " + ("–" if c is None else "%d %%" % round(c)) + ("" if t is None else " · %d °C" % round(t))
    hot = (c is not None and c >= CPU_HOT[0]) or (t is not None and t >= CPU_HOT[1])
    warn = not hot and ((c is not None and c >= CPU_WARN[0]) or (t is not None and t >= CPU_WARN[1]))
    return txt, "hot" if hot else ("warn" if warn else "")


def _anim_cpu_chip_tick(self):
    self._cpu_chip_job = None
    try:
        v = getattr(self, "video", None)
        if v is not None and v.winfo_exists():
            lb = getattr(self, "_cpu_chip_lbl", None)
            if lb is None or not lb.winfo_exists() or str(lb.master) != str(v):
                lb = self._cpu_chip_lbl = tk.Label(v, font=("DejaVu Sans", 9, "bold"), padx=6, pady=1, bd=0)
                Tip(lb, tr("Processor load and temperature"))
            txt, lv = anim_cpu_text(STATE.get("cpu"), STATE.get("cpu_temp"))
            if not txt:
                lb.place_forget()
            else:
                lb.config(text=txt, bg={"hot": "#ff4d4d", "warn": "#f59a4a"}.get(lv, "#1b2330"), fg="#111111" if lv == "warn" else "#ffffff")
                lb.place(relx=1.0, x=-8, y=8, anchor="ne")
    except Exception:
        pass
    try:
        self._cpu_chip_job = self.root.after(2000, self._anim_cpu_chip_tick)
    except Exception:
        self._cpu_chip_job = None


if "App" in globals():
    App._anim_cpu_chip_start = _anim_cpu_chip_start
    App._anim_cpu_chip_tick = _anim_cpu_chip_tick
