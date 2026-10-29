#@ Motion Watch – Teil 510: Web: Service Worker, Kopf, Alarm, gemeinsames JavaScript. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
SW_JS = r"""// MoveEye service worker: shows web push messages (alarm) and opens the page on a tap
self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = {body: e.data ? e.data.text() : ""}; }
  e.waitUntil(self.registration.showNotification(d.title || "MoveEye", {
    body: d.body || "", icon: "/icon-192.png", badge: "/icon-192.png", tag: d.tag || "mw", renotify: true,
    requireInteraction: !!d.urgent, vibrate: d.urgent ? [300, 120, 300, 120, 300] : [120], data: {url: d.url || "/"}}));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({type: "window", includeUncontrolled: true}).then(cs => {
    for (const c of cs) { if ("focus" in c) { try { c.navigate(url); } catch (x) {} return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
"""


def i18n_loader(help_=False):
    """Runs first: for French, Italian and Romansh the page gets its translation file (cached by the browser per version)."""
    return ("<script>" + LANG_JS.replace("</", "<\\/") + "\n(function(){var l='';try{l=localStorage.getItem('mw-lang')||'';}catch(e){}if(!l)l=" + json.dumps(CFG["lang"]) + ";"
            "window.LX=function(s){var d=window.I18NX;return (d&&d[s])||'';};"
            "if(['fr','it','rm'].indexOf(l)>=0)document.write('<script src=\"/i18n/'+l+'.js?v=" + APP_VERSION + ("&h=1" if help_ else "")
            + "\"><\\/script>');})();</script>")


def i18n_js(lang, help_=False):
    """/i18n/<lang>.js: the translations of one language for the pages (Romansh: German where nothing is translated yet)."""
    L = norm_lang(lang)
    d = dict(TRX.get(L, {}))
    out = "window.I18NX=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";"
    if help_:
        out += "window.HELPX=" + json.dumps(HELP_X.get(L, ""), ensure_ascii=False) + ";"
    out += "window.MSGX=" + json.dumps(MSG_DEFAULTS.get(L, {}), ensure_ascii=False) + ";"
    return out.replace("</", "<\\/")


def render_page(page, active):
    """Fill the shared pieces into a page template."""
    page = page.replace("<head>", "<head>" + ui_seed_script() + i18n_loader(active == "help") + PWA_HEAD.replace(
        'content="MoveEye">', 'content="' + app_title(host_variant()) + '">').replace(".png\"", ".png?i=" + app_icon_id() + "\"")
        + "<script>window.MW_ICON=" + json.dumps(app_icon_id()) + ";</script>" + makeover_head()
        + ("<style>:root{--mw-icon:url(/app-icon/anim.svg?i=" + app_icon_id() + ")}</style>"
           if CFG.get("app_icon_anim", True) and app_icon_id() in APP_ICONS_ANIM else ""), 1)
    if CFG.get("header_wordmark", True):                # 2.96.11: the wordmark W6 / W1 instead of icon + name (144)
        page = re.sub(r"(<h1[^>]*>)MoveEye</h1>", lambda m_: wordmark_h1(m_) + "</h1>", page, count=1)
        page = page.replace("</svg></h1>", '</svg><span class="ver">' + APP_VERSION + "</span>"
                            + ('<span class="badge yel" style="font-size:10px;padding:1px 7px;min-height:0">DEMO</span>' if DEMO["on"] else "") + "</h1>", 1)
    page = re.sub(r"(<h1[^>]*>)MoveEye</h1>", r'\1MoveEye <span class="ver">' + APP_VERSION + "</span>"
                  + ('<span class="badge yel" style="font-size:10px;padding:1px 7px;min-height:0">DEMO</span>' if DEMO["on"] else "") + "</h1>", page, count=1)
    return (page.replace("/*BASECSS*/", BASE_CSS).replace("/*COMMON*/", COMMON_JS).replace("<!--NAV-->", nav_html(active))
            .replace("/*ALERTS*/", HEADER_JS.replace("__APPVER__", APP_VERSION).replace("__BELLY__", _BELLY) + guide_js(active) + ALERT_JS).replace("/*BTJS*/", BT_JS))


HEADER_JS = r"""
// ---- 2.95.86: back from the simulation - which settings changed there are taken over? (all pages) ----
(function simProfAsk() {
  if (window._spa) return; window._spa = true;
  const T = {de: {"Settings from the simulation": "Einstellungen aus der Simulation", "During the simulation these settings were changed. MoveEye now uses the real settings again. Take over changes for the real camera?": "Während der Simulation wurden diese Einstellungen geändert. MoveEye arbeitet jetzt wieder mit den echten Einstellungen. Änderungen für die echte Kamera übernehmen?",
      "Take over the selected": "Ausgewählte übernehmen", "Keep the real settings": "Echte Einstellungen behalten", "real": "echt", "simulation": "Simulation", "All": "Alle", "on": "ein", "off": "aus", "taken over": "übernommen",
      "never ask": "nie fragen", "never asked again": "wird nie mehr gefragt", "settings are never asked": "Einstellungen werden nie gefragt", "ask again": "wieder fragen"}};
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || "de"; } catch (e) { return "de"; } };
  const tt = k => (typeof t === "function" && t(k) !== k) ? t(k) : ((T[L()] || {})[k] || k);
  const fmt = v => v === true ? tt("on") : v === false ? tt("off") : (Array.isArray(v) || (v && typeof v === "object")) ? "…" : String(v).slice(0, 40);
  let shown = 0;
  const show = q => {
    if (!q || shown === q.t || document.getElementById("spa")) return; shown = q.t;
    const ov = document.createElement("div"); ov.id = "spa";
    ov.style.cssText = "position:fixed;inset:0;z-index:300;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:12px";
    const b = document.createElement("div");
    b.style.cssText = "background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:16px;max-width:560px;width:100%;max-height:90vh;display:flex;flex-direction:column;overflow:hidden";
    const h = document.createElement("div"); h.style.cssText = "padding:14px 16px 6px;font-weight:600;font-size:17px"; h.textContent = "🧪 " + tt("Settings from the simulation");
    const p = document.createElement("div"); p.style.cssText = "padding:0 16px 8px;font-size:13px;color:var(--mut,#8b9bb0);line-height:1.45"; p.textContent = tt("During the simulation these settings were changed. MoveEye now uses the real settings again. Take over changes for the real camera?");
    const list = document.createElement("div"); list.style.cssText = "overflow:auto;padding:0 16px;flex:1";
    const all = document.createElement("label"); all.style.cssText = "display:flex;gap:8px;align-items:center;padding:6px 0;font-size:13px;border-bottom:1px solid var(--line,#1f2b3a)";
    const ca = document.createElement("input"); ca.type = "checkbox"; ca.checked = true; all.append(ca, document.createTextNode(tt("All") + " (" + q.changes.length + ")")); list.appendChild(all);
    const boxes = [], nev = {};
    q.changes.forEach(c => { const r = document.createElement("label"); r.style.cssText = "display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--line,#1f2b3a);font-size:14px";
      const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = true; cb.value = c.key; cb.style.marginTop = "3px"; boxes.push(cb);
      const tx = document.createElement("div"); tx.style.flex = "1";
      const n = document.createElement("div"); n.textContent = c.label;
      const v = document.createElement("div"); v.style.cssText = "font-size:12px;color:var(--mut,#8b9bb0)"; v.textContent = tt("real") + ": " + fmt(c.real) + "  →  " + tt("simulation") + ": " + fmt(c.sim);
      const nv = document.createElement("button"); nv.type = "button"; nv.className = "sec"; nv.textContent = "🔕 " + tt("never ask");      // 2.96.10
      nv.style.cssText = "font-size:12px;padding:4px 8px;min-height:0;align-self:center;white-space:nowrap";
      nv.onclick = e => { e.preventDefault(); const on = !nv.classList.contains("on"); nv.classList.toggle("on", on); nv.style.borderColor = on ? "#f59a4a" : "";
        nv.textContent = (on ? "✓ " + tt("never asked again") : "🔕 " + tt("never ask")); cb.checked = !on && cb.checked; cb.disabled = on; nev[c.key] = on; };
      tx.append(n, v); r.append(cb, tx, nv); list.appendChild(r); });
    if (q.ignored) { const ig = document.createElement("div"); ig.style.cssText = "font-size:12px;color:var(--mut,#8b9bb0);padding:8px 0";
      ig.textContent = q.ignored + " " + tt("settings are never asked") + " · "; const a = document.createElement("a"); a.href = "#"; a.textContent = tt("ask again");
      a.onclick = async e => { e.preventDefault(); await fetch("/api/simprofile", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({reset_ignore: true})}); ig.remove(); };
      ig.appendChild(a); list.appendChild(ig); }
    ca.onchange = () => boxes.forEach(x => x.checked = ca.checked);
    const bt = document.createElement("div"); bt.style.cssText = "display:flex;gap:8px;padding:12px 16px;border-top:1px solid var(--line,#1f2b3a);flex-wrap:wrap";
    const ok = document.createElement("button"); ok.type = "button"; ok.textContent = tt("Take over the selected"); ok.style.flex = "1";
    const no = document.createElement("button"); no.type = "button"; no.className = "sec"; no.textContent = tt("Keep the real settings"); no.style.flex = "1";
    const send = async take => { ok.disabled = no.disabled = true;
      try { const r = await (await fetch("/api/simprofile", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({take: take, ignore: Object.keys(nev).filter(k => nev[k])})})).json();
        if (take.length && typeof toast === "function") toast("✓ " + (r.taken || 0) + " " + tt("taken over")); } catch (e) {}
      ov.remove(); };
    ok.onclick = () => send(boxes.filter(x => x.checked).map(x => x.value)); no.onclick = () => send([]);
    bt.append(ok, no); b.append(h, p, list, bt); ov.appendChild(b); document.body.appendChild(ov);
  };
  const poll = async () => { try { if (!document.hidden) { const r = await fetch("/api/simprofile?lang=" + L(), {cache: "no-store"}); if (r.ok) { const j = await r.json(); if (j && j.q) show(j.q); } } } catch (e) {}
    setTimeout(poll, 4000); };
  setTimeout(poll, 1500);
})();
// ---- little extras; 1 August = Swiss cross with sparks ----
(function () {
  const h1 = document.querySelector("header h1"); if (!h1) return;
  const lang = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "en"; } catch (e) { return "en"; } };
  const say = k => { const L = lang(); return sayL(k, L); };
  const sayL = (k, L) => (window.LX && LX(k)) || ({"All quiet – I'm keeping watch!": "Alles ruhig – ich halte Wache!", "Happy Swiss National Day!": "Schöne Bundesfeier!"}[k] && (L === "de" || L === "rm")
                    ? {"All quiet – I'm keeping watch!": "Alles ruhig – ich halte Wache!", "Happy Swiss National Day!": "Schöne Bundesfeier!"}[k] : k);
  const SVG = '<svg viewBox="0 0 120 120" aria-hidden="true"><ellipse cx="60" cy="104" rx="40" ry="30" fill="#8a5a3b"/><ellipse cx="60" cy="108" rx="23" ry="20" fill="#c99d6e"/>'
    + '<circle cx="35" cy="31" r="8" fill="#6e4529"/><circle cx="85" cy="31" r="8" fill="#6e4529"/><circle cx="35" cy="31" r="4" fill="#b98457"/><circle cx="85" cy="31" r="4" fill="#b98457"/>'
    + '<circle cx="60" cy="54" r="30" fill="#8a5a3b"/><ellipse cx="60" cy="66" rx="17" ry="13" fill="#ecd3b2"/>'
    + '<circle cx="48" cy="49" r="4.6" fill="#1b1410"/><circle cx="72" cy="49" r="4.6" fill="#1b1410"/><circle cx="49.5" cy="47.5" r="1.5" fill="#fff"/><circle cx="73.5" cy="47.5" r="1.5" fill="#fff"/>'
    + '<ellipse cx="60" cy="60" rx="5.5" ry="3.8" fill="#2a1a12"/><path d="M54 66 Q60 70 66 66" stroke="#2a1a12" stroke-width="1.8" fill="none"/>'
    + '<rect x="55.6" y="67.5" width="4" height="7" rx="1" fill="#fff"/><rect x="60.4" y="67.5" width="4" height="7" rx="1" fill="#fff"/>'
    + '<ellipse cx="40" cy="88" rx="9" ry="6.5" fill="#6e4529"/><ellipse cx="80" cy="88" rx="9" ry="6.5" fill="#6e4529"/></svg>';
  function whistle() {
    try {
      const A = window.AudioContext || window.webkitAudioContext; if (!A) return;
      const ac = new A();
      [0.0, 0.5].forEach(st => { const o = ac.createOscillator(), g = ac.createGain(), t0 = ac.currentTime + 0.05 + st;
        o.type = "sine"; o.frequency.setValueAtTime(3000, t0); o.frequency.exponentialRampToValueAtTime(2100, t0 + 0.26);
        g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.25, t0 + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.27);
        o.connect(g); g.connect(ac.destination); o.start(t0); o.stop(t0 + 0.3); });
      setTimeout(() => ac.close(), 1600);
    } catch (e) {}
  }
  function belly(size) {          // the little pattern on the belly (as SVG squares)
    const [n, hx] = "__BELLY__".split(":"), N = +n; let bits = "";
    for (const ch of hx) bits += parseInt(ch, 16).toString(2).padStart(4, "0");
    let r = '<rect x="-2" y="-2" width="' + (N + 4) + '" height="' + (N + 4) + '" fill="#f3e2c8"/>';
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (bits[y * N + x] === "1") r += '<rect x="' + x + '" y="' + y + '" width="1.02" height="1.02" fill="#3a2516"/>';
    return '<svg viewBox="-2 -2 ' + (N + 4) + ' ' + (N + 4) + '" width="' + size + '" height="' + size + '" shape-rendering="crispEdges">' + r + '</svg>';
  }
  function microBelly() {          // the pattern with one device pixel per square (canvas, no smoothing)
    const [n, hx] = "__BELLY__".split(":"), N = +n, dpr = window.devicePixelRatio || 1;
    const Q = Math.ceil((N + 8) / dpr) * dpr, o = Math.floor((Q - N) / 2); let bits = "";   // a whole number of CSS pixels: no stretching
    for (const ch of hx) bits += parseInt(ch, 16).toString(2).padStart(4, "0");
    const c = document.createElement("canvas"); c.width = Q; c.height = Q;
    const g = c.getContext("2d"); g.fillStyle = "#c99d6e"; g.fillRect(0, 0, Q, Q); g.fillStyle = "#6e4529";
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (bits[y * N + x] === "1") g.fillRect(x + o, y + o, 1, 1);
    c.style.cssText = "position:fixed;z-index:2147483602;pointer-events:none;width:" + (Q / dpr) + "px;height:" + (Q / dpr) + "px;image-rendering:pixelated;border-radius:0;border:0;margin:0;background:none;aspect-ratio:auto;display:block";
    return c;
  }
  let busy = false;
  // only over the live picture (an HTML layer: it is never part of the stream or of a recording)
  const liveOk = v => { const r = v.getBoundingClientRect(); return r.width > 160 && r.height > 120 && r.bottom > 80 && r.top < innerHeight - 80
    && !document.querySelector("#pip:not([hidden])"); };
  window.marmot = function () {
    if (busy) return;
    const v = document.querySelector("#vcard .vwrap"); if (!v) return;          // pages without a live picture: nothing
    busy = true;
    if (liveOk(v)) return show(v);
    v.scrollIntoView({behavior: "smooth", block: "center"});
    let n = 0; const w = setInterval(() => { if (liveOk(v)) { clearInterval(w); setTimeout(() => show(v), 250); } else if (++n > 30) { clearInterval(w); busy = false; } }, 100);
  };
  function cwTriangle(P) {                // a closed triangle, drawn clockwise (screen: y goes down)
    if (P.length < 8) return false;
    const xs = P.map(p => p[0]), ys = P.map(p => p[1]), w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys), size = Math.max(w, h);
    if (size < 40 || Math.min(w, h) < size * 0.3 || Math.hypot(P[0][0] - P[P.length - 1][0], P[0][1] - P[P.length - 1][1]) > size * 0.35) return false;
    let A = 0; for (let i = 0; i < P.length; i++) { const p = P[i], q = P[(i + 1) % P.length]; A += p[0] * q[1] - q[0] * p[1]; }
    A /= 2; if (A <= 0 || A / (w * h) < 0.25 || A / (w * h) > 0.68) return false;
    const rdp = (Q, eps) => { if (Q.length < 3) return Q.slice(); const a = Q[0], b = Q[Q.length - 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1e-9;
      let dm = -1, ix = 0; for (let i = 1; i < Q.length - 1; i++) { const d = L > 1e-6 ? Math.abs((b[0] - a[0]) * (a[1] - Q[i][1]) - (a[0] - Q[i][0]) * (b[1] - a[1])) / L : Math.hypot(Q[i][0] - a[0], Q[i][1] - a[1]); if (d > dm) { dm = d; ix = i; } }
      return dm <= eps ? [a, b] : rdp(Q.slice(0, ix + 1), eps).slice(0, -1).concat(rdp(Q.slice(ix), eps)); };
    const V = rdp(P.concat([P[0]]), size * 0.12).slice(0, -1);
    let ch = true;
    while (ch && V.length > 3) { ch = false;
      for (let i = 0; i < V.length; i++) { const a = V[(i - 1 + V.length) % V.length], b = V[i], c = V[(i + 1) % V.length];
        const u = [a[0] - b[0], a[1] - b[1]], q = [c[0] - b[0], c[1] - b[1]], nu = Math.hypot(...u), nq = Math.hypot(...q);
        if (nu < size * 0.12 || nq < size * 0.12 || (u[0] * q[0] + u[1] * q[1]) / (nu * nq) < -0.88) { V.splice(i, 1); ch = true; break; } } }
    return V.length === 3;
  }
  window.mwTri = cwTriangle;
  function ccwHeart(P0) {                  // 2.95.61: a big closed heart, drawn counter-clockwise (same rules as ccw_heart in Python)
    let P = P0; if (P.length < 12) return false;
    const xs = P.map(p => p[0]), ys = P.map(p => p[1]), L = Math.min(...xs), R = Math.max(...xs), T = Math.min(...ys), B = Math.max(...ys);
    const w = R - L, h = B - T, size = Math.max(w, h);
    if (size < 90 || w / Math.max(h, 1e-6) < 0.6 || w / Math.max(h, 1e-6) > 1.6 || Math.hypot(P[0][0] - P[P.length - 1][0], P[0][1] - P[P.length - 1][1]) > size * 0.3) return false;
    let A = 0; for (let i = 0; i < P.length; i++) { const p = P[i], q = P[(i + 1) % P.length]; A += p[0] * q[1] - q[0] * p[1]; }
    A /= 2; if (A >= 0 || -A / (w * h) < 0.4 || -A / (w * h) > 0.88) return false;
    const cx = (L + R) / 2, D = [];
    for (let i = 0; i < P.length; i++) { const a = P[i], b = P[(i + 1) % P.length], k = Math.max(1, Math.floor(Math.hypot(b[0] - a[0], b[1] - a[1]) / (size / 80)));
      for (let j = 0; j < k; j++) D.push([a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k]); }
    P = D; const tip = P.reduce((m, p) => p[1] > m[1] ? p : m, P[0]);
    if (Math.abs(tip[0] - cx) > 0.22 * w) return false;
    const low = P.filter(p => p[1] > T + 0.8 * h).map(p => p[0]);
    if (low.length && Math.max(...low) - Math.min(...low) > 0.55 * w) return false;
    const mid = P.filter(p => Math.abs(p[0] - cx) < 0.07 * w && p[1] < T + 0.6 * h).map(p => p[1]);
    if (!mid.length || Math.min(...mid) < T + 0.07 * h) return false;
    const lt = P.filter(p => p[0] < cx - 0.15 * w).map(p => p[1]), rt = P.filter(p => p[0] > cx + 0.15 * w).map(p => p[1]);
    return !!(lt.length && rt.length && Math.min(...lt) <= T + 0.15 * h && Math.min(...rt) <= T + 0.15 * h);
  }
  window.mwHeart = ccwHeart;
  const HEART_D = (() => { let d = ""; for (let i = 0; i <= 60; i++) { const t = 2 * Math.PI * i / 60;
    const x = 16 * Math.pow(Math.sin(t), 3), y = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t));
    d += (i ? "L" : "M") + x.toFixed(2) + " " + y.toFixed(2); } return d + "Z"; })();
  const heartSvg = (fill) => '<svg viewBox="-17 -13 34 31" aria-hidden="true"><path d="' + HEART_D + '" fill="' + fill + '"/></svg>';
  function burst(pts) {                    // the drawn heart bursts into pieces
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]), L = Math.min(...xs), T = Math.min(...ys), w = Math.max(...xs) - L, h = Math.max(...ys) - T;
    const b = document.createElement("div"); b.className = "mw-burst";
    b.style.cssText += "left:" + L + "px;top:" + T + "px;width:" + w + "px;height:" + h + "px";
    const N = 12, pieces = [];
    for (let i = 0; i < N; i++) {
      const a0 = 2 * Math.PI * i / N, a1 = 2 * Math.PI * (i + 1) / N, am = (a0 + a1) / 2;
      const pt = a => (50 + Math.cos(a) * 110).toFixed(1) + "% " + (50 + Math.sin(a) * 110).toFixed(1) + "%";
      const d = document.createElement("div"); d.innerHTML = heartSvg(i % 2 ? "#e8436a" : "#ff7aa2");
      const sv = d.firstChild; sv.style.clipPath = "polygon(50% 50%, " + pt(a0) + ", " + pt(am) + ", " + pt(a1) + ")";
      b.appendChild(sv); pieces.push([sv, am]);
    }
    document.body.appendChild(b);
    requestAnimationFrame(() => requestAnimationFrame(() => pieces.forEach(([sv, am], i) => {
      sv.style.transform = "translate(" + Math.round(Math.cos(am) * w * .9) + "px," + Math.round(Math.sin(am) * h * .9 + h * .5) + "px) rotate(" + ((i % 2 ? 1 : -1) * (60 + i * 17)) + "deg) scale(.6)";
      sv.style.opacity = "0"; })));
    setTimeout(() => b.remove(), 900);
  }
  function show(v) {
    const m = document.createElement("div"); m.className = "mw-marmot";
    m.innerHTML = SVG; const b = document.createElement("div"); b.className = "bub"; b.textContent = say("All quiet – I'm keeping watch!"); m.appendChild(b);
    // 2.95.61: on the belly a turning heart: touch it and draw a big heart counter-clockwise - it bursts, the secret shows
    const bl = document.createElement("div"); bl.className = "hrt"; bl.innerHTML = heartSvg("#e8436a");
    m.appendChild(bl); v.appendChild(m);
    let held = false, qr = false, pts = [], trail = null;
    const leave = () => { if (held || qr) return; m.classList.remove("up"); setTimeout(() => { m.remove(); busy = false; }, 500); };
    const drawTrail = () => { if (!trail) return; trail.firstChild.setAttribute("points", pts.map(p => p[0] + "," + p[1]).join(" ")); };
    bl.addEventListener("pointerdown", e => { e.preventDefault(); e.stopPropagation(); held = true; pts = [[e.clientX, e.clientY]]; m.classList.add("drawing");
      trail = document.createElementNS("http://www.w3.org/2000/svg", "svg"); trail.setAttribute("class", "mw-trail");
      trail.innerHTML = '<polyline fill="none" stroke="#ff7aa2" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>';
      document.body.appendChild(trail);
      try { bl.setPointerCapture(e.pointerId); } catch (x) {} });
    bl.addEventListener("pointermove", e => { if (held) { e.preventDefault(); pts.push([e.clientX, e.clientY]); drawTrail(); } });
    const end = e => { if (!held) return; held = false; e.stopPropagation(); m.classList.remove("drawing");
      if (trail) { trail.remove(); trail = null; }
      if (ccwHeart(pts)) { qr = true; bl.style.visibility = "hidden"; burst(pts);
        setTimeout(() => { const q = microBelly();            // 2.95.62: tiny - one screen pixel per square, only readable with a magnifier
          // fixed on the screen, exactly on whole screen pixels (inside the moving marmot it would get blurred)
          const hr = bl.getBoundingClientRect(), dp = window.devicePixelRatio || 1, w = q.width / dp;
          q.style.left = Math.round(hr.left + hr.width / 2 - w / 2) + "px"; q.style.top = Math.round(hr.top + hr.height / 2 - 6 - w / 2) + "px";
          // 2.95.88: first 3 s a tiny target where the code comes (time to put the phone under the microscope), then 3 s the code
          const tg = document.createElement("div"), cx = Math.round(hr.left + hr.width / 2), cy = Math.round(hr.top + hr.height / 2 - 6);
          tg.style.cssText = "position:fixed;z-index:99999;pointer-events:none;width:9px;height:9px;left:" + (cx - 4) + "px;top:" + (cy - 4) + "px";
          tg.innerHTML = '<svg width="9" height="9" viewBox="0 0 9 9"><circle cx="4.5" cy="4.5" r="4" fill="#fff" stroke="#e8436a"/><circle cx="4.5" cy="4.5" r="2.4" fill="none" stroke="#e8436a"/><circle cx="4.5" cy="4.5" r=".9" fill="#e8436a"/></svg>';
          document.body.appendChild(tg);
          let t2 = null;
          const t1 = setTimeout(() => { tg.remove(); document.body.appendChild(q);   // no fading: a see-through layer gets blurred on some screens
            t2 = setTimeout(done, 3000); }, 3000);
          const done = () => { removeEventListener("scroll", done, true); clearTimeout(t1); clearTimeout(t2); tg.remove(); q.remove(); setTimeout(() => { qr = false; leave(); }, 100); };
          addEventListener("scroll", done, {capture: true, once: true});
          bl.style.visibility = "visible"; bl.style.opacity = "0";
          bl.addEventListener("pointerdown", () => done(), {once: true}); }, 650);
      } else setTimeout(leave, 700); };
    bl.addEventListener("pointerup", end); bl.addEventListener("pointercancel", end);
    bl.addEventListener("click", e => e.stopPropagation());
    requestAnimationFrame(() => requestAnimationFrame(() => m.classList.add("up")));
    setTimeout(whistle, 250);
    setTimeout(leave, 3200);                // a little longer than before: time to find the heart
  }
  let taps = [];
  h1.addEventListener("click", () => { const now = Date.now(); taps = taps.filter(x => now - x < 3000); taps.push(now);
    if (taps.length >= 7) { taps = []; window.marmot(); } });
  const d = new Date();
  if ((d.getMonth() === 7 && d.getDate() === 1) || /[?&]aug1=1/.test(location.search)) {
    document.body.classList.add("aug1"); h1.title = "🇨🇭 " + say("Happy Swiss National Day!");
    const cols = ["#ffd166", "#ff6b6b", "#ffffff", "#e8112d", "#ffd166", "#ffffff"];
    cols.forEach((c, i) => { const sp = document.createElement("span"); sp.className = "aug-spark";
      const a = (i / cols.length) * Math.PI * 2; sp.style.cssText = "right:-12px;top:50%;background:" + c + ";--dx:" + Math.round(Math.cos(a) * 22) + "px;--dy:" + Math.round(Math.sin(a) * 18) + "px;animation-delay:" + (i * 0.27).toFixed(2) + "s";
      h1.appendChild(sp); });
  }
})();

// ---- hide / show the whole header (remembered per device) ----
(function () {
  const H = document.querySelector("header"); if (!H) return;
  const TX = {"Hide header": "Kopfzeile ausblenden", "Show header": "Kopfzeile einblenden"};
  const tx = s => (LANG === "de" && TX[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && TX[s]) || s;
  const hb = el("button", "sec", "▴"); hb.type = "button"; hb.id = "btn-hdr";
  const ctl = H.querySelector(".hdr-ctl"); (ctl || H).appendChild(hb);
  const sh = el("button", "sec", "▾"); sh.type = "button"; sh.id = "hdr-show"; document.body.appendChild(sh);
  function set(hidden, store) {
    document.body.classList.toggle("hdrhidden", hidden);
    hb.title = tx("Hide header"); sh.title = tx("Show header"); hb.setAttribute("aria-label", hb.title); sh.setAttribute("aria-label", sh.title);
    if (store) { try { localStorage.setItem("mw-hdr", hidden ? "0" : "1"); } catch (e) {} }
    window.dispatchEvent(new Event("resize"));
  }
  hb.onclick = () => set(true, true); sh.onclick = () => set(false, true);
  let v = null; try { v = localStorage.getItem("mw-hdr"); } catch (e) {}
  set(v === "0", false);
  setTimeout(() => set(document.body.classList.contains("hdrhidden"), false), 1500);   // titles in the right language
})();
// ---- app mode (opened from the home screen icon, no browser bars): reload button; every page: note when a new version runs ----
(function () {
  const H = document.querySelector("header"); if (!H) return;
  const TX = {"Reload page": "Seite neu laden", "New version running": "Neue Version läuft", "Reload": "Neu laden", "later": "später"};
  const tx = s => (LANG === "de" && TX[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && TX[s]) || s;
  const app = (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
  document.body.classList.toggle("appmode", app);
  if (app) {
    const b = el("button", "sec ic"); b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v5h-5"/></svg>'; b.type = "button"; b.id = "btn-reload";
    // reload: first ask the Pi to look for a new version (max. 8 s), then load the page again - the update bar shows it
    b.onclick = async () => {
      b.disabled = true; b.classList.add("spin");
      const ac = window.AbortController ? new AbortController() : null; const to = setTimeout(() => ac && ac.abort(), 8000);
      try { await fetch("/api/update", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "check", lang: LANG}),
                                       signal: ac ? ac.signal : undefined, cache: "no-store"}); } catch (e) {}
      clearTimeout(to); location.reload();
    };
    const ctl = H.querySelector(".hdr-ctl"); (ctl || H).insertBefore(b, ctl ? ctl.firstChild : null);
    setTimeout(() => { b.title = tx("Reload page"); b.setAttribute("aria-label", b.title); }, 1200);
  }
  // app mode (home screen): a download opens a page without "back" - instead the file goes to the share sheet (Save to Files)
  if (app) document.addEventListener("click", async e => {
    const a = e.target.closest && e.target.closest("a[download], a[href*='dl=1'], a[href^='/api/settings/export']");
    if (!a || !a.href || a.href.startsWith("blob:")) return;
    e.preventDefault();
    try {
      const r = await fetch(a.href); if (!r.ok) throw new Error("HTTP " + r.status);
      const bl = await r.blob();
      const name = a.getAttribute("download") || decodeURIComponent((a.href.split("/").pop() || "file").split("?")[0]);
      const f = new File([bl], name, {type: bl.type || "application/octet-stream"});
      if (navigator.canShare && navigator.canShare({files: [f]})) { await navigator.share({files: [f], title: name}); return; }
      const u = URL.createObjectURL(bl), x = document.createElement("a"); x.href = u; x.download = name; document.body.appendChild(x); x.click(); x.remove();
      setTimeout(() => URL.revokeObjectURL(u), 10000);
    } catch (err) { if (!(err && err.name === "AbortError")) alert("⚠ " + (err.message || err)); }
  }, true);
  const PAGEVER = "__APPVER__"; let shown = false;
  async function check() {
    if (document.hidden || shown) return;
    try {
      const r = await fetch("/api/version", {cache: "no-store"}); if (!r.ok) return;
      const j = await r.json();
      if (j.version && j.version !== PAGEVER) {
        shown = true;
        const bar = el("div"); bar.id = "newver";
        bar.style.cssText = "position:fixed;left:12px;right:12px;bottom:max(12px,env(safe-area-inset-bottom));z-index:90;display:flex;gap:10px;align-items:center;"
          + "background:var(--panel);border:1px solid var(--acc);border-radius:12px;padding:10px 12px;box-shadow:var(--shadow)";
        const tt = el("div", "", "✨ " + tx("New version running") + ": " + j.version); tt.style.flex = "1"; tt.style.fontWeight = "700";
        const go = el("button", "", tx("Reload")); go.onclick = () => location.reload();
        const no = el("button", "sec", tx("later")); no.onclick = () => bar.remove();
        bar.append(tt, go, no); document.body.appendChild(bar);
      }
    } catch (e) {}
  }
  setInterval(check, 20000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) setTimeout(check, 1500); });
})();
// ---- location of the phone for the GPS data of photos / videos (browsers give it only to https pages) ----
(function () {
  if (!window.isSecureContext || !navigator.geolocation) return;
  let last = null, lastT = 0;
  const send = p => { const c = p.coords, now = Date.now();
    const moved = !last || Math.hypot((c.latitude - last[0]) * 111000, (c.longitude - last[1]) * 75000) > 30;
    if (!moved && now - lastT < 600000) return;
    last = [c.latitude, c.longitude]; lastT = now;
    fetch("/api/gps", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({lat: c.latitude, lon: c.longitude, acc: c.accuracy})}).catch(() => {}); };
  setTimeout(() => fetch("/api/gps").then(r => r.json()).then(j => { if (j && j.on)
    navigator.geolocation.watchPosition(send, () => {}, {enableHighAccuracy: false, maximumAge: 120000, timeout: 30000}); }).catch(() => {}), 1500);
})();
// ---- clock: the Pi has no battery clock; without internet it takes the time of the phone ----
(function () {
  let tz = ""; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
  setTimeout(() => { try { fetch("/api/time", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({t: Date.now(), tz: tz})}).catch(() => {}); } catch (e) {} }, 800);
})();
"""


ALERT_JS = r"""
// ---- alarm sound in the browser (every page): the server sends alarms over a live connection (/api/alerts) ----
(function () {
  const ALT = {"Alarm sound": "Alarmton", "Sound on": "Ton ein", "Pre-alarm (first movement)": "Voralarm (erste Bewegung)",
    "Person detected": "Person erkannt", "Warm body (thermal camera)": "Wärme erkannt (Wärmebild)", "Armed - alarms are active": "Schutz an – Alarme aktiv",
    "Person / warm body / noise": "Person / Wärme / Geräusch", "Noise (microphone)": "Geräusch (Mikrofon)", "Volume": "Lautstärke", "Test": "Test", "Vibrate (phones)": "Vibrieren (Handy)",
    "Pre-alarm: movement": "Voralarm: Bewegung", "Tap anywhere on the page to allow the sound": "Irgendwo auf die Seite tippen, um den Ton zu erlauben",
    "Mute 30 min": "30 Min. stumm", "Muted until": "Stumm bis", "Unmute": "Ton wieder an", "Pre-alarm": "Voralarm", "Person": "Person",
    "connection to the camera interrupted - reconnecting": "Verbindung zur Kamera unterbrochen - verbinde neu",
    "The page must stay open (also in the background). With the screen off or the browser closed only the push message (ntfy / Telegram) arrives.":
      "Die Seite muss offen bleiben (auch im Hintergrund geht es). Bei ausgeschaltetem Bildschirm oder geschlossenem Browser kommt nur die Push-Nachricht (ntfy / Telegram)."};
  const at = s => (LANG === "de" && ALT[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && ALT[s]) || s;
  const S = {on: false, pre: true, person: true, vol: 0.7, vib: true, mute: 0};
  try { Object.assign(S, JSON.parse(localStorage.getItem("mw-sound") || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem("mw-sound", JSON.stringify(S)); } catch (e) {} };
  let ctx = null, es = null, lastPre = 0, connOk = true, errTimer = null, titleTimer = null;
  const baseTitle = document.title;

  function audio() {
    if (!ctx) { const A = window.AudioContext || window.webkitAudioContext; if (!A) return null; try { ctx = new A(); } catch (e) { return null; } }
    if (ctx.state === "suspended") ctx.resume().then(paint).catch(() => {});
    return ctx;
  }
  function tone(c, f0, f1, t0, dur, type, vol) {
    const o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.setValueAtTime(f0, t0);
    if (f1 !== f0) o.frequency.linearRampToValueAtTime(f1, t0 + dur);
    const v = Math.max(0.002, vol);
    g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(v, t0 + 0.02);
    g.gain.setValueAtTime(v, t0 + dur - 0.04); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(c.destination); o.start(t0); o.stop(t0 + dur + 0.03);
  }
  function play(kind) {
    const c = audio(); if (!c) return;
    const v = S.vol * 0.45, t0 = c.currentTime + 0.05;
    if (kind === "prealarm") {                       // two short, friendly beeps
      tone(c, 880, 880, t0, 0.14, "sine", v); tone(c, 1175, 1175, t0 + 0.22, 0.2, "sine", v);
    } else {                                         // person: siren, about 2 seconds
      for (let i = 0; i < 4; i++) { tone(c, 620, 1180, t0 + i * 0.5, 0.25, "triangle", v); tone(c, 1180, 620, t0 + i * 0.5 + 0.25, 0.25, "triangle", v); }
    }
    if (S.vib && navigator.vibrate) { try { navigator.vibrate(kind === "prealarm" ? [120, 80, 120] : [300, 120, 300, 120, 300]); } catch (e) {} }
  }
  const muted = () => S.mute && Date.now() < S.mute;

  // ---- header button ----
  const btn = el("button", "sec sndbtn ic"); btn.type = "button"; btn.id = "btn-sound";
  const ctl = document.querySelector(".hdr-ctl"); if (ctl) ctl.insertBefore(btn, ctl.firstChild); else document.body.appendChild(btn);
  function paint() {
    const needTap = S.on && (!ctx || ctx.state !== "running");
    btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>' + ((S.on && !muted()) ? '' : '<path d="M3 3l18 18"/>') + '</svg>';
    btn.classList.toggle("on", S.on && !muted() && !needTap && connOk);
    btn.classList.toggle("warn", S.on && (needTap || !connOk));
    btn.title = at("Alarm sound") + (needTap ? " · " + at("Tap anywhere on the page to allow the sound") : "")
      + (!connOk ? " · " + at("connection to the camera interrupted - reconnecting") : "")
      + (muted() ? " · " + at("Muted until") + " " + new Date(S.mute).toLocaleTimeString().slice(0, 5) : "");
  }
  // browsers only allow sound after a click / tap on the page: unlock on the first one
  ["pointerdown", "keydown", "touchstart"].forEach(ev => document.addEventListener(ev, () => { if (S.on) { audio(); setTimeout(paint, 200); } }, {passive: true}));

  // ---- settings panel ----
  let pop = null;
  function closePop() { if (pop) { pop.remove(); pop = null; } }
  function sw(label, key, after) {
    const row = el("label", "row"); const cb = el("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!S[key];
    cb.onchange = () => { S[key] = cb.checked; save(); if (after) after(); paint(); };
    row.append(el("span", "", at(label)), cb); return row;
  }
  function openPop() {
    closePop();
    pop = el("div", "sndpop card");
    pop.appendChild(el("div", "sndhead", at("Alarm sound")));
    pop.append(sw("Sound on", "on", () => { if (S.on) { audio(); play("prealarm"); } connect(); }),
               sw("Pre-alarm (first movement)", "pre"), sw("Person / warm body / noise", "person"), sw("Vibrate (phones)", "vib"));
    const vr = el("div", "sl"); const top = el("div", "row"); const vv = el("span", "val", Math.round(S.vol * 100) + " %");
    top.append(el("span", "", at("Volume")), vv);
    const r = el("input"); r.type = "range"; r.min = 0.1; r.max = 1; r.step = 0.05; r.value = S.vol;
    r.oninput = () => { S.vol = parseFloat(r.value); vv.textContent = Math.round(S.vol * 100) + " %"; save(); };
    vr.append(top, r); pop.appendChild(vr);
    const b = el("div", "btns");
    const t1 = el("button", "sec", at("Test") + ": " + at("Pre-alarm")); t1.type = "button"; t1.onclick = () => play("prealarm");
    const t2 = el("button", "sec", at("Test") + ": " + at("Person")); t2.type = "button"; t2.onclick = () => play("person");
    const m = el("button", "sec", muted() ? at("Unmute") : at("Mute 30 min")); m.type = "button";
    m.onclick = () => { S.mute = muted() ? 0 : Date.now() + 30 * 60000; save(); paint(); openPop(); };
    b.append(t1, t2, m); pop.appendChild(b);
    const hint = el("div", "mut", at("The page must stay open (also in the background). With the screen off or the browser closed only the push message (ntfy / Telegram) arrives."));
    hint.style.marginTop = "8px"; pop.appendChild(hint);
    pop.addEventListener("pointerdown", e => e.stopPropagation());
    document.body.appendChild(pop);
  }
  btn.addEventListener("pointerdown", e => e.stopPropagation());
  btn.onclick = () => { audio(); pop ? closePop() : openPop(); paint(); };
  document.addEventListener("pointerdown", closePop);
  document.addEventListener("keydown", e => { if (e.key === "Escape") closePop(); });

  // ---- alarms from the server ----
  function flash(label) {
    document.body.classList.remove("alarmflash"); void document.body.offsetWidth; document.body.classList.add("alarmflash");
    if (document.hidden) { document.title = "🔔 " + label; clearTimeout(titleTimer); titleTimer = setTimeout(() => { document.title = baseTitle; }, 15000); }
  }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) document.title = baseTitle; });
  function onAlert(a) {
    if (!S.on) return;
    if (a.kind === "armed") { try { toast("🛡 " + at("Armed - alarms are active")); } catch (e) {} return; }
    const label = a.kind === "person" ? at("Person detected") + (a.count ? " (" + a.count + ")" : "")
      : (a.kind === "warm" ? at("Warm body (thermal camera)") : (a.kind === "noise" ? at("Noise (microphone)") + (a.db != null ? " " + a.db + " dB" : "") : at("Pre-alarm: movement")));
    flash(label);
    try { toast("🔔 " + label + " · " + a.time); } catch (e) {}
    if (muted()) return;
    if (a.kind === "prealarm") { if (!S.pre || Date.now() - lastPre < 8000) return; lastPre = Date.now(); }
    if ((a.kind === "person" || a.kind === "warm" || a.kind === "noise") && !S.person) return;
    play(a.kind);
  }
  function connect() {
    if (!S.on) { if (es) { es.close(); es = null; } connOk = true; paint(); return; }
    if (es || !window.EventSource) return;
    es = new EventSource("/api/alerts");
    es.addEventListener("alert", e => { try { onAlert(JSON.parse(e.data)); } catch (x) {} });
    es.onopen = () => { clearTimeout(errTimer); connOk = true; paint(); };
    es.onerror = () => { clearTimeout(errTimer); errTimer = setTimeout(() => { connOk = false; paint(); }, 8000); };   // it reconnects by itself
  }
  window.mwPlayAlarm = play;               // for testing in the browser console
  paint(); connect();
  setInterval(paint, 30000);
})();
"""


COMMON_JS = r"""
const $ = s => document.querySelector(s);
// Live picture that heals itself: phones (above all iPhone) drop the endless MJPEG stream after a network hiccup,
// in the background or when the Pi restarts -> broken-image "?" icon. Reconnect automatically.
function keepStream(img) {
  if (!img || img.dataset.keep) return;
  img.dataset.keep = "1";
  const base = (img.dataset.src || img.getAttribute("src") || "").split("?")[0];
  let tries = 0, timer = null;
  const box = img.parentNode;
  const lost = on => { img.style.visibility = on ? "hidden" : ""; if (box) box.classList.toggle("vlost", on); };
  let iv = 0;
  // 2.95.34: a picture that was removed from the page stops its stream (otherwise every rebuilt tile kept one open)
  const alive = () => { if (img.isConnected) return true; clearInterval(iv); clearTimeout(timer); document.removeEventListener("visibilitychange", vis); img.src = ""; return false; };
  const restart = () => { clearTimeout(timer); timer = null; if (alive()) img.src = base + "?r=" + Date.now(); };
  const later = () => { if (timer) return; lost(true); timer = setTimeout(restart, Math.min(10000, 1000 * (1 + tries++))); };
  const vis = () => { if (!document.hidden) restart(); };
  img.mwRestart = restart;                  // 2.95.72: the page fetches the picture anew when the video source changes
  img.addEventListener("error", later);
  img.addEventListener("load", () => { tries = 0; lost(false); });
  document.addEventListener("visibilitychange", vis);
  addEventListener("pageshow", e => { if (e.persisted) restart(); });
  iv = setInterval(() => {
    if (!alive() || document.hidden) return;
    if (img.naturalWidth) { if (!timer) { tries = 0; lost(false); } }
    else if (img.complete) later();
  }, 3000);
}
const post = (u, b) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b || {})})
    .then(r => r.json()).catch(() => ({ok: false, error: "connection"}));
const sleep = ms => new Promise(r => setTimeout(r, ms));
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
let LANG = "", THEME = "";
try { LANG = localStorage.getItem("mw-lang") || ""; THEME = localStorage.getItem("mw-theme") || ""; } catch (e) {}
const I18N = {de: {"Live": "Live", "Cameras": "Kameras", "Recordings": "Aufzeichnungen", "Zones": "Zonen", "Manual": "Anleitung", "Diary": "Tagebuch", "Tools": "Werkzeuge", "Simulator": "Simulator", "Game corner": "Spielecke"}};
Object.assign(I18N.de, {"Protection": "Schutz", "History": "Verlauf", "Message list": "Nachrichten", "Settings": "Einstellungen", "Sett.": "Einst.", "More": "Mehr", "Overview": "Übersicht", "Log": "Protokoll", "Sim": "Sim", "Recordings": "Aufnahmen", "Diary": "Tagebuch", "Zones": "Zonen", "Cameras": "Kameras", "Manual": "Anleitung", "Game corner": "Spielecke", "Tools": "Werkzeuge"});  // 2.98.0: the six tabs
const t = s => (LANG === "de" && I18N.de[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && I18N.de[s]) || (I18N.en && I18N.en[s]) || s;
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(e => e.textContent = t(e.dataset.i18n));
  const b = $("#btn-lang"); if (b) b.textContent = (LANG || "en").toUpperCase();
  document.documentElement.lang = LANG;
}
function themeStep() { return document.documentElement.classList.contains("sxnight") ? "red" : THEME === "light" ? "light" : "dark"; }   // 573/578: Hell → Dunkel → Rotlicht
function applyTheme() { document.body.classList.toggle("light", THEME === "light"); const b = $("#btn-theme"), s = themeStep();
  if (b) { b.innerHTML = s === "light" ? "&#9790;" : s === "dark" ? "&#9673;" : "&#9728;"; b.classList.toggle("thred", s === "red"); } }
function toggleTheme() { const n = {light: "dark", dark: "red", red: "light"}[themeStep()];
  document.documentElement.classList.toggle("sxnight", n === "red"); THEME = n === "light" ? "light" : "dark";
  try { localStorage.setItem("mw-theme", THEME); localStorage.setItem("mw-night", n === "red" ? "1" : "0"); } catch (e) {} applyTheme();
  if (window.sxThemeSaid) window.sxThemeSaid(n); }
function toggleLang() { langMenu(document.querySelector("#btn-lang")); }
let toastTimer = null;
function toast(msg) { let e = $("#toast"); if (!e) { e = el("div"); e.id = "toast"; document.body.appendChild(e); } e.textContent = msg; e.classList.add("on");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => e.classList.remove("on"), 2600); }
async function initAppearance() {
  if (!LANG || !THEME) {
    try { const a = await (await fetch("/api/appearance")).json(); LANG = LANG || a.lang; THEME = THEME || a.theme; }
    catch (e) { LANG = LANG || "en"; THEME = THEME || "dark"; }
  }
  applyTheme(); applyI18n();
}
"""


