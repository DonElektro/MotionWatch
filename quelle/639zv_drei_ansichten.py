#@ MoveEye – Teil 639zv: «Drei Kamera-Ansichten» – Knopf «Ansicht» schaltet das Hauptbild 🎯 Kopf → 🌡 Wärmebild → 🔭 Weitwinkel (lang drücken = Auswahl), kleines Übersichtsbild in der Ecke (antippen = gross / klein tauschen), Rahmen «wohin der Kopf schaut» im Weitwinkelbild; Live-Seite, Controller-Ansicht, Sim-Ansicht und Pi-Fenster. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (07.11.2026, «Drei Kamera-Ansichten»):
#   * Ein Knopf «Ansicht» (Bild-Werkzeug auf der Live-Seite + Schnellschalter «view») schaltet das grosse Bild der Reihe nach:
#       🎯 Kopf       = die Hauptkamera am Kopf (/video_feed, wie bisher)
#       🌡 Wärmebild  = dasselbe Bild mit dem Wärmebild halb durchsichtig darüber - genau der bisherige 🌡-Schalter
#                       (CFG thermal_on, Quelle thermal_source; gilt also für alle Geräte und die Aufnahmen wie bisher)
#       🔭 Weitwinkel = die Übersichtskamera (Zusatzkamera, 440: CFG kopf_ov «Übersicht lenkt den Kopf», sonst die
#                       Weitwinkel-Kamera des Simulators sim:1, 163) über /cam_feed/<n>, mit einem Rahmen, wohin der Kopf
#                       gerade schaut (view3_frame: Kopf-Richtung, kopf_ov_offset bzw. Montage des Simulators, Blickwinkel).
#     Lang drücken (oder Rechtsklick) = kleines Menü mit den drei Ansichten; was fehlt (keine Wärmebildquelle, keine
#     Weitwinkel-Kamera), wird übersprungen und im Menü grau gezeigt. Der 🌡-Schalter bleibt, wie er ist.
#   * Bild im Bild: klein die Weitwinkel-Übersicht in der Ecke (bzw. der Kopf, wenn das Weitwinkelbild gross ist), ein / aus im
#     Menü, pro Gerät gemerkt (localStorage «mw-view3» = WEB_UI_LOCAL; Fenster: CFG tk_live_view view3 / pip3). Antippen = tauschen.
#   * Bildströme (3.55.2, KEEP_JS 510): das grosse Bild bleibt EIN Strom (keepStream.retarget wechselt nur seine Adresse), das
#     kleine Bild holt Einzelbilder (/cam_snap/<n>, ~2 / s) und ist zu, sobald es nicht sichtbar ist (verdeckt, weggescrollt,
#     Sim-Ansicht, anderer Reiter). Pro Gerät also höchstens ein langer Bildstrom.
#   * Controller-Ansicht (538): Knopf «Ansicht» in der Leiste; «⇅ Tauschen» (Select, langes Tippen) tauscht ohne Simulator
#     gross / klein der Kamera-Ansichten. Die Belegung des Controllers (542 / padmap.gd) bleibt: Select = «Bilder / Ansichten
#     tauschen». Sim-Ansicht (639zt): das kleine Kamerabild zeigt die gewählte Ansicht, «⋯ Mehr» hat den Knopf.
#   * Pi-Fenster (570 / 581): derselbe Schnellschalter (lang drücken / Rechtsklick = Menü), Bild im Bild unten links.
# Übersetzungen: unten (_HX_V3, alle 5 Sprachen), Anleitung: Abschnitt «views».
# ----------------------------------------------------------------------------
VIEW3_ORDER = ("head", "thermal", "wide")


def view3_wide_cam():
    """the wide overview camera (an extra camera of 440): «Übersicht lenkt den Kopf» (kopf_ov), else the simulator's wide
    camera sim:1 (when it is built in) - or None"""
    sp = str(CFG.get("kopf_ov") or "")
    c = next((x for x in CAMS if sp and str(x.spec) == sp), None)
    if c is None:
        try:
            sc = weit_sim_cam()
            if sc and "mount" in sc and not weit_missing():
                c = next((x for x in CAMS if str(x.spec) == "sim:1"), None)
        except Exception:
            c = None
    return c


def view3_frame_calc(head_pan, head_tilt, centre, ov_tilt, hf, vf, of, ofv):
    """where the head picture lies in the wide picture: centre x / y and size w / h (0..1 of the wide picture), or None when
    the head looks outside it. Degrees: + = right / up; centre = where the middle of the wide picture looks (pan)."""
    try:
        of = max(10.0, float(of)); ofv = max(5.0, float(ofv))
        dx = (float(head_pan) - float(centre) + 180.0) % 360.0 - 180.0
        cx = 0.5 + dx / of; w = min(1.5, float(hf) / of)
        cy = 0.5 - (float(head_tilt) - float(ov_tilt)) / ofv; h = min(1.5, float(vf) / ofv)
    except (TypeError, ValueError):
        return None
    if cx + w / 2 <= 0.0 or cx - w / 2 >= 1.0 or cy + h / 2 <= 0.0 or cy - h / 2 >= 1.0:
        return None
    return {"x": round(cx, 3), "y": round(cy, 3), "w": round(w, 3), "h": round(h, 3)}


def view3_frame(c=None):
    """the frame «where the head looks» in the picture of the wide camera c (see view3_frame_calc)"""
    c = c or view3_wide_cam()
    if c is None:
        return None
    try:
        spec = str(c.spec)
        hf, vf = cam_fov()
        of = kopf_ov_fov() if spec == str(CFG.get("kopf_ov") or "") else cam_fov_h(spec)
        ofv = cam_fov_hv(spec)[1]
        head = weit_head_deg()
        h = SIM.get("head") if CFG.get("sim_on") else None
        ht = float(h[1]) if isinstance(h, list) and len(h) >= 2 else servo_pos_deg()[1]
        sc = weit_sim_cam() if spec == "sim:1" else None
        centre, ot = float(CFG.get("kopf_ov_offset") or 0.0), 0.0
        if sc and str(sc.get("mount") or "scene") in WEIT_DEVICE_MOUNTS:
            centre = float(sc.get("yaw_offset") or 0.0) + (head if sc.get("on_head") else 0.0)
            ot = float(sc.get("tilt_deg") or 0.0) + (ht if sc.get("tilt_follow") else 0.0)
            of = float(sc.get("fov_h") or of); ofv = float(sc.get("fov_v") or ofv)
        elif sc:
            ot = float(sc.get("tilt_deg") or 0.0)
        return view3_frame_calc(head, ht, centre, ot, hf, vf, of, ofv)
    except Exception:
        return None


def view3_info():
    """for the pages (in /api/state → extra[0].view3): the wide camera (number, name, connected), thermal source, frame"""
    c = view3_wide_cam()
    return {"wide": c.idx if c else None, "wide_label": c.label if c else "", "wide_ok": bool(c and c.status == "connected"),
            "thermal": bool(CFG.get("thermal_source")), "frame": view3_frame(c) if c else None}


_cams_status_v3 = cams_status


def cams_status(watch=None):                              # + 639zv: the main camera tells the pages about the three views
    out = _cams_status_v3(watch)
    try:
        out[0]["view3"] = view3_info()
    except Exception:
        pass
    return out


_HX_V3 = {   # English (key): Deutsch, Français, Italiano, Rumantsch
    "Camera view": ("Ansicht", "Vue", "Vista", "Vista"),
    "Head view": ("Kopf", "Tête", "Testa", "Chau"),
    "Thermal view": ("Wärmebild", "Image thermique", "Immagine termica", "Maletg termic"),
    "Wide view": ("Weitwinkel", "Grand angle", "Grandangolo", "Grond angul"),
    "Main picture": ("Hauptbild", "Image principale", "Immagine principale", "Maletg principal"),
    "Camera view: head → thermal → wide angle (hold: choose)": ("Ansicht: Kopf → Wärmebild → Weitwinkel (halten: wählen)",
                                                               "Vue : tête → image thermique → grand angle (maintenir : choisir)",
                                                               "Vista: testa → immagine termica → grandangolo (tenere premuto: scegliere)",
                                                               "Vista: chau → maletg termic → grond angul (tegnair: tscherner)"),
    "The camera of the head": ("Die Kamera am Kopf", "La caméra de la tête", "La telecamera della testa", "La camera dal chau"),
    "Thermal picture half transparent over the head picture": ("Wärmebild halb durchsichtig über dem Kopfbild",
                                                               "Image thermique semi-transparente sur l’image de la tête",
                                                               "Immagine termica semitrasparente sopra l’immagine della testa",
                                                               "Maletg termic mez transparent sur il maletg dal chau"),
    "The overview camera - the frame shows where the head looks": ("Die Übersichtskamera – der Rahmen zeigt, wohin der Kopf schaut",
                                                                   "La caméra d’ensemble – le cadre montre où regarde la tête",
                                                                   "La telecamera panoramica – il riquadro mostra dove guarda la testa",
                                                                   "La camera da survista – il rom mussa nua ch’il chau guarda"),
    "No thermal camera chosen": ("Keine Wärmebildkamera gewählt", "Aucune caméra thermique choisie", "Nessuna termocamera scelta",
                                 "Nagina camera termica tschernida"),
    "No wide-angle camera (overview)": ("Keine Weitwinkel-Kamera (Übersicht)", "Pas de caméra grand angle (vue d’ensemble)",
                                        "Nessuna telecamera grandangolare (panoramica)", "Nagina camera da grond angul (survista)"),
    "Small overview picture": ("Kleines Übersichtsbild", "Petite image d’ensemble", "Piccola immagine panoramica", "Pitschen maletg da survista"),
    "Tap the small picture: swap big and small": ("Kleines Bild antippen: gross und klein tauschen",
                                                  "Toucher la petite image : échanger grande et petite",
                                                  "Tocca l’immagine piccola: scambia grande e piccola",
                                                  "Tutgar il pitschen maletg: barattar grond e pitschen"),
    "Where the head looks": ("Wohin der Kopf schaut", "Où regarde la tête", "Dove guarda la testa", "Nua ch’il chau guarda"),
    "Views swapped": ("Ansichten getauscht", "Vues échangées", "Viste scambiate", "Vistas barattadas"),
}
for _k, _v in _HX_V3.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

VIEW3_JS = r"""
<style id="v3-css">
#v3-mini{position:absolute;z-index:4;left:8px;top:8px;width:min(30%,220px);padding:0;margin:0;border:2px solid rgba(255,255,255,.8);border-radius:8px;overflow:hidden;
  background:#000;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5);touch-action:manipulation;-webkit-tap-highlight-color:transparent;display:block;min-height:0}
#v3-mini[hidden]{display:none}
#v3-mini img{display:block;width:100%;height:auto;min-height:36px;max-height:none;-webkit-user-drag:none;pointer-events:none}
#v3-mini .v3ml{position:absolute;left:4px;bottom:4px;z-index:4;font:700 10px/1 system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.6);padding:3px 5px;border-radius:4px;pointer-events:none}
#pv #v3-mini{top:30px}
.v3ov{position:absolute;pointer-events:none;overflow:hidden;z-index:3}
.v3ov[hidden]{display:none}
.v3fr{position:absolute;border:2px solid #ffd34d;border-radius:3px;box-shadow:0 0 0 1px rgba(0,0,0,.55);box-sizing:border-box}
.v3fr span{position:absolute;left:-2px;top:-2px;font:700 10px/1.2 system-ui,sans-serif;color:#000;background:#ffd34d;padding:1px 4px;border-radius:2px 0 3px 0;white-space:nowrap}
#v3-mini .v3fr{border-width:1.5px}#v3-mini .v3fr span{display:none}
#v3-tag{background:rgba(0,0,0,.55);color:#fff;padding:3px 8px;border-radius:8px;font-size:12px;font-weight:600}
#v3-tag[hidden]{display:none}
#lv-tools #lv-b-cam{font-size:18px;line-height:1}
#v3-menu{position:fixed;z-index:400;min-width:230px;max-width:calc(100vw - 24px);background:var(--panel,#121821);color:var(--txt,#e8eef5);
  border:1px solid var(--line,#2a3442);border-radius:12px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.5);font-family:system-ui,-apple-system,sans-serif}
#v3-menu[hidden]{display:none}
#v3-menu .v3mh{font-size:12px;font-weight:700;opacity:.7;padding:4px 8px 6px}
#v3-menu button{display:flex;width:100%;align-items:center;gap:10px;text-align:left;padding:8px 10px;min-height:46px;border-radius:8px;background:transparent;
  border:0;color:inherit;font:inherit;font-size:15px;cursor:pointer}
#v3-menu button.on{background:var(--acc,#3b8cff);color:#fff}
#v3-menu button:disabled{opacity:.42;cursor:default}
#v3-menu .v3i{font-size:20px;width:26px;text-align:center;flex:none}
#v3-menu small{display:block;font-size:11px;opacity:.78;margin-top:1px}
#v3-menu hr{border:0;border-top:1px solid var(--line,#2a3442);margin:4px 2px}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*V3DE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const say = m => { try { toast(m); } catch (e) {} };
  // the place of the big picture: NOT vimg.parentNode when the scroll corner (530 #pip) holds the picture right now - on a big
  // page its IntersectionObserver can fire while the page is still parsed, before this script runs (3.62.0: then the small
  // picture and the frame never showed up until a reload)
  const vimg = document.getElementById("video"), pipC = document.getElementById("pip");
  const home = vimg && (pipC && pipC.contains(vimg) ? document.querySelector("#vcard .vwrap") : vimg.parentNode);
  if (!vimg || !home) return;
  const KEY = "mw-view3";                                 // per device (WEB_UI_LOCAL): which picture is big, small picture on / off
  const V = {view: "head", pip: true};
  try { const o = JSON.parse(localStorage.getItem(KEY) || "{}"); if (o.view === "wide") V.view = "wide"; if (o.pip === false) V.pip = false; } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(V)); } catch (e) {} };
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const info = () => { const x = (J().state || {}).extra; return (x && x[0] && x[0].view3) || {}; };
  const IC = {head: "🎯", thermal: "🌡", wide: "🔭"};
  const LB = {head: "Head view", thermal: "Thermal view", wide: "Wide view"};
  const DS = {head: "The camera of the head", thermal: "Thermal picture half transparent over the head picture", wide: "The overview camera - the frame shows where the head looks"};
  const NA = {thermal: "No thermal camera chosen", wide: "No wide-angle camera (overview)"};
  let thWant = null, thT = 0, noClick = 0, eatClick = false;
  const thOn = () => (thWant !== null && Date.now() - thT < 4000) ? thWant : !!(J().cfg || {}).thermal_on;
  const game = () => { const G = ((J().state || {}).sim || {}).game; return !!(G && G.mode === "mwhand" && (G.round === "play" || G.round === "countdown")); };   // the hunter aims in the head picture
  function avail(v) {
    if (v === "thermal") return !!(J().cfg || {}).thermal_source;
    if (v === "wide") return info().wide != null && !game();
    return true;
  }
  const order = () => ["head", "thermal", "wide"].filter(avail);
  function cur() { if (V.view === "wide" && avail("wide")) return "wide"; return thOn() && avail("thermal") ? "thermal" : "head"; }
  function setTh(on) {                                    // the 🌡 switch (thermal_on) - the same as the quick switch «Thermal»
    if (thOn() === on) return Promise.resolve({ok: true});
    thWant = on; thT = Date.now();
    return post("/api/set", {key: "thermal_on", value: on}).then(r => { if (r && r.ok === false) { thWant = null; say("⚠ " + (r.error || "error")); }
      if (typeof refresh === "function") refresh(); return r; });
  }
  function set(v, quiet) {
    if (!avail(v)) return Promise.resolve({ok: false, error: T(NA[v] || "")});
    let p = Promise.resolve({ok: true});
    if (v === "wide") V.view = "wide"; else { V.view = "head"; p = setTh(v === "thermal"); }
    save(); apply();
    if (!quiet) say(IC[v] + " " + T(LB[v]));
    return p;
  }
  function next() { const L = order(), i = L.indexOf(cur()); return set(L[(i + 1) % L.length]); }
  function swap() {                                       // big <-> small: the wide picture and the head picture (thermal stays as it is)
    if (!avail("wide")) return Promise.resolve({ok: false});
    V.view = cur() === "wide" ? "head" : "wide"; save(); apply(); say("⇅ " + T("Views swapped") + " · " + IC[cur()] + " " + T(LB[cur()]));
    return Promise.resolve({ok: true});
  }
  const click = () => Date.now() < noClick ? Promise.resolve({ok: true}) : next();
  // ---- the pieces: frame over the big picture, the small picture, the tag, the menu ----
  const OV = E("div", "v3ov"), FR = E("div", "v3fr"); FR.appendChild(E("span", "", "🎯 " + T("Where the head looks"))); OV.appendChild(FR); OV.hidden = true;
  const MB = E("button"); MB.type = "button"; MB.id = "v3-mini"; MB.hidden = true; MB.title = T("Tap the small picture: swap big and small");
  const MI = E("img"); MI.id = "v3-mimg"; MI.alt = ""; MI.draggable = false;
  const MOV = E("div", "v3ov"), MFR = E("div", "v3fr"); MOV.appendChild(MFR); MOV.hidden = true;
  const ML = E("span", "v3ml"); MB.append(MI, MOV, ML);
  MB.addEventListener("click", e => { e.stopPropagation(); e.preventDefault(); swap(); });
  MB.addEventListener("dblclick", e => e.stopPropagation());
  const TAG = E("span"); TAG.id = "v3-tag"; TAG.hidden = true;
  const vt = home.querySelector(".vtag"); if (vt) vt.appendChild(TAG);
  const MN = E("div"); MN.id = "v3-menu"; MN.hidden = true; MN.setAttribute("role", "menu"); document.body.appendChild(MN);
  function host() {                                       // the big picture on the live page or in the controller view - not in the scroll corner (#pip)
    const p = vimg.parentNode;
    return p === home || (p && p.parentNode && p.parentNode.id === "pv-live") ? p : null;
  }
  function fitOv(ov, img) {                               // the layer exactly over the shown picture (object-fit: contain = black edges)
    const p = ov.parentNode; if (!p || !img.naturalWidth || !img.getClientRects().length) return false;
    const r = img.getBoundingClientRect(), pr = p.getBoundingClientRect(), nw = img.naturalWidth, nh = img.naturalHeight || 1;
    const k = Math.min(r.width / nw, r.height / nh), w = nw * k, h = nh * k;
    ov.style.left = (r.left - pr.left - (p.clientLeft || 0) + (r.width - w) / 2) + "px"; ov.style.top = (r.top - pr.top - (p.clientTop || 0) + (r.height - h) / 2) + "px";
    ov.style.width = w + "px"; ov.style.height = h + "px"; return true;
  }
  function frameIn(ov, fr, img, on) {
    const f = info().frame;
    if (!on || !f || !fitOv(ov, img)) { ov.hidden = true; return; }
    ov.hidden = false;
    fr.style.left = ((f.x - f.w / 2) * 100) + "%"; fr.style.top = ((f.y - f.h / 2) * 100) + "%"; fr.style.width = (f.w * 100) + "%"; fr.style.height = (f.h * 100) + "%";
  }
  let TB = null;
  function toolBtn() {                                    // «Ansicht» on the picture, next to ◫ (536)
    const tools = document.getElementById("lv-tools"); if (!tools || document.getElementById("lv-b-cam")) return;
    TB = E("button"); TB.type = "button"; TB.id = "lv-b-cam";
    TB.onclick = e => { e.stopPropagation(); click(); }; TB.addEventListener("dblclick", e => e.stopPropagation());
    const vb = document.getElementById("lv-b-view"); tools.insertBefore(TB, vb || null);
  }
  function apply() {
    toolBtn();
    const i = info(), c = cur(), h = host(), sv = document.body.classList.contains("sv-on");
    const K = vimg.mwKeep;
    if (K && K.retarget) K.retarget(c === "wide" ? "/cam_feed/" + i.wide : "/video_feed");    // one stream: only its address changes
    vimg.dataset.v3 = c;
    TAG.hidden = c === "head"; TAG.textContent = IC[c] + " " + T(LB[c]);
    if (h && OV.parentNode !== h) h.appendChild(OV);
    if (h && MB.parentNode !== h) h.appendChild(MB);
    const showM = !!h && V.pip && avail("wide") && !sv;
    MB.hidden = !showM;
    if (sv || vimg.dataset.hold === "1") MI.dataset.hold = "1"; else delete MI.dataset.hold;   // covered (Sim-Ansicht): closed like the big one
    if (showM) {
      const sn = c === "wide" ? "/cam_snap/0" : "/cam_snap/" + i.wide;
      if (!MI.mwKeep) keepStream(MI, {snap: sn, every: 500, onlost: on => MB.classList.toggle("v3wait", on)});
      else MI.mwKeep.retarget(null, sn);
      ML.textContent = c === "wide" ? (IC[thOn() && avail("thermal") ? "thermal" : "head"] + " " + T(LB[thOn() && avail("thermal") ? "thermal" : "head"])) : "🔭 " + T("Wide view");
    }
    frameIn(OV, FR, vimg, c === "wide" && !!h);
    frameIn(MOV, MFR, MI, c !== "wide" && showM);
    const tip = T("Camera view") + ": " + T(LB[c]) + " · " + T("Camera view: head → thermal → wide angle (hold: choose)");
    if (TB) { TB.textContent = IC[c]; TB.title = tip; TB.setAttribute("aria-label", tip); TB.hidden = order().length < 2; }
    try { if (typeof QSJ !== "undefined" && QSJ && typeof qsPaint === "function") qsPaint(QSJ); } catch (e) {}
  }
  // ---- the menu (long press / right click): the three views, the small picture ----
  function menu(anchor) {
    MN.textContent = ""; const c = cur();
    MN.appendChild(E("div", "v3mh", "📷 " + T("Main picture")));
    VIEWS.forEach(v => { const ok = avail(v), b = E("button", v === c ? "on" : ""); b.type = "button"; b.disabled = !ok; b.dataset.v = v; b.setAttribute("role", "menuitemradio");
      const tx = E("span"); tx.append(T(LB[v]), E("small", "", T(ok ? DS[v] : NA[v]))); b.append(E("span", "v3i", IC[v]), tx);
      b.onclick = e => { e.stopPropagation(); MN.hidden = true; set(v); }; MN.appendChild(b); });
    MN.appendChild(E("hr"));
    const p = E("button", V.pip && avail("wide") ? "on" : ""); p.type = "button"; p.dataset.v = "pip"; p.disabled = !avail("wide"); p.setAttribute("role", "menuitemcheckbox");
    const tx = E("span"); tx.append(T("Small overview picture") + (V.pip ? " ✓" : ""), E("small", "", T(avail("wide") ? "Tap the small picture: swap big and small" : NA.wide)));
    p.append(E("span", "v3i", "▣"), tx);
    p.onclick = e => { e.stopPropagation(); V.pip = !V.pip; save(); apply(); menu(anchor); };
    MN.appendChild(p);
    MN.hidden = false;
    const r = anchor && anchor.getBoundingClientRect ? anchor.getBoundingClientRect() : {left: innerWidth / 2, width: 0, top: innerHeight / 2, bottom: innerHeight / 2};
    const mw = MN.offsetWidth, mh = MN.offsetHeight;
    let x = Math.min(innerWidth - mw - 8, Math.max(8, r.left + r.width / 2 - mw / 2)), y = r.bottom + 6;
    if (y + mh > innerHeight - 8) y = Math.max(8, r.top - mh - 6);
    MN.style.left = x + "px"; MN.style.top = y + "px";
  }
  const VIEWS = ["head", "thermal", "wide"];
  const LP = "#qs-view, #lv-b-cam, button.pvb[data-id='view'], [data-v3btn]";
  let lp = null;
  document.addEventListener("pointerdown", e => {
    const b = e.target.closest && e.target.closest(LP); if (!b || b.disabled) return;
    if (lp) clearTimeout(lp.t);
    lp = {x: e.clientX, y: e.clientY, t: setTimeout(() => { lp = null; noClick = Date.now() + 900; eatClick = true; menu(b); }, 550)};
  }, true);
  const lpEnd = e => { if (lp && (e.type !== "pointermove" || Math.hypot(e.clientX - lp.x, e.clientY - lp.y) > 12)) { clearTimeout(lp.t); lp = null; } };
  ["pointerup", "pointercancel", "pointermove"].forEach(n => document.addEventListener(n, lpEnd, true));
  document.addEventListener("contextmenu", e => { const b = e.target.closest && e.target.closest(LP); if (b) { e.preventDefault(); noClick = Date.now() + 900; menu(b); } }, true);
  document.addEventListener("click", e => {
    // the click when the finger lifts after a long press: always swallow it. 3.63.2: when the menu opens under the finger,
    // pointerdown (button) and pointerup (menu) differ and the click goes to <body> - before, that closed the menu at once
    if (eatClick && Date.now() < noClick) { eatClick = false; e.stopPropagation(); e.preventDefault(); return; }
    eatClick = false;
    if (Date.now() < noClick && e.target.closest && e.target.closest(LP)) { e.stopPropagation(); e.preventDefault(); return; }
    if (!MN.hidden && !MN.contains(e.target)) MN.hidden = true;
  }, true);
  addEventListener("keydown", e => { if (e.key === "Escape" && !MN.hidden) MN.hidden = true; });
  // ---- the quick switch «view» (530 QS): live page, controller view (538), «⋯ Mehr» of the Sim-Ansicht (639zt) ----
  try {
    if (typeof QS !== "undefined" && Array.isArray(QS) && !QS.some(q => q.id === "view")) {
      const at = QS.findIndex(q => q.id === "therm");
      QS.splice(at + 1, 0, {id: "view", ic: "📷", lb: "Camera view", tip: "Camera view: head → thermal → wide angle (hold: choose)",
        on: () => cur() !== "head", ok: () => order().length > 1, icf: () => IC[cur()], go: () => click()});
    }
  } catch (e) {}
  window.mwView3 = {cur: cur, set: set, next: next, swap: swap, avail: avail, menu: menu, canSwap: () => avail("wide"), icon: () => IC[cur()],
    pipSrc: () => cur() === "wide" ? "/cam_snap/" + info().wide : null, state: () => ({view: V.view, pip: V.pip, cur: cur(), order: order()})};
  addEventListener("resize", () => setTimeout(apply, 60));
  vimg.addEventListener("load", () => { if (cur() === "wide") frameIn(OV, FR, vimg, !!host()); });
  setInterval(apply, 700);
  setTimeout(apply, 0);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", VIEW3_JS.replace("/*V3DE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_V3.items()}, ensure_ascii=False), 1)
                            + "</body>", 1)
WEB_UI_LOCAL.add("mw-view3")                              # per device: which picture is big on this phone, small picture on / off


# ---- the window (Tk, 570 / 581): the same quick switch, menu, small picture ------------------------------------------
_tkv_v3 = tkv


def tkv():                                                # + 639zv: view3 (head / wide) and pip3 (small picture) of this window
    v = _tkv_v3()
    d = CFG.get("tk_live_view") if isinstance(CFG.get("tk_live_view"), dict) else {}
    v["view3"] = "wide" if d.get("view3") == "wide" else "head"
    v["pip3"] = d.get("pip3") is not False
    return v


V3_TK_IC = {"head": "⊙", "thermal": "♨", "wide": "◠"}
V3_TK_LB = {"head": "Head view", "thermal": "Thermal view", "wide": "Wide view"}


def v3_avail(v):
    if v == "thermal":
        return bool(CFG.get("thermal_source"))
    if v == "wide":
        return view3_wide_cam() is not None
    return True


def v3_cur():
    if tkv()["view3"] == "wide" and v3_avail("wide"):
        return "wide"
    return "thermal" if CFG.get("thermal_on") and v3_avail("thermal") else "head"


def _v3_tk_set(self, v):
    if not v3_avail(v):
        return
    if v == "wide":
        tkv_set(view3="wide")
    else:
        tkv_set(view3="head")
        if bool(CFG.get("thermal_on")) != (v == "thermal"):
            self._set("thermal_on", v == "thermal")
    self._qs_paint()


def _v3_tk_next(self):
    L = [v for v in VIEW3_ORDER if v3_avail(v)]
    c = v3_cur()
    self._v3_set(L[(L.index(c) + 1) % len(L)] if c in L else L[0])


def _v3_tk_swap(self):
    if v3_avail("wide"):
        tkv_set(view3="head" if v3_cur() == "wide" else "wide"); self._qs_paint()


def _v3_tk_menu(self, x, y):
    m = tk.Menu(self.root, tearoff=0)
    c = v3_cur()
    m.add_command(label=tr("Main picture"), state="disabled")
    for v in VIEW3_ORDER:
        ok = v3_avail(v)
        lab = ("● " if v == c else "○ ") + V3_TK_IC[v] + "  " + tr(V3_TK_LB[v]) + ("" if ok else "  (" + tr("No thermal camera chosen" if v == "thermal" else "No wide-angle camera (overview)") + ")")
        m.add_command(label=lab, state="normal" if ok else "disabled", command=lambda v=v: self._v3_set(v))
    m.add_separator()
    pv = tkv()["pip3"]
    m.add_command(label=("☑ " if pv else "☐ ") + tr("Small overview picture"), state="normal" if v3_avail("wide") else "disabled",
                  command=lambda: (tkv_set(pip3=not tkv()["pip3"]), self._qs_paint()))
    try:
        m.tk_popup(x, y)
    finally:
        m.grab_release()


_v3_qs_list_581 = App._qs_list


def _v3_qs_list(self):                                    # + 639zv: «Ansicht» right after «Wärmebild»
    q = _v3_qs_list_581(self)
    it = dict(id="view", ic=V3_TK_IC[v3_cur()], lb=tr("Camera view"), tip=tr("Camera view: head → thermal → wide angle (hold: choose)"),
              on=lambda: v3_cur() != "head", ok=lambda: sum(1 for v in VIEW3_ORDER if v3_avail(v)) > 1, go=lambda: self._v3_next())
    at = next((i for i, x in enumerate(q) if x.get("id") == "therm"), len(q) - 1)
    q.insert(at + 1, it)
    return q


_v3_qs_paint_570 = App._qs_paint


def _v3_qs_paint(self):                                   # + 639zv: the tile «view» shows the current view, long press = menu
    _v3_qs_paint_570(self)
    tl = (getattr(self, "qs_tiles", None) or {}).get("view")
    if not tl:
        return
    t, ic, lb, q = tl
    try:
        if not t.winfo_exists():
            return
        ic.config(text=V3_TK_IC[v3_cur()]); lb.config(text=tr(V3_TK_LB[v3_cur()]))
        if getattr(t, "_v3b", False):
            return
        t._v3b = True
        st = {"job": None, "long": False}

        def press(e):
            st["long"] = False
            st["job"] = self.root.after(550, lambda: (st.update(long=True, job=None), self._v3_menu(e.x_root, e.y_root)))

        def release(e):
            if st["job"] is not None:
                self.root.after_cancel(st["job"]); st["job"] = None
                self._qs_click(q)
        for w in (t, ic, lb):
            w.unbind("<Button-1>")
            w.bind("<ButtonPress-1>", press); w.bind("<ButtonRelease-1>", release)
            w.bind("<Button-3>", lambda e: self._v3_menu(e.x_root, e.y_root))
    except tk.TclError:
        pass


def _v3_wide_img(self, cam):
    """the newest picture of the wide camera (decoded once per new JPEG) with the frame «where the head looks»"""
    jpg, seq = cam.jpeg, cam.seq
    if not jpg:
        return None
    w = getattr(self, "_v3_w", None)
    now = time.time()
    if w and w[0] is cam and w[1] == seq and now - w[3] < 0.5:
        return w[2]
    img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    f = view3_frame(cam)
    if f:
        H, W = img.shape[:2]
        x0, y0 = int((f["x"] - f["w"] / 2) * W), int((f["y"] - f["h"] / 2) * H)
        x1, y1 = int((f["x"] + f["w"] / 2) * W), int((f["y"] + f["h"] / 2) * H)
        cv2.rectangle(img, (x0, y0), (x1, y1), (0, 0, 0), 4); cv2.rectangle(img, (x0, y0), (x1, y1), (77, 211, 255), 2)
    self._v3_w = (cam, seq, img, now)
    return img


def _v3_lease(self, cam):
    """the wide camera makes JPEGs only for viewers (440): the window counts as one while it needs the picture"""
    old = getattr(self, "_v3_cam", None)
    if old is cam:
        return
    if old is not None:
        old.viewers = max(0, old.viewers - 1)
    if cam is not None:
        cam.viewers += 1
    self._v3_cam = cam


def _v3_tk_update_video(self):
    """like 578 (night view) + 639zv: the big picture is the head or the wide camera, the other one small in a corner"""
    try:
        frame = self.watch.frame_out
        if self.video is not None and self.video.winfo_exists():
            cam = view3_wide_cam(); cur = v3_cur(); pip = tkv()["pip3"] and cam is not None
            _v3_lease(self, cam if cam is not None and (cur == "wide" or pip) else None)
            wide = _v3_wide_img(self, cam) if self._v3_cam is not None else None
            big, small = (wide if wide is not None else frame, frame) if cur == "wide" else (frame, wide)
            if not pip:
                small = None
            if big is not None:
                w = max(160, self.video.winfo_width()); h = max(90, self.video.winfo_height())
                fh, fw = big.shape[:2]; scale = min(w / fw, h / fh)
                out = cv2.resize(big, (max(1, int(fw * scale)), max(1, int(fh * scale))))
                self._v3_pip = None
                if small is not None and small is not big:
                    oh, ow = out.shape[:2]; pw = max(80, min(260, int(ow * 0.3)))
                    sh, sw = small.shape[:2]; ph = max(1, int(sh * pw / sw))
                    if ph + 16 < oh:
                        out = out.copy()
                        out[8:8 + ph, 8:8 + pw] = cv2.resize(small, (pw, ph))
                        cv2.rectangle(out, (7, 7), (8 + pw, 8 + ph), (235, 235, 235), 2)
                        self._v3_pip = (8, 8, 8 + pw, 8 + ph, ow, oh)
                if CFG.get("tk_night"):
                    gy = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
                    img = np.zeros((gy.shape[0], gy.shape[1], 3), dtype=np.uint8); img[:, :, 0] = (gy * 0.42).astype(np.uint8)
                else:
                    img = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
                pim = Image.fromarray(img)
                if getattr(self, "_egg_t0", 0):
                    pim = self._egg_draw(pim)
                self.photo = ImageTk.PhotoImage(pim); self.video.config(image=self.photo)
                if getattr(self, "_v3_bound", None) is not self.video:
                    self._v3_bound = self.video
                    self.video.bind("<ButtonRelease-1>", self._v3_tap, add="+")
        else:
            _v3_lease(self, None)
    finally:
        self.root.after(33, self._update_video)


def _v3_tk_tap(self, e):
    """a tap on the small picture: swap big and small"""
    p = getattr(self, "_v3_pip", None)
    if not p or self.video is None:
        return
    x0, y0, x1, y1, ow, oh = p
    x = e.x - (self.video.winfo_width() - ow) / 2; y = e.y - (self.video.winfo_height() - oh) / 2
    if x0 <= x <= x1 and y0 <= y <= y1:
        self._v3_swap()


# wraps: App._qs_list
App._qs_list = _v3_qs_list
# wraps: App._qs_paint
App._qs_paint = _v3_qs_paint
# wraps: App._update_video
App._update_video = _v3_tk_update_video
for _n, _f in (("_v3_set", _v3_tk_set), ("_v3_next", _v3_tk_next), ("_v3_swap", _v3_tk_swap), ("_v3_menu", _v3_tk_menu), ("_v3_tap", _v3_tk_tap)):
    setattr(App, _n, _f)


# ---- the manual: a short chapter before «Tipps & Tricks» ----
_HELP_V3 = {
    "de": ('<section id="views" data-icon="📷"><h2>Drei Kamera-Ansichten</h2><ul>'
           '<li><b>Ansicht</b> (Knopf auf dem Live-Bild und Schnellschalter): das grosse Bild der Reihe nach 🎯 Kopf → 🌡 Wärmebild '
           '(halb durchsichtig über dem Kopfbild, wie der Schalter 🌡) → 🔭 Weitwinkel (die Übersichtskamera; ein gelber Rahmen zeigt, wohin der Kopf schaut). '
           'Fehlt eine Kamera, wird die Ansicht übersprungen.</li>'
           '<li><b>Lang drücken</b> (am PC Rechtsklick): kleines Menü mit den drei Ansichten und «Kleines Übersichtsbild» ein / aus.</li>'
           '<li><b>Bild im Bild:</b> klein in der Ecke die Übersicht (oder der Kopf); antippen tauscht gross und klein. Die Wahl gilt pro Gerät. '
           'Auch in der Controller-Ansicht (⇅ / Select), der Sim-Ansicht und im Fenster am Pi.</li>'
           '</ul></section>\n'),
    "en": ('<section id="views" data-icon="📷"><h2>Three camera views</h2><ul>'
           '<li><b>View</b> (button on the live picture and quick switch): the big picture in turn 🎯 Head → 🌡 Thermal '
           '(half transparent over the head picture, like the 🌡 switch) → 🔭 Wide angle (the overview camera; a yellow frame shows where the head looks). '
           'A missing camera is skipped.</li>'
           '<li><b>Long press</b> (right click on a PC): a small menu with the three views and «Small overview picture» on / off.</li>'
           '<li><b>Picture in picture:</b> the overview (or the head) small in the corner; tap it to swap big and small. The choice is kept per device. '
           'Also in the controller view (⇅ / Select), the Sim view and in the window on the Pi.</li>'
           '</ul></section>\n'),
    "fr": ('<section id="views" data-icon="📷"><h2>Trois vues de caméra</h2><ul>'
           '<li><b>Vue</b> (bouton sur l’image live et interrupteur rapide) : la grande image tour à tour 🎯 Tête → 🌡 Image thermique '
           '(semi-transparente sur l’image de la tête, comme l’interrupteur 🌡) → 🔭 Grand angle (la caméra d’ensemble ; un cadre jaune montre où regarde la tête). '
           'Une caméra absente est sautée.</li>'
           '<li><b>Appui long</b> (clic droit sur PC) : un petit menu avec les trois vues et «Petite image d’ensemble» oui / non.</li>'
           '<li><b>Image dans l’image :</b> la vue d’ensemble (ou la tête) en petit dans le coin ; la toucher échange grande et petite. Le choix vaut pour cet appareil. '
           'Aussi dans la vue manette (⇅ / Select), la vue simulateur et dans la fenêtre du Pi.</li>'
           '</ul></section>\n'),
    "it": ('<section id="views" data-icon="📷"><h2>Tre viste della telecamera</h2><ul>'
           '<li><b>Vista</b> (pulsante sull’immagine live e interruttore rapido): l’immagine grande a turno 🎯 Testa → 🌡 Immagine termica '
           '(semitrasparente sopra l’immagine della testa, come l’interruttore 🌡) → 🔭 Grandangolo (la telecamera panoramica; un riquadro giallo mostra dove guarda la testa). '
           'Una telecamera mancante viene saltata.</li>'
           '<li><b>Pressione lunga</b> (clic destro sul PC): un piccolo menu con le tre viste e «Piccola immagine panoramica» sì / no.</li>'
           '<li><b>Immagine nell’immagine:</b> la panoramica (o la testa) piccola nell’angolo; toccarla scambia grande e piccola. La scelta vale per questo dispositivo. '
           'Anche nella vista controller (⇅ / Select), nella vista simulatore e nella finestra sul Pi.</li>'
           '</ul></section>\n'),
    "rm": ('<section id="views" data-icon="📷"><h2>Trais vistas da la camera</h2><ul>'
           '<li><b>Vista</b> (buttun sin il maletg live ed interruttur svelt): il grond maletg per turn 🎯 Chau → 🌡 Maletg termic '
           '(mez transparent sur il maletg dal chau, sco l’interruttur 🌡) → 🔭 Grond angul (la camera da survista; in rom mellen mussa nua ch’il chau guarda). '
           'Ina camera che manca vegn sursiglida.</li>'
           '<li><b>Smatgar ditg</b> (al PC clic dretg): in pitschen menu cun las trais vistas e «Pitschen maletg da survista» en / ora.</li>'
           '<li><b>Maletg en il maletg:</b> la survista (u il chau) pitschna en il chantun; tutgar barattescha grond e pitschen. La tscherna vala per quest apparat. '
           'Er en la vista dal controller (⇅ / Select), en la vista dal simulatur ed en la fanestra al Pi.</li>'
           '</ul></section>\n'),
}


def _help_v3(doc, lang):
    if 'id="views"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_V3[lang] + doc[i:] if i >= 0 else doc


_hp_en_v3 = HELP_PAGE.find('<div lang="en">')
if _hp_en_v3 > 0:
    HELP_PAGE = _help_v3(HELP_PAGE[:_hp_en_v3], "de") + _help_v3(HELP_PAGE[_hp_en_v3:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_v3(HELP_X[_L], _L)


def view3_selftest():
    f = view3_frame_calc(0.0, 0.0, 0.0, 0.0, 66.0, 41.0, 102.0, 67.0)
    assert f and f["x"] == 0.5 and f["y"] == 0.5 and abs(f["w"] - 66 / 102) < 0.01, f
    f = view3_frame_calc(30.0, 0.0, 0.0, 0.0, 66.0, 41.0, 102.0, 67.0)
    assert abs(f["x"] - (0.5 + 30 / 102)) < 0.01, f                               # head right -> frame right
    f = view3_frame_calc(0.0, 10.0, 0.0, -12.0, 66.0, 41.0, 102.0, 67.0)
    assert f["y"] < 0.5, f                                                          # head up, wide camera down -> frame high
    assert view3_frame_calc(180.0, 0.0, 0.0, 0.0, 66.0, 41.0, 102.0, 67.0) is None  # looks backwards: no frame
    assert abs(view3_frame_calc(-170.0, 0.0, 170.0, 0.0, 66.0, 41.0, 102.0, 67.0)["x"] - (0.5 + 20 / 102)) < 0.01   # across ±180°
    html = WEB_PAGE
    assert html.count('id="v3-css"') == 1 and "/*V3DE*/" not in html, "Drei Ansichten not in the live page"
    assert html.find('id="v3-css"') > html.find('id="sv-css"') > 0 and html.find('id="v3-css"') > html.find('id="pv-css"') > 0, "after 538 / 639zt"
    for need in ('"/cam_feed/"', '"/cam_snap/"', '"/video_feed"', "K.retarget", 'key: "thermal_on"', '"mw-view3"', "keepStream(MI"):
        assert need in VIEW3_JS, "Drei Ansichten: missing " + need
    assert "K.retarget = (src, sn)" in KEEP_JS, "keepStream.retarget (510)"
    for k, v in _HX_V3.items():
        assert len(v) == 4 and all(v), k
        assert k in DE and k in TRX["fr"] and k in TRX["it"] and k in TRX["rm"], k
    assert tr("Wide view", "de") == "Weitwinkel" and tr("Camera view", "rm") == "Vista"
    assert HELP_PAGE.count('<section id="views"') == 2 and all('id="views"' in (HELP_X.get(L) or 'id="views"') for L in ("fr", "it", "rm")), "manual: views"
    assert "mw-view3" in WEB_UI_LOCAL
    keep = {k: CFG.get(k) for k in ("kopf_ov", "tk_live_view", "thermal_source", "thermal_on")}
    _ss = save_settings
    try:
        globals()["save_settings"] = lambda *a, **k: None
        CFG.update(kopf_ov="", thermal_source="", thermal_on=False)
        if view3_wide_cam() is None:
            assert not v3_avail("wide") and v3_cur() == "head" and view3_info()["wide"] is None
        CFG["thermal_source"] = "senxor"; CFG["thermal_on"] = True
        assert v3_avail("thermal") and v3_cur() in ("thermal", "wide")
        tkv_set(view3="wide", pip3=False)
        assert tkv()["view3"] == "wide" and tkv()["pip3"] is False
        assert "view3" in cams_status()[0]
    finally:
        globals()["save_settings"] = _ss
        CFG.update(keep)
    return "Drei Ansichten: views, frame of the head, page, window, translations"


SELFTEST_EXTRA.append(("Three camera views: head / thermal / wide, picture in picture, frame of the head (639zv)", view3_selftest))
