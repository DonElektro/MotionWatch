/* Bild 2 «Zeltplatz am Morgen»: Kettenreaktion + richtiger Moment (Wind) + eine Sackgasse (leerer Kessel).
   Lösung: Holz in die Feuerstelle · Wasser in den Kessel (beliebige Reihenfolge) · Streichholz, wenn die Fahne schlaff hängt ·
   pfeifenden Kessel antippen (Kaffee in die Tasse) · Zelt antippen. */
(function () {
  var Z = WASNUN.Z;
  // Wind: 6 Sekunden Takt - zuerst 3 s Wind (Fahne flattert), dann 3 s ruhig (Fahne hängt)
  function phase(t) { return ((t % 6) + 6) % 6; }
  function windig(t) { return phase(t) < 2.85; }
  function kessel(s) {
    var f = s.kessel === 'glueht' ? '#e2553b' : '#5f7186';
    return '<g id="kessel"><path class="l n" d="M500 300v62"/><g transform="translate(500 398)">'
      + '<path class="l n" style="stroke-width:5" d="M-26 -22q26 -34 52 0"/><path class="l" fill="' + f + '" d="M30 -8l34 -16l4 10l-30 22z"/>'
      + '<path class="l" fill="' + f + '" d="M-38 -14q0 -12 38 -12t38 12q8 44 -38 46t-38 -46z"/><ellipse class="l" cx="0" cy="-22" rx="20" ry="6" fill="#3d4a5a"/><circle class="l" cx="0" cy="-30" r="6" fill="#e9a23b"/>'
      + '<path class="n" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".5" d="M-24 -4q-2 12 4 22"/>'
      + (s.wasser && s.kessel === 'kalt' ? '<path fill="#4aa3e8" d="M-52 6q7 12 0 16q-7 -4 0 -16z"/>' : '')
      + '</g>'
      + (s.kessel === 'pfeift' ? '<g class="a-schweb"><path class="l" fill="#fff" d="M572 360a12 12 0 0 1 14 -16a14 14 0 0 1 26 2a11 11 0 0 1 4 20q-24 6 -44 -6z"/><path class="l" fill="#fff" d="M604 322a8 8 0 0 1 10 -10a9 9 0 0 1 16 2a7 7 0 0 1 2 12q-16 4 -28 -4z"/></g>' : '')
      + (s.kessel === 'glueht' ? '<g class="a-schweb"><path class="l" fill="#6b6570" d="M470 340a14 14 0 0 1 16 -18a16 16 0 0 1 30 2a12 12 0 0 1 4 22q-28 8 -50 -6z"/><path class="l" fill="#6b6570" d="M500 296a9 9 0 0 1 10 -12a10 10 0 0 1 18 2a8 8 0 0 1 2 14q-18 4 -30 -4z"/></g>' : '')
      + '</g>';
  }
  function tasse(x, y, voll) {
    return '<g transform="translate(' + x + ' ' + y + ')"><path class="l n" style="stroke-width:5" d="M16 -22q18 2 14 14q-4 8 -16 6"/><path class="l" fill="#f6f1e6" d="M-18 -30h36l-4 30h-28z"/><path class="l n" style="stroke:#3f6fb3;stroke-width:4" d="M-18 -30h36"/>'
      + (voll ? '<ellipse cx="0" cy="-29" rx="14" ry="3" fill="#6b3f22"/><g class="a-schweb"><path class="d n" style="stroke:#fff" d="M-6 -40q-6 -8 0 -16t0 -16M8 -42q-6 -8 0 -16t0 -14"/></g>' : '') + '</g>';
  }
  WASNUN.szene({
    id: 'zeltplatz', titel: 'Zeltplatz am Morgen',
    ziel: 'Der Camper schläft noch. Ein heisser Kaffee würde ihn wecken – aber die Feuerstelle ist kalt.',
    start: function () { return { holz: false, wasser: false, feuer: false, kessel: 'kalt', tasse: false, camper: false }; },
    bild: function (s) {
      var h = '<rect width="800" height="600" fill="#c3e6f8"/>' + Z.sonne(110, 96) + Z.wolke(440, 74, 0.9)
        + '<path class="l" fill="#9db4c8" d="M250 420l150 -250l80 110l70 -80l210 220z"/><path class="l" fill="#fff" d="M400 170l34 46l-20 12l-18 -14l-24 14zM550 200l34 36l-24 -6l-12 14l-22 -18z"/>'
        + '<path fill="#93d48c" d="M0 400q200 -50 420 0t380 -20v220h-800z"/>'
        + Z.tanne(42, 440, 1.15) + '<g id="tanne" class="fuss">' + Z.tanne(750, 432, 1.25) + '</g>'
        + '<g id="zapfen" opacity="0"><ellipse class="d" cx="742" cy="330" rx="9" ry="14" fill="#8a5a3a"/></g>'
        + '<path class="l" fill="#7cc45a" d="M-5 430q210 -18 400 -4t410 -12v190h-810z"/>'
        + '<path class="d n" style="stroke:#4e9c38" d="M130 570l6 -12l6 12M470 578l6 -12l6 12M560 566l6 -12l6 12M30 580l6 -12l6 12M250 560l6 -12l6 12"/>'
        + '<g id="wind"><path class="l n" style="stroke:#fff;stroke-width:5" d="M0 150q30 -18 60 0t60 0M40 200q30 -18 60 0t60 0M-20 250q30 -18 60 0t60 0"/></g>';
      // Zelt mit Camper
      h += '<g id="zelt" class="fuss' + (s.camper ? '' : ' a-atmen') + '"><path class="l" fill="#f08a3c" d="M230 200L78 448h304z"/><path class="l n" style="stroke:#c96a24" d="M230 200L150 448M230 200L310 448"/>'
        + '<path class="l" fill="#5b3a2e" d="M230 262L176 448h108z"/>'
        + (s.camper ? '' : '<path class="l" fill="#ffd9a8" d="M230 262L176 448h54z" opacity=".25"/>') + '</g>';
      if (s.camper) h += '<g id="camper"><g transform="translate(232 410)"><path class="l" fill="#3f8fd0" d="M-40 40q0 -34 40 -34t40 34z"/><circle class="l" r="28" fill="#f3c9a5"/><path class="l" fill="#d64b3c" d="M-29 -6q4 -30 29 -30t29 30q-28 -12 -58 0z"/><circle class="l" cy="-38" r="7" fill="#fff"/>'
        + '<path class="l n" d="M-16 0q6 -7 12 0M5 0q6 -7 12 0"/><ellipse class="d" cx="0" cy="8" rx="5" ry="4" fill="#e79a8a"/><path class="l" fill="#fff" d="M-12 14q12 12 24 0z"/></g>' + tasse(282, 446, true) + '</g>';
      else h += Z.zzz(262, 300, 1);
      h += '<g id="vogel"><g transform="translate(230 178)">' + Z.vogel({ f: '#4aa3e8' }) + '</g></g>';
      // Rucksack mit Socke
      h += '<g id="socke"><path class="l" fill="#fff" d="M52 452v-30h18v30z"/><path class="l n" style="stroke:#d64b3c;stroke-width:4" d="M52 430h18"/></g>'
        + '<path class="l" fill="#3f9b6a" d="M22 520q-6 -70 40 -72q44 2 40 72q-40 14 -80 0z"/><path class="l" fill="#2f7d55" d="M38 520q0 -30 24 -30t24 30q-24 8 -48 0z"/><path class="l n" d="M40 456q22 -26 44 0"/>';
      // Maus hinter den Stiefeln (Geheimnis)
      h += '<g id="maus"><g transform="translate(186 500) scale(.85)"><circle class="d" cx="-10" cy="-14" r="8" fill="#b9b3bd"/><circle class="d" cx="10" cy="-14" r="8" fill="#b9b3bd"/><ellipse class="l" rx="14" ry="13" fill="#b9b3bd"/>' + Z.auge(-5, -3, 3) + Z.auge(5, -3, 3) + '<circle cy="5" r="3" fill="#f2a3a0"/></g></g>'
        + '<g transform="translate(196 520)"><path class="l" fill="#8a5a3a" d="M-22 -44h24v26q24 0 26 18h-50z"/><path class="l" fill="#5b3a2e" d="M-24 0h54v8h-54z"/><path class="d n" style="stroke:#f6f1e6" d="M-8 -30h10M-8 -22h10"/></g>'
        + '<g transform="translate(238 530)"><path class="l" fill="#9a6b43" d="M-22 -44h24v26q24 0 26 18h-50z"/><path class="l" fill="#5b3a2e" d="M-24 0h54v8h-54z"/><path class="d n" style="stroke:#f6f1e6" d="M-8 -30h10M-8 -22h10"/></g>';
      // Baumstrunk mit Tasse
      h += '<path class="l" fill="#9a6b43" d="M296 548v-42h76v42q-38 12 -76 0z"/><ellipse class="l" cx="334" cy="506" rx="38" ry="12" fill="#d9b48a"/><ellipse class="d n" cx="334" cy="506" rx="18" ry="5"/>';
      if (!s.camper) h += '<g id="tasse">' + tasse(334, 506, s.tasse) + '</g>';
      // Feuerstelle, Dreibein, Kessel
      h += '<path class="l n" style="stroke:#6d5a48;stroke-width:6" d="M500 296L432 500M500 296L568 500M500 296L506 470"/>'
        + '<ellipse cx="500" cy="500" rx="74" ry="20" fill="#5a5560" opacity=".5"/>';
      if (s.holz) h += '<g transform="translate(500 492)"><path class="l" fill="#9a6b43" d="M-46 -4l84 -22l6 16l-84 22z"/><path class="l" fill="#b07a4c" d="M-40 -26l84 22l-6 16l-84 -22z"/><ellipse class="d" cx="41" cy="5" rx="6" ry="9" fill="#e6c79f"/></g>';
      if (s.feuer) h += '<g class="fuss a-flack"><path class="l" fill="#f2711c" d="M500 486q-44 -8 -30 -48q8 12 14 6q-8 -30 18 -48q-2 22 14 30q4 -12 12 -14q20 54 -28 74z"/><path class="d" fill="#ffd23f" d="M500 484q-22 -6 -14 -28q6 8 10 2q0 -14 10 -22q2 14 10 18q10 22 -16 30z"/></g>';
      else if (s.streich) h += '<g id="flamme"><path class="d" fill="#ffd23f" d="M508 470q-10 -4 -4 -16q2 -8 6 -10q6 16 4 22z"/><path class="l n" style="stroke:#e6c79f;stroke-width:4" d="M508 470l26 22"/></g>';
      h += '<g><ellipse class="l" cx="440" cy="502" rx="20" ry="13" fill="#a9a4ae"/><ellipse class="l" cx="560" cy="502" rx="20" ry="13" fill="#bdb8c2"/><ellipse class="l" cx="478" cy="514" rx="22" ry="13" fill="#bdb8c2"/><ellipse class="l" cx="524" cy="514" rx="22" ry="13" fill="#a9a4ae"/></g>'
        + kessel(s);
      // Wasserkanister
      h += '<g id="kanister" class="dreh"><g transform="translate(420 560)"><path class="l" fill="#4aa3e8" d="M-28 -62h34l22 16v46h-56z"/><path class="l n" style="stroke-width:5" d="M-18 -62q0 -14 14 -14t14 14"/><rect class="l" x="12" y="-58" width="12" height="10" fill="#fff"/>'
        + '<path fill="#fff" opacity=".85" d="M0 -34q14 18 0 26q-14 -8 0 -26z"/></g></g>';
      // Fahne (flattert / hängt) - lauf() schaltet um
      h += '<path class="l n" style="stroke:#8a5a3a;stroke-width:6" d="M645 452V210"/><circle class="l" cx="645" cy="208" r="7" fill="#ffd23f"/>'
        + '<g id="fw" class="linksm"><path class="l" fill="#d64b3c" d="M648 218q24 -14 44 0t40 -2l-14 20l14 20q-20 4 -40 -8t-44 4z"/></g>'
        + '<g id="fr" style="display:none"><path class="l" fill="#d64b3c" d="M648 218q20 6 16 34t6 46l-12 -6l-10 10z"/></g>';
      // Streichhölzer auf dem Stein, Holzstapel
      h += '<ellipse class="l" cx="612" cy="548" rx="46" ry="16" fill="#bdb8c2"/><g id="zuendholz"><g transform="translate(612 536)"><path class="l n" style="stroke:#e6c79f;stroke-width:5" d="M4 -12l22 -26"/><circle class="d" cx="27" cy="-39" r="5" fill="#d64b3c"/>'
        + '<path class="l" fill="#ffd23f" d="M-26 -16h46v18h-46z"/><path class="l" fill="#d64b3c" d="M-26 -16h46v6h-46z"/><path class="l" fill="#5b3a2e" d="M-26 2h46l-4 6h-38z"/></g></g>'
        + '<g id="stapel"><g transform="translate(736 560)">' + (s.holz ? '' : '<g><rect class="l" x="-30" y="-78" width="60" height="26" rx="12" fill="#b07a4c"/><circle class="d" cx="-18" cy="-65" r="8" fill="#e6c79f"/></g>')
        + '<rect class="l" x="-52" y="-52" width="60" height="26" rx="12" fill="#9a6b43"/><circle class="d" cx="-40" cy="-39" r="8" fill="#e6c79f"/><rect class="l" x="-6" y="-52" width="60" height="26" rx="12" fill="#b07a4c"/><circle class="d" cx="6" cy="-39" r="8" fill="#e6c79f"/>'
        + '<rect class="l" x="-64" y="-26" width="60" height="26" rx="12" fill="#b07a4c"/><circle class="d" cx="-52" cy="-13" r="8" fill="#e6c79f"/><rect class="l" x="-2" y="-26" width="66" height="26" rx="12" fill="#9a6b43"/><circle class="d" cx="10" cy="-13" r="8" fill="#e6c79f"/></g></g>';
      return h;
    },
    lauf: function (s, t, q) {
      var w = windig(t), fw = q('#fw'), fr = q('#fr'), wd = q('#wind'), tn = q('#tanne');
      if (fw) { fw.style.display = w ? '' : 'none'; fw.style.transform = 'scaleY(' + (1 + 0.18 * Math.sin(t * 14)) + ')'; }
      if (fr) fr.style.display = w ? 'none' : '';
      if (wd) { var p = phase(t); wd.style.opacity = w ? 0.85 : 0; wd.style.transform = 'translateX(' + (p * 330 - 100) + 'px)'; }
      if (tn) tn.style.transform = 'rotate(' + (w ? 2.5 * Math.sin(t * 5) : 0) + 'deg)';
    },
    stellen: [
      { id: 'zuendholz', r: [560, 468, 100, 100], gut: function (s, t) { var p = phase(t); return !s.holz || s.feuer || (p > 3.15 && p < 5.5); }, schlecht: function (s, t) { var p = phase(t); return s.holz && !s.feuer && p > 0.3 && p < 2.3; }, tipp: async function (s, a) {
        if (s.feuer) { a.ton('klick'); return a.gag('Das Feuer brennt schon. Die Streichhölzer bleiben in der Schachtel.'); }
        a.ton('zisch');
        await a.anim('#zuendholz', [{ transform: 'translate(0,0)' }, { transform: 'translate(-84px,-50px)' }], 450);
        a.mal({ streich: true });
        if (windig(a.t)) {
          a.ton('puff'); await a.anim('#flamme', [{ opacity: 1, transform: 'translateX(0)' }, { opacity: 0, transform: 'translateX(60px)' }], 400);
          a.mal({ streich: false });
          return s.holz ? a.fehl('Pffft – der Wind bläst das Streichholz aus. Schau auf die Fahne und warte, bis sie schlaff hängt!')
            : a.gag('Der Wind bläst das Streichholz aus. Und Holz liegt auch noch keines in der Feuerstelle.');
        }
        if (!s.holz) {
          await a.warte(600); a.ton('puff'); a.mal({ streich: false });
          return a.gag('Das Streichholz brennt ab. Ohne Holz gibt es kein Feuer.');
        }
        await a.warte(350); a.mal({ streich: false, feuer: true }); a.ton('zisch'); await a.warte(900);
        if (!s.wasser) {
          a.mal({ kessel: 'glueht' }); a.ton('zisch'); await a.warte(500);
          return a.sackgasse('Oje, der Kessel ist leer! Er glüht und qualmt.');
        }
        a.mal({ kessel: 'pfeift' }); a.ton('pfeif');
        return a.weiter('Das Feuer brennt und der Kessel pfeift schon. Das Wasser kocht!');
      } },
      { id: 'holz', r: [668, 462, 130, 120], tipp: async function (s, a) {
        if (s.holz) { a.ton('plumps'); return a.gag('Ein Scheit reicht für einen Kaffee. Der Rest bleibt für heute Abend.'); }
        a.ton('plumps');
        await a.anim('#stapel', [{ transform: 'translate(0,0)' }, { transform: 'translate(0,-8px)' }, { transform: 'translate(0,0)' }], 250);
        a.mal({ holz: true });
        return a.weiter('Ein dickes Scheit liegt in der Feuerstelle.');
      } },
      { id: 'kanister', r: [372, 482, 96, 105], tipp: async function (s, a) {
        if (s.wasser) { a.ton('tropf'); return a.gag('Der Kessel ist voll. Noch mehr Wasser und er läuft über.'); }
        if (s.feuer) return a.gag('Jetzt nicht mehr.');
        await a.anim('#kanister', [{ transform: 'translate(0,0) rotate(0deg)' }, { transform: 'translate(34px,-196px) rotate(0deg)' }, { transform: 'translate(34px,-196px) rotate(50deg)' }], 700);
        a.ton('wasser'); await a.warte(700);
        await a.anim('#kanister', [{ transform: 'translate(34px,-196px) rotate(50deg)' }, { transform: 'translate(0,0) rotate(0deg)' }], 450);
        a.mal({ wasser: true });
        return a.weiter('Gluck, gluck – der Kessel ist voll Wasser.');
      } },
      { id: 'kessel', r: [448, 335, 104, 100], tipp: async function (s, a) {
        if (s.kessel === 'pfeift') {
          a.ton('wasser');
          await a.anim('#kessel', [{ transform: 'translate(0,0)' }, { transform: 'translate(-150px,60px)' }, { transform: 'translate(-150px,60px) rotate(-18deg)' }, { transform: 'translate(-150px,60px)' }, { transform: 'translate(0,0)' }], 1500);
          a.mal({ tasse: true, kessel: 'fertig' });
          return a.weiter('Heisser Kaffee in der Tasse! Der Duft zieht hinüber zum Zelt.');
        }
        a.ton('metall'); await a.anim('#kessel', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(5deg)' }, { transform: 'rotate(-4deg)' }, { transform: 'rotate(0deg)' }], 500);
        return a.gag(s.kessel === 'fertig' ? 'Der Kessel ist leer. Der Kaffee wartet in der Tasse.' : s.wasser ? 'Voll mit kaltem Wasser. Kalter Kaffee? Brrr.' : 'Klong. Der Kessel ist leer und kalt.');
      } },
      { id: 'zelt', r: [130, 235, 200, 195], tipp: async function (s, a) {
        if (s.tasse) {
          await a.anim('#zelt', [{ transform: 'scale(1,1)' }, { transform: 'scale(1.04,.96)' }, { transform: 'scale(.97,1.03)' }, { transform: 'scale(1,1)' }], 600);
          a.ton('huch'); a.mal({ camper: true });
          await a.anim('#camper', [{ transform: 'translateY(30px)', opacity: 0 }, { transform: 'translateY(0)', opacity: 1 }], 500);
          return a.fertig('«Mmmh, Kaffee!» Der Camper kriecht aus dem Zelt. Guten Morgen!');
        }
        a.ton('schnarch'); await a.anim('#zelt', [{ transform: 'scale(1,1)' }, { transform: 'scale(1.06,.95)' }, { transform: 'scale(1,1)' }], 900);
        return a.gag(a.nr % 2 ? 'Chrrr … Rütteln nützt nichts. Der Camper schnarcht weiter.' : 'Das ganze Zelt schnarcht mit. Den weckt nur seine Nase.');
      } },
      { id: 'tasse', r: [286, 425, 96, 95], tipp: async function (s, a) {
        a.ton('klick');
        return a.gag(s.tasse ? 'Finger weg, der Kaffee ist für den Camper!' : 'Die Tasse ist leer. Gähnend leer.');
      } },
      { id: 'stiefel', r: [166, 462, 110, 95], tipp: async function (s, a) {
        a.ton('fiep'); await a.anim('#maus', [{ transform: 'translateY(0)' }, { transform: 'translateY(-42px)' }, { transform: 'translateY(-42px)' }, { transform: 'translateY(0)' }], 1100);
        return a.geheim('Im Stiefel wohnt eine Maus. Der Camper wird sich wundern.');
      } },
      { id: 'feuer', r: [440, 445, 120, 95], tipp: async function (s, a) {
        a.ton(s.feuer ? 'zisch' : 'puff');
        return a.gag(s.feuer ? 'Heiss! Lieber nicht anfassen.' : s.holz ? 'Das Holz liegt bereit. Jetzt fehlt nur noch ein Funke.' : 'Kalte Asche von gestern. Hier brennt nichts.');
      } },
      { id: 'fahne', r: [600, 195, 140, 120], tipp: async function (s, a) {
        a.ton('flatter');
        return a.gag(windig(a.t) ? 'Die Fahne flattert: Es windet gerade.' : 'Die Fahne hängt schlaff herunter: Es ist windstill.');
      } },
      { id: 'vogel', r: [182, 128, 96, 100], tipp: async function (s, a) {
        a.ton('pieps'); await a.anim('#vogel', [{ transform: 'translateY(0)' }, { transform: 'translateY(-22px)' }, { transform: 'translateY(0)' }, { transform: 'translateY(-12px)' }, { transform: 'translateY(0)' }], 600);
        return a.gag('Der Vogel singt sein Morgenlied. Den Camper weckt das nicht.');
      } },
      { id: 'rucksack', r: [14, 420, 104, 115], tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#socke', [{ transform: 'translateY(0)' }, { transform: 'translateY(-26px)' }, { transform: 'translateY(-26px)' }, { transform: 'translateY(0)' }], 900);
        return a.gag(a.nr % 2 ? 'Im Rucksack: eine Socke. Riecht nicht nach Kaffee.' : 'Noch eine Socke. Und Kaffeepulver hat er zum Glück schon im Kessel.');
      } },
      { id: 'tanne', r: [690, 215, 110, 215], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#zapfen', [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(110px)' }, { opacity: 0, transform: 'translateY(118px)' }], 600, { easing: 'ease-in' });
        a.ton('plumps');
        return a.gag('Ein Tannzapfen fällt herunter. Tock.');
      } },
      { id: 'sonne', r: [40, 30, 140, 135], tipp: async function (s, a) {
        a.ton('plopp');
        return a.gag('Die Sonne ist auch gerade erst aufgestanden.');
      } }
    ],
    naechster: function (s) { return !s.holz ? 'holz' : !s.wasser ? 'kanister' : !s.feuer ? 'zuendholz' : !s.tasse ? 'kessel' : 'zelt'; }
  });
})();
