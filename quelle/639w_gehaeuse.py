#@ MoveEye – Teil 639w: Seite «Bauen» (/build, Mehr → Bauen; früher «Gehäuse & Bau» /case, leitet weiter): MoveEye komplett selbst bauen – 10 Reiter Übersicht · Teile · Einkauf · Drucken · Montage · Verkabeln · Software · Inbetriebnahme · Fehlersuche · Wartung, 3D-Werkstatt im Browser (three.js lokal, ohne Simulator), Varianten, «Mein Bau» pro Benutzer (/api/bau), Druckdateien (/build/datei, alle als ZIP), Knopf «Im Simulator ansehen» nur mit verbundenem Simulator; Eintrag im Fenster (Reiter Mehr); Selbsttest: Modelle = Quelle, Bau-Infos aktuell (Warnung). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «real-gehaeuse» (01.11.2026), ausgebaut im Paket «real-bauen» (01.11.2026, Daniel: «ein Bediener kann MoveEye komplett
# selbst bauen»). Eine Quelle: hardware/gehaeuse/bau.json (Teile, Materialliste mit Preis-Schätzung und Händler-Suche, Montage,
# Drucken, Werkzeug, Sicherheit, Verkabeln, Software, Inbetriebnahme, Fehlersuche, Wartung, Varianten – 5 Sprachen).
# werkzeuge/gehaeuse_bauen.py --texte macht daraus 639v (GEH_BAU, Texte), 639vb (three.js r160 + gehaeuse.glb, gepackt) und die
# Daten des Simulators (werkstatt_daten.gd). Daniel (01.11.2026): die 3D-Werkstatt in MoveEye geht OHNE Simulator – MoveEye
# liefert three.js, das Modell und die Daten selbst aus (auch offline); «Im Simulator ansehen» ist nur ein Zusatz.
#   * /build: Seite (Reiter Mehr «Bauen»), Reiter über #uebersicht … #wartung; /case leitet auf /build weiter (alte Links).
#   * /bau3d/<pfad>: three.js (gzip), /build/gehaeuse.glb: das Modell (gzip), /build/qr.svg: QR-Code zu dieser MoveEye-Seite.
#   * /build/datei/<name>: eine Druckdatei (3MF) aus hardware/gehaeuse/Druckdateien/ – auf dem Pi ohne Repository: Weiterleitung
#     zu GitHub; /build/alle.zip: alle Druckdateien in einem ZIP (nur wo sie liegen).
#   * /api/bau: «Mein Bau» – GET {var, done}, POST {var?, done?}: Variante und erledigte Schritte pro Benutzer (wie «Meine
#     Ansicht», CFG bau_mein), auf allen Geräten gleich.
#   * /api/case: GET = ob der Simulator verbunden ist; POST {do: "sim", step?} -> Simulator /control werkstatt (wie bisher).
#   * Mehr (525) und das Fenster (572 _tk_more_bar): ein Eintrag «Bauen». Gemeinsame Menü-Datei: «more» -> build
#     (simulator3d/ui_gemeinsam.json; im Simulator heisst derselbe Eintrag «Bauen», mehr.gd, Fenster werkstatt.gd mit denselben Reitern).
#   * «Fertig kaufen» (Daniel 01.11.2026, Teil 639zj): schmaler Hinweis ganz oben (#g-fertig), Paket wählen, «Fertig bestellen
#     (Anfrage)» öffnet die Rückmeldung (584 mwOrder) mit Art «Bestellung fertiges Gerät» und dem Paket.
# Hier (nach 639p) weil render_page, sim_control, MORE_PAGE, smalltv_routes (639n), UI_GEMEINSAM (639p) vorher kommen.
# ----------------------------------------------------------------------------
DE.update(GEH_UI_DE)
for _L in ("fr", "it", "rm"):
    TRX.setdefault(_L, {}).update(GEH_UI_TRX.get(_L, {}))
for _k, _v in GEH_UI2_DE.items():                         # real-bauen: the texts of the page «Bauen» (existing ones stay)
    DE.setdefault(_k, _v)
    for _L in ("fr", "it", "rm"):
        TRX.setdefault(_L, {}).setdefault(_k, GEH_UI2_TRX[_L][_k])

BAU_TABS = (("uebersicht", "Overview"), ("teile", "Parts"), ("einkauf", "Shopping"), ("drucken", "Printing"), ("montage", "Assembly"),
            ("verkabeln", "Wiring"), ("software", "Software"), ("inbetrieb", "Commissioning"), ("fehler", "Troubleshooting"),
            ("wartung", "Maintenance"))
BAU_MAX_IDS = 600
_BAU_ID = re.compile(r"^[a-z]:[A-Za-z0-9_.\-]{1,60}$")
CFG.setdefault("bau_mein", {})
LOCK_KEEP.add("bau_mein")                                 # operator mode: the own checklist is no setting of the device
VIEW_GET_PAGES.add("/build")                              # every user may look at the build guide and keep his own checklist
VIEW_GET = VIEW_GET + ("/api/bau", "/bau3d/", "/build/")
VIEW_POST.add("/api/bau")

GEH_MORE_ROW = ('  <a class="mi" href="/build" id="m-build"><i>🛠</i><span><b data-i18n="Build yourself">Build yourself</b><small data-i18n="Everything to build it yourself: 3D, parts, shopping, printing, assembly, wiring, software">'
                'Everything to build it yourself: 3D, parts, shopping, printing, assembly, wiring, software</small></span><span class="ar">›</span></a>\n')
_geh_anchor = '  <a class="mi" href="/info" id="m-info">'
if 'href="/build"' not in MORE_PAGE and _geh_anchor in MORE_PAGE:
    MORE_PAGE = MORE_PAGE.replace(_geh_anchor, GEH_MORE_ROW + _geh_anchor, 1)

# the setup assistant from a link (Bauen → Software: «/?guide=1»)
_geh_wz = "setTimeout(() => setupWizard(false), 600);"
if _geh_wz in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_geh_wz, "setTimeout(() => setupWizard(/[?&]guide=1/.test(location.search)), 600);", 1)

GEH_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Build yourself</title>
<script type="importmap">{"imports": {"three": "/bau3d/three.module.min.js", "three/addons/": "/bau3d/"}}</script>
<style>
/*BASECSS*/
main{padding:12px 16px 40px;max-width:1000px;margin:0 auto}
.gc{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:14px;margin:0 0 12px}
.gc h2{font-size:16px;margin:0 0 8px}.gc h3{font-size:14px;margin:12px 0 6px}.mut{color:var(--mut);font-size:13px}
#g-vd summary{font-weight:600;margin-top:8px}
.gtop{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap}.gtop .gt{flex:1 1 260px}
.vrow{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin-top:8px}.vrow b{font-size:13px;min-width:70px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;flex-wrap:wrap}
.seg button{border:0;border-radius:0;background:transparent;color:var(--txt);padding:6px 10px;font-size:13px;min-height:34px}
.seg button.on{background:var(--acc);color:#fff}
.prog{height:8px;border-radius:5px;background:var(--line);overflow:hidden;margin:6px 0 2px}.prog i{display:block;height:100%;background:var(--acc);width:0}
.tabs{position:sticky;top:0;z-index:5;display:flex;gap:6px;overflow-x:auto;padding:8px 2px;margin:0 0 10px;background:var(--bg);scrollbar-width:thin}
.tabs button{flex:0 0 auto;border:1px solid var(--line);background:var(--panel);color:var(--txt);border-radius:999px;padding:7px 12px;font-size:13px;min-height:36px;white-space:nowrap}
.tabs button.on{background:var(--acc);border-color:var(--acc);color:#fff}
.pane{display:none}.pane.on{display:block}
#v3d{position:relative;height:min(58vh,520px);min-height:260px;border-radius:12px;overflow:hidden;background:#1b2430;touch-action:none}
#v3d canvas{display:block;width:100%;height:100%}
#v3d .vmsg{position:absolute;left:12px;top:10px;right:12px;color:#cfd8e3;font-size:13px;pointer-events:none}
.vctl{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:10px 0 4px;font-size:13px}
.vctl label{display:flex;gap:6px;align-items:center}.vctl input[type=range]{width:140px}
.pinfo{border:1px solid var(--line);border-radius:10px;padding:10px;margin-top:8px;font-size:13px;min-height:40px}
.pinfo b{display:block;font-size:14px;margin-bottom:3px}
table.gb{width:100%;border-collapse:collapse;font-size:13px}table.gb td,table.gb th{padding:6px 4px;border-top:1px solid var(--line);vertical-align:top;text-align:left}
table.gb th{font-size:12px;color:var(--mut);font-weight:600;border-top:0}
table.gb td.q{white-space:nowrap;color:var(--mut)}table.gb td.n{color:var(--mut);font-size:12px}table.gb td.r{text-align:right;white-space:nowrap}
table.gb tr.gh td{border-top:0;padding-top:12px;font-weight:700}
.chk{width:20px;height:20px;accent-color:var(--acc)}
.lk a{color:var(--acc);margin-right:10px;white-space:nowrap;font-size:12px}
.tag{display:inline-block;font-size:11px;border-radius:6px;padding:1px 6px;margin-left:4px;background:var(--line);color:var(--txt)}
.tag.u{background:#b8860b;color:#fff}.tag.o{background:transparent;border:1px solid var(--line);color:var(--mut)}
ol.gs{padding-left:0;list-style:none;margin:0}
ol.gs li{display:flex;gap:10px;padding:9px 6px;border-top:1px solid var(--line);border-radius:8px}ol.gs li:first-child{border-top:0}
ol.gs li.cur{background:color-mix(in srgb,var(--acc) 14%,transparent)}
ol.gs .nr{flex:0 0 28px;height:28px;border-radius:50%;background:var(--acc);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}
ol.gs .tx{flex:1;cursor:pointer}ol.gs b{display:block;font-size:14px}ol.gs small{color:var(--mut);font-size:13px;line-height:1.4;display:block}
pre.cmd{background:#0f141b;color:#d6e2ee;border-radius:8px;padding:8px 10px;font-size:12px;overflow-x:auto;margin:6px 0}
.sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}
.sum button{text-align:left;border:1px solid var(--line);background:var(--panel);color:var(--txt);border-radius:12px;padding:10px;min-height:64px}
.sum button b{display:block;font-size:18px}.sum button small{color:var(--mut)}
#plan{width:100%;height:auto;max-height:70vh;background:var(--panel);border:1px solid var(--line);border-radius:12px}
#plan .nd rect{fill:var(--bg);stroke:var(--line);stroke-width:.35}#plan .nd text{fill:var(--txt);font-size:1.75px}
#plan .nd{cursor:pointer}#plan .nd.on rect{stroke:var(--acc);stroke-width:.8}#plan line{stroke-width:.45;opacity:.75}#plan line.dim{opacity:.12}#plan line.hi{stroke-width:.9;opacity:1}
.leg{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:12px;margin:6px 0}.leg i{display:inline-block;width:14px;height:4px;border-radius:2px;margin-right:4px;vertical-align:middle}
.qr{width:150px;height:150px;background:#fff;border-radius:8px;padding:4px}
.warn{border-left:4px solid #b8860b;padding-left:10px}
details summary{cursor:pointer;font-weight:600;padding:6px 0}
#g-msg{margin-top:6px;min-height:16px}
.fk{border-left:4px solid var(--acc);display:flex;flex-direction:column;gap:8px;padding:10px 12px}.fkr{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
.fk .fki{font-size:18px}.fk .fkt{flex:1 1 240px;font-size:14px}.fk .seg button{min-height:32px;padding:5px 10px}
@media (max-width:640px){main{padding:8px 10px 30px}#v3d{height:52vh}.vctl input[type=range]{width:110px}.hide-s{display:none}}
@media print{header,.tabs,.noprint,#v3d,.vctl,.gtop .vrow{display:none!important}.pane{display:none!important}.pane.on{display:block!important}
  body{background:#fff;color:#000}.gc{border:0;padding:0}a{color:#000}}
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
  <div class="gc fk noprint" id="g-fertig" hidden></div>
  <div class="gc gtop"><div class="gt">
    <h2><span data-i18n="Build yourself">Build yourself</span> · <span data-i18n="Case">Case</span> v<span id="g-ver"></span> <span class="mut" id="g-stand" style="font-size:.6em;font-weight:400"></span></h2><div class="mut" id="g-masse"></div>
    <details id="g-vd"><summary><span data-i18n="Your variant">Your variant</span>: <span class="mut" id="g-vs"></span></summary><div id="g-var"></div></details>
    <div style="margin-top:10px"><b data-i18n="My build">My build</b> <span class="mut" id="g-prog-t"></span><div class="prog"><i id="g-prog"></i></div><div class="mut" id="g-save"></div></div>
  </div></div>
  <nav class="tabs noprint" id="g-tabs" role="tablist"></nav>

  <section class="pane" id="p-uebersicht">
    <div class="gc"><div id="slot-ov"></div><div class="mut" style="margin-top:6px"><span data-i18n="Drag = turn · two fingers / wheel = zoom · tap a part = what is it?">Drag = turn · two fingers / wheel = zoom · tap a part = what is it?</span> <span data-i18n="The 3D workshop runs here in the browser – no simulator needed.">The 3D workshop runs here in the browser – no simulator needed.</span></div>
      <div class="noprint" id="g-simbox" style="display:none;margin-top:8px"><button type="button" class="sec" onclick="gSim(0)">🧊 <span data-i18n="View in the simulator">View in the simulator</span></button><div id="g-msg" class="mut"></div></div></div>
    <div class="gc"><div class="sum" id="g-sum"></div></div>
    <div class="gc warn"><b>⚠ <span data-i18n="Measure first: UPS HAT (E) with its cells (assumed 90 × 80 × 26 mm) before printing the lower part.">Measure first: UPS HAT (E) with its cells (assumed 90 × 80 × 26 mm) before printing the lower part.</span></b></div>
    <div class="gc mut" data-i18n="Own work of Daniel (DonElektro) – parametric Python model.">Own work of Daniel (DonElektro) – parametric Python model.</div>
  </section>
  <section class="pane" id="p-teile"><div class="gc"><h2 data-i18n="Parts list">Parts list</h2><table class="gb" id="g-bom"></table></div></section>
  <section class="pane" id="p-einkauf"><div class="gc">
    <h2 data-i18n="Shopping">Shopping</h2><div class="mut" data-i18n="Prices are estimates in CHF without shipping – check at the shop.">Prices are estimates in CHF without shipping – check at the shop.</div>
    <div class="noprint" style="margin:8px 0;display:flex;gap:8px;flex-wrap:wrap"><button type="button" onclick="gCsv()">⬇ <span data-i18n="Download CSV">Download CSV</span></button><button type="button" class="sec" onclick="window.print()">🖨 <span data-i18n="Print / PDF">Print / PDF</span></button></div>
    <table class="gb" id="g-buy"></table></div></section>
  <section class="pane" id="p-drucken"><div class="gc"><h2 data-i18n="Printing">Printing</h2><table class="gb" id="g-print"></table></div>
    <div class="gc"><h3 data-i18n="Notes for the Bambu printer">Notes for the Bambu printer</h3><ul id="g-phint" class="mut"></ul></div>
    <div class="gc lk"><h3 data-i18n="Print files">Print files</h3><div id="g-files"></div></div></section>
  <section class="pane" id="p-montage">
    <div class="gc"><div id="slot-mo"></div>
      <div class="vctl noprint"><button type="button" class="sec" onclick="gStep(G.step - 1)">◀ <span data-i18n="Back">Back</span></button>
        <button type="button" id="g-next" onclick="gStep(G.step + 1)"></button><button type="button" class="sec" onclick="gStep(0)" data-i18n="End">End</button><span class="mut" id="g-snr"></span></div></div>
    <div class="gc"><details><summary>🧰 <span data-i18n="Tools">Tools</span> · <span data-i18n="Screws">Screws</span></summary><ul id="g-tools"></ul><table class="gb" id="g-screws"></table></details>
      <details open><summary>⚠ <span data-i18n="Safety">Safety</span></summary><ul id="g-safe"></ul></details></div>
    <div class="gc"><h2 data-i18n="Assembly step by step">Assembly step by step</h2><ol class="gs" id="g-steps"></ol>
      <h3 data-i18n="Additionally, depending on the variant">Additionally, depending on the variant</h3><ol class="gs" id="g-xsteps"></ol></div></section>
  <section class="pane" id="p-verkabeln"><div class="gc"><h2 data-i18n="Wiring">Wiring</h2>
    <div class="mut" data-i18n="Pins and channels come from the MoveEye code and the docs. Unclear points are marked.">Pins and channels come from the MoveEye code and the docs. Unclear points are marked.</div>
    <div class="mut" data-i18n="Tap a module: its connections light up.">Tap a module: its connections light up.</div>
    <svg id="plan" viewBox="-2 -3 115 102" role="img"></svg><div class="leg" id="g-leg"></div>
    <div class="noprint"><button type="button" class="sec" onclick="gNode('')" data-i18n="All connections">All connections</button></div>
    <table class="gb" id="g-wire"></table></div></section>
  <section class="pane" id="p-software"><div class="gc"><h2 data-i18n="Software">Software</h2><ol class="gs" id="g-sw"></ol></div>
    <div class="gc gtop"><img class="qr" src="/build/qr.svg" alt="QR"><div class="gt"><b data-i18n="QR code to this MoveEye page">QR code to this MoveEye page</b><div class="mut" id="g-url"></div></div></div></section>
  <section class="pane" id="p-inbetrieb"><div class="gc"><h2 data-i18n="Commissioning">Commissioning</h2><ol class="gs" id="g-ib"></ol></div></section>
  <section class="pane" id="p-fehler"><div class="gc"><h2 data-i18n="Troubleshooting">Troubleshooting</h2><div id="g-fx"></div></div></section>
  <section class="pane" id="p-wartung"><div class="gc"><h2 data-i18n="What wears out and when to check">What wears out and when to check</h2><table class="gb" id="g-wart"></table></div></section>
  <div id="v3d"><div class="vmsg" id="v3d-msg"></div></div>
  <div class="vctl noprint" id="v3d-ctl"><label><span data-i18n="Explode">Explode</span> <input type="range" min="0" max="1" step="0.01" value="0" id="v-exp"></label>
    <label><input type="checkbox" id="v-xray"> <span data-i18n="Case see-through">Case see-through</span></label>
    <label><input type="checkbox" id="v-inner" checked> <span data-i18n="Show the inside">Show the inside</span></label>
    <button type="button" class="sec" onclick="bv('reset')" data-i18n="Reset the view">Reset the view</button></div>
  <div class="pinfo" id="v3d-info"></div>
</main>
<script>
/*COMMON*/
/*GEHDE*/
const GB = /*GEHBAU*/null;
const FK = /*GEHFK*/null;
const M3 = /*GEHM3*/null;
const SIM_ON = /*GEHSIM*/false;
const gL = () => LANG || "en";
const gx = v => v == null ? "" : typeof v === "string" ? v : (v[gL()] || (gL() === "rm" ? v.de : v.en) || v.de || "");
const fmt = (s, ...a) => { let i = 0; return String(s).replace(/%[sd]/g, () => String(a[i++])); };
const G = {tab: "uebersicht", step: 0, sel: "", node: "", var: Object.assign({}, GB.variante_standard || {}), done: new Set(), server: false};
window.BV = {explode: 0, xray: false, inner: true, v52: G.var.gehaeuse === "v52", dev: G.var.akku === "entwicklung", step: 0, sel: "", api: null};   // real-v52-standard: v5.2 is the standard (bau.json variante_standard)
function bv(what, a) { if (BV.api && BV.api[what]) BV.api[what](a); }
const ok = w => !w || Object.values(G.var).includes(w);
const TEIL = {}; (GB.teile || []).forEach(x => TEIL[x.id] = x);
const BOM = {}; (GB.bom || []).forEach(b => BOM[b.id] = b);
const isV52 = () => G.var.gehaeuse === "v52";
const GEH_VER = /*GEHVER*/"";                          // real-abgleich-v52: «Stand MoveEye X.Y.Z» from APP_VERSION (not in bau.json)
// the texts of an assembly step: v5.2 (standard) or the v5.1 texts when v5.1 is chosen (bau.json «v51»)
const sv = s => (!isV52() && s.v51) ? Object.assign({}, s, s.v51) : s;
// the 3MF of a print part: v5.2 -> Druckdateien/v5-2/ (also for parts that exist only there), else the v5.1 file
function pfile(datei) {
  const all = GB.druckdateien_einzeln || [], f1 = "MoveEye_v5-1_" + datei + ".3mf", f2 = "v5-2/MoveEye_v5-2_" + datei + ".3mf";
  return all.includes(f2) && (isV52() || !all.includes(f1)) ? f2 : f1;
}
const vname = w => { for (const v of GB.varianten || []) for (const o of v.werte) if (o.id === w) return gx(o.name); return w; };
const chf = n => (Math.round(n * 20) / 20).toFixed(2);
// ---- «Mein Bau»: the checklist (per user on the Pi, else in this browser)
let saveT = null;
function gSave() {
  clearTimeout(saveT);
  saveT = setTimeout(async () => {
    const d = {var: G.var, done: [...G.done]};
    try { localStorage.setItem("mwbau", JSON.stringify(d)); } catch (e) {}
    try { const r = await post("/api/bau", d); G.server = !!(r && r.ok); } catch (e) { G.server = false; }
    gProg();
  }, 700);
}
async function gLoad() {
  try { const r = await (await fetch("/api/bau")).json(); if (r && r.ok) { G.server = true; if (r.var && Object.keys(r.var).length) G.var = Object.assign(G.var, r.var); G.done = new Set(r.done || []); return; } } catch (e) {}
  try { const d = JSON.parse(localStorage.getItem("mwbau") || "{}"); if (d.var) G.var = Object.assign(G.var, d.var); G.done = new Set(d.done || []); } catch (e) {}
}
function allIds() {
  const ids = [];
  (GB.bom || []).forEach(b => { if (ok(b.wenn) && !b.optional) ids.push("e:" + b.id); });
  ((GB.druck || {}).teile || []).forEach(p => { if (ok(p.wenn)) ids.push("d:" + p.datei); });
  (GB.schritte || []).forEach(s => ids.push("m:" + s.nr));
  (GB.extra_schritte || []).forEach((s, i) => { if (ok(s.wenn)) ids.push("x:" + i); });
  (((GB.verkabelung || {}).verbindungen) || []).forEach(v => { if (ok(v.wenn)) ids.push("k:" + v.id); });
  (GB.software || []).forEach((s, i) => ids.push("s:" + i));
  (GB.inbetriebnahme || []).forEach((s, i) => ids.push("i:" + i));
  return ids;
}
function gProg() {
  const ids = allIds(), n = ids.filter(i => G.done.has(i)).length;
  document.getElementById("g-prog").style.width = (ids.length ? 100 * n / ids.length : 0) + "%";
  document.getElementById("g-prog-t").textContent = fmt(t("%d of %d done"), n, ids.length);
  document.getElementById("g-save").textContent = G.server ? t("Saved for you on the Pi – the same on every device.") : t("Saved only on this device (no connection to the Pi).");
}
function chk(id) {
  const c = el("input", "chk"); c.type = "checkbox"; c.checked = G.done.has(id); c.title = t("done");
  c.onchange = () => { if (c.checked) G.done.add(id); else G.done.delete(id); gSave(); };
  return c;
}
function tags(o) {
  const s = el("span");
  if (o.wenn) s.appendChild(el("span", "tag", "⚑ " + vname(o.wenn)));
  if (o.optional) s.appendChild(el("span", "tag o", t("optional")));
  if (o.unklar) { const u = el("span", "tag u", "⚠ " + t("unclear")); u.title = gx(o.unklar); s.appendChild(u); s.appendChild(el("small", "mut", " " + gx(o.unklar))); }
  return s;
}
// ---- the head: variants, tabs
function gVar() {
  const box = document.getElementById("g-var"); box.textContent = "";
  document.getElementById("g-vs").textContent = (GB.varianten || []).map(v => { const o = v.werte.find(o => o.id === G.var[v.id]); return o ? gx(o.name).split(/[:(]/)[0].trim() : ""; }).join(" · ");
  (GB.varianten || []).forEach(v => {
    const r = el("div", "vrow"); r.appendChild(el("b", "", gx(v.titel)));
    const sg = el("span", "seg");
    v.werte.forEach(o => { const b = el("button", G.var[v.id] === o.id ? "on" : "", gx(o.name)); b.type = "button";
      b.onclick = () => { G.var[v.id] = o.id; gSave(); gRender(); }; sg.appendChild(b); });
    r.appendChild(sg); box.appendChild(r);
  });
}
function gTabs() {
  const nav = document.getElementById("g-tabs"); nav.textContent = "";
  /*GEHTABS*/.forEach(([id, k]) => { const b = el("button", G.tab === id ? "on" : "", t(k)); b.type = "button"; b.setAttribute("role", "tab"); b.onclick = () => gTab(id); nav.appendChild(b); });
  document.querySelectorAll(".pane").forEach(p => p.classList.toggle("on", p.id === "p-" + G.tab));
  const slot = document.getElementById(G.tab === "montage" ? "slot-mo" : "slot-ov");
  ["v3d", "v3d-ctl", "v3d-info"].forEach(i => slot.appendChild(document.getElementById(i)));
  setTimeout(() => bv("resize"), 30);
}
function gTab(id) {
  G.tab = id; try { localStorage.setItem("mwbau-tab", id); } catch (e) {}
  history.replaceState(null, "", "#" + id); gTabs();
  const tb = document.getElementById("g-tabs"), on = tb.querySelector("button.on");
  if (on) tb.scrollLeft = on.offsetLeft - 16;
  window.scrollTo({top: Math.max(0, tb.getBoundingClientRect().top + window.scrollY - 4)});
}
// ---- the tabs
function gSummary() {
  const box = document.getElementById("g-sum"); box.textContent = "";
  const bom = (GB.bom || []).filter(b => ok(b.wenn) && !b.optional);
  const sum = bom.reduce((a, b) => a + (b.preis || 0), 0), hrs = ((GB.druck || {}).teile || []).filter(p => ok(p.wenn)).reduce((a, p) => a + p.zeit_h, 0);
  [["teile", bom.length, t("Parts")], ["einkauf", "CHF " + chf(sum), t("Total (estimate)")], ["drucken", fmt(t("about %s h"), Math.round(hrs)), t("Print time")],
   ["montage", (GB.schritte || []).length, t("Assembly")], ["verkabeln", ((GB.verkabelung || {}).verbindungen || []).filter(v => ok(v.wenn)).length, t("Wiring")]].forEach(([tab, v, k]) => {
    const b = el("button"); b.type = "button"; b.append(el("b", "", String(v)), el("small", "", k)); b.onclick = () => gTab(tab); box.appendChild(b); });
}
function gParts() {
  const tb = document.getElementById("g-bom"); tb.textContent = ""; let grp = "";
  (GB.bom || []).filter(b => ok(b.wenn)).forEach(b => {
    if (b.gruppe !== grp) { grp = b.gruppe; const tr = el("tr", "gh"), td = el("td", "", gx((GB.bom_gruppen || {})[grp] || grp)); td.colSpan = 4; tr.appendChild(td); tb.appendChild(tr); }
    const tr = el("tr"), nm = el("td"); nm.append(el("span", "", gx(b.name)), tags(b));
    const t3 = el("td", "r"), teil = (GB.teile || []).find(x => x.bom === b.id);
    if (teil) { const a = el("button", "sec", "🧊"); a.type = "button"; a.title = t("Show the part in 3D"); a.onclick = () => { gTab("uebersicht"); bv("select", teil.id); }; t3.appendChild(a); }
    tr.append(el("td", "q", b.menge), nm, el("td", "n", b.nr || ""), t3); tb.appendChild(tr);
  });
}
function shopLinks(b) {
  const s = el("span", "lk"), H = GB.haendler || {}, ks = [b.haendler, "galaxus"].filter((k, i, a) => k && H[k] && a.indexOf(k) === i);
  ks.forEach(k => { const a = el("a", "", "🔎 " + H[k].name); a.href = H[k].suche.replace("{q}", encodeURIComponent(b.suche || gx(b.name))); a.target = "_blank"; a.rel = "noopener"; a.title = t("Search link"); s.appendChild(a); });
  return s;
}
function gBuy() {
  const tb = document.getElementById("g-buy"); tb.textContent = ""; let sum = 0;
  const hd = el("tr"); ["", t("Qty"), t("Name"), t("Price"), t("Search at")].forEach(x => hd.appendChild(el("th", "", x))); tb.appendChild(hd);
  (GB.bom || []).filter(b => ok(b.wenn)).forEach(b => {
    const tr = el("tr"), c0 = el("td"); c0.appendChild(chk("e:" + b.id));
    const nm = el("td"); nm.append(el("span", "", gx(b.name)), tags(b));
    if (b.nr) nm.appendChild(el("div", "mut", b.nr));
    if (b.alt) nm.appendChild(el("div", "mut", t("Alternative") + ": " + gx(b.alt)));
    if (!b.optional) sum += b.preis || 0;
    const sl = el("td"); sl.appendChild(shopLinks(b));
    tr.append(c0, el("td", "q", b.menge), nm, el("td", "r", b.preis != null ? chf(b.preis) : ""), sl); tb.appendChild(tr);
  });
  const tr = el("tr", "gh"), a = el("td", "", t("Total (estimate)")); a.colSpan = 3; tr.append(a, el("td", "r", "CHF " + chf(sum)), el("td")); tb.appendChild(tr);
}
function gCsv() {
  const q = s => '"' + String(s == null ? "" : s).replace(/"/g, '""') + '"', H = GB.haendler || {};
  const rows = [["MoveEye – " + t("Case") + " v" + (isV52() ? "5.2" : GB.version) + (GEH_VER ? " · " + fmt(t("as of MoveEye %s"), GEH_VER) : "")],
                [t("done"), t("Qty"), t("Name"), t("Part number"), t("Price") + " CHF", t("Alternative"), t("Shop"), t("Search link"), t("optional")]];
  (GB.bom || []).filter(b => ok(b.wenn)).forEach(b => { const h = H[b.haendler] || {};
    rows.push([G.done.has("e:" + b.id) ? "x" : "", b.menge, gx(b.name), b.nr || "", b.preis != null ? chf(b.preis) : "", gx(b.alt), h.name || "", h.suche ? h.suche.replace("{q}", encodeURIComponent(b.suche || "")) : "", b.optional ? "x" : ""]); });
  const blob = new Blob(["﻿" + rows.map(r => r.map(q).join(";")).join("\r\n")], {type: "text/csv;charset=utf-8"});
  const a = el("a"); a.href = URL.createObjectURL(blob); a.download = "MoveEye_Einkauf_v" + (isV52() ? "5.2" : GB.version) + (GEH_VER ? "_" + GEH_VER : "") + ".csv"; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
function fileLink(f, label) { const a = el("a", "", "⬇ " + (label || f)); a.href = "/build/datei/" + encodeURIComponent(f); a.setAttribute("download", f); return a; }
function gPrint() {
  const D = GB.druck || {}, tb = document.getElementById("g-print"); tb.textContent = "";
  const hd = el("tr"); ["", t("Part"), t("pcs"), t("Infill"), t("Walls"), t("Supports"), t("Layer"), t("lies on"), t("Print time"), ""].forEach((x, i) => hd.appendChild(el("th", i > 5 && i < 9 ? "hide-s" : "", x))); tb.appendChild(hd);
  let hrs = 0;
  (D.teile || []).filter(p => ok(p.wenn)).forEach(p => {   // parts of a variant (e.g. v5.2) come from the data by themselves
    const tr = el("tr"), c0 = el("td"); c0.appendChild(chk("d:" + p.datei)); hrs += p.zeit_h;
    const nm = (GB.teile || []).find(x => x.datei === p.datei), dl = el("td", "lk"); dl.appendChild(fileLink(pfile(p.datei), "3MF"));
    tr.append(c0, el("td", "", nm ? gx(nm.name).replace(/^\d+ /, "") : p.datei), el("td", "q", "× " + p.stueck), el("td", "q", p.fuellung + " %"), el("td", "q", String(p.waende)),
      el("td", "q", p.stuetzen ? "✓" : t("none")), el("td", "q hide-s", p.schicht + " mm" + (p.brim ? " · Brim " + p.brim + " mm" : "")), el("td", "n hide-s", gx(p.liegt)), el("td", "q hide-s", fmt(t("about %s h"), p.zeit_h)), dl);
    tb.appendChild(tr);
  });
  const tr = el("tr", "gh"), a = el("td", "", t("Print time") + ": " + fmt(t("about %s h"), Math.round(hrs * 10) / 10) + " · " + gx(D.zeit_hinweis)); a.colSpan = 10; tr.appendChild(a); tb.appendChild(tr);
  const ul = document.getElementById("g-phint"); ul.textContent = ""; (D.hinweise || []).forEach(h => ul.appendChild(el("li", "", gx(h))));
  const fl = document.getElementById("g-files"); fl.textContent = "";
  const all = fileLink((isV52() ? "MoveEye_v5-2_Druck_" : "MoveEye_v5-1_Druck_") + GEH_VER + ".zip", t("All print files (ZIP)")); all.href = "/build/alle.zip?v=" + (isV52() ? "v52" : "v51"); fl.append(all, el("h3", "", t("Plates for the X2D (everything on 2 plates)")));
  (GB.druckdateien || []).filter(f => f.startsWith("v5-2/") === isV52()).forEach(f => fl.appendChild(fileLink(f)));   // the plates of the chosen case
  fl.appendChild(el("h3", "", t("Single parts (3MF)"))); (GB.druckdateien_einzeln || []).filter(f => {
    const datei = f.replace(/^(v5-2\/)?MoveEye_v5-[12]_/, "").replace(/\.3mf$/, ""), p = (D.teile || []).find(x => x.datei === datei);
    return p ? ok(p.wenn) && pfile(datei) === f : f.startsWith("v5-2/") === isV52();
  }).forEach(f => { fl.appendChild(fileLink(f)); fl.appendChild(el("br")); });
}
function stepLi(nr, s, id, cur) {
  const li = el("li", cur ? "cur" : ""), n = el("span", "nr", String(nr)), tx = el("span", "tx");
  s = sv(s); tx.append(el("b", "", gx(s.titel)), el("small", "", gx(s.text)));
  if (s.unklar) tx.appendChild(tags({unklar: s.unklar}));
  li.append(chk(id), n, tx); return li;
}
function gAssembly() {
  const ol = document.getElementById("g-steps"); ol.textContent = "";
  (GB.schritte || []).forEach(s => {
    const li = stepLi(s.nr, s, "m:" + s.nr, G.step === s.nr); li.id = "schritt-" + s.nr;
    const sc = (GB.schrauben || []).filter(x => x.schritt === s.nr).map(x => x.menge + " " + gx(x.was) + (x.unklar ? " (⚠ " + gx(x.unklar) + ")" : "")).join(" · ");
    if (sc) li.querySelector(".tx").appendChild(el("small", "", "🔩 " + sc));
    li.querySelector(".tx").onclick = () => { gStep(s.nr); document.getElementById("slot-mo").scrollIntoView({behavior: "smooth"}); };
    ol.appendChild(li);
  });
  const xo = document.getElementById("g-xsteps"); xo.textContent = "";
  (GB.extra_schritte || []).forEach((s, i) => { if (ok(s.wenn)) xo.appendChild(stepLi("+", s, "x:" + i, false)); });
  const tl = document.getElementById("g-tools"); tl.textContent = ""; (GB.werkzeug || []).forEach(w => tl.appendChild(el("li", "", gx(w))));
  const sc = document.getElementById("g-screws"); sc.textContent = "";
  (GB.schrauben || []).forEach(x => { const tr = el("tr"), u = el("td"); u.appendChild(tags(x)); tr.append(el("td", "q", x.menge), el("td", "", gx(x.was)), el("td", "n", t("Step") + " " + x.schritt), u); sc.appendChild(tr); });
  const sf = document.getElementById("g-safe"); sf.textContent = ""; (GB.sicherheit || []).forEach(x => { if (ok(x.wenn)) sf.appendChild(el("li", "", gx(x.text))); });
  gStepUi();
}
function gStepUi() {
  const n = (GB.schritte || []).length, nx = document.getElementById("g-next");
  nx.textContent = G.step ? t("Next") + " ▶" : t("Start the assembly") + " ▶"; nx.disabled = G.step >= n;
  document.getElementById("g-snr").textContent = G.step ? fmt(t("Step %d of %d"), G.step, n) + " – " + gx(sv(GB.schritte[G.step - 1]).titel) : "";
  document.querySelectorAll("#g-steps li").forEach(li => li.classList.toggle("cur", li.id === "schritt-" + G.step));
}
function gStep(n) {
  const N = (GB.schritte || []).length; n = Math.max(0, Math.min(N, n)); if (n === 0 && G.step === 0 && arguments.length && n !== 0) return;
  G.step = n; BV.step = n; if (n) { G.sel = ""; BV.sel = ""; } bv("step", n); gStepUi(); gInfo();
}
const ART_COL = {i2c: "#3b82f6", pwm: "#f59e0b", gpio: "#10b981", strom: "#ef4444", usb: "#8b5cf6", csi: "#ec4899", spi: "#14b8a6", audio: "#a3a3a3"};
function gWire() {
  const V = GB.verkabelung || {}, K = V.knoten || {}, svg = document.getElementById("plan"), NS = "http://www.w3.org/2000/svg"; svg.textContent = "";
  const vis = Object.keys(K).filter(k => ok(K[k].wenn)), pos = k => [K[k].x, K[k].y];
  const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); return e; };
  (V.verbindungen || []).filter(v => ok(v.wenn) && vis.includes(v.von) && vis.includes(v.nach)).forEach(v => {
    const [x1, y1] = pos(v.von), [x2, y2] = pos(v.nach), on = !G.node || v.von === G.node || v.nach === G.node;
    const l = mk("line", {x1: x1 + 7.5, y1: y1 + 2.75, x2: x2 + 7.5, y2: y2 + 2.75, stroke: ART_COL[v.art] || "#888", class: G.node ? (on ? "hi" : "dim") : ""});
    if (v.unklar) l.setAttribute("stroke-dasharray", "1.2 0.8");
    svg.appendChild(l);
  });
  vis.forEach(k => {
    const g = mk("g", {class: "nd" + (G.node === k ? " on" : "")}), [x, y] = pos(k);
    const nm = gx(K[k].name), ti = mk("title", {}); ti.textContent = nm; g.appendChild(ti);
    g.appendChild(mk("rect", {x: x, y: y, width: 15, height: 5.5, rx: 1.2}));
    const tx = mk("text", {x: x + 7.5, y: y + 3.4, "text-anchor": "middle"}); tx.textContent = nm.length > 17 ? nm.slice(0, 16) + "…" : nm; g.appendChild(tx);
    g.onclick = () => gNode(G.node === k ? "" : k); svg.appendChild(g);
  });
  const lg = document.getElementById("g-leg"); lg.textContent = "";
  Object.entries(ART_COL).forEach(([a, c]) => { const s = el("span"); const i = el("i"); i.style.background = c; s.append(i, a.toUpperCase().replace("STROM", "⚡")); lg.appendChild(s); });
  const tb = document.getElementById("g-wire"); tb.textContent = "";
  (V.verbindungen || []).filter(v => ok(v.wenn) && (!G.node || v.von === G.node || v.nach === G.node)).forEach(v => {
    const tr = el("tr"), c0 = el("td"); c0.appendChild(chk("k:" + v.id));
    const a = el("td"); const sw = el("i"); sw.style.cssText = "display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;background:" + (ART_COL[v.art] || "#888");
    a.append(sw, el("b", "", gx((K[v.von] || {}).name) + " → " + gx((K[v.nach] || {}).name)));
    const p = el("div", "", gx(v.pins)); a.appendChild(p); a.appendChild(tags({wenn: v.wenn, unklar: v.unklar}));
    tr.append(c0, a); tb.appendChild(tr);
  });
}
function gNode(k) { G.node = k; gWire(); }
function gSoftware() {
  const ol = document.getElementById("g-sw"); ol.textContent = "";
  (GB.software || []).forEach((s, i) => {
    const li = stepLi(i + 1, s, "s:" + i, false), tx = li.querySelector(".tx");
    if (s.befehl) { const pr = el("pre", "cmd", s.befehl), cp = el("button", "sec", "📋 " + t("Copy")); cp.type = "button";
      cp.onclick = () => { try { navigator.clipboard.writeText(s.befehl); toast(t("Copy") + " ✓"); } catch (e) {} }; tx.append(pr, cp); }
    if (s.link && s.link !== "qr") { const a = el("a", "", "↗ " + t("Open")); a.href = s.link; tx.appendChild(a); }
    ol.appendChild(li);
  });
  document.getElementById("g-url").textContent = location.origin + "/";
  const ib = document.getElementById("g-ib"); ib.textContent = "";
  (GB.inbetriebnahme || []).forEach((s, i) => {
    const li = stepLi(i + 1, s, "i:" + i, false);
    if (s.link) { const b = el("button", "", "↗ " + t("Open")); b.type = "button"; b.onclick = () => { location.href = s.link; }; li.appendChild(b); }
    ib.appendChild(li);
  });
}
function gFix() {
  const box = document.getElementById("g-fx"); box.textContent = "";
  (GB.fehlersuche || []).forEach(id => {
    const e = (FK || {})[id]; if (!e) return;
    const d = el("details"), sm = el("summary", "", (e.stufe === "bad" ? "⛔ " : "⚠ ") + gx(e.titel));
    d.append(sm, el("div", "mut", gx(e.text)));
    const ol = el("ol"); ((e.schritte || {})[gL()] || (e.schritte || {}).en || []).forEach(x => ol.appendChild(el("li", "", x))); d.appendChild(ol);
    const a = el("a", "", "↗ " + t("Open help")); a.href = "/hilfe/fehler/" + id; d.appendChild(a);
    box.appendChild(d);
  });
}
function gWart() {
  const tb = document.getElementById("g-wart"); tb.textContent = "";
  (GB.wartung || []).filter(w => ok(w.wenn)).forEach(w => { const tr = el("tr"); tr.append(el("td", "", gx(w.teil)), el("td", "q", gx(w.wann)), el("td", "n", gx(w.was))); tb.appendChild(tr); });
}
// ---- the part info (3D)
function gInfo() {
  const box = document.getElementById("v3d-info"); box.textContent = "";
  const p = TEIL[G.sel];
  if (!p) { box.appendChild(el("span", "mut", t("Tap a part – or choose a step of the assembly."))); return; }
  const b = BOM[p.bom];
  box.appendChild(el("b", "", gx(p.name || (b && b.name) || p.id)));
  if (b) box.appendChild(el("div", "", fmt(t("Parts list: %s %s"), b.menge, gx(b.name)) + (b.nr ? " · " + b.nr : "") + "  (" + gx((GB.bom_gruppen || {})[b.gruppe]) + ")"));
  else box.appendChild(el("div", "mut", t("not in the parts list")));
  if (p.datei) { const d = el("div", "lk"); d.append(el("span", "", fmt(t("Print file: %s"), p.datei) + " "), fileLink(pfile(p.datei), "3MF")); box.appendChild(d); }
  if (p.schritt) {
    box.appendChild(el("div", "mut", fmt(t("Assembly: step %d – %s"), p.schritt, gx(GB.schritte[p.schritt - 1].titel))));
    const go = el("button", "sec", t("Go to this step")); go.type = "button"; go.onclick = () => { gTab("montage"); gStep(p.schritt); }; box.appendChild(go);
  }
}
BV.onSelect = id => { G.sel = id || ""; BV.sel = G.sel; gInfo(); };
// ---- simulator (only an extra: the 3D view above works without it)
async function gSim(step) {
  const m = document.getElementById("g-msg"); m.textContent = "…";
  const r = await post("/api/case", {do: "sim", step: step || 0});
  m.textContent = r && r.ok ? t("Opened in the simulator.") : (r && r.offline ? t("Simulator not connected – start it and connect it on the page Simulator.") : ((r && r.error) || "error"));
}
function gRender() {
  document.getElementById("g-ver").textContent = GB.version || ""; document.getElementById("g-masse").textContent = gx(GB.masse || "");
  BV.v52 = isV52(); BV.dev = G.var.akku === "entwicklung"; bv("paint");
  if (BV.v52) document.getElementById("g-ver").textContent = "5.2";
  document.getElementById("g-stand").textContent = GEH_VER ? "· " + fmt(t("as of MoveEye %s"), GEH_VER) : "";
  gVar(); gTabs(); gSummary(); gParts(); gBuy(); gPrint(); gAssembly(); gWire(); gSoftware(); gFix(); gWart(); gInfo(); gProg();
  document.getElementById("g-simbox").style.display = SIM_ON ? "" : "none";
}
document.getElementById("v-exp").oninput = e => { BV.explode = +e.target.value; bv("paint"); };
document.getElementById("v-xray").onchange = e => { BV.xray = e.target.checked; bv("paint"); };
document.getElementById("v-inner").onchange = e => { BV.inner = e.target.checked; bv("paint"); };
const _gAi = applyI18n;
applyI18n = function () { _gAi(); try { gRender(); } catch (e) { console.error(e); } };
(async () => {
  const h = (location.hash || "").slice(1), tabs = /*GEHTABS*/.map(x => x[0]);
  let st = ""; try { st = localStorage.getItem("mwbau-tab") || ""; } catch (e) {}
  if (/^schritt-\d+$/.test(h)) { G.tab = "montage"; G.step = +h.split("-")[1]; BV.step = G.step; }
  else G.tab = tabs.includes(h) ? h : tabs.includes(st) ? st : "uebersicht";
  await gLoad(); await initAppearance(); gRender();
  if (window.innerWidth > 640) document.getElementById("g-vd").open = true;
  try { const r = await (await fetch("/api/case")).json(); document.getElementById("g-simbox").style.display = r && r.sim ? "" : "none"; } catch (e) {}
})();
/*ALERTS*/
</script>
<script>/*GEHFERTIG*/</script>
<script type="module">
/*GEH3D*/
</script>
</body></html>
"""

# the 3D workshop in the browser (three.js r160 from 639vb, the model /build/gehaeuse.glb) - like werkstatt.gd in the simulator
GEH_3D_JS = r"""
import * as THREE from "three";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
const box = document.getElementById("v3d"), msg = document.getElementById("v3d-msg"), M = window.M3 || M3, B = window.BV;
const E = {}; (M.teile || []).forEach(e => E[e.id] = e);
const T0 = new THREE.Vector3(0, -0.06, 0.04), DRUCK_ALPHA = 0.16;
msg.textContent = t("Loading 3D …");
let renderer;
try { renderer = new THREE.WebGLRenderer({antialias: true}); } catch (e) { renderer = null; msg.textContent = t("3D does not work here (no WebGL) – the lists still work."); }
if (renderer) {
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
box.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color("#1b2430");
scene.add(new THREE.HemisphereLight(0xdde6f0, 0x2a3442, 1.1));
const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(-0.5, 1.0, 0.6); scene.add(sun);
const fill = new THREE.DirectionalLight(0xffffff, 0.6); fill.position.set(0.6, 0.4, -0.8); scene.add(fill);
const cam = new THREE.PerspectiveCamera(40, 1, 0.01, 10);
const ctl = new OrbitControls(cam, renderer.domElement);
ctl.minDistance = 0.12; ctl.maxDistance = 2.0; ctl.enableDamping = false;
const bench = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.7), new THREE.MeshStandardMaterial({color: 0x2a3442, roughness: 0.9}));
bench.rotation.x = -Math.PI / 2; bench.position.set(0, -((M.kippachse_ueber_boden_m || 0.1258) + (M.fuesse_m || 0.006)) - 0.0005, 0.045); scene.add(bench);
const parts = {};
let anim = 1, raf = 0;
function view(yaw, pitch, d, tg) {
  const y = yaw * Math.PI / 180, p = pitch * Math.PI / 180; ctl.target.copy(tg || T0);
  cam.position.set(ctl.target.x + d * Math.cos(p) * Math.sin(y), ctl.target.y + d * Math.sin(p), ctl.target.z + d * Math.cos(p) * Math.cos(y));
  ctl.update(); render();
}
function render() { renderer.render(scene, cam); }
function size() { const w = box.clientWidth || 300, h = box.clientHeight || 260; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); render(); }
new ResizeObserver(size).observe(box);
ctl.addEventListener("change", render);
const row = id => (GB.teile || []).find(x => x.id === id) || {};
const REPL = {}; (GB.teile || []).forEach(x => { if (x.ersetzt) REPL[x.ersetzt] = x.id; });
function shown(id) {
  const r = row(id), art = r.art || "", s = B.step;
  if (art === "v52" && !B.v52) return false;           // real-v52-standard: v5.2 parts in every step (bau.json «schritt»)
  if (art === "dev" && !B.dev) return false;           // development: socket 13 instead of the UPS HAT
  if (r.ohne) return false;                            // 12 blind plug: only in the scene (device without the wide camera)
  const by = REPL[id];                                 // replaced by the part of the chosen variant (lower part v5.2, socket ...)
  if (by && parts[by] && ((row(by).art === "v52" && B.v52) || (row(by).art === "dev" && B.dev))) return false;
  const pr = art === "druck" || !!r.datei;
  if (s === 1) return pr;
  if (s > 1 && (r.schritt || 0) > s) return false;
  if (!B.inner && !pr && !(E[id] || {}).aussen) return false;
  return true;
}
const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
function paint() {
  for (const id in parts) {
    const p = parts[id], r = row(id), m = p.mesh, ex = (E[id] || {}).explosion || [0, 0, 0];
    m.visible = shown(id);
    let k = B.explode;
    const cur = B.step > 1 && r.schritt === B.step;
    if (B.step === 1) k = 1; else if (cur) k = Math.max(B.explode, 1 - ease(anim));
    m.position.set(ex[0] * k, ex[1] * k + (cur ? 0.06 * (1 - ease(anim)) : 0), ex[2] * k);
    const see = B.xray && (r.art === "druck" || !!r.datei), mat = m.material;
    mat.transparent = see; mat.opacity = see ? DRUCK_ALPHA : 1; mat.depthWrite = !see;
    const hi = id === B.sel || cur;
    mat.emissive.set(hi ? (id === B.sel ? 0x3b82f6 : 0xf59a4a) : 0x000000); mat.emissiveIntensity = hi ? (id === B.sel ? 0.55 : 0.35) : 0;
  }
  render();
}
function loop() { anim = Math.min(1, anim + 1 / 66); paint(); if (anim < 1) raf = requestAnimationFrame(loop); else raf = 0; }
function step(n) {
  anim = n > 1 ? 0 : 1;
  if (n > 0) { const c = new THREE.Vector3(); let k = 0;
    for (const id in parts) if (row(id).schritt === n && E[id]) { c.add(new THREE.Vector3(...E[id].mitte)); k++; }
    const tg = k && n > 1 ? T0.clone().lerp(c.multiplyScalar(1 / k), 0.6) : T0;
    const off = cam.position.clone().sub(ctl.target); ctl.target.copy(tg); cam.position.copy(tg).add(off); ctl.update();
  }
  paint(); if (anim < 1 && !raf) raf = requestAnimationFrame(loop);
}
function pick(ev) {
  const rc = new THREE.Raycaster(), r = renderer.domElement.getBoundingClientRect();
  rc.setFromCamera(new THREE.Vector2((ev.clientX - r.left) / r.width * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1), cam);
  const vis = Object.values(parts).filter(p => p.mesh.visible).map(p => p.mesh);
  let hits = rc.intersectObjects(vis, false);
  if (B.xray) { const inner = hits.filter(h => row(h.object.name).art !== "druck" && !row(h.object.name).datei); if (inner.length) hits = inner; }
  return hits.length ? hits[0].object.name : "";
}
let down = null;
renderer.domElement.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener("pointerup", e => {
  if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 6) { B.sel = pick(e); B.onSelect && B.onSelect(B.sel); paint(); }
  down = null;
});
new GLTFLoader().load("/build/gehaeuse.glb", g => {
  const FB = GB.farben || {}, farbe = id => (row(id) || {}).farbe || FB[id] || ((FB.grau_teile || []).includes(id) && FB.grau) || (E[id] || {}).farbe || "";   // colours from the data (bau.json / modelle.json), else the model's
  g.scene.traverse(o => { if (o.isMesh) { o.material = o.material.clone(); o.material.side = THREE.DoubleSide; o.material.roughness = 0.6; o.material.metalness = 0;
    if (farbe(o.name)) o.material.color.set(farbe(o.name)); parts[o.name] = {mesh: o}; } });
  scene.add(g.scene); msg.textContent = ""; size(); view(145, 24, 0.5); step(B.step);
  window.BV_READY = Object.keys(parts).length;
}, undefined, e => { msg.textContent = "3D: " + (e && e.message || e); });
B.api = {paint, step, resize: size, select: id => { B.sel = id; B.onSelect && B.onSelect(id); paint(); }, reset: () => { B.explode = 0; document.getElementById("v-exp").value = 0; view(145, 24, 0.5); paint(); }};
size(); view(145, 24, 0.5);
}
"""
GEH_KEYS = sorted(set(GEH_UI_DE) | set(GEH_UI2_DE) | {k for _i, k in BAU_TABS} | {
    "Case", "Step", "Name", "Opened in the simulator.", "Simulator not connected – start it and connect it on the page Simulator."})


def geh_fk():
    """the entries of the error catalogue (639u) the tab «Fehlersuche» shows: title, text, steps in 5 languages"""
    es = {e["id"]: e for e in (FEHLER_KATALOG.get("fehler") or [])}
    return {i: {k: es[i].get(k) for k in ("titel", "text", "schritte", "stufe")} for i in GEH_BAU.get("fehlersuche") or [] if i in es}


def geh_page():
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in GEH_KEYS}, ensure_ascii=False) + ");"
    J = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    return (render_page(GEH_PAGE, "more").replace("/*GEHDE*/", js, 1).replace("/*GEHBAU*/null", J(GEH_BAU), 1)
            .replace("/*GEHFK*/null", J(geh_fk()), 1).replace("/*GEHM3*/null", J(BAU3D_MODELLE), 1)
            .replace("/*GEHVER*/\"\"", json.dumps(APP_VERSION), 1)
            .replace("/*GEHSIM*/false", "true" if CFG.get("sim_on") else "false", 1)
            .replace("/*GEHTABS*/", J([list(x) for x in BAU_TABS])).replace("/*GEH3D*/", GEH_3D_JS, 1)
            .replace("/*GEHFERTIG*/", fertig_js(), 1))                       # «Fertig kaufen» (639zj): the hint at the top


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


# ---- «Mein Bau» (per user, like «Meine Ansicht» 639r) ------------------------------------------------------------------------
def bau_var_clean(v):
    out = {}
    if isinstance(v, dict):
        for grp in GEH_BAU.get("varianten") or []:
            x = v.get(grp["id"])
            if isinstance(x, str) and x in {o["id"] for o in grp["werte"]}:
                out[grp["id"]] = x
    return out


def bau_mein_get(user):
    e = (CFG.get("bau_mein") or {}).get(str(user)[:60]) or {}
    return {"var": bau_var_clean(e.get("var")), "done": [x for x in e.get("done") or [] if isinstance(x, str) and _BAU_ID.match(x)]}


def bau_mein_set(user, var=None, done=None):
    allv = dict(CFG.get("bau_mein") or {})
    e = dict(allv.get(str(user)[:60]) or {})
    if var is not None:
        e["var"] = bau_var_clean(var)
    if done is not None:
        if not isinstance(done, list):
            return False
        e["done"] = sorted({x for x in done if isinstance(x, str) and _BAU_ID.match(x)})[:BAU_MAX_IDS]
    e["t"] = int(time.time())
    allv[str(user)[:60]] = e
    CFG["bau_mein"] = dict(sorted(allv.items(), key=lambda kv: -int((kv[1] or {}).get("t") or 0))[:60])
    save_settings()
    return True


def geh_preview():
    """the preview picture (Bilder/Vorschau_v5-1.png) - only where the repository is (PC), else 404"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware", "gehaeuse", "Bilder", "Vorschau_v5-1.png")
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        return f.read()


def geh_druck_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware", "gehaeuse", "Druckdateien")


def geh_druck_namen():
    return list(GEH_BAU.get("druckdateien") or []) + list(GEH_BAU.get("druckdateien_einzeln") or [])


def geh_alle_zip(v52=True):
    """the print files of one case (v5.2: Druckdateien/v5-2/, v5.1: the others) that are here in one ZIP, named with the
    version (real-abgleich-v52: MoveEye_v5-2_Druck_X.Y.Z) - 3MF are compressed already: stored. None without the repository"""
    import io
    import zipfile
    d = geh_druck_dir()
    fs = [n for n in geh_druck_namen() if os.path.isfile(os.path.join(d, n)) and n.startswith("v5-2/") == v52]
    if not fs:
        return None
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_STORED) as z:
        for n in fs:
            z.write(os.path.join(d, n), geh_alle_name(v52) + "/" + n.split("/")[-1])
    return b.getvalue()


def geh_alle_name(v52=True):
    """the name of the print ZIP with the running version, e.g. MoveEye_v5-2_Druck_3.46.1 (the 3MF keep their names)"""
    return ("MoveEye_v5-2_Druck_" if v52 else "MoveEye_v5-1_Druck_") + APP_VERSION


_BAU3D_CACHE = {}


def bau3d_bytes(key):
    """the gzip bytes of a three.js file or of the model (639vb) - decoded once"""
    import base64
    if key not in _BAU3D_CACHE:
        if key == "glb":
            _BAU3D_CACHE[key] = base64.b64decode(BAU3D_GLB[2])
        elif key in BAU3D:
            _BAU3D_CACHE[key] = base64.b64decode(BAU3D[key][1])
        else:
            return None
    return _BAU3D_CACHE[key]


_smalltv_routes_geh_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639w: /build, /case (-> /build), /bau3d, /api/bau, /api/case
    _smalltv_routes_geh_base(app, reply, body)
    from flask import Response, redirect, request, g

    @app.route("/build")
    def geh_page_():
        return Response(geh_page(), mimetype="text/html")

    @app.route("/case")
    def geh_case_old():                                  # the old page «Gehäuse & Bau» is in «Bauen» now
        return redirect("/build", code=302)

    @app.route("/case/preview.png")
    @app.route("/build/preview.png")
    def geh_prev_():
        b_ = geh_preview()
        return Response(b_, mimetype="image/png", headers={"Cache-Control": "private, max-age=3600"}) if b_ else Response("no", 404)

    def gz(b_, mt):
        return Response(b_, mimetype=mt, headers={"Content-Encoding": "gzip", "Cache-Control": "private, max-age=86400", "Vary": "Accept-Encoding"})

    @app.route("/bau3d/<path:p>")
    def geh_three(p):
        b_ = bau3d_bytes(p)
        return gz(b_, "text/javascript") if b_ else Response("no", 404)

    @app.route("/build/gehaeuse.glb")
    def geh_glb():
        return gz(bau3d_bytes("glb"), "model/gltf-binary")

    @app.route("/build/qr.svg")
    def geh_qr():
        return Response(qr_svg(request.host_url), mimetype="image/svg+xml", headers={"Cache-Control": "no-store"})

    @app.route("/build/datei/<path:name>")                # path: the files of v5.2 are in Druckdateien/v5-2/
    def geh_datei(name):
        if name not in geh_druck_namen():
            return Response("no", 404)
        p = os.path.join(geh_druck_dir(), name)
        if os.path.isfile(p):
            with open(p, "rb") as f_:
                return Response(f_.read(), mimetype="model/3mf", headers={"Content-Disposition": f'attachment; filename="{name}"'})
        return redirect(GEH_BAU.get("github", "") + "/raw/main/hardware/gehaeuse/Druckdateien/" + name, code=302)

    @app.route("/build/alle.zip")
    def geh_alle():
        v52_ = request.args.get("v", "v52") != "v51"
        b_ = geh_alle_zip(v52_)
        if b_ is None:
            return redirect(GEH_BAU.get("github", "") + "/tree/main/hardware/gehaeuse/Druckdateien", code=302)
        return Response(b_, mimetype="application/zip", headers={"Content-Disposition": f'attachment; filename="{geh_alle_name(v52_)}.zip"'})

    @app.route("/api/bau", methods=["GET", "POST"])
    def api_bau():                                       # «Mein Bau»: variant and checklist per user (every device)
        user = ansicht_user(g)
        if request.method == "POST":
            d = body()
            ok_ = bau_mein_set(user, d.get("var"), d.get("done"))
            return reply({"ok": ok_, "user": user}, 200 if ok_ else 400)
        return reply(dict(bau_mein_get(user), ok=True, user=user))

    @app.route("/api/case", methods=["GET", "POST"])
    def api_case():
        if request.method == "GET":
            return reply({"ok": True, "version": GEH_BAU.get("version"), "sim": bool(CFG.get("sim_on")), "steps": len(GEH_BAU.get("schritte") or [])})
        r = geh_do(body())
        code = r.pop("code", None)
        return reply(r, code) if code else reply(r)


# the manual (HELP_PAGE 540 + HELP_X): a short chapter «Bauen» before «Einrichtung», in all 5 languages
_HELP_GEH = {
    "de": ('<section id="case" data-icon="🛠"><h2>Bauen</h2><p>Alles, um MoveEye selbst zu bauen, steht unter Mehr → <a href="/build"><b>Bauen</b></a> '
           '(früher «Gehäuse &amp; Bau»), in Reitern: Übersicht mit der <b>3D-Werkstatt</b> (drehen, zoomen, Explosion, durchsichtig, Innenleben, '
           'Teil antippen – läuft im Browser, ohne Simulator und ohne Internet), Teile, Einkauf (Preis-Schätzung, Händler-Suche, CSV, Drucken), '
           'Drucken (pro Teil, Druckdateien einzeln oder alle), Montage (14 Schritte, animiert), Verkabeln (Plan mit Pins und Kanälen), Software, '
           'Inbetriebnahme, Fehlersuche und Wartung. Oben die Variante (v5.1 / v5.2, mit / ohne Akku, mit / ohne Mover) und <b>«Mein Bau»</b>: '
           'deine Checkliste, für dich auf dem Pi gespeichert. Mit verbundenem Simulator öffnet «Im Simulator ansehen» dasselbe im Simulator '
           '(Mehr → Bauen). Vor dem Druck des Unterteils die Masse des UPS HAT (E) mit Akkus nachmessen.</p></section>\n'),
    "en": ('<section id="case" data-icon="🛠"><h2>Build</h2><p>Everything to build MoveEye yourself is under More → <a href="/build"><b>Build</b></a> '
           '(formerly «Case &amp; build»), in tabs: Overview with the <b>3D workshop</b> (turn, zoom, explode, see through, inside, tap a part – '
           'runs in the browser, no simulator and no internet needed), Parts, Shopping (price estimate, shop search, CSV, print), Printing (per part, '
           'print files one by one or all), Assembly (14 steps, animated), Wiring (plan with pins and channels), Software, Commissioning, '
           'Troubleshooting and Maintenance. At the top the variant (v5.1 / v5.2, with / without battery, with / without mover) and <b>«My build»</b>: '
           'your checklist, saved for you on the Pi. With a connected simulator «View in the simulator» opens the same there (More → Build). '
           'Before printing the lower part, measure the UPS HAT (E) with its cells.</p></section>\n'),
    "fr": ('<section id="case" data-icon="🛠"><h2>Construire</h2><p>Tout pour construire MoveEye soi-même se trouve sous Plus → <a href="/build"><b>Construire</b></a> '
           '(avant «Boîtier et construction»), en onglets : Aperçu avec l\'<b>atelier 3D</b> (tourner, zoomer, éclater, transparent, intérieur, toucher '
           'une pièce – dans le navigateur, sans simulateur ni internet), Pièces, Achats (prix estimés, recherche, CSV, impression), Impression, '
           'Montage (14 étapes animées), Câblage (plan avec broches et canaux), Logiciel, Mise en service, Dépannage et Entretien. En haut la '
           'variante et <b>«Ma construction»</b> : ta liste, gardée pour toi sur le Pi. Avec un simulateur connecté, «Voir dans le simulateur» '
           'ouvre la même chose (Plus → Construire). Avant d\'imprimer la partie inférieure, mesurer l\'UPS HAT (E) avec ses accus.</p></section>\n'),
    "it": ('<section id="case" data-icon="🛠"><h2>Costruire</h2><p>Tutto per costruire MoveEye da sé si trova in Altro → <a href="/build"><b>Costruire</b></a> '
           '(prima «Custodia e costruzione»), in schede: Panoramica con l\'<b>officina 3D</b> (ruotare, zoomare, esploso, trasparente, interno, '
           'toccare un pezzo – nel browser, senza simulatore né internet), Pezzi, Acquisti (prezzi stimati, ricerca, CSV, stampa), Stampa, '
           'Montaggio (14 passi animati), Cablaggio (schema con pin e canali), Software, Messa in funzione, Risoluzione problemi e Manutenzione. '
           'In alto la variante e <b>«La mia costruzione»</b>: la tua lista, salvata per te sul Pi. Con un simulatore collegato «Vedere nel '
           'simulatore» apre lo stesso (Altro → Costruire). Prima di stampare la parte inferiore misurare l\'UPS HAT (E) con le batterie.</p></section>\n'),
    "rm": ('<section id="case" data-icon="🛠"><h2>Construir</h2><p>Tut per construir sez MoveEye è sut Dapli → <a href="/build"><b>Construir</b></a> '
           '(pli baud «Chascha e construcziun»), en tabs: Survista cun l\'<b>ufficina 3D</b> (rotar, zoomar, explosiun, transparent, intern, '
           'tutgar ina part – en il navigatur, senza simulatur ed internet), Parts, Cumpras (pretschs stimads, tschertga, CSV, stampar), Stampar, '
           'Muntadi (14 pass animads), Cablar (plan cun pins e chanals), Software, Messa en funcziun, Tschertgar sbagls e Mantegniment. '
           'Sura la variante e <b>«Mia construcziun»</b>: tia glista, memorisada per tai sin il Pi. Cun in simulatur connectà avra «Guardar en il '
           'simulatur» il medem (Dapli → Construir). Avant che stampar la part sut mesirar l\'UPS HAT (E) cun ils accus.</p></section>\n'),
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


if GUI_OK:                                                # the window: «Bauen» in the tab «Mehr» (572)
    _geh_tk_more_base = App._tk_more_bar

    def _geh_tk_more_bar(self, parent):
        f = _geh_tk_more_base(self, parent)
        i = len(f.grid_slaves())
        self._fbtn(f, "🛠 " + tr("Build yourself"), lambda: self._open_page("/build")).grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 6), pady=(0, 6))
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
    """problems: the simulator models / texts / the 3D files of the page against the source (only in the repository)"""
    import hashlib
    base = base or os.path.dirname(os.path.abspath(__file__))
    probs = []
    if not os.path.isfile(os.path.join(base, "hardware", "gehaeuse", "bau.json")):
        return probs
    sha = geh_quelle_sha(base)
    if sha != GEH_QUELLE_SHA:
        probs.append("quelle/639v is older than hardware/gehaeuse - run werkzeuge/gehaeuse_bauen.py --sim")
    if sha != BAU3D_QUELLE_SHA:
        probs.append("quelle/639vb is older than hardware/gehaeuse - run werkzeuge/gehaeuse_bauen.py --texte")
    with open(os.path.join(base, "hardware", "gehaeuse", "bau.json"), encoding="utf-8") as f_:
        bau = json.load(f_)
    for k in ("version", "bom", "schritte", "druckdateien", "verkabelung", "druck", "varianten"):
        if bau.get(k) != GEH_BAU.get(k):
            probs.append(f"GEH_BAU[{k}] differs from bau.json - run werkzeuge/gehaeuse_bauen.py --texte")
    dd = os.path.join(base, "hardware", "gehaeuse", "Druckdateien")
    for n in list(bau.get("druckdateien") or []) + list(bau.get("druckdateien_einzeln") or []):
        if not os.path.isfile(os.path.join(dd, n)):
            probs.append("print file missing: " + n)
    for rel, (h_, _b) in BAU3D.items():
        p = os.path.join(base, "werkzeuge", "three", rel)
        if os.path.isfile(p):
            with open(p, "rb") as f_:
                if hashlib.sha256(f_.read()).hexdigest() != h_:
                    probs.append(f"werkzeuge/three/{rel} differs from 639vb - gehaeuse_bauen.py --texte")
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
        if (man.get("dateien") or {}).get("gehaeuse.glb") != BAU3D_GLB[0]:
            probs.append("the model of the page /build (639vb) is not simulator3d/inhalte/gehaeuse/gehaeuse.glb - gehaeuse_bauen.py --texte")
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


def bau_infos_veraltet(base=None):
    """werkzeuge/bau_pruefen.py (only in the repository): do the build infos still fit the code / the case? -> list of warnings.
    Nothing is changed by itself - the warning only says «Bau-Infos veraltet: … – nachziehen?»"""
    import subprocess
    base = base or os.path.dirname(os.path.abspath(__file__))
    tool = os.path.join(base, "werkzeuge", "bau_pruefen.py")
    if not os.path.isfile(tool):
        return []
    try:
        r = subprocess.run([sys.executable, tool, "--json"], capture_output=True, text=True, timeout=60, cwd=base)
        return list(json.loads(r.stdout or "{}").get("warnungen") or [])
    except Exception as e:
        return ["bau_pruefen.py: " + str(e)[:120]]


def geh_selftest():
    B = GEH_BAU
    assert B.get("version") == "5.1" and len(B.get("schritte") or []) == 14, "data"
    bom = {b["id"] for b in B["bom"]}
    for t_ in B["teile"]:
        assert not t_.get("bom") or t_["bom"] in bom, t_["id"]
        assert not t_.get("schritt") or 1 <= t_["schritt"] <= 14, t_["id"]
    vals = {o["id"] for v in B["varianten"] for o in v["werte"]}
    T_ = {t_["id"]: t_ for t_ in B["teile"]}
    assert (B.get("variante_standard") or {}).get("gehaeuse") == "v52" and "v51" in vals, "real-v52-standard: v5.2 is the standard, v5.1 stays"
    for t_ in B["teile"]:                         # the parts of a variant are in the assembly steps, at the step of the part they replace
        if t_.get("art") in ("v52", "dev"):
            assert t_.get("schritt"), ("step", t_["id"])
            assert not t_.get("ersetzt") or T_[t_["ersetzt"]].get("schritt") == t_["schritt"], ("step of the replaced part", t_["id"])
    for b in B["bom"]:
        assert isinstance(b.get("preis"), (int, float)) and b.get("haendler") in B["haendler"], ("price / shop", b["id"])
        assert not b.get("wenn") or b["wenn"] in vals, ("variant", b["id"])
    K = B["verkabelung"]["knoten"]
    for v in B["verkabelung"]["verbindungen"]:
        assert v["von"] in K and v["nach"] in K and (not v.get("wenn") or v["wenn"] in vals), ("wiring", v["id"])
    assert {p["datei"] for p in B["druck"]["teile"]} >= {t_["datei"] for t_ in B["teile"] if t_.get("datei")}, "every print part in the print table"
    fk = geh_fk()
    assert set(fk) == set(B["fehlersuche"]), "troubleshooting ids in the error catalogue: " + str(set(B["fehlersuche"]) - set(fk))
    for k in GEH_KEYS:
        assert DE.get(k), k
        for L in ("fr", "it", "rm"):
            assert TRX[L].get(k), (L, k)
    assert 'href="/build"' in MORE_PAGE and MORE_PAGE.index('href="/build"') < MORE_PAGE.index('id="m-info"'), "Mehr"
    html = geh_page()
    for x in ("/api/bau", '"schritte"', "/build/gehaeuse.glb", "importmap", "/bau3d/three.module.min.js", '"HW_PCA9685"', "Raspberry Pi 5"):
        assert x in html, x
    assert "<!--NAV-->" not in html and "/*GEH" not in html
    import gzip
    for k in list(BAU3D) + ["glb"]:
        raw = gzip.decompress(bau3d_bytes(k))
        assert hashlib.sha256(raw).hexdigest() == (BAU3D_GLB[0] if k == "glb" else BAU3D[k][0]), k
    assert gzip.decompress(bau3d_bytes("three.module.min.js")).startswith(b"/**") and bau3d_bytes("x.js") is None
    assert HELP_PAGE.count('<section id="case"') == 2 and all('href="/build"' in (HELP_X.get(L) or "href=\"/build\"") for L in ("fr", "it", "rm")), "manual"
    keep = CFG.get("sim_on"), CFG.get("bau_mein")
    _sc, _ss = globals()["sim_control"], globals()["save_settings"]
    asked = []
    try:
        globals()["save_settings"] = lambda: None
        CFG["bau_mein"] = {}
        assert bau_mein_set("anna", {"gehaeuse": "v52", "akku": "x"}, ["m:3", "e:pi5", "bad id", 7]) and bau_mein_get("anna") == {"var": {"gehaeuse": "v52"}, "done": ["e:pi5", "m:3"]}
        assert bau_mein_get("admin") == {"var": {}, "done": []} and not bau_mein_set("anna", None, "x"), "per user"
        assert "/api/bau" in VIEW_POST and role_allows("view", "/api/bau", "GET", {}) and role_allows("view", "/build", "GET", {}), "rights"
        CFG["sim_on"] = False
        r = geh_do({"do": "sim"})
        assert not r["ok"] and r.get("offline"), r
        assert "const SIM_ON = false" in geh_page() and "/build/gehaeuse.glb" in geh_page(), "the 3D view does not need the simulator"
        assert geh_do({"do": "x"}).get("code") == 400
        CFG["sim_on"] = True
        globals()["sim_control"] = lambda d_: (asked.append(d_), {"ok": True, "open": True, "step": int(d_.get("n", 0)), "steps": 14})[1]
        assert geh_do({"do": "sim"})["ok"] and asked[-1] == {"action": "werkstatt", "do": "open"}
        assert geh_do({"do": "sim", "step": 4})["ok"] and asked[-1] == {"action": "werkstatt", "do": "step", "n": 4}
        globals()["sim_control"] = lambda d_: {"ok": False, "error": "unknown action"}
        assert not geh_do({"do": "sim"})["ok"]                       # an older simulator without the workshop
    finally:
        globals()["sim_control"], globals()["save_settings"] = _sc, _ss
        CFG["sim_on"], CFG["bau_mein"] = keep
    more = (UI_GEMEINSAM.get("more") or [])
    case = next((m for m in more if m.get("id") == "build"), None)
    assert case and case["mw"]["href"] == "/build" and case["mw"]["key"] == "Build yourself" and "case" in case.get("alias", []), "ui_gemeinsam.json more/build"
    for L in ("de", "fr", "it", "rm"):
        assert ui_gem_tr("Build yourself", L) == case["mw"]["names"][L], ("name", L)
    assert case["mw"]["names"]["de"] == case["sim"]["names"]["de"] == "Bauen", "the same name in both"
    mg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "scripts", "mehr.gd")
    if os.path.isfile(mg):
        with open(mg, encoding="utf-8") as f_:
            assert '["%s", "%s", "%s"' % (case["sim"]["row"], case["draw"], case["sim"]["key"]) in f_.read(), "simulator mehr.gd row"
    node = shutil.which("node")
    if node:                                              # the scripts of the page: the classic one and the module
        import tempfile
        for i, (typ, js) in enumerate(re.findall(r'<script( type="module")?>(.*?)</script>', html, re.S)):
            with tempfile.NamedTemporaryFile("w", suffix=".mjs" if typ else ".js", delete=False) as f_:
                f_.write(js)
            r = subprocess.run([node, "--check", f_.name], capture_output=True, text=True)
            os.remove(f_.name)
            assert r.returncode == 0, f"/build script {i}: {(r.stderr or '').strip()[-300:]}"
    probs = geh_check()
    assert not probs, " | ".join(probs)
    warn = bau_infos_veraltet()
    if warn:                                              # a warning, no error: nothing is changed by itself
        return "WARNING – " + " · ".join(tr("Build info out of date: %s – update it?") % w for w in warn[:4])
    return "Build: page /build (10 tabs, 3D without simulator), My build per user, models = source, build infos fit the code"


SELFTEST_EXTRA.append(("Build (page /build, 3D in the browser, My build, models = source, build infos)", geh_selftest))
