#!/usr/bin/env python3
"""Test für sim_web_sandbox.py (ohne Godot-Export, ohne Browser; Node nur wenn vorhanden):
  1. jede Godot-Stelle wird genau einmal ersetzt, zweiter Lauf ändert nichts, fehlt eine Stelle -> Abbruch (SystemExit)
  2. Node: gepatchtes _godot_js_pwa_cb / _godot_js_pwa_update werfen NICHT, wenn schon das Lesen von navigator.serviceWorker
     wirft (so in Safari und Chromium bei «sandbox» ohne allow-same-origin); IDBFS.indexedDB wirft in der Herkunft «null»
     (fällt so im try von getDB auf RAM zurück), sonst nicht
  3. optional: --ordner EXPORT (echter Godot-4.3-Export, index.js / index.html) wird fehlerfrei gepatcht, Node --check

    python3 werkzeuge/sim_web_sandbox_test.py [--ordner EXPORTORDNER]     # Ende: «Sim-Web-Sandbox-Test OK» (Exit 0)
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_web_sandbox as sb  # noqa: E402

FEHLER = []


def ok(bed, was):
    print(("  ok: " if bed else "  FEHLER: ") + was)
    if not bed:
        FEHLER.append(was)


def wirft(fn, *a):
    try:
        fn(*a)
    except SystemExit:
        return True
    return False


# künstliches index.js aus genau den Stellen der Godot-4.3-Fassung
JS = ("var GodotRuntime={get_func:function(f){return f}};var GodotPWA={hasUpdate:true,updateState:function(cb,reg){}};"
      "var IDBFS={" + sb.JS_ERSATZ[2][0] + "return null}};\n"
      + sb.JS_ERSATZ[0][0] + sb.JS_ERSATZ[1][0] + "\nclass E{x(){\n\t\t\t\t" + sb.JS_ERSATZ[3][0] + "\n\t\t\t\t}\n\t\t\t\treturn null;}}\n")
HTML = "<script>\n(function(){\n" + sb.HTML_ALT + "\t}\n}());\n</script>\n"

print("1. Ersetzen")
j1 = sb.patch_js(JS)
ok(j1 != JS and sb.MARKE_JS in j1, "index.js gepatcht")
ok(all(neu in j1 for _, neu in sb.JS_ERSATZ), "alle %d Stellen ersetzt" % len(sb.JS_ERSATZ))
ok(sb.patch_js(j1) == j1, "zweiter Lauf ändert nichts")
for i, (alt, _) in enumerate(sb.JS_ERSATZ):
    ok(wirft(sb.patch_js, JS.replace(alt, "")), "Stelle %d fehlt -> Abbruch" % i)
ok(wirft(sb.patch_js, JS + sb.JS_ERSATZ[0][0]), "Stelle doppelt -> Abbruch")
h1 = sb.patch_html(HTML)
ok(h1 != HTML and sb.patch_html(h1) == h1, "index.html gepatcht, zweiter Lauf ändert nichts")
ok(wirft(sb.patch_html, HTML.replace(sb.HTML_ALT, "")), "index.html ohne displayFailureNotice -> Abbruch")

node = shutil.which("node")
print("2. Node" + ("" if node else " (nicht vorhanden - übersprungen)"))
if node:
    prog = (r"""
const NAV = {}; Object.defineProperty(NAV, 'serviceWorker', {get() { throw new Error("SecurityError: Service Worker is disabled because the context is sandboxed and lacks the 'allow-same-origin' flag"); }});
globalThis.navigator = NAV; globalThis.self = {origin: 'null'}; globalThis.indexedDB = {open() { return {}; }};
""" + j1.replace("class E", "globalThis.E=class E") + r"""
let r = [];
try { _godot_js_pwa_cb(function () {}); r.push('cb-ok'); } catch (e) { r.push('cb-WIRFT ' + e.message); }
try { r.push('update=' + _godot_js_pwa_update()); } catch (e) { r.push('update-WIRFT ' + e.message); }
try { IDBFS.indexedDB(); r.push('idb-null-KEIN-FEHLER'); } catch (e) { r.push('idb-null-wirft'); }
self.origin = 'https://kevlaschef.com';
try { r.push(IDBFS.indexedDB() ? 'idb-normal-ok' : 'idb-normal-LEER'); } catch (e) { r.push('idb-normal-WIRFT'); }
console.log(r.join(' '));
""")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.js")
        with open(p, "w", encoding="utf-8") as f:
            f.write(prog)
        out = subprocess.run([node, p], capture_output=True, text=True, timeout=60)
    s = (out.stdout + out.stderr).strip()
    ok("cb-ok" in s, "_godot_js_pwa_cb wirft nicht (%s)" % s[:160])
    ok("update=1" in s, "_godot_js_pwa_update gibt 1 zurück")
    ok("idb-null-wirft" in s, "IDBFS.indexedDB wirft in Herkunft «null»")
    ok("idb-normal-ok" in s, "IDBFS.indexedDB normal unverändert")

if "--ordner" in sys.argv:
    o = sys.argv[sys.argv.index("--ordner") + 1]
    print("3. Export " + o)
    with open(os.path.join(o, "index.js"), encoding="utf-8") as f:
        ej = f.read()
    with open(os.path.join(o, "index.html"), encoding="utf-8") as f:
        eh = f.read()
    ok(not wirft(sb.patch_js, ej), "echtes index.js patchbar")
    ok(not wirft(sb.patch_html, eh), "echtes index.html patchbar")
    if node and not FEHLER:
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "index.js")
            with open(p, "w", encoding="utf-8") as f:
                f.write(sb.patch_js(ej))
            ok(subprocess.run([node, "--check", p]).returncode == 0, "node --check index.js")

if FEHLER:
    print("Sim-Web-Sandbox-Test FEHLER: %d" % len(FEHLER))
    sys.exit(1)
print("Sim-Web-Sandbox-Test OK")
