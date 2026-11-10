/* Bild 1 «Im Garten» (leicht): Kettenreaktion + genau hinschauen (Knoten im Schlauch) + eine Sackgasse (Eimer).
   Lösung: Knoten lösen · Eimer wegkippen (beides in beliebiger Reihenfolge) · Wasserhahn · Igel. */
(function () {
  var Z = WASNUN.Z;
  var HX = 690, HY = 500;            // Igel
  function igel(s) {
    var satt = s.apfel === 'igel';
    return '<g id="igel"><g transform="translate(' + HX + ' ' + HY + ')">'
      + '<ellipse cx="-4" cy="2" rx="62" ry="8" fill="#2f7d38" opacity=".35"/>'
      + '<path class="l" fill="#7a5236" d="M-46 0l-10 -20l14 4l-4 -24l16 12l2 -26l14 16l8 -24l10 20l12 -18l4 20l14 -10l-2 18l12 -2l-6 16l8 6l-10 12z"/>'
      + '<path class="l" fill="#e9c8a0" d="M-40 0q-40 0 -56 -16q24 -24 58 -20q10 14 -2 36z"/>'
      + '<circle cx="-96" cy="-16" r="6" fill="#2b2530"/>'
      + (satt ? '<path class="l n" d="M-72 -24q6 -7 12 0"/><path class="d n" d="M-84 -6q10 8 22 2"/>' : Z.auge(-66, -24, 6, false, -1.5, -1.5))
      + '<ellipse class="d" cx="-30" cy="1" rx="10" ry="5" fill="#e9c8a0"/><ellipse class="d" cx="18" cy="1" rx="10" ry="5" fill="#e9c8a0"/>'
      + (satt ? apfel(6, -50) : '')
      + '</g></g>';
  }
  function apfel(x, y) {
    return '<g transform="translate(' + x + ' ' + y + ')"><g id="apfelr" class="dreh"><circle class="l" r="24" fill="#e23b2e"/><path d="M-12 -8a14 14 0 0 1 10 -8" class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".7"/>'
      + '<path class="l n" style="stroke-width:4" d="M0 -22q2 -8 6 -12"/><path class="d" fill="#57b04f" d="M5 -30q14 -8 20 2q-12 8 -20 -2z"/></g></g>';
  }
  function eimer(s) {
    var steht = s.eimer === 'steht';
    var e = '<path class="l n" style="stroke-width:4" d="M-30 -58q30 -34 60 0"/><path class="l" fill="#6d9fe0" d="M-34 -60h68l-9 60h-50z"/><path class="d n" style="stroke:#fff" opacity=".6" d="M-22 -48l5 38"/><ellipse class="l" cx="0" cy="-60" rx="34" ry="9" fill="#3f6fb3"/>';
    return '<g id="eimer">' + (steht ? '<g transform="translate(400 496)">' + e + (s.apfel === 'eimer' ? '<g transform="translate(0 -66) scale(.8)">' + apfel(0, 0) + '</g><ellipse class="l" cx="0" cy="-60" rx="34" ry="9" fill="none"/>' : '') + '</g>'
      : '<g transform="translate(280 500) rotate(-96)">' + e + '</g>') + '</g>';
  }
  WASNUN.szene({
    id: 'garten', titel: 'Im Garten',
    ziel: 'Der Igel hat Hunger auf den Apfel. Wie kommt der Apfel zu ihm?',
    start: function () { return { knoten: true, eimer: 'steht', wasser: false, vogel: 'sitzt', apfel: 'baum', brille: false }; },
    bild: function (s) {
      var h = '<rect width="800" height="600" fill="#a8dcf5"/>'
        + '<path fill="#93d48c" d="M0 372q190 -80 410 -6t390 -34v268h-800z"/>'
        + Z.sonne(86, 86, s.brille) + '<g id="wolke">' + Z.wolke(330, 92, 1.1) + '<g id="tropfen" opacity="0"><path fill="#4aa3e8" d="M300 130q7 12 0 16q-7 -4 0 -16zM334 136q7 12 0 16q-7 -4 0 -16zM366 130q7 12 0 16q-7 -4 0 -16z"/></g></g>'
        + Z.wolke(650, 60, 0.7)
        + '<path class="l" fill="#6cc04a" d="M-5 440q200 -22 400 -6t410 -10v190h-810z"/>'
        + '<path class="d n" style="stroke:#4e9c38" d="M150 560l6 -12l6 12M430 570l6 -12l6 12M610 566l6 -12l6 12M740 548l6 -12l6 12M330 552l6 -12l6 12"/>';
      // Zwerg hinter dem Busch (Geheimnis), dann der Busch davor
      h += '<g id="zwerg"><g transform="translate(250 396)"><path class="l" fill="#fff" d="M-16 -8q16 28 32 0z"/><circle class="l" cy="-16" r="16" fill="#f3c9a5"/><path class="l" fill="#e23b2e" d="M-18 -22q18 -10 36 0l-16 -40z"/>'
        + Z.auge(-6, -16, 4) + Z.auge(7, -16, 4) + '<circle cx="0" cy="-9" r="4" fill="#e79a8a"/></g></g>'
        + Z.busch(250, 432, 1.1);
      // Baum: Stamm, Ast nach links, Krone
      h += '<g id="blaetter" opacity="0"><path class="d" fill="#57b04f" d="M560 250q12 -10 20 0q-10 10 -20 0zM650 270q12 -10 20 0q-10 10 -20 0zM700 240q12 -10 20 0q-10 10 -20 0z"/></g>'
        + '<path class="l" fill="#9a6b43" d="M566 486q16 -90 8 -200h54q-8 110 12 200z"/><path class="d n" d="M590 440q6 -30 2 -60M610 400q4 -20 0 -40"/>'
        + '<g id="ast" class="rechtsu"><path class="l" fill="#9a6b43" d="M580 318q-90 -44 -206 -40q-6 8 0 16q110 -2 196 50z"/></g>'
        + '<g id="krone"><path class="l" fill="#4caf50" d="M500 268a72 72 0 0 1 14 -128a92 92 0 0 1 166 -34a78 78 0 0 1 96 104a62 62 0 0 1 -44 86q-120 34 -232 -28z"/>'
        + '<path class="d n" style="stroke:#3a8f3f" d="M560 150q10 -10 20 0M640 120q10 -10 20 0M700 200q10 -10 20 0M590 230q10 -10 20 0M670 262q10 -10 20 0"/>'
        + '<circle class="d" cx="720" cy="150" r="13" fill="#e23b2e"/><circle class="d" cx="560" cy="205" r="12" fill="#e23b2e"/></g>';
      // Schlauch vom Hahn zum Sprenger
      var sch = s.knoten ? 'M88 352C84 430 96 492 150 506c22 6 38 -2 46 -16c12 -24 46 -20 40 6c-6 22 -44 14 -30 -12c10 -18 40 -4 60 6c60 28 150 14 236 14'
        : 'M88 352C84 430 96 492 150 506c60 14 100 -6 150 4c70 14 130 2 202 4';
      h += '<path class="n" stroke="#3a3340" stroke-width="15" stroke-linecap="round" d="' + sch + '"/><path class="n" stroke="#35b56a" stroke-width="9" stroke-linecap="round" d="' + sch + '"/>'
        + '<g id="beule" class="dreh" style="transform:scale(0)"><ellipse class="l" cx="140" cy="500" rx="26" ry="20" fill="#35b56a"/></g>';
      // Pfosten mit Wasserhahn
      h += '<rect class="l" x="66" y="300" width="30" height="180" rx="4" fill="#b98958"/><path class="l" fill="#c9ced6" d="M70 330h34q14 0 14 14v12h-14v-10h-34z"/>'
        + '<g id="griff" class="dreh"><path class="l" style="stroke:#d64b3c;stroke-width:8" d="M66 318h40"/><circle class="l" cx="86" cy="318" r="7" fill="#d64b3c"/></g>';
      // Maulwurf hinter seinem Hügel
      h += '<g id="maulwurf"><g transform="translate(74 566)"><ellipse class="l" cx="0" cy="-8" rx="22" ry="24" fill="#4a4048"/><ellipse class="d" cx="0" cy="-2" rx="9" ry="7" fill="#f2a3a0"/>'
        + '<path class="l n" style="stroke-width:4" d="M-12 -16h6M6 -16h6"/></g></g>'
        + '<path class="l" fill="#9a6b43" d="M18 590q8 -48 56 -50q46 2 56 50z"/><path class="d n" d="M50 560q6 -6 12 0M84 566q6 -6 12 0"/>';
      // Eimer, Sprenger, Wasserstrahl
      h += eimer(s)
        + '<path class="l" fill="#f2a900" d="M488 514h44l-8 -14h-28z"/><rect class="l" x="503" y="476" width="14" height="26" rx="3" fill="#c9ced6"/><circle class="l" cx="510" cy="474" r="9" fill="#d64b3c"/>';
      if (s.wasser) h += '<g id="strahl" class="a-flack rechtsu"><path class="n" stroke="#4aa3e8" stroke-width="7" stroke-linecap="round" stroke-dasharray="4 16" d="M506 466q-10 -130 -44 -196M512 466q-2 -150 -64 -214M500 468q-30 -110 -70 -170"/><path class="n" stroke="#bfe6ff" stroke-width="5" stroke-linecap="round" stroke-dasharray="3 22" d="M509 466q-6 -140 -54 -206"/></g>';
      // Apfel am Ast, Vogel
      if (s.apfel === 'baum') h += '<g id="apfel">' + apfel(396, 326) + '</g>';
      if (s.apfel === 'boden') h += '<g id="apfel">' + apfel(606, 506) + '</g>';
      if (s.vogel !== 'weg') h += '<g id="vogel"><g transform="translate(452 250)">' + Z.vogel({ f: '#f08a3c', zu: s.vogel === 'sitzt', flug: s.vogel === 'auf', spiegel: true }) + '</g></g>'
        + (s.vogel === 'sitzt' ? Z.zzz(420, 206, 0.8) : '');
      h += igel(s);
      if (s.apfel === 'igel') h += '<g class="a-schweb"><path class="l" fill="#ff6f91" d="M640 400c-10 -16 -32 -4 -18 12l18 16l18 -16c14 -16 -8 -28 -18 -12z"/></g>';
      return h;
    },
    stellen: [
      { id: 'hahn', r: [20, 270, 120, 130], tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#griff', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(180deg)' }], 400);
        if (s.knoten) {
          a.ton('boing'); await a.anim('#beule', [{ transform: 'scale(0)' }, { transform: 'scale(1.5)' }, { transform: 'scale(1.2)' }, { transform: 'scale(1.6)' }, { transform: 'scale(0)' }], 1400);
          return a.gag(a.nr > 1 ? 'Wieder nur eine dicke Beule. Das Wasser bleibt im Schlauch stecken.' : 'Der Schlauch bläht sich auf – aber vorne kommt nichts. Schau ihn dir genau an!');
        }
        if (s.apfel !== 'baum') return a.gag('Der Hahn tropft noch ein wenig. Genug gegossen.');
        a.mal({ wasser: true, vogel: 'wach' }); a.ton('wasser'); await a.warte(700);
        a.mal({ vogel: 'auf' }); a.ton('pieps'); a.ton('flatter');
        await a.anim('#vogel', [{ transform: 'translate(0,0)' }, { transform: 'translate(-90px,-120px)' }, { transform: 'translate(-320px,-330px)' }], 900, { easing: 'ease-in' });
        a.mal({ vogel: 'weg', wasser: false });
        await a.anim('#ast', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(7deg)' }, { transform: 'rotate(-3deg)' }, { transform: 'rotate(0deg)' }], 450);
        if (s.eimer === 'steht') {
          await a.anim('#apfel', [{ transform: 'translateY(0)' }, { transform: 'translateY(106px)' }], 420, { easing: 'ease-in' });
          a.ton('plumps'); a.mal({ apfel: 'eimer' });
          await a.anim('#eimer', [{ transform: 'translateY(0)' }, { transform: 'translateY(5px)' }, { transform: 'translateY(0)' }], 220);
          return a.sackgasse('Plumps – genau in den Eimer! Da kommt der Igel nicht heran.');
        }
        await a.anim('#apfel', [{ transform: 'translateY(0)' }, { transform: 'translateY(180px)' }], 520, { easing: 'ease-in' });
        a.ton('plumps');
        a.anim('#apfelr', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(540deg)' }], 1000, { easing: 'ease-out' });
        await a.anim('#apfel', [{ transform: 'translate(0,180px)' }, { transform: 'translate(70px,160px)' }, { transform: 'translate(140px,180px)' }, { transform: 'translate(210px,180px)' }], 1000, { easing: 'ease-out' });
        a.mal({ apfel: 'boden' });
        return a.weiter('Der Vogel flattert davon, der Ast schnellt hoch – und der Apfel rollt ins Gras.');
      } },
      { id: 'knoten', r: [150, 448, 110, 100], wenn: function (s) { return s.knoten; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ knoten: false });
        return a.weiter('Knoten gelöst. Jetzt kann das Wasser durch den Schlauch.');
      } },
      { id: 'eimer', r: [345, 400, 110, 110], wenn: function (s) { return s.eimer === 'steht'; }, tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#eimer', [{ transform: 'translate(0,0)' }, { transform: 'translate(-40px,-30px)' }, { transform: 'translate(-90px,0)' }], 450);
        a.mal({ eimer: 'liegt' });
        return a.weiter('Der Eimer kippt zur Seite. Unter dem Apfel ist jetzt freie Bahn.');
      } },
      { id: 'eimer2', r: [225, 440, 110, 95], wenn: function (s) { return s.eimer === 'liegt' && !s.knoten; }, tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#eimer', [{ transform: 'translateX(0)' }, { transform: 'translateX(-8px)' }, { transform: 'translateX(6px)' }, { transform: 'translateX(0)' }], 400);
        return a.gag('Klong! Der Eimer liegt gut, wo er liegt.');
      } },
      { id: 'igel', r: [600, 425, 180, 110], tipp: async function (s, a) {
        if (s.apfel === 'boden') {
          await a.anim('#igel', [{ transform: 'translateX(0)' }, { transform: 'translateX(-40px)' }], 500);
          a.ton('plopp'); a.mal({ apfel: 'igel' });
          await a.anim('#igel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-16px)' }, { transform: 'translateY(0)' }, { transform: 'translateY(-10px)' }, { transform: 'translateY(0)' }], 700);
          return a.fertig('Aufgespiesst! Der Igel trägt seinen Apfel stolz nach Hause.');
        }
        a.ton('knarr'); await a.anim('#igel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-6px)' }, { transform: 'translateY(0)' }], 300);
        return a.gag(a.nr % 2 ? 'Dem Igel knurrt der Magen. Er schielt hinauf zum Apfel.' : 'Klettern kann der Igel nicht. Der Apfel muss zu ihm herunter.');
      } },
      { id: 'vogel', r: [405, 185, 95, 100], wenn: function (s) { return s.vogel === 'sitzt'; }, tipp: async function (s, a) {
        a.mal({ vogel: 'wach' }); a.ton('pieps'); await a.warte(900);
        return a.gag(a.nr % 2 ? 'Der dicke Vogel blinzelt kurz – und schläft weiter. Antippen stört ihn nicht.' : 'Piep. Der bleibt sitzen. Vielleicht mag er kein Wasser?');
      } },
      { id: 'apfel', r: [345, 285, 100, 95], wenn: function (s) { return s.apfel === 'baum'; }, tipp: async function (s, a) {
        a.ton('boing'); await a.anim('#apfel', [{ transform: 'translateX(0)' }, { transform: 'translateX(-9px)' }, { transform: 'translateX(8px)' }, { transform: 'translateX(-4px)' }, { transform: 'translateX(0)' }], 600);
        return a.gag('Der Apfel wackelt, hängt aber fest. Der Vogel drückt den Ast schön nach unten.');
      } },
      { id: 'sprenger', r: [462, 440, 96, 95], tipp: async function (s, a) {
        a.ton('klick');
        return a.gag(s.knoten ? 'Der Rasensprenger ist trocken. Es kommt kein Wasser an.' : 'Der Rasensprenger zielt genau nach oben. Fehlt nur noch Wasser.');
      } },
      { id: 'busch', r: [185, 345, 130, 100], tipp: async function (s, a) {
        a.ton('huch'); await a.anim('#zwerg', [{ transform: 'translateY(0)' }, { transform: 'translateY(-52px)' }, { transform: 'translateY(-52px)' }, { transform: 'translateY(-46px)' }, { transform: 'translateY(-52px)' }], 900);
        return a.geheim('Im Busch wohnt ein Gartenzwerg. Er winkt und taucht wieder ab.');
      } },
      { id: 'maulwurf', r: [14, 495, 120, 100], tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#maulwurf', [{ transform: 'translateY(0)' }, { transform: 'translateY(-44px)' }, { transform: 'translateY(-44px)' }, { transform: 'translateY(0)' }], 1100);
        return a.gag(a.nr % 2 ? 'Der Maulwurf schaut nach, wer da klopft. Sehen kann er dich nicht.' : 'Der Maulwurf schnuppert und verschwindet wieder.');
      } },
      { id: 'sonne', r: [20, 20, 132, 132], tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ brille: !s.brille });
        return a.gag(s.brille ? 'Die Sonne setzt ihre Sonnenbrille auf. Cool.' : 'Brille ab. Auch gut.', true);
      } },
      { id: 'wolke', r: [262, 40, 140, 105], tipp: async function (s, a) {
        a.ton('tropf'); await a.anim('#tropfen', [{ opacity: 0, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(20px)' }, { opacity: 0, transform: 'translateY(90px)' }], 800);
        return a.gag('Die Wolke drückt drei Tropfen heraus. Mehr hat sie nicht.');
      } },
      { id: 'krone', r: [520, 60, 250, 210], tipp: async function (s, a) {
        a.ton('flatter'); await a.anim('#blaetter', [{ opacity: 0, transform: 'translate(0,0)' }, { opacity: 1, transform: 'translate(-10px,60px)' }, { opacity: 1, transform: 'translate(12px,150px)' }, { opacity: 0, transform: 'translate(0,230px)' }], 1300);
        return a.gag('Es raschelt, drei Blätter segeln herunter. Der Apfel bleibt hängen.');
      } }
    ],
    naechster: function (s) { return s.knoten ? 'knoten' : s.eimer === 'steht' ? 'eimer' : s.apfel === 'baum' ? 'hahn' : 'igel'; }
  });
})();
