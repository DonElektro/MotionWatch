/* Schach für MoveEye – Teil «Spiel»: Ablauf, Spieler, Bedienung, Lern-Modus, Ton, Speichern.
   Lizenz: GPL-3.0-or-later (siehe LIESMICH.txt). Brett: Chessground (lib/chessground.js), Regeln: partie.js, Rechner: motor.js.

   Aufbau (wichtig für später, z. B. zwei Handys über MoveEye):
     - Die Partie (partie.js) kennt nur Stellung und Züge. Sie ist als {startFen, zuege} speicher- und übertragbar.
     - Jede Seite hat einen «Spieler» mit derselben kleinen Schnittstelle:
         art            "mensch" | "motor" | "fern"
         amZug(spiel)   wird gerufen, wenn diese Seite dran ist; der Spieler liefert seinen Zug über spiel.ziehe(uci, art)
         gegnerZog(uci, zustand, quelle)   (freiwillig) erfährt jeden Zug der anderen Seite – der «Fern»-Spieler schickt ihn weiter
         abbrechen()    (freiwillig) laufendes Überlegen / Warten beenden
     - spiel.ziehe(uci, quelle) ist der EINE Weg für jeden Zug, egal woher er kommt. Die Bedienung (Brett, Knöpfe) ruft
       nur diese Funktion und zeichnet danach den Zustand.
   Zwei Handys («Zwei Handys», ab GS-1.15): der Netz-Teil liegt in fern.js (Verbindung zu MoveEye); hier nur der Ablauf
   (Abschnitt «Zwei Handys» unten): eigene Seite = MenschSpieler, Gegenseite = FernSpieler. Der Pi prüft jeden Zug und ist
   massgebend; weicht die eigene Partie ab (Zug zurück angenommen, Revanche, verlorener Zug), wird sie aus seiner Zugliste
   neu aufgebaut. Tipps und Lern-Modus rechnen nur auf diesem Handy; der Pi erfährt nur, DASS sie an sind (Hinweis für beide). */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var P = window.Partie, Motor = window.Motor, Fern = window.Fern;
  var URLP = new URLSearchParams(location.search), TEST = URLP.get("test") === "1";

  /* ---------- Stärke-Stufen ----------
     skill / tiefe / elo gelten für Stockfish (Skill Level, Suchtiefe, UCI_LimitStrength + UCI_Elo), js für den Ersatz-Motor.
     patzer = Anteil der Züge, bei denen der Computer absichtlich irgendeinen erlaubten Zug spielt (macht die unteren
     Stufen für Anfänger wirklich schlagbar: er stellt dann auch Figuren ein und übersieht Matt). */
  var STUFEN = [
    { name: "Anfänger",            skill: 0, tiefe: 1, patzer: 0.38, js: 1, text: "macht viele Fehler" },
    { name: "Einsteiger",          skill: 0, tiefe: 2, patzer: 0.20, js: 1, text: "übersieht noch einiges" },
    { name: "Gelegenheitsspieler", skill: 2, tiefe: 4, patzer: 0.07, js: 2, text: "spielt ab und zu" },
    { name: "Hobbyspieler",        elo: 1400, js: 2, text: "kennt die Tricks" },
    { name: "Vereinsspieler",      elo: 1750, js: 3, text: "spielt solide" },
    { name: "Turnierspieler",      elo: 2100, js: 3, text: "stark" },
    { name: "Meister",             elo: 2500, js: 4, text: "sehr stark" },
    { name: "Grossmeister",        js: 4, text: "volle Stärke" }
  ];
  var ROLLE = { p: "pawn", n: "knight", b: "bishop", r: "rook", q: "queen", k: "king" };
  var LERN_SCHWELLE = 200;       // ab so vielen Hundertstel-Bauern Verlust gegenüber dem besten Zug warnt der Lern-Modus
  var LERN_FRIST = 3000;         // ms: dauert die Prüfung länger, gilt der Zug einfach

  /* ---------- Einstellungen und Speichern (läuft auch ohne Speicher) ---------- */
  var K_EINST = "moveeye-schach-einst", K_PARTIE = "moveeye-schach-partie";
  var einst = { stufe: 3, farbe: "w", gegner: "motor", lern: true, ton: true, balken: true, zeit: 1000, autodrehen: false, fernLern: false, fernBalken: false };
  function lies(k) { try { var t = localStorage.getItem(k); return t ? JSON.parse(t) : null; } catch (e) { return null; } }
  function schreib(k, o) { try { localStorage.setItem(k, JSON.stringify(o)); return true; } catch (e) { return false; } }
  function weg(k) { try { localStorage.removeItem(k); } catch (e) {} }
  (function () {
    var e = lies(K_EINST);
    if (!e || typeof e !== "object") return;
    if (e.stufe >= 1 && e.stufe <= STUFEN.length) einst.stufe = e.stufe | 0;
    if (["w", "b", "zufall"].indexOf(e.farbe) >= 0) einst.farbe = e.farbe;
    if (e.gegner === "motor" || e.gegner === "mensch" || e.gegner === "fern") einst.gegner = e.gegner;
    ["lern", "ton", "balken", "autodrehen", "fernLern", "fernBalken"].forEach(function (k) { if (typeof e[k] === "boolean") einst[k] = e[k]; });
    if ([300, 500, 1000, 2000, 3000].indexOf(e.zeit) >= 0) einst.zeit = e.zeit;
  })();
  function einstSpeichern() { schreib(K_EINST, einst); }

  /* ---------- Zustand des Spiels ---------- */
  var spiel = {
    partie: new P(), spieler: { w: new MenschSpieler(), b: new MotorSpieler() }, gegner: "motor", mensch: "w", stufe: 3,
    drehung: "w", nr: 0, prueft: false, denkt: false, analyse: null, tippPfeil: null, tipps: 0, fern: null
  };
  /* Lern-Modus und Bewertungsbalken: bei «Zwei Handys» eigene Schalter (aus, bis man sie selbst einschaltet - Fairness) */
  function lernAn(modus) { return (modus || spiel.gegner) === "fern" ? einst.fernLern : einst.lern; }
  function balkenAn() { return spiel.gegner === "fern" ? einst.fernBalken : einst.balken; }
  var cg = null, tonZaehler = {}, letzteWarnung = null;

  /* ---------- Spieler ---------- */
  function MenschSpieler() { this.art = "mensch"; }
  MenschSpieler.prototype.amZug = function () { zeichne(); analysiere(); };

  function MotorSpieler() { this.art = "motor"; }
  MotorSpieler.prototype.amZug = function (s) {
    var nr = s.nr, t0 = Date.now();
    s.denkt = true; zeichne();
    motorZug(s.partie, s.stufe, einst.zeit).then(function (uci) {
      if (nr !== s.nr) return;                                   // inzwischen neues Spiel / Zug zurück
      var warte = Math.max(0, 450 - (Date.now() - t0));          // nicht schneller als das Auge
      setTimeout(function () {
        if (nr !== s.nr) return;
        s.denkt = false;
        if (!uci || !s.ziehe(uci, "motor")) { var l = s.partie.alleZuege(); if (l.length) s.ziehe(l[Math.floor(Math.random() * l.length)], "motor"); }
      }, TEST ? Math.min(warte, 120) : warte);
    });
  };
  MotorSpieler.prototype.abbrechen = function () { Motor.stopp(); };

  /** die Gegenseite auf dem anderen Handy: ihre Züge kommen von MoveEye (fernZustand), die eigenen gehen dorthin */
  function FernSpieler() { this.art = "fern"; }
  FernSpieler.prototype.amZug = function () { zeichne(); };
  FernSpieler.prototype.gegnerZog = function (uci, z, quelle) { if (quelle !== "fern" && spiel.fern) fernSende(uci, z.zugNr - 1); };

  /** Zug des Computers für eine Stufe: UCI, oder null wenn abgebrochen / kein Motor (der Aufrufer zieht dann zufällig) */
  function motorZug(partie, stufe, zeit) {
    var c = STUFEN[stufe - 1] || STUFEN[2], legal = partie.alleZuege();
    if (!legal.length) return Promise.resolve(null);
    if (c.patzer && Math.random() < c.patzer) return Promise.resolve(legal[Math.floor(Math.random() * legal.length)]);
    return Motor.suche({ fen: partie.fen(), startFen: partie.startFen, zuege: partie.zuege.slice(), zeit: zeit,
                         tiefe: c.tiefe, elo: c.elo, skill: c.skill, jsStufe: c.js }).then(function (r) {
      return r && r.zug && legal.indexOf(r.zug) >= 0 ? r.zug : null;
    });
  }

  function auftrag(partie, zeit) {                                // Suche mit voller Stärke (Tipp, Lern-Modus, Balken)
    return { fen: partie.fen(), startFen: partie.startFen, zuege: partie.zuege.slice(), zeit: zeit, jsStufe: 3 };
  }

  /* ---------- der eine Weg für Züge ---------- */
  spiel.ziehe = function (uci, quelle) {
    var vorher = spiel.partie.amZug(), z = spiel.partie.zug(uci);
    if (!z) return false;
    spiel.nr++; spiel.denkt = false; spiel.prueft = false; spiel.tippPfeil = null;
    if (spiel.analyse && spiel.analyse.zugNr !== z.zugNr) spiel.analyse = null;
    ton(z.ende ? (z.ende.art === "matt" ? "matt" : "remis") : z.schach ? "schach" : z.zug.geschlagen ? "schlag" : "zug");
    if (spiel.gegner === "mensch" && einst.autodrehen && !z.ende) {
      var nr = spiel.nr; zeichne(z);
      setTimeout(function () { if (nr === spiel.nr) { spiel.drehung = spiel.partie.amZug(); zeichne(); } }, 480);
    }
    partieSpeichern();
    var anderer = spiel.spieler[vorher === "w" ? "b" : "w"];
    if (anderer && anderer.gegnerZog) try { anderer.gegnerZog(uci, z, quelle); } catch (e) {}
    if (z.ende) { zeichne(z); endeZeigen(z); balkenEnde(z.ende); }
    else naechster();
    return true;
  };

  function naechster() {
    var sp = spiel.spieler[spiel.partie.amZug()];
    if (sp) sp.amZug(spiel);
  }

  function abbrechen() { ["w", "b"].forEach(function (c) { var s = spiel.spieler[c]; if (s && s.abbrechen) s.abbrechen(); }); Motor.stopp(); }

  /** neues Spiel. o: {gegner, farbe (w/b), stufe, fen, partie (geladen), drehung} */
  function starte(o) {
    abbrechen();
    spiel.nr++; spiel.denkt = false; spiel.prueft = false; spiel.analyse = null; spiel.tippPfeil = null; spiel.tipps = 0; letzteWarnung = null;
    if (Motor.name) infoZeile();
    spiel.gegner = o.gegner === "mensch" || o.gegner === "fern" ? o.gegner : "motor";
    if (spiel.gegner !== "fern") fernAus();
    spiel.mensch = o.farbe === "b" ? "b" : "w";
    spiel.stufe = o.stufe || einst.stufe;
    spiel.partie = o.partie || new P(o.fen);
    if (spiel.gegner === "fern") {
      spiel.spieler.w = !o.zuschauer && spiel.mensch === "w" ? new MenschSpieler() : new FernSpieler();
      spiel.spieler.b = !o.zuschauer && spiel.mensch === "b" ? new MenschSpieler() : new FernSpieler();
    } else {
      spiel.spieler.w = spiel.gegner === "motor" && spiel.mensch === "b" ? new MotorSpieler() : new MenschSpieler();
      spiel.spieler.b = spiel.gegner === "motor" && spiel.mensch === "w" ? new MotorSpieler() : new MenschSpieler();
    }
    spiel.drehung = o.drehung || (spiel.gegner === "mensch" ? "w" : spiel.mensch);
    if (!o.partie || !spiel.partie.zuege.length) Motor.neuesSpiel();
    alleZu();
    partieSpeichern();
    var z = spiel.partie.zustand();
    zeichne(z); balkenSetzen(50);
    if (z.ende) { endeZeigen(z); balkenEnde(z.ende); } else naechster();
  }

  function partieSpeichern() {
    var p = spiel.partie;
    if (spiel.gegner === "fern") return;                           // zwei Handys: die Partie liegt auf MoveEye (fern.js merkt Code + Sitz)
    if (!p.zuege.length && p.startFen === P.START) { weg(K_PARTIE); return; }
    schreib(K_PARTIE, { v: 1, partie: p.speichern(), gegner: spiel.gegner, mensch: spiel.mensch, stufe: spiel.stufe, drehung: spiel.drehung });
  }

  /* ---------- Brett ---------- */
  function farbe(c) { return c === "w" ? "white" : "black"; }
  function menschDran() { var s = spiel.spieler[spiel.partie.amZug()]; return !!s && s.art === "mensch"; }

  function zeichne(z) {
    z = z || spiel.partie.zustand();
    var frei = !z.ende && menschDran() && !spiel.prueft && fernFrei(), d = new Map();
    if (frei) Object.keys(z.ziele).forEach(function (k) { d.set(k, z.ziele[k]); });
    cg.set({
      fen: z.fen, orientation: farbe(spiel.drehung), turnColor: farbe(z.amZug), lastMove: z.letzter || [],
      check: z.schach, movable: { color: frei ? farbe(z.amZug) : undefined, dests: d }
    });
    cg.setAutoShapes(spiel.tippPfeil ? [{ orig: spiel.tippPfeil[0], dest: spiel.tippPfeil[1], brush: "green" }] : []);
    leisten(z); zugliste(z); statusZeile(z); knoepfe(z);
  }

  function figurBild(typ, c, neu) {
    return '<span class="cg-wrap' + (neu ? " neu" : "") + '"><piece class="' + ROLLE[typ] + " " + farbe(c) + '"></piece></span>';
  }

  function leisten(z) {
    var oben = spiel.drehung === "w" ? "b" : "w", unten = spiel.drehung;
    [[$("spOben"), oben], [$("spUnten"), unten]].forEach(function (x) {
      var el = x[0], c = x[1], gegn = c === "w" ? "b" : "w", name, sp = spiel.spieler[c];
      if (spiel.gegner === "mensch") name = c === "w" ? "Weiss" : "Schwarz";
      else if (spiel.gegner === "fern") name = fernName(c);
      else name = sp && sp.art === "motor" ? "Computer · " + STUFEN[spiel.stufe - 1].name : "Du (" + (c === "w" ? "Weiss" : "Schwarz") + ")";
      el.querySelector(".nm").textContent = name;
      var h = "", vor = "";
      z.material.fehlt[gegn].forEach(function (t) { h += figurBild(t, gegn, vor && vor !== t); vor = t; });
      el.querySelector(".gs").innerHTML = h;
      var plus = (c === "w" ? 1 : -1) * z.material.stand;
      el.querySelector(".pl").textContent = plus > 0 ? "+" + plus : "";
      el.querySelector(".dk").hidden = !(spiel.denkt && !z.ende && z.amZug === c && sp && sp.art === "motor");
      el.classList.toggle("dran", !z.ende && z.amZug === c);
    });
  }

  function zugliste(z) {
    var el = $("zuege"), h = "", start = z.startFen.split(" "), nr = +(start[5] || 1) || 1, schwarzBeginnt = start[1] === "b";
    if (!z.san.length) { el.innerHTML = '<span class="leer">Noch kein Zug – Weiss beginnt.</span>'; return; }
    for (var i = 0; i < z.san.length; i++) {
      var halb = i + (schwarzBeginnt ? 1 : 0), neu = i === z.san.length - 1 ? " neu" : "";
      if (halb % 2 === 0) h += '<span class="paar"><span class="nr">' + (nr + halb / 2) + '.</span><span class="z' + neu + '">' + z.san[i] + "</span>";
      else h += (i === 0 ? '<span class="paar"><span class="nr">' + (nr + (halb - 1) / 2) + ".…</span>" : " ") + '<span class="z' + neu + '">' + z.san[i] + "</span></span>";
    }
    if ((z.san.length + (schwarzBeginnt ? 1 : 0)) % 2 === 1) h += "</span>";
    el.innerHTML = h;
    var l = el.querySelector(".z.neu");
    if (document.body.classList.contains("quer")) el.scrollTop = el.scrollHeight; else el.scrollLeft = el.scrollWidth;
    return l;
  }

  function endeTexte(e) {
    var zweit = spiel.gegner === "mensch", gew = e.sieger === "w" ? "Weiss" : "Schwarz", ich = e.sieger === spiel.mensch;
    if (e.art === "einigung") return ["Remis – unentschieden", "Ihr habt euch auf Remis geeinigt."];
    if (spiel.gegner === "fern") {
      var sz = fernSitz();
      if (sz !== "w" && sz !== "b") zweit = true;
      else if (e.art === "matt") return e.sieger === sz ? ["Schachmatt – du hast gewonnen!", "Glückwunsch! Der König deines Gegners kann nicht mehr entkommen."]
        : ["Schachmatt – dein Gegner gewinnt", "Dein König kann dem Schach nicht mehr entkommen. Mit «Revanche» spielt ihr nochmals – mit getauschten Farben."];
      else if (e.art === "aufgabe") return e.sieger === sz ? ["Dein Gegner hat aufgegeben", "Du gewinnst die Partie."] : ["Aufgegeben", "Du hast aufgegeben – dein Gegner gewinnt."];
    }
    if (e.art === "matt") {
      if (zweit) return ["Schachmatt – " + gew + " gewinnt!", "Der König kann dem Schach nicht mehr entkommen."];
      return ich ? ["Schachmatt – du hast gewonnen!", "Glückwunsch! Der König des Computers kann nicht mehr entkommen."]
                 : ["Schachmatt – der Computer gewinnt", "Dein König steht im Schach und kann nicht mehr entkommen. Mit «Zug zurück» kannst du es nochmals versuchen."];
    }
    if (e.art === "aufgabe") {
      if (zweit) return ["Aufgegeben – " + gew + " gewinnt", (e.sieger === "w" ? "Schwarz" : "Weiss") + " hat aufgegeben."];
      return ["Aufgegeben", "Du hast aufgegeben – der Computer gewinnt. Kopf hoch, die nächste Partie wird besser."];
    }
    if (e.art === "patt") return ["Patt – unentschieden", "Wer am Zug ist, hat keinen erlaubten Zug mehr, steht aber nicht im Schach."];
    if (e.art === "wiederholung") return ["Remis – unentschieden", "Dieselbe Stellung ist zum dritten Mal entstanden."];
    if (e.art === "50zuege") return ["Remis – unentschieden", "50 Züge lang wurde nichts geschlagen und kein Bauer gezogen."];
    return ["Remis – unentschieden", "Es sind zu wenig Figuren übrig, um noch matt zu setzen."];
  }

  var statusFest = null;                 // Text, der bis zum nächsten Zug stehen bleibt (Tipp)
  function statusZeile(z) {
    var el = $("status"), t, kl = "";
    if (z.ende) { t = endeTexte(z.ende)[0]; kl = "ende"; }
    else if (spiel.prueft) t = "Ich schaue mir den Zug kurz an …";
    else if (statusFest && statusFest.nr === spiel.nr) { t = statusFest.text; kl = "tipp"; }
    else {
      var wer = z.amZug === "w" ? "Weiss" : "Schwarz";
      var fz = spiel.gegner === "fern" ? fernStatusText(z) : null;
      if (fz) t = fz;
      else if (spiel.gegner === "mensch") t = z.schach ? "Schach! " + wer + " muss den König retten." : wer + " ist am Zug.";
      else if (menschDran()) t = z.schach ? "Schach! Dein König ist bedroht." : "Du bist am Zug.";
      else t = z.schach ? "Schach! Der Computer überlegt …" : "Der Computer überlegt …";
      if (z.schach) kl = "schach";
    }
    el.textContent = t; el.className = kl;
  }

  function knoepfe(z) {
    var eigene = spiel.gegner === "mensch" ? z.zugNr : z.zuege.filter(function (_, i) {
      return ((z.startFen.split(" ")[1] === "b" ? i + 1 : i) % 2 === 0 ? "w" : "b") === spiel.mensch; }).length;
    var fs = spiel.gegner === "fern" ? fernSitz() : "", spielt = fs === "w" || fs === "b";
    var lauf = spielt && !z.ende && !!spiel.fern.v && spiel.fern.v.status === "laeuft", offen = spielt && !!spiel.fern.v && !!spiel.fern.v.anfrage;
    $("bZurueck").textContent = spielt ? "Zug zurück?" : "Zug zurück";
    $("bDrehen").textContent = spielt ? "Remis anbieten" : "Brett drehen";
    if (spiel.gegner === "fern") {
      $("bZurueck").disabled = !lauf || !eigene || offen;
      $("bDrehen").disabled = spielt && (!lauf || offen);
      $("bTipp").disabled = !lauf || !menschDran() || spiel.prueft;
      $("bAufgeben").disabled = !lauf;
    } else {
      $("bZurueck").disabled = !eigene || spiel.prueft; $("bDrehen").disabled = false;
      $("bTipp").disabled = !!z.ende || !menschDran() || spiel.prueft;
      $("bAufgeben").disabled = !!z.ende || !z.zugNr;
    }
    $("bLern").classList.toggle("an", lernAn()); $("bLern").setAttribute("aria-pressed", lernAn() ? "true" : "false");
    $("balken").hidden = !balkenAn();
  }

  function infoZeile() {
    var t = Motor.name;
    if (spiel.analyse && spiel.analyse.text && balkenAn()) t = spiel.analyse.text + " · " + t;
    $("info").textContent = t; $("ueberMotor").textContent = "Aktiver Motor: " + Motor.name;
  }

  /* ---------- Bewertung (Balken), Tipp ---------- */
  function cpVon(w) { return !w ? 0 : typeof w.matt === "number" ? (w.matt > 0 ? 3000 : -3000) : Math.max(-1500, Math.min(1500, w.cp)); }
  function balkenSetzen(prozentWeiss) { $("balken").firstElementChild.style.width = prozentWeiss.toFixed(1) + "%"; }
  function balkenEnde(e) { balkenSetzen(e.sieger === "w" ? 100 : e.sieger === "b" ? 0 : 50); spiel.analyse = null; infoZeile(); }
  function bewertungsText(w, amZug) {
    var s = amZug === "w" ? 1 : -1;
    if (typeof w.matt === "number") return (w.matt * s > 0 ? "Weiss" : "Schwarz") + " kann matt setzen";
    var cp = w.cp * s, b = (Math.abs(cp) / 100).toFixed(1).replace(".", ",");
    return Math.abs(cp) < 40 ? "ausgeglichen" : (cp > 0 ? "Weiss" : "Schwarz") + " steht besser (" + b + ")";
  }

  /** Stellung des Menschen am Zug kurz mit voller Stärke ansehen: Grundlage für Balken, Tipp und Lern-Modus */
  function analysiere() {
    var p = spiel.partie, nr = spiel.nr;
    if (!(balkenAn() || lernAn()) || !Motor.bereit || p.ende()) return Promise.resolve(null);
    if (spiel.analyse && spiel.analyse.zugNr === p.zuege.length) return Promise.resolve(spiel.analyse);
    return Motor.suche(auftrag(p, Math.min(350, einst.zeit))).then(function (r) {
      if (!r || !r.zug || nr !== spiel.nr) return null;
      spiel.analyse = { zugNr: p.zuege.length, zug: r.zug, wert: r.wert, pv: r.pv, text: r.wert ? bewertungsText(r.wert, p.amZug()) : "" };
      if (r.wert) { var w = cpVon(r.wert) * (p.amZug() === "w" ? 1 : -1); balkenSetzen(50 + 50 * (2 / (1 + Math.exp(-w / 280)) - 1)); }
      infoZeile();
      return spiel.analyse;
    });
  }

  function feldName(f) { return f; }
  function tipp() {
    var p = spiel.partie, nr = spiel.nr;
    if (p.ende() || !menschDran() || spiel.prueft) return Promise.resolve(null);
    if (!Motor.bereit) { statusFest = { nr: nr, text: "Der Computer ist noch nicht bereit – gleich nochmals versuchen." }; zeichne(); return Promise.resolve(null); }
    statusFest = { nr: nr, text: "Ich suche einen guten Zug …" }; zeichne();
    var fertig = spiel.analyse && spiel.analyse.zugNr === p.zuege.length ? Promise.resolve(spiel.analyse)
      : Motor.suche(auftrag(p, Math.min(700, Math.max(300, einst.zeit)))).then(function (r) {
          if (!r || !r.zug || nr !== spiel.nr) return null;
          spiel.analyse = { zugNr: p.zuege.length, zug: r.zug, wert: r.wert, pv: r.pv, text: r.wert ? bewertungsText(r.wert, p.amZug()) : "" };
          return spiel.analyse;
        });
    return fertig.then(function (a) {
      if (nr !== spiel.nr) return null;
      if (!a) { statusFest = { nr: nr, text: "Gerade kein Tipp möglich." }; zeichne(); return null; }
      var von = a.zug.slice(0, 2), nach = a.zug.slice(2, 4), f = p.figur(von), ziel = p.figur(nach);
      spiel.tippPfeil = [von, nach]; spiel.tipps++;
      statusFest = { nr: nr, text: "Tipp: " + (f ? P.NAME[f.type] : "Figur") + " von " + feldName(von) + " nach " + feldName(nach) + (ziel ? " (schlägt " + P.ARTIKEL_AKK[ziel.type] + ")" : "") + "." };
      ton("tipp"); zeichne(); infoZeile();
      if (spiel.gegner === "fern") fernHilfeMelden({ tipp: true });
      return a;
    });
  }

  /* ---------- Lern-Modus ----------
     Vergleicht den gewählten Zug mit dem besten Zug des Motors (zwei kurze Suchen mit voller Stärke). Rückgabe: null
     (Zug ist in Ordnung oder nicht prüfbar) oder {art, text}. Grund nur, wo er sicher ableitbar ist:
       matt     der Gegner kann danach matt setzen (Zahl der Züge vom Motor)
       figur    der beste Gegenzug schlägt eine Figur und die Bewertung fällt etwa um deren Wert
       patt     der Zug setzt patt, obwohl man klar besser steht
       sonst    neutral «kein guter Zug» */
  function lernPruefung(uci) {
    var p = spiel.partie, nr = spiel.nr;
    if (!lernAn() || !Motor.bereit) return Promise.resolve(null);
    var probe = P.laden(p.speichern());
    if (!probe || !probe.zug(uci)) return Promise.resolve(null);
    var basisP = spiel.analyse && spiel.analyse.zugNr === p.zuege.length ? Promise.resolve(spiel.analyse) : Motor.suche(auftrag(p, 250));
    var arbeit = basisP.then(function (basis) {
      if (!basis || !basis.wert || nr !== spiel.nr) return null;
      var vorher = cpVon(basis.wert), e = probe.ende();
      if (e) return e.art === "patt" && vorher >= 300 ? { art: "patt", text: "Damit ist die Partie patt – also nur unentschieden, obwohl du klar besser stehst." } : null;
      if (basis.zug === uci) return null;                                        // genau der beste Zug
      return Motor.suche(auftrag(probe, 300)).then(function (nach) {
        if (!nach || !nach.wert || nr !== spiel.nr) return null;
        var danach = -cpVon(nach.wert), verlust = vorher - danach;
        if (typeof nach.wert.matt === "number" && nach.wert.matt > 0 && !(typeof basis.wert.matt === "number" && basis.wert.matt < 0)) {
          var n = nach.wert.matt;
          return { art: "matt", verlust: verlust, text: n <= 1 ? "Danach kann dich dein Gegner mit dem nächsten Zug matt setzen."
            : "Danach kann dich dein Gegner in " + n + " Zügen matt setzen." };
        }
        if (verlust < LERN_SCHWELLE || danach >= 400) return null;
        var g = nach.pv && nach.pv[0], opfer = g ? probe.figur(g.slice(2, 4)) : null;
        if (opfer && opfer.type !== "p" && opfer.type !== "k" && opfer.color === p.amZug() && verlust >= 100 * (P.WERT[opfer.type] - 1.5))
          return { art: "figur", figur: opfer.type, verlust: verlust, text: "Damit verlierst du " + P.ARTIKEL_AKK[opfer.type] + "." };
        return { art: "neutral", verlust: verlust, text: "Das ist kein guter Zug – es gibt etwas Besseres." };
      });
    });
    var frist = new Promise(function (ok) { setTimeout(function () { ok("frist"); }, LERN_FRIST); });
    return Promise.race([arbeit, frist]).then(function (x) { if (x === "frist") { Motor.stopp(); return null; } return x; });
  }

  /* ---------- Eingabe am Brett ---------- */
  function eingabe(von, nach) {
    var p = spiel.partie, nr = spiel.nr, c = p.amZug();
    var promo = p.istUmwandlung(von, nach) ? frageUmwandlung(c) : Promise.resolve("");
    promo.then(function (u) {
      if (nr !== spiel.nr) return;
      if (u === null) { zeichne(); return; }                    // abgebrochen: Bauer zurück
      var uci = von + nach + u;
      if (!lernAn() || !Motor.bereit) { if (!spiel.ziehe(uci, "mensch")) zeichne(); return; }
      spiel.prueft = true; statusZeile(spiel.partie.zustand()); knoepfe(spiel.partie.zustand());
      lernPruefung(uci).then(function (w) {
        if (nr !== spiel.nr) return;
        spiel.prueft = false;
        if (!w) { if (!spiel.ziehe(uci, "mensch")) zeichne(); return; }
        letzteWarnung = w; ton("warn");
        frageWarnung(w).then(function (trotzdem) {
          if (nr !== spiel.nr) return;
          if (trotzdem) { if (!spiel.ziehe(uci, "mensch")) zeichne(); }
          else { zeichne(); analysiere(); }
        });
      });
    });
  }

  /* ---------- Fenster ---------- */
  var FENSTER = ["dNeu", "dWeiter", "dUmw", "dWarn", "dEnde", "dFrage", "dEinst", "dUeber", "dFernWarte", "dAnfrage"], wartend = {};
  function auf(id) { $(id).hidden = false; }
  function zu(id) { $(id).hidden = true; if (wartend[id]) { var f = wartend[id]; wartend[id] = null; f(null); } }
  function alleZu() { FENSTER.forEach(zu); }
  function frage(id, knopfWerte) {                                // Fenster zeigen, Promise mit dem Wert des gedrückten Knopfs
    return new Promise(function (ok) {
      if (wartend[id]) { var alt = wartend[id]; wartend[id] = null; alt(null); }
      wartend[id] = ok; auf(id);
      Object.keys(knopfWerte).forEach(function (kid) {
        $(kid).onclick = function () { wartend[id] = null; $(id).hidden = true; ok(knopfWerte[kid]); };
      });
    });
  }
  function frageUmwandlung(c) {
    var h = "", namen = { q: "Dame", r: "Turm", b: "Läufer", n: "Springer" };
    ["q", "r", "b", "n"].forEach(function (t) {
      h += '<button type="button" data-u="' + t + '"><span class="fig cg-wrap"><piece class="' + ROLLE[t] + " " + farbe(c) + '"></piece></span>' + namen[t] + "</button>";
    });
    $("umw").innerHTML = h;
    return new Promise(function (ok) {
      if (wartend.dUmw) { var alt = wartend.dUmw; wartend.dUmw = null; alt(null); }
      wartend.dUmw = ok; auf("dUmw");
      Array.prototype.forEach.call($("umw").children, function (b) {
        b.onclick = function () { wartend.dUmw = null; $("dUmw").hidden = true; ok(b.getAttribute("data-u")); };
      });
      $("bUmwAbbr").onclick = function () { wartend.dUmw = null; $("dUmw").hidden = true; ok(null); };
    });
  }
  function frageWarnung(w) {
    $("warnText").textContent = w.text + " Trotzdem ziehen?";
    return frage("dWarn", { bNochmal: false, bTrotzdem: true }).then(function (x) { return x === true; });
  }
  function endeZeigen(z) {
    var t = endeTexte(z.ende);
    $("endeTitel").textContent = t[0]; $("endeText").textContent = t[1];
    var fs = spiel.gegner === "fern" ? fernSitz() : "";
    $("bEndeNeu").textContent = fs === "w" || fs === "b" ? "Revanche" : "Neues Spiel";
    setTimeout(function () { if (spiel.partie.ende() && spiel.partie.zuege.length === z.zugNr) auf("dEnde"); }, TEST ? 50 : 650);
  }

  function schalter(el, an) { el.classList.toggle("an", !!an); el.setAttribute("aria-pressed", an ? "true" : "false"); }
  function seg(el, wert) { Array.prototype.forEach.call(el.children, function (b) { b.classList.toggle("an", b.getAttribute("data-w") === wert); }); }
  var neuWahl = { gegner: "motor", farbe: "w" };
  function neuDialog() {
    neuWahl.gegner = einst.gegner; neuWahl.farbe = einst.farbe;
    seg($("segFarbe"), neuWahl.farbe);
    $("fernFehler").hidden = true;
    gegnerWahl(neuWahl.gegner);
    $("selStufe").value = String(einst.stufe);
    $("bNeuAbbr").hidden = !spiel.gestartet;
    $("fernVerlassen").hidden = !fernLaeuft();
    alleZu(); auf("dNeu");
  }
  function einstDialog() {
    $("selStufe2").value = String(spiel.stufe); $("selZeit").value = String(einst.zeit);
    $("einstMotor").hidden = spiel.gegner !== "motor";
    schalter($("schLern"), lernAn()); schalter($("schTon"), einst.ton); schalter($("schBalken"), balkenAn()); schalter($("schDrehen"), einst.autodrehen);
    auf("dEinst");
  }
  function lernSetzen(an, modus) {
    modus = modus || spiel.gegner;
    if (modus === "fern") einst.fernLern = !!an; else einst.lern = !!an;
    einstSpeichern();
    schalter($("schLern"), lernAn()); schalter($("schLernNeu"), lernAn(modus));
    knoepfe(spiel.partie.zustand());
    if (lernAn() && menschDran()) analysiere();
    if (spiel.gegner === "fern" && modus === "fern") fernHilfeMelden();
  }
  function gegnerWahl(g) {                                     // «Neues Spiel»: Computer · Zu zweit (ein Gerät) · Zwei Handys
    neuWahl.gegner = g; seg($("segGegner"), g);
    $("nurMotor").hidden = g !== "motor"; $("nurFern").hidden = g !== "fern";
    $("nurFarbe").hidden = g === "mensch"; $("bSpielen").hidden = g === "fern";
    $("farbeTitel").textContent = g === "fern" ? "Deine Farbe (beim Erstellen)" : "Deine Farbe";
    schalter($("schLernNeu"), lernAn(g));
    if (g === "fern" && !Fern.basis()) fernFehlerZeigen(FERN_TEXT.kein_pi);
  }

  /* ---------- Knöpfe ---------- */
  function zugZurueck() {
    if (spiel.gegner === "fern") { fernAnfrage("zurueck"); return; }
    var p = spiel.partie;
    if (!p.zuege.length || spiel.prueft) return;
    abbrechen(); alleZu();
    spiel.nr++; spiel.denkt = false; spiel.analyse = null; spiel.tippPfeil = null; statusFest = null;
    if (p.aufgabe) p.aufgabe = null;                           // eine Aufgabe zurücknehmen kostet keinen Zug
    else p.zurueck(1);
    if (spiel.gegner === "motor") while (p.zuege.length && p.amZug() !== spiel.mensch) p.zurueck(1);
    if (spiel.gegner === "mensch" && einst.autodrehen) spiel.drehung = p.amZug();
    partieSpeichern(); ton("zug"); zeichne(); balkenSetzen(50);
    naechster();
  }
  function aufgeben() {
    var p = spiel.partie;
    if (p.ende()) return;
    var c = spiel.gegner === "mensch" ? p.amZug() : spiel.mensch;
    $("frageTitel").textContent = "Aufgeben?";
    $("frageText").textContent = spiel.gegner === "mensch" ? (c === "w" ? "Weiss" : "Schwarz") + " gibt die Partie auf?"
      : spiel.gegner === "fern" ? "Willst du diese Partie wirklich aufgeben? Dein Gegner gewinnt dann." : "Willst du diese Partie wirklich aufgeben?";
    frage("dFrage", { bFrageNein: false, bFrageJa: true }).then(function (ja) {
      if (!ja || p !== spiel.partie || p.ende()) return;
      if (spiel.gegner === "fern") { fernAktion("aufgeben"); return; }
      abbrechen(); spiel.nr++; spiel.denkt = false;
      var z = p.aufgeben(c); partieSpeichern(); ton("remis"); zeichne(z); endeZeigen(z); balkenEnde(z.ende);
    });
  }

  /* ---------- Zwei Handys (je eines; MoveEye vermittelt, fern.js) ----------
     spiel.fern = {s: {code, token, sitz}, v: letzter Stand vom Pi, verb: "ok"|"weg", ausstehend: eigener Zug unterwegs {uci, n}} */
  var FERN_TEXT = {
    kein_pi: "«Zwei Handys» geht nur, wenn Schach über MoveEye geöffnet wurde (Spielecke oder Spiele-Link).",
    netz: "Keine Verbindung zu MoveEye. Bist du im selben WLAN oder im Fernzugriff?",
    voll: "Auf MoveEye sind schon zu viele Spiele offen. Bitte ein altes beenden oder später nochmals versuchen.",
    zu_oft: "Zu viele Versuche – bitte eine Minute warten.",
    weg: "Kein Spiel mit diesem Code. Stimmt er?",
    zu: "Die Spielecke ist geschlossen – frag den Besitzer von MoveEye, ob er die Spiele freigibt.",
    token: "Dieses Handy gehört nicht mehr zu diesem Spiel.",
    nicht_dran: "Dein Gegner ist am Zug.", illegal: "Dieser Zug ist nicht erlaubt.", nicht_synchron: "Die Stellung hat sich inzwischen geändert.",
    ende: "Die Partie ist schon zu Ende.", warte: "Dein Gegner ist noch nicht da.", offen: "Dein Gegner hat dich gerade etwas gefragt – bitte zuerst antworten.",
    geht_nicht: "Das geht gerade nicht.", keine: "Die Frage ist nicht mehr offen.", laeuft: "Dein Gegner ist schon da – das Spiel läuft."
  };
  var FERN_FRAGE = {
    remis: ["Remis?", "Dein Gegner bietet Remis an. Wenn du annimmst, endet die Partie unentschieden."],
    zurueck: ["Zug zurücknehmen?", "Dein Gegner möchte seinen letzten Zug zurücknehmen."],
    revanche: ["Revanche?", "Dein Gegner möchte nochmals spielen – mit getauschten Farben."]
  };
  var FERN_MEINE = { remis: "Remis angeboten – warte auf Antwort", zurueck: "Zug zurück gefragt – warte auf Antwort", revanche: "Revanche gefragt – warte auf Antwort" };
  function fernText(x) { var f = x && x.j && x.j.fehler; return FERN_TEXT[f] || (x && x.st === 0 ? FERN_TEXT.netz : "Das ging nicht (" + (f || (x && x.st)) + ")."); }
  function FN(c) { return c === "w" ? "Weiss" : "Schwarz"; }
  function fernSitz() { return spiel.fern ? spiel.fern.s.sitz : ""; }
  function fernAnders() { var s = fernSitz(); return s === "w" ? "b" : s === "b" ? "w" : ""; }
  function fernLaeuft() { var f = spiel.fern; return !!f && (f.s.sitz === "w" || f.s.sitz === "b") && !!f.v && f.v.status === "laeuft" && !spiel.partie.ende(); }
  function fernFrei() { var f = spiel.fern; return !f || (!!f.v && f.v.status === "laeuft" && !f.ausstehend && !f.v.ende); }
  function fernName(c) {
    var f = spiel.fern, ich = fernSitz();
    if (ich !== "w" && ich !== "b") return FN(c);
    if (c === ich) return "Du (" + FN(c) + ")";
    var st = f && f.v && f.v.sitze[c], zusatz = !st || !st.da ? " · noch nicht da" : !st.online && !(f.v && f.v.ende) ? " · offline" : "";
    return "Gegner (" + FN(c) + ")" + zusatz;
  }
  function fernStatusText(z) {
    var f = spiel.fern, v = f && f.v, ich = fernSitz(), wer = FN(z.amZug);
    if (!v) return "Verbinde mit dem Spiel " + (f ? f.s.code : "") + " …";
    if (v.status === "warte") return ich === "w" || ich === "b" ? "Warte auf deinen Gegner – Code " + f.s.code : "Warte auf die Spieler …";
    if (ich !== "w" && ich !== "b") return (z.schach ? "Schach! " : "") + wer + " ist am Zug.";
    if (f.ausstehend) return f.verb === "weg" ? "Dein Zug wartet – er geht los, sobald die Verbindung wieder da ist." : "Dein Zug wird gesendet …";
    if (z.amZug === ich) return z.schach ? "Schach! Dein König ist bedroht." : "Du bist am Zug.";
    return z.schach ? "Schach! Dein Gegner muss den König retten." : "Dein Gegner ist am Zug.";
  }
  function fernFehlerZeigen(t) { var el = $("fernFehler"); el.textContent = t; el.hidden = !t; }

  function fernZeile() {
    var f = spiel.fern, el = $("fern"), hl = $("fernHilfe"), vorher = el.hidden + "|" + hl.hidden + "|" + el.offsetHeight + "|" + hl.offsetHeight;
    if (!f) { el.hidden = true; hl.hidden = true; }
    else {
      var v = f.v, ich = f.s.sitz, ander = fernAnders(), kl, t;
      $("fernIch").textContent = (ich === "w" || ich === "b" ? "Du bist " + FN(ich) : "Du schaust zu") + " · Code " + f.s.code;
      if (f.verb === "weg") { kl = "weg"; t = "Verbindung weg – versuche neu"; }
      else if (!v) { kl = "warte"; t = "verbinde …"; }
      else if (v.status === "warte") { kl = "warte"; t = "warte auf Gegner"; }
      else if (ander && !v.sitze[ander].online && !v.ende) { kl = "warte"; t = "Gegner offline"; }
      else { kl = "ok"; t = "verbunden"; }
      $("fernVerb").className = "verb " + kl; $("fernVerb").textContent = t;
      el.hidden = false;
      var teile = [], hilfe = [];
      if (v && v.anfrage && v.anfrage.von === ich) teile.push(FERN_MEINE[v.anfrage.art] || "");
      ["w", "b"].forEach(function (c) {
        var h = v && v.hilfe && v.hilfe[c], was = [];
        if (!h) return;
        if (h.lern) was.push("Lern-Modus");
        if (h.balken) was.push("Balken");
        if (h.tipps) was.push(h.tipps + (h.tipps === 1 ? " Tipp" : " Tipps"));
        if (was.length) hilfe.push((ich === "w" || ich === "b" ? (c === ich ? "du" : "Gegner") : FN(c)) + " (" + was.join(", ") + ")");
      });
      if (hilfe.length) teile.push("💡 Tipps sind an: " + hilfe.join(" · "));
      hl.textContent = teile.join(" · "); hl.hidden = !teile.length;
    }
    if (vorher !== el.hidden + "|" + hl.hidden + "|" + el.offsetHeight + "|" + hl.offsetHeight) ordnen();
  }
  function fernStatus(st) { if (spiel.fern) { spiel.fern.verb = st; fernZeile(); statusZeile(spiel.partie.zustand()); } }

  /** die Partie aus dem Stand des Pi neu aufbauen (Start, Wiederaufnahme, Revanche, Zug zurück, Abweichung) */
  function fernAufbauen(v) {
    var e = v.ende, p = P.laden({ startFen: v.startFen, zuege: v.zuege, aufgabe: e && e.art === "aufgabe" ? (e.sieger === "w" ? "b" : "w") : null, remis: !!(e && e.art === "einigung") });
    var f = spiel.fern;
    if (!p) { fernStatus("weg"); return; }
    f.ausstehend = null;
    var sz = v.sitz === "w" || v.sitz === "b" ? v.sitz : "zuschauer";
    if (sz !== f.s.sitz) { f.s.sitz = sz; Fern.sitzung.schreib(f.s); }
    var warte = !$("dFernWarte").hidden || !f.v0;
    f.v0 = true;
    starte({ partie: p, gegner: "fern", farbe: sz === "b" ? "b" : "w", zuschauer: sz === "zuschauer" });
    if (warte && v.status === "warte") fernWarteZeigen();
    fernNachher(v);
  }
  function fernNachher(v) { fernZeile(); fernFrage(v); zeichne(); }
  function istAnfang(a, b) { if (a.length > b.length) return false; for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false; return true; }

  /** neuer Stand vom Pi (Abfrage oder Antwort auf einen Zug / eine Aktion) */
  function fernZustand(v) {
    var f = spiel.fern;
    if (!f || !v || v.code !== f.s.code) return;
    var alt = f.v; f.v = v;
    var p = spiel.partie, L = p.zuege, S = v.zuege;
    var vs = v.sitz === "w" || v.sitz === "b" ? v.sitz : "zuschauer";
    if (!alt || alt.nr !== v.nr || v.startFen !== p.startFen || vs !== f.s.sitz) { if (alt && alt.nr !== v.nr) ton("tipp"); fernAufbauen(v); return; }
    if (istAnfang(L, S) && !(S.length > L.length && p.ende())) {
      for (var i = L.length; i < S.length; i++) if (!spiel.ziehe(S[i], "fern")) { fernAufbauen(v); return; }
      if (f.ausstehend && S.length > f.ausstehend.n) f.ausstehend = null;
    } else if (f.ausstehend && L.length === S.length + 1 && istAnfang(S, L) && L[L.length - 1] === f.ausstehend.uci && S.length === f.ausstehend.n) {
      if (!f.sendet) fernSende(f.ausstehend.uci, f.ausstehend.n);             // eigener Zug kam (noch) nicht an: nochmals
    } else { fernAufbauen(v); return; }
    var e = v.ende, pe = spiel.partie.ende();
    if (e && !pe) {                                                         // Aufgabe oder Remis-Einigung vom Pi
      if (e.art === "aufgabe") spiel.partie.aufgabe = e.sieger === "w" ? "b" : "w";
      else if (e.art === "einigung") spiel.partie.remis = true;
      else { fernAufbauen(v); return; }
      abbrechen(); spiel.nr++; spiel.denkt = false;
      var z = spiel.partie.zustand(); ton("remis"); zeichne(z); endeZeigen(z); balkenEnde(z.ende);
    } else if (!e && pe && (spiel.partie.aufgabe || spiel.partie.remis)) { fernAufbauen(v); return; }
    if (alt.status === "warte" && v.status === "laeuft") {                  // der Gegner ist da
      zu("dFernWarte"); ton("tipp");
      if (!statusFest || statusFest.nr !== spiel.nr) statusFest = { nr: spiel.nr, text: menschDran() ? "Dein Gegner ist da – du bist am Zug." : "Dein Gegner ist da – er beginnt." };
    }
    fernNachher(v);
  }

  /** Frage des Gegners (Remis, Zug zurück, Revanche) zeigen bzw. wegnehmen, wenn sie nicht mehr offen ist */
  var fernFrageOffen = "";
  function fernFrage(v) {
    var a = v && v.anfrage, ich = fernSitz(), key = a ? a.art + "|" + a.von + "|" + a.nr + "|" + v.nr : "";
    if (!a || a.von === ich || (ich !== "w" && ich !== "b")) { if (fernFrageOffen) { fernFrageOffen = ""; zu("dAnfrage"); } return; }
    if (key === fernFrageOffen && !$("dAnfrage").hidden) return;
    fernFrageOffen = key;
    var t = FERN_FRAGE[a.art] || ["Frage", ""];
    $("anfrageTitel").textContent = t[0];
    $("anfrageText").textContent = t[1] + (a.art === "revanche" ? " Du spielst dann " + FN(ich === "w" ? "b" : "w") + "." : "");
    zu("dEnde"); auf("dAnfrage"); ton("warn");
  }

  function fernSende(uci, n) {
    var f = spiel.fern;
    if (!f || (f.s.sitz !== "w" && f.s.sitz !== "b")) return;
    f.ausstehend = { uci: uci, n: n }; f.sendet = true;
    Fern.zug(f.s, uci, n).then(function (x) {
      if (f !== spiel.fern) return;
      f.sendet = false;
      if (x.st === 200 && x.j.ok) { f.ausstehend = null; fernStatus("ok"); fernZustand(x.j); return; }
      if (x.st === 0 || x.st === 429 || x.st >= 500 || x.st === 401) {        // keine Verbindung: der Zug bleibt und geht später
        fernStatus("weg"); statusZeile(spiel.partie.zustand());
        setTimeout(function () { if (f === spiel.fern && f.ausstehend && !f.sendet) fernSende(f.ausstehend.uci, f.ausstehend.n); }, 1500);
        return;
      }
      f.ausstehend = null;
      if (x.j && x.j.v) fernZustand(x.j.v);
      statusFest = { nr: spiel.nr, text: "Der Zug kam nicht an: " + fernText(x) + " Es gilt die Stellung auf MoveEye." }; zeichne();
    });
  }

  function fernAktion(art, mehr) {
    var f = spiel.fern;
    if (!f) return Promise.resolve(null);
    return Fern.aktion(f.s, art, mehr).then(function (x) {
      if (f !== spiel.fern) return x;
      if (x.st === 200 && x.j.ok && x.j.weg) { fernAus(); neuDialog(); return x; }
      if (x.st === 200 && x.j.ok) { fernStatus("ok"); fernZustand(x.j); return x; }
      if (x.j && x.j.v) fernZustand(x.j.v);
      if (art !== "hilfe") { statusFest = { nr: spiel.nr, text: fernText(x) }; zeichne(); }
      return x;
    });
  }
  function fernAnfrage(art) { return fernAktion(art); }
  function fernHilfeMelden(mehr) {
    var ich = fernSitz();
    if (ich !== "w" && ich !== "b") return;
    var d = { lern: einst.fernLern, balken: einst.fernBalken };
    if (mehr && mehr.tipp) d.tipp = true;
    fernAktion("hilfe", d);
  }

  /** eine Sitzung beginnen (nach Erstellen, Beitreten oder beim Öffnen der Seite) */
  function fernStart(s, v) {
    if (spiel.fern && spiel.fern.verbindung) spiel.fern.verbindung.stopp();
    spiel.fern = { s: s, v: null, verb: v ? "ok" : "weg", ausstehend: null, sendet: false };
    Fern.sitzung.schreib(s);
    einst.gegner = "fern"; einstSpeichern(); spiel.gestartet = true;
    var f = spiel.fern;
    f.verbindung = new Fern.Verbindung(s, { zustand: fernZustand, status: fernStatus, fehler: fernVerloren });
    if (v) fernZustand(v);
    else starte({ partie: new P(), gegner: "fern", farbe: s.sitz === "b" ? "b" : "w", zuschauer: s.sitz !== "w" && s.sitz !== "b" });
    f.verbindung.start();
    fernHilfeMelden(); fernZeile(); ordnen();
  }
  function fernAus() {
    var f = spiel.fern;
    if (!f) return;
    if (f.verbindung) f.verbindung.stopp();
    spiel.fern = null; Fern.sitzung.weg(); fernFrageOffen = "";
    fernZeile();
  }
  /** vor einem anderen Spiel: ein laufendes Spiel auf zwei Handys gilt als aufgegeben */
  function fernVerlassen() {
    var f = spiel.fern;
    if (!f) return;
    if (fernLaeuft()) Fern.aktion(f.s, "aufgeben");
    else if (f.v && f.v.status === "warte" && (f.s.sitz === "w" || f.s.sitz === "b")) Fern.aktion(f.s, "abbrechen");
    fernAus();
  }
  function fernVerloren(x) {                                        // das Spiel gibt es nicht mehr / der Schlüssel gilt nicht mehr
    var code = spiel.fern ? spiel.fern.s.code : "";
    fernAus();
    neuDialog(); gegnerWahl("fern");
    fernFehlerZeigen(x && x.j && x.j.fehler === "weg" ? "Das Spiel " + code + " gibt es auf MoveEye nicht mehr." : fernText(x));
  }
  function fernWiederaufnehmen(s) {
    $("status").textContent = "Verbinde mit dem Spiel " + s.code + " …";
    Fern.zustand(s).then(function (x) {
      if (x.st === 200 && x.j.ok) fernStart({ code: s.code, token: s.token || "", sitz: x.j.sitz }, x.j);
      else if (x.st === 404 || x.st === 403) { Fern.sitzung.weg(); spiel.fern = { s: s }; fernVerloren(x); }
      else fernStart(s, null);                                     // gerade keine Verbindung: weiter versuchen
    });
  }
  function fernErstellen() {
    if (!Fern.basis()) { fernFehlerZeigen(FERN_TEXT.kein_pi); return; }
    var farbe = neuWahl.farbe, b = $("bFernNeu");
    einst.farbe = farbe; einstSpeichern();
    b.disabled = true;
    fernVerlassen();
    Fern.neu(farbe).then(function (x) {
      b.disabled = false;
      if (!(x.st === 200 && x.j.ok)) { fernFehlerZeigen(fernText(x)); return; }
      fernStart({ code: x.j.code, token: x.j.token, sitz: x.j.sitz }, x.j);
      fernWarteZeigen();
    });
  }
  /** Code gross, QR-Code (nur Adresse der Seite + Code) und Link für das zweite Handy */
  function fernWarteZeigen() {
    var f = spiel.fern;
    if (!f || (f.s.sitz !== "w" && f.s.sitz !== "b")) return;
    $("fernCode").textContent = f.s.code;
    if ($("fernQr").getAttribute("data-code") !== f.s.code) { $("fernQr").src = Fern.qr(f.s.code); $("fernQr").setAttribute("data-code", f.s.code); }
    $("fernLink").textContent = Fern.link(f.s.code);
    $("fernWarteText").textContent = "Warte auf deinen Gegner … Du spielst " + FN(f.s.sitz) + ".";
    auf("dFernWarte");
  }
  function fernBeitreten(code) {
    code = String(code || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (!Fern.basis()) { fernFehlerZeigen(FERN_TEXT.kein_pi); return; }
    if (code.length !== 4) { fernFehlerZeigen("Der Code hat 4 Zeichen (Buchstaben und Ziffern)."); return; }
    var alt = Fern.sitzung.lies(), b = $("bFernBei");
    b.disabled = true;
    if (!(alt && alt.code === code)) fernVerlassen();
    Fern.beitreten(code, alt && alt.code === code ? alt.token : "").then(function (x) {
      b.disabled = false;
      if (!(x.st === 200 && x.j.ok)) { fernFehlerZeigen(fernText(x)); return; }
      fernStart({ code: code, token: x.j.token || "", sitz: x.j.sitz }, x.j);
      ton("tipp");
      if (x.j.sitz === "zuschauer") { statusFest = { nr: spiel.nr, text: "Beide Plätze sind besetzt – du schaust zu." }; zeichne(); }
    });
  }
  // das Wiederfinden nach dem Schlafen macht fern.js (Seite wieder sichtbar -> sofort neu fragen)

  /* ---------- Töne (WebAudio, erzeugt; erst nach der ersten Berührung) ---------- */
  var ac = null;
  function tonStart() {
    if (!einst.ton) return;
    try {
      if (!ac) { var A = window.AudioContext || window.webkitAudioContext; if (A) ac = new A(); }
      if (ac && ac.state === "suspended") ac.resume();
    } catch (e) { ac = null; }
  }
  function piep(f1, f2, dauer, typ, laut, wann) {
    var t = ac.currentTime + (wann || 0), o = ac.createOscillator(), g = ac.createGain();
    o.type = typ; o.frequency.setValueAtTime(f1, t); o.frequency.exponentialRampToValueAtTime(Math.max(30, f2), t + dauer);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(laut, t + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, t + dauer);
    o.connect(g); g.connect(ac.destination); o.start(t); o.stop(t + dauer + 0.03);
  }
  function ton(art) {
    tonZaehler[art] = (tonZaehler[art] || 0) + 1;
    if (!einst.ton || !ac || ac.state !== "running") return;
    try {
      if (art === "zug") { piep(300, 120, 0.07, "triangle", 0.35); piep(900, 400, 0.03, "square", 0.05); }
      else if (art === "schlag") { piep(240, 70, 0.11, "triangle", 0.45); piep(1400, 300, 0.05, "square", 0.08); piep(180, 60, 0.09, "triangle", 0.3, 0.07); }
      else if (art === "schach") { piep(300, 120, 0.07, "triangle", 0.3); piep(660, 660, 0.11, "sine", 0.22, 0.06); piep(880, 880, 0.16, "sine", 0.22, 0.18); }
      else if (art === "matt") { piep(523, 523, 0.16, "sine", 0.22); piep(659, 659, 0.16, "sine", 0.22, 0.15); piep(784, 784, 0.34, "sine", 0.24, 0.3); }
      else if (art === "remis") { piep(440, 440, 0.18, "sine", 0.2); piep(392, 392, 0.3, "sine", 0.2, 0.18); }
      else if (art === "warn") { piep(520, 520, 0.1, "sine", 0.2); piep(390, 390, 0.18, "sine", 0.2, 0.12); }
      else if (art === "tipp") { piep(700, 1050, 0.12, "sine", 0.16); }
    } catch (e) {}
  }

  /* ---------- Aufteilung der Seite ---------- */
  function ordnen() {
    var h = $("haupt"), W = h.clientWidth, H = h.clientHeight, quer = W >= 560 && W > H * 1.15, b;
    document.body.classList.toggle("quer", quer);
    document.body.classList.toggle("breit", !quer && W >= 700);
    var leisten = 48 + (balkenAn() ? 6 : 0), bedarf = 6;        // Platz für Status, Zugliste, Knöpfe, Info-Zeile (gemessen)
    if (!quer) Array.prototype.forEach.call($("rechts").children, function (k) { bedarf += k.offsetHeight; });
    if (quer) b = Math.min(H - leisten - 6, W - 16 - 12 - 290);
    else b = Math.min(W, H - leisten - bedarf);
    var dpr = window.devicePixelRatio || 1;
    b = Math.max(200, Math.floor(b * dpr / 8) * 8 / dpr);       // Chessground rundet das Brett auf ganze Geräte-Pixel je Feld: gleich so wählen
    document.documentElement.style.setProperty("--b", b + "px");
    if (cg) cg.redrawAll();
  }

  /* ---------- Start ---------- */
  function init() {
    var opt = "";
    STUFEN.forEach(function (s, i) { opt += '<option value="' + (i + 1) + '">' + (i + 1) + " · " + s.name + " – " + s.text + "</option>"; });
    $("selStufe").innerHTML = opt; $("selStufe2").innerHTML = opt;
    ordnen();
    cg = window.Chessground($("brett"), {
      fen: P.START, coordinates: true, blockTouchScroll: true, disableContextMenu: true,
      animation: { enabled: true, duration: 240 },
      highlight: { lastMove: true, check: true },
      movable: { free: false, color: undefined, showDests: true, events: { after: eingabe } },
      premovable: { enabled: false }, draggable: { enabled: true, showGhost: true }, selectable: { enabled: true },
      drawable: { enabled: false, visible: true }
    });
    addEventListener("resize", function () { ordnen(); setTimeout(ordnen, 300); });
    addEventListener("orientationchange", function () { setTimeout(ordnen, 350); });
    document.addEventListener("pointerdown", tonStart, true);
    document.addEventListener("keydown", tonStart, true);

    Motor.onStatus = function () { infoZeile(); if (Motor.bereit && menschDran() && !spiel.partie.ende()) analysiere(); };
    Motor.start({ nurJs: URLP.get("motor") === "js" });
    infoZeile();

    $("bTipp").onclick = function () { tipp(); };
    $("bZurueck").onclick = zugZurueck;
    $("bDrehen").onclick = function () {
      var fs = spiel.gegner === "fern" ? fernSitz() : "";
      if (fs === "w" || fs === "b") { fernAnfrage("remis"); return; }       // zwei Handys: hier sitzt «Remis anbieten»
      spiel.drehung = spiel.drehung === "w" ? "b" : "w"; partieSpeichern(); zeichne();
    };
    $("bNeu").onclick = neuDialog;
    $("bAufgeben").onclick = aufgeben;
    $("bEinst").onclick = einstDialog;
    $("bLern").onclick = function () { lernSetzen(!lernAn()); };
    $("bUeber").onclick = function () { infoZeile(); auf("dUeber"); };
    $("bUeberZu").onclick = function () { zu("dUeber"); };
    $("bEinstZu").onclick = function () { zu("dEinst"); };
    $("bEndeBrett").onclick = function () { zu("dEnde"); };
    $("bEndeNeu").onclick = function () {
      var fs = spiel.gegner === "fern" ? fernSitz() : "";
      if (fs === "w" || fs === "b") { zu("dEnde"); fernAnfrage("revanche"); } else neuDialog();
    };
    $("bNeuAbbr").onclick = function () { zu("dNeu"); };
    $("segGegner").onclick = function (e) { var b = e.target.closest("button"); if (!b) return; $("fernFehler").hidden = true; gegnerWahl(b.getAttribute("data-w")); };
    $("segFarbe").onclick = function (e) { var b = e.target.closest("button"); if (!b) return; neuWahl.farbe = b.getAttribute("data-w"); seg($("segFarbe"), neuWahl.farbe); };
    $("schLernNeu").onclick = function () { lernSetzen(!lernAn(neuWahl.gegner), neuWahl.gegner); };
    $("bSpielen").onclick = function () {
      einst.gegner = neuWahl.gegner; einst.farbe = neuWahl.farbe; einst.stufe = +$("selStufe").value || einst.stufe; einstSpeichern();
      spiel.gestartet = true;
      fernVerlassen();
      starte({ gegner: einst.gegner, stufe: einst.stufe, farbe: einst.farbe === "zufall" ? (Math.random() < 0.5 ? "w" : "b") : einst.farbe });
    };
    $("bFernNeu").onclick = fernErstellen;
    $("bFernBei").onclick = function () { fernBeitreten($("fernCodeEin").value); };
    $("fernCodeEin").oninput = function () { var v = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 4); if (v !== this.value) this.value = v; $("fernFehler").hidden = true; };
    $("fernCodeEin").onkeydown = function (e) { if (e.key === "Enter") { e.preventDefault(); fernBeitreten(this.value); } };
    $("bFernBrett").onclick = function () { zu("dFernWarte"); };
    $("fern").onclick = function () { if (spiel.fern && spiel.fern.v && spiel.fern.v.status === "warte") fernWarteZeigen(); };
    $("bFernAbbr").onclick = function () { fernAktion("abbrechen"); };
    $("bAnfrageJa").onclick = function () { zu("dAnfrage"); fernAktion("annehmen"); };
    $("bAnfrageNein").onclick = function () { zu("dAnfrage"); fernAktion("ablehnen"); };
    $("selStufe2").onchange = function () { spiel.stufe = einst.stufe = +this.value || einst.stufe; einstSpeichern(); partieSpeichern(); zeichne(); };
    $("selZeit").onchange = function () { einst.zeit = +this.value || 1000; einstSpeichern(); };
    $("schLern").onclick = function () { lernSetzen(!lernAn()); };
    $("schTon").onclick = function () { einst.ton = !einst.ton; einstSpeichern(); schalter(this, einst.ton); tonStart(); ton("zug"); };
    $("schBalken").onclick = function () {
      if (spiel.gegner === "fern") einst.fernBalken = !einst.fernBalken; else einst.balken = !einst.balken;
      einstSpeichern(); schalter(this, balkenAn()); ordnen(); zeichne(); infoZeile(); if (balkenAn() && menschDran()) analysiere();
      if (spiel.gegner === "fern") fernHilfeMelden();
    };
    $("schDrehen").onclick = function () { einst.autodrehen = !einst.autodrehen; einstSpeichern(); schalter(this, einst.autodrehen); };

    // zwei Handys: ein Spiel dieses Handys (Code + Sitz) läuft noch, oder der Link/QR-Code nennt einen Code (?fern=)
    var fCode = (URLP.get("fern") || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 4), fS = Fern.sitzung.lies();
    zeichne();
    if (Fern.basis() && fS && (!fCode || fCode === fS.code)) { fernWiederaufnehmen(fS); return; }
    if (fCode) { einst.gegner = "fern"; neuDialog(); $("fernCodeEin").value = fCode; return; }
    // angefangene Partie?
    var g = lies(K_PARTIE), alt = g && g.partie ? P.laden(g.partie) : null;
    if (alt && alt.zuege.length && !alt.ende()) {
      var gg = g.gegner === "mensch" ? "mensch" : "motor", st = g.stufe >= 1 && g.stufe <= STUFEN.length ? g.stufe | 0 : einst.stufe;
      $("weiterText").textContent = "Deine letzte Partie ist noch nicht fertig (" + alt.zuege.length + (alt.zuege.length === 1 ? " Zug" : " Züge") + ", "
        + (gg === "mensch" ? "zu zweit" : "gegen den Computer · " + STUFEN[st - 1].name) + ").";
      $("bWeiter").onclick = function () { spiel.gestartet = true; starte({ partie: alt, gegner: gg, farbe: g.mensch === "b" ? "b" : "w", stufe: st, drehung: g.drehung === "b" ? "b" : g.drehung === "w" ? "w" : null }); };
      $("bWeiterNeu").onclick = neuDialog;
      auf("dWeiter");
    } else neuDialog();
  }

  /* ---------- Prüf-Zugang (nur mit ?test=1): für werkzeuge/spiele_test.py ---------- */
  if (TEST) {
    window.__schach = {
      zustand: function () {
        var z = spiel.partie.zustand();
        var f = spiel.fern;
        return { fern: f ? { code: f.s.code, sitz: f.s.sitz, verb: f.verb, status: f.v && f.v.status, nr: f.v && f.v.nr, anfrage: f.v && f.v.anfrage, ausstehend: f.ausstehend,
                             hilfe: f.v && f.v.hilfe, gegnerOnline: !!(f.v && fernAnders() && f.v.sitze[fernAnders()].online), zeile: $("fern").innerText, hilfeZeile: $("fernHilfe").hidden ? "" : $("fernHilfe").textContent } : null,
                 fen: z.fen, amZug: z.amZug, schach: z.schach, ende: z.ende, zuege: z.zuege, san: z.san, zugNr: z.zugNr, gegner: spiel.gegner, mensch: spiel.mensch,
                 stufe: spiel.stufe, drehung: spiel.drehung, denkt: spiel.denkt, prueft: spiel.prueft, menschDran: menschDran(), tippPfeil: spiel.tippPfeil,
                 analyse: spiel.analyse, motor: Motor.art, motorName: Motor.name, bereit: Motor.bereit, statistik: Motor.statistik, toene: tonZaehler,
                 warnung: letzteWarnung, einst: einst, tonLaeuft: !!ac && ac.state, material: z.material };
      },
      /** Feldmitte in Seiten-Koordinaten */
      feld: function (f) {
        var r = $("brett").getBoundingClientRect(), x = f.charCodeAt(0) - 97, y = +f[1] - 1, w = spiel.drehung === "w";
        return { x: r.left + ((w ? x : 7 - x) + 0.5) * r.width / 8, y: r.top + ((w ? 7 - y : y) + 0.5) * r.height / 8 };
      },
      stelle: function (fen, o) { o = o || {}; spiel.gestartet = true; if (typeof o.lern === "boolean") { einst.lern = o.lern; } starte({ fen: fen, gegner: o.gegner || "motor", farbe: o.farbe || "w", stufe: o.stufe || 1 }); },
      ziehe: function (uci) { return spiel.ziehe(uci, "test"); },
      setze: function (k, v) { einst[k] = v; einstSpeichern(); ordnen(); zeichne(); },
      stufen: STUFEN.map(function (s) { return s.name; }),
      /** Motor gegen Motor über die Regeln (partie.js): jeder Zug muss erlaubt sein, kein Hängen */
      selbstspiel: function (o) {
        var p = new P(o.fen), max = o.max || 300, maxMs = 0, n = 0, zufall = 0;
        function schritt() {
          if (p.ende() || n >= max) return Promise.resolve({ ende: p.ende(), halbzuege: n, maxMs: maxMs, zufall: zufall, fen: p.fen(), motor: Motor.art });
          var t0 = Date.now(), st = p.amZug() === "w" ? o.w : o.s;
          return motorZug(p, st, o.zeit || 60).then(function (uci) {
            maxMs = Math.max(maxMs, Date.now() - t0);
            if (!uci) { var l = p.alleZuege(); uci = l[Math.floor(Math.random() * l.length)]; zufall++; if (!Motor.bereit) return { fehler: "Motor weg", halbzuege: n }; }
            if (!p.zug(uci)) return { fehler: "unerlaubter Zug " + uci + " in " + p.fen(), halbzuege: n };
            n++; return schritt();
          });
        }
        return schritt();
      },
      motorZug: function (stufe, zeit) { var t0 = Date.now(); return motorZug(spiel.partie, stufe, zeit || einst.zeit).then(function (u) { return { zug: u, ms: Date.now() - t0 }; }); },
      suche: function (fen, zeit) { return Motor.suche({ fen: fen, zeit: zeit || 300, jsStufe: 3 }); }
    };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
