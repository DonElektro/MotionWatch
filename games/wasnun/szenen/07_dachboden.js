/* Bild 7 «Auf dem Dachboden» (knifflig): drei Lärmquellen in beliebiger Reihenfolge - falsche Fährten (Schirm, Kissen),
   kombinieren (Besen + Kleiderbügel), ein Hinweis im Bild (Farben der Wimpel = Farben am Schloss), eine Sackgasse (Kissen).
   Lösung: Socke von der Leine in die Blechwanne (Tropfen leise) · Besen + Kleiderbügel = Hakenstange, damit die
   Dachluke zuziehen · die drei Knöpfe der Vitrine auf die Farben der Wimpel (blau, rot, gelb) stellen, dann den
   Blechaffen abstellen. */
(function () {
  var Z = WASNUN.Z;
  var FARBEN = ['#3fbf6b', '#e23b2e', '#ffd23f', '#3b8cff'];       // grün, rot, gelb, blau - ein Knopf blättert in dieser Reihenfolge
  var CODE = [3, 1, 2];                                              // Wimpel von links: blau, rot, gelb
  function laut(s) { return (s.tropf ? 1 : 0) + (s.luke ? 1 : 0) + (s.affe ? 1 : 0); }
  function offen(s) { return s.k[0] === CODE[0] && s.k[1] === CODE[1] && s.k[2] === CODE[2]; }
  var SOCKE = '<path class="l" fill="#f6f1e6" d="M-10 -24h20v26q0 8 8 12q10 6 4 14q-8 6 -22 -2q-10 -6 -10 -20z"/><path class="l n" style="stroke:#d64b3c;stroke-width:4" d="M-10 -14h20M-10 -6h20"/>';
  var BESEN = '<path class="l n" style="stroke:#c99562;stroke-width:6" d="M0 -28v36"/><path class="l" fill="#ffd23f" d="M-14 8h28l4 20h-36z"/><path class="d n" style="stroke:#b98a00" d="M-6 14v12M2 14v12M10 14v12"/>';
  var BUEGEL = '<path class="l n" style="stroke:#8d98a8;stroke-width:5" d="M0 -8q0 -12 8 -12q8 2 4 10M0 -8l-24 18h48z"/>';
  var STANGE = '<path class="l n" style="stroke:#c99562;stroke-width:6" d="M-14 26l24 -44"/><path class="l n" style="stroke:#8d98a8;stroke-width:5" d="M10 -18q8 -12 16 -4q4 8 -6 12"/><path class="l n" style="stroke:#f6f1e6;stroke-width:4" d="M4 -10l8 4"/>';
  function gespenst(s) {
    var n = laut(s), wuetend = s.wut;
    return '<g id="geist"' + (n ? '' : ' class="a-atmen fuss"') + '><g transform="translate(430 392)"><path class="l" fill="#fff" d="M-44 40v-56a44 44 0 0 1 88 0v56l-15 -12l-14 12l-15 -12l-15 12l-14 -12z"/>'
      + (n === 0 ? Z.auge(-14, -18, 8, true) + Z.auge(14, -18, 8, true) + '<path class="d n" d="M-6 0q6 6 12 0"/>'
        : '<circle cx="-14" cy="-18" r="8" fill="#3a3340"/><circle cx="14" cy="-18" r="8" fill="#3a3340"/><path class="l n" d="M-26 -' + (wuetend ? 36 : 30) + 'l18 ' + (wuetend ? 10 : 4) + 'M26 -' + (wuetend ? 36 : 30) + 'l-18 ' + (wuetend ? 10 : 4) + '"/>'
          + (wuetend ? '<ellipse cx="0" cy="6" rx="12" ry="14" fill="#3a3340"/>' : '<path class="l n" d="M-10 6q10 -8 20 0"/>')
          + '<path class="l" fill="#fff" d="M-44 -22q-16 -6 -16 8q8 8 18 2zM44 -22q16 -6 16 8q-8 8 -18 2z"/>')
      + '<path class="l" fill="#7b6fd0" d="M-36 -44q36 -34 72 0q14 -40 40 -34q-6 8 -4 16q-44 -14 -64 18z"/><circle class="d" cx="76" cy="-78" r="8" fill="#fff"/></g>'
      + (n === 0 ? Z.zzz(486, 300, 1) : '') + '</g>';
  }
  function affe(s) {
    return '<g id="affe"><g transform="translate(652 368)"><ellipse class="l" cx="0" cy="-8" rx="26" ry="30" fill="#a57c52"/><ellipse cx="0" cy="-2" rx="14" ry="18" fill="#e9c8a0"/><rect class="l" x="-22" y="6" width="44" height="14" rx="4" fill="#d64b3c"/>'
      + '<circle class="d" cx="-26" cy="-58" r="10" fill="#a57c52"/><circle class="d" cx="26" cy="-58" r="10" fill="#a57c52"/><circle class="l" cx="0" cy="-54" r="24" fill="#a57c52"/><ellipse cx="0" cy="-46" rx="15" ry="12" fill="#e9c8a0"/>'
      + (s.affe ? Z.auge(-9, -60, 6) + Z.auge(9, -60, 6) + '<path class="l" fill="#fff" d="M-9 -46h18q-2 10 -9 10t-9 -10z"/>' : Z.auge(-9, -60, 6, true) + Z.auge(9, -60, 6, true) + '<path class="d n" d="M-6 -44q6 4 12 0"/>')
      + '<path class="l" fill="#d64b3c" d="M-16 -74h32l-6 -16h-20z"/>'
      + '<g id="bl" class="rechtsu"><path class="l n" style="stroke:#a57c52;stroke-width:8" d="M-22 -18l-22 -10"/><ellipse class="l" cx="-50" cy="-30" rx="7" ry="22" fill="#ffd23f"/></g>'
      + '<g id="br" class="linksu"><path class="l n" style="stroke:#a57c52;stroke-width:8" d="M22 -18l22 -10"/><ellipse class="l" cx="50" cy="-30" rx="7" ry="22" fill="#ffd23f"/></g></g></g>';
  }
  function knopf(i) {
    return { id: 'knopf' + i, r: [[512, 604, 700][i], 396, [92, 96, 96][i], 92], wenn: function (s) { return !s.auf; }, tipp: async function (s, a) {
      var k = s.k.slice(); k[i] = (k[i] + 1) % 4; a.ton('klick'); a.mal({ k: k });
      if (offen(s)) {
        a.ton('glocke'); await a.warte(350); a.mal({ auf: true }); a.ton('knarr');
        return a.weiter('Klick, klack, klick – blau, rot, gelb wie die Wimpel! Die Vitrine springt auf.');
      }
      return a.wechsel(['Der Knopf leuchtet jetzt grün.', 'Der Knopf leuchtet jetzt rot.', 'Der Knopf leuchtet jetzt gelb.', 'Der Knopf leuchtet jetzt blau.'][k[i]] + ' Drei Knöpfe, drei Fähnchen …');
    } };
  }
  function still(s, a, text) {
    return laut(s) === 0 ? a.fertig(text + ' Endlich Ruhe: Das Gespenst seufzt, gähnt – und schläft selig ein.') : a.weiter(text + (laut(s) === 1 ? ' Nur noch ein Lärm stört.' : ' Das Gespenst hält sich noch die Ohren zu.'));
  }
  WASNUN.szene({
    id: 'dachboden', titel: 'Auf dem Dachboden', stufe: 3,
    ziel: 'Das kleine Gespenst möchte schlafen. Aber es tropft, klappert und scheppert. Sorge für Ruhe!',
    start: function () { return { tasche: [], tropf: true, luke: true, affe: true, socke: true, besen: true, buegel: true, k: [0, 0, 0], auf: false, schirm: false, wut: false }; },
    dinge: {
      socke: { name: 'Wollsocke', svg: '<g transform="translate(28 32)">' + SOCKE + '</g>' },
      besen: { name: 'Besen', svg: '<g transform="translate(30 30)">' + BESEN + '</g>' },
      buegel: { name: 'Kleiderbügel', svg: '<g transform="translate(30 30)">' + BUEGEL + '</g>' },
      stange: { name: 'Hakenstange', svg: '<g transform="translate(28 30)">' + STANGE + '</g>' }
    },
    kombi: [{ a: 'besen', b: 'buegel', gibt: 'stange', text: 'Den Kleiderbügel oben an den Besenstiel gebunden: eine lange Hakenstange!' },
      { a: 'socke', b: 'besen', nein: 'Eine Socke über den Besen? Dann wischt er leiser, aber das hilft gerade nicht.' }],
    bild: function (s) {
      var h = '<rect width="800" height="600" fill="#2b2233"/><path class="l" fill="#6b5340" d="M-5 334L400 16L805 334v160h-810z"/>'
        + '<path class="d n" style="stroke:#5a4636" d="M100 258v230M200 180v310M300 102v390M400 20v470M500 102v390M600 180v310M700 258v230"/>'
        + '<path class="l" fill="#4a382c" d="M-5 334L400 16L805 334l0 -34L400 -20L-5 300z"/>'
        + '<rect class="l" x="-5" y="486" width="810" height="120" fill="#8a6240"/><path class="d n" style="stroke:#6b4a34" d="M0 524h800M0 562h800M150 486v38M450 486v38M680 486v38M300 524v38M580 524v38M120 562v38M400 562v38M700 562v38"/>'
        + '<path fill="#ffd98a" opacity=".13" d="M400 100l-190 390h380z"/>';
      // Lampe, Bild an der Wand (Geheimnis)
      h += '<g id="lampe" class="kopf"><path class="l n" d="M400 20v34"/><path class="l" fill="#3a3340" d="M376 84q4 -30 24 -30t24 30z"/><ellipse class="l" cx="400" cy="86" rx="12" ry="7" fill="#ffe9a8"/></g>'
        + '<g id="bildnis"><rect class="l" x="392" y="150" width="84" height="104" fill="#c99562"/><rect class="l" x="402" y="160" width="64" height="84" fill="#40507a"/><path class="l" fill="#5b3a2e" d="M410 244q0 -30 24 -30t24 30z"/><circle class="l" cx="434" cy="198" r="18" fill="#f3c9a5"/>'
        + '<path class="l" fill="#8d98a8" d="M414 194q4 -24 20 -22q16 -2 20 22q-20 -12 -40 0z"/>' + Z.auge(427, 198, 4) + Z.auge(441, 198, 4) + '<g id="zunge" opacity="0"><path class="d" fill="#ff6f91" d="M429 208h10v10q-5 5 -10 0z"/></g><path class="d n" d="M428 208h12"/></g>';
      // Wimpelkette unter der linken Dachschräge: blau, rot, gelb
      h += '<path class="l n" style="stroke:#f6f1e6;stroke-width:2.5" d="M150 222q110 -50 200 -140"/>';
      [[188, 204, 3], [252, 168, 1], [312, 122, 2]].forEach(function (w) { h += '<path class="l" fill="' + FARBEN[w[2]] + '" d="M' + (w[0] - 20) + ' ' + (w[1] + 8) + 'l40 -22l-8 50z"/>'; });
      // Dachluke rechts (klappert), Regen
      h += '<path class="l" fill="#1d2748" d="M560 96l96 -26l22 76l-96 28z"/>' + (s.luke ? '<path class="n" stroke="#9fd3ee" stroke-width="3" stroke-linecap="round" d="M588 100l-10 26M616 92l-10 30M644 86l-10 30M606 136l-6 18M636 126l-6 20"/>' : '')
        + (s.luke ? '<g id="luke" class="kopf"><path class="l" fill="#c99562" d="M556 92l100 -28l-10 -40l-100 28z"/><path class="l n" style="stroke:#3a3340;stroke-width:5" d="M590 50q8 -14 18 -6"/></g><g id="klapper" class="a-flack"><path class="l n" style="stroke:#ffd23f;stroke-width:4" d="M530 44l-16 -8M528 66l-18 2M676 30l14 -10M682 52l18 -2"/></g>'
          : '<path class="l" fill="#c99562" d="M554 100l104 -30l24 80l-104 30z"/><path class="l n" style="stroke:#8a5a3a" d="M566 112l92 -26M574 138l92 -26"/><path class="l n" style="stroke:#3a3340;stroke-width:5" d="M610 150q10 6 18 -4"/>');
      // Wäscheleine: Socke, Kleiderbügel
      h += '<path class="l n" style="stroke:#f6f1e6;stroke-width:2.5" d="M40 300q130 26 290 -10"/>';
      if (s.socke) h += '<g id="socke"><g transform="translate(118 344)">' + SOCKE + '</g><rect class="d" x="112" y="306" width="8" height="18" fill="#c99562"/></g>';
      if (s.buegel) h += '<g id="buegel"><g transform="translate(262 330) scale(1.5)">' + BUEGEL + '</g></g>';
      h += '<g transform="translate(190 334) rotate(4)"><path class="l" fill="#e9a23b" d="M-22 -18h44v40h-44z"/><path class="d n" d="M-22 -4h44"/><rect class="d" x="-16" y="-24" width="7" height="14" fill="#c99562"/><rect class="d" x="9" y="-24" width="7" height="14" fill="#c99562"/></g>';
      // Besen an der Wand, Schirm im Ständer
      if (s.besen) h += '<g id="besen"><g transform="translate(46 420) scale(2.2)">' + BESEN + '</g></g>';
      h += '<path class="l" fill="#5b6470" d="M108 496h56l-6 60h-44z"/>'
        + (s.schirm ? '<g id="schirm"><path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M136 520v-118"/><path class="l" fill="#d64b3c" d="M66 446q70 -84 140 0q-17 -12 -35 0q-17 -12 -35 0q-17 -12 -35 0q-17 -12 -35 0z"/></g>'
          : '<g id="schirm"><path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M136 520v-120q0 -14 -12 -14"/><path class="l" fill="#d64b3c" d="M124 500l12 -92l12 92z"/></g>');
      // Tropfen vom Dach in die Blechwanne
      h += '<path class="l" fill="#3a2d38" d="M236 150q14 -10 28 0q-6 12 -14 12t-14 -12z"/>';
      if (s.tropf) h += '<g id="tropfen"><path class="d" fill="#7cc4ee" d="M250 170q9 14 0 20q-9 -6 0 -20z"/></g><g id="plink" class="a-flack"><path class="l n" style="stroke:#ffd23f;stroke-width:4" d="M196 470l-16 -10M250 458v-18M304 470l16 -10"/></g>';
      h += '<g id="wanne"><path class="l" fill="#aab6c6" d="M190 488h120l-12 60h-96z"/><ellipse class="l" cx="250" cy="488" rx="60" ry="14" fill="#8d98a8"/><ellipse cx="250" cy="490" rx="46" ry="9" fill="#7cc4ee"/>'
        + (s.tropf ? '' : '<g transform="translate(250 486) rotate(80) scale(.9)">' + SOCKE + '</g>') + '<path class="l n" style="stroke-width:5" d="M186 506q-14 2 -12 18M314 506q14 2 12 18"/></g>';
      // Gespenst auf seinem Kissen
      h += '<g id="kissen"><path class="l" fill="#b08fe0" d="M360 492q-10 -44 14 -52q56 -12 112 0q24 8 14 52q-70 12 -140 0z"/><path class="d n" style="stroke:#8a6cc0" d="M384 452q46 -8 92 0"/><circle class="d" cx="366" cy="444" r="6" fill="#ffd23f"/><circle class="d" cx="494" cy="444" r="6" fill="#ffd23f"/></g>' + gespenst(s);
      // Vitrine mit Blechaffe, Schloss mit drei Farb-Knöpfen
      h += '<rect class="l" x="514" y="262" width="278" height="226" rx="6" fill="#7a5236"/><rect class="l" x="530" y="278" width="246" height="112" fill="#8fb3c9" fill-opacity=".35"/>' + affe(s)
        + (s.auf ? '<path class="l" fill="#8fb3c9" fill-opacity=".4" d="M776 278l22 -14v112l-22 14z"/>' : '<path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".55" d="M546 300l30 -14M546 326l54 -26"/><path class="l n" d="M653 278v112"/>')
        + (s.affe ? '<g class="a-flack"><path class="l n" style="stroke:#ffd23f;stroke-width:4" d="M584 320l-16 -8M582 344l-18 2M722 320l16 -8M724 344l18 2"/></g>' : '')
        + '<rect class="l" x="530" y="404" width="246" height="70" rx="8" fill="#5b3a2e"/>';
      for (var i = 0; i < 3; i++) { var x = [570, 653, 736][i]; h += '<circle class="l" cx="' + x + '" cy="439" r="27" fill="#3a2d38"/><path class="l" fill="' + FARBEN[s.k[i]] + '" d="M' + (x - 16) + ' ' + 426 + 'h32l-16 30z"/>'; }
      // Koffer, Schaukelpferd
      h += '<g id="koffer"><rect class="l" x="352" y="512" width="120" height="70" rx="8" fill="#9a6b43"/><path class="l n" style="stroke:#5b3a2e;stroke-width:6" d="M352 536h120"/><path class="l n" style="stroke-width:5" d="M396 512q16 -18 32 0"/><rect class="l" x="404" y="530" width="16" height="14" fill="#ffd23f"/></g>'
        + '<g id="motte" opacity="0"><path class="d" fill="#e6dfc8" d="M410 500q-14 -14 -18 0q8 8 18 0zM414 500q14 -14 18 0q-8 8 -18 0z"/></g>'
        + '<g id="pferd" class="fuss"><path class="l n" style="stroke:#8a5a3a;stroke-width:7" d="M560 586q60 16 120 0"/><path class="l" fill="#e6c79f" d="M584 574v-34h72v34h-12v-20h-48v20z"/><path class="l" fill="#e6c79f" d="M640 546l14 -36l24 6l-4 16l-14 -2l-4 18z"/><path class="l" fill="#d64b3c" d="M596 540h40v-8h-40z"/>' + Z.auge(664, 518, 3) + '<path class="l n" style="stroke:#8a5a3a;stroke-width:5" d="M584 546q-14 4 -12 20"/></g>';
      return h;
    },
    lauf: function (s, t, q) {
      var d = q('#tropfen'), p = (t % 1.4) / 1.4, l = q('#luke'), bl = q('#bl'), br = q('#br');
      if (d) { d.style.transform = 'translateY(' + (p * p * 290).toFixed(0) + 'px)'; d.style.opacity = p > 0.95 ? 0 : 1; }
      if (l) l.style.transform = 'rotate(' + (Math.abs(Math.sin(t * 5)) * -9).toFixed(1) + 'deg)';
      if (bl && s.affe) { var w = Math.abs(Math.sin(t * 6)) * 26; bl.style.transform = 'rotate(' + w.toFixed(0) + 'deg)'; br.style.transform = 'rotate(' + (-w).toFixed(0) + 'deg)'; }
    },
    stellen: [
      knopf(0), knopf(1), knopf(2),
      { id: 'affe', r: [560, 270, 190, 124], tipp: async function (s, a) {
        if (!s.affe) { a.ton('klick'); return a.gag('Der Blechaffe hält still. Sein Schlüssel im Rücken dreht sich nicht mehr.'); }
        if (!s.auf) { a.ton('metall'); return a.gag(a.nr % 2 ? 'Tschäng, tschäng! Der Blechaffe scheppert hinter Glas. Die Vitrine ist abgeschlossen.' : 'Am Schloss sind drei Knöpfe mit bunten Fähnchen. Wo hat man solche Fähnchen schon gesehen?'); }
        a.ton('klick'); a.mal({ affe: false });
        return still(s, a, 'Du hältst den Schlüssel im Rücken an – der Blechaffe lässt die Becken sinken.');
      } },
      { id: 'luke', r: [536, 14, 170, 170], tipp: async function (s, a) {
        if (!s.luke) { a.ton('klick'); return a.gag('Die Dachluke ist zu und verriegelt. Draussen prasselt der Regen ganz leise.'); }
        a.ton('knarr'); return a.gag(a.nr % 2 ? 'Klapper, klapper! Die Dachluke schlägt im Wind. Sie ist viel zu hoch oben – am Griff müsste man ziehen können.' : 'So hoch kommst du nicht. Es bräuchte etwas Langes mit einem Haken vorne dran.');
      }, mit: {
        stange: async function (s, a) {
          if (!s.luke) return a.gag('Die Luke ist schon zu.');
          a.ton('knarr'); await a.anim('#luke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(40deg)' }], 500); a.ton('plumps'); a.gib('stange'); a.mal({ luke: false });
          return still(s, a, 'Haken in den Griff, ein Ruck – die Dachluke fällt zu. Kein Klappern mehr.');
        },
        besen: async function (s, a) { a.ton('boing'); return a.gag('Der Besen reicht bis hinauf, rutscht aber am Griff ab. Vorne fehlt ein Haken.'); },
        buegel: async function (s, a) { a.ton('boing'); return a.gag('Der Kleiderbügel hätte einen schönen Haken – aber er ist viel zu kurz.'); }
      } },
      { id: 'wanne', r: [180, 440, 140, 116], tipp: async function (s, a) {
        a.ton(s.tropf ? 'metall' : 'plopp'); await a.anim('#wanne', [{ transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' }], 250);
        return a.gag(s.tropf ? (a.nr % 2 ? 'Plink! Plink! Jeder Tropfen knallt auf das Blech der Wanne.' : 'Wegschieben geht nicht: Dann tropft es auf den Boden. Es bräuchte etwas Weiches in der Wanne.') : 'Die Tropfen landen weich auf der Socke. Man hört nichts mehr.');
      }, mit: {
        socke: async function (s, a) {
          a.ton('plopp'); a.gib('socke'); a.mal({ tropf: false });
          return still(s, a, 'Die dicke Wollsocke in die Wanne – jetzt machen die Tropfen nur noch «pff».');
        }
      } },
      { id: 'geist', r: [376, 320, 110, 116], tipp: async function (s, a) {
        a.ton('huch'); await a.anim('#geist', [{ transform: 'translateY(0)' }, { transform: 'translateY(-10px)' }, { transform: 'translateY(0)' }], 500);
        var n = laut(s);
        return a.gag(n === 3 ? 'Das Gespenst hält sich die Ohren zu: Es tropft, es klappert, es scheppert.' : n === 2 ? 'Schon etwas besser. Aber zwei Dinge lärmen noch.' : 'Fast still! Nur ein Lärm fehlt noch.');
      } },
      { id: 'kissen', r: [352, 424, 156, 92], tipp: async function (s, a) {
        a.ton('huch'); a.mal({ wut: true });
        await a.anim('#geist', [{ transform: 'scale(1)' }, { transform: 'scale(1.5) translateY(-30px)' }, { transform: 'scale(1.4) translateY(-26px)' }, { transform: 'scale(1.5) translateY(-30px)' }], 900);
        return a.sackgasse('«Huuuu! MEIN Kissen!» Das wäre schön weich gewesen – aber dem Gespenst nimmt man nicht das Kopfkissen weg.');
      } },
      { id: 'socke', r: [68, 300, 100, 100], wenn: function (s) { return s.socke; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ socke: false }); a.nimm('socke'); return a.weiter('Eine dicke Wollsocke, schön weich. Wo ihr Zwilling ist, weiss niemand.');
      } },
      { id: 'buegel', r: [214, 290, 100, 96], wenn: function (s) { return s.buegel; }, tipp: async function (s, a) {
        a.ton('metall'); a.mal({ buegel: false }); a.nimm('buegel'); return a.weiter('Ein Kleiderbügel aus Draht, mit einem kräftigen Haken.');
      } },
      { id: 'besen', r: [6, 350, 92, 150], wenn: function (s) { return s.besen; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ besen: false }); a.nimm('besen'); return a.weiter('Ein Besen mit einem schön langen Stiel.');
      } },
      { id: 'schirm', r: [86, 384, 106, 112], tipp: async function (s, a) {
        a.ton('boing'); a.mal({ schirm: !s.schirm });
        return a.gag(s.schirm ? 'Plopp – ein Regenschirm, wie praktisch! Nur tropft es drüben bei der Wanne, und ein Schirm würde erst recht trommeln.' : 'Schirm wieder zu. Im Haus bringt er sowieso Unglück.', true);
      } },
      { id: 'bildnis', r: [386, 144, 96, 116], tipp: async function (s, a) {
        a.ton('boing'); await a.anim('#zunge', [{ opacity: 0 }, { opacity: 1 }, { opacity: 1 }, { opacity: 0 }], 1200);
        return a.geheim('Der strenge Urgrossonkel im Bilderrahmen streckt dir die Zunge heraus.');
      } },
      { id: 'lampe', r: [350, 24, 100, 100], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#lampe', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(-10deg)' }, { transform: 'rotate(0deg)' }], 900);
        return a.gag('Die Lampe schaukelt und wirft tanzende Schatten. Leise ist sie wenigstens.');
      } },
      { id: 'wimpel', r: [150, 100, 200, 130], tipp: async function (s, a) {
        a.ton('flatter'); return a.gag('Eine Wimpelkette vom letzten Fest: ein blaues, ein rotes und ein gelbes Fähnchen.');
      } },
      { id: 'koffer', r: [346, 508, 130, 92], tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#motte', [{ opacity: 1, transform: 'translate(0,0)' }, { opacity: 1, transform: 'translate(30px,-60px)' }, { opacity: 0, transform: 'translate(-20px,-130px)' }], 1000);
        return a.gag('Im alten Koffer wohnt eine Motte. Sie flattert empört davon – immerhin lautlos.');
      } },
      { id: 'pferd', r: [556, 496, 130, 100], tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#pferd', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(8deg)' }, { transform: 'rotate(-8deg)' }, { transform: 'rotate(5deg)' }, { transform: 'rotate(0deg)' }], 1000);
        return a.gag('Das Schaukelpferd knarrt ein paar Mal und bleibt stehen. Pssst!');
      } }
    ],
    naechster: function (s) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (s.tropf) return s.socke ? 'socke' : { stelle: 'wanne', ding: 'socke' };
      if (s.luke) return hat('stange') ? { stelle: 'luke', ding: 'stange' } : s.besen ? 'besen' : s.buegel ? 'buegel' : { kombi: ['besen', 'buegel'] };
      if (s.auf) return 'affe';
      for (var i = 0; i < 3; i++) if (s.k[i] !== CODE[i]) return { stelle: 'knopf' + i, wink: 'Die Farben stehen irgendwo im Bild – in derselben Reihenfolge.' };
      return 'affe';
    }
  });
})();
