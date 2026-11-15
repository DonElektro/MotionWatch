#@ MoveEye – Teil 639zzzi: «★ Favoriten» (Besitzer 2026-11) – ein eigener Reiter mit Kacheln: Seiten, Aktionen, Schalter und Spiele, pro Benutzer gemerkt. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Reiter «★» (schmal, nur das Symbol, vor «Live») -> /fav = die Hauptseite mit data-tab="fav" (wie Schutz / Einstellungen): so
# laufen die Kacheln über DIESELBEN Funktionen wie auf Live / Schutz (QS der Schnellschalter, protectLevel …) – die Rechte prüft der
# Server wie bisher (/api/set, /api/protect …). «Aus» mit PIN fragt die PIN.
# Merken: CFG ui_fav = {Benutzer: [{"k": Schlüssel, "l": Name, "i": Symbol}]} über /api/fav (wie «Meine Ansicht» 639r: jeder
# Benutzer, auch «Nur ansehen»), im Browser zusätzlich localStorage (mw-fav) als Ersatz ohne Verbindung.
# Schlüssel: qs:<id> (Schnellschalter von Live), pr:off|watch|full|night (Schutz), row:<seite>:<zeile> (Zeilen im Mehr-Stil 639zzzg),
# page:<adresse> (Seiten unter «Mehr»), game:<id> (Spielecke).
# Hinzufügen: ☆ am Ende jeder Zeile (Einstellungen, Schutz, Kameras, Sim, Verlauf) und auf der ★-Seite «+ Hinzufügen» (alles in
# einer Liste, mit Suche). Bearbeiten: ✕ entfernt, ziehen ordnet.
# ----------------------------------------------------------------------------
_HX_FAV = {
    "Favourites": ("Favoriten", "Favoris", "Preferiti", "Favurits"),
    "Edit": ("Bearbeiten", "Modifier", "Modifica", "Modifitgar"), "Done": ("Fertig", "Terminé", "Fatto", "Finì"),
    "+ Add": ("+ Hinzufügen", "+ Ajouter", "+ Aggiungi", "+ Agiuntar"),
    "No favourites yet": ("Noch keine Favoriten", "Pas encore de favoris", "Ancora nessun preferito", "Anc nagins favurits"),
    "fav-empty": ("Tippe auf ☆ am Ende einer Zeile – oder hier auf «+ Hinzufügen»: Seiten, Schalter, Aktionen und Spiele, mit einem Tipp erreichbar.",
                  "Touche ☆ au bout d’une ligne – ou ici «+ Ajouter» : pages, interrupteurs, actions et jeux, à portée d’un geste.",
                  "Tocca ☆ alla fine di una riga – o qui «+ Aggiungi»: pagine, interruttori, azioni e giochi, a portata di un tocco.",
                  "Tutga ☆ a la fin d’ina lingia – u qua «+ Agiuntar»: paginas, interruptur, acziuns e gieus, cun in tip."),
    "Drag to sort, ✕ removes": ("Ziehen zum Ordnen, ✕ entfernt", "Glisser pour trier, ✕ supprime", "Trascina per ordinare, ✕ rimuove", "Trair per ordinar, ✕ allontanescha"),
    "Add to favourites": ("Zu den Favoriten", "Ajouter aux favoris", "Aggiungi ai preferiti", "Agiuntar als favurits"),
    "Remove from favourites": ("Aus den Favoriten", "Retirer des favoris", "Rimuovi dai preferiti", "Allontanar dals favurits"),
    "Added to the favourites": ("Zu den Favoriten hinzugefügt", "Ajouté aux favoris", "Aggiunto ai preferiti", "Agiuntà als favurits"),
    "Quick switches": ("Schnellschalter", "Interrupteurs rapides", "Interruttori rapidi", "Interruptur svelts"),
    "Pages": ("Seiten", "Pages", "Pagine", "Paginas"), "Games (favourites)": ("Spiele", "Jeux", "Giochi", "Gieus"),
    "PIN for switching off": ("PIN zum Ausschalten", "PIN pour désactiver", "PIN per spegnere", "PIN per deactivar"),
    "Search …": ("Suchen …", "Chercher …", "Cerca …", "Tschertgar …"),
    "not here": ("nicht da", "absent", "non presente", "betg qua"),
    "Quiz with buzzer": ("Quiz mit Buzzer", "Quiz avec buzzer", "Quiz con pulsante", "Quiz cun buzzer"),
    "Werewolf": ("Werwolf", "Loup-garou", "Lupo mannaro", "Luf"), "Pictionary": ("Montagsmaler", "Pictionary", "Pictionary", "Pictionary"),
    "Connect four": ("Vier gewinnt", "Puissance 4", "Forza quattro", "Quatter en lingia"),
    "Scattergories": ("Stadt-Land-Fluss", "Petit bac", "Nomi, cose, città", "Citad-pajais-flum"),
    "Estimation": ("Schätzfrage", "Question d’estimation", "Domanda di stima", "Dumonda da stimar"),
    "Explain the word": ("Begriffe erklären", "Expliquer le mot", "Spiega la parola", "Declerar il pled"),
    "Who am I?": ("Wer bin ich?", "Qui suis-je ?", "Chi sono?", "Tgi sun jau?"),
    "Reaction": ("Reaktion", "Réaction", "Reazione", "Reacziun"), "Battleships": ("Schiffe versenken", "Bataille navale", "Battaglia navale", "Bastiments"),
    "Removed from the favourites": ("Aus den Favoriten entfernt", "Retiré des favoris", "Rimosso dai preferiti", "Allontanà dals favurits"),
    "Game chosen": ("Spiel gewählt", "Jeu choisi", "Gioco scelto", "Gieu tschernì"),
    "fav-tk-empty": ("Noch keine Favoriten. Im Browser auf ☆ am Ende einer Zeile tippen oder unter ★ «+ Hinzufügen» – sie erscheinen dann auch hier.",
                     "Pas encore de favoris. Dans le navigateur, touche ☆ au bout d’une ligne ou ★ «+ Ajouter» – ils apparaissent ensuite ici aussi.",
                     "Ancora nessun preferito. Nel browser tocca ☆ alla fine di una riga o ★ «+ Aggiungi» – poi appaiono anche qui.",
                     "Anc nagins favurits. En il navigatur tutga ☆ a la fin d’ina lingia u ★ «+ Agiuntar» – lura cumparan els er qua."),
    "Long press: favourite": ("Lange drücken: Favorit", "Appui long : favori", "Pressione lunga: preferito", "Smatgar ditg: favurit"),
}
for _k, _v in _HX_FAV.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

FAV_MAX = 60
_FAV_KEY = re.compile(r"^(qs|pr|row|page|game):[\w:#./\- ]{1,90}$")
VIEW_GET = VIEW_GET + ("/api/fav", "/fav")                    # every user has his own favourites (also «Nur ansehen»)
VIEW_POST.add("/api/fav")
LOCK_KEEP.update({"ui_fav"})
CFG.setdefault("ui_fav", {})

# the pages and games of the catalogue: (key, icon, English title, address)
FAV_PAGES = [("page:/", "👁", "Live", "/"), ("page:/protect", "🛡", "Protection", "/protect"), ("page:/recordings", "🕘", "History", "/recordings"),
             ("page:/settings", "⚙", "Settings", "/settings"), ("page:/cams", "📷", "Cameras", "/cams"), ("page:/sim", "🧪", "Simulator", "/sim"),
             ("page:/zones", "🗺", "Zones", "/zones"), ("page:/tausch", "📁", "File " + "ex" "change", "/tausch"), ("page:/karte", "🗺", "Map", "/karte"),
             ("page:/almanach", "🌦", "Almanac", "/almanach"), ("page:/morse", "📡", "Morse mode", "/morse"), ("page:/help", "📖", "Manual", "/help"),
             ("page:/quick", "📄", "Quick guide (1 page)", "/quick"), ("page:/qr", "▦", "QR codes", "/qr"), ("page:/tools", "🧰", "Tools", "/tools"),
             ("page:/kino", "🎬", "Cinema", "/kino"), ("page:/more", "▦", "More", "/more")]
FAV_GAMES = [("game:quiz", "🔔", "Quiz with buzzer"), ("game:wolf", "🐺", "Werewolf"), ("game:draw", "🎨", "Pictionary"), ("game:c4", "🔴", "Connect four"),
             ("game:slf", "🏙", "Scattergories"), ("game:guess", "📏", "Estimation"), ("game:taboo", "🗣", "Explain the word"), ("game:whoami", "🤔", "Who am I?"),
             ("game:react", "⚡", "Reaction"), ("game:ships", "🚢", "Battleships")]


def fav_user(g_=None):
    return ansicht_user(g_)                                    # 639r: the owner = «admin», else the logged-in name


def fav_clean(items):
    out, seen = [], set()
    for x in items if isinstance(items, list) else []:
        if not isinstance(x, dict):
            continue
        k = str(x.get("k") or "")[:100]
        if not _FAV_KEY.match(k) or k in seen:
            continue
        seen.add(k)
        out.append({"k": k, "l": str(x.get("l") or "")[:60], "i": str(x.get("i") or "")[:8]})
        if len(out) >= FAV_MAX:
            break
    return out


def fav_get(user):
    return fav_clean((CFG.get("ui_fav") or {}).get(str(user)[:60]) or [])


def fav_set(user, items):
    allf = dict(CFG.get("ui_fav") or {})
    allf[str(user)[:60]] = fav_clean(items)
    CFG["ui_fav"] = allf
    save_settings()
    return allf[str(user)[:60]]


def fav_catalog():
    """the pages and games with their names in the five languages (the rest comes from the page itself)"""
    langs = ("de", "en", "fr", "it", "rm")
    more_de = dict(globals().get("MORE_DE") or {}, **(globals().get("MORE_GROUPS_DE") or {}))      # the page «Mehr» has its own German (525)
    nm = lambda e: {L: (EN_SHOW.get(e, e) if L == "en" else (more_de.get(e) or tr(e, L)) if L == "de" else tr(e, L)) for L in langs}
    return {"pages": [{"k": k, "i": i, "n": nm(e), "h": h} for k, i, e, h in FAV_PAGES],
            "games": [{"k": k, "i": i, "n": nm(e), "h": "/party?game=" + k.split(":", 1)[1]} for k, i, e in FAV_GAMES],
            "tx": {L: {k: (EN_SHOW.get(k, k) if L == "en" else tr(k, L)) for k in _HX_FAV} for L in langs},
            "ic": dict(globals().get("TK_SUB_ICONS") or {})}         # the symbols of the topics (570) when the page has not built them


_smalltv_routes_fav = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzi: /fav (the tab), /api/fav (GET / POST)
    _smalltv_routes_fav(app, reply, body)
    from flask import Response, request, g as g_

    @app.route("/fav")
    def fav_page():
        return Response(main_tab_page("fav"), mimetype="text/html")

    @app.route("/api/fav/game", methods=["POST"])
    def api_fav_game():                                        # /party?game=<id>: the tile of a game - open the games, choose it
        if getattr(g_, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        err = fav_game(str(body().get("game") or ""))
        return reply({"ok": not err, "error": err or None, "game": PARTY.get("game")}, 200 if not err else 400)

    @app.route("/api/fav", methods=["GET", "POST"])
    def api_fav():
        user = fav_user(g_)
        if request.method == "POST":
            d = body()
            return reply({"ok": True, "items": fav_set(user, d.get("items")), "user": user})
        return reply({"ok": True, "items": fav_get(user), "user": user})


def fav_game(gm):
    """choose a game of the game corner like its host does (party_act) - the games are opened first when they are closed"""
    if gm not in [k.split(":", 1)[1] for k, _i, _e in FAV_GAMES]:
        return "unknown game"
    if not party_on():
        games_all_open(6.0, "favourite")
    host = PARTY.get("host") if PARTY.get("host") in PARTY["players"] else ""
    tmp = ""
    if not host:                                               # nobody there yet: a short helper as host, gone right after
        tmp = "fav-" + secrets.token_hex(4)
        PARTY["players"][tmp] = {"name": "★", "score": 0, "t": time.time()}
        PARTY["host"] = host = tmp
    try:
        err = party_act(host, {"a": "game", "game": gm})
    finally:
        if tmp:
            PARTY["players"].pop(tmp, None)
            if PARTY.get("host") == tmp:
                PARTY["host"] = ""
            party_bump()
    return err or ""


# ---- the tab: narrow, only the star (seven tabs fit at 390 px in all five languages) -------------------------------------------
if not any(x[0] == "fav" for x in NAV_ITEMS):
    NAV_ITEMS.insert(0, ("fav", "/fav", "Favourites", "Favourites"))
FAV_STAR_SVG = ('<svg class="ni" aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3.2l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17.2l-5.4 2.9 1-6.1-4.4-4.3 '
                '6.1-.9z"/></svg>')
_nav_html_639zzzi = nav_html


# wraps: nav_html
def nav_html(active):                                          # + 639zzzi: the star tab
    h_ = _nav_html_639zzzi(active)
    return re.sub(r'<a href="/fav"( class="on")?>', lambda m_: '<a href="/fav" class="fav%s" title="%s" aria-label="%s">%s' % (
        " on" if m_.group(1) else "", tr("Favourites"), tr("Favourites"), FAV_STAR_SVG), h_, count=1)


FAV_CSS = r"""<style id="fav-css">
/* 639zzzi: the star tab - narrow, only the symbol */
header>nav.nav>a.fav{flex:0 0 auto!important;min-width:44px;padding-left:10px!important;padding-right:10px!important;justify-content:center}
header>nav.nav>a.fav .nl,header>nav.nav>a.fav .ns{display:none!important}
header>nav.nav>a.fav .ni{width:22px;height:22px}
header>nav.nav>a.fav.on .ni{fill:currentColor}
@media(max-width:760px){header>nav.nav>a.fav{flex:0 0 40px!important;min-width:40px;padding:5px 0 4px!important}}
/* the ★ page */
body[data-tab="fav"] main>*:not(#fav){display:none!important}
body[data-tab="fav"] main{display:block!important;max-width:980px}
#fav{padding:4px 0 24px}
#fav .fv-h{display:flex;align-items:center;gap:8px;margin:4px 2px 12px}#fav .fv-h h2{margin:0;font-size:20px;flex:1}
#fav .fv-h h2{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
#fav .fv-h button{min-height:44px;min-width:44px;padding:0 12px;display:inline-flex;align-items:center;gap:6px;flex:none}
#fav .fv-h .fv-ic{font-size:18px}#fav .fv-h button.on{background:var(--acc,#3b8cff);color:#fff}
@media(max-width:559px){#fav .fv-h .fv-w{display:none}}
#fv-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
@media(min-width:560px){#fv-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}@media(min-width:900px){#fv-grid{grid-template-columns:repeat(6,minmax(0,1fr))}}
.fv-t{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;min-height:104px;padding:12px 6px;border-radius:16px;
  border:1px solid var(--line);background:var(--panel);color:var(--txt);text-decoration:none;font:inherit;text-align:center;cursor:pointer;touch-action:manipulation;user-select:none}
.fv-t .fi{font-size:34px;line-height:1}.fv-t .fi svg{width:34px;height:34px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.fv-t .fn{font-size:13px;font-weight:650;line-height:1.2;overflow-wrap:anywhere;max-width:100%}
.fv-t .fs{font-size:11.5px;color:var(--mut)}
.fv-t.on{border-color:var(--grn);background:rgba(63,207,107,.13)}.fv-t.on .fs{color:var(--grn)}
.fv-t.na{opacity:.45}
.fv-t .fx{display:none;position:absolute;top:-8px;right:-8px;width:30px;height:30px;border-radius:50%;border:0;background:var(--red,#ff4d4d);color:#fff;font-size:16px;line-height:30px;padding:0;cursor:pointer}
#fav.edit .fv-t .fx{display:block}#fav.edit .fv-t{cursor:grab;border-style:dashed;touch-action:none}#fav.edit .fv-t.drag{opacity:.4}
#fav .fv-note{color:var(--mut);font-size:13px;margin:10px 2px}
.fv-empty{text-align:center;padding:40px 16px;border:1px dashed var(--line);border-radius:18px;color:var(--mut)}
.fv-empty .big{font-size:56px;line-height:1;color:var(--acc2,#5aa2ff)}.fv-empty b{display:block;color:var(--txt);font-size:17px;margin:10px 0 6px}
.fv-empty p{margin:0 auto 16px;max-width:420px;line-height:1.45}.fv-empty button{min-height:44px;padding:0 18px}
#fv-pick{margin-top:16px}#fv-pick[hidden]{display:none}#fv-pick input{width:100%;box-sizing:border-box;padding:11px 14px;border-radius:12px;font-size:15px;margin-bottom:6px}
#fv-pick .mgh{font-size:15px;font-weight:700;margin:14px 4px 6px}
#fv-pick .pl{border:1px solid var(--line);border-radius:14px;background:var(--panel);overflow:hidden}
#fv-pick .pi{display:flex;align-items:center;gap:10px;min-height:48px;padding:4px 6px 4px 12px}#fv-pick .pi+.pi{border-top:1px solid var(--line)}
#fv-pick .pi i{font-style:normal;font-size:20px;width:26px;text-align:center}#fv-pick .pi span{flex:1;min-width:0}
.fv-star{flex:none;min-width:44px;min-height:44px;border:0;background:none;color:var(--mut);font-size:20px;cursor:pointer;padding:0}
.fv-star.is{color:var(--yel,#f5c542)}
/* the ☆ at the end of every row (Mehr-Stil) */
.ms-list .mi .fv-star{min-width:36px;min-height:40px;margin-right:-6px;font-size:18px;opacity:.55}.ms-list .mi .fv-star.is{opacity:1}
#fv-pin{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;z-index:200}
#fv-pin>div{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px;width:min(320px,90vw)}
#fv-pin input{width:100%;box-sizing:border-box;padding:11px;font-size:18px;border-radius:10px;margin:10px 0}#fv-pin .row{display:flex;gap:8px}
html.mwrm .fv-t{transition:none}
</style>"""

FAV_PARTY_JS = r"""<script>
(async function () {                                       // 639zzzi: the tile of a game - /party?game=<id> chooses it
  const q = new URLSearchParams(location.search), gm = q.get("game"); if (!gm) return;
  try { const r = await fetch("/api/fav/game", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({game: gm})});
    const j = await r.json(), L = (typeof LANG !== "undefined" && LANG) || "de", tx = ((window.FAV_CAT || {}).tx || {})[L] || {};
    if (j.ok && typeof toast === "function") toast("🎮 " + (tx["Game chosen"] || "✓"));
    if (typeof partyLoad === "function") partyLoad(); } catch (e) {}
  try { history.replaceState(null, "", location.pathname); } catch (e) {}
})();
</script>"""

FAV_JS = r"""<script>
(function () {                                             // 639zzzi: ★ Favoriten
  if (window.favInit) return; window.favInit = 1;
  const CAT = window.FAV_CAT || {pages: [], games: [], tx: {}}, $ = s => document.querySelector(s);
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) { return "de"; } };
  const tr = k => ((CAT.tx[L()] || {})[k]) || ((CAT.tx.en || {})[k]) || k;
  const tt = k => (typeof t === "function" ? t(k) : k);
  const E = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const toast_ = m => { try { if (typeof toast === "function") toast(m); } catch (e) {} };
  const postj = async (u, d) => { try { const r = await fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)}); return await r.json(); } catch (e) { return {ok: false}; } };
  // ---- the list: server per user, the browser as a fallback --------------------------------------------------------------
  let FAV = []; try { FAV = JSON.parse(localStorage.getItem("mw-fav") || "[]"); } catch (e) {}
  const has = k => FAV.some(x => x.k === k);
  async function load() { try { const j = await (await fetch("/api/fav", {cache: "no-store"})).json(); if (j && j.ok) { FAV = j.items || []; keep(); } } catch (e) {} paintAll(); }
  function keep() { try { localStorage.setItem("mw-fav", JSON.stringify(FAV)); } catch (e) {} }
  async function save() { keep(); const r = await postj("/api/fav", {items: FAV}); if (r && r.ok && r.items) { FAV = r.items; keep(); } paintAll(); }
  function toggle(it) { if (has(it.k)) FAV = FAV.filter(x => x.k !== it.k); else { FAV.push({k: it.k, l: it.l || "", i: it.i || ""}); toast_("★ " + tr("Added to the favourites")); } save(); }
  window.mwFav = {toggle, has, list: () => FAV.slice()};
  // ---- what can be a favourite: the quick switches of Live, protection, the rows (Mehr-Stil), the pages, the games ------------
  const J = () => (typeof MAINJ !== "undefined" && MAINJ) || {};
  function catalog() {
    const out = [], j = J(), c = j.cfg || {}, s = j.state || window.__lastState || {};
    const P = s.protect || {};
    out.push({g: "Protection", items: [
      {k: "pr:off", i: "⚪", l: tt("Off"), on: () => (((window.__lastState || {}).protect || {}).level === "off"), run: () => prLevel("off")},
      {k: "pr:watch", i: "🟡", l: tt("Watchful"), on: () => (((window.__lastState || {}).protect || {}).level === "watch"), run: () => prLevel("watch")},
      {k: "pr:full", i: "🛡", l: tt("Full protection"), on: () => (((window.__lastState || {}).protect || {}).level === "full"), run: () => prLevel("full")},
      {k: "pr:night", i: "🌙", l: tt("🌙 Guard tonight").replace(/^🌙\s*/, ""), run: () => (typeof nightGuard === "function" ? nightGuard() : null)}]});
    const act = q => q.flash || /^\(\)\s*=>\s*false$/.test(String(q.on || ""));      // Photo, Cinema …: an action, no on / off
    if (typeof qsList === "function") out.push({g: "Quick switches", items: qsList(j).filter(q => !q.talk).map(q => ({k: "qs:" + q.id, i: q.ic, l: q.raw ? q.lb : tt(q.lb),
      on: act(q) ? null : () => { const jj = J(); try { return !!q.on(jj.cfg || {}, jj.state || {}); } catch (e) { return false; } },
      ok: () => { const jj = J(); try { return q.ok ? !!q.ok(jj.cfg || {}, jj.state || {}) : true; } catch (e) { return true; } },
      run: async () => { const jj = J(); const r = await q.go(jj.cfg || {}, jj.state || {}); if (r && r.ok === false) toast_("⚠ " + (r.error || "error"));
        else if (q.flash) toast_("📷 " + tt("Photo saved")); if (typeof refresh === "function") refresh(); }}))});
    const C = window.MS_CONF || {}, PG = {settings: "/settings", protect: "/protect", cams: "/cams", sim: "/sim", history: "/recordings"};
    Object.entries(PG).forEach(([pg, path]) => (C[pg] || []).forEach(([gk, items]) => {
      const rows = items.map(([id, dk, sk, ic, ti, href]) => {
        const el = id[0] === "#" || id[0] === "@" || id[0] === "~" || id[0] === "?" ? null : document.querySelector('[data-view="' + id + '"]');
        const sm = el && el.querySelector(":scope > summary"); let l = ti ? (window.MS_TX && (MS_TX[L()] || {})[ti]) || tt(ti) : "";
        if (!l && id.startsWith("sec:")) l = tt(id.slice(4));           // the topic name (the page may not have built it here)
        if (!l && sm) { const cl = sm.cloneNode(true); cl.querySelectorAll(".mst, small, .gi").forEach(n => n.remove()); l = (cl.querySelector(".sn") || cl).textContent.trim(); }
        const m = sm && /(\p{Extended_Pictographic}️?)/u.exec(sm.textContent); const k = "row:" + pg + ":" + id;
        const saved = FAV.find(x => x.k === k);
        const sv = !ic && !m && sm && sm.querySelector(".gi svg, .ie svg, svg");                    // the line symbol of the topic (530)
        const tk = id.startsWith("sec:") && (CAT.ic || {})[id.slice(4)];
        return {k, i: ic || (m ? m[1] : (saved && saved.i) || tk || "•"), svg: sv ? sv.outerHTML : "", l: l || (saved && saved.l) || "", h: href || (path + "#s=" + encodeURIComponent(id))}; }).filter(x => x.l);
      if (rows.length) out.push({g: (window.MS_TX && (MS_TX[L()] || {})[gk]) || gk, raw: true, items: rows}); }));
    out.push({g: "Pages", items: CAT.pages.map(p => ({k: p.k, i: p.i, l: p.n[L()] || p.n.en, h: p.h}))});
    out.push({g: "Games (favourites)", items: CAT.games.map(p => ({k: p.k, i: p.i, l: p.n[L()] || p.n.en, h: p.h}))});
    return out;
  }
  function find(k) { for (const g of catalog()) for (const x of g.items) if (x.k === k) return x; return null; }
  // ---- protection: the same calls as the tab Schutz; «Off» with a PIN asks for it -------------------------------------------
  async function prLevel(k) {
    const P = (window.__lastState || {}).protect || {};
    if (k === "off" && P.pin) return pinAsk();
    if (typeof protectLevel === "function") return protectLevel(k);
    const r = await postj("/api/protect", {action: "level", level: k, lang: L()}); if (!r.ok) toast_("⚠ " + (r.error || "error"));
  }
  function pinAsk() {
    const o = E("div"); o.id = "fv-pin"; const b = E("div"); b.append(E("b", "", "🔐 " + tr("PIN for switching off")));
    const i = E("input"); i.type = "password"; i.inputMode = "numeric"; i.autocomplete = "off"; const r = E("div", "row");
    const ok = E("button", "", tt("Switch off")); const no = E("button", "sec", "✕"); r.append(ok, no); b.append(i, r); o.appendChild(b); document.body.appendChild(o); i.focus();
    no.onclick = () => o.remove();
    ok.onclick = async () => { const x = await postj("/api/protect", {action: "level", level: "off", pin: i.value, lang: L()});
      if (x.ok) { o.remove(); toast_("✓ " + tt("Protection off")); } else { i.value = ""; toast_("⚠ " + (x.error || "error")); } };
    i.onkeydown = e => { if (e.key === "Enter") ok.click(); };
  }
  // ---- the ★ page --------------------------------------------------------------------------------------------------------
  let box = null, grid = null, pick = null, edit = false, sig = "";
  function buildPage() {
    const main = $("main"); if (!main || $("#fav")) return;
    box = E("section"); box.id = "fav"; main.prepend(box);
    const h = E("div", "fv-h"); const h2 = E("h2", "", "★ " + tr("Favourites")); h2.id = "fv-title";
    const add = E("button", "sec"); add.type = "button"; add.id = "fv-add"; add.append(E("span", "fv-ic", "＋"), E("span", "fv-w", tr("+ Add").replace(/^\+\s*/, "")));
    add.title = tr("+ Add"); add.setAttribute("aria-label", add.title);
    const eb = E("button", "sec"); eb.type = "button"; eb.id = "fv-edit"; eb.append(E("span", "fv-ic", "✎"), E("span", "fv-w", tr("Edit")));
    eb.title = tr("Edit"); eb.setAttribute("aria-label", eb.title);
    h.append(h2, add, eb); box.appendChild(h);
    grid = E("div"); grid.id = "fv-grid"; box.appendChild(grid);
    const note = E("div", "fv-note", tr("Drag to sort, ✕ removes")); note.id = "fv-note"; note.hidden = true; box.appendChild(note);
    pick = E("div"); pick.id = "fv-pick"; pick.hidden = true; box.appendChild(pick);
    eb.onclick = () => { edit = !edit; box.classList.toggle("edit", edit); eb.firstChild.textContent = edit ? "✓" : "✎"; eb.lastChild.textContent = edit ? tr("Done") : tr("Edit"); eb.classList.toggle("on", edit); note.hidden = !edit; if (!edit) pick.hidden = true; sig = ""; paintPage(); };
    add.onclick = () => { pick.hidden = !pick.hidden; if (!pick.hidden) { paintPick(""); pick.scrollIntoView({behavior: "smooth", block: "start"}); } };
  }
  function paintPage() {
    if (!grid) return;
    const s = JSON.stringify([FAV, edit, L()]);
    if (s !== sig) { sig = s; grid.textContent = ""; grid.hidden = !FAV.length;
      const old = $("#fv-empty"); if (old) old.remove();
      if (!FAV.length) { const e = E("div", "fv-empty"); e.id = "fv-empty"; e.append(E("div", "big", "☆"), E("b", "", tr("No favourites yet")), E("p", "", tr("fav-empty")));
        const b = E("button", "", tr("+ Add")); b.type = "button"; b.onclick = () => $("#fv-add").click(); e.appendChild(b); grid.after(e); }
      FAV.forEach((f, n) => { const x = find(f.k) || {k: f.k, i: f.i || "•", l: f.l || f.k, h: null};
        const tile = E(x.h ? "a" : "button", "fv-t"); if (x.h) tile.href = x.h; else tile.type = "button"; tile.dataset.k = f.k;
        const fi = E("span", "fi", x.svg ? "" : x.i); if (x.svg) fi.innerHTML = x.svg;            // (a symbol of this page, not stored text)
        tile.append(fi, E("span", "fn", x.l), E("span", "fs", ""));
        const del = E("button", "fx", "✕"); del.type = "button"; del.title = tr("Remove from favourites"); del.setAttribute("aria-label", del.title);
        del.onclick = e => { e.preventDefault(); e.stopPropagation(); FAV = FAV.filter(y => y.k !== f.k); save(); };
        tile.appendChild(del);
        tile.addEventListener("click", async e => { if (edit) { e.preventDefault(); return; } if (x.run) { e.preventDefault(); tile.disabled = true; try { await x.run(); } finally { tile.disabled = false; } } });
        drag(tile, n); grid.appendChild(tile); }); }
    // the live state of the switches
    grid.querySelectorAll(".fv-t").forEach(tile => { const x = find(tile.dataset.k); if (!x) return;
      const on = x.on ? !!x.on() : null, ok = x.ok ? x.ok() : true;
      tile.classList.toggle("on", on === true); tile.classList.toggle("na", !ok);
      const st = tile.querySelector(".fs"), tx = !ok ? tr("not here") : on === null ? "" : (on ? tt("on") : tt("off")); if (st.textContent !== tx) st.textContent = tx; });
  }
  // drag to sort (pointer: finger and mouse), only in the edit mode
  function drag(tile, n) {
    tile.addEventListener("pointerdown", e => {
      if (!edit || e.target.classList.contains("fx")) return; e.preventDefault(); tile.classList.add("drag");
      // the OTHER tile moves (moving the held one would lose the pointer): the held tile travels through the grid
      const move = ev => { const over = document.elementFromPoint(ev.clientX, ev.clientY); const t2 = over && over.closest(".fv-t");
        if (t2 && t2 !== tile && t2.parentNode === grid) { const a = [...grid.children]; if (a.indexOf(t2) > a.indexOf(tile)) tile.before(t2); else tile.after(t2); } };
      const up = () => { tile.classList.remove("drag"); document.removeEventListener("pointermove", move, true); document.removeEventListener("pointerup", up, true);
        document.removeEventListener("pointercancel", up, true);
        const order = [...grid.children].map(c => c.dataset.k); FAV.sort((a, b) => order.indexOf(a.k) - order.indexOf(b.k)); save(); };
      document.addEventListener("pointermove", move, true); document.addEventListener("pointerup", up, true); document.addEventListener("pointercancel", up, true);
    });
  }
  function paintPick(q) {
    pick.textContent = ""; const inp = E("input"); inp.type = "search"; inp.placeholder = tr("Search …"); inp.value = q; pick.appendChild(inp);
    inp.oninput = () => { const v = inp.value; paintPick(v); const i2 = pick.querySelector("input"); i2.focus(); i2.setSelectionRange(v.length, v.length); };
    const w = q.trim().toLowerCase();
    catalog().forEach(g => { const items = g.items.filter(x => !w || (x.l + " " + x.k).toLowerCase().includes(w)); if (!items.length) return;
      pick.appendChild(E("div", "mgh", g.raw ? g.g : tr(g.g) === g.g ? tt(g.g) : tr(g.g))); const l = E("div", "pl");
      items.forEach(x => { const r = E("div", "pi"); r.dataset.k = x.k; r.append(E("i", "", x.i), E("span", "", x.l)); const b = starBtn(x); r.appendChild(b); l.appendChild(r); });
      pick.appendChild(l); });
  }
  function starBtn(x) {
    const b = E("button", "fv-star"); b.type = "button"; const paint = () => { const on = has(x.k); b.textContent = on ? "★" : "☆"; b.classList.toggle("is", on);
      b.title = on ? tr("Remove from favourites") : tr("Add to favourites"); b.setAttribute("aria-label", b.title); b.setAttribute("aria-pressed", on ? "true" : "false"); };
    paint(); b.onclick = e => { e.preventDefault(); e.stopPropagation(); toggle({k: x.k, l: x.l, i: x.i}); paint(); }; b._paint = paint; return b;
  }
  // ---- the ☆ at the end of every row of the Mehr-Stil (639zzzg) -----------------------------------------------------------
  const PAGEKEY = () => window.MS_PAGE || "";
  function rowStars() {
    if (!PAGEKEY() || PAGEKEY() === "live") return;             // Live: only the long press on the quick tiles
    document.querySelectorAll("#ms-list .mi").forEach(r => {
      let b = r.querySelector(":scope > .fv-star");
      if (!b) { const k = "row:" + PAGEKEY() + ":" + r.dataset.ms;
        b = starBtn({k, get l() { return (r.querySelector("b") || {}).textContent || ""; }, get i() { return (r.querySelector("i") || {}).textContent || ""; }});
        const ar = r.querySelector(".ar"); if (ar) ar.before(b); else r.appendChild(b); }
      else if (b._paint) b._paint(); });
  }
  // ---- Live: a long press on a quick tile (Photo, Record …) adds it / takes it away - the only change on Live ----------------
  let lp = null;
  document.addEventListener("pointerdown", e => {
    const b = e.target.closest && e.target.closest("#qsw > button[id^='qs-']"); if (!b || b.dataset.talk) return;
    const x0 = e.clientX, y0 = e.clientY;
    lp = {b, x0, y0, t: setTimeout(() => { const id = b.id.slice(3), k = "qs:" + id; b.dataset.lp = "1";
      const was = has(k); toggle({k, l: (b.querySelector("small") || {}).textContent || id, i: (b.querySelector("span") || {}).textContent || ""});
      if (was) toast_("☆ " + tr("Removed from the favourites"));
      try { navigator.vibrate && navigator.vibrate(25); } catch (x) {} }, 550)};
  }, true);
  const lpEnd = e => { if (lp && (e.type !== "pointermove" || Math.hypot(e.clientX - lp.x0, e.clientY - lp.y0) > 12)) { clearTimeout(lp.t); lp = null; } };
  ["pointerup", "pointercancel", "pointermove"].forEach(n => document.addEventListener(n, lpEnd, true));
  document.addEventListener("click", e => { const b = e.target.closest && e.target.closest("#qsw > button[id^='qs-']");
    if (b && b.dataset.lp) { e.preventDefault(); e.stopImmediatePropagation(); delete b.dataset.lp; } }, true);   // the long press does not switch
  document.addEventListener("contextmenu", e => { if (e.target.closest && e.target.closest("#qsw > button[id^='qs-']")) e.preventDefault(); }, true);
  function qsTips() { document.querySelectorAll("#qsw > button[id^='qs-']").forEach(b => { if (b.dataset.fvTip) return; b.dataset.fvTip = "1";
    b.title = (b.title ? b.title + " · " : "") + tr("Long press: favourite"); }); }
  function paintAll() { if (document.body.dataset.tab === "fav") { buildPage(); paintPage(); } rowStars(); qsTips(); }
  load(); setInterval(paintAll, 1000);
})();
</script>"""

_render_page_639zzzi = render_page


# wraps: render_page
def render_page(page, active):                                 # + 639zzzi: the star tab everywhere, the ★ page, the ☆ on the rows
    out = _render_page_639zzzi(page, active)
    if '<nav class="nav">' not in out or "</head>" not in out or "</body>" not in out:
        return out
    out = out.replace("</head>", FAV_CSS + "</head>", 1)
    if active == "party" and "</body>" in out:                 # /party?game=<id>: the game of the tile is chosen
        i = out.rfind("</body>")
        out = out[:i] + "<script>window.FAV_CAT=" + json.dumps(fav_catalog(), ensure_ascii=False).replace("</", "<\\/") + ";</script>" + FAV_PARTY_JS + out[i:]
    if active in ("fav", "live") or "MS_PAGE=" in out:
        i = out.rfind("</body>")
        extra = ""
        if active == "fav" and "window.MS_CONF" not in out:
            extra = "<script>window.MS_CONF=" + json.dumps(MS_PAGES, ensure_ascii=False) + ";window.MS_TX=" + json.dumps(ms_tx(), ensure_ascii=False).replace("</", "<\\/") + ";</script>"
        out = out[:i] + extra + "<script>window.FAV_CAT=" + json.dumps(fav_catalog(), ensure_ascii=False).replace("</", "<\\/") + ";</script>" + FAV_JS + out[i:]
    return out


def fav_selftest():
    for k in _HX_FAV:
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), "639zzzi: text " + k
    assert fav_clean([{"k": "qs:patrol"}, {"k": "qs:patrol"}, {"k": "bad key"}, {"k": "row:settings:sec:Updates", "l": "Updates", "i": "⬆"}]) == [
        {"k": "qs:patrol", "l": "", "i": ""}, {"k": "row:settings:sec:Updates", "l": "Updates", "i": "⬆"}], "639zzzi: clean"
    keep = CFG.get("ui_fav")
    try:
        CFG["ui_fav"] = {}
        fav_set("kid", [{"k": "game:quiz"}])
        assert fav_get("kid") == [{"k": "game:quiz", "l": "", "i": ""}] and fav_get("admin") == [], "639zzzi: per user"
    finally:
        CFG["ui_fav"] = keep
    assert "/api/fav" in VIEW_POST and role_allows("view", "/api/fav", "GET", {}) and role_allows("kid", "/api/fav", "POST", {}), "639zzzi: every user keeps his favourites"
    p = render_page(WEB_PAGE, "fav")
    assert 'href="/fav" class="fav on"' in p and "favInit" in p and "FAV_CAT" in p, "639zzzi: the ★ tab"
    return "★ tab, favourites per user (/api/fav), tiles with the same functions, ☆ on the rows"


SELFTEST_EXTRA.append(("★ Favourites (639zzzi)", fav_selftest))


# ---- the window (Tkinter): a tab «★» with the same favourites (the window = the owner, «admin») ----------------------------------
def _fav_tk_tabs(self):
    return [(k, "★" if k == "fav" else lab) for k, lab in _fav_tk_tabs_before(self)]


def _fav_tk_level():
    try:
        return str((protect_status(None) or {}).get("level") or "")
    except Exception:
        return ""


def _fav_tk(self, body):
    """the tab ★: the favourites as big buttons (four per row), switches with their state, a click runs it"""
    card = tk.Frame(body, bg=C["bg"]); card.grid(row=0, column=0, sticky="nsew")
    tk.Label(card, text="★ " + tr("Favourites"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 14, "bold"), anchor="w").pack(fill="x", pady=(4, 10))
    items = fav_get("admin")
    self._fav_tiles = []
    if not items:
        tk.Label(card, text="☆", bg=C["bg"], fg=C["acc"], font=("DejaVu Sans", 40)).pack(pady=(30, 6))
        tk.Label(card, text=tr("fav-tk-empty"), bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 10), wraplength=420, justify="center").pack()
        return
    grid = tk.Frame(card, bg=C["bg"]); grid.pack(fill="both", expand=True)
    cols = 4
    for c_ in range(cols):
        grid.columnconfigure(c_, weight=1, uniform="fav")
    for n, f in enumerate(items):
        b = tk.Label(grid, text=(f.get("i") or "★") + "\n" + (f.get("l") or f["k"].split(":", 1)[1]), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"),
                     highlightthickness=1, highlightbackground=C["line"], padx=6, pady=14, wraplength=150, justify="center", cursor="hand2")
        b.grid(row=n // cols, column=n % cols, sticky="nsew", padx=4, pady=4)
        b.bind("<Button-1>", lambda e, f=f: self._fav_go(f))
        self._fav_tiles.append((f, b))
    self._fav_paint()


def _fav_tk_on(self, f):
    kind, rest = f["k"].split(":", 1)
    if kind == "qs":
        q = next((x for x in self._qs_list() if x["id"] == rest), None)
        if q is None or q.get("flash") or rest in ("photo",):
            return None
        try:
            return bool(q["on"]())
        except Exception:
            return None
    if kind == "pr" and rest in ("off", "watch", "full"):
        return _fav_tk_level() == rest
    return None


def _fav_paint(self):
    for f, b in getattr(self, "_fav_tiles", []):
        try:
            if not b.winfo_exists():
                continue
            on = self._fav_tk_on(f)
            col = C["grn"] if on else C["line"]
            if b.cget("highlightbackground") != col:
                b.config(highlightbackground=col, highlightthickness=2 if on else 1)
        except Exception:
            pass
    if getattr(self, "_fav_tiles", None) and not getattr(self, "_fav_job", None):
        def run():
            self._fav_job = None
            if self.tab == "fav":
                self._fav_paint()
        self._fav_job = self.root.after(2000, run)


def _fav_go(self, f):
    """a click: the same function as the web page / the quick tiles of the window; pages and games open in the browser"""
    kind, rest = f["k"].split(":", 1)
    import webbrowser
    from tkinter import simpledialog, messagebox as mb_
    try:
        if kind == "qs":
            q = next((x for x in self._qs_list() if x["id"] == rest), None)
            if q is not None and (not q.get("ok") or q["ok"]()):
                q["go"]()
        elif kind == "pr":
            if rest == "night":
                self._night()
            elif rest == "off" and CFG.get("protect_pin"):     # with a PIN: asked like on the web page
                pin = simpledialog.askstring("MoveEye", tr("PIN for switching off"), show="*", parent=self.root)
                if pin is not None:
                    ok, err = protect_disarm(pin, "window")
                    if not ok:
                        mb_.showwarning("MoveEye", tr(err))
            elif rest in ("off", "watch", "full"):
                protect_set(rest, "window", None)
        elif kind == "row":
            page, rid = rest.split(":", 1)
            tab = {"settings": "settings", "protect": "protect", "sim": "sim"}.get(page)
            if tab:
                self._ms_next = rid[4:] if rid.startswith("sec:") else None
                self._tab(tab)
            else:
                webbrowser.open(page_address().rstrip("/") + {"history": "/recordings", "cams": "/cams"}.get(page, "/"))
        elif kind in ("page", "game"):
            href = next((h for k, _i, _e, h in FAV_PAGES if k == f["k"]), None) if kind == "page" else "/party?game=" + rest
            webbrowser.open(page_address().rstrip("/") + (href or "/"))
    except Exception as e:                                     # a favourite must never break the window
        log_event("sys", f"Favourite {f['k']}: {e}")
    self._fav_paint()


if "App" in globals():
    _fav_tk_tabs_before = App._tabs
    # wraps: App._tabs
    App._tabs = _fav_tk_tabs
    App._fav_tk, App._fav_tk_on, App._fav_paint, App._fav_go = _fav_tk, _fav_tk_on, _fav_paint, _fav_go
