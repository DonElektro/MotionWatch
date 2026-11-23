#!/usr/bin/env python3
"""Simulator im Browser: Grafikspeicher auf iPhone / iPad (Besitzer 23.11.2026, iPad Pro 12.9": beim Laden «WebGL context
lost, please reload the page» als Meldung des Browsers, am PC gut).

Safari gibt einer Seite nur wenig Grafikspeicher und nimmt ihn bei Knappheit ganz weg («context lost»). Godot 4.3 zeichnet die
Leinwand mit der vollen Pixeldichte (iPad Pro: 2 -> 2732 × 2048 Bildpunkte) und meldet einen Verlust nur mit alert().
Dieser Patch (für sim_web_paket.py, wie sim_web_sandbox.py: Text rein, Text raus, jede Stelle genau einmal):
  index.js
    - GodotDisplayScreen.getPixelRatio fragt window.mwPixelRatio(d): die Pixeldichte der Leinwand begrenzt
      (iPhone / iPad automatisch höchstens 1.5 und rund 3.2 Mio. Bildpunkte; mit ?lite=1 überall 1.0 und 1.6 Mio.;
      sonst unverändert). Dieselbe Zahl liefert Godot DisplayServer.screen_get_scale -> Oberfläche und Leinwand passen.
    - «webglcontextlost»: statt alert() window.mwContextLost(ev) (Rückfall: das alte alert).
  index.html (vor <script src="index.js">)
    - eine Meldung in der Seite, 5 Sprachen (?sprache=… oder Sprache des Browsers): «Grafikspeicher voll – im Spar-Modus
      neu laden?» mit den Knöpfen «Im Spar-Modus neu laden» (dieselbe Adresse mit lite=1) und «Normal neu laden»;
      ist lite=1 schon an: Hinweis, andere Tabs / Apps zu schliessen, und «Neu laden».
Im Spiel (scripts/web.gd spar()) gilt dazu: iOS bzw. lite=1 -> kein MSAA, 3D-Ansicht höchstens 1.8 bzw. 1.0 Mio. Bildpunkte,
lite=1 ohne Sonnenschatten.

  python3 werkzeuge/sim_web_speicher.py ORDNER      # patcht ORDNER/index.js und ORDNER/index.html (mehrfach aufrufbar)
  from sim_web_speicher import patch_js, patch_html  # für sim_web_paket.py
Test: werkzeuge/sim_web_speicher_test.py (Node + Chromium: WEBGL_lose_context -> Meldung statt alert).
"""
import os
import sys

MARKE_JS = "/*mw-gpu*/"
MARKE_HTML = "<!--mw-gpu-->"

JS_ERSATZ = (
    ('getPixelRatio:function(){return GodotDisplayScreen.hidpi?window.devicePixelRatio||1:1}',
     'getPixelRatio:function(){' + MARKE_JS + 'const d=window.devicePixelRatio||1;if(!GodotDisplayScreen.hidpi){return 1}'
     'try{if(typeof window.mwPixelRatio==="function"){const r=+window.mwPixelRatio(d);if(r>0&&r<=d){return r}}}catch(e){}return d}'),
    ('GodotEventListeners.add(canvas,"webglcontextlost",function(ev){alert("WebGL context lost, please reload the page");ev.preventDefault()},false)',
     'GodotEventListeners.add(canvas,"webglcontextlost",function(ev){ev.preventDefault();'
     'try{if(typeof window.mwContextLost==="function"){window.mwContextLost(ev);return}}catch(e){}'
     'alert("WebGL context lost, please reload the page")},false)'),
)

SCRIPT_TAG = '<script src="index.js"></script>'

# Texte: Schlüssel = Sprache; t = Titel, p = Erklärung, a = Knopf Spar-Modus, b = Knopf normal, pl / bl = schon im Spar-Modus
TEXTE = {
    "de": {"t": "Grafikspeicher voll – im Spar-Modus neu laden?",
           "p": "Das Gerät hat dem Simulator den Grafikspeicher entzogen. Im Spar-Modus (kleinere Auflösung, einfachere Grafik) "
                "läuft er meist auch auf iPad und Handy.",
           "a": "Im Spar-Modus neu laden", "b": "Normal neu laden",
           "pl": "Auch im Spar-Modus reicht der Grafikspeicher nicht. Bitte andere Tabs und Apps schliessen und neu laden.",
           "bl": "Neu laden"},
    "fr": {"t": "Mémoire graphique pleine – recharger en mode économie ?",
           "p": "L’appareil a retiré la mémoire graphique au simulateur. En mode économie (résolution réduite, graphismes "
                "simplifiés), il fonctionne généralement aussi sur iPad et smartphone.",
           "a": "Recharger en mode économie", "b": "Recharger normalement",
           "pl": "Même en mode économie, la mémoire graphique ne suffit pas. Fermez les autres onglets et applications, puis rechargez.",
           "bl": "Recharger"},
    "it": {"t": "Memoria grafica piena – ricaricare in modalità risparmio?",
           "p": "Il dispositivo ha tolto la memoria grafica al simulatore. In modalità risparmio (risoluzione ridotta, grafica "
                "semplificata) di solito funziona anche su iPad e smartphone.",
           "a": "Ricarica in modalità risparmio", "b": "Ricarica normalmente",
           "pl": "Anche in modalità risparmio la memoria grafica non basta. Chiudi le altre schede e app e ricarica.",
           "bl": "Ricarica"},
    "rm": {"t": "Memoria grafica plaina – chargiar danovamain en il modus da spargn?",
           "p": "L’apparat ha retratg la memoria grafica al simulatur. En il modus da spargn (resoluziun pli pitschna, grafica "
                "pli simpla) funcziunescha el per ordinari er sin iPad e telefonin.",
           "a": "Chargiar danovamain en il modus da spargn", "b": "Chargiar danovamain normal",
           "pl": "Er en il modus da spargn na basta la memoria grafica betg. Serra p.pl. autras tabs ed apps e chargia danovamain.",
           "bl": "Chargiar danovamain"},
    "en": {"t": "Graphics memory full – reload in saver mode?",
           "p": "The device took the graphics memory away from the simulator. In saver mode (lower resolution, simpler graphics) "
                "it usually runs on iPad and phones too.",
           "a": "Reload in saver mode", "b": "Reload normally",
           "pl": "Even in saver mode there is not enough graphics memory. Please close other tabs and apps, then reload.",
           "bl": "Reload"},
}


def _block():
    import json
    tx = json.dumps(TEXTE, ensure_ascii=False, sort_keys=True)
    return MARKE_HTML + r"""
		<style>
#mw-gpu{position:fixed;left:0;top:0;right:0;bottom:0;z-index:10;display:none;align-items:center;justify-content:center;
	background:rgba(11,18,32,.94);padding:16px;box-sizing:border-box}
#mw-gpu.on{display:flex}
#mw-gpu .box{max-width:440px;width:100%;box-sizing:border-box;background:#172134;color:#e6ebf4;border:1px solid #f59a4a;
	border-radius:12px;padding:20px;font:16px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;text-align:center}
#mw-gpu h2{margin:0 0 10px;font-size:20px;line-height:1.3}
#mw-gpu p{margin:0 0 16px;color:#b8c2d6}
#mw-gpu button{display:block;width:100%;min-height:44px;margin:10px 0 0;padding:8px 12px;border-radius:8px;font:inherit;
	font-weight:600;cursor:pointer;border:1px solid #3a4866;background:transparent;color:#e6ebf4}
#mw-gpu button.a{background:#f59a4a;border-color:#f59a4a;color:#14181f}
#mw-gpu button:focus-visible{outline:3px solid #fff;outline-offset:2px}
		</style>
		<div id="mw-gpu" role="alertdialog" aria-modal="true" aria-labelledby="mw-gpu-t" aria-describedby="mw-gpu-p"><div class="box">
			<h2 id="mw-gpu-t"></h2><p id="mw-gpu-p"></p>
			<button type="button" class="a" id="mw-gpu-a"></button><button type="button" id="mw-gpu-b"></button>
		</div></div>
		<script>
(function () {
	/* Grafikspeicher iPhone / iPad (werkzeuge/sim_web_speicher.py) */
	const TX = """ + tx + r""";
	let q;
	try { q = new URLSearchParams(location.search); } catch (e) { q = new URLSearchParams(''); }
	const lite = /^(1|true|ja|an|on)$/i.test(q.get('lite') || '');
	const ua = navigator.userAgent || '';
	const ios = /iPad|iPhone|iPod/.test(ua) || (/Mac/.test(navigator.platform || '') && navigator.maxTouchPoints > 1);
	const MAX_DPR = lite ? 1 : (ios ? 1.5 : 0);
	const MAX_PX = lite ? 1.6e6 : (ios ? 3.2e6 : 0);
	window.mwGpu = { ios: ios, lite: lite, maxDpr: MAX_DPR, maxPx: MAX_PX, lost: 0 };
	window.mwPixelRatio = function (d) {
		let r = d;
		if (MAX_DPR && r > MAX_DPR) { r = MAX_DPR; }
		if (MAX_PX) {
			const css = Math.max(1, (window.innerWidth || 1) * (window.innerHeight || 1));
			const m = Math.sqrt(MAX_PX / css);
			if (r > m) { r = m; }
		}
		return Math.max(r, Math.min(d, 1));
	};
	function lang() {
		const s = (q.get('sprache') || navigator.language || 'de').slice(0, 2).toLowerCase();
		return TX[s] ? s : (s === 'gs' ? 'de' : 'en');
	}
	function reload(withLite) {
		if (withLite) { q.set('lite', '1'); } else { q.delete('lite'); }
		const s = q.toString();
		location.href = location.pathname + (s ? '?' + s : '') + location.hash;
	}
	window.mwContextLost = function (ev) {
		window.mwGpu.lost += 1;
		console.warn('MoveEye Sim: WebGL context lost (lite=' + lite + ', ios=' + ios + ')');
		const box = document.getElementById('mw-gpu');
		if (!box) { return; }
		const t = TX[lang()];
		document.getElementById('mw-gpu-t').textContent = t.t;
		document.getElementById('mw-gpu-p').textContent = lite ? t.pl : t.p;
		const a = document.getElementById('mw-gpu-a');
		const b = document.getElementById('mw-gpu-b');
		a.textContent = lite ? t.bl : t.a;
		a.onclick = function () { reload(true); };
		b.textContent = t.b;
		b.style.display = lite ? 'none' : '';
		b.onclick = function () { reload(false); };
		box.classList.add('on');
		try { a.focus(); } catch (e) { /* nichts */ }
	};
}());
		</script>
		"""


def patch_js(js):
    if MARKE_JS in js:
        return js
    for alt, neu in JS_ERSATZ:
        n = js.count(alt)
        if n != 1:
            raise SystemExit("index.js: Stelle %d-mal statt genau einmal gefunden (andere Godot-Fassung?): %s…" % (n, alt[:70]))
        js = js.replace(alt, neu)
    return js


def patch_html(html):
    if MARKE_HTML in html:
        return html
    n = html.count(SCRIPT_TAG)
    if n != 1:
        raise SystemExit("index.html: %s %d-mal statt genau einmal gefunden" % (SCRIPT_TAG, n))
    return html.replace(SCRIPT_TAG, _block() + SCRIPT_TAG)


def ordner_patchen(ordner):
    for name, fn in (("index.js", patch_js), ("index.html", patch_html)):
        p = os.path.join(ordner, name)
        with open(p, encoding="utf-8") as f:
            alt = f.read()
        neu = fn(alt)
        if neu != alt:
            tmp = p + ".neu"
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(neu)
            os.replace(tmp, p)
            print("%s: gepatcht (Grafikspeicher)" % p)
        else:
            print("%s: schon gepatcht" % p)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(ordner_patchen(sys.argv[1]))
