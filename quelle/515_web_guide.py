#@ MoveEye – Teil 515: Guide – Erklärungen beim ersten Öffnen, Markierungen «neu / noch nie geöffnet» (2.98.9). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel: a guide that leads the operator through the device from the start. Every page / tab / settings topic is
# explained shortly the first time it is opened; a small dot shows what was never opened, «NEU» what came with a recent
# version. Levels (CFG tips_level): off · basic (only the most important) · normal · all (nearly every detail).
# What was seen is kept in the browser storage key «mw-tips-seen», which MoveEye copies to the Pi (web_ui) - so it is the
# same on every device, and the window (Tk) uses it too.
# ----------------------------------------------------------------------------
TIPS_LEVELS = ("off", "basic", "normal", "all")
# (key, level 1..3, since version or "", English title, English text, German title, German text)
GUIDE_TIPS = [
    ("page:live", 1, "", "Live", "The live picture. Turn the head with the joystick, tap the picture to look there. The quick switches below: light, follow, record, games …",
     "Live", "Das Livebild. Den Kopf mit dem Joystick drehen, ins Bild tippen = dorthin schauen. Darunter die Schnellschalter: Licht, Folgen, Aufnahme, Spiele …"),
    ("page:protect", 1, "", "Protection", "Here you switch the protection: Off · Watchful (only messages) · Full (light, siren). «Guard tonight» sets everything for the night in one tap.",
     "Schutz", "Hier schaltest du den Schutz: Aus · Wachsam (nur Meldungen) · Voll (Licht, Sirene). «Heute Nacht bewachen» stellt mit einem Tipp alles für die Nacht ein."),
    ("page:history", 1, "", "History", "Everything that happened: recordings (videos and photos), the animal diary and the log.",
     "Verlauf", "Alles, was passiert ist: Aufnahmen (Videos und Fotos), das Tier-Tagebuch und das Protokoll."),
    ("page:settings", 1, "", "Settings", "All settings, sorted by topic. «Simple» shows only the important ones, «Expert» all. The search finds every setting.",
     "Einstellungen", "Alle Einstellungen, nach Thema sortiert. «Einfach» zeigt nur das Wichtige, «Experte» alles. Die Suche findet jede Einstellung."),
    ("page:sim", 1, "", "Simulator", "The 3D simulator on the PC: test MoveEye without the real place - day, night, weather, animals, people - and play «Team against MoveEye».",
     "Simulator", "Der 3D-Simulator auf dem PC: MoveEye ohne echten Ort testen – Tag, Nacht, Wetter, Tiere, Menschen – und «Team gegen MoveEye» spielen."),
    ("page:more", 1, "2.98.7", "More", "«Open all games» for the guests, the manual, tools, the info page for neighbours and the almanac.",
     "Mehr", "«Spiele freigeben» für die Gäste, die Anleitung, Werkzeuge, die Infoseite für Nachbarn und der Almanach."),
    ("sec:Notifications", 1, "", "Push messages", "Set up how MoveEye reaches your phone (ntfy app). Without this you only see alarms on the page.",
     "Push-Nachrichten", "Hier stellst du ein, wie MoveEye dein Handy erreicht (App ntfy). Ohne das siehst du Alarme nur auf der Seite."),
    ("page:zones", 2, "2.98.9", "Zones", "Draw areas on the picture: ignore (street), only here (entrance), privacy (black), sleeping place (wake-up alarm), line, dwell area. Privacy zones stay on their place when the head turns.",
     "Zonen", "Bereiche ins Bild zeichnen: ignorieren (Strasse), nur hier (Eingang), Privatsphäre (schwarz), Schlafplatz (Wecker), Linie, Verweil-Bereich. Privatsphäre-Zonen bleiben an ihrem Ort, wenn der Kopf sich dreht."),
    ("page:rec", 2, "", "Recordings", "Videos and photos of the alarms. ⭐ keeps one for ever; old ones are deleted when the memory card is full.",
     "Aufnahmen", "Videos und Fotos der Alarme. ⭐ behält eine für immer; alte werden gelöscht, wenn die Speicherkarte voll ist."),
    ("page:diary", 2, "", "Animal diary", "The best picture of every animal visit, collected by itself. Every day on one page with weather, sun and moon.",
     "Tier-Tagebuch", "Das beste Bild jedes Tierbesuchs, von selbst gesammelt. Jeder Tag auf einer Seite mit Wetter, Sonne und Mond."),
    ("page:log", 2, "", "Log", "What MoveEye did and why - helpful when something does not work as expected.",
     "Protokoll", "Was MoveEye getan hat und warum – hilfreich, wenn etwas nicht wie erwartet geht."),
    ("page:cams", 2, "", "Cameras", "Choose the camera, add a second one, check the picture and the thermal camera.",
     "Kameras", "Kamera wählen, eine zweite dazunehmen, Bild und Wärmebild prüfen."),
    ("page:help", 2, "", "Manual", "Everything explained, with a search. Also as a one-page quick guide to print.",
     "Anleitung", "Alles erklärt, mit Suche. Auch als Kurzanleitung auf einer Seite zum Ausdrucken."),
    ("page:party", 2, "2.98.7", "Game corner", "Quiz, werewolf, connect four and more for the phones in the same Wi-Fi. «Open all games» opens everything with one QR code.",
     "Spielecke", "Quiz, Werwolf, Vier gewinnt und mehr für die Handys im gleichen WLAN. «Spiele freigeben» öffnet alles mit einem QR-Code."),
    ("page:tools", 2, "", "Tools", "Network and Wi-Fi tests, speed, Bluetooth, servo test, memory card, diagnosis package.",
     "Werkzeuge", "Netz- und WLAN-Tests, Tempo, Bluetooth, Servo-Test, Speicherkarte, Diagnose-Paket."),
    ("page:dev", 2, "2.98.8", "Developer", "Only this device, read-only: its own connections, the names it reached, the data per network card. Protected by its own PIN.",
     "Entwickler", "Nur dieses Gerät, nur lesen: eigene Verbindungen, erreichte Namen, Datenmenge pro Netzwerkkarte. Mit eigener PIN geschützt."),
    ("sec:Camping / protection", 2, "", "Arming and own Wi-Fi", "The countdown before arming, the camping profile and the own Wi-Fi of MoveEye (when there is no other network).",
     "Scharf schalten und eigenes WLAN", "Der Countdown vor dem Scharfschalten, das Camping-Profil und das eigene WLAN von MoveEye (wenn kein anderes Netz da ist)."),
    ("sec:Wake-up alarm", 2, "2.98.7", "Wake-up alarm", "Wakes you with a melody and light, turns to the bed only then. Wave = snooze, sit up = off. Draw the sleeping place under Zones first.",
     "Wecker", "Weckt dich mit Melodie und Licht und dreht sich erst dann zum Bett. Winken = schlummern, aufsitzen = aus. Zuerst unter Zonen den Schlafplatz einzeichnen."),
    ("sec:Deterrence", 2, "", "Deterrence", "What MoveEye does by itself when it sees a person or an animal: sound, flashing light or both.",
     "Abschreckung", "Was MoveEye von selbst tut, wenn es eine Person oder ein Tier sieht: Ton, blinkendes Licht oder beides."),
    ("sec:Recording", 2, "", "Recording", "Videos at an alarm (with a few seconds before), photos, how much memory may be used.",
     "Aufnahme", "Videos bei einem Alarm (mit ein paar Sekunden davor), Fotos, wie viel Speicher verwendet werden darf."),
    ("sec:Camera / Servos", 2, "", "Camera and head", "How the head turns: follow persons or anything that moves, limits, speed.",
     "Kamera und Kopf", "Wie sich der Kopf dreht: Personen oder allem folgen, was sich bewegt, Grenzen, Tempo."),
    ("sec:Patrol", 2, "", "Patrol", "The head drives through set points (waypoints) and looks round the place by itself.",
     "Patrouille", "Der Kopf fährt gespeicherte Punkte (Wegpunkte) ab und schaut sich von selbst um."),
    ("sec:AI detection", 2, "", "AI detection", "The artificial intelligence that says «person», «fox», «car». More certainty = fewer false alarms, but slower.",
     "KI-Erkennung", "Die künstliche Intelligenz, die «Person», «Fuchs», «Auto» sagt. Mehr Sicherheit = weniger Fehlalarme, aber langsamer."),
    ("sec:Lights", 2, "", "Lights", "White light and infrared: when they go on by themselves (at an alarm, at night).",
     "Licht", "Weisses Licht und Infrarot: wann sie von selbst angehen (bei einem Alarm, in der Nacht)."),
    ("sec:Loudspeaker", 2, "", "Loudspeaker", "Siren and sounds: which loudspeaker, how loud, which sound.",
     "Lautsprecher", "Sirene und Töne: welcher Lautsprecher, wie laut, welcher Ton."),
    ("sec:Night report", 2, "2.98.9", "Night report and night time", "The ONE night time of MoveEye: the report comes at its end, the wake-up alarm looks away during it, «Guard tonight» ends with it.",
     "Nachtbericht und Nachtzeit", "Die EINE Nachtzeit von MoveEye: am Ende kommt der Bericht, der Wecker schaut während der Nacht weg, «Heute Nacht bewachen» endet damit."),
    ("sec:Battery", 2, "", "Battery", "Charge, time left and what happens when the battery gets low.",
     "Akku", "Ladung, Restlaufzeit und was passiert, wenn der Akku schwach wird."),
    ("sec:Setup", 2, "2.98.9", "Setup", "Place, time, name, what MoveEye is for («Simple» shows only what fits) and these explanations (fewer / more / off).",
     "Setup", "Ort, Zeit, Name, wofür MoveEye da ist («Einfach» zeigt nur das Passende) und diese Erklärungen (weniger / mehr / aus)."),
]
_DETAIL = [   # level 3: nearly every topic (short)
    ("Detection", "Motion detection: how sensitive, how big something must be.", "Bewegungserkennung: wie empfindlich, wie gross etwas sein muss."),
    ("Thermal camera", "The thermal camera finds warm bodies, also in the dark and behind grass.", "Die Wärmebildkamera findet warme Körper, auch im Dunkeln und hinter Gras."),
    ("Low light", "Night vision and the brighter picture at dusk.", "Nachtsicht und das hellere Bild in der Dämmerung."),
    ("Rain", "Rain filter: drops on the lens do not give alarms.", "Regenfilter: Tropfen auf der Linse lösen keinen Alarm aus."),
    ("Wind", "Wind filter: moving branches and grass are ignored.", "Windfilter: bewegte Äste und Gras werden ignoriert."),
    ("Auto-tune", "MoveEye adapts its sensitivity to the place by itself.", "MoveEye passt seine Empfindlichkeit selbst an den Ort an."),
    ("Timelapse", "A photo every few minutes - a film of the whole day.", "Alle paar Minuten ein Foto – ein Film des ganzen Tages."),
    ("Video source", "Which camera MoveEye uses (also an IP camera or the simulator).", "Welche Kamera MoveEye benutzt (auch eine IP-Kamera oder den Simulator)."),
    ("Servo driver", "How the servos are connected (PCA9685 or GPIO) - only when building the device.", "Wie die Servos angeschlossen sind (PCA9685 oder GPIO) – nur beim Bauen des Geräts."),
    ("Microphone", "Listen, noise alarm, clap switch.", "Mithören, Lärmalarm, Klatschschalter."),
    ("Clap switch", "Clap 2, 3 or 4 times to switch something.", "2-, 3- oder 4-mal klatschen schaltet etwas."),
    ("Bless you", "MoveEye answers a sneeze.", "MoveEye antwortet auf ein Niesen."),
    ("Relays", "Switch other devices (lamp, pump, horn) at an alarm or by hand.", "Andere Geräte schalten (Lampe, Pumpe, Hupe) bei einem Alarm oder von Hand."),
    ("Extra sensors", "Door contacts, motion detectors and more, by radio or cable.", "Türkontakte, Bewegungsmelder und mehr, per Funk oder Kabel."),
    ("Storm warning", "A wind meter warns before a storm.", "Ein Windmesser warnt vor Sturm."),
    ("GPS module", "Position of the device - also against theft.", "Standort des Geräts – auch gegen Diebstahl."),
    ("Power saving", "Fewer pictures while all is quiet - the battery lasts longer.", "Weniger Bilder, solange alles ruhig ist – der Akku hält länger."),
    ("Solar panel", "Charging from the sun, measured.", "Laden mit der Sonne, gemessen."),
    ("Wi-Fi / hotspot", "Networks, the own Wi-Fi, the phone hotspot.", "Netze, das eigene WLAN, der Handy-Hotspot."),
    ("Web stream", "Quality and size of the live picture.", "Qualität und Grösse des Livebilds."),
    ("Guest access", "A link for others: only watching, for a limited time.", "Ein Link für andere: nur zuschauen, für eine bestimmte Zeit."),
    ("MQTT / Home Assistant", "Connection to a smart home.", "Verbindung zu einem Smart Home."),
    ("Updates", "New versions: by itself or by hand, and back to an older one.", "Neue Versionen: von selbst oder von Hand, und zurück zu einer älteren."),
    ("Simulator", "The connection to the 3D simulator on the PC.", "Die Verbindung zum 3D-Simulator auf dem PC."),
    ("Backup", "Copy recordings off the device (cloud, USB stick).", "Aufnahmen vom Gerät wegkopieren (Cloud, USB-Stick)."),
    ("Theft protection", "Alarm when the device is moved or opened.", "Alarm, wenn das Gerät bewegt oder geöffnet wird."),
    ("Reference scan", "The head photographs the place and later sees what is missing or new.", "Der Kopf fotografiert den Platz und sieht später, was fehlt oder neu ist."),
    ("Messages", "The texts of the push messages, also your own.", "Die Texte der Push-Nachrichten, auch eigene."),
    ("SMS (LTE stick)", "Alarms by SMS without internet.", "Alarme per SMS ohne Internet."),
    ("Schedule", "Times when features go on or off by themselves.", "Zeiten, zu denen Funktionen von selbst ein- oder ausgehen."),
    ("Vehicle filter", "Passing cars do not give alarms.", "Vorbeifahrende Autos lösen keinen Alarm aus."),
    ("Walking recognition", "A person counts only when it really walks.", "Eine Person zählt erst, wenn sie wirklich geht."),
    ("Mover", "The small tracked vehicle under the head.", "Das kleine Raupenfahrzeug unter dem Kopf."),
]
GUIDE_TIPS += [("sec:" + s, 3, "", s, en, s, de) for s, en, de in _DETAIL]
GUIDE_UI = {"Got it": "Verstanden", "Fewer tips": "Weniger Tipps", "Tips off": "Tipps aus", "NEW": "NEU", "Tip": "Tipp",
            "Explanations are off. Switch them on again under Settings → Setup.": "Erklärungen sind aus. Wieder einschalten unter Einstellungen → Setup.",
            "Now only the most important explanations.": "Jetzt nur noch die wichtigsten Erklärungen."}


def guide_seen():
    try:
        v = json.loads((CFG.get("web_ui") or {}).get("mw-tips-seen") or "[]")
        return set(v) if isinstance(v, list) else set()
    except (TypeError, ValueError):
        return set()


def guide_level():
    lv = CFG.get("tips_level") or "normal"
    return TIPS_LEVELS.index(lv) if lv in TIPS_LEVELS else 2


def guide_tip_for(key):
    """the tip for the window (Tk): (title, text) in the current language, or None (seen, level, unknown)"""
    if guide_level() == 0 or key in guide_seen():
        return None
    for k, lv, _v, te, xe, td, xd in GUIDE_TIPS:
        if k == key and lv <= guide_level():
            L = cur_lang()
            return (td, xd) if L == "de" else (tr(te, L), tr(xe, L))
    return None


def guide_mark_seen(key):
    s = guide_seen()
    if key in s:
        return
    s.add(key)
    CFG.setdefault("web_ui", {})["mw-tips-seen"] = json.dumps(sorted(s)[-400:])
    save_settings()


def guide_js(active):
    data = {"active": active, "level": guide_level(), "ver": APP_VERSION,
            "tips": [{"k": k, "l": lv, "v": v, "te": te, "xe": xe, "td": td, "xd": xd} for k, lv, v, te, xe, td, xd in GUIDE_TIPS],
            "ui": GUIDE_UI}
    return "window.MW_GUIDE=" + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";\n" + GUIDE_JS


GUIDE_JS = r"""
// ---- 2.98.9: guide - a short explanation the first time something is opened, a dot for «never opened», «NEW» ----
(function guide() {
  if (window._mwg) return; window._mwg = true;
  const G = window.MW_GUIDE; if (!G || !G.level) return;
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || "de"; } catch (e) { return "de"; } };
  const de = () => L() === "de";
  const tx = s => de() ? (G.ui[s] || s) : ((typeof t === "function" && t(s) !== s) ? t(s) : s);
  const tip = {}; G.tips.forEach(x => { if (x.l <= G.level) tip[x.k] = x; });
  const titleOf = x => de() ? x.td : ((typeof t === "function" && t(x.te) !== x.te) ? t(x.te) : x.te);
  const textOf = x => de() ? x.xd : ((typeof t === "function" && t(x.xe) !== x.xe) ? t(x.xe) : x.xe);
  const vnum = v => (v || "0").split(".").map(n => +n || 0);
  const newer = (a, b) => { const A = vnum(a), B = vnum(b); for (let i = 0; i < 3; i++) { if ((A[i] || 0) !== (B[i] || 0)) return (A[i] || 0) > (B[i] || 0); } return false; };
  const recent = v => { if (!v) return false; const C = vnum(G.ver), V = vnum(v); return C[0] === V[0] && C[1] === V[1] && C[2] - V[2] <= 3 || newer(v, G.ver); };
  let seen; try { seen = new Set(JSON.parse(localStorage.getItem("mw-tips-seen") || "[]")); } catch (e) { seen = new Set(); }
  const save = () => { try { localStorage.setItem("mw-tips-seen", JSON.stringify([...seen].slice(-400))); } catch (e) {} };
  const css = document.createElement("style");
  css.textContent = ".gd-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--acc,#3d8bff);margin-left:5px;vertical-align:middle;box-shadow:0 0 0 2px rgba(61,139,255,.25)}"
    + ".gd-new{display:inline-block;font-size:9px;font-weight:800;letter-spacing:.04em;padding:1px 5px;border-radius:999px;background:#f0a540;color:#111;margin-left:5px;vertical-align:middle}"
    + "#gd-card{position:fixed;left:50%;bottom:calc(16px + env(safe-area-inset-bottom,0px));transform:translate(-50%,20px);opacity:0;transition:transform .35s ease,opacity .35s ease;z-index:250;"
    + "width:min(440px,calc(100vw - 24px));background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-left:4px solid var(--acc,#3d8bff);border-radius:14px;padding:12px 14px;box-shadow:0 12px 40px rgba(0,0,0,.45)}"
    + "#gd-card.on{transform:translate(-50%,0);opacity:1}#gd-card b{display:block;font-size:15px;margin-bottom:4px}#gd-card p{margin:0 0 10px;font-size:14px;line-height:1.4;color:var(--mut,#9fb0c3)}"
    + "#gd-card .gb{display:flex;gap:8px;flex-wrap:wrap}#gd-card button{font:inherit;font-size:13px;padding:7px 12px;border-radius:10px;cursor:pointer;border:1px solid var(--line,#1f2b3a);background:transparent;color:var(--txt,#e8eef5)}"
    + "#gd-card button.ok{background:var(--acc,#3d8bff);border-color:var(--acc,#3d8bff);color:#fff}@media (prefers-reduced-motion:reduce){#gd-card{transition:none}}";
  document.head.appendChild(css);
  const queue = []; let busy = false;
  function setLevel(v) { fetch("/api/text", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({key: "tips_level", value: v})}).catch(() => {}); }
  function showNext() {
    if (busy || !queue.length) return; const x = queue.shift(); if (seen.has(x.k)) { showNext(); return; } busy = true;
    const c = document.createElement("div"); c.id = "gd-card"; c.setAttribute("role", "status");
    const b = document.createElement("b"); b.textContent = "💡 " + titleOf(x) + (recent(x.v) ? " " : "");
    if (recent(x.v)) { const n = document.createElement("span"); n.className = "gd-new"; n.textContent = tx("NEW"); b.appendChild(n); }
    const p = document.createElement("p"); p.textContent = textOf(x);
    const bt = document.createElement("div"); bt.className = "gb";
    const done = () => { seen.add(x.k); save(); paintDots(); c.classList.remove("on"); setTimeout(() => { c.remove(); busy = false; setTimeout(showNext, 400); }, 350); };
    const ok = document.createElement("button"); ok.className = "ok"; ok.type = "button"; ok.textContent = tx("Got it"); ok.onclick = done;
    const less = document.createElement("button"); less.type = "button"; less.textContent = tx("Fewer tips");
    less.onclick = () => { setLevel(G.level > 1 ? G.level === 3 ? "normal" : "basic" : "basic"); G.level = Math.max(1, G.level - 1);
      Object.keys(tip).forEach(k => { if (tip[k].l > G.level) delete tip[k]; }); for (let i = queue.length - 1; i >= 0; i--) if (!tip[queue[i].k]) queue.splice(i, 1);
      p.textContent = tx("Now only the most important explanations."); setTimeout(done, 1200); };
    const off = document.createElement("button"); off.type = "button"; off.textContent = tx("Tips off");
    off.onclick = () => { setLevel("off"); G.level = 0; queue.length = 0; p.textContent = tx("Explanations are off. Switch them on again under Settings → Setup."); setTimeout(() => { done(); paintDots(); }, 1800); };
    bt.append(ok, less, off); c.append(b, p, bt); document.body.appendChild(c);
    requestAnimationFrame(() => requestAnimationFrame(() => c.classList.add("on")));
  }
  function want(k) { const x = tip[k]; if (!x || seen.has(k) || !G.level || queue.some(q => q.k === k)) return; queue.push(x); setTimeout(showNext, 600); }
  // which key a link opens
  const HREF = {"/": "page:live", "/protect": "page:protect", "/recordings": "page:rec", "/settings": "page:settings", "/sim": "page:sim", "/more": "page:more",
    "/zones": "page:zones", "/diary": "page:diary", "/log": "page:log", "/cams": "page:cams", "/help": "page:help", "/party": "page:party", "/tools": "page:tools", "/dev": "page:dev"};
  const TOP = {"/recordings": "page:history"};
  function mark(el, key) {
    if (!el) return; el.querySelectorAll(":scope > .gd-dot, :scope > .gd-new").forEach(e => e.remove());
    const x = tip[key]; if (!G.level || !x || seen.has(key)) return;
    const s = document.createElement("span"); s.className = recent(x.v) ? "gd-new" : "gd-dot"; if (recent(x.v)) s.textContent = tx("NEW");
    s.title = titleOf(x); el.appendChild(s);
  }
  function paintDots() {
    document.querySelectorAll("nav.nav a, nav.subnav a").forEach(a => { const h = a.getAttribute("href"); const k = (a.closest("nav.nav") && TOP[h]) || HREF[h]; if (k) mark(a, k); });
    document.querySelectorAll('details[data-view^="sec:"] > summary').forEach(s => mark(s, s.parentElement.dataset.view));
  }
  // the page itself
  const act = G.active === "history" ? "rec" : G.active;
  const here = "page:" + act;
  if (act === "rec" && tip["page:history"] && !seen.has("page:history")) want("page:history");
  want(here);
  if (here === "page:history") { seen.add("page:rec"); }
  // a settings topic opened the first time
  const t0 = Date.now();                                    // sections the page opens by itself at the start do not count
  document.addEventListener("toggle", ev => { const d = ev.target; if (!d || d.tagName !== "DETAILS" || !d.open || Date.now() - t0 < 2500) return;
    const v = d.dataset && d.dataset.view; if (v && v.startsWith("sec:")) want(v); }, true);
  const start = () => { paintDots(); setTimeout(paintDots, 2500); setTimeout(paintDots, 6000); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
"""
