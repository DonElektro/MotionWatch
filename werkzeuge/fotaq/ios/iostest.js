/* MoveEye: «Queen – iPhone-Test» - picks the test variant of the engine and shows a diagnostics line that a screenshot can
   carry: device, variant, step 1-3, run time, memory, data read, sound. The last runs stay in this browser (localStorage),
   also after a crash: a run that did not end properly is marked. Loaded before the launcher script of index.html.
   Second round (after the first test on the iPhone): the game ends cleanly («Spiel beendet», never ScummVM's launcher),
   an error stays on the screen with «Fehler kopieren» (no black screen) and is kept with the run, the line hides itself
   after the start (button «ⓘ»), saved games are written to the browser store when the page goes to the background, and a
   short report (no addresses, no names) goes to MoveEye for the administrator (Mehr → Spielecke). */
(function () {
  "use strict";
  var d = document, KEY = "fotaq-iostest-runs", q = new URLSearchParams(location.search);
  var V = (q.get("v") || "a").toLowerCase().replace(/[^a-z]/g, "") || "a", MAN = null, run = null, acs = [];
  var fatalTxt = "", fatalKind = "", ended = false, showLine = true, hideAt = 0, sent = {};
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
    if (step === 3 && !hideAt) hideAt = Date.now() + 6000;
    var heap = 0; try { heap = M.HEAPU8 ? M.HEAPU8.length : 0; } catch (e) {}
    var vi = vinfo(V) || {}, a = acs[acs.length - 1];
    return {v: V, lang: F.lang || "", dev: dev(), step: step, sec: F.t0 ? (Date.now() - F.t0) / 1000 : 0, wasm: vi.wasm || 0, heap: heap,
      js: (performance.memory || {}).usedJSHeapSize || 0, req: st.requests, bytes: st.bytes, errors: st.errors,
      retries: st.retries || 0, audio: a ? a.state + " " + a.sampleRate : "-", tag: (MAN || {}).tag || "",
      ended: ended, kind: fatalKind, err: fatalTxt};
  };
  function line(x) {
    var mb = function (n) { return (n / 1048576).toFixed(n < 10485760 ? 1 : 0) + " MB"; };
    return "Test " + x.v.toUpperCase() + " · " + x.dev + " · wasm " + mb(x.wasm) + " · " + stepTxt(x.step) + " · " + mmss(x.sec)
      + " · " + (de() ? "Speicher " : "memory ") + (x.heap ? mb(x.heap) : "?") + (x.js ? " + JS " + mb(x.js) : "")
      + " · " + (de() ? "Daten " : "data ") + mb(x.bytes) + "/" + x.req + (x.errors ? " · " + x.errors + (de() ? " Fehler" : " errors") : "")
      + (x.retries ? " · " + x.retries + (de() ? " Wiederholungen" : " retries") : "")
      + " · " + (de() ? "Ton " : "sound ") + x.audio + (x.ended ? (de() ? " · Spiel beendet" : " · game ended") : "")
      + (x.err ? " · " + (de() ? "FEHLER: " : "ERROR: ") + x.err.slice(0, 160) : "");
  }
  function tick() {
    if (!window.FOTAQ || !d.body.classList.contains("play")) return;
    var x = window.FOTAQ_DIAG(), z = d.getElementById("dz");
    if (z) { z.textContent = line(x); z.classList.toggle("hidden", !(showLine || x.step < 3 || Date.now() < hideAt || x.err)); }
    if (x.step === 3) report("start");
    if (!run) { run = {v: x.v, L: x.lang, at: new Date().toTimeString().slice(0, 5), dev: x.dev, step: 0, sec: 0, clean: false, err: ""}; var a = runs(); a.push(run); save(a); }
    if (ended || fatalTxt) return;                      // the record of an ended run stays as it is
    run.step = x.step; run.sec = Math.round(x.sec); run.heap = x.heap; run.req = x.req;
    var b = runs(); b[b.length - 1] = run; save(b);
  }
  setInterval(tick, 1000);
  function keep() { if (run) { var b = runs(); b[b.length - 1] = run; save(b); } }
  addEventListener("pagehide", function () { syncSaves(); if (run && !fatalTxt) { run.clean = true; keep(); } });
  d.addEventListener("visibilitychange", function () { if (d.hidden) syncSaves(); });
  addEventListener("error", function (e) { if (run && !run.err) { run.err = String(e.message || e).slice(0, 80); keep(); } });

  // ---- saved games: ScummVM writes them into the browser store (IndexedDB) by itself a moment after saving; do it at once
  // when the page goes to the background or the game ends (iOS may drop a page in the background) ----
  function syncSaves(done) {
    var FS = (window.FOTAQ || {}).FS, fin = function (e) { if (done) done(e); };
    if (!FS || !FS.syncfs) return fin("no FS");
    try { FS.syncfs(false, function (e) { fin(e); }); } catch (e) { fin(e); }
  }

  // ---- a short report for the administrator (MoveEye, Mehr → Spielecke): only the numbers of the line and the error text ----
  function report(why) {
    if (sent[why]) return; sent[why] = 1;
    try {
      var x = window.FOTAQ_DIAG(), b = JSON.stringify({why: why, v: x.v, lang: x.lang, dev: x.dev, step: x.step, sec: Math.round(x.sec), wasm: x.wasm,
        heap: x.heap, req: x.req, bytes: x.bytes, errors: x.errors, retries: x.retries, audio: x.audio, tag: x.tag, kind: x.kind, err: x.err.slice(0, 600)});
      var u = new URL("../../fotaqtest-diag/report", location.href).pathname;
      if (navigator.sendBeacon && navigator.sendBeacon(u, new Blob([b], {type: "text/plain"}))) return;
      fetch(u, {method: "POST", body: b, keepalive: true}).catch(function () {});
    } catch (e) {}
  }

  // ---- end of the game and errors: a panel that stays (never a black screen) ----
  function logTail() { return ((window.FOTAQ || {}).log || []).filter(function (t) { return !/^E: WARNING: (FSNode|SearchSet|initWithU32String)/.test(t); }).slice(-8).join("\n"); }
  function copyText() { return line(window.FOTAQ_DIAG()) + "\n" + (fatalTxt || "") + "\n--\n" + logTail(); }
  function copy(btn) {
    var t = copyText(), ok = function () { btn.textContent = de() ? "✓ kopiert" : "✓ copied"; };
    function old() {                                                   // http page: select the text field and copy
      var a = d.getElementById("fqMsg"); if (!a) return;
      a.focus(); a.select(); try { a.setSelectionRange(0, 99999); } catch (e) {}
      var done = false; try { done = d.execCommand("copy"); } catch (e) {}
      if (done) ok(); else btn.textContent = de() ? "Text ist markiert – «Kopieren» antippen" : "The text is selected – tap «Copy»";
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(ok, old); else old();
  }
  function panel(bad, title, text) {
    var st = d.getElementById("stage"), p = d.getElementById("fqEnd");
    if (!st) return;
    if (!p) { p = d.createElement("div"); p.id = "fqEnd"; st.appendChild(p); }
    p.className = bad ? "bad" : ""; p.textContent = "";
    var h = d.createElement("b"); h.textContent = title; p.appendChild(h);
    if (bad) {
      var a = d.createElement("textarea"); a.id = "fqMsg"; a.readOnly = true; a.value = copyText(); p.appendChild(a);
    } else { var s = d.createElement("div"); s.textContent = text; p.appendChild(s); }
    var row = d.createElement("div"); row.className = "row";
    function btn(id, tx, fn) { var b = d.createElement("button"); b.type = "button"; b.id = id; b.textContent = tx; b.addEventListener("click", fn); row.appendChild(b); return b; }
    if (bad) btn("fqCopy", de() ? "📋 Fehler kopieren" : "📋 Copy the error", function () { copy(this); });
    btn("fqAgain", de() ? "↻ Nochmal" : "↻ Again", function () { location.reload(); });
    btn("fqBack", de() ? "‹ Spiele" : "‹ Games", function () { var b = d.getElementById("backGame"); if (b) b.click(); });
    p.appendChild(row);
    var ld = d.getElementById("load"); if (ld) ld.classList.add("hidden");
  }
  function fatal(kind, text) {
    if (fatalTxt) return;
    fatalKind = kind; fatalTxt = String(text || "?").replace(/https?:\/\/[^\/\s]+/g, "…").slice(0, 600);
    if (run) { run.err = fatalTxt; run.kind = kind; run.clean = false; keep(); }
    syncSaves();
    var t = kind === "data" ? (de() ? "Spieldaten konnten nicht geladen werden (unvollständig oder Verbindung zu MoveEye weg)" : "The game data could not be loaded (incomplete, or the connection to MoveEye is gone)")
                            : (de() ? "Fehler – das Spiel wurde angehalten" : "Error – the game has stopped");
    panel(true, "⚠️ " + t, fatalTxt); report("error");
  }
  function lastError() {
    var a = ((window.FOTAQ || {}).log || []).filter(function (t) { return /^E: /.test(t) && !/^E: WARNING/.test(t); });
    return a.slice(-3).join(" | ").replace(/^E: /, "");
  }
  function gameEnded(code) {
    if (ended) return; ended = true;
    if (run && !fatalTxt) { run.clean = true; run.end = "game"; keep(); }
    syncSaves(function (e) {
      if (fatalTxt) return;
      if (code) { fatal("exit", (lastError() || "ScummVM") + " (Ende " + code + ")"); return; }
      panel(false, de() ? "Spiel beendet" : "Game ended", e ? (de() ? "Achtung: die Spielstände konnten nicht gesichert werden (" : "Careful: the saved games could not be stored (") + e + ")"
        : (de() ? "Die Spielstände sind in diesem Browser gesichert." : "The saved games are stored in this browser."));
      report("end");
    });
  }
  // called by the launcher (index.html) with the Module object, before ScummVM is loaded
  window.FOTAQ_MODULE = function (M) {
    M.quitAfterGame = true;                               // patch 0005: the end of the game ends ScummVM (no launcher)
    // (not «--gui-theme=builtin»: tried on 12.11.2026, ScummVM then fails to load any theme in this build without FreeType)
    M.onScummvmEnded = function (code) { gameEnded(code); };
    M.onHttpFsError = function (url, off, len, why) { fatal("data", String(url).replace(/^.*data\//, "data/") + " @" + off + ": " + why); };
    // patch 0005: error() of ScummVM comes here instead of a message box drawn by SDL (it waited for a tap, then black)
    M.onScummvmMessage = function (isError, text) { if (!isError) return 0; fatal("error", String(text).replace(/\s+$/, "")); return 1; };
    M.onAbort = function (what) { fatal("abort", (lastError() ? lastError() + " | " : "") + what); };
    M.quit = function (status, toThrow) {                 // exit() of ScummVM: after error() the status is not 0
      if (status && !ended) fatal("exit", (lastError() || "ScummVM") + " (Ende " + status + ")"); else if (!status) gameEnded(0);
      throw toThrow;
    };
    var home = M.onHomeMounted;
    M.onHomeMounted = function (h, FS) { window.FOTAQ.FS = FS; if (home) return home.apply(this, arguments); };
  };
  window.FOTAQ_TEST = {fatal: fatal, ended: gameEnded, sync: syncSaves};      // for the tests

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
          + (r.clean ? (de() ? "sauber beendet" : "ended properly") : r.kind ? (de() ? "FEHLER" : "ERROR") : (de() ? "NICHT sauber beendet (Absturz?)" : "did NOT end properly (crash?)")) + (r.err ? " · " + r.err : "");
        if (!r.clean) p.className = "bad";
        hist.appendChild(p);
      });
      if (!a.length) { var n = d.createElement("div"); n.textContent = de() ? "Noch kein Lauf. Eine Variante wählen, dann die Sprache antippen." : "No run yet. Pick a variant, then tap a language."; hist.appendChild(n); }
    }
  }
  addEventListener("DOMContentLoaded", function () {
    paint();
    var bar = d.getElementById("bar"), kf = d.getElementById("kFull");
    if (bar) { var kb = d.createElement("button"); kb.type = "button"; kb.id = "kDiag"; kb.title = "Diagnose"; kb.textContent = "ⓘ";
      kb.addEventListener("click", function () { showLine = !showLine; hideAt = 1; this.classList.toggle("on", showLine); tick(); }); bar.insertBefore(kb, kf); }
    showLine = false;
    fetch("fotaqtest.json", {cache: "no-store"}).then(function (r) { return r.json(); }).then(function (j) {
      MAN = j; if (!vinfo(V)) { V = ((j.varianten || [])[0] || {}).id || "a"; window.FOTAQ_VAR = V; } paint(); }).catch(function () {});
    d.querySelectorAll(".langs button").forEach(function (b) { b.addEventListener("click", function () { setTimeout(paint, 50); }); });
  });
})();
