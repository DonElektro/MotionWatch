#@ MoveEye – Teil 139: Makeover – Simulator-Zentrale, Startseiten-Kachel, Kachel-Steuerung fürs Handy. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.4 (Makeover-Punkte 3, 4, 7):
#  3  Startseite: Kachel «Simulation» (nur wenn der Simulator an ist) - kleines Livebild, Szene, Uhrzeit, Wetter, Besucher;
#     antippen = die Kachel-Steuerung.
#  4  Kachel-Steuerung: grosse Kacheln statt Schalterlisten - Szene · Tageszeit · Wetter · Besuch schicken · Überraschungsnacht ·
#     Vorlagen (am PC) · Spiel · Tests · Tagebuch. Ein Tippen öffnet die Auswahl, ein zweites führt es aus.
#  7  Simulator-Zentrale: dieselben Kacheln gross oben auf der Simulator-Seite - alles an einem Ort.
# Der Zustand kommt von /api/simhub (zusammengefasst aus GET /control des Simulators, 3 s zwischengespeichert).
# ----------------------------------------------------------------------------
_SIMHUB = {"t": 0.0, "d": None}

SIMHUB_VISITS = [("person", "🚶"), ("burglar", "🥷"), ("child", "🧒"), ("dogwalk", "🐕"), ("fox", "🦊"), ("deer", "🦌"), ("cat", "🐈"),
                 ("boar", "🐗"), ("hedgehog", "🦔"), ("cyclist", "🚲"), ("courier", "🍕"), ("car", "🚗")]


def sim_hub(force=False):
    """a short summary of the simulator for the tiles"""
    now = time.time()
    if not CFG.get("sim_on"):
        return {"on": False}
    if not force and _SIMHUB["d"] is not None and now - _SIMHUB["t"] < 3.0:
        return _SIMHUB["d"]
    d = {"on": True, "ok": False}
    try:
        r = sim_control(None)
        vals = {c.get("id"): c.get("value") for c in r.get("controls") or [] if isinstance(c, dict)}
        st = str(r.get("status") or "")
        m = re.search(r"Besucher (\d+)", st)
        h = float(vals.get("hour") or 0)
        wx = str(vals.get("weather") or "")
        d.update(ok=True, name=str(r.get("name") or ""), scene=str(r.get("scenario") or ""), status=st,
                 scenes=[{"id": s.get("id"), "name": str(s.get("name") or "").replace(" (3D)", "")} for s in r.get("scenarios") or []][:40],
                 hour=h, clock="%02d:%02d" % (int(h), int(round((h % 1) * 60)) % 60), dark=" Nacht " in st or st.find("· Nacht ·") >= 0,
                 weather=wx, ambient=vals.get("ambient"), visitors=int(m.group(1)) if m else None, surprise=bool(vals.get("surprise_on")),
                 game=r.get("game") or {}, has={k: k in vals for k in ("surprise_on", "weather", "hour", "spawn_person", "thief")})
    except Exception as e:
        d["msg"] = str(e)[:80]
    _SIMHUB.update(t=now, d=d)
    return d


def sim_hub_do(a, v=None):
    """one tile action -> the simulator. Returns (ok, error)"""
    try:
        if a == "scene":
            r = sim_control({"action": "scenario", "id": str(v)[:40]})
        elif a == "hour":
            r = sim_control({"action": "set", "id": "hour", "value": max(0.0, min(23.75, float(v)))})
        elif a == "weather":
            r = sim_control({"action": "set", "id": "weather", "value": str(v)[:12]})
        elif a == "visit":
            k = str(v)[:20]
            r = sim_control({"action": "press", "id": {"car": "car", "burglar": "thief", "dogwalk": "dogwalk"}.get(k, "spawn_" + k)})
        elif a == "surprise":
            r = sim_control({"action": "set", "id": "surprise_on", "value": bool(v)})
        elif a == "templates":
            r = sim_control({"action": "templates", "do": "open", "tab": 0})
        else:
            return False, "unknown action"
        _SIMHUB["t"] = 0.0
        return bool(r.get("ok", True)), str(r.get("error") or "")
    except Exception as e:
        return False, "simulator not reachable"


SIMHUB_CSS = r"""
.shub{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px}
.shub .st{display:flex;flex-direction:column;align-items:flex-start;gap:3px;padding:10px;border-radius:14px;border:1px solid var(--line,#1f2b3a);
  background:var(--panel2,#151e2b);color:var(--txt,#e8eef5);font:inherit;text-align:left;cursor:pointer;min-height:76px;transition:transform .12s,border-color .12s}
.shub .st:hover{border-color:var(--acc,#3b8cff)}.shub .st:active{transform:scale(.97)}
.shub .st i{font-style:normal;font-size:24px;line-height:1}.shub .st b{font-size:13px;hyphens:auto;overflow-wrap:anywhere}.shub .st small{font-size:11px;color:var(--mut,#8a9bb0)}
.shub .st.on{border-color:#f59a4a;box-shadow:0 0 0 1px #f59a4a inset}
.shsheet{margin-top:8px;padding:10px;border-radius:14px;background:var(--panel,#111822);border:1px solid var(--line,#1f2b3a);display:flex;flex-wrap:wrap;gap:6px}
.shsheet button{flex:1 1 auto;min-width:84px}.shsheet .shrow{display:flex;gap:6px;width:100%;align-items:center}
.stile{display:flex;gap:10px;align-items:stretch;padding:10px;border-radius:16px;border:1px solid #f59a4a;background:linear-gradient(135deg,rgba(245,154,74,.12),transparent 60%);cursor:pointer}
.stile img{width:132px;height:74px;object-fit:cover;border-radius:10px;background:#000;flex:0 0 auto}
.stile .sti{display:flex;flex-direction:column;gap:2px;min-width:0;font-size:13px}.stile .sti b{font-size:14px}.stile .sti span{color:var(--mut,#8a9bb0)}
"""

SIMHUB_JS = r"""
(function () {
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || "de"; } catch (e) { return "de"; } };
  const DE = {"Simulation": "Simulation", "Scene": "Szene", "Time of day": "Tageszeit", "Weather": "Wetter", "Send a visitor": "Besuch schicken",
    "Surprise night": "Überraschungsnacht", "Templates": "Vorlagen", "Game": "Spiel", "Tests": "Tests", "Diary": "Tagebuch", "on": "an", "off": "aus",
    "Morning": "Morgen", "Noon": "Mittag", "Evening": "Abend", "Night": "Nacht", "clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee",
    "visitors": "Besucher", "Opens on the PC": "Öffnet sich am PC", "Simulator not reachable": "Simulator nicht erreichbar", "Simulator centre": "Simulator-Zentrale",
    "Tap = control": "Antippen = steuern", "person": "Person", "burglar": "Dieb", "child": "Kind", "dogwalk": "Hund", "fox": "Fuchs", "deer": "Reh", "cat": "Katze",
    "boar": "Wildschwein", "hedgehog": "Igel", "cyclist": "Velo", "courier": "Kurier", "car": "Auto", "sent": "geschickt", "Test run, test bench": "Testlauf, Prüfstand",
    "Play on the phone": "Mitspielen mit dem Handy", "Visits and detection": "Besuche und Erkennung", "now": "jetzt"};
  const tt = k => (typeof t === "function" && t(k) !== k) ? t(k) : (L() === "en" ? k : (DE[k] || k));
  const WX = [["clear", "☀"], ["cloudy", "☁"], ["rain", "🌧"], ["fog", "🌫"], ["snow", "❄"]];
  const VIS = __VIS__;
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const say = m => { if (typeof toast === "function") toast(m); };
  let H = null, open = "";
  const act = async (a, v) => { try { const r = await (await fetch("/api/simhub", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({a: a, v: v})})).json();
      if (r.hub) H = r.hub; if (!r.ok) say("⚠ " + (r.error || tt("Simulator not reachable"))); paintAll(); return r; } catch (e) { say("⚠ " + tt("Simulator not reachable")); } };
  const wxIcon = w => (WX.find(x => x[0] === w) || ["", "☁"])[1];
  function sheet(box, kind) {
    const s = E("div", "shsheet");
    if (kind === "scene") (H.scenes || []).forEach(x => { const b = E("button", x.id === H.scene ? "" : "sec", x.name); b.type = "button"; b.onclick = () => act("scene", x.id); s.appendChild(b); });
    if (kind === "hour") { [["Morning", 7], ["Noon", 13], ["Evening", 19.5], ["Night", 23]].forEach(([n, h]) => { const b = E("button", "sec", tt(n) + " " + String(Math.floor(h)).padStart(2, "0") + ":" + (h % 1 ? "30" : "00")); b.type = "button"; b.onclick = () => act("hour", h); s.appendChild(b); });
      const r = E("div", "shrow"), i = E("input"); i.type = "range"; i.min = 0; i.max = 23.75; i.step = 0.25; i.value = H.hour || 12; i.style.flex = "1"; const o = E("b", "", H.clock || "");
      i.oninput = () => { o.textContent = String(Math.floor(i.value)).padStart(2, "0") + ":" + String(Math.round(i.value % 1 * 60)).padStart(2, "0"); }; i.onchange = () => act("hour", +i.value); r.append(i, o); s.appendChild(r); }
    if (kind === "weather") WX.forEach(([k, ic]) => { const b = E("button", k === H.weather ? "" : "sec", ic + " " + tt(k)); b.type = "button"; b.onclick = () => act("weather", k); s.appendChild(b); });
    if (kind === "visit") VIS.forEach(([k, ic]) => { const b = E("button", "sec", ic + " " + tt(k)); b.type = "button"; b.onclick = async () => { const r = await act("visit", k); if (r && r.ok) say(ic + " " + tt("sent")); }; s.appendChild(b); });
    box.appendChild(s);
  }
  function tiles(box, full) {
    const g = E("div", "shub");
    const T = [["scene", "🗺", tt("Scene"), ((H.scenes || []).find(x => x.id === H.scene) || {}).name || H.scene || "–"],
      ["hour", H.dark ? "🌙" : "☀", tt("Time of day"), H.clock || "–"],
      ["weather", wxIcon(H.weather), tt("Weather"), tt(H.weather || "–") + (H.ambient != null ? " · " + Math.round(H.ambient) + " °C" : "")],
      ["visit", (window.EVI || {}).person || "🚶", tt("Send a visitor"), (H.visitors != null ? H.visitors + " " + tt("visitors") + " " + tt("now") : "")],
      ["surprise", "🎲", tt("Surprise night"), H.surprise ? tt("on") : tt("off")]];
    if (full) T.push(["templates", "🧩", tt("Templates"), tt("Opens on the PC")], ["game", "🎮", tt("Game"), tt("Play on the phone")],
      ["tests", "🧪", tt("Tests"), tt("Test run, test bench")], ["diary", "📔", tt("Diary"), tt("Visits and detection")]);
    T.forEach(([k, ic, n, sub]) => { const b = E("button", "st" + (open === k || (k === "surprise" && H.surprise) ? " on" : "")); b.type = "button";
      b.append(E("i", "", ic), E("b", "", n), E("small", "", sub));
      b.onclick = () => { if (k === "surprise") return act("surprise", !H.surprise); if (k === "templates") return act("templates").then(r => r && r.ok && say("🧩 " + tt("Opens on the PC")));
        if (k === "game") return location.href = "/sim#c-game"; if (k === "tests") return location.href = "/sim#c-test"; if (k === "diary") return location.href = "/diary#simcard";
        open = open === k ? "" : k; paintAll(); };
      g.appendChild(b); });
    box.appendChild(g); if (open) sheet(box, open);
  }
  function paintTile(el_) {
    el_.hidden = !(H && H.on); if (!H || !H.on) return; el_.textContent = "";
    const top = E("div", "stile"), im = E("img"); im.alt = ""; im.src = "/sim/view.jpg?w=320&r=" + Date.now();
    const i = E("div", "sti"); i.append(E("b", "", "🧪 " + tt("Simulation") + (H.ok ? "" : " ⚠")), E("div", "", H.ok ? (((H.scenes || []).find(x => x.id === H.scene) || {}).name || H.scene) : tt("Simulator not reachable")),
      E("span", "", H.ok ? (H.dark ? "🌙 " : "☀ ") + H.clock + " · " + wxIcon(H.weather) + " " + tt(H.weather || "") + (H.visitors != null ? " · " + H.visitors + " " + tt("visitors") : "") : ""), E("span", "", tt("Tap = control")));
    top.append(im, i); top.onclick = () => { el_.dataset.open = el_.dataset.open ? "" : "1"; paintAll(); }; el_.appendChild(top);
    if (el_.dataset.open && H.ok) { const w = E("div"); w.style.marginTop = "8px"; tiles(w, false); el_.appendChild(w); }
  }
  function paintFull(el_) { el_.textContent = ""; if (!H || !H.on) { el_.hidden = true; return; } el_.hidden = false;
    if (!H.ok) { el_.appendChild(E("div", "mut", "⚠ " + tt("Simulator not reachable") + (H.msg ? " (" + H.msg + ")" : ""))); return; } tiles(el_, true); }
  function paintAll() { document.querySelectorAll("[data-simhub]").forEach(x => x.dataset.simhub === "full" ? paintFull(x) : paintTile(x)); }
  async function load() { if (!document.querySelector("[data-simhub]")) return; try { H = await (await fetch("/api/simhub")).json(); } catch (e) { return; }
    const ti = document.querySelector('[data-simhub="tile"] img'); if (ti && !document.hidden) ti.src = "/sim/view.jpg?w=320&r=" + Date.now();
    if (!document.activeElement || document.activeElement.type !== "range") paintAll(); }
  document.addEventListener("DOMContentLoaded", () => { load(); setInterval(load, 6000); });
})();
"""


def simhub_head():
    return "<style>" + SIMHUB_CSS + "</style><script>" + SIMHUB_JS.replace("__VIS__", json.dumps(SIMHUB_VISITS, ensure_ascii=False)) + "</script>"


# ---- 2.96.4 (Makeover-Punkt 5): Kino-Modus /kino - Vollbild für TV / Beamer: Livebild mit den Rahmen, Uhr, Zustand und
# ein Laufband mit den letzten Ereignissen (die gleichen Symbole wie überall). Mit Tastatur: F = Vollbild, Esc = zurück.
def kino_state():
    with LOCK:
        evs = [e for e in STATE.get("events", []) if e.get("imp") or e.get("kind") in ("person", "ai", "car")][:8]
    return {"name": CFG.get("device_name") or "MoveEye", "version": APP_VERSION, "persons": STATE.get("persons", 0),
            "armed": bool(is_armed()), "rec": bool(STATE.get("recording")), "sim": bool(CFG.get("sim_on")),
            "events": [{"t": e["t"][:5], "i": LOG_ICON.get(e["kind"], "·"), "x": tr(e["text"]) if isinstance(e.get("text"), str) else ""} for e in evs]}


KINO_PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye · Kino</title><style>
html,body{margin:0;height:100%;background:#000;color:#e8eef5;font-family:system-ui,sans-serif;overflow:hidden}
#v{position:fixed;inset:0;width:100%;height:100%;object-fit:contain}
.top{position:fixed;top:0;left:0;right:0;display:flex;justify-content:space-between;align-items:center;padding:14px 22px;
  background:linear-gradient(#000c,#0000);font-size:clamp(14px,1.6vw,24px)}
.top b{font-weight:700;letter-spacing:.02em}.pill{padding:3px 12px;border-radius:99px;background:#111822cc;margin-left:8px}
.pill.red{background:#ff4d4d;color:#fff;animation:bl 1s infinite}.pill.org{background:#f59a4a;color:#1a1206}
@keyframes bl{50%{opacity:.55}}
#clock{font-variant-numeric:tabular-nums;font-size:clamp(18px,2.4vw,36px);font-weight:600}
.tick{position:fixed;left:0;right:0;bottom:0;padding:10px 0;background:linear-gradient(#0000,#000d);white-space:nowrap;overflow:hidden;font-size:clamp(14px,1.5vw,22px)}
.tick div{display:inline-block;padding-left:100%;animation:run 40s linear infinite}.tick span{margin-right:48px}
@keyframes run{to{transform:translateX(-100%)}}
.hint{position:fixed;right:16px;bottom:56px;font-size:12px;opacity:.5}
</style></head><body>
<img id="v" src="/video_feed" alt="">
<div class="top"><div><b id="nm">MoveEye</b><span id="st"></span></div><div id="clock"></div></div>
<div class="tick"><div id="tk"></div></div><div class="hint">F = Vollbild · Esc = zurück</div>
<script>
const $ = s => document.querySelector(s);
const pad = n => String(n).padStart(2, "0");
setInterval(() => { const d = new Date(); $("#clock").textContent = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds()); }, 1000);
async function load() { try { const r = await (await fetch("/api/kino")).json();
  $("#nm").textContent = r.name; const st = $("#st"); st.textContent = "";
  const P = (txt, cls) => { const s = document.createElement("span"); s.className = "pill " + (cls || ""); s.textContent = txt; st.appendChild(s); };
  if (r.sim) P("🧪 SIMULATION", "org"); P(r.armed ? "🛡 Schutz an" : "Schutz aus"); if (r.persons) P("🚶 " + r.persons, "red"); if (r.rec) P("● REC", "red");
  const tk = $("#tk"), txt = r.events.map(e => e.t + " " + e.i + " " + e.x).join("|");
  if (tk.dataset.s !== txt) { tk.dataset.s = txt; tk.textContent = ""; (r.events.length ? r.events : [{t: "", i: "", x: "–"}]).forEach(e => { const s = document.createElement("span"); s.textContent = (e.t ? e.t + "  " : "") + e.i + " " + e.x; tk.appendChild(s); }); }
  } catch (e) {} }
load(); setInterval(load, 3000);
$("#v").onerror = () => setTimeout(() => { $("#v").src = "/video_feed?r=" + Date.now(); }, 2000);
document.addEventListener("keydown", e => { if (e.key === "f" || e.key === "F") (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {});
  if (e.key === "Escape" && !document.fullscreenElement) location.href = "/"; });
document.body.ondblclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {});
</script></body></html>"""
