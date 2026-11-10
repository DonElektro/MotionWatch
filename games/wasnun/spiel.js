/* «Was nun?» - Ablauf des Spiels (eigenes Spiel für MoveEye, MIT).

   EIN BILD (Szene) ist eine Datei in szenen/ und meldet sich mit WASNUN.szene({...}) an:

     id        kurzer Name (wird gespeichert, nie ändern)
     titel     Name auf der Kachel
     stufe     Schwierigkeit 1 leicht · 2 mittel · 3 knifflig · 4 Meister (steht auf der Kachel)
     ziel      ein Satz: worum geht es (steht am Anfang unter dem Bild)
     start()   -> Zustand am Anfang (einfaches Objekt, nur Zahlen / Texte / true / false / Listen davon)
     bild(s)   -> SVG-Inhalt (Text) für den Zustand s, Zeichenfläche 800 x 600. Keine url(#…)-Verweise (die Kacheln
                  zeigen dasselbe Bild klein), keine Schrift im Bild. Zwei Ansichten desselben Ortes: ein Feld im
                  Zustand (z. B. s.sicht) und bild() / wenn() danach richten; gewechselt wird mit a.wechsel().
     stellen   Liste der Tipp-Flächen, die erste passende gewinnt:
                 {id, r: [x, y, breite, höhe] oder (s, t) => […], wenn: s => true/false (fehlt: immer),
                  gut: (s, t) => true/false (nur bei «richtiger Moment»: ist JETZT sicher der richtige Augenblick?),
                  schlecht: (s, t) => true/false (dazu für den Test: JETZT ist sicher der falsche Augenblick),
                  tipp: async (s, a) => Ergebnis          (Antippen ohne gewähltes Ding)
                  mit: {dingId: async (s, a) => Ergebnis} (Antippen MIT diesem gewählten Ding; fehlt der Eintrag,
                        sagt das Spiel freundlich, dass das Ding hier nicht hilft - kostet nichts)}
               Mindestgrösse einer Fläche: 92 x 92 (das sind 44 px auf einem iPhone hochkant).
     naechster(s, weg, t) -> was als Nächstes richtig ist (für den Tipp-Knopf und den Test):
                 'stelleId'  oder  {stelle: 'id', ding: 'dingId'}  oder  {kombi: ['dingA', 'dingB']}
                 oder {stelle: 'id', warte: true} (hier läuft gerade etwas ab, Geduld); dazu wahlweise wink: 'Satz'
                 (kommt ab dem zweiten Tipp im selben Bild dazu). weg: Name eines Lösungswegs aus «wege» (fehlt: der erste).
     wege      (fehlt meist) Namen der Lösungswege, z. B. ['normal', 'meister'] - der Test spielt jeden davon.
     lauf(s, t, q)   (fehlt meist) wird für jedes Bild des Bildschirms gerufen: bewegt Dinge («richtiger Moment», Zeit);
                     t = Sekunden seit Beginn, q(sel) = Element im Bild
     uhr(s, t)       (fehlt meist) etwa viermal pro Sekunde, wenn gerade nichts läuft: etwas ist mit der Zeit fertig
                     geworden -> {setze: {…}, text: 'Satz', ton: 'name', fehl: true/false} (sonst nichts zurückgeben).
                     Zeitpunkte merkt man sich im Zustand (z. B. a.mal({feuerAb: a.t})).

   DINGE ZUM MITNEHMEN (ab Bild 6; die Leiste unten hat 4 Plätze):
     dinge     {dingId: {name: 'Eimer', svg: 'SVG-Inhalt 60 x 60' oder s => '…'}}  - alles, was in der Tasche sein kann.
               Der Zustand braucht dann die Liste s.tasche (am Anfang meist []). Nie mehr als 4 Dinge zugleich.
     kombi     [{a: 'ast', b: 'zeitung', gibt: 'fackel', text: 'Satz', setze: {…}, wenn: s => …}]  zwei Dinge werden eines;
               oder {a, b, nein: 'Satz'} für einen eigenen Spruch, wenn es (noch) nicht passt. Alles andere: «Das passt
               nicht zusammen» - kostet nichts, nichts geht verloren.
     nutzlos(s, dingId, stelleId) (fehlt meist) -> eigener Spruch, wenn ein Ding an einer Stelle nichts bringt.
     Bedienung: Ding antippen = gewählt (leuchtet), nochmals = abgewählt; zweites Ding antippen = kombinieren;
     Stelle im Bild antippen = dort benutzen. Ein Ding, das seinen Zustand ändert, ist einfach ein neues Ding (a.tausch).
     Alt (Bilder 4 und 5): tasche(s) -> null oder {name, svg} zeigt ein einzelnes getragenes Ding ohne Auswahl.

   In tipp(s, a) / mit[…](s, a): s ist eine Arbeitskopie des Zustands, a hilft:
     a.mal({…})                 Zustand ändern und neu zeichnen (gilt erst mit a.weiter / a.fertig / a.wechsel)
     await a.anim(sel, kf, ms)  Element bewegen (Web Animations: Liste von Schritten wie [{transform:…}, {transform:…}])
     await a.warte(ms)          kurz warten            a.ton('name')   Geräusch (Liste unten: TON)
     a.nr                       das wievielte Mal wurde diese Stelle angetippt (1, 2, 3 …)   a.t  Sekunden seit Beginn
     a.ding                     das gewählte Ding (nur in mit[…])
     a.hat('id')   a.nimm('id')   a.gib('id') (weglegen / verbrauchen)   a.tausch('alt', 'neu')
   und das Ergebnis (immer mit return):
     return a.weiter('Text')     richtiger Schritt, der neue Zustand gilt
     return a.fertig('Text')     Bild gelöst; der Text steht als kleine Geschichte im Sternebild.
                                 a.fertig('Text', {meister: true}) = der elegantere Weg, gibt das Abzeichen «Meister-Lösung»
     return a.wechsel('Text')    nur die Ansicht gewechselt (oder sonst etwas Neutrales): der Zustand gilt, zählt nicht
     return a.gag('Text')        lustig, aber nutzlos: nichts ändert sich, kostet nichts   (a.gag('Text', true): Änderung bleibt)
     return a.fehl('Text')       entscheidender Fehlversuch (z. B. falscher Moment): zählt für die Sterne
     return a.sackgasse('Text')  falsche Reihenfolge: das Bild spult sichtbar zum letzten guten Stand zurück (auch die
                                 Tasche), zählt für die Sterne
     return a.geheim('Text')     das versteckte Extra dieses Bildes

   STERNE: 3 = ohne Fehlversuch und ohne Tipp · 2 = höchstens 3 Fehlversuche, ohne Tipp · 1 = mit Tipp (oder mehr Fehlversuche).
   Lustige falsche Stellen und unsinniges Kombinieren kosten nie etwas - Ausprobieren soll Spass machen.
   Gespeichert wird unter «mw-wasnun-v1» (Sterne, Geheimnisse, Meister-Lösungen je Bild-id): neue Bilder kommen dazu,
   alte Einträge bleiben. */
(function () {
  'use strict';
  var SZ = [], KEY = 'mw-wasnun-v1', MIN = 92;
  var Q = (function () { try { return new URLSearchParams(location.search); } catch (e) { return { get: function () { return null; } }; } })();
  var TEST = Q.get('test') === '1', ZEIG = Q.get('zeig') === '1', TEMPO = TEST ? Math.max(1, +Q.get('tempo') || 6) : 1, PLATZ = 4;
  var $ = function (id) { return document.getElementById(id); };
  var bild, fx;
  var S = { i: -1, sz: null, zustand: null, busy: false, fertig: false, fehler: 0, tipp: false, ohne: 0, t0: 0, n: {}, akt: null, spul: 0, wahl: null, neu: null, tippN: 0, meister: false, schluss: '', uhrT: 0, nein: 0 };
  var MERK = { sterne: {}, geheim: {}, meister: {}, stumm: false };

  // ---- Speichern (geht auch ohne: dann gilt der Fortschritt bis zum Schliessen der Seite) ----
  function laden() {
    try { var d = JSON.parse(localStorage.getItem(KEY) || '{}'); if (d && typeof d === 'object') { MERK.sterne = d.sterne || {}; MERK.geheim = d.geheim || {}; MERK.meister = d.meister || {}; MERK.stumm = !!d.stumm; } } catch (e) {}
  }
  function sichern() { try { localStorage.setItem(KEY, JSON.stringify(MERK)); } catch (e) {} }

  // ---- Ton: kleine erzeugte Geräusche (WebAudio), erst nach der ersten Berührung (iOS) ----
  var AC = null;
  function audio() {
    if (MERK.stumm) return null;
    try { if (!AC) AC = new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === 'suspended') AC.resume(); } catch (e) { return null; }
    return AC;
  }
  function piep(f, d, o) {
    var ac = audio(); if (!ac) return; o = o || {};
    try {
      var t = ac.currentTime + (o.ab || 0), os = ac.createOscillator(), g = ac.createGain();
      os.type = o.typ || 'sine'; os.frequency.setValueAtTime(f, t);
      if (o.zu) os.frequency.exponentialRampToValueAtTime(o.zu, t + d);
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(o.v || 0.16, t + (o.an || 0.012)); g.gain.exponentialRampToValueAtTime(0.0001, t + d);
      os.connect(g); g.connect(ac.destination); os.start(t); os.stop(t + d + 0.05);
    } catch (e) {}
  }
  function rausch(d, o) {
    var ac = audio(); if (!ac) return; o = o || {};
    try {
      var n = Math.max(1, Math.floor(ac.sampleRate * d)), b = ac.createBuffer(1, n, ac.sampleRate), x = b.getChannelData(0);
      for (var i = 0; i < n; i++) x[i] = Math.random() * 2 - 1;
      var q = ac.createBufferSource(), fl = ac.createBiquadFilter(), g = ac.createGain(), t = ac.currentTime + (o.ab || 0);
      q.buffer = b; fl.type = o.art || 'bandpass'; fl.frequency.setValueAtTime(o.f || 1200, t); if (o.zu) fl.frequency.exponentialRampToValueAtTime(o.zu, t + d);
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(o.v || 0.12, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + d);
      q.connect(fl); fl.connect(g); g.connect(ac.destination); q.start(t);
    } catch (e) {}
  }
  var TON = {
    tap: function () { piep(480, 0.05, { v: 0.05 }); },
    ok: function () { piep(523, 0.12); piep(784, 0.2, { ab: 0.1 }); },
    fehl: function () { piep(220, 0.22, { typ: 'triangle', zu: 150, v: 0.14 }); },
    rueck: function () { for (var i = 0; i < 7; i++) piep(900 - i * 90, 0.07, { ab: i * 0.09, typ: 'square', v: 0.05 }); },
    fertig: function () { [523, 659, 784, 1047].forEach(function (f, i) { piep(f, 0.22, { ab: i * 0.13, typ: 'triangle', v: 0.17 }); }); },
    stern: function () { piep(1175, 0.25, { v: 0.12 }); piep(1568, 0.3, { ab: 0.06, v: 0.08 }); },
    geheim: function () { [988, 1319, 1568, 1976, 2637].forEach(function (f, i) { piep(f, 0.16, { ab: i * 0.07, v: 0.1 }); }); },
    tipp: function () { piep(660, 0.12, { v: 0.1 }); piep(880, 0.25, { ab: 0.12, v: 0.1 }); },
    boing: function () { piep(180, 0.3, { zu: 420, typ: 'triangle' }); },
    plopp: function () { piep(300, 0.08, { zu: 700 }); },
    plumps: function () { piep(160, 0.18, { zu: 70, typ: 'triangle', v: 0.2 }); },
    pieps: function () { piep(2100, 0.07, { zu: 2900, v: 0.08 }); piep(2500, 0.09, { ab: 0.1, zu: 3200, v: 0.08 }); },
    flatter: function () { for (var i = 0; i < 5; i++) rausch(0.05, { ab: i * 0.07, f: 700, v: 0.1 }); },
    quak: function () { piep(190, 0.16, { typ: 'sawtooth', zu: 150, v: 0.1 }); piep(210, 0.2, { ab: 0.2, typ: 'sawtooth', zu: 140, v: 0.1 }); },
    wasser: function () { rausch(0.9, { f: 2400, zu: 1500, v: 0.1 }); },
    tropf: function () { piep(1400, 0.07, { zu: 700, v: 0.1 }); },
    klick: function () { rausch(0.03, { f: 3000, v: 0.2 }); },
    knarr: function () { piep(90, 0.35, { typ: 'sawtooth', zu: 130, v: 0.08 }); },
    glocke: function () { piep(880, 0.7, { v: 0.14 }); piep(1320, 0.5, { v: 0.07 }); piep(2210, 0.3, { v: 0.04 }); },
    kuhglocke: function () { piep(540, 0.3, { typ: 'square', v: 0.06 }); piep(810, 0.25, { typ: 'square', v: 0.04 }); piep(560, 0.3, { ab: 0.28, typ: 'square', v: 0.05 }); },
    muh: function () { piep(150, 0.7, { typ: 'sawtooth', zu: 110, v: 0.1, an: 0.15 }); },
    horn: function () { piep(131, 0.5, { typ: 'triangle', v: 0.2, an: 0.08 }); piep(196, 0.5, { ab: 0.45, typ: 'triangle', v: 0.2, an: 0.08 }); piep(262, 0.9, { ab: 0.9, typ: 'triangle', v: 0.2, an: 0.08 }); },
    puff: function () { rausch(0.25, { f: 500, zu: 200, v: 0.14 }); },
    kraechz: function () { piep(520, 0.16, { typ: 'sawtooth', zu: 380, v: 0.09 }); piep(500, 0.18, { ab: 0.2, typ: 'sawtooth', zu: 360, v: 0.09 }); },
    zisch: function () { rausch(0.4, { f: 5000, zu: 2500, v: 0.08 }); },
    pfeif: function () { piep(1800, 0.9, { zu: 2400, v: 0.08, an: 0.2 }); },
    schnarch: function () { rausch(0.5, { f: 180, v: 0.16 }); piep(700, 0.3, { ab: 0.55, zu: 1100, v: 0.03 }); },
    miau: function () { piep(700, 0.35, { zu: 1000, typ: 'triangle', v: 0.1, an: 0.1 }); piep(1000, 0.25, { ab: 0.33, zu: 600, typ: 'triangle', v: 0.1 }); },
    schnurr: function () { for (var i = 0; i < 8; i++) rausch(0.05, { ab: i * 0.06, f: 120, v: 0.12 }); },
    fiep: function () { piep(2600, 0.06, { v: 0.07 }); piep(3000, 0.06, { ab: 0.09, v: 0.07 }); },
    metall: function () { piep(1244, 0.25, { typ: 'square', v: 0.04 }); piep(1661, 0.2, { typ: 'square', v: 0.03 }); },
    robo: function () { [330, 440, 330, 660].forEach(function (f, i) { piep(f, 0.09, { ab: i * 0.1, typ: 'square', v: 0.06 }); }); },
    radio: function () { [392, 494, 587, 494, 392].forEach(function (f, i) { piep(f, 0.12, { ab: i * 0.13, typ: 'square', v: 0.04 }); }); },
    ring: function () { for (var i = 0; i < 10; i++) piep(i % 2 ? 1900 : 2300, 0.05, { ab: i * 0.055, typ: 'square', v: 0.06 }); },
    platsch: function () { rausch(0.35, { f: 900, zu: 300, v: 0.2 }); },
    kuckuck: function () { piep(784, 0.18, { v: 0.12 }); piep(622, 0.28, { ab: 0.22, v: 0.12 }); },
    huch: function () { piep(500, 0.15, { zu: 900, typ: 'triangle', v: 0.1 }); },
    jodel: function () { [392, 523, 659, 523, 784].forEach(function (f, i) { piep(f, 0.14, { ab: i * 0.14, typ: 'triangle', v: 0.12 }); }); }
  };
  function ton(n) { if (TON[n]) TON[n](); }

  // ---- kleine Zeichen-Hilfen für die Bilder (alle geben SVG-Text zurück) ----
  var Z = {
    auge: function (x, y, r, zu, dx, dy) {
      r = r || 7;
      if (zu) return '<path class="l n" d="M' + (x - r) + ' ' + y + ' q' + r + ' ' + (r * 0.9) + ' ' + (2 * r) + ' 0"/>';
      return '<circle class="d" cx="' + x + '" cy="' + y + '" r="' + r + '" fill="#fff"/><circle cx="' + (x + (dx || 0)) + '" cy="' + (y + (dy || 0)) + '" r="' + (r * 0.48) + '" fill="#2b2530"/>';
    },
    wolke: function (x, y, k, f) {
      return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><path class="l" fill="' + (f || '#fff') + '" d="M-58 22a24 24 0 0 1 4-47a34 34 0 0 1 62-10a28 28 0 0 1 46 26a17 17 0 0 1-4 31z"/></g>';
    },
    sonne: function (x, y, brille) {
      var s = '<g transform="translate(' + x + ' ' + y + ')"><g class="dreh" style="animation:wedel 6s ease-in-out infinite">';
      for (var i = 0; i < 8; i++) s += '<path class="l" style="stroke:#f2a900;stroke-width:6" d="M0 -52V-66" transform="rotate(' + i * 45 + ')"/>';
      s += '</g><circle class="l" r="42" fill="#ffd23f"/>';
      s += brille ? '<path class="l" fill="#2b2530" d="M-30 -10h24v10a12 12 0 0 1-24 0zM6 -10h24v10a12 12 0 0 1-24 0z"/><path class="l n" d="M-6 -8h12"/>'
        : Z.auge(-14, -6, 7) + Z.auge(14, -6, 7);
      return s + '<path class="l n" d="M-14 14q14 12 28 0"/></g>';
    },
    mond: function (x, y, zu) {
      return '<g transform="translate(' + x + ' ' + y + ')"><circle class="l" r="44" fill="#fdf3c0"/><circle cx="-16" cy="16" r="7" fill="#eadf9f"/><circle cx="20" cy="-22" r="5" fill="#eadf9f"/>'
        + Z.auge(-12, -6, 6, zu) + Z.auge(14, -6, 6, zu) + '<path class="d n" d="M-6 14q7 6 14 0"/></g>';
    },
    stern: function (x, y, r) { return '<path fill="#fff7c2" d="M' + x + ' ' + (y - r) + 'l' + r * 0.3 + ' ' + r * 0.7 + 'l' + r * 0.7 + ' ' + r * 0.3 + 'l' + -r * 0.7 + ' ' + r * 0.3 + 'l' + -r * 0.3 + ' ' + r * 0.7 + 'l' + -r * 0.3 + ' ' + -r * 0.7 + 'l' + -r * 0.7 + ' ' + -r * 0.3 + 'l' + r * 0.7 + ' ' + -r * 0.3 + 'z"/>'; },
    // runder kleiner Vogel um (0,0); o: {f: Farbe, zu: schläft, flug: Flügel offen, spiegel}
    vogel: function (o) {
      o = o || {}; var f = o.f || '#e8574a';
      return '<g' + (o.spiegel ? ' transform="scale(-1 1)"' : '') + '><path class="d n" d="M-6 22v10M6 22v10"/><ellipse class="l" cx="0" cy="0" rx="24" ry="22" fill="' + f + '"/>'
        + '<ellipse cx="4" cy="8" rx="13" ry="10" fill="#fff" opacity=".35"/>'
        + (o.flug ? '<path class="l" fill="' + f + '" d="M-8 -4q-26 -34 -40 -18q14 6 26 26z"/>' : '<path class="l" fill="' + f + '" d="M-18 -2q8 16 22 8q-6 -12 -22 -8z"/>')
        + '<path class="l" fill="#f2a900" d="M21 -6l16 5l-16 6z"/>' + Z.auge(10, -8, 6, o.zu, 1.5, 0) + '</g>';
    },
    zzz: function (x, y, k) {
      return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><g class="a-schweb"><path class="l n" style="stroke:#fff;stroke-width:4" d="M0 0h14l-14 16h14"/><path class="l n" style="stroke:#fff;stroke-width:3" d="M22 -18h10l-10 11h10"/><path class="l n" style="stroke:#fff;stroke-width:2.5" d="M40 -32h7l-7 8h7"/></g></g>';
    },
    blume: function (x, y, f, h) {
      h = h || 34; var s = '<g transform="translate(' + x + ' ' + y + ')"><path class="l n" style="stroke:#3d8a3a;stroke-width:4" d="M0 0v' + -h + '"/><path class="d" fill="#57b04f" d="M0 -8q12 -10 18 -2q-10 8 -18 2z"/><g transform="translate(0 ' + -h + ')">';
      for (var i = 0; i < 5; i++) s += '<circle class="d" cx="0" cy="-10" r="8" fill="' + f + '" transform="rotate(' + i * 72 + ')"/>';
      return s + '<circle class="d" r="6" fill="#ffd23f"/></g></g>';
    },
    busch: function (x, y, k, f) {
      return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><path class="l" fill="' + (f || '#3f9b46') + '" d="M-62 0a26 26 0 0 1 8-46a32 32 0 0 1 52-18a30 30 0 0 1 50 18a24 24 0 0 1 12 46z"/><path class="d n" style="stroke:#2f7d38" d="M-30 -22q8 -8 16 0M10 -34q8 -8 16 0M28 -12q7 -7 14 0"/></g>';
    },
    tanne: function (x, y, k) {
      return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><rect class="l" x="-9" y="-30" width="18" height="30" fill="#8a5a3a"/><path class="l" fill="#2f7d4a" d="M0 -190l44 62h-22l38 52h-24l40 50h-152l40 -50h-24l38 -52h-22z"/></g>';
    },
    funken: function (x, y, f) {
      var s = '<g transform="translate(' + x + ' ' + y + ')">';
      for (var i = 0; i < 8; i++) s += '<path class="l" style="stroke:' + (f || '#ffd23f') + ';stroke-width:5" d="M0 -18V-34" transform="rotate(' + i * 45 + ')"/>';
      return s + '</g>';
    },
    stern5: function (an) { return '<svg viewBox="0 0 24 24" class="' + (an ? 'an' : '') + '"><path class="' + (an ? 'st-an' : 'st-aus') + '" stroke-width="1.5" stroke-linejoin="round" d="M12 2.5l2.9 6.2 6.8.7-5.1 4.6 1.5 6.7L12 17.3 5.9 20.7l1.5-6.7L2.3 9.4l6.8-.7z"/></svg>'; }
  };

  // ---- Helfer ----
  var STUFEN = ['', 'leicht', 'mittel', 'knifflig', 'Meister'];
  function klon(o) { return JSON.parse(JSON.stringify(o)); }
  function warte(ms) { return new Promise(function (r) { setTimeout(r, ms / TEMPO); }); }
  function zeit() { return (performance.now() - S.t0) / 1000; }
  function q(sel) { return bild.querySelector(sel); }
  function anim(sel, kf, ms, o) {
    var el = typeof sel === 'string' ? q(sel) : sel;
    if (!el || !el.animate) return warte(ms);
    var opt = { duration: Math.max(1, ms / TEMPO), easing: 'ease-in-out', fill: 'forwards' };
    if (o) for (var k in o) opt[k] = o[k];
    try {
      var an = el.animate(kf, opt);
      return (an.finished || new Promise(function (r) { an.onfinish = r; })).then(function () {}, function () {});
    } catch (e) { return warte(ms); }
  }
  function male(s) { bild.innerHTML = S.sz.bild(s); if (S.sz.lauf) try { S.sz.lauf(s, zeit(), q); } catch (e) {} tasche(s); if (ZEIG) zeigeStellen(s); }
  function rect(st, s) { return typeof st.r === 'function' ? st.r(s, zeit()) : st.r; }
  function finde(x, y, s) {
    var L = S.sz.stellen;
    for (var i = 0; i < L.length; i++) {
      var st = L[i]; if (st.wenn && !st.wenn(s)) continue;
      var r = rect(st, s); if (x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3]) return st;
    }
    return null;
  }
  function sterneJetzt() { return S.tipp ? 1 : S.fehler === 0 ? 3 : S.fehler <= 3 ? 2 : 1; }
  function sterneHtml(n) { return Z.stern5(n >= 1) + Z.stern5(n >= 2) + Z.stern5(n >= 3); }
  function offen(i) { return i === 0 || !!MERK.sterne[SZ[i - 1].id] || Q.get('alle') === '1'; }
  function sag(t, frage) {
    var e = $('text'); if (frage) e.innerHTML = t; else e.textContent = t || '';
    e.classList.remove('neu'); void e.offsetWidth; e.classList.add('neu');
  }
  function hud() {
    $('hudSterne').innerHTML = sterneHtml(sterneJetzt());
    $('hudSterne').setAttribute('title', 'Sterne für dieses Bild');
    $('bTipp').classList.toggle('lockt', !S.fertig && !S.tipp && (S.ohne >= 6 || S.fehler >= 2));
  }
  function ding(id, s) {
    var d = (S.sz.dinge || {})[id] || { name: id, svg: '' };
    return { name: d.name, svg: typeof d.svg === 'function' ? d.svg(s) : d.svg };
  }
  function platz(id) { var L = $('tasche').querySelectorAll('.platz[data-d]'); for (var i = 0; i < L.length; i++) if (L[i].getAttribute('data-d') === id) return L[i]; return null; }
  function tasche(s) {
    var e = $('tasche'), sz = S.sz, L = $('leiste');
    if (!sz) { e.hidden = true; return; }
    if (sz.dinge) {                      // ab Bild 6: bis 4 Dinge, wählbar und kombinierbar
      var T = s.tasche || [], h = '';
      L.classList.add('viel'); e.hidden = false; e.className = 'viel';
      if (S.wahl && T.indexOf(S.wahl) < 0) S.wahl = null;
      for (var i = 0; i < Math.max(PLATZ, T.length); i++) {
        if (T[i]) { var d = ding(T[i], s); h += '<button type="button" class="platz' + (S.wahl === T[i] ? ' wahl' : '') + (S.neu === T[i] ? ' neu' : '') + '" data-d="' + T[i] + '" aria-label="' + d.name + '" aria-pressed="' + (S.wahl === T[i]) + '" title="' + d.name + '"><svg viewBox="0 0 60 60">' + d.svg + '</svg></button>'; }
        else h += '<span class="platz frei"></span>';
      }
      e.innerHTML = h; S.neu = null; return;
    }
    L.classList.remove('viel');
    if (!sz.tasche) { e.hidden = true; return; }
    e.hidden = false;
    var x = sz.tasche(s), war = e.getAttribute('data-n') || '';
    if (x) { if (war !== x.name) { e.className = ''; void e.offsetWidth; } e.className = 'voll'; e.setAttribute('data-n', x.name); e.setAttribute('title', x.name); e.innerHTML = '<svg viewBox="0 0 60 60">' + x.svg + '</svg>'; }
    else { e.className = ''; e.setAttribute('data-n', ''); e.innerHTML = '<div class="leer">Tasche leer</div>'; }
  }
  function tonKnopf() {
    $('bTon').innerHTML = MERK.stumm
      ? '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9h4l5-4v14l-5-4H4z" fill="currentColor"/><path d="M17 9l5 6M22 9l-5 6"/></svg>'
      : '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9h4l5-4v14l-5-4H4z" fill="currentColor"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19.5 6a9 9 0 0 1 0 12"/></svg>';
    $('bTon').setAttribute('aria-label', MERK.stumm ? 'Ton ist aus' : 'Ton ist an');
    $('bTon').setAttribute('aria-pressed', MERK.stumm ? 'true' : 'false');
  }
  function passe() {
    var b = $('buehne'); if (!b || $('spiel').hidden) return;
    var W = b.clientWidth, H = b.clientHeight, w = Math.min(W, H * 4 / 3);
    $('rahmen').style.width = Math.floor(w) + 'px'; $('rahmen').style.height = Math.floor(w * 0.75) + 'px';
  }
  function welle(x, y) {
    var c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 10); c.setAttribute('fill', 'none'); c.setAttribute('stroke', '#fff'); c.setAttribute('stroke-width', 5);
    fx.appendChild(c);
    if (c.animate) c.animate([{ r: '8px', opacity: 0.9 }, { r: '46px', opacity: 0 }], { duration: 380, easing: 'ease-out' }).onfinish = function () { c.remove(); };
    else setTimeout(function () { c.remove(); }, 300);
  }
  function zeigeStellen(s) {
    var alt = fx.querySelectorAll('.zeig'); for (var i = 0; i < alt.length; i++) alt[i].remove();
    S.sz.stellen.forEach(function (st) {
      if (st.wenn && !st.wenn(s)) return; var r = rect(st, s);
      fx.insertAdjacentHTML('beforeend', '<g class="zeig"><rect x="' + r[0] + '" y="' + r[1] + '" width="' + r[2] + '" height="' + r[3] + '" fill="rgba(255,0,120,.12)" stroke="#f08" stroke-width="2"/><text x="' + (r[0] + 4) + '" y="' + (r[1] + 16) + '" font-size="15" fill="#f08" font-family="sans-serif">' + st.id + '</text></g>');
    });
  }

  // ---- was eine Stelle beim Antippen tun kann ----
  function Akt(st, dingId) { this.s = klon(S.zustand); this.t = zeit(); this.ding = dingId || null; this.nr = S.n[st.id] = (S.n[st.id] || 0) + 1; }
  Akt.prototype = {
    mal: function (p) { for (var k in p) this.s[k] = p[k]; male(this.s); },
    anim: anim, warte: warte, ton: ton, q: q,
    hat: function (id) { return (this.s.tasche || []).indexOf(id) >= 0; },
    nimm: function (id) { var T = (this.s.tasche || []).slice(); if (T.indexOf(id) < 0) T.push(id); S.neu = id; this.mal({ tasche: T }); },
    gib: function (id) { this.mal({ tasche: (this.s.tasche || []).filter(function (x) { return x !== id; }) }); },
    tausch: function (alt, neu) { S.neu = neu; this.mal({ tasche: (this.s.tasche || []).map(function (x) { return x === alt ? neu : x; }) }); },
    weiter: function (t) { return { art: 'weiter', text: t }; },
    fertig: function (t, o) { return { art: 'fertig', text: t, meister: !!(o && o.meister) }; },
    wechsel: function (t) { return { art: 'wechsel', text: t }; },
    gag: function (t, bleibt) { return { art: 'gag', text: t, bleibt: !!bleibt }; },
    fehl: function (t) { return { art: 'fehl', text: t }; },
    sackgasse: function (t) { return { art: 'sackgasse', text: t }; },
    geheim: function (t) { return { art: 'geheim', text: t }; }
  };
  var NUTZLOS = ['«%» hilft hier nicht weiter.', 'Damit? Hier? Das bringt nichts.', '«%» passt hier nicht. Vielleicht woanders.'];
  var NEIN = ['Das passt nicht zusammen.', '«%a» und «%b»? Daraus wird nichts.', 'Hübsche Idee – aber das hält nicht zusammen.'];

  function tippe(x, y) {
    if (S.busy || S.fertig || !S.sz) return;
    welle(x, y);
    var st = finde(x, y, S.zustand), dg = S.wahl, fn;
    if (!st) { if (dg) { S.wahl = null; tasche(S.zustand); } ton('tap'); return; }
    if (dg) {
      S.wahl = null; fn = st.mit && st.mit[dg];
      if (!fn) {                         // das Ding bringt hier nichts: freundlich sagen, kostet nichts
        tasche(S.zustand); ton('boing'); S.ohne++;
        sag((S.sz.nutzlos && S.sz.nutzlos(S.zustand, dg, st.id)) || NUTZLOS[S.nein++ % NUTZLOS.length].replace('%', ding(dg, S.zustand).name));
        hud(); return;
      }
    } else fn = st.tipp;
    if (!fn) { ton('tap'); return; }
    S.busy = true;
    var a = new Akt(st, dg);
    S.akt = a.s;                       // lauf() sieht während der Aktion die Arbeitskopie (Bewegtes springt nicht)
    Promise.resolve().then(function () { return fn(a.s, a); }).then(null, function (e) { if (window.console) console.error(e); return { art: 'gag', text: '' }; }).then(function (r) {
      r = r || { art: 'gag', text: '' };
      if (r.art === 'weiter') { S.zustand = a.s; S.ohne = 0; ton('ok'); sag(r.text); male(S.zustand); }
      else if (r.art === 'wechsel') { S.zustand = a.s; if (r.text) sag(r.text); male(S.zustand); }
      else if (r.art === 'fertig') { S.zustand = a.s; S.fertig = true; S.meister = r.meister; S.schluss = r.text; sag(r.text); male(S.zustand); return warte(900).then(schluss); }
      else if (r.art === 'geheim') {
        var neu = !MERK.geheim[S.sz.id]; MERK.geheim[S.sz.id] = 1; sichern(); ton('geheim');
        sag((neu ? 'Geheimnis gefunden! ' : 'Das Geheimnis kennst du schon: ') + (r.text || ''));
        return warte(500).then(function () { male(S.zustand); });
      }
      else if (r.art === 'fehl') { S.fehler++; ton('fehl'); sag(r.text); male(S.zustand); }
      else if (r.art === 'sackgasse') {
        S.fehler++; ton('fehl'); sag(r.text);
        return warte(1300).then(function () {
          ton('rueck'); S.spul++; S.akt = null;
          var b = $('buehne'); b.classList.remove('rueck'); void b.offsetWidth; b.classList.add('rueck');
          return warte(450);
        }).then(function () { male(S.zustand); return warte(450); }).then(function () { $('buehne').classList.remove('rueck'); sag('Zurückgespult. ' + r.text); });
      }
      else { if (r.bleibt) S.zustand = a.s; S.ohne++; if (r.text) sag(r.text); male(S.zustand); }
    }).then(function () { S.akt = null; S.busy = false; hud(); });
  }

  // ---- Dinge in der Leiste: wählen, abwählen, zwei kombinieren ----
  function kombiFinde(a, b, s) {
    var L = S.sz.kombi || [];
    for (var i = 0; i < L.length; i++) { var k = L[i]; if (((k.a === a && k.b === b) || (k.a === b && k.b === a)) && (!k.wenn || k.wenn(s))) return k; }
    return null;
  }
  function platzTipp(id) {
    if (S.busy || S.fertig || !S.sz || !S.sz.dinge) return;
    var s = S.zustand, d = ding(id, s);
    if (!S.wahl) { S.wahl = id; ton('tap'); tasche(s); sag('«' + d.name + '» gewählt. Tippe auf eine Stelle im Bild – oder auf ein zweites Ding zum Kombinieren.'); return; }
    if (S.wahl === id) { S.wahl = null; ton('tap'); tasche(s); sag('«' + d.name + '» wieder eingesteckt.'); return; }
    var a = S.wahl, k = kombiFinde(a, id, s), ea = platz(a), eb = platz(id);
    S.wahl = null; S.busy = true;
    var fertig = function () { S.busy = false; hud(); };
    if (k && k.gibt) {
      var ra = ea.getBoundingClientRect(), rb = eb.getBoundingClientRect(), dx = (rb.left - ra.left) / 2, dy = (rb.top - ra.top) / 2;
      ton('plopp');
      Promise.all([anim(ea, [{ transform: 'translate(0,0)' }, { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(.8) rotate(-12deg)' }], 380),
        anim(eb, [{ transform: 'translate(0,0)' }, { transform: 'translate(' + (-dx) + 'px,' + (-dy) + 'px) scale(.8) rotate(12deg)' }], 380)]).then(function () {
        var n = klon(s); n.tasche = n.tasche.filter(function (x) { return x !== a && x !== id; }); n.tasche.push(k.gibt);
        if (k.setze) for (var f in k.setze) n[f] = k.setze[f];
        S.zustand = n; S.neu = k.gibt; S.ohne = 0; ton('ok'); male(n);
        sag(k.text || ('Daraus wird: «' + ding(k.gibt, n).name + '».'));
      }).then(fertig);
    } else {
      ton('boing'); S.ohne++;
      var kf = [{ transform: 'translateX(0)' }, { transform: 'translateX(-6px)' }, { transform: 'translateX(6px)' }, { transform: 'translateX(-4px)' }, { transform: 'translateX(0)' }];
      sag(k && k.nein ? k.nein : NEIN[S.nein++ % NEIN.length].replace('%a', d.name).replace('%b', ding(a, s).name));
      Promise.all([anim(ea, kf, 350, { fill: 'none' }), anim(eb, kf, 350, { fill: 'none' })]).then(function () { tasche(s); }).then(fertig);
    }
  }

  // ---- Tipp: die Gegend pulsiert, nicht die genaue Stelle; ab dem zweiten Tipp im selben Bild etwas genauer ----
  function norm(n) { return !n ? {} : typeof n === 'string' ? { stelle: n } : n; }
  function naechster(weg) { return norm(S.sz.naechster(S.zustand, weg || (S.sz.wege || [])[0], zeit())); }
  function pulsPlatz(id) { var e = platz(id); if (e) { e.classList.remove('puls'); void e.offsetWidth; e.classList.add('puls'); } }
  function tippFrage() {
    if (S.busy || S.fertig) return;
    if (S.tipp) return tippZeigen();
    sag('<div class="frage"><span>Tipp zeigen? Dann gibt es für dieses Bild höchstens 1 Stern.</span><button type="button" class="ja" id="tJa">Ja, zeigen</button><button type="button" id="tNein">Nein</button></div>', true);
    $('tJa').onclick = function () { S.tipp = true; hud(); tippZeigen(); };
    $('tNein').onclick = function () { sag(S.sz.ziel); };
  }
  function tippZeigen() {
    var n = naechster(), st = null, genau = ++S.tippN > 1, s = S.zustand;
    ton('tipp');
    if (n.kombi) {
      pulsPlatz(n.kombi[0]); pulsPlatz(n.kombi[1]);
      sag(genau ? '«' + ding(n.kombi[0], s).name + '» und «' + ding(n.kombi[1], s).name + '» gehören zusammen: eines antippen, dann das andere.' : 'Zwei Dinge in deiner Tasche gehören zusammen.');
      return;
    }
    S.sz.stellen.forEach(function (x) { if (x.id === n.stelle && !st && (!x.wenn || x.wenn(s))) st = x; });
    if (!st) return;
    var r = rect(st, s), k = (S.n['?'] = (S.n['?'] || 0) + 1), w = genau ? 0.5 : 1;
    var cx = r[0] + r[2] / 2 + w * [28, -30, 12][k % 3], cy = r[1] + r[3] / 2 + w * [-22, 18, 30][k % 3], R = Math.max(r[2], r[3]) / 2 + (genau ? 40 : 70);
    cx = Math.max(R * 0.6, Math.min(800 - R * 0.6, cx)); cy = Math.max(R * 0.6, Math.min(600 - R * 0.6, cy));
    var t = n.warte ? 'Hier tut sich gerade etwas. Hab einen Moment Geduld …'
      : n.ding ? (genau ? 'Hier hilft: «' + ding(n.ding, s).name + '». Erst das Ding antippen, dann die Stelle.' : 'Schau mal in diese Gegend … und in deine Tasche.')
      : 'Schau mal in diese Gegend …';
    if (genau && n.wink) t += ' ' + n.wink;
    sag(t);
    if (n.ding && genau) pulsPlatz(n.ding);
    var c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('class', 'tippkreis'); c.setAttribute('cx', cx); c.setAttribute('cy', cy); c.setAttribute('r', R);
    c.setAttribute('fill', 'rgba(255,210,63,.22)'); c.setAttribute('stroke', '#ffd23f'); c.setAttribute('stroke-width', 6); c.setAttribute('stroke-dasharray', '14 12');
    c.style.transformBox = 'fill-box'; c.style.transformOrigin = '50% 50%';
    var alt = fx.querySelectorAll('.tippkreis'); for (var i = 0; i < alt.length; i++) alt[i].remove();
    fx.appendChild(c);
    var weg = function () { c.remove(); };
    if (c.animate) c.animate([{ transform: 'scale(.8)', opacity: 0 }, { transform: 'scale(1.05)', opacity: 1 }, { transform: 'scale(.92)', opacity: 0.6 }, { transform: 'scale(1.05)', opacity: 1 }, { transform: 'scale(.92)', opacity: 0.6 }, { transform: 'scale(1.05)', opacity: 1 }, { transform: 'scale(1.1)', opacity: 0 }], { duration: 3200 }).onfinish = weg;
    else setTimeout(weg, 3000);
  }

  // ---- Bildwahl ----
  function stufeHtml(n) {
    var h = '<span class="stufe st' + n + '" title="Schwierigkeit: ' + STUFEN[n] + '">';
    for (var i = 1; i <= 4; i++) h += '<i' + (i <= n ? ' class="an"' : '') + '></i>';
    return h + '<b>' + STUFEN[n] + '</b></span>';
  }
  function wahl() {
    S.sz = null; S.i = -1; S.wahl = null;
    $('spiel').hidden = true; $('wahl').hidden = false; $('ende').hidden = true;
    ['bBilder', 'bTipp', 'bNeu', 'hudSterne'].forEach(function (k) { $(k).hidden = true; });
    $('titel').textContent = 'Was nun?';
    document.body.classList.remove('imspiel');
    var sum = 0, geh = 0, h = '', erste = -1;
    SZ.forEach(function (sz, i) {
      var n = MERK.sterne[sz.id] || 0, auf = offen(i); sum += n; if (MERK.geheim[sz.id]) geh++;
      if (auf && !n && erste < 0) erste = i;
      h += '<button type="button" class="karte' + (auf ? '' : ' zu') + (i === erste ? ' neu' : '') + '" data-i="' + i + '"' + (auf ? '' : ' aria-disabled="true"') + ' aria-label="Bild ' + (i + 1) + ': ' + sz.titel + ', ' + STUFEN[sz.stufe || 1] + (auf ? '' : ' (noch gesperrt)') + '">'
        + '<span class="mini"><svg viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">' + sz.bild(sz.start()) + '</svg></span>'
        + (auf ? '' : '<span class="schloss"><svg width="54" height="54" viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="11" rx="3" fill="#e9a23b" stroke="#0e1621" stroke-width="1.5"/><path d="M8 10V7a4 4 0 0 1 8 0v3" fill="none" stroke="#e9a23b" stroke-width="2.5" stroke-linecap="round"/><circle cx="12" cy="15.5" r="1.8" fill="#0e1621"/></svg></span>')
        + '<span class="u"><span class="n">' + (i + 1) + ' · ' + sz.titel + '</span>' + stufeHtml(sz.stufe || 1)
        + '<span class="s">' + (auf ? sterneHtml(n) : '<span class="g" style="margin:0">Zuerst Bild ' + i + ' lösen</span>')
        + (auf ? '<span class="g">' + (MERK.meister[sz.id] ? '<span class="krone" title="Meister-Lösung gefunden">♛</span> ' : '') + (MERK.geheim[sz.id] ? 'Geheimnis ✓' : '') + '</span>' : '') + '</span></span></button>';
    });
    $('karten').innerHTML = h;
    $('chipSterne').textContent = 'Sterne ' + sum + '/' + SZ.length * 3;
    $('chipGeheim').textContent = 'Geheimnisse ' + geh + '/' + SZ.length;
    $('regel').innerHTML = '<b>So gibt es Sterne</b>'
      + '<div class="r"><span class="st">' + sterneHtml(3) + '</span><span>ohne Fehlversuch und ohne Tipp</span></div>'
      + '<div class="r"><span class="st">' + sterneHtml(2) + '</span><span>höchstens 3 Fehlversuche, ohne Tipp</span></div>'
      + '<div class="r"><span class="st">' + sterneHtml(1) + '</span><span>mit Tipp (Lampe oben) oder mehr Fehlversuche</span></div>'
      + '<div style="margin-top:6px">Ein Fehlversuch ist nur, wenn etwas schiefgeht und das Bild zurückspult oder der Moment falsch war. '
      + '<b>Herumtippen kostet nichts</b> – fast alles im Bild macht etwas Lustiges. In jedem Bild ist dazu ein Geheimnis versteckt.</div>'
      + '<div style="margin-top:8px"><b>Ab Bild 6: Dinge mitnehmen</b><br>Was du einsteckst, liegt unten in der Leiste. Ein Ding antippen und dann eine Stelle im Bild: Du benutzt es dort. '
      + 'Ein Ding antippen und dann ein zweites: Du setzt beide zusammen. Passt es nicht, kostet das nichts. Manche Bilder haben zwei Lösungen – die elegantere gibt das Abzeichen <span class="krone">♛</span> Meister-Lösung.</div>';
  }

  function starte(i) {
    if (!SZ[i] || !offen(i)) return;
    var sz = SZ[i];
    S.i = i; S.sz = sz; S.zustand = sz.start(); S.busy = false; S.fertig = false; S.fehler = 0; S.tipp = false; S.ohne = 0; S.n = {}; S.t0 = performance.now();
    S.wahl = null; S.neu = null; S.tippN = 0; S.meister = false; S.akt = null;
    if (sz.dinge && !S.zustand.tasche) S.zustand.tasche = [];
    $('wahl').hidden = true; $('spiel').hidden = false; $('ende').hidden = true; $('buehne').classList.remove('rueck');
    ['bBilder', 'bTipp', 'bNeu', 'hudSterne'].forEach(function (k) { $(k).hidden = false; });
    $('titel').textContent = $('titel2').textContent = (i + 1) + ' · ' + sz.titel;
    document.body.classList.add('imspiel');
    fx.innerHTML = '';
    male(S.zustand); passe(); sag(sz.ziel); hud();
  }

  function schluss() {
    var sz = S.sz, n = sterneJetzt(), alt = MERK.sterne[sz.id] || 0;
    if (n > alt) MERK.sterne[sz.id] = n;
    if (S.meister) MERK.meister[sz.id] = 1;
    sichern(); ton('fertig');
    for (var k = 0; k < n; k++) setTimeout(function () { ton('stern'); }, 500 + k * 250);
    var warum = S.tipp ? 'Mit Tipp gelöst – ohne Tipp gibt es mehr Sterne.'
      : S.fehler === 0 ? 'Ohne Fehlversuch und ohne Tipp!'
      : S.fehler <= 3 ? (S.fehler === 1 ? '1 Fehlversuch' : S.fehler + ' Fehlversuche') + ' – ohne gibt es 3 Sterne.'
      : S.fehler + ' Fehlversuche – mit höchstens 3 gibt es 2 Sterne.';
    var letzte = S.i === SZ.length - 1, zwei = (sz.wege || []).length > 1;
    $('ende').innerHTML = '<div class="k"><h2>' + ['Geschafft!', 'Geschafft!', 'Gut gemacht!', 'Natürlich!'][n] + '</h2><div class="gs" aria-label="' + n + ' von 3 Sternen">' + sterneHtml(n) + '</div>'
      + (S.meister ? '<p class="abz"><span class="krone">♛</span> Meister-Lösung</p>' : '')
      + (S.schluss ? '<p class="gesch">' + S.schluss.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</p>' : '')
      + '<p><b>' + warum + '</b></p>'
      + (alt > n ? '<p>Dein bestes Ergebnis hier bleibt: ' + alt + ' Sterne.</p>' : '')
      + '<p>' + (MERK.geheim[sz.id] ? 'Geheimnis in diesem Bild: gefunden ✓' : 'In diesem Bild ist noch ein Geheimnis versteckt.') + '</p>'
      + (zwei && !MERK.meister[sz.id] ? '<p>Dieses Bild hat noch eine zweite, elegantere Lösung.</p>' : '')
      + (letzte ? '<p>Das war das letzte Bild. Alle Sterne und Geheimnisse schon gefunden?</p>' : '')
      + '<div class="kn">' + (letzte ? '' : '<button type="button" class="haupt" id="eWeiter">Nächstes Bild</button>')
      + '<button type="button" id="eNochmal">Nochmal</button><button type="button"' + (letzte ? ' class="haupt"' : '') + ' id="eAlle">Alle Bilder</button></div></div>';
    $('ende').hidden = false; hud();
    if ($('eWeiter')) $('eWeiter').onclick = function () { starte(S.i + 1); };
    $('eNochmal').onclick = function () { starte(S.i); };
    $('eAlle').onclick = wahl;
  }

  function uhr() {                       // etwas ist mit der Zeit fertig geworden (Eis geschmolzen, Schiff angekommen …)
    var r = null; try { r = S.sz.uhr(S.zustand, zeit()); } catch (e) {}
    if (!r) return;
    var n = klon(S.zustand); if (r.setze) for (var f in r.setze) n[f] = r.setze[f];
    S.zustand = n; if (r.fehl) S.fehler++;
    ton(r.ton || (r.fehl ? 'fehl' : 'plopp')); male(n); if (r.text) sag(r.text); hud();
  }
  function schleife() {
    if (S.sz && !$('spiel').hidden) {
      var t = performance.now();
      if (S.sz.lauf) { try { S.sz.lauf(S.busy && S.akt ? S.akt : S.zustand, zeit(), q); } catch (e) {} }
      if (S.sz.uhr && !S.busy && !S.fertig && t - S.uhrT > 240) { S.uhrT = t; uhr(); }
    }
    requestAnimationFrame(schleife);
  }

  var api = window.WASNUN = {
    Z: Z, MIN: MIN,
    szene: function (d) { SZ.push(d); },
    los: function () {
      bild = $('bild'); fx = $('fx');
      laden(); tonKnopf(); wahl();
      $('karten').addEventListener('click', function (e) { var k = e.target.closest && e.target.closest('.karte'); if (!k) return; var i = +k.getAttribute('data-i'); if (offen(i)) starte(i); else { ton('fehl'); } });
      $('tasche').addEventListener('click', function (e) { var p = e.target.closest && e.target.closest('.platz[data-d]'); if (p) platzTipp(p.getAttribute('data-d')); });
      var runter = function (e) {
        if (e.button) return; e.preventDefault();
        var r = bild.getBoundingClientRect(); if (!r.width) return;
        tippe((e.clientX - r.left) / r.width * 800, (e.clientY - r.top) / r.height * 600);
      };
      if (window.PointerEvent) bild.addEventListener('pointerdown', runter);
      else { bild.addEventListener('mousedown', runter); bild.addEventListener('touchstart', function (e) { var t = e.changedTouches[0]; runter({ clientX: t.clientX, clientY: t.clientY, preventDefault: function () { e.preventDefault(); } }); }, { passive: false }); }
      $('bBilder').onclick = wahl;
      $('bNeu').onclick = function () { if (!S.busy && S.sz) starte(S.i); };
      $('bTipp').onclick = tippFrage;
      $('bTon').onclick = function () { MERK.stumm = !MERK.stumm; sichern(); tonKnopf(); if (!MERK.stumm) ton('ok'); };
      var wecken = function () { audio(); };            // iOS: Ton erst nach der ersten Berührung
      document.addEventListener('pointerdown', wecken, true); document.addEventListener('touchend', wecken, true); document.addEventListener('keydown', wecken, true);
      addEventListener('resize', passe); addEventListener('orientationchange', function () { setTimeout(passe, 250); });
      requestAnimationFrame(schleife);
      if (TEST) window.__wn = {
        S: S, SZ: SZ, MERK: MERK, MIN: MIN, frei: function () { return !S.busy; }, start: starte, wahl: wahl,
        // immer in der Form {stelle, ding, kombi, warte}; für alte Tests: next() gibt nur die Stelle
        naechster: function (weg) { return S.sz ? naechster(weg) : null; },
        next: function () { return S.sz ? (naechster().stelle || null) : null; },
        wege: function () { return S.sz.wege || ['']; },
        gut: function (id) { var ok = true; S.sz.stellen.forEach(function (st) { if (st.id === id && st.gut && (!st.wenn || st.wenn(S.zustand))) ok = st.gut(S.zustand, zeit()); }); return ok; },
        schlecht: function (id) { var x = false; S.sz.stellen.forEach(function (st) { if (st.id === id && st.schlecht) x = st.schlecht(S.zustand, zeit()); }); return x; },
        // Dinge in der Leiste mit Bildschirm-Platz, und welche Paare jetzt wirklich etwas ergeben
        plaetze: function () { var o = []; $('tasche').querySelectorAll('.platz[data-d]').forEach(function (e) { var r = e.getBoundingClientRect(); o.push({ id: e.getAttribute('data-d'), x: r.left + r.width / 2, y: r.top + r.height / 2, w: e.offsetWidth, h: e.offsetHeight, wahl: e.classList.contains('wahl') }); }); return o; },
        kombis: function () { var T = S.zustand.tasche || [], o = []; for (var i = 0; i < T.length; i++) for (var j = i + 1; j < T.length; j++) { var k = kombiFinde(T[i], T[j], S.zustand); o.push({ a: T[i], b: T[j], gibt: k && k.gibt ? k.gibt : null }); } return o; },
        // Punkt auf dem Bildschirm, an dem ein Tipp wirklich diese Stelle trifft, dazu ihre Grösse in Bildschirm-Pixeln
        stellen: function () {
          var b = bild.getBoundingClientRect(), k = b.width / 800, out = [];
          S.sz.stellen.forEach(function (st) {
            if (st.wenn && !st.wenn(S.zustand)) return; var r = rect(st, S.zustand), p = null;
            for (var j = 2; j >= 0 && !p; j--) for (var i = 0; i < 5 && !p; i++) {
              var x = r[0] + r[2] * [0.5, 0.3, 0.7, 0.15, 0.85][i], y = r[1] + r[3] * [0.3, 0.7, 0.5][j];
              if (finde(x, y, S.zustand) === st) p = [b.left + x * k, b.top + y * k];
            }
            out.push({ id: st.id, w: r[2] * k, h: r[3] * k, bw: r[2], bh: r[3], x: p ? p[0] : null, y: p ? p[1] : null, zeit: !!st.gut, mit: st.mit ? Object.keys(st.mit) : [], tipp: !!st.tipp });
          });
          return out;
        }
      };
    }
  };
})();
