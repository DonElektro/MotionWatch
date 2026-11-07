#@ MoveEye – Teil 639w: Seite «Bauen» (/build, Mehr → Bauen; früher «Gehäuse & Bau» /case, leitet weiter): MoveEye komplett selbst bauen – 10 Reiter Übersicht · Teile · Einkauf · Drucken · Montage · Verkabeln · Software · Inbetriebnahme · Fehlersuche · Wartung, 3D-Werkstatt im Browser (three.js lokal, ohne Simulator), Varianten, «Mein Bau» pro Benutzer (/api/bau), Druckdateien (/build/datei, alle als ZIP), Knopf «Im Simulator ansehen» nur mit verbundenem Simulator; Eintrag im Fenster (Reiter Mehr); Selbsttest: Modelle = Quelle, Bau-Infos aktuell (Warnung). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «real-gehaeuse» (01.11.2026), ausgebaut im Paket «real-bauen» (01.11.2026, Besitzer: «ein Bediener kann MoveEye komplett
# selbst bauen»). Eine Quelle: hardware/gehaeuse/bau.json (Teile, Materialliste mit Preis-Schätzung und Händler-Suche, Montage,
# Drucken, Werkzeug, Sicherheit, Verkabeln, Software, Inbetriebnahme, Fehlersuche, Wartung, Varianten – 5 Sprachen).
# werkzeuge/gehaeuse_bauen.py --texte macht daraus 639v (GEH_BAU, Texte), 639vb (three.js r160 + gehaeuse.glb, gepackt) und die
# Daten des Simulators (werkstatt_daten.gd). Besitzer (01.11.2026): die 3D-Werkstatt in MoveEye geht OHNE Simulator – MoveEye
# liefert three.js, das Modell und die Daten selbst aus (auch offline); «Im Simulator ansehen» ist nur ein Zusatz.
#   * /build: Seite (Reiter Mehr «Bauen»), Reiter über #uebersicht … #wartung; /case leitet auf /build weiter (alte Links).
#   * /bau3d/<pfad>: three.js (gzip), /build/gehaeuse.glb: das Modell (gzip), /build/qr.svg: QR-Code zu dieser MoveEye-Seite.
#   * /build/datei/<name>: eine Druckdatei (3MF) aus hardware/gehaeuse/Druckdateien/ – auf dem Pi ohne Repository holt MoveEye
#     sie selbst von GitHub (Cache ~/.config/motionwatch/druck_cache/, real-download-fix); /build/alle.zip?var=v52|v51: die
#     Druckdateien der gewählten Variante mit LIESMICH.txt als MoveEye_v5-2_Druck_X.Y.Z.zip.
#   * /api/bau: «Mein Bau» – GET {var, done}, POST {var?, done?}: Variante und erledigte Schritte pro Benutzer (wie «Meine
#     Ansicht», CFG bau_mein), auf allen Geräten gleich.
#   * /api/case: GET = ob der Simulator verbunden ist; POST {do: "sim", step?} -> Simulator /control werkstatt (wie bisher).
#   * Mehr (525) und das Fenster (572 _tk_more_bar): ein Eintrag «Bauen». Gemeinsame Menü-Datei: «more» -> build
#     (simulator3d/ui_gemeinsam.json; im Simulator heisst derselbe Eintrag «Bauen», mehr.gd, Fenster werkstatt.gd mit denselben Reitern).
#   * «Fertig kaufen» (Besitzer 01.11.2026, Teil 639zj): schmaler Hinweis ganz oben (#g-fertig), Paket wählen, «Fertig bestellen
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
    <div class="gc mut" data-i18n="Own work of Elektro – parametric Python model.">Own work of Elektro – parametric Python model.</div>
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
    <div class="gc gtop" id="g-qrbox"><img class="qr" src="/build/qr.svg" alt="QR"><div class="gt"><b data-i18n="QR code to this MoveEye page">QR code to this MoveEye page</b><div class="mut" id="g-url"></div></div></div></section>
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
window.BV = {explode: 0, xray: false, inner: true, v52: ["v52", "v53"].includes(G.var.gehaeuse), v53: G.var.gehaeuse === "v53", dev: G.var.akku === "entwicklung", step: 0, sel: "", api: null};   // real-v52-standard: v5.2 is the standard (bau.json variante_standard)
function bv(what, a) { if (BV.api && BV.api[what]) BV.api[what](a); }
// real-gehaeuse-v53: v5.3 builds on v5.2 – «wenn: v52» holds for v5.3 too, «wenn: v53» only for v5.3
const isV53 = () => G.var.gehaeuse === "v53";
const ok = w => !w || Object.values(G.var).includes(w) || (w === "v52" && isV53());
const okp = p => ok(p.wenn) && !(p.nicht && Object.values(G.var).includes(p.nicht));   // print parts: «nicht» = replaced in that variant
const TEIL = {}; (GB.teile || []).forEach(x => TEIL[x.id] = x);
const BOM = {}; (GB.bom || []).forEach(b => BOM[b.id] = b);
const isV52 = () => G.var.gehaeuse === "v52" || isV53();   // v5.2 or a version built on it (v5.3)
const GDIR = () => isV53() ? "v5-3/" : isV52() ? "v5-2/" : "";          // the folder of the print files of the chosen case
const GVT = () => isV53() ? "5.3" : isV52() ? "5.2" : "5.1";
const GVAR = () => isV53() ? "v53" : isV52() ? "v52" : "v51";
const dirOf = f => (String(f).match(/^v5-\d\//) || [""])[0];
const GEH_VER = /*GEHVER*/"";                          // real-abgleich-v52: «Stand MoveEye X.Y.Z» from APP_VERSION (not in bau.json)
// real-werkstatt-standalone: the same page as one file without the Pi (werkzeuge/werkstatt_html.py, geh_page(off=…)):
// window.MW_OFFLINE = {raw, kit, glb} – no /api/…, «My build» only in this browser, print files and ZIPs from GitHub (internet)
const GEH_OFF = window.MW_OFFLINE || null;
// the texts of an assembly step: v5.2 (standard) or the v5.1 texts when v5.1 is chosen (bau.json «v51»)
const sv = s => (isV53() && s.v53) ? Object.assign({}, s, s.v53) : (!isV52() && s.v51) ? Object.assign({}, s, s.v51) : s;
// the 3MF of a print part: v5.2 -> Druckdateien/v5-2/ (also for parts that exist only there), else the v5.1 file
function pfile(datei) {
  const all = GB.druckdateien_einzeln || [], f1 = "MoveEye_v5-1_" + datei + ".3mf", f2 = "v5-2/MoveEye_v5-2_" + datei + ".3mf", f3 = "v5-3/MoveEye_v5-3_" + datei + ".3mf";
  if (all.includes(f3) && (isV53() || (!all.includes(f2) && !all.includes(f1)))) return f3;   // v5.3: Druckdateien/v5-3/
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
    if (GEH_OFF) { G.server = false; gProg(); return; }
    try { const r = await post("/api/bau", d); G.server = !!(r && r.ok); } catch (e) { G.server = false; }
    gProg();
  }, 700);
}
async function gLoad() {
  if (!GEH_OFF) try { const r = await (await fetch("/api/bau")).json(); if (r && r.ok) { G.server = true; if (r.var && Object.keys(r.var).length) G.var = Object.assign(G.var, r.var); G.done = new Set(r.done || []); return; } } catch (e) {}
  try { const d = JSON.parse(localStorage.getItem("mwbau") || "{}"); if (d.var) G.var = Object.assign(G.var, d.var); G.done = new Set(d.done || []); } catch (e) {}
}
function allIds() {
  const ids = [];
  (GB.bom || []).forEach(b => { if (ok(b.wenn) && !b.optional) ids.push("e:" + b.id); });
  ((GB.druck || {}).teile || []).forEach(p => { if (okp(p)) ids.push("d:" + p.datei); });
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
  document.getElementById("g-save").textContent = G.server ? t("Saved for you on the Pi – the same on every device.") : GEH_OFF ? t("Saved only in this browser (offline version).") : t("Saved only on this device (no connection to the Pi).");
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
  const sum = bom.reduce((a, b) => a + (b.preis || 0), 0), hrs = ((GB.druck || {}).teile || []).filter(okp).reduce((a, p) => a + p.zeit_h, 0);
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
  const a = el("a"); a.href = URL.createObjectURL(blob); a.download = "MoveEye_Einkauf_v" + GVT() + (GEH_VER ? "_" + GEH_VER : "") + ".csv"; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
// real-download-fix: a normal link (no fetch, no «download» attribute - the iPhone only half supports it); each part of the path
// coded by itself (v5-2/… stays a folder); MoveEye sends the file itself with Content-Disposition and the base name
function fileLink(f, label) { const a = el("a", "", "⬇ " + (label || f.split("/").pop()) + (GEH_OFF ? " 🌐" : "")); a.href = (GEH_OFF ? GEH_OFF.raw : "/build/datei/") + f.split("/").map(encodeURIComponent).join("/"); if (GEH_OFF) { a.target = "_blank"; a.rel = "noopener"; a.title = t("Needs internet (GitHub)"); } return a; }
function gPrint() {
  const D = GB.druck || {}, tb = document.getElementById("g-print"); tb.textContent = "";
  const hd = el("tr"); ["", t("Part"), t("pcs"), t("Infill"), t("Walls"), t("Supports"), t("Layer"), t("lies on"), t("Print time"), ""].forEach((x, i) => hd.appendChild(el("th", i > 5 && i < 9 ? "hide-s" : "", x))); tb.appendChild(hd);
  let hrs = 0;
  (D.teile || []).filter(okp).forEach(p => {   // parts of a variant (e.g. v5.2) come from the data by themselves
    const tr = el("tr"), c0 = el("td"); c0.appendChild(chk("d:" + p.datei)); hrs += p.zeit_h;
    const nm = (GB.teile || []).find(x => x.datei === p.datei), dl = el("td", "lk"); dl.appendChild(fileLink(pfile(p.datei), "3MF"));
    tr.append(c0, el("td", "", nm ? gx(nm.name).replace(/^\d+ /, "") : p.datei), el("td", "q", "× " + p.stueck), el("td", "q", p.fuellung + " %"), el("td", "q", String(p.waende)),
      el("td", "q", p.stuetzen ? "✓" : t("none")), el("td", "q hide-s", p.schicht + " mm" + (p.brim ? " · Brim " + p.brim + " mm" : "")), el("td", "n hide-s", gx(p.liegt)), el("td", "q hide-s", fmt(t("about %s h"), p.zeit_h)), dl);
    tb.appendChild(tr);
  });
  const tr = el("tr", "gh"), a = el("td", "", t("Print time") + ": " + fmt(t("about %s h"), Math.round(hrs * 10) / 10) + " · " + gx(D.zeit_hinweis)); a.colSpan = 10; tr.appendChild(a); tb.appendChild(tr);
  const ul = document.getElementById("g-phint"); ul.textContent = ""; (D.hinweise || []).forEach(h => ul.appendChild(el("li", "", gx(h))));
  const fl = document.getElementById("g-files"); fl.textContent = "";
  const all = el("a", "", "⬇ " + t("All print files (ZIP)") + " · v" + GVT()); all.href = "/build/alle.zip?var=" + GVAR();
  if (GEH_OFF) { all.textContent = "⬇ " + t("Complete kit package (GitHub)") + " 🌐"; all.href = GEH_OFF.kit; all.target = "_blank"; all.rel = "noopener"; }   // offline: everything in the kit package
  const kit = el("a", "", t("Complete kit package (GitHub)")); kit.href = GB.github + "/releases/latest/download/MoveEye_Bausatz.zip"; kit.target = "_blank"; kit.rel = "noopener";
  const kh = el("div", "mut", t("Without the repository MoveEye fetches the files from GitHub itself (the first time takes about a minute). Everything in one package:") + " "); kh.appendChild(kit);
  if (GEH_OFF) { kh.textContent = "🌐 " + t("The print files come from GitHub – this needs internet. Everything else on this page works offline."); }
  fl.append(all, kh, el("h3", "", t("Plates for the X2D (everything on 2 plates)")));
  (GB.druckdateien || []).filter(f => dirOf(f) === GDIR()).forEach(f => fl.appendChild(fileLink(f)));   // the plates of the chosen case
  fl.appendChild(el("h3", "", t("Single parts (3MF)"))); (GB.druckdateien_einzeln || []).filter(f => {
    const datei = f.replace(/^(v5-\d\/)?MoveEye_v5-\d_/, "").replace(/\.3mf$/, ""), p = (D.teile || []).find(x => x.datei === datei);
    return p ? okp(p) && pfile(datei) === f : dirOf(f) === GDIR();
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
    if (s.link && s.link !== "qr" && !(GEH_OFF && s.link.startsWith("/"))) { const a = el("a", "", "↗ " + t("Open")); a.href = s.link; tx.appendChild(a); }
    ol.appendChild(li);
  });
  document.getElementById("g-url").textContent = location.origin + "/";
  document.getElementById("g-qrbox").hidden = !!GEH_OFF;   // offline: no MoveEye page to point to
  const ib = document.getElementById("g-ib"); ib.textContent = "";
  (GB.inbetriebnahme || []).forEach((s, i) => {
    const li = stepLi(i + 1, s, "i:" + i, false);
    if (s.link && !GEH_OFF) { const b = el("button", "", "↗ " + t("Open")); b.type = "button"; b.onclick = () => { location.href = s.link; }; li.appendChild(b); }
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
    if (!GEH_OFF) { const a = el("a", "", "↗ " + t("Open help")); a.href = "/hilfe/fehler/" + id; d.appendChild(a); }
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
  BV.v52 = isV52(); BV.v53 = isV53(); BV.dev = G.var.akku === "entwicklung"; bv("paint");
  if (BV.v52) document.getElementById("g-ver").textContent = GVT();
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
  if (!GEH_OFF) try { const r = await (await fetch("/api/case")).json(); document.getElementById("g-simbox").style.display = r && r.sim ? "" : "none"; } catch (e) {}
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
const X = {};                                          // 639wc: single part / print plates (paint, after, tap, reset)
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
function render() { renderer.render(scene, cam); if (X.after) X.after(); }
function size() { const w = box.clientWidth || 300, h = box.clientHeight || 260; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); render(); }
new ResizeObserver(size).observe(box);
ctl.addEventListener("change", render);
const row = id => (GB.teile || []).find(x => x.id === id) || {};
const REPL = {}; (GB.teile || []).forEach(x => { if (x.ersetzt) REPL[x.ersetzt] = x.id; });
function shown(id) {
  const r = row(id), art = r.art || "", s = B.step;
  if (art === "v52" && !B.v52) return false;           // real-v52-standard: v5.2 parts in every step (bau.json «schritt»)
  if (art === "v53" && !B.v53) return false;           // real-gehaeuse-v53: the parts of v5.3 (lower part, lid, hatch, duct, holder)
  if (art === "dev" && !B.dev) return false;           // development: socket 13 instead of the UPS HAT
  if (r.ohne) return false;                            // 12 blind plug: only in the scene (device without the wide camera)
  const by = REPL[id];                                 // replaced by the part of the chosen variant (lower part v5.2, socket ...)
  if (by && parts[by] && ((row(by).art === "v52" && B.v52) || (row(by).art === "v53" && B.v53) || (row(by).art === "dev" && B.dev))) return false;
  const pr = art === "druck" || !!r.datei;
  if (s === 1) return pr;
  if (s > 1 && (r.schritt || 0) > s) return false;
  if (!B.inner && !pr && !(E[id] || {}).aussen) return false;
  return true;
}
const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
function paint() {
  if (B.mode && X.paint) { X.paint(); return; }           // 639wc: a single part or a print plate
  if (X.reset) X.reset();
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
  if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 6) {
    if (B.mode) { if (X.tap) X.tap(e); } else { B.sel = pick(e); B.onSelect && B.onSelect(B.sel); paint(); } }
  down = null;
});
new GLTFLoader().load((window.MW_OFFLINE || {}).glb || "/build/gehaeuse.glb", g => {
  const FB = GB.farben || {}, farbe = id => (row(id) || {}).farbe || FB[id] || ((FB.grau_teile || []).includes(id) && FB.grau) || (E[id] || {}).farbe || "";   // colours from the data (bau.json / modelle.json), else the model's
  g.scene.traverse(o => { if (o.isMesh) { o.material = o.material.clone(); o.material.side = THREE.DoubleSide; o.material.roughness = 0.6; o.material.metalness = 0;
    if (farbe(o.name)) o.material.color.set(farbe(o.name)); parts[o.name] = {mesh: o}; } });
  scene.add(g.scene); msg.textContent = ""; size(); view(145, 24, 0.5); step(B.step);
  window.BV_READY = Object.keys(parts).length;
}, undefined, e => { msg.textContent = "3D: " + (e && e.message || e); });
B.api = {paint, step, resize: size, select: id => { B.sel = id; B.onSelect && B.onSelect(id); paint(); }, reset: () => { B.explode = 0; document.getElementById("v-exp").value = 0; view(145, 24, 0.5); paint(); }};
/*GEHEINZEL3D*/
size(); view(145, 24, 0.5);
}
"""
GEH_DL_TX = {                                             # real-download-fix: EN -> (de, fr, it, rm)
    "The print file is not on this MoveEye and could not be fetched from the internet (no connection?). Try again later, or load the complete kit package.": (
        "Die Druckdatei liegt nicht auf diesem MoveEye und konnte nicht aus dem Internet geholt werden (keine Verbindung?). Später nochmals versuchen oder das komplette Bausatz-Paket laden.",
        "Le fichier d'impression n'est pas sur ce MoveEye et n'a pas pu être téléchargé (pas de connexion ?). Réessayer plus tard ou charger le kit complet.",
        "Il file di stampa non è su questo MoveEye e non è stato possibile scaricarlo (nessuna connessione?). Riprovare più tardi o scaricare il kit completo.",
        "La datoteca da stampa n'è betg sin quest MoveEye e n'ha betg pudì vegnir chargiada da l'internet (nagina colliaziun?). Empruvar pli tard u chargiar il pachet cumplet."),
    "The print files are being fetched from the internet (%d of %d). This page tries again by itself; you can also tap «Try again».": (
        "Die Druckdateien werden aus dem Internet geholt (%d von %d). Diese Seite versucht es selbst nochmals; du kannst auch «Nochmals versuchen» tippen.",
        "Les fichiers d'impression sont en cours de téléchargement (%d sur %d). Cette page réessaie d'elle-même ; vous pouvez aussi toucher «Réessayer».",
        "I file di stampa vengono scaricati da internet (%d di %d). Questa pagina riprova da sola; puoi anche toccare «Riprova».",
        "Las datotecas da stampa vegnan chargiadas da l'internet (%d da %d). Questa pagina emprova sezza anc ina giada; ti pos er tutgar «Empruvar anc ina giada»."),
    "Try again": ("Nochmals versuchen", "Réessayer", "Riprova", "Empruvar anc ina giada"),
    "Complete kit package (GitHub)": ("Komplettes Bausatz-Paket (GitHub)", "Kit complet (GitHub)", "Kit completo (GitHub)", "Pachet cumplet (GitHub)"),
    "Back to Build": ("Zurück zu Bauen", "Retour à Construire", "Torna a Costruire", "Enavos tar Construir"),
    "The print file is too big.": ("Die Druckdatei ist zu gross.", "Le fichier d'impression est trop grand.", "Il file di stampa è troppo grande.", "La datoteca da stampa è memia gronda."),
    "MoveEye print files – case %s – as of MoveEye %s": ("MoveEye Druckdateien – Gehäuse %s – Stand MoveEye %s", "Fichiers d'impression MoveEye – boîtier %s – état MoveEye %s",
        "File di stampa MoveEye – custodia %s – stato MoveEye %s", "Datotecas da stampa MoveEye – chascha %s – stadi MoveEye %s"),
    "folder": ("Ordner", "dossier", "cartella", "ordinatur"),
    "Without the repository MoveEye fetches the files from GitHub itself (the first time takes about a minute). Everything in one package:": (
        "Ohne Repository holt MoveEye die Dateien selbst von GitHub (beim ersten Mal rund eine Minute). Alles in einem Paket:",
        "Sans dépôt, MoveEye télécharge lui-même les fichiers depuis GitHub (la première fois environ une minute). Tout en un paquet :",
        "Senza repository MoveEye scarica i file da GitHub da solo (la prima volta circa un minuto). Tutto in un pacchetto:",
        "Senza repository chargia MoveEye las datotecas sez da GitHub (l'emprima giada var ina minuta). Tut en in pachet:"),
    # real-werkstatt-standalone: the offline file (werkzeuge/werkstatt_html.py)
    "Needs internet (GitHub)": ("Braucht Internet (GitHub)", "Nécessite internet (GitHub)", "Richiede internet (GitHub)", "Basegna internet (GitHub)"),
    "Saved only in this browser (offline version).": ("Nur in diesem Browser gespeichert (Offline-Version).", "Enregistré seulement dans ce navigateur (version hors ligne).",
        "Salvato solo in questo browser (versione offline).", "Memorisà mo en quest navigatur (versiun offline)."),
    "The print files come from GitHub – this needs internet. Everything else on this page works offline.": (
        "Die Druckdateien kommen von GitHub – dafür braucht es Internet. Alles andere auf dieser Seite geht offline.",
        "Les fichiers d'impression viennent de GitHub – il faut internet. Tout le reste de cette page fonctionne hors ligne.",
        "I file di stampa arrivano da GitHub – serve internet. Tutto il resto di questa pagina funziona offline.",
        "Las datotecas da stampa vegnan da GitHub – per quai basegni internet. Tut il rest da questa pagina funcziuna offline."),
    "Ready-made? Request on the MoveEye homepage": ("Fixfertig kaufen? Anfrage auf der MoveEye-Homepage", "Tout prêt ? Demande sur le site de MoveEye",
        "Già pronto? Richiesta sul sito di MoveEye", "Cumplettamain pront? Dumonda sin la pagina d'internet da MoveEye"),
    "Offline version": ("Offline-Version", "Version hors ligne", "Versione offline", "Versiun offline"),
}
for _k, _v in GEH_DL_TX.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX.setdefault(_L, {}).setdefault(_k, _v[_i + 1])
GEH_KEYS = sorted(set(GEH_UI_DE) | set(GEH_UI2_DE) | {k for _i, k in BAU_TABS} | {"Complete kit package (GitHub)", "Needs internet (GitHub)",
    "Saved only in this browser (offline version).", "The print files come from GitHub – this needs internet. Everything else on this page works offline.", "Offline version", "Ready-made? Request on the MoveEye homepage",
    "Without the repository MoveEye fetches the files from GitHub itself (the first time takes about a minute). Everything in one package:"} | {
    "Case", "Step", "Name", "Opened in the simulator.", "Simulator not connected – start it and connect it on the page Simulator."})


def geh_fk():
    """the entries of the error catalogue (639u) the tab «Fehlersuche» shows: title, text, steps in 5 languages"""
    es = {e["id"]: e for e in (FEHLER_KATALOG.get("fehler") or [])}
    return {i: {k: es[i].get(k) for k in ("titel", "text", "schritte", "stufe")} for i in GEH_BAU.get("fehlersuche") or [] if i in es}


def geh_page(off=None):
    """the page /build; off = {"raw", "kit", "glb", "imports"}: the same page as one file without the Pi (geh_render_off)"""
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in GEH_KEYS}, ensure_ascii=False) + ");"
    J = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    return ((geh_render_off(GEH_PAGE, off) if off else render_page(GEH_PAGE, "more")).replace("/*GEHDE*/", js, 1).replace("/*GEHBAU*/null", J(GEH_BAU), 1)
            .replace("/*GEHFK*/null", J(geh_fk()), 1).replace("/*GEHM3*/null", J(BAU3D_MODELLE), 1)
            .replace("/*GEHVER*/\"\"", json.dumps(APP_VERSION), 1)
            .replace("/*GEHSIM*/false", "true" if CFG.get("sim_on") else "false", 1)
            .replace("/*GEHTABS*/", J([list(x) for x in BAU_TABS])).replace("/*GEH3D*/", GEH_3D_JS, 1)
            .replace("/*GEHFERTIG*/", fertig_js(), 1))                       # «Fertig kaufen» (639zj): the hint at the top


def geh_render_off(page, off):
    """real-werkstatt-standalone: like render_page, but for a file opened by double-click (file://, no Pi, no internet):
    base CSS and COMMON_JS, the language menu with the translations of all five languages inside, no menu bar, no alerts,
    no calls to the Pi (fetch of a Pi address answers at once: /api/appearance = language of the browser, else «offline»),
    three.js and the model from `off` (data URLs), window.MW_OFFLINE for the page (639w GEH_OFF)."""
    import base64
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    probe = page + COMMON_JS + GEH_3D_JS + str(globals().get("GEH_EINZEL_JS", "")) + str(globals().get("GEH_EINZEL_3D", "")) + fertig_js()
    keys = set(GEH_KEYS) | set(re.findall(r'data-i18n="([^"]+)"', page)) | {k for k in TRX.get("fr", {}) if '"' + k + '"' in probe}
    trx = {L: {k: TRX.get(L, {})[k] for k in sorted(keys) if TRX.get(L, {}).get(k)} for L in ("fr", "it", "rm")}
    cfg = {k: off[k] for k in ("home", "raw", "kit", "glb") if off.get(k)}
    head = ("<script>window.MW_OFFLINE=" + J(cfg) + ";window.I18NXA=" + J(trx) + ";\n" + LANG_JS.replace("</", "<\\/") + "\n"
            "(function(){var l='';try{l=localStorage.getItem('mw-lang')||'';}catch(e){}"
            "var nl=((navigator.language||'de').slice(0,2)||'de').toLowerCase();if(['de','fr','it','rm','en'].indexOf(nl)<0)nl='en';"
            "window.I18NX=window.I18NXA[l||nl]||null;window.LX=function(s){var d=window.I18NX;return (d&&d[s])||'';};"
            "var f0=window.fetch;window.fetch=function(u,o){var s=String((u&&u.url)||u||'');"
            "if(/^\\/[^\\/]/.test(s)){if(s.indexOf('/api/appearance')===0)return Promise.resolve(new Response(JSON.stringify({lang:nl,theme:'dark'}),{headers:{'Content-Type':'application/json'}}));"
            "return Promise.reject(new TypeError('offline: '+s));}return f0.apply(this,arguments);};})();</script>")
    imp = '<script type="importmap">' + J({"imports": off.get("imports") or {}}) + "</script>"
    page = re.sub(r'<script type="importmap">.*?</script>', lambda m_: imp, page, count=1, flags=re.S)
    page = page.replace("<head>", "<head>" + head, 1).replace('<img class="qr" src="/build/qr.svg" alt="QR">', "", 1)
    page = page.replace("<!--NAV-->", '<span class="badge" style="font-size:11px" data-i18n="Offline version">Offline version</span>', 1)
    page = re.sub(r"(<h1[^>]*>)MoveEye</h1>", r'\1MoveEye <span class="ver">' + APP_VERSION + "</span></h1>", page, count=1)
    ico = "data:image/png;base64," + base64.b64encode(app_icon_png(64)).decode()     # the app icon (header, tab) inside
    page = page.replace("</head>", str(globals().get("SX_NIGHT_CSS", "")) + '<link rel="icon" type="image/png" href="' + ico + '">'
                        "<style>:root{--mw-icon:url(" + ico + ")}</style></head>", 1)
    return page.replace("/*BASECSS*/", BASE_CSS).replace("/*COMMON*/", COMMON_JS).replace("/*ALERTS*/", "")


def geh_offline_html(homepage=""):
    """-> the whole workshop «Bauen» as one HTML file (werkzeuge/werkstatt_html.py): three.js and gehaeuse.glb inside as data URLs,
    the print files from GitHub (GEH_DRUCK_RAW), «All» = the kit package of the latest release (GEH_BAUSATZ_URL)"""
    import base64
    import gzip
    du = lambda b_, mt: "data:" + mt + ";base64," + base64.b64encode(b_).decode()
    src = {k: gzip.decompress(bau3d_bytes(k)).decode("utf-8") for k in BAU3D}
    # GLTFLoader imports «../utils/BufferGeometryUtils.js»: a data URL has no folder -> the name from the import map
    src = {k: v.replace("'../utils/BufferGeometryUtils.js'", "'three/addons/utils/BufferGeometryUtils.js'") for k, v in src.items()}
    imports = {("three" if k == "three.module.min.js" else "three/addons/" + k): du(v.encode("utf-8"), "text/javascript") for k, v in src.items()}
    home = str(homepage or (globals().get("FERTIG") or {}).get("homepage_url") or "")   # empty: the hint without a link
    off = {"home": home if home.startswith("https://") else "", "raw": GEH_DRUCK_RAW, "kit": GEH_BAUSATZ_URL, "glb": du(gzip.decompress(bau3d_bytes("glb")), "model/gltf-binary"), "imports": imports}
    return geh_page(off=off)


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


# ---- real-download-fix (01.11.2026): print files on the Pi without the repository ------------------------------------------
# Safari on the iPhone showed «Load failed»: the Pi has no hardware/gehaeuse/Druckdateien/ and redirected to GitHub (302 ->
# github.com/raw -> raw.githubusercontent). Now MoveEye fetches the file itself (update network functions, proxy from the
# environment, GitHub key only for GitHub), checks the size, keeps it in ~/.config/motionwatch/druck_cache/ (renewed per
# version with the ETag) and sends it itself with «Content-Disposition: attachment; filename=<base name>». Only names of
# geh_druck_namen() (no path tricks). /build/alle.zip?var=v52|v51: the files of the chosen case + LIESMICH.txt, named
# MoveEye_v5-2_Druck_X.Y.Z.zip; takes it too long, the rest is fetched in the background and the page tries again
# (hint to the kit package MoveEye_Bausatz.zip of the releases).
GEH_DRUCK_RAW = "https://raw.githubusercontent.com/DonElektro/MotionWatch/main/hardware/gehaeuse/Druckdateien/"
GEH_DRUCK_MAX = 30 * 1024 * 1024                          # one print file (the biggest plate has ~6.5 MB)
GEH_ZIP_BUDGET = 45.0                                     # seconds /build/alle.zip may fetch before it answers «try again»
GEH_BAUSATZ_URL = "https://github.com/DonElektro/MotionWatch/releases/latest/download/MoveEye_Bausatz.zip"
_GEH_DL_LOCK = threading.Lock()
_GEH_DL_NAME_LOCKS = {}
_GEH_DL_BG = {"run": False}


def geh_cache_dir():
    return os.path.join(DATA_DIR, "druck_cache")


def geh_cache_file(name):
    return os.path.join(geh_cache_dir(), name.replace("/", "__"))


def _geh_meta(write=None):
    p = os.path.join(geh_cache_dir(), "cache.json")
    if write is None:
        try:
            with open(p, encoding="utf-8") as f_:
                m = json.load(f_)
            return m if isinstance(m, dict) else {}
        except (OSError, ValueError):
            return {}
    os.makedirs(geh_cache_dir(), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f_:
        json.dump(write, f_)
    os.replace(tmp, p)


def geh_base_name(name):
    return name.rsplit("/", 1)[-1]


def geh_druck_holen(name, timeout=30):
    """the path of a print file: the repository, else the cache, else fetched from GitHub -> (path, None) or (None, reason);
    reason: unknown | offline | too big | bad file | <HTTP code>. An older cached file is used when the internet is gone."""
    import http.client
    import urllib.error
    from urllib.parse import quote
    if name not in geh_druck_namen() or ".." in name or name.startswith("/") or "\\" in name:
        return None, "unknown"
    local = os.path.join(geh_druck_dir(), name)
    if os.path.isfile(local):
        return local, None
    with _GEH_DL_LOCK:
        nl = _GEH_DL_NAME_LOCKS.setdefault(name, threading.Lock())
    with nl:
        cp = geh_cache_file(name)
        with _GEH_DL_LOCK:
            m = dict(_geh_meta().get(name) or {})
        have = os.path.isfile(cp) and os.path.getsize(cp) == m.get("size")
        if have and m.get("ver") == APP_VERSION:
            return cp, None
        hdr = {"If-None-Match": m["etag"]} if have and m.get("etag") else {}
        tmp = cp + ".part"
        try:
            os.makedirs(geh_cache_dir(), exist_ok=True)
            with urllib.request.urlopen(_upd_request(GEH_DRUCK_RAW + quote(name), hdr), timeout=timeout) as r:
                cl = r.headers.get("Content-Length")
                if cl and cl.isdigit() and int(cl) > GEH_DRUCK_MAX:
                    return (cp, None) if have else (None, "too big")
                n = 0
                with open(tmp, "wb") as f_:
                    while True:
                        b_ = r.read(65536)
                        if not b_:
                            break
                        n += len(b_)
                        if n > GEH_DRUCK_MAX:
                            break
                        f_.write(b_)
                etag = r.headers.get("ETag") or ""
            if n > GEH_DRUCK_MAX:
                os.remove(tmp)
                return (cp, None) if have else (None, "too big")
            with open(tmp, "rb") as f_:
                if f_.read(2) != b"PK":                       # 3MF = ZIP; an error page of a portal is no print file
                    os.remove(tmp)
                    return (cp, None) if have else (None, "bad file")
            os.replace(tmp, cp)
            m = {"size": n, "etag": etag, "ver": APP_VERSION, "t": int(time.time())}
        except urllib.error.HTTPError as e:
            if e.code == 304 and have:
                m["ver"], m["t"] = APP_VERSION, int(time.time())
            else:
                return (cp, None) if have else (None, str(e.code))
        except (OSError, ValueError, http.client.HTTPException):   # no internet, timeout, DNS, cut off, disk
            try:
                os.remove(tmp)
            except OSError:
                pass
            return (cp, None) if have else (None, "offline")
        with _GEH_DL_LOCK:
            meta = _geh_meta()
            meta = {k: v for k, v in meta.items() if k in geh_druck_namen()}
            meta[name] = m
            try:
                _geh_meta(meta)
            except OSError:
                pass
        return cp, None


def geh_var_namen(var):
    """the print files of a case: v52 -> Druckdateien/v5-2/, v53 -> Druckdateien/v5-3/ (real-gehaeuse-v53), v51 -> the others"""
    d = GEH_VAR_DIR.get(var, "v5-2/")
    return [n for n in geh_druck_namen() if (n.split("/")[0] + "/" if "/" in n else "") == d]


GEH_VAR_DIR = {"v51": "", "v52": "v5-2/", "v53": "v5-3/"}     # case -> folder of its print files
GEH_VAR_TXT = {"v51": "v5.1", "v52": "v5.2", "v53": "v5.3"}


def geh_var_std():
    return (GEH_BAU.get("variante_standard") or {}).get("gehaeuse") or "v52"


def geh_zip_name(var):
    return "MoveEye_%s_Druck_%s.zip" % (GEH_VAR_TXT.get(var, "v5.2").replace(".", "-"), APP_VERSION)


def _gx_py(o, L):
    return o.get(L) or o.get("de" if L == "rm" else "en") or o.get("de") or "" if isinstance(o, dict) else str(o or "")


def geh_liesmich(var, L=None):
    """the short guide in the ZIP (language of the device)"""
    L = cur_lang(L)
    D = GEH_BAU.get("druck") or {}
    vals = {o["id"] for g_ in GEH_BAU.get("varianten") or [] if g_["id"] == "gehaeuse" for o in g_["werte"]}
    vt = GEH_VAR_TXT.get(var, "v5.2")
    out = [tr("MoveEye print files – case %s – as of MoveEye %s", L) % (vt, APP_VERSION), ""]
    for h in D.get("hinweise") or []:
        out.append("- " + _gx_py(h, L))
    out += ["", tr("Plates for the X2D (everything on 2 plates)", L) + ": " + tr("folder", L) + " Platten_X2D/",
            tr("Single parts (3MF)", L) + ":"]
    for p in D.get("teile") or []:
        w = p.get("wenn")
        if p.get("nicht") == var:                     # replaced in this case (v5.3: lower part / lid v5.2)
            continue
        if w in vals and w != var and not (w == "v52" and var == "v53"):   # v5.3 builds on v5.2
            continue
        opt = "  (" + tr("optional", L) + ": " + w + ")" if w and w not in vals else ""
        out.append("- %s: × %s · %s %s %% · %s %s · %s %s · %s %s mm%s · %s %s · %s ~%s h%s" % (
            p["datei"], p["stueck"], tr("Infill", L), p["fuellung"], tr("Walls", L), p["waende"], tr("Supports", L),
            "✓" if p.get("stuetzen") else tr("none", L), tr("Layer", L), p["schicht"], " · Brim %s mm" % p["brim"] if p.get("brim") else "",
            tr("lies on", L), _gx_py(p.get("liegt"), L), tr("Print time", L), p["zeit_h"], opt))
    out += ["", _gx_py(D.get("zeit_hinweis"), L), "", tr("Complete kit package (GitHub)", L) + ": " + GEH_BAUSATZ_URL, ""]
    return "\r\n".join(out)


def _geh_bg_fetch(names):
    try:
        for n in names:
            geh_druck_holen(n, timeout=60)
    finally:
        _GEH_DL_BG["run"] = False


def geh_alle_zip(var=None, budget=None):
    """-> ("zip", bytes, file name) | ("wait", done, total) | ("offline", reason, None): the print files of the chosen case
    in one ZIP (3MF are compressed already: stored), fetched where missing"""
    import io
    var = var if var in GEH_VAR_DIR else geh_var_std()
    names = geh_var_namen(var)
    t0, paths = time.time(), {}
    budget = GEH_ZIP_BUDGET if budget is None else budget
    for i, n in enumerate(names):
        if time.time() - t0 > budget:
            rest = names[i:]
            if not _GEH_DL_BG["run"]:
                _GEH_DL_BG["run"] = True
                threading.Thread(target=_geh_bg_fetch, args=(rest,), daemon=True).start()
            return "wait", len(paths), len(names)
        p, why = geh_druck_holen(n)
        if not p:
            return "offline", why, None
        paths[n] = p
    zn = geh_zip_name(var)
    top = zn[:-4] + "/"
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_STORED) as z:
        z.writestr(top + "LIESMICH.txt", geh_liesmich(var).encode("utf-8"))
        for n in names:
            bn = geh_base_name(n)
            z.write(paths[n], top + ("Platten_X2D/" + bn if n in (GEH_BAU.get("druckdateien") or []) else bn))
    return "zip", b.getvalue(), zn


def geh_dl_page(msg, retry=None, refresh=0):
    """a small page instead of an error (no internet, still fetching)"""
    import html as _h
    e = _h.escape
    L = cur_lang()
    rf = '<meta http-equiv="refresh" content="%d">' % refresh if refresh else ""
    rb = '<p><a class="b" href="%s">%s</a></p>' % (e(retry), e(tr("Try again"))) if retry else ""
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">%s'
            '<title>MoveEye</title><style>:root{color-scheme:light dark}body{font:16px/1.5 system-ui,-apple-system,sans-serif;margin:0;padding:24px 16px;'
            'background:#f4f6fa;color:#162033}@media (prefers-color-scheme:dark){body{background:#0f1624;color:#e6ebf4}}main{max-width:560px;margin:0 auto}'
            'a{color:#2f7de1}a.b{display:inline-block;padding:10px 16px;border-radius:10px;background:#2f7de1;color:#fff;text-decoration:none}</style></head>'
            '<body><main><h2>🛠 MoveEye</h2><p>%s</p>%s<p><a href="%s">⬇ %s</a></p><p><a href="/build#drucken">‹ %s</a></p></main></body></html>'
            % (L, rf, e(msg), rb, e(GEH_BAUSATZ_URL), e(tr("Complete kit package (GitHub)")), e(tr("Back to Build"))))


def geh_alle_name(v52=True):
    """the name of the print ZIP with the running version, e.g. MoveEye_v5-2_Druck_3.46.1 (the 3MF keep their names)"""
    return ("MoveEye_v5-2_Druck_" if v52 else "MoveEye_v5-1_Druck_") + APP_VERSION


_BAU3D_CACHE = {}


def bau3d_bytes(key):
    """the gzip bytes of a three.js file or of the model (639vb) - decoded once"""
    import base64
    if key not in _BAU3D_CACHE:
        if key == "glb":
            if len(BAU3D_GLB) < 3:                         # Schlank: the model is in the data zip (012) - without it: 503
                return None
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
        b_ = bau3d_bytes("glb")
        return gz(b_, "model/gltf-binary") if b_ else Response("additional data missing", 503)

    @app.route("/build/qr.svg")
    def geh_qr():
        return Response(qr_svg(request.host_url), mimetype="image/svg+xml", headers={"Cache-Control": "no-store"})

    @app.route("/build/datei/<path:name>")                # path: the files of v5.2 are in Druckdateien/v5-2/
    def geh_datei(name):
        if name not in geh_druck_namen():
            return Response("no", 404)
        p, why = geh_druck_holen(name)                   # real-download-fix: no redirect to GitHub (Safari: «Load failed»)
        if not p:
            msg = tr("The print file is too big.") if why == "too big" else tr("The print file is not on this MoveEye and could not be fetched from the internet (no connection?). Try again later, or load the complete kit package.")
            return Response(geh_dl_page(msg, retry="/build/datei/" + name), 503, mimetype="text/html")
        with open(p, "rb") as f_:
            return Response(f_.read(), mimetype="application/octet-stream",
                            headers={"Content-Disposition": f'attachment; filename="{geh_base_name(name)}"', "Cache-Control": "private, max-age=600"})

    @app.route("/build/alle.zip")
    def geh_alle():
        var = request.args.get("var") or geh_var_std()
        st, a_, b_ = geh_alle_zip(var)
        if st == "zip":
            return Response(a_, mimetype="application/zip", headers={"Content-Disposition": f'attachment; filename="{b_}"', "Cache-Control": "no-store"})
        url = "/build/alle.zip?var=" + (var if var in GEH_VAR_DIR else geh_var_std())
        if st == "wait":
            return Response(geh_dl_page(tr("The print files are being fetched from the internet (%d of %d). This page tries again by itself; you can also tap «Try again».") % (a_, b_), retry=url, refresh=15), 202, mimetype="text/html")
        return Response(geh_dl_page(tr("The print file is not on this MoveEye and could not be fetched from the internet (no connection?). Try again later, or load the complete kit package."), retry=url), 503, mimetype="text/html")

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
           'Inbetriebnahme, Fehlersuche und Wartung. Oben die Variante (v5.1 / v5.2 / v5.3, mit / ohne Akku, mit / ohne Mover) und <b>«Mein Bau»</b>: '
           'deine Checkliste, für dich auf dem Pi gespeichert. Mit verbundenem Simulator öffnet «Im Simulator ansehen» dasselbe im Simulator '
           '(Mehr → Bauen). Vor dem Druck des Unterteils die Masse des UPS HAT (E) mit Akkus nachmessen.</p></section>\n'),
    "en": ('<section id="case" data-icon="🛠"><h2>Build</h2><p>Everything to build MoveEye yourself is under More → <a href="/build"><b>Build</b></a> '
           '(formerly «Case &amp; build»), in tabs: Overview with the <b>3D workshop</b> (turn, zoom, explode, see through, inside, tap a part – '
           'runs in the browser, no simulator and no internet needed), Parts, Shopping (price estimate, shop search, CSV, print), Printing (per part, '
           'print files one by one or all), Assembly (14 steps, animated), Wiring (plan with pins and channels), Software, Commissioning, '
           'Troubleshooting and Maintenance. At the top the variant (v5.1 / v5.2 / v5.3, with / without battery, with / without mover) and <b>«My build»</b>: '
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
    assert re.fullmatch(r"\d+\.\d+(\.\d+)?", str(B.get("version"))) and len(B.get("schritte") or []) == 14, "data"   # 3 tracks: own number
    bom = {b["id"] for b in B["bom"]}
    for t_ in B["teile"]:
        assert not t_.get("bom") or t_["bom"] in bom, t_["id"]
        assert not t_.get("schritt") or 1 <= t_["schritt"] <= 14, t_["id"]
    vals = {o["id"] for v in B["varianten"] for o in v["werte"]}
    T_ = {t_["id"]: t_ for t_ in B["teile"]}
    assert (B.get("variante_standard") or {}).get("gehaeuse") == "v53" and {"v51", "v52"} <= vals, "real-gehaeuse-v53: v5.3 is the standard (released 02.11.2026), v5.2 and v5.1 stay"
    for t_ in B["teile"]:                         # the parts of a variant are in the assembly steps, at the step of the part they replace
        if t_.get("art") in ("v52", "v53", "dev"):
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
    off_ = geh_offline_html()                             # real-werkstatt-standalone: the same page as one offline file
    for x in ("window.MW_OFFLINE=", '"three":"data:text/javascript;base64,', "data:model/gltf-binary;base64,", GEH_DRUCK_RAW, GEH_BAUSATZ_URL,
              "const GEH_OFF = window.MW_OFFLINE", "window.I18NXA=", '"Offline version"', "Parties", APP_VERSION, "Request on the MoveEye homepage"):
        assert x in off_, ("offline file", x)
    assert '"home"' not in off_.split("window.I18NXA=")[0] and '"home":"https://x.ch/"' in geh_offline_html("https://x.ch/")[:300000], "homepage link only when set"
    for x in ('src="/', "/bau3d/", "/build/qr.svg", "/i18n/", "/*GEH", "<!--NAV-->", "/*ALERTS*/"):
        assert x not in off_, ("offline file", x)
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
    if probs:   # Drei Spuren (Besitzer 03.11.2026): the case is released on its own, its data come with the next MoveEye /
        # simulator version («Kamera/Gehäuse überall nachziehen» is paused) - a warning here; rel_mw.sh shows it before a release
        return "WARNING – case data in the repository differ from this MoveEye (3 tracks: gehaeuse_bauen.py --sim at the next release): " + probs[0]
    assert not probs, " | ".join(probs)
    warn = bau_infos_veraltet()
    if warn:                                              # a warning, no error: nothing is changed by itself
        return "WARNING – " + " · ".join(tr("Build info out of date: %s – update it?") % w for w in warn[:4])
    return "Build: page /build (10 tabs, 3D without simulator), My build per user, models = source, build infos fit the code"


SELFTEST_EXTRA.append(("Build (page /build, 3D in the browser, My build, models = source, build infos)", geh_selftest))
def geh_dl_selftest():
    """real-download-fix: print files without the repository - fetched from a stand-in server, cache, ETag, base name,
    path tricks refused, size limit, no internet"""
    import http.server
    import tempfile
    body_ = b"PK\x03\x04" + b"3mf" * 400
    hits = []

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            hits.append((self.path, self.headers.get("If-None-Match")))
            if "bad" in self.path:
                b_ = b"<html>portal</html>"
            elif self.headers.get("If-None-Match") == '"e1"':
                self.send_response(304)
                self.end_headers()
                return
            else:
                b_ = body_
            self.send_response(200)
            self.send_header("ETag", '"e1"')
            self.send_header("Content-Length", str(len(b_)))
            self.end_headers()
            self.wfile.write(b_)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    tmp = tempfile.mkdtemp(prefix="mw_druck_")
    G_ = globals()
    keep = {k: G_[k] for k in ("GEH_DRUCK_RAW", "GEH_DRUCK_MAX", "geh_druck_dir", "geh_cache_dir", "GEH_ZIP_BUDGET")}
    npx = os.environ.get("no_proxy"), os.environ.get("NO_PROXY")
    try:
        os.environ["no_proxy"] = os.environ["NO_PROXY"] = "127.0.0.1,localhost"
        G_["GEH_DRUCK_RAW"] = "http://127.0.0.1:%d/raw/" % srv.server_address[1]
        G_["geh_druck_dir"] = lambda: os.path.join(tmp, "kein_repo")
        G_["geh_cache_dir"] = lambda: os.path.join(tmp, "druck_cache")
        n52 = "v5-2/MoveEye_v5-2_01_Unterteil_v52.3mf"
        assert n52 in geh_druck_namen()
        for bad in ("../motionwatch_settings.json", "v5-2/../../versions.json", "/etc/passwd", "v5-2\\x.3mf", "x.3mf"):
            assert geh_druck_holen(bad) == (None, "unknown"), bad
        p, why = geh_druck_holen(n52)
        assert p and not why and os.path.dirname(p) == os.path.join(tmp, "druck_cache") and "/" not in os.path.basename(p), (p, why)
        with open(p, "rb") as f_:
            assert f_.read() == body_
        assert hits[-1][0] == "/raw/v5-2/MoveEye_v5-2_01_Unterteil_v52.3mf", hits
        assert geh_druck_holen(n52)[0] == p and len(hits) == 1, "from the cache, no new request"
        m = _geh_meta()
        m[n52]["ver"] = "0.0.1"                       # a new version: asked again with the ETag, 304 keeps the file
        _geh_meta(m)
        assert geh_druck_holen(n52)[0] == p and hits[-1][1] == '"e1"' and _geh_meta()[n52]["ver"] == APP_VERSION, hits
        assert geh_base_name(n52) == "MoveEye_v5-2_01_Unterteil_v52.3mf"
        G_["GEH_DRUCK_MAX"] = 100
        assert geh_druck_holen("v5-2/MoveEye_v5-2_03_Drehteller.3mf") == (None, "too big")
        G_["GEH_DRUCK_MAX"] = keep["GEH_DRUCK_MAX"]
        G_["GEH_DRUCK_RAW"] = "http://127.0.0.1:%d/bad/" % srv.server_address[1]
        assert geh_druck_holen("v5-2/MoveEye_v5-2_05_Arm2_Lagerseite.3mf") == (None, "bad file")
        assert not [f_ for f_ in os.listdir(os.path.join(tmp, "druck_cache")) if f_.endswith(".part")], "no half files"
        G_["GEH_DRUCK_RAW"] = "http://127.0.0.1:1/"   # no internet: a readable reason, the cached file still works
        assert geh_druck_holen("v5-2/MoveEye_v5-2_07_Seitendeckel.3mf", timeout=3) == (None, "offline")
        m = _geh_meta()
        m[n52]["ver"] = "0.0.1"
        _geh_meta(m)
        assert geh_druck_holen(n52, timeout=3)[0] == p, "old cache without internet"
        st, why, _n = geh_alle_zip("v52")
        assert st == "offline" and why == "offline", (st, why)
        assert "Bausatz" in geh_dl_page(tr("Try again"), retry="/build/alle.zip?var=v52") and "<script" not in geh_dl_page("<script>")
        G_["GEH_DRUCK_RAW"] = "http://127.0.0.1:%d/raw/" % srv.server_address[1]
        G_["GEH_ZIP_BUDGET"] = -1                     # too slow: the rest in the background, the page asks to try again
        st, a_, b_ = geh_alle_zip("v52")
        assert st == "wait" and a_ == 0 and b_ == len(geh_var_namen("v52")), (st, a_, b_)
        for _i in range(100):
            if not _GEH_DL_BG["run"]:
                break
            time.sleep(0.05)
        G_["GEH_ZIP_BUDGET"] = keep["GEH_ZIP_BUDGET"]
        st, zb, zn = geh_alle_zip("v52")
        assert st == "zip" and zn == "MoveEye_v5-2_Druck_%s.zip" % APP_VERSION, (st, zn)
        import io
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            nl = z.namelist()
        top = zn[:-4] + "/"
        assert top + "LIESMICH.txt" in nl and top + "MoveEye_v5-2_01_Unterteil_v52.3mf" in nl and top + "Platten_X2D/MotionWatch_v5-2_Platte_A_Unterteil.3mf" in nl, nl[:5]
        assert len(nl) == len(geh_var_namen("v52")) + 1 and not [x for x in nl if "v5-1" in x or "v5-2/" in x[len(top):]], nl
        assert geh_zip_name("v51") == "MoveEye_v5-1_Druck_%s.zip" % APP_VERSION and all(not n.startswith("v5-2/") for n in geh_var_namen("v51"))
        n53 = geh_var_namen("v53")                    # real-gehaeuse-v53: own folder, all parts (also the unchanged ones of v5.2)
        assert n53 and all(n.startswith("v5-3/") for n in n53) and geh_zip_name("v53") == "MoveEye_v5-3_Druck_%s.zip" % APP_VERSION, n53[:3]
        assert len([n for n in n53 if n not in (GEH_BAU.get("druckdateien") or [])]) >= len([n for n in geh_var_namen("v52") if n not in (GEH_BAU.get("druckdateien") or [])]), "v5.3: every single part"
    finally:
        srv.shutdown()
        srv.server_close()
        G_.update(keep)
        for k_, v_ in zip(("no_proxy", "NO_PROXY"), npx):
            if v_ is None:
                os.environ.pop(k_, None)
            else:
                os.environ[k_] = v_
        shutil.rmtree(tmp, ignore_errors=True)
    html = geh_page()
    fl_ = re.search(r"function fileLink\(f, label\) \{.*?\n", html)
    assert fl_ and "download" not in fl_.group(0) and 'split("/").map(encodeURIComponent).join("/")' in fl_.group(0), ("links", fl_ and fl_.group(0)[:200])
    assert "/build/alle.zip?var=" in html and "MoveEye_Bausatz.zip" in html, "ZIP of the case, kit package"
    return "Print files without the repository: fetched, cached (ETag), base name, path tricks refused, ZIP of the case"


SELFTEST_EXTRA.append(("Build print files (fetched without the repository, cache, ZIP of the case)", geh_dl_selftest))
