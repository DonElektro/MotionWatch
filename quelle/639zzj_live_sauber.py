#@ MoveEye – Teil 639zzj: «Live-Bild sauber» – die Knöpfe auf dem Live-Bild (🎮, 🔍, 📷, Ansicht, Vollbild …) und die Kamera-Kacheln (639zzi, #v3-mini) sind ab Werk versteckt; Antippen des Bildes (PC: Maus darüber, Tastatur: Tab) zeigt sie 4 s, jede Berührung startet die 4 s neu, danach blenden sie weich aus; offene Menüs / Untersuchen / Steuern halten sie sichtbar. Schalter «Knöpfe im Live-Bild immer zeigen» (Einstellungen → Netzwerk & Zugang → Web-Stream, pro Browser). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (10.11.2026, Bildschirmfoto iPhone, Reiter Live, Experte): das Live-Bild ist zu voll. Entscheid:
#   * Ab Werk startet das Live-Bild sauber: die Knöpfe oben (#lv-tools: 🎮 Controller-Ansicht 538, 🔍 / 📷 Untersuchen 639zze,
#     🎯 Ansicht 639zv, ◫ Ansicht 536, ⛶ Vollbild, ☰ im kleinen Fenster) und die Kamera-Kacheln (#kw-row 639zzi, #v3-mini 639zv)
#     sind unsichtbar. Im Vollbild ebenso ✕ / ⇆ / 🚜 oben rechts (#vo-exit, #vo-side, #vo-mv). «LIVE», «● REC» und der Name der
#     Kamera unten (.vtag, #v3-tag) bleiben immer sichtbar; der Joystick (#lv-joy, #vo-ctl) bleibt, wie er ist.
#   * Antippen des Bildes zeigt sie 4 s (LVK_MS); jede Berührung / Bedienung eines Knopfs oder einer Kachel startet die 4 s neu,
#     danach weich ausblenden (Opacity). Offen ist ein Menü / eine Liste («⋯ Kameras» #kw-menu, Ansicht #v3-menu / #lv-menu),
#     «Untersuchen» (#unt-bar: Bereich wählen, läuft, Ergebnis; #unt-up), der Bearbeiten-Modus, die Schublade ☰, die
#     Controller-Ansicht (body.pv-on) oder der Finger ist auf dem Joystick: nicht ausblenden, erst 4 s nach dem Schliessen / Ende.
#   * Der erste Tipp aufs Bild zeigt nur: versteckte Knöpfe nehmen keine Berührung an (pointer-events: none) und gezeigt wird erst
#     beim «click» (nach dem Loslassen) - ein Tipp an die Stelle eines versteckten Knopfs löst ihn nicht aus. Was Tipps braucht
#     (Untersuchen: Bereich wählen; Schilder des Ergebnisses), bekommt sie direkt - dann ist die Leiste ohnehin sichtbar (gehalten).
#   * PC: Maus über dem Bild zeigt sie (4 s nach der letzten Bewegung), solange die Maus auf einem Knopf liegt, bleiben sie.
#     Tastatur: Tab auf einen versteckten Knopf zeigt sie (sie bleiben fokussierbar), solange er den Fokus sichtbar hat, bleiben sie.
#   * Versteckte Kacheln holen keine Bilder (data-hold, keepStream 510) - schont den Pi; beim Zeigen kommt zuerst das letzte Bild.
#   * Schalter «Knöpfe im Live-Bild immer zeigen» (Standard aus = sauber) in Einstellungen → Netzwerk & Zugang → «Web-Stream»
#     (dort stehen Qualität und Grösse des Live-Bilds; nur «Experte», wie der ganze Abschnitt). Gespeichert PRO BROWSER
#     (localStorage «mw-lv-knoepfe», WEB_UI_LOCAL), wie die anderen Anzeige-Wahlen des Live-Bilds («mw-live-view» 536,
#     «mw-kamwahl» 639zzi, «mw-view3» 639zv): auf dem Handy will man das Bild frei, am PC vielleicht alles sichtbar.
#   * Gilt für jede Ansicht dieser Seite (Einfach / Experte, hoch / quer / nur Bild, Vollbild). Die Gast-Seite (/g/…) hat keine
#     Knöpfe auf dem Bild (antippen = Vollbild, «🔍 Untersuchen» unter dem Bild) - unverändert. Pi-Fenster (Tk): keine solchen
#     Knöpfe auf dem Bild - unverändert.
# Dazu (Besitzer, Punkt 6): die Kacheln zeigten «USB camera: …» auch auf Deutsch - die Vorsilbe wird übersetzt (639zzi nm(),
# kwCamName), ebenso «Pi camera N». Übersetzungen unten (_HX_LVK, alle 5 Sprachen). Test: werkzeuge/live_sauber_test.py.
# ----------------------------------------------------------------------------
LVK_MS = 4000                                             # ms the buttons stay after the last touch
WEB_UI_LOCAL.add("mw-lv-knoepfe")                         # per browser: "1" = always show the buttons on the live picture

_HX_LVK = {   # English (key): Deutsch, Français, Italiano, Rumantsch
    "Always show the buttons in the live picture": (
        "Knöpfe im Live-Bild immer zeigen", "Toujours afficher les boutons dans l’image en direct",
        "Mostra sempre i pulsanti nell’immagine dal vivo", "Adina mussar ils buttuns en il maletg live"),
    "Off: the live picture stays clean - tap it (PC: move the mouse over it) and the buttons and camera tiles show for 4 seconds. Only on this device (this browser).": (
        "Aus: Das Live-Bild bleibt frei – antippen (PC: Maus darüber), dann erscheinen die Knöpfe und Kamera-Kacheln für 4 Sekunden. Gilt nur auf diesem Gerät (in diesem Browser).",
        "Désactivé : l’image en direct reste dégagée – touche-la (PC : passe la souris dessus) et les boutons et vignettes des caméras s’affichent 4 secondes. Seulement sur cet appareil (ce navigateur).",
        "Spento: l’immagine dal vivo resta libera – toccala (PC: passa sopra con il mouse) e i pulsanti e i riquadri delle telecamere appaiono per 4 secondi. Solo su questo dispositivo (questo browser).",
        "Stizzà: il maletg live resta liber – tutga el (PC: va cun la mieur sur el) ed ils buttuns e las plattinas da las cameras cumparan per 4 secundas. Mo sin quest apparat (quest navigatur)."),
    "USB camera": ("USB-Kamera", "Caméra USB", "Telecamera USB", "Camera USB"),
    "Pi camera": ("Pi-Kamera", "Caméra Pi", "Telecamera Pi", "Camera Pi"),
}
for _k, _v in _HX_LVK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

LVK_JS = r"""
<style id="lvk-css">
/* 639zzj: the buttons and tiles on the live picture - hidden until the picture is tapped (body.lvc-auto without .lvc-show) */
#lv-tools,#kw-row,#v3-mini,#vo-exit,#vo-side,#vo-mv{transition:opacity .2s ease}
body.lvc-auto:not(.lvc-show) #lv-tools,body.lvc-auto:not(.lvc-show) #kw-row,body.lvc-auto:not(.lvc-show) #v3-mini,
body.lvc-auto:not(.lvc-show) #vo-exit,body.lvc-auto:not(.lvc-show) #vo-side,body.lvc-auto:not(.lvc-show) #vo-mv{opacity:0!important;pointer-events:none!important;transition:opacity .7s ease}
body.lvc-auto:not(.lvc-show) #lv-tools button,body.lvc-auto:not(.lvc-show) #kw-row .kw-t{pointer-events:none!important}
body.lvc-auto #lv-tools :focus-visible,body.lvc-auto #kw-row :focus-visible{outline:2px solid #ffd34d;outline-offset:2px}
#lvk-hint{font-size:12px;margin:-2px 0 8px}
</style>
<script>
(function () {
  const tab = document.body.dataset.tab;
  if (tab !== "live" && tab !== "settings") return;
  try { const D = /*LVKDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const KEY = "mw-lv-knoepfe";                            // per browser (WEB_UI_LOCAL): "1" = always show
  const always = () => { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } };
  // ---- the tab «Einstellungen»: the switch in «Web-Stream» (quality and size of the live picture) ----
  if (tab === "settings") {
    const put = () => {
      const sec = document.querySelector('#settings [data-view="sec:Web stream"]');
      if (!sec || sec.querySelector("#lvk-row")) return;
      const box = sec.querySelector(":scope > .blk") || sec;
      const row = E("label", "row tg"); row.id = "lvk-row"; row.dataset.key = KEY;
      const cb = E("input"); cb.type = "checkbox"; cb.className = "sw"; cb.id = "lvk-cb"; cb.checked = always();
      cb.onchange = () => { try { if (cb.checked) localStorage.setItem(KEY, "1"); else localStorage.removeItem(KEY); } catch (e) {}
        try { toast("✓ " + T("Saved")); } catch (e) {} };
      row.append(E("span", "", "👆 " + T("Always show the buttons in the live picture")), cb);
      const hint = E("div", "mut", T("Off: the live picture stays clean - tap it (PC: move the mouse over it) and the buttons and camera tiles show for 4 seconds. Only on this device (this browser)."));
      hint.id = "lvk-hint";
      box.insertBefore(hint, box.firstChild); box.insertBefore(row, hint);
    };
    setInterval(put, 1000); setTimeout(put, 300);
    return;
  }
  // ---- the tab «Live» ----
  const B = document.body, HOLD = /*LVKMS*/4000;
  const vw = document.querySelector("#vcard .vwrap");
  if (!vw) return;
  const OV = "#lv-tools, #kw-row, #v3-mini, #vo-exit, #vo-side, #vo-mv";
  const POP = ["kw-menu", "v3-menu", "lv-menu", "unt-bar", "unt-up"];
  const inOv = x => !!(x && x.closest && x.closest(OV + ", #kw-menu, #v3-menu, #lv-menu"));
  const STICK = "#lv-joy, #stick, #mstick, #vo-ctl, #vo-mctl";
  let last = 0, shown = false, onStick = false, mouseOn = false, why = "";
  const open = id => { const x = document.getElementById(id); return !!(x && !x.hidden && x.getClientRects().length); };
  function pinned() {                                     // something is open / being used: do not hide (yet)
    for (const id of POP) if (open(id)) return id;
    for (const c of ["lv-edit", "lv-drawer", "pv-on"]) if (B.classList.contains(c)) return c;
    if (onStick) return "stick";
    if (mouseOn) return "mouse";
    try { const a = document.activeElement; if (a && inOv(a) && a.matches(":focus-visible")) return "focus"; } catch (e) {}
    return "";
  }
  function holdTiles(h) {                                 // hidden tiles fetch no pictures (keepStream 510: data-hold)
    document.querySelectorAll("#kw-row img").forEach(i => { if (h) { if (i.dataset.hold !== "1") i.dataset.hold = "1"; } else if (i.dataset.hold === "1") delete i.dataset.hold; });
  }
  function show(on) {
    if (shown !== on) { shown = on; B.classList.toggle("lvc-show", on); }
    holdTiles(!on && B.classList.contains("lvc-auto"));
  }
  function wake(w) { last = Date.now(); why = w || "touch"; show(true); }
  function mode() {
    const auto = !always();
    B.classList.toggle("lvc-auto", auto);
    if (!auto) show(true); else if (!shown) holdTiles(true);
  }
  // a tap on the picture (click = after the finger is up: a hidden button at that spot does not get this tap)
  vw.addEventListener("click", e => { if (!B.classList.contains("lvc-auto")) return; if (!inOv(e.target)) wake("tap"); });
  // a hidden button never takes the first tap (pointer-events: none; this catches the rest, e.g. a click sent while fading)
  document.addEventListener("click", e => {
    if (B.classList.contains("lvc-auto") && !shown && e.isTrusted && e.detail > 0 && inOv(e.target) && !(e.target.closest && e.target.closest("#kw-menu, #v3-menu, #lv-menu"))) {
      e.preventDefault(); e.stopPropagation(); wake("tap");
    }
  }, true);
  // every touch of a button / tile / its menu: 4 s again
  ["pointerdown", "click", "keydown", "input", "change"].forEach(ev => document.addEventListener(ev, e => { if (inOv(e.target)) wake(ev); }, true));
  document.addEventListener("focusin", e => { if (inOv(e.target)) wake("focus"); });   // keyboard: Tab onto a hidden button shows them
  // steering: the finger on the joystick holds them, 4 s after letting go
  document.addEventListener("pointerdown", e => { if (e.target.closest && e.target.closest(STICK)) onStick = true; }, true);
  const up = () => { if (onStick) { onStick = false; if (shown) wake("stick"); } };
  addEventListener("pointerup", up, true); addEventListener("pointercancel", up, true);
  // PC: the mouse over the picture shows them; on a button they stay
  let mvT = 0;
  vw.addEventListener("pointermove", e => { if (e.pointerType !== "mouse" || !B.classList.contains("lvc-auto")) return; const n = Date.now(); if (n - mvT > 150) { mvT = n; wake("hover"); } });
  document.addEventListener("pointerover", e => { if (e.pointerType === "mouse") mouseOn = inOv(e.target); });
  document.addEventListener("pointerout", e => { if (e.pointerType === "mouse" && !e.relatedTarget) mouseOn = false; });
  setInterval(() => {
    if (!B.classList.contains("lvc-auto")) return;
    const p = pinned();
    if (p) { last = Date.now(); if (!shown) { why = p; show(true); } return; }
    if (shown && Date.now() - last > HOLD) show(false);
    else if (!shown) holdTiles(true);                     // tiles made while hidden
  }, 200);
  addEventListener("storage", e => { if (e.key === KEY || e.key === null) mode(); });
  addEventListener("pageshow", mode);
  window.mwLiveKnoepfe = {state: () => ({auto: B.classList.contains("lvc-auto"), shown: shown, pinned: pinned(), why: why,
    left: shown && B.classList.contains("lvc-auto") ? Math.max(0, HOLD - (Date.now() - last)) : null}), show: () => wake("api"), mode: mode};
  mode();
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", LVK_JS.replace("/*LVKDE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_LVK.items()}, ensure_ascii=False), 1)
                            .replace("/*LVKMS*/4000", str(int(LVK_MS)), 1) + "</body>", 1)

_HELP_LVK = {
    "de": '<li><b>Sauberes Live-Bild:</b> Die Knöpfe auf dem Bild (🎮, 🔍, 📷, Ansicht, Vollbild) und die kleinen Kamera-Bilder sind versteckt. Bild antippen (PC: Maus darüber, Tastatur: Tab) = sie erscheinen für 4 Sekunden, jede Berührung verlängert; ist ein Menü, «Untersuchen» oder die Steuerung offen, bleiben sie. «LIVE» und der Kamera-Name bleiben immer. Immer zeigen: Einstellungen → Netzwerk &amp; Zugang → Web-Stream → «Knöpfe im Live-Bild immer zeigen» (nur in diesem Browser).</li>',
    "en": '<li><b>Clean live picture:</b> the buttons on the picture (🎮, 🔍, 📷, view, full screen) and the small camera pictures are hidden. Tap the picture (PC: mouse over it, keyboard: Tab) = they show for 4 seconds, every touch adds time; while a menu, «Examine» or the control is open they stay. «LIVE» and the camera name always stay. Always show: Settings → Network &amp; access → Web stream → «Always show the buttons in the live picture» (only in this browser).</li>',
    "fr": '<li><b>Image en direct dégagée :</b> les boutons sur l’image (🎮, 🔍, 📷, vue, plein écran) et les petites images des caméras sont masqués. Toucher l’image (PC : souris dessus, clavier : Tab) = ils s’affichent 4 secondes, chaque contact prolonge ; si un menu, « Examiner » ou la commande est ouvert, ils restent. « LIVE » et le nom de la caméra restent toujours. Toujours afficher : Réglages → Réseau &amp; accès → Flux web → « Toujours afficher les boutons dans l’image en direct » (seulement dans ce navigateur).</li>',
    "it": '<li><b>Immagine dal vivo pulita:</b> i pulsanti sull’immagine (🎮, 🔍, 📷, vista, schermo intero) e le piccole immagini delle telecamere sono nascosti. Tocca l’immagine (PC: mouse sopra, tastiera: Tab) = appaiono per 4 secondi, ogni tocco prolunga; se un menu, «Esaminare» o il comando è aperto, restano. «LIVE» e il nome della telecamera restano sempre. Mostrare sempre: Impostazioni → Rete &amp; accesso → Stream web → «Mostra sempre i pulsanti nell’immagine dal vivo» (solo in questo browser).</li>',
    "rm": '<li><b>Maletg live net:</b> ils buttuns sin il maletg (🎮, 🔍, 📷, vista, entir visur) e las pitschnas maletgs da las cameras èn zuppads. Tutgar il maletg (PC: mieur sur el, tastatura: Tab) = els cumparan per 4 secundas, mintga tutg prolunghescha; sch’in menu, «Examinar» u la direcziun è avert, restan els. «LIVE» ed il num da la camera restan adina. Adina mussar: Parameters → Rait &amp; access → Stream web → «Adina mussar ils buttuns en il maletg live» (mo en quest navigatur).</li>',
}


def _help_lvk(doc, lang):
    i = doc.find('<section id="views"')
    if i < 0 or 'id="lvk-help"' in doc:
        return doc
    j = doc.find("</ul></section>", i)
    if j < 0:
        return doc
    return doc[:j] + _HELP_LVK[lang].replace("<li>", '<li id="lvk-help">', 1) + doc[j:]


_hp_en_lvk = HELP_PAGE.find('<div lang="en">')
if _hp_en_lvk > 0:
    HELP_PAGE = _help_lvk(HELP_PAGE[:_hp_en_lvk], "de") + _help_lvk(HELP_PAGE[_hp_en_lvk:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_lvk(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def live_sauber_selftest():
    html = WEB_PAGE
    assert html.count('id="lvk-css"') == 1 and "/*LVKDE*/" not in html and "/*LVKMS*/" not in html, "Live-Bild sauber not in the page"
    assert html.find('id="lvk-css"') > html.find('id="kw-css"') > 0, "after 639zzi"
    for need in ("window.mwLiveKnoepfe", '"mw-lv-knoepfe"', "body.lvc-auto:not(.lvc-show) #lv-tools", "#kw-row img", 'data-view="sec:Web stream"',
                 "pointer-events:none!important", '"kw-menu", "v3-menu", "lv-menu", "unt-bar"', '"pv-on"', ":focus-visible"):
        assert need in LVK_JS, "Live-Bild sauber: missing " + need
    for bad in ("/api/set", "/api/ui\"", ".vtag", "#v3-tag"):
        assert bad not in LVK_JS.split("<script>")[1], "Live-Bild sauber must not touch: " + bad
    assert "mw-lv-knoepfe" in WEB_UI_LOCAL, "per browser"
    for k, v in _HX_LVK.items():
        assert len(v) == 4 and all(v), k
        assert k in DE and k in TRX["fr"] and k in TRX["it"] and k in TRX["rm"], k
    assert tr("USB camera", "de") == "USB-Kamera"
    assert "kwCamName" in KAMWAHL_JS, "639zzi: the prefix «USB camera» translated"
    assert HELP_PAGE.count('id="lvk-help"') == 2, "manual: clean live picture"
    return "live picture clean by default, tap = 4 s, switch per browser, USB prefix translated"


SELFTEST_EXTRA.append(("Live picture clean: buttons and tiles after a tap (639zzj)", live_sauber_selftest))
