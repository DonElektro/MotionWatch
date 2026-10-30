#@ MoveEye – Teil 531a: Web-Seite «Push-Nachrichten» als Karten (Kopf · Wohin · Was · Wann · Erweitert) – baut die Felder des Abschnitts Benachrichtigungen um (530 ruft pushPanel). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): the push section like the slim cards of the simulator panel (card «Spiel»: name, state,
# the main buttons; details on demand). The generic rows of the section (530 build) are MOVED into the cards - their
# handlers and the ctrl registry stay the same, nothing is built twice. Logic + /api/push: 579a; window: 571a; texts: 639a.
#   Kopf       «Push senden», status line («2 Kanäle · Test ✓»), «Alle testen» (results below)
#   Wohin      a card per channel (name, state, ▶ Test, switch; tap = its fields). Unused ones behind «+ Kanal hinzufügen».
#              SMS: the section «SMS (LTE-Stick)» moves into its card (regroup hook below).
#   Was        level (segment), pre-alarm, pictures (segment)
#   Wann       the two pauses, quiet hours (time windows, «Personen trotzdem melden»), night time of the night report
#   Erweitert  keyword (one field), buttons, symbols, page address, info messages, the message texts (section «Nachrichten-
#              texte» moves here, one row per message), iPhone shortcuts (#scbox of 530)
#   Moved out  «Alarmton im Browser» → the bell 🔔 at the top (a switch in its panel); «Doppelte Bestätigung» → Erkennung,
#              device name → System (both server side in 579a).
# Fields: «Löschen» is a small ✕ inside the field (secret fields: after a confirmation).
# ----------------------------------------------------------------------------

PUSH_CARDS_JS = r"""
<style id="px-css">
.px-h{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--mut);font-weight:700;margin:16px 0 6px}
.px-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:2px}
.px-head .px-st{flex:1 1 140px;min-width:0;font-size:13px;color:var(--mut)}
.px-head .px-st.ok{color:var(--grn)}
.px-res{white-space:pre-line;font-size:12.5px;margin-top:4px}
.pxc{border:1px solid var(--line);border-radius:12px;background:var(--field);margin:6px 0;overflow:hidden}
.pxc-hd{display:flex;align-items:center;gap:8px;padding:7px 8px 7px 10px;cursor:pointer;min-height:40px}
.pxc-hd .pxic{width:22px;text-align:center;flex:none}
.pxc-hd .pxnm{flex:1;min-width:0;font-size:14px;line-height:1.2}
.pxc-hd .pxnm small{display:block;font-size:12px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pxc-hd .pxnm small.ok{color:var(--grn)}.pxc-hd .pxnm small.warn{color:var(--yel)}
.pxc-hd .pxar{color:var(--mut);font-size:12px;flex:none;width:12px}
.pxc.open .pxc-hd .pxar{transform:rotate(90deg)}
.pxc-hd button.pxtest{padding:4px 9px;font-size:12px;flex:none}
.pxc-b{padding:2px 10px 10px;border-top:1px solid var(--line)}
.pxc-b .sl,.pxc-b .row{margin-top:6px}
.pxc-b .auxbox{margin-top:8px}
.px-note{font-size:12px;color:var(--mut);margin-top:6px}
.px-add{margin-top:6px}.px-addm{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.px-seg{display:flex;width:100%;margin-top:4px}.px-seg button{flex:1;padding:7px 4px;font-size:12.5px;white-space:nowrap}
.px-lbl{font-size:14px;margin-top:8px}
.pxf{position:relative;display:block;margin-top:4px}
.pxf>input{width:100%!important;margin-top:0!important;padding-right:34px!important;box-sizing:border-box}
.pxx{position:absolute;right:3px;top:50%;transform:translateY(-50%);width:28px;height:28px;padding:0!important;border-radius:7px;font-size:13px;line-height:1;
  background:transparent!important;border:0!important;color:var(--mut)}
.pxx:hover{color:var(--txt);background:var(--btn2)!important}
.px-q{margin-top:6px}.px-qw{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 0;border-bottom:1px dashed var(--line)}
.px-qw input[type=time]{width:96px;padding:4px 6px}
.px-days{display:flex;gap:2px;flex-wrap:wrap}.px-days button{padding:3px 6px;font-size:11.5px;min-width:30px}
.px-days button.on{background:var(--acc);color:#fff;border-color:transparent}
details.px-adv{margin-top:14px;border-top:1px solid var(--line);padding-top:4px}
details.px-adv>summary{cursor:pointer;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--mut);font-weight:700;padding:8px 0;list-style:none}
details.px-adv>summary::-webkit-details-marker{display:none}
details.px-adv>summary::before{content:"▸ ";}details.px-adv[open]>summary::before{content:"▾ ";}
.px-msg .msgcard{margin-top:6px;padding:0;background:transparent}
.px-msg .msgcard>summary{padding:8px 10px;cursor:pointer}
.px-msg .msgcard[open]{padding-bottom:8px}.px-msg .msgcard>:not(summary){margin-left:10px;margin-right:10px}
.px-hidden{display:none!important}
.sndpop .px-bell{border-top:1px solid var(--line);margin-top:8px;padding-top:6px}
</style>
<script>
(function () {
  try { const D = /*PXDE*/{}; Object.keys(D).forEach(k => { if (!(k in I18N.de)) I18N.de[k] = D[k]; }); } catch (e) {}   // 639a; existing texts stay
  const CH = {
    ntfy: {ic: "📲", nm: "ntfy", keys: ["notify_url"]},
    webpush: {ic: "🌐", nm: "Web push (this device)", keys: []},
    telegram: {ic: "✈️", nm: "Telegram", keys: ["telegram_token", "telegram_chat"]},
    pushover: {ic: "🔔", nm: "Pushover", keys: ["pushover_user", "pushover_token", "pushover_emergency"]},
    email: {ic: "✉️", nm: "E-mail", keys: ["email_to"], adv: ["email_host", "email_port", "email_user", "email_password", "email_events"]},
    webhook: {ic: "🔗", nm: "Webhook", keys: ["notify_url"]},
    sms: {ic: "📱", nm: "SMS", keys: []}};
  const ORDER = ["ntfy", "webpush", "telegram", "pushover", "email", "webhook", "sms"];
  const MAIN = ["ntfy", "telegram", "webhook"];
  const DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
  const X = {P: null, root: null, cards: {}, added: new Set(), urlRow: null, editQ: 0, adv: null, msg: null};
  const api = (b) => post("/api/push", Object.assign({lang: LANG}, b || {}));
  const rowOf = (d, k) => d.querySelector('[data-key="' + k + '"]');

  // a text field: «Löschen» as a small ✕ inside (secret: after a confirmation)
  function xField(wrap) {
    if (!wrap || wrap.dataset.pxx) return; wrap.dataset.pxx = "1";
    const inp = wrap.querySelector("input[type=text],input[type=password]"); if (!inp) return;
    const f = el("span", "pxf"); inp.parentNode.insertBefore(f, inp); f.appendChild(inp);
    const clr = [...wrap.querySelectorAll(":scope > button.sec")].find(b => b.textContent === t("Clear"));
    const x = el("button", "pxx", "✕"); x.type = "button"; x.title = t("Clear"); x.setAttribute("aria-label", t("Clear"));
    if (clr) { clr.classList.add("px-hidden");
      x.onclick = () => { if (!confirm(t("Clear the saved value? It cannot be shown again."))) return; clr.click(); inp.value = ""; }; }
    else x.onclick = () => { if (!inp.value) return; inp.value = ""; inp.dispatchEvent(new Event("change")); };
    f.appendChild(x);
  }
  function seg(choices, cur, onpick) {
    const s = el("div", "seg lseg px-seg");
    choices.forEach(([v, lab]) => { const b = el("button", v === cur ? "sel-auto" : "", t(lab)); b.type = "button"; b.dataset.v = v;
      b.onclick = () => { [...s.children].forEach(x => x.className = x === b ? "sel-auto" : ""); onpick(v); }; s.appendChild(b); });
    s.set = v => [...s.children].forEach(x => x.className = x.dataset.v === v ? "sel-auto" : "");
    return s;
  }
  function hide(n) { if (n) n.classList.add("px-hidden"); }

  function card(id, d) {
    const C = CH[id], c = el("div", "pxc"); c.dataset.ch = id;
    const hd = el("div", "pxc-hd"), ar = el("span", "pxar", "▸"), ic = el("span", "pxic", C.ic), nm = el("span", "pxnm"), st = el("small", "", "");
    nm.append(document.createTextNode(t(C.nm)), st);
    const tb = el("button", "sec pxtest", "▶ " + t("Test")); tb.type = "button"; tb.title = t("Send a test message over this channel only");
    const sw = el("input"); sw.type = "checkbox"; sw.className = "sw"; sw.title = t("on / off");
    hd.append(ar, ic, nm, tb, sw);
    const body = el("div", "pxc-b"); body.hidden = true;
    hd.onclick = e => { if (e.target === sw || e.target === tb) return; body.hidden = !body.hidden; c.classList.toggle("open", !body.hidden); };
    sw.onchange = async () => { const r = await api({action: "channel", ch: id, on: sw.checked});
      if (r && r.ok === false) toast("⚠ " + (r.error || "error")); paint(r && r.channels ? r : null);
      if (sw.checked && body.children.length > 1) { body.hidden = false; c.classList.add("open"); } };
    tb.onclick = async () => { tb.disabled = true; st.textContent = t("testing …"); st.className = "";
      const r = await api({action: "test", ch: id}); tb.disabled = false;
      const x = r && r.results && r.results[0];
      if (!r || r.ok === false) toast("⚠ " + ((r && r.error) || "error"));
      else if (x) toast((x.ok ? "✓ " : "✗ ") + x.ch + " – " + x.msg);
      paint(r && r.channels ? r : null); };
    C.keys.forEach(k => { const r_ = k === "notify_url" ? null : rowOf(d, k); if (r_) body.appendChild(r_); });
    if (C.adv) { const a = el("details", "adv sblk"); a.appendChild(el("summary", "", t("Advanced")));
      C.adv.forEach(k => { const r_ = rowOf(d, k); if (r_) a.appendChild(r_); }); if (a.children.length > 1) body.appendChild(a); }
    if (MAIN.includes(id)) body.appendChild(el("div", "px-note", t("Only one of ntfy · Telegram · Webhook (the main channel, with repeats and the outbox).")));
    if (id === "webpush") { const wp = d.querySelector("#wp-box"); if (wp) body.appendChild(wp); }
    if (id === "email") body.appendChild(el("div", "px-note", t("The iPhone can start a shortcut from an e-mail (see Advanced → iPhone shortcuts).")));
    c.append(hd, body); X.cards[id] = {c, sw, st, body, tb};
    return c;
  }

  function quietBox(d) {
    const box = el("div", "px-q"), list = el("div");
    const add = el("button", "sec", "+ " + t("Time window")); add.type = "button";
    const pre = el("button", "sec", "🏠 " + t("Day at home")); pre.type = "button"; pre.title = t("Weekdays 08:00 until the night time of the night report");
    const bt = el("div", "btns"); bt.append(add, pre);
    const info = el("div", "px-note");
    box.append(list, bt, info);
    let W = [];
    const save = () => { X.editQ = Date.now(); api({action: "quiet", windows: W}).then(r => { if (r && r.ok) { toast(t("Saved")); paint(r); } }); };
    const draw = () => { list.textContent = "";
      W.forEach((w, i) => { const r = el("div", "px-qw");
        const a = el("input"); a.type = "time"; a.value = w.from; const b = el("input"); b.type = "time"; b.value = w.to;
        a.onchange = () => { w.from = a.value; save(); }; b.onchange = () => { w.to = b.value; save(); };
        const ds = el("div", "px-days");
        DAYS.forEach((dn, k) => { const x = el("button", "sec" + (w.days.includes(k) ? " on" : ""), t(dn)); x.type = "button";
          x.onclick = () => { w.days = w.days.includes(k) ? w.days.filter(z => z !== k) : w.days.concat([k]).sort(); if (!w.days.length) w.days = [k]; draw(); save(); };
          ds.appendChild(x); });
        const del = el("button", "sec pxx", "✕"); del.type = "button"; del.style.position = "static"; del.style.transform = "none"; del.title = t("Remove");
        del.onclick = () => { if (W.length <= 1) { toast(t("At least one time window - switch the quiet hours off instead.")); return; } W.splice(i, 1); draw(); save(); };
        r.append(a, el("span", "mut", "–"), b, ds, del); list.appendChild(r); });
      add.hidden = W.length >= 4; };
    add.onclick = () => { W.push({from: "12:00", to: "14:00", days: [0, 1, 2, 3, 4, 5, 6]}); draw(); save(); };
    pre.onclick = () => { const nf = (X.P && X.P.night_from) || 20; W = [{from: "08:00", to: String(nf).padStart(2, "0") + ":00", days: [0, 1, 2, 3, 4]}]; draw(); save(); };
    box.fill = P => { if (Date.now() - X.editQ > 4000 && !box.contains(document.activeElement)) { W = JSON.parse(JSON.stringify(P.quiet.windows || [])); draw(); }
      info.textContent = (P.quiet.now ? "🌙 " + t("Quiet hours now - alarms are only logged") + " · " : "") + t("Clock") + ": " + P.quiet.clock + (P.quiet.sim ? " (" + t("sim time") + ")" : "")
        + " · " + t("Night time from") + " " + P.night_from + ":00 (" + t("night report") + ")"; };
    return box;
  }

  window.pushPanel = function (d, sec) {
    if (d.querySelector(".px")) return;
    const root = el("div", "px"); X.root = root;
    // the generic buttons of 530 (test, test all) - replaced by «▶ Test» per card and «Alle testen» on top
    [...d.children].filter(c => c.tagName === "BUTTON").forEach(b => { const nx = b.nextElementSibling; b.remove(); if (nx && nx.tagName === "DIV" && nx.classList.contains("mut") && !nx.dataset.key && !nx.id) nx.remove(); });
    // ---- Kopf ----
    const on = rowOf(d, "notify_on"); if (on) root.appendChild(on);
    const head = el("div", "px-head"), st = el("div", "px-st", ""), all = el("button", "sec", "🧪 " + t("Test all")); all.type = "button";
    const res = el("div", "px-res mut"); head.append(st, all); root.append(head, res); X.st = st;
    all.onclick = async () => { all.disabled = true; res.textContent = t("testing …");
      const r = await api({action: "test", ch: "all"}); all.disabled = false;
      res.textContent = !r || r.ok === false ? "⚠ " + ((r && r.error) || "error") : (r.results || []).length ? r.results.map(x => (x.ok ? "✓ " : "✗ ") + x.ch + " – " + x.msg).join("\n") : t("No channel set up.");
      paint(r && r.channels ? r : null); };
    // ---- Wohin ----
    root.appendChild(el("div", "px-h", t("Where to")));
    const cw = el("div", "px-cards"); root.appendChild(cw);
    ORDER.forEach(id => cw.appendChild(card(id, d)));
    X.urlRow = rowOf(d, "notify_url");
    const addB = el("button", "sec px-add", "+ " + t("Add channel")); addB.type = "button"; const addM = el("div", "px-addm"); addM.hidden = true;
    addB.onclick = () => { addM.hidden = !addM.hidden; }; root.append(addB, addM); X.addB = addB; X.addM = addM;
    // ---- Was ----
    root.appendChild(el("div", "px-h", t("What")));
    X.lvl = seg([["persons", "Only persons"], ["animals", "Persons + animals"], ["all", "Everything"]], "all",
      v => post("/api/text", {key: "push_level", value: v, lang: LANG}).then(r => { toast(r.ok ? t("Saved") : "⚠ " + (r.error || "error")); refreshP(); }));
    const lvW = el("div", ""); lvW.dataset.key = "push_level"; const lvL = el("div", "row"); lvL.appendChild(el("span", "", t("What is reported"))); lvW.append(lvL, X.lvl); root.appendChild(lvW);
    X.lvlNote = el("div", "px-note", ""); root.appendChild(X.lvlNote);
    hide(rowOf(d, "push_level")); const pr = rowOf(d, "notify_prealarm"); if (pr) root.appendChild(pr);
    X.pics = seg([["with", "with picture"], ["small", "small picture"], ["text", "without picture"]], "with",
      v => post("/api/text", {key: "push_pics", value: v, lang: LANG}).then(r => toast(r.ok ? t("Saved") : "⚠ " + (r.error || "error"))));
    const pW = el("div", ""); pW.dataset.key = "push_pics"; const pL = el("div", "row"); pL.appendChild(el("span", "", t("Pictures"))); pW.append(pL, X.pics); root.appendChild(pW);
    hide(rowOf(d, "push_pics"));
    // ---- Wann ----
    root.appendChild(el("div", "px-h", t("When")));
    ["notify_cooldown", "prealarm_cooldown", "quiet_on"].forEach(k => { const r_ = rowOf(d, k); if (r_) root.appendChild(r_); });
    X.q = quietBox(d); root.appendChild(X.q);
    const qp = rowOf(d, "quiet_persons"); if (qp) { X.q.insertBefore(qp, X.q.firstChild); }
    const qcb = ctrl.quiet_on && ctrl.quiet_on.input; if (qcb) { const upd = () => { X.q.hidden = !qcb.checked; }; qcb.addEventListener("change", upd); X.qUpd = upd; }
    // ---- Erweitert ----
    const adv = el("details", "px-adv"); adv.appendChild(el("summary", "", t("Advanced"))); X.adv = adv;
    const kw = el("div", "sl"); kw.dataset.key = "msg_keyword_prefix"; const kl = el("div", "row"); kl.appendChild(el("span", "", t("Keyword (empty = off)")));
    const ki = el("input"); ki.type = "text"; ki.autocomplete = "off"; ki.placeholder = "MW"; ki.maxLength = 12; ki.style.width = "100%"; ki.style.marginTop = "4px";
    ki.onchange = () => api({action: "keyword", value: ki.value}).then(r => { toast(r.ok ? t("Saved") : "⚠ " + (r.error || "error")); paint(r && r.channels ? r : null); });
    kw.append(kl, ki); adv.appendChild(kw); X.kw = ki; xField(kw);
    hide(rowOf(d, "msg_keyword_on")); hide(rowOf(d, "msg_keyword_prefix"));
    ["webpush_on", "pushover_on", "email_on"].forEach(k => hide(rowOf(d, k)));     // = the switches of the cards
    ["push_actions", "msg_icons", "public_url", "notify_network", "notify_remote"].forEach(k => { const r_ = rowOf(d, k); if (r_) adv.appendChild(r_); });
    const ba = rowOf(d, "browser_alarm"); if (ba) { hide(ba); adv.appendChild(ba); }      // moved to the bell 🔔 (below)
    X.msg = el("div", "px-msg"); adv.appendChild(X.msg);
    root.appendChild(adv);
    // anything left over of the section (a later version) stays below, nothing gets lost
    [...d.children].filter(c => c.tagName !== "SUMMARY" && c !== root && !c.classList.contains("px-hidden")).forEach(c => adv.appendChild(c));
    const sm = d.querySelector(":scope > summary"); d.insertBefore(root, sm ? sm.nextSibling : d.firstChild);
    root.querySelectorAll(".sl[data-key]").forEach(xField);
    refreshP(); setInterval(() => { if (X.root && X.root.offsetParent) refreshP(); pxMoveSc(); }, 5000);
    setTimeout(pxMoveSc, 1500);
  };
  function pxMoveSc() { const sc = document.getElementById("scbox"); if (sc && X.adv && sc.parentNode !== X.adv) X.adv.appendChild(sc); }
  async function refreshP() { try { paint(await (await fetch("/api/push?lang=" + LANG, {cache: "no-store"})).json()); } catch (e) {} }

  function paint(P) {
    if (!P || !P.channels) { refreshP(); return; }
    X.P = P;
    X.st.textContent = P.status_line; X.st.classList.toggle("ok", P.on && P.ready > 0 && (!P.test.n || P.test.ok === P.test.n));
    const hidden = [];
    P.channels.forEach(c => { const K = X.cards[c.id]; if (!K) return;
      const show = c.used || c.on || X.added.has(c.id);
      K.c.hidden = !show; if (!show) hidden.push(c.id);
      if (K.sw !== document.activeElement) K.sw.checked = c.on;
      K.st.textContent = !c.on ? t("switched off") : c.ready ? "✓ " + (c.id === "webpush" ? c.info + " " + t("devices") : (c.info || t("ready"))) : "⚠ " + t(c.id === "webpush" ? "no device yet" : "not set up yet");
      K.st.className = !c.on ? "" : c.ready ? "ok" : "warn";
      K.tb.hidden = !c.on; });
    // the shared address field: in the card of the main channel (ntfy or Webhook)
    if (X.urlRow) { const tgt = X.cards[P.main === "webhook" ? "webhook" : "ntfy"]; if (tgt && X.urlRow.parentNode !== tgt.body) tgt.body.insertBefore(X.urlRow, tgt.body.firstChild);
      const lb = X.urlRow.querySelector(".row span"); if (lb) lb.textContent = t(P.main === "webhook" ? "Webhook address (JSON POST)" : "Address (server/topic)");
      const inp = X.urlRow.querySelector("input"); if (inp && inp !== document.activeElement && inp.value !== P.url) inp.value = P.url; }
    X.addM.textContent = "";
    hidden.forEach(id => { const b = el("button", "sec", CH[id].ic + " " + t(CH[id].nm)); b.type = "button";
      b.onclick = () => { X.added.add(id); api({action: "add", ch: id}); X.addM.hidden = true; paint(P); const K = X.cards[id]; K.body.hidden = false; K.c.classList.add("open"); K.c.scrollIntoView({block: "nearest"}); };
      X.addM.appendChild(b); });
    X.addB.hidden = !hidden.length;
    X.lvl.set(P.level); X.pics.set(P.pics);
    X.lvlNote.textContent = t({persons: "Only person alarms. Warm bodies and noise are only logged.", animals: "Persons and warm bodies (thermal camera). Noise is only logged.",
      all: "Persons, warm bodies and noise (as up to now)."}[P.level] || "") + " " + t("Sabotage, theft and notes always come.");
    if (X.kw !== document.activeElement) X.kw.value = P.keyword;
    X.q.fill(P); if (X.qUpd) X.qUpd(); else X.q.hidden = !P.quiet.on;
  }

  // ---- sections that move into the push panel (before the groups are built, 530 regroup) ----
  function pxRelocate() {
    const box = document.getElementById("settings"); if (!box || !X.root) return;
    const sms = box.querySelector(':scope > details[data-view="sec:SMS (LTE stick)"]');
    if (sms && X.cards.sms) { const b = X.cards.sms.body; hide(sms.querySelector('[data-key="sms_on"]'));
      [...sms.children].filter(c => c.tagName !== "SUMMARY").forEach(c => b.appendChild(c)); sms.remove();
      b.querySelectorAll(".sl[data-key]").forEach(xField); }
    const msg = box.querySelector(':scope > details[data-view="sec:Messages"]');
    if (msg && X.msg) { X.msg.appendChild(el("div", "px-lbl", "💬 " + t("Message texts")));
      [...msg.children].filter(c => c.tagName !== "SUMMARY").forEach(c => X.msg.appendChild(c)); msg.remove();
      X.msg.querySelectorAll(".msgcard > summary > span:first-child").forEach(s => { if (!/✎/.test(s.textContent)) s.textContent += " ✎"; }); }
  }
  try { const _rg = regroup; regroup = function () { try { pxRelocate(); } catch (e) {} return _rg.apply(this, arguments); }; } catch (e) {}

  // ---- «Alarmton in geöffneten Browsern» in the panel of the bell 🔔 (moved out of the push messages) ----
  new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
    if (!(n.classList && n.classList.contains("sndpop")) || n.querySelector(".px-bell")) return;
    const c = ctrl.browser_alarm; if (!c || !c.input) return;
    const row = el("label", "row px-bell"); const cb = el("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = c.input.checked;
    cb.onchange = () => { c.input.checked = cb.checked; post("/api/set", {key: "browser_alarm", value: cb.checked}); };
    row.append(el("span", "", t("Alarms to all open browsers (MoveEye)")), cb); n.appendChild(row);
  }))).observe(document.body, {childList: true});
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", PUSH_CARDS_JS + "</body>", 1)
