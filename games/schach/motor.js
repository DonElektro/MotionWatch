/* Schach für MoveEye – Teil «Motor»: der Schach-Rechner im Hintergrund (Web Worker), die Seite bleibt bedienbar.
   Lizenz: GPL-3.0-or-later (siehe LIESMICH.txt).

   1. Stockfish 19 «lite single» als WebAssembly (lib/stockfish-19-lite-single.js + .wasm, ein Faden, kein SharedArrayBuffer).
   2. Ersatz ohne WebAssembly (motor-js-worker.js mit js-chess-engine): springt von selbst ein, wenn Stockfish nicht lädt
      oder nicht innert einiger Sekunden antwortet. Schwächer, aber gleiche Bedienung.
   Beide sprechen UCI über postMessage. Es läuft immer nur eine Suche; eine neue Suche bricht die laufende ab. */
(function (global) {
  "use strict";
  var START_FRIST = 9000;        // ms: so lange darf Stockfish zum Laden brauchen (1,8 MB vom Pi + Übersetzen am Handy)
  var ANTWORT_FRIST = 5000;      // ms über die Bedenkzeit hinaus, dann gilt der Motor als hängen geblieben

  var M = {
    art: null,                   // "wasm" | "js" | "kein"
    name: "Motor lädt …",
    bereit: false,
    onStatus: null,              // Rückruf, wenn sich Art / Name ändert
    statistik: { suchen: 0, maxMs: 0, wechsel: "" },
    _w: null, _lauf: null, _warte: [], _startP: null, _nurJs: false
  };

  function melde() { if (M.onStatus) try { M.onStatus(M); } catch (e) {} }

  function arbeiter(datei) {
    try { return new Worker(datei); } catch (e) { return null; }
  }

  /** einen Worker starten und auf «uciok» warten */
  function starte(datei, frist) {
    return new Promise(function (ok) {
      var w = arbeiter(datei), fertig = false, name = "";
      if (!w) return ok(null);
      var t = setTimeout(function () { ende(null); }, frist);
      function ende(x) {
        if (fertig) return; fertig = true; clearTimeout(t);
        if (!x) { try { w.terminate(); } catch (e) {} }
        ok(x);
      }
      w.onerror = function (e) { if (e && e.preventDefault) e.preventDefault(); if (!fertig) ende(null); else ausfall(w); };
      w.onmessage = function (ev) {
        var z = String(ev.data);
        if (!fertig) {
          if (z.indexOf("id name ") === 0) name = z.slice(8);
          if (z === "uciok") ende({ w: w, name: name });
          return;
        }
        zeile(w, z);
      };
      try { w.postMessage("uci"); } catch (e) { ende(null); }
    });
  }

  function nimm(x, art) {
    M._w = x.w; M.art = art; M.bereit = true;
    M.name = art === "wasm" ? "Stockfish 19 Lite (WebAssembly)" : "Ersatz-Motor js-chess-engine (ohne WebAssembly, schwächer)";
    melde();
  }

  function starteJs(grund) {
    M.statistik.wechsel = grund || "";
    return starte("motor-js-worker.js", 6000).then(function (x) {
      if (x) nimm(x, "js");
      else { M._w = null; M.art = "kein"; M.bereit = false; M.name = "Kein Motor verfügbar (der Computer zieht zufällig)"; melde(); }
      return M.art;
    });
  }

  /** Motor laden (einmal). opt.nurJs: gleich den Ersatz nehmen (Test, Einstellung) */
  M.start = function (opt) {
    if (M._startP) return M._startP;
    M._nurJs = !!(opt && opt.nurJs);
    var wasmDa = typeof WebAssembly === "object" && typeof Worker === "function";
    if (typeof Worker !== "function") { M.art = "kein"; M.name = "Kein Motor verfügbar (der Computer zieht zufällig)"; melde(); return (M._startP = Promise.resolve("kein")); }
    M._startP = (M._nurJs || !wasmDa ? Promise.resolve(null) : starte("lib/stockfish-19-lite-single.js", START_FRIST)).then(function (x) {
      if (x) { nimm(x, "wasm"); return "wasm"; }
      return starteJs(M._nurJs ? "gewählt" : "Stockfish lädt nicht");
    });
    return M._startP;
  };

  /** der laufende Motor antwortet nicht mehr: auf den Ersatz wechseln und die Suche dort wiederholen */
  function ausfall(w) {
    if (w !== M._w) return;
    var lauf = M._lauf;
    M._lauf = null; M.bereit = false;
    try { w.terminate(); } catch (e) {}
    if (lauf) clearTimeout(lauf.uhr);
    if (M.art === "js") {                                   // auch der Ersatz hängt: ohne Motor weiter
      M._w = null; M.art = "kein"; M.name = "Kein Motor verfügbar (der Computer zieht zufällig)"; melde();
      if (lauf) lauf.ok(null);
      return;
    }
    M._startP = starteJs("Stockfish antwortet nicht").then(function (art) {
      if (lauf) { if (art === "js" && !lauf.abbruch) los(lauf); else lauf.ok(null); }
      return art;
    });
  }

  function zeile(w, z) {
    var l = M._lauf, m;
    if (w !== M._w || !l) return;
    if (z.indexOf("info ") === 0 && (m = /score (cp|mate) (-?\d+)/.exec(z))) {
      var pv = / pv (.+)$/.exec(z);
      if (pv && (!/bound/.test(z) || !l.wert)) {
        l.wert = m[1] === "cp" ? { cp: +m[2] } : { matt: +m[2] };
        l.pv = pv[1].trim().split(/\s+/);
        var t = /depth (\d+)/.exec(z); l.tiefe = t ? +t[1] : 0;
      }
    } else if (z.indexOf("bestmove") === 0) {
      clearTimeout(l.uhr);
      M._lauf = null;
      var zug = z.split(/\s+/)[1], ms = Date.now() - l.t0;
      M.statistik.suchen++; M.statistik.maxMs = Math.max(M.statistik.maxMs, ms);
      l.ok(l.abbruch || !zug || zug === "(none)" ? (l.abbruch ? null : { zug: null, wert: l.wert || null, pv: [], ms: ms, tiefe: 0, motor: M.art })
        : { zug: zug, wert: l.wert || null, pv: l.pv && l.pv.length ? l.pv : [zug], ms: ms, tiefe: l.tiefe || 0, motor: M.art });
      weiter();
    }
  }

  function los(l) {
    var w = M._w, a = l.auftrag, s = function (t) { w.postMessage(t); };
    M._lauf = l; l.t0 = Date.now(); l.wert = null; l.pv = null;
    try {
      if (M.art === "wasm") {
        var begrenzt = typeof a.elo === "number";
        s("setoption name UCI_LimitStrength value " + (begrenzt ? "true" : "false"));
        if (begrenzt) s("setoption name UCI_Elo value " + a.elo);
        s("setoption name Skill Level value " + (typeof a.skill === "number" ? a.skill : 20));
        s("position fen " + (a.startFen || a.fen) + (a.zuege && a.zuege.length ? " moves " + a.zuege.join(" ") : ""));
        s("go movetime " + Math.max(20, a.zeit | 0) + (a.tiefe ? " depth " + a.tiefe : ""));
      } else {
        s("setoption name JsStufe value " + (a.jsStufe || 2));
        s("position fen " + a.fen);
        s("go");
      }
    } catch (e) { return ausfall(w); }
    l.uhr = setTimeout(function () { ausfall(w); }, (a.zeit | 0) + ANTWORT_FRIST + (M.art === "js" ? 6000 : 0));
  }

  function weiter() {
    if (M._lauf || !M._warte.length) return;
    var l = M._warte.shift();
    if (l.abbruch) { l.ok(null); return weiter(); }
    if (!M._w || !M.bereit) { l.ok(null); return weiter(); }
    los(l);
  }

  /** Suche. auftrag: {fen (Stellung jetzt), startFen + zuege (für Stockfish, damit er Wiederholungen sieht), zeit (ms),
      tiefe, elo, skill, jsStufe}. Ergebnis: {zug, wert: {cp} | {matt} aus Sicht der Seite am Zug, pv, ms} oder null
      (abgebrochen / kein Motor). Eine neue Suche bricht die laufende und alle wartenden ab. */
  M.suche = function (auftrag) {
    M.stopp();
    return new Promise(function (ok) {
      var l = { auftrag: auftrag, ok: ok, abbruch: false };
      (M._startP || M.start()).then(function () {
        if (l.abbruch || !M._w) return ok(null);
        M._warte.push(l); weiter();
      });
      M._neu = l;
    });
  };

  /** laufende Suche abbrechen (ihr Versprechen liefert null) */
  M.stopp = function () {
    if (M._neu) M._neu.abbruch = true;
    M._warte.forEach(function (l) { l.abbruch = true; });
    if (M._lauf && !M._lauf.abbruch) {
      M._lauf.abbruch = true;
      try { if (M.art === "wasm") M._w.postMessage("stop"); } catch (e) {}
    }
  };

  M.neuesSpiel = function () { M.stopp(); try { if (M._w && M.art === "wasm") M._w.postMessage("ucinewgame"); } catch (e) {} };

  global.Motor = M;
})(typeof globalThis !== "undefined" ? globalThis : this);
