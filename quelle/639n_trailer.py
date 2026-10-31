#@ MoveEye – Teil 639n: Trailer der Geschichten (Daniel 31.10.2026) – live im Browser: /sim/trailer?id=grossvater|maggie (Bild des Simulators wie /sim/vorfuehrung, startet den Trailer im Simulator), /api/trailer; Schnell-Karte «🛠 Entwickler» ganz oben im Reiter «Sim» (Trailer Grossvater · Trailer Maggie · Vorführung) und die zwei Trailer oben in Einstellungen → Entwickler; nur der Besitzer mit Entwickler-Bereich. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Der 3D-Simulator spielt den Trailer selbst (simulator3d/scripts/trailer.gd: Kamerafahrt im Bergtal, Musik, Texttafeln,
# Erzähler). Hier nur das Starten und Zuschauen:
#   * /sim/trailer?id=…: startet den Trailer (wenn nicht schon einer läuft) und zeigt das Bild des Simulators
#     (/sim/view.jpg?bare=1), unten eine Leiste: Beenden, Nochmals, Vollbild, Zurück. Den Ton hört man am Simulator-PC
#     (das Bild im Browser ist ohne Ton).
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
    <button type="button" class="sec" onclick="tlFull()" data-i18n="Full screen">Full screen</button>
    <a class="btn sec" href="/sim" data-mw-exit data-i18n="Back">Back</a>
  </div>
</div>
<script>
/*COMMON*/
/*TLDE*/
const ID = (new URLSearchParams(location.search).get("id") || "grossvater") === "maggie" ? "maggie" : "grossvater";
let S = {}, HIDE_T = 0, BUSY = 0, STARTED = 0;
(async () => { try { await initAppearance(); } catch (e) {} tlInfo(true); tlPic(); tlShow(); })();
function tlShow() { const b = document.getElementById("tl-bar"); b.classList.remove("off"); clearTimeout(HIDE_T);
  HIDE_T = setTimeout(() => { if (S.laeuft && !S.ende) b.classList.add("off"); }, 4000); }
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
  n.src = "/sim/view.jpg?bare=1&clean=1&q=72&w=" + w + "&t=" + Date.now();
}
async function tlInfo(first) {
  let j = null;
  try { j = await (await fetch("/api/trailer", {cache: "no-store"})).json(); } catch (e) {}
  if (j) tlPaint(j);
  if (first && j && j.ok !== false && !j.laeuft && !STARTED) { STARTED = 1; tlDo({do: "start", id: ID}); }   // the button of the card started us
  setTimeout(tlInfo, 1500);
}
function tlPaint(j) {
  S = j || {};
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
  if (d.do === "start") m.textContent = t("The valley is being prepared …");
  try { const r = await (await fetch("/api/trailer", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)})).json();
    if (r && r.ok === false && r.error) m.textContent = "⚠ " + r.error; else { if (d.do !== "start") m.textContent = ""; if (r && "laeuft" in r) tlPaint(r); } }
  catch (e) { m.textContent = "⚠ " + e; }
  BUSY = 0; tlShow(); setTimeout(() => { if (!m.textContent.startsWith("⚠")) m.textContent = ""; }, 5000);
}
</script></body></html>"""

_HX_TRL = {
    'Trailer Grossvater': ('Trailer Grossvater', 'Bande-annonce Grand-père', 'Trailer Nonno', 'Trailer Tat'),
    'Trailer Maggie': ('Trailer Maggie', 'Bande-annonce Maggie', 'Trailer Maggie', 'Trailer Maggie'),
    'Vorführung': ('Vorführung', 'Démonstration', 'Dimostrazione', 'Demonstraziun'),
    'Developer': ('Entwickler', 'Développeur', 'Sviluppatore', 'Sviluppader'),
    'End the trailer': ('Trailer beenden', 'Arrêter la bande-annonce', 'Termina il trailer', 'Terminar il trailer'),
    'Watch again': ('Nochmals ansehen', 'Revoir', 'Guarda di nuovo', 'Guardar anc ina giada'),
    'The end': ('Ende', 'Fin', 'Fine', 'Fin'),
    'Over': ('Vorbei', 'Terminé', 'Finito', 'Terminà'),
    'This simulator has no trailers yet – update it.': ('Dieser Simulator kennt die Trailer noch nicht – bitte aktualisieren.',
                                                        'Ce simulateur ne connaît pas encore les bandes-annonces – mets-le à jour.',
                                                        'Questo simulatore non conosce ancora i trailer – aggiornalo.',
                                                        'Quest simulatur na conuscha anc betg ils trailers – actualisescha el.'),
    'The simulator is busy: {w}': ('Der Simulator ist beschäftigt: {w}', 'Le simulateur est occupé : {w}', 'Il simulatore è occupato: {w}',
                                   'Il simulatur è occupà: {w}'),
}
for _k, _v in _HX_TRL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
_TRL_KEYS = list(_HX_TRL) + ["Full screen", "Back", "The valley is being prepared …", "The 3D simulator is not connected."]
_TRL_DE_JS = json.dumps({k: DE.get(k, k) for k in ("Trailer Grossvater", "Trailer Maggie", "Vorführung", "Developer")}, ensure_ascii=False)

# Settings → Developer (web 530 devExtras): the two trailers on top of the list (the window 639c: see below)
WEB_PAGE = WEB_PAGE.replace('[["🧪", "Test bench and test run", "/sim#c-test"]',
                            '[["🎬", "Trailer Grossvater", "/sim/trailer?id=grossvater"], ["🎬", "Trailer Maggie", "/sim/trailer?id=maggie"], '
                            '["🧪", "Test bench and test run", "/sim#c-test"]', 1)
WEB_PAGE = WEB_PAGE.replace("</body>", "<script>Object.assign(I18N.de, " + _TRL_DE_JS + ");</script></body>", 1)

# the tab «Sim»: on top the card «🛠 Entwickler» (only the owner with the developer area: /api/ui_simple dev + /api/trailer not 403)
TRL_SIM_CARD = """<details class="sc fold wide" id="c-devquick" hidden open>
    <summary><h2><span>🛠</span><span data-i18n="Developer">Developer</span></h2></summary>
    <div class="fb">
      <a class="btn sec" href="/sim/trailer?id=grossvater" style="display:block;margin:4px 0;text-align:left">🎬 <span data-i18n="Trailer Grossvater">Trailer Grossvater</span> ›</a>
      <a class="btn sec" href="/sim/trailer?id=maggie" style="display:block;margin:4px 0;text-align:left">🎬 <span data-i18n="Trailer Maggie">Trailer Maggie</span> ›</a>
      <a class="btn sec" href="/sim/vorfuehrung" style="display:block;margin:4px 0;text-align:left">🎬 <span data-i18n="Vorführung">Vorführung</span> ›</a>
    </div>
  </details>
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
    return render_page(TRL_PAGE, "sim").replace("/*TLDE*/", js, 1)


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
            return reply(trl_info()) if own else reply({"ok": False, "error": tr("Only the owner can do this.")}, 403)
        r = trl_do(body(), own)
        code = r.pop("code", None)
        return reply(r, code) if code else reply(r)


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
    assert "/sim/view.jpg?bare=1" in html and "/api/trailer" in html and "<!--NAV-->" not in html
    assert 'id="c-devquick"' in SIM_PAGE and "/sim/trailer?id=maggie" in SIM_PAGE and "/sim/vorfuehrung" in SIM_PAGE
    assert SIM_PAGE.index('id="c-devquick"') < SIM_PAGE.index('id="c-conn"')
    assert "/sim/trailer?id=grossvater" in WEB_PAGE
    for L in ("fr", "it", "rm"):
        assert TRX[L].get("End the trailer"), L
    return "Trailer: page, owner only, commands to the simulator, card on top of «Sim», entries"


SELFTEST_EXTRA.append(("Trailer der Geschichten (page /sim/trailer, owner only)", trl_selftest))
