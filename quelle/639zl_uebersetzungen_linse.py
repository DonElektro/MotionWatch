#@ MoveEye – Teil 639zl: Übersetzungen und Seiten-Teil des Hinweises «Linse verschmutzt» im Simulator-Betrieb (558l). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_LINSE = {
    'Lens dirty': ('Linse verschmutzt', 'Objectif sale', 'Obiettivo sporco', 'Lentilla malnetta'),
    'Lens dirty – in the simulator «Clean lens»': ('Linse verschmutzt – im Simulator «Linse putzen»', 'Objectif sale – dans le simulateur « Nettoyer l’objectif »',
                                                   'Obiettivo sporco – nel simulatore «Pulire l’obiettivo»', 'Lentilla malnetta – en il simulatur «Nettegiar la lentilla»'),
    'Clean lens': ('Linse putzen', 'Nettoyer l’objectif', 'Pulire l’obiettivo', 'Nettegiar la lentilla'),
    'Clean the lens in the simulator?': ('Linse im Simulator putzen?', 'Nettoyer l’objectif dans le simulateur ?', 'Pulire l’obiettivo nel simulatore?',
                                         'Nettegiar la lentilla en il simulatur?'),
    'Lens cleaned in the simulator': ('Linse im Simulator geputzt', 'Objectif nettoyé dans le simulateur', 'Obiettivo pulito nel simulatore',
                                      'Lentilla nettegiada en il simulatur'),
    'covered': ('bedeckt', 'couvert', 'coperto', 'cuvert'),
    'drops and fog on the lens of the head camera': ('Tropfen und Beschlag auf der Linse der Kopfkamera', 'gouttes et buée sur l’objectif de la caméra de tête',
                                                     'gocce e condensa sull’obiettivo della telecamera della testa', 'gutas e vapur sin la lentilla da la camera dal chau'),
}
for _k, _v in _HX_LINSE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

LENS_JS = r"""
<script>
(function () {
  try { const de = /*LNDE*/{}; if (typeof I18N !== "undefined" && I18N.de) for (const k in de) if (!(k in I18N.de)) I18N.de[k] = de[k]; } catch (e) {}
  const tt = s => (typeof t === "function" ? t(s) : s);
  let busy = false;
  async function wipe(btn) {
    if (busy) return; busy = true; if (btn) btn.disabled = true;
    try {
      const r = await fetch("/api/sim", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "lens_wipe", lang: (typeof LANG !== "undefined" ? LANG : "")})});
      const j = await r.json().catch(() => ({}));
      if (typeof toast === "function") toast(j.ok ? "🧽 " + tt("Lens cleaned in the simulator") : (j.error || "?"));
    } catch (e) {}
    setTimeout(() => { busy = false; if (btn) btn.disabled = false; }, 3000);
  }
  function chip() {
    let b = document.getElementById("b-lens"); if (b) return b;
    const ref = document.getElementById("b-light") || document.getElementById("b-sim"); if (!ref) return null;
    b = document.createElement("span"); b.id = "b-lens"; b.className = "badge yel"; b.hidden = true; b.style.cursor = "pointer";
    b.onclick = () => { if (confirm(tt("Clean the lens in the simulator?"))) wipe(null); };
    ref.parentNode.insertBefore(b, ref.nextSibling); return b;
  }
  function line() {
    let l = document.getElementById("lens-hint"); if (l) return l;
    const at = document.getElementById("simtile") || document.getElementById("c-hub"); if (!at) return null;
    l = document.createElement("div"); l.id = "lens-hint"; l.hidden = true;
    l.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:14px;margin:0 0 10px;padding:8px 10px;border:1px solid #e0b000;border-radius:10px;background:rgba(224,176,0,.12)";
    const sp = document.createElement("span"); sp.id = "lens-hint-t";
    const bt = document.createElement("button"); bt.type = "button"; bt.className = "btn"; bt.id = "lens-hint-b"; bt.onclick = () => wipe(bt);
    l.append(sp, bt); at.parentNode.insertBefore(l, at); return l;
  }
  function paint(s) {
    const S = (s && s.sim) || {}, L = (s && s.sim_lens) || null;
    const on = !!(S.on && S.ok && L && L.dirty);
    const h = (L && L.head) || {};
    const pct = Math.round((h.cover || 0) * 100);
    const info = tt("drops and fog on the lens of the head camera") + ": " + pct + " % " + tt("covered") + (h.fog > 0.05 ? " · 🌫 " + Math.round(h.fog * 100) + " %" : "");
    const b = chip();
    if (b) { b.hidden = !on; if (on) { b.textContent = "💧 " + tt("Lens dirty"); b.title = tt("Lens dirty – in the simulator «Clean lens»") + "\n" + info; } }
    const l = line();
    if (l) {
      l.hidden = !on;
      if (on) { document.getElementById("lens-hint-t").textContent = "💧 " + tt("Lens dirty – in the simulator «Clean lens»"); l.title = info;
                document.getElementById("lens-hint-b").textContent = "🧽 " + tt("Clean lens"); }
    }
  }
  window.lensPaint = paint;
  if (typeof window.tidyHeader === "function") {                 // main page: after every refresh (as 598)
    const th = window.tidyHeader;
    window.tidyHeader = function (s, c) { const r = th.apply(this, arguments); setTimeout(() => { try { paint(s); } catch (e) {} }, 0); return r; };
  }
})();
</script>
"""
LENS_JS = LENS_JS.replace("/*LNDE*/{}", json.dumps({k: v[0] for k, v in _HX_LINSE.items()}, ensure_ascii=False))
WEB_PAGE = WEB_PAGE.replace("</body>", LENS_JS + "</body>", 1)
