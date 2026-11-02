#@ MoveEye – Teil 639i: Reiter «Spielen» (Paket «Spielbereich», Besitzer 31.10.2026; Geschichten-Menü) – Kopfzeile (Stufe, Spielstand), «Weiterspielen»-Hinweis, Regal «Geschichten» (Karten nur zum Anschauen), «Entdecken» (Orte der Reihe nach), Blinki; Web /play und Fenster-Reiter, Daten vom 3D-Simulator (spielbereich.gd). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Same structure as the start screen «Spielen» of the simulator (simulator3d/scripts/spielbereich.gd): Blinki on top
# (greets, a tip, happy about a new level / a finished adventure), the level with its bar, the adventures (Camping-Platz →
# Ferienpark → Bergtal → Zuhause; locked / new / here / done / coming soon, «12 of 34 discovered»), the badges, and the
# links into the game wizard (/sim#gw), the discovery book (/sim#c-disc) and «Start the adventure» (simulator /control
# {"action": "spielbereich", "do": "start", "id"} – the simulator has the hook for the later Bergtal adventure).
# The state lives in the simulator (per PC: user://spiel/spielbereich.json); MoveEye keeps the last answer in
# DATA_DIR/spielbereich.json so the tab shows it when the simulator is off. No ranking, no music, no animations besides
# Blinki's blink.
# Geschichten-Menü (Besitzer 31.10.2026): the same cards as the simulator (geschichten.gd) - only to look at here: picture
# (/sim/story_pic/<id>.jpg from the simulator, else a drawn placeholder), one sentence, duration, «from X years», progress
# in %; on top «Continue: <story>, <chapter> (x %)» as information; the head line has level and Spielstand. «Adventures»
# is now «Discover». The badges moved into the discovery book (139 sheet 📖). «Das Hospiz» only for the owner (nacht_may:
# administrator, not in operator mode) - for everybody else the card and its picture do not exist.
# Here (after 639h, before 640) because NAV_ITEMS (470), render_page (510/584), blinki_js (589),
# smalltv_routes (552/599c), App (570) and the tables DE / TRX come before.
# ----------------------------------------------------------------------------
# 2.98.85 (Koordinator, bis Besitzer entscheidet): «Spielen» steht unter «Mehr» (zweite Zeile nach «Übersicht») statt als 7. Reiter -
# mit 7 Reitern passt die Leiste am Handy nicht mehr, «Mehr» wäre erst nach dem Wischen sichtbar. Als eigener Reiter wieder:
# NAV_ITEMS.insert([k for k, *_r in NAV_ITEMS].index("more"), ("play", "/play", "Play area", "Playing"))  (+ NAV_SUB/NAV_OF-Zeilen weg)
NAV_SUB["more"].insert(1, ("play", "/play", "Play area"))   # not «Play» (= «Abspielen» / «Lire» of videos)
NAV_OF["play"] = "more"
_PLAY = {"t": 0.0, "d": None}
PLAY_STATES = {"new": "New", "done": "✓ Done", "locked": "🔒 Locked", "soon": "Coming soon", "open": ""}


def _play_file():
    return os.path.join(DATA_DIR, "spielbereich.json")


def play_state(force=False):
    """the play area from the simulator (3 s cache); without simulator the last answer (offline=True)"""
    now = time.time()
    if not force and _PLAY["d"] is not None and now - _PLAY["t"] < 3.0:
        return _PLAY["d"]
    d = None
    if CFG.get("sim_on"):
        try:
            r = sim_control({"action": "spielbereich", "do": "info"}) or {}
            if r.get("ok") and isinstance(r.get("chapters"), list):
                d = {k: r.get(k) for k in ("chapters", "badges", "level", "blinki", "current", "scene", "stories", "resume", "slot", "kids", "playing")}
                d.update(ok=True, offline=False, t=now)
                try:
                    with open(_play_file(), "w", encoding="utf-8") as f:
                        json.dump(d, f, ensure_ascii=False)
                except OSError:
                    pass
        except Exception:
            d = None
    if d is None:
        try:
            with open(_play_file(), encoding="utf-8") as f:
                d = json.load(f)
            d.update(ok=True, offline=True)
        except (OSError, ValueError):
            d = {"ok": True, "offline": True, "chapters": [], "badges": [], "level": None, "blinki": None, "t": 0}
        d["sim_on"] = bool(CFG.get("sim_on"))
    _PLAY.update(t=now, d=d)
    return d


def play_for(d, owner=True):
    """the answer for one viewer: «Das Hospiz» only for the owner (administrator, not in operator mode)"""
    if owner or not d:
        return d
    d = dict(d)
    d["stories"] = [x for x in (d.get("stories") or []) if x.get("id") != "horror"]
    if (d.get("resume") or {}).get("id") == "horror":
        d["resume"] = {}
    return d


def play_story_pic(sid, owner=True):
    """the picture of a story card from the simulator (JPEG bytes) or None"""
    sid = str(sid or "")
    if not CFG.get("sim_on") or not re.fullmatch(r"[a-z0-9]{1,16}", sid) or (sid == "horror" and not owner):
        return None
    try:
        b_, _h = _sim_get(f"/story_pic/{sid}.jpg", 3.0)
        return b_ or None
    except Exception:
        return None


def play_do(action, cid="", owner=True, what=""):
    """«Start the adventure» (id) / open or close the start screen in the simulator / «seen» (Blinki's joy shown).
    owner = nacht_may(...): «Das Hospiz» starts only for the owner (Code-Prüfung M4: before only the answer was filtered)"""
    if action in ("start", "story") and str(cid or "").strip().lower() == "horror" and not owner:
        log_event("web", "Play area: «Das Hospiz» refused (not the owner / operator mode)")
        return {"ok": False, "error": tr("Only the owner can start this story."), "code": 403}
    if not CFG.get("sim_on"):
        return {"ok": False, "error": tr("The 3D simulator is not connected.")}
    try:
        q_ = {"action": "spielbereich", "do": action, "id": str(cid)[:24]}
        if action == "story":                              # 3.51.x: a story from the phone - the same buttons as its card in the simulator
            q_["what"] = what if what in ("weiter", "neu", "unlock") else "weiter"
        r = sim_control(q_) or {}
    except Exception as e:
        _PLAY["t"] = 0.0
        if action == "start" and "timed out" in str(e):       # a big scene (Ferienpark) takes longer to build than the 8 s
            return {"ok": True, "loading": True, "state": _PLAY["d"] or play_state(True)}
        return {"ok": False, "error": str(e)[:80]}
    _PLAY["t"] = 0.0
    if not r.get("ok"):
        return {"ok": False, "error": {"locked": tr("This place is still locked."), "soon": tr("This place comes with a next version.")}.get(r.get("error"), str(r.get("error") or ""))}
    return {"ok": True, "state": play_state(True)}


PLAY_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Play</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:720px;margin:0 auto}
.pl-card{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px 14px;margin:0 0 12px}
.pl-h{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin:16px 2px 8px}
.pl-lv{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}.pl-lv b{font-size:17px}.pl-lv small{color:var(--mut)}
.pl-bar{height:6px;border-radius:3px;background:var(--line);overflow:hidden;margin-top:8px}.pl-bar i{display:block;height:100%;background:var(--acc)}
.pl-ch{display:flex;gap:12px;align-items:center;border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:12px 14px;margin:0 0 8px}
.pl-ch.cur{border-color:var(--acc)}.pl-ch.off{opacity:.62}
.pl-n{flex:none;width:30px;height:30px;border-radius:50%;border:2px solid var(--line);display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--mut)}
.pl-ch.st-new .pl-n,.pl-ch.st-open .pl-n{border-color:var(--acc);color:var(--acc)}.pl-ch.st-done .pl-n{border-color:var(--grn);color:var(--grn)}
.pl-t{flex:1;min-width:0}.pl-t b{font-size:15px}.pl-t .mut{font-size:12px;margin-top:2px}
.pl-chip{display:inline-block;font-size:11px;padding:1px 8px;border-radius:9px;margin-left:6px;border:1px solid var(--acc);color:var(--acc);vertical-align:2px}
.pl-chip.done{border-color:var(--grn);color:var(--grn)}.pl-chip.mut{border-color:var(--line);color:var(--mut)}
.pl-p{display:flex;gap:8px;align-items:center;margin-top:5px;font-size:13px}.pl-p .pl-bar{flex:0 0 110px;margin:0}
.pl-ch button{flex:none}
.pl-btns{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.pl-who{margin-left:auto;font-size:13px;color:var(--txt)}
.pl-go{border:1px solid var(--acc);border-radius:14px;background:var(--glow);padding:12px 14px;margin:0 0 12px;font-weight:600}.pl-go small{display:block;font-weight:400;color:var(--mut);margin-top:2px}
.pl-st{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.pl-s{border:1px solid var(--line);border-radius:14px;background:var(--panel);overflow:hidden;display:flex;flex-direction:column}
.pl-s.last{border-color:var(--acc)}.pl-s.off{opacity:.62}
.pl-sbt{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.pl-sbt button{min-height:38px}
.pl-pic{height:120px;background:#223 center/cover no-repeat;display:flex;align-items:center;justify-content:center;font-size:44px}
.pl-pic.grossvater{background-color:#a8946d;background-image:repeating-linear-gradient(90deg,transparent 0 24%,rgba(80,50,20,.2) 24% 25%)}
.pl-pic.maggie{background-image:linear-gradient(#5c94db,#c7e0f7 55%,#52803f 56%)}
.pl-pic.horror{background-image:linear-gradient(#05070c,#1a1e26 60%,#2a2f38)}
.pl-pic.teil2{background-color:#8c7c5c;filter:grayscale(.4)}
.pl-sb{padding:10px 12px 12px;display:flex;flex-direction:column;gap:4px}.pl-sb b{font-size:15px}.pl-sb .mut{font-size:12px}
.pl-m{font-size:12px}.pl-sp{display:flex;gap:8px;align-items:center;font-size:12px}.pl-sp .pl-bar{flex:1;margin:0}
body.kids .pl-sb b{font-size:18px}body.kids .pl-sb .mut,body.kids .pl-m,body.kids .pl-sp{font-size:15px}
@media(max-width:520px){.pl-st{grid-template-columns:1fr}.pl-ch{flex-wrap:wrap}.pl-ch button{width:100%}.pl-t{flex-basis:calc(100% - 44px)}}
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
  <div class="pl-card" id="pl-lv" hidden></div>
  <div id="pl-go"></div>
  <div class="pl-h" data-i18n="Stories">Stories</div>
  <div class="pl-st" id="pl-st"></div>
  <p class="mut" style="font-size:12px;margin:6px 2px 0" data-i18n="Stories are played in the simulator – here you see the progress.">Stories are played in the simulator – here you see the progress.</p>
  <div class="pl-h" data-i18n="Discover">Discover</div>
  <div id="pl-bk"></div>
  <div id="pl-ch"></div>
  <div class="pl-btns">
    <a class="btn" href="/sim#gw">🎮 <span data-i18n="Game wizard">Game wizard</span></a>
    <a class="btn sec" href="/sim#c-disc">📖 <span data-i18n="Discovery book">Discovery book</span></a>
    <button type="button" class="sec" id="pl-sim" onclick="plDo('open')">🖥 <span data-i18n="Open in the simulator">Open in the simulator</span></button>
  </div>
  <p class="mut" id="pl-msg"></p>
</main>
<script>/*BLINKI*/</script>
<script>
/*COMMON*/
/*PLAYDE*/
const ST = /*STATES*/{};
let PT = 0, BK = null, LASTB = "";
(async () => { await initAppearance(); plLoad(); })();
async function plLoad() {
  clearTimeout(PT); let j = null;
  try { j = await (await fetch("/api/play", {cache: "no-store"})).json(); } catch (e) {}
  if (j && j.ok) plPaint(j);
  PT = setTimeout(plLoad, 6000);
}
function el(tag, cls, txt) { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
function plPaint(j) {
  const B = window.MWBlinki, bk = j.blinki || (j.offline ? {mood: "think", title: t("Hello, I am Blinki!"), text: t("The 3D simulator is not connected. Switch on the simulation (tab Simulator) – then you see your stories and places here.")} : null);
  if (j.offline && j.blinki) bk.text = t("The 3D simulator is not connected – this is the state of last time.");
  const key = bk ? bk.mood + bk.title + bk.text : "";
  if (key !== LASTB) {
    LASTB = key; const box = document.getElementById("pl-bk"); box.textContent = "";
    if (bk && B && B.on()) { const r = B.row(bk.mood || "normal", bk.title, [bk.text]); box.appendChild(r); if (bk.mood === "happy") B.hop(r.fig); }
    else if (bk) { const c = el("div", "pl-card"); c.append(el("b", "", bk.title), el("div", "mut", bk.text)); box.appendChild(c); }
    if (bk && bk.mood === "happy" && !j.offline) post("/api/play", {action: "seen"}).catch(() => {});
  }
  const L = j.level, lv = document.getElementById("pl-lv"); lv.hidden = !L;
  if (L) {
    lv.textContent = ""; const h = el("div", "pl-lv"); h.append(el("b", "", "⭐ " + t("Level") + " " + L.lv),
      el("small", "", t("{xp} points · {n} more to level {l}").replace("{xp}", L.xp).replace("{n}", L.to - L.xp).replace("{l}", L.lv + 1)));
    if (j.slot) h.appendChild(el("span", "pl-who", "👤 " + (j.slot.name || t("Game state {n}").replace("{n}", j.slot.n))));
    h.title = (L.parts || []).map(p => p[0] + " " + p[1]).join(" · ");
    const b = el("div", "pl-bar"), i = el("i"); i.style.width = Math.max(0, Math.min(100, 100 * (L.xp - L.from) / Math.max(1, L.to - L.from))) + "%"; b.appendChild(i);
    lv.append(h, b);
  }
  document.body.classList.toggle("kids", !!j.kids);
  const go = document.getElementById("pl-go"), R = j.resume || {}; go.textContent = "";
  if (R.id) { const g = el("div", "pl-go", "▶ " + (R.where ? t("Continue: {t}, {w} ({p} %)").replace("{w}", R.where) : t("Continue: {t} ({p} %)")).replace("{t}", R.title).replace("{p}", R.pct));
    const gb = el("button", "", t("Continue playing")); gb.type = "button"; gb.disabled = !!j.offline || !!R.locked;
    gb.onclick = () => plDo("story", R.id, gb, "weiter"); g.appendChild(el("div", "pl-sbt")).appendChild(gb);
    g.appendChild(el("small", "", t("Opened in the simulator – you play it in the simulator window (tab «Sim»).")));
    go.appendChild(g); }
  const sg = document.getElementById("pl-st"); sg.textContent = "";
  if (!(j.stories || []).length) sg.appendChild(el("p", "mut", t("No stories yet – they come from the 3D simulator.")));
  const EMO = {grossvater: "🗺", maggie: "🐕", horror: "🔒", teil2: "🔒"};
  (j.stories || []).forEach(x => {
    const c = el("div", "pl-s" + (x.last && x.started ? " last" : "") + (x.soon ? " off" : "")), pic = el("div", "pl-pic " + x.id);
    if (x.pic && !j.offline && !x.locked) pic.style.backgroundImage = "url('/sim/story_pic/" + x.id + ".jpg?p=" + x.pct + "')";
    else pic.textContent = x.locked || x.soon ? "🔒" : (EMO[x.id] || "📖");
    const b = el("div", "pl-sb"), ti = el("b", "", x.title);
    const chip = x.soon ? t("Coming soon") : x.locked ? t("🔒 Locked") : x.done ? t("✓ Done") : !x.started ? t("New") : "";
    if (chip) ti.appendChild(el("span", "pl-chip" + (x.done ? " done" : x.soon || x.locked ? " mut" : ""), chip));
    const p = el("div", "pl-sp"), br = el("div", "pl-bar"), i = el("i"); i.style.width = Math.max(0, Math.min(100, x.pct)) + "%"; br.appendChild(i);
    p.append(br, el("span", "", x.pct + " %" + (x.where && !x.done ? " · " + x.where : "")));
    b.append(ti, el("div", "mut", x.short || ""), el("div", "pl-m", "⏱ " + (x.dauer || "") + " · " + t("from {n} years").replace("{n}", x.age)), p);
    if (!x.soon) {                                   // 3.51.x: start / continue from the phone (the same as the buttons of the card in the simulator)
      const bt = el("div", "pl-sbt"), add = (txt, what, sec) => { const k = el("button", sec ? "sec" : "", txt); k.type = "button";
        k.disabled = !!j.offline; k.onclick = () => plDo("story", x.id, k, what); bt.appendChild(k); };
      if (x.locked) add(t("Unlock"), "unlock", false);
      else { add(x.started && !x.done ? t("Continue playing") : t("Start story"), "weiter", false); if (x.started) add(t("Start over"), "neu", true); }
      b.appendChild(bt); }
    c.append(pic, b); sg.appendChild(c);
  });
  const ch = document.getElementById("pl-ch"); ch.textContent = "";
  if (!(j.chapters || []).length) ch.appendChild(el("p", "mut", t("No places yet – they come from the 3D simulator.")));
  (j.chapters || []).forEach(c => {
    const off = c.state === "locked" || c.state === "soon", r = el("div", "pl-ch st-" + c.state + (c.current ? " cur" : "") + (off ? " off" : ""));
    const tx = el("div", "pl-t"), ti = el("b", "", c.name); tx.appendChild(ti);
    const chip = ST[c.state] ? t(ST[c.state]) : "";
    if (chip) tx.appendChild(el("span", "pl-chip" + (c.state === "done" ? " done" : off ? " mut" : ""), chip));
    if (c.current) tx.appendChild(el("span", "pl-chip", t("You are here")));
    tx.appendChild(el("div", "mut", c.short || ""));
    const p = el("div", "pl-p");
    if (c.state === "soon") p.appendChild(el("span", "mut", t("This place comes with a next version.")));
    else if (c.state === "locked") p.appendChild(el("span", "mut", t("Opens when half of the place before is discovered.")));
    else if (c.total > 0) { p.appendChild(el("span", "", t("{f} of {n} discovered").replace("{f}", c.found).replace("{n}", c.total)));
      const b = el("div", "pl-bar"), i = el("i"); i.style.width = (100 * c.found / c.total) + "%"; b.appendChild(i); p.appendChild(b); }
    else p.appendChild(el("span", "mut", c.visited ? t("Nothing to discover here (yet).") : t("Not visited yet – what there is to discover shows on the spot.")));
    tx.appendChild(p);
    const n = el("div", "pl-n", String(c.n)), bt = el("button", off || c.current ? "sec" : "", off ? (c.state === "soon" ? t("Coming soon") : t("Locked")) : c.current ? t("Keep discovering") : t("Travel there"));
    bt.type = "button"; bt.disabled = off || j.offline; if (!off) bt.onclick = () => plDo("start", c.id, bt);
    r.append(n, tx, bt); ch.appendChild(r);
  });
  document.getElementById("pl-sim").disabled = !!j.offline;
  document.getElementById("pl-msg").textContent = j.offline && j.t ? t("Last state from the simulator") + ": " + new Date(j.t * 1000).toLocaleString() : "";
}
async function plDo(a, id, b, what) {
  if (b) b.disabled = true;
  const r = await post("/api/play", {action: a, id: id || "", what: what || ""});
  if (r && r.ok && r.state) plPaint(r.state);
  const m = document.getElementById("pl-msg");
  m.textContent = r && !r.ok ? "⚠ " + (r.error || "") : (a === "start" && r && r.ok ? "✓ " + t("The simulator travels there.") : "");
  if (a === "story" && r && r.ok) {                  // 3.51.x: the story runs in the simulator - play it in its window (stream, fingers)
    m.textContent = "✓ " + t("Opened in the simulator – you play it in the simulator window (tab «Sim»).") + " ";
    const go = el("a", "", t("To the simulator window") + " ›"); go.href = "/sim"; m.appendChild(go); }
  if (b) b.disabled = false;
}
/*ALERTS*/
</script>
</body></html>
"""

_HX_PLAY = {
    'Play area': ('Spielen', 'Jouer', 'Giocare', 'Giugar'),
    'Playing': ('Spielen', 'Jouer', 'Giocare', 'Giugar'),
    'Badges': ('Abzeichen', 'Badges', 'Distintivi', 'Insignas'),
    'Level': ('Stufe', 'Niveau', 'Livello', 'Stgalim'),
    '{xp} points · {n} more to level {l}': ('{xp} Punkte · noch {n} bis Stufe {l}', '{xp} points · encore {n} jusqu’au niveau {l}',
                                            '{xp} punti · ancora {n} per il livello {l}', '{xp} puncts · anc {n} fin al stgalim {l}'),
    'New': ('Neu', 'Nouveau', 'Nuovo', 'Nov'),
    '✓ Done': ('✓ Geschafft', '✓ Réussi', '✓ Fatto', '✓ Reussì'),
    '🔒 Locked': ('🔒 Gesperrt', '🔒 Verrouillé', '🔒 Bloccato', '🔒 Bloccà'),
    'Locked': ('Gesperrt', 'Verrouillé', 'Bloccato', 'Bloccà'),
    'Coming soon': ('Kommt bald', 'Bientôt', 'Presto', 'Vegn prest'),
    'You are here': ('Hier bist du', 'Tu es ici', 'Sei qui', 'Ti es qua'),
    'Keep playing': ('Weiter spielen', 'Continuer à jouer', 'Continua a giocare', 'Giugar vinavant'),
    'Nothing to discover here (yet).': ('Hier gibt es (noch) nichts zu entdecken.', 'Rien à découvrir ici (pour l’instant).', 'Qui non c’è (ancora) niente da scoprire.',
                                        'Qua na datti (anc) nagut da scuvrir.'),
    'Not visited yet – what there is to discover shows on the spot.': ('Noch nicht besucht – was es zu entdecken gibt, zeigt sich vor Ort.',
                                                                       'Pas encore visité – ce qu’il y a à découvrir se montre sur place.',
                                                                       'Non ancora visitato – cosa c’è da scoprire si vede sul posto.',
                                                                       'Anc betg visità – tge ch’i dat da scuvrir sa mussa al lieu.'),
    'Stories': ('Geschichten', 'Histoires', 'Storie', 'Istorgias'),
    'Start story': ('Starten', 'Démarrer', 'Avvia', 'Cumenzar'),
    'Continue playing': ('Weiterspielen', 'Continuer', 'Continua', 'Cuntinuar a giugar'),
    'Start over': ('Neu beginnen', 'Recommencer', 'Ricomincia', 'Cumenzar da nov'),
    'Unlock': ('Entsperren', 'Déverrouiller', 'Sblocca', 'Deblocar'),
    'Opened in the simulator – you play it in the simulator window (tab «Sim»).': (
        'Im Simulator geöffnet – gespielt wird im Simulator-Fenster (Reiter «Sim»).',
        'Ouvert dans le simulateur – on joue dans la fenêtre du simulateur (onglet «Sim»).',
        'Aperto nel simulatore – si gioca nella finestra del simulatore (scheda «Sim»).',
        'Avert en il simulatur – ins giogia en la fanestra dal simulatur (tab «Sim»).'),
    'To the simulator window': ('Zum Simulator-Fenster', 'Vers la fenêtre du simulateur', 'Alla finestra del simulatore', 'Tar la fanestra dal simulatur'),
    'Only the owner can start this story.': ('Nur der Besitzer kann diese Geschichte starten.', 'Seul le propriétaire peut lancer cette histoire.',
                                             'Solo il proprietario può avviare questa storia.', 'Mo il proprietari po cumenzar questa istorgia.'),
    'Discover': ('Entdecken', 'Découvrir', 'Scoprire', 'Scuvrir'),
    'Travel there': ('Hinreisen', 'Y aller', 'Andarci', 'Ir là'),
    'Keep discovering': ('Weiter entdecken', 'Continuer à découvrir', 'Continua a scoprire', 'Cuntinuar a scuvrir'),
    'This place comes with a next version.': ('Dieser Ort kommt mit einer nächsten Version.', 'Ce lieu arrive avec une prochaine version.',
                                              'Questo luogo arriva con una prossima versione.', 'Quest lieu vegn cun ina proxima versiun.'),
    'This place is still locked.': ('Dieser Ort ist noch gesperrt.', 'Ce lieu est encore verrouillé.', 'Questo luogo è ancora bloccato.', 'Quest lieu è anc bloccà.'),
    'Opens when half of the place before is discovered.': ('Öffnet sich, wenn der Ort davor zur Hälfte entdeckt ist.',
                                                           'S’ouvre quand la moitié du lieu précédent est découverte.',
                                                           'Si apre quando metà del luogo precedente è scoperta.',
                                                           'S’avra, cura che la mesadad dal lieu avant è scuvrida.'),
    'No places yet – they come from the 3D simulator.': ('Noch keine Orte – sie kommen vom 3D-Simulator.', 'Pas encore de lieux – ils viennent du simulateur 3D.',
                                                         'Ancora nessun luogo – arrivano dal simulatore 3D.', 'Anc nagins lieus – els vegnan dal simulatur 3D.'),
    'No stories yet – they come from the 3D simulator.': ('Noch keine Geschichten – sie kommen vom 3D-Simulator.', 'Pas encore d’histoires – elles viennent du simulateur 3D.',
                                                          'Ancora nessuna storia – arrivano dal simulatore 3D.', 'Anc naginas istorgias – ellas vegnan dal simulatur 3D.'),
    'The simulator travels there.': ('Der Simulator reist hin.', 'Le simulateur y va.', 'Il simulatore ci va.', 'Il simulatur va là.'),
    'Continue: {t}, {w} ({p} %)': ('Weiterspielen: {t}, {w} ({p} %)', 'Continuer : {t}, {w} ({p} %)', 'Continua: {t}, {w} ({p} %)', 'Giugar vinavant: {t}, {w} ({p} %)'),
    'Continue: {t} ({p} %)': ('Weiterspielen: {t} ({p} %)', 'Continuer : {t} ({p} %)', 'Continua: {t} ({p} %)', 'Giugar vinavant: {t} ({p} %)'),
    'The button «Continue» is in the simulator (window «Playing»).': ('Den Knopf «Weiterspielen» gibt es im Simulator (Fenster «Spielen»).',
                                                                     'Le bouton «Continuer» se trouve dans le simulateur (fenêtre «Jouer»).',
                                                                     'Il pulsante «Continua» è nel simulatore (finestra «Giocare»).',
                                                                     'Il buttun «Giugar vinavant» è en il simulatur (fanestra «Giugar»).'),
    'from {n} years': ('ab {n} Jahren', 'dès {n} ans', 'da {n} anni', 'a partir da {n} onns'),
    'Game state {n}': ('Spielstand {n}', 'Partie {n}', 'Partita {n}', 'Stadi dal gieu {n}'),
    'Stories are played in the simulator – here you see the progress.': ('Gespielt wird im Simulator – hier siehst du den Fortschritt.',
                                                                         'On joue dans le simulateur – ici tu vois la progression.',
                                                                         'Si gioca nel simulatore – qui vedi i progressi.',
                                                                         'I vegn giugà en il simulatur – qua vesas ti il progress.'),
    'not yet': ('noch nicht', 'pas encore', 'non ancora', 'anc betg'),
    'Discovery book': ('Entdeckungsbuch', 'Carnet de découvertes', 'Diario delle scoperte', 'Cudesch da scuvertas'),
    'The 3D simulator is not connected.': ('Der 3D-Simulator ist nicht verbunden.', 'Le simulateur 3D n’est pas connecté.', 'Il simulatore 3D non è collegato.',
                                           'Il simulatur 3D n’è betg collià.'),
    'The 3D simulator is not connected. Switch on the simulation (tab Simulator) – then you see your stories and places here.': (
        'Der 3D-Simulator ist nicht verbunden. Schalte die Simulation ein (Reiter Simulator) – dann siehst du hier deine Geschichten und Orte.',
        'Le simulateur 3D n’est pas connecté. Active la simulation (onglet Simulateur) – ensuite tu vois ici tes histoires et tes lieux.',
        'Il simulatore 3D non è collegato. Attiva la simulazione (scheda Simulatore) – poi qui vedi le tue storie e i tuoi luoghi.',
        'Il simulatur 3D n’è betg collià. Activescha la simulaziun (register Simulatur) – lura vesas ti qua tias istorgias e tes lieus.'),
    'The 3D simulator is not connected – this is the state of last time.': ('Der 3D-Simulator ist nicht verbunden – das ist der Stand vom letzten Mal.',
                                                                            'Le simulateur 3D n’est pas connecté – voici l’état de la dernière fois.',
                                                                            'Il simulatore 3D non è collegato – questo è lo stato dell’ultima volta.',
                                                                            'Il simulatur 3D n’è betg collià – quai è il stadi da l’ultima giada.'),
    'Last state from the simulator': ('Letzter Stand vom Simulator', 'Dernier état du simulateur', 'Ultimo stato dal simulatore', 'Ultim stadi dal simulatur'),
    'Refresh': ('Aktualisieren', 'Actualiser', 'Aggiorna', 'Actualisar'),
    'Game wizard (browser)': ('Spiel-Assistent (Browser)', 'Assistant de jeu (navigateur)', 'Assistente di gioco (browser)', 'Assistent da gieu (navigatur)'),
    'Discovery book (browser)': ('Entdeckungsbuch (Browser)', 'Carnet de découvertes (navigateur)', 'Diario delle scoperte (browser)', 'Cudesch da scuvertas (navigatur)'),
    'Game wizard': ('Spiel-Assistent', 'Assistant de jeu', 'Assistente di gioco', 'Assistent da gieu'),
    'Open in the simulator': ('Im Simulator öffnen', 'Ouvrir dans le simulateur', 'Apri nel simulatore', 'Avrir en il simulatur'),
    'Hello, I am Blinki!': ('Hallo, ich bin Blinki!', 'Bonjour, je suis Blinki !', 'Ciao, sono Blinki!', 'Allegra, jau sun Blinki!'),
    '{f} of {n} discovered': ('{f} von {n} entdeckt', '{f} sur {n} découverts', '{f} di {n} scoperti', '{f} da {n} scuvrids'),
}
for _k, _v in _HX_PLAY.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


def play_page():
    keys = list(_HX_PLAY) + [v for v in PLAY_STATES.values() if v]
    js = "Object.assign(I18N.de, " + json.dumps({k: DE.get(k, k) for k in keys}, ensure_ascii=False) + ");"
    try:
        bk = blinki_js(cur_lang())
    except Exception:
        bk = ""
    return (render_page(PLAY_PAGE, "play").replace("/*PLAYDE*/", js, 1).replace("/*STATES*/{}", json.dumps(PLAY_STATES, ensure_ascii=False), 1)
            .replace("/*BLINKI*/", bk.replace("</", "<\\/"), 1))


_smalltv_routes_play_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639i: /play and /api/play (550 calls smalltv_routes once)
    _smalltv_routes_play_base(app, reply, body)
    from flask import request, Response

    @app.route("/play")
    def play_page_():
        return Response(play_page(), mimetype="text/html")

    @app.route("/api/play", methods=["GET", "POST"])
    def api_play():
        own = nacht_may(_nacht_role())                    # «Das Hospiz»: only the owner (administrator, not operator mode)
        if request.method == "GET":
            return reply(play_for(play_state(), own))
        d = body(); a = str(d.get("action") or "")
        if a not in ("start", "open", "close", "seen", "story"):
            return reply({"ok": False, "error": "unknown action"}, 400)
        r = play_do(a, d.get("id") or "", own, str(d.get("what") or ""))
        if r.pop("code", None) == 403:
            return reply(r, 403)
        if r.get("state"):
            r["state"] = play_for(r["state"], own)
        return reply(r)

    @app.route("/sim/story_pic/<sid>.jpg")
    def play_story_pic_(sid):
        """Geschichten-Menü: the picture of a story card (a picture from the story itself, from the simulator)"""
        b_ = play_story_pic(sid, nacht_may(_nacht_role()))
        if not b_:
            return Response("no picture", 404)
        return Response(b_, mimetype="image/jpeg", headers={"Cache-Control": "max-age=120"})


# ---- the window: the same tab «Spielen» --------------------------------------------------------------------------------
def _tk_play_tab(self, left):
    left.rowconfigure(0, weight=1)
    outer = tk.Frame(left, bg=C["bg"]); outer.grid(row=0, column=0, sticky="nsew")
    cv = tk.Canvas(outer, bg=C["bg"], bd=0, highlightthickness=0)
    sb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview); cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(cv, bg=C["bg"]); wid = cv.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.bind("<Configure>", lambda e: cv.itemconfigure(wid, width=e.width))
    self._play_inner = inner
    self._play_sig = None
    bar = self._tk_bar(left, [("🎮 " + tr("Game wizard (browser)"), lambda: self._open_page("/sim#gw")),
                              ("📖 " + tr("Discovery book (browser)"), lambda: self._open_page("/sim#c-disc")),
                              ("🖥 " + tr("Open in the simulator"), lambda: self._play_act("open"))])
    bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    self._play_paint(play_state() if _PLAY["d"] is not None else {"ok": True, "offline": True, "chapters": [], "badges": [], "stories": []})
    self._play_poll()


def _tk_play_poll(self):
    """fetch in the background (the simulator may be slow), paint in the Tk thread; every 6 s while the tab is shown"""
    if self.tab != "play" or not getattr(self, "_play_inner", None) or not self._play_inner.winfo_exists():
        return
    def work():
        d = play_state()
        try:
            self.root.after(0, lambda: self._play_paint(d))
        except Exception:
            pass
    threading.Thread(target=work, daemon=True).start()
    self._play_inner.after(6000, self._play_poll)


def _tk_play_act(self, a, cid="", what=""):
    def work():
        r = play_do(a, cid, nacht_may("admin"), what)     # the window = the owner, unless operator mode (M4)
        r.pop("code", None)
        try:
            self.root.after(0, lambda: (self._status("Playing", ("✓ " + tr("The simulator travels there.")) if r.get("ok") and a == "start"
                                                     else ("✓ " + tr("Opened in the simulator – you play it in the simulator window (tab «Sim»).")) if r.get("ok") and a == "story"
                                                     else ("⚠ " + str(r.get("error") or "")) if not r.get("ok") else tr("Open in the simulator")),
                                        r.get("ok") and self._play_paint(r["state"])))
        except Exception:
            pass
    threading.Thread(target=work, daemon=True).start()


def _tk_play_paint(self, d):
    inner = getattr(self, "_play_inner", None)
    if inner is None or not inner.winfo_exists():
        return
    d = play_for(d, nacht_may("admin"))                    # the window = the owner (unless operator mode)
    sig = json.dumps([d.get(k) for k in ("chapters", "stories", "resume", "slot", "level", "blinki", "offline")], sort_keys=True, default=str)
    if sig == self._play_sig:
        return
    self._play_sig = sig
    for w in inner.winfo_children():
        w.destroy()
    bk = d.get("blinki")
    if d.get("offline"):
        bk = {"mood": "think", "title": (bk or {}).get("title") or tr("Hello, I am Blinki!"),
              "text": tr("The 3D simulator is not connected – this is the state of last time.") if bk else
              tr("The 3D simulator is not connected. Switch on the simulation (tab Simulator) – then you see your stories and places here.")}
    if bk and not blinki_tk_say(inner, bk.get("mood") or "normal", bk.get("title") or "", bk.get("text") or "", C["bg"]):
        tk.Label(inner, text=bk.get("title") or "", bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(inner, text=bk.get("text") or "", bg=C["bg"], fg=C["mut"], anchor="w", justify="left", wraplength=520).pack(fill="x")
    if bk and bk.get("mood") == "happy" and not d.get("offline"):
        threading.Thread(target=lambda: play_do("seen"), daemon=True).start()
    L = d.get("level")
    if L:
        lc = self._card(inner); lc.pack(fill="x", pady=(8, 0))
        hl = tk.Frame(lc, bg=C["panel"]); hl.pack(fill="x")
        tk.Label(hl, text="⭐ " + tr("Level") + " " + str(L["lv"]), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 12, "bold")).pack(side="left")
        tk.Label(hl, text=tr("{xp} points · {n} more to level {l}").replace("{xp}", str(L["xp"])).replace("{n}", str(L["to"] - L["xp"])).replace("{l}", str(L["lv"] + 1)),
                 bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9)).pack(side="left", padx=(10, 0))
        sl = d.get("slot") or {}
        if sl:
            tk.Label(hl, text="👤 " + (sl.get("name") or tr("Game state {n}").replace("{n}", str(sl.get("n")))), bg=C["panel"], fg=C["txt"],
                     font=("DejaVu Sans", 10)).pack(side="right")
        pb = ttk.Progressbar(lc, maximum=max(1, L["to"] - L["from"])); pb.pack(fill="x", pady=(6, 0)); pb["value"] = max(0, L["xp"] - L["from"])
    R = d.get("resume") or {}
    if R.get("id"):
        txt = (tr("Continue: {t}, {w} ({p} %)").replace("{w}", str(R.get("where"))) if R.get("where") else tr("Continue: {t} ({p} %)"))
        rf = tk.Frame(inner, bg=C["panel"], highlightthickness=1, highlightbackground=C["acc"], padx=10, pady=8); rf.pack(fill="x", pady=(8, 0))
        tk.Label(rf, text="▶ " + txt.replace("{t}", str(R.get("title"))).replace("{p}", str(R.get("pct"))), bg=C["panel"], fg=C["txt"],
                 font=("DejaVu Sans", 11, "bold"), anchor="w").pack(fill="x")
        if not d.get("offline") and not R.get("locked"):
            self._fbtn(rf, tr("Continue playing"), lambda i=R.get("id"): self._play_act("story", i, "weiter"), primary=True).pack(anchor="w", pady=(4, 0))
        tk.Label(rf, text=tr("Opened in the simulator – you play it in the simulator window (tab «Sim»)."), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9),
                 anchor="w").pack(fill="x")
    ttk.Label(inner, text=tr("Stories").upper(), style="Mut.TLabel").pack(anchor="w", pady=(12, 4))
    sg = tk.Frame(inner, bg=C["bg"]); sg.pack(fill="x")
    if not d.get("stories"):
        ttk.Label(sg, text=tr("No stories yet – they come from the 3D simulator."), style="Mut.TLabel").grid(row=0, column=0, sticky="w")
    emo = {"grossvater": "🗺", "maggie": "🐕", "horror": "🔒", "teil2": "🔒"}
    for i, x in enumerate(d.get("stories") or []):
        off = bool(x.get("soon"))
        f = tk.Frame(sg, bg=C["panel"], highlightthickness=1, highlightbackground=C["acc"] if x.get("last") and x.get("started") else C["line"], padx=10, pady=8)
        f.grid(row=i // 2, column=i % 2, sticky="nsew", padx=(0, 8), pady=(0, 8)); sg.columnconfigure(i % 2, weight=1, uniform="st")
        chip = tr("Coming soon") if off else tr("🔒 Locked") if x.get("locked") else tr("✓ Done") if x.get("done") else tr("New") if not x.get("started") else ""
        tk.Label(f, text=("🔒" if x.get("locked") or off else emo.get(x.get("id"), "📖")) + "  " + str(x.get("title")) + ("   " + chip if chip else ""), bg=C["panel"],
                 fg=C["mut"] if off else C["txt"], font=("DejaVu Sans", 11, "bold"), anchor="w", justify="left", wraplength=250).pack(fill="x")
        tk.Label(f, text=str(x.get("short") or ""), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w", justify="left", wraplength=250).pack(fill="x")
        tk.Label(f, text="⏱ " + str(x.get("dauer") or "") + " · " + tr("from {n} years").replace("{n}", str(x.get("age"))), bg=C["panel"], fg=C["txt"],
                 font=("DejaVu Sans", 9), anchor="w").pack(fill="x", pady=(3, 0))
        pr = tk.Frame(f, bg=C["panel"]); pr.pack(fill="x", pady=(3, 0))
        pb = ttk.Progressbar(pr, maximum=100, length=120); pb.pack(side="left"); pb["value"] = int(x.get("pct") or 0)
        tk.Label(pr, text=f"{int(x.get('pct') or 0)} %" + (" · " + str(x.get("where")) if x.get("where") and not x.get("done") else ""), bg=C["panel"], fg=C["txt"],
                 font=("DejaVu Sans", 9)).pack(side="left", padx=(8, 0))
        if not off and not d.get("offline"):             # 3.51.x: start / continue here as well (the same buttons as the card in the simulator)
            br_ = tk.Frame(f, bg=C["panel"]); br_.pack(fill="x", pady=(6, 0))
            sid_ = x.get("id")
            if x.get("locked"):
                self._fbtn(br_, tr("Unlock"), lambda i=sid_: self._play_act("story", i, "unlock")).pack(side="left")
            else:
                self._fbtn(br_, tr("Continue playing") if x.get("started") and not x.get("done") else tr("Start story"),
                           lambda i=sid_: self._play_act("story", i, "weiter"), primary=True).pack(side="left")
                if x.get("started"):
                    self._fbtn(br_, tr("Start over"), lambda i=sid_: self._play_act("story", i, "neu")).pack(side="left", padx=(6, 0))
    ttk.Label(inner, text=tr("Stories are played in the simulator – here you see the progress."), style="Mut.TLabel").pack(anchor="w")
    ttk.Label(inner, text=tr("Discover").upper(), style="Mut.TLabel").pack(anchor="w", pady=(12, 4))
    if not d.get("chapters"):
        ttk.Label(inner, text=tr("No places yet – they come from the 3D simulator."), style="Mut.TLabel").pack(anchor="w")
    for c in d.get("chapters") or []:
        off = c.get("state") in ("locked", "soon")
        f = tk.Frame(inner, bg=C["panel"], highlightthickness=1, highlightbackground=C["acc"] if c.get("current") else C["line"], padx=10, pady=8)
        f.pack(fill="x", pady=(0, 6))
        col = C["grn"] if c.get("state") == "done" else (C["mut"] if off else C["acc"])
        tk.Label(f, text=str(c.get("n")), bg=C["panel"], fg=col, font=("DejaVu Sans", 14, "bold"), width=2).pack(side="left", padx=(0, 8))
        tx = tk.Frame(f, bg=C["panel"]); tx.pack(side="left", fill="x", expand=True)
        st = tr(PLAY_STATES.get(c.get("state"), "")) if PLAY_STATES.get(c.get("state")) else ""
        if c.get("current"):
            st = (st + " · " if st else "") + tr("You are here")
        tk.Label(tx, text=str(c.get("name")) + ("   " + st if st else ""), bg=C["panel"], fg=C["mut"] if off else C["txt"], font=("DejaVu Sans", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(tx, text=str(c.get("short") or ""), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w", justify="left", wraplength=420).pack(fill="x")
        if c.get("state") == "soon":
            pt = tr("This place comes with a next version.")
        elif c.get("state") == "locked":
            pt = tr("Opens when half of the place before is discovered.")
        elif int(c.get("total") or 0) > 0:
            pt = tr("{f} of {n} discovered").replace("{f}", str(c.get("found"))).replace("{n}", str(c.get("total")))
        else:
            pt = tr("Nothing to discover here (yet).") if c.get("visited") else tr("Not visited yet – what there is to discover shows on the spot.")
        pr = tk.Frame(tx, bg=C["panel"]); pr.pack(fill="x", pady=(3, 0))
        tk.Label(pr, text=pt, bg=C["panel"], fg=C["txt"] if int(c.get("total") or 0) > 0 else C["mut"], font=("DejaVu Sans", 9)).pack(side="left")
        if int(c.get("total") or 0) > 0 and not off:
            pb = ttk.Progressbar(pr, maximum=int(c["total"]), length=110); pb.pack(side="left", padx=(8, 0)); pb["value"] = int(c.get("found") or 0)
        if off:
            b = self._fbtn(f, tr("Coming soon") if c.get("state") == "soon" else tr("Locked"), lambda: None); b.config(fg=C["mut"], cursor="arrow")
        else:
            b = self._fbtn(f, tr("Keep discovering") if c.get("current") else tr("Travel there"), lambda i=c.get("id"): self._play_act("start", i),
                           primary=not c.get("current"))
        b.pack(side="right")
    if d.get("offline") and d.get("t"):
        ttk.Label(inner, text=tr("Last state from the simulator") + ": " + datetime.fromtimestamp(float(d["t"])).strftime("%d.%m. %H:%M"),
                  style="Mut.TLabel").pack(anchor="w", pady=(8, 0))


for _n, _f in (("_tk_play_tab", _tk_play_tab), ("_play_poll", _tk_play_poll), ("_play_act", _tk_play_act), ("_play_paint", _tk_play_paint)):
    setattr(App, _n, _f)


def play_selftest():
    assert ("play", "/play", "Play area") in NAV_SUB["more"] and NAV_OF.get("play") == "more" and "play" not in [k for k, *_r in NAV_ITEMS]
    keep = (CFG.get("sim_on"), dict(_PLAY))
    try:
        CFG["sim_on"] = False; _PLAY["d"] = None
        d = play_state(True)
        assert d["ok"] and d["offline"] and isinstance(d.get("chapters"), list)
        assert not play_do("start", "camping")["ok"]
        CFG["sim_on"] = True                                 # M4: «Das Hospiz» never starts for others (before: simulator asked)
        _sc = globals()["sim_control"]; asked = []
        globals()["sim_control"] = lambda d_: (asked.append(d_), {"ok": True})[1]
        _le = globals()["log_event"]; globals()["log_event"] = lambda *a, **k: None
        try:
            r = play_do("start", "horror", False)
            assert not r["ok"] and r.get("code") == 403 and not asked, ("Hospiz started without the owner", r, asked)
            r = play_do("start", " HORROR ", False)
            assert not r["ok"] and not asked, "Hospiz with another spelling"
            r = play_do("story", "horror", False, "neu")          # 3.51.x: the story buttons of the phone - the same rule
            assert not r["ok"] and r.get("code") == 403 and not asked, ("Hospiz story button without the owner", r, asked)
            play_do("story", "maggie", True, "neu")
            play_do("story", "maggie", True, "x")
            sq_ = [x_ for x_ in asked if x_.get("do") == "story"]
            assert sq_ == [{"action": "spielbereich", "do": "story", "id": "maggie", "what": "neu"},
                           {"action": "spielbereich", "do": "story", "id": "maggie", "what": "weiter"}], asked
            assert nacht_may("admin", locked=True) is False and nacht_may("user", locked=False) is False
        finally:
            globals()["sim_control"] = _sc; globals()["log_event"] = _le; CFG["sim_on"] = False
        html = play_page()
        assert 'href="/play"' in html and "/api/play" in html and "Geschichten" in html and "Entdecken" in html and "MWBlinki" in html
        assert 'plDo("story"' in html and "/sim" in html and tr("Start over", "rm") == "Cumenzar da nov"   # 3.51.x: stories from the phone
        assert 'id="pl-bd"' not in html and "/sim/story_pic/" in html             # Geschichten-Menü: badges in the discovery book
        st = {"stories": [{"id": "horror"}, {"id": "maggie"}], "resume": {"id": "horror"}}
        assert [x["id"] for x in play_for(st, False)["stories"]] == ["maggie"] and not play_for(st, False)["resume"]
        assert len(play_for(st, True)["stories"]) == 2 and play_story_pic("horror", False) is None and play_story_pic("../x") is None
        assert tr("Travel there", "fr") != "Travel there" and tr("Stories", "rm") == "Istorgias" and tr("Discover", "it") == "Scoprire"
        assert hasattr(App, "_tk_play_tab")
        assert HELP_PAGE.count('<section id="stories"') == 2 and all('id="stories"' in (HELP_X.get(L) or 'id="stories"') for L in ("fr", "it", "rm")), "manual: stories"
    finally:
        CFG["sim_on"] = keep[0]; _PLAY.clear(); _PLAY.update(keep[1])
    return "tab Play: nav, offline state, page, translations, window"


SELFTEST_EXTRA.append(("Play area: tab «Spielen» (web, window, simulator spielbereich.gd)", play_selftest))


# ---- 3.51.x (Daniel 02.11.2026): the manual (HELP_PAGE 540 + HELP_X) - a short chapter «Geschichten» before «Tipps & Tricks» ----
_HELP_STORY = {
    "de": ('<section id="stories" data-icon="📖"><h2>Geschichten im 3D-Simulator</h2><ul>'
           '<li><b>Vom Handy starten:</b> Mehr → Spielen → bei der Geschichte «Starten», «Weiterspielen» oder «Neu beginnen». '
           'Die Auswahl (Spielstand, Figur …) erscheint im Simulator-Fenster (Reiter Sim) – dort mit dem Finger antippen.</li>'
           '<li><b>Gehen:</b> im Simulator-Fenster (Vollbild oder 🕹) mit dem Stick links (gehen) und rechts (umschauen); am PC W A S D und die Maus.</li>'
           '<li><b>× Beenden:</b> jede Karte einer Geschichte hat oben rechts «× Beenden» (speichert und beendet). '
           '<b>Esc</b> öffnet die Pause, «Weiter» bringt die Karte zurück.</li>'
           '<li><b>Alles im Handy-Bild:</b> das Simulator-Fenster zeigt, was am PC offen ist – Karten der Geschichten und Spiele, Tagebuch, '
           'Fenster wie Gerät oder Kameras, Hinweise und Popups. Nur das Bedienfeld und der Mover-Stick des Simulators fehlen (MoveEye hat eigene).</li>'
           '</ul></section>\n'),
    "en": ('<section id="stories" data-icon="📖"><h2>Stories in the 3D simulator</h2><ul>'
           '<li><b>Start from the phone:</b> More → Play area → at the story «Start», «Continue playing» or «Start over». '
           'The choice (game state, figure …) appears in the simulator window (tab Sim) – tap it there with the finger.</li>'
           '<li><b>Walking:</b> in the simulator window (full screen or 🕹) the left stick walks, the right one looks around; at the PC W A S D and the mouse.</li>'
           '<li><b>× Quit:</b> every card of a story has «× Quit» at the top right (saves and ends). '
           '<b>Esc</b> opens the pause, «Continue» brings the card back.</li>'
           '<li><b>Everything in the phone picture:</b> the simulator window shows what is open at the PC – cards of the stories and games, diary, '
           'windows such as device or cameras, hints and popups. Only the panel and the mover stick of the simulator are left out (MoveEye has its own).</li>'
           '</ul></section>\n'),
    "fr": ('<section id="stories" data-icon="📖"><h2>Histoires dans le simulateur 3D</h2><ul>'
           '<li><b>Lancer depuis le portable :</b> Plus → Jouer → pour l’histoire « Démarrer », « Continuer » ou « Recommencer ». '
           'Le choix (partie, personnage …) apparaît dans la fenêtre du simulateur (onglet Sim) – le toucher du doigt.</li>'
           '<li><b>Marcher :</b> dans la fenêtre du simulateur (plein écran ou 🕹) le stick gauche fait marcher, le droit regarde autour ; au PC W A S D et la souris.</li>'
           '<li><b>× Quitter :</b> chaque carte d’une histoire a « × Quitter » en haut à droite (sauvegarde et termine). '
           '<b>Échap</b> ouvre la pause, « Continuer » ramène la carte.</li>'
           '<li><b>Tout dans l’image du portable :</b> la fenêtre du simulateur montre ce qui est ouvert au PC – cartes des histoires et des jeux, journal, '
           'fenêtres comme appareil ou caméras, conseils et fenêtres surgissantes. Seuls le panneau et le stick du mover du simulateur manquent (MoveEye a les siens).</li>'
           '</ul></section>\n'),
    "it": ('<section id="stories" data-icon="📖"><h2>Storie nel simulatore 3D</h2><ul>'
           '<li><b>Avviare dal telefono:</b> Altro → Giocare → per la storia «Avvia», «Continua» o «Ricomincia». '
           'La scelta (partita, personaggio …) appare nella finestra del simulatore (scheda Sim) – toccarla lì con il dito.</li>'
           '<li><b>Camminare:</b> nella finestra del simulatore (schermo intero o 🕹) lo stick sinistro cammina, quello destro guarda intorno; al PC W A S D e il mouse.</li>'
           '<li><b>× Esci:</b> ogni carta di una storia ha «× Esci» in alto a destra (salva e termina). '
           '<b>Esc</b> apre la pausa, «Continua» riporta la carta.</li>'
           '<li><b>Tutto nell’immagine del telefono:</b> la finestra del simulatore mostra ciò che è aperto al PC – carte delle storie e dei giochi, diario, '
           'finestre come dispositivo o telecamere, consigli e popup. Mancano solo il pannello e lo stick del mover del simulatore (MoveEye ha i suoi).</li>'
           '</ul></section>\n'),
    "rm": ('<section id="stories" data-icon="📖"><h2>Istorgias en il simulatur 3D</h2><ul>'
           '<li><b>Cumenzar cun il telefonin:</b> Dapli → Giugar → tar l’istorgia «Cumenzar», «Cuntinuar a giugar» u «Cumenzar da nov». '
           'La tscherna (stadi dal gieu, figura …) cumpara en la fanestra dal simulatur (tab Sim) – là la tutgar cun il det.</li>'
           '<li><b>Ir:</b> en la fanestra dal simulatur (maletg entir u 🕹) il stick sanester va, il dretg guarda enturn; al PC W A S D e la mieur.</li>'
           '<li><b>× Terminar:</b> mintga carta d’ina istorgia ha «× Terminar» sisum a dretga (memorisescha e termina). '
           '<b>Esc</b> avra la pausa, «Vinavant» porta la carta enavos.</li>'
           '<li><b>Tut en il maletg dal telefonin:</b> la fanestra dal simulatur mussa quai ch’è avert al PC – cartas da las istorgias e dals gieus, diari, '
           'fanestras sco apparat u cameras, cussegls e popups. Mo il pult e il stick dal mover dal simulatur mancan (MoveEye ha ils agens).</li>'
           '</ul></section>\n'),
}


def _help_story(doc, lang):
    if 'id="stories"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_STORY[lang] + doc[i:] if i >= 0 else doc


_hp_en_story = HELP_PAGE.find('<div lang="en">')
if _hp_en_story > 0:
    HELP_PAGE = _help_story(HELP_PAGE[:_hp_en_story], "de") + _help_story(HELP_PAGE[_hp_en_story:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_story(HELP_X[_L], _L)
