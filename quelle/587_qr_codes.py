#@ MoveEye – Teil 585: QR-Codes überall, wo ein Link fürs Handy steht (Web und Fenster), «QR-Galerie» und Druckseite. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): a small QR icon next to every link that a phone should open; the link and «Copy» stay.
#   Web: one shared helper for every page (rendered into <head> by render_page below, so the main page has it too):
#     qrBtn(url, title, opts) -> a small QR button;  qrShow(url, title, opts) -> big overlay (QR, link, Copy, Print, Close)
#     opts: {secret: true} (a warning, never cached), {alt: [{label, url, note}]} (choice, e.g. ntfy Android / iPhone),
#           {note: "…"}, {pick: 1} (first choice), {print: true} (print at once).
#     The QR comes from the own encoder (qr_svg, part 110) over POST /api/qr: the text never stands in an address (no
#     browser history, no proxy log), the answer is «no-store». Like GET /api/qr only for the administrator (role_guard).
#     Fields that already exist are decorated by themselves (no change in 530 needed): guest link #g-link, the ntfy
#     address (Notifications), «Address of this page for links», the Tailscale line (System) → all addresses.
#     Explicit calls: iPhone shortcuts, picture for other programs, TV link, simulator tunnel (530), app key (573),
#     recordings (540).
#   «QR codes» (Mehr → QR codes, /qr): every current code on one page, only for the administrator (not for app keys),
#     secrets blurred until tapped, each with print; «Print all» → /qr/print (A4, labels; secrets only when ticked).
#   Window: qr_tk_dialog (picture via qr_png, Copy, Save picture, Print with lp) and qr_tk_gallery; buttons in the sections
#     Guest access, Web stream, Notifications, Simulator (tunnel) and Setup (all codes); the app key (573) too.
#   ntfy: the Android app subscribes with ntfy://<server>/<topic>?display=… (docs.ntfy.sh/subscribe/phone - https links
#     do not work there); the iPhone app has no such link: the https address opens the topic in the browser.
# Translations: part 625.
# ----------------------------------------------------------------------------

QR_SECRET_PATHS = ("/api/ext", "/api/shortcut", "/api/guest", "/api/tunnel", "/api/qr", "/qr", "/api/appkeys", "/api/setup", "/api/party")
QR_SHORTCUTS = (("arm", "Arm"), ("disarm", "Disarm"), ("siren_off", "Siren off"), ("light_on", "White light on"), ("light_off", "White light off"),
                ("photo.jpg", "Photo now"), ("status", "Status (text)"))
QR_GROUPS = (("addr", "Addresses of MoveEye"), ("wifi", "Own Wi-Fi of the device"), ("push", "Push messages (ntfy)"), ("guest", "Guest access"),
             ("short", "iPhone shortcuts"), ("stream", "Picture for other programs"), ("tv", "TV view"), ("sim", "Simulator connection (tunnel)"),
             ("games", "Games"), ("info", "Info page for guests"))


def ntfy_app_url(url, name="MoveEye"):
    """https://<server>/<topic> -> ntfy://<server>/<topic>?display=<name> (the Android app subscribes); '' if it is no topic address"""
    m = re.fullmatch(r"(https?)://([^/\s?#]+)/([A-Za-z0-9_-]{1,64})/?", str(url or "").strip())
    if not m:
        return ""
    from urllib.parse import quote
    return f"ntfy://{m.group(2)}/{m.group(3)}?display={quote(str(name or 'MoveEye')[:40])}" + ("&secure=false" if m.group(1) == "http" else "")


def qr_items(lang=None, host=None):
    """All QR codes of now: [{id, group, title, url, secret, note, alt: [{label, url, note}]}]. host = the address the
    browser uses (fallback when no network address is known). Secrets only go to the administrator (routes below)."""
    L = norm_lang(lang)
    T = lambda s: tr(s, L)
    out, seen = [], set()

    def add(group, title, url, secret=False, note="", alt=None):
        if not url or (group, url) in seen:
            return
        seen.add((group, url))
        out.append({"id": f"{group}{len(out)}", "group": group, "title": title, "url": url, "secret": bool(secret), "note": note, "alt": alt or []})
    try:
        addrs = setup_addresses()
    except Exception:
        addrs = []
    names = {"lan": "Home network", "hotspot": "Own Wi-Fi of the device", "tailscale": "On the road (Tailscale)"}
    for a in addrs:
        add("addr", T(names.get(a["kind"], a["kind"])), a["url"])
    try:
        hu = tailscale_https_url()
    except Exception:
        hu = ""
    add("addr", T("On the road, encrypted (https)"), hu)
    pu = str(CFG.get("public_url") or "").strip()
    if pu and pu.rstrip("/") not in [o["url"].rstrip("/") for o in out]:
        add("addr", T("Address of this page for links"), pu)
    loc = (page_address() or "").rstrip("/") or str(host or "").rstrip("/")
    if not out and loc:
        add("addr", T("This address"), loc + "/")
    if CFG.get("hotspot_on") and CFG.get("hotspot_password"):
        add("wifi", T("Own Wi-Fi of the device") + ": " + str(CFG.get("hotspot_ssid") or ""), wifi_qr_text(CFG["hotspot_ssid"], CFG["hotspot_password"]), True,
            T("Scan with the phone camera to join the Wi-Fi."))
    nu = str(CFG.get("notify_url") or "").strip()
    na = ntfy_app_url(nu, CFG.get("device_name") or "MoveEye") if CFG.get("notify_type") == "ntfy" else ""
    if na:
        add("push", T("Push messages (ntfy)"), na, True, T("Android: the ntfy app subscribes to the topic by itself."),
            [{"label": "Android", "url": na, "note": T("Android: the ntfy app subscribes to the topic by itself.")}, {"label": "iPhone / " + T("Browser"), "url": nu, "note": T("iPhone: the ntfy app cannot subscribe from a code - the code opens the topic in the browser. In the app: + and enter the topic.")}])
    try:
        gi = guest_info()
    except Exception:
        gi = {"active": False}
    if gi.get("active") and loc:
        add("guest", T("Guest access"), loc + gi["path"], True, T("Guests see only the live picture."))
    tok = str(CFG.get("shortcut_token") or "")
    if tok:
        base = (pu.rstrip("/") or loc)
        for a, n in QR_SHORTCUTS:
            add("short", T("iPhone shortcuts") + " · " + T(n), f"{base}/k/{tok}/{a}", True)
    try:
        from urllib.parse import urlparse
        hn = None if page_address() else (urlparse(str(host or "")).hostname or None)
        lk = ext_links(hn if hn not in ("localhost",) else None) if CFG.get("ext_on") else {"on": False}
    except Exception:
        lk = {"on": False}
    if lk.get("on"):
        for k, n in (("mjpeg", "MJPEG"), ("jpg", T("Still picture")), ("rtsp", "RTSP")):
            add("stream", T("Picture for other programs") + " · " + n, lk.get(k) or "", True,
                T("Keep these addresses secret: whoever has them sees the picture without a password."))
    if loc:
        try:
            add("tv", T("TV view"), loc + tv_url(False), True, T("Open on a TV or a second screen."))
        except Exception:
            pass
    if CFG.get("tunnel_on") and loc:
        try:
            code = tunnel_code()
        except Exception:
            code = ""
        add("sim", T("Simulator connection (tunnel)"), loc + "/", True, T("Code") + ": " + code + " · " + T("In the simulator (Verbindung → «Tunnel zu MoveEye») paste the address and type the code."))
    try:
        if party_on() and loc:
            add("games", T("Games"), loc + "/p/" + PARTY["key"] + "/", False, T("Scan the QR code with the phone (same Wi-Fi)."))
    except Exception:
        pass
    if CFG.get("info_page") and loc:
        add("info", T("Info page for guests"), loc + "/info/")
    return out


def qr_items_json(lang=None, host=None, svg=True):
    items = qr_items(lang, host)
    if svg:
        for it in items:
            try:
                it["svg"] = qr_svg(it["url"])
            except ValueError:
                it["svg"] = ""
    L = norm_lang(lang)
    return {"ok": True, "items": items, "groups": {g: tr(n, L) for g, n in QR_GROUPS}}


# ---- web: the shared helper (every page, through render_page) ------------------------------------------------------------
QR_JS = r"""
(function () {
  if (window.qrShow) return;
  const QT = /*QRTX*/{}, DEF = /*QRLANG*/"de";
  const lang = () => { let l = ""; try { l = (typeof LANG !== "undefined" && LANG) || ""; } catch (e) {} if (!l) { try { l = localStorage.getItem("mw-lang") || ""; } catch (e) {} } return l || DEF; };
  const qt = k => { const d = QT[lang()]; return (d && d[k]) || (lang() === "rm" && QT.de && QT.de[k]) || k; };
  window.qrT = qt;
  const abs = u => { u = String(u == null ? "" : u); return u.charAt(0) === "/" ? location.origin + u : u; };
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 3h8v8H3zm2 2v4h4V5zm8-2h8v8h-8zm2 2v4h4V5zM3 13h8v8H3zm2 2v4h4v-4zm8-2h3v3h-3zm5 0h3v3h-3zm-5 5h3v3h-3zm5 0h3v3h-3zm-2.5-2.5h3v3h-3z"/></svg>';
  const CSS = ".qrb{display:inline-flex;align-items:center;justify-content:center;min-width:32px;min-height:32px;padding:4px 7px;margin:2px;border:1px solid var(--line,#8886);border-radius:8px;background:transparent;color:inherit;cursor:pointer;vertical-align:middle;opacity:.8;flex:0 0 auto}"
    + ".qrb:hover,.qrb:focus-visible{opacity:1;border-color:var(--acc,#e8590c)}.qrb svg{width:16px;height:16px;display:block}.qrb[hidden]{display:none}"
    + "#qr-ov{position:fixed;inset:0;z-index:9500;background:rgba(0,0,0,.62);display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box}"
    + "#qr-ov .qr-card{background:var(--panel,#fff);color:var(--txt,#111);border:1px solid var(--line,#ccc);border-radius:14px;max-width:420px;width:100%;max-height:calc(100vh - 32px);overflow:auto;padding:16px;box-sizing:border-box;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,.45)}"
    + "#qr-ov h3{margin:0 0 6px;font-size:17px}#qr-ov .qr-img{background:#fff;border-radius:10px;padding:8px;margin:8px auto;width:min(300px,72vw);aspect-ratio:1/1;box-sizing:border-box;color:#333;display:flex;align-items:center;justify-content:center}"
    + "#qr-ov .qr-img svg{width:100%;height:100%;display:block}#qr-ov .qr-url{display:block;word-break:break-all;font-size:13px;margin:6px 0;user-select:all;-webkit-user-select:all;font-family:ui-monospace,Menlo,monospace}"
    + "#qr-ov .qr-note{font-size:12px;opacity:.8;margin:6px 0}#qr-ov .qr-sec{font-size:12px;color:var(--org,#c60);margin:6px 0}"
    + "#qr-ov .qr-btns{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:10px}#qr-ov .qr-seg{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin:4px 0}"
    + "#qr-ov .qr-seg button{min-height:32px;padding:4px 10px}#qr-ov .qr-seg button.on{outline:2px solid var(--acc,#e8590c);outline-offset:1px}"
    + "@media print{body.qr-print>*:not(#qr-ov){display:none!important}body.qr-print #qr-ov{position:static;background:none;padding:0;display:block}"
    + "body.qr-print #qr-ov .qr-card{border:0;box-shadow:none;max-height:none;max-width:none;color:#000;background:#fff;overflow:visible}"
    + "body.qr-print #qr-ov .qr-btns,body.qr-print #qr-ov .qr-seg,body.qr-print #qr-ov .qr-sec{display:none!important}body.qr-print #qr-ov .qr-img{width:8cm}body.qr-print #qr-ov .qr-url{font-size:11pt}}";
  const addCss = () => { if (document.getElementById("qr-css")) return; const s = E("style"); s.id = "qr-css"; s.textContent = CSS; (document.head || document.documentElement).appendChild(s); };
  const cache = new Map();
  async function svgOf(text, secret) {
    if (!secret && cache.has(text)) return cache.get(text);
    const r = await fetch("/api/qr", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({t: text}), cache: "no-store", credentials: "same-origin"});
    if (!r.ok) throw new Error(r.status === 403 ? qt("Only for the administrator") : r.status === 400 ? qt("Too long for a QR code") : "HTTP " + r.status);
    const s = await r.text(); if (!secret) { if (cache.size > 40) cache.clear(); cache.set(text, s); } return s;
  }
  window.qrSvg = svgOf;
  async function copy(txt, node) {
    try { if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(txt); return true; } } catch (e) {}
    try { const ta = E("textarea"); ta.value = txt; ta.setAttribute("readonly", ""); ta.style.cssText = "position:fixed;left:-9999px;top:0"; (node || document.body).appendChild(ta); ta.select();
      const ok = document.execCommand("copy"); ta.remove(); return ok; } catch (e) { return false; }
  }
  function close() { const o = document.getElementById("qr-ov"); if (o) { if (o._key) document.removeEventListener("keydown", o._key); o.remove(); } document.body.classList.remove("qr-print"); }
  window.qrClose = close;
  window.qrShow = function (url, title, o) {
    o = (typeof o === "function" ? o() : o) || {}; addCss(); close();
    const alts = (o.alt && o.alt.length ? o.alt : [{label: "", url: url, note: o.note}]).map(a => ({label: a.label || "", url: abs(a.url), note: a.note || o.note || ""}));
    let cur = Math.max(0, Math.min(alts.length - 1, (typeof o.pick === "function" ? o.pick() : o.pick) | 0)), last = null;
    const ov = E("div"); ov.id = "qr-ov"; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true");
    const c = E("div", "qr-card"); ov.appendChild(c);
    const h = E("h3", "", title || qt("QR code")); h.id = "qr-h"; ov.setAttribute("aria-labelledby", "qr-h");
    const seg = E("div", "qr-seg"), img = E("div", "qr-img", "…"), u = E("code", "qr-url"), note = E("div", "qr-note");
    img.setAttribute("role", "img");
    c.append(h, seg, img, u, note);
    if (o.secret) c.appendChild(E("div", "qr-sec", "🔒 " + qt("Secret: whoever scans this code gets access. Show it only to people you trust.")));
    const bt = E("div", "qr-btns"), cp = E("button", "sec", "📋 " + qt("Copy")), pr = E("button", "sec", "🖨 " + qt("Print")), cl = E("button", "", qt("Close"));
    cp.type = pr.type = cl.type = "button"; cp.id = "qr-copy"; pr.id = "qr-printb"; cl.id = "qr-close";
    bt.append(cp, pr, cl); c.appendChild(bt);
    const paint = async () => { const a = alts[cur];
      [...seg.children].forEach((b, i) => b.classList.toggle("on", i === cur));
      u.textContent = a.url; note.textContent = a.note; note.hidden = !a.note; img.textContent = "…"; img.removeAttribute("data-ok");
      try { const s = await svgOf(a.url, !!o.secret); if (alts[cur] !== a) return; img.innerHTML = s; img.dataset.ok = "1"; img.setAttribute("aria-label", qt("QR code") + ": " + a.url); last = a.url; }
      catch (e) { img.textContent = "⚠ " + e.message; } };
    if (alts.length > 1) alts.forEach((a, i) => { const b = E("button", "sec", a.label || String(i + 1)); b.type = "button"; b.onclick = () => { cur = i; paint(); }; seg.appendChild(b); });
    cp.onclick = async () => { const ok = await copy(alts[cur].url, c); cp.textContent = ok ? "✓ " + qt("Copied") : "⚠ " + qt("Copy the link from the field"); if (!ok) { const r = document.createRange(); r.selectNodeContents(u); const s = getSelection(); s.removeAllRanges(); s.addRange(r); } };
    const doPrint = () => { document.body.classList.add("qr-print"); const off = () => { document.body.classList.remove("qr-print"); removeEventListener("afterprint", off); }; addEventListener("afterprint", off); setTimeout(() => { try { print(); } catch (e) {} }, 50); };
    pr.onclick = doPrint;
    cl.onclick = close;
    ov.addEventListener("click", e => { if (e.target === ov) close(); });
    ov._key = e => { if (e.key === "Escape") close(); }; document.addEventListener("keydown", ov._key);
    document.body.appendChild(ov); cl.focus();
    paint().then(() => { if (o.print && last) doPrint(); });
    return ov;
  };
  window.qrBtn = function (url, title, o) {
    addCss(); const b = E("button", "qrb"); b.type = "button"; b.innerHTML = ICON; b.dataset.qr = "1";
    const tl = qt("Show the QR code") + (title ? " – " + title : ""); b.title = tl; b.setAttribute("aria-label", tl);
    b.onclick = e => { e.preventDefault(); e.stopPropagation(); const v = typeof url === "function" ? url() : url; if (v) qrShow(v, title, o); };
    return b;
  };
  // -- fields that exist already: decorated here, so the pages need no change --
  const ntfyAlt = v => { const m = /^(https?):\/\/([^\/\s?#]+)\/([A-Za-z0-9_-]{1,64})\/?$/.exec(String(v || "").trim()); if (!m) return null;
    const app = "ntfy://" + m[2] + "/" + m[3] + "?display=MoveEye" + (m[1] === "http" ? "&secure=false" : "");
    return [{label: "Android", url: app, note: qt("Android: the ntfy app subscribes to the topic by itself.")}, {label: "iPhone / " + qt("Browser"), url: m[0], note: qt("iPhone: the ntfy app cannot subscribe from a code - the code opens the topic in the browser. In the app: + and enter the topic.")}]; };
  window.qrNtfy = ntfyAlt;
  async function listShow(group, title) {
    let j = null; try { j = await (await fetch("/api/qr/items?lang=" + encodeURIComponent(lang()), {cache: "no-store"})).json(); } catch (e) {}
    const it = ((j && j.items) || []).filter(x => x.group === group);
    if (!it.length) { qrShow(location.origin + "/", title); return; }
    qrShow(it[0].url, title, {alt: it.map(x => ({label: x.title, url: x.url, note: x.note}))});
  }
  const AUTO = [
    {sel: "#g-link", get: e => (!e.hidden && e.value) || "", title: "Guest access", o: {secret: true}},
    {sel: '[data-key="notify_url"] input', get: e => ntfyAlt(e.value) ? e.value : "", title: "Push messages (ntfy)",
     o: e => ({secret: true, alt: ntfyAlt(e.value), pick: /iPhone|iPad|iPod/.test(navigator.userAgent) ? 1 : 0})},
    {sel: '[data-key="public_url"] input', get: e => /^https?:\/\/\S+$/.test(e.value.trim()) ? e.value.trim() : "", title: "Address of this page for links"},
    {sel: "#sys-remote", list: "addr", title: "Addresses of MoveEye"}];
  function deco() {
    AUTO.forEach(a => document.querySelectorAll(a.sel).forEach(e => {
      let b = e._qrb;
      if (!b || !b.isConnected) {
        b = a.list ? qrBtn(() => { listShow(a.list, qt(a.title)); return ""; }, qt(a.title))
                   : qrBtn(() => a.get(e), qt(a.title), () => (typeof a.o === "function" ? a.o(e) : a.o) || {});
        b.classList.add("qr-auto"); e.insertAdjacentElement("afterend", b); e._qrb = b;
      }
      b.hidden = !(a.list || a.get(e));
    }));
  }
  let tm = 0; const soon = () => { clearTimeout(tm); tm = setTimeout(deco, 250); };
  const start = () => { deco(); try { new MutationObserver(soon).observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ["hidden"]}); } catch (e) {}
    document.addEventListener("input", soon, true); document.addEventListener("change", soon, true); };
  if (document.body) start(); else document.addEventListener("DOMContentLoaded", start);
})();
"""


def qr_js_tx():
    """the texts of the helper in every language (it is the same on every page; the pages have different dictionaries)"""
    d = {"de": {}, "fr": {}, "it": {}, "rm": {}}
    for k, v in _HX_QR.items():
        d["de"][k] = DE.get(k) or v[0]                          # the German of the rest of the program wins (same word everywhere)
        for i, L in enumerate(("fr", "it", "rm")):
            d[L][k] = TRX[L].get(k) or v[i + 1]
    return d


def qr_js():
    return ("<script>" + QR_JS.replace("/*QRTX*/{}", json.dumps(qr_js_tx(), ensure_ascii=False, separators=(",", ":")), 1)
            .replace('/*QRLANG*/"de"', json.dumps(norm_lang(CFG.get("lang"))), 1).replace("</", "<\\/") + "</script>")


QR_MORE_ITEM = ('<a class="mi" href="/qr" id="m-qr"><i>▦</i><span><b id="m-qr-t">QR codes</b><small id="m-qr-s">All addresses and links to scan and print</small></span>'
                '<span class="ar">›</span></a>\n<script>(function(){var T=window.qrT||function(s){return s;};document.getElementById("m-qr-t").textContent=T("QR codes");'
                'document.getElementById("m-qr-s").textContent=T("All addresses and links to scan and print");})();</script>\n  ')


_render_page_before_qr = render_page


# wraps: render_page
def render_page(page, active):
    """+ the QR helper (qrBtn / qrShow) on every page, and «QR codes» on the page «Mehr»"""
    out = _render_page_before_qr(page, active)
    out = out.replace("</head>", qr_js() + "</head>", 1)
    if active == "more" and 'href="/qr"' not in out:
        i = out.find('<a class="mi" href="/tools">')
        if i >= 0:
            out = out[:i] + QR_MORE_ITEM + out[i:]
    return out


# ---- web: the gallery /qr and the print page /qr/print --------------------------------------------------------------------
QR_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - QR codes</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:980px;margin:0 auto;box-sizing:border-box}
.qg-top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 12px}.qg-top h2{margin:0;flex:1 1 200px;font-size:20px}
.qg-top label{display:flex;gap:6px;align-items:center;font-size:13px}
.qg-h{font-weight:700;margin:16px 0 6px;font-size:15px}
.qg-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}@media(max-width:520px){.qg-grid{grid-template-columns:1fr 1fr;gap:8px}.qg-card .btns button{flex:1 1 100%}}
.qg-card{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:10px;display:flex;flex-direction:column;gap:6px;min-width:0}
.qg-img{background:#fff;border-radius:10px;padding:6px;aspect-ratio:1/1;cursor:zoom-in;position:relative;overflow:hidden}.qg-img svg{width:100%;height:100%;display:block}
.qg-card b{font-size:14px}.qg-url{font-size:11px;word-break:break-all;color:var(--mut);font-family:ui-monospace,Menlo,monospace}
.qg-note{font-size:11px;color:var(--mut)}
.qg-card .btns{display:flex;gap:6px;flex-wrap:wrap}.qg-card .btns button{flex:1 1 auto;min-height:34px;padding:4px 8px}
.qg-sec .qg-img svg,.qg-sec .qg-url{filter:blur(9px)}.qg-sec .qg-img::after{content:attr(data-tap);position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  text-align:center;padding:10px;color:#111;font-weight:700;font-size:13px;background:rgba(255,255,255,.35)}
.qg-lock{font-size:11px;color:var(--org)}
#qg-empty{color:var(--mut)}
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
  <div class="qg-top"><h2 id="qg-title">QR codes</h2>
    <label><input type="checkbox" id="qg-sec"> <span id="qg-sec-l">Print secret codes too</span></label>
    <a class="btn sec" id="qg-all" href="/qr/print?p=1" target="_blank" rel="noopener">🖨 Print all</a></div>
  <div class="mut" id="qg-intro"></div>
  <div id="qg-list">…</div>
</main>
<script>
/*COMMON*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const T = window.qrT || (s => s), $ = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  document.title = "MoveEye – " + T("QR codes");
  $("qg-title").textContent = "▦ " + T("QR codes"); $("qg-sec-l").textContent = T("Print secret codes too"); $("qg-all").textContent = "🖨 " + T("Print all");
  $("qg-intro").textContent = T("All current QR codes for the phone. Secret ones are blurred - tap to show. Each one can be printed.");
  const allHref = () => { $("qg-all").href = "/qr/print?p=1&lang=" + encodeURIComponent(L()) + ($("qg-sec").checked ? "&s=1" : ""); };
  $("qg-sec").onchange = allHref; allHref();
  let j = null; try { j = await (await fetch("/api/qr/items?lang=" + encodeURIComponent(L()), {cache: "no-store"})).json(); } catch (e) {}
  const box = $("qg-list"); box.textContent = "";
  if (!j || !j.ok) { box.appendChild(E("div", "err", "⚠ " + ((j && j.error) || T("Only for the administrator")))); return; }
  const by = {}; (j.items || []).forEach(it => { (by[it.group] = by[it.group] || []).push(it); });
  Object.keys(j.groups).forEach(g => { if (!by[g]) return;
    box.appendChild(E("div", "qg-h", j.groups[g])); const grid = E("div", "qg-grid"); box.appendChild(grid);
    by[g].forEach(it => {
      const c = E("div", "qg-card" + (it.secret ? " qg-sec" : "")); c.dataset.id = it.id; c.dataset.url = it.url;
      const im = E("div", "qg-img"); im.innerHTML = it.svg || ""; im.dataset.tap = "🔒 " + T("Tap to show");
      const opts = it.alt && it.alt.length ? {secret: it.secret, alt: it.alt, pick: /iPhone|iPad|iPod/.test(navigator.userAgent) ? 1 : 0} : {secret: it.secret, note: it.note};
      const big = pr => { if (c.classList.contains("qg-sec")) { c.classList.remove("qg-sec"); return; } qrShow(it.url, it.title, Object.assign({}, opts, {print: !!pr})); };
      im.onclick = () => big(false);
      c.append(im, E("b", "", it.title), E("div", "qg-url", it.url));
      if (it.note) c.appendChild(E("div", "qg-note", it.note));
      if (it.secret) c.appendChild(E("div", "qg-lock", "🔒 " + T("secret")));
      const bb = E("div", "btns"), b1 = E("button", "sec", "🔍 " + T("Big")), b2 = E("button", "sec", "🖨 " + T("Print"));
      b1.type = b2.type = "button"; b1.onclick = () => { c.classList.remove("qg-sec"); big(false); }; b2.onclick = () => { c.classList.remove("qg-sec"); big(true); };
      bb.append(b1, b2); c.appendChild(bb); grid.appendChild(c);
    }); });
  if (!(j.items || []).length) box.appendChild(E("div", "", T("No codes right now.")));
  box.appendChild(E("div", "mut", "🔑 " + T("App keys show their QR code only once, when they are made (Settings → Security).")));
})();
</script>
</body></html>
"""


def qr_print_page(lang=None, host=None, secrets=False, auto=False):
    """A4 page with labels: QR, name, address (secrets only when asked)"""
    L = norm_lang(lang)
    T = lambda s: tr(s, L)
    groups = {g: T(n) for g, n in QR_GROUPS}
    cards = []
    for it in qr_items(L, host):
        if it["secret"] and not secrets:
            continue
        try:
            svg = qr_svg(it["url"])
        except ValueError:
            continue
        cards.append(f'<div class="lb"><div class="q">{svg}</div><b>{html_escape(it["title"])}</b>'
                     f'<div class="g">{html_escape(groups.get(it["group"], ""))}{" · 🔒 " + html_escape(T("secret")) if it["secret"] else ""}</div>'
                     f'<div class="u">{html_escape(it["url"])}</div>{("<div class=g>" + html_escape(it["note"]) + "</div>") if it["note"] else ""}</div>')
    name = html_escape(str(CFG.get("device_name") or "MoveEye"))
    return ('<!doctype html><html lang="' + L + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="referrer" content="no-referrer"><title>MoveEye – ' + html_escape(T("QR codes")) + '</title><style>'
            '@page{size:A4;margin:12mm}body{font:13px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif;color:#111;background:#fff;margin:0;padding:16px}'
            'h1{font-size:18px;margin:0 0 4px}.m{color:#555;margin:0 0 12px}.bar{display:flex;gap:8px;margin:0 0 12px}.bar button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid #999;background:#f4f4f4;cursor:pointer}'
            '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(58mm,1fr));gap:4mm}'
            '.lb{border:1px dashed #999;border-radius:3mm;padding:3mm;break-inside:avoid;page-break-inside:avoid;text-align:center}'
            '.q{width:40mm;height:40mm;margin:0 auto 2mm}.q svg{width:100%;height:100%;display:block}.lb b{display:block;font-size:11pt}'
            '.g{font-size:8.5pt;color:#555}.u{font:8pt ui-monospace,Menlo,monospace;word-break:break-all;margin-top:1mm}'
            '@media print{.bar,.m.np{display:none}body{padding:0}.grid{grid-template-columns:repeat(3,1fr)}}'
            '</style></head><body><h1>▦ ' + name + ' – ' + html_escape(T("QR codes")) + '</h1>'
            '<div class="m">' + html_escape(datetime.now().strftime("%d.%m.%Y %H:%M")) + ' · ' + html_escape(T("Scan with the phone camera.")) + '</div>'
            '<div class="bar"><button type="button" onclick="print()">🖨 ' + html_escape(T("Print")) + '</button>'
            '<button type="button" onclick="history.length>1?history.back():close()">' + html_escape(T("Close")) + '</button></div>'
            + ('<div class="m np">🔒 ' + html_escape(T("Secret codes are on this page - keep the paper safe.")) + '</div>' if secrets else "")
            + '<div class="grid">' + ("".join(cards) or "<p>" + html_escape(T("No codes right now.")) + "</p>") + '</div>'
            + ('<script>addEventListener("load",function(){setTimeout(function(){try{print();}catch(e){}},300);});</script>' if auto else "")
            + '<script>window.__mwExit = true;</script></body></html>')       # own «Close» (no «✕ Zurück» of 340 on the paper)


def qr_routes(app, reply, body):
    from flask import request, Response, g as g_

    def nope():
        # the administrator only (role_guard already stops other users); an app key may not read the secrets as pictures
        if getattr(g_, "role", "admin") != "admin" or getattr(g_, "appkey", None):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    @app.route("/api/qr", methods=["POST"])
    def api_qr_post():
        n = nope()
        if n is not None:
            return n
        txt = str(body().get("t") or "")[:600]
        try:
            svg = qr_svg(txt or " ")
        except ValueError:
            return Response("too long", 400, headers={"Cache-Control": "no-store"})
        return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "no-store"})

    @app.route("/api/qr/items")
    def api_qr_items():
        n = nope()
        if n is not None:
            return n
        return reply(qr_items_json(request.args.get("lang"), request.host_url))

    @app.route("/qr")
    def qr_gallery():
        n = nope()
        if n is not None:
            return n
        return Response(render_page(QR_PAGE, "more"), mimetype="text/html")

    @app.route("/qr/print")
    def qr_print():
        n = nope()
        if n is not None:
            return n
        return Response(qr_print_page(request.args.get("lang") or CFG["lang"], request.host_url, request.args.get("s") == "1", request.args.get("p") == "1"),
                        mimetype="text/html")

    @app.after_request
    def qr_no_store(resp):                       # secrets (keys, topics, stream addresses, codes) never stay in the browser cache
        try:
            p = request.path
            if p.startswith(QR_SECRET_PATHS) and not resp.headers.get("Cache-Control"):
                resp.headers["Cache-Control"] = "no-store"
        except Exception:
            pass
        return resp


# ---- window (Tkinter): the same as a dialog ---------------------------------------------------------------------------------
def qr_tk_dialog(parent, text, title, secret=False, note="", alts=None):
    """QR picture (qr_png) + the text + Copy, Save picture, Print (lp), Close. alts = [(label, text, note)] for a choice."""
    import base64
    alts = [a for a in (alts or [("", text, note)]) if a and a[1]]
    if not alts:
        return None
    w = tk.Toplevel(parent); w.title("MoveEye – " + tr("QR code")); w.configure(bg=C["panel"])
    try:
        w.transient(parent)
    except tk.TclError:
        pass
    tk.Label(w, text="▦ " + str(title or tr("QR code")), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 12, "bold"), wraplength=380).pack(padx=14, pady=(12, 4))
    cur = {"i": 0}
    seg = tk.Frame(w, bg=C["panel"]); seg.pack(padx=14)
    pic = tk.Label(w, bg="#ffffff"); pic.pack(padx=14, pady=8)
    uv = tk.StringVar(value="")
    tk.Entry(w, textvariable=uv, state="readonly", readonlybackground=C["field"], fg=C["txt"], relief="flat", width=48).pack(fill="x", padx=14)
    nl = tk.Label(w, text="", bg=C["panel"], fg=C["mut"], wraplength=380, justify="center"); nl.pack(padx=14, pady=(4, 0))
    if secret:
        tk.Label(w, text="🔒 " + tr("Secret: whoever scans this code gets access. Show it only to people you trust."), bg=C["panel"], fg=C.get("org", C["txt"]),
                 wraplength=380, justify="center").pack(padx=14, pady=(4, 0))
    st = tk.Label(w, text="", bg=C["panel"], fg=C["mut"]); st.pack()

    def show(i):
        cur["i"] = i; _l, t_, n_ = alts[i]
        try:
            img = tk.PhotoImage(data=base64.b64encode(qr_png(t_, 6)).decode())
        except Exception as e:
            pic.configure(image="", text="⚠ " + str(e)[:80]); return
        pic.configure(image=img); pic.image = img
        uv.set(t_); nl.configure(text=n_ or ""); st.configure(text="")
    if len(alts) > 1:
        for i, (l_, _t, _n) in enumerate(alts):
            ttk.Button(seg, text=l_ or str(i + 1), command=lambda i=i: show(i)).pack(side="left", padx=2)

    def cp():
        try:
            w.clipboard_clear(); w.clipboard_append(alts[cur["i"]][1]); st.configure(text="✓ " + tr("Copied"))
        except tk.TclError:
            pass

    def save():
        from tkinter import filedialog
        p = filedialog.asksaveasfilename(parent=w, defaultextension=".png", initialfile="MoveEye-QR.png", filetypes=[("PNG", "*.png")])
        if p:
            try:
                with open(p, "wb") as f:
                    f.write(qr_png(alts[cur["i"]][1], 10))
                st.configure(text="✓ " + tr("Saved"))
            except OSError as e:
                st.configure(text="⚠ " + str(e)[:80])

    def prn():
        import tempfile
        try:
            fd, p = tempfile.mkstemp(suffix=".png", prefix="moveeye-qr-")
            with os.fdopen(fd, "wb") as f:
                f.write(qr_png(alts[cur["i"]][1], 10))
            subprocess.Popen([shutil.which("lp"), "-o", "fit-to-page", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            st.configure(text="✓ " + tr("Sent to the printer"))
            w.after(60000, lambda: os.path.exists(p) and os.remove(p))
        except (OSError, TypeError) as e:
            st.configure(text="⚠ " + str(e)[:80])
    bf = tk.Frame(w, bg=C["panel"]); bf.pack(fill="x", padx=14, pady=(6, 12))
    ttk.Button(bf, text="📋 " + tr("Copy"), command=cp).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="💾 " + tr("Save picture …"), command=save).pack(side="left", expand=True, fill="x", padx=(0, 4))
    if shutil.which("lp"):
        ttk.Button(bf, text="🖨 " + tr("Print"), command=prn).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text=tr("Close"), command=w.destroy).pack(side="left", expand=True, fill="x")
    show(0)
    return w


def qr_tk_gallery(app):
    """all QR codes of now (like /qr): secrets hidden until «Show»"""
    w = tk.Toplevel(app.root); w.title("MoveEye – " + tr("QR codes")); w.configure(bg=C["panel"])
    tk.Label(w, text="▦ " + tr("QR codes"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
    tk.Label(w, text=tr("All current QR codes for the phone. Secret ones are blurred - tap to show. Each one can be printed."), bg=C["panel"], fg=C["mut"], wraplength=460, justify="left").pack(anchor="w", padx=14)
    cv = tk.Canvas(w, bg=C["panel"], highlightthickness=0, width=500, height=420); sb = ttk.Scrollbar(w, orient="vertical", command=cv.yview)
    fr = tk.Frame(cv, bg=C["panel"]); cv.create_window((0, 0), window=fr, anchor="nw"); cv.configure(yscrollcommand=sb.set)
    fr.bind("<Configure>", lambda _e: cv.configure(scrollregion=cv.bbox("all")))
    sb.pack(side="right", fill="y"); cv.pack(fill="both", expand=True, padx=(14, 0), pady=8)
    groups = {g: tr(n) for g, n in QR_GROUPS}
    items = qr_items(CFG["lang"])
    last = None
    for it in items:
        if it["group"] != last:
            last = it["group"]
            tk.Label(fr, text=groups.get(last, last).upper(), bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 7, "bold"), anchor="w").pack(fill="x", pady=(8, 0))
        row = tk.Frame(fr, bg=C["panel"]); row.pack(fill="x", pady=2)
        lv = tk.StringVar(value=it["title"] + "\n" + ("•••••• (" + tr("secret") + ")" if it["secret"] else it["url"]))
        tk.Label(row, textvariable=lv, bg=C["panel"], fg=C["txt"], wraplength=330, justify="left", anchor="w").pack(side="left", fill="x", expand=True)
        alts = [(a["label"], a["url"], a.get("note", "")) for a in it["alt"]] or None
        ttk.Button(row, text="▦ QR", command=lambda it=it, alts=alts: qr_tk_dialog(w, it["url"], it["title"], it["secret"], it["note"], alts)).pack(side="right")
        if it["secret"]:
            ttk.Button(row, text=tr("Show"), command=lambda lv=lv, it=it: lv.set(it["title"] + "\n" + it["url"])).pack(side="right", padx=(0, 4))
    if not items:
        tk.Label(fr, text=tr("No codes right now."), bg=C["panel"], fg=C["mut"]).pack(anchor="w")
    tk.Label(w, text="🔑 " + tr("App keys show their QR code only once, when they are made (Settings → Security)."), bg=C["panel"], fg=C["mut"],
             wraplength=460, justify="left").pack(anchor="w", padx=14)
    bf = ttk.Frame(w); bf.pack(fill="x", padx=14, pady=(6, 12))
    ttk.Button(bf, text="🖨 " + tr("Print all") + " (" + tr("browser") + ")", command=lambda: app._open_page("/qr/print?p=1")).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text=tr("Close"), command=w.destroy).pack(side="left", expand=True, fill="x")
    return w


def _qr_hint(app, sec, text):
    if app.status_labels.get(sec) is not None:
        app._status(sec, text)
    else:
        messagebox.showinfo("MoveEye", text, parent=app.root)


def _qr_tk_btn(parent, label, cmd):
    b = ttk.Button(parent, text="▦ " + label, command=cmd); b.pack(fill="x", pady=(4, 0)); return b


def _qr_tk_build_section(self, sec, sbody, settings_parent=None):
    _qr_tk_build_section_before(self, sec, sbody, settings_parent)
    try:
        if sec == "Guest access":
            def gq():
                v = self.guest_var.get() if hasattr(self, "guest_var") else ""
                if not v:
                    _qr_hint(self, "Guest access", tr("Create a link first.")); return
                qr_tk_dialog(self.root, v, tr("Guest access"), True, tr("Guests see only the live picture."))
            _qr_tk_btn(sbody, tr("QR code of the link") + " …", gq)
        elif sec == "Web stream":
            def sq():
                lk = ext_links()
                if not lk.get("on"):
                    _qr_hint(self, "Web stream", tr("Off – switch on «Picture for other programs» above.")); return
                alts = [(n, lk.get(k), "") for k, n in (("mjpeg", "MJPEG"), ("jpg", tr("Still picture")), ("rtsp", "RTSP")) if lk.get(k)]
                qr_tk_dialog(self.root, alts[0][1], tr("Picture for other programs"), True,
                             tr("Keep these addresses secret: whoever has them sees the picture without a password."), alts)
            _qr_tk_btn(sbody, tr("QR codes of the addresses") + " …", sq)
        elif sec == "Notifications":
            def nq():
                nu = str(CFG.get("notify_url") or "")
                na = ntfy_app_url(nu, CFG.get("device_name") or "MoveEye") if CFG.get("notify_type") == "ntfy" else ""
                if not na:
                    _qr_hint(self, "Notifications", tr("Enter the ntfy address first (https://server/topic).")); return
                qr_tk_dialog(self.root, na, tr("Push messages (ntfy)"), True, "", [("Android", na, tr("Android: the ntfy app subscribes to the topic by itself.")),
                                                                                  ("iPhone / " + tr("Browser"), nu, tr("iPhone: the ntfy app cannot subscribe from a code - the code opens the topic in the browser. In the app: + and enter the topic."))])
            _qr_tk_btn(sbody, tr("QR code for the ntfy app") + " …", nq)
        elif sec == "Simulator":
            def tq():
                if not CFG.get("tunnel_on"):
                    _qr_hint(self, "Simulator", tr("The tunnel is off (web: Simulator → «Simulator behind a firewall»).")); return
                qr_tk_dialog(self.root, page_address() or f"http://<pi-ip>:{CFG['web_port']}/", tr("Simulator connection (tunnel)"), True,
                             tr("Code") + ": " + tunnel_code() + " · " + tr("In the simulator (Verbindung → «Tunnel zu MoveEye») paste the address and type the code."))
            _qr_tk_btn(sbody, tr("QR code of the tunnel (for a tablet)") + " …", tq)
        elif sec == "Setup":
            _qr_tk_btn(sbody, tr("All QR codes") + " …", lambda: qr_tk_gallery(self))
    except Exception as e:
        log_event("sys", f"Window: QR buttons ({sec}): {e}"[:160])


_qr_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _qr_tk_build_section


# ---- self-test ----------------------------------------------------------------------------------------------------------------
def qr_selftest():
    assert ntfy_app_url("https://ntfy-me.com/mw-abc_12") == "ntfy://ntfy-me.com/mw-abc_12?display=MoveEye"
    assert ntfy_app_url("http://10.0.0.2:8080/x", "Zelt 1").endswith("display=Zelt%201&secure=false")
    assert ntfy_app_url("https://hooks.example.com/a/b") == "" and ntfy_app_url("") == ""
    det = cv2.QRCodeDetector()
    t_ = ntfy_app_url("https://ntfy-me.com/mw-abcdefgh")
    img = cv2.imdecode(np.frombuffer(qr_png(t_, 6), np.uint8), cv2.IMREAD_GRAYSCALE)
    got, _p, _s = det.detectAndDecode(img)
    assert got == t_, f"QR decoded {got!r}"
    items = qr_items("de", "http://192.0.2.1:5000/")
    assert all(set(("id", "group", "title", "url", "secret")) <= set(i) for i in items)
    assert not [i for i in items if i["group"] in ("wifi", "push", "guest", "short", "stream", "tv", "sim") and not i["secret"]], "secret without the mark"
    js = qr_js()
    assert "window.qrBtn" in js and "/*QRTX*/" not in js and "</script" not in js[8:-9]
    for k in _HX_QR:
        assert "ß" not in _HX_QR[k][0], k
    p = render_page("<html><head></head><body></body></html>", "more")
    assert "window.qrShow" in p


SELFTEST_EXTRA.append(("QR codes (ntfy link, gallery, helper)", qr_selftest))
