#@ MoveEye – Teil 522: Web-Seite «Nachrichten» (Reiter Verlauf) – die Push-Nachrichten in einer Liste. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13 (Wunsch Daniel): eigenes Menü für die ntfy-Nachrichten. Zwei Quellen: «Von MoveEye» (was dieses Gerät geschickt hat,
# mit Bild und ob es ankam, 065_nachrichten.py) und «ntfy-Server» (alle Nachrichten des Themas der letzten 24 h / 7 Tage).
# ----------------------------------------------------------------------------
MSG_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Messages</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:900px;margin:0 auto}
.mf{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.seg button{border:0;border-radius:0;background:transparent;color:var(--txt);padding:7px 12px}
.seg button.on{background:var(--acc);color:#fff}
.msg{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);align-items:flex-start}
.msg .ic{font-size:22px;width:30px;text-align:center;flex:none}
.msg .bd{flex:1;min-width:0}
.msg .tt{font-weight:700}.msg .tx{white-space:pre-wrap;word-break:break-word;margin-top:2px}
.msg .mt{color:var(--mut);font-size:12.5px;margin-top:4px}
.msg img{width:150px;max-width:38vw;border-radius:8px;flex:none;cursor:zoom-in;background:#000}
.st{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11.5px;font-weight:700;margin-left:6px}
.st-sent{background:rgba(52,199,89,.18);color:var(--grn)}.st-failed{background:rgba(255,69,58,.18);color:var(--red)}
.st-test{background:rgba(255,159,10,.18);color:var(--org)}.st-none{background:rgba(142,142,147,.2);color:var(--mut)}
.st-server{background:rgba(10,132,255,.18);color:var(--blu)}
#big{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:50}
#big img{max-width:96vw;max-height:92vh;border-radius:8px}
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
  <section class="card" style="margin:0">
    <h3 style="margin:0 0 4px" data-i18n="Message list">Messages</h3>
    <div class="mut" style="margin-bottom:10px" data-i18n="Everything MoveEye sent to your phone - and the messages on the ntfy server.">Everything MoveEye sent to your phone - and the messages on the ntfy server.</div>
    <div class="mf">
      <span class="seg" id="src"><button data-v="local" class="on" data-i18n="From MoveEye">From MoveEye</button><button data-v="server" data-i18n="ntfy server">ntfy server</button></span>
      <select id="since" style="display:none"><option value="24h" data-i18n="last 24 h">last 24 h</option><option value="7d" data-i18n="last 7 days">last 7 days</option><option value="all" data-i18n="all (as long as the server keeps them)">all (as long as the server keeps them)</option></select>
      <span class="seg" id="kind"><button data-v="all" class="on" data-i18n="All">All</button><button data-v="alarm" data-i18n="Alarms">Alarms</button><button data-v="info" data-i18n="Info">Info</button><button data-v="test" data-i18n="Tests">Tests</button></span>
      <button class="sec" id="reload" data-i18n="↻ Refresh">↻ Refresh</button>
      <button class="sec" id="clr" data-i18n="Clear list">Clear list</button>
    </div>
    <div id="alx-what"></div>
    <div class="mut" id="cnt"></div>
    <div id="list"></div>
  </section>
</main>
<div id="big" onclick="this.style.display='none'"><img alt=""></div>
<script>
/*COMMON*/
Object.assign(I18N.de, {"Message list": "Nachrichten", "Everything MoveEye sent to your phone - and the messages on the ntfy server.": "Alles, was MoveEye ans Handy geschickt hat – und die Nachrichten auf dem ntfy-Server.",
  "From MoveEye": "Von MoveEye", "ntfy server": "ntfy-Server", "last 24 h": "letzte 24 h", "last 7 days": "letzte 7 Tage", "all (as long as the server keeps them)": "alle (solange der Server sie behält)",
  "All": "Alle", "Alarms": "Alarme", "Info": "Info", "Tests": "Tests", "↻ Refresh": "↻ Neu laden", "Clear list": "Liste leeren",
  "sent": "gesendet", "failed": "fehlgeschlagen", "test inbox": "Test-Postfach", "no push channel": "kein Push-Kanal", "on the server": "auf dem Server",
  "messages": "Nachrichten", "No messages yet.": "Noch keine Nachrichten.", "Clear the list on MoveEye? (The messages on your phone stay.)": "Liste auf MoveEye leeren? (Die Nachrichten auf dem Handy bleiben.)",
  "loading …": "lade …", "Not sent - it is kept and sent again as soon as there is internet.": "Nicht gesendet – sie wird aufbewahrt und nochmals geschickt, sobald es Internet gibt."});
var SRC = "local", KIND = "all", DATA = [];
var ICON = {person: "🚨", tamper: "🛑", warm: "🔥", noise: "🔊", prealarm: "👀", test: "🧪", info: "ℹ️"};
var ALARM = {person: 1, tamper: 1, warm: 1, noise: 1, prealarm: 1};
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
function fmtT(t) { var d = new Date(t * 1000); return d.toLocaleDateString(LANG === "de" ? "de-CH" : undefined, {weekday: "short", day: "2-digit", month: "2-digit"}) + " " + d.toLocaleTimeString(LANG === "de" ? "de-CH" : undefined, {hour: "2-digit", minute: "2-digit", second: "2-digit"}); }
function stTxt(s) { return {sent: t("sent"), failed: t("failed"), test: t("test inbox"), none: t("no push channel"), server: t("on the server")}[s] || s; }
function paint() {
  var L = DATA.filter(function (m) {
    if (KIND === "alarm") return !!ALARM[m.ev];
    if (KIND === "info") return !ALARM[m.ev] && m.status !== "test";
    if (KIND === "test") return m.status === "test" || m.ev === "test";
    return true;
  });
  document.getElementById("cnt").textContent = L.length + " " + t("messages");
  var h = "";
  L.forEach(function (m) {
    var img = m.img ? "/api/messages/img/" + m.id : (m.img_url || "");
    h += '<div class="msg"><div class="ic">' + (ICON[m.ev] || "📩") + '</div><div class="bd"><div class="tt">' + esc(m.title || "MoveEye") +
      '<span class="st st-' + esc(m.status) + '">' + esc(stTxt(m.status)) + (m.where && m.status === "sent" ? " · " + esc(m.where) : "") + '</span></div>' +
      '<div class="tx">' + esc(m.text) + '</div><div class="mt">' + fmtT(m.t) + (m.status === "failed" ? " · " + t("Not sent - it is kept and sent again as soon as there is internet.") : "") +
      '</div></div>' + (img ? '<img loading="lazy" src="' + esc(img) + '" alt="" onclick="big(this.src)">' : "") + '</div>';
  });
  document.getElementById("list").innerHTML = h || '<p class="mut">' + t("No messages yet.") + '</p>';
}
function big(src) { var b = document.getElementById("big"); b.querySelector("img").src = src; b.style.display = "flex"; }
async function load() {
  document.getElementById("cnt").textContent = t("loading …");
  var u = "/api/messages?src=" + SRC + (SRC === "server" ? "&since=" + document.getElementById("since").value : "");
  var r = await fetch(u).then(function (x) { return x.json(); }).catch(function () { return {ok: false, error: "⚠"}; });
  DATA = (r && r.items) || [];
  paint();
  if (r && r.error) document.getElementById("cnt").textContent = "⚠ " + t(r.error);
}
function seg(id, cb) {
  document.querySelectorAll("#" + id + " button").forEach(function (b) {
    b.onclick = function () { document.querySelectorAll("#" + id + " button").forEach(function (x) { x.classList.toggle("on", x === b); }); cb(b.dataset.v); };
  });
}
seg("src", function (v) { SRC = v; document.getElementById("since").style.display = v === "server" ? "" : "none"; document.getElementById("clr").style.display = v === "server" ? "none" : ""; load(); });
seg("kind", function (v) { KIND = v; paint(); });
document.getElementById("since").onchange = load;
document.getElementById("reload").onclick = load;
document.getElementById("clr").onclick = async function () {
  if (!confirm(t("Clear the list on MoveEye? (The messages on your phone stay.)"))) return;
  await fetch("/api/messages", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "clear"})});
  load();
};
load();
setInterval(function () { if (SRC === "local" && !document.hidden) load(); }, 20000);
/*ALERTS*/
</script><script src="/alx/what.js" defer></script></body></html>
"""
