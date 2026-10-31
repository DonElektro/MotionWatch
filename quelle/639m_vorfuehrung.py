#@ MoveEye – Teil 639m: Vorführung «Maggie und der Bergkristall» (Daniel 31.10.2026) – live im Browser: Vollbild-Ansicht /sim/vorfuehrung ohne Bedienelemente (Bild des Simulators, Pause / Weiter / Kapitel / Beenden, am Handy tauglich), Start Kurzfassung / ganz; nur der Besitzer; Einstieg über Entwickler (Web, Fenster) und die Karte «Entwickler» der Simulator-Seite. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Der 3D-Simulator spielt die Geschichte selbst (simulator3d/scripts/maggie_vorfuehrung.gd, Autopilot + Film-Kamera,
# eigener Vorführ-Spielstand). Hier nur das Zuschauen:
#   * Seite /sim/vorfuehrung: das Bild des Simulators (/sim/view.jpg?bare=1 – ohne die Knöpfe des Simulator-Fensters, die
#     Leiste der Vorführung blendet der Simulator dann auch aus), Bild für Bild geholt (nie eine wachsende Verzögerung);
#     unten eine Leiste (verschwindet nach 4 s, Tippen zeigt sie wieder): Pause / Weiter, Kapitel zurück / Liste / weiter,
#     Beenden, Vollbild. Ohne laufende Vorführung: Start «Kurzfassung» / «Ganze Geschichte».
#   * /api/vorfuehrung: GET = Stand (Simulator /control vorfuehrung info), POST {do: start (len) | pause | weiter |
#     kapitel (n) | stop}. Nur der Besitzer (nacht_may: Administrator, nicht im Bedienermodus) – neue Adressen sind
#     ohnehin nur für den Administrator (040 VIEW_GET). Der Simulator nimmt die Befehle nur von diesem PC oder vom
#     verbundenen MoveEye an (net.gd dangerous, wie werk reset).
#   * Einstieg: Einstellungen → Entwickler (Web 530 devExtras, Fenster 639c) und die Karte «Entwickler» der
#     Simulator-Seite (dort zusätzlich die Start-Knöpfe des Simulators, Gruppe Entwickler) – nur mit dem Entwickler-Bereich.
# Hier (nach 639i, vor 640) weil render_page (510/584), sim_control (290), nacht_may (579b), SIM_PAGE (470), WEB_PAGE,
# smalltv_routes (552 …) und die Tabellen DE / TRX vorher kommen.
# ----------------------------------------------------------------------------
VF_DO = ("start", "pause", "weiter", "kapitel", "stop")


def vf_info():
    """the state of the Vorführung in the simulator ({ok: False, error} without simulator)"""
    if not CFG.get("sim_on"):
        return {"ok": False, "error": tr("The 3D simulator is not connected."), "offline": True}
    try:
        r = sim_control({"action": "vorfuehrung", "do": "info"}) or {}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
    if not r.get("ok") and "laeuft" not in r:
        if "unknown" in str(r.get("error") or "").lower():     # an older simulator (before the Vorführung)
            return {"ok": False, "error": tr("This simulator has no Vorführung yet – update it.")}
        return {"ok": False, "error": str(r.get("error") or tr("The 3D simulator is not connected."))[:120]}
    return r


def vf_do(d, owner=True):
    """start / pause / weiter / kapitel / stop – only the owner"""
    if not owner:
        log_event("web", "Vorführung refused (not the owner / operator mode)")
        return {"ok": False, "error": tr("Only the owner can do this."), "code": 403}
    w = str((d or {}).get("do") or "")
    if w not in VF_DO:
        return {"ok": False, "error": "do: " + " | ".join(VF_DO), "code": 400}
    if not CFG.get("sim_on"):
        return {"ok": False, "error": tr("The 3D simulator is not connected.")}
    c = {"action": "vorfuehrung", "do": w}
    if w == "start":
        c["len"] = "ganz" if str(d.get("len") or "") == "ganz" else "kurz"
    if w == "kapitel":
        try:
            c["n"] = max(0, min(5, int(d.get("n"))))
        except (TypeError, ValueError):
            return {"ok": False, "error": "n", "code": 400}
    try:
        r = sim_control(c) or {}
    except Exception as e:
        if w == "start" and "timed out" in str(e):          # building the Bergtal takes a moment
            return {"ok": True, "loading": True}
        return {"ok": False, "error": str(e)[:80]}
    if r.get("error") == "nur_lokal":
        return {"ok": False, "error": tr("The simulator only takes this from the connected MoveEye – switch on the simulation.")}
    return r


VF_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MoveEye - Vorführung</title>
<style>
/*BASECSS*/
html,body{height:100%;margin:0;background:#000;overflow:hidden}
#vf-img{position:fixed;inset:0;width:100%;height:100%;object-fit:contain;background:#000;display:block}
#vf-bar{position:fixed;left:50%;bottom:calc(12px + env(safe-area-inset-bottom));transform:translateX(-50%);max-width:calc(100% - 20px);box-sizing:border-box;
  background:rgba(17,24,34,.88);border:1px solid var(--line);border-radius:14px;padding:8px 10px;transition:opacity .4s;z-index:3}
#vf-bar.off{opacity:0;pointer-events:none}
#vf-st{font-size:12px;color:var(--mut);text-align:center;margin:0 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vf-row{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}
.vf-row button,.vf-row select,.vf-row a{min-height:40px;font-size:14px}
#vf-start{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;z-index:4;padding:16px;box-sizing:border-box}
#vf-start .pl-card{max-width:440px;width:100%;border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:16px}
#vf-start h2{margin:0 0 6px;font-size:19px}
#vf-start .vf-row{justify-content:flex-start;margin-top:12px}
#vf-msg{position:fixed;top:10px;left:50%;transform:translateX(-50%);font-size:13px;color:#fff;background:rgba(0,0,0,.55);padding:4px 10px;border-radius:9px;z-index:5}
#vf-msg:empty{display:none}
@media(max-width:520px){.vf-row button,.vf-row select{flex:1 1 auto;font-size:13px;padding-left:8px;padding-right:8px}#vf-st{white-space:normal}}
</style></head><body>
<img id="vf-img" alt="">
<div id="vf-msg"></div>
<div id="vf-start" hidden><div class="pl-card">
  <h2 data-i18n="Maggie and the mountain crystal – as a film">Maggie and the mountain crystal – as a film</h2>
  <div class="mut" data-i18n="vf-intro">The simulator plays the story by itself, you just watch.</div>
  <div class="vf-row">
    <button type="button" onclick="vfDo({do:'start',len:'kurz'})" data-i18n="Short version (15–20 min)">Short version (15–20 min)</button>
    <button type="button" class="sec" onclick="vfDo({do:'start',len:'ganz'})" data-i18n="The whole story">The whole story</button>
    <a class="btn sec" href="/sim" data-mw-exit data-i18n="Back">Back</a>
  </div>
  <div class="mut" id="vf-err" style="margin-top:10px"></div>
</div></div>
<div id="vf-bar" class="off">
  <div id="vf-st"></div>
  <div class="vf-row">
    <button type="button" id="vf-pause" onclick="vfDo({do: S.pause ? 'weiter' : 'pause'})" data-i18n="Pause">Pause</button>
    <button type="button" class="sec" onclick="vfDo({do:'kapitel',n:Math.max(0,(S.kapitel||0)-1)})" data-i18n="Chapter back">Chapter back</button>
    <select id="vf-kap" onchange="vfDo({do:'kapitel',n:+this.value})"></select>
    <button type="button" class="sec" onclick="vfDo({do:'kapitel',n:Math.min(5,(S.kapitel||0)+1)})" data-i18n="Next chapter">Next chapter</button>
    <button type="button" class="sec" onclick="vfFull()" data-i18n="Full screen">Full screen</button>
    <button type="button" class="sec" onclick="vfDo({do:'stop'})" data-i18n="End the show">End the show</button>
  </div>
</div>
<script>
/*COMMON*/
/*VFDE*/
let S = {}, IMG_T = 0, HIDE_T = 0, BUSY = 0, LASTURL = "";
(async () => { try { await initAppearance(); } catch (e) {} vfInfo(); vfPic(); vfShow(); })();
function vfShow() { const b = document.getElementById("vf-bar"); b.classList.remove("off"); clearTimeout(HIDE_T);
  HIDE_T = setTimeout(() => { if (!S.pause) b.classList.add("off"); }, 4000); }
["pointerdown", "pointermove", "keydown"].forEach(e => addEventListener(e, vfShow, {passive: true}));
addEventListener("keydown", e => { if (!S.laeuft) return; if (e.key === "Escape") vfDo({do: "stop"}); else if (e.key === " ") { e.preventDefault(); vfDo({do: S.pause ? "weiter" : "pause"}); }
  else if (e.key === "ArrowRight") vfDo({do: "kapitel", n: Math.min(5, (S.kapitel || 0) + 1)}); else if (e.key === "ArrowLeft") vfDo({do: "kapitel", n: Math.max(0, (S.kapitel || 0) - 1)}); });
function vfFull() { const d = document.documentElement; try { (document.fullscreenElement ? document.exitFullscreen() : (d.requestFullscreen || d.webkitRequestFullscreen).call(d)); } catch (e) {} }
function vfPic() {                                   // one picture after the other (never a growing delay)
  const im = document.getElementById("vf-img"), w = Math.min(1600, Math.round(innerWidth * (devicePixelRatio || 1)));
  const n = new Image(); let done = false;
  const next = () => { if (done) return; done = true; clearTimeout(to); setTimeout(vfPic, S.laeuft ? 80 : 1500); };
  const to = setTimeout(next, 6000);
  n.onload = () => { if (LASTURL) URL.revokeObjectURL(LASTURL); im.src = n.src; next(); };
  n.onerror = next;
  n.src = "/sim/view.jpg?bare=1&clean=1&q=72&w=" + w + "&t=" + Date.now();
}
async function vfInfo() {
  let j = null;
  try { j = await (await fetch("/api/vorfuehrung", {cache: "no-store"})).json(); } catch (e) {}
  if (j) vfPaint(j);
  setTimeout(vfInfo, 2000);
}
function vfPaint(j) {
  S = j || {};
  const run = !!S.laeuft, st = document.getElementById("vf-start");
  st.hidden = run;
  document.getElementById("vf-bar").hidden = !run;
  document.getElementById("vf-err").textContent = !S.ok && S.error ? "⚠ " + S.error : (S.ergebnis && S.text ? t("Last run") + ": " + S.text : "");
  if (!run) return;
  document.getElementById("vf-pause").textContent = S.pause ? t("Continue") : t("Pause");
  const se = document.getElementById("vf-kap"), nm = S.kapitel_namen || [];
  if (se.options.length !== nm.length) { se.textContent = ""; nm.forEach((x, i) => { const o = document.createElement("option"); o.value = i; o.textContent = (i + 1) + " · " + x; se.appendChild(o); }); }
  if (document.activeElement !== se) se.value = String(Math.max(0, S.kapitel || 0));
  document.getElementById("vf-st").textContent = (S.laenge === "ganz" ? t("The whole story") : t("Short version")) + " · " + t("Chapter") + " " + (Math.max(0, S.kapitel || 0) + 1) + "/6 · " + (S.spielzeit || "")
    + (S.pause ? " · " + t("Paused") : "") + (S.blockiert ? " · ⚠ " + t("BLOCKED") + " " + S.blockiert : "");
  if (S.pause) vfShow();
}
async function vfDo(d) {
  if (BUSY) return; BUSY = 1; const m = document.getElementById("vf-msg");
  if (d.do === "start") m.textContent = t("The valley is being prepared …");
  try { const r = await (await fetch("/api/vorfuehrung", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)})).json();
    if (r && r.ok === false && r.error) m.textContent = "⚠ " + r.error; else { m.textContent = ""; if (r && "laeuft" in r) vfPaint(r); } }
  catch (e) { m.textContent = "⚠ " + e; }
  BUSY = 0; vfShow(); setTimeout(() => { if (!m.textContent.startsWith("⚠")) m.textContent = ""; }, 4000);
}
</script></body></html>"""

_HX_VF = {
    'Maggie and the mountain crystal – as a film': ('Maggie und der Bergkristall – als Film', 'Maggie et le cristal de montagne – en film',
                                                    'Maggie e il cristallo di montagna – come film', 'Maggie ed il cristal da muntogna – sco film'),
    'vf-intro': ('Der Simulator spielt die Geschichte selbst, du schaust nur zu. Eigener Vorführ-Spielstand – deine Spielstände bleiben, wie sie sind.',
                 'Le simulateur joue l’histoire tout seul, tu regardes. Partie de démonstration à part – tes parties restent intactes.',
                 'Il simulatore gioca la storia da solo, tu guardi. Partita dimostrativa a parte – le tue partite restano come sono.',
                 'Il simulatur giuga l’istorgia sez, ti guardas mo. Stadi da demonstraziun separà – tes stadis dal gieu restan sco ch’els èn.'),
    'Short version (15–20 min)': ('Kurzfassung (15–20 Min.)', 'Version courte (15–20 min)', 'Versione breve (15–20 min)', 'Versiun curta (15–20 min.)'),
    'Short version': ('Kurzfassung', 'Version courte', 'Versione breve', 'Versiun curta'),
    'The whole story': ('Ganze Geschichte', 'Toute l’histoire', 'Tutta la storia', 'Tut l’istorgia'),
    'Chapter back': ('Kapitel zurück', 'Chapitre précédent', 'Capitolo indietro', 'Chapitel enavos'),
    'Next chapter': ('Nächstes Kapitel', 'Chapitre suivant', 'Capitolo successivo', 'Proxim chapitel'),
    'Chapter': ('Kapitel', 'Chapitre', 'Capitolo', 'Chapitel'),
    'Full screen': ('Vollbild', 'Plein écran', 'Schermo intero', 'Maletg entir'),
    'End the show': ('Beenden', 'Terminer', 'Termina', 'Terminar'),
    'Paused': ('Pause', 'En pause', 'In pausa', 'Pausa'),
    'BLOCKED': ('BLOCKIERT', 'BLOQUÉ', 'BLOCCATO', 'BLOCCÀ'),
    'Last run': ('Letzter Durchlauf', 'Dernier passage', 'Ultimo passaggio', 'Ultim passagi'),
    'The valley is being prepared …': ('Das Tal wird vorbereitet …', 'La vallée se prépare …', 'La valle viene preparata …', 'La val vegn preparada …'),
    'Watch «Maggie» as a film (demo)': ('Vorführung «Maggie» ansehen (als Film)', 'Regarder «Maggie» en film (démo)', 'Guardare «Maggie» come film (demo)',
                                        'Guardar «Maggie» sco film (demonstraziun)'),
    'Only the owner can do this.': ('Das darf nur der Besitzer.', 'Seul le propriétaire peut faire cela.', 'Solo il proprietario può farlo.',
                                    'Quai po mo il possessur.'),
    'This simulator has no Vorführung yet – update it.': ('Dieser Simulator kennt die Vorführung noch nicht – bitte aktualisieren.',
                                                          'Ce simulateur ne connaît pas encore la démonstration – mets-le à jour.',
                                                          'Questo simulatore non conosce ancora la dimostrazione – aggiornalo.',
                                                          'Quest simulatur na conuscha anc betg la demonstraziun – actualisescha el.'),
    'The simulator only takes this from the connected MoveEye – switch on the simulation.': (
        'Der Simulator nimmt das nur vom verbundenen MoveEye an – schalte die Simulation ein.',
        'Le simulateur n’accepte cela que du MoveEye connecté – active la simulation.',
        'Il simulatore lo accetta solo dal MoveEye collegato – attiva la simulazione.',
        'Il simulatur accepta quai mo dal MoveEye collià – activescha la simulaziun.'),
}
for _k, _v in _HX_VF.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
_VF_KEYS = list(_HX_VF) + ["Pause", "Continue", "Back", "The 3D simulator is not connected."]

# the way in: Settings → Developer (web 530 devExtras, window 639c has the same row there) and the card «Entwickler» of
# the Simulator page (only shown with the developer area)
WEB_PAGE = WEB_PAGE.replace('["🛠", "Developer area", "/dev"]]', '["🛠", "Developer area", "/dev"], ["🎬", "Watch «Maggie» as a film (demo)", "/sim/vorfuehrung"]]', 1)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps({"Watch «Maggie» as a film (demo)": DE["Watch «Maggie» as a film (demo)"]},
                                                                                      ensure_ascii=False) + ");</script></body>", 1)
VF_SIMJS = r"""<script>
// 639m: the card «Entwickler» of the Simulator page: «Watch as a film» (the start buttons come from the simulator itself)
(function vfLink() {
  try { Object.assign(I18N.de, /*VFLDE*/{}); } catch (e) {}
  setInterval(() => { document.querySelectorAll(".sc-card[data-dev] > .sc-bd").forEach(bd => {
    if (bd.querySelector(".vf-link")) return;
    const a = document.createElement("a"); a.className = "btn vf-link"; a.href = "/sim/vorfuehrung"; a.style.cssText = "display:block;margin:6px 0;text-align:left";
    a.textContent = "🎬 " + t("Watch «Maggie» as a film (demo)") + " ›"; bd.insertBefore(a, bd.firstChild); }); }, 1500);
})();
</script>"""
SIM_PAGE = SIM_PAGE.replace("</body>", VF_SIMJS.replace("/*VFLDE*/{}", json.dumps({"Watch «Maggie» as a film (demo)": DE["Watch «Maggie» as a film (demo)"]},
                                                                                    ensure_ascii=False)) + "</body>", 1)


def vf_page():
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in _VF_KEYS}, ensure_ascii=False) + ");"
    return render_page(VF_PAGE, "sim").replace("/*VFDE*/", js, 1)


_smalltv_routes_vf_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639m: /sim/vorfuehrung and /api/vorfuehrung (550 calls smalltv_routes once)
    _smalltv_routes_vf_base(app, reply, body)
    from flask import Response

    @app.route("/sim/vorfuehrung")
    def vf_page_():
        if not nacht_may(_nacht_role()):
            return Response(tr("Only the owner can do this."), 403)
        return Response(vf_page(), mimetype="text/html")

    @app.route("/api/vorfuehrung", methods=["GET", "POST"])
    def api_vorfuehrung():
        from flask import request
        own = nacht_may(_nacht_role())
        if request.method == "GET":
            return reply(vf_info()) if own else reply({"ok": False, "error": tr("Only the owner can do this.")}, 403)
        r = vf_do(body(), own)
        code = r.pop("code", None)
        return reply(r, code) if code else reply(r)


if GUI_OK:                                                # the window: the same row in the developer part (639c)
    _vf_tk_build_section_base = App._build_section

    def _vf_tk_build_section(self, sec, sbody, settings_parent=None):
        r = _vf_tk_build_section_base(self, sec, sbody, settings_parent)
        if sec == "Developer":
            ttk.Button(sbody, text="🎬 " + tr("Watch «Maggie» as a film (demo)") + " ›", command=lambda: self._open_page("/sim/vorfuehrung")).pack(fill="x", pady=(4, 0))
        return r

    # wraps: App._build_section (after 639d)
    App._build_section = _vf_tk_build_section


def vf_selftest():
    keep = CFG.get("sim_on")
    try:
        CFG["sim_on"] = False
        assert not vf_info()["ok"] and not vf_do({"do": "start"})["ok"]
        r = vf_do({"do": "start"}, owner=False)
        assert not r["ok"] and r.get("code") == 403, r
        assert vf_do({"do": "rm -rf"}).get("code") == 400
        CFG["sim_on"] = True
        _sc = globals()["sim_control"]; asked = []
        globals()["sim_control"] = lambda d_: (asked.append(d_), {"ok": True, "laeuft": True})[1]
        try:
            assert vf_do({"do": "start", "len": "ganz"})["ok"] and asked[-1] == {"action": "vorfuehrung", "do": "start", "len": "ganz"}
            assert vf_do({"do": "start", "len": "x"})["ok"] and asked[-1]["len"] == "kurz"
            assert vf_do({"do": "kapitel", "n": 9})["ok"] and asked[-1]["n"] == 5
            n = len(asked); assert vf_do({"do": "stop"}, owner=False).get("code") == 403 and len(asked) == n
        finally:
            globals()["sim_control"] = _sc
    finally:
        CFG["sim_on"] = keep
    html = vf_page()
    assert "/sim/view.jpg?bare=1" in html and "/api/vorfuehrung" in html and "Kurzfassung" in html and "<!--NAV-->" not in html
    assert "/sim/vorfuehrung" in SIM_PAGE and "/sim/vorfuehrung" in WEB_PAGE
    for L in ("fr", "it", "rm"):
        assert TRX[L].get("Watch «Maggie» as a film (demo)"), L
    return "Vorführung: page, owner only, commands to the simulator, translations, entries"


SELFTEST_EXTRA.append(("Vorführung «Maggie» (page /sim/vorfuehrung, owner only)", vf_selftest))
