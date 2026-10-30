#@ MoveEye – Teil 543: Web: auf der Seite Simulator in der Karte «Spiel» – «Mensch gegen KI» (Start, Stand, Ergebnis) und «Online über das WLAN hinaus» (Einladungslink mit QR-Code, Ablauf, Zurückziehen, Protokoll). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
LOCK_DENY_PATHS.add("/api/game_invite")         # operator mode (390): no new invitations to the outside
# wraps: DEMO_BLOCK
DEMO_BLOCK = tuple(DEMO_BLOCK) + ("/api/game_invite", "/api/game_compare")

GONL_DE = {"Human vs AI": "Mensch gegen KI", "online-note": "Freunde spielen von zu Hause mit: ein Link mit Ablaufzeit. Er öffnet nur das Spiel (kein Kamerabild, keine Einstellungen) und gilt nur, solange er nicht abgelaufen oder zurückgezogen ist.",
           "cmp-note": "Dieselbe Runde zweimal: zuerst bewacht ein Mensch (Wächter am Handy oder PC, sonst der Bot-Wächter), dann die echte Erkennung von MoveEye – mit denselben Wegen und denselben Kamerabildern. Mit Bots läuft es von selbst.",
           "Online beyond the WLAN": "Online über das WLAN hinaus", "Bots": "Bots", "Duration": "Dauer", "Start both rounds": "Beide Runden starten", "Stop the comparison": "Vergleich abbrechen",
           "Round 1 of 2: a person guards": "Runde 1 von 2: ein Mensch bewacht", "Round 2 of 2: MoveEye guards the same round": "Runde 2 von 2: MoveEye bewacht dieselbe Runde",
           "Short break between the rounds": "Kurze Pause zwischen den Runden", "time left": "noch", "MoveEye is not connected to the simulator game": "MoveEye ist nicht mit dem Spiel des Simulators verbunden",
           "Learning pictures": "Lernbilder", "Test bench ways": "Prüfstand-Wege", "Human saw, MoveEye missed": "Mensch sah, MoveEye nicht", "False alarms": "Fehlalarme",
           "faster": "schneller", "nobody caught him": "keiner hat ihn erwischt", "same speed": "gleich schnell", "Human": "Mensch", "Bot guard": "Bot-Wächter",
           "Saved ways instead of free bots": "Gespeicherte Schleichwege statt freier Bots", "New invitation": "Neue Einladung", "valid for": "gültig für", "players at most": "Spieler höchstens",
           "Name (optional)": "Name (freiwillig)", "Make the invitation": "Einladung erstellen", "Revoke": "Zurückziehen", "Revoke all": "Alle zurückziehen", "Copy": "Kopieren", "copied": "kopiert",
           "expired": "abgelaufen", "revoked": "zurückgezogen", "players": "Spieler", "valid for another": "noch gültig", "Game invitation": "Spiel-Einladung", "Protocol": "Protokoll",
           "local-warn": "Dieser Link geht nur im eigenen Netz. Für Freunde zu Hause: Tailscale einrichten (Funnel für Gäste ohne Tailscale) oder unter Einstellungen → Meldungen die «Adresse dieser Seite» eintragen.",
           "The game is open - guests can join": "Das Spiel ist offen – Gäste können beitreten", "through the tunnel": "über den Tunnel",
           "the game is not open in the simulator": "das Spiel ist im Simulator nicht offen", "simulator not reachable": "Simulator nicht erreichbar",
           "Only the game: the guest sees no camera picture and no settings. Whoever has the link can play until it expires.": "Nur das Spiel: der Gast sieht kein Kamerabild und keine Einstellungen. Wer den Link hat, kann bis zum Ablauf mitspielen.",
           "Online game over Tailscale Funnel": "Online-Spiel über Tailscale Funnel", "Switch the funnel on": "Funnel einschalten",
           "funnel-note": "Macht nur das Spiel (/game/…) über Tailscale Funnel im Internet erreichbar – für Freunde ohne Tailscale. Alles andere von MoveEye bleibt privat. Geht von selbst aus, wenn die letzte Einladung abläuft oder zurückgezogen wird, spätestens nach der gewählten Zeit und beim Neustart.",
           "local-warn-funnel": "Dieser Link geht nur im eigenen Netz. Für Freunde ohne Tailscale: Funnel einschalten – dann ist nur das Spiel öffentlich.",
           "switches off at the latest after": "geht spätestens aus nach", "Funnel on": "Funnel an – öffentlich", "Funnel off": "Funnel aus",
           "Make an invitation now - without one the funnel switches off after 15 minutes.": "Jetzt eine Einladung erstellen – ohne Einladung geht der Funnel nach 15 Minuten wieder aus.",
           "Only the administrator can switch the funnel on.": "Nur der Administrator kann den Funnel einschalten.", "Only for the administrator": "Nur für den Administrator",
           "Who caught more?": "Wer hat mehr erwischt?", "wins": "gewinnt", "Draw": "Gleichstand", "h": "h", "no invitation yet": "noch keine Einladung"}

GONL_JS = r"""<script>
Object.assign(I18N.de, /*GONLDE*/{});
(function () {
  const C = document.getElementById("g-cmp"), V = document.getElementById("g-inv"); if (!C || !V) return;
  const L = () => "lang=" + encodeURIComponent(LANG || "");
  const fmtS = s => { s = Math.max(0, s | 0); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60); return h ? h + ":" + String(m).padStart(2, "0") + " " + t("h") : (m || 1) + " " + t("min"); };
  let CK = "", VK = "", busyC = false;
  const head = (box, ic, ttl, note) => { const d = el("details", "sub"); d.open = true; const s = el("summary", "", ic + " " + t(ttl)); d.appendChild(s); d.appendChild(el("div", "mut", t(note))); const b = el("div", ""); d.appendChild(b); box.appendChild(d); return b; };
  // ---- «Mensch gegen KI» ----
  let cb = null;
  const paintC = j => { const k = JSON.stringify(j); if (k === CK) return; CK = k; if (!cb) cb = head(C, "⚖", "Human vs AI", "cmp-note"); cb.textContent = "";
    const S = j || {};
    if (S.ok === false && S.error) cb.appendChild(el("div", "", "⚠ " + S.error));
    const run = ["r1", "pause", "r2"].includes(S.state);
    if (run) { cb.appendChild(el("div", "", "⏳ " + t(S.state === "r1" ? "Round 1 of 2: a person guards" : S.state === "r2" ? "Round 2 of 2: MoveEye guards the same round" : "Short break between the rounds") + " · " + t("time left") + " " + fmtS(S.left_s)));
      if (S.info) cb.appendChild(el("div", "mut", S.info)); }
    if (!S.mw && !run) cb.appendChild(el("div", "mut", "⚠ " + t("MoveEye is not connected to the simulator game")));
    const R = S.result || {};
    if (R.title && !run) { const b = el("div", ""); b.style.cssText = "font-size:18px;font-weight:700;margin:6px 0 2px";
      b.textContent = "⚖ " + t("Who caught more?") + " " + (R.guard_human ? t("Human") : t("Bot guard")) + " " + R.human + " · MoveEye " + R.mw; cb.appendChild(b);
      cb.appendChild(el("div", "", R.human === R.mw ? t("Draw") : ((R.human > R.mw ? (R.guard_human ? t("Human") : t("Bot guard")) : "MoveEye") + " " + t("wins"))));
      const ul = el("ul", ""); ul.style.cssText = "margin:6px 0;padding-left:18px;font-size:14px";
      (R.per || []).forEach(p => { const li = el("li", ""); const dot = el("span", "", "● "); dot.style.color = p.c; li.appendChild(dot);
        const who = p.faster === "human" ? (R.guard_human ? t("Human") : t("Bot guard")) + " " + t("faster") : p.faster === "mw" ? "MoveEye " + t("faster") : p.faster === "same" ? t("same speed") : t("nobody caught him");
        li.appendChild(document.createTextNode(p.n + ": " + p.human + " · " + p.mw + " – " + who + (p.human > 0 || p.mw > 0 ? " (" + (p.human > 0 ? p.rt_human + " s" : "–") + " / " + (p.mw > 0 ? p.rt_mw + " s" : "–") + ")" : ""))); ul.appendChild(li); });
      cb.appendChild(ul);
      cb.appendChild(el("div", "mut", t("False alarms") + ": " + (R.guard_human ? t("Human") : t("Bot guard")) + " " + R.false_human + " · MoveEye " + R.false_mw));
      if (R.missed) cb.appendChild(el("div", "", "🧠 " + t("Human saw, MoveEye missed") + ": " + R.missed + " → " + R.pics + " " + t("Learning pictures") + ", " + R.ways + " " + t("Test bench ways"))); }
    const r = el("div", "btns"); r.style.cssText = "align-items:center;flex-wrap:wrap;margin-top:6px";
    const sb = document.createElement("select"); [1, 2, 3].forEach(n => { const o = el("option", "", t("Bots") + ": " + n); o.value = n; sb.appendChild(o); }); sb.value = String(Math.max(1, Math.min(3, S.bots || 2)));
    const sm = document.createElement("select"); [2, 3, 5].forEach(n => { const o = el("option", "", n + " " + t("min")); o.value = n; sm.appendChild(o); }); sm.value = String([2, 3, 5].includes(S.minutes) ? S.minutes : 3);
    sb.setAttribute("aria-label", t("Bots")); sm.setAttribute("aria-label", t("Duration")); sb.style.width = sm.style.width = "auto";
    const wl = el("label", "mut"); const wc = document.createElement("input"); wc.type = "checkbox"; wc.id = "gc-ways"; wl.append(wc, document.createTextNode(" " + t("Saved ways instead of free bots")));
    wl.style.fontSize = "13px"; if (!S.ways_n) wl.hidden = true;
    const b1 = el("button", "", "▶ " + t("Start both rounds")); b1.type = "button"; b1.disabled = run || !S.mw;
    b1.onclick = async () => { b1.disabled = true; busyC = true; const q = await post("/api/game_compare?" + L(), {op: "start", bots: +sb.value, minutes: +sm.value, source: wc.checked ? "ways" : "rec", lang: LANG}); busyC = false; CK = ""; paintC(q); };
    const b2 = el("button", "sec", t("Stop the comparison")); b2.type = "button"; b2.hidden = !run; b2.onclick = async () => { CK = ""; paintC(await post("/api/game_compare?" + L(), {op: "stop", lang: LANG})); };
    if (!run) r.append(sb, sm); r.append(b1, b2); cb.appendChild(r); if (!run) cb.appendChild(wl); };
  // ---- 556: «Online-Spiel über Tailscale Funnel» (only the game public; only the administrator switches) ----
  const fErr = E => { const d = el("div", ""); d.style.margin = "4px 0"; d.appendChild(el("div", "err", "⚠ " + E.msg));
    (E.steps || []).forEach(x => d.appendChild(el("div", "", "• " + x)));
    if (E.cmd) { const c = el("pre", "", E.cmd); c.style.cssText = "white-space:pre-wrap;word-break:break-all;background:var(--field,#0c121a);border:1px solid var(--line);padding:6px 8px;border-radius:8px;font-size:12px;margin:4px 0;user-select:all"; d.appendChild(c); }
    (E.links || []).forEach(l => { const a = el("a", "", "🔗 " + l.t); a.href = l.u; a.target = "_blank"; a.rel = "noopener noreferrer"; a.style.cssText = "display:block;margin:2px 0;font-size:13px;color:var(--acc)"; d.appendChild(a); });
    return d; };
  const fSet = async b => { b.lang = LANG; await post("/api/game_funnel?" + L(), b); VK = "";
    try { paintV(await (await fetch("/api/game_invite?" + L(), {cache: "no-store"})).json()); } catch (e) {} };
  const paintF = (box, S) => { const F = S.funnel; if (!F) { if (!S.public) box.appendChild(el("div", "mut", "⚠ " + t("local-warn"))); return; }
    const w = el("div", ""); w.id = "g-funnel"; w.style.cssText = "border:1px solid " + (F.on ? "var(--acc)" : "var(--line)") + ";border-radius:10px;padding:8px;margin:6px 0";
    if (!S.public && !F.on) { const r = el("div", "mut", "⚠ " + t(F.avail ? "local-warn-funnel" : "local-warn"));
      if (F.avail && F.can) { const b = el("button", "", "🌍 " + t("Switch the funnel on")); b.type = "button"; b.style.cssText = "display:block;margin-top:6px";
        b.onclick = () => { b.disabled = true; fSet({action: "on", hours: +(F.hours || 6)}); }; r.appendChild(b); }
      w.appendChild(r); }
    const lab = el("label", "opt"), cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw"; cb.id = "g-funnel-sw"; cb.checked = !!F.on; cb.disabled = !F.can;
    lab.append(el("span", "", "🌍 " + t("Online game over Tailscale Funnel")), cb); if (!F.can) { lab.style.opacity = ".5"; lab.title = t("Only for the administrator"); }
    const hs = document.createElement("select"); hs.setAttribute("aria-label", t("switches off at the latest after")); hs.style.width = "auto"; hs.disabled = !F.can;
    (F.choices || [1, 2, 3, 6, 12, 24]).forEach(h => { const o = el("option", "", t("switches off at the latest after") + " " + h + " " + t("h")); o.value = h; hs.appendChild(o); }); hs.value = String(F.hours || 6);
    hs.onchange = () => fSet({action: F.on ? "on" : "hours", hours: +hs.value});
    cb.onchange = () => { cb.disabled = true; fSet({action: cb.checked ? "on" : "off", hours: +hs.value}); };
    w.appendChild(lab); w.appendChild(el("div", "mut", t("funnel-note")));
    const hr = el("div", "btns"); hr.style.cssText = "align-items:center;flex-wrap:wrap;margin-top:6px"; hr.appendChild(hs); w.appendChild(hr);
    const st = el("div", "", F.on ? "🌍 " + t("Funnel on") + " · " + t("time left") + " " + fmtS(F.left_s) : "⚪ " + t("Funnel off") + (F.why_off ? " (" + F.why_off + ")" : ""));
    st.style.marginTop = "6px"; w.appendChild(st);
    if (F.on) { const u = el("div", "mut", F.url); u.style.cssText = "word-break:break-all;font-size:12px"; w.appendChild(u); }
    if (F.on && F.grace_s) w.appendChild(el("div", "mut", "⏳ " + t("Make an invitation now - without one the funnel switches off after 15 minutes.")));
    if (!F.can) w.appendChild(el("div", "mut", "🔒 " + t("Only the administrator can switch the funnel on.")));
    const E = F.err || F.need; if (E) w.appendChild(fErr(E));
    box.appendChild(w); };
  // ---- invitations ----
  let vb = null, sel = {h: 3, p: 6};
  const paintV = j => { const k = JSON.stringify(j); if (k === VK) return; VK = k; if (!vb) vb = head(V, "🌐", "Online beyond the WLAN", "online-note"); vb.textContent = "";
    const S = j || {};
    if (S.ok === false) { vb.appendChild(el("div", "", "⚠ " + (S.error || "?"))); return; }
    vb.appendChild(el("div", S.game_open ? "" : "mut", S.game_open ? "🟢 " + t("The game is open - guests can join") + (S.tunnel ? " (" + t("through the tunnel") + ")" : "") : "⚪ " + (S.why || t("the game is not open in the simulator"))));
    paintF(vb, S);
    const act = (S.invites || []).filter(x => x.active), old = (S.invites || []).filter(x => !x.active);
    if (!act.length) vb.appendChild(el("div", "mut", t("no invitation yet")));
    act.forEach(x => { const row = el("div", ""); row.style.cssText = "border:1px solid var(--line);border-radius:10px;padding:8px;margin:6px 0";
      row.appendChild(el("div", "", "🎟 " + (x.name || t("Game invitation")) + " · " + t("valid for another") + " " + fmtS(x.left_s) + " · " + x.players + "/" + x.max + " " + t("players")));
      const u = el("div", "mut", x.url); u.style.cssText = "word-break:break-all;font-size:12px;user-select:all"; row.appendChild(u);
      const br = el("div", "btns");
      const cp = el("button", "sec", t("Copy")); cp.type = "button"; cp.onclick = () => { try { navigator.clipboard.writeText(x.url); cp.textContent = "✓ " + t("copied"); } catch (e) {} };
      const rv = el("button", "sec", t("Revoke")); rv.type = "button"; rv.onclick = async () => { VK = ""; paintV(await post("/api/game_invite?" + L(), {action: "revoke", id: x.id, lang: LANG})); };
      br.append(cp, rv); if (window.qrBtn) br.appendChild(qrBtn(x.url, t("Game invitation"), {secret: true, note: t("Only the game: the guest sees no camera picture and no settings. Whoever has the link can play until it expires.")}));
      row.appendChild(br); vb.appendChild(row); });
    const f = el("div", "btns"); f.style.cssText = "align-items:center;flex-wrap:wrap;margin-top:6px";
    const sh = document.createElement("select"); (S.hours || [1, 3, 6, 12, 24]).forEach(h => { const o = el("option", "", t("valid for") + " " + h + " " + t("h")); o.value = h; sh.appendChild(o); }); sh.value = String(sel.h);
    const sp = document.createElement("select"); [2, 4, 6, 8, 12].forEach(n => { const o = el("option", "", n + " " + t("players at most")); o.value = n; sp.appendChild(o); }); sp.value = String(sel.p);
    sh.onchange = () => sel.h = +sh.value; sp.onchange = () => sel.p = +sp.value; sh.style.width = sp.style.width = "auto";
    const nm = document.createElement("input"); nm.type = "text"; nm.maxLength = 30; nm.placeholder = t("Name (optional)"); nm.style.cssText = "flex:1 1 140px;min-width:0;width:auto";
    const mk = el("button", "", "➕ " + t("Make the invitation")); mk.type = "button";
    mk.onclick = async () => { mk.disabled = true; const q = await post("/api/game_invite?" + L(), {action: "create", hours: +sh.value, players: +sp.value, name: nm.value, lang: LANG}); VK = ""; paintV(q);
      if (q && q.new && window.qrShow) qrShow(q.new, t("Game invitation"), {secret: true, note: t("Only the game: the guest sees no camera picture and no settings. Whoever has the link can play until it expires.")}); };
    vb.appendChild(el("div", "", "")).appendChild(el("b", "", t("New invitation")));
    f.append(sh, sp, nm, mk); vb.appendChild(f);
    if (act.length > 1) { const ra = el("button", "sec", t("Revoke all")); ra.type = "button"; ra.onclick = async () => { VK = ""; paintV(await post("/api/game_invite?" + L(), {action: "revoke", all: true, lang: LANG})); }; vb.appendChild(ra); }
    if (old.length) vb.appendChild(el("div", "mut", old.map(x => "🎟 " + (x.name || x.id) + ": " + t(x.revoked ? "revoked" : "expired")).join(" · ")));
    if ((S.log || []).length) { const d = el("details", "sub"); d.appendChild(el("summary", "", t("Protocol")));
      (S.log || []).forEach(e => d.appendChild(el("div", "mut", new Date(e.t * 1000).toLocaleTimeString() + " · " + e.ip + " · " + e.what))); vb.appendChild(d); } };
  const poll = async () => { const g = document.getElementById("c-game");
    if (g && !g.hidden && !document.hidden) {
      if (!busyC) { try { paintC(await (await fetch("/api/game_compare?" + L(), {cache: "no-store"})).json()); } catch (e) {} }
      try { paintV(await (await fetch("/api/game_invite?" + L(), {cache: "no-store"})).json()); } catch (e) {} }
    setTimeout(poll, 4000); };
  setTimeout(poll, 800);
})();
</script>"""
GONL_JS = GONL_JS.replace("/*GONLDE*/{}", json.dumps(GONL_DE, ensure_ascii=False))
SIM_PAGE = SIM_PAGE.replace('<div id="g-more"></div>', '<div id="g-more"></div><div id="g-cmp"></div><div id="g-inv"></div>', 1)
SIM_PAGE = SIM_PAGE.replace("</body>", GONL_JS + "</body>", 1)
