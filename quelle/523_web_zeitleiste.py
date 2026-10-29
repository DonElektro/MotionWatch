#@ MoveEye – Teil 523: Web-Seite «Zeitleiste» (Reiter Verlauf) – eine Nacht auf einer Zeitachse, dazu der Wochenbericht. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Wunsch Daniel): «Zeitleiste der Nacht». Handy zuerst (390 px): oben Tag wählen (◀ ▶, Kalender, Nacht / Tag),
# Zusammenfassung, ein Streifen mit Akku-, Temperatur- und Regenkurve und allen Ereignissen als Striche (antippen = dorthin
# springen), darunter die Liste nach Stunden. Ein Eintrag antippen öffnet ihn (Video / Bild / Tagebuch-Bild / Nachricht),
# mit Knopf zur ausführlichen Seite. Unten die Karte «Wochenbericht» (426). Daten: /api/timeline (425), /api/weekreport.
# ----------------------------------------------------------------------------
TL_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Timeline</title>
<style>
/*BASECSS*/
main{padding:12px 16px 48px;max-width:820px;margin:0 auto}
.tlbar{display:flex;gap:8px;align-items:center;margin:2px 0 8px}
.tlbar .day{flex:1;min-width:0;text-align:center;font-weight:700;font-size:15.5px;line-height:1.25;overflow-wrap:anywhere}
.tlbar button{padding:8px 14px;flex:none}
.tlopt{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:center;margin-bottom:8px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.seg button{border:0;border-radius:0;background:transparent;color:var(--txt);padding:7px 12px;font-weight:600}
.seg button.on{background:var(--acc);color:#fff}
#d-pick{width:auto;padding:6px 8px;border-radius:9px;border:1px solid var(--line);background:var(--field);color:var(--txt)}
.sum{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin:4px 0 10px}
.sum .badge{font-size:12.5px;color:var(--txt)}
.chartbox{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 6px 4px;margin-bottom:6px}
#chart{width:100%;height:132px;display:block;cursor:crosshair;touch-action:manipulation}
#chart text{font:10.5px system-ui,sans-serif;fill:var(--mut)}
.leg{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;font-size:11.5px;color:var(--mut);padding:2px 0 2px}
.leg i{display:inline-block;width:12px;height:3px;border-radius:2px;vertical-align:middle;margin-right:4px}
.flt{display:flex;gap:6px;overflow-x:auto;margin:10px 0 2px;scrollbar-width:none;padding-bottom:2px}.flt::-webkit-scrollbar{display:none}
.flt button{flex:none;padding:6px 12px;border-radius:99px;background:var(--btn2);color:var(--txt);border:1px solid var(--line);font-size:13px}
.flt button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
#list{position:relative;margin-top:4px}
#list::before{content:"";position:absolute;left:62px;top:4px;bottom:4px;width:2px;background:var(--line);border-radius:2px}
.hr{position:relative;padding:12px 0 2px 78px;color:var(--mut);font-size:11.5px;font-weight:700;letter-spacing:.06em}
.hr::before{content:"";position:absolute;left:57px;top:15px;width:12px;height:2px;background:var(--mut)}
.it{position:relative;display:flex;gap:8px;align-items:center;padding:5px 0;cursor:pointer}
.it .tm{width:46px;flex:none;text-align:right;color:var(--mut);font-size:12.5px;font-variant-numeric:tabular-nums}
.it .dot{width:20px;height:20px;flex:none;border-radius:50%;display:grid;place-items:center;font-size:10.5px;background:var(--panel);
  border:2px solid var(--line);z-index:1;line-height:1}
.it .bd{flex:1;min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px 10px;display:flex;gap:10px;align-items:center}
.it:hover .bd{border-color:var(--acc2)}
.it .tx{flex:1;min-width:0}.it .t1{font-weight:600;overflow-wrap:anywhere}
.it .t2{color:var(--mut);font-size:12.5px;overflow-wrap:anywhere;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.it img{width:78px;height:56px;object-fit:cover;border-radius:8px;flex:none;background:#000}
.it.rec .dot{border-color:var(--acc)}.it.sight .dot{border-color:var(--grn)}.it.msg .dot{border-color:var(--blu)}
.it.alarm .dot{border-color:var(--red)}.it.alarm .bd{border-color:var(--red)}
.it.log .bd{background:transparent;border-style:dashed;padding:5px 10px}.it.log .t1{font-weight:500;font-size:13px}
.it.hl .bd{outline:2px solid var(--acc);outline-offset:1px}
.it .fa{color:var(--org);font-weight:700}
.empty{padding:26px 8px;text-align:center;color:var(--mut)}
#viewer{position:fixed;inset:0;z-index:60;background:rgba(0,0,0,.9);display:flex;align-items:center;justify-content:center;padding:12px}
#viewer .vb{width:100%;max-width:900px;max-height:100%;overflow:auto}
#viewer img,#viewer video{display:block;width:100%;max-height:68vh;object-fit:contain;border-radius:10px;background:#000}
#viewer .vt{color:#fff;font-weight:700;font-size:16px;margin:10px 0 2px}#viewer .vs{color:#cbd5e1;font-size:13.5px;white-space:pre-wrap;overflow-wrap:anywhere}
#viewer .vn{color:#cbd5e1;font-size:13px;margin:8px 0}
#viewer .vbtn{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
#wr{margin-top:18px}
#wr .ln{padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px}
#wr .tip{margin-top:10px;padding:10px 12px;border-radius:10px;background:var(--field);border:1px solid var(--line)}
#wr .tip a{color:var(--acc2)}
#wr svg{width:100%;height:70px;display:block;margin:6px 0}
#wr svg text{font:10px system-ui,sans-serif;fill:var(--mut)}
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
  <div class="tlbar">
    <button class="sec" id="prev" aria-label="previous">◀</button>
    <div class="day" id="day">…</div>
    <button class="sec" id="next" aria-label="next">▶</button>
  </div>
  <div class="tlopt">
    <span class="seg" id="mode"><button data-v="night" class="on" data-i18n="Night 18–09">Night 18–09</button><button data-v="day" data-i18n="Whole day">Whole day</button></span>
    <input type="date" id="d-pick">
    <button class="sec" id="reload" data-i18n="↻ Refresh">↻ Refresh</button>
  </div>
  <div class="sum" id="sum"></div>
  <div class="chartbox"><svg id="chart" role="img" aria-label="timeline chart"></svg><div class="leg" id="leg"></div></div>
  <div class="flt" id="flt">
    <button data-v="all" class="on" data-i18n="All">All</button><button data-v="rec" data-i18n="Recordings">Recordings</button>
    <button data-v="sight" data-i18n="Animals and persons">Animals and persons</button><button data-v="msg" data-i18n="Messages">Messages</button>
    <button data-v="log" data-i18n="Alarms and log">Alarms and log</button>
  </div>
  <div id="list"><div class="empty" data-i18n="loading …">loading …</div></div>
  <details class="card" id="wr"><summary><span>📈 <span data-i18n="Weekly detection report">Weekly detection report</span> <span id="wr-sub" style="text-transform:none;letter-spacing:0"></span></span></summary>
    <div id="wr-body" style="margin-top:8px"><div class="mut" data-i18n="loading …">loading …</div></div>
  </details>
</main>
<div id="viewer" hidden><div class="vb" id="vb"></div></div>
<script>
/*COMMON*/
Object.assign(I18N.de, __TLDE__);
var DAY = "", MODE = "night", FILT = "all", D = null, VTOK = 0;
try { MODE = localStorage.getItem("mw-tl-mode") === "day" ? "day" : "night"; } catch (e) {}
var ICON = {person: "🚨", tamper: "🛑", warm: "🔥", noise: "🔊", prealarm: "👀", test: "🧪", info: "ℹ️"};
var SIC = {animal: "🦊", person: "👤", warm: "🔥", noise: "🔊", object: "▫"};
function LOC() { return {de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"}[LANG] || "en-GB"; }
function iso(d) { return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
function hm(ts) { return new Date(ts * 1000).toLocaleTimeString(LOC(), {hour: "2-digit", minute: "2-digit"}); }
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
function enc(s) { return encodeURIComponent(s); }
function dayLabel() {
  var d = new Date(DAY + "T12:00:00");
  var w = d.toLocaleDateString(LOC(), {weekday: "long", day: "numeric", month: "numeric"});
  if (MODE === "day") return w;
  var p = new Date(d); p.setDate(p.getDate() - 1);
  return t("Night") + " " + p.toLocaleDateString(LOC(), {weekday: "short"}) + " → " + w;
}
function shift(n) {
  var d = new Date(DAY + "T12:00:00"); d.setDate(d.getDate() + n);
  if (iso(d) > iso(new Date())) return;
  DAY = iso(d); load();
}
function itemsF() {
  if (!D) return [];
  return D.items.filter(function (it) {
    if (FILT === "all") return true;
    if (FILT === "log") return it.type === "log";
    return it.type === FILT;
  });
}
function paintSum() {
  var c = D.count, h = [];
  h.push("🎬 " + c.rec + " " + t("recordings"));
  if (c.false) h.push("✗ " + c.false + " " + t("false alarms"));
  h.push("🦊 " + c.animal + " " + t("animals"));
  h.push("✉ " + c.msg + " " + t("messages"));
  h.push("🚨 " + c.alarm + " " + t("alarms"));
  if (D.bat) h.push("🔋 " + Math.round(D.bat.first) + " → " + Math.round(D.bat.last) + " %");
  if (D.temp) h.push("🌡 " + Math.round(D.temp.min) + "…" + Math.round(D.temp.max) + " °C");
  document.getElementById("sum").innerHTML = h.map(function (x) { return '<span class="badge">' + esc(x) + "</span>"; }).join("");
}
var COL = {rec: "var(--acc)", sight: "var(--grn)", msg: "var(--blu)", alarm: "var(--red)", log: "var(--mut)"};
function paintChart() {
  var svg = document.getElementById("chart"), W = Math.max(280, svg.clientWidth || 360), H = 132, top = 8, bot = 84;
  var a = D.start, b = D.end, X = function (ts) { return 4 + (W - 8) * (ts - a) / (b - a); };
  var s = "";
  var step = (b - a) > 16 * 3600 ? 3 : (W < 420 ? 3 : 2);
  for (var ts = a; ts <= b; ts += 3600) {
    var hh = new Date(ts * 1000).getHours(), x = X(ts);
    s += '<line x1="' + x + '" x2="' + x + '" y1="' + top + '" y2="' + (H - 18) + '" stroke="var(--line)" stroke-width="1"/>';
    if (hh % step === 0) s += '<text x="' + x + '" y="' + (H - 4) + '" text-anchor="middle">' + String(hh).padStart(2, "0") + "</text>";
  }
  var leg = [];
  var rain = D.weather.filter(function (w) { return w.rain > 0; });
  if (rain.length) {
    leg.push('<span><i style="background:var(--blu);opacity:.5;height:8px"></i>' + esc(t("Rain")) + "</span>");
    rain.forEach(function (w) { var hgt = Math.min(bot - top, 10 + 14 * w.rain); s += '<rect x="' + X(w.t) + '" y="' + (bot - hgt) + '" width="' + Math.max(2, X(w.t + 3600) - X(w.t) - 1) + '" height="' + hgt + '" fill="var(--blu)" opacity=".28"/>'; });
  }
  function line(pts, col, dash) {
    if (pts.length < 2) return "";
    return '<polyline fill="none" stroke="' + col + '" stroke-width="2" stroke-linejoin="round"' + (dash ? ' stroke-dasharray="4 3"' : "") + ' points="' + pts.map(function (p) { return p[0].toFixed(1) + "," + p[1].toFixed(1); }).join(" ") + '"/>';
  }
  var bat = D.climate.filter(function (c) { return c.bat != null; });
  if (bat.length) {
    s += line(bat.map(function (c) { return [X(c.t), bot - (bot - top) * Math.max(0, Math.min(100, c.bat)) / 100]; }), "var(--grn)");
    leg.push('<span><i style="background:var(--grn)"></i>' + esc(t("Battery")) + " " + Math.round(bat[bat.length - 1].bat) + " %</span>");
  }
  var tmp = D.climate.filter(function (c) { return c.temp != null; }), own = tmp.length > 0;
  if (!own) tmp = D.weather.filter(function (w) { return w.temp != null; });
  if (tmp.length) {
    var lo = Math.min.apply(null, tmp.map(function (c) { return c.temp; })), hi = Math.max.apply(null, tmp.map(function (c) { return c.temp; }));
    if (hi - lo < 4) { lo -= 2; hi += 2; }
    s += line(tmp.map(function (c) { return [X(c.t), bot - 6 - (bot - top - 12) * (c.temp - lo) / (hi - lo)]; }), "var(--org)", !own);
    leg.push('<span><i style="background:var(--org)"></i>' + esc(own ? t("Temperature") : t("Temperature (weather)")) + " " + Math.round(lo) + "…" + Math.round(hi) + " °C</span>");
  }
  D.items.forEach(function (it) {
    var k = it.type === "log" ? (it.alarm ? "alarm" : "log") : it.type, y0 = {rec: 90, sight: 96, msg: 102, alarm: 88, log: 104}[k];
    var x = X(it.t);
    s += '<line x1="' + x + '" x2="' + x + '" y1="' + y0 + '" y2="' + (k === "log" ? 110 : 112) + '" stroke="' + COL[k] + '" stroke-width="' + (k === "log" ? 1 : 2.5) + '" stroke-linecap="round"/>';
  });
  if (D.now > a && D.now < b) s += '<line x1="' + X(D.now) + '" x2="' + X(D.now) + '" y1="' + top + '" y2="' + (H - 18) + '" stroke="var(--acc2)" stroke-width="1.5" stroke-dasharray="3 3"/>';
  if (!bat.length && !tmp.length) s += '<text x="' + (W / 2) + '" y="' + ((top + bot) / 2) + '" text-anchor="middle">' + esc(t("No battery or temperature values for this time")) + "</text>";
  svg.setAttribute("viewBox", "0 0 " + W + " " + H);
  svg.innerHTML = s;
  leg.push('<span><i style="background:var(--acc)"></i>' + esc(t("Recordings")) + '</span><span><i style="background:var(--grn)"></i>' + esc(t("Animals")) +
           '</span><span><i style="background:var(--blu)"></i>' + esc(t("Messages")) + '</span><span><i style="background:var(--red)"></i>' + esc(t("Alarms")) + "</span>");
  document.getElementById("leg").innerHTML = leg.join("");
}
function rowHtml(it, i) {
  var cls = it.type, dot = "•", t1 = "", t2 = "", img = "";
  if (it.type === "rec") {
    dot = it.kind === "video" ? "🎬" : "📷";
    t1 = t(it.kind === "video" ? "Video" : "Picture") + (it.persons ? " · 👤 " + it.persons : "") + (it.fav ? " ★" : "");
    t2 = [it.dur ? Math.round(it.dur) + " s" : "", it.src || "", it.live ? t("recording now") : ""].filter(Boolean).join(" · ");
    if (it.false) t2 += (t2 ? " · " : "") + '<span class="fa">✗ ' + esc(t("false alarm")) + "</span>";
    else t2 = esc(t2);
    img = "/rec/thumb/" + enc(it.name);
    return wrap(cls, i, it, dot, esc(t1), t2, img);
  }
  if (it.type === "sight") {
    dot = SIC[it.kind] || "▫";
    t1 = it.name || it.label;
    t2 = [it.dur ? it.dur + " s" : "", it.conf ? Math.round(it.conf * 100) + " %" : ""].filter(Boolean).join(" · ");
    img = it.img ? "/diary/img/" + enc(it.img) + "?thumb=1" : "";
  } else if (it.type === "msg") {
    dot = ICON[it.ev] || "✉"; t1 = it.title || "MoveEye"; t2 = it.text || "";
    img = it.img ? "/api/messages/img/" + enc(it.id) : "";
    if ({person: 1, tamper: 1, warm: 1, noise: 1}[it.ev]) cls += " alarm";
  } else {
    dot = it.alarm ? "🚨" : "•"; t1 = it.text; t2 = it.n > 1 ? "× " + it.n + " · " + t("last") + " " + hm(it.t_last) : "";
    if (it.alarm) cls += " alarm";
  }
  return wrap(cls, i, it, dot, esc(t1), esc(t2), img);
}
function wrap(cls, i, it, dot, t1, t2, img) {
  return '<div class="it ' + cls + '" data-i="' + i + '" id="it' + i + '"><div class="tm">' + hm(it.t) + '</div><div class="dot">' + dot + '</div><div class="bd"><div class="tx"><div class="t1">' +
    t1 + "</div>" + (t2 ? '<div class="t2">' + t2 + "</div>" : "") + "</div>" + (img ? '<img loading="lazy" alt="" src="' + esc(img) + '">' : "") + "</div></div>";
}
function paintList() {
  var L = itemsF(), h = "", lastH = null;
  L.forEach(function (it) {
    var d = new Date(it.t * 1000), k = d.getDate() + "-" + d.getHours();
    if (k !== lastH) { lastH = k; h += '<div class="hr">' + String(d.getHours()).padStart(2, "0") + ":00</div>"; }
    h += rowHtml(it, D.items.indexOf(it));
  });
  var box = document.getElementById("list");
  box.innerHTML = h || '<div class="empty">' + esc(t(D.items.length ? "Nothing of this kind in this time." : (MODE === "night" ? "Nothing happened in this night." : "Nothing happened on this day."))) + "</div>";
  box.querySelectorAll(".it").forEach(function (e) { e.onclick = function () { openIt(D.items[+e.dataset.i]); }; });
}
function paint() {
  document.getElementById("day").textContent = dayLabel();
  document.getElementById("d-pick").value = DAY;
  document.getElementById("next").disabled = DAY >= iso(new Date());
  document.querySelectorAll("#mode button").forEach(function (b) { b.classList.toggle("on", b.dataset.v === MODE); });
  if (!D) return;
  paintSum(); paintChart(); paintList();
}
async function load() {
  paint();
  var r = await fetch("/api/timeline?day=" + DAY + "&mode=" + MODE + "&lang=" + LANG).then(function (x) { return x.json(); }).catch(function () { return null; });
  if (!r || !r.ok) { document.getElementById("list").innerHTML = '<div class="empty">⚠ ' + esc(t("connection")) + "</div>"; return; }
  D = r; paint();
}
// tap the chart: jump to the nearest entry of the list
document.getElementById("chart").addEventListener("click", function (ev) {
  if (!D) return;
  var svg = this, rc = svg.getBoundingClientRect(), W = Math.max(280, svg.clientWidth || 360);
  var ts = D.start + (D.end - D.start) * Math.max(0, Math.min(1, ((ev.clientX - rc.left) * W / rc.width - 4) / (W - 8)));
  var L = itemsF(); if (!L.length) return;
  var best = L[0]; L.forEach(function (it) { if (Math.abs(it.t - ts) < Math.abs(best.t - ts)) best = it; });
  var e = document.getElementById("it" + D.items.indexOf(best)); if (!e) return;
  document.querySelectorAll(".it.hl").forEach(function (x) { x.classList.remove("hl"); });
  e.classList.add("hl"); e.scrollIntoView({behavior: "smooth", block: "center"});
});
// ---- the viewer: a recording / a diary picture / a message ----
function vClose() { VTOK++; var v = document.getElementById("viewer"); v.hidden = true; document.getElementById("vb").innerHTML = ""; }
function vBtns(btns) {
  return '<div class="vbtn">' + btns.map(function (b) { return b[1] ? '<a class="btn' + (b[2] ? "" : " sec") + '" href="' + esc(b[1]) + '"' + (b[3] ? " download" : "") + ">" + esc(b[0]) + "</a>" : '<button class="sec" onclick="vClose()">' + esc(b[0]) + "</button>"; }).join("") + "</div>";
}
async function openIt(it) {
  var vb = document.getElementById("vb"), tok = ++VTOK, day = iso(new Date(it.t * 1000));
  document.getElementById("viewer").hidden = false;
  if (it.type === "rec") {
    var media = it.kind === "image" ? '<img alt="" src="/rec/file/' + enc(it.name) + '">' : '<div id="vmedia"><img alt="" src="/rec/thumb/' + enc(it.name) + '"></div>';
    vb.innerHTML = media + '<div class="vt">' + esc(hm(it.t) + " · " + t(it.kind === "video" ? "Video" : "Picture")) + "</div>" +
      '<div class="vs">' + esc([it.dur ? Math.round(it.dur) + " s" : "", it.src, it.false ? "✗ " + t("false alarm") : ""].filter(Boolean).join(" · ")) + '</div><div class="vn" id="vnote"></div>' +
      vBtns([[t("Open in Recordings"), "/recordings?open=" + enc(it.name) + "&day=" + day, true], ["⬇", "/rec/file/" + enc(it.name) + "?dl=1", false, true], ["✕ " + t("Close")]]);
    if (it.kind === "video") {
      var note = document.getElementById("vnote"); note.textContent = t("Preparing video…");
      for (var n = 0; n < 400; n++) {
        var r = await post("/api/rec/prepare", {name: it.name});
        if (tok !== VTOK) return;
        if (r.state === "ready") { document.getElementById("vmedia").innerHTML = '<video controls autoplay playsinline src="' + esc(r.url) + '"></video>'; note.textContent = ""; return; }
        if (r.state === "converting") { note.textContent = t("Converting for the browser (one time)…"); await sleep(1500); continue; }
        note.textContent = r.state === "live" ? t("Still recording - available when it ends.") : (t("Error") + ": " + (r.error || r.state)); return;
      }
    }
  } else if (it.type === "sight") {
    vb.innerHTML = (it.img ? '<img alt="" src="/diary/img/' + enc(it.img) + '">' : "") + '<div class="vt">' + esc(hm(it.t) + " · " + (it.name || it.label)) + "</div>" +
      '<div class="vs">' + esc([it.dur ? it.dur + " s" : "", it.conf ? Math.round(it.conf * 100) + " %" : ""].filter(Boolean).join(" · ")) + "</div>" +
      vBtns([[t("Open the diary"), "/diary", true], ["✕ " + t("Close")]]);
  } else if (it.type === "msg") {
    vb.innerHTML = (it.img ? '<img alt="" src="/api/messages/img/' + enc(it.id) + '">' : "") + '<div class="vt">' + esc(hm(it.t) + " · " + (it.title || "MoveEye")) + "</div>" +
      '<div class="vs">' + esc(it.text || "") + "</div>" + vBtns([[t("All messages"), "/messages", true], ["✕ " + t("Close")]]);
  } else {
    vb.innerHTML = '<div class="vt">' + esc(hm(it.t) + " · " + it.kind) + '</div><div class="vs">' + esc(it.text) + "</div>" + vBtns([[t("Open the log"), "/log", true], ["✕ " + t("Close")]]);
  }
}
document.getElementById("viewer").addEventListener("click", function (e) { if (e.target.id === "viewer") vClose(); });
addEventListener("keydown", function (e) { if (e.key === "Escape") vClose(); });
// ---- weekly detection report (426) ----
async function loadWr() {
  var r = await fetch("/api/weekreport?lang=" + LANG).then(function (x) { return x.json(); }).catch(function () { return null; });
  var b = document.getElementById("wr-body"); if (!r || !r.lines) { b.innerHTML = '<div class="mut">⚠</div>'; return; }
  document.getElementById("wr-sub").textContent = "· " + r.from + " – " + r.to;
  var h = r.lines.map(function (l) { return '<div class="ln">' + esc(l) + "</div>"; }).join("");
  var pts = r.weeks.filter(function (w) { return w.score != null; });
  if (pts.length >= 2) {
    var W = 320, lo = Math.min.apply(null, pts.map(function (w) { return w.score; })), hi = Math.max.apply(null, pts.map(function (w) { return w.score; }));
    if (hi - lo < 10) { lo -= 5; hi += 5; }
    var X = function (i) { return 16 + (W - 32) * i / (r.weeks.length - 1); }, Y = function (v) { return 52 - 40 * (v - lo) / (hi - lo); }, s = "", p = [];
    r.weeks.forEach(function (w, i) { s += '<text x="' + X(i) + '" y="68" text-anchor="middle">' + esc(w.wk) + "</text>";
      if (w.score != null) { p.push(X(i) + "," + Y(w.score)); s += '<circle cx="' + X(i) + '" cy="' + Y(w.score) + '" r="3" fill="var(--acc)"/><text x="' + X(i) + '" y="' + (Y(w.score) - 6) + '" text-anchor="middle">' + Math.round(w.score) + "</text>"; } });
    h += '<div class="mut" style="margin-top:8px">' + esc(t("Test score per week")) + '</div><svg viewBox="0 0 ' + W + ' 72"><polyline fill="none" stroke="var(--acc)" stroke-width="2" points="' + p.join(" ") + '"/>' + s + "</svg>";
  }
  h += '<div class="tip">💡 ' + esc(r.tip) + (r.link ? ' <a href="' + esc(r.link) + '">→</a>' : "") + "</div>";
  h += '<div class="mut" style="margin-top:10px">' + esc(r.on ? t("Comes as a push every") + " " + t(r.day) + " " + String(r.hour).padStart(2, "0") + ":00 (" + t("Settings → Night report") + ")" : t("The weekly push is off (Settings → Night report).")) + "</div>";
  h += '<div class="btns" style="margin-top:10px"><button class="sec" id="wr-send">' + esc(t("Send as push now")) + "</button></div>";
  b.innerHTML = h;
  document.getElementById("wr-send").onclick = async function () { var x = await post("/api/weekreport", {action: "send", lang: LANG}); toast(x.ok ? "✓ " + t("sent") : "⚠ " + (x.error || t("not sent"))); };
}
(function () { var w = document.getElementById("wr"), o = null; try { o = localStorage.getItem("mw-tl-wr"); } catch (e) {}
  w.open = o === "1"; if (w.open) loadWr();
  w.addEventListener("toggle", function () { try { localStorage.setItem("mw-tl-wr", w.open ? "1" : "0"); } catch (e) {} if (w.open) loadWr(); }); })();
document.getElementById("prev").onclick = function () { shift(-1); };
document.getElementById("next").onclick = function () { shift(1); };
document.getElementById("reload").onclick = load;
document.getElementById("d-pick").onchange = function (e) { if (e.target.value) { DAY = e.target.value > iso(new Date()) ? iso(new Date()) : e.target.value; load(); } };
document.querySelectorAll("#mode button").forEach(function (b) { b.onclick = function () { MODE = b.dataset.v; try { localStorage.setItem("mw-tl-mode", MODE); } catch (e) {} load(); }; });
document.querySelectorAll("#flt button").forEach(function (b) { b.onclick = function () { FILT = b.dataset.v; document.querySelectorAll("#flt button").forEach(function (x) { x.classList.toggle("on", x === b); }); if (D) paintList(); }; });
addEventListener("resize", function () { if (D) paintChart(); });
(async function () {
  await initAppearance();
  var q = new URLSearchParams(location.search);
  DAY = /^\d{4}-\d{2}-\d{2}$/.test(q.get("day") || "") ? q.get("day") : iso(new Date());
  load();
  setInterval(function () { if (!document.hidden && DAY === iso(new Date()) && document.getElementById("viewer").hidden) load(); }, 60000);
})();
/*ALERTS*/
</script></body></html>
"""


def tl_page_html():
    de = {k: v[0] for k, v in _HX_VERLAUF.items()}
    return render_page(TL_PAGE, "tl").replace("__TLDE__", json.dumps(de, ensure_ascii=False).replace("</", "<\\/"), 1)


def timeline_routes(app, reply, body, request, Response):
    """the addresses of the timeline and the weekly report (called once by the web server, 550)"""
    @app.route("/timeline")
    def timeline_page():
        return Response(tl_page_html(), mimetype="text/html")

    @app.route("/api/timeline")
    def api_timeline():
        return reply(timeline_build(str(request.args.get("day") or "")[:10], request.args.get("mode", "night"), request.args.get("lang")))

    @app.route("/api/weekreport", methods=["GET", "POST"])
    def api_weekreport():
        if request.method == "POST":
            d = body()
            if d.get("action") == "send":
                r, ok = weekrep_send(manual=True)
                return reply({"ok": ok, "text": r["text"], "error": None if ok else tr_err("notification is not configured", norm_lang(d.get("lang")))})
            return reply({"ok": False, "error": "unknown action"}, 400)
        return reply(weekrep_build(request.args.get("lang")))
