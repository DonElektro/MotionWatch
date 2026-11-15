#@ MoveEye – Teil 639zzzzk_blinki_seite: «Blinki fragen» – die Web-Seite /blinki (ein Literal: werkzeuge/bauen.py legt es in die Zusatz-ZIP; ohne ZIP zeigt /blinki «Zusatzdaten fehlen»). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
BLINKI_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Blinki</title>
<style>
/*BASECSS*/
main{padding:16px 16px 120px;max-width:760px;margin:0 auto}
.bk-back{display:inline-flex;align-items:center;min-height:40px;text-decoration:none;color:var(--acc);font-weight:600}
.bkp-hero{display:flex;gap:14px;align-items:center;margin:4px 0 12px}
.bkp-hero .bk{width:64px;height:70px;flex:none}.bkp-hero h2{margin:0;font-size:22px}
.bkp-sub{color:var(--mut);font-size:14px;margin:2px 0 6px}
.bkp-chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:13px;color:var(--mut);max-width:100%;overflow-wrap:anywhere}
.bkp-chip i{width:9px;height:9px;border-radius:50%;background:var(--mut);flex:none;font-style:normal}
.bkp-chip.ok i{background:var(--grn)}.bkp-chip.held i{background:var(--yel)}.bkp-chip.no i{background:var(--red)}.bkp-chip.cloud i{background:var(--blu)}
.bkp-modes{display:flex;gap:8px;overflow-x:auto;padding:2px 2px 8px;margin:0 -2px 6px;scrollbar-width:none}.bkp-modes::-webkit-scrollbar{display:none}
.bkp-modes button{flex:none;min-height:42px;border-radius:999px;padding:0 14px;font:inherit;font-size:15px;white-space:nowrap}
.bkp-modes button.sel{outline:2px solid var(--acc);outline-offset:-2px;font-weight:700}
.bkp-card{border:1px solid var(--line);border-radius:16px;background:var(--panel);padding:14px;margin:0 0 12px}
.bkp-card h3{margin:0 0 6px;font-size:16px}.bkp-card p{margin:4px 0;color:var(--mut);font-size:14px}
.bkp-card .row-b{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.bkp-card .row-b button{min-height:44px}
.bkp-bar{height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:8px}.bkp-bar b{display:block;height:100%;width:0;background:var(--acc);transition:width .4s}
.bkp-chat{display:flex;flex-direction:column;gap:12px}
.bkp-me{align-self:flex-end;max-width:86%;background:var(--acc);color:#fff;border-radius:18px 18px 6px 18px;padding:10px 14px;font-size:16px;overflow-wrap:anywhere;white-space:pre-wrap}
.bkp-me small{display:block;opacity:.75;font-size:12px;margin-top:4px}
.bkp-it{display:flex;gap:8px;align-items:flex-start}.bkp-it>.bk{width:40px;height:44px;flex:none;margin-top:2px}
.bkp-say{flex:1;min-width:0;border:1px solid var(--line);background:var(--panel);border-radius:6px 18px 18px 18px;padding:10px 14px;font-size:16px;line-height:1.5;overflow-wrap:anywhere}
.bkp-say p{margin:0 0 8px}.bkp-say p:last-child{margin-bottom:0}.bkp-say ol,.bkp-say ul{margin:0 0 8px;padding-left:22px}
.bkp-say .cur::after{content:"▍";animation:bkcur 1s steps(2) infinite;color:var(--acc)}@keyframes bkcur{50%{opacity:0}}
.bkp-wait{color:var(--mut);font-size:14px}.bkp-wait.warn{color:var(--yel)}.bkp-err{color:var(--red);font-size:14px;margin-top:6px}
.bkp-open{display:flex;flex-direction:column;align-items:flex-start;gap:8px;margin-top:10px}
.bkp-open a{display:inline-flex;align-items:center;min-height:42px;padding:6px 14px;border-radius:12px;text-decoration:none;font-weight:600;background:var(--btn2);color:var(--txt);max-width:100%;overflow-wrap:anywhere}
.bkp-open a:first-child{background:var(--acc);color:#fff}
.bkp-fix{margin-top:10px;border:1px dashed var(--yel);border-radius:12px;padding:8px 10px;font-size:14px}.bkp-fix button{margin-top:6px;min-height:40px}
.bkp-src{border-top:1px dashed var(--line);margin-top:10px;padding-top:8px;font-size:13px;color:var(--mut)}
.bkp-act{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.bkp-act button{min-height:36px;font-size:14px;padding:0 10px}
.bkp-ex{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 4px}.bkp-ex button{min-height:40px;font-size:14px;text-align:left;white-space:normal}
.bkp-in{position:fixed;left:0;right:0;bottom:0;z-index:20;background:var(--hdr);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-top:1px solid var(--line);
  padding:10px 16px calc(10px + env(safe-area-inset-bottom))}
.bkp-in form{max-width:760px;margin:0 auto;display:flex;gap:8px;align-items:flex-end}
.bkp-in textarea{flex:1;min-width:0;resize:none;font:inherit;font-size:16px;min-height:48px;max-height:140px;border-radius:24px;padding:12px 16px;background:var(--field);color:var(--txt);border:1px solid var(--line)}
.bkp-in button{flex:none;width:48px;height:48px;border-radius:50%;font-size:20px;padding:0;display:grid;place-items:center}
.bkp-in #bk-mic{display:none}.bkp-in #bk-mic.on{display:grid}.bkp-in #bk-mic.rec{background:var(--red);color:#fff;animation:bkpulse 1s infinite}
@keyframes bkpulse{50%{box-shadow:0 0 0 8px rgba(255,77,77,.25)}}
.bkp-opts{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}.bkp-opts select{min-height:40px;font:inherit;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:4px 8px;max-width:100%}
.bkp-opts .seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}.bkp-opts .seg button{min-height:40px;border:0;border-radius:0;padding:0 12px;font:inherit;font-size:14px}
.bkp-opts .seg button.sel{background:var(--acc);color:#fff;font-weight:700}.bkp-opts label{display:flex;gap:8px;align-items:center;font-size:14px}
.bkp-quiz{margin:10px 0 0;padding-left:22px}.bkp-quiz li{margin:0 0 6px}.bkp-quiz small{display:block;color:var(--mut)}
.bkp-hint{max-width:760px;margin:0 auto 6px;font-size:13px;color:var(--mut)}.bkp-hint:empty{display:none}
details.bkp-card>summary{cursor:pointer;font-weight:700;min-height:36px;display:flex;align-items:center}
.bkp-set{display:flex;flex-direction:column;gap:10px;margin-top:8px}.bkp-set label{display:flex;gap:10px;align-items:center;font-size:15px}
.bkp-set select,.bkp-set input[type=text],.bkp-set input[type=password]{min-height:40px;font:inherit;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:4px 8px;width:100%}
.bkp-set .mut{font-size:13px;color:var(--mut)}
@media(min-width:900px){main{padding-top:22px}.bkp-me,.bkp-say{font-size:15px}}
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
  <a class="bk-back" href="/more" id="bk-back">‹ More</a>
  <div class="bkp-hero"><span id="bk-face"></span><div style="min-width:0"><h2 id="bk-title">Ask Blinki</h2><div class="bkp-sub" id="bk-sub"></div>
    <span class="bkp-chip" id="bk-chip"><i></i><span id="bk-chip-t">…</span></span></div></div>
  <div class="bkp-modes" id="bk-modes" role="tablist"></div>
  <div class="bkp-opts" id="bk-opts" hidden></div>
  <section class="bkp-card" id="bk-setup" hidden><h3 id="bk-su-t"></h3><p id="bk-su-p"></p><p id="bk-su-m"></p>
    <div class="bkp-bar" id="bk-su-bar" hidden><b></b></div><p id="bk-su-s"></p><div class="row-b" id="bk-su-b"></div></section>
  <section class="bkp-card" id="bk-intro"><p id="bk-intro-p"></p><div class="bkp-ex" id="bk-ex"></div></section>
  <div class="bkp-chat" id="bk-chat" aria-live="polite"></div>
  <details class="bkp-card" id="bk-adm" hidden style="margin-top:18px"><summary id="bk-adm-t">⚙️ Settings</summary><div class="bkp-set" id="bk-set"></div></details>
</main>
<div class="bkp-in"><div class="bkp-hint" id="bk-hint"></div><form id="bk-form"><textarea id="bk-q" rows="1" maxlength="600" enterkeyhint="send"></textarea>
  <button type="button" class="sec" id="bk-mic" aria-label="Speak">🎙</button><button type="submit" id="bk-go" aria-label="Send">➤</button></form></div>
<script>
/*COMMON*/
/*BLINKIDE*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const LS = {get: (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } },
              set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} }};
  const BK = window.MWBlinki, client = Math.random().toString(36).slice(2, 12);
  const fig = m => BK ? BK.make(m || "normal") : E("span");
  const api = async (path, b) => { try { const r = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))});
    return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  const get = async path => { try { return await (await fetch(path, {cache: "no-store"})).json(); } catch (e) { return null; } };
  let S = null, mode = LS.get("mw-bk-mode", "frag"), last = null, tm = 0;
  const face = fig("normal"); $i("bk-face").appendChild(face);
  document.title = "MoveEye – " + t("Ask Blinki");
  $i("bk-back").textContent = "‹ " + t("More"); $i("bk-title").textContent = t("Ask Blinki");
  $i("bk-go").setAttribute("aria-label", t("Send")); $i("bk-mic").setAttribute("aria-label", t("Hold to speak"));
  const SUB = {frag: "Questions about MoveEye - answers from the manual", fehler: "Blinki reads the log and the self-check - and only suggests",
               geschichte: "A story for the campfire - for children or adults", natur: "About the animals MoveEye saw near the camp", quiz: "New questions for the quiz of the game corner"};
  const PH = {frag: "Ask something about MoveEye …", fehler: "What does not work? (or just send)", geschichte: "What about? (or just send)",
              natur: "Which animal? (or just send)", quiz: "Topic? (or just send)"};
  const EX = {frag: ["How loud is the siren?", "What does the clap switch do?", "How do I set up push messages?", "Why does it alarm at night?"],
              fehler: ["Why are there no push messages?", "The picture is black", "Check everything"],
              geschichte: ["A fox who wants to camp", "The night the stars went out", "Blinki and the lost tent peg"],
              natur: ["What did MoveEye see this week?", "How do I watch foxes without disturbing them?"],
              quiz: ["Animals of the Alps", "Stars and moon", "Switzerland"]};
  const INTRO = {geschichte: "Lean back - I tell you a story. Choose for whom, and if you like a place of your site.",
                 natur: "I look at what MoveEye saw in the last 7 days and tell you about these animals.",
                 quiz: "I write new questions for the quiz of the game corner. You check them and take the good ones."};
  const OPT = {kid: LS.get("mw-bk-kid", "1") === "1", place: "", n: 8, img: false};
  window.MWBK = {SUB: SUB, PH: PH, EX: EX, hooks: []};     // the later stages add their modes here
  const fmtInline = (el, s) => { s.split(/(\*\*[^*]+\*\*)/).forEach(p => { if (/^\*\*[^*]+\*\*$/.test(p)) el.appendChild(E("b", "", p.slice(2, -2))); else if (p) el.appendChild(document.createTextNode(p)); }); };
  function render(box, text, writing) {                  // a small part of Markdown: paragraphs, 1. / - lists, **bold** (always as text, never HTML)
    box.textContent = ""; let list = null;
    String(text || "").split("\n").forEach(line => {
      const m = line.match(/^\s*(\d+[.)]|[-•*])\s+(.*)$/);
      if (m) { const tag = /\d/.test(m[1]) ? "ol" : "ul"; if (!list || list.tagName.toLowerCase() !== tag) { list = E(tag); box.appendChild(list); } const li = E("li"); fmtInline(li, m[2]); list.appendChild(li); return; }
      list = null; if (!line.trim()) return; const p = E("p"); fmtInline(p, line); box.appendChild(p);
    });
    if (writing) { const lastEl = box.lastElementChild && (box.lastElementChild.lastElementChild || box.lastElementChild); (lastEl || box).classList.add("cur"); }
  }
  function chip() {
    const c = $i("bk-chip"); let cls = "no", tx = t("The language model is missing - Blinki shows the places of the manual");
    if (S.held) { cls = "held"; tx = S.held_t; }
    else if (S.cloud && S.cloud.on) { cls = "cloud"; tx = t("Cloud") + " · " + (S.cloud.name || ""); }
    else if (S.offline_ok) { cls = "ok"; tx = t("offline on this device") + " · " + S.model.name; }
    c.className = "bkp-chip " + cls; $i("bk-chip-t").textContent = tx;
  }
  function modes() {
    const box = $i("bk-modes"); box.textContent = "";
    if (!S.modes.some(x => x.m === mode)) mode = (S.modes[0] || {}).m || "frag";
    S.modes.forEach(x => { const b = E("button", "sec" + (x.m === mode ? " sel" : ""), x.icon + " " + x.label); b.type = "button"; b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", x.m === mode ? "true" : "false"); b.onclick = () => { mode = x.m; LS.set("mw-bk-mode", mode); modes(); intro(); }; box.appendChild(b); });
  }
  function intro() {
    $i("bk-sub").textContent = t(SUB[mode] || SUB.frag); $i("bk-q").placeholder = t(PH[mode] || PH.frag);
    $i("bk-intro").hidden = !!$i("bk-chat").children.length;
    $i("bk-intro-p").textContent = t({frag: "Hello! I know the manual of MoveEye. Ask me how something works - I show you where to find it.",
      fehler: "I look at the self-check and the log of MoveEye and explain what is wrong. I change nothing by myself: a fix only runs after your OK."}[mode]
      || INTRO[mode] || "");
    opts();
    const ex = $i("bk-ex"); ex.textContent = "";
    (EX[mode] || []).forEach(q => { const b = E("button", "sec", t(q)); b.type = "button"; b.onclick = () => ask(t(q)); ex.appendChild(b); });
    window.MWBK.hooks.forEach(f => { try { f("intro", mode, S); } catch (e) {} });
  }
  function opts() {
    const box = $i("bk-opts"); box.textContent = ""; box.hidden = !["geschichte", "natur", "quiz"].includes(mode); if (box.hidden || !S) return;
    if (mode === "geschichte") {
      if (!S.kid_only) { const sg = E("div", "seg"); [["1", "🧒 " + t("Children")], ["0", "🧑 " + t("Adults")]].forEach(([v, l]) => { const b = E("button", "sec" + ((OPT.kid ? "1" : "0") === v ? " sel" : ""), l); b.type = "button";
        b.onclick = () => { OPT.kid = v === "1"; LS.set("mw-bk-kid", v); opts(); }; sg.appendChild(b); }); box.appendChild(sg); }
      if ((S.places || []).length) { const sel = E("select"); sel.setAttribute("aria-label", t("Place"));
        [["", "📍 " + t("anywhere")]].concat(S.places.map(x => [x, "📍 " + x])).forEach(([v, l]) => { const o = E("option", "", l); o.value = v; if (v === OPT.place) o.selected = true; sel.appendChild(o); });
        sel.onchange = () => { OPT.place = sel.value; }; box.appendChild(sel); }
    } else if (mode === "natur" && S.cloud && S.cloud.on) {
      const l = E("label"), c = E("input"); c.type = "checkbox"; c.checked = OPT.img; c.id = "bk-img"; c.onchange = () => { OPT.img = c.checked; };
      l.append(c, E("span", "", "📷 " + t("Send the camera picture to the cloud (only this once)"))); box.appendChild(l);
    } else if (mode === "quiz") {
      const sel = E("select"); sel.setAttribute("aria-label", t("Number of questions")); [5, 8, 10].forEach(n => { const o = E("option", "", n + " " + t("questions")); o.value = n; if (n === OPT.n) o.selected = true; sel.appendChild(o); });
      sel.onchange = () => { OPT.n = +sel.value; }; box.appendChild(sel);
      if (S.quiz_n) box.appendChild(E("span", "bkp-wait", "🎲 " + S.quiz_n + " " + t("questions of Blinki in the game corner")));
    }
  }
  function setup() {
    const box = $i("bk-setup"), need = !S.offline_ok && !(S.cloud && S.cloud.on);
    box.hidden = !need; if (!need) return;
    $i("bk-su-t").textContent = "🧠 " + t("Set up Blinki");
    $i("bk-su-p").textContent = t("For free answers Blinki needs a language model on this device (about 1 GB, loaded once, then offline) and the engine llama.cpp.");
    $i("bk-su-m").textContent = S.model.name + " · " + S.model.mb + " MB · " + t("licence") + ": " + S.model.licence + " · " + t("checked with a fixed checksum");
    const bar = $i("bk-su-bar"), bs = $i("bk-su-b"); bs.textContent = ""; let st = "";
    if (S.dl.running) { bar.hidden = false; bar.firstChild.style.width = Math.round(100 * S.dl.got / Math.max(1, S.dl.total)) + "%";
      st = "⬇ " + t("loading …") + " " + Math.round(S.dl.got / 1048576) + " / " + Math.round(S.dl.total / 1048576) + " MB"; }
    else if (S.engine.install === "running") { bar.hidden = false; bar.firstChild.style.width = S.engine.pct + "%"; st = "🔧 " + t("building the engine …") + " " + (S.engine.step || "") + " " + (S.engine.pct ? S.engine.pct + "%" : ""); }
    else bar.hidden = true;
    if (S.dl_t) st += (st ? " · " : "") + "⚠ " + S.dl_t; if (S.install_t) st += (st ? " · " : "") + "⚠ " + S.install_t;
    st += (st ? " · " : "") + (S.model.ok ? "✓ " + t("model ready") : "✗ " + t("model missing")) + " · " + (S.engine.ok ? "✓ " + t("engine ready") : "✗ " + t("engine missing"));
    if (S.disk_free_mb != null) st += " · " + t("free") + ": " + S.disk_free_mb + " MB";
    $i("bk-su-s").textContent = st;
    if (!S.admin) { bs.appendChild(E("p", "", t("The administrator sets Blinki up (Mehr › Blinki fragen)."))); return; }
    const B = (txt, f, sec) => { const b = E("button", sec ? "sec" : "", txt); b.type = "button"; b.onclick = f; bs.appendChild(b); };
    if (S.dl.running) B("✕ " + t("Cancel"), async () => { await api("/api/ki/model", {action: "cancel"}); load(); }, true);
    else if (!S.model.ok) B("⬇ " + t("Load the model") + " (" + S.model.mb + " MB)", async () => { const j = await api("/api/ki/model", {action: "load"}); if (!j.ok) alert(j.error); load(); });
    if (!S.engine.ok && S.engine.install !== "running") B("🔧 " + t("Set up the engine"), async () => {
      if (!confirm(t("The engine llama.cpp is built once on this device from the checked source (15-30 min, the protection keeps running). Start?"))) return;
      const j = await api("/api/ki/model", {action: "engine"}); if (!j.ok) alert(j.error); load(); }, true);
  }
  function adm() {
    const d = $i("bk-adm"); d.hidden = !S.admin; if (!S.admin) return;
    $i("bk-adm-t").textContent = "⚙️ " + t("Blinki settings");
    const box = $i("bk-set"); if (box.contains(document.activeElement)) return; box.textContent = "";
    const sw = (key, label, val, note) => { const l = E("label"), c = E("input"); c.type = "checkbox"; c.checked = !!val;
      c.onchange = async () => { const j = await api("/api/ki/set", {key: key, value: c.checked}); if (!j.ok) { alert(j.error); c.checked = !c.checked; } else { S = j.state; } };
      l.append(c, E("span", "", label)); box.appendChild(l); if (note) box.appendChild(E("div", "mut", note)); };
    const ls = E("label"), c2 = E("input"); c2.type = "checkbox"; c2.checked = LS.get("mw-bk-read", "0") === "1"; c2.onchange = () => LS.set("mw-bk-read", c2.checked ? "1" : "0");
    ls.append(c2, E("span", "", "🔊 " + t("Read the answers aloud in this browser"))); box.appendChild(ls);
    const th = E("label"), sel = E("select"); [1, 2, 3, 4].forEach(n => { const o = E("option", "", n + " " + t("cores")); o.value = n; if (n === S.threads) o.selected = true; sel.appendChild(o); });
    sel.onchange = async () => { const j = await api("/api/ki/set", {key: "blinki_threads", value: +sel.value}); if (j.ok) S = j.state; };
    th.append(E("span", "", t("Cores for Blinki")), sel); box.appendChild(th);
    box.appendChild(E("div", "mut", t("2 cores are fastest on the Pi 5 (the memory is the limit); the detection keeps the other cores. Blinki pauses at an alarm, while MoveEye follows a movement and over 80 °C.")));
    if (S.cloud) {                                       // the cloud: generic formats, the key only goes in, never comes back
      const C = S.cloud, h = E("div", "", ""); h.appendChild(E("b", "", "☁ " + t("Cloud instead of the device")));
      box.appendChild(h); box.appendChild(E("div", "mut", t("Faster and better answers - but the question goes over the internet to the service you choose. Pictures only with your OK each time.")));
      sw("blinki_cloud_on", t("Use the cloud"), C.switch);
      const fld = (key, label, val, type, ph) => { const l = E("label"); l.style.flexDirection = "column"; l.style.alignItems = "stretch";
        const i = E("input"); i.type = type || "text"; i.value = val || ""; i.autocomplete = "off"; i.spellcheck = false; if (ph) i.placeholder = ph; i.id = "bk-c-" + key;
        i.onchange = async () => { if (type === "password" && !i.value) return; const j = await api("/api/ki/set", {key: key, value: i.value});
          if (!j.ok) alert(j.error); else { S = j.state; if (type === "password") { i.value = ""; i.placeholder = "•••••• (" + t("set") + ")"; } } };
        l.append(E("span", "mut", label), i); box.appendChild(l); return i; };
      const fl = E("label"); fl.style.flexDirection = "column"; fl.style.alignItems = "stretch"; const fs = E("select"); fs.id = "bk-c-fmt";
      C.fmts.forEach(x => { const o = E("option", "", x.label); o.value = x.v; if (x.v === C.fmt) o.selected = true; fs.appendChild(o); });
      fs.onchange = async () => { const j = await api("/api/ki/set", {key: "blinki_cloud_fmt", value: fs.value}); if (j.ok) S = j.state; };
      fl.append(E("span", "mut", t("Format")), fs); box.appendChild(fl);
      fld("blinki_cloud_url", t("Address of the service (https://…)"), C.url, "url", "https://…/v1");
      fld("blinki_cloud_model", t("Model name (as the service names it)"), C.model, "text", "");
      const k = fld("blinki_cloud_key", t("Key (API key) - only the administrator, never shown again"), "", "password", C.key_set ? "•••••• (" + t("set") + ")" : "");
      if (C.key_set) { const b = E("button", "sec", t("Clear")); b.type = "button"; b.onclick = async () => { const j = await api("/api/ki/set", {key: "blinki_cloud_key", value: ""}); if (j.ok) { S = j.state; k.placeholder = ""; } }; box.appendChild(b); }
    }
    window.MWBK.hooks.forEach(f => { try { f("settings", box, S, sw); } catch (e) {} });
    if (S.model.ok) { const b = E("button", "sec", "🗑 " + t("Delete the model") + " (" + S.model.mb + " MB)"); b.type = "button";
      b.onclick = async () => { if (confirm(t("Delete the language model? Blinki then only shows the places of the manual."))) { await api("/api/ki/model", {action: "delete"}); load(); } }; box.appendChild(b); }
  }
  function paint() { if (!S) return; chip(); modes(); intro(); setup(); adm(); window.MWBK.hooks.forEach(f => { try { f("paint", S); } catch (e) {} }); }
  async function load() {
    clearTimeout(tm); const j = await get("/api/ki/state?lang=" + L());
    if (j && j.state) { S = j.state; window.MWBK.S = S; paint(); }
    tm = setTimeout(load, S && (S.dl.running || S.engine.install === "running" || S.held) ? 1500 : 8000);
  }
  function hm() { const d = new Date(); return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); }
  // the voice: piece after piece of Piper (Blinki only knows its own pieces)
  let VO = null;
  async function sayBrowser(id, btn) {
    if (VO) { VO.stop = true; VO = null; if (btn) btn.textContent = "🔊 " + t("Read aloud"); return; }
    const me = VO = {stop: false}; if (btn) btn.textContent = "⏹ " + t("Stop");
    for (let n = 0; n < 12 && !me.stop; n++) {
      const j = await api("/api/ki/say", {id: id, n: n});
      if (!j.ok || me.stop) { if (!j.ok && n === 0) alert(j.error); break; }
      const a = new Audio("/api/ki/voice/" + j.sid + ".wav"); me.a = a;
      await new Promise(r => { a.onended = r; a.onerror = r; a.play().catch(r); const iv = setInterval(() => { if (me.stop) { a.pause(); clearInterval(iv); r(); } }, 200); a.addEventListener("ended", () => clearInterval(iv)); });
      if (!j.more) break;
    }
    if (VO === me) VO = null; if (btn) btn.textContent = "🔊 " + t("Read aloud");
  }
  window.MWBK.sayBrowser = sayBrowser;
  function bubble(job, q) {
    const chat = $i("bk-chat");
    if (q) { const me = E("div", "bkp-me", q); me.appendChild(E("small", "", hm())); chat.appendChild(me); }
    const it = E("div", "bkp-it"), f = fig("think"), say = E("div", "bkp-say"), txt = E("div"), wait = E("div", "bkp-wait"), err = E("div", "bkp-err");
    err.hidden = true; say.append(wait, txt, err); it.append(f, say); chat.appendChild(it); $i("bk-intro").hidden = true;
    it.scrollIntoView({block: "end", behavior: "smooth"});
    return {it: it, f: f, say: say, txt: txt, wait: wait, err: err, n: 0, text: "", job: job};
  }
  function finish(b, j) {
    const say = b.say;
    if (BK) BK.mood(b.f, j.state === "done" ? "happy" : "normal");
    if (j.err) { b.err.hidden = false; b.err.textContent = "⚠ " + j.err; }
    if (j.state === "stopped") { b.err.hidden = false; b.err.textContent = "⏹ " + t("stopped"); }
    if ((j.links || []).length) { const o = E("div", "bkp-open"); j.links.slice(0, 3).forEach(l => { const a = E("a", "", t("Open") + ": " + l.title + " ›"); a.href = l.href; o.appendChild(a); }); say.appendChild(o); }
    (j.fixes || []).filter(x => x.act && S && S.admin).forEach(x => {
      const fx = E("div", "bkp-fix"); fx.appendChild(E("div", "", "💡 " + t("Suggestion") + ": " + x.title + (x.fix ? " → " + x.fix : "")));
      const bt = E("button", "sec", "✓ " + (x.fix || t("Fix"))); bt.type = "button";
      bt.onclick = async () => { if (!confirm(t("Blinki suggests:") + "\n" + (x.fix || x.title) + "\n\n" + t("Run it now?"))) return;
        bt.disabled = true; const r = await api("/api/ki/fix", {fid: x.fid, ok: true}); fx.appendChild(E("div", r.ok ? "bkp-wait" : "bkp-err", r.ok ? "✓ " + (r.msg || t("done")) : "⚠ " + r.error)); };
      fx.appendChild(bt); say.appendChild(fx); });
    const src = (j.sources || []).map(s => "«" + s.title + "»").join(" · ");
    const info = [src ? (j.mode === "fehler" ? "🔎 " + t("Read") + ": " : "📖 " + t("From the manual") + ": ") + src : "",
      j.engine === "cloud" ? "☁ " + t("Cloud") : j.engine === "offline" ? t("Answer in") + " " + Math.round(j.secs) + " s" : ""].filter(Boolean).join(" · ");
    if (info) say.appendChild(E("div", "bkp-src", info));
    if (j.quiz && j.quiz.length) {                       // the quizmaster: check the questions, take them into the game corner
      const ol = E("ol", "bkp-quiz"); j.quiz.forEach(x => { const li = E("li", "", x.q); li.appendChild(E("small", "", "→ " + x.a)); ol.appendChild(li); }); say.appendChild(ol);
      b.txt.hidden = true;
      const tk = E("button", "", "➕ " + t("Into the game corner") + " (" + j.quiz.length + ")"); tk.type = "button"; tk.disabled = !!j.taken;
      tk.onclick = async () => { tk.disabled = true; const r = await api("/api/ki/quiz", {id: j.id}); tk.textContent = r.ok ? "✓ " + r.n + " " + t("questions in the game corner") : "⚠ " + r.error; if (!r.ok) tk.disabled = false; };
      const ac = E("div", "bkp-act"); ac.appendChild(tk); say.appendChild(ac);
    } else if (j.mode === "quiz" && j.state === "done") { b.err.hidden = false; b.err.textContent = "⚠ " + t("No usable questions - try again."); }
    if (j.image) say.appendChild(E("div", "bkp-src", "📷 " + t("one camera picture was sent to the cloud")));
    window.MWBK.hooks.forEach(f => { try { f("done", b, j); } catch (e) {} });
    if (!b.text) return;
    const act = E("div", "bkp-act"), rd = E("button", "sec", "🔊 " + t("Read aloud")); rd.type = "button"; rd.onclick = () => sayBrowser(j.id, rd); act.appendChild(rd);
    if (S && S.talk) { const sp = E("button", "sec", "📢 " + t("On the loudspeaker")); sp.type = "button"; sp.onclick = async () => { const r = await api("/api/ki/say", {id: j.id, where: "pi"}); if (!r.ok) alert(r.error); }; act.appendChild(sp); }
    const cp = E("button", "sec", "📋 " + t("Copy")); cp.type = "button"; cp.onclick = () => { try { navigator.clipboard.writeText(b.text); cp.textContent = "✓ " + t("Copied"); } catch (e) {} }; act.appendChild(cp);
    say.appendChild(act);
    if (LS.get("mw-bk-read", "0") === "1" && j.state === "done") sayBrowser(j.id, rd);
  }
  async function follow(b) {
    const j = await get("/api/ki/job/" + b.job + "?from=" + b.n);
    const v = j && j.job;
    if (!v) { b.err.hidden = false; b.err.textContent = "⚠ " + t("No connection to MoveEye."); return; }
    if (v.full) { b.text = v.text; b.n = v.n; } else if (v.text) { b.text += v.text; b.n = v.n; }
    const live = ["wait", "think", "write"].includes(v.state);
    b.wait.className = "bkp-wait" + (v.held ? " warn" : "");
    b.wait.textContent = v.held ? "⏸ " + v.held : v.state === "wait" ? (v.queue ? t("waiting - questions before you:") + " " + v.queue : t("Blinki wakes up …")) : v.state === "think" && !b.text ? t("Blinki thinks …") : "";
    if (BK) BK.mood(b.f, v.held ? "normal" : v.state === "write" ? "point" : "think");
    render(b.txt, b.text, live && !!b.text);
    if (live) { setTimeout(() => follow(b), 400); return; }
    b.wait.textContent = ""; last = [b.q || "", b.text]; finish(b, v); $i("bk-go").disabled = false; cur = null;
  }
  let cur = null;
  async function ask(q, extra) {
    q = String(q || "").trim(); if (!q && !["fehler", "geschichte", "natur", "quiz"].includes(mode)) return;
    extra = Object.assign({}, extra || {});
    if (mode === "geschichte") Object.assign(extra, {kid: OPT.kid, place: OPT.place});
    if (mode === "quiz") extra.n = OPT.n;
    if (mode === "natur" && OPT.img && S && S.cloud && S.cloud.on) {
      if (confirm(t("Send ONE picture of the camera to the cloud service now?") + "\n" + (S.cloud.name || ""))) extra.image_ok = true;
      OPT.img = false; const c = $i("bk-img"); if (c) c.checked = false; }
    if (cur) api("/api/ki/stop", {id: cur.job});
    $i("bk-go").disabled = true; $i("bk-q").value = ""; grow();
    const j = await api("/api/ki/ask", Object.assign({mode: mode, q: q, client: client, prev: last}, extra || {}));
    if (!j.ok) { $i("bk-go").disabled = false; const b = bubble("", q); b.wait.textContent = ""; b.err.hidden = false; b.err.textContent = "⚠ " + j.error; if (BK) BK.mood(b.f, "normal"); return; }
    const b = bubble(j.id, q || (j.job && j.job.q) || ""); b.q = q; cur = b; follow(b);
    return b;
  }
  window.MWBK.ask = ask;
  const grow = () => { const a = $i("bk-q"); a.style.height = "auto"; a.style.height = Math.min(140, a.scrollHeight) + "px"; };
  $i("bk-q").addEventListener("input", grow);
  $i("bk-q").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); ask($i("bk-q").value); } });
  $i("bk-form").onsubmit = e => { e.preventDefault(); ask($i("bk-q").value); };
  window.MWBK.mode = () => mode;
  load();
})();
</script>
</body></html>
"""
