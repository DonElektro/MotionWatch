#@ MoveEye – Teil 639zzzzzzd: «Bild drehen» für JEDE Kamera (Besitzer 28.11.2026) – Weitwinkel / Übersicht, Zusatzkameras (USB, Netzwerk, Simulator) und Wärmebild, wie bei der Hauptkamera 0 / 90 / 180 / 270° + spiegeln. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Besitzer (28.11.2026): «Bei der zweiten Kamera (Weitwinkel) kann man das Bild nicht drehen. Für ALLE Kameras soll man
# das Bild drehen können.»
#   - Hauptkamera: wie bisher cam_rotate / cam_mirror (Kamera / Servos, 200 cam_orient, 410).
#   - Wärmebild: thermal_rotate / thermal_mirror (Einstellungen → Wärmebild → Kamera und Ausrichtung), gedreht direkt beim Einlesen
#     (230 ThermalCam.loop) - Überlagerung, Wärme-Alarm, Abgleich (557), Nachtsicht und Kacheln sehen das gedrehte Bild.
#   - Jede weitere Kamera (Weitwinkel pi:1 / sim:1, USB, Netzwerk): CFG["cam_turn"] = {spec: {"rot": "90", "mirror": true}},
#     gedreht direkt beim Einlesen (440 ExtraCam._turn, Kamerawahl-Vorschau 639zzi) - Bewegung, Wache-KI (639zw), Zonen der
#     Übersicht, Aufnahmen, Schnappschüsse, Panorama-Rohbild und Live-Bild rechnen mit dem aufrechten Bild.
#   - Bei 90 / 270° tauscht der Blickwinkel Breite und Höhe (cam_fov_hv unten): die Richtungs-Umrechnung Übersicht → Kopf
#     (162 kopf_ov_deg über kopf_ov_fov / cam_fov_h) und der Abgleich Wärmebild ↔ Hauptbild im Simulator (sim_geom) stimmen so.
#   - Ab Werk 0° / aus; bestehende Einstellungen bleiben (nur neue Schlüssel). Eine Kamera, die gedreht wird: neue Szene
#     (Hintergrund neu, eine laufende Aufnahme endet, Protokollzeile). Zonen, die vorher auf dieses Bild gezeichnet wurden
#     (Auslösezonen der Übersicht), passen nicht mehr: der Hinweis steht bei der Kamera.
# Web: Einstellungen → Kamera / Servos, Kasten «🔄 Bild drehen: weitere Kameras» unter «Blickwinkel der Kamera» (CT_JS);
# Fenster: derselbe Kasten unter dem Blickwinkel (App._fov_box). Live-Reiter unverändert.
# ----------------------------------------------------------------------------
for _k, _v in {"cam_turn": {}, "thermal_rotate": "0", "thermal_mirror": False}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

_HX_CT = {
    "Turn picture: other cameras": ("Bild drehen: weitere Kameras", "Tourner l'image : autres caméras", "Ruota immagine: altre telecamere",
                                    "Volver il maletg: autras cameras"),
    "Camera mounted on its side or upside down? Everything after it (detection, zones, recordings, the head steered by the overview) uses the upright picture.":
        ("Kamera seitlich oder kopfüber montiert? Alles danach (Erkennung, Zonen, Aufnahmen, die Kopf-Lenkung durch die Übersicht) rechnet mit dem aufrechten Bild.",
         "Caméra montée de côté ou à l'envers ? Tout ce qui suit (détection, zones, enregistrements, la tête guidée par la vue d'ensemble) utilise l'image droite.",
         "Telecamera montata di lato o capovolta? Tutto il resto (rilevamento, zone, registrazioni, la testa guidata dalla panoramica) usa l'immagine dritta.",
         "Camera montada da la vart u cun il chau engiu? Tut quai che suonda (identificaziun, zonas, registraziuns, il chau manà da la survista) lavura cun il maletg dretg."),
    "Zones drawn on this picture before turning no longer fit - check them.":
        ("Zonen, die vor dem Drehen auf dieses Bild gezeichnet wurden, passen nicht mehr – bitte prüfen.",
         "Les zones dessinées sur cette image avant de la tourner ne correspondent plus – vérifie-les.",
         "Le zone disegnate su questa immagine prima di ruotarla non corrispondono più – controllale.",
         "Las zonas dissegnadas sin quest maletg avant che volver na correspundan betg pli – controllescha ellas."),
    "No extra camera - add one on the Cameras page.": ("Keine weitere Kamera – auf der Seite «Kameras» hinzufügen.",
                                                       "Aucune autre caméra – ajoute-en une sur la page « Caméras ».",
                                                       "Nessun'altra telecamera – aggiungila nella pagina «Telecamere».",
                                                       "Nagina autra camera – agiuntar ina sin la pagina «Cameras»."),
    "Mirror thermal picture (left ↔ right)": ("Wärmebild spiegeln (links ↔ rechts)", "Miroir de l'image thermique (gauche ↔ droite)",
                                              "Specchia immagine termica (sinistra ↔ destra)", "Spievlar il maletg termic (sanester ↔ dretg)"),
    "Turn thermal picture": ("Wärmebild drehen", "Tourner l'image thermique", "Ruota immagine termica", "Volver il maletg termic"),
    "invalid value": ("ungültiger Wert", "valeur non valable", "valore non valido", "valur nunvalaivla"),
}
for _k, _v in _HX_CT.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
# ---- settings of the thermal camera (schema, like the main camera: Kamera / Servos) ------------------------------------------
TEXTS.append(("Thermal camera", "thermal_rotate", "Turn thermal picture", "enum", "cam_rotate"))
TEXT_SPECS["thermal_rotate"] = ("enum", "cam_rotate")
TOGGLES.append(("Thermal camera", "thermal_mirror", "Mirror thermal picture (left ↔ right)"))
SIMPLE_KEYS.update({"thermal_rotate", "thermal_mirror"})
SET_HELP["thermal_rotate"] = ("Turns the thermal picture when the thermal camera is mounted upside down or on its side - the overlay, "
                              "the thermal alarm and the alignment then use the upright picture.", "Look at the thermal picture and choose what is upright.")
SET_HELP["thermal_mirror"] = ("Mirrors the thermal picture left ↔ right (e.g. a camera that delivers it mirrored).", "Off.")


# ---- the field of view of a turned camera: at 90 / 270° width and height change places ------------------------------------
_cam_fov_hv_318 = cam_fov_hv


# wraps: cam_fov_hv
def cam_fov_hv(spec=None):
    """+ 639zzzzzzd: (horizontal °, vertical °, source) of the picture as it is used - turned by 90 / 270° the camera's vertical
    field of view becomes the horizontal one (direction overview → head, distance, thermal alignment)"""
    h, v, src = _cam_fov_hv_318(spec)
    if cam_turn_get(spec)[0] in ("90", "270"):
        return v, h, src
    return h, v, src


_sim_geom_230 = ThermalCam.sim_geom


def _ct_sim_geom():
    """+ 639zzzzzzd: the simulator fit of the thermal picture with a turned main or thermal camera (fields of view swapped)"""
    g = _sim_geom_230()
    if g is None or (cam_turn_get(None)[0] not in ("90", "270") and cam_turn_get("thermal")[0] not in ("90", "270")):
        return g
    try:
        th_h, th_v, _s = cam_fov_hv("thermal")
        c_h, c_v, _s2 = cam_fov_hv(None)
        t_ = math.tan
        return (t_(math.radians(th_h) / 2) / t_(math.radians(c_h) / 2), t_(math.radians(th_v) / 2) / t_(math.radians(c_v) / 2))
    except (TypeError, ValueError, ZeroDivisionError):
        return g


# wraps: ThermalCam.sim_geom
ThermalCam.sim_geom = staticmethod(_ct_sim_geom)


# ---- set / list -----------------------------------------------------------------------------------------------------------
def cam_turn_set(spec, rot, mirror):
    """turn / mirror one camera: the main camera and the thermal camera write their schema settings, every other one cam_turn"""
    spec = str(spec or "")
    rot = str(rot if rot is not None else "0")
    if not re.fullmatch(r"[A-Za-z0-9:_./\-@]{1,200}", spec) or rot not in ("0", "90", "180", "270"):
        return False, "invalid value"
    mirror = bool(mirror)
    if spec == str(CFG.get("source") or ""):
        CFG["cam_rotate"], CFG["cam_mirror"] = rot, mirror
    elif spec in ("thermal", "sim:thermal") or spec == str(CFG.get("thermal_source") or "-"):
        CFG["thermal_rotate"], CFG["thermal_mirror"] = rot, mirror
    else:
        d = dict(CFG.get("cam_turn") or {}) if isinstance(CFG.get("cam_turn"), dict) else {}
        d.pop(spec, None)
        if rot != "0" or mirror:
            d[spec] = {"rot": rot, "mirror": mirror}
        CFG["cam_turn"] = dict(list(d.items())[-12:])
    save_settings()
    log_event("sys", f"Picture of {source_label(spec) if spec not in ('thermal',) else 'thermal camera'}: turned {rot}°" + (", mirrored" if mirror else ""))
    return True, ""


def cam_turn_zones(spec):
    """True when zones were drawn on the picture of this camera (the trigger zones of the overview, 639zw)"""
    if str(CFG.get("kopf_ov") or "") != str(spec):
        return False
    sets = CFG.get("kopf_ov_zone_sets")
    return bool(CFG.get("kopf_ov_zones")) or (isinstance(sets, dict) and any(bool(v) for v in sets.values()))


def cam_turn_list(lang=None):
    """the other cameras (not the main one) with how they are turned - for the web page and the window"""
    main = str(CFG.get("source") or "")
    out = []
    for s in dict.fromkeys(str(x) for x in (CFG.get("extra_cams") or []) if x):
        if s == main:
            continue
        r, m = cam_turn_get(s)
        out.append({"spec": s, "label": source_label(s), "rot": r, "mirror": m, "zones": cam_turn_zones(s),
                    "ov": str(CFG.get("kopf_ov") or "") == s})
    ch = [("0", "not turned"), ("90", "90° to the right"), ("180", "upside down (180°)"), ("270", "90° to the left")]
    return {"cams": out, "choices": [[k, tr(n, lang)] for k, n in ch]}


_ct_sx_routes_before = sx_routes


def sx_routes(app, watch, reply, body):                    # + /api/camturn (called once by 550; changes: administrator only)
    _ct_sx_routes_before(app, watch, reply, body)
    from flask import request, g as g_

    @app.route("/api/camturn", methods=["GET", "POST"])
    def api_camturn():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "POST":
            if getattr(g_, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            d = body(); lang = norm_lang(d.get("lang") or lang)
            ok, err = cam_turn_set(d.get("spec"), d.get("rot"), d.get("mirror"))
            if not ok:
                return reply({"ok": False, "error": tr(err, lang)}, 400)
        return reply(dict(cam_turn_list(lang), ok=True))


# ---- web: Einstellungen → Kamera / Servos, under «Blickwinkel der Kamera» (main page) ----------------------------------------
CT_JS = r"""
<script>
(function () {
  try { const D = /*CTDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  let busy = false;
  async function box() {
    const sec = document.querySelector('details[data-view="sec:Camera / Servos"]'), sl = document.querySelector('.sl[data-key="cam_vfov"]');
    if ((!sec && !sl) || document.getElementById("ct-box") || busy) return;
    busy = true; let F = null;
    try { F = await (await fetch("/api/camturn?lang=" + L(), {cache: "no-store"})).json(); } catch (e) { F = null; }
    busy = false;
    if (!F || !F.ok || document.getElementById("ct-box")) return;
    const bx = E("div", "auxbox"); bx.id = "ct-box"; bx.style.margin = "8px 0";
    bx.appendChild(E("b", "", "🔄 " + T("Turn picture: other cameras")));
    const why = E("div", "mut", T("Camera mounted on its side or upside down? Everything after it (detection, zones, recordings, the head steered by the overview) uses the upright picture.")); why.style.marginTop = "4px";
    bx.appendChild(why);
    if (!F.cams.length) bx.appendChild(E("div", "mut", T("No extra camera - add one on the Cameras page.")));
    F.cams.forEach(c => {
      const r = E("div"); r.style.marginTop = "8px"; r.dataset.spec = c.spec;
      r.appendChild(E("div", "", T("Extra camera") + ": " + c.label + (c.ov ? " · 🔭" : "")));
      const s = E("select"); s.style.width = "100%"; s.setAttribute("aria-label", T("Turn picture") + " – " + c.label);
      F.choices.forEach(([k, n]) => { const o = E("option", "", n); o.value = k; s.appendChild(o); }); s.value = c.rot;
      const l = E("label", "mut"); const m = E("input"); m.type = "checkbox"; m.checked = !!c.mirror; l.append(m, " " + T("Mirror picture (left ↔ right)"));
      l.style.cssText = "display:block;margin-top:4px";
      const hint = E("div", "mut", "⚠ " + T("Zones drawn on this picture before turning no longer fit - check them.")); hint.hidden = true; hint.style.marginTop = "4px";
      const send = async () => {
        const q = await post("/api/camturn", {spec: c.spec, rot: s.value, mirror: m.checked, lang: L()});
        if (q && q.ok) { toast("✓"); hint.hidden = !c.zones; } else toast("⚠ " + ((q && q.error) || "error"));
      };
      s.onchange = send; m.onchange = send;
      r.append(s, l, hint); bx.appendChild(r);
    });
    const fb = document.getElementById("fov-box");
    if (fb) fb.after(bx); else if (sl) sl.before(bx); else sec.appendChild(bx);
  }
  function place() {                                     // always right below «Blickwinkel der Kamera» (its box may come later)
    const b = document.getElementById("ct-box"), f = document.getElementById("fov-box");
    if (b && f && f.nextElementSibling !== b) f.after(b);
  }
  setInterval(() => { try { box(); place(); } catch (e) {} }, 1500);
})();
</script>
"""
CT_KEYS = ["Turn picture: other cameras", "Extra camera", "Turn picture", "Mirror picture (left ↔ right)",
           "Camera mounted on its side or upside down? Everything after it (detection, zones, recordings, the head steered by the overview) uses the upright picture.",
           "Zones drawn on this picture before turning no longer fit - check them.", "No extra camera - add one on the Cameras page."]
WEB_PAGE = WEB_PAGE.replace("</body>", CT_JS.replace("/*CTDE*/{}", json.dumps({k: DE.get(k, k) for k in CT_KEYS}, ensure_ascii=False), 1) + "</body>", 1)


# ---- Pi window: the same box under the field of view (Kamera / Servos) ------------------------------------------------------
_ct_fov_box_582 = App._fov_box


def _ct_app_fov_box(self, parent):
    _ct_fov_box_582(self, parent)
    try:
        _ct_tk_box(parent)
    except Exception as e:
        print(f"turn picture box: {e}")


def _ct_tk_box(parent):
    box = ttk.Frame(parent); box.pack(fill="x", pady=(8, 0))
    ttk.Label(box, text="🔄 " + tr("Turn picture: other cameras")).pack(anchor="w")
    ttk.Label(box, text=tr("Camera mounted on its side or upside down? Everything after it (detection, zones, recordings, the head steered by the overview) uses the upright picture."),
              style="Mut.TLabel", wraplength=380, justify="left").pack(anchor="w")
    F = cam_turn_list()
    names = [n for _k, n in F["choices"]]; keys = [k for k, _n in F["choices"]]
    if not F["cams"]:
        ttk.Label(box, text=tr("No extra camera - add one on the Cameras page."), style="Mut.TLabel").pack(anchor="w")
    for c in F["cams"]:
        r = ttk.Frame(box); r.pack(fill="x", pady=(4, 0))
        ttk.Label(r, text=tr("Extra camera") + ": " + str(c["label"]), style="Mut.TLabel").pack(anchor="w")
        cb = ttk.Combobox(r, values=names, state="readonly", width=34)
        cb.current(keys.index(c["rot"]) if c["rot"] in keys else 0); cb.pack(anchor="w")
        v_m = tk.BooleanVar(r, bool(c["mirror"]))
        info = ttk.Label(r, text="", style="Mut.TLabel", wraplength=380, justify="left")

        def send(*_a, c=c, cb=cb, v_m=v_m, info=info):
            ok, err = cam_turn_set(c["spec"], keys[cb.current()], v_m.get())
            info.config(text=("⚠ " + tr("Zones drawn on this picture before turning no longer fit - check them.")) if ok and c["zones"]
                        else ("" if ok else "⚠ " + tr(err)))
        cb.bind("<<ComboboxSelected>>", send)
        ttk.Checkbutton(r, variable=v_m, text=tr("Mirror picture (left ↔ right)"), command=send).pack(anchor="w")
        info.pack(anchor="w")


App._fov_box = _ct_app_fov_box


# ---- manual (HELP_PAGE de / en, HELP_X fr / it / rm): section «Kamera & Servos» ---------------------------------------------
HELP_CT = {
    "de": '<p id="ct-help"><b>🔄 Bild drehen – für jede Kamera:</b> Ist eine Kamera seitlich oder kopfüber montiert, dreht MoveEye ihr Bild '
          'um 90° / 180° / 270° und spiegelt es auf Wunsch – direkt nach dem Einlesen, so dass Erkennung, Zonen, Aufnahmen, Schnappschüsse, '
          'das Live-Bild und die Kopf-Lenkung durch die Weitwinkel-Kamera mit dem aufrechten Bild rechnen (bei 90° / 270° tauschen auch '
          'Breite und Höhe des Blickwinkels). Hauptkamera: <i>Kamera / Servos → Bild drehen</i> und <i>Bild spiegeln</i>. Weitwinkel- und '
          'weitere Kameras: <i>Kamera / Servos → 🔄 Bild drehen: weitere Kameras</i> (unter «Blickwinkel der Kamera»). Wärmebild: '
          '<i>Wärmebild → Kamera und Ausrichtung → Wärmebild drehen / spiegeln</i>. Ab Werk nicht gedreht. Zonen, die vorher auf dieses '
          'Bild gezeichnet wurden, danach prüfen.</p>',
    "en": '<p id="ct-help"><b>🔄 Turn the picture – for every camera:</b> when a camera is mounted on its side or upside down, MoveEye '
          'turns its picture by 90° / 180° / 270° and mirrors it if you like – right after reading it, so detection, zones, recordings, '
          'snapshots, the live picture and the head steered by the wide-angle camera all use the upright picture (at 90° / 270° the width '
          'and height of the field of view change places too). Main camera: <i>Camera / Servos → Turn picture</i> and <i>Mirror picture</i>. '
          'Wide-angle and other cameras: <i>Camera / Servos → 🔄 Turn picture: other cameras</i> (below «Field of view of the camera»). '
          'Thermal camera: <i>Thermal camera → Camera and alignment → Turn / mirror thermal picture</i>. Not turned from the factory. '
          'Check zones drawn on that picture before afterwards.</p>',
    "fr": '<p id="ct-help"><b>🔄 Tourner l\'image – pour chaque caméra :</b> si une caméra est montée de côté ou à l\'envers, MoveEye tourne '
          'son image de 90° / 180° / 270° et la met en miroir si tu veux – juste après la lecture, ainsi la détection, les zones, les '
          'enregistrements, les instantanés, l\'image en direct et la tête guidée par la caméra grand angle utilisent l\'image droite (à '
          '90° / 270°, la largeur et la hauteur du champ de vision s\'échangent aussi). Caméra principale : <i>Caméra / servos → Tourner '
          'l\'image</i> et <i>Miroir de l\'image</i>. Grand angle et autres caméras : <i>Caméra / servos → 🔄 Tourner l\'image : autres '
          'caméras</i>. Caméra thermique : <i>Caméra thermique → Caméra et alignement</i>. Par défaut non tournée. Vérifie ensuite les '
          'zones dessinées avant sur cette image.</p>',
    "it": '<p id="ct-help"><b>🔄 Ruotare l\'immagine – per ogni telecamera:</b> se una telecamera è montata di lato o capovolta, MoveEye '
          'ruota la sua immagine di 90° / 180° / 270° e la specchia se vuoi – subito dopo la lettura, così rilevamento, zone, '
          'registrazioni, istantanee, immagine dal vivo e la testa guidata dalla telecamera grandangolare usano l\'immagine dritta (a '
          '90° / 270° si scambiano anche larghezza e altezza del campo visivo). Telecamera principale: <i>Telecamera / servo → Ruota '
          'immagine</i> e <i>Specchia immagine</i>. Grandangolo e altre telecamere: <i>Telecamera / servo → 🔄 Ruota immagine: altre '
          'telecamere</i>. Termocamera: <i>Termocamera → Telecamera e allineamento</i>. Di fabbrica non ruotata. Poi controlla le zone '
          'disegnate prima su questa immagine.</p>',
    "rm": '<p id="ct-help"><b>🔄 Volver il maletg – per mintga camera:</b> sch\'ina camera è montada da la vart u cun il chau engiu, '
          'volva MoveEye ses maletg per 90° / 180° / 270° e al spievla sche ti vuls – directamain suenter il leger, uschia lavuran '
          'l\'identificaziun, las zonas, las registraziuns, ils fotos, il maletg live ed il chau manà da la camera da grond angul cun il '
          'maletg dretg (cun 90° / 270° sbarattan era la ladezza e l\'autezza dal champ da vista). Camera principala: <i>Camera / servos '
          '→ Volver il maletg</i> e <i>Spievlar il maletg</i>. Grond angul ed autras cameras: <i>Camera / servos → 🔄 Volver il maletg: '
          'autras cameras</i>. Camera termica: <i>Camera termica → Camera ed orientaziun</i>. Da fabrica betg vieut. Suenter controllar '
          'las zonas dissegnadas avant sin quest maletg.</p>',
}


def _help_ct(doc, lang):
    i = doc.find('<section id="camera"')
    if i < 0 or 'id="ct-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_CT[lang] + doc[j:] if j >= 0 else doc


_hp_en_ct = HELP_PAGE.find('<div lang="en">')
if _hp_en_ct > 0:
    HELP_PAGE = _help_ct(HELP_PAGE[:_hp_en_ct], "de") + _help_ct(HELP_PAGE[_hp_en_ct:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_ct(HELP_X[_L], _L)


# ---- self-test ---------------------------------------------------------------------------------------------------------------
def cam_turn_selftest():
    keys = ("source", "sim_on", "cam_rotate", "cam_mirror", "cam_turn", "thermal_rotate", "thermal_mirror", "thermal_source",
            "cam_fov", "cam_head", "kopf_ov", "kopf_ov_offset", "extra_cams")
    sv = {k: CFG.get(k) for k in keys}
    _save = globals()["save_settings"]
    try:
        globals()["save_settings"] = lambda *a, **k: None
        CFG.update(source="pi:0", sim_on=False, cam_rotate="0", cam_mirror=False, cam_turn={}, thermal_rotate="0", thermal_mirror=False,
                   thermal_source="senxor:0", cam_fov={"usb:7": {"model": "m3wide"}}, cam_head={}, kopf_ov="usb:7", kopf_ov_offset=0.0,
                   extra_cams=["usb:7"])
        # 1. size of the turned picture (also a 2-D float picture of a thermal camera)
        fr = np.zeros((360, 640, 3), np.uint8)
        assert cam_turn_frame(fr, "usb:7").shape == (360, 640, 3), "factory: not turned"
        assert cam_turn_set("usb:7", "90", False)[0] and cam_turn_frame(fr, "usb:7").shape == (640, 360, 3)
        assert cam_turn_frame(fr, "pi:0").shape == (360, 640, 3), "the main camera keeps cam_rotate"
        assert cam_turn_set("usb:7", "180", True)[0] and cam_turn_frame(fr, "usb:7").shape == (360, 640, 3)
        assert cam_turn_set("thermal", "270", False)[0] and CFG["thermal_rotate"] == "270"
        th = np.arange(62 * 80, dtype=np.float32).reshape(62, 80)
        assert cam_turn_frame(th, "thermal").shape == (80, 62) and cam_turn_frame(th, "senxor:0").shape == (80, 62)
        assert not cam_turn_set("usb:7", "45", False)[0] and not cam_turn_set("bad spec!", "90", False)[0]
        assert cam_turn_set("usb:7", "0", False)[0] and "usb:7" not in CFG["cam_turn"], "0° / not mirrored = no entry"
        # 2. the field of view: width and height change places at 90 / 270
        for rot, hv in (("0", (102, 67)), ("90", (67, 102)), ("180", (102, 67)), ("270", (67, 102))):
            cam_turn_set("usb:7", rot, False)
            h, v, _s = cam_fov_hv("usb:7")
            assert (round(h), round(v)) == hv, (rot, h, v)
        # 3. direction overview → head: a thing 20° right of the overview's middle, camera mounted turned (and mirrored)
        inv = {"0": None, "90": cv2.ROTATE_90_COUNTERCLOCKWISE, "180": cv2.ROTATE_180, "270": cv2.ROTATE_90_CLOCKWISE}
        for rot in ("0", "90", "180", "270"):
            for mir in (False, True):
                cam_turn_set("usb:7", rot, mir)
                Hu, Wu = (640, 360) if rot in ("90", "270") else (360, 640)
                up = np.zeros((Hu, Wu, 3), np.uint8)
                x = int(round((0.5 + 20.0 / kopf_ov_fov()) * Wu))
                cv2.rectangle(up, (x - 4, Hu // 2 - 4), (x + 4, Hu // 2 + 4), (255, 255, 255), -1)
                nat = cv2.flip(up, 1) if mir else up                # what the camera delivers: undo mirror, then undo the turn
                nat = cv2.rotate(nat, inv[rot]) if inv[rot] is not None else nat
                assert nat.shape[:2] == (360, 640), (rot, nat.shape)
                got = cam_turn_frame(nat, "usb:7")
                xs = np.where(got[:, :, 0].max(axis=0) > 0)[0]
                cx = (xs.min() + xs.max() + 1) / 2.0 / got.shape[1]
                d = kopf_ov_deg(cx)
                assert abs(d - 20.0) < 1.0, (rot, mir, d)
        cam_turn_set("usb:7", "90", True)
        L_ = cam_turn_list("de")
        assert L_["cams"][0]["rot"] == "90" and L_["cams"][0]["mirror"] and len(L_["choices"]) == 4
        assert all(TRX[L].get(k) for L in ("fr", "it", "rm") for k in _HX_CT), "texts fr / it / rm"
        assert 'id="ct-help"' in HELP_PAGE and HELP_PAGE.count('id="ct-help"') == 2, "manual de / en"
        return "size 90/180/270, thermal 2-D, field of view swapped, direction overview → head at 0/90/180/270 ± mirrored"
    finally:
        globals()["save_settings"] = _save
        for k, v in sv.items():
            CFG[k] = v


SELFTEST_EXTRA.append(("Turn the picture of every camera (639zzzzzzd)", cam_turn_selftest))
