#!/usr/bin/env python3
"""Simulator im Browser: aus dem Godot-Web-Export (Vorlage «Web», 8 Dateien) das Paket sim-web.zip für den Release sim-X.Y.Z.

Warum ein eigenes Paket: der Webspace des Besitzers (MoveEye → Mehr → Homepage, Teil 639zzzh) ersetzt beim Hochladen jeden
Punkt im Dateinamen ausser dem letzten durch «_» (beobachtet: «index.audio.worklet.js» → «index_audio_worklet.js»). Darum hat
im Paket jede Datei genau einen Punkt, und die Verweise darauf sind angepasst:
  index.audio.worklet.js      → index_audio_worklet.js       (index.js: `${loadPath}.audio.worklet.js` → `${loadPath}_audio_worklet.js`)
  index.icon.png              → index_icon.png               (index.html: href)
  index.apple-touch-icon.png  → index_apple-touch-icon.png   (index.html: href)
Dazu (offizielles Paket, wie die vom Besitzer geprüfte Fassung «sim_fix3»):
  - Sandbox-Patch aus sim_web_sandbox.py (index.js / index.html): läuft auch, wenn der Webspace die Seite in einer Sandbox
    ohne allow-same-origin ausliefert (iPhone: «Service Worker is disabled …»).
  - index.pck zusätzlich in Teilen zu 12 MB: index_pck1.wasm … index_pckN.wasm. Der Webspace liefert grosse Dateien in der
    Sandbox ohne CORS aus; die Teile lädt index.html selbst (fetch, Fortschritt), setzt sie zusammen und gibt sie Godot als
    index.pck (preloadFile + --main-pack). index.pck bleibt im Paket, weil MoveEye bis 4.6.0 (Teil 639zzzh, HP_SIM_NAMES)
    es als Pflichtdatei verlangt; die Seite lädt es nicht mehr.
  - Grafikspeicher iPhone / iPad aus sim_web_speicher.py (index.js / index.html): Pixeldichte der Leinwand begrenzt,
    statt alert «WebGL context lost» eine Meldung «Grafikspeicher voll – im Spar-Modus neu laden?» (Besitzer 23.11.2026).
  - Cache-Buster: index.html lädt «index.js?v=<Prüfsumme>», damit ein Handy nach dem Update nicht das alte index.js nimmt.
Die Dateien liegen ohne Ordner in der ZIP (so lädt MoveEye sie nach Sim/ hoch). Nur der Release-Workflow «Sim-Pakete»
(.github/workflows/sim_pi.yml, Paket «web») und die Tests rufen das auf; MoveEye nimmt das Paket nur mit der signierten
Prüfsumme aus versions.json «sim.anhang.web» an (Teil 300).

  python3 werkzeuge/sim_web_paket.py packen EXPORTORDNER ZIEL.zip
  python3 werkzeuge/sim_web_paket.py pruefen PAKET.zip            # Exit 0 = gut (auch für versionen.paket_inhalt «web»)
"""
import hashlib
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_web_sandbox  # noqa: E402
import sim_web_speicher  # noqa: E402

PFLICHT = ("index.html", "index.js", "index.wasm", "index.pck", "index_audio_worklet.js")
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}\.[a-z0-9]{1,12}$")        # genau ein Punkt: der Webspace ändert nichts mehr
MAX_DATEI = 100 * 1024 * 1024                                         # Grenze des Webspace pro Datei
MAX_SUMME = 400 * 1024 * 1024                                         # Platz: 500 MB, dazu Startseite / Funk
WORKLET_ALT = "`${loadPath}.audio.worklet.js`"
WORKLET_NEU = "`${loadPath}_audio_worklet.js`"
TEIL = 12000000                                                       # Bytes pro Teil von index.pck
TEIL_NAME = "index_pck%d.wasm"
TEIL_RE = re.compile(r"^index_pck(\d{1,2})\.wasm$")
JS_TAG_RE = re.compile(r'<script src="index\.js(?:\?v=[0-9a-z]+)?"></script>')
LADER_MARKE = "/*mw-teile*/"
LADER_ALT_RE = re.compile(r"\t\tsetStatusMode\('progress'\);\n\t\tengine\.startGame\(\{.*?\}, displayFailureNotice\);\n", re.S)
LADER_NEU = r"""		setStatusMode('progress');
		/*mw-teile*/ // Webspace des Besitzers: grosse Dateien kommen in der Sandbox ohne CORS - das Pack liegt in Teilen zu 12 MB
		const PARTS = %(parts)s;
		const TOTAL = %(total)d;
		let done = 0;
		const prog = (n) => { done += n; statusProgress.value = done; statusProgress.max = TOTAL; };
		// Speicher (iPhone / iPad, 23.11.2026): die Teile gleich an ihren Platz im einen Puffer schreiben (keine Zwischenkopien)
		// und ihn nach dem Start loslassen - Godot kopiert ihn ins eigene Dateisystem
		let all = new Uint8Array(%(pck)d);
		let pos = 0;
		const put = (u) => {
			if (pos + u.length > all.length) { throw new Error('index.pck: mehr als %(pck)d Bytes'); }
			all.set(u, pos); pos += u.length; prog(u.length);
		};
		const getPart = (f) => fetch(f).then((r) => {
			if (!r.ok) { throw new Error(f + ': ' + r.status); }
			if (!r.body || !r.body.getReader) { return r.arrayBuffer().then((b) => { put(new Uint8Array(b)); }); }
			const rd = r.body.getReader();
			const pump = () => rd.read().then(({ done: d, value }) => { if (d) { return null; } put(value); return pump(); });
			return pump();
		});
		let packP = PARTS.reduce((p, f) => p.then(() => getPart(f)), Promise.resolve()).then(() => {
			if (pos !== %(pck)d) { throw new Error('index.pck: ' + pos + ' statt %(pck)d Bytes'); }
			const buf = all.buffer; all = null;
			return buf;
		});
		engine.config.update({ 'onProgress': function (current, total) { if (current > 0) { statusProgress.value = done + current; statusProgress.max = TOTAL; } } });
		engine.config.args = ['--main-pack', 'index.pck'].concat(engine.config.args);
		Promise.all([engine.init('index'), packP.then((buf) => engine.preloadFile(buf, 'index.pck'))])
			.then(() => { packP = null; return engine.start(); })
			.then(() => { setStatusMode('hidden'); }, displayFailureNotice);
"""


def neuer_name(n):
    a, _, e = n.rpartition(".")
    return a.replace(".", "_") + "." + e if a else n


def packen(ordner, ziel):
    namen = sorted(n for n in os.listdir(ordner) if os.path.isfile(os.path.join(ordner, n)))
    umben = {n: neuer_name(n) for n in namen}
    daten = {}
    for alt, neu in umben.items():
        with open(os.path.join(ordner, alt), "rb") as f:
            daten[neu] = f.read()
    js = daten.get("index.js", b"").decode("utf-8")
    if js.count(WORKLET_ALT) != 1:
        raise SystemExit("index.js: %s nicht genau einmal (andere Godot-Fassung?)" % WORKLET_ALT)
    js = sim_web_speicher.patch_js(sim_web_sandbox.patch_js(js.replace(WORKLET_ALT, WORKLET_NEU)))
    daten["index.js"] = js.encode("utf-8")
    html = sim_web_speicher.patch_html(sim_web_sandbox.patch_html(daten.get("index.html", b"").decode("utf-8")))
    for alt, neu in umben.items():
        if alt != neu and alt.endswith(".png"):
            html = html.replace('"%s"' % alt, '"%s"' % neu)
    pck = daten.get("index.pck", b"")
    if not pck:
        raise SystemExit("index.pck fehlt")
    teile = [TEIL_NAME % (i + 1) for i in range((len(pck) + TEIL - 1) // TEIL)]
    for i, n in enumerate(teile):
        daten[n] = pck[i * TEIL:(i + 1) * TEIL]
    if len(JS_TAG_RE.findall(html)) != 1:
        raise SystemExit("index.html: <script src=\"index.js\"> nicht genau einmal")
    v = hashlib.sha256(daten["index.js"]).hexdigest()[:12]
    html = JS_TAG_RE.sub('<script src="index.js?v=%s"></script>' % v, html)
    if len(LADER_ALT_RE.findall(html)) != 1:
        raise SystemExit("index.html: engine.startGame nicht genau einmal (andere Godot-Fassung?)")
    lader = LADER_NEU % {"parts": "[" + ", ".join("'%s'" % n for n in teile) + "]",
                         "total": len(pck) + len(daten.get("index.wasm", b"")), "pck": len(pck)}
    html = LADER_ALT_RE.sub(lambda m: lader, html)
    daten["index.html"] = html.encode("utf-8")
    tmp = ziel + ".neu"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for n in sorted(daten):
            zi = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))   # feste Zeit: gleicher Export = gleiche ZIP
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, daten[n])
    fehler = pruefen(tmp)
    if fehler:
        os.remove(tmp)
        raise SystemExit("sim-web.zip: " + "; ".join(fehler))
    os.replace(tmp, ziel)
    print("sim-web.zip: %d Dateien, %d Bytes -> %s" % (len(daten), os.path.getsize(ziel), ziel))
    return 0


def pruefen(pfad):
    """[] = gut, sonst die Gründe (dieselben Regeln wie MoveEye hp_sim_files, Teil 639zzzh)"""
    f = []
    try:
        with zipfile.ZipFile(pfad) as z:
            inf = z.infolist()
            namen = [i.filename for i in inf]
            if len(inf) > 16:
                f.append("zu viele Dateien (%d)" % len(inf))
            for i in inf:
                if not NAME_RE.match(i.filename):
                    f.append("Name %r: genau ein Punkt, ohne Ordner" % i.filename[:80])
                if i.file_size > MAX_DATEI:
                    f.append("%s grösser als 100 MB" % i.filename)
            if sum(i.file_size for i in inf) > MAX_SUMME:
                f.append("zusammen grösser als 400 MB")
            for p in PFLICHT:
                if p not in namen:
                    f.append("%s fehlt" % p)
            if not f:
                js = z.read("index.js").decode("utf-8", "replace")
                if WORKLET_NEU not in js or WORKLET_ALT in js:
                    f.append("index.js lädt nicht index_audio_worklet.js")
                html = z.read("index.html").decode("utf-8", "replace")
                if "index.js" not in html or re.search(r'(?:href|src)="index\.[^".]+\.[a-z]+"', html):
                    f.append("index.html verweist auf einen Namen mit zwei Punkten")
                if z.read("index.wasm")[:4] != b"\0asm":
                    f.append("index.wasm ist kein WebAssembly")
                if sim_web_sandbox.MARKE_JS not in js or sim_web_sandbox.MARKE_HTML not in html:
                    f.append("Sandbox-Patch fehlt")
                if sim_web_speicher.MARKE_JS not in js or sim_web_speicher.MARKE_HTML not in html:
                    f.append("Grafikspeicher-Patch fehlt (sim_web_speicher.py)")
                m = re.search(r'<script src="index\.js\?v=([0-9a-f]{12})"></script>', html)
                if not m or m.group(1) != hashlib.sha256(z.read("index.js")).hexdigest()[:12]:
                    f.append("index.html lädt index.js nicht mit ?v=<Prüfsumme>")
                nr = sorted(int(TEIL_RE.match(n).group(1)) for n in namen if TEIL_RE.match(n))
                pck = z.read("index.pck")
                teile = [TEIL_NAME % i for i in nr]
                if not nr or nr != list(range(1, len(nr) + 1)) or b"".join(z.read(n) for n in teile) != pck \
                        or any(z.getinfo(n).file_size > TEIL for n in teile):
                    f.append("index_pck1..N.wasm fehlen oder ergeben nicht index.pck")
                elif LADER_MARKE not in html or "const PARTS = [%s];" % ", ".join("'%s'" % n for n in teile) not in html:
                    f.append("index.html lädt die Teile index_pck1..N.wasm nicht")
    except (OSError, zipfile.BadZipFile, KeyError) as e:
        f.append("keine gültige ZIP (%s)" % e.__class__.__name__)
    return f


def main(a):
    if len(a) == 3 and a[0] == "packen":
        return packen(a[1], a[2])
    if len(a) == 2 and a[0] == "pruefen":
        f = pruefen(a[1])
        print("sim-web.zip:", "; ".join(f) if f else "ok")
        return 1 if f else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
