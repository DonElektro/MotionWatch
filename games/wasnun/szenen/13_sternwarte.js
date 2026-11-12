/* Bild 13 «Die Sternwarte» (Meister+): das Fernrohr auf den Kometen richten. Richtung, Höhe und Zeit stehen als
   Hinweise im Bild (Sternkarte, Schattenstab am Fenster, Tagebuch) und landen im Notizbuch. Zwei Wege:
   Weg «meister» (selber gerechnet): Sternkarte (Komet beim Schwan, der Schwan steht im Osten) · Schattenstab (der Mond
              steht 30° hoch) · Tagebuch («ab 23 Uhr, genau so hoch wie der Mond»).
   Weg «papagei» (der Trick): Keks aus der Dose · dem Papagei geben – er plappert nach, was der Astronom gestern
              gesagt hat: «Osten! Dreissig Grad! Dreiundzwanzig Uhr!»
   Danach gleich: leeren Karton nehmen · der Katze hinstellen (sie springt hinein und lässt das Okular fallen) · Okular
   nehmen · ins Fernrohr · Kuppel auf Osten drehen · Höhe auf 30° kurbeln · Kuppelklappe öffnen · (bis 23:00 warten,
   die Uhr läuft eine Minute pro Sekunde) · durchs Okular schauen.
   Falsch gezielt nach 23 Uhr = ein Fehlversuch. Sackgasse: die Deckenlampe anknipsen, während die Klappe offen ist. */
(function () {
  var Z = WASNUN.Z, RICHT = ['N', 'O', 'S', 'W'], RNAME = ['Norden', 'Osten', 'Süden', 'Westen'], HOEHE = [15, 30, 45, 60, 75];
  var START = 22 * 60 + 30;
  function uhrMin(t) { return Math.min(23 * 60 + 59, START + Math.floor(t)); }
  function zielt(s) { return s.dir === 1 && s.alt === 1; }
  function nacht(t) { return uhrMin(t) >= 23 * 60; }
  var KARTON = '<path class="l" fill="#c99562" d="M-26 -6h52v30h-52z"/><path class="l" fill="#b07a4c" d="M-26 -6l-10 -12h28l8 12zM26 -6l10 -12h-28l-8 12z"/><path class="d n" style="stroke:#8a5a3a" d="M-10 6h20"/>';
  var OKULAR = '<rect class="l" x="-10" y="-20" width="20" height="40" rx="5" fill="#3a3340"/><rect class="l" x="-13" y="-22" width="26" height="10" rx="3" fill="#8d98a8"/><ellipse cx="0" cy="-22" rx="8" ry="3" fill="#9fd3ee"/>';
  var KEKS = '<circle class="l" r="16" fill="#e6c79f"/><circle cx="-5" cy="-4" r="2.5" fill="#6b4a34"/><circle cx="6" cy="2" r="2.5" fill="#6b4a34"/><circle cx="-2" cy="7" r="2.5" fill="#6b4a34"/>';
  function stern(x, y, r) { return Z.stern(x, y, r); }
  WASNUN.szene({
    id: 'sternwarte', titel: 'Die Sternwarte', stufe: 5, wege: ['meister', 'papagei'],
    ziel: 'Heute Nacht zieht ein Komet vorbei – und der Astronom ist eingeschlafen. Richte das Fernrohr auf den Kometen!',
    start: function () { return { tasche: [], karte: false, schatten: false, tagebuch: false, papagei: false, keks: 'dose', karton: 'boden', okular: 'katze', dir: 3, alt: 3, klappe: false, lampe: false }; },
    notizen: {
      karte: { titel: 'Sternkarte', text: 'Der Komet zieht am Sternbild Schwan vorbei. Der Schwan steht heute Nacht im Osten.' },
      schatten: { titel: 'Schattenstab am Fenster', text: 'Der Schatten im Mondlicht zeigt: Der Mond steht 30° hoch.' },
      tagebuch: { titel: 'Tagebuch des Astronomen', text: '«Der Komet kommt heute ab 23 Uhr – genau so hoch über dem Horizont wie der Mond.»' },
      papagei: { titel: 'Papagei Galileo', text: '«Osten! Dreissig Grad! Dreiundzwanzig Uhr! Krah!»' }
    },
    dinge: {
      karton: { name: 'Leerer Karton', svg: '<g transform="translate(30 32)">' + KARTON + '</g>' },
      okular: { name: 'Okular', svg: '<g transform="translate(30 32)">' + OKULAR + '</g>' },
      keks: { name: 'Keks', svg: '<g transform="translate(30 30)">' + KEKS + '</g>' }
    },
    kombi: [{ a: 'keks', b: 'karton', nein: 'Ein Keks im Karton? Die Katze mag Kartons – Kekse mag jemand anderes.' }],
    nutzlos: function (s, d, st) {
      if (d === 'keks') return 'Kekse mag hier nur einer: der mit dem Schnabel.';
      if (d === 'karton') return 'Ein leerer Karton. Wer in diesem Raum springt wohl am liebsten in Kartons?';
      if (d === 'okular') return 'Das Okular gehört unten ins Fernrohr, dort, wo man hineinschaut.';
      return '';
    },
    bild: function (s) {
      var auf = s.klappe, h = '<rect width="800" height="600" fill="#2b2f4a"/>';
      // Kuppel mit Klappe
      h += '<path class="l" fill="#3d4566" d="M-5 330q0 -320 405 -320t405 320z"/><path class="d n" style="stroke:#323a58;stroke-width:6" d="M120 330q20 -230 280 -290M680 330q-20 -230 -280 -290M40 330q40 -260 360 -300"/>';
      h += '<g id="spalt"><path class="l" fill="' + (auf ? '#0d1330' : '#4a5378') + '" d="M340 20q60 -14 120 0v250h-120z"/>';
      if (auf) {
        h += stern(370, 60, 5) + stern(430, 100, 4) + stern(390, 170, 5) + stern(445, 220, 3) + stern(360, 230, 4);
        h += '<g id="komet" style="opacity:0"><path fill="#bfe6ff" opacity=".55" d="M410 128q30 -6 46 -40q-6 34 -40 50z"/><circle cx="406" cy="134" r="9" fill="#fff"/><circle cx="406" cy="134" r="16" fill="#bfe6ff" opacity=".4"/></g>';
      } else h += '<path class="d n" style="stroke:#3d4566" d="M340 80h120M340 140h120M340 200h120"/>';
      h += '<path class="l n" style="stroke:#8d98a8;stroke-width:6" d="M340 270V20M460 270V20"/><g><rect class="l" x="378" y="272" width="44" height="30" rx="6" fill="#ffd23f"/>' + Z.text(400, 295, RICHT[s.dir], { k: 22 }) + '</g></g>';
      // Fenster mit Mond und Schattenstab
      h += '<g id="fenster"><circle class="l" cx="110" cy="140" r="64" fill="#1c2742"/>' + stern(80, 110, 4) + stern(150, 170, 3) + '<circle class="l" cx="136" cy="110" r="18" fill="#fdf3c0"/><path class="l n" style="stroke:#c9b99a;stroke-width:8" d="M46 140h128M110 76v128"/><circle class="l n" cx="110" cy="140" r="64" style="stroke:#c9b99a;stroke-width:8"/></g>'
        + '<g id="mondfahne" opacity="0"><path class="l n" style="stroke-width:2" d="M138 100v-16"/><path fill="#ff6f91" d="M138 84h12l-3 4l3 4h-12z"/></g>';
      h += '<g id="stab"><rect class="l" x="26" y="214" width="228" height="16" rx="3" fill="#c99562"/><path fill="#00000066" d="M44 214L150 214l-6 6H44z"/><rect class="l" x="38" y="168" width="8" height="48" fill="#8a5a3a"/>';
      [[230, '15'], [150, '30'], [104, '45'], [72, '60']].forEach(function (m) { h += '<path class="d n" d="M' + m[0] + ' 214v8"/>' + Z.text(m[0], 244, m[1] + '°', { k: 12, f: '#f6efd8' }); });
      h += '<circle cx="150" cy="216" r="5" fill="#ffd23f"/></g>';
      // Sternkarte
      h += '<g id="karte"><rect class="l" x="20" y="262" width="200" height="190" rx="6" fill="#1c2742"/><circle class="l n" cx="120" cy="356" r="72" style="stroke:#5b6890;stroke-width:2"/>'
        + Z.text(120, 284, 'N', { k: 14, f: '#ffd23f' }) + Z.text(120, 444, 'S', { k: 14, f: '#ffd23f' }) + Z.text(204, 361, 'O', { k: 14, f: '#ffd23f' }) + Z.text(36, 361, 'W', { k: 14, f: '#ffd23f' })
        + '<path class="n" stroke="#bcd3e6" stroke-width="2" d="M100 300l14 6l12 -4l14 8M106 400l8 12l12 -2l6 -12M60 346l12 -10l10 6l4 14"/>'
        + '<path class="n" stroke="#fff" stroke-width="2.5" d="M162 332l14 24l-14 22M154 356h34"/><circle cx="176" cy="356" r="3" fill="#fff"/>'
        + '<circle class="n" cx="176" cy="356" r="20" stroke="#ff5a5f" stroke-width="3"/><path fill="#ff5a5f" d="M190 340l16 -16l-4 12l10 2z"/>' + Z.text(176, 398, 'Schwan', { k: 11, f: '#bcd3e6' }) + '</g>';
      // Wanduhr
      h += '<g id="uhr"><circle class="l" cx="270" cy="96" r="38" fill="#f6efd8"/>';
      for (var i = 0; i < 12; i++) h += '<path class="d n" style="stroke-width:3" d="M270 64v6" transform="rotate(' + i * 30 + ' 270 96)"/>';
      h += '<g id="zstd" style="transform-origin:270px 96px"><path class="l n" style="stroke-width:5" d="M270 96v-20"/></g><g id="zmin" style="transform-origin:270px 96px"><path class="l n" style="stroke-width:3" d="M270 96v-30"/></g><circle cx="270" cy="96" r="4" fill="#3a3340"/></g>';
      // Deckenlampe
      h += '<g id="lampe"><path class="l n" d="M560 10v50"/><path class="l" fill="#3a3340" d="M536 86q4 -26 24 -26t24 26z"/><ellipse class="l" cx="560" cy="88" rx="12" ry="6" fill="' + (s.lampe ? '#fff7c2' : '#8d98a8') + '"/></g>';
      if (s.lampe) h += '<path fill="#fff7c2" opacity=".25" d="M540 90L380 600h360z"/>';
      // Fernrohr auf Säule, Höhenskala und Kurbel
      var w = HOEHE[s.alt];
      h += '<path class="l" fill="#5b6470" d="M420 540l20 -150h40l20 150z"/><rect class="l" x="390" y="530" width="140" height="24" rx="6" fill="#3a3f4c"/>'
        + '<g id="skala"><path class="l" fill="#f6efd8" d="M530 400a70 70 0 0 0 -70 -70v70z"/>';
      HOEHE.forEach(function (g) { var r = g * Math.PI / 180; h += '<path class="d n" d="M' + (460 + Math.cos(r) * 58).toFixed(0) + ' ' + (400 - Math.sin(r) * 58).toFixed(0) + 'L' + (460 + Math.cos(r) * 70).toFixed(0) + ' ' + (400 - Math.sin(r) * 70).toFixed(0) + '"/>'; });
      h += Z.text(512, 396, w + '°', { k: 14 }) + '</g>';
      h += '<g transform="translate(460 390) rotate(' + (-w) + ')"><g id="rohr"><rect class="l" x="-120" y="-24" width="330" height="48" rx="10" fill="#e9a23b"/><rect class="l" x="200" y="-30" width="34" height="60" rx="6" fill="#b98a00"/><rect class="l" x="-60" y="-28" width="16" height="56" fill="#b98a00"/><rect class="l" x="60" y="-28" width="16" height="56" fill="#b98a00"/>'
        + '<rect class="l" x="-150" y="-12" width="32" height="24" rx="4" fill="#3a3340"/>' + (s.okular === 'drin' ? '<g transform="translate(-160 0) rotate(-90)">' + OKULAR + '</g>' : '<circle class="d" cx="-150" cy="0" r="6" fill="#1c1c26"/>') + '</g></g>'
        + '<circle class="l" cx="460" cy="390" r="14" fill="#8d98a8"/>';
      h += '<g id="kurbel"><path class="l n" style="stroke:#8d98a8;stroke-width:7" d="M500 460h30v24"/><circle class="l" cx="530" cy="490" r="9" fill="#d64b3c"/><circle class="l" cx="492" cy="460" r="12" fill="#5b6470"/></g>';
      // Kuppelrad an der Wand, Klappenzug
      h += '<g id="kuppelrad"><circle class="l n" cx="700" cy="420" r="46" style="stroke:#9a6b43;stroke-width:9"/><path class="l n" style="stroke:#9a6b43;stroke-width:6" d="M700 374v92M654 420h92M668 388l64 64M732 388l-64 64"/><circle class="l" cx="700" cy="420" r="12" fill="#c99562"/>'
        + '<rect class="l" x="676" y="340" width="48" height="26" rx="5" fill="#f6efd8"/>' + Z.text(700, 360, RICHT[s.dir], { k: 18 }) + '</g>';
      h += '<g id="klappe"><path class="l n" style="stroke:#e6c79f;stroke-width:4" d="M600 120V' + (auf ? 286 : 250) + '"/><rect class="l" x="584" y="' + (auf ? 286 : 250) + '" width="32" height="40" rx="8" fill="' + (auf ? '#3fcf6b' : '#d64b3c') + '"/></g>';
      // Papagei auf der Stange
      h += '<g id="papagei"><path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M660 210h90M705 210v80"/><g transform="translate(700 182)"><path class="l" fill="#3fbf6b" d="M-6 24q-24 -40 6 -50q26 6 16 50z"/><path class="l" fill="#e23b2e" d="M-6 -30q14 -14 26 2q-6 8 -18 6z"/>' + Z.auge(6, -26, 5) + '<path class="l" fill="#ffd23f" d="M18 -24q12 2 8 14q-6 -6 -10 -4z"/><path class="l" fill="#3b8cff" d="M-6 24l-6 26l10 -6l6 8l2 -26z"/></g></g>';
      // Fernglas am Haken
      h += '<g id="fernglas"><path class="l n" d="M760 60v30"/><circle class="l" cx="748" cy="106" r="13" fill="#3a3340"/><circle class="l" cx="776" cy="106" r="13" fill="#3a3340"/><rect class="l" x="756" y="98" width="12" height="12" fill="#5b6470"/></g>';
      // Schreibtisch mit Tagebuch und Keksdose, schlafender Astronom
      h += '<path class="l" fill="#8a5a3a" d="M20 488h290v16h-290z"/><path class="l n" style="stroke:#6b4a34;stroke-width:8" d="M34 504v80M296 504v80"/>'
        + '<g id="tagebuch"><path class="l" fill="#f6efd8" d="M40 486l50 -8l50 8v-32l-50 -8l-50 8z"/><path class="l n" d="M90 446v40"/><path class="d n" style="stroke:#a89a7a" d="M50 466l30 -4M50 474l30 -4M100 462l30 4M100 470l30 4"/></g>'
        + '<g id="dose"><rect class="l" x="162" y="446" width="52" height="40" rx="6" fill="#3b8cff"/><rect class="l" x="158" y="440" width="60" height="12" rx="4" fill="#2f6fd0"/><circle cx="188" cy="468" r="8" fill="#ffd23f"/></g>'
        + '<g id="astronom"><g transform="translate(286 476)"><path class="l" fill="#5b3a8a" d="M-30 30q-6 -50 30 -52q36 2 30 52z"/><circle class="l" cy="-34" r="22" fill="#f3c9a5"/><path class="l" fill="#5b3a8a" d="M-24 -46l24 -40l24 40z"/>' + Z.stern(0, -60, 7) + Z.auge(-8, -34, 4, true) + Z.auge(8, -34, 4, true) + '<path class="l" fill="#f6f1e6" d="M-16 -22q16 30 32 0q-16 8 -32 0z"/></g></g>' + Z.zzz(312, 410, 0.7);
      // Katze mit Okular, Karton
      var kat = s.karton === 'katze';
      if (kat) h += '<g id="katze"><g transform="translate(600 540)">' + KARTON.replace(/#c99562/g, '#c99562') + '<g transform="translate(0 -18)"><circle class="l" cx="0" cy="-6" r="18" fill="#f0a04b"/><path class="l" fill="#f0a04b" d="M-14 -16l-2 -14l12 8zM14 -16l2 -14l-12 8z"/>' + Z.auge(-6, -8, 4, true) + Z.auge(6, -8, 4, true) + '</g></g></g>' + Z.zzz(620, 480, 0.6);
      else h += '<g id="katze"><g transform="translate(600 530)"><path class="l" fill="#d9863a" d="M30 4q26 0 24 -24q8 0 8 6q-2 28 -30 26z"/><ellipse class="l" cx="0" cy="-6" rx="36" ry="18" fill="#f0a04b"/><circle class="l" cx="-32" cy="-18" r="16" fill="#f0a04b"/><path class="l" fill="#f0a04b" d="M-44 -28l2 -14l10 8zM-26 -30l6 -12l4 12z"/>'
        + Z.auge(-38, -20, 4, false, -1, 1) + Z.auge(-26, -20, 4, false, -1, 1) + (s.okular === 'katze' ? '<g transform="translate(-62 6) rotate(70) scale(.8)">' + OKULAR + '</g>' : '') + '</g></g>';
      if (s.okular === 'boden') h += '<g id="okular"><g transform="translate(662 568) rotate(80) scale(.9)">' + OKULAR + '</g></g>';
      if (s.karton === 'boden') h += '<g id="karton"><g transform="translate(720 548) scale(1.3)">' + KARTON + '</g></g>';
      // Globus
      h += '<g id="globus"><path class="l n" style="stroke:#8a5a3a;stroke-width:5" d="M500 588h50M525 588v-20"/><g id="kugel" class="dreh"><circle class="l" cx="525" cy="540" r="28" fill="#4aa3e8"/><path class="l" fill="#57b04f" d="M508 528q10 -8 16 2t12 -2q6 12 -6 18q-12 6 -18 -6zM530 556q8 -6 12 2q-4 6 -12 -2z"/></g></g>';
      if (s.lampe) h += '<rect width="800" height="600" fill="#fff7c2" opacity=".12"/>';
      return h;
    },
    lauf: function (s, t, q) {
      var m = uhrMin(t), a = q('#zmin'), b = q('#zstd'), k = q('#komet');
      if (a) { a.style.transform = 'rotate(' + (m % 60 * 6) + 'deg)'; b.style.transform = 'rotate(' + ((m / 60) % 12 * 30).toFixed(1) + 'deg)'; }
      if (k) k.style.opacity = zielt(s) && nacht(t) && !s.lampe ? 1 : 0;
    },
    stellen: [
      { id: 'okular', r: [604, 508, 112, 92], wenn: function (s) { return s.okular === 'boden'; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ okular: 'tasche' }); a.nimm('okular'); return a.weiter('Das Okular des Fernrohrs – ohne das sieht man nur ein dunkles Loch.');
      } },
      { id: 'katze', r: [550, 486, 110, 104], tipp: async function (s, a) {
        if (s.karton === 'katze') { a.ton('schnurr'); return a.gag('Kater Kepler schnurrt im Karton. Für ihn ist der Abend gelaufen.'); }
        a.ton('miau'); return a.gag(a.nr % 2 ? 'Kater Kepler spielt mit dem Okular des Fernrohrs und rollt es hin und her. Hergeben? Niemals!' : 'Kepler faucht, wenn du nach dem Okular greifst. Man müsste ihm etwas viel Besseres bieten.');
      }, mit: {
        karton: async function (s, a) {
          a.ton('miau'); a.gib('karton'); a.mal({ karton: 'katze', okular: 'boden' });
          return a.weiter('Ein Karton! Kepler lässt das Okular fallen und springt mit einem Satz hinein. Katzen eben.');
        },
        keks: async function (s, a) { a.ton('miau'); return a.gag('Kepler schnüffelt am Keks und gähnt. Kekse sind für Papageien.'); }
      } },
      { id: 'karton', r: [670, 506, 110, 92], wenn: function (s) { return s.karton === 'boden'; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ karton: 'tasche' }); a.nimm('karton'); return a.weiter('Der leere Karton vom neuen Okular. Genau die richtige Grösse für … eine Katze.');
      } },
      { id: 'rohr', r: function (s) { var w = HOEHE[s.alt] * Math.PI / 180; return [Math.round(460 - 150 * Math.cos(w) - 55), Math.round(390 + 150 * Math.sin(w) - 50), 110, 100]; }, tipp: async function (s, a) {
        if (s.okular !== 'drin') { a.ton('klick'); return a.gag('Hinten am Fernrohr fehlt das Okular. Du schaust in ein leeres Loch.'); }
        if (s.lampe) { a.ton('fehl'); return a.gag('Die Deckenlampe blendet. So siehst du gar nichts.'); }
        if (!s.klappe) { a.ton('klick'); return a.gag('Du siehst … die Innenseite der Kuppel. Die Klappe ist noch zu.'); }
        if (!nacht(a.t)) { a.ton('tap'); return a.gag('Ein paar Sterne – vom Kometen noch keine Spur. Laut Tagebuch kommt er erst ab 23 Uhr.'); }
        if (!zielt(s)) { a.ton('fehl'); return a.fehl('Nur gewöhnliche Sterne. Daneben! Prüf Richtung und Höhe noch einmal – die Hinweise stehen im Notizbuch.'); }
        a.ton('geheim'); await a.anim('#komet', [{ transform: 'scale(1)' }, { transform: 'scale(1.6)' }, { transform: 'scale(1)' }], 900);
        return a.fertig('Da ist er! Ein leuchtender Komet mit langem Schweif, genau im Osten, dreissig Grad hoch. Der Astronom wacht auf und jubelt.', { meister: !s.papagei });
      }, mit: {
        okular: async function (s, a) { a.ton('klick'); a.gib('okular'); a.mal({ okular: 'drin' }); return a.weiter('Klick – das Okular sitzt im Fernrohr.'); }
      } },
      { id: 'kurbel', r: [478, 432, 96, 92], tipp: async function (s, a) {
        a.ton('knarr'); var n = (s.alt + 1) % 5; a.mal({ alt: n }); return a.wechsel('Das Fernrohr steht jetzt ' + HOEHE[n] + '° hoch.');
      } },
      { id: 'kuppelrad', r: [650, 336, 100, 132], tipp: async function (s, a) {
        a.ton('knarr'); var n = (s.dir + 1) % 4; a.mal({ dir: n }); return a.wechsel('Die Kuppel dreht sich rumpelnd: Der Spalt zeigt jetzt nach ' + RNAME[n] + '.');
      } },
      { id: 'klappe', r: [554, 214, 92, 120], tipp: async function (s, a) {
        a.ton('knarr');
        if (!s.klappe && s.lampe) { a.mal({ klappe: true }); await a.warte(300); a.ton('fehl'); return a.sackgasse('Klappe auf – aber die Deckenlampe brennt! Im grellen Licht ist draussen kein einziger Stern zu sehen. Die Augen müssen sich erst wieder an die Nacht gewöhnen.'); }
        a.mal({ klappe: !s.klappe }); return a.wechsel(s.klappe ? 'Die Kuppelklappe gleitet auf. Kühle Nachtluft und Sterne!' : 'Klappe zu.');
      } },
      { id: 'lampe', r: [512, 20, 96, 92], tipp: async function (s, a) {
        if (s.lampe) { a.ton('klick'); a.mal({ lampe: false }); return a.wechsel('Licht aus. Schön dunkel.'); }
        a.ton('klick'); a.mal({ lampe: true });
        if (s.klappe) { await a.warte(400); return a.sackgasse('Licht an bei offener Kuppel? Jetzt sieht man draussen keinen Stern mehr – und die Augen brauchen eine Weile, bis sie sich wieder an die Dunkelheit gewöhnen.'); }
        return a.wechsel('Licht an. Gemütlich – aber Sternegucker schalten es aus, sobald die Kuppel offen ist.');
      } },
      { id: 'karte', r: [20, 262, 200, 190], tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('karte'); if (!s.karte) { a.mal({ karte: true }); return a.weiter('Auf der Sternkarte ist der Komet rot eingekreist: beim Sternbild Schwan – und der Schwan steht im Osten. Steht im Notizbuch.'); }
        return a.gag('Der Komet beim Schwan, im Osten.');
      } },
      { id: 'stab', r: [24, 166, 232, 92], tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('schatten'); if (!s.schatten) { a.mal({ schatten: true }); return a.weiter('Der Schatten des Stabes im Mondlicht reicht genau bis zur Marke 30°: So hoch steht der Mond. Steht im Notizbuch.'); }
        return a.gag('Der Schatten endet bei 30°.');
      } },
      { id: 'tagebuch', r: [36, 410, 112, 92], tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('tagebuch'); if (!s.tagebuch) { a.mal({ tagebuch: true }); return a.weiter('Im Tagebuch steht: «Der Komet kommt heute ab 23 Uhr – genau so hoch über dem Horizont wie der Mond.» Steht im Notizbuch.'); }
        return a.gag('«Ab 23 Uhr, so hoch wie der Mond.»');
      } },
      { id: 'dose', r: [150, 410, 96, 96], tipp: async function (s, a) {
        if (s.keks === 'dose') { a.ton('metall'); a.mal({ keks: 'tasche' }); a.nimm('keks'); return a.weiter('In der Keksdose: ein einzelner Schokoladenkeks.'); }
        a.ton('metall'); return a.gag('Die Keksdose ist leer. Nur noch Krümel.');
      } },
      { id: 'papagei', r: [652, 130, 104, 120], tipp: async function (s, a) {
        a.ton('kraechz'); return a.gag(['Papagei Galileo legt den Kopf schief: «Krah! Keks? Keks?»', 'Galileo plappert alles nach, was er hört. Für einen Keks verrät er bestimmt etwas.', '«Gestern-Nacht, gestern-Nacht!», krächzt Galileo.'][(a.nr - 1) % 3]);
      }, mit: {
        keks: async function (s, a) {
          a.ton('kraechz'); a.gib('keks'); a.notiz('papagei'); a.mal({ papagei: true, keks: 'weg' }); await a.warte(400); a.ton('kraechz');
          return a.weiter('Galileo knackt den Keks und plappert, was er gestern vom Astronomen gehört hat: «Osten! Dreissig Grad! Dreiundzwanzig Uhr! Krah!»');
        }
      } },
      { id: 'uhr', r: [222, 50, 96, 96], tipp: async function (s, a) {
        var m = uhrMin(a.t); a.ton('klick');
        return a.gag('Die Wanduhr zeigt ' + Math.floor(m / 60) + ':' + ('0' + m % 60).slice(-2) + ' Uhr.' + (m < 23 * 60 ? ' Bis 23 Uhr ist noch ein bisschen Zeit.' : ''));
      } },
      { id: 'spalt', r: [330, 14, 140, 290], tipp: async function (s, a) {
        a.ton('plopp'); return a.gag(s.klappe ? 'Durch den Spalt funkeln die Sterne. Die Kuppel zeigt nach ' + RNAME[s.dir] + '.' : 'Der Kuppelspalt ist zu. Der Buchstabe am Rand zeigt die Richtung: ' + RNAME[s.dir] + '.');
      } },
      { id: 'fenster', r: [46, 72, 128, 96], tipp: async function (s, a) {
        a.ton('geheim'); await a.anim('#mondfahne', [{ opacity: 0 }, { opacity: 1 }, { opacity: 1 }, { opacity: 0 }], 1600);
        return a.geheim('Auf dem Mond weht ganz klein eine Fahne – mit einer Katze drauf. Kepler war wohl schon dort.');
      } },
      { id: 'astronom', r: [246, 404, 96, 116], tipp: async function (s, a) {
        a.ton('schnarch'); return a.gag(a.nr % 2 ? 'Der Astronom schnarcht mit offenem Mund: «Chrrr … Schwan … Chrrr …»' : 'Er murmelt im Schlaf: «Nicht das Licht anmachen, Kepler … nie bei offener Kuppel …»');
      } },
      { id: 'fernglas', r: [704, 54, 96, 96], tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Mit dem Fernglas siehst du … Nachbars Kühe auf der Weide. Für einen Kometen ist es viel zu schwach.');
      } },
      { id: 'kugel', r: [477, 504, 96, 96], tipp: async function (s, a) {
        a.ton('boing'); await a.anim('#kugel', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(720deg)' }], 1200);
        return a.gag('Der Globus dreht sich wie verrückt. Die Erde schafft das zum Glück langsamer.');
      } }
    ],
    naechster: function (s, weg, t) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (weg === 'papagei' && !s.papagei && !(s.karte && s.schatten && s.tagebuch)) {
        if (hat('keks')) return { stelle: 'papagei', ding: 'keks' };
        if (s.keks === 'dose') return 'dose';
      } else if (!s.papagei) {
        if (!s.karte) return { stelle: 'karte', wink: 'Wo steht der Komet am Himmel? Die Sternkarte weiss es.' };
        if (!s.schatten) return { stelle: 'stab', wink: 'Wie hoch steht der Mond? Der Schatten verrät es.' };
        if (!s.tagebuch) return 'tagebuch';
      }
      if (s.okular !== 'drin') {
        if (hat('okular')) return { stelle: 'rohr', ding: 'okular' };
        if (s.okular === 'boden') return 'okular';
        if (hat('karton')) return { stelle: 'katze', ding: 'karton', wink: 'Katzen können Kartons nicht widerstehen.' };
        return 'karton';
      }
      if (s.lampe) return 'lampe';
      if (s.dir !== 1) return { stelle: 'kuppelrad', wink: 'Der Schwan steht im Osten.' };
      if (s.alt !== 1) return { stelle: 'kurbel', wink: 'So hoch wie der Mond: 30°.' };
      if (!s.klappe) return 'klappe';
      if (!nacht(t)) return { stelle: 'uhr', warte: true };
      return 'rohr';
    }
  });
})();
