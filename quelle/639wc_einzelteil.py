#@ MoveEye – Teil 639wc: Einzelteil-Vorschau und Ansicht «Druckplatten» der 3D-Werkstatt in «Bauen» (/build, 639w): ein angetipptes Teil allein zeigen (drehen, zoomen, zentriert), Grösse, Druck-Infos bzw. Zukauf-Infos, Download 3MF genau dieses Teils, «Liegend wie gedruckt» auf einer Druckplatte 256 × 256 mm, «Wo es hingehört» (Einblendung mit dem ganzen Modell und dem Montageschritt); Druckplatten A / B der Variante mit allen Teilen wie in der 3MF, Platte herunterladen, alle Platten als ZIP mit Kurzanleitung (/build/platten.zip). Gleich im Simulator (werkstatt.gd). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «real-einzelteil-vorschau» (01.11.2026, Wunsch des Besitzers). Die Lage jedes Druckteils auf der Platte und die Platten kommen
# aus 639wb (GEH_DRUCK_LAGE, werkzeuge/druck_lage.py aus gehaeuse.glb und den 3MF) – die Werkstatt dreht nur ihr vorhandenes
# Modell, es kommen keine weiteren Netze dazu. Teile der Platte ohne eigenes Netz (kleine Stopfen, die 4 Füsse) erscheinen als
# Quader in ihrer Grösse. Bestehendes bleibt: Explosion, Durchsichtig, Innenleben, Montage (die Regler ruhen in den neuen Ansichten).
#   * GEH_PAGE: Knopf «Druckplatten» und «Zurück zum ganzen Modell» bei den 3D-Reglern, /*GEHEINZEL*/ (Bedienung, Texte),
#     GEH_3D_JS: /*GEHEINZEL3D*/ (die Ansichten im selben Bild; «Wo es hingehört» als kleines Bild unten rechts im selben Canvas).
#   * /build/platten.zip?v=v52|v51&lang=..: die Platten der Variante + LIESMICH_Druck.txt (Kurzanleitung in der Sprache),
#     Name mit Version (MoveEye_v5-2_Druckplatten_X.Y.Z.zip); auf dem Pi ohne Repository holt MoveEye die Platten selbst
#     (real-download-fix: geh_druck_holen, Cache, Basisnamen), keine Weiterleitung zu GitHub.
#   * «In Bambu Studio öffnen» bewusst weggelassen: das Link-Schema (bambustudio://open?file=…) ist nicht offiziell beschrieben und
#     lädt nur Dateien, die Bambu Studio selbst aus dem Internet holen kann – die Seite des Pi im Heimnetz geht dafür nicht sicher.
# ----------------------------------------------------------------------------
EINZEL_TX = {   # English key: (de, fr, it, rm)
    "Show only this part": ("Nur dieses Teil zeigen", "Afficher seulement cette pièce", "Mostra solo questo pezzo", "Mussar mo questa part"),
    "Back to the whole model": ("Zurück zum ganzen Modell", "Retour au modèle complet", "Torna al modello completo", "Enavos al model entir"),
    "Print plates": ("Druckplatten", "Plateaux d'impression", "Piatti di stampa", "Plattas da stampa"),
    "Lying as printed (plate 256 × 256 mm)": ("Liegend wie gedruckt (Druckplatte 256 × 256 mm)", "Couchée comme imprimée (plateau 256 × 256 mm)",
                                               "Disteso come stampato (piatto 256 × 256 mm)", "Giaschend sco stampà (platta 256 × 256 mm)"),
    "Size (bounding box): %s mm": ("Grösse (Bounding Box): %s mm", "Taille (boîte englobante) : %s mm", "Dimensioni (ingombro): %s mm", "Grondezza (bounding box): %s mm"),
    "on the plate %s mm": ("auf der Platte %s mm", "sur le plateau %s mm", "sul piatto %s mm", "sin la platta %s mm"),
    "Material": ("Material", "Matériau", "Materiale", "Material"),
    "Colour": ("Farbe", "Couleur", "Colore", "Colur"),
    "orange": ("orange", "orange", "arancione", "oransch"),
    "grey": ("grau", "gris", "grigio", "grisch"),
    "natural / white": ("natur / weiss", "naturel / blanc", "naturale / bianco", "natira / alv"),
    "black": ("schwarz", "noir", "nero", "nair"),
    "Orientation": ("Ausrichtung", "Orientation", "Orientamento", "Orientaziun"),
    "Weight": ("Gewicht", "Poids", "Peso", "Paisa"),
    "about %s g (estimated)": ("ca. %s g (geschätzt)", "env. %s g (estimé)", "circa %s g (stimato)", "circa %s g (stimà)"),
    "about %s h (estimated)": ("ca. %s h (geschätzt)", "env. %s h (estimé)", "circa %s h (stimato)", "circa %s h (stimà)"),
    "Where it goes": ("Wo es hingehört", "Où elle va", "Dove va", "Nua ch'ella va"),
    "Step %d – %s": ("Schritt %d – %s", "Étape %d – %s", "Passo %d – %s", "Pass %d – %s"),
    "Plate %s": ("Platte %s", "Plateau %s", "Piatto %s", "Platta %s"),
    "Download plate (3MF)": ("Platte herunterladen (3MF)", "Télécharger le plateau (3MF)", "Scarica il piatto (3MF)", "Telechargiar la platta (3MF)"),
    "All plates (ZIP with short guide)": ("Alle Platten (ZIP mit Kurzanleitung)", "Tous les plateaux (ZIP avec notice courte)",
                                          "Tutti i piatti (ZIP con breve guida)", "Tut las plattas (ZIP cun curt manual)"),
    "Tap a part on the plate: single-part view.": ("Teil auf der Platte antippen: Einzelteil-Vorschau.", "Toucher une pièce du plateau : vue de la pièce seule.",
                                                   "Tocca un pezzo sul piatto: vista del pezzo singolo.", "Tutgar ina part sin la platta: vista da la part singula."),
    "Open the 3MF in Bambu Studio (File → Open): the parts already lie right, without supports.": (
        "3MF in Bambu Studio öffnen (Datei → Öffnen): die Teile liegen schon richtig, ohne Stützen.",
        "Ouvrir le 3MF dans Bambu Studio (Fichier → Ouvrir) : les pièces sont déjà bien posées, sans supports.",
        "Aprire il 3MF in Bambu Studio (File → Apri): i pezzi sono già orientati, senza supporti.",
        "Avrir il 3MF en Bambu Studio (Datoteca → Avrir): las parts èn gia posiziunadas endretg, senza sustegns."),
    "Bought part": ("Zukaufteil", "Pièce achetée", "Pezzo acquistato", "Part cumprada"),
    "Print part": ("Druckteil", "Pièce imprimée", "Pezzo stampato", "Part stampada"),
    "Order number": ("Bestellnummer", "Numéro de commande", "Numero d'ordine", "Numer d'empustaziun"),
    "as built (orientation estimated)": ("wie eingebaut (Lage geschätzt)", "comme montée (position estimée)", "come montato (posizione stimata)", "sco muntà (posiziun stimada)"),
    "shown as a box (no own 3D model)": ("als Quader gezeigt (kein eigenes 3D-Modell)", "montrée en bloc (pas de modèle 3D propre)",
                                         "mostrato come blocco (nessun modello 3D proprio)", "mussà sco bloc (nagin agen model 3D)"),
    "Print file 3MF (this part)": ("Druckdatei 3MF (dieses Teil)", "Fichier d'impression 3MF (cette pièce)", "File di stampa 3MF (questo pezzo)", "Datoteca da stampa 3MF (questa part)"),
    "%d parts on this plate": ("%d Teile auf dieser Platte", "%d pièces sur ce plateau", "%d pezzi su questo piatto", "%d parts sin questa platta"),
    "Single part": ("Einzelteil", "Pièce seule", "Pezzo singolo", "Part singula"),
    "Group": ("Gruppe", "Groupe", "Gruppo", "Gruppa"),
    "Brim": ("Brim", "Bordure (brim)", "Brim", "Brim"),
    # the short guide in the ZIP (LIESMICH_Druck.txt)
    "MoveEye – print plates case v%s (as of MoveEye %s)": ("MoveEye – Druckplatten Gehäuse v%s (Stand MoveEye %s)", "MoveEye – plateaux d'impression boîtier v%s (état MoveEye %s)",
                                                           "MoveEye – piatti di stampa custodia v%s (stato MoveEye %s)", "MoveEye – plattas da stampa chascha v%s (stadi MoveEye %s)"),
    "Printer: Bambu Lab X2D (other printers work too), 0.4 mm nozzle, material PETG – dry it first.": (
        "Drucker: Bambu Lab X2D (andere Drucker gehen auch), 0,4-mm-Düse, Material PETG – vorher trocknen.",
        "Imprimante : Bambu Lab X2D (d'autres aussi), buse 0,4 mm, matériau PETG – le sécher avant.",
        "Stampante: Bambu Lab X2D (anche altre), ugello 0,4 mm, materiale PETG – prima essiccarlo.",
        "Stampader: Bambu Lab X2D (er auters), duscha 0,4 mm, material PETG – l'emprim sitgar."),
    "No supports: all parts already lie right on the plate. Brim 5 mm only for head (06), yoke (04) and side cover (07).": (
        "Keine Stützen: alle Teile liegen schon richtig auf der Platte. Brim 5 mm nur bei Kopf (06), Gabel (04) und Seitendeckel (07).",
        "Pas de supports : toutes les pièces sont déjà bien posées. Brim 5 mm seulement pour la tête (06), la fourche (04) et le couvercle latéral (07).",
        "Nessun supporto: tutti i pezzi sono già orientati. Brim 5 mm solo per testa (06), forcella (04) e coperchio laterale (07).",
        "Nagins sustegns: tut las parts èn gia posiziunadas. Brim 5 mm mo per il chau (06), la furtga (04) ed il cuvertg lateral (07)."),
    "Colours: head parts orange (everything that turns or tilts), the rest grey; diffuser 14 natural/white, pupil ring 15 black.": (
        "Farben: Kopfteile orange (alles, was sich dreht oder neigt), Rest grau; Diffusor 14 natur/weiss, Pupillenring 15 schwarz.",
        "Couleurs : pièces de la tête orange (tout ce qui tourne ou s'incline), le reste gris ; diffuseur 14 naturel/blanc, anneau 15 noir.",
        "Colori: pezzi della testa arancione (tutto ciò che ruota o si inclina), il resto grigio; diffusore 14 naturale/bianco, anello 15 nero.",
        "Colurs: parts dal chau oransch (tut quai che sa volva u sa pendenta), il rest grisch; diffusur 14 natira/alv, anè 15 nair."),
    "Open: Bambu Studio → File → Open, choose the plate, slice and print.": (
        "Öffnen: Bambu Studio → Datei → Öffnen, Platte wählen, slicen und drucken.",
        "Ouvrir : Bambu Studio → Fichier → Ouvrir, choisir le plateau, découper et imprimer.",
        "Aprire: Bambu Studio → File → Apri, scegliere il piatto, slice e stampa.",
        "Avrir: Bambu Studio → Datoteca → Avrir, tscherner la platta, slicen e stampar."),
    "Plate %s (%s): %s": ("Platte %s (%s): %s", "Plateau %s (%s) : %s", "Piatto %s (%s): %s", "Platta %s (%s): %s"),
    "Single parts and everything else: MoveEye → More → Build → Printing.": (
        "Einzelteile und alles Weitere: MoveEye → Mehr → Bauen → Drucken.", "Pièces seules et tout le reste : MoveEye → Plus → Construire → Impression.",
        "Pezzi singoli e tutto il resto: MoveEye → Altro → Costruire → Stampa.", "Parts singulas e tut il rest: MoveEye → Dapli → Construir → Stampar."),
}
for _k, (_de, _fr, _it, _rm) in EINZEL_TX.items():
    DE.setdefault(_k, _de)
    for _L, _v in (("fr", _fr), ("it", _it), ("rm", _rm)):
        TRX.setdefault(_L, {}).setdefault(_k, _v)
GEH_KEYS = sorted(set(GEH_KEYS) | set(EINZEL_TX) | {"none", "Supports", "Infill", "Walls", "Layer", "pcs", "Shop", "Qty"})

_EINZEL_CTL_ANCHOR = '<button type="button" class="sec" onclick="bv(\'reset\')" data-i18n="Reset the view">Reset the view</button></div>'
_EINZEL_CTL = ('<button type="button" class="sec" id="v-plates" onclick="gPlates(BV.plate || 0)">🖨 <span data-i18n="Print plates">Print plates</span></button>'
               '<button type="button" id="v-whole" hidden onclick="gWhole()">↩ <span data-i18n="Back to the whole model">Back to the whole model</span></button>\n    ')
if 'id="v-plates"' not in GEH_PAGE and _EINZEL_CTL_ANCHOR in GEH_PAGE:
    GEH_PAGE = GEH_PAGE.replace(_EINZEL_CTL_ANCHOR, _EINZEL_CTL + _EINZEL_CTL_ANCHOR, 1)
_EINZEL_CSS = ("#v3d-where{position:absolute;right:8px;bottom:8px;border:1px solid #4b5868;border-radius:10px;background:transparent;color:#e6edf5;"
               "display:none;align-items:flex-end;justify-content:center;padding:0 0 4px;font-size:10px;line-height:1.25;text-align:center;cursor:pointer;min-height:0}"
               "#v3d-where span{background:#1b2430cc;border-radius:6px;padding:2px 6px;margin:0 4px}"
               ".pinfo table.gb{margin:6px 0}.pinfo .vrow{margin-top:6px}.pinfo ul.pl{margin:6px 0;padding-left:18px}.pinfo ul.pl li{cursor:pointer;color:var(--acc);padding:2px 0}"
               ".pinfo .btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}\n")
if "#v3d-where" not in GEH_PAGE:
    GEH_PAGE = GEH_PAGE.replace("</style></head>", _EINZEL_CSS + "</style></head>", 1)
if "/*GEHEINZEL*/" not in GEH_PAGE:
    GEH_PAGE = GEH_PAGE.replace("<script>/*GEHFERTIG*/</script>", "<script>/*GEHFERTIG*/</script>\n<script>/*GEHEINZEL*/</script>", 1)

# the operation (classic script, after the page script: it may wrap gInfo / gStep, it knows GB, G, BV, TEIL, BOM, pfile …)
GEH_EINZEL_JS = r"""
(function () {
const DL = window.DL = /*GEHDL*/null, B = BV;
Object.assign(B, {mode: "", solo: "", flat: false, plate: 0, inset: true, pdatei: "", whereText: ""});
const FARBE = {orange: "orange", grau: "grey", natur: "natural / white", schwarz: "black"};
const plates = () => ((DL || {}).platten || {})[isV52() ? "v52" : "v51"] || [];
const lage = id => ((DL || {}).lage || {})[id];
const n1 = v => { const r = v >= 20 ? Math.round(v) : Math.round(v * 10) / 10; return String(r).replace(".", gL() === "en" ? "." : ","); };
const dims = id => { const g = ((DL || {}).masse || {})[id]; return g ? g.map(n1).join(" × ") : ""; };
const druckOf = d => { const all = (GB.druck || {}).teile || []; return all.find(p => p.datei === d && ok(p.wenn)) || all.find(p => p.datei === d); };
const pname = d => { const p = (GB.teile || []).find(x => x.datei === d && x.name); return p ? gx(p.name) : d.replace(/_/g, " "); };
function btn(txt, fn, cls) { const b = el("button", cls || "", txt); b.type = "button"; b.onclick = fn; return b; }
function table(rows) {
  const tb = el("table", "gb");
  rows.filter(r => r && r[1] !== "" && r[1] != null).forEach(([k, v]) => { const tr = el("tr"); const a = el("td", "q", k), b = el("td"); if (v instanceof Node) b.appendChild(v); else b.textContent = v; tr.append(a, b); tb.appendChild(tr); });
  return tb;
}
function printRows(datei) {
  const d = druckOf(datei) || {}, de = ((DL || {}).dateien || {})[datei] || {};
  return [[t("Material"), "PETG"], [t("Colour"), t(FARBE[de.farbe] || "grey")], [t("Orientation"), gx(d.liegt)],
    [t("Supports"), d.stuetzen ? "✓" : t("none")], [t("Brim"), d.brim ? d.brim + " mm" : t("none")],
    [t("Infill"), d.fuellung != null ? d.fuellung + " %" : ""], [t("Walls"), d.waende != null ? String(d.waende) : ""], [t("Layer"), d.schicht ? d.schicht + " mm" : ""],
    [t("pcs"), d.stueck ? "× " + d.stueck : ""], [t("Print time"), d.zeit_h != null ? fmt(t("about %s h (estimated)"), d.zeit_h) : ""],
    [t("Weight"), de.gramm ? fmt(t("about %s g (estimated)"), de.gramm) : ""]];
}
function modeUi() {
  ["v-exp", "v-xray", "v-inner"].forEach(i => { const e = document.getElementById(i); if (e) e.disabled = !!B.mode; });
  const w = document.getElementById("v-whole"), p = document.getElementById("v-plates");
  if (w) w.hidden = !B.mode;
  if (p) p.classList.toggle("on", B.mode === "platten");
}
function setMode(m, o) { bv("mode", [m, o || {}]); modeUi(); gInfo(); }
window.gSolo = (id, flat) => { if (!id) return; G.sel = id; B.sel = id; B.pdatei = ""; setMode("teil", {solo: id, flat: !!flat && !!lage(id)}); };
window.gWhole = () => { B.pdatei = ""; setMode("", {}); };
window.gPlates = n => { const ps = plates(); B.pdatei = ""; setMode("platten", {plate: Math.max(0, Math.min(ps.length - 1, n | 0))}); };
window.gWhere = () => { const p = TEIL[B.solo]; if (!p || !p.schritt) return; gWhole(); gTab("montage"); gStep(p.schritt); };
B.onWhere = () => gWhere();
B.onPlateTap = (id, datei) => {
  if (id && lage(id)) return gSolo(id, true);
  B.pdatei = datei || ""; gInfo();
};
function soloInfo(box) {
  const id = B.solo, p = TEIL[id] || {}, b = BOM[p.bom], L = lage(id);
  box.appendChild(el("b", "", "🔍 " + t("Single part") + ": " + gx(p.name || (b && b.name) || id)));
  const dm = dims(id);
  let sz = dm ? fmt(t("Size (bounding box): %s mm"), dm) : "";
  if (L && B.flat) sz += (sz ? " · " : "") + fmt(t("on the plate %s mm"), L.g.map(n1).join(" × "));
  if (sz) box.appendChild(el("div", "", sz));
  if (p.datei) {
    box.appendChild(el("div", "mut", t("Print part")));
    box.appendChild(table(printRows(p.datei)));
    const d = el("div", "lk"); d.appendChild(fileLink(pfile(p.datei), t("Print file 3MF (this part)"))); box.appendChild(d);
    if (L) {
      const lb = el("label"), c = el("input"); lb.style.cssText = "display:flex;gap:8px;align-items:center;margin-top:8px"; c.type = "checkbox"; c.checked = !!B.flat; c.id = "v-flat";
      c.onchange = () => setMode("teil", {solo: id, flat: c.checked}); lb.append(c, el("span", "", t("Lying as printed (plate 256 × 256 mm)")));
      box.appendChild(lb);
      if (L.unsicher && B.flat) box.appendChild(el("div", "mut", t("as built (orientation estimated)")));
    }
  } else if (b) {
    box.appendChild(el("div", "mut", t("Bought part")));
    box.appendChild(table([[t("Name"), gx(b.name)], [t("Qty"), b.menge], [t("Order number"), b.nr || ""], [t("Group"), gx((GB.bom_gruppen || {})[b.gruppe])], [t("Shop"), shopLinks(b)]]));
  } else box.appendChild(el("div", "mut", t("not in the parts list")));
  B.whereText = ""; B.whereShort = "";
  if (p.schritt && GB.schritte[p.schritt - 1]) {
    const s = (typeof sv === "function" ? sv : x => x)(GB.schritte[p.schritt - 1]);
    B.whereText = "📍 " + t("Where it goes") + " · " + fmt(t("Step %d – %s"), p.schritt, gx(s.titel));
    B.whereShort = "📍 " + fmt(t("Step %d of %d"), p.schritt, GB.schritte.length);
    box.appendChild(el("div", "btns")).appendChild(btn(B.whereText, gWhere, "sec"));
  }
  box.appendChild(el("div", "btns")).appendChild(btn("↩ " + t("Back to the whole model"), gWhole));
  bv("paint");
}
function plateInfo(box) {
  const ps = plates(), pl = ps[B.plate] || ps[0];
  box.appendChild(el("b", "", "🖨 " + t("Print plates") + " · " + t("Case") + " v" + (isV52() ? "5.2" : "5.1")));
  const sg = el("span", "seg");
  ps.forEach((q, i) => sg.appendChild(btn(fmt(t("Plate %s"), q.name), () => gPlates(i), i === B.plate ? "on" : "")));
  const r = el("div", "vrow"); r.appendChild(sg); box.appendChild(r);
  if (!pl) return;
  box.appendChild(el("div", "mut", fmt(t("%d parts on this plate"), pl.teile.length) + " · 256 × 256 mm · " + t("Tap a part on the plate: single-part view.")));
  if (B.pdatei) {
    const c = el("div", "pinfo"); c.appendChild(el("b", "", pname(B.pdatei))); c.appendChild(el("div", "mut", t("shown as a box (no own 3D model)")));
    c.appendChild(table(printRows(B.pdatei))); const d = el("div", "lk"); d.appendChild(fileLink(pfile(B.pdatei), t("Print file 3MF (this part)"))); c.appendChild(d); box.appendChild(c);
  }
  const ul = el("ul", "pl"); const seen = new Set();
  pl.teile.forEach(it => { const k = it.datei; if (seen.has(k)) return; seen.add(k);
    const n = pl.teile.filter(x => x.datei === k).length, li = el("li", "", pname(k) + (n > 1 ? " × " + n : ""));
    li.onclick = () => B.onPlateTap(it.id || it.teil || "", it.datei); ul.appendChild(li); });
  box.appendChild(ul);
  const lk = el("div", "lk btns"); lk.appendChild(fileLink(pl.datei, t("Download plate (3MF)")));
  const z = fileLink("", t("All plates (ZIP with short guide)")); z.href = "/build/platten.zip?v=" + (isV52() ? "v52" : "v51") + "&lang=" + gL();
  z.setAttribute("download", (isV52() ? "MoveEye_v5-2_Druckplatten_" : "MoveEye_v5-1_Druckplatten_") + (typeof GEH_VER === "string" ? GEH_VER : "") + ".zip"); lk.appendChild(z);
  box.appendChild(lk);
  box.appendChild(el("div", "mut", t("Open the 3MF in Bambu Studio (File → Open): the parts already lie right, without supports.")));
  box.appendChild(el("div", "btns")).appendChild(btn("↩ " + t("Back to the whole model"), gWhole));
}
const _gInfo = gInfo;
gInfo = function () {
  const box = document.getElementById("v3d-info");
  if (B.mode === "teil" && TEIL[B.solo]) { box.textContent = ""; return soloInfo(box); }
  if (B.mode === "platten") { box.textContent = ""; return plateInfo(box); }
  B.whereText = "";
  _gInfo();
  if (G.sel && TEIL[G.sel]) box.appendChild(el("div", "btns")).appendChild(btn("🔍 " + t("Show only this part"), () => gSolo(G.sel)));
};
const _gStep = gStep;
gStep = function () { if (B.mode) { B.pdatei = ""; bv("mode", ["", {}]); modeUi(); } return _gStep.apply(this, arguments); };
const _gRender = gRender;
const _gOs = B.onSelect;
B.onSelect = id => { if (B.mode) { B.pdatei = ""; bv("mode", ["", {}]); modeUi(); } _gOs(id); };
gRender = function () { const r = _gRender.apply(this, arguments); if (B.mode === "platten") B.plate = Math.min(B.plate, Math.max(0, plates().length - 1)); modeUi(); return r; };
})();
"""

# the 3D part (inside the module of GEH_3D_JS: it uses THREE, scene, cam, ctl, parts, paint, render, view, row, shown, bench, T0)
GEH_EINZEL_3D = r"""
// ---- 639wc: single part · print plates (the same model, only turned / placed as in the 3MF) -------------------------------
{
const LG = window.DL || {lage: {}, platten: {}, dateien: {}}, MM = 0.001, PL = (LG.platte_mm || 256) * MM;
const COL = {orange: "#f59a4a", grau: (GB.farben || {}).grau || "#6d7074", natur: "#e9e5d9", schwarz: "#222222"};
const plateG = new THREE.Group(); plateG.visible = false; scene.add(plateG);
const top = new THREE.Mesh(new THREE.BoxGeometry(PL, 0.002, PL), new THREE.MeshStandardMaterial({color: 0x39424f, roughness: 0.85}));
top.position.y = -0.0011; plateG.add(top);
const grid = new THREE.GridHelper(PL, 8, 0x8a99ab, 0x55637a); grid.position.y = 0.0001; plateG.add(grid);
const front = new THREE.Mesh(new THREE.BoxGeometry(PL, 0.0025, 0.004), new THREE.MeshStandardMaterial({color: 0xf59a4a}));
front.position.set(0, -0.001, PL / 2 + 0.002); plateG.add(front);           // the front edge of the plate (y = 0 in the 3MF)
const boxes = new THREE.Group(); plateG.add(boxes);
let boxKey = "";
const icam = new THREE.PerspectiveCamera(40, 1.25, 0.01, 10);
{ const y = 145 * Math.PI / 180, p = 24 * Math.PI / 180, d = 0.5; icam.position.set(T0.x + d * Math.cos(p) * Math.sin(y), T0.y + d * Math.sin(p), T0.z + d * Math.cos(p) * Math.cos(y)); icam.lookAt(T0); }
const IBG = new THREE.Color("#243142");
const wh = document.createElement("button"); wh.type = "button"; wh.id = "v3d-where"; box.appendChild(wh);
wh.addEventListener("pointerdown", e => e.stopPropagation()); wh.addEventListener("pointerup", e => e.stopPropagation());
wh.onclick = () => B.onWhere && B.onWhere();
const touched = new Set();
const plates = () => (LG.platten || {})[B.v52 ? "v52" : "v51"] || [];
function lageM(id, dx, dz) {
  const L = (LG.lage || {})[id]; if (!L) return null;
  const r = L.r, t = L.t, m = new THREE.Matrix4();
  m.set(r[0], r[1], r[2], t[0] + (dx || 0), r[3], r[4], r[5], t[1], r[6], r[7], r[8], t[2] + (dz || 0), 0, 0, 0, 1); return m;
}
function place(m, M) { touched.add(m); m.matrixAutoUpdate = false; m.matrix.copy(M); m.matrixWorldNeedsUpdate = true; }
function built(m) { m.matrixAutoUpdate = true; m.position.set(0, 0, 0); m.updateMatrix(); touched.delete(m); }
X.reset = () => { [...touched].forEach(built); plateG.visible = false; bench.visible = true; wh.style.display = "none"; };
function makeBoxes(pl) {
  const key = (B.v52 ? "v52" : "v51") + ":" + (pl ? pl.name : "");
  if (key === boxKey) return; boxKey = key;
  boxes.children.slice().forEach(b => { b.geometry.dispose(); b.material.dispose(); boxes.remove(b); });
  if (!pl) return;
  pl.teile.forEach(it => {
    if (it.id && parts[it.id]) return;
    const g = it.g, c = COL[((LG.dateien || {})[it.datei] || {}).farbe] || COL.grau;
    const bx = new THREE.Mesh(new THREE.BoxGeometry(Math.max(g[0], 0.5) * MM, Math.max(g[2], 0.5) * MM, Math.max(g[1], 0.5) * MM), new THREE.MeshStandardMaterial({color: c, roughness: 0.6}));
    bx.position.set(it.x * MM - PL / 2, g[2] * MM / 2, PL / 2 - it.y * MM); bx.userData.it = it; boxes.add(bx);
  });
}
X.paint = () => {
  bench.visible = false;
  const flat = B.mode === "platten" || (B.mode === "teil" && B.flat && !!(LG.lage || {})[B.solo]);
  plateG.visible = flat;
  const pl = B.mode === "platten" ? (plates()[B.plate] || plates()[0]) : null;
  makeBoxes(pl); boxes.visible = !!pl;
  const on = {}; if (pl) pl.teile.forEach(it => { if (it.id && parts[it.id]) on[it.id] = it; });
  for (const id in parts) {
    const m = parts[id].mesh, mat = m.material;
    mat.transparent = false; mat.opacity = 1; mat.depthWrite = true; mat.emissive.set(0x000000); mat.emissiveIntensity = 0;
    if (B.mode === "teil") {
      m.visible = id === B.solo;
      if (m.visible && flat) place(m, lageM(id)); else built(m);
    } else {
      const it = on[id]; m.visible = !!it;
      if (it) place(m, lageM(id, it.x * MM - PL / 2, PL / 2 - it.y * MM)); else built(m);
    }
  }
  if (B.mode !== "teil") wh.style.display = "none";
  render();
};
X.frame = () => {
  const b = new THREE.Box3();
  if (B.mode === "platten") b.setFromCenterAndSize(new THREE.Vector3(0, 0.02, 0), new THREE.Vector3(PL, 0.04, PL));
  else { const p = parts[B.solo]; if (!p) return; p.mesh.updateMatrixWorld(true); b.setFromObject(p.mesh); if (B.flat) b.min.y = 0; }
  const c = b.getCenter(new THREE.Vector3()), r = Math.max(0.006, b.getSize(new THREE.Vector3()).length() / 2);
  ctl.minDistance = Math.max(0.008, r * 0.5); cam.near = Math.max(0.0005, r / 60); cam.updateProjectionMatrix();
  const d = r / Math.sin(cam.fov * Math.PI / 360) * (B.mode === "teil" && B.inset ? 1.25 : 0.82);
  view(B.mode === "platten" ? 0 : 145, B.mode === "platten" ? 58 : (B.flat ? 32 : 24), d, c);
};
X.after = () => {                                   // «Wo es hingehört»: the whole model, the part lit, bottom right in the same picture
  if (B.mode !== "teil" || !B.inset || !parts[B.solo]) { wh.style.display = "none"; return; }
  const W = box.clientWidth || 300, H = box.clientHeight || 260, w = Math.round(Math.min(W * 0.36, 230)), h = Math.round(w * 0.8);
  const keep = [], s0 = B.step; B.step = 0;
  for (const id in parts) {
    const m = parts[id].mesh, mat = m.material, me = id === B.solo;
    keep.push([m, m.visible, m.matrixAutoUpdate, m.matrix.clone(), mat.transparent, mat.opacity, mat.depthWrite, mat.emissive.getHex(), mat.emissiveIntensity]);
    m.visible = me || shown(id); m.matrixAutoUpdate = false; m.matrix.identity(); m.updateMatrixWorld(true);
    mat.transparent = !me; mat.opacity = me ? 1 : 0.2; mat.depthWrite = me; mat.emissive.set(me ? 0xf59a4a : 0x000000); mat.emissiveIntensity = me ? 0.7 : 0;
  }
  B.step = s0;
  const pv = plateG.visible, bv_ = bench.visible, bg = scene.background; plateG.visible = false; bench.visible = false; scene.background = IBG;
  renderer.setScissorTest(true); renderer.setScissor(W - w - 8, 8, w, h); renderer.setViewport(W - w - 8, 8, w, h);
  icam.aspect = w / h; icam.updateProjectionMatrix(); renderer.render(scene, icam);
  renderer.setScissorTest(false); renderer.setViewport(0, 0, W, H);
  plateG.visible = pv; bench.visible = bv_; scene.background = bg;
  keep.forEach(([m, v, au, mx, tr, op, dw, em, ei]) => { m.visible = v; m.matrixAutoUpdate = au; m.matrix.copy(mx); m.updateMatrixWorld(true);
    m.material.transparent = tr; m.material.opacity = op; m.material.depthWrite = dw; m.material.emissive.setHex(em); m.material.emissiveIntensity = ei; });
  wh.style.cssText = "display:flex;width:" + w + "px;height:" + h + "px";
  wh.textContent = ""; if (B.whereShort) { const s = document.createElement("span"); s.textContent = B.whereShort; wh.appendChild(s); }
  wh.title = B.whereText || "";
};
X.tap = ev => {
  if (B.mode !== "platten") return;
  const rc = new THREE.Raycaster(), r = renderer.domElement.getBoundingClientRect();
  rc.setFromCamera(new THREE.Vector2((ev.clientX - r.left) / r.width * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1), cam);
  const objs = Object.values(parts).filter(p => p.mesh.visible).map(p => p.mesh).concat(boxes.children);
  const h = rc.intersectObjects(objs, false)[0]; if (!h) return;
  const it = h.object.userData.it;
  B.onPlateTap && B.onPlateTap(it ? (it.teil || "") : h.object.name, it ? it.datei : (((LG.lage || {})[h.object.name]) || {}).datei);
};
X.setMode = a => {
  const [m, o_] = a || [], o = o_ || {};
  B.mode = m || ""; if ("solo" in o) B.solo = o.solo; if ("flat" in o) B.flat = !!o.flat; if ("plate" in o) B.plate = o.plate | 0;
  if (!B.mode) { X.reset(); ctl.minDistance = 0.12; cam.near = 0.01; cam.updateProjectionMatrix(); view(145, 24, 0.5); paint(); return; }
  paint(); X.frame();
};
X.info = () => ({mode: B.mode, solo: B.solo, flat: B.flat, plate: B.plate, plates: plates().length, onPlate: B.mode === "platten" ? Object.values(parts).filter(p => p.mesh.visible).length + boxes.children.length : 0,
  visible: Object.values(parts).filter(p => p.mesh.visible).map(p => p.mesh.name)});
const _reset = B.api.reset;
B.api.mode = X.setMode; B.api.einzel = X.info; B.api.reset = () => B.mode ? X.frame() : _reset();
}
"""


def _geh_page_einzel():
    js = GEH_EINZEL_JS.replace("/*GEHDL*/null", json.dumps(GEH_DRUCK_LAGE, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), 1)
    return _geh_page_einzel_base().replace("/*GEHEINZEL*/", js, 1).replace("/*GEHEINZEL3D*/", GEH_EINZEL_3D, 1)


_geh_page_einzel_base = geh_page
# wraps: geh_page (639w)
geh_page = _geh_page_einzel


def geh_platten_zip(v52=True, lang="de", budget=None):
    """the plates (3MF) of one case + LIESMICH_Druck.txt (short guide in the language), named with the version
    -> ("zip", name, bytes) | ("wait", done, total) | ("offline", reason, None). 3.48.0: like /build/alle.zip (real-download-fix,
    639w geh_druck_holen) - on the Pi without the repository MoveEye fetches the plates itself (cache, base names), no redirect"""
    import io
    import zipfile
    var = "v52" if v52 else "v51"
    fs = (GEH_DRUCK_LAGE.get("platten") or {}).get(var) or []
    if not fs:
        return "offline", "unknown", None
    t0, paths = time.time(), {}
    budget = GEH_ZIP_BUDGET if budget is None else budget
    for i, p in enumerate(fs):
        if time.time() - t0 > budget:
            rest = [x["datei"] for x in fs[i:]]
            if not _GEH_DL_BG["run"]:
                _GEH_DL_BG["run"] = True
                threading.Thread(target=_geh_bg_fetch, args=(rest,), daemon=True).start()
            return "wait", len(paths), len(fs)
        fp, why = geh_druck_holen(p["datei"])
        if not fp:
            return "offline", why, None
        paths[p["datei"]] = fp
    L = lang if lang in ("de", "en", "fr", "it", "rm") else "de"
    T = lambda k: tr(k, L) if L != "en" else k
    nm = lambda dt: next((x["name"].get(L) or x["name"].get("de") for x in GEH_BAU.get("teile") or [] if x.get("datei") == dt and isinstance(x.get("name"), dict)), dt.replace("_", " "))
    z = [T("MoveEye – print plates case v%s (as of MoveEye %s)") % ("5.2" if v52 else "5.1", APP_VERSION), "=" * 64, "",
         T("Printer: Bambu Lab X2D (other printers work too), 0.4 mm nozzle, material PETG – dry it first."),
         T("No supports: all parts already lie right on the plate. Brim 5 mm only for head (06), yoke (04) and side cover (07)."),
         T("Colours: head parts orange (everything that turns or tilts), the rest grey; diffuser 14 natural/white, pupil ring 15 black."),
         T("Open: Bambu Studio → File → Open, choose the plate, slice and print."), ""]
    for p in fs:
        seen = []
        for it in p["teile"]:
            n = sum(1 for x in p["teile"] if x["datei"] == it["datei"])
            s = nm(it["datei"]) + (" × %d" % n if n > 1 else "")
            if s not in seen:
                seen.append(s)
        z.append(T("Plate %s (%s): %s") % (p["name"], p["datei"].split("/")[-1], ", ".join(seen)))
    z += ["", T("Single parts and everything else: MoveEye → More → Build → Printing."), ""]
    top_ = ("MoveEye_v5-2_Druckplatten_" if v52 else "MoveEye_v5-1_Druckplatten_") + APP_VERSION
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr(top_ + "/LIESMICH_Druck.txt", "﻿" + "\r\n".join(z))
        for p in fs:
            zf.write(paths[p["datei"]], top_ + "/" + geh_base_name(p["datei"]))
    return "zip", top_, b.getvalue()


_smalltv_routes_einzel_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639wc: /build/platten.zip
    _smalltv_routes_einzel_base(app, reply, body)
    from flask import Response, request

    @app.route("/build/platten.zip")
    def geh_platten_():
        v52_ = request.args.get("v", "v52") != "v51"
        lg_ = str(request.args.get("lang") or "de")[:2]
        st, a_, b_ = geh_platten_zip(v52_, lg_)
        if st == "zip":
            return Response(b_, mimetype="application/zip", headers={"Content-Disposition": f'attachment; filename="{a_}.zip"', "Cache-Control": "no-store"})
        url = "/build/platten.zip?v=" + ("v52" if v52_ else "v51") + "&lang=" + lg_
        if st == "wait":
            return Response(geh_dl_page(tr("The print files are being fetched from the internet (%d of %d). This page tries again by itself; you can also tap «Try again».") % (a_, b_), retry=url, refresh=15), 202, mimetype="text/html")
        return Response(geh_dl_page(tr("The print file is not on this MoveEye and could not be fetched from the internet (no connection?). Try again later, or load the complete kit package."), retry=url), 503, mimetype="text/html")


def geh_einzel_selftest():
    D = GEH_DRUCK_LAGE
    T_ = {t_["id"]: t_ for t_ in GEH_BAU["teile"]}
    assert D.get("platte_mm") == 256 and D.get("lage") and D.get("platten"), "data 639wb"
    for id_, L in D["lage"].items():
        assert id_ in T_ and T_[id_].get("datei") == L["datei"], ("lage", id_)
        r = L["r"]
        assert len(r) == 9 and all(abs(x) in (0, 1) for x in r) and sorted(abs(x) for x in r).count(1) == 3, ("rotation", id_)
    for t_ in GEH_BAU["teile"]:                   # every print part of the model knows how it lies on the plate
        if t_.get("datei") and t_["id"] in {e["id"] for e in BAU3D_MODELLE.get("teile", [])}:
            assert t_["id"] in D["lage"], ("print part without orientation", t_["id"])
    for var in ("v52", "v51"):
        ps = D["platten"].get(var) or []
        assert [p["datei"] for p in ps] == [f for f in GEH_BAU.get("druckdateien") or [] if f.startswith("v5-2/") == (var == "v52")], ("plates", var)
        for p in ps:
            for it in p["teile"]:
                assert 0 <= it["x"] <= 256 and 0 <= it["y"] <= 256 and len(it["g"]) == 3, ("on the plate", var, it["o"])
                assert not it.get("id") or it["id"] in D["lage"], ("plate part", it["o"])
    import hashlib
    alt = False
    sim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "inhalte", "gehaeuse")
    if os.path.isfile(os.path.join(sim, "druck_lage.json")):    # the same data in the simulator, and they fit the model
        with open(os.path.join(sim, "druck_lage.json"), encoding="utf-8") as f_:
            assert json.load(f_) == D, "simulator3d/inhalte/gehaeuse/druck_lage.json differs from 639wb - werkzeuge/druck_lage.py"
        with open(os.path.join(sim, "gehaeuse.glb"), "rb") as f_:
            alt = hashlib.sha256(f_.read()).hexdigest() != D["glb_sha256"]
    for k in EINZEL_TX:
        assert DE.get(k) and all(TRX[L_].get(k) for L_ in ("fr", "it", "rm")), k
    html = geh_page()
    for x in ('id="v-plates"', "gSolo", "X.setMode", "v3d-where", '"platten"', "/build/platten.zip"):
        assert x in html, x
    assert "/*GEHEINZEL" not in html and "/*GEHDL*/" not in html
    st_, a_, b_ = geh_platten_zip(True, "fr", budget=0 if not os.path.isdir(geh_druck_dir()) else None)
    if st_ == "zip":                                      # in the repository; on the Pi without it: fetched (wait / offline)
        import io
        import zipfile
        with zipfile.ZipFile(io.BytesIO(b_)) as zf:
            ns = zf.namelist()
            txt = zf.read(a_ + "/LIESMICH_Druck.txt").decode("utf-8-sig")
        assert a_.endswith(APP_VERSION) and len(ns) == 1 + len(D["platten"]["v52"]) and "Plateau A" in txt, (ns, txt[:200])
    else:
        assert st_ in ("wait", "offline"), st_
    if alt:                                               # a warning (like the build infos): the model changed after the data
        return "WARNING – gehaeuse.glb changed after werkzeuge/druck_lage.py – run it again (orientation on the plate)"
    return "Build: single part view and print plates (%d parts with orientation, plates v5.2 %d / v5.1 %d)" % (
        len(D["lage"]), len(D["platten"].get("v52") or []), len(D["platten"].get("v51") or []))


SELFTEST_EXTRA.append(("Build: single part view, print plates (orientation from the 3MF, ZIP with short guide)", geh_einzel_selftest))
