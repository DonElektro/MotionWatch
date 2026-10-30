#@ Motion Watch – Teil 470: Web: Seite Simulator. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
SIMMAP_JS = r"""// ---- map of the simulator (control type "map", from 2.93.16): swisstopo map / aerial picture, drag, wheel / two fingers,
// tap = choose the place where MoveEye stands, search (swisstopo), «Load this place» -> the simulator builds it
function simMap(c, send) {
  const T = (k, z, x, y) => "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo." + k + "/default/current/3857/" + z + "/" + x + "/" + y + ".jpeg";
  const W2 = (z) => 256 * Math.pow(2, z);
  const lx = (lo, z) => (lo + 180) / 360 * W2(z);
  const ly = (la, z) => { const s = Math.sin(la * Math.PI / 180); return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * W2(z); };
  const xl = (x, z) => x / W2(z) * 360 - 180;
  const yl = (y, z) => { const n = Math.PI - 2 * Math.PI * y / W2(z); return 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n))); };
  const inCH = (la, lo) => la > 45.8 && la < 47.85 && lo > 5.9 && lo < 10.5;
  const box = document.createElement("div"); box.style.cssText = "flex:1 1 100%;width:100%;grid-column:1/-1";
  const lab = el("div", "top", c.label); box.appendChild(lab);
  const sr = document.createElement("div"); sr.style.cssText = "display:flex;gap:6px;margin:4px 0";
  const q = document.createElement("input"); q.type = "search"; q.placeholder = t("Search a place (e.g. Zermatt)"); q.style.cssText = "flex:1;min-width:0;padding:8px 10px;border-radius:10px;border:1px solid var(--line,#1f2b3a);background:var(--field,#0c121a);color:var(--txt,#e8eef5)";
  const sb = el("button", "sec", "🔎"); sb.type = "button";
  const kb = el("button", "sec", t("Aerial picture")); kb.type = "button";
  sr.append(q, sb, kb); box.appendChild(sr);
  const res = document.createElement("div"); res.style.cssText = "display:flex;flex-direction:column;gap:4px;margin-bottom:4px"; box.appendChild(res);
  const map = document.createElement("div");
  map.style.cssText = "position:relative;height:300px;overflow:hidden;border-radius:10px;background:#cfd6cf;touch-action:none;cursor:crosshair;user-select:none";
  const lay = document.createElement("div"); lay.style.cssText = "position:absolute;left:0;top:0"; map.appendChild(lay);
  const sq = document.createElement("div"); sq.style.cssText = "position:absolute;border:2px solid #f5862a;background:rgba(245,134,42,.12);pointer-events:none;display:none";
  const mk = document.createElement("div"); mk.style.cssText = "position:absolute;width:14px;height:14px;margin:-9px 0 0 -9px;border-radius:50%;background:#f0571a;border:2px solid #fff;pointer-events:none;display:none";
  const at = el("div", "", "© swisstopo"); at.style.cssText = "position:absolute;right:4px;bottom:2px;font-size:10px;color:#222;background:rgba(255,255,255,.7);padding:0 4px;border-radius:4px";
  map.append(sq, mk, at); box.appendChild(map);
  const info = el("div", "mut", t("Tap on the map where MoveEye stands. Drag = move, two fingers or wheel = zoom.")); info.style.margin = "4px 0"; box.appendChild(info);
  const go = el("button", "", t("Load this place")); go.type = "button"; go.disabled = true; box.appendChild(go);
  let kind = "pixelkarte-farbe", z = 7, cx = lx(8.23, 7), cy = ly(46.8, 7), sel = null, imgs = {};
  const v = String(c.value || "").match(/(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)/);
  if (v && inCH(+v[1], +v[2])) { sel = {la: +v[1], lo: +v[2], name: ""}; z = 15; cx = lx(sel.lo, z); cy = ly(sel.la, z); go.disabled = false; }
  function draw() {
    const w = map.clientWidth, h = map.clientHeight; if (!w) return;
    const tlx = cx - w / 2, tly = cy - h / 2, n = Math.pow(2, z), keep = {};
    for (let ty = Math.floor(tly / 256); ty <= Math.floor((tly + h) / 256); ty++) for (let tx = Math.floor(tlx / 256); tx <= Math.floor((tlx + w) / 256); tx++) {
      if (tx < 0 || ty < 0 || tx >= n || ty >= n) continue;
      const k = kind + "/" + z + "/" + tx + "/" + ty; keep[k] = 1;
      let im = imgs[k]; if (!im) { im = document.createElement("img"); im.src = T(kind, z, tx, ty); im.draggable = false; im.style.cssText = "position:absolute;width:256px;height:256px"; lay.appendChild(im); imgs[k] = im; }
      im.style.left = (tx * 256 - tlx) + "px"; im.style.top = (ty * 256 - tly) + "px";
    }
    for (const k in imgs) if (!keep[k]) { imgs[k].remove(); delete imgs[k]; }
    if (sel) {
      const px = lx(sel.lo, z) - tlx, py = ly(sel.la, z) - tly, mpp = 40075016.7 * Math.cos(sel.la * Math.PI / 180) / W2(z), hs = 200 / mpp;
      mk.style.display = "block"; mk.style.left = px + "px"; mk.style.top = py + "px";
      sq.style.display = hs > 5 ? "block" : "none"; sq.style.left = (px - hs) + "px"; sq.style.top = (py - hs) + "px"; sq.style.width = sq.style.height = (2 * hs) + "px";
    }
  }
  function zoomAt(px, py, dz) {
    const z2 = Math.max(7, Math.min(19, z + dz)); if (z2 === z) return;
    const f = Math.pow(2, z2 - z), w = map.clientWidth, h = map.clientHeight;
    const ax = cx + px - w / 2, ay = cy + py - h / 2;
    cx = ax * f - (px - w / 2); cy = ay * f - (py - h / 2); z = z2; draw();
  }
  function choose(px, py) {
    const w = map.clientWidth, h = map.clientHeight, la = yl(cy + py - h / 2, z), lo = xl(cx + px - w / 2, z);
    if (!inCH(la, lo)) { info.textContent = t("Only in Switzerland"); return; }
    sel = {la: la, lo: lo, name: ""}; go.disabled = false; info.textContent = la.toFixed(5) + ", " + lo.toFixed(5); draw();
  }
  const P = new Map(); let moved = 0, pinch = 0;
  map.addEventListener("pointerdown", e => { map.setPointerCapture(e.pointerId); P.set(e.pointerId, {x: e.offsetX, y: e.offsetY}); moved = 0; if (P.size === 2) { const a = [...P.values()]; pinch = Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y); } });
  map.addEventListener("pointermove", e => {
    const p = P.get(e.pointerId); if (!p) return;
    const r = map.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (P.size === 1) { cx -= x - p.x; cy -= y - p.y; moved += Math.abs(x - p.x) + Math.abs(y - p.y); draw(); }
    p.x = x; p.y = y;
    if (P.size === 2) {
      moved = 99; const a = [...P.values()], d = Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y);
      if (pinch && d / pinch > 1.6) { zoomAt((a[0].x + a[1].x) / 2, (a[0].y + a[1].y) / 2, 1); pinch = d; }
      else if (pinch && d / pinch < 0.62) { zoomAt((a[0].x + a[1].x) / 2, (a[0].y + a[1].y) / 2, -1); pinch = d; }
    }
  });
  const up = e => { const p = P.get(e.pointerId); P.delete(e.pointerId); if (p && P.size === 0 && moved < 6) { const r = map.getBoundingClientRect(); choose(e.clientX - r.left, e.clientY - r.top); } };
  map.addEventListener("pointerup", up); map.addEventListener("pointercancel", e => P.delete(e.pointerId));
  map.addEventListener("wheel", e => { e.preventDefault(); const r = map.getBoundingClientRect(); zoomAt(e.clientX - r.left, e.clientY - r.top, e.deltaY < 0 ? 1 : -1); }, {passive: false});
  map.addEventListener("dblclick", e => { const r = map.getBoundingClientRect(); zoomAt(e.clientX - r.left, e.clientY - r.top, 1); });
  kb.onclick = () => { kind = kind === "pixelkarte-farbe" ? "swissimage" : "pixelkarte-farbe"; kb.textContent = t(kind === "swissimage" ? "Map" : "Aerial picture"); for (const k in imgs) { imgs[k].remove(); delete imgs[k]; } draw(); };
  async function search() {
    const s = q.value.trim(); if (!s) return; res.textContent = "";
    try {
      const r = await fetch("https://api3.geo.admin.ch/rest/services/api/SearchServer?type=locations&sr=4326&limit=6&searchText=" + encodeURIComponent(s));
      const d = await r.json(); const L = (d.results || []).filter(x => x.attrs && x.attrs.lat);
      if (!L.length) { info.textContent = t("Nothing found"); return; }
      L.forEach(x => { const name = String(x.attrs.label || "").replace(/<[^>]*>/g, ""); const b = el("button", "sec", name); b.type = "button"; b.style.textAlign = "left";
        b.onclick = () => { sel = {la: x.attrs.lat, lo: x.attrs.lon, name: name}; z = 16; cx = lx(sel.lo, z); cy = ly(sel.la, z); res.textContent = ""; go.disabled = false; info.textContent = name; draw(); };
        res.appendChild(b); });
    } catch (e) { info.textContent = t("Search not possible – tap the place on the map"); }
  }
  sb.onclick = search; q.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); search(); } });
  go.onclick = () => { if (!sel) return; send(sel.la.toFixed(6) + ", " + sel.lo.toFixed(6) + (sel.name ? ", " + sel.name.replace(/,/g, " ") : "")); info.textContent = t("The simulator loads the place (about a minute the first time)."); };
  if (window.ResizeObserver) new ResizeObserver(() => draw()).observe(map); else setTimeout(draw, 300);
  return box;
}

// ---- control of the simulator (from 2.93.16): built like the panel in the window of the simulator - a card per group with
// its symbol, parts inside that open and close, switches on the right, «Simple | Expert», search. Rows keep data-cid /
// .simv / .simvv, so the code that refreshes the values stays the same.
const SC_ICON = {
  link: '<path d="M9 7H7a5 5 0 0 0 0 10h2M15 7h2a5 5 0 0 1 0 10h-2M8 12h8"/>',
  camera: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7l2-3h4l2 3"/><circle cx="12" cy="13.5" r="3.5"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><ellipse cx="12" cy="12" rx="4" ry="9"/>',
  cloud: '<path d="M7 17h10a4 4 0 0 0 0-8 6 6 0 0 0-11.5 1.5A3.3 3.3 0 0 0 7 17z"/><path d="M9 20l-1 2M14 20l-1 2"/>',
  person: '<circle cx="12" cy="7" r="3.5"/><path d="M5 21a7 7 0 0 1 14 0z"/>',
  lens: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="2.6" fill="currentColor"/>',
  bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><circle cx="12" cy="20.5" r="1.4" fill="currentColor"/>',
  pad: '<rect x="2" y="7" width="20" height="11" rx="4"/><path d="M7 12.5h4M9 10.5v4"/><circle cx="15" cy="11.5" r="1.2" fill="currentColor"/><circle cx="17.5" cy="14" r="1.2" fill="currentColor"/>',
  target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/><path d="M12 1v5M12 18v5M1 12h5M18 12h5"/>',
  check: '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 12l3 3 5-6"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/><circle cx="12" cy="12" r="6.5"/>',
  keys: '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h1M10 10h1M14 10h1M18 10h1M7 14h10"/>',
  track: '<rect x="2" y="11" width="20" height="8" rx="4"/><circle cx="7" cy="15" r="1.8"/><circle cx="12" cy="15" r="1.8"/><circle cx="17" cy="15" r="1.8"/><path d="M8 11V6h8v5"/>'};
function scCss() {
  if (document.getElementById("simctl-css")) return;
  const s = document.createElement("style"); s.id = "simctl-css";
  s.textContent = `
.sc-top{display:flex;gap:6px;margin:6px 0 10px}.sc-top input{flex:1;min-width:0;padding:8px 10px;border-radius:10px;border:1px solid var(--line,#1f2b3a);background:var(--field,#0c121a);color:var(--txt,#e8eef5)}
.sc-card{background:var(--panel,#111822);border:1px solid var(--line,#1f2b3a);border-radius:12px;margin:0 0 10px;overflow:hidden}
.sc-hd{display:flex;align-items:center;gap:9px;width:100%;padding:11px 12px;background:none;border:0;color:var(--txt,#e8eef5);cursor:pointer;font:inherit;text-align:left}
.sc-hd svg{width:20px;height:20px;flex:none;fill:none;stroke:var(--mut,#8a9bb0);stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.sc-hd .sc-t{flex:1;font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase}
.sc-hd .sc-ar{color:var(--mut,#8a9bb0);font-size:12px}
.sc-bd{display:none;padding:0 12px 12px}.sc-card.open>.sc-bd{display:block}
.sc-sub{border-top:1px solid var(--line,#1f2b3a);margin-top:8px}
.sc-sh{display:block;width:100%;background:none;border:0;padding:8px 0 4px;color:var(--mut,#8a9bb0);font:inherit;font-size:13px;text-align:left;cursor:pointer}
.sc-sub.open>.sc-sh{color:var(--txt,#e8eef5)}.sc-sb{display:none;padding-left:10px}.sc-sub.open>.sc-sb{display:block}
.sc-row{margin:8px 0}.sc-tg{display:flex;align-items:center;gap:10px;cursor:pointer}.sc-tg span{flex:1}
.sc-sl .sc-l{display:flex;justify-content:space-between;gap:8px}.sc-sl input{width:100%}
.sc-se select,.sc-tx input{width:100%;margin-top:4px;padding:8px 10px;border-radius:10px;border:1px solid var(--line,#1f2b3a);background:var(--field,#0c121a);color:var(--txt,#e8eef5)}
.sc-bt{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:8px 0}.sc-bt button{min-height:38px;padding:6px 8px;border-radius:10px;
  border:1px solid var(--line,#1f2b3a);background:var(--panel2,#1a2433);color:var(--txt,#e8eef5);font:inherit;cursor:pointer;line-height:1.25}
.sc-bt button:active{background:var(--acc,#3b8cff);color:#fff}.sc-bt button.wide{grid-column:1/-1}
.sc-sw{appearance:none;-webkit-appearance:none;flex:none;width:44px;height:26px;border-radius:99px;background:var(--line,#2a3646);position:relative;cursor:pointer;transition:.2s;margin:0}
.sc-sw::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;transition:.2s}
.sc-sw:checked{background:var(--grn,#3fcf6b)}.sc-sw:checked::after{left:21px}
.sc-seg{display:flex;border:1px solid var(--line,#1f2b3a);border-radius:10px;overflow:hidden;margin:4px 0}.sc-seg button{flex:1;padding:9px;border:0;background:var(--panel,#111822);color:var(--txt,#e8eef5);font:inherit;cursor:pointer}
.sc-seg button.on{background:var(--acc,#3b8cff);color:#fff}.sc-none{margin:8px 2px}
.sc-hide{display:none!important}
.sc-sub.sc-fine{border-top:1px dashed var(--line,#1f2b3a)}.sc-sub.sc-fine>.sc-sh{color:var(--acc2,var(--acc,#3b8cff));font-size:11px;letter-spacing:.06em;text-transform:uppercase}
.sc-card.sc-on1>.sc-hd svg{stroke:var(--grn,#3fcf6b)}.sc-card.sc-on1>.sc-hd .sc-ar{color:var(--grn,#3fcf6b)}
.sc-card.sc-on2>.sc-hd svg{stroke:var(--org,#f2a33a)}.sc-card.sc-on2>.sc-hd .sc-ar{color:var(--org,#f2a33a)}`;
  document.head.appendChild(s);
}
function scOn(G, r) {                               // 2.95.51: the symbol of a group is green when something is on (3D-3.43 sends groups_on)
  const O = (r && r.groups_on) || {}; if (!G) return;
  G.querySelectorAll(".sc-card[data-g]").forEach(c => { const v = O[c.dataset.g] || 0; c.classList.toggle("sc-on1", v === 1); c.classList.toggle("sc-on2", v === 2); });
}
// 2.98.15 (Konzept-Check): the group «Spiel» shows only assistant / start / stop - everything else is set in the game wizard
// (simulator 3D-4.7: «Spiel-Karte schlank», those controls come with «wiz»; for older simulators the list below decides)
const SC_GAME_MAIN = ["game_wizard", "game_start", "game_stop"];
// 2.98.24: the groups by their fixed id «gid» (simulator 3D-4.7), the visible name only for older simulators
const scGid = c => c.gid || ({"Spiel": "game", "Game": "game", "Testlauf": "testrun", "Test run": "testrun"})[c.group] || "";
function scExpert(c) { return !!c.expert; }
function scWizOnly(c) { return !!c.wiz || (!("gid" in c) && scGid(c) === "game" && SC_GAME_MAIN.indexOf(c.id) < 0); }
// 2.98.23 (Konzept): the simulator group «Testlauf» is not shown in the Simulator control (testing has ONE place: group «Testen»,
// tile «Tests»); there it is built with data-only="testrun" (#tr-sim, recordings of the sneak paths, Pi 5 settings)
const SC_TEST_DUP = ["testrun_plan", "testrun_start", "testrun_stop"];   // the same as «Testlauf starten» of MoveEye right above (/api/simtest)
try { Object.assign(I18N.de, {"from MoveEye (setting of MoveEye, only shown here)": "von MoveEye (Einstellung von MoveEye, hier nur angezeigt)", "Fine-tuning": "Feineinstellungen"}); } catch (e) {}   // Aufräumen 2
// 639d (Angleichen, Daniel 30.10.2026): «Einfach» like everywhere - the Experte settings sit in a closed «Feineinstellungen (n)» of
// their part / card (not hidden); the group «Entwickler» (gid dev) only with MoveEye's «Entwickler-Bereich» (dev_area, also sent to
// the simulator, which shows its group the same way)
const scDev = c => scGid(c) === "dev";
function simCtlBuild(G, r, ctl, fmt) {
  scCss();
  const only = G.dataset.only || "";
  r = Object.assign({}, r, {controls: (r.controls || []).filter(c => !scWizOnly(c) && (only ? scGid(c) === only && SC_TEST_DUP.indexOf(c.id) < 0 : scGid(c) !== "testrun"))});
  const ls = (k, d) => { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } };
  const ss = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const openC = new Set(ls("mw-sc-open", ["Szene", "Besuch"])), openS = new Set(ls("mw-sc-sub2", ["Besuch/Vorlagen", "Besuch/Menschen schicken", "Besuch/Tiere schicken", "Spiel/Runde"]));
  // Aufräumen 2: Einfach / Experte is stored in the settings of MoveEye (page «sim», /api/ui_simple like the main page and the
  // simulator centre 139) - no longer per browser; the first build asks once, later builds take the known value
  let expert = only ? true : window.SC_EXPERT != null ? window.SC_EXPERT : false, q = G.dataset.q || "";
  if (only) (r.controls || []).forEach(c => openC.add(c.group));
  G.textContent = "";
  const top = el("div", "sc-top"); const qi = document.createElement("input"); qi.type = "search"; qi.placeholder = t("Search a setting …"); qi.value = q;
  top.appendChild(qi); G.appendChild(top);
  const none = el("div", "mut sc-none", t("Nothing found")); none.hidden = true; G.appendChild(none);
  const byG = {}, order = [];
  (r.controls || []).forEach(c => { const g = c.group || t("Controls"); if (!byG[g]) { byG[g] = []; order.push(g); } byG[g].push(c); });
  const cards = [];
  order.forEach(g => {
    const cs = byG[g], card = el("div", "sc-card"); card.dataset.g = g; if (openC.has(g)) card.classList.add("open");
    const hd = document.createElement("button"); hd.type = "button"; hd.className = "sc-hd";
    const ik = (cs.find(c => c.iconk) || {}).iconk, ie = (cs.find(c => c.icon) || {}).icon;
    hd.innerHTML = (ik && SC_ICON[ik] ? '<svg viewBox="0 0 24 24">' + SC_ICON[ik] + '</svg>' : (ie ? "<span>" + String(ie).replace(/[&<>"']/g, c => "&#" + c.charCodeAt(0) + ";") + "</span>" : "")) + '<span class="sc-t"></span><span class="sc-ar"></span>';
    hd.querySelector(".sc-t").textContent = g;
    const ar = () => { hd.querySelector(".sc-ar").textContent = card.classList.contains("open") ? "▼" : "▶"; };
    hd.onclick = () => { card.classList.toggle("open"); ar(); card.classList.contains("open") ? openC.add(g) : openC.delete(g); ss("mw-sc-open", [...openC]); };
    ar(); const bd = el("div", "sc-bd"); card.append(hd, bd); G.appendChild(card); cards.push(card);
    const subs = {}, fines = new Map();
    if (cs.some(scDev)) card.dataset.dev = "1";
    cs.forEach(c => {
      let tgt = bd; const sub = !only && c.sub === "Feineinstellungen" ? "" : c.sub || "";   // 639d: one fold «Feineinstellungen» per card
      if (sub) {
        if (!subs[sub]) {
          const key = g + "/" + sub, w = el("div", "sc-sub"); if (openS.has(key) || (only && sub === "Störungen" && location.hash === "#c-stoer")) w.classList.add("open");
          const sh = document.createElement("button"); sh.type = "button"; sh.className = "sc-sh";
          const p = () => { sh.textContent = (w.classList.contains("open") ? "▾  " : "▸  ") + sub; };
          sh.onclick = () => { w.classList.toggle("open"); p(); w.classList.contains("open") ? openS.add(key) : openS.delete(key); ss("mw-sc-sub2", [...openS]); };
          p(); const sb = el("div", "sc-sb"); w.append(sh, sb); bd.appendChild(w); subs[sub] = sb;
        }
        tgt = subs[sub];
      }
      if (!only && (scExpert(c) || c.sub === "Feineinstellungen") && !scDev(c)) {      // 639d: into the «Feineinstellungen» of its part
        if (!fines.has(tgt)) { const w = el("div", "sc-sub sc-fine"), sh = document.createElement("button"), sb = el("div", "sc-sb"); sh.type = "button"; sh.className = "sc-sh";
          sh.onclick = () => { w.classList.toggle("open"); w.dataset.own = "1"; scFineP(w); }; w.append(sh, sb); tgt.appendChild(w); fines.set(tgt, w); }
        tgt = fines.get(tgt).querySelector(".sc-sb");
      }
      let row;
      if (c.type === "map") { row = simMap(c, v => ctl({ctl: "set", id: c.id, value: v})); row.classList.add("sc-row"); }
      else if (c.type === "button") {
        let grid = tgt.lastElementChild; if (!grid || !grid.classList.contains("sc-bt")) { grid = el("div", "sc-bt"); tgt.appendChild(grid); }
        const x = el("button", "", (c.emoji ? c.emoji + " " : "") + c.label); x.type = "button"; if (c.label.length > 26) x.className = "wide";
        x.onclick = () => ctl({ctl: "press", id: c.id}); x.dataset.lab = c.label; x.dataset.ex = scExpert(c) && only ? "1" : ""; grid.appendChild(x); return;
      } else if (c.type === "toggle") {
        row = el("label", "sc-row sc-tg"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sc-sw simv";
        cb.onchange = () => ctl({ctl: "set", id: c.id, value: cb.checked}); row.append(el("span", "", c.label), cb);
      } else if (c.type === "slider") {
        row = el("div", "sc-row sc-sl"); const l = el("div", "sc-l"); const vv = el("span", "mut simvv"); l.append(el("span", "", c.label), vv);
        const rg = document.createElement("input"); rg.type = "range"; rg.className = "simv"; rg.min = c.min; rg.max = c.max; rg.step = c.step || 1;
        if (c.ro) { rg.disabled = true; rg.title = t("from MoveEye (setting of MoveEye, only shown here)"); }   // Aufräumen 2: e.g. the battery size
        let lvT = 0, lvW = null;                      // «live» (simulator 3D-4.x, e.g. the height of the pole): sent while dragging, 5× a second at most
        const lvSend = () => { lvW = null; lvT = Date.now(); ctl({ctl: "set", id: c.id, value: +rg.value}); };
        rg.oninput = () => { vv.textContent = fmt(c, +rg.value); if (c.live && !lvW) lvW = setTimeout(lvSend, Math.max(0, 200 - (Date.now() - lvT))); };
        rg.onchange = () => { clearTimeout(lvW); lvW = null; ctl({ctl: "set", id: c.id, value: +rg.value}); }; row.append(l, rg);
      } else if (c.type === "select") {
        row = el("div", "sc-row sc-se"); const se = document.createElement("select"); se.className = "simv";
        (c.options || []).forEach(o => { const op = document.createElement("option"); op.value = o[0]; op.textContent = o[1] || o[0]; se.appendChild(op); });
        se.onchange = () => ctl({ctl: "set", id: c.id, value: se.value}); row.append(el("div", "", c.label), se);
      } else {
        row = el("div", "sc-row sc-tx"); const ti = document.createElement("input"); ti.className = "simv";
        ti.onkeydown = e => { if (e.key === "Enter") ctl({ctl: "set", id: c.id, value: ti.value}); }; row.append(el("div", "", c.label), ti);
      }
      row.dataset.cid = c.id; row.dataset.lab = c.label; row.dataset.ex = scExpert(c) && only ? "1" : ""; tgt.appendChild(row);
    });
    fines.forEach(w => { w.parentNode.appendChild(w); scFineP(w); });            // «Feineinstellungen» last in its part / card
  });
  const seg = el("div", "sc-seg"); const b1 = el("button", "", t("Simple")), b2 = el("button", "", t("Expert")); b1.type = b2.type = "button"; seg.append(b1, b2); G.appendChild(seg);
  const note = el("div", "mut", t("Simple: only the important settings. «Expert» shows all.")); G.appendChild(note);
  if (only) { top.hidden = true; seg.hidden = true; }
  function apply() {
    q = qi.value.trim().toLowerCase(); G.dataset.q = qi.value; let any = false;
    b1.classList.toggle("on", !expert); b2.classList.toggle("on", expert); note.hidden = expert || !!only;
    cards.forEach(card => {
      let vis = 0;
      card.querySelectorAll(".sc-fine").forEach(w => { if (!w.dataset.own) w.classList.toggle("open", expert); });   // 639d: closed in «Einfach», open in «Experte»
      card.querySelectorAll("[data-lab]").forEach(n => { const ok = (q ? n.dataset.lab.toLowerCase().includes(q) : true) && (expert || q || n.dataset.ex !== "1"); n.classList.toggle("sc-hide", !ok); if (ok) vis++; });
      card.querySelectorAll(".sc-sub").forEach(w => { const n = w.querySelectorAll("[data-lab]:not(.sc-hide)").length; w.classList.toggle("sc-hide", !n); if (q && n) w.classList.add("open"); });
      card.querySelectorAll(".sc-bt").forEach(b => b.classList.toggle("sc-hide", !b.querySelector("button:not(.sc-hide)")));
      card.querySelectorAll(".sc-fine").forEach(scFineP);
      if (card.dataset.dev && !window.SC_DEV) vis = 0;                         // 639d: «Entwickler» only with dev_area
      card.classList.toggle("sc-hide", !vis); if (q && vis) { card.classList.add("open"); any = true; }
      const ar = card.querySelector(".sc-ar"); ar.textContent = card.classList.contains("open") ? "▼" : "▶";
    });
    none.hidden = !q || any;
  }
  const setEx = v => { expert = v; window.SC_EXPERT = v; apply();
    fetch("/api/ui_simple", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({on: !v, page: "sim"})}).catch(() => {}); };
  qi.oninput = apply; b1.onclick = () => setEx(false); b2.onclick = () => setEx(true);
  apply();
  if (!only && window.SC_EXPERT == null) fetch("/api/ui_simple?page=sim").then(x => x.json()).then(j => { window.SC_EXPERT = !j.on; window.SC_DEV = !!j.dev; expert = window.SC_EXPERT; apply(); }).catch(() => {});
  if (only && location.hash === "#c-stoer" && !window.SC_STOER) G.querySelectorAll(".sc-sub.open").forEach(w => {   // 639d: link «Störungen» (Entwickler)
    if (/Störungen/.test(w.textContent.slice(0, 40))) { window.SC_STOER = 1; setTimeout(() => w.scrollIntoView({block: "start", behavior: "smooth"}), 300); } });
}
function scFineP(w) {                                // 639d: «▸ Feineinstellungen (n)»
  const n = w.querySelectorAll(".sc-sb [data-lab]").length, sh = w.querySelector(":scope > .sc-sh");
  sh.textContent = (w.classList.contains("open") ? "▾  " : "▸  ") + t("Fine-tuning") + " (" + n + ")";
}

// ---- the simulator window (3D-3.18): mouse / finger / keys on a picture of /sim/view.mjpg go to the simulator ----
function simViewBind(VI, opt) {
  opt = opt || {};
  let Q = [], qT = null;
  const flush = () => { qT = null; if (!Q.length) return; const ev = Q; Q = [];
    post("/api/sim", {action: "view_in", ev: ev, lang: LANG}).catch(() => {}); };
  const push = (e, now) => { if (e.t === "move" && Q.length && Q[Q.length - 1].t === "move") Q[Q.length - 1] = e; else Q.push(e);
    if (now) { clearTimeout(qT); flush(); } else if (!qT) qT = setTimeout(flush, 70); };
  const pos = (ev) => { const r = VI.getBoundingClientRect(); return {x: Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)), y: Math.max(0, Math.min(1, (ev.clientY - r.top) / r.height))}; };
  const pts = new Map(); let pinch = 0, btn = 0, tap = null;
  const ctlOn = () => !opt.ctl || opt.ctl();             // finger: control the simulator (else the page scrolls, a tap still clicks)
  const tAct = () => { VI.style.touchAction = ctlOn() ? "none" : "pan-x pan-y pinch-zoom"; };
  tAct(); setInterval(tAct, 500);
  VI.addEventListener("contextmenu", e => { if (!opt.active || opt.active()) e.preventDefault(); });
  VI.addEventListener("pointerdown", e => {
    if (opt.active && !opt.active()) return;
    if (e.pointerType !== "mouse" && !ctlOn()) { tap = {id: e.pointerId, x: e.clientX, y: e.clientY, t: Date.now()}; return; }
    e.preventDefault(); VI.focus({preventScroll: true});
    try { VI.setPointerCapture(e.pointerId); } catch (x) {}
    pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
    if (pts.size === 2) {                                   // two fingers: let go of the drag, zoom by pinching
      if (btn) { push(Object.assign({t: "up", b: btn}, pos(e)), true); btn = 0; }
      const [a, b] = [...pts.values()]; pinch = Math.hypot(a.x - b.x, a.y - b.y); return;
    }
    if (pts.size > 2) return;
    btn = e.pointerType === "mouse" ? ({0: 1, 1: 3, 2: 2}[e.button] || 1) : (opt.rot && opt.rot() ? 2 : 1);
    const p = pos(e); push(Object.assign({t: "move"}, p)); push(Object.assign({t: "down", b: btn, shift: e.shiftKey, alt: e.altKey}, p), true);
  });
  VI.addEventListener("pointermove", e => {
    if (tap && tap.id === e.pointerId) { if (Math.hypot(e.clientX - tap.x, e.clientY - tap.y) > 10) tap = null; return; }
    if (opt.active && !opt.active()) return;
    if (pts.has(e.pointerId)) pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
    if (pts.size === 2 && pinch) { const [a, b] = [...pts.values()], d = Math.hypot(a.x - b.x, a.y - b.y);
      if (Math.abs(d - pinch) > 40) { const c = pos({clientX: (a.x + b.x) / 2, clientY: (a.y + b.y) / 2}); push(Object.assign({t: "wheel", d: d > pinch ? 1 : -1}, c), true); pinch = d; } return; }
    if (e.pointerType !== "mouse" && !btn) return;
    push(Object.assign({t: "move"}, pos(e)));
  });
  const upH = e => {
    if (tap && tap.id === e.pointerId) { const ok = e.type === "pointerup" && Date.now() - tap.t < 700; tap = null;
      if (ok) { const p = pos(e); push(Object.assign({t: "move"}, p)); push(Object.assign({t: "down", b: 1}, p)); push(Object.assign({t: "up", b: 1}, p), true); } return; }
    if (pts.delete(e.pointerId) && btn) { push(Object.assign({t: "up", b: btn}, pos(e)), true); btn = 0; } if (pts.size < 2) pinch = 0; };
  VI.addEventListener("pointerup", upH); VI.addEventListener("pointercancel", upH);
  VI.addEventListener("dblclick", e => { if (opt.active && !opt.active()) return; const p = pos(e); push(Object.assign({t: "dbl", b: 1}, p)); push(Object.assign({t: "up", b: 1}, p), true); });
  VI.addEventListener("wheel", e => { if (opt.active && !opt.active()) return; if (!ctlOn() && document.activeElement !== VI) return; e.preventDefault(); push(Object.assign({t: "wheel", d: e.deltaY < 0 ? 1 : -1}, pos(e)), true); }, {passive: false});
  const KEYS = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d", "q", "e", "r", "f", "PageUp", "PageDown", "0", "1", "2", "3", "4", "5", "+", "-", "Shift"];
  const keyH = down => e => { if (opt.active && !opt.active()) return; const k = e.key.length === 1 ? e.key.toLowerCase() : e.key; if (!KEYS.includes(k)) return; e.preventDefault(); if (down && e.repeat) return; push({t: "key", k: k, down: down}, true); };
  VI.addEventListener("keydown", keyH(true)); VI.addEventListener("keyup", keyH(false));
  return {push: push};
}

// ---- touch controls on the simulator window (2.95.11): left stick = fly (W A S D), right stick = look around, ▲ ▼ = up / down ----
function simTouchPad(box, VB, show) {
  if (!document.getElementById("stp-css")) { const st = document.createElement("style"); st.id = "stp-css"; st.textContent =
    ".stp{position:absolute;inset:0;pointer-events:none;z-index:1}.stp .stk{position:absolute;bottom:22%;width:clamp(96px,22vmin,150px);aspect-ratio:1;border-radius:50%;" +
    "background:rgba(10,14,20,.35);border:2px solid rgba(255,255,255,.45);pointer-events:auto;touch-action:none}.stp .stk.l{left:14px}.stp .stk.r{right:62px}" +
    ".stp .kn{position:absolute;left:50%;top:50%;width:42%;height:42%;margin:-21% 0 0 -21%;border-radius:50%;background:rgba(255,255,255,.75);pointer-events:none}" +
    ".stp .lb{position:absolute;left:0;right:0;bottom:-20px;text-align:center;font-size:11px;color:#fff;text-shadow:0 1px 2px #000}" +
    ".stp .ud{position:absolute;left:calc(clamp(96px,22vmin,150px) + 30px);bottom:22%;display:flex;flex-direction:column;gap:8px;pointer-events:auto}" +
    ".stp .ud button{width:42px;height:42px;border-radius:10px;border:1px solid rgba(255,255,255,.4);background:rgba(10,14,20,.55);color:#fff;font-size:18px;touch-action:none}";
    document.head.appendChild(st); }
  const P = document.createElement("div"); P.className = "stp"; P.hidden = true;
  P.innerHTML = '<div class="stk l"><div class="kn"></div><div class="lb">fliegen</div></div><div class="stk r"><div class="kn"></div><div class="lb">umschauen</div></div>' +
    '<div class="ud"><button type="button" data-k="e">▲</button><button type="button" data-k="q">▼</button></div>';
  box.appendChild(P);
  const held = new Set(), key = (k, on) => { if (on === held.has(k)) return; on ? held.add(k) : held.delete(k); VB.push({t: "key", k: k, down: on}, true); };
  setInterval(() => held.forEach(k => VB.push({t: "key", k: k, down: true}, true)), 400);     // the simulator lets go by itself without news
  const stick = (el, onMove, onEnd) => {
    const kn = el.querySelector(".kn"); let id = null;
    const at = e => { const r = el.getBoundingClientRect(); let x = (e.clientX - r.left) / r.width * 2 - 1, y = (e.clientY - r.top) / r.height * 2 - 1;
      const m = Math.hypot(x, y); if (m > 1) { x /= m; y /= m; } kn.style.transform = "translate(" + x * 60 + "%," + y * 60 + "%)"; return [x, y]; };
    el.addEventListener("pointerdown", e => { e.preventDefault(); e.stopPropagation(); id = e.pointerId; try { el.setPointerCapture(id); } catch (x) {} onMove(...at(e), true); });
    el.addEventListener("pointermove", e => { if (e.pointerId !== id) return; e.preventDefault(); onMove(...at(e), false); });
    const end = e => { if (e.pointerId !== id) return; id = null; kn.style.transform = ""; onEnd(); };
    el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
  };
  stick(P.querySelector(".stk.l"), (x, y) => { key("w", y < -0.35); key("s", y > 0.35); key("a", x < -0.35); key("d", x > 0.35); key("Shift", Math.hypot(x, y) > 0.95); },
    () => ["w", "s", "a", "d", "Shift"].forEach(k => key(k, false)));
  let lk = null, lv = [0, 0], cur = [0.5, 0.5];                  // looking: a drag with the right mouse button that goes on while the stick is held
  stick(P.querySelector(".stk.r"), (x, y, first) => { lv = [x, y];
      if (first) { cur = [0.5, 0.5]; VB.push({t: "move", x: 0.5, y: 0.5}); VB.push({t: "down", b: 2, x: 0.5, y: 0.5}, true);
        lk = setInterval(() => { cur = [cur[0] + lv[0] * 0.012, cur[1] + lv[1] * 0.008];
          if (cur[0] < 0.05 || cur[0] > 0.95 || cur[1] < 0.05 || cur[1] > 0.95) {        // at the edge: let go and start again in the middle
            VB.push({t: "up", b: 2, x: cur[0], y: cur[1]}); cur = [0.5, 0.5]; VB.push({t: "move", x: 0.5, y: 0.5}); VB.push({t: "down", b: 2, x: 0.5, y: 0.5}, true); }
          else VB.push({t: "move", x: cur[0], y: cur[1]}); }, 50); } },
    () => { clearInterval(lk); lk = null; VB.push({t: "up", b: 2, x: cur[0], y: cur[1]}, true); });
  P.querySelectorAll(".ud button").forEach(b => { const k = b.dataset.k;
    b.addEventListener("pointerdown", e => { e.preventDefault(); e.stopPropagation(); try { b.setPointerCapture(e.pointerId); } catch (x) {} key(k, true); });
    ["pointerup", "pointercancel"].forEach(n => b.addEventListener(n, () => key(k, false))); });
  setInterval(() => { const on = !!show(); if (P.hidden === on) { P.hidden = !on; if (!on) { ["w", "s", "a", "d", "e", "q", "Shift"].forEach(k => key(k, false)); } } }, 300);
  return P;
}

// ---- the picture of the simulator window, fetched one by one (2.95.10): always the newest, never a growing delay ----
// 2.95.81: the page asks for exactly its size (shown width × pixel density of the screen), a quality and WebP when the
// browser shows it. «Bildqualität»: automatisch (measures how fast the pictures come and steps down / up), hoch, mittel, niedrig.
const SIMQ = [{n: "low", f: 0.5, q: 55}, {n: "mid", f: 0.75, q: 70}, {n: "high", f: 1.0, q: 82}, {n: "max", f: 1.0, q: 90}];
let SIM_WEBP = false;
(() => { const i = new Image(); i.onload = () => { SIM_WEBP = i.width === 1; }; i.src = "data:image/webp;base64,UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA"; })();
function simQMode() { try { return localStorage.getItem("mw-simq") || "auto"; } catch (e) { return "auto"; } }
function simViewPoll(VI, fps) {
  let on = false, gen = 0, url = "", lvl = 2, slow = 0, fast = 0, ema = 0;
  const info = {w: 0, q: 0, fmt: "", kb: 0, lvl: 2, mode: "auto"};
  const params = () => {
    const mode = simQMode(); info.mode = mode;
    if (mode !== "auto") lvl = {low: 0, mid: 1, high: 2, max: 3}[mode] ?? 2;
    const L = SIMQ[lvl], dpr = Math.min(window.devicePixelRatio || 1, 3);
    const box = VI.closest("details, .card, section") || VI.parentElement;     // the card, not the picture (it shrinks with a small picture)
    const cw = (document.fullscreenElement || VI.closest(".fs")) ? window.innerWidth : Math.max(VI.clientWidth, box.clientWidth || 0) || 640;
    const w = Math.max(320, Math.min(2560, Math.round(cw * dpr * L.f / 16) * 16));
    info.w = w; info.q = L.q; info.fmt = SIM_WEBP ? "webp" : "jpg"; info.lvl = lvl;
    const fs = !!(document.fullscreenElement || document.webkitFullscreenElement || VI.closest(".fs"));
    const clean = fs && (typeof PVPAD === "undefined" || !PVPAD);      // 2.95.92: full screen: the simulator hides its rover stick
    return "w=" + w + "&q=" + L.q + "&fmt=" + info.fmt + (clean ? "&clean=1" : "") + (VI.closest("[data-bare]") ? "&bare=1" : "") + (VI.closest("[data-dock]") ? "&dock=1" : "");   // 538: without the buttons of the window; /sim: only the 3D view + dock
  };
  const step = async (g) => {
    if (!on || g !== gen) return;
    const t0 = Date.now(); let wait = 1000;
    try {
      const r = await fetch("/sim/view.jpg?" + params() + "&r=" + t0, {cache: "no-store"});
      if (r.ok) { const b = await r.blob(); if (on && g === gen && b.size > 0) { const u = URL.createObjectURL(b); const old = url; url = u; VI.src = u;
        if (old) setTimeout(() => URL.revokeObjectURL(old), 1000); info.kb = Math.round(b.size / 1024); }
        const target = 1000 / (fps || 8), dt = Date.now() - t0;
        ema = ema ? ema * 0.7 + dt * 0.3 : dt;
        if (info.mode === "auto") {                    // too slow -> smaller / softer, fast for a while -> sharper
          if (ema > target * 2.5) { slow++; fast = 0; if (slow >= 4 && lvl > 0) { lvl--; slow = 0; ema = 0; } }
          else if (ema < target * 1.2) { fast++; slow = 0; if (fast >= 10 && lvl < 3) { lvl++; fast = 0; ema = 0; } }
          else { slow = 0; fast = 0; } }
        wait = Math.max(0, target - dt); }
    } catch (e) {}
    setTimeout(() => step(g), wait);
  };
  return {start() { if (on) return; on = true; gen++; step(gen); }, stop() { on = false; gen++; }, get on() { return on; }, info};
}
// 2.95.83: a game controller at this browser (PS5, Xbox, …: paired with the PC or the phone) drives the rover in the
// simulator - also when the simulator runs in a virtual machine that cannot see the controller. Start = explore on / off.
const SIMPAD = {name: "", on: false};
(function simPadLink() {
  if (window._simPad || !navigator.getGamepads) return; window._simPad = true;
  let last = "", lastT = 0, idle = true;
  const tick = () => {
    let g = null; try { g = [...navigator.getGamepads()].find(x => x && x.connected); } catch (e) {}
    SIMPAD.on = !!g; SIMPAD.name = g ? String(g.id).replace(/\(.*?\)/g, "").trim().slice(0, 40) : "";
    if (!g || document.hidden || (typeof window.mwPadOwn === "function" && window.mwPadOwn())) return;   // the «Controller-Ansicht» (538) has its own mapping
    // 2.98.10: the sticks go to the simulator unchanged - it takes off the drift itself (rest position + round dead zone)
    const ax = [0, 1, 2, 3].map(i => Math.round((g.axes[i] || 0) * 1000) / 1000);
    const bt = g.buttons.slice(0, 17).map(b => Math.round((b.value || (b.pressed ? 1 : 0)) * 100) / 100);
    const sig = JSON.stringify([ax.map(v => Math.round(v * 50)), bt]), neutral = ax.every(v => Math.abs(v) < 0.25) && bt.every(v => v === 0), now = Date.now();
    if (neutral && idle) return;                     // nothing pressed: nothing to send
    if (sig === last && now - lastT < 300) return;   // unchanged: only now and then (the simulator lets go after 0.6 s)
    last = sig; lastT = now; idle = neutral;
    post("/api/sim", {action: "pad", ax: ax, bt: bt, name: SIMPAD.name}).then(r => { if (r && r.rumble && window.MWPad) MWPad.rumble(g, r.rumble); });   // 2.98.41: the simulator lets it vibrate (542)
  };
  setInterval(tick, 66);
  addEventListener("gamepadconnected", e => { if (typeof window.mwPadAsk === "function" && window.mwPadAsk(e)) return; try { toast("🎮 " + t("Controller connected") + ": " + String(e.gamepad.id).replace(/\(.*?\)/g, "").trim().slice(0, 40) + " – " + t("Start = menu of the simulator, left stick = head, right stick = rover")); } catch (x) {} });
})();
function simQBox(VP) {                             // «Bildqualität» under the picture of the simulator window
  try { if (I18N && I18N.de) Object.assign(I18N.de, {"Controller connected": "Controller verbunden", "Start = menu of the simulator, left stick = head, right stick = rover": "Start = Menü des Simulators, linker Stick = Kopf, rechter Stick = Rover", "Picture quality": "Bildqualität", "automatic": "automatisch", "very high": "sehr hoch", "high": "hoch", "medium": "mittel", "low": "niedrig"}); } catch (e) {}
  if (!document.getElementById("simq-css")) { const c = document.createElement("style"); c.id = "simq-css";
    c.textContent = ".simq{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:13px;margin-top:8px}.simq select{padding:4px 8px;font-size:13px;width:auto}"; document.head.appendChild(c); }
  const box = document.createElement("div"); box.className = "simq";
  const sel = document.createElement("select");
  [["auto", "automatic"], ["max", "very high"], ["high", "high"], ["mid", "medium"], ["low", "low"]].forEach(([v, l]) => { const o = document.createElement("option"); o.value = v; o.textContent = t(l); sel.appendChild(o); });
  sel.value = simQMode();
  sel.onchange = () => { try { localStorage.setItem("mw-simq", sel.value); } catch (e) {} };
  const lab = document.createElement("span"); lab.textContent = t("Picture quality") + ":";
  const st = document.createElement("span"); st.className = "mut";
  box.append(lab, sel, st);
  setInterval(() => { const I = VP.info; st.textContent = (I.w ? I.w + " px · " + (I.fmt === "webp" ? "WebP" : "JPEG") + " " + I.q + " % · " + I.kb + " kB" + (I.mode === "auto" ? " · " + t(["low", "medium", "high", "very high"][I.lvl]) : "") : "")
    + (SIMPAD.on ? " · 🎮 " + SIMPAD.name + " (" + t("Start = menu of the simulator, left stick = head, right stick = rover") + ")" : ""); }, 1000);
  return box;
}
"""


SIM_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Simulator</title>
<style>
/*BASECSS*/
#c-prev{scroll-margin-top:calc(var(--hdr-h,64px) + 10px)}
main.simp{max-width:1500px;margin:0 auto;padding:20px 16px 40px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;align-items:start}
.sc{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.sc.wide{grid-column:1/-1}
details.fold{padding:0}
details.fold>summary{list-style:none;cursor:pointer;padding:16px 20px;display:flex;align-items:center;user-select:none;border-radius:14px}
details.fold>summary::-webkit-details-marker{display:none}
details.fold>summary:hover{background:var(--field)}
details.fold>summary h2{flex:1;margin:0}
details.fold>summary::after{content:"▾";color:var(--mut);font-size:15px;transition:transform .15s;margin-left:10px}
details.fold:not([open])>summary::after{transform:rotate(-90deg)}
details.fold.act>summary::after{color:var(--grn,#3fb950)}
/* 2.95.69: the symbol is green too while the function works (red: switched on, but it does not work) */
details.fold.act>summary h2 svg{color:var(--grn,#3fb950)}details.fold.bad>summary h2 svg,details.fold.bad>summary::after{color:var(--red,#ff5b4b)}
[data-need][hidden],.needhide{display:none!important}
.hsub{font-weight:400;font-size:13px;margin-left:2px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.opt.first{border-top:0;padding-top:0}
details.sub{border-top:1px solid var(--line);padding-top:4px}
details.sub>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:8px 0;font-size:14px;font-weight:600}
details.sub>summary::-webkit-details-marker{display:none}
details.sub>summary svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;color:var(--mut);flex:none}
details.sub>summary>span{flex:1}
details.sub>summary::after{content:"▾";color:var(--mut);font-size:14px;transition:transform .15s}details.sub:not([open])>summary::after{transform:rotate(-90deg)}
details.sub.act>summary svg,details.sub.act>summary::after{color:var(--grn,#3fb950)}
details.sub>*+*{margin-top:8px}
details.fold>.fb{padding:0 20px 18px}
details.fold>.fb>*+*{margin-top:12px}
details.fold>.fb>.mut:first-child{margin-top:0}

.sc h2{margin:0 0 4px;font-size:16px;font-weight:600;display:flex;align-items:center;gap:10px}
.sc h2 svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;color:var(--mut);flex:none}
.sc>.mut:first-of-type{margin-bottom:10px}
.sc .mut{font-size:13px;line-height:1.5}
.sc>*+*{margin-top:12px}
.sthead{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.sdot{width:12px;height:12px;border-radius:50%;background:var(--mut);flex:none}
.sdot.ok{background:var(--grn);box-shadow:0 0 8px var(--grn)}.sdot.bad{background:var(--red)}
.sttl{font-size:20px;font-weight:600;flex:1;min-width:0}
#s-btn{padding:10px 18px;font-size:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px}
/* test run and optimization (2.95.22) */
.tr-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.tr-row select{flex:1 1 240px;min-width:0}
.tr-prog{height:8px;border-radius:5px;background:var(--field);overflow:hidden}.tr-prog i{display:block;height:100%;background:var(--acc,#3b82f6);transition:width .5s}
.tr-tab{width:100%;border-collapse:collapse;font-size:13px}.tr-tab td,.tr-tab th{padding:5px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.tr-tab th{font-weight:600;color:var(--mut);font-size:12px}.tr-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}.tr-tab{min-width:560px}.tr-tab td:last-child{min-width:150px}
.tr-sug{border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:grid;gap:6px}.tr-sug b{font-size:15px}
.tr-sug .ch{font-size:13px;display:flex;flex-wrap:wrap;gap:4px 12px}.tr-sug .ch span{white-space:nowrap}.tr-sug .ch s{opacity:.6}
.tr-chip{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 9px;font-size:12px;margin:2px 4px 2px 0}
.tr-good{color:var(--grn,#3fb950)}.tr-bad{color:#f85149}.tr-hist{display:flex;align-items:flex-end;gap:4px;height:70px;border-bottom:1px solid var(--line);padding-top:4px}
.tr-hist i{flex:1;max-width:34px;background:var(--acc,#3b82f6);border-radius:4px 4px 0 0;min-height:3px;position:relative}.tr-hist i.cur{background:var(--grn,#3fb950)}
.tile{border:1px solid var(--line);border-radius:10px;padding:8px 10px}.tile .mut{font-size:11px}.tile b{font-weight:600;font-size:15px}
.opt{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:11px 0;border-top:1px solid var(--line);font-size:14px;cursor:pointer}
.row2{display:flex;gap:8px;align-items:center}.row2 input[type=text]{flex:1;min-width:0}
.fnd{display:flex;align-items:center;gap:10px;padding:9px 10px;border:1px solid var(--line);border-radius:10px}
.fnd+.fnd{margin-top:6px}.fnd .n{flex:1;min-width:0}.fnd .n b{font-weight:500}.fnd .n .mut{font-size:12px}
.fnd.cur{border-color:var(--grn)}.fnd .host{margin-left:8px;font-size:13px;color:var(--mut);white-space:nowrap}
.rng{display:flex;justify-content:space-between;font-size:14px}
.dl{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.dl a,.dl button{display:flex;flex-direction:column;align-items:flex-start;gap:2px;text-align:left;padding:10px 12px;font-size:14px}
.dl a small,.dl button small{font-weight:400;font-size:12px;opacity:.75}
.dl .main{grid-column:1/-1}.dlic{width:26px;height:26px;border-radius:7px;vertical-align:middle;margin-right:4px}
#c-prev>.fb>*+*{margin-top:8px}#c-prev>.fb{padding:0 12px 12px}#c-prev.full>summary{padding:10px 10px}
/* 2.95.20: the simulator window uses the whole width of the screen (out of the page column) */
#c-prev.full{width:calc(100vw - var(--sbw,0px));margin-left:calc(50% - (100vw - var(--sbw,0px)) / 2);border-radius:0;border-left:0;border-right:0;padding:8px 6px}#c-prev.full>.fb{padding:0}
#c-prev.full .pvw{border-radius:6px}
#c-prev.full .pvw.view:not(.fs) #s-prev{max-height:none}
.pvw{position:relative;background:#000;border-radius:10px;overflow:hidden}
.gm{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
.chips2{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}.hcp{display:flex;align-items:center;gap:4px;border:1px solid var(--line);border-radius:999px;padding:3px 4px 3px 10px;font-size:13px}
.hcp select{padding:3px 6px;border-radius:999px;font-size:12px}
.spec{position:absolute;top:8px;left:50%;transform:translateX(-50%);max-width:min(62%,560px);z-index:2;pointer-events:none;background:rgba(8,12,18,.72);color:#fff;
  border-radius:12px;padding:7px 12px;font-size:13px;line-height:1.35;box-shadow:0 2px 10px rgba(0,0,0,.35)}
.spec-h{display:flex;gap:10px;align-items:baseline;justify-content:center;flex-wrap:wrap}.spec-h .tm{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}
.spec-h .tm.hot{color:#ff6b5b}.spec-h .sh{opacity:.8;font-size:12px}
.spec-p{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:5px}
.spec-p .pl{display:flex;align-items:center;gap:5px;background:rgba(255,255,255,.08);border-radius:999px;padding:2px 8px 2px 4px;font-size:12px}
.spec-p .dot{width:10px;height:10px;border-radius:50%}.spec-p .mb{width:34px;height:5px;border-radius:3px;background:rgba(255,255,255,.2);overflow:hidden}
.spec-p .mb i{display:block;height:100%;background:#3fb950}.spec-p .mb i.w{background:#e8b33a}.spec-p .mb i.d{background:#ff5b4b}
.spec-f{margin-top:4px;text-align:center;font-size:12px;opacity:.9;min-height:1em}
.specres{position:absolute;inset:0;z-index:3;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.5)}
.specres .bx{background:rgba(10,14,20,.94);color:#fff;border-radius:14px;padding:16px 20px;min-width:min(380px,90%);max-width:90%}
.specres h3{margin:0 0 8px;text-align:center}.specres .r{display:flex;gap:10px;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.1)}
.specres .r b{flex:1}.specres .r .sc{font-variant-numeric:tabular-nums;font-weight:700}.specres button{margin-top:10px;width:100%}
.pvw.fs .spec,.pvw:fullscreen .spec{font-size:15px}
#gw{position:fixed;inset:0;z-index:400;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:12px}
.gw-box{background:var(--panel,#111822);border:1px solid var(--line,#1f2b3a);border-radius:16px;width:min(760px,100%);max-height:100%;display:flex;flex-direction:column;overflow:hidden}
.gw-top{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--line,#1f2b3a)}.gw-x{margin-left:auto;padding:6px 12px}
.gw-steps{display:flex;gap:6px;flex-wrap:wrap}.gw-steps span{font-size:12px;padding:4px 10px;border-radius:999px;border:1px solid var(--line,#1f2b3a);color:var(--mut,#8b9bb0)}
.gw-steps span.on{background:var(--acc,#3b8cff);border-color:var(--acc,#3b8cff);color:#fff}.gw-steps span.done{color:var(--txt,#e8eef5)}
.gw-body{padding:16px;overflow:auto}.gw-body h3{margin:0 0 4px;font-size:20px}.gw-body .lead{margin:0 0 14px}
.gw-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}
.gw-card{text-align:left;padding:14px;border-radius:12px;border:2px solid var(--line,#1f2b3a);background:transparent;color:inherit;font:inherit;cursor:pointer;display:flex;flex-direction:column;gap:6px;min-height:120px}
.gw-pic{width:100%;aspect-ratio:16/9;border-radius:10px;display:block;margin-bottom:4px}.gw-card .ic:empty,.gw-q .ic:empty{display:none}
.gw-pics2{display:flex;gap:8px;margin:2px 0 10px}.gw-pics2 img{width:calc(50% - 4px);border-radius:10px}
.gw-card b{font-size:16px}.gw-card .ic{font-size:28px;line-height:1}.gw-card small{color:var(--mut,#8b9bb0);line-height:1.35}
.gw-card.on{border-color:var(--acc,#3b8cff);background:rgba(59,140,255,.12)}
.gw-quick{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:6px 0 16px}
.gw-q{text-align:left;padding:14px;border-radius:14px;border:2px solid var(--acc,#3b8cff);background:rgba(59,140,255,.14);color:inherit;font:inherit;cursor:pointer;display:flex;flex-direction:column;gap:4px}
.gw-q .ic{font-size:30px;line-height:1}.gw-q b{font-size:17px}.gw-q small{color:var(--mut,#8b9bb0);line-height:1.35}.gw-sub{font-weight:600;margin:4px 0 8px}
.gw-row{display:flex;align-items:center;gap:10px;margin:12px 0}.gw-row label{flex:1}.gw-row input[type=range]{flex:1}
.gw-sum{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:6px 0 14px}.gw-sum div:nth-child(odd){color:var(--mut,#8b9bb0)}
.gw-rules{border-left:3px solid var(--acc,#3b8cff);padding:4px 0 4px 12px;margin:10px 0}.gw-rules p{margin:6px 0}
.gw-err{background:rgba(255,80,60,.14);border:1px solid #c0392b;color:#ff8b7b;border-radius:10px;padding:8px 10px;margin:0 0 10px;font-size:13px}
.gw-ex{margin-top:12px;border:1px solid var(--line,#1f2b3a);border-radius:12px;padding:6px 12px}.gw-ex summary{cursor:pointer;padding:6px 0;font-weight:600}
.gw-board{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}.gw-board td{padding:4px 6px;border-bottom:1px solid var(--line,#1f2b3a)}
.gw-pics{display:flex;gap:6px;overflow-x:auto;margin-top:8px}.gw-pics figure{margin:0;font-size:11px;text-align:center}.gw-pics img{height:84px;border-radius:8px;display:block}
.gw-nav{display:flex;justify-content:space-between;gap:10px;padding:12px 16px;border-top:1px solid var(--line,#1f2b3a)}
.gw-qr{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:10px}.gw-qr img{width:200px;height:200px;image-rendering:pixelated;background:#fff;padding:6px;border-radius:8px}.gm-t{flex:1;min-width:220px}
.gm-qr img{width:180px;height:180px;image-rendering:pixelated;background:#fff;border-radius:8px;padding:6px;cursor:zoom-in;display:block}
.gm-url{font-size:18px;font-weight:600;margin-top:6px;word-break:break-all;user-select:all}
#g-bigov{position:fixed;inset:0;z-index:450;background:#fff;color:#111;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:16px}
#g-bigov img{width:min(80vw,70vh);height:min(80vw,70vh);image-rendering:pixelated}#g-urlbig{font-size:clamp(18px,4vw,34px);font-weight:700;word-break:break-all;text-align:center}
.supd{margin:10px 0 2px;padding:10px 12px;border-radius:10px;border:1px solid #b88a1c;background:rgba(240,180,40,.12)}
.supd-t{font-weight:600;color:#e8b33a}.supd-n{margin-top:3px}.sver{margin-top:6px;font-size:13px}
.pvmode{display:flex;border:1px solid var(--line,#1f2b3a);border-radius:10px;overflow:hidden;margin:0 0 10px}
.pvmode button{flex:1;padding:8px;border:0;border-radius:0;background:transparent;color:inherit;font:inherit;cursor:pointer}.pvmode button.on{background:var(--acc,#3b8cff);color:#fff}
.pvw.view img{cursor:grab;user-select:none;-webkit-user-select:none;outline:none}.pvw.view img:active{cursor:grabbing}
.pvbtn{position:absolute;right:8px;top:8px;display:flex;flex-direction:column;gap:6px;z-index:2}.pvbtn .pvbtn{position:static}
.pvw.fs{position:fixed;inset:0;z-index:200;border-radius:0;display:flex;align-items:center;justify-content:center;
  padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)}
.pvw.fs #s-prev,.pvw:fullscreen #s-prev{max-height:100vh;height:100%;width:100%}
.pvw:fullscreen{display:flex;align-items:center;justify-content:center;border-radius:0}
.pvbtn button{width:38px;height:38px;padding:0;border-radius:10px;border:1px solid rgba(255,255,255,.25);background:rgba(10,14,20,.65);color:#fff;font-size:18px;cursor:pointer}
.pvbtn button.on{background:var(--acc,#3b8cff)}
/* 2.95.92: full screen = only the picture of the simulator (the finger drives the view directly); 🕹 brings the sticks and buttons */
.pvw.fs:not(.pad) #s-pvbtn>button:not(#s-vpad),.pvw:fullscreen:not(.pad) #s-pvbtn>button:not(#s-vpad),.pvw.fs #s-vstat,.pvw:fullscreen #s-vstat{display:none}
.pvw.fs:not(.pad) #s-pvcam,.pvw:fullscreen:not(.pad) #s-pvcam{display:none}
.pvw.fs .pvbtn button,.pvw:fullscreen .pvbtn button{background:rgba(10,14,20,.4);border-color:rgba(255,255,255,.18)}
#s-prev{width:100%;height:auto;min-height:200px;object-fit:contain;background:#000;display:block;max-height:calc(100vh - var(--hdr-h,64px) - 170px)}
.pvcam{position:absolute;right:58px;top:10px;width:28%;max-width:320px;min-width:120px;border:2px solid rgba(255,255,255,.8);border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.5);background:#000;cursor:pointer;z-index:3}
.pvcam img{display:block;width:100%;border-radius:6px}.pvcam span{position:absolute;left:5px;top:5px;font:700 10px/1 system-ui,sans-serif;color:#fff;background:rgba(200,0,0,.75);padding:3px 5px;border-radius:4px}
.pvlive{position:absolute;left:10px;bottom:10px;font:700 11px/1 system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.55);padding:4px 8px;border-radius:6px}
#pip{position:fixed;z-index:45;width:min(44vw,300px);border-radius:12px;overflow:hidden;background:#000;cursor:pointer;touch-action:none;box-shadow:0 8px 26px rgba(0,0,0,.55);border:1px solid var(--line)}
#pip[hidden]{display:none}
#pip[data-c="br"]{right:12px;bottom:calc(env(safe-area-inset-bottom) + 12px)}#pip[data-c="bl"]{left:12px;bottom:calc(env(safe-area-inset-bottom) + 12px)}
#pip[data-c="tr"]{right:12px;top:calc(var(--hdr-h,64px) + 10px)}#pip[data-c="tl"]{left:12px;top:calc(var(--hdr-h,64px) + 10px)}
#pip .pip-in img{width:100%;height:auto;max-height:none;aspect-ratio:auto;display:block;pointer-events:none}
#pip .pip-live{position:absolute;left:6px;bottom:6px;font:700 10px/1 system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.55);padding:3px 6px;border-radius:6px}
#pip-x{position:absolute;top:5px;right:5px;width:28px;height:28px;border-radius:50%;border:0;background:rgba(0,0,0,.6);color:#fff;font-size:13px;line-height:28px;padding:0;min-height:0}
.cg{border-top:1px solid var(--line);padding-top:6px}
.cg>summary{cursor:pointer;padding:6px 0;font-weight:500;font-size:14px;list-style:none}
.cg>summary::-webkit-details-marker{display:none}.cg>summary::before{content:"▸ ";color:var(--mut)}.cg[open]>summary::before{content:"▾ "}
.cgb{display:flex;flex-wrap:wrap;gap:8px;padding:4px 0 10px}
.cgb .cr{flex:1 1 100%}.cgb>button{flex:1 1 30%;padding:8px 10px;font-size:13px}
.cgb .cr .top{display:flex;justify-content:space-between;font-size:14px;margin-bottom:2px}
.cgb label.cr{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:14px}
#s-scn{display:flex;gap:8px;flex-wrap:wrap}#s-scn select{flex:1 1 220px;min-width:0}
.howto{margin:0;padding-left:20px;font-size:14px;line-height:1.6}
.simq{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:13px;margin-top:8px}.simq select{padding:4px 8px;font-size:13px;width:auto}
@media(max-width:820px){main.simp{grid-template-columns:minmax(0,1fr);padding:12px 12px 32px}.sc{padding:14px}details.fold{padding:0}details.fold>summary{padding:14px}details.fold>.fb{padding:0 14px 14px}.dl{grid-template-columns:1fr}
  .tiles{grid-template-columns:repeat(auto-fill,minmax(100px,1fr))}}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main class="simp">
  <!-- 2.95.69: order by logic - 1 connection, 2 status, 3 (only when connected) picture, control, test run …; every card:
       symbol, name, arrow on the right; symbol and arrow green while its function works -->
  <details class="sc fold wide" id="c-conn" data-k="conn" open>
    <summary><h2><svg viewBox="0 0 24 24"><path d="M2 9.5a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/></svg><span data-i18n="Connection">Connection</span><span class="mut hsub" id="s-csub"></span></h2></summary>
    <div class="fb">
    <label class="opt first"><span><b style="font-weight:600" data-i18n="Simulation">Simulation</b><br><small class="mut" id="s-onnote"></small></span><input type="checkbox" class="sw" id="s-on" onchange="simOnOff()"></label>
    <div class="mut" data-i18n="conn-note">conn-note</div>
    <div class="row2"><input type="text" id="s-url" placeholder="http://192.168.1.50:8765" autocomplete="off"><button type="button" class="sec" onclick="saveUrl()" data-i18n="Save">Save</button></div>
    <label class="opt"><span data-i18n="Find the simulator in the network by itself">Find the simulator in the network by itself</span><input type="checkbox" class="sw" id="k-sim_auto" onchange="setKey('sim_auto', this.checked)"></label>
    <label class="opt"><span><span data-i18n="Switch the simulation on by itself when a simulator is online">Switch the simulation on by itself when a simulator is online</span><br><small class="mut" data-i18n="autostart-note">autostart-note</small></span><input type="checkbox" class="sw" id="k-sim_autostart" onchange="setKey('sim_autostart', this.checked)"></label>
    <label class="opt"><span><span data-i18n="Update the simulator by itself when a newer version is there">Update the simulator by itself when a newer version is there</span><br><small class="mut" data-i18n="upd-owner-note">This is the setting «Neue Versionen» of the simulator – the same here and there.</small></span><input type="checkbox" class="sw" id="k-sim_autoupd" onchange="setKey('sim_autoupd', this.checked)"></label>
    <div><b style="font-weight:600;font-size:14px" data-i18n="Simulators in the network">Simulators in the network</b><div class="mut" id="s-scan"></div></div>
    <div id="s-found"></div>
    <button type="button" class="sec" id="s-search" onclick="search()" style="width:100%" data-i18n="Search now">Search now</button>
    <details class="sub" id="c-tunnel">
      <summary><svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg><span data-i18n="Simulator behind a firewall">Simulator behind a firewall</span></summary>
      <div class="mut" data-i18n="tunnel-note">tunnel-note</div>
      <div id="tun-box" style="margin-top:8px"></div>
    </details>
    </div>
  </details>
  <details class="sc fold wide" id="c-status" data-k="status" data-need="on" open>
    <summary><h2><svg viewBox="0 0 24 24"><path d="M3 12h4l2.5-6 5 12 2.5-6H21"/></svg><span id="s-ttl">–</span></h2></summary>
    <div class="fb" id="s-stbody">
    <div class="supd" id="s-supd" hidden><div class="supd-t" id="s-supdt"></div><div class="mut supd-n" id="s-supdn"></div></div>
    <button type="button" class="sec" id="s-upd" onclick="simUpdate()" hidden>⟳ <span data-i18n="Update the simulator">Update the simulator</span></button>
    <div class="mut" id="s-msg"></div>
    <div class="mut sver" id="s-ver"></div>
    <div class="tiles" id="s-tiles"></div>
    </div>
  </details>
  <details class="sc fold wide" id="c-prev" data-k="prev" data-need="ok" open>
    <summary><h2><svg viewBox="0 0 24 24"><rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3"/></svg><span data-i18n="Live picture">Live picture</span></h2></summary>
    <div class="fb">
    <div class="pvmode" id="s-pvmode" hidden><button type="button" data-m="view">🗺 <span data-i18n="Simulator window">Simulator window</span></button><button type="button" data-m="cam">📷 <span data-i18n="Camera picture">Camera picture</span></button></div>
    <div class="pvw" id="s-pvw"><img id="s-prev" data-dock="1" alt="" draggable="false" tabindex="0"><span class="pvlive" id="s-pvlive" hidden>● LIVE</span>
      <div class="pvcam" id="s-pvcam" hidden title="Kamera gross zeigen"><img id="s-pvcimg" alt=""><span>📷 LIVE</span></div>
      <div class="spec" id="s-spec" hidden><div class="spec-h" id="s-spech"></div><div class="spec-p" id="s-specp"></div><div class="spec-f" id="s-specf"></div></div>
      <div class="specres" id="s-specres" hidden></div>
      <div class="pvbtn"><button type="button" id="s-vfs" title="Vollbild">⛶</button><button type="button" id="s-vstat" title="Statistik ein / aus" hidden>📊</button><span class="pvbtn" id="s-pvbtn" hidden><button type="button" id="s-vpad" title="Steuer-Sticks und Knöpfe ein / aus">🕹</button><button type="button" id="s-vgyro" title="Handy als Fenster: das Handy drehen = umschauen" hidden>📱</button><button type="button" id="s-vcam" title="Kamerabild klein ein / aus">📷</button><button type="button" id="s-vctl" title="Bedienen mit dem Finger (sonst scrollt die Seite)">✋</button><button type="button" id="s-vrot" title="Finger: drehen statt verschieben">⟲</button><button type="button" id="s-vin">＋</button><button type="button" id="s-vout">－</button></span></div></div>
    <div class="mut" id="s-prevnote"></div>
    </div>
  </details>
  <section class="sc wide" id="c-hub" data-need="ok" style="padding:12px 14px"><h2 style="margin:0 0 8px;font-size:15px">🎛 <span data-i18n="Simulator centre">Simulator centre</span></h2><div id="simhub" data-simhub="full" hidden></div></section>
  <details class="sc fold wide" id="c-game" data-k="game" data-need="ok" hidden open>
    <summary><h2><svg viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="11" rx="4"/><path d="M7 12.5h4M9 10.5v4"/><circle cx="15" cy="11.5" r="1"/><circle cx="17.5" cy="14" r="1"/></svg><span data-i18n="Game «Unseen to the goal»">Game «Unseen to the goal»</span></h2></summary>
    <div class="fb"><div class="gm">
      <div class="gm-qr" id="g-qrbox" hidden><img id="g-qr" alt="QR" onclick="gameBig(true)"></div>
      <div class="gm-t">
        <div class="mut" id="g-txt"></div>
        <div class="gm-url" id="g-url"></div>
        <div id="g-more"></div>
        <div class="btns" style="margin-top:10px"><button type="button" id="g-wiz" onclick="gwOpen()">🧭 <span data-i18n="Game wizard">Game wizard</span></button><button type="button" class="sec" id="g-open" onclick="gameOpen(true)"></button>
          <button type="button" class="sec" id="g-big" onclick="gameBig(true)" hidden>🔍 <span data-i18n="Show the QR code big">Show the QR code big</span></button>
          <button type="button" class="sec" id="g-close" onclick="gameOpen(false)" hidden data-i18n="Close the game">Close the game</button></div>
      </div>
    </div>
    </div>
  </details>
  <div id="gw" hidden><div class="gw-box">
    <div class="gw-top"><div class="gw-steps" id="gw-steps"></div><button type="button" class="sec gw-x" onclick="gwClose()" aria-label="close">✕</button></div>
    <div class="gw-body" id="gw-body"></div>
    <div class="gw-nav"><button type="button" class="sec" id="gw-back" onclick="gwGo(-1)">‹ <span data-i18n="Back">Back</span></button><button type="button" id="gw-next" onclick="gwGo(1)"></button></div>
  </div></div>
  <div id="g-bigov" hidden onclick="gameBig(false)"><img id="g-qrbig" alt="QR"><div id="g-urlbig"></div><div class="mut" data-i18n="Tap to close">Tap to close</div></div>
  <details class="sc fold wide" id="c-tools" data-k="tools" data-need="ok" hidden>
    <summary><h2><svg viewBox="0 0 24 24"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/></svg><span data-i18n="Simulator tools">Simulator tools</span></h2></summary>
    <div class="fb"><div id="st-box"></div></div>
  </details>

  <details class="sc fold wide" id="c-ctl" data-k="ctl" data-need="ok" open>
    <summary><h2><svg viewBox="0 0 24 24"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/></svg><span data-i18n="Simulator control">Simulator control</span><span class="mut" id="s-cname" style="font-weight:400"></span></h2></summary>
    <div class="fb">
    <div class="mut" id="s-cst" data-i18n="ctl-note">ctl-note</div>
    <div id="s-scn" hidden><select id="s-sel"></select><button type="button" onclick="scnLoad()" data-i18n="Load">Load</button><button type="button" class="sec" onclick="ctl({ctl:'get'})">↻</button><button type="button" class="sec" id="s-del" onclick="scnDel()" data-i18n="Delete">Delete</button></div>
    <div id="s-groups"></div>
    <div id="s-up" hidden><div class="mut" id="s-upl"></div><input type="file" id="s-file"><div class="mut" id="s-prog"></div></div>
    </div>
  </details>

  <!-- 2.98.23 (Konzept): no own card «Testlauf und Optimierung» any more - the test run is the tile «Tests» in the group
       «Testen» of the Simulator centre (139 moves #tr-box into its sheet); here only its parking place -->
  <div id="c-test" hidden>
    <div class="fb" id="tr-box">
    <div class="mut" data-i18n="tr-note">tr-note</div>
    <div class="tr-row"><select id="tr-plan"></select>
      <button type="button" id="tr-run">▶ <span data-i18n="Start test run">Start test run</span></button>
      <button type="button" class="sec" id="tr-auto">🤖 <span data-i18n="Optimize automatically">Optimize automatically</span></button>
      <button type="button" class="sec" id="tr-stop" hidden>⏹ <span data-i18n="Stop">Stop</span></button></div>
    <div class="mut" id="tr-autonote"></div>
    <div id="tr-live" hidden><div class="rng"><span id="tr-livet"></span><b id="tr-left"></b></div><div class="tr-prog"><i id="tr-bar" style="width:0"></i></div></div>
    <div id="tr-res"></div>
    <div id="tr-sim" data-only="testrun" style="margin-top:10px"></div>
    </div>
  </div>

  <details class="sc fold" id="c-perf" data-k="perf" data-need="ok">
    <summary><h2><svg viewBox="0 0 24 24"><path d="M13 3L4 14h7l-1 7 9-11h-7z"/></svg><span data-i18n="Computing power">Computing power</span></h2></summary>
    <div class="fb">
    <div class="mut" data-i18n="perf-note">perf-note</div>
    <label class="opt"><span data-i18n="Simulator: fewer pictures">Simulator: fewer pictures</span><input type="checkbox" class="sw" id="k-sim_eco" onchange="setKey('sim_eco', this.checked)"></label>
    <div><div class="rng"><span data-i18n="Pictures per second">Pictures per second</span><b id="v-sim_fps">–</b></div>
      <input type="range" id="k-sim_fps" min="2" max="15" step="1" oninput="$('#v-sim_fps').textContent=this.value" onchange="setKey('sim_fps', +this.value)"></div>
    </div>
  </details>

  <details class="sc fold" id="c-simset" data-k="simset">
    <summary><h2><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg><span data-i18n="Settings of the simulation">Settings of the simulation</span></h2></summary>
    <div class="fb"><div class="mut" data-i18n="simset-note">simset-note</div><div id="simset-box"></div></div>
  </details>

  <details class="sc fold" id="c-dl" data-k="dl">
    <summary><h2><svg viewBox="0 0 24 24"><path d="M12 3v12M7 10l5 5 5-5M4 19h16"/></svg><span data-i18n="Programs and downloads">Programs and downloads</span></h2></summary>
    <div class="fb">
    <div class="dl">
      <a class="btn main" id="d-3d" href="/sim/simulator3d.zip"><span><img class="dlic" src="/sim-icon/sim3d.png" alt=""> <span data-i18n="3D simulator for Windows (ZIP)">3D simulator for Windows (ZIP)</span></span><small id="d-3dn"></small></a>
      <a class="btn main" id="d-py" href="/sim/simulator_py.zip"><span><img class="dlic" src="/sim-icon/simwelt.png" alt=""> <span data-i18n="Python world simulator (ZIP)">Python world simulator (ZIP)</span></span><small id="d-pyn"></small></a>
      <a class="btn sec" href="/sim/simulator.zip"><span><img class="dlic" src="/sim-icon/simbasis.png" alt=""> <span data-i18n="Simple simulator (ZIP)">Simple simulator (ZIP)</span></span><small data-i18n="Python, for a PC or the Pi">Python, for a PC or the Pi</small></a>
      <a class="btn sec" href="/preview" target="_blank"><span>📱 <span data-i18n="Phone / tablet view">Phone / tablet view</span></span><small data-i18n="this page as on a phone">this page as on a phone</small></a>
      <button type="button" class="sec" id="p-inst" onclick="piAct('install')"><span id="p-instt">📦</span><small data-i18n="simple simulator directly on the Pi">simple simulator directly on the Pi</small></button>
      <button type="button" class="sec" id="p-start" onclick="piAct('start')"><span>▶ <span data-i18n="Start simulator here">Start simulator here</span></span><small data-i18n="on the Pi (uses its CPU)">on the Pi (uses its CPU)</small></button>
      <button type="button" class="sec" id="p-stop" onclick="piAct('stop')" hidden><span>⏹ <span data-i18n="Stop simulator">Stop simulator</span></span><small data-i18n="on the Pi">on the Pi</small></button>
    </div>
    <div class="mut" id="d-link"></div>
    </div>
  </details>

  <details class="sc fold wide" id="c-help" data-k="help">
    <summary><h2><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17h.01"/></svg><span data-i18n="How it works">How it works</span></h2></summary>
    <div class="fb">
    <ol class="howto">
      <li data-i18n="how-1">how-1</li><li data-i18n="how-2">how-2</li><li data-i18n="how-3">how-3</li><li data-i18n="how-4">how-4</li>
    </ol>
    </div>
  </details>
</main>
<div id="pip" hidden data-c="br"><div class="pip-in"></div><span class="pip-live">● LIVE</span><button type="button" id="pip-x" aria-label="close">✕</button></div>
<script>
/*COMMON*/
Object.assign(I18N.de, {"No access to the motion sensor": "Kein Zugriff auf den Bewegungssensor", "The motion sensor needs https (iPhone / iPad)": "Der Bewegungssensor braucht https (iPhone / iPad)",
 "Turn the phone to look round. Press 📱 again to stop.": "Handy drehen zum Umschauen. Nochmals 📱 drücken zum Beenden.",
 "Team against MoveEye": "Team gegen MoveEye",
 "gw-mwhand": "Die Spieler schleichen mit dem Handy. Die Wächter sitzen an MoveEye: sie drehen die echte Kamera mit dem Joystick auf der Live-Seite, zielen mit der Bildmitte auf einen Spieler und drücken den Auslöser 🎯 (oder R2 am Controller). Trifft der Kreis, ist der Spieler erwischt (Foto, Alarm, Punkte) – sonst gibt es einen Fehlalarm und 3 Sekunden Sperre.",
 "A task for every round (bonus)": "Eine Aufgabe für jede Runde (Bonus)",
 "gw-tasks": "🎯 Jede Runde hat eine Aufgabe, z. B. «nur kriechend ins Ziel» oder «nie über 50 % Verdacht». Wer sie schafft, bekommt Bonuspunkte. Neben der Rangliste des Abends gibt es eine Rangliste der Woche.",
 "Task of this round": "Aufgabe dieser Runde", "Ranking of the week": "Rangliste der Woche", "week": "Woche", "task done": "Aufgabe erfüllt",
 "Switch the simulation on by itself when a simulator is online": "Simulation von selbst einschalten, sobald ein Simulator online ist",
 "autostart-note": "Und wieder aus (zurück zu den echten Kameras und Sensoren), wenn eine Minute lang keiner mehr da ist. Von Hand ausgeschaltet: bleibt aus, bis wieder ein neuer Simulator auftaucht.",
 "persons found": "Personen erkannt", "false alarms": "Fehlalarme", "against": "gegen", "Version": "Version",
 "Pictures of the mistakes (what MoveEye saw)": "Bilder der Fehler (was MoveEye gesehen hat)", "False alarm": "Fehlalarm",
 "dark": "zu dunkel", "small": "klein / weit weg", "crouch": "geduckt", "?": "unklar", "fast": "schnell",
 "For the development": "Für die Entwicklung", "Report for the development": "Bericht für die Entwicklung",
 "dev-note": "Packt die letzten 10 Testläufe in eine Datei: Versionen, Erkennungs-Einstellungen, Ergebnisse, Ursachen und die Bilder der Fehler – ohne Passwörter, Schlüssel und Aufnahmen. Im Chat mit Claude anhängen oder auf GitHub in den Ordner «feedback» hochladen.",
 "Test run every night": "Jede Nacht ein Testlauf", "Saved": "Gespeichert",
 "night-note": "Läuft nur, wenn der Simulator verbunden ist und kein Spiel läuft. Eine Meldung kommt nur, wenn die Punktzahl um 10 oder mehr schlechter ist als in der Nacht davor.",
 "Test run and optimization": "Testlauf und Optimierung",
 "tr-note": "MoveEye Sim · 3D spielt einen festen Test ab (jedes Mal dieselben Besucher auf denselben Wegen) und weiss, wer wirklich zu sehen war. MoveEye vergleicht das mit dem, was es erkannt hat, und schlägt bessere Einstellungen vor. Du kannst sie einzeln oder alle übernehmen und rückgängig machen – oder «Automatisch optimieren» probiert sie nacheinander aus und behält nur, was im nächsten Test wirklich besser ist.",
 "Start test run": "Testlauf starten", "Optimize automatically": "Automatisch optimieren",
 "tr-auto-ask": "Automatisch optimieren: zuerst ein Testlauf wie jetzt, dann werden bis zu 4 Vorschläge nacheinander ausprobiert (je ein Testlauf). Behalten wird nur, was besser ist. Das dauert je nach Test 10 bis 35 Minuten. Starten?",
 "Standard (day, wind, night, rain · about 4 min)": "Standard (Tag, Wind, Nacht, Regen · etwa 4 Min.)", "Short (day and night · about 2 min)": "Kurz (Tag und Nacht · etwa 2 Min.)",
 "Difficult conditions (low sun, fog, snow, drops, spider web, headlights, cloud shadows · about 7 min)": "Schwierige Bedingungen (Gegenlicht, Nebel, Schnee, Tropfen, Spinnennetz, Scheinwerfer, Wolkenschatten · etwa 7 Min.)",
 "Night (dark, infrared, animals · about 3 min)": "Nacht (dunkel, Infrarot, Tiere · etwa 3 Min.)",
 "Connect the simulation first (3D simulator 3D-3.27 or newer).": "Zuerst die Simulation verbinden (MoveEye Sim · 3D ab 3D-3.27).",
 "Try": "Versuch", "first a test run as it is now": "zuerst ein Testlauf wie jetzt", "starting …": "startet …", "still about": "noch etwa",
 "No test run yet.": "Noch kein Testlauf.", "Last test run": "Letzter Testlauf", "Persons found": "Personen erkannt", "Reaction time": "Reaktionszeit",
 "False alarms": "Fehlalarme", "Animals taken for persons": "Tiere als Person gemeldet", "Score": "Punktzahl", "Phase": "Phase", "Persons": "Personen",
 "Reaction": "Reaktion", "Animals reported": "Tiere gemeldet", "Missed": "Verpasst", "too dark": "zu dunkel", "small / far": "klein / weit weg", "fast": "schnell",
 "crouching": "geduckt", "False alarms by cause": "Fehlalarme nach Ursache", "Proposals for MoveEye": "Vorschläge für MoveEye",
 "Everything found, no false alarm - nothing to improve.": "Alles erkannt, kein Fehlalarm – nichts zu verbessern.", "No proposals for this test run.": "Keine Vorschläge für diesen Testlauf.",
 "Take over all": "Alle übernehmen", "Take over all and test again": "Alle übernehmen und nochmals testen", "Undo the last change": "Letzte Änderung rückgängig",
 "Take over": "Übernehmen", "Take over and test again": "Übernehmen und nochmals testen",
 "(goes against another proposal - test again after taking it over)": "(widerspricht einem anderen Vorschlag – nach dem Übernehmen nochmals testen)",
 "Automatic optimization": "Automatische Optimierung", "Score at the start": "Punktzahl am Anfang", "now": "jetzt", "kept": "behalten", "not better, undone": "nicht besser, rückgängig gemacht",
 "Earlier test runs": "Frühere Testläufe", "When": "Wann", "Test": "Test", "Changed before": "Vorher geändert",
 "The previous settings are back": "Die vorherigen Einstellungen sind zurück", "Taken over - a new test run shows whether it is better": "Übernommen – ein neuer Testlauf zeigt, ob es besser ist",
 "on": "ein", "off": "aus", "stopped": "abgebrochen", "a test run is already going": "es läuft schon ein Testlauf", "the simulation is not connected": "die Simulation ist nicht verbunden",
 "nothing to undo": "nichts rückgängig zu machen", "the test run takes too long - stopped": "der Testlauf dauert zu lange – abgebrochen",
 "the simulator does not answer (3D-3.27 or newer needed)": "der Simulator antwortet nicht (3D-3.27 oder neuer nötig)",
 "Sensitivity": "Empfindlichkeit", "Smallest moving area": "Kleinste bewegte Fläche", "AI: minimum certainty": "KI: Mindest-Sicherheit", "AI looks at every n-th picture": "KI prüft jedes n-te Bild",
 "AI must confirm persons": "KI muss Personen bestätigen", "Wind filter": "Wind-Filter", "Wind filter: reacts from": "Wind-Filter: reagiert ab", "Wind filter: strongest": "Wind-Filter: höchstens",
 "Rain filter": "Regen-Filter", "Rain filter: reacts from": "Regen-Filter: reagiert ab", "Brighten in the dark": "Im Dunkeln aufhellen", "Brighten below": "Aufhellen unter",
 "Pictures to recognise walking": "Bilder bis Gehen erkannt", "Steadiness of walking": "Gleichmässigkeit des Gehens", "Shadow filter": "Schatten-Filter", "Vehicle filter": "Fahrzeug-Filter",
 "Objects: minimum certainty": "Objekte: Mindest-Sicherheit", "Auto-tune": "Selbst-Einstellung",
 "Calm down wind and cloud shadows": "Wind und Wolkenschatten beruhigen", "{n} false alarms from moving branches or cloud shadows: the wind filter reacts earlier and moving areas must be bigger.": "{n} Fehlalarme durch bewegte Äste oder Wolkenschatten: der Wind-Filter greift früher und bewegte Flächen müssen grösser sein.",
 "AI confirms every person": "KI bestätigt jede Person", "{n} false alarms from insects or a spider web in the light: a person only counts when the AI sees it.": "{n} Fehlalarme durch Insekten oder ein Spinnennetz im Licht: eine Person zählt nur, wenn die KI sie sieht.",
 "Stronger rain and snow filter": "Stärkerer Regen- und Schnee-Filter", "{n} false alarms from rain, snow or drops on the lens: the rain filter switches on earlier.": "{n} Fehlalarme durch Regen, Schnee oder Tropfen auf der Linse: der Regen-Filter schaltet früher ein.",
 "Ignore changes of the light": "Lichtwechsel nicht beachten", "{n} false alarms from low sun, headlights or fog: the shadow filter and the AI check what moves.": "{n} Fehlalarme durch tiefe Sonne, Scheinwerfer oder Nebel: Schatten-Filter und KI prüfen, was sich bewegt.",
 "Do not take animals for persons": "Tiere nicht für Personen halten", "{n} times an animal was reported as a person: the AI must be surer and small moving things count less.": "{n}-mal wurde ein Tier als Person gemeldet: die KI muss sicherer sein und kleine bewegte Dinge zählen weniger.",
 "Less sensitive": "Weniger empfindlich", "{n} false alarms without a clear cause: a bit less sensitive.": "{n} Fehlalarme ohne klare Ursache: etwas weniger empfindlich.",
 "See better in the dark": "Im Dunkeln besser sehen", "{n} persons were missed at night: brighten the picture earlier and let the AI accept less sure persons.": "{n} Personen in der Nacht verpasst: das Bild früher aufhellen und die KI auch weniger sichere Personen annehmen lassen.",
 "Find small and crouching persons": "Kleine und geduckte Personen finden", "{n} persons were far away, small or crouching and were missed: smaller moving areas count too.": "{n} Personen waren weit weg, klein oder geduckt und wurden verpasst: auch kleinere bewegte Flächen zählen.",
 "Catch fast persons": "Schnelle Personen erwischen", "{n} fast persons (joggers) were missed: fewer pictures needed to recognise walking, the AI looks at every picture.": "{n} schnelle Personen (Jogger) verpasst: weniger Bilder bis das Gehen erkannt ist, die KI prüft jedes Bild.",
 "More sensitive by day": "Am Tag empfindlicher", "{n} persons were missed by day: more sensitive and the AI accepts less sure persons.": "{n} Personen am Tag verpasst: empfindlicher, und die KI nimmt auch weniger sichere Personen an.",
 "React faster": "Schneller reagieren", "MoveEye needed {n} s on average: the AI looks at every picture and walking is recognised sooner.": "MoveEye brauchte im Mittel {n} s: die KI prüft jedes Bild und das Gehen wird früher erkannt."});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"how-1": "Download MoveEye Sim · 3D for Windows, unzip it on the PC and start MoveEyeSim3D.exe (until 3D-4.23 it was called MotionWatch3D.exe).", "how-2": "In the simulator window, top right, switch on «Send to MoveEye».", "how-3": "The simulator appears here under «Simulators in the network» – tap «Use» if needed.", "how-4": "«Switch the simulation on»: MoveEye now works with the pictures and sensors of the simulator instead of the real hardware. Switching it off = back to the real hardware.", "upd-owner-note": "This is the setting «Neue Versionen» of the simulator – the same here and there.", "simset-note": "What MoveEye does by itself in the simulation. Connection, computing power and the tiles have their switches above.", "conn-note": "Address of the simulator program. Usually not needed: the simulator announces itself in the network and is found by itself.", "autostart-note": "And off again (back to the real cameras and sensors) when none is there for a minute. Switched off by hand: stays off until a new simulator appears.", "sim-missing": "A simulator is missing? Switch on «Send to MoveEye» in the simulator. On a PC the Windows firewall must allow its port (8765; a second simulator e.g. 8767).", "sim-view-help": "The window of the simulator: drag with the left mouse button = move, right = turn, wheel = zoom (after a click into the picture), double click = fly there. Finger: tap = click, otherwise the page scrolls; with ✋ the finger controls the simulator (drag = move, ⟲ = turn, two fingers = zoom). The buttons below change the view."});  // 2.97.0: no raw keys in English
Object.assign(I18N.de, {"Settings of the simulation": "Einstellungen der Simulation", "simset-note": "Was MoveEye in der Simulation selbst tut. Verbindung, Rechenleistung und die Kacheln haben ihre Schalter oben.", "Simulator centre": "Simulator-Zentrale", "Picture quality": "Bildqualität", "automatic": "automatisch", "very high": "sehr hoch", "high": "hoch", "medium": "mittel", "low": "niedrig", "best sneaker": "bester Schleicher", "unreported": "unerkannt", "Best sneaker of the week": "Bester Schleicher der Woche", "visible, but not reported by MoveEye": "sichtbar, aber von MoveEye nicht gemeldet", "Simulator": "Simulator", "Connection": "Verbindung", "Live picture": "Livebild", "off - the real cameras and sensors are used": "aus – die echten Kameras und Sensoren werden benutzt", "Button «Update the simulator» above.": "Knopf «Simulator aktualisieren» darunter.", "conn-note": "Adresse des Simulator-Programms. Meist nicht nötig: der Simulator meldet sich im Netz und wird von selbst gefunden.",
 "Save": "Speichern", "Find the simulator in the network by itself": "Simulator im Netz selbst finden", "Simulators in the network": "Simulatoren im Netz", "Search now": "Jetzt suchen",
 "Picture": "Bild", "Simulator control": "Simulator-Steuerung", "ctl-note": "Erscheint, sobald der Simulator verbunden ist: Szenarien, Tageszeit, Wetter, Besucher und mehr.",
 "Load": "Laden", "Delete": "Löschen", "Computing power": "Rechenleistung", "perf-note": "Weniger Bilder pro Sekunde entlasten den Pi und den PC.",
 "Simulator: fewer pictures": "Simulator: weniger Bilder", "upd-owner-note": "Das ist die Einstellung «Neue Versionen» im Simulator – hier und dort dieselbe.", "Pictures per second": "Bilder pro Sekunde",
 "Programs and downloads": "Programme und Downloads", "3D simulator for Windows (ZIP)": "MoveEye Sim · 3D für Windows (ZIP)", "Simple simulator (ZIP)": "MoveEye Sim · Basis (ZIP)",
 "Python, for a PC or the Pi": "Python, für PC oder Pi", "Phone / tablet view": "Handy- / Tablet-Ansicht", "this page as on a phone": "die Webseite wie auf dem Handy",
 "simple simulator directly on the Pi": "einfacher Simulator direkt auf dem Pi", "Start simulator here": "Simulator hier starten", "on the Pi (uses its CPU)": "auf dem Pi (braucht seine Rechenleistung)",
 "Stop simulator": "Simulator stoppen", "on the Pi": "auf dem Pi", "Install simulator on the Pi": "Simulator auf dem Pi installieren", "Install simulator again": "Simulator neu installieren",
 "How it works": "So funktioniert es",
 "how-1": "MoveEye Sim · 3D für Windows herunterladen, auf dem PC entpacken und MoveEyeSim3D.exe starten (bis 3D-4.23 hiess sie MotionWatch3D.exe).",
 "how-2": "Im Simulator-Fenster oben rechts den Schalter «An MoveEye senden» einschalten.",
 "how-3": "Der Simulator erscheint hier unter «Simulatoren im Netz» – bei Bedarf «Verwenden» antippen.",
 "how-4": "«Simulation einschalten»: MoveEye arbeitet jetzt mit den Bildern und Sensoren des Simulators statt mit der echten Hardware. Ausschalten = zurück zur echten Hardware.",
 "Simulation off": "Simulation aus", "Simulator not reachable": "Simulator nicht erreichbar", "connected": "verbunden", "answers, but no picture arrives yet": "antwortet, aber es kommt noch kein Bild an",
 "Switch the simulation on": "Simulation einschalten", "Switch the simulation off": "Simulation ausschalten",
 "Connected for": "Verbunden seit", "Response time": "Antwortzeit", "Camera pictures/s": "Kamera Bilder/s", "Thermal pictures/s": "Wärmebilder/s", "Messages sent": "Meldungen gesendet",
 "Sensor events": "Sensor-Ereignisse", "Errors": "Fehler", "Searching": "Suche", "found": "gefunden", "Last search": "Letzte Suche", "addresses in": "Adressen in",
 "Simulators announce themselves every 2 s. «Search now» also asks every address of the network.": "Simulatoren melden sich alle 2 s. «Jetzt suchen» fragt zusätzlich jede Adresse im Netz ab.",
 "No simulator announces itself in the network right now.": "Im Moment meldet sich kein Simulator im Netz.", "sim-missing": "Ein Simulator fehlt? Im Simulator den Schalter «An MoveEye senden» einschalten. Läuft er auf einem PC, muss die Windows-Firewall seinen Port erlauben (8765; ein zweiter Simulator z. B. 8767).", "Use": "Verwenden", "in use": "in Gebrauch",
 "Version": "Version", "installed": "installiert", "newest": "neueste", "up to date": "aktuell", "newest version not known": "neueste Version unbekannt", "checking for the newest version …": "suche die neueste Version …", "New update for the simulator": "Neues Update für den Simulator", "Update it in the simulator on the PC.": "Im Simulator auf dem PC aktualisieren.", "Button «Update the simulator» above.": "Knopf «Simulator aktualisieren» oben.", "The finger now controls the simulator (scrolling: press ✋ again)": "Der Finger bedient jetzt den Simulator (Scrollen: ✋ nochmals drücken)", "The finger scrolls the page again (a tap still clicks)": "Der Finger scrollt wieder die Seite (Antippen klickt trotzdem)", "Game wizard": "Spiel-Assistent", "Back": "Zurück", "Next": "Weiter", "Game type": "Spielart", "Goal": "Ziel", "Difficulty": "Schwierigkeit", "Start": "Los", "Which game?": "Welches Spiel?", "gw-intro": "Bis zu 12 Läufer (dazu Zuschauer) machen mit dem Handy mit. Wähle die Spielart – der Assistent erklärt die Regeln und stellt alles ein.", "Like last time": "Wie letztes Mal", "What is the goal?": "Was ist das Ziel?", "How hard?": "Wie schwierig?", "Beginners": "Anfänger", "Normal": "Normal", "Pros": "Profis", "gw-easy": "Wächter leicht, unbegrenzte Leben, 8 Minuten, Sichtfeld der Kameras sichtbar.", "gw-normal": "Wächter normal, 3 Leben, 5 Minuten.", "gw-hard": "Wächter schwer, nur 1 Leben, 4 Minuten, kein Sichtfeld.", "Sneak to the goal": "Zum Ziel schleichen", "Fetch the loot and bring it back": "Beute holen und zurückbringen", "Capture the flag (two teams)": "Fahne erobern (zwei Teams)", "gw-reach": "Ziel: zum grünen Licht schleichen, ohne erwischt zu werden. Der Pfeil auf dem Handy zeigt den Weg.", "gw-return": "Ziel: die Beute beim grünen Licht holen und zurück zum Start bringen.", "gw-flag": "Ziel: zwei Teams. Holt die Fahne der anderen und bringt sie zur eigenen Basis. Wer mit der Fahne erwischt wird, verliert sie.", "Duration of a round": "Dauer einer Runde", "Lives": "Leben", "unlimited": "unbegrenzt", "3 lives": "3 Leben", "1 life": "1 Leben", "Crystals to collect": "Kristalle zum Sammeln", "Two teams (red against blue)": "Zwei Teams (Rot gegen Blau)", "Free the caught ones (they wait in the cell)": "Befreien (Erwischte warten in der Zelle)", "Throw stones to distract": "Steine werfen zum Ablenken", "Show the field of view of the cameras": "Sichtfeld der Kameras zeigen", "Ready!": "Bereit!", "Teams": "Teams", "red against blue": "Rot gegen Blau", "no": "nein", "gw-tips": "Tipps: Ducken und Kriechen hilft. Im Dunkeln und hinter Dingen sieht euch die Kamera schlechter. Rennen hört das Mikrofon. Ein geworfener Stein lenkt die Kamera ab.", "gw-rescue": "Befreien: Wer erwischt wird, wartet in der Zelle, bis ihn ein Teamkollege befreit.", "gw-items": "Kristalle: Wer welche einsammelt, bekommt Extrapunkte.", "Power-ups: invisibility potion (purple) and turbo (yellow)": "Power-ups: Unsichtbar-Trank (lila) und Turbo (gelb)", "gw-powers": "Power-ups: Die lila Kugel ist ein Unsichtbar-Trank (9 s fast unsichtbar), die gelbe ein Turbo (7 s schneller, aber lauter). Sie tauchen später an einem anderen Ort wieder auf.", "gw-lastmin": "Letzte Minute: Die Kamera passt dann besser auf – jetzt wird es spannend!", "Extras": "Extras", "photos, hiding places, decoy, night, events, checkpoints, handicap": "Fotos, Verstecke, Lockvogel, Nacht, Ereignisse, Checkpoints, Handicap", "Caught photos (gallery at the end)": "Erwischt-Fotos (Galerie am Schluss)", "Hiding places (bushes, 8 s invisible)": "Verstecke (Büsche, 8 s unsichtbar)", "Decoy allowed": "Lockvogel erlaubt", "Night round with torches": "Nacht-Runde mit Taschenlampen", "Random events (storm, dog, car)": "Zufallsereignisse (Gewitter, Hund, Auto)", "Checkpoints (+150 points each)": "Checkpoints (je +150 Punkte)", "Handicap for the leader of the ranking": "Handicap für den Ersten der Rangliste", "gw-photos": "📸 Erwischt-Fotos: Wer erwischt wird, sieht auf dem Handy das Bild der Kamera. Am Schluss gibt es eine Galerie.", "gw-hides": "🌳 Verstecke: In einem Busch geduckt oder kriechend sieht dich die Kamera nicht – aber nur 8 Sekunden lang.", "gw-decoy": "🦆 Lockvogel: Wer will, wählt auf dem Handy «Lockvogel». Er lässt sich absichtlich sehen, lockt die Kamera weg und bekommt Punkte für jede beobachtete Sekunde.", "gw-night": "🌙 Nacht-Runde: Es ist dunkel. Mit 🔦 siehst du mehr – aber die Kamera sieht dich auch.", "gw-events": "⛈ Zufallsereignisse: Gewitter (man hört dich kaum), ein bellender Hund, ein Auto mit Scheinwerfern.", "gw-cps": "🚩 Checkpoints: Leuchtende Ringe unterwegs geben je 150 Punkte.", "gw-hc": "🎯 Handicap: Wer in der Rangliste vorne liegt, wird leichter gesehen und ist etwas langsamer.", "Handicap (experienced players are seen more easily, are a bit slower, shorter invisibility potion)": "Handicap (Geübte werden leichter gesehen, sind etwas langsamer, kürzerer Unsichtbar-Trank)", "none": "keins", "a little": "etwas", "strong": "stark", "Ranking of the evening": "Rangliste des Abends", "rounds": "Runden", "won": "gewonnen", "best time": "Bestzeit", "never caught": "nie erwischt", "fastest": "am schnellsten", "most crystals": "meiste Kristalle", "best guard": "bester Wächter", "Records": "Rekorde", "Reset the ranking": "Rangliste zurücksetzen", "Reset the ranking of the evening?": "Rangliste des Abends zurücksetzen?", "Storm": "Gewitter", "Dog": "Hund", "Car": "Auto", "Caught!": "Erwischt!", "Result": "Ergebnis", "Close": "Schliessen", "Spectator camera: flies over the field by itself": "Zuschauer-Kamera: fliegt selbst übers Spielfeld", "Settings": "Einstellungen", "Opening the game …": "Spiel wird geöffnet …", "the simulator did not open the game": "der Simulator hat das Spiel nicht geöffnet", "Start the round": "Runde starten", "Open the game & show the QR code": "Spiel öffnen & QR-Code zeigen", "The round starts": "Die Runde startet", "Game «Unseen to the goal»": "Spiel «Unentdeckt ans Ziel»", "Show the QR code big": "QR-Code gross zeigen", "Close the game": "Spiel schliessen", "Tap to close": "Antippen zum Schliessen", "Open the game": "Spiel öffnen", "Players scan the QR code with their phone (same WLAN) or open the address:": "Mitspieler scannen den QR-Code mit dem Handy (gleiches WLAN) oder öffnen die Adresse:", "players": "Spieler", "Up to 12 players sneak unseen to the goal with their phones. Open the game, then they scan the QR code.": "Bis zu 12 Spieler schleichen mit dem Handy unentdeckt zum Ziel. Spiel öffnen, dann scannen sie den QR-Code.", "CPU of the PC": "CPU des PCs", "Update the simulator by itself when a newer version is there": "Simulator selbst aktualisieren, wenn eine neuere Version da ist", "Simulator window": "Simulator-Fenster", "Camera picture": "Kamerabild", "Update the simulator": "Simulator aktualisieren", "New version available": "Neue Version verfügbar", "The simulator looks for a new version and installs it": "Der Simulator sucht eine neue Version und installiert sie", "The simulator looks for a new version and installs it (about a minute, it starts again by itself).": "Der Simulator sucht eine neue Version und installiert sie (etwa eine Minute, er startet danach von selbst wieder).", "this device": "dieses Gerät", "found by the search": "durch die Suche gefunden", "last": "zuletzt vor", "messages": "Meldungen",
 "The picture appears when the simulation is on.": "Das Bild erscheint, wenn die Simulation eingeschaltet ist.",
 "Delete this scenario in the simulator?": "Dieses Szenario im Simulator löschen?", "running": "läuft", "Controls": "Bedienung",
 "uploaded": "hochgeladen", "upload interrupted": "Hochladen abgebrochen", "Upload a file to the simulator": "Datei zum Simulator hochladen",
 "Link for the PC browser": "Link für den Browser am PC", "Saved": "Gespeichert", "not possible": "nicht möglich", "Simulator installed": "Simulator installiert",
 "Python world simulator (ZIP)": "MoveEye Sim · Welt (Kevin) (ZIP)", "second simulator, needs Python on the PC": "zweiter Simulator, braucht Python auf dem PC", "prepared on the first download": "wird beim ersten Download vorbereitet", "Simulator started": "Simulator gestartet", "Simulator stopped": "Simulator gestoppt", "simulator not reachable": "Simulator nicht erreichbar", "Search a place (e.g. Zermatt)": "Ort suchen (z. B. Zermatt)", "Aerial picture": "Luftbild", "Map": "Karte", "Load this place": "Diesen Ort laden", "Tap on the map where MoveEye stands. Drag = move, two fingers or wheel = zoom.": "Auf der Karte antippen, wo MoveEye steht. Ziehen = verschieben, zwei Finger oder Mausrad = zoomen.", "Search not possible – tap the place on the map": "Suche nicht möglich – den Ort direkt auf der Karte antippen", "Search a setting …": "Einstellung suchen …", "Simple": "Einfach", "Expert": "Experte", "Simple: only the important settings. «Expert» shows all.": "Einfach: nur die wichtigen Einstellungen. «Experte» zeigt alle.", "Nothing found": "Nichts gefunden", "Only in Switzerland": "Nur in der Schweiz", "The simulator loads the place (about a minute the first time).": "Der Simulator lädt den Ort (beim ersten Mal etwa eine Minute)."});
let S = null, CS = "", URLEDIT = false;
const dur = n => n == null ? "–" : n < 60 ? n + " s" : n < 3600 ? Math.floor(n / 60) + " min" : Math.floor(n / 3600) + " h " + Math.floor(n % 3600 / 60) + " min";
async function load() {
  const r = await fetch("/api/sim").then(x => x.ok ? x.json() : null).catch(() => null);
  if (r) { if ("connected" in r) r.ok = !!r.connected; S = r; paint(); }   // 2.95.93: «ok» of the answer is the request, «connected» the simulator
  clearTimeout(load.t); load.t = setTimeout(load, S && S.scan && S.scan.running ? 1000 : 3000);
}
function foldAct() {                       // 2.95.69: symbol + arrow green while the function of the card works
  const on = !!(S && S.on), ok = !!(on && S.ok), T = (S && S.stats) || {}, full = ok && S.pic !== false;   // 2.95.93: green only with pictures
  const act = {conn: full, status: full, prev: ok && T.cam_fps != null && T.cam_fps > 0, ctl: ok, perf: !!(S && S.eco),
               test: !!(TR && (TR.busy || (TR.sim && TR.sim.running))), tools: ok, game: !!(GWR && GWR.game && GWR.game.open)};
  document.querySelectorAll("details.fold[data-k]").forEach(d => { const k = d.dataset.k;
    d.classList.toggle("act", !!act[k]); d.classList.toggle("bad", (k === "conn" || k === "status") && on && !full); });
  const tu = $("#c-tunnel"); if (tu) tu.classList.toggle("act", !!(S && S.tunnel && S.tunnel.active));
  // order by logic: the status only with the simulation on, the rest only when the simulator answers
  document.querySelectorAll("[data-need]").forEach(d => d.classList.toggle("needhide", d.dataset.need === "on" ? !on : !ok));
  if (ok && !foldAct.was) { const c = $("#c-conn"); if (c) c.open = false; }   // connected: the connection folds away
  if (!ok && foldAct.was !== false) { const c = $("#c-conn"); if (c) c.open = true; }
  foldAct.was = ok;
}
function paint() {
  foldAct();
  const T = S.stats || {};
  const nopic = S.on && S.ok && S.pic === false, NP = t("answers, but no picture arrives yet");   // 2.95.93
  $("#s-ttl").textContent = "Status · " + (!S.on ? t("Simulation off") : nopic ? NP : S.ok ? (T.name || t("connected")) : t("Simulator not reachable"));
  const so = $("#s-on"); if (so && document.activeElement !== so) so.checked = !!S.on;
  $("#s-onnote").textContent = !S.on ? t("off - the real cameras and sensors are used") : nopic ? NP : S.ok ? t("connected") + (T.name ? ": " + T.name : "") : t("Simulator not reachable");
  $("#s-csub").textContent = nopic ? "· " + NP : S.on && S.ok ? "· " + t("connected") : "";
  $("#s-msg").textContent = (S.msg ? t(S.msg) + (S.leader ? " (" + S.leader + ")" : "") + " · " : "") + (S.url || "");   // Aufräumen 2: who steers
  const tile = (k, v) => '<div class="tile"><div class="mut">' + k + '</div><b>' + v + '</b></div>';
  $("#s-tiles").hidden = !S.on;
  const pcc = T.pc_cpu == null ? "–" : Math.round(T.pc_cpu) + " %" + (T.sim_cpu != null ? " · Sim " + Math.round(T.sim_cpu) + " %" : "");   // Aufräumen 2: «sim_cpu_own»
  $("#s-tiles").innerHTML = tile(t("CPU of the PC"), '<span style="color:' + (T.pc_cpu > 85 ? "var(--red,#ff5b4b)" : T.pc_cpu > 60 ? "#e8b33a" : "inherit") + '">' + pcc + '</span>') + tile(t("Connected for"), dur(T.since)) + tile(t("Response time"), T.rtt == null ? "–" : T.rtt + " ms") + tile(t("Camera pictures/s"), T.cam_fps == null ? "–" : T.cam_fps)
    + tile(t("Thermal pictures/s"), T.th_fps == null ? "–" : T.th_fps) + tile(t("Messages sent"), T.sent || 0) + tile(t("Sensor events"), T.events || 0) + tile(t("Errors"), T.errs || 0);
  const u = $("#s-url"); if (!URLEDIT && document.activeElement !== u) u.value = S.url || "";
  $("#k-sim_auto").checked = !!S.auto; $("#k-sim_autostart").checked = S.autostart !== false; $("#k-sim_eco").checked = !!S.eco; $("#k-sim_autoupd").checked = S.autoupd !== false;
  const fr = $("#k-sim_fps"); if (document.activeElement !== fr && S.fps != null) { fr.value = S.fps; $("#v-sim_fps").textContent = S.fps; }
  paint3d();
  const SC = S.scan || {}, ago = SC.t ? Math.round(Date.now() / 1000 - SC.t) : null;
  $("#s-scan").textContent = SC.running ? t("Searching") + " " + SC.net + " … " + Math.round(100 * (SC.done || 0) / Math.max(1, SC.hosts || 1)) + " % · " + (SC.found || 0) + " " + t("found")
    : SC.t ? t("Last search") + ": " + (ago < 60 ? ago + " s" : Math.round(ago / 60) + " min") + " · " + SC.hosts + " " + t("addresses in") + " " + SC.secs + " s · " + SC.found + " " + t("found")
    : t("Simulators announce themselves every 2 s. «Search now» also asks every address of the network.");
  $("#s-search").disabled = !!SC.running;
  const fb = $("#s-found"), F = S.found || [], sig = JSON.stringify(F.map(x => [x.ip, x.port, x.name, x.host, x.count, x.age > 5, x.pc_cpu, x.sim_cpu])) + S.url;
  if (fb.dataset.sig !== sig) { fb.dataset.sig = sig; fb.textContent = "";
    if (!F.length) fb.appendChild(el("div", "mut", t("No simulator announces itself in the network right now.")));
    fb.appendChild(el("div", "mut", t("sim-missing"))).style.marginTop = "6px";
    F.forEach(x => { const cur = S.url === "http://" + x.ip + ":" + x.port; const r = el("div", "fnd" + (cur ? " cur" : ""));
      const n = el("div", "n"); n.append(el("b", "", x.name || "Simulator"));
      if (x.host) { const h = el("span", "host", "💻 " + x.host + (x.ip === "127.0.0.1" ? " (" + t("this device") + ")" : "")); n.firstChild.after(h); }
      if (x.pc_cpu != null) { const c = el("span", "host", "⚙ PC " + Math.round(x.pc_cpu) + " %" + (x.sim_cpu != null ? " · Sim " + Math.round(x.sim_cpu) + " %" : ""));
        c.style.color = x.pc_cpu > 85 ? "#f85149" : x.pc_cpu > 60 ? "#d29922" : ""; n.firstChild.after(c); }
      n.append(el("div", "mut", x.ip + ":" + x.port + (x.version ? " · " + x.version : "")
        + (x.via === "scan" ? " · " + t("found by the search") : " · " + t("last") + " " + Math.round(x.age || 0) + " s")));
      r.appendChild(n);
      if (cur) r.appendChild(el("span", "mut", "✓ " + t("in use")));
      else { const b = el("button", "sec", t("Use")); b.type = "button"; b.onclick = async () => { const q = await post("/api/sim", {action: "use", ip: x.ip, port: x.port, lang: LANG}); if (q.ok === false) toast(q.error || t("not possible")); load(); }; r.appendChild(b); }
      fb.appendChild(r); }); }
  // preview
  $("#s-prevnote").textContent = S.on ? "" : t("The picture appears when the simulation is on.");
  liveOn(!!S.on); pvPaint(); verPaint();
  // control
  if (S.ok && !CS) ctl({ctl: "get"});
  if (!S.ok) { CS = ""; $("#s-groups").textContent = ""; $("#s-scn").hidden = true; $("#s-up").hidden = true; $("#s-cname").textContent = ""; $("#s-cst").textContent = t("ctl-note"); }
  // pi programs
  $("#p-instt").textContent = "📦 " + t(S.installed ? "Install simulator again" : "Install simulator on the Pi");
  $("#p-start").hidden = !!S.running; $("#p-stop").hidden = !S.running;
}
// ---- button «Update the simulator» (2.95.5): the simulator's own update (control «update_now»), newest version shown ----
const vnum = v => (String(v || "").match(/(\d+)\.(\d+)/) || [0, 0, 0]).slice(1).map(Number);
function verPaint() {
  const V = S && S.on && S.versions, w = $("#s-supd");
  if (!V || !V.current) { $("#s-ver").textContent = ""; w.hidden = true; return; }
  $("#s-ver").textContent = t("Version") + ": " + V.current + " " + t("installed") + " · " + (V.latest ? t("newest") + ": " + V.latest + (V.newer ? "" : " ✓ " + t("up to date"))
    : (V.err ? t("newest version not known") + " (" + V.err + ")" : t("checking for the newest version …")));
  w.hidden = !V.newer;
  if (V.newer) { $("#s-supdt").textContent = "⚠ " + t("New update for the simulator") + ": " + V.latest + " (" + t("installed") + ": " + V.current + ")";
    $("#s-supdn").textContent = (V.notes ? V.notes + " · " : "") + ($("#s-upd").hidden ? t("Update it in the simulator on the PC.") : t("Button «Update the simulator» above.")); }
}
function updPaint(r) {
  const b = $("#s-upd"), has = !!(r && r.ok && (r.controls || []).some(c => c.id === "update_now"));
  b.hidden = !(has && S && S.on); verPaint(); if (b.hidden) return;
  const V = S.versions || {}, m = String(r.name || "").match(/3D-\d+\.\d+/), cur = V.current || (m ? m[0] : ""), nw = V.latest || (S.sim3d && S.sim3d.version);
  const [a1, a2] = vnum(cur), [b1, b2] = vnum(nw), newer = cur && nw && (b1 > a1 || (b1 === a1 && b2 > a2));
  b.className = newer ? "" : "sec";
  b.title = newer ? t("New version available") + ": " + nw : t("The simulator looks for a new version and installs it");
  b.lastChild.textContent = newer ? t("Update the simulator") + " → " + nw : t("Update the simulator");
}
// ---- the game of the 3D simulator (3D-3.20): QR code and address here, for the phones of the players ----
let GQR = "";
function gamePaint(r) {
  if (r && r.ok) GWR = r;
  const G = r && r.ok ? r.game : null, c = $("#c-game");
  c.hidden = !G || !(S && S.on); if (c.hidden) return;
  $("#g-open").hidden = !!G.open; $("#g-close").hidden = !G.open; $("#g-big").hidden = !G.open; $("#g-qrbox").hidden = !G.open;
  $("#g-open").textContent = "▶ " + t("Open the game");
  $("#g-txt").textContent = G.open ? t("Players scan the QR code with their phone (same WLAN) or open the address:") + " · " + t("players") + ": " + (G.players || 0)
    : t("Up to 12 players sneak unseen to the goal with their phones. Open the game, then they scan the QR code.");
  $("#g-url").textContent = G.open ? G.url : "";
  if (G.open && GQR !== G.url) { GQR = G.url; const u = "/sim/game_qr.png?r=" + Date.now(); $("#g-qr").src = u; $("#g-qrbig").src = u; $("#g-urlbig").textContent = G.url; }
  if (!G.open) { GQR = ""; gameBig(false); }
}
Object.assign(I18N.de, {"the game wizard runs in the 3D simulator from 3D-3.41 - please update the simulator": "der Spiel-Assistent läuft ab 3D-3.41 im 3D-Simulator – bitte den Simulator aktualisieren",
  "Quick start": "Schnellstart", "runners at most": "Läufer höchstens", "Duel": "Duell", "MoveEye against the guard": "MoveEye gegen den Wächter",
  "Guesses «Who gets through?»": "Tipps «Wer kommt durch?»", "Level": "Stufe", "Best teachers": "Beste Lehrer"});
// ---- game wizard: from 2.95.48 it lives in the 3D simulator (3D-3.41) - this page shows its steps and works them from afar ----
let GW = null, GWS = 0, GWR = null, GWM = null, gwT = null;
async function gwOp(o) {
  let r = null;
  try { r = await post("/api/sim", Object.assign({action: "gamewiz", lang: LANG}, o)); } catch (e) { r = null; }
  if (!r || r.ok === false) {
    const B = $("#gw-body"); B.innerHTML = "";
    B.append(el("h3", "", t("Game wizard")), el("div", "gw-err", "⚠ " + ((r && r.error) || t("simulator not reachable")) + " – " + t("the game wizard runs in the 3D simulator from 3D-3.41 - please update the simulator")));
    $("#gw-next").hidden = true; $("#gw-back").style.visibility = "hidden"; return null; }
  $("#gw-next").hidden = false; GWM = r; gwPaint(r); return r;
}
async function gwOpen() { $("#gw").hidden = false; GWS = 0; await gwOp({op: "open"}); gwPoll(); }
function gwClose() { $("#gw").hidden = true; clearTimeout(gwT); post("/api/sim", {action: "gamewiz", op: "close", lang: LANG}).catch(() => {}); }
function gwPoll() {                                   // the simulator may change it too (its window) - and the players come
  clearTimeout(gwT);
  gwT = setTimeout(async () => {
    if ($("#gw").hidden) return;
    let r = null; try { r = await post("/api/sim", {action: "gamewiz", op: "get", lang: LANG}); } catch (e) {}
    if (r && r.ok !== false) {
      if (!r.shown) { $("#gw").hidden = true; return; }
      const sig = r.seq + "|" + JSON.stringify(r.game);
      if (!GWM || sig !== GWM.seq + "|" + JSON.stringify(GWM.game)) { GWM = r; gwPaint(r); }
    }
    gwPoll();
  }, 1500);
}
function gwPaint(M) {
  GWS = M.step;
  $("#gw-steps").innerHTML = ""; (M.steps || []).forEach((x, i) => $("#gw-steps").appendChild(el("span", i === M.step ? "on" : i < M.step ? "done" : "", (i + 1) + " " + x)));
  const B = $("#gw-body"); B.innerHTML = "";
  if (M.error) B.appendChild(el("div", "gw-err", M.error));
  B.appendChild(el("h3", "", M.title)); if (M.lead) B.appendChild(el("p", "mut lead", M.lead));
  if ((M.quick || []).length) {                      // 3D-4.x: three quick starts - one tap sets everything and opens the game
    B.appendChild(el("div", "gw-sub", "⚡ " + (M.quick_title || t("Quick start"))));
    const qg = el("div", "gw-quick");
    M.quick.forEach(q => { const b = el("button", "gw-q"); b.type = "button";
      if (q.pic) { const im = el("img", "gw-pic"); im.alt = ""; im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(q.pic); b.appendChild(im); }   // 3D-4.20: pictures again, like in the simulator
      b.append(el("span", "ic", q.pic ? "" : q.icon), el("b", "", (q.pic ? q.icon + " " : "") + q.title), el("small", "", q.text));
      b.onclick = async () => { b.disabled = true; const r = await gwOp({op: "quick", value: q.v}); b.disabled = false;
        if (r && r.game && r.game.open) { const qq = $("#gw-qr"); if (qq && qq.firstChild) qq.scrollIntoView({behavior: "smooth", block: "center"}); } };
      qg.appendChild(b); });
    B.appendChild(qg);
    if (M.own_btn) { const ob = el("button", "sec", M.own_btn); ob.type = "button"; ob.style.cssText = "width:100%;text-align:left;white-space:normal;margin:2px 0 8px";   // 2.98.37: «Eigene Regeln» (3D-4.x: three fixed games first)
      ob.onclick = () => gwOp({op: "own", value: !M.own_open}); B.appendChild(ob); }
    if (M.own_title) B.appendChild(el("div", "gw-sub mut", M.own_title)); }
  if ((M.cards || []).length) { const g = el("div", "gw-cards");
    M.cards.forEach(c => { const b = el("button", "gw-card" + (c.on ? " on" : "")); b.type = "button";
      if (c.pic) { const im = el("img", "gw-pic"); im.alt = ""; im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(c.pic); b.appendChild(im); }   // 3D-3.42: a picture
      b.append(el("span", "ic", c.pic ? "" : c.icon), el("b", "", (c.pic ? c.icon + " " : "") + c.title), el("small", "", c.text));
      b.onclick = () => gwOp({op: "pick", key: M.key, value: c.v}); g.appendChild(b); }); B.appendChild(g); }
  if (M.last) { const q = el("button", "sec", "⚡ " + t("Like last time") + ": " + M.last); q.type = "button"; q.style.cssText = "margin-top:14px;width:100%;white-space:normal";
    q.onclick = () => gwOp({op: "last"}); B.appendChild(q); }
  let ex = null;
  (M.options || []).forEach(o => {
    let into = B;
    if (o.extra) { if (!ex) { ex = document.createElement("details"); ex.className = "gw-ex"; ex.open = !!M.extras_open;
        ex.ontoggle = () => { if (ex.open !== !!M.extras_open) { M.extras_open = ex.open; post("/api/sim", {action: "gamewiz", op: "extras", value: ex.open, lang: LANG}); } };
        const sm = document.createElement("summary"); sm.textContent = "✨ " + (M.extras_label || ("Extras – " + t("photos, hiding places, decoy, night, events, checkpoints, handicap"))); ex.appendChild(sm); B.appendChild(ex); }
      into = ex; }
    const r = el("div", "gw-row"); r.appendChild(el("label", "", o.label));
    const send = v => post("/api/sim", {action: "gamewiz", op: "set", key: o.id, value: v, lang: LANG}).then(x => { if (x && x.ok !== false) GWM = x; });
    if (o.type === "range") { const w = el("span", ""); w.style.cssText = "display:flex;gap:10px;align-items:center;flex:1"; const i = document.createElement("input");
      i.type = "range"; i.min = o.min; i.max = o.max; i.value = o.value; const v = el("b", "", Math.round(o.value) + (o.unit || ""));
      i.oninput = () => { v.textContent = i.value + (o.unit || ""); }; i.onchange = () => send(+i.value); w.append(i, v); r.appendChild(w); }
    else if (o.type === "toggle") { const i = document.createElement("input"); i.type = "checkbox"; i.className = "sc-sw"; i.checked = !!o.value; i.onchange = () => send(i.checked); r.appendChild(i); }
    else { const i = document.createElement("select"); (o.options || []).forEach(([v, l]) => { const op = el("option", "", l); op.value = v; i.appendChild(op); });
      i.value = String(o.value); i.onchange = () => send(i.value); r.appendChild(i); }
    into.appendChild(r);
  });
  if ((M.pics || []).some(x => x)) { const pr = el("div", "gw-pics2"); M.pics.forEach(x => { if (x) { const im = el("img"); im.alt = ""; im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(x); pr.appendChild(im); } }); B.appendChild(pr); }
  if ((M.summary || []).length) { const sm = el("div", "gw-sum"); M.summary.forEach(([k, v]) => sm.append(el("div", "", k), el("div", "", v))); B.appendChild(sm); }
  if ((M.rules || []).length) { const rl = el("div", "gw-rules"); M.rules.forEach(x => rl.appendChild(el("p", "", x))); B.appendChild(rl); }
  if (M.step === 3) { const q = el("div", "gw-qr"); q.id = "gw-qr"; B.appendChild(q);
    const G = M.game || {};
    if (G.open) { const im = el("img"); im.src = "/sim/game_qr.png?r=" + Date.now(); im.onclick = () => gameBig(true);
      const tx = el("div", ""); tx.append(el("div", "mut", t("Players scan the QR code with their phone (same WLAN) or open the address:")), el("div", "gm-url", G.url),
        el("div", "mut", t("players") + ": " + (G.players || 0) + (G.max ? " · " + t("runners at most") + " " + G.max : ""))); q.append(im, tx); } }
  if ((M.actions || []).length) { const ab = el("div", "btns"); ab.style.marginTop = "10px";   // 2.98.24 (3D-4.7): TV mode, spectator camera, ranking, reports
    M.actions.forEach(a => { const b = el("button", "sec", a.label); b.type = "button"; b.onclick = () => { if (a.id === "game_board_reset" && !confirm(t("Reset the ranking of the evening?"))) return; gwOp({op: "act", value: a.id}); }; ab.appendChild(b); }); B.appendChild(ab); }
  $("#gw-back").style.visibility = M.back ? "visible" : "hidden";
  $("#gw-next").textContent = M.next;
}
async function gwGo(d) {
  if (d < 0) { await gwOp({op: "back"}); return; }
  const b = $("#gw-next"); const wasOpen = GWM && GWM.step === 3 && GWM.game && GWM.game.open; b.disabled = true;
  if (GWM && GWM.step === 3 && !wasOpen) b.textContent = "⏳ " + t("Opening the game …");
  try {
    const r = await gwOp({op: "next"});
    if (r && wasOpen) { toast("▶ " + t("The round starts")); $("#gw").hidden = true; clearTimeout(gwT);
      if (S && S.view) { PVM = "view"; try { localStorage.setItem("mw-sim-pvmode", "view"); } catch (e) {} pvPaint(); }   // the spectators watch the simulator window
      SPECON = true; specPoll(); $("#c-prev").scrollIntoView({behavior: "smooth", block: "start"}); }
    else if (r && r.step === 3 && r.game && r.game.open) { const q = $("#gw-qr"); if (q && q.firstChild) q.scrollIntoView({behavior: "smooth", block: "center"}); }
  } finally { b.disabled = false; }
}
// ---- spectators (2.95.14): time, players with their meter, what happened, the result - over the picture ----
let SPEC = null, SPECON = true, SPECRES = "", specT = null;
try { SPECON = localStorage.getItem("mw-sim-spec") !== "0"; } catch (e) {}
const MODE_TXT = {camera: "Alle gegen die Kamera", guard: "Wächter", teamguard: "Team gegen Team", mw: "Gegen MoveEye", mwhand: "Team gegen MoveEye",
  patrol: "Patrouille", seek: "Verstecken mit dem Rover", free: "Zonen-Check", jaeger: "Fehlalarm-Jäger", escape: "Entkomme der Kamera"};     // 2.98.0: all game types (2.98.18: Fehlalarm-Jäger)
const ST_IC = {play: "🏃", goal: "🎉", jail: "🔒", out: "👀", lobby: "⏳"};
async function specPoll() {
  clearTimeout(specT);
  const G = GWR && GWR.game;
  if (!(S && S.on && G && G.open) || document.hidden) { SPEC = null; specPaint(); specT = setTimeout(specPoll, 3000); return; }
  try { const r = await post("/api/sim", {action: "game", lang: LANG}); SPEC = r && r.ok ? r : null; } catch (e) { SPEC = null; }
  specPaint();
  specT = setTimeout(specPoll, SPEC && ["countdown", "play"].includes(SPEC.round) ? 1000 : 2500);
}
const mmss = n => Math.floor(n / 60) + ":" + ("0" + (n % 60)).slice(-2);
function gMorePaint() {                            // game card: players with handicap, the ranking of the evening (3D-3.25)
  const box = $("#g-more"), G = SPEC; if (!box) return;
  if (!G || !G.open) { box.innerHTML = ""; box.dataset.sig = ""; return; }
  const sig = JSON.stringify([(G.players || []).map(p => [p.n, p.hc, p.slot, p.dc]), G.board, G.records, G.week, G.sneak, G.task]);
  if (box.dataset.sig === sig) return; box.dataset.sig = sig; box.innerHTML = "";
  if (G.task) { const tk = el("div", "", "🎯 " + t("Task of this round") + ": " + G.task + " (+" + G.task_bonus + ")"); tk.style.cssText = "margin-top:8px;font-weight:600"; box.appendChild(tk); }
  if ((G.players || []).length && (G.players[0].hc !== undefined)) {
    const h = el("div", "mut", "🎯 " + t("Handicap (experienced players are seen more easily, are a bit slower, shorter invisibility potion)") + ":"); h.style.marginTop = "8px"; box.appendChild(h);
    const row = el("div", "chips2");
    G.players.forEach(p => { const w = el("label", "hcp"); const d = el("span", "", "● "); d.style.color = p.c; const sel = document.createElement("select");
      [["0", t("none")], ["1", t("a little")], ["2", t("strong")]].forEach(([v, l]) => { const o = el("option", "", l); o.value = v; sel.appendChild(o); });
      sel.value = String(p.hc || 0); sel.onchange = () => post("/api/sim", {action: "game_hc", slot: p.slot, level: +sel.value, lang: LANG});
      w.append(d, el("span", "", p.n + (p.dc ? " 🦆" : "") + " "), sel); row.appendChild(w); });
    box.appendChild(row); }
  if ((G.board || []).length) {
    const h = el("div", "", "🏆 " + t("Ranking of the evening")); h.style.cssText = "margin-top:10px;font-weight:600"; box.appendChild(h);
    const tb = el("table", "gw-board");
    G.board.forEach((b, i) => { const tr = el("tr"); const n = el("td", "", (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + " " + b.n); n.style.color = b.c;
      tr.append(n, el("td", "", String(b.score)), el("td", "mut", b.rounds + " " + t("rounds") + (b.wins ? " · " + b.wins + "× " + t("won") : "") + (b.best ? " · " + t("best time") + " " + mmss(b.best) : "") + (b.clean ? " · " + b.clean + "× " + t("never caught") : ""))); tb.appendChild(tr); });
    box.appendChild(tb);
    const R = G.records || {}, rec = [];
    if (R.fast) rec.push("⚡ " + t("fastest") + ": " + R.fast[0] + " " + mmss(R.fast[1])); if (R.items) rec.push("💎 " + t("most crystals") + ": " + R.items[0] + " " + R.items[1]);
    if (R.catches) rec.push("👮 " + t("best guard") + ": " + R.catches[0] + " " + R.catches[1] + "×");
    if (R.blind) rec.push("🙈 " + t("best sneaker") + ": " + R.blind[0] + " " + R.blind[1] + " s " + t("unreported"));
    if (rec.length) box.appendChild(el("div", "mut", t("Records") + ": " + rec.join(" · ")));
    const rb = el("button", "sec", t("Reset the ranking")); rb.type = "button"; rb.style.marginTop = "6px";
    rb.onclick = async () => { if (confirm(t("Reset the ranking of the evening?"))) { await ctl({ctl: "press", id: "game_board_reset"}); specPoll(); } }; box.appendChild(rb); }
  if ((G.week || []).length) {                     // the ranking of the week (3D-3.27)
    const h = el("div", "", "📅 " + t("Ranking of the week") + (G.week_id ? " (" + G.week_id.replace("-W", " · " + t("week") + " ") + ")" : "")); h.style.cssText = "margin-top:10px;font-weight:600"; box.appendChild(h);
    const tb = el("table", "gw-board");
    G.week.forEach((b, i) => { const tr = el("tr"); const n = el("td", "", (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + " " + b.n); n.style.color = b.c;
      tr.append(n, el("td", "", String(b.score)), el("td", "mut", b.rounds + " " + t("rounds") + (b.wins ? " · " + b.wins + "× " + t("won") : "") + (b.tasks ? " · " + b.tasks + "× " + t("task done") : "") + (b.blind ? " · 🙈 " + b.blind + " s" : ""))); tb.appendChild(tr); });
    box.appendChild(tb); }
  if ((G.sneak || []).length) {                    // 3D-3.53: who found the most blind spots of MoveEye this week
    const h = el("div", "", "🙈 " + t("Best sneaker of the week") + " – " + t("visible, but not reported by MoveEye")); h.style.cssText = "margin-top:10px;font-weight:600"; box.appendChild(h);
    const tb = el("table", "gw-board");
    G.sneak.forEach((b, i) => { const tr = el("tr"); const n = el("td", "", (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + " " + b.n); n.style.color = b.c;
      tr.append(n, el("td", "", b.blind + " s")); tb.appendChild(tr); });
    box.appendChild(tb); }
}
function specPaint() {
  gMorePaint();
  const G = SPEC, run = !!(G && ["countdown", "play", "end"].includes(G.round));
  $("#s-vstat").hidden = !run; $("#s-vstat").classList.toggle("on", SPECON);
  const box = $("#s-spec"); box.hidden = !(run && SPECON && LIVE && !$("#s-prev").closest("#pip"));
  if (!run) { $("#s-specres").hidden = true; SPECRES = ""; return; }
  const h = $("#s-spech"); h.innerHTML = "";
  const tm = el("span", "tm" + (G.round === "play" && G.left <= 60 ? " hot" : ""), G.round === "countdown" ? "⏳ " + (G.cd || 0) : G.round === "play" ? "⏱ " + mmss(G.left || 0) : "🏁");
  h.append(tm, el("span", "", (MODE_TXT[G.mode] || G.mode) + " · " + (G.goal_mode === "flag" ? "🚩 " + (G.caps || [0, 0]).join(" : ") : G.mode === "jaeger" ? "🎉 " + ((G.jaeger || {}).n || 0) + ((G.jaeger || {}).mw === false ? " · ⚠ MoveEye" : "") : "🎯 " + (G.goal || ""))));
  if (G.items_all) h.appendChild(el("span", "", "💎 " + (G.items_all - G.items_left) + "/" + G.items_all));
  if (G.last_minute && G.round === "play") h.appendChild(el("span", "", "⏰"));
  if (G.night) h.appendChild(el("span", "", "🌙"));
  if (G.ev) h.appendChild(el("span", "", {storm: "⛈ " + t("Storm"), dog: "🐕 " + t("Dog"), car: "🚗 " + t("Car")}[G.ev] || ""));
  if (G.shot) h.appendChild(el("span", "sh", "🎥 " + G.shot));
  const P = $("#s-specp"); P.innerHTML = "";
  (G.players || []).forEach(p => { const c = el("span", "pl"); const d = el("span", "dot"); d.style.background = p.c;
    c.append(d, el("span", "", (ST_IC[p.s] || "") + " " + p.n + (p.r === "guard" ? " 👮" : "")));
    if (p.r !== "guard" && p.s === "play") { const mb = el("span", "mb"), i = el("i", p.susp > 70 ? "d" : p.susp > 35 ? "w" : ""); i.style.width = Math.max(4, p.susp) + "%"; mb.appendChild(i); c.appendChild(mb); }
    const extra = (p.lure ? " " + p.lure : "") + (p.fa ? " 🎉" + p.fa : "") + (p.k ? " 🚨" + p.k : "") + (p.i ? " 💎" + p.i : "") + (p.pw === "cloak" ? " 🌫" : p.pw === "turbo" ? " ⚡" : "") + (p.carry ? " 💰" : "")
      + (p.dc ? " 🦆" : "") + (p.hid ? " 🌳" : "") + (G.cps_all && p.cp ? " 🚩" + p.cp + "/" + G.cps_all : "") + (p.hc ? " 🎯" : "");
    if (extra) c.appendChild(el("span", "", extra.trim()));
    P.appendChild(c); });
  const f = (G.feed || []).filter(x => x.a < 20).slice(-2).map(x => x.x).join("  ·  ");
  $("#s-specf").textContent = f;
  const R = $("#s-specres");
  if (G.round === "end" && G.res && G.res.length) {
    const sig = JSON.stringify(G.res) + JSON.stringify((G.px || {}).lines || []);   // 3D-4.x: the theft answer of MoveEye comes later
    if (SPECRES !== sig && SPECRES !== "closed:" + sig) { SPECRES = sig; R.innerHTML = ""; const bx = el("div", "bx"); bx.appendChild(el("h3", "", "🏆 " + t("Result")));
      const RU = G.rules || {}, RW = RU.win || {};      // 2.98.37 (3D-4.x): winner, closest moment, fairness, the next guard
      if (RW.title) { const w = el("div", "", RW.title + " · " + RW.score); w.style.cssText = "font-size:24px;font-weight:800;margin:4px 0 2px;color:#ffd166"; bx.appendChild(w);
        if (RW.hl && RW.hl.text) bx.appendChild(el("div", "", RW.hl.text)); }
      ["fair", "next"].forEach(k => { if (RU[k]) bx.appendChild(el("div", "mut", RU[k])); });
      if (G.jres && G.jres.text) { const jr = el("div", "", (G.jres.n ? "🎉 " : "🛡 ") + G.jres.text); jr.style.cssText = "font-size:22px;font-weight:800;margin:4px 0 8px"; bx.appendChild(jr);   // 2.98.18: «Fehlalarm-Jäger»
        if ((G.jres.cases || []).length) bx.appendChild(el("div", "mut", G.jres.cases.map(c => c[0] + " " + c[1] + " (" + c[2] + ", " + Math.round(c[3]) + " m)").join(" · "))); }
      if (G.fres && G.fres.text) { const fr = el("div", "", "🚩 " + G.fres.text + " – " + G.fres.title); fr.style.cssText = "font-size:26px;font-weight:800;margin:4px 0 8px"; bx.appendChild(fr); }   // 3D-4.x
      if (G.duel && G.duel.text) { const du = el("div", "", "🛡 " + t("Duel") + ": 🤖 MoveEye " + G.duel.mw + " : " + G.duel.human + " " + G.duel.who); du.style.cssText = "font-size:22px;font-weight:800;margin:4px 0 2px";
        bx.append(du, el("div", "", G.duel.text)); }
      if (G.px && (G.px.lines || []).length) { const px = el("div", "", G.px.lines.join("\n")); px.style.cssText = "white-space:pre-line;font-weight:600;margin:4px 0 8px"; bx.appendChild(px); }   // 3D-4.x: weather change, theft, learning points
      if (G.px && (G.px.teachers || []).length) bx.appendChild(el("div", "mut", "🧠 " + t("Best teachers") + ": " + G.px.teachers.slice(0, 3).map((b, i) => ["🥇", "🥈", "🥉"][i] + " " + b.n + " " + b.t).join("  ")));
      if ((G.votes || []).length) bx.appendChild(el("div", "mut", "🔮 " + t("Guesses «Who gets through?»") + ": " + G.votes.map(v => v.n + " → " + v.pick + (v.ok ? " ✅" : " ❌")).join(" · ")));
      [...G.res].sort((a, b) => (b.score || 0) - (a.score || 0)).forEach((x, i) => { const r = el("div", "r"); const d = el("span", ""); d.textContent = ["🥇", "🥈", "🥉", "4."][i] || (i + 1) + ".";
        const nm = el("b", "", x.n); nm.style.color = x.c; r.append(d, nm, el("span", "mut", x.info || ""), el("span", "sc", String(x.score ?? ""))); bx.appendChild(r); });
      if ((G.pics || []).length) { const pr = el("div", "gw-pics"); G.pics.forEach((x, i) => { const f = el("figure"); const im = el("img"); im.src = "/sim/game_pic/" + i + ".jpg?r=" + Date.now();
          const cap = el("figcaption", "", x.n); cap.style.color = x.c; f.append(im, cap); pr.appendChild(f); }); bx.append(el("div", "", "📸 " + t("Caught!")), pr); }
      if ((G.board || []).length) bx.appendChild(el("div", "mut", "🏆 " + t("Ranking of the evening") + ": " + G.board.slice(0, 3).map((b, i) => ["🥇", "🥈", "🥉"][i] + " " + b.n + " " + b.score).join("  ")));
      const cb = el("button", "", t("Close")); cb.type = "button"; cb.onclick = () => { SPECRES = "closed:" + sig; R.hidden = true; }; bx.appendChild(cb); R.appendChild(bx); R.hidden = false; }
  } else if (G.round !== "end") { R.hidden = true; SPECRES = ""; }
}
$("#s-vstat").onclick = () => { SPECON = !SPECON; try { localStorage.setItem("mw-sim-spec", SPECON ? "1" : "0"); } catch (e) {} specPaint(); };
setTimeout(specPoll, 2500);
async function gameOpen(on) { await ctl({ctl: "set", id: "game_open", value: !!on}); }
function gameBig(on) { $("#g-bigov").hidden = !on; }
async function simUpdate() {
  const b = $("#s-upd"); b.disabled = true;
  const r = await post("/api/sim", {action: "ctl", ctl: "press", id: "update_now", lang: LANG});
  toast(r.ok ? "⟳ " + t("The simulator looks for a new version and installs it (about a minute, it starts again by itself).") : "⚠ " + (r.error || t("not possible")));
  setTimeout(() => { b.disabled = false; }, 20000);
}
async function simOnOff() { const b = $("#s-on"); b.disabled = true; await mwSimSet(b.checked, LANG); b.disabled = false; CS = ""; load(); }
async function saveUrl() { URLEDIT = false; const r = await post("/api/sim", {url: $("#s-url").value.trim(), lang: LANG}); toast(r.ok === false ? (r.error || t("not possible")) : t("Saved")); load(); }
$("#s-url").addEventListener("input", () => URLEDIT = true);
async function setKey(k, v) { const r = await post("/api/set", {key: k, value: v}); if (!r.ok) toast(r.error || t("not possible")); load(); }
// 2.98.14 (Konzept): the settings of the section «Simulator» live here (no longer under Einstellungen → System) - all of
// them that have no own switch on this page yet
const SIM_TILE_KEYS = ["notify_sandbox", "train_night_on", "rover_alarm", "fa_learn_auto", "rehearsal_on_arm", "weekcheck_on"];
async function simsetLoad() {
  const box = $("#simset-box"); if (!box || box.contains(document.activeElement)) return;
  let sch; try { sch = await (await fetch("/api/schema?sec=Simulator&lang=" + LANG)).json(); } catch (e) { return; }
  // 2.98.24 («Sim-Schalter nur einmal», Daniel): the switches of the tiles of the Simulator centre (Test-Postfach, Trainings-Nacht,
  // Rover, Fehlalarm-Lernen, Generalprobe, Wochen-Check) are only in their tile sheet (139), not here a second time
  const S = sch[0] || {toggles: [], sliders: [], texts: []}, own = k => !!document.getElementById("k-" + k) || k === "sim_url" || SIM_TILE_KEYS.indexOf(k) >= 0;
  box.textContent = "";
  S.toggles.filter(x => !own(x.key)).forEach(x => { const l = el("label", "opt"), cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!x.value;
    cb.onchange = () => post("/api/set", {key: x.key, value: cb.checked}).then(r => { if (!r.ok) toast(r.error || t("not possible")); }); l.append(el("span", "", x.label), cb); box.appendChild(l); });
  S.sliders.filter(x => !own(x.key)).forEach(x => { const w = el("div"), top = el("div", "rng"), v = el("b", "", String(x.value)), r = document.createElement("input");
    r.type = "range"; r.min = x.min; r.max = x.max; r.step = x.step; r.value = x.value; r.oninput = () => { v.textContent = r.value; };
    r.onchange = () => post("/api/set", {key: x.key, value: +r.value}); top.append(el("span", "", x.label), v); w.append(top, r); box.appendChild(w); });
  (S.texts || []).filter(x => !own(x.key) && x.kind !== "secret").forEach(x => { const w = el("div", "row2"), i = document.createElement("input"); i.type = "text"; i.value = x.value == null ? "" : x.value;
    const b = el("button", "sec", t("Save")); b.type = "button"; b.onclick = () => post("/api/text", {key: x.key, value: i.value, lang: LANG}).then(r => toast(r.ok ? t("Saved") : (r.error || t("not possible"))));
    box.append(el("div", "mut", x.label)); w.append(i, b); box.appendChild(w); });
  if (!box.children.length) box.appendChild(el("div", "mut", "–"));
}
document.addEventListener("DOMContentLoaded", () => { simsetLoad(); const d = $("#c-simset"); if (d) d.addEventListener("toggle", () => { if (d.open) simsetLoad(); }); });
async function search() { $("#s-search").disabled = true; await post("/api/sim", {action: "search", lang: LANG}); load(); }
async function piAct(a) { const r = await post("/api/sim", {action: a, lang: LANG}); toast(r.ok === false ? (r.error || t("not possible")) : t({install: "Simulator installed", start: "Simulator started", stop: "Simulator stopped"}[a])); load(); }
// ---- simulator control (CONTROL protocol 1): the simulator describes its own controls ----
const fmt = (c, v) => (v == null ? "–" : (Math.abs(v) >= 100 || c.step >= 1 ? Math.round(v) : (+v).toFixed(c.step < 0.1 ? 2 : 1))) + (c.unit ? " " + c.unit : "");
async function ctl(d) { const r = await post("/api/sim", Object.assign({action: "ctl", lang: LANG}, d)); showCtl(r); return r; }
function scnLoad() { const v = $("#s-sel").value; if (v) ctl({ctl: "scenario", id: v}); }
function scnDel() { const s = $("#s-sel"); if (s.value && confirm(t("Delete this scenario in the simulator?") + "\n" + s.options[s.selectedIndex].textContent)) ctl({ctl: "delete", id: s.value}); }
/*SIMMAP*/
function buildCtl(r) { simCtlBuild($("#s-groups"), r, ctl, fmt); const ts = $("#tr-sim"); if (ts) simCtlBuild(ts, r, ctl, fmt); }   // 2.98.23: «Testlauf» of the simulator in the sheet «Tests»        // like the panel of the simulator (simCtlBuild, 2.93.16)

function showCtl(r) {
  if (!r || !r.ok) { $("#s-cst").textContent = "⚠ " + ((r && r.error) || t("simulator not reachable")); return; }
  $("#s-cname").textContent = r.name ? "· " + r.name : "";
  const sig = JSON.stringify([(r.controls || []).map(c => [c.id, c.type, c.label, c.group, c.options, c.sub])]);
  if (sig !== CS) { CS = sig; buildCtl(r); }
  scOn($("#s-groups"), r); scOn($("#tr-sim"), r);
  updPaint(r); gamePaint(r);
  document.querySelectorAll("#s-groups [data-cid], #tr-sim [data-cid]").forEach(row => {
    const c = (r.controls || []).find(x => x.id === row.dataset.cid); const inp = row.querySelector(".simv"); if (!c || !inp || inp === document.activeElement) return;
    if (c.type === "toggle") inp.checked = !!c.value; else if (c.value != null) inp.value = c.value;
    const vv = row.querySelector(".simvv"); if (vv) vv.textContent = fmt(c, c.value);
  });
  const sel = $("#s-sel"), cur = sel.value; sel.textContent = "";
  (r.scenarios || []).forEach(o => { const op = document.createElement("option"); op.value = o.id; op.dataset.del = o.deletable ? "1" : "";
    op.textContent = (o.en && LANG !== "de" ? t(o.en) + " (3D)" : o.name) + (o.id === r.scenario ? "  ◀ " + t("running") : ""); sel.appendChild(op); });
  $("#s-scn").hidden = !(r.scenarios || []).length;
  sel.value = [...sel.options].some(o => o.value === cur) ? cur : (r.scenario || (sel.options[0] && sel.options[0].value) || "");
  const o = sel.options[sel.selectedIndex]; $("#s-del").hidden = !(o && o.dataset.del === "1");
  $("#s-cst").textContent = r.status || "";
  $("#s-up").hidden = !r.upload;
  if (r.upload) { $("#s-upl").textContent = "⬆ " + (r.upload.label || t("Upload a file to the simulator")) + (r.upload.max_mb ? " (max. " + r.upload.max_mb + " MB)" : ""); $("#s-file").accept = (r.upload.accept || []).join(","); }
}
$("#s-sel").onchange = () => { const o = $("#s-sel").options[$("#s-sel").selectedIndex]; $("#s-del").hidden = !(o && o.dataset.del === "1"); };
$("#s-file").onchange = () => {
  const f = $("#s-file").files[0]; if (!f) return; const prog = $("#s-prog");
  const x = new XMLHttpRequest(); x.open("POST", "/api/sim/upload?lang=" + LANG + "&name=" + encodeURIComponent(f.name));
  x.upload.onprogress = e => { if (e.lengthComputable) prog.textContent = "⬆ " + f.name + " · " + Math.round(e.loaded / e.total * 100) + " %"; };
  x.onload = () => { let r = null; try { r = JSON.parse(x.responseText); } catch (e) {}
    prog.textContent = r && r.ok ? "✓ " + t("uploaded") + ": " + (r.saved || f.name) : "⚠ " + ((r && r.error) || x.status); $("#s-file").value = ""; if (r && r.ok) showCtl(r); };
  x.onerror = () => { prog.textContent = "⚠ " + t("upload interrupted"); };
  x.send(f);
};
setInterval(() => { if (!document.hidden && S && S.ok) ctl({ctl: "get"}); }, 4000);

// ---- test run and optimization (2.95.22): the simulator plays a fixed test, MoveEye judges it and proposes settings ----
const TR_KEYS = {sensitivity: "Sensitivity", min_area: "Smallest moving area", ai_conf: "AI: minimum certainty", ai_every: "AI looks at every n-th picture",
  ai_require: "AI must confirm persons", wind_auto: "Wind filter", wind_threshold: "Wind filter: reacts from", wind_boost_max: "Wind filter: strongest",
  rain_auto: "Rain filter", rain_threshold: "Rain filter: reacts from", lowlight_auto: "Brighten in the dark", lowlight_threshold: "Brighten below",
  walk_frames: "Pictures to recognise walking", speed_consistency: "Steadiness of walking", shadow_filter: "Shadow filter", car_filter: "Vehicle filter",
  object_conf: "Objects: minimum certainty", auto_tune: "Auto-tune"};
const TR_PLANS = [["standard", "Standard (day, wind, night, rain · about 4 min)"], ["quick", "Short (day and night · about 2 min)"],
  ["hard", "Difficult conditions (low sun, fog, snow, drops, spider web, headlights, cloud shadows · about 7 min)"], ["night", "Night (dark, infrared, animals · about 3 min)"]];
let TR = null, trT = null, TRPLAN = "standard";
try { TRPLAN = localStorage.getItem("mw-tr-plan") || "standard"; } catch (e) {}
const trVal = v => v === true ? t("on") : v === false ? t("off") : (typeof v === "number" && !Number.isInteger(v) ? (+v).toFixed(2).replace(/0$/, "") : String(v));
const trLC = () => { try { return Intl.DateTimeFormat.supportedLocalesOf([LANG || "de"]).length ? (LANG || "de") : "de"; } catch (e) { return "de"; } };  // 2.97.0: an empty LANG broke the page
const trDate = ts => { const d = new Date(ts * 1000); const LANG_ = trLC(); return d.toLocaleDateString(LANG_, {day: "2-digit", month: "2-digit"}) + " " + d.toLocaleTimeString(LANG_, {hour: "2-digit", minute: "2-digit"}); };
function trInit() {
  const sel = $("#tr-plan"); sel.innerHTML = "";
  TR_PLANS.forEach(([k, n]) => { const o = el("option", "", t(n)); o.value = k; sel.appendChild(o); }); sel.value = TRPLAN;
  sel.onchange = () => { TRPLAN = sel.value; try { localStorage.setItem("mw-tr-plan", TRPLAN); } catch (e) {} };
  $("#tr-run").onclick = () => trAct({action: "run", plan: TRPLAN});
  $("#tr-auto").onclick = () => { if (confirm(t("tr-auto-ask"))) trAct({action: "auto", plan: TRPLAN, tries: 4}); };
  $("#tr-stop").onclick = () => trAct({action: "stop"});
  trLoad();
}
async function trAct(d) {
  const r = await post("/api/simtest", d);
  if (r && r.ok === false) toast("⚠ " + t(r.error || "error")); else if (r) { TR = r; trPaint(); }
  if (d.action === "undo" && r && r.ok) toast("↩ " + t("The previous settings are back"));
  if ((d.action === "apply" || d.action === "apply_all") && r && r.ok) toast("✓ " + t("Taken over - a new test run shows whether it is better"));
  setTimeout(trLoad, 800);
}
async function trLoad() {
  clearTimeout(trT);
  const open = !!document.querySelector(".shsheet #tr-box");          // 2.98.23: open = shown in the sheet «Tests» of the Simulator centre
  const r = await fetch("/api/simtest").then(x => x.ok ? x.json() : null).catch(() => null);
  if (r) { TR = r; trPaint(); }
  const busy = r && (r.busy || (r.sim && r.sim.running));
  trT = setTimeout(trLoad, busy ? 2000 : open ? 6000 : 20000);
}
function trPaint() {
  const R = TR || {}, SM = R.sim || {}, busy = !!R.busy || !!SM.running, A = R.auto;
  [...$("#tr-plan").options].forEach(o => { const p = TR_PLANS.find(x => x[0] === o.value); if (p) o.textContent = t(p[1]); });
  $("#tr-run").disabled = busy || !R.connected; $("#tr-auto").disabled = busy || !R.connected; $("#tr-stop").hidden = !busy; $("#tr-plan").disabled = busy;
  $("#tr-autonote").textContent = !R.connected ? t("Connect the simulation first (3D simulator 3D-3.27 or newer).") : R.msg && !busy ? "⚠ " + t(R.msg) : "";
  $("#tr-live").hidden = !busy;
  if (busy) {
    const tot = SM.total_s || 1, left = SM.left_s || 0;
    $("#tr-livet").textContent = (R.busy === "auto" && A ? "🤖 " + t("Try") + " " + (A.step || 0) + "/" + (A.tries || 0) + (A.now ? " · " + t(A.now) : " · " + t("first a test run as it is now")) + " — " : "")
      + (SM.running ? t("Phase") + " " + SM.phase + "/" + SM.phases + " · " + (SM.phase_name || "") : t("starting …"));
    $("#tr-left").textContent = SM.running ? t("still about") + " " + dur(left) : "";
    $("#tr-bar").style.width = Math.max(2, Math.min(100, 100 * (1 - left / tot))) + "%";
  }
  const box = $("#tr-res");
  if (box.contains(document.activeElement) && document.activeElement.tagName === "SELECT") return;   // do not close an open list
  box.innerHTML = "";
  const L = R.last;
  if (!L) { box.appendChild(el("div", "mut", t("No test run yet."))); return; }
  const rp = L.report || {}, same = (R.runs || []).filter(x => x.plan === L.plan), prev = same.length > 1 ? same[same.length - 2] : null;
  const h = el("h3", "", t("Last test run") + " · " + trDate(L.t) + " · " + t((TR_PLANS.find(p => p[0] === L.plan) || ["", L.plan])[1]).split(" (")[0]); h.style.margin = "6px 0"; box.appendChild(h);
  const tiles = el("div", "tiles");
  const tile = (lab, val, cls) => { const d = el("div", "tile"); d.appendChild(el("div", "mut", lab)); const b = el("b", cls || "", val); d.appendChild(b); tiles.appendChild(d); };
  const asp = (rp.phases || []).reduce((a, p) => a + (p.animals_as_person || 0), 0);
  tile(t("Persons found"), (rp.persons_detected ?? "–") + " / " + (rp.persons ?? "–") + " (" + (rp.rate ?? 0) + " %)", rp.rate >= 90 ? "tr-good" : rp.rate < 70 ? "tr-bad" : "");
  tile(t("Reaction time"), rp.latency_s >= 0 ? rp.latency_s + " s" : "–", rp.latency_s > 2.5 ? "tr-bad" : "");
  tile(t("False alarms"), String(rp.false_alarms ?? "–"), rp.false_alarms ? "tr-bad" : "tr-good");
  tile(t("Animals taken for persons"), String(asp), asp ? "tr-bad" : "tr-good");
  const dsc = prev && L.score != null && prev.score != null ? L.score - prev.score : null;
  tile(t("Score"), (L.score ?? "–") + (dsc != null ? " (" + (dsc >= 0 ? "+" : "") + dsc.toFixed(1) + ")" : ""), dsc > 0 ? "tr-good" : dsc < 0 ? "tr-bad" : "");
  box.appendChild(tiles);
  const CP = R.compare;                             // against the last run with another MoveEye version (2.95.28)
  if (CP) { const d = el("div", CP.score > 0 ? "tr-good" : CP.score < 0 ? "tr-bad" : "mut");
    const ph = (CP.phases || []).map(p => p.name + ": " + [p.found ? (p.found > 0 ? "+" : "") + p.found + " " + t("persons found") : "", p.fa ? (p.fa > 0 ? "+" : "") + p.fa + " " + t("false alarms") : ""].filter(x => x).join(", ")).join(" · ");
    d.textContent = "📊 " + t("Version") + " " + CP.to + " " + t("against") + " " + CP.from + ": " + t("Score") + " " + (CP.score > 0 ? "+" : "") + CP.score + (ph ? " · " + ph : "");
    d.style.margin = "8px 0"; box.appendChild(d); }
  // pictures of the mistakes (2.95.28)
  if ((L.pics || []).length) {
    const hp = el("div", "", "📷 " + t("Pictures of the mistakes (what MoveEye saw)")); hp.style.cssText = "font-weight:600;margin:10px 0 6px"; box.appendChild(hp);
    const gr = el("div"); gr.style.cssText = "display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px";
    L.pics.forEach(pc => { const f = el("figure"); f.style.cssText = "margin:0;border:1px solid var(--line);border-radius:10px;overflow:hidden";
      const im = document.createElement("img"); im.src = "/api/simtest/pic/" + Math.floor(L.t) + "/" + pc.file; im.alt = ""; im.loading = "lazy"; im.style.cssText = "display:block;width:100%";
      const cap = el("figcaption", "", (pc.kind === "false" ? "🚨 " + t("False alarm") + ": " + pc.why : "👻 " + t("Missed") + " (" + pc.what + "): " + String(pc.why).split(", ").map(x => t(x)).join(", ")) + " · " + pc.phase + " · " + Math.round(pc.t) + " s");
      cap.style.cssText = "font-size:12px;padding:5px 7px"; f.append(im, cap); gr.appendChild(f); });
    box.appendChild(gr); }
  // phases
  const sc = el("div", "tr-scroll"), tb = el("table", "tr-tab");
  tb.innerHTML = "<tr><th>" + [t("Phase"), t("Persons"), t("Reaction"), t("Animals reported"), t("False alarms"), t("Missed")].join("</th><th>") + "</th></tr>";
  (rp.phases || []).forEach(p => { const tr = el("tr");
    const why = Object.entries(p.missed_why || {}).filter(([, n]) => n).map(([k, n]) => t({dark: "too dark", small: "small / far", fast: "fast", crouch: "crouching"}[k]) + (n > 1 ? " ×" + n : ""));
    [p.name, p.persons_detected + " / " + p.persons, p.latency_s >= 0 ? p.latency_s + " s" : "–", p.animals_reported + " / " + p.animals, String(p.false_alarms),
     (p.missed || []).length ? (p.missed.length + (why.length ? " (" + why.join(", ") + ")" : "")) : "–"].forEach((v, i) => { const td = el("td", i === 4 && p.false_alarms ? "tr-bad" : "", v); tr.appendChild(td); });
    tb.appendChild(tr); });
  sc.appendChild(tb); box.appendChild(sc);
  const causes = {}; (rp.false_list || []).forEach(f => { causes[f.cause] = (causes[f.cause] || 0) + 1; });
  if (Object.keys(causes).length) { const d = el("div"); d.appendChild(el("span", "mut", t("False alarms by cause") + ": "));
    Object.entries(causes).sort((a, b) => b[1] - a[1]).forEach(([c, n]) => d.appendChild(el("span", "tr-chip", c + " ×" + n))); box.appendChild(d); }
  // proposals
  const sg = R.sugg || [];
  const hs = el("h3", "", "💡 " + t("Proposals for MoveEye")); hs.style.margin = "12px 0 4px"; box.appendChild(hs);
  if (!sg.length) box.appendChild(el("div", "mut", rp.persons && rp.rate >= 100 && !rp.false_alarms ? "🎉 " + t("Everything found, no false alarm - nothing to improve.") : t("No proposals for this test run.")));
  if (sg.length > 1 || R.undo) { const row = el("div", "tr-row");
    if (sg.length > 1) { const b = el("button", "", "✓ " + t("Take over all")); b.type = "button"; b.disabled = busy; b.onclick = () => trAct({action: "apply_all"}); row.appendChild(b);
      const b2 = el("button", "sec", "✓▶ " + t("Take over all and test again")); b2.type = "button"; b2.disabled = busy || !R.connected;
      b2.onclick = async () => { await post("/api/simtest", {action: "apply_all"}); trAct({action: "run", plan: L.plan}); }; row.appendChild(b2); }
    if (R.undo) { const u = el("button", "sec", "↩ " + t("Undo the last change")); u.type = "button"; u.disabled = busy; u.onclick = () => trAct({action: "undo"}); row.appendChild(u); }
    box.appendChild(row); }
  sg.forEach(x => { const c = el("div", "tr-sug");
    c.appendChild(el("b", "", t(x.title)));
    c.appendChild(el("div", "mut", t(x.why).replace("{n}", x.n) + (x.conflict ? " " + t("(goes against another proposal - test again after taking it over)") : "")));
    const ch = el("div", "ch"); x.changes.forEach(([k, o, n]) => { const sp = el("span"); sp.innerHTML = "";
      sp.appendChild(document.createTextNode(t(TR_KEYS[k] || k) + ": ")); sp.appendChild(el("s", "", trVal(o))); sp.appendChild(document.createTextNode(" → ")); sp.appendChild(el("b", "", trVal(n))); ch.appendChild(sp); });
    c.appendChild(ch);
    const row = el("div", "tr-row");
    const b = el("button", "", "✓ " + t("Take over")); b.type = "button"; b.disabled = busy; b.onclick = () => trAct({action: "apply", id: x.id}); row.appendChild(b);
    const b2 = el("button", "sec", "✓▶ " + t("Take over and test again")); b2.type = "button"; b2.disabled = busy || !R.connected;
    b2.onclick = async () => { await post("/api/simtest", {action: "apply", id: x.id}); trAct({action: "run", plan: L.plan}); }; row.appendChild(b2);
    c.appendChild(row); box.appendChild(c); });
  // the report for the development and the night test (2.95.28)
  const hd = el("h3", "", "🛠 " + t("For the development")); hd.style.margin = "14px 0 4px"; box.appendChild(hd);
  box.appendChild(el("div", "mut", t("dev-note")));
  const rr = el("div", "tr-row"); rr.style.marginTop = "6px";
  const dl = el("a", "btn", "📦 " + t("Report for the development")); dl.href = "/api/simtest/report.zip?n=10"; rr.appendChild(dl); box.appendChild(rr);
  const NT = R.nightly || {}; const nr = el("div", "tr-row"); nr.style.marginTop = "10px";
  const nl = el("label", "opt"); nl.style.cssText = "display:flex;gap:8px;align-items:center;flex:1 1 260px";
  const nc = document.createElement("input"); nc.type = "checkbox"; nc.className = "sw"; nc.checked = !!NT.on;
  nl.append(nc, el("span", "", "🌙 " + t("Test run every night")));
  const nhs = document.createElement("select"); for (let h = 0; h < 24; h++) { const o = el("option", "", ("0" + h).slice(-2) + ":00"); o.value = h; nhs.appendChild(o); } nhs.value = NT.hour ?? 3;
  const ps = document.createElement("select"); TR_PLANS.forEach(([k, n]) => { const o = el("option", "", t(n).split(" (")[0]); o.value = k; ps.appendChild(o); }); ps.value = NT.plan || "quick";
  const save = () => post("/api/simtest", {action: "nightly", on: nc.checked, hour: +nhs.value, plan: ps.value}).then(() => toast("✓ " + t("Saved")));
  nc.onchange = nhs.onchange = ps.onchange = save;
  nr.append(nl, nhs, ps); box.appendChild(nr);
  box.appendChild(el("div", "mut", t("night-note"))).style.marginTop = "4px";
  // the automatic optimization
  if (A && (A.log || []).length) {
    const ha = el("h3", "", "🤖 " + t("Automatic optimization")); ha.style.margin = "12px 0 4px"; box.appendChild(ha);
    box.appendChild(el("div", "mut", t("Score at the start") + ": " + (A.base ?? "–") + " · " + t("now") + ": " + (A.best ?? "–")));
    A.log.forEach(g => { if (!g.title) return; const d = el("div", "", (g.kept ? "✅ " : "✖ ") + t(g.title) + " → " + g.score + " · " + t(g.kept ? "kept" : "not better, undone")); d.className = g.kept ? "tr-good" : "mut"; box.appendChild(d); });
  }
  // history
  const runs = R.runs || [];
  if (runs.length > 1) {
    const hh = el("h3", "", "📈 " + t("Earlier test runs")); hh.style.margin = "12px 0 4px"; box.appendChild(hh);
    const hist = el("div", "tr-hist"), vals = runs.map(r => r.score).filter(v => v != null), lo = Math.min(0, ...vals), hi = Math.max(1, ...vals);
    runs.forEach((r, i) => { const b = el("i", i === runs.length - 1 ? "cur" : ""); b.style.height = (r.score == null ? 3 : 6 + 64 * (r.score - lo) / (hi - lo || 1)) + "px";
      b.title = trDate(r.t) + " · " + r.plan + " · " + t("Score") + " " + r.score + " · " + r.found + "/" + r.persons + " · " + t("False alarms") + " " + r.fa; hist.appendChild(b); });
    box.appendChild(hist);
    const sc2 = el("div", "tr-scroll"), t2 = el("table", "tr-tab");
    t2.innerHTML = "<tr><th>" + [t("When"), t("Test"), "MW", t("Persons"), t("False alarms"), t("Score"), t("Changed before")].join("</th><th>") + "</th></tr>";
    runs.slice().reverse().forEach((r, i, arr) => { const tr = el("tr"); const pv = arr.slice(i + 1).find(x => x.plan === r.plan);
      const diff = pv && r.cfg && pv.cfg ? Object.keys(r.cfg).filter(k => JSON.stringify(r.cfg[k]) !== JSON.stringify(pv.cfg[k])).map(k => t(TR_KEYS[k] || k) + " " + trVal(r.cfg[k])) : [];
      [trDate(r.t) + (r.night ? " 🌙" : ""), t((TR_PLANS.find(p => p[0] === r.plan) || ["", r.plan])[1]).split(" (")[0], r.mw || "–", r.found + " / " + r.persons, String(r.fa), String(r.score ?? "–"), diff.join(", ") || "–"].forEach(v => tr.appendChild(el("td", "", v)));
      t2.appendChild(tr); });
    sc2.appendChild(t2); box.appendChild(sc2);
  }
}
trInit();
// ---- live picture: the same moving picture as on the live page; it shrinks into a corner while it is scrolled away ----
let LIVE = false, liveRetry = null, PVM = "view", PVCUR = "";
try { PVM = localStorage.getItem("mw-sim-pvmode") || "view"; } catch (e) {}
// the picture at the top: the simulator window (map, compass, view buttons; 3D-3.18) or the camera picture of MoveEye
const pvView = () => PVM === "view" && !!(S && S.view);
const PVP = simViewPoll($("#s-prev"), 10);
$("#s-prevnote").before(simQBox(PVP));
let PVCTL = false;
let PVPAD = (() => { try { return localStorage.getItem("mw-sim-pvpad") === "1"; } catch (e) { return false; } })();   // 2.95.92: sticks only on request
const pvSrc = () => "/video_feed?r=" + Date.now();
function pvLoad() { const img = $("#s-prev"); if (!LIVE) { PVP.stop(); return; }
  if (pvView()) { img.removeAttribute("src"); PVP.start(); } else { PVP.stop(); img.src = pvSrc(); } }
function pvPaint() {
  const has = !!(S && S.on && S.view), v = pvView();
  $("#s-pvmode").hidden = !(has && LIVE);
  $("#s-pvmode").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.m === (v ? "view" : "cam")));
  $("#s-pvw").classList.toggle("view", v); $("#s-pvbtn").hidden = !v;
  $("#c-prev").classList.toggle("full", v && LIVE); pvSbw(); $("#s-pvlive").hidden = !LIVE || v;
  const want = v ? "view" : "cam";
  if (LIVE && PVCUR !== want) { PVCUR = want; pvLoad(); }
  pvCam();
}
// ---- the phone as a window (2.95.22 / 3D-3.27): turn the phone and look round in the simulator ----
let GYRO = null;
if (window.DeviceOrientationEvent && matchMedia("(pointer:coarse)").matches) $("#s-vgyro").hidden = false;
function gyroAngles(e) {                         // yaw (compass) and pitch for the way the phone is held
  const a = e.alpha || 0, ang = (screen.orientation && screen.orientation.angle) || window.orientation || 0;
  const p = ang === 90 ? -(e.gamma || 0) : ang === -90 || ang === 270 ? (e.gamma || 0) : (e.beta || 0);
  return [a, p];
}
async function gyroOn(on) {
  if (!on) { if (GYRO) removeEventListener("deviceorientation", GYRO.h); GYRO = null; $("#s-vgyro").classList.remove("on"); return; }
  if (typeof DeviceOrientationEvent.requestPermission === "function") {
    try { if (await DeviceOrientationEvent.requestPermission() !== "granted") { toast("⚠ " + t("No access to the motion sensor")); return; } }
    catch (e) { toast("⚠ " + t("The motion sensor needs https (iPhone / iPad)")); return; } }
  GYRO = {a0: null, p0: 0, t: 0, busy: false, last: null};
  GYRO.h = e => { if (!GYRO || e.alpha == null) return; const [a, p] = gyroAngles(e);
    if (GYRO.a0 === null) { GYRO.a0 = a; GYRO.p0 = p; GYRO.start = true; }
    let dy = a - GYRO.a0; dy = ((dy + 540) % 360) - 180;
    GYRO.last = {yaw: dy, pitch: p - GYRO.p0};
    if (GYRO.busy || Date.now() - GYRO.t < 70) return; GYRO.busy = true; GYRO.t = Date.now();
    const st = !!GYRO.start; GYRO.start = false;
    post("/api/sim", Object.assign({action: "look", start: st}, GYRO.last)).finally(() => { if (GYRO) GYRO.busy = false; }); };
  addEventListener("deviceorientation", GYRO.h);
  $("#s-vgyro").classList.add("on"); toast("📱 " + t("Turn the phone to look round. Press 📱 again to stop."));
}
$("#s-vgyro").addEventListener("click", e => { e.stopPropagation(); gyroOn(!GYRO); });
function pvSbw() { document.documentElement.style.setProperty("--sbw", Math.max(0, innerWidth - document.documentElement.clientWidth) + "px"); }
addEventListener("resize", pvSbw);
// small camera live picture inside the simulator window (2.95.19): single pictures, so it never lags behind
let PVCAM = true, pvCamT = null, pvCamBusy = false;
try { PVCAM = localStorage.getItem("mw-sim-pvcam") !== "0"; } catch (e) {}
function pvCam() {
  const on = LIVE && pvView() && PVCAM, box = $("#s-pvcam"); box.hidden = !on;
  $("#s-vcam").classList.toggle("on", PVCAM);
  if (on && !pvCamT) {
    const img = $("#s-pvcimg");
    img.onload = img.onerror = () => { pvCamBusy = false; };
    pvCamT = setInterval(() => { if (document.hidden || pvCamBusy) return; pvCamBusy = true; img.src = "/snapshot.jpg?r=" + Date.now(); }, 500);
  } else if (!on && pvCamT) { clearInterval(pvCamT); pvCamT = null; pvCamBusy = false; }
}
$("#s-vcam").addEventListener("click", e => { e.stopPropagation(); PVCAM = !PVCAM; try { localStorage.setItem("mw-sim-pvcam", PVCAM ? "1" : "0"); } catch (x) {} pvCam(); });
$("#s-pvcam").addEventListener("click", e => { e.stopPropagation(); PVM = "cam"; try { localStorage.setItem("mw-sim-pvmode", PVM); } catch (x) {} pvPaint(); });
$("#s-pvmode").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; PVM = b.dataset.m;
  try { localStorage.setItem("mw-sim-pvmode", PVM); } catch (x) {} pvPaint(); });
function liveOn(on) {
  const img = $("#s-prev");
  if (on === LIVE) return;
  LIVE = on; $("#s-pvw").hidden = !on; $("#s-pvlive").hidden = !on;
  if (on) { PVCUR = pvView() ? "view" : "cam"; pvLoad(); }
  else { clearTimeout(liveRetry); PVP.stop(); img.removeAttribute("src"); PVCUR = ""; pipShow(false); }
  pvPaint();
}
$("#s-prev").addEventListener("error", () => { if (!LIVE || pvView()) return; clearTimeout(liveRetry); liveRetry = setTimeout(() => { if (LIVE && !pvView()) $("#s-prev").src = pvSrc(); }, 2000); });
document.addEventListener("visibilitychange", () => { if (document.hidden) PVP.stop(); else if (LIVE) pvLoad(); });
{ let rot = false;
  const VB = simViewBind($("#s-prev"), {rot: () => rot, active: () => pvView() && !$("#s-prev").closest("#pip"),
    ctl: () => PVCTL || !!(document.fullscreenElement || document.webkitFullscreenElement) || $("#s-pvw").classList.contains("fs")});
  simTouchPad($("#s-pvw"), VB, () => PVPAD && pvView() && !$("#s-prev").closest("#pip") && (PVCTL || !!(document.fullscreenElement || document.webkitFullscreenElement) || $("#s-pvw").classList.contains("fs")));
  const padPaint = () => { $("#s-vpad").classList.toggle("on", PVPAD); $("#s-pvw").classList.toggle("pad", PVPAD); };
  $("#s-vpad").onclick = e => { e.stopPropagation(); PVPAD = !PVPAD; try { localStorage.setItem("mw-sim-pvpad", PVPAD ? "1" : "0"); } catch (x) {} padPaint(); };
  padPaint();
  $("#s-vctl").onclick = () => { PVCTL = !PVCTL; $("#s-vctl").classList.toggle("on", PVCTL); toast(PVCTL ? "✋ " + t("The finger now controls the simulator (scrolling: press ✋ again)") : "↕ " + t("The finger scrolls the page again (a tap still clicks)")); };
  $("#s-vin").onclick = () => VB.push({t: "wheel", d: 1, x: 0.5, y: 0.5}, true);
  $("#s-vout").onclick = () => VB.push({t: "wheel", d: -1, x: 0.5, y: 0.5}, true);
  $("#s-vrot").onclick = () => { rot = !rot; $("#s-vrot").classList.toggle("on", rot); }; }
// full screen for the picture at the top (2.95.9): the real full screen where the browser allows it, else the whole window
function pvFs(on) {
  const w = $("#s-pvw"), fsEl = document.fullscreenElement || document.webkitFullscreenElement;
  if (on === undefined) on = !(fsEl || w.classList.contains("fs"));
  if (on) {
    pipShow(false);
    const rq = w.requestFullscreen || w.webkitRequestFullscreen;
    let p = null; try { p = rq ? rq.call(w) : null; } catch (e) { p = null; }
    if (p && p.catch) p.catch(() => w.classList.add("fs")); else if (!rq) w.classList.add("fs");
  } else {
    w.classList.remove("fs");
    if (fsEl) { const ex = document.exitFullscreen || document.webkitExitFullscreen; try { ex && ex.call(document); } catch (e) {} }
  }
  setTimeout(() => { const f = !!(document.fullscreenElement || document.webkitFullscreenElement) || w.classList.contains("fs"); $("#s-vfs").textContent = f ? "✕" : "⛶"; }, 300);
}
$("#s-vfs").onclick = () => pvFs();
document.addEventListener("keydown", e => { if (e.key === "Escape" && $("#s-pvw").classList.contains("fs")) pvFs(false); });
["fullscreenchange", "webkitfullscreenchange"].forEach(n => document.addEventListener(n, () => { const f = !!(document.fullscreenElement || document.webkitFullscreenElement) || $("#s-pvw").classList.contains("fs"); $("#s-vfs").textContent = f ? "✕" : "⛶"; }));
let pipShow = () => {};
(function () {
  const pip = $("#pip"), slot = pip.querySelector(".pip-in"), img = $("#s-prev"), wrap = $("#s-pvw");
  if (!("IntersectionObserver" in window)) return;
  let closed = false, seen = true;
  try { pip.dataset.c = localStorage.getItem("mw-simpip-corner") || "br"; } catch (e) {}
  img.draggable = false;
  pipShow = on => {
    on = !!on && LIVE && !closed;
    if (on === !pip.hidden) return;
    if (on) { wrap.style.minHeight = wrap.offsetHeight + "px"; slot.appendChild(img); pip.hidden = false; }
    else { pip.hidden = true; wrap.insertBefore(img, wrap.firstChild); wrap.style.minHeight = ""; }
  };
  new IntersectionObserver(es => es.forEach(e => { seen = e.isIntersecting && e.intersectionRatio > 0.2; if (seen) closed = false; pipShow(!seen); }),
    {threshold: [0, 0.2, 0.5, 1]}).observe(wrap);
  $("#pip-x").addEventListener("pointerdown", e => e.stopPropagation());
  $("#pip-x").addEventListener("click", e => { e.stopPropagation(); closed = true; pipShow(false); });
  let st = null;
  pip.addEventListener("pointerdown", e => { if (e.target.id === "pip-x") return; st = {x: e.clientX, y: e.clientY, moved: false};
    try { pip.setPointerCapture(e.pointerId); } catch (x) {} });
  pip.addEventListener("pointermove", e => { if (!st) return; const dx = e.clientX - st.x, dy = e.clientY - st.y;
    if (Math.hypot(dx, dy) > 10) st.moved = true; if (st.moved) pip.style.transform = "translate(" + dx + "px," + dy + "px)"; });
  pip.addEventListener("pointerup", e => {
    if (!st) return; const moved = st.moved; st = null; pip.style.transform = "";
    if (!moved) { $("#c-prev").scrollIntoView({behavior: "smooth", block: "start"}); return; }
    const c = (e.clientY < innerHeight / 2 ? "t" : "b") + (e.clientX < innerWidth / 2 ? "l" : "r"); pip.dataset.c = c;
    try { localStorage.setItem("mw-simpip-corner", c); } catch (x) {}
  });
})();
$("#d-3d").href = "/sim/simulator3d.zip?lang=" + (LANG || "");
function paint3d() { const D = S && S.sim3d; if (D) $("#d-3dn").textContent = D.version + " · " + D.size_mb + " MB" + (D.ready ? "" : " · " + t("prepared on the first download"));
  $("#d-link").textContent = t("Link for the PC browser") + ": " + location.origin + "/sim/simulator3d.zip · " + location.origin + "/sim/simulator_py.zip";
  const P = S && S.simpy; if (P) $("#d-pyn").textContent = P.version + " · " + t("second simulator, needs Python on the PC") + (P.ready ? "" : " · " + t("prepared on the first download")); }
$("#d-py").href = "/sim/simulator_py.zip?lang=" + (LANG || "");
$("#d-link").textContent = t("Link for the PC browser") + ": " + location.origin + "/sim/simulator3d.zip";
(function () { let o = null; try { o = JSON.parse(localStorage.getItem("mw-sim-fold") || "null"); } catch (e) {}
  document.querySelectorAll("details.fold").forEach(d => { if (o && d.dataset.k in o) d.open = !!o[d.dataset.k];
    d.addEventListener("toggle", () => { const m = {}; document.querySelectorAll("details.fold").forEach(x => m[x.dataset.k] = x.open);
      try { localStorage.setItem("mw-sim-fold", JSON.stringify(m)); } catch (e) {} }); }); })();
(async () => { await initAppearance(); load(); })();
/*ALERTS*/
</script></body></html>
"""


# 2.98.0: six tabs by goal (Live · Schutz · Verlauf · Einstellungen · Simulator · Mehr) instead of nine by technique.
# The pages of a tab have a second line (sub tabs). [key, address, name, short name for the phone]
NAV_ITEMS = [("live", "/", "Live", "Live"), ("protect", "/protect", "Protection", "Protection"), ("history", "/recordings", "History", "History"),
             ("settings", "/settings", "Settings", "Sett."), ("sim", "/sim", "Simulator", "Sim"), ("more", "/more", "More", "More")]
NAV_SUB = {"protect": [("protect", "/protect", "Protection"), ("zones", "/zones", "Zones")],
           "history": [("rec", "/recordings", "Recordings"), ("tl", "/timeline", "Night timeline"), ("diary", "/diary", "Diary"), ("msgs", "/messages", "Message list"), ("log", "/log", "Log")],
           "settings": [("settings", "/settings", "Settings"), ("cams", "/cams", "Cameras")],
           "more": [("more", "/more", "Overview"), ("help", "/help", "Manual"), ("party", "/party", "Game corner"), ("tools", "/tools", "Tools")]}
NAV_OF = {"zones": "protect", "rec": "history", "tl": "history", "diary": "history", "msgs": "history", "log": "history", "cams": "settings", "help": "more",
          "party": "more", "tools": "more"}


def nav_html(active):
    top = NAV_OF.get(active, active)
    out = []
    for key, href, label, short in NAV_ITEMS:
        cls = ' class="on"' if key == top else ""
        out.append(f'<a href="{href}"{cls}><span class="nl" data-i18n="{label}">{label}</span><span class="ns" data-i18n="{short}">{short}</span></a>')
    sub = ""
    if top in NAV_SUB:
        sub = '<nav class="subnav">' + "".join(
            f'<a href="{h}"{" class=on" if k == active else ""} data-i18n="{lb}">{lb}</a>' for k, h, lb in NAV_SUB[top]) + "</nav>"
    return '<nav class="nav">' + "".join(out) + "</nav>" + sub


def ui_seed_script():
    """Runs first on every page: copies the saved layout into the browser storage (so the page code finds it there) and
    sends every later layout change back to the Pi, where it is kept in the settings file."""
    data = json.dumps({k: v for k, v in CFG["web_ui"].items() if k not in WEB_UI_LOCAL}).replace("</", "<\\/")   # aufr: per-device keys stay on the device
    return ("<script>(function(){var S=" + data + ";try{for(var k in S)localStorage.setItem(k,S[k]);}catch(e){}"
            "var P={},T=null,L=" + json.dumps(sorted(WEB_UI_LOCAL)) + ";"
            "function send(){var b=P;P={};T=null;try{fetch('/api/ui',{method:'POST',headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({set:b}),keepalive:true}).catch(function(){});}catch(e){}}"
            "try{var o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){o.call(this,k,v);"
            "try{if(this===window.localStorage&&/^mw-/.test(k)&&L.indexOf(k)<0&&S[k]!==String(v)){S[k]=String(v);P[k]=String(v);"
            "clearTimeout(T);T=setTimeout(send,700);}}catch(e){}};}catch(e){}"
            "addEventListener('pagehide',function(){if(T){clearTimeout(T);send();}});})();</script>")


PWA_HEAD = ('<link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'
            '<link rel="icon" type="image/png" href="/icon-192.png"><meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="MoveEye">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black"><meta name="theme-color" content="#0b0f14">')
_ICONS = {}
