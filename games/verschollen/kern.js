/* «Verschollen im Bergtal» – Kapitel 1. Eigenes Spiel für MoveEye (MIT), Geschichte und Idee: der Besitzer.

   kern.js = die Regeln, ohne Bildschirm: Zustand, Zeit, Feuer, Wetter, Bauen, Erkunden, Geschichte, Aufnahmen.
   Läuft im Browser (window.VB) und in node (module.exports) – so kann der Balance-Test ohne Browser rechnen.

   ZEIT: ein Tag = 300 Sekunden echte Spielzeit (K.DAY): Morgen 0–10 %, Tag bis 68 %, Abend bis 78 %, dann Nacht.
   Jeder Morgen verbraucht Essen und Wasser (du und die Hündin, dazu jede Person im Lager). Fehlt etwas, bist du an
   diesem Tag müde (alles dauert länger) – niemand kommt zu Schaden. Ein ausgegangenes Feuer macht kalte Finger
   (alles dauert doppelt so lang), bis es wieder brennt.
   GESCHICHTE: jede Reparatur und jeder neu entdeckte Ort lässt MoveEye eine Aufnahme wiederherstellen (CLIPS, 12
   Stücke). Die 13. ist die ganze Nacht des Felssturzes = Ende Kapitel 1.
   SPEICHERN: ui.js legt den Zustand unter «mw-verschollen-v1» ab ({v: VERSION, s: Zustand}); K.migriere() hebt ältere
   Fassungen an. Der Zustand enthält nur Zahlen, Texte, true/false, Listen und einfache Objekte.
   TEMPO (ab GS-1.20): S.tempo = 1, 2 oder 4 – ui.js lässt die Spieluhr so viel schneller laufen (K.step mit dt × tempo).
   Weil ALLES hier auf der Spieluhr läuft (Tag und Nacht, Feuer, Abklingzeiten, Ausflüge, Wetter, Erträge, MoveEye-Sprüche),
   bleibt die Balance gleich. S.echt = Spielzeit auf der Spieluhr, S.wirk = wirklich gespielte Sekunden.
   TEST: K.bot() spielt wie ein vernünftiger Mensch (mit Lese- und Denkzeit) und zählt die echte Spielzeit (S.echt). */
(function (G) {
  'use strict';
  var K = {};
  var HUND = 'Maggie';          // Name der Hündin (vom Besitzer) – hier ändern, gilt für das ganze Spiel (die Texte sagen «sie» / «ihr»)
  var VERSION = 1, DAY = 300, START_T = 246;
  K.HUND = HUND; K.VERSION = VERSION; K.DAY = DAY;
  K.TEMPI = [1, 2, 4];             // Spieltempo (ui.js): die Spieluhr läuft so viel schneller, alle Regeln bleiben gleich

  var NAME = { holz: 'Holz', wasser: 'Wasser', essen: 'Essen', draht: 'Draht', naegel: 'Nägel', schnur: 'Schnur', stoff: 'Stoff',
    seil: 'Seil', akku: 'Akku', panel: 'Solarpanel', wind: 'Windmesser', logger: 'Datenlogger' };
  var RES = ['holz', 'wasser', 'essen'], ITEMS = ['draht', 'naegel', 'schnur', 'stoff'];
  K.NAME = NAME; K.RES = RES; K.ITEMS = ITEMS;

  // ---- Zufall mit Startwert (gleicher Startwert = gleiches Wetter und gleiche Funde) ----
  function zufall(S) {
    var t = (S.seed = (S.seed + 0x6D2B79F5) | 0);
    t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  function wahl(S, l) { return l[Math.floor(zufall(S) * l.length) % l.length]; }

  // ---- Tageszeit ----
  function phase(S) { return (S.t % DAY) / DAY; }
  function zeit(S) { var p = phase(S); return p < 0.1 ? 'morgen' : p < 0.68 ? 'tag' : p < 0.78 ? 'abend' : 'nacht'; }
  function nacht(S) { return zeit(S) === 'nacht'; }
  function tagNr(S) { return Math.floor(S.t / DAY); }
  K.phase = phase; K.zeit = zeit; K.tagNr = tagNr;
  K.ZEITNAME = { morgen: 'Morgen', tag: 'Tag', abend: 'Abend', nacht: 'Nacht' };
  K.WETTER = { klar: 'klar', wolkig: 'bewölkt', regen: 'Regen', nebel: 'Nebel', sturm: 'Sturm' };

  K.neu = function (seed) {
    return {
      v: VERSION, t: START_T, echt: 0, seed: (seed || (Date.now() % 1000003) + 7) | 0,
      feuer: 0, fz: 0, r: { holz: 0, wasser: 0, essen: 0 }, it: { draht: 0, naegel: 0, schnur: 0, stoff: 0 },
      w: {}, bau: {}, f: {}, n: {}, orte: {}, station: 0, leute: { livia: 0, balz: 0 }, clips: [], log: [], karten: [],
      cd: {}, cdl: {}, wetter: 'sturm', muede: false, trip: null, ende: false, acc: {}, wahl: {}, meT: 0, meI: {}, logN: 0, tempo: 1, wirk: 0
    };
  };
  K.migriere = function (d) {               // ältere Spielstände anheben (heute gibt es nur Fassung 1)
    if (!d || typeof d !== 'object' || !d.s || typeof d.s !== 'object') return null;
    var s = d.s, n = K.neu(s.seed);
    for (var k in n) if (!(k in s)) s[k] = n[k];
    if (!Array.isArray(s.karten)) s.karten = [];
    s.v = VERSION;
    return s;
  };

  // ---- Tagebuch ----
  function log(S, k, s) { S.log.push({ k: k, s: s, t: Math.round(S.t), n: ++S.logN }); if (S.log.length > 80) S.log.splice(0, S.log.length - 80); }
  function me(S, s) { if (S.f.me) log(S, 'me', s); }
  function karte(S, c) { S.karten.push(c); }
  K.log = log;

  // ---- Lager-Grenzen und Kosten ----
  K.cap = function (S, r) {
    if (r === 'holz') return S.bau.schopf ? 80 : S.bau.dach ? 40 : 25;
    if (r === 'wasser') return S.bau.tonne ? 30 : 12;
    if (r === 'essen') return S.bau.gestell ? 30 : 15;
    return 99;
  };
  function hat(S, k) {
    for (var x in k) {
      if (RES.indexOf(x) >= 0) { if (S.r[x] < k[x]) return false; }
      else if (ITEMS.indexOf(x) >= 0) { if (S.it[x] < k[x]) return false; }
      else if (!S.w[x]) return false;
    }
    return true;
  }
  function zahle(S, k) {
    for (var x in k) {
      if (RES.indexOf(x) >= 0) S.r[x] -= k[x];
      else if (ITEMS.indexOf(x) >= 0) S.it[x] -= k[x];
    }
  }
  function gib(S, r, n) {
    if (RES.indexOf(r) >= 0) { var c = K.cap(S, r), v = Math.min(c, S.r[r] + n), g = v - S.r[r]; S.r[r] = Math.max(S.r[r], v); return g; }
    S.it[r] = (S.it[r] || 0) + n; return n;
  }
  K.kostenText = function (k) {
    var a = [];
    for (var x in k) a.push((typeof k[x] === 'number' ? k[x] + ' ' : '') + NAME[x]);
    return a.join(' · ');
  };
  K.fehlt = function (S, k) {
    var a = [];
    for (var x in k) {
      var have = RES.indexOf(x) >= 0 ? S.r[x] : ITEMS.indexOf(x) >= 0 ? S.it[x] : (S.w[x] ? 1 : 0), need = typeof k[x] === 'number' ? k[x] : 1;
      if (have < need) a.push(x);
    }
    return a;
  };

  // ---- Aufnahmen (12 Stücke + die ganze Nacht). zeit = wann sie aufgenommen wurde (vor dem Erwachen) ----
  var CLIPS = {
    c1: { titel: 'Anreise', zeit: 'Tag −4 · 07:42', z: ['Ein Postauto, beschlagene Scheiben, draussen ziehen Tannen vorbei.', 'Deine Stimme: «Tag eins. Unterwegs zur Wetterstation B-7.»', HUND + ' schläft auf deinen Füssen.'] },
    c2: { titel: 'Der Auftrag', zeit: 'Tag −5 · 21:10', z: ['Ein Küchentisch. Eine ausgedruckte Messkurve, rot umkreist.', 'Jemand neben der Kamera: «Das ist kein Messfehler. Schau es dir an. Bitte.»', 'Du nickst. Dann wird das Bild schwarz.'] },
    c3: { titel: 'Aufstieg', zeit: 'Tag −4 · 11:05', z: ['Ein Wegweiser: «Bergtal 3 h». Der Weg ist frei, die Sonne scheint.', HUND + ' trägt stolz einen Stock, der viel zu gross für sie ist.', 'Du filmst die Felswände: «Schön hier. Und so still.»'] },
    c4: { titel: 'Das Hüttenbuch', zeit: 'Tag −4 · 18:30', z: ['Das Hüttenbuch auf diesem Tisch. Du blätterst.', 'Der letzte Eintrag ist zwei Jahre alt. Darunter zwei frische Unterschriften.', 'Eine davon ist deine. Die andere ist verwischt.'] },
    c5: { titel: 'Eine zweite Hand', zeit: 'Tag −3 · 08:15', z: ['Werkzeug auf einer Bank: Zange, Draht, ein Messgerät.', 'Eine Hand reicht dir einen Schraubenzieher. Ein grüner Ärmel.', '«Danke», sagst du. Jemand lacht. Dann Rauschen.'] },
    c6: { titel: 'Das Blinken', zeit: 'Tag −3 · 19:48', z: ['Abend am See. Oben am Grat blinkt die Wetterstation: dreimal kurz, einmal lang.', 'Du, leise: «Die hat doch gar keinen Strom mehr.»', HUND + ' bellt den Grat an. Das tut sie sonst nie.'] },
    c7: { titel: 'Kerzenlicht', zeit: 'Tag −2 · 20:02', z: ['Die alte Kapelle. Drinnen brennen Kerzen.', 'Auf dem Altar liegt eine Karte des Tals, mit Bleistift ergänzt.', 'Eine Linie führt hinauf zum Grat. Daneben steht: «nur bei klarem Wetter».'] },
    c8: { titel: 'Der Windmesser', zeit: 'Tag −2 · 10:20', z: ['Am Wasserfall. Du hältst einen Windmesser in die Kamera.', '«Den hat der Sturm vom Mast geholt. Zweihundert Meter weit.»', 'Eine zweite Stimme: «Oder jemand hat ihn geholt.»'] },
    c9: { titel: 'Zwei Spuren', zeit: 'Tag −1 · 09:30', z: ['Du querst den Lawinenkegel, ein Seil läuft nach hinten.', 'Die Kamera schwenkt: zwei Paar Fussspuren im harten Schnee.', 'Das zweite Paar ist kleiner als deines.'] },
    c10: { titel: 'Am Mast', zeit: 'Tag −1 · 12:44', z: ['Die Station von nahe. Du klappst den Kasten auf.', 'Die Anzeige: 14,2 °C. Rundherum liegt Reif.', '«Unmöglich», sagst du. «Schreib die Uhrzeit auf.»'] },
    c11: { titel: 'Wetterleuchten', zeit: 'Tag −1 · 17:58', z: ['Wolken quellen über den Grat. Zwei Stirnlampen am Hang.', 'Du rufst: «Runter, sofort! Das wird ein Sturm.»', 'Donner. Das Bild wackelt, dann läufst du.'] },
    c12: { titel: 'Grollen', zeit: 'Tag 0 · 02:09', z: ['Die Hütte im Dunkeln. Ein tiefes Grollen, wie ein Zug im Berg.', 'Jemand zieht dich unter das Vordach. ' + HUND + ' bellt.', 'Steine prasseln. Dann ist es still.'] },
    c13: { titel: 'Der Lageplan', zeit: 'Tag −2 · 15:30', z: ['Im Stollen filmst du einen Lageplan an der Wand.', 'Eine Linie ist neu eingezeichnet, mit rotem Stift: vom Stollen bis unter den alten Weg.', 'Deine Stimme: «Wer gräbt denn heute noch hier?» Keine Antwort, nur Tropfen.'] },
    ganz: { titel: 'Die ganze Nacht', zeit: 'Tag 0 · 02:07–02:11', z: ['Zum ersten Mal läuft die Aufnahme ohne Lücke.', 'Die Nacht des Felssturzes. Du stehst vor der Hütte, ' + HUND + ' an deinem Bein.', 'Neben dir steht jemand. Kapuze, Stirnlampe – das Licht blendet die Kamera.', 'Die Person sagt: «Sie dürfen die Daten nicht finden. Noch nicht.»', 'Dann kommt der Hang. Die Person zieht dich in Sicherheit. Das Gesicht bleibt im Licht verborgen.'] }
  };
  K.CLIPS = CLIPS;
  function clip(S, id) {
    if (S.clips.indexOf(id) >= 0) return;
    S.clips.push(id);
    karte(S, { art: 'clip', id: id, nr: S.clips.length });
    log(S, 'n', 'MoveEye stellt eine Aufnahme wieder her: «' + CLIPS[id].titel + '».');
  }
  K.stufe = function (S) { var n = S.clips.length; return n <= 2 ? 0 : n <= 5 ? 1 : n <= 9 ? 2 : 3; };

  // ---- MoveEye: Sprüche je Vertrautheit (Stufe 0 knapp … Stufe 3 mit Meinung) ----
  var ME_IDLE = [
    ['Speicher zu 3 % lesbar. Der Rest ist Rauschen. Wie bei dir, schätze ich.', 'Ich bin eine Kamera. Ich friere nicht. Trotzdem: Mach das Feuer gross.',
      'Hinweis: Deine Hündin schaut seit zehn Minuten in meine Linse.', 'Akku voll. Erinnerung leer. Ich nehme es sportlich.'],
    ['Jede Reparatur rüttelt etwas in meinem Speicher frei. Seltsam – aber ich beschwere mich nicht.', 'Du hast heute viel Holz geschleppt. Applaus. Leise, ich bin nur eine Kamera.',
      'Wenn du mich hinlegst, bitte mit der Linse nach oben. Ich mag den Himmel.', 'Ich habe ein Bild von dir mit Bart gefunden. Kleiner Scherz. Oder?'],
    ['Weisst du, was ich vermisse? Ich weiss es auch nicht. Das ist ja das Problem.', HUND + ' hat mich angestupst. Ich glaube, wir sind jetzt Freunde.',
      'Ich habe die Aufnahmen sortiert. Du sagst sehr oft «Schau mal». Ich schaue ja.', 'Die Station blinkt in meinen Aufnahmen immer gleich: dreimal kurz, einmal lang. Merk dir das.'],
    ['Meine Meinung zur Station: hinauf, reparieren und dann ganz genau hinschauen.', 'Früher hätte ich nur «Speicher voll» gesagt. Jetzt sage ich: Danke, dass du mich mitnimmst.',
      'Was auch immer auf der Station ist – wir finden es zusammen heraus. Du, ich und ' + HUND + '.', 'Ich habe beschlossen, dass ich Nebel nicht mag. Man sieht nichts. Als Kamera nehme ich das persönlich.']
  ];
  function meIdle(S) {
    var st = K.stufe(S), l = ME_IDLE[st], i = S.meI[st] || 0;
    S.meI[st] = i + 1;
    me(S, l[i % l.length]);
  }

  // ---- Wetter ----
  var WT = { klar: 'Klarer Himmel über den Felsen.', wolkig: 'Wolken hängen an den Gipfeln.', regen: 'Es regnet. Die Felsen glänzen nass.',
    nebel: 'Nebel liegt im Tal. Man sieht kaum zum See.', sturm: 'Sturm! Der Wind heult um die Hütte.' };
  function wetterWechsel(S) {
    var n = S.n.wetterN = (S.n.wetterN || 0) + 1, w;
    if (n === 1) w = 'nebel'; else if (n === 2) w = 'wolkig';
    else {
      var g = { klar: 32, wolkig: 30, regen: 16, nebel: 14, sturm: S.wetter === 'sturm' || n < 6 ? 0 : 8 }, sum = 0, x;
      for (x in g) sum += g[x];
      var r = zufall(S) * sum;
      for (x in g) { r -= g[x]; if (r < 0) { w = x; break; } }
      w = w || 'klar';
    }
    if (w === S.wetter) return;
    S.wetter = w;
    log(S, 'w', WT[w]);
    if (w === 'sturm') me(S, wahl(S, ['Sturm. Ich schlage vor: drinnen bleiben, Feuer füttern, ' + HUND + ' kraulen.', 'Bei dem Wind fliegt sogar meine Laune weg. Bleib in der Nähe der Hütte.']));
    if (w === 'nebel' && S.f.karte) me(S, 'Nebel. Wer jetzt losgeht, braucht länger. ' + HUND + ' findet zum Glück immer heim.');
  }

  // ---- Tageswechsel ----
  function leuteN(S) { return (S.leute.livia === 2 ? 1 : 0) + (S.leute.balz === 2 ? 1 : 0); }
  K.bedarf = function (S) { var p = leuteN(S); return { essen: 2 + p, wasser: 2 + p }; };
  function morgen(S) {
    var tg = tagNr(S);
    log(S, 'w', 'Tag ' + tg + ' bricht an.');
    wetterWechsel(S);
    if (S.f.draussen) {
      var b = K.bedarf(S), ok = S.r.essen >= b.essen && S.r.wasser >= b.wasser;
      S.r.essen = Math.max(0, S.r.essen - b.essen); S.r.wasser = Math.max(0, S.r.wasser - b.wasser);
      var war = S.muede; S.muede = !ok;
      if (ok) log(S, 'n', 'Frühstück: ' + b.essen + ' Essen und ' + b.wasser + ' Wasser' + (leuteN(S) ? ' für alle.' : ' für dich und ' + HUND + '.'));
      else { log(S, 'n', 'Zu wenig zu essen oder zu trinken. Du bist heute müde – alles geht langsamer.'); if (!war) me(S, 'Kleiner Tipp aus der Kameraperspektive: Ein Vorrat an Essen und Wasser macht morgens bessere Laune.'); }
    }
    if (S.bau.unterstand && S.f.balzTraf && S.leute.balz < 2) balzKommt(S);
  }
  function abend(S) {
    if (S.f.draussen) log(S, 'w', 'Die Sonne sinkt hinter die Felsen.');
    if (S.f.draussen && !S.w.laterne && !S.n.abendTipp) { S.n.abendTipp = 1; me(S, 'Bald ist es dunkel. Ohne Licht kannst du nachts nur ruhen und das Feuer hüten.'); }
  }
  function nachtBeginn(S) {
    if (S.f.draussen) log(S, 'w', 'Nacht. Über den Felsen funkeln ' + (S.wetter === 'klar' ? 'unzählige Sterne.' : 'ein paar Sterne zwischen den Wolken.'));
    if (S.f.signal && S.leute.livia === 0) S.f.liviaT = Math.max(S.f.liviaT || 0, S.t + 20);
  }

  // ---- Feuer ----
  function feuerStep(S, dt) {
    if (S.feuer <= 0) return;
    var iv = 32 * (S.f.draussen ? 1 : 2) * (S.bau.ofentuer ? 1.7 : 1) * (nacht(S) ? 0.8 : 1) * (S.wetter === 'sturm' ? 0.7 : 1);
    S.fz += dt;
    while (S.fz >= iv && S.feuer > 0) {
      S.fz -= iv;
      if (S.leute.livia === 2 && S.feuer <= 2 && S.r.holz >= 1) { S.r.holz--; S.n.liviaFeuer = (S.n.liviaFeuer || 0) + 1; continue; }   // Livia legt nach
      S.feuer--;
      if (S.feuer === 1) log(S, 'n', 'Das Feuer wird klein.');
      if (S.feuer === 0) {
        log(S, 'n', 'Das Feuer ist aus. Die Kälte kriecht herein.');
        var st = K.stufe(S);
        me(S, ['Feuer aus. Temperatur sinkt. Das ist kein Vorwurf, nur eine Messung.', 'Ich bin ja nur eine Kamera, aber: kalt.', 'Ehrlich, ' + HUND + ' und ich hätten gern wieder Feuer.', 'Ich sage es freundlich: Holz. Ofen. Jetzt.'][st]);
      }
    }
  }
  K.mult = function (S) { return (S.feuer <= 0 && S.f.feuerAn ? 2 : S.feuer === 1 ? 1.3 : 1) * (S.muede ? 1.4 : 1); };

  // ---- Passive Erträge ----
  function acc(S, k, dt, iv, fn) { S.acc[k] = (S.acc[k] || 0) + dt; while (S.acc[k] >= iv) { S.acc[k] -= iv; fn(); } }
  function passiv(S, dt) {
    if (S.bau.tonne) acc(S, 'tonne', dt, S.wetter === 'regen' || S.wetter === 'sturm' ? 15 : 80, function () { gib(S, 'wasser', 1); });
    if (S.leute.livia === 2 && !nacht(S)) acc(S, 'livia', dt, 40, function () { gib(S, 'holz', 1); });
    if (S.leute.balz === 2 && !nacht(S)) acc(S, 'balz', dt, 40, function () { gib(S, 'essen', 1); });
  }

  // ---- Personen ----
  function liviaKommt(S) {
    S.leute.livia = 1; S.f.liviaT = 0;
    karte(S, { art: 'wahl', id: 'livia', bild: 'livia', titel: 'Licht am Hang',
      z: ['Gegen Mitternacht springt ' + HUND + ' auf und bellt. Eine Stirnlampe schwankt den Hang herunter.',
        'Eine junge Frau in grüner Jacke humpelt ins Licht. «Ich habe dein Feuer gesehen», keucht sie. «Ich bin Livia. Mein Knöchel …»',
        'Dann stockt sie und starrt dich an. «Du? Du bist doch … – nein. Vergiss es.»'] });
  }
  function balzKommt(S) {
    S.leute.balz = 2; S.w.logger = true; gib(S, 'essen', 6);
    karte(S, { art: 'bild', bild: 'balz', titel: 'Balz zieht ein',
      z: ['Am Morgen steht Balz vor der Hütte, einen Sack über der Schulter. «Ein Dach für einen alten Mann. Gut gemacht.»',
        'Im Sack: ein Laib Käse – und ein grauer Kasten mit Kabeln.',
        '«Der Datenlogger der Station», sagt Balz. «Ich habe ihn geholt, bevor der Hang kam.» Woher wusste er, dass der Hang kommt?'] });
    log(S, 'p', 'Balz: «Ab jetzt gibt es Käse. Und keine dummen Fragen vor dem Frühstück.»');
  }
  var WAHL = {
    livia: [
      { t: 'Ehrlich sein: «Ich weiss nichts mehr. Kennst du mich?»', fn: function (S) {
        S.wahl.livia = 'ehrlich';
        log(S, 'p', 'Livia: «Wir sind uns … einmal begegnet. Unten im Dorf. Glaube ich.» Sie schaut weg.');
        me(S, 'Sie lügt schlecht. Ich mag sie trotzdem.');
      } },
      { t: 'Ausweichen: «Setz dich erst mal ans Feuer.»', fn: function (S) {
        S.wahl.livia = 'still';
        log(S, 'p', 'Livia: «Danke.» Sie setzt sich und lässt dich nicht aus den Augen.');
        me(S, 'Ehrlich wäre auch gegangen. Nur so – als Kamera gesagt.');
      } }
    ],
    balz: [
      { t: 'Ja – Balz die Aufnahmen zeigen', fn: function (S) {
        S.wahl.balz = 'gezeigt';
        log(S, 'p', 'Balz schaut lange auf den kleinen Bildschirm. «Das bist du, ja. Und das Tal.» Bei der Station wird er still.');
        me(S, 'Man hätte mich fragen können. Aber gut: Er hat warme Hände.');
      } },
      { t: 'Nein – noch nicht', fn: function (S) {
        S.wahl.balz = 'nein';
        log(S, 'p', 'Balz: «Recht so. Man zeigt nicht jedem alles.»');
        me(S, 'Danke. Ich bin wählerisch, wem ich mich zeige.');
      } }
    ],
    daten: [
      { t: 'Livia die Daten zuerst zeigen', fn: function (S) {
        S.wahl.daten = 'livia';
        log(S, 'p', 'Livia wird blass. «Drei Tage», flüstert sie. «Dann haben wir drei Tage.»');
        me(S, 'Du hast es versprochen und gehalten. Das gefällt mir. Ihr Gesicht weniger.');
        ende(S);
      } },
      { t: 'Erst selbst verstehen, dann erzählen', fn: function (S) {
        S.wahl.daten = 'selbst';
        log(S, 'p', 'Livia sieht dir nach, als du mit MoveEye allein ans Fenster gehst. Sie sagt nichts.');
        me(S, 'Erst verstehen, dann erzählen. Das hätte ich auch gesagt. Ab jetzt behaupte ich, dass ich es gesagt habe.');
        ende(S);
      } }
    ]
  };
  K.WAHL = WAHL;
  K.wahlTexte = function (id) { return (WAHL[id] || []).map(function (o) { return o.t; }); };

  var LIVIA = [
    { s: '«Ich war unterwegs zum Grat, als der Sturm kam. Dann kam der Hang. Seither sitze ich hier fest – wie du.»' },
    { s: '«Das Seil? Behalt es. Mit dem Knöchel klettere ich eine Weile nirgendwohin.»' },
    { s: '«' + HUND + ' mag dich», sagt Livia. «Das war schon immer so.» Dann beisst sie sich auf die Lippe.' },
    { wenn: function (S) { return S.w.wind || S.station >= 2; }, s: '«Ein Windmesser im Becken? Den hat nicht der Wind dorthin getragen.» Mehr sagt sie nicht.' },
    { wenn: function (S) { return S.f.balzTraf; }, s: '«Balz? Der alte Senn? Der redet nur, wenn er will. Aber er weiss mehr über den Hang als alle anderen.»' },
    { wenn: function (S) { return S.station >= 1; }, s: '«Wenn die Station wieder misst … versprich mir, dass du mir zuerst zeigst, was drauf ist.»' },
    { wenn: function (S) { return S.station >= 3; }, s: '«Deine Kamera hast du schon im Dorf ständig laufen lassen.» Sie lächelt, zum ersten Mal.' }
  ];
  var LIVIA_RUHE = ['Livia schnitzt einen Stock für ihren Knöchel.', 'Livia hält die Hände ans Feuer und summt ein Lied, das du kennst. Woher?', 'Livia schaut zum Grat hinauf. «Bald», sagt sie leise.'];
  var BALZ = [
    { s: '«Siebzig Winter habe ich hier oben gesehen. Der hier kommt früh.»' },
    { s: '«Die Station hat schon einmal so seltsame Zahlen gemeldet. Vor vierzig Jahren. Damals kam auch der Hang.»' },
    { s: '«Warum der Weg zu ist? Weil der Berg es wollte – oder jemand. Frag mich, wenn sie wieder misst.»' },
    { wenn: function (S) { return S.leute.livia === 2; }, s: '«Die Livia … nein, ich sage nichts. Ist nicht meine Geschichte.»' },
    { wenn: function (S) { return S.station >= 4; }, s: '«Wenn du sie neu startest, dann bei klarem Wetter. Sonst misst sie nur Wolken.»' }
  ];
  var BALZ_RUHE = ['Balz schneidet Käse für alle. ' + HUND + ' sitzt sehr, sehr brav daneben.', 'Balz schaut lange zum Grat. Dann stopft er seine Pfeife, ohne sie anzuzünden.', '«Holz hacken wärmt zweimal», brummt Balz.'];
  K.neueRede = function (S, wer) {
    var L = wer === 'livia' ? LIVIA : BALZ, i = S.n['rede_' + wer] || 0;
    return i < L.length && (!L[i].wenn || L[i].wenn(S));
  };
  function rede(S, wer, L, R) {
    var k = 'rede_' + wer, i = S.n[k] || 0;
    for (var j = i; j < L.length; j++) {
      if (!L[j].wenn || L[j].wenn(S)) {
        if (j === i) { S.n[k] = i + 1; log(S, 'p', (wer === 'livia' ? 'Livia: ' : 'Balz: ') + L[j].s); return; }
        break;
      }
    }
    S.n[k + 'R'] = (S.n[k + 'R'] || 0) + 1;
    log(S, 'p', R[S.n[k + 'R'] % R.length]);
  }

  // ---- Fundstücke des Hundes: meistens das, was gerade fehlt ----
  function bedarfItems(S) {
    var need = {}, ziel = {}, z = K.ziel(S), i, x;
    for (i = 0; i < ITEMS.length; i++) need[ITEMS[i]] = 0;
    var L = K.liste(S, true);
    for (i = 0; i < L.length; i++) {
      var e = L[i]; if (!e.kosten || (e.art !== 'bau' && e.id !== 'ort_station')) continue;
      for (x in e.kosten) if (x in need) { need[x] += e.kosten[x]; if (z && z.id === e.id) ziel[x] = 1; }
    }
    var best = null, bw = 0;
    for (x in need) { var f = need[x] - S.it[x]; if (f > 0 && f + (ziel[x] ? 100 : 0) > bw) { bw = f + (ziel[x] ? 100 : 0); best = x; } }
    return best;
  }
  var HUND_SPASS = ['einen alten Schuh. Sie ist sehr stolz darauf.', 'einen Tannzapfen. Den schönsten im ganzen Tal, findet sie.', 'einen Stock. Einen sehr, sehr langen Stock.', 'nichts – aber sie hat sich im Moos gewälzt und ist glücklich.'];
  function hundSucht(S) {
    var n = S.n.hund = (S.n.hund || 0) + 1, it = bedarfItems(S);
    if (n === 1) it = 'draht';
    var r = zufall(S);
    if (it && (r < 0.72 || n <= 2)) {
      gib(S, it, 1);
      log(S, 'n', HUND + ' kommt zurück und legt dir ' + { draht: 'eine Rolle rostigen Draht', naegel: 'eine Handvoll alter Nägel', schnur: 'ein Stück Schnur', stoff: 'einen Fetzen festen Stoff' }[it] + ' vor die Füsse. (+1 ' + NAME[it] + ')');
      if (n === 1) me(S, 'Deine Hündin ist besser organisiert als du. Nichts für ungut.');
    } else if (r < 0.9) {
      var g = gib(S, 'essen', 2);
      log(S, 'n', HUND + ' führt dich zu einem Busch voller Hagebutten. (+' + g + ' Essen)');
    } else log(S, 'n', HUND + ' bringt ' + wahl(S, HUND_SPASS));
  }

  // ---- Ruhen bis zum Morgen ----
  function ruhen(S) {
    if (S.f.signal && S.leute.livia === 0) {          // the signal burns: you doze by the fire until someone comes
      var w = Math.max(0, (S.f.liviaT || S.t + 20) - S.t);
      S.t += w; S.fz = 0; for (var y in S.cd) S.cd[y] = Math.min(S.cd[y], S.t);
      log(S, 'n', 'Du döst am Feuer ein. Das Signal brennt draussen weiter.');
      tick(S, 0.02); return;
    }
    var dt = DAY - (S.t % DAY), k = Math.min(S.r.holz, Math.ceil(dt / 30));
    S.r.holz -= k;
    var f0 = S.feuer;
    S.t += dt - 0.01; S.fz = 0;
    S.feuer = k >= 2 ? Math.max(1, Math.min(2, f0)) : 0;
    for (var x in S.cd) S.cd[x] = Math.min(S.cd[x], S.t);
    tick(S, 0.02);
    log(S, 'n', k >= 2 ? 'Du schläfst neben dem Ofen. ' + HUND + ' wärmt dir den Rücken. (−' + k + ' Holz)' : 'Ohne Holz wird die Nacht bitterkalt. Du schläfst kaum.');
    if (k < 2) S.muede = true;
    S.n.ruhen = (S.n.ruhen || 0) + 1;
    if (S.n.ruhen === 2) me(S, 'Du schnarchst übrigens. Ich habe es nicht aufgenommen. Diesmal.');
  }

  // ---- Bauen und Werkbank ----
  var BAU = [
    { id: 'ofentuer', tab: 'huette', gr: 'Hütte reparieren', name: 'Ofentür richten', k: { holz: 5, draht: 1 }, info: 'Die Tür hängt schief, das Feuer frisst Holz.',
      sicht: function (S) { return S.f.draussen; }, fertig: 'Die Ofentür schliesst wieder. Das Feuer brennt ruhiger und länger.', clip: 'c2' },
    { id: 'dach', tab: 'huette', gr: 'Hütte reparieren', name: 'Dach flicken', k: { holz: 25, naegel: 4 }, info: 'Durchs Dach tropft es auf die Pritsche.',
      sicht: function (S) { return S.bau.ofentuer; }, fertig: 'Das Loch im Dach ist zu. Drinnen bleibt es trocken, und mehr Holz hat Platz.', clip: 'c3' },
    { id: 'fenster', tab: 'huette', gr: 'Hütte reparieren', name: 'Fenster abdichten', k: { holz: 10, stoff: 1 }, info: 'Der Wind pfeift durch die zerbrochene Scheibe.',
      sicht: function (S) { return S.bau.dach; }, fertig: 'Bretter und Stoff halten den Wind draussen. Durchs Fenster sieht man den Grat.', clip: 'c4' },
    { id: 'schopf', tab: 'lager', gr: 'Lager bauen', name: 'Holzschopf', k: { holz: 26 }, info: 'Trockenes Holz, viel mehr Platz, mehr Holz pro Gang.',
      sicht: function (S) { return S.bau.dach; }, fertig: 'Der Holzschopf steht. Hier bleibt Holz trocken.' },
    { id: 'tonne', tab: 'lager', gr: 'Lager bauen', name: 'Regentonne', k: { holz: 15, naegel: 1 }, info: 'Sammelt Wasser, besonders bei Regen.',
      sicht: function (S) { return S.bau.dach; }, fertig: 'Die Regentonne steht unter der Dachrinne.' },
    { id: 'werkbank', tab: 'lager', gr: 'Lager bauen', name: 'Werkbank', k: { holz: 32, naegel: 4 }, info: 'Damit baust du Werkzeug.',
      sicht: function (S) { return S.bau.dach; }, fertig: 'Eine stabile Werkbank. Zeit für Werkzeug.', clip: 'c5' },
    { id: 'gestell', tab: 'lager', gr: 'Lager bauen', name: 'Trockengestell', k: { holz: 18, schnur: 1 }, info: 'Dörrt Beeren und Fisch: mehr Essen pro Gang, mehr Vorrat.',
      sicht: function (S) { return S.bau.werkbank; }, fertig: 'Das Trockengestell steht im Wind.' },
    { id: 'signal', tab: 'lager', gr: 'Lager bauen', name: 'Signalfeuer aufschichten', k: { holz: 25 }, info: 'Ein grosses Feuer, das man nachts im ganzen Tal sieht.',
      sicht: function (S) { return S.w.laterne && S.f.spuren && S.leute.livia === 0; }, fertig: 'Der Holzstoss für das Signalfeuer ist bereit.' },
    { id: 'unterstand', tab: 'lager', gr: 'Lager bauen', name: 'Unterstand für Balz', k: { holz: 30, stoff: 3 }, info: 'Balz kommt herunter, wenn er ein Dach hat.',
      sicht: function (S) { return S.f.balzTraf; }, fertig: 'Ein Unterstand mit Bank und Plane. Balz kommt am nächsten Morgen.' },
    { id: 'axt', tab: 'lager', gr: 'Werkbank', name: 'Axt schärfen', k: { holz: 6, draht: 1 }, info: '+2 Holz pro Gang.', werk: 1,
      sicht: function (S) { return S.bau.werkbank; }, fertig: 'Die alte Axt ist wieder scharf.' },
    { id: 'eimer', tab: 'lager', gr: 'Werkbank', name: 'Eimer bauen', k: { holz: 8, draht: 1 }, info: 'Doppelt so viel Wasser pro Gang.', werk: 1,
      sicht: function (S) { return S.bau.werkbank; }, fertig: 'Ein Holzeimer mit Drahtbügel. Dicht!' },
    { id: 'laterne', tab: 'lager', gr: 'Werkbank', name: 'Laterne bauen', k: { holz: 5, draht: 1, stoff: 1 }, info: 'Licht für die Nacht: draussen arbeiten, nachts gehen.', werk: 1,
      sicht: function (S) { return S.bau.werkbank; }, fertig: 'Eine Laterne mit Docht aus Stoff. Die Nacht ist nicht mehr ganz so schwarz.' },
    { id: 'angel', tab: 'lager', gr: 'Werkbank', name: 'Angel bauen', k: { holz: 4, schnur: 1 }, info: 'Fischen am See.', werk: 1,
      sicht: function (S) { return S.bau.werkbank && S.orte.see; }, fertig: 'Eine einfache Angel. Der See wartet.' },
    { id: 'steigeisen', tab: 'lager', gr: 'Werkbank', name: 'Steigeisen schmieden', k: { holz: 8, draht: 2, naegel: 3 }, info: 'Für den harten Schnee des Lawinenkegels.', werk: 1,
      sicht: function (S) { return S.bau.werkbank && S.f.balzTraf; }, fertig: 'Grobe Steigeisen aus Nägeln und Draht. Sie beissen ins Eis.' }
  ];
  K.BAU = BAU;
  function gebaut(S, b) {
    if (b.werk) S.w[b.id] = true; else S.bau[b.id] = true;
    log(S, 'n', b.fertig);
    if (b.id === 'dach' && !S.f.karte) { S.f.karte = true; me(S, 'Beim Hämmern ist mir etwas aufgetaucht: eine Karte des Tals. Schau unter «Tal».'); }
    if (b.id === 'ofentuer') me(S, 'Siehst du? Reparatur – Erinnerung. Ich verstehe es auch nicht, aber es funktioniert.');
    if (b.id === 'werkbank') me(S, 'Eine Werkbank! Ich bin begeistert. Innerlich. Äusserlich bin ich eine Kamera.');
    if (b.id === 'laterne' && !S.f.spuren) me(S, 'Mit Licht sieht man uns nachts von weit her. Nur so ein Gedanke.');
    if (b.id === 'laterne' && S.f.spuren) me(S, 'Mit Licht und einem grossen Feuer sieht man uns im ganzen Tal. Die Spuren am See …?');
    if (b.clip) clip(S, b.clip);
  }

  // ---- Orte im Tal ----
  var ORTE = {
    geroell: { name: 'Verschütteter Weg', x: 18, y: 84, dauer: 35, k: {}, info: 'Wo der Weg ins Dorf war, liegt jetzt ein Berg aus Fels.' },
    see: { name: 'Seeufer', x: 66, y: 62, dauer: 55, k: { essen: 2, wasser: 1 }, info: 'Schwarzes, stilles Wasser unter den Felsen.' },
    wasserfall: { name: 'Wasserfall', x: 87, y: 36, dauer: 60, k: { essen: 2, wasser: 2 }, info: 'Er donnert über eine Felsstufe in ein tiefes Becken.' },
    kapelle: { name: 'Alte Kapelle', x: 28, y: 46, dauer: 75, k: { essen: 3, wasser: 2 }, info: 'Ein weisses Kirchlein zwischen Lärchen.' },
    stollen: { name: 'Alter Stollen', x: 10, y: 26, dauer: 70, k: { essen: 2, wasser: 2 }, info: 'Ein verrammelter Eingang in der Felswand.' },
    lawine: { name: 'Lawinenkegel', x: 47, y: 28, dauer: 85, k: { essen: 3, wasser: 3 }, info: 'Harter Altschnee unter der Rinne zum Grat.' },
    station: { name: 'Wetterstation', x: 68, y: 10, dauer: 85, k: { essen: 3, wasser: 3 }, info: 'Station B-7 auf dem Grat.' }
  };
  K.ORTE = ORTE;
  var ST_SCHRITT = [
    { name: 'Mast aufrichten', k: { holz: 20, seil: true } },
    { name: 'Solarpanel und Windmesser montieren', k: { draht: 2, panel: true, wind: true } },
    { name: 'Akku einsetzen', k: { akku: true } },
    { name: 'Datenlogger anschliessen', k: { logger: true } },
    { name: 'Station neu starten', k: {} }
  ];
  K.ST_SCHRITT = ST_SCHRITT;
  function ortSicht(S, id) {
    if (!S.f.karte) return false;
    if (id === 'geroell' || id === 'see') return true;
    if (id === 'wasserfall' || id === 'kapelle') return !!S.orte.see;
    if (id === 'lawine') return !!S.f.balzTraf;
    if (id === 'station') return !!S.orte.lawine;
    if (id === 'stollen') return !!S.f.balzTraf;
    return false;
  }
  function ortKosten(S, id) {
    var k = {}, o = ORTE[id], x;
    for (x in o.k) k[x] = o.k[x];
    if (id === 'station' && S.station < 5) { var st = ST_SCHRITT[S.station].k; for (x in st) k[x] = st[x]; }
    return k;
  }
  function ortSperre(S, id) {
    if (S.wetter === 'sturm') return 'Im Sturm bleibst du besser bei der Hütte.';
    if (nacht(S) && !S.w.laterne) return 'Ohne Licht verirrst du dich in der Nacht.';
    if (id === 'stollen' && !S.w.laterne) return 'Im Stollen ist es stockdunkel. Ohne Laterne geht das nicht.';
    if (id === 'lawine' && !S.w.steigeisen) return 'Ohne Steigeisen rutschst du auf dem harten Schnee ab.';
    if ((id === 'lawine' || id === 'station') && S.wetter === 'regen') return 'Bei Regen kommen Steine aus der Rinne. Warte auf trockenes Wetter.';
    if (id === 'station') {
      if (S.station >= 5) return 'Die Station misst. Hier gibt es nichts mehr zu tun.';
      if (S.station === 1 && !(S.w.panel && S.w.wind)) return S.w.panel ? 'Es fehlt noch der Windmesser.' : 'Es fehlt noch das Solarpanel.';
      if (S.station === 2 && !S.w.akku) return 'Ohne Akku läuft die Station nachts nicht. Wo gäbe es einen?';
      if (S.station === 3 && !S.w.logger) return 'Es fehlt der Datenlogger. Wer hat ihn wohl?';
      if (S.station === 0 && !S.w.seil) return 'Den schweren Mast richtest du nur mit einem Seil auf.';
      if (S.station === 4 && (nacht(S) || (S.wetter !== 'klar' && S.wetter !== 'wolkig'))) return 'Neu starten nur bei Tag und trockenem Wetter – sonst misst sie nur Wolken.';
    }
    return '';
  }
  function ortDauer(S, id) { return Math.round(ORTE[id].dauer * (nacht(S) ? 1.5 : 1) * (S.wetter === 'nebel' ? 1.4 : 1)); }
  function aufbrechen(S, id) {
    S.trip = { ort: id, ab: S.t, bis: S.t + ortDauer(S, id) };
    log(S, 'n', 'Du brichst auf: ' + ORTE[id].name + '. ' + HUND + ' läuft voraus.');
  }
  function ortKarte(S, id, titel, z, extra) { karte(S, { art: 'bild', bild: 'ort:' + id, titel: titel, z: z }); if (extra) extra(); }
  function besuch(S, id) {
    var n = S.orte[id] = (S.orte[id] || 0) + 1, g;
    if (id === 'geroell') {
      if (n === 1) {
        gib(S, 'naegel', 2); gib(S, 'stoff', 1);
        ortKarte(S, id, 'Der verschüttete Weg', ['Ein Hang aus Fels und Erde, hoch wie ein Haus. Darunter liegt irgendwo der Weg ins Dorf.',
          'Aus dem Geröll ragt ein Wegweiser: «Bergtal 3 h». Daneben ein zersplitterter Zaun.',
          HUND + ' schnüffelt an einem Handschuh zwischen den Steinen. Er ist zu klein für deine Hand.', 'Du nimmst Nägel aus dem Zaun und den Handschuh mit. (+2 Nägel, +1 Stoff)']);
        me(S, 'Kein Durchkommen. Wir sind eine Insel. Eine Insel mit Hündin – immerhin.');
      } else { g = gib(S, 'holz', 5); log(S, 'n', 'Am Geröll sammelst du gesplittertes Zaunholz. (+' + g + ' Holz) Der Berg schweigt.'); }
    } else if (id === 'see') {
      if (n === 1) {
        gib(S, 'schnur', 1); S.f.spuren = true;
        ortKarte(S, id, 'Am Seeufer', ['Der See ist dunkel und still. Am Ufer eine Feuerstelle, kalt, ein paar Tage alt.',
          'Fussspuren führen zum Wasserfall. Hier war jemand – und vielleicht ist er noch im Tal.', 'Im Schilf hängt eine Angelschnur. (+1 Schnur)']);
        clip(S, 'c6');
        me(S, 'Wenn hier noch jemand ist, sieht er uns nachts nur, wenn wir Licht machen. Viel Licht.');
      } else { g = gib(S, 'wasser', 6); log(S, 'n', 'Du füllst am See Wasser ab und schaust zum Grat hinauf. (+' + g + ' Wasser)'); }
    } else if (id === 'wasserfall') {
      if (n === 1 && !S.w.seil) {
        gib(S, 'stoff', 1); S.f.glanz = true;
        ortKarte(S, id, 'Am Wasserfall', ['Der Wasserfall donnert in ein tiefes Becken. Gischt glitzert in der Luft.',
          'Unten im Becken glänzt etwas Metallisches. Ohne Seil kommst du nicht hinunter.', 'Am Felsen flattert eine verlorene Mütze. (+1 Stoff)']);
      } else if (S.w.seil && !S.w.wind && S.station < 2) {
        S.w.wind = true;
        ortKarte(S, id, 'Hinunter ins Becken', ['Mit Livias Seil kletterst du die nasse Felsstufe hinunter. ' + HUND + ' bellt aufgeregt vom Rand.',
          'Im eiskalten Becken liegt ein Windmesser – von der Wetterstation, zweihundert Meter vom Mast entfernt.']);
        clip(S, 'c8');
      } else { g = gib(S, 'wasser', 6); log(S, 'n', 'Das Wasser rauscht. Du füllst den Eimer mit klarem Wasser. (+' + g + ' Wasser)'); }
    } else if (id === 'kapelle') {
      if (!S.f.balzTraf) {
        S.f.balzTraf = true; gib(S, 'naegel', 2); gib(S, 'draht', 1);
        karte(S, { art: 'wahl', id: 'balz', bild: 'ort:kapelle', titel: 'Die alte Kapelle',
          z: ['In der Kapelle brennt ein kleines Feuer. Ein alter Mann sitzt daneben, eine Decke um die Schultern.',
            '«So. Du bist also wieder da», sagt er. «Ich bin Balz. Früher Senn auf der Alp.»',
            '«Der Weg ist nicht einfach so verschüttet», sagt er und schaut zum Grat. «Mehr sage ich, wenn die Station wieder misst.»',
            '«Zum Grat kommst du über den Lawinenkegel. Aber nicht ohne Eisen an den Schuhen.» Er schenkt dir Nägel und Draht.',
            '«Und wenn du Strom brauchst: Im alten Stollen liegt ein Akku. Nimm Licht mit.»',
            'Dann zeigt er auf MoveEye: «Was hat das Ding da aufgenommen?»'] });
        clip(S, 'c7');
      } else if (S.leute.balz < 2) log(S, 'p', 'Balz: «Bau mir unten ein Dach, dann komme ich. Mit Käse. Und mit etwas, das du brauchst.»');
      else { gib(S, 'stoff', 1); log(S, 'n', 'Die Kapelle ist leer. In der Sakristei findest du eine alte Decke. (+1 Stoff)'); }
    } else if (id === 'stollen') {
      if (!S.w.akku && S.station < 3) {
        S.w.akku = true; gib(S, 'draht', 2);
        ortKarte(S, id, 'Der alte Stollen', ['Bretter verrammeln den Eingang. Ein verblichenes Schild: «Gesperrt – Sprengarbeiten 1984».',
          'Im Laternenlicht: Kisten, Kabelrollen und ein Akku mit dem Aufkleber «B-7 Reserve». Er ist sogar geladen. (+Akku, +2 Draht)',
          'Auf dem staubigen Boden: frische Stiefelabdrücke. ' + HUND + ' schnüffelt daran und wedelt.']);
        clip(S, 'c13');
      } else { gib(S, 'draht', 1); log(S, 'n', 'Im Stollen tropft es. Du nimmst noch ein Stück Kabel mit. (+1 Draht)'); }
    } else if (id === 'lawine') {
      if (!S.w.panel && S.station < 2) {
        S.w.panel = true;
        ortKarte(S, id, 'Auf dem Lawinenkegel', ['Der Altschnee ist hart wie Glas. Mit den Steigeisen geht es Schritt für Schritt.',
          'Halb im Schnee steckt ein Solarpanel – verbogen, aber ganz. Der Sturm hat es vom Grat geweht.']);
        clip(S, 'c9');
      } else log(S, 'n', 'Vom Lawinenkegel siehst du das ganze Tal: die Hütte, den See, die Kapelle. Und kein Weg hinaus.');
    } else if (id === 'station') {
      var s = S.station;
      if (s === 0) {
        S.station = 1;
        ortKarte(S, id, 'Station B-7', ['Die Wetterstation liegt umgestürzt auf dem Grat. Mit dem Seil und Holzkeilen richtest du den Mast wieder auf.',
          'Der Kasten ist zugefroren. Darauf klebt ein Zettel in deiner Handschrift: «Nicht auslesen, bevor alles läuft.»']);
        clip(S, 'c10');
        me(S, 'Deine Handschrift. Auf der Station. Ich sage nichts. Ich nehme nur auf.');
      } else if (s === 1) {
        S.w.panel = false; S.w.wind = false; S.station = 2;
        ortKarte(S, id, 'Strom und Wind', ['Das Solarpanel sitzt wieder oben, der Windmesser dreht sich im Wind.', 'Ein Lämpchen im Kasten flackert. Es fehlt nur noch der Datenlogger.']);
        clip(S, 'c11');
      } else if (s === 2) {
        S.w.akku = false; S.station = 3;
        ortKarte(S, id, 'Der Akku', ['Der Akku aus dem Stollen passt in den Kasten. Die Anzeige springt an: «Speicher: 1 Datensatz».',
          'Ein einziger Datensatz? Die Station hat doch jahrelang gemessen.']);
        me(S, 'Ein Datensatz. Ich bin neugierig. Das ist neu für mich – und ich mag es nicht besonders.');
      } else if (s === 3) {
        S.w.logger = false; S.station = 4;
        ortKarte(S, id, 'Der Datenlogger', ['Du steckst den Datenlogger ein. Die Kabel passen, als hätte sie jemand genau so vorbereitet.',
          'Die Anzeige zeigt: «Neustart bereit». Balz hat recht: Das braucht klares Wetter.']);
        clip(S, 'c12');
      } else if (s === 4) {
        S.station = 5;
        karte(S, { art: 'bild', bild: 'ort:station', titel: 'Die Station misst', z: ['Du drückst den Knopf. Die Station summt, das Lämpchen wird grün.',
          'Dreimal kurz, einmal lang – genau wie in deiner Aufnahme vom See.', 'MoveEye verbindet sich mit dem Logger. «Ich habe jetzt alles», sagt die Kamera. «Alle Stücke.»'] });
        karte(S, { art: 'clip', id: 'ganz', nr: 13 });
        S.clips.push('ganz');
        karte(S, { art: 'bild', bild: 'daten', titel: 'Der letzte Messwert', z: ['Die Station zeigt ihre gespeicherten Werte. Die meisten sind normal.',
          'Der letzte aber trägt ein Datum: in drei Tagen. Luftdruck, Wind, Temperatur – gemessen an einem Tag, der noch gar nicht war.',
          'MoveEye: «Entweder ist meine Uhr kaputt – oder diese Station weiss etwas, das wir noch nicht wissen. Ich hoffe auf die Uhr.»'] });
        if (S.leute.livia === 2) karte(S, { art: 'wahl', id: 'daten', bild: 'livia', titel: 'Livias Bitte', z: ['Livia hat dich gebeten, ihr zuerst zu zeigen, was auf der Station ist.', 'Was tust du?'] });
        else ende(S);
      }
    }
  }
  function ende(S) { if (!S.f.endeKarte) { S.f.endeKarte = true; karte(S, { art: 'ende' }); } }
  function tripEnde(S) {
    var id = S.trip.ort; S.trip = null;
    besuch(S, id);
  }

  // ---- Die Liste aller Dinge, die man tun kann (für Bildschirm, Tipp und Test) ----
  // Eintrag: {id, tab, gr, art: 'akt' | 'bau' | 'ort', name, info, kosten, cd (Sekunden), sperre ('' = geht), bereit (0..1)}
  var AKT = [
    { id: 'anblasen', tab: 'huette', name: 'In die Glut blasen', cd: 2, sicht: function (S) { return !S.f.feuerAn; } },
    { id: 'tasten', tab: 'huette', name: 'Im Dunkeln umhertasten', cd: 3, sicht: function (S) { return S.f.feuerAn && (S.n.tasten || 0) < 3; } },
    { id: 'nachlegen', tab: 'huette', cd: 5, sicht: function (S) { return S.f.holzDa; },
      name: function (S) { return S.feuer <= 0 ? 'Feuer neu entfachen' : 'Holz nachlegen'; },
      kosten: function (S) { return { holz: S.feuer <= 0 ? 2 : 1 }; },
      sperre: function (S) { return S.feuer >= 4 ? 'Das Feuer brennt hell.' : ''; } },
    { id: 'rucksack', tab: 'huette', name: 'Rucksack öffnen', cd: 2, sicht: function (S) { return S.f.rucksack && !S.f.offen; } },
    { id: 'kamera', tab: 'huette', name: 'Kamera einschalten', cd: 2, sicht: function (S) { return S.f.offen && !S.f.me; } },
    { id: 'hinaus', tab: 'huette', name: 'Die Tür aufdrücken', cd: 2, sicht: function (S) { return S.f.me && !S.f.draussen; },
      sperre: function (S) { return nacht(S) ? 'Draussen ist es stockfinster. Warte auf den Morgen.' : S.feuer < 2 ? 'Erst das Feuer gross machen.' : ''; } },
    { id: 'ruhen', tab: 'huette', name: 'Ruhen bis zum Morgen', cd: 2, sicht: function (S) { return S.f.me && nacht(S); },
      info: function (S) { return 'Das Feuer brennt mit etwas Holz durch die Nacht.'; } },
    { id: 'streicheln', tab: function (S) { return S.f.draussen ? 'leute' : 'huette'; }, name: HUND + ' kraulen', cd: 6, sicht: function (S) { return S.f.hund; } },
    { id: 'holz', tab: 'lager', gr: 'Draussen', name: 'Holz sammeln', cd: 12, sicht: function (S) { return S.f.draussen; },
      info: function (S) { return '+' + holzMenge(S) + ' Holz'; },
      sperre: function (S) { return nacht(S) && !S.w.laterne ? 'Zu dunkel. Eine Laterne wäre gut.' : S.r.holz >= K.cap(S, 'holz') ? 'Kein Platz mehr für Holz.' : ''; } },
    { id: 'wasser', tab: 'lager', gr: 'Draussen', name: 'Wasser holen', cd: 12, sicht: function (S) { return S.f.draussen; },
      info: function (S) { return '+' + (S.w.eimer ? 4 : 2) + ' Wasser'; },
      sperre: function (S) { return nacht(S) && !S.w.laterne ? 'Den Bach findest du nachts nicht.' : S.r.wasser >= K.cap(S, 'wasser') ? 'Alle Gefässe sind voll.' : ''; } },
    { id: 'beeren', tab: 'lager', gr: 'Draussen', name: 'Beeren suchen', cd: 15, sicht: function (S) { return S.f.draussen; },
      info: function (S) { return '+' + (S.bau.gestell ? 3 : 2) + ' Essen'; },
      sperre: function (S) { return nacht(S) ? 'Beeren findet man nachts nicht.' : S.r.essen >= K.cap(S, 'essen') ? 'Der Vorrat ist voll.' : ''; } },
    { id: 'fischen', tab: 'lager', gr: 'Draussen', name: 'Am See fischen', cd: 20, sicht: function (S) { return S.w.angel; },
      info: function (S) { return '+' + (S.bau.gestell ? 4 : 3) + ' Essen'; },
      sperre: function (S) { return nacht(S) && !S.w.laterne ? 'Zu dunkel zum Fischen.' : S.wetter === 'sturm' ? 'Bei Sturm ist der See gefährlich.' : S.r.essen >= K.cap(S, 'essen') ? 'Der Vorrat ist voll.' : ''; } },
    { id: 'signal_an', tab: 'lager', gr: 'Draussen', name: 'Signalfeuer anzünden', cd: 5, kosten: function () { return { holz: 3 }; },
      sicht: function (S) { return S.bau.signal && S.leute.livia === 0 && !S.f.signal; },
      sperre: function (S) { var z = zeit(S); return z === 'abend' || z === 'nacht' ? '' : 'Ein Signal sieht man erst in der Dämmerung.'; } },
    { id: 'hund', tab: 'leute', name: HUND + ' suchen lassen', cd: 60, sicht: function (S) { return S.f.draussen; },
      info: function () { return 'Er findet oft, was fehlt.'; },
      sperre: function (S) { return nacht(S) && !S.w.laterne ? HUND + ' rollt sich ein. Nachts sucht sie nicht.' : S.wetter === 'sturm' ? HUND + ' will bei dem Sturm nicht hinaus.' : ''; } },
    { id: 'livia', tab: 'leute', name: 'Mit Livia reden', cd: 4, sicht: function (S) { return S.leute.livia === 2; } },
    { id: 'balz', tab: 'leute', name: 'Mit Balz reden', cd: 4, sicht: function (S) { return S.leute.balz === 2; } },
    { id: 'tipp', tab: 'moveeye', name: 'MoveEye fragen: Was jetzt?', cd: 2, sicht: function (S) { return S.f.me; } }
  ];
  function holzMenge(S) { return 2 + (S.w.axt ? 2 : 0) + (S.bau.schopf ? 1 : 0) - (S.wetter === 'regen' && !S.bau.schopf ? 1 : 0); }
  function val(v, S) { return typeof v === 'function' ? v(S) : v; }
  K.liste = function (S, alle) {
    var L = [], i, a, sp;
    var unterwegs = S.trip ? 'Du bist unterwegs: ' + ORTE[S.trip.ort].name + '.' : '';
    for (i = 0; i < AKT.length; i++) {
      a = AKT[i]; if (!a.sicht(S)) continue;
      var k = a.kosten ? a.kosten(S) : null;
      sp = (a.id !== 'tipp' && a.id !== 'streicheln' && unterwegs) || (a.sperre ? a.sperre(S) : '');
      if (!sp && k && !hat(S, k)) sp = 'Es fehlt: ' + K.fehlt(S, k).map(function (x) { return NAME[x]; }).join(', ') + '.';
      L.push({ id: a.id, tab: val(a.tab, S), gr: a.gr || '', art: 'akt', name: val(a.name, S), info: a.info ? a.info(S) : '', kosten: k, cd: a.cd, sperre: sp, bereit: bereit(S, a.id) });
    }
    for (i = 0; i < BAU.length; i++) {
      var b = BAU[i]; if ((b.werk ? S.w[b.id] : S.bau[b.id]) || !b.sicht(S)) continue;
      sp = unterwegs || (hat(S, b.k) ? '' : 'Es fehlt: ' + K.fehlt(S, b.k).map(function (x) { return NAME[x]; }).join(', ') + '.');
      L.push({ id: 'bau_' + b.id, tab: b.tab, gr: b.gr, art: 'bau', name: b.name, info: b.info, kosten: b.k, cd: 2, sperre: sp, bereit: bereit(S, 'bau_' + b.id), clip: !!b.clip });
    }
    for (var o in ORTE) {
      if (!ortSicht(S, o)) continue;
      var kk = ortKosten(S, o);
      sp = unterwegs || ortSperre(S, o) || (hat(S, kk) ? '' : 'Es fehlt: ' + K.fehlt(S, kk).map(function (x) { return NAME[x]; }).join(', ') + '.');
      var nm = ORTE[o].name, inf = ORTE[o].info;
      if (o === 'station' && S.station < 5) inf = 'Nächster Schritt: ' + ST_SCHRITT[S.station].name + '.';
      L.push({ id: 'ort_' + o, tab: 'tal', gr: 'Aufbrechen', art: 'ort', ort: o, name: nm, info: inf, kosten: kk, cd: 1, sperre: sp, bereit: 1, besucht: S.orte[o] || 0, dauer: ortDauer(S, o) });
    }
    return L;
  };
  function bereit(S, id) {
    var e = S.cd[id] || 0; if (e <= S.t) return 1;
    var l = S.cdl[id] || 1; return Math.max(0, 1 - (e - S.t) / l);
  }
  K.eintrag = function (S, id) { var L = K.liste(S); for (var i = 0; i < L.length; i++) if (L[i].id === id) return L[i]; return null; };

  // ---- Etwas tun ----
  K.tun = function (S, id) {
    if (S.karten.length) return false;
    var e = K.eintrag(S, id);
    if (!e || e.sperre || e.bereit < 1) return false;
    var c = e.cd * (e.art === 'akt' && ['holz', 'wasser', 'beeren', 'fischen', 'hund', 'nachlegen'].indexOf(id) >= 0 ? K.mult(S) : 1);
    S.cd[id] = S.t + c; S.cdl[id] = c;
    if (e.art === 'bau') {
      var b = BAU.filter(function (x) { return 'bau_' + x.id === id; })[0];
      zahle(S, b.k); gebaut(S, b); return true;
    }
    if (e.art === 'ort') { zahle(S, ortKostenOhneStation(S, e.ort)); aufbrechen(S, e.ort); return true; }
    var g;
    switch (id) {
      case 'anblasen':
        S.n.blasen = (S.n.blasen || 0) + 1;
        if (S.n.blasen < 2) log(S, 'n', 'Du bläst in die Glut. Sie glimmt rot auf – und wird wieder dunkel.');
        else { S.f.feuerAn = true; S.feuer = 1; S.fz = 0; log(S, 'n', 'Noch einmal. Ein Flämmchen züngelt hoch. Du siehst deine Hände.'); }
        break;
      case 'tasten':
        S.n.tasten = (S.n.tasten || 0) + 1;
        if (S.n.tasten === 1) { S.f.holzDa = true; gib(S, 'holz', 5); log(S, 'n', 'Deine Hand findet Holzscheite neben einem eisernen Ofen. (+5 Holz)'); }
        else if (S.n.tasten === 2) { S.f.hund = true; log(S, 'n', 'Etwas Warmes, Weiches. Eine Hündin! Sie leckt dir die Hand, als würde sie dich kennen. Am Halsband steht «' + HUND + '».'); }
        else { S.f.rucksack = true; log(S, 'n', 'Ein Rucksack, schwer und nass. Deiner? Du weisst es nicht. Du weisst nicht einmal deinen Namen.'); }
        break;
      case 'nachlegen':
        zahle(S, e.kosten);
        if (S.feuer <= 0) { S.feuer = 1; S.fz = 0; log(S, 'n', 'Mit klammen Fingern bringst du das Feuer wieder in Gang.'); }
        else {
          S.feuer++;
          log(S, 'n', ['', 'Das Feuer knistert.', 'Das Feuer brennt. Es wird wärmer.', 'Das Feuer prasselt. Schatten tanzen an den Wänden.', 'Das Feuer brennt hell und warm.'][S.feuer]);
        }
        break;
      case 'rucksack':
        S.f.offen = true; S.w.kessel = true;
        log(S, 'n', 'Im Rucksack: eine Trinkflasche, ein Kessel, ein zerknitterter Plan – und eine Kamera. Auf dem Gehäuse steht «MoveEye».');
        break;
      case 'kamera':
        S.f.me = true; S.meT = S.t;
        log(S, 'me', '… System startet. Speicherkarte beschädigt. Lesbar: 3 %.');
        log(S, 'me', 'Oh. Hallo. Du siehst schlecht aus. Ich übrigens auch – zumindest innen drin.');
        clip(S, 'c1');
        me(S, 'Das war alles, was ich retten konnte. Vielleicht findet sich mehr, wenn hier wieder etwas funktioniert.');
        break;
      case 'hinaus':
        S.f.draussen = true;
        karte(S, { art: 'bild', bild: 'aussen', titel: 'Draussen', z: ['Kalte Luft. Du stehst vor einer kleinen Steinhütte, das Dach halb abgedeckt.',
          'Ringsum ragen Felswände auf wie Mauern. Unten liegt ein dunkler See, und hoch oben auf dem Grat steht ein Mast.',
          'Wo ein Weg sein müsste, türmt sich ein Berg aus Geröll. Das Tal ist abgeschnitten – wie eine Insel.'] });
        me(S, 'Hm. Ich glaube, wir sind wegen dieser Station dort oben hier. Das Gefühl habe ich jedenfalls. Kameras haben Gefühle. Kleine.');
        break;
      case 'ruhen': ruhen(S); break;
      case 'streicheln':
        S.n.kraulen = (S.n.kraulen || 0) + 1;
        log(S, 'n', [HUND + ' legt dir den Kopf aufs Knie.', HUND + ' wedelt so fest, dass ihr ganzer Hintern mitwackelt.', HUND + ' brummt zufrieden und rollt sich auf den Rücken.', HUND + ' schaut dich an, als wüsste sie alles, was du vergessen hast.'][S.n.kraulen % 4]);
        if (S.n.kraulen === 5) me(S, 'Ich zähle mit: fünfmal gekrault. Sie findet, das ist zu wenig.');
        break;
      case 'holz':
        g = gib(S, 'holz', holzMenge(S));
        log(S, 'n', (S.wetter === 'regen' && !S.bau.schopf ? 'Nasses Holz, aber Holz.' : nacht(S) ? 'Im Laternenlicht sammelst du Holz.' : 'Du sammelst Äste und Bruchholz.') + ' (+' + g + ' Holz)');
        break;
      case 'wasser': g = gib(S, 'wasser', S.w.eimer ? 4 : 2); log(S, 'n', 'Eiskaltes Wasser aus dem Bach. (+' + g + ' Wasser)'); break;
      case 'beeren': g = gib(S, 'essen', S.bau.gestell ? 3 : 2); log(S, 'n', 'Heidelbeeren und ein paar Pilze. (+' + g + ' Essen)'); break;
      case 'fischen': g = gib(S, 'essen', S.bau.gestell ? 4 : 3); log(S, 'n', 'Eine Forelle beisst an! (+' + g + ' Essen)'); break;
      case 'signal_an':
        zahle(S, e.kosten); S.f.signal = true;
        log(S, 'n', 'Das Signalfeuer lodert hoch. Funken steigen in den Himmel.');
        me(S, 'Wenn uns jemand sehen kann, dann jetzt. Ich nehme das auf. Für alle Fälle.');
        if (nacht(S)) S.f.liviaT = S.t + 20;
        break;
      case 'hund': hundSucht(S); break;
      case 'livia': rede(S, 'livia', LIVIA, LIVIA_RUHE); break;
      case 'balz': rede(S, 'balz', BALZ, BALZ_RUHE); break;
      case 'tipp': me(S, K.tipp(S)); break;
    }
    return true;
  };
  function ortKostenOhneStation(S, id) {
    var k = ortKosten(S, id), r = {};
    for (var x in k) if (typeof k[x] === 'number') r[x] = k[x];
    return r;
  }

  // ---- Karten (Bilder, Aufnahmen, Entscheidungen) schliessen ----
  K.karteZu = function (S, i) {
    var c = S.karten[0]; if (!c) return;
    if (c.art === 'wahl') {
      var o = WAHL[c.id]; if (!o) { S.karten.shift(); return; }
      i = Math.max(0, Math.min(o.length - 1, i | 0));
      S.karten.shift();
      if (c.id === 'livia') { S.leute.livia = 2; S.w.seil = true; S.f.signal = false; log(S, 'n', 'Livia bleibt. In ihrem Rucksack: ein langes Kletterseil. (+Seil)'); }
      o[i].fn(S);
      return;
    }
    if (c.art === 'ende') { S.karten.shift(); S.ende = true; return; }
    S.karten.shift();
  };

  // ---- Zeit läuft ----
  function tick(S, d) {
    var p0 = phase(S); S.t += d; var p1 = phase(S);
    if (p1 < p0) morgen(S);
    if (p0 < 0.4 && p1 >= 0.4) wetterWechsel(S);
    if (p0 < 0.68 && p1 >= 0.68) abend(S);
    if (p0 < 0.78 && p1 >= 0.78) nachtBeginn(S);
    feuerStep(S, d);
    passiv(S, d);
    if (S.trip && S.t >= S.trip.bis) tripEnde(S);
    if (S.f.liviaT && S.leute.livia === 0 && S.t >= S.f.liviaT && !S.trip && !S.karten.length) liviaKommt(S);
    if (S.f.me && !S.trip && !S.karten.length && S.t - S.meT > 140) { S.meT = S.t; meIdle(S); }
  }
  K.step = function (S, dt) {
    while (dt > 1e-6) { var d = Math.min(dt, 0.5); dt -= d; S.echt += d; tick(S, d); }
  };

  // ---- Was ist als Nächstes dran? (MoveEye-Tipp und Test-Spieler) ----
  K.ziel = function (S) {
    var f = S.f;
    function z(id, t) { return { id: id, t: t }; }
    if (!f.feuerAn) return z('anblasen', 'Da glimmt noch etwas im Ofen. Hineinblasen?');
    if ((S.n.tasten || 0) < 3) return z('tasten', 'Taste dich im Dunkeln um. Vielleicht findest du Holz.');
    if (!f.offen) return z('rucksack', 'Da ist ein Rucksack. Öffne ihn.');
    if (!f.me) return z('kamera', 'Die Kamera im Rucksack – schalte sie ein.');
    if (!f.draussen) return nacht(S) ? z('ruhen', 'Draussen ist Nacht. Ruh dich aus, bis es hell wird – oder halte das Feuer in Gang.') : z('hinaus', 'Es wird hell. Drück die Tür auf und schau, wo wir sind.');
    if (!S.bau.ofentuer) return z('bau_ofentuer', 'Die Ofentür richten. Dafür brauchst du Draht – lass ' + HUND + ' suchen.');
    if (!S.bau.dach) return z('bau_dach', 'Das Dach flicken: Holz sammeln, und ' + HUND + ' findet bestimmt Nägel.');
    if (!S.bau.fenster) return z('bau_fenster', 'Das Fenster abdichten. Stoff findest du vielleicht am verschütteten Weg – oder ' + HUND + ' bringt welchen.');
    if (!S.orte.see) return z('ort_see', 'Unter «Tal»: zum See hinunter. Wer weiss, was dort liegt.');
    if (!S.bau.werkbank) return z('bau_werkbank', 'Eine Werkbank im Lager. Ohne Werkzeug kommen wir nicht weit.');
    if (!S.w.laterne) return z('bau_laterne', 'Eine Laterne an der Werkbank bauen. Licht in der Nacht.');
    if (S.leute.livia < 2) {
      if (!S.bau.signal) return z('bau_signal', 'Die Spuren am See … Schichte ein Signalfeuer auf. Nachts sieht man es im ganzen Tal.');
      if (!f.signal) return z('signal_an', 'Zünde das Signalfeuer an, sobald es dämmert.');
      return z('warten', 'Das Signal brennt. Jetzt heisst es warten – und das Feuer hüten.');
    }
    if (!f.balzTraf) return z('ort_kapelle', 'Die alte Kapelle. Livia meint, dort brenne manchmal Licht.');
    if (!S.w.wind && S.station < 2) return z('ort_wasserfall', 'Mit Livias Seil kommst du ins Becken am Wasserfall. Da glänzte doch etwas.');
    if (!S.bau.unterstand && S.leute.balz < 2) return z('bau_unterstand', 'Ein Unterstand für Balz. Er hat etwas, das wir brauchen, glaube ich.');
    if (!S.w.steigeisen) return z('bau_steigeisen', 'Steigeisen an der Werkbank schmieden – für den Lawinenkegel.');
    if (!S.orte.lawine) return z('ort_lawine', 'Über den Lawinenkegel zum Grat. Nur bei trockenem Wetter.');
    if (!S.w.akku && S.station < 3) return z('ort_stollen', 'Balz sprach von einem Akku im alten Stollen. Nimm die Laterne mit.');
    if (S.station === 3 && !S.w.logger) return z('warten', 'Der Datenlogger fehlt. Balz hat ihn – er kommt, sobald sein Unterstand steht.');
    if (S.station < 5) return z('ort_station', 'Zur Wetterstation: ' + ST_SCHRITT[S.station].name + '.');
    return z('fertig', 'Die Station misst. Kapitel 1 ist geschafft.');
  };
  var TIPP_VOR = ['Analyse: ', '', 'Mein Vorschlag: ', 'Ich an deiner Stelle: '];
  K.tipp = function (S) {
    var z = K.ziel(S), e = K.eintrag(S, z.id), t = TIPP_VOR[K.stufe(S)] + z.t;
    if (e && e.sperre && e.sperre.indexOf('Es fehlt') === 0) t += ' ' + e.sperre;
    else if (e && e.sperre && e.art === 'ort') t += ' Gerade nicht: ' + e.sperre;
    if (S.feuer <= 1 && S.f.holzDa && z.id !== 'anblasen') t += ' Und: Das Feuer ist fast aus.';
    return t;
  };

  // ---- Test-Spieler: spielt wie ein vernünftiger Mensch (liest, denkt, wartet) ----
  function worte(s) { return String(s).split(/\s+/).length; }
  K.botWahl = function (S) {
    if (S.trip || S.karten.length || S.ende) return null;
    var L = K.liste(S), M = {}, i;
    for (i = 0; i < L.length; i++) M[L[i].id] = L[i];
    function geht(id) { var e = M[id]; return e && !e.sperre && e.bereit >= 1; }
    var z = K.ziel(S), b = K.bedarf(S);
    if (!S.f.draussen) {
      if (geht(z.id) && z.id !== 'ruhen') return z.id;
      if (S.feuer < 3 && geht('nachlegen') && S.r.holz > 1) return 'nachlegen';
      if (z.id === 'ruhen' && geht('ruhen')) return 'ruhen';
      return geht(z.id) ? z.id : null;
    }
    if (S.feuer <= 1 && geht('nachlegen')) return 'nachlegen';
    if (geht('livia') && K.neueRede(S, 'livia')) return 'livia';
    if (geht('balz') && K.neueRede(S, 'balz')) return 'balz';
    var zid = z.id;
    // the goal itself
    if (geht(zid)) {
      var e = M[zid];
      if (e.art === 'ort') {
        var res = { essen: b.essen + 1, wasser: b.wasser };
        if ((S.r.essen - (e.kosten.essen || 0) >= Math.min(res.essen, 4) || S.leute.balz === 2) && S.r.wasser - (e.kosten.wasser || 0) >= 1) {
          if (S.feuer < 3 && geht('nachlegen') && S.leute.livia < 2) return 'nachlegen';
          return zid;
        }
      } else return zid;
    }
    // useful extras when affordable
    var extra = ['bau_axt', 'bau_schopf', 'bau_eimer', 'bau_angel', 'bau_tonne', 'bau_gestell'];
    for (i = 0; i < extra.length; i++) if (geht(extra[i]) && S.r.holz - M[extra[i]].kosten.holz >= 4) return extra[i];
    // night without light: sleep
    if (nacht(S) && !S.w.laterne && geht('ruhen') && S.r.holz >= 4) return 'ruhen';
    if (zid === 'warten' && nacht(S) && geht('ruhen') && !(S.f.signal && S.leute.livia === 0) && S.r.holz >= 6) return 'ruhen';
    // what is missing for the goal (and some reserve)?
    var need = { holz: 6, essen: b.essen + 3, wasser: b.wasser + 2 }, ge = M[zid];
    if (ge && ge.kosten) for (var x in ge.kosten) if (typeof ge.kosten[x] === 'number') need[x] = Math.max(need[x] || 0, ge.kosten[x] + (x === 'holz' ? 4 : x === 'essen' ? b.essen : x === 'wasser' ? b.wasser : 0));
    if (zid === 'ort_station' && S.station === 0) need.holz = Math.max(need.holz, 14);
    var opt = [];
    for (x in need) {
      var have = S.r[x] !== undefined ? S.r[x] : S.it[x], fe = need[x] - have;
      if (fe > 0) opt.push([x, fe / need[x]]);
    }
    opt.sort(function (a, c) { return c[1] - a[1]; });
    var QUELLE = { holz: ['holz'], wasser: ['wasser'], essen: ['fischen', 'beeren', 'hund'], draht: ['hund'], naegel: ['hund', 'ort_geroell'], schnur: ['hund'], stoff: ['ort_geroell', 'hund'] };
    for (i = 0; i < opt.length; i++) {
      var q = QUELLE[opt[i][0]] || [];
      for (var j = 0; j < q.length; j++) if (geht(q[j]) && !(q[j] === 'ort_geroell' && S.orte.geroell)) return q[j];
    }
    if (geht('hund') && (bedarfItems(S))) return 'hund';
    if (S.feuer < 3 && geht('nachlegen') && S.r.holz > 4) return 'nachlegen';
    if (geht('holz') && S.r.holz < K.cap(S, 'holz') - 6) return 'holz';
    if (geht('wasser') && S.r.wasser < 8) return 'wasser';
    if (geht('beeren') && S.r.essen < 8) return 'beeren';
    if (nacht(S) && geht('ruhen') && zid !== 'signal_an' && !(S.f.signal && S.leute.livia === 0) && S.r.holz >= 4) return 'ruhen';
    return null;
  };
  K.bot = function (S, o) {
    o = o || {};
    var max = o.max || 4 * 3600, denk = o.denk === undefined ? 2 : o.denk, lese = o.lese === undefined ? 3.5 : o.lese, n = 0, letzt = S.logN, zug = [];
    while (!S.ende && S.echt < max) {
      if (S.karten.length) {
        var c = S.karten[0], w = c.art === 'clip' ? CLIPS[c.id].z.join(' ') : (c.z || []).join(' ');
        K.step(S, 6 + worte(w) / lese);
        K.karteZu(S, 0); continue;
      }
      var a = K.botWahl(S);
      if (a) {
        K.tun(S, a); n++; if (o.zuege) zug.push([Math.round(S.echt), a]);
        var wl = 0; for (var i = 0; i < S.log.length; i++) if (S.log[i].n > letzt) wl += worte(S.log[i].s);
        letzt = S.logN;
        K.step(S, denk + wl / lese);
      } else K.step(S, 1);
    }
    return { echt: Math.round(S.echt), tage: tagNr(S), aktionen: n, ende: S.ende, zuege: zug };
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = K;
  else G.VB = K;
})(typeof window !== 'undefined' ? window : this);
