#@ MoveEye – Teil 639r: Seite «Gehäuse & Bau» (/case, Mehr → Gehäuse & Bau): Gehäuse v5.1 – Montage Schritt für Schritt, Materialliste, Druckdateien (Links), Knopf «Im Simulator ansehen» (öffnet die Werkstatt im 3D-Simulator), Eintrag im Fenster (Reiter Mehr); Selbsttest: passen die Simulator-Modelle zur Quelle (Prüfsumme). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «real-gehaeuse» (01.11.2026). Eine Quelle: hardware/gehaeuse/ (Daniels parametrisches Modell v5.1 + bau.json mit den
# Texten in 5 Sprachen). werkzeuge/gehaeuse_bauen.py macht daraus die Simulator-Modelle (simulator3d/inhalte/gehaeuse/), die
# Texte des Simulators (werkstatt_daten.gd, i18n/texte.json) und die Daten hier (639q: GEH_BAU, GEH_UI_*, GEH_QUELLE_SHA).
#   * /case: Seite (Reiter Mehr) – Masse, «Im Simulator ansehen», Montage (14 Schritte, je «im Simulator zeigen»),
#     Materialliste nach Gruppen (Menge, Bezeichnung, Teilenummer), Druckdateien (3MF-Platten auf GitHub), Anleitungen.
#     Inhalte in der Sprache der Seite (LANG; rm -> de, fr / it -> en wie sonst).
#   * /api/case: GET = Daten + ob der Simulator verbunden ist; POST {do: "sim", step?} -> Simulator /control
#     {"action": "werkstatt", "do": "open"} (bzw. "step", n). Ältere Simulatoren ohne Werkstatt antworten mit Fehler.
#   * Mehr (525) und das Fenster (572 _tk_more_bar): ein Eintrag «Gehäuse & Bau». Gemeinsame Menü-Datei: «more» -> case
#     (simulator3d/ui_gemeinsam.json; im Simulator heisst derselbe Eintrag «Werkstatt», mehr.gd).
# Hier (nach 639p) weil render_page, sim_control, MORE_PAGE, smalltv_routes (639n), UI_GEMEINSAM (639p) vorher kommen.
# ----------------------------------------------------------------------------
DE.update(GEH_UI_DE)
for _L in ("fr", "it", "rm"):
    TRX.setdefault(_L, {}).update(GEH_UI_TRX.get(_L, {}))

GEH_MORE_ROW = ('  <a class="mi" href="/case" id="m-case"><i>📐</i><span><b data-i18n="Case &amp; build">Case &amp; build</b><small data-i18n="Guide, parts list, print files – in 3D in the workshop of the simulator">'
                'Guide, parts list, print files – in 3D in the workshop of the simulator</small></span><span class="ar">›</span></a>\n')
_geh_anchor = '  <a class="mi" href="/info" id="m-info">'
if 'href="/case"' not in MORE_PAGE and _geh_anchor in MORE_PAGE:
    MORE_PAGE = MORE_PAGE.replace(_geh_anchor, GEH_MORE_ROW + _geh_anchor, 1)

GEH_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Case &amp; build</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:820px;margin:0 auto}
.gc{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:14px;margin:0 0 12px}
.gc h2{font-size:16px;margin:0 0 8px}.gc .mut{color:var(--mut);font-size:13px}
.gtop{display:flex;gap:14px;align-items:center;flex-wrap:wrap}.gtop img{width:160px;max-width:40%;border-radius:10px;background:#fff}
.gtop .gt{flex:1 1 240px}
ol.gs{padding-left:0;list-style:none;margin:0;counter-reset:gs}
ol.gs li{display:flex;gap:10px;padding:9px 0;border-top:1px solid var(--line)}ol.gs li:first-child{border-top:0}
ol.gs .nr{flex:0 0 28px;height:28px;border-radius:50%;background:var(--acc);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}
ol.gs .tx{flex:1}ol.gs b{display:block;font-size:14px}ol.gs small{color:var(--mut);font-size:13px;line-height:1.4}
ol.gs button{flex:0 0 auto;align-self:center;padding:4px 9px;font-size:13px}
table.gb{width:100%;border-collapse:collapse;font-size:13px}table.gb td{padding:5px 4px;border-top:1px solid var(--line);vertical-align:top}
table.gb td.q{white-space:nowrap;color:var(--mut);width:52px}table.gb td.n{color:var(--mut);font-size:12px}
table.gb tr.gh td{border-top:0;padding-top:12px;font-weight:700;color:var(--txt)}
.gl a{display:block;padding:7px 0;color:var(--acc)}
#g-msg{margin-top:8px;min-height:18px}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <div class="gc gtop"><img src="/case/preview.png" alt="" onerror="this.remove()"><div class="gt">
    <h2><span data-i18n="Case">Case</span> v<span id="g-ver"></span></h2><div class="mut" id="g-masse"></div>
    <div class="mut" style="margin-top:6px" data-i18n="Own work of Daniel (DonElektro) – parametric Python model.">Own work of Daniel (DonElektro) – parametric Python model.</div>
    <div style="margin-top:10px"><button type="button" id="g-sim" onclick="gSim(0)">🧊 <span data-i18n="View in the simulator">View in the simulator</span></button></div>
    <div class="mut" data-i18n="Opens the workshop in the 3D simulator: turn, explode, see through, click parts, assembly step by step.">Opens the workshop in the 3D simulator: turn, explode, see through, click parts, assembly step by step.</div>
    <div id="g-msg" class="mut"></div></div></div>
  <div class="gc"><h2>⚠ <span data-i18n="Measure first: UPS HAT (E) with its cells (assumed 90 × 80 × 26 mm) before printing the lower part.">Measure first: UPS HAT (E) with its cells (assumed 90 × 80 × 26 mm) before printing the lower part.</span></h2></div>
  <div class="gc"><h2 data-i18n="Assembly step by step">Assembly step by step</h2><ol class="gs" id="g-steps"></ol></div>
  <div class="gc"><h2 data-i18n="Parts list">Parts list</h2><table class="gb" id="g-bom"></table></div>
  <div class="gc gl"><h2 data-i18n="Print files">Print files</h2><div class="mut" data-i18n="3MF plates for the Bambu Lab X2D (PETG, no supports)">3MF plates for the Bambu Lab X2D (PETG, no supports)</div>
    <div id="g-files"></div><div class="mut" data-i18n="Single STL files: in the hand-over package (ZIP, about 60 MB), not in the repository.">Single STL files: in the hand-over package (ZIP, about 60 MB), not in the repository.</div></div>
  <div class="gc gl"><h2 data-i18n="Guides and source (GitHub)">Guides and source (GitHub)</h2><div id="g-docs"></div></div>
</main>
<script>
/*COMMON*/
/*GEHDE*/
const GB = /*GEHBAU*/null;
const gL = () => LANG || "en";
const gx = v => typeof v === "string" ? v : (v[gL()] || (gL() === "rm" ? v.de : v.en) || v.de || "");
function gRender() {
  const B = GB || {}, $$ = id => document.getElementById(id);
  $$("g-ver").textContent = B.version || ""; $$("g-masse").textContent = gx(B.masse || "");
  const ol = $$("g-steps"); ol.textContent = "";
  (B.schritte || []).forEach(s => {
    const li = el("li"), nr = el("span", "nr", String(s.nr)), tx = el("span", "tx"), bt = el("button", "sec", "🧊");
    tx.append(el("b", "", gx(s.titel)), el("small", "", gx(s.text)));
    bt.type = "button"; bt.title = t("Show this step in the simulator"); bt.onclick = () => gSim(s.nr);
    li.append(nr, tx, bt); ol.appendChild(li);
  });
  const tb = $$("g-bom"); tb.textContent = ""; let grp = "";
  (B.bom || []).forEach(b => {
    if (b.gruppe !== grp) { grp = b.gruppe; const tr = el("tr", "gh"), td = el("td", "", gx((B.bom_gruppen || {})[grp] || grp)); td.colSpan = 3; tr.appendChild(td); tb.appendChild(tr); }
    const tr = el("tr"); tr.append(el("td", "q", b.menge), el("td", "", gx(b.name)), el("td", "n", b.nr || "")); tb.appendChild(tr);
  });
  const gh = B.github || "", fl = $$("g-files"), dc = $$("g-docs"); fl.textContent = ""; dc.textContent = "";
  (B.druckdateien || []).forEach(f => { const a = el("a", "", "⬇ " + f); a.href = gh + "/raw/main/hardware/gehaeuse/Druckdateien/" + f; a.target = "_blank"; a.rel = "noopener"; fl.appendChild(a); });
  [["Detailed guide v5.1", "Dokumente/LIESMICH_Montage_v5-1.md"], ["Full parts list with order list", "Dokumente/Materialliste.md"], ["Case", "LIESMICH.md"]].forEach(([k, p]) => {
    const a = el("a", "", "📄 " + t(k)); a.href = gh + "/blob/main/hardware/gehaeuse/" + p; a.target = "_blank"; a.rel = "noopener"; dc.appendChild(a); });
}
async function gSim(step) {
  const m = document.getElementById("g-msg"); m.textContent = "…";
  const r = await post("/api/case", {do: "sim", step: step || 0});
  m.textContent = r && r.ok ? t("Opened in the simulator.") : (r && r.offline ? t("Simulator not connected – start it and connect it on the page Simulator.") : ((r && r.error) || "error"));
}
const _gAi = applyI18n;
applyI18n = function () { _gAi(); try { gRender(); } catch (e) {} };
(async () => { await initAppearance(); })();
/*ALERTS*/
</script>
</body></html>
"""
GEH_KEYS = list(GEH_UI_DE)


def geh_page():
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in GEH_KEYS}, ensure_ascii=False) + ");"
    data = json.dumps(GEH_BAU, ensure_ascii=False).replace("</", "<\\/")
    return render_page(GEH_PAGE, "more").replace("/*GEHDE*/", js, 1).replace("/*GEHBAU*/null", data, 1)


def geh_do(d):
    """POST /api/case: {do: sim, step}"""
    if str(d.get("do", "")) != "sim":
        return {"ok": False, "error": "unknown action", "code": 400}
    if not CFG.get("sim_on"):
        return {"ok": False, "offline": True, "error": tr("Simulator not connected – start it and connect it on the page Simulator.")}
    try:
        n = int(d.get("step") or 0)
    except (TypeError, ValueError):
        n = 0
    n = max(0, min(n, len(GEH_BAU.get("schritte") or [])))
    try:
        r = sim_control({"action": "werkstatt", "do": "step", "n": n} if n else {"action": "werkstatt", "do": "open"}) or {}
    except Exception:
        return {"ok": False, "offline": True, "error": tr("Simulator not connected – start it and connect it on the page Simulator.")}
    if not r.get("ok") or not r.get("open"):
        return {"ok": False, "error": str(r.get("error") or "the simulator has no workshop yet (update the simulator)")}
    return {"ok": True, "step": r.get("step", 0), "steps": r.get("steps")}


def geh_preview():
    """the preview picture (Bilder/Vorschau_v5-1.png) - only where the repository is (PC), else 404"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware", "gehaeuse", "Bilder", "Vorschau_v5-1.png")
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        return f.read()


_smalltv_routes_geh_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639r: /case, /case/preview.png and /api/case
    _smalltv_routes_geh_base(app, reply, body)
    from flask import Response

    @app.route("/case")
    def geh_page_():
        return Response(geh_page(), mimetype="text/html")

    @app.route("/case/preview.png")
    def geh_prev_():
        b_ = geh_preview()
        return Response(b_, mimetype="image/png", headers={"Cache-Control": "private, max-age=3600"}) if b_ else Response("no", 404)

    @app.route("/api/case", methods=["GET", "POST"])
    def api_case():
        from flask import request
        if request.method == "GET":
            return reply({"ok": True, "version": GEH_BAU.get("version"), "sim": bool(CFG.get("sim_on")), "steps": len(GEH_BAU.get("schritte") or [])})
        r = geh_do(body())
        code = r.pop("code", None)
        return reply(r, code) if code else reply(r)


# the manual (HELP_PAGE 540 + HELP_X): a short chapter «Gehäuse & Bau» before «Einrichtung», in all 5 languages
_HELP_GEH = {
    "de": ('<section id="case" data-icon="📐"><h2>Gehäuse &amp; Bau</h2><p>Das Gehäuse v5.1 (Daniels parametrisches Python-Modell, '
           'PETG, 2 Druckplatten ohne Stützen) steht unter Mehr → <a href="/case"><b>Gehäuse &amp; Bau</b></a>: Montage in 14 Schritten, '
           'Materialliste nach Gruppen, Links zu den Druckdateien (3MF) und zur ausführlichen Anleitung. <b>«Im Simulator ansehen»</b> öffnet die '
           '<b>Werkstatt</b> im 3D-Simulator (Mehr → Werkstatt): drehen, zoomen, Explosion, durchsichtig, Teil anklicken (Materialliste und '
           'Montageschritt), Montage animiert Schritt für Schritt. Vor dem Druck des Unterteils die Masse des UPS HAT (E) mit Akkus nachmessen.</p></section>\n'),
    "en": ('<section id="case" data-icon="📐"><h2>Case &amp; build</h2><p>The case v5.1 (Daniel\'s parametric Python model, PETG, '
           '2 print plates without supports) is under More → <a href="/case"><b>Case &amp; build</b></a>: assembly in 14 steps, parts list by '
           'group, links to the print files (3MF) and to the detailed guide. <b>«View in the simulator»</b> opens the <b>workshop</b> in the 3D '
           'simulator (More → Workshop): turn, zoom, explode, see through, click a part (parts list and assembly step), animated assembly step by '
           'step. Before printing the lower part, measure the UPS HAT (E) with its cells.</p></section>\n'),
    "fr": ('<section id="case" data-icon="📐"><h2>Boîtier et construction</h2><p>Le boîtier v5.1 (modèle Python paramétrique de Daniel, '
           'PETG, 2 plateaux sans supports) se trouve sous Plus → <a href="/case"><b>Boîtier et construction</b></a> : montage en 14 étapes, '
           'liste du matériel par groupe, liens vers les fichiers d\'impression (3MF) et le guide détaillé. <b>«Voir dans le simulateur»</b> '
           'ouvre l\'<b>atelier</b> du simulateur 3D (Plus → Atelier) : tourner, zoomer, vue éclatée, transparent, cliquer une pièce, montage '
           'animé étape par étape. Avant d\'imprimer la partie inférieure, mesurer l\'UPS HAT (E) avec ses accus.</p></section>\n'),
    "it": ('<section id="case" data-icon="📐"><h2>Custodia e costruzione</h2><p>La custodia v5.1 (modello Python parametrico di Daniel, '
           'PETG, 2 piatti senza supporti) si trova in Altro → <a href="/case"><b>Custodia e costruzione</b></a>: montaggio in 14 passi, '
           'distinta dei materiali per gruppo, link ai file di stampa (3MF) e alla guida dettagliata. <b>«Vedere nel simulatore»</b> apre '
           'l\'<b>officina</b> del simulatore 3D (Altro → Officina): ruotare, zoomare, esploso, trasparente, cliccare un pezzo, montaggio '
           'animato passo per passo. Prima di stampare la parte inferiore misurare l\'UPS HAT (E) con le batterie.</p></section>\n'),
    "rm": ('<section id="case" data-icon="📐"><h2>Chascha e construcziun</h2><p>La chascha v5.1 (model Python parametric da Daniel, '
           'PETG, 2 plattas senza sustegns) è sut Dapli → <a href="/case"><b>Chascha e construcziun</b></a>: muntascha en 14 pass, '
           'glista dal material tenor gruppas, colliaziuns a las datotecas da stampa (3MF) ed a l\'instrucziun detagliada. '
           '<b>«Guardar en il simulatur»</b> avra l\'<b>ufficina</b> dal simulatur 3D (Dapli → Ufficina): volver, zoomar, explosiun, transparent, '
           'cliccar ina part, muntascha animada pass per pass. Avant che stampar la part sut mesirar l\'UPS HAT (E) cun ils accus.</p></section>\n'),
}


def _help_geh(doc, lang):
    if 'id="case"' in doc:
        return doc
    i = doc.find('<section id="setup"')
    return doc[:i] + _HELP_GEH[lang] + doc[i:] if i >= 0 else doc


_hp_en_geh = HELP_PAGE.find('<div lang="en">')
if _hp_en_geh > 0:
    HELP_PAGE = _help_geh(HELP_PAGE[:_hp_en_geh], "de") + _help_geh(HELP_PAGE[_hp_en_geh:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_geh(HELP_X[_L], _L)


if GUI_OK:                                                # the window: «Gehäuse & Bau» in the tab «Mehr» (572)
    _geh_tk_more_base = App._tk_more_bar

    def _geh_tk_more_bar(self, parent):
        f = _geh_tk_more_base(self, parent)
        i = len(f.grid_slaves())
        self._fbtn(f, "📐 " + tr("Case & build"), lambda: self._open_page("/case")).grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572)
    App._tk_more_bar = _geh_tk_more_bar


def geh_quelle_sha(base):
    """the same checksum as werkzeuge/gehaeuse_bauen.py quelle_sha() (Quellcode/*.py, bau.json, the tool)"""
    import hashlib
    q = os.path.join(base, "hardware", "gehaeuse", "Quellcode")
    fs = sorted(os.path.join(q, n) for n in os.listdir(q) if n.endswith(".py")) + [
        os.path.join(base, "hardware", "gehaeuse", "bau.json"), os.path.join(base, "werkzeuge", "gehaeuse_bauen.py")]
    h = hashlib.sha256()
    for p in fs:
        h.update(os.path.relpath(p, base).replace(os.sep, "/").encode() + b"\0")
        with open(p, "rb") as f_:
            h.update(f_.read())
        h.update(b"\0")
    return h.hexdigest()


def geh_check(base=None):
    """problems: the simulator models / texts against the source (only in the repository; the Pi has no hardware/)"""
    import hashlib
    base = base or os.path.dirname(os.path.abspath(__file__))
    probs = []
    if not os.path.isfile(os.path.join(base, "hardware", "gehaeuse", "bau.json")):
        return probs
    sha = geh_quelle_sha(base)
    if sha != GEH_QUELLE_SHA:
        probs.append("quelle/639q is older than hardware/gehaeuse - run werkzeuge/gehaeuse_bauen.py --sim")
    with open(os.path.join(base, "hardware", "gehaeuse", "bau.json"), encoding="utf-8") as f_:
        bau = json.load(f_)
    for k in ("version", "bom", "schritte", "druckdateien"):
        if bau.get(k) != GEH_BAU.get(k):
            probs.append(f"GEH_BAU[{k}] differs from bau.json - run werkzeuge/gehaeuse_bauen.py --texte")
    sd = os.path.join(base, "simulator3d", "inhalte", "gehaeuse")
    mp = os.path.join(sd, "modelle.json")
    if os.path.isfile(mp):
        with open(mp, encoding="utf-8") as f_:
            man = json.load(f_)
        if man.get("quelle_sha256") != sha:
            probs.append("simulator models do not fit the source (checksum) - run werkzeuge/gehaeuse_bauen.py --sim")
        for fn, h_ in (man.get("dateien") or {}).items():
            p = os.path.join(sd, fn)
            if not os.path.isfile(p):
                probs.append(fn + " missing")
                continue
            with open(p, "rb") as f_:
                if hashlib.sha256(f_.read()).hexdigest() != h_:
                    probs.append(fn + " changed after the build")
        if {t["id"] for t in man.get("teile", [])} != {t["id"] for t in bau.get("teile", [])}:
            probs.append("modelle.json and bau.json have different parts")
    elif os.path.isdir(os.path.join(base, "simulator3d")):
        probs.append("simulator3d/inhalte/gehaeuse/modelle.json missing")
    gd = os.path.join(base, "simulator3d", "scripts", "werkstatt_daten.gd")
    if os.path.isfile(gd):
        with open(gd, encoding="utf-8") as f_:
            if f'const QUELLE_SHA := "{sha}"' not in f_.read():
                probs.append("simulator3d/scripts/werkstatt_daten.gd is older than the source - gehaeuse_bauen.py --texte")
    ep = os.path.join(base, "simulator3d", "export_presets.cfg")
    if os.path.isfile(ep):
        with open(ep, encoding="utf-8") as f_:
            if "inhalte/gehaeuse/*" not in f_.read():
                probs.append("export_presets.cfg: inhalte/gehaeuse/* is not in the .exe")
    return probs


def geh_selftest():
    B = GEH_BAU
    assert B.get("version") == "5.1" and len(B.get("schritte") or []) == 14, "data"
    bom = {b["id"] for b in B["bom"]}
    for t_ in B["teile"]:
        assert not t_.get("bom") or t_["bom"] in bom, t_["id"]
        assert not t_.get("schritt") or 1 <= t_["schritt"] <= 14, t_["id"]
    for k in GEH_KEYS:
        assert DE.get(k), k
        for L in ("fr", "it", "rm"):
            assert TRX[L].get(k), (L, k)
    assert 'href="/case"' in MORE_PAGE and MORE_PAGE.index('href="/case"') < MORE_PAGE.index('id="m-info"'), "Mehr"
    html = geh_page()
    assert "/api/case" in html and '"schritte"' in html and "<!--NAV-->" not in html and "/*GEHBAU*/" not in html
    assert "Raspberry Pi 5" in html and "MotionWatch_v5-1_Platte_A_Unterteil.3mf" in html
    assert HELP_PAGE.count('<section id="case"') == 2 and all('href="/case"' in (HELP_X.get(L) or "href=\"/case\"") for L in ("fr", "it", "rm")), "manual"
    keep = CFG.get("sim_on")
    _sc = globals()["sim_control"]
    asked = []
    try:
        CFG["sim_on"] = False
        r = geh_do({"do": "sim"})
        assert not r["ok"] and r.get("offline"), r
        assert geh_do({"do": "x"}).get("code") == 400
        CFG["sim_on"] = True
        globals()["sim_control"] = lambda d_: (asked.append(d_), {"ok": True, "open": True, "step": int(d_.get("n", 0)), "steps": 14})[1]
        assert geh_do({"do": "sim"})["ok"] and asked[-1] == {"action": "werkstatt", "do": "open"}
        assert geh_do({"do": "sim", "step": 4})["ok"] and asked[-1] == {"action": "werkstatt", "do": "step", "n": 4}
        globals()["sim_control"] = lambda d_: {"ok": False, "error": "unknown action"}
        assert not geh_do({"do": "sim"})["ok"]                       # an older simulator without the workshop
    finally:
        globals()["sim_control"] = _sc
        CFG["sim_on"] = keep
    more = (UI_GEMEINSAM.get("more") or [])
    case = next((m for m in more if m.get("id") == "case"), None)
    assert case and case["mw"]["href"] == "/case" and case["mw"]["key"] == "Case & build", "ui_gemeinsam.json more/case"
    for L in ("de", "fr", "it", "rm"):
        assert ui_gem_tr("Case & build", L) == case["mw"]["names"][L], ("name", L)
    mg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "scripts", "mehr.gd")
    if os.path.isfile(mg):
        with open(mg, encoding="utf-8") as f_:
            assert '["%s", "wrench", "%s"' % (case["sim"]["row"], case["sim"]["key"]) in f_.read(), "simulator mehr.gd row"
    probs = geh_check()
    assert not probs, " | ".join(probs)
    return "Case & build: page /case, Mehr, simulator workshop command, models fit the source"


SELFTEST_EXTRA.append(("Case & build (page /case, workshop in the simulator, models = source)", geh_selftest))
