/* Schach für MoveEye – Teil «Partie»: die Spiellogik ohne Bildschirm und ohne Eingabequelle.
   Lizenz: GPL-3.0-or-later (siehe LIESMICH.txt). Regeln: chess.js (BSD-2-Clause) in lib/chess.js.

   Eine Partie ist vollständig beschrieben durch Startstellung (FEN) + Zugliste (UCI, z. B. «e2e4», «e7e8q»).
   Alle Züge – vom Menschen an diesem Gerät, vom Computer und von einem zweiten Handy («fern», fern.js) – gehen durch
   genau eine Funktion: partie.zug(uciOderSan) -> neuer Zustand (oder null, wenn der Zug nicht erlaubt ist).
   Diese Datei kennt weder das Brett noch den Motor noch ein Netz; sie läuft auch in Node (Tests). */
(function (global) {
  "use strict";
  var ChessKlasse = global.Chess;
  var START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
  var WERT = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
  var DE = { K: "K", Q: "D", R: "T", B: "L", N: "S" };              // deutsche Figurenbuchstaben
  var NAME = { p: "Bauer", n: "Springer", b: "Läufer", r: "Turm", q: "Dame", k: "König" };
  var ARTIKEL_AKK = { p: "den Bauern", n: "den Springer", b: "den Läufer", r: "den Turm", q: "die Dame", k: "den König" };

  /** englische Kurznotation von chess.js -> deutsche (K D T L S, 0-0, Umwandlung «e8D») */
  function sanDeutsch(san) {
    if (san.indexOf("O-O-O") === 0) return "0-0-0" + san.slice(5);
    if (san.indexOf("O-O") === 0) return "0-0" + san.slice(3);
    return san.replace(/=([QRBN])/, function (_, f) { return DE[f]; }).replace(/^[KQRBN]/, function (f) { return DE[f]; });
  }

  function Partie(startFen) {
    this.startFen = startFen || START;
    this.zuege = [];                 // UCI
    this.aufgabe = null;             // "w" / "b": diese Seite hat aufgegeben
    this.remis = false;              // zwei Handys: beide haben sich auf Remis geeinigt
    this._c = new ChessKlasse(this.startFen);
    this._san = [];
  }

  /** aus dem gespeicherten bzw. übertragenen Objekt {startFen, zuege, aufgabe}; ungültige Daten -> null */
  Partie.laden = function (o) {
    try {
      var p = new Partie(o && o.startFen);
      var z = (o && o.zuege) || [];
      for (var i = 0; i < z.length; i++) if (!p.zug(z[i])) return null;
      if (o.aufgabe === "w" || o.aufgabe === "b") p.aufgabe = o.aufgabe;
      if (o.remis === true) p.remis = true;
      return p;
    } catch (e) { return null; }
  };

  Partie.prototype.speichern = function () {
    return { v: 1, startFen: this.startFen, zuege: this.zuege.slice(), aufgabe: this.aufgabe, remis: this.remis || undefined };
  };

  Partie.prototype.fen = function () { return this._c.fen(); };
  Partie.prototype.amZug = function () { return this._c.turn(); };          // "w" / "b"
  Partie.prototype.figur = function (feld) { return this._c.get(feld) || null; };

  /** erlaubte Züge als {von: [nach, …]} */
  Partie.prototype.ziele = function () {
    var out = {}, m = this.ende() ? [] : this._c.moves({ verbose: true });
    for (var i = 0; i < m.length; i++) {
      (out[m[i].from] = out[m[i].from] || []);
      if (out[m[i].from].indexOf(m[i].to) < 0) out[m[i].from].push(m[i].to);
    }
    return out;
  };

  Partie.prototype.alleZuege = function () {                                 // UCI aller erlaubten Züge
    return this._c.moves({ verbose: true }).map(function (m) { return m.from + m.to + (m.promotion || ""); });
  };

  Partie.prototype.istUmwandlung = function (von, nach) {
    var f = this._c.get(von);
    return !!f && f.type === "p" && (nach[1] === "8" || nach[1] === "1") &&
      this._c.moves({ verbose: true, square: von }).some(function (m) { return m.to === nach && m.promotion; });
  };

  /** DER eine Weg für jeden Zug. zug: UCI («e2e4», «e7e8q») oder Kurznotation («Nf3»). Rückgabe: Zustand oder null. */
  Partie.prototype.zug = function (zug) {
    if (this.ende()) return null;
    var m = null;
    try {
      if (/^[a-h][1-8][a-h][1-8][qrbn]?$/.test(zug)) m = this._c.move({ from: zug.slice(0, 2), to: zug.slice(2, 4), promotion: zug[4] });
      else m = this._c.move(zug);
    } catch (e) { m = null; }
    if (!m) return null;
    this.zuege.push(m.from + m.to + (m.promotion || ""));
    this._san.push(sanDeutsch(m.san));
    var z = this.zustand();
    z.zug = { von: m.from, nach: m.to, figur: m.piece, geschlagen: m.captured || null, umwandlung: m.promotion || null,
              rochade: /^O-O/.test(m.san), san: sanDeutsch(m.san) };
    return z;
  };

  /** n Halbzüge zurücknehmen (hebt auch eine Aufgabe auf) */
  Partie.prototype.zurueck = function (n) {
    this.aufgabe = null; this.remis = false;
    for (var i = 0; i < (n || 1) && this.zuege.length; i++) { this._c.undo(); this.zuege.pop(); this._san.pop(); }
    return this.zustand();
  };

  Partie.prototype.aufgeben = function (farbe) { if (!this.ende()) this.aufgabe = farbe; return this.zustand(); };
  Partie.prototype.remisVereinbart = function () { if (!this.ende()) this.remis = true; return this.zustand(); };

  /** null oder {art: matt|patt|wiederholung|50zuege|material|aufgabe|einigung, sieger: "w"|"b"|null} */
  Partie.prototype.ende = function () {
    var c = this._c;
    if (this.aufgabe) return { art: "aufgabe", sieger: this.aufgabe === "w" ? "b" : "w" };
    if (this.remis) return { art: "einigung", sieger: null };
    if (c.isCheckmate()) return { art: "matt", sieger: c.turn() === "w" ? "b" : "w" };
    if (c.isStalemate()) return { art: "patt", sieger: null };
    if (c.isInsufficientMaterial()) return { art: "material", sieger: null };
    if (c.isThreefoldRepetition()) return { art: "wiederholung", sieger: null };
    if (c.isDrawByFiftyMoves()) return { art: "50zuege", sieger: null };
    return null;
  };

  /** geschlagene Figuren (was jeder Seite gegenüber der Grundaufstellung fehlt) und Materialstand aus Sicht von Weiss */
  Partie.prototype.material = function () {
    var soll = { p: 8, n: 2, b: 2, r: 2, q: 1 }, hat = { w: { p: 0, n: 0, b: 0, r: 0, q: 0, k: 0 }, b: { p: 0, n: 0, b: 0, r: 0, q: 0, k: 0 } };
    var b = this._c.board(), sum = 0;
    for (var r = 0; r < 8; r++) for (var f = 0; f < 8; f++) if (b[r][f]) {
      hat[b[r][f].color][b[r][f].type]++; sum += (b[r][f].color === "w" ? 1 : -1) * WERT[b[r][f].type];
    }
    var fehlt = { w: [], b: [] };                    // fehlt.w = weisse Figuren, die Schwarz geschlagen hat
    ["w", "b"].forEach(function (c) {
      ["q", "r", "b", "n", "p"].forEach(function (t) { for (var i = hat[c][t]; i < soll[t]; i++) fehlt[c].push(t); });
    });
    return { fehlt: fehlt, stand: sum };
  };

  Partie.prototype.zustand = function () {
    var c = this._c, n = this.zuege.length, l = n ? this.zuege[n - 1] : null;
    return { fen: c.fen(), amZug: c.turn(), schach: c.isCheck(), ende: this.ende(), ziele: this.ziele(),
             letzter: l ? [l.slice(0, 2), l.slice(2, 4)] : null, zuege: this.zuege.slice(), san: this._san.slice(),
             startFen: this.startFen, material: this.material(), zugNr: n };
  };

  Partie.START = START; Partie.WERT = WERT; Partie.NAME = NAME; Partie.ARTIKEL_AKK = ARTIKEL_AKK; Partie.sanDeutsch = sanDeutsch;
  global.Partie = Partie;
  if (typeof module !== "undefined" && module.exports) module.exports = Partie;
})(typeof globalThis !== "undefined" ? globalThis : this);
