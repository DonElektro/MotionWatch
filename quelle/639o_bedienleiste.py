#@ MoveEye – Teil 639o: Bedienleiste und einklappbarer Kopf (ein gemeinsamer Baustein für jede Web-Seite mit Reitern): Kopf – Reiterzeile und Statuszeile einzeln einklappbar (Griff, roter Punkt bei Warnungen, pro Gerät gemerkt); Leiste unter den Reitern – Einfach / Experte · Symbole farbig / schlicht · Beim Start: Nur Gruppen · Alle zuklappen / Meine Ansicht (639r; lange drücken: Nur Gruppen) / Alle aufklappen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Besitzer (31.10.2026, Screenshots iPad): «Kopfbereich einklappbar, beide Teile einzeln» und «eine einheitliche Bedienleiste oben auf jeder Seite»
# (bisher nur in Einstellungen: Suche mit drei Knöpfen, darunter Einfach / Experte, Symbole, Beim Start). Der Baustein kommt über
# render_page() auf JEDE Seite mit Reitern (nav.nav); die Seite kann ihn über window.MWB_PAGE anpassen:
#   simplePage() -> Seitenschlüssel für /api/ui_simple ("" = auf dieser Seite gibt es nur eine Ansicht: Einfach / Experte grau)
#   simple(on)   -> eigene Umschaltung (sonst: speichern und neu laden)
#   (3.23: der Schalter «Beim Start: Nur Gruppen» ist entfernt - der Start ist «Meine Ansicht»)
# Die drei Klapp-Knöpfe wirken auf alle sichtbaren Klappkarten der Seite (<details>, dazu die Karten der Simulator-Steuerung
# .sc-card / .sc-sub; ohne Hilfe- und Statuskarten: #g2-tt, [data-mwb-skip]); «Nur Gruppen» = oberste Karten offen, die Themen darin zu. Keine Klappkarten: grau. Gleiche Ids wie früher
# (#all-close, #all-groups, #all-open, #start-groups), damit Hilfe, Rundgang und Bildschirmleser sie weiter finden.
# Simulator (Godot): derselbe Baustein in scripts/bedienleiste.gd; Pi-Fenster: App._mwbar() in 570.

# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_MWB = {
    'Hide the tabs': ('Reiter einklappen', 'Replier les onglets', 'Comprimi le schede', 'Zuppentar ils registers'),
    'Show the tabs': ('Reiter ausklappen', 'Afficher les onglets', 'Mostra le schede', 'Mussar ils registers'),
    'Hide the status line': ('Statuszeile einklappen', 'Replier la ligne d’état', 'Comprimi la riga di stato', 'Zuppentar la lingia da status'),
    'Show the status line': ('Statuszeile ausklappen', 'Afficher la ligne d’état', 'Mostra la riga di stato', 'Mussar la lingia da status'),
    'Status': ('Status', 'État', 'Stato', 'Status'),
    'This page has only one view': ('Diese Seite hat nur eine Ansicht', 'Cette page n’a qu’une seule vue', 'Questa pagina ha una sola vista',
                                    'Questa pagina ha mo ina vista'),
    'Nothing to fold on this page': ('Auf dieser Seite gibt es nichts zum Klappen', 'Rien à replier sur cette page', 'Niente da comprimere in questa pagina',
                                     'Nagut da zuppentar sin questa pagina'),
    'Symbols coloured': ('Symbole farbig', 'Symboles en couleur', 'Simboli a colori', 'Simbols colurads'),
    'plain': ('schlicht', 'simples', 'semplici', 'simpels'),
    # 3.88 (Klar stage 1): the menu «Display» of the bar and the one status line of the phone
    'Display': ('Darstellung', 'Affichage', 'Visualizzazione', 'Preschentaziun'),
    'Symbols': ('Symbole', 'Symboles', 'Simboli', 'Simbols'),
    'Fold the menus': ('Menüs auf- und zuklappen', 'Ouvrir et fermer les menus', 'Aprire e chiudere i menu', 'Avrir e serrar ils menus'),
    'Groups only': ('Nur Gruppen', 'Ouvrir seulement les groupes', 'Aprire solo i gruppi', 'Avrir mo las gruppas'),
    '1 problem': ('1 Problem', '1 problème', '1 problema', '1 problem'),
    '{n} problems': ('{n} Probleme', '{n} problèmes', '{n} problemi', '{n} problems'),
    'Status – tap: show all values': ('Status – antippen: alle Werte zeigen', 'État – toucher : afficher toutes les valeurs',
                                      'Stato – tocca: mostra tutti i valori', 'Status – tutgar: mussar tut las valurs'),
}
for _k, _v in _HX_MWB.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

MWB_KEYS = sorted(set(_HX_MWB) | {
    "Simple", "Expert", "On start: groups only", "Collapse all", "Groups only", "Expand all", "My view",
    "Simple: only the important settings. «Expert» shows all of them.", "Symbols: green dot or green symbol = switched on",
    "On every start the settings show only the groups. Off: the menus open as you left them."})


def mwb_tx():
    """the texts of the bar in de / fr / it / rm (English = the key)"""
    out = {"de": {k: DE.get(k, k) for k in MWB_KEYS}}
    for L in ("fr", "it", "rm"):
        out[L] = {k: TRX[L].get(k) or (DE.get(k, k) if L == "rm" else k) for k in MWB_KEYS}
    return out


MWB_CSS = r"""<style id="mwb-css">
/* 639o: header folds (tabs, status line) and the one bar under the tabs - sizes in rem, wraps on narrow screens (no sideways scroll) */
.mwb-grip{flex:none;display:inline-flex;align-items:center;gap:.35rem;height:1.6rem;min-height:0;padding:0 .45rem;margin:0;border-radius:99px;
  border:1px solid transparent;background:none;color:var(--mut);font-size:.75rem;font-weight:600;line-height:1;cursor:pointer;box-shadow:none}
.mwb-grip:hover{color:var(--txt);border-color:var(--line)}
.mwb-grip .mwb-ch{font-style:normal;font-size:.7rem}.mwb-grip .mwb-ch::before{content:"▴"}
.mwb-grip .mwb-gl,.mwb-grip .mwb-gi,.mwb-grip .mwb-dot{display:none}
.mwb-grip .mwb-dot{width:.55rem;height:.55rem;border-radius:50%;background:var(--red);font-style:normal;flex:none}
.mwb-grip.off{border-color:var(--line);background:var(--field);padding:0 .65rem}
.mwb-grip.off .mwb-ch::before{content:"▾"}.mwb-grip.off .mwb-gl{display:inline}
.mwb-grip.off.alert{border-color:var(--red);color:var(--red)}.mwb-grip.off.alert .mwb-dot{display:inline-block;animation:mwbPulse 1.2s infinite}
.mwb-grip.off.warn .mwb-dot{display:inline-block;background:var(--yel)}
.mwb-grip.off.alert .mwb-gi{display:inline;max-width:14rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@keyframes mwbPulse{50%{box-shadow:0 0 0 .3rem rgba(255,77,77,.25)}}
header>.chips>.mwb-grip{order:-10}
body.mwb-tabs-off header>nav.nav>a,body.mwb-tabs-off header>nav.subnav{display:none!important}
body.mwb-tabs-off header>nav.nav{background:none;border-color:transparent;padding:0;flex:0 0 auto!important;box-shadow:none}
body.mwb-chips-off header>.chips>:not(.mwb-grip){display:none!important}
body.mwb-chips-off header>.chips{flex:0 0 auto!important;overflow:visible!important;-webkit-mask-image:none!important;mask-image:none!important}
@media(min-width:761px){
  /* folded: both grips move up into the first line next to the name - the header shrinks to one line */
  body.mwb-tabs-off header:has(.chips)>.nav{grid-column:2!important;grid-row:1!important;justify-self:start!important}
  body.mwb-chips-off header:has(.chips)>.chips{grid-column:2!important;grid-row:1!important;justify-self:end;overflow:visible}
  body.mwb-tabs-off:not(.mwb-chips-off) header:has(.chips)>.chips{grid-row:2!important}
  body.mwb-tabs-off header:has(.chips)>.subnav{display:none!important}
}
/* narrow tablet (tabs in line 2, chips in line 3): the sub tabs in their own line 4 (before they lay over the chips) */
@media(min-width:761px) and (max-width:1099px){header:has(.chips)>.subnav{grid-column:1/4!important;grid-row:4!important}}
/* narrow screens: the status chips wrap instead of a sideways scroll row */
@media(max-width:760px){
  header>.chips{flex-wrap:wrap!important;overflow:visible!important;-webkit-mask-image:none!important;mask-image:none!important;row-gap:.3rem}
  header>.chips>.badge{font-size:.7rem;padding:.1rem .5rem;min-height:1.5rem}
}
@media(min-width:761px){.chips{flex-wrap:wrap!important;overflow:visible!important;row-gap:.35rem}}
#mwbar{display:flex;flex-wrap:wrap;align-items:center;gap:.45rem .7rem;padding:.4rem 1rem;border-bottom:1px solid var(--line);
  background:var(--hdr,var(--bg));font-size:.8rem;box-sizing:border-box;max-width:100%}
#mwbar .mwb-seg{display:inline-flex;flex:none;border:1px solid var(--line);border-radius:.6rem;overflow:hidden;background:var(--field)}
#mwbar .mwb-seg button{background:none;color:var(--mut);border:0;border-radius:0;padding:.32rem .75rem;font-size:.8rem;font-weight:600;
  white-space:nowrap;min-height:0;box-shadow:none}
#mwbar .mwb-seg button+button{border-left:1px solid var(--line)}
#mwbar .mwb-seg button.on{background:var(--acc);color:#fff}
#mwbar .dis{opacity:.45;pointer-events:none}
#mwbar .mwb-sg{display:inline-flex;align-items:center;gap:.5rem;flex:none;cursor:pointer;white-space:nowrap;color:var(--txt);margin:0}
#mwbar .mwb-sg input.sw{transform:scale(.85)}
/* 3.88 (Klar stage 1): symbols and the fold buttons are in ONE menu «Display» at the right end of the bar; Simple / Expert stays in the bar */
#mwbar .mwb-vw{position:relative;margin-left:auto;flex:none}
#mwbar .mwb-vbtn{display:inline-flex;align-items:center;gap:.45rem;min-height:2.4rem;padding:0 .8rem;border-radius:.6rem;font-size:.8rem;font-weight:600;white-space:nowrap}
#mwbar .mwb-vbtn svg{width:1.1rem;height:1.1rem;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
#mwbar .mwb-vbtn .mwb-cv{font-style:normal;font-size:.7rem;color:var(--mut)}
#mwbar .mwb-vbtn[aria-expanded="true"]{border-color:var(--acc)}
#mwbar .mwb-vpop{position:absolute;right:0;top:calc(100% + 6px);z-index:60;width:min(19rem,calc(100vw - 1.5rem));box-sizing:border-box;background:var(--panel);
  border:1px solid var(--line);border-radius:12px;padding:.7rem .8rem .8rem;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:.5rem}
#mwbar .mwb-vpop[hidden]{display:none}
#mwbar .mwb-vh{font-size:.78rem;color:var(--mut);font-weight:600;margin-top:.2rem}
#mwbar .mwb-vpop .mwb-seg{align-self:stretch;display:flex}#mwbar .mwb-vpop .mwb-seg button{flex:1;min-height:2.6rem;white-space:normal}
#mwbar .mwb-fold{display:flex;flex-direction:column;gap:.35rem}
#mwbar .mwb-fold button{width:100%;min-height:2.75rem;padding:0 .8rem;display:flex;align-items:center;justify-content:flex-start;gap:.7rem;border-radius:.6rem;
  font-size:.88rem;font-weight:600;text-align:left;line-height:1.2}
#mwbar .mwb-fold button .l{flex:1;min-width:0;overflow-wrap:anywhere}
#mwbar .mwb-fold button svg{flex:none;width:1.15rem;height:1.15rem;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
#mwbar .mwb-fold button.cur{background:var(--acc);color:#fff;border-color:transparent}
#mwbar .mwb-fold button:disabled{opacity:.4;cursor:default}
#mwbar .s{display:none}
@media(max-width:520px){
  #mwbar{padding:.35rem .6rem;gap:.35rem .45rem}
  #mwbar .mwb-seg button{padding:.3rem .7rem;font-size:.8rem}
  #mwbar .mwb-sg{font-size:.75rem;gap:.35rem}
}
/* touch screens: every button of the bar and the header grips at least 44 px high (Klar stage 1) */
@media(pointer:coarse),(max-width:760px){
  #mwbar .mwb-mode button,#mwbar .mwb-vbtn{min-height:44px}
  .mwb-grip{min-height:44px;min-width:40px;justify-content:center}
}
/* the phone: the tabs 44 px high, text in the middle */
@media(max-width:760px){header>nav.nav{align-items:stretch}header>nav.nav>a{display:inline-flex;align-items:center;justify-content:center;min-height:44px;box-sizing:border-box}
  header>nav.nav>.mwb-grip{min-width:28px;padding:0 .3rem}}
/* the phone: the status chips as ONE line - state, the worst thing, battery; a tap shows all chips (as before) */
.mwb-sum{display:none}
@media(max-width:760px){
  body:not(.mwb-sum-open) header:not(.hx)>.chips:has(>.mwb-sum)>.badge{display:none!important}   /* «alle Werte» (b-ok, hx) shows them too */
  .mwb-sum{display:flex;align-items:center;gap:.55rem;flex:1 1 0;min-width:0;min-height:44px;margin:0;padding:0 .8rem;border-radius:14px;
    border:1px solid var(--line);background:var(--panel);color:var(--txt);font-size:.85rem;line-height:1.2;text-align:left;cursor:pointer;box-shadow:none}
  body.mwb-sum-open .mwb-sum{flex:1 1 100%}
  .mwb-sum .mws-st{font-weight:700;white-space:nowrap}.mwb-sum .mws-st.grn{color:var(--grn)}.mwb-sum .mws-st.red,.mwb-sum .mws-st.alarm{color:var(--red)}
  .mwb-sum .mws-st.yel,.mwb-sum .mws-st.org{color:var(--yel)}
  .mwb-sum .mws-msg{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--mut)}
  .mwb-sum .mws-msg.red{color:var(--red)}.mwb-sum .mws-msg.yel{color:var(--yel)}
  .mwb-sum .mws-bat{white-space:nowrap;color:var(--mut)}
  .mwb-sum .mws-ch{font-style:normal;color:var(--mut);font-size:.75rem}.mwb-sum .mws-ch::before{content:"▾"}body.mwb-sum-open .mwb-sum .mws-ch::before{content:"▴"}
}
body.videoonly #mwbar,body.lv-mini #mwbar,body.hdrhidden #mwbar,body.mwb-nobar #mwbar{display:none!important}
</style>"""


MWB_JS = r"""<script>
(function () {
  if (window.MWB) return;
  const H = document.querySelector("header"); if (!H) return;
  const TX = window.MWB_TX || {};
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "de"; } catch (e) { return "de"; } };
  const tr = k => ((TX[L()] || {})[k]) || k;
  const lsg = (k, d) => { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } };
  const lss = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const P = () => window.MWB_PAGE || {};
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const post = (u, d) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)}).then(r => r.json()).catch(() => ({}));
  const B = document.body;
  // ---- 1. the header: tabs and status line fold one by one (remembered per device: mw-hdr-tabs / mw-hdr-chips, WEB_UI_LOCAL) ----
  const nav = H.querySelector(":scope > nav.nav"), chips = H.querySelector(":scope > .chips");
  function grip(host, kind) {
    const b = E("button", "mwb-grip"); b.type = "button"; b.id = "mwb-g-" + kind;
    b.append(E("i", "mwb-ch"), E("span", "mwb-gl"), E("i", "mwb-dot"), E("span", "mwb-gi"));
    host.insertBefore(b, host.firstChild); return b;
  }
  const G = {};
  if (nav) G.tabs = grip(nav, "tabs");
  if (chips) G.chips = grip(chips, "chips");
  function paintGrips() {
    if (G.tabs) { const off = B.classList.contains("mwb-tabs-off"), a = nav.querySelector("a.on .nl") || nav.querySelector("a.on");
      G.tabs.classList.toggle("off", off); G.tabs.querySelector(".mwb-gl").textContent = a ? a.textContent.trim() : "";
      G.tabs.title = tr(off ? "Show the tabs" : "Hide the tabs"); G.tabs.setAttribute("aria-label", G.tabs.title); G.tabs.setAttribute("aria-expanded", off ? "false" : "true"); }
    if (G.chips) { const off = B.classList.contains("mwb-chips-off");
      G.chips.classList.toggle("off", off); G.chips.querySelector(".mwb-gl").textContent = tr("Status");
      G.chips.setAttribute("aria-expanded", off ? "false" : "true"); alerts(); }
  }
  function alerts() {                         // folded status line: a red dot and a short info for alarm / error / FPS warning
    if (!G.chips) return; const red = [], yel = [];
    chips.querySelectorAll(".badge").forEach(b => { if (b.hidden || b.id === "b-sim" || b.classList.contains("vh")) return;
      const t = (b.textContent || "").replace(/\s+/g, " ").trim(); if (!t && !b.classList.contains("alarm")) return;
      if (b.classList.contains("red") || b.classList.contains("alarm")) red.push(t || "⚠"); else if (b.classList.contains("yel") || b.classList.contains("org")) yel.push(t); });
    const off = B.classList.contains("mwb-chips-off"), g = G.chips;
    g.classList.toggle("alert", off && red.length > 0); g.classList.toggle("warn", off && !red.length && yel.length > 0);
    g.querySelector(".mwb-gi").textContent = red.slice(0, 2).join(" · ");
    g.title = tr(off ? "Show the status line" : "Hide the status line") + (off && red.concat(yel).length ? "\n" + red.concat(yel).join("\n") : "");
    g.setAttribute("aria-label", g.title);
  }
  function setFold(kind, off, store) {
    B.classList.toggle("mwb-" + kind + "-off", off);
    if (store) lss("mw-hdr-" + kind, off ? "0" : "1");
    paintGrips(); window.dispatchEvent(new Event("resize"));
  }
  ["tabs", "chips"].forEach(k => { if (!G[k]) return;
    G[k].onclick = e => { e.stopPropagation(); setFold(k, !B.classList.contains("mwb-" + k + "-off"), true); };
    B.classList.toggle("mwb-" + k + "-off", lsg("mw-hdr-" + k, "1") === "0"); });
  setInterval(() => { if (B.classList.contains("mwb-chips-off")) alerts(); }, 1000);
  // ---- 3.88 (Klar stage 1): the phone shows the status chips as ONE line - state · the worst thing · battery; a tap shows all
  // chips as before (remembered per device: mw-hdr-sum). Only where the status line has the protection state (b-arm).
  const SUM = chips && chips.querySelector("#b-arm") ? E("button", "mwb-sum") : null;
  let sumT = 0;
  function paintSum() {
    sumT = 0; if (!SUM) return;
    const T = b => (b.textContent || "").replace(/\s+/g, " ").trim(), shown = b => !!b && !b.hidden && !b.classList.contains("vh");
    const q = id => chips.querySelector("#" + id), arm = q("b-arm"), ok = q("b-ok");
    const bat = [q("b-batt"), q("b-pwr")].find(b => shown(b) && T(b));
    const st = SUM.querySelector(".mws-st"); st.textContent = shown(arm) ? T(arm) : "";
    st.className = "mws-st " + (arm ? [...arm.classList].filter(c => /^(grn|red|yel|org|blu|alarm)$/.test(c)).join(" ") : "");
    const red = [], yel = [], skip = ["b-arm", "b-ok", "b-led", "b-sim", "b-person", "b-view", "b-count", bat ? bat.id : ""];
    chips.querySelectorAll(".badge").forEach(b => { if (!shown(b) || skip.includes(b.id)) return;
      let t = T(b); if (b.id === "b-health") { const n = parseInt(t.replace(/\D+/g, ""), 10) || 1; t = n === 1 ? tr("1 problem") : tr("{n} problems").replace("{n}", n); }
      if (!t) return;
      if (b.classList.contains("red") || b.classList.contains("alarm")) red.push(t); else if (b.classList.contains("yel") || b.classList.contains("org")) yel.push(t); });
    const parts = red.concat(yel); if (!parts.length && shown(ok) && T(ok)) parts.push(T(ok));
    const m = SUM.querySelector(".mws-msg"), mt = parts.join(" · ");
    if (m.textContent !== mt) m.textContent = mt;
    m.className = "mws-msg" + (red.length ? " red" : yel.length ? " yel" : "");
    const bt = SUM.querySelector(".mws-bat"), btt = bat ? T(bat) : ""; if (bt.textContent !== btt) bt.textContent = btt;
    SUM.title = tr("Status – tap: show all values");
    SUM.setAttribute("aria-label", [st.textContent, mt, btt].filter(Boolean).join(", ") + " – " + SUM.title);
  }
  if (SUM) {
    SUM.type = "button"; SUM.id = "mwb-sum";
    SUM.append(E("span", "mws-st"), E("span", "mws-msg"), E("span", "mws-bat"), E("i", "mws-ch"));
    chips.insertBefore(SUM, G.chips ? G.chips.nextSibling : chips.firstChild);
    const setOpen = (v, store) => { B.classList.toggle("mwb-sum-open", v); SUM.setAttribute("aria-expanded", v ? "true" : "false");
      if (store) { lss("mw-hdr-sum", v ? "1" : "0"); window.dispatchEvent(new Event("resize")); } };
    SUM.onclick = e => { e.stopPropagation(); setOpen(!B.classList.contains("mwb-sum-open"), true); };
    setOpen(lsg("mw-hdr-sum", "0") === "1", false);
    new MutationObserver(ms => { if (!sumT && ms.some(x => !SUM.contains(x.target))) sumT = setTimeout(paintSum, 250); })
      .observe(chips, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["class", "hidden"]});
    paintSum();
  }
  // ---- 2. the bar under the tabs ----
  const bar = E("div"); bar.id = "mwbar"; bar.setAttribute("role", "toolbar");
  const seg = (cls, a, b) => { const s = E("div", "mwb-seg " + cls), x = E("button"), y = E("button"); x.type = y.type = "button";
    x.innerHTML = a; y.innerHTML = b; s.append(x, y); return [s, x, y]; };
  const [sm, bS, bE] = seg("mwb-mode", "", "");
  const [si, bC, bP] = seg("mwb-ic", '🎨 <span class="l"></span>', '◯ <span class="l"></span>');
  const fd = E("div", "mwb-fold");
  // 639r: the middle is «My view» (two bars + a small star); «Groups only» stays: long press / right click on «My view»,
  // and since 3.88 (Klar stage 1) also its own line in the menu «Display»
  const SV = {close: "M7 4l5 5 5-5M7 20l5-5 5 5", mine: "M4 5h16v5H4zM4 14h8v5H4zM18 12.6l1.2 2.4 2.6.4-1.9 1.8.5 2.6-2.4-1.3-2.4 1.3.5-2.6-1.9-1.8 2.6-.4z",
              groups: "M4 5h16v5H4zM8 14h12v5H8z", open: "M7 15l5 5 5-5M7 9l5-5 5 5"};
  const FB = {};
  [["close", "Collapse all"], ["mine", "My view"], ["groups", "Groups only"], ["open", "Expand all"]].forEach(([k, lb]) => {
    const b = E("button", "sec"); b.type = "button"; b.id = "all-" + k; b.dataset.k = lb; b.setAttribute("role", "menuitem");
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + SV[k] + '"/></svg><span class="l"></span>';
    b.onclick = () => { if (b._long) { b._long = false; return; } fold(k); closeView(); };
    FB[k] = b; fd.appendChild(b); });
  // 3.88 (Klar stage 1, owner): «Symbols» and the fold buttons are in ONE menu «Display»; Simple / Expert stays visible in the bar
  const vb = E("button", "sec mwb-vbtn"); vb.type = "button"; vb.id = "mwb-view"; vb.setAttribute("aria-haspopup", "true"); vb.setAttribute("aria-expanded", "false");
  vb.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/></svg><span class="l"></span><i class="mwb-cv">▾</i>';
  const vp = E("div", "mwb-vpop"); vp.id = "mwb-vpop"; vp.hidden = true; vp.setAttribute("role", "menu");
  const vh1 = E("div", "mwb-vh"), vh2 = E("div", "mwb-vh");
  vp.append(vh1, si, vh2, fd);
  function closeView() { vp.hidden = true; vb.setAttribute("aria-expanded", "false"); }
  vb.onclick = e => { e.stopPropagation(); const open = vp.hidden; vp.hidden = !open; vb.setAttribute("aria-expanded", open ? "true" : "false"); if (open) state(); };
  document.addEventListener("click", e => { if (!vp.hidden && !vp.contains(e.target) && !vb.contains(e.target)) closeView(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !vp.hidden) { closeView(); vb.focus(); } });
  (function () { const b = FB.mine; let tm = 0;                     // long press (touch / mouse) or right click: «Groups only»
    const go = () => { b._long = true; fold("groups"); };
    b.addEventListener("contextmenu", e => { e.preventDefault(); clearTimeout(tm); go(); setTimeout(() => { b._long = false; }, 400); });
    b.addEventListener("pointerdown", e => { if (e.button) return; clearTimeout(tm); b._long = false; tm = setTimeout(go, 600); });
    ["pointerup", "pointerleave", "pointercancel"].forEach(n => b.addEventListener(n, () => clearTimeout(tm))); })();
  const vw = E("div", "mwb-vw"); vw.append(vb, vp);
  bar.append(sm, vw);
  H.after(bar);
  // Simple / Expert of this page (586: /api/ui_simple per page); a page without two views shows it grey
  let SIMPLE = true;
  const pageKey = () => { const p = P(); return typeof p.simplePage === "function" ? (p.simplePage() || "") : ""; };
  function paintSimple() { bS.classList.toggle("on", SIMPLE); bE.classList.toggle("on", !SIMPLE); sm.classList.toggle("dis", !pageKey());
    sm.title = pageKey() ? tr("Simple: only the important settings. «Expert» shows all of them.") : tr("This page has only one view"); }
  async function loadSimple() { const k = pageKey();
    try { const j = await (await fetch("/api/ui_simple" + (k ? "?page=" + encodeURIComponent(k) : ""), {cache: "no-store"})).json();
      SIMPLE = !!j.on; } catch (e) {}
    paintSimple(); }
  // the ONE switch Simple / Expert (true = "simple", false = "expert")
  function setSimple(v) { if (!pageKey() || v === SIMPLE) return; SIMPLE = v; paintSimple(); const p = P();
    if (typeof p.simple === "function") return p.simple(v);
    post("/api/ui_simple", {on: v, page: pageKey()}).then(() => location.reload()); }
  bS.onclick = () => setSimple(true); bE.onclick = () => setSimple(false);
  // symbols coloured / plain (per device, like before: mw-icons + body.icplain)
  function paintIc() { const pl = lsg("mw-icons", "color") === "plain"; bC.classList.toggle("on", !pl); bP.classList.toggle("on", pl); B.classList.toggle("icplain", pl); }
  function setIcons(v) { lss("mw-icons", v === "plain" ? "plain" : "color"); paintIc(); }      // the ONE switch for the symbols: "color" | "plain"
  bC.onclick = () => setIcons("color"); bP.onclick = () => setIcons("plain");
  // 3.23 (Elektro 01.11.2026): the switch «On start: groups only» is gone - the start is «My view»; «Groups only» = long press on the middle
  // ---- the three fold buttons: every fold card that can be seen on this page ----
  const EXTRA = [{sel: ".sc-card", head: ":scope > .sc-hd"}, {sel: ".sc-sub", head: ":scope > .sc-sh"}];   // simulator control (470): div cards
  const SKIP = "header,#mwbar,.pop,#viewmenu,#lv-menu,[role=dialog],.mwt-ov,#g2-tt,[data-mwb-skip]";   // help / status cards (Tipps & Tricks, Selbstdiagnose) are no groups
  function shown(x) { for (let n = x; n && n !== B; n = n.parentElement) { if (n.hidden || getComputedStyle(n).display === "none") return false; } return true; }
  function items() {
    const R = document.querySelector("main") || B, out = [], seen = {};
    R.querySelectorAll("details").forEach(d => { if (d.classList.contains("inline") || d.closest(SKIP) || !shown(d)) return;
      out.push({el: d, get: () => d.open, set: v => { if (d.open !== v) d.open = v; }}); });
    EXTRA.forEach(x => R.querySelectorAll(x.sel).forEach(n => { const h = n.querySelector(x.head); if (!h || n.closest(SKIP) || !shown(n)) return;
      out.push({el: n, get: () => n.classList.contains("open"), set: v => { if (n.classList.contains("open") !== v) h.click(); }}); }));
    const S = new Map(out.map(o => [o.el, o]));
    out.forEach(o => { o.top = true; for (let n = o.el.parentElement; n && n !== R; n = n.parentElement) if (S.has(n)) { o.top = false; o.par = S.get(n); break; } });
    out.forEach(o => { let id = idOf(o); if (seen[id]) id += "#" + (++seen[id]); else seen[id] = 1; o.id = id; });
    return out;
  }
  // ---- 639r «My view» (Elektro 1.11.2026): the folds the user set himself - per user and page on the Pi (/api/ansicht), the same on
  // every device; without the Pi (no connection / not allowed) in this browser («mwa:…», not shared through web_ui). Kept: only what the
  // user opens / closes himself while «My view» is on. «Collapse all» / «Expand all» / «Groups only»: off, the kept view stays.
  function idOf(o) {                         // a stable id: data-view (grp:… / sec:…, the same as the Pi window), id, data-k, data-g …
    if (o._id) return o._id;
    const n = o.el, d = n.dataset || {};
    let id = d.mwbId || d.view || n.id || (d.k ? "k:" + d.k : "") || (d.g ? "g:" + d.g : "") || (d.fold ? "f:" + d.fold : "");
    if (!id) { const h = n.querySelector(":scope > summary, :scope > .sc-hd, :scope > .sc-sh"), i = h && (h.getAttribute("data-i18n") ? h : h.querySelector("[data-i18n]"));
      const t = i ? i.getAttribute("data-i18n") : (h ? h.textContent : "");
      id = "t:" + (o.par ? idOf(o.par) + "/" : "") + String(t || "").replace(/[▾▸▼▶]/g, "").replace(/\(\d+\)/g, "").replace(/\s+/g, " ").trim().slice(0, 60); }
    return (o._id = id.slice(0, 120));
  }
  const pageId = () => String(B.dataset.tab || window.MWB_SEITE || location.pathname.replace(/^\/+|\/+$/g, "").replace(/[^a-z0-9_-]/gi, "-") || "live").toLowerCase().slice(0, 40);
  const MINE = {on: true, page: "", map: {}, ready: false, done: new WeakSet(), first: false, local: false, timer: 0};
  const LSK = p => "mwa:ansicht:" + p;
  async function mineLoad() {
    const p = pageId(); MINE.page = p; MINE.ready = false; MINE.done = new WeakSet(); MINE.touched = false;
    let j = null;
    try { const r = await fetch("/api/ansicht?seite=" + encodeURIComponent(p), {cache: "no-store"}); if (r.ok) j = await r.json(); } catch (e) {}
    if (p !== MINE.page) return;
    let m = null; MINE.local = !(j && j.ok);
    if (!MINE.local) { if (j.known) { m = {}; (j.offen || []).forEach(k => { m[k] = true; }); (j.zu || []).forEach(k => { m[k] = false; }); } MINE.first = !!j.first_groups; }
    else { try { const v = JSON.parse(lsg(LSK(p), "null")); if (v && typeof v === "object") m = v; } catch (e) {} }
    MINE.map = m || {}; MINE.known = !!m; MINE.ready = true;
    if (MINE.on) mineApply(true); state();
  }
  function mineApply(all) {                  // the kept view onto the cards (all = every card; else only cards that came later)
    if (!MINE.ready) return;
    if (!MINE.known) {                       // nothing kept yet: the first view is «Groups only» (switch was on) or as the page builds it -
      if (MINE.first && !MINE.touched) items().forEach(o => o.set(o.top));   // kept with the first own click (the page has moved its cards by then)
      return;
    }
    items().forEach(o => { if (!all && MINE.done.has(o.el)) return; MINE.done.add(o.el);
      if (o.id in MINE.map) o.set(!!MINE.map[o.id]); });
  }
  // the ONE function per change (P2 can hang the simulator in here): one card opened / closed by the user
  function ansichtMerken(id, open) {
    if (!MINE.on || !MINE.ready || !id) return;
    if (!MINE.known) { items().forEach(o => { if (!(o.id in MINE.map)) MINE.map[o.id] = o.get(); }); MINE.known = true; }   // the first own click: the whole page
    MINE.map[id] = !!open; mineSave();
    if (typeof window.MWB_ON_ANSICHT === "function") try { window.MWB_ON_ANSICHT(MINE.page, id, !!open); } catch (e) {}
  }
  function mineSave() { clearTimeout(MINE.timer); MINE.timer = setTimeout(mineFlush, 1000); }
  function mineFlush() {
    MINE.timer = 0; const p = MINE.page, o = [], z = [];
    Object.keys(MINE.map).forEach(k => (MINE.map[k] ? o : z).push(k));
    lss(LSK(p), JSON.stringify(MINE.map));
    try { fetch("/api/ansicht", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({seite: p, offen: o, zu: z}), keepalive: true})
      .then(r => { MINE.local = !r.ok; paintMine(); }).catch(() => { MINE.local = true; paintMine(); }); } catch (e) {}
  }
  addEventListener("pagehide", () => { if (MINE.timer) { clearTimeout(MINE.timer); mineFlush(); } });
  const USR = new WeakMap();                 // a fold the user clicked himself (summary / card heading) - only these are kept
  document.addEventListener("click", e => { const h = e.target.closest && e.target.closest("summary, .sc-hd, .sc-sh"); if (!h || h.closest(SKIP)) return;
    const n = h.parentElement; USR.set(n, Date.now()); if (MINE.on) MINE.touched = true;   // from now on the user folds (no start view any more)
    if (n.tagName !== "DETAILS") setTimeout(() => { const o = items().find(x => x.el === n); if (o) ansichtMerken(o.id, o.get()); }, 0); }, true);
  document.addEventListener("toggle", e => { const n = e.target; if (n.tagName !== "DETAILS" || !(Date.now() - (USR.get(n) || 0) < 1500)) return;
    USR.delete(n); const o = items().find(x => x.el === n); if (o) ansichtMerken(o.id, o.get()); }, true);
  function paintMine() { const b = FB.mine; if (!b) return;
    b.title = tr("My view: the menus open and close the way you left them (kept for you on every device). Long press or right click: groups only.")
      + (MINE.local && MINE.ready ? "\n" + tr("My view – saved only on this device (no connection)") : ""); }
  function fold(k) {
    if (k === "mine") { MINE.on = true; mineApply(true); state(); return; }
    MINE.on = false; clearTimeout(MINE.timer); if (MINE.timer) mineFlush();
    const its = items();
    its.forEach(o => o.set(k === "open" || (k === "groups" && o.top)));
    state();
  }
  let stRaf = 0;
  function state() {
    stRaf = 0; if (MINE.on) mineApply(false);
    const its = items(), subs = its.filter(o => !o.top), tops = its.filter(o => o.top);
    const st = !its.length ? "" : its.every(o => o.get()) ? "open" : its.every(o => !o.get()) ? "close"
      : subs.length && tops.every(o => o.get()) && subs.every(o => !o.get()) ? "groups" : "";
    Object.keys(FB).forEach(k => { const b = FB[k], cur = MINE.on ? k === "mine" : st === k; b.classList.toggle("cur", cur); b.setAttribute("aria-pressed", cur ? "true" : "false");
      b.disabled = !its.length; b.title = its.length ? tr(b.dataset.k) : tr("Nothing to fold on this page");
      b.setAttribute("aria-label", tr(b.dataset.k)); });
    if (its.length) paintMine();
  }
  const later = () => { if (!stRaf) stRaf = requestAnimationFrame(state); };
  document.addEventListener("toggle", e => { if (e.target.tagName === "DETAILS") later(); }, true);
  document.addEventListener("click", e => { if (e.target.closest && e.target.closest(".sc-hd,.sc-sh")) setTimeout(later, 0); }, true);
  new MutationObserver(() => { later(); paintGrips(); paintSimple(); if (pageId() !== MINE.page) mineLoad(); }).observe(B, {attributes: true, attributeFilter: ["data-tab"]});
  let keySeen = null;
  function labels() {
    if (pageKey() !== keySeen) { keySeen = pageKey(); loadSimple(); }   // the page told its key later (guide 516 loads its data first)
    bS.textContent = tr("Simple"); bE.textContent = tr("Expert");
    vb.querySelector(".l").textContent = tr("Display"); vb.title = tr("Display"); vh1.textContent = tr("Symbols"); vh2.textContent = tr("Fold the menus");
    Object.keys(FB).forEach(k => { FB[k].querySelector(".l").textContent = tr(FB[k].dataset.k); });
    paintSum();
    bC.querySelector(".l").textContent = tr("Symbols coloured"); bP.querySelector(".l").textContent = tr("plain");
    bC.title = tr("Symbols coloured"); bP.title = tr("plain"); si.setAttribute("aria-label", tr("Symbols: green dot or green symbol = switched on"));
    paintGrips(); paintSimple(); state();
  }
  paintIc(); labels(); mineLoad();
  [300, 1500, 4000].forEach(ms => setTimeout(labels, ms));            // after the page has built its cards and knows its language
  // one function per change (review P0): setSimple, setIcons, setStartGroups, fold("close" | "mine" | "groups" | "open"), ansichtMerken; the header folds stay per device
  window.MWB = {setSimple: setSimple, setIcons: setIcons, fold: fold, state: later, setFold: setFold, refresh: labels,
                mine: () => fold("mine"), ansichtMerken: ansichtMerken, ansicht: () => ({on: MINE.on, page: MINE.page, map: Object.assign({}, MINE.map), local: MINE.local, ready: MINE.ready})};
})();
</script>"""


# the manual (HELP_PAGE of 540): one paragraph in «Tipps & Tricks», German and English
for _a, _b in (('<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>',
                "<p><b>▴ Kopf einklappen und Bedienleiste:</b> Die Reiterzeile und die Statuszeile oben klappst du je mit dem kleinen Pfeil "
                "▴ ein und mit dem Griff ▾ wieder aus. Jedes Gerät merkt sich das selbst. Ist die Statuszeile eingeklappt und gibt es einen "
                "Alarm, einen Fehler oder zu wenige Bilder pro Sekunde, zeigt der Griff einen roten Punkt und eine Kurzinfo. Unter den Reitern "
                "steht auf jeder Seite dieselbe Leiste: links Einfach / Experte, rechts das Menü «Darstellung» mit Symbole farbig / schlicht und "
                "Alle zuklappen · Meine Ansicht · Nur Gruppen · Alle aufklappen. Was auf einer Seite nichts bewirkt, ist grau. Auf dem Handy "
                "stehen die Status-Chips in einer Zeile: Schutz-Zustand, das Wichtigste und der Akku – antippen zeigt alle Werte.</p>"),
               ('<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>',
                "<p><b>▴ Fold the header and the bar:</b> fold the tabs and the status line at the top one by one with the small arrow ▴ "
                "and open them again with the grip ▾. Every device remembers it by itself. With the status line folded, an alarm, an error "
                "or too few pictures per second show a red dot and a short note on the grip. Under the tabs every page has the same bar: "
                "Simple / Expert on the left, on the right the menu «Display» with symbols coloured / plain and Collapse all · My view · "
                "Groups only · Expand all. What does nothing on a page is grey. On a phone the status chips are one line: the protection "
                "state, the most important thing and the battery - a tap shows all values.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


_render_page_before_mwb = render_page


# wraps: render_page
def render_page(page, active):
    """+ 639o: the header folds and the bar under the tabs on every page with tabs (not on guest / kiosk pages)"""
    out = _render_page_before_mwb(page, active)
    if '<nav class="nav">' not in out or "<header" not in out:
        return out
    out = out.replace("</head>", MWB_CSS + "</head>", 1)
    i = out.rfind("</body>")
    tag = ("<script>window.MWB_SEITE=" + json.dumps(re.sub(r"[^a-z0-9_-]", "-", str(active or "").lower())[:40]) + ";window.MWB_TX=" + json.dumps(mwb_tx(), ensure_ascii=False).replace("</", "<\\/") + ";</script>" + MWB_JS)
    return out[:i] + tag + out[i:] if i >= 0 else out + tag


def _mwb_selftest():
    p = render_page("<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>", "live")
    assert p.count('id="mwb-css"') == 1 and "window.MWB_TX=" in p and p.count("window.MWB)") == 1, "639o: bar missing / twice"
    assert "mwbar" not in render_page("<html><head></head><body><main></main></body></html>", "guest"), "639o: bar on a page without tabs"
    tx = mwb_tx()
    for L in ("de", "fr", "it", "rm"):
        assert all(tx[L].get(k) for k in _HX_MWB), "639o: text missing in " + L
    assert {"mw-hdr-tabs", "mw-hdr-chips", "mw-hdr-sum"} <= WEB_UI_LOCAL, "639o: header folds must stay per device"
    for k in ('id = "mwb-view"', 'id = "mwb-vpop"', '"groups", "Groups only"', 'SUM.id = "mwb-sum"', "mw-hdr-sum"):
        assert k in MWB_JS, "639o (Klar): menu «Display» / status line: " + k


SELFTEST_EXTRA.append(("Header folds and bar (639o)", _mwb_selftest))
