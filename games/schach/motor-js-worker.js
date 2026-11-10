/* Schach für MoveEye – Ersatz-Motor in reinem JavaScript (ohne WebAssembly), läuft als Web Worker.
   Lizenz dieser Datei: GPL-3.0-or-later. Rechnet mit js-chess-engine 2.4.6 (MIT, Josef Jadrny) aus lib/js-chess-engine.js.
   Spricht einen kleinen Teil des UCI-Protokolls, damit motor.js beide Motoren gleich bedienen kann:
     uci · isready · ucinewgame · setoption name JsStufe value 1..4 · position fen <FEN> · go … · stop · quit
   Antwort auf «go»: eine Zeile «info depth D score cp N pv <zug>» (oder «score mate N») und «bestmove <zug>».
   Der Motor rechnet am Stück (kein Abbruch möglich), darum nur Stufen, die auch am Handy rasch fertig sind. */
"use strict";
importScripts("lib/js-chess-engine.js");
var J = self.JsChessEngine, fen = "", stufe = 2;

function feld(fenText, f) {                           // Figur auf einem Feld der FEN («e7» -> «P»)
  var reihen = fenText.split(" ")[0].split("/"), r = reihen[8 - (+f[1])], x = 0, soll = f.charCodeAt(0) - 97;
  for (var i = 0; i < r.length; i++) {
    if (/\d/.test(r[i])) x += +r[i]; else { if (x === soll) return r[i]; x++; }
  }
  return "";
}
function uci(zug, fenText) {                          // {"E7": "E8"} -> «e7e8q»
  var von = Object.keys(zug)[0], a = von.toLowerCase(), b = String(zug[von]).toLowerCase(), fig = feld(fenText, a);
  return a + b + ((fig === "P" && b[1] === "8") || (fig === "p" && b[1] === "1") ? "q" : "");
}
function rechne() {
  try {
    var r = J.ai(fen, { level: stufe, play: false, analysis: true });
    var s = typeof r.bestScore === "number" ? r.bestScore : 0, z = uci(r.move, fen), wert;
    if (Math.abs(s) > 900000) wert = "mate " + (s > 0 ? 1 : -1) * Math.max(1, Math.ceil((1000000 - Math.abs(s)) / 2));
    else wert = "cp " + Math.round(s);
    postMessage("info depth " + (r.depth || 1) + " score " + wert + " pv " + z);
    postMessage("bestmove " + z);
  } catch (e) {
    postMessage("bestmove (none)");
  }
}
onmessage = function (ev) {
  var t = String(ev.data || "").trim(), m;
  if (t === "uci") { postMessage("id name js-chess-engine 2.4.6"); postMessage("uciok"); }
  else if (t === "isready") postMessage("readyok");
  else if ((m = /^setoption name JsStufe value (\d+)/.exec(t))) stufe = Math.max(1, Math.min(4, +m[1]));
  else if ((m = /^position fen (.+?)(?: moves .*)?$/.exec(t))) fen = m[1];
  else if (t.indexOf("go") === 0) rechne();
  else if (t === "quit") close();
};
