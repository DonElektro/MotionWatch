/* Bild 11 «Das U-Boot» (Meister): drei Räume (Zentrale, Torpedoraum, Maschinenraum), Wasser steigt mit der Zeit,
   Strom umleiten macht anderswo das Licht aus, ein Code aus zwei Hinweisen in zwei Räumen (Notizbuch).
   Lösung: Torpedoraum: Gummimatte · Maschinenraum: Rohrschelle · Matte + Schelle = Dichtschelle · Torpedoraum: aufs Leck
   (Reihenfolge frei, solange das Licht brennt) · Maschinenraum: Zettel am Spind («Code = unsere Tauchtiefe») ·
   Zentrale: Tiefenmesser (140 m) · Spind 1-4-0 · Griff · Keilriemen · auf die Pumpe · Zentrale: Licht Torpedoraum aus
   (der Generator schafft nur zwei Verbraucher, der Notfunk ist verplombt) · Pumpe ein · (Wasser wird abgepumpt) ·
   Auftauchen. Sackgassen: Auftauchen, solange das Leck offen ist · die Turmluke unter Wasser öffnen.
   Zeit: ohne Dichtung steigt das Wasser (gut 3 Minuten bis zur Decke); Warnung bei 65 und 85 %; voll -> zurückgespult
   auf weniger Wasser, alles Erreichte bleibt, ein Fehlversuch. */
(function () {
  var Z = WASNUN.Z, STEIG = 0.45, SINK = 7;
  var G = { 0: { 1: 'zuTorpedo', 2: 'zuMaschine' }, 1: { 0: 'zuZentrale1' }, 2: { 0: 'zuZentrale2' } };
  function pumpt(s) { return s.riemen === 'pumpe' && s.sw[2]; }
  function pegel(s, t) {
    var r = s.leck ? STEIG : pumpt(s) ? -SINK : 0;
    return Math.max(0, Math.min(100, s.w0 + r * ((t == null ? s.wt : t) - s.wt)));
  }
  function basis(s, t) { return { w0: pegel(s, t), wt: t }; }
  function geh(s, raum, ziel) { return s.raum === raum ? ziel : { stelle: WASNUN.weg(G, s.raum, raum), tuer: true }; }
  function hell(s) { return s.sw[0]; }
  var MATTE = '<rect class="l" x="-24" y="-16" width="48" height="32" rx="14" fill="#2b2b38"/><ellipse class="l" cx="18" cy="0" rx="8" ry="16" fill="#3d3d4c"/><ellipse cx="18" cy="0" rx="3" ry="8" fill="#1c1c26"/>';
  var SCHELLE = '<circle class="l n" r="18" style="stroke:#c9ced6;stroke-width:7"/><circle class="n" r="18" stroke="#8d98a8" stroke-width="2"/><rect class="l" x="14" y="-8" width="16" height="16" rx="3" fill="#8d98a8"/><path class="d n" d="M22 -8v16"/>';
  var DICHT = '<circle class="l n" r="18" style="stroke:#2b2b38;stroke-width:11"/><circle class="l n" r="18" style="stroke:#c9ced6;stroke-width:4"/><rect class="l" x="14" y="-8" width="16" height="16" rx="3" fill="#8d98a8"/>';
  var RIEMEN = '<ellipse class="l n" rx="24" ry="14" style="stroke:#2b2b38;stroke-width:7"/><ellipse class="n" rx="24" ry="14" stroke="#5b6470" stroke-width="2" stroke-dasharray="3 4"/>';
  function rumpf(s, f) {      // Innenwand des Bootes: runde Spanten, Nieten, Rohre
    var h = '<rect width="800" height="600" fill="' + f + '"/><path fill="#00000022" d="M0 0h800v70q-400 -40 -800 0zM0 600v-60q400 40 800 0v60z"/>';
    for (var x = 60; x < 800; x += 170) h += '<path class="d n" style="stroke:#00000044;stroke-width:9" d="M' + x + ' 0q-30 300 0 600"/>';
    for (x = 30; x < 800; x += 46) h += '<circle cx="' + x + '" cy="78" r="3" fill="#00000055"/><circle cx="' + x + '" cy="520" r="3" fill="#00000055"/>';
    return h + '<path class="l n" style="stroke:#8d98a8;stroke-width:10" d="M0 40h800"/><path class="l n" style="stroke:#b5652a;stroke-width:8" d="M0 58h800"/><rect class="l" x="-5" y="530" width="810" height="80" fill="#3a3f4c"/><path class="d n" style="stroke:#2b2f3a" d="M0 556h800M0 584h800M120 530v26M300 530v26M480 530v26M660 530v26M200 556v28M400 556v28M600 556v28"/>';
  }
  function bullauge(x, y, fisch) {
    return '<g transform="translate(' + x + ' ' + y + ')"><circle class="l" r="40" fill="#8d98a8"/><circle class="l" r="30" fill="#1f5a8a"/>'
      + (fisch ? '<g class="a-schweb"><path class="l" fill="' + fisch + '" d="M-14 0q12 -12 26 0q-14 12 -26 0zM-12 0l-10 -8v16z"/><circle cx="6" cy="-2" r="2.5" fill="#2b2233"/></g>' : '')
      + '<path class="n" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".4" d="M-18 -10q6 -10 16 -12"/><circle cx="-32" cy="0" r="3" fill="#5b6470"/><circle cx="32" cy="0" r="3" fill="#5b6470"/><circle cx="0" cy="-32" r="3" fill="#5b6470"/><circle cx="0" cy="32" r="3" fill="#5b6470"/></g>';
  }
  function schalter(i, an, x, y, icon) {
    return '<g id="sw' + i + '"><rect class="l" x="' + (x - 34) + '" y="' + (y - 40) + '" width="68" height="84" rx="8" fill="#5b6470"/>' + icon
      + '<rect class="l" x="' + (x - 9) + '" y="' + (y - 6) + '" width="18" height="40" rx="6" fill="#2b2233"/><rect class="l" x="' + (x - 14) + '" y="' + (an ? y - 6 : y + 14) + '" width="28" height="20" rx="5" fill="' + (an ? '#3fcf6b' : '#d64b3c') + '"/></g>';
  }
  WASNUN.szene({
    id: 'uboot', titel: 'Das U-Boot', stufe: 4,
    raeume: ['Zentrale', 'Torpedoraum', 'Maschinenraum'],
    ziel: 'Leck im Bug! Das Wasser im Torpedoraum steigt. Dichte das Leck, pump das Wasser hinaus und bring das U-Boot an die Oberfläche.',
    start: function () { return { tasche: [], raum: 0, w0: 20, wt: 0, leck: true, warn: 0, leer: false, matte: true, schelle: true, zettel: false, tiefe: false, rad: [0, 0, 0], spind: false, riemen: 'spind', sw: [true, true, false], oben: false, luke: false }; },
    tuer: function (s, raum) { return WASNUN.weg(G, s.raum, raum); },
    notizen: {
      zettel: { titel: 'Zettel am Spind (Maschinenraum)', text: '«Ersatzteile im Spind. Code = unsere Tauchtiefe.»' },
      tiefe: { titel: 'Tiefenmesser (Zentrale)', text: 'Wir liegen auf 140 m Tiefe.' },
      strom: { titel: 'Generator (Maschinenraum)', text: 'Schild: «Höchstens 2 Verbraucher gleichzeitig!»' },
      funk: { titel: 'Schalttafel (Zentrale)', text: 'Der Notfunk ist verplombt und bleibt immer an.' }
    },
    dinge: {
      matte: { name: 'Gummimatte', svg: '<g transform="translate(30 30)">' + MATTE + '</g>' },
      schelle: { name: 'Rohrschelle', svg: '<g transform="translate(26 30)">' + SCHELLE + '</g>' },
      dicht: { name: 'Dichtschelle', svg: '<g transform="translate(26 30)">' + DICHT + '</g>' },
      riemen: { name: 'Keilriemen', svg: '<g transform="translate(30 30)">' + RIEMEN + '</g>' }
    },
    kombi: [{ a: 'matte', b: 'schelle', gibt: 'dicht', text: 'Ein Stück Gummimatte in die Rohrschelle gelegt: Damit lässt sich ein Riss fest zupressen!' },
      { a: 'riemen', b: 'schelle', nein: 'Ein Keilriemen in einer Rohrschelle? Der gehört auf zwei Räder.' }],
    nutzlos: function (s, d, st) {
      if (d === 'riemen' && st !== 'pumpe') return 'Ein Keilriemen läuft über Räder. Wo gibt es hier zwei Räder ohne Riemen?';
      return '';
    },
    bild: function (s) {
      var h, R = s.raum;
      if (s.oben) {     // aufgetaucht: Blick aus der Turmluke
        h = '<rect width="800" height="600" fill="#a8dcf5"/>' + Z.sonne(640, 100) + Z.wolke(200, 90, 1.1) + '<path fill="#4aa3e8" d="M0 330h800v270h-800z"/><path class="n" stroke="#fff" stroke-width="4" stroke-linecap="round" d="M60 380q20 -12 40 0M540 420q20 -12 40 0M300 470q20 -12 40 0"/>'
          + '<path class="l" fill="#5b6470" d="M120 400q280 -60 560 0l-40 60h-480z"/><rect class="l" x="340" y="250" width="120" height="120" rx="20" fill="#6b7686"/><path class="l n" style="stroke:#3a3f4c;stroke-width:8" d="M400 250v-70"/>'
          + '<g transform="translate(400 238)"><circle class="l" r="22" fill="#f3c9a5"/><path class="l" fill="#f6f1e6" d="M-26 -12h52l-6 -18h-40z"/><rect class="l" x="-30" y="-16" width="60" height="8" fill="#3a3340"/>' + Z.auge(-8, 0, 4) + Z.auge(8, 0, 4) + '<path class="l n" d="M-10 10q10 8 20 0"/></g>'
          + '<g transform="translate(560 200)">' + Z.vogel({ f: '#f6f1e6' }) + '</g>';
        return h;
      }
      if (R === 0) {     // ---- Zentrale ----
        h = rumpf(s, '#6f8a8c') + bullauge(120, 150, '#ffd23f');
        // Sehrohr
        h += '<g id="sehrohr"><rect class="l" x="250" y="40" width="40" height="300" fill="#8d98a8"/><rect class="l" x="226" y="300" width="88" height="50" rx="12" fill="#5b6470"/><path class="l" fill="#3a3f4c" d="M232 314h24v22h-24zM284 314h24v22h-24z"/><path class="l n" style="stroke:#5b6470;stroke-width:10" d="M226 330h-22M314 330h22"/></g>';
        // Turmluke mit Leiter
        h += '<path class="l n" style="stroke:#8d98a8;stroke-width:6" d="M420 530V96M470 530V96M420 150h50M420 210h50M420 270h50M420 330h50M420 390h50M420 450h50M420 510h50"/><g id="luke"><circle class="l" cx="445" cy="78" r="44" fill="#5b6470"/><circle class="l n" cx="445" cy="78" r="26" style="stroke:#d64b3c;stroke-width:7"/><path class="l n" style="stroke:#d64b3c;stroke-width:6" d="M419 78h52M445 52v52"/></g>';
        // Tiefenmesser und Wasser-im-Bug-Anzeige
        h += '<g id="tiefe"><circle class="l" cx="130" cy="300" r="56" fill="#f6efd8"/><circle class="l n" cx="130" cy="300" r="46" style="stroke:#c9b99a"/>' + Z.text(130, 336, '140 m', { k: 17 })
          + '<path class="l n" style="stroke:#d64b3c;stroke-width:5" d="M130 300l30 -28"/><circle cx="130" cy="300" r="6" fill="#3a3340"/>' + Z.text(130, 272, 'TIEFE', { k: 11, f: '#6b5a48' }) + '</g>'
          + '<g id="pegel"><rect class="l" x="520" y="96" width="80" height="150" rx="10" fill="#3a3f4c"/><rect class="l" x="538" y="110" width="44" height="110" rx="4" fill="#1c2340"/><rect id="pegelsaeule" x="540" y="112" width="40" height="106" fill="#4aa3e8"/>'
          + '<path class="d n" style="stroke:#fff" d="M538 132h10M538 165h10M538 198h10"/>' + Z.text(560, 240, 'BUG', { k: 12, f: '#f6efd8' }) + '</g>';
        // Schalttafel: Licht Torpedoraum · Notfunk (verplombt) · Pumpe
        h += '<rect class="l" x="500" y="266" width="300" height="176" rx="10" fill="#3a3f4c"/>'
          + schalter(0, s.sw[0], 550, 364, '<path class="l" fill="#ffd23f" d="M538 318a12 12 0 1 1 24 0q0 6 -6 10h-12q-6 -4 -6 -10z"/>')
          + schalter(1, s.sw[1], 650, 364, '<path class="l n" style="stroke:#ffd23f;stroke-width:3" d="M640 318q10 -10 20 0M644 324q6 -6 12 0"/><circle cx="650" cy="329" r="3" fill="#ffd23f"/>')
          + schalter(2, s.sw[2], 750, 364, '<circle class="l" cx="750" cy="320" r="11" fill="#4aa3e8"/><path class="d n" style="stroke:#fff" d="M744 320h12M750 314v12"/>')
          + '<g transform="translate(650 425)"><rect class="l" x="-14" y="-7" width="28" height="12" rx="3" fill="#d64b3c"/><path class="d n" style="stroke:#fff" d="M-8 -1h16"/></g>';
        // Hebel «Auftauchen»
        h += '<g id="hebel"><rect class="l" x="512" y="448" width="92" height="80" rx="10" fill="#5b6470"/><path class="l" fill="#3fcf6b" d="M536 470l14 16h-8v14h-12v-14h-8z"/><rect class="l" x="570" y="458" width="14" height="60" rx="5" fill="#2b2233"/><circle class="l" cx="577" cy="462" r="12" fill="#d64b3c"/></g>';
        // Steuerrad, Kapitänin
        h += '<g id="rad" class="dreh"><circle class="l n" cx="170" cy="450" r="44" style="stroke:#9a6b43;stroke-width:9"/><path class="l n" style="stroke:#9a6b43;stroke-width:6" d="M170 406v88M126 450h88M139 419l62 62M201 419l-62 62"/><circle class="l" cx="170" cy="450" r="12" fill="#c99562"/></g>'
          + '<g id="kapitaen"><g transform="translate(330 470)"><path class="l" fill="#2f4f8a" d="M-30 60q-6 -60 30 -62q36 2 30 62z"/><circle class="l" cy="-24" r="26" fill="#f3c9a5"/><path class="l" fill="#f6f1e6" d="M-30 -36h60l-8 -18h-44z"/><rect class="l" x="-32" y="-40" width="64" height="8" fill="#3a3340"/><circle class="d" cx="0" cy="-44" r="5" fill="#ffd23f"/>'
          + Z.auge(-9, -24, 5, false, 0, -2) + Z.auge(9, -24, 5, false, 0, -2) + '<path class="l" fill="#8a5a3a" d="M-14 -10q14 -8 28 0q-6 8 -14 4q-8 4 -14 -4z"/></g></g>';
        h += Z.tuer(40, 470, 'l', 'tLinks') + Z.tuer(760, 488, 'r', 'tRechts');
        return h;
      }
      if (R === 1) {     // ---- Torpedoraum ----
        h = rumpf(s, '#7a8a6f') + bullauge(410, 150, '#f2a05a');
        h += '<g id="rohre"><rect class="l" x="30" y="160" width="230" height="330" rx="16" fill="#5b6470"/>';
        for (var i = 0; i < 2; i++) h += '<circle class="l" cx="' + (90 + i * 110) + '" cy="260" r="42" fill="#8d98a8"/><circle class="l" cx="' + (90 + i * 110) + '" cy="260" r="28" fill="#3a3f4c"/><path class="l n" style="stroke:#d64b3c;stroke-width:5" d="M' + (68 + i * 110) + ' 260h44"/>';
        h += '<rect class="l" x="56" y="340" width="178" height="40" rx="8" fill="#3a3f4c"/><circle class="l" cx="210" cy="430" r="22" fill="#d64b3c"/><circle cx="210" cy="430" r="10" fill="#ff8a8a"/></g>';
        h += '<g id="torpedo"><path class="l" fill="#aab6c6" d="M300 470h260q40 0 40 -26t-40 -26h-260z"/><path class="l" fill="#d64b3c" d="M300 418l-34 -16v84l34 -16z"/><path class="d n" d="M520 418v52"/></g>';
        // Hängematte mit Matrose
        h += '<g id="matrose"><path class="l n" style="stroke:#c99562;stroke-width:3" d="M470 96l40 60M760 96l-40 60"/><path class="l" fill="#e6c79f" d="M500 150q115 70 230 0q-12 40 -115 46q-103 -6 -115 -46z"/><circle class="l" cx="540" cy="160" r="20" fill="#f3c9a5"/><path class="l" fill="#f6f1e6" d="M522 150q18 -20 36 0z"/>' + Z.auge(534, 160, 4, true) + Z.auge(548, 160, 4, true) + '</g>' + Z.zzz(570, 120, 0.8);
        // Gummimatte, Handtuch
        if (s.matte) h += '<g id="matte"><g transform="translate(560 514) scale(1.5)">' + MATTE + '</g></g>';
        h += '<g id="tuch"><path class="l n" style="stroke-width:4" d="M330 250v12"/><path class="l" fill="#f6f1e6" d="M310 262h40v70h-40z"/><path class="d n" style="stroke:#3b8cff;stroke-width:4" d="M310 274h40M310 320h40"/></g>';
        // Rohr mit Leck
        h += '<path class="l n" style="stroke:#8d98a8;stroke-width:18" d="M800 300H640q-20 0 -20 -20V70"/>';
        if (s.leck) h += '<g id="spritz"><path class="l n" style="stroke:#3a3340;stroke-width:3" d="M690 292l8 16"/><g class="a-flack"><path fill="#9fd3ee" d="M694 302q-60 30 -110 110q60 -50 116 -100zM700 304q-20 60 -50 140q40 -70 54 -136z"/><circle cx="600" cy="400" r="5" fill="#9fd3ee"/><circle cx="640" cy="420" r="4" fill="#9fd3ee"/></g></g>';
        else h += '<g transform="translate(696 300)">' + DICHT + '</g>';
        // Wasser
        h += '<g id="wasser" style="transform:translateY(' + (560 - pegel(s) * 3.2).toFixed(0) + 'px)"><path fill="#4aa3e8" fill-opacity=".72" d="M0 0q50 -10 100 0t100 0t100 0t100 0t100 0t100 0t100 0t100 0v700h-800z"/><path class="n" stroke="#fff" stroke-width="3" opacity=".6" d="M30 6q20 -6 40 0M330 6q20 -6 40 0M630 6q20 -6 40 0"/></g>';
          if (!hell(s)) h += '<rect width="800" height="600" fill="#05070c" opacity=".9"/><path fill="#4aa3e8" opacity=".25" d="M0 ' + (560 - pegel(s) * 3.2).toFixed(0) + 'h800v8h-800z"/>';
        h += Z.tuer(760, 470, 'r', 'tRechts');
        return h;
      }
      // ---- Maschinenraum ----
      h = rumpf(s, '#8a7a6a');
      var last = (s.sw[0] ? 1 : 0) + (s.sw[1] ? 1 : 0) + (s.sw[2] ? 1 : 0);
      h += '<g id="gen"><rect class="l" x="40" y="160" width="210" height="200" rx="14" fill="#3f6b4f"/><rect class="l" x="58" y="180" width="174" height="56" rx="6" fill="#f6efd8"/>' + Z.text(145, 216, 'MAX 2', { k: 26 })
        + [0, 1, 2].map(function (i) { return '<circle class="l" cx="' + (95 + i * 50) + '" cy="270" r="13" fill="' + (i < last ? '#ffd23f' : '#2b3a2f') + '"/>'; }).join('')
        + '<path class="l n" style="stroke:#2b3a2f;stroke-width:6" d="M58 310h174M58 330h174"/><g class="a-flack"><path class="l n" style="stroke:#ffd23f;stroke-width:3" d="M40 160l-12 -12M250 160l12 -12"/></g></g>';
      // Lenzpumpe mit zwei Rädern
      var rl = s.riemen === 'pumpe';
      h += '<g id="pumpe"><rect class="l" x="270" y="380" width="200" height="140" rx="12" fill="#5b6470"/><path class="l n" style="stroke:#8d98a8;stroke-width:14" d="M470 450h30v80"/>'
        + (rl ? '<path class="l n" style="stroke:#2b2b38;stroke-width:8" d="M282 308L402 414M330 350L428 452"/>' : '')
        + '<g id="pr1" class="dreh"><circle class="l" cx="310" cy="320" r="34" fill="#8d98a8"/><path class="d n" d="M310 290v60M280 320h60"/></g><g id="pr2" class="dreh"><circle class="l" cx="420" cy="430" r="26" fill="#8d98a8"/><path class="d n" d="M420 406v48M396 430h48"/></g>'
        + (pumpt(s) ? '<g class="a-flack"><path class="l n" style="stroke:#9fd3ee;stroke-width:4" d="M484 534l-10 12M500 538v16M516 534l10 12"/></g>' : '') + '</g>';
      h += '<g id="kaputt"><path class="l n" style="stroke:#2b2b38;stroke-width:7" d="M280 560q20 -16 40 -4M334 562q16 -14 30 -2"/></g>';
      // Werkzeugwand mit Rohrschelle
      h += '<g id="werkzeug"><rect class="l" x="292" y="88" width="140" height="150" rx="6" fill="#c99562"/>' + (s.schelle ? '<g transform="translate(340 140)">' + SCHELLE + '</g>' : '')
        + '<path class="l n" style="stroke:#d64b3c;stroke-width:6" d="M400 214l10 -40M416 214l-6 -40"/><circle class="l" cx="410" cy="174" r="5" fill="#8d98a8"/><path class="l n" style="stroke:#5b6470;stroke-width:6" d="M392 110l24 40"/></g>';
      // Spind mit Zahlenrädern und Zettel
      h += '<g id="spind"><rect class="l" x="500" y="128" width="292" height="396" rx="8" fill="' + (s.spind ? '#3a3f4c' : '#6b7686') + '"/>';
      if (s.spind) h += (s.riemen === 'spind' ? '<g transform="translate(646 300) scale(1.4)">' + RIEMEN + '</g>' : '') + '<path class="l" fill="#f3c9a5" d="M690 420h40v60h-40z"/><path class="l" fill="#d64b3c" d="M560 380h60v100h-60z"/><path class="l" fill="#6b7686" d="M500 128l-34 22v370l34 4z"/>';
      else {
        for (var i = 0; i < 3; i++) h += '<rect class="l" x="' + (509 + i * 92) + '" y="284" width="82" height="76" rx="8" fill="#f6efd8"/>' + Z.text(550 + i * 92, 336, String(s.rad[i]), { k: 40 })
          + '<path class="d n" style="stroke:#c9b99a" d="M' + (517 + i * 92) + ' 296h66M' + (517 + i * 92) + ' 348h66"/>';
        h += '<g id="griff"><rect class="l" x="610" y="398" width="72" height="64" rx="10" fill="#3a3f4c"/><rect class="l" x="626" y="410" width="40" height="40" rx="6" fill="#c9ced6"/></g>'
          + '<g id="zettel" transform="rotate(-3 640 200)"><path class="l" fill="#fff7c2" d="M560 156h160l-6 92h-150z"/>' + Z.text(640, 186, 'Code =', { k: 18, f: '#5a4636' }) + Z.text(638, 214, 'unsere', { k: 18, f: '#5a4636' }) + Z.text(636, 240, 'Tauchtiefe!', { k: 18, f: '#5a4636' }) + '<circle class="d" cx="640" cy="160" r="5" fill="#d64b3c"/></g>';
      }
      h += '</g>';
      h += '<g id="ente"><g transform="translate(190 480)"><ellipse class="l" cx="0" cy="10" rx="26" ry="16" fill="#ffd23f"/><circle class="l" cx="-12" cy="-12" r="14" fill="#ffd23f"/><path class="l" fill="#f2711c" d="M-24 -10l-14 4l14 6z"/>' + Z.auge(-14, -16, 4) + '</g></g>';
      h += Z.tuer(40, 470, 'l', 'tLinks');
      return h;
    },
    lauf: function (s, t, q) {
      var p = pegel(s, t), w = q('#wasser'), ps = q('#pegelsaeule'), a = q('#pr1'), b = q('#pr2');
      if (w) w.style.transform = 'translateY(' + (560 - p * 3.2).toFixed(1) + 'px)';
      if (ps) { ps.setAttribute('height', (106 * p / 100).toFixed(1)); ps.setAttribute('y', (218 - 106 * p / 100).toFixed(1)); ps.setAttribute('fill', p > 84 ? '#ff5a5f' : p > 64 ? '#ff9a3c' : '#4aa3e8'); }
      if (a && pumpt(s)) { a.style.transform = 'rotate(' + (t * 300 % 360).toFixed(0) + 'deg)'; b.style.transform = 'rotate(' + (t * 400 % 360).toFixed(0) + 'deg)'; }
    },
    uhr: function (s, t) {
      var p = pegel(s, t);
      if (s.leck) {
        if (p >= 100) return { rueck: true, fehl: true, setze: { w0: 40, wt: t, warn: 0 }, ton: 'ring', text: 'Der Torpedoraum ist voll Wasser! Matrose Fritz schöpft mit dem Eimer ein gutes Stück hinaus. Schnell zum Leck!' };
        if (p >= 85 && s.warn < 2) return { setze: { warn: 2 }, ton: 'ring', text: 'Alarm! Im Torpedoraum steht das Wasser schon bis zur Hängematte.' };
        if (p >= 65 && s.warn < 1) return { setze: { warn: 1 }, ton: 'tropf', text: 'Achtung: Die Anzeige «Bug» wird orange – das Wasser steigt.' };
      }
      if (pumpt(s) && p <= 0 && !s.leer) return { setze: { leer: true, w0: 0, wt: t }, ton: 'ok', text: 'Gluck, gluck – fertig: Die Pumpe hat den Torpedoraum leer gepumpt.' };
    },
    stellen: [
      // ---- Türen ----
      { id: 'zuTorpedo', r: [0, 420, 96, 100], wenn: function (s) { return !s.oben && s.raum === 0; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 1 }); return a.wechsel(hell(s) ? 'Durchs Schott nach vorn in den Torpedoraum. Es spritzt und gluckert.' : 'Im Torpedoraum ist es stockdunkel – das Licht ist ausgeschaltet.'); } },
      { id: 'zuMaschine', r: [704, 438, 96, 100], wenn: function (s) { return !s.oben && s.raum === 0; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 2 }); return a.wechsel('Nach hinten in den Maschinenraum. Es riecht nach Öl.'); } },
      { id: 'zuZentrale1', r: [704, 420, 96, 100], wenn: function (s) { return !s.oben && s.raum === 1; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 0 }); return a.wechsel('Zurück in die Zentrale.'); } },
      { id: 'zuZentrale2', r: [0, 420, 96, 100], wenn: function (s) { return !s.oben && s.raum === 2; }, tipp: async function (s, a) { a.ton('knarr'); a.mal({ raum: 0 }); return a.wechsel('Zurück in die Zentrale.'); } },
      // ---- Zentrale ----
      { id: 'tiefe', r: [74, 244, 112, 112], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('klick'); a.notiz('tiefe'); if (!s.tiefe) { a.mal({ tiefe: true }); return a.weiter('Der Tiefenmesser zeigt 140 m. Das steht jetzt im Notizbuch.'); }
        return a.gag('Immer noch 140 m. Ganz schön tief.');
      } },
      { id: 'pegel', r: [514, 90, 92, 166], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        var p = Math.round(pegel(s, a.t)); a.ton('tropf');
        return a.gag('Anzeige «Wasser im Bug»: ' + p + ' %' + (s.leck ? ' – und es steigt.' : pumpt(s) ? ' – die Pumpe arbeitet.' : p > 3 ? ' – es steigt nicht mehr, ist aber noch drin.' : ' – trocken!'));
      } },
      { id: 'sw0', r: [502, 270, 96, 170], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        var sw = s.sw.slice();
        if (!sw[0] && sw[1] && sw[2]) { a.ton('zisch'); return a.gag('Klack – und gleich wieder aus: Der Generator schafft nur zwei Verbraucher. Pumpe und Notfunk laufen schon.'); }
        var b = basis(s, a.t); sw[0] = !sw[0]; a.ton('klick'); a.mal({ sw: sw, w0: b.w0, wt: b.wt });
        return a.wechsel(sw[0] ? 'Licht im Torpedoraum: an.' : 'Licht im Torpedoraum: aus. Vorne ist es jetzt stockdunkel.');
      } },
      { id: 'sw1', r: [602, 270, 96, 170], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('klick'); a.notiz('funk'); return a.gag('Der Notfunk ist mit einer roten Plombe gesichert: Er bleibt immer an. Der funkt «Wir kommen bald!»');
      } },
      { id: 'sw2', r: [702, 270, 96, 170], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        var sw = s.sw.slice(), b = basis(s, a.t);
        if (!sw[2] && sw[0] && sw[1]) { a.ton('zisch'); a.notiz('funk'); return a.gag('Klack – und gleich wieder aus: zu viel Strom! Licht und Notfunk laufen schon, und der Generator schafft nur zwei.'); }
        sw[2] = !sw[2]; a.ton('klick'); a.mal({ sw: sw, w0: b.w0, wt: b.wt });
        if (!sw[2]) return a.wechsel('Pumpe aus.');
        if (s.riemen !== 'pumpe') return a.wechsel('Pumpe ein – aber hinten summt nur der Motor. Die Pumpe selbst dreht sich nicht.');
        return a.weiter(s.leck ? 'Die Pumpe läuft! Aber solange das Leck offen ist, kommt mehr Wasser herein, als sie hinausschafft.' : 'Die Pumpe läuft und schlürft das Wasser aus dem Bug!');
      } },
      { id: 'hebel', r: [506, 442, 104, 92], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (s.leck) {
          a.ton('zisch'); await a.anim('#hebel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-10px)' }], 300); a.ton('ring'); await a.warte(500);
          return a.sackgasse('Pressluft in die Tanks – wir steigen! Aber durchs Leck drückt immer mehr Wasser herein. Notstopp, zurück auf Tiefe!');
        }
        if (pegel(s, a.t) > 3) { a.ton('zisch'); return a.gag('Zisch! Das Boot hebt sich keinen Meter: Im Bug steht noch zu viel Wasser. Das muss zuerst hinaus.'); }
        a.ton('zisch'); await a.anim('#hebel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-10px)' }], 300); await a.warte(400); a.ton('horn');
        a.mal({ oben: true });
        return a.fertig('Blubb, blubb – das U-Boot steigt und taucht in die Sonne auf. Die Kapitänin öffnet die Luke: frische Luft für alle!');
      } },
      { id: 'luke', r: [395, 30, 100, 100], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#luke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(40deg)' }], 600); a.ton('platsch'); a.mal({ luke: true }); await a.warte(400);
        return a.sackgasse('Die Turmluke unter Wasser öffnen? Ein eiskalter Schwall schiesst herein! Schnell wieder zu.');
      } },
      { id: 'sehrohr', r: [222, 150, 96, 206], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#sehrohr', [{ transform: 'translateY(0)' }, { transform: 'translateY(-14px)' }, { transform: 'translateY(0)' }], 900);
        return a.geheim('Im Sehrohr: ein Wal, der neugierig zurückschaut – und dir zuzwinkert.');
      } },
      { id: 'kapitaen', r: [282, 412, 96, 118], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('huch'); return a.gag(['Die Kapitänin: «Zuerst das Leck, Matrose! Dann pumpen, dann auftauchen.»', 'Die Kapitänin zwirbelt ihren Schnurrbart: «Strom haben wir nur für zwei Dinge gleichzeitig.»', '«Der Spind-Code? Den hat sich der Maschinist an den Spind geklebt. Typisch.»'][(a.nr - 1) % 3]);
      } },
      { id: 'rad', r: [122, 404, 96, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#rad', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(60deg)' }, { transform: 'rotate(0deg)' }], 700);
        return a.gag('Hart Steuerbord! … Wir liegen ja still am Grund. Das Steuerrad dreht ins Leere.');
      } },
      { id: 'bullauge', r: [72, 104, 96, 94], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Ein gelber Fisch schaut herein, macht «Blubb» und schwimmt weiter.');
      } },
      // ---- Torpedoraum (nur mit Licht) ----
      { id: 'dunkel', r: [0, 60, 700, 470], wenn: function (s) { return s.raum === 1 && !hell(s); }, tipp: async function (s, a) {
        a.ton('tap'); return a.gag('Stockdunkel! Ohne Licht findest du hier nichts. Der Schalter ist in der Zentrale.');
      } },
      { id: 'leck', r: [600, 250, 140, 130], wenn: function (s) { return s.raum === 1 && hell(s); }, tipp: async function (s, a) {
        a.ton('wasser'); return a.gag(s.leck ? 'Ein Riss im Rohr! Das Wasser spritzt in einem dicken Strahl heraus. Mit der Hand hältst du das nicht zu.' : 'Die Dichtschelle hält. Kein Tropfen mehr.');
      }, mit: {
        dicht: async function (s, a) {
          var b = basis(s, a.t); a.ton('metall'); a.gib('dicht'); a.mal({ leck: false, w0: b.w0, wt: b.wt }); a.punkt();
          return a.weiter('Gummi auf den Riss, Schelle drum, festgeschraubt – das Leck ist dicht! Das Wasser steigt nicht mehr.');
        },
        matte: async function (s, a) { a.ton('platsch'); return a.gag('Du drückst die Matte auf den Riss – sobald du loslässt, spritzt es wieder. Sie müsste festgeklemmt werden.'); },
        schelle: async function (s, a) { a.ton('metall'); return a.gag('Die Schelle allein presst nur Metall auf Metall. Durch den Riss spritzt es weiter – es fehlt etwas Weiches dazwischen.'); }
      } },
      { id: 'matte', r: [506, 476, 110, 92], wenn: function (s) { return s.raum === 1 && hell(s) && s.matte; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ matte: false }); a.nimm('matte'); return a.weiter('Eine dicke Gummimatte, schön weich und wasserdicht.');
      } },
      { id: 'tuch', r: [282, 232, 96, 110], wenn: function (s) { return s.raum === 1 && hell(s); }, tipp: async function (s, a) {
        a.ton('platsch'); return a.gag('Du stopfst das Handtuch ins Leck – es saugt sich voll und klatscht dir vor die Füsse. Zurück an den Haken.');
      } },
      { id: 'torpedo', r: [266, 400, 334, 96], wenn: function (s) { return s.raum === 1 && hell(s); }, tipp: async function (s, a) {
        a.ton('metall'); return a.gag(a.nr % 2 ? 'Ein Übungstorpedo. Wir wollen auftauchen, nicht die Fische erschrecken.' : 'Auf dem Torpedo hat jemand «Für Oma» geschrieben. Lieber nicht.');
      } },
      { id: 'feuer', r: [160, 380, 100, 100], wenn: function (s) { return s.raum === 1 && hell(s); }, tipp: async function (s, a) {
        a.ton('boing'); return a.gag('Der rote Knopf «Feuer» ist mit einer Kappe gesichert. Zum Glück.');
      } },
      { id: 'matrose', r: [480, 90, 260, 120], wenn: function (s) { return s.raum === 1 && hell(s); }, tipp: async function (s, a) {
        a.ton('schnarch'); return a.gag(a.nr % 2 ? 'Matrose Fritz schläft in der Hängematte. «Mama, noch fünf Minuten …»' : 'Er murmelt: «Gummimatte … gegen kalte Füsse …» und schnarcht weiter.');
      } },
      { id: 'bug', r: [360, 100, 100, 100], wenn: function (s) { return s.raum === 1 && hell(s); }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Draussen schwimmt ein orangefarbener Fisch vorbei und schaut neugierig aufs Leck.');
      } },
      // ---- Maschinenraum ----
      { id: 'schelle', r: [294, 94, 92, 92], wenn: function (s) { return s.raum === 2 && s.schelle; }, tipp: async function (s, a) {
        a.ton('metall'); a.mal({ schelle: false }); a.nimm('schelle'); return a.weiter('Eine Rohrschelle aus Stahl, mit Schraube zum Festziehen.');
      } },
      { id: 'zettel', r: [556, 150, 170, 104], wenn: function (s) { return s.raum === 2 && !s.spind; }, tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('zettel'); if (!s.zettel) { a.mal({ zettel: true }); return a.weiter('Auf dem Zettel steht: «Ersatzteile im Spind. Code = unsere Tauchtiefe.» Steht im Notizbuch.'); }
        return a.gag('«Code = unsere Tauchtiefe.» Und die zeigt ein Messgerät in der Zentrale.');
      } },
      { id: 'rad0', r: [505, 276, 92, 96], wenn: function (s) { return s.raum === 2 && !s.spind; }, tipp: rad(0) },
      { id: 'rad1', r: [597, 276, 92, 96], wenn: function (s) { return s.raum === 2 && !s.spind; }, tipp: rad(1) },
      { id: 'rad2', r: [689, 276, 96, 96], wenn: function (s) { return s.raum === 2 && !s.spind; }, tipp: rad(2) },
      { id: 'griff', r: [598, 384, 96, 92], wenn: function (s) { return s.raum === 2 && !s.spind; }, tipp: async function (s, a) {
        if (s.rad.join('') !== '140') { a.ton('klick'); return a.gag('Der Griff klemmt: Der Code ' + s.rad.join('-') + ' stimmt nicht.'); }
        a.ton('knarr'); a.mal({ spind: true }); return a.weiter('Klick – 1-4-0, der Spind springt auf! Drin hängt ein nagelneuer Keilriemen.');
      } },
      { id: 'riemen', r: [560, 236, 170, 140], wenn: function (s) { return s.raum === 2 && s.spind && s.riemen === 'spind'; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ riemen: 'tasche' }); a.nimm('riemen'); return a.weiter('Ein Ersatz-Keilriemen. Wo dreht sich hier etwas ohne Riemen?');
      } },
      { id: 'spindzu', r: [520, 150, 260, 360], wenn: function (s) { return s.raum === 2 && s.spind; }, tipp: async function (s, a) {
        a.ton('klick'); return a.gag('Im Spind hängen nur noch ein Pullover und ein Foto vom Maschinisten mit seiner Katze.');
      } },
      { id: 'pumpe', r: [270, 280, 210, 240], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('klick');
        if (s.riemen !== 'pumpe') return a.gag('Die Lenzpumpe: zwei Räder – aber der Riemen dazwischen ist gerissen. Die Stücke liegen am Boden.');
        return a.gag(pumpt(s) ? 'Wusch, wusch – die Pumpe läuft.' : 'Der neue Riemen sitzt. Jetzt braucht die Pumpe noch Strom – der Schalter ist in der Zentrale.');
      }, mit: {
        riemen: async function (s, a) {
          a.ton('metall'); a.gib('riemen'); var b = basis(s, a.t); a.mal({ riemen: 'pumpe', w0: b.w0, wt: b.wt });
          return a.weiter(s.sw[2] ? 'Der Riemen springt auf die Räder – und die Pumpe legt los!' : 'Der Riemen liegt straff auf beiden Rädern. Jetzt fehlt nur noch Strom für die Pumpe.');
        }
      } },
      { id: 'kaputt', r: [270, 504, 110, 96], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Die Reste des alten Keilriemens. Durchgescheuert – damit dreht sich nichts mehr.');
      } },
      { id: 'gen', r: [40, 160, 210, 200], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('robo'); a.notiz('strom');
        return a.gag('Der Generator brummt. Auf dem Schild steht gross: MAX 2 – höchstens zwei Verbraucher. Die Lämpchen zeigen, wie viele laufen.');
      } },
      { id: 'ente', r: [142, 444, 96, 92], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('quak'); return a.gag('Quietsch! Eine Badeente. Der Maschinist badet gern – sagt man.');
      } },
      { id: 'werkzeug', r: [292, 88, 140, 150], wenn: function (s) { return s.raum === 2; }, tipp: async function (s, a) {
        a.ton('metall'); return a.gag('Zange, Schraubenschlüssel, ein Hammer. Mit einem Hammer wird ein Leck nur grösser.');
      } }
    ],
    naechster: function (s, weg, t) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (s.leck) {
        if (!hell(s)) return geh(s, 0, 'sw0');
        if (hat('dicht')) return geh(s, 1, { stelle: 'leck', ding: 'dicht' });
        if (hat('matte') && hat('schelle')) return { kombi: ['matte', 'schelle'] };
        if (s.matte) return geh(s, 1, 'matte');
        return geh(s, 2, 'schelle');
      }
      if (s.riemen !== 'pumpe') {
        if (hat('riemen')) return geh(s, 2, { stelle: 'pumpe', ding: 'riemen' });
        if (s.spind) return geh(s, 2, 'riemen');
        if (!s.zettel) return geh(s, 2, 'zettel');
        if (!s.tiefe) return geh(s, 0, { stelle: 'tiefe', wink: 'Der Zettel sagt: Code = unsere Tauchtiefe.' });
        for (var i = 0; i < 3; i++) if (s.rad[i] !== [1, 4, 0][i]) return geh(s, 2, { stelle: 'rad' + i, wink: 'Die Tiefe steht im Notizbuch.' });
        return geh(s, 2, 'griff');
      }
      if (s.sw[0]) return geh(s, 0, { stelle: 'sw0', wink: 'Der Generator schafft nur zwei Verbraucher – einer muss weichen.' });
      if (!s.sw[2]) return geh(s, 0, 'sw2');
      if (pegel(s, t) > 3) return geh(s, 0, { stelle: 'pegel', warte: true });
      return geh(s, 0, 'hebel');
    }
  });
  function rad(i) {
    return async function (s, a) { var r = s.rad.slice(); r[i] = (r[i] + 1) % 10; a.ton('klick'); a.mal({ rad: r }); return a.wechsel('Zahlenrad ' + (i + 1) + ': ' + r[i] + '. Code jetzt ' + r.join('-') + '.'); };
  }
})();
