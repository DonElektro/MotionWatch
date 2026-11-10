/* Bild 6 «Am gefrorenen Weiher» (mittel): Dinge mitnehmen und kombinieren, ein Ding ändert seinen Zustand, Zeit (Schnee
   schmilzt), eine falsche Fährte (Axt), eine Sackgasse (heisses Wasser auf den Schneemann).
   Lösung: Eimer nehmen · mit Schnee füllen · Ast vom Schlitten · Zeitung aus dem Briefkasten · Ast + Zeitung = Fackel ·
   Fackel an der Laterne anzünden · Feuerschale anzünden · Schnee-Eimer übers Feuer · (warten, dabei) Handschuh vom
   Schneemann · heissen Eimer mit dem Handschuh nehmen · heisses Wasser aufs Eis beim Boot. */
(function () {
  var Z = WASNUN.Z, DAUER = 7;
  function eimer(inhalt) {
    return '<path class="l n" style="stroke-width:4" d="M-20 -34q20 -26 40 0"/><path class="l" fill="#8fa3b8" d="M-24 -36h48l-7 44h-34z"/><ellipse class="l" cx="0" cy="-36" rx="24" ry="7" fill="' + (inhalt === 'schnee' ? '#fff' : inhalt === 'heiss' ? '#7cc4ee' : '#5f7186') + '"/>'
      + (inhalt === 'schnee' ? '<path class="l" fill="#fff" d="M-22 -37q6 -16 22 -16t22 16z"/>' : '')
      + (inhalt === 'heiss' ? '<path class="d n" style="stroke:#fff" d="M-8 -44q-6 -8 0 -14t0 -12M8 -46q-6 -8 0 -14t0 -10"/>' : '');
  }
  var AST = '<path class="l" fill="#8a5a3a" d="M-6 26l-4 -50l10 -2l6 50z"/><path class="l n" style="stroke:#8a5a3a;stroke-width:5" d="M-4 -6l-14 -12M2 -14l12 -10"/>';
  var ZEITUNG = '<g transform="rotate(-10)"><rect class="l" x="-22" y="-16" width="44" height="32" rx="3" fill="#f6f1e6"/><path class="d n" d="M-16 -8h20M-16 -1h32M-16 6h32"/><rect x="8" y="-11" width="9" height="7" fill="#8ea0b6"/></g>';
  function fackel(an) {
    return '<path class="l" fill="#8a5a3a" d="M-5 28l-3 -40h12l3 40z"/><path class="l" fill="#f6f1e6" d="M-12 -8q-4 -18 12 -20q16 2 12 20z"/><path class="d n" d="M-8 -14h16"/>'
      + (an ? '<g class="fuss a-flack"><path class="l" fill="#f2711c" d="M0 -22q-18 -6 -10 -22q4 6 6 2q-2 -14 8 -22q0 12 8 16q8 20 -12 26z"/><path fill="#ffd23f" d="M1 -24q-8 -4 -4 -12q2 4 4 0q2 6 4 6q2 6 -4 6z"/></g>' : '');
  }
  var HANDSCHUH = '<path class="l" fill="#d64b3c" d="M-16 22v-30q0 -18 16 -18t16 18v6l8 -8q8 -4 10 4l-16 22v14z"/><path class="l" fill="#fff" d="M-18 20h36v10h-36z"/>';
  function ente(froh) {
    return '<g id="ente" class="fuss"><ellipse class="l" cx="0" cy="-18" rx="24" ry="17" fill="#fff"/><path class="l" fill="#fff" d="M14 -22q16 -8 22 0q-10 10 -22 6z"/>'
      + '<circle class="l" cx="-12" cy="-46" r="16" fill="#fff"/><path class="l" fill="#f2a900" d="M-26 -46l-18 4l18 8z"/>' + Z.auge(-16, -50, 5, froh, -1, 0)
      + '<path class="l" fill="#3b8cff" d="M-26 -32q14 8 28 0l2 9q-16 8 -32 0z"/><path class="l" fill="#3b8cff" d="M-2 -28l8 18l-10 2z"/>'
      + '<path class="l" fill="#d64b3c" d="M-26 -58q14 -14 28 0z"/><circle class="d" cx="-12" cy="-68" r="5" fill="#fff"/></g>';
  }
  WASNUN.szene({
    id: 'weiher', titel: 'Am gefrorenen Weiher', stufe: 2,
    ziel: 'Das Boot der Ente ist im Weiher festgefroren. Hilf ihr heim ins warme Entenhaus!',
    start: function () { return { tasche: [], eimerWo: 'boden', feuer: false, ab: 0, heiss: false, ast: true, zeitung: true, handschuh: true, frei: false, mann: 'ok' }; },
    dinge: {
      eimer: { name: 'Leerer Eimer', svg: '<g transform="translate(30 42)">' + eimer('') + '</g>' },
      eimer_schnee: { name: 'Eimer voll Schnee', svg: '<g transform="translate(30 44)">' + eimer('schnee') + '</g>' },
      eimer_heiss: { name: 'Eimer mit heissem Wasser', svg: '<g transform="translate(30 46)">' + eimer('heiss') + '</g>' },
      ast: { name: 'Ast', svg: '<g transform="translate(30 30)">' + AST + '</g>' },
      zeitung: { name: 'Zeitung', svg: '<g transform="translate(30 30)">' + ZEITUNG + '</g>' },
      fackel: { name: 'Fackel', svg: '<g transform="translate(30 30)">' + fackel(false) + '</g>' },
      fackel_an: { name: 'Brennende Fackel', svg: '<g transform="translate(30 36) scale(.85)">' + fackel(true) + '</g>' },
      handschuh: { name: 'Handschuh', svg: '<g transform="translate(26 28) scale(.9)">' + HANDSCHUH + '</g>' }
    },
    kombi: [{ a: 'ast', b: 'zeitung', gibt: 'fackel', text: 'Die Zeitung fest um den Ast gewickelt: eine Fackel! Jetzt fehlt nur noch eine Flamme.' }],
    nutzlos: function (s, d, st) {
      if (d === 'eimer_heiss' && st !== 'boot' && st !== 'mann') return 'Vorsicht, heisses Wasser! Das gehört dorthin, wo etwas auftauen soll.';
      if (d === 'fackel_an' && st === 'mann') return 'Der Schneemann schielt nervös auf die Flamme. Bitte nicht!';
      return '';
    },
    bild: function (s) {
      var h = '<rect width="800" height="600" fill="#b7c4ea"/><rect y="170" width="800" height="120" fill="#e9c9dc" opacity=".55"/>'
        + '<g id="mond"><circle class="l" cx="620" cy="84" r="34" fill="#fdf3c0"/><circle cx="608" cy="92" r="6" fill="#eadf9f"/><circle cx="632" cy="72" r="4" fill="#eadf9f"/></g>'
        + '<g class="a-schweb" fill="#fff"><circle cx="70" cy="120" r="4"/><circle cx="250" cy="90" r="3"/><circle cx="420" cy="150" r="4"/><circle cx="520" cy="60" r="3"/><circle cx="700" cy="200" r="4"/><circle cx="770" cy="70" r="3"/><circle cx="160" cy="30" r="3"/><circle cx="480" cy="240" r="3"/></g>' + Z.stern(120, 60, 7) + Z.stern(300, 40, 6) + Z.stern(460, 90, 5) + Z.stern(730, 150, 6) + Z.stern(40, 150, 5)
        + '<path class="l" fill="#eef3fd" d="M-5 300q160 -70 330 -20t260 -30t230 20v340h-820z"/><path fill="#d5def5" d="M0 330q150 -50 320 -6q-170 -20 -320 40z"/>';
      // Tanne mit Schnee, Laterne am Pfosten
      h += '<g id="tanne" class="fuss">' + Z.tanne(196, 330, 1.05) + '<path class="l" fill="#fff" d="M196 130l22 32q-22 -8 -44 0zM196 196l34 44q-34 -10 -68 0z"/></g>'
        + '<g id="schneefall" opacity="0"><circle cx="180" cy="210" r="7" fill="#fff"/><circle cx="210" cy="230" r="6" fill="#fff"/><circle cx="196" cy="190" r="5" fill="#fff"/></g>'
        + '<circle cx="86" cy="262" r="70" fill="#ffd98a" opacity=".3"/><path class="l n" style="stroke:#6d5a48;stroke-width:8" d="M54 470V200h34"/>'
        + '<g id="laterne" class="kopf"><path class="l n" d="M88 200v18"/><path class="l" fill="#3a3340" d="M68 232l20 -16l20 16z"/><rect class="l" x="70" y="232" width="36" height="46" rx="4" fill="#ffe9a8"/><path class="l n" d="M88 232v46"/>'
        + '<g class="fuss a-flack"><path class="d" fill="#f2711c" d="M88 272q-10 -4 -6 -14q2 -8 6 -12q4 6 6 12q4 10 -6 14z"/></g><rect class="l" x="66" y="278" width="44" height="8" fill="#3a3340"/></g>';
      // Schneemann (mit Handschuh am Arm), Axt im Eisblock
      if (s.mann === 'ok') h += '<g id="mann" class="fuss"><path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M300 262l-36 -26M372 262l44 -18"/><circle class="l" cx="336" cy="318" r="46" fill="#fff"/><circle class="l" cx="336" cy="252" r="34" fill="#fff"/>'
        + '<circle class="l" cx="336" cy="198" r="26" fill="#fff"/><path class="l" fill="#f2711c" d="M336 198l34 6l-34 6z"/>' + Z.auge(326, 190, 4) + Z.auge(346, 190, 4) + '<path class="d n" d="M324 210q12 8 24 0"/>'
        + '<path class="l" fill="#3fbf6b" d="M310 216q26 12 52 0l2 12q-28 12 -56 0z"/><path class="l" fill="#3fbf6b" d="M352 224l10 34l-14 2z"/><rect class="l" x="316" y="150" width="40" height="24" fill="#3a3340"/><rect class="l" x="306" y="172" width="60" height="7" fill="#3a3340"/>'
        + '<circle cx="336" cy="244" r="4" fill="#3a3340"/><circle cx="336" cy="262" r="4" fill="#3a3340"/>'
        + (s.handschuh ? '<g id="hs"><g transform="translate(424 236) scale(.62) rotate(20)">' + HANDSCHUH + '</g></g>' : '') + '</g>';
      else h += '<ellipse class="l" cx="336" cy="356" rx="70" ry="14" fill="#9fd3ee"/><rect class="l" x="316" y="326" width="40" height="24" fill="#3a3340"/><path class="l" fill="#f2711c" d="M366 352l30 4l-30 6z"/>' + Z.auge(300, 350, 4) + Z.auge(316, 350, 4) + '<path class="d n" d="M298 362q10 -6 20 0"/>';
      h += '<g id="axt"><path class="l" fill="#cfeaf8" d="M520 372l10 -52l60 -8l14 60z" opacity=".9"/><path class="l n" style="stroke:#8a5a3a;stroke-width:7" d="M556 350l34 -62"/><path class="l" fill="#aab6c6" d="M580 280l22 -10q10 16 2 30l-20 -6z"/><path class="d n" style="stroke:#fff" d="M532 360l8 -30"/></g>';
      // Entenhaus auf der Insel, Briefkasten
      h += '<ellipse class="l" cx="690" cy="416" rx="76" ry="20" fill="#fff"/><path class="l" fill="#c99562" d="M652 410v-44h72v44z"/><path class="l" fill="#d64b3c" d="M640 370l48 -38l48 38z"/><path class="l" fill="#fff" d="M688 332l22 18q-22 -8 -44 0z"/>'
        + '<path class="l" fill="#ffd23f" d="M676 410v-22a12 12 0 0 1 24 0v22z"/><circle cx="688" cy="356" r="6" fill="#ffe9a8" class="d"/><g id="hausrauch" class="a-schweb"><circle cx="716" cy="318" r="7" fill="#fff" opacity=".8"/><circle cx="724" cy="302" r="5" fill="#fff" opacity=".6"/></g>'
        + '<path class="l n" style="stroke:#6d5a48;stroke-width:7" d="M752 330v-70"/><g id="kasten"><rect class="l" x="716" y="222" width="72" height="42" rx="12" fill="#ffd23f"/><path class="l n" d="M728 244h30"/>'
        + (s.zeitung ? '<g transform="translate(772 226) rotate(-60) scale(.8)"><rect class="l" x="-22" y="-10" width="44" height="20" rx="8" fill="#f6f1e6"/><path class="d n" d="M-12 -3h24M-12 4h24"/></g>' : '') + '</g>';
      // Eis mit Eisloch (Geheimnis: Fisch), Boot mit Ente
      h += '<path class="l" fill="#cfeaf8" d="M150 470q20 -80 250 -86t300 60q20 110 -250 122t-300 -96z"/><path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" d="M230 500l60 -20M540 420l70 14M330 410l40 -8M560 520l50 -14"/>'
        + '<g id="fisch"><g transform="translate(310 448)"><path class="l" fill="#f2a05a" d="M-16 0q16 -18 34 0q-18 18 -34 0zM-14 0l-14 -10v20z"/>' + Z.auge(8, -3, 3) + '<path class="l" fill="#d64b3c" d="M-2 6q8 6 14 0l2 6q-8 4 -16 0z"/></g></g>'
        + '<ellipse class="l" cx="310" cy="446" rx="34" ry="13" fill="#3a6ea5"/><path class="n" stroke="#fff" stroke-width="3" d="M286 444q10 -6 20 0"/>';
      if (s.frei) h += '<ellipse cx="470" cy="486" rx="150" ry="40" fill="#3a6ea5"/><path class="n" stroke="#fff" stroke-width="3" stroke-linecap="round" d="M360 490q14 -8 28 0M540 496q14 -8 28 0M430 510q14 -8 28 0"/>';
      h += '<g id="boot"' + (s.frei ? ' class="a-wipp"' : '') + '><g transform="translate(' + (s.frei ? 520 : 450) + ' 478)">' + '<g transform="translate(-4 -8)">' + ente(s.frei) + '</g>'
        + '<path class="l" fill="#d64b3c" d="M-70 -14h140q-8 34 -40 34h-60q-32 0 -40 -34z"/><path class="l n" style="stroke:#fff;stroke-width:4" d="M-58 -2h116"/>'
        + '<g id="ruder" class="dreh"><path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M20 -30l44 44"/><ellipse class="l" cx="68" cy="18" rx="9" ry="14" fill="#c99562" transform="rotate(-45 68 18)"/></g></g></g>';
      if (!s.frei) h += '<path class="l" fill="#eaf6fd" d="M372 492q10 -14 26 -6q8 -12 24 -4q40 8 82 0q14 -8 22 4q18 -8 24 8q-90 16 -178 -2z"/>';
      // Feuerschale auf Dreibein, Eimer darüber
      h += '<path class="l n" style="stroke:#3a3340;stroke-width:6" d="M136 546l22 -70M214 546l-22 -70M176 552v-70"/>';
      if (s.feuer) h += '<circle cx="176" cy="450" r="74" fill="#ffb347" opacity=".25"/><g class="fuss a-flack"><path class="l" fill="#f2711c" d="M176 468q-40 -8 -26 -44q8 12 12 6q-6 -28 16 -44q-2 20 12 28q4 -10 10 -12q18 48 -24 66z"/><path class="d" fill="#ffd23f" d="M176 466q-20 -6 -12 -26q6 8 8 2q0 -12 10 -20q2 12 8 16q8 20 -14 28z"/></g>';
      h += '<path class="l" fill="#9a6b43" d="M146 462l56 -12l4 10l-56 12z"/><path class="l" fill="#5b6470" d="M120 462h112q-4 34 -56 34t-56 -34z"/>';
      if (s.eimerWo === 'feuer') h += '<path class="l n" style="stroke:#3a3340;stroke-width:5" d="M112 470v-104h64v18"/><g id="topf"><g transform="translate(176 428)">' + eimer(s.heiss ? 'heiss' : 'schnee') + '</g></g>'
        + '<g id="dampf" style="opacity:' + (s.heiss ? 1 : 0) + '"><g class="a-schweb"><path class="l" fill="#fff" d="M150 372a12 12 0 0 1 14 -16a14 14 0 0 1 26 2a11 11 0 0 1 4 20q-24 6 -44 -6z"/><path class="l" fill="#fff" d="M180 336a8 8 0 0 1 10 -10a9 9 0 0 1 16 2a7 7 0 0 1 2 12q-16 4 -28 -4z"/></g></g>';
      if (s.eimerWo === 'boden') h += '<g id="eimer"><g transform="translate(58 562)">' + eimer('') + '</g></g>';
      // Schneehaufen, Schlitten mit Ast
      h += '<path class="l" fill="#fff" d="M236 596q-6 -44 30 -50q10 -26 40 -14q28 -8 36 20q22 8 14 44z"/><path class="d n" style="stroke:#c9d6f0" d="M270 566q10 -8 20 0M310 556q10 -8 20 0"/>'
        + '<g id="schlitten"><path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M556 580h96q14 0 14 -14M572 580v-22M636 580v-22"/><path class="l" fill="#c99562" d="M552 546h100l8 12h-116z"/>'
        + (s.ast ? '<g transform="translate(600 540) rotate(78)">' + AST + '</g>' : '') + '</g>';
      return h;
    },
    lauf: function (s, t, q) {
      var d = q('#dampf'); if (d && !s.heiss && s.eimerWo === 'feuer') d.style.opacity = Math.max(0, Math.min(1, (t - s.ab) / DAUER)).toFixed(2);
    },
    uhr: function (s, t) {
      if (s.eimerWo === 'feuer' && !s.heiss && t - s.ab > DAUER) return { setze: { heiss: true }, text: 'Der Schnee ist geschmolzen – das Wasser im Eimer dampft!', ton: 'pfeif' };
    },
    stellen: [
      { id: 'eimer', r: [8, 486, 100, 110], wenn: function (s) { return s.eimerWo === 'boden'; }, tipp: async function (s, a) {
        a.ton('metall'); a.mal({ eimerWo: 'tasche' }); a.nimm('eimer');
        return a.weiter('Ein leerer Eimer. Den kann man bestimmt mit etwas füllen.');
      } },
      { id: 'feuer', r: [106, 350, 140, 200], tipp: async function (s, a) {
        if (s.eimerWo === 'feuer') {
          a.ton(s.heiss ? 'zisch' : 'tropf'); await a.anim('#topf', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(4deg)' }, { transform: 'rotate(0deg)' }], 300);
          return a.gag(s.heiss ? 'Autsch! Der Henkel ist glühend heiss. Mit blossen Fingern geht das nicht.' : 'Es zischt und tropft schon. Der Schnee braucht noch ein Momentchen.');
        }
        a.ton(s.feuer ? 'zisch' : 'puff');
        return a.gag(s.feuer ? 'Das Feuer knistert. Schön warm – hier könnte man etwas aufwärmen.' : 'In der Feuerschale liegt Holz bereit. Aber sie ist kalt.');
      }, mit: {
        fackel_an: async function (s, a) {
          if (s.feuer) return a.gag('Das Feuer brennt doch schon.');
          a.ton('zisch'); a.gib('fackel_an'); a.mal({ feuer: true }); await a.warte(500);
          return a.weiter('Die Feuerschale brennt! Die Fackel wandert gleich mit ins Feuer.');
        },
        fackel: async function (s, a) { a.ton('puff'); return a.gag('Die Fackel brennt noch nicht. Wo gibt es hier schon eine Flamme?'); },
        eimer_schnee: async function (s, a) {
          if (!s.feuer) { a.ton('puff'); return a.gag('Auf der kalten Feuerschale bleibt Schnee einfach Schnee.'); }
          a.ton('metall'); a.gib('eimer_schnee'); a.mal({ eimerWo: 'feuer', ab: a.t, heiss: false });
          return a.weiter('Der Eimer hängt über dem Feuer. Jetzt braucht der Schnee etwas Zeit …');
        },
        eimer: async function (s, a) { a.ton('metall'); return a.gag('Ein leerer Eimer über dem Feuer? Da wird höchstens der Eimer warm.'); },
        handschuh: async function (s, a) {
          if (s.eimerWo !== 'feuer') return a.gag('Der Handschuh wärmt sich kurz am Feuer. Gemütlich.');
          if (!s.heiss) return a.gag('Der Schnee ist noch nicht geschmolzen. Hab noch einen Moment Geduld.');
          a.ton('metall'); a.gib('handschuh'); a.mal({ eimerWo: 'tasche' }); a.nimm('eimer_heiss');
          return a.weiter('Mit dem dicken Handschuh geht es: Du hast einen Eimer voll heissem Wasser.');
        }
      } },
      { id: 'schnee', r: [232, 500, 130, 98], tipp: async function (s, a) {
        a.ton('plumps'); return a.gag(a.nr % 2 ? 'Ein Schneeball! Er fliegt im hohen Bogen – und trifft niemanden.' : 'Schnee, Schnee, Schnee. Davon gibt es hier genug.');
      }, mit: {
        eimer: async function (s, a) { a.ton('plumps'); a.tausch('eimer', 'eimer_schnee'); return a.weiter('Der Eimer ist bis oben voll Schnee.'); },
        eimer_schnee: async function (s, a) { return a.gag('Mehr Schnee passt nicht hinein.'); }
      } },
      { id: 'boot', r: [376, 396, 150, 120], tipp: async function (s, a) {
        a.ton('quak'); a.anim('#ruder', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-30deg)' }, { transform: 'rotate(0deg)' }, { transform: 'rotate(-30deg)' }, { transform: 'rotate(0deg)' }], 700);
        await a.anim('#ente', [{ transform: 'translateY(0)' }, { transform: 'translateY(-8px)' }, { transform: 'translateY(0)' }], 700);
        return a.gag(a.nr % 2 ? 'Quak! Die Ente rudert und rudert – das Boot bewegt sich keinen Zentimeter.' : 'Das Eis hält das Boot eisern fest. Ziehen und Schieben nützt nichts.');
      }, mit: {
        eimer_heiss: async function (s, a) {
          a.ton('wasser'); a.ton('zisch'); a.gib('eimer_heiss'); await a.warte(700); a.mal({ frei: true }); a.ton('quak');
          await a.anim('#boot', [{ transform: 'translateX(-70px)' }, { transform: 'translateX(0)' }], 900);
          return a.fertig('Zisch! Das Eis schmilzt, das Boot schaukelt frei – und die Ente rudert heim an den warmen Ofen.');
        },
        eimer_schnee: async function (s, a) { a.ton('quak'); return a.gag('Noch mehr Schnee aufs Eis? Die Ente schüttelt den Kopf.'); },
        fackel_an: async function (s, a) { a.ton('zisch'); return a.gag('Die kleine Flamme kitzelt das dicke Eis nur. Da braucht es viel mehr Wärme.'); },
        handschuh: async function (s, a) { a.ton('quak'); return a.gag('Die Ente hat schon einen Schal. Einen Handschuh braucht sie nicht – sie hat Flügel.'); }
      } },
      { id: 'hs', r: [374, 190, 96, 96], wenn: function (s) { return s.handschuh && s.mann === 'ok'; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ handschuh: false }); a.nimm('handschuh');
        return a.weiter('Der Schneemann leiht dir seinen dicken Handschuh. Damit verbrennt man sich nicht so schnell.');
      } },
      { id: 'mann', r: [270, 150, 110, 215], tipp: async function (s, a) {
        a.ton('boing'); await a.anim('#mann', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(4deg)' }, { transform: 'rotate(-3deg)' }, { transform: 'rotate(0deg)' }], 500);
        return a.gag(a.nr % 2 ? 'Der Schneemann wackelt mit der Rüeblinase. Kalt hat er es gern.' : 'Er steht einfach da und lächelt. Wärme ist nichts für ihn.');
      }, mit: {
        eimer_heiss: async function (s, a) {
          a.ton('wasser'); a.ton('zisch'); a.gib('eimer_heiss'); await a.anim('#mann', [{ transform: 'scale(1,1)' }, { transform: 'scale(1.2,.3)' }], 800);
          a.mal({ mann: 'pfuetze' }); await a.warte(500);
          return a.sackgasse('O nein! Der Schneemann schmilzt zur Pfütze und schaut ganz beleidigt.');
        },
        eimer_schnee: async function (s, a) { a.ton('plumps'); return a.gag('Der Schneemann freut sich über Nachschub. Dicker wird er davon nicht.'); }
      } },
      { id: 'laterne', r: [36, 190, 110, 120], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#laterne', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(10deg)' }, { transform: 'rotate(-8deg)' }, { transform: 'rotate(0deg)' }], 700);
        return a.gag('Die Laterne schaukelt. Ihre kleine Flamme ist das einzige Feuer weit und breit.');
      }, mit: {
        fackel: async function (s, a) { a.ton('zisch'); a.tausch('fackel', 'fackel_an'); return a.weiter('Die Fackel fängt Feuer! Jetzt hast du eine Flamme zum Mitnehmen.'); },
        fackel_an: async function (s, a) { return a.gag('Die Fackel brennt schon.'); },
        zeitung: async function (s, a) { a.ton('zisch'); return a.gag('Autsch! So verbrennst du dir fast die Finger. Die Zeitung bräuchte einen Stiel.'); },
        ast: async function (s, a) { a.ton('puff'); return a.gag('Der dicke Ast fängt an der kleinen Flamme kein Feuer. Er bräuchte etwas, das leicht brennt.'); }
      } },
      { id: 'kasten', r: [700, 200, 100, 110], tipp: async function (s, a) {
        if (s.zeitung) { a.ton('plopp'); a.mal({ zeitung: false }); a.nimm('zeitung'); return a.weiter('Die Zeitung von gestern. Lesen will die niemand mehr – aber Papier brennt gut.'); }
        a.ton('klick'); return a.gag('Der Briefkasten ist leer. Im Winter schreibt der Ente kaum jemand.');
      } },
      { id: 'schlitten', r: [540, 500, 130, 96], tipp: async function (s, a) {
        if (s.ast) { a.ton('plopp'); a.mal({ ast: false }); a.nimm('ast'); return a.weiter('Ein langer, trockener Ast. Der könnte ein guter Stiel sein.'); }
        a.ton('knarr'); await a.anim('#schlitten', [{ transform: 'translateX(0)' }, { transform: 'translateX(14px)' }, { transform: 'translateX(0)' }], 500);
        return a.gag('Der Schlitten rutscht ein Stück und kommt zurück. Hui!');
      } },
      { id: 'axt', r: [510, 270, 104, 110], tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#axt', [{ transform: 'translateX(0)' }, { transform: 'translateX(3px)' }, { transform: 'translateX(-3px)' }, { transform: 'translateX(0)' }], 300);
        return a.gag(a.nr % 2 ? 'Eine Axt – die wäre praktisch! Aber sie ist selber im Eis festgefroren.' : 'Keine Chance. Und zum Glück: Neben dem Boot Eis hacken wäre gefährlich.');
      } },
      { id: 'loch', r: [262, 396, 100, 96], tipp: async function (s, a) {
        a.ton('platsch'); await a.anim('#fisch', [{ transform: 'translateY(0) rotate(0deg)' }, { transform: 'translateY(-70px) rotate(-20deg)' }, { transform: 'translateY(-76px) rotate(10deg)' }, { transform: 'translateY(0) rotate(0deg)' }], 900);
        return a.geheim('Im Eisloch wohnt ein Fisch mit Schal. Er springt kurz hoch und grüsst.');
      } },
      { id: 'haus', r: [640, 320, 110, 110], tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Im Entenhaus brennt schon Licht, und aus dem Kamin steigt Rauch. Dort wartet der Tee.');
      } },
      { id: 'tanne', r: [146, 120, 100, 200], tipp: async function (s, a) {
        a.ton('plumps'); a.anim('#tanne', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(3deg)' }, { transform: 'rotate(-2deg)' }, { transform: 'rotate(0deg)' }], 500);
        await a.anim('#schneefall', [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(90px)' }, { opacity: 0, transform: 'translateY(110px)' }], 700);
        return a.gag('Schnee rieselt von der Tanne. Genau in den Kragen. Brrr!');
      } },
      { id: 'mond', r: [566, 30, 110, 110], tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#mond', [{ transform: 'translateY(0)' }, { transform: 'translateY(-8px)' }, { transform: 'translateY(0)' }], 500);
        return a.gag('Der Mond geht schon auf. Bald wird es bitterkalt – die Ente sollte heim.');
      } }
    ],
    naechster: function (s) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (hat('eimer_heiss')) return { stelle: 'boot', ding: 'eimer_heiss' };
      if (s.eimerWo === 'feuer') return s.handschuh ? 'hs' : !s.heiss ? { stelle: 'feuer', warte: true } : { stelle: 'feuer', ding: 'handschuh' };
      if (s.eimerWo === 'boden') return 'eimer';
      if (hat('eimer')) return { stelle: 'schnee', ding: 'eimer' };
      if (s.feuer) return { stelle: 'feuer', ding: 'eimer_schnee' };
      if (hat('fackel_an')) return { stelle: 'feuer', ding: 'fackel_an' };
      if (hat('fackel')) return { stelle: 'laterne', ding: 'fackel', wink: 'Die Laterne hat die einzige Flamme.' };
      if (s.ast) return 'schlitten';
      if (s.zeitung) return 'kasten';
      return { kombi: ['ast', 'zeitung'] };
    }
  });
})();
