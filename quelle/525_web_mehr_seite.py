#@ MoveEye – Teil 525: Seite «Mehr» (2.98.0) – Anleitung, Spielecke, Werkzeuge, Gäste-Infoseite, Almanach, Rückmeldung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.0: the sixth tab. Everything that is not live picture, protection, history, settings or simulator - one tap away.
# ----------------------------------------------------------------------------
MORE_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - More</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:720px;margin:0 auto}
.mi{display:flex;align-items:center;gap:12px;padding:13px 14px;margin:0 0 8px;border:1px solid var(--line);border-radius:14px;background:var(--panel);
  color:var(--txt);text-decoration:none;cursor:pointer;font:inherit;width:100%;text-align:left}
.mi:hover{border-color:var(--acc)}.mi i{font-style:normal;font-size:22px;width:30px;text-align:center}.mi b{display:block;font-size:15px}
.mi small{color:var(--mut);font-size:12px}.mi .ar{margin-left:auto;color:var(--mut);font-size:18px}
#games{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:14px;margin:0 0 12px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}
#games.on{border-color:var(--grn)}#games .gq{width:120px;height:120px;background:#fff;border-radius:10px;padding:6px;box-sizing:border-box}#games .gq svg{width:100%;height:100%}
#games .gt{flex:1 1 200px}#games .gt b{font-size:16px}#games button{margin:8px 8px 0 0}
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
  <div id="games"><div class="gt"><b>🎮 <span data-i18n="Games">Games</span></b><div class="mut" id="g-txt"></div><div id="g-btn"></div></div></div>
  <a class="mi" href="/help"><i>📖</i><span><b data-i18n="Manual">Manual</b><small data-i18n="Everything explained, with search">Everything explained, with search</small></span><span class="ar">›</span></a>
  <a class="mi" href="/quick"><i>📄</i><span><b data-i18n="Quick guide (1 page)">Quick guide (1 page)</b><small data-i18n="to print, with the QR codes">to print, with the QR codes</small></span><span class="ar">›</span></a>
  <a class="mi" href="/party"><i>🎲</i><span><b data-i18n="Game corner">Game corner</b><small data-i18n="Quiz, werewolf, connect four … for the campfire">Quiz, werewolf, connect four … for the campfire</small></span><span class="ar">›</span></a>
  <a class="mi" href="/tools"><i>🧰</i><span><b data-i18n="Tools">Tools</b><small data-i18n="Network test, diagnosis and more">Network test, diagnosis and more</small></span><span class="ar">›</span></a>
  <a class="mi" href="/info" id="m-info"><i>👋</i><span><b data-i18n="Info page for guests">Info page for guests</b><small data-i18n="what MoveEye is - for neighbours and fellow campers">what MoveEye is - for neighbours and fellow campers</small></span><span class="ar">›</span></a>
  <a class="mi" href="/almanach"><i>🌦</i><span><b data-i18n="Almanac">Almanac</b><small data-i18n="Sun, moon, weather">Sun, moon, weather</small></span><span class="ar">›</span></a>
  <button type="button" class="mi" id="m-fb" onclick="window.mwFeedback && mwFeedback()"><i>💬</i><span><b data-i18n="Feedback to the developer">Feedback to the developer</b><small data-i18n="Errors, wishes, praise, questions - anonymous">Errors, wishes, praise, questions - anonymous</small></span><span class="ar">›</span></button>
  <button type="button" class="mi" id="m-about" onclick="window.mwAbout && mwAbout()"><i>ℹ️</i><span><b data-i18n="About MoveEye">About MoveEye</b><small data-i18n="history, developer, numbers">history, developer, numbers</small></span><span class="ar">›</span></button>
  <div id="g2-more"></div>
  <div id="g2-sys"></div>
</main>
<script>
/*COMMON*/
/*MOREDE*/
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"games-off-note": "One button: game corner (quiz, werewolf …), game collection and - when the 3D simulator runs - «Team against MoveEye». One QR code, type the name, done."});
(async () => { await initAppearance(); gmLoad(); })();
// 2.98.7: «Spiele freigeben» - one button for the game corner, the game collection and the game of the 3D simulator
let GMT = 0;
async function gmLoad() {
  clearTimeout(GMT); let j = null;
  try { j = await (await fetch("/api/party", {cache: "no-store"})).json(); } catch (e) {}
  if (j && j.ok) gmPaint(j);
  GMT = setTimeout(gmLoad, j && j.on ? 4000 : 15000);
}
function gmPaint(j) {
  const box = document.getElementById("games"), tx = document.getElementById("g-txt"), bb = document.getElementById("g-btn"), A = j.all || {};
  box.classList.toggle("on", !!j.on); bb.textContent = ""; const old = box.querySelector(".gq"); if (old) old.remove();
  if (!j.on) {
    tx.textContent = t("games-off-note");
    const b = document.createElement("button"); b.type = "button"; b.textContent = "🎮 " + t("Open all games");
    b.onclick = async () => { b.disabled = true; const r = await post("/api/party", {action: "all", hours: 6}); if (r && r.ok) gmPaint(r); b.disabled = false; };
    bb.appendChild(b); return;
  }
  const q = document.createElement("div"); q.className = "gq"; q.innerHTML = j.qr || ""; box.insertBefore(q, box.firstChild);
  const until = new Date(Date.now() + (j.left || 0) * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
  tx.textContent = t("Open until") + " " + until + " · " + (j.players || []).length + " " + t("players") + " · "
    + [t("Game corner"), A.coll ? t("Game collection") : "", A.sim ? t("Simulator game") : ""].filter(Boolean).join(" + ") + ". " + t("Scan the QR code with the phone (same Wi-Fi).");
  const a = document.createElement("a"); a.className = "btn"; a.href = "/party"; a.textContent = t("Players and QR code") + " ›";
  const c = document.createElement("button"); c.type = "button"; c.className = "sec"; c.textContent = "⛔ " + t("Close");
  c.onclick = async () => { if (!confirm(t("Close all games? The players are logged out."))) return; const r = await post("/api/party", {action: "close"}); if (r && r.ok) gmPaint(r); };
  bb.append(a, c);
}
fetch("/info", {method: "HEAD"}).then(r => { if (!r.ok) document.getElementById("m-info").hidden = true; }).catch(() => {});
/*ALERTS*/
</script>
</body></html>
"""

MORE_DE = {"Everything explained, with search": "Alles erklärt, mit Suche", "Quick guide (1 page)": "Kurzanleitung (1 Seite)",
           "to print, with the QR codes": "zum Ausdrucken, mit den QR-Codes", "Quiz, werewolf, connect four … for the campfire": "Quiz, Werwolf, Vier gewinnt … fürs Lagerfeuer",
           "Network test, diagnosis and more": "Netztest, Diagnose und mehr", "Info page for guests": "Infoseite für Gäste",
           "what MoveEye is - for neighbours and fellow campers": "was MoveEye ist – für Nachbarn und Mitcamper", "Almanac": "Almanach",
           "Sun, moon, weather": "Sonne, Mond, Wetter", "Feedback to the developer": "Rückmeldung an den Entwickler",
           "Errors, wishes, praise, questions - anonymous": "Fehler, Wünsche, Lob, Fragen – anonym",
           "About MoveEye": "Über MoveEye", "Send a test feedback": "Test-Feedback senden",
           "for the developer: does a message reach the servers?": "für den Entwickler: kommt eine Nachricht bei den Servern an?", "history, developer, numbers": "Geschichte, Entwickler, Zahlen",
           "Games": "Spiele", "Open all games": "Spiele freigeben", "Open until": "Offen bis", "players": "Spieler", "Game corner": "Spielecke",
           "Game collection": "Spielesammlung", "Simulator game": "Simulator-Spiel", "Scan the QR code with the phone (same Wi-Fi).": "QR-Code mit dem Handy scannen (gleiches WLAN).",
           "Players and QR code": "Spieler und QR-Code", "Close": "Schliessen", "Close all games? The players are logged out.": "Alle Spiele schliessen? Die Spieler werden abgemeldet.",
           "games-off-note": "Eine Taste: Spielecke (Quiz, Werwolf …), Spielesammlung und – wenn der 3D-Simulator läuft – «Team gegen MoveEye». Ein QR-Code, Name eingeben, fertig."}


def more_page():
    js = "Object.assign(I18N.de, " + json.dumps(MORE_DE, ensure_ascii=False) + ");"
    return render_page(MORE_PAGE, "more").replace("/*MOREDE*/", js, 1)


def main_tab_page(tab):
    """2.98.0: one main page, three tabs - Live (picture, joystick, quick switches), Schutz (protection groups) and
    Einstellungen (all other settings). The body gets data-tab; CSS shows the part of the tab."""
    return render_page(WEB_PAGE, tab).replace("<body>", '<body data-tab="' + tab + '">', 1).replace(
        "</body>", '<script src="/alx/what.js" defer></script></body>', 1)          # 2.98.13: «What was it?» below the picture (066)
