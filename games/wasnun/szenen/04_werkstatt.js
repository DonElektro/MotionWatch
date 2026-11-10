/* Bild 4 «In der Werkstatt»: ein Ding mitnehmen (Schlüssel, dann Batterie) + richtiger Moment (schwingender Magnet) +
   eine Sackgasse (Farbkübel). Lösung: Magnet antippen, wenn er rechts beim Schlüssel ist · Schublade aufschliessen ·
   Batterie nehmen · Batterie in den Roboter · Farbkübel herunternehmen (geht auch früher) · Starthebel. */
(function () {
  var Z = WASNUN.Z;
  // Pendel: 5 Sekunden hin und her, Ausschlag in Grad (+ = rechts beim Schlüssel, - = links bei der Dose)
  function aus(t) { return 40 * Math.sin(t * 2 * Math.PI / 5); }
  var SCHLUESSEL = '<circle class="l" cx="0" cy="0" r="9" fill="none" style="stroke:#b98a00;stroke-width:6"/><path class="l n" style="stroke:#b98a00;stroke-width:6" d="M0 9v30M0 26h10M0 36h8"/>'
    + '<circle class="n" cx="0" cy="0" r="9" stroke="#ffd23f" stroke-width="3"/><path class="n" stroke="#ffd23f" stroke-width="3" stroke-linecap="round" d="M0 9v30M0 26h10M0 36h8"/>';
  function batterie(x, y, k) {
    return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><rect class="l" x="-9" y="-36" width="18" height="8" fill="#c9ced6"/><rect class="l" x="-20" y="-30" width="40" height="60" rx="6" fill="#3fbf6b"/><rect x="-20" y="-30" width="40" height="16" rx="6" fill="#e9a23b"/><rect class="l n" x="-20" y="-30" width="40" height="60" rx="6"/>'
      + '<path class="l n" style="stroke:#fff;stroke-width:5" d="M-8 8h16M0 0v16"/></g>';
  }
  function kuebel(kipp) {
    return '<path class="l n" style="stroke-width:4" d="M-26 -48q26 -30 52 0"/><path class="l" fill="#d9dde3" d="M-30 -50h60l-6 50h-48z"/><ellipse class="l" cx="0" cy="-50" rx="30" ry="8" fill="#3b8cff"/>'
      + '<path class="l" fill="#3b8cff" d="M-30 -50q2 22 10 22q6 0 6 -12q2 -8 8 0q0 20 8 20q6 -2 6 -22l22 -8z"/>' + (kipp ? '' : '');
  }
  function robo(s) {
    var an = s.an, nass = s.eimer === 'kopf';
    var h = '<g id="robo"><path class="l n" style="stroke:#3a3340;stroke-width:5" d="M532 396q-4 108 76 108"/>'
      + '<path class="l" fill="#8d8793" d="M618 448h22v44h-22zM664 448h22v44h-22z"/><path class="l" fill="#5b6470" d="M606 490h40v16h-40zM658 490h40v16h-40z"/>'
      + '<g id="armL" class="kopf"><path class="l" fill="#8d8793" d="M578 356h16v64h-16z"/><circle class="l" cx="586" cy="426" r="11" fill="#5b6470"/></g>'
      + '<g id="armR" class="fuss"><path class="l" fill="#8d8793" d="M708 300h16v66h-16z"/><path class="l" fill="#5b6470" d="M700 286h32v16h-32z"/></g>'
      + '<rect class="l" x="592" y="340" width="120" height="112" rx="14" fill="#5fb3a8"/><circle class="d" cx="606" cy="354" r="4" fill="#3d857c"/><circle class="d" cx="698" cy="354" r="4" fill="#3d857c"/><circle class="d" cx="606" cy="438" r="4" fill="#3d857c"/><circle class="d" cx="698" cy="438" r="4" fill="#3d857c"/>'
      + '<rect class="l" x="626" y="362" width="52" height="72" rx="6" fill="#2b3a4a"/>'
      + (s.batterie === 'robo' ? batterie(652, 400, 0.95) : '<path class="d n" style="stroke:#5f7186;stroke-dasharray:5 6" d="M636 372h32v52h-32z"/>')
      + '<rect class="l" x="640" y="330" width="24" height="12" fill="#8d8793"/>'
      + '<g id="rkopf"><path class="l n" d="M652 262v-22"/><circle class="l" cx="652" cy="236" r="8" fill="' + (an && !nass ? '#ff5a5f' : '#8d8793') + '"/>'
      + '<rect class="l" x="604" y="262" width="96" height="70" rx="14" fill="#7fd0c4"/>';
    if (nass) h += '<path class="l n" style="stroke-width:4" d="M620 282l16 16M636 282l-16 16M668 282l16 16M684 282l-16 16"/><path class="l n" d="M632 316q6 -8 12 0t12 0t12 0"/>';
    else if (an) h += '<circle class="l" cx="630" cy="290" r="13" fill="#ffd23f"/><circle class="l" cx="674" cy="290" r="13" fill="#ffd23f"/><circle cx="630" cy="290" r="5" fill="#3a3340"/><circle cx="674" cy="290" r="5" fill="#3a3340"/><path class="l" fill="#fff" d="M634 310h36q-4 14 -18 14t-18 -14z"/>';
    else h += '<circle class="l" cx="630" cy="290" r="13" fill="#4a5a6a"/><circle class="l" cx="674" cy="290" r="13" fill="#4a5a6a"/><path class="l n" d="M622 292h16M666 292h16"/><path class="l n" d="M638 316h28"/>';
    h += '</g>';
    if (nass) h += '<path class="l" fill="#3b8cff" d="M596 268q4 -18 56 -18t56 18q6 40 -8 44q-8 -2 -8 -22q-4 -10 -10 0q2 60 -10 60q-10 -2 -8 -50q-4 -10 -12 0q2 26 -8 28q-10 -2 -8 -34q-6 -8 -12 0q0 40 -12 42q-14 -4 -16 -68z"/>'
      + Z.funken(600, 330, '#ffd23f') + Z.funken(716, 392, '#ffd23f');
    return h + '</g>';
  }
  WASNUN.szene({
    id: 'werkstatt', titel: 'In der Werkstatt',
    ziel: 'Der alte Roboter Rosto steht still. Bring ihn wieder zum Laufen!',
    start: function () { return { schluessel: 'haken', lade: false, batterie: 'lade', eimer: 'oben', an: false, dose: false }; },
    tasche: function (s) {
      if (s.schluessel === 'tasche') return { name: 'Schlüssel', svg: '<g transform="translate(30 10) scale(1.05)">' + SCHLUESSEL + '</g>' };
      if (s.batterie === 'tasche') return { name: 'Batterie', svg: batterie(30, 33, 0.8) };
      return null;
    },
    bild: function (s) {
      var h = '<rect width="800" height="600" fill="#ecdcbb"/><path class="d n" style="stroke:#dcc9a2" d="M0 160h800M0 320h800"/>'
        + '<rect class="l" x="-5" y="486" width="810" height="120" fill="#b98352"/><path class="d n" style="stroke:#8a5a3a" d="M0 524h800M0 562h800M120 486v38M420 486v38M700 486v38M260 524v38M560 524v38M90 562v38M380 562v38M660 562v38"/>';
      // Fenster mit Vogel
      h += '<rect class="l" x="40" y="96" width="116" height="104" fill="#a8dcf5"/><g id="fvogel"><g transform="translate(120 196) scale(.8)">' + Z.vogel({ f: '#e8574a', spiegel: true }) + '</g></g>'
        + '<path class="l n" style="stroke:#f6f1e6;stroke-width:8" d="M40 96h116v104h-116zM98 96v104"/><rect class="l" x="30" y="200" width="136" height="12" fill="#d9b48a"/>';
      // Lampe
      h += '<g id="lampe" class="kopf"><path class="l n" d="M660 0v52"/><path class="l" fill="#5f7186" d="M620 96q4 -44 40 -44t40 44z"/><ellipse class="l" cx="660" cy="98" rx="18" ry="9" fill="#fff3b0"/></g>';
      // Schiene, Regal mit Dose, Haken mit Schlüssel, Pendel
      h += '<rect class="l" x="240" y="30" width="320" height="14" rx="4" fill="#8d8793"/><path class="l" fill="#8d8793" d="M250 0h12v30h-12zM538 0h12v30h-12z"/><rect class="l" x="384" y="38" width="32" height="18" rx="4" fill="#5b6470"/>'
        + '<rect class="l" x="246" y="238" width="92" height="10" fill="#c99562"/><path class="l n" d="M258 248v16l14 -16M326 248v16l-14 -16"/>';
      if (!s.dose) h += '<g id="dose"><rect class="l" x="274" y="206" width="34" height="32" rx="3" fill="#c9ced6"/><rect x="275" y="214" width="32" height="14" fill="#d64b3c"/><ellipse class="l" cx="291" cy="206" rx="17" ry="5" fill="#e3e6ea"/></g>';
      h += '<path class="l n" style="stroke-width:5" d="M512 176v10q0 8 -8 8"/><circle class="l" cx="512" cy="174" r="5" fill="#5b6470"/>';
      if (s.schluessel === 'haken') h += '<g id="schluessel"><g transform="translate(503 203)">' + SCHLUESSEL + '</g></g>';
      h += '<g id="pendel" style="transform-origin:400px 48px"><path class="l n" style="stroke:#6d5a48" d="M400 50v150"/><g transform="translate(400 212)"><path class="l" fill="#d64b3c" d="M-18 -14h36v20q0 8 -8 8h-4v-14h-12v14h-4q-8 0 -8 -8z"/><path class="l" fill="#c9ced6" d="M-18 6h12v10h-12zM6 6h12v10h-12z"/>'
        + (s.dose ? '<rect class="l" x="-17" y="16" width="34" height="30" rx="3" fill="#c9ced6"/><rect x="-16" y="24" width="32" height="13" fill="#d64b3c"/>' : '') + '</g></g>';
      // Werkzeugwand
      h += '<rect class="l" x="352" y="290" width="126" height="110" rx="6" fill="#d9b48a"/><g id="hammer" class="dreh"><path class="l n" style="stroke:#8a5a3a;stroke-width:8" d="M384 312v70"/><path class="l" fill="#5b6470" d="M366 304h40v18h-40z"/></g>'
        + '<path class="l" fill="#c9ced6" d="M424 306a12 12 0 0 1 20 10l-8 4v62h-10v-62l-8 -4a12 12 0 0 1 6 -10v8h4z"/><circle class="d" cx="462" cy="304" r="3" fill="#3a3340"/><circle class="d" cx="364" cy="388" r="3" fill="#3a3340"/>';
      // Starthebel
      h += '<rect class="l" x="504" y="312" width="56" height="84" rx="8" fill="#8d8793"/><rect class="l" x="526" y="324" width="12" height="60" rx="5" fill="#3a3340"/>'
        + '<g id="hebel">' + (s.an ? '<path class="l n" style="stroke:#c9ced6;stroke-width:8" d="M532 354v26"/><circle class="l" cx="532" cy="384" r="11" fill="#3fcf6b"/>' : '<path class="l n" style="stroke:#c9ced6;stroke-width:8" d="M532 354v-26"/><circle class="l" cx="532" cy="324" r="11" fill="#d64b3c"/>') + '</g>';
      // Mausloch (Geheimnis)
      h += '<path class="l" fill="#3d2a20" d="M92 486v-22a24 24 0 0 1 48 0v22z"/><g id="maus" opacity="0"><g transform="translate(116 474)"><circle class="d" cx="-11" cy="-16" r="8" fill="#b9b3bd"/><circle class="d" cx="11" cy="-16" r="8" fill="#b9b3bd"/><ellipse class="l" rx="15" ry="14" fill="#b9b3bd"/>'
        + '<rect class="l" x="-15" y="-9" width="30" height="10" rx="5" fill="#2b3a4a"/><circle cy="7" r="3" fill="#f2a3a0"/></g></g>';
      // Werkbank: Schraubstock, Radio, Schublade
      h += '<path class="l" fill="#9a6b43" d="M44 392h16v96h-16zM330 392h16v96h-16z"/><rect class="l" x="28" y="374" width="336" height="20" rx="3" fill="#c99562"/>'
        + '<g id="stock"><path class="l" fill="#4a78b5" d="M64 374v-20h70v20zM74 354v-34h16v34zM112 354v-34h16v34z"/><path class="l n" style="stroke-width:5" d="M128 336h26M154 326v20"/></g>'
        + '<g id="radio"><path class="l n" d="M300 318l22 -36"/><rect class="l" x="232" y="318" width="100" height="56" rx="8" fill="#e9a23b"/><circle class="l" cx="262" cy="346" r="16" fill="#5b3a2e"/><circle class="d" cx="308" cy="336" r="6" fill="#f6f1e6"/><path class="d n" d="M296 358h24"/></g>'
        + '<g id="noten" opacity="0"><path class="l" fill="#3a3340" d="M330 300a8 6 0 1 1 0 .1zM346 300v-30l14 -6v10l-9 4"/></g>';
      if (s.lade) h += '<g id="lade"><rect class="l" x="196" y="398" width="150" height="26" fill="#3d2a20"/>' + (s.batterie === 'lade' ? '<g id="batt">' + batterie(270, 404, 0.8) + '</g>' : '') + '<rect class="l" x="190" y="416" width="162" height="54" rx="4" fill="#b07a4c"/><circle class="l" cx="271" cy="443" r="7" fill="#ffd23f"/></g>';
      else h += '<g id="lade"><rect class="l" x="204" y="396" width="134" height="54" rx="4" fill="#b07a4c"/><circle class="l" cx="271" cy="416" r="7" fill="#ffd23f"/><path fill="#3a3340" d="M271 428a5 5 0 0 1 3 9l2 8h-10l2 -8a5 5 0 0 1 3 -9z"/></g>';
      // Roboter, Farbkübel
      h += robo(s);
      if (s.eimer === 'oben') h += '<g id="eimer" class="linksu"><g transform="translate(722 290) rotate(-14)">' + kuebel() + '</g></g>';
      if (s.eimer === 'kopf') h += '<g transform="translate(700 262) rotate(-150)">' + kuebel(true) + '</g>';
      if (s.eimer === 'boden') h += '<g id="eimer"><g transform="translate(744 566)">' + kuebel() + '</g></g>';
      if (s.an && s.eimer !== 'kopf') h += Z.funken(574, 250, '#ffd23f') + Z.funken(740, 250, '#ffd23f');
      return h;
    },
    lauf: function (s, t, q) {
      var p = q('#pendel'); if (p) p.style.transform = 'rotate(' + (-aus(t)).toFixed(2) + 'deg)';
    },
    stellen: [
      { id: 'magnet', r: [262, 140, 320, 118], gut: function (s, t) { return s.schluessel !== 'haken' || aus(t) > 27; }, schlecht: function (s, t) { return s.schluessel === 'haken' && Math.abs(aus(t)) < 14; }, tipp: async function (s, a) {
        var w = aus(a.t);
        if (s.schluessel !== 'haken') {
          if (w < -22 && !s.dose) { a.ton('metall'); a.mal({ dose: true }); return a.gag('Klack – der Magnet schnappt sich die alte Konservendose und nimmt sie mit auf die Schaukel.', true); }
          a.ton('klick'); return a.gag('Der Magnet schwingt gemütlich weiter. Den Schlüssel hast du ja schon.');
        }
        if (w >= 22) {
          a.ton('metall'); await a.anim('#schluessel', [{ transform: 'translate(0,0)' }, { transform: 'translate(0,-10px)' }, { transform: 'translate(-60px,160px) scale(1.3)', opacity: 1 }, { transform: 'translate(-200px,420px) scale(.6)', opacity: 0 }], 900);
          a.mal({ schluessel: 'tasche' });
          return a.weiter('Klack! Der Magnet zieht den Schlüssel vom Haken – und du hast ihn in der Tasche.');
        }
        if (w <= -22) { a.ton('metall'); await a.anim('#dose', [{ transform: 'translateY(0)' }, { transform: 'translateY(-12px)' }, { transform: 'translateY(0)' }], 400); return a.gag('Klack – eine alte Konservendose. Die braucht niemand. Der Schlüssel hängt auf der anderen Seite.'); }
        a.ton('klick');
        return a.fehl('Daneben! Der Magnet schnappt ins Leere. Warte, bis er ganz rechts beim Schlüssel ist.');
      } },
      { id: 'schublade', r: [196, 392, 150, 96], tipp: async function (s, a) {
        if (!s.lade) {
          if (s.schluessel !== 'tasche') {
            a.ton('klick'); await a.anim('#lade', [{ transform: 'translateX(0)' }, { transform: 'translateX(4px)' }, { transform: 'translateX(-4px)' }, { transform: 'translateX(0)' }], 300);
            return a.gag(a.nr % 2 ? 'Abgeschlossen. Die Schublade rüttelt nur.' : 'Fest zu. Wo ist bloss der Schlüssel? Schau dich an den Wänden um.');
          }
          a.ton('klick'); await a.warte(250); a.ton('knarr'); a.mal({ lade: true, schluessel: 'weg' });
          return a.weiter('Der Schlüssel passt! In der Schublade liegt eine dicke Batterie.');
        }
        if (s.batterie === 'lade') {
          a.ton('plopp'); await a.anim('#batt', [{ transform: 'translate(0,0)' }, { transform: 'translate(0,-50px)' }, { transform: 'translate(-120px,200px)', opacity: 0 }], 700);
          a.mal({ batterie: 'tasche' });
          return a.weiter('Batterie eingepackt. Wer könnte die wohl brauchen?');
        }
        a.ton('knarr'); return a.gag('Die Schublade ist leer. Nur ein paar Schrauben kullern herum.');
      } },
      { id: 'eimer', r: [668, 196, 110, 100], wenn: function (s) { return s.eimer === 'oben'; }, tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#eimer', [{ transform: 'translate(0,0)' }, { transform: 'translate(44px,60px)' }, { transform: 'translate(30px,276px)' }], 800);
        a.mal({ eimer: 'boden' }); a.ton('plumps');
        return a.weiter('Der wacklige Farbkübel steht jetzt sicher am Boden.');
      } },
      { id: 'eimer2', r: [700, 492, 100, 104], wenn: function (s) { return s.eimer === 'boden'; }, tipp: async function (s, a) {
        a.ton('platsch'); await a.anim('#eimer', [{ transform: 'translateY(0)' }, { transform: 'translateY(-8px)' }, { transform: 'translateY(0)' }], 300);
        return a.gag('Blaue Farbe. Schön – aber lieber im Kübel als auf dem Roboter.');
      } },
      { id: 'robo', r: [590, 262, 124, 240], tipp: async function (s, a) {
        if (s.an) return a.gag('Piep!');
        if (s.batterie === 'tasche') {
          a.ton('klick'); a.mal({ batterie: 'robo' }); a.ton('robo');
          return a.weiter('Die Batterie sitzt in Rostos Brust. Er rührt sich aber noch nicht …');
        }
        a.ton('metall'); await a.anim('#rkopf', [{ transform: 'translateX(0)' }, { transform: 'translateX(4px)' }, { transform: 'translateX(-4px)' }, { transform: 'translateX(0)' }], 300);
        if (s.batterie === 'robo') return a.gag('Die Batterie ist drin. Rosto wartet nur noch auf den Startbefehl.');
        return a.gag(a.nr % 2 ? 'Dong. Rosto ist aus. In seiner Brust ist ein leeres Fach.' : 'Ganz schön verstaubt. Und er hält einen wackligen Farbkübel über dem Kopf …');
      } },
      { id: 'hebel', r: [482, 304, 100, 100], tipp: async function (s, a) {
        a.ton('klick');
        if (s.batterie !== 'robo') {
          await a.anim('#hebel', [{ transform: 'translateY(0)' }, { transform: 'translateY(22px)' }, { transform: 'translateY(0)' }], 500);
          return a.gag('Klack – nichts passiert. Ohne Batterie bleibt Rosto dunkel.');
        }
        a.mal({ an: true }); a.ton('robo');
        await a.anim('#robo', [{ transform: 'translateY(0)' }, { transform: 'translateY(-14px)' }, { transform: 'translateY(0)' }], 300);
        if (s.eimer === 'oben') {
          await a.anim('#eimer', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(-60deg)' }], 350);
          a.ton('platsch'); a.mal({ eimer: 'kopf' }); a.ton('zisch'); await a.warte(500);
          return a.sackgasse('Platsch! Rosto erwacht mit einem Ruck – und der Farbkübel kippt ihm über den Kopf. Kurzschluss!');
        }
        await a.anim('#armR', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(18deg)' }, { transform: 'rotate(-12deg)' }, { transform: 'rotate(18deg)' }, { transform: 'rotate(0deg)' }], 900);
        return a.fertig('Piep, piep! Rostos Augen leuchten auf. Er winkt dir zu – er läuft wieder!');
      } },
      { id: 'mausloch', r: [64, 400, 104, 100], tipp: async function (s, a) {
        a.ton('fiep'); await a.anim('#maus', [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(8px)' }], 1500);
        return a.geheim('Im Mausloch arbeitet auch jemand: eine Maus mit Schweisserbrille.');
      } },
      { id: 'radio', r: [224, 280, 116, 96], tipp: async function (s, a) {
        a.ton('radio'); a.anim('#radio', [{ transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' }], 700);
        await a.anim('#noten', [{ opacity: 0, transform: 'translate(0,0)' }, { opacity: 1, transform: 'translate(10px,-30px)' }, { opacity: 0, transform: 'translate(24px,-70px)' }], 900);
        return a.gag(a.nr % 2 ? 'Das Radio dudelt ein Liedchen. Rosto tanzt leider nicht mit.' : 'Dideldum. Gute Laune, aber kein Strom für Rosto.');
      } },
      { id: 'stock', r: [50, 300, 110, 96], tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#stock', [{ transform: 'translateX(0)' }, { transform: 'translateX(5px)' }, { transform: 'translateX(0)' }], 400);
        return a.gag('Der Schraubstock hält bombenfest. Leider hält er gerade gar nichts.');
      } },
      { id: 'werkzeug', r: [352, 290, 126, 110], tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#hammer', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(40deg)' }, { transform: 'rotate(-30deg)' }, { transform: 'rotate(16deg)' }, { transform: 'rotate(0deg)' }], 900);
        return a.gag('Der Hammer baumelt hin und her. Mit Draufhauen wird Rosto nicht wach.');
      } },
      { id: 'fenster', r: [36, 92, 124, 122], tipp: async function (s, a) {
        a.ton('pieps'); await a.anim('#fvogel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-16px)' }, { transform: 'translateY(0)' }], 400);
        return a.gag('Draussen schaut ein Vogel zu. Er findet Roboter spannend.');
      } },
      { id: 'lampe', r: [608, 30, 104, 100], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#lampe', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(-10deg)' }, { transform: 'rotate(6deg)' }, { transform: 'rotate(0deg)' }], 1000);
        return a.gag('Die Lampe schaukelt. Hier schaukelt überhaupt einiges …');
      } }
    ],
    naechster: function (s) {
      return s.schluessel === 'haken' ? 'magnet' : !s.lade ? 'schublade' : s.batterie === 'lade' ? 'schublade' : s.batterie === 'tasche' ? 'robo' : s.eimer === 'oben' ? 'eimer' : 'hebel';
    }
  });
})();
