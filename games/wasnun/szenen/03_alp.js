/* Bild 3 «Auf der Alp»: genau hinschauen (Schwanz im Alphorn, die Krähe äugt auf den Käse) + Kettenreaktion + eine Sackgasse (Krähe).
   Lösung: Glocke läuten (Krähe fliegt weg) · Käse vom Fenstersims stossen (Murmeltier kommt aus dem Alphorn) ·
   Alphorn blasen (Kuh kommt bis zum Gatter) · Gatter öffnen. Das Gatter darf auch früher geöffnet werden. */
(function () {
  var Z = WASNUN.Z;
  var KUH = { weide: [694, 322], tor: [600, 428], da: [452, 492] };
  function kuh(s) {
    var p = KUH[s.kuh], frisst = s.kuh === 'weide' && !s.horcht;
    return '<g id="kuh"><g transform="translate(' + p[0] + ' ' + p[1] + ') scale(.9)">'
      + '<path class="l n" d="M64 -66q22 6 18 36"/><path class="l" fill="#6b4a34" d="M76 -34q10 6 6 16q-10 -2 -6 -16z"/>'
      + '<path class="l" fill="#fff" d="M-34 -30h16v30h-16zM-12 -30h16v30h-16zM30 -30h16v30h-16zM50 -30h16v30h-16z"/><path fill="#3a3340" d="M-34 -6h16v6h-16zM-12 -6h16v6h-16zM30 -6h16v6h-16zM50 -6h16v6h-16z"/>'
      + '<ellipse class="l" cx="12" cy="-52" rx="60" ry="34" fill="#fff"/><path fill="#6b4a34" d="M-6 -82q30 -10 44 8q-8 24 -38 16q-12 -10 -6 -24zM46 -44q14 -12 24 2q2 14 -12 18q-14 -4 -12 -20z"/>'
      + '<ellipse class="l n" cx="12" cy="-52" rx="60" ry="34"/><ellipse class="l" cx="14" cy="-20" rx="14" ry="8" fill="#f2b8b0"/>'
      + '<g id="kuhkopf"><g transform="translate(0 ' + (frisst ? 30 : 0) + ') rotate(' + (frisst ? -18 : 0) + ' -40 -60)">'
      + '<path class="l" fill="#f6f1e6" d="M-78 -98q-10 -14 -2 -24q10 8 12 22zM-36 -98q10 -14 2 -24q-10 8 -12 22z"/>'
      + '<path class="l" fill="#6b4a34" d="M-88 -84q-18 -6 -22 6q12 8 24 4zM-28 -84q18 -6 22 6q-12 8 -24 4z"/>'
      + '<ellipse class="l" cx="-58" cy="-78" rx="30" ry="26" fill="#fff"/><path fill="#6b4a34" d="M-50 -103q20 2 22 22q-16 4 -24 -8z"/>'
      + '<ellipse class="l" cx="-62" cy="-58" rx="24" ry="15" fill="#f2b8b0"/><circle cx="-70" cy="-58" r="3" fill="#3a3340"/><circle cx="-54" cy="-58" r="3" fill="#3a3340"/>'
      + Z.auge(-70, -82, 6, s.kuh === 'da', -1, 1) + Z.auge(-46, -82, 6, s.kuh === 'da', -1, 1)
      + '</g></g>'
      + '<path class="l" fill="#d64b3c" d="M-44 -50l22 4l-2 8l-22 -4z"/><path class="l" fill="#ffd23f" d="M-42 -40h14l4 16h-22z"/>'
      + '</g></g>';
  }
  function kraehe(s) {
    if (!s.kraehe) return '';
    return '<g id="kraehe"><g transform="translate(268 204)"><path class="d n" d="M-6 22v10M6 22v10"/><ellipse class="l" rx="25" ry="22" fill="#3d3d4c"/>'
      + (s.kraehe === 'flug' ? '<path class="l" fill="#3d3d4c" d="M-8 -4q-30 -36 -46 -18q16 6 28 28z"/>' : '<path class="l" fill="#2b2b38" d="M-20 -2q8 18 24 8q-6 -14 -24 -8z"/>')
      + '<path class="l" fill="#f2a900" d="M18 2l20 12l-22 2z"/>' + Z.auge(8, -8, 7, false, 1.5, 3) + '<path class="l n" d="M0 -18l8 4"/></g></g>';
  }
  function kaese(x, y) {
    return '<g transform="translate(' + x + ' ' + y + ')"><path class="l" fill="#ffd23f" d="M-28 0l44 -26l14 26z"/><path class="l" fill="#f2b705" d="M-28 0h58v10h-58z"/><circle cx="2" cy="-8" r="4" fill="#d99a00"/><circle cx="16" cy="-4" r="3" fill="#d99a00"/><circle cx="-8" cy="5" r="2.5" fill="#d99a00"/></g>';
  }
  function murmel() {
    return '<g id="murmel"><g transform="translate(226 498)"><path class="l" fill="#8a6a4a" d="M22 -4q30 -4 26 -30q-14 0 -26 22z"/><ellipse class="l" cx="0" cy="-26" rx="26" ry="30" fill="#a57c52"/><ellipse cx="0" cy="-18" rx="14" ry="18" fill="#e9c8a0"/>'
      + '<circle class="d" cx="-14" cy="-78" r="6" fill="#8a6a4a"/><circle class="d" cx="14" cy="-78" r="6" fill="#8a6a4a"/><ellipse class="l" cx="0" cy="-62" rx="22" ry="19" fill="#a57c52"/>'
      + Z.auge(-8, -66, 5, false, 1, 1) + Z.auge(8, -66, 5, false, 1, 1) + '<ellipse cx="0" cy="-56" rx="5" ry="3.5" fill="#3a3340"/><path class="d" fill="#fff" d="M-4 -52h8v7h-8z"/>'
      + '<ellipse class="d" cx="-12" cy="0" rx="10" ry="5" fill="#8a6a4a"/><ellipse class="d" cx="12" cy="0" rx="10" ry="5" fill="#8a6a4a"/><path class="l n" style="stroke-width:5;stroke:#8a6a4a" d="M-22 -34q8 10 20 8M22 -34q-4 8 -8 8"/></g></g>';
  }
  WASNUN.szene({
    id: 'alp', titel: 'Auf der Alp',
    ziel: 'Abend auf der Alp: Kuh Berta soll von der Weide heim zur Hütte. Aber sie frisst und frisst …',
    start: function () { return { kraehe: 'sitzt', kaese: 'sims', murmel: 'horn', kuh: 'weide', tor: false, horcht: false }; },
    bild: function (s) {
      var h = '<rect width="800" height="600" fill="#bde4f7"/>' + Z.sonne(330, 78) + Z.wolke(730, 190, 0.6)
        // Yeti hinter dem Gipfel (Geheimnis)
        + '<g id="yeti"><g transform="translate(642 176)"><path class="l" fill="#fff" d="M-26 20q-8 -44 26 -46q34 2 26 46z"/><ellipse cx="0" cy="-2" rx="15" ry="12" fill="#bcd3e6"/>' + Z.auge(-6, -4, 4) + Z.auge(7, -4, 4) + '<path class="d n" d="M-5 5q5 4 10 0"/>'
        + '<g id="yetiarm" class="linksu"><path class="l" fill="#fff" d="M20 8q14 -8 16 -26q8 0 8 8q-2 20 -20 32z"/></g></g></g>'
        + '<path class="l" fill="#a9bccd" d="M290 400L470 130l80 100l90 -138l180 250v160z"/><path class="l" fill="#fff" d="M470 130l34 42l-22 14l-16 -14l-26 20zM640 92l40 56l-26 -8l-16 18l-18 -22l-14 6z"/>'
        + '<path class="l" fill="#8fd18a" d="M360 430q180 -170 450 -110v280h-450z"/>'
        + '<path class="l" fill="#6cc04a" d="M-5 470q200 -26 400 -12t410 -6v160h-810z"/>'
        + '<path class="d n" style="stroke:#4e9c38" d="M150 580l6 -12l6 12M660 584l6 -12l6 12M520 590l6 -12l6 12M300 570l6 -12l6 12"/>';
      // Hütte
      h += '<g id="rauch" opacity="0"><ellipse class="l n" style="stroke:#fff;stroke-width:6" cx="125" cy="170" rx="18" ry="9"/></g>'
        + '<rect class="l" x="108" y="182" width="34" height="60" fill="#a9a4ae"/><rect class="l" x="102" y="176" width="46" height="12" fill="#8d8793"/>'
        + '<rect class="l" x="60" y="296" width="270" height="190" fill="#b98352"/><path class="d n" style="stroke:#8a5a3a" d="M60 340h270M60 388h270M60 436h270"/>'
        + '<path class="l" fill="#c99562" d="M66 300L195 200L324 300z"/><circle class="l" cx="195" cy="262" r="15" fill="#2b3a4a"/>'
        + '<path class="l" fill="#6b4a34" d="M26 304L195 166L364 304l-18 16L195 198L44 320z"/>'
        + '<ellipse class="d" cx="118" cy="252" rx="13" ry="8" fill="#bdb8c2"/><ellipse class="d" cx="300" cy="268" rx="13" ry="8" fill="#bdb8c2"/>'
        + '<g id="tuer"><rect class="l" x="112" y="376" width="72" height="110" rx="4" fill="#7a5236"/><path class="l" fill="#3d2a20" d="M148 410c-6 -10 -20 -2 -11 8l11 10l11 -10c9 -10 -5 -18 -11 -8z"/><circle cx="174" cy="436" r="4" fill="#ffd23f"/></g>'
        + '<rect class="l" x="226" y="336" width="80" height="60" fill="#2b3a4a"/><path class="l n" style="stroke:#f6f1e6" d="M266 336v60M226 366h80"/>'
        + '<path class="l" fill="#d64b3c" d="M206 334h20v64h-20zM306 334h20v64h-20z"/><rect class="l" x="214" y="396" width="104" height="10" fill="#d9b48a"/>'
        + '<path class="l n" style="stroke-width:5" d="M60 306h36"/><g id="glocke" class="kopf"><path class="l n" d="M88 306v12"/><path class="l" fill="#ffd23f" d="M72 350q2 -32 16 -32t16 32z"/><circle class="d" cx="88" cy="354" r="5" fill="#b98a00"/><path class="l n" style="stroke:#8a5a3a" d="M88 358v26"/></g>';
      if (s.kaese === 'sims') h += '<g id="kaese">' + kaese(264, 396) + '</g>';
      if (s.kaese === 'boden') h += kaese(276, 500);
      h += kraehe(s);
      // Milchkanne
      h += '<g id="kanne" class="fuss"><path class="l" fill="#c9ced6" d="M30 566v-52q0 -14 8 -20v-12h28v12q8 6 8 20v52z"/><rect class="l" x="34" y="474" width="36" height="10" rx="3" fill="#a9a4ae"/><path class="l n" d="M30 520q-12 6 -6 22"/><path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".6" d="M42 506v44"/></g>';
      // Weide, Zaun mit Gatter, Kuh (hinter dem Zaun, ausser sie ist daheim)
      var zaun = '<path class="l" fill="#b98352" d="M420 420h12v60h-12zM470 418h12v60h-12zM668 410h12v60h-12zM722 406h12v60h-12zM776 402h12v60h-12z"/>'
        + '<path class="l" fill="#d9b48a" d="M416 434l106 -4v10l-106 4zM416 456l106 -4v10l-106 4zM616 428l190 -12v10l-190 12zM616 450l190 -12v10l-190 12z"/>'
        + '<path class="l" fill="#9a6b43" d="M514 404h14v80h-14zM610 400h14v80h-14z"/>';
      var tor = s.tor ? '<g id="tor"><path class="l" fill="#e6c79f" d="M528 420l34 26v46l-34 -22z"/><path class="l n" d="M528 420l34 72"/></g>'
        : '<g id="tor"><path class="l" fill="#e6c79f" d="M528 418h82v50h-82z"/><path class="l n" d="M528 418l82 50M528 468l82 -50"/><circle cx="602" cy="442" r="4" fill="#3a3340"/></g>';
      if (s.kuh !== 'da') h += kuh(s);
      h += zaun + tor;
      if (s.horcht || s.kuh === 'tor') h += '<path class="l n" style="stroke:#ff8a3c;stroke-width:4" d="' + (s.kuh === 'tor' ? 'M520 330l-10 -14M536 322l-2 -18M552 326l8 -14' : 'M610 250l-10 -14M626 242l-2 -18M642 246l8 -14') + '"/>';
      if (s.murmel === 'kaese') h += murmel();
      if (s.kuh === 'da') h += kuh(s) + '<g class="a-schweb"><path class="l" fill="#ff6f91" d="M392 360c-10 -16 -32 -4 -18 12l18 16l18 -16c14 -16 -8 -28 -18 -12z"/></g>';
      // Alphorn (mit Schwanz im Becher), Noten
      h += '<g id="noten" opacity="0"><path class="l" fill="#3a3340" d="M664 500a9 7 0 1 1 0 .1zM682 500v-34l16 -6v10l-10 4M700 456a9 7 0 1 1 0 .1zM718 456v-34"/></g>';
      if (s.murmel === 'horn') h += '<g id="schwanz" class="linksu"><path class="l" fill="#8a6a4a" d="M600 536q4 -44 34 -42q12 22 -16 46z"/><path class="d n" style="stroke:#6b4a34" d="M612 516q6 -8 12 -8M610 526q8 -6 14 -4"/></g>';
      h += '<g id="horn"><path class="l" fill="#dba25c" d="M318 470l8 -10l226 94q30 10 44 -22l30 12q-20 66 -90 40l-222 -104z"/><ellipse class="l" cx="611" cy="538" rx="17" ry="9" fill="#5b3a2e" transform="rotate(22 611 538)"/>'
        + '<path class="l n" style="stroke:#d64b3c;stroke-width:6" d="M398 502l-6 14M476 536l-6 14"/><path class="l" fill="#3a3340" d="M312 462l12 4l-4 10l-12 -6z"/>'
        + '<path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M560 590l10 -24M584 590l-12 -24"/></g>';
      // Edelweiss mit Biene
      h += '<g id="biene"><g transform="translate(758 500)"><ellipse class="d" cx="-4" cy="-8" rx="7" ry="5" fill="#fff" opacity=".8"/><ellipse class="d" rx="10" ry="7" fill="#ffd23f"/><path class="d n" d="M-2 -6v12M4 -6v12"/></g></g>'
        + Z.blume(716, 574, '#fff', 30) + Z.blume(748, 582, '#fff', 40) + Z.blume(690, 586, '#fff', 24);
      return h;
    },
    stellen: [
      { id: 'tor', r: [512, 380, 112, 96], tipp: async function (s, a) {
        if (s.tor) { a.ton('knarr'); return a.gag('Das Gatter steht schon weit offen.'); }
        a.ton('knarr'); a.mal({ tor: true });
        if (s.kuh === 'tor') {
          a.ton('kuhglocke'); await a.anim('#kuh', [{ transform: 'translate(0,0)' }, { transform: 'translate(-70px,40px)' }, { transform: 'translate(-148px,64px)' }], 1200);
          a.mal({ kuh: 'da' }); a.ton('muh');
          return a.fertig('Muuuh! Berta trottet durchs Gatter und ist daheim.');
        }
        return a.weiter('Das Gatter schwingt auf. Der Weg zur Hütte wäre frei.');
      } },
      { id: 'glocke', r: [36, 290, 100, 100], tipp: async function (s, a) {
        a.ton('glocke'); await a.anim('#glocke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(24deg)' }, { transform: 'rotate(-20deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(0deg)' }], 800);
        if (s.kraehe) {
          a.mal({ kraehe: 'flug' }); a.ton('kraechz');
          await a.anim('#kraehe', [{ transform: 'translate(0,0)' }, { transform: 'translate(160px,-120px)' }, { transform: 'translate(560px,-260px)' }], 1000, { easing: 'ease-in' });
          a.mal({ kraehe: '' });
          return a.weiter('Bim, bam! Die Krähe erschrickt und flattert davon.');
        }
        return a.gag(s.kuh === 'weide' ? 'Bim, bam. Berta kennt die Glocke – und frisst gemütlich weiter.' : 'Bim, bam.');
      } },
      { id: 'kaese', r: [214, 318, 104, 96], wenn: function (s) { return s.kaese === 'sims'; }, tipp: async function (s, a) {
        a.ton('plopp');
        await a.anim('#kaese', [{ transform: 'translate(0,0)' }, { transform: 'translate(12px,104px)' }], 450, { easing: 'ease-in' });
        a.ton('plumps');
        if (s.kraehe) {
          a.mal({ kraehe: 'flug', kaese: 'boden' }); a.ton('kraechz');
          await a.anim('#kraehe', [{ transform: 'translate(0,0)' }, { transform: 'translate(8px,270px)' }], 450, { easing: 'ease-in' });
          a.mal({ kaese: 'weg' });
          await a.anim('#kraehe', [{ transform: 'translate(8px,270px)' }, { transform: 'translate(560px,-240px)' }], 800, { easing: 'ease-in' });
          a.mal({ kraehe: '' });
          return a.sackgasse('Schwupp – die Krähe schnappt sich den Käse! Sie hat nur darauf gewartet.');
        }
        a.mal({ kaese: 'boden' }); await a.warte(300);
        a.ton('fiep'); await a.anim('#schwanz', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-20deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(-14deg)' }, { transform: 'rotate(0deg)' }], 700);
        a.mal({ murmel: 'kaese' }); a.ton('fiep');
        await a.anim('#murmel', [{ transform: 'translate(380px,20px)' }, { transform: 'translate(250px,-30px)' }, { transform: 'translate(120px,10px)' }, { transform: 'translate(0,0)' }], 800);
        return a.weiter('Mmh, Käse! Ein Murmeltier flitzt aus dem Alphorn und holt ihn sich.');
      } },
      { id: 'murmel', r: [176, 420, 104, 96], wenn: function (s) { return s.murmel === 'kaese'; }, tipp: async function (s, a) {
        a.ton('fiep'); await a.anim('#murmel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-14px)' }, { transform: 'translateY(0)' }], 350);
        return a.gag('Das Murmeltier mampft und pfeift zufrieden.');
      } },
      { id: 'horn', r: [320, 462, 320, 120], tipp: async function (s, a) {
        if (s.murmel === 'horn') {
          a.ton('puff'); a.anim('#horn', [{ transform: 'translateY(0)' }, { transform: 'translateY(-5px)' }, { transform: 'translateY(0)' }], 300);
          await a.anim('#schwanz', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-22deg)' }, { transform: 'rotate(16deg)' }, { transform: 'rotate(0deg)' }], 700);
          return a.gag(a.nr > 1 ? 'Wieder nur «Pfffft». Was schaut denn da vorne aus dem Alphorn heraus?' : 'Pfffft – kein Ton! Das Alphorn ist verstopft. Schau genau hin.');
        }
        a.ton('horn'); a.anim('#horn', [{ transform: 'translateY(0)' }, { transform: 'translateY(-6px)' }, { transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' }], 1400);
        await a.anim('#noten', [{ opacity: 0, transform: 'translate(0,0)' }, { opacity: 1, transform: 'translate(20px,-40px)' }, { opacity: 0, transform: 'translate(50px,-110px)' }], 1500);
        if (s.kuh !== 'weide') return a.gag(s.kuh === 'tor' ? 'Tuuut! Berta ist schon da – aber das Gatter ist zu.' : 'Tuuut!');
        a.mal({ horcht: true }); a.ton('muh'); await a.warte(500);
        if (s.tor) {
          a.ton('kuhglocke'); await a.anim('#kuh', [{ transform: 'translate(0,0)' }, { transform: 'translate(-94px,106px)' }, { transform: 'translate(-242px,170px)' }], 1800);
          a.mal({ kuh: 'da', horcht: false }); a.ton('muh');
          return a.fertig('Tuuut! Berta hört das Alphorn, trabt durchs offene Gatter und ist daheim.');
        }
        a.ton('kuhglocke'); await a.anim('#kuh', [{ transform: 'translate(0,0)' }, { transform: 'translate(-94px,106px)' }], 1100);
        a.mal({ kuh: 'tor', horcht: false });
        return a.weiter('Tuuut! Berta spitzt die Ohren und trabt los – bis zum Gatter. Das ist zu.');
      } },
      { id: 'kuh', r: function (s) { return s.kuh === 'tor' ? [540, 300, 150, 100] : [612, 222, 160, 112]; }, wenn: function (s) { return s.kuh !== 'da'; }, tipp: async function (s, a) {
        a.ton('muh'); await a.anim('#kuhkopf', [{ transform: 'translateY(0)' }, { transform: 'translateY(-10px)' }, { transform: 'translateY(0)' }], 600);
        if (s.kuh === 'tor') return a.gag('Berta schaut dich mit grossen Augen an. Sie will hinein.');
        return a.gag(a.nr % 2 ? 'Muh. Berta frisst weiter. Rufen und Winken beeindruckt sie nicht.' : 'Berta hört nur auf eines: den Klang vom Alphorn.');
      } },
      { id: 'kraehe', r: [220, 150, 100, 96], wenn: function (s) { return !!s.kraehe; }, tipp: async function (s, a) {
        a.ton('kraechz'); await a.anim('#kraehe', [{ transform: 'translateY(0)' }, { transform: 'translateY(-10px)' }, { transform: 'translateY(0)' }], 300);
        return a.gag(a.nr % 2 ? 'Kraah! Die Krähe bleibt sitzen. Sie lässt den Käse nicht aus den Augen.' : 'Die Krähe hüpft nur. Antippen erschreckt sie nicht – da braucht es etwas Lauteres.');
      } },
      { id: 'gipfel', r: [584, 50, 120, 110], tipp: async function (s, a) {
        a.ton('jodel'); await a.anim('#yeti', [{ transform: 'translateY(0)' }, { transform: 'translateY(-104px)' }], 500);
        await a.anim('#yetiarm', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-24deg)' }, { transform: 'rotate(8deg)' }, { transform: 'rotate(-24deg)' }, { transform: 'rotate(0deg)' }], 800);
        await a.anim('#yeti', [{ transform: 'translateY(-104px)' }, { transform: 'translateY(0)' }], 400);
        return a.geheim('Hinter dem Gipfel wohnt ein Yeti. Er winkt und jodelt zurück.');
      } },
      { id: 'tuer', r: [100, 384, 96, 100], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#tuer', [{ transform: 'translateX(0)' }, { transform: 'translateX(3px)' }, { transform: 'translateX(-3px)' }, { transform: 'translateX(0)' }], 300);
        return a.gag('Klopf, klopf. Keine Antwort – der Senn hält sein Nickerchen.');
      } },
      { id: 'kamin', r: [76, 140, 100, 100], tipp: async function (s, a) {
        a.ton('puff'); await a.anim('#rauch', [{ opacity: 0, transform: 'translateY(0) scale(.6)' }, { opacity: 1, transform: 'translateY(-40px) scale(1)' }, { opacity: 0, transform: 'translateY(-100px) scale(1.6)' }], 1200, { easing: 'ease-out' });
        return a.gag('Aus dem Kamin steigt ein hübscher Rauchring.');
      } },
      { id: 'kanne', r: [4, 470, 96, 110], tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#kanne', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(8deg)' }, { transform: 'rotate(-6deg)' }, { transform: 'rotate(0deg)' }], 500);
        return a.gag('Die Milchkanne scheppert. Leer – Berta ist ja noch nicht daheim.');
      } },
      { id: 'edelweiss', r: [670, 490, 124, 104], tipp: async function (s, a) {
        a.ton('schnurr'); await a.anim('#biene', [{ transform: 'translate(0,0)' }, { transform: 'translate(-40px,-30px)' }, { transform: 'translate(-70px,10px)' }, { transform: 'translate(-30px,-16px)' }, { transform: 'translate(0,0)' }], 1200);
        return a.gag('Edelweiss! Nur anschauen, nicht pflücken – sagt die Biene.');
      } },
      { id: 'sonne', r: [266, 14, 130, 128], tipp: async function (s, a) {
        a.ton('plopp');
        return a.gag('Die Sonne steht schon tief. Zeit, dass Berta heimkommt.');
      } }
    ],
    naechster: function (s) { return s.kraehe ? 'glocke' : s.kaese === 'sims' ? 'kaese' : s.kuh === 'weide' ? 'horn' : 'tor'; }
  });
})();
