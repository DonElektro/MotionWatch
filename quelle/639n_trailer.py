#@ MoveEye – Teil 639n: Trailer der Geschichten (Daniel 31.10.2026) – live im Browser: /sim/trailer?id=grossvater|maggie (Bild des Simulators wie /sim/vorfuehrung, startet den Trailer im Simulator), /api/trailer; Schnell-Karte «🛠 Entwickler» ganz oben im Reiter «Sim» (Trailer Grossvater · Trailer Maggie · Vorführung) und die zwei Trailer oben in Einstellungen → Entwickler; nur der Besitzer mit Entwickler-Bereich. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Der 3D-Simulator spielt den Trailer selbst (simulator3d/scripts/trailer.gd: Kamerafahrt im Bergtal, Musik, Texttafeln,
# Erzähler). Hier nur das Starten und Zuschauen:
#   * /sim/trailer?id=…: startet den Trailer (wenn nicht schon einer läuft) und zeigt das Bild des Simulators
#     (/sim/view.jpg?bare=1 – nur solange der Film läuft; danach ohne bare, sonst blieben die Knöpfe am PC versteckt),
#     unten eine Leiste: Beenden, Nochmals, Ton, Stimme, Vollbild, Zurück.
#   * Ton auch im Browser (Fix 3.19.x, Daniel: «am iPad nichts»): grosser Knopf «🔊 Tippen für Ton» (iOS braucht ein Tippen
#     vor Sprache und Audio; ein Tippen irgendwo genügt). Danach Erzähler (speechSynthesis, wie bisher) und Musik + Geräusche:
#     /api/trailer?plan=1 holt den Ton-Plan des Simulators (trailer.gd ton_plan: Zeit, Klang, Lautstärke, Überblendung),
#     /sim/trailer_ton/<klang>.wav die Klänge (ab 01.11.2026 echte Aufnahmen als MP3 aus simulator3d/klang/web/, ≈ 2.4 MB;
#     ältere Simulatoren: WAV, mono 22 kHz; Schleifen mit Schleifenpunkten «schleifen» aus dem Plan, dazu ein Begrenzer wie der
#     Bus «Trailer» im Simulator); die Seite spielt sie mit
#     WebAudio im Takt von «t» aus /api/trailer (nachgeführt, wenn es mehr als 0.35 s abweicht). Ältere Simulatoren ohne
#     Plan: nur der Erzähler. Der Ton läuft auf beiden Geräten (PC und iPad).
#   * /api/trailer: GET = Stand (Simulator /control trailer info), POST {do: start (id) | stop}. Nur der Besitzer
#     (nacht_may: Administrator, nicht im Bedienermodus), wie die Vorführung (639m).
#   * Einstieg: Reiter «Sim» ganz oben die Karte «🛠 Entwickler» (nur mit dem Entwickler-Bereich und für den Besitzer) mit
#     «🎬 Trailer Grossvater», «🎬 Trailer Maggie», «🎬 Vorführung»; dazu Einstellungen → Entwickler (Web 530 devExtras,
#     Fenster 639c) ganz oben die zwei Trailer. Im Simulator selbst: oben im Fenster «Entwickler» und auf den Story-Karten.
# Hier (nach 639m) weil VF-Teile (639m), render_page, sim_control, nacht_may, SIM_PAGE, WEB_PAGE vorher kommen.
# ----------------------------------------------------------------------------
TRL_IDS = ("grossvater", "maggie")


def trl_info():
    if not CFG.get("sim_on"):
        return {"ok": False, "error": tr("The 3D simulator is not connected."), "offline": True}
    try:
        r = sim_control({"action": "trailer", "do": "info"}) or {}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
    if not r.get("ok") and "laeuft" not in r:
        if "unknown" in str(r.get("error") or "").lower():
            return {"ok": False, "error": tr("This simulator has no trailers yet – update it.")}
        return {"ok": False, "error": str(r.get("error") or tr("The 3D simulator is not connected."))[:120]}
    return r


def trl_plan():
    """the sound plan of the running trailer (simulator trailer.gd ton_plan) – for music and noises in the browser"""
    if not CFG.get("sim_on"):
        return {"ok": False, "error": tr("The 3D simulator is not connected.")}
    try:
        r = sim_control({"action": "trailer", "do": "plan"}) or {}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
    if not isinstance(r.get("plan"), list):
        return {"ok": False, "error": str(r.get("error") or "no plan")[:120]}
    return r


TRL_TON_RE = re.compile(r"^[a-z_]{2,24}$")


def trl_do(d, owner=True):
    """start (id) / stop – only the owner"""
    if not owner:
        log_event("web", "Trailer refused (not the owner / operator mode)")
        return {"ok": False, "error": tr("Only the owner can do this."), "code": 403}
    w = str((d or {}).get("do") or "")
    if w not in ("start", "stop"):
        return {"ok": False, "error": "do: start | stop", "code": 400}
    if not CFG.get("sim_on"):
        return {"ok": False, "error": tr("The 3D simulator is not connected.")}
    c = {"action": "trailer", "do": w}
    if w == "start":
        tid = str(d.get("id") or "")
        if tid not in TRL_IDS:
            return {"ok": False, "error": "id: " + " | ".join(TRL_IDS), "code": 400}
        c["id"] = tid
        lg = str(CFG.get("lang") or "")
        if lg in ("de", "fr", "it", "rm", "en"):
            c["sprache"] = lg
    try:
        r = sim_control(c) or {}
    except Exception as e:
        if w == "start" and "timed out" in str(e):           # building the Bergtal takes a moment
            return {"ok": True, "loading": True}
        return {"ok": False, "error": str(e)[:80]}
    if str(r.get("error") or "").startswith("busy: "):
        return {"ok": False, "error": tr("The simulator is busy: {w}").replace("{w}", str(r["error"])[6:])}
    return r


TRL_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MoveEye - Trailer</title>
<style>
/*BASECSS*/
html,body{height:100%;margin:0;background:#000;overflow:hidden}
#tl-img{position:fixed;inset:0;width:100%;height:100%;object-fit:contain;background:#000;display:block}
#tl-bar{position:fixed;left:50%;bottom:calc(12px + env(safe-area-inset-bottom));transform:translateX(-50%);max-width:calc(100% - 20px);box-sizing:border-box;
  background:rgba(17,24,34,.88);border:1px solid var(--line);border-radius:14px;padding:8px 10px;transition:opacity .4s;z-index:3}
#tl-bar.off{opacity:0;pointer-events:none}
#tl-st{font-size:12px;color:var(--mut);text-align:center;margin:0 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tl-row{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}
.tl-row button,.tl-row a{min-height:40px;font-size:14px}
#tl-msg{position:fixed;top:10px;left:50%;transform:translateX(-50%);font-size:13px;color:#fff;background:rgba(0,0,0,.55);padding:4px 10px;border-radius:9px;z-index:5}
#tl-msg:empty{display:none}
@media(max-width:520px){.tl-row button,.tl-row a{flex:1 1 auto;font-size:13px;padding-left:8px;padding-right:8px}#tl-st{white-space:normal}}
</style></head><body>
<img id="tl-img" alt="">
<div id="tl-msg"></div>
<div id="tl-bar">
  <div id="tl-st"></div>
  <div class="tl-row">
    <button type="button" id="tl-stop" onclick="tlDo({do:'stop'})" data-i18n="End the trailer">End the trailer</button>
    <button type="button" class="sec" id="tl-again" onclick="tlDo({do:'start',id:ID})" data-i18n="Watch again">Watch again</button>
    <button type="button" class="sec spk-btn" onclick="spkToggle()">🔇</button>
    <button type="button" class="sec" onclick="tlFull()" data-i18n="Full screen">Full screen</button>
    <a class="btn sec" href="/sim" data-mw-exit data-i18n="Back">Back</a>
  </div>
</div>
<script>
/*COMMON*/
/*TLDE*/
/*SPKJS*/
/*TAJS*/
const ID = (new URLSearchParams(location.search).get("id") || "grossvater") === "maggie" ? "maggie" : "grossvater";
let S = {}, HIDE_T = 0, BUSY = 0, STARTED = 0, START_T = Date.now();
(async () => { try { await initAppearance(); } catch (e) {} tlInfo(true); tlPic(); tlShow(); })();
function tlShow() { const b = document.getElementById("tl-bar"); b.classList.remove("off"); clearTimeout(HIDE_T);
  HIDE_T = setTimeout(() => { if (S.laeuft && !S.ende && !SPK.pop) b.classList.add("off"); }, 4000); }
["pointerdown", "pointermove", "keydown"].forEach(e => addEventListener(e, tlShow, {passive: true}));
addEventListener("keydown", e => { if (e.key === "Escape" && S.laeuft) tlDo({do: "stop"}); });
function tlFull() { const d = document.documentElement; try { (document.fullscreenElement ? document.exitFullscreen() : (d.requestFullscreen || d.webkitRequestFullscreen).call(d)); } catch (e) {} }
function tlPic() {
  const im = document.getElementById("tl-img"), w = Math.min(1600, Math.round(innerWidth * (devicePixelRatio || 1)));
  const n = new Image(); let done = false;
  const next = () => { if (done) return; done = true; clearTimeout(to); setTimeout(tlPic, S.laeuft ? 80 : 1500); };
  const to = setTimeout(next, 6000);
  n.onload = () => { im.src = n.src; next(); };
  n.onerror = next;
  const bare = S.laeuft || (START_T && Date.now() - START_T < 30000);   // only while the film runs: afterwards the PC gets its buttons back
  n.src = "/sim/view.jpg?" + (bare ? "bare=1&" : "") + "clean=1&q=72&w=" + w + "&t=" + Date.now();
}
async function tlInfo(first) {
  let j = null;
  try { j = await (await fetch("/api/trailer", {cache: "no-store"})).json(); } catch (e) {}
  if (j) tlPaint(j);
  if (first && j && j.ok !== false && !j.laeuft && !STARTED) { STARTED = 1; tlDo({do: "start", id: ID}); }   // the button of the card started us
  setTimeout(tlInfo, 1500);
}
function tlPaint(j) {
  const was = !!S.laeuft;
  S = j || {};
  if (S.laeuft) START_T = 0; else if (was) START_T = 0;
  spkTick(S, false, !!S.laeuft);
  taSync(S);
  const nm = (S.id || ID) === "maggie" ? t("Trailer Maggie") : t("Trailer Grossvater");
  let st = nm;
  if (S.ok === false && S.error) st = "⚠ " + S.error;
  else if (S.laeuft && S.ende) st = nm + " · " + t("The end");
  else if (S.laeuft) st = nm + " · " + Math.floor(S.t || 0) + " / " + Math.round(S.dauer || 0) + " s" + (S.dauer ? "" : " · " + t("The valley is being prepared …"));
  else if (S.ergebnis) st = nm + " · " + t("Over");
  document.getElementById("tl-st").textContent = st;
  document.getElementById("tl-stop").hidden = !S.laeuft;
  document.getElementById("tl-again").hidden = !!S.laeuft;
  if (!S.laeuft || S.ende) tlShow();
}
async function tlDo(d) {
  if (BUSY) return; BUSY = 1; const m = document.getElementById("tl-msg");
  if (d.do === "start") { m.textContent = t("The valley is being prepared …"); START_T = Date.now(); }
  if (d.do === "stop") { START_T = 0; taStop(); }
  try { const r = await (await fetch("/api/trailer", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)})).json();
    if (r && r.ok === false && r.error) m.textContent = "⚠ " + r.error; else { if (d.do !== "start") m.textContent = ""; if (r && "laeuft" in r) tlPaint(r); } }
  catch (e) { m.textContent = "⚠ " + e; }
  BUSY = 0; tlShow(); setTimeout(() => { if (!m.textContent.startsWith("⚠")) m.textContent = ""; }, 5000);
}
</script></body></html>"""

# Sprachausgabe im Browser (Daniel 31.10.2026, Vorführung und Trailer): der Simulator meldet in /control … info das Feld
# «sprechen» {id, text, lang} (Erzähler, Untertitel, Texttafeln); die Seite liest jeden neuen Satz mit speechSynthesis vor, in
# der Sprache von MoveEye (rm: eine romanische Stimme, falls das Gerät eine hat, sonst Deutsch). iOS: Ton erst nach einem
# Tippen («🔊 Ton an»), dabei wird speechSynthesis einmal angestossen; Pause = Stimme verstummt. Dazu hält navigator.wakeLock
# den Bildschirm wach, solange der Film läuft (iPad). Die Texte bleiben unten als Untertitel im Bild (der Simulator zeigt sie).
# Stimme (Daniel 31.10.2026, «klingt fürchterlich»): automatisch die beste Stimme der Sprache – 1. Name/voiceURI mit Premium,
# Enhanced, Erweitert, Natural, Neural, Online oder Google, 2. lokale Stimme der Region (de-CH vor de-DE vor de-AT), 3. die
# Standardstimme; die Liste kommt auf iOS / Chrome verzögert (voiceschanged + Nachfragen). Tempo 0.92, Trailer 0.88, Tonhöhe 0.95,
# lange Sätze an Satzzeichen geteilt. Knopf «🗣 Stimme» neben 🔊: Liste der Stimmen (beste «empfohlen», ▶ Hörprobe), Tempo-
# Regler 0.8–1.1, Wahl pro Gerät (localStorage mw-film-stimme-<sprache>, mw-film-tempo); nur einfache Stimmen: Hinweis «Premium laden».
SPK_JS = r"""
let SPK = {on: true, unlocked: false, run: false, hooks: [], last: -1, wl: null, vs: [], pop: false, rate0: /\/trailer/.test(location.pathname) ? 0.88 : 0.92};
try { SPK.on = localStorage.getItem("mw-film-ton2") !== "0"; } catch (e) {}      // Fix 3.19.x: sound on by default (it still needs one tap: iOS)
const SPK_GOOD = /premium|enhanced|erweitert|natural|neural|online|google/i;      // the better voices (iOS Premium / Enhanced, Edge Online (Natural), Chrome Google)
const SPK_PROBE = {de: "Die Karte gehört jetzt dir – lies sie mit der Sonne.", en: "The map is yours now – read it with the sun.",
  fr: "La carte est à toi maintenant – lis-la avec le soleil.", it: "Ora la mappa è tua – leggila con il sole.",
  rm: "La charta tutga ussa a tai – legia ella cun il sulegl."};
function spkLang(l) { l = (l || (typeof LANG !== "undefined" ? LANG : "de") || "de").toLowerCase(); return l === "de" ? "de-CH" : l; }
function spkBase(l) { return spkLang(l).slice(0, 2); }
function spkVL(v) { return (v.lang || "").toLowerCase().replace("_", "-"); }
function spkLoad() { try { SPK.vs = (window.speechSynthesis && speechSynthesis.getVoices()) || []; } catch (e) { SPK.vs = []; } return SPK.vs; }
function spkScore(v, l) {                                  // 1. better voices by name, 2. local voice of the right region (de-CH > de-DE > de-AT), 3. the default
  const want = spkLang(l).toLowerCase(), base = want.slice(0, 2), vl = spkVL(v);
  let s = 0;
  if (SPK_GOOD.test((v.name || "") + " " + (v.voiceURI || ""))) s += 1000;
  if (vl.startsWith(base)) s += 300;                       // rm: a Romansh voice before a German one
  const reg = base === "de" || base === "rm" ? ["de-ch", "de-de", "de-at"] : [want];
  const ri = reg.indexOf(vl);
  if (ri >= 0) s += (3 - ri) * 20 + (v.localService ? 10 : 0);
  else if (v.localService) s += 5;
  if (v.default) s += 1;
  return s;
}
function spkList(l) {                                      // the voices of this language, best first
  const base = spkBase(l), vs = SPK.vs.length ? SPK.vs : spkLoad();
  let c = vs.filter(v => spkVL(v).startsWith(base));
  if (base === "rm") c = c.concat(vs.filter(v => spkVL(v).startsWith("de")));
  return c.map(v => [spkScore(v, l), v]).sort((a, b) => b[0] - a[0]).map(x => x[1]);
}
function spkId(v) { return v ? (v.voiceURI || v.name || "") : ""; }
function spkSaved(l) { try { return localStorage.getItem("mw-film-stimme-" + spkBase(l)) || ""; } catch (e) { return ""; } }
function spkRate() { let r = 0; try { r = parseFloat(localStorage.getItem("mw-film-tempo") || ""); } catch (e) {}
  return r >= 0.8 && r <= 1.1 ? (SPK.rate0 < 0.9 ? r - 0.04 : r) : SPK.rate0; }      // the trailer a bit calmer
function spkPick(l) {
  if (!window.speechSynthesis) return null;
  const list = spkList(l), want = spkSaved(l);
  return (want && list.find(v => spkId(v) === want)) || list[0] || null;
}
function spkParts(text) {                                  // long sentences in pieces at the punctuation (a more natural melody)
  const out = [];
  String(text).replace(/[«»]/g, "").replace(/\s+/g, " ").trim().split(/(?<=[.!?…])\s+/).forEach(s => {
    if (s.length <= 140) { if (s) out.push(s); return; }
    let cur = "";
    s.split(/(?<=[,;:–—])\s+/).forEach(p => { if (cur && (cur + " " + p).length > 140) { out.push(cur); cur = p; } else cur = cur ? cur + " " + p : p; });
    if (cur) out.push(cur);
  });
  return out;
}
function spkSay(text, l, v) {
  if (window.MW_VOICE && window.MW_VOICE !== "on") return;   // 3.23: one switch «Stimme» (639q voice_mode)
  v = v || spkPick(l);
  try { speechSynthesis.resume(); } catch (e) {}           // (iOS sometimes keeps the voice «paused» after a while)
  spkParts(text).forEach(p => { const u = new SpeechSynthesisUtterance(p);
    if (v) { u.voice = v; u.lang = v.lang; } else u.lang = spkLang(l);
    u.rate = spkRate(); u.pitch = 0.95; speechSynthesis.speak(u); });
}
function spkBtn() { document.querySelectorAll(".spk-btn").forEach(b => { b.textContent = SPK.on && SPK.unlocked ? "🔊 " + t("Sound on") : "🔇 " + t("Sound off"); });
  document.querySelectorAll(".spk-vbtn").forEach(b => { b.textContent = "🗣 " + t("Voice"); b.classList.toggle("on", SPK.pop); });
  const tp = document.getElementById("spk-tap"); if (tp) tp.textContent = "🔊 " + t("Tap for sound"); }
function spkToggle() {
  if (!SPK.unlocked || !SPK.on) { spkUnlock(); return; }   // not yet unlocked: this tap switches the sound on (never off)
  SPK.on = false; try { localStorage.setItem("mw-film-ton2", "0"); } catch (e) {}
  if (window.speechSynthesis) speechSynthesis.cancel();
  SPK.hooks.forEach(f => { try { f(false); } catch (e) {} });
  spkBtn(); spkTap();
}
function spkUnlock() {                                     // iOS: speech and WebAudio only after a tap - this one (in the tap itself)
  SPK.unlocked = true; SPK.on = true; try { localStorage.setItem("mw-film-ton2", "1"); } catch (e) {}
  if (window.speechSynthesis) {
    try { speechSynthesis.cancel(); } catch (e) {}
    const sp = S && S.sprechen, run = !!(S && S.laeuft && !S.pause);
    if (run && sp && sp.text) { SPK.last = sp.id; spkSay(sp.text, sp.lang || SPK.lang); }   // the sentence of right now
    else spkSay(t("Sound on"), SPK.lang);                  // a short «Ton an»: the voice is unlocked and you hear it works
  }
  SPK.hooks.forEach(f => { try { f(true); } catch (e) {} });   // the trailer: music and noises (WebAudio)
  spkBtn(); spkTap(); spkWake(!!(S && S.laeuft));
}
function spkTap() { const b = document.getElementById("spk-tap"); if (!b) return; const h = SPK.unlocked || !(S && S.laeuft); if (b.hidden !== h) { b.hidden = h; spkBtn(); } }
function spkTick(s, paused, running) {
  const sp = (s && s.sprechen) || null, act = running && !paused;
  if (sp && sp.lang) SPK.lang = sp.lang;
  if (window.speechSynthesis && SPK.run && !act) speechSynthesis.cancel();      // pause / end: the voice stops (only then - not the «Ton an»)
  SPK.run = act;
  spkWake(act);
  spkTap();
  if (!sp) return;
  if (SPK.last < 0 || !SPK.on || !SPK.unlocked || !running || paused || sp.id === SPK.last || !sp.text) { SPK.last = sp.id; return; }   // only new sentences
  SPK.last = sp.id;
  if (!window.speechSynthesis) return;
  if (sp.vorne) speechSynthesis.cancel();
  spkSay(sp.text, sp.lang);
}
async function spkWake(on) {                               // the screen stays awake while the film runs (iPad)
  try { if (on && !SPK.wl && navigator.wakeLock) { SPK.wl = await navigator.wakeLock.request("screen"); SPK.wl.addEventListener("release", () => { SPK.wl = null; }); }
    else if (!on && SPK.wl) { SPK.wl.release(); SPK.wl = null; } } catch (e) {}
}
// «🗣 Stimme»: the voices of the language, the best marked «recommended», ▶ = a sample; the choice stays on this device
function spkPop(open) {
  const p = document.getElementById("spk-pop"); if (!p) return;
  SPK.pop = open === undefined ? !SPK.pop : !!open; p.hidden = !SPK.pop; spkBtn();
  if (!SPK.pop) return;
  spkLoad(); spkPaint();
  const b = document.querySelector(".spk-vbtn"), bar = b && b.closest("[id$='-bar']");
  if (bar) p.style.bottom = Math.max(70, innerHeight - bar.getBoundingClientRect().top + 8) + "px";
}
function spkPaint() {
  const p = document.getElementById("spk-pop"); if (!p || p.hidden) return;
  const l = SPK.lang, list = spkList(l), best = list[0], cur = spkPick(l), saved = spkSaved(l), esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"})[c]);
  let h = '<div class="spk-hd"><b>🗣 ' + esc(t("Voice")) + '</b><button type="button" class="sec spk-x" onclick="spkPop(false)" aria-label="×">×</button></div>';
  if (!list.length) h += '<div class="mut spk-hint">' + esc(t("No voice for this language on this device.")) + "</div>";
  else {
    h += '<div class="spk-ls">';
    list.forEach((v, i) => { const id = spkId(v);
      h += '<div class="spk-v' + (v === cur ? " on" : "") + '"><button type="button" class="spk-nm" data-i="' + i + '">' + esc(v.name || id)
        + ' <span class="mut">' + esc(v.lang || "") + (v.localService === false ? " · ☁" : "") + "</span>"
        + (v === best ? ' <span class="spk-rec">' + esc(t("recommended")) + "</span>" : "") + '</button>'
        + '<button type="button" class="sec spk-pl" data-p="' + i + '" aria-label="' + esc(t("Listen")) + '">▶</button></div>'; });
    h += "</div>";
    if (saved) h += '<button type="button" class="sec spk-auto" style="width:100%;margin-top:6px">' + esc(t("Automatic (recommended)")) + "</button>";
  }
  const r = spkRate() + (SPK.rate0 < 0.9 ? 0.04 : 0);
  h += '<label class="spk-rt"><span>' + esc(t("Speed")) + '</span><input type="range" min="0.8" max="1.1" step="0.02" value="' + r.toFixed(2) + '"><span class="mut spk-rv">' + r.toFixed(2) + "</span></label>";
  if (!list.some(v => SPK_GOOD.test((v.name || "") + " " + (v.voiceURI || "")))) h += '<div class="mut spk-hint">💡 ' + esc(t("Better voices: iPad → Settings → Accessibility → Spoken Content → Voices → English → download «Premium».")) + "</div>";
  p.innerHTML = h;
  p.querySelectorAll(".spk-nm").forEach(b => b.onclick = () => { const v = list[+b.dataset.i];
    try { localStorage.setItem("mw-film-stimme-" + spkBase(l), spkId(v)); } catch (e) {} spkProbe(v); spkPaint(); });
  p.querySelectorAll(".spk-pl").forEach(b => b.onclick = () => spkProbe(list[+b.dataset.p]));
  const a = p.querySelector(".spk-auto"); if (a) a.onclick = () => { try { localStorage.removeItem("mw-film-stimme-" + spkBase(l)); } catch (e) {} spkPaint(); };
  const rg = p.querySelector(".spk-rt input");
  rg.oninput = () => { p.querySelector(".spk-rv").textContent = (+rg.value).toFixed(2); };
  rg.onchange = () => { try { localStorage.setItem("mw-film-tempo", rg.value); } catch (e) {} spkProbe(spkPick(l)); };
}
function spkProbe(v) {
  if (!window.speechSynthesis) return;
  speechSynthesis.cancel(); const l = SPK.lang;
  spkSay(SPK_PROBE[spkBase(l)] || SPK_PROBE.en, l, v);
}
(function spkSetup() {
  SPK.lang = spkLang();
  const st = document.createElement("style");
  st.textContent = "#spk-pop{position:fixed;left:50%;transform:translateX(-50%);bottom:90px;width:min(420px,calc(100% - 20px));max-height:min(60vh,460px);overflow:auto;z-index:6;"
    + "background:rgba(17,24,34,.94);border:1px solid var(--line);border-radius:14px;padding:8px 10px;color:var(--txt);-webkit-overflow-scrolling:touch}"
    + ".spk-hd{display:flex;align-items:center;justify-content:space-between;margin:0 0 6px}.spk-x{min-height:34px;min-width:40px;padding:0 10px}"
    + ".spk-v{display:flex;gap:6px;align-items:stretch;margin:4px 0}.spk-nm{flex:1 1 auto;text-align:left;min-height:42px;background:var(--btn2);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:6px 10px;font-size:14px;line-height:1.25;overflow-wrap:anywhere}"
    + ".spk-v.on .spk-nm{background:var(--acc);border-color:var(--acc);color:#fff}.spk-v.on .spk-nm .mut{color:#dbe8ff}"
    + ".spk-pl{flex:0 0 46px;min-height:42px;padding:0}.spk-rec{display:inline-block;font-size:11px;font-weight:700;padding:1px 7px;border-radius:9px;background:var(--grn);color:#06210f;margin-left:4px;vertical-align:1px}"
    + ".spk-rt{display:flex;align-items:center;gap:8px;margin:8px 0 2px;font-size:13px}.spk-rt input{flex:1 1 auto}.spk-hint{font-size:12px;margin-top:8px;line-height:1.4}"
    + ".spk-vbtn.on{background:var(--acc)!important;border-color:var(--acc)!important;color:#fff!important}"
    + "#spk-tap{position:fixed;left:50%;top:38%;transform:translate(-50%,-50%);z-index:7;font-size:22px;font-weight:700;padding:16px 28px;min-height:64px;"
    + "border-radius:999px;background:var(--acc);border:2px solid #fff;color:#fff;box-shadow:0 6px 30px rgba(0,0,0,.6);animation:spkp 1.6s ease-in-out infinite}"
    + "#spk-tap[hidden]{display:none}@keyframes spkp{50%{transform:translate(-50%,-50%) scale(1.06)}}";
  document.head.appendChild(st);
  const tap = document.createElement("button"); tap.type = "button"; tap.id = "spk-tap"; tap.hidden = true;
  tap.textContent = "🔊 " + t("Tap for sound"); tap.onclick = e => { e.stopPropagation(); spkUnlock(); };
  document.body.appendChild(tap);
  ["touchend", "click"].forEach(ev => addEventListener(ev, e => {        // one tap anywhere is enough (iOS: touchend / click count as a gesture)
    if (!SPK.unlocked && !(e.target && e.target.closest && e.target.closest(".spk-btn,.spk-vbtn,#spk-tap,#spk-pop"))) spkUnlock(); }, true));
  if (!window.speechSynthesis) return;
  const p = document.createElement("div"); p.id = "spk-pop"; p.hidden = true; document.body.appendChild(p);
  document.querySelectorAll(".spk-btn").forEach(b => { const v = document.createElement("button"); v.type = "button"; v.className = "sec spk-vbtn";
    v.onclick = () => spkPop(); b.after(v); });
  const fresh = () => { spkLoad(); spkPaint(); };
  try { speechSynthesis.addEventListener("voiceschanged", fresh); } catch (e) { speechSynthesis.onvoiceschanged = fresh; }
  [0, 250, 1000, 3000].forEach(ms => setTimeout(fresh, ms));      // iOS / Chrome load the voices late (voiceschanged is not always sent)
  addEventListener("keydown", e => { if (e.key === "Escape" && SPK.pop) { e.stopImmediatePropagation(); spkPop(false); } }, true);
})();
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && !SPK.wl && S && S.laeuft) spkWake(true); });
setTimeout(spkBtn, 50);
"""


# Musik und Geräusche des Trailers im Browser (Fix 3.19.x): der Ton-Plan des Simulators (trailer.gd ton_plan) mit WebAudio
# nachgespielt – Schleifen (Musikflächen, Wind, Wasser …) mit gleitender Lautstärke, Einzelklänge, Musik leiser während der
# Erzähler spricht (0.6, wie trailer.gd _audio_tick), am Schluss 2 s ausblenden. Die Uhr: «t» aus /api/trailer (alle 1.5 s);
# weicht sie mehr als 0.35 s ab, wird nachgeführt, bei mehr als 3 s (Sprung) neu aufgesetzt. Erst nach dem Tippen (iOS).
TA_JS = r"""
const TA = {ctx: null, buf: {}, plan: null, pid: "", loops: {}, ones: [], i: 0, base: null, mus: [], mb: null, fb: null, mg: null, load: 0, fail: 0, duck: 0, iv: 0, schl: {}, lim: null, pre: null};
function taDb(db) { return Math.pow(10, db / 20); }
function taUnlock(on) {
  try {
    if (!TA.ctx) { const C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      TA.ctx = new C(); TA.mg = TA.ctx.createGain();
      try {                                                // like the simulator's bus «Trailer»: +bus_db, then a limiter (no clipping)
        TA.pre = TA.ctx.createGain(); TA.lim = TA.ctx.createDynamicsCompressor();
        TA.lim.threshold.value = -2; TA.lim.knee.value = 0; TA.lim.ratio.value = 20; TA.lim.attack.value = 0.002; TA.lim.release.value = 0.12;
        TA.mg.connect(TA.pre); TA.pre.connect(TA.lim); TA.lim.connect(TA.ctx.destination);
      } catch (e) { TA.mg.connect(TA.ctx.destination); }
      TA.mb = TA.ctx.createGain(); TA.mb.connect(TA.mg); TA.fb = TA.ctx.createGain(); TA.fb.connect(TA.mg); }
    if (TA.ctx.resume) TA.ctx.resume();
    const b = TA.ctx.createBuffer(1, 1, 22050), x = TA.ctx.createBufferSource(); x.buffer = b; x.connect(TA.ctx.destination); x.start(0);   // iOS: unlocked by this tap
    TA.mg.gain.value = on === false ? 0 : 1;
  } catch (e) {}
  if (on !== false) taSync(S);
}
SPK.hooks.push(taUnlock);
async function taLoad() {                                  // the plan and the sounds of this trailer (once per trailer)
  if (TA.load || !TA.ctx || TA.fail > 2) return; TA.load = 1;
  try {
    const j = await (await fetch("/api/trailer?plan=1", {cache: "no-store"})).json();
    if (!j || !Array.isArray(j.plan)) { TA.fail++; TA.load = 0; return; }   // an older simulator: only the narrator
    TA.mus = j.musik || []; TA.schl = j.schleifen || {};
    if (TA.pre) TA.pre.gain.value = taDb(+j.bus_db || 0);
    await Promise.all((j.klaenge || []).map(async nm => {
      if (TA.buf[nm]) return;
      const ab = await (await fetch("/sim/trailer_ton/" + encodeURIComponent(nm) + ".wav")).arrayBuffer();
      TA.buf[nm] = await new Promise((ok, no) => { const p = TA.ctx.decodeAudioData(ab, ok, no); if (p && p.then) p.then(ok, no); });
    }));
    TA.plan = j.plan; TA.pid = j.id; TA.base = null;
  } catch (e) { TA.fail++; }
  TA.load = 0;
}
function taNow() { return TA.ctx.currentTime - TA.base; }  // the film time in the browser
function taLv(L, at) { if (at >= L.t1) return L.to; if (at <= L.t0) return L.from; return L.from + (L.to - L.from) * (at - L.t0) / (L.t1 - L.t0); }
function taRamp(L, to, at, f) { const v = taLv(L, at), g = L.g.gain;
  try { g.cancelScheduledValues(at); g.setValueAtTime(v, at); g.linearRampToValueAtTime(to, at + Math.max(0.02, f)); } catch (e) {}
  L.from = v; L.to = to; L.t0 = at; L.t1 = at + Math.max(0.02, f); }
function taLoop(nm, at) {
  let L = TA.loops[nm]; if (L || !TA.buf[nm]) return L;
  const x = TA.ctx.createBufferSource(), g = TA.ctx.createGain(); x.buffer = TA.buf[nm]; x.loop = true; g.gain.value = 0;
  const lp = TA.schl[nm]; if (lp && lp[1] <= x.buffer.duration + 0.01) { x.loopStart = lp[0]; x.loopEnd = Math.min(lp[1], x.buffer.duration); }   // MP3: 0.1 s wrap at both ends
  x.connect(g); g.connect(TA.mus.indexOf(nm) >= 0 ? TA.mb : TA.fb); x.start(at, lp ? lp[0] : 0);
  return TA.loops[nm] = {x, g, from: 0, to: 0, t0: 0, t1: 0};
}
function taOnesStop(at) { TA.ones.forEach(o => { try { o.stop(at); } catch (e) {} }); TA.ones = []; }
function taDo(e, at, now) {                                // one command of the plan (now = set at once: catching up)
  const k = e[1], c = TA.ctx;
  if (k === "loop") { const L = taLoop(e[2], at); if (L) taRamp(L, taDb(e[3]), at, now ? 0.05 : e[4]); }
  else if (k === "stop") { const L = TA.loops[e[2]]; if (L) taRamp(L, 0, at, now ? 0.05 : e[3]); }
  else if (k === "stille") { Object.values(TA.loops).forEach(L => taRamp(L, 0, at, now ? 0.05 : e[2])); taOnesStop(at); }
  else if (k === "one" && !now && TA.buf[e[2]]) { const x = c.createBufferSource(), g = c.createGain(); x.buffer = TA.buf[e[2]]; g.gain.value = taDb(e[3]);
    x.connect(g); g.connect(TA.fb); x.start(at); TA.ones.push(x); x.onended = () => { TA.ones = TA.ones.filter(o => o !== x); }; }
  else if (k === "say" && !now) { const g = TA.mb.gain;        // the music a bit lower while the narrator speaks
    try { if (at < TA.duck) g.cancelScheduledValues(at); g.setValueAtTime(0.6, at); g.setValueAtTime(1, at + e[2]); } catch (x) {} TA.duck = at + e[2]; }
}
function taStop() {
  if (!TA.ctx) return;
  const at = TA.ctx.currentTime;
  Object.values(TA.loops).forEach(L => { try { L.g.gain.cancelScheduledValues(at); L.g.gain.setTargetAtTime(0, at, 0.1); L.x.stop(at + 0.6); } catch (e) {} });
  TA.loops = {}; taOnesStop(at + 0.3); TA.base = null; TA.i = 0;
  try { TA.mb.gain.cancelScheduledValues(at); TA.mb.gain.setValueAtTime(1, at); } catch (e) {}
}
function taSeek(ft) {                                      // start / a jump: the loops as they are at ft (like trailer.gd _vorspulen)
  taStop(); TA.base = TA.ctx.currentTime - ft; const at = TA.ctx.currentTime + 0.02;
  let i = 0; while (i < TA.plan.length && TA.plan[i][0] <= ft) { if (["loop", "stop", "stille"].indexOf(TA.plan[i][1]) >= 0) taDo(TA.plan[i], at, true); i++; }
  TA.i = i;
}
function taTick() {                                        // every 50 ms: the commands of the next 150 ms, exactly on time
  if (!TA.ctx || !TA.plan || TA.base === null) return;
  const ft = taNow();
  while (TA.i < TA.plan.length && TA.plan[TA.i][0] <= ft + 0.15) { const e = TA.plan[TA.i++]; taDo(e, Math.max(TA.ctx.currentTime, TA.base + e[0]), false); }
}
function taSync(s) {
  if (!TA.ctx || !SPK.unlocked) return;
  if (!s || !s.laeuft) { if (TA.base !== null || Object.keys(TA.loops).length) taStop(); return; }
  if (!s.dauer) return;                                    // the valley is still being built
  if (TA.pid && s.id && TA.pid !== s.id) { taStop(); TA.plan = null; TA.pid = ""; }
  if (!TA.plan) { taLoad().then(() => { if (TA.plan) taSync(S); }); return; }
  if (!TA.iv) TA.iv = setInterval(taTick, 50);
  if (s.ende) return;                                      // the end card: the fade of the plan runs out
  const est = (+s.t || 0) + 0.15;                          // (the way from the simulator to here)
  if (TA.base === null || Math.abs(taNow() - est) > 3) taSeek(est);
  else if (Math.abs(taNow() - est) > 0.35) TA.base = TA.ctx.currentTime - est;   // slowly off (the simulator had a hitch): follow
}
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && TA.ctx && TA.ctx.resume) TA.ctx.resume(); });
"""

_HX_TRL = {
    'Trailer Grossvater': ('Trailer Grossvater', 'Bande-annonce Grand-père', 'Trailer Nonno', 'Trailer Tat'),
    'Trailer Maggie': ('Trailer Maggie', 'Bande-annonce Maggie', 'Trailer Maggie', 'Trailer Maggie'),
    'Vorführung': ('Vorführung', 'Démonstration', 'Dimostrazione', 'Demonstraziun'),
    'Developer': ('Entwickler', 'Développeur', 'Sviluppatore', 'Sviluppader'),
    'End the trailer': ('Trailer beenden', 'Arrêter la bande-annonce', 'Termina il trailer', 'Terminar il trailer'),
    'Watch again': ('Nochmals ansehen', 'Revoir', 'Guarda di nuovo', 'Guardar anc ina giada'),
    'The end': ('Ende', 'Fin', 'Fine', 'Fin'),
    'Over': ('Vorbei', 'Terminé', 'Finito', 'Terminà'),
    'Sound on': ('Ton an', 'Son activé', 'Audio attivo', 'Tun activà'),
    'Sound off': ('Ton aus', 'Son coupé', 'Audio spento', 'Tun deactivà'),
    'Tap for sound': ('Tippen für Ton', 'Touchez pour le son', 'Tocca per l’audio', 'Tutgar per tun'),
    'This simulator has no trailers yet – update it.': ('Dieser Simulator kennt die Trailer noch nicht – bitte aktualisieren.',
                                                        'Ce simulateur ne connaît pas encore les bandes-annonces – mets-le à jour.',
                                                        'Questo simulatore non conosce ancora i trailer – aggiornalo.',
                                                        'Quest simulatur na conuscha anc betg ils trailers – actualisescha el.'),
    'The simulator is busy: {w}': ('Der Simulator ist beschäftigt: {w}', 'Le simulateur est occupé : {w}', 'Il simulatore è occupato: {w}',
                                   'Il simulatur è occupà: {w}'),
    'Voice': ('Stimme', 'Voix', 'Voce', 'Vusch'),
    'recommended': ('empfohlen', 'recommandée', 'consigliata', 'recumandada'),
    'Automatic (recommended)': ('Automatisch (empfohlen)', 'Automatique (recommandée)', 'Automatica (consigliata)', 'Automatic (recumandà)'),
    'Listen': ('Anhören', 'Écouter', 'Ascolta', 'Tadlar'),
    'Speed': ('Tempo', 'Vitesse', 'Velocità', 'Tempo'),
    'No voice for this language on this device.': ('Dieses Gerät hat keine Stimme für diese Sprache.', 'Cet appareil n’a pas de voix pour cette langue.',
                                                    'Questo dispositivo non ha una voce per questa lingua.', 'Quest apparat n’ha nagina vusch per quest linguatg.'),
    'Better voices: iPad → Settings → Accessibility → Spoken Content → Voices → English → download «Premium».': ('Bessere Stimmen: iPad → Einstellungen → Bedienungshilfen → Gesprochene Inhalte → Stimmen → Deutsch → «Premium» laden.',
                          'Meilleures voix : iPad → Réglages → Accessibilité → Contenu énoncé → Voix → Français → télécharger « Premium ».',
                          'Voci migliori: iPad → Impostazioni → Accessibilità → Contenuto letto ad alta voce → Voci → Italiano → scarica «Premium».',
                          'Meglras vuschs: iPad → Einstellungen → Bedienungshilfen → Gesprochene Inhalte → Stimmen → Deutsch → chargiar «Premium».'),
}
for _k, _v in _HX_TRL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
_SPK_KEYS = ['Tap for sound', 'Voice', 'recommended', 'Automatic (recommended)', 'Listen', 'Speed', 'No voice for this language on this device.', 'Better voices: iPad → Settings → Accessibility → Spoken Content → Voices → English → download «Premium».']
_TRL_KEYS = list(_HX_TRL) + ["Full screen", "Back", "The valley is being prepared …", "The 3D simulator is not connected."]

# the Vorführung (639m) gets the same: the button in its bar, the new sentences read aloud, silent on pause, screen awake
VF_PAGE = VF_PAGE.replace('<button type="button" class="sec" onclick="vfFull()"', '<button type="button" class="sec spk-btn" onclick="spkToggle()">🔇</button>\n    <button type="button" class="sec" onclick="vfFull()"', 1)
VF_PAGE = VF_PAGE.replace("/*VFDE*/\n", "/*VFDE*/\n" + SPK_JS, 1)
VF_PAGE = VF_PAGE.replace('HIDE_T = setTimeout(() => { if (!S.pause) b.classList.add("off"); }, 4000); }',
                          'HIDE_T = setTimeout(() => { if (!S.pause && !SPK.pop) b.classList.add("off"); }, 4000); }', 1)
VF_PAGE = VF_PAGE.replace("function vfPaint(j) {\n  S = j || {};", "function vfPaint(j) {\n  S = j || {};\n  spkTick(S, !!S.pause, !!S.laeuft);", 1)
_VF_KEYS.extend(["Sound on", "Sound off"] + _SPK_KEYS)
_TRL_DE_JS = json.dumps({k: DE.get(k, k) for k in ("Trailer Grossvater", "Trailer Maggie", "Vorführung", "Developer")}, ensure_ascii=False)

# Settings → Developer (web 530 devExtras): the two trailers on top of the list (the window 639c: see below)
WEB_PAGE = WEB_PAGE.replace('[["🧪", "Test bench and test run", "/sim#c-test"]',
                            '[["🎬", "Trailer Grossvater", "/sim/trailer?id=grossvater"], ["🎬", "Trailer Maggie", "/sim/trailer?id=maggie"], '
                            '["🧪", "Test bench and test run", "/sim#c-test"]', 1)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + _TRL_DE_JS + ");</script></body>", 1)

# the tab «Sim»: on top the card «🛠 Entwickler» (no fold card: the links are always visible, also with «Nur Gruppen») (only the owner with the developer area: /api/ui_simple dev + /api/trailer not 403)
TRL_SIM_CARD = """<div class="sc wide" id="c-devquick" hidden>
    <h2 style="margin:0 0 8px"><span>🛠</span> <span data-i18n="Developer">Developer</span></h2>
    <div class="row2" style="display:flex;gap:8px;flex-wrap:wrap">
      <a class="btn sec" href="/sim/trailer?id=grossvater" style="flex:1 1 180px;text-align:left">🎬 <span data-i18n="Trailer Grossvater">Trailer Grossvater</span> ›</a>
      <a class="btn sec" href="/sim/trailer?id=maggie" style="flex:1 1 180px;text-align:left">🎬 <span data-i18n="Trailer Maggie">Trailer Maggie</span> ›</a>
      <a class="btn sec" href="/sim/vorfuehrung" style="flex:1 1 180px;text-align:left">🎬 <span data-i18n="Vorführung">Vorführung</span> ›</a>
    </div>
  </div>
  """
TRL_SIMJS = """<script>
(function trlQuick() {
  try { Object.assign(I18N.de, /*TRLDE*/{}); } catch (e) {}
  const c = document.getElementById("c-devquick"); if (!c) return;
  Promise.all([fetch("/api/ui_simple?page=sim").then(x => x.json()).catch(() => ({})), fetch("/api/trailer", {cache: "no-store"}).then(x => x.status).catch(() => 403)])
    .then(([u, st]) => { c.hidden = !(u && u.dev) || st === 403; if (!c.hidden) try { applyI18n(); } catch (e) {} });
})();
</script>"""
SIM_PAGE = SIM_PAGE.replace('<main class="simp">\n', '<main class="simp">\n  ' + TRL_SIM_CARD, 1)
SIM_PAGE = SIM_PAGE.replace("</body>", TRL_SIMJS.replace("/*TRLDE*/{}", _TRL_DE_JS) + "</body>", 1)


def trl_page():
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in _TRL_KEYS}, ensure_ascii=False) + ");"
    return render_page(TRL_PAGE, "sim").replace("/*TLDE*/", js, 1).replace("/*SPKJS*/", SPK_JS, 1).replace("/*TAJS*/", TA_JS, 1)


_smalltv_routes_trl_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639n: /sim/trailer and /api/trailer (550 calls smalltv_routes once)
    _smalltv_routes_trl_base(app, reply, body)
    from flask import Response

    @app.route("/sim/trailer")
    def trl_page_():
        if not nacht_may(_nacht_role()):
            return Response(tr("Only the owner can do this."), 403)
        return Response(trl_page(), mimetype="text/html")

    @app.route("/api/trailer", methods=["GET", "POST"])
    def api_trailer():
        own = nacht_may(_nacht_role())
        from flask import request
        if request.method == "GET":
            if not own:
                return reply({"ok": False, "error": tr("Only the owner can do this.")}, 403)
            return reply(trl_plan() if request.args.get("plan") == "1" else trl_info())
        r = trl_do(body(), own)
        code = r.pop("code", None)
        return reply(r, code) if code else reply(r)

    @app.route("/sim/trailer_ton/<nm>.wav")
    def trl_ton_(nm):                                      # one sound of the trailer (simulator /trailer_ton/<nm>.wav)
        if not nacht_may(_nacht_role()):
            return Response(tr("Only the owner can do this."), 403)
        if not CFG.get("sim_on") or not TRL_TON_RE.match(nm or ""):
            return Response("no", 404)
        try:
            b_, _h = _sim_get("/trailer_ton/" + nm + ".wav", 8.0)
        except Exception:
            return Response("simulator not reachable", 502)
        mt_ = "audio/mpeg" if b_[:3] == b"ID3" or b_[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") else "audio/wav"
        return Response(b_, mimetype=mt_, headers={"Cache-Control": "private, max-age=3600"})


if GUI_OK:                                                # the window: the two trailers in the developer part (639c)
    _trl_tk_build_section_base = App._build_section

    def _trl_tk_build_section(self, sec, sbody, settings_parent=None):
        r = _trl_tk_build_section_base(self, sec, sbody, settings_parent)
        if sec == "Developer":
            for tid, nm in (("grossvater", "Trailer Grossvater"), ("maggie", "Trailer Maggie")):
                ttk.Button(sbody, text="🎬 " + tr(nm) + " ›", command=lambda u="/sim/trailer?id=" + tid: self._open_page(u)).pack(fill="x", pady=(4, 0))
        return r

    # wraps: App._build_section (after 639m)
    App._build_section = _trl_tk_build_section


def trl_selftest():
    keep = CFG.get("sim_on")
    try:
        CFG["sim_on"] = False
        assert not trl_info()["ok"] and not trl_do({"do": "start", "id": "maggie"})["ok"]
        assert trl_do({"do": "start", "id": "maggie"}, owner=False).get("code") == 403
        assert trl_do({"do": "rm"}).get("code") == 400
        CFG["sim_on"] = True
        assert trl_do({"do": "start", "id": "x"}).get("code") == 400
        _sc = globals()["sim_control"]; asked = []
        globals()["sim_control"] = lambda d_: (asked.append(d_), {"ok": True, "loading": True})[1]
        try:
            assert trl_do({"do": "start", "id": "maggie"})["ok"] and asked[-1]["action"] == "trailer" and asked[-1]["id"] == "maggie"
            assert trl_do({"do": "stop"})["ok"] and asked[-1] == {"action": "trailer", "do": "stop"}
        finally:
            globals()["sim_control"] = _sc
    finally:
        CFG["sim_on"] = keep
    html = trl_page()
    assert "/sim/view.jpg?" in html and "bare=1&" in html and "/api/trailer" in html and "<!--NAV-->" not in html
    assert 'id="c-devquick"' in SIM_PAGE and "/sim/trailer?id=maggie" in SIM_PAGE and "/sim/vorfuehrung" in SIM_PAGE
    assert SIM_PAGE.index('id="c-devquick"') < SIM_PAGE.index('id="c-conn"')
    assert "/sim/trailer?id=grossvater" in WEB_PAGE
    assert "speechSynthesis" in html and "spkTick(S" in html and "wakeLock" in html
    assert "spk-tap" in html and "spkUnlock" in html and "taSync(S)" in html and "/sim/trailer_ton/" in html and "/api/trailer?plan=1" in html
    assert "bare ? \"bare=1&\"" in html                    # the browser picture without the PC's buttons only while the film runs
    assert TRL_TON_RE.match("pad_ruhig") and not TRL_TON_RE.match("../x")
    assert "TA.schl[nm]" in html and "createDynamicsCompressor" in html and "x.loopStart" in html
    assert "voiceschanged" in html and "spk-vbtn" in html and "SPK_GOOD" in html and "!SPK.pop" in html and "Stimme" in html
    vh = vf_page()
    assert "spkTick(S, !!S.pause" in vh and "spk-btn" in vh and "Ton an" in vh and "!SPK.pop" in vh and "Premium" in vh
    assert "spk-tap" in vh and "Tippen für Ton" in vh and "S.laeuft ? \"bare=1&\"" in vh
    for L in ("fr", "it", "rm"):
        assert TRX[L].get("End the trailer"), L
    return "Trailer: page, owner only, commands to the simulator, card on top of «Sim», entries"


SELFTEST_EXTRA.append(("Trailer der Geschichten (page /sim/trailer, owner only)", trl_selftest))
