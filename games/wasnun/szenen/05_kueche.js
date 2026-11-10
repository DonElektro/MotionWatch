/* Bild 5 «Küche um Mitternacht» (knifflig): alles gemischt - genau hinschauen (Schnur an der Käseglocke), ein Ding mitnehmen
   (Milch), Sackgasse (Katze ohne Milch geweckt), richtiger Moment (die Katze schaut beim Trinken immer wieder auf).
   Lösung: Kühlschrank öffnen · Milch nehmen · Milch in den Napf · Küchenwecker (Katze geht trinken) ·
   Topf vom Regal (zieht die Käseglocke hoch; geht auch früher) · Maus antippen, während die Katze den Kopf im Napf hat. */
(function () {
  var Z = WASNUN.Z, F = '#f0a04b', FD = '#d9863a';
  // die trinkende Katze: 5.5 Sekunden Takt, in den ersten 1.7 s hebt sie den Kopf und schaut sich um
  function phase(t) { return ((t % 5.5) + 5.5) % 5.5; }
  function schaut(t) { return phase(t) < 1.7; }
  function kopf(x, y, o) {
    o = o || {};
    return '<g transform="translate(' + x + ' ' + y + ')"><path class="l" fill="' + F + '" d="M-27 -12l2 -28l22 16zM27 -12l-2 -28l-22 16z"/><path fill="#f7c8c0" d="M-22 -18l1 -13l10 8zM22 -18l-1 -13l-10 8z"/>'
      + '<ellipse class="l" rx="31" ry="26" fill="' + F + '"/><path class="d n" style="stroke:' + FD + ';stroke-width:4" d="M-7 -24v9M0 -25v10M7 -24v9"/>'
      + (o.zu ? Z.auge(-12, -3, 6, true) + Z.auge(12, -3, 6, true) : Z.auge(-12, -4, o.gross ? 9 : 7, false, o.dx || 0, 0) + Z.auge(12, -4, o.gross ? 9 : 7, false, o.dx || 0, 0))
      + '<path fill="#e2787a" d="M-4 6h8l-4 5z"/><path class="d n" d="M0 11q-5 6 -10 2M0 11q5 6 10 2M-22 6l-18 -3M-22 11l-18 4M22 6l18 -3M22 11l18 4"/>'
      + (o.zunge ? '<path class="d" fill="#ff6f91" d="M-4 15h8v8q-4 4 -8 0z"/>' : '') + '</g>';
  }
  function katze(s) {
    if (s.katze === 'schlaeft') return '<g id="katze"><g transform="translate(318 512)"><g class="a-atmen fuss"><path class="l" fill="' + FD + '" d="M84 4q26 8 12 24q-60 16 -130 6q-10 -8 2 -14q66 8 104 -6z"/>'
      + '<ellipse class="l" cx="22" cy="-8" rx="70" ry="34" fill="' + F + '"/><path class="d n" style="stroke:' + FD + ';stroke-width:5" d="M10 -40v14M30 -42v14M50 -38v14"/></g>'
      + '<g id="ohr">' + kopf(-44, -6, { zu: true }) + '</g></g>' + Z.zzz(296, 440, 0.9) + '</g>';
    if (s.katze === 'wach') return '<g id="katze"><g transform="translate(300 536)"><path class="l" fill="' + FD + '" d="M30 -6q46 6 50 -30q10 -2 10 8q-6 40 -60 36z"/><path class="l" fill="' + F + '" d="M-36 0q-12 -78 36 -82q48 4 36 82z"/>'
      + '<path class="l" fill="#fff" d="M-16 0q-2 -22 8 -22t8 22zM4 0q-2 -22 8 -22t8 22z"/>' + kopf(-4, -100, { gross: true, dx: -3 }) + '</g></g>';
    // trinkt: Körper beim Napf, zwei Köpfe (lauf() zeigt einen davon)
    return '<g id="katze"><g transform="translate(604 548)"><path class="l" fill="' + FD + '" d="M-52 -40q-26 -8 -22 -44q8 -6 12 2q-2 22 16 24z"/>'
      + '<path class="l" fill="' + F + '" d="M-44 -22h16v22h-16zM-22 -22h16v22h-16zM22 -22h16v22h-16zM42 -22h16v22h-16z"/><ellipse class="l" cx="6" cy="-38" rx="62" ry="28" fill="' + F + '"/>'
      + '<path class="d n" style="stroke:' + FD + ';stroke-width:5" d="M-14 -64v14M6 -66v14M26 -64v14"/>'
      + '<g id="kt">' + kopf(72, -22, { zu: true, zunge: true }) + '</g><g id="ks" style="display:none">' + kopf(58, -70, { gross: true, dx: -3 }) + '<path class="l n" style="stroke:#fff;stroke-width:4" d="M18 -112l-8 -14M38 -118v-16M58 -112l8 -14"/></g></g></g>';
  }
  function maus(x, y, mitKaese, guckt) {
    return '<g transform="translate(' + x + ' ' + y + ')">' + (guckt ? '' : '<path class="l n" style="stroke:#e2a3a8;stroke-width:4" d="M-20 0q-18 4 -24 -10"/><ellipse class="l" cx="-4" cy="-2" rx="22" ry="14" fill="#cfcad6"/>')
      + '<circle class="d" cx="10" cy="-24" r="9" fill="#cfcad6"/><circle cx="10" cy="-24" r="4.5" fill="#f2b8c0"/><ellipse class="l" cx="16" cy="-10" rx="16" ry="13" fill="#cfcad6"/>'
      + Z.auge(20, -13, 4.5, false, 1, 0) + '<circle cx="32" cy="-8" r="3.5" fill="#e2787a"/><path class="d n" d="M26 -5l12 4M26 -8l13 -2"/>'
      + (mitKaese ? '<g transform="translate(34 -22) scale(.62)">' + kaese() + '</g>' : '') + '</g>';
  }
  function kaese() { return '<path class="l" fill="#ffd23f" d="M-28 0l44 -26l14 26z"/><path class="l" fill="#f2b705" d="M-28 0h58v10h-58z"/><circle cx="2" cy="-8" r="4" fill="#d99a00"/><circle cx="16" cy="-4" r="3" fill="#d99a00"/>'; }
  var MILCH = '<rect class="l" x="-9" y="-44" width="18" height="12" rx="3" fill="#3b8cff"/><path class="l" fill="#fff" d="M-9 -34q-9 6 -9 18v32q0 6 6 6h24q6 0 6 -6v-32q0 -12 -9 -18z"/><rect x="-17" y="-8" width="34" height="16" fill="#9fd3ee"/><path class="l n" d="M-9 -34q-9 6 -9 18v32q0 6 6 6h24q6 0 6 -6v-32q0 -12 -9 -18z"/>';
  WASNUN.szene({
    id: 'kueche', titel: 'Küche um Mitternacht', stufe: 3,
    ziel: 'Mitternacht. Die Maus hat Hunger auf den Käse – aber die Katze darf nichts merken.',
    start: function () { return { kuehl: false, milch: 'drin', katze: 'schlaeft', glocke: false, maus: 'loch', toast: false }; },
    tasche: function (s) { return s.milch === 'tasche' ? { name: 'Milch', svg: '<g transform="translate(30 34) scale(.95)">' + MILCH + '</g>' } : null; },
    bild: function (s) {
      var hoch = s.glocke ? 104 : 0;
      var h = '<rect width="800" height="600" fill="#3c4b73"/><path class="d n" style="stroke:#34426a" d="M0 150h800M0 300h800"/>'
        + '<rect class="l" x="-5" y="470" width="810" height="140" fill="#2b3557"/><path class="d n" style="stroke:#222b49" d="M0 514h800M0 560h800M90 470v44M250 470v44M410 470v44M570 470v44M730 470v44M170 514v46M330 514v46M490 514v46M650 514v46M90 560v40M250 560v40M410 560v40M570 560v40M730 560v40"/>';
      // Fenster mit Mond
      h += '<rect class="l" x="192" y="52" width="132" height="124" fill="#1d2748"/>' + Z.stern(214, 78, 7) + Z.stern(300, 150, 6) + Z.stern(292, 72, 5)
        + '<g id="mond"><g transform="translate(250 112) scale(.82)">' + Z.mond(0, 0, s.mondzu) + '</g></g>'
        + '<path class="l n" style="stroke:#e6dfc8;stroke-width:8" d="M192 52h132v124h-132zM258 52v124"/><rect class="l" x="182" y="176" width="152" height="12" fill="#c9b99a"/>'
        + '<path fill="#fdf3c0" opacity=".09" d="M200 188h116l150 282h-330z"/>';
      // Kuckucksuhr
      h += '<g id="uhr"><path class="l" fill="#8a5a3a" d="M476 96l38 -34l38 34v62h-76z"/><path class="l" fill="#6b4a34" d="M468 100l46 -42l46 42l-8 8l-38 -34l-38 34z"/><circle class="l" cx="514" cy="126" r="20" fill="#f6f1e6"/><path class="l n" d="M514 126v-12M514 126l8 6"/>'
        + '<path class="l n" d="M500 158v34M528 158v24"/><ellipse class="d" cx="500" cy="198" rx="6" ry="9" fill="#6b4a34"/><ellipse class="d" cx="528" cy="188" rx="6" ry="9" fill="#6b4a34"/></g>'
        + '<g id="kuckuck" opacity="0"><g transform="translate(514 84) scale(.5)">' + Z.vogel({ f: '#ffd23f' }) + '</g></g>';
      // Kühlschrank
      if (s.kuehl) h += '<path fill="#fff3b0" opacity=".16" d="M28 180h124l120 300h-300z"/><rect class="l" x="24" y="150" width="130" height="322" rx="10" fill="#aab6c6"/><rect class="l" x="34" y="162" width="110" height="298" rx="4" fill="#fff3b0"/>'
        + '<path class="l n" style="stroke:#c9b56a" d="M34 250h110M34 340h110"/><circle class="d" cx="62" cy="328" r="10" fill="#e23b6a"/><path class="d n" style="stroke:#3d8a3a" d="M62 318q-4 -10 -10 -10M62 318q4 -10 10 -8"/>'
        + (s.milch === 'drin' ? '<g id="milch"><g transform="translate(96 310) scale(1.1)">' + MILCH + '</g></g>' : '')
        + '<path class="l" fill="#dfe8f2" d="M154 150l20 16v322l-20 -16z"/>';
      else h += '<g id="kuehl"><rect class="l" x="24" y="150" width="130" height="322" rx="10" fill="#dfe8f2"/><path class="l n" d="M24 240h130"/><path class="l n" style="stroke:#8d98a8;stroke-width:6" d="M138 180v40M138 262v70"/>'
        + '<circle class="d" cx="60" cy="290" r="9" fill="#e23b2e"/><rect class="d" x="80" y="300" width="22" height="16" fill="#ffd23f" transform="rotate(-8 91 308)"/><path class="d" fill="#3fcf6b" d="M50 350l12 -18l12 18z"/></g>';
      h += '<path class="l" fill="#8d98a8" d="M30 472h20v10h-20zM128 472h20v10h-20z"/>';
      // Mauseloch
      h += '<path class="l" fill="#141a30" d="M178 470v-26a26 26 0 0 1 52 0v26z"/>';
      // Buffet rechts: Wecker, Toaster, Schranktür (Geheimnis)
      h += '<rect class="l" x="574" y="336" width="216" height="136" rx="4" fill="#4f8a8b"/><rect class="l" x="566" y="326" width="232" height="16" rx="4" fill="#c9b99a"/>'
        + '<rect class="l" x="588" y="356" width="88" height="100" rx="4" fill="#5fa3a3"/><rect class="l" x="688" y="356" width="88" height="100" rx="4" fill="#5fa3a3"/><circle class="d" cx="666" cy="404" r="5" fill="#ffd23f"/><circle class="d" cx="698" cy="404" r="5" fill="#ffd23f"/>'
        + '<g id="geist" opacity="0"><g transform="translate(732 404)"><path class="l" fill="#fff" d="M-26 34v-40a26 26 0 0 1 52 0v40l-9 -8l-9 8l-8 -8l-9 8l-8 -8z"/><ellipse cx="-9" cy="-6" rx="5" ry="7" fill="#3a3340"/><ellipse cx="9" cy="-6" rx="5" ry="7" fill="#3a3340"/><ellipse cx="0" cy="10" rx="5" ry="4" fill="#3a3340"/>'
        + '<path class="l" fill="#3b8cff" d="M-22 -24q22 -22 44 0q8 -30 26 -26q-4 6 -2 12q-30 -10 -46 14z"/><circle class="d" cx="48" cy="-48" r="6" fill="#fff"/></g></g>'
        + '<g id="wecker" class="fuss"><path class="l" fill="#e23b2e" d="M592 326q-8 -52 26 -54q34 2 26 54z"/><circle class="l" cx="618" cy="300" r="14" fill="#f6f1e6"/><path class="l n" d="M618 300v-9M618 300l6 4"/><circle class="l" cx="618" cy="268" r="6" fill="#c9ced6"/></g>'
        + (s.toast ? '<g id="toast"><rect class="l" x="716" y="254" width="44" height="46" rx="8" fill="#e6c79f"/>' + Z.auge(730, 270, 4) + Z.auge(746, 270, 4) + '<path class="d n" d="M730 280q8 6 16 0"/></g>' : '')
        + '<rect class="l" x="696" y="282" width="84" height="44" rx="10" fill="#c9ced6"/><path class="l n" d="M712 290h52"/><rect class="l" x="772" y="296" width="10" height="16" rx="3" fill="#3a3340"/>';
      // Regal, Topf als Gegengewicht, Schnur über zwei Haken zur Käseglocke
      h += '<rect class="l" x="588" y="150" width="130" height="12" fill="#c9b99a"/><path class="l n" d="M600 162v16l14 -16M706 162v16l-14 -16"/>'
        + '<path class="l n" style="stroke:#e6dfc8;stroke-width:2.5" d="M430 ' + (246 - hoch) + 'V16H646V' + (s.glocke ? 196 : 100) + '"/><circle class="l" cx="430" cy="14" r="6" fill="#8d98a8"/><circle class="l" cx="646" cy="14" r="6" fill="#8d98a8"/>'
        + '<g id="topf"><g transform="translate(646 ' + (s.glocke ? 246 : 150) + ')"><path class="l n" style="stroke-width:5" d="M-26 -40q26 -26 52 0"/><path class="l" fill="#c9714a" d="M-36 -40h72v28q0 12 -12 12h-48q-12 0 -12 -12z"/><path class="l" fill="#a85a38" d="M-42 -44h84v10h-84z"/><path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".35" d="M-24 -26v14"/></g></g>';
      // Tisch, Besen, Käse unter der Glocke
      h += '<path class="l" fill="#8a6240" d="M318 346h18v126h-18zM524 346h18v126h-18z"/><rect class="l" x="300" y="330" width="260" height="18" rx="4" fill="#b98352"/>'
        + '<g id="besen"><path class="l n" style="stroke:#c99562;stroke-width:8" d="M312 322L262 452"/><path class="l" fill="#ffd23f" d="M246 446l34 12l-10 26l-44 -16z"/><path class="d n" style="stroke:#b98a00" d="M244 458l-8 18M256 462l-8 18M268 466l-8 18"/></g>';
      if (s.maus !== 'tisch' && s.maus !== 'kaese') h += '<g id="kaese"><g transform="translate(428 330)">' + kaese() + '</g></g>';
      h += '<g id="glocke"><g transform="translate(430 ' + (330 - hoch) + ')"><path class="l" fill="#fff" fill-opacity=".22" d="M-56 0v-36q0 -42 56 -42t56 42v36z"/><path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".7" d="M-40 -34q2 -24 22 -30"/><circle class="l" cx="0" cy="-84" r="8" fill="#e6dfc8"/></g></g>';
      // Napf
      h += '<g id="napf"><path class="l" fill="#3b8cff" d="M678 548l8 -30h60l8 30z"/><ellipse class="l" cx="716" cy="518" rx="30" ry="8" fill="' + (s.milch === 'napf' ? '#fff' : '#22408a') + '"/></g>';
      // Katze, Maus
      h += katze(s);
      if (s.maus === 'loch') h += '<g id="maus">' + maus(196, 466, false, true) + '</g>';
      if (s.maus === 'lauf') h += '<g id="maus">' + maus(204, 468, false) + '</g>';
      if (s.maus === 'tisch') h += '<g id="maus">' + maus(386, 328, true) + '</g>';
      if (s.maus === 'kaese') h += '<g id="maus">' + maus(214, 468, true) + '</g><g class="a-schweb"><path class="l" fill="#ff6f91" d="M214 400c-8 -13 -26 -3 -15 10l15 13l15 -13c11 -13 -7 -23 -15 -10z"/></g>';
      return h;
    },
    lauf: function (s, t, q) {
      if (s.katze !== 'trinkt') return;
      var g = schaut(t), a = q('#kt'), b = q('#ks');
      if (a) a.style.display = g ? 'none' : ''; if (b) b.style.display = g ? '' : 'none';
    },
    stellen: [
      { id: 'maus', r: [150, 392, 100, 100], gut: function (s, t) { var p = phase(t); return !(s.katze === 'trinkt' && s.glocke) || (p > 2.0 && p < 4.9); }, schlecht: function (s, t) { var p = phase(t); return s.katze === 'trinkt' && s.glocke && p > 0.2 && p < 1.3; }, tipp: async function (s, a) {
        if (s.katze === 'schlaeft') {
          a.ton('fiep'); a.mal({ maus: 'lauf' });
          await a.anim('#maus', [{ transform: 'translateX(0)' }, { transform: 'translateX(26px)' }], 400);
          a.ton('schnurr'); await a.anim('#ohr', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-8deg)' }, { transform: 'rotate(0deg)' }], 400);
          await a.anim('#maus', [{ transform: 'translateX(26px)' }, { transform: 'translateX(0)' }], 200);
          return a.gag(a.nr % 2 ? 'Die Maus traut sich nicht hinaus: Die Katze liegt genau vor ihrem Loch.' : 'Ein Katzenohr zuckt – schnell zurück! Die Katze muss hier weg, aber freundlich.');
        }
        if (!s.glocke) {
          a.ton('fiep'); a.mal({ maus: 'lauf' });
          await a.anim('#maus', [{ transform: 'translate(0,0)' }, { transform: 'translate(54px,-4px)' }, { transform: 'translate(120px,-140px)' }, { transform: 'translate(160px,-140px)' }], 900);
          a.ton('glocke'); await a.anim('#maus', [{ transform: 'translate(160px,-140px)' }, { transform: 'translate(146px,-140px)' }, { transform: 'translate(120px,-140px)' }, { transform: 'translate(54px,-4px)' }, { transform: 'translate(0,0)' }], 900);
          return a.gag('Dong! Die Maus rennt hinauf – und stösst mit der Nase ans Glas. Die Käseglocke ist im Weg.');
        }
        if (schaut(a.t)) {
          a.ton('miau'); a.mal({ maus: 'lauf' });
          await a.anim('#maus', [{ transform: 'translateX(0)' }, { transform: 'translateX(34px)' }, { transform: 'translateX(0)' }], 450);
          return a.fehl('Halt! Die Katze hebt gerade den Kopf – die Maus huscht zurück. Warte, bis die Katze wieder trinkt.');
        }
        a.ton('fiep'); a.mal({ maus: 'lauf' });
        await a.anim('#maus', [{ transform: 'translate(0,0)' }, { transform: 'translate(54px,-4px)' }, { transform: 'translate(120px,-140px)' }, { transform: 'translate(182px,-140px)' }], 1000);
        a.ton('plopp'); a.mal({ maus: 'tisch' });
        await a.anim('#maus', [{ transform: 'translate(0,0)' }, { transform: 'translate(-62px,0)' }, { transform: 'translate(-128px,136px)' }, { transform: 'translate(-172px,140px)' }], 1000);
        a.mal({ maus: 'kaese' });
        return a.fertig('Geschafft! Die Maus schleppt den Käse in ihr Loch – und die Katze hat nichts gemerkt.');
      } },
      { id: 'milch', r: [44, 250, 104, 100], wenn: function (s) { return s.kuehl && s.milch === 'drin'; }, tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#milch', [{ transform: 'translate(0,0)' }, { transform: 'translate(20px,-30px)' }, { transform: 'translate(-40px,300px)', opacity: 0 }], 700);
        a.mal({ milch: 'tasche' });
        return a.weiter('Die Milchflasche ist eingepackt. Wer mag wohl Milch?');
      } },
      { id: 'kuehlschrank', r: [24, 150, 140, 320], tipp: async function (s, a) {
        if (!s.kuehl) {
          a.ton('knarr'); await a.anim('#kuehl', [{ transform: 'translateX(0)' }, { transform: 'translateX(4px)' }, { transform: 'translateX(0)' }], 250);
          a.mal({ kuehl: true });
          return a.weiter('Der Kühlschrank geht auf. Licht! Die Katze schnarcht zum Glück weiter. Was steht denn da drin?');
        }
        a.ton('klick');
        return a.gag(s.milch === 'drin' ? 'Brrr, kalt. Ein Radieschen – und eine Flasche Milch.' : 'Nur noch ein einsames Radieschen. Das mag hier niemand.');
      } },
      { id: 'napf', r: [662, 480, 110, 100], tipp: async function (s, a) {
        if (s.milch === 'tasche') {
          a.ton('wasser'); await a.warte(500); a.mal({ milch: 'napf' });
          return a.weiter('Gluck, gluck – der Napf ist voll Milch. Die Katze schläft aber tief und fest.');
        }
        a.ton('klick'); await a.anim('#napf', [{ transform: 'translateX(0)' }, { transform: 'translateX(5px)' }, { transform: 'translateX(0)' }], 300);
        return a.gag(s.milch === 'napf' ? 'Frische Milch. Die Katze müsste nur aufwachen und sie riechen.' : 'Der Katzennapf ist leer geleckt.');
      } },
      { id: 'wecker', r: [570, 240, 100, 96], tipp: async function (s, a) {
        a.ton('ring'); await a.anim('#wecker', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(9deg)' }, { transform: 'rotate(-9deg)' }, { transform: 'rotate(9deg)' }, { transform: 'rotate(-9deg)' }, { transform: 'rotate(0deg)' }], 600);
        if (s.katze === 'trinkt') return a.gag('Rrring! Die Katze schlabbert weiter. Milch ist wichtiger.');
        a.ton('miau'); a.mal({ katze: 'wach' }); await a.warte(700);
        if (s.milch !== 'napf') return a.sackgasse('Rrring! Die Katze ist hellwach, hat Hunger – und setzt sich genau vors Mauseloch.');
        await a.anim('#katze', [{ transform: 'translate(0,0)' }, { transform: 'translate(150px,10px)' }, { transform: 'translate(290px,12px)' }], 1100);
        a.mal({ katze: 'trinkt' });
        return a.weiter('Rrring! Die Katze schreckt hoch, riecht die Milch und tapst zum Napf. Der Weg ist frei – fast.');
      } },
      { id: 'topf', r: function (s) { return s.glocke ? [594, 180, 104, 96] : [594, 84, 104, 96]; }, tipp: async function (s, a) {
        if (s.glocke) { a.ton('metall'); await a.anim('#topf', [{ transform: 'translateY(0)' }, { transform: 'translateY(8px)' }, { transform: 'translateY(0)' }], 400); return a.gag('Der Topf baumelt als Gegengewicht an der Schnur.'); }
        a.ton('metall');
        a.anim('#glocke', [{ transform: 'translateY(0)' }, { transform: 'translateY(-104px)' }], 700);
        await a.anim('#topf', [{ transform: 'translate(0,0)' }, { transform: 'translate(0,96px)' }], 700);
        a.mal({ glocke: true });
        return a.weiter('Der Topf rutscht vom Regal und zieht an der Schnur: Die Käseglocke schwebt ganz leise nach oben!');
      } },
      { id: 'glocke', r: [374, 240, 112, 96], tipp: async function (s, a) {
        if (s.glocke) { a.ton('plopp'); return a.gag('Mmmh, der Käse liegt frei. Jetzt müsste nur noch jemand hinkommen.'); }
        a.ton('glocke'); await a.anim('#glocke', [{ transform: 'translateY(0)' }, { transform: 'translateY(-5px)' }, { transform: 'translateY(0)' }], 300);
        return a.gag(a.nr % 2 ? 'Ting! Die Käseglocke aus Glas ist viel zu schwer für eine Maus.' : 'Oben am Knauf ist eine Schnur festgebunden. Wohin führt die wohl?');
      } },
      { id: 'katze', r: function (s) { return s.katze === 'trinkt' ? [540, 440, 122, 110] : [236, 462, 160, 100]; }, tipp: async function (s, a) {
        if (s.katze === 'trinkt') { a.ton('schnurr'); return a.gag('Schlabber, schlabber. Ab und zu schaut sie sich um – eine Katze bleibt eine Katze.'); }
        a.ton('schnurr'); await a.anim('#ohr', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-8deg)' }, { transform: 'rotate(0deg)' }], 500);
        return a.gag(a.nr % 2 ? 'Schnurr … Die Katze träumt. Streicheln weckt sie nicht.' : 'Sie schmatzt im Schlaf. Bestimmt träumt sie von einem vollen Napf.');
      } },
      { id: 'schrank', r: [684, 352, 104, 108], tipp: async function (s, a) {
        a.ton('huch'); await a.anim('#geist', [{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(-10px)' }, { opacity: 1, transform: 'translateY(-4px)' }, { opacity: 1, transform: 'translateY(-10px)' }, { opacity: 0, transform: 'translateY(10px)' }], 1800);
        return a.geheim('Im Schrank wohnt ein kleines Gespenst mit Schlafmütze. «Buh … äh, gute Nacht!»');
      } },
      { id: 'toaster', r: [690, 244, 104, 92], tipp: async function (s, a) {
        a.ton('boing'); a.mal({ toast: !s.toast });
        return a.gag(s.toast ? 'Pling! Ein Toast hüpft heraus und lächelt. Um Mitternacht!' : 'Der Toast geht wieder schlafen.', true);
      } },
      { id: 'uhr', r: [464, 52, 100, 150], tipp: async function (s, a) {
        a.ton('kuckuck'); await a.anim('#kuckuck', [{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(-14px)' }, { opacity: 1, transform: 'translateY(-14px)' }, { opacity: 0, transform: 'translateY(10px)' }], 900);
        return a.gag(s.katze === 'schlaeft' ? 'Kuckuck! Die Katze kennt den Vogel schon und schläft weiter.' : 'Kuckuck! Es ist Mitternacht.');
      } },
      { id: 'mond', r: [190, 50, 136, 128], tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ mondzu: !s.mondzu });
        return a.gag(s.mondzu ? 'Der Mond macht die Augen zu. Er verrät nichts.' : 'Der Mond schaut wieder zu.', true);
      } },
      { id: 'besen', r: [222, 300, 100, 92], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#besen', [{ transform: 'translateX(0)' }, { transform: 'translateX(-5px)' }, { transform: 'translateX(0)' }], 300);
        return a.gag('Der Besen lehnt am Tisch. Für eine Maus wäre das eine prima Leiter.');
      } }
    ],
    naechster: function (s) {
      return !s.kuehl ? 'kuehlschrank' : s.milch === 'drin' ? 'milch' : s.milch === 'tasche' ? 'napf' : s.katze === 'schlaeft' ? 'wecker' : !s.glocke ? 'topf' : 'maus';
    }
  });
})();
