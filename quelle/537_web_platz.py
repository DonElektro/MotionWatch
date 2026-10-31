#@ MoveEye – Teil 537: Webseite «Platz einrichten» (/place), die Karte auf der Schutz-Seite, das Angebot nach dem Hinstellen und «Blickwinkel der Kamera» in den Einstellungen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.30: phone first (390 px): three steps - 1 look around (scan), 2 mark (tap the suggestions or draw a box with one
# of four big buttons), 3 done (what was made, «Gehtest» at once). The main page (530) stays as it is: a small script at its
# end adds the card on the Schutz tab, the offer («MoveEye hingestellt? Platz einrichten») and the field of view per camera.
# ----------------------------------------------------------------------------
PLACE_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Set up the place</title>
<style>
/*BASECSS*/
main{padding:14px 16px 90px;max-width:980px;margin:0 auto}
.steps{display:flex;gap:6px;margin:0 0 12px}.steps span{flex:1;text-align:center;padding:6px 4px;border-radius:10px;border:1px solid var(--line);font-size:12.5px;color:var(--mut)}
.steps span.on{border-color:var(--acc);color:var(--txt);font-weight:700}
.big{display:block;width:100%;padding:15px 12px;font-size:17px;border-radius:14px;margin:10px 0 0}
.opt{display:flex;align-items:center;gap:10px;padding:10px 12px;margin:8px 0 0;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
.opt input{width:22px;height:22px;flex:none}
.bar{height:12px;border-radius:8px;background:var(--line);overflow:hidden}.bar i{display:block;height:100%;background:var(--acc);transition:width .4s}
#prev{width:100%;max-width:520px;border-radius:12px;display:block;margin:10px auto 0;background:#000;aspect-ratio:16/9;object-fit:cover}
.tools{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:10px 0}
@media(min-width:700px){.tools{grid-template-columns:repeat(5,1fr)}}
.tools button{padding:12px 6px;font-size:15px;border-radius:12px;min-height:52px;line-height:1.2}
.tools button.on{outline:3px solid var(--acc);outline-offset:1px;font-weight:700}
#pwrap{overflow-x:auto;overflow-y:hidden;border-radius:12px;background:#111;-webkit-overflow-scrolling:touch;position:relative}
#pin{position:relative;display:inline-block;vertical-align:top}
#pimg{display:block;height:260px;width:auto;max-width:none;user-select:none;-webkit-user-drag:none}
@media(min-width:700px){#pimg{height:min(420px,50vh)}}
#psvg{position:absolute;left:0;top:0;width:100%;height:100%}
#pin.draw #psvg{touch-action:none;cursor:crosshair}
.lst .it{display:grid;grid-template-columns:34px 1fr 40px;gap:6px;align-items:center;padding:8px 0;border-top:1px solid var(--line)}
.lst .it i{font-style:normal;font-size:22px;text-align:center}.lst .it input[type=text]{width:100%;box-sizing:border-box}
.lst .it .sub{grid-column:2/-1;font-size:13px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.lst .it.sel{background:rgba(120,160,255,.10)}
.leg{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:12px;margin:6px 0}
.sum div{padding:6px 0;border-top:1px solid var(--line)}
#selbar{display:none;gap:6px;margin:8px 0;flex-wrap:wrap}#selbar.on{display:flex}
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
  <h2 style="margin:0 0 8px">📍 <span data-i18n="Set up the place">Set up the place</span></h2>
  <div class="steps"><span id="st1" data-i18n="1 Look around">1 Look around</span><span id="st2" data-i18n="2 Mark">2 Mark</span><span id="st3" data-i18n="3 Done">3 Done</span></div>
  <div id="view" class="card"></div>
</main>
<script>
/*COMMON*/
/*PLACEDE*/
const KINDS = {tent: ["⛺", "My tent / camper", "#ff5a5a"], access: ["🚶", "Access / path", "#ffb020"], public_path: ["🛣", "Public path", "#c9a0ff"],
  valuable: ["🚲", "Valuables", "#3cc8ff"], ignore: ["🌿", "Ignore", "#8fd18f"]};
const P = {s: null, items: [], tool: "", sel: -1, th: false, timer: 0, mode: "", ver: 0, drag: null};
const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
const V = () => document.getElementById("view");
const LOC = () => ({de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"}[LANG] || "en-GB");
function steps(n) { [1, 2, 3].forEach(i => document.getElementById("st" + i).classList.toggle("on", i === n)); }
function mmss(s) { s = Math.max(0, s | 0); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
async function load() {
  clearTimeout(P.timer);
  try { const r = await fetch("/api/place?lang=" + LANG, {cache: "no-store"}); if (r.ok) P.s = await r.json(); } catch (e) {}
  const S = P.s; if (!S) { P.timer = setTimeout(load, 3000); return; }
  if (S.busy) { if (P.mode !== "scan") P.mode = "scan"; paintScan(); P.timer = setTimeout(load, 1000); return; }
  if (P.mode === "scan") { P.mode = S.scan && S.done_msg ? "mark" : "start"; if (P.mode === "mark") startMark(true); else paintStart(); return; }
  if (!P.mode) { P.mode = location.hash === "#mark" && S.scan ? "mark" : "start"; if (P.mode === "mark") startMark(false); else paintStart(); }
}
// ---- step 1: start ----
function paintStart() {
  steps(1); const S = P.s, v = V(); v.textContent = ""; const pl = S.plan;
  v.appendChild(E("p", "", t("Put MoveEye where it will guard. The head looks around once: it takes a photo in every direction and watches for about 10 seconds what moves and what the AI recognises. Then you only mark your tent, the access, your valuables and what to ignore.")));
  const cov = pl.wrap ? t("the whole circle (360°)") : t("about") + " " + pl.cover + "°";
  v.appendChild(E("p", "mut", tf("Pan range of the servo {servo}°, with the lens it sees {cover} (camera {hf}°).", {servo: pl.servo, cover: cov, hf: Math.round(pl.hf)})));
  if (!pl.wrap) v.appendChild(E("p", "mut", t("No full turn: the head turns only as far as its servo goes.")));
  v.appendChild(E("p", "mut", tf("{n} directions in {rows} rows - about {min} minutes.", {n: pl.n, rows: pl.rows, min: Math.max(1, Math.round(pl.eta / 60))})));
  const opts = {};
  const opt = (id, label, on) => { const l = E("label", "opt"); const c = E("input"); c.type = "checkbox"; c.checked = on; c.id = id; l.append(c, E("span", "", label)); v.appendChild(l); opts[id] = c; };
  if (S.wide) opt("o-wide", tf("Use the wide-angle camera ({cam}, {deg}°): {n} directions, about {min} min", {cam: S.wide.label, deg: Math.round(S.wide.hf), n: S.wide.n, min: Math.max(1, Math.round(S.wide.eta / 60))}), true);
  opt("o-rows", t("Thorough: 3 rows instead of 2 (takes longer)"), false);
  if (S.cam_h) {                                   // real-reh-fusspunkt: the height of the camera (foot point of the thermal check, 232)
    const l = E("label", "opt"); const n = E("input"); n.type = "number"; n.min = 0.2; n.max = 10; n.step = 0.05; n.value = S.cam_h.m;
    n.style.width = "90px"; n.id = "o-camh";
    n.onchange = async () => { const r = await post("/api/place", {op: "height", value: parseFloat(n.value)}); if (r && r.ok) { n.value = r.m; toast("✓ " + t("Camera height (m)") + ": " + r.m); } };
    l.append(n, E("span", "", t("Camera height (m)"))); v.appendChild(l);
    v.appendChild(E("div", "mut", t("Height of the lens above the ground - helps to tell animals from persons at night.") +
      (S.cam_h.sim ? " " + tf("Simulator: pole {m} m - counts while connected", {m: S.cam_h.sim.toFixed(2)}) : "")));
  }
  if (S.dark) {
    v.appendChild(E("div", "mut", "🌙 " + t("It is dark: the night reference is made now.")));
    if (S.ir_ok) opt("o-ir", t("with the infrared light"), true);
    if (S.thermal_ok) opt("o-th", t("with the thermal camera too"), true);
  }
  const b = E("button", "big", "▶ " + t("Start looking around")); b.type = "button";
  if (S.why_not) { b.disabled = true; v.appendChild(E("div", "mut", "⚠ " + S.why_not)); }
  b.onclick = async () => {
    b.disabled = true;
    const r = await post("/api/place", {op: "start", lang: LANG, wide: !!(opts["o-wide"] && opts["o-wide"].checked), rows: opts["o-rows"].checked ? 3 : 2,
      ir: !!(opts["o-ir"] && opts["o-ir"].checked), thermal: !!(opts["o-th"] && opts["o-th"].checked)});
    if (!r || !r.ok) { b.disabled = false; toast("⚠ " + ((r && r.error) || "error")); return; }
    P.mode = "scan"; load();
  };
  v.appendChild(b);
  if (S.scan) { const m = E("button", "sec big", "🖼 " + t("Show the last look-around") + " (" + new Date(S.scan.t * 1000).toLocaleString(LOC(), {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"}) + ")");
    m.type = "button"; m.onclick = () => startMark(false); v.appendChild(m); }
  if (S.record) {
    const R = S.record; const d = E("div", "mut"); d.style.marginTop = "12px";
    d.textContent = "✓ " + tf("Place set up on {when}: {n} things marked", {when: new Date(R.t * 1000).toLocaleString(LOC(), {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"}), n: R.items.length});
    v.appendChild(d);
    const f = E("button", "sec", "🗑 " + t("Forget the place")); f.type = "button"; f.style.marginTop = "8px";
    f.onclick = async () => { if (!confirm(t("Forget the place? Its zones, waypoints and guarded things are removed."))) return; await post("/api/place", {op: "clear", lang: LANG}); P.mode = ""; load(); };
    v.appendChild(f);
  }
}
// ---- step 1b: scanning ----
function paintScan() {
  steps(1); const S = P.s, v = V();
  if (!document.getElementById("sc-bar")) {
    v.textContent = "";
    v.appendChild(E("div", "", "")).id = "sc-t";
    const bar = E("div", "bar"); const i = E("i"); i.id = "sc-bar"; bar.appendChild(i); bar.style.margin = "10px 0"; v.appendChild(bar);
    v.appendChild(E("div", "mut", "")).id = "sc-left";
    const im = E("img"); im.id = "prev"; im.alt = ""; v.appendChild(im);
    v.appendChild(E("div", "mut", t("The head turns by itself - please do not stand in front of it."))).style.marginTop = "8px";
    const c = E("button", "sec big", "✕ " + t("Cancel")); c.type = "button"; c.onclick = () => post("/api/place", {op: "stop"}); v.appendChild(c);
    P.pv = 0;
  }
  const ph = {photo: t("taking the photo"), watch: t("watching what moves"), panorama: t("making the panorama")}[S.phase] || "…";
  document.getElementById("sc-t").innerHTML = "";
  const h = E("b", "", "🔄 " + tf("Direction {i} of {n}", {i: S.step, n: S.n})); h.style.fontSize = "18px";
  document.getElementById("sc-t").append(h, E("div", "mut", ph));
  document.getElementById("sc-bar").style.width = Math.round(100 * Math.max(0, S.step - (S.phase === "photo" ? 1 : 0.5)) / Math.max(1, S.n)) + "%";
  document.getElementById("sc-left").textContent = t("about") + " " + mmss(S.left) + " " + t("left");
  if (Date.now() - P.pv > 2000) { P.pv = Date.now(); document.getElementById("prev").src = "/api/frame.jpg?" + Date.now(); }
}
// ---- step 2: mark ----
function geo() { return P.s.scan.geo; }
function toPx(a, e) { const g = geo(); let x = (a - g.a0) * g.k; if (g.wrap && x < 0) x += 360 * g.k; return [x, (g.e_top - e) * g.k + (g.head || 0)]; }
function toAng(x, y) { const g = geo(); return [g.a0 + x / g.k, g.e_top - (y - (g.head || 0)) / g.k]; }
function startMark(fresh) {
  P.mode = "mark"; const S = P.s;
  if (!S.scan) { paintStart(); return; }
  P.items = (!fresh && S.record && S.record.items && S.record.items.length && (S.record.t || 0) >= (S.scan.t || 0) - 1)
    ? S.record.items.filter(it => it.a0 != null).map(it => ({kind: it.kind, name: it.name, a0: it.a0, a1: it.a1, e0: it.e0, e1: it.e1})) : [];
  P.taken = {}; P.tool = ""; P.sel = -1; paintMark();
}
function paintMark() {
  steps(2); const S = P.s, v = V(), g = geo(); v.textContent = "";
  v.appendChild(E("div", "mut", t("Tap a suggestion to take it, or choose a button and draw a box on the panorama with your finger. Swipe sideways with ✋.")));
  const tools = E("div", "tools");
  [["tent"], ["access"], ["valuable"], ["ignore"], [""]].forEach(([k]) => {
    const b = E("button", "sec", k ? KINDS[k][0] + " " + t(KINDS[k][1]) : "✋ " + t("Move / select")); b.type = "button"; b.classList.toggle("on", P.tool === k);
    b.onclick = () => { P.tool = k; paintMark(); }; tools.appendChild(b);
  });
  v.appendChild(tools);
  if (S.scan.thermal) { const l = E("label", "opt"); const c = E("input"); c.type = "checkbox"; c.checked = P.th; c.onchange = () => { P.th = c.checked; paintMark(); };
    l.append(c, E("span", "", "🌡 " + t("Show the thermal picture"))); v.appendChild(l); }
  const wrap = E("div"); wrap.id = "pwrap"; const pin = E("div"); pin.id = "pin"; pin.classList.toggle("draw", !!P.tool);
  const img = E("img"); img.id = "pimg"; img.alt = ""; img.draggable = false; img.src = "/place/file/" + (P.th ? "pano_th.jpg" : "pano.jpg") + "?v=" + S.scan.v;
  const NS = "http://www.w3.org/2000/svg"; const svg = document.createElementNS(NS, "svg"); svg.id = "psvg"; svg.setAttribute("viewBox", "0 0 " + g.w + " " + g.h);
  svg.setAttribute("preserveAspectRatio", "none"); pin.append(img, svg); wrap.appendChild(pin); v.appendChild(wrap);
  const lg = E("div", "leg mut"); lg.append(E("span", "", "┅ " + t("suggestion - tap to take it")), E("span", "", "▭ " + t("marked")));
  if (g.wrap) lg.appendChild(E("span", "", "↔ " + t("the picture goes on after the seam (360°)")));
  v.appendChild(lg);
  const sb = E("div"); sb.id = "selbar"; v.appendChild(sb);
  drawSvg(svg);
  bindDraw(svg, pin);
  const all = E("button", "sec", "✚ " + t("Take all suggestions")); all.type = "button"; all.style.marginTop = "6px";
  all.onclick = () => { (S.scan.suggest || []).forEach(s => take(s, s.kind)); paintMark(); };
  if ((S.scan.suggest || []).some(s => !P.taken[s.id])) v.appendChild(all);
  const lst = E("div", "lst"); lst.style.marginTop = "10px";
  if (!P.items.length) lst.appendChild(E("div", "mut", t("Nothing marked yet.")));
  P.items.forEach((it, i) => {
    const r = E("div", "it" + (i === P.sel ? " sel" : "")); r.appendChild(E("i", "", KINDS[it.kind][0]));
    const n = E("input"); n.type = "text"; n.value = it.name; n.maxLength = 40; n.placeholder = t(KINDS[it.kind][1]); n.oninput = () => { it.name = n.value; };
    const x = E("button", "sec", "✕"); x.type = "button"; x.title = t("Remove"); x.onclick = () => { P.items.splice(i, 1); P.sel = -1; paintMark(); };
    r.append(n, x);
    const sub = E("div", "sub mut");
    const ks = E("select"); ["tent", "access", "valuable", "ignore"].forEach(k => { const o = E("option", "", KINDS[k][0] + " " + t(KINDS[k][1])); o.value = k; ks.appendChild(o); });
    ks.value = it.kind === "public_path" ? "access" : it.kind; ks.onchange = () => { it.kind = ks.value; paintMark(); }; sub.appendChild(ks);
    if (it.kind === "access" || it.kind === "public_path") { const l = E("label"); const c = E("input"); c.type = "checkbox"; c.checked = it.kind === "public_path";
      c.onchange = () => { it.kind = c.checked ? "public_path" : "access"; paintMark(); }; l.append(c, " " + t("public path = only report")); sub.appendChild(l); }
    sub.appendChild(E("span", "", KIND_NOTE(it.kind)));
    r.appendChild(sub); r.onclick = e => { if (e.target === r) { P.sel = i; paintMark(); } }; lst.appendChild(r);
  });
  v.appendChild(lst);
  const pt = E("label", "opt"); const pc = E("input"); pc.type = "checkbox"; pc.id = "o-patrol"; pc.checked = !!(S.info && S.info.patrol);
  pt.append(pc, E("span", "", "🔁 " + t("Patrol: the head looks at the accesses now and then"))); v.appendChild(pt);
  const ap = E("button", "big", "✓ " + t("Apply")); ap.type = "button";
  ap.onclick = async () => {
    ap.disabled = true;
    const r = await post("/api/place", {op: "apply", lang: LANG, items: P.items, patrol: pc.checked});
    ap.disabled = false;
    if (!r || !r.ok) { toast("⚠ " + ((r && r.error) || "error")); return; }
    P.res = r.result; paintDone();
  };
  v.appendChild(ap);
  const bk = E("button", "sec big", "↻ " + t("Look around again")); bk.type = "button"; bk.onclick = () => { P.mode = "start"; paintStart(); }; v.appendChild(bk);
  // scroll to the tent / the first item once
  if (!P.scrolled) { P.scrolled = true; setTimeout(() => { const f = P.items[0] || (S.scan.suggest || [])[0]; if (f) { const [x] = toPx(f.a0, f.e1); wrap.scrollLeft = Math.max(0, x * scaleOf() - 60); } }, 300); }
}
function KIND_NOTE(k) { return {tent: t("protection zone, lights / siren aim here, a person close by counts more"), access: t("line: a person crossing it is reported + patrol point"),
  public_path: t("persons there: only a note, no alarm"), valuable: t("guarded: in the morning «Bike missing»"), ignore: t("mask: movement there is ignored")}[k] || ""; }
function scaleOf() { const im = document.getElementById("pimg"); return im && im.naturalHeight ? im.clientHeight / im.naturalHeight : 260 / geo().h; }
function take(s, kind) { if (P.taken[s.id]) return; P.taken[s.id] = 1; P.items.push({kind: kind || s.kind, name: t(s.name || KINDS[s.kind][1]), a0: s.a0, a1: s.a1, e0: s.e0, e1: s.e1}); }
function rect(svg, b, col, dash, label, extra) {
  const NS = "http://www.w3.org/2000/svg"; const [x0, y0] = toPx(b.a0, b.e1); const [x1, y1] = toPx(b.a1, b.e0);
  const r = document.createElementNS(NS, "rect"); r.setAttribute("x", Math.min(x0, x1)); r.setAttribute("y", y0); r.setAttribute("width", Math.abs(x1 - x0)); r.setAttribute("height", y1 - y0);
  r.setAttribute("fill", dash ? "rgba(255,255,255,.06)" : col + "33"); r.setAttribute("stroke", col); r.setAttribute("stroke-width", extra ? 5 : 3); if (dash) r.setAttribute("stroke-dasharray", "10 7");
  r.setAttribute("vector-effect", "non-scaling-stroke"); svg.appendChild(r);
  const tx = document.createElementNS(NS, "text"); tx.setAttribute("x", Math.min(x0, x1) + 6); tx.setAttribute("y", y0 + 26); tx.setAttribute("fill", "#fff"); tx.setAttribute("font-size", "22");
  tx.setAttribute("stroke", "#000"); tx.setAttribute("stroke-width", "4"); tx.setAttribute("paint-order", "stroke"); tx.textContent = label; svg.appendChild(tx);
  return r;
}
function drawSvg(svg) {
  svg.textContent = ""; const S = P.s;
  (S.scan.suggest || []).forEach(s => { if (!P.taken[s.id]) rect(svg, s, KINDS[s.kind][2], true, "+" + KINDS[s.kind][0]); });
  P.items.forEach((it, i) => rect(svg, it, KINDS[it.kind][2], false, KINDS[it.kind][0] + " " + (it.name || t(KINDS[it.kind][1])), i === P.sel));
  if (P.drag && P.drag.b) rect(svg, P.drag.b, P.tool ? KINDS[P.tool][2] : "#fff", false, "");
}
function hit(list, a, e) { for (let i = list.length - 1; i >= 0; i--) { const b = list[i]; let aa = a; const g = geo(); if (g.wrap) { const c = (b.a0 + b.a1) / 2; aa = c + (((a - c + 180) % 360) + 360) % 360 - 180; }
  if (aa >= b.a0 && aa <= b.a1 && e >= b.e0 && e <= b.e1) return i; } return -1; }
function bindDraw(svg, pin) {
  const pt = ev => { const r = svg.getBoundingClientRect(), g = geo(); return [(ev.clientX - r.left) / r.width * g.w, (ev.clientY - r.top) / r.height * g.h]; };
  svg.onpointerdown = ev => { const [x, y] = pt(ev); P.drag = {x0: x, y0: y, sx: ev.clientX, sy: ev.clientY, b: null}; if (P.tool) { try { svg.setPointerCapture(ev.pointerId); } catch (e) {} ev.preventDefault(); } };
  svg.onpointermove = ev => { if (!P.drag || !P.tool) return; const [x, y] = pt(ev); const [a0, e0] = toAng(Math.min(P.drag.x0, x), Math.max(P.drag.y0, y)), [a1, e1] = toAng(Math.max(P.drag.x0, x), Math.min(P.drag.y0, y));
    P.drag.b = {a0: a0, a1: a1, e0: e0, e1: e1}; drawSvg(svg); };
  svg.onpointerup = ev => {
    const D = P.drag; P.drag = null; if (!D) return;
    const moved = Math.hypot(ev.clientX - D.sx, ev.clientY - D.sy);
    if (P.tool && moved > 14 && D.b) { P.items.push({kind: P.tool, name: "", a0: D.b.a0, a1: D.b.a1, e0: D.b.e0, e1: D.b.e1}); P.sel = P.items.length - 1; paintMark(); return; }
    if (moved > 14) { drawSvg(svg); return; }
    const [a, e] = toAng(...pt(ev));
    const ii = hit(P.items, a, e); if (ii >= 0) { P.sel = ii; if (P.tool) P.items[ii].kind = P.tool; paintMark(); return; }
    const sg = (P.s.scan.suggest || []).filter(s => !P.taken[s.id]); const si = hit(sg, a, e);
    if (si >= 0) { take(sg[si], P.tool || sg[si].kind); P.sel = P.items.length - 1; paintMark(); return; }
    if (P.tool) { const g = geo(), half = 4; P.items.push({kind: P.tool, name: "", a0: a - half * 1.5, a1: a + half * 1.5, e0: e - half, e1: e + half}); P.sel = P.items.length - 1; paintMark(); }
  };
  svg.onpointercancel = () => { P.drag = null; drawSvg(svg); };
}
// ---- step 3: done ----
function paintDone() {
  steps(3); const R = P.res || {}, v = V(); v.textContent = "";
  v.appendChild(E("h3", "", "✓ " + t("The place is set up")));
  const s = E("div", "sum");
  const line = (ic, txt) => s.appendChild(E("div", "", ic + " " + txt));
  if (R.tent) line("⛺", tf("{n} protection zone(s) at the tent", {n: R.tent}));
  if (R.lines) line("🚶", tf("{n} line(s) at the accesses", {n: R.lines}));
  if (R.public) line("🛣", tf("{n} public path(s): only reported", {n: R.public}));
  if (R.masks) line("🌿", tf("{n} mask(s): ignored", {n: R.masks}));
  if (R.waypoints) line("🔁", tf("{n} patrol point(s)", {n: R.waypoints}));
  if (R.watched) line("🚲", tf("{n} guarded thing(s) - reported in the morning when missing", {n: R.watched}));
  else if ((P.items || []).some(i => i.kind === "valuable")) line("🚲", t("The guarded things follow after the reference scan of the main camera."));
  if (R.skipped) line("⚠", tf("{n} zone(s) not made: at most 12 zones", {n: R.skipped}));
  if (!R.items) line("ℹ", t("Nothing marked - nothing changed."));
  v.appendChild(s);
  v.appendChild(E("p", "mut", t("Now test it: walk past like a visitor would. MoveEye beeps at every detection.")));
  const w = E("button", "big", "🚶 " + t("Start the walk test")); w.type = "button";
  w.onclick = async () => { const r = await post("/api/walktest", {action: "start", lang: LANG}); if (r && r.ok) location.href = "/"; else toast("⚠ " + ((r && r.error) || "error")); };
  v.appendChild(w);
  const z = E("a", "btn sec big", "▱ " + t("Look at the zones")); z.href = "/zones"; z.style.textAlign = "center"; v.appendChild(z);
  const b = E("a", "btn sec big", "🛡 " + t("Back to Schutz")); b.href = "/protect"; b.style.textAlign = "center"; v.appendChild(b);
}
function tf(k, o) { let s = t(k); for (const x in o) s = s.split("{" + x + "}").join(o[x]); return s; }
(async () => { await initAppearance(); load(); })();
/*ALERTS*/
</script>
</body></html>
"""

# the card on the Schutz tab, the offer after setting up, the field of view in Settings → Camera / Servos (main page 530)
PLACE_MAIN_JS = r"""
<script>
(function () {
  try { const D = /*PLDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const tab = () => document.body.getAttribute("data-tab") || "";
  let S = null;
  function card() {
    const pc = document.getElementById("pr-card"); if (!pc) return;
    let c = document.getElementById("pl-card");
    if (!c) { c = E("div", "auxbox"); c.id = "pl-card"; c.style.margin = "10px 0";
      const nr = document.getElementById("pr-night"); if (nr) nr.before(c); else pc.appendChild(c); }
    c.textContent = "";
    const a = E("a", "btn", "📍 " + T("Set up the place")); a.href = "/place"; a.style.cssText = "display:block;text-align:center;padding:12px;font-size:16px";
    const R = S && S.record;
    const d = E("div", "mut", R ? "✓ " + T("Place set up") + " · " + new Date(R.t * 1000).toLocaleDateString({de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"}[L()] || "en-GB") + " · " + (R.items || []).length + " " + T("things marked")
                            : T("MoveEye put up? Let it look around once: tent, access, valuables, what to ignore."));
    d.style.marginTop = "6px"; c.append(a, d);
  }
  function offer() {
    let o = document.getElementById("pl-offer");
    const want = S && S.offer && (tab() === "protect" || tab() === "live");
    if (!want) { if (o) o.remove(); return; }
    if (o) return;
    o = E("div", "card"); o.id = "pl-offer"; o.style.cssText = "border:2px solid var(--acc);margin:0 0 12px";
    o.appendChild(E("b", "", "📍 " + T(S.offer === "moved" ? "New place? Set it up again" : "MoveEye put up? Set up the place")));
    o.appendChild(E("div", "mut", T("2-3 minutes: the head looks around, you only tap tent, access, valuables.")));
    const r = E("div", "btns"); const a = E("a", "btn", "📍 " + T("Set up the place")); a.href = "/place";
    const x = E("button", "sec", T("Later")); x.type = "button"; x.onclick = async () => { await post("/api/place", {op: "dismiss"}); o.remove(); };
    r.append(a, x); o.appendChild(r);
    const m = document.querySelector("main"); if (m) m.prepend(o);
  }
  // Settings → Camera / Servos: field of view per camera
  let F = null, fbusy = false;
  async function fov() {
    const sl = document.querySelector('.sl[data-key="cam_vfov"]'), sec = document.querySelector('details[data-view="sec:Camera / Servos"]');
    if ((!sl && !sec) || document.getElementById("fov-box") || fbusy) return;
    fbusy = true;
    try { F = await (await fetch("/api/camfov?lang=" + L(), {cache: "no-store"})).json(); } catch (e) { F = null; }
    fbusy = false;
    if (!F || !F.ok || document.getElementById("fov-box")) return;
    const bx = E("div", "auxbox"); bx.id = "fov-box"; bx.style.margin = "8px 0";
    bx.appendChild(E("b", "", "📐 " + T("Field of view of the camera")));
    F.cams.forEach(c => {
      const r = E("div"); r.style.cssText = "margin-top:8px";
      r.appendChild(E("div", "", (c.main ? T("Main camera") : T("Extra camera")) + ": " + c.label));
      const s = E("select"); s.style.width = "100%"; F.choices.forEach(([k, n]) => { const o = E("option", "", n); o.value = k; s.appendChild(o); }); s.value = c.model;
      const n = E("input"); n.type = "number"; n.min = 20; n.max = 200; n.step = 1; n.value = c.deg || Math.round(c.h); n.style.width = "90px"; n.hidden = c.model !== "own";
      const info = E("div", "mut", "");
      const src = {sim: T("from the simulator"), auto: c.detected_name ? T("detected") + ": " + c.detected_name : T("not detected - Camera Module 3 assumed"), model: T("chosen"), own: T("own value"), default: T("standard")}[c.src] || "";
      info.textContent = Math.round(c.h) + "° × " + Math.round(c.v) + "° · " + src;
      const send = async () => { n.hidden = s.value !== "own";
        const q = await post("/api/camfov", {spec: c.spec, model: s.value, deg: +n.value, head: hd ? hd.checked : null, lang: L()});
        if (q && q.ok) { const cc = (q.cams || []).find(x => x.spec === c.spec); if (cc) info.textContent = Math.round(cc.h) + "° × " + Math.round(cc.v) + "°"; toast("✓"); } else toast("⚠ " + ((q && q.error) || "error")); };
      s.onchange = send; n.onchange = send;
      let hd = null;
      const row = E("div"); row.style.cssText = "display:flex;gap:8px;align-items:center;margin-top:4px"; row.append(s, n); r.append(row, info);
      if (!c.main) { const l = E("label", "mut"); hd = E("input"); hd.type = "checkbox"; hd.checked = !!c.head; hd.onchange = send; l.append(hd, " " + T("sits on the head (turns with it) - for the panorama")); r.appendChild(l); }
      bx.appendChild(r);
    });
    if (sl) sl.before(bx); else sec.appendChild(bx);
  }
  async function poll() {
    try { const r = await fetch("/api/place?lite=1&lang=" + L(), {cache: "no-store"}); if (r.ok) S = await r.json(); } catch (e) {}
    try { card(); offer(); } catch (e) {}
    setTimeout(poll, 20000);
  }
  setInterval(() => { try { fov(); } catch (e) {} }, 1500);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(poll, 600)); else setTimeout(poll, 600);
})();
</script>
"""


def _place_de(keys):
    return {k: DE.get(k, k) for k in keys}


PLACE_PAGE_KEYS = ["Set up the place", "1 Look around", "2 Mark", "3 Done", "Put MoveEye where it will guard. The head looks around once: it takes a photo in every direction and watches for about 10 seconds what moves and what the AI recognises. Then you only mark your tent, the access, your valuables and what to ignore.", "the whole circle (360°)", "about", "Pan range of the servo {servo}°, with the lens it sees {cover} (camera {hf}°).",
                   "No full turn: the head turns only as far as its servo goes.", "{n} directions in {rows} rows - about {min} minutes.",
                   "Use the wide-angle camera ({cam}, {deg}°): {n} directions, about {min} min", "Thorough: 3 rows instead of 2 (takes longer)",
                   "Camera height (m)", "Height of the lens above the ground - helps to tell animals from persons at night.",
                   "Simulator: pole {m} m - counts while connected",
                   "It is dark: the night reference is made now.", "with the infrared light", "with the thermal camera too", "Start looking around",
                   "Show the last look-around", "Place set up on {when}: {n} things marked", "Forget the place",
                   "Forget the place? Its zones, waypoints and guarded things are removed.", "The head turns by itself - please do not stand in front of it.",
                   "Cancel", "taking the photo", "watching what moves", "making the panorama", "Direction {i} of {n}", "left", "Tap a suggestion to take it, or choose a button and draw a box on the panorama with your finger. Swipe sideways with ✋.",
                   "My tent / camper", "Access / path", "Public path", "Valuables", "Ignore", "Move / select", "Show the thermal picture",
                   "suggestion - tap to take it", "marked", "the picture goes on after the seam (360°)", "Take all suggestions", "Nothing marked yet.",
                   "Remove", "public path = only report", "Patrol: the head looks at the accesses now and then", "Apply", "Look around again",
                   "protection zone, lights / siren aim here, a person close by counts more", "line: a person crossing it is reported + patrol point",
                   "persons there: only a note, no alarm", "guarded: in the morning «Bike missing»", "mask: movement there is ignored",
                   "The place is set up", "{n} protection zone(s) at the tent", "{n} line(s) at the accesses", "{n} public path(s): only reported",
                   "{n} mask(s): ignored", "{n} patrol point(s)", "{n} guarded thing(s) - reported in the morning when missing",
                   "The guarded things follow after the reference scan of the main camera.", "{n} zone(s) not made: at most 12 zones",
                   "Nothing marked - nothing changed.", "Now test it: walk past like a visitor would. MoveEye beeps at every detection.",
                   "Start the walk test", "Look at the zones", "Back to Schutz",
                   "Bike", "Motorbike", "Car", "Camper?", "Chair", "Bench", "Backpack", "Suitcase", "Bag", "Umbrella", "Table", "Path?", "Road?", "Moves by itself"]
PLACE_MAIN_KEYS = ["Set up the place", "Place set up", "things marked", "MoveEye put up? Let it look around once: tent, access, valuables, what to ignore.",
                   "New place? Set it up again", "MoveEye put up? Set up the place", "2-3 minutes: the head looks around, you only tap tent, access, valuables.",
                   "Later", "Field of view of the camera", "Main camera", "Extra camera", "from the simulator", "detected",
                   "not detected - Camera Module 3 assumed", "chosen", "own value", "standard", "sits on the head (turns with it) - for the panorama"]


def place_page():
    js = "Object.assign(I18N.de, " + json.dumps(_place_de(PLACE_PAGE_KEYS), ensure_ascii=False) + ");"
    return render_page(PLACE_PAGE, "place").replace("/*PLACEDE*/", js, 1)


def _place_main_js():
    return PLACE_MAIN_JS.replace("/*PLDE*/{}", json.dumps(_place_de(PLACE_MAIN_KEYS), ensure_ascii=False))


NAV_SUB["protect"].append(("place", "/place", "Set up the place"))     # Schutz · Zonen · Platz einrichten
NAV_OF["place"] = "protect"
COMMON_JS = COMMON_JS.replace('"Game corner": "Spielecke"}};', '"Game corner": "Spielecke", "Set up the place": "Platz einrichten"}};', 1)
WEB_PAGE = WEB_PAGE.replace("</body>", "<!--PLACEJS--></body>", 1)     # filled by 624 (after the German texts are known)


def place_routes(app, watch, reply, body):
    """the addresses (called once by the web server, 550)"""
    from flask import Response, request, g, send_file

    @app.route("/place")
    def place_web_page():
        return Response(place_page(), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/place", methods=["GET", "POST"])
    def api_place():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "GET":
            if request.args.get("lite") == "1":
                rec = _place_load()
                return reply({"ok": True, "offer": place_offer(), "busy": PLACE["busy"],
                              "record": {"t": rec.get("t"), "items": rec.get("items") or []} if rec else None})
            return reply(dict(place_state(lang), ok=True))
        d = body(); lang = norm_lang(d.get("lang") or lang); op = str(d.get("op") or "")
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        if op == "start":
            ok, err = place_start(bool(d.get("ir", True)), bool(d.get("thermal", True)), bool(d.get("wide")), int(d.get("rows") or 2) if str(d.get("rows") or "2").isdigit() else 2, "web")
            return reply({"ok": ok, "error": tr(err, lang) if err else None}, 200 if ok else 400)
        if op == "stop":
            place_stop()
        elif op == "apply":
            ok, err, res = place_apply(d.get("items") or [], True, bool(d.get("patrol")), "web")
            if not ok:
                return reply({"ok": False, "error": tr_err(err, lang)}, 400)
            return reply({"ok": True, "result": res})
        elif op == "height":                            # real-reh-fusspunkt: «Höhe der Kamera (m)» (232 cam_height)
            try:
                v_ = round(float(d.get("value")), 2)
            except (TypeError, ValueError):
                return reply({"ok": False, "error": "number"}, 400)
            if not 0.2 <= v_ <= 10.0:
                return reply({"ok": False, "error": "0.2 … 10 m"}, 400)
            CFG["cam_height"] = v_; save_settings()
            return reply({"ok": True, "m": v_})
        elif op == "dismiss":
            place_offer_dismiss()
        elif op == "clear":
            place_clear("web")
        else:
            return reply({"ok": False, "error": "unknown"}, 400)
        return reply({"ok": True})

    @app.route("/place/file/<fn>")
    def place_file(fn):
        if not re.fullmatch(r"(pano|pano_th|pos_\d{2}|th_\d{2})\.jpg", fn):
            return Response("not found", 404)
        p_ = place_dir("scan", fn)
        return send_file(p_, mimetype="image/jpeg", max_age=60) if os.path.isfile(p_) else Response("not found", 404)

    @app.route("/api/camfov", methods=["GET", "POST"])
    def api_camfov():
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "POST":
            if getattr(g, "role", "admin") != "admin":
                return reply({"ok": False, "error": "not allowed"}, 403)
            d = body(); lang = norm_lang(d.get("lang") or lang)
            ok, err = cam_fov_set(d.get("spec"), str(d.get("model") or ""), d.get("deg"), d.get("head") if isinstance(d.get("head"), bool) else None)
            if not ok:
                return reply({"ok": False, "error": tr_err(err, lang)}, 400)
        return reply(dict(cam_fov_list(lang), ok=True))


SELFTEST_EXTRA.append(("Set up the place (directions, plan, items)", place_selftest))
SELFTEST_EXTRA.append(("Field of view per camera (cam_fov_h)", cam_fov_selftest))
