#@ MoveEye – Teil 639zj: «Fertig kaufen» – Hinweis oben auf «Bauen» (/build, auch für die 3D-Werkstatt im Browser): «Keine Lust zu basteln? MoveEye gibt es auch fixfertig – Basis, Komplett oder Autark», Knopf «Fertig bestellen (Anfrage)» öffnet die Rückmeldung (584) mit Art «Bestellung fertiges Gerät» (370 FB_KINDS «order») und dem Paket; Kontakt Pflicht, nur in der Nachricht, nie im Protokoll; Preise auf Anfrage; Texte und Pakete aus ui_gemeinsam.json «fertig» (5 Sprachen, gleich im Simulator werkstatt.gd / feedback.gd); Selbsttest. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Besitzer (01.11.2026): auf der Bastel- bzw. Werkstatt-Seite soll jeder sehen, dass man MoveEye auch fixfertig kaufen kann.
#   * Eine Quelle: simulator3d/ui_gemeinsam.json «fertig» (kind, emoji, draw, standard, texts {hint, button, topic, price,
#     package, contact, contact_note, contact_needed, text}, pakete [{id, names, desc}]) - MoveEye (eingebettet als
#     UI_GEMEINSAM, 639p) und der Simulator (scripts/ui_gemeinsam.gd fertig_*) zeigen dieselben Texte.
#   * /build (639w): #g-fertig ganz oben, Paket-Wahl (pro Browser gemerkt, localStorage mw-fertig-pkg), Kurzbeschrieb + «Preise
#     auf Anfrage», Knopf -> mwOrder(paket) (584); ohne Rückmeldungs-Skript: #order.
#   * Rückmeldung (584 mwFeedback {kind: "order", pkg}): fünfte Art nur in diesem Fall, Paket umschaltbar, Text vorausgefüllt,
#     Feld «Kontakt (E-Mail/Telefon)» Pflicht (auch feedback_send prüft das), keine technischen Angaben / kein Bild als Standard.
#   * Pi-Fenster (Besitzer 01.11.2026): Reiter Mehr zeigt unter den Knöpfen denselben Hinweis mit «Fertig bestellen (Anfrage)»
#     -> App._feedback("order", paket) (584: fünfte Art, Paket-Wahl, Text vorausgefüllt, Kontakt Pflicht).
#   * feedback_send (370): «Paket: … (…) · Preis auf Anfrage» in der Nachricht; der Kontakt steht nur in der Nachricht (Ausgang
#     bis gesendet), log_event schreibt ihn nie.
# Hier (nach 639w) weil UI_GEMEINSAM (639p), geh_page (639w), FBX_JS (584), FB_KINDS / feedback_send (370) vorher kommen.
# ----------------------------------------------------------------------------
FERTIG = UI_GEMEINSAM.get("fertig") or {}
FERTIG_LANGS = ("de", "en", "fr", "it", "rm")
FERTIG_ERR = "please enter a contact (e-mail or phone)"            # the error of feedback_send (370) for an order without contact


def _fk_l5(d, lang):
    """a text in de / en / fr / it / rm, the same fallback as the pages (rm -> de, fr / it -> en -> de)"""
    if not isinstance(d, dict):
        return str(d or "")
    for c in [lang] + {"en": ["de"], "fr": ["en", "de"], "it": ["en", "de"], "rm": ["de"]}.get(lang, ["de"]):
        if d.get(c):
            return d[c]
    return d.get("de", "")


def fertig_text(k, lang="de"):
    return _fk_l5((FERTIG.get("texts") or {}).get(k), norm_lang(lang) if lang else "de")


def fertig_paket(pid, lang="de"):
    """{id, name, desc} of a package; an unknown id -> the standard one (Komplett)"""
    ps = FERTIG.get("pakete") or []
    p = next((x for x in ps if x.get("id") == pid), None) or next((x for x in ps if x.get("id") == FERTIG.get("standard")), None) or (ps[0] if ps else {})
    return {"id": p.get("id", ""), "name": _fk_l5(p.get("names"), lang), "desc": _fk_l5(p.get("desc"), lang)} if p else {}


# the error message of feedback_send in the pages' languages (English = key)
_fk_cn = (FERTIG.get("texts") or {}).get("contact_needed") or {}
if _fk_cn:
    DE.setdefault(FERTIG_ERR, _fk_cn.get("de", FERTIG_ERR))
    for _L in ("fr", "it", "rm"):
        TRX.setdefault(_L, {}).setdefault(FERTIG_ERR, _fk_cn.get(_L) or _fk_cn.get("de", FERTIG_ERR))
if FERTIG.get("texts"):
    FB_KINDS["order"] = fertig_text("topic", "de")                  # the title of the message: «MoveEye – Bestellung fertiges Gerät»

if GUI_OK and FERTIG.get("texts"):                    # the window: the same hint below the buttons of the tab «Mehr» (next to «Bauen»)
    _fk_tk_more_base = App._tk_more_bar

    def _fk_tk_more_bar(self, parent):
        f = _fk_tk_more_base(self, parent)
        fl = norm_lang(CFG.get("lang"))
        n = len(f.grid_slaves())
        row = tk.Frame(f, bg=C["panel"], highlightthickness=1, highlightbackground=C["acc"])
        row.grid(row=(n + 2) // 3, column=0, columnspan=3, sticky="ew", pady=(4, 6))
        tk.Label(row, text="🛒 " + fertig_text("hint", fl) + "  ·  " + fertig_text("price", fl), bg=C["panel"], fg=C["txt"],
                 font=("DejaVu Sans", 9), wraplength=480, justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=6)
        self._fbtn(row, fertig_text("button", fl), lambda: self._feedback("order", FERTIG.get("standard", ""))).pack(side="right", padx=8, pady=6)
        self._fk_more_row = row
        return f

    # wraps: App._tk_more_bar (572, after 639w «Bauen»)
    App._tk_more_bar = _fk_tk_more_bar

FERTIG_JS = r"""
// ---- «Fertig kaufen» (639zj): the hint at the top of «Bauen» ----
(function fertig() {
  const FK = /*FK*/null;
  const box = document.getElementById("g-fertig"); if (!box || !FK || !FK.texts) return;
  const PS = FK.pakete || [];
  const Lg = () => (typeof LANG !== "undefined" && LANG) || "en";
  const L5 = d => { if (!d || typeof d !== "object") return d || ""; const l = Lg(); for (const c of [l].concat({en: ["de"], fr: ["en", "de"], it: ["en", "de"], rm: ["de"]}[l] || ["de"])) if (d[c]) return d[c]; return d.de || ""; };
  const FT = k => L5(FK.texts[k]);
  const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  let pkg = FK.standard || (PS[0] || {}).id || "";
  try { const s = localStorage.getItem("mw-fertig-pkg"); if (PS.some(p => p.id === s)) pkg = s; } catch (e) {}
  function paint() {
    box.textContent = "";
    const r1 = mk("div", "fkr"), r2 = mk("div", "fkr");
    const OFF = !window.mwOrder && window.MW_OFFLINE;   // the offline file (639w geh_page(off)): request on the homepage, link only when set
    const ht = mk("span", "fkt", OFF ? t("Ready-made? Request on the MoveEye homepage") : FT("hint"));
    if (OFF && OFF.home) { ht.textContent = ""; const a = mk("a", "", t("Ready-made? Request on the MoveEye homepage")); a.href = OFF.home; a.target = "_blank"; a.rel = "noopener"; ht.appendChild(a); }
    r1.append(mk("span", "fki", FK.emoji || "🛒"), ht);
    const sg = mk("span", "seg"); sg.setAttribute("role", "group"); sg.setAttribute("aria-label", FT("package"));
    PS.forEach(p => { const b = mk("button", p.id === pkg ? "on" : "", L5(p.names)); b.type = "button"; b.title = L5(p.desc); b.dataset.pkg = p.id;
      b.setAttribute("aria-pressed", p.id === pkg ? "true" : "false");
      b.onclick = () => { pkg = p.id; try { localStorage.setItem("mw-fertig-pkg", pkg); } catch (e) {} paint(); }; sg.appendChild(b); });
    const cur = PS.find(p => p.id === pkg) || {};
    const ds = mk("span", "mut", [L5(cur.desc), FT("price")].filter(Boolean).join(" · ")); ds.id = "g-fk-desc";
    const ob = mk("button", "sec", FT("button")); ob.type = "button"; ob.id = "g-fk-btn";
    ob.onclick = () => { if (window.mwOrder) window.mwOrder(pkg); else location.hash = "#order"; };
    if (!window.mwOrder && window.MW_OFFLINE) ob.hidden = true;   // the offline file (639w geh_page(off)): no feedback to the Pi
    r2.append(sg, ds, ob); box.append(r1, r2); box.hidden = false;
  }
  const ai = window.applyI18n;                         // the language changes: the hint follows
  if (typeof ai === "function") window.applyI18n = function () { const r = ai.apply(this, arguments); paint(); return r; };
  window.mwFertigPkg = () => pkg;
  paint();
})();
"""


def fertig_js():
    """the script of the hint on /build (geh_page, 639w)"""
    return FERTIG_JS.replace("/*FK*/null", json.dumps(FERTIG, ensure_ascii=False)).replace("</", "<\\/")


def fertig_selftest():
    F = FERTIG
    assert F.get("kind") == "order" and F.get("texts") and F.get("pakete"), "ui_gemeinsam.json «fertig» missing"
    assert [p["id"] for p in F["pakete"]] == ["basis", "komplett", "autark"] and F.get("standard") == "komplett", "the three packages"
    for k in ("hint", "button", "topic", "price", "package", "contact", "contact_note", "contact_needed", "text"):
        assert all((F["texts"].get(k) or {}).get(L) for L in FERTIG_LANGS), ("text in 5 languages", k)
    for p in F["pakete"]:
        assert all(p["names"].get(L) and p["desc"].get(L) for L in FERTIG_LANGS), ("package in 5 languages", p["id"])
    blob = json.dumps(F, ensure_ascii=False)
    assert "ß" not in blob and "CHF" not in blob and "€" not in blob, "no ß, no fixed prices"
    assert "{paket}" in F["texts"]["text"]["de"] and fertig_text("button", "de") == "Fertig bestellen (Anfrage)"
    assert fertig_text("price", "fr") == F["texts"]["price"]["fr"] and fertig_paket("x")["id"] == "komplett" and fertig_paket("autark", "it")["name"] == "Autonomo"
    assert FB_KINDS.get("order") == "Bestellung fertiges Gerät" and tr_err(FERTIG_ERR, "de") != FERTIG_ERR, "kind / error text"
    # the page /build: the hint at the top, the script without placeholder
    html = geh_page()
    assert html.index('id="g-fertig"') < html.index('class="gc gtop"') and "mwOrder" in html and "/*FK*/" not in html and '"komplett"' in html, "/build hint"
    js = fbx_ui_js()
    assert "window.mwOrder" in js and "/*FERTIG*/" not in js and '"contact_needed"' in js, "feedback dialog: order"
    # feedback_send: the order needs a contact, the package is in the message, the contact never in the log
    logged, saved = [], []
    keep = {n: globals()[n] for n in ("feedback_flush", "_fb_load", "_fb_save", "_fb_shots_tidy", "log_event")}
    sent = list(FEEDBACK["sent"])
    try:
        globals().update(feedback_flush=lambda: None, _fb_load=lambda: [], _fb_save=lambda b: saved.extend(b), _fb_shots_tidy=lambda b: None,
                         log_event=lambda k, t: logged.append(str(t)))
        FEEDBACK["sent"] = []
        ok, err = feedback_send("order", "Ich möchte MoveEye fixfertig", "", False, 0, "build", None, "web", "autark")
        assert not ok and err == FERTIG_ERR, "order without contact"
        ok, err = feedback_send("order", "Ich möchte MoveEye fixfertig", "test@example.invalid", False, 0, "build", None, "web", "autark")
        assert ok and saved and saved[-1]["kind"] == "order", err
        b = saved[-1]["body"]
        assert "Paket: Autark (mit Akku und Ladequelle) · Preis auf Anfrage" in b and "Kontakt: test@example.invalid" in b, b[:200]
        assert logged and not any("example.invalid" in x for x in logged), "contact in the log"
        ok, _e = feedback_send("idea", "ein Wunsch ohne Kontakt", "", False, 0, "build", None, "web", "autark")
        assert ok and "Paket:" not in saved[-1]["body"], "a normal feedback has no package"
    finally:
        globals().update(keep)
        FEEDBACK["sent"] = sent
    if GUI_OK:
        assert App._tk_more_bar is _fk_tk_more_bar and "pkg" in App._feedback.__code__.co_varnames, "window: hint and order"
    # the simulator shows the same (only in the repository)
    sd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "scripts")
    if os.path.isdir(sd):
        for fn, need in (("werkstatt.gd", ("_fertig_bar", "UG.fertig_text(\"hint\"", "open_order")), ("feedback.gd", ("func open_order", "\"pkg\": _pkg", "contact_needed")),
                         ("ui_gemeinsam.gd", ("static func fertig_text", "static func fertig_paket"))):
            with open(os.path.join(sd, fn), encoding="utf-8") as f_:
                src = f_.read()
            assert all(x in src for x in need), ("simulator", fn)
    return "Ready-made: hint on /build, order in the feedback (package, contact needed, not in the log), the same texts as the simulator"


SELFTEST_EXTRA.append(("Ready-made device: hint on /build, order over the feedback (639zj)", fertig_selftest))
