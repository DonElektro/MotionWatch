#@ MoveEye – Teil 639zu: «HP rechnet» – vom Handy aus zuschauen, was der Simulator-PC (HP) gerade rechnet (Dauerrechnen 3.55.0). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer (02.11.2026): der HP rechnet rund um die Uhr (Erkennung messen, KI-Trainingsbilder, Langzeittest; Werkzeug
# werkzeuge/test_runner/dauer.py). Hier nur ZUSCHAUEN, nichts steuern:
#   * Karte «HP rechnet» im Reiter Simulator (kleines Live-Bild, Arbeit, Fall N/M; Tipp -> ganze Ansicht /hp)
#   * Eintrag «HP rechnet» unter Einstellungen → Entwickler (devExtras, 530)
#   * /hp: dasselbe wie das Testbild am HP - Live-Bild mit MoveEyes Rahmen, Fortschritt, Bilanz, welche Arbeit läuft, oder
#     «Spielen – Rechnen pausiert» / «HP frei» / «HP nicht erreichbar».
# Der Weg: das Handy fragt nur MoveEye (/api/hp, /api/hp/bild.png; zu Hause und unterwegs über den gewohnten Zugang bzw.
# Tunnel). MoveEye fragt den HP im eigenen Netz: kleiner Status-Dienst der Kiosk-Sitzung (hp_wache.py, Port 8761, nur GET,
# nur private Adressen). Wo der HP steht, weiss MoveEye schon: die Adresse des Simulators (sim_url, Teil 290) bzw. die
# gefundenen Simulatoren (SIMFOUND, Teil 300). Gefragt wird nur, solange die Karte oder die Seite offen ist (sie fragen alle
# paar Sekunden; dazwischen ein kurzer Zwischenspeicher) - keine Dauerlast. Alles vom HP gilt als fremde Daten: nur bekannte
# Felder, gekürzt, Grösse begrenzt (JSON 64 KB, Bild 2,5 MB und nur PNG). Nur für den Besitzer (Rolle admin).
# Zuschauer (Entscheid Besitzer 03.11.2026): eine Verbindung MoveEye <-> Simulator allein hält den HP NICHT vom Rechnen ab.
# Nur wenn jemand im Simulator-Betrieb wirklich zuschaut - Reiter Live / Sim-Ansicht im Browser offen und sichtbar, oder
# das Fenster am Pi zeigt den Reiter Live (nicht verkleinert) -, schickt MoveEye alle ~20 s «POST /zuschauer» an den HP (nur eine Zeitmarke);
# dann pausiert der HP sein Rechnen und der Simulator läuft. Die Karte / Seite «HP rechnet» schicken das nie.
# ----------------------------------------------------------------------------
HPR_PORT = 8761
HPR = {"t": 0.0, "d": None, "host": "", "bild": b"", "bild_t": 0.0, "fehl_t": 0.0}
HPR_LOCK = threading.Lock()
HPR_ARBEITEN = ("Erkennung messen", "KI-Trainingsbilder", "Langzeittest")
_HPR_HOST_RE = re.compile(r"^[A-Za-z0-9.\-]{1,100}$|^\[?[0-9A-Fa-f:]{2,45}\]?$")


def hpr_hosts():
    """wo der HP sein kann: Rechner der Simulator-Adresse (nicht dieses Gerät), dann die gefundenen Simulatoren (letzte Std.)"""
    out = []
    try:
        h = urllib.parse.urlsplit(sim_base()).hostname or ""
    except ValueError:
        h = ""
    if h and not h.startswith("127.") and h not in ("localhost", "::1"):
        out.append(h)
    try:
        now = time.time()
        for e in sorted(list(SIMFOUND.values()), key=lambda e_: -float(e_.get("t") or 0)):
            ip = str(e.get("ip") or "")
            if ip and not ip.startswith("127.") and now - float(e.get("t") or 0) < 3600 and ip not in out:
                out.append(ip)
    except Exception:
        pass
    return [h_ for h_ in out if _HPR_HOST_RE.match(h_)][:4]


def _hpr_get(host, path, max_bytes, timeout=2.5):
    h = "[" + host.strip("[]") + "]" if ":" in host else host
    with _SIM_OPENER.open(urllib.request.Request("http://%s:%d%s" % (h, HPR_PORT, path), headers={"User-Agent": "MotionWatch"}),
                          timeout=timeout) as r:
        b_ = r.read(max_bytes + 1)
    if len(b_) > max_bytes:
        raise ValueError("zu gross")
    return b_


def _hpr_t(v, n):
    if not isinstance(v, str):
        return ""
    return "".join(c for c in v if c.isprintable()).strip()[:n]


def _hpr_z(v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v if lo <= v <= hi else None


def hpr_sauber(d):
    """Antwort des HP -> nur bekannte Felder (er steht im eigenen Netz, gilt trotzdem als fremd)"""
    if not isinstance(d, dict):
        return {"zustand": "unbekannt"}
    z = d.get("zustand") if d.get("zustand") in ("rechnet", "spielen", "frei") else "unbekannt"
    out = {"zustand": z}
    if z == "rechnet":
        f = d.get("fortschritt") if isinstance(d.get("fortschritt"), dict) else {}
        now = time.time()
        g_ = {"arbeit": _hpr_t(f.get("arbeit"), 30), "titel": _hpr_t(f.get("titel"), 40), "plan": _hpr_t(f.get("plan"), 24),
              "plan_text": _hpr_t(f.get("plan_text"), 90), "name": _hpr_t(f.get("name"), 60), "fall_name": _hpr_t(f.get("fall_name"), 14),
              "fall": _hpr_z(f.get("fall"), 0, 100000), "faelle": _hpr_z(f.get("faelle"), 1, 100000),
              "start": _hpr_z(f.get("start"), now - 7 * 86400, now + 600), "status": _hpr_t(f.get("status"), 20),
              "soll": _hpr_t(f.get("soll"), 20)}
        ist = f.get("ist") if isinstance(f.get("ist"), dict) else {}
        if ist:
            g_["ist"] = {"art": _hpr_t(ist.get("art"), 12), "text": _hpr_t(ist.get("text"), 30)}
        b_ = f.get("bilanz") if isinstance(f.get("bilanz"), dict) else {}
        bil = {}
        for k in ("personen", "ignoriert", "leer"):
            v = b_.get(k)
            if isinstance(v, list) and len(v) == 2 and all(_hpr_z(x, 0, 100000) is not None for x in v) and v[0] <= v[1]:
                bil[k] = [int(v[0]), int(v[1])]
        if _hpr_z(b_.get("pushes"), 0, 100000) is not None:
            bil["pushes"] = int(b_["pushes"])
        g_["bilanz"] = bil
        ka = []
        for k in (f.get("kacheln") if isinstance(f.get("kacheln"), list) else [])[:4]:
            if isinstance(k, list) and len(k) >= 2:
                ka.append([_hpr_t(k[0], 30), _hpr_t(k[1], 20), _hpr_t(k[2], 8) if len(k) > 2 and k[2] in ("gruen", "orange", "rot") else ""])
        g_["kacheln"] = ka
        le = f.get("letzter") if isinstance(f.get("letzter"), dict) else {}
        if le:
            g_["letzter"] = {"name": _hpr_t(le.get("name"), 60), "text": _hpr_t(le.get("text"), 60),
                             "ok": le.get("ok") if isinstance(le.get("ok"), bool) else None}
        if g_["fall"] is not None and g_["faelle"] is not None:
            g_["faelle"] = max(g_["faelle"], g_["fall"])
        out["fortschritt"] = {k: v for k, v in g_.items() if v not in ("", None, {}, [])}
        out["arbeit"] = d.get("arbeit") if d.get("arbeit") in HPR_ARBEITEN else (g_["arbeit"] if g_["arbeit"] in HPR_ARBEITEN else "")
        out["bild"] = d.get("bild") is True
    elif z == "spielen":
        s = d.get("spielen") if isinstance(d.get("spielen"), dict) else {}
        out["spielen"] = {"grund": _hpr_t(s.get("grund"), 20), "ruhe_noch_s": _hpr_z(s.get("ruhe_noch_s"), 0, 86400)}
    return out


def hpr_status():
    """{"ok", "bekannt" (ein HP ist bekannt), "erreichbar", "zustand", …} - höchstens alle 3 s wird der HP gefragt"""
    now = time.time()
    with HPR_LOCK:
        if HPR["d"] is not None and now - HPR["t"] < 3.0:
            return HPR["d"]
        hosts = hpr_hosts()
        if HPR["host"] in hosts:                            # der zuletzt erreichte zuerst
            hosts.remove(HPR["host"])
            hosts.insert(0, HPR["host"])
        res = {"ok": True, "bekannt": bool(hosts), "erreichbar": False, "zustand": "unbekannt", "t": int(now)}
        if hosts and HPR["fehl_t"] and now - HPR["fehl_t"] < 10:
            pass                                            # eben nicht erreicht: 10 s nicht wieder fragen
        elif hosts:
            for h in hosts:
                try:
                    d = json.loads(_hpr_get(h, "/status.json", 65536).decode("utf-8", "replace"))
                except (OSError, ValueError):
                    continue
                res.update(hpr_sauber(d), erreichbar=True)
                HPR["host"] = h
                break
            else:
                HPR["fehl_t"] = now
            if res["erreichbar"]:
                HPR["fehl_t"] = 0.0
        HPR.update(t=now, d=res)
        return res


HPR_ZU = {"t": 0.0, "faden": False, "app": None}


def hpr_zuschauer(was):
    """jemand schaut im Simulator-Betrieb zu (Live / Sim-Ansicht / Fenster): dem HP melden (höchstens alle 15 s, im
    Hintergrund). Nur, wenn die Simulation an ist und der Simulator auf einem anderen Rechner läuft."""
    if was not in ("live", "fenster", "spiel") or not CFG.get("sim_on"):
        return False
    try:
        h = urllib.parse.urlsplit(sim_base()).hostname or ""
    except ValueError:
        return False
    if not h or h.startswith("127.") or h in ("localhost", "::1") or not _HPR_HOST_RE.match(h):
        return False
    now = time.time()
    with HPR_LOCK:
        if now - HPR_ZU["t"] < 15:
            return True
        HPR_ZU["t"] = now

    def senden():
        hh = "[" + h.strip("[]") + "]" if ":" in h else h
        try:
            req = urllib.request.Request("http://%s:%d/zuschauer" % (hh, HPR_PORT), data=json.dumps({"was": was}).encode(),
                                         headers={"User-Agent": "MotionWatch", "Content-Type": "application/json"})
            with _SIM_OPENER.open(req, timeout=3) as r:
                r.read(65536)
        except (OSError, ValueError):
            pass                                      # kein HP mit Dauerrechnen dort: egal
    threading.Thread(target=senden, daemon=True, name="hpr-zuschauer").start()
    return True


def hpr_fenster_schaut():
    """das Fenster am Pi ist ein Zuschauer - gleiche Regel wie im Browser: es ist sichtbar (nicht verkleinert, STATE
    local_view_t, Teil 570) UND zeigt den Reiter Live (App.tab)"""
    app = HPR_ZU.get("app")
    return (app is not None and getattr(app, "tab", "") == "live"
            and time.time() - float(STATE.get("local_view_t") or 0) <= 5)


def _hpr_fenster_faden():
    while True:
        time.sleep(20)
        try:
            if hpr_fenster_schaut():
                hpr_zuschauer("fenster")
        except Exception:
            pass


if GUI_OK:                                                # das Fenster merken (für den Reiter, nur lesen)
    _hpr_app_init_base = App.__init__

    def _hpr_app_init(self, *a, **kw):
        HPR_ZU["app"] = self
        _hpr_app_init_base(self, *a, **kw)
    # wraps: App.__init__
    App.__init__ = _hpr_app_init


def hpr_bild():
    """das kleine Live-Bild des HP (PNG) - nur während er rechnet; höchstens alle 4 s neu geholt"""
    now = time.time()
    with HPR_LOCK:
        if HPR["bild"] and now - HPR["bild_t"] < 4.0:
            return HPR["bild"]
    st = hpr_status()
    if not (st.get("erreichbar") and st.get("zustand") == "rechnet" and st.get("bild")):
        return b""
    try:
        b_ = _hpr_get(HPR["host"], "/bild.png", 2_500_000, timeout=4.0)
    except (OSError, ValueError):
        return b""
    if not b_.startswith(b"\x89PNG\r\n\x1a\n"):
        return b""
    with HPR_LOCK:
        HPR.update(bild=b_, bild_t=now)
    return b_


# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_HPR = {
    "HP computes": ("HP rechnet", "Le PC HP calcule", "Il PC HP calcola", "Il PC HP quinta"),
    "Measuring detection": ("Erkennung messen", "Mesurer la détection", "Misurare il rilevamento", "Mesirar la renconuschientscha"),
    "AI training pictures": ("KI-Trainingsbilder", "Images d'entraînement IA", "Immagini di addestramento IA", "Maletgs da trenament IA"),
    "Long-run test": ("Langzeittest", "Test de longue durée", "Test di lunga durata", "Test da lunga durada"),
    "Playing – computing paused": ("Spielen – Rechnen pausiert", "On joue – calcul en pause", "Si gioca – calcolo in pausa",
                                   "Ins giogia – il quint è en pausa"),
    "HP not reachable": ("HP nicht erreichbar", "PC HP injoignable", "PC HP non raggiungibile", "PC HP betg cuntanschibel"),
    "HP free – the simulator is running": ("HP frei – der Simulator läuft", "PC HP libre – le simulateur tourne",
                                           "PC HP libero – il simulatore è in funzione", "PC HP liber – il simulatur va"),
    "No HP known yet: connect MoveEye once with the simulator on the HP.": (
        "Noch kein HP bekannt: MoveEye einmal mit dem Simulator auf dem HP verbinden.",
        "Aucun PC HP connu : connecte une fois MoveEye au simulateur sur le PC HP.",
        "Nessun PC HP noto: collega una volta MoveEye al simulatore sul PC HP.",
        "Anc nagin PC HP enconuschent: collia ina giada MoveEye cun il simulatur sin il PC HP."),
    "Case": ("Fall", "Cas", "Caso", "Cas"),
    "since": ("seit", "depuis", "da", "dapi"),
    "rest about": ("Rest etwa", "reste environ", "resto circa", "rest var"),
    "Persons detected": ("Personen erkannt", "Personnes détectées", "Persone rilevate", "Persunas renconuschidas"),
    "Animals / cars ignored": ("Tiere / Autos ignoriert", "Animaux / voitures ignorés", "Animali / auto ignorati", "Animals / autos ignorads"),
    "Idle quiet": ("Leerlauf ruhig", "Ralenti calme", "Inattivo tranquillo", "Marscha vida quieta"),
    "Pushes": ("Pushes", "Notifications", "Notifiche", "Avis push"),
    "Last case": ("Letzter Fall", "Dernier cas", "Ultimo caso", "Ultim cas"),
    "Should": ("Soll", "Attendu", "Atteso", "Duess"),
    "Is": ("Ist", "Vu", "Visto", "È"),
    "Computing goes on after 15 min without playing": ("Weitergerechnet wird nach 15 Min. ohne Spielen",
                                                        "Le calcul reprend après 15 min sans jeu",
                                                        "Il calcolo riprende dopo 15 min senza giocare",
                                                        "Il quint cuntinuescha suenter 15 min senza giugar"),
    "in about": ("in etwa", "dans environ", "tra circa", "en var"),
    "Watch only – the HP computes by itself.": ("Nur zuschauen – der HP rechnet von selbst.", "Seulement regarder – le PC HP calcule tout seul.",
                                                "Solo guardare – il PC HP calcola da solo.", "Mo guardar – il PC HP quinta sez."),
    "Live picture of the HP": ("Live-Bild des HP", "Image en direct du PC HP", "Immagine dal vivo del PC HP", "Maletg live dal PC HP"),
    "No picture yet": ("Noch kein Bild", "Pas encore d'image", "Ancora nessuna immagine", "Anc nagin maletg"),
    "Back": ("Zurück", "Retour", "Indietro", "Enavos"),
    "Tap for the full view": ("Antippen für die ganze Ansicht", "Toucher pour la vue complète", "Tocca per la vista completa",
                              "Tutgar per la vista cumpletta"),
}
for _k, _v in _HX_HPR.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


def hpr_tx():
    return {L: {k: v[i] for k, v in _HX_HPR.items()} for i, L in enumerate(("de", "fr", "it", "rm"))}


# gemeinsam für Karte und Seite: Texte, Zeichnen der Angaben (nur textContent, nichts vom HP als HTML)
HPR_JS = r"""<script>
(function () {
  if (window.HPR) return;
  const TX = /*HPRTX*/{};
  const L = () => (typeof LANG === "string" && LANG) || (document.documentElement.lang || "de").slice(0, 2);
  const T = k => ((TX[L()] || {})[k]) || k;
  const ARB = {"Erkennung messen": "Measuring detection", "KI-Trainingsbilder": "AI training pictures", "Langzeittest": "Long-run test"};
  const E = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const dauer = s => { const m = Math.max(0, Math.round(s / 60)); return m < 60 ? m + " Min." : Math.floor(m / 60) + ":" + String(m % 60).padStart(2, "0") + " h"; };
  async function holen() { try { const r = await fetch("/api/hp", {cache: "no-store"}); return r.ok ? await r.json() : null; } catch (e) { return null; } }
  function titel(j) {
    if (!j || !j.bekannt) return ["⚪", T("No HP known yet: connect MoveEye once with the simulator on the HP.")];
    if (!j.erreichbar) return ["⚪", T("HP not reachable")];
    if (j.zustand === "spielen") return ["🎮", T("Playing – computing paused")];
    if (j.zustand === "frei") return ["🟢", T("HP free – the simulator is running")];
    if (j.zustand === "rechnet") return ["🟠", T("HP computes") + (j.arbeit ? " · " + T(ARB[j.arbeit] || j.arbeit) : "")];
    return ["⚪", T("HP not reachable")];
  }
  function zeile(j) {                       // kurz: Fall N/M · Name
    const f = (j && j.fortschritt) || {};
    if (!j || j.zustand !== "rechnet") {
      if (j && j.zustand === "spielen") { const r = (j.spielen || {}).ruhe_noch_s; return T("Computing goes on after 15 min without playing") + (r != null ? " (" + T("in about") + " " + dauer(r) + ")" : "") + "."; }
      return "";
    }
    const n = f.fall, m = f.faelle, fn = f.fall_name || T("Case");
    return [n && m ? fn + " " + n + " / " + m + " (" + Math.round(Math.max(0, (n - 1) / m) * 100) + " %)" : "", f.name || f.plan_text || ""].filter(Boolean).join(" · ");
  }
  function kacheln(j) {
    const f = (j && j.fortschritt) || {};
    if (f.kacheln && f.kacheln.length) return f.kacheln.map(k => [k[0], k[1], k[2] || ""]);
    const b = f.bilanz || {}, p = v => v ? v[0] + " / " + v[1] : "–";
    const fb = v => !v || !v[1] ? "" : v[0] === v[1] ? "gruen" : v[0] >= 0.8 * v[1] ? "orange" : "rot";
    if (!Object.keys(b).length) return [];
    return [[T("Persons detected"), p(b.personen), fb(b.personen)], [T("Animals / cars ignored"), p(b.ignoriert), fb(b.ignoriert)],
            [T("Idle quiet"), p(b.leer), fb(b.leer)], [T("Pushes"), b.pushes != null ? String(b.pushes) : "–", ""]];
  }
  window.HPR = {T, E, holen, titel, zeile, kacheln, dauer};
})();
</script>"""

HPR_CSS = """<style>
.hpr-card{display:flex;gap:12px;align-items:center;color:var(--txt);text-decoration:none;border-radius:12px}
.hpr-card img{width:160px;max-width:42%;aspect-ratio:16/9;object-fit:cover;border-radius:8px;background:#0f1624;flex:0 0 auto}
.hpr-card .hpr-t{flex:1 1 auto;min-width:0}.hpr-card b{display:block;font-size:15px}.hpr-card .mut{font-size:12px;overflow-wrap:anywhere}
.hpr-bar{height:6px;border-radius:3px;background:var(--line);margin:6px 0 2px;overflow:hidden}.hpr-bar i{display:block;height:100%;background:#f59a4a}
.hpr-k{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:12px;margin-top:4px}.hpr-k span b{display:inline;font-size:12px}
.hpr-gruen{color:#3ecf8e}.hpr-orange{color:#f59a4a}.hpr-rot{color:#ef5b5b}
</style>"""

HPR_CARD = (HPR_CSS + """
  <details class="sc fold wide" id="c-hp" data-k="hp" hidden open>
    <summary><h2><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg><span data-i18n="HP computes">HP computes</span><span class="mut hsub" id="hp-sub"></span></h2></summary>
    <div class="fb"><a class="hpr-card" href="/hp" id="hp-card"><img id="hp-img" alt="" hidden><div class="hpr-t"><b id="hp-t1"></b>
      <div class="mut" id="hp-t2"></div><div class="hpr-bar" id="hp-bar" hidden><i id="hp-bari"></i></div><div class="hpr-k" id="hp-k"></div>
      <div class="mut" id="hp-t3"></div></div><span class="ar" style="margin-left:auto;color:var(--mut);font-size:18px">›</span></a></div>
  </details>
""")

HPR_CARD_JS = r"""<script>
(function () {
  const box = document.getElementById("c-hp"); if (!box || !window.HPR) return;
  const H = window.HPR, $i = id => document.getElementById(id);
  let tm = 0, bt = 0, warBild = false;
  async function lauf() {
    clearTimeout(tm);
    if (document.hidden || !box.open && !box.hidden) { tm = setTimeout(lauf, 4000); return; }   // nur solange sichtbar und offen
    const j = await H.holen();
    if (!j || j.ok === false) { box.hidden = true; tm = setTimeout(lauf, 60000); return; }       // kein Recht / alte Fassung
    box.hidden = !j.bekannt;
    const [ic, t1] = H.titel(j); $i("hp-t1").textContent = ic + " " + (j.zustand === "rechnet" ? t1.replace(H.T("HP computes") + " · ", "") : t1);
    $i("hp-sub").textContent = j.zustand === "rechnet" ? "· " + H.T(({"Erkennung messen": "Measuring detection", "KI-Trainingsbilder": "AI training pictures", "Langzeittest": "Long-run test"})[j.arbeit] || "HP computes") : "";
    $i("hp-t2").textContent = H.zeile(j);
    const f = j.fortschritt || {};
    const an = j.zustand === "rechnet" && f.fall && f.faelle;
    $i("hp-bar").hidden = !an; if (an) $i("hp-bari").style.width = Math.round(Math.max(0, (f.fall - 1) / f.faelle) * 100) + "%";
    const k = $i("hp-k"); k.textContent = "";
    if (j.zustand === "rechnet") H.kacheln(j).forEach(([n, v, c]) => { const s = H.E("span", "", n + ": "); const b = H.E("b", c ? "hpr-" + c : "", v); s.appendChild(b); k.appendChild(s); });
    $i("hp-t3").textContent = j.bekannt ? H.T("Tap for the full view") : "";
    const img = $i("hp-img"), bild = j.zustand === "rechnet" && j.bild;
    if (bild && (!warBild || Date.now() - bt > 10000)) { img.src = "/api/hp/bild.png?t=" + Date.now(); bt = Date.now(); }
    img.hidden = !bild; warBild = bild;
    tm = setTimeout(lauf, !j.bekannt ? 60000 : j.zustand === "rechnet" ? 6000 : 15000);
  }
  box.addEventListener("toggle", () => { if (box.open) lauf(); });
  document.addEventListener("visibilitychange", () => { if (!document.hidden) lauf(); });
  setTimeout(lauf, 800);
})();
</script>"""

HPR_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MoveEye - HP</title>
<style>
/*BASECSS*/
main{padding:14px 16px 40px;max-width:1180px;margin:0 auto}
.hp-kopf{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 10px}.hp-kopf h2{margin:0;font-size:20px}
.hp-kopf .mut{font-size:13px}.hp-kopf a{margin-left:auto}
.hp-grid{display:grid;grid-template-columns:1fr;gap:12px}
@media (min-width:900px){.hp-grid{grid-template-columns:minmax(0,1.45fr) minmax(0,1fr)}}
.hp-p{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;min-width:0}
.hp-p h3{margin:0 0 8px;font-size:12px;letter-spacing:.06em;color:var(--mut);text-transform:uppercase;font-weight:600}
.hp-bild{position:relative;width:100%;aspect-ratio:16/9;background:#0f1624;border-radius:10px;overflow:hidden;display:flex;align-items:center;justify-content:center}
.hp-bild img{width:100%;height:100%;object-fit:contain}.hp-bild .mut{position:absolute;color:#9aa6bd}
.hp-live{position:absolute;top:8px;left:8px;background:rgba(15,22,36,.75);color:#f59a4a;font:600 12px system-ui;padding:3px 8px;border-radius:8px}
.hp-soll{margin-top:8px;font-size:16px}.hp-soll b{font-weight:600}
.hp-fall{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.hp-fall .gr{font-size:34px;font-weight:700;color:#f59a4a}
.hp-fall .pc{margin-left:auto;font-size:20px;font-weight:600}
.hp-bar{height:10px;border-radius:5px;background:var(--line);margin:10px 0 6px;overflow:hidden}.hp-bar i{display:block;height:100%;background:#f59a4a}
.hp-tiles{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.hp-tile{background:var(--bg);border-radius:10px;padding:10px 12px;min-width:0}.hp-tile small{color:var(--mut);display:block;font-size:12px}
.hp-tile b{font-size:26px;font-weight:700;overflow-wrap:anywhere}
.hpr-gruen{color:#3ecf8e}.hpr-orange{color:#f59a4a}.hpr-rot{color:#ef5b5b}
.hp-gross{text-align:center;padding:40px 16px}.hp-gross .ic{font-size:54px}.hp-gross b{display:block;font-size:22px;margin:8px 0}
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
  <div class="hp-kopf"><h2 id="hp-h">🖥 <span data-i18n="HP computes">HP computes</span></h2><span class="mut" id="hp-note"></span>
    <a class="btn sec" href="/sim" id="hp-back">‹ <span data-i18n="Back">Back</span></a></div>
  <div id="hp-inhalt"></div>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"HP computes": "HP rechnet", "Back": "Zurück"});
</script>
/*HPRJS*/
<script>
(function () {
  const H = window.HPR, root = document.getElementById("hp-inhalt"), E = H.E;
  let tm = 0, bt = 0, ansicht = "";
  document.getElementById("hp-note").textContent = H.T("Watch only – the HP computes by itself.");
  function aufbau(z) {
    root.textContent = ""; ansicht = z;
    if (z !== "rechnet") { const g = E("div", "hp-p hp-gross"); g.append(E("div", "ic", ""), E("b", "", ""), E("div", "mut", "")); g.id = "hp-g"; root.appendChild(g); return; }
    const grid = E("div", "hp-grid"), l = E("div", "hp-p"), r = E("div", "");
    l.appendChild(E("h3", "", H.T("Live picture of the HP")));
    const b = E("div", "hp-bild"); const img = E("img"); img.id = "hp-img"; img.alt = ""; const leer = E("span", "mut", H.T("No picture yet")); leer.id = "hp-leer";
    const live = E("span", "hp-live", "● LIVE"); b.append(img, leer, live); l.appendChild(b);
    const so = E("div", "hp-soll"); so.id = "hp-soll"; l.appendChild(so);
    const p1 = E("div", "hp-p"); p1.id = "hp-fort"; const p2 = E("div", "hp-p"); p2.id = "hp-bil"; p2.style.marginTop = "12px";
    r.append(p1, p2); grid.append(l, r); root.appendChild(grid);
  }
  function malen(j) {
    const z = j && j.erreichbar ? j.zustand : "weg";
    if ((z === "rechnet") !== (ansicht === "rechnet") || !ansicht) aufbau(z);
    const [ic, t1] = H.titel(j);
    if (z !== "rechnet") { const g = document.getElementById("hp-g"); g.children[0].textContent = ic; g.children[1].textContent = t1; g.children[2].textContent = H.zeile(j); return; }
    const f = j.fortschritt || {}, now = Date.now() / 1000;
    const img = document.getElementById("hp-img"), leer = document.getElementById("hp-leer");
    if (j.bild && Date.now() - bt > 4500) { img.src = "/api/hp/bild.png?t=" + Date.now(); bt = Date.now(); }
    img.hidden = !j.bild; leer.hidden = !!j.bild;
    const so = document.getElementById("hp-soll"); so.textContent = "";
    if (f.soll) { so.append(E("span", "mut", H.T("Should") + ": "), E("b", "", f.soll)); if (f.ist && f.ist.text) { const ok = (f.soll === "Person") === (f.ist.art === "person"); so.append(E("span", "mut", "   " + H.T("Is") + ": "), E("b", ok ? "hpr-gruen" : "hpr-orange", f.ist.text)); } }
    const p1 = document.getElementById("hp-fort"); p1.textContent = "";
    p1.appendChild(E("h3", "", [j.arbeit ? H.T(({"Erkennung messen": "Measuring detection", "KI-Trainingsbilder": "AI training pictures", "Langzeittest": "Long-run test"})[j.arbeit]) : "", f.plan ? "Plan " + f.plan : "", f.plan_text || ""].filter(Boolean).join(" · ")));
    const fa = E("div", "hp-fall");
    if (f.fall && f.faelle) { const a = Math.max(0, Math.min(1, (f.fall - 1) / f.faelle)); fa.append(E("span", "gr", (f.fall_name || H.T("Case")) + " " + f.fall), E("span", "mut", "/ " + f.faelle), E("span", "pc", Math.round(a * 100) + " %"));
      p1.appendChild(fa); p1.appendChild(E("div", "", f.name || "")); const bar = E("div", "hp-bar"), i = E("i"); i.style.width = Math.round(a * 100) + "%"; bar.appendChild(i); p1.appendChild(bar);
      let zt = f.start ? H.T("since") + " " + H.dauer(now - f.start) : "";
      if (f.start && f.fall > 2) zt += " · " + H.T("rest about") + " " + H.dauer((now - f.start) / (f.fall - 1) * (f.faelle - f.fall + 1));
      p1.appendChild(E("div", "mut", zt));
    } else { fa.append(E("span", "gr", "…")); p1.appendChild(fa); p1.appendChild(E("div", "", f.name || "")); }
    const p2 = document.getElementById("hp-bil"); p2.textContent = "";
    const ks = H.kacheln(j);
    if (ks.length) { const t = E("div", "hp-tiles"); ks.forEach(([n, v, c]) => { const d = E("div", "hp-tile"); d.append(E("small", "", n), E("b", c ? "hpr-" + c : "", v)); t.appendChild(d); }); p2.appendChild(t); }
    if (f.letzter && f.letzter.name) { p2.appendChild(E("div", "mut", H.T("Last case") + ": " + f.letzter.name)); p2.appendChild(E("div", f.letzter.ok ? "hpr-gruen" : f.letzter.ok === false ? "hpr-rot" : "", f.letzter.text || "")); }
    p2.hidden = !p2.children.length;
  }
  async function lauf() {
    clearTimeout(tm);
    if (document.hidden) { tm = setTimeout(lauf, 3000); return; }          // nur solange die Seite sichtbar ist
    const j = await H.holen();
    if (j) malen(j);
    tm = setTimeout(lauf, j && j.zustand === "rechnet" ? 3000 : 8000);
  }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) lauf(); });
  (async () => { if (typeof initAppearance === "function") await initAppearance(); lauf(); })();
})();
</script>
<script>/*ALERTS*/</script>
</body></html>
"""


def hpr_js():
    return HPR_JS.replace("/*HPRTX*/{}", json.dumps(hpr_tx(), ensure_ascii=False).replace("</", "<\\/"))


def hpr_page():
    return render_page(HPR_PAGE, "sim").replace("/*HPRJS*/", hpr_js(), 1)


# Karte im Reiter Simulator: vor der Simulator-Zentrale (eigene Karte, nur wenn ein HP bekannt ist)
_HPR_ANKER = '<section class="sc wide" id="c-hub"'
if _HPR_ANKER in SIM_PAGE:
    SIM_PAGE = SIM_PAGE.replace(_HPR_ANKER, HPR_CARD + _HPR_ANKER, 1)
    SIM_PAGE = SIM_PAGE.replace("</body>", hpr_js() + "<script>Object.assign(I18N.de, " + json.dumps(
        {"HP computes": _HX_HPR["HP computes"][0]}, ensure_ascii=False) + ");</script>" + HPR_CARD_JS + "</body>", 1)

# Reiter Live (auch die Sim-Ansicht, 639zt): solange die Seite sichtbar ist, alle 20 s ein Zuschauer-Puls (der Server
# meldet ihn nur im Simulator-Betrieb weiter)
HPR_LIVE_JS = r"""<script>
(function () {
  if (window._hprZu || !document.body || document.body.dataset.tab !== "live") return; window._hprZu = true;
  const puls = () => { if (document.hidden) return; fetch("/api/hp/zuschauer", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({was: "live"}), cache: "no-store"}).catch(() => {}); };
  setInterval(puls, 20000); setTimeout(puls, 1500);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) puls(); });
})();
</script>"""
WEB_PAGE = WEB_PAGE.replace("</body>", HPR_LIVE_JS + "</body>", 1)

# Einstellungen → Entwickler (530 devExtras): Eintrag «HP rechnet» vor «Entwickler-Bereich»
_HPR_DEV = '["⚗", "Settings of the simulation", "/sim"], ["🛠", "Developer area", "/dev"]]'
if _HPR_DEV in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_HPR_DEV, '["⚗", "Settings of the simulation", "/sim"], ["🖥", "HP computes", "/hp"], ["🛠", "Developer area", "/dev"]]', 1)
    WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps({"HP computes": _HX_HPR["HP computes"][0]}, ensure_ascii=False)
                                + ");</script></body>", 1)


_smalltv_routes_hpr_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zu: /hp, /api/hp, /api/hp/bild.png (nur zuschauen)
    _smalltv_routes_hpr_base(app, reply, body)
    from flask import Response, g

    def _darf():
        return getattr(g, "role", "admin") == "admin"

    @app.route("/hp")
    def hpr_page_():
        if not _darf():
            return Response("forbidden", 403)
        return Response(hpr_page(), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/hp")
    def hpr_api_():
        if not _darf():
            return reply({"ok": False, "error": "forbidden"}, 403)
        return reply(hpr_status())

    @app.route("/api/hp/zuschauer", methods=["POST"])
    def hpr_zuschauer_():                                # Puls vom Reiter Live (jede angemeldete Rolle; nur eine Zeitmarke)
        return reply({"ok": True, "gemeldet": hpr_zuschauer(str(body().get("was") or ""))})

    if not HPR_ZU["faden"]:
        HPR_ZU["faden"] = True
        threading.Thread(target=_hpr_fenster_faden, daemon=True, name="hpr-fenster").start()

    @app.route("/api/hp/bild.png")
    def hpr_bild_():
        if not _darf():
            return Response("forbidden", 403)
        b_ = hpr_bild()
        if not b_:
            return Response("no picture", 404, headers={"Cache-Control": "no-store"})
        return Response(b_, mimetype="image/png", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
