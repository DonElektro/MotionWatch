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
#fb{display:none}#fb.on{display:block}#fb textarea{width:100%;box-sizing:border-box;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit}
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
  <a class="mi" href="/help"><i>📖</i><span><b data-i18n="Manual">Manual</b><small data-i18n="Everything explained, with search">Everything explained, with search</small></span><span class="ar">›</span></a>
  <a class="mi" href="/quick"><i>📄</i><span><b data-i18n="Quick guide (1 page)">Quick guide (1 page)</b><small data-i18n="to print, with the QR codes">to print, with the QR codes</small></span><span class="ar">›</span></a>
  <a class="mi" href="/party"><i>🎲</i><span><b data-i18n="Game corner">Game corner</b><small data-i18n="Quiz, werewolf, connect four … for the campfire">Quiz, werewolf, connect four … for the campfire</small></span><span class="ar">›</span></a>
  <a class="mi" href="/tools"><i>🧰</i><span><b data-i18n="Tools">Tools</b><small data-i18n="Network test, diagnosis and more">Network test, diagnosis and more</small></span><span class="ar">›</span></a>
  <a class="mi" href="/info" id="m-info"><i>👋</i><span><b data-i18n="Info page for guests">Info page for guests</b><small data-i18n="what MoveEye is - for neighbours and fellow campers">what MoveEye is - for neighbours and fellow campers</small></span><span class="ar">›</span></a>
  <a class="mi" href="/almanach"><i>🌦</i><span><b data-i18n="Almanac">Almanac</b><small data-i18n="Sun, moon, weather">Sun, moon, weather</small></span><span class="ar">›</span></a>
  <button type="button" class="mi" onclick="document.getElementById('fb').classList.toggle('on')"><i>💬</i><span><b data-i18n="Feedback to the developer">Feedback to the developer</b><small data-i18n="Ideas, errors, praise - anonymous">Ideas, errors, praise - anonymous</small></span><span class="ar">›</span></button>
  <div class="card" id="fb">
    <select id="fb-k" style="width:100%;margin-bottom:8px"><option value="idea" data-i18n="💡 Idea">💡 Idea</option><option value="bug" data-i18n="🐞 Error">🐞 Error</option><option value="praise" data-i18n="⭐ Praise">⭐ Praise</option><option value="other" data-i18n="💬 Other">💬 Other</option></select>
    <textarea id="fb-t" rows="5" maxlength="3000"></textarea>
    <div class="btns"><button type="button" id="fb-s" data-i18n="Send">Send</button></div><div class="mut" id="fb-r"></div>
  </div>
</main>
<script>
/*COMMON*/
/*MOREDE*/
document.getElementById("fb-s").onclick = async () => {
  const r = await post("/api/feedback", {kind: document.getElementById("fb-k").value, text: document.getElementById("fb-t").value, diag: true, lang: LANG});
  document.getElementById("fb-r").textContent = r && r.ok ? "✓ " + t("Thank you! The message is on its way.") : "⚠ " + ((r && r.error) || "error");
};
(async () => { await initAppearance(); })();
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
           "Ideas, errors, praise - anonymous": "Ideen, Fehler, Lob – anonym", "💡 Idea": "💡 Idee", "🐞 Error": "🐞 Fehler", "⭐ Praise": "⭐ Lob",
           "💬 Other": "💬 Anderes", "Send": "Senden", "Thank you! The message is on its way.": "Danke! Die Nachricht ist unterwegs."}


def more_page():
    js = "Object.assign(I18N.de, " + json.dumps(MORE_DE, ensure_ascii=False) + ");"
    return render_page(MORE_PAGE, "more").replace("/*MOREDE*/", js, 1)


def main_tab_page(tab):
    """2.98.0: one main page, three tabs - Live (picture, joystick, quick switches), Schutz (protection groups) and
    Einstellungen (all other settings). The body gets data-tab; CSS shows the part of the tab."""
    return render_page(WEB_PAGE, tab).replace("<body>", '<body data-tab="' + tab + '">', 1)
