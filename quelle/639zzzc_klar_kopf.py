#@ MoveEye – Teil 639zzzc: Design «Klar», Etappe 2 – der Kopf (Besitzer 2026-11): Reiter mit einem Linien-Symbol über dem Wort (Handy) bzw. daneben (PC), der aktive Reiter hell hinterlegt; die vier Kopf-Knöpfe als ruhige Linien-Symbole; ein Symbolsatz (SVG, Daten-ZIP) für Web und Fenster. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer: «Kopf wie im Entwurf A (A_einst, A_live)»; das Logo (orange Kegel mit der roten Figur + Schriftzug «MoveEye») bleibt
# GROSS wie heute (144, einzeilig seit Etappe 1). Hier:
#   * MWI: der Symbolsatz (24 × 24, Strich 1.8, runde Enden) - eine Tabelle {Name: SVG-Inhalt}; auf jeder Seite mit Reitern ein
#     unsichtbares <svg> mit den <symbol id="mwi-…"> (MWI_SPRITE_HTML), die Reiter zeigen <use href="#mwi-…">.
#   * nav_html(): jedem Reiter sein Symbol (Live = Auge, Schutz = Schild, Verlauf = Uhr mit Pfeil, Einstellungen = Regler,
#     Simulator = Würfel, Mehr = vier Kacheln); die kurzen Namen für das Handy - «Schutz» / «Verlauf» bekommen eigene kurze
#     Schlüssel, damit sie auch auf Französisch, Italienisch und Rätoromanisch in einen Reiter passen (DejaVu, 390 px).
#   * KLAR_KOPF_CSS: Handy - eine Reiterzeile, Symbol über dem Wort, 52 px hoch; PC - Symbol neben dem Wort; aktiver Reiter
#     hell hinterlegt (--acc-soft), kein Punkt. Kopf-Knöpfe ohne Rahmen, 44 px, Linien-Symbole wie die Reiter.
#   * Fenster (Tk kann kein SVG): MWI_TK - dieselben Symbole als Alpha-Masken 20 × 20, erzeugt aus MWI mit
#     werkzeuge/symbole_tk.py; tk_icon(name, farbe) macht daraus zur Laufzeit ein PNG in der Farbe des Themas (ohne
#     Zusatzbibliothek, zlib). Die Reiter des Fensters zeigen Symbol + Wort (570 _build_header / _paint_tabs).
# ----------------------------------------------------------------------------
MWI = {
    "live": '<path d="M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5S2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "protect": '<path d="M12 3l7.5 3v5.5c0 4.6-3.1 8.2-7.5 9.5-4.4-1.3-7.5-4.9-7.5-9.5V6z"/>',
    "history": '<path d="M3.5 12a8.5 8.5 0 1 0 2.5-6"/><path d="M3.5 4.5V8h3.5"/><path d="M12 7.5V12l3 2"/>',
    "settings": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "sim": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
    "more": ('<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/>'
             '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>'),
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.8"/><path d="M12 17h.01"/>',
}
MWI_SPRITE_HTML = ('<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">'
                   + "".join('<symbol id="mwi-%s" viewBox="0 0 24 24">%s</symbol>' % (k, v) for k, v in MWI.items()) + "</svg>")
MWI_HELP_SVG = ('<svg class="mwi" viewBox="0 0 24 24" aria-hidden="true">' + MWI["help"] + "</svg>")

# the short names of the tabs on the phone: own keys where the word is too long in a language (fr «Historique», it «Protezione» …)
_HX_KOPF2 = {
    "Protection (tab)": ("Schutz", "Protec.", "Protez.", "Protec."),
    "History (tab)": ("Verlauf", "Histor.", "Cronol.", "Cronol."),
}
for _k, _v in _HX_KOPF2.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
EN_SHOW.update({"Protection (tab)": "Protect", "History (tab)": "History"})
NAV_ITEMS[:] = [(k, h, lab, {"protect": "Protection (tab)", "history": "History (tab)"}.get(k, sh)) for k, h, lab, sh in NAV_ITEMS]

KLAR_KOPF_CSS = r"""<style id="klar-kopf-css">
/* 639zzzc (Klar stage 2): the header - tabs with a line symbol, quiet icon buttons, the active tab lightly filled */
:root{--acc-soft:rgba(59,140,255,.16)}body.light{--acc-soft:rgba(31,111,235,.11)}
.nav a{display:inline-flex;align-items:center;gap:7px}
.nav a .ni{flex:none;width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
.nav a.on{background:var(--acc-soft);color:var(--acc2);box-shadow:none}
body.light .nav a.on{color:var(--acc)}
.nav a .gd-new{position:absolute;top:1px;right:1px;margin:0;font-size:8px;padding:0 4px}
.nav a{position:relative}
.hdr-ctl.mwk>button,.hdr-ctl.mwk>a.btn{background:transparent;border:0;color:var(--mut);box-shadow:none;border-radius:12px}
.hdr-ctl.mwk>button:hover,.hdr-ctl.mwk>a.btn:hover{background:var(--field);color:var(--txt);filter:none}
.hdr-ctl.mwk>button svg,.hdr-ctl.mwk>a.btn svg{stroke-width:1.8}
.hdr-ctl.mwk>button .mwi{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
/* phone: ONE row of six tabs, the symbol above the short word, 52 px high; no box around the row */
@media(max-width:760px){
  header>nav.nav{background:none;border:0;border-radius:0;padding:0 0 4px;gap:2px;overflow:visible;border-bottom:1px solid var(--line);margin:0 -10px;padding-left:6px;padding-right:6px;flex:0 0 calc(100% + 20px);max-width:none;box-sizing:border-box}
  header>nav.nav>a{flex:1 1 0;min-width:0;flex-direction:column;justify-content:center;gap:3px;min-height:52px;padding:5px 1px 4px!important;border-radius:12px;
    font-size:11.5px;line-height:1.15;letter-spacing:0}
  header>nav.nav>a .ni{width:21px;height:21px}
  header>nav.nav>a .nl{display:none!important}
  header>nav.nav>a .ns{display:block!important;max-width:100%;overflow:hidden;white-space:nowrap}
  header>nav.nav>.mwb-grip{align-self:center}
}
@media(max-width:359px){header>nav.nav>a{font-size:10.5px}}
</style>"""


_nav_html_639zzzc = nav_html


# wraps: nav_html
def nav_html(active):                                          # + 639zzzc: the line symbol of every tab
    h_ = _nav_html_639zzzc(active)
    for k, href, _lab, _sh in NAV_ITEMS:
        if k in MWI:
            h_ = re.sub(r'(<a href="%s"(?: class="on")?>)(<span class="nl")' % re.escape(href),
                        r'\1<svg class="ni" aria-hidden="true"><use href="#mwi-%s"/></svg>\2' % k, h_, count=1)
    return h_


_render_page_639zzzc = render_page


# wraps: render_page
def render_page(page, active):                                 # + 639zzzc: the symbols and the header style on every page with tabs
    out = _render_page_639zzzc(page, active)
    if '<nav class="nav">' not in out or "</head>" not in out:
        return out
    out = out.replace("</head>", KLAR_KOPF_CSS + "</head>", 1)
    out = re.sub(r"(<body[^>]*>)", lambda m_: m_.group(1) + MWI_SPRITE_HTML, out, count=1)
    return re.sub(r'(<button class="sec ic" type="button" id="mwk-help" title="[^"]*">)\?</button>', lambda m_: m_.group(1) + MWI_HELP_SVG + "</button>", out, count=1)


# ---- the window (Tkinter): the same symbols as small pictures in the colour of the theme --------------------------------------------
# MWI_TK = {name: base64 of zlib(20 × 20 alpha bytes)} - made by werkzeuge/symbole_tk.py from MWI (Chromium draws the SVG)
MWI_TK_SIZE = 20
_TK_ICONS = {}


def tk_icon_png(name, color):
    """PNG bytes of a symbol in one colour (#rrggbb) - from its alpha mask, plain zlib (no extra library)"""
    import base64 as _b64
    import struct as _st
    import zlib as _z
    m = MWI_TK.get(name)
    if not m:
        return b""
    a = _z.decompress(_b64.b64decode(m))
    n = MWI_TK_SIZE
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    raw = b"".join(b"\x00" + b"".join(bytes((r, g, b, a[y * n + x])) for x in range(n)) for y in range(n))

    def chunk(t, d):
        return _st.pack(">I", len(d)) + t + d + _st.pack(">I", _z.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", _st.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0)) + chunk(b"IDAT", _z.compress(raw, 9))
            + chunk(b"IEND", b""))


def tk_icon(name, color):
    """a tk.PhotoImage of the symbol in the colour (kept, so Tk does not lose it); None without Tk / without the symbol"""
    k = (name, color)
    if k in _TK_ICONS:
        return _TK_ICONS[k]
    try:
        import base64 as _b64
        png = tk_icon_png(name, color)
        im = tk.PhotoImage(data=_b64.b64encode(png).decode()) if png else None
    except Exception:
        im = None
    _TK_ICONS[k] = im
    return im


def klar_kopf_selftest():
    h_ = nav_html("settings")
    assert all('<use href="#mwi-%s"/>' % k in h_ for k in ("live", "protect", "history", "settings", "sim", "more")), "639zzzc: symbols of the tabs"
    assert h_.count('class="on"') == 1 and 'data-i18n="Protection (tab)"' in h_ and 'data-i18n="History (tab)"' in h_, "639zzzc: short names"
    for k, v in _HX_KOPF2.items():
        assert DE[k] == v[0] and all(TRX[L].get(k) for L in ("fr", "it", "rm")) and len(max(v, key=len)) <= 7, "639zzzc: short " + k
    p = render_page("<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>", "live")
    assert p.count('id="mwi-live"') == 1 and "klar-kopf-css" in p, "639zzzc: sprite / css once"
    assert 'id="mwk-help"' not in p or MWI_HELP_SVG in p, "639zzzc: the help button as a line symbol"
    assert set(MWI_TK) == set(MWI), "639zzzc: window symbols = web symbols (werkzeuge/symbole_tk.py)"
    png = tk_icon_png("live", "#3b8cff")
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 60, "639zzzc: window symbol as PNG"
    return "6 tabs with symbols, short names fit (≤ 7 letters), %d window symbols" % len(MWI_TK)


SELFTEST_EXTRA.append(("Design «Klar» stage 2: header (639zzzc)", klar_kopf_selftest))
