/* Bild 15 «Die Werkstatt des Erfinders» (Meister+, grosses Finale): eine Kettenreaktions-Maschine mit 15 Stationen und
   Grüssen aus früheren Bildern (Apfel, Kessel, Socke, Kuckuck, Glühbirne, Krone, Badeente, Gespenst …).
   Der Startknopf lässt die Maschine laufen; sie stockt sichtbar bei der ersten kaputten Station (kostet nichts).
   Lösung (Reihenfolge der Reparaturen frei): Bauplan lesen · Brett von der Wand in die Lücke der Rinne · umgefallenen
   Dominostein aufstellen · Krug nehmen · am Wasserhahn füllen · in die Giesskanne · Socke aus dem Trichter ziehen ·
   Seil zurück auf die Rolle · Apfel aus der Obstschale hinter die Klappe · Krug wieder füllen · in den Kessel ·
   Flügel vom Boden + Klebeband = geflickter Flügel · ans Windrad · Glühbirne aus der Schublade in die Lampe · Start.
   Sackgasse: die Maschine mit leerem Kessel laufen lassen (der Brenner heizt einen leeren Kessel – nie!). */
(function () {
  var Z = WASNUN.Z;
  var BRETT = '<rect class="l" x="-26" y="-7" width="52" height="14" rx="3" fill="#c99562" transform="rotate(-20)"/>';
  function krug(voll) { return '<path class="l" fill="#9fd3ee" fill-opacity=".55" d="M-14 -20h24l4 8q8 4 6 16q-2 8 -8 8v8h-26z"/>' + (voll ? '<path fill="#4aa3e8" d="M-13 -6h22v24h-22z"/>' : '') + '<path class="l n" d="M-14 -20h24l4 8q8 4 6 16q-2 8 -8 8v8h-26z"/><path class="l n" style="stroke-width:4" d="M-14 -10q-10 2 -8 12q2 6 8 6"/>'; }
  var APFEL = '<circle class="l" r="16" fill="#e23b2e"/><path class="l n" style="stroke-width:3" d="M0 -15q2 -6 5 -9"/><path class="d" fill="#57b04f" d="M4 -20q10 -6 14 2q-8 6 -14 -2z"/>';
  var BAND = '<circle class="l" r="16" fill="#c9ced6"/><circle class="l" r="7" fill="#8a7a6a"/><path class="l" fill="#c9ced6" d="M14 4l14 6l-2 6l-14 -6z"/>';
  var FLUEGEL = '<path class="l" fill="#ffd23f" d="M-4 18l-6 -40q10 -8 20 0l-6 40z"/>';
  var FLUEGELK = FLUEGEL + '<path class="l" fill="#c9ced6" fill-opacity=".85" d="M-10 8h20v8h-20z"/>';
  var BIRNE = '<rect class="l" x="-7" y="10" width="14" height="10" fill="#8d98a8"/><path class="l" fill="#f6f1e6" d="M-15 -6a15 15 0 1 1 30 0q0 8 -8 16h-14q-8 -8 -8 -16z"/>';
  var KRONE = '<path class="l" fill="#ffd23f" d="M-24 10l-5 -30l14 12l15 -20l15 20l14 -12l-5 30z"/><rect class="l" x="-24" y="8" width="48" height="10" rx="3" fill="#f2b705"/><circle class="d" cx="0" cy="-16" r="4" fill="#e23b2e"/>';
  // die Stationen der Maschine in ihrer Reihenfolge: Punkt für den Funken, was dort repariert sein muss, und was sonst passiert
  var KETTE = [
    { id: 'start', p: [64, 130] },
    { id: 'rinne', p: [300, 196], ok: function (s) { return s.brett; }, halt: 'Die Kugel rollt los – und fällt mitten in der Rinne durch eine Lücke. Da fehlt ein Stück Bahn.' },
    { id: 'domino', p: [448, 196], ok: function (s) { return s.domino; }, halt: 'Klack, klack, klack – die Dominos fallen bis zum umgekippten Stein. Dort ist die Reihe unterbrochen.' },
    { id: 'giess', p: [504, 196], ok: function (s) { return s.giess; }, halt: 'Der letzte Domino kippt die Giesskanne – aber sie ist leer. Kein Tropfen läuft in den Trichter.' },
    { id: 'trichter', p: [560, 252], ok: function (s) { return !s.socke; }, halt: 'Wasser in den Trichter – und nichts kommt unten heraus. Im Trichter steckt etwas Weiches.' },
    { id: 'eimer', p: [602, 330], ok: function (s) { return s.rolle; }, halt: 'Der Eimer füllt sich und sinkt – aber das Seil ist von der Rolle gesprungen. Die Klappe oben bleibt zu.' },
    { id: 'klappe', p: [740, 214], ok: function (s) { return s.apfel; }, halt: 'Die Klappe geht auf – dahinter ist nichts, was die Rutsche hinunterrollen könnte.' },
    { id: 'wippe', p: [600, 402] },
    { id: 'kessel', p: [470, 430], leer: true },
    { id: 'windrad', p: [380, 330], ok: function (s) { return s.fluegel; }, halt: 'Der Dampf pfeift aufs Windrad – aber ein Flügel fehlt, es dreht sich nicht richtig.' },
    { id: 'kuckuck', p: [270, 292] },
    { id: 'knopf', p: [270, 396] },
    { id: 'lampe', p: [140, 448], ok: function (s) { return s.birne; }, halt: 'Der Kuckuck drückt den Knopf – klick – aber die Lampe bleibt dunkel. Die Fassung ist leer.' },
    { id: 'ballon', p: [140, 330] },
    { id: 'krone', p: [292, 486] }
  ];
  WASNUN.szene({
    id: 'erfinder', titel: 'Die Werkstatt des Erfinders', stufe: 5,
    ziel: 'Die grosse Weckmaschine des Erfinders soll ihn heute zum Geburtstag wecken – aber überall klemmt etwas. Bring die ganze Kette zum Laufen!',
    start: function () { return { tasche: [], plan: false, brett: false, brettWand: true, domino: false, krug: 'boden', giess: false, socke: true, rolle: false, apfel: false, obst: true, kessel: false, fluegelBoden: true, band: true, fluegel: false, birne: false, schublade: true, fertig: false }; },
    notizen: {
      plan: { titel: 'Bauplan der Weckmaschine', text: 'Kugel → Rinne → Dominos → Giesskanne (Wasser!) → Trichter → Eimer an der Rolle → Klappe → etwas Rundes → Wippe → Kessel (Wasser!) → Windrad → Kuckuck → Knopf → Lampe → Ballon → Krone.' },
      kessel: { titel: 'Zettel am Kessel', text: '«Kessel NIE leer heizen!»' }
    },
    dinge: {
      brett: { name: 'Brett', svg: '<g transform="translate(30 30)">' + BRETT + '</g>' },
      krug: { name: 'Leerer Krug', svg: '<g transform="translate(30 32)">' + krug(false) + '</g>' },
      krug_voll: { name: 'Krug voll Wasser', svg: '<g transform="translate(30 32)">' + krug(true) + '</g>' },
      apfel: { name: 'Apfel', svg: '<g transform="translate(30 32)">' + APFEL + '</g>' },
      band: { name: 'Klebeband', svg: '<g transform="translate(28 30)">' + BAND + '</g>' },
      fluegel: { name: 'Windrad-Flügel', svg: '<g transform="translate(30 30)">' + FLUEGEL + '</g>' },
      fluegel_k: { name: 'Flügel mit Klebeband', svg: '<g transform="translate(30 30)">' + FLUEGELK + '</g>' },
      birne: { name: 'Glühbirne', svg: '<g transform="translate(30 30)">' + BIRNE + '</g>' }
    },
    kombi: [{ a: 'fluegel', b: 'band', gibt: 'fluegel_k', text: 'Ein Streifen Klebeband um den Fuss des Flügels: Jetzt hält er bestimmt am Windrad.' },
      { a: 'band', b: 'brett', nein: 'Das Brett braucht kein Klebeband – es liegt einfach in der Lücke.' },
      { a: 'apfel', b: 'band', nein: 'Ein beklebter Apfel rollt schlechter. Lass ihn rund.' }],
    nutzlos: function (s, d) {
      if (d === 'krug_voll') return 'Wasser braucht die Maschine an zwei Stellen – der Bauplan sagt, wo.';
      if (d === 'krug') return 'Ein leerer Krug. Wo gibt es hier Wasser?';
      if (d === 'apfel') return 'Der Apfel soll rollen – hinter der Klappe oben ist eine Rutsche.';
      return '';
    },
    bild: function (s) {
      var f = s.fertig, h = '<rect width="800" height="600" fill="#e9d8b6"/><path class="d n" style="stroke:#d8c49c" d="M0 150h800M0 300h800M0 450h800"/>'
        + '<rect class="l" x="-5" y="560" width="810" height="50" fill="#9a6b43"/>';
      // Bauplan, oberes Regal mit Glas (Geheimnis) und Badeente
      h += '<g id="plan"><rect class="l" x="132" y="14" width="196" height="92" rx="4" fill="#2f6fd0"/><path class="n" stroke="#bfe6ff" stroke-width="2" d="M146 40h40l20 16h40l12 20h50M146 86q40 -14 80 0t80 -10"/><circle cx="186" cy="40" r="4" fill="#bfe6ff"/>' + Z.text(230, 32, 'WECKMASCHINE', { k: 11, f: '#fff' }) + '</g>'
        + '<rect class="l" x="360" y="104" width="230" height="10" fill="#8a5a3a"/>'
        + '<g id="glas"><rect class="l" x="392" y="52" width="50" height="52" rx="10" fill="#bfe6ff" fill-opacity=".5"/><rect class="l" x="388" y="46" width="58" height="10" rx="3" fill="#d64b3c"/><g id="geist" opacity=".5"><path fill="#fff" d="M404 96v-20a13 13 0 0 1 26 0v20l-5 -4l-4 4l-4 -4l-4 4l-4 -4z"/><circle cx="412" cy="78" r="2.5" fill="#3a3340"/><circle cx="422" cy="78" r="2.5" fill="#3a3340"/></g></g>'
        + '<g id="ente"><g transform="translate(540 86)"><ellipse class="l" cx="0" cy="8" rx="20" ry="12" fill="#ffd23f"/><circle class="l" cx="-10" cy="-8" r="11" fill="#ffd23f"/><path class="l" fill="#f2711c" d="M-20 -6l-12 3l12 5z"/>' + Z.auge(-12, -11, 3) + '</g></g>';
      // 1 Start, 2 Rinne mit Lücke, Kugel
      h += '<g id="start"><rect class="l" x="30" y="70" width="70" height="80" rx="10" fill="#5b6470"/><rect class="l" x="42" y="82" width="46" height="30" rx="6" fill="#3fcf6b"/>' + Z.text(65, 103, 'START', { k: 12, f: '#fff' }) + '<path class="l n" style="stroke:#3a3340;stroke-width:6" d="M65 150v14"/></g>'
        + '<circle class="l" cx="96" cy="140" r="11" fill="#c06bff"/>'
        + '<path class="l n" style="stroke:#8a5a3a;stroke-width:10" d="M84 156L180 180M240 186L320 206"/>' + (s.brett ? '<path class="l n" style="stroke:#c99562;stroke-width:10" d="M176 179L244 187"/>' : '<path class="d n" style="stroke:#d64b3c;stroke-dasharray:4 5" d="M184 182l52 4"/>');
      // 3 Dominos auf dem Regal
      h += '<rect class="l" x="320" y="208" width="150" height="10" fill="#8a5a3a"/><g id="domino">';
      for (var i = 0; i < 6; i++) { var x = 334 + i * 22; h += (i === 3 && !s.domino) ? '<rect class="l" x="' + (x - 6) + '" y="198" width="30" height="10" rx="2" fill="#f6f1e6"/>' : '<rect class="l" x="' + x + '" y="' + (f ? 196 : 170) + '" width="10" height="' + (f ? 12 : 38) + '" rx="2" fill="#f6f1e6"/><circle cx="' + (x + 5) + '" cy="184" r="2" fill="#3a3340"/>'; }
      h += '</g>';
      // 4 Giesskanne, Trichter mit Socke, Eimer an der Rolle
      h += '<g id="giess"><path class="l" fill="#3fbf6b" d="M478 212v-34h40v34z"/><path class="l n" style="stroke:#3fbf6b;stroke-width:6" d="M518 186l26 -10"/><path class="l n" style="stroke-width:4" d="M482 180q16 -20 32 0"/>' + (s.giess ? '<ellipse cx="498" cy="180" rx="16" ry="3" fill="#4aa3e8"/>' : '') + '</g>'
        + '<g id="trichter"><path class="l" fill="#c9ced6" d="M536 232h48l-18 30v40h-12v-40z"/>' + (s.socke ? '<path class="l" fill="#fff" d="M548 232v-16h16v10q4 8 -4 10z"/><path class="l n" style="stroke:#d64b3c;stroke-width:3" d="M548 222h16"/>' : '') + '</g>'
        + '<g id="rolle"><path class="l n" style="stroke:#5b6470;stroke-width:5" d="M660 20v24"/><circle class="l" cx="660" cy="60" r="18" fill="#8d98a8"/><circle cx="660" cy="60" r="5" fill="#3a3340"/></g>'
        + (s.rolle ? '<path class="l n" style="stroke:#c99562;stroke-width:3" d="M602 300V60q0 -18 18 -18h40q20 0 20 18v136"/>' : '<path class="l n" style="stroke:#c99562;stroke-width:3" d="M602 300V90q0 -20 30 -14q30 16 48 0v120"/>')
        + '<g id="eimer"><path class="l" fill="#8d98a8" d="M582 ' + (f ? 360 : 304) + 'h40l-6 40h-28z"/><path class="l n" style="stroke-width:3" d="M584 ' + (f ? 360 : 304) + 'q18 -16 36 0"/></g>';
      // 5 Klappe vor der Rutsche, Apfel
      h += '<path class="l n" style="stroke:#8a5a3a;stroke-width:9" d="M720 226L608 386"/><g id="klappe"><rect class="l" x="' + (f ? 680 : 696) + '" y="' + (f ? 170 : 196) + '" width="10" height="38" fill="#d64b3c"/></g><rect class="l" x="700" y="226" width="80" height="8" fill="#8a5a3a"/>'
        + (s.apfel && !f ? '<g transform="translate(744 210) scale(.9)">' + APFEL + '</g>' : '');
      // Brett an der Wand
      if (s.brettWand) h += '<g id="brett"><rect class="l" x="752" y="300" width="22" height="160" rx="3" fill="#c99562" transform="rotate(6 763 380)"/></g>';
      // 6 Wippe, 7 Kessel auf Brenner mit Zettel, 8 Windrad
      h += '<g id="wippe"><path class="l" fill="#5b6470" d="M590 432l14 -24l14 24z"/><path class="l n" style="stroke:#c99562;stroke-width:9" d="' + (f ? 'M550 382L660 426' : 'M548 424L660 392') + '"/></g>'
        + '<g id="kessel"><path class="l n" style="stroke:#3a3340;stroke-width:5" d="M440 480l10 -30M500 480l-10 -30"/>' + (f ? '<g class="fuss a-flack"><path class="d" fill="#3b8cff" d="M470 452q-12 -4 -6 -16q4 6 6 2q2 -10 8 -12q0 10 4 12q4 12 -12 14z"/></g>' : '<circle class="l" cx="470" cy="450" r="6" fill="#5b6470"/>')
        + '<path class="l" fill="#5f7186" d="M440 438q0 -40 30 -40t30 40z"/><path class="l n" style="stroke:#5f7186;stroke-width:6" d="M444 420l-24 -18"/><rect class="l" x="452" y="392" width="36" height="8" rx="3" fill="#3a3f4c"/>' + (s.kessel ? '<path fill="#4aa3e8" d="M456 430h28v6h-28z" opacity=".8"/>' : '')
        + '<g transform="translate(508 410) rotate(8)"><rect class="l" x="0" y="0" width="34" height="26" fill="#fff7c2"/><path class="d n" style="stroke:#d64b3c" d="M6 8h22M6 16h16"/></g></g>'
        + (f ? '<g class="a-schweb"><path class="l" fill="#fff" d="M410 378a10 10 0 0 1 12 -14a12 12 0 0 1 22 2a9 9 0 0 1 3 16q-20 4 -37 -4z"/></g>' : '');
      h += '<path class="l n" style="stroke:#5b6470;stroke-width:6" d="M380 330v110"/><g id="windrad"><g id="wr" class="dreh">' + [0, 90, 180, 270].map(function (w) { return (w === 270 && !s.fluegel) ? '' : '<g transform="translate(380 330) rotate(' + w + ')"><g transform="translate(0 -24)">' + FLUEGEL + '</g></g>'; }).join('') + '</g><circle class="l" cx="380" cy="330" r="7" fill="#d64b3c"/></g>';
      if (s.fluegelBoden) h += '<g id="fluegel"><g transform="translate(196 578) rotate(80)">' + FLUEGEL + '</g></g>';
      // 9 Kuckucksuhr (Gruss vom Uhrturm), 10 Knopf, 11 Lampe, 12 Ballon, 13 Krone
      h += '<g id="kuckuck"><path class="l" fill="#8a5a3a" d="M236 336v-66l34 -28l34 28v66z"/><path class="l" fill="#2b2233" d="M256 300v-20a14 14 0 0 1 28 0v20z"/>' + (f ? '<g transform="translate(292 292) scale(.5)">' + Z.vogel({ f: '#4aa3e8' }) + '</g>' : '') + '<path class="l n" style="stroke:#5b6470;stroke-width:2" d="M380 330L304 300"/></g>'
        + '<g id="knopf"><rect class="l" x="246" y="376" width="48" height="36" rx="6" fill="#5b6470"/><circle class="l" cx="270" cy="394" r="12" fill="#e23b2e"/><path class="n" stroke="#3a3340" stroke-width="3" d="M246 400Q180 420 156 436"/></g>'
        + '<g id="lampe"><path class="l n" style="stroke:#3a3340;stroke-width:6" d="M140 520v-50"/><rect class="l" x="110" y="516" width="60" height="12" rx="4" fill="#3a3f4c"/><path class="l" fill="#5b6470" d="M124 474l16 -20l16 20z"/>'
        + (s.birne ? '<g transform="translate(140 440) scale(.9)">' + BIRNE.replace('#f6f1e6', f ? '#fff7a8' : '#f6f1e6') + '</g>' + (f ? '<circle cx="140" cy="436" r="30" fill="#fff7a8" opacity=".35"/>' : '') : '<circle class="d" cx="140" cy="452" r="5" fill="#3a3340"/>') + '</g>'
        + '<g id="ballon"><path class="l n" style="stroke:#3a3340;stroke-width:2" d="M140 ' + (f ? 280 : 382) + 'L60 270"/><g transform="translate(0 ' + (f ? -100 : 0) + ')"><path class="l" fill="#ff9a3c" d="M118 350q-6 -50 22 -52q28 2 22 52q-10 18 -22 18t-22 -18z"/><path class="d n" style="stroke:#e26a1c" d="M140 298v70M124 310q-4 30 6 56M156 310q4 30 -6 56"/><rect class="l" x="130" y="366" width="20" height="10" rx="2" fill="#c99562"/></g></g>'
        + '<rect class="l" x="20" y="266" width="84" height="10" fill="#8a5a3a"/><path class="l n" style="stroke:#8a5a3a;stroke-width:7" d="M100 276L262 456"/>'
        + (f ? '' : '<g id="krone"><g transform="translate(56 256) scale(.8)">' + KRONE + '</g></g>');
      // Erfinder schläft im Sessel
      h += '<g id="erfinder"><path class="l" fill="#b06fd0" d="M222 568v-70q0 -20 20 -20h100q20 0 20 20v70z"/><path class="l" fill="#f6f1e6" d="M262 568q-6 -60 30 -62q36 2 30 62z"/><circle class="l" cx="292" cy="486" r="24" fill="#f3c9a5"/>'
        + '<path class="l" fill="#fff" d="M268 478q-14 -14 -4 -26q10 6 10 18zM316 478q14 -14 4 -26q-10 6 -10 18z"/>' + (f ? Z.auge(284, 486, 5) + Z.auge(300, 486, 5) + '<path class="l" fill="#fff" d="M282 498h20q-2 10 -10 10t-10 -10z"/>' : Z.auge(284, 486, 5, true) + Z.auge(300, 486, 5, true))
        + '<path class="l" fill="#c9ced6" d="M276 474h32v-6h-32z"/><circle class="l n" cx="284" cy="472" r="7"/><circle class="l n" cx="300" cy="472" r="7"/>' + (f ? '<g transform="translate(292 450) scale(.8)">' + KRONE + '</g>' : '') + '</g>' + (f ? '' : Z.zzz(326, 440, 0.8));
      // Obstschale, Spülbecken mit Hahn, Krug, Werkbank mit Klebeband und Schublade, Turbo-Knopf
      h += '<g id="obst"><path class="l" fill="#5fb3a8" d="M392 548q0 30 44 30t44 -30z"/>' + (s.obst ? '<g transform="translate(420 536) scale(.8)">' + APFEL + '</g>' : '') + '<circle class="l" cx="448" cy="538" r="12" fill="#ffd23f"/><path class="l" fill="#f2a900" d="M456 534q14 -6 18 6q-10 4 -18 -6z"/></g>'
        + '<g id="hahn"><rect class="l" x="500" y="510" width="120" height="50" rx="6" fill="#c9ced6"/><path class="l" fill="#9fb0c3" d="M510 516h100v20h-100z"/><path class="l n" style="stroke:#8d98a8;stroke-width:9" d="M560 510v-28h30v14"/><circle class="l" cx="560" cy="478" r="7" fill="#d64b3c"/></g>'
        + (s.krug === 'boden' ? '<g id="krug"><g transform="translate(650 548)">' + krug(false) + '</g></g>' : '')
        + '<g id="werkbank"><rect class="l" x="676" y="490" width="124" height="14" fill="#8a5a3a"/><rect class="l" x="690" y="504" width="96" height="56" fill="#9a6b43"/><rect class="l" x="704" y="516" width="68" height="28" rx="4" fill="#b07a4c"/><circle class="l" cx="738" cy="530" r="5" fill="#ffd23f"/>'
        + (s.band ? '<g transform="translate(712 476) scale(.8)">' + BAND + '</g>' : '') + '</g>'
        + '<g id="turbo"><rect class="l" x="728" y="22" width="62" height="50" rx="8" fill="#3a3340"/><circle class="l" cx="759" cy="47" r="14" fill="#ff5a5f"/>' + Z.text(759, 90, 'TURBO', { k: 12 }) + '</g>';
      if (f) h += '<g><path class="l" fill="#ffd23f" d="M420 20h300l-14 24l14 24h-300l14 -24z"/>' + Z.text(570, 52, 'Alles Gute, Erfinder!', { k: 18 }) + '</g>';
      h += '<circle id="funke" cx="0" cy="0" r="0" fill="#fff7a8" style="opacity:0"/>';
      return h;
    },
    stellen: [
      { id: 'start', r: [20, 60, 92, 100], tipp: async function (s, a) {
        a.ton('klick'); var F = a.q('#funke'); if (F) { F.setAttribute('r', 13); F.setAttribute('stroke', '#ff9a3c'); F.setAttribute('stroke-width', 4); }
        for (var i = 0; i < KETTE.length; i++) {
          var k = KETTE[i], v = KETTE[Math.max(0, i - 1)].p;
          await a.anim('#funke', [{ opacity: 1, transform: 'translate(' + v[0] + 'px,' + v[1] + 'px)' }, { opacity: 1, transform: 'translate(' + k.p[0] + 'px,' + k.p[1] + 'px)' }], i ? 380 : 10);
          a.ton(['klick', 'plopp', 'metall', 'tropf'][i % 4]);
          if (k.leer && !s.kessel) {
            a.ton('zisch'); await a.warte(500);
            return a.sackgasse('Die Wippe schnippt den Brenner an – und der Kessel ist leer! Er glüht und qualmt. Notaus!');
          }
          if (k.ok && !k.ok(s)) {
            await a.anim('#funke', [{ opacity: 1, transform: 'translate(' + k.p[0] + 'px,' + k.p[1] + 'px) scale(1)' }, { opacity: 0, transform: 'translate(' + k.p[0] + 'px,' + k.p[1] + 'px) scale(2.5)' }], 500);
            return a.gag(k.halt);
          }
        }
        a.ton('kuckuck'); a.mal({ fertig: true }); await a.warte(600); a.ton('fertig');
        return a.fertig('Kugel, Dominos, Wasser, Apfel, Dampf, Kuckuck, Licht, Ballon – und die Krone landet sanft auf dem Kopf des Erfinders. Er wacht auf: «Die Maschine läuft! Das schönste Geburtstagsgeschenk!»');
      } },
      { id: 'luecke', r: [164, 136, 96, 92], tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.brett ? 'Das Brett liegt sauber in der Lücke.' : 'In der Rinne klafft eine Lücke. Da fällt jede Kugel hindurch.');
      }, mit: { brett: async function (s, a) { a.ton('plumps'); a.gib('brett'); a.mal({ brett: true }); return a.weiter('Das Brett passt genau in die Lücke. Die Rinne ist wieder ganz.'); } } },
      { id: 'domino', r: [326, 134, 140, 92], tipp: async function (s, a) {
        if (s.domino) { a.ton('klick'); return a.gag('Alle Dominos stehen stramm in einer Reihe.'); }
        a.ton('klick'); a.mal({ domino: true }); return a.weiter('Den umgefallenen Dominostein wieder aufgestellt. Die Reihe ist komplett.');
      } },
      { id: 'giess', r: [456, 132, 96, 96], tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.giess ? 'Die Giesskanne ist voll Wasser und wartet auf den Domino.' : 'Die Giesskanne ist leer.');
      }, mit: { krug_voll: async function (s, a) {
        if (s.giess) return a.gag('Die Giesskanne ist schon voll.');
        a.ton('wasser'); a.tausch('krug_voll', 'krug'); a.mal({ giess: true }); return a.weiter('Gluck, gluck – die Giesskanne ist voll.');
      } } },
      { id: 'trichter', r: [514, 206, 92, 96], tipp: async function (s, a) {
        if (!s.socke) { a.ton('klick'); return a.gag('Der Trichter ist frei.'); }
        a.ton('plopp'); a.mal({ socke: false }); return a.weiter('Du ziehst eine Wollsocke aus dem Trichter – der Zwilling der Socke vom Dachboden! Jetzt läuft das Wasser durch.');
      } },
      { id: 'rolle', r: [612, 20, 96, 92], tipp: async function (s, a) {
        if (s.rolle) { a.ton('klick'); return a.gag('Das Seil läuft sauber über die Rolle.'); }
        a.ton('knarr'); a.mal({ rolle: true }); return a.weiter('Das Seil wieder in die Rille der Rolle gelegt. Jetzt zieht der Eimer die Klappe hoch.');
      } },
      { id: 'eimer', r: [556, 304, 92, 92], tipp: async function (s, a) {
        a.ton('metall'); return a.gag('Ein Eimer am Seil. Wenn Wasser hineinläuft, wird er schwer und sinkt.');
      } },
      { id: 'klappe', r: [690, 160, 100, 92], tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.apfel ? 'Hinter der Klappe wartet der Apfel auf seine grosse Fahrt.' : 'Hinter der Klappe ist eine leere Mulde – und dann die Rutsche hinunter zur Wippe.');
      }, mit: { apfel: async function (s, a) { a.ton('plopp'); a.gib('apfel'); a.mal({ apfel: true }); return a.weiter('Der Apfel liegt hinter der Klappe. Rund genug, um die Rutsche hinunterzurollen.'); } } },
      { id: 'brett', r: [708, 296, 92, 170], wenn: function (s) { return s.brettWand; }, tipp: async function (s, a) {
        a.ton('plumps'); a.mal({ brettWand: false }); a.nimm('brett'); return a.weiter('Ein Brett, genau so breit wie die Rinne.');
      } },
      { id: 'kessel', r: [416, 380, 132, 104], tipp: async function (s, a) {
        a.ton('metall'); a.notiz('kessel'); return a.gag(s.kessel ? 'Der Kessel ist voll Wasser. Am Zettel steht: «NIE leer heizen!»' : 'Der Kessel über dem Brenner ist leer. Ein Zettel daran: «Kessel NIE leer heizen!»');
      }, mit: { krug_voll: async function (s, a) {
        if (s.kessel) return a.gag('Der Kessel ist schon voll.');
        a.ton('wasser'); a.tausch('krug_voll', 'krug'); a.mal({ kessel: true }); return a.weiter('Der Kessel ist voll Wasser. Jetzt darf der Brenner kommen.');
      } } },
      { id: 'windrad', r: [332, 282, 96, 96], tipp: async function (s, a) {
        a.ton('flatter'); return a.gag(s.fluegel ? 'Vier Flügel, alle fest. Das Windrad wartet auf Dampf.' : 'Dem Windrad fehlt ein Flügel. So dreht es nur stotternd.');
      }, mit: {
        fluegel_k: async function (s, a) { a.ton('klick'); a.gib('fluegel_k'); a.mal({ fluegel: true }); return a.weiter('Den geflickten Flügel angeklebt – das Windrad ist wieder vollständig.'); },
        fluegel: async function (s, a) { a.ton('plumps'); return a.gag('Du steckst den Flügel an – und er fällt gleich wieder ab. Er braucht etwas zum Festkleben.'); }
      } },
      { id: 'fluegel', r: [150, 508, 92, 92], wenn: function (s) { return s.fluegelBoden; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ fluegelBoden: false }); a.nimm('fluegel'); return a.weiter('Ein abgebrochener Flügel vom Windrad.');
      } },
      { id: 'lampe', r: [96, 404, 92, 96], tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.birne ? 'Die Birne sitzt in der Lampe. Wenn sie leuchtet, wird der Ballon warm.' : 'Die Lampe unter dem Papierballon hat keine Birne.');
      }, mit: { birne: async function (s, a) { a.ton('klick'); a.gib('birne'); a.mal({ birne: true }); return a.weiter('Die Glühbirne – wie die neue im Leuchtturm – sitzt in der Lampe.'); } } },
      { id: 'lade', r: [690, 504, 108, 92], tipp: async function (s, a) {
        if (s.schublade) { a.ton('knarr'); a.mal({ schublade: false }); a.nimm('birne'); return a.weiter('In der Schublade der Werkbank: eine Glühbirne.'); }
        a.ton('knarr'); return a.gag('Die Schublade ist leer bis auf eine Schraube und einen Zettel mit «Geburtstag!!!».');
      } },
      { id: 'klebeband', r: [664, 410, 96, 94], wenn: function (s) { return s.band; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ band: false }); a.nimm('band'); return a.weiter('Eine Rolle Klebeband. Klebt fast alles.');
      } },
      { id: 'hahn', r: [500, 466, 124, 96], tipp: async function (s, a) {
        a.ton('wasser'); return a.gag('Der Wasserhahn rauscht. Ohne Gefäss läuft das Wasser einfach in den Abfluss.');
      }, mit: {
        krug: async function (s, a) { a.ton('wasser'); a.tausch('krug', 'krug_voll'); return a.weiter('Der Krug ist voll Wasser.'); },
        krug_voll: async function (s, a) { return a.gag('Der Krug ist schon voll.'); }
      } },
      { id: 'krugB', r: [604, 504, 92, 96], wenn: function (s) { return s.krug === 'boden'; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ krug: 'tasche' }); a.nimm('krug'); return a.weiter('Ein leerer Glaskrug.');
      } },
      { id: 'obst', r: [388, 496, 100, 96], tipp: async function (s, a) {
        if (s.obst) { a.ton('plopp'); a.mal({ obst: false }); a.nimm('apfel'); return a.weiter('Ein roter Apfel – so einen mochte schon der Igel im Garten.'); }
        a.ton('plopp'); return a.gag('Nur noch eine Banane. Die rollt nicht, die schaukelt.');
      } },
      { id: 'plan', r: [132, 14, 196, 96], tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('plan');
        if (!s.plan) { a.mal({ plan: true }); return a.weiter('Der Bauplan zeigt die ganze Kette, von der Kugel bis zur Krone – und wo Wasser hinein muss. Steht im Notizbuch.'); }
        return a.gag('Kugel, Rinne, Dominos, Giesskanne, Trichter, Eimer, Klappe, Wippe, Kessel, Windrad, Kuckuck, Knopf, Lampe, Ballon, Krone.');
      } },
      { id: 'glas', r: [372, 24, 96, 92], tipp: async function (s, a) {
        a.ton('huch'); await a.anim('#geist', [{ opacity: 0.5, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(-16px)' }, { opacity: 1, transform: 'translateY(-16px)' }, { opacity: 0.5, transform: 'translateY(0)' }], 1500);
        return a.geheim('Im Einmachglas wohnt das kleine Gespenst vom Dachboden. Hier ist es endlich schön ruhig – meistens.');
      } },
      { id: 'badeente', r: [494, 14, 96, 92], tipp: async function (s, a) {
        a.ton('quak'); return a.gag('Quietsch! Die Badeente aus dem U-Boot hat hier Urlaub gemacht.');
      } },
      { id: 'kuckuck', r: [222, 240, 96, 100], tipp: async function (s, a) {
        a.ton('kuckuck'); return a.gag('Die Kuckucksuhr ist noch zu. Wenn sich das Windrad dreht, zieht die Schnur ihr Türchen auf.');
      } },
      { id: 'knopf2', r: [222, 342, 96, 92], tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.birne ? 'Klick – die Lampe leuchtet kurz auf. Den Knopf drückt gleich der Kuckuck.' : 'Klick – nichts. Der Knopf schaltet die Lampe ein, aber die hat keine Birne.');
      } },
      { id: 'ballon', r: [92, 292, 96, 96], tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Ein Papierballon. Warme Luft steigt nach oben – dann zieht er an der Schnur zum Kronenregal.');
      } },
      { id: 'kroneRegal', r: [12, 198, 96, 92], tipp: async function (s, a) {
        a.ton('glocke'); return a.gag('Die Krone aus dem Museum – geliehen für den Geburtstag. Sie soll ganz am Schluss auf den Kopf des Erfinders rutschen.');
      } },
      { id: 'erfinder', r: [222, 462, 140, 100], tipp: async function (s, a) {
        a.ton('schnarch'); return a.gag(['Der Erfinder schnarcht: «Noch fünf Minuten …» Heute ist sein Geburtstag.', 'Er murmelt im Schlaf: «Erst alles reparieren, dann Start …»'][(a.nr - 1) % 2]);
      } },
      { id: 'wippe', r: [548, 380, 112, 92], tipp: async function (s, a) {
        a.ton('knarr'); return a.gag('Eine Wippe. Wenn der Apfel auf das tiefe Ende rollt, schnippt das andere hoch – an den Brenner.');
      } },
      { id: 'turbo', r: [708, 10, 92, 92], tipp: async function (s, a) {
        a.ton('radio'); return a.gag(a.nr % 2 ? 'TURBO! Das Radio des Erfinders spielt jetzt doppelt so schnell. Sonst passiert nichts.' : 'Turbo aus. Das Radio spielt wieder normal. Ein Knopf für nichts – typisch Erfinder.');
      } }
    ],
    naechster: function (s) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (!s.plan) return 'plan';
      if (!s.brett) return hat('brett') ? { stelle: 'luecke', ding: 'brett' } : 'brett';
      if (!s.domino) return 'domino';
      if (!s.giess) return hat('krug_voll') ? { stelle: 'giess', ding: 'krug_voll' } : hat('krug') ? { stelle: 'hahn', ding: 'krug' } : 'krugB';
      if (s.socke) return 'trichter';
      if (!s.rolle) return 'rolle';
      if (!s.apfel) return hat('apfel') ? { stelle: 'klappe', ding: 'apfel' } : 'obst';
      if (!s.kessel) return hat('krug_voll') ? { stelle: 'kessel', ding: 'krug_voll', wink: 'Der Bauplan: Kessel (Wasser!).' } : { stelle: 'hahn', ding: 'krug' };
      if (!s.fluegel) return hat('fluegel_k') ? { stelle: 'windrad', ding: 'fluegel_k' } : hat('fluegel') && hat('band') ? { kombi: ['fluegel', 'band'] } : s.fluegelBoden ? 'fluegel' : 'klebeband';
      if (!s.birne) return hat('birne') ? { stelle: 'lampe', ding: 'birne' } : 'lade';
      return 'start';
    }
  });
})();
