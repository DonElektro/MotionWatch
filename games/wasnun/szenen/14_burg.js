/* Bild 14 «Die Burg im Nebel» (Meister+): vier Räume (Torhaus, Turm, Keller, Burggraben), die Zugbrücke herunterlassen.
   Die Kette ist von der Trommel der Winde durchs Kettenloch in den Graben gerutscht; die Brücke hält nur noch der Riegel.
   Lösung: Torhaus: Tafel lesen (erst Kette auf die Trommel, dann Riegel, dann kurbeln) · Brot aus dem Korb der Wache
   (wird erst im letzten Raum gebraucht) · Keller: Messer aus dem Käselaib · Rad am Wassertor (Gitter hoch) ·
   Burggraben: das Brot dem Schwan zuwerfen (er schwimmt weg, unter seinem Nest liegt ein alter Anker) · Anker ·
   Turm: mit dem Messer das Glockenseil abschneiden · Seil + Anker = Enterhaken · Torhaus: Enterhaken durchs Kettenloch
   (die Kette kommt herauf auf die Trommel) · Riegel ziehen · Winde kurbeln.
   Sackgassen: den Riegel ziehen, bevor die Kette auf der Trommel liegt · die Kanone im Turm abfeuern. */
(function () {
  var Z = WASNUN.Z;
  var G = { 0: { 1: 'zuTurm', 2: 'zuKeller' }, 1: { 0: 'turmRunter' }, 2: { 0: 'kellerHoch', 3: 'zumGraben' }, 3: { 2: 'grabenZurueck' } };
  function weg(s, raum) {
    if (raum === 3 && !s.gitter) return s.raum === 2 ? 'gitterrad' : WASNUN.weg(G, s.raum, 2);
    return WASNUN.weg(G, s.raum, raum);
  }
  function geh(s, raum, ziel) { return s.raum === raum ? ziel : { stelle: weg(s, raum), tuer: true }; }
  var BROT = '<path class="l" fill="#d9a35a" d="M-24 6q-4 -22 24 -24q28 2 24 24q-24 10 -48 0z"/><path class="d n" style="stroke:#a86f2a" d="M-12 -8l6 8M0 -12l6 8M12 -8l6 8"/>';
  var MESSER = '<g transform="rotate(-30)"><path class="l" fill="#c9ced6" d="M-4 -26q10 6 8 24h-8z"/><rect class="l" x="-6" y="-2" width="12" height="26" rx="3" fill="#8a5a3a"/></g>';
  var SEIL = '<path class="l n" style="stroke:#c99562;stroke-width:6" d="M-18 -10q18 -18 30 -2t-24 14q10 20 30 6"/><path class="n" stroke="#8a5a3a" stroke-width="2" stroke-dasharray="3 4" d="M-18 -10q18 -18 30 -2t-24 14q10 20 30 6"/>';
  var ANKER = '<path class="l n" style="stroke:#5b6470;stroke-width:6" d="M0 -22v40M-12 -12h24M-20 4q4 18 20 18t20 -18"/><circle class="l n" cx="0" cy="-26" r="5" style="stroke:#5b6470;stroke-width:4"/><path class="l" fill="#5b6470" d="M-24 0l8 6l-10 4zM24 0l-8 6l10 4z"/>';
  var HAKEN = '<g transform="translate(6 6) scale(.8)">' + ANKER + '</g><path class="l n" style="stroke:#c99562;stroke-width:5" d="M6 -14q-10 -10 -22 -4t-8 18"/>';
  function stein(f, g) {      // Steinwand
    var h = '<rect width="800" height="600" fill="' + f + '"/>';
    for (var y = 0, r = 0; y < 600; y += 46, r++) for (var x = (r % 2) * -40; x < 800; x += 80) h += '<rect x="' + (x + 2) + '" y="' + (y + 2) + '" width="76" height="42" rx="6" fill="' + g + '"/>';
    return h;
  }
  function nebel(o) { return '<g class="a-schweb" opacity="' + (o || 0.5) + '"><path fill="#e6ecf2" d="M-20 300q120 -40 240 0t240 0t240 0t140 0v60h-860z"/><path fill="#e6ecf2" d="M-20 420q140 -30 280 0t280 0t280 0v40h-840z" opacity=".7"/></g>'; }
  function baecker(x, y, k) {
    return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><path class="l" fill="#f6f1e6" d="M-22 0q-4 -50 22 -52q26 2 22 52z"/><circle class="l" cy="-66" r="16" fill="#f3c9a5"/><path class="l" fill="#fff" d="M-16 -76q-8 -20 8 -22q8 -10 16 0q16 2 8 22z"/>' + Z.auge(-5, -66, 3) + Z.auge(5, -66, 3)
      + '<path class="l n" d="M-6 -58q6 4 12 0"/><path class="l" fill="#9a6b43" d="M18 -30h34l-4 22h-26z"/><path class="l" fill="#d9a35a" d="M22 -36q8 -8 14 0zM34 -36q8 -8 14 0z"/></g>';
  }
  WASNUN.szene({
    id: 'burg', titel: 'Die Burg im Nebel', stufe: 5,
    raeume: ['Torhaus', 'Turm', 'Keller', 'Burggraben'],
    ziel: 'Im Nebel vor der Burg wartet der Bäcker mit frischem Brot – aber die Zugbrücke ist oben und die Kette der Winde verschwunden. Lass die Brücke herunter!',
    start: function () { return { tasche: [], raum: 0, tafel: false, brot: 'korb', messer: 'kaese', gitter: false, schwan: 'nest', anker: 'grund', seil: 'glocke', kette: 'graben', riegel: true, bruecke: 'oben' }; },
    tuer: function (s, raum) { return weg(s, raum); },
    notizen: {
      tafel: { titel: 'Tafel im Torhaus', text: '«Zugbrücke: 1. Kette auf die Trommel. 2. Riegel ziehen. 3. Langsam kurbeln. NIE den Riegel zuerst!»' },
      kette: { titel: 'Die Kette', text: 'Die Kette ist durchs Kettenloch nach draussen gerutscht und hängt in den Burggraben.' }
    },
    dinge: {
      brot: { name: 'Brotlaib', svg: '<g transform="translate(30 32)">' + BROT + '</g>' },
      messer: { name: 'Käsemesser', svg: '<g transform="translate(30 30)">' + MESSER + '</g>' },
      seil: { name: 'Glockenseil', svg: '<g transform="translate(28 30)">' + SEIL + '</g>' },
      anker: { name: 'Alter Anker', svg: '<g transform="translate(30 30)">' + ANKER + '</g>' },
      haken: { name: 'Enterhaken', svg: '<g transform="translate(30 30)">' + HAKEN + '</g>' }
    },
    kombi: [{ a: 'seil', b: 'anker', gibt: 'haken', text: 'Das Seil fest an den Ring des Ankers geknotet: ein Enterhaken! Damit lässt sich etwas aus der Tiefe heraufholen.' },
      { a: 'messer', b: 'brot', nein: 'Brot schneiden? Der Bäcker bringt gleich frisches. Dieses hier braucht noch jemand anderes.' },
      { a: 'messer', b: 'seil', nein: 'Das Seil noch kürzer schneiden? Lieber nicht, es wird noch gebraucht – und zwar lang.' }],
    nutzlos: function (s, d) {
      if (d === 'brot') return 'Das Brot isst du lieber nicht selbst. Jemand im Burggraben hat bestimmt Hunger.';
      if (d === 'anker') return 'Ein Anker allein ist schwer und kurz. Mit einem langen Seil daran wäre er viel nützlicher.';
      return '';
    },
    bild: function (s) {
      var h, R = s.raum, x, y, r;
      if (R === 0) {      // ---- Torhaus ----
        h = stein('#5a5560', '#6b6672') + '<rect class="l" x="-5" y="540" width="810" height="70" fill="#4a3f38"/>';
        h += '<path class="l" fill="#3a3340" d="M560 540V180a110 110 0 0 1 220 0v360z"/>';
        if (s.bruecke === 'unten') h += '<path fill="#bfcad6" d="M566 540V180a104 104 0 0 1 208 0v360z"/>' + nebel(0.8) + '<path class="l" fill="#9a6b43" d="M566 540l40 -120h128l40 120z"/>' + baecker(670, 470, 0.9);
        else { h += '<g id="bruecke" style="transform-origin:670px 540px"><path class="l" fill="#9a6b43" d="M566 540V184a104 104 0 0 1 208 0v356z"/>'; for (x = 586; x < 770; x += 32) h += '<path class="d n" style="stroke:#6b4a34" d="M' + x + ' 120v420"/>'; h += '<path class="l n" style="stroke:#3a3340;stroke-width:8" d="M566 250h208M566 450h208"/></g>'; }
        h += '<g id="loch"><rect class="l" x="596" y="56" width="48" height="40" rx="8" fill="#1c1a22"/>' + (s.kette === 'trommel' ? '<path class="l n" style="stroke:#8d98a8;stroke-width:6;stroke-dasharray:8 4" d="M620 96L470 330"/>' : '') + '</g>';
        if (s.bruecke !== 'unten') h += '<g id="riegel"><rect class="l" x="' + (s.riegel ? 540 : 470) + '" y="300" width="250" height="26" rx="6" fill="#5b6470"/><rect class="l" x="' + (s.riegel ? 580 : 510) + '" y="288" width="20" height="50" rx="4" fill="#3a3f4c"/><path class="l n" style="stroke:#3a3f4c;stroke-width:8" d="M548 290v46"/></g>';
        h += '<g id="winde"><path class="l n" style="stroke:#6b4a34;stroke-width:14" d="M300 540L330 390M480 540L450 390"/><rect class="l" x="300" y="340" width="180" height="96" rx="20" fill="#9a6b43"/>'
          + (s.kette === 'trommel' ? '<path class="d n" style="stroke:#8d98a8;stroke-width:6" d="M310 356h160M310 372h160M310 388h160M310 404h160M310 420h160"/>' : '<path class="d n" style="stroke:#6b4a34" d="M330 340v96M390 340v96M450 340v96"/>')
          + '<g id="kurbel" style="transform-origin:490px 388px"><path class="l n" style="stroke:#5b6470;stroke-width:10" d="M480 388h20v-50h24"/><circle class="l" cx="530" cy="338" r="9" fill="#d64b3c"/></g><circle class="l" cx="490" cy="388" r="12" fill="#5b6470"/></g>';
        h += '<g id="tafel"><rect class="l" x="120" y="160" width="140" height="120" rx="6" fill="#3a2d20"/><rect class="l" x="130" y="170" width="120" height="100" rx="3" fill="#2f3f35"/>'
          + Z.text(190, 192, '1. Kette', { k: 13, f: '#f6efd8' }) + Z.text(190, 216, '2. Riegel', { k: 13, f: '#f6efd8' }) + Z.text(190, 240, '3. Kurbeln', { k: 13, f: '#f6efd8' }) + Z.text(190, 262, 'NIE zuerst 2!', { k: 11, f: '#ffd23f' }) + '</g>'
          + '<g id="fackel"><path class="l n" style="stroke:#3a3340;stroke-width:6" d="M500 196l12 30"/><path class="l" fill="#8a5a3a" d="M496 200l8 -4l-6 -40l-8 4z"/><g class="fuss a-flack"><path class="l" fill="#f2711c" d="M494 160q-18 -10 -8 -30q6 8 8 4q0 -16 12 -22q-2 14 8 20q6 20 -20 28z"/></g></g>'
          + '<g id="hellebarde"><path class="l n" style="stroke:#8a5a3a;stroke-width:7" d="M292 300V110"/><path class="l" fill="#c9ced6" d="M292 110l-6 30h12zM298 132q30 10 30 34q-20 -6 -30 -6z"/></g>'
          + '<g id="korb"><path class="l" fill="#8a5a3a" d="M140 470h150v12h-150z"/><path class="l n" style="stroke:#6b4a34;stroke-width:6" d="M150 482v58M280 482v58"/><path class="l" fill="#c99562" d="M180 470l8 -38h64l8 38z"/><path class="l n" style="stroke:#8a5a3a;stroke-width:4" d="M196 432q24 -30 48 0"/>'
          + (s.brot === 'korb' ? '<g transform="translate(220 432) scale(.8)">' + BROT + '</g>' : '') + '<path class="d" fill="#f6f1e6" d="M240 432l10 -8l6 10z"/></g>';
        h += Z.tuer(60, 110, 'o', 'pTurm') + Z.tuer(60, 520, 'u', 'pKeller');
        return h;
      }
      if (R === 1) {      // ---- Turm ----
        h = stein('#6b6672', '#7a7682') + '<rect class="l" x="-5" y="550" width="810" height="60" fill="#4a3f38"/>';
        h += '<g id="fenster"><path class="l" fill="#bfcad6" d="M120 360V230a70 70 0 0 1 140 0v130z"/><g transform="translate(-40 0)">' + baecker(230, 340, 0.6) + '</g><path fill="#e6ecf2" opacity=".7" d="M124 320q30 -10 60 0t70 0v40h-130z"/></g>';
        h += '<rect class="l" x="250" y="60" width="380" height="30" fill="#6b4a34"/><g id="glocke" class="kopf"><path class="l n" d="M400 90v16"/><path class="l" fill="#e9a23b" d="M350 236q4 -130 50 -130t50 130z"/><path class="l" fill="#b98a00" d="M340 236h120v14h-120z"/><circle class="l" cx="400" cy="262" r="10" fill="#b98a00"/></g>';
        if (s.seil === 'glocke') h += '<g id="seil"><path class="l n" style="stroke:#c99562;stroke-width:7" d="M540 90q10 120 -2 240"/><circle class="l" cx="540" cy="100" r="12" fill="#c99562"/><path class="l n" style="stroke:#c99562;stroke-width:7" d="M400 252q60 -20 140 -150"/></g>';
        else h += '<path class="l n" style="stroke:#c99562;stroke-width:7" d="M540 90v18"/><circle class="l" cx="540" cy="100" r="12" fill="#c99562"/>';
        h += '<g id="rabe"><path class="l" fill="#8a5a3a" d="M640 176q50 18 100 0q-6 20 -50 22q-44 -2 -50 -22z"/><g transform="translate(690 150)"><ellipse class="l" rx="22" ry="18" fill="#3a3340"/><path class="l" fill="#f2a900" d="M18 -4l16 6l-16 4z"/>' + Z.auge(8, -6, 5) + '</g></g>';
        h += '<rect class="l" x="560" y="300" width="240" height="80" fill="#4a4652"/><path fill="#bfcad6" d="M600 304h60v40h-60zM700 304h60v40h-60z"/><g id="kanone"><path class="l" fill="#3a3f4c" d="M560 450l200 -90l14 30l-196 92z"/><circle class="l" cx="600" cy="470" r="34" fill="#6b4a34"/><circle class="l" cx="600" cy="470" r="10" fill="#3a3340"/></g>'
          + '<g id="kugeln"><circle class="l" cx="420" cy="534" r="16" fill="#3a3f4c"/><circle class="l" cx="452" cy="534" r="16" fill="#3a3f4c"/><circle class="l" cx="436" cy="508" r="16" fill="#3a3f4c"/></g>';
        h += Z.tuer(60, 520, 'u', 'pRunter');
        return h;
      }
      if (R === 2) {      // ---- Keller ----
        h = stein('#3f3a44', '#4a4550') + '<rect class="l" x="-5" y="540" width="810" height="70" fill="#2b2630"/>';
        h += '<path class="l" fill="#1f4a5a" d="M600 540V300a90 90 0 0 1 180 0v240z"/><path class="n" stroke="#7fd0d6" stroke-width="3" opacity=".6" d="M620 500q20 -8 40 0t40 0t40 0"/>';
        var gx;
        if (!s.gitter) { h += '<g id="gitter">'; for (gx = 612; gx < 780; gx += 24) h += '<path class="l n" style="stroke:#3a3f4c;stroke-width:7" d="M' + gx + ' 240V540"/>'; h += '<path class="l n" style="stroke:#3a3f4c;stroke-width:7" d="M600 320h180M600 420h180"/></g>'; }
        else { h += '<g id="gitter">'; for (gx = 612; gx < 780; gx += 24) h += '<path class="l n" style="stroke:#3a3f4c;stroke-width:7" d="M' + gx + ' 200V260"/>'; h += '</g>'; }
        h += '<g id="gitterrad" class="dreh"><circle class="l n" cx="520" cy="300" r="38" style="stroke:#8a5a3a;stroke-width:8"/><path class="l n" style="stroke:#8a5a3a;stroke-width:5" d="M520 262v76M482 300h76"/><circle class="l" cx="520" cy="300" r="9" fill="#c99562"/></g><path class="l n" style="stroke:#5b6470;stroke-width:4" d="M558 300h40"/>';
        h += '<g id="fass"><ellipse class="l" cx="130" cy="300" rx="60" ry="70" fill="#8a5a3a"/><path class="d n" style="stroke:#3a3340;stroke-width:5" d="M76 270h108M76 330h108"/><circle class="l" cx="130" cy="300" r="10" fill="#6b4a34"/></g>'
          + '<g id="kaese"><path class="l" fill="#ffd23f" d="M190 520q0 -40 70 -40t70 40v14q-70 20 -140 0z"/><ellipse class="l" cx="260" cy="484" rx="70" ry="16" fill="#ffe14a"/><circle cx="230" cy="510" r="6" fill="#d99a00"/><circle cx="292" cy="516" r="5" fill="#d99a00"/>'
          + (s.messer === 'kaese' ? '<g transform="translate(276 462) rotate(20)"><path class="l" fill="#c9ced6" d="M-4 -10q10 6 8 30h-8z"/><rect class="l" x="-6" y="-36" width="12" height="28" rx="3" fill="#8a5a3a"/></g>' : '') + '</g>'
          + '<g id="schinken" class="kopf"><path class="l n" style="stroke-width:3" d="M380 60v40"/><path class="l n" style="stroke:#5b6470;stroke-width:4" d="M380 100q-10 6 0 12"/><path class="l" fill="#d9776a" d="M360 116q20 -10 40 0q14 60 -20 86q-34 -26 -20 -86z"/><ellipse cx="380" cy="190" rx="10" ry="8" fill="#f6f1e6"/></g>'
          + '<g id="kerze"><rect class="l" x="232" y="236" width="16" height="36" fill="#f6efd8"/><g class="fuss a-flack"><path class="d" fill="#ffd23f" d="M240 236q-8 -6 0 -18q8 12 0 18z"/></g><circle cx="240" cy="226" r="40" fill="#ffd98a" opacity=".12"/></g>'
          + '<g id="ratte"><g transform="translate(410 540)"><path class="l n" style="stroke:#d9a0a6;stroke-width:3" d="M20 -6q20 0 30 -14"/><ellipse class="l" cx="0" cy="-12" rx="24" ry="14" fill="#8d8793"/><circle class="d" cx="-18" cy="-22" r="7" fill="#8d8793"/>' + Z.auge(-22, -14, 3) + '<circle cx="-28" cy="-10" r="3" fill="#e2787a"/></g></g>';
        h += Z.tuer(60, 110, 'o', 'pHoch') + (s.gitter ? Z.tuer(740, 470, 'r', 'pGraben') : '');
        return h;
      }
      // ---- Burggraben ----
      h = '<rect width="800" height="600" fill="#bfcad6"/><path fill="#9aa8b8" d="M0 0h340v400h-340z"/>';
      for (y = 0, r = 0; y < 400; y += 46, r++) for (x = (r % 2) * -40; x < 340; x += 80) h += '<rect x="' + (x + 2) + '" y="' + (y + 2) + '" width="76" height="42" rx="6" fill="#aab6c6"/>';
      h += '<path class="l n" style="stroke:#7a8696;stroke-width:4" d="M340 0v400"/>';
      h += '<g id="hbruecke"><rect class="l" x="130" y="80" width="170" height="250" rx="6" fill="#9a6b43"/><path class="d n" style="stroke:#6b4a34" d="M160 80v250M190 80v250M220 80v250M250 80v250M280 80v250"/></g>'
        + '<rect class="l" x="60" y="50" width="40" height="34" rx="6" fill="#1c1a22"/>' + (s.kette === 'graben' ? '<g id="kette"><path class="l n" style="stroke:#5b6470;stroke-width:7;stroke-dasharray:9 5" d="M80 84q-6 200 4 380"/></g>' : '');
      h += '<path class="l" fill="#1f4a5a" d="M14 404v-56a46 46 0 0 1 92 0v56z"/><path class="l n" style="stroke:#3a3f4c;stroke-width:5" d="M30 310v-20M54 302v-14M78 310v-20"/>';
      h += '<path fill="#5a7a8a" d="M0 400h800v200h-800z"/><path class="n" stroke="#bfe6ff" stroke-width="3" opacity=".6" d="M40 440q20 -8 40 0M520 470q20 -8 40 0M640 520q20 -8 40 0M200 560q20 -8 40 0"/>';
      h += '<path class="l" fill="#7a9a6a" d="M520 400q60 -60 290 -70v80h-290z"/><g id="baecker">' + baecker(660, 360, 0.9) + '</g><g transform="translate(730 350)"><rect class="l" x="-24" y="-36" width="60" height="30" rx="4" fill="#c99562"/><circle class="l" cx="-10" cy="-2" r="10" fill="#5b3a2e"/><circle class="l" cx="24" cy="-2" r="10" fill="#5b3a2e"/></g>';
      h += '<g id="ungeheuer" opacity="0"><g transform="translate(560 500)"><path class="l" fill="#57b04f" d="M-20 20q0 -60 20 -70q24 -6 26 20q-10 0 -16 6q-6 20 -6 44z"/>' + Z.auge(8, -38, 5) + '<path class="l" fill="#57b04f" d="M10 20q20 -20 40 0z"/></g></g>';
      if (s.anker === 'grund') h += '<g id="anker"><g transform="translate(410 520) scale(1.5)">' + ANKER + '</g></g>';
      h += '<g id="schwan"><g transform="translate(' + (s.schwan === 'nest' ? 410 : 690) + ' 470)">' + (s.schwan === 'nest' ? '<path class="l" fill="#9a6b43" d="M-56 30q56 30 112 0q-6 -30 -56 -30t-56 30z"/>' : '')
        + '<path class="l" fill="#fff" d="M-40 10q-10 -36 40 -40q40 0 40 30q-20 24 -80 10z"/><path class="l n" style="stroke:#fff;stroke-width:12" d="M28 -18q12 -40 -10 -56"/><path class="l n" style="stroke-width:3" d="M28 -18q12 -40 -10 -56"/><circle class="l" cx="14" cy="-74" r="11" fill="#fff"/><path class="l" fill="#f2711c" d="M4 -76l-16 4l16 6z"/><circle cx="12" cy="-77" r="2.5" fill="#3a3340"/></g></g>'
        + (s.brot === 'schwan' ? '<g transform="translate(640 492) scale(.6)">' + BROT + '</g>' : '');
      h += '<g id="frosch"><g transform="translate(250 560)"><ellipse class="l" rx="22" ry="14" fill="#57b04f"/>' + Z.auge(-8, -12, 5) + Z.auge(8, -12, 5) + '<path class="l n" d="M-8 2q8 6 16 0"/></g></g>';
      h += nebel(0.55) + Z.tuer(60, 540, 'l', 'pZurueck');
      return h;
    },
    stellen: [
      // ---- Türen ----
      { id: 'zuTurm', r: [12, 62, 96, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 1 }); return a.wechsel('Die Wendeltreppe hinauf in den Turm.'); } },
      { id: 'zuKeller', r: [12, 472, 96, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 2 }); return a.wechsel('Hinunter in den feuchten Keller.'); } },
      { id: 'turmRunter', r: [12, 472, 96, 96], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 0 }); return a.wechsel('Zurück ins Torhaus.'); } },
      { id: 'kellerHoch', r: [12, 62, 96, 96], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 0 }); return a.wechsel('Hinauf ins Torhaus.'); } },
      { id: 'zumGraben', r: [692, 422, 96, 96], wenn: function (s) { return s.raum === 2 && s.gitter; }, tipp: async function (s, a) { a.ton('platsch'); a.mal({ raum: 3 }); return a.wechsel('Durchs Wassertor hinaus auf den schmalen Steg am Burggraben. Nebel überall.'); } },
      { id: 'grabenZurueck', r: [12, 492, 96, 96], wenn: function (s) { return s.raum === 3; }, tipp: async function (s, a) { a.ton('platsch'); a.mal({ raum: 2 }); return a.wechsel('Zurück in den Keller.'); } },
      // ---- Torhaus ----
      { id: 'loch', r: [570, 30, 100, 92], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('tap'); a.notiz('kette');
        return a.gag(s.kette === 'trommel' ? 'Die Kette läuft jetzt wieder durchs Kettenloch zur Trommel.' : 'Das Kettenloch. Die Kette ist hindurch nach draussen gerutscht und hängt unten in den Graben – von hier oben viel zu tief für die Hand.');
      }, mit: {
        haken: async function (s, a) {
          a.ton('platsch'); await a.warte(500); a.ton('metall'); a.gib('haken'); a.mal({ kette: 'trommel' });
          return a.weiter('Du lässt den Enterhaken durchs Kettenloch hinunter, angelst die Kette und ziehst sie herauf – rasselnd legt sie sich auf die Trommel.');
        },
        seil: async function (s, a) { a.ton('tap'); return a.gag('Das Seil baumelt durchs Loch, aber die Kette bleibt nicht daran hängen. Vorne fehlt ein Haken.'); },
        anker: async function (s, a) { a.ton('metall'); return a.gag('Den Anker allein durchs Loch werfen? Weg wäre er. Er braucht ein Seil.'); }
      } },
      { id: 'riegel', r: [530, 270, 260, 92], wenn: function (s) { return s.raum === 0 && s.bruecke !== 'unten'; }, tipp: async function (s, a) {
        if (!s.riegel) { a.ton('klick'); return a.gag('Der Riegel ist schon offen. Jetzt hält nur noch die Kette die Brücke.'); }
        a.ton('metall'); a.mal({ riegel: false });
        if (s.kette !== 'trommel') {
          await a.anim('#bruecke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(4deg)' }], 400); a.ton('knarr'); await a.warte(300);
          return a.sackgasse('Der Riegel rutscht – und die Brücke kippt gefährlich nach aussen! Ohne Kette würde sie in den Graben krachen. Schnell, Riegel wieder rein!');
        }
        return a.weiter('Klack – der Riegel ist offen. Die Brücke hängt jetzt an der Kette.');
      } },
      { id: 'winde', r: [292, 320, 248, 140], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (s.bruecke === 'unten') return a.gag('Die Brücke liegt unten.');
        if (s.kette !== 'trommel') { a.ton('knarr'); a.notiz('kette'); return a.gag('Die Trommel der Winde ist leer: Die Kette ist durchs Kettenloch nach draussen gerutscht.'); }
        if (s.riegel) { a.ton('klick'); return a.gag('Die Kurbel dreht sich nicht – solange der Riegel steckt, ist alles blockiert.'); }
        a.ton('knarr'); a.anim('#kurbel', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-720deg)' }], 1400, { easing: 'linear' });
        await a.anim('#bruecke', [{ transform: 'scaleY(1)', opacity: 1 }, { transform: 'scaleY(.2)', opacity: 0.2 }], 1400);
        a.mal({ bruecke: 'unten' }); a.ton('plumps');
        return a.fertig('Langsam senkt sich die Zugbrücke in den Nebel. Der Bäcker rollt seinen Karren herein: «Frische Brötchen für die ganze Burg!»');
      } },
      { id: 'tafel', r: [116, 156, 148, 128], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('tafel');
        if (!s.tafel) { a.mal({ tafel: true }); return a.weiter('Auf der Tafel: «1. Kette auf die Trommel. 2. Riegel ziehen. 3. Langsam kurbeln. NIE den Riegel zuerst!» Steht im Notizbuch.'); }
        return a.gag('1. Kette, 2. Riegel, 3. Kurbeln.');
      } },
      { id: 'korb', r: [150, 400, 140, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (s.brot === 'korb') { a.ton('plopp'); a.mal({ brot: 'tasche' }); a.nimm('brot'); return a.weiter('Im Korb der Torwache liegt ein Brotlaib. Die Wache ist wohl selbst zum Bäcker gegangen.'); }
        a.ton('plopp'); return a.gag('Im Korb ist nur noch ein Apfelbutzen.');
      } },
      { id: 'fackel', r: [466, 112, 96, 112], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('zisch'); return a.gag('Die Fackel knistert. Brücke anzünden? Lieber nicht – sie soll ja noch halten.');
      } },
      { id: 'hellebarde', r: [246, 100, 96, 200], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('metall'); return a.gag('Eine Hellebarde, scharf und schwer. Damit die Kette angeln? Zu kurz, und ohne Haken.');
      } },
      { id: 'bruecke', r: [560, 130, 220, 140], wenn: function (s) { return s.raum === 0 && s.bruecke !== 'unten'; }, tipp: async function (s, a) {
        a.ton('knarr'); return a.gag('Die Zugbrücke ist hochgeklappt. Von draussen ruft der Bäcker: «Huhu! Ist jemand da?»');
      } },
      // ---- Turm ----
      { id: 'seil', r: [492, 120, 100, 220], wenn: function (s) { return s.raum === 1 && s.seil === 'glocke'; }, tipp: async function (s, a) {
        a.ton('glocke'); await a.anim('#glocke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(12deg)' }, { transform: 'rotate(-10deg)' }, { transform: 'rotate(0deg)' }], 800);
        return a.gag('Bimmm! Das Glockenseil ist oben am Balken mit einem dicken Knoten festgemacht. Aufknoten unmöglich.');
      }, mit: {
        messer: async function (s, a) { a.ton('klick'); a.mal({ seil: 'tasche' }); a.nimm('seil'); return a.weiter('Ritsch – du schneidest das lange Glockenseil ab. Die Glocke läutet zum Abschied.'); }
      } },
      { id: 'glocke', r: [336, 100, 128, 170], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('glocke'); return a.gag('Dong! Aus dem Nebel ruft der Bäcker: «Ich höre euch! Macht doch auf!»');
      } },
      { id: 'kanone', r: [550, 380, 220, 130], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('plumps'); a.ton('puff'); await a.anim('#kanone', [{ transform: 'translateX(0)' }, { transform: 'translateX(-20px)' }, { transform: 'translateX(0)' }], 400); await a.warte(400);
        return a.sackgasse('BUMM! Die Kanone donnert in den Nebel. Draussen schreit der Bäcker auf und lässt vor Schreck den ganzen Korb fallen. So lädt man keinen Gast ein!');
      } },
      { id: 'rabe', r: [636, 112, 112, 96], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('kraechz'); return a.gag('Der Burgrabe krächzt: «Graben! Graben!» Er weiss offenbar mehr als du.');
      }, mit: {
        brot: async function (s, a) { a.ton('kraechz'); return a.gag('Der Rabe pickt einmal und spuckt aus. «Krah! Zu hart! Gib das den Schwänen!»'); }
      } },
      { id: 'kugeln', r: [390, 478, 100, 92], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('plumps'); return a.gag('Kanonenkugeln, schwer wie Kürbisse. Die rollen nirgends hin.');
      } },
      { id: 'fenster', r: [120, 160, 140, 200], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('huch'); return a.gag('Tief unten im Nebel wartet der Bäcker mit seinem Karren und winkt hinauf.');
      } },
      // ---- Keller ----
      { id: 'gitterrad', r: [470, 250, 100, 100], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#gitterrad', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(' + (s.gitter ? -270 : 270) + 'deg)' }], 900);
        a.mal({ gitter: !s.gitter }); return a.wechsel(s.gitter ? 'Rasselnd hebt sich das Gitter am Wassertor. Dahinter: der Burggraben.' : 'Das Gitter senkt sich wieder.');
      } },
      { id: 'gitter', r: [600, 230, 180, 180], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('metall'); return a.gag(s.gitter ? 'Das Wassertor ist offen. Draussen glitzert der Graben im Nebel.' : 'Ein Eisengitter vor dem Wassertor. Daneben ist ein Rad an der Wand.');
      } },
      { id: 'kaese', r: [190, 426, 140, 110], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        if (s.messer === 'kaese') { a.ton('plopp'); a.mal({ messer: 'tasche' }); a.nimm('messer'); return a.weiter('Du ziehst das Käsemesser aus dem Laib. Scharf genug für ein dickes Seil.'); }
        a.ton('plopp'); return a.gag('Ein Käselaib, so gross wie ein Wagenrad. Er riecht nach drei Jahren Keller.');
      } },
      { id: 'fass', r: [70, 222, 120, 160], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('plumps'); return a.gag('Ein Fass Apfelsaft vom Burgherrn. Plopp – der Zapfen hält.');
      } },
      { id: 'schinken', r: [332, 60, 96, 150], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#schinken', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(-10deg)' }, { transform: 'rotate(0deg)' }], 900);
        return a.gag('Der Schinken schaukelt am Haken. Die Ratte schaut ihm sehnsüchtig nach.');
      } },
      { id: 'kerze', r: [194, 196, 92, 96], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('zisch'); return a.gag('Die Kerze flackert. Hier unten ist es feucht und kühl.');
      } },
      { id: 'ratte', r: [362, 496, 96, 92], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('fiep'); return a.gag('Die Kellerratte fiept beleidigt: «Den Käse rührst du nicht an!» Zu spät.');
      }, mit: {
        brot: async function (s, a) { a.ton('fiep'); return a.gag('Die Ratte schnuppert, will aber lieber Käse. Und das Brot braucht jemand anderes.'); }
      } },
      // ---- Burggraben ----
      { id: 'anker', r: [350, 470, 120, 110], wenn: function (s) { return s.raum === 3 && s.anker === 'grund' && s.schwan === 'weg'; }, tipp: async function (s, a) {
        a.ton('platsch'); a.mal({ anker: 'tasche' }); a.nimm('anker'); return a.weiter('Unter dem Nest lag ein alter, rostiger Anker. Schwer – aber er hat kräftige Haken.');
      } },
      { id: 'schwan', r: function (s) { return s.schwan === 'nest' ? [330, 380, 160, 140] : [610, 380, 160, 130]; }, wenn: function (s) { return s.raum === 3; }, tipp: async function (s, a) {
        if (s.schwan === 'weg') { a.ton('quak'); return a.gag('Der Schwan knabbert zufrieden am Brot.'); }
        a.ton('zisch'); return a.gag(a.nr % 2 ? 'Zischhh! Der Schwan sitzt auf seinem Nest und faucht dich an. Unter dem Nest schaut etwas Rostiges hervor.' : 'Der Schwan breitet drohend die Flügel aus. So kommst du nicht an ihm vorbei – er müsste freiwillig wegschwimmen.');
      }, mit: {
        brot: async function (s, a) {
          a.ton('platsch'); a.gib('brot'); a.mal({ brot: 'schwan', schwan: 'weg' }); await a.anim('#schwan', [{ transform: 'translateX(-280px)' }, { transform: 'translateX(0)' }], 1200);
          return a.weiter('Du wirfst das Brot weit hinaus aufs Wasser. Der Schwan gleitet hinterher – und das Nest ist frei. Darunter: ein Anker!');
        }
      } },
      { id: 'kette', r: [34, 90, 96, 340], wenn: function (s) { return s.raum === 3 && s.kette === 'graben'; }, tipp: async function (s, a) {
        a.ton('metall'); a.notiz('kette'); return a.gag('Da hängt die Kette der Zugbrücke aus dem Kettenloch ins Wasser. Von hier unten zu hoch und zu schwer – die muss man von oben im Torhaus heraufholen.');
      } },
      { id: 'baecker', r: [610, 254, 110, 120], wenn: function (s) { return s.raum === 3; }, tipp: async function (s, a) {
        a.ton('huch'); return a.gag(['Der Bäcker ruft übers Wasser: «Die Brötchen werden kalt!»', '«Lasst doch einfach die Brücke herunter!» – Wenn es nur so einfach wäre.'][(a.nr - 1) % 2]);
      } },
      { id: 'hbruecke', r: [130, 120, 170, 210], wenn: function (s) { return s.raum === 3; }, tipp: async function (s, a) {
        a.ton('knarr'); return a.gag('Von aussen sieht man: Die Brücke hängt nur noch am Riegel. Die Kette baumelt nutzlos daneben.');
      } },
      { id: 'frosch', r: [202, 508, 96, 92], wenn: function (s) { return s.raum === 3; }, tipp: async function (s, a) {
        a.ton('quak'); return a.gag('Quak! Der Frosch hält dich für einen Prinzen. Leider nein.');
      } },
      { id: 'nebel', r: [500, 450, 110, 120], wenn: function (s) { return s.raum === 3; }, tipp: async function (s, a) {
        a.ton('platsch'); await a.anim('#ungeheuer', [{ opacity: 0, transform: 'translateY(30px)' }, { opacity: 1, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(30px)' }], 1800);
        return a.geheim('Aus dem Nebel taucht ein kleines, grünes Graben-Ungeheuer auf, winkt schüchtern und verschwindet wieder.');
      } }
    ],
    naechster: function (s) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (!s.tafel) return geh(s, 0, 'tafel');
      if (s.kette !== 'trommel') {
        if (hat('haken')) return geh(s, 0, { stelle: 'loch', ding: 'haken', wink: 'Die Kette hängt draussen unter dem Kettenloch.' });
        if (hat('seil') && hat('anker')) return { kombi: ['seil', 'anker'] };
        if (s.brot === 'korb') return geh(s, 0, 'korb');
        if (s.messer === 'kaese') return geh(s, 2, 'kaese');
        if (s.anker === 'grund') return s.schwan === 'nest' ? geh(s, 3, { stelle: 'schwan', ding: 'brot', wink: 'Schwäne mögen Brot.' }) : geh(s, 3, 'anker');
        return geh(s, 1, { stelle: 'seil', ding: 'messer' });
      }
      if (s.riegel) return geh(s, 0, 'riegel');
      return geh(s, 0, 'winde');
    }
  });
})();
