#@ Motion Watch – Teil 520: Web: Kameras, Zonen, Tagebuch, Gast, Protokoll. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
CAMS_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Cameras</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1700px;margin:0 auto}
.camgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}
@media(max-width:520px){.camgrid{grid-template-columns:1fr}}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);overflow:hidden;box-shadow:var(--shadow)}
.tile.big{grid-column:1/-1}
.tile .vw{position:relative;background:#000;aspect-ratio:16/9;cursor:zoom-in}
.tile.big .vw{cursor:zoom-out}
.tile img{width:100%;height:100%;object-fit:contain;display:block}
.tile .vw .ov{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#9fb0c6;font-weight:600;text-align:center;padding:12px;pointer-events:none}
.th2{display:flex;align-items:center;gap:8px;padding:9px 12px}
.th2 b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dot{font-size:14px;color:var(--mut)}.dot.on{color:var(--grn)}.dot.bad{color:var(--red)}
.chip{font-size:11px;font-weight:700;border-radius:6px;padding:1px 7px;color:#fff}
.chip.mo{background:var(--org)}.chip.rc{background:var(--red)}
.add{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center}
.add select{width:100%}
h3{margin:0 0 8px;font-size:11px;letter-spacing:.09em;color:var(--mut);text-transform:uppercase}
.note{margin-top:8px}
.btrow{gap:8px;padding:5px 0;border-bottom:1px solid var(--line)}.btrow>span:first-child{flex:1;min-width:0;overflow-wrap:anywhere}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="badge" id="b-n">–</span>
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <div class="camgrid" id="grid"></div>
  <section class="card" style="margin-top:16px">
    <h3 data-i18n="Add camera">Add camera</h3>
    <div class="add">
      <select id="pick"></select>
      <button class="sec" id="btn-scan" onclick="scan()" data-i18n="Scan for cameras">Scan for cameras</button>
      <button onclick="add()" data-i18n="Add">Add</button>
    </div>
    <div class="err" id="err"></div>
    <details style="margin-top:6px"><summary class="mut" style="cursor:pointer" data-i18n="Add network camera">Add network camera</summary>
      <div class="add" style="grid-template-columns:1fr 2fr auto;margin-top:8px">
        <input type="text" id="ip-name" placeholder="Name" maxlength="40">
        <input type="text" id="ip-url" placeholder="rtsp://user:pass@192.168.1.50:554/stream1  |  http://192.168.1.50:8080/video" maxlength="500">
        <button class="sec" onclick="addIp()" data-i18n="Add">Add</button>
      </div></details>
    <div class="mut note" id="note"></div>
  </section>
  <section class="card" style="margin-top:16px" id="fleet-card">
    <h3 data-i18n="Other MoveEye devices">Other MoveEye devices</h3>
    <div class="mut" data-i18n="Several devices around the tent or camper: see them all here and arm / disarm them together.">Several devices around the tent or camper: see them all here and arm / disarm them together.</div>
    <div class="btns">
      <button type="button" onclick="fleetArm('all','arm')" data-i18n="🛡 Arm all">🛡 Arm all</button>
      <button type="button" class="sec" onclick="fleetArm('all','disarm')" data-i18n="Disarm all">Disarm all</button>
    </div>
    <div class="camgrid" id="fleet" style="margin-top:12px"></div>
    <details style="margin-top:10px"><summary class="mut" style="cursor:pointer" data-i18n="Add a device">Add a device</summary>
      <div class="add" style="grid-template-columns:2fr 1fr 1fr auto;margin-top:8px">
        <input type="text" id="fl-url" placeholder="http://192.168.1.20:5000" maxlength="140">
        <input type="text" id="fl-name" placeholder="Name" maxlength="40">
        <input type="password" id="fl-pw" placeholder="Password" maxlength="64" autocomplete="new-password">
        <button class="sec" onclick="fleetAdd()" data-i18n="Add">Add</button>
      </div>
      <div class="btns"><button class="sec" type="button" id="fl-scan" onclick="fleetScan()" data-i18n="🔍 Search in the network">🔍 Search in the network</button></div>
      <div id="fl-found"></div>
    </details>
    <div class="err" id="fl-err"></div>
  </section>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"Add camera": "Kamera hinzufügen", "Scan for cameras": "Nach Kameras suchen", "Scanning…": "Suche läuft …", "Add": "Hinzufügen",
  "Add network camera": "Netzwerk-Kamera hinzufügen", "Main camera": "Hauptkamera", "Remove": "Entfernen", "motion": "Bewegung", "REC": "AUFN",
  "connected": "verbunden", "connecting…": "verbinde …", "failed": "fehlgeschlagen", "switch failed": "Wechsel fehlgeschlagen", "still using": "weiter mit", "starting": "startet", "connection lost - reconnecting": "Verbindung verloren - verbinde neu",
  "cameras": "Kameras", "Choose a camera…": "Kamera wählen …", "no picture yet": "noch kein Bild",
  "The main camera does the full detection (AI, tracking, relays). Extra cameras watch for movement and record clips; they follow the same switches and schedules. Every extra camera needs CPU - on a Raspberry Pi 2-3 cameras are realistic.":
    "Die Hauptkamera macht die volle Erkennung (KI, Verfolgung, Relais). Zusatzkameras erkennen Bewegung und nehmen Clips auf; sie folgen denselben Schaltern und Zeitplänen. Jede Zusatzkamera braucht CPU - auf einem Raspberry Pi sind 2-3 Kameras realistisch.",
  "Remove this camera?": "Diese Kamera entfernen?", "Name": "Name"});
let SIG = "", SRC = null;
const tStatus = s => !s ? "" : s.startsWith("switch failed:") ? t("switch failed") + s.slice(14).replace("(still using ", "(" + t("still using") + " ") : s.startsWith("failed:") ? t("failed") + s.slice(7) : t(s);
function tile(c) {
  const box = el("div", "tile"); box.dataset.id = c.id;
  const vw = el("div", "vw"), img = el("img"); img.alt = ""; img.dataset.src = c.n === 0 ? "/video_feed" : "/cam_feed/" + c.n; img.src = img.dataset.src; keepStream(img);
  const ov = el("div", "ov", t("no picture yet")); img.onload = () => ov.hidden = true;
  vw.append(img, ov); vw.onclick = () => box.classList.toggle("big");
  const hd = el("div", "th2"), dot = el("span", "dot", "●"), name = el("b", "", c.n === 0 ? t("Main camera") + " · " + c.label : c.label);
  const mo = el("span", "chip mo", t("motion")), rc = el("span", "chip rc", "● " + t("REC")), st = el("span", "mut");
  mo.hidden = rc.hidden = true; hd.append(dot, name, mo, rc, st);
  if (c.n !== 0) { const x = el("button", "sec", "✕"); x.title = t("Remove"); x.style.padding = "3px 9px";
    x.onclick = async () => { if (confirm(t("Remove this camera?"))) { await post("/api/cams", {action: "remove", id: c.id}); SIG = ""; poll(); } }; hd.appendChild(x); }
  box.append(vw, hd); box._u = c2 => {
    dot.className = "dot " + (c2.status === "connected" ? "on" : (c2.status.startsWith("failed") ? "bad" : ""));
    mo.hidden = !c2.motion; rc.hidden = !c2.recording;
    st.textContent = tStatus(c2.status) === t("connected") ? (c2.res || "") + (c2.fps ? " · " + c2.fps + " fps" : "") : tStatus(c2.status);
    ov.hidden = c2.status === "connected" && img.naturalWidth > 0;
  };
  return box;
}
async function poll() {
  let j; try { j = await (await fetch("/api/cams")).json(); } catch (e) { return; }
  const sig = j.cams.map(c => c.id + ":" + c.n).join("|") + LANG;
  const g = $("#grid");
  if (sig !== SIG) { SIG = sig; g.textContent = ""; j.cams.forEach(c => g.appendChild(tile(c))); }
  [...g.children].forEach((b, i) => j.cams[i] && b._u(j.cams[i]));
  $("#b-n").textContent = j.cams.length + " " + t("cameras");
  SRC = j.sources; fillPick(j);
}
function fillPick(j) {
  const sel = $("#pick"), cur = sel.value; if (sel.matches(":focus")) return;
  const used = new Set(j.cams.map(c => c.id)); sel.textContent = "";
  const o0 = el("option", "", t("Choose a camera…")); o0.value = ""; sel.appendChild(o0);
  (j.sources.items || []).filter(i => i.id !== "auto" && !used.has(i.id)).forEach(i => {
    const o = el("option", "", i.name + (i.detail ? " [" + i.detail.replace("in use", "") + "]" : "")); o.value = i.id; sel.appendChild(o); });
  sel.value = cur;
  $("#note").textContent = t("The main camera does the full detection (AI, tracking, relays). Extra cameras watch for movement and record clips; they follow the same switches and schedules. Every extra camera needs CPU - on a Raspberry Pi 2-3 cameras are realistic.");
}
function showErr(m) { $("#err").textContent = m ? "⚠ " + m : ""; if (m) setTimeout(() => $("#err").textContent = "", 6000); }
async function add() { const id = $("#pick").value; if (!id) return; const r = await post("/api/cams", {action: "add", id: id, lang: LANG}); showErr(r.ok ? "" : r.error); SIG = ""; poll(); }
async function scan() {
  const b = $("#btn-scan"); b.disabled = true; b.textContent = t("Scanning…");
  await post("/api/sources/scan", {}); b.disabled = false; b.textContent = t("Scan for cameras"); poll();
}
async function addIp() {
  const r = await post("/api/source", {action: "add", name: $("#ip-name").value, url: $("#ip-url").value, select: false, lang: LANG});
  if (!r.ok) { showErr(r.error); return; }
  $("#ip-name").value = $("#ip-url").value = "";
  const r2 = await post("/api/cams", {action: "add", id: r.id, lang: LANG}); showErr(r2.ok ? "" : r2.error); SIG = ""; poll();
}
// ---- other MoveEye devices ----
Object.assign(I18N.de, {"Other MoveEye devices": "Weitere Motion-Watch-Geräte",
  "Several devices around the tent or camper: see them all here and arm / disarm them together.": "Mehrere Geräte rund ums Zelt oder Wohnmobil: hier alle sehen und gemeinsam scharf / unscharf schalten.",
  "🛡 Arm all": "🛡 Alle scharf", "Disarm all": "Alle unscharf", "Add a device": "Gerät hinzufügen", "Password": "Passwort",
  "🔍 Search in the network": "🔍 Im Netzwerk suchen", "This device": "Dieses Gerät", "armed": "Schutz an", "disarmed": "Schutz aus", "arming": "Schutz startet",
  "ALARM": "ALARM", "not reachable": "nicht erreichbar", "password wrong": "Passwort falsch", "Open": "Öffnen", "Arm": "Scharf", "Disarm": "Schutz aus",
  "Remove this device from the list?": "Dieses Gerät aus der Liste entfernen?", "needs a password": "braucht ein Passwort", "Nothing found.": "Nichts gefunden.",
  "searching (about 10 s) …": "suche (ca. 10 s) …", "mains": "Netz", "battery": "Akku", "Set password": "Passwort setzen", "recording": "Aufnahme"});
let FLSIG = "";
function flTile(id, name, url, st, me) {
  const box = el("div", "tile");
  const vw = el("div", "vw"), img = el("img"); img.alt = "";
  img.src = me ? "/video_feed" : "/fleet/snap/" + id + "?t=" + Date.now(); if (me) keepStream(img); else img.dataset.fl = id;
  const ov = el("div", "ov", st.ok === false ? "⚠ " + t(st.err || "not reachable") : t("no picture yet")); img.onload = () => ov.hidden = true;
  vw.append(img, ov);
  const hd = el("div", "th2"), dot = el("span", "dot" + (st.ok === false ? " bad" : " on"), "●");
  const nm = el("b", "", (me ? "📍 " : "") + (name || url || "?"));
  hd.append(dot, nm);
  if (st.persons) hd.appendChild(el("span", "chip rc", t("ALARM")));
  if (st.recording) hd.appendChild(el("span", "chip rc", t("REC")));
  const info = el("div", "mut"); info.style.cssText = "padding:0 12px 6px";
  if (st.ok !== false && st.arm) info.textContent = [t(st.arm), st.battery != null ? "🔋 " + st.battery + " %" : "", st.mains === true ? "🔌 " + t("mains") : (st.mains === false ? "⚡ " + t("battery") : ""),
    st.temp != null ? Math.round(st.temp) + " °C" : "", st.version ? "v" + st.version : "", st.tamper ? "⚠ " + st.tamper : ""].filter(Boolean).join(" · ");
  const last = el("div", "mut", st.last || ""); last.style.cssText = "padding:0 12px 8px;font-size:11px";
  const bt = el("div", "btns"); bt.style.cssText = "padding:0 12px 12px;margin:0";
  const armed = st.arm === "armed" || st.arm === "arming";
  const ab = el("button", armed ? "sec" : "", armed ? t("Disarm") : t("Arm")); ab.type = "button"; ab.onclick = () => fleetArm(me ? "me" : id, armed ? "disarm" : "arm");
  bt.appendChild(ab);
  if (!me) {
    const op = el("a", "btn sec", t("Open")); op.href = url; op.target = "_blank"; bt.appendChild(op);
    if (st.err === "password wrong") { const pb = el("button", "sec", "🔑 " + t("Set password")); pb.type = "button";
      pb.onclick = async () => { const pw = prompt(t("Password")); if (pw === null) return; await post("/api/fleet", {action: "password", id: id, password: pw}); fleetPoll(); }; bt.appendChild(pb); }
    const rm = el("button", "sec", "🗑"); rm.type = "button"; rm.title = t("Remove");
    rm.onclick = async () => { if (!confirm(t("Remove this device from the list?"))) return; await post("/api/fleet", {action: "remove", id: id}); FLSIG = ""; fleetPoll(); };
    bt.appendChild(rm);
  }
  box.append(vw, hd, info, last, bt);
  return box;
}
async function fleetPoll() {
  if (document.hidden) return;
  let j; try { j = await (await fetch("/api/fleet", {cache: "no-store"})).json(); } catch (e) { return; }
  const G = $("#fleet"); if (!G || !j || !j.me || !Array.isArray(j.devices)) return;    // e.g. a user without admin rights
  const sig = JSON.stringify([j.me.arm, j.me.persons, j.me.recording, j.me.battery, j.me.tamper, j.me.last, j.devices.map(d => [d.id, d.name, d.st.ok, d.st.err, d.st.arm, d.st.persons, d.st.recording, d.st.battery, d.st.mains, d.st.tamper, d.st.last])]);
  if (sig !== FLSIG) {
    FLSIG = sig; G.textContent = "";
    G.appendChild(flTile("me", t("This device") + (j.me.name && j.me.name !== "MoveEye" ? " – " + j.me.name : ""), "", Object.assign({ok: true}, j.me), true));
    j.devices.forEach(d => G.appendChild(flTile(d.id, d.name, d.url, d.st || {}, false)));
  } else {
    G.querySelectorAll("img[data-fl]").forEach(i => { i.src = "/fleet/snap/" + i.dataset.fl + "?t=" + Date.now(); });
  }
}
async function fleetArm(id, action) {
  const r = await post("/api/fleet", {action: action, id: id, lang: LANG});
  $("#fl-err").textContent = r.ok ? "" : "⚠ " + t("not reachable"); FLSIG = ""; fleetPoll();
}
async function fleetAdd(url, needsPw) {
  const r = await post("/api/fleet", {action: "add", url: url || $("#fl-url").value, name: url ? "" : $("#fl-name").value, password: url ? (needsPw ? prompt(t("Password")) || "" : "") : $("#fl-pw").value, lang: LANG});
  $("#fl-err").textContent = r.ok ? "" : "⚠ " + (r.error || "error");
  if (r.ok && !url) { $("#fl-url").value = $("#fl-name").value = $("#fl-pw").value = ""; }
  FLSIG = ""; fleetPoll();
}
async function fleetScan() {
  const b = $("#fl-scan"), out = $("#fl-found"); b.disabled = true; out.textContent = t("searching (about 10 s) …");
  const r = await post("/api/fleet", {action: "scan", lang: LANG}); b.disabled = false; out.textContent = "";
  if (!r.found || !r.found.length) { out.textContent = t("Nothing found."); return; }
  r.found.forEach(f => { const row = el("div", "row btrow"); row.append(el("span", "", (f.name || "MoveEye") + " · " + f.url + (f.needs_pw ? " · 🔑 " + t("needs a password") : "")));
    const a = el("button", "sec", t("Add")); a.type = "button"; a.onclick = () => { fleetAdd(f.url, f.needs_pw); row.remove(); }; row.appendChild(a); out.appendChild(row); });
}
/*BTJS*/
async function btUse() {
  try { const j = await (await fetch("/api/bt", {cache: "no-store"})).json(); const d = (j.devices || []).find(x => "bt:" + x.mac === j.out);
    $("#bt-use").textContent = t("Loudspeaker in use") + ": " + (d ? d.name + (d.connected ? " ✓" : "") : (j.out && !j.out.startsWith("bt:") ? j.out.replace("plughw:CARD=", "").split(",")[0] : t("none")));
  } catch (e) {}
}
document.addEventListener("visibilitychange", () => {      // no stream while the tab is hidden = no CPU
  document.querySelectorAll(".tile img").forEach(i => { if (i.dataset.src) i.src = document.hidden ? "" : i.dataset.src; });
});
(async () => { await initAppearance(); poll(); setInterval(poll, 2500);
  fleetPoll(); setInterval(fleetPoll, 3000); })();
/*ALERTS*/
</script></body></html>
"""

ZONES_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Zones</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1500px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;align-items:start}
@media(max-width:980px){main{grid-template-columns:1fr}}
#cv{width:100%;display:block;background:#000;border-radius:12px;touch-action:none;cursor:crosshair;box-shadow:0 0 0 1px var(--line)}
.zrow{border:1px solid var(--line);border-radius:10px;padding:8px;margin-top:8px;display:grid;grid-template-columns:1fr auto;gap:6px 8px;align-items:center;background:var(--field)}
.zrow.sel{border-color:var(--acc);box-shadow:0 0 0 3px var(--glow)}
.zrow input[type=text]{width:100%}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
ol{padding-left:18px;margin:6px 0}
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
    <canvas id="cv" width="1280" height="720"></canvas>
    <div class="mut" id="hint" style="margin-top:8px"></div>
  </section>
  <aside>
    <div class="card" style="margin:0 0 14px">
      <div class="btns" style="margin-top:0">
        <button onclick="startZone('ignore')" data-i18n="+ Ignore zone">+ Ignore zone</button>
        <button onclick="startZone('only')" data-i18n="+ Only-here zone">+ Only-here zone</button>
        <button onclick="startZone('privacy')" data-i18n="+ Privacy zone">+ Privacy zone</button>
        <button onclick="startZone('line')" data-i18n="+ Line">+ Line</button>
        <button onclick="startZone('loiter')" data-i18n="+ Dwell area">+ Dwell area</button>
      </div>
      <div class="btns"><button class="sec" id="b-fin" onclick="finish()" data-i18n="Finish shape" hidden>Finish shape</button>
        <button class="sec" onclick="loadFrame()" data-i18n="New picture">New picture</button></div>
      <div id="list"></div>
      <div class="btns"><button id="b-save" onclick="save()" data-i18n="Save zones">Save zones</button></div>
      <div class="err" id="err"></div>
    </div>
    <div class="card" style="margin:0">
      <div class="legend mut"><div><i style="background:#f59a4a"></i><span data-i18n="Ignore zone">Ignore zone</span>: <span data-i18n="z-ign">z-ign</span></div>
      <div style="margin-top:4px"><i style="background:#3fcf6b"></i><span data-i18n="Only-here zone">Only-here zone</span>: <span data-i18n="z-only">z-only</span></div>
      <div style="margin-top:4px"><i style="background:#a98bff"></i><span data-i18n="Privacy zone">Privacy zone</span>: <span data-i18n="z-priv">z-priv</span></div>
      <div style="margin-top:4px"><i style="background:#3cd2ff"></i><span data-i18n="Line">Line</span>: <span data-i18n="z-line">z-line</span></div>
      <div style="margin-top:4px"><i style="background:#ffdc3c"></i><span data-i18n="Dwell area">Dwell area</span>: <span data-i18n="z-loit">z-loit</span></div></div>
      <div class="mut" style="margin-top:8px" data-i18n="z-how">z-how</div>
    </div>
  </aside>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"+ Ignore zone": "+ Ignorier-Zone", "+ Only-here zone": "+ Nur-hier-Zone", "+ Privacy zone": "+ Privatsphäre-Zone",
  "Privacy zone": "Privatsphäre-Zone",
  "z-priv": "Der Bereich wird schwarz abgedeckt – im Live-Bild, in Aufnahmen, Fotos und Zeitraffer. Er wird nie gespeichert oder übertragen (Nachbarzelt, Weg, fremdes Fenster). Wichtig für den Datenschutz.", "Finish shape": "Form abschliessen", "New picture": "Neues Bild",
  "Save zones": "Zonen speichern", "Ignore zone": "Ignorier-Zone", "Only-here zone": "Nur-hier-Zone", "Delete": "Löschen", "Saved": "Gespeichert",
  "Click the corners of the area in the picture. Click the first point or press 'Finish shape' to close it.": "Klicke die Ecken des Bereichs im Bild an. Klicke den ersten Punkt oder 'Form abschliessen', um die Form zu schliessen.",
  "Drag a corner to move it. Select a zone in the list to edit it.": "Eine Ecke lässt sich verschieben. Wähle eine Zone in der Liste zum Bearbeiten.",
  "no zones": "keine Zonen", "+ Line": "+ Linie", "+ Dwell area": "+ Verweil-Bereich", "Line": "Linie", "Dwell area": "Verweil-Bereich",
  "both directions": "beide Richtungen", "only in the arrow direction": "nur in Pfeilrichtung", "only against the arrow": "nur gegen den Pfeil",
  "Alarm after (seconds)": "Alarm nach (Sekunden)", "Click the start and the end of the line in the picture.": "Klicke Anfang und Ende der Linie im Bild an.",
  "z-line": "Meldet, wenn eine Person die Linie überquert – in beide Richtungen oder nur in Pfeilrichtung (z. B. «kommt zum Zelt»).",
  "z-loit": "Meldet, wenn sich eine Person länger als die eingestellte Zeit darin aufhält (z. B. beim Auto).", "no picture - is the camera running?": "kein Bild - läuft die Kamera?", "Name": "Name",
  "z-ign": "Personen und Objekte, deren Füsse darin stehen, werden ignoriert (Strasse, Baum, Nachbars Garten).",
  "z-only": "Wenn mindestens eine solche Zone existiert, zählt nur, was darin passiert (Eingang, Einfahrt).",
  "z-how": "Eine Zone wirkt auf die Erkennung, die Aufnahme, die Alarme und die Relais. Gezählt wird der Punkt unten in der Mitte des erkannten Objekts (die Füsse)."});
Object.assign(I18N, {en: {"z-line": "Reports when a person crosses the line – both ways or only in the arrow direction (e.g. «comes to the tent»).",
  "z-loit": "Reports when a person stays inside longer than the time set (e.g. at the car).", "z-ign": "Persons and objects whose feet are inside are ignored (street, tree, neighbour's garden).",
  "z-only": "If at least one such zone exists, only what happens inside it counts (entrance, driveway).",
  "z-how": "A zone affects detection, recording, alarms and relays. The point that counts is the bottom middle of the detected object (the feet).",
  "z-priv": "The area is covered in black – in the live picture, recordings, photos and timelapse. It is never stored or sent (neighbour's tent, a path, somebody's window). Important for data protection."}});
const tt = s => (LANG === "de" && I18N.de[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && I18N.de[s]) || (I18N.en && I18N.en[s]) || s;
const cv = $("#cv"), g = cv.getContext("2d"), img = new Image();
let zones = [], sel = -1, drawing = null, drawMode = "ignore", drag = null;
const COL = {ignore: "245,154,74", only: "63,207,107", privacy: "169,139,255", line: "60,210,255", loiter: "255,220,60"};
const ZNAME = {only: "Only-here zone", privacy: "Privacy zone", ignore: "Ignore zone", line: "Line", loiter: "Dwell area"};
function arrow(z, on) {                 // line: the arrow shows in which direction crossing it counts
  const [a, b] = z.points.map(px), mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
  let nx = -(b[1] - a[1]), ny = b[0] - a[0]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
  const dirs = z.dir === "ab" ? [1] : z.dir === "ba" ? [-1] : [1, -1];
  g.strokeStyle = g.fillStyle = "rgb(" + COL.line + ")"; g.lineWidth = on ? 5 : 3;
  dirs.forEach(sg => { const ex = mx + sg * nx * 46, ey = my + sg * ny * 46;
    g.beginPath(); g.moveTo(mx, my); g.lineTo(ex, ey); g.stroke();
    g.beginPath(); g.moveTo(ex, ey); g.lineTo(ex - sg * nx * 16 + ny * 10 * sg, ey - sg * ny * 16 - nx * 10 * sg); g.lineTo(ex - sg * nx * 16 - ny * 10 * sg, ey - sg * ny * 16 + nx * 10 * sg); g.closePath(); g.fill(); });
}
function norm(e) { const r = cv.getBoundingClientRect(); return [Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), Math.min(1, Math.max(0, (e.clientY - r.top) / r.height))]; }
function px(p) { return [p[0] * cv.width, p[1] * cv.height]; }
function draw() {
  g.clearRect(0, 0, cv.width, cv.height);
  if (img.complete && img.naturalWidth) g.drawImage(img, 0, 0, cv.width, cv.height);
  else { g.fillStyle = "#0b0f14"; g.fillRect(0, 0, cv.width, cv.height); g.fillStyle = "#8a9bb0"; g.font = "28px sans-serif"; g.textAlign = "center"; g.fillText(t("no picture - is the camera running?"), cv.width / 2, cv.height / 2); g.textAlign = "left"; }
  const poly = (pts, mode, on, close) => {
    g.beginPath(); pts.forEach((p, i) => { const [x, y] = px(p); i ? g.lineTo(x, y) : g.moveTo(x, y); }); if (close) g.closePath();
    if (close) { g.fillStyle = mode === "privacy" ? "rgba(0,0,0,.82)" : "rgba(" + COL[mode] + "," + (on ? .34 : .22) + ")"; g.fill(); }
    g.strokeStyle = "rgb(" + COL[mode] + ")"; g.lineWidth = on ? 4 : 2.5; g.stroke();
    pts.forEach(p => { const [x, y] = px(p); g.beginPath(); g.arc(x, y, on || !close ? 8 : 5, 0, 7); g.fillStyle = "#fff"; g.fill(); g.strokeStyle = "rgb(" + COL[mode] + ")"; g.lineWidth = 2; g.stroke(); });
  };
  zones.forEach((z, i) => { poly(z.points, z.mode, i === sel, z.mode !== "line"); if (z.mode === "line") arrow(z, i === sel);
    const [x, y] = px(z.points[0]); g.fillStyle = "#fff"; g.font = "bold 24px sans-serif"; g.fillText(z.name, x + 12, y - 10); });
  if (drawing) poly(drawing, drawMode, true, false);
}
function hit(n) {
  const r = cv.getBoundingClientRect(), tol = 14 / r.width;
  for (let zi = zones.length - 1; zi >= 0; zi--) for (let pi = 0; pi < zones[zi].points.length; pi++) {
    const p = zones[zi].points[pi]; if (Math.hypot((p[0] - n[0]), (p[1] - n[1]) * r.height / r.width) < tol) return [zi, pi]; }
  return null;
}
function inside(n, pts) { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
  if ((pts[i][1] > n[1]) !== (pts[j][1] > n[1]) && n[0] < (pts[j][0] - pts[i][0]) * (n[1] - pts[i][1]) / (pts[j][1] - pts[i][1]) + pts[i][0]) c = !c; } return c; }
cv.addEventListener("pointerdown", e => {
  const n = norm(e);
  if (drawing) {
    if (drawMode === "line") { drawing.push(n); if (drawing.length >= 2) finish(); else draw(); return; }
    const r = cv.getBoundingClientRect();
    if (drawing.length >= 3 && Math.hypot(n[0] - drawing[0][0], (n[1] - drawing[0][1]) * r.height / r.width) < 14 / r.width) { finish(); return; }
    drawing.push(n); draw(); return;
  }
  const h = hit(n);
  if (h) { sel = h[0]; drag = h; cv.setPointerCapture(e.pointerId); renderList(); draw(); return; }
  const idx = zones.findIndex(z => z.mode !== "line" && inside(n, z.points)); sel = idx; renderList(); draw();
});
cv.addEventListener("pointermove", e => { if (drag) { zones[drag[0]].points[drag[1]] = norm(e); draw(); } });
cv.addEventListener("pointerup", () => { drag = null; });
cv.addEventListener("dblclick", () => { if (drawing && drawing.length >= 3) finish(); });
function startZone(mode) { drawMode = mode; drawing = []; sel = -1; $("#b-fin").hidden = false; setHint(); draw(); }
function finish() {
  if (drawing && drawing.length >= (drawMode === "line" ? 2 : 3)) { const z = {name: t(ZNAME[drawMode]) + " " + (zones.length + 1), mode: drawMode, points: drawing};
    if (drawMode === "line") z.dir = "both"; if (drawMode === "loiter") z.secs = 20; zones.push(z); sel = zones.length - 1; }
  drawing = null; $("#b-fin").hidden = true; setHint(); renderList(); draw();
}
function setHint() { $("#hint").textContent = drawing ? (drawMode === "line" ? tt("Click the start and the end of the line in the picture.") : tt("Click the corners of the area in the picture. Click the first point or press 'Finish shape' to close it.")) : tt("Drag a corner to move it. Select a zone in the list to edit it."); }
function renderList() {
  const L = $("#list"); L.textContent = "";
  if (!zones.length) L.appendChild(el("div", "mut", t("no zones"))).style.marginTop = "8px";
  zones.forEach((z, i) => {
    const r = el("div", "zrow" + (i === sel ? " sel" : "")); r.onclick = () => { sel = i; renderList(); draw(); };
    const nm = el("input"); nm.type = "text"; nm.value = z.name; nm.maxLength = 40; nm.oninput = () => { z.name = nm.value; draw(); }; nm.onclick = e => e.stopPropagation();
    const del = el("button", "sec", "✕"); del.title = t("Delete"); del.onclick = e => { e.stopPropagation(); zones.splice(i, 1); sel = -1; renderList(); draw(); };
    const md = el("select");
    (z.mode === "line" ? [["line", t("Line")]] : [["ignore", t("Ignore zone")], ["only", t("Only-here zone")], ["privacy", t("Privacy zone")], ["loiter", t("Dwell area")]])
      .forEach(([v, l]) => { const o = el("option", "", l); o.value = v; md.appendChild(o); });
    md.value = z.mode; md.onchange = () => { z.mode = md.value; if (z.mode === "loiter" && !z.secs) z.secs = 20; renderList(); draw(); }; md.onclick = e => e.stopPropagation();
    r.append(nm, del, md);
    if (z.mode === "line") { const d = el("select"); [["both", t("both directions")], ["ab", "→ " + t("only in the arrow direction")], ["ba", "← " + t("only against the arrow")]]
        .forEach(([v, l]) => { const o = el("option", "", l); o.value = v; d.appendChild(o); });
      d.value = z.dir || "both"; d.onchange = () => { z.dir = d.value; draw(); }; d.onclick = e => e.stopPropagation(); d.style.gridColumn = "1 / -1"; r.appendChild(d); }
    if (z.mode === "loiter") { const w = el("label", "mut", t("Alarm after (seconds)") + " "); const n = el("input"); n.type = "number"; n.min = 3; n.max = 600; n.value = z.secs || 20; n.style.width = "80px";
      n.onchange = () => { z.secs = Math.max(3, Math.min(600, +n.value || 20)); }; n.onclick = e => e.stopPropagation(); w.appendChild(n); w.style.gridColumn = "1 / -1"; r.appendChild(w); }
    L.appendChild(r);
  });
}
async function save() {
  const r = await post("/api/zones", {zones: zones, lang: LANG});
  $("#err").textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok) toast(t("Saved"));
}
function loadFrame() { img.onload = draw; img.onerror = draw; img.src = "/api/frame.jpg?" + Date.now(); }
(async () => {
  await initAppearance(); setHint();
  try { zones = (await (await fetch("/api/zones")).json()).zones || []; } catch (e) { zones = []; }
  renderList(); loadFrame(); setTimeout(loadFrame, 1500); draw();
})();
/*ALERTS*/
</script></body></html>
"""


DIARY_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Diary</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1500px;margin:0 auto}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 12px}
.chip{border:1px solid var(--line);background:var(--field);color:var(--txt);border-radius:999px;padding:6px 12px;cursor:pointer;font:inherit;font-size:13px}
.chip.on{background:var(--acc);border-color:var(--acc);color:#fff}
.dgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
@media(max-width:520px){.dgrid{grid-template-columns:1fr 1fr;gap:8px}}
.dcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column}
.dcard img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#000;cursor:zoom-in}
.dcard .meta{padding:8px 10px 4px}.dcard .meta b{font-size:15px}.dcard .meta .mut{font-size:12px}
.dcard .acts{display:flex;gap:6px;padding:4px 8px 8px;margin-top:auto}
.dcard .acts button{flex:1;padding:6px 0;font-size:15px}
.dcard .fav.on{color:#f5c542}
#big{position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:80;display:none;align-items:center;justify-content:center;flex-direction:column;padding:12px}
#big.on{display:flex}#big img{max-width:100%;max-height:82vh;border-radius:8px}
#big .cap{color:#fff;margin-top:10px;text-align:center}
#big .x{position:absolute;top:12px;right:12px;width:44px;height:44px;border-radius:50%;background:rgba(0,0,0,.6);color:#fff;border:1px solid rgba(255,255,255,.4);font-size:22px}
#rep{white-space:pre-wrap;line-height:1.5}
.empty{padding:30px 10px;text-align:center}
.dayhead{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.dayhead input{width:auto;padding:6px 8px}.dayhead button{padding:6px 12px;font-size:16px}
.dayhead h3{margin:0 8px 0 0;font-size:17px}
.dtiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px;margin:6px 0 10px}
.dline a{color:var(--acc);text-decoration:none}
.dtile{background:var(--field);border:1px solid var(--line);border-radius:12px;padding:8px 10px}
.dtile b{display:block;font-size:22px;line-height:1.1}.dtile span{font-size:12px;color:var(--mut)}
.dline{display:flex;flex-wrap:wrap;gap:6px 16px;margin:6px 0;font-size:14px}
.dchart{width:100%;height:auto;display:block;margin:8px 0 2px;background:var(--field);border:1px solid var(--line);border-radius:12px}
.dchart text{fill:var(--mut);font:11px system-ui,sans-serif}
.dleg{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;color:var(--mut);margin-bottom:8px}
.dleg i{display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle}
.dbest{display:flex;gap:8px;overflow-x:auto;margin:8px 0}.dbest figure{margin:0;flex:none;width:150px}
.dbest img{width:150px;height:112px;object-fit:cover;border-radius:10px;display:block;cursor:zoom-in;background:#000}
.dbest figcaption{font-size:12px;color:var(--mut);margin-top:3px}
#d-rep{white-space:pre-wrap;line-height:1.5;margin-top:6px}
.sdt{width:100%;border-collapse:collapse;margin:8px 0;font-size:13px}.sdt th,.sdt td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}.sdt th{color:var(--mut);font-weight:600}
.sdv{border-bottom:1px solid var(--line);padding:6px 0;font-size:14px}.sdv summary{cursor:pointer}.sdr{display:inline-block;min-width:92px;font-weight:700}.sdr.ok{color:var(--grn,#3fcf6b)}.sdr.miss{color:#ff6b6b}.sdr.none{color:var(--mut)}
.sdi{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;margin:6px 0 4px 8px;font-size:13px}
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
  <div class="card" id="daycard">
    <div class="dayhead"><h3 data-i18n="Day overview">Day overview</h3>
      <button class="sec" type="button" id="d-prev" aria-label="previous day">‹</button><input type="date" id="d-date"><button class="sec" type="button" id="d-next" aria-label="next day">›</button>
      <b id="d-title"></b></div>
    <div id="d-body" class="mut">…</div>
  </div>
  <details class="card" open id="repcard">
    <summary data-i18n="Night report">Night report</summary>
    <div id="rep" class="mut">…</div>
    <div class="btns"><button class="sec" onclick="sendReport()" data-i18n="Send now">Send now</button></div>
    <div class="mut" id="rep-note" style="margin-top:6px"></div>
  </details>
  <details class="card" id="simcard" hidden open>
    <summary>🎮 <span data-i18n="Simulator diary">Simulator diary</span> <span class="mut" id="sd-sum"></span></summary>
    <div class="mut" data-i18n="sd-note">sd-note</div>
    <div class="dtiles" id="sd-tiles"></div>
    <div id="sd-tables"></div>
    <div class="chips" id="sd-chips"></div>
    <div id="sd-list"></div>
  </details>
  <div class="card">
    <h3 style="margin:0 0 6px" data-i18n="Animal diary">Animal diary</h3>
    <div class="mut" id="d-note" data-i18n="d-note">d-note</div>
    <div class="chips" id="chips"></div>
    <div class="dgrid" id="grid"></div>
  </div>
</main>
<div id="big"><button class="x" onclick="closeBig()">&#x2715;</button><img id="big-img" alt=""><div class="cap" id="big-cap"></div></div>
<script>
/*COMMON*/
Object.assign(I18N.de, {"Sneezes": "Mal geniest"});
Object.assign(I18N.de, {"Day overview": "Tagesübersicht", "Persons": "Personen", "Animals": "Tiere", "Warm bodies": "Warme Körper", "Noises": "Geräusche", "Photos": "Fotos", "Sensor": "Fühler", "Temperature (sensor)": "Temperatur (Fühler)", "Temperature (weather)": "Temperatur (Wetter)", "Rain / humidity": "Regen / Feuchte", "Person": "Person", "Animal": "Tier", "Warm body": "Warmer Körper", "Noise": "Geräusch", "No measurements for this day yet.": "Für diesen Tag gibt es noch keine Messwerte.", "Weather from the internet: switch on under Notifications → Night report.": "Wetter aus dem Internet: einschalten unter Benachrichtigungen → Nachtbericht.", "No weather for this day": "Kein Wetter für diesen Tag", "no location": "kein Standort", "Day overview: weather from the internet (Open-Meteo; the location is sent there)": "Tagesübersicht: Wetter aus dem Internet (Open-Meteo; dafür wird der Standort dorthin geschickt)", "clear": "klar", "partly cloudy": "leicht bewölkt", "cloudy": "bewölkt", "fog": "Nebel", "drizzle": "Nieselregen", "rain": "Regen", "snow": "Schnee", "showers": "Schauer", "thunderstorm": "Gewitter", "new moon": "Neumond", "waxing crescent": "zunehmende Sichel", "first quarter": "erstes Viertel", "waxing gibbous": "zunehmender Mond", "full moon": "Vollmond", "waning gibbous": "abnehmender Mond", "last quarter": "letztes Viertel", "waning crescent": "abnehmende Sichel"});
Object.assign(I18N.de, {"recordings": "Aufnahmen", "Diary": "Tagebuch", "Night report": "Nachtbericht", "Send now": "Jetzt senden", "Animal diary": "Tier-Tagebuch",
  "All animals": "Alle Tiere", "Favourites": "Favoriten", "Delete this entry?": "Diesen Eintrag löschen?", "Share": "Teilen",
  "Download": "Herunterladen", "Favourite": "Favorit", "Delete": "Löschen", "sent": "gesendet", "not sent – notifications are not set up": "nicht gesendet – Benachrichtigungen sind nicht eingerichtet",
  "Last report": "Letzter Bericht", "So far tonight": "Bisher diese Nacht", "Last night": "Letzte Nacht",
  "No animals yet. As soon as the AI recognises an animal, its best picture appears here.": "Noch keine Tiere. Sobald die KI ein Tier erkennt, erscheint hier sein bestes Bild.",
  "d-note": "Das beste Bild jedes Tier-Besuchs (KI-Erkennung) – automatisch gesammelt. Tippen zum Vergrössern, ★ = behalten (wird nie automatisch gelöscht).",
  "The night report is off (Notifications → Night report).": "Der Nachtbericht ist aus (Benachrichtigungen → Nachtbericht)."});
Object.assign(I18N, {en: {"d-note": "The best picture of every animal visit (AI detection) – collected automatically. Tap to enlarge, ★ = keep (never deleted automatically)."}});
let filt = "", data = {items: [], labels: []}, cur = null;
const fmt = iso => { const d = new Date(iso); return d.toLocaleDateString(LOCALE(LANG), {day: "2-digit", month: "2-digit", year: "numeric"}) + " " + iso.slice(11, 16); };
async function load() {
  const q = new URLSearchParams({lang: LANG}); if (filt && filt !== "*fav") q.set("label", filt); if (filt === "*fav") q.set("fav", "1");
  try { data = await (await fetch("/api/diary?" + q)).json(); } catch (e) { return; }
  const C = $("#chips"); C.textContent = "";
  const chip = (k, lbl) => { const b = el("button", "chip" + (filt === k ? " on" : ""), lbl); b.onclick = () => { filt = k; load(); }; C.appendChild(b); };
  chip("", t("All animals") + " · " + data.total); chip("*fav", "★ " + t("Favourites"));
  data.labels.forEach(l => chip(l.key, l.label + " · " + l.count));
  const G = $("#grid"); G.textContent = "";
  if (!data.items.length) { G.appendChild(el("div", "mut empty", t("No animals yet. As soon as the AI recognises an animal, its best picture appears here."))); return; }
  data.items.forEach(e => {
    const c = el("div", "dcard"), im = el("img"); im.loading = "lazy"; im.src = "/diary/img/" + e.img + "?thumb=1"; im.alt = e.name;
    im.onclick = () => openBig(e);
    const m = el("div", "meta"); m.append(el("b", "", e.name), el("div", "mut", fmt(e.start) + (e.dur ? " · " + e.dur + " s" : "")));
    const a = el("div", "acts");
    const fv = el("button", "sec fav" + (e.fav ? " on" : ""), "★"); fv.title = t("Favourite");
    fv.onclick = async () => { const r = await post("/api/diary", {action: "fav", id: e.id, value: !e.fav}); if (r.ok) { e.fav = !e.fav; fv.classList.toggle("on", e.fav); } };
    const sh = el("button", "sec", "⤴"); sh.title = t("Share"); sh.onclick = () => share(e);
    const dl = el("a", "", ""); const db = el("button", "sec", "⤓"); db.title = t("Download");
    db.onclick = () => { dl.href = "/diary/img/" + e.img; dl.download = e.img; dl.click(); };
    const del = el("button", "sec", "🗑"); del.title = t("Delete");
    del.onclick = async () => { if (!confirm(t("Delete this entry?"))) return; const r = await post("/api/diary", {action: "delete", id: e.id}); if (r.ok) load(); };
    a.append(fv, sh, db, del); c.append(im, m, a); G.appendChild(c);
  });
}
async function share(e) {
  const title = e.name + " – " + fmt(e.start), url = "/diary/img/" + e.img + "?share=1&cap=" + encodeURIComponent(title);
  try {
    const b = await (await fetch(url)).blob(), f = new File([b], e.img, {type: "image/jpeg"});
    if (navigator.canShare && navigator.canShare({files: [f]})) { await navigator.share({files: [f], title: title}); return; }
  } catch (x) { if (x && x.name === "AbortError") return; }
  const a = el("a"); a.href = url; a.download = e.img; a.click();
}
function openBig(e) { cur = e; $("#big-img").src = "/diary/img/" + e.img; $("#big-cap").textContent = e.name + " · " + fmt(e.start); $("#big").classList.add("on"); }
function closeBig() { $("#big").classList.remove("on"); $("#big-img").src = ""; }
$("#big").addEventListener("click", e => { if (e.target.id === "big") closeBig(); });
addEventListener("keydown", e => { if (e.key === "Escape") closeBig(); });
async function loadReport() {
  let r; try { r = await (await fetch("/api/report?lang=" + LANG)).json(); } catch (e) { return; }
  const L = r.last;
  $("#rep").textContent = t(r.partial ? "So far tonight" : "Last night") + ": " + r.preview.text
    + (L && L.text ? "\n\n" + t("Last report") + " (" + fmt(L.t) + ", " + (L.sent ? t("sent") : t("not sent – notifications are not set up")) + "):\n" + L.text : "");
  $("#rep-note").textContent = r.on ? "" : t("The night report is off (Notifications → Night report).");
}
async function sendReport() {
  const r = await post("/api/report/send", {lang: LANG});
  toast(r.ok ? t("sent") : t("not sent – notifications are not set up")); loadReport();
}
// ---- day overview: what happened, climate curve, weather, sun, moon, place ----
const dIso = d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
let DAY = dIso(new Date());
function dShift(n) { const d = new Date(DAY + "T12:00:00"); d.setDate(d.getDate() + n); if (dIso(d) > dIso(new Date())) return; DAY = dIso(d); loadDay(); }
async function loadDay(refresh) {
  $("#d-date").value = DAY; $("#d-date").max = dIso(new Date());
  $("#d-next").disabled = DAY >= dIso(new Date());
  let j; try { j = await (await fetch("/api/day?d=" + DAY + "&lang=" + LANG + (refresh ? "&refresh=1" : ""))).json(); } catch (e) { return; }
  renderDay(j);
}
function dChart(j) {
  const W = Math.max(330, Math.min(760, ($("#d-body").clientWidth || 640))), H = W < 480 ? 210 : 190, L = 34, R = 34, T = 12, B = 34, PW = W - L - R, PH = H - T - B;
  const xm = m => L + PW * m / 1440, mins = hhmm => (+hhmm.slice(0, 2)) * 60 + (+hhmm.slice(3, 5));
  const cl = (j.climate || []).filter(r => r[1] != null), wh = j.weather ? j.weather.hourly : {};
  const wt = Object.keys(wh).sort().map(h => [(+h) * 60 + 30, wh[h][0], wh[h][1]]).filter(x => x[1] != null);
  const temps = cl.map(r => r[1]).concat(wt.map(x => x[1]));
  if (!temps.length && !(j.events || []).length) return null;
  let tmin = temps.length ? Math.floor(Math.min(...temps) - 1) : 0, tmax = temps.length ? Math.ceil(Math.max(...temps) + 1) : 20;
  if (tmax - tmin < 6) { tmin -= 3; tmax += 3; }
  const yt = v => T + PH - PH * (v - tmin) / (tmax - tmin), yh = v => T + PH - PH * v / 100;
  const NS = "http://www.w3.org/2000/svg", svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("class", "dchart");
  const mk = (n, a, txt) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; svg.appendChild(e); return e; };
  for (let h = 0; h <= 24; h += 6) { mk("line", {x1: xm(h * 60), x2: xm(h * 60), y1: T, y2: T + PH, stroke: "currentColor", "stroke-opacity": .12});
    mk("text", {x: xm(h * 60), y: H - 18, "text-anchor": "middle"}, h + ":00"); }
  [tmin, Math.round((tmin + tmax) / 2), tmax].forEach(v => { mk("line", {x1: L, x2: L + PW, y1: yt(v), y2: yt(v), stroke: "currentColor", "stroke-opacity": .08});
    mk("text", {x: L - 4, y: yt(v) + 4, "text-anchor": "end"}, v + "°"); });
  if (j.sun && j.sun.rise) { const a = mins(j.sun.rise), b = mins(j.sun.set);
    mk("rect", {x: L, y: T, width: xm(a) - L, height: PH, fill: "#3a5ccc", "fill-opacity": .10}); mk("rect", {x: xm(b), y: T, width: L + PW - xm(b), height: PH, fill: "#3a5ccc", "fill-opacity": .10}); }
  const rmax = Math.max(2, ...wt.map(x => x[2] || 0));
  wt.forEach(x => { if (x[2] > 0) { const h = PH * 0.45 * x[2] / rmax; mk("rect", {x: xm(x[0] - 25), y: T + PH - h, width: Math.max(2, xm(50) - xm(0)), height: h, fill: "#58a6ff", "fill-opacity": .45}); } });
  const path = (pts, y) => pts.map((p, i) => (i ? "L" : "M") + xm(p[0]).toFixed(1) + " " + y(p[1]).toFixed(1)).join(" ");
  if (wt.length > 1) mk("path", {d: path(wt.map(x => [x[0], x[1]]), yt), fill: "none", stroke: "#8b9bb0", "stroke-width": 1.5, "stroke-dasharray": "4 3"});
  const hum = (j.climate || []).filter(r => r[2] != null).map(r => [mins(r[0]), r[2]]);
  if (hum.length > 1) { mk("path", {d: path(hum, yh), fill: "none", stroke: "#58a6ff", "stroke-width": 1.6});
    [0, 50, 100].forEach(v => mk("text", {x: L + PW + 4, y: yh(v) + 4}, v + "%")); }
  if (cl.length > 1) mk("path", {d: path(cl.map(r => [mins(r[0]), r[1]]), yt), fill: "none", stroke: "#f0883e", "stroke-width": 2.2});
  const col = {person: "#ff3b3b", animal: "#f5c542", warm: "#ff7ab6", noise: "#bc8cff", object: "#8b9bb0"};
  (j.events || []).forEach(e => { const c = mk("circle", {cx: xm(mins(e.t)), cy: H - 6, r: 3.5, fill: col[e.kind] || "#8b9bb0"}); const ti = document.createElementNS(NS, "title"); ti.textContent = e.t + " " + e.label; c.appendChild(ti); });
  return svg;
}
function renderDay(j) {
  const b = $("#d-body"); b.textContent = ""; b.className = "";
  if (!j || j.error) { b.textContent = "–"; return; }
  const d = new Date(j.day + "T12:00:00");
  $("#d-title").textContent = d.toLocaleDateString(LOCALE(LANG), {weekday: "long", day: "numeric", month: "long", year: "numeric"});
  const c = j.counts, tl = el("div", "dtiles");
  const E = window.EVI || {};
  [[E.person || "🚶", c.persons, "Persons"], [E.animal || "🦊", c.animals, "Animals"], [E.warm || "🔥", c.warm, "Warm bodies"], [E.noise || "🔊", c.noise, "Noises"],
   [E.rec || "🎬", c.recordings + (c.alarm_recordings ? " (" + c.alarm_recordings + " 🚨)" : ""), "recordings"], ["📷", c.photos, "Photos"]].concat(c.sneezes ? [["🤧", c.sneezes, "Sneezes"]] : []).forEach(([i, n, k]) => {
    const t_ = el("div", "dtile"), lb = t(k); t_.append(el("b", "", i + " " + n), el("span", "", lb.charAt(0).toUpperCase() + lb.slice(1))); tl.appendChild(t_); });
  b.appendChild(tl);
  const ln = el("div", "dline"), w = j.weather, cs = j.climate_sum || {};
  if (cs.tmin != null) ln.append(el("span", "", "🌡 " + t("Sensor") + ": " + cs.tmin.toFixed(1) + " … " + cs.tmax.toFixed(1) + " °C" + (cs.hmin != null ? " · 💧 " + cs.hmin + "–" + cs.hmax + " %" : "") + (cs.pmin != null ? " · " + Math.round(cs.pmin) + "–" + Math.round(cs.pmax) + " hPa" : "")));
  if (w) ln.append(el("span", "", w.icon + " " + w.text + (w.tmax != null ? " · " + Math.round(w.tmin) + "° / " + Math.round(w.tmax) + "°" : "") + (w.rain != null ? " · ☔ " + w.rain.toFixed(1) + " mm" : "") + (w.wind != null ? " · 💨 " + Math.round(w.wind) + " km/h" : "")));
  if (j.sun) ln.append(el("span", "", j.sun.rise ? "🌅 " + j.sun.rise + " · 🌇 " + j.sun.set + " (" + j.sun.len + ")" : "☀ –"));
  if (j.moon) ln.append(el("span", "", j.moon.icon + " " + j.moon.name));
  if (j.gps) { const a = el("a", "", "📍 " + j.gps[0].toFixed(3) + ", " + j.gps[1].toFixed(3)); a.href = "https://www.openstreetmap.org/?mlat=" + j.gps[0] + "&mlon=" + j.gps[1] + "#map=13/" + j.gps[0] + "/" + j.gps[1]; a.target = "_blank"; a.rel = "noopener"; ln.append(a); }
  b.appendChild(ln);
  const ch = dChart(j);
  if (ch) { b.appendChild(ch);
    const lg = el("div", "dleg"); const li = (col, k) => { const s_ = el("span"); const i_ = el("i"); i_.style.background = col; s_.append(i_, t(k)); lg.appendChild(s_); };
    if ((j.climate || []).some(r => r[1] != null)) li("#f0883e", "Temperature (sensor)"); if (w && Object.keys(w.hourly || {}).length) { li("#8b9bb0", "Temperature (weather)"); li("#58a6ff", "Rain / humidity"); }
    li("#ff3b3b", "Person"); li("#f5c542", "Animal"); li("#ff7ab6", "Warm body"); li("#bc8cff", "Noise"); b.appendChild(lg);
  } else b.appendChild(el("div", "mut", t("No measurements for this day yet.")));
  if (!j.weather_on) b.appendChild(el("div", "mut", "☁ " + t("Weather from the internet: switch on under Notifications → Night report.")));
  else if (!w) { const x = el("div", "mut", "☁ " + t("No weather for this day") + (j.weather_status && j.weather_status !== "ok" ? " (" + t(j.weather_status) + ")" : "") + " ");
    const rb = el("button", "sec", "↻"); rb.type = "button"; rb.onclick = () => loadDay(true); x.appendChild(rb); b.appendChild(x); }
  if ((j.animals || []).length) { const a = el("div", "dline"); j.animals.forEach(x => a.appendChild(el("span", "", x.label + " ×" + x.count))); b.appendChild(a); }
  if ((j.best || []).length) { const bb = el("div", "dbest"); j.best.forEach(x => { const f = el("figure"), im = el("img"); im.src = "/diary/img/" + x.img + "?thumb=1"; im.alt = x.label; im.loading = "lazy";
      im.onclick = () => { $("#big-img").src = "/diary/img/" + x.img; $("#big-cap").textContent = x.label + " · " + x.t; $("#big").classList.add("on"); };
      f.append(im, el("figcaption", "", x.label + " · " + x.t)); bb.appendChild(f); }); b.appendChild(bb); }
  if (j.report) { b.appendChild(el("div", "mut", "🌙 " + t("Night report"))); b.appendChild(el("div", "", j.report)).id = "d-rep"; }
}
$("#d-prev").onclick = () => dShift(-1); $("#d-next").onclick = () => dShift(1);
$("#d-date").onchange = e => { if (e.target.value) { DAY = e.target.value; loadDay(); } };
// ---- 2.96.1: the diary of the simulator - every visit in the simulated world, with what MoveEye made of it ----
const SDK = {person: "🚶", car: "🚗", fox: "🦊", deer: "🦌", boar: "🐗", cat: "🐈", dog: "🐕", badger: "🦡", hare: "🐇", hedgehog: "🦔", wolf: "🐺", marten: "🦦", squirrel: "🐿",
  cow: "🐄", sheep: "🐑", horse: "🐎", chamois: "🐐", ibex: "🐐", lynx: "🐆"};
let SD = {items: [], filt: "all", day: ""};
async function sdLoad() {
  let r; try { r = await (await fetch("/api/sim_diary?day=" + DAY, {cache: "no-store"})).json(); } catch (e) { return; }
  const card = $("#simcard"); card.hidden = !Object.keys(r.days || {}).length; if (card.hidden) return;
  SD.items = (r.items || []).slice().reverse(); SD.day = DAY; sdPaint();
}
function sdRes(v) { return v.detected ? "ok" : (v.vis_s >= 2 ? "miss" : "none"); }
function sdPaint() {
  const I = SD.items, pct = (a, b) => b ? Math.round(100 * a / b) + " %" : "–";
  const vis = I.filter(v => v.vis_s >= 2 && v.kind !== "car"), det = vis.filter(v => v.detected), times = det.map(v => v.detect_s).filter(x => x >= 0);
  const avg = times.length ? (times.reduce((a, b) => a + b, 0) / times.length).toFixed(1) + " s" : "–";
  $("#sd-sum").textContent = "· " + I.length + " " + t("visits");
  const T = $("#sd-tiles"); T.textContent = "";
  [[I.length, t("visits")], [pct(det.length, vis.length), t("recognised")], [avg, t("until recognised")], [vis.length - det.length, t("missed")], [I.filter(v => v.vis_s < 2).length, t("never well in the picture")]]
    .forEach(([n, l]) => { const d = el("div", "dtile"); d.append(el("b", "", String(n)), el("span", "", l)); T.appendChild(d); });
  const tab = (title, keyf, namef) => { const g = {}; vis.forEach(v => { const k = keyf(v); (g[k] = g[k] || []).push(v); });
    const ks = Object.keys(g); if (!ks.length) return null; const tb = document.createElement("table"); tb.className = "sdt";
    tb.innerHTML = "<tr><th>" + title + "</th><th>" + t("visits") + "</th><th>" + t("recognised") + "</th><th>Ø s</th></tr>" + ks.sort((a, b) => g[b].length - g[a].length).map(k => {
      const d = g[k].filter(v => v.detected), ts = d.map(v => v.detect_s).filter(x => x >= 0);
      return "<tr><td>" + namef(k) + "</td><td>" + g[k].length + "</td><td>" + pct(d.length, g[k].length) + "</td><td>" + (ts.length ? (ts.reduce((a, b) => a + b, 0) / ts.length).toFixed(1) : "–") + "</td></tr>"; }).join("");
    return tb; };
  const TB = $("#sd-tables"); TB.textContent = "";
  [tab(t("Kind"), v => v.kind, k => (SDK[k] || "•") + " " + t(k)), tab(t("Light"), v => v.dark ? "n" : "d", k => k === "n" ? "🌙 " + t("night") : "☀️ " + t("day")),
   tab(t("Posture"), v => String(v.post || 0), k => ["🧍 " + t("standing"), "🧎 " + t("crouching"), "🐍 " + t("crawling")][+k] || k)].forEach(x => { if (x) TB.appendChild(x); });
  const C = $("#sd-chips"); C.textContent = "";
  [["all", t("All")], ["person", t("Persons")], ["animal", t("Animals")], ["miss", t("missed")]].forEach(([k, n]) => { const b = el("button", "chip" + (SD.filt === k ? " on" : ""), n); b.type = "button";
    b.onclick = () => { SD.filt = k; sdPaint(); }; C.appendChild(b); });
  const L = $("#sd-list"); L.textContent = "";
  const F = I.filter(v => SD.filt === "all" || (SD.filt === "person" && v.kind === "person") || (SD.filt === "animal" && v.kind !== "person" && v.kind !== "car") || (SD.filt === "miss" && sdRes(v) === "miss"));
  if (!F.length) L.appendChild(el("div", "mut", t("No visits on this day.")));
  F.slice(0, 150).forEach(v => { const d = document.createElement("details"); d.className = "sdv"; const sm = document.createElement("summary"); const r = sdRes(v);
    const tm = new Date(v.t_in * 1000).toLocaleTimeString(LANG === "en" ? "en-GB" : "de-CH", {hour: "2-digit", minute: "2-digit"});
    sm.innerHTML = '<span class="sdr ' + r + '">' + (r === "ok" ? "✓ " + (v.detect_s >= 0 ? v.detect_s + " s" : "") : r === "miss" ? "✗ " + t("missed") : "– " + t("not seen")) + "</span> " + tm + " · " + (SDK[v.kind] || "•") + " " + esc(t(v.kind)) + (v.var ? " (" + esc(t(v.var)) + ")" : "") + " · " + (v.dark ? "🌙" : "☀️");
    const info = [[t("Scene"), v.scene], [t("Weather"), t(v.weather)], [t("closest"), v.min_d + " m"], [t("well in the picture"), v.vis_s + " s"], [t("Posture"), ["standing", "crouching", "crawling"].map(t)[v.post || 0]],
      [t("scared away"), v.fled ? "✓" : "–"], [t("Duration"), Math.round((v.t_out - v.t_in)) + " s"], ["MoveEye", v.mw ? (v.mw_version || "✓") : t("not connected")]];
    const g = el("div", "sdi"); info.forEach(([a, b]) => g.append(el("span", "mut", a), el("span", "", String(b)))); d.append(sm, g); L.appendChild(d); });
}
function esc(x) { return String(x).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
const _ld = loadDay; loadDay = async function (r) { await _ld(r); sdLoad(); };
setInterval(() => { if (!document.hidden && $("#simcard") && !$("#simcard").hidden) sdLoad(); }, 30000);
Object.assign(I18N.de, {"Simulator diary": "Simulator-Tagebuch", "sd-note": "Jeder Besuch in der Simulation (Menschen, Tiere, Autos) – und was MoveEye daraus gemacht hat. «Verpasst» = mindestens 2 s gut im Bild der Kopfkamera, aber nicht erkannt.",
  "visits": "Besuche", "recognised": "erkannt", "until recognised": "bis erkannt", "missed": "verpasst", "never well in the picture": "nie gut im Bild", "Kind": "Art", "Light": "Licht", "night": "Nacht", "day": "Tag",
  "Posture": "Haltung", "standing": "stehend", "crouching": "geduckt", "crawling": "kriechend", "All": "Alle", "Persons": "Personen", "Animals": "Tiere", "No visits on this day.": "Keine Besuche an diesem Tag.",
  "not seen": "nicht im Bild", "Scene": "Szene", "Weather": "Wetter", "closest": "am nächsten", "well in the picture": "gut im Bild", "scared away": "verscheucht", "Duration": "Dauer", "not connected": "nicht verbunden",
  "person": "Person", "car": "Auto", "fox": "Fuchs", "deer": "Reh", "boar": "Wildschwein", "cat": "Katze", "dog": "Hund", "badger": "Dachs", "hare": "Hase", "hedgehog": "Igel", "wolf": "Wolf", "marten": "Marder",
  "squirrel": "Eichhörnchen", "cow": "Kuh", "sheep": "Schaf", "horse": "Pferd", "chamois": "Gämse", "ibex": "Steinbock", "lynx": "Luchs", "child": "Kind", "jogger": "Jogger", "burglar": "Einbrecher", "thief": "Dieb",
  "clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee", "storm": "Sturm"});
Object.assign(I18N.en || (I18N.en = {}), {"sd-note": "Every visit in the simulation (persons, animals, cars) – and what MoveEye made of it. «Missed» = at least 2 s well in the picture of the head camera, but not recognised."});
(async () => { await initAppearance(); loadDay(); load(); loadReport(); })();
/*ALERTS*/
</script></body></html>
"""


GUEST_KEYS = ("Guest view · watch only · tap the picture = full screen", "access expired", "Armed", "Disarmed", "person in view", "quiet", "until")
GUEST_PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<title>MoveEye – Live</title>
<style>
html,body{margin:0;background:#000;color:#e6edf3;font:15px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;height:100%}
.top{display:flex;align-items:center;gap:10px;padding:10px 14px;padding-top:max(10px,env(safe-area-inset-top))}
.top b{font-size:17px}.dot{width:10px;height:10px;border-radius:50%;background:#3fb950;display:inline-block}
.st{margin-left:auto;font-size:13px;color:#8b9bb0;text-align:right}
.wrap{position:relative;display:flex;align-items:center;justify-content:center;min-height:180px}
#v{width:100%;max-height:calc(100dvh - 110px);object-fit:contain;display:block}
.vwrap.vlost::after{content:"↻";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#8b9bb0;font-size:34px}
.foot{padding:8px 14px;font-size:12px;color:#8b9bb0}
.big .top,.big .foot{display:none}.big #v{max-height:100dvh;height:100dvh}
</style></head><body>
<div class="top"><span class="dot"></span><b>MoveEye</b><span class="st" id="st">…</span></div>
<div class="wrap vwrap"><img id="v" alt="" src="__BASE__/video"></div>
<div class="foot" id="ft"></div>
<script>
const GL = (navigator.language || "").toLowerCase().slice(0, 2), GT = /*GT*/{};
const de = GL === "de", g_ = (k, d, e) => (GT[GL] && GT[GL][k]) || (de ? d : e);
const $ = s => document.querySelector(s);
/*KEEP*/
keepStream($("#v"));
$("#v").addEventListener("click", () => document.body.classList.toggle("big"));
$("#ft").textContent = g_("Guest view · watch only · tap the picture = full screen", "Gast-Ansicht · nur zuschauen · Tippen aufs Bild = Vollbild", "Guest view · watch only · tap the picture = full screen");
async function st() {
  try {
    const r = await fetch("__BASE__/state", {cache: "no-store"});
    if (r.status === 403 || r.status === 404) { $("#st").textContent = g_("access expired", "Zugang abgelaufen", "access expired"); $("#v").remove(); return; }
    const j = await r.json();
    $("#st").textContent = (j.armed ? g_("Armed", "Scharf", "Armed") : g_("Disarmed", "Unscharf", "Disarmed")) + " · " + (j.persons ? g_("person in view", "Person im Bild", "person in view") : g_("quiet", "ruhig", "quiet"))
      + (j.until ? " · " + g_("until", "bis", "until") + " " + new Date(j.until * 1000).toLocaleString(({de: "de-CH", fr: "fr-CH", it: "it-CH"})[GL] || "en-GB", {weekday: "short", hour: "2-digit", minute: "2-digit"}) : "");
  } catch (e) {}
  setTimeout(st, 3000);
}
st();
</script></body></html>
"""


LOG_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Event log</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1400px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:16px;align-items:start}
@media(max-width:900px){main{grid-template-columns:1fr}}
.lf{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.lf input{flex:1;min-width:140px}.lf select{min-width:120px}
#lines{font:12.5px/1.55 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
#lines .ln{padding:3px 0;border-bottom:1px solid var(--line)}
#lines .tm{color:var(--mut)}#lines .k{display:inline-block;min-width:62px;font-weight:700;margin:0 6px}
.k-person{color:var(--red)}.k-sys{color:var(--blu)}.k-web{color:var(--pur)}.k-rec{color:var(--org)}.k-status{color:var(--grn)}.k-servo,.k-patrol,.k-relay{color:var(--yel)}
#arch a{display:flex;justify-content:space-between;gap:8px;padding:7px 0;border-bottom:1px solid var(--line);color:var(--txt);text-decoration:none}
#arch a:hover{color:var(--acc2)}#arch .on{color:var(--acc2);font-weight:700}
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
    <div class="btns" style="margin:0 0 10px"><button type="button" class="sec" onclick="history.length > 1 && document.referrer ? history.back() : (location.href = '/')"
      data-i18n="← Back to the live picture">← Back to the live picture</button></div>
    <h3 style="margin:0 0 8px" id="ttl"></h3>
    <div class="lf">
      <select id="kind"></select>
      <input type="text" id="q" data-ph="Search …" placeholder="Search …">
      <select id="lim"><option value="300">300</option><option value="1000">1000</option><option value="5000">5000</option></select>
      <button class="sec" id="dl" data-i18n="⬇ Download">⬇ Download</button>
    </div>
    <div class="mut" id="cnt"></div>
    <div id="lines"></div>
  </section>
  <aside class="card" style="margin:0">
    <h3 style="margin:0 0 6px" data-i18n="Archive">Archive</h3>
    <div class="mut" id="arch-note"></div>
    <div id="arch"></div>
  </aside>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"← Back to the live picture": "← Zurück zum Live-Bild", "Event log": "Ereignisprotokoll", "Archive": "Archiv", "Today (running)": "Heute (laufend)", "All kinds": "Alle Arten",
  "Search …": "Suchen …", "⬇ Download": "⬇ Herunterladen", "Important only": "Nur Wichtiges", "entries": "Einträge", "no entries": "keine Einträge",
  "Each day is saved as its own file and kept for": "Jeder Tag wird als eigene Datei gespeichert und aufbewahrt:", "days": "Tage",
  "person": "Person", "sys": "System", "web": "Web", "rec": "Aufnahme", "status": "Status", "servo": "Kamera", "patrol": "Patrouille",
  "sched": "Zeitplan", "auto": "Auto", "ai": "KI", "wind": "Wind", "rain": "Regen", "relay": "Relais", "car": "Fahrzeug"});
const KINDS = ["person", "status", "sys", "web", "rec", "servo", "patrol", "sched", "auto", "ai", "relay", "rain", "wind", "car"];
let file = "", timer = null;
const fmtS = b => b < 1024 ? b + " B" : b < 1048576 ? (b / 1024).toFixed(0) + " KB" : (b / 1048576).toFixed(1) + " MB";
async function load() {
  const p = new URLSearchParams({limit: $("#lim").value, kind: $("#kind").value, q: $("#q").value}); if (file) p.set("file", file);
  let j; try { j = await (await fetch("/api/log?" + p)).json(); } catch (e) { return; }
  const L = $("#lines"); L.textContent = "";
  j.lines.forEach(x => {
    const d = el("div", "ln"); d.append(el("span", "tm", (file ? x.d.slice(8) + "." + x.d.slice(5, 7) + ". " : "") + x.t), el("span", "k k-" + x.kind, t(x.kind)), document.createTextNode(x.text));
    L.appendChild(d);
  });
  $("#cnt").textContent = j.lines.length ? j.lines.length + " " + t("entries") : t("no entries");
  $("#ttl").textContent = t("Event log") + " · " + (file ? file.slice(12, 22) : t("Today (running)"));
  const A = $("#arch"); A.textContent = "";
  const add = (name, label, size) => { const a = el("a"); a.href = "#"; a.append(el("span", (file === name || (!file && !name)) ? "on" : "", label), el("span", "mut", fmtS(size)));
    a.onclick = e => { e.preventDefault(); file = name; load(); scrollTo(0, 0); }; A.appendChild(a); };
  add("", t("Today (running)"), j.archive.current.size);
  j.archive.files.forEach(f => add(f.name, f.day.slice(8) + "." + f.day.slice(5, 7) + "." + f.day.slice(0, 4) + (/_\d+\.log/.test(f.name) ? " (2)" : ""), f.size));
  $("#arch-note").textContent = t("Each day is saved as its own file and kept for") + " " + j.archive.keep_days + " " + t("days") + ".";
}
(async () => {
  await initAppearance();
  const k = $("#kind"); const a = el("option", "", t("All kinds")); a.value = ""; k.appendChild(a);
  const im = el("option", "", "★ " + t("Important only")); im.value = "important"; k.appendChild(im);
  KINDS.forEach(x => { const o = el("option", "", t(x)); o.value = x; k.appendChild(o); });
  $("#q").placeholder = t("Search …");
  k.onchange = load; $("#lim").onchange = load;
  $("#q").oninput = () => { clearTimeout(timer); timer = setTimeout(load, 300); };
  $("#dl").onclick = () => { location.href = "/api/log/file/" + (file || "motionwatch.log"); };
  load(); setInterval(() => { if (!file && !document.hidden) load(); }, 10000);
})();
/*ALERTS*/
</script></body></html>
"""


