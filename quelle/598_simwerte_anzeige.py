#@ MoveEye – Teil 598: «🧪 Simulator»-Hinweis bei allen Werten, die vom Simulator kommen (Webseite und Fenster) + Anleitung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Simulator-Werte (285): STATE["simvals"] = {"on", "keys": battery / clock / place / weather / pi_temp / solar / gps / net,
# "time", "dark", "place", "weather", "net", "pi_temp", "off", "sched"}. Shown:
#   web (main page: after every refresh, hook on tidyHeader of 530; Simulator page: own poll every 3 s)
#     - one line under the simulator tile of the Live page / under the Simulator centre: which values come from the
#       simulator, the simulated time (day / night, time-lapse), place, weather, Pi temperature, «WLAN weg» test
#     - «🧪» + tooltip at the battery (header badge, battery line), the CPU temperature, solar, GPS, storm, schedules
#     - a red header badge «📵 🧪 WLAN weg» / «Internet weg» while the simulator plays the outage
#   window (Tk): the status lines Battery, Solar panel, GPS module, Storm warning, Night report, Simulator, the battery
#     badge, the CPU temperature and the Wi-Fi line get «🧪 Simulator».
# Texts: part 599 (German into the pages through /*SVDE*/).
# ----------------------------------------------------------------------------
SIMVALS_JS = r"""
<script>
(function () {
  try { const de = /*SVDE*/{}; if (typeof I18N !== "undefined" && I18N.de) for (const k in de) if (!(k in I18N.de)) I18N.de[k] = de[k]; } catch (e) {}
  try { if (typeof I18N !== "undefined") I18N.en = I18N.en || {}; if (typeof I18N !== "undefined") I18N.en["sv-note"] = I18N.en["sv-note"] || "When the simulator does not answer for 10 seconds, the real sensors and the real clock apply again. Log, file names and updates stay on the real clock."; } catch (e) {}
  const tt = s => (typeof t === "function" ? t(s) : s);
  const KN = {battery: "Battery", clock: "Clock", place: "Place", weather: "Weather", pi_temp: "Pi temperature", solar: "Solar panel", gps: "GPS module", net: "Network"};
  const SIMT = () => "🧪 " + tt("from the simulator");
  function tag(sel, sep, extra) {
    const e = document.querySelector(sel); if (!e || e.hidden || !e.textContent) return;
    if (!e.textContent.includes("🧪")) e.textContent += sep + "🧪" + (extra ? " " + extra : "");
    if (!(e.title || "").includes("🧪")) e.title = ((e.title || "") + "\n" + SIMT()).trim();
  }
  function box() {
    let b = document.getElementById("sv-box"); if (b) return b;
    const at = document.getElementById("simtile") || document.getElementById("c-hub"); if (!at) return null;
    b = document.createElement("div"); b.id = "sv-box"; b.className = "mut"; b.hidden = true;
    b.style.cssText = "white-space:pre-wrap;font-size:13px;margin:0 0 12px;padding:8px 10px;border:1px dashed var(--line,#444);border-radius:10px";
    at.parentNode.insertBefore(b, at.nextSibling); return b;
  }
  function netBadge(v) {
    let nb = document.getElementById("b-simnet"); const ref = document.getElementById("b-sim");
    if (!v.on || !v.net) { if (nb) nb.remove(); return; }
    if (!nb && ref) { nb = document.createElement("span"); nb.id = "b-simnet"; nb.className = "badge red"; ref.parentNode.insertBefore(nb, ref.nextSibling); }
    if (nb) { nb.textContent = "📵 🧪 " + tt(v.net === "wifi" ? "Wi-Fi gone" : "Internet gone"); nb.title = tt("Simulator test: push messages wait and are sent later"); }
  }
  function paint(s) {
    const v = (s && s.simvals) || {}; const b = box(); netBadge(v);
    if (!v.on) { if (b) b.hidden = true; return; }
    const K = new Set(v.keys || []);
    const L = ["🧪 " + tt("Values from the simulator") + ": " + [...K].map(k => tt(KN[k] || k)).join(", ")];
    const l2 = [];
    if (K.has("clock")) l2.push("🕑 " + v.time + " (" + tt(v.dark ? "night" : "day") + (v.speed > 1 ? ", " + tt("time-lapse") + " " + Math.round(v.speed) + "×" : "") + ")");
    if (K.has("place") && v.place) l2.push("📍 " + v.place);
    if (K.has("weather") && v.weather) l2.push("🌦 " + tt(v.weather));
    if (v.pi_temp != null) l2.push("🌡 Pi " + Math.round(v.pi_temp) + " °C");
    if (l2.length) L.push(l2.join(" · "));
    if ((v.sched || []).length) L.push("🗓 " + tt("Schedule") + ": " + v.sched.join(", "));
    if (v.net) L.push("📵 " + tt(v.net === "wifi" ? "Wi-Fi gone" : "Internet gone") + " – " + tt("Simulator test: push messages wait and are sent later"));
    if (v.off) L.push("⏻ " + tt("Battery empty – the device would be off now"));
    L.push(tt("sv-note"));
    if (b) { b.textContent = L.join("\n"); b.hidden = false; }
    const bs = document.getElementById("b-sim"); if (bs) bs.title = ((bs.title || "").split("\n🧪")[0] + "\n" + L.slice(0, 2).join("\n")).trim();
    if (K.has("battery")) { tag("#b-batt", " "); tag("#batt-line", "\n", tt("from the simulator") + (v.off ? " · ⏻ " + tt("Battery empty – the device would be off now") : "")); }
    if (K.has("pi_temp")) { tag("#b-cpu", " "); tag("#cpu-info", " · ", tt("Pi temperature from the simulator")); }
    if (K.has("solar")) tag("#solar-st", "\n", tt("from the simulator"));
    if (K.has("gps")) tag("#gpsm-st", "\n", tt("from the simulator"));
    if (K.has("weather")) tag("#storm-st", "\n", tt("weather and forecast from the simulator"));
    if (K.has("clock")) tag("#b-sched", " ", v.time);
  }
  window.svPaint = paint;
  if (typeof window.tidyHeader === "function") {                 // main page: after every refresh (tidyHeader paints last)
    const th = window.tidyHeader;
    window.tidyHeader = function (s, c) { const r = th.apply(this, arguments); setTimeout(() => { try { paint(s); } catch (e) {} }, 0); return r; };
  } else {                                                      // Simulator page: an own look every 3 s
    const poll = async () => { if (document.hidden) return; try { const j = await (await fetch("/api/state", {cache: "no-store"})).json(); paint(j.state || {}); } catch (e) {} };
    setInterval(poll, 3000); setTimeout(poll, 900);
  }
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", SIMVALS_JS + "</body>", 1)
SIM_PAGE = SIM_PAGE.replace("</body>", SIMVALS_JS + "</body>", 1)


# ---- window (Tk): «🧪 Simulator» at the status lines and badges --------------------------------------------------------
def _sv_keys():
    v = STATE.get("simvals") or {}
    return set(v.get("keys") or []) if v.get("on") else set()


_SV_STATUS_KEYS = {"Battery": "battery", "Solar panel": "solar", "GPS module": "gps", "Storm warning": "weather", "Night report": "clock"}
_sv_status_orig = App._status


def _sv_status(self, sec, text):
    try:
        K = _sv_keys()
        if K and sec in _SV_STATUS_KEYS and _SV_STATUS_KEYS[sec] in K and "🧪" not in str(text):
            text = str(text) + "\n🧪 " + tr("from the simulator")
            if sec == "Battery" and SIMVAL.get("off"):
                text += " · ⏻ " + tr("Battery empty – the device would be off now")
        elif K and sec == "Simulator":
            v = STATE.get("simvals") or {}
            text = str(text) + "\n🧪 " + tr("Values from the simulator") + ": " + ", ".join(tr({"battery": "Battery", "clock": "Clock", "place": "Place",
                    "weather": "Weather", "pi_temp": "Pi temperature", "solar": "Solar panel", "gps": "GPS module", "net": "Network"}.get(k, k)) for k in sorted(K)) \
                + f"\n🕑 {v.get('time', '')} ({tr('night') if v.get('dark') else tr('day')})" + (f" · 📍 {v['place']}" if v.get("place") else "") \
                + (f" · 🌡 Pi {v['pi_temp']:.0f} °C" if isinstance(v.get("pi_temp"), (int, float)) else "") \
                + (("\n📵 " + tr("Wi-Fi gone" if v.get("net") == "wifi" else "Internet gone") + " – " + tr("Simulator test: push messages wait and are sent later")) if v.get("net") else "")
    except Exception:
        pass
    return _sv_status_orig(self, sec, text)


_sv_sb_orig = App._sb


def _sv_sb(self, key, text, color=None, show=True):
    try:
        if key == "b_batt" and "battery" in _sv_keys() and "🧪" not in str(text):
            text = str(text) + " 🧪"
    except Exception:
        pass
    return _sv_sb_orig(self, key, text, color, show)


_sv_cpu_orig = App._update_cpu


def _sv_update_cpu(self):
    r = _sv_cpu_orig(self)
    try:
        if "pi_temp" in _sv_keys() and self.l_cpu_info is not None and "🧪" not in self.l_cpu_info.cget("text"):
            self.l_cpu_info.config(text=self.l_cpu_info.cget("text") + " · 🧪 " + tr("Pi temperature from the simulator"))
    except Exception:
        pass
    return r


_sv_wifi_orig = App._update_wifi


def _sv_update_wifi(self):
    r = _sv_wifi_orig(self)
    try:
        nd = (STATE.get("simvals") or {}).get("net")
        if nd and self.l_wifi is not None and "🧪" not in self.l_wifi.cget("text"):
            self.l_wifi.config(text=self.l_wifi.cget("text") + "\n📵 🧪 " + tr("Wi-Fi gone" if nd == "wifi" else "Internet gone") + " – "
                               + tr("Simulator test: push messages wait and are sent later"), foreground=C["red"])
    except Exception:
        pass
    return r


# wraps: App._status
App._status = _sv_status
# wraps: App._sb
App._sb = _sv_sb
# wraps: App._update_cpu
App._update_cpu = _sv_update_cpu
# wraps: App._update_wifi
App._update_wifi = _sv_update_wifi

# ---- the manual (HELP_PAGE of 540): one paragraph in the section about the simulator, German and English ----------------
_SV_HELP = {
    "de": "<p><b>🧪 Werte aus dem Simulator (ab 2.98.47):</b> Ist MoveEye mit dem 3D-Simulator verbunden, kommen die «Hardware»-Werte "
          "aus der simulierten Welt: Akku (ein simulierter USV-HAT mit 2 × 18650 – entlädt sich mit Pi, Servos, Licht und Sirene, lädt mit "
          "dem Solarpanel oder dem Netzteil, Kälte senkt die Kapazität), Uhrzeit und Datum (Zeitpläne, Nachtbericht, «Heute Nacht bewachen», "
          "Nacht-Prognose – auch im Zeitraffer), Ort (Sonnenauf- und -untergang), Wetter und Böen-Prognose (kein Internet-Wetter), die "
          "Temperatur des Pi (Hitze-Warnung, KI langsamer) und der Test «WLAN weg» / «Internet weg» (Alarme warten und werden nachgeschickt). "
          "Solar, GPS, Aussentemperatur, Wind, Geräusche, Wärmebild und Sensoren kamen schon vorher vom Simulator. Jeder solche Wert trägt "
          "«🧪». Die Regler sind im Simulator unter Sensoren → «Strom» und «Netz». Protokoll, Dateinamen, Signaturen "
          "und Updates bleiben auf der echten Uhr. Antwortet der Simulator 10 Sekunden nicht, gelten wieder die echten Werte.</p>",
    "en": "<p><b>🧪 Values from the simulator (from 2.98.47):</b> while MoveEye is connected to the 3D simulator its «hardware» values come "
          "from the simulated world: battery (a simulated UPS HAT with 2 × 18650 – drained by the Pi, servos, light and siren, charged by the "
          "solar panel or a mains adapter, cold lowers the capacity), time and date (schedules, night report, «Guard tonight», night forecast – "
          "also in the time-lapse), place (sunrise and sunset), weather and gust forecast (no internet weather), the temperature of the Pi "
          "(heat warning, AI slower) and the test «Wi-Fi gone» / «Internet gone» (alarms wait and are sent later). Solar, GPS, outside "
          "temperature, wind, sounds, thermal camera and sensors came from the simulator before. Every such value carries «🧪». The controls "
          "are in the simulator under Sensors → «Strom» and «Netz». Log, file names, signatures and updates stay on "
          "the real clock. When the simulator does not answer for 10 seconds the real values apply again.</p>"}
for _a, _b in (('<section id="system" data-icon="⚙"><h2>System &amp; Netz</h2>', _SV_HELP["de"]),
               ('<section id="system" data-icon="⚙"><h2>System &amp; network</h2>', _SV_HELP["en"])):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)
