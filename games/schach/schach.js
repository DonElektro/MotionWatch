/* Schach für MoveEye – Teil «Spiel»: Ablauf, Spieler, Bedienung, Lern-Modus, Ton, Speichern.
   Lizenz: GPL-3.0-or-later (siehe LIESMICH.txt). Brett: Chessground (lib/chessground.js), Regeln: partie.js, Rechner: motor.js.

   Aufbau (wichtig für später, z. B. zwei Handys über MoveEye):
     - Die Partie (partie.js) kennt nur Stellung und Züge. Sie ist als {startFen, zuege} speicher- und übertragbar.
     - Jede Seite hat einen «Spieler» mit derselben kleinen Schnittstelle:
         art            "mensch" | "motor" | (später) "fern"
         amZug(spiel)   wird gerufen, wenn diese Seite dran ist; der Spieler liefert seinen Zug über spiel.ziehe(uci, art)
         gegnerZog(uci, zustand)   (freiwillig) erfährt jeden Zug der anderen Seite – ein «Fern»-Spieler schickt ihn weiter
         abbrechen()    (freiwillig) laufendes Überlegen / Warten beenden
     - spiel.ziehe(uci, quelle) ist der EINE Weg für jeden Zug, egal woher er kommt. Die Bedienung (Brett, Knöpfe) ruft
       nur diese Funktion und zeichnet danach den Zustand.
   Hier gibt es bewusst keinen Netz-Code. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var P = window.Partie, Motor = window.Motor;
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
  var einst = { stufe: 3, farbe: "w", gegner: "motor", lern: true, ton: true, balken: true, zeit: 1000, autodrehen: false };
  function lies(k) { try { var t = localStorage.getItem(k); return t ? JSON.parse(t) : null; } catch (e) { return null; } }
  function schreib(k, o) { try { localStorage.setItem(k, JSON.stringify(o)); return true; } catch (e) { return false; } }
  function weg(k) { try { localStorage.removeItem(k); } catch (e) {} }
  (function () {
    var e = lies(K_EINST);
    if (!e || typeof e !== "object") return;
    if (e.stufe >= 1 && e.stufe <= STUFEN.length) einst.stufe = e.stufe | 0;
    if (["w", "b", "zufall"].indexOf(e.farbe) >= 0) einst.farbe = e.farbe;
    if (e.gegner === "motor" || e.gegner === "mensch") einst.gegner = e.gegner;
    ["lern", "ton", "balken", "autodrehen"].forEach(function (k) { if (typeof e[k] === "boolean") einst[k] = e[k]; });
    if ([300, 500, 1000, 2000, 3000].indexOf(e.zeit) >= 0) einst.zeit = e.zeit;
  })();
  function einstSpeichern() { schreib(K_EINST, einst); }

  /* ---------- Zustand des Spiels ---------- */
  var spiel = {
    partie: new P(), spieler: { w: new MenschSpieler(), b: new MotorSpieler() }, gegner: "motor", mensch: "w", stufe: 3,
    drehung: "w", nr: 0, prueft: false, denkt: false, analyse: null, tippPfeil: null, tipps: 0
  };
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
    if (anderer && anderer.gegnerZog) try { anderer.gegnerZog(uci, z); } catch (e) {}
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
    spiel.gegner = o.gegner === "mensch" ? "mensch" : "motor";
    spiel.mensch = o.farbe === "b" ? "b" : "w";
    spiel.stufe = o.stufe || einst.stufe;
    spiel.partie = o.partie || new P(o.fen);
    spiel.spieler.w = spiel.gegner === "motor" && spiel.mensch === "b" ? new MotorSpieler() : new MenschSpieler();
    spiel.spieler.b = spiel.gegner === "motor" && spiel.mensch === "w" ? new MotorSpieler() : new MenschSpieler();
    spiel.drehung = o.drehung || (spiel.gegner === "motor" ? spiel.mensch : "w");
    if (!o.partie) Motor.neuesSpiel();
    alleZu();
    partieSpeichern();
    var z = spiel.partie.zustand();
    zeichne(z); balkenSetzen(50);
    if (z.ende) { endeZeigen(z); balkenEnde(z.ende); } else naechster();
  }

  function partieSpeichern() {
    var p = spiel.partie;
    if (!p.zuege.length && p.startFen === P.START) { weg(K_PARTIE); return; }
    schreib(K_PARTIE, { v: 1, partie: p.speichern(), gegner: spiel.gegner, mensch: spiel.mensch, stufe: spiel.stufe, drehung: spiel.drehung });
  }

  /* ---------- Brett ---------- */
  function farbe(c) { return c === "w" ? "white" : "black"; }
  function menschDran() { var s = spiel.spieler[spiel.partie.amZug()]; return !!s && s.art === "mensch"; }

  function zeichne(z) {
    z = z || spiel.partie.zustand();
    var frei = !z.ende && menschDran() && !spiel.prueft, d = new Map();
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
      if (spiel.gegner === "mensch") t = z.schach ? "Schach! " + wer + " muss den König retten." : wer + " ist am Zug.";
      else if (menschDran()) t = z.schach ? "Schach! Dein König ist bedroht." : "Du bist am Zug.";
      else t = z.schach ? "Schach! Der Computer überlegt …" : "Der Computer überlegt …";
      if (z.schach) kl = "schach";
    }
    el.textContent = t; el.className = kl;
  }

  function knoepfe(z) {
    var eigene = spiel.gegner === "mensch" ? z.zugNr : z.zuege.filter(function (_, i) {
      return ((z.startFen.split(" ")[1] === "b" ? i + 1 : i) % 2 === 0 ? "w" : "b") === spiel.mensch; }).length;
    $("bZurueck").disabled = !eigene || spiel.prueft;
    $("bTipp").disabled = !!z.ende || !menschDran() || spiel.prueft;
    $("bAufgeben").disabled = !!z.ende || !z.zugNr;
    $("bLern").classList.toggle("an", einst.lern); $("bLern").setAttribute("aria-pressed", einst.lern ? "true" : "false");
    $("balken").hidden = !einst.balken;
  }

  function infoZeile() {
    var t = Motor.name;
    if (spiel.analyse && spiel.analyse.text && einst.balken) t = spiel.analyse.text + " · " + t;
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
    if (!(einst.balken || einst.lern) || !Motor.bereit || p.ende()) return Promise.resolve(null);
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
    if (!einst.lern || !Motor.bereit) return Promise.resolve(null);
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
      if (!einst.lern || !Motor.bereit) { if (!spiel.ziehe(uci, "mensch")) zeichne(); return; }
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
  var FENSTER = ["dNeu", "dWeiter", "dUmw", "dWarn", "dEnde", "dFrage", "dEinst", "dUeber"], wartend = {};
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
    setTimeout(function () { if (spiel.partie.ende() && spiel.partie.zuege.length === z.zugNr) auf("dEnde"); }, TEST ? 50 : 650);
  }

  function schalter(el, an) { el.classList.toggle("an", !!an); el.setAttribute("aria-pressed", an ? "true" : "false"); }
  function seg(el, wert) { Array.prototype.forEach.call(el.children, function (b) { b.classList.toggle("an", b.getAttribute("data-w") === wert); }); }
  var neuWahl = { gegner: "motor", farbe: "w" };
  function neuDialog() {
    neuWahl.gegner = einst.gegner; neuWahl.farbe = einst.farbe;
    seg($("segGegner"), neuWahl.gegner); seg($("segFarbe"), neuWahl.farbe);
    $("nurMotor").hidden = neuWahl.gegner !== "motor";
    $("selStufe").value = String(einst.stufe); schalter($("schLernNeu"), einst.lern);
    $("bNeuAbbr").hidden = !spiel.gestartet;
    alleZu(); auf("dNeu");
  }
  function einstDialog() {
    $("selStufe2").value = String(spiel.stufe); $("selZeit").value = String(einst.zeit);
    $("einstMotor").hidden = spiel.gegner !== "motor";
    schalter($("schLern"), einst.lern); schalter($("schTon"), einst.ton); schalter($("schBalken"), einst.balken); schalter($("schDrehen"), einst.autodrehen);
    auf("dEinst");
  }
  function lernSetzen(an) {
    einst.lern = !!an; einstSpeichern();
    schalter($("schLern"), einst.lern); schalter($("schLernNeu"), einst.lern);
    knoepfe(spiel.partie.zustand());
    if (einst.lern && menschDran()) analysiere();
  }

  /* ---------- Knöpfe ---------- */
  function zugZurueck() {
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
    $("frageText").textContent = spiel.gegner === "mensch" ? (c === "w" ? "Weiss" : "Schwarz") + " gibt die Partie auf?" : "Willst du diese Partie wirklich aufgeben?";
    frage("dFrage", { bFrageNein: false, bFrageJa: true }).then(function (ja) {
      if (!ja || p !== spiel.partie || p.ende()) return;
      abbrechen(); spiel.nr++; spiel.denkt = false;
      var z = p.aufgeben(c); partieSpeichern(); ton("remis"); zeichne(z); endeZeigen(z); balkenEnde(z.ende);
    });
  }

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
    var leisten = 48 + (einst.balken ? 6 : 0), bedarf = 6;        // Platz für Status, Zugliste, Knöpfe, Info-Zeile (gemessen)
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
    $("bDrehen").onclick = function () { spiel.drehung = spiel.drehung === "w" ? "b" : "w"; partieSpeichern(); zeichne(); };
    $("bNeu").onclick = neuDialog;
    $("bAufgeben").onclick = aufgeben;
    $("bEinst").onclick = einstDialog;
    $("bLern").onclick = function () { lernSetzen(!einst.lern); };
    $("bUeber").onclick = function () { infoZeile(); auf("dUeber"); };
    $("bUeberZu").onclick = function () { zu("dUeber"); };
    $("bEinstZu").onclick = function () { zu("dEinst"); };
    $("bEndeBrett").onclick = function () { zu("dEnde"); };
    $("bEndeNeu").onclick = neuDialog;
    $("bNeuAbbr").onclick = function () { zu("dNeu"); };
    $("segGegner").onclick = function (e) { var b = e.target.closest("button"); if (!b) return; neuWahl.gegner = b.getAttribute("data-w"); seg($("segGegner"), neuWahl.gegner); $("nurMotor").hidden = neuWahl.gegner !== "motor"; };
    $("segFarbe").onclick = function (e) { var b = e.target.closest("button"); if (!b) return; neuWahl.farbe = b.getAttribute("data-w"); seg($("segFarbe"), neuWahl.farbe); };
    $("schLernNeu").onclick = function () { lernSetzen(!einst.lern); };
    $("bSpielen").onclick = function () {
      einst.gegner = neuWahl.gegner; einst.farbe = neuWahl.farbe; einst.stufe = +$("selStufe").value || einst.stufe; einstSpeichern();
      spiel.gestartet = true;
      starte({ gegner: einst.gegner, stufe: einst.stufe, farbe: einst.farbe === "zufall" ? (Math.random() < 0.5 ? "w" : "b") : einst.farbe });
    };
    $("selStufe2").onchange = function () { spiel.stufe = einst.stufe = +this.value || einst.stufe; einstSpeichern(); partieSpeichern(); zeichne(); };
    $("selZeit").onchange = function () { einst.zeit = +this.value || 1000; einstSpeichern(); };
    $("schLern").onclick = function () { lernSetzen(!einst.lern); };
    $("schTon").onclick = function () { einst.ton = !einst.ton; einstSpeichern(); schalter(this, einst.ton); tonStart(); ton("zug"); };
    $("schBalken").onclick = function () { einst.balken = !einst.balken; einstSpeichern(); schalter(this, einst.balken); ordnen(); zeichne(); infoZeile(); if (einst.balken && menschDran()) analysiere(); };
    $("schDrehen").onclick = function () { einst.autodrehen = !einst.autodrehen; einstSpeichern(); schalter(this, einst.autodrehen); };

    // angefangene Partie?
    var g = lies(K_PARTIE), alt = g && g.partie ? P.laden(g.partie) : null;
    zeichne();
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
        return { fen: z.fen, amZug: z.amZug, schach: z.schach, ende: z.ende, zuege: z.zuege, san: z.san, zugNr: z.zugNr, gegner: spiel.gegner, mensch: spiel.mensch,
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
