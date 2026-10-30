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
                 scenes=[{"id": s.get("id"), "name": str(s.get("name") or "").replace(" (3D)", ""), "en": str(s.get("en") or "")} for s in r.get("scenarios") or []][:40],
                 hour=h, clock="%02d:%02d" % (int(h), int(round((h % 1) * 60)) % 60), dark=" Nacht " in st or st.find("· Nacht ·") >= 0,
                 weather=wx, ambient=vals.get("ambient"), visitors=int(m.group(1)) if m else None, surprise=bool(vals.get("surprise_on")), dev2=bool(vals.get("dev2_on")), dev2_place=str(vals.get("dev2_place") or ""), zones3d=bool(vals.get("show_zones3d")), det3d=bool(vals.get("show_det3d")),
                 twin_ok="show_zones3d" in vals,
                 game=r.get("game") or {}, has={k: k in vals for k in ("surprise_on", "weather", "hour", "spawn_person", "thief")})
    except Exception as e:
        d["msg"] = str(e)[:80]
    d["handover"] = list(FLEET.get("handover") or [])[:3]   # 2.96.7: makeover 16
    if d.get("ok"):
        try:
            d["rover"] = (sim_control({"action": "rover"}) or {}).get("rover")
        except Exception:
            d["rover"] = None
        d["rover_alarm"] = bool(CFG.get("rover_alarm"))
    d["demo"] = {"busy": DEMO_RUN["busy"], "i": DEMO_RUN["i"], "n": DEMO_RUN["n"]}
    d["simple"] = page_simple("sim")                      # 2.98.14: «Simple» shows the assistant instead of the single tools
    d["tune"] = {"busy": TUNEA["busy"], "step": TUNEA["step"], "last": bool(TUNEA.get("last"))}
    d["devices"] = len(CFG.get("fleet") or [])
    if d.get("ok"):                                         # the twin, back from the simulator (place, mast)
        try:
            d["twin"] = sim_twin_info() if d.get("twin_ok") else {}
        except Exception:
            d["twin"] = {}
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
        elif a == "dev2":
            r = sim_control({"action": "set", "id": "dev2_on", "value": bool(v)})
        elif a == "dev2_place":
            r = sim_control({"action": "set", "id": "dev2_place", "value": str(v)[:12]})
        elif a == "rover":
            if v == "auto_on" or v == "auto_off":
                CFG["rover_alarm"] = v == "auto_on"; save_settings(); r = {"ok": True}
            else:
                r = sim_control({"action": "rover", "do": str(v)[:10], "on": True}) if v != "patrol_off" else sim_control({"action": "rover", "do": "patrol", "on": False})
        elif a == "twin":
            r = sim_twin()
        elif a == "overlay":
            r = sim_control({"action": "set", "id": str(v.get("id")), "value": bool(v.get("on"))}) if isinstance(v, dict) and v.get("id") in ("show_zones3d", "show_det3d") else {"ok": False}
        else:
            return False, "unknown action"
        _SIMHUB["t"] = 0.0
        return bool(r.get("ok", True)), str(r.get("error") or "")
    except Exception as e:
        return False, "simulator not reachable"


SIMHUB_CSS = r"""
.shubh{font:700 11px/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--mut,#8a9bb0);margin:14px 2px 6px}
.shubh:first-child{margin-top:2px}
.shub{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px}
.shub .st{display:flex;flex-direction:column;align-items:flex-start;gap:3px;padding:10px;border-radius:14px;border:1px solid var(--line,#1f2b3a);
  background:var(--panel2,#151e2b);color:var(--txt,#e8eef5);font:inherit;text-align:left;cursor:pointer;min-height:76px;transition:transform .12s,border-color .12s}
.shub .st:hover{border-color:var(--acc,#3b8cff)}.shub .st:active{transform:scale(.97)}
.shub .st i{font-style:normal;font-size:24px;line-height:1}.shub .st b{font-size:13px;hyphens:auto;overflow-wrap:anywhere}.shub .st small{font-size:11px;color:var(--mut,#8a9bb0)}
.shub .st.on{border-color:#f59a4a;box-shadow:0 0 0 1px #f59a4a inset}
.shsheet{margin-top:8px;padding:10px;border-radius:14px;background:var(--panel,#111822);border:1px solid var(--line,#1f2b3a);display:flex;flex-wrap:wrap;gap:6px}
.shsheet.trs{display:block}.shsheet #tr-box button{flex:0 1 auto}
.shsheet button{flex:1 1 auto;min-width:84px}.shsheet .shrow{display:flex;gap:6px;width:100%;align-items:center}
.stile{display:flex;gap:10px;align-items:stretch;padding:10px;border-radius:16px;border:1px solid #f59a4a;background:linear-gradient(135deg,rgba(245,154,74,.12),transparent 60%);cursor:pointer}
.stile img{width:132px;height:74px;object-fit:cover;border-radius:10px;background:#000;flex:0 0 auto}
.stile .sti{display:flex;flex-direction:column;gap:2px;min-width:0;font-size:13px}.stile .sti b{font-size:14px}.stile .sti span{color:var(--mut,#8a9bb0)}
"""

SIMHUB_JS = r"""
(function () {
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || "de"; } catch (e) { return "de"; } };
  const DE = Object.assign({"Improve detection": "Erkennung verbessern", "step by step": "Schritt für Schritt", "World": "Welt", "Testing": "Testen", "Learning": "Lernen", "Playing": "Spielen", "Show all tools («Expert»)": "Alle Werkzeuge zeigen («Experte»)", "Only the assistant («Simple»)": "Nur den Assistenten («Einfach»)", "Day": "Tag", "Night": "Nacht"}, {"Try out": "Ausprobieren", "Learn & test": "Lernen & Testen", "MoveEye points": "MoveEye-Punkte", "points": "Punkte", "points-note": "Ein Konto für Spiel und echten Betrieb: blinde Flecken in Spielen gefunden (+5), Fehlalarm im Spiel entlarvt (+30), Übung gemacht (+50), Woche ohne Fehlalarm (+100), «Entdecker»: früher blinde Stellen werden jetzt erkannt (+50 je Stelle).", "Badges of the players": "Abzeichen der Spieler", "Calm week: no false alarm": "Ruhige Woche: kein Fehlalarm", "False alarm unmasked in a game": "Fehlalarm im Spiel entlarvt", "{n} blind spot(s) found in games": "{n} blinde Flecken in Spielen gefunden", "Explorer: {n} blind spot(s) fixed": "Entdecker: {n} blinde Flecken behoben", "Drill done: battery": "Übung gemacht: Akku", "Drill done: net": "Übung gemacht: WLAN", "Drill done: heat": "Übung gemacht: Hitze", "Drill done: cold": "Übung gemacht: Kälte"}, {"Simulation": "Simulation", "Scene": "Szene", "Time of day": "Tageszeit", "Weather": "Wetter", "Send a visitor": "Besuch schicken",
    "Surprise night": "Überraschungsnacht", "Templates": "Vorlagen", "Game": "Spiel", "Tests": "Tests", "Diary": "Tagebuch", "on": "an", "off": "aus",
    "Morning": "Morgen", "Noon": "Mittag", "Evening": "Abend", "Night": "Nacht", "clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee",
    "visitors": "Besucher", "Opens on the PC": "Öffnet sich am PC", "Simulator not reachable": "Simulator nicht erreichbar", "Simulator centre": "Simulator-Zentrale",
    "Tap = control": "Antippen = steuern", "person": "Person", "burglar": "Dieb", "child": "Kind", "dogwalk": "Hund", "fox": "Fuchs", "deer": "Reh", "cat": "Katze",
    "boar": "Wildschwein", "hedgehog": "Igel", "cyclist": "Velo", "courier": "Kurier", "car": "Auto", "sent": "geschickt", "Test run, test bench": "Testlauf, Prüfstand",
    "Play on the phone": "Mitspielen mit dem Handy", "Several devices": "Mehrere Geräte", "Blind spots": "Blinde Flecken", "recognised": "erkannt", "find them": "finden", "Night rehearsal": "Nacht-Generalprobe", "up to": "bis",
    "before arming": "vor dem Einschalten des Schutzes", "Thresholds automatic": "Schwellen automatisch", "day and night": "Tag und Nacht", "False alarm learning": "Fehlalarm-Lernen",
    "Weekly check": "Wochen-Check", "Find the blind spots (about 5 min)": "Blinde Flecken suchen (etwa 5 Min.)", "in the picture, not recognised": "im Bild, nicht erkannt", "found by players in the games": "von Spielern in den Spielen gefunden",
    "outside the picture": "ausserhalb des Bildes", "Rehearsal now (2 min)": "Generalprobe jetzt (2 Min.)", "By itself when arming": "Von selbst beim Einschalten des Schutzes",
    "Set the thresholds now (day + night)": "Schwellen jetzt einstellen (Tag + Nacht)", "autoth-note": "Die automatische Optimierung probiert Empfindlichkeit, Mindestgrösse, KI-Schwelle, Nacht- und Regen-Einstellungen aus – zuerst am Tag, dann in der Nacht. Eine Änderung bleibt nur, wenn sie klar besser ist.",
    "Re-enact every 👎 in the simulator": "Jedes 👎 im Simulator nachstellen", "fa-note": "Markierst du eine Aufnahme als Fehlalarm (mit Ursache), stellt der Simulator die Ursache nach und schaut 60 s zu. Meldet MoveEye wieder, kommen die Bilder als «keine Person» ins Training.",
    "Check learning pictures": "Lernbilder prüfen", "Game pictures for the training": "Spielbilder fürs Training", "doubtful (not used)": "zweifelhaft (nicht verwendet)",
    "Learning pictures checked": "Lernbilder geprüft", "moved to «doubtful»": "nach «zweifel» verschoben",
    "stays quiet": "bleibt ruhig", "alarm(s) – pictures kept for the training": "Alarm(e) – Bilder fürs Training behalten", "Every Sunday night": "Jeden Sonntag in der Nacht",
    "week-note": "Sonntags zur Stunde des Nacht-Tests ein Testlauf «standard». Ist er klar schlechter als letzte Woche, kommt ein Push.", "2nd device": "2. Gerät", "P_opposite": "gegenüber", "P_door": "bewacht Zelt / Tür", "P_bike": "bewacht Velo",
    "P_car": "bewacht Auto", "P_left": "links", "P_right": "rechts", "Rover": "Rover", "M_alarm": "fährt zum Alarm", "M_dock": "fährt zur Ladestation", "M_goto": "fährt hin",
    "patrols": "patrouilliert", "charging": "lädt", "ready": "bereit", "Statistics & versions": "Statistik & Versionen", "4 weeks, per version": "4 Wochen, pro Version",
    "Second device in the simulator": "Zweites Gerät im Simulator", "dev-note": "Ein zweites MoveEye verbindet sich mit Port 8785 des Simulators (z. B. eine zweite Kopie auf dem PC). Unter Kameras → Geräte hinzufügen: dann meldet MoveEye die Übergabe, wenn eine Person von einem Gerät zum anderen geht.",
    "Patrol": "Patrouille", "Drive to the alarm": "Zum Alarm fahren", "To the charger": "Zur Ladestation", "At a person alarm: drive there by itself": "Bei Personen-Alarm von selbst hinfahren",
    "rover-note": "Akku hält etwa 30 Minuten Fahrt; unter 20 % fährt der Rover von selbst zur Ladestation.",
    "Visits (blue) and persons recognised in % (green), 4 weeks": "Besuche (blau) und erkannte Personen in % (grün), 4 Wochen", "Per MoveEye version": "Pro MoveEye-Version", "test": "Test",
    "Your place": "Dein Platz", "Test inbox": "Test-Posteingang", "Drills": "Störfall-Übungen", "Battery, Wi-Fi, heat, cold": "Akku, WLAN, Hitze, Kälte",
    "Training night": "Trainings-Nacht", "A/B comparison": "A/B-Vergleich", "Which setting is better?": "Welche Einstellung ist besser?", "Messages here instead of the phone": "Meldungen hierhin statt aufs Handy",
    "Test the alarm chain": "Alarm-Kette testen", "Empty – nothing arrived yet": "Leer – noch nichts angekommen", "held back (offline), sent later": "zurückgehalten (offline), wird später gesendet",
    "Battery empty": "Akku leer", "Wi-Fi / internet gone": "WLAN / Internet weg", "Heat": "Hitze", "Cold": "Kälte", "Drill runs": "Übung läuft", "Last drill": "Letzte Übung",
    "how MoveEye reacted": "so hat MoveEye reagiert", "no reaction": "keine Reaktion", "Every night": "Jede Nacht", "Stop": "Stopp", "Start now": "Jetzt starten",
    "train-note": "Testläufe in 5 Szenen (Tag- und Nacht-Plan), dann die automatische Optimierung am schwächsten Plan, dann 300 Trainingsbilder auf dem PC des Simulators. Läuft nur, wenn nicht Schutz eingeschaltet. Bericht als Push am Schluss.",
    "Last training": "Letztes Training", "before": "vorher", "false alarms": "Fehlalarme", "kept": "übernommen", "training pictures": "Trainingsbilder",
    "ab-note": "Zweimal derselbe Testlauf: A mit den jetzigen Einstellungen, B mit der Änderung. B bleibt nur, wenn es klar besser ist (+3 Punkte).",
    "More sensitive": "Empfindlicher", "Less sensitive": "Weniger empfindlich", "AI stricter": "KI strenger", "AI more generous": "KI grosszügiger", "Also small objects": "Auch kleine Objekte",
    "Faster decision": "Schneller entscheiden", "B is better – kept": "B ist besser – übernommen", "A stays": "A bleibt", "Place, zones, patrol": "Ort, Zonen, Patrouille",
    "Zones in 3D": "Zonen in 3D", "mast": "Stange", "zones": "Zonen", "patrol points": "Patrouillen-Punkte", "Detection in 3D": "Erkennung in 3D", "The map opens at your place on the PC – confirm «Load this place»": "Am PC öffnet sich die Karte an deinem Ort – «Diesen Ort laden» bestätigen", "Visits and detection": "Besuche und Erkennung", "now": "jetzt"});
  const tt = k => (typeof t === "function" && t(k) !== k) ? t(k) : (L() === "en" ? k : (DE[k] || k));
  const scn = x => !x ? "" : (x.en && L() !== "de" ? tt(x.en) : x.name);     // 551: scene names in the language of the page (German from the simulator)
  const WX = [["clear", "☀"], ["cloudy", "☁"], ["rain", "🌧"], ["fog", "🌫"], ["snow", "❄"]];
  const VIS = __VIS__;
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const say = m => { if (typeof toast === "function") toast(m); };
  let H = null, open = "", HASHED = 0;
  const act = async (a, v) => { try { const r = await (await fetch("/api/simhub", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({a: a, v: v})})).json();
      if (r.hub) H = r.hub; if (!r.ok) say("⚠ " + (r.error || tt("Simulator not reachable"))); paintAll(); return r; } catch (e) { say("⚠ " + tt("Simulator not reachable")); } };
  const wxIcon = w => (WX.find(x => x[0] === w) || ["", "☁"])[1];
  function sheet(box, kind) {
    const s = E("div", "shsheet");
    if (kind === "scene") (H.scenes || []).forEach(x => { const b = E("button", x.id === H.scene ? "" : "sec", scn(x)); b.type = "button"; b.onclick = () => act("scene", x.id); s.appendChild(b); });
    if (kind === "hour") { [["Morning", 7], ["Noon", 13], ["Evening", 19.5], ["Night", 23]].forEach(([n, h]) => { const b = E("button", "sec", tt(n) + " " + String(Math.floor(h)).padStart(2, "0") + ":" + (h % 1 ? "30" : "00")); b.type = "button"; b.onclick = () => act("hour", h); s.appendChild(b); });
      const r = E("div", "shrow"), i = E("input"); i.type = "range"; i.min = 0; i.max = 23.75; i.step = 0.25; i.value = H.hour || 12; i.style.flex = "1"; const o = E("b", "", H.clock || "");
      i.oninput = () => { o.textContent = String(Math.floor(i.value)).padStart(2, "0") + ":" + String(Math.round(i.value % 1 * 60)).padStart(2, "0"); }; i.onchange = () => act("hour", +i.value); r.append(i, o); s.appendChild(r); }
    if (kind === "wide" && window.mwWide) window.mwWide.sheet(s, H, act);         // 591: the wide camera (picture, mount)
    if (kind === "parc" && window.mwParc) window.mwParc.sheet(s, H, act);         // 416: the tracking parcours
    if (kind === "weather") WX.forEach(([k, ic]) => { const b = E("button", k === H.weather ? "" : "sec", ic + " " + tt(k)); b.type = "button"; b.onclick = () => act("weather", k); s.appendChild(b); });
    if (kind === "visit") VIS.forEach(([k, ic]) => { const b = E("button", "sec", ic + " " + tt(k)); b.type = "button"; b.onclick = async () => { const r = await act("visit", k); if (r && r.ok) say(ic + " " + tt("sent")); }; s.appendChild(b); });
    if (["inbox", "drill", "train", "ab"].includes(kind)) labSheet(s, kind);
    if (kind === "devices") {
      s.appendChild(B((H.dev2 ? "✓ " : "") + tt("Second device in the simulator"), () => act("dev2", !H.dev2), H.dev2 ? "" : "sec"));
      ["opposite", "door", "bike", "car", "left", "right"].forEach(p => s.appendChild(B(tt("P_" + p), () => act("dev2_place", p), H.dev2_place === p ? "" : "sec")));
      s.appendChild(E("div", "mut", tt("dev-note")));
    }
    if (kind === "rover") { const R = H.rover || {};
      s.append(B("▶ " + tt("Patrol"), () => act("rover", "patrol")), B("⏹ " + tt("Stop"), () => act("rover", "patrol_off")), B("🚨 " + tt("Drive to the alarm"), () => act("rover", "alarm")),
        B("⚡ " + tt("To the charger"), () => act("rover", "dock")), B((H.rover_alarm ? "✓ " : "") + tt("At a person alarm: drive there by itself"), () => act("rover", H.rover_alarm ? "auto_off" : "auto_on"), H.rover_alarm ? "" : "sec"));
      s.appendChild(E("div", "mut", "🔋 " + (R.batt != null ? R.batt + " %" : "–") + (R.charging ? " · " + tt("charging") : "") + " · " + tt("rover-note")));
    }
    if (kind === "stats") statsSheet(s);
    if (kind === "tests") { const tb = document.getElementById("tr-box") || window._trBox;   // 2.98.23: the test run (470) lives here, no own card
      if (tb) { window._trBox = tb; s.classList.add("trs"); s.appendChild(tb); } else s.appendChild(E("div", "mut", "–")); }
    if (["blind", "rehearsal", "autoth", "falearn", "week", "points"].includes(kind)) learnSheet(s, kind);
    box.appendChild(s);
  }
  let LB = null, ST = null, LN = null;
  const learn = async (d) => { try { const r = d ? await (await fetch("/api/learn", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})).json()
      : await (await fetch("/api/learn")).json(); if (r && r.blind) LN = r; if (r && r.ok === false && r.error) say("⚠ " + r.error); paintAll(); return r; } catch (e) {} };
  function blindSvg(res, game) {
    const W = 300, Hh = 170, cx = W / 2, by = Hh - 10, k = (Hh - 20) / 30;
    let g = '<svg viewBox="0 0 ' + W + ' ' + Hh + '" style="width:100%;max-width:420px">';
    [10, 20, 30].forEach(r => { g += '<path d="M' + (cx - r * k) + ' ' + by + ' A' + r * k + ' ' + r * k + ' 0 0 1 ' + (cx + r * k) + ' ' + by + '" fill="none" stroke="#1f2b3a"/><text x="' + (cx + r * k - 2) + '" y="' + (by - 2) + '" font-size="8" fill="#8a9bb0" text-anchor="end">' + r + ' m</text>'; });
    (res.points || []).forEach(p => { const a = p.az * Math.PI / 180, x = cx + Math.sin(a) * p.d * k, y = by - Math.cos(a) * p.d * k;
      g += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="5" fill="' + (!p.inview ? "#5a6b80" : p.found ? "#3fcf6b" : "#ff4d4d") + '"/>'; });
    (game || []).forEach(p => { if (p.d > 30) return; const a = p.az * Math.PI / 180, x = cx + Math.sin(a) * p.d * k, y = by - Math.cos(a) * p.d * k;
      g += '<rect x="' + (x - 2.5).toFixed(1) + '" y="' + (y - 2.5).toFixed(1) + '" width="5" height="5" transform="rotate(45 ' + x.toFixed(1) + ' ' + y.toFixed(1) + ')" fill="#b46cff" opacity=".8"/>'; });
    return g + '<circle cx="' + cx + '" cy="' + by + '" r="6" fill="#f59a4a"/></svg>';
  }
  function learnSheet(s, kind) {
    if (!LN) { s.appendChild(E("div", "mut", "…")); learn(); return; }
    const bl = LN.blind;
    if (kind === "blind") { s.appendChild(B("▶ " + tt("Find the blind spots (about 5 min)"), () => learn({do: "blind"})));
      if (bl.last) { const c = E("div"); c.style.width = "100%"; c.innerHTML = blindSvg(bl.last, bl.game); s.append(c, E("div", "mut", "🟢 " + tt("recognised") + " · 🔴 " + tt("in the picture, not recognised") + " · ⚪ " + tt("outside the picture") + ((bl.game || []).length ? " · 🟣 " + tt("found by players in the games") : "")), E("b", "", "💡 " + (bl.last.tip || ""))); }
      else if ((bl.game || []).length) { const c = E("div"); c.style.width = "100%"; c.innerHTML = blindSvg({points: []}, bl.game); s.append(c, E("div", "mut", "🟣 " + tt("found by players in the games"))); } }
    if (kind === "rehearsal") { s.append(B("▶ " + tt("Rehearsal now (2 min)"), () => learn({do: "rehearsal"})), B((LN.rehearsal_on_arm ? "✓ " : "") + tt("By itself when arming"), () => learn({do: "set", key: "rehearsal_on_arm", on: !LN.rehearsal_on_arm}), LN.rehearsal_on_arm ? "" : "sec"));
      if (bl.rehearsal) { s.appendChild(E("b", "", "🌙 " + (bl.rehearsal.text || ""))); const c = E("div"); c.style.width = "100%"; c.innerHTML = blindSvg(bl.rehearsal); s.appendChild(c); } }
    if (kind === "autoth") { s.append(B("▶ " + tt("Set the thresholds now (day + night)"), () => learn({do: "autoth"})), E("div", "mut", tt("autoth-note")));
      const l = LN.autoth.last; if (l) l.res.forEach(r => s.appendChild(E("div", "mut", (r.plan === "night" ? "🌙 " : "☀ ") + (r.base != null ? r.base : "–") + " → " + (r.best != null ? r.best : "–") + " · " + tt("kept") + ": " + (r.kept.join(", ") || "–")))); }
    if (kind === "falearn") { s.append(B((LN.fa_learn_auto ? "✓ " : "") + tt("Re-enact every 👎 in the simulator"), () => learn({do: "set", key: "fa_learn_auto", on: !LN.fa_learn_auto}), LN.fa_learn_auto ? "" : "sec"), E("div", "mut", tt("fa-note")));
      (LN.falearn.last || []).forEach(r => s.appendChild(E("div", "mut", (r.ok ? "✅ " + tt("stays quiet") : "⚠ " + r.alarms + " " + tt("alarm(s) – pictures kept for the training") + " (" + r.pics + ")") + " · " + r.cause + " · " + r.name)));
      const fc = LN.facheck || {};                    // 2.98.38: the false alarms of the games, checked once more (148)
      s.append(B("🔍 " + tt("Check learning pictures"), () => learn({do: "facheck"}), "sec"),
        E("div", "mut", tt("Game pictures for the training") + ": " + (fc.game || 0) + " · " + tt("doubtful (not used)") + ": " + (fc.doubt || 0)));
      if (fc.last) s.appendChild(E("div", "mut", "✓ " + tt("Learning pictures checked") + ": " + fc.last.checked + " · " + tt("kept") + " " + fc.last.kept + " · " + tt("moved to «doubtful»") + " " + fc.last.moved)); }
    if (kind === "points") { const P = LN.points || {};               // 2.98.2: one account for games and real use
      s.append(E("b", "", "🏅 " + (P.total || 0) + " " + tt("points")), E("div", "mut", tt("points-note")));
      (P.log || []).forEach(x => s.appendChild(E("div", "mut", new Date(x.t * 1000).toLocaleDateString() + " · +" + x.n + " · " + tt(x.why.replace(/\d+/, "{n}")).replace("{n}", (x.why.match(/\d+/) || [""])[0]))));
      const B_ = P.badges || {}, names = Object.keys(B_);
      if (names.length) { s.appendChild(E("b", "", "🎖 " + tt("Badges of the players")));
        const BI = {ghost: "👻", fast: "⚡", snake: "🐍", hero: "🦸", gems: "💎", eagle: "🦅", bush: "🌳", first: "🥇", spotter: "🔍"};
        names.forEach(n => s.appendChild(E("div", "mut", n + ": " + Object.entries(B_[n]).map(([k, c]) => (BI[k] || k) + "×" + c).join("  ")))); } }
    if (kind === "week") { s.append(B((LN.week.on ? "✓ " : "") + tt("Every Sunday night"), () => learn({do: "set", key: "weekcheck_on", on: !LN.week.on}), LN.week.on ? "" : "sec"), E("div", "mut", tt("week-note")));
      (LN.week.runs || []).forEach(r => s.appendChild(E("div", "mut", new Date(r.t * 1000).toLocaleDateString() + " · " + r.score + " · v" + r.mw))); }
  }
  async function statsSheet(s) {
    if (!ST) { s.appendChild(E("div", "mut", "…")); try { ST = await (await fetch("/api/simstats")).json(); } catch (e) { return; } setTimeout(() => { ST = null; }, 60000); paintAll(); return; }
    const W = 320, Hh = 90, days = ST.days, bw = W / days.length;
    const svg = '<svg viewBox="0 0 ' + W + ' ' + (Hh + 14) + '" style="width:100%;max-width:560px">' + days.map((d, i) => { const h = d.rate == null ? 0 : d.rate / 100 * Hh;
      const v = Math.min(Hh, d.visits * 3); return '<rect x="' + (i * bw + 1) + '" y="' + (Hh - v) + '" width="' + (bw - 2) + '" height="' + v + '" fill="#3b8cff" opacity=".25"/>'
        + (d.rate == null ? "" : '<rect x="' + (i * bw + bw * .25) + '" y="' + (Hh - h) + '" width="' + (bw * .5) + '" height="' + h + '" fill="#3fcf6b"/>'); }).join("")
      + '<text x="0" y="' + (Hh + 12) + '" font-size="9" fill="#8a9bb0">' + days[0].d.slice(5) + '</text><text x="' + W + '" y="' + (Hh + 12) + '" font-size="9" fill="#8a9bb0" text-anchor="end">' + days[days.length - 1].d.slice(5) + '</text></svg>';
    const c = E("div"); c.style.width = "100%"; c.innerHTML = svg; s.append(E("b", "", tt("Visits (blue) and persons recognised in % (green), 4 weeks")), c);
    s.appendChild(E("div", "mut", ST.kinds.map(k => ((window.EVI || {})[k.person ? "person" : k.animal ? "animal" : "vehicle"] || "") + " " + k.k + " " + k.n).join(" · ") || "–"));
    s.appendChild(E("b", "", tt("Per MoveEye version")));
    const tb = E("div"); tb.style.cssText = "width:100%;display:flex;flex-direction:column;gap:4px";
    (ST.versions.length ? ST.versions : [{v: "–"}]).forEach(v => { const r = E("div"); r.style.cssText = "display:flex;align-items:center;gap:8px;font-size:12px";
      const bar = E("div"); bar.style.cssText = "flex:1;height:10px;background:var(--line,#1f2b3a);border-radius:5px;overflow:hidden";
      const f = E("div"); f.style.cssText = "height:100%;background:#3fcf6b;width:" + (v.rate || 0) + "%"; bar.appendChild(f);
      r.append(E("b", "", v.v), bar, E("span", "", (v.rate != null ? v.rate + " %" : "–") + (v.lat != null ? " · " + v.lat + " s" : "") + (v.score != null ? " · " + tt("test") + " " + v.score : "")));
      tb.appendChild(r); }); s.appendChild(tb);
  }
  const lab = async (d) => { try { const r = d ? await (await fetch("/api/lab", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})).json()
      : await (await fetch("/api/lab")).json(); if (r && r.inbox) LB = r; if (r && r.ok === false && r.error) say("⚠ " + r.error); paintAll(); return r; } catch (e) {} };
  const B = (txt, fn, cls) => { const b = E("button", cls || "sec", txt); b.type = "button"; b.onclick = fn; return b; };
  const row = (...xs) => { const r = E("div", "shrow"); r.style.flexWrap = "wrap"; xs.forEach(x => r.appendChild(x)); return r; };
  const NM = {"Push message": "Push", "Light": "Licht", "Siren": "Sirene", "Siren after a while (escalation)": "Sirene nach einer Weile"};
  function labSheet(s, kind) {
    if (!LB) { s.appendChild(E("div", "mut", "…")); lab(); return; }
    if (kind === "inbox") {
      s.appendChild(row(B((LB.sandbox ? "✓ " : "") + tt("Messages here instead of the phone"), () => lab({do: "sandbox", on: !LB.sandbox}), LB.sandbox ? "" : "sec"),
        B("🔔 " + tt("Test the alarm chain"), async () => { const r = await lab({do: "chain"}); if (r && r.chain) { open = "inbox"; window._chain = r.chain; paintAll(); } }), B("🗑", () => lab({do: "clear"}))));
      if (window._chain) s.appendChild(row(...window._chain.map(x => E("span", "", (x.ok ? "✅ " : "❌ ") + (L() === "en" ? x.name : (NM[x.name] || x.name)) + (x.text ? " (" + x.text + ")" : "")))));
      const ph = E("div"); ph.style.cssText = "width:100%;display:flex;flex-direction:column;gap:6px;max-height:300px;overflow:auto";
      (LB.inbox.length ? LB.inbox : [{t: "", title: tt("Empty – nothing arrived yet"), text: ""}]).forEach(m => { const c = E("div"); c.style.cssText = "display:flex;gap:8px;padding:8px;border-radius:12px;background:var(--panel2,#151e2b)";
        if (m.img) { const im = E("img"); im.src = "/api/lab/img/" + m.img; im.style.cssText = "width:64px;height:40px;object-fit:cover;border-radius:6px"; c.appendChild(im); }
        const tx = E("div"); tx.append(E("b", "", (m.held ? "⏸ " : "") + m.title), E("div", "mut", (m.t ? m.t + " · " : "") + m.text + (m.held ? " · " + tt("held back (offline), sent later") : ""))); tx.style.fontSize = "13px"; c.appendChild(tx); ph.appendChild(c); });
      s.appendChild(ph);
    }
    if (kind === "drill") {
      s.appendChild(row(B("🔋 " + tt("Battery empty"), () => lab({do: "drill", kind: "battery"})), B("📶 " + tt("Wi-Fi / internet gone"), () => lab({do: "drill", kind: "net"})),
        B("🔥 " + tt("Heat"), () => lab({do: "drill", kind: "heat"})), B("❄ " + tt("Cold"), () => lab({do: "drill", kind: "cold"}))));
      if (LB.drill.busy) s.appendChild(E("div", "mut", "⏳ " + tt("Drill runs") + " · " + LB.drill.left + " s"));
      const l = LB.drill.last; if (l) { s.appendChild(E("b", "", tt("Last drill") + ": " + l.kind + " – " + tt("how MoveEye reacted") + ":"));
        (l.reactions.length ? l.reactions : [{t: "", text: tt("no reaction")}]).forEach(x => s.appendChild(E("div", "mut", (x.t ? x.t + " · " : "") + x.text))); }
    }
    if (kind === "train") {
      const h = E("select"); for (let i = 0; i < 24; i++) { const o = E("option", "", String(i).padStart(2, "0") + ":00"); o.value = i; if (i === LB.train.hour) o.selected = true; h.appendChild(o); }
      h.onchange = () => lab({do: "train", hour: +h.value});
      s.appendChild(row(B((LB.train.on ? "✓ " : "") + tt("Every night"), () => lab({do: "train", on: !LB.train.on}), LB.train.on ? "" : "sec"), h,
        LB.train.busy ? B("⏹ " + tt("Stop"), () => lab({do: "train", stop: true})) : B("▶ " + tt("Start now"), () => lab({do: "train", start: true}))));
      s.appendChild(E("div", "mut", tt("train-note")));
      const l = LB.train.last; if (l) { s.appendChild(E("b", "", tt("Last training") + " (" + l.min + " min)"));
        l.results.forEach(r => s.appendChild(E("div", "mut", r.scene + " · " + r.plan + ": " + (r.score != null ? r.score : "–") + (r.base != null ? " (" + tt("before") + " " + r.base + ")" : "") + (r.persons != null ? " · " + r.found + "/" + r.persons + " · " + tt("false alarms") + " " + r.fa : ""))));
        s.appendChild(E("div", "mut", tt("kept") + ": " + (l.kept.join(", ") || "–") + (l.pics ? " · " + l.pics + " " + tt("training pictures") : ""))); }
    }
    if (kind === "ab") {
      s.appendChild(row(...LB.ab.presets.map(([k, n]) => B(tt(n), () => lab({do: "ab", preset: k})))));
      s.appendChild(E("div", "mut", tt("ab-note")));
      const l = LB.ab.last; if (l) s.appendChild(E("b", "", tt(l.title) + ": A " + (l.a != null ? l.a : "–") + " · B " + (l.b != null ? l.b : "–") + " → " + (l.winner === "B" ? tt("B is better – kept") : tt("A stays"))));
    }
  }
  // 2.98.14 (Konzept): the tiles in four groups - Welt (what happens in the simulator), Testen, Lernen, Spielen. «Simple»
  // shows the assistant «Erkennung verbessern» instead of the single tools for the thresholds (they stay in «Expert»).
  const GRP = {wide: "world", scene: "world", hour: "world", weather: "world", visit: "world", surprise: "world", twin: "world", devices: "world", rover: "world", templates: "world",
    tests: "test", parc: "test", blind: "test", rehearsal: "test", inbox: "test", drill: "test", ab: "test", week: "test", stats: "test",
    improve: "learn", autoth: "learn", train: "learn", falearn: "learn", diary: "learn",
    game: "play", points: "play"};
  // 2.98.24 («Sim-Schalter nur einmal»): Trainings-Nacht, Fehlalarm-Lernen and Wochen-Check are switched only in their tile
  // (no longer also in the assistant «Erkennung verbessern» and in «Einstellungen der Simulation») - so always shown
  const EXPERT_K = ["autoth", "ab"];
  function tiles(box, full) {
    const G = {world: E("div", "shub"), test: E("div", "shub"), learn: E("div", "shub"), play: E("div", "shub")}, g = G.world;
    const T = [["scene", "🗺", tt("Scene"), scn((H.scenes || []).find(x => x.id === H.scene)) || H.scene || "–"],
      ["hour", H.dark ? "🌙" : "☀", tt("Time of day"), H.clock || "–"],
      ["weather", wxIcon(H.weather), tt("Weather"), tt(H.weather || "–") + (H.ambient != null ? " · " + Math.round(H.ambient) + " °C" : "")],
      ["visit", (window.EVI || {}).person || "🚶", tt("Send a visitor"), (H.visitors != null ? H.visitors + " " + tt("visitors") + " " + tt("now") : "")]
      ];
    if (full) T.push(["surprise", "🎲", tt("Surprise night"), H.surprise ? tt("on") : tt("off")]);   // 2.98.13: drills / surprise only in the Simulator tab
    if (full && H.wide && window.mwWide) T.push(["wide", "🔭", tt("Wide camera"), window.mwWide.sub(H)]);   // 591: the wide camera of the simulator
    if (full && H.twin_ok) T.push(["twin", "🪞", tt("Your place"), tt("Place, zones, patrol")]);   // 2.98.5: zones / detection in 3D = simulator, «Ansicht»
    if (full) { const R = H.rover || {};
      T.push(["devices", "📡", tt("Several devices"), H.dev2 ? tt("2nd device") + ": " + tt("P_" + (H.dev2_place || "opposite")) : tt("off")],
        ["rover", "🚜", tt("Rover"), H.rover ? (R.mission ? "⏳ " + tt("M_" + R.mission) : R.active ? tt("patrols") : R.charging ? "⚡ " + tt("charging") : tt("ready")) + " · 🔋 " + R.batt + " %" : "–"],
        ["templates", "🧩", tt("Templates"), tt("Opens on the PC")]); }
    if (full) { const TU = H.tune || {};
      T.push(["improve", "🎯", tt("Improve detection"), TU.busy ? "⏳ " + (TU.step === "night" ? tt("Night") : tt("Day")) : tt("step by step")]); }
    if (full) { const N = LN || {}; const bl = N.blind || {}, au = N.autoth || {}, re = bl.rehearsal;
      T.push(["tests", "🧪", tt("Tests"), tt("Test run, test bench")]);
      if (window.mwParc && H.parc) T.push(["parc", "🎯", tt("Tracking parcours"), window.mwParc.sub(H)]);   // 416: the tracking parcours
      T.push(
        ["blind", "🗺", tt("Blind spots"), bl.busy && bl.kind === "map" ? "⏳ " + (bl.prog || "") : bl.last ? bl.last.found + "/" + bl.last.inview + " " + tt("recognised") : tt("find them")],
        ["rehearsal", "🌙", tt("Night rehearsal"), bl.busy && bl.kind === "rehearsal" ? "⏳ " + (bl.prog || "") : re ? (re.max_found ? tt("up to") + " " + re.max_found + " m" : "–") : tt("before arming")],
        ["autoth", "🎚", tt("Thresholds automatic"), au.busy ? "⏳ " + au.step : au.last ? "✓" : tt("day and night")],
        ["falearn", "👎", tt("False alarm learning"), N.fa_learn_auto ? tt("on") : tt("off")],
        ["week", "📅", tt("Weekly check"), N.week && N.week.on ? tt("on") : tt("off")],
        ["points", "🏅", tt("MoveEye points"), N.points ? String(N.points.total) : "–"]); }
    if (full) T.push(["inbox", "📨", tt("Test inbox"), LB ? (LB.sandbox ? tt("on") : tt("off")) + " · " + (LB.inbox || []).length : ""],
      ["drill", "⚡", tt("Drills"), LB && LB.drill.busy ? "⏳ " + LB.drill.left + " s" : tt("Battery, Wi-Fi, heat, cold")],
      ["train", "🌙", tt("Training night"), LB ? (LB.train.busy ? "⏳ " + (LB.train.step || "") : LB.train.on ? tt("on") + " · " + String(LB.train.hour).padStart(2, "0") + ":00" : tt("off")) : ""],
      ["ab", "⚖", tt("A/B comparison"), LB && LB.ab.busy ? "⏳ " + LB.ab.step : tt("Which setting is better?")],
      ["stats", "📈", tt("Statistics & versions"), tt("4 weeks, per version")]);
    if (full) T.push(["game", "🎮", tt("Game"), tt("Play on the phone")], ["diary", "📔", tt("Diary"), tt("Visits and detection")]);
    T.forEach(([k, ic, n, sub]) => { if (full && H.simple && EXPERT_K.includes(k)) return;
      const b = E("button", "st" + (open === k || (k === "surprise" && H.surprise) ? " on" : "")); b.type = "button";
      b.append(E("i", "", ic), E("b", "", n), E("small", "", sub));
      b.onclick = () => { if (k === "surprise") return act("surprise", !H.surprise); if (k === "templates") return act("templates").then(r => r && r.ok && say("🧩 " + tt("Opens on the PC")));
        if (k === "improve") return window.mwTune && window.mwTune.open();
        if (k === "twin") return act("twin").then(r => r && r.ok && say("🪞 " + tt("The map opens at your place on the PC – confirm «Load this place»")));
        if (k === "zones3d") return act("overlay", {id: "show_zones3d", on: !H.zones3d}); if (k === "det3d") return act("overlay", {id: "show_det3d", on: !H.det3d});
        if (k === "game") return location.href = "/sim#c-game"; if (k === "tests" && !document.getElementById("tr-box") && !window._trBox) return location.href = "/sim#c-test"; if (k === "diary") return location.href = "/diary#simcard";
        open = open === k ? "" : k; paintAll(); if (k === "tests" && open && typeof trLoad === "function") trLoad(); };
      (full ? G[GRP[k] || "world"] : g).appendChild(b); });
    if (full) { [["world", "🌍 " + tt("World")], ["test", "🧪 " + tt("Testing")], ["learn", "🎓 " + tt("Learning")], ["play", "🎮 " + tt("Playing")]].forEach(([id, h]) => {
        if (G[id].children.length) box.append(E("div", "shubh", h), G[id]); });
      const sx = B(H.simple ? "🧰 " + tt("Show all tools («Expert»)") : "🎯 " + tt("Only the assistant («Simple»)"), async () => {
        try { await fetch("/api/ui_simple", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({on: !H.simple, page: "sim"})}); } catch (e) {} H.simple = !H.simple; paintAll(); });
      sx.style.cssText = "margin-top:10px;font-size:12px"; box.appendChild(sx); }   // 2.98.14: four groups, Simple / Expert
    else box.appendChild(g);
    if (open && full && G[GRP[open] || "world"].parentNode) { const hold = E("div"); G[GRP[open] || "world"].after(hold); sheet(hold, open); }   // the sheet right under its group
    else if (open) sheet(box, open);
    if (full && H.handover && H.handover.length) { const w = E("div", "mut", "🔁 " + H.handover.map(x => x.t + " " + x.from + " → " + x.to).join(" · ")); w.style.cssText = "margin-top:6px;font-size:12px"; box.appendChild(w); }
    if (full && H.twin && (H.twin.place || H.twin.mast)) { const w = E("div", "mut", "🪞 " + tt("Your place") + ": " + (H.twin.place || "–") + (H.twin.mast ? " · " + tt("mast") + " " + H.twin.mast.toFixed(2) + " m" : "")
      + (H.twin.zones != null ? " · " + H.twin.zones + " " + tt("zones") : "") + (H.twin.waypoints != null ? " · " + H.twin.waypoints + " " + tt("patrol points") : "")); w.style.cssText = "margin-top:8px;font-size:12px"; box.appendChild(w); }
  }
  function paintTile(el_) {
    el_.hidden = !(H && H.on); if (!H || !H.on) return; el_.textContent = "";
    const top = E("div", "stile"), im = E("img"); im.alt = ""; im.src = "/sim/view.jpg?w=320&r=" + Date.now();
    const i = E("div", "sti"); i.append(E("b", "", "🧪 " + tt("Simulation") + (H.ok ? "" : " ⚠")), E("div", "", H.ok ? (scn((H.scenes || []).find(x => x.id === H.scene)) || H.scene) : tt("Simulator not reachable")),
      E("span", "", H.ok ? (H.dark ? "🌙 " : "☀ ") + H.clock + " · " + wxIcon(H.weather) + " " + tt(H.weather || "") + (H.visitors != null ? " · " + H.visitors + " " + tt("visitors") : "") : ""), E("span", "", tt("Tap = control")));
    top.append(im, i); top.onclick = () => { el_.dataset.open = el_.dataset.open ? "" : "1"; paintAll(); }; el_.appendChild(top);
    if (el_.dataset.open && H.ok) { const w = E("div"); w.style.marginTop = "8px"; tiles(w, false); el_.appendChild(w); }
  }
  function paintFull(el_) { el_.textContent = ""; if (!H || !H.on) { el_.hidden = true; return; } el_.hidden = false;
    if (!H.ok) { el_.appendChild(E("div", "mut", "⚠ " + tt("Simulator not reachable") + (H.msg ? " (" + H.msg + ")" : ""))); return; } tiles(el_, true); }
  function parkTr() { const tb = window._trBox, home = document.getElementById("c-test"); if (tb && home && !home.contains(tb)) home.appendChild(tb); }
  function paintSheet(el_) { if (el_.contains(document.activeElement) && document.activeElement.type === "range") return;   // 549 Sim-Kompakt: one sheet alone
    el_.textContent = ""; if (H && H.ok && el_.dataset.kind) sheet(el_, el_.dataset.kind); }
  function paintAll() { parkTr(); document.querySelectorAll("[data-simhub]").forEach(x => x.dataset.simhub === "full" ? paintFull(x) : x.dataset.simhub === "sheet" ? paintSheet(x) : paintTile(x)); }
  window.mwSimHub = {H: () => H, tt: tt, scn: scn, paint: () => paintAll(), load: () => load()};   // 549: the tiles of the live page «Sim-Kompakt»
  async function load() { if (!document.querySelector("[data-simhub]")) return; try { H = await (await fetch("/api/simhub")).json(); } catch (e) { return; }
    if (document.querySelector('[data-simhub="full"]')) { try { LB = await (await fetch("/api/lab")).json(); LN = await (await fetch("/api/learn")).json(); } catch (e) {} }
    const ti = document.querySelector('[data-simhub="tile"] img'); if (ti && !document.hidden) ti.src = "/sim/view.jpg?w=320&r=" + Date.now();
    if (!HASHED && location.hash === "#c-test" && document.getElementById("tr-box")) { HASHED = 1; open = "tests"; }   // 2.98.23: old links to the test run
    if (!HASHED && location.hash === "#c-parc" && H.parc) { HASHED = 1; open = "parc"; }   // 416: the window opens the tile 🎯
    const ae = document.activeElement;
    if (!ae || (ae.type !== "range" && !(ae.closest && ae.closest("#tr-box")))) paintAll(); }
  document.addEventListener("DOMContentLoaded", () => { load(); setInterval(load, 6000); });
})();
"""


def simhub_head():
    return ("<style>" + SIMHUB_CSS + "</style><script>" + SIMHUB_JS.replace("__VIS__", json.dumps(SIMHUB_VISITS, ensure_ascii=False)) + "</script>"
            + tune_head())                                  # 2.98.14: the assistant «Erkennung verbessern» (312)


# ---- 2.96.4 (Makeover-Punkt 5): Kino-Modus /kino - Vollbild für TV / Beamer: Livebild mit den Rahmen, Uhr, Zustand und
# ein Laufband mit den letzten Ereignissen (die gleichen Symbole wie überall). Mit Tastatur: F = Vollbild, Esc = zurück.
def kino_state():
    with LOCK:
        evs = [e for e in STATE.get("events", []) if e.get("imp") or e.get("kind") in ("person", "ai", "car")][:8]
    return {"name": CFG.get("device_name") or "MoveEye", "version": APP_VERSION, "persons": STATE.get("persons", 0),
            "armed": bool(is_armed()), "rec": bool(STATE.get("recording")), "sim": bool(CFG.get("sim_on")),
            "events": [{"t": e["t"][:5], "i": LOG_ICON.get(e["kind"], "·"), "x": tr(e["text"]) if isinstance(e.get("text"), str) else ""} for e in evs],
            "demo": {"busy": DEMO_RUN["busy"], "i": DEMO_RUN["i"], "n": DEMO_RUN["n"], "text": tr(DEMO_RUN["step"]) if DEMO_RUN["step"] else ""}}


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
#demo{position:fixed;left:50%;bottom:70px;transform:translateX(-50%);max-width:80vw;padding:14px 26px;border-radius:18px;background:#0a0e14dd;border:2px solid #f59a4a;
  font-size:clamp(18px,2.6vw,38px);font-weight:600;text-align:center;transition:opacity .4s}#demo small{display:block;font-size:.45em;color:#f59a4a;letter-spacing:.12em}
</style></head><body>
<img id="v" src="/video_feed" alt="">
<div class="top"><div><b id="nm">MoveEye</b><span id="st"></span></div><div id="clock"></div></div>
<div id="demo" hidden></div><div class="tick"><div id="tk"></div></div><div class="hint">F = Vollbild · Esc = zurück</div>
<script>
const $ = s => document.querySelector(s);
const pad = n => String(n).padStart(2, "0");
setInterval(() => { const d = new Date(); $("#clock").textContent = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds()); }, 1000);
async function load() { try { const r = await (await fetch("/api/kino")).json();
  $("#nm").textContent = r.name; const st = $("#st"); st.textContent = "";
  const P = (txt, cls) => { const s = document.createElement("span"); s.className = "pill " + (cls || ""); s.textContent = txt; st.appendChild(s); };
  if (r.sim) P("🧪 SIMULATION", "org"); P(r.armed ? "🛡 Schutz an" : "Schutz aus"); if (r.persons) P("🚶 " + r.persons, "red"); if (r.rec) P("● REC", "red");
  const dm = $("#demo"); dm.hidden = !(r.demo && r.demo.busy && r.demo.text);
  if (!dm.hidden && dm.dataset.s !== r.demo.text) { dm.dataset.s = r.demo.text; dm.textContent = ""; const sm = document.createElement("small"); sm.textContent = "DEMO " + r.demo.i + " / " + r.demo.n; dm.append(sm, document.createTextNode(r.demo.text)); }
  const tk = $("#tk"), txt = r.events.map(e => e.t + " " + e.i + " " + e.x).join("|");
  if (tk.dataset.s !== txt) { tk.dataset.s = txt; tk.textContent = ""; (r.events.length ? r.events : [{t: "", i: "", x: "–"}]).forEach(e => { const s = document.createElement("span"); s.textContent = (e.t ? e.t + "  " : "") + e.i + " " + e.x; tk.appendChild(s); }); }
  } catch (e) {} }
load(); setInterval(load, 3000);
$("#v").onerror = () => setTimeout(() => { $("#v").src = "/video_feed?r=" + Date.now(); }, 2000);
document.addEventListener("keydown", e => { if (e.key === "f" || e.key === "F") (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {});
  if (e.key === "Escape" && !document.fullscreenElement) location.href = "/"; });
document.body.ondblclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {});
</script></body></html>"""


# ---- 2.96.5 (Makeover-Punkt 8): «Was wäre wenn …?» - eine echte Aufnahme im Simulator nachstellen: gleiche Uhrzeit, Licht,
# Regen, Richtung des Kopfes, gleich viele Personen (bzw. ein Tier / Auto). Jede neue Aufnahme bekommt dafür «situ» in ihre
# Info-Datei; ältere Aufnahmen nehmen die Uhrzeit aus dem Namen und schauen geradeaus.
def whatif_situ_now(info=None):
    hp, ht = servo_half("pan"), servo_half("tilt")
    obj = str(STATE.get("object_summary") or "").lower()
    animal = any(w in obj for w in ("cat", "dog", "fox", "deer", "bird", "animal", "horse", "sheep", "cow", "bear", "boar"))
    car = any(w in obj for w in ("car", "truck", "bus", "motorcycle"))
    return {"pan_deg": round((CFG["pan"] - 50) / 50 * hp, 1), "tilt_deg": round((CFG["tilt"] - 50) / 50 * ht, 1),
            "dark": bool(STATE.get("lowlight")), "rain": bool(STATE.get("rain_mode")), "wind": str(STATE.get("wind_level") or ""),
            "animal": animal, "car": car, "ir": bool((STATE.get("lights") or {}).get("ir")) if isinstance(STATE.get("lights"), dict) else False}


def whatif(name):
    """re-enact the recording «name» in the simulator. Returns (ok, error, text)"""
    if not CFG.get("sim_on"):
        return False, "the simulator is not switched on (tab Simulator)", ""
    if not rec_path(name):
        return False, "not found", ""
    meta = _read_sidecar(name)
    situ = meta.get("situ") or {}
    try:
        dt = datetime.fromisoformat(meta["start"]) if meta.get("start") else (parse_stamp(os.path.basename(name)) or datetime.now())
    except ValueError:
        dt = datetime.now()
    persons = int(meta.get("persons") or 0)
    kind = "person" if persons or not (situ.get("animal") or situ.get("car")) else ("fox" if situ.get("animal") else "car")
    q = {"action": "whatif", "hour": round(dt.hour + dt.minute / 60.0, 2), "weather": "rain" if situ.get("rain") else "clear",
         "kind": kind, "n": max(1, min(4, persons or 1)), "pan_deg": float(situ.get("pan_deg") or 0.0),
         "dist": 9.0 if situ.get("dark") else 14.0, "name": os.path.basename(name)}
    try:
        r = sim_control(q)
    except Exception:
        return False, "simulator not reachable", ""
    if not r.get("ok"):
        return False, str(r.get("error") or "not supported - update the simulator"), ""
    log_event("sys", f"What if: {name} re-enacted in the simulator ({kind}, {q['hour']:.2f} h)")
    _SIMHUB["t"] = 0.0
    return True, "", "%02d:%02d · %s%s · %s" % (dt.hour, dt.minute, ev_icon("person" if kind == "person" else "animal" if kind == "fox" else "vehicle"),
                                                 (" ×%d" % q["n"]) if q["n"] > 1 else "", "🌧" if situ.get("rain") else ("🌙" if situ.get("dark") else "☀"))


# ---- 2.96.5 (Makeover-Punkt 9): Zwilling deines Platzes. MoveEye -> Simulator: Ort (GPS / eingestellter Ort), Zonen und
# Patrouillen-Punkte (die beiden letzten gehen laufend im Zustand mit, sim_state). Der Simulator öffnet die Karte an diesem Ort
# («Diesen Ort laden» bestätigen). Simulator -> MoveEye: der geladene Ort, die Stangenhöhe und die Szene (sim_twin_info).
def sim_twin():
    g = gps_now()
    q = {"action": "twin", "name": CFG.get("device_name") or "MoveEye", "zones": len(ZONES), "waypoints": len(WAYPOINTS)}
    if g:
        q.update(lat=round(g[0], 6), lon=round(g[1], 6), src=g[2])
    r = sim_control(q)
    return r


def sim_twin_info():
    try:
        r = sim_control({"action": "twin", "op": "info"})
        return r.get("twin") or {}
    except Exception:
        return {}
