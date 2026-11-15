#!/usr/bin/env python3
"""Simulator im Browser: Godot-4.3-Web-Export auch in einer Sandbox ohne «allow-same-origin» lauffähig machen.

Beobachtet (iPhone, Webspace des Besitzers): die Seite kommt mit «Content-Security-Policy: sandbox allow-scripts …» ohne
allow-same-origin -> Herkunft «null». Dann wirft schon das LESEN von navigator.serviceWorker (Safari und Chromium) einen
SecurityError. Godot ruft das in _godot_js_pwa_cb beim Start aus WebAssembly auf -> der Start bricht nach dem Fortschritt ab:
  «Service Worker is disabled because the context is sandboxed and lacks the 'allow-same-origin' flag»
IndexedDB (user://) ist dort ebenfalls gesperrt - Godot fällt dann von selbst auf Speicher im RAM zurück (die Demo speichert
nichts Wichtiges); hier wird IndexedDB in der Herkunft «null» gar nicht erst angefasst.

Was NICHT ohne den Server geht: index.wasm / index.pck / index_audio_worklet.js werden per fetch / addModule geladen; aus der
Herkunft «null» ist das eine fremde Anfrage (Origin: null) und braucht «Access-Control-Allow-Origin: *» (oder der Server gibt
allow-same-origin in der Sandbox frei). Fehlt beides, zeigt index.html jetzt eine klare Meldung dazu statt «Failed to fetch».

  python3 werkzeuge/sim_web_sandbox.py ORDNER      # patcht ORDNER/index.js und ORDNER/index.html (mehrfach aufrufbar)
  from sim_web_sandbox import patch_js, patch_html  # für sim_web_paket.py: Text rein, Text raus; Fehler = SystemExit
"""
import os
import sys

MARKE_JS = "/*mw-sandbox*/"
MARKE_HTML = "/*mw-sandbox*/"

# (alt, neu) - jedes «alt» muss genau einmal vorkommen, sonst ist es eine andere Godot-Fassung -> Abbruch
JS_ERSATZ = (
    # Service-Worker-Abfrage beim Start: Lesen von navigator.serviceWorker darf werfen, Promise darf scheitern
    ('function _godot_js_pwa_cb(p_update_cb){if("serviceWorker"in navigator){const cb=GodotRuntime.get_func(p_update_cb);'
     'navigator.serviceWorker.getRegistration().then(GodotPWA.updateState.bind(null,cb))}}',
     'function _godot_js_pwa_cb(p_update_cb){' + MARKE_JS + 'try{if("serviceWorker"in navigator){const cb=GodotRuntime.get_func(p_update_cb);'
     'navigator.serviceWorker.getRegistration().then(GodotPWA.updateState.bind(null,cb)).catch(function(){})}}catch(e){}}'),
    ('function _godot_js_pwa_update(){if("serviceWorker"in navigator&&GodotPWA.hasUpdate){navigator.serviceWorker.getRegistration()'
     '.then(function(reg){if(!reg||!reg.waiting){return}reg.waiting.postMessage("update")});return 0}return 1}',
     'function _godot_js_pwa_update(){try{if("serviceWorker"in navigator&&GodotPWA.hasUpdate){navigator.serviceWorker.getRegistration()'
     '.then(function(reg){if(!reg||!reg.waiting){return}reg.waiting.postMessage("update")}).catch(function(){});return 0}}catch(e){}return 1}'),
    # IndexedDB in der Herkunft «null»: gar nicht anfassen (Safari kann schon beim Lesen werfen) -> Godot nimmt RAM für user://
    ('indexedDB:()=>{if(typeof indexedDB!="undefined")return indexedDB;',
     'indexedDB:()=>{if(typeof self=="object"&&self.origin==="null")throw new Error("opaque origin (sandbox): no IndexedDB");'
     'if(typeof indexedDB!="undefined")return indexedDB;'),
    # Engine.installServiceWorker (nur mit PWA): auch hier das Lesen absichern
    ("if (this.config.serviceWorker && 'serviceWorker' in navigator) {\n\t\t\t\t\treturn navigator.serviceWorker.register(this.config.serviceWorker);",
     "if (this.config.serviceWorker && 'serviceWorker' in navigator) {\n\t\t\t\t\ttry { return navigator.serviceWorker.register(this.config.serviceWorker); }"
     " catch (e) { return Promise.reject(e); }"),
)

# index.html: verständliche Meldung, wenn in der Sandbox der Server das Laden verweigert (fehlendes CORS)
HTML_ALT = "\tfunction displayFailureNotice(err) {\n\t\tconsole.error(err);\n"
HTML_NEU = (
    "\tfunction displayFailureNotice(err) {\n\t\tconsole.error(err);\n"
    "\t\t" + MARKE_HTML + "\n"
    "\t\ttry {\n"
    "\t\t\tif (self.origin === 'null' && location.protocol !== 'file:' && err && /fetch|load|network|import/i.test(String(err.message || err))) {\n"
    "\t\t\t\terr = new Error('Der Server liefert die Seite in einer Sandbox (Herkunft «null») und erlaubt das Laden der Dateien nicht.\\n'\n"
    "\t\t\t\t\t+ 'Server: bitte «Access-Control-Allow-Origin: *» senden oder in der Sandbox «allow-same-origin» erlauben.\\n'\n"
    "\t\t\t\t\t+ 'The server sandboxes this page (origin \"null\") and blocks loading the files: it must send '\n"
    "\t\t\t\t\t+ '\"Access-Control-Allow-Origin: *\" or add \"allow-same-origin\" to the sandbox.\\n(' + String(err.message || err) + ')');\n"
    "\t\t\t}\n"
    "\t\t} catch (e) { /* nichts */ }\n"
)


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
    n = html.count(HTML_ALT)
    if n != 1:
        raise SystemExit("index.html: displayFailureNotice %d-mal statt genau einmal gefunden" % n)
    return html.replace(HTML_ALT, HTML_NEU)


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
            print("%s: gepatcht (Sandbox)" % p)
        else:
            print("%s: schon gepatcht" % p)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(ordner_patchen(sys.argv[1]))
