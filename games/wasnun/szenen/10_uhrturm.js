/* Bild 10 «Im Uhrturm» (Meister): lange Kette, bei der ein früher Schritt erst ganz am Schluss zählt (Vogelnest in der
   Glocke), kombinieren (Zahnrad + Achsbolzen), falsche Fährten (Riesen-Zahnrad, den Kuckuck fangen wollen), zwei Wege
   zur Kurbel, eine Sackgasse (Uhr starten, solange das Nest in der Glocke sitzt).
   Gemeinsam: Zahnrad vom Boden · Achsbolzen aus der Werkzeugkiste · Zahnrad + Bolzen · in die Lücke setzen ·
              Kurbel auf die Seiltrommel (Gewicht hochziehen) · Nest aus der Glocke auf den Balken · Pendel anstossen.
   Weg 1 «koerner»: Körner aus dem Sack · dem Kuckuck hinstreuen: er kommt fressen und lässt die Kurbel fallen.
   Weg 2 «meister»: den kleinen Stellzeiger fünfmal antippen (11:55 -> 12:00): zur vollen Stunde MUSS der Kuckuck
                    herauskommen und rufen - dabei fällt ihm die Kurbel aus dem Schnabel. Braucht kein einziges Ding. */
(function () {
  var Z = WASNUN.Z;
  function zahn(r, n, f, loch) {
    var d = '', i, a, rr;
    for (i = 0; i < n * 4; i++) { a = (i + 0.5) / (n * 4) * 2 * Math.PI; rr = (i % 4 < 2) ? r : r - 11; d += (i ? 'L' : 'M') + (Math.cos(a) * rr).toFixed(1) + ' ' + (Math.sin(a) * rr).toFixed(1); }
    return '<path class="l" fill="' + f + '" d="' + d + 'z"/><circle class="l" r="' + (r * 0.55).toFixed(0) + '" fill="none"/><circle class="l" r="' + (loch ? 9 : 7) + '" fill="' + (loch ? '#2b2233' : '#5b3a2e') + '"/>';
  }
  var BOLZEN = '<path class="l" fill="#8d98a8" d="M-6 -22h12v40h-12z"/><path class="l" fill="#5b6470" d="M-13 -30h26v10h-26z"/><path class="d n" d="M-6 0h12M-6 8h12"/>';
  var KOERNER = '<path class="l" fill="#f3c9a5" d="M-18 6q-6 -18 4 -22q14 -6 26 4q10 10 2 24q-20 8 -32 -6z"/><g fill="#ffd23f" class="d"><ellipse cx="-6" cy="-8" rx="5" ry="3.5"/><ellipse cx="6" cy="-10" rx="5" ry="3.5"/><ellipse cx="0" cy="0" rx="5" ry="3.5"/><ellipse cx="12" cy="0" rx="5" ry="3.5"/><ellipse cx="-10" cy="4" rx="5" ry="3.5"/></g>';
  var KURBEL = '<path class="l n" style="stroke:#8d98a8;stroke-width:8" d="M-18 14h18v-28h16"/><rect class="l" x="12" y="-22" width="14" height="16" rx="4" fill="#d64b3c"/><rect class="l" x="-26" y="8" width="12" height="12" fill="#5b6470"/>';
  function kuckuck(s) {
    var hat = s.kurbel === 'vogel', frisst = s.weg === 'koerner';
    return '<g id="kk"><g transform="translate(126 146)"><ellipse class="l" cx="0" cy="0" rx="22" ry="19" fill="#4aa3e8"/><path class="l" fill="#3b8cff" d="M-18 -2q8 14 20 6q-6 -10 -20 -6z"/><path class="l" fill="#f2a900" d="M19 -6l16 5l-16 6z"/>'
      + Z.auge(9, -8, 6, false, 1.5, 0) + '<path class="l" fill="#d64b3c" d="M-6 -18q4 -12 12 -8q-2 6 -4 10z"/>'
      + (hat ? '<g transform="translate(44 4) scale(.7)">' + KURBEL + '</g>' : '') + (frisst ? '<g fill="#ffd23f"><ellipse cx="30" cy="22" rx="5" ry="3"/><ellipse cx="44" cy="24" rx="5" ry="3"/><ellipse cx="18" cy="24" rx="5" ry="3"/></g>' : '') + '</g></g>';
  }
  WASNUN.szene({
    id: 'uhrturm', titel: 'Im Uhrturm', stufe: 4, wege: ['koerner', 'meister'],
    ziel: 'Die Turmuhr steht seit Tagen auf fünf vor zwölf. Unten wartet das ganze Dorf auf den Mittagsschlag. Bring sie zum Laufen!',
    start: function () { return { tasche: [], rad: 'boden', bolzen: true, sack: true, kurbel: 'vogel', min: 55, nest: 'glocke', gewicht: 'unten', laeuft: false, weg: '', bruch: false }; },
    dinge: {
      zahnrad: { name: 'Zahnrad', svg: '<g transform="translate(30 30) scale(.5)">' + zahn(46, 9, '#e9a23b', true) + '</g>' },
      bolzen: { name: 'Achsbolzen', svg: '<g transform="translate(30 34)">' + BOLZEN + '</g>' },
      zahnrad_achse: { name: 'Zahnrad mit Achse', svg: '<g transform="translate(30 30) scale(.5)">' + zahn(46, 9, '#e9a23b', false) + '<circle class="l" r="13" fill="#8d98a8"/></g>' },
      koerner: { name: 'Handvoll Körner', svg: '<g transform="translate(30 32)">' + KOERNER + '</g>' },
      kurbel: { name: 'Kurbel', svg: '<g transform="translate(30 32)">' + KURBEL + '</g>' }
    },
    kombi: [{ a: 'zahnrad', b: 'bolzen', gibt: 'zahnrad_achse', text: 'Der Bolzen passt genau ins Loch in der Mitte: Jetzt hat das Zahnrad eine Achse.' },
      { a: 'kurbel', b: 'zahnrad', nein: 'Die Kurbel hat einen Vierkant, das Zahnrad ein rundes Loch. Das wird nichts.' },
      { a: 'kurbel', b: 'zahnrad_achse', nein: 'Am Zahnrad kurbeln? Es gehört zuerst zwischen die anderen Räder.' }],
    nutzlos: function (s, d, st) {
      if (d === 'koerner' && st !== 'kuckuck') return 'Körner streuen? Hier pickt sie niemand auf. Wer in diesem Turm hat wohl einen Schnabel?';
      if (d === 'kurbel' && st !== 'trommel') return 'Die Kurbel hat einen Vierkant. Irgendwo muss das passende Gegenstück sein.';
      return '';
    },
    bild: function (s) {
      var m = s.laeuft ? 60 : s.min, wz = (m - 60) * 6;
      var h = '<rect width="800" height="600" fill="#5a4636"/><path class="d n" style="stroke:#4a382c" d="M0 120h800M0 250h800M0 380h800M110 0v120M330 120v130M560 0v120M660 250v130M200 380v110M470 380v110"/>'
        + '<rect class="l" x="-5" y="486" width="810" height="120" fill="#8a6240"/><path class="d n" style="stroke:#6b4a34" d="M0 524h800M0 562h800M180 486v38M520 486v38M340 524v38M640 524v38"/>'
        + '<path class="l" fill="#4a382c" d="M-5 -5h810v26h-810z"/>';
      // grosses Zifferblatt von hinten
      h += '<g id="blatt"><circle class="l" cx="400" cy="140" r="104" fill="#f6efd8"/><circle class="l n" cx="400" cy="140" r="90" style="stroke:#c9b99a"/>';
      for (var i = 0; i < 12; i++) h += '<path class="l n" style="stroke:#8a7a5a;stroke-width:4" d="M400 54v14" transform="rotate(' + i * 30 + ' 400 140)"/>';
      h += '<path class="l n" style="stroke-width:7" d="M400 140v-44" transform="rotate(' + (s.laeuft ? 0 : 28) + ' 400 140)"/><g id="gz" style="transform-origin:400px 140px;transform:rotate(' + (-wz) + 'deg)"><path class="l n" style="stroke-width:5" d="M400 140v-72"/></g><circle class="l" cx="400" cy="140" r="8" fill="#3a3340"/></g>';
      // Spinnennetz (Geheimnis)
      h += '<path class="n" stroke="#e6dfc8" stroke-width="2" opacity=".7" d="M0 22h70M22 22v70M0 22l60 60M22 44q20 6 26 26M22 64q10 2 14 14"/><g id="spinne"><path class="n" stroke="#e6dfc8" stroke-width="2" d="M44 22v24"/><g transform="translate(44 56)"><circle class="l" r="10" fill="#3a3340"/><path class="d n" d="M-9 -3l-10 -6M-9 3l-10 6M9 -3l10 -6M9 3l10 6"/><circle cx="-3" cy="-2" r="2" fill="#fff"/><circle cx="3" cy="-2" r="2" fill="#fff"/><rect class="d" x="-6" y="-20" width="12" height="9" fill="#3a3340"/><rect class="d" x="-9" y="-12" width="18" height="3" fill="#3a3340"/></g></g>';
      // Kuckuckshaus, Stellzeiger
      h += '<path class="l" fill="#8a5a3a" d="M70 196v-90l56 -44l56 44v90z"/><path class="l" fill="#6b4a34" d="M60 112l66 -52l66 52l-10 10l-56 -44l-56 44z"/><path class="l" fill="#2b2233" d="M100 174v-40a26 26 0 0 1 52 0v40z"/>'
        + kuckuck(s) + '<g id="kt"><path class="l" fill="#c99562" d="M100 174v-40a26 26 0 0 1 52 0v40z"/><circle cx="144" cy="152" r="3" fill="#3a3340"/></g><path class="l n" style="stroke:#c99562;stroke-width:6" d="M92 180h100"/>'
        + '<g id="stell"><circle class="l" cx="126" cy="262" r="42" fill="#f6efd8"/>';
      for (i = 0; i < 12; i++) h += '<path class="d n" style="stroke:#8a7a5a" d="M126 226v8" transform="rotate(' + i * 30 + ' 126 262)"/>';
      h += '<path class="l n" style="stroke-width:6" d="M126 262v-18" transform="rotate(' + (s.min === 60 ? 0 : -30 + 30 * (s.min - 55) / 5 * 0.9) + ' 126 262)"/><path class="l n" style="stroke:#d64b3c;stroke-width:4" d="M126 262v-30" transform="rotate(' + (s.min - 60) * 6 + ' 126 262)"/><circle cx="126" cy="262" r="5" fill="#3a3340"/><path class="l" fill="#d64b3c" d="M120 216h12l-6 10z"/></g>';
      // Räderwerk: grosses Rad, Lücke (oder eingesetztes Rad), kleines Rad mit Welle zum Zifferblatt
      h += '<path class="l n" style="stroke:#8d98a8;stroke-width:8" d="M410 330V236"/><rect class="l" x="180" y="318" width="250" height="24" rx="6" fill="#4a382c"/>'
        + '<g transform="translate(226 330)"><g id="ra" class="dreh">' + zahn(58, 11, '#c9714a', false) + '</g></g>'
        + (s.rad === 'drin' ? '<g transform="translate(326 330)"><g id="rb" class="dreh">' + zahn(46, 9, '#e9a23b', false) + '<circle class="l" r="13" fill="#8d98a8"/></g></g>'
          : '<circle class="l n" cx="326" cy="330" r="42" style="stroke:#e6dfc8;stroke-dasharray:7 9;stroke-width:3"/><circle class="l" cx="326" cy="330" r="9" fill="#2b2233"/>')
        + '<g transform="translate(404 330)"><g id="rc" class="dreh">' + zahn(36, 7, '#c9ced6', false) + '</g></g>';
      // Pendel
      h += '<g id="pendel" style="transform-origin:490px 250px"><path class="l n" style="stroke:#c9ced6;stroke-width:6" d="M490 250v190"/><circle class="l" cx="490" cy="446" r="26" fill="#ffd23f"/><circle class="n" cx="482" cy="438" r="8" stroke="#fff" stroke-width="4" opacity=".6"/></g><rect class="l" x="476" y="240" width="28" height="14" rx="4" fill="#5b6470"/>';
      // Seiltrommel mit Vierkant, Seil, Gewicht
      var gy = s.gewicht === 'oben' ? 370 : 462;
      h += '<path class="l n" style="stroke:#e6c79f;stroke-width:4" d="M600 320V' + (gy - 40) + '"/><g id="gew"><g transform="translate(600 ' + gy + ')"><path class="l" fill="#5b6470" d="M-22 -34h44l6 54h-56z"/><path class="l n" style="stroke-width:5" d="M-8 -34q8 -14 16 0"/><path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".3" d="M-12 -22l-4 30"/></g></g>'
        + '<g id="trommel"><rect class="l" x="560" y="268" width="80" height="56" rx="10" fill="#9a6b43"/><path class="d n" style="stroke:#e6c79f;stroke-width:3" d="M572 268v56M584 268v56M596 268v56M608 268v56M620 268v56"/><rect class="l" x="640" y="286" width="16" height="20" fill="#5b6470"/>'
        + (s.kurbel === 'trommel' ? '<g id="kdreh" style="transform-origin:662px 296px"><g transform="translate(680 290)">' + KURBEL + '</g></g>' : '') + '</g>';
      // Glocke mit Hammer und Vogelnest, Balken
      h += '<path class="l n" style="stroke:#4a382c;stroke-width:10" d="M620 40h150"/><g id="glocke" class="kopf"><path class="l n" d="M680 40v14"/><path class="l" fill="#e9a23b" d="M640 150q4 -96 40 -96t40 96z"/><path class="l" fill="#b98a00" d="M632 150h96v12h-96z"/></g>'
        + '<g id="hammer" class="rechtsu"><path class="l n" style="stroke:#8d98a8;stroke-width:6" d="M770 150l-40 -30"/><rect class="l" x="716" y="106" width="22" height="22" rx="4" fill="#5b6470" transform="rotate(36 727 117)"/></g>'
        + '<rect class="l" x="700" y="246" width="100" height="14" fill="#4a382c"/>';
      var nx = s.nest === 'glocke' ? 680 : 748, ny = s.nest === 'glocke' ? 168 : 244;
      h += '<g id="nest"><g transform="translate(' + nx + ' ' + ny + ')"><g transform="translate(0 -18) scale(.62)">' + Z.vogel({ f: '#b98352', zu: s.nest !== 'glocke' && !s.bruch }) + '</g><path class="l" fill="#9a6b43" d="M-34 -8q34 26 68 0q-4 22 -34 22t-34 -22z"/><path class="d n" style="stroke:#6b4a34" d="M-26 0l14 6M-4 4l12 4M14 6l12 -6"/><ellipse class="d" cx="-14" cy="-6" rx="7" ry="9" fill="#e6f1f5"/><ellipse class="d" cx="16" cy="-6" rx="7" ry="9" fill="#e6f1f5"/></g></g>'
        + (s.bruch ? Z.funken(680, 150, '#ff5a5f') : '');
      // Fensterluke mit Dorf
      h += '<g id="luke"><rect class="l" x="716" y="290" width="68" height="84" rx="30" fill="#a8dcf5"/><path fill="#93d48c" d="M718 350q30 -16 64 0v14q-34 10 -64 0z"/><path class="d" fill="#d64b3c" d="M730 346l10 -10l10 10zM752 348l8 -8l8 8z"/><circle cx="742" cy="358" r="3" fill="#3a3340"/><circle cx="754" cy="360" r="3" fill="#3a3340"/><circle cx="766" cy="358" r="3" fill="#3a3340"/></g>';
      // am Boden: Körnersack, Kurbel (wenn gefallen), Zahnrad, Werkzeugkiste, Riesen-Zahnrad
      h += '<g id="sack"><path class="l" fill="#d9b48a" d="M20 590q-14 -60 14 -74q-8 -14 6 -18h44q14 4 6 18q28 14 14 74z"/><path class="l n" style="stroke:#8a5a3a;stroke-width:4" d="M38 516h48"/><g fill="#ffd23f" class="d"><ellipse cx="50" cy="500" rx="6" ry="4"/><ellipse cx="66" cy="497" rx="6" ry="4"/><ellipse cx="78" cy="501" rx="6" ry="4"/></g></g>';
      if (s.kurbel === 'boden') h += '<g id="kboden"><g transform="translate(150 470) scale(1.3)">' + KURBEL + '</g></g>';
      if (s.rad === 'boden') h += '<g id="rboden"><g transform="translate(322 540) scale(.9)">' + zahn(46, 9, '#e9a23b', true) + '</g></g>';
      h += '<g id="kiste"><path class="l" fill="#d64b3c" d="M408 588v-52h104v52z"/><path class="l" fill="#b53a2e" d="M408 536l10 -18h84l10 18z"/><path class="l n" style="stroke-width:5" d="M446 518q14 -16 28 0"/><rect class="l" x="452" y="548" width="16" height="12" fill="#ffd23f"/>'
        + (s.bolzen ? '<g transform="translate(494 522) rotate(30) scale(.9)">' + BOLZEN + '</g>' : '') + '</g>'
        + '<g id="riesen" class="fuss"><g transform="translate(728 512)">' + zahn(84, 14, '#6b7686', true) + '</g></g>';
      return h;
    },
    lauf: function (s, t, q) {
      var kk = q('#kk'), kt = q('#kt'), p = q('#pendel'), ra = q('#ra'), rb = q('#rb'), rc = q('#rc');
      if (kk) {
        var raus = s.kurbel !== 'vogel' ? (s.weg === 'koerner' ? 1 : 0) : (function () { var ph = t % 4.5; return ph < 0.3 ? ph / 0.3 * 0.55 : ph < 1.3 ? 0.55 : ph < 1.6 ? (1.6 - ph) / 0.3 * 0.55 : 0; })();
        if (s.ruf) raus = 1;
        kk.style.transform = 'translateX(' + (-34 + raus * 44).toFixed(1) + 'px)'; kk.style.opacity = raus > 0.05 ? 1 : 0;
        if (kt) kt.style.transform = 'translateX(' + (-raus * 56).toFixed(1) + 'px)';
      }
      if (p) p.style.transform = 'rotate(' + (s.laeuft ? Math.sin(t * 3) * 14 : 0).toFixed(1) + 'deg)';
      if (s.laeuft) { if (ra) ra.style.transform = 'rotate(' + (t * 40 % 360).toFixed(0) + 'deg)'; if (rb) rb.style.transform = 'rotate(' + (-t * 51 % 360).toFixed(0) + 'deg)'; if (rc) rc.style.transform = 'rotate(' + (t * 66 % 360).toFixed(0) + 'deg)'; }
    },
    stellen: [
      { id: 'kuckuck', r: [62, 56, 126, 136], tipp: async function (s, a) {
        if (s.kurbel !== 'vogel') { a.ton('kuckuck'); return a.gag(s.weg === 'koerner' ? 'Der Kuckuck pickt zufrieden seine Körner. Die Kurbel ist ihm jetzt egal.' : 'Der Kuckuck hat sich heiser gerufen und bleibt lieber drin.'); }
        a.ton('huch');
        return a.gag(['Schwupp – weg ist er! Der Kuckuck hat die Kurbel im Schnabel und ist schneller als jede Hand.', 'Wieder daneben. Fangen lässt sich der nie. Er müsste von selber herauskommen – und den Schnabel aufmachen.', 'Zu flink! Wann kommt ein Kuckuck freiwillig ganz heraus? Zum Fressen … oder wenn es seine Zeit ist.'][(a.nr - 1) % 3]);
      }, mit: {
        koerner: async function (s, a) {
          if (s.kurbel !== 'vogel') return a.gag('Der Kuckuck ist satt.');
          a.ton('pieps'); a.gib('koerner'); a.mal({ weg: 'koerner', ruf: true }); await a.warte(700); a.ton('metall');
          a.mal({ kurbel: 'boden', ruf: false });
          await a.anim('#kboden', [{ transform: 'translate(-20px,-300px) rotate(-90deg)' }, { transform: 'translate(0,0) rotate(0deg)' }], 600, { easing: 'ease-in' });
          return a.weiter('Körner! Der Kuckuck hüpft heraus, reisst den Schnabel auf – und die Kurbel scheppert auf den Boden.');
        }
      } },
      { id: 'stell', r: [72, 212, 108, 100], tipp: async function (s, a) {
        if (s.min >= 60) { a.ton('klick'); return a.gag('Der Stellzeiger steht auf zwölf. Weiter drehen lässt er sich nicht.'); }
        a.ton('klick'); a.mal({ min: s.min + 1 });
        if (s.min < 60) return a.wechsel('Klick – der kleine Stellzeiger rückt eine Minute vor: 11:' + s.min + '. Im Kuckuckshaus rumpelt es leise.');
        a.ton('kuckuck'); a.mal({ ruf: true }); await a.warte(600); a.ton('kuckuck');
        if (s.kurbel !== 'vogel') { await a.warte(500); a.mal({ ruf: false }); return a.gag('Zwölf Uhr auf dem Stellzeiger: «Kuckuck, Kuckuck!» Pflicht ist Pflicht.', true); }
        await a.warte(400); a.ton('metall'); a.mal({ kurbel: 'boden', ruf: false, weg: 'meister' });
        await a.anim('#kboden', [{ transform: 'translate(-20px,-300px) rotate(-90deg)' }, { transform: 'translate(0,0) rotate(0deg)' }], 600, { easing: 'ease-in' });
        return a.weiter('Punkt zwölf! Da MUSS er heraus und rufen: «Kuckuck!» – und schon fällt ihm die Kurbel aus dem Schnabel.');
      } },
      { id: 'kboden', r: [100, 410, 100, 96], wenn: function (s) { return s.kurbel === 'boden'; }, tipp: async function (s, a) {
        a.ton('metall'); a.mal({ kurbel: 'tasche' }); a.nimm('kurbel'); return a.weiter('Die Kurbel der Turmuhr, mit einem Vierkant am Ende.');
      } },
      { id: 'luecke', r: [276, 270, 96, 124], tipp: async function (s, a) {
        a.ton('klick');
        return a.gag(s.rad === 'drin' ? 'Das Zahnrad sitzt fest auf seiner Achse und greift links und rechts sauber ein.' : 'Zwischen dem grossen und dem kleinen Rad klafft eine Lücke – mit einem leeren Achsloch in der Mitte.');
      }, mit: {
        zahnrad_achse: async function (s, a) {
          a.ton('metall'); a.gib('zahnrad_achse'); a.mal({ rad: 'drin' }); await a.anim('#rb', [{ transform: 'rotate(-60deg)' }, { transform: 'rotate(0deg)' }], 500);
          return a.weiter('Klack! Das Zahnrad sitzt in der Lücke, die Zähne greifen ineinander.');
        },
        zahnrad: async function (s, a) { a.ton('metall'); await a.warte(300); a.ton('plumps'); return a.gag('Das Zahnrad passt genau in die Lücke – und fällt gleich wieder heraus. In seinem Loch fehlt eine Achse.'); },
        bolzen: async function (s, a) { a.ton('klick'); return a.gag('Der Bolzen passt ins Achsloch. Aber ein Bolzen allein dreht nichts weiter.'); }
      } },
      { id: 'ra', r: [168, 270, 108, 124], tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#ra', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(40deg)' }, { transform: 'rotate(0deg)' }], 700);
        return a.gag(s.rad === 'drin' ? 'Die Räder greifen ineinander. Jetzt fehlt nur der Schwung.' : 'Das grosse Rad dreht sich – und sonst gar nichts. Es greift ins Leere.');
      } },
      { id: 'trommel', r: [548, 244, 130, 110], tipp: async function (s, a) {
        a.ton('klick');
        return a.gag(s.gewicht === 'oben' ? 'Das Gewicht hängt oben. Die Uhr hat wieder Kraft für eine ganze Woche.' : 'Die Seiltrommel. Vorne ragt ein Vierkant heraus – da gehört eine Kurbel drauf.');
      }, mit: {
        kurbel: async function (s, a) {
          a.gib('kurbel'); a.mal({ kurbel: 'trommel' }); a.ton('knarr');
          a.anim('#kdreh', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(1080deg)' }], 1400, { easing: 'linear' });
          await a.anim('#gew', [{ transform: 'translateY(0)' }, { transform: 'translateY(-92px)' }], 1400);
          a.mal({ gewicht: 'oben' });
          return a.weiter('Kurbeln, kurbeln, kurbeln … das schwere Gewicht schwebt nach oben. Die Uhr hat wieder Kraft.');
        }
      } },
      { id: 'pendel', r: [440, 250, 100, 230], tipp: async function (s, a) {
        a.ton('tap');
        if (s.rad !== 'drin' || s.gewicht !== 'oben') {
          await a.anim('#pendel', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(-10deg)' }, { transform: 'rotate(6deg)' }, { transform: 'rotate(0deg)' }], 1400);
          return a.gag(s.gewicht !== 'oben' ? 'Tick … tack … aus. Das Pendel bleibt stehen: Das Gewicht liegt am Boden, die Uhr hat keine Kraft.' : 'Tick … tack … aus. Das Pendel bleibt stehen: Im Räderwerk fehlt ein Rad.');
        }
        a.mal({ laeuft: true }); await a.warte(900);
        a.ton('glocke'); a.anim('#glocke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(10deg)' }, { transform: 'rotate(-8deg)' }, { transform: 'rotate(0deg)' }], 700);
        await a.anim('#hammer', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-22deg)' }, { transform: 'rotate(0deg)' }], 350);
        if (s.nest === 'glocke') {
          a.ton('pieps'); a.mal({ bruch: true }); await a.warte(600);
          return a.sackgasse('DONG! Die Uhr läuft – aber in der Glocke sitzt ein Vogel auf seinem Nest! Er zetert, die Eier wackeln bedenklich.');
        }
        await a.warte(400); a.ton('glocke');
        return a.fertig(s.weg === 'meister' ? 'Tick, tack – DONG! Zwölf Schläge über dem Dorf. Und der Kuckuck ruft stolz mit: Er war heute der Schlüssel zu allem.' : 'Tick, tack – DONG! Zwölf Schläge hallen über das Dorf. Endlich Mittag: Der Bäcker winkt mit einem Gipfeli herauf.', { meister: s.weg === 'meister' });
      } },
      { id: 'nest', r: function (s) { return s.nest === 'glocke' ? [616, 40, 130, 160] : [694, 180, 106, 96]; }, tipp: async function (s, a) {
        if (s.nest === 'glocke') {
          a.ton('pieps'); await a.anim('#nest', [{ transform: 'translate(0,0)' }, { transform: 'translate(40px,30px)' }, { transform: 'translate(68px,76px)' }], 800);
          a.mal({ nest: 'balken' });
          return a.weiter('Ganz behutsam: Das Nest zieht um auf den Balken. Der Vogel plustert sich und brütet dort weiter.');
        }
        a.ton('pieps'); return a.gag('Piep. Auf dem Balken ist es ruhig und sicher. Die Vogelmutter döst.');
      } },
      { id: 'glocke', r: [616, 40, 130, 124], wenn: function (s) { return s.nest !== 'glocke'; }, tipp: async function (s, a) {
        a.ton('glocke'); await a.anim('#glocke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(8deg)' }, { transform: 'rotate(-6deg)' }, { transform: 'rotate(0deg)' }], 600);
        return a.gag('Ding! Ein leiser Ton zur Probe. Richtig schlagen kann nur die Uhr selbst.');
      } },
      { id: 'rboden', r: [272, 490, 100, 100], wenn: function (s) { return s.rad === 'boden'; }, tipp: async function (s, a) {
        a.ton('metall'); a.mal({ rad: 'tasche' }); a.nimm('zahnrad'); return a.weiter('Ein Zahnrad aus Messing, mittelgross. In der Mitte hat es nur ein leeres Loch.');
      } },
      { id: 'kiste', r: [404, 496, 112, 96], tipp: async function (s, a) {
        if (s.bolzen) { a.ton('metall'); a.mal({ bolzen: false }); a.nimm('bolzen'); return a.weiter('In der Werkzeugkiste liegt ein dicker Achsbolzen.'); }
        a.ton('knarr'); return a.gag('In der Kiste klimpern noch ein paar Schrauben. Zu klein für eine Turmuhr.');
      } },
      { id: 'sack', r: [6, 492, 110, 104], tipp: async function (s, a) {
        if (s.sack && s.kurbel === 'vogel') { a.ton('plopp'); a.mal({ sack: false }); a.nimm('koerner'); return a.weiter('Eine Handvoll Körner aus dem Sack. Der Turmwart füttert damit die Vögel.'); }
        a.ton('plopp'); return a.gag('Körner, Körner, Körner. Der Sack ist noch fast voll.');
      } },
      { id: 'riesen', r: [650, 420, 150, 176], tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#riesen', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(3deg)' }, { transform: 'rotate(0deg)' }], 500);
        return a.gag(a.nr % 2 ? 'Uff! Das Riesen-Zahnrad bewegt sich keinen Millimeter. Und in die kleine Lücke passt es sowieso nie.' : 'Ein Ersatzrad für das grosse Zifferblatt. Viel zu gross für hier.');
      } },
      { id: 'blatt', r: [300, 34, 200, 200], tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.laeuft ? 'Die grossen Zeiger laufen wieder.' : 'Das grosse Zifferblatt von hinten: fünf vor zwölf. Seit Tagen. Von Hand lassen sich die schweren Zeiger nicht schieben.');
      } },
      { id: 'luke', r: [704, 282, 96, 100], tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Unten auf dem Dorfplatz schauen alle herauf. Der Bäcker klopft ungeduldig auf seine Taschenuhr.');
      } },
      { id: 'gewicht', r: [552, 396, 100, 96], wenn: function (s) { return s.gewicht === 'unten'; }, tipp: async function (s, a) {
        a.ton('plumps'); return a.gag('Das Gewicht ist ganz abgelaufen und liegt am Boden. Von Hand hebt das niemand – dafür gibt es die Seiltrommel.');
      } },
      { id: 'spinne', r: [0, 0, 96, 96], tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#spinne', [{ transform: 'translateY(0)' }, { transform: 'translateY(60px)' }, { transform: 'translateY(54px)' }, { transform: 'translateY(60px)' }, { transform: 'translateY(0)' }], 1600);
        return a.geheim('Eine Spinne mit Zylinder seilt sich ab, zieht den Hut und klettert wieder hoch. Sie wohnt hier seit fünf vor zwölf.');
      } }
    ],
    naechster: function (s, weg) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (s.rad !== 'drin') return hat('zahnrad_achse') ? { stelle: 'luecke', ding: 'zahnrad_achse' } : s.rad === 'boden' ? 'rboden' : s.bolzen ? 'kiste' : { kombi: ['zahnrad', 'bolzen'] };
      if (s.gewicht !== 'oben') {
        if (hat('kurbel')) return { stelle: 'trommel', ding: 'kurbel' };
        if (s.kurbel === 'boden') return 'kboden';
        if (hat('koerner')) return { stelle: 'kuckuck', ding: 'koerner' };
        if (weg === 'meister' || s.min > 55 || !s.sack) return { stelle: 'stell', wink: 'Ein Kuckuck ruft immer zur vollen Stunde.' };
        return { stelle: 'sack', wink: 'Womit lockt man einen Vogel?' };
      }
      return s.nest === 'glocke' ? { stelle: 'nest', wink: 'Was passiert in der Glocke, wenn die Uhr schlägt?' } : 'pendel';
    }
  });
})();
