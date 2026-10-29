#@ MoveEye – Teil 584: Rückmeldung von überall (💬 auf jeder Seite, Fenster, Simulator; Art, Sterne, Bildschirmfoto) und «Über MoveEye» (Geschichte, Entwickler, Zeitleiste, Zahlen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.33 (Wunsch Daniel):
#   A) Rückmeldung an den Entwickler von überall: ein dezentes 💬 im Kopf jeder Webseite (ein Dialog für alle Seiten, hier
#      im Skript /fbx/ui.js), im Fenster (💬 im Kopf, Reiter Mehr, Einstellungen) und im 3D-Simulator (Knopf → mw_cmd
#      «feedback», 350). Art Fehler / Wunsch / Lob / Frage, «Wie zufrieden?» 1–5 Sterne, Version und Seite immer dabei,
#      «Bildschirmfoto mitschicken» (Web: das aktuelle Live-Bild – ein Bild der Seite selbst kann der Browser nicht machen;
#      Fenster: das Fenster, sonst das Live-Bild; Simulator: sein Bild /view.jpg), Gesichter verpixelt (375), höchstens
#      FB_SHOT_MAX. Gesendet wird wie bisher von feedback_send / feedback_flush (370): Text als ntfy-Nachricht, das Bild als
#      zweite Nachricht mit Anhang (PUT, wie die Alarm-Pushes mit Bild).
#   B) «Über MoveEye»: Antippen der Versionsnummer neben dem Logo (Web und Fenster; ein einzelnes Tippen – 7× schnell
#      bleibt für die kleine Überraschung) und «Über MoveEye» unten in Mehr. Geschichte, Entwickler «Daniel alias Elektro»,
#      Zeitleiste, Zahlen (zur Laufzeit gezählt), aufklappbar «Für Technik-Interessierte». Texte: 622.
# ----------------------------------------------------------------------------
INFO_PARTS = 152                       # number of parts in quelle/ (written by werkzeuge/bauen.py --neue-version)
INFO_START = "2026-10-16"              # the first lines (a small webcam program for the Pi 5)
FBX = {"shot": None, "shot_t": 0.0, "lines": 0}

# the milestones: (date or "", version, text) - dates from the chats and the git history, versions from the change list
INFO_TIMELINE = [
    ("16.10.2026", "", "The first lines: a small program reads the USB webcam of the Raspberry Pi 5 and marks movement in red - Motion Watch begins"),
    ("18.10.2026", "1.2", "AI marks persons and objects; web page with camera control; desktop window"),
    ("", "1.5", "Thermal camera over the picture"),
    ("", "1.7", "Camping: own Wi-Fi, armed / disarmed with countdown"),
    ("23.10.2026", "2.0", "Animal diary, night report, remote access"),
    ("", "2.28", "Five languages (with Romansh)"),
    ("", "2.70", "Simulator inside the program"),
    ("26.10.2026", "2.90", "3D simulator with six scenes"),
    ("27.10.2026", "2.95.29", "Game corner for the campfire"),
    ("28.10.2026", "2.95.63", "Program in parts, test bench"),
    ("28.10.2026", "2.95.99", "Training package for an own AI model"),
    ("28.10.2026", "2.96.0", "New name: MoveEye"),
    ("28.10.2026", "2.98.0", "Six tabs"),
    ("29.10.2026", "2.98.20", "AI training and realism"),
    ("29.10.2026", "2.98.30", "Set up the place"),
    ("29.10.2026", "2.98.32", "Controller view for phone and tablet"),
]
INFO_STORY = [
    "MoveEye was born while camping, from a simple question: who keeps an eye on the tent while we sleep or are away? Instead of an expensive alarm system Elektro wanted something of his own - a small camera on a pan / tilt head that recognises wild animals and persons and quietly reports to the phone.",
    "The developer is Elektro (alias Daniel) from Switzerland. Elektro develops robots for a living - but MoveEye was honestly built together with Claude, an AI by Anthropic. Elektro brings the ideas, the wishes and the tests on the real device, Claude writes and explains the code. Out of the joy of tinkering a small webcam script quickly became a whole system - with web page, window, 3D simulator and games for the campfire.",
    "Do you like MoveEye, or does something not work? With 💬 your message reaches Elektro directly - anonymously.",
]
INFO_TECH = [
    "One Python program (OpenCV, Flask, Tkinter) for the Raspberry Pi 5 - edited in {parts} parts, put together into one file with {lines} lines.",
    "Detection: movement (background model), walking pattern, AI model (SSD MobileNet, optionally an own YOLO model trained in the simulator), thermal camera (Waveshare Thermal-90).",
    "The 3D simulator (Godot 4, version {sim}) rebuilds the place - persons, animals, weather, night - so MoveEye can practise without real nights. The test bench measures every version with it.",
    "Updates come signed over GitHub; push messages over ntfy; remote access over Tailscale.",
]


def info_numbers():
    """counted at run time: versions in the change list (head of this file), lines of this file, parts (bauen.py), languages"""
    if not FBX["lines"]:
        try:
            with open(os.path.abspath(__file__), "rb") as f:
                FBX["lines"] = f.read().count(b"\n")
        except (OSError, NameError):
            FBX["lines"] = 0
    vers = set(re.findall(r"^\s*\*\s*(\d+\.\d+\.\d+):", globals().get("__doc__") or "", re.M))
    try:
        days = (datetime.now().date() - datetime.strptime(INFO_START, "%Y-%m-%d").date()).days
    except ValueError:
        days = 0
    sim = ""
    try:
        sim = str(SIM3D.get("version") or "")
    except NameError:
        pass
    return {"versions": len(vers), "lines": FBX["lines"], "parts": INFO_PARTS, "languages": len(LANGS), "sim": sim, "days": days,
            "version": APP_VERSION}


def _fbx_n(v):
    return f"{v:,}".replace(",", "'") if isinstance(v, int) else str(v)


def about_info(lang=None):
    """everything for the window «About MoveEye» in one language (web: /api/about, window: _about_win)"""
    L = cur_lang(lang); N = info_numbers()
    fmt = {k: _fbx_n(v) for k, v in N.items()}
    return {"ok": True, "lang": L, "title": tr("About MoveEye", L), "version": APP_VERSION,
            "dev": tr("Elektro (alias Daniel)", L), "dev_where": tr("Switzerland", L),
            "story": [tr(x, L) for x in INFO_STORY],
            "tech_title": tr("For the technically interested", L),
            "tech": [trf(x, L, **fmt) for x in INFO_TECH],
            "numbers": [(tr("Versions in the change list", L), fmt["versions"]), (tr("Lines of code", L), fmt["lines"]),
                        (tr("Parts", L), fmt["parts"]), (tr("Languages", L), fmt["languages"] + " (DE · FR · IT · RM · EN)"),
                        (tr("3D simulator", L), fmt["sim"] or "–"), (tr("Days since the first line", L), fmt["days"])],
            "timeline_title": tr("Timeline", L),
            "timeline": [{"d": d, "v": v, "t": tr(t, L)} for d, v, t in INFO_TIMELINE],
            "egg": tr("Psst … there is a hidden easter egg.", L),
            "fb": tr("Feedback to the developer", L)}


# ---- the screenshot that goes with a message --------------------------------------------------------------------------
def _fbx_jpg(img, maxw=1024):
    """small JPEG (faces pixelated, like everything that is shared): at most FB_SHOT_MAX"""
    if img is None:
        return None
    img = img.copy()
    try:
        faces_blur_image(img)                            # (in place)
    except Exception:
        pass
    h, w = img.shape[:2]
    if w > maxw:
        img = cv2.resize(img, (maxw, max(1, int(h * maxw / w))), interpolation=cv2.INTER_AREA)
    for q in (75, 60, 45, 35):
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
        if ok and len(buf) <= FB_SHOT_MAX:
            return buf.tobytes()
        if ok and q == 45:
            img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA)
    return None


def feedback_shot(src="live", root=None):
    """JPEG bytes for «Send a screenshot»: live = the current live picture, sim = the picture of the 3D simulator,
    window = the window of MoveEye (when the screen can be read, else the live picture)"""
    img = None
    if src == "window" and root is not None:
        try:
            from PIL import ImageGrab
            root.update_idletasks()
            x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
            im = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            img = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception:
            img = None
    if src == "sim" and img is None:
        try:
            data, _ = _sim_get("/view.jpg", timeout=4.0)
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            img = None
    if img is None:
        w_ = WATCH_REF.get("w")
        fo = getattr(w_, "frame_out", None) if w_ is not None else None
        img = fo.copy() if fo is not None else None
    return _fbx_jpg(img)


def fbx_web_shot(fresh=True):
    """the live picture for the web dialog: the preview and the message use the same picture (2 minutes)"""
    if fresh or not FBX["shot"] or time.time() - FBX["shot_t"] > 120:
        FBX["shot"] = feedback_shot("live"); FBX["shot_t"] = time.time()
    return FBX["shot"]


# ---- the web page: one script for every page (dialog, info window, 💬 in the header, version number) -----------------
_render_page_before_fbx = render_page


# wraps: render_page
def render_page(page, active):
    """+ the 💬 and «About MoveEye» on every page (not on guest pages)"""
    out = _render_page_before_fbx(page, active)
    if active in ("guest", "info"):
        return out
    i = out.rfind("</body>")
    tag = '<script src="/fbx/ui.js?v=' + APP_VERSION + '" data-page="' + _fbx_esc(str(active)) + '" defer></script>'
    return out[:i] + tag + out[i:] if i >= 0 else out + tag


def _fbx_esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fbx_tx():
    """the texts of the script in de / fr / it / rm (English = the key)"""
    keys = sorted(_HX_INFO.keys())
    out = {"de": {k: DE.get(k, k) for k in keys}}
    for L in ("fr", "it", "rm"):
        out[L] = {k: TRX[L].get(k) or (DE.get(k, k) if L == "rm" else k) for k in keys}
    return out


def fbx_ui_js():
    return FBX_JS.replace("/*FX*/{}", json.dumps(fbx_tx(), ensure_ascii=False)).replace("__VER__", APP_VERSION).replace("</", "<\\/")


FBX_JS = r"""
// ---- 2.98.33: feedback from every page (one dialog) and «About MoveEye» (584) ----
(function fbx() {
  if (window._fbx) return; window._fbx = true;
  const FX = /*FX*/{};
  const me = document.currentScript, PAGE = (me && me.dataset.page) || location.pathname;
  const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "de"; } catch (e) { return "de"; } };
  const T = k => ((FX[L()] || {})[k]) || k;
  const E = (tag, css, txt) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; return e; };
  const POST = async (u, d) => { try { const r = await fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)}); return await r.json(); } catch (e) { return {ok: false, error: String(e)}; } };
  const BOX = "background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:16px;max-width:520px;width:100%;max-height:92vh;overflow:auto;padding:16px;box-sizing:border-box";
  const FIELD = "width:100%;box-sizing:border-box;background:var(--field,#0c121a);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:10px;padding:10px;font:inherit";
  const MUT = "color:var(--mut,#8b9bb0);font-size:13px;line-height:1.45";
  function overlay(id) {
    let ov = document.getElementById(id); if (ov) ov.remove();
    ov = E("div", "position:fixed;inset:0;z-index:320;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center;padding:12px");
    ov.id = id; ov.addEventListener("click", e => { if (e.target === ov) ov.remove(); });
    const b = E("div", BOX); b.setAttribute("role", "dialog"); b.setAttribute("aria-modal", "true"); ov.appendChild(b); document.body.appendChild(ov);
    const esc = e => { if (e.key === "Escape") { ov.remove(); removeEventListener("keydown", esc); } }; addEventListener("keydown", esc);
    return [ov, b];
  }
  function seg(items, cur, on) {                       // a row of buttons, one is chosen
    const r = E("div", "display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 4px"), bs = [];
    items.forEach(([v, lb]) => { const b = E("button", "flex:1 1 auto;min-width:0;padding:7px 8px;font-size:13px", lb); b.type = "button"; b.className = "sec";
      b.onclick = () => { cur = v; bs.forEach(x => { const sel = x._v === cur; x.classList.toggle("on", sel); x.style.borderColor = sel ? "var(--acc,#f59a4a)" : ""; x.setAttribute("aria-pressed", sel); }); on(v); };
      b._v = v; bs.push(b); r.appendChild(b); });
    bs.forEach(x => { const sel = x._v === cur; x.style.borderColor = sel ? "var(--acc,#f59a4a)" : ""; x.setAttribute("aria-pressed", sel); });
    return r;
  }
  // ---- A) the one feedback dialog ----
  window.mwFeedback = function (opt) {
    opt = opt || {};
    const [ov, c] = overlay("fbx-ov");
    let kind = opt.kind || "idea", stars = 0;
    c.append(E("h3", "margin:0 0 4px", "💬 " + T("Feedback to the developer")),
             E("div", MUT, T("Errors, wishes, praise, questions - everything helps. The message is sent anonymously: no name, no address, unless you write one.")));
    c.appendChild(seg([["bug", "🐞 " + T("Error")], ["idea", "💡 " + T("Wish")], ["praise", "⭐ " + T("Praise")], ["question", "❓ " + T("Question")]], kind, v => kind = v));
    const sr = E("div", "display:flex;align-items:center;gap:4px;margin:8px 0;flex-wrap:wrap"); sr.appendChild(E("span", MUT + ";margin-right:6px", T("How happy are you?") + " (" + T("optional") + ")"));
    const sb = [], sw = E("span", "display:inline-flex;white-space:nowrap"); sr.appendChild(sw);
    for (let i = 1; i <= 5; i++) { const b = E("button", "background:none;border:0;padding:2px 3px;font-size:24px;line-height:1;cursor:pointer;color:var(--yel,#f5c542);min-height:0", "☆"); b.type = "button";
      b.setAttribute("aria-label", i + " / 5"); b.onclick = () => { stars = stars === i ? 0 : i; sb.forEach((x, j) => x.textContent = j < stars ? "★" : "☆"); }; sb.push(b); sw.appendChild(b); }
    c.appendChild(sr);
    const tx = E("textarea", FIELD); tx.rows = 5; tx.maxLength = 3000; tx.placeholder = T("Your message …");
    const ct = E("input", FIELD + ";margin-top:8px;padding:8px 10px"); ct.type = "text"; ct.maxLength = 120; ct.placeholder = T("Contact for an answer (optional)");
    const chk = (label, on) => { const l = E("label", "display:flex;gap:8px;align-items:flex-start;margin-top:10px;cursor:pointer"); const i = E("input", "margin-top:3px"); i.type = "checkbox"; i.checked = on;
      l.append(i, E("span", MUT, label)); return [l, i]; };
    const [sl, si] = chk(T("Send a screenshot") + " – " + T("the current live picture (faces pixelated). A picture of the page itself is not possible in the browser."), !!opt.shot);
    const pv = E("img", "display:none;max-width:100%;max-height:160px;border-radius:8px;margin-top:6px;border:1px solid var(--line,#1f2b3a)"); pv.alt = "";
    const pvShow = () => { if (si.checked) { pv.src = "/api/fbx/shot.jpg?t=" + Date.now(); pv.style.display = "block"; pv.onerror = () => { pv.style.display = "none"; }; } else pv.style.display = "none"; };
    si.onchange = pvShow;
    const [dl, di] = chk(T("Add technical details (version, device, last important events - no pictures, no passwords)"), true);
    const info = E("div", MUT + ";font-size:12px;margin-top:8px", T("Always included") + ": MoveEye __VER__ · " + T("page") + " «" + PAGE + "»");
    const st = E("div", "color:var(--red,#ff6b6b);font-size:13px;margin-top:6px"), bt = E("div", "display:flex;gap:8px;justify-content:flex-end;margin-top:12px;flex-wrap:wrap");
    const cancel = E("button", "", T("Cancel")), send = E("button", "", T("Send")); cancel.type = send.type = "button"; cancel.className = "sec";
    cancel.onclick = () => ov.remove();
    send.onclick = async () => { send.disabled = true; st.textContent = "";
      const r = await POST("/api/feedback", {kind: kind, stars: stars, text: tx.value, contact: ct.value, diag: di.checked, shot: si.checked, page: PAGE, lang: L()});
      send.disabled = false; if (!r || !r.ok) { st.textContent = "⚠ " + ((r && r.error) || "error"); return; }
      ov.remove(); const m = "✓ " + T("Thank you! The message is on its way.");
      if (typeof toast === "function") toast(m); else { const d = E("div", "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:330;background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--grn,#3ecf8e);border-radius:12px;padding:10px 16px", m); document.body.appendChild(d); setTimeout(() => d.remove(), 3500); } };
    const wq = E("div", MUT + ";font-size:12px;margin-top:8px;display:none");
    bt.append(cancel, send); c.append(tx, ct, sl, pv, dl, info, wq, st, bt); pvShow(); tx.focus();
    fbWaiting(wq);
  };
  // 2.98.33: messages that could not be sent yet - how many, the last refusal, «Send now»
  async function fbWaiting(box, j) {
    if (!j) { try { j = await (await fetch("/api/fbx/status", {cache: "no-store"})).json(); } catch (e) { return; } }
    box.textContent = ""; if (!j || !j.waiting) { box.style.display = "none"; return; }
    box.style.display = "block";
    box.appendChild(E("span", "", "⏳ " + T("{n} feedbacks are still waiting to be sent").replace("{n}", j.waiting) + " "));
    const now = E("button", "padding:3px 9px;font-size:12px;min-height:0;margin-left:4px", T("Send now")); now.type = "button"; now.className = "sec";
    now.onclick = async () => { now.disabled = true; now.textContent = "…"; const r = await POST("/api/fbx/flush", {}); fbWaiting(box, r); };
    box.appendChild(now);
    (j.errors || []).forEach(e => box.appendChild(E("div", "margin-top:3px", T("Last error") + " · " + e.host + ": " + e.why)));
  }
  // 2.98.33: «Send a test feedback» (developer): the result per server
  window.mwFeedbackTest = async function (out) {
    if (out) out.textContent = "…";
    const r = await POST("/api/fbx/test", {lang: L()});
    const txt = r && r.servers && r.servers.length ? r.servers.map(x => (x.ok ? "✓ " : "✗ ") + x.host + (x.ok ? "" : " – " + x.why)).join(" · ") : "⚠ " + ((r && r.error) || "error");
    if (out) out.textContent = txt; else alert(txt);
    return r;
  };
  // ---- B) «About MoveEye» ----
  window.mwAbout = async function () {
    const [ov, c] = overlay("fbx-about");
    c.appendChild(E("div", MUT, "…"));
    let j = null; try { j = await (await fetch("/api/about?lang=" + L(), {cache: "no-store"})).json(); } catch (e) {}
    c.textContent = ""; if (!j || !j.ok) { c.appendChild(E("div", MUT, "⚠")); return; }
    const hd = E("div", "display:flex;align-items:center;gap:12px;margin-bottom:8px");
    const ic = E("img", "width:52px;height:52px;border-radius:12px;flex:none"); ic.src = "/icon-192.png?i=" + (window.MW_ICON || ""); ic.alt = "";
    const ht = E("div"); ht.append(E("div", "font-size:19px;font-weight:700", j.title), E("div", MUT, "MoveEye " + j.version + " · " + j.dev + " · " + j.dev_where));
    hd.append(ic, ht); c.appendChild(hd);
    j.story.forEach(p => c.appendChild(E("p", "margin:8px 0;line-height:1.5;font-size:14.5px", p)));
    const det = E("details", "margin:12px 0 4px;border:1px solid var(--line,#1f2b3a);border-radius:12px;padding:8px 12px"); det.id = "fbx-tech";
    const sm = E("summary", "cursor:pointer;font-weight:600", "🔧 " + j.tech_title); det.appendChild(sm);
    const ul = E("ul", "margin:8px 0;padding-left:18px;line-height:1.5;font-size:13.5px"); j.tech.forEach(x => ul.appendChild(E("li", "", x))); det.appendChild(ul);
    const g = E("div", "display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px;margin:8px 0");
    j.numbers.forEach(([k, v]) => { const b = E("div", "border:1px solid var(--line,#1f2b3a);border-radius:10px;padding:6px 8px"); b.append(E("div", "font-size:17px;font-weight:700", v), E("div", MUT + ";font-size:12px", k)); g.appendChild(b); });
    det.appendChild(g);
    det.appendChild(E("div", "font-weight:600;margin:10px 0 4px", "🗓 " + j.timeline_title));
    const tl = E("div", "border-left:2px solid var(--acc,#f59a4a);margin-left:6px;padding-left:12px");
    j.timeline.forEach(e => { const r = E("div", "margin:0 0 8px;font-size:13.5px;line-height:1.4");
      r.append(E("div", MUT + ";font-size:12px", [e.d, e.v ? "v" + e.v : ""].filter(Boolean).join(" · ")), E("div", "", e.t)); tl.appendChild(r); });
    det.appendChild(tl); c.appendChild(det);
    c.appendChild(E("div", MUT + ";font-style:italic;margin:12px 0 4px;text-align:center", "🤫 " + j.egg));
    const bt = E("div", "display:flex;gap:8px;justify-content:flex-end;margin-top:10px;flex-wrap:wrap");
    const fb = E("button", "", "💬 " + j.fb), cl = E("button", "", T("Close")); fb.type = cl.type = "button"; fb.className = "sec";
    fb.onclick = () => { ov.remove(); mwFeedback(); }; cl.onclick = () => ov.remove();
    bt.append(fb, cl); c.appendChild(bt);
  };
  // ---- the discreet 💬 in the header ----
  function addBtn() {
    const hc = document.querySelector("header .hdr-ctl"); if (!hc || document.getElementById("fbx-b")) return;
    const b = E("button", "font-size:15px"); b.type = "button"; b.id = "fbx-b"; b.className = "sec ic"; b.textContent = "💬";
    b.title = T("Feedback to the developer"); b.setAttribute("aria-label", T("Feedback to the developer"));
    b.onclick = () => mwFeedback(); hc.insertBefore(b, hc.firstChild);
  }
  // ---- the version number next to the logo: one tap = «About MoveEye» (7 quick taps stay the little surprise) ----
  function verTap() {
    const h1 = document.querySelector("header h1"); if (!h1) return;
    const v = h1.querySelector(".ver"); if (!v) return;
    v.style.cursor = "pointer"; v.title = T("About MoveEye"); v.setAttribute("role", "button"); v.tabIndex = 0;
    let tm = 0, last = 0;
    h1.addEventListener("click", e => { const now = Date.now(), quick = now - last < 900; last = now; clearTimeout(tm);
      if (e.target.closest && e.target.closest(".ver") && !quick) tm = setTimeout(() => { if (Date.now() - last >= 600) mwAbout(); }, 650); });
    v.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); mwAbout(); } });
  }
  const byHash = () => { if (location.hash === "#feedback") mwFeedback(); else if (location.hash === "#about") mwAbout(); };
  const go = () => { addBtn(); verTap(); byHash(); };
  addEventListener("hashchange", byHash);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
"""


def fbx_routes(app, watch, reply, body):
    """the web addresses (called once by the web server, 550)"""
    from flask import Response, request

    @app.route("/fbx/ui.js")
    def fbx_ui():
        return Response(fbx_ui_js(), mimetype="application/javascript", headers={"Cache-Control": "no-cache"})

    @app.route("/api/about")
    def api_about():
        return reply(about_info(norm_lang(request.args.get("lang") or CFG["lang"])))

    @app.route("/api/fbx/status")
    def api_fbx_status():
        return reply(dict(feedback_status(), ok=True))

    @app.route("/api/fbx/flush", methods=["POST"])
    def api_fbx_flush():
        """«Send now»: the waiting messages (to both servers)"""
        t_ = threading.Thread(target=feedback_flush, daemon=True); t_.start(); t_.join(40)
        return reply(dict(feedback_status(), ok=True))

    @app.route("/api/fbx/test", methods=["POST"])
    def api_fbx_test():
        """«Send a test feedback» (developer): the result per server"""
        lang = norm_lang(body().get("lang"))
        ok, err, res = feedback_test()
        return reply({"ok": ok, "error": tr(err, lang) if err else None, "servers": res})

    @app.route("/api/fbx/shot.jpg")
    def api_fbx_shot():
        j = fbx_web_shot(True)
        if not j:
            return Response("no picture", 404)
        return Response(j, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


# ---- the window (Tkinter): the same dialog and the info window --------------------------------------------------------
def _fbx_tk_feedback(self, kind="idea"):
    from tkinter import messagebox
    w = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Feedback to the developer")); w.configure(bg=C["bg"])
    ttk.Label(w, text=tr("Errors, wishes, praise, questions - everything helps. The message is sent anonymously: no name, no address, unless you write one."),
              style="Mut.TLabel", wraplength=440, justify="left").pack(padx=14, pady=(12, 6), anchor="w")
    kinds = [("bug", "🐞 " + tr("Error")), ("idea", "💡 " + tr("Wish")), ("praise", "⭐ " + tr("Praise")), ("question", "❓ " + tr("Question"))]
    kv = tk.StringVar(value=kind)
    kf = tk.Frame(w, bg=C["bg"]); kf.pack(fill="x", padx=14)
    for k, lb in kinds:
        ttk.Radiobutton(kf, text=lb, value=k, variable=kv).pack(side="left", padx=(0, 10))
    sf = tk.Frame(w, bg=C["bg"]); sf.pack(fill="x", padx=14, pady=(8, 0))
    ttk.Label(sf, text=tr("How happy are you?") + " (" + tr("optional") + ")", style="Mut.TLabel").pack(side="left", padx=(0, 6))
    stars = {"n": 0}; sbs = []

    def star(i):
        stars["n"] = 0 if stars["n"] == i else i
        for j, b in enumerate(sbs):
            b.config(text="★" if j < stars["n"] else "☆")
    for i in range(1, 6):
        b = tk.Label(sf, text="☆", bg=C["bg"], fg=C.get("yel", "#f5c542"), font=("DejaVu Sans", 16), cursor="hand2")
        b.bind("<Button-1>", lambda e, i=i: star(i)); b.pack(side="left"); sbs.append(b)
    txt = tk.Text(w, height=7, width=54, bg=C.get("field", C["panel"]), fg=C["txt"], insertbackground=C["txt"], relief="flat")
    txt.pack(fill="both", expand=True, padx=14, pady=8)
    cf = tk.Frame(w, bg=C["bg"]); cf.pack(fill="x", padx=14)
    ttk.Label(cf, text=tr("Contact for an answer (optional)"), style="Mut.TLabel").pack(side="left")
    ct = ttk.Entry(cf); ct.pack(side="left", fill="x", expand=True, padx=(8, 0))
    shot = tk.BooleanVar(value=False); diag = tk.BooleanVar(value=True)
    ttk.Checkbutton(w, text=tr("Send a screenshot") + " (" + tr("the window, faces pixelated") + ")", variable=shot).pack(anchor="w", padx=14, pady=(8, 0))
    ttk.Checkbutton(w, text=tr("Add technical details (version, device, last important events - no pictures, no passwords)"), variable=diag).pack(anchor="w", padx=14)
    ttk.Label(w, text=tr("Always included") + f": MoveEye {APP_VERSION} · " + tr("page") + " «" + tr("Window") + "»", style="Mut.TLabel").pack(anchor="w", padx=14, pady=(6, 0))
    st_ = feedback_status()
    if st_["waiting"]:                                   # 2.98.33: messages still waiting, the last refusal, «Send now»
        wf = tk.Frame(w, bg=C["bg"]); wf.pack(fill="x", padx=14, pady=(6, 0))
        wl = ttk.Label(wf, text="⏳ " + tr("{n} feedbacks are still waiting to be sent").replace("{n}", str(st_["waiting"])) + "".join(
            "\n" + tr("Last error") + " · " + e["host"] + ": " + e["why"] for e in st_["errors"]), style="Mut.TLabel", justify="left")
        wl.pack(side="left")

        def now_():
            threading.Thread(target=lambda: (feedback_flush(), self.root.after(0, lambda: wl.winfo_exists() and wl.config(
                text="⏳ " + tr("{n} feedbacks are still waiting to be sent").replace("{n}", str(feedback_status()["waiting"]))))), daemon=True).start()
        ttk.Button(wf, text=tr("Send now"), command=now_).pack(side="right")
    bf = ttk.Frame(w); bf.pack(fill="x", padx=14, pady=10)

    def send():
        img = None
        if shot.get():
            w.withdraw(); self.root.update(); time.sleep(0.15)       # the picture without this little window
            try:
                img = feedback_shot("window", self.root)
            finally:
                w.deiconify()
        page = "Fenster/" + str(getattr(self, "tab", "") or "")
        ok, err = feedback_send(kv.get(), txt.get("1.0", "end"), ct.get().strip(), diag.get(), stars["n"], page, img, "window")
        if ok:
            messagebox.showinfo("MoveEye", tr("Thank you! The message is on its way."), parent=w); w.destroy()
        else:
            messagebox.showerror("MoveEye", tr_err(err), parent=w)
    ttk.Button(bf, text=tr("Send"), command=send).pack(side="right")
    ttk.Button(bf, text=tr("Cancel"), command=w.destroy).pack(side="right", padx=(0, 6))
    txt.focus_set()


def _fbx_tk_about(self):
    j = about_info()
    w = tk.Toplevel(self.root); w.title("MoveEye – " + j["title"]); w.configure(bg=C["bg"])
    head = tk.Frame(w, bg=C["bg"]); head.pack(fill="x", padx=16, pady=(14, 4))
    try:
        import base64
        self._about_logo = tk.PhotoImage(data=base64.b64encode(app_icon_png(48)).decode())
        tk.Label(head, image=self._about_logo, bg=C["bg"]).pack(side="left", padx=(0, 10))
    except Exception:
        pass
    hf = tk.Frame(head, bg=C["bg"]); hf.pack(side="left", fill="x")
    tk.Label(hf, text=j["title"], bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 14, "bold"), anchor="w").pack(anchor="w")
    tk.Label(hf, text=f"MoveEye {j['version']} · {j['dev']} · {j['dev_where']}", bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), anchor="w").pack(anchor="w")
    for p in j["story"]:
        tk.Label(w, text=p, bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 10), wraplength=520, justify="left", anchor="w").pack(fill="x", padx=16, pady=4)
    tech = tk.Frame(w, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=12, pady=8)
    shown = {"on": False}

    def fold():
        shown["on"] = not shown["on"]
        tb.config(text=("▾ " if shown["on"] else "▸ ") + j["tech_title"])
        if shown["on"]:
            tech.pack(fill="x", padx=16, pady=(0, 6), after=tb)
        else:
            tech.pack_forget()
    tb = self._fbtn(w, "▸ " + j["tech_title"], fold); tb.pack(anchor="w", padx=16, pady=(8, 4))
    for x in j["tech"]:
        tk.Label(tech, text="• " + x, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 9), wraplength=500, justify="left", anchor="w").pack(fill="x", pady=1)
    nf = tk.Frame(tech, bg=C["panel"]); nf.pack(fill="x", pady=(6, 4))
    for i, (k, v) in enumerate(j["numbers"]):
        c_ = tk.Frame(nf, bg=C["panel"]); c_.grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 16), pady=2)
        tk.Label(c_, text=v, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold")).pack(anchor="w")
        tk.Label(c_, text=k, bg=C["panel"], fg=C["mut"], font=("DejaVu Sans", 8)).pack(anchor="w")
    tk.Label(tech, text=j["timeline_title"], bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x", pady=(6, 2))
    tl = tk.Text(tech, height=9, width=64, bg=C["panel"], fg=C["txt"], relief="flat", font=("DejaVu Sans", 9), wrap="word", highlightthickness=0)
    tl.tag_configure("m", foreground=C["mut"])
    for e in j["timeline"]:
        tl.insert("end", " · ".join(x for x in (e["d"], ("v" + e["v"]) if e["v"] else "") if x) + "\n", "m")
        tl.insert("end", e["t"] + "\n\n")
    tl.config(state="disabled"); tl.pack(fill="both", expand=True)
    tk.Label(w, text="🤫 " + j["egg"], bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9, "italic")).pack(pady=(8, 2))
    bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=16, pady=(4, 12))
    self._fbtn(bf, tr("Close"), w.destroy, primary=True).pack(side="right")
    self._fbtn(bf, "💬 " + j["fb"], lambda: (w.destroy(), self._feedback())).pack(side="right", padx=(0, 6))


def _fbx_tk_ver_tap(self, _e=None):
    """a single tap on the version number: «About MoveEye»; quick taps (the little surprise) open nothing"""
    now = time.time()
    last = getattr(self, "_ver_last", 0.0); self._ver_last = now
    try:
        self.root.after_cancel(self._ver_job)
    except Exception:
        pass
    if now - last < 0.9:
        return
    self._ver_job = self.root.after(650, lambda: self._about_win() if time.time() - self._ver_last >= 0.6 else None)


App._feedback = _fbx_tk_feedback
App._about_win = _fbx_tk_about
App._ver_tap = _fbx_tk_ver_tap


def fbx_selftest():
    j = about_info("de")
    assert j["numbers"] and j["timeline"] and len(j["story"]) == 3, "about_info incomplete"
    assert all("{" not in x for x in j["tech"]), "placeholder left in the technical text"
    assert "ß" not in json.dumps(j, ensure_ascii=False), "German with ß"
    out = render_page("<html><head></head><body><header><h1>MoveEye</h1></header></body></html>", "live")
    assert "/fbx/ui.js" in out, "script not on the page"
    assert "/fbx/ui.js" not in render_page("<html><head></head><body></body></html>", "guest"), "script on a guest page"
    assert all(x in (HELP_X.get(L) or "") for L, x in (("fr", "À propos de MoveEye"), ("it", "Informazioni su MoveEye"), ("rm", "Davart MoveEye"))), "manual fr / it / rm"
    assert "Über MoveEye" in HELP_PAGE, "manual de"
    miss = [k for k in _HX_INFO if not all(_HX_INFO[k])]
    assert not miss, f"texts without translation: {miss[:3]}"
    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(fbx_ui_js()); fn = f.name
        r = subprocess.run([node, "--check", fn], capture_output=True, text=True)
        os.remove(fn)
        assert r.returncode == 0, "fbx/ui.js: " + (r.stderr.strip().splitlines()[-1] if r.stderr else "error")
    N = info_numbers()
    return f"{N['versions']} versions, {N['lines']} lines, {N['parts']} parts" + ("" if node else " (JavaScript not checked)")


SELFTEST_EXTRA.append(("Feedback from everywhere, «About MoveEye»", fbx_selftest))
