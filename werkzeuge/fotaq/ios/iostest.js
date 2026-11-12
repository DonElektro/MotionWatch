/* MoveEye: «Queen – iPhone-Test» - picks the test variant of the engine and shows a diagnostics line that a screenshot can
   carry: device, variant, step 1-3, run time, memory, data read, sound. The last runs stay in this browser (localStorage),
   also after a crash: a run that did not end properly is marked. Loaded before the launcher script of index.html. */
(function () {
  "use strict";
  var d = document, KEY = "fotaq-iostest-runs", q = new URLSearchParams(location.search);
  var V = (q.get("v") || "a").toLowerCase().replace(/[^a-z]/g, "") || "a", MAN = null, run = null, acs = [];
  window.FOTAQ_VAR = V;
  function de() { return (d.documentElement.lang || "de") === "de"; }
  function dev() {
    var ua = navigator.userAgent || "", m = /OS (\d+)[_.](\d+)(?:[_.](\d+))?/.exec(ua), s = /Version\/([\d.]+)/.exec(ua);
    if (/iPhone|iPod/.test(ua)) return "iPhone iOS " + (m ? m[1] + "." + m[2] + (m[3] ? "." + m[3] : "") : "?");
    if (/iPad/.test(ua)) return "iPad iPadOS " + (m ? m[1] + "." + m[2] : "?");
    if (/Macintosh/.test(ua) && (navigator.maxTouchPoints || 0) > 0) return "iPad (Safari " + (s ? s[1] : "?") + ")";
    var c = /(Chrome|Firefox|Edg)\/(\d+)/.exec(ua);
    return c ? c[1] + " " + c[2] : (s ? "Safari " + s[1] : "Browser");
  }
  function mmss(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ":" + ("0" + s % 60).slice(-2); }
  function runs() { try { return JSON.parse(localStorage.getItem(KEY) || "[]") || []; } catch (e) { return []; } }
  function save(a) { try { localStorage.setItem(KEY, JSON.stringify(a.slice(-8))); } catch (e) {} }
  function vinfo(id) { var x = null; ((MAN || {}).varianten || []).forEach(function (v) { if (v.id === id) x = v; }); return x; }
  function stepTxt(n) {
    return de() ? ["Start gedrückt", "Schritt 1: Programm geladen", "Schritt 2: Spieldaten", "Schritt 3: gestartet"][n]
                : ["start pressed", "step 1: program loaded", "step 2: game data", "step 3: started"][n];
  }
  // sound: iOS starts an AudioContext only after a tap - keep every context and resume it on the next tap
  ["AudioContext", "webkitAudioContext"].forEach(function (n) {
    var O = window[n]; if (!O) return;
    var W = function (o) { var c = o === undefined ? new O() : new O(o); acs.push(c); return c; };
    W.prototype = O.prototype; try { Object.setPrototypeOf(W, O); } catch (e) {}
    window[n] = W;
  });
  ["touchend", "click", "keydown"].forEach(function (ev) { addEventListener(ev, function () {
    acs.forEach(function (c) { if (c.state === "suspended" && c.resume) c.resume().catch(function () {}); }); }, true); });

  window.FOTAQ_DIAG = function () {
    var F = window.FOTAQ || {}, M = window.Module || {}, st = window.httpFsStat || {requests: 0, bytes: 0, errors: 0, last: ""};
    var step = 0, log = (F.log || []).join("\n"), ld = d.getElementById("load");
    if (F.ready) step = 1;
    if (step && st.requests > 0) step = 2;
    if (step === 2 && /data\/games\//.test(st.last || "") && st.requests >= 3 && /User picked target/.test(log) && ld && ld.classList.contains("hidden")) step = 3;
    if (run && run.step > step) step = run.step;
    var heap = 0; try { heap = M.HEAPU8 ? M.HEAPU8.length : 0; } catch (e) {}
    var vi = vinfo(V) || {}, a = acs[acs.length - 1];
    return {v: V, lang: F.lang || "", dev: dev(), step: step, sec: F.t0 ? (Date.now() - F.t0) / 1000 : 0, wasm: vi.wasm || 0, heap: heap,
      js: (performance.memory || {}).usedJSHeapSize || 0, req: st.requests, bytes: st.bytes, errors: st.errors,
      audio: a ? a.state + " " + a.sampleRate : "-", tag: (MAN || {}).tag || ""};
  };
  function line(x) {
    var mb = function (n) { return (n / 1048576).toFixed(n < 10485760 ? 1 : 0) + " MB"; };
    return "Test " + x.v.toUpperCase() + " · " + x.dev + " · wasm " + mb(x.wasm) + " · " + stepTxt(x.step) + " · " + mmss(x.sec)
      + " · " + (de() ? "Speicher " : "memory ") + (x.heap ? mb(x.heap) : "?") + (x.js ? " + JS " + mb(x.js) : "")
      + " · " + (de() ? "Daten " : "data ") + mb(x.bytes) + "/" + x.req + (x.errors ? " · " + x.errors + (de() ? " Fehler" : " errors") : "")
      + " · " + (de() ? "Ton " : "sound ") + x.audio;
  }
  function tick() {
    if (!window.FOTAQ || !d.body.classList.contains("play")) return;
    var x = window.FOTAQ_DIAG(), z = d.getElementById("dz");
    if (z) z.textContent = line(x);
    if (!run) { run = {v: x.v, L: x.lang, at: new Date().toTimeString().slice(0, 5), dev: x.dev, step: 0, sec: 0, clean: false, err: ""}; var a = runs(); a.push(run); save(a); }
    run.step = x.step; run.sec = Math.round(x.sec); run.heap = x.heap; run.req = x.req;
    var b = runs(); b[b.length - 1] = run; save(b);
  }
  setInterval(tick, 1000);
  addEventListener("pagehide", function () { if (run) { run.clean = true; var b = runs(); b[b.length - 1] = run; save(b); } });
  addEventListener("error", function (e) { if (run && !run.err) run.err = String(e.message || e).slice(0, 80); });

  function paint() {
    var box = d.getElementById("vars"), hist = d.getElementById("hist");
    if (box && MAN) {
      box.textContent = "";
      (MAN.varianten || []).forEach(function (v) {
        var a = d.createElement("a"); a.href = "?v=" + v.id; a.className = "var" + (v.id === V ? " on" : ""); a.id = "var-" + v.id;
        var b = d.createElement("b"); b.textContent = "Test " + v.id.toUpperCase() + (v.id === V ? " ✓" : "");
        var s = d.createElement("span"); s.textContent = (de() ? v.de : v.en) + " · wasm " + (v.wasm / 1048576).toFixed(1) + " MB";
        a.appendChild(b); a.appendChild(s); box.appendChild(a);
      });
    }
    if (hist) {
      var a = runs(); hist.textContent = "";
      var h = d.createElement("b"); h.textContent = (de() ? "Gerät: " : "Device: ") + dev() + (MAN ? " · " + MAN.tag : ""); hist.appendChild(h);
      a.slice().reverse().forEach(function (r) {
        var p = d.createElement("div");
        p.textContent = r.at + " · Test " + String(r.v).toUpperCase() + " " + (r.L || "") + " · " + stepTxt(r.step || 0) + " · " + mmss(r.sec || 0)
          + (r.heap ? " · " + Math.round(r.heap / 1048576) + " MB" : "") + " · "
          + (r.clean ? (de() ? "sauber beendet" : "ended properly") : (de() ? "NICHT sauber beendet (Absturz?)" : "did NOT end properly (crash?)")) + (r.err ? " · " + r.err : "");
        if (!r.clean) p.className = "bad";
        hist.appendChild(p);
      });
      if (!a.length) { var n = d.createElement("div"); n.textContent = de() ? "Noch kein Lauf. Eine Variante wählen, dann die Sprache antippen." : "No run yet. Pick a variant, then tap a language."; hist.appendChild(n); }
    }
  }
  addEventListener("DOMContentLoaded", function () {
    paint();
    fetch("fotaqtest.json", {cache: "no-store"}).then(function (r) { return r.json(); }).then(function (j) {
      MAN = j; if (!vinfo(V)) { V = ((j.varianten || [])[0] || {}).id || "a"; window.FOTAQ_VAR = V; } paint(); }).catch(function () {});
    d.querySelectorAll(".langs button").forEach(function (b) { b.addEventListener("click", function () { setTimeout(paint, 50); }); });
  });
})();
